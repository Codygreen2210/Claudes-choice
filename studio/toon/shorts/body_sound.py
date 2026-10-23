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
M.light_score(key={'hiccup': 62, 'yawn': 57, 'diarrhea': 59, 'gum': 64, 'dream': 55, 'twitch': 61, 'greenpoop': 58, 'fart': 63, 'regum': 64, 'candy': 57, 'flu': 59, 'clocks': 62, 'turkey': 60, 'octopus': 55, 'tattoo': 58, 'digest': 62, 'bored': 57, 'ocean': 60, 'scared': 55, 'spider': 58, 'sneeze': 57, 'ice': 56, 'nosleep': 55, 'lightning': 54, 'knuckles': 59, 'pepper': 57, 'bat': 53, 'water': 60}[name], db=-21)
reveal = {'hiccup': 4, 'yawn': 4, 'diarrhea': 6, 'gum': 5, 'dream': 3, 'twitch': 3, 'greenpoop': 6, 'fart': 3, 'regum': 5, 'candy': 5, 'flu': 5, 'clocks': 5, 'turkey': 5, 'octopus': 4, 'tattoo': 5, 'digest': 7, 'bored': 5, 'ocean': 7, 'scared': 8, 'spider': 7, 'sneeze': 6, 'ice': 5, 'nosleep': 7, 'lightning': 6, 'knuckles': 7, 'pepper': 7, 'bat': 6, 'water': 6}[name]

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

def flutter(t, dur, db=-14, rate=7.0):
    """The twitch: tiny dry ticks in uneven bursts, matching the lid jumps."""
    k = 0
    while k / rate < dur:
        g = np.random.default_rng(k)
        if g.random() > 0.3:
            M.fx_(S.pop_note(int(g.integers(90, 98)), 0.03), t + k / rate, db + g.uniform(-4, 0))
            M.fx_(M.tick(), t + k / rate + 0.02, db - 4)
        k += 1


def zap(t, db=-14):
    n = int(0.18 * SR); tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * (900 + 600 * np.random.default_rng(int(t * 50)).random()) * tt)) * np.exp(-tt / 0.05)
    M.fx_(S.bp(x, 800, 6000) * 0.5, t, db)


