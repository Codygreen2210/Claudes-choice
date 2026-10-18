"""Sound for the swimming Short.  STUDIO_ROOT=... python3 swim_sound.py times.json narration.wav out.wav

Music: underwater calm that turns wrong. Opening and loop: muffled drone + slow strings (calm on the
surface, wrong underneath). Breaths and jump: lighter. The trick and the alarm: ticking, a bell.
Air running out: strings rise, heartbeat. Blackout: everything drops to a low hum and slow heartbeat.
Brain: dissonant tone. Rules: warm lift. Loop: back to the opening bed.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Mix

M = Mix(sys.argv[1]); S = M.S; B, DUR, D = M.B, M.DUR, M.D; SR = M.SR
rng = np.random.default_rng(1)


def under(dur, seed):                 # muffled underwater room
    n = int(dur * SR)
    x = S.lp(np.random.default_rng(seed).standard_normal(n), 400)
    return S.norm(x) * M.env(n, 0.4, 0.4)


def bubbles_snd(t0, t1, rate, db):
    t = t0
    while t < t1:
        M.fx_(S.pop_note(int(rng.integers(76, 92)), 0.06), t, db, rng.uniform(-0.6, 0.6)); t += rng.exponential(1 / rate)


def breath(t, db, dur=0.45, seed=0):
    n = int(dur * SR)
    M.fx_(S.bp(np.random.default_rng(seed).standard_normal(n), 500, 3500) * M.env(n, 0.08, 0.25), t, db)


def bell(t, db):
    for j in range(4):
        M.fx_(S.bell(84, 0.5, dec=0.15), t + j * 0.12, db)


# underwater bed for every underwater beat (the loop beat too, so the seam is the same sound)
for i in (0, 2, 7, 8, 9, 10, 12, len(B) - 1):
    t1 = B[i] + DUR[i] + (0.05 if i == len(B) - 1 else 0)
    M.fx_(under(t1 - B[i] + 0.3, 10 + i), B[i], -16)
bubbles_snd(B[-1], D, 6, -24); bubbles_snd(0, 0.6, 6, -24)                  # bubbles stop as he goes limp
M.fx_(S.pop_note(84, 0.2), 0.02, -12)                                        # hook text
M.heartbeat(B[-1], D, 90, 90, -14); M.heartbeat(0, B[1], 90, 60, -14)
M.swishes()
# 1 fast breaths at the edge (rewind first)
M.fx_(S.whoosh(0.5, 5000, 300), B[1] - 0.05, -7)
for j in range(int(DUR[1] / 0.36)):
    breath(B[1] + 0.3 + j * 0.36, -12, 0.3, j)
# 2 the jump and splash
M.fx_(M.k('water/splash', 4), B[2] + 0.75, -4)
M.fx_(M.k('water/splash', 9), B[2] + 0.8, -8)
bubbles_snd(B[2] + 0.8, B[2] + DUR[2], 14, -18)
# 3-6 the trick: ticks, the alarm bell, CO2 fizz, breaths dumping the gas
M.mu(S.bell(64, 3.0, dec=1.5), B[3] + 0.4, -16)
for j in range(3):
    bell(B[4] + j * 1.0, -15)
for j in range(int(DUR[5] / 0.18)):
    M.fx_(S.pop_note(int(rng.integers(60, 72)), 0.05), B[5] + j * 0.18, -20, rng.uniform(-0.5, 0.5))
bell(B[5] + DUR[5] * 0.88, -13)
for j in range(int(DUR[6] / 0.5)):
    breath(B[6] + 0.2 + j * 0.5, -11, 0.4, 40 + j)
    M.fx_(S.whoosh(0.35, 2000, 300), B[6] + 0.3 + j * 0.5, -18)
M.fx_(M.k('rooms/slam', 3), B[6] + DUR[6] * 0.45, -9)                       # ALARM OFF stamp
# 7-8 air running out: meter beeps falling in pitch, then a flat tone on EMPTY
for j in range(8):
    M.fx_(S.pop_note(84 - j, 0.08), B[7] + 0.3 + j * DUR[7] / 8, -16)
M.heartbeat(B[7], B[9], 90, 120, -12)
flat_n = int(1.6 * SR)
M.fx_(np.sin(2 * np.pi * 988 * np.arange(flat_n) / SR) * 0.3 * M.env(flat_n, 0.01, 0.5), B[8] + DUR[8] * 0.6, -16)
M.fx_(M.k('rooms/slam', 5), B[8] + DUR[8] * 0.6, -10)
# 9 blackout: slow heartbeat fading, deep muffled thump
M.heartbeat(B[9] + 0.2, B[10], 60, 40, -12)
M.fx_(S.impact(1.6), B[9] + 0.4, -10)
# 10 water rushing in
M.fx_(M.noise(DUR[10], 200, 1500, 50, 0.3, 0.4), B[10], -10)
bubbles_snd(B[10] + 0.2, B[10] + DUR[10] - 0.3, 18, -16)
# 11 brain: ticking clock, rising whine
for j in range(int(DUR[11] / 0.5)):
    M.fx_(M.tick(), B[11] + j * 0.5, -14)
n11 = int(DUR[11] * SR); t11 = np.arange(n11) / SR
M.fx_(np.sin(2 * np.pi * np.cumsum(np.linspace(400, 900, n11)) / SR) * 0.2 * M.env(n11, 0.5, 0.3), B[11], -20)
# 12 strong swimmer: power kicks
for j in range(int(DUR[12] / 0.4)):
    M.fx_(M.k('water/splash', j), B[12] + j * 0.4, -22, (j % 2 - 0.5) * 0.6)
# 13 rules: three pops
for j in range(3):
    M.fx_(S.pop_note(76 + 4 * j, 0.25), B[13] + j * DUR[13] * 0.28, -10)
    M.fx_(M.k('rooms/slam', j), B[13] + j * DUR[13] * 0.28, -14)

# music
M.drone(0, B[1], 38, -19); M.strings([50, 57, 62], 0, B[1], -23, 600, 900)
M.drone(B[-1], D + 0.6, 38, -19); M.strings([50, 57, 62], B[-1], D + 0.05, -23, 600, 900)
M.pad([50, 57, 62, 66], B[1], B[3], -22, 2000)                               # surface: lighter
M.drone(B[3], B[7], 36, -19); M.clock(B[3], B[7])                            # the trick
M.drone(B[7], B[9], 34, -18); M.strings([46, 49, 53, 58], B[7], B[9], -21)   # running out
M.drone(B[9], B[12], 29, -20)                                                # blackout: just a low hum
M.pad([50, 57, 62, 66, 69], B[12], B[-1], -20, 2400, a=1.2)                  # rules: warm
M.shape(B[1], B[3], -3); M.shape(B[7], B[9], 1.5); M.shape(B[9], B[11], -3); M.shape(B[13], B[-1], -2)
M.finish(sys.argv[2], sys.argv[3])
print('ok')
