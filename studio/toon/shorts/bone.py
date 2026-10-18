#!/usr/bin/env python3
"""How Your Bones Heal After a Break. Opens on a see-through leg; the shin bone bends and snaps."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

BONE = ramp('#f4ecd8', '#cbbf9e', '#ffffff')
CLOT = ramp('#b8202a', '#7a1018', '#e85060')
BRUISE = ramp('#7a4fd0', '#4f3292', '#a985ff')
SOFT = ramp('#7fc8ff', '#4f98d0', '#bfe6ff')
ROUGH = ramp('#e0d4b0', '#b0a080', '#f6eedc')
CAST = ramp('#f4f1ea', '#c9c3b8', '#ffffff')
CLEAN = ramp('#7fd34f', '#4f9a2a', '#b6f08a')
BREAK_Y = 0


def leg(cv, T, see=0.7, swell=0.0, bruise=0.0, cast=0.0):
    sky_bg(cv)
    w = 150 * (1 + 0.25 * swell)
    cv.shape(capsule(0, -900, 0, 900, 170, 140 + 100 * swell * 0.6), (-300, -1100, 300, 1100), SKIN, alpha=1 - see,
             tint=('#7a4fd0', 0.5 * bruise) if bruise else None)
    if see > 0:
        cv.shape(capsule(0, -900, 0, 900, 170, 140 + 100 * swell * 0.6), (-300, -1100, 300, 1100), ramp('#9fd8ff'), alpha=0.25 * see, ow=4, shadow=0)
    if cast > 0:
        cv.shape(capsule(0, -500, 0, 500, 200, 200), (-220, -720, 220, 720), CAST, alpha=cast)
        for y in range(-450, 451, 90):
            line(cv, [(-195, y), (195, y + 40)], 4, flat(hexc('#c9c3b8')), a=cast)


def bone(cv, gap=0.0, bend=0.0, lump=0.0, fill=None, fillc=SOFT, offset=0.0):
    """Shin bone in two halves split at BREAK_Y."""
    for sgn in (-1, 1):
        y0 = BREAK_Y + sgn * gap
        y1 = sgn * 850
        dx = bend * 30 * (1 if sgn < 0 else -1) + (offset if sgn > 0 else 0)
        f = smooth(20, capsule(dx, y0, 0, y1, 60, 60), circle(0, y1, 95))
        cv.shape(f, (-160, min(y0, y1) - 100, 160, max(y0, y1) + 100), BONE, bevel=50)
    if fill is not None and fill > 0:
        cv.shape(rotell(0, BREAK_Y, 80 + 60 * lump, 50 + 30 * lump, 0), (-150, -90, 150, 90), fillc, ow=4, alpha=fill)


def b0_hook(lt, dur, T):
    """The bone bends... SNAP. Before 0: bending (the loop)."""
    cv = Canvas(0, 0, 1.0)
    leg(cv, T)
    if lt < 0.12:
        b = np.clip((lt + 1.2) / 1.2, 0, 1)
        bone(cv, bend=b)
        if lt > -0.3:
            for k in range(3):
                line(cv, [(-40 + k * 30, -10), (-30 + k * 30, 10)], 5, flat(hexc('#e2483d')))
    else:
        g = ease(np.clip((lt - 0.12) / 0.2, 0, 1))
        bone(cv, gap=30 * g, offset=40 * g)
        specks(cv, T, lambda i, v, tt: ((v[0] - 0.5) * 300 * g, (v[1] - 0.5) * 200 * g, 1 - g * 0.5), 18, (244, 236, 216), 8, seed=7)
        hook_text(cv, 'SNAP', lt, y=-700, size=150, pop_t=0.12, color=(255, 90, 80))
    if 0.12 <= lt < 0.22:
        cv.flash('#ffffff', 0.4 * (1 - (lt - 0.12) / 0.1))
    return cv


def b1_clot(lt, dur, T):
    cv = Canvas(0, 0, 1.2)
    leg(cv, T)
    bone(cv, gap=30, offset=40, fill=ease(np.clip(lt / 0.8, 0, 1)), lump=0.8, fillc=CLOT)
    label(cv, 'CLOT', 260, 0, 90, (255, 90, 80))
    return cv


def b2_swell(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(0, 0, 1.0)
    leg(cv, T, see=0.0, swell=k, bruise=k)
    hook_text(cv, 'SWELLING', lt, y=-700, size=120, pop_t=dur * 0.4, color=(169, 133, 255))
    return cv


def b3_clean(lt, dur, T):
    cv = Canvas(0, 0, 1.3)
    leg(cv, T)
    bone(cv, gap=30, offset=40, fill=1 - 0.6 * lt / dur, lump=0.8, fillc=CLOT)
    rng = np.random.default_rng(4)
    for i in range(8):
        a = i * 0.8 + lt
        x, y = np.cos(a) * 120, np.sin(a) * 70
        disc(cv, x, y, 26, CLEAN, ow=3)
        dot(cv, x - 8, y - 4, 4); dot(cv, x + 8, y - 4, 4)
    label(cv, 'CLEANUP CREW', 0, -520, 70, (127, 211, 79))
    return cv


def b4_soft(lt, dur, T):
    cv = Canvas(0, 0, 1.3)
    leg(cv, T)
    bone(cv, gap=30, offset=40 * (1 - 0.6 * lt / dur), fill=ease(np.clip(lt / 0.8, 0, 1)), lump=1.0, fillc=SOFT)
    wob = 1 + 0.06 * np.sin(lt * 8)
    label(cv, 'SOFT BRIDGE', 0, -520, 76 * wob, (127, 200, 255))
    return cv


def b5_hard(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, 0, 1.3)
    leg(cv, T)
    bone(cv, gap=30, offset=16, fill=1.0, lump=1.0, fillc=SOFT if k < 0.5 else ROUGH)
    box(cv, 0, -520, 240, 85, DARK, r=26)
    label(cv, f'WEEK {1 + int(k * 4)}', 0, -510, 90, (255, 236, 80))
    return cv


def b6_cast(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    k = ease(np.clip(lt / 0.8, 0, 1))
    leg(cv, T, see=0.0, cast=k)
    label(cv, 'HOLD STILL', 0, -760, 90, (255, 255, 255))
    return cv


def b7_weeks(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=600)
    x = -400 + 800 * (lt / dur)
    step = abs(np.sin(lt * 6))
    guy(cv, x, 600, 0.7, face='happy', arms=((20 + 15 * step, 0), (20 + 15 * (1 - step), 0)))
    box(cv, 0, -560, 280, 85, DARK, r=26)
    label(cv, '6-8 WEEKS', 0, -550, 90, (120, 255, 140))
    return cv


def b8_reshape(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.85), 0, 1))
    cv = Canvas(0, 0, 1.3)
    leg(cv, T)
    bone(cv, gap=0, offset=0, fill=1.0, lump=1.0 - k, fillc=ROUGH)
    for i in range(3):
        a = lt * 5 + i * 2
        line(cv, [(110 + np.cos(a) * 20, np.sin(a) * 30), (170 + np.cos(a) * 20, np.sin(a) * 30)], 8, flat(hexc('#ffd23f')))
    box(cv, 0, -520, 280, 85, DARK, r=26)
    label(cv, f'MONTH {1 + int(k * 5)}', 0, -510, 90, (255, 236, 80))
    return cv


BEATS = [b0_hook, b1_clot, b2_swell, b3_clean, b4_soft, b5_hard, b6_cast, b7_weeks, b8_reshape]

if __name__ == '__main__':
    run(BEATS)
