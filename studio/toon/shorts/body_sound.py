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


HYPE = ('ele', 'g9', 'foot', 'cramp', 'robot', 'stone', 'torn', 'cabin', 'crush')                 # fun science Shorts: the upbeat bed (kit.hype_score) instead of the light one
M.swishes(-18)
(M.light_score if name not in HYPE else (lambda **k: None))(key={'hiccup': 62, 'yawn': 57, 'diarrhea': 59, 'gum': 64, 'dream': 55, 'twitch': 61, 'greenpoop': 58, 'fart': 63, 'regum': 64, 'candy': 57, 'flu': 59, 'clocks': 62, 'turkey': 60, 'octopus': 55, 'tattoo': 58, 'digest': 62, 'bored': 57, 'ocean': 60, 'scared': 55, 'spider': 58, 'sneeze': 57, 'ice': 56, 'nosleep': 55, 'lightning': 54, 'knuckles': 59, 'pepper': 57, 'bat': 53, 'water': 60, 'contacts': 56, 'lava': 52, 'blackhole': 50, 'quicksand': 57, 'avalanche': 52, 'mold': 60, 'elevator': 55, 'sink': 57, 'bleach': 56, 'gum3d': 62, 'diesel': 55, 'plane': 53, 'estop': 55, 'yellowstone': 52, 'heartstop': 50, 'afterdeath': 48, 'dogchoc': 57, 'choke': 53, 'grease': 55, 'fryer': 54, 'energy': 56, 'cola': 57, 'monoxide': 53, 'starve': 52, 'brokenheart': 50, 'bruise': 58, 'screens': 57, 'moon': 52, 'sled': 55, 'jet': 50, 'af447': 48, 'tackle': 50, 'coaster': 52, 'heli': 50, 'grizzly': 50, 'campbell': 50, 'campbellx': 50, 'acid': 52, 'clock': 48, 'ele': 57, 'g9': 57, 'foot': 55, 'cramp': 53, 'robot': 57, 'stone': 50, 'torn': 45, 'cabin': 50, 'crush': 45}[name], db=-21)
reveal = {'hiccup': 4, 'yawn': 4, 'diarrhea': 6, 'gum': 5, 'dream': 3, 'twitch': 3, 'greenpoop': 6, 'fart': 3, 'regum': 5, 'candy': 5, 'flu': 5, 'clocks': 5, 'turkey': 5, 'octopus': 4, 'tattoo': 5, 'digest': 7, 'bored': 5, 'ocean': 7, 'scared': 8, 'spider': 7, 'sneeze': 6, 'ice': 5, 'nosleep': 7, 'lightning': 6, 'knuckles': 7, 'pepper': 7, 'bat': 6, 'water': 6, 'contacts': 6, 'lava': 5, 'blackhole': 6, 'quicksand': 5, 'avalanche': 8, 'mold': 8, 'elevator': 7, 'sink': 3, 'bleach': 7, 'gum3d': 7, 'diesel': 7, 'plane': 8, 'estop': 8, 'yellowstone': 8, 'heartstop': 5, 'afterdeath': 8, 'dogchoc': 6, 'choke': 5, 'grease': 4, 'fryer': 4, 'energy': 5, 'cola': 4, 'monoxide': 5, 'starve': 5, 'brokenheart': 4, 'bruise': 4, 'screens': 6, 'moon': 7, 'sled': 6, 'jet': 7, 'af447': 9, 'tackle': 5, 'coaster': 7, 'heli': 7, 'grizzly': 8, 'campbell': 12, 'campbellx': 11, 'acid': 8, 'clock': 9, 'ele': 11, 'g9': 10, 'foot': 4, 'cramp': 4, 'robot': 6, 'stone': 7, 'torn': 7, 'cabin': 7, 'crush': 8}[name]

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

elif name == 'contacts':
    END = B[-1] + DUR[-1]
    for q in range(4):
        M.fx_(M.tick(), B[9] + 0.2 + q * 0.5, -28)                               # phone scroll taps
    stretch(END - 0.6, 0.5, -27, 400, 200)                                       # eyes getting heavy
    M.fx_(M.noise(DUR[0], 100, 500, 17, 0.4, 0.3), 0.1, -31)                    # breathing asleep
    sparkle(0.15, -26)                                                           # lens glint
    for q in range(6):
        M.fx_(S.pop_note(86 + q % 3, 0.04), B[1] + 0.3 + q * 0.5, -27)          # oxygen bubbles
    M.fx_(S.whoosh(0.6, 900, 300), B[2] + 0.1, -25)                              # the lid closing
    for q in range(4):
        M.fx_(S.pop_note(78, 0.04), B[2] + DUR[2] * 0.4 + q * 0.5, -27)         # bubbles bouncing off
    for q in range(6):
        squelch(B[3] + 0.3 + q * 0.5, -27, seed=q, dur=0.2)                      # germs creeping
    for q in range(8):
        M.fx_(S.pop_note(70 + q, 0.04), B[4] + q * DUR[4] * 0.7 / 8, -25)       # germs piling up
    stretch(B[5] + 0.1, DUR[5] * 0.9, -25, 120, 90)                              # creepy low drone
    squelch(B[6] + 0.3, -23, seed=7, dur=0.4)
    for q in range(3):
        pop(B[6] + DUR[6] * (0.45 + 0.13 * q), 80 + q * 4, -25)
    for q in range(4):
        zap(B[7] + DUR[7] * 0.2 + q * 0.5, -25)                                  # pain bolts
    M.fx_(S.pop_note(84, 0.05), B[8] + DUR[8] * 0.4, -25); sparkle(B[8] + DUR[8] * 0.7, -25)

elif name == 'lava':
    END = B[-1] + DUR[-1]
    M.fx_(M.rumble(DUR[9], f=34, seed=9), B[9], -29)                             # the volcano rumbling at the rim
    crunch(END - 1.05, -24)                                                      # his foot slips
    M.fx_(S.whoosh(0.5, 300, 2600), END - 0.55, -22)                             # the camera whips down
    for b, db in ((0, -26), (1, -25), (2, -24), (3, -23), (4, -23)):            # wind roar building all the way down
        M.fx_(M.noise(DUR[b], 300, 4000, 21 + b, 0.05, 0.05), B[b], db - 3)
    M.fx_(M.noise(0.6, 300, 4000, 40, 0.3, 0.05), END - 0.6, -29)
    for b in (1, 2, 3, 4):
        stretch(B[b] + 0.1, DUR[b] * 0.8, -28 + b, 200 + 60 * b, 260 + 80 * b)  # heat rising in pitch
    M.heartbeat(B[3], B[4] + DUR[4], 90, 150, -26)
    for q in range(6):
        M.fx_(M.tick(), B[5] + 0.2 + q * 0.5, -25)                               # slow-mo stopwatch
    stretch(B[5] + 0.1, DUR[5] * 0.9, -27, 300, 120)
    M.fx_(S.impact(0.6), B[6] + 0.3, -18); splash(B[6] + 0.33, -24, 3)          # SMACK
    for q in range(5):
        crunch(B[6] + 1.4 + q * 0.24, -24)                                       # bones cracking on the x-ray
    M.fx_(M.noise(DUR[7] - 0.2, 400, 5000, 30, 0.4, 0.3), B[7] + 0.1, -25)      # fire roar
    M.fx_(S.whoosh(0.5, 2600, 300), B[8] + DUR[8] * 0.30, -24)                   # whip down after the bag
    M.fx_(S.whoosh(1.4, 1600, 300), B[8] + DUR[8] * 0.35, -27)
    M.fx_(S.impact(0.4), B[8] + DUR[8] * 0.63, -21); splash(B[8] + DUR[8] * 0.65, -24, 3)

elif name == 'quicksand':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        y = np.asarray(F.Track.make(nm, **kw), float)
        return y
    def bed(nm, dur, **kw):
        y = np.asarray(F.REG[nm]['fn'](dur, **kw), float); r = np.sqrt(np.mean(y ** 2))
        return y * (0.05 / r) if r > 0 else y
    def suck(t, db=-20, seed=0, dur=0.5):                     # wet mud letting go / taking hold
        squelch(t, db, seed, dur); gurgle(t + 0.05, dur * 0.8, db - 6, seed + 1)
    END = B[-1] + DUR[-1]
    M.fx_(bed('waves', END + 1.0), 0.0, -27)                   # the sea all the way through (the mix wraps, so it loops)
    M.fx_(bed('wind', END + 1.0), 0.0, -33)
    for j, tt in enumerate((0.15, 1.1, 2.2)):                  # 0: sinking, the sand sucking at him
        suck(tt, -21 + j, seed=j, dur=0.55)
    for j in range(9):                                         # 1: kicking and thrashing
        suck(B[1] + 0.3 + j * 0.38, -19 - (j % 3), seed=10 + j, dur=0.4)
    gurgle(B[1] + 0.4, DUR[1] - 0.6, -24, 3)
    stretch(B[2] + 0.4, DUR[2] * 0.7, -27, 160, 90)            # 2: the sand packing in, a low tightening groan
    crunch(B[2] + DUR[2] * 0.5, -26, 4)
    M.fx_(S.pop_note(76, 0.25), B[3] + 1.0, -24)               # 3: good news, a light pop
    for j in range(3):                                         # 4: arrows push up
        stretch(B[4] + 0.4 + j * 0.15, 0.6, -27, 220 + 60 * j, 520 + 80 * j)
    for j in range(3):                                         # 5: heave, heave, heave
        suck(B[5] + 0.5 + j * 0.45, -20, seed=30 + j, dur=0.45)
    M.fx_(fol('creak'), B[5] + DUR[5] * 0.62, -22)            # 5: the car's springs creak as the rear comes up
    M.fx_(fol('thud'), B[5] + DUR[5] * 0.95, -24)
    M.fx_(bed('waves', DUR[6] + 0.6), B[6], -21)               # 6: the tide rolling in, louder
    M.fx_(fol('splash'), B[6] + DUR[6] * 0.7, -27)
    gurgle(B[7] + 0.5, DUR[7] - 0.8, -26, 7)                   # 7: water seeping in
    for j in range(int(DUR[7] / 0.3)):
        M.fx_(S.pop_note(84 + (j * 5) % 9, 0.06), B[7] + 0.4 + j * 0.3, -29)
    suck(B[8] + 0.3, -20, seed=50, dur=0.9)                    # 8: leaning back, then sculling out
    for j in range(4):
        suck(B[8] + 1.5 + j * 0.5, -25, seed=60 + j, dur=0.35)
    walk_t = B[9] + 0.1
    for j in range(4):                                         # 9: wet footsteps, then the plunge
        M.fx_(fol('step', surface='dirt'), walk_t + j * 0.5, -26)
    suck(END - 0.6, -17, seed=70, dur=0.7)
    M.fx_(S.whoosh(0.4, 600, 2400), END - 0.75, -24)

elif name == 'avalanche':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def bed(nm, dur, **kw):
        y = np.asarray(F.REG[nm]['fn'](dur, **kw), float); r = np.sqrt(np.mean(y ** 2))
        return y * (0.05 / r) if r > 0 else y
    def carve(t, dur, db):                                     # board edge hissing through snow
        M.fx_(M.noise(dur, 1500, 7000, int(t * 10) + 3, 0.15, 0.2), t, db)
    def roar(t, dur, db, seed=0, lo=60, hi=900):               # the slide: low churning roar
        M.fx_(M.noise(dur, lo, hi, 40 + seed, 0.6, 0.6), t, db)
    END = B[-1] + DUR[-1]
    T_CRACK, T_REL = 0.95, 1.9
    M.fx_(bed('wind', END + 1.0), 0.0, -32)                    # mountain wind all the way (the mix wraps, so it loops)
    carve(0.0, 1.3, -27); carve(B[9], DUR[9] + 0.05, -27)      # 0 / 9: cruising across the slope (seamless through the loop)
    M.fx_(fol('boom'), T_CRACK, -19); M.fx_(fol('thud'), T_CRACK, -20)          # WHUMPF: the slab settles and cracks
    for j in range(7):                                         # the crack zips across the slope
        M.fx_(fol('ice_crack'), T_CRACK + 0.04 + j * 0.09, -24 - j * 0.8)
    M.fx_(M.rumble(B[1] - T_REL + 0.2, f=38, seed=5), T_REL, -27)               # it starts to move
    roar(B[1], DUR[1], -24, 1)                                 # 1: the slab breaking up and running
    M.fx_(M.rumble(DUR[1], f=32, seed=6), B[1], -22)
    for j in range(8):
        crunch(B[1] + 0.3 + j * 0.62, -27 - (j % 3), seed=20 + j)
    M.fx_(fol('thunder'), B[1] + DUR[1] * 0.45, -26)
    carve(B[2], DUR[2], -20)                                   # 2: riding hard for the edge, the roar right behind
    roar(B[2], DUR[2], -22, 2)
    M.heartbeat(B[2], B[3] + 0.6, 110, 150, -25)
    M.fx_(fol('thud'), B[3] + 0.5, -16); M.fx_(S.impact(0.6), B[3] + 0.5, -18)  # 3: it hits him
    M.fx_(bed('blizzard', DUR[3] + 0.3), B[3] + 0.3, -21)
    roar(B[3], DUR[3], -21, 3, 40, 600)
    for j in range(int(DUR[3] / 0.42)):                        #    swim strokes through the churn
        M.fx_(S.whoosh(0.3, 400, 1500), B[3] + 0.9 + j * 0.42, -26)
    roar(B[4], DUR[4] * 0.6, -25, 4, 40, 400)                  # 4: slowing, settling
    for j in range(5):
        crunch(B[4] + 0.2 + j * 0.25 * (1 + j * 0.3), -24 - j, seed=40 + j)
    crunch(B[4] + 1.1, -19, seed=48); crunch(B[4] + 1.18, -22, seed=49)      #    the hand punches through
    M.fx_(M.noise(DUR[5] - 0.2, 200, 1400, 50, 0.4, 0.3), B[5] + 0.1, -30)  # 5: muffled breathing in the pocket
    M.fx_(fol('thud'), B[6] + 0.05, -17); crunch(B[6] + 0.08, -18, seed=60)  # 6: it sets: one hard thud, then nothing
    stretch(B[6] + 0.3, DUR[6] * 0.8, -29, 90, 70)
    M.shape(B[6] + 0.1, B[6] + DUR[6], -5, 0.3)                # the world goes quiet
    M.fx_(S.pop_note(86, 0.07), B[7] + 0.55, -24)              # 7: the spit drop
    M.fx_(S.pop_note(42, 0.35), B[7] + 2.35, -20); M.fx_(S.pop_note(37, 0.4), B[7] + 2.5, -21)   # "myth": a flat buzzer
    stretch(B[7] + DUR[7] - 1.8, 1.4, -28, 120, 95)            #    he strains; nothing moves
    for j in range(4):                                         # 8: the friend runs in, then digs
        M.fx_(fol('step', surface='snow'), B[8] + 0.05 + j * 0.3, -22)
    dig0 = B[8] + 1.45
    for j in range(int((DUR[8] - 2.6) * 2.3)):
        crunch(dig0 + j / 2.3, -19 - (j % 2) * 2, seed=80 + j); M.fx_(S.whoosh(0.2, 900, 2800), dig0 + j / 2.3 + 0.18, -27)
    M.fx_(M.noise(0.6, 300, 2500, 90, 0.05, 0.3), B[8] + DUR[8] - 0.85, -19)   #    his first breath of air
    M.fx_(S.whoosh(0.4, 600, 2400), END - 0.5, -26)

elif name == 'mold':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    crunch(0.95, -16, seed=1); crunch(1.05, -20, seed=2)                    # 0: the bite
    for j in range(5):
        crunch(1.35 + j * 0.22, -25 - j, seed=3 + j)                         #    chewing
    for j in range(4):                                                      # 1: the threads creeping out
        stretch(B[1] + 1.3 + j * 0.55, 0.7, -27, 300 + 60 * j, 520 + 70 * j)
    M.fx_(S.whoosh(0.5, 800, 3000), B[1] + 1.0, -25)
    for j in range(3):                                                      # 2: the knife sawing, the piece sliding off
        M.fx_(M.noise(0.22, 2500, 8000, 10 + j, 0.02, 0.12), B[2] + 0.6 + j * 0.25, -24)
    M.fx_(fol('thud'), B[2] + 0.6, -27); M.fx_(S.whoosh(0.4, 500, 1800), B[2] + 1.45, -26)
    M.fx_(S.pop_note(42, 0.35), B[2] + 2.4, -22)                           #    "nope" buzz
    M.fx_(S.whoosh(0.4, 300, 2600), B[3] + 0.05, -22)                       # 3: x-ray on; acid fizz and bubbles
    M.fx_(M.noise(DUR[3] - 0.3, 2000, 9000, 20, 0.3, 0.3), B[3] + 0.2, -26)
    gurgle(B[3] + 0.6, DUR[3] - 0.8, -24, 21)
    M.fx_(S.pop_note(79, 0.2), B[4] + 2.6, -22)                             # 4: relief
    gurgle(B[4] + 0.3, 1.6, -26, 23)
    M.fx_(S.whoosh(0.4, 300, 2600), B[5] + 0.05, -22)                       # 5: toxins: an uneasy low drone, rising
    stretch(B[5] + 0.6, DUR[5] - 0.8, -25, 70, 110)
    M.heartbeat(B[5] + 1.5, B[6], 80, 110, -27)
    for j in range(4):                                                      # 6: itch scratches, then the sneeze
        M.fx_(M.noise(0.12, 3000, 9000, 30 + j, 0.01, 0.06), B[6] + 0.8 + j * 0.3, -27)
    M.fx_(M.noise(0.7, 400, 3000, 35, 0.6, 0.05), B[6] + 2.2, -27)          #    the big inhale
    M.fx_(M.noise(0.35, 300, 7000, 36, 0.005, 0.25), B[6] + 2.9, -15)       #    ACHOO
    M.fx_(S.impact(0.3), B[6] + 2.9, -22)
    M.fx_(M.noise(0.8, 300, 2500, 40, 0.3, 0.2), B[7] + 0.6, -25)          # 7: the long sniff
    for j in range(3):
        M.fx_(M.noise(0.18, 200, 3000, 41 + j, 0.01, 0.12), B[7] + 2.3 + j * 0.35, -21)   # coughs
    M.fx_(S.whoosh(0.5, 400, 2000), B[8] + 0.8, -22)                        # 8: the throw
    M.fx_(fol('thud'), B[8] + 1.65, -20); M.fx_(M.tick(), B[8] + 1.15, -22); M.fx_(M.tick(), B[8] + 2.15, -22)   # into the bin, the lid
    M.fx_(S.whoosh(0.4, 600, 2400), END - 0.5, -26)

elif name == 'elevator':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    T_SNAP = END - 0.62                                        # same as elev.js: the cable snaps 0.62 s before the loop
    G_, VMAX, V0 = 9.81, 11.0, 9.81 * 0.62
    def speed(tt):                                            # car speed (m/s), tt = seconds since the snap
        return np.minimum(G_ * tt, VMAX)
    # the rush of air in the shaft: one sound from the snap, folding through the loop to the end of beat 4
    dur = (END - T_SNAP) + B[5] + 0.3; n = int(dur * SR); tt = np.arange(n) / SR
    v = speed(tt); lvl = (v / VMAX) ** 1.3
    x = S.bp(np.random.default_rng(3).standard_normal(n), 250, 2600) * 0.7 + S.lp(np.random.default_rng(4).standard_normal(n), 180) * 2.2
    flutter = 1 + 0.25 * np.sin(2 * np.pi * (3.3 + 0.4 * np.sin(tt * 0.7)) * tt)
    tail = np.clip((dur - tt) / 0.3, 0, 1)
    M.fx_(S.norm(x) * lvl * flutter * tail, T_SNAP, -23)
    # rattling car: steel panels buzzing against the frame while it falls
    rat = (np.random.default_rng(5).random(n) < 0.002 + 0.004 * lvl).astype(float)
    rat = np.convolve(rat, np.exp(-np.arange(300) / 40.0))[:n] * np.sin(2 * np.pi * 1900 * tt)
    M.fx_(S.norm(S.bp(rat, 900, 5000)) * lvl * tail, T_SNAP, -30)
    # each floor whipping past (a soft tick per landing, faster as it falls)
    pos, k = 0.0, 0
    for i in range(1, n, int(SR / 200)):
        pos += speed(tt[i]) / 200
        if pos >= 3.05 * (k + 1) and tt[i] < dur - 0.3:
            M.fx_(S.whoosh(0.09, 1400, 3200), T_SNAP + tt[i], -31 + (2 if B[3] <= (T_SNAP + tt[i]) % END < B[4] else 0)); k += 1
    # the snap (beat 9 -> loop): a cable cracks like a whip, a metal bang, the lights buzz
    M.fx_(fol('whip'), T_SNAP - 0.02, -15); M.fx_(fol('clack'), T_SNAP, -18); M.fx_(S.impact(0.5), T_SNAP + 0.01, -20)
    M.fx_(S.bell(64, 0.7, dec=0.25), T_SNAP + 0.03, -27)          #    the ping of a steel cable letting go
    M.fx_(fol('creak'), T_SNAP - 0.5, -28)
    def buzz(t, dur, db):                                       # fluorescent light buzzing and cutting out
        n2 = int(dur * SR); t2 = np.arange(n2) / SR
        z = np.sign(np.sin(2 * np.pi * 120 * t2)) * 0.4 + np.sin(2 * np.pi * 240 * t2) * 0.3
        gate = (np.sin(t2 * 37 + 3 * np.sin(t2 * 11)) > -0.2).astype(float)
        M.fx_(S.bp(z, 100, 4000) * gate * M.env(n2, 0.02, 0.2), t, db)
    buzz(T_SNAP + 0.02, END - T_SNAP - 0.02 + 1.6, -30)           #    through the loop into the hook
    M.fx_(fol('whip'), 0.55, -24)                                 # 0: the loose cable ends lashing above the car
    M.fx_(fol('chain'), 1.6, -27)
    M.fx_(S.whoosh(0.6, 200, 900), B[1] + 0.3, -26)               # 1: floating: a slow airy swell
    M.fx_(fol('clack'), B[2] + 0.25, -20)                         # 2: a movie clapper
    M.heartbeat(B[2] + 0.6, B[3] + DUR[3], 120, 150, -26)         # 3: heart racing, the floors flying by
    M.fx_(M.rumble(DUR[3], f=40, seed=7), B[3], -24)
    M.fx_(S.whoosh(0.35, 400, 2200), B[4] + 0.3, -21)             # 4: the jump
    M.fx_(S.pop_note(33, 0.4), B[4] + 1.6, -19); M.fx_(fol('thud'), B[4] + 1.6, -24)   #    lights out: a dead clunk
    M.heartbeat(B[4] + 1.9, B[5], 140, 150, -24)
    M.shape(B[4] + 1.6, B[5], -4, 0.1)                            #    the bed drops in the dark
    hum_n = int((DUR[5] + 0.2) * SR); th = np.arange(hum_n) / SR  # 5: calm: the machine room hum, cables counted
    M.fx_(S.lp(np.sin(2 * np.pi * 60 * th) + 0.4 * np.sin(2 * np.pi * 120 * th), 400) * M.env(hum_n, 0.2, 0.3), B[5], -31)
    for i in range(6):
        M.fx_(S.pop_note(72 + [0, 2, 4, 7, 9, 12][i], 0.12), B[5] + DUR[5] * (0.08 + i * 0.05), -24)
    for i in range(5):
        M.fx_(S.pop_note(60 - i * 2, 0.14), B[5] + DUR[5] * (0.52 + i * 0.015), -29)
    M.fx_(S.bell(84, 0.9, dec=0.4), B[5] + DUR[5] * 0.6, -25)     #    the one that holds
    t6 = B[6] + 0.42                                             # 6: the safety brakes bite: a scream of steel, sparks, a hard stop
    sq_n = int(0.55 * SR); tq = np.arange(sq_n) / SR
    sq = np.sin(2 * np.pi * (2600 - 900 * tq / 0.55) * tq + 3 * np.sin(2 * np.pi * 37 * tq)) * 0.6 + S.bp(np.random.default_rng(8).standard_normal(sq_n), 2500, 9000) * 0.8
    M.fx_(S.norm(sq) * M.env(sq_n, 0.01, 0.15), t6 - 0.02, -19)
    for j in range(10):
        M.fx_(M.noise(0.05, 4000, 11000, 60 + j, 0.002, 0.04), t6 + 0.03 * j + 0.02 * (j % 3), -27)   #    sparks crackling
    M.fx_(fol('thud'), t6 + 0.38, -15); M.fx_(S.impact(0.6), t6 + 0.38, -19)
    M.fx_(fol('creak'), t6 + 0.7, -28)
    M.fx_(M.noise(0.7, 300, 2200, 66, 0.15, 0.4), B[6] + DUR[6] - 0.9, -27)   #    a long breath out
    M.fx_(fol('wind', dur=DUR[7] + 0.3), B[7], -31)                 # 7: 1945: wind round the tower, and a long falling whistle
    wn = int((DUR[7] - 0.6) * SR); tw = np.arange(wn) / SR
    fwh = 1800 * np.exp(-tw * 0.32) + 220
    M.fx_(np.sin(2 * np.pi * np.cumsum(fwh) / SR) * M.env(wn, 0.3, 0.6) * 0.6, B[7] + 0.4, -30)
    M.fx_(S.whoosh(0.5, 300, 1800), B[8] + 0.05, -24)              # 8: air squeezed under the car: a rising hiss
    M.fx_(M.noise(DUR[8] * 0.8, 1500, 7000, 70, 0.6, 0.2), B[8] + 0.1, -25)
    for j in range(6):
        M.fx_(fol('chain'), B[8] + 0.3 + j * 0.25, -28 - (j % 2) * 2)   #    cable piling up in coils
    M.fx_(fol('thud'), B[8] + DUR[8] * 0.82, -22)
    M.fx_(S.bell(88, 1.0, dec=0.5), B[9] + 0.1, -24); M.fx_(S.bell(84, 1.2, dec=0.6), B[9] + 0.32, -25)   # 9: the elevator ding

elif name == 'sink':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def glug(t, db=-24, seed=0):                               # a big bubble breaking the surface / gurgling up
        M.fx_(S.pop_note(40 + seed % 9, 0.12), t, db); M.fx_(M.noise(0.12, 200, 1200, 300 + seed, 0.005, 0.08), t, db - 4)
    def under(t, dur, db):                                    # muffled underwater rumble
        n = int(dur * SR); x = S.lp(np.random.default_rng(int(t * 10) + 7).standard_normal(n), 300) * 3
        M.fx_(S.norm(x) * M.env(n, 0.3, 0.4), t, db)
    # 9: rolling down the ramp: tires on rough concrete, a low engine, then the nose hits the water (folds into frame one)
    n9 = int(DUR[9] * SR); t9 = np.arange(n9) / SR
    eng = S.lp(np.sin(2 * np.pi * 42 * t9) + 0.5 * np.sin(2 * np.pi * 84 * t9) + 0.3 * np.random.default_rng(2).standard_normal(n9), 500)
    M.fx_(S.norm(eng) * M.env(n9, 0.3, 0.1), B[9], -30)
    M.fx_(M.noise(DUR[9], 80, 900, 91, 0.4, 0.1), B[9], -29)
    T_HIT = END - 0.12
    M.fx_(fol('splash'), T_HIT, -14); M.fx_(fol('boom'), T_HIT, -22); M.fx_(S.impact(0.7), T_HIT, -18)
    M.fx_(M.noise(1.8, 300, 6000, 92, 0.01, 1.2), T_HIT, -19)          # spray coming down (runs into beat 0)
    for j in range(6):
        glug(0.6 + j * 0.42, -23 - j, j)                          # 0: water rushing over the hood, the car rocking
    M.fx_(fol('creak'), 1.4, -26)
    M.fx_(fol('waves', dur=DUR[1] + 0.3), B[1], -27)              # 1: floating: lapping water, a slow creak, bubbles
    for j in range(4):
        glug(B[1] + 0.4 + j * 0.55, -26, 10 + j)
    M.fx_(M.tick(), B[2] + 1.0, -21); M.fx_(M.tick(), B[2] + 1.12, -24)   # 2: hand on the door handle: click, click
    M.heartbeat(B[2] + 0.4, B[4], 90, 130, -27)
    M.fx_(fol('creak'), B[3] + 0.6, -23)                          # 3: the door groaning under the water's weight
    stretch(B[3] + 0.4, DUR[3] - 0.6, -26, 70, 55)
    M.fx_(M.rumble(DUR[3], f=36, seed=13), B[3], -26)
    under(B[4], DUR[4] + 0.05, -21)                               # 4: underwater, dark, holding his breath, the door creaking open
    for j in range(7):
        M.fx_(S.pop_note(70 + (j * 5) % 12, 0.05), B[4] + 0.4 + j * 0.6, -28)
    M.fx_(fol('creak'), B[4] + 2.0, -24)
    M.heartbeat(B[4] + 0.2, B[5], 120, 140, -24)
    M.shape(B[4], B[5], -4, 0.1)
    M.fx_(fol('clack'), B[5] + DUR[5] * 0.45, -18)                # 5: the buckle clicks open, the belt zips back
    M.fx_(S.whoosh(0.35, 1500, 4000), B[5] + DUR[5] * 0.55, -24)
    nw = int(1.6 * SR); tw = np.arange(nw) / SR                   # 6: the window motor, then water pouring over the sill
    motor = np.sign(np.sin(2 * np.pi * (140 + 30 * tw) * tw)) * 0.3 + np.sin(2 * np.pi * (280 + 60 * tw) * tw) * 0.5
    M.fx_(S.bp(motor, 120, 2500) * M.env(nw, 0.05, 0.1), B[6] + 0.6, -25)
    M.fx_(M.noise(DUR[6] - 0.8, 400, 5000, 60, 0.4, 0.2), B[6] + 0.9, -22)
    M.fx_(fol('waves', dur=DUR[6] - 0.8), B[6] + 0.9, -27)
    t7 = B[7] + DUR[7] * 0.5                                     # 7: the spring punch snaps, the glass bursts, the lake comes in
    M.fx_(fol('clack'), t7 - 0.03, -17)
    for j in range(12):
        M.fx_(M.noise(0.06, 3000, 12000, 70 + j, 0.002, 0.05), t7 + 0.02 + j * 0.035 + 0.01 * (j % 3), -22 - (j % 4))
        if j % 3 == 0:
            M.fx_(S.bell(96 + j % 5, 0.3, dec=0.15), t7 + 0.03 + j * 0.03, -31)
    M.fx_(M.noise(DUR[7] - DUR[7] * 0.5, 200, 4000, 77, 0.05, 0.2), t7 + 0.05, -20)
    under(B[8], DUR[8], -24)                                      # 8: swimming up and out: strokes, bubbles, then air
    for j in range(int(DUR[8] / 0.9)):
        M.fx_(S.whoosh(0.4, 200, 700), B[8] + 0.2 + j * 0.9, -26)
    for j in range(6):
        M.fx_(S.pop_note(74 + (j * 7) % 12, 0.05), B[8] + 0.3 + j * 0.4, -28)
    M.fx_(M.noise(0.5, 400, 3000, 88, 0.02, 0.3), B[9] - 0.15, -23)          # breaking the surface, a big breath

