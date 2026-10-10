#!/usr/bin/env python3
"""film_voice.py: narrate the whole film with the studio voice (style B) and write the timing the picture is cut to.

    python3 film_voice.py <folder with the Kokoro model files>   ->  narration.wav, timing.json, timing.js, notes/voice.json

Each sentence is said on its own at the pace its delivery number asks for, its inside pauses checked against the
human bands, and joined to the next with a pause of the right kind. Word times are worked out from the waveform:
the voice gives no timestamps, so each sentence's words are laid over its speech (silences skipped) by length.
That is good to roughly a fifth of a second, which is what the picture cues need.
"""
import sys, os, re, json, warnings
warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, librosa
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
import narrate as N
from assemble import align
from kokoro_onnx import Kokoro
SR = N.SR; LEAD, GAP, TAIL = 2.0, 1.25, 5.0
VOICE = 'am_michael:0.75+am_eric:0.25'; G, Hh, PACE = 2.0, 1.5, 0.05

def word_times(p, text):
    runs = N.silences(p); size = lambda w: len(re.sub(r'[^A-Za-z]', '', w)) + 4 * len(re.sub(r'[^0-9]', '', w)) + 1
    words = text.split(); wts = np.array([size(w) for w in words], float); cum = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
    durs = [b - a for a, b in runs]; total = sum(durs)
    def at(frac):
        s = frac * total
        for (a, b), d in zip(runs, durs):
            if s <= d + 1e-9: return a + s
            s -= d
        return runs[-1][1]
    return [(w, at(cum[i]), at(cum[i + 1])) for i, w in enumerate(words)]

def main(M):
    S = json.load(open(f'{HERE}/script.json')); spoken, shown, delivery = S['spoken'], S['scenes'], S['delivery']
    k = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))
    vec = sum(float(w) * k.get_voice_style(nm) for nm, w in (p.split(':') for p in VOICE.split('+')))
    say = lambda text, speed: librosa.resample(k.create(text, voice=vec, speed=speed, lang='en-us')[0].astype(np.float64), orig_sr=24000, target_sr=SR)
    speed = 0.94; rngp = np.random.default_rng(7); log = []; scenes_audio = []; scenes_words = []
    for n in range(1, len(spoken) + 1):
        sents = N.sentences(spoken[n - 1]); plan = delivery[str(n)]
        assert len(plan) == len(sents), f'scene {n}: {len(sents)} sentences, {len(plan)} delivery numbers'
        parts = [N.retime(say(text, speed * (1 + PACE * d)), text, log)[0] for (text, nxt), d in zip(sents, plan)]
        base = float(np.median([N.level(p) for p in parts])); seq = []; spans = []; t = 0.0; heard = []
        for i, (p, (text, nxt), d) in enumerate(zip(parts, sents, plan)):
            p = p * np.clip(base / N.level(p), 0.71, 1.41); spans.append((t, t + len(p) / SR, d)); seq.append(p)
            heard += [{'text': w, 'start': t + a, 'end': t + b} for w, a, b in word_times(p, text)]
            t += len(p) / SR
            if nxt == 'end': break
            want = rngp.uniform(*N.BAND['beat']) if nxt == 'beat' else rngp.uniform(0.52, 0.72)
            if plan[i + 1] <= -0.6: want += 0.22
            if d >= 0.4 and plan[i + 1] >= 0.4: want -= 0.08
            gap = max(0.05, want - 0.29); seq.append(np.zeros(int(gap * SR))); t += gap
            log.append({'scene': n, 'after': text.split()[-1], 'kind': nxt, 'now': round(want, 2)})
        scenes_audio.append(N.shape(np.concatenate(seq), spans, G, Hh)); scenes_words.append(heard)
    target = float(np.median([N.level(c) for c in scenes_audio]))
    out = [np.zeros(int(LEAD * SR))]; t = LEAD; T = []
    for i, (y, heard) in enumerate(zip(scenes_audio, scenes_words)):
        y = y * np.clip(target / N.level(y), 0.71, 1.41)
        disp = shown[i].split(); tw = align(disp, heard)
        T.append({'start': round(t + tw[0][0], 3), 'end': round(t + tw[-1][1], 3), 'words': [{'w': w, 's': round(t + s, 3), 'e': round(t + max(e, s + 0.04), 3)} for w, (s, e) in zip(disp, tw)]})
        out.append(y); t += len(y) / SR
        if i < len(scenes_audio) - 1: out.append(np.zeros(int(GAP * SR))); t += GAP
    out.append(np.zeros(int(TAIL * SR))); total = round(t + TAIL, 2)
    y = N.polish(np.concatenate(out))
    sf.write(f'{HERE}/narration.wav', y.astype(np.float32), SR, subtype='PCM_16')
    TT = {'scenes': T, 'total': total}
    json.dump(TT, open(f'{HERE}/timing.json', 'w')); open(f'{HERE}/timing.js', 'w').write('window.TIMING = ' + json.dumps(TT))
    m, pauses = N.measure(f'{HERE}/narration.wav')
    json.dump({'voice': VOICE, 'speed': speed, 'measured': m, 'breaks': log}, open(f'{HERE}/notes/voice.json', 'w'), indent=1, default=float)
    print('narration.wav', total, 's;', [round(s['end'] - s['start'], 1) for s in T]); print(m)

if __name__ == '__main__': main(sys.argv[1])
