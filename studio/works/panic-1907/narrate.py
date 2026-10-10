#!/usr/bin/env python3
"""narrate.py: the studio's own voice (Kokoro, run locally), with its timing set by what speech.py measured in people.

    python3 narrate.py <folder with kokoro-v1.0.onnx and voices-v1.0.bin> [scene numbers, default 1] [--voice am_michael]

speech.py does not speak. It listens: it finds the pauses and breath groups in a recording and measures rate.
Here it is used three ways:
  1. pace: the voice is run once, its talk rate measured, and the speed reset so it lands on the human median
  2. pauses: every silence in the take is found in the waveform, matched to the punctuation that caused it,
     and left alone unless it falls outside the band human narrators use for that kind of break
  3. proof: the raw and the tuned takes are both measured and printed next to the human numbers
Writes notes/sample_raw.wav, notes/sample_tuned.wav and notes/sample.json.
"""
import sys, os, re, json, warnings
warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, librosa
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from studio.senses import speech as SP
from kokoro_onnx import Kokoro

SR = 44100
HUMAN = json.load(open(f'{HERE}/notes/human.json'))['pooled']
BAND = {'none': (0.0, 0.16), 'comma': (0.17, 0.46), 'stop': (0.50, 0.85), 'dots': (0.55, 0.80), 'beat': (0.95, 1.30)}   # beat: a [pause] in the script, a new thought

def breaks(text):
    """Where the punctuation falls, as a fraction of the letters spoken, and what kind it is."""
    size = lambda w: len(re.sub(r'[^A-Za-z]', '', w)) + 4 * len(re.sub(r'[^0-9]', '', w))     # a digit is a whole word aloud
    toks = text.split(); letters = sum(size(w) for w in toks if w != '[pause]'); out = []; n = 0
    for i, w in enumerate(toks):
        if w == '[pause]': continue
        n += size(w)
        k = 'dots' if re.search(r'(…|\.\.\.)["”]?$', w) else 'stop' if re.search(r'[.?!]["”]?$', w) else 'comma' if re.search(r'[,;:]["”]?$', w) else None
        if k and i + 1 < len(toks) and toks[i + 1] == '[pause]': k = 'beat'            # the script asks for a held beat here
        if k and n < letters: out.append((n / letters, k, w))
    return out

def silences(y):
    y16 = librosa.resample(y, orig_sr=SR, target_sr=SP.SR); y16 = y16 / (np.max(np.abs(y16)) + 1e-9)
    mask, runs = SP.speech_mask(SP.envelope(y16)); fr = SP.HOP / SP.SR
    return [(a * fr, b * fr) for a, b in runs]

def retime(y, text, log):
    runs = silences(y)
    t0, t1 = runs[0][0], runs[-1][1]
    gaps = [(runs[i][1], runs[i + 1][0]) for i in range(len(runs) - 1)]
    bk = breaks(text); used = set(); edits = []; last = -1; found = []
    # speech time only (pauses taken out) is what the letter fraction tracks
    talk = np.cumsum([b - a for a, b in runs]); total = talk[-1]
    for gi, (ga, gb) in enumerate(gaps):
        frac = talk[gi] / total; have = gb - ga
        # breaks and silences come in the same order, so only look forward from the last match
        cand = [(abs(f - frac), j) for j, (f, k, w) in enumerate(bk) if j > last and abs(f - frac) < 0.15]
        if cand: j = min(cand)[1]; used.add(j); last = j; kind, word = bk[j][1], bk[j][2]
        else: kind, word = 'none', ''
        lo, hi = BAND[kind]; want = min(max(have, lo), hi)
        if kind == 'none': want = min(have, BAND['comma'][1])       # a breath the script did not mark: keep it, cap it
        log.append({'after': word, 'kind': kind, 'was': round(float(have), 2), 'now': round(float(want), 2)})
        if abs(want - have) >= 0.03: edits.append(((ga + gb) / 2, want - have))
        found.append(((ga + gb) / 2, kind, word))
    for j, (f, k, w) in enumerate(bk):
        if j not in used and k in ('stop', 'dots'): log.append({'after': w, 'kind': k, 'was': 0.0, 'now': 0.0, 'note': 'no silence found here; left as spoken'})
    # cut or add silence at the middle of each gap, with short crossfades
    a = int(max(0, t0 - 0.07) * SR); b = int(min(len(y) / SR, t1 + 0.22) * SR)
    segs = []; cur = a; floor = 1e-4
    for mid, d in edits:
        m = int(mid * SR)
        if d > 0: segs.append(y[cur:m]); segs.append(np.random.default_rng(m).standard_normal(int(d * SR)) * floor); cur = m
        else: h = int(-d * SR / 2); segs.append(y[cur:m - h]); cur = m + h
    segs.append(y[cur:b])
    xf = int(0.008 * SR); out = segs[0].copy()
    for s in segs[1:]:
        if len(s) < xf or len(out) < xf: out = np.concatenate([out, s]); continue
        w = np.linspace(0, 1, xf); out[-xf:] = out[-xf:] * (1 - w) + s[:xf] * w; out = np.concatenate([out, s[xf:]])
    n_in, n_out = int(0.012 * SR), int(0.10 * SR)
    out[:n_in] *= np.sin(np.linspace(0, np.pi / 2, n_in)) ** 2; out[-n_out:] *= np.cos(np.linspace(0, np.pi / 2, n_out)) ** 2
    a_s = a / SR
    where = [(mid - a_s + sum(d for m, d in edits if m < mid) + sum(d / 2 for m, d in edits if m == mid), kind, word) for mid, kind, word in found]
    return out, where