elif name == 'bleach':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def spritz(t, db=-21, seed=0):                             # one trigger pull: a click and a hiss of mist
        M.fx_(M.tick(), t, db + 2); M.fx_(M.noise(0.22, 3000, 11000, 400 + seed, 0.005, 0.12), t + 0.01, db)
    def fizzle(t, dur, db, seed=0):                            # fizzing, tiny bubbles popping
        n = int(dur * SR); x = (np.random.default_rng(seed).random(n) < 0.012).astype(float)
        x = np.convolve(x, np.exp(-np.arange(80) / 9.0))[:n] * np.random.default_rng(seed + 1).standard_normal(n)
        M.fx_(S.norm(S.bp(x, 2500, 12000)) * M.env(n, 0.2, 0.3), t, db)
    def cough(t, db=-17, seed=0):
        M.fx_(M.noise(0.16, 250, 3000, 500 + seed, 0.004, 0.12), t, db); M.fx_(S.pop_note(40 + seed % 5, 0.08), t, db - 6)
    # 9 -> 0: lifts the bottle, sprays three times (the first spritz lands right at the loop)
    for j, tt in enumerate([END - 0.3, 0.35, 0.95, 1.55]):
        spritz(tt, -20, j)
    fizzle(0.6, 3.6, -27, 1)                                     # 0: the water starts to fizz, the haze rising
    M.fx_(M.noise(1.2, 300, 2000, 31, 0.3, 0.4), 2.2, -28)        #    he pulls back, a sharp sniff
    cough(3.3, -21, 1)
    fizzle(B[1], DUR[1], -22, 2)                                  # 1: macro: loud fizz and swirl
    M.fx_(S.whoosh(0.6, 300, 1500), B[1] + 0.2, -26)
    for j in range(4):                                            # 2: molecules: soft clicks as they meet, a snap as the Cl jumps
        M.fx_(S.pop_note(76 + j * 3, 0.1), B[2] + 0.3 + j * 0.3, -27)
    M.fx_(S.pop_note(88, 0.15), B[2] + 1.55, -21); M.fx_(S.bell(91, 0.6, dec=0.3), B[2] + 1.6, -27)
    M.fx_(S.whoosh(0.8, 200, 900), B[3] + 0.3, -24)              # 3: a long inhale, gas going down
    M.fx_(M.noise(1.4, 300, 2500, 33, 0.5, 0.4), B[3] + 0.4, -27)
    t = B[4] + 0.15                                               # 4: coughing fits
    for j in range(int(DUR[4] * 1.6)):
        cough(B[4] + 0.15 + j / 1.6, -18 - (j % 2) * 2, 10 + j); cough(B[4] + 0.15 + j / 1.6 + 0.2, -22, 30 + j)
    M.fx_(M.noise(0.9, 300, 2600, 41, 0.15, 0.3), B[5] + 0.4, -24)   # 5: a big sniff ... a shrug
    M.fx_(S.pop_note(79, 0.18), B[5] + 2.0, -25)
    for j in range(5):                                            # 6: the smell signal: soft pings that fade away
        M.fx_(S.pop_note(84, 0.08), B[6] + 0.4 + j * 0.7, -22 - j * 3)
    M.fx_(M.noise(DUR[6] - 0.3, 300, 2200, 45, 0.6, 0.4), B[6] + 0.2, -30)   #    he keeps breathing it in
    M.fx_(M.rumble(DUR[7], f=34, seed=7), B[7], -27)              # 7: lungs filling: a low swell and wet gurgles
    for j in range(6):
        M.fx_(S.pop_note(38 + j % 4, 0.14), B[7] + 0.6 + j * 0.5, -27)
    M.heartbeat(B[7] + 0.4, B[8], 90, 115, -26)
    for j in range(5):                                            # 8: footsteps out, a cough, the phone ringing through
        M.fx_(fol('step'), B[8] + 0.3 + j * 0.53, -25)
    cough(B[8] + 1.2, -21, 60)
    for j in range(3):
        M.fx_(S.bell(83, 0.35, dec=0.2), B[8] + 2.1 + j * 0.5, -28); M.fx_(S.bell(79, 0.35, dec=0.2), B[8] + 2.3 + j * 0.5, -29)

elif name == 'gum3d':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def chew(t, db=-26, seed=0):                                # a wet chew
        M.fx_(M.noise(0.09, 300, 2500, 600 + seed, 0.005, 0.07), t, db); M.fx_(S.pop_note(50 + seed % 4, 0.05), t, db - 5)
    def gulp(t, db=-17):                                        # the swallow: a low gulp with a little click
        M.fx_(S.pop_note(36, 0.22), t, db); M.fx_(M.noise(0.18, 200, 1200, 77, 0.01, 0.12), t + 0.02, db - 4); M.fx_(M.tick(), t - 0.03, db - 6)
    gulp(END - 0.12)                                             # 9 -> 0: the gulp lands at the loop, then the slide down
    M.fx_(S.whoosh(1.2, 900, 200), 0.1, -24)
    M.fx_(S.pop_note(45, 0.2), B[1] - 0.25, -24)                 #    plop into the stomach
    M.fx_(S.pop_note(55, 0.25), B[1] + 0.3, -26); M.fx_(S.pop_note(52, 0.3), B[1] + 0.6, -27)   # 1: worried belly gurgle
    gurgle(B[1] + 0.9, 1.4, -27, 5)
    M.fx_(M.noise(DUR[2] - 0.3, 2000, 9000, 20, 0.3, 0.3), B[2] + 0.2, -27)    # 2: acid fizz, the color fading
    gurgle(B[2] + 0.4, DUR[2] - 0.6, -25, 21)
    for j in range(8):                                           # 3: acid drops bouncing off rubber: boing
        M.fx_(S.pop_note(70 + (j * 5) % 12, 0.08), B[3] + 0.3 + j * 0.4, -26)
    boing(B[3] + 1.4, -25)
    M.fx_(S.whoosh(DUR[4], 300, 1600), B[4], -24)               # 4: whizzing through the coil
    for j in range(6):
        M.fx_(S.whoosh(0.18, 1200, 2600), B[4] + 0.2 + j * 0.35, -27)
    for j in range(3):                                           # 5: calendar pages flipping, then the flush
        M.fx_(M.noise(0.15, 1500, 6000, 80 + j, 0.005, 0.1), B[5] + DUR[5] * 0.2 * (j + 1), -22)
    M.fx_(M.noise(1.3, 150, 2500, 85, 0.1, 0.6), B[5] + DUR[5] * 0.62, -19); M.fx_(fol('splash'), B[5] + DUR[5] * 0.65, -27)
    M.fx_(M.rumble(DUR[6], f=40, seed=11), B[6], -29)            # 6: inside: a low hum and a slow heartbeat, the scope light
    M.heartbeat(B[6] + 0.2, B[7], 64, 66, -28)
    M.fx_(fol('thud'), B[7] + 0.3, -21); stretch(B[7] + 0.6, DUR[7] - 1.0, -27, 90, 70)   # 7: stuck: a heavy thud, a straining groan
    M.fx_(S.pop_note(42, 0.35), B[8] + DUR[8] * 0.55, -22)      # 8: the "no" buzz on the pack
    M.fx_(S.pop_note(84, 0.12), B[8] + 0.3, -23)
    M.fx_(M.noise(0.12, 2000, 7000, 90, 0.005, 0.08), B[9] + 0.15, -24)   # 9: wrapper crinkle, then chewing
    for j in range(int((DUR[9] - 1.5) * 1.9)):
        chew(B[9] + 0.95 + j / 1.9, -25, j)

elif name == 'diesel':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def flow(t, dur, db=-27):                                  # fuel running through the nozzle: a steady low rush with a little gurgle
        n = int(dur * SR); x = S.bp(np.random.default_rng(int(t * 10) + 3).standard_normal(n), 250, 1800)
        M.fx_(S.norm(x) * M.env(n, 0.15, 0.15), t, db)
    def counter(t0, t1, db=-31):                               # the pump's counter ticking over
        k = 0
        while t0 + k * 0.23 < t1:
            M.fx_(M.tick(), t0 + k * 0.23, db - (k % 2) * 2); k += 1
    # 9 -> 0: the nozzle goes in, the lever clicks, fuel runs and the counter ticks (it keeps going across the loop)
    t_sq = END - 0.6
    M.fx_(fol('clink'), B[9] + DUR[9] * 0.55, -26)
    M.fx_(fol('clack'), t_sq, -22)
    flow(t_sq, END - t_sq + 0.02, -27); flow(0.0, DUR[0] + 0.1, -27)
    counter(t_sq + 0.1, END); counter(0.05, B[1] - 0.05)
    # 1: x-ray: keys jingle, the key turns (click), the fuel pump whines up and pushes diesel down the line
    tk = B[1] + DUR[1] * 0.27
    M.fx_(fol('keys'), tk - 0.5, -27); M.fx_(M.tick(), tk, -18); M.fx_(M.tick(), tk + 0.08, -22)
    nw = int((B[2] - tk - 0.3) * SR); tw = np.arange(nw) / SR
    fw = 620 + 260 * (1 - np.exp(-tw * 3))
    whine = np.sin(2 * np.pi * np.cumsum(fw) / SR) * 0.5 + 0.3 * np.sin(2 * np.pi * np.cumsum(fw * 2) / SR)
    M.fx_(whine * M.env(nw, 0.25, 0.2), tk + 0.15, -30)
    flow(tk + 0.5, B[2] - tk - 0.8, -30)
    # 2: the cylinder on gas: squeeze, spark snap, BOOM, every 1.25 s
    k = 0
    while B[2] + k * 1.25 + 0.6 < B[3] - 0.1:
        c = B[2] + k * 1.25
        M.fx_(S.whoosh(0.5, 300, 1200), c + 0.1, -29)
        M.fx_(M.noise(0.03, 4000, 12000, 50 + k, 0.001, 0.02), c + 0.6, -21)
        M.fx_(S.impact(0.5), c + 0.625, -17); M.fx_(S.pop_note(34, 0.3), c + 0.625, -20)
        k += 1
    # 3: diesel: the piston squeezes, the spark ticks... nothing lights, only a dull fizz
    M.fx_(S.whoosh(DUR[3] * 0.5, 250, 700), B[3] + 0.1, -28)
    k = 0
    while B[3] + k * 0.625 < B[4] - 0.1:
        M.fx_(M.noise(0.03, 4000, 12000, 70 + k, 0.001, 0.02), B[3] + k * 0.625, -26)
        M.fx_(M.noise(0.25, 600, 2500, 80 + k, 0.01, 0.2), B[3] + k * 0.625 + 0.03, -32); k += 1
    # 4: the road: the engine running on leftover gas, then knocking, shaking, sputtering, and dying
    stop = B[4] + DUR[4] - 0.9
    n4 = int((stop - B[4] + 0.4) * SR); t4 = np.arange(n4) / SR
    rpm = 34 * (1 - 0.55 * np.clip((t4 - (stop - B[4] - 0.8)) / 1.0, 0, 1))
    eng = np.sin(2 * np.pi * np.cumsum(rpm) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(rpm * 2) / SR) + 0.25 * np.random.default_rng(4).standard_normal(n4)
    gate = np.ones(n4)
    for j in range(14):                                       # sputter: the engine cutting out in gaps once the diesel arrives
        g0 = int((1.6 + j * 0.24 + 0.05 * (j % 3)) * SR)
        if g0 < n4: gate[g0:g0 + int(0.07 * SR)] *= 0.15
    M.fx_(S.lp(eng, 600) * gate * M.env(n4, 0.2, 0.35), B[4], -24)
    M.fx_(M.noise(stop - B[4], 80, 900, 91, 0.3, 0.2), B[4], -31)      # tires on the road
    for j in range(10):                                       # knocks
        M.fx_(S.pop_note(40 + (j % 3), 0.07), B[4] + 1.3 + j * 0.31, -21 - (j % 2) * 2)
    M.fx_(fol('thud'), stop + 0.05, -25)
    # 5: roadside: the phone call, and a tow truck backing in (reverse beeps)
    for j in range(int((DUR[5] - 0.6) / 0.5)):
        M.fx_(fol('beep', dur=0.22, f=1050), B[5] + 0.4 + j * 0.5, -31)
    M.fx_(fol('engines', dur=DUR[5] - 0.3), B[5] + 0.2, -33)
    # 6: the macro: the fat spout knocks the small filler ring twice (clink), then fuel pours in anyway
    for f in (0.33, 0.5):
        M.fx_(fol('clink'), B[6] + DUR[6] * f, -21)
    flow(B[6] + DUR[6] * 0.75, DUR[6] * 0.25, -28)
    # 7: the tow: chains, the truck pulling off, a cash register
    M.fx_(fol('chain'), B[7] + 0.15, -26); M.fx_(fol('engines', dur=DUR[7] - 0.6), B[7] + 0.5, -31)
    M.fx_(fol('ching'), B[7] + DUR[7] * 0.45, -22)
    # 8: the parts bill: each part drops in with a clank, then coins pouring
    for i in range(7):
        M.fx_(fol('clink'), B[8] + 0.15 * i + 0.55, -24 - (i % 2) * 2)
    for i in range(5):
        M.fx_(fol('coin_drop'), B[8] + 1.5 + i * 0.13, -27 - (i % 2) * 2)
    M.fx_(fol('ching'), B[8] + DUR[8] * 0.5, -21)

elif name == 'plane':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def wrap(t):                                               # sounds that start before the loop point land at the end and carry on at the start
        return t % END
    def cough(t, db=-19, seed=0):
        M.fx_(M.noise(0.16, 250, 3000, 500 + seed, 0.004, 0.12), t, db); M.fx_(S.pop_note(40 + seed % 5, 0.08), t, db - 6)
    T_BANG = END - 0.5                                          # the bang (the window flash), 0.5 s before the loop point
    # cabin: a steady jet roar under the seat beats (calm in 9, louder and shaking in the dive)
    M.fx_(fol('jet_cruise', dur=DUR[9] + 0.2), B[9], -30)
    M.fx_(fol('jet_cruise', dur=B[4] - 0.0), 0.0, -27)
    # 9 -> 0: seatbelt chime early in 9; the bang lands 0.5 s before the loop and rings into frame one; then the dive: wind, rattle
    M.fx_(fol('caution_chime'), B[9] + 0.3, -26)
    M.fx_(fol('explosion'), T_BANG, -14); M.fx_(S.impact(0.6), T_BANG, -18)
    nb = int((END - T_BANG) * SR)
    M.fx_(S.norm(S.lp(np.random.default_rng(3).standard_normal(int(2.0 * SR)), 400)) * M.env(int(2.0 * SR), 0.01, 1.2), 0.0, -18)   # the blast tail, after the loop point
    M.fx_(fol('wind', dur=B[1] + 0.2), 0.0, -24); M.fx_(fol('wind', dur=END - T_BANG + 0.1), T_BANG, -26)
    for j in range(7):                                         # bins popping, things rattling
        M.fx_(fol('clack', f=300 + 60 * j), 0.15 + j * 0.37, -24 - (j % 3) * 2)
    M.fx_(fol('clack'), T_BANG + 0.25, -24)
    # 1: the masks drop (a plastic clatter), oxygen hiss
    for j in range(14):
        M.fx_(M.tick(), B[1] + 0.06 + j * 0.022 + 0.01 * (j % 3), -24 - (j % 4) * 2)
    M.fx_(M.noise(1.6, 3000, 9000, 41, 0.2, 0.6), B[1] + 1.6, -31)
    M.fx_(fol('wind', dur=DUR[1] + DUR[2] + DUR[3]), B[1], -28)
    # 2: the buckle and the strap pulled tight
    M.fx_(fol('clack', f=900), B[2] + 0.2, -21); M.fx_(S.whoosh(0.35, 1500, 4000), B[2] + 0.35, -25)
    M.fx_(S.whoosh(0.3, 1800, 4500), B[2] + 1.0, -27)
    # 3: brace: the roar climbs, heartbeat
    M.fx_(fol('riser', dur=DUR[3] + 0.4), B[3] - 0.1, -23)
    M.heartbeat(B[3] + 0.3, B[4], 110, 140, -24)
    # 4: outside: the jet screams in, the belly hits (BOOM), metal scraping; inside: shaking, clatter
    te = DUR[4] * 0.55; t_hit = B[4] + te * 0.38
    M.fx_(fol('jet_cruise', dur=t_hit - B[4] + 0.2), B[4], -19)
    M.fx_(S.whoosh(t_hit - B[4], 200, 2400), B[4], -22)
    M.fx_(fol('explosion'), t_hit, -12); M.fx_(fol('boom'), t_hit, -16); M.fx_(S.impact(0.8), t_hit, -15)
    nsc = int((B[5] - t_hit) * SR); tsc = np.arange(nsc) / SR
    scrape = S.bp(np.random.default_rng(9).standard_normal(nsc), 900, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * tsc))
    M.fx_(S.norm(scrape) * M.env(nsc, 0.01, 0.6), t_hit, -21)
    M.fx_(M.rumble(B[5] - t_hit, f=32, seed=5), t_hit, -19)
    for j in range(6):
        M.fx_(fol('clack', f=250 + 80 * j), B[4] + te + 0.1 + j * 0.18, -22 - (j % 2) * 3)
    # 5: smoke: fire crackling, the floor-light alarm chime, coughing
    M.fx_(fol('fire', dur=B[7] - B[5]), B[5], -27)
    for j in range(3):
        M.fx_(fol('caution_chime'), B[5] + 0.4 + j * 1.6, -30)
    for j in range(4):
        cough(B[5] + 0.3 + j * 0.62, -20 - (j % 2) * 2, j)
    # 6: crouch-walking: soft steps, a tap on each armrest he counts
    TAPS = [23.772, 24.772, 25.726, 26.692]          # the left hand reaching each armrest (from plane.js countHand)
    for tt in TAPS:
        M.fx_(fol('clack', f=520), tt, -20)
    for j in range(int(DUR[6] / 0.45)):
        M.fx_(fol('step', surface='wood'), B[6] + 0.2 + j * 0.45, -29)
    # 7: the door: a thunk, daylight wind, the bag drops; the slide (a long rubbery whoosh); running on grass, the fire roaring
    M.fx_(fol('thud'), B[7] + 0.05, -20); M.fx_(fol('wind', dur=DUR[7] * 0.3), B[7], -25)
    M.fx_(fol('thud'), B[7] + DUR[7] * 0.3 * 0.55 + 0.25, -21)
    M.fx_(S.whoosh(DUR[7] * 0.3, 300, 1400), B[7] + DUR[7] * 0.32, -20)
    M.fx_(fol('fire', dur=DUR[7] * 0.7 + 0.3), B[7] + DUR[7] * 0.3, -22)
    for j in range(int(DUR[7] * 0.38 / 0.34)):
        M.fx_(fol('step', surface='dirt'), B[7] + DUR[7] * 0.62 + j * 0.34, -24)
    # 8: the 100 people pop in (soft ticks), then the green wave: a rising chime
    for j in range(10):
        M.fx_(S.pop_note(76 + j % 5, 0.05), B[8] + 0.05 + j * DUR[8] * 0.35 / 10, -27)
    for j in range(8):
        M.fx_(S.bell(84 + [0, 2, 4, 7, 9, 12, 14, 16][j], 0.4, dec=0.25), B[8] + DUR[8] * 0.45 + j * 0.14, -28)

elif name == 'estop':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def glass(t, db=-26, seed=0):                              # a pane breaking: bright crackle
        n = int(0.25 * SR); g = np.random.default_rng(seed).standard_normal(n) * (np.random.default_rng(seed + 1).random(n) < 0.08) * np.exp(-np.arange(n) / SR * 18)
        M.fx_(S.bp(g, 3500, 12000), t, db)
    def stop(t, db=-10):                                        # the ground stops: a huge low hit and the air tearing loose
        M.fx_(fol('explosion'), t, db); M.fx_(S.impact(0.8), t, db - 4); M.fx_(fol('boom'), t, db - 4)
    T9 = B[9] + DUR[9] - 0.25                                   # the stop at the end of beat 9 (it rings on past the loop into beat 0)
    # calm street (2, 9): people talking, a slurp of coffee
    M.fx_(fol('murmur', dur=DUR[2]), B[2], -29); M.fx_(fol('murmur', dur=T9 - B[9]), B[9], -29)
    M.fx_(S.whoosh(0.3, 1500, 4000), B[2] + 1.55, -30); M.fx_(S.whoosh(0.3, 1500, 4000), B[9] + 0.3, -30)
    stop(T9); M.fx_(fol('wind', dur=DUR[0] + 0.3), 0.0, -18); M.fx_(fol('wind', dur=END - T9), T9, -20)
    for j in range(8):
        glass(0.2 + j * 0.42, -26 - (j % 3), j); M.fx_(fol('clack', f=300 + 60 * j), 0.35 + j * 0.4, -25)
    M.fx_(fol('thud'), 1.4, -22); M.fx_(fol('thud'), 2.6, -24)
    # 1: space: a deep hum, the camera swoops in, a ping when the pin shows
    M.fx_(M.rumble(DUR[1], f=40, seed=21), B[1], -27); M.fx_(S.whoosh(DUR[1] * 0.8, 200, 1200), B[1] + 0.2, -27)
    M.fx_(S.bell(91, 0.6, dec=0.3), B[1] + DUR[1] * 0.6, -26)
    # 3: the stop (side view)
    t3 = B[3] + 0.95; stop(t3, -11); M.fx_(fol('wind', dur=B[4] - t3 + 0.2), t3, -19)
    # 4: the sonic boom: a double crack, then the roar of air and a high whistle
    M.fx_(S.impact(0.5), B[4] + 0.05, -14); M.fx_(S.impact(0.5), B[4] + 0.17, -16); M.fx_(fol('explosion'), B[4] + 0.05, -18)
    M.fx_(fol('wind', dur=DUR[4]), B[4], -19); M.fx_(fol('whistle', dur=DUR[4] - 0.4), B[4] + 0.3, -32)
    # 5: the street tears loose: wind, wood groaning (the houses), thuds, glass
    M.fx_(fol('wind', dur=DUR[5]), B[5], -19)
    for j in range(4):
        M.fx_(fol('creak'), B[5] + 0.4 + j * 0.9, -22 - (j % 2) * 2)
    for j in range(6):
        M.fx_(fol('thud'), B[5] + 0.3 + j * 0.65, -22 - (j % 2) * 3); glass(B[5] + 0.5 + j * 0.6, -27, 40 + j)
    # 6: the wall of wind: a deep rolling roar that grows, debris clattering
    M.fx_(fol('wind', dur=DUR[6]), B[6], -17); M.fx_(M.rumble(DUR[6], f=30, seed=31), B[6], -20)
    M.fx_(fol('riser', dur=DUR[6] * 0.8), B[6] + 0.2, -26)
    for j in range(8):
        M.fx_(fol('clack', f=250 + 50 * j), B[6] + 1.0 + j * 0.5, -25)
    # 7: the tsunami: surf building to a roar, then the crash
    M.fx_(fol('waves', dur=DUR[7]), B[7], -20); M.fx_(M.rumble(DUR[7], f=34, seed=41), B[7], -21)
    M.fx_(fol('splash'), B[7] + DUR[7] - 0.45, -15); M.fx_(fol('boom'), B[7] + DUR[7] - 0.45, -18)
    # 8: the North Pole: a soft breeze, all calm
    M.fx_(fol('wind', dur=DUR[8]), B[8], -31)

elif name == 'yellowstone':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def glass(t, db=-26, seed=0):                              # bright glassy crackle
        n = int(0.25 * SR); g = np.random.default_rng(seed).standard_normal(n) * (np.random.default_rng(seed + 1).random(n) < 0.08) * np.exp(-np.arange(n) / SR * 18)
        M.fx_(S.bp(g, 3500, 12000), t, db)
    def cough(t, db=-17, seed=0):                              # a dry cough: a hard noise burst through the throat
        n = int(0.32 * SR); tt = np.arange(n) / SR; r = np.random.default_rng(seed)
        env_ = (1 - np.exp(-tt / 0.006)) * np.exp(-tt / 0.07) + 0.35 * np.exp(-((tt - 0.12) / 0.05) ** 2)
        M.fx_(S.norm(S.bp(r.standard_normal(n), 250, 2600) * env_), t, db)
    def blast(t, db=-9):                                        # the eruption: a huge low hit, a boom, thunder rolling after
        M.fx_(fol('explosion'), t, db); M.fx_(S.impact(0.9), t, db - 3); M.fx_(fol('boom'), t + 0.05, db - 3); M.fx_(fol('thunder'), t + 0.4, db - 6)
    T9 = B[9] + DUR[9] - 0.3                                   # the blast at the end of beat 9 (loops into beat 0)
    TH = max(T9, M.TM['voice'][-1][1] + 0.02)                  # its sound lands after the last word (it's miles away: sound comes late)
    # 9: calm at the overlook: a breeze, a shutter click; then the blast
    M.fx_(fol('wind', dur=DUR[9]), B[9], -31); M.fx_(fol('click') if 'click' in F.REG else S.impact(0.05), B[9] + 0.9, -30); blast(TH)
    # 0: the blast is 0.3 s old: the roar, the rumble, lightning cracks in the cloud, rocks whistling down
    M.fx_(M.rumble(DUR[0] + 0.2, f=32, seed=7), 0.0, -16); M.fx_(fol('explosion'), 0.0, -16); M.fx_(fol('wind', dur=DUR[0]), 0.0, -22)
    M.fx_(fol('thunder'), 1.3, -20); M.fx_(fol('whistle', dur=1.0), 1.8, -32)
    # 1: the wall of hot ash: a rolling roar that grows, his running steps, trees cracking
    M.fx_(M.rumble(DUR[1], f=28, seed=11), B[1], -15); M.fx_(fol('wind', dur=DUR[1]), B[1], -19); M.fx_(fol('riser', dur=DUR[1] * 0.9), B[1] + 0.3, -25)
    k = 0; tt_ = B[1] + 0.12
    while tt_ < B[2] - 0.15:
        M.fx_(fol('step'), tt_, -21 - (k % 2)); tt_ += 1 / 2.8; k += 1
    for j in range(5):
        M.fx_(fol('creak'), B[1] + 1.0 + j * 0.9, -25); M.fx_(fol('thud'), B[1] + 1.2 + j * 0.9, -25)
    # 2: the map: a soft whoosh as the cloud spreads, a tick when the upwind bracket draws
    M.fx_(S.whoosh(DUR[2] * 0.9, 200, 1400), B[2] + 0.2, -25); M.fx_(fol('wind', dur=DUR[2]), B[2], -29)
    M.fx_(S.bell(88, 0.5, dec=0.3), B[2] + DUR[2] * 0.47, -27); M.fx_(S.bell(95, 0.5, dec=0.3), B[2] + DUR[2] * 0.8, -27)
    # 3: ash falling: quiet, a hush of grains, a muffled wind
    M.fx_(fol('wind', dur=DUR[3]), B[3], -27); M.fx_(fol('rain', dur=DUR[3]), B[3], -36)
    # 4: rain on the ash; the roof creaks, sags, then caves in
    M.fx_(fol('rain', dur=DUR[4] + DUR[5] * 0.5), B[4], -22)
    for j in range(3):
        M.fx_(fol('creak'), B[4] + DUR[4] * (0.5 + 0.06 * j), -19 - j)
    tc = B[4] + DUR[4] * 0.68; M.fx_(fol('thud'), tc, -13); M.fx_(fol('explosion'), tc + 0.05, -20); M.fx_(S.impact(0.5), tc, -15)
    for j in range(6):
        M.fx_(fol('clack', f=220 + 40 * j), tc + 0.15 + j * 0.12, -24)
    # 5: he coughs; then the ash up close: glassy tinkles over a low hum
    for j, c0 in enumerate([0.17, 0.83, 1.49]):
        if c0 < DUR[5] * 0.5 - 0.1: cough(B[5] + c0, -15 - j, 60 + j)
    t5 = B[5] + DUR[5] * 0.5; M.fx_(S.whoosh(0.5, 600, 3000), t5 - 0.15, -24); M.fx_(M.rumble(DUR[5] * 0.5, f=55, seed=51), t5, -32)
    for j in range(6):
        glass(t5 + 0.1 + j * 0.3, -27 - (j % 2), 70 + j); M.fx_(S.bell(100 + (j * 5) % 9, 0.4, dec=0.2), t5 + 0.2 + j * 0.3, -31)
    # 6: the jet in the ash: engines, the burner sizzling, then the engine spools down
    M.fx_(fol('jet_cruise', dur=DUR[6]), B[6], -18); M.fx_(fol('wind', dur=DUR[6]), B[6], -24); M.fx_(fol('fire', dur=DUR[6] * 0.6), B[6] + DUR[6] * 0.2, -24)
    M.fx_(fol('jet_spooldown'), B[6] + DUR[6] * 0.7, -17)
    # 7: summer snow on the corn: a cold wind, him blowing into his hands
    M.fx_(fol('blizzard', dur=DUR[7]), B[7], -25); M.fx_(S.whoosh(0.6, 400, 2500), B[7] + DUR[7] * 0.5, -25)
    # 8: Old Faithful on a sunny day: the geyser rushing, people chatting, a happy note
    M.fx_(fol('murmur', dur=DUR[8]), B[8], -27); M.fx_(fol('waves', dur=DUR[8]), B[8], -27); M.fx_(S.whoosh(DUR[8] * 0.9, 900, 5000), B[8] + 0.1, -27)

elif name == 'heartstop':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def tone(f, dur, a=0.005, r=0.02):                          # a plain sine (monitor beeps, the flatline)
        n = int(dur * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * f * tt) * M.env(n, a, r)
    def thump(t, db=-14):                                        # one heartbeat (lub-dub)
        M.fx_(S.impact(0.35), t, db); M.fx_(S.impact(0.25), t + 0.18, db - 5)
    def glass(t, db=-24, seed=0):
        n = int(0.3 * SR); g = np.random.default_rng(seed).standard_normal(n) * (np.random.default_rng(seed + 1).random(n) < 0.1) * np.exp(-np.arange(n) / SR * 14)
        M.fx_(S.bp(g, 2500, 11000), t, db)
    def gasp(t, db=-17, seed=0):                                 # a sharp breath in through an open mouth
        n = int(0.55 * SR); tt = np.arange(n) / SR; e = np.sin(np.pi * np.clip(tt / 0.5, 0, 1)) ** 1.5
        M.fx_(S.norm(S.bp(np.random.default_rng(seed).standard_normal(n), 500, 3200) * e), t, db)
    END = B[-1] + DUR[-1]
    beats = lambda t0, t1: [k / 1.25 + 0.1 / 1.25 for k in range(int(t0 * 1.25) - 1, int(t1 * 1.25) + 2) if t0 <= k / 1.25 + 0.1 / 1.25 < t1]
    # 9: home, calm; a sip; the push into his chest: his heartbeat and a monitor beep come up
    M.fx_(fol('murmur', dur=DUR[9]), B[9], -38); M.fx_(S.whoosh(0.3, 1200, 3500), B[9] + 1.4, -32)
    for tb in beats(END - 1.2, END):
        thump(tb, -16); M.fx_(tone(1000, 0.09), tb, -30)
    # 0: one last beat, then the flatline; the mug slips and smashes; his knees go
    for tb in beats(0.0, 0.4):
        thump(tb, -14); M.fx_(tone(1000, 0.09), tb, -28)
    M.fx_(tone(1000, 2.4, a=0.01, r=0.6), 0.45, -27)
    M.fx_(S.whoosh(0.35, 800, 3000), 1.42, -28); tm = 1.4 + 0.42
    M.fx_(fol('thud'), tm, -20); glass(tm, -18, 3); glass(tm + 0.05, -22, 5); M.fx_(fol('clink'), tm + 0.02, -22) if 'clink' in F.REG else None
    M.fx_(M.rumble(DUR[0] + DUR[1], f=40, seed=9), 0.8, -28)
    # 1: he falls: a knee hits, then his body; a falling hum as his brain dims
    M.fx_(fol('thud'), B[1] + 0.45, -21); M.fx_(fol('thud'), B[1] + 1.2, -14); M.fx_(S.impact(0.5), B[1] + 1.2, -18)
    M.fx_(S.whoosh(1.0, 300, 1500), B[1] + 0.2, -28)
    # 2: two gasps (not real breathing)
    gasp(B[2] + 0.62, -17, 21); gasp(B[2] + 1.72, -19, 22)
    # 3: brain cells: a fizzle as each goes dark, over a low hum
    M.fx_(M.rumble(DUR[3], f=60, seed=31), B[3], -30)
    for j in range(9):
        glass(B[3] + DUR[3] * (0.12 + 0.09 * j), -30 - (j % 3), 40 + j)
    # 4: the clock races; the room is silent
    t_ = B[4] + 0.1; step = 0.32
    while t_ < B[5] - 0.1:
        M.fx_(M.tick(), t_, -24); t_ += step; step = max(0.09, step * 0.9)
    # 5: someone kneels (knees on the floor), shakes his shoulder, puts their hands on his chest
    M.fx_(fol('thud'), B[5] + 0.05, -24); M.fx_(S.whoosh(0.4, 500, 2500), B[5] + 0.3, -30); M.fx_(S.whoosh(0.5, 400, 2000), B[5] + DUR[5] * 0.6, -29)
    # 6-7: the pushes, 110 a minute (soft thumps on the beat)
    hz = 110 / 60
    for k in range(200):
        tp = B[6] + (k + 0.5) / hz
        if tp >= B[7] + DUR[7] * 0.5: break
        M.fx_(fol('thud'), tp, -25 - (k % 2))
    # 7: the AED: beeps, charging, the shock; the heart starts again (beat and monitor)
    tc = B[7] + DUR[7] * 0.5
    M.fx_(tone(880, 0.12), tc + 0.05, -26); M.fx_(tone(880, 0.12), tc + 0.3, -26)
    ts = B[7] + DUR[7] * 0.72; n = int((ts - tc - 0.45) * SR); tt = np.arange(n) / SR
    M.fx_(np.sin(2 * np.pi * np.cumsum(np.linspace(600, 2600, n)) / SR) * M.env(n, 0.05, 0.01), tc + 0.45, -31)
    M.fx_(S.impact(0.6), ts, -12); M.fx_(S.bp(np.random.default_rng(77).standard_normal(int(0.12 * SR)) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30), 1500, 9000), ts, -16)
    for tb in beats(ts + 0.3, B[8]):
        thump(tb, -18); M.fx_(tone(1000, 0.09), tb, -30)
    # 8: alive: a steady heartbeat, the monitor, a deep breath
    for tb in beats(B[8], B[9]):
        thump(tb, -19); M.fx_(tone(1000, 0.08), tb, -32)
    gasp(B[8] + 0.6, -24, 81)

