#!/usr/bin/env python3
"""The flu. Opens on a sneeze cloud of viruses blasting at the camera; loops back into the sneeze."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

AIRWAY = ramp('#f4b0b8', '#c97a86', '#ffd4da')


def airway_wall(cv, y=300, n=7, T=0.0, infected=(), burst=None):
    box(cv, 0, y + 260, 1200, 220, ramp('#c45a72'), r=0, ow=0, shadow=0)
    for j in range(n):
        x = -600 + j * 200
        hit = j in infected
        cell(cv, x, y, 95, T, col=ramp('#ff9a8a', '#d0606a', '#ffc8c0') if hit else AIRWAY, seed=j)
        for q in range(5):                                                 # little hairs (cilia) on top
            line(cv, [(x - 60 + q * 30, y - 90), (x - 55 + q * 30 + 10 * np.sin(T * 6 + q + j), y - 140)], 6, ramp('#ffd4da'), ow=2, flat=False)


def b0_hook(lt, dur, T):
    """The sneeze blast is already flying at us on frame one; before 0 he winds up (the loop)."""
    wind = ease(np.clip((lt + 0.6) / 0.6, 0, 1)) if lt < 0 else 1.0
    cv = Canvas(0, -420, 1.15)
    sky_bg(cv, ground=0)
    guy(cv, -200, 0, 1.0, face='closed' if lt < 0 else 'shock', arms=((20, 60), (20, 60)), tilt_head=-0.3 * wind if lt < 0 else 0.3)
    if lt >= 0:
        for j in range(16):
            rng = np.random.default_rng(j)
            ph = min(1.0, (lt * 1.3 + rng.uniform(0, 0.3)))
            a = rng.uniform(-0.5, 0.5)
            r = 60 + 900 * ph
            x, y = -160 + np.cos(a) * r, -700 + np.sin(a) * r * 0.6
            if j % 3 == 0:
                virus(cv, x, y, 18 + 30 * ph, T, seed=j)
            else:
                disc(cv, x, y, 8 + 10 * ph, SPIT, ow=2, alpha=1 - ph * 0.6)
        hook_text(cv, 'INVADED', lt, y=-800, size=160, color=RED)
    return cv


def b1_grab(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    airway_wall(cv, T=T)
    for j in range(4):
        u = ease(np.clip((lt - j * 0.4) / 1.0, 0, 1))
        x = -500 + j * 330
        virus(cv, x, -600 + 450 * u, 50, T, seed=j)
    label(cv, 'YOUR AIRWAY', 0, 700, 70, WHT)
    return cv


def b2_hijack(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    cv = Canvas(0, 0, 1.3)
    sky_bg(cv)
    cell(cv, 0, 0, 330, T, col=ramp('#ff9a8a', '#d0606a', '#ffc8c0'))
    for j in range(int(1 + 6 * k)):
        a = j * 0.9 + lt
        virus(cv, np.cos(a) * 160, np.sin(a) * 130, 30, T, seed=j)
    for j in range(3):                                                    # factory gears
        a = lt * (3 if j % 2 else -3)
        gx, gy = -120 + j * 120, 220
        for q in range(8):
            b = a + q * np.pi / 4
            line(cv, [(gx + np.cos(b) * 30, gy + np.sin(b) * 30), (gx + np.cos(b) * 50, gy + np.sin(b) * 50)], 14, STEEL, ow=2, flat=False)
        disc(cv, gx, gy, 34, STEEL)
    hook_text(cv, 'FLU FACTORY', lt, y=-720, size=120, pop_t=0.6, color=RED)
    return cv


def b3_burst(lt, dur, T):
    pop_t = dur * 0.6
    cv = Canvas(0, 0, 1.2)
    sky_bg(cv)
    sx_, sy_ = shake(lt, pop_t, 20, 0.4)
    cv.cx += sx_; cv.cy += sy_
    if lt < pop_t:
        sw = 1 + 0.15 * lt / pop_t + 0.04 * np.sin(lt * 20)
        cell(cv, 0, 0, 300 * sw, T, col=ramp('#ff9a8a', '#d0606a', '#ffc8c0'))
        for j in range(20):
            a = j * 0.7 + lt
            virus(cv, np.cos(a) * 180 * sw, np.sin(a) * 160 * sw, 22, T, seed=j)
    else:
        u = min(1.0, (lt - pop_t) / 0.8)
        for j in range(30):
            a = j * 0.42
            r = 80 + 700 * ease(u)
            virus(cv, np.cos(a) * r * (0.6 + 0.4 * ((j * 7) % 5) / 5), np.sin(a) * r, 26, T, seed=j)
        if u < 0.2:
            cv.flash('#ffffff', 0.4 * (1 - u / 0.2))
        badge(cv, 'THOUSANDS', y=-560, col=RED)
    return cv


def b4_alarm(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    flash = 0.5 + 0.5 * np.sin(lt * 10)
    cv.vignette(0.2 + 0.3 * flash)
    for j in range(3):
        u = ease(np.clip((lt - j * 0.3) / 0.6, 0, 1))
        fighter(cv, -300 + j * 300, 600 - 500 * u, 110, T, seed=j)
    for j in range(5):
        virus(cv, -400 + j * 200, -350 + 40 * np.sin(lt * 3 + j), 40, T, seed=j)
    hook_text(cv, 'ALARM', lt, y=-720, size=150, pop_t=0.3, color=RED)
    return cv


def b5_twist(lt, dur, T):
    cv = Canvas(0, -300, 1.05)
    sky_bg(cv, ground=0)
    guy(cv, 0, 0, 1.0, face='pain', arms=((20, 100), (20, 100)), tint=('#ff6a5a', 0.3))
    thermo(cv, 380, -500, 102, lo=96, hi=105, h=440, label_=False)
    label(cv, '102°F', 380, -820, 60, YEL)
    for j in range(4):                                                    # ache zaps
        a = j * 1.6 + lt * 3
        x, y = np.cos(a) * 200, -500 + np.sin(a) * 300
        line(cv, [(x, y), (x + 30, y + 20), (x + 10, y + 40), (x + 40, y + 60)], 7, flat(hexc('#ffd23f')), a=0.5 + 0.5 * np.sin(lt * 9 + j))
    hook_text(cv, 'YOUR OWN BODY', lt, y=-760, size=110, pop_t=dur * 0.45, color=YEL)
    return cv


def b6_heat(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#ff8a3a', '#ffd27a', vignette=0.25)
    for j in range(6):
        sl = 0.4 + 0.6 * (1 - ease(np.clip(lt / (dur * 0.8), 0, 1)))
        x = -400 + j * 160
        virus(cv, x, 40 * np.sin(lt * 2 * sl + j), 46 * (0.8 + 0.2 * sl), T * sl, seed=j, col=ramp('#c06a5a', '#8a3a32', '#e0908a'))
    thermo(cv, 0, -480, 102, lo=96, hi=105, h=300, label_=False)
    label(cv, 'SLOWED DOWN', 0, -260, 80, WHT)
    return cv


def b7_spread(lt, dur, T):
    cv = Canvas(0, -300, 0.95)
    sky_bg(cv, ground=0)
    guy(cv, -280, 0, 0.9, face='happy', arms=((12, 0), (60, 60)))
    guy(cv, 280, 0, 0.9, face='happy', shirt=ORANGE, arms=((60, 60), (12, 0)))
    for j in range(10):
        ph = (lt * 0.7 + j / 10) % 1
        virus(cv, -240 + 480 * ph, -560 + 60 * np.sin(ph * 6 + j), 18, T, seed=j)
    label(cv, 'FEELS FINE', -280, -1050, 56, (120, 255, 140))
    badge(cv, 'EARLY THIS YEAR', y=-1350, col=RED)
    return cv


def b8_shot(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    fighter(cv, -150, 50, 150, T, seed=1)
    cv.shape(rbox(300, -200, 120, 160, 20), (170, -370, 430, -30), ramp('#ffffff', '#d8dde4', '#ffffff'))    # wanted poster
    virus(cv, 300, -220, 60, T, seed=3)
    label(cv, 'WANTED', 300, -330, 40, RED)
    if k > 0.6:
        virus(cv, 250, 300, 50, T, seed=5)
        line(cv, [(130, 220), (370, 380)], 18, flat(hexc('#e2483d')), ow=3)
    hook_text(cv, 'TRAINED', lt, y=-720, size=150, pop_t=0.5, color=(127, 210, 255))
    return cv


BEATS = [b0_hook, b1_grab, b2_hijack, b3_burst, b4_alarm, b5_twist, b6_heat, b7_spread, b8_shot]

if __name__ == '__main__':
    run(BEATS)