def toot(t, dur=0.6, db=-8, f0=95, seed=0):
    """A cartoon fart: a low buzzy reed that wobbles and drops."""
    n = int(dur * SR); tt = np.arange(n) / SR
    g = np.random.default_rng(seed)
    f = f0 * (1 + 0.25 * np.sin(2 * np.pi * g.uniform(5, 9) * tt) + 0.15 * g.standard_normal(n).cumsum() / np.sqrt(n)) * (1 - 0.3 * tt / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sign(np.sin(ph)) * 0.4 + np.sin(ph * 2) * 0.3
    x = S.bp(x + 0.3 * g.standard_normal(n), 60, 1400)
    M.fx_(S.norm(x) * np.minimum(tt / 0.02, 1) * np.minimum((dur - tt) / 0.08, 1), t, db)


if name == 'twitch':
    flutter(0.0, B[1] - 0.2, -11)
    flutter(B[-1] + DUR[-1] - 0.45, 0.45, -14)
    for j in range(2):
        stretch(B[1] + DUR[1] * (0.45 + 0.15 * j), 0.3, -17, 300, 200)        # the blink squeeze
    for j in range(int(DUR[2] / 0.5)):
        M.fx_(S.pop_note(84 + (j % 3) * 2, 0.06), B[2] + 0.3 + j * 0.5, -18)
    for j in range(6):
        zap(B[3] + 0.4 + j * DUR[3] / 7, -13)
    flutter(B[3] + 0.6, DUR[3] - 0.8, -15, 6)
    flutter(B[4] + 0.05, DUR[4] - 0.2, -9, 9)
    for j in range(int(DUR[4] / 0.6)):
        zap(B[4] + j * 0.6, -17)
    M.fx_(S.pop_note(60, 0.2), B[5] + 0.2, -13); M.fx_(M.noise(0.6, 2000, 7000, 3, 0.1, 0.3), B[5] + 0.3, -20)   # coffee pour
    M.fx_(S.bell(88, 0.6, dec=0.2), B[5] + DUR[5] * 0.25 + 0.1, -16)              # phone ding
    M.fx_(S.pop_note(96, 0.08), B[5] + DUR[5] * 0.5 + 0.1, -15)                    # dry eye drop
    flutter(B[6] + 0.2, DUR[6] - 0.4, -18, 8)
    flutter(B[7] + 0.05, DUR[7] * 0.7, -14, 7)
    sparkle(B[7] + DUR[7] * 0.8, -14)
    for j in range(3):
        air(B[8] + 0.6 + j * 1.2, 1.0, -22, 150, 800)                            # slow sleepy breaths
elif name == 'greenpoop':
    M.fx_(S.impact(0.4), 0.0, -12); boing(0.05, -11)
    M.fx_(M.noise(1.2, 100, 900, 2, 0.4, 0.4), B[-1], -24)
    for j in range(8):
        M.fx_(S.pop_note(86 + (j % 4), 0.05), B[1] + 0.3 + j * DUR[1] / 9, -18)    # bile drips
    for j in range(5):
        squelch(B[2] + 0.2 + j * DUR[2] / 6, -15, j, 0.25)                        # the squirt
    gurgle(B[3] + 0.3, DUR[3] - 0.6, -18, 3)
    for j in range(4):
        M.fx_(S.pop_note(70 - j * 2, 0.15), B[4] + 0.3 + j * DUR[4] / 5, -16)
    for j in range(int(DUR[5] / 0.28)):
        squelch(B[5] + 0.1 + j * 0.28, -17, 20 + j)
    M.fx_(S.whoosh(0.5, 2000, 300), B[6] + 0.3, -14); splash(B[6] + 0.85, -9, 2)
    M.fx_(S.pop_note(52, 0.3), B[7] + 0.4, -14); sparkle(B[7] + DUR[7] * 0.45, -15)
    M.fx_(S.impact(0.5), B[8] + DUR[8] * 0.5, -12); boing(B[8] + DUR[8] * 0.52, -12)
elif name == 'fart':
    toot(-0.05, 0.9, -6, 90, 1)
    M.fx_(S.whoosh(0.6, 300, 1200), 0.0, -16)
    for j in range(int(DUR[1] / 0.4)):
        M.fx_(S.pop_note(int(rng.integers(80, 92)), 0.05), B[1] + 0.2 + j * 0.4, -18)
    for j in range(5):
        air(B[2] + 0.2 + j * 0.5, 0.35, -18, 300, 2500)                           # gulps of air
    M.fx_(S.pop_note(96, 0.2), B[3] + 0.5, -10)
    crunch(B[4] + 0.1, -10, 3)                                                    # the egg cracks
    stretch(B[4] + 0.5, 1.2, -18, 160, 120)
    gurgle(B[5] + 0.2, DUR[5] - 0.4, -14, 8)
    for j in range(4):
        M.fx_(S.pop_note(76 + j * 3, 0.1), B[6] + 0.2 + j * 0.45, -15)
        toot(B[6] + 0.35 + j * 0.45, 0.18, -20, 140 + j * 20, 10 + j)
    t = B[7] + 0.05
    j = 0
    while t < B[7] + DUR[7] - 0.3:
        toot(t, 0.25, -13, 100 + 25 * (j % 4), 20 + j); t += 0.8; j += 1
    stretch(B[8] + 0.3, DUR[8] * 0.5, -16, 200, 260)                              # holding it in, straining
    toot(B[8] + DUR[8] * 0.6, 1.1, -7, 75, 33)

elif name == 'regum':
    M.fx_(S.whoosh(0.6, 400, 2400), -0.45, -12)
    for j in range(int(B[1] / 0.35)):
        squelch(0.3 + j * 0.35, -18, j, 0.2)                                     # chewing
    for j in range(5):
        M.fx_(S.pop_note(92 + j % 3, 0.05), B[1] + 0.3 + j * DUR[1] / 6, -17)
    M.fx_(M.noise(DUR[1] - 0.4, 3000, 9000, 4, 0.2, 0.3), B[1] + 0.2, -24)    # acid fizz
    for j in range(8):
        M.fx_(S.pop_note(84 - j, 0.06), B[2] + 0.2 + j * DUR[2] / 9, -18)
    for j in range(int(DUR[3] / 0.35)):
        squelch(B[3] + 0.1 + j * 0.35, -16, 10 + j, 0.2)
    M.fx_(M.noise(DUR[4] - 0.3, 300, 2500, 6, 0.4, 0.4), B[4] + 0.1, -18)    # spit wash
    for j in range(6):
        M.fx_(S.bell(88 + (j % 3) * 2, 0.5, dec=0.15), B[5] + 0.2 + j * DUR[5] * 0.1, -18)
    sparkle(B[6] + 0.3, -15)
    M.fx_(S.impact(0.4), B[7] + DUR[7] * 0.4, -10)
    for j in range(int(DUR[8] / 0.18)):
        M.fx_(M.noise(0.12, 3000, 9000, 50 + j, 0.01, 0.05), B[8] + 0.6 + j * 0.18, -22)   # brushing
elif name == 'candy':
    for j in range(24):
        M.fx_(S.pop_note(int(rng.integers(72, 96)), 0.05), -0.1 + j * 0.06, -16, rng.uniform(-0.7, 0.7))   # candy tumbling out
    M.fx_(M.noise(0.6, 1500, 6000, 1, 0.05, 0.4), -0.2, -16)                   # wrapper crinkle
    M.fx_(M.noise(0.5, 1500, 6000, 2, 0.05, 0.3), B[-1] + DUR[-1] - 0.6, -18)
    gurgle(B[1] + 0.2, DUR[1] - 0.4, -20, 2)
    for j in range(10):
        M.fx_(S.pop_note(84 + (j % 4), 0.05), B[2] + 0.5 + j * 0.25, -17)
    for j in range(4):
        M.fx_(S.whoosh(0.3, 500, 2500), B[3] + 0.2 + j * 0.3, -18)
    stretch(B[4] + 0.3, 1.0, -17, 160, 120)
    M.fx_(M.k('rooms/slam', 3), B[5] + DUR[5] * 0.5, -9)
    for j in range(6):
        boing(B[6] + 0.3 + j * 0.35, -20)
    for j in range(8):
        M.fx_(S.pop_note(int(rng.integers(76, 92)), 0.05), B[7] + 0.2 + j * 0.3, -16)
    for j in range(7):
        M.fx_(M.tick(), B[8] + 0.2 + j * DUR[8] * 0.1, -13)
elif name == 'flu':
    M.fx_(M.noise(0.25, 300, 4000, 1, 0.01, 0.2), 0.0, -6); M.fx_(S.impact(0.4), 0.0, -12)   # ACHOO
    air(B[-1] + DUR[-1] - 0.8, 0.75, -14, 300, 2000)                           # the wind-up breath
    for j in range(4):
        M.fx_(S.pop_note(60 + j * 2, 0.15), B[1] + 0.5 + j * 0.4, -14)
    for j in range(int(DUR[2] / 0.4)):
        M.fx_(M.k('rooms/metal_hit', j), B[2] + 0.2 + j * 0.4, -21)          # factory clanks
    stretch(B[3] + 0.3, DUR[3] * 0.55, -16, 120, 300)
    M.fx_(S.impact(0.8), B[3] + DUR[3] * 0.6, -6)
    for j in range(8):
        ring(B[4] + 0.2 + j * 0.25, 0.15, -18)                                 # alarm
    M.fx_(M.noise(DUR[5], 60, 400, 9, 0.5, 0.5), B[5], -20)
    M.fx_(M.noise(DUR[6], 80, 700, 12, 0.5, 0.5), B[6], -22)                  # heat shimmer
    for j in range(4):
        M.fx_(S.whoosh(0.3, 800, 2000), B[7] + 0.4 + j * 0.6, -20)
    sparkle(B[8] + DUR[8] * 0.6, -14)
elif name == 'clocks':
    t = -0.1
    while t < B[1] - 0.2:
        M.fx_(M.tick(), t, -10); t += 0.09                                     # hands whirring backward
    for j in range(int(DUR[-1] / 0.5)):
        M.fx_(M.tick(), B[-1] + j * 0.5, -16)
    sparkle(B[1] + DUR[1] * 0.5, -16)
    for j in range(int(DUR[2] / 0.8)):
        M.fx_(S.bell(76 if j % 2 == 0 else 69, 0.8, dec=0.4), B[2] + 0.2 + j * 0.8, -20)
    for j in range(6):
        M.fx_(S.bell(91, 0.4, dec=0.15), B[3] + 0.3 + j * 0.3, -21)
    ring(B[4] + 0.3, 1.0, -13)                                                 # too-early alarm
    for j in range(int(DUR[5] / 0.5)):
        M.fx_(M.tick(), B[5] + j * 0.5, -17)
    M.heartbeat(B[7], B[7] + DUR[7], 80, 110, -12)
    M.fx_(M.noise(DUR[8], 80, 500, 14, 0.6, 0.6), B[8], -24)
elif name == 'turkey':
    M.fx_(M.k('rooms/soft_hit', 0), 0.05, -8); boing(0.08, -14)                # flop onto the couch
    for j in range(int(DUR[-1] / 0.45)):
        M.fx_(M.k('people/step_stone', j), B[-1] + j * 0.45, -18)
    M.fx_(M.noise(DUR[1] - 0.3, 2000, 8000, 3, 0.3, 0.3), B[1] + 0.1, -22)    # sizzle
    M.fx_(M.k('rooms/slam', 2), B[2] + 0.4, -14)
    for j in range(4):
        M.fx_(S.pop_note(72 + j * 2, 0.1), B[3] + 0.2 + j * 0.35, -15)
    for j in range(6):
        M.fx_(M.k('rooms/knock', j), B[4] + 0.3 + j * 0.4, -18)
    for j in range(5):
        M.fx_(M.k('rooms/soft_hit', j), B[5] + 0.2 + j * 0.25, -14)            # plates stacking
    gurgle(B[6] + 0.3, DUR[6] - 0.6, -16, 5)
    for j in range(3):
        M.fx_(S.pop_note(76 + j * 4, 0.15), B[7] + 0.3 + j * DUR[7] * 0.25, -14)
    for j in range(int(DUR[8] * 6)):
        M.fx_(M.tick(), B[8] + j / 6, -20)
elif name == 'octopus':
    M.fx_(S.whoosh(0.9, 200, 1500), -0.2, -9)
    for j in range(10):
        M.fx_(S.pop_note(int(rng.integers(84, 96)), 0.05), 0.1 + j * 0.08, -18)   # bubbles
    for j in range(9):
        M.fx_(S.bell(72 + j, 0.4, dec=0.15), B[1] + 0.3 + j * DUR[1] / 10, -19)  # brains lighting up one by one
    for j in range(3):
        squelch(B[2] + 0.3 + j * DUR[2] * 0.25, -16, j, 0.3)
    M.heartbeat(B[3], B[3] + DUR[3], 70, 70, -13)
    M.heartbeat(B[4], B[4] + DUR[4] * 0.45, 70, 70, -13)
    M.fx_(S.whoosh(0.8, 300, 1500), B[4] + DUR[4] * 0.45, -12)
    for j in range(8):
        M.fx_(S.pop_note(80 + (j % 3), 0.05), B[5] + 0.2 + j * DUR[5] / 9, -18)
    for j in range(int(DUR[6] * 3)):
        M.fx_(S.whoosh(0.15, 1200, 3000), B[6] + j / 3, -21)
    for j in range(6):
        M.fx_(S.bell(80 + (j * 5) % 12, 0.5, dec=0.2), B[7] + 0.3 + j * 0.35, -19)
    for j in range(3):
        M.fx_(M.k('rooms/creak', j), B[8] + 0.3 + j * 0.5, -16)
    M.fx_(M.k('rooms/metal_hit', 1), B[8] + DUR[8] * 0.6, -13)

elif name == 'tattoo':
    def buzz(t, dur, db=-14):
        n = int(dur * SR); tt = np.arange(n) / SR
        x = np.sign(np.sin(2 * np.pi * 120 * tt)) * 0.5 + 0.3 * np.sin(2 * np.pi * 240 * tt)
        M.fx_(S.bp(x, 100, 3000) * np.minimum(tt / 0.03, 1) * np.minimum((dur - tt) / 0.05, 1), t, db)
    buzz(0.0, B[1] - 0.1, -12)
    buzz(B[1], DUR[1] - 0.2, -14); buzz(B[2], DUR[2] * 0.75, -16)
    for j in range(10):
        M.fx_(S.pop_note(60 + (j % 3), 0.05), B[2] + 0.3 + j * DUR[2] * 0.07, -18)
    for j in range(8):
        ring(B[3] + 0.3 + j * 0.3, 0.12, -20)
    for j in range(8):
        squelch(B[4] + 0.3 + j * DUR[4] * 0.06, -16, j, 0.2)
    M.fx_(S.whoosh(1.2, 2000, 300), B[5] + 0.1, -14)
    M.fx_(S.impact(0.4), B[6] + 0.9, -14); squelch(B[6] + 1.4, -14, 22, 0.4)
    for j in range(4):
        M.fx_(M.tick(), B[7] + 0.4 + j * DUR[7] * 0.2, -14)
    M.fx_(M.noise(DUR[8], 100, 800, 31, 0.6, 0.6), B[8], -24)
    for j in range(int(DUR[8] * 3)):
        M.fx_(M.tick(), B[8] + j / 3, -21)
elif name == 'digest':
    M.fx_(S.whoosh(0.7, 300, 1600), -0.75, -14)
    crunch(0.0, -6, 1); squelch(0.08, -12, 2, 0.3)                              # the big bite
    M.fx_(S.whoosh(0.8, 1600, 300), B[1] + 0.3, -13); M.fx_(S.pop_note(48, 0.3), B[1] + 1.0, -12)   # gulp
    gurgle(B[2] + 0.2, DUR[2] - 0.4, -13, 3)
    for j in range(int(DUR[3] / 0.5)):
        squelch(B[3] + 0.2 + j * 0.5, -18, 10 + j, 0.25)
    for j in range(10):
        M.fx_(S.pop_note(84 + j % 4, 0.05), B[4] + 0.2 + j * DUR[4] / 11, -17)
    for j in range(3):
        stretch(B[5] + 0.4 + j * 0.6, 0.5, -20, 120, 90)                            # snores of a lazy lump
    for j in range(int(DUR[6] / 0.5)):
        M.fx_(M.tick(), B[6] + j * 0.5, -15)
    for j in range(int(DUR[7] * 4)):
        M.fx_(M.tick(), B[7] + j / 4, -20)
    sparkle(B[8] + DUR[8] * 0.7, -15)

elif name == 'bored':
    for j in range(int(DUR[0] / 0.9)):
        M.fx_(S.bell(96, 0.4, dec=0.3), B[0] + j * 0.9, -19)                    # radar pings, first one on frame one
    for j in range(int(DUR[1] * 0.6 / 0.3)):
        M.fx_(S.pop_note(81, 0.12), B[1] + DUR[1] * 0.4 + j * 0.3, -15)         # warning beeps
    M.fx_(S.whoosh(0.5, 400, 1800), B[2] + 0.2, -15)
    for j in range(int(DUR[3] / 0.17)):
        M.fx_(M.tick(), B[3] + j * 0.17, -21)                                    # fidget tapping
    stretch(B[3] + 0.2, DUR[3] * 0.6, -18, 520, 140)                             # dopamine drains away
    for j in range(int(DUR[4])):
        M.fx_(M.tick(), B[4] + j, -15)                                           # the clock in the empty room
    for j in range(int(DUR[5] / 1.1) + 1):
        zap(B[5] + j * 1.1, -15)
    for j in range(4):
        M.fx_(S.pop_note(76 + 3 * j, 0.08), B[6] + j * 0.5 + 0.2, -17)          # thought bubbles
    sparkle(B[6] + DUR[6] * 0.55, -16)
    for j in range(7):
        M.fx_(S.pop_note(79 + j, 0.07), B[7] + 0.1 + j * DUR[7] * 0.7 / 6, -16)  # ideas pop in

elif name == 'ocean':
    def slurp(t, dur, db=-20, rate=6.0, seed=3):
        n = int(dur * SR); tt = np.arange(n) / SR
        x = S.bp(np.random.default_rng(seed).standard_normal(n), 500, 2600)
        am = (0.5 + 0.5 * np.sin(2 * np.pi * rate * tt + np.sin(2 * np.pi * 1.3 * tt))) ** 2
        M.fx_(S.norm(x * am) * env(n, 0.05, 0.15), t, db)

    def gulp(t, db=-18):
        M.fx_(S.pop_note(45, 0.22), t, db); M.fx_(S.pop_note(52, 0.12), t + 0.06, db - 4)

    slurp(0.0, DUR[0] - 0.1, -21)                                               # straw sucking from frame one
    gulp(1.1); gulp(2.2)
    gulp(B[1] + 0.1, -16)
    for q in range(14):
        M.fx_(S.pop_note(96 + q % 4, 0.03), B[1] + 0.3 + q * 0.12, -23)        # salt grains landing
    stretch(B[2] + 0.5, DUR[2] * 0.65, -21, 420, 160)                            # cells squeezing down
    for q in range(10):
        M.fx_(S.pop_note(84 + (q % 3) * 3, 0.05), B[2] + 0.5 + q * 0.4, -21)    # water drips leaving
    stretch(B[3] + 0.1, DUR[3] * 0.55, -21, 200, 520)                            # meters rising
    zap(B[3] + DUR[3] * 0.6, -19)                                                # can't keep up
    air(B[4] + 0.2, DUR[4] * 0.7, -24, 300, 1500)                                # pouring out
    for q in range(6):
        M.fx_(S.pop_note(80 + q, 0.05), B[4] + 0.4 + q * 0.4, -22)
    slurp(B[5], DUR[5] * 0.5, -24, rate=4.0, seed=5)
    M.heartbeat(B[5] + 0.3, B[5] + DUR[5] - 0.2, 70, 125, -23)                  # body struggling
    M.fx_(S.whoosh(0.9, 2400, 300), B[6] - 0.1, -17)                             # zoom out to the planet
    for q in range(12):
        M.fx_(M.tick(), B[6] + 0.2 + q * DUR[6] * 0.5 / 12, -22)
    for q in range(int(DUR[7] / 0.12)):
        M.fx_(M.tick(), B[7] + q * 0.12, -29)                                    # time-lapse clock
    splash(B[8] + 0.15, -16, 4)                                                  # flush
    for q in range(6):
        M.fx_(S.pop_note(88 + (q % 2) * 2, 0.04), B[8] + 0.6 + q * 0.45, -22)  # rain drops

elif name == 'scared':
    M.fx_(S.whoosh(0.35, 3200, 300), -0.25, -18)                                # ghost lunging out
    M.fx_(S.bell(84, 0.9, dec=0.4), 0.0, -18, -0.2); M.fx_(S.bell(85, 0.9, dec=0.4), 0.0, -18, 0.2)   # the jump-scare stab
    M.fx_(S.pop_note(38, 0.25), 0.02, -15)
    M.heartbeat(0.3, B[1] - 0.1, 120, 130, -21)
    for q in range(int((DUR[1] - 0.6) / 0.32)):
        M.fx_(S.pop_note(88 if q % 2 else 84, 0.12), B[1] + 0.6 + q * 0.32, -24)   # the alarm
    zap(B[2] + 0.1, -21)
    air(B[2] + 0.8, DUR[2] * 0.7, -26, 1500, 6000)                              # adrenaline pouring
    for q in range(10):
        M.fx_(S.pop_note(86 + q % 3, 0.04), B[2] + 0.9 + q * 0.32, -23)
    M.heartbeat(B[3], B[3] + DUR[3], 105, 125, -20)
    stretch(B[3] + 1.4, 0.6, -23, 200, 420)                                      # pupils opening
    stretch(B[3] + 2.6, 0.7, -23, 150, 300)                                      # muscle pumping up
    gurgle(B[4] + 0.1, DUR[4] * 0.5, -21, 7)
    M.fx_(S.pop_note(40, 0.2), B[4] + 0.45, -17)                                 # STOP
    splash(B[4] + DUR[4] * 0.62, -19, 3)                                         # the toilet, later
    M.heartbeat(B[5], B[5] + DUR[5], 120, 175, -19)                              # adrenaline climbing
    for q in range(int(DUR[6] / 0.45)):
        M.fx_(S.pop_note(96, 0.06), B[6] + q * 0.45 + (0.12 * np.sin(q * 3) if q > 3 else 0), -22)   # monitor beeps going wild
    air(B[6] + 0.2, DUR[6] * 0.6, -27, 3000, 9000)                               # calcium fizz
    for q in range(int(DUR[7] / 0.35)):
        M.fx_(S.pop_note(90 if q % 2 else 86, 0.14), B[7] + q * 0.35, -25)      # police siren
        M.fx_(M.tick(), B[7] + q * 0.35 + 0.17, -24)                             # running feet
    crunch(B[8] + 1.2, -17, 5); M.fx_(S.pop_note(36, 0.3), B[8] + 1.2, -16)      # prison bars slam
    M.fx_(S.bell(60, 1.0, dec=0.5), B[8] + 1.22, -20)

elif name == 'spider':
    def skitter(t, dur, db=-25, rate=14.0, seed=7):
        """Tiny leg taps: a spider walking."""
        g = np.random.default_rng(seed); k = 0
        while k / rate < dur:
            M.fx_(S.pop_note(int(g.integers(97, 101)), 0.02), t + k / rate + g.uniform(0, 0.02), db + g.uniform(-3, 0))
            k += 1

    def snore(t, dur=1.2, db=-22):
        n = int(dur * SR); tt = np.arange(n) / SR
        x = S.bp(np.random.default_rng(int(t * 10)).standard_normal(n), 80, 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 38 * tt))
        M.fx_(S.norm(x) * np.sin(np.pi * tt / dur) ** 2, t, db)

    skitter(0.0, DUR[0] - 0.1, -25)                                              # spider walking on frame one
    skitter(B[9] + 0.1, DUR[9] - 0.1, -25, seed=8)                               # and in the run-up to the loop
    snore(0.6, 1.3, -24); snore(B[9] + 0.3, 1.2, -25)
    for q in range(8):
        M.fx_(S.pop_note(70 + (q % 3) * 3, 0.06), B[1] + q * DUR[1] * 0.75 / 8 + 0.2, -22)   # spiders plopping in
    M.fx_(M.rumble(DUR[2] - 0.2), B[2] + 0.1, -22)                               # the mountain shaking
    M.heartbeat(B[3] + 0.1, B[3] + DUR[3] - 0.1, 72, 72, -23)
    snore(B[3] + DUR[3] * 0.5, DUR[3] * 0.45, -22)
    for q in range(5):
        M.fx_(S.whoosh(0.5, 200, 700), B[4] + q * DUR[4] / 5, -25)               # waves rolling in
    zap(B[4] + DUR[4] * 0.5, -21)                                                # danger
    M.fx_(S.whoosh(0.9, 600, 3200), B[5] + DUR[5] * 0.2, -19)                    # the breath blast
    for q in range(12):
        M.fx_(M.tick(), B[6] + 0.1 + q * DUR[6] * 0.92 / 12, -24)                # months flipping
    skitter(B[6] + DUR[6] * 0.12 * 0.92, DUR[6] * 0.28, -26, seed=9)
    skitter(B[6] + DUR[6] * 0.55 * 0.92, DUR[6] * 0.3, -26, seed=10)
    for q in range(5):
        M.fx_(S.pop_note(86 + q, 0.04), B[7] + DUR[7] * (0.15 + 0.07 * q), -23)  # question marks
    M.fx_(S.impact(0.4), B[7] + DUR[7] * 0.6, -19)                               # the stamp
    skitter(B[8] + DUR[8] * 0.3, DUR[8] * 0.65, -25, seed=11)                    # walking off

