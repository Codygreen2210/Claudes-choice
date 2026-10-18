"""Sound for the five 'how it works' Shorts (scab, wrinkle, gut, jump, bone).

    STUDIO_ROOT=... python3 howto_sound.py <name> times.json narration.wav out.wav

Music: a light, curious bed (warm pad, soft plucks, ticking hat) the whole way, seamless around the
loop, with one hard stop on each Short's big reveal and a sting on it. Effects land on the on-screen actions.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Mix

name = sys.argv[1]
M = Mix(sys.argv[2]); S = M.S; B, DUR, D = M.B, M.DUR, M.D; SR = M.SR
rng = np.random.default_rng(7)


def pop(t, n=80, db=-11):
    M.fx_(S.pop_note(n, 0.2), t, db)


def slam(t, i=3, db=-10):
    M.fx_(M.k('rooms/slam', i), t, db)


def squish(t, dur=0.5, db=-10, seed=0):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = S.bp(np.random.default_rng(seed).standard_normal(n), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * tt))
    M.fx_(S.norm(x) * M.env(n, 0.03, 0.2), t, db)


def boing(t, db=-12):
    n = int(0.5 * SR); tt = np.arange(n) / SR
    f = 200 + 400 * np.exp(-tt / 0.08) + 40 * np.sin(2 * np.pi * 12 * tt)
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.2), t, db)


def sparkle(t, db=-14):
    for j, m in enumerate((84, 88, 91, 96)):
        M.fx_(S.bell(m, 0.8, dec=0.3), t + j * 0.06, db)


def zip_(t, dur, up=True, db=-14):
    M.fx_(S.whoosh(dur, 300 if up else 3000, 3000 if up else 300), t, db)


def drips(t0, t1, db=-16):
    t = t0
    while t < t1:
        M.fx_(S.pop_note(int(rng.integers(86, 96)), 0.06), t, db, rng.uniform(-0.4, 0.4)); t += rng.uniform(0.15, 0.35)


M.swishes(-18)
M.light_score(key={'scab': 60, 'wrinkle': 62, 'gut': 57, 'jump': 64, 'bone': 59}[name], db=-21)
reveal = {'scab': 5, 'wrinkle': 4, 'gut': 2, 'jump': 5, 'bone': 0}[name]    # beat whose payoff gets a stop + sting

if name == 'scab':
    zip_(B[-1], DUR[-1] * 0.9, True, -10)                       # the slide in (loop beat) ...
    M.fx_(M.noise(0.6, 800, 5000, 3, 0.02, 0.3), -0.05, -6)      # ... scrape on frame one
    M.fx_(S.impact(0.5), 0.0, -12)
    drips(0.4, B[1], -15); pop(0.1)
    for j in range(10):
        M.fx_(S.pop_note(70 + (j % 5) * 3, 0.06), B[1] + 0.2 + j * 0.2, -15, (-0.5 if j % 2 else 0.5))
    for j in range(8):
        M.fx_(M.k('rooms/keyclick', j), B[2] + 0.2 + j * DUR[2] * 0.08, -14)
    slam(B[2] + DUR[2] * 0.5)
    zip_(B[3] + 0.1, DUR[3] * 0.8, True, -14)
    for j in range(6):
        M.fx_(S.pop_note(64, 0.08), B[4] + 0.2 + j * 0.25, -15)
    slam(B[4] + DUR[4] * 0.62, 5)
    M.fx_(M.noise(DUR[5] * 0.6, 2000, 8000, 9, 0.3, 0.3), B[5], -18)
    for j in range(5):
        M.fx_(S.pop_note(76 + j, 0.1), B[6] + 0.2 + j * DUR[6] * 0.17, -15)
    boing(B[7] + 0.4)
    M.fx_(M.noise(0.25, 1500, 6000, 12, 0.01, 0.1), B[8] + DUR[8] * 0.45, -8)  # rip
    slam(B[8] + DUR[8] * 0.55, 6, -8)
elif name == 'wrinkle':
    M.fx_(M.k('water/splash', 6), B[-1] + 0.2, -12)
    M.fx_(M.k('water/splash', 3), -0.05, -8)
    drips(0.2, B[1], -15); pop(0.2)
    for j in range(6):
        M.fx_(S.whoosh(0.3, 600, 2400), B[1] + 0.2 + j * 0.45, -17)
    M.fx_(S.bell(70, 1.2), B[2] + 0.4, -13)
    M.fx_(M.k('rooms/metal_hit', 0), B[3] + 0.5, -10)               # the cut
    slam(B[3] + DUR[3] * 0.5, 2, -12)
    zip_(B[4], DUR[4] * 0.7, False, -12); sparkle(B[4] + DUR[4] * 0.5)
    for j in range(6):
        M.fx_(S.pop_note(60 - j, 0.08), B[5] + 0.2 + j * 0.3, -15)
    squish(B[6] + 0.2, DUR[6] * 0.7, -14, 3)
    M.fx_(M.noise(DUR[7], 300, 3000, 15, 0.3, 0.3), B[7], -12)       # tire spray
    for j in range(int(DUR[8] * 1.5)):
        M.fx_(S.pop_note(88, 0.1), B[8] + j / 1.5 + 0.33, -11)       # marble lands
        M.fx_(M.tick(), B[8] + j / 1.5, -18)
elif name == 'gut':
    zip_(-0.35, 2.4, True, -8)                                          # the tube shooting out
    squish(-0.1, 0.5, -9, 1); pop(0.3, 76)
    for j in range(5):
        M.fx_(M.tick(), B[1] + 0.2 + j * DUR[1] * 0.16, -12)
    slam(B[1] + DUR[1] * 0.8, 3, -11)
    zip_(B[2], DUR[2] * 0.6, True, -12)
    for j in range(5):
        M.fx_(S.pop_note(70 + j * 2, 0.15), B[3] + 0.3 + j * 0.45, -14)
    for j in range(9):
        M.fx_(S.pop_note(80 + (j % 3), 0.06), B[4] + 0.2 + j * 0.18, -17)
    for j in range(8):
        M.fx_(S.pop_note(90, 0.06), B[5] + 0.2 + j * DUR[5] / 8, -15)
    for j in range(4):
        squish(B[6] + 0.2 + j * DUR[6] / 4, 0.5, -12, 10 + j)
    boing(B[7] + 0.4, -12)
    M.fx_(S.whoosh(0.8, 200, 1200), B[8] + 0.1, -13)
elif name == 'jump':
    for t0 in (B[-1] + DUR[-1] - 0.35,):
        M.fx_(S.riser(0.35, 300, 2500), t0, -14)
    M.fx_(S.whoosh(0.7, 200, 2500), 0.0, -8)                             # everyone leaps on frame one
    for j in range(12):
        M.fx_(S.pop_note(int(rng.integers(70, 90)), 0.05), 0.02 + j * 0.03, -18, rng.uniform(-0.8, 0.8))
    M.fx_(S.impact(1.0), 1.25, -11)                                      # landing thud
    pop(0.25)
    for j in range(20):
        M.fx_(M.tick(), B[1] + j * DUR[1] * 0.04, -17)
    M.fx_(M.k('rooms/metal_slam', 1), B[2] + 0.3, -9)
    M.fx_(S.whoosh(0.6, 200, 2500), B[3] + 0.1, -11); M.fx_(S.impact(0.6), B[3] + 0.5, -14)
    M.fx_(S.bell(64, 1.5), B[4] + 0.3, -13)
    zip_(B[5], DUR[5] * 0.6, False, -12)
    M.fx_(M.k('rooms/creak', 1), B[6] + 0.2, -11); M.fx_(S.impact(0.6), B[6] + 0.8, -12)
    M.fx_(S.impact(1.2), B[7] + DUR[7] * 0.5, -8)
    for j in range(int(DUR[8] / (np.pi / 3))):
        M.fx_(S.whoosh(0.4, 300, 2000), B[8] + j * np.pi / 3, -15)
elif name == 'bone':
    M.fx_(M.k('rooms/creak', 0), B[-1] + DUR[-1] - 1.2, -12)          # bending
    M.fx_(M.k('rooms/wood_crack', 2), 0.10, -2)                          # SNAP
    M.fx_(S.impact(0.8), 0.12, -6)
    pop(0.14, 70, -10)
    M.fx_(S.pop_note(60, 0.3), B[1] + 0.3, -12)
    squish(B[1] + 0.2, 0.8, -12, 4)
    for j in range(3):
        M.fx_(S.pop_note(55 - j * 3, 0.25), B[2] + 0.3 + j * 0.4, -13)
    for j in range(8):
        M.fx_(S.pop_note(int(rng.integers(84, 92)), 0.05), B[3] + 0.2 + j * DUR[3] / 8, -15)
    boing(B[4] + 0.3, -11)
    for j in range(4):
        M.fx_(M.k('rooms/knock', j), B[5] + 0.3 + j * DUR[5] * 0.2, -12)
    M.fx_(M.noise(1.0, 1500, 6000, 31, 0.1, 0.3), B[6] + 0.1, -14)       # cast wrap
    for j in range(int(DUR[7] / 0.52)):
        M.fx_(M.k('people/step_stone', j), B[7] + j * 0.52, -14, (-0.3 if j % 2 else 0.3))
    for j in range(int(DUR[8] / 0.3)):
        M.fx_(M.noise(0.2, 2500, 8000, 40 + j, 0.02, 0.1), B[8] + j * 0.3, -18)   # sanding

# ---- extra texture (scab, wrinkle, gut): wet squelches, chomps, crunches, rubber squeaks,
# and a soft tick on every camera punch-in ----
def squelch(t, db=-13, seed=0):
    n = int(0.35 * SR); tt = np.arange(n) / SR
    x = S.bp(np.random.default_rng(seed).standard_normal(n), 150, 1200)
    f = 300 + 500 * np.exp(-tt / 0.06)
    x = x * (0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    M.fx_(S.norm(x) * np.exp(-tt / 0.09) * np.minimum(tt / 0.008, 1), t, db)


def crunch(t, db=-12, seed=0):
    n = int(0.3 * SR); tt = np.arange(n) / SR
    g = np.random.default_rng(seed)
    x = S.bp(g.standard_normal(n), 1500, 8000) * (g.random(n) < 0.08)
    M.fx_(S.norm(np.convolve(x, np.exp(-np.arange(60) / 10.0))[:n]) * np.exp(-tt / 0.1), t, db)


def stretch(t, dur=0.7, db=-15):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = 180 + 260 * tt / dur
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dur) * (0.7 + 0.3 * np.sin(2 * np.pi * 23 * tt)), t, db)


def punches():
    for i in range(1, len(B) - 1):
        k = 1
        while k * 3.5 < DUR[i] - 0.4:
            M.fx_(S.whoosh(0.18, 900, 2600), B[i] + k * 3.5 - 0.06, -24)
            k += 1


if name in ('scab', 'wrinkle', 'gut'):
    punches()
if name == 'scab':
    for j in range(3):
        squelch(B[2] + DUR[2] * (0.2 + 0.2 * j), -14, j)                    # the plug piling up
    stretch(B[3] + 0.3, DUR[3] * 0.5, -15)                                  # sticky threads
    stretch(B[3] + DUR[3] * 0.55, DUR[3] * 0.35, -17)
    for j in range(4):
        crunch(B[5] + DUR[5] * (0.35 + 0.12 * j), -13, j)                   # scab drying hard
elif name == 'wrinkle':
    squelch(B[1] + 0.3, -15, 1)
    for j in range(3):
        stretch(B[5] + 0.3 + j * DUR[5] * 0.25, 0.4, -16)                    # blood pipes squeezing (rubbery)
    for j in range(5):
        crunch(B[6] + DUR[6] * (0.15 + 0.15 * j), -18, j)                   # skin folding
elif name == 'gut':
    for j in range(3):
        squelch(B[3] + DUR[3] * (0.2 + 0.25 * j), -15, j)                   # food sliding through
    for j in range(5):
        M.fx_(S.pop_note(48 + (j % 3) * 3, 0.12), B[5] + 0.3 + j * DUR[5] / 6, -15)   # blood soaking it up (gulps)
    for j in range(3):
        squelch(B[8] + 0.3 + j * DUR[8] * 0.25, -14, 10 + j)                 # folded up inside: gurgles


# ---- extra texture (scab, wrinkle, gut): wet squelches, crunches, rubbery stretches,
# and a soft whoosh on every camera punch-in ----
def squelch(t, db=-13, seed=0):
    n = int(0.35 * SR); tt = np.arange(n) / SR
    x = S.bp(np.random.default_rng(seed).standard_normal(n), 150, 1200)
    f = 300 + 500 * np.exp(-tt / 0.06)
    x = x * (0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    M.fx_(S.norm(x) * np.exp(-tt / 0.09) * np.minimum(tt / 0.008, 1), t, db)


def crunch(t, db=-12, seed=0):
    n = int(0.3 * SR); tt = np.arange(n) / SR
    g = np.random.default_rng(seed)
    x = S.bp(g.standard_normal(n), 1500, 8000) * (g.random(n) < 0.08)
    M.fx_(S.norm(np.convolve(x, np.exp(-np.arange(60) / 10.0))[:n]) * np.exp(-tt / 0.1), t, db)


def stretch(t, dur=0.7, db=-15):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = 180 + 260 * tt / dur
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dur) * (0.7 + 0.3 * np.sin(2 * np.pi * 23 * tt)), t, db)


if name in ('scab', 'wrinkle', 'gut'):
    for i in range(1, len(B) - 1):
        k = 1
        while k * 3.5 < DUR[i] - 0.4:
            M.fx_(S.whoosh(0.18, 900, 2600), B[i] + k * 3.5 - 0.06, -24)
            k += 1
if name == 'scab':
    for j in range(3):
        squelch(B[2] + DUR[2] * (0.2 + 0.2 * j), -14, j)                    # the plug piling up
    stretch(B[3] + 0.3, DUR[3] * 0.5, -15)                                  # sticky threads
    stretch(B[3] + DUR[3] * 0.55, DUR[3] * 0.35, -17)
    for j in range(4):
        crunch(B[5] + DUR[5] * (0.35 + 0.12 * j), -13, j)                   # scab drying hard
elif name == 'wrinkle':
    squelch(B[1] + 0.3, -15, 1)
    for j in range(3):
        stretch(B[5] + 0.3 + j * DUR[5] * 0.25, 0.4, -16)                    # blood pipes squeezing
    for j in range(5):
        crunch(B[6] + DUR[6] * (0.15 + 0.15 * j), -18, j)                   # skin folding
elif name == 'gut':
    for j in range(3):
        squelch(B[3] + DUR[3] * (0.2 + 0.25 * j), -15, j)                   # food sliding through
    for j in range(5):
        M.fx_(S.pop_note(48 + (j % 3) * 3, 0.12), B[5] + 0.3 + j * DUR[5] / 6, -15)   # gulps into the blood
    for j in range(3):
        squelch(B[8] + 0.3 + j * DUR[8] * 0.25, -14, 10 + j)                 # gurgles


# ---- house sounds, same in every Short ----
# the sound logo: two bright notes, always C then G, on the reveal
def chime(t, db=-10):
    M.fx_(S.bell(84, 1.4, dec=0.6), t, db, -0.15)
    M.fx_(S.bell(91, 1.8, dec=0.8), t + 0.13, db + 1, 0.15)


# the paper fold on every scene change: a dry paper crinkle and a soft air push
def fold(t):
    n = int(0.42 * SR); tt = np.arange(n) / SR
    x = S.bp(np.random.default_rng(int(t * 100)).standard_normal(n), 1800, 7000)
    crk = (np.random.default_rng(int(t * 100) + 1).random(n) < 0.004).astype(float)
    crk = np.convolve(crk, np.exp(-np.arange(200) / 30.0))[:n]
    env = np.exp(-((tt - 0.16) / 0.12) ** 2)
    M.fx_(S.norm(x * (0.4 + crk)) * env, t - 0.02, -19, 0.3)
    M.fx_(S.whoosh(0.4, 500, 1800), t, -24, -0.3)


# Blip's little squeak when he gets a shock
def squeak(t, db=-19):
    n = int(0.16 * SR); tt = np.arange(n) / SR
    f = 900 + 1300 * tt / 0.16
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.07) * np.minimum(tt / 0.01, 1), t, db, 0.5)


import json as _json
_lines = _json.load(open(os.path.join(os.path.dirname(sys.argv[2]), 'lines.json')))
for i in range(1, len(B) - 1):
    fold(B[i])

# the reveal: drop the bed for a beat, then the chime
rt = B[reveal] + (DUR[reveal] * 0.6 if reveal else 0.12)
chime(rt)
M.shape(rt - 0.4, rt + 0.1, -5, 0.2)
M.shape(rt + 0.1, rt + 1.0, 1.5, 0.2)
# story shape: settle down for the explaining, lift for the payoff, ease off before the loop line
M.shape(B[1], B[reveal] if reveal > 2 else B[3], -4)
M.shape(B[reveal + 1] if reveal < len(B) - 3 else B[-3], B[-3], -2.5)
M.shape(B[-3], B[-2] + DUR[-2], 1.5)
M.finish(sys.argv[3], sys.argv[4])
print('ok', name)
