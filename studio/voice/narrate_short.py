#!/usr/bin/env python3
"""Narrate a Short with the studio voice (Kokoro, local, free), matched to the beer-flood narrator.

    python3 studio/voice/narrate_short.py <models dir> <beer_ref.wav> <out dir> --lines lines.json

lines.json is a list of strings, one per beat. Writes narration.wav (44.1 kHz) and times.json:
{"durs": [...beat seconds...], "starts": [...], "voice": [[start, end], ...]} so the picture can retime to the read.
"""
import argparse, json, os, re, subprocess
import numpy as np, soundfile as sf, librosa
from scipy import signal as sg
from kokoro_onnx import Kokoro

SR = 24000
LEAD, TAIL = 0.06, 0.10          # silence before a line starts in its beat, and after it ends


def ltas(y):
    f, p = sg.welch(y, SR, nperseg=2048)
    return f, 10 * np.log10(p + 1e-14)


def squeeze(a, max_pause=0.13, floor_db=-42.0, guard=0.06, xf=0.012):
    """Shorten long silences inside a take, without touching the words.

    Only a run that is truly silent (envelope more than 42 dB under the take's peak) for longer than max_pause + 2 * guard
    is shortened. guard seconds of untouched audio stay on each side (the decay of the word before, the lead-in of the word
    after), and the two sides meet with a short crossfade in the middle of the silence. The old version faded across
    65 ms on each side of anything under a fixed level, which clipped soft word starts and tails (owner, 2026-10-26).
    """
    env = np.convolve(np.abs(a), np.ones(240) / 240, 'same')
    quiet = env < np.max(env) * 10 ** (floor_db / 20)
    n, g, x, keep = len(a), int(guard * SR), int(xf * SR), int(max_pause * SR)
    out, last, i = [], 0, 0
    while i < n:
        if not quiet[i]:
            i += 1; continue
        j = i
        while j < n and quiet[j]:
            j += 1
        if j - i > keep + 2 * g and i > 0 and j < n:            # inner silence only (trim() handles the ends)
            cut0 = i + g + (keep - x) // 2                       # keep guard + half the pause, then jump to the matching point
            cut1 = j - g - (keep - x) // 2
            out.append(a[last:cut0])
            fade = np.linspace(1, 0, x)
            out.append(a[cut0:cut0 + x] * fade + a[cut1 - x:cut1] * (1 - fade))
            last = cut1
        i = j
    out.append(a[last:])
    return np.concatenate(out)


