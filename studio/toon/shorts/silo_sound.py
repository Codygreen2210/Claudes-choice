"""Sound for the silo Short: effects per beat, music, the narration on top, mixed as a circle so it loops.

    STUDIO_ROOT=<repo with studio/instruments + studio/sfx> python3 silo_sound.py times.json narration.wav out.wav

Circular mix: everything that rings past the end (pads, tails, the roar) is folded back onto the start,
and the music never fades in from silence, so the last second flows into the first with no seam.
"""
import os, sys, json, subprocess, tempfile
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('STUDIO_ROOT', os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, ROOT)
from studio.instruments import synth as S

SR = 44100
K = os.path.join(ROOT, 'studio', 'sfx', 'samples')
TM = json.load(open(sys.argv[1]))
B, DUR, D = TM['starts'], TM['durs'], TM['total']
N = int(round(D * SR))
PAD = 4 * SR                                   # room for tails, folded back onto the start
fx = np.zeros((2, N + PAD)); mus = np.zeros((2, N + PAD))


def ld(p):
    t = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ac', '1', '-ar', str(SR), t])
    x, _ = sf.read(t); os.unlink(t); return x


def k(cat, i=0):
    d = os.path.join(K, cat); fs = sorted(os.listdir(d)); return ld(os.path.join(d, fs[i % len(fs)]))


def put(buf, x, t, db, pan=0.0):
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
    a = int(t * SR) % N; b = min(N + PAD, a + x.shape[1])
    buf[:, a:b] += x[:, :b - a] * 10 ** (db / 20)


def pour(dur, bright=3000, seed=1):
    """Grain hiss: dense filtered noise with a grainy crackle."""
    n = int(dur * SR); r = np.random.default_rng(seed)
    x = S.bp(r.standard_normal(n), 800, bright)
    crackle = (r.random(n) < 0.004) * r.standard_normal(n) * 6
    return S.norm(x + S.hp(crackle, 1500)) * np.clip(np.arange(n) / (0.2 * SR), 0, 1) * np.clip((n - np.arange(n)) / (0.3 * SR), 0, 1)


def creak():
    return k('rooms/creak', 0)


room = S.lp(np.random.default_rng(3).standard_normal(N + PAD), 300)
room = room / np.max(np.abs(room))
# a steady silo hum under everything (loops cleanly: it's the same level at both ends)
fx += np.stack([room, np.roll(room, 997)]) * 10 ** (-30 / 20)

put(fx, k('rooms/metal_hit', 2), B[0] + 0.05, -14)
for j in range(4):                                        # boots thumping on grain
    put(fx, k('people/step_dirt', j), B[1] + 0.2 + j * 0.55, -10, (j % 2 - 0.5) * 0.4)
put(fx, pour(DUR[2] + DUR[3], 2600, 2), B[2] + 0.2, -14)
for j in range(10):
    put(fx, k('rooms/metal_hit', j), B[2] + 0.4 + j * 0.18, -26, 0.3)  # auger clanks
put(fx, S.whoosh(1.4, 200, 1200), B[3] + 0.4, -14)
put(fx, pour(DUR[3] + DUR[4] + DUR[5] + DUR[6] * 0.7, 4000, 3), B[3], -12)
for j in range(4):
    put(fx, S.pop_note(96, 0.05), B[4] + j * DUR[4] / 4, -16)       # timer ticks
put(fx, k('people/step_wet', 0), B[5] + 0.2, -10)
put(fx, k('people/step_wet', 1), B[5] + 0.7, -10)
put(fx, S.riser(DUR[6] * 0.7, 200, 2500), B[6], -14)
put(fx, S.impact(1.4), B[6] + DUR[6] * 0.72, -9)                    # the grain closes over
for j in range(3):                                                  # heartbeat under the chest squeeze
    hb = S.impact(0.4) * 0.8
    put(fx, hb, B[7] + 0.5 + j * 0.9, -12); put(fx, hb * 0.6, B[7] + 0.72 + j * 0.9, -15)
put(fx, k('rooms/chain', 0), B[8] + 0.2, -12)                       # rope and pulley strain
put(fx, creak(), B[8] + 0.6, -12)
put(fx, k('rooms/slam', 2), B[8] + DUR[8] * 0.62, -10)              # gauge lands on +600
put(fx, k('rooms/wood_squeak', 0), B[9] + 0.4, -14)
put(fx, k('rooms/wood_crack', 1), B[10] + DUR[10] * 0.38, -6)       # crust gives way
put(fx, pour(1.6, 2000, 5), B[10] + DUR[10] * 0.42, -6)
put(fx, S.impact(1.2), B[10] + DUR[10] * 0.45, -8)
put(fx, k('rooms/metal_slam', 0), B[11] + DUR[11] * 0.6, -9)        # tube lands
for j in range(4):
    put(fx, k('people/step_dirt', j + 2), B[12] + 0.3 + j * 0.62, -12)  # scoops
