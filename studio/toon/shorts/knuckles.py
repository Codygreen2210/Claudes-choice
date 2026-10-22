#!/usr/bin/env python3
"""Does cracking your knuckles cause arthritis? Opens on a big hand mid-crack, POP bursts popping across the knuckles;
loops back into it (the last line plays over the hand flexing, getting ready)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

WALLC = ('#d8e4c8', '#b0c4a0')
FLUID = ramp('#fff2b0', '#e8d080', '#fffbe0')
CAPS = ramp('#f4b0b8', '#c97a86', '#ffd4da')
GOLD = ramp('#ffd23f', '#c89a10', '#fff08a')
POPC = (255, 236, 80)
HX, HY, HS = 0, 720, 1.6                              # the big hand: wrist at (0, 720)


def knuckle_pos(name, x=HX, y=HY, s=HS):
    for n, bx, L, r, lean in FINGERS:
        if n == name:
            return x + bx * s, y - 385 * s
    return x, y


def burst(cv, x, y, k, size=1.0):
    """A cartoon POP: yellow spikes flying out, then gone (k 0..1)."""
    if not 0 < k < 1:
        return
    for j in range(8):
        a = j * np.pi / 4 + 0.2
        r0, r1 = (30 + 60 * k) * size, (60 + 110 * k) * size
        line(cv, [(x + np.cos(a) * r0, y + np.sin(a) * r0), (x + np.cos(a) * r1, y + np.sin(a) * r1)], 10 * size, flat(hexc('#ffe14d')), a=1 - k)


def wall(cv, T):
    """His wall: a LIKE & SUBSCRIBE poster, a clock and a framed bell (Easter eggs)."""
    cv.background(*WALLC, vignette=0.25)
    sub_poster(cv, -400, -560, 0.8, T=T)
    box(cv, 400, -570, 100, 100, WOOD, r=8)
    box(cv, 400, -570, 84, 84, ramp('#2a3a6a', '#1a2448', '#4a5a9a'), r=4, ow=0, shadow=0)
    bell_icon(cv, 400, -588, 52)
    label(cv, 'HIT THE BELL', 400, -508, 20, (255, 236, 80), stroke=2)


def cracking(cv, lt, T, x=HX, y=HY, s=HS, start=-0.15, xray=0.0, fx=True):
    """The hand popping one knuckle after another (from `start`), with a little jolt on each pop."""
    names = ['index', 'middle', 'ring', 'pinky']
    t = lt - start
    jolt_ = 0.0
    if t > 0:
        i = int(t / 0.32) % 4
        k = (t % 0.32) / 0.32
        jolt_ = -10 * np.exp(-k * 8)
    hand(cv, x, y + jolt_, s, spread=1.0 + 0.15 * np.sin(T * 3), xray=xray)
    if t > 0:
        bx, by = knuckle_pos(names[i], x, y + jolt_, s)
        if fx:
            pop_fx(cv, bx, by, k, s)
        return bx, by, k
    return None


def pop_fx(cv, bx, by, k, s):
    burst(cv, bx, by, k, size=s / 1.6)
    if k < 0.6:
        label(cv, 'POP', bx, by - 150 * s / 1.6, int(70 * s / 1.6), POPC)


def joint(cv, x, y, s, gap=0.0, bubble=0.0, T=0.0):
    """Cross-section of a knuckle: two bone ends in a pink capsule full of fluid; gap pulls them apart, bubble grows."""
    cv.shape(ellipse(x, y, 230 * s, (200 + 60 * gap) * s), (x - 240 * s, y - 270 * s, x + 240 * s, y + 270 * s), CAPS, ow=4)
    cv.shape(ellipse(x, y, 205 * s, (175 + 60 * gap) * s), (x - 210 * s, y - 240 * s, x + 210 * s, y + 240 * s), FLUID, ow=0, shadow=0)
    g = (30 + 120 * gap) * s
    for sy in (-1, 1):                                                          # the two bone ends
        cy = y + sy * (g + 260 * s)
        cv.shape(smooth(40 * s, rbox(x, cy + sy * 120 * s, 90 * s, 220 * s, 60 * s), ellipse(x, y + sy * (g + 70 * s), 150 * s, 80 * s)),
                 (x - 160 * s, min(y + sy * g, cy + sy * 340 * s) - 10, x + 160 * s, max(y + sy * g, cy + sy * 340 * s) + 10), BONEC)
    if bubble > 0:
        disc(cv, x + 10 * np.sin(T * 5) * s, y, 70 * bubble * s, ramp('#ffffff', '#d8e8f8', '#ffffff'), ow=3, alpha=0.95)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    wall(cv, T)
    cracking(cv, lt, T)
    if lt >= -0.3:
        hook_text(cv, 'POP!', lt + 0.3, y=-780, size=200, color=POPC)
    return cv


def b1_warning(lt, dur, T):
    """Mom wags her finger: YOU'LL GET ARTHRITIS!"""
    cv = Canvas(0, 0, 1.0)
    wall(cv, T)
    wag = 22 * np.sin(T * 9)
    guy(cv, -120, 900, 1.3, woman=True, face='worried', arms=((12, 0), (150 + wag * 0.3, 10)), shirt=ramp('#d84a8a', '#a02a60', '#ff8ac0'), hair=ramp('#7a4a2a', '#4a2a16', '#a86a40'))
    box(cv, 230, -270, 250, 110, ramp('#ffffff', '#d8dde4', '#ffffff'), r=50)
    cv.shape(poly([(80, -180), (140, -170), (60, -120)]), (55, -185, 145, -115), ramp('#ffffff', '#d8dde4', '#ffffff'), ow=4, shadow=0)
    label(cv, "YOU'LL GET", 230, -300, 54, (40, 34, 50), stroke=0)
    label(cv, 'ARTHRITIS!', 230, -230, 66, (200, 40, 40), stroke=0)
    doormat(cv, 300, 820, 0.9)
    return cv