def sentences(tagged):
    """The scene's sentences, each with what follows it: 'stop', 'beat' or 'end'."""
    out = []
    for i, part in enumerate(re.split(r'\s*\[pause\]\s*', tagged)):
        ss = re.findall(r'[^.?!]+(?:\.\.\.[^.?!]+)*[.?!]+', part)
        out += [(x.strip(), 'stop') for x in ss]; out[-1] = (out[-1][0], 'beat')
    out[-1] = (out[-1][0], 'end'); return out

def shape(y, spans, g_db, h_db):
    """Sharp to soft, without changing the voice: level and brightness follow the delivery number, eased across joins."""
    import scipy.signal as sg
    from scipy.ndimage import uniform_filter1d
    d = np.zeros(len(y))
    for t0, t1, v in spans: d[int(t0 * SR):int(t1 * SR)] = v
    d = uniform_filter1d(d, int(0.25 * SR))
    low = sg.sosfiltfilt(sg.butter(2, 2500, 'low', fs=SR, output='sos'), y); high = y - low
    return (low + high * 10 ** (h_db * d / 20)) * 10 ** (g_db * d / 20)

def level(y):
    r = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]; return float(np.sqrt(np.mean(r[r > 0.15 * r.max()] ** 2)))

def polish(y):
    """The same light voice chain as the cheetah film: clear rumble, a little presence, round the tallest peaks."""
    import scipy.signal as sg
    y = sg.sosfilt(sg.butter(2, 80, 'high', fs=SR, output='sos'), y)
    y = y + 0.2 * sg.sosfilt(sg.butter(2, [2500, 5500], 'bandpass', fs=SR, output='sos'), y)
    y = y - 0.25 * sg.sosfilt(sg.butter(2, [280, 520], 'bandpass', fs=SR, output='sos'), y)
    pk = np.percentile(np.abs(y[np.abs(y) > 1e-3]), 99.8); y = np.tanh(y / pk) * pk
    return y / np.max(np.abs(y)) * 0.80

