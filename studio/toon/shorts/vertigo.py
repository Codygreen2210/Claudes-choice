#!/usr/bin/env python3
"""Vertigo (BPPV). Opens on him in bed, the whole room spinning; inside the inner ear: the pouch of ear rocks, the three
fluid loops, the hair tuft; rocks break loose, roll on after the head stops; ears vs eyes; the doctor's head moves roll
them back. Loops back into the spin.
Facts: Cleveland Clinic (BPPV page): calcium carbonate otoconia in the utricle break loose into the semicircular canals,
move the fluid, mixed signals cause vertigo; triggers include rolling over in bed; spells last up to a minute; a
canalith repositioning move (Epley) in the office."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

DIVE = {1: (540, 560), 9: (540, 900)}
NIGHT = ('#1c2238', '#0e1220')
GRN = (120, 255, 140)
FLUID = ramp('#7fd0ff', '#3fa9e0', '#bfeaff')
CANAL = ramp('#f6c0b0', '#c98a7a', '#ffe2d8')
POUCH = ramp('#f2a6b4', '#c06a80', '#ffd0da')
ROCK = ramp('#ffffff', '#c8d4e0', '#ffffff')
NERVE = ramp('#ffe14d', '#c8a020', '#fff4a0')
BED_Y, BED_S = 80, 1.0

def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


# ---------------------------------------------------------------- the inner ear (local units, s = 1 is about 700 px wide)
LOOPS = [((-150, -130), 175, 220, 0), ((165, -70), 200, 160, 25), ((30, 40), 270, 92, 0)]   # centre, rx, ry, deg
POUCH_C = (0, 225)
AMP = (-325, -60)            # the bulge at the base of loop A, where the hair tuft sits


def loop_pt(i, th, s=1.0, x=0, y=0):
    (cx, cy), rx, ry, dg = LOOPS[i]
    c, sn = np.cos(np.radians(dg)), np.sin(np.radians(dg))
    px, py = rx * np.cos(th), ry * np.sin(th)
    return x + (cx + px * c - py * sn) * s, y + (cy + px * sn + py * c) * s


def rock(cv, x, y, r, ang=0.0, a=1.0, glow=0.0):
    pts = [(x + r * np.cos(ang + k * np.pi / 3) * (1.0 if k % 2 == 0 else 0.7), y + r * np.sin(ang + k * np.pi / 3) * (1.0 if k % 2 == 0 else 0.7))
           for k in range(6)]
    if glow > 0:
        cv.glow(circle(x, y, r), (x - r * 3, y - r * 3, x + r * 3, y + r * 3), '#ffffff', 26, glow)
    cv.shape(poly(pts), pbox(pts, 4), ROCK, ow=3, alpha=a)


def inner_ear(cv, x, y, s, T, flow=0.0, bend=0.0, hot=None, pouch_rocks=12, label_loops=0.0, hair_glow=0.0):
    """flow: fluid particles moving round the loops (signed speed); bend: hair tuft lean (-1..1); hot: loop index lit up."""
    for i, ((cx, cy), rx, ry, dg) in enumerate(LOOPS):
        X, Y = x + cx * s, y + cy * s
        ring = subtract(rotell(X, Y, rx * s, ry * s, dg), rotell(X, Y, (rx - 52) * s, (ry - 52) * s, dg))
        bb = (X - (rx + 60) * s, Y - (rx + 60) * s, X + (rx + 60) * s, Y + (rx + 60) * s)
        if hot == i:
            cv.glow(ring, bb, '#7fd0ff', 40, 0.6 + 0.3 * np.sin(T * 8))
        cv.shape(ring, bb, CANAL, ow=4)
        inner = subtract(rotell(X, Y, (rx - 14) * s, (ry - 14) * s, dg), rotell(X, Y, (rx - 38) * s, (ry - 38) * s, dg))
        cv.shape(inner, bb, FLUID, ow=0, shadow=0, alpha=0.85)
        for k in range(9):                                            # fluid specks: they show which way it moves
            th = k * 2 * np.pi / 9 + T * flow * (1.0 + 0.2 * i)
            px, py = loop_pt(i, th, s, x, y)
            dot(cv, px, py, 6 * s, flat(hexc('#ffffff')), a=0.8)
    ax, ay = x + AMP[0] * s, y + AMP[1] * s                          # the bulge and its hair tuft
    cv.shape(circle(ax, ay, 70 * s), (ax - 80 * s, ay - 80 * s, ax + 80 * s, ay + 80 * s), CANAL, ow=4)
    cv.shape(circle(ax, ay, 52 * s), (ax - 60 * s, ay - 60 * s, ax + 60 * s, ay + 60 * s), FLUID, ow=0, shadow=0)
    if hair_glow > 0:
        cv.glow(circle(ax, ay, 40 * s), (ax - 120 * s, ay - 120 * s, ax + 120 * s, ay + 120 * s), '#ffe14d', 40, hair_glow)
    for k in range(7):
        bx = ax + (k - 3) * 11 * s
        tip = (bx + bend * 38 * s + 4 * s * np.sin(T * 6 + k), ay - 40 * s)
        line(cv, [(bx, ay + 30 * s), ((bx + tip[0]) / 2 + bend * 6 * s, ay - 6 * s), tip], 5 * s, flat(hexc('#ffe14d')))
    px, py = x + POUCH_C[0] * s, y + POUCH_C[1] * s                  # the pouch with its bed of ear rocks
    cv.shape(rotell(px, py, 210 * s, 120 * s, -6), (px - 230 * s, py - 140 * s, px + 230 * s, py + 140 * s), POUCH, ow=4)
    cv.shape(rotell(px, py + 40 * s, 170 * s, 46 * s, -6), (px - 190 * s, py - 20 * s, px + 190 * s, py + 100 * s), ramp('#e9d6ff', '#b39ad8', '#f6eeff'),
             ow=0, shadow=0, alpha=0.9)
    rr = np.random.default_rng(3)
    for k in range(pouch_rocks):
        rx_ = px + (-140 + 280 * (k + 0.5) / max(pouch_rocks, 1)) * s + rr.uniform(-8, 8) * s
        rock(cv, rx_, py + (12 + rr.uniform(-10, 10)) * s, 24 * s, rr.uniform(0, 6))
    line(cv, [(px + 180 * s, py + 70 * s), (px + 330 * s, py + 260 * s), (px + 360 * s, py + 520 * s)], 26 * s, NERVE, ow=3, flat=False)
    if label_loops > 0:
        slabel(cv, '3 LOOPS', 0, -700, 96, YEL, a=label_loops)


def eye(cv, x, y, r, look=0.0, a=1.0):
    cv.shape(ellipse(x, y, r, r * 0.62), (x - r, y - r, x + r, y + r), WHITE, ow=4, alpha=a)
    disc(cv, x + look * r * 0.3, y, r * 0.36, ramp('#4a8fd8', '#2a5a9a', '#8ac0ff'), ow=0, alpha=a)
    disc(cv, x + look * r * 0.3, y, r * 0.16, DARK, ow=0, shadow=0, alpha=a)


def bedroom(cv, T, face='calm'):
    cv.background(*NIGHT, vignette=0.35)
    box(cv, -360, -560, 120, 90, ramp('#3a4258', '#252b3c', '#4c5674'), r=12)          # nightstand + lamp glow
    cv.glow(circle(-360, -600, 30), (-520, -760, -200, -440), '#ffd58a', 60, 0.4)
    disc(cv, -360, -600, 34, ramp('#ffe0a0', '#d0a050', '#fff4d0'))
    box(cv, 0, BED_Y + 250 * BED_S, 430 * BED_S, 760 * BED_S, WOOD, r=40 * BED_S)
    box(cv, 0, BED_Y + 260 * BED_S, 400 * BED_S, 730 * BED_S, ramp('#d8dce8'), r=30 * BED_S)
    box(cv, 0, BED_Y - 380 * BED_S, 300 * BED_S, 110 * BED_S, ramp('#e8ecf4', '#c0c8d8', '#ffffff'), r=80 * BED_S)
    guy(cv, 0, BED_Y + 520 * BED_S, BED_S, face=face, legs=False, ground=False)
    box(cv, 0, BED_Y + 520 * BED_S, 390 * BED_S, 480 * BED_S, ramp('#4f7fd8', '#2f559a', '#8fb4ff'), r=60 * BED_S)
    for k in range(4):
        line(cv, [(-360, BED_Y + 150 + k * 220), (360, BED_Y + 170 + k * 220)], 6, flat(hexc('#2f559a')), a=0.5)


def spin_room(cv, T, ang, face='shock', blur=0):
    cv.background(*NIGHT, vignette=0.5)
    layer_xform(cv, lambda c: bedroom(c, T, face), 0, -260, angle=ang, blur=blur)
    for k in range(3):                                                # swirl lines round his head
        a0 = T * 5 + k * 2.1
        pts = [(np.cos(a0 + u) * (230 + 30 * k), -300 + np.sin(a0 + u) * (110 + 15 * k)) for u in np.linspace(0, 1.6, 9)]
        line(cv, pts, 10, flat(hexc('#ffffff')), a=0.7)


# ---------------------------------------------------------------- beats
def spin_angle(lt):
    """continuous across lt = 0 (the loop): a slow sway before, then the room lurches round"""
    return 14 * np.sin(lt * 2.0) + (38 * lt + 18 * np.sin(lt * 3.1) if lt > 0 else 0.0)


def b0_hook(lt, dur, T):
    cv = Canvas(0, -180, 1.15)
    rolled = lt > -0.5
    spin_room(cv, T, spin_angle(lt), face='shock' if rolled else 'closed', blur=int(12 * float(np.clip((lt + 0.5) / 0.5, 0, 1))))
    hook_text(cv, 'SPINNING', lt, y=-780, size=150, color=YEL, pop_t=-0.25 if lt < 0 else 0.0)      # pops in just before the loop, so frame one matches
    return cv


def b1_ear(lt, dur, T):
    k = ease(np.clip(lt / 0.8, 0, 1))
    cv = Canvas(0, 20, 0.95 + 0.15 * k)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    disc(cv, 0, 60, 640, SKIN, ow=0, shadow=0, alpha=0.18)
    inner_ear(cv, 0, 0, 1.0, T, flow=0.4)
    a = ease(np.clip((lt - 1.2) / 0.4, 0, 1))
    if a > 0:
        arrows(cv, [((260, -380), (60, 150))], YEL, 14)
        slabel(cv, 'EAR ROCKS', 0, -700, 110, YEL, a=a)
    return cv


def b2_up(lt, dur, T):
    cv = Canvas(0, 120, 1.35)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    tilt = 16 * np.sin(lt * 2.6)
    layer_xform(cv, lambda c: inner_ear(c, 0, 0, 1.0, T, flow=0.2, pouch_rocks=0), 0, 225, angle=tilt)
    px, py = 0, 225                                                   # rocks slide downhill as the head tips
    for k in range(10):
        u = (k + 0.5) / 10 - 0.5
        rock(cv, px + u * 260 + tilt * 5.0, py + 10 + u * 260 * np.sin(np.radians(tilt)), 26, k + lt, glow=0.25)
    x, y = W2(cv, 0, -560); arrows(cv, [((x, y + 60), (x, y - 100))], GRN, 16)
    slabel(cv, 'WHICH WAY IS UP', 0, -760, 96, GRN)
    return cv


def b3_loops(lt, dur, T):
    k = ease(np.clip(lt / 0.5, 0, 1))
    cv = Canvas(0, 20, 1.05 + 0.1 * k)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    hot = int(lt / max(dur, 0.1) * 3) % 3
    inner_ear(cv, 0, 0, 1.0, T, flow=0.6, hot=hot, label_loops=k)
    return cv


def b4_slosh(lt, dur, T):
    cv = Canvas(-260, -60, 1.8)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    turn = np.sin(np.clip(lt / max(dur, 0.1), 0, 1) * np.pi)
    bend = -0.9 * np.sin(lt * 3.2)
    inner_ear(cv, 0, 0, 1.0, T, flow=1.6 * np.cos(lt * 3.2), bend=bend, hair_glow=0.4 * abs(bend))
    slabel(cv, 'TINY HAIRS', 0, -720, 110, YEL, a=ease(np.clip((lt - 1.0) / 0.3, 0, 1)))
    del turn
    return cv


def b5_brain(lt, dur, T):
    cv = Canvas(0, -100, 0.95)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    inner_ear(cv, 0, 130, 0.6, T, flow=1.0, bend=0.6 * np.sin(lt * 4), hair_glow=0.5)
    brain(cv, 0, -560, 0.9, hot=0.0)
    path = [(216, 440), (300, 150), (200, -120), (60, -400)]
    line(cv, path, 18, NERVE, ow=3, flat=False)
    for j in range(3):                                                # signals running up the nerve
        u = (lt * 1.4 + j / 3) % 1
        i_ = min(int(u * 3), 2); w = u * 3 - i_
        pxy = (path[i_][0] + (path[i_ + 1][0] - path[i_][0]) * w, path[i_][1] + (path[i_ + 1][1] - path[i_][1]) * w)
        cv.glow(circle(*pxy, 16), (pxy[0] - 60, pxy[1] - 60, pxy[0] + 60, pxy[1] + 60), '#fff4a0', 30, 1.0)
        disc(cv, pxy[0], pxy[1], 16, NERVE, ow=0)
    meter(cv, *W2(cv, 0, -760), 420, 0.5 + 0.4 * np.sin(lt * 2.5), ramp('#7fd34f', '#4f9a2a', '#b6f08a'), 'TURN SPEED')
    return cv


ROLL_IN = [(-150 + 30 * k, 180 + 10 * (k % 2)) for k in range(4)]


def falling_rocks(cv, lt, s, x, y, T, k_fall, roll=0.0, n=4, glow=0.6):
    """k_fall 0..1: rocks drop from the pouch to the bottom of loop A; roll: radians along loop A after that"""
    for j in range(n):
        x0, y0 = x + (-60 + 40 * j) * s, y + 235 * s
        bx, by = loop_pt(0, np.pi / 2 + 0.25 * j - 0.3, s, x, y)
        kk = ease(np.clip(k_fall * 1.3 - j * 0.1, 0, 1))
        if roll != 0 and kk >= 1:
            bx, by = loop_pt(0, np.pi / 2 + 0.25 * j - 0.3 + roll, s, x, y)
        px = x0 + (bx - x0) * kk; py = y0 + (by - y0) * kk - 60 * s * np.sin(np.pi * kk)
        rock(cv, px, py, 28 * s, T * 4 + j, glow=glow)


def b6_loose(lt, dur, T):
    sx_, sy_ = shake(lt, 0.3, 22, 0.5)
    cv = Canvas(-80 + sx_, 40 + sy_, 1.3)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    kf = np.clip((lt - 0.4) / 1.6, 0, 1)
    inner_ear(cv, 0, 0, 1.0, T, flow=0.3, pouch_rocks=8, hot=0 if kf > 0.6 else None)
    falling_rocks(cv, lt, 1.0, 0, 0, T, kf)
    hook_text(cv, 'LOOSE!', lt, y=-760, size=140, pop_t=0.5, color=RED)
    return cv


def b7_rolling(lt, dur, T):
    cv = Canvas(-150, 40, 1.3)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    head = np.clip(lt / 1.0, 0, 1)                                    # head turns, then stops at 1 s; rocks keep going
    roll = 2.4 * (1 - np.exp(-lt * 0.9)) + 0.4 * lt
    stopped = lt > 1.0
    inner_ear(cv, 0, 0, 1.0, T, flow=1.2 * (1.0 if stopped else head), bend=-0.9, hair_glow=0.7, pouch_rocks=8, hot=0)
    falling_rocks(cv, lt, 1.0, 0, 0, T, 1.0, roll=-roll, glow=0.9)
    sbadge(cv, 'HEAD STOPPED' if stopped else 'HEAD TURNING', -760, GRN if stopped else YEL)
    if stopped:
        slabel(cv, 'ROCKS KEEP ROLLING', 0, -620, 84, RED, a=ease(np.clip((lt - 1.2) / 0.3, 0, 1)))
    return cv


def b8_fight(lt, dur, T):
    cv = Canvas(0, -100, 1.0)
    cv.background('#2a1730', '#120a18', vignette=0.4)
    hot = 0.35 + 0.35 * np.sin(lt * 9) ** 2
    sx_, sy_ = shake(lt % 0.8, 0.0, 10, 0.4)
    brain(cv, sx_, -520 + sy_, 1.0, hot=hot)
    inner_ear(cv, -260, 120, 0.42, T, flow=2.0, bend=-0.9, hair_glow=0.8)
    eye(cv, 260, 120, 120, look=0.0)
    for (fx, fy), col in (((-230, -20), (255, 90, 80)), ((260, 20), GRN)):
        arrows(cv, [((fx, fy), (fx * 0.3, -330))], col, 16)
    label(cv, 'SPINNING!', -300, -160, 74, RED)
    label(cv, 'STILL', 320, -130, 74, GRN, a=ease(np.clip((lt - 1.0) / 0.3, 0, 1)))
    return cv


def b9_ride(lt, dur, T):
    cv = Canvas(0, -180, 1.15)
    spin_room(cv, T, 70 * lt + 25 * np.sin(lt * 2.4), face='pain', blur=14)
    sec = int(np.clip(lt / max(dur, 0.1), 0, 1) * 60)
    sbadge(cv, f'0:{sec:02d}' if sec < 60 else '1:00', -760, YEL)
    return cv


def b10_fix(lt, dur, T):
    cv = Canvas(0, 40, 1.15)
    cv.background('#1d3a4a', '#0e1e28', vignette=0.35)
    steps = [0, 45, 90, 180]
    st = min(int(lt / max(dur, 0.1) * 4), 3); w = ease(np.clip((lt / max(dur, 0.1) * 4 - st) / 0.5, 0, 1))
    ang = steps[st - 1] + (steps[st] - steps[st - 1]) * w if st > 0 else steps[0]
    back = ease(np.clip(lt / max(dur, 0.1), 0, 1))
    layer_xform(cv, lambda c: inner_ear(c, 0, 0, 0.9, T, flow=0.4, pouch_rocks=8), 0, 0, angle=ang * 0.5)
    for j in range(4):                                                # the loose rocks roll back round into the pouch
        th = np.pi / 2 - 0.3 + 0.25 * j - (1 - back) * 1.8
        bx, by = loop_pt(0, th, 0.9)
        tx, ty = (-60 + 40 * j) * 0.9, 235 * 0.9
        kk = ease(np.clip(back * 1.6 - 0.6, 0, 1))
        rock(cv, bx + (tx - bx) * kk, by + (ty - by) * kk, 26, T * 3 + j, glow=0.6)
    sbadge(cv, f'MOVE {st + 1}', -760, GRN)
    if back > 0.85:
        slabel(cv, 'ROCKS BACK HOME', 0, -620, 90, GRN)
    return cv


BEATS = [b0_hook, b1_ear, b2_up, b3_loops, b4_slosh, b5_brain, b6_loose, b7_rolling, b8_fight, b9_ride, b10_fix]

if __name__ == '__main__':
    run(BEATS)