elif name == 'afterdeath':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def sweep(f0, f1, dur, a=0.05, r=0.3):                      # a gliding sine
        n = int(dur * SR); return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * M.env(n, a, r)
    def thump(t, db=-15):
        M.fx_(S.impact(0.35), t, db); M.fx_(S.impact(0.25), t + 0.18, db - 5)
    def crackle(t, dur, db=-30, seed=0):
        n = int(dur * SR); g = np.random.default_rng(seed).standard_normal(n) * (np.random.default_rng(seed + 1).random(n) < 0.02)
        M.fx_(S.bp(g, 1500, 6000) * M.env(n, 0.1, 0.2), t, db)
    END = B[-1] + DUR[-1]
    beats = lambda t0, t1: [k / 1.15 + 0.1 / 1.15 for k in range(int(t0 * 1.15) - 1, int(t1 * 1.15) + 2) if t0 <= k / 1.15 + 0.1 / 1.15 < t1]
    # night room under everything (crickets outside), louder while he's alive
    M.fx_(fol('crickets', dur=END), 0.0, -36)
    # 9 / 0: his heartbeat as we push into his chest; the last beat, then a low tone falls away
    for tb in beats(END - 1.3, END): thump(tb, -23 if tb < M.TM['voice'][-1][1] else -16)
    for tb in beats(0.0, 0.5): thump(tb, -19)
    M.fx_(sweep(220, 70, 3.0, a=0.2, r=1.2), 0.6, -27)
    # 1: blood stops: a low rush that slows to nothing
    M.fx_(S.whoosh(DUR[1] * 0.6, 120, 900), B[1] + 0.1, -27); M.fx_(M.rumble(DUR[1] * 0.7, f=38, seed=5), B[1], -30)
    # 2: hearing: soft chimes arrive like far-off sound, muffled
    for j in range(5): M.fx_(S.bell(84 + (j * 3) % 7, 0.8, dec=0.5), B[2] + 0.6 + j * 1.05, -31 - (j % 2))
    # 3: every muscle goes loose: a soft settling rustle
    M.fx_(S.whoosh(1.2, 300, 1800), B[3] + 0.4, -28); M.fx_(fol('creak'), B[3] + 0.9, -32)
    # 4: cooling: a slow falling tone
    M.fx_(sweep(520, 180, DUR[4], a=0.3, r=0.6), B[4], -31)
    # 5: blood settling: a low slow drain
    M.fx_(M.noise(DUR[5], 80, 400, seed=55, a=0.5, r=0.8), B[5], -31)
    # 6: stiffening: the clock ticks, slow creaks as each part locks
    M.clock(B[6], B[7], db=-27, step=0.5)
    for j in range(6): M.fx_(fol('creak'), B[6] + 0.3 + j * 0.75, -29 - (j % 2))
    # 7: a day later: the clock races, then a soft release
    t_ = B[7]; st = 0.4
    while t_ < B[8] - 0.2:
        M.fx_(M.tick(), t_, -27); t_ += st; st = max(0.1, st * 0.85)
    M.fx_(S.whoosh(0.9, 400, 2200), B[7] + DUR[7] * 0.55, -28)
    # 8: the skin dries and pulls back: a faint dry crackle
    crackle(B[8] + 0.6, DUR[8] - 1.0, -32, 80)
    M.shape(B[9] - 0.05, B[9] + 0.6, -5, 0.1)                  # the cut swish into the short last line sat on top of the voice

elif name == 'dogchoc':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def sweep(f0, f1, dur, a=0.05, r=0.3):
        n = int(dur * SR); return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * M.env(n, a, r)
    def crinkle(t, dur, db=-30, seed=0):                         # foil wrapper: sparse bright crackle
        n = int(dur * SR); g = np.random.default_rng(seed).standard_normal(n) * (np.random.default_rng(seed + 1).random(n) < 0.03)
        M.fx_(S.bp(g, 2500, 9000) * M.env(n, 0.05, 0.15), t, db)
    def crunch(t, db=-28, seed=0):                               # one chomp
        n = int(0.09 * SR); g = np.random.default_rng(seed).standard_normal(n) * np.exp(-np.arange(n) / (0.025 * SR))
        M.fx_(S.bp(g, 600, 4000), t, db)
    def thump(t, db=-18):
        M.fx_(S.impact(0.3), t, db); M.fx_(S.impact(0.22), t + 0.14, db - 5)
    def pant(t0, t1, db=-31, rate=3.2):                          # dog panting: short breathy bursts
        k = 0
        while t0 + k / rate < t1:
            M.fx_(M.noise(0.13, 700, 3000, seed=300 + k, a=0.02, r=0.08), t0 + k / rate, db - (k % 2) * 2); k += 1
    END = B[-1] + DUR[-1]
    w13 = 2 * np.pi * round(13 * END / (2 * np.pi)) / END        # the chew speed in the scene (repeats over the loop)
    # 0 / 9: chewing the bar on the floor, foil crinkling
    for k in range(int(B[1] * w13 / (2 * np.pi)) + 1):
        tc = (np.pi / 2 + 2 * np.pi * k) / w13
        if tc < B[1] - 0.1: crunch(tc, -27 - (k % 3), k)
    crinkle(0.0, B[1] - 0.2, -31, 7)
    for k in range(int(END * w13 / (2 * np.pi)) + 1):
        tc = (np.pi / 2 + 2 * np.pi * k) / w13
        if END - 0.85 < tc < END - 0.05: crunch(tc, -27, 50 + k)
    # 1: inside him: x-ray whoosh, the poison seeping through his blood
    M.fx_(S.whoosh(0.7, 300, 2500), B[1] - 0.15, -26)
    M.fx_(M.noise(DUR[1], 120, 700, seed=21, a=0.6, r=0.8), B[1], -32)
    for j in range(int(DUR[1] / 0.62)): thump(B[1] + 0.3 + j * 0.62, -25)
    # 2: his heart races, then the shaking on the floor
    cut2 = B[2] + DUR[2] * 0.45
    tb = B[2]
    while tb < cut2: thump(tb, -21); tb += 0.31
    M.fx_(fol('thud'), cut2, -24)
    M.fx_(M.noise(B[3] - cut2, 150, 1200, seed=33, a=0.05, r=0.3) * (0.6 + 0.4 * np.sin(2 * np.pi * 17 * np.arange(int((B[3] - cut2) * SR)) / SR)), cut2, -31)
    tb = cut2 + 0.15
    while tb < B[3] - 0.1: thump(tb, -25); tb += 0.29
    # 3: hours go by: the clock ticks fast, he pants on his bed
    t_ = B[3] + 0.2
    while t_ < B[4] - 0.2: M.fx_(M.tick(), t_, -29); t_ += 0.25
    pant(B[3] + 0.3, B[4] - 0.3, -32)
    # 4: the lineup: each danger bar rises with a falling tone (worst first)
    for i in range(4):
        tt = B[4] + DUR[4] * (0.08 + 0.12 * i)
        M.fx_(sweep(330 - 50 * i, 520 - 90 * i, 0.5, a=0.05, r=0.25), tt, -29 - 2 * i)
    # 5: sitting by the bar: soft tail thumps on the floor
    for j in range(3): M.fx_(fol('thud'), B[5] + 0.6 + j * 0.55, -33)
    # 6: on the phone with the wrapper: ringback tone, foil crinkle
    for j in range(2): M.fx_(sweep(440, 440, 0.9, a=0.02, r=0.05) + 0.6 * sweep(480, 480, 0.9, a=0.02, r=0.05), B[6] + 0.1 + j * 1.6, -36)
    crinkle(B[6] + 0.3, 0.6, -31, 61)
    # 7: kneeling by him: a soft rustle, slow panting
    M.fx_(S.whoosh(0.6, 300, 1500), B[7] + 0.1, -30)
    pant(B[7] + 0.5, B[8] - 0.2, -34, rate=2.4)
    # 8: Halloween: candy rattling in the bowl
    for j in range(7): M.fx_(fol('clink'), B[8] + 0.4 + j * 0.42 + 0.07 * (j % 3), -33 - (j % 2) * 2)
    crinkle(B[8] + 0.3, DUR[8] - 0.6, -33, 81)
    M.shape(B[9] - 0.05, B[9] + 0.6, -4, 0.1)

elif name == 'choke':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def tone(f, dur, a=0.005, r=0.02):
        n = int(dur * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * f * tt) * M.env(n, a, r)
    def dtmf(d, dur=0.16):                                       # a phone key tone
        lo, hi = {'9': (852, 1477), '1': (697, 1209)}[d]; return 0.5 * (tone(lo, dur) + tone(hi, dur))
    def thump(t, db=-20):                                        # one heartbeat
        M.fx_(S.impact(0.32), t, db); M.fx_(S.impact(0.24), t + 0.15, db - 5)
    def gag(t, db=-26, seed=0):                                  # a muffled try to cough with the airway shut: a tight throat click and a strangled push
        n = int(0.32 * SR); tt = np.arange(n) / SR; g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n), 250, 1100) * np.sin(np.pi * np.clip(tt / 0.3, 0, 1)) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * tt))
        M.fx_(S.norm(x), t, db); M.fx_(S.bp(g.standard_normal(int(0.03 * SR)), 800, 4000), t, db - 4)
    def gasp(t, dur=0.6, db=-19, seed=0):                        # a big breath in
        n = int(dur * SR); tt = np.arange(n) / SR; e = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.3
        M.fx_(S.norm(S.bp(np.random.default_rng(seed).standard_normal(n), 400, 3500) * e), t, db)
    def scrape(t, dur, db=-24, seed=0):                          # chair legs dragged on the wood floor
        n = int(dur * SR); tt = np.arange(n) / SR; g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n), 300, 2500) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * (38 + 20 * tt / dur) * tt)))
        M.fx_(S.norm(x) * M.env(n, 0.03, 0.08), t, db)
    END = B[-1] + DUR[-1]
    T_CH, T_POPA = B[0] + 0.95, B[5] + 0.45                      # he starts choking / the bite pops out (the clock runs between)
    # 0: fork off the plate, the bite, a hard gulp; the fork drops; the chair scrapes back as he jumps up
    M.fx_(fol('clink'), 0.03, -27); M.fx_(fol('clink'), T_CH + 0.12, -22); M.fx_(fol('clink'), T_CH + 0.2, -28)
    M.fx_(S.bp(np.random.default_rng(3).standard_normal(int(0.06 * SR)), 400, 2500), 0.42, -30)      # the bite
    gag(T_CH, -22, 1)
    scrape(1.55, 0.5, -23, 4)
    # the clock: no ticking (owner: annoying). His heartbeat speeds up and a low tone rises under it; both cut dead at the pop
    t_ = T_CH + 0.3
    while t_ < T_POPA - 0.1:
        k = (t_ - T_CH) / (T_POPA - T_CH); thump(t_, -20 - 2 * (B[3] <= t_ < B[5]) + 2 * k); t_ += 0.66 - 0.3 * k
    n = int((T_POPA - T_CH) * SR); tt = np.arange(n) / SR; kk = tt / tt[-1]
    f = 55 * 2 ** (kk * 1.0)                                    # one octave up over the whole choke
    ph = 2 * np.pi * np.cumsum(f) / SR
    rise = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3.01 * ph)) * (0.35 + 0.65 * kk ** 1.5)
    rise *= np.minimum(tt / 0.8, 1) * np.minimum((n - np.arange(n)) / (0.01 * SR), 1)     # fades in, stops dead
    M.fx_(S.bp(rise, 40, 900), T_CH, -27)
    # 1-2: x-ray in; muffled tries to cough (no air gets through)
    M.fx_(S.whoosh(0.6, 300, 2500), B[1] - 0.12, -26)
    for j, tg in enumerate(np.arange(B[1] + 0.25, B[3] - 0.3, 0.7)):
        gag(tg, -29 - (j % 2) * 2, 10 + j)
    M.fx_(S.whoosh(0.5, 2500, 300), B[2] + 1.55 - 0.1, -27)     # into the brain x-ray: it dims
    M.fx_(M.rumble(DUR[2] - 1.5, f=50, seed=8), B[2] + 1.55, -31)
    # 3: 9-1-1 on the phone, then it rings
    for j, d in enumerate('911'):
        M.fx_(dtmf(d), B[3] + 0.62 + 0.5 * j, -28)
    M.fx_(0.5 * (tone(440, 0.5) + tone(480, 0.5)), B[3] + 0.62 + 1.2, -35)
    # 4: the fist pushes in and up; cut to the chair: wood creaks as he leans on it; first thrust
    T_CHAIR, T_PUSH = 2.2, 1.55
    M.fx_(fol('thud'), B[4] + T_PUSH + 0.15, -27)
    M.fx_(fol('creak'), B[4] + T_CHAIR + 0.1, -27)
    M.fx_(fol('thud'), B[4] + T_CHAIR + 1.2, -18); M.fx_(fol('creak'), B[4] + T_CHAIR + 1.22, -28); gag(B[4] + T_CHAIR + 1.25, -28, 31)
    # 5: second thrust: it pops out, hits the table; a big gasp, breathing comes back
    M.fx_(fol('thud'), T_POPA, -17); M.fx_(fol('creak'), T_POPA + 0.02, -28)
    M.fx_(S.pop_note(60, 0.12), T_POPA + 0.02, -18)
    M.fx_(fol('clink'), T_POPA + 0.5, -26); M.fx_(fol('thud'), T_POPA + 0.5, -31)
    gasp(T_POPA + 0.12, 0.75, -17, 41); gasp(T_POPA + 1.05, 0.5, -24, 42)
    for j in range(2): thump(T_POPA + 0.6 + j * 0.55, -25)
    # 6: what not to do: x-ray, the bite slips deeper, a low buzz on the red X
    T_X6 = 1.75
    M.fx_(S.whoosh(0.5, 300, 2500), B[6] + T_X6 - 0.12, -26)
    M.fx_(S.whoosh(0.5, 900, 200), B[6] + T_X6 + 0.2, -29)
    n = int(0.35 * SR); tt = np.arange(n) / SR; M.fx_(np.sign(np.sin(2 * np.pi * 110 * tt)) * M.env(n, 0.01, 0.08) * 0.4, B[6] + T_X6 + 0.4, -33)
    # 7: sits back down (chair), slides the plate away, shaky breaths
    M.fx_(fol('thud'), B[7] + 0.03, -28); scrape(B[7] + 0.15, 0.6, -32, 71)
    gasp(B[7] + 0.5, 0.5, -31, 72)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)

elif name == 'grease':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):   # steam / sizzle
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def sizzle(t0, t1, db=-30, seed=0):                         # hot oil: dense tiny crackles
        n = int((t1 - t0) * SR); g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n) * (g.random(n) < 0.05), 2500, 10000) * M.env(n, 0.3, 0.3)
        M.fx_(x, t0, db)
    END = B[-1] + DUR[-1]
    # the fire bed follows how big the fire is (same levels as the picture)
    def level(t):
        b = max(i for i in range(len(B)) if B[i] <= t); lt = t - B[b]
        if b == 7: return 0.35 * min(1, max(0, (lt - (DUR[7] - 0.4)) / 0.35))
        if b == 0: return 0.35 + 0.35 * lt / DUR[0]
        if b in (1, 2): return 0.7 if (b == 1 and lt < 0.82) else 0.25          # the cutaway is quieter (inside the pan)
        if b == 3: return 1.3
        if b == 4: return 0.7 * (1 - max(0, min(1, (lt - 2.0) / 0.35)) * 0.85)
        if b == 5: return 0.12 * max(0, 1 - (lt - 0.35))
        if b == 6: return 1.6
        return 0
    n = int(END * SR); bed = np.asarray(F.REG['fire']['fn'](END), float)[:, :n]
    lv = np.array([level(i / SR) for i in range(0, n, 441)]); env = np.interp(np.arange(n), np.arange(0, n, 441), lv)
    bed = bed * (0.25 + 0.75 * np.minimum(env, 1.6) / 1.6) * (env > 0.01)
    M.fx_(bed / (np.abs(bed).max() + 1e-9), 0.0, -22)
    # 7: the oil heats on the burner (sizzle grows), he scrolls; it catches with a soft whoomp
    sizzle(B[7], END, -34, 3); M.fx_(S.whoosh(0.5, 200, 1800), END - 0.4, -24)
    # 0: he grabs the glass off the counter
    M.fx_(fol('clink'), B[0] + 0.95, -28)
    # 1: the throw (swish), the water hits the oil: a violent hiss and spit; cut into the pan (low muffled bubbling)
    M.fx_(fol('swish'), B[1] + 0.12, -24)
    hiss(B[1] + 0.5, 0.6, -20, 1800, 9000, 11, 0.005, 0.3); M.fx_(S.impact(0.4), B[1] + 0.5, -24)
    for j in range(6): M.fx_(S.pop_note(40 + j % 3, 0.12), B[1] + 1.2 + j * 0.42, -32)
    # 2: it boils, then flashes to steam: a sharp burst and a rising roar
    for j in range(8): M.fx_(S.pop_note(48 + j, 0.08), B[2] + 0.15 + j * 0.13, -32)
    tf = B[2] + 1.55
    M.fx_(fol('boom'), tf, -18); hiss(tf, 1.4, -21, 1500, 8000, 21, 0.003, 0.9); M.fx_(S.whoosh(1.2, 300, 3000), tf + 0.1, -25)
    # 3: the fireball: a deep whoomp and a roar up the cabinets
    M.fx_(fol('explosion'), B[3] + 0.05, -16); M.fx_(M.rumble(1.6, f=40, seed=31), B[3], -22)
    # 4: the right way: the knob clicks off, the lid slides and lands
    M.fx_(S.whoosh(0.3, 600, 2500), B[4] - 0.1, -27)
    for j in range(3): M.fx_(fol('clink'), B[4] + 0.85 + j * 0.09, -32 - 2 * j)
    M.fx_(S.whoosh(0.6, 400, 1800), B[4] + 1.3, -30); M.fx_(fol('clink'), B[4] + 2.15, -21); M.fx_(fol('thud'), B[4] + 2.15, -29)
    # 5: under the lid the flames choke out: a falling hiss
    hiss(B[5] + 0.2, 1.4, -27, 1200, 6000, 51, 0.05, 1.0)
    # 6: too big: the smoke alarm (three beeps, pause)
    k = 0
    for rep in range(2):
        for j in range(3):
            nn = int(0.45 * SR); tt = np.arange(nn) / SR
            M.fx_(np.sin(2 * np.pi * 3100 * tt) * M.env(nn, 0.005, 0.02) * 0.5, B[6] + 0.25 + rep * 2.0 + j * 0.5, -32)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)

elif name == 'fryer':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):   # steam / sizzle
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def sizzle(t0, t1, db=-30, seed=0, dens=0.05):              # hot oil: dense tiny crackles
        n = int((t1 - t0) * SR); g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n) * (g.random(n) < dens), 2500, 10000) * M.env(n, 0.3, 0.3)
        M.fx_(x, t0, db)
    END = B[-1] + DUR[-1]
    # the propane burner: a low steady roar while it's lit (beats 7, 0-2, 3 until the fire takes over, 5 until the knob, 6)
    for (t0, t1, db) in [(B[7], END, -33), (0, B[1], -33), (B[1], B[3], -40), (B[3], B[3] + 0.4, -33), (B[5], B[5] + 0.8, -33), (B[6], B[7], -36)]:
        M.fx_(M.noise(t1 - t0, 150, 1100, int(t0 * 10) + 3, 0.05, 0.1), t0, db)
    sizzle(B[7], END, -36, 3, 0.02); sizzle(0, 0.9, -36, 4, 0.02)      # hot oil ticking
    # 0: the frozen bird goes in: a violent hiss, popping and a boiling roar
    tt = B[0] + 0.87
    M.fx_(fol('clink'), B[0] + 0.1, -32)
    hiss(tt, 2.1, -19, 1500, 9000, 11, 0.004, 0.6); sizzle(tt, B[1] + 0.1, -24, 5, 0.12); M.fx_(S.impact(0.4), tt, -26)
    M.fx_(M.rumble(2.0, f=55, seed=7), tt + 0.1, -27)
    # 1: inside the pot (muffled): a low boil, bubbles popping off the ice
    M.fx_(M.rumble(DUR[1], f=45, seed=9), B[1], -28)
    for j in range(9): M.fx_(S.pop_note(42 + j % 4, 0.1), B[1] + 0.3 + j * 0.33, -32)
    # 2: the ice flashes to steam: a sharp burst, a rising roar; the oil spills over
    tf = B[2] + 0.45
    M.fx_(fol('boom'), tf, -19); hiss(tf, 2.6, -20, 1500, 8000, 21, 0.003, 0.9); M.fx_(S.whoosh(1.4, 300, 3000), tf + 0.1, -25)
    for j in range(10): M.fx_(S.pop_note(47 + j % 5, 0.08), B[2] + 0.6 + j * 0.2, -31)
    M.fx_(fol('splash'), B[2] + 1.9, -27)
    # 3: oil on the flame: the fireball, then the fire roars up the siding
    ti = B[3] + 0.3
    hiss(B[3], 0.35, -22, 1500, 8000, 31, 0.01, 0.2)
    M.fx_(fol('explosion'), ti, -15); M.fx_(M.rumble(2.4, f=40, seed=31), ti, -21)
    n3 = int((B[4] - ti) * SR); bed = np.asarray(F.REG['fire']['fn'](B[4] - ti), float)[:, :n3]
    M.fx_(bed / (np.abs(bed).max() + 1e-9) * M.env(n3, 0.15, 0.25), ti, -18)
    # 4: the fridge: its hum, the door's soft seal, a page flip for each day
    nn = int(DUR[4] * SR); tq = np.arange(nn) / SR
    M.fx_((np.sin(2 * np.pi * 60 * tq) + 0.4 * np.sin(2 * np.pi * 120 * tq)) * M.env(nn, 0.2, 0.3) * 0.5, B[4], -33)
    M.fx_(S.whoosh(0.35, 500, 2000), B[4] + 0.02, -29)
    for k in (1, 2, 3): M.fx_(fol('page'), B[4] + 0.55 + 0.85 * k, -24)
    # 5: the knob clicks off, the burner dies; the bird goes in slowly: a gentle sizzle
    M.fx_(fol('clink'), B[5] + 0.5, -30); M.fx_(fol('clink'), B[5] + 0.72, -32)
    M.fx_(S.whoosh(0.4, 1100, 200), B[5] + 0.62, -31)
    sizzle(B[5] + 2.1, B[6] + 0.3, -30, 51, 0.04)
    # 6: frying calmly out in the yard
    sizzle(B[6], B[7], -33, 61, 0.04)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)

elif name == 'energy':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def thump(t, db=-20):                                        # one heartbeat (lub-dub, lined up with the picture's pulse)
        M.fx_(S.impact(0.32), t, db); M.fx_(S.impact(0.24), t + 0.23 * 60 / bpm_, db - 5)
    def beats(t0, t1, bpm, db):                                   # the picture beats at (n + 0.05) * 60 / bpm (whole-video time)
        global bpm_; bpm_ = bpm; p = 60 / bpm; n = int(np.ceil(t0 / p - 0.05))
        while (n + 0.05) * p < t1: thump((n + 0.05) * p, db); n += 1
    def gulp(t, db=-24, seed=0):                                  # a swallow: a low wet thump
        n = int(0.16 * SR); tt = np.arange(n) / SR; g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n), 120, 700) * np.exp(-tt / 0.05) + 0.6 * np.sin(2 * np.pi * (180 - 400 * tt) * tt) * np.exp(-tt / 0.06)
        M.fx_(S.norm(x), t, db)
    def zap(t, db=-24, seed=0):                                   # an electric crackle
        n = int(0.22 * SR); g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n) * (g.random(n) < 0.25), 1500, 11000) * M.env(n, 0.002, 0.08)
        M.fx_(S.norm(x), t, db)
    END = B[-1] + DUR[-1]
    # 7: he grabs the next can and starts to drink
    M.fx_(fol('clink'), B[7] + 0.72, -28)
    for j in range(2): gulp(B[7] + 2.5 + j * 0.3, -24, j)
    # 0: gulping; the can goes down on the counter; the heartbeat comes up hard with the x-ray
    for j in range(4): gulp(B[0] + 0.1 + j * 0.3, -23, 10 + j)
    M.fx_(fol('clink'), B[0] + 2.2, -24); M.fx_(fol('thud'), B[0] + 2.2, -32)
    beats(0, B[0] + 1.85, 150, -29); beats(B[0] + 1.85, B[1], 150, -19); M.fx_(S.whoosh(0.4, 300, 2500), B[0] + 1.8, -27)
    beats(B[7], END, 150, -31)
    # 1: the can up close: fizz
    hiss(B[1], DUR[1], -34, 3000, 11000, 41, 0.2, 0.4)
    # 2: four pours into the tube; a warning beep as it passes the 400 mg line
    for k in range(4): M.fx_(fol('splash'), B[2] + 0.35 + 0.7 * k, -31 - k * 0.5)
    for j in range(3):
        nn = int(0.12 * SR); tq = np.arange(nn) / SR
        M.fx_(np.sin(2 * np.pi * 1760 * tq) * M.env(nn, 0.004, 0.03) * 0.5, B[2] + 1.25 + j * 0.18, -30)
    # 3: inside the brain: a soft low drone; caffeine clicks into each receptor, the "tired" signal bounces off
    nn = int(DUR[3] * SR); tq = np.arange(nn) / SR
    M.fx_(S.bp(np.sin(2 * np.pi * 65 * tq) + 0.5 * np.sin(2 * np.pi * 97.5 * tq), 40, 600) * M.env(nn, 0.3, 0.4), B[3], -31)
    for i in range(3): M.fx_(S.pop_note(55 + 2 * i, 0.12), B[3] + 0.75 + 0.18 * i, -27)
    for i in range(3): M.fx_(S.pop_note(76 + i, 0.09), B[3] + 1.3 + 0.25 * i + 0.45, -28)
    # 4: the heart races; then his hand shakes the can (a fine rattle)
    beats(B[4], B[5], 175, -20)
    g4 = np.random.default_rng(4); n4 = int((DUR[4] - 1.75) * SR)
    M.fx_(S.bp(g4.standard_normal(n4) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * np.arange(n4) / SR)) ** 4, 2000, 7000) * M.env(n4, 0.05, 0.1), B[4] + 1.75, -32)
    # 5: an electric storm in his brain; the heartbeat pounding under it
    beats(B[5], B[6], 180, -21)
    for j in range(14): zap(B[5] + 0.3 + j * 0.21 + 0.05 * np.sin(j * 3.1), -24 - 3 * (j % 3), 50 + j)
    # 6: five hours go by: a long falling whoosh, the heartbeat slowing
    M.fx_(S.whoosh(2.6, 2400, 300), B[6] + 0.2, -27)
    for j, tt_ in enumerate([0.3, 0.75, 1.25, 1.85, 2.5]): thump(B[6] + tt_, -26 - j)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)

elif name == 'cola':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def fizzle(t, dur, db=-30, seed=0):                           # carbonation: tiny dense pops
        n = int(dur * SR); g = np.random.default_rng(seed)
        M.fx_(S.bp(g.standard_normal(n) * (g.random(n) < 0.03), 3000, 12000) * M.env(n, 0.02, 0.4), t, db)
    def gulp(t, db=-24, seed=0):
        n = int(0.16 * SR); tt = np.arange(n) / SR; g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n), 120, 700) * np.exp(-tt / 0.05) + 0.6 * np.sin(2 * np.pi * (180 - 400 * tt) * tt) * np.exp(-tt / 0.06)
        M.fx_(S.norm(x), t, db)
    END = B[-1] + DUR[-1]
    # 7: he grabs the next can
    M.fx_(fol('clink'), B[7] + 0.75, -28)
    # 0: the can's just been cracked: a sharp pssht and fizz (frame one), then gulps
    hiss(B[0], 0.5, -19, 2500, 11000, 3, 0.002, 0.35); fizzle(B[0], 1.6, -26, 4)
    for j in range(5): gulp(B[0] + 1.55 + j * 0.42, -23, 10 + j)
    # 1: ten sugar cubes clack onto the tower
    for i in range(10): M.fx_(S.pop_note(72 + (i % 3), 0.05), B[1] + 0.15 + 0.19 * (i + 1) - 0.02, -30)
    # 2: the daily max line: a warning buzz
    nn = int(0.5 * SR); tq = np.arange(nn) / SR
    M.fx_(S.bp(np.sign(np.sin(2 * np.pi * 110 * tq)), 100, 2500) * M.env(nn, 0.01, 0.1) * 0.4, B[2] + 0.12, -29)
    # 3: x-ray: the sugar rush (rising whoosh), insulin (soft pops)
    M.fx_(S.whoosh(1.3, 300, 2600), B[3] + 0.1, -26)
    for j in range(6): M.fx_(S.pop_note(64 + 2 * (j % 3), 0.08), B[3] + 1.6 + j * 0.16, -31)
    M.fx_(S.whoosh(1.2, 2200, 400), B[3] + 2.4, -29)
    # 4: the tooth: three sips slosh over it; the acid fizzes on the enamel
    for s_ in (0.15, 1.35, 2.55): M.fx_(fol('splash'), B[4] + s_, -27); fizzle(B[4] + s_ + 0.2, 0.9, -28, int(s_ * 10))
    # 5: the extra sugar is stored as fat: low soft blobs
    for j in range(7): M.fx_(S.pop_note(40 + j % 3, 0.14), B[5] + 0.7 + j * 0.42, -30)
    # 6: weak muscles: a slow heavy heartbeat; the can slips and clatters on the floor, rolls, spills
    for j in range(5): M.fx_(S.impact(0.32), B[6] + 0.3 + j * 0.85, -27); M.fx_(S.impact(0.24), B[6] + 0.45 + j * 0.85, -32)
    td = B[6] + 2.5 + 0.47
    M.fx_(fol('clink'), td, -21); M.fx_(fol('thud'), td, -27); M.fx_(fol('clink'), td + 0.18, -28); fizzle(td + 0.1, 1.0, -29, 61)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)

elif name == 'monoxide':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def tone(f, dur, a=0.005, r=0.02):
        n = int(dur * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * f * tt) * M.env(n, a, r)
    def thump(t, db=-20):
        M.fx_(S.impact(0.32), t, db); M.fx_(S.impact(0.24), t + 0.15, db - 5)
    def idle(t0, t1, db, seed=1):                                 # the truck's engine idling: a low throb at ~30 firings a second
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR; g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n), 40, 260) * (0.6 + 0.4 * np.sin(2 * np.pi * 29 * tt)) + 0.5 * np.sin(2 * np.pi * 58 * tt) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * tt))
        M.fx_(S.norm(x) * M.env(n, 0.05, 0.05), t0, db)
    END = B[-1] + DUR[-1]
    # 7: the starter cranks, it catches, then idles
    n7 = int(0.75 * SR); tt = np.arange(n7) / SR
    M.fx_(S.bp(np.sign(np.sin(2 * np.pi * (11 + 2 * tt) * tt * 6)) * np.random.default_rng(3).standard_normal(n7) * 0.5 + np.sin(2 * np.pi * 95 * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt)), 60, 1800) * M.env(n7, 0.02, 0.05), B[7] + 0.05, -26)
    M.fx_(fol('thud'), B[7] + 0.8, -26); M.fx_(S.whoosh(0.5, 120, 600), B[7] + 0.8, -26)
    idle(B[7] + 0.8, END, -24, 1); idle(0, B[2], -24, 2)
    hiss(B[1], DUR[1], -31, 600, 3000, 11, 0.3, 0.4)                  # 1: exhaust at the pipe
    M.fx_(S.whoosh(1.0, 1800, 300), B[1] + 1.9, -29)                   # the molecules fade out
    # 2: inside the blood: the rush of flow, a heartbeat, the oxygen knocked off (pops), CO locking on (clicks)
    M.fx_(M.rumble(DUR[2], f=38, seed=21), B[2], -27); hiss(B[2], DUR[2], -34, 200, 1200, 22, 0.3, 0.4)
    for j in range(5): thump(B[2] + 0.2 + j * 0.85, -27)
    for j in range(8): M.fx_(S.pop_note(70 + (j % 4), 0.07), B[2] + 1.3 + j * 0.16, -29); M.fx_(fol('clink'), B[2] + 1.35 + j * 0.16, -38)
    # 3: x-ray: the heartbeat slows, a low tone sinks
    idle(B[3], B[4], -32, 3)
    for j, tt_ in enumerate([0.2, 0.95, 1.8, 2.75]): thump(B[3] + tt_, -22 - j)
    n3 = int(DUR[3] * SR); tq = np.arange(n3) / SR; f = 110 * 2 ** (-tq / DUR[3]); M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * M.env(n3, 0.3, 0.3) * 0.5, B[3], -30)
    # 4-5: headache and dizziness: the engine goes muffled, a ringing grows; then everything fades out as he passes out
    idle(B[4], B[6] - 0.3, -30, 4)
    n45 = int((B[6] - B[4]) * SR); tq = np.arange(n45) / SR; k = tq / tq[-1]
    ring = np.sin(2 * np.pi * 3900 * tq) * (0.15 + 0.85 * k) * (1 - np.clip((tq - (tq[-1] - 0.5)) / 0.5, 0, 1)); M.fx_(ring * 0.4, B[4], -33)
    for j in range(5): thump(B[4] + 0.3 + j * 1.0, -25 - j)
    M.fx_(S.whoosh(1.6, 900, 120), B[5] + 1.6, -27)
    # 6: open door, still idling (outside air); then the CO alarm: four beeps, a pause
    idle(B[6], B[6] + 2.2, -27, 6)
    for rep in range(2):
        for j in range(4):
            nn = int(0.12 * SR); tq = np.arange(nn) / SR
            M.fx_(np.sin(2 * np.pi * 3200 * tq) * M.env(nn, 0.004, 0.02) * 0.5, B[6] + 2.25 + rep * 1.25 + j * 0.25, -27)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)

