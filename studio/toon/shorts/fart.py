#!/usr/bin/env python3
"""Why farts smell. Opens on a stink cloud blasting out behind a guy; loops back into the blast."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

STINK = ramp('#b8d86a', '#80a83a', '#e4f8a8')
SULF = ramp('#e8d84a', '#b8a020', '#fff8a0')
CLEAR = ramp('#dff4ff', '#a8d4f0', '#ffffff')


def stink_cloud(cv, x, y, r, T, a=1.0, col=None):
    col = STINK if col is None else col
    blobs = [circle(x + np.cos(k * 1.3 + T) * r * 0.5, y + np.sin(k * 1.7 + T * 0.8) * r * 0.35, r * (0.45 + 0.1 * np.sin(k + T * 2))) for k in range(5)]
    cv.shape(smooth(r * 0.2, *blobs), (x - r * 1.2, y - r, x + r * 1.2, y + r), col, alpha=0.85 * a)
    for k in range(4):
        ph = (T * 0.8 + k / 4) % 1
        xx = x + (k - 1.5) * r * 0.4
        pts = [(xx + 18 * np.sin(u * 6 + T * 3), y - r * 0.8 - u * r * 0.6 - ph * 40) for u in np.linspace(0, 1, 6)]
        line(cv, pts, 7, flat(hexc('#80a83a')), a=a * (1 - ph))


def b0_hook(lt, dur, T):
    """The blast is already out on frame one; before 0 he's standing there, a little uneasy (the loop)."""
    k = ease(np.clip((lt + 0.1) / 0.5, 0, 1)) if lt > -0.1 else 0.0
    cv = Canvas(0, -420, 1.15)
    sky_bg(cv, ground=0)
    guy(cv, -120, jolt(lt, 0.0, 25) if lt >= 0 else 0, 1.0, face='worried' if lt < 0 else 'squint', arms=((12, 0), (12, 0)), shirt=BLUE)
    if k > 0:
        stink_cloud(cv, 230 + 100 * k, -420, 120 + 160 * k, T, a=1.0)
        for j in range(6):
            a = -0.6 + j * 0.25
            line(cv, [(80 + np.cos(a) * 60, -420 + np.sin(a) * 60), (80 + np.cos(a) * (60 + 200 * k), -420 + np.sin(a) * (60 + 200 * k))], 8,
                 flat(hexc('#ffffff')), a=1 - k * 0.6)
    if lt >= 0:
        hook_text(cv, 'STINK', lt, y=-780, size=170, color=(184, 216, 106))
    return cv


def bubbles_mix(cv, lt, smelly_frac, n=40, r=420, seed=2, label_=True):
    rng = np.random.default_rng(seed)
    for j in range(n):
        a = rng.uniform(0, 2 * np.pi); d = np.sqrt(rng.uniform(0, 1)) * r
        x, y = np.cos(a) * d + 10 * np.sin(lt * 2 + j), np.sin(a) * d * 1.2 + 10 * np.cos(lt * 2 + j)
        smelly = j < max(1, int(n * smelly_frac))
        disc(cv, x, y, rng.uniform(22, 40), SULF if smelly else CLEAR, ow=3)


