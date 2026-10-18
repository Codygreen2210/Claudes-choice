"""Sound for the hot car Short.  STUDIO_ROOT=... python3 hotcar_sound.py times.json narration.wav out.wav

Music: summer heat that turns into a pressure cooker. Opening/loop: door slam + lock + a hot,
droning low string with a fast clock. Outside: lazy warm pad, cicadas. Trapped / 10 minutes: rising
drone, ticking. Body: heartbeat climbing 80 -> 150. Heatstroke: a high whine, then everything smears and
drops at "pass out". Kids / windows: low, serious. Escape: horn honks and glass, then a hard stop into the loop.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Mix

M = Mix(sys.argv[1]); S = M.S; B, DUR, D = M.B, M.DUR, M.D; SR = M.SR
rng = np.random.default_rng(2)


def cicadas(dur, seed):
    n = int(dur * SR); t = np.arange(n) / SR
    x = S.bp(np.random.default_rng(seed).standard_normal(n), 4000, 7000) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 38 * t)))
    return S.norm(x) * M.env(n, 0.5, 0.5) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t))


def horn(dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    return S.norm(S.lp(S.saw(420, n) + S.saw(522, n), 2500)) * M.env(n, 0.01, 0.05)


def sizzle(dur, seed):
    n = int(dur * SR)
    return S.norm(S.hp(np.random.default_rng(seed).standard_normal(n) * (np.random.default_rng(seed + 1).random(n) < 0.05), 3000)) * M.env(n, 0.3, 0.3)


# opening and loop: the door slam happens exactly at frame one
M.fx_(M.k('rooms/door_close', 1), -0.02, -2)
M.fx_(M.k('rooms/lock', 0), 0.18, -6)
M.fx_(S.impact(0.8), 0.0, -9)
M.fx_(S.pop_note(80, 0.2), 0.27, -11)                          # OVEN text
for t0, t1 in ((B[-1], D + 0.05), (0.0, B[1] + 0.2)):
    M.fx_(cicadas(t1 - t0 + 0.4, 3), t0, -22)
    M.fx_(sizzle(t1 - t0 + 0.4, 4), t0, -24)
M.fx_(M.k('people/step_stone', 0), B[-1] + 0.2, -14)            # someone climbs in before the door shuts
for j in range(int(DUR[0] / 0.25)):
    M.fx_(M.tick(), 0.4 + j * 0.25, -20)                       # temperature ticking up
M.swishes()
# 1 outside (rewind)
M.fx_(S.whoosh(0.5, 5000, 300), B[1] - 0.05, -7)
M.fx_(cicadas(DUR[1] + DUR[2], 5), B[1], -18)
# 2 trapped: light beams 'pew' in, heat bouncing
for j in range(3):
    M.fx_(S.whoosh(0.3, 4000, 1200), B[2] + 0.3 + j * 0.6, -16, 0.4)
M.fx_(sizzle(DUR[2] + DUR[3], 6), B[2], -18)
M.fx_(M.k('rooms/slam', 2), B[2] + DUR[2] * 0.5, -10)
# 3 ten minutes: fast clock + rising tone, ding at +20
for j in range(int(DUR[3] * 0.85 / 0.12)):
    M.fx_(M.tick(), B[3] + j * 0.12, -17)
n3 = int(DUR[3] * SR)
M.fx_(np.sin(2 * np.pi * np.cumsum(np.linspace(200, 600, n3)) / SR) * 0.25 * M.env(n3, 0.3, 0.2), B[3], -20)
M.fx_(S.bell(84, 1.5), B[3] + DUR[3] * 0.86, -12)
# 4-5 sweat drips, steamy fog hiss
for j in range(8):
    M.fx_(S.pop_note(int(rng.integers(86, 96)), 0.06), B[4] + 0.3 + j * DUR[4] / 8, -18, rng.uniform(-0.5, 0.5))
M.fx_(M.noise(DUR[5], 3000, 9000, 9, 0.4, 0.4), B[5], -22)
M.fx_(M.k('rooms/slam', 4), B[5] + DUR[5] * 0.5, -11)
# 6-8 the body: heartbeat climbing, heatstroke whine, dizzy smear at pass out
M.heartbeat(B[6], B[8] + DUR[8] * 0.7, 80, 150, -9)
n7 = int(DUR[7] * SR)
M.fx_(np.sin(2 * np.pi * 2600 * np.arange(n7) / SR) * 0.08 * M.env(n7, 1.0, 0.2), B[7], -18)
M.fx_(M.k('rooms/slam', 6), B[7] + DUR[7] * 0.62, -8)
M.fx_(S.whoosh(DUR[8], 3000, 100), B[8], -12)
M.fx_(S.impact(1.4), B[8] + DUR[8] * 0.75, -9)
# 9 kids: two quick tones racing up, the small one faster
for j in range(6):
    M.fx_(S.pop_note(60 + j, 0.08), B[9] + 0.3 + j * 0.45, -18, -0.5)
    M.fx_(S.pop_note(60 + 3 * j, 0.08), B[9] + 0.3 + j * 0.45 + 0.1, -16, 0.5)
# 10 cracked window: thin air whistle
n10 = int(DUR[10] * SR)
M.fx_(S.bp(np.random.default_rng(10).standard_normal(n10), 1800, 2400) * M.env(n10, 0.3, 0.3), B[10], -22)
# 11 never: buzzer
nb = int(0.5 * SR)
M.fx_(S.norm(S.square(110, nb)) * M.env(nb, 0.01, 0.05), B[11] + 0.5, -16)
# 12 escape: horn honks, then glass breaking
for j in range(3):
    M.fx_(horn(0.35), B[12] + 0.2 + j * 0.45, -9)
gb = B[12] + DUR[12] * 0.55
M.fx_(M.k('rooms/metal_hit', 0), gb, -6)
for j in range(10):
    M.fx_(M.k('rooms/keyclick', j), gb + 0.03 + j * 0.03, -10, rng.uniform(-0.7, 0.7))

# music
M.drone(0, B[1], 40, -18); M.strings([52, 55, 59], 0, B[1], -22, 800, 1800); M.clock(0, B[1], -26, 0.25)
M.drone(B[-1], D + 0.6, 40, -18); M.strings([52, 55, 59], B[-1], D + 0.05, -22, 800, 1800)
M.pad([52, 59, 64, 68], B[1], B[2], -22, 2200)                                # outside: lazy summer
M.drone(B[2], B[6], 40, -18); M.strings([52, 55, 59, 62], B[2], B[6], -22, 400, 3000)  # heat building
M.drone(B[6], B[8] + DUR[8] * 0.7, 38, -17)
M.strings([50, 53, 57, 60], B[6], B[8] + DUR[8] * 0.7, -21, 1000, 5000)
M.drone(B[9], B[12], 33, -19); M.pad([45, 52, 57], B[9], B[12], -22, 800)    # kids / windows: serious
M.pad([52, 59, 64, 68, 71], B[12], B[-1], -20, 2600, a=0.8)                   # escape: hope
M.shape(B[1], B[2], -4)                      # outside: easy
M.shape(B[4], B[6], -2)
M.shape(B[7] + DUR[7] * 0.5, B[8] + DUR[8], 2)  # heatstroke peak
M.shape(B[9], B[12], -3)                      # serious, quieter
M.finish(sys.argv[2], sys.argv[3])
print('ok')