elif name == 'sneeze':
    END = B[-1] + DUR[-1]
    stretch(B[9] + 0.3, DUR[9] - 0.9, -23, 300, 700)                             # the "ahh" building before the loop
    M.fx_(S.impact(0.3), END - 0.12, -21)                                        # hand slaps onto his nose
    M.fx_(M.noise(DUR[0] - 0.2, 150, 900, 3, 0.2, 0.3), 0.05, -27)              # muffled strain on frame one
    for q in range(10):
        M.fx_(S.pop_note(95 + q % 4, 0.03), B[1] + 0.3 + q * 0.25, -25)         # dust tickle
    sparkle(B[1] + DUR[1] * 0.45, -23)
    zap(B[2] + 0.1, -21); zap(B[2] + DUR[2] * 0.3, -22)                          # nerve signal
    M.fx_(S.impact(0.4), B[2] + DUR[2] * 0.5, -20)                               # chest clamps
    M.fx_(M.noise(0.8, 1500, 9000, 4, 0.01, 0.6), B[3] + 0.05, -17)             # ACHOO spray
    for q in range(8):
        M.fx_(S.pop_note(90 + q % 3, 0.03), B[3] + 0.6 + q * 0.18, -26)
    stretch(B[4] + 0.2, DUR[4] * 0.8, -23, 160, 320)                             # pressure building
    for q in range(5):
        M.fx_(S.whoosh(0.35, 400, 1800), B[4] + 0.3 + q * 0.6, -26)
    for q in range(4):
        M.fx_(S.whoosh(0.4, 300, 2200), B[5] + 0.1 + q * DUR[5] / 4, -24)        # air ramming up
    stretch(B[6] + DUR[6] * 0.15, DUR[6] * 0.5, -22, 200, 800)                   # needle swinging
    crunch(B[7] + 0.2, -20)                                                      # the tear
    for q in range(7):
        M.fx_(M.tick(), B[7] + DUR[7] * 0.55 + q * DUR[7] * 0.45 * 0.8 / 7, -24)  # days ticking by
    stretch(B[8] + 0.1, DUR[8] * 0.35, -23, 300, 900)
    pop(B[8] + DUR[8] * 0.45, 76, -19)                                           # eardrum pop

