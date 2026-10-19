#!/usr/bin/env python3
"""Swallowing gum. Opens on the gum sliding down the throat; loops back into the gulp."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403


def gumball(cv, x, y, r, T=0.0, stretch=0.0, pale=0.0):
    col = GUMC if pale <= 0 else ramp('#ffc0e0', '#e090b8', '#ffe8f4')
    cv.shape(rotell(x, y, r * (1 + 0.35 * stretch), r * (1 - 0.2 * stretch), 8 * np.sin(T * 2)), (x - r * 1.6, y - r * 1.4, x + r * 1.6, y + r * 1.4), col, ow=4)


def gullet(cv, s=1.0):
    """Side view of the food pipe running down from the mouth."""
    box(cv, 0, 260, 120, 900, ramp('#f4b0b8', '#c97a86', '#ffd4da'), r=110)
    box(cv, 0, 260, 76, 900, ramp('#7a2a3a', '#4e1a26', '#9a4050'), r=70, ow=0, shadow=0)


def b0_hook(lt, dur, T):
    """GULP: the gum is already sliding down on frame one. Before 0: in the mouth, about to go (the loop)."""
    y = -520 + 900 * ease(np.clip((lt + 0.35) / 1.6, 0, 1))
    cv = Canvas(0, -60, 1.15)
    sky_bg(cv)
    gullet(cv)
    sq = 0.4 + 0.3 * np.sin(lt * 10)
    gumball(cv, 0, y, 62, T, stretch=-0.3)
    for sx in (-1, 1):                                                  # the pipe squeezing behind it
        cv.shape(rotell(sx * 85, y - 120, 40, 60 * sq, 0), (sx * 85 - 50, y - 190, sx * 85 + 50, y - 50), ramp('#f4b0b8', '#c97a86', '#ffd4da'), ow=3)
    if lt >= 0:
        hook_text(cv, 'GULP', lt, y=-760, size=170, color=(255, 127, 191))
    return cv


def b1_rubber(lt, dur, T):
    st = 0.5 + 0.5 * np.sin(lt * 3)
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    for sx in (-1, 1):
        hand(cv, sx * (180 + 220 * st), 520, 0.5, arm=False, spread=0.5)
    pts = [(-(160 + 220 * st) + u * 2 * (160 + 220 * st), 60 * np.sin(u * np.pi) * (1 - st)) for u in np.linspace(0, 1, 15)]
    line(cv, pts, 70 - 40 * st, GUMC, ow=4, flat=False)
    for sx in (-1, 1):
        gumball(cv, sx * (160 + 220 * st), 0, 70)
    hook_text(cv, "CAN'T BREAK IT", lt, y=-720, size=110, pop_t=0.4, color=(255, 127, 191))
    return cv


def b2_acid(lt, dur, T):
    cv = Canvas(0, 0, 1.1)
    sky_bg(cv)
    stomach(cv, 0, 100, 1.1, T, acid=0.6)
    bob = 20 * np.sin(lt * 3)
    gumball(cv, 60, 260 + bob, 60, T)
    if lt > dur * 0.5:
        hook_text(cv, 'NOTHING', lt, y=-720, size=140, pop_t=dur * 0.5, color=(155, 225, 93))
    return cv


def b3_flavor(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, 0, 1.1)
    sky_bg(cv)
    stomach(cv, 0, 100, 1.1, T, acid=0.6)
    gumball(cv, 60, 260, 60, T, pale=k)
    for j in range(14):
        ph = (lt * 0.8 + j / 14) % 1
        a = j * 0.45
        r = 60 + ph * 260
        cv.shape(rbox(60 + np.cos(a) * r, 260 + np.sin(a) * r * 0.7, 9, 9, 2), (0, 0, 0, 0) if False else
                 (60 + np.cos(a) * r - 12, 260 + np.sin(a) * r * 0.7 - 12, 60 + np.cos(a) * r + 12, 260 + np.sin(a) * r * 0.7 + 12),
                 ramp('#ffffff', '#d8e4f4', '#ffffff'), ow=2, alpha=1 - ph)
    label(cv, 'SUGAR', 0, -330, 70, WHT)
    return cv


def b4_ride(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 0, rings=[-500 + ((lt * 300) % 1000)], ring_k=0.5)
    for j, (dx, col) in enumerate(((-300, SLOP), (-120, ramp('#7fbf4f')), (260, SLOP))):
        lump(cv, dx + lt * 70, 15 * np.sin(j + lt * 2), 55, col=col)
    gumball(cv, 80 + lt * 70, 0, 55, T, pale=1.0)
    return cv


def b5_myth(lt, dur, T):
    st = ease(np.clip((lt - dur * 0.45) / 0.12, 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    box(cv, 0, 0, 330, 330, ramp('#ffffff', '#d8dde4', '#ffffff'), r=30)
    box(cv, 0, -290, 330, 60, ramp('#e2483d'), r=24)
    label(cv, '7 YEARS', 0, 40, 150, (40, 40, 50))
    if st > 0:
        sc = 1 + 0.6 * (1 - st)
        cv.shape(rbox(0, 0, 360 * sc, 90 * sc, 20), (-400 * sc, -100 * sc, 400 * sc, 100 * sc), ramp('#e2483d'), ow=5, alpha=0.9 * st)
        label(cv, 'MYTH', 0, 20, 150 * sc, WHT, a=st)
    return cv


def b6_out(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.75), 0, 1))
    cv = Canvas(0, 120, 1.0)
    sky_bg(cv, ground=500, gcol='#c8ccd4')
    toilet(cv, 0, 500, 1.1, T=T)
    if lt > dur * 0.7:
        u = (lt - dur * 0.7) / 0.4
        gumball(cv, 0, min(-460 + 600 * u * u, 270), 50, T, pale=1.0)
    badge(cv, f'DAY {1 + int(k * 2)}', y=-620, col=(120, 255, 140))
    hook_text(cv, 'PLOP', lt, y=-760, size=140, pop_t=dur * 0.9, color=(255, 127, 191))
    return cv


def b7_lots(lt, dur, T):
    cv = Canvas(0, 0, 1.1)
    sky_bg(cv)
    stomach(cv, 0, 100, 1.1, T, acid=0.6)
    n = int(4 + 22 * ease(np.clip(lt / (dur * 0.8), 0, 1)))
    rng = np.random.default_rng(5)
    for j in range(n):
        gumball(cv, rng.uniform(-150, 200), rng.uniform(80, 360), rng.uniform(30, 48), T, pale=rng.uniform(0, 1) > 0.5)
    hook_text(cv, 'TOO MUCH', lt, y=-720, size=140, pop_t=dur * 0.4, color=RED)
    return cv


def b8_ball(lt, dur, T):
    pull = ease(np.clip((lt - dur * 0.4) / (dur * 0.5), 0, 1))
    cv = Canvas(0, 0, 1.4)
    sky_bg(cv)
    tube(cv, 0)
    bx = -60 - 330 * pull
    for j in range(9):
        a = j * 0.7
        gumball(cv, bx + np.cos(a) * 60, np.sin(a) * 60, 60, T, pale=j % 2)
    gumball(cv, bx, 0, 70, T)
    for sy in (-1, 1):                                                  # the doctor's grabber
        line(cv, [(bx + 70, sy * 50), (bx + 260, sy * 20), (bx + 900, sy * 14)], 16, STEEL, ow=3, flat=False)
    if pull < 0.1:
        label(cv, 'STUCK', 0, -300, 90, RED)
    return cv


BEATS = [b0_hook, b1_rubber, b2_acid, b3_flavor, b4_ride, b5_myth, b6_out, b7_lots, b8_ball]

if __name__ == '__main__':
    run(BEATS)
