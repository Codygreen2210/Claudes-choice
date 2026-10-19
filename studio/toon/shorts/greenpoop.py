#!/usr/bin/env python3
"""Green poop. Opens on a guy staring down into a toilet with green water glowing up at him; loops back into it."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

BILE = ramp('#7fd34f', '#4f9a2a', '#c4f590')
LIVER = ramp('#a8443a', '#6e2622', '#d0706a')
BROWN = POOP


def mixr(a, b, t):
    return tuple(np.asarray(x) * (1 - t) + np.asarray(y) * t for x, y in zip(a, b))


def green_toilet(cv, T, glow=1.0, x=0, y=500, s=1.1):
    toilet(cv, x, y, s, T=T)
    cv.shape(rotell(x, y - 200 * s, 230 * s, 60 * s, 0), (x - 240 * s, y - 270 * s, x + 240 * s, y - 130 * s), ramp('#9be15d', '#5fa83a', '#d4ff9a'), ow=3, shadow=0)
    lump(cv, x - 40 * s, y - 200 * s, 40 * s, col=BILE)
    if glow > 0:
        cv.glow(rotell(x, y - 200 * s, 200 * s, 50 * s, 0), (x - 400, y - 600, x + 400, y), '#9be15d', 70, 0.35 * glow)


def b0_hook(lt, dur, T):
    """He's already leaning over the bowl, jolting back on frame one. Before 0: leaning in (the loop)."""
    jolt_ = jolt(lt, 0.0, 50) if lt >= 0 else 0.0
    lean = 1 - ease(np.clip(lt / 0.4, 0, 1)) * 0.5 if lt >= 0 else ease(np.clip((lt + 1.0) / 1.0, 0, 1))
    cv = Canvas(0, -60, 1.0)
    sky_bg(cv, ground=700, gcol='#c8ccd4')
    green_toilet(cv, T, x=180, y=700, s=0.95)
    guy(cv, -190, 700 + jolt_ * 0.3, 0.95, face='shock' if lt >= 0 else 'calm', arms=((40, 60), (40, 60)), tilt_head=0.6 * lean)
    for q in range(5):
        ph = (lt * 1.2 + q / 5) % 1
        line(cv, [(80 + q * 50, 420 - ph * 200), (90 + q * 50, 380 - ph * 200)], 7, flat(hexc('#9be15d')), a=1 - ph)
    if lt >= 0:
        hook_text(cv, 'GREEN', lt, y=-760, size=170, color=(155, 225, 93))
    return cv