elif name == 'ice':
    END = B[-1] + DUR[-1]
    for q in range(5):
        M.fx_(S.pop_note(60 + q % 2, 0.05), B[9] + 0.1 + q * 0.32, -26)          # footsteps on the ice
    crunch(B[9] + DUR[9] - 0.95, -27); crunch(END - 0.35, -24)                   # creak, then CRACK
    splash(0.05, -21, 4)                                                         # the plunge on frame one
    M.fx_(M.noise(1.2, 120, 900, 5, 0.05, 0.6), 0.1, -28)                       # water churning
    M.fx_(M.noise(0.5, 600, 5000, 6, 0.02, 0.3), B[1] + DUR[1] * 0.4, -23)      # the gasp
    for q in range(4):
        M.fx_(S.pop_note(78 + q, 0.05), B[2] + DUR[2] * 0.3 + q * 0.45, -23)    # water gurgling in
    for q in range(int(DUR[3] / 0.25)):
        M.fx_(M.tick(), B[3] + q * 0.25, -26)                                    # stopwatch
    for q in range(10):
        M.fx_(M.tick(), B[4] + q * DUR[4] * 0.85 / 10, -24)                      # minutes counting up
    stretch(B[5] + 0.1, DUR[5] * 0.55, -26, 220, 660)                            # clock spinning to an hour
    for q in range(6):
        splash(B[6] + 0.3 + q * 0.4, -27, 2)                                     # kicking
    M.fx_(S.whoosh(0.8, 300, 1400), B[6] + DUR[6] * 0.5, -22)                    # sliding out
    for q in range(3):
        M.fx_(S.whoosh(0.4, 500, 1500), B[7] + 0.2 + q * 0.8, -25)               # rolling
    for q in range(3):
        pop(B[8] + DUR[8] * (0.35 + 0.2 * q), 80 + q * 3, -20)                  # the three cards

