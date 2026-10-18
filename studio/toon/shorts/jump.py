#!/usr/bin/env python3
"""What If Everyone on Earth Jumped at Once? Opens with people all around the planet leaping up."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

OCEAN = ramp('#2f7fd0', '#1d5a9e', '#6fb6ff')
LAND = ramp('#5fbf4a', '#3d8a30', '#9ee07a')
SHIRTS = [ORANGE, BLUE, GREEN, PINK, YELLOW, ramp('#7a4fd0')]


def earth(cv, x, y, r, T, dy=0.0):
    disc(cv, x, y + dy, r, OCEAN, bevel=r * 0.5)
    for a, rr, d in ((0.3, 0.42, 0.45), (2.2, 0.35, 0.5), (4.0, 0.3, 0.4), (5.2, 0.22, 0.6)):
        cv.shape(circle(x + np.cos(a + T * 0.05) * r * d, y + dy + np.sin(a) * r * d, r * rr),
                 (x - r, y + dy - r, x + r, y + dy + r), LAND, ow=3, shadow=0, mask=lambda X, Y: np.sqrt((X - x) ** 2 + (Y - y - dy) ** 2) - r)


def people_ring(cv, x, y, r, T, jump, n=22, s=0.17):
    for i in range(n):
        a = -np.pi + i * 2 * np.pi / n
        if np.sin(a) > 0.35:
            continue                                  # skip the far bottom (out of view behind the planet)
        h = r + 30 + jump * 110
        px, py = x + np.cos(a) * h, y + np.sin(a) * h
        up = np.degrees(a) + 90
        guy_r(cv, px, py, s, up, SHIRTS[i % 6], jump)


def guy_r(cv, x, y, s, deg, shirt, jump):
    """Tiny person standing on the curve, rotated to face outward."""
    c, sn = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    P = lambda u, v: (x + u * c - v * sn, y + u * sn + v * c)
    body = [P(0, 0), P(0, -330 * s)]
    line(cv, [P(-30 * s, 0), P(-20 * s, -200 * s)], 30 * s, JEANS, ow=3)
    line(cv, [P(30 * s, 0), P(20 * s, -200 * s)], 30 * s, JEANS, ow=3)
    line(cv, [P(0, -200 * s), P(0, -380 * s)], 70 * s, shirt, ow=3)
    arm = 150 if jump > 0.3 else 20
    for sx in (-1, 1):
        line(cv, [P(sx * 50 * s, -360 * s), P(sx * 140 * s * np.sin(np.radians(arm)), -360 * s - 140 * s * np.cos(np.radians(arm)))], 24 * s, SKIN, ow=3)
    hx, hy = P(0, -470 * s)
    disc(cv, hx, hy, 70 * s, SKIN, ow=3)


def b0_hook(lt, dur, T):
    """Everyone leaps. Before 0: crouching, about to jump (the loop)."""
    j = max(0.0, np.sin(np.clip((lt + 0.3) / 1.4, 0, 1) * np.pi)) if lt > -0.3 else 0.0
    cv = Canvas(0, -60, 1.0)
    sky_bg(cv)
    earth(cv, 0, 250, 420, T)
    people_ring(cv, 0, 250, 420, T, j)
    if lt >= 0:
        hook_text(cv, 'ALL AT ONCE', lt, y=-700, size=120, pop_t=0.25)
    return cv


def b1_count(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=500)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    n = int(8_000_000_000 * k)
    label(cv, f'{n:,}', 0, -560, 96, (255, 236, 80))
    rng = np.random.default_rng(2)
    for i in range(int(70 * k) + 1):
        guy(cv, rng.uniform(-520, 520), 500 + rng.uniform(0, 400), 0.16, face='happy', shirt=SHIRTS[i % 6], arms=((20, 0), (20, 0)))
    return cv


def b2_weight(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    box(cv, 0, 400, 420, 60, STEEL, r=20)
    box(cv, 0, 470, 120, 80, DARK, r=10)
    rng = np.random.default_rng(3)
    k = ease(np.clip(lt / 0.8, 0, 1))
    for i in range(int(40 * k)):
        guy(cv, rng.uniform(-360, 360), 340 - rng.uniform(0, 300), 0.15, face='happy', shirt=SHIRTS[i % 6], arms=((20, 0), (20, 0)))
    label(cv, '500,000,000 TONS', 0, -560, 84, (255, 236, 80))
    return cv


def b3_push(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    sky_bg(cv)
    j = ease(np.clip(lt / (dur * 0.5), 0, 1))
    earth(cv, 0, 250, 420, T, dy=8 * j)
    people_ring(cv, 0, 250, 420, T, j)
    arrows(cv, [((0, -420), (0, -620))], (255, 236, 80), 14)
    arrows(cv, [((0, 760), (0, 900))], (255, 90, 80), 14)
    return cv


def b4_q(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    earth(cv, 0, 100, 420, T)
    hook_text(cv, 'DOES IT MOVE?', lt, y=-680, size=110, pop_t=0.3)
    return cv


def b5_atom(lt, dur, T):
    z = 1.0 + 12 * ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    r = 60 * z ** 0.8
    disc(cv, 0, 0, r * 0.4, ramp('#e2483d'))
    for k in range(3):
        a = T * 3 + k * 2.1
        cv.shape(subtract(rotell(0, 0, r * 2, r * 0.7, k * 60), rotell(0, 0, r * 2 - 4, r * 0.7 - 4, k * 60)), (-r * 2.2, -r * 2.2, r * 2.2, r * 2.2), flat(hexc('#ffffff')), ow=0, shadow=0, flat=True)
        disc(cv, np.cos(a) * r * 2 * np.cos(np.radians(k * 60)) - np.sin(a) * r * 0.7 * np.sin(np.radians(k * 60)),
             np.cos(a) * r * 2 * np.sin(np.radians(k * 60)) + np.sin(a) * r * 0.7 * np.cos(np.radians(k * 60)), 14, BLUE)
    label(cv, 'LESS THAN AN ATOM', 0, -640, 84, (255, 236, 80))
    return cv


def b6_ratio(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=700)
    tilt = 14 * ease(np.clip(lt / 0.8, 0, 1))
    c, s = np.cos(np.radians(tilt)), np.sin(np.radians(tilt))
    cv.shape(poly([(-60, 700), (60, 700), (0, 560)]), (-70, 550, 70, 710), DARK)
    line(cv, [(-450 * c, 560 + 450 * s), (450 * c, 560 - 450 * s)], 22, ramp('#a8693a'), ow=4)
    earth(cv, -420 * c, 560 + 420 * s - 260, 240, T)
    guy(cv, 420 * c, 560 - 420 * s - 10, 0.22, face='shock', arms=((150, 20), (150, 20)))
    label(cv, '10 TRILLION X HEAVIER', 0, -560, 76, (255, 236, 80))
    return cv


def b7_land(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    sky_bg(cv)
    j = 1 - ease(np.clip(lt / (dur * 0.5), 0, 1))
    earth(cv, 0, 250, 420, T, dy=-8 * (1 - j))
    people_ring(cv, 0, 250, 420, T, j)
    if j < 0.05:
        arrows(cv, [((0, 900), (0, 760))], (120, 255, 140), 14)
    return cv


def b8_silly(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    sky_bg(cv)
    j = abs(np.sin(lt * 3))
    earth(cv, 0, 250, 420, T)
    people_ring(cv, 0, 250, 420, T, j)
    hook_text(cv, "DIDN'T NOTICE", lt, y=-700, size=110, pop_t=0.4, color=(255, 236, 80))
    return cv


BEATS = [b0_hook, b1_count, b2_weight, b3_push, b4_q, b5_atom, b6_ratio, b7_land, b8_silly]

if __name__ == '__main__':
    run(BEATS)
