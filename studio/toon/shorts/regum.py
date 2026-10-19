#!/usr/bin/env python3
"""Remineralizing gum. Opens on a stick of gum diving into a chewing mouth; loops back into it."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

MINT = ramp('#7fe8c8', '#3fb898', '#c4fff0')


def chew_face(cv, lt, x=0, y=0, s=1.0, chew=1.0, gum_in=1.0):
    """Close-up of a mouth chewing: jaw bobbing, cheeks puffing."""
    j = 0.5 + 0.5 * np.sin(lt * 9) if chew > 0 else 0.0
    s = s * 1.9
    cv.shape(rbox(x, y, 1600, 1800, 400), (x - 1600, y - 1800, x + 1600, y + 1800), SKIN, ow=0, shadow=0)
    cv.shape(smooth(30 * s, capsule(x, y - 330 * s, x, y - 200 * s, 50 * s), circle(x - 45 * s, y - 190 * s, 40 * s), circle(x + 45 * s, y - 190 * s, 40 * s)),
             (x - 100 * s, y - 400 * s, x + 100 * s, y - 140 * s), SKIN)                              # nose
    for sx in (-1, 1):
        cv.shape(rotell(x + sx * 330 * s, y + 40 * s, 170 * s * (1 + 0.06 * j), 150 * s, 0), (x + sx * 330 * s - 200 * s, y - 160 * s, x + sx * 330 * s + 200 * s, y + 240 * s),
                 ramp('#f7a88c', '#d07a62', '#ffd0bd'), ow=0, alpha=0.6)
    my = y + 40 * s + 30 * s * j
    cv.shape(ellipse(x, my, 250 * s, (70 + 70 * j) * s), (x - 270 * s, my - 160 * s, x + 270 * s, my + 160 * s), ramp('#d0606a', '#a03a4a', '#f08a90'), ow=5)   # lips
    cv.shape(ellipse(x, my, 215 * s, (45 + 60 * j) * s), (x - 240 * s, my - 130 * s, x + 240 * s, my + 130 * s), ramp('#5a1f2a'), ow=3)
    for sx in (-1, 0, 1):
        box(cv, x + sx * 70 * s, my - (40 + 60 * j) * s + 18 * s, 32 * s, 22 * s, ENAMEL, r=8 * s, ow=3, shadow=0)
    if gum_in > 0:
        disc(cv, x + 40 * s, my + 10 * s, 40 * s, MINT, ow=3, alpha=gum_in)


def b0_hook(lt, dur, T):
    """The gum stick is flying in on frame one; before 0 the mouth opens (the loop)."""
    u = ease(np.clip((lt + 0.5) / 0.7, 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    chew_face(cv, lt, chew=1.0 if lt > 0.3 else 0.0, gum_in=1.0 if lt > 0.25 else 0.0)
    if u < 1:
        gx, gy = 420 - 380 * u, -520 + 560 * u
        cv.shape(rbox(gx, gy, 110, 34, 10), (gx - 120, gy - 40, gx + 120, gy + 40), MINT, ow=4)
        speed_lines(cv, T, 0.5)
    if lt >= 0:
        hook_text(cv, 'REBUILD', lt, y=-760, size=160, color=(127, 232, 200))
    return cv


def b1_acid(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    tooth(cv, 0, 150, 1.2)
    for j in range(5):
        germ(cv, -330 + j * 165, -200 + 30 * np.sin(lt * 3 + j), 40, T, seed=j)
    acid_drops(cv, lt, 0, 0, 600, n=12)
    label(cv, 'ACID', 0, -560, 100, (155, 225, 93))
    return cv


def b2_weak(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(0, -100, 1.5)
    sky_bg(cv)
    tooth(cv, 0, 150, 1.2, weak=k)
    for j in range(8):                                                     # minerals leaving
        ph = (lt * 0.9 + j / 8) % 1
        disc(cv, -200 + j * 55, -100 - ph * 300, 12, CALC, ow=2, alpha=1 - ph)
    label(cv, 'WEAK SPOTS', 0, -470, 70, YEL)
    return cv


def b3_spit(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    chew_face(cv, lt)
    for j in range(14):
        ph = (lt * 1.4 + j / 14) % 1
        a = j * 0.45
        disc(cv, np.cos(a) * (120 + 260 * ph), 60 + np.sin(a) * (60 + 160 * ph), 14, SPIT, ow=2, alpha=1 - ph)
    badge(cv, 'MORE SPIT', y=-560, col=(127, 210, 255))
    return cv


def b4_wash(lt, dur, T):
    cv = Canvas(0, -60, 1.2)
    sky_bg(cv)
    tooth(cv, 0, 150, 1.2, weak=1.0)
    f, bb = wave_surface(-80 + 10 * np.sin(lt * 2), 18, 0.02, T * 3, x0=-700, x1=700, y1=900)
    cv.shape(f, bb, SPIT, ow=4, shadow=0, alpha=0.45)
    for j in range(12):
        ph = (lt * 0.7 + j / 12) % 1
        disc(cv, -500 + j * 90, 300 - ph * 300, 14, CALC, ow=2)
    label(cv, 'CALCIUM', 0, -520, 80, WHT)
    return cv


def b5_refill(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, -100, 1.5)
    sky_bg(cv)
    tooth(cv, 0, 150, 1.2, weak=1.0, refill=k)
    if k > 0.95:
        sparkle_n = 6
        for j in range(sparkle_n):
            a = j * 1.05 + lt * 2
            disc(cv, np.cos(a) * 260, -100 + np.sin(a) * 120, 10, ramp('#ffffff'), ow=0, alpha=0.8)
    hook_text(cv, 'REBUILT', lt, y=-760, size=140, pop_t=dur * 0.6, color=(127, 232, 200))
    return cv


def b6_extra(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    cv.shape(rbox(0, 0, 260, 80, 24), (-270, -90, 270, 90), MINT)
    label(cv, 'GUM', 0, 15, 90, WHT)
    for j in range(12):
        a = j * 0.52 + lt
        r = 300 + 40 * np.sin(lt * 3 + j)
        disc(cv, np.cos(a) * r, np.sin(a) * r * 0.7, 16, CALC, ow=2)
    label(cv, '+ MINERALS', 0, -420, 80, YEL)
    return cv


def b7_hole(lt, dur, T):
    cv = Canvas(0, -100, 1.5)
    sky_bg(cv)
    tooth(cv, 0, 150, 1.2, hole=1.0)
    k = ease(np.clip((lt - dur * 0.4) / 0.2, 0, 1))
    if k > 0:
        line(cv, [(-260, -420), (260, 100)], 24, flat(hexc('#e2483d')), ow=4, a=k)
        line(cv, [(260, -420), (-260, 100)], 24, flat(hexc('#e2483d')), ow=4, a=k)
    hook_text(cv, "CAN'T FIX THIS", lt, y=-760, size=110, pop_t=dur * 0.4, color=RED)
    return cv


def b8_after(lt, dur, T):
    cv = Canvas(0, -300, 1.0)
    sky_bg(cv, ground=0)
    guy(cv, -200, 0, 0.95, face='happy', arms=((12, 0), (60, 110)))
    box(cv, 260, -150, 200, 20, ramp('#e8eef3'), r=10)                        # plate, done eating
    cv.shape(rbox(-90, -830, 50, 16, 6), (-140, -850, -40, -810), MINT, ow=3)
    box(cv, 260, -700, 26, 160, ramp('#3d7fd8'), r=14)                         # toothbrush
    box(cv, 260, -880, 40, 40, ramp('#ffffff'), r=10)
    label(cv, 'SUGAR FREE', -200, -1180, 64, (127, 232, 200))
    return cv


BEATS = [b0_hook, b1_acid, b2_weak, b3_spit, b4_wash, b5_refill, b6_extra, b7_hole, b8_after]

if __name__ == '__main__':
    run(BEATS)