elif name == 'nosleep':
    END = B[-1] + DUR[-1]
    stretch(B[9] + 0.2, DUR[9] - 0.7, -26, 300, 160)                             # nodding off
    M.fx_(S.impact(0.3), END - 0.25, -22); boing(END - 0.22, -24)                # the jolt awake
    for q in range(int(DUR[0] / 0.12)):
        M.fx_(M.tick(), q * 0.12, -29)                                           # fast clock ticking
    stretch(B[1] + 0.4, DUR[1] * 0.7, -24, 500, 160)                             # brain winding down
    for q in range(4):
        sparkle(B[2] + 0.4 + q * DUR[2] / 4, -25)                                # things that aren't there
    for q in range(3):
        t0 = B[3] + 0.455 + q * 1.3
        M.fx_(S.whoosh(0.3, 1200, 200), t0, -24); M.fx_(S.impact(0.2), t0 + 0.39, -25)   # blink out, snap back
    for q in range(29):
        M.fx_(M.tick(), B[4] + q * DUR[4] * 0.8 / 29, -26)                       # 30-second timer
    stretch(B[5] + 0.3, DUR[5] * 0.8, -25, 260, 200)                             # the wobble
    for q in range(11):
        M.fx_(S.pop_note(84 + q % 4, 0.04), B[7] + q * DUR[7] * 0.55 / 11, -23) # calendar flipping
    M.fx_(M.noise(DUR[8] * 0.6, 100, 600, 7, 0.4, 0.6), B[8] + 0.3, -29)        # snoring breath