elif name == 'starve':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def thump(t, db=-20):
        M.fx_(S.impact(0.32), t, db); M.fx_(S.impact(0.24), t + 0.15, db - 5)
    def gulp(t, db=-24, seed=0):
        n = int(0.16 * SR); tt = np.arange(n) / SR; g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n), 120, 700) * np.exp(-tt / 0.05) + 0.6 * np.sin(2 * np.pi * (180 - 400 * tt) * tt) * np.exp(-tt / 0.06)
        M.fx_(S.norm(x), t, db)
    def bed(nm, t0, t1, db):
        n = int((t1 - t0) * SR); x = np.asarray(F.REG[nm]['fn'](t1 - t0), float)[:, :n]
        M.fx_(x / (np.abs(x).max() + 1e-9) * M.env(n, 0.3, 0.3), t0, db)
    END = B[-1] + DUR[-1]
    # the woods all through: wind in the pines; crickets when it's dark
    bed('wind', 0, END, -30); bed('crickets', 0, B[1], -33); bed('crickets', B[7], END, -33); bed('crickets', B[1], B[2], -31)
    # 0: the empty bottle shaken out: plastic rattles, one drop
    for j in range(9):
        n = int(0.05 * SR); M.fx_(S.bp(np.random.default_rng(j).standard_normal(n), 1500, 7000) * M.env(n, 0.002, 0.03), B[0] + 1.05 + j * 0.14, -29)
    M.fx_(S.pop_note(88, 0.06), B[0] + 1.5 + 0.38, -28)
    # 1: three days and nights race by: three whooshes; his heartbeat
    for j in range(3): M.fx_(S.whoosh(0.9, 400 + 200 * j, 2400), B[1] + 0.3 + j * DUR[1] / 3, -28)
    for j in range(5): thump(B[1] + 0.4 + j * 0.75, -29)
    # 2: x-ray: the kidneys fail: a sinking tone; a fast, faint heartbeat
    n2 = int(DUR[2] * SR); tq = np.arange(n2) / SR; f = 140 * 2 ** (-tq / DUR[2]); M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * M.env(n2, 0.3, 0.3) * 0.5, B[2], -28)
    for j in range(int(DUR[2] / 0.5)): thump(B[2] + 0.2 + j * 0.5, -30)
    # 3: the stream babbling; he drinks
    hiss(B[3] - 0.05, DUR[3] + 0.1, -28, 300, 3000, 31, 0.15, 0.2)
    for j in range(3): gulp(B[3] + 1.3 + j * 0.35, -23, 30 + j)
    # 4: the fuel switches: a whoosh; the fat burns (soft sizzle)
    M.fx_(S.whoosh(0.8, 300, 2200), B[4] + 1.3, -27); hiss(B[4] + 1.4, DUR[4] - 1.4, -33, 2500, 9000, 41, 0.2, 0.3)
    # 5: the muscle wastes: a low groan of a tone, the heartbeat slowing
    n5 = int(DUR[5] * SR); tq = np.arange(n5) / SR; M.fx_(S.bp(np.sin(2 * np.pi * 73 * tq) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.8 * tq)), 40, 400) * M.env(n5, 0.3, 0.4), B[5], -29)
    for j in range(4): thump(B[5] + 0.3 + j * 0.95, -27 - j)
    # 6: a knife scratching tally marks on the bark, faster and faster
    k = 0.0; tt_ = B[6] + 0.25
    while tt_ < B[7] - 0.3:
        n = int(0.06 * SR); M.fx_(S.bp(np.random.default_rng(int(tt_ * 100)).standard_normal(n), 1200, 5000) * M.env(n, 0.003, 0.04), tt_, -28); tt_ += max(0.05, 0.22 - 0.05 * (tt_ - B[6]))
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)


elif name == 'brokenheart':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def tone(f, dur, a=0.005, r=0.02):
        n = int(dur * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * f * tt) * M.env(n, a, r)
    def thump(t, db=-20, k=1.0):
        M.fx_(S.impact(0.32 * k), t, db); M.fx_(S.impact(0.24 * k), t + 0.15, db - 5)
    def beats(t0, t1, bpm, db, fade=0.0):
        j, t = 0, t0
        while t < t1 - 0.1:
            thump(t, db - fade * (t - t0) / max(1e-3, t1 - t0)); j += 1; t = t0 + j * 60.0 / bpm
    def buzz(t, db=-24):
        n = int(0.32 * SR); tt = np.arange(n) / SR
        M.fx_(S.bp(np.sign(np.sin(2 * np.pi * 170 * tt)) * 0.5, 90, 900) * M.env(n, 0.01, 0.04), t, db)
    END = B[-1] + DUR[-1]
    # 7: the text comes in: two buzzes and a soft chime
    buzz(B[7] + 0.1); buzz(B[7] + 0.5)
    for j, m in enumerate((79, 84)): M.fx_(S.bell(m, 0.5, dec=0.25), B[7] + 0.15 + j * 0.1, -30)
    # 0: the shock: a deep hit, the phone thuds onto the rug, his heart starts to pound
    M.fx_(S.impact(0.9), B[0] + 0.2, -16); M.fx_(S.whoosh(0.9, 900, 120), B[0] + 0.15, -24)
    M.fx_(fol('thud'), B[0] + 0.72, -22); M.fx_(fol('clink'), B[0] + 0.75, -34)
    beats(B[0] + 0.9, B[1], 120, -24)
    # 1-2: x-ray: a hard fast heartbeat; then adrenaline floods in: a rising rush and an electric fizz
    M.fx_(S.whoosh(0.6, 300, 2400), B[1] - 0.15, -26)
    beats(B[1] + 0.1, B[3], 130, -22)
    n2 = int(DUR[2] * SR); tq = np.arange(n2) / SR; f = 90 * 2 ** (1.5 * tq / DUR[2]); M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * M.env(n2, 0.3, 0.2) * 0.5, B[2], -29)
    hiss(B[2] + 0.2, DUR[2] - 0.2, -31, 3000, 10000, 23, 0.6, 0.2)
    # 3: the big heart: a low stretching groan as its bottom balloons; a clay knock when the pot shows up
    n3 = int(2.0 * SR); tq = np.arange(n3) / SR; f = 70 * 2 ** (-0.6 * tq / 2.0)
    M.fx_(S.bp(np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tq)), 40, 600) * M.env(n3, 0.2, 0.3), B[3] + 0.3, -25)
    beats(B[3] + 0.2, B[4], 90, -27)
    M.fx_(fol('thud'), B[3] + 2.05, -27); M.fx_(S.pop_note(62, 0.08), B[3] + 2.05, -27)
    # 4: it can't pump right: weak, muffled beats over a low drone
    M.fx_(M.rumble(DUR[4], f=36, seed=41), B[4], -30); beats(B[4] + 0.2, B[5], 70, -29, 4)
    # 5: dialing 911 (three tones), then it rings
    for j, fq in enumerate((1209, 941, 941)): M.fx_((tone(fq, 0.12) + tone(fq * 0.75, 0.12)) * 0.4, B[5] + 0.3 + j * 0.22, -27)
    for j in range(2):
        nn = int(0.9 * SR); tq = np.arange(nn) / SR; M.fx_((np.sin(2 * np.pi * 440 * tq) + np.sin(2 * np.pi * 480 * tq)) * 0.25 * M.env(nn, 0.01, 0.05), B[5] + 1.2 + j * 1.4, -30)
    beats(B[5] + 0.1, B[6], 110, -29)
    # 6: weeks pass: the heart finds its shape, the beat comes back strong and steady
    M.fx_(S.whoosh(1.0, 300, 1800), B[6] + 0.1, -28); beats(B[6] + 0.3, B[7] - 0.2, 72, -25)
    for j, m in enumerate((67, 71, 74)): M.fx_(S.bell(m, 1.2, dec=0.8), B[6] + 2.2 + j * 0.12, -33)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)


elif name == 'bruise':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    def crack(t, db=-22, seed=0):                                   # a tiny vessel popping
        n = int(0.05 * SR); M.fx_(S.bp(np.random.default_rng(seed).standard_normal(n), 900, 5000) * M.env(n, 0.001, 0.03), t, db); M.fx_(S.pop_note(76 + seed % 5, 0.05), t, db - 4)
    def ooze(t, dur, db=-30, seed=0):                               # blood seeping out: a low wet gurgle
        n = int(dur * SR); tt = np.arange(n) / SR; g = np.random.default_rng(seed)
        x = S.bp(g.standard_normal(n), 80, 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 5 * tt + 3 * np.sin(2 * np.pi * 0.7 * tt)))
        M.fx_(S.norm(x) * M.env(n, 0.2, 0.4), t, db)
    def step(t, db=-28):
        M.fx_(fol('thud'), t, db)
    END = B[-1] + DUR[-1]
    # 7: the room: a soft thumb tap on the phone now and then
    for j in range(3): M.fx_(S.pop_note(96, 0.02), B[7] + 0.6 + j * 0.9, -36)
    # 0: a step, then the shin cracks into the table: a hard wooden knock and a thump; then a time-skip whoosh (next day)
    step(B[0] + 0.05, -30)
    M.fx_(S.impact(0.7), B[0] + 0.42, -12); M.fx_(fol('thud'), B[0] + 0.42, -16); M.fx_(fol('clink'), B[0] + 0.44, -30)
    M.fx_(S.whoosh(0.9, 300, 2600), B[0] + 2.0, -26); M.fx_(S.bell(77, 0.8, dec=0.5), B[0] + 2.35, -32)
    # 1: in the skin: the edge comes down hard; vessels pop; blood oozes out
    M.fx_(S.whoosh(0.35, 1200, 200), B[1] + 0.0, -26); M.fx_(S.impact(0.6), B[1] + 0.35, -13)
    for j in range(4): crack(B[1] + 0.37 + j * 0.05, -22 - 2 * j, j)
    ooze(B[1] + 0.5, DUR[1] - 0.5, -27, 11)
    # 2: the bruise darkens: a low tone sinks as it goes from red to purple
    n2 = int(DUR[2] * SR); tq = np.arange(n2) / SR; f = 220 * 2 ** (-0.8 * tq / DUR[2]); M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * M.env(n2, 0.3, 0.3) * 0.5, B[2], -30)
    ooze(B[2], DUR[2] * 0.6, -33, 12)
    # 3: days pass: a ticking clock, a brightening chime as it heals and fades
    for j in range(int(DUR[3] * 4)): M.fx_(M.tick(), B[3] + j * 0.25, -29)
    for j, m in enumerate((72, 76, 79, 84)): M.fx_(S.bell(m, 1.0, dec=0.6), B[3] + 0.6 + j * 0.9, -33)
    # 4: the question: a curious two-note sting
    for j, m in enumerate((67, 70)): M.fx_(S.bell(m, 0.6, dec=0.4), B[4] + 0.15 + j * 0.18, -30)
    # 5: older, thinner skin: a slow shrinking whoosh; a light tap still pops a vessel
    M.fx_(S.whoosh(1.6, 1800, 300), B[5] + 0.2, -28)
    M.fx_(S.impact(0.25), B[5] + 2.1, -22); crack(B[5] + 2.12, -22, 3); ooze(B[5] + 2.2, DUR[5] - 2.2, -29, 13)
    # 6: pills rattle in the bottle; then a warning tone
    for j in range(7):
        n = int(0.04 * SR); M.fx_(S.bp(np.random.default_rng(60 + j).standard_normal(n), 2000, 8000) * M.env(n, 0.002, 0.02), B[6] + 0.3 + j * 0.07, -28)
    for j in range(2):
        nn = int(0.25 * SR); tq = np.arange(nn) / SR; M.fx_(np.sin(2 * np.pi * 880 * tq) * M.env(nn, 0.01, 0.08) * 0.4, B[6] + 2.3 + j * 0.35, -30)
    M.shape(B[7] - 0.05, B[7] + 0.6, -4, 0.1)


elif name == 'screens':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def hiss(t, dur, db=-24, lo=2500, hi=9000, seed=0, a=0.01, r=0.3):
        M.fx_(M.noise(dur, lo, hi, seed, a, r), t, db)
    END = B[-1] + DUR[-1]
    def warble(t0, t1, db, k0=1.0, k1=1.0):
        # the rainbow waves: two close tones beating against each other (the sound of two grids out of step), a slow wobble on top
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR; kk = k0 + (k1 - k0) * tt / max(1e-3, t1 - t0)
        y = (np.sin(2 * np.pi * 330 * tt + 0.8 * np.sin(2 * np.pi * 0.7 * (tt + t0))) + np.sin(2 * np.pi * 333.2 * tt)) * 0.3 + 0.15 * np.sin(2 * np.pi * 660.5 * tt)
        M.fx_(S.bp(y, 150, 2400) * kk * M.env(n, 0.05, 0.05), t0, db)
    # 9 -> 0 (one sound across the loop): the TV's beach show (soft waves) and the waves' warble on his phone
    M.fx_(fol('waves', dur=B[1] + 0.1), 0.0, -33)
    warble(0.0, B[1] - 0.05, -31)
    for j, fq in enumerate((1320, 1760)): M.fx_(fol('beep', dur=0.06, f=fq), 0.12 + j * 0.09, -34)      # the phone starts recording
    # 1: the dive into the TV: a rising whoosh, then the hum and whine of millions of tiny lights
    M.fx_(S.whoosh(1.4, 300, 3200), B[1] - 0.1, -24)
    n1 = int((DUR[1] - 0.8) * SR); tq = np.arange(n1) / SR
    M.fx_((S.bp(np.sign(np.sin(2 * np.pi * 120 * tq)) * 0.3, 100, 1200) + 0.2 * np.sin(2 * np.pi * 7800 * tq)) * M.env(n1, 0.4, 0.2), B[1] + 0.8, -32)
    # 2: the sensor: light lands on the squares (tiny pings), a low chip hum
    M.fx_(M.rumble(DUR[2], f=55, seed=7), B[2], -33)
    rng = np.random.default_rng(5)
    for j in range(14): M.fx_(S.bell(int(rng.integers(86, 98)), 0.25, dec=0.12), B[2] + 0.3 + j * (DUR[2] - 0.5) / 14, -36 - 3 * rng.random())
    # 3: the top grid slides in (a soft slide), then the two grids go out of step: the beating tones slow-wobble in
    M.fx_(S.whoosh(0.9, 600, 1800), B[3] + 0.05, -27)
    n3 = int((DUR[3] - 0.9) * SR); tq = np.arange(n3) / SR; df = 0.2 + 5.0 * (tq / (DUR[3] - 0.9)) ** 1.5
    M.fx_(S.bp((np.sin(2 * np.pi * 220 * tq) + np.sin(2 * np.pi * np.cumsum(220 + df) / SR)) * 0.35, 120, 1500) * M.env(n3, 0.3, 0.1), B[3] + 0.9, -28)
    # 4: the two rings: bright (a high ding), dark (a low knock)
    M.fx_(S.bell(91, 0.6, dec=0.3), B[4] + 0.2, -28); M.fx_(fol('thud'), B[4] + 0.75, -27); M.fx_(S.bell(67, 0.4, dec=0.2), B[4] + 0.75, -31)
    n4 = int(DUR[4] * SR); tq = np.arange(n4) / SR
    M.fx_(S.bp((np.sin(2 * np.pi * 220 * tq) + np.sin(2 * np.pi * 225 * tq)) * 0.35, 120, 1500) * M.env(n4, 0.05, 0.2), B[4], -31)
    # 5: the color filters drop in: a rising rainbow arpeggio and a sparkle
    for j, m in enumerate((72, 76, 79, 84, 88, 91)): M.fx_(S.bell(m, 0.5, dec=0.3), B[5] + 0.25 + j * 0.12, -30)
    hiss(B[5] + 0.3, DUR[5] - 0.5, -36, 5000, 12000, 31, 0.4, 0.4)
    warble(B[5] + 1.2, B[6] - 0.05, -34, 0.3, 1.0)
    # 6: the dark bars roll (a low electric buzz), then slow motion: a soft thump each time the screen comes back on
    n6 = int(1.6 * SR); tq = np.arange(n6) / SR
    M.fx_(S.bp(np.sign(np.sin(2 * np.pi * 60 * tq)) * 0.3, 60, 700) * M.env(n6, 0.2, 0.15), B[6] + 0.1, -31)
    M.fx_(S.whoosh(0.5, 2000, 200), B[6] + 1.45, -27)
    tt6 = 0.0
    while tt6 < DUR[6] - 1.6 - 0.1:
        M.fx_(fol('thud'), B[6] + 1.6 + tt6, -29); M.fx_(S.bell(96, 0.08, dec=0.04), B[6] + 1.6 + tt6, -38); tt6 += 1 / 2.4
    # 7: the rows are read top to bottom: a scanner sweep per pass, a click as the screen flips on or off
    for j in range(3):
        if B[7] + j * 1.6 < B[8] - 0.2:
            M.fx_(S.whoosh(min(1.5, B[8] - (B[7] + j * 1.6)), 400, 4000), B[7] + j * 1.6, -30)
    tc = 0.0
    while tc < DUR[7] - 0.05:
        M.fx_(fol('tick'), B[7] + tc, -33); tc += 0.5 / 1.9
    # 8: he tilts the phone (a soft swish), steps back twice; the warble fades away
    M.fx_(S.whoosh(0.5, 900, 2500), B[8] + 0.1, -30)
    for j, t in enumerate((0.95, 1.35)): M.fx_(fol('step'), B[8] + t, -27)
    warble(B[8], B[8] + 2.0, -32, 1.0, 0.0)
    M.fx_(fol('waves', dur=DUR[8]), B[8], -35)
    # 9: the title (a sting), he steps back in, the waves come back on his phone (into beat 0)
    M.fx_(fol('waves', dur=DUR[9]), B[9], -34)
    for j, t in enumerate((1.75, 2.15)): M.fx_(fol('step'), B[9] + t, -27)
    warble(B[9] + 2.4, END, -31, 0.0, 1.0)


elif name == 'moon':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def chirps(t0, t1, db=-36, seed=0):                                # a cricket or two (night)
        rng = np.random.default_rng(seed); t = t0
        while t < t1 - 0.3:
            n = int(0.09 * SR); tt = np.arange(n) / SR
            M.fx_(np.sin(2 * np.pi * 4300 * tt) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 45 * tt))) * M.env(n, 0.005, 0.02), t, db); t += 0.35 + 0.5 * rng.random()
    def drone(t, dur, f=46, db=-30, seed=0):
        M.fx_(M.rumble(dur, f=f, seed=seed), t, db)
    END = B[-1] + DUR[-1]
    # the dock: water lapping on the pilings under every dock beat
    for b_ in (0, 2, 4, 9): M.fx_(fol('hull', dur=DUR[b_]), B[b_], -31)
    # 0: the moon flickers out: a glassy shimmer, a deep soft "whump" as the light drops; the bobber ducks under
    for j, m in enumerate((88, 84, 79)): M.fx_(S.bell(m, 0.4, dec=0.2), B[0] + 0.12 + j * 0.13, -31)
    M.fx_(S.impact(0.7), B[0] + 0.62, -19); M.fx_(S.whoosh(1.0, 1400, 90), B[0] + 0.3, -26)
    M.fx_(S.pop_note(58, 0.06), B[0] + 0.3, -29)
    # 1: space: a low hum; the moon pops; its last light streams down to Earth (a rising shimmer that cuts off when it lands)
    drone(B[1], DUR[1], 40, -31, 3)
    M.fx_(S.pop_note(70, 0.1), B[1] + 0.35, -24); M.fx_(S.whoosh(0.5, 3000, 600), B[1] + 0.3, -28)
    n1 = int(1.6 * SR); tq = np.arange(n1) / SR; f = 600 * 2 ** (1.2 * tq / 1.6)
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * M.env(n1, 0.3, 0.03) * 0.4, B[1] + 0.35, -32)
    # 2: the tide drains away: a sucking, falling wash and a creak of the dock
    M.fx_(S.whoosh(DUR[2] - 0.3, 900, 120), B[2] + 0.2, -27)
    # 3: space: a slow swell as the bulge shrinks
    drone(B[3], DUR[3], 44, -31, 5); M.fx_(S.whoosh(2.0, 200, 1200), B[3] + 0.5, -29)
    # 4: the dark: the sea, a cricket, very little else
    chirps(B[4] + 0.3, B[5], -37, 4)
    # 5: the beach: little sand scratches, the far waves
    M.fx_(fol('waves', dur=DUR[5]), B[5], -35)
    rng = np.random.default_rng(9)
    for j in range(26): M.fx_(M.noise(0.04, 2500, 8000, 50 + j, 0.003, 0.03), B[5] + 0.2 + rng.random() * (DUR[5] - 0.4), -36)
    # 6: the reef: muffled underwater hum and small bubbles
    drone(B[6], DUR[6], 55, -30, 7)
    for j in range(9): M.fx_(S.pop_note(76 + (j * 5) % 12, 0.04), B[6] + 0.3 + j * DUR[6] / 10, -34)
    # 7: the tilt swings over: a long rising groan under the number (the house chime marks the reveal)
    n7 = int(2.6 * SR); tq = np.arange(n7) / SR; f = 50 * 2 ** (1.0 * tq / 2.6)
    M.fx_(S.bp(np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.7 + 0.3 * np.sin(2 * np.pi * 5 * tq)), 30, 700) * M.env(n7, 0.3, 0.4), B[7] + 0.45, -26)
    # 8: cold wind on the side that hardly sees the Sun
    M.fx_(fol('wind', dur=DUR[8]), B[8], -32)
    # 9: the dark dock again; at the end the moon comes back with the same shimmer (into beat 0)
    chirps(B[9] + 0.2, END - 1.2, -37, 11)
    for j, m in enumerate((79, 84, 88)): M.fx_(S.bell(m, 0.4, dec=0.2), END - 0.85 + j * 0.13, -32)


elif name == 'sled':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def roar(t, dur, db, a=0.05, r=0.3, seed=0):                       # rocket roar: wide noise with a low rumble under it
        M.fx_(M.noise(dur, 60, 3000, seed, a, r), t, db); M.fx_(M.rumble(dur, f=38, seed=seed + 1), t, db - 3)
    def beep(t, f, dur=0.12, db=-28):
        n = int(dur * SR); tt = np.arange(n) / SR; M.fx_(np.sin(2 * np.pi * f * tt) * M.env(n, 0.004, 0.03), t, db)
    END = B[-1] + DUR[-1]
    # 0-2: ignition (a hit and a roar that keeps building), wind rising with the speed
    M.fx_(S.impact(0.9), B[0] + 0.0, -18); roar(B[0], B[3] - B[0] + 0.6, -25, 0.02, 0.6, 3)
    n = int((B[3] - B[0]) * SR); tq = np.arange(n) / SR
    M.fx_(M.noise(B[3] - B[0], 400, 6000, 7, 0.5, 0.2) * (tq / tq[-1]) ** 1.5, B[0], -27)
    M.fx_(S.whoosh(0.8, 200, 3000), B[1] - 0.2, -27); M.fx_(S.whoosh(0.8, 300, 4000), B[2] - 0.2, -27)
    # 3: the rockets burn out; just the wind tearing past
    M.fx_(M.noise(DUR[3], 300, 7000, 9, 0.05, 0.5), B[3], -27); M.fx_(S.whoosh(0.5, 4000, 300), B[3] + 0.6, -30)
    # 4: SLOW MOTION: the scoop hits the water: a deep, stretched boom and a low hiss
    M.fx_(S.impact(1.0), B[4] + 0.05, -19); drone_n = int(DUR[4] * SR); tq = np.arange(drone_n) / SR
    M.fx_(np.sin(2 * np.pi * np.cumsum(55 * 2 ** (-0.5 * tq / DUR[4])) / SR) * M.env(drone_n, 0.05, 0.4) * 0.6, B[4], -26)
    M.fx_(M.noise(DUR[4], 150, 1200, 11, 0.2, 0.4), B[4] + 0.1, -30)
    # 5: the stop: a roar of spray and a slam, then silence
    M.fx_(M.noise(1.6, 300, 8000, 13, 0.02, 0.5), B[5], -24); M.fx_(S.impact(0.8), B[5] + 0.3, -20); M.fx_(fol('thud'), B[5] + 0.35, -24)
    # 6: REPLAY at 46 g: slowed, a heavy heartbeat under a low swell
    for j in range(3): M.fx_(S.impact(0.32), B[6] + 0.3 + j * 1.1, -25); M.fx_(S.impact(0.24), B[6] + 0.45 + j * 1.1, -29)
    M.fx_(S.whoosh(DUR[6] - 0.4, 120, 600), B[6] + 0.2, -30)
    # 7: the eye: a high ringing that fades as it goes dark
    n7 = int(DUR[7] * SR); tq = np.arange(n7) / SR
    M.fx_(np.sin(2 * np.pi * 3800 * tq) * M.env(n7, 0.3, 0.8) * 0.25, B[7], -32); M.fx_(S.impact(0.4), B[7] + 0.2, -26)
    # 8: the 1954 newsreel: a projector's chatter, then today's seat belt clicks in
    t8 = B[8] + 0.1
    while t8 < B[8] + DUR[8] * 0.55: M.fx_(fol('tick'), t8, -36); t8 += 1 / 12
    M.fx_(M.noise(DUR[8] * 0.55, 80, 500, 17, 0.05, 0.1), B[8], -36)
    tc = B[8] + DUR[8] * (0.55 + 0.45 * 0.72); M.fx_(S.pop_note(76, 0.03), tc, -24); M.fx_(fol('clink'), tc + 0.01, -26)
    M.fx_(S.whoosh(0.6, 2000, 800), B[8] + DUR[8] * 0.6, -32)
    # 9: the countdown: three beeps and a high one, then the rockets catch (into beat 0)
    for j in range(3): beep(END - 2.35 + j * 0.6, 880)
    beep(END - 0.55, 1320, 0.25, -27)
    M.fx_(fol('wind', dur=DUR[9]), B[9], -36)

elif name == 'jet':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def wind(t, dur, db, seed=0, lo=150, hi=5000, rise=0.0):     # air tearing past; rise > 0 swells toward the end
        n = int(dur * SR); x = M.noise(dur, lo, hi, seed, 0.15, 0.3)[:n]
        if rise: x = x * (0.4 + 0.6 * (np.arange(len(x)) / max(1, len(x) - 1)) ** rise)
        M.fx_(x, t, db)
    def whine(t, dur, db, f=3600):                                 # jet engine whine
        n = int(dur * SR); tt = np.arange(n) / SR; M.fx_(np.sin(2 * np.pi * f * tt + 0.3 * np.sin(2 * np.pi * 0.7 * tt)) * M.env(n, 0.3, 0.3) * 0.3, t, db)
    def clacker(t, dur, db=-31):                                   # the overspeed warning: a fast mechanical clacking
        k = 0.0
        while k < dur: M.fx_(fol('tick'), t + k, db); k += 1 / 11
    def thump(t, db=-27): M.fx_(S.impact(0.35), t, db)
    def static(t, dur, db=-30): M.fx_(M.noise(dur, 900, 3500, int(t * 10), 0.01, 0.05), t, db)
    def dive(t, dur, o=0.0):
        wind(t, dur, -24 + o, 3, 120, 6000, 1.2); M.fx_(M.rumble(dur, f=34, seed=5), t, -30 + o); whine(t, dur, -34 + o, 4200); clacker(t + 0.2, dur - 0.3, -33 + o)
    # 0 the dive / 5 the dive / the loop's last second
    dive(B[0], DUR[0]); dive(B[5], DUR[5]); dive(END - 1.0, 1.0, -5)   # the loop's last second sat 2 dB hot over the music's end (ears, 2026-11-02)
    # 1 cruise: smooth engine hum   2 the storm ahead: far thunder
    whine(B[1], DUR[1], -36, 3400); M.fx_(M.rumble(DUR[1], f=40, seed=7), B[1], -38); M.fx_(fol('wind', dur=DUR[1] + DUR[2]), B[1], -38)
    M.fx_(M.rumble(2.6, f=30, seed=9), B[2] + 1.2, -27); M.fx_(M.rumble(2.0, f=26, seed=10), B[2] + 3.0, -30)
    # 3 ice and turbulence: rain/ice hiss, bumps   4 the climb request, then mayday (radio static), the nose drops
    M.fx_(M.noise(DUR[3] + DUR[4], 1500, 9000, 21, 0.3, 0.3), B[3], -31); wind(B[3], DUR[3] + DUR[4], -32, 22, 200, 3000)
    for j in range(7): thump(B[3] + 0.4 + j * 0.92 + 0.2 * np.sin(j * 2.1), -28 - (j % 3))
    static(B[4] + 0.05, 0.35); static(B[4] + DUR[4] * 0.55, 0.45, -29); wind(B[4] + DUR[4] * 0.55, DUR[4] * 0.45, -27, 23, 150, 6000, 1.5)
    # 6 Greenacres: wind, then a deep far boom and a long low rumble (kept low: nine people died)
    tI = B[6] + DUR[6] * 0.32
    wind(B[6], tI - B[6], -32, 25, 600, 6000, 2.0); M.fx_(S.impact(1.0), tI, -23); M.fx_(M.rumble(DUR[6] - (tI - B[6]), f=28, seed=27), tI, -27)
    # 7 the dark stage: a low drone
    n7 = int(DUR[7] * SR); tq = np.arange(n7) / SR; M.fx_(np.sin(2 * np.pi * 55 * tq) * M.env(n7, 0.6, 0.8) * 0.4, B[7], -33)
    # 8 storm gust: a heavy whoosh down, buffeting   9 overspeed: wind rising, the clacker
    M.fx_(S.whoosh(1.0, 1400, 200), B[8] + DUR[8] * 0.12, -25); wind(B[8], DUR[8], -31, 31, 150, 4000); thump(B[8] + DUR[8] * 0.3); thump(B[8] + DUR[8] * 0.45, -29)
    wind(B[9], DUR[9], -26, 33, 150, 7000, 1.3); clacker(B[9] + DUR[9] * 0.5, DUR[9] * 0.5)
    # 10 ice crystals ticking into the probe, the sensor icing over   11 wind building again
    for j in range(40): M.fx_(fol('tick'), B[10] + 0.2 + j * DUR[10] / 44 + 0.03 * np.sin(j * 7.3), -37 + 3 * (j % 2))
    M.fx_(M.noise(DUR[10], 3000, 11000, 35, 0.3, 0.4), B[10], -36)
    wind(B[11], DUR[11], -29, 37, 150, 5000, 1.4)
    # 12 near the speed of sound: a deep shuddering buffet   13 flutter, then a sharp tear (slow motion: low and stretched)
    M.fx_(M.rumble(DUR[12], f=22, seed=41), B[12], -26); wind(B[12], DUR[12], -30, 42, 200, 6000)
    n13 = int(DUR[13] * 0.58 * SR); tq = np.arange(n13) / SR; M.fx_(M.noise(DUR[13] * 0.58, 50, 500, 43, 0.2, 0.05)[:n13] * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * 0.35 * tq)) * (0.3 + 0.7 * tq / tq[-1]), B[13], -25)   # the tail buzzing (slowed)
    M.fx_(S.impact(0.7), B[13] + DUR[13] * 0.58, -24); M.fx_(S.whoosh(1.4, 2000, 150), B[13] + DUR[13] * 0.6, -29)
    # 14 the radar chart: soft data ticks   15 cruise hum, then the dive (into beat 0)
    for j in range(int(DUR[14] * 2.5)): M.fx_(fol('tick'), B[14] + 0.3 + j * 0.4, -38)
    whine(B[15], DUR[15] - 1.0, -37, 3400)
    M.shape(END - 4.2, END, -4.5, 0.4)          # the bed swelled ~4 dB over the last line (ears): hold it level with the rest
    M.shape(B[12], B[13], -1.5, 0.3)