def b1_mostly(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    bubbles_mix(cv, lt, 0.0)
    label(cv, 'NO SMELL', 0, -620, 96, WHT)
    return cv


def b2_air(lt, dur, T):
    cv = Canvas(0, -300, 1.05)
    sky_bg(cv, ground=0)
    guy(cv, -200, 0, 1.0, face='happy', arms=((40, 110), (12, 0)))
    for j in range(8):                                                   # gulping air while eating
        ph = (lt * 1.4 + j / 8) % 1
        disc(cv, -200 + (1 - ph) * 200, -700 + ph * 60, 14, CLEAR, ow=2, alpha=1 - ph * 0.5)
    tube(cv, -300, x0=100, x1=560, r=110)
    for j in range(6):
        ph = (lt * 0.9 + j / 6) % 1
        disc(cv, 140 + ph * 380, -300 + 30 * np.sin(j * 2 + lt * 3), 16, CLEAR, ow=2)
    label(cv, 'SWALLOWED AIR', -120, -1080, 56, WHT)
    label(cv, 'GUT GAS', 330, -480, 56, WHT)
    return cv


def b3_one(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    bubbles_mix(cv, lt, 0.025)
    k = ease(np.clip((lt - 0.5) / 0.3, 0, 1))
    if k > 0:
        cv.glow(circle(0, 0, 40), (-200, -200, 200, 200), '#ffe14d', 60, 0.3 * k)
    hook_text(cv, 'LESS THAN 1%', lt, y=-720, size=130, pop_t=0.5, color=(232, 216, 74))
    return cv


def b4_egg(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    sp = ease(np.clip(lt / 0.5, 0, 1))
    for sx in (-1, 1):
        cv.shape(inter(rotell(sx * 30 * sp, 40, 170, 220, 0), lambda X, Y, sx=sx: sx * X - 10 * sp), (-240, -200, 240, 280), ramp('#f4f1ea'), ow=4)
    cv.shape(rotell(0, 160, 120, 50, 0), (-130, 100, 130, 220), ramp('#ffd23f'), ow=3)
    stink_cloud(cv, 0, -200, 180 * sp + 1, T, a=sp, col=SULF)
    label(cv, 'SULFUR', 0, -520, 90, (232, 216, 74))
    return cv


def b5_germs(lt, dur, T):
    cv = Canvas(0, 0, 1.5)
    sky_bg(cv)
    tube(cv, 0, x0=-900, x1=900)
    lump(cv, -100 + lt * 30, 10, 110, col=SLOP)
    for j in range(6):
        a = j * 1.05 + lt * 1.5
        germ(cv, -100 + lt * 30 + np.cos(a) * 160, 10 + np.sin(a) * 90, 30, T, seed=j, angry=False)
    for j in range(8):
        ph = (lt * 1.3 + j / 8) % 1
        disc(cv, -100 + 120 * np.sin(j * 2.3), 10 - ph * 140, 10 + 6 * ph, SULF, ow=2, alpha=1 - ph)
    label(cv, 'TRILLIONS', 0, -300, 70, (127, 211, 79))
    return cv


def b6_foods(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for j in range(4):
        u = ease(np.clip((lt - j * 0.45) / 0.4, 0, 1))
        if u <= 0:
            continue
        x, y = [(-230, -230), (230, -230), (-230, 230), (230, 230)][j]
        if j == 0:
            cv.shape(rotell(x, y, 110 * u, 140 * u, 0), (x - 120, y - 150, x + 120, y + 150), ramp('#f4f1ea'))
        elif j == 1:
            cv.shape(smooth(30, rotell(x, y, 150 * u, 90 * u, 10), circle(x - 100 * u, y + 30 * u, 60 * u)), (x - 200, y - 120, x + 180, y + 120), ramp('#b8443a', '#7a2622', '#e0706a'))
            line(cv, [(x - 60 * u, y - 30 * u), (x + 80 * u, y + 20 * u)], 12 * u, flat(hexc('#f4d0c0')), a=u)
        elif j == 2:
            line(cv, [(x, y + 120 * u), (x, y)], 30 * u, ramp('#7fbf4f'), ow=3, flat=False)
            cv.shape(smooth(20, circle(x - 60 * u, y - 30 * u, 60 * u), circle(x + 60 * u, y - 30 * u, 60 * u), circle(x, y - 80 * u, 70 * u)), (x - 140, y - 170, x + 140, y + 50), ramp('#3fa84a', '#25703a', '#7fd88a'))
        else:
            for q in range(6):
                cv.shape(rotell(x - 90 + (q % 3) * 90, y - 30 + (q // 3) * 70, 40 * u, 26 * u, 20), (x - 140, y - 80, x + 140, y + 120), ramp('#a8443a', '#6e2622', '#d0706a'))
        stink_cloud(cv, x + 90, y - 120, 50 * u + 1, T + j, a=0.7 * u, col=SULF)
    return cv


def b7_count(lt, dur, T):
    cv = Canvas(0, -300, 1.05)
    sky_bg(cv, ground=0)
    n = int(np.clip(lt / (dur * 0.8), 0, 1) * 20)
    guy(cv, -150, jolt(lt % 0.8, 0.05, 15), 1.0, face='happy', arms=((12, 0), (12, 0)))
    if (lt % 0.8) < 0.5:
        stink_cloud(cv, 170, -420, 90, T, a=1 - (lt % 0.8) / 0.5)
    badge(cv, f'{max(n, 1)} TODAY', y=-1080, col=(184, 216, 106))
    return cv


def b8_hold(lt, dur, T):
    cv = Canvas(0, -300, 1.05)
    sky_bg(cv, ground=0)
    held = lt < dur * 0.6
    guy(cv, 0, 0, 1.0, face='puff' if held else 'happy', arms=((12, 0), (12, 0)), tint=('#ff6a5a', 0.25 * min(1, lt)) if held else None)
    if held:
        disc(cv, 0, -400, 50 + 30 * lt / dur, STINK, ow=3, alpha=0.8)              # gas trapped in the gut
        label(cv, 'TRAPPED', 0, -1100, 70, RED)
    else:
        stink_cloud(cv, 260, -420, 200, T)
        hook_text(cv, 'LATER', lt, y=-760, size=150, pop_t=dur * 0.6, color=(184, 216, 106))
    return cv


BEATS = [b0_hook, b1_mostly, b2_air, b3_one, b4_egg, b5_germs, b6_foods, b7_count, b8_hold]

if __name__ == '__main__':
    run(BEATS)
