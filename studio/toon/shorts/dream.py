#!/usr/bin/env python3
"""Dreams. Opens on a sleeper with a dream bubble bursting out of his head; loops back into it."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

NIGHT = ('#1b2350', '#3a3f7a')


def night_bg(cv):
    cv.background(*NIGHT, vignette=0.25)
    rng = np.random.default_rng(3)
    for k in range(30):
        x, y = rng.uniform(-700, 700), rng.uniform(-1200, 1200)
        tw = 0.5 + 0.5 * np.sin(k * 1.7)
        disc(cv, cv.cx + x / cv.zoom, cv.cy + y / cv.zoom, 4 / cv.zoom, ramp('#ffffff'), ow=0, shadow=0, flat=True, alpha=0.5 + 0.4 * tw)


def fish(cv, x, y, s, T, legs=False):
    cv.shape(rotell(x, y, 110 * s, 60 * s, 0), (x - 130 * s, y - 70 * s, x + 130 * s, y + 70 * s), ORANGE)
    cv.shape(poly([(x - 100 * s, y), (x - 180 * s, y - 60 * s), (x - 180 * s, y + 60 * s)]), (x - 190 * s, y - 70 * s, x - 90 * s, y + 70 * s), ORANGE)
    disc(cv, x + 60 * s, y - 15 * s, 14 * s, ramp('#ffffff'), ow=2, shadow=0); dot(cv, x + 63 * s, y - 15 * s, 7 * s)
    if legs:
        for dx in (-30, 30):
            st = 20 * np.sin(T * 8 + dx)
            line(cv, [(x + dx * s, y + 50 * s), (x + (dx + st) * s, y + 130 * s)], 14 * s, JEANS, ow=3, flat=False)


def b0_hook(lt, dur, T):
    """The dream bubble is bursting out on frame one. Before 0: Zzz, deep asleep (the loop)."""
    k = np.clip((lt + 0.3) / 0.8, 0, 1)
    cv = Canvas(0, 60, 0.9)
    night_bg(cv)
    bed(cv, T, 0, 420, 0.9)
    dream_bubble(cv, 0, -280, 80, -560, 330, k)
    if k > 0.6:
        fish(cv, 80 + 30 * np.sin(T * 2), -560 + 20 * np.sin(T * 3), 0.9, T)
        cloud(cv, -130, -500, 60, col=ramp('#ffffff'))
    for j in range(3):
        ph = (lt * 0.7 + j / 3) % 1
        label(cv, 'Z', 250 + 40 * j, -300 - 200 * ph, 50 + 20 * j, WHT, a=1 - ph)
    if lt >= 0:
        hook_text(cv, 'DREAMING', lt, y=-800, size=140, color=(190, 170, 255))
    return cv


def b1_eyes(lt, dur, T):
    cv = Canvas(0, -700, 3.2)
    night_bg(cv)
    guy(cv, 0, 0, 1.0, face='closed', legs=False, ground=False)
    for sx in (-1, 1):
        ex = sx * 34 + 10 * np.sin(lt * 14) * (1 if lt > 0.6 else 0)
        cv.shape(rotell(ex, -770, 22, 12, 0), (ex - 26, -786, ex + 26, -754), SKIN, ow=2.5, shadow=0)
    hook_text(cv, '90 MIN', lt, y=-760, size=130, pop_t=0.2, color=(190, 170, 255))
    return cv


def b2_lights(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    night_bg(cv)
    brain(cv, 0, 0, 1.6, hot=0.0)
    rng = np.random.default_rng(int(lt * 6))
    for j in range(8):
        x, y = rng.uniform(-260, 260), rng.uniform(-180, 180)
        cv.glow(circle(x, y, 18), (x - 120, y - 120, x + 120, y + 120), rng.choice(['#ffd23f', '#7fd0ff', '#ff8af0']), 30, 0.4)
    hook_text(cv, 'WIDE AWAKE', lt, y=-720, size=130, pop_t=0.5, color=YEL)
    return cv


def b3_locked(lt, dur, T):
    lk = ease(np.clip((lt - 0.5) / 0.4, 0, 1))
    cv = Canvas(0, 60, 0.9)
    night_bg(cv)
    bed(cv, T, 0, 420, 0.9, lock=lk)
    dream_bubble(cv, 0, -280, 0, -600, 300, 1.0)
    guy(cv, 30 * np.sin(lt * 6), -460, 0.3, face='shock', arms=((40 + 40 * np.sin(lt * 12), 0), (40 - 40 * np.sin(lt * 12), 0)))
    hook_text(cv, 'LOCKED', lt, y=-820, size=140, pop_t=0.7, color=RED)
    return cv


def card(cv, x, y, s, kind, a=1.0):
    box(cv, x, y, 90 * s, 110 * s, ramp('#ffffff', '#d8dde4', '#ffffff'), r=16 * s, alpha=a)
    if kind == 'car':
        box(cv, x, y + 10 * s, 60 * s, 25 * s, RED, r=12 * s, alpha=a)
        for dx in (-35, 35):
            disc(cv, x + dx * s, y + 40 * s, 14 * s, DARK, alpha=a)
    elif kind == 'cat':
        disc(cv, x, y + 10 * s, 45 * s, ORANGE, alpha=a)
        for sx in (-1, 1):
            cv.shape(poly([(x + sx * 40 * s, y - 20 * s), (x + sx * 15 * s, y - 30 * s), (x + sx * 40 * s, y - 60 * s)]), (x - 50 * s, y - 70 * s, x + 50 * s, y), ORANGE, alpha=a)
    elif kind == 'house':
        box(cv, x, y + 25 * s, 50 * s, 40 * s, BLUE, r=6 * s, alpha=a)
        cv.shape(poly([(x - 65 * s, y - 10 * s), (x, y - 65 * s), (x + 65 * s, y - 10 * s)]), (x - 70 * s, y - 70 * s, x + 70 * s, y), RED, alpha=a)
    elif kind == 'school':
        box(cv, x, y + 15 * s, 60 * s, 50 * s, YELLOW, r=6 * s, alpha=a)
        label(cv, 'A+', x, y + 20 * s, 40 * s, (40, 40, 50), a=a)


def b4_sort(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    night_bg(cv)
    brain(cv, 0, -400, 1.3)
    kinds = ['car', 'cat', 'house', 'school']
    for j, kd in enumerate(kinds):
        u = ease(np.clip((lt - j * 0.4) / 0.8, 0, 1))
        x0, y0 = -420 + j * 280, 500
        x1, y1 = (-200 if j % 2 else 200), 100 + 120 * (j // 2)
        card(cv, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u - 150 * np.sin(np.pi * u), 1.3, kd)
    label(cv, 'SORTING', 0, -720, 90, (190, 170, 255))
    return cv


def b5_mash(lt, dur, T):
    u = ease(np.clip(lt / (dur * 0.5), 0, 1))
    cv = Canvas(0, 0, 1.0)
    night_bg(cv)
    if u < 1:
        card(cv, -360 + 360 * u, 0, 1.4, 'cat', a=1.0)
        card(cv, 360 - 360 * u, 0, 1.4, 'car', a=1.0)
    else:
        cloud(cv, 0, 0, 280 * (1 + 0.05 * np.sin(lt * 6)))
        box(cv, 0, 30, 110, 45, RED, r=20)                              # a car...
        for dx in (-70, 70):
            disc(cv, dx, 80, 26, DARK)
        disc(cv, 0, -40, 55, ORANGE)                                    # ...with a cat's head
        for sx in (-1, 1):
            cv.shape(poly([(sx * 50, -70), (sx * 20, -80), (sx * 50, -120)]), (-60, -130, 60, -60), ORANGE)
            dot(cv, sx * 18, -45, 7)
        cv.flash('#ffffff', 0.4 * max(0, 1 - (lt - dur * 0.5) / 0.15))
    hook_text(cv, 'MASHED UP', lt, y=-720, size=130, pop_t=dur * 0.5, color=(255, 138, 240))
    return cv


def b6_weird(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#6a3fa8', '#ff8ac8', vignette=0.25)
    disc(cv, 300, -500, 140, ramp('#fff0a0', '#e0c060', '#ffffff'))
    dot(cv, 260, -520, 12); dot(cv, 340, -520, 12)
    line(cv, [(250, -460), (300, -440), (350, -460)], 7, INKC)
    for j in range(3):
        fish(cv, -300 + ((lt * 220 + j * 400) % 1000) - 200, 150 + j * 160 + 30 * np.sin(lt * 3 + j), 0.9, T, legs=True)
    box(cv, -260, -260 + 30 * np.sin(lt * 2), 90, 70, BLUE, r=10)
    cv.shape(poly([(-370, -320), (-260, -420), (-150, -320)]), (-380, -430, -140, -310), RED)
    hook_text(cv, 'SO WEIRD', lt, y=-760, size=140, pop_t=0.4, color=YEL)
    return cv


def b7_count(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    night_bg(cv)
    box(cv, 0, 200, 460, 12, ramp('#8a90c0'), r=6, ow=0, shadow=0)
    n = int(np.clip(lt / (dur * 0.8), 0, 1) * 5.99)
    for j in range(5):
        x = -360 + j * 180
        hgt = 80 + 40 * j
        on = j < n
        box(cv, x, 200 - hgt / 2, 50, hgt / 2, ramp('#b9a8ff') if on else ramp('#3a3f7a'), r=20)
        if on:
            cloud(cv, x, 200 - hgt - 90, 70)
    badge(cv, f'{max(n, 1)} DREAMS', y=-560, col=(190, 170, 255))
    return cv


def b8_gone(lt, dur, T):
    cv = Canvas(0, 60, 0.9)
    night_bg(cv) if lt < 0.6 else cv.background('#ffd27a', '#fff3d0', vignette=0.15)
    bed(cv, T, 0, 420, 0.9, face='shock' if lt > 0.6 else 'closed')
    for j in range(4):                                                  # bubbles popping one by one
        t0 = 0.8 + j * 0.45
        if lt < t0:
            cloud(cv, -330 + j * 220, -560 + 60 * (j % 2), 100)
        elif lt < t0 + 0.2:
            u = (lt - t0) / 0.2
            for q in range(8):
                a = q * 0.785
                disc(cv, -330 + j * 220 + np.cos(a) * 130 * u, -560 + 60 * (j % 2) + np.sin(a) * 130 * u, 10, ramp('#ffffff'), ow=0, alpha=1 - u)
    ax = 360
    shk = 8 * np.sin(lt * 60) if lt > 0.5 else 0
    disc(cv, ax + shk, -200, 90, RED)                                   # alarm clock ringing
    disc(cv, ax + shk, -200, 66, ramp('#ffffff'), ow=3)
    line(cv, [(ax + shk, -200), (ax + shk, -250)], 7, INKC)
    line(cv, [(ax + shk, -200), (ax + shk + 35, -200)], 7, INKC)
    hook_text(cv, 'GONE', lt, y=-820, size=150, pop_t=1.6, color=WHT)
    return cv


BEATS = [b0_hook, b1_eyes, b2_lights, b3_locked, b4_sort, b5_mash, b6_weird, b7_count, b8_gone]

if __name__ == '__main__':
    run(BEATS)