elif name == 'af447':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def wind(t, dur, db, seed=0, lo=150, hi=5000, rise=0.0):
        n = int(dur * SR); x = M.noise(dur, lo, hi, seed, 0.15, 0.3)[:n]
        if rise: x = x * (0.4 + 0.6 * (np.arange(len(x)) / max(1, len(x) - 1)) ** rise)
        M.fx_(x, t, db)
    def hum(t, dur, db, f=110):                                     # airliner cabin-ish engine hum from outside: low drone + faint whine
        n = int(dur * SR); tt = np.arange(n) / SR; M.fx_((np.sin(2 * np.pi * f * tt) * 0.5 + 0.2 * np.sin(2 * np.pi * 2900 * tt)) * M.env(n, 0.4, 0.4), t, db)
    def tone(t, dur, f, db, rate=0.0):                              # warning tones (kept under the voice)
        n = int(dur * SR); tt = np.arange(n) / SR; x = np.sin(2 * np.pi * f * tt) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * rate * tt)) if rate else 1) * M.env(n, 0.01, 0.05); M.fx_(x, t, db)
    def cavalry(t, db=-30):                                          # the Airbus autopilot-disconnect "cavalry charge": a short rising/falling trill
        for j, f in enumerate([1180, 1500, 1180, 1500, 1180, 1500, 1180, 1500]): tone(t + j * 0.11, 0.1, f, db)
    def stall_tone(t, dur, db=-31): tone(t, dur, 1000, db, rate=3.5)
    def fall(t, dur, o=0.0):
        wind(t, dur, -25 + o, 3, 100, 4000, 0.8); M.fx_(M.rumble(dur, f=30, seed=5), t, -29 + o); stall_tone(t + 0.2, dur - 0.3, -33 + o)
    fall(B[0], DUR[0]); fall(B[8], DUR[8]); fall(END - 1.0, 1.0, -5)
    hum(B[1], DUR[1] + DUR[2], -35); M.fx_(fol('wind', dur=DUR[1] + DUR[2]), B[1], -38)
    M.fx_(M.rumble(2.4, f=28, seed=9), B[2] + 1.5, -29); M.fx_(M.rumble(2.0, f=24, seed=10), B[2] + 3.4, -31)
    for j in range(34): M.fx_(fol('tick'), B[3] + 0.2 + j * DUR[3] / 36 + 0.03 * np.sin(j * 7.3), -37 + 3 * (j % 2))
    M.fx_(M.noise(DUR[3], 3000, 11000, 35, 0.3, 0.4), B[3], -36)
    wind(B[4], DUR[4], -31, 41, 200, 4000); cavalry(B[4] + DUR[4] * 0.35)
    wind(B[5], DUR[5], -31, 43, 150, 3000); hum(B[5], DUR[5], -37, 100)
    n6 = int(DUR[6] * SR); tq = np.arange(n6) / SR; M.fx_(M.noise(DUR[6], 40, 300, 47, 0.2, 0.2)[:n6] * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * tq)), B[6], -27)   # buffet: the wing shuddering
    stall_tone(B[6] + DUR[6] * 0.2, DUR[6] * 0.8); stall_tone(B[7], DUR[7] * 0.9, -33); wind(B[7], DUR[7], -30, 49, 120, 3500)
    n9 = int(DUR[9] * SR); tq = np.arange(n9) / SR; M.fx_(np.sin(2 * np.pi * 55 * tq) * M.env(n9, 0.6, 0.8) * 0.4, B[9], -33)
    wind(B[10], DUR[10] * 0.6, -31, 51, 100, 2500); M.fx_(M.rumble(DUR[10] * 0.6, f=26, seed=53), B[10], -32)     # no impact sound: it fades out
    n11 = int(DUR[11] * SR); tq = np.arange(n11) / SR; M.fx_(np.sin(2 * np.pi * 42 * tq) * M.env(n11, 0.8, 0.8) * 0.5 + M.noise(DUR[11], 60, 400, 55, 0.5, 0.5)[:n11] * 0.3, B[11], -32)
    for j in range(3): tone(B[11] + 0.8 + j * 1.6, 0.05, 37500 / 9, -40)            # a faint ping (the recorders' underwater locator beacons)
    wind(B[12], DUR[12], -37, 57, 200, 3000); hum(B[13], DUR[13], -36)
    wind(B[14], DUR[14] - 1.0, -27, 59, 120, 6000, 1.2)
    M.shape(END - 4.2, END, -4.0, 0.4)

elif name == 'tackle':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def crowd(t, dur, db):                                          # a stadium crowd: broadband murmur with slow swells
        n = int(dur * SR); tt = np.arange(n) / SR; x = M.noise(dur, 250, 2500, int(t * 7) + 3, 0.6, 0.6)[:n] * (0.75 + 0.25 * np.sin(2 * np.pi * 0.23 * tt)); M.fx_(x, t, db)
    def whistle(t, dur=0.5, db=-29):
        n = int(dur * SR); tt = np.arange(n) / SR; M.fx_(np.sin(2 * np.pi * (3150 + 60 * np.sin(2 * np.pi * 28 * tt)) * tt) * M.env(n, 0.01, 0.06), t, db)
    def beat(t, db=-31): M.fx_(S.impact(0.22), t, db); M.fx_(S.impact(0.16), t + 0.16, db - 4)
    hit = B[3] + DUR[3] * 0.25                                      # the moment of contact in line 3 (then the x-ray)
    crowd(B[0], hit - B[0], -31); crowd(hit, B[4] - hit, -40); crowd(B[9], DUR[9], -39)
    M.fx_(S.impact(0.45), B[0] + 0.05, -27); M.fx_(S.impact(0.55), hit, -25); M.fx_(S.whoosh(0.9, 2400, 200), hit + 0.05, -31)
    M.fx_(S.whoosh(0.5, 300, 1500), B[2] + 0.4, -32)
    for k in range(int(DUR[5] * 0.55 / 0.84)): beat(B[5] + 0.3 + k * 0.84)
    n7 = int((DUR[5] * 0.45 + DUR[6]) * SR); tq = np.arange(n7) / SR; t7 = B[5] + DUR[5] * 0.55
    M.fx_(np.sin(2 * np.pi * 180 * tq + 3 * np.sin(2 * np.pi * 6 * tq)) * 0.3 * M.env(n7, 0.2, 0.5), t7, -35)   # the quivering heart: a thin buzz
    M.fx_(S.impact(0.4), B[7] + 0.2, -28); M.fx_(S.impact(0.25), B[7] + 0.55, -32)
    n10 = int(DUR[8] * SR); tq = np.arange(n10) / SR; M.fx_(np.sin(2 * np.pi * 48 * tq) * (tq / tq[-1]) * 0.5, B[8], -31)   # pressure building: a rising low hum
    whistle(B[9] + DUR[9] * 0.45, 0.35); whistle(B[9] + DUR[9] * 0.62, 0.35); whistle(B[9] + DUR[9] * 0.78, 0.9)
    M.fx_(M.rumble(DUR[10], f=40, seed=61), B[10], -34); M.fx_(fol('wind', dur=DUR[10]), B[10], -38)
    crowd(B[13], DUR[13], -44)
    M.shape(B[12], END, -3.0, 0.5)

elif name == 'coaster':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def rush(t, dur, db, lo=300, hi=4000):                          # wind past a fast train
        n = int(dur * SR); x = M.noise(dur, lo, hi, int(t * 11) + 5, 0.5, 0.5)[:n]; M.fx_(x * M.env(n, 0.3, 0.4), t, db)
    def clicks(t, dur, every, db):                                   # the lift chain's anti-rollback clicks
        for k in range(int(dur / every)): M.fx_(S.impact(0.05), t + k * every, db)
    def ratchet_(t, n=5, db=-30):                                    # a lap bar ratcheting down
        for k in range(n): M.fx_(S.impact(0.04), t + k * 0.07, db - k * 0.5)
    rush(B[0], DUR[0], -30); M.fx_(S.whoosh(0.9, 300, 3000), B[0] + 0.05, -29)
    clicks(B[1] + 0.2, DUR[1] - 0.4, 0.33, -33)
    rush(B[2] + 1.0, DUR[2] - 1.0, -31); M.fx_(S.whoosh(1.2, 200, 3200), B[2] + 0.9, -30)
    M.fx_(M.rumble(DUR[3], f=40, seed=71), B[3], -36); M.fx_(fol('wind', dur=DUR[3]), B[3], -40)
    rush(B[5], DUR[5] + DUR[6], -36)
    ratchet_(B[7] + DUR[7] * 0.2); M.fx_(S.impact(0.3), B[7] + DUR[7] * 0.5, -29)
    n8 = int(0.18 * SR); tq = np.arange(n8) / SR; M.fx_(np.sin(2 * np.pi * 1320 * tq) * M.env(n8, 0.01, 0.05), B[8] + DUR[8] * 0.15, -32)
    ratchet_(B[8] + DUR[8] * 0.5, 3, -33)
    ratchet_(B[9] + 0.4, 4, -32)
    M.fx_(fol('wind', dur=DUR[10]), B[10], -39)
    ratchet_(B[12] + 0.5, 2, -34)
    M.fx_(fol('wind', dur=DUR[13]), B[13], -42)
    M.shape(B[12], END, -3.0, 0.5)

elif name == 'heli':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def chop(t, dur, db, rate=11.0, seed=3):                         # rotor thump: low noise pulsed at the blade rate
        n = int(dur * SR); x = M.noise(dur, 60, 420, seed, 0.5, 0.5)[:n]; tt = np.arange(n) / SR
        am = 0.35 + 0.65 * np.clip(np.sin(2 * np.pi * rate * tt), 0, 1) ** 3
        M.fx_(x * am * M.env(n, 0.25, 0.3), t, db)
    def crunch(t, db):                                               # the strike: a hard hit, scraping metal, bits raining down
        M.fx_(S.impact(1.2), t, db); M.fx_(S.impact(0.6), t + 0.05, db - 3)
        for k in range(14): M.fx_(S.impact(0.06), t + 0.15 + 0.09 * k + 0.03 * np.sin(k * 7), db - 10 - k * 0.4)
        M.fx_(M.rumble(1.4, f=45, seed=17), t, db - 4)
    chop(B[0], 1.0, -27); crunch(B[0] + 1.0, -22)
    M.fx_(fol('wind', dur=DUR[1]), B[1], -36)
    chop(B[2], DUR[2], -30, 11.5, 5); M.fx_(fol('wind', dur=DUR[2]), B[2], -40)
    chop(B[3], DUR[3], -33, 9.0, 7)
    chop(B[4], 1.2, -30, 7.0, 9); crunch(B[4] + 1.21, -23)
    M.fx_(fol('wind', dur=DUR[5]), B[5], -38)
    chop(B[6], DUR[6] + DUR[7], -31, 11.0, 11)
    chop(B[8], 0.45, -32, 6.0, 13); M.fx_(S.impact(0.4), B[8] + 0.45, -26)
    M.fx_(fol('wind', dur=DUR[9] + DUR[10]), B[9], -40)
    M.fx_(fol('wind', dur=DUR[11]), B[11], -40)
    chop(B[12], DUR[12], -31, 11.0, 15)
    M.fx_(fol('wind', dur=DUR[13]), B[13], -42)
    M.shape(B[12], END, -3.0, 0.5)

elif name == 'grizzly':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    def gallop(t, dur, rate, db):                                   # heavy paws on dirt: two thumps per stride
        k = 0
        while k / rate < dur - 0.1:
            M.fx_(S.impact(0.12), t + k / rate, db - 2 * (k % 2)); k += 1
    def growl(t, dur, db, seed=3):                                   # a low huffing growl
        n = int(dur * SR); x = M.noise(dur, 70, 380, seed, 0.5, 0.5)[:n]; tt = np.arange(n) / SR
        M.fx_(x * (0.55 + 0.45 * np.sin(2 * np.pi * 7 * tt)) * M.env(n, 0.15, 0.4), t, db)
    def hiss(t, dur, db):                                            # bear spray firing
        n = int(dur * SR); x = M.noise(dur, 2500, 9000, 11, 0.5, 0.5)[:n]; M.fx_(x * M.env(n, 0.02, 0.4), t, db)
    for i in range(14): M.fx_(fol('wind', dur=DUR[i]), B[i], -42)
    gallop(B[0], DUR[0], 4.6, -26); growl(B[0] + 0.3, 1.4, -31)
    growl(B[4] + 0.2, 1.2, -36, 5)
    gallop(B[5], DUR[5], 5.2, -31)
    gallop(B[6], DUR[6] * 0.6, 4.6, -28); growl(B[6] + DUR[6] * 0.55, 0.9, -32, 7)
    gallop(B[7], DUR[7] * 0.5, 3.0, -32); hiss(B[7] + DUR[7] * 0.35, 1.6, -27)
    gallop(B[8] + 0.5, DUR[8] - 0.6, 4.6, -33)
    growl(B[9] + 0.4, 1.6, -38, 9)
    growl(B[11] + 0.2, 1.8, -30, 13)
    M.shape(B[12], END, -3.0, 0.5)

elif name == 'campbell':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    TC_, TD_, T0 = 0.75, 1.6, -1.5                                  # the play's times (scene: contact, all down)
    def crowd(t, dur, db, swell=0.23):                              # a domed-stadium crowd: broadband murmur with slow swells
        n = int(dur * SR); tt = np.arange(n) / SR; x = M.noise(dur, 250, 2600, int(t * 7) + 3, 0.6, 0.6)[:n] * (0.75 + 0.25 * np.sin(2 * np.pi * swell * tt)); M.fx_(x, t, db)
    def pads(t, db):                                                 # helmets and pads meeting: two dull knocks and a scuff
        M.fx_(S.impact(0.5), t, db); M.fx_(S.impact(0.3), t + 0.07, db - 3); M.fx_(S.whoosh(0.35, 900, 250), t + 0.02, db - 6)
    def clap(t, dur, db):                                            # applause: dense little noise bursts
        n = int(dur * SR); x = np.zeros(n); rng = np.random.default_rng(int(t * 13) + 7)
        for k in rng.integers(0, max(1, n - 600), int(dur * 140)): x[k:k + 400] += rng.normal(0, 1, 400) * np.exp(-np.arange(400) / 60)
        M.fx_(x / (np.max(np.abs(x)) + 1e-9) * M.env(n, 0.6, 0.8), t, db)
    hit0 = B[0] + 0.05
    crowd(B[0], B[4] - B[0], -31); pads(hit0, -26); M.fx_(M.rumble(1.4, f=38, seed=11), hit0, -33)
    u3 = (0 - T0) / 2.0; M.fx_(S.whoosh(0.7, 500, 2400), B[3] + DUR[3] * u3 - 0.5, -31)             # the throw arriving at the catch
    M.fx_(S.impact(0.12), B[3] + DUR[3] * u3, -33)
    # slow motion: everything drops low and heavy, the hit and the landing
    M.fx_(M.rumble(DUR[4], f=34, seed=21), B[4], -34); crowd(B[4], DUR[4], -40, 0.08)
    pads(B[4] + DUR[4] * 0.25, -25); M.fx_(S.whoosh(1.0, 2000, 150), B[4] + DUR[4] * 0.27, -31)
    M.fx_(S.impact(0.6), B[4] + DUR[4] * 0.9, -26); M.fx_(S.impact(0.3), B[4] + DUR[4] * 0.93, -30)
    crowd(B[5], DUR[5], -46, 0.05)                                   # the stadium goes quiet
    for i in (6, 7, 8): M.fx_(fol('wind', dur=DUR[i]), B[i], -43)
    n7 = int(DUR[7] * SR); tq = np.arange(n7) / SR; M.fx_(np.sin(2 * np.pi * 660 * tq) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * tq)) * 0.25 * M.env(n7, 0.3, 0.4), B[7], -37)   # signals running: a soft pulse
    p8 = B[8] + DUR[8] * 0.42; M.fx_(S.impact(0.35), p8, -29)
    n8 = int((B[9] - p8) * SR); tq = np.arange(n8) / SR; M.fx_(np.sin(2 * np.pi * (440 - 260 * tq / tq[-1]) * tq) * 0.25 * M.env(n8, 0.05, 0.5), p8 + 0.05, -36)   # the pulse falling away
    crowd(B[9], DUR[9], -45, 0.05)
    crowd(B[10], DUR[10] + DUR[11], -38, 0.1); clap(B[10] + DUR[10] * 0.5, DUR[10] * 0.5 + DUR[11], -35)   # the crowd applauds as the cart takes him off
    n11 = int(DUR[11] * SR); tq = np.arange(n11) / SR; M.fx_(np.sin(2 * np.pi * 90 * tq) * 0.35 * M.env(n11, 0.3, 0.6), B[11], -38)   # the cart's motor
    crowd(B[13], DUR[13], -33, 0.4)
    M.shape(B[12], END, -3.0, 0.5)

elif name == 'campbellx':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]; L = len(B) - 1
    def crowd(t, dur, db, swell=0.2):
        n = int(dur * SR); tt = np.arange(n) / SR; x = M.noise(dur, 250, 2600, int(t * 7) + 3, 0.6, 0.6)[:n] * (0.75 + 0.25 * np.sin(2 * np.pi * swell * tt)); M.fx_(x, t, db)
    def hum(t, dur, db, f=110):                                      # the x-ray room tone: a soft low hum
        n = int(dur * SR); tq = np.arange(n) / SR; M.fx_((np.sin(2 * np.pi * f * tq) + 0.4 * np.sin(2 * np.pi * 2 * f * tq)) * 0.3 * M.env(n, 0.3, 0.3), t, db)
    def snap(t, db=-27):                                             # the neck snapping forward: a dull knock and a short whoosh
        M.fx_(S.impact(0.45), t, db); M.fx_(S.whoosh(0.4, 1500, 200), t - 0.15, db - 5)
    snap(B[0] + 0.95); snap(B[L] + DUR[L] - 0.95, -29)                  # the hook's forward snap (the bend peaks 0.95 s either side of frame one)
    hum(B[0], DUR[0], -38); crowd(B[1], DUR[1], -41, 0.05)
    snap(B[2] + DUR[2] * 0.55, -29)
    for i in (2, 3, 4, 5, 6, 8, 9, 10, 11): hum(B[i], DUR[i], -39)
    n4 = int(DUR[4] * SR); tq = np.arange(n4) / SR; M.fx_(np.sin(2 * np.pi * 660 * tq) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * tq)) * 0.22 * M.env(n4, 0.3, 0.4), B[4], -38)   # signals running
    snap(B[5] + DUR[5] * 0.3, -28)
    n6 = int(DUR[6] * SR); tq = np.arange(n6) / SR; M.fx_(np.sin(2 * np.pi * (440 - 260 * tq / tq[-1]) * tq) * 0.25 * M.env(n6, 0.05, 0.5), B[6], -36)   # signals falling away
    M.fx_(fol('wind', dur=DUR[7]), B[7], -42); crowd(B[7], DUR[7], -46, 0.05)
    n8 = int(DUR[8] * SR); tq = np.arange(n8) / SR; M.fx_(np.sin(2 * np.pi * (300 + 360 * tq / tq[-1]) * tq) * 0.22 * M.env(n8, 0.3, 0.4), B[8], -37)   # waking back up: a rising tone
    M.shape(B[11], END, -3.0, 0.5)

elif name == 'acid':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    def sweep(f0, f1, dur, a=0.05, r=0.3):                      # a gliding sine
        n = int(dur * SR); return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * M.env(n, a, r)
    def gasp(t, db=-20, seed=0):                                 # a sharp breath in through a tight throat
        n = int(0.45 * SR); tt = np.arange(n) / SR; x = S.bp(np.random.default_rng(seed).standard_normal(n), 900, 4200) * np.sin(np.pi * np.minimum(tt / 0.45, 1)) ** 0.6
        M.fx_(S.norm(x) * (1 + 0.6 * np.sin(2 * np.pi * 22 * tt)), t, db)
    def cough(t, db=-21, seed=0):
        n = int(0.22 * SR); tt = np.arange(n) / SR; x = S.bp(np.random.default_rng(seed).standard_normal(n), 250, 2200) * np.exp(-tt / 0.06) * np.minimum(tt / 0.01, 1)
        M.fx_(S.norm(x), t, db)
    END = B[-1] + DUR[-1]
    M.fx_(fol('crickets', dur=END), 0.0, -37)                    # the night room under everything
    J = 1.15                                                     # the scene's jolt (beat 0)
    gurgle(0.0, J, -30, seed=3); M.fx_(sweep(180, 520, J, a=0.1, r=0.1), 0.0, -34)   # the acid climbing
    gasp(J + 0.05, -19, seed=1); cough(J + 0.6, -22, seed=2); cough(J + 0.95, -24, seed=4)
    gurgle(B[12] + DUR[12] - 1.5, 1.45, -31, seed=5); M.fx_(sweep(120, 180, 1.4, a=0.6, r=0.05), END - 1.45, -35)   # climbing again into the loop
    M.fx_(M.rumble(DUR[1], f=40, seed=7), B[1], -33)
    gurgle(B[3] + DUR[3] * 0.3, DUR[3] * 0.65, -30, seed=6)
    gasp(B[4] + DUR[4] * 0.3, -18, seed=8); cough(B[4] + DUR[4] * 0.62, -21, seed=9); gasp(B[4] + DUR[4] * 0.8, -21, seed=10)
    M.fx_(S.whoosh(1.2, 900, 300), B[5] + 0.3, -31)               # breath coming back
    for j in range(7): M.fx_(S.pop_note(96 + j % 3, 0.03), B[6] + 0.3 + j * 0.38, -31)   # drips into the lungs
    M.fx_(sweep(300, 140, DUR[7], a=0.3, r=0.6), B[7], -33)
    M.fx_(S.impact(0.3), B[9] + DUR[9] * 0.28, -24); M.fx_(S.impact(0.25), B[9] + DUR[9] * 0.35, -26)   # the risers going in
    M.fx_(fol('creak'), B[9] + DUR[9] * 0.42, -30)
    M.fx_(S.whoosh(0.8, 300, 1500), B[10] + 0.05, -29)            # rolling over (sheets)
    M.clock(B[11], B[12], db=-27, step=0.25)
    M.shape(B[12], END, -3.0, 0.5)

elif name == 'clock':
    from studio.sfx import foley as F
    def fol(nm, **kw):
        return np.asarray(F.Track.make(nm, **kw), float)
    END = B[-1] + DUR[-1]
    rng_ = np.random.default_rng(7)
    def hum(t, dur, db):                                             # the stir plate: a soft motor hum
        n = int(dur * SR); tt = np.arange(n) / SR; x = 0.6 * np.sin(2 * np.pi * 100 * tt) + 0.25 * np.sin(2 * np.pi * 200 * tt) + 0.3 * M.noise(dur, 80, 300, 3, 0.5, 0.5)[:n]
        M.fx_(x * M.env(n, 0.3, 0.3), t, db)
    def trickle(t, dur, db):                                         # a thin stream into water: hiss plus little bubble chirps
        n = int(dur * SR); x = M.noise(dur, 700, 5000, 11, 0.5, 0.5)[:n] * 0.6; tt = np.arange(n) / SR
        for k in range(int(dur * 22)):
            c = rng_.uniform(0, dur - 0.05); f0 = rng_.uniform(500, 1400); m = (tt >= c) & (tt < c + 0.04); u = tt[m] - c
            x[m] += 0.5 * np.sin(2 * np.pi * (f0 + 9000 * u) * u) * np.exp(-u / 0.012)
        M.fx_(x * M.env(n, 0.05, 0.2), t, db)
    def pop(t, db): M.fx_(fol('clink', m=98), t, db)                 # a molecule split: a tiny glassy ping
    # hook: pour, hum, then the snap
    hum(B[0], DUR[0], -38); trickle(B[0], 1.6, -30); M.fx_(fol('riser', dur=1.6), B[0] + 0.4, -34); M.fx_(S.impact(0.5), B[0] + 2.0, -27)
    hum(B[1], DUR[1], -38); hum(B[2], DUR[2], -38)
    trickle(B[2] + 0.3 * DUR[2], 0.7 * DUR[2], -30)
    for k in range(7):                                               # beat 3: each iodine pair gets split (k = pair)
        tk = B[3] + 0.35 * k + 0.9
        if tk < B[4]: pop(tk, -32)
    hum(B[4], DUR[4], -38)
    for tk in np.arange(B[4], B[5], 1.0): M.fx_(fol('tick', hi=True), tk, -34)
    for k in range(7):
        tk = B[5] - 1.2 + 0.35 * k + 0.9
        if B[5] <= tk < B[6]: pop(tk, -32)
    for k in range(3):
        tk = B[6] - 2.0 + 0.35 * k + 0.9
        if B[6] <= tk < B[7]: pop(tk, -32)
    M.fx_(fol('swish', dur=0.4), B[8] + 0.2, -34)
    hum(B[10], DUR[10], -38)
    for tk in np.arange(B[10], B[10] + 0.6 * DUR[10], 0.5): M.fx_(fol('tick', hi=True), tk, -34)
    M.fx_(fol('riser', dur=1.2), B[10] + 0.15 * DUR[10], -34); M.fx_(S.impact(0.6), B[10] + 0.62 * DUR[10], -26)
    def suction(t0, t1, db):                                         # air pulled through a tight gap, climbing until the seal lets go at t1
        dur = t1 - t0; n = int(dur * SR); tt = np.arange(n) / SR; u = tt / dur
        fc = np.minimum(220 * 14.0 ** (u ** 1.4), SR / 6)            # the hiss climbs from 220 Hz to about 3 kHz
        f_ = 2 * np.sin(np.pi * fc / SR); w = np.random.default_rng(11).standard_normal(n); y = np.zeros(n); lo = bp = 0.0
        for i in range(n):                                           # a sweeping band-pass (state-variable filter)
            hp = w[i] - lo - 0.35 * bp; bp += f_[i] * hp; lo += f_[i] * bp; y[i] = bp
        ph = 2 * np.pi * np.cumsum(330 * 4.2 ** u * (1 + 0.012 * np.sin(2 * np.pi * 7 * tt))) / SR
        y = y / (np.abs(y).max() + 1e-9) + 0.22 * np.sin(ph) * u     # a thin whistle rising with it
        g = u ** 1.6 * (1 + 0.25 * np.sin(2 * np.pi * (6 + 10 * u) * tt) * u); k = int(0.012 * SR); g[-k:] *= np.linspace(1, 0, k)
        y = y * g; M.fx_(y / (np.abs(y).max() + 1e-9), t0, db)
        m = int(0.12 * SR); tm = np.arange(m) / SR                   # the seal lets go: a low thup
        M.fx_(np.sin(2 * np.pi * np.cumsum(140 * np.exp(-tm / 0.04) + 45) / SR) * np.exp(-tm / 0.035), t1, db + 2)
    T2 = B[11] + 0.858 * DUR[11]                                     # the right beaker turns (frames 32.03-32.13 s)
    hum(B[11], DUR[11], -38); suction(T2 - 1.7, T2, -9); M.fx_(S.impact(0.4), T2, -29)
    M.shape(B[11], END, -3.0, 0.5)

elif name == 'ele':
    # Elephant toothpaste. Rule for these: something new to hear every half second or so, no dead air. Upbeat bed with a drop
    # on the eruption, a tape-stop on "super slow", builds into the pour and the bubbles, foley on every on-screen action.
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(21)
    def fizz(t, dur, db, d0=40, d1=200, lo=1800, hi=9000):          # bubbles popping: a crackle that thickens
        n = int(dur * SR); tt = np.arange(n) / SR; dens = d0 + (d1 - d0) * tt / dur
        x = (g_.random(n) < dens / SR).astype(float) * g_.uniform(0.3, 1.0, n)
        x = np.convolve(x, np.exp(-np.arange(90) / 12.0))[:n]; x = S.bp(x * g_.standard_normal(n), lo, hi)
        M.fx_(S.norm(x) * M.env(n, 0.05, 0.15), t, db, 0.15)
    def roar(t, dur, db):                                            # the eruption: a bubbly rushing swell
        n = int(dur * SR); tt = np.arange(n) / SR
        x = S.bp(g_.standard_normal(n), 120, 2500) * (0.5 + 0.5 * np.exp(-tt / 0.6))
        for _ in range(int(dur * 30)):                               # big wet bubbles
            c = g_.uniform(0, dur - 0.08); f0 = g_.uniform(140, 520); m = (tt >= c) & (tt < c + 0.07); u = tt[m] - c
            x[m] += 0.9 * np.sin(2 * np.pi * (f0 + 2600 * u) * u) * np.exp(-u / 0.02)
        M.fx_(S.norm(x) * np.minimum(tt / 0.03, 1) * np.clip((dur - tt) / 0.4, 0, 1), t, db)
    def blorp(t, db, f0=420):                                        # a squirt of thick soap
        n = int(0.32 * SR); tt = np.arange(n) / SR; f = f0 * np.exp(-tt * 5) + 90
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.4 * np.sin(2 * np.pi * 28 * tt)) + 0.3 * S.bp(g_.standard_normal(n), 200, 1500)
        M.fx_(S.norm(x) * np.exp(-tt / 0.12) * np.minimum(tt / 0.006, 1), t, db)
    def plink(t, db, f=900, pan=0.0):                                # a drop
        n = int(0.16 * SR); tt = np.arange(n) / SR; ff = f * (1 + 0.9 * (1 - np.exp(-tt / 0.012)))
        M.fx_(np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-tt / 0.05) * np.minimum(tt / 0.002, 1), t, db, pan)
    def trickle(t, dur, db):
        n = int(dur * SR); x = M.noise(dur, 700, 5000, 11, 0.05, 0.15)[:n] * 0.6; tt = np.arange(n) / SR
        for k in range(int(dur * 22)):
            c = g_.uniform(0, dur - 0.05); f0 = g_.uniform(500, 1400); m = (tt >= c) & (tt < c + 0.04); u = tt[m] - c
            x[m] += 0.5 * np.sin(2 * np.pi * (f0 + 9000 * u) * u) * np.exp(-u / 0.012)
        M.fx_(x * M.env(n, 0.05, 0.2), t, db)
    def hiss(t, dur, db):                                            # steam
        n = int(dur * SR); tt = np.arange(n) / SR
        x = S.bp(g_.standard_normal(n), 2500, 11000) * (0.7 + 0.3 * np.sin(2 * np.pi * 3.1 * tt) * np.sin(2 * np.pi * 0.7 * tt))
        M.fx_(S.norm(x) * M.env(n, 0.3, 0.4), t, db, -0.2)
    def zip_(t, db, up=True, pan=0.0):                               # the helper zipping over
        n = int(0.11 * SR); tt = np.arange(n) / SR; f = (700 + 2400 * tt / 0.11) if up else (3000 - 2200 * tt / 0.11)
        M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.11) ** 2, t, db, pan)
    def snap(t, db, pan=0.0):                                        # a bond ripped apart
        n = int(0.09 * SR); tt = np.arange(n) / SR
        x = S.bp(g_.standard_normal(n), 900, 5000) * np.exp(-tt / 0.015) + np.sin(2 * np.pi * 180 * tt) * np.exp(-tt / 0.03)
        M.fx_(S.norm(x), t, db, pan)
    def bloop(t, db, f0=300, pan=0.0):                               # a bubble blowing up
        n = int(0.2 * SR); tt = np.arange(n) / SR; f = f0 * (1 + 1.2 * tt / 0.2) * (1 + 0.03 * np.sin(2 * np.pi * 30 * tt))
        M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.2) ** 1.5, t, db, pan)
    def splat(t, db):                                                # foam landing on the tray
        n = int(0.45 * SR); tt = np.arange(n) / SR
        x = S.lp(g_.standard_normal(n), 900) * np.exp(-tt / 0.12) + 0.8 * np.sin(2 * np.pi * np.cumsum(110 * np.exp(-tt * 6) + 50) / SR) * np.exp(-tt / 0.1)
        M.fx_(S.norm(x) * np.minimum(tt / 0.004, 1), t, db)
    def glove_snap(t, db):
        n = int(0.12 * SR); tt = np.arange(n) / SR
        M.fx_(S.norm(S.bp(g_.standard_normal(n), 600, 6000) * np.exp(-tt / 0.012) + 0.6 * np.sin(2 * np.pi * 140 * tt) * np.exp(-tt / 0.025)), t, db)
    E4 = B[4] + 0.72 * DUR[4]                                        # first fizz
    M.music_drop = 1.5                                              # this bed carries energy; it sits close under the voice
    M.hype_score(bpm=120, key=57, db=-18, anchor=B[8], plan=[
        (B[1], B[2], 'light'), (B[3] + 0.0, B[3] + DUR[3] - 0.62, 'light'), (B[3] + DUR[3] - 0.62, B[4], 'stop'), (B[4], B[5], 'build'),
        (B[7] + 0.6, B[8], 'build')])
    # 0 hook: hit, the roar, crackle, the head slaps down on the tray
    M.fx_(S.impact(1.0), 0.0, -14); M.fx_(fol('boom'), 0.0, -22); roar(0.0, DUR[0] + 0.2, -15); fizz(0.0, DUR[0], -24, 200, 260); splat(1.08, -13)
    M.fx_(S.whoosh(0.45, 2400, 400), 0.55, -19); splat(1.9, -19); M.fx_(S.whoosh(0.3, 500, 2000), 2.3, -21)
    # 1 the set-up: glass clink as the camera settles, sparkle on "pure chemistry"
    M.fx_(fol('clink', m=96), B[1] + 0.35, -24); M.fx_(fol('clink', m=101), B[1] + 0.5, -27)
    for j, m in enumerate((84, 88, 91, 96)): M.fx_(S.bell(m, 0.8, dec=0.3), B[1] + 0.82 * DUR[1] + j * 0.06, -22)
    M.fx_(S.whoosh(0.5, 300, 1500), B[1] + 0.3 * DUR[1], -24, -0.3); M.fx_(fol('clink', m=105), B[1] + 0.52 * DUR[1], -25, 0.4)   # the camera drifting past the glass
    # 2 soap squirt, then the dye drips (one plink per colour) and a glug
    blorp(B[2] + 0.05 * DUR[2] + 0.15, -14); trickle(B[2] + 0.12 * DUR[2], 0.4 * DUR[2], -27)
    for k, uu in enumerate((0.16, 0.3, 0.4, 0.49)): plink(B[2] + uu * DUR[2], -18, 820 + 120 * k, (-0.4, -0.15, 0.15, 0.4)[k])
    blorp(B[2] + 0.62 * DUR[2], -22, 300)
    # 3 molecules, slow: soft wobble while they tumble, a creak as two pull apart, pop + ding when the oxygen forms
    for j in range(6): M.fx_(S.pop_note(76 + (j % 3) * 3, 0.12), B[3] + 0.25 + 0.55 * j, -26, 0.3 * np.sin(j))
    n = int(1.1 * SR); tt = np.arange(n) / SR; M.fx_(np.sin(2 * np.pi * np.cumsum(140 + 60 * tt + 8 * np.sin(2 * np.pi * 9 * tt)) / SR) * M.env(n, 0.1, 0.2), B[3] + 0.45 * DUR[3], -24)
    snap(B[3] + 0.65 * DUR[3], -18); M.fx_(S.bell(88, 0.9, dec=0.35), B[3] + 0.66 * DUR[3], -21)
    for j in range(3): M.fx_(fol('tick', hi=j % 2 == 0), B[3] + DUR[3] - 0.6 + 0.25 * j, -24)   # tick... tock... (slow)
    # 4 the pour: beaker clink, trickle, the fizz starts and climbs into the molecules
    M.fx_(fol('clink', m=93), B[4] + 0.12, -20); trickle(B[4] + 0.18 * DUR[4], 0.64 * DUR[4], -19)
    for j in range(5): plink(B[4] + (0.3 + 0.1 * j) * DUR[4], -21, 600 + 90 * j, 0.2 * np.sin(j))           # splashing into the cylinder
    M.fx_(fol('clink', m=98), B[4] + 0.84 * DUR[4], -21)                                                       # the beaker set down
    fizz(E4, B[5] - E4 + 0.1, -21, 30, 220)
    # 5 the helper: zip in, rip (water leaves), zip over, the O2 forms (ding) and flies off, zip on to the next
    u5 = lambda uu: B[5] + uu * DUR[5]
    zip_(u5(0.1), -19, True, -0.3); snap(u5(0.25), -14, -0.2); M.fx_(S.pop_note(70, 0.15), u5(0.37), -20, -0.4)
    zip_(u5(0.45), -19, True, 0.2); snap(u5(0.6), -16, 0.2); M.fx_(S.bell(91, 0.9, dec=0.35), u5(0.66), -16, 0.3)
    M.fx_(S.whoosh(0.5, 400, 3500), u5(0.68), -22, 0.3); zip_(u5(0.8), -20, False, -0.2)
    # 6 it keeps going: the same pair of sounds, fast, from three helpers, the dings climbing
    for ci, (t0, per) in enumerate(((B[6] - 0.2, 0.62), (B[6] - 0.45, 0.58), (B[6] - 0.1, 0.66))):
        for c in range(4):
            tc = t0 + c * per
            if B[6] - 0.05 <= tc + 0.2 * per < B[7]: snap(tc + 0.2 * per, -19, (-0.5, 0.5, 0.0)[ci])
            if B[6] - 0.05 <= tc + 0.7 * per < B[7]: M.fx_(S.bell(86 + 2 * c + 3 * ci, 0.6, dec=0.25), tc + 0.7 * per, -19, (-0.5, 0.5, 0.0)[ci])
    # 7 bubbles blowing up, one after another (pitch by size), little fizz
    for i in range(80):                                              # the same timing as ele.py's bubbles
        if i % 3: continue
        tb = 0.05 + 0.6 * ((np.sin(i * 13 * 127.1 + 311.7) * 43758.5453) % 1.0)
        bloop(B[7] + (tb + 0.06) * DUR[7], -21, 260 + 220 * ((i * 7) % 5) / 4, 0.6 * np.sin(i))
    fizz(B[7], DUR[7], -28, 60, 160, 3000, 10000)
    # 8 THE DROP: hit, boom, the roar out of the mouth, the slap on the tray
    M.fx_(S.impact(1.4), B[8], -11); M.fx_(fol('boom'), B[8], -17); roar(B[8], DUR[8] + 0.6, -12)
    M.fx_(S.whoosh(0.6, 300, 2600), B[8] + 0.41 * DUR[8] - 0.2, -17); M.fx_(S.impact(0.5), B[8] + 0.41 * DUR[8], -18); splat(B[8] + 0.86 * DUR[8], -12)
    fizz(B[8], B[11] + DUR[11] - B[8], -24, 220, 120)                 # the pile keeps crackling to the end
    # 9 steam
    hiss(B[9] - 0.1, DUR[9] + 0.6, -21); splat(B[9] + 0.45 * DUR[9], -19)
    for j in range(4): M.fx_(S.whoosh(0.35, 3000, 6000), B[9] + 0.15 + 0.4 * j, -26, 0.3 * (-1) ** j)      # puffs of steam
    # 10 gloves and goggles: a glove snap, the goggles' plastic clack
    glove_snap(B[10] + 0.25 * DUR[10], -15); M.fx_(fol('clack', f=900), B[10] + 0.55 * DUR[10], -18); M.fx_(fol('clack', f=1200), B[10] + 0.6 * DUR[10], -22)
    # 11 the pile, one more slump, then it loops into the hook's hit
    splat(B[11] + 0.3, -18); roar(B[11] + 0.1, 1.2, -22)

