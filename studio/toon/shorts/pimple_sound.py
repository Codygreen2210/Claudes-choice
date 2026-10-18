"""Sound for the pimple Short.  STUDIO_ROOT=... python3 pimple_sound.py times.json narration.wav out.wav

Music: creepy body-horror, small and close. Opening/loop: a squelchy squeeze, a pop, and a dissonant
string glide following the red line up. Triangle: a low pulse and a cold bell. X-ray veins: hollow drone,
heartbeat. Germs riding the blood: tense ticking strings. Clot / sick: it all darkens, fever whine.
Good news: warm major lift. Tips and doctor: light, calm. Loop line: back to the squeeze.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Mix

M = Mix(sys.argv[1]); S = M.S; B, DUR, D = M.B, M.DUR, M.D; SR = M.SR
rng = np.random.default_rng(4)


def squish(dur=0.6, seed=0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 180 + 120 * np.sin(2 * np.pi * 6 * t)
    x = S.bp(np.random.default_rng(seed).standard_normal(n), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t))
    x += 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return S.norm(x) * M.env(n, 0.05, 0.2)


def glide(t0, t1, db):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    f = np.linspace(220, 880, n)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.6 * np.sin(2 * np.pi * np.cumsum(f * 1.06) / SR)
    M.mu(x * 0.4 * M.env(n, 0.1, 0.2), t0, db)


# opening / loop: squeeze builds in the last beat, POP right on frame one, red line glides up
M.fx_(squish(0.9, 1), B[-1] + max(0.0, DUR[-1] - 1.0), -6)
M.fx_(S.pop_note(60, 0.15), 0.0, -4)
M.fx_(M.k('people/step_wet', 2), 0.02, -8)
M.fx_(S.impact(0.5), 0.0, -12)
glide(0.45, min(B[1], 1.5), -18)
M.heartbeat(0.3, B[1], 100, 110, -14)
M.swishes()
# 1-2 triangle drawn line by line, red stamp
M.fx_(S.whoosh(0.5, 5000, 300), B[1] - 0.05, -7)
for j in range(3):
    M.fx_(M.k('rooms/pen', j), B[1] + 0.1 + j * 0.35, -10)
M.fx_(M.k('rooms/slam', 3), B[2] + 0.2, -8)
M.mu(S.bell(70, 2.5, dec=1.5), B[2] + 0.2, -17)
# 3-4 x-ray: whoosh in, hollow heartbeat, vein drawing scrape
M.fx_(S.whoosh(0.6, 300, 2500), B[3], -11)
M.heartbeat(B[3], B[5], 70, 80, -13)
for j in range(5):
    M.fx_(S.pop_note(70 + j * 2, 0.08), B[4] + j * DUR[4] * 0.14, -18)
# 5 squeeze and germs going in
M.fx_(squish(1.1, 5), B[5] + 0.05, -6)
for j in range(8):
    M.fx_(S.pop_note(int(rng.integers(84, 96)), 0.05), B[5] + 0.8 + j * 0.12, -14, rng.uniform(-0.5, 0.5))
M.fx_(M.k('rooms/slam', 4), B[5] + DUR[5] * 0.5, -10)
# 6 germs ride the blood: whooshing flow, ticking, heartbeat speeds up
M.fx_(M.noise(DUR[6], 200, 1200, 61, 0.3, 0.3), B[6], -15)
M.heartbeat(B[6], B[8], 90, 130, -11)
for j in range(int(DUR[6] / 0.2)):
    M.fx_(M.tick(), B[6] + j * 0.2, -19)
# 7 clot: deep thud, a stamp
M.fx_(S.impact(1.6), B[7] + 0.8, -6)
M.fx_(M.k('rooms/slam', 6), B[7] + 0.8, -8)
# 8 sick: fever whine, swelling squelch
n8 = int(DUR[8] * SR)
M.fx_(np.sin(2 * np.pi * 2400 * np.arange(n8) / SR) * 0.07 * M.env(n8, 1.0, 0.3), B[8], -16)
M.fx_(squish(1.0, 8), B[8] + 0.4, -12)
# 9 good news: chime
for j, m in enumerate((72, 76, 79, 84)):
    M.fx_(S.bell(m, 1.2), B[9] + 0.2 + j * 0.1, -12)
# 10 tips: warm cloth steam hiss, patch stick
M.fx_(M.noise(DUR[10] * 0.45, 2000, 8000, 101, 0.2, 0.2), B[10] + 0.1, -18)
M.fx_(S.pop_note(80, 0.12), B[10] + DUR[10] * 0.5, -10)
M.fx_(M.k('rooms/keyclick', 2), B[10] + DUR[10] * 0.52, -12)
# 11 doctor: door knock, friendly ding
for j in range(2):
    M.fx_(M.k('rooms/knock', j), B[11] + 0.2 + j * 0.25, -12)
M.fx_(S.bell(84, 1.2), B[11] + 0.9, -14)

# music
M.drone(0, B[1], 37, -19); M.strings([49, 52, 55, 58], 0, B[1], -23, 500, 1500)
M.drone(B[-1], D + 0.6, 37, -19); M.strings([49, 52, 55, 58], B[-1], D + 0.05, -23, 500, 1500)
M.drone(B[1], B[3], 33, -19); M.clock(B[1], B[3], -26, 0.8)
M.drone(B[3], B[5], 31, -18); M.pad([43, 50, 55], B[3], B[5], -23, 700)
M.drone(B[5], B[7], 31, -17); M.strings([43, 46, 50, 53], B[5], B[7], -21, 400, 4000)
M.drone(B[7], B[9], 28, -18)
M.pad([48, 55, 60, 64, 67], B[9], B[-1], -20, 2600, a=0.8)
M.shape(B[3], B[5], -2); M.shape(B[6], B[8] + DUR[8], 2); M.shape(B[9], B[-1], -3)
M.finish(sys.argv[2], sys.argv[3])
print('ok')