def b2_inside(lt, dur, T):
    """Inside the knuckle: two bone ends and a pocket of slippery fluid."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1828', '#1a0a12', vignette=0.4)
    joint(cv, 0, -200, 1.2, T=T)
    for q in range(6):                                                          # the fluid sloshing
        a = T * 1.5 + q
        disc(cv, np.cos(a) * 160, -200 + np.sin(a * 1.3) * 40, 10, ramp('#ffffff'), ow=0, shadow=0, alpha=0.6)
    label(cv, 'FLUID', 330, -200, 60, (255, 242, 176))
    label(cv, 'BONE', -330, -520, 54, (240, 230, 210)); label(cv, 'BONE', -330, 140, 54, (240, 230, 210))
    neon_sign(cv, 0, 720, 'SUBSCRIBE', '#ff3a6a', T)
    return cv


def b3_bubble(lt, dur, T):
    """Pull the bones apart: pressure drops, a gas bubble forms with a POP."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1828', '#1a0a12', vignette=0.4)
    k = ease(float(np.clip(lt / (dur * 0.55), 0, 1)))
    pop_t = dur * 0.6
    joint(cv, 0, -200, 1.2, gap=k, bubble=min(1, k * 1.2), T=T)
    for sy in (-1, 1):
        arrows(cv, [((0, -200 + sy * 330), (0, -200 + sy * 470))], POPC, 14)
    meter(cv, 0, 230, 480, 1 - 0.8 * k, GOLD if k < 0.6 else ramp('#e2483d'), 'PRESSURE')
    burst(cv, 0, -200, (lt - pop_t) / 0.5, 1.4)
    if lt > pop_t:
        hook_text(cv, 'POP!', lt, y=-780, size=200, pop_t=pop_t, color=POPC)
    xray_tag(cv, 360, 720, ('JOINT:', 'SUBSCRIBED'))
    return cv


def b4_wait(lt, dur, T):
    """Try again too soon: nothing. A timer runs to 30 minutes."""
    cv = Canvas(0, 0, 1.0)
    wall(cv, T)
    hand(cv, -130, 900, 1.15)
    k = float(np.clip(lt / (dur * 0.85), 0, 1))
    mins = int(30 * k)
    cx, cy = 290, -170
    disc(cv, cx, cy, 150, ramp('#ffffff', '#d8dde4', '#ffffff'))
    cv.shape(poly([(cx, cy)] + [(cx + np.sin(a) * 140, cy - np.cos(a) * 140) for a in np.linspace(0, 2 * np.pi * k, 30)]) if k > 0.02 else circle(cx, cy, 1),
             (cx - 150, cy - 150, cx + 150, cy + 150), ramp('#ffd23f'), ow=0, shadow=0, alpha=0.8)
    dot(cv, cx, cy, 10)
    badge(cv, f'{mins} MIN', y=40, x=cx, col=(255, 236, 80), w=240)
    if (lt % 1.0) < 0.5 and k < 0.8:
        label(cv, 'NOPE', -130, -260, 80, (255, 90, 80))
    if k > 0.95:
        hook_text(cv, 'WAIT', lt, y=-780, size=180, pop_t=dur * 0.82, color=(255, 236, 80))
    return cv


def b5_doctor(lt, dur, T):
    """A doctor with a clipboard and a question mark. His diploma is from Subscribe University."""
    cv = Canvas(0, 0, 1.0)
    wall(cv, T)
    box(cv, 330, -290, 120, 90, WOOD, r=6)
    box(cv, 330, -290, 104, 74, ramp('#fffdf4'), r=4, ow=0, shadow=0)
    label(cv, 'DIPLOMA', 330, -320, 24, (40, 34, 50), stroke=0)
    label(cv, 'SUBSCRIBE U.', 330, -270, 24, (200, 40, 40), stroke=0)
    guy(cv, -60, 900, 1.25, face='calm', coat=True, glasses=True, shirt=COAT, arms=((12, 0), (40, 70)), hair=ramp('#a0a0a8', '#707078', '#d0d0d8'), look=(0.5, -0.5))
    box(cv, 130, 230, 70, 90, ramp('#c8a070'), r=8)
    box(cv, 130, 240, 58, 70, ramp('#ffffff'), r=4, ow=0, shadow=0)
    label(cv, '?', 120, -560 + 10 * np.sin(T * 3), 200, (255, 236, 80))
    return cv