elif name == 'g9':
    # 9 G's in a fighter. Same rule as the fun science Shorts: something new to hear every half second. Driving bed with a drop when the
    # jet pulls itself up; it winds down and stops as he passes out. Jet roar outside, muffled roar + canopy wind inside, his strained
    # breathing in the mask, heartbeat and blood in the x-ray, the G-suit's air, warning beeps in the dive, a fly-past on the pull-up.
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(9)
    END = B[-1] + DUR[-1]
    def roar(t, dur, db, inside=False, seed=0, swell=0.0):          # the engine at full power: wide noise, low rumble, fan whine
        n = int(dur * SR); tt = np.arange(n) / SR; sh = 1.0 + swell * (tt / max(dur, 1e-3)) ** 1.5
        x = S.bp(np.random.default_rng(seed).standard_normal(n), 50, 900 if inside else 5000) * 1.0 + M.rumble(dur, f=36, seed=seed + 1)[:n] * 0.8
        x = x + 0.12 * np.sin(2 * np.pi * (3300 if not inside else 2400) * tt + 0.4 * np.sin(2 * np.pi * 0.6 * tt))
        M.fx_(S.norm(x) * sh * M.env(n, 0.15, 0.3), t, db)
        if inside:                                                   # air hammering the canopy
            M.fx_(M.noise(dur, 900, 6500, seed + 5, 0.15, 0.3)[:n] * (0.75 + 0.25 * np.sin(2 * np.pi * 5.3 * tt)), t, db - 7, 0.2)
    def rip(t, dur, db, pan=0.0):                                    # vapor tearing off the wings: a crackling rush
        n = int(dur * SR); tt = np.arange(n) / SR
        x = S.bp(g_.standard_normal(n), 300, 6000) * (0.4 + 0.6 * (g_.random(n) < 0.02).astype(float).cumsum() % 2)
        x = S.bp(g_.standard_normal(n), 250, 7000) * (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 13 * tt + 3 * np.sin(2 * np.pi * 2.1 * tt))))
        M.fx_(S.norm(x) * M.env(n, 0.08, 0.35), t, db, pan)
    def grunt(t, db=-17, f0=105, dur=0.22):                          # the straining breath: a hard 'huk' through the mask
        n = int(dur * SR); tt = np.arange(n) / SR; f = f0 * (1 + 0.25 * np.exp(-tt / 0.05))
        pulses = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)); v = S.bp(pulses + 0.4 * g_.standard_normal(n), 250, 1700)
        e = np.minimum(tt / 0.012, 1) * np.exp(-tt / (dur * 0.45))
        M.fx_(S.norm(v) * e, t, db); M.fx_(M.noise(0.12, 1500, 6000, int(t * 37), 0.005, 0.08), t + dur * 0.6, db - 6)
    def breath(t, db=-24, inhale=True):                              # oxygen regulator: a click and a hiss in, a softer flutter out
        d = 0.38 if inhale else 0.45; n = int(d * SR); tt = np.arange(n) / SR
        x = S.bp(g_.standard_normal(n), 1400 if inhale else 600, 7000 if inhale else 3500) * (1.0 if inhale else (0.7 + 0.3 * np.sin(2 * np.pi * 31 * tt)))
        M.fx_(S.norm(x) * np.sin(np.pi * tt / d) ** 0.7, t, db)
        if inhale: M.fx_(S.pop_note(96, 0.02), t, db - 4)
    def creak(t, dur=0.35, db=-26, f0=70):                           # leather/strap creak, helmet on the neck
        n = int(dur * SR); tt = np.arange(n) / SR; f = f0 * (1 + 0.3 * g_.standard_normal(n).cumsum() / np.sqrt(n))
        x = S.bp(np.sign(np.sin(2 * np.pi * np.cumsum(np.abs(f)) / SR)) + 0.3 * g_.standard_normal(n), 300, 2500)
        M.fx_(S.norm(x) * np.sin(np.pi * tt / dur), t, db)
    def whoosh_blood(t, dur, db, f0, f1):                            # blood rushing (a low swept noise)
        n = int(dur * SR); tt = np.arange(n) / SR; fc = f0 + (f1 - f0) * tt / dur
        x = g_.standard_normal(n); y = np.zeros(n); k_ = 0
        for c in range(0, n, 2048):
            seg = x[c:c + 2048]; y[c:c + len(seg)] = S.bp(seg, max(40, fc[c] * 0.5), fc[c] * 1.8)
        M.fx_(S.norm(y) * np.sin(np.pi * tt / dur) ** 0.8, t, db)
    def ring(t, dur, db, f=5200):                                    # ears ringing as the blood leaves
        n = int(dur * SR); tt = np.arange(n) / SR; M.fx_(np.sin(2 * np.pi * f * tt) * (0.8 + 0.2 * np.sin(2 * np.pi * 3 * tt)) * M.env(n, 0.6, 0.3) * 0.5, t, db)
    def beeps(t0, t1, db, r0, r1, f=1300):                           # warning tones, speeding up
        t = t0
        while t < t1:
            u = (t - t0) / max(t1 - t0, 1e-3); n = int(0.07 * SR); tt = np.arange(n) / SR
            M.fx_(np.sin(2 * np.pi * f * tt) * M.env(n, 0.004, 0.02), t, db); t += 1 / (r0 + (r1 - r0) * u)
    def hiss_air(t, dur, db):                                        # the G-suit valve: a click, then air rushing in
        n = int(dur * SR); tt = np.arange(n) / SR; M.fx_(fol('tick'), t, db + 2)
        x = S.bp(g_.standard_normal(n), 1800, 9000) * (0.4 + 0.6 * np.minimum(tt / 0.2, 1)) * np.clip((dur - tt) / 0.3, 0, 1)
        M.fx_(S.norm(x), t + 0.02, db)
    def rub(t, db=-25, dur=0.25):                                    # glove on the grip
        n = int(dur * SR); tt = np.arange(n) / SR; M.fx_(S.norm(S.bp(g_.standard_normal(n), 1200, 5000)) * np.sin(np.pi * tt / dur) ** 2, t, db)
    def gasp(t, db=-19):
        n = int(0.42 * SR); tt = np.arange(n) / SR; x = S.bp(g_.standard_normal(n), 900, 6500) * (tt / 0.42) ** 0.6
        M.fx_(S.norm(x) * np.clip((0.42 - tt) / 0.05, 0, 1), t, db)
    def flyby(t, dur, db):                                           # the jet tearing past the camera: rising in, a pitch drop, gone
        n = int(dur * SR); tt = np.arange(n) / SR; c = dur * 0.45
        amp = 1 / (1 + ((tt - c) / (dur * 0.12)) ** 2)
        x = g_.standard_normal(n); y = np.zeros(n)
        for k in range(0, n, 2048):
            fc = 2600 if tt[k] < c else 900; seg = x[k:k + 2048]; y[k:k + len(seg)] = S.bp(seg, fc * 0.25, fc * 2.2)
        wh = np.sin(2 * np.pi * np.cumsum(np.where(tt < c, 4200, 2900)) / SR) * 0.15
        M.fx_(S.norm(y + wh) * amp * M.env(n, 0.05, 0.3), t, db); M.fx_(M.rumble(dur, f=30, seed=77)[:n] * amp, t, db - 2)
    def ui_ticks(t0, t1, db, n):                                     # the G readout counting up
        for k in range(n): M.fx_(S.pop_note(84 + k, 0.03), t0 + (t1 - t0) * k / max(n - 1, 1), db)
    M.music_drop = 14.0          # owner (Nov 8): music way down under the voice and effects; the effects carry it
    PULL = B[9] + 0.95
    M.hype_score(bpm=120, key=57, db=-18, anchor=PULL, plan=[
        (B[2], B[5], 'light'), (B[5], B[6], 'build'), (B[6], B[7] + 0.4 * DUR[7], 'light'), (B[7] + 0.4 * DUR[7], B[8] + 1.15, 'stop'),
        (B[8] + 1.15, PULL, 'build'), (B[10], B[11], 'light')])
    # ---- 11 -> 0: the roll-in and the yank (one shot across the loop): roar swelling, vapor ripping, a grunt as the G hits
    roar(B[11], DUR[11] + 2.45, -22, seed=1, swell=0.6); rip(END - 0.9, 3.2, -24, -0.2); rip(END - 0.4, 2.6, -27, 0.3)
    M.fx_(S.whoosh(0.8, 300, 2600), END - 1.3, -25); M.fx_(M.rumble(1.4, f=28, seed=3), END - 0.8, -24)
    ui_ticks(END - 0.25, 0.95, -30, 8)
    grunt(0.35, -20); M.fx_(S.impact(0.5), 0.05, -26)
    # 0 at 2.4: inside, the roar muffled, canopy wind, his breathing
    M.fx_(S.whoosh(0.2, 2400, 500), 2.25, -22); roar(2.4, DUR[0] - 2.4 + DUR[1], -26, inside=True, seed=5)
    breath(2.55, -25); grunt(3.35, -21); creak(3.0, 0.4, -27)
    # 1 the neck: helmet creak, strain tremble, a grunt, breathing
    creak(B[1] + 0.1, 0.6, -24, 60); grunt(B[1] + 0.9, -21, 98); breath(B[1] + 1.35, -26, False); M.fx_(M.rumble(DUR[1], f=24, seed=8), B[1], -30); creak(B[1] + 1.6, 0.4, -27, 85)
    # 2 x-ray: a riser in, the heart racing, blood rushing DOWN into the legs
    M.fx_(S.whoosh(0.5, 400, 4000), B[2] - 0.3, -24); M.heartbeat(B[2] + 0.1, B[4], 150, 160, -24)
    whoosh_blood(B[2] + 0.3, 1.2, -24, 600, 120); whoosh_blood(B[2] + 1.3, 1.3, -25, 500, 90)
    for j in range(5): M.fx_(S.pop_note(60 - 2 * j, 0.06), B[2] + 0.4 + 0.42 * j, -30)          # drips of blood 'falling'
    # 3 the heart pounds, the push up the neck falls back
    for j in range(4): whoosh_blood(B[3] + 0.25 + 0.62 * j, 0.5, -26, 180, 520); whoosh_blood(B[3] + 0.55 + 0.62 * j, 0.35, -29, 500, 150)
    M.fx_(M.noise(DUR[3], 60, 300, 41, 0.3, 0.3), B[3], -31)
    # 4 the G-suit: valve click, air rushing in, fabric squeezing; then the blood pushed back UP
    hiss_air(B[4] + 0.1, 1.2, -23); creak(B[4] + 0.6, 0.5, -26, 55); creak(B[4] + 1.0, 0.4, -27, 65)
    M.fx_(S.whoosh(0.4, 500, 3500), B[4] + 0.45 * DUR[4] - 0.25, -25)
    whoosh_blood(B[4] + 0.5 * DUR[4], 1.4, -24, 120, 700); M.heartbeat(B[4] + 0.5 * DUR[4], B[5], 150, 150, -27)
    # 5 the straining move: two hard 'huk' breaths with the regulator, muscles creaking, a tremble
    def formant(x, fs_):                                             # breath noise through a mouth shape: a sum of resonances
        return sum(gn * S.bp(x, max(60, f - bw / 2), f + bw / 2) for f, bw, gn in fs_)
    def sharp_breath(tb, db=-3):
        """the straining breath (owner: hush everything but the narration and let it be heard): a hard 'HUH' out, then a fast pull in
        through the mask regulator (click, rushing hiss) cut off short when his chest is full; centred on the moment his head lifts"""
        ex_n = int(0.17 * SR); te = np.arange(ex_n) / SR
        pul = np.sign(np.sin(2 * np.pi * np.cumsum(115 * (1 + 0.2 * np.exp(-te / 0.04))) / SR))
        ex = formant(g_.standard_normal(ex_n) + 0.25 * pul, [(700, 180, 1.0), (1200, 220, 0.7), (2600, 360, 0.35)])
        ex = S.norm(ex) * np.minimum(te / 0.008, 1) * np.exp(-te / 0.06)
        in_n = int(0.34 * SR); ti = np.arange(in_n) / SR
        inh = formant(g_.standard_normal(in_n), [(450, 220, 0.5), (1900, 320, 1.0), (2800, 420, 0.6)]) + 0.8 * S.bp(g_.standard_normal(in_n), 3000, 8000)
        inh = S.norm(inh) * (ti / 0.3) ** 0.7 * np.clip((0.34 - ti) / 0.02, 0, 1)
        x = np.zeros(int(0.62 * SR)); x[:ex_n] += ex * 0.9; o_ = int(0.2 * SR); x[o_:o_ + in_n] += inh
        click = np.zeros(int(0.004 * SR)); click[0] = 1.0; x[o_:o_ + len(click)] += S.bp(click, 2000, 9000) * 6
        x = S.bp(x, 180, 7000) + 0.35 * S.bp(x, 900, 1400)          # the mask: a small hard cup round his mouth
        M.solo_(S.norm(x), tb - 0.2, db)
    for tb in (B[5] + 0.45, B[5] + 2.75):
        M.shape(tb - 0.42, tb + 0.42, -20, 0.08); sharp_breath(tb)
    creak(B[5] + 1.2, 0.6, -26, 50); creak(B[5] + 1.9, 0.4, -28, 75); roar(B[5], DUR[5], -27, inside=True, seed=11)
    M.fx_(M.rumble(DUR[5], f=22, seed=12), B[5], -29)
    # 6 his view fades: the world goes dull (muffled roar), his ears ring, the heart thumps louder
    roar(B[6], DUR[6], -27, inside=True, seed=13); ring(B[6] + 0.6, DUR[6] + 0.8, -31, 5600); M.heartbeat(B[6] + 0.2, B[7] + 0.4 * DUR[7], 140, 110, -24)
    M.fx_(S.whoosh(1.2, 2000, 200), B[6] + 1.2, -28)
    # 7 black, then out: a low drone, the helmet drops (a dull knock), the ringing cut off
    n7 = int(DUR[7] * SR); tq = np.arange(n7) / SR; M.fx_(np.sin(2 * np.pi * 48 * tq) * M.env(n7, 0.3, 0.3) * 0.5, B[7], -28)
    M.fx_(S.impact(0.4), B[7] + 0.6 * DUR[7], -24); M.fx_(fol('thud'), B[7] + 0.62 * DUR[7], -27); M.fx_(M.noise(DUR[7] * 0.5, 150, 1500, 19, 0.4, 0.3), B[7] + 0.5 * DUR[7], -32)
    # 8 the hand slides off; the stick springs back; the dive: wind rising, warning beeps speeding up
    rub(B[8] + 0.2, -24, 0.35); M.fx_(fol('tick'), B[8] + 0.62, -22); M.fx_(S.impact(0.3), B[8] + 0.7, -27)
    roar(B[8] + 1.1, DUR[8] - 1.1 + 1.0, -22, seed=17, swell=0.8); M.fx_(S.whoosh(0.5, 300, 3000), B[8] + 0.95, -24)
    beeps(B[8] + 1.3, B[9] + 0.9, -27, 3.0, 9.0, 1300)
    # 9 it pulls up by itself: chevrons beeping fast, then the G hits (a deep thump), vapor rips, the jet tears past the camera
    beeps(B[9] + 0.0, B[9] + 0.9, -27, 9.0, 12.0, 1500); M.fx_(S.impact(0.9), PULL, -20); rip(PULL, 1.6, -23)
    flyby(B[9] + 1.05, 2.2, -19); roar(B[9] + 2.6, DUR[9] - 2.6 + 0.4, -25, seed=21)
    # 10 he comes to: a gasp, fast breaths, his glove grabs the stick; then the jet climbing away
    gasp(B[10] + 0.1, -20); breath(B[10] + 0.6, -24); breath(B[10] + 1.05, -25, False); rub(B[10] + 0.65 * 1.8, -24); M.fx_(fol('tick'), B[10] + 0.8, -26)
    M.fx_(S.whoosh(0.3, 800, 2800), B[10] + 1.65, -24); roar(B[10] + 1.8, DUR[10] - 1.8, -24, seed=23)
    M.fx_(fol('jet_spooldown'), B[10] + 2.4, -31)
    for j in range(3): M.fx_(S.pop_note(79 + 4 * j, 0.05), B[10] + 2.0 + 0.12 * j, -29)                 # the '13 pilots' count

elif name == 'foot':
    # Why your foot falls asleep. Living room: couch creaks, a game on the TV, bare feet on wood, the stumble into the coffee table.
    # Inside: electric nerve signals (zips), the knee squeezing (a creaking press), the tiny vessels' trickle stopping, the nerve
    # powering down, blood rushing back, pins and needles (crackling static), an alarm buzz. Something new every half second.
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(41)
    END = B[-1] + DUR[-1]
    def couch(t, db=-24, dur=0.5):                                   # cushion squish + frame creak
        n = int(dur * SR); tt = np.arange(n) / SR
        M.fx_(S.norm(S.bp(g_.standard_normal(n), 120, 900)) * np.sin(np.pi * tt / dur) ** 1.5, t, db)
        f = 90 * (1 + 0.25 * g_.standard_normal(n).cumsum() / np.sqrt(n))
        cr = S.bp(np.sign(np.sin(2 * np.pi * np.cumsum(np.abs(f)) / SR)) + 0.3 * g_.standard_normal(n), 400, 2600)
        M.fx_(S.norm(cr) * np.sin(np.pi * tt / dur) ** 3, t + 0.05, db - 6)
    def step(t, db=-20, slap=True):                                  # bare foot on wood: low thump + skin slap
        M.fx_(fol('thud'), t, db)
        if slap: n = int(0.06 * SR); tt = np.arange(n) / SR; M.fx_(S.norm(S.bp(g_.standard_normal(n), 1200, 4500)) * np.exp(-tt / 0.012), t, db - 2)
    def scuff(t, dur=0.35, db=-22):                                  # toes dragging on the floor
        n = int(dur * SR); tt = np.arange(n) / SR
        M.fx_(S.norm(S.bp(g_.standard_normal(n), 700, 3800)) * np.sin(np.pi * tt / dur) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * tt)), t, db)
    def game(t0, t1, db=-31):                                        # a little platform game on the TV: jumps, coins, bloops
        t = t0; k = 0
        while t < t1:
            m = [72, 76, 79, 84, 79, 76, 88, 74][k % 8]
            M.fx_(S.pop_note(m, 0.06), t, db, -0.3); k += 1; t += [0.18, 0.12, 0.3, 0.22][k % 4]
            if k % 5 == 0: M.fx_(fol('tick'), t - 0.05, db - 2, 0.1)      # his thumb on a button
    def zap(t, dur=0.25, db=-22, f0=900, f1=2600, pan=0.0):           # an electric signal zipping down the nerve
        n = int(dur * SR); tt = np.arange(n) / SR; f = f0 + (f1 - f0) * (tt / dur)
        buzz = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + S.bp(g_.standard_normal(n), 1500, 5000) * 0.5
        M.fx_(S.norm(S.bp(buzz, 300, 4500)) * M.env(n, 0.005, dur * 0.5) * np.exp(-tt / (dur * 0.6)), t, db, pan)
    def crackle(t, dur, db, rate=60, seed=3):                        # pins and needles: random static clicks
        n = int(dur * SR); x = np.zeros(n); r_ = np.random.default_rng(seed)
        for _ in range(int(rate * dur)):
            i = r_.integers(0, n - 400); L_ = r_.integers(40, 300); x[i:i + L_] += r_.standard_normal(L_) * r_.uniform(0.3, 1.0) * np.exp(-np.arange(L_) / (L_ * 0.3))
        M.fx_(S.norm(S.bp(x, 1200, 5500)) * M.env(n, 0.1, 0.3), t, db)
    def press(t, dur=1.2, db=-22):                                   # the knee bearing down: a slow creaking squeeze
        n = int(dur * SR); tt = np.arange(n) / SR; f = 55 * (1 + 0.4 * np.minimum(tt / dur, 1)) * (1 + 0.15 * g_.standard_normal(n).cumsum() / np.sqrt(n))
        x = S.bp(np.sign(np.sin(2 * np.pi * np.cumsum(np.abs(f)) / SR)) + 0.4 * g_.standard_normal(n), 120, 1800)
        M.fx_(S.norm(x) * np.minimum(tt / 0.3, 1) * np.clip((dur - tt) / 0.2, 0, 1), t, db); M.fx_(M.rumble(dur, f=30, seed=5)[:n], t, db - 4)
    def trickle(t, dur, db, stop=None):                              # blood in the tiny vessels: soft bubbly ticks (cut off at 'stop')
        n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n); r_ = np.random.default_rng(7)
        for i in r_.integers(0, n - 2000, int(dur * 28)):
            L_ = 1500; f = r_.uniform(500, 1400) * (1 + np.arange(L_) / L_); x[i:i + L_] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-np.arange(L_) / 250)
        if stop is not None: x *= np.clip((t + stop - (t + tt)) / 0.25 + 1, 0, 1)
        M.fx_(S.norm(x) * M.env(n, 0.1, 0.2), t, db)
    def power_down(t, dur=1.4, db=-21):                              # the nerve shutting off: a buzz falling away
        n = int(dur * SR); tt = np.arange(n) / SR; f = 420 * np.exp(-tt / (dur * 0.35)) + 40
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.6 + np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR)
        M.fx_(S.norm(S.bp(x, 40, 3000)) * np.clip((dur - tt) / (dur * 0.6), 0, 1), t, db)
    def rush(t, dur, db, f0, f1):                                    # blood rushing (swept noise)
        n = int(dur * SR); tt = np.arange(n) / SR; fc = f0 + (f1 - f0) * tt / dur; x = g_.standard_normal(n); y = np.zeros(n)
        for c in range(0, n, 2048):
            seg = x[c:c + 2048]; y[c:c + len(seg)] = S.bp(seg, max(40, fc[c] * 0.5), fc[c] * 1.8)
        M.fx_(S.norm(y) * np.sin(np.pi * tt / dur) ** 0.7, t, db)
    def alarm(t, db=-24):                                            # two-tone buzz
        for k in range(3):
            n = int(0.13 * SR); tt = np.arange(n) / SR
            M.fx_(S.lp(np.sign(np.sin(2 * np.pi * (880 if k % 2 == 0 else 660) * tt)), 2500) * 0.4 * M.env(n, 0.01, 0.04), t + 0.16 * k, db)
    M.music_drop = 14.0          # owner (Nov 8): music way down under the voice and effects
    # owner (Nov 9): 'the Narration and overall sound of the video is loud ... the balance needs to be better'. The old house mix
    # (-14 LUFS, effects 7 dB under a nonstop voice, +2 dB air, buzzy 9 kHz zaps) was a wall of sound. Calmer: -16 LUFS, effects
    # 11 dB under the voice, no air lift, every buzz and crackle low-passed so nothing hisses or stings.
    M.lufs = -16.0; M.fx_under = 11.0; M.air = 0.0
    M.hype_score(bpm=118, key=55, db=-18, anchor=B[8], plan=[
        (0.0, B[1], 'light'), (B[1], B[2], 'light'), (B[2], B[5], 'build'), (B[5], B[7], 'light'), (B[7], B[7] + 0.8 * DUR[7], 'stop'),
        (B[7] + 0.8 * DUR[7], B[8], 'build'), (B[10], END, 'light')])
    # 11 -> 0: he gets up off the couch (one move across the loop): cushion, a step, the dead foot slaps and folds, he crashes into the table
    couch(B[11] + 0.95, -23, 0.7); step(B[11] + 1.8, -24, False)
    step(0.35, -22); M.fx_(S.whoosh(0.35, 400, 2400), 1.15, -26); step(1.62, -18); scuff(1.72, 0.3, -21)
    M.fx_(fol('creak'), 1.85, -27); M.fx_(S.whoosh(0.4, 2000, 300), 2.0, -24)
    M.fx_(fol('thud'), 2.48, -16); M.fx_(S.impact(0.5), 2.48, -21); M.fx_(fol('clink', m=88), 2.55, -25); M.fx_(fol('clink', m=93), 2.62, -27)
    # 1 an hour earlier: the game, his thumbs on the buttons, the couch
    M.fx_(S.whoosh(0.3, 3000, 600), B[1] - 0.15, -26); game(B[1] + 0.05, B[2] - 0.05); couch(B[1] + 0.6, -27, 0.5)
    # 2 x-ray in: a riser, the nerve lighting up with a hum
    M.fx_(S.whoosh(0.5, 400, 4500), B[2] - 0.3, -22); zap(B[2] + 0.35, 0.5, -24, 300, 1200)
    n2 = int(DUR[2] * SR); M.fx_(np.sin(2 * np.pi * 110 * np.arange(n2) / SR) * M.env(n2, 0.2, 0.3) * 0.4, B[2], -29)
    # 3 the muscles it works (a flex) and the skin it feels (a soft shimmer)
    M.fx_(fol('creak'), B[3] + 0.4, -25); zap(B[3] + 0.3, 0.35, -25, 600, 1500); zap(B[3] + 1.4, 0.3, -26, 1500, 3500, 0.2)
    for j in range(5): M.fx_(S.pop_note(86 + 2 * j, 0.04), B[3] + 1.6 + 0.09 * j, -31)
    # 4 signals racing down at ~100 mph: zips one after another
    for j in range(8): zap(B[4] + 0.1 + 0.3 * j, 0.22, -21 - (j % 2) * 2, 700 + 60 * j, 2600 + 80 * j, 0.3 * ((j % 3) - 1))
    # 5 the squeeze: the knee bearing down, the tiny vessels' trickle stopping
    press(B[5] + 0.2, 1.6, -21); trickle(B[5] + 0.05, DUR[5] - 0.1, -27, stop=0.8 * DUR[5]); M.fx_(fol('thud'), B[5] + 0.3, -26)
    # 6 starved: the signals fizzle out past the pinch, the nerve powers down
    zap(B[6] + 0.1, 0.25, -24); zap(B[6] + 0.55, 0.2, -27); power_down(B[6] + 0.8, 1.6, -21); M.fx_(M.rumble(DUR[6], f=26, seed=9), B[6], -30)
    # 7 slow motion: a deep slowed thump, toes scraping, the ankle rolling over
    n7 = int(DUR[7] * SR); M.fx_(np.sin(2 * np.pi * 44 * np.arange(n7) / SR) * M.env(n7, 0.3, 0.4) * 0.5, B[7], -27)
    M.fx_(fol('thud'), B[7] + 0.9, -19); scuff(B[7] + 1.2, 0.9, -21); M.fx_(fol('creak'), B[7] + 1.7, -24); M.fx_(S.whoosh(0.6, 1500, 250), B[7] + 2.2, -25)
    # 8 pressure off: blood rushes back down the leg, the heart thumping it along
    rush(B[8] - 0.1, DUR[8] + 0.3, -20, 150, 900); M.heartbeat(B[8], B[9], 90, 100, -25); M.fx_(S.impact(0.6), B[8], -24)
    # 9 pins and needles: crackling static, then he shakes it out (foot slaps)
    crackle(B[9] + 0.05, 0.62 * DUR[9], -19, 90); crackle(B[9] + 0.3, 0.5 * DUR[9], -25, 40, 5)
    for j in range(4): step(B[9] + 0.64 * DUR[9] + 0.3 * j, -24, True)
    # 10 the tingle is an alarm: a buzz, the static fading, the couch as he sits, toes wiggling
    alarm(B[10] + 0.3, -25); crackle(B[10], 0.5 * DUR[10], -27, 30, 9); couch(B[10] + 0.1, -24, 0.6)
    for j in range(4): M.fx_(fol('tick'), B[10] + 1.7 + 0.22 * j, -30)

