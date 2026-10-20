#!/usr/bin/env python3
"""How long food takes to digest. Opens mid-chomp on a burger; loops back into the bite."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

BUN = ramp('#f0b060', '#c08030', '#ffd8a0')
PATTY = ramp('#7a4022', '#4e2414', '#a8603a')
FOOD = ramp('#c8783a', '#8a4a1e', '#f0a868')


def burger(cv, x, y, s, bite=0.0):
    f_top = rotell(x, y - 90 * s, 260 * s, 120 * s, 0)
    if bite > 0:
        b = circle(x + 250 * s, y - 20 * s, 140 * s * bite)
        f_top = subtract(f_top, b)
    cv.shape(f_top, (x - 280 * s, y - 220 * s, x + 280 * s, y + 40 * s), BUN)
    pat = rbox(x, y + 10 * s, 270 * s, 40 * s, 30 * s)
    lettuce = rbox(x, y - 30 * s, 280 * s, 14 * s, 10 * s)
    if bite > 0:
        b = circle(x + 250 * s, y - 20 * s, 140 * s * bite)
        pat, lettuce = subtract(pat, b), subtract(lettuce, b)
    cv.shape(lettuce, (x - 300 * s, y - 60 * s, x + 300 * s, y), ramp('#7fd34f'))
    cv.shape(pat, (x - 290 * s, y - 40 * s, x + 290 * s, y + 60 * s), PATTY)
    bot = rbox(x, y + 80 * s, 250 * s, 40 * s, 30 * s)
    if bite > 0:
        bot = subtract(bot, circle(x + 250 * s, y - 20 * s, 140 * s * bite))
    cv.shape(bot, (x - 260 * s, y + 30 * s, x + 260 * s, y + 130 * s), BUN)
    for k in range(7):
        dot(cv, x - 150 * s + k * 50 * s, y - 150 * s + 15 * s * np.sin(k), 6 * s, (np.full(3, 0.97, np.float32),) * 3)


def body_map(cv, T, x=0, y=0, s=1.0, pos=0.0, hi=None):
    """See-through body with the whole food route: mouth, food pipe, stomach, small gut, large gut.
    pos 0..1 places the food dot along the route; hi names a part to light up."""
    cv.shape(smooth(80 * s, circle(x, y - 760 * s, 150 * s), capsule(x, y - 520 * s, x, y + 420 * s, 300 * s, 260 * s)), (x - 340 * s, y - 930 * s, x + 340 * s, y + 700 * s),
             ramp('#a8c8f0', '#6a8fb8', '#d8ecff'), ow=4, alpha=0.4)
    route = [(x, y - 700 * s), (x, y - 560 * s), (x - 10 * s, y - 330 * s)]
    line(cv, route, 26 * s, ramp('#f4b0b8'), ow=3, flat=False, a=1.0 if hi in (None, 'pipe') else 0.5)
    stomach(cv, x - 40 * s, y - 220 * s, 0.4 * s, T, acid=0.5)
    pts = []
    for k in range(60):                                                     # the small gut coil
        a = k * 0.55
        pts.append((x + (160 - 2 * k) * s * np.cos(a) * 0.9, y + 60 * s + k * 3.2 * s + 70 * s * np.sin(a)))
    line(cv, pts, 22 * s, GUTC, ow=3, flat=False, a=1.0 if hi in (None, 'small') else 0.5)
    frame_ = [(x - 220 * s, y + 380 * s), (x - 220 * s, y + 20 * s), (x + 220 * s, y + 20 * s), (x + 220 * s, y + 380 * s), (x + 60 * s, y + 430 * s)]
    line(cv, frame_, 46 * s, ramp('#d9a07a', '#a8704e', '#f4c8a8'), ow=4, flat=False, a=1.0 if hi in (None, 'large') else 0.5)
    full = route + [(x - 40 * s, y - 220 * s)] + pts[::6] + frame_
    L = len(full) - 1
    u = np.clip(pos, 0, 1) * L
    i = min(int(u), L - 1); f = u - i
    px = full[i][0] + (full[i + 1][0] - full[i][0]) * f
    py = full[i][1] + (full[i + 1][1] - full[i][1]) * f
    disc(cv, px, py, 30 * s, FOOD, ow=3)
    cv.glow(circle(px, py, 30 * s), (px - 120, py - 120, px + 120, py + 120), '#ffd23f', 40 * s, 0.4)


def b0_hook(lt, dur, T):
    """Mid-chomp on frame one; before 0 the burger flies in (the loop)."""
    fly = ease(np.clip((lt + 0.8) / 0.8, 0, 1))
    bite = ease(np.clip(lt / 0.25, 0, 1)) if lt >= 0 else 0.0
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    burger(cv, -500 + 500 * fly, 100 - 80 * np.sin(np.pi * fly), 1.3, bite=bite)
    if lt >= 0:
        for q in range(10):
            ph = min(1.0, lt * 1.5 + q * 0.03)
            a = -0.8 + q * 0.18
            disc(cv, 300 + np.cos(a) * 400 * ph, 50 + np.sin(a) * 300 * ph + 600 * ph * ph, 12, BUN, ow=2, alpha=1 - ph)
        hook_text(cv, 'THE TRIP', lt, y=-760, size=160, color=(255, 138, 42))
    return cv


def b1_swallow(lt, dur, T):
    cv = Canvas(0, -300, 0.95)
    sky_bg(cv)
    body_map(cv, T, 0, 0, 1.0, pos=0.03 + 0.07 * ease(np.clip(lt / (dur * 0.6), 0, 1)), hi='pipe')
    badge(cv, 'SECONDS', y=-1150, col=(120, 255, 140))
    return cv


def b2_stomach(lt, dur, T):
    cv = Canvas(0, 0, 1.1)
    sky_bg(cv)
    stomach(cv, 0, 100, 1.1, T, acid=0.6)
    for q in range(6):
        a = lt * 2 + q * 1.05
        disc(cv, 20 + np.cos(a) * 120, 260 + np.sin(a) * 60, 30, FOOD, ow=3)
    badge(cv, '2-4 HOURS', y=-560, col=YEL)
    return cv


def b3_small(lt, dur, T):
    cv = Canvas(0, -300, 0.95)
    sky_bg(cv)
    body_map(cv, T, 0, 0, 1.0, pos=0.22 + 0.4 * ease(np.clip(lt / (dur * 0.9), 0, 1)), hi='small')
    badge(cv, '+ HOURS', y=-1150, col=YEL)
    return cv


def b4_soak(lt, dur, T):
    cv = Canvas(0, 200, 1.0)
    sky_bg(cv)
    box(cv, 0, 600, 900, 300, ramp('#c45a72'), r=0, ow=4, shadow=0)
    box(cv, 0, 860, 900, 70, ramp('#d8343a'), r=30, ow=4)
    for i in range(9):
        x = -480 + i * 120
        sway = 18 * np.sin(T * 2 + i)
        cv.shape(capsule(x, 600, x + sway, 220, 46, 40), (x - 60, 170, x + 60, 640), GUTC)
    for i in range(12):
        u = ((lt * 0.6 + i / 12) % 1)
        disc(cv, -480 + (i % 9) * 120, 100 + u * 780, 16, ramp('#ffd23f'), ow=2)
    label(cv, 'SOAKED UP', 0, -320, 90, YEL)
    return cv


def b5_large(lt, dur, T):
    cv = Canvas(0, 0, 1.4)
    sky_bg(cv)
    box(cv, 0, 0, 1000, 260, ramp('#d9a07a', '#a8704e', '#f4c8a8'), r=240)
    box(cv, 0, 0, 1000, 190, ramp('#b07a50', '#80502e', '#d09a70'), r=180, ow=0, shadow=0)
    lump(cv, 0, 0, 120, col=POOP)
    for q in range(3):
        ph = (lt * 0.6 + q / 3) % 1
        label(cv, 'z', 90 + 30 * q, -140 - 120 * ph, 40 + 14 * q, WHT, a=1 - ph)
    label(cv, 'JUST SITS THERE', 0, -360, 70, WHT)
    return cv


def b6_day(lt, dur, T):
    k = np.clip(lt / (dur * 0.8), 0, 1)
    cv = Canvas(0, 0, 1.0)
    cv.background('#3fa2ee' if (k * 2) % 1 < 0.5 else '#1b2350', '#bfe6ff' if (k * 2) % 1 < 0.5 else '#3a3f7a', vignette=0.2)
    box(cv, 0, 0, 260, 300, ramp('#ffffff', '#d8dde4', '#ffffff'), r=30)
    box(cv, 0, -240, 260, 60, RED, r=24)
    label(cv, f'DAY {1 + int(k * 1.99)}', 0, 30, 110, (40, 40, 50))
    lump(cv, 0, 450, 80, col=POOP)
    return cv


def b7_total(lt, dur, T):
    cv = Canvas(0, -300, 0.95)
    sky_bg(cv)
    body_map(cv, T, 0, 0, 1.0, pos=(lt / dur) % 1)
    badge(cv, '1-3 DAYS', y=-1150, col=(255, 138, 42))
    return cv


def b8_study(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(0, -300, 1.0)
    sky_bg(cv, ground=0)
    guy(cv, -250, 0, 0.9, face='happy', arms=((12, 0), (12, 0)))
    guy(cv, 250, 0, 0.9, face='happy', woman=True, shirt=PINK, arms=((12, 0), (12, 0)))
    badge(cv, f'{int(33 * k)} HRS', y=-1050, col=(127, 210, 255), x=-250, w=240)
    badge(cv, f'{int(47 * k)} HRS', y=-1050, col=(255, 160, 180), x=250, w=240)
    return cv


BEATS = [b0_hook, b1_swallow, b2_stomach, b3_small, b4_soak, b5_large, b6_day, b7_total, b8_study]

if __name__ == '__main__':
    run(BEATS)
