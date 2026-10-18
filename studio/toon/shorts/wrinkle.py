#!/usr/bin/env python3
"""Why Your Fingers Wrinkle in Water. Opens on a whole hand bursting up out of bath water, the fingertips
wrinkling into tread on the way up."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

TIRE = ramp('#2b2b30', '#18181b', '#4a4a52')
TUB = ramp('#f4f1ea', '#c9c3b8', '#ffffff')
XRAY = ramp('#6a8fb0', '#3d5a78', '#a8c8e8')


def water(cv, y, T, a=1.0):
    f, bb = wave_surface(y, 16, 0.018, T * 3, x0=-1600, x1=1600, y1=3000)
    cv.shape(f, bb, ramp('#7fd0ff', '#3fa9e0', '#bfeaff'), ow=4, shadow=0, alpha=0.78 * a)


def splash(cv, lt, x, y, n=16, seed=3):
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = rng.uniform(-2.6, -0.5); v = rng.uniform(500, 1100)
        t = lt * 1.1
        px, py = x + np.cos(a) * v * t, y + np.sin(a) * v * t + 1400 * t * t
        r = rng.uniform(10, 22) * max(0, 1 - t)
        if r > 1:
            disc(cv, px, py, r, ramp('#bfeaff', '#7fd0ff', '#ffffff'), ow=2.5)


def drips(cv, T, tips, k=1.0):
    for j, (x, y) in enumerate(tips):
        ph = (T * 0.9 + j * 0.31) % 1
        disc(cv, x, y + 30 + ph * 300, 10 * (1 - ph * 0.5), ramp('#bfeaff', '#7fd0ff', '#ffffff'), ow=2, alpha=k * (1 - ph))


def b0_hook(lt, dur, T):
    """The hand bursts up out of the water and the tips wrinkle. Before 0: sinking back in (the loop)."""
    rise = ease(np.clip((lt + 0.9) / 1.0, 0, 1))
    cv = Canvas(0, 160, 1.0)
    sky_bg(cv)
    box(cv, 0, 700, 900, 260, TUB, r=120)                                  # tub rim behind the water
    y = 1500 - 820 * rise
    tips = hand(cv, 0, y, 1.0, wr=ease(np.clip((lt - 0.15) / 0.9, 0, 1)) if lt >= 0 else 0.0, spread=1.1)
    water(cv, 640, T)
    if lt >= 0:
        splash(cv, lt, 0, 620)
        drips(cv, T, [tips[k] for k in ('index', 'middle', 'ring', 'pinky')], 1 - lt / dur)
        hook_text(cv, 'RAIN TIRES', lt, y=-760, size=130, color=(255, 236, 80))
    return cv


def b1_myth(lt, dur, T):
    cv = Canvas(0, 180, 1.0)
    sky_bg(cv)
    puff = 0.5 + 0.5 * np.sin(lt * 5)
    hand(cv, 0, 760, 1.0 + 0.04 * puff, wr=0.0)
    for k in range(8):
        a = k * np.pi / 4 + lt * 0.8
        r0 = 470 + 40 * ((lt * 2 + k / 8) % 1)
        arrows(cv, [((np.cos(a) * r0, 200 + np.sin(a) * r0), (np.cos(a) * (r0 - 150), 200 + np.sin(a) * (r0 - 150)))], (140, 210, 255), 12)
    hook_text(cv, 'SOAKS UP WATER?', lt, y=-760, size=92, pop_t=0.2, color=(255, 255, 255))
    return cv


def b2_weird(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=700)
    box(cv, 300, 500, 220, 200, ramp('#e8eef3'), r=30)                     # lab bench
    for j, c in enumerate(('#7fe8a0', '#ff8f9a', '#7fb4ff')):
        box(cv, 180 + j * 110, 260 - 30 * j, 34, 90 + 20 * j, ramp(c), r=16)
    guy(cv, -180, 700, 0.95, face='shock', coat=True, shirt=ramp('#f4f1ea'), arms=((40, 90), (140, 30)), glasses=True)
    hook_text(cv, 'WAIT...', lt, y=-660, size=130, pop_t=0.3)
    return cv


def b3_nerve(lt, dur, T):
    cv = Canvas(0, 200, 1.0)
    sky_bg(cv)
    k = ease(np.clip((lt - 0.2) / (dur * 0.6), 0, 1))
    hand(cv, 0, 820, 1.05, wr={'middle': k, 'ring': k, 'pinky': k, 'thumb': k}, nerve='index', xray=0.25)
    label(cv, 'NERVE CUT', -300, -380, 64, (255, 90, 80))
    arrows(cv, [((-300, -330), (-170, -180))], (255, 90, 80), 12)
    if lt > dur * 0.55:
        hook_text(cv, 'NO WRINKLES', lt, y=-760, size=100, pop_t=dur * 0.55, color=(255, 255, 255))
    return cv


def b4_brain(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    brain(cv, 0, -560, 1.2, hot=0.3)
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    pts = [(0, -380), (40, -150), (140, 80), (190, 330), (190, 520)]
    n = max(2, int(k * len(pts) + 0.999))
    line(cv, pts[:n], 12, flat(hexc('#ffd23f')), ow=3)
    tip = pts[n - 1]
    cv.glow(circle(tip[0], tip[1], 20), (tip[0] - 60, tip[1] - 60, tip[0] + 60, tip[1] + 60), '#ffd23f', 40, 0.9)
    hand(cv, 190, 1020, 0.7, wr=k)
    hook_text(cv, 'ON PURPOSE', lt, y=-900, size=110, pop_t=dur * 0.45)
    return cv


def b5_vessels(lt, dur, T):
    """Zoomed into the hand: x-ray, the blood pipes squeeze thin."""
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    cv = Canvas(-20, 330, 1.55)
    sky_bg(cv)
    hand(cv, 0, 760, 1.0, xray=0.75, vessels=k, skin=XRAY)
    for sx in (-1, 1):
        arrows(cv, [((sx * 420, 120), (sx * 270, 120))], (255, 90, 80), 10)
    label(cv, 'SQUEEZE', 0, -150, 80, (255, 90, 80))
    return cv


def b6_grooves(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(-40, 200, 2.0)
    sky_bg(cv)
    hand(cv, 0, 760, 1.0 - 0.02 * k, wr=k)
    return cv


def b7_tire(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=420, gcol='#5a6070')
    for k in range(6):                                                      # wet road shine
        x = ((-lt * 900 + k * 260) % 1600) - 800
        box(cv, x, 440, 70, 6, ramp('#9ad8ff'), r=6, ow=0, shadow=0)
    disc(cv, 0, 80, 320, TIRE)
    disc(cv, 0, 80, 150, STEEL)
    a0 = T * 220
    for k in range(18):
        a = np.radians(a0 + k * 20)
        line(cv, [(np.cos(a) * 262, 80 + np.sin(a) * 262), (np.cos(a) * 316, 80 + np.sin(a) * 316)], 16, flat(hexc('#55555e')))
    specks(cv, T, lambda i, v, tt: (-260 - ((tt * 900 + v[0] * 600) % 600), 400 - v[1] * 260 * ((tt * 900 + v[0] * 600) % 600) / 600, 1.0),
           40, (160, 220, 255), 9, seed=4)
    label(cv, 'GROOVES MOVE WATER', 0, -560, 66, (255, 255, 255))
    return cv


def b8_marbles(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for sx in (-1, 1):
        cv.shape(inter(circle(sx * 300, 200, 200), lambda X, Y: 200 - Y), (sx * 300 - 210, 0, sx * 300 + 210, 210), ramp('#e8eef3'), ow=5)
    k = (lt * 1.5) % 1
    mx = -300 + 600 * ease(k); my = 110 - 280 * np.sin(np.pi * k)
    for i in range(int(lt * 1.5)):
        disc(cv, 300 - 60 + (i % 4) * 40, 150 - (i // 4) * 40, 30, ramp('#3d7fd8'), ow=3)
    hand(cv, mx + 30, my + 330, 0.5, wr=1.0, spread=0.6, arm=False)
    disc(cv, mx, my, 38, ramp('#3d7fd8'), ow=4)
    box(cv, 0, -560, 230, 85, DARK, r=26)
    label(cv, f'{lt:0.1f} SEC', 0, -550, 90, (120, 255, 140))
    label(cv, 'WRINKLY = FASTER', 0, -400, 70, (255, 255, 255))
    return cv


BEATS = [b0_hook, b1_myth, b2_weird, b3_nerve, b4_brain, b5_vessels, b6_grooves, b7_tire, b8_marbles]

if __name__ == '__main__':
    run(BEATS)