elif name == 'cramp':
    # Charley horse. Bedroom at night: slow sleeping breaths, the duvet, the bed frame; the calf locking (a tight creaking strain), the
    # jolt up. Inside: nerve signals (zips), each squeeze of the fibres (a soft wet thump) and letting go; the end plates misfiring
    # (crackles that speed up until they fuse into a 150 Hz buzz, the real firing rate); pulling the toes back (the buzz winds down).
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(43)
    END = B[-1] + DUR[-1]
    def rustle(t, dur=0.6, db=-26, rate=30):                           # duvet / sheets: grains of soft cloth noise
        n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n); r_ = np.random.default_rng(int(t * 100) % 9973)
        for i in r_.integers(0, max(1, n - 3000), int(rate * dur)):
            L_ = r_.integers(800, 3000); x[i:i + L_] += r_.standard_normal(L_) * np.sin(np.pi * np.arange(L_) / L_) * r_.uniform(0.3, 1.0)
        M.fx_(S.norm(S.bp(x, 500, 4200)) * np.sin(np.pi * tt / dur) ** 0.6, t, db)
    def bed(t, db=-26, dur=0.45):                                      # mattress springs and the frame taking his weight
        n = int(dur * SR); tt = np.arange(n) / SR; f = 70 * (1 + 0.3 * g_.standard_normal(n).cumsum() / np.sqrt(n))
        cr = S.bp(np.sign(np.sin(2 * np.pi * np.cumsum(np.abs(f)) / SR)) + 0.3 * g_.standard_normal(n), 300, 2200)
        M.fx_(S.norm(cr) * np.sin(np.pi * tt / dur) ** 3, t, db); M.fx_(S.norm(S.bp(g_.standard_normal(n), 80, 500)) * np.sin(np.pi * tt / dur) ** 1.5, t, db - 3)
    def breath(t, dur=1.6, db=-30):                                    # slow sleeping breath (in and out)
        n = int(dur * SR); tt = np.arange(n) / SR
        M.fx_(S.norm(S.bp(g_.standard_normal(n), 250, 1600)) * np.sin(np.pi * tt / dur) ** 2 * (0.5 + 0.5 * np.sin(np.pi * tt / dur)), t, db)
    def strain(t, dur=1.2, db=-22, f0=48, f1=75):                      # the muscle locking: a slow, tight creaking squeeze
        n = int(dur * SR); tt = np.arange(n) / SR; f = (f0 + (f1 - f0) * np.minimum(tt / dur, 1)) * (1 + 0.15 * g_.standard_normal(n).cumsum() / np.sqrt(n))
        x = S.bp(np.sign(np.sin(2 * np.pi * np.cumsum(np.abs(f)) / SR)) + 0.4 * g_.standard_normal(n), 110, 1700)
        M.fx_(S.norm(x) * np.minimum(tt / 0.25, 1) * np.clip((dur - tt) / 0.2, 0, 1), t, db); M.fx_(M.rumble(dur, f=32, seed=6)[:n], t, db - 4)
    def twang(t, db=-24, f=98):                                        # the heel tendon, plucked
        n = int(0.8 * SR); tt = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * f * k * tt) / k for k in (1, 2, 3, 4)) * np.exp(-tt / 0.22)
        M.fx_(S.norm(S.lp(x, 2400)), t, db)
    def zap(t, dur=0.25, db=-22, f0=900, f1=2600, pan=0.0):           # an electric signal zipping down the nerve
        n = int(dur * SR); tt = np.arange(n) / SR; f = f0 + (f1 - f0) * (tt / dur)
        buzz = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + S.bp(g_.standard_normal(n), 1500, 5000) * 0.5
        M.fx_(S.norm(S.bp(buzz, 300, 4500)) * M.env(n, 0.005, dur * 0.5) * np.exp(-tt / (dur * 0.6)), t, db, pan)
    def squeeze(t, db=-21):                                            # the fibres pulling together: a soft wet thump, then letting go
        n = int(0.35 * SR); tt = np.arange(n) / SR; f = 140 * np.exp(-tt / 0.08) + 55
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.09) + 0.35 * S.bp(g_.standard_normal(n), 200, 900) * np.exp(-tt / 0.05)
        M.fx_(S.norm(x), t, db); M.fx_(S.norm(S.bp(g_.standard_normal(int(0.25 * SR)), 300, 1200)) * np.linspace(0, 1, int(0.25 * SR)) ** 2 * np.linspace(1, 0, int(0.25 * SR)), t + 0.18, db - 9)
    def clicks(t, dur, db, r0, r1, seed=3):                            # misfires: sharp clicks, r0 -> r1 per second
        n = int(dur * SR); x = np.zeros(n); r_ = np.random.default_rng(seed); tc = 0.0
        while tc < dur:
            i = int(tc * SR); L_ = 220
            if i + L_ < n: x[i:i + L_] += r_.standard_normal(L_) * np.exp(-np.arange(L_) / 40) * r_.uniform(0.5, 1.0)
            tc += 1.0 / (r0 + (r1 - r0) * (tc / dur) ** 2) * r_.uniform(0.7, 1.3)
        M.fx_(S.norm(S.bp(x, 900, 5000)), t, db)
    def buzz150(t, dur, db, fade_in=0.4, fade_out=0.3):                # 150 shots a second blur into one buzz: 150 Hz
        n = int(dur * SR); tt = np.arange(n) / SR
        x = np.sign(np.sin(2 * np.pi * 150 * tt)) * 0.5 + np.sin(2 * np.pi * 150 * tt) + 0.3 * np.sin(2 * np.pi * 300 * tt)
        x = S.lp(x, 2000) * (1 + 0.15 * np.sin(2 * np.pi * 9 * tt)) * np.minimum(tt / fade_in, 1) * np.clip((dur - tt) / fade_out, 0, 1)
        M.fx_(S.norm(x), t, db)
    def wind_down(t, dur=1.6, db=-21):                                 # the buzz slowing to nothing as the cramp lets go
        n = int(dur * SR); tt = np.arange(n) / SR; f = 150 * np.exp(-tt / (dur * 0.33)) + 4
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f) / SR)
        M.fx_(S.norm(S.lp(x, 1800)) * np.clip((dur - tt) / (dur * 0.6), 0, 1), t, db)
    def rub(t, dur, db=-26):                                           # a palm rubbing skin, back and forth
        n = int(dur * SR); tt = np.arange(n) / SR
        M.fx_(S.norm(S.bp(g_.standard_normal(n), 700, 3800)) * (0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 1.03 * tt))) * M.env(n, 0.1, 0.2), t, db)
    M.music_drop = 14.0
    M.lufs = -16.0; M.fx_under = 11.0; M.air = 0.0                    # the calmer house mix (owner, Nov 9)
    M.hype_score(bpm=112, key=53, db=-18, anchor=B[7], plan=[
        (0.0, B[1], 'light'), (B[1], B[2], 'light'), (B[2], B[4], 'build'), (B[4], B[5], 'light'), (B[5], B[7], 'build'),
        (B[7], B[7] + 0.5 * DUR[7], 'stop'), (B[7] + 0.5 * DUR[7], B[9], 'build'), (B[9], END, 'light')])
    # 11 -> 0 across the loop: he lies back down (duvet, bed), sleeps; then the calf locks and he jolts up
    rustle(B[11] + 0.2, 1.2, -25); bed(B[11] + 0.9, -25, 0.6); M.fx_(S.whoosh(0.5, 900, 250), B[11] + 0.7, -28); breath(B[11] + 1.9, 1.3, -31)
    strain(0.02, 1.0, -21); M.fx_(S.impact(0.4), 0.22, -24); M.fx_(S.whoosh(0.4, 300, 1800), 0.25, -24); rustle(0.3, 0.8, -23, 45); bed(0.45, -23, 0.5)
    M.fx_(fol('thud'), 0.85, -27); rustle(1.2, 0.6, -27)
    # 1 earlier: asleep, toes pointed (breaths, a little rustle as his feet point); his heart slow and steady; x-ray riser at the cut
    M.heartbeat(B[1] + 0.1, B[2] - 0.1, 58, 58, -27); bed(B[1] + 1.1, -28, 0.4)
    breath(B[1] + 0.05, 1.5, -29); rustle(B[1] + 0.6, 0.4, -30, 15); breath(B[1] + 1.6, 1.5, -30)
    M.fx_(S.whoosh(0.5, 400, 4200), B[1] + 0.5 * DUR[1] - 0.3, -24); strain(B[1] + 0.55 * DUR[1], 1.0, -27, 40, 52)
    # 2 the two calf muscles (a flex) and the tendon they pull on (a twang)
    M.fx_(fol('creak'), B[2] + 0.3, -25); M.fx_(M.rumble(1.0, f=36, seed=3), B[2] + 0.2, -29); twang(B[2] + 0.56 * DUR[2], -23)
    # 3 the tibial nerve: signals zip down into the muscles; the dive into the muscle
    for j in range(5): zap(B[3] + 0.1 + 0.32 * j, 0.24, -22 - (j % 2) * 2, 600 + 80 * j, 2400 + 100 * j, 0.25 * ((j % 3) - 1))
    M.fx_(S.whoosh(0.6, 300, 3200), B[3] + 0.72 * DUR[3], -21)
    # 4 inside: three signals, each a zip, a squeeze and a let-go (VOLLEYS in cramp.py: 0.25, 1.3, 2.35 s; arrive ~0.35 s later)
    n4 = int(DUR[4] * SR); M.fx_(M.rumble(DUR[4], f=24, seed=4)[:n4], B[4], -31)
    for v in (0.25, 1.3, 2.35): zap(B[4] + v, 0.3, -23, 500, 1600); squeeze(B[4] + v + 0.36, -21)
    # 5 misfire: clicks on their own, faster and faster, the muscle straining
    clicks(B[5] + 0.05, DUR[5] - 0.05, -22, 2.0, 30.0); strain(B[5] + 0.4, DUR[5] - 0.3, -25, 45, 70)
    for j in range(3): squeeze(B[5] + 0.5 + 0.8 * j, -25)
    # 6 a hundred and fifty a second: the clicks fuse into a 150 Hz buzz (it carries through the locked knot in 7)
    buzz150(B[6] - 0.3, DUR[6] + 0.3 + 0.4, -23, 0.35, 0.25); clicks(B[6], DUR[6], -27, 30.0, 60.0, 5)
    # 7 locked: pull back out (whoosh), the knot creaking tight; he grips it (sheets)
    M.fx_(S.whoosh(0.4, 3000, 300), B[7], -22); strain(B[7] + 0.3, DUR[7] - 0.4, -21, 52, 80); buzz150(B[7] + 0.3, 0.55 * DUR[7], -28, 0.1, 0.4)
    rustle(B[7] + 0.56 * DUR[7], 0.7, -25, 40); M.fx_(fol('thud'), B[7] + 0.58 * DUR[7], -28)
    # 8 straighten the leg, pull the toes: sheets, the bed, a long pull
    rustle(B[8] + 0.05, 1.0, -23, 40); bed(B[8] + 0.3, -26); M.fx_(S.whoosh(0.8, 250, 1200), B[8] + 0.9, -26); rustle(B[8] + 1.5, 0.5, -28)
    # 9 the stretch shuts it off: the buzz winds down to nothing, then calm
    wind_down(B[9] + 0.15, 1.7, -21); M.fx_(M.rumble(1.5, f=30, seed=8), B[9] + 0.1, -30)
    for j in range(4): M.fx_(S.pop_note(76 + 3 * j, 0.06), B[9] + 1.9 + 0.12 * j, -31)
    # 10 sore for hours: rubbing the calf, the bed, a sigh-like whoosh
    rub(B[10] + 0.1, DUR[10] - 0.3, -24); bed(B[10] + 0.2, -27); M.fx_(S.whoosh(0.9, 700, 250), B[10] + 0.4 * DUR[10], -28)
    M.fx_(fol('tick'), B[10] + 0.5 * DUR[10], -29)

elif name == 'robot':
    # The machine that builds itself. A brass clockwork robot: its balance ticks 5 times a second (tick, tock), its gear-driven arms whirr
    # (a fast run of tiny teeth clicks), parts land with small bright tinks, the tape reader's pins drop into holes (soft ticks, in time
    # with the rows in the picture), the copier's punches clack through paper; DNA and the cell get air and shimmer; the copy winds up
    # (its ratchet clicking), its heart starts ticking, its eye powers on.
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(57)
    END = B[-1] + DUR[-1]
    def tick(t, hi=True, db=-30, pan=0.0): M.fx_(fol('tick', hi=hi), t, db, pan)
    def ticking(t0, t1, db=-31, rate=5.0, ramp=0.0, pan=0.0):           # the balance: 5 ticks a second (2.5 swings), tick-tock
        k = 0; tt = t0
        while tt < t1:
            a = min(1.0, (tt - t0) / ramp) if ramp > 0 else 1.0
            tick(tt, k % 2 == 0, db + 20 * np.log10(max(a, 0.05)), pan); k += 1; tt += 1.0 / rate
    def tink(t, m=96, db=-22, pan=0.0):                                  # a brass part set down on its arbor
        M.fx_(fol('clink', m=m), t, db, pan); M.fx_(S.bell(m + 12, 0.5, dec=0.12), t + 0.004, db - 8, pan)
    def whirr(t, dur, db=-27, f0=70, f1=110, pan=0.0):                  # gear-driven joint: a run of tiny teeth clicks under a soft hum
        n = int(dur * SR); tt = np.arange(n) / SR; f = f0 + (f1 - f0) * np.sin(np.pi * tt / dur)
        ph = np.cumsum(f) / SR; teeth = np.exp(-((ph % 1.0) * 30.0)) * (0.6 + 0.4 * g_.random(n))
        x = S.bp(teeth + 0.2 * np.sin(2 * np.pi * 3 * ph), 900, 7000) + 0.25 * S.lp(np.sin(2 * np.pi * 2.0 * np.cumsum(f) / SR), 600)
        M.fx_(S.norm(x) * np.sin(np.pi * tt / dur) ** 0.7, t, db, pan)
    def paper(t, dur, db=-33):                                           # paper tape sliding over brass
        n = int(dur * SR); tt = np.arange(n) / SR
        M.fx_(S.norm(S.bp(g_.standard_normal(n), 1800, 7500)) * (0.7 + 0.3 * np.sin(2 * np.pi * 3.2 * tt)) * M.env(n, 0.1, 0.15), t, db)
    def pin(t, db=-27, pan=0.0):                                         # a reading pin dropping into a hole
        M.fx_(fol('telegraph'), t, db, pan)
    def punch_(t, db=-23, pan=0.0):                                      # a punch through paper: a dry clack and a tiny tear
        M.fx_(fol('typekey'), t, db, pan); n = int(0.03 * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 2500, 9000)) * np.exp(-np.arange(n) / (0.006 * SR)), t + 0.006, db - 6, pan)
    def ratchet(t0, t1, n_teeth, db=-24, pan=0.0):                      # winding: one click for every ratchet tooth that passes
        for k in range(n_teeth): M.fx_(fol('tick', hi=True), t0 + (t1 - t0) * (k + 0.5) / n_teeth, db - 3 * (k % 2), pan)
    def shimmer(t, dur, db=-30, base=84):                                # soft glassy air for DNA and the cell
        for j, m in enumerate((base, base + 7, base + 12, base + 16, base + 19)): M.fx_(S.bell(m, dur * 0.6, dec=dur * 0.25), t + j * dur * 0.12, db - j)
        n = int(dur * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 3000, 9000)) * np.sin(np.pi * np.arange(n) / n) ** 2, t, db - 4)
    def squelch(t, dur, db=-27):                                         # the cell pinching in two: a soft wet stretch
        n = int(dur * SR); tt = np.arange(n) / SR; f = 90 + 160 * (tt / dur) ** 2
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * tt)) + 0.3 * S.bp(g_.standard_normal(n), 200, 1200)
        M.fx_(S.norm(S.lp(x, 1500)) * np.sin(np.pi * tt / dur) ** 1.5, t, db)
    def power_up(t, db=-24):                                             # the eye lighting: a rising hum and a soft glassy ping
        n = int(0.9 * SR); tt = np.arange(n) / SR; f = 110 * 2 ** (tt / 0.9 * 1.5)
        M.fx_(S.norm(S.lp(np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR), 1800)) * (tt / 0.9) ** 1.5 * np.clip((0.9 - tt) / 0.1, 0, 1), t, db)
        M.fx_(S.bell(93, 1.2, dec=0.5), t + 0.85, db - 2)
    def power_down(t, db=-25):                                           # 'no plans': a hollow falling hum
        n = int(1.0 * SR); tt = np.arange(n) / SR; f = 220 * 2 ** (-tt * 1.6)
        M.fx_(S.norm(S.lp(np.sin(2 * np.pi * np.cumsum(f) / SR), 1200)) * np.exp(-tt / 0.45), t, db)
    # the tape bits, the same hash the picture uses (robot.py tape_bit / hole_depth) so pin and punch sounds land on real holes
    def tbit(row, col):
        if col == 2: return True
        v = np.float32(np.sin(np.float32(row) * np.float32(12.9898) + np.float32(col) * np.float32(78.233))) * np.float32(43758.55)
        return float(v - np.floor(v)) > 0.45
    def tape_path_top():
        P = [np.array((-0.011 + 0.0069 * np.cos(a), 0.012 + 0.0069 * np.sin(a))) for a in np.linspace(np.pi * 0.95, np.pi * 0.5, 7)]
        a0 = P[-1]; a1 = np.array((0.0033 * np.cos(np.pi * 0.75), 0.024 + 0.0033 * np.sin(np.pi * 0.75)))
        P += [a0 + (a1 - a0) * k / 6 for k in range(1, 7)]
        P += [np.array((0.0033 * np.cos(a), 0.024 + 0.0033 * np.sin(a))) for a in np.linspace(np.pi * 0.75, np.pi * 0.25, 13)[1:]]
        return sum(np.linalg.norm(P[i] - P[i - 1]) for i in range(1, 19))
    TU_TOP, ROW = tape_path_top(), 0.0025
    def row_events(t0, t1, coord_at, cols=(1, 3, 4)):                    # (time, number of holes) each time a row centre passes the pins
        out = []; ts = np.arange(t0, t1, 1.0 / 600); c = np.array([coord_at(x) for x in ts]); r = np.floor(c / ROW - 0.5)
        for i in range(1, len(ts)):
            if r[i] != r[i - 1]:
                rr = int(max(r[i], r[i - 1])); nb_ = sum(tbit(rr, cc) for cc in cols)
                if nb_: out.append((ts[i], nb_))
        return out
    M.music_drop = 14.0
    M.lufs = -16.0; M.fx_under = 11.0; M.air = 0.0                    # the calmer house mix (owner, Nov 9)
    st5 = B[5] + 0.55 * DUR[5]; wake = B[10] + 0.4 * DUR[10]
    M.hype_score(bpm=100, key=57, db=-18, anchor=wake, plan=[
        (0.0, B[2], 'light'), (B[2], B[4], 'full'), (B[4], B[5], 'light'), (B[5], st5, 'build'), (st5, B[6], 'stop'),
        (B[6], B[10], 'light'), (B[10], wake, 'build'), (wake, END, 'full')])
    # all through the workshop beats the builder ticks quietly (louder in its close-ups)
    ticking(0.0, B[4], -33); ticking(B[5], B[8], -34); ticking(B[10] + 0.4 * DUR[10], END, -32, ramp=0.4)
    # 0 picks a wheel out of the tray (whirr down, grip click), carries it (whirr), sets it on the copy (tink)
    whirr(0.0, 0.8, -26, 80, 120, 0.2); M.fx_(fol('clack'), 0.27 * 0.92 * DUR[0], -30, 0.2)
    whirr(0.34 * 0.92 * DUR[0], 0.52 * 0.92 * DUR[0], -25, 60, 130, -0.1); tink(0.9 * 0.92 * DUR[0], 96, -22, -0.2)
    # 1 the reader: paper sliding, a pin dropping into each hole as the rows pass
    paper(B[1], DUR[1], -31)
    for te, nh in row_events(B[1], B[2], lambda x: TU_TOP - x * 0.008):
        for j in range(nh): pin(te + 0.012 * j, -27 + 2 * (j == 0), 0.15 * (j - 1))
    # 2 one row, one part: whirr to the tray, grip, carry, set the third wheel in
    u2 = lambda v: B[2] + DUR[2] * (0.05 + 0.9 * v)
    whirr(u2(0.0), u2(0.25) - u2(0.0), -26, 70, 120); M.fx_(fol('clack'), u2(0.3), -30); whirr(u2(0.34), u2(0.86) - u2(0.34), -25, 60, 125); tink(u2(0.9), 99, -22)
    # 3 two wheels drop onto their arbors and mesh; then the builder's own train turning fast (teeth chattering)
    tink(B[3] + 0.22 * DUR[3], 101, -22, 0.2); tink(B[3] + 0.4 * DUR[3], 94, -22, -0.2)
    ticking(B[3] + 0.45 * DUR[3], B[4], -26, rate=30.0); whirr(B[3] + 0.45 * DUR[3], 0.55 * DUR[3], -27, 140, 160)
    # 4 its heart: the balance close up, tick and tock loud and clear, a little spring shimmer
    ticking(B[4], B[5], -22); M.fx_(S.bell(100, 2.0, dec=0.9), B[4] + 0.3, -36)
    # 5 time-lapse: every part lands (a flurry of tinks, the arms a blur), then the empty copy: power down, tape-stop in the score
    nl = 19
    for i in range(nl): tink(B[5] + DUR[5] * (0.04 + 0.5 * (i + 1.4) / nl), (89, 94, 96, 99, 101, 103)[i % 6], -27 - (i % 3), 0.3 * ((i % 3) - 1))
    whirr(B[5], 0.58 * DUR[5], -27, 160, 200); power_down(st5 - 0.05, -25)
    # 6 the copier: tape sliding, a punch clack on every row that has a hole, chips pattering down the chute
    paper(B[6], DUR[6], -29)
    for te, nh in row_events(B[6], B[7], lambda x: 0.07 - 0.06 + (x - B[6]) * 0.02):
        punch_(te, -23 - (3 - nh)); pin(te - 0.01, -31, 0.3)
        for j in range(nh): M.fx_(S.pop_note(108 + 2 * j, 0.02), te + 0.05 + 0.03 * j, -38, -0.3)
    # 7 the copied tape goes into the copy: arm whirr, slide, a solid latch click
    whirr(B[7] + 0.05, 0.6 * DUR[7], -26, 70, 115, 0.2); paper(B[7] + 0.3 * DUR[7], 0.4 * DUR[7], -32); M.fx_(fol('clack'), B[7] + 0.72 * DUR[7], -23)
    tink(B[7] + 0.73 * DUR[7], 91, -27); whirr(B[7] + 0.76 * DUR[7], 0.22 * DUR[7], -29, 90, 120, 0.2)
    # 8 DNA, 9 the cell: air and glassy shimmer; the cell pinching in two
    shimmer(B[8] + 0.05, DUR[8], -29, 84); M.fx_(S.whoosh(1.2, 300, 2200), B[8] + 0.4, -32)
    shimmer(B[9] + 0.05, DUR[9], -30, 81); squelch(B[9] + 0.45 * DUR[9], 0.55 * DUR[9], -26)
    # 10 the copy winds up (ratchet clicking, one per tooth), its heart starts ticking, its eye powers on, it stands
    ratchet(B[10], B[10] + 0.4 * DUR[10], 19, -24); ticking(B[10] + 0.4 * DUR[10], B[11], -24, ramp=0.5)
    power_up(B[10] + 0.66 * DUR[10], -24); whirr(B[10] + 0.74 * DUR[10], 0.26 * DUR[10], -25, 60, 110)
    for k in range(6): M.fx_(fol('clink', m=103), B[10] + 0.95 * DUR[10] + 0.01 * k, -34)
    # 11 it walks to the tray (tripod gait: three feet land together, twice a step), then reaches for the next wheel (the loop)
    nst = 8; t11 = np.linspace(0, 1, 2000); kw = np.clip(t11 / 0.6, 0, 1); kw = kw * kw * (3 - 2 * kw)
    for g in (0, 1):
        for i in range(nst):
            land = (i + 1 + 0.5 * g) / nst
            if land <= 1.0:
                tl = B[11] + DUR[11] * float(t11[np.searchsorted(kw, land - 1e-6)])
                for j in range(3): M.fx_(fol('clink', m=(98, 101, 103)[j]), tl + 0.006 * j, -31 - j, 0.3 * (j - 1))
    whirr(B[11], 0.6 * DUR[11], -29, 90, 130); whirr(B[11] + 0.6 * DUR[11], 0.4 * DUR[11] + 0.05, -26, 80, 120, 0.2)

elif name == 'stone':
    # Kidney stone. He drops to his knees at the counter (gasp, knees on the floor); inside: a heartbeat and blood rushing in, pee
    # trickling down; in the kidney the waste crowds (fizzing gets thicker), crystals click together (glassy ticks), the stone
    # stacks up (stony clacks, lower each time); it drops into the ureter (a clunk, a slide); it scrapes (gritty rasp) and jams
    # (thud); the pain comes in waves (low swells with a held tone); a small one rattles through; water runs into a glass.
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(50)
    END = B[-1] + DUR[-1]
    def breath(t, dur=0.5, db=-27, sharp=True):                         # a sharp breath in through the teeth / a strained breath out
        n = int(dur * SR); tt = np.arange(n) / SR; x = S.bp(g_.standard_normal(n), 1400 if sharp else 500, 5200 if sharp else 2200)
        M.fx_(S.norm(x) * (np.minimum(tt / 0.05, 1) * np.exp(-tt / (dur * 0.45)) if sharp else np.sin(np.pi * tt / dur) ** 1.5), t, db)
    def tink(t, m=100, db=-25, pan=0.0):                                # two specks or crystals touching: a small glassy tick
        M.fx_(fol('clink', m=m), t, db, pan)
    def clack(t, db=-23, pan=0.0, lo=900):                              # a crystal landing on the stone: dry and stony
        n = int(0.07 * SR); x = S.bp(g_.standard_normal(n), lo, lo * 4) * np.exp(-np.arange(n) / (0.012 * SR)); M.fx_(S.norm(x), t, db, pan); M.fx_(S.pop_note(52, 0.05), t, db - 6, pan)
    def fizz(t, dur, db=-31, f0=2500, f1=6000, swell=True):             # waste in the water: a fine fizz that thickens
        n = int(dur * SR); tt = np.arange(n) / SR; x = S.bp(g_.standard_normal(n), f0, f1) * (0.6 + 0.4 * g_.random(n))
        M.fx_(S.norm(x) * ((tt / dur) ** 1.2 if swell else np.sin(np.pi * tt / dur)) * M.env(n, 0.05, 0.1), t, db)
    def rasp(t, dur, db=-24):                                           # stone on the lining: a gritty scrape, low-passed (no harsh top)
        n = int(dur * SR); tt = np.arange(n) / SR; x = S.bp(g_.standard_normal(n), 300, 2600) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 23 * tt + 3 * np.sin(2 * np.pi * 5 * tt))))
        M.fx_(S.norm(S.lp(x, 3000)) * np.sin(np.pi * tt / dur) ** 0.6, t, db)
    def trickle(t, dur, db=-30):                                        # pee / water running: soft bubbling
        n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
        for k in range(int(dur * 26)):
            i = int(g_.random() * (n - 2000)); f = 500 + 1400 * g_.random(); m = 1500; ee = np.exp(-np.arange(m) / (0.008 * SR)); x[i:i + m] += np.sin(2 * np.pi * f * (1 + 0.4 * np.arange(m) / m) * np.arange(m) / SR) * ee
        M.fx_(S.norm(S.lp(x, 2600)) * M.env(n, 0.08, 0.12), t, db)
    def swell(t, dur, db=-22, base=38):                                 # a wave of pain: a low swell with a tight held tone on top
        n = int(dur * SR); tt = np.arange(n) / SR; f = 440 * 2 ** ((base - 69) / 12)
        x = np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.5 * tt) + 0.12 * np.sin(2 * np.pi * f * 6 * tt)
        M.fx_(S.norm(S.lp(x, 900)) * np.sin(np.pi * tt / dur) ** 2, t, db)
    def pour(t, dur, db=-26):                                           # tap water filling a glass: the pitch of the glass rises as it fills
        n = int(dur * SR); tt = np.arange(n) / SR; x = S.bp(g_.standard_normal(n), 700, 3200) * 0.6; f = 300 + 500 * (tt / dur)
        x = x + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * g_.random(n))
        M.fx_(S.norm(S.lp(x, 3500)) * M.env(n, 0.06, 0.15), t, db)
    M.music_drop = 14.0
    M.lufs = -16.0; M.fx_under = 11.0; M.air = 0.0                    # the calmer house mix (owner, Nov 9)
    jam = B[7] + 0.64 * DUR[7]
    M.hype_score(bpm=104, key=50, db=-18, anchor=B[8], plan=[
        (0.0, B[1], 'light'), (B[1], B[3], 'light'), (B[3], B[6], 'build'), (B[6], jam, 'full'), (jam, B[8], 'stop'), (B[8], B[10], 'full'), (B[10], END, 'light')])
    # 0 the pain hits: sharp breath, he goes down (cloth, two knees on the floor), a groan-breath, the counter creaks under his hand
    breath(0.02, 0.45, -24); M.fx_(S.whoosh(0.5, 300, 1500), 0.25, -27)
    kn = 0.4 * DUR[0]; M.fx_(fol('thud'), kn, -19, -0.15); M.fx_(fol('thud'), kn + 0.05, -21, 0.15); M.fx_(M.rumble(0.4), kn, -27)
    breath(kn + 0.25, 0.7, -27, sharp=False); M.fx_(fol('creak'), kn + 0.1, -31, 0.4); breath(B[0] + 0.8 * DUR[0], 0.4, -28)
    M.heartbeat(0.1, B[3] - 0.1, 96, 84, -26)
    # 1 into him: the x-ray comes on (airy sweep), the kidney is found (soft low ping)
    M.fx_(S.whoosh(0.9, 400, 3000), B[1], -27); M.fx_(S.bell(62, 1.6, dec=0.7), B[1] + 0.55 * DUR[1], -30)
    # 2 blood rushes in (pulsing whoosh with each beat), then the pee trickles down to the bladder, small drips landing
    for k in range(4): M.fx_(S.whoosh(0.3, 200, 900), B[2] + 0.05 + k * 0.3, -28, -0.2)
    trickle(B[2] + 0.3 * DUR[2], 0.7 * DUR[2], -28)
    for k in range(5): M.fx_(S.pop_note(74 + 3 * (k % 3), 0.05), B[2] + 0.45 * DUR[2] + k * 0.24, -32, 0.2)
    # 3 not enough water: the fizz of waste gets thicker and lower as it packs in; specks start bumping (ticks, faster)
    fizz(B[3], DUR[3], -29, 2200, 6000); M.fx_(M.rumble(0.7 * DUR[3]), B[3] + 0.3 * DUR[3], -30)
    tt_ = B[3] + 0.15
    k = 0
    while tt_ < B[4]: tink(tt_, 96 + (k * 5) % 12, -31 + min(k, 5), 0.5 * ((k % 3) - 1)); tt_ += max(0.09, 0.34 - 0.03 * k); k += 1
    # 4 calcium and oxalate lock together: quick glassy ticks in bursts as each crystal forms (16 crystals), a bright ring as they finish
    for i in range(16):
        tc = B[4] + DUR[4] * (0.12 + 0.72 * i / 15)
        for j in range(3): tink(tc + 0.035 * j, 98 + (i * 3 + j * 4) % 14, -27 - j, 0.6 * ((i % 3) - 1))
    M.fx_(S.bell(98, 0.9, dec=0.35), B[4] + 0.88 * DUR[4], -30)
    # 5 the stone stacks up: a crystal lands every tenth of a second, the sound getting lower and stonier as it grows; a last heavy clack
    n5 = int(DUR[5] * 0.9 / 0.105)
    for i in range(n5): clack(B[5] + 0.05 + i * 0.105, -26 + 3 * i / n5, 0.4 * ((i % 3) - 1), 1400 - 800 * i / n5)
    M.fx_(fol('thud'), B[5] + 0.93 * DUR[5], -23); M.fx_(M.rumble(0.5 * DUR[5]), B[5] + 0.5 * DUR[5], -29)
    # 6 it breaks loose (a crack), rolls out of the funnel (rattle) and drops into the ureter (clunk)
    clack(B[6] + 0.15 * DUR[6], -20, 0, 700); M.fx_(S.impact(), B[6] + 0.15 * DUR[6], -27)
    for k in range(7): clack(B[6] + DUR[6] * (0.24 + 0.07 * k), -27, 0.3 * ((k % 3) - 1), 1000)
    M.fx_(fol('thud'), B[6] + 0.78 * DUR[6], -21); M.fx_(S.whoosh(0.5, 200, 1200), B[6] + 0.55 * DUR[6], -28); breath(B[6] + 0.85 * DUR[6], 0.35, -27)
    # 7 scraping down the lining (rasp, in jerks), then jammed: a hard thud, the score cuts out, pee starts to fill behind it
    for k in range(4): rasp(B[7] + DUR[7] * (0.02 + 0.15 * k), 0.14 * DUR[7] + 0.1, -23 - k * 0.5)
    M.fx_(fol('thud'), jam, -17); M.fx_(S.impact(), jam, -22); M.fx_(M.rumble(0.6), jam, -24); trickle(jam + 0.15, B[8] - jam - 0.15, -29)
    # 8 backed up: pressure building (rising low hum, bubbling), the pain in waves: three swells with a strained breath on each
    trickle(B[8], DUR[8], -30)
    for k in range(3):
        tw = B[8] + 0.05 + k * 0.8; swell(tw, 0.75, -21 + k); breath(tw + 0.3, 0.35, -28); M.fx_(S.pop_note(40, 0.12), tw + 0.36, -24)
    # 9 a small stone: carried down by the squeeze waves (soft gulps, a light rattle, a plink as it drops out); a big one: thuds, no go
    for k in range(4): M.fx_(S.whoosh(0.28, 150, 700), B[9] + 0.04 + k * 0.3, -28); tink(B[9] + 0.12 + k * 0.3, 92 + 2 * k, -29)
    M.fx_(S.pop_note(86, 0.08), B[9] + 0.46 * DUR[9], -25); M.fx_(S.bell(86, 0.6, dec=0.2), B[9] + 0.47 * DUR[9], -31)
    for k in range(3): M.fx_(fol('thud'), B[9] + DUR[9] * (0.56 + 0.15 * k), -21 + k); rasp(B[9] + DUR[9] * (0.6 + 0.15 * k), 0.2, -27)
    # 10 water: the tap runs into the glass (the note of the glass rising as it fills), a bright ping for one in ten
    M.fx_(fol('tick', hi=False), B[10] + 0.02, -27); pour(B[10] + 0.05, DUR[10] - 0.1, -24); M.fx_(S.bell(86, 1.0, dec=0.4), B[10] + 0.1, -30)
    # 11 back at the counter: fridge-quiet room, his breath catches, the heartbeat picks up into the loop
    M.heartbeat(B[11] + 0.2, END, 70, 96, -27); breath(B[11] + 0.62 * DUR[11], 0.4, -26); M.fx_(fol('creak'), B[11] + 0.75 * DUR[11], -31, 0.4)
    M.fx_(S.whoosh(0.6, 300, 1600), END - 0.6, -29)