put(fx, k('rooms/metal_hit', 4), B[13] + 0.2, -10)
for j in range(3):
    put(fx, S.whoosh(0.4, 3000, 8000), B[13] + 0.3 + j * DUR[13] * 0.16, -14)  # cutter sparks
put(fx, pour(DUR[13] * 0.6, 3000, 7), B[13] + DUR[13] * 0.45, -9)

# music: one low pad that changes colour by section, never fading in from silence, so the loop point is just another bar
def pad(notes, t0, t1, db, bright=1400):
    p = S.soft_pad(notes, t1 - t0 + 0.6, a=0.35, r=0.6, bright=bright)
    put(mus, p, t0, db)

pad([45, 52, 57, 60], -0.3 % D, D, -21)                # under the hook and around the loop seam (the pre-roll wraps)
pad([45, 52, 57, 60], 0.0, B[3], -19)
pad([41, 48, 53, 56], B[3], B[7], -18, 1000)           # the sinking: darker
pad([38, 45, 50], B[7], B[11], -19, 800)               # the facts
pad([45, 52, 57, 61], B[11], D, -18, 2000)             # the rescue: lighter, and back to the hook's chord
for j in range(int((B[7] - B[3]) / 0.5)):              # pulse while sinking
    put(mus, S.kick(pitch=46, punch=90), B[3] + j * 0.5, -22)

# fold the tails past the end back onto the start
fx[:, :PAD] += fx[:, N:N + PAD]; mus[:, :PAD] += mus[:, N:N + PAD]
fx, mus = fx[:, :N], mus[:, :N]

# narration on top, everything else ducks under it
v = ld(sys.argv[2])[:N]
vo = np.zeros((2, N)); vo[:, :len(v)] += v
env = np.convolve(np.abs(vo[0]), np.ones(2205) / 2205, 'same')
act = np.convolve(np.clip(env / (np.percentile(env, 95) + 1e-9) * 3, 0, 1), np.ones(4410) / 4410, 'same')
duck = 1 - 0.55 * act
bed = S.hp(fx, 50) * duck + S.hp(mus, 60) * duck * 0.85
bed = bed / (np.max(np.abs(bed)) + 1e-9) * 0.5 + vo / (np.max(np.abs(vo)) + 1e-9) * 0.6

# story shape: quiet at the burial, back off for the facts, open up for the rescue
shape = np.zeros(N)
def seg(t0, t1, db, ramp=0.4):
    a, b = int(t0 * SR), int(t1 * SR); r = int(ramp * SR)
    w = np.zeros(N); w[a:b] = 1; shape[:] += db * np.convolve(w, np.ones(r) / r, 'same')
seg(B[6] + DUR[6] * 0.75, B[7], -4)
seg(B[7], B[10], -2)
seg(B[11], B[13] + DUR[13], 1.5)
bed = bed * 10 ** (shape / 20)
mix = np.tanh(bed / np.max(np.abs(bed)) * 0.9) / np.tanh(0.9) * 10 ** (-1.5 / 20)
out = sys.argv[3]; raw = out + '.raw.wav'
sf.write(raw, mix.T, SR)
eq = out + '.eq.wav'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'equalizer=f=450:t=o:w=1.2:g=-4,highshelf=f=5000:g=2', '-ar', '44100', eq])
# one fixed gain to -14 LUFS (no moving loudness ride, so the end and the start match at the loop point)
import pyloudnorm as pyln
y, _ = sf.read(eq)
g = 10 ** ((-14 - pyln.Meter(SR).integrated_loudness(y)) / 20)
y = y * g
pk = np.max(np.abs(y)); lim = 10 ** (-2 / 20)
if pk > lim:
    y = np.tanh(y / lim) * lim
# smooth the wrap-around: the last 10 ms ease into the first sample so a looping player doesn't click
n = int(0.01 * SR); w = np.linspace(0, 1, n)[:, None]
y[-n:] = y[-n:] * (1 - w) + y[:1] * w
sf.write(out, y, SR)
os.unlink(raw); os.unlink(eq)
print('ok', round(D, 2))
