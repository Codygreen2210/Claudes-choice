"""voice.py (story cut): narration where the speech sets the clock, not the pictures.
    python3 story/voice.py <dir with kokoro-v1.0.onnx and voices-v1.0.bin>  ->  story/voice.wav, story/cues.js

What changed from the first video, after Cody said the pauses and pickups needed work:
- Pauses: lines used to start wherever their caption started, so gaps ran from 0.3 s to 3 s. Now every line
  follows the one before it by a set pause (script.json: gap, paragraph_gap, or the line's own number).
- Pauses inside a line: any silence longer than 0.42 s is tightened to 0.32 s.
- Pickups: the old trim cut close to the first sound and faded in over 10 ms, which can shave a soft first
  consonant. Now 70 ms of lead-in is kept and each line is matched in level to the others, so a new line
  does not jump in louder or quieter than the last.
The pictures read cues.js and follow the voice.
"""
import sys, os, json, warnings
warnings.filterwarnings('ignore')
import numpy as np, scipy.signal as sg, soundfile as sf, librosa
from kokoro_onnx import Kokoro
HERE = os.path.dirname(os.path.abspath(__file__)); M = sys.argv[1]
SR = 48000
S = json.load(open(os.path.join(HERE, 'script.json')))
k = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))

def rms_frames(y): return librosa.feature.rms(y=y, frame_length=1024, hop_length=240)[0]

def clean(y):
    r = rms_frames(y); th = 0.02 * r.max(); on = np.where(r > th)[0]
    a = max(0, on[0] * 240 - int(0.07 * SR)); b = min(len(y), on[-1] * 240 + int(0.20 * SR))
    y = y[a:b].copy()
    # tighten long silences inside the line
    r = rms_frames(y); quiet = r < 0.02 * r.max(); out = []; i = 0; pos = 0; cuts = 0
    runs = []; start = None
    for j, q in enumerate(quiet):
        if q and start is None: start = j
        if not q and start is not None: runs.append((start, j)); start = None
    keep = np.ones(len(y), bool)
    for (a0, b0) in runs:
        d = (b0 - a0) * 240 / SR
        if a0 > 20 and d > 0.42:
            cut = int((d - 0.32) * SR); mid = (a0 + b0) // 2 * 240
            keep[mid - cut // 2: mid + cut // 2] = False; cuts += 1
    y = y[keep]
    n_in, n_out = int(0.012 * SR), int(0.10 * SR)
    y[:n_in] *= np.sin(np.linspace(0, np.pi / 2, n_in)) ** 2; y[-n_out:] *= np.cos(np.linspace(0, np.pi / 2, n_out)) ** 2
    return y, cuts

clips = []
for pi, par in enumerate(S['paragraphs']):
    for li, line in enumerate(par['lines']):
        cid, text = line[0], line[1]; gap = line[2] if len(line) > 2 else None
        y, sr = k.create(text, voice=S['voice'], speed=par.get('speed', 0.94), lang='en-us')
        y = librosa.resample(y.astype(np.float64), orig_sr=sr, target_sr=SR)
        y, cuts = clean(y)
        r = rms_frames(y); loud = np.sqrt(np.mean(r[r > 0.15 * r.max()] ** 2))
        last = li == len(par['lines']) - 1
        clips.append(dict(id=cid, p=pi, text=text, y=y, loud=loud, cuts=cuts, gap=gap if gap is not None else (S['paragraph_gap'] if last else S['gap'])))
target = np.median([c['loud'] for c in clips])
t = S['start']; cues = []
for c in clips:
    g = np.clip(target / c['loud'], 0.71, 1.41); c['y'] *= g
    c['t0'] = t; c['t1'] = t + len(c['y']) / SR - 0.20     # t1 = where the speech ends, not the tail
    t = c['t1'] + c['gap']
    cues.append(dict(id=c['id'], p=c['p'], text=c['text'], t0=round(c['t0'], 3), t1=round(c['t1'], 3)))
DUR = float(np.ceil(t + 6.0))
out = np.zeros(int(DUR * SR))
for c in clips:
    i0 = int(c['t0'] * SR); out[i0:i0 + len(c['y'])] += c['y']
# voice chain: clear rumble, a little presence, even out the level, take out some box, round the tallest peaks
out = sg.sosfilt(sg.butter(2, 85, 'high', fs=SR, output='sos'), out)
out = out + 0.25 * sg.sosfilt(sg.butter(2, [2500, 5500], 'bandpass', fs=SR, output='sos'), out)
env = np.sqrt(sg.sosfilt(sg.butter(1, 12, 'low', fs=SR, output='sos'), out ** 2) + 1e-12)
thr = np.percentile(env[env > 1e-3], 60); out = out * np.where(env > thr, (thr / env) ** 0.45, 1.0)
out = out - 0.3 * sg.sosfilt(sg.butter(2, [280, 520], 'bandpass', fs=SR, output='sos'), out)
pk = np.percentile(np.abs(out[np.abs(out) > 1e-3]), 99.7); out = np.tanh(out / pk) * pk
sf.write(os.path.join(HERE, 'voice.wav'), out, SR, subtype='PCM_24')
# mouth: how open, 24 times a second
e = np.sqrt(sg.sosfilt(sg.butter(1, 14, 'low', fs=SR, output='sos'), out ** 2) + 1e-12)
mouth = e[::SR // 24]; mouth = np.clip(mouth / np.percentile(mouth[mouth > 1e-3], 90), 0, 1)
open(os.path.join(HERE, 'cues.js'), 'w').write('// made by voice.py: when each line is spoken, and how open the mouth is 24 times a second\n(typeof window !== "undefined" ? window : globalThis).CUES = ' + json.dumps(dict(dur=DUR, cues=cues, mouth=[round(float(m), 2) for m in mouth])) + '\n')
prev = None
for c in clips:
    words = len(c['text'].split()); d = c['t1'] - c['t0']
    print(f"{c['id']:8s} {c['t0']:6.2f}-{c['t1']:6.2f}  {words / d:4.2f} w/s  gap before {0 if prev is None else c['t0'] - prev:4.2f}  tightened {c['cuts']}  {c['text'][:38]}")
    prev = c['t1']
print('duration', DUR)
