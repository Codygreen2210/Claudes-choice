#!/usr/bin/env python3
"""Clocks falling back. Opens on a wall clock spinning its hands backward; loops back into the spin."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

SCN = ramp('#ffd23f', '#d09a10', '#fff08a')


def head_side(cv, x, y, s, T, glow=0.0):
    """Big see-through head (front view) with the brain and the tiny clock spot in the middle."""
    cv.shape(smooth(60 * s, circle(x, y, 380 * s), capsule(x, y + 200 * s, x, y + 700 * s, 160 * s)), (x - 400 * s, y - 400 * s, x + 400 * s, y + 900 * s),
             ramp('#a8c8f0', '#6a8fb8', '#d8ecff'), ow=4, alpha=0.4)
    brain(cv, x, y - 40 * s, 1.35 * s)
    cx, cy = x, y + 120 * s
    cv.glow(circle(cx, cy, 22 * s), (cx - 120 * s, cy - 120 * s, cx + 120 * s, cy + 120 * s), '#ffd23f', 50 * s, 0.6 + 0.4 * glow)
    disc(cv, cx, cy, 22 * s, SCN, ow=3)
    for sx in (-1, 1):                                                      # the eyes
        disc(cv, x + sx * 130 * s, y + 210 * s, 46 * s, ramp('#ffffff'), ow=3, alpha=0.8)
        dot(cv, x + sx * 130 * s, y + 210 * s, 18 * s)
    return cx, cy


def b0_hook(lt, dur, T):
    """The hands are already spinning backward on frame one; before 0 they tick normally (the loop)."""
    spin = max(0.0, lt + 0.1) * 6.0 if lt > -0.1 else 0.0
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    m = (T * 0.4 if lt < -0.1 else -spin) * 2 * np.pi
    wall_clock(cv, 0, 0, 380, m / 12 + 2 * np.pi * (2 / 12), m)
    if lt >= 0:
        for j in range(3):
            a = -lt * 6 + j * 2.1
            arrows(cv, [((np.cos(a) * 470, np.sin(a) * 470), (np.cos(a - 0.4) * 470, np.sin(a - 0.4) * 470))], YEL, 12)
        hook_text(cv, '-1 HOUR', lt, y=-760, size=150, color=YEL)
    return cv


def b1_rice(lt, dur, T):
    z = 1.0 + 0.6 * ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(0, 120, z)
    sky_bg(cv)
    cx, cy = head_side(cv, 0, 0, 1.0, T)
    cv.shape(rotell(cx + 160, cy, 30, 12, 20), (cx + 120, cy - 30, cx + 200, cy + 30), ramp('#ffffff', '#e8e4d8', '#ffffff'), ow=3)
    label(cv, 'RICE', cx + 160, cy + 50, 30, WHT)
    label(cv, 'BODY CLOCK', cx, cy - 120, 50, YEL)
    return cv


def b2_runs(lt, dur, T):
    cv = Canvas(0, -300, 1.0)
    day = 0.5 + 0.5 * np.sin(lt * 1.6)
    cv.background('#3fa2ee' if day > 0.5 else '#1b2350', '#bfe6ff' if day > 0.5 else '#3a3f7a', vignette=0.2)
    box(cv, 0, 600, 1600, 600, ramp('#5fbf4a'), r=0, ow=0, shadow=0)
    if day > 0.5:
        sun(cv, 300, -1100, 110)
    else:
        moon(cv, 300, -1100, 100)
    guy(cv, -60, 0, 1.0, face='happy' if day > 0.5 else 'closed', arms=((150, 20), (150, 20)) if day > 0.5 else ((12, 0), (12, 0)))
    label(cv, 'WAKE UP' if day > 0.5 else 'GET SLEEPY', -60, -1150, 70, YEL if day > 0.5 else (190, 170, 255))
    return cv


def b3_light(lt, dur, T):
    cv = Canvas(0, 120, 1.2)
    sky_bg(cv)
    cx, cy = head_side(cv, 0, 0, 1.0, T, glow=0.5 + 0.5 * np.sin(lt * 4))
    sun(cv, -380, -450, 90)
    for j in range(6):
        ph = (lt * 1.4 + j / 6) % 1
        x0, y0 = -380, -450
        x1, y1 = -130, 210
        x, y = x0 + (x1 - x0) * ph, y0 + (y1 - y0) * ph
        disc(cv, x, y, 12, YELLOW, ow=0, alpha=1 - ph * 0.3)
    for j in range(6):
        ph = (lt * 1.4 + j / 6) % 1
        disc(cv, -130 + (cx - -130) * ph, 210 + (cy - 210) * ph, 9, YELLOW, ow=0, alpha=0.8)
    return cv


def b4_wrong(lt, dur, T):
    cv = Canvas(0, -300, 1.0)
    cv.background('#1b2350', '#ff9a5a', vignette=0.25)
    sun(cv, 260, -700, 110, a=ease(np.clip(lt / 0.8, 0, 1)))
    wall_clock(cv, -260, -1000, 150, 2 * np.pi * 5 / 12, 0)
    guy(cv, 0, 0, 1.0, face='shock', arms=((40, 100), (40, 100)))
    label(cv, 'TOO EARLY', -260, -800, 54, RED)
    return cv


def b5_melatonin(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1b2350', '#3a3f7a', vignette=0.25)
    wall_clock(cv, -260, -420, 170, 2 * np.pi * 9 / 12, 0)
    wall_clock(cv, 260, -420, 170, 2 * np.pi * 10 / 12, 0, col=ramp('#7a4fd0'))
    label(cv, 'CLOCK SAYS', -260, -650, 60, WHT)
    label(cv, 'BODY SAYS', 260, -650, 60, (190, 170, 255))
    for j in range(10):
        ph = (lt * 0.8 + j / 10) % 1
        disc(cv, 260 + 120 * np.sin(j * 1.7), 300 - ph * 400, 14, ramp('#b9a8ff'), ow=2, alpha=1 - ph)
    label(cv, 'MELATONIN', 260, -80, 56, (190, 170, 255))
    return cv


def b6_days(lt, dur, T):
    cv = Canvas(0, -300, 1.0)
    sky_bg(cv, ground=0)
    k = np.clip(lt / (dur * 0.85), 0, 1)
    guy(cv, -200, 0, 0.95, face='worried' if k < 0.8 else 'happy', arms=((12, 0), (12, 0)))
    for d in range(4):
        on = d < int(k * 4.99)
        box(cv, 200 + (d % 2) * 180, -900 + (d // 2) * 200, 75, 75, ramp('#ffffff', '#d8dde4', '#ffffff') if on else ramp('#8a90c0'), r=14)
        label(cv, f'DAY {d + 1}', 200 + (d % 2) * 180, -890 + (d // 2) * 200, 30, (40, 40, 50) if on else WHT)
    meter(cv, -200, -950, 340, k, GREEN, 'CATCHING UP')
    return cv


def b7_heart(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    beat = max(0, np.sin(lt * 9))
    heart_icon(cv, 0, 60, 1.3, beat)
    badge(cv, 'MONDAY', y=-520, col=RED)
    arrows(cv, [((340, 260), (340, -40))], RED, 16)
    label(cv, 'SPRING', -330, -330, 60, (120, 255, 140))
    return cv


def b8_dark(lt, dur, T):
    d = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, -300, 1.0)
    cv.background('#3fa2ee' if d < 0.5 else '#1b2350', '#ff9a5a' if d < 0.5 else '#3a3f7a', vignette=0.25)
    box(cv, 0, 600, 1600, 600, ramp('#5fbf4a') if d < 0.5 else ramp('#2f6a3a'), r=0, ow=0, shadow=0)
    sun(cv, 380, -700 + 600 * d, 100, a=1 - d)
    wall_clock(cv, -330, -1050, 130, 2 * np.pi * 5 / 12, np.pi)
    guy(cv, 0, 0, 1.0, face='worried', arms=((12, 0), (12, 0)), shirt=BLUE)
    label(cv, '5:30 PM', -330, -880, 46, WHT)
    return cv


BEATS = [b0_hook, b1_rice, b2_runs, b3_light, b4_wrong, b5_melatonin, b6_days, b7_heart, b8_dark]

if __name__ == '__main__':
    run(BEATS)
