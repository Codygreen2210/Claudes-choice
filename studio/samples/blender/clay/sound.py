# Sound for the clay demo: a bouncy plucked bed plus cartoon clay foley timed to clay.py's ball (t in seconds).
#   STUDIO_ROOT=/root/vt/kit python3 sound.py OUT.wav
import sys, os
import numpy as np, soundfile as sf
sys.path.insert(0, os.environ.get('STUDIO_ROOT', '/root/vt/kit'))
from studio.instruments import synth as S
from studio.sfx import foley as F
SR = 44100; D = 10.0; N = int(D * SR)
fx = np.zeros((2, N + 4 * SR)); mus = np.zeros((2, N + 4 * SR))
rng = np.random.default_rng(5)
def put(buf, x, t, db, pan=0.0):
    x = np.asarray(x, float)
    if x.ndim == 1: x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
    a = int(t * SR); a0 = max(a, 0); x = x[:, a0 - a:]; b = min(buf.shape[1], a0 + x.shape[1])
    buf[:, a0:b] += x[:, :b - a0] * 10 ** (db / 20)
def tt(d): return np.arange(int(d * SR)) / SR
def glide(f0, f1, d, vib=0.0, rate=7.0, shape=1.0):
    t = tt(d); k = (t / d) ** shape; f = f0 * (f1 / f0) ** k * (1 + vib * np.sin(2 * np.pi * rate * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return x * np.clip(t / 0.015, 0, 1) * np.clip((d - t) / 0.04, 0, 1)
def squish(d=0.18, f=220, seed=0):       # wet clay smoosh: a short filtered noise with a falling formant and a soft low thump
    t = tt(d); g = np.random.default_rng(seed).standard_normal(len(t))
    x = S.bp(g, 400, 5000) * np.exp(-t / (d * 0.3)) * np.clip(t / 0.004, 0, 1)
    th = np.sin(2 * np.pi * np.cumsum(f * (0.6 + 0.4 * np.exp(-t / 0.03))) / SR) * np.exp(-t / 0.05)
    return S.norm(x * 0.8 + th)
def boing(f=330, d=0.45, depth=0.25):
    t = tt(d); fr = f * (1 + depth * np.exp(-t / 0.08) * np.sin(2 * np.pi * 18 * t))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / (d * 0.35)) * np.clip(t / 0.003, 0, 1)
def chirp(m, d=0.12):
    t = tt(d); f = S.mtof(m) * (1 + 0.12 * np.sin(2 * np.pi * 30 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
def rattle(d, seed):                      # a grey clay collar knocking against the grass: little irregular taps
    t = tt(d); x = np.zeros(len(t)); r = np.random.default_rng(seed)
    for _ in range(int(d * 40)):
        i = r.integers(0, len(t) - 2000); x[i:i + 2000] += S.bp(r.standard_normal(2000), 400, 3000) * np.exp(-np.arange(2000) / 150) * r.uniform(0.3, 1)
    return S.norm(x)

# ---------------------------------------------------------------- music: a tiptoe pizzicato bed, C major, 120 bpm
beat = 0.5; prog = [[48, 52, 55, 60], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]]
mel = [72, 76, 79, 76, 77, 74, 72, 71, 69, 72, 77, 76, 74, 71, 67, 71]
for i in range(20):
    t = i * beat; c = prog[(i // 4) % 4]
    put(mus, S.pluck(c[0] if i % 2 == 0 else c[0] + 7, 0.3, bright=2600), t, -8 if i % 2 == 0 else -12)
    put(mus, S.pluck(c[1 + i % 3] + 12, 0.25, bright=4000), t + beat / 2, -15, 0.35 * (1 if i % 2 else -1))
    put(mus, S.hat(), t + beat / 2, -19, 0.25); put(mus, S.hat(), t, -24, -0.25)
for i in range(40):                       # off-beat melody, half the time on 8ths
    t = i * beat / 2
    if (i % 8) in (0, 3, 4, 6):
        put(mus, S.pluck(mel[(i // 2) % 16], 0.22, bright=7000), t, -8, -0.2)
for i in range(80):                       # shaker on 16ths for air
    put(mus, S.bp(rng.standard_normal(int(0.05 * SR)), 5000, 12000) * np.exp(-tt(0.05) / 0.012), i * beat / 4, -16 if i % 2 else -21, 0.3)
# hush the bed while the ball is underground, then open back up with the pop
env = np.ones(mus.shape[1]); tm = np.arange(mus.shape[1]) / SR
env *= 1 - 0.55 * np.clip((tm - 5.45) / 0.2, 0, 1) * np.clip((7.1 - tm) / 0.1, 0, 1)
mus *= env

# ---------------------------------------------------------------- foley, timed to the animation
put(fx, S.whoosh(0.45, 600, 2400), 0.0, -14, -0.6)
for t, m, pn in [(0.45, 67, -0.5), (1.2, 71, -0.35), (1.85, 74, -0.2)]:
    put(fx, squish(seed=int(t * 10)), t, -6, pn); put(fx, boing(S.mtof(m), 0.35, 0.12), t, -16, pn)
    put(fx, S.whoosh(0.35, 500, 1800), t + 0.15, -20, pn)
put(fx, squish(0.15, 300, 9), 2.5, -7, -0.1); put(fx, F.step(1.0, 'stone') if hasattr(F, 'step') else squish(), 2.5, -14)
put(fx, glide(520, 470, 1.4, vib=0.05, rate=4.5), 2.66, -24)            # wobble on the rim
put(fx, glide(900, 260, 0.6, shape=0.8), 3.0, -16, 0.15)                # peeks down: slide whistle down
put(fx, chirp(96, 0.06), 4.0, -16); put(fx, chirp(91, 0.05), 4.09, -18)  # blink
put(fx, glide(140, 420, 0.45, vib=0.15, rate=23), 4.3, -15)              # winding up: rubbery stretch
put(fx, S.whoosh(0.5, 300, 3000), 4.75, -10)
put(fx, squish(0.12, 240, 4), 4.75, -10)
put(fx, glide(1400, 300, 0.45, shape=1.3), 5.0, -14)                    # falling whistle into the hole
put(fx, S.bp(S.impact(0.7), 60, 6000), 5.42, -12); put(fx, squish(0.3, 120, 11), 5.42, -6)
put(fx, boing(150, 0.6, 0.35), 5.45, -12)                               # the collar wobbles
for k in range(9):                                                      # clods land around the hole
    put(fx, squish(0.07, 500 + 60 * k, 20 + k), 6.08 + 0.03 * k + rng.uniform(0, 0.12), -17, rng.uniform(-0.6, 0.6))
put(fx, S.lp(rng.standard_normal(int(1.7 * SR)), 140) * np.clip(tt(1.7) / 0.5, 0, 1) * np.clip((1.7 - tt(1.7)) / 0.2, 0, 1) * 6, 5.5, -20)  # rumble below
for k, t in enumerate([5.85, 6.2, 6.5, 6.72]):                          # muffled bounces down in the hole
    put(fx, S.lp(squish(0.2, 90, 30 + k), 600), t, -9 - 2 * k)
put(fx, rattle(0.2, 1), 6.3, -14); put(fx, rattle(0.3, 2), 6.8, -11)
put(fx, S.bp(S.impact(0.4), 60, 6000), 6.8, -17)
put(fx, S.pop_note(86, 0.15), 7.1, -8); put(fx, squish(0.12, 420, 40), 7.1, -8)   # pops out
put(fx, glide(300, 1500, 0.5, shape=0.7), 7.1, -14)
spin = S.whoosh(0.9, 800, 2600) * (0.55 + 0.45 * np.sin(2 * np.pi * 7 * tt(0.9) + 0.0))[: int(0.9 * SR)]
put(fx, spin, 7.15, -12)
put(fx, glide(1300, 380, 0.4, shape=1.2), 7.7, -18)
put(fx, S.bp(S.impact(0.5), 60, 6000), 8.1, -14); put(fx, squish(0.28, 160, 50), 8.1, -4); put(fx, boing(200, 0.5, 0.3), 8.12, -14)
for k in range(8):                                                      # dizzy birdies circling
    put(fx, chirp(93 + (k % 2) * 4, 0.1), 8.35 + k * 0.12, -17, 0.7 * np.sin(k * 1.6))
put(fx, glide(380, 330, 0.9, vib=0.08, rate=6), 8.35, -22)
put(fx, S.bp(rng.standard_normal(int(0.12 * SR)), 300, 2000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 40 * tt(0.12)))), 9.35, -16)   # shake off
put(fx, boing(440, 0.3, 0.1), 9.47, -14); put(fx, S.whoosh(0.3, 600, 2200), 9.47, -20)
put(fx, squish(0.12, 300, 60), 9.85, -8)
for k, m in enumerate([72, 76, 79, 84]): put(fx, S.bell(m, 0.6, dec=0.25), 9.85 + k * 0.03, -20)

mix = mus[:, :N] * 10 ** (-9 / 20) + fx[:, :N]
mix = S.bp(mix, 35, 16000)
mix = mix + 1.6 * S.bp(mix, 2500, 15000) - 0.5 * S.bp(mix, 200, 900)      # open the top, thin the boxy low-mids
mix[:, -int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
try:
    import pyloudnorm as pln
    L = pln.Meter(SR).integrated_loudness(mix.T); mix *= 10 ** ((-16 - L) / 20)
except Exception as e: print('loudness', e)
for _ in range(2):                          # soft-limit the peaks, then settle back on -16 LUFS
    mix = 0.8 * np.tanh(mix / 0.8)
    L = pln.Meter(SR).integrated_loudness(mix.T); mix *= 10 ** ((-16 - L) / 20)
pk = np.max(np.abs(mix))
if pk > 0.84: mix *= 0.84 / pk
sf.write(sys.argv[1], mix.T, SR); print('wrote', sys.argv[1])
