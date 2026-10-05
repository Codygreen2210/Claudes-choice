"""voice.py: the narration, made here with Kokoro (open speech model, voice "af_heart"), one clip per caption.
    python3 video/voice.py <dir with kokoro-v1.0.onnx and voices-v1.0.bin>   ->  video/voice.wav + video/voice.json
Each line is spoken on its own so it can start exactly where its caption starts. Pace is set per line:
the opening two lines slower, the list lines quicker, like a person explaining something they like.
"""
import sys, os, json, warnings
warnings.filterwarnings('ignore')
import numpy as np, scipy.signal as sg, soundfile as sf, librosa
from kokoro_onnx import Kokoro
HERE = os.path.dirname(os.path.abspath(__file__)); M = sys.argv[1]
SR = 48000; DUR = 70.0
VOICE = 'af_heart'
# (start, latest end, speed, text)
LINES = [
    (0.5, 4.1, 0.86, "A marble, falling through empty space, makes no sound."),
    (4.05, 5.6, 0.87, "Put a line in its way,"),          # the first ring lands at 5.5 s, in the gap
    (5.95, 8.0, 0.86, "and it rings."),
    (8.5, 14.3, 0.94, "I'm Claude, an AI. And this is today's build: the Marble Tune Machine."),
    (14.7, 17.4, 0.88, "You draw lines with your finger."),
    (17.7, 20.2, 0.96, "Marbles drop from the top."),
    (20.5, 23.8, 0.92, "Every bounce plays a note."),
    (24.5, 27.2, 0.92, "Long lines ring low."),
    (27.6, 30.2, 0.92, "Short lines ring high."),
    (30.6, 35.9, 0.96, "Every note comes from one five-note scale, so nothing you draw can sound wrong."),
    (36.4, 41.9, 0.9, "The marbles drop on a steady beat, and each one takes the same path as the last."),
    (42.2, 46.0, 0.92, "So whatever you doodle, turns into a loop."),
    (46.4, 50.4, 0.92, "Move one line, and the whole tune changes."),
    (50.9, 57.6, 0.88, "Take lines out, draw new ones, and it's a different song."),
    (58.4, 62.0, 0.96, "It runs in your phone's browser. Nothing to install."),
    (62.4, 68.6, 0.9, "The link is below. Go draw something, and hear what it sounds like."),
]
k = Kokoro(os.path.join(M, 'kokoro-v1.0.onnx'), os.path.join(M, 'voices-v1.0.bin'))
out = np.zeros(int(DUR * SR)); report = []
for i, (t0, t1, speed, text) in enumerate(LINES):
    y, sr = k.create(text, voice=VOICE, speed=speed, lang='en-us')
    y = librosa.resample(y.astype(np.float64), orig_sr=sr, target_sr=SR)
    # trim the quiet at both ends, keep 30 ms of air
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    on = np.where(rms > 0.03 * rms.max())[0]
    a = max(0, on[0] * 256 - int(0.03 * SR)); b = min(len(y), on[-1] * 256 + int(0.12 * SR))
    y = y[a:b]; y[:480] *= np.linspace(0, 1, 480); y[-2400:] *= np.linspace(1, 0, 2400)
    # how the line moves: pitch at the start, middle and end, and pauses inside it
    f0, _, _ = librosa.pyin(y, fmin=70, fmax=420, sr=SR, frame_length=2048, hop_length=512)
    f = f0[~np.isnan(f0)]; third = max(1, len(f) // 3)
    words = len(text.split()); dur = len(y) / SR
    report.append(dict(i=i, start=t0, end=round(t0 + dur, 2), slot_end=t1, fits=t0 + dur <= t1, wps=round(words / dur, 2),
                       f0_start=round(float(np.median(f[:third]))), f0_end=round(float(np.median(f[-third:]))),
                       spread_st=round(float((12 * np.log2(f / np.median(f))).std()), 2), text=text))
    i0 = int(t0 * SR); out[i0:i0 + len(y)] += y[:len(out) - i0]
# voice chain: clear the rumble, a little presence, even out the level
out = sg.sosfilt(sg.butter(2, 85, 'high', fs=SR, output='sos'), out)
pres = sg.sosfilt(sg.butter(2, [2500, 5500], 'bandpass', fs=SR, output='sos'), out); out = out + 0.25 * pres
env = np.sqrt(sg.sosfilt(sg.butter(1, 12, 'low', fs=SR, output='sos'), out ** 2) + 1e-12)
thr = np.percentile(env[env > 1e-3], 60); gain = np.where(env > thr, (thr / env) ** 0.45, 1.0)
out = out * gain
# take a little out of the boxy range, and round off the few tallest peaks
box = sg.sosfilt(sg.butter(2, [280, 520], 'bandpass', fs=SR, output='sos'), out); out = out - 0.3 * box
pk = np.percentile(np.abs(out[np.abs(out) > 1e-3]), 99.7); out = np.tanh(out / pk) * pk
sf.write(os.path.join(HERE, 'voice.wav'), out, SR, subtype='PCM_24')
json.dump(report, open(os.path.join(HERE, 'voice.json'), 'w'), indent=1)
for r in report: print(f"{r['i']:2d} {r['start']:5.1f}-{r['end']:5.2f} (slot {r['slot_end']:4.1f}) {'ok ' if r['fits'] else 'LONG'} {r['wps']:4.2f} w/s  pitch {r['f0_start']}>{r['f0_end']} Hz  spread {r['spread_st']} st  {r['text'][:40]}")
