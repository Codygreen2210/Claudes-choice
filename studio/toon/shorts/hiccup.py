#!/usr/bin/env python3
"""Hiccups. Opens on a guy jolting mid-hiccup; loops back into the jolt."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403


def b0_hook(lt, dur, T):
    """HIC: the jolt lands on frame one. Before 0 he's breathing easy (the loop)."""
    dy = jolt(lt, 0.0, 70) + (jolt(lt, 2.0, 50) if lt > 0 else 0)
    cv = Canvas(0, -420, 1.55)
    sky_bg(cv, ground=0)
    hit = 0 <= lt < 0.6 or 2.0 <= lt < 2.5
    guy(cv, 0, dy, 1.0, face='shock' if hit else 'calm', arms=((25, 40), (25, 40)) if hit else ((12, 0), (12, 0)))
    if lt >= 0:
        for j, t0 in enumerate((0.0, 2.0)):
            u = lt - t0
            if 0 <= u < 0.5:
                for k in range(6):
                    a = -np.pi / 2 + (k - 2.5) * 0.35
                    r0 = 140 + 300 * u
                    line(cv, [(np.cos(a) * r0, -720 + np.sin(a) * r0), (np.cos(a) * (r0 + 60), -720 + np.sin(a) * (r0 + 60))], 9,
                         flat(hexc('#ffffff')), a=1 - u * 2)
        hook_text(cv, 'HIC!', lt, y=-800, size=170, color=YEL)
    return cv


def b1_dia(lt, dur, T):
    cv = Canvas(0, 0, 1.25)
    sky_bg(cv)
    br = 0.5 + 0.5 * np.sin(lt * 2.4)
    top = chest(cv, 0, 0, 1.0, T, dia=0.35 * br, lung=br)
    k = ease(np.clip((lt - 0.8) / 0.4, 0, 1))
    if k > 0:
        arrows(cv, [((-330, top - 240), (-120, top - 20))], YEL, 12)
        label(cv, 'DIAPHRAGM', -120, top - 300, 70, YEL, a=k)
    return cv


def b2_bugged(lt, dur, T):
    cv = Canvas(0, 60, 1.0)
    sky_bg(cv)
    inn = stomach(cv, 120, 420, 0.9, T, acid=0.55)
    for k in range(12):                                                # fizz shooting up
        ph = (lt * 1.4 + k / 12) % 1
        disc(cv, 40 + 60 * np.sin(k * 2.1), 420 - ph * 420, 12 + 6 * (k % 3), ramp('#fff4d0'), ow=2, alpha=1 - ph)
    tw = np.clip((lt - dur * 0.5) / 0.3, 0, 1)
    pts = [(u * 420, -60 - 80 * (1 - u * u / 1) + tw * 14 * np.sin(T * 60) * (1 - u * u)) for u in np.linspace(-1, 1, 21)]
    line(cv, pts, 36, MUSC, ow=4, flat=False)
    if tw > 0:
        cv.glow(circle(0, -140, 60), (-300, -340, 300, 60), '#ff4a3a', 50, 0.7 * tw)
        for k in range(5):
            a = k * 1.2 + lt * 4
            line(cv, [(np.cos(a) * 120, -140 + np.sin(a) * 70), (np.cos(a) * 190, -140 + np.sin(a) * 110)], 8, flat(hexc('#ffd23f')), a=tw)
    box(cv, -330, -420, 70, 140, ramp('#e2483d'), r=30)                 # the soda can
    box(cv, -330, -540, 56, 18, STEEL, r=10)
    label(cv, 'TOO FAST', 0, -760, 96, RED)
    return cv


def b3_yank(lt, dur, T):
    sx_, sy_ = shake(lt, 0.25, 26, 0.5)
    cv = Canvas(sx_, sy_, 1.25)
    sky_bg(cv)
    d = ease(np.clip((lt - 0.2) / 0.12, 0, 1)) * (1 - 0.4 * ease(np.clip((lt - 1.2) / 1.0, 0, 1)))
    chest(cv, 0, 0, 1.0, T, dia=d, lung=0.3 + 0.7 * d, twitch=d)
    for k in range(8):                                                 # air rushing down the windpipe
        ph = (lt * 2.2 + k / 8) % 1
        disc(cv, 18 * np.sin(k * 3), -720 + ph * 420, 16, ramp('#bfeaff', '#7fd0ff', '#ffffff'), ow=2, alpha=d * (1 - ph * 0.5))
    if d > 0.5:
        arrows(cv, [((-400, 120), (-400, 330)), ((400, 120), (400, 330))], RED, 14)
    return cv


