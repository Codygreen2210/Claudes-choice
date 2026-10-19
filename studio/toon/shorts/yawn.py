#!/usr/bin/env python3
"""Yawning. Opens mid-yawn, mouth stretching wide; loops back into the yawn."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403


def yk(t, t0=0.0, up=0.7, hold=0.8, down=0.6):
    """Yawn curve: opens, holds, closes."""
    u = t - t0
    if u < 0:
        return 0.0
    if u < up:
        return ease(u / up)
    if u < up + hold:
        return 1.0
    return 1 - ease((u - up - hold) / down)


def air_in(cv, lt, x, y, a=1.0, n=10, spread=260, col='#bfeaff'):
    for k in range(n):
        ph = (lt * 1.6 + k / n) % 1
        sx = x + (k - n / 2) / n * spread * (1 - ph)
        disc(cv, sx, y - 260 * (1 - ph), 12, ramp(col, '#7fd0ff', '#ffffff'), ow=2, alpha=a * (1 - ph * 0.6))


def b0_hook(lt, dur, T):
    """Already opening into the yawn on frame one; before 0, the eyes get heavy (the loop)."""
    k = yk(lt, -0.35, 0.8, 1.0, 0.7)
    cv = Canvas(0, -620, 1.9)
    sky_bg(cv, ground=0)
    yawn_guy(cv, 0, 0, 1.0, k)
    if lt >= 0:
        air_in(cv, lt, 0, -702, a=k)
        hook_text(cv, 'YAWN', lt, y=-780, size=160, color=YEL)
    return cv


def b1_jaw(lt, dur, T):
    k = yk(lt, 0.1, 0.9, 1.2, 0.8)
    cv = Canvas(0, -700, 2.6)
    sky_bg(cv, ground=0)
    yawn_guy(cv, 0, 0, 1.0, k, stretch=False)
    air_in(cv, lt, 0, -702, a=k, n=14, spread=320)
    if k > 0.6:
        arrows(cv, [((-150, -780), (-150, -640)), ((150, -780), (150, -640))], YEL, 8)
    return cv


def b2_air(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=700)
    box(cv, 260, 150, 260, 180, ramp('#2b4a3a', '#1a3026', '#3d6650'), r=20)          # chalkboard
    label(cv, 'MORE AIR?', 260, 160, 70, WHT)
    guy(cv, -220, 700, 0.95, face='calm', coat=True, shirt=ramp('#f4f1ea'), arms=((40, 90), (60, 20)), glasses=True)
    for k in range(5):
        ph = (lt * 0.7 + k / 5) % 1
        disc(cv, -400 + k * 60, 200 - ph * 300, 26, ramp('#bfeaff', '#7fd0ff', '#ffffff'), ow=3, alpha=1 - ph)
        label(cv, 'O2', -400 + k * 60, 205 - ph * 300, 26, (40, 90, 140), a=1 - ph)
    return cv


def b3_mask(lt, dur, T):
    k = yk(lt, dur * 0.35, 0.6, 0.8, 0.5)
    cv = Canvas(0, -300, 1.15)
    sky_bg(cv, ground=0)
    box(cv, 330, -260, 90, 260, ramp('#3fbf6a', '#25804a', '#7fe8a0'), r=80)              # oxygen tank
    box(cv, 330, -540, 40, 30, STEEL, r=10)
    line(cv, [(330, -560), (250, -640), (60, -690)], 14, ramp('#dfe6ec'), ow=3, flat=False)
    yawn_guy(cv, 0, 0, 1.0, k, stretch=False)
    cv.shape(rotell(0, -700, 70, 50, 0), (-80, -760, 80, -640), ramp('#bfeaff', '#7fb6d9', '#eaf7ff'), ow=3, alpha=0.6)
    if lt > dur * 0.55:
        hook_text(cv, 'NO CHANGE', lt, y=-760, size=120, pop_t=dur * 0.55, color=RED)
    return cv


def b4_cool(lt, dur, T):
    h = 1 - ease(np.clip((lt - 0.4) / (dur * 0.6), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    brain(cv, -80, -60, 1.5, hot=0.7 * h)
    if h < 0.9:
        cv.glow(circle(-80, -60, 250), (-500, -450, 400, 350), '#4fb0ff', 40, 0.22 * (1 - h))
    else:
        for k in range(6):
            ph = (lt * 1.5 + k / 6) % 1
            line(cv, [(-280 + k * 80, -330 - ph * 160), (-260 + k * 80, -380 - ph * 160)], 8, flat(hexc('#ff8a5a')), a=1 - ph)
    thermo(cv, 400, 80, 104 - 8 * (1 - h), lo=90, hi=106, h=560)
    hook_text(cv, 'COOLS YOUR BRAIN', lt, y=-760, size=96, pop_t=dur * 0.45, color=(127, 210, 255))
    return cv


def b5_flow(lt, dur, T):
    k = yk(lt, 0.0, 0.6, dur - 1.2, 0.6)
    cv = Canvas(0, -650, 1.7)
    sky_bg(cv, ground=0)
    yawn_guy(cv, 0, 0, 1.0, k, stretch=False, tint=None)
    air_in(cv, lt, 0, -702, a=k, n=10)
    for j in range(8):                                                                    # warm blood draining down the neck
        ph = (lt * 1.2 + j / 8) % 1
        disc(cv, (-30 if j % 2 else 30), -760 + ph * 240, 10, ramp('#ff6a5a', '#c43a2a', '#ffa090'), ow=2, alpha=1 - ph)
    label(cv, 'COOL IN', -210, -880, 40, (127, 210, 255))
    label(cv, 'HOT OUT', 210, -560, 40, RED)
    return cv


def b6_hot(lt, dur, T):
    cv = Canvas(0, -300, 1.1)
    sky_bg(cv, ground=0, gcol='#e0c060')
    sun_r = 130 + 8 * np.sin(lt * 4)
    cv.glow(circle(330, -1000, sun_r), (100, -1250, 560, -750), '#ffd23f', 80, 0.9)
    disc(cv, 330, -1000, sun_r, YELLOW)
    guy(cv, -60, 0, 1.0, face='worried', arms=((12, 0), (12, 0)))
    for j in range(4):
        ph = (lt * 1.1 + j / 4) % 1
        drop(cv, -60 + (-90 if j % 2 else 90), -780 + ph * 140, 12, a=1 - ph)
    badge(cv, 'LESS YAWNS', y=-1250, col=YEL)
    return cv


def b7_spread(lt, dur, T):
    cv = Canvas(0, -330, 0.85)
    sky_bg(cv, ground=0)
    for j, x in enumerate((-380, 0, 380)):
        k = yk(lt, 0.2 + j * 0.9, 0.5, 0.6, 0.5)
        yawn_guy(cv, x, 0, 0.82, k, shirt=[SHIRT, ORANGE, BLUE][j])
    hook_text(cv, 'IT SPREADS', lt, y=-760, size=120, pop_t=1.1, color=YEL)
    return cv


def b8_dog(lt, dur, T):
    cv = Canvas(0, -300, 1.15)
    sky_bg(cv, ground=0)
    yawn_guy(cv, -260, 0, 0.9, yk(lt, 0.1, 0.5, 0.7, 0.5))
    dog(cv, 220, 0, 0.9, yawn=yk(lt, 1.3, 0.5, 0.8, 0.5), T=T)
    return cv


BEATS = [b0_hook, b1_jaw, b2_air, b3_mask, b4_cool, b5_flow, b6_hot, b7_spread, b8_dog]

if __name__ == '__main__':
    run(BEATS)
