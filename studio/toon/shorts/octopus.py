#!/usr/bin/env python3
"""Octopus. Opens on an octopus jetting straight at the camera; loops back into the jet."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403


def sea(cv):
    cv.background('#0f5a8a', '#3fb0e0', vignette=0.3)
    rng = np.random.default_rng(4)
    for k in range(14):
        x = rng.uniform(-700, 700); y = rng.uniform(-1100, 1100)
        disc(cv, cv.cx + x / cv.zoom, cv.cy + y / cv.zoom, rng.uniform(6, 14) / cv.zoom, ramp('#bfeaff'), ow=0, shadow=0, alpha=0.4)


def b0_hook(lt, dur, T):
    """It's already jetting at us on frame one; before 0 it bunches up (the loop)."""
    u = ease(np.clip((lt + 0.2) / 0.9, 0, 1))
    cv = Canvas(0, 0, 1.0)
    sea(cv)
    octopus(cv, 0, 180 - 220 * u, 0.95 + 0.35 * u, T, swim=1.0 - u * 0.6)
    bubbles(cv, T, -300, 300, 200, 900, n=20, speed=400, seed=2)
    if lt >= 0:
        hook_text(cv, '9 BRAINS', lt, y=-780, size=160, color=(255, 154, 136))
    return cv


def b1_brains(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, 60, 0.85)
    sea(cv)
    octopus(cv, 0, -100, 1.0, T, xray=0.6, brains=k)
    label(cv, '1 + 8', 0, -700, 110, YEL)
    return cv


def b2_arms(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sea(cv)
    pts = [(-500 + u * 900, 200 + 120 * np.sin(u * 5 + T * 2)) for u in np.linspace(0, 1, 16)]
    line(cv, pts, 70, OCTO, ow=5, flat=False)
    for j, p in enumerate(pts[2:14:2]):
        disc(cv, p[0], p[1] + 40, 22, ramp('#ffd0c8'), ow=2.5)
    disc(cv, pts[8][0], pts[8][1] - 10, 30, ramp('#ffd23f'), ow=3)
    box(cv, 380, -150, 70, 50, ramp('#f4f1ea'), r=10)                        # a shell it's checking
    for j, nm in enumerate(('TASTE', 'TOUCH', 'DECIDE')):
        u = ease(np.clip((lt - j * dur * 0.25) / 0.4, 0, 1))
        label(cv, nm, -300 + j * 300, -450, 70, WHT, a=u)
    return cv


def b3_hearts(lt, dur, T):
    cv = Canvas(0, 60, 0.85)
    sea(cv)
    octopus(cv, 0, -100, 1.0, T, xray=0.7, hearts=1.0)
    label(cv, 'GILLS', -330, -500, 54, WHT)
    label(cv, 'GILLS', 330, -500, 54, WHT)
    label(cv, 'BODY', 0, -600, 60, YEL)
    return cv


def b4_stops(lt, dur, T):
    cv = Canvas(0, 60, 0.85)
    sea(cv)
    sw = ease(np.clip((lt - 0.4) / 0.4, 0, 1))
    octopus(cv, 0, -100 - 200 * sw, 1.0, T, xray=0.7, hearts=1.0, swim=sw)
    if sw > 0.5:
        hook_text(cv, 'HEART STOPS', lt, y=-760, size=130, pop_t=dur * 0.45, color=RED)
    return cv


def b5_blue(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sea(cv)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    vessel(cv, 100, r=150)
    for j in range(10):
        x = -800 + ((lt * 260 + j * 170) % 1600)
        disc(cv, x, 100 + 30 * np.sin(j), 30, ramp('#3d7fd8', '#2a559a', '#7fb4ff') if k > 0.5 else ramp('#e2483d'), ow=3)
    badge(cv, 'COPPER', y=-360, col=(255, 160, 80))
    label(cv, 'NOT IRON', 0, -200, 60, WHT, a=k)
    return cv


def b6_color(lt, dur, T):
    cols = [OCTO, ramp('#f4d070', '#c0a040', '#fff0b0'), ramp('#7a8a5a', '#4a5a3a', '#a8b880'), ramp('#e8e0d8', '#b0a898', '#ffffff')]
    c = cols[int(lt * 3) % len(cols)]
    cv = Canvas(0, 60, 0.9)
    sea(cv)
    octopus(cv, 0, 0, 0.9, T, col=c)
    badge(cv, 'UNDER 1 SEC', y=-640, col=YEL)
    return cv


def b7_dna(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sea(cv)
    for i in range(16):                                                     # a twisting DNA ladder, pieces swapping
        y = -500 + i * 66
        ph = lt * 2 + i * 0.5
        xa, xb = 160 * np.sin(ph), -160 * np.sin(ph)
        line(cv, [(xa, y), (xb, y)], 10, ramp(['#ffd23f', '#3fbf6a', '#3d7fd8', '#e2483d'][(i + int(lt * 2) * (i % 3 == 0)) % 4]), ow=2, flat=False)
        disc(cv, xa, y, 16, ramp('#ffffff'), ow=2.5)
        disc(cv, xb, y, 16, ramp('#ffffff'), ow=2.5)
    hook_text(cv, 'SHUFFLED', lt, y=-760, size=140, pop_t=0.5, color=YEL)
    return cv


def b8_jar(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sea(cv)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    box(cv, 0, 150, 220, 260, ramp('#bfe6ff', '#7fb6d9', '#eaf7ff'), r=40, alpha=0.6)        # the jar
    lid_a = np.radians(720 * k)
    cv.shape(rbox(0 + 300 * k, -140 - 200 * k, 230, 40, 14), (-240 + 300 * k, -190 - 200 * k, 240 + 300 * k, -90 - 200 * k), ramp('#e2483d'))
    octopus(cv, 0, 120 - 80 * k, 0.45, T)
    if k > 0.95:
        hook_text(cv, 'ESCAPED', lt, y=-760, size=150, pop_t=dur * 0.6, color=(255, 154, 136))
    return cv


BEATS = [b0_hook, b1_brains, b2_arms, b3_hearts, b4_stops, b5_blue, b6_color, b7_dna, b8_jar]

if __name__ == '__main__':
    run(BEATS)