def two_hands(cv, lt, T, crack=True):
    """Left hand (cracked) and right hand (never), side by side."""
    fxp = None
    if crack:
        fxp = cracking(cv, (lt % 1.28), T, x=-270, y=760, s=1.0, start=0.0, fx=False)
    else:
        hand(cv, -270, 760, 1.0)
    cv.img[:, :540] = cv.img[:, :540][:, ::-1].copy()                           # mirror it into a LEFT hand
    if fxp:
        pop_fx(cv, -540 - fxp[0], fxp[1], fxp[2], 1.0)
    hand(cv, 270, 760, 1.0)
    label(cv, 'LEFT', -270, -310, 64, (255, 236, 80))
    label(cv, 'RIGHT', 270, -310, 64, (255, 255, 255))


def b6_experiment(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background(*WALLC, vignette=0.25)
    two_hands(cv, lt, T)
    k = float(np.clip(lt / (dur * 0.85), 0, 1))
    badge(cv, f'{int(50 * k)}+ YEARS', y=-660, col=(255, 236, 80), w=420)
    label(cv, '2X A DAY', -270, -440, 48, (200, 40, 40))
    label(cv, 'NEVER', 270, -440, 48, (60, 60, 80))
    sticky(cv, 0, -420, 0.6, ['LIKE', '+ SUB'])
    return cv


def b7_count(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background(*WALLC, vignette=0.25)
    two_hands(cv, lt, T, crack=False)
    k = ease(float(np.clip(lt / (dur * 0.5), 0, 1)))
    badge(cv, f'{int(round(36500 * k)):,} CRACKS', y=-660, col=(255, 236, 80), w=640)
    if lt > dur * 0.55:
        for x in (-270, 270):                                                   # no arthritis in either hand
            disc(cv, x, -470, 60, ramp('#3fbf6a', '#25804a', '#7fe8a0'))
            line(cv, [(x - 28, -470), (x - 6, -446), (x + 30, -496)], 14, flat(hexc('#ffffff')))
        hook_text(cv, 'NO ARTHRITIS', lt, y=-800, size=120, pop_t=dur * 0.6, color=(127, 255, 160))
    return cv


def b8_prize(lt, dur, T):
    """The doctor with a gold trophy, confetti falling."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1a4a', '#14102a', vignette=0.35)
    guy(cv, -170, 900, 1.15, face='happy', coat=True, glasses=True, shirt=COAT, arms=((12, 0), (150, 15)), hair=ramp('#a0a0a8', '#707078', '#d0d0d8'))
    tx, ty = 160, -300
    cv.shape(smooth(30, inter(circle(tx, ty - 60, 130), lambda X, Y: Y - (ty - 60)), rbox(tx, ty + 40, 30, 80, 10), rbox(tx, ty + 130, 90, 26, 10)),
             (tx - 135, ty - 75, tx + 135, ty + 160), GOLD)
    for sx in (-1, 1):
        cv.shape(subtract(circle(tx + sx * 140, ty - 20, 50), circle(tx + sx * 140, ty - 20, 30)), (tx + sx * 140 - 52, ty - 72, tx + sx * 140 + 52, ty + 32), GOLD, ow=3)
    box(cv, tx, ty + 130, 86, 22, ramp('#3a2a10'), r=6, ow=0, shadow=0)
    label(cv, 'IG NOBEL 2009', tx, ty + 137, 22, (255, 220, 120), stroke=0)
    label(cv, 'MOST LIKED', tx, ty - 10, 26, (140, 100, 10), stroke=0)
    rng = np.random.default_rng(9)
    for q in range(40):                                                         # confetti
        x = -540 + (q * 131) % 1080
        y = -960 + ((T * 300 + q * 197) % 1920)
        box(cv, x, y, 10, 6, [GOLD, SUBRED, ramp('#3fa9ff'), ramp('#3fbf6a')][q % 4], r=2, shadow=0)
    hook_text(cv, 'PRIZE', lt, y=-780, size=180, pop_t=dur * 0.3, color=(255, 214, 63))
    return cv


# the cut that goes INSIDE: into a knuckle (screen px)
DIVE = {2: (540 + int(FINGERS[1][1] * HS), int(960 + HY - 385 * HS))}

BEATS = [b0_hook, b1_warning, b2_inside, b3_bubble, b4_wait, b5_doctor, b6_experiment, b7_count, b8_prize]

if __name__ == '__main__':
    run(BEATS)
