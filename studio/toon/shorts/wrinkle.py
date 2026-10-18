#!/usr/bin/env python3
"""Why Your Fingers Wrinkle in Water. Opens on a hand lifting out of bath water as the tips wrinkle into treads."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

NERVE = flat(hexc('#ffd23f'))
VES = ramp('#d8343a', '#9a1f24', '#ff6a6a')
TIRE = ramp('#2b2b30', '#18181b', '#4a4a52')


def finger(cv, x, y, s, wr=0.0, swell=0.0, shrink=0.0, tilt=0.0, xray=0.0, nerve=None, vessels=0.0, T=0.0):
    """One big finger pointing up. wr: wrinkle grooves 0..1."""
    w = 150 * s * (1 + 0.15 * swell - 0.08 * shrink)
    top = y - 900 * s
    f = capsule(x, y + 200 * s, x, top, w, w * 0.95)
    cv.shape(f, (x - w - 10, top - w - 10, x + w + 10, y + 200 * s + w), SKIN, bevel=90 * s, alpha=1 - 0.55 * xray)
    cv.shape(rotell(x, top + 40 * s, w * 0.6, w * 0.45, 0), (x - w, top - w, x + w, top + w), ramp('#f8d8c8'), ow=3, alpha=0.9 - 0.5 * xray)
    if wr > 0:
        for i in range(9):
            yy = top - 40 * s + i * 52 * s
            amp = 14 * s * wr
            pts = [(x - w * 0.85 + u * w * 1.7, yy + amp * np.sin(u * 7 + i)) for u in np.linspace(0, 1, 14)]
            line(cv, pts, 6 * s, flat(hexc('#c98a6e')), a=min(1, wr * 1.4))
    if vessels > 0:
        for k in (-1, 0, 1):
            ww = 18 * s * (1 - 0.6 * vessels)
            line(cv, [(x + k * w * 0.5, y + 150 * s), (x + k * w * 0.4, top + 80 * s), (x + k * w * 0.15, top - 30 * s)], ww, VES, ow=3)
    if nerve is not None:
        line(cv, [(x, y + 200 * s), (x + 10, top + 100 * s), (x, top - 20 * s)], 10 * s, NERVE, ow=3)
        if nerve > 0:
            cy = y - 100 * s
            for d in (-1, 1):
                line(cv, [(x - 60 * s, cy - 50 * s * d), (x + 60 * s, cy + 50 * s * d)], 14 * s, flat(hexc('#e2483d')), ow=3)


def water(cv, y, T, a=1.0):
    f, bb = wave_surface(y, 14, 0.02, T * 3, x0=-1600, x1=1600, y1=3000)
    cv.shape(f, bb, ramp('#7fd0ff', '#3fa9e0', '#bfeaff'), ow=4, shadow=0, alpha=0.8 * a)


def b0_hook(lt, dur, T):
    """The finger rises out of the water and wrinkles into tire tread. Before 0: dipping down (the loop)."""
    p = lt + 1.2
    rise = ease(np.clip(p / 1.4, 0, 1))
    cv = Canvas(0, -150, 1.0)
    sky_bg(cv)
    finger(cv, 0, 950 - 600 * rise, 1.0, wr=ease(np.clip((lt - 0.2) / 0.8, 0, 1)) if lt >= 0 else 0.0)
    water(cv, 600, T)
    if lt >= 0:
        for k in range(4):
            ph = (lt * 1.2 + k / 4) % 1
            disc(cv, -120 + k * 80, 420 + ph * 200, 12, ramp('#bfeaff'), ow=2, alpha=1 - ph)
        hook_text(cv, 'RAIN TIRES', lt, y=-680, size=130, pop_t=0.2, color=(255, 236, 80))
    return cv


def b1_myth(lt, dur, T):
    cv = Canvas(0, -150, 1.0)
    sky_bg(cv)
    finger(cv, 0, 650, 1.0, swell=0.6 + 0.3 * np.sin(lt * 4))
    for k in range(6):
        a = k * np.pi / 3 + lt
        arrows(cv, [((np.cos(a) * 400, -300 + np.sin(a) * 400), (np.cos(a) * 230, -300 + np.sin(a) * 230))], (120, 200, 255), 10)
    label(cv, 'SOAKS UP WATER?', 0, -880, 76, (255, 255, 255))
    return cv


def b2_weird(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=700)
    guy(cv, 0, 700, 0.95, face='shock', coat=True, shirt=ramp('#f4f1ea'), arms=((40, 90), (140, 30)), glasses=True)
    hook_text(cv, 'WAIT...', lt, y=-660, size=130, pop_t=0.4)
    return cv


def b3_nerve(lt, dur, T):
    cv = Canvas(0, -150, 1.0)
    sky_bg(cv)
    k = np.clip((lt - 0.5) / 0.3, 0, 1)
    for sx, cut in ((-1, True), (1, False)):
        finger(cv, sx * 250, 650, 0.75, wr=0 if cut else 1.0, nerve=k if cut else 0.0, xray=0.4)
    label(cv, 'NERVE CUT', -250, -650, 60, (255, 90, 80))
    label(cv, 'NORMAL', 250, -650, 60, (255, 255, 255))
    if lt > dur * 0.5:
        label(cv, 'NO WRINKLES', -250, 900, 56, (255, 90, 80))
    return cv


def b4_brain(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    brain(cv, 0, -560, 1.2, hot=0.3)
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    pts = [(0, -380), (60, -100), (200, 150), (300, 450), (330, 650)]
    n = max(2, int(k * len(pts) + 0.999))
    line(cv, pts[:n], 12, NERVE, ow=3)
    tip = pts[n - 1]
    cv.glow(circle(tip[0], tip[1], 20), (tip[0] - 60, tip[1] - 60, tip[0] + 60, tip[1] + 60), '#ffd23f', 40, 0.9)
    finger(cv, 330, 1400, 0.6)
    hook_text(cv, 'ON PURPOSE', lt, y=-900, size=110, pop_t=dur * 0.5)
    return cv


def b5_vessels(lt, dur, T):
    cv = Canvas(0, -150, 1.0)
    sky_bg(cv)
    finger(cv, 0, 650, 1.0, xray=0.6, vessels=ease(np.clip(lt / (dur * 0.7), 0, 1)))
    for sx in (-1, 1):
        arrows(cv, [((sx * 380, -150), (sx * 200, -150))], (255, 90, 80), 12)
    label(cv, 'SQUEEZE', 0, -900, 90, (255, 90, 80))
    return cv


def b6_grooves(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, -300, 1.4)
    sky_bg(cv)
    finger(cv, 0, 650, 1.0, wr=k, shrink=k)
    return cv


def b7_tire(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv, ground=500, gcol='#5a6070')
    for sx, c in ((-1, None), (1, None)):
        pass
    disc(cv, 0, 150, 340, TIRE)
    disc(cv, 0, 150, 160, STEEL)
    a0 = T * 200
    for k in range(18):
        a = np.radians(a0 + k * 20)
        line(cv, [(np.cos(a) * 280, 150 + np.sin(a) * 280), (np.cos(a) * 335, 150 + np.sin(a) * 335)], 14, flat(hexc('#55555e')))
    specks(cv, T, lambda i, v, tt: (-200 - ((tt * 900 + v[0] * 600) % 600), 470 - v[1] * 260 * ((tt * 900 + v[0] * 600) % 600) / 600, 1.0), 40, (160, 220, 255), 9, seed=4)
    finger(cv, 0, 2100, 0.55, wr=1.0)
    label(cv, 'GROOVES MOVE WATER', 0, -560, 66, (255, 255, 255))
    return cv


def b8_marbles(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for sx in (-1, 1):
        cv.shape(inter(circle(sx * 300, 200, 200), lambda X, Y: 200 - Y), (sx * 300 - 210, 0, sx * 300 + 210, 210), ramp('#e8eef3'), ow=5)
    k = (lt * 1.5) % 1
    mx = -300 + 600 * ease(k); my = 120 - 260 * np.sin(np.pi * k)
    disc(cv, mx, my, 40, ramp('#3d7fd8'), ow=4)
    finger(cv, mx, my + 900 * 0.5, 0.5, wr=1.0)
    for i in range(int(lt * 1.5)):
        disc(cv, 300 - 60 + (i % 4) * 40, 150 - (i // 4) * 40, 34, ramp('#3d7fd8'), ow=3)
    box(cv, 0, -560, 230, 85, DARK, r=26)
    label(cv, f'{lt:0.1f} SEC', 0, -550, 90, (120, 255, 140))
    label(cv, 'WRINKLY = FASTER', 0, -400, 70, (255, 255, 255))
    return cv


BEATS = [b0_hook, b1_myth, b2_weird, b3_nerve, b4_brain, b5_vessels, b6_grooves, b7_tire, b8_marbles]

if __name__ == '__main__':
    run(BEATS)