def trim(a, floor_db=-50.0, pre=0.03, post=0.06):
    """Cut the silence before and after a take, with room for soft first/last sounds (s, f, h) and a short fade."""
    env = np.convolve(np.abs(a), np.ones(120) / 120, 'same')
    nz = np.where(env > np.max(env) * 10 ** (floor_db / 20))[0]
    y = a[max(0, nz[0] - int(pre * SR)):nz[-1] + int(post * SR)].copy()
    f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('models'); ap.add_argument('ref'); ap.add_argument('out')
    ap.add_argument('--lines', required=True)
    ap.add_argument('--holds', help='json list of extra seconds per beat')
    ap.add_argument('--speed', type=float, default=1.12)
    ap.add_argument('--preset', help='named voice from voices.json (male is the default; female = Cody\'s A3 pick)')
    ap.add_argument('--voice', default='am_fenrir:0.65,am_puck:0.35', help='voice blend, e.g. af_heart:0.6,af_bella:0.4')
    ap.add_argument('--no-match', action='store_true', help='skip the tone match to the reference read (use for voices unlike the ref)')
    ap.add_argument('--lang', default='en-us')
    ap.add_argument('--gap', type=float, default=0.12, help='pause at a sentence end inside a line (s)')
    ap.add_argument('--max-pause', type=float, default=0.13, help='longest quiet gap allowed inside a sentence (s)')
    ap.add_argument('--choppy', action='store_true', help='old way: speak each sentence separately (each one restarts like a fresh breath)')
    ap.add_argument('--hold', type=float, default=0.8, help="pause for '...' (s)")
    ap.add_argument('--after-scale', type=float, default=0.35, help='scale the pause after each line (tight, no dead air)')
    ap.add_argument('--one-take', action='store_true', help='read the WHOLE script as one take (no fresh breath and no pitch reset at each line), '
                    'then cut it into beats in the pause nearest each line end')
    a = ap.parse_args()
    if a.preset:                                    # a saved voice overrides the voice settings
        P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voices.json')))[a.preset]
        a.voice, a.speed, a.no_match = P['voice'], P['speed'], not P.get('match', True)
        a.gap, a.hold, a.after_scale = P.get('gap', a.gap), P.get('hold', a.hold), P.get('after_scale', a.after_scale)
        a.max_pause = P.get('max_pause', a.max_pause)
    lines = json.load(open(a.lines))
    # a line is a string, or {"text", "speed" (x base speed), "after" (pause after the line, s)}
    lines = [l if isinstance(l, dict) else {'text': l} for l in lines]
    holds = json.load(open(a.holds)) if a.holds else [l.get('after', 0.3) * a.after_scale for l in lines]
    k = Kokoro(os.path.join(a.models, 'kokoro-v1.0.onnx'), os.path.join(a.models, 'voices-v1.0.bin'))
    style = None
    for part in a.voice.split(','):
        nm, w = (part.split(':') + ['1'])[:2]
        v = k.get_voice_style(nm.strip()) * float(w)
        style = v if style is None else style + v
    female = a.voice.startswith(('af_', 'bf_'))
    # words the voice gets wrong: swap in the right sound (say.json), captions keep the real word
    say = {w.lower(): ph for w, ph in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'say.json'))).items() if not w.startswith('_')}

    def speak(txt, sp):
        if not any(re.search(r'\b' + re.escape(w) + r'\b', txt, re.I) for w in say):
            return k.create(txt, voice=style, speed=sp, lang=a.lang)[0]
        ph = k.tokenizer.phonemize(txt, a.lang)
        for w, fix in say.items():
            ph = ph.replace(k.tokenizer.phonemize(w, a.lang).strip(), fix)
        return k.create(ph, voice=style, speed=sp, lang=a.lang, is_phonemes=True)[0]
    if a.one_take:
        return one_take(a, lines, k, speak, female)
    takes = []
    for line in lines:
        sp = a.speed * line.get('speed', 1.0)
        segs = []
        # '...' is a held beat (0.8 s). By default a whole line is spoken in ONE take so the sentences run on
        # naturally (owner: 'take the breaths out'); --choppy splits at sentence ends like before.
        splitter = r'(\.\.\.|(?<=[.!?])\s+)' if a.choppy else r'(\.\.\.)'
        for chunk in re.split(splitter, line['text'].strip()):
            if chunk is None or not chunk.strip():
                continue
            if chunk == '...':
                segs.append(np.zeros(int(a.hold * SR))); continue
            y = speak(chunk.strip(), sp)
            segs += [squeeze(trim(y), a.max_pause), np.zeros(int(a.gap * SR))]
        takes.append(np.concatenate(segs[:-1]))
    # every line at the same loudness, so the voice never jumps between beats
    lv = [np.sqrt(np.mean(y[np.abs(y) > 0.02] ** 2)) for y in takes]
    ref_lv = float(np.median(lv))
    takes = [y * float(np.clip(ref_lv / (l + 1e-9), 0.6, 1.6)) for y, l in zip(takes, lv)]
    # tone match to the beer narrator, measured on the whole read
    ref, _ = librosa.load(a.ref, sr=SR)
    f, Lr = ltas(ref); _, Ly = ltas(np.concatenate(takes))
    diff = np.clip(sg.savgol_filter(Lr - Ly - np.mean((Lr - Ly)[(f > 300) & (f < 3000)]), 101, 2), -5, 5)
    diff[f < 70] = -12
    if a.no_match:
        diff = np.where(f < 70, -12.0, 0.0)
    fir = sg.minimum_phase(sg.firwin2(513, f / (SR / 2), 10 ** (diff / 20)), method='homomorphic')
    starts, durs, voice, t = [], [], [], 0.0
    for y, h in zip(takes, holds):
        d = LEAD + len(y) / SR + TAIL + h
        starts.append(t); durs.append(d); voice.append([t + LEAD, t + LEAD + len(y) / SR]); t += d
    out = np.zeros(int(t * SR) + SR)
    for y, (s0, _) in zip(takes, voice):
        y = sg.lfilter(fir, [1.0], y)
        # Gentle compression on a smooth envelope (5 ms attack, 120 ms release). The old fast gain rider (~20 ms) worked
        # inside each word: onsets popped through and word tails swelled, which read as broken, breathy words.
        ab = np.abs(y); env = np.zeros_like(ab); e = 0.0
        ka, kr = np.exp(-1 / (0.005 * SR)), np.exp(-1 / (0.12 * SR))
        for i_, v in enumerate(ab):
            e = ka * e + (1 - ka) * v if v > e else kr * e + (1 - kr) * v
            env[i_] = e
        th = 10 ** (-20 / 20) * np.max(env)
        y = y * np.where(env > th, (th + (env - th) / 2.5) / (env + 1e-9), 1.0)
        i = int(s0 * SR); out[i:i + len(y)] += y
    out = out[:int(t * SR)]
    os.makedirs(a.out, exist_ok=True)
    raw = os.path.join(a.out, 'narration_raw.wav')
    sf.write(raw, out / (np.max(np.abs(out)) + 1e-9) * 0.9, SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                    ('highpass=f=90,equalizer=f=300:t=o:w=1.2:g=-2.5,equalizer=f=4500:t=o:w=1.2:g=2,equalizer=f=9500:t=o:w=1:g=-2,'
                     'loudnorm=I=-16:TP=-2:LRA=15') if female else
                    'equalizer=f=450:t=o:w=1.3:g=-5,equalizer=f=150:t=o:w=1:g=2,loudnorm=I=-16:TP=-2:LRA=15',
                    '-ar', '44100', os.path.join(a.out, 'narration.wav')])
    os.unlink(raw)
    json.dump(dict(durs=durs, starts=starts, voice=voice, total=t), open(os.path.join(a.out, 'times.json'), 'w'), indent=1)
    print('ok', round(t, 2))