elif name == 'lightning':
    END = B[-1] + DUR[-1]
    M.fx_(M.noise(DUR[9], 2000, 9000, 9, 0.3, 0.1), B[9], -30)                  # rain before the loop
    M.fx_(M.noise(DUR[0], 2000, 9000, 10, 0.05, 0.4), 0.0, -30)                 # rain on frame one
    M.fx_(M.rumble(1.6, f=38), B[9] + 0.6, -25)                                  # far-off thunder
    M.fx_(S.impact(0.5), END - 0.32, -21)                                        # the strike (just before frame one)
    M.fx_(M.rumble(2.0, f=32, seed=5), 0.05, -21)                                # the thunder crack rolling on
    for q in range(8):
        zap(0.2 + q * 0.22, -26)                                                 # crackles around him
    M.fx_(M.noise(DUR[1] - 0.2, 600, 6000, 11, 0.2, 0.3), B[1] + 0.1, -26)      # the bolt sizzling
    stretch(B[1] + 0.2, DUR[1] * 0.7, -24, 200, 900)                             # the counter climbing
    stretch(B[2] + 0.2, DUR[2] * 0.6, -25, 300, 700)
    for q in range(6):
        zap(B[3] + 0.2 + q * 0.3, -24)                                           # current racing through
    boing(B[4] + 0.1, -22)
    for q in range(2):
        M.fx_(S.whoosh(0.5, 800, 2400), B[4] + 0.4 + q * 0.2, -24)              # shoes flying
    M.heartbeat(B[5] + 0.1, B[5] + DUR[5] * 0.45, 72, 72, -23)
    zap(B[5] + DUR[5] * 0.45, -20)
    for q in range(9):
        pop(B[6] + DUR[6] * (0.35 + 0.05 * q), 84 + q % 3, -24)                  # thumbs popping up
    stretch(B[7] + 0.2, DUR[7] * 0.6, -25, 250, 600)                             # the fern spreading
    for q in range(3):
        M.fx_(M.tick(), B[8] + DUR[8] * (0.4 + 0.18 * q), -24)                   # days going by

