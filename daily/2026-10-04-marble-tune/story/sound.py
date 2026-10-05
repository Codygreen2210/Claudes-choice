"""sound.py (story cut): score for the long video.  python3 story/sound.py -> story/score.wav
Pings come from the machine's real bounces (events.json). Under them, a slow bed in C at 120 BPM:
C, A minor, F, G, four seconds each. Drums only where the machine or the ideas are on screen.
Everything stops for "I can't hear."
"""
import json, os
import numpy as np, scipy.signal as sg, soundfile as sf, pyloudnorm as pyln
SR = 48000; HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(HERE, 'events.json'))); CUE = E['cue']
DUR = float(E['dur']); N = int(DUR * SR); t = np.arange(N) / SR
rng = np.random.default_rng(11)
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
def place(buf, y, t0, gl=.707, gr=.707):
    i = int(round(t0 * SR))
    if i >= N or i < 0: return
    n = min(len(y), N - i); buf[0, i:i + n] += y[:n] * gl; buf[1, i:i + n] += y[:n] * gr
def pan(p): a = (p + 1) * np.pi / 4; return np.cos(a), np.sin(a)
def lp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'low', fs=SR, output='sos'), x, axis=-1)
def hp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'high', fs=SR, output='sos'), x, axis=-1)
def ramp(a, b, fade=1.0): return np.clip((t - a) / fade, 0, 1) * np.clip((b - t) / fade, 0, 1)

def ping(m, vel):
    f = mtof(m); n = int(1.3 * SR); x = np.arange(n) / SR
    dec = 0.42 if m < 72 else 0.3 if m < 84 else 0.2
    body = np.sin(2 * np.pi * f * x) * np.exp(-x / dec)
    octave = 0.18 * np.sin(2 * np.pi * 2 * f * x) * np.exp(-x / (dec * 0.5))
    knock = 0.34 * np.sin(2 * np.pi * 4 * f * x) * np.exp(-x / 0.03)
    bar = 0.22 * np.sin(2 * np.pi * 2.76 * f * x) * np.exp(-x / 0.09) + 0.16 * np.sin(2 * np.pi * 5.4 * f * x) * np.exp(-x / 0.05)
    tick = 0.5 * hp(rng.standard_normal(n), 5000) * np.exp(-x / 0.006)
    return ((body + octave + knock + bar) * np.minimum(1, x / 0.002) + tick) * (0.16 + 0.5 * vel)
pings = np.zeros((2, N))
for e in E['hits']:
    gl, gr = pan((e['x'] / 1000 - 0.5) * 1.1); place(pings, ping(e['midi'], e['vel']), e['t'], gl, gr)
d = int(0.375 * SR); wet = np.zeros_like(pings); src = pings.copy()
for k in range(1, 5):
    src = np.roll(src[::-1], d, axis=1) * 0.42; src[:, :d] = 0; wet += src
pings = pings + lp(wet, 5000) * 0.6
pings = pings + hp(pings, 3000) * 2.0

CH = {'C': ([48, 55, 60, 64, 67, 74], 36), 'Am': ([45, 52, 57, 60, 64, 72], 33), 'F': ([41, 53, 57, 60, 64, 67], 29), 'G': ([43, 50, 55, 59, 62, 69], 31)}
def pad(notes, dur):
    n = int((dur + 2.5) * SR); x = np.arange(n) / SR; y = np.zeros((2, n))
    for m in notes:
        for det, side in ((-0.06, -0.6), (0.05, 0.6), (0.0, 0.0)):
            f = mtof(m + det); ph = rng.uniform(0, 2 * np.pi)
            v = np.sin(2 * np.pi * f * x + ph) + 0.35 * np.sin(2 * np.pi * 2 * f * x + ph * 1.7) + 0.12 * np.sin(2 * np.pi * 3 * f * x)
            gl, gr = pan(side); y[0] += v * gl; y[1] += v * gr
    env = np.minimum(1, x / 1.2) * np.minimum(1, np.maximum(0, (dur + 2.5 - x) / 2.5))
    return lp(y, 2600) * env * (1 + 0.06 * np.sin(2 * np.pi * 0.25 * x)) / (len(notes) * 3)
