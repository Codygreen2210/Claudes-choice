#!/usr/bin/env python3
"""Drinking the ocean. Opens on a guy already slurping the sea through a giant straw; loops back into the slurp."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

SEA = ramp('#2f7fd0', '#1d5a9e', '#6fb6ff')
LAND = ramp('#5fbf4a', '#3d8a30', '#9ee07a')
SAND = ramp('#f2d79a', '#c9a866', '#fff0c8')
STRAW = ramp('#ff5a5a', '#c02a2a', '#ff9a9a')
KID = ramp('#c8505e', '#8e2a38', '#ee8a96')
SALT = (np.full(3, 0.97, np.float32),) * 3


def sea(cv, T, y0=150, amp=18):
    f, bb = wave_surface(y0, amp, 0.012, T * 2.2, x0=cv.cx - 640 / cv.zoom, x1=cv.cx + 640 / cv.zoom, y1=cv.cy + 1060 / cv.zoom)   # keep the field screen-sized
    cv.shape(f, bb, SEA, ow=4, shadow=0)
    for k in range(4):                                                      # glints on the water
        x = -420 + k * 280 + 40 * np.sin(T + k)
        line(cv, [(x - 50, y0 + 70 + k * 45), (x + 50, y0 + 70 + k * 45)], 6, flat(hexc('#bfeaff')), a=0.5)


def straw_path(x0, y0, x1, y1, n=24):
    """A bendy straw: up and over from (x0, y0) at the mouth, down into the water at (x1, y1)."""
    u = np.linspace(0, 1, n)
    mx, my = (x0 + x1) / 2, min(y0, y1) - 160
    xs = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u ** 2 * x1
    ys = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u ** 2 * y1
    return list(zip(xs, ys))


def slurp(cv, pts, T, rate=1.6, n=5, r=16):
    """Water slugs racing up the straw from the sea end to the mouth."""
    L = len(pts) - 1
    for q in range(n):
        u = 1 - ((T * rate + q / n) % 1)
        i = min(int(u * L), L - 1); f = u * L - i
        x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
        y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
        disc(cv, x, y, r, WATERC, ow=2)


def drinker(cv, T, x=-260, y=170, s=0.72, face='happy', tip=(170, 330), rate=1.6):
    guy(cv, x, y, s, face=face, arms=((40, 70), (70, 40)))
    mx, my = x + 30 * s, y - 640 * s                                        # his mouth
    pts = straw_path(mx, my, tip[0], tip[1])
    line(cv, pts, 30, STRAW, ow=4, flat=False)
    for k in range(0, len(pts), 3):                                         # candy stripes
        line(cv, pts[k:k + 2], 30, ramp('#ffffff'), ow=0, flat=True, a=0.8)
    slurp(cv, pts, T, rate)
    puff = 0.5 + 0.5 * np.sin(T * rate * 2 * np.pi)
    disc(cv, mx + 20 * s, my + 10 * s, (26 + 10 * puff) * s, ramp('#f6b8a0', '#d8907a', '#ffd8c8'), ow=2.5)


def earth(cv, x, y, r, T):
    disc(cv, x, y, r, SEA, bevel=r * 0.5)
    for a, rr, d in ((0.3, 0.42, 0.45), (2.2, 0.35, 0.5), (4.0, 0.3, 0.4), (5.2, 0.22, 0.6)):
        cv.shape(circle(x + np.cos(a + T * 0.05) * r * d, y + np.sin(a) * r * d, r * rr),
                 (x - r, y - r, x + r, y + r), LAND, ow=3, shadow=0, flat=True, mask=lambda X, Y: np.sqrt((X - x) ** 2 + (Y - y) ** 2) - r)


def kidney(cv, x, y, s, flip=1):
    f = subtract(rotell(x, y, 110 * s, 160 * s, 0), circle(x + flip * 120 * s, y, 60 * s))
    cv.shape(f, (x - 130 * s, y - 180 * s, x + 130 * s, y + 180 * s), KID)


def bottle(cv, x, y, s=1.0, fill=1.0, salt=0.0):
    box(cv, x, y, 110 * s, 230 * s, ramp('#e6f6ff', '#a8d4ee', '#ffffff'), r=40 * s, alpha=0.55)
    h = 210 * s * fill
    if fill > 0:
        box(cv, x, y + 210 * s - h, 95 * s, h, WATERC, r=30 * s, ow=0, shadow=0, alpha=0.9)
    box(cv, x, y - 260 * s, 50 * s, 30 * s, ramp('#3d7fd8'), r=10 * s)
    if salt > 0:
        box(cv, x, y + 200 * s - 30 * s * salt, 90 * s, 30 * s * salt, ramp('#ffffff', '#dfe6ec', '#ffffff'), r=12 * s, ow=2)


def b0_hook(lt, dur, T):
    """He's already slurping on frame one; before 0 it's the same slurp (the loop)."""
    cv = Canvas(0, 130, 1.0)
    sky_bg(cv)
    sea(cv, T)
    box(cv, -260, 230, 230, 80, SAND, r=60)                                 # his little rock of sand
    drinker(cv, T)
    for k in range(3):                                                      # ripples sucked toward the straw
        ph = (T * 1.2 + k / 3) % 1
        cv.shape(subtract(rotell(170, 335, 160 * (1 - ph) + 20, 40 * (1 - ph) + 6, 0), rotell(170, 335, 150 * (1 - ph) + 12, 32 * (1 - ph) + 2, 0)),
                 (-20, 280, 360, 390), flat(hexc('#bfeaff')), ow=0, shadow=0, flat=True, alpha=0.7 * ph)
    if lt >= 0:
        hook_text(cv, 'GULP', lt, y=-780, size=180, color=(127, 210, 255))
    return cv


def b1_world(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(0, 0, 1.0)
    cv.background('#0b1430', '#1b2350', vignette=0.3)
    earth(cv, 0, -60, 270, T)
    for i in range(18):                                                     # straws poking out all over the planet
        a = i * 2 * np.pi / 18 + 0.1
        wig = 10 * np.sin(T * 6 + i)
        p0 = (np.cos(a) * 262, -60 + np.sin(a) * 262)
        p1 = (np.cos(a) * 370 + wig, -60 + np.sin(a) * 370)
        line(cv, [p0, p1], 9, ramp('#ffffff'), ow=2.5, flat=False)
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        line(cv, [mid, p1], 9, STRAW, ow=2.5, flat=False)
    badge(cv, f'{int(65000 * k):,} POOLS EACH', y=-640, col=(127, 210, 255), w=580)
    label(cv, '8.2 BILLION STRAWS', 0, -520, 56, WHT)
    return cv


def b2_normal(lt, dur, T):
    cv = Canvas(0, -300, 1.0)
    sky_bg(cv, ground=0)
    sip = 0.5 + 0.5 * np.sin(lt * 4)
    guy(cv, -200, 0, 0.95, face='happy', arms=((12, 0), (60 + 50 * sip, 150)))
    bottle(cv, 190, -480, 0.8, fill=1.0)
    bottle(cv, 390, -480, 0.8, fill=1.0)
    badge(cv, '2 LITERS A DAY', y=-1000, col=(127, 210, 255), w=440)
    return cv


def b3_years(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for q in range(5):
        ph = (lt * 3 + q / 5) % 1
        box(cv, 120 + 420 * ph, -60 - 300 * ph + 400 * ph * ph, 150 * (1 - ph * 0.5), 170 * (1 - ph * 0.5), ramp('#ffffff', '#d8dde4', '#ffffff'), r=16, alpha=1 - ph)
    box(cv, 0, -40, 300, 260, ramp('#ffffff', '#d8dde4', '#ffffff'), r=30)    # a calendar tearing pages
    box(cv, 0, -270, 300, 50, RED, r=24)
    yr = int(220_000_000 * k)
    label(cv, 'YEAR', 0, -110, 60, (40, 40, 50))
    label(cv, f'{yr:,}', 0, 20, 70, (40, 40, 50))
    if k > 0.95:
        hook_text(cv, '220 MILLION YEARS', lt, y=-700, size=84, pop_t=dur * 0.6, color=YEL)
    return cv


def b4_kidneys(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    kidney(cv, -200, 0, 1.2, 1)
    kidney(cv, 200, 0, 1.2, -1)
    k = min(1.0, lt / (dur * 0.5))
    meter(cv, 0, -480, 460, k, RED if k > 0.95 else YEL, '1 LITER AN HOUR')
    for q in range(4):
        ph = (lt * 1.5 + q / 4) % 1
        drop(cv, -20 + 40 * (q % 2), -300 + 300 * ph, 22, a=1 - ph)
    if k > 0.95:
        label(cv, 'MAX', 0, -360, 70, RED)
    return cv


def b5_nonstop(lt, dur, T):
    k = np.clip(lt / (dur * 0.85), 0, 1)
    day = (lt * 0.9) % 1 < 0.5
    cv = Canvas(0, -300, 1.0)
    cv.background('#3fa2ee' if day else '#1b2350', '#bfe6ff' if day else '#3a3f7a', vignette=0.2)
    if day:
        sun(cv, 380, -800, 90, T)
    else:
        moon(cv, 380, -800, 80)
    sea(cv, T, y0=60)
    drinker(cv, T * 2, x=-240, y=40, s=0.85, face='worried', tip=(200, 230), rate=3.0)
    badge(cv, f'{int(18_000_000 * k):,}+ YEARS', y=-1010, col=YEL, w=560)
    return cv


def b6_salt(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    bottle(cv, 0, -40, 1.2, fill=1.0, salt=k)
    for sx in (-1, 1):                                                      # two spoons tipping salt in
        ang = 0.4 * ease(np.clip(lt / 0.6, 0, 1))
        hx, hy = sx * 330, -480
        line(cv, [(hx, hy), (hx - sx * 150 * np.cos(ang), hy + 150 * np.sin(ang))], 16, STEEL, ow=3, flat=False)
        cv.shape(rotell(hx + sx * 60, hy + 10, 70, 36, 0), (hx + sx * 60 - 80, hy - 40, hx + sx * 60 + 80, hy + 60), STEEL)
        for q in range(8):
            ph = (lt * 1.6 + q / 8) % 1
            gx = hx + sx * 60 + (0 - (hx + sx * 60)) * ph + 10 * np.sin(q * 3)
            dot(cv, gx, hy + 20 + 260 * ph, 8, SALT)
    badge(cv, '2 SPOONS OF SALT', y=-640, col=WHT, w=470)
    label(cv, '1 LITER', 0, -60, 64, (30, 60, 110))
    return cv


def b7_thirst(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.85), 0, 1))
    cv = Canvas(0, -300, 1.0)
    cv.background('#ffb07a', '#ffe0b0', vignette=0.3 + 0.3 * k)
    box(cv, 0, 600, 1600, 600, SAND, r=0, ow=0, shadow=0)
    sway = 8 * k * np.sin(lt * 5)
    guy(cv, -120 + sway, 0, 0.95, face='shock' if k > 0.6 else 'worried', arms=((20, 0), (30, 40)), tilt_head=0.3 * k)
    meter(cv, 330, -700, 300, 1 - 0.9 * k, (127, 210, 255) if k < 0.6 else RED, 'WATER')
    for q in range(3):
        ph = (lt * 1.3 + q / 3) % 1
        drop(cv, -120 + (q - 1) * 120, -880 + 200 * ph, 18, a=1 - ph)
    if k > 0.7:
        vignette_red(cv, 0.4 * (k - 0.7) / 0.3)
    badge(cv, 'THIRSTIER', y=-1040, col=RED, w=380)
    return cv


def b8_cycle(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    sea(cv, T, y0=250)
    toilet(cv, -170, -60, 0.8, swirl=lt, T=T, handle=min(1, lt * 2))
    pipe = [(-170, 30), (-170, 180), (100, 180), (240, 300)]
    line(cv, pipe, 40, STEEL, ow=4, flat=False)
    for q in range(5):
        u = (lt * 0.8 + q / 5) % 1
        seg = u * 3; i = min(int(seg), 2); f = seg - i
        x = pipe[i][0] + (pipe[i + 1][0] - pipe[i][0]) * f
        y = pipe[i][1] + (pipe[i + 1][1] - pipe[i][1]) * f
        disc(cv, x, y, 14, ramp('#ffe066'), ow=2)
    arrows(cv, [((300, 80), (300, -200)), ((330, -330), (-60, -420))], WHT, 14)
    label(cv, 'BACK TO THE SEA', 0, -620, 80, (127, 210, 255))
    return cv


BEATS = [b0_hook, b1_world, b2_normal, b3_years, b4_kidneys, b5_nonstop, b6_salt, b7_thirst, b8_cycle]

if __name__ == '__main__':
    run(BEATS)
