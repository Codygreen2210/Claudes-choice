#!/usr/bin/env python3
"""Turkey and sleepiness. Opens on a guy slumping onto the couch, stuffed; loops back into the slump."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

COUCH = ramp('#a8693a', '#6e4122', '#d08f58')
TRYP = ramp('#b9a8ff', '#7a4fd0', '#e0d8ff')


def couch(cv, x, y, s=1.0):
    box(cv, x, y - 140 * s, 520 * s, 200 * s, COUCH, r=60 * s)
    box(cv, x, y + 40 * s, 560 * s, 110 * s, COUCH, r=50 * s)
    for sx in (-1, 1):
        box(cv, x + sx * 520 * s, y - 40 * s, 70 * s, 190 * s, COUCH, r=40 * s)


def b0_hook(lt, dur, T):
    """He's already flopping onto the couch on frame one; before 0 he staggers in (the loop)."""
    u = ease(np.clip((lt + 0.6) / 0.9, 0, 1))
    cv = Canvas(0, -260, 1.0)
    sky_bg(cv, ground=200, gcol='#c8a878')
    couch(cv, 0, 100)
    sink = 260 * u
    guy(cv, -40 + 40 * u, sink - 40, 1.0, face='closed' if u > 0.7 else 'worried', arms=((60 * u, 20), (60 * u, 20)), legs=u < 0.8, ground=False)
    cv.shape(rotell(-40 + 40 * u, sink - 480, 170, 120, 0), (-260, sink - 620, 180, sink - 340), ramp('#24b3a3', '#147a77', '#5fe0cc'), ow=4)   # stuffed belly
    if lt >= 0:
        for j in range(3):
            ph = (lt * 0.7 + j / 3) % 1
            label(cv, 'Z', 200 + 40 * j, -600 - 200 * ph, 50 + 20 * j, WHT, a=1 - ph)
        hook_text(cv, 'FOOD COMA', lt, y=-780, size=150, color=(255, 138, 42))
    return cv


def b1_tryp(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    roast_turkey(cv, 0, 300, 1.0, T)
    for j in range(8):
        ph = (lt * 0.9 + j / 8) % 1
        a = j * 0.8
        x, y = np.cos(a) * 120 * (1 - ph), 200 - ph * 700
        cv.shape(rotell(x, y, 22, 14, j * 30), (x - 30, y - 30, x + 30, y + 30), TRYP, ow=2.5, alpha=1 - ph * 0.5)
    label(cv, 'TRYPTOPHAN', 0, -520, 90, (185, 168, 255))
    return cv


def b2_blame(lt, dur, T):
    cv = Canvas(0, -260, 1.0)
    sky_bg(cv, ground=200, gcol='#c8a878')
    roast_turkey(cv, 220, 0, 0.7, T)
    for j, x in enumerate((-380, -150)):
        guy(cv, x, 200, 0.75, face='worried', shirt=[ORANGE, BLUE][j], arms=((20, 0), (95, 0)))
    arrows(cv, [((-60, -380), (90, -200))], RED, 14)
    hook_text(cv, 'BLAME IT', lt, y=-760, size=140, pop_t=0.4, color=RED)
    return cv


def b3_same(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    items = [('TURKEY', ROAST), ('CHICKEN', ramp('#f0c070', '#c0904a', '#ffe0a0')), ('BEEF', ramp('#a8443a', '#6e2622', '#d0706a')), ('CHEESE', ramp('#ffd23f'))]
    for j, (nm, col) in enumerate(items):
        u = ease(np.clip((lt - j * 0.35) / 0.4, 0, 1))
        x = -330 + (j % 2) * 660 if False else -390 + j * 260
        cv.shape(rotell(x, 0, 100 * u + 1, 70 * u + 1, 0), (x - 110, -80, x + 110, 80), col)
        meter(cv, x, 260, 180, 0.62 * u, TRYP, nm, a=u)
    label(cv, 'SAME AMOUNT', 0, -420, 90, (185, 168, 255))
    return cv


def b4_fight(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    box(cv, 0, -350, 600, 40, ramp('#8a5a2a'), r=10)                         # the brain's gate
    brain(cv, 0, -620, 0.9)
    for j in range(16):
        ph = (lt * 0.8 + j / 16) % 1
        x = -500 + (j % 8) * 140 + 20 * np.sin(lt * 3 + j)
        y = 400 - ph * 700
        col = TRYP if j % 5 == 0 else ramp(['#7fd34f', '#ff8a2a', '#3d7fd8', '#e2483d'][j % 4])
        if y < -320 and j % 5 != 0:
            y = -320 + 20 * np.sin(j)
        cv.shape(rotell(x, y, 22, 14, j * 30), (x - 30, y - 30, x + 30, y + 30), col, ow=2.5)
    label(cv, 'CROWDED OUT', 0, 560, 70, WHT)
    return cv


def b5_pile(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for j in range(int(1 + 4 * k)):
        plate(cv, 0, 360 - j * 110, 0.9, items=1.0, T=T)
    hook_text(cv, 'THE REAL REASON', lt, y=-760, size=110, pop_t=dur * 0.4, color=(255, 138, 42))
    return cv


def b6_digest(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(0, -400, 1.2)
    sky_bg(cv, ground=0)
    guy(cv, 0, 0, 1.0, face='closed' if k > 0.6 else 'calm', arms=((12, 0), (12, 0)))
    inn = stomach(cv, 0, -470, 0.35 + 0.15 * k, T, acid=0.6)
    meter(cv, 0, -1020, 360, k, ramp('#b9a8ff'), 'REST AND DIGEST')
    return cv


def b7_combo(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for j, (nm, col) in enumerate((('PIE', ramp('#e0a050')), ('LONG DAY', ramp('#7a4fd0')), ('WARM HOUSE', ramp('#ff8a2a')))):
        u = ease(np.clip((lt - j * dur * 0.25) / 0.4, 0, 1))
        y = -300 + j * 280
        box(cv, 0, y, 280 * u + 1, 90 * u + 1, col, r=40)
        label(cv, nm, 0, y + 15, 70, WHT, a=u)
    return cv


def b8_cal(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    plate(cv, 0, 300, 1.1, items=1.0, T=T)
    roast_turkey(cv, 0, -120, 0.6, T)
    n = int(3000 * ease(np.clip(lt / (dur * 0.8), 0, 1)))
    badge(cv, f'{n:,} CAL', y=-560, col=(255, 138, 42), w=420)
    return cv


BEATS = [b0_hook, b1_tryp, b2_blame, b3_same, b4_fight, b5_pile, b6_digest, b7_combo, b8_cal]

if __name__ == '__main__':
    run(BEATS)
