"""Sound for the body Shorts (hiccup, yawn, diarrhea, gum, dream).

    STUDIO_ROOT=... python3 body_sound.py <name> times.json narration.wav out.wav

Same house sounds as the others: light bed seamless around the loop, paper fold on each scene change,
a soft whoosh on each camera punch-in, the two-note chime on the reveal. Effects land on the on-screen action.
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Mix

name = sys.argv[1]
M = Mix(sys.argv[2]); S = M.S; B, DUR, D = M.B, M.DUR, M.D; SR = M.SR
rng = np.random.default_rng(11)


def env(n, a, r):
    return M.env(n, a, r)


def squelch(t, db=-13, seed=0, dur=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = S.bp(np.random.default_rng(seed).standard_normal(n), 150, 1200)
    f = 300 + 500 * np.exp(-tt / 0.06)
    x = x * (0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    M.fx_(S.norm(x) * np.exp(-tt / (dur * 0.26)) * np.minimum(tt / 0.008, 1), t, db)


def gurgle(t, dur=1.0, db=-14, seed=0):
    g = np.random.default_rng(seed); t0 = t
    while t0 < t + dur:
        n = int(0.12 * SR); tt = np.arange(n) / SR
        f = g.uniform(120, 320) * (1 + 1.5 * tt / 0.12)
        M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.12) ** 2, t0, db + g.uniform(-4, 2))
        t0 += g.uniform(0.06, 0.16)


def crunch(t, db=-12, seed=0):
    n = int(0.3 * SR); tt = np.arange(n) / SR
    g = np.random.default_rng(seed)
    x = S.bp(g.standard_normal(n), 1500, 8000) * (g.random(n) < 0.08)
    M.fx_(S.norm(np.convolve(x, np.exp(-np.arange(60) / 10.0))[:n]) * np.exp(-tt / 0.1), t, db)


def stretch(t, dur=0.7, db=-15, f0=180, f1=440):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f0 + (f1 - f0) * tt / dur
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dur) * (0.7 + 0.3 * np.sin(2 * np.pi * 23 * tt)), t, db)


def hic(t, db=-6):
    """A hiccup: a sharp throaty click with a short voiced chirp."""
    n = int(0.22 * SR); tt = np.arange(n) / SR
    click = S.bp(np.random.default_rng(int(t * 10)).standard_normal(n), 600, 4000) * np.exp(-tt / 0.012)
    f = 260 + 180 * np.exp(-tt / 0.04)
    voice = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.05) * 0.6
    M.fx_(S.norm(click + voice), t, db)


def air(t, dur, db=-16, lo=300, hi=3000):
    M.fx_(M.noise(dur, lo, hi, int(t * 7) + 3, dur * 0.3, dur * 0.4), t, db)


def splash(t, db=-10, i=3):
    M.fx_(M.k('water/splash', i), t, db)


def pop(t, n=80, db=-12):
    M.fx_(S.pop_note(n, 0.2), t, db)


def boing(t, db=-12):
    n = int(0.5 * SR); tt = np.arange(n) / SR
    f = 200 + 400 * np.exp(-tt / 0.08) + 40 * np.sin(2 * np.pi * 12 * tt)
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.2), t, db)


def sparkle(t, db=-14):
    for j, m in enumerate((84, 88, 91, 96)):
        M.fx_(S.bell(m, 0.8, dec=0.3), t + j * 0.06, db)


def ring(t, dur, db=-13):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 22 * tt)) * np.sin(2 * np.pi * 2400 * tt) * 0.5
    M.fx_(S.bp(x, 1200, 6000) * env(n, 0.01, 0.05), t, db)


M.swishes(-18)
M.light_score(key={'hiccup': 62, 'yawn': 57, 'diarrhea': 59, 'gum': 64, 'dream': 55}[name], db=-21)
reveal = {'hiccup': 4, 'yawn': 4, 'diarrhea': 6, 'gum': 5, 'dream': 3}[name]

if name == 'hiccup':
    hic(0.0); hic(2.0, -8)
    air(B[1] + 0.3, DUR[1] * 0.8, -20)
    M.fx_(M.noise(DUR[2] * 0.7, 2000, 9000, 5, 0.1, 0.3), B[2] + 0.2, -17)   # soda fizz
    for j in range(4):
        M.fx_(S.pop_note(90 + j, 0.05), B[2] + DUR[2] * (0.5 + 0.06 * j), -16)
    M.fx_(S.impact(0.6), B[3] + 0.2, -9); air(B[3] + 0.2, 0.9, -12, 400, 5000)
    hic(B[4] + DUR[4] * 0.55, -5); M.fx_(S.impact(0.5), B[4] + DUR[4] * 0.55, -12)
    for j in range(int(DUR[5] / 0.42)):
        M.fx_(M.k('rooms/knock', j % 4), B[5] + 0.1 + j * 0.42, -13)
    for j in range(int(DUR[6] / 1.4) + 1):
        hic(B[6] + 0.2 + j * 1.4, -16)
    t, gap = B[7] + 0.05, 0.6
    while t < B[7] + DUR[7]:
        hic(t, -9 - 8 * (t - B[7]) / DUR[7]); gap += 0.5 * 0.6; t += gap
    for j in range(int(DUR[8] / 0.9) + 1):
        hic(B[8] + 0.05 + j * 0.9, -10)
    for j in range(int(DUR[8] * 8)):
        M.fx_(M.tick(), B[8] + j / 8, -20)
elif name == 'yawn':
    air(-0.35, 1.8, -10, 200, 1600)                                      # the big inhale of the yawn
    stretch(-0.2, 1.4, -20, 120, 90)
    air(B[1] + 0.1, 2.2, -12, 200, 1800)
    M.fx_(S.pop_note(76, 0.1), B[2] + 0.3, -15)
    for j in range(5):
        M.fx_(S.pop_note(84 + j, 0.08), B[2] + 0.5 + j * 0.5, -17)
    M.fx_(M.noise(DUR[3] * 0.7, 3000, 9000, 9, 0.2, 0.3), B[3] + 0.1, -22)   # oxygen hiss
    air(B[3] + DUR[3] * 0.35, 1.6, -13, 200, 1600)
    sparkle(B[4] + DUR[4] * 0.45, -13)
    air(B[5] + 0.1, DUR[5] - 0.4, -15, 200, 1800)
    M.fx_(M.noise(DUR[6], 80, 600, 12, 0.5, 0.5), B[6], -22)             # heat shimmer drone
    for j in range(3):
        air(B[7] + 0.2 + j * 0.9, 1.3, -14 - 2 * j, 200, 1600)
    air(B[8] + 0.1, 1.5, -14, 200, 1600)
    stretch(B[8] + 1.3, 1.2, -16, 500, 260)                                # the dog's squeaky yawn
elif name == 'diarrhea':
    for j in range(int((B[1]) / 0.14)):                                   # running feet
        M.fx_(M.k('people/step_stone', j), j * 0.14, -15, (-0.3 if j % 2 else 0.3))
    gurgle(0.1, 1.2, -9, 1)
    for j in range(int((DUR[-1]) / 0.14)):
        M.fx_(M.k('people/step_stone', j), B[-1] + j * 0.14, -17)
    gurgle(B[1] + 0.4, 1.0, -18, 2)
    for j in range(6):
        M.fx_(S.pop_note(92 + (j % 3), 0.05), B[2] + 0.4 + j * DUR[2] / 7, -18)
    M.fx_(S.impact(0.4), B[3] + 0.5, -14)
    for j in range(4):
        M.fx_(S.bell(60, 0.4, dec=0.15), B[3] + 0.5 + j * 0.3, -19)        # alarm blips
    M.fx_(M.noise(DUR[4], 300, 3000, 15, 0.3, 0.3), B[4], -14)           # water dumping in
    gurgle(B[4] + 0.5, DUR[4] - 0.8, -15, 4)
    for j in range(int(DUR[5] / 0.28)):
        squelch(B[5] + 0.1 + j * 0.28, -16, j)
    M.fx_(M.noise(DUR[6] - 0.4, 200, 2000, 21, 0.1, 0.3), B[6] + 0.3, -9)  # out it comes
    for j in range(5):
        squelch(B[6] + 0.4 + j * 0.3, -11, 30 + j, 0.45)
    splash(B[6] + 0.6, -13, 2)
    for j in range(5):
        M.fx_(S.pop_note(55 + (j % 2) * 3, 0.15), B[7] + 0.8 + j * 0.45, -15)   # gulps
    M.fx_(M.k('rooms/metal_hit', 0), B[8] + 0.6, -14)
    M.fx_(M.noise(2.4, 200, 3000, 33, 0.1, 1.0), B[8] + 0.65, -9)          # the flush
elif name == 'gum':
    squelch(0.0, -8, 1, 0.5); M.fx_(S.whoosh(1.4, 1200, 300), -0.2, -14)
    squelch(B[-1] + DUR[-1] - 0.3, -16, 2)
    for j in range(int(DUR[1] / 0.9)):
        stretch(B[1] + 0.2 + j * 0.9, 0.7, -14, 160, 420)
    gurgle(B[2] + 0.2, DUR[2] - 0.4, -18, 5)
    M.fx_(M.tick(), B[2] + DUR[2] * 0.5, -12)
    sparkle(B[3] + 0.3, -15); sparkle(B[3] + DUR[3] * 0.5, -17)
    for j in range(int(DUR[4] / 0.6)):
        squelch(B[4] + 0.2 + j * 0.6, -18, 40 + j)
    M.fx_(M.k('rooms/slam', 3), B[5] + DUR[5] * 0.45, -8)
    for j in range(3):
        M.fx_(M.tick(), B[6] + 0.3 + j * DUR[6] * 0.25, -15)
    M.fx_(S.whoosh(0.4, 2000, 400), B[6] + DUR[6] * 0.7, -14); splash(B[6] + DUR[6] * 0.7 + 0.4, -11, 4)
    for j in range(10):
        M.fx_(S.pop_note(78 + (j % 5) * 2, 0.08), B[7] + 0.2 + j * DUR[7] / 12, -15)
    stretch(B[8] + DUR[8] * 0.4, DUR[8] * 0.5, -12, 140, 300)
    squelch(B[8] + DUR[8] * 0.9, -10, 50, 0.5)
elif name == 'dream':
    sparkle(0.0, -11); M.fx_(S.riser(0.6, 300, 2500), -0.6, -16)
    for j in range(5):
        M.fx_(S.bell(88 + (j % 3) * 3, 1.2, dec=0.6), B[1] + 0.3 + j * 0.5, -21)
    for j in range(10):
        M.fx_(S.pop_note(int(rng.integers(84, 98)), 0.06), B[2] + 0.4 + j * DUR[2] / 11, -16)
    M.fx_(M.k('rooms/lock', 0), B[3] + 0.6, -8)                           # the lock clicks shut
    for j in range(4):
        M.fx_(S.whoosh(0.4, 600, 2000), B[4] + j * 0.4, -18)
    M.fx_(S.impact(0.6), B[5] + DUR[5] * 0.5, -10); boing(B[5] + DUR[5] * 0.55, -13)
    for j in range(int(DUR[6] / 0.5)):
        boing(B[6] + 0.2 + j * 0.5, -20)
    for j in range(5):
        sparkle(B[7] + 0.2 + j * DUR[7] * 0.16, -19)
    ring(B[8] + 0.5, 1.4, -12)
    for j in range(4):
        pop(B[8] + 0.8 + j * 0.45, 84 + j, -12)

# ---- house sounds ----
def chime(t, db=-10):
    M.fx_(S.bell(84, 1.4, dec=0.6), t, db, -0.15)
    M.fx_(S.bell(91, 1.8, dec=0.8), t + 0.13, db + 1, 0.15)


def fold(t):
    n = int(0.42 * SR); tt = np.arange(n) / SR
    x = S.bp(np.random.default_rng(int(t * 100)).standard_normal(n), 1800, 7000)
    crk = (np.random.default_rng(int(t * 100) + 1).random(n) < 0.004).astype(float)
    crk = np.convolve(crk, np.exp(-np.arange(200) / 30.0))[:n]
    env_ = np.exp(-((tt - 0.16) / 0.12) ** 2)
    M.fx_(S.norm(x * (0.4 + crk)) * env_, t - 0.02, -19, 0.3)
    M.fx_(S.whoosh(0.4, 500, 1800), t, -24, -0.3)


for i in range(1, len(B) - 1):
    fold(B[i])
    k = 1
    while k * 3.5 < DUR[i] - 0.4:
        M.fx_(S.whoosh(0.18, 900, 2600), B[i] + k * 3.5 - 0.06, -24)
        k += 1

rt = B[reveal] + DUR[reveal] * 0.6
chime(rt)
M.shape(rt - 0.4, rt + 0.1, -5, 0.2)
M.shape(rt + 0.1, rt + 1.0, 1.5, 0.2)
M.shape(B[1], B[reveal], -4)
M.shape(B[reveal + 1], B[-3], -2.5)
M.shape(B[-3], B[-2] + DUR[-2], 1.5)
M.finish(sys.argv[3], sys.argv[4])
print('ok', name)
