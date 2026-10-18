#!/usr/bin/env python3
"""How Long Is Your Small Intestine? Opens on the tube shooting out of a guy's belly across the grass."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

GUT = ramp('#f08aa0', '#c45a72', '#ffc0cc')
BIG = ramp('#d9a07a', '#a8704e', '#f4c8a8')
GROUND = 700
FT = 70                       # world px per foot on the lawn


def gut_line(cv, x0, y0, length, T, wob=1.0, w=40):
    """The tube lying on the grass from (x0, y0) to the right, gently wavy."""
    if length < 4:
        return
    xs = np.linspace(0, length, max(4, int(length / 25)))
    pts = [(x0 + u, y0 + 10 * wob * np.sin(u / 60 + T * 2)) for u in xs]
    line(cv, pts, w, GUT, ow=4)


def b0_hook(lt, dur, T):
    """It shoots out of his belly and races across the lawn. Before 0: coiled at the belly (the loop)."""
    L = 20 * FT * ease(np.clip((lt + 0.4) / 2.2, 0, 1))
    cv = Canvas(-500 + 0.5 * L, 200, 1.0 - 0.38 * min(1, L / (20 * FT)))
    sky_bg(cv, ground=GROUND)
    guy(cv, -500, GROUND, 0.9, face='shock' if L > 50 else 'calm', arms=((150, 20), (150, 20)))
    gut_line(cv, -500, GROUND - 420, L, T)
    disc(cv, -500 + L, GROUND - 420, 30, GUT)
    if lt >= 0:
        hook_text(cv, 'THIS LONG', lt, y=-640, size=130, pop_t=0.3)
    return cv


def lawn(cv, T, L=20 * FT):
    sky_bg(cv, ground=GROUND)
    guy(cv, -500, GROUND, 0.9, face='shock', arms=((150, 20), (150, 20)))
    gut_line(cv, -500, GROUND - 420, L, T)


def b1_twenty(lt, dur, T):
    cv = Canvas(200, 280, 0.62)
    lawn(cv, T)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    x1 = -500 + 20 * FT * k
    line(cv, [(-500, GROUND - 120), (x1, GROUND - 120)], 16, YELLOW, ow=4)
    for f in range(0, int(20 * k) + 1, 5):
        line(cv, [(-500 + f * FT, GROUND - 160), (-500 + f * FT, GROUND - 80)], 8, YELLOW, ow=3)
    ft = max(1, int(20 * k))
    label(cv, f'{ft} FOOT' if ft == 1 else f'{ft} FEET', 200, -560, 140, (255, 236, 80))
    return cv


def giraffe(cv, x, ground, h):
    s = h / 1260
    cv.shape(rotell(x, ground - 520 * s, 230 * s, 130 * s, 0), (x - 240 * s, ground - 660 * s, x + 240 * s, ground - 380 * s), YELLOW)
    for dx in (-150, -60, 70, 160):
        line(cv, [(x + dx * s, ground - 450 * s), (x + dx * s, ground)], 30 * s, YELLOW, ow=4)
    line(cv, [(x + 150 * s, ground - 560 * s), (x + 230 * s, ground - 1150 * s)], 60 * s, YELLOW, ow=4)
    cv.shape(rotell(x + 280 * s, ground - 1190 * s, 90 * s, 45 * s, -15), (x + 180 * s, ground - 1260 * s, x + 380 * s, ground - 1120 * s), YELLOW)
    for k in range(7):
        disc(cv, x + (-160 + k * 50) * s, ground - (520 + 30 * np.sin(k)) * s, 22 * s, ramp('#b07030'), ow=0, shadow=0)
    dot(cv, x + 300 * s, ground - 1200 * s, 9 * s)


def b2_giraffe(lt, dur, T):
    cv = Canvas(0, -100, 0.62)
    sky_bg(cv, ground=GROUND)
    giraffe(cv, -380, GROUND, 18 * FT)
    rise = ease(np.clip(lt / (dur * 0.6), 0, 1))
    top = GROUND - 20 * FT * rise
    line(cv, [(300, GROUND), (300 + 20 * np.sin(top / 80), top)], 30, GUT, ow=4)
    if rise > 0.95:
        hook_text(cv, 'TALLER!', lt, y=-680, size=130, pop_t=dur * 0.62, color=(255, 236, 80))
    return cv


def tube_close(cv, T, food=0.0, squeeze_t=None):
    sky_bg(cv)
    box(cv, 0, 0, 700, 260, GUT, r=200)
    box(cv, 0, 0, 640, 200, ramp('#c45a72', '#9a3a52', '#e07890'), r=180, ow=0, shadow=0)
    if squeeze_t is not None:
        x = -600 + (squeeze_t % 1) * 1200
        cv.shape(rotell(x, 0, 80, 120, 0), (x - 90, -130, x + 90, 130), ramp('#8a5a2a'), ow=4)


def b3_soak(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    tube_close(cv, T)
    for i in range(6):
        x = -700 + ((lt * 300 + i * 220) % 1400)
        disc(cv, x, 0, 46, ramp(['#e0a050', '#7fbf4f', '#e2483d'][i % 3]), ow=4)
    label(cv, 'FOOD', 0, -330, 100, (255, 236, 80))
    return cv


def villi(cv, T, grab=0.0):
    sky_bg(cv)
    box(cv, 0, 600, 900, 300, ramp('#c45a72'), r=0, ow=4, shadow=0)
    box(cv, 0, 860, 900, 70, ramp('#d8343a'), r=30, ow=4)                       # blood vessel under
    for i in range(9):
        x = -480 + i * 120
        sway = 18 * np.sin(T * 2 + i)
        cv.shape(capsule(x, 600, x + sway, 220, 46, 40), (x - 60, 170, x + 60, 640), GUT)
    return grab


def b4_villi(lt, dur, T):
    cv = Canvas(0, 200, 1.0)
    villi(cv, T)
    hook_text(cv, 'TINY FINGERS', lt, y=-680, size=110, pop_t=0.4)
    return cv


def b5_grab(lt, dur, T):
    cv = Canvas(0, 200, 1.0)
    villi(cv, T)
    for i in range(10):
        u = ((lt * 0.6 + i / 10) % 1)
        x = -480 + (i % 9) * 120
        y = 100 + u * 780
        disc(cv, x + 10 * np.sin(u * 8), y, 18, ramp('#ffd23f'), ow=3)
    arrows(cv, [((520, 300), (520, 820))], (255, 236, 80), 12)
    label(cv, 'INTO YOUR BLOOD', 0, -500, 80, (255, 90, 80))
    return cv


def b6_hours(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    tube_close(cv, T, squeeze_t=lt / dur)
    box(cv, 0, -480, 260, 85, DARK, r=26)
    h = 1 + int(lt / dur * 4)
    label(cv, f'{h} HOUR' if h == 1 else f'{h} HOURS', 0, -470, 90, (255, 236, 80))
    return cv


def b7_large(lt, dur, T):
    cv = Canvas(200, 280, 0.62)
    sky_bg(cv, ground=GROUND)
    gut_line(cv, -500, GROUND - 420, 20 * FT, T)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    line(cv, [(-500, GROUND - 150), (-500 + 5 * FT * k, GROUND - 150)], 90, BIG, ow=5)
    label(cv, 'SMALL: 20 FT', 200, GROUND - 640, 120, (255, 160, 180))
    label(cv, 'LARGE: 5 FT', 420, GROUND - 150, 100, (240, 190, 150))
    return cv


def b8_inside(lt, dur, T):
    cv = Canvas(0, 230, 1.4)
    sky_bg(cv, ground=GROUND)
    guy(cv, 0, GROUND, 1.0, face='calm', arms=((15, 0), (15, 0)))
    k = ease(np.clip(lt / 0.6, 0, 1))
    cx, cy = 0, GROUND - 480
    cv.shape(ellipse(cx, cy, 130, 120), (cx - 140, cy - 130, cx + 140, cy + 130), ramp('#1d3f66'), ow=4, alpha=0.6 * k)
    pts = [(cx + 100 * np.cos(a) * (1 - a / 30), cy + 90 * np.sin(a * 1.3) * (1 - a / 40)) for a in np.linspace(0, 26, 80)]
    line(cv, pts, 12, GUT, ow=3, a=k)
    return cv


BEATS = [b0_hook, b1_twenty, b2_giraffe, b3_soak, b4_villi, b5_grab, b6_hours, b7_large, b8_inside]

if __name__ == '__main__':
    run(BEATS)
