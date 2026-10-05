"""sound.py: the episode's soundtrack, made from the machine's own bounces (video/events.json).
Marimba-like pings for every bounce (same recipe as the page: a sine plus a short knock two octaves up),
then a quiet bed under them: a pad and long bass notes from 12 s, kick, shaker and a moving bass from 36 s. 120 BPM; marbles drop every second.
    python3 video/sound.py  ->  video/score.wav
"""
import json, os
import numpy as np, scipy.signal as sg, soundfile as sf, pyloudnorm as pyln

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 70.0
N = int(DUR * SR)
rng = np.random.default_rng(7)
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)

def place(buf, y, t, gl=1.0, gr=1.0):
    i = int(round(t * SR))
    if i >= N: return
    n = min(len(y), N - i)
    buf[0, i:i + n] += y[:n] * gl
    buf[1, i:i + n] += y[:n] * gr

def pan(p):  # -1..1, equal power
    a = (p + 1) * np.pi / 4
    return np.cos(a), np.sin(a)

def lp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'low', fs=SR, output='sos'), x, axis=-1)
def hp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'high', fs=SR, output='sos'), x, axis=-1)

# ---- pings
def ping(m, vel):
    f = mtof(m); n = int(1.3 * SR); t = np.arange(n) / SR
    dec = 0.42 if m < 72 else 0.3 if m < 84 else 0.2          # low bars ring longer
    body = np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
    octave = 0.18 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / (dec * 0.5))
    knock = 0.34 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / 0.03)
    tick = 0.5 * hp(rng.standard_normal(n), 5000) * np.exp(-t / 0.006)     # the click of glass on wood
    # a struck bar's own overtones (about 2.76x and 5.4x), short, so the note has some top to it
    bar = 0.22 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.09) + 0.16 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t / 0.05)
    y = (body + octave + knock + bar) * np.minimum(1, t / 0.002) + tick
    return y * (0.16 + 0.5 * vel)

pings = np.zeros((2, N))
events = json.load(open(os.path.join(HERE, 'events.json')))
for e in events:
    gl, gr = pan((e['x'] / 1000 - 0.5) * 1.1)
    place(pings, ping(e['midi'], e['vel']), e['t'], gl, gr)
# echo: dotted eighth, swapped sides
d = int(0.375 * SR)
wet = np.zeros_like(pings); src = pings.copy()
for k in range(1, 5):
    src = np.roll(src[::-1], d, axis=1) * 0.42; src[:, :d] = 0
    wet += src
pings = pings + lp(wet, 5000) * 0.6

# ---- bed, from 36 s. Two bars (4 s) per chord.
bed = np.zeros((2, N))
CH = {'C': ([48, 55, 60, 64, 67, 74], 36), 'Am': ([45, 52, 57, 60, 64, 72], 33), 'F': ([41, 53, 57, 60, 64, 67], 29), 'G': ([43, 50, 55, 59, 62, 69], 31)}
PLAN = [(12, 'C'), (16, 'Am'), (20, 'C'), (24, 'Am'), (28, 'C'), (32, 'Am'), (36, 'C'), (40, 'Am'), (44, 'C'), (48, 'F'), (52, 'G'), (56, 'Am'), (60, 'F'), (64, 'C')]
def pad(notes, dur):
    n = int((dur + 2.5) * SR); t = np.arange(n) / SR; y = np.zeros((2, n))
    for m in notes:
        for det, side in ((-0.06, -0.6), (0.05, 0.6), (0.0, 0.0)):
            f = mtof(m + det)
            ph = rng.uniform(0, 2 * np.pi)
            v = np.sin(2 * np.pi * f * t + ph) + 0.35 * np.sin(2 * np.pi * 2 * f * t + ph * 1.7) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
            gl, gr = pan(side); y[0] += v * gl; y[1] += v * gr
    env = np.minimum(1, t / 1.2) * np.minimum(1, np.maximum(0, (dur + 2.5 - t) / 2.5))
    trem = 1 + 0.06 * np.sin(2 * np.pi * 0.25 * t)
    return lp(y, 2600) * env * trem / (len(notes) * 3)
def bass(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    y = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
    return y * np.minimum(1, t / 0.012) * np.exp(-t / max(0.9, dur * 0.8)) * np.minimum(1, (dur - t) / 0.05)
def kick():
    n = int(0.3 * SR); t = np.arange(n) / SR
    f = 48 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)
def shaker(g):
    n = int(0.07 * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 6500) * np.exp(-t / 0.018) * g

for k, (t0, name) in enumerate(PLAN):
    notes, root = CH[name]
    last = k == len(PLAN) - 1
    p = pad(notes, 4.0 if not last else 4.5)
    place(bed, p[0] * (0.32 if t0 < 36 else 0.5), t0, 1, 0); place(bed, p[1] * (0.32 if t0 < 36 else 0.5), t0, 0, 1)
    # bass: root on 1, a push on the "and" of 2, root again on 3 (bars are 2 s, beats 0.5 s)
    for bar in range(2):
        b0 = t0 + bar * 2
        early = t0 < 36                      # before 36 s: only the pad and one long, quiet bass note per bar
        place(bed, bass(root, 1.9 if early else 0.95) * (0.5 if early else 0.8), b0, .707, .707)
        if not early and not (last and bar == 1):
            place(bed, bass(root, 0.45) * 0.5, b0 + 0.75, .707, .707)
            place(bed, bass(root + 7 if name != 'G' else root, 0.9) * 0.6, b0 + 1.0, .707, .707)
        # kick on 1 and 3, shaker on the eighths (from the second chord on, so the bed arrives in two steps)
        if t0 >= 36 and not (last and bar == 1):
            for beat in (0, 1.0): place(bed, kick() * 0.72, b0 + beat, .707, .707)
            for e in range(8):
                gl, gr = pan(0.35 if e % 2 else -0.25)
                place(bed, shaker(0.5 if e % 2 else 0.28), b0 + e * 0.25, gl, gr)
# the bed fades in over the first bar and out with the last chord
t = np.arange(N) / SR
bed *= np.clip((t - 12) / 3.0, 0, 1) * np.clip((69.6 - t) / 2.2, 0, 1)

pings = pings + hp(pings, 3000) * 2.0          # lift the top of the bars so they are not all 400 to 1500 Hz
mix = pings * 0.72 + bed
mix = hp(mix, 28)
mix *= np.clip((69.9 - t) / 1.2, 0, 1)
# loudness to -15 LUFS, then a soft ceiling at -1.5 dBTP (checked 4x oversampled)
meter = pyln.Meter(SR)
mix *= 10 ** ((-15 - meter.integrated_loudness(mix.T)) / 20)
def tp(x): return np.max(np.abs(sg.resample_poly(x, 4, 1, axis=-1)))
ceil = 10 ** (-1.5 / 20)
if tp(mix) > ceil:
    mix = np.tanh(mix / ceil * 0.9) * ceil / np.tanh(0.9) if tp(mix) < ceil * 1.6 else mix * ceil / tp(mix)
    if tp(mix) > ceil: mix *= ceil / tp(mix)
sf.write(os.path.join(HERE, 'score.wav'), mix.T, SR, subtype='PCM_24')
print('score.wav', round(meter.integrated_loudness(mix.T), 1), 'LUFS, true peak', round(20 * np.log10(tp(mix)), 2), 'dBTP')
