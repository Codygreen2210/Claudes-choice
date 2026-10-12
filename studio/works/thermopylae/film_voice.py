#!/usr/bin/env python3
"""film_voice.py: narrate a film from script.json with the studio voice and write the timing the picture is cut to.

    python3 film_voice.py <folder with the Kokoro model files> [scene numbers to say, default all]

script.json holds scenes -> lines of [delivery, spoken text, beat after?, caption text or null].
Each line is said on its own at the pace its delivery number asks for; pauses inside a line are checked
against the human bands (narrate.py); lines are joined with a pause of the right kind.
Word times come from the waveform, laid over each line's speech by word length (good to about 0.2 s).
"""
import sys, os, re, json, warnings
warnings.filterwarnings('ignore')
import numpy as np, soundfile as sf, librosa
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
import narrate as N
from assemble import align
from kokoro_onnx import Kokoro
SR = N.SR; LEAD, GAP, TAIL = 2.5, 1.3, 6.0
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
    S = json.load(open(f'{HERE}/script.json'))['scenes']
    k = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))
    vec = sum(float(w) * k.get_voice_style(nm) for nm, w in (p.split(':') for p in VOICE.split('+')))
    say = lambda text, speed: librosa.resample(k.create(text, voice=vec, speed=speed, lang='en-us')[0].astype(np.float64), orig_sr=24000, target_sr=SR)
    speed = 0.94; rngp = np.random.default_rng(11); log = []; scenes_audio = []; scenes_words = []; shown_all = []
    for n, lines in enumerate(S, 1):
        parts = [N.retime(say(text, speed * (1 + PACE * d)), text, log)[0] for d, text, beat, shown in lines]
        base = float(np.median([N.level(p) for p in parts])); seq = []; spans = []; t = 0.0; heard = []; shown_words = []
        for i, (p, (d, text, beat, shown)) in enumerate(zip(parts, lines)):
            p = p * np.clip(base / N.level(p), 0.71, 1.41); spans.append((t, t + len(p) / SR, d)); seq.append(p)
            wt = word_times(p, text); sw = (shown or text).split()
            tw = align(sw, [{'text': w, 'start': a, 'end': b} for w, a, b in wt])
            heard += [(w, t + a, t + max(b, a + 0.04)) for w, (a, b) in zip(sw, tw)]
            t += len(p) / SR
            if i == len(lines) - 1: break
            want = rngp.uniform(*N.BAND['beat']) if beat else rngp.uniform(0.52, 0.72)
            if lines[i + 1][0] <= -0.6: want += 0.22
            if d >= 0.4 and lines[i + 1][0] >= 0.4: want -= 0.08
            gap = max(0.05, want - 0.29); seq.append(np.zeros(int(gap * SR))); t += gap
        scenes_audio.append(N.shape(np.concatenate(seq), spans, G, Hh)); scenes_words.append(heard)
    target = float(np.median([N.level(c) for c in scenes_audio]))
    out = [np.zeros(int(LEAD * SR))]; t = LEAD; T = []
    for i, (y, heard) in enumerate(zip(scenes_audio, scenes_words)):
        y = y * np.clip(target / N.level(y), 0.71, 1.41)
        T.append({'start': round(t + heard[0][1], 3), 'end': round(t + heard[-1][2], 3), 'words': [{'w': w, 's': round(t + a, 3), 'e': round(t + b, 3)} for w, a, b in heard]})
        out.append(y); t += len(y) / SR
        if i < len(scenes_audio) - 1: out.append(np.zeros(int(GAP * SR))); t += GAP
    out.append(np.zeros(int(TAIL * SR))); total = round(t + TAIL, 2)
    y = N.polish(np.concatenate(out))
    sf.write(f'{HERE}/narration.wav', y.astype(np.float32), SR, subtype='PCM_16')
    TT = {'scenes': T, 'total': total}
    json.dump(TT, open(f'{HERE}/timing.json', 'w')); open(f'{HERE}/timing.js', 'w').write('window.TIMING = ' + json.dumps(TT))
    m, pauses = N.measure(f'{HERE}/narration.wav')
    json.dump({'voice': VOICE, 'speed': speed, 'measured': m, 'breaks': log}, open(f'{HERE}/notes/voice.json', 'w'), indent=1, default=float)
    print('narration.wav', total, 's;', [round(s['end'] - s['start'], 1) for s in T])

if __name__ == '__main__': main(sys.argv[1])
