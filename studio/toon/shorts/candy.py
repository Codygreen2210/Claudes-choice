#!/usr/bin/env python3
"""Halloween candy. Opens on a bag of candy pouring out at the camera; loops back into the pour."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

NIGHT = ('#2a1f4a', '#ff8a3a')
PANC = ramp('#f4b880', '#c8885a', '#ffd8b0')


def halloween_bg(cv):
    cv.background(*NIGHT, vignette=0.25)


def pumpkin_bag(cv, x, y, s):
    cv.shape(smooth(30 * s, circle(x - 90 * s, y, 150 * s), circle(x + 90 * s, y, 150 * s), circle(x, y - 10 * s, 170 * s)), (x - 260 * s, y - 190 * s, x + 260 * s, y + 170 * s), ORANGE)
    line(cv, [(x - 150 * s, y - 120 * s), (x, y - 330 * s), (x + 150 * s, y - 120 * s)], 16 * s, DARK, ow=3, flat=False)
    for sx in (-1, 1):
        cv.shape(poly([(x + sx * 90 * s, y - 50 * s), (x + sx * 40 * s, y - 50 * s), (x + sx * 65 * s, y - 100 * s)]), (x - 150 * s, y - 110 * s, x + 150 * s, y - 40 * s), DARK, ow=0)
    line(cv, [(x - 100 * s, y + 60 * s), (x - 50 * s, y + 90 * s), (x, y + 60 * s), (x + 50 * s, y + 90 * s), (x + 100 * s, y + 60 * s)], 14 * s, DARK)


def b0_hook(lt, dur, T):
    """The candy is already pouring out at us on frame one; before 0 the bag tips (the loop)."""
    tip = ease(np.clip((lt + 0.6) / 0.6, 0, 1))
    cv = Canvas(0, 0, 1.0)
    halloween_bg(cv)
    pumpkin_bag(cv, 0, -350 + 60 * tip, 1.1)
    if lt >= -0.1:
        for j in range(18):
            ph = ((lt + 0.1) * 0.9 + j / 18) % 1
            rng = np.random.default_rng(j)
            x = rng.uniform(-250, 250) * (0.4 + ph)
            y = -200 + ph * 1200
            candy(cv, x, y, 0.6 + 0.9 * ph, kind=j, rot=j * 40 + lt * 200)
    if lt >= 0:
        hook_text(cv, 'SUGAR', lt, y=-780, size=170, color=(255, 138, 42))
    return cv


def b1_blood(lt, dur, T):
    cv = Canvas(0, 0, 1.4)
    sky_bg(cv)
    vessel(cv, 0)
    n = int(6 + 30 * ease(np.clip(lt / (dur * 0.8), 0, 1)))
    rng = np.random.default_rng(3)
    for j in range(n):
        x = -800 + ((lt * 300 + rng.uniform(0, 1600)) % 1600)
        sugar_cube(cv, x, rng.uniform(-90, 90), 1.0)
    for j in range(5):
        x = -800 + ((lt * 260 + j * 330) % 1600)
        cv.shape(rotell(x, 40 * np.sin(j), 50, 22, 0), (x - 60, -40, x + 60, 60), ramp('#e2483d'), ow=3)
    badge(cv, 'MINUTES', y=-330)
    return cv


def b2_insulin(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    cv.shape(smooth(40, capsule(-300, 60, 260, -40, 110, 60), circle(-320, 80, 140)), (-480, -180, 400, 260), PANC)
    label(cv, 'PANCREAS', -40, 300, 70, WHT)
    sh = 6 * np.sin(lt * 40) if lt > 0.3 else 0
    for j in range(12):
        ph = (lt * 1.6 + j / 12) % 1
        a = -1.2 + j * 0.2
        x, y = -40 + sh + np.cos(a) * (120 + 520 * ph), -60 + np.sin(a) * (120 + 520 * ph)
        line(cv, [(x - 18, y), (x + 18, y)], 12, INSUL, ow=2.5, flat=False)
        disc(cv, x - 22, y, 14, INSUL, ow=2.5)
    hook_text(cv, 'INSULIN', lt, y=-720, size=140, pop_t=0.5, color=(79, 192, 255))
    return cv


def b3_shove(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for j, (x, y) in enumerate(((-260, -280), (260, -280), (-260, 300), (260, 300))):
        k = np.clip((lt - j * 0.3) / 0.6, 0, 1)
        cell(cv, x, y, 190, T, door=1.0, fill=int(6 * k), seed=j)
        for q in range(3):
            u = ((lt * 1.5 + q / 3 + j * 0.2) % 1)
            sugar_cube(cv, x - 420 + 220 * u, y + (q - 1) * 40, 1.0, a=1 - u * 0.3)
    return cv


def b4_fat(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, -300, 1.05)
    sky_bg(cv, ground=0)
    guy(cv, 0, 0, 1.0, face='worried', arms=((12, 0), (12, 0)))
    cv.shape(rotell(0, -470, 130 + 50 * k, 80 + 30 * k, 0), (-200, -580, 200, -360), FATC, alpha=0.8)
    for j in range(6):
        ph = (lt * 0.8 + j / 6) % 1
        sugar_cube(cv, -300 + 300 * ph, -800 + 330 * ph, 1.0, a=1 - ph)
    label(cv, 'STORED AS FAT', 0, -1120, 70, (255, 233, 168))
    return cv


def b5_myth(lt, dur, T):
    st = ease(np.clip((lt - dur * 0.5) / 0.12, 0, 1))
    cv = Canvas(0, -300, 1.05)
    sky_bg(cv, ground=0)
    guy(cv, 0, 0, 0.85, face='calm', arms=((12, 0), (12, 0)), shirt=ORANGE)
    label(cv, 'SUGAR RUSH', 0, -1100, 110, (255, 138, 42))
    if st > 0:
        sc = 1 + 0.5 * (1 - st)
        cv.shape(rbox(0, -1090, 380 * sc, 90 * sc, 20), (-420 * sc, -1200, 420 * sc, -980), ramp('#e2483d'), ow=5, alpha=0.92 * st)
        label(cv, 'MYTH', 0, -1075, 140 * sc, WHT, a=st)
    return cv


def b6_parents(lt, dur, T):
    cv = Canvas(0, -300, 1.0)
    sky_bg(cv, ground=0)
    guy(cv, -260, 0, 1.0, face='worried', arms=((40, 100), (12, 0)), woman=True, shirt=PINK)
    guy(cv, 240, 0, 0.6, face='calm', shirt=ORANGE, arms=((12, 0), (12, 0)))
    cloud(cv, -260, -1000, 180)
    for q in range(4):
        a = q * 1.6 + lt * 5
        guy(cv, -260 + np.cos(a) * 80, -950 + np.sin(a) * 30, 0.15, face='happy', shirt=ORANGE, arms=((150, 20), (150, 20)))
    label(cv, 'TOLD: SUGAR', -260, -760, 50, YEL)
    return cv


def b7_teeth(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    tooth(cv, 0, 150, 1.2, weak=ease(np.clip(lt / dur, 0, 1)))
    for j in range(5):
        a = j * 1.25 + lt * 2
        germ(cv, np.cos(a) * 330, -150 + np.sin(a) * 120, 44, T, seed=j, angry=False)
    acid_drops(cv, lt, 0, 0, 500)
    hook_text(cv, 'PARTY', lt, y=-720, size=150, pop_t=0.4, color=(155, 225, 93))
    return cv


def b8_week(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    halloween_bg(cv)
    pumpkin_bag(cv, -200, 200, 0.8)
    n = int(np.clip(lt / (dur * 0.7), 0, 1) * 7)
    for d in range(7):
        x = -330 + (d % 4) * 220 - (0 if d < 4 else -110)
        y = -500 + (d // 4) * 240
        box(cv, x, y, 90, 90, ramp('#ffffff', '#d8dde4', '#ffffff') if d < n else ramp('#3a3f7a'), r=14)
        if d < n:
            for q in range(3):
                sugar_cube(cv, x - 40 + q * 40, y + 10, 0.8)
    label(cv, '1 WEEK OF SUGAR', 0, -720, 80, YEL)
    return cv


BEATS = [b0_hook, b1_blood, b2_insulin, b3_shove, b4_fat, b5_myth, b6_parents, b7_teeth, b8_week]

if __name__ == '__main__':
    run(BEATS)