elif name == 'knuckles':
    END = B[-1] + DUR[-1]

    def crack_(t, db=-21):
        M.fx_(S.pop_note(88, 0.03), t, db); M.fx_(M.tick(), t + 0.01, db - 2)
    t = END - 0.15
    while t < END:
        crack_(t); t += 0.32
    t = 0.17
    while t < DUR[0]:
        crack_(t); t += 0.32                                                     # the hand popping from frame one
    zap(B[1] + 0.3, -26)
    for q in range(4):
        M.fx_(S.pop_note(80 + q, 0.05), B[2] + 0.4 + q * 0.6, -26)              # fluid sloshing
    stretch(B[3] + 0.1, DUR[3] * 0.55, -24, 200, 500)                            # pulling apart
    pop(B[3] + DUR[3] * 0.6, 82, -19)                                            # the bubble pop
    for q in range(10):
        M.fx_(M.tick(), B[4] + q * DUR[4] * 0.85 / 10, -26)                      # timer
    sparkle(B[5] + 0.4, -24)                                                     # the doctor's idea
    for q in range(int(DUR[6] / 1.28) + 1):
        for j in range(4):
            if q * 1.28 + j * 0.32 < DUR[6]:
                crack_(B[6] + q * 1.28 + j * 0.32, -24)
    for q in range(16):
        M.fx_(M.tick(), B[7] + q * DUR[7] * 0.5 / 16, -25)                       # counter running
    for q in range(5):
        sparkle(B[8] + 0.3 + q * 0.5, -24)                                       # confetti

elif name == 'pepper':
    END = B[-1] + DUR[-1]
    stretch(B[9] + 0.3, DUR[9] - 0.9, -27, 300, 420)                             # lifting the pepper
    crunch(END - 0.3, -22)                                                       # the bite
    M.fx_(M.noise(DUR[0] - 0.1, 400, 3000, 12, 0.1, 0.4), 0.05, -26)            # flames whooshing
    for q in range(3):
        M.fx_(S.whoosh(0.5, 600, 2400), 0.2 + q * 0.8, -25)
    stretch(B[1] + 0.3, DUR[1] * 0.6, -24, 200, 900)                             # the heat bar climbing
    for q in range(8):
        M.fx_(S.pop_note(86 + q % 4, 0.04), B[2] + 0.2 + q * 0.4, -26)          # capsaicin drops
    for q in range(2):
        M.fx_(M.tick(), B[3] + DUR[3] * 0.4 + q * 0.05, -22)                     # sensors clicking on
    zap(B[3] + DUR[3] * 0.45, -23)
    for q in range(5):
        M.fx_(S.pop_note(78 + q, 0.05), B[4] + 0.3 + q * 0.7, -26)               # sweat drips
    M.fx_(M.noise(0.6, 300, 2000, 13, 0.05, 0.3), B[5] + 0.2, -27)               # water pour
    zap(B[5] + DUR[5] * 0.4, -23)                                                # NOPE
    M.fx_(M.noise(0.6, 200, 1500, 14, 0.05, 0.3), B[6] + 0.2, -27)               # milk glug
    sparkle(B[6] + DUR[6] * 0.35, -23)
    stretch(B[7] + 0.2, DUR[7] * 0.55, -23, 500, 180)                            # arteries squeezing
    for q in range(4):
        zap(B[7] + DUR[7] * 0.45 + q * 0.4, -25)
    stretch(B[8] + 0.2, DUR[8] * 0.6, -25, 200, 500)                             # opening back up