def measure(path):
    r = SP.analyse(path); keep = ['seconds', 'talk_rate_syl_s', 'pause_share', 'pauses_per_min', 'pause_median_s', 'pause_p90_s', 'group_median_s', 'group_cv', 'pitch_range_st', 'declination_st', 'reset_st']
    return {k: r[k] for k in keep}, r['pauses']

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; M = args[0]
    which = [int(x) for x in args[1].split(',')] if len(args) > 1 else [1]
    voice = sys.argv[sys.argv.index('--voice') + 1] if '--voice' in sys.argv else 'am_michael'
    tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'sample'
    k = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))
    say = lambda text, speed: librosa.resample(k.create(text, voice=voice, speed=speed, lang='en-us')[0].astype(np.float64), orig_sr=24000, target_sr=SR)
    # the spoken script: numbers and names written the way they are said ("nineteen oh seven", not "1907")
    spoken = json.load(open(f'{HERE}/script.json'))['spoken']
    plain = lambda t: re.sub(r'\s*\[pause\]', '', t)
    os.makedirs(f'{HERE}/notes', exist_ok=True)

    style = sys.argv[sys.argv.index('--style') + 1] if '--style' in sys.argv else 'A'
    G, Hh, PACE = {'0': (0, 0, 0), 'A': (2.0, 2.5, 0), 'B': (2.0, 2.5, 0.05), 'C': (3.0, 4.0, 0.08)}[style]
    delivery = json.load(open(f'{HERE}/script.json')).get('delivery', {})

    # raw: exactly as the voice gives it at its default speed
    raw = np.concatenate([say(plain(spoken[n - 1]), 1.0) for n in which])
    sf.write(f'{HERE}/notes/{tag}_raw.wav', polish(raw).astype(np.float32), SR, subtype='PCM_16')
    m_raw, p_raw = measure(f'{HERE}/notes/{tag}_raw.wav')
    speed = float(np.clip(HUMAN['talk_rate_syl_s'] / m_raw['talk_rate_syl_s'], 0.94, 1.03))
    log = []; clips = []; rngp = np.random.default_rng(7)
    for n in which:
        sents = sentences(spoken[n - 1]); plan = delivery.get(str(n), [0] * len(sents))
        assert len(plan) == len(sents), f'scene {n}: {len(sents)} sentences, {len(plan)} delivery numbers'
        if PACE == 0:
            # one pass for the whole scene; find where each sentence ended and lay the delivery over it
            y, where = retime(say(plain(spoken[n - 1]), speed), spoken[n - 1], log)
            ends = {w: t for t, kind, w in where if kind in ('stop', 'beat')}
            spans = []; t0 = 0.0
            for (text, nxt), d in zip(sents, plan):
                last = text.split()[-1]
                if last in ends and ends[last] > t0: spans.append((t0, ends[last], d)); t0 = ends[last]
            spans.append((t0, len(y) / SR, plan[-1]))
            clips.append(shape(y, spans, G, Hh))
        else:
            # each sentence said on its own at its own pace: sharp lines move, soft lines take their time
            parts = [retime(say(text, speed * (1 + PACE * d)), text, log)[0] for (text, nxt), d in zip(sents, plan)]
            base = float(np.median([level(p) for p in parts])); seq = []; spans = []; t = 0.0
            for i, (p, (text, nxt), d) in enumerate(zip(parts, sents, plan)):
                p = p * np.clip(base / level(p), 0.71, 1.41); spans.append((t, t + len(p) / SR, d)); seq.append(p); t += len(p) / SR
                if nxt == 'end': break
                want = rngp.uniform(*BAND['beat']) if nxt == 'beat' else rngp.uniform(0.52, 0.72)
                if plan[i + 1] <= -0.6: want += 0.22                      # room before a line that has to land
                if d >= 0.4 and plan[i + 1] >= 0.4: want -= 0.08           # two sharp lines sit closer
                gap = max(0.05, want - 0.29)                                # each piece keeps 0.07 s lead and 0.22 s tail
                seq.append(np.zeros(int(gap * SR))); t += gap; log.append({'after': text.split()[-1], 'kind': nxt, 'was': None, 'now': round(want, 2)})
            clips.append(shape(np.concatenate(seq), spans, G, Hh))
    target = float(np.median([level(c) for c in clips]))
    out = [np.zeros(int(0.4 * SR))]
    for i, y in enumerate(clips):
        out.append(y * np.clip(target / level(y), 0.71, 1.41))
        if i < len(clips) - 1: out.append(np.zeros(int(rngp.uniform(1.1, 1.3) * SR)))
    out.append(np.zeros(int(0.6 * SR)))
    sf.write(f'{HERE}/notes/{tag}_tuned.wav', polish(np.concatenate(out)).astype(np.float32), SR, subtype='PCM_16')
    m_tun, p_tun = measure(f'{HERE}/notes/{tag}_tuned.wav')

    human = {k2: HUMAN.get(k2) for k2 in m_raw}; human['pause_median_s'] = HUMAN['pause_quartiles_s'][2]; human['pause_p90_s'] = HUMAN['pause_quartiles_s'][4]
    json.dump({'voice': voice, 'speed': round(speed, 3), 'human': human, 'raw': m_raw, 'tuned': m_tun, 'raw_pauses': p_raw, 'tuned_pauses': p_tun, 'breaks': log}, open(f'{HERE}/notes/{tag}.json', 'w'), indent=1)
    print(f'voice {voice}, speed set to {speed:.2f}')
    print(f"{'':22s}{'human':>9s}{'raw':>9s}{'tuned':>9s}")
    for k2 in m_raw: print(f'{k2:22s}{str(human[k2]):>9s}{str(m_raw[k2]):>9s}{str(m_tun[k2]):>9s}')
    print('breaks:')
    for b in log: print('  ', b)
