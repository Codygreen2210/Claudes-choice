#!/usr/bin/env python3
"""Boredom. Opens on the brain already scanning, radar sweeping; loops back into the scan."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

DESK = ramp('#a8693a', '#6e4122', '#d08f58')
DOPA = ramp('#ffd23f', '#d09a10', '#fff08a')
GREY = ('#8a96a8', '#c8d0dc')


def b1_hunt(lt, dur, T):
    cv = Canvas(0, 260, 1.0)
    sky_bg(cv)
    brain(cv, 0, 100, 1.6)
    a = lt * 2.5
    for r in (300, 420, 540):                                               # radar sweep
        cv.shape(subtract(circle(0, 100, r), circle(0, 100, r - 8)), (-r, 100 - r, r, 100 + r), flat(hexc('#7fe8a0')), ow=0, shadow=0, flat=True, alpha=0.5)
    line(cv, [(0, 100), (np.cos(a) * 540, 100 + np.sin(a) * 540)], 10, flat(hexc('#7fe8a0')), a=0.8)
    for q in range(5):
        b = q * 1.3
        if abs(((a - b) % (2 * np.pi))) < 0.5:
            disc(cv, np.cos(b) * 450, 100 + np.sin(b) * 450, 22, ramp('#7fe8a0'), ow=2)
    if lt >= 0:
        hook_text(cv, 'SCANNING', lt, y=-780, size=150, color=(127, 232, 160))
    return cv


def b2_warning(lt, dur, T):
    on = ease(np.clip((lt - dur * 0.4) / 0.2, 0, 1))
    blink = 0.5 + 0.5 * np.sin(lt * 10) if on > 0 else 0
    cv = Canvas(0, 220, 1.0)
    cv.background('#2b2f38', '#454b57', vignette=0.3)
    box(cv, 0, 150, 460, 300, DARK, r=40)                                  # the brain's dashboard
    for j in range(3):
        disc(cv, -250 + j * 250, 60, 70, ramp('#3a3f4a'), ow=4)
    disc(cv, 0, 60, 70, ramp('#ff8a2a') if on > 0 else ramp('#3a3f4a'), ow=4)
    if on > 0:
        cv.glow(circle(0, 60, 70), (-300, -240, 300, 360), '#ff8a2a', 80, 0.8 * blink)
    label(cv, 'NEW?', -250, 230, 46, WHT); label(cv, 'BORED', 0, 230, 46, (255, 160, 80)); label(cv, 'USEFUL?', 250, 230, 46, WHT)
    hook_text(cv, 'WARNING', lt, y=-720, size=150, pop_t=dur * 0.45, color=(255, 138, 42))
    return cv


def b3_go(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    brain(cv, -150, -250, 1.1)
    for j in range(3):
        u = (lt * 0.8 + j / 3) % 1
        arrows(cv, [((80 + 200 * u, -250 + 30 * j), (220 + 200 * u, -250 + 30 * j))], YEL, 14)
    cloud(cv, 120, 150, 260)
    label(cv, 'SOMETHING', 120, 125, 54, (40, 40, 50)); label(cv, 'BETTER', 120, 195, 54, (40, 40, 50))
    return cv


def b4_dopamine(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, -300, 1.05)
    cv.background(*GREY, vignette=0.25)
    box(cv, 0, 600, 1600, 600, ramp('#9aa4b2'), r=0, ow=0, shadow=0)
    tap = abs(np.sin(lt * 12)) * 30
    guy(cv, 0, -tap * 0.2, 1.0, face='worried', arms=((30, 40 + 30 * np.sin(lt * 9)), (30, 40 + 30 * np.cos(lt * 9))))
    meter(cv, 0, -1000, 420, 0.85 - 0.65 * k, DOPA, 'DOPAMINE')
    for sx in (-1, 1):
        line(cv, [(sx * 160, -400 + 20 * np.sin(lt * 15)), (sx * 210, -420 + 20 * np.sin(lt * 15))], 7, flat(hexc('#ffffff')), a=0.8)
    return cv


def b5_room(lt, dur, T):
    k = np.clip(lt / (dur * 0.8), 0, 1)
    cv = Canvas(0, -300, 1.0)
    cv.background('#e8eef3', '#c8d0d8', vignette=0.3)
    box(cv, 0, 600, 1600, 600, ramp('#b8c0c8'), r=0, ow=0, shadow=0)
    box(cv, 0, -100, 160, 20, DARK, r=8)                                   # chair seat
    guy(cv, 0, 0, 1.0, face='calm', arms=((12, 0), (12, 0)))
    box(cv, 320, -380, 70, 50, ramp('#e2483d'), r=16)                       # the shock button on a little table
    box(cv, 320, -320, 110, 14, STEEL, r=6)
    badge(cv, f'{int(15 * k)}:00', y=-1000, col=YEL, w=220)
    label(cv, 'ALONE', 0, -1140, 70, WHT)
    return cv


def b6_shock(lt, dur, T):
    press = (lt % 1.1) < 0.18
    cv = Canvas(0, -300, 1.0)
    cv.background('#e8eef3', '#c8d0d8', vignette=0.3)
    box(cv, 0, 600, 1600, 600, ramp('#b8c0c8'), r=0, ow=0, shadow=0)
    guy(cv, 0, jolt(lt % 1.1, 0.0, 30), 1.0, face='shock' if press else 'calm', arms=((12, 0), (60, 60)))
    box(cv, 320, -380 + (10 if press else 0), 70, 50, ramp('#e2483d'), r=16)
    box(cv, 320, -320, 110, 14, STEEL, r=6)
    if press:
        for q in range(6):
            a = q * 1.05
            line(cv, [(np.cos(a) * 140, -500 + np.sin(a) * 140), (np.cos(a) * 170 + 20, -500 + np.sin(a) * 170), (np.cos(a) * 210, -500 + np.sin(a) * 210)], 8,
                 flat(hexc('#ffd23f')), ow=2)
        cv.flash('#fff8c0', 0.25)
    badge(cv, '2 OUT OF 3 MEN', y=-960, col=RED, w=520)
    hook_text(cv, 'ZAP', lt, y=-830, size=170, pop_t=0.3, color=YEL)
    return cv


def b7_wander(lt, dur, T):
    cv = Canvas(0, -300, 1.0)
    sky_bg(cv, ground=0)
    guy(cv, -200, 0, 0.95, face='happy', arms=((12, 0), (60, 160)), look=(0.6, -1))
    for j in range(4):
        u = ease(np.clip((lt - j * 0.5) / 0.6, 0, 1))
        cloud(cv, -100 + j * 110, -860 - j * 80, 30 + 22 * j * u + 1, a=u)
    if lt > dur * 0.55:
        bx, by = 300, -1120
        cv.glow(circle(bx, by, 70), (bx - 250, by - 250, bx + 250, by + 250), '#ffd23f', 90, 0.8)
        disc(cv, bx, by, 70, YELLOW)
        box(cv, bx, by + 90, 34, 24, STEEL, r=8)
    return cv


def b8_creative(lt, dur, T):
    cv = Canvas(0, 250, 1.0)
    sky_bg(cv)
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    box(cv, -260, -60, 170, 220, ramp('#ffffff', '#d8dde4', '#ffffff'), r=16)      # the boring phone-number list
    for q in range(8):
        box(cv, -260, -230 + q * 50, 120, 8, ramp('#9aa4b2'), r=4, ow=0, shadow=0)
    label(cv, 'BORING', -260, 230, 54, (200, 205, 215))
    arrows(cv, [((-60, 0), (60, 0))], YEL, 14)
    n = int(1 + 6 * k)
    for q in range(n):
        a = q * 0.9
        x, y = 280 + np.cos(a) * 140, np.sin(a) * 200
        cv.shape(poly([(x - 40, y - 50), (x + 40, y - 50), (x + 28, y + 50), (x - 28, y + 50)]), (x - 50, y - 60, x + 50, y + 60), ramp(['#e2483d', '#3d7fd8', '#3fbf6a', '#ffd23f', '#7a4fd0', '#ff8a2a', '#ff8f9a'][q]))
    label(cv, 'MORE IDEAS', 280, 330, 54, YEL)
    return cv


BEATS = [b1_hunt, b2_warning, b3_go, b4_dopamine, b5_room, b6_shock, b7_wander, b8_creative]

if __name__ == '__main__':
    run(BEATS)