def bass(m, dur):
    n = int(dur * SR); x = np.arange(n) / SR; f = mtof(m)
    y = np.sin(2 * np.pi * f * x) + 0.25 * np.sin(2 * np.pi * 2 * f * x) + 0.08 * np.sin(2 * np.pi * 3 * f * x)
    return y * np.minimum(1, x / 0.012) * np.exp(-x / max(0.9, dur * 0.8)) * np.minimum(1, (dur - x) / 0.05)
def kick():
    n = int(0.3 * SR); x = np.arange(n) / SR; f = 48 + 70 * np.exp(-x / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.11)
def shaker(g):
    n = int(0.07 * SR); x = np.arange(n) / SR
    return hp(rng.standard_normal(n), 6500) * np.exp(-x / 0.018) * g

harm = np.zeros((2, N)); low = np.zeros((2, N)); drums = np.zeros((2, N))
order = ['C', 'Am', 'F', 'G']
for k in range(int(DUR // 4)):
    t0 = k * 4.0; notes, root = CH[order[k % 4]]
    p = pad(notes, 4.0); place(harm, p[0] * 0.42, t0, 1, 0); place(harm, p[1] * 0.42, t0, 0, 1)
    for bar in range(2):
        b0 = t0 + bar * 2
        place(low, bass(root, 0.95) * 0.8, b0); place(low, bass(root, 0.45) * 0.5, b0 + 0.75); place(low, bass(root + 7, 0.9) * 0.6, b0 + 1.0)
        for beat in (0, 1.0): place(drums, kick() * 0.72, b0 + beat)
        for e in range(8):
            gl, gr = pan(0.35 if e % 2 else -0.25); place(drums, shaker(0.5 if e % 2 else 0.28), b0 + e * 0.25, gl, gr)
# where the rhythm plays: the three ideas and the pick, building it, the fix, and the ending
rhythm = np.maximum.reduce([ramp(CUE['brought'][0], CUE['why1'][1] + 0.5), ramp(CUE['built'][0], CUE['fail'][0] - 0.3), ramp(CUE['fix'][0] + 3.0, CUE['hear'][0] - 0.3, 0.4),
                            ramp(CUE['senses'][0] + 0.5, CUE['harmed'][1] + 0.4) * 0.6, ramp(CUE['honest'][0], CUE['bye'][1] + 2.5, 1.5)])
# the first try gets no bed at all, so the one note sits alone
bedlevel = 1 - 0.85 * ramp(CUE['bouncy'][0] - 0.3, CUE['fix'][0] + 0.8, 0.6)
bed = (harm * 0.95 + low * 0.56 * (0.35 + 0.65 * rhythm) + drums * 0.7 * rhythm) * bedlevel
q0, q1 = E['quiet']
hush = 1 - np.clip((t - q0) / 0.08, 0, 1) * np.clip((q1 - t) / 0.9, 0, 1)
mix = (pings * 0.72 + bed) * hush
mix *= np.clip(t / 1.5, 0, 1) * np.clip((DUR - 0.3 - t) / 3.0, 0, 1)
mix = hp(mix, 28)
meter = pyln.Meter(SR)
mix *= 10 ** ((-16 - meter.integrated_loudness(mix.T)) / 20)
tp = lambda x: np.max(np.abs(sg.resample_poly(x, 4, 1, axis=-1)))
ceil = 10 ** (-1.5 / 20)
knee = ceil * 0.6                                   # round off the tallest ping peaks so the whole thing can sit louder
mix = np.where(np.abs(mix) > knee, np.sign(mix) * (knee + np.tanh((np.abs(mix) - knee) / (ceil - knee)) * (ceil - knee) * 0.92), mix)
if tp(mix) > ceil: mix *= ceil / tp(mix)
sf.write(os.path.join(HERE, 'score.wav'), mix.T, SR, subtype='PCM_24')
print('score.wav', round(meter.integrated_loudness(mix.T), 1), 'LUFS, true peak', round(20 * np.log10(tp(mix)), 2), 'dBTP')