def one_take(a, lines, k, speak, female):
    """The whole script in one read. The model only resets its prosody at its own batch joins (about 500 phonemes), so the lines
    run on like one person talking. Beat cuts go in the quiet gap nearest where each line should end (from separate reads of the lines)."""
    sp = a.speed
    orig = k.create                                                # the model's own joins add 0.25 s after every sentence: keep them short
    k.create = lambda *aa, **kw: orig(*aa, **{**kw, 'sentence_pause': a.gap, 'clause_pause': 0.0})
    full = ' '.join(l['text'].strip() for l in lines)
    y = squeeze(trim(speak(full, sp)), a.max_pause)
    lens = np.array([len(squeeze(trim(speak(l['text'].strip(), sp)), a.max_pause)) for l in lines], float)
    exp = np.cumsum(lens)[:-1] / lens.sum() * len(y)
    env = np.convolve(np.abs(y), np.ones(240) / 240, 'same'); quiet = env < np.max(env) * 10 ** (-36 / 20)
    runs, i, n = [], 0, len(y)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            if j - i > int(0.1 * SR): runs.append((i, j))            # sentence-end gaps only (a line always ends a sentence; commas are shorter)
            i = j
        else: i += 1
    nsent = [max(1, len(re.findall(r'[.!?](?=\s|$)', l['text'].strip()))) for l in lines]
    if len(runs) == sum(nsent) - 1:                                # one long gap per sentence end: a line ends after its own sentences
        idx = np.cumsum(nsent)[:-1] - 1; cuts = [(runs[i][0] + runs[i][1]) // 2 for i in idx]; exp = []
    else:
        print(f'one-take: {len(runs)} sentence gaps for {sum(nsent) - 1} sentence ends, cutting by expected length'); cuts = []
    last = 0
    for e in exp:                                                  # the gap nearest each expected line end (and after the last cut)
        c = [r for r in runs if (r[0] + r[1]) / 2 > last + 0.4 * SR]
        r = min(c, key=lambda r: abs((r[0] + r[1]) / 2 - e))
        if abs((r[0] + r[1]) / 2 - e) > 0.8 * SR: raise SystemExit(f'one-take: no pause near line end at {e / SR:.2f}s')
        cuts.append((r[0] + r[1]) // 2); last = cuts[-1]
    bounds = [0] + cuts + [n]
    # tone match to the reference and the same gentle compression as the line-by-line path
    ref, _ = librosa.load(a.ref, sr=SR)
    f, Lr = ltas(ref); _, Ly = ltas(y)
    diff = np.clip(sg.savgol_filter(Lr - Ly - np.mean((Lr - Ly)[(f > 300) & (f < 3000)]), 101, 2), -5, 5); diff[f < 70] = -12
    if a.no_match: diff = np.where(f < 70, -12.0, 0.0)
    fir = sg.minimum_phase(sg.firwin2(513, f / (SR / 2), 10 ** (diff / 20)), method='homomorphic')
    yy = sg.lfilter(fir, [1.0], y)
    ab = np.abs(yy); env2 = np.zeros_like(ab); e_ = 0.0; ka, kr = np.exp(-1 / (0.005 * SR)), np.exp(-1 / (0.12 * SR))
    for i_, v in enumerate(ab):
        e_ = ka * e_ + (1 - ka) * v if v > e_ else kr * e_ + (1 - kr) * v
        env2[i_] = e_
    th = 10 ** (-20 / 20) * np.max(env2); yy = yy * np.where(env2 > th, (th + (env2 - th) / 2.5) / (env2 + 1e-9), 1.0)
    t_end = LEAD + n / SR + TAIL
    out = np.zeros(int(t_end * SR) + SR); out[int(LEAD * SR):int(LEAD * SR) + n] = yy; out = out[:int(t_end * SR)]
    starts, durs, voice = [], [], []
    for li in range(len(lines)):
        s0, s1 = bounds[li], bounds[li + 1]; seg = ~quiet[s0:s1]; nz = np.where(seg)[0]
        v0, v1 = LEAD + (s0 + nz[0]) / SR, LEAD + (s0 + nz[-1]) / SR
        st = 0.0 if li == 0 else LEAD + s0 / SR; en = t_end if li == len(lines) - 1 else LEAD + s1 / SR
        starts.append(st); durs.append(en - st); voice.append([v0, v1])
    os.makedirs(a.out, exist_ok=True)
    raw = os.path.join(a.out, 'narration_raw.wav')
    sf.write(raw, out / (np.max(np.abs(out)) + 1e-9) * 0.9, SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                    ('highpass=f=90,equalizer=f=300:t=o:w=1.2:g=-2.5,equalizer=f=4500:t=o:w=1.2:g=2,equalizer=f=9500:t=o:w=1:g=-2,'
                     'loudnorm=I=-16:TP=-2:LRA=15') if female else
                    'equalizer=f=450:t=o:w=1.3:g=-5,equalizer=f=150:t=o:w=1:g=2,loudnorm=I=-16:TP=-2:LRA=15',
                    '-ar', '44100', os.path.join(a.out, 'narration.wav')])
    os.unlink(raw)
    json.dump(dict(durs=durs, starts=starts, voice=voice, total=t_end), open(os.path.join(a.out, 'times.json'), 'w'), indent=1)
    print('ok one take', round(t_end, 2))


if __name__ == '__main__':
    main()