def b1_bile(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    liver = smooth(60, rotell(-60, -120, 380, 200, -8), circle(220, -60, 150))
    cv.shape(liver, (-460, -340, 400, 120), LIVER)
    gb = rotell(80, 160, 70, 110, 20)
    cv.shape(gb, (0, 40, 160, 280), BILE, ow=4)
    for j in range(8):                                                   # bile trickling from liver into the gallbladder
        ph = (lt * 1.2 + j / 8) % 1
        disc(cv, 40 + 10 * np.sin(j), 0 + ph * 140, 12, BILE, ow=2, alpha=k)
    label(cv, 'LIVER', -150, -120, 80, WHT)
    label(cv, 'BILE', 240, 220, 80, (155, 225, 93), a=k)
    return cv


def b2_squirt(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 120)
    gb = rotell(-200, -260, 100, 150, 20)
    cv.shape(gb, (-320, -430, -80, -90), BILE, ow=4)
    line(cv, [(-160, -120), (-120, -40), (-120, 0)], 22, ramp('#c4f590'), ow=3, flat=False)
    for j in range(10):
        ph = (lt * 1.8 + j / 10) % 1
        disc(cv, -120 + ph * 300 + 20 * np.sin(j), 0 + ph * 150, 13, BILE, ow=2, alpha=1 - ph * 0.5)
    for j in range(3):
        u = (lt * 0.3 + j / 3) % 1
        cv.shape(rotell(-400 + u * 800, 120, 60, 30, 0), (-480 + u * 800, 80, -320 + u * 800, 160), ramp('#ffe9a8', '#e0c070', '#fff6d8'), ow=3)
    label(cv, 'BREAKS DOWN FAT', 120, -330, 50, WHT)
    return cv


def b3_ride(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 0, rings=[-500 + ((lt * 160) % 1000)], ring_k=0.5)
    x = -500 + lt * 120
    lump(cv, x, 0, 80, col=BILE)
    badge(cv, '1 DAY+', y=-340, col=YEL)
    return cv


def gradient_lumps(cv, lt, speed=120, n=5, x0=-900, x1=900, y=0, r=70):
    for j in range(n):
        x = x0 + ((lt * speed + j * (x1 - x0) / n) % (x1 - x0))
        t = np.clip((x - x0) / (x1 - x0), 0, 1)
        lump(cv, x, y, r, col=mixr(BILE, BROWN, t))


def b4_brown(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    tube(cv, 0, x0=-900, x1=900)
    gradient_lumps(cv, lt, 120)
    for j in range(5):
        germ(cv, -500 + j * 250, -110 + 40 * np.sin(lt * 3 + j), 30, T, seed=j, angry=False)
    label(cv, 'GERMS', 0, -320, 70, (127, 211, 79))
    return cv


def b5_fast(lt, dur, T):
    cv = Canvas(0, 0, 1.6)
    sky_bg(cv)
    rings = [-900 + ((lt * 900 + j * 450) % 1800) for j in range(4)]
    tube(cv, 0, rings=rings, ring_k=0.8)
    for j in range(4):
        x = -900 + ((lt * 1100 + j * 450) % 1800)
        lump(cv, x, 0, 65, col=BILE, squish=0.4)
    speed_lines(cv, T, 0.8, vertical=False)
    label(cv, 'TOO FAST', 0, -320, 80, RED)
    return cv


def b6_out(lt, dur, T):
    cv = Canvas(0, 100, 1.0)
    sky_bg(cv, ground=500, gcol='#c8ccd4')
    k = ease(np.clip((lt - 0.4) / 0.5, 0, 1))
    toilet(cv, 0, 500, 1.1, T=T)
    if k > 0:
        green_toilet(cv, T, glow=k)
    if lt < 0.9:
        u = lt / 0.9
        lump(cv, 0, -500 + 280 * u * u, 50, col=BILE)
    hook_text(cv, 'STILL GREEN', lt, y=-740, size=120, pop_t=0.9, color=(155, 225, 93))
    return cv


def b7_food(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    u1 = ease(np.clip(lt / 0.5, 0, 1)); u2 = ease(np.clip((lt - dur * 0.45) / 0.5, 0, 1))
    if u1 > 0:                                                           # spinach leaves
        for j in range(5):
            a = j * 1.25
            cv.shape(rotell(-260 + np.cos(a) * 80, -40 + np.sin(a) * 60, 110 * u1, 55 * u1, np.degrees(a)), (-450, -230, -70, 150),
                     ramp('#3fa84a', '#25703a', '#7fd88a'))
        label(cv, 'SPINACH', -260, 200, 64, WHT, a=u1)
    if u2 > 0:                                                           # cupcake with neon frosting
        box(cv, 260, 80 * u2, 110 * u2, 90 * u2, ramp('#f4c890', '#c49050', '#ffe8c0'), r=20)
        cv.shape(smooth(30, circle(260, -60, 120 * u2), circle(200, -20, 80 * u2), circle(320, -20, 80 * u2)), (100, -200, 420, 80),
                 ramp('#3fd84a', '#20a030', '#a0ffb0'))
        label(cv, 'FOOD DYE', 260, 230, 64, WHT, a=u2)
    return cv


def b8_burger(lt, dur, T):
    cv = Canvas(0, -40, 1.45)
    sky_bg(cv)
    bob = 10 * np.sin(lt * 3)
    BUN = ramp('#2b2b30', '#141418', '#4a4a52')
    cv.shape(smooth(40, rotell(0, -120 + bob, 300, 140, 0), rbox(0, -60 + bob, 300, 40, 30)), (-320, -270, 320, 0), BUN)
    box(cv, 0, 20 + bob, 320, 40, ramp('#7a4022', '#4e2414', '#a8603a'), r=30)
    box(cv, 0, 70 + bob, 330, 18, ramp('#7fd34f'), r=12)
    box(cv, 0, 130 + bob, 300, 50, BUN, r=30)
    for j in range(8):
        dot(cv, -200 + j * 55, -170 + bob + 20 * np.sin(j), 7, (np.full(3, 0.85, np.float32),) * 3)
    badge(cv, '2015', y=-390, col=(255, 160, 60))
    hook_text(cv, 'GREEN POOP', lt, y=-760, size=130, pop_t=dur * 0.5, color=(155, 225, 93))
    return cv


BEATS = [b0_hook, b1_bile, b2_squirt, b3_ride, b4_brown, b5_fast, b6_out, b7_food, b8_burger]

if __name__ == '__main__':
    run(BEATS)