elif name == 'bat':
    END = B[-1] + DUR[-1]

    def flaps(t0, dur, db=-25, rate=8.0):
        k = 0
        while k / rate < dur:
            M.fx_(S.whoosh(0.09, 300, 1400), t0 + k / rate, db); k += 1
    flaps(B[9] + 0.2, DUR[9] - 0.55, -26)                                         # wings beating in
    M.fx_(S.pop_note(62, 0.06), END - 0.35, -23)                                 # soft landing
    flaps(0.0, 0.5, -27, 10.0)
    M.fx_(M.noise(DUR[0], 100, 500, 15, 0.3, 0.3), 0.0, -31)                    # him snoring
    stretch(B[1] + 0.2, DUR[1] * 0.7, -26, 600, 1400)                            # heat-vision hum
    flaps(B[1] + 0.3, DUR[1] * 0.7, -28)
    for q in range(6):
        M.fx_(M.tick(), B[2] + 0.3 + q * 0.12, -27)                              # hairs snipped
    sparkle(B[2] + DUR[2] * 0.6, -24)                                            # teeth glint
    for q in range(6):
        M.fx_(S.pop_note(88 + q % 3, 0.04), B[3] + DUR[3] * 0.3 + q * 0.35, -26)  # draculin drops
    for q in range(int(DUR[4] / 0.2)):
        M.fx_(S.pop_note(92, 0.025), B[4] + 0.1 + q * 0.2, -28)                  # lap lap lap
    stretch(B[5] + 0.2, DUR[5] * 0.7, -24, 180, 420)                             # swelling up
    for q in range(2):
        M.fx_(S.whoosh(1.2, 400, 200), B[6] + q * DUR[6] * 0.45, -27)            # nights passing
    for q in range(3):
        M.fx_(S.pop_note(70, 0.06), B[7] + 0.5 + q * 0.6, -25)                   # sharing
    sparkle(B[7] + DUR[7] * 0.7, -26)
    for q in range(3):
        M.fx_(S.pop_note(74, 0.06), B[8] + 0.5 + q * 0.6, -25)
    sparkle(B[8] + DUR[8] * 0.7, -26)

elif name == 'water':
    END = B[-1] + DUR[-1]

    def glug(t, db=-22):
        M.fx_(S.pop_note(48, 0.12), t, db); M.fx_(S.pop_note(55, 0.08), t + 0.05, db - 4)
    M.fx_(S.whoosh(0.4, 300, 1200), B[9] + DUR[9] - 0.9, -25)                   # swinging the jug up
    t = END - 0.3
    while t < END:
        glug(t); t += 0.28
    t = 0.0
    while t < DUR[0] - 0.1:
        glug(t + 0.02); t += 0.28                                                # glug glug glug from frame one
    for q in range(10):
        M.fx_(S.pop_note(80 + q % 3, 0.04), B[1] + 0.2 + q * 0.3, -27)          # water pouring in
    M.fx_(S.pop_note(86, 0.05), B[1] + DUR[1] * 0.6, -24)                       # the trickle out
    M.fx_(M.noise(DUR[2] - 0.2, 300, 2500, 16, 0.3, 0.3), B[2] + 0.1, -28)      # flood rush
    for q in range(8):
        M.fx_(M.tick(), B[3] + 0.3 + q * 0.3, -27)                               # salt spreading
    stretch(B[4] + 0.2, DUR[4] * 0.75, -24, 180, 380)                            # cells ballooning
    for q in range(4):
        M.fx_(S.pop_note(70 + q * 3, 0.06), B[5] + DUR[5] * (0.1 + 0.18 * q), -24)  # symptoms popping up
    stretch(B[6] + 0.2, DUR[6] * 0.6, -23, 160, 300)                             # brain pressing out
    M.heartbeat(B[7] + 0.1, B[7] + DUR[7] - 0.1, 90, 120, -25)                   # alarm pulse
    for q in range(int(DUR[8] / 0.25)):
        M.fx_(S.pop_note(60, 0.03), B[8] + q * 0.25, -29)                        # footsteps


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


import kit as _kit


try:
    _DIVE = getattr(__import__(name), 'DIVE', {})          # the Short's dive cuts, for the hybrid style
except Exception:
    _DIVE = {}


def cut_sound(t, i=0):
    """The sound of a cut, matched to the house cut style (kit.CUT)."""
    style = _kit.CUT if _kit.CUT != 'hybrid' else ('dive' if i in _DIVE else 'punch')
    if style == 'punch':                       # a tight whoosh into a soft low hit
        M.fx_(S.whoosh(0.16, 700, 3000), t - 0.14, -21)
        M.fx_(S.pop_note(38, 0.18), t, -21)
    elif style == 'dive':                         # rising rush into the point, air on the landing
        M.fx_(S.whoosh(0.32, 250, 3600), t - 0.22, -18)
        M.fx_(S.pop_note(36, 0.22), t + 0.01, -22)
    elif style == 'whip':
        M.fx_(S.whoosh(0.24, 3200, 400), t - 0.12, -19)
    else:
        fold(t)


for i in range(1, len(B)):
    cut_sound(B[i], i)
    k = 1
    while k * 3.5 < DUR[i] - 0.4:
        M.fx_(S.whoosh(0.18, 900, 2600), B[i] + k * 3.5 - 0.06, -24)
        k += 1

rt = B[reveal] + DUR[reveal] * 0.6
chime(rt, -19)                                    # brand chime, kept under the voice
M.shape(rt - 0.4, rt + 0.1, -4, 0.2)              # small dip before the reveal; the bed stays steady otherwise
M.finish(sys.argv[3], sys.argv[4])
print('ok', name)
