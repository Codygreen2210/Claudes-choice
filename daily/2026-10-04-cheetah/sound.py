"""sound.py: score for "How a cheetah runs".  python3 sound.py -> score.wav
A bed in D minor at 112 BPM (D minor, C, B flat, C), hand drums when she is running, and a soft clay thump on
every footfall (events.json, from the same clock the pictures use): four thumps a stride in slow motion,
a low patter at full speed.
"""
import json, os
import numpy as np, scipy.signal as sg, soundfile as sf, pyloudnorm as pyln
SR = 48000; HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(HERE, 'events.json'))); CUE = E['cue']
DUR = float(E['dur']); N = int(DUR * SR); t = np.arange(N) / SR
rng = np.random.default_rng(23); BEAT = 60 / 112
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
def place(buf, y, t0, gl=.707, gr=.707):
    i = int(round(t0 * SR))
    if i >= N or i < 0: return
    n = min(len(y), N - i); buf[0, i:i + n] += y[:n] * gl; buf[1, i:i + n] += y[:n] * gr
def pan(p): a = (p + 1) * np.pi / 4; return np.cos(a), np.sin(a)
def lp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'low', fs=SR, output='sos'), x, axis=-1)
def hp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'high', fs=SR, output='sos'), x, axis=-1)
def ramp(a, b, fade=1.0): return np.clip((t - a) / fade, 0, 1) * np.clip((b - t) / fade, 0, 1)
def pad(notes, dur):
    n = int((dur + 2.0) * SR); x = np.arange(n) / SR; y = np.zeros((2, n))
    for m in notes:
        for det, side in ((-0.06, -0.6), (0.05, 0.6), (0.0, 0.0)):
            f = mtof(m + det); ph = rng.uniform(0, 2 * np.pi)
            v = np.sin(2 * np.pi * f * x + ph) + 0.35 * np.sin(2 * np.pi * 2 * f * x + ph * 1.7) + 0.12 * np.sin(2 * np.pi * 3 * f * x)
            gl, gr = pan(side); y[0] += v * gl; y[1] += v * gr
    env = np.minimum(1, x / 1.0) * np.minimum(1, np.maximum(0, (dur + 2.0 - x) / 2.0))
    return lp(y, 2600) * env / (len(notes) * 3)
def bass(m, dur):
    n = int(dur * SR); x = np.arange(n) / SR; f = mtof(m)
    y = np.sin(2 * np.pi * f * x) + 0.25 * np.sin(2 * np.pi * 2 * f * x) + 0.08 * np.sin(2 * np.pi * 3 * f * x)
    return y * np.minimum(1, x / 0.012) * np.exp(-x / max(0.7, dur * 0.8)) * np.minimum(1, (dur - x) / 0.05)
def mallet(m, vel=0.6):
    f = mtof(m); n = int(0.9 * SR); x = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * x) * np.exp(-x / 0.22) + 0.3 * np.sin(2 * np.pi * 4 * f * x) * np.exp(-x / 0.03) + 0.2 * np.sin(2 * np.pi * 2.76 * f * x) * np.exp(-x / 0.08)
    return (y * np.minimum(1, x / 0.002) + 0.3 * hp(rng.standard_normal(n), 5000) * np.exp(-x / 0.006)) * vel
def drum(pitch, dec=0.16, tone=1.0):           # a hand drum: a pitched skin plus a slap of noise
    n = int(0.4 * SR); x = np.arange(n) / SR; f = pitch * (1 + 0.5 * np.exp(-x / 0.02))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / dec) * tone + 0.25 * lp(hp(rng.standard_normal(n), 900), 5000) * np.exp(-x / 0.02))
def shaker(g):
    n = int(0.07 * SR); x = np.arange(n) / SR
    return hp(rng.standard_normal(n), 6500) * np.exp(-x / 0.018) * g
def thump(v):                                   # a paw landing on a clay table
    n = int(0.25 * SR); x = np.arange(n) / SR; f = 70 + 60 * np.exp(-x / 0.02)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.07) + 0.5 * lp(rng.standard_normal(n), 1800) * np.exp(-x / 0.012)) * v