def b4_flap(lt, dur, T):
    shut = ease(np.clip((lt - dur * 0.55) / 0.08, 0, 1))
    sx_, sy_ = shake(lt, dur * 0.55, 30, 0.4)
    cv = Canvas(sx_, -220 + sy_, 1.2)
    sky_bg(cv)
    throat(cv, 0, 0, 1.4, shut=shut)
    for k in range(10):
        ph = (lt * 1.8 + k / 10) % 1
        y = -620 + ph * 520
        if shut > 0.5 and y > -360:
            y = -360 - 30 * np.sin(k)
        disc(cv, 30 * np.sin(k * 2.3), y, 16, ramp('#bfeaff', '#7fd0ff', '#ffffff'), ow=2)
    if shut < 0.5:
        label(cv, 'THE FLAP', 0, -700, 80, WHT)
    if shut > 0.9:
        cv.flash('#ffffff', 0.35 * max(0, 1 - (lt - dur * 0.6) / 0.15))
        hook_text(cv, 'HIC!', lt, y=-560, size=170, pop_t=dur * 0.6, color=YEL)
    return cv


def b5_door(lt, dur, T):
    cv = Canvas(0, -260, 1.4)
    sky_bg(cv)
    throat(cv, 0, 0, 1.4, shut=1.0)
    for k in range(14):
        ph = ((lt * 2.4 + k / 14) % 1)
        y = -720 + ease(ph) * 380
        disc(cv, 70 * np.sin(k * 2.3), y, 14, ramp('#bfeaff', '#7fd0ff', '#ffffff'), ow=2)
    ring = (lt * 2.4) % 1
    cv.shape(subtract(circle(0, -330, 60 + 260 * ring), circle(0, -330, 50 + 260 * ring)), (-340, -670, 340, 10), flat(hexc('#ffffff')),
             ow=0, shadow=0, flat=True, alpha=1 - ring)
    hook_text(cv, 'SLAM', lt, y=-720, size=130, pop_t=0.3, color=RED)
    return cv


def b6_womb(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    disc(cv, 0, 60, 430, ramp('#f6a5b4', '#d0708a', '#ffd0da'))
    disc(cv, 0, 60, 380, ramp('#ffe0e6', '#f0b8c4', '#fff4f6'), ow=0, shadow=0)
    dy = jolt(lt % 1.4, 0.2, 30)
    bx, by = 0, 60 + dy
    cv.shape(smooth(40, circle(bx - 60, by - 90, 130), rotell(bx + 60, by + 90, 140, 170, -30)), (bx - 220, by - 250, bx + 230, by + 290), SKIN)
    line(cv, [(bx - 70, by - 80), (bx - 40, by - 70)], 6, INKC)
    line(cv, [(bx + 120, by + 200), (bx + 260, by + 330)], 24, ramp('#f0b0c0'), ow=3, flat=False)
    if (lt % 1.4) > 0.2 and (lt % 1.4) < 0.6:
        label(cv, 'hic', 180, -180, 70, WHT)
    label(cv, 'BEFORE BIRTH', 0, -560, 84, YEL)
    return cv


def b7_minutes(lt, dur, T):
    cv = Canvas(0, -300, 1.2)
    sky_bg(cv, ground=0)
    gap = 0.6 + lt * 0.5
    dy = jolt(lt % gap, 0.05, 40 * max(0.1, 1 - lt / dur))
    guy(cv, 0, dy, 1.0, face='calm', arms=((12, 0), (12, 0)))
    badge(cv, f'{1 + int(lt / dur * 4)} MIN', y=-1050, col=(120, 255, 140))
    return cv


def b8_years(lt, dur, T):
    cv = Canvas(0, -300, 1.2)
    sky_bg(cv, ground=0)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    dy = jolt((lt * 1.0) % 0.9, 0.05, 45)
    hair = ramp('#c8c8c8', '#9a9a9a', '#f0f0f0') if k > 0.5 else HAIR
    guy(cv, 0, dy, 1.0, face='worried', hair=hair, glasses=k > 0.5, arms=((20, 30), (20, 30)))
    badge(cv, f'{int(68 * k)} YEARS', y=-1050, col=RED)
    return cv


BEATS = [b0_hook, b1_dia, b2_bugged, b3_yank, b4_flap, b5_door, b6_womb, b7_minutes, b8_years]

if __name__ == '__main__':
    run(BEATS)
