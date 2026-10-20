#!/usr/bin/env python3
"""Tattoos. Opens on the tattoo needle already buzzing into an arm; loops back into it."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

INK = ramp('#2b2f48', '#151828', '#4a5070')
EPI = ramp('#f6c2a2', '#d89a7a', '#ffe0cc')
DERM = ramp('#f08a9a', '#c05a6a', '#ffb8c4')
FAT = ramp('#ffe9a8', '#e0c070', '#fff6d8')


def pen(cv, x, y, s, T, buzz=True):
    """The tattoo machine: grip, body, needle tip at (x, y)."""
    j = 6 * s * np.sin(T * 90) if buzz else 0
    line(cv, [(x, y + j), (x + 30 * s, y - 120 * s + j)], 8 * s, STEEL, ow=2, flat=False)
    cv.shape(capsule(x + 30 * s, y - 120 * s + j, x + 120 * s, y - 420 * s + j, 40 * s, 52 * s), (x - 60 * s, y - 500 * s, x + 200 * s, y - 60 * s), DARK)
    box(cv, x + 100 * s, y - 330 * s + j, 70 * s, 30 * s, ramp('#e2483d'), r=12 * s)
    line(cv, [(x + 120 * s, y - 420 * s + j), (x + 260 * s, y - 640 * s)], 10 * s, ramp('#3a3a44'), ow=2, flat=False)


def arm_skin(cv, x, y, w, h, drawn=1.0, blur=0.0, T=0.0):
    box(cv, x, y, w, h, SKIN, r=min(w, h) * 0.4)
    hs = 1.6
    outer = heart(x, y - 20, 300 * hs)
    k = drawn
    if k > 0:
        ring = subtract(outer, offset(outer, 0, 0, -16 - 30 * blur))
        clip = (lambda X, Y: X - (x - 260 + 520 * k)) if k < 1 else None
        f = ring if clip is None else inter(ring, clip)
        cv.shape(f, (x - 280, y - 260, x + 280, y + 260), INK, ow=0, shadow=0, flat=True, alpha=1 - 0.35 * blur)
        if blur > 0:
            cv.shape(subtract(offset(outer, 0, 0, 20 * blur), offset(outer, 0, 0, -60 * blur)), (x - 320, y - 300, x + 320, y + 300),
                     ramp('#4a5070'), ow=0, shadow=0, flat=True, alpha=0.3 * blur)


def layers(cv, y0=-200, w=1100, T=0.0):
    """Skin seen from the side: thin top layer, the deep layer, fat underneath."""
    box(cv, 0, y0 + 40, w, 40, EPI, r=10)
    box(cv, 0, y0 + 330, w, 250, DERM, r=10, ow=3)
    box(cv, 0, y0 + 760, w, 180, FAT, r=10, ow=3)
    return y0 + 80, y0 + 580


def b0_hook(lt, dur, T):
    """The needle is already buzzing and the outline is half drawn on frame one; before 0 it lowers in (the loop)."""
    k = np.clip(0.35 + lt / (dur * 1.6), 0.0, 1.0) if lt >= 0 else 0.35
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    arm_skin(cv, 0, 150, 700, 420, drawn=k)
    tip_x = -260 + 520 * k
    tip_y = 150 - 20 + 210 * np.sin(np.pi * max(k, 0.02)) * 0.0 - 200 + (0 if lt >= 0 else -200 * (1 - ease(np.clip((lt + 1) / 1, 0, 1))))
    pen(cv, tip_x, 130 if lt >= 0 else tip_y, 1.0, T, buzz=lt >= 0)
    if lt >= 0:
        for q in range(4):
            a = q * 1.6 + T * 20
            line(cv, [(tip_x + np.cos(a) * 30, 130 + np.sin(a) * 20), (tip_x + np.cos(a) * 60, 130 + np.sin(a) * 40)], 6, flat(hexc('#ffffff')), a=0.7)
        hook_text(cv, 'INKED', lt, y=-760, size=170, color=(255, 90, 80))
    return cv


def b1_speed(lt, dur, T):
    cv = Canvas(0, 0, 1.4)
    sky_bg(cv)
    top, deep = layers(cv, -100)
    j = abs(np.sin(lt * 40)) * 200
    line(cv, [(0, -700 + j), (0, -20 + j)], 12, STEEL, ow=3, flat=False)
    n = int(3000 * ease(np.clip(lt / (dur * 0.8), 0, 1)))
    badge(cv, f'{n:,} / MIN', y=-520, col=RED, w=380)
    return cv


def b2_layer(lt, dur, T):
    cv = Canvas(0, 0, 1.2)
    sky_bg(cv)
    top, deep = layers(cv, -200)
    k = np.clip(lt / (dur * 0.7), 0, 1)
    j = abs(np.sin(lt * 18)) * 220
    line(cv, [(-200 + 400 * k, -800 + j), (-200 + 400 * k, 20 + j)], 12, STEEL, ow=3, flat=False)
    for q in range(int(14 * k) + 1):
        x = -200 + 400 * q / 14
        disc(cv, x, 130 + 30 * np.sin(q * 2.1), 20, INK, ow=2)
    label(cv, 'TOP LAYER', 300, -230, 52, WHT)
    label(cv, 'INK LAYER', 300, 30, 52, WHT)
    return cv


def b3_cleanup(lt, dur, T):
    cv = Canvas(0, 0, 1.2)
    sky_bg(cv)
    layers(cv, -200)
    for q in range(10):
        disc(cv, -300 + q * 66, 130 + 30 * np.sin(q * 2.1), 20, INK, ow=2)
    for j in range(3):
        u = ease(np.clip((lt - j * 0.4) / 1.0, 0, 1))
        fighter(cv, -250 + j * 250, 520 - 330 * u, 80, T, seed=j)
    hook_text(cv, 'INVADER', lt, y=-720, size=150, pop_t=0.4, color=RED)
    return cv


def b4_swallow(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    fighter(cv, 0, 0, 220, T, seed=2)
    for q in range(8):
        a = q * 0.8
        r = 380 * (1 - k) + 70
        disc(cv, np.cos(a) * r, np.sin(a) * r * 0.8, 24, INK, ow=2)
    if k > 0.9:
        line(cv, [(-200, -300), (200, -260)], 14, flat(hexc('#e2483d')), ow=3)
        label(cv, "CAN'T BREAK IT", 0, -380, 56, RED)
    return cv


def b5_hold(lt, dur, T):
    z = 1.8 - 0.8 * ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, 150, z)
    sky_bg(cv)
    arm_skin(cv, 0, 150, 700, 420, drawn=1.0)
    if z > 1.2:
        for q in range(16):
            a = q * 2 * np.pi / 16
            px, py = np.cos(a) * 200, 150 + np.sin(a) * 160
            fighter(cv, px, py, 22, T, seed=q)
    hook_text(cv, 'INK IN YOUR CELLS', lt, y=-760, size=110, pop_t=dur * 0.45, color=YEL)
    return cv


def b6_relay(lt, dur, T):
    cv = Canvas(0, 0, 1.5)
    sky_bg(cv)
    cyc = (lt % 2.2) / 2.2
    if cyc < 0.45:
        fighter(cv, -150, 0, 150 * (1 - cyc), T, seed=1)
        for q in range(6):
            disc(cv, -150 + 40 * np.cos(q), 40 * np.sin(q), 18, INK, ow=2)
    else:
        u = (cyc - 0.45) / 0.55
        for q in range(6):
            disc(cv, -150 + (40 + 120 * (1 - u)) * np.cos(q) + 300 * u * 0.5, (40 + 120 * (1 - u)) * np.sin(q), 18, INK, ow=2)
        fighter(cv, 300 - 300 * u, 0, 150, T, seed=4)
    label(cv, 'NEW CELL', 0, -340, 70, (127, 210, 255))
    return cv


def b7_heal(lt, dur, T):
    k = np.clip(lt / (dur * 0.85), 0, 1)
    cv = Canvas(0, 0, 1.1)
    sky_bg(cv)
    top, deep = layers(cv, -100)
    meter(cv, 0, -560, 460, min(1, k * 3), GREEN, 'TOP: WEEKS')
    meter(cv, 0, -380, 460, k, ramp('#f08a9a'), 'DEEP: MONTHS')
    for q in range(10):
        disc(cv, -300 + q * 66, 230 + 30 * np.sin(q * 2.1), 20, INK, ow=2)
    return cv


def b8_blur(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    arm_skin(cv, 0, 150, 700, 420, drawn=1.0, blur=k)
    badge(cv, f'YEAR {1 + int(k * 29)}', y=-460, col=YEL)
    return cv


BEATS = [b0_hook, b1_speed, b2_layer, b3_cleanup, b4_swallow, b5_hold, b6_relay, b7_heal, b8_blur]

if __name__ == '__main__':
    run(BEATS)