harm = np.zeros((2, N)); low = np.zeros((2, N)); perc = np.zeros((2, N)); tune = np.zeros((2, N)); feet = np.zeros((2, N))
CH = [([50, 57, 62, 65, 69], 38), ([48, 55, 60, 64, 67], 36), ([46, 53, 58, 62, 65], 34), ([48, 55, 60, 64, 67], 36)]
BAR = BEAT * 4; SCALE = [62, 65, 67, 69, 72, 74, 77]
for k in range(int(DUR // BAR) + 1):
    t0 = k * BAR; notes, root = CH[k % 4]
    p = pad(notes, BAR); place(harm, p[0] * 0.42, t0, 1, 0); place(harm, p[1] * 0.42, t0, 0, 1)
    place(low, bass(root, BEAT * 1.9) * 0.8, t0); place(low, bass(root, BEAT * 0.9) * 0.5, t0 + BEAT * 2.5); place(low, bass(root + 7, BEAT * 0.9) * 0.5, t0 + BEAT * 3)
    # hand drums: low on 1 and the "and" of 2, high slaps between, shaker on the eighths
    for b, pch, g in [(0, 110, 0.4), (1.5, 110, 0.32), (2, 170, 0.42), (3, 170, 0.46), (3.5, 220, 0.34)]: place(perc, drum(pch) * g, t0 + b * BEAT, *pan(-0.2 if pch < 100 else 0.3))
    for e in range(8): place(perc, shaker(0.8 if e % 2 else 0.45), t0 + e * BEAT / 2, *pan(0.4 if e % 2 else -0.3))
    # a small mallet figure that walks the chord
    for i, st in enumerate([0, 2, 4, 2, 5, 4, 2, 1]):
        m = notes[1 + (st % 4)] + 12; place(tune, mallet(m, 0.34 + 0.1 * (i % 4 == 0)), t0 + i * BEAT / 2, *pan(0.5 * np.sin(i)))
for f in E['falls']:
    slow = f['rate'] < 1.2
    place(feet, thump(0.9 if slow else 0.28) * (1.0 if f['foot'] < 2 else 0.8), f['t'], *pan(-0.2 if f['foot'] < 2 else 0.25))
running = np.maximum.reduce([ramp(CUE['go'][0] + 0.4, CUE['slow'][0] + 0.2, 0.5), ramp(CUE['turn'][0], CUE['grip'][1] + 0.3, 0.6), ramp(CUE['short'][0], CUE['short'][0] + 4.5, 0.5)])
calm = np.maximum.reduce([ramp(CUE['slow'][0] + 0.5, CUE['turn'][0], 1.0), ramp(CUE['myth'][0], CUE['sum'][0], 1.0)])
melody = np.maximum.reduce([ramp(0.5, CUE['go'][0], 1.0) * 0.7, running, ramp(CUE['sum'][0], CUE['bye'][1] + 3, 1.0)])
tune = tune + hp(tune, 3000) * 2.0; perc = perc + hp(perc, 4000) * 1.5      # lift the tops so it is not all thud
mix = harm * 0.62 + low * (0.21 + 0.12 * running) + perc * (running * 0.8 + calm * 0.2) + tune * (melody * 0.9 + calm * 0.5) + feet * 0.6
mix *= np.clip(t / 1.2, 0, 1) * np.clip((DUR - 0.3 - t) / 3.0, 0, 1)
mix = hp(mix, 28)
meter = pyln.Meter(SR); mix *= 10 ** ((-16 - meter.integrated_loudness(mix.T)) / 20)
tp = lambda x: np.max(np.abs(sg.resample_poly(x, 4, 1, axis=-1))); ceil = 10 ** (-1.5 / 20); knee = ceil * 0.6
mix = np.where(np.abs(mix) > knee, np.sign(mix) * (knee + np.tanh((np.abs(mix) - knee) / (ceil - knee)) * (ceil - knee) * 0.92), mix)
if tp(mix) > ceil: mix *= ceil / tp(mix)
sf.write(os.path.join(HERE, 'score.wav'), mix.T, SR, subtype='PCM_24')
print('score.wav', round(meter.integrated_loudness(mix.T), 1), 'LUFS, true peak', round(20 * np.log10(tp(mix)), 2), 'dBTP')