elif name == 'torn':
    # Sucked into a tornado. The roar (a deep rumbling wind that swells with how close the funnel is, low-passed so it never hisses),
    # gusts whooshing past, debris (wood knocks, glass tinkles, rocks clacking) all around him; slow motion = the roar drops in pitch and
    # the hits stretch; a board zips past the camera; the trailer door rips, thunder; the map dings as the path draws; a soft landing in
    # grass; the closet: the house groaning, the bulb rattling, his breathing; then the wind builds back up into the loop.
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(45)
    END = B[-1] + DUR[-1]
    def roar(t0, t1, db=-24, lo=60, hi=900, swell=None, pitch=1.0):  # the tornado's roar: rumbling, gusting wind (no hiss)
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR
        x = S.lp(g_.standard_normal(n), hi * pitch) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 0.7 * tt + 2 * np.sin(2 * np.pi * 0.23 * tt))))
        x = x + 0.6 * S.lp(g_.standard_normal(n), lo * 2 * pitch)
        env = np.ones(n) if swell is None else np.interp(tt, np.linspace(0, tt[-1] if n else 1, len(swell)), swell)
        M.fx_(S.norm(S.bp(x, lo * pitch, hi * pitch)) * env * M.env(n, 0.15, 0.2), t0, db)
    def gust(t, dur=0.6, db=-26, pan=0.0): M.fx_(S.whoosh(dur, 200, 1600), t, db, pan)
    def wood(t, db=-25, pan=0.0):                                    # a board knocking / tumbling
        n = int(0.09 * SR); x = S.bp(g_.standard_normal(n), 250, 1400) * np.exp(-np.arange(n) / (0.015 * SR)); M.fx_(S.norm(x), t, db, pan); M.fx_(S.pop_note(48 + int(g_.integers(0, 6)), 0.06), t, db - 5, pan)
    def glass(t, db=-29, pan=0.0):
        for j in range(3): M.fx_(fol('clink', m=100 + int(g_.integers(0, 12))), t + 0.025 * j, db - 2 * j, pan)
    def rock(t, db=-27, pan=0.0):
        n = int(0.05 * SR); x = S.bp(g_.standard_normal(n), 800, 3200) * np.exp(-np.arange(n) / (0.008 * SR)); M.fx_(S.norm(x), t, db, pan)
    def debris(t0, t1, rate, db=-26, slow=1.0):                     # a mix of hits scattered left and right
        tt_ = t0
        while tt_ < t1:
            r = g_.random(); pn = float(g_.uniform(-0.8, 0.8))
            if r < 0.45: wood(tt_, db, pn)
            elif r < 0.75: rock(tt_, db - 1, pn)
            else: glass(tt_, db - 3, pn)
            tt_ += float(g_.exponential(1.0 / rate)) * slow + 0.04
    def thunder(t, db=-20):
        n = int(2.2 * SR); tt = np.arange(n) / SR; x = S.lp(g_.standard_normal(n), 300) * (np.exp(-tt / 0.9) + 0.6 * np.exp(-((tt - 0.25) / 0.1) ** 2))
        M.fx_(S.norm(x), t, db); M.fx_(S.impact(), t, db - 4)
    M.music_drop = 14.0
    M.lufs = -16.0; M.fx_under = 11.0; M.air = 0.0                    # the calmer house mix (owner, Nov 9)
    M.hype_score(bpm=96, key=45, db=-18, anchor=B[1], plan=[
        (0.0, B[1], 'build'), (B[1], B[4], 'full'), (B[4], B[7], 'light'), (B[7], B[8], 'full'), (B[8], B[10], 'light'), (B[10], B[11], 'stop'), (B[11], END, 'build')])
    # 0 ripped up: the roar right on top of him, gusts, junk hitting all around, his shout-breath
    roar(0.0, B[1], -21, swell=[0.8, 1.0, 1.0]); gust(0.05, 0.7, -24); gust(1.2, 0.8, -25, 0.4); debris(0.1, B[1], 7, -26)
    n = int(0.5 * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 600, 2500)) * np.exp(-np.arange(n) / (0.15 * SR)), 0.3, -28)
    # 1 the inflow: wide, the roar further off; the streams whoosh in, faster (rising whooshes)
    roar(B[1], B[2], -25, 50, 700)
    for k in range(5): M.fx_(S.whoosh(0.6 - 0.07 * k, 200 + 80 * k, 1200 + 300 * k), B[1] + 0.3 + k * 0.6, -27, 0.6 * ((k % 3) - 1))
    # 2 straight up the middle: a rising roar, a big upward whoosh
    roar(B[2], B[3], -22, 70, 1000, swell=[0.6, 1.0]); M.fx_(S.whoosh(1.4, 150, 2800), B[2], -23); debris(B[2], B[3], 6, -27)
    # 3 200+ mph: the full roar, a lightning crack
    roar(B[3], B[4], -21, 50, 900); thunder(B[3] + 0.35 * DUR[3], -22); debris(B[3], B[4], 4, -29)
    # 4-6 slow motion: everything drops in pitch and stretches; hits are slow and heavy; a board zips past the camera (B6)
    roar(B[4], B[7], -24, 40, 500, pitch=0.6); M.fx_(S.whoosh(1.0, 600, 120), B[4] - 0.05, -24)
    debris(B[4], B[6], 2.6, -24, slow=1.0)
    for k in range(4): M.fx_(S.pop_note(40 + 2 * k, 0.4), B[5] + 0.4 + k * 1.0, -30)
    zip_t = B[6] + 0.55 * DUR[6]; M.fx_(S.whoosh(0.45, 300, 3200), zip_t - 0.2, -21, 0.7); wood(zip_t + 0.1, -24, 0.8); debris(B[6], B[7], 2.5, -27)
    # 7 the trailer: lightning and thunder, the door ripped off its hinges, glass breaking, the roar back up full speed
    roar(B[7], B[8], -21, 60, 900, swell=[0.7, 1.0]); thunder(B[7] + 0.3 * DUR[7], -19); M.fx_(fol('creak'), B[7] + 0.15 * DUR[7], -25)
    wood(B[7] + 0.27 * DUR[7], -21); glass(B[7] + 0.3 * DUR[7], -25); debris(B[7] + 0.3 * DUR[7], B[8], 6, -26)
    # 8 the map: the roar far off, a ticking as the path draws, a ding when it lands
    roar(B[8], B[9], -30, 40, 500)
    for k in range(10): M.fx_(fol('tick', hi=k % 2 == 0), B[8] + 0.1 + k * 0.22, -30)
    M.fx_(S.bell(84, 1.0, dec=0.4), B[8] + 0.9 * DUR[8], -26)
    # 9 he lands in a field: a thump in the grass, quiet wind, a groan-breath, crickets far off
    M.fx_(fol('thud'), B[9] + 0.03, -21); n = int(DUR[9] * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 300, 1500)) * 0.5 * M.env(n, 0.3, 0.3), B[9], -31)
    for k in range(6): M.fx_(S.pop_note(96 + (k % 2), 0.03), B[9] + 0.5 + k * 0.25, -34, 0.6)
    n = int(0.6 * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 300, 1400)) * np.sin(np.pi * np.arange(n) / n) ** 1.5, B[9] + 0.6 * DUR[9], -28)
    # 10 the closet: the house groaning and shaking, the bulb chain rattling, muffled roar through the walls, his fast breathing
    roar(B[10], B[11], -25, 40, 300); M.fx_(fol('creak'), B[10] + 0.2, -24, -0.3); M.fx_(fol('creak'), B[10] + 1.6, -25, 0.3)
    for k in range(int(DUR[10] / 0.18)): M.fx_(fol('clink', m=104 + (k % 3)), B[10] + 0.1 + k * 0.18, -33, 0.2)
    for k in range(4):
        n = int(0.3 * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 700, 2400)) * np.sin(np.pi * np.arange(n) / n), B[10] + 0.3 + k * 0.7, -30)
    M.rumble and M.fx_(M.rumble(DUR[10]), B[10], -27)
    # 11 back outside: the roar builds from far to right on top of him (into frame one), grass and junk start moving
    roar(B[11], END, -23, 50, 900, swell=[0.2, 0.5, 1.0]); gust(B[11] + 0.6, 0.8, -27, -0.4); gust(B[11] + 1.9, 0.8, -25, 0.4)
    debris(B[11] + 0.55 * DUR[11], END, 5, -27); M.fx_(S.whoosh(0.7, 200, 1800), END - 0.7, -25)

elif name == 'cabin':
    # A plane loses cabin pressure. A window bangs out (a sharp pop + glass), the air roars out of the hole (a big low-passed rush that
    # fades over a few seconds), paper flutter; his ears: a muffled ring; the x-ray: a slowing heartbeat, everything woozy and pitched
    # down; the masks clatter down with a ding; the dive: engines and rushing air, altitude ticks; slow breathing in the mask; 2024: a
    # jet passing, the plug bangs out in slow motion, cabin wind, a shirt flapping, phones whooshing out; the roadside: birds, a car;
    # then the calm cabin hum, a creak in the window, and the bang again (the loop).
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(51)
    END = B[-1] + DUR[-1]
    def rush(t0, t1, db=-22, lo=60, hi=1400, swell=None, pitch=1.0):     # air roaring out of a hole (no hiss)
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR
        x = S.lp(g_.standard_normal(n), hi * pitch) * (0.75 + 0.25 * np.abs(np.sin(2 * np.pi * 1.3 * tt + 2 * np.sin(2 * np.pi * 0.4 * tt))))
        x = x + 0.5 * S.lp(g_.standard_normal(n), lo * 2 * pitch)
        env = np.ones(n) if swell is None else np.interp(tt, np.linspace(0, tt[-1] if n else 1, len(swell)), swell)
        M.fx_(S.norm(S.bp(x, lo * pitch, hi * pitch)) * env * M.env(n, 0.03, 0.2), t0, db)
    def bang(t, db=-17):                                              # the window / plug going: a pop, a thump, glass
        M.fx_(S.impact(0.5), t, db); M.fx_(fol('thud'), t, db - 3)
        for j in range(4): M.fx_(fol('clink', m=100 + int(g_.integers(0, 12))), t + 0.02 + 0.03 * j, db - 9 - 2 * j, float(g_.uniform(-0.5, 0.5)))
    def flutter(t0, t1, db=-30):                                      # paper flapping
        tt_ = t0
        while tt_ < t1:
            n = int(0.03 * SR); x = S.bp(g_.standard_normal(n), 1200, 4500) * np.exp(-np.arange(n) / (0.006 * SR))
            M.fx_(S.norm(x), tt_, db, float(g_.uniform(-0.6, 0.6))); tt_ += float(g_.uniform(0.03, 0.09))
    def hum(t0, t1, db=-33, f=95):                                    # airliner cabin hum
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR
        x = 0.5 * np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt) + 0.4 * S.norm(S.lp(g_.standard_normal(n), 400))
        M.fx_(x * M.env(n, 0.2, 0.2), t0, db)
    def beat_(t, db=-27): M.fx_(S.impact(0.2), t, db); M.fx_(S.impact(0.14), t + 0.17, db - 4)
    def breath(t, dur=1.0, db=-30, out=False):                        # a breath through the mask (a soft, plasticky rush)
        n = int(dur * SR); x = S.bp(g_.standard_normal(n), 500 if out else 900, 2400 if out else 3600) * np.sin(np.pi * np.arange(n) / n) ** 1.5
        M.fx_(S.norm(x), t, db)
    def ding(t, db=-24): M.fx_(S.bell(81, 1.0, dec=0.5), t, db); M.fx_(S.bell(76, 1.0, dec=0.6), t + 0.35, db - 1)
    M.music_drop = 14.0
    M.lufs = -16.0; M.fx_under = 11.0; M.air = 0.0
    M.hype_score(bpm=100, key=50, db=-18, anchor=B[1], plan=[
        (0.0, B[1], 'build'), (B[1], B[3], 'full'), (B[3], B[4], 'light'), (B[4], B[7], 'full'), (B[7], B[8], 'light'), (B[8], B[11], 'full'), (B[11], B[13], 'light'), (B[13], END, 'build')])
    # 0-1 the window goes: bang, the roar out of the hole, paper flutter, a big whoosh past the camera
    bang(0.0); rush(0.0, B[2] + 1.0, -20, swell=[1.0, 1.0, 0.75, 0.5]); flutter(0.05, B[2], -30); M.fx_(S.whoosh(0.6, 2600, 300), 0.08, -23, 0.5)
    for k in range(4): M.fx_(S.whoosh(0.5, 300 + 120 * k, 2200), B[1] + 0.25 + 0.55 * k, -27, 0.5 * ((k % 3) - 1))
    # 2 fifteen seconds: the roar fades, his ears ring, a clock-like tick
    M.fx_(np.sin(2 * np.pi * 3100 * np.arange(int(DUR[2] * SR)) / SR) * M.env(int(DUR[2] * SR), 0.3, 0.6) * 0.3, B[2], -38)
    for k in range(int(DUR[2] / 0.5)): M.fx_(fol('tick', hi=k % 2 == 0), B[2] + 0.1 + k * 0.5, -28)
    # 3 the x-ray: a slow heartbeat, the wind far off and pitched down, a woozy whoosh
    for k in range(int(DUR[3] / 0.85)): beat_(B[3] + 0.15 + k * (0.75 + 0.06 * k), -26)
    rush(B[3], B[4], -32, 40, 400, pitch=0.6); M.fx_(S.whoosh(1.4, 900, 150), B[3], -28)
    # 4 masks: the doors pop, masks clatter down, the chime, his grab
    t4 = B[4] + 0.15; M.fx_(fol('clack'), t4, -23); M.fx_(fol('clack'), t4 + 0.04, -26, -0.4); M.fx_(fol('clack'), t4 + 0.07, -27, 0.4)
    for k in range(10): M.fx_(fol('clink', m=88 + (k % 5)), t4 + 0.3 + 0.07 * k, -33, float(g_.uniform(-0.7, 0.7)))
    ding(t4 + 0.6); rush(B[4], B[5], -30, 60, 900); M.fx_(S.whoosh(0.35, 400, 1800), B[4] + DUR[4] * 0.55, -28)
    # 5 the dive: engines, rushing air rising, fast altitude ticks
    rush(B[5], B[6], -23, 50, 1600, swell=[0.5, 1.0]); hum(B[5], B[6], -30, 70)
    for k in range(int(DUR[5] / 0.12)): M.fx_(fol('tick', hi=True), B[5] + 0.1 + k * 0.12, -33)
    M.fx_(S.whoosh(1.2, 200, 2500), B[5], -25)
    # 6 the mask: slow breaths, the cabin hum back
    hum(B[6], B[7], -32)
    for k in range(int(DUR[6] / 1.3)): breath(B[6] + 0.1 + k * 1.3, 0.6, -29); breath(B[6] + 0.75 + k * 1.3, 0.55, -31, out=True)
    # 7 2024: a jet flying past (rising then falling roar)
    rush(B[7], B[8], -24, 70, 1800, swell=[0.3, 1.0, 0.6]); hum(B[7], B[8], -30, 60)
    # 8 the plug goes (slow motion): a deep slowed bang and a long low whoosh
    tb8 = B[8] + 0.12 / 0.35; M.fx_(S.impact(0.9), tb8, -18); M.fx_(fol('thud'), tb8, -21); M.fx_(S.whoosh(1.4, 800, 120), tb8, -23); rush(tb8, B[9], -26, 40, 500, pitch=0.6)
    # 9-10 cabin wind through the hole, papers, a shirt flapping, phones whooshing out
    rush(B[9], B[11], -21, 60, 1300); flutter(B[9], B[11], -29)
    for k in range(int(DUR[10] / 0.07)):
        n = int(0.05 * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 250, 1200)) * np.exp(-np.arange(n) / (0.015 * SR)), B[10] + k * 0.07, -29, -0.3)
    M.fx_(S.whoosh(0.4, 500, 2600), B[10] + 0.45 * DUR[10], -24, -0.5); M.fx_(S.whoosh(0.4, 600, 3000), B[10] + 0.75 * DUR[10], -25, -0.6)
    # 11-12 the roadside: birds, a car passing, a soft phone buzz; "no one died": a warm swell
    for k in range(7): M.fx_(S.pop_note(93 + (k % 3) * 2, 0.04), B[11] + 0.2 + k * 0.27, -31, 0.5)
    M.fx_(S.whoosh(1.6, 150, 900), B[11] + 0.3, -28, -0.6)
    for k in range(3):
        n = int(0.18 * SR); M.fx_(np.sin(2 * np.pi * 180 * np.arange(n) / SR) * (np.arange(n) % int(SR / 30) < SR / 60) * 0.5, B[11] + 0.9 + k * 0.32, -30)
    M.fx_(S.bell(76, 1.6, dec=0.8), B[12], -26)
    # 13 calm cabin: the hum, a seatbelt ding, the window creaks, the air starts to hiss, then (the loop) the bang at frame one
    hum(B[13], END, -30); M.fx_(S.bell(84, 0.8, dec=0.4), B[13] + 0.3, -29)
    M.fx_(fol('creak'), END - 1.3, -24); rush(END - 0.9, END, -27, 200, 1600, swell=[0.0, 1.0]); M.fx_(S.whoosh(0.6, 300, 2400), END - 0.6, -25)

elif name == 'crush':
    # Trapped under a building (Brooklyn, Nov 11 2026). The ceiling gives: a crack, a deep rumble, bricks and tiles crashing down, the
    # lights buzzing and failing; the pile settling and grit trickling, his strained breath; rescuers pulling bricks off (scrape, clack),
    # flashlights clicking on; outside at night: a drone's whine, a fire truck idling, a siren far off, radio beeps; the warning: a low
    # rising tone, a creak in the beam, a heartbeat; the x-ray: fizzing pops as the specks build up; the beam lifted (a big creak and
    # a rush up the veins); the heart stutters (monitor beeps out of step, then a held tone); the IV drips; the building falls into the
    # pit (rumble, cascading bricks, crashes, dust); the night dig (generators, a siren, shovels); the store hum, then the crack again.
    from studio.sfx import foley as F
    def fol(nm, **kw): return np.asarray(F.Track.make(nm, **kw), float)
    g_ = np.random.default_rng(61)
    END = B[-1] + DUR[-1]
    def rumbl(t0, t1, db=-22, hi=180, swell=None):                  # deep building rumble (no hiss)
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR
        x = S.lp(g_.standard_normal(n), hi) * (0.7 + 0.3 * np.abs(np.sin(2 * np.pi * 2.3 * tt + 3 * np.sin(2 * np.pi * 0.7 * tt))))
        env = np.ones(n) if swell is None else np.interp(tt, np.linspace(0, tt[-1] if n else 1, len(swell)), swell)
        M.fx_(S.norm(S.bp(x, 25, hi)) * env * M.env(n, 0.05, 0.25), t0, db)
    def crack(t, db=-19, pan=0.0):                                   # wood/plaster snapping
        n = int(0.25 * SR); x = S.lp(S.bp(g_.standard_normal(n), 400, 5000) * (g_.random(n) < 0.06), 5000)
        M.fx_(S.norm(np.convolve(x, np.exp(-np.arange(80) / 12.0))[:n]) * np.exp(-np.arange(n) / (0.06 * SR)), t, db, pan); M.fx_(fol('thud'), t, db - 2, pan)
    def brick(t, db=-25, pan=0.0):                                   # a brick landing: a dull knock and grit
        n = int(0.08 * SR); x = S.bp(g_.standard_normal(n), 300, 2200) * np.exp(-np.arange(n) / (0.012 * SR))
        M.fx_(S.norm(x), t, db, pan); M.fx_(S.pop_note(43 + int(g_.integers(0, 6)), 0.07), t, db - 4, pan)
    def bricks(t0, t1, rate, db=-25):
        tt_ = t0
        while tt_ < t1: brick(tt_, db + float(g_.uniform(-3, 2)), float(g_.uniform(-0.8, 0.8))); tt_ += float(g_.exponential(1.0 / rate)) + 0.03
    def grit_(t0, t1, db=-33):                                       # dust and grit trickling
        tt_ = t0
        while tt_ < t1:
            n = int(0.02 * SR); M.fx_(S.norm(S.lp(S.bp(g_.standard_normal(n), 1500, 5000), 5000)) * np.exp(-np.arange(n) / (0.004 * SR)), tt_, db + float(g_.uniform(-4, 2)), float(g_.uniform(-0.6, 0.6)))
            tt_ += float(g_.uniform(0.015, 0.06))
    def buzz(t0, t1, db=-31):                                        # the failing lights (low-passed hum, not a 9 kHz zap)
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR; x = np.sign(np.sin(2 * np.pi * 120 * tt)) * (np.sin(2 * np.pi * 7 * tt) > -0.2)
        M.fx_(S.lp(x, 2500) * M.env(n, 0.02, 0.1), t0, db)
    def breath(t, dur=0.7, db=-30):
        n = int(dur * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 400, 1800)) * np.sin(np.pi * np.arange(n) / n) ** 1.6, t, db)
    def beat_(t, db=-25): M.fx_(S.impact(0.2), t, db); M.fx_(S.impact(0.14), t + 0.16, db - 4)
    def siren(t0, t1, db=-34, pan=-0.5):                             # a far NYC siren (wail)
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR; f = 900 + 350 * np.sin(2 * np.pi * 0.35 * tt)
        M.fx_(S.lp(np.sin(2 * np.pi * np.cumsum(f) / SR), 3000) * M.env(n, 0.4, 0.5), t0, db, pan)
    def whine(t0, t1, db=-33):                                       # drone rotors
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR; f = 210 + 8 * np.sin(2 * np.pi * 0.5 * tt)
        x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 5)) + 0.4 * S.norm(S.bp(g_.standard_normal(n), 600, 3000))
        M.fx_(S.lp(x, 4500) * M.env(n, 0.2, 0.3), t0, db, 0.2)
    def idle(t0, t1, db=-31):                                        # a fire truck's diesel idling
        n = int((t1 - t0) * SR); tt = np.arange(n) / SR
        x = S.lp(g_.standard_normal(n), 220) * (0.6 + 0.4 * (np.sin(2 * np.pi * 11 * tt) > 0)) + 0.3 * np.sin(2 * np.pi * 44 * tt)
        M.fx_(S.norm(x) * M.env(n, 0.2, 0.3), t0, db, -0.3)
    def radio(t, db=-30):
        M.fx_(fol('beep', f=1150, dur=0.08), t, db, 0.4); M.fx_(fol('beep', f=1150, dur=0.08), t + 0.13, db - 2, 0.4)
    def scrape(t, db=-26, pan=0.0):                                  # a brick dragged off the pile
        n = int(0.22 * SR); x = S.bp(g_.standard_normal(n), 500, 3500) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 37 * np.arange(n) / SR)))
        M.fx_(S.norm(S.lp(x, 4500)) * np.sin(np.pi * np.arange(n) / n), t, db, pan); brick(t + 0.2, db - 2, pan)
    def fizz(t, db=-31, pan=0.0): M.fx_(S.pop_note(86 + int(g_.integers(0, 8)), 0.05), t, db, pan)
    def mbeep(t, db=-26): M.fx_(fol('beep', f=980, dur=0.09), t, db)
    def drip(t, db=-26): M.fx_(S.pop_note(88, 0.06), t, db); M.fx_(S.pop_note(95, 0.04), t + 0.03, db - 6)
    M.music_drop = 14.0
    M.lufs = -16.0; M.fx_under = 11.0; M.air = 0.0                    # the calmer house mix (owner, Nov 9)
    M.hype_score(bpm=88, key=45, db=-18, anchor=B[1], plan=[
        (0.0, B[1], 'build'), (B[1], B[4], 'full'), (B[4], B[7], 'light'), (B[7], B[9], 'full'), (B[9], B[10], 'light'), (B[10], B[11], 'full'), (B[11], B[12], 'light'), (B[12], END, 'build')])
    # 0 the ceiling comes down: snaps, the rumble, tiles and bricks crashing round him, the lights buzzing out
    crack(0.0, -18); crack(0.55, -21, 0.4); crack(1.2, -20, -0.4); rumbl(0.0, B[1] + 0.6, -19, swell=[0.8, 1.0, 1.0, 0.6])
    bricks(0.15, B[1], 11, -24); buzz(0.0, 1.3, -31); M.fx_(fol('clack', f=300), 0.4, -24, 0.3)
    M.fx_(S.whoosh(0.5, 2400, 300), B[1] - 0.45, -22); M.fx_(S.impact(0.7), B[1] - 0.02, -19)
    # 1 pinned: the pile settles (knocks, grit), the floor above groans, his strained breath
    grit_(B[1], B[2], -32); bricks(B[1] + 0.1, B[1] + 1.2, 6, -27); M.fx_(fol('creak'), B[1] + 0.6, -25, -0.3); breath(B[1] + 1.1, 0.8, -28)
    rumbl(B[1], B[2], -30, 120)
    # 2 the rescuers dig: bricks scraped off and tossed, flashlight clicks, light pouring in (a soft rising air)
    for k in range(7): scrape(B[2] + 0.2 + k * 0.38, -26, float(g_.uniform(-0.6, 0.6)))
    for k in range(3): M.fx_(fol('tick', hi=True), B[2] + 0.5 + 0.45 * k, -27, 0.3)
    M.fx_(S.whoosh(1.6, 300, 2500), B[2] + 0.6, -29); grit_(B[2], B[3], -34)
    # 3 outside at night: the drone whining overhead, a fire truck idling, a siren far off, radio beeps, sniffing-dog pants
    whine(B[3], B[4], -30); idle(B[3], B[4], -31); siren(B[3], B[4] + 0.3, -35); radio(B[3] + 0.5); radio(B[3] + 1.5, -31)
    M.fx_(S.whoosh(0.7, 300, 1600), B[3] + 0.05, -26)
    for k in range(5): n = int(0.09 * SR); M.fx_(S.norm(S.bp(g_.standard_normal(n), 800, 3000)) * np.sin(np.pi * np.arange(n) / n), B[3] + 0.9 + 0.17 * k, -32, -0.4)
    # 4 the warning: a low rising tone, the beam creaks, his heartbeat
    n = int(DUR[4] * SR); tt = np.arange(n) / SR; M.fx_(np.sin(2 * np.pi * np.cumsum(55 + 25 * tt / DUR[4]) / SR) * M.env(n, 0.3, 0.2), B[4], -27)
    M.fx_(fol('creak'), B[4] + 0.3, -24, 0.3); M.fx_(fol('creak'), B[4] + 1.9, -26, -0.2)
    for k in range(int(DUR[4] / 0.75)): beat_(B[4] + 0.2 + k * 0.75, -26)
    grit_(B[4], B[5], -35)
    # 5-6 the x-ray: a slow heavy heartbeat; a fizzing pop for the specks as they build up (faster in 6); the legs throb
    M.fx_(S.whoosh(0.8, 1800, 200), B[5] - 0.1, -24)
    for k in range(int((B[7] - B[5]) / 0.8)): beat_(B[5] + 0.15 + k * 0.8, -27)
    tt_ = B[5] + 0.4
    while tt_ < B[7] - 0.1:
        fizz(tt_, -30, float(g_.uniform(-0.6, 0.6))); tt_ += 0.16 if tt_ < B[6] else 0.07
    rumbl(B[5], B[7], -32, 90)
    M.fx_(S.whoosh(0.7, 200, 1400), B[7] - 0.6, -17); M.fx_(fol('creak'), B[7] - 0.55, -19); rumbl(B[7] - 0.7, B[7] + 0.2, -20, 160)          # no gap before the lift
    # 7 the weight comes off: a big wood creak and scrape, a rush up the veins (rising whoosh), the heartbeat jumps
    M.fx_(fol('creak'), B[7] + 0.02, -21); scrape(B[7] + 0.15, -22); M.fx_(S.impact(0.6), B[7] + 0.05, -22)
    M.fx_(S.whoosh(1.6, 150, 3200), B[7] + 0.35, -21)
    for k in range(6): beat_(B[7] + 0.4 + k * 0.32, -25)
    # 8 the heart stutters: monitor beeps out of step with it, then a held flat tone that fades
    for s_ in [0.0, 0.18, 0.31, 0.62, 0.7, 0.78, 1.05, 1.5, 1.58, 2.2, 2.32, 2.4]:
        beat_(B[8] + s_, -24); mbeep(B[8] + s_ + 0.02, -27)
    n = int(0.9 * SR); M.fx_(np.sin(2 * np.pi * 980 * np.arange(n) / SR) * M.env(n, 0.01, 0.4) * 0.5, B[8] + 2.65, -30)
    # 9 the IV: drips in the chamber, a soft hiss in the line, a calmer beat
    for k in range(int(DUR[9] * 2.2)): drip(B[9] + 0.1 + k / 2.2, -27)
    n = int(DUR[9] * SR); M.fx_(S.norm(S.lp(S.bp(g_.standard_normal(n), 900, 3000), 4000)) * M.env(n, 0.3, 0.3), B[9], -36)
    for k in range(3): beat_(B[9] + 0.3 + k * 0.85, -28)
    M.fx_(fol('creak'), B[9] + DUR[9] - 0.5, -26)
    # 10 the building falls into the pit: street sounds, the deep groan, then crumbling bricks, crashes, the dust rolling out
    n = int(DUR[10] * SR); M.fx_(S.norm(S.lp(g_.standard_normal(n), 900)) * 0.4 * M.env(n, 0.2, 0.2), B[10], -33)
    M.fx_(fol('creak'), B[10] + 0.2, -22); rumbl(B[10] + 0.4, B[11] + 0.4, -18, swell=[0.4, 1.0, 1.0, 0.7])
    crack(B[10] + 0.7, -19, 0.2); crack(B[10] + 1.1, -20, 0.5)
    for k in range(5): M.fx_(S.impact(0.8), B[10] + 1.3 + k * 0.42, -21, float(g_.uniform(-0.3, 0.6)))
    bricks(B[10] + 1.1, B[11], 16, -24); M.fx_(S.whoosh(1.8, 200, 1500), B[10] + 2.0, -24)
    # 11 the night dig: light-tower generators, a siren passing, radio, shovels and bricks being moved
    idle(B[11], B[12], -32); siren(B[11] + 0.2, B[12], -33, 0.5); radio(B[11] + 0.9, -31)
    for k in range(6): scrape(B[11] + 0.3 + k * 0.42, -29, float(g_.uniform(-0.7, 0.7)))
    whine(B[11], B[12], -34)
    # 12 back in the store before: the cooler hum, a door chime, then the ceiling creaks, grit falls, a rumble swells into frame one
    n = int(DUR[12] * SR); tt = np.arange(n) / SR; M.fx_((0.5 * np.sin(2 * np.pi * 60 * tt) + 0.3 * S.norm(S.lp(g_.standard_normal(n), 300))) * M.env(n, 0.2, 0.1), B[12], -32)
    M.fx_(S.bell(84, 0.6, dec=0.3), B[12] + 0.15, -30); M.fx_(S.bell(80, 0.6, dec=0.3), B[12] + 0.3, -31)
    M.fx_(fol('creak'), B[12] + 0.9, -24); crack(B[12] + 1.6, -24, 0.3); grit_(B[12] + 1.4, END, -32)
    rumbl(B[12] + 1.2, END, -22, swell=[0.0, 0.5, 1.0]); bricks(END - 0.8, END, 6, -27)

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
