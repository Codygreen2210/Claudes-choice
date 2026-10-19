#!/usr/bin/env python3
"""Diarrhea. Opens on a guy sprinting for the bathroom, gut churning; loops back into the sprint."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403


def b0_hook(lt, dur, T):
    """Mid-sprint on frame one, a gurgle bubbling in his gut. Before 0: the run-up (the loop)."""
    x = -260 + 160 * np.tanh((lt + 1.2) / 1.5)
    bob = -abs(np.sin(lt * 9)) * 30
    cv = Canvas(0, -420, 1.25)
    sky_bg(cv, ground=0, gcol='#c8ccd4')
    box(cv, 330, -500, 150, 520, ramp('#a8693a', '#6e4122', '#d08f58'), r=16)            # bathroom door
    disc(cv, 220, -480, 22, YELLOW)
    label(cv, 'WC', 330, -880, 70, WHT)
    sw = np.sin(lt * 9)
    guy(cv, x, bob, 1.0, face='pain', arms=((35, 110), (35, 110)), shirt=ORANGE)
    for k in range(4):                                                                  # gurgle
        ph = (lt * 1.7 + k / 4) % 1
        disc(cv, x - 40 + k * 30, -470 - ph * 60, 10 + 8 * ph, ramp('#c8e6a0', '#8ab060', '#eaffd0'), ow=2, alpha=1 - ph)
    speed_lines(cv, T, 0.6, vertical=False)
    if lt >= 0:
        hook_text(cv, 'RUN', lt, y=-780, size=170, color=RED)
    return cv


def b1_crawl(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 0, rings=[-500 + ((lt * 120) % 1000)], ring_k=0.6)
    lump(cv, -300 + lt * 60, 0, 90, col=SLOP)
    badge(cv, 'HOURS', y=-360)
    return cv


def b2_soak(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 0)
    lump(cv, -60 + lt * 30, 0, 100 - 18 * k, col=POOP if k > 0.5 else SLOP, squish=-0.2 * k)
    for j in range(10):
        ph = (lt * 0.9 + j / 10) % 1
        sx = -1 if j % 2 else 1
        drop(cv, -360 + j * 80, sx * (40 + ph * 240), 14, a=1 - ph)
    label(cv, 'WATER OUT', 0, -300, 70, (127, 210, 255))
    return cv


def b3_germs(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 0)
    a = np.clip((lt - 0.4) / 0.4, 0, 1)
    for j in range(5):
        x = -700 + ((lt * 260 + j * 260) % 1400)
        germ(cv, x, 30 * np.sin(j * 2 + lt * 3), 52, T, seed=j)
    if a > 0:
        box(cv, 0, -190, 1000, 30, ramp('#ff4a3a'), r=14, ow=0, alpha=0.5 * a * (0.6 + 0.4 * np.sin(lt * 14)))
        box(cv, 0, 190, 1000, 30, ramp('#ff4a3a'), r=14, ow=0, alpha=0.5 * a * (0.6 + 0.4 * np.sin(lt * 14)))
        hook_text(cv, 'PANIC MODE', lt, y=-700, size=120, pop_t=0.5, color=RED)
    return cv


def b4_dump(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 0)
    lvl = 130 - 260 * k
    box(cv, 0, (lvl + 133) / 2, 990, max(1, (133 - lvl) / 2), WATERC, r=20, ow=0, shadow=0, alpha=0.7)
    for j in range(14):
        ph = (lt * 1.5 + j / 14) % 1
        sx = -1 if j % 2 else 1
        drop(cv, -620 + j * 95, sx * (190 - ph * 150), 14, a=1 - ph * 0.3)
    for j in range(4):
        germ(cv, -400 + j * 260 + lt * 160, lvl - 20 + 20 * np.sin(j + lt * 4), 42, T, seed=j)
    hook_text(cv, 'FLUSH', lt, y=-700, size=140, pop_t=dur * 0.4, color=(127, 210, 255))
    return cv


def b5_rush(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    rings = [-900 + ((lt * 900 + j * 450) % 1800) for j in range(4)]
    tube(cv, 0, rings=rings, ring_k=0.8)
    box(cv, 0, 0, 990, 120, WATERC, r=40, ow=0, shadow=0, alpha=0.55)
    for j in range(4):
        x = -900 + ((lt * 1100 + j * 450) % 1800)
        lump(cv, x, 0, 70, col=SLOP, squish=0.4)
    speed_lines(cv, T, 0.8, vertical=False)
    label(cv, 'FASTER', 0, -300, 80, YEL)
    return cv


def b6_out(lt, dur, T):
    cv = Canvas(0, 120, 1.0)
    sky_bg(cv, ground=500, gcol='#c8ccd4')
    toilet(cv, 0, 500, 1.1, swirl=0.0, T=T)
    k = np.clip((lt - 0.3) / 0.3, 0, 1)
    if k > 0:
        for j in range(26):
            ph = (lt * 2.2 + j / 26) % 1
            x = 20 * np.sin(j * 1.7)
            disc(cv, x, -420 + ph * 640 * k, 16 + 6 * (j % 3), SLOP, ow=2.5, alpha=0.95)
        for j in range(8):
            ph = (lt * 2 + j / 8) % 1
            a = np.radians(200 + j * 18)
            disc(cv, np.cos(a) * 200 * ph, 270 + np.sin(a) * 120 * ph, 10, SLOP, ow=2, alpha=1 - ph)
    hook_text(cv, 'OUT IT COMES', lt, y=-720, size=120, pop_t=dur * 0.35, color=(200, 140, 70))
    return cv


def b7_dry(lt, dur, T):
    cv = Canvas(0, -320, 1.15)
    sky_bg(cv, ground=0)
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    guy(cv, -100, 0, 1.0, face='worried' if k < 0.9 else 'calm', arms=((12, 0), (160, 30)))
    box(cv, 120, -860, 40, 110, ramp('#bfeaff', '#7fb6d9', '#eaf7ff'), r=24, alpha=0.9)
    meter(cv, 0, -1000, 600, 0.25 + 0.6 * k, ramp('#3fa9e0', '#2378b0', '#8fd6ff'), 'WATER')
    return cv


def b8_button(lt, dur, T):
    press = ease(np.clip((lt - 0.6) / 0.2, 0, 1))
    cv = Canvas(0, 60, 1.1)
    sky_bg(cv, ground=500, gcol='#c8ccd4')
    toilet(cv, 0, 500, 1.1, swirl=press, T=T, handle=press)
    hook_text(cv, 'FLUSH', lt, y=-720, size=150, pop_t=0.7, color=(127, 210, 255))
    return cv


BEATS = [b0_hook, b1_crawl, b2_soak, b3_germs, b4_dump, b5_rush, b6_out, b7_dry, b8_button]

if __name__ == '__main__':
    run(BEATS)
