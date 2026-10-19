"""Sound for the 'going viral' Short.

    STUDIO_ROOT=... python3 viral_sound.py times.json narration.wav out.wav

House sounds (light bed seamless around the loop, paper fold on each scene change, a soft whoosh on each
camera punch-in, the C-G chime sound logo on the reveal) plus effects on the on-screen action.
Times match viral.py.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Mix

M = Mix(sys.argv[1]); S = M.S; B, DUR, D = M.B, M.DUR, M.D; SR = M.SR


def env(n, a, r):
    return M.env(n, a, r)


def pinpop(t, i, db=-17):
    M.fx_(S.pop_note(84 + (i * 5) % 12, 0.06), t, db, ((i * 37) % 11) / 11 - 0.5)


def sparkle(t, db=-16):
    for j in range(5):
        M.fx_(S.bell(96 + (j * 3) % 7, 0.4, dec=0.12), t + j * 0.04, db - j, (j - 2) * 0.25)


def boing(t, db=-14):
    n = int(0.4 * SR); tt = np.arange(n) / SR
    f = 220 + 260 * tt / 0.4
    M.fx_(np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.5 * np.sin(2 * np.pi * 18 * tt)) * env(n, 0.005, 0.25), t, db)


M.swishes(-19)
M.light_score(key=62, db=-21)

# 0 - the hook: pins popping onto the globe (also runs in the loop beat, folding round the seam), TV hum
for i in range(48):
    t = i / 9.0 - 3.2                         # same clock as viral.py: pin i appears at lt = i/9 - 3.2
    if t > DUR[0]:
        break
    pinpop(t, i, -17 if t >= 0 else -19)
M.fx_(S.whoosh(0.6, 200, 2400), -0.15, -16)   # energy coming into frame one
M.fx_(M.noise(DUR[0] + 2.9, 90, 300, 3, 0.4, 0.4), -2.9, -27)

# 1 - the trailer: car passes (every ~2.9 s), calendar pops with page flips on "November 19th"
t = B[1]
while t < B[1] + DUR[1]:
    M.fx_(S.whoosh(0.7, 300, 1800), t + 0.4, -18, -0.4); t += 1.6 / 0.55
cal = B[1] + DUR[1] * 0.42
M.fx_(S.pop_note(76, 0.08), cal, -13)
for q in range(3):
    M.fx_(M.k('rooms/page', q), cal + 0.05 + q * 0.12, -16, 0.4)

# 2 - the song climbs the list: ticks as it passes rows, a bright pluck run on arrival
c0 = B[2] + DUR[2] * 0.45; c1 = c0 + DUR[2] * 0.35
for j in range(3):
    M.fx_(M.tick(), c0 + (j + 0.5) * (c1 - c0) / 3, -15)
for j, m in enumerate((72, 76, 79, 84)):
    M.fx_(S.pluck(m, 0.25), c1 + j * 0.06, -16, 0.2)

# 3 - survive: running steps on grass, a cash drop + coins each new day
for j in range(int(DUR[3] * 4.3)):
    M.fx_(M.k('people/step_grass', j), B[3] + j / 4.3, -21, -0.2)
for d in range(1, 5):
    t = B[3] + d * DUR[3] / 5
    M.fx_(S.impact(0.3), t + 0.25, -17)
    M.fx_(M.k('rooms/coins', d), t + 0.27, -15, 0.35)

# 4 - challenges: bars rising, the jump, landing, cheer (the sound logo), confetti
M.fx_(S.riser(DUR[4] * 0.45, 300, 2500), B[4], -22)
jt = B[4] + DUR[4] * 0.5
boing(jt, -15)
M.fx_(S.impact(0.4), jt + 0.5, -19)
reveal = jt + 0.5
sparkle(reveal + 0.15, -17)

# 5 - shorts: swipe flicks, a pop for each person that lights up
t = B[5]
while t < B[5] + DUR[5]:
    M.fx_(S.whoosh(0.22, 1500, 4000), t + 0.3, -22, -0.3); t += 1 / 1.6
for i in range(6):
    M.fx_(S.pop_note(79 + i, 0.07), B[5] + 0.8 + i * 0.35, -14, 0.3)

# 6 - channels: a fast run of clicks as 39 tiles light, then a stamp on the badge
for i in range(39):
    M.fx_(S.pop_note(91 + (i % 4), 0.03), B[6] + 0.4 + i * 2.6 / 39, -21, (i % 5 - 2) * 0.2)
M.fx_(M.k('rooms/soft_hit', 0), B[6] + 3.1, -12)

# 7 - the recipe: lid pop + shimmer, dart thunk, play click and a rising fill
t1, t2, t3 = B[7] + DUR[7] * 0.30, B[7] + DUR[7] * 0.48, B[7] + DUR[7] * 0.62
M.fx_(S.pop_note(70, 0.1), t1 + 0.25, -12); sparkle(t1 + 0.3, -19)
M.fx_(S.whoosh(0.25, 2500, 700), t2, -18); M.fx_(M.k('rooms/wood_crack', 0), t2 + 0.45, -13)
M.fx_(M.k('rooms/keyclick', 0), t3 + 0.05, -14)
M.fx_(S.riser(1.2, 600, 3000), t3 + 0.2, -24)


# ---- house sounds, same in every Short ----
def chime(t, db=-10):                         # the sound logo: two bright notes, C then G, on the reveal
    M.fx_(S.bell(84, 1.4, dec=0.6), t, db, -0.15)
    M.fx_(S.bell(91, 1.8, dec=0.8), t + 0.13, db + 1, 0.15)


def fold(t):                                  # the paper fold on every scene change
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

chime(reveal, -13)
M.shape(reveal - 0.4, reveal + 0.1, -5, 0.2)
M.shape(B[-3], B[-2] + DUR[-2], 1.5)
M.finish(sys.argv[2], sys.argv[3])
print('ok viral')
