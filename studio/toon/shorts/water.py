#!/usr/bin/env python3
"""What happens when you drink too much water. Opens mid-chug: a gallon jug tipped up at his mouth, water glugging down,
spilling down his chin; loops back into it (the last line plays over him grabbing the jug off the bench)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

JUG = ramp('#e8f6ff', '#a8cce4', '#ffffff')
WAT = ramp('#5ac0ff', '#2a8ad0', '#a8e4ff')
CAP = ramp('#3d7fd8', '#2a559a', '#7fb4ff')
KID = ramp('#b8404e', '#7a2030', '#e47a88')
SALT = ramp('#ffffff', '#cfd8e2', '#ffffff')
CELLW = ramp('#ffb0c4', '#d87090', '#ffd8e4')
BONE = ramp('#f4ecd8', '#cbbf9e', '#ffffff')
TILE = ('#d8e8ec', '#b0c8d0')
LOCK = ramp('#5a8ab8', '#3a6a98', '#7aaad8')
GX, GY, GS = -60, 960, 1.5
MOUTH_L = (0, -708)
DRINK = (90, -700)                              # where his hand holds the jug up (guy units)


def jug(cv, x, y, s, tilt=0.0, level=1.0, T=0.0):
    """A gallon jug held by its handle at (x, y); tilt in radians tips the spout toward the left (his mouth)."""
    c, sn = np.cos(tilt), np.sin(tilt)
    R = lambda dx, dy: (x + (dx * c - dy * sn) * s, y + (dx * sn + dy * c) * s)
    body = [R(-90, -40), R(90, -40), R(90, 220), R(-90, 220)]
    cv.shape(smooth(30 * s, poly(body), circle(*R(-40, -60), 40 * s)), bbox_of(body + [R(-40, -110)], 50 * s), JUG, alpha=0.75)
    if level > 0.02:                                                           # the water inside (level stays flat-ish)
        top = 220 - 250 * level
        wpts = [R(-82, max(top, -30)), R(82, max(top, -30)), R(82, 212), R(-82, 212)]
        cv.shape(poly(wpts), bbox_of(wpts, 6), WAT, ow=0, shadow=0, alpha=0.8)
    sp = R(-40, -110)
    cv.shape(capsule(*R(-40, -70), *sp, 22 * s), bbox_of([R(-40, -70), sp], 26 * s), JUG, alpha=0.8)
    disc(cv, *sp, 24 * s, CAP)
    label(cv, '1 GAL', *R(10, 120), int(36 * s), (40, 80, 140), stroke=0)


def gym(cv, T):
    """A gym locker room: tiles, lockers (one with a little LIKE sticker: the Easter egg), a bench."""
    cv.background(*TILE, vignette=0.25)
    for k in range(-6, 7):
        line(cv, [(k * 95, -960), (k * 95, 960)], 3, flat(hexc('#a8c0c8')), a=0.6)
    for k in range(-10, 11):
        line(cv, [(-560, k * 95), (560, k * 95)], 3, flat(hexc('#a8c0c8')), a=0.6)
    for i, x in enumerate((240, 360, 480)):
        box(cv, x, -380, 55, 300, LOCK, r=8)
        for v in range(4):
            line(cv, [(x - 30, -620 + v * 18), (x + 30, -620 + v * 18)], 4, flat(hexc('#2a4a70')), a=0.7)
        box(cv, x + 38, -380, 6, 26, STEEL, r=3, shadow=0)
    thumb_icon(cv, 360, -470, 26)                                              # sticker on the middle locker
    box(cv, 0, 620, 700, 340, ramp('#8a9aa8', '#5a6a78', '#aab8c4'), r=0, ow=0, shadow=0)


def drinker(cv, lt, T, k=1.0, chug=1.0, face='hold', tint=None):
    right = reach_move(1, k, DRINK)
    guy(cv, GX, GY, GS, face=face, arms=((12, 0), right), shirt=ramp('#e2483d', '#a82a26', '#ff8070'), tint=tint)
    H = front_arm(cv, GX, GY, GS, 1, *right, shirt=ramp('#e2483d', '#a82a26', '#ff8070'))
    return H


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """lt < 0: he grabs the jug off the bench and swings it up. From lt = -0.3 he's chugging; frame one is mid-gulp."""
    cv = Canvas(0, 0, 1.0)
    gym(cv, T)
    k = ease(float(np.clip((lt + 2.2) / 1.9, 0, 1)))
    chug = lt > -0.3
    H = drinker(cv, lt, T, k=k, face='hold' if chug else 'calm')
    tilt = -1.9 * k
    level = 1.0 if not chug else max(0.35, 0.95 - 0.12 * (lt + 0.3))
    jug(cv, H[0] + 40, H[1] - 20, 0.9, tilt=tilt, level=level, T=T)
    if chug:
        mx, my = GX + MOUTH_L[0] * GS, GY + MOUTH_L[1] * GS
        for q in range(5):                                                     # glug bubbles rising in the jug, spill down his chin
            ph = (T * 2.5 + q / 5) % 1
            disc(cv, H[0] + 80 + 20 * np.sin(q * 3), H[1] - 40 - 150 * ph, 8 + 6 * (q % 2), ramp('#ffffff'), ow=1.5, shadow=0, alpha=0.8 * (1 - ph))
            drop(cv, mx - 30 + 20 * q % 50, my + 40 + 140 * ph, 10, a=1 - ph)
        hook_text(cv, '1 GALLON', lt + 0.3, y=-800, size=160, color=(90, 192, 255))
    return cv


def kidney(cv, x, y, s, side):
    f = subtract(rotell(x, y, 105 * s, 165 * s, 0), circle(x - side * 118 * s, y, 58 * s))
    cv.shape(f, (x - 130 * s, y - 185 * s, x + 130 * s, y + 185 * s), KID)


def b1_kidneys(lt, dur, T):
    """Water pours in through a fat pipe, the kidneys let out only a trickle: 1 liter an hour."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1828', '#1a0a12', vignette=0.4)
    line(cv, [(-500, -640), (-200, -640), (0, -480)], 90, ramp('#3a6a98'), ow=4, flat=False)   # the pipe in
    for q in range(10):
        ph = (lt * 1.6 + q / 10) % 1
        x = -500 + 500 * ph; y = -640 + 160 * max(0, ph - 0.6) / 0.4
        disc(cv, x, y, 18, WAT, ow=2, shadow=0)
    kidney(cv, -200, -150, 1.0, -1)
    kidney(cv, 200, -150, 1.0, 1)
    for sx in (-1, 1):
        line(cv, [(sx * 120, -120), (sx * 60, 120), (0, 200)], 18, ramp('#ffe066', '#d0a820', '#fff2a8'), ow=3, flat=False)
    ph = (lt * 0.6) % 1                                                        # just a trickle out
    drop(cv, 0, 230 + 80 * ph, 14, a=1 - ph)
    badge(cv, '1 LITER / HOUR', y=-800, col=(255, 236, 80), w=560)
    return cv


def b2_flood(lt, dur, T):
    """Inside a blood vessel: water drops pour in faster and faster, shoving the red cells apart."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a0a14', '#1a0408', vignette=0.4)
    vessel(cv, -150, x0=-800, x1=800, r=230)
    k = float(np.clip(lt / (dur * 0.8), 0, 1))
    for q in range(7):
        x = -700 + ((T * 260 + q * 210) % 1400)
        cv.shape(rotell(x, -150 + 90 * np.sin(q * 2.3), 48, 28, 0), (x - 60, -270, x + 60, -30), ramp('#d8343a', '#9a1f24', '#ff7070'), ow=3)
    n = int(6 + 30 * k)
    for q in range(n):                                                         # water flooding in
        ph = (lt * 1.3 + q * 0.137) % 1
        x = -620 + (q * 97) % 1240
        disc(cv, x + 30 * np.sin(T + q), -150 + 130 * np.sin(q * 1.7 + T), 14, WAT, ow=2, shadow=0, alpha=0.9 * min(1, ph * 4))
    meter(cv, 0, 230, 520, 0.2 + 0.75 * k, WAT, 'WATER IN BLOOD')
    hook_text(cv, 'FLOOD', lt, y=-780, size=170, pop_t=dur * 0.4, color=(90, 192, 255))
    return cv


def b3_salt(lt, dur, T):
    """The salt in his blood gets watered down: salt cubes spread thin, the meter drops. HYPONATREMIA."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a0a14', '#1a0408', vignette=0.4)
    k = ease(float(np.clip(lt / (dur * 0.7), 0, 1)))
    rng = np.random.default_rng(3)
    base = rng.uniform([-160, -460], [160, -160], (24, 2))
    for i, (x, y) in enumerate(base):                                          # salt spreading out as water pours in
        f = 1 + 1.6 * k
        sx_, sy_ = x * f, -310 + (y + 310) * f
        cv.shape(rbox(sx_, sy_, 16, 16, 4), (sx_ - 20, sy_ - 20, sx_ + 20, sy_ + 20), SALT, ow=2.5, alpha=1 - 0.5 * k * (i % 2))
    for q in range(int(30 * k)):
        x, y = rng.uniform(-480, 480), rng.uniform(-700, 80)
        disc(cv, x, y, 12, WAT, ow=2, shadow=0, alpha=0.8)
    meter(cv, 0, 200, 520, 1 - 0.6 * k, ramp('#ffffff', '#cfd8e2', '#ffffff') if k < 0.5 else ramp('#e2483d'), 'SALT LEVEL')
    if lt > dur * 0.5:
        box(cv, 0, -790, 390, 62, DARK, r=26)
        label(cv, 'HYPONATREMIA', 0, -782, 84, (255, 236, 80))
    return cv


def b4_cells(lt, dur, T):
    """Three cells: water rushes in and they balloon up."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1828', '#1a0a12', vignette=0.4)
    k = ease(float(np.clip(lt / (dur * 0.8), 0, 1)))
    for j, (cx, cy) in enumerate(((-230, -380), (230, -380), (0, -40))):
        r = 120 * (1 + 0.45 * k) * (1 + 0.03 * np.sin(T * 5 + j))
        cv.shape(circle(cx, cy, r), (cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), CELLW)
        disc(cv, cx + r * 0.2, cy - r * 0.1, r * 0.28, ramp('#c0607a', '#8a3a50', '#e090a8'), ow=3, shadow=0)
        for q in range(4):                                                     # water arrows in
            a = q * np.pi / 2 + 0.4 + j
            ph = (lt * 1.2 + q / 4) % 1
            p0 = (cx + np.cos(a) * (r + 120 - 80 * ph), cy + np.sin(a) * (r + 120 - 80 * ph))
            drop(cv, p0[0], p0[1], 12, a=1 - ph)
    hook_text(cv, 'SWELL', lt, y=-800, size=170, pop_t=dur * 0.45, color=(255, 170, 200))
    return cv


def b5_sick(lt, dur, T):
    """Back in the gym: hand to his head, green and dizzy, the symptoms popping up one by one."""
    cv = Canvas(GX, -150, 1.35)
    gym(cv, T)
    right = reach(1, 70, -840)
    guy(cv, GX, GY, GS, face='pain', arms=((12, 0), right), shirt=ramp('#e2483d', '#a82a26', '#ff8070'), tint=('#7ac85a', 0.3))
    front_arm(cv, GX, GY, GS, 1, *right, shirt=ramp('#e2483d', '#a82a26', '#ff8070'))
    hx, hy = GX, GY - 762 * GS
    for j in range(5):                                                         # dizzy stars
        a = T * 4 + j * 1.25
        label(cv, '*', hx + np.cos(a) * 190, hy - 190 + np.sin(a) * 40, 70, (255, 230, 90))
    for i, (txt, dx, dy) in enumerate((('HEADACHE', -230, -360), ('CRAMPS', 250, -260), ('THROWING UP', -250, -100), ('CONFUSED', 240, 20))):
        t0 = dur * (0.1 + 0.18 * i)
        if lt > t0:
            sc = min(1, (lt - t0) / 0.15)
            box(cv, hx + dx, hy + dy, 120 * sc, 34 * sc, DARK, r=16)
            label(cv, txt, hx + dx, hy + dy + 6, int(34 * sc), (255, 236, 80))
    return cv


def b6_skull(lt, dur, T):
    """X-ray of his head: the brain swells up against a skull that can't stretch. Nowhere to go."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#0e1430', '#060a18', vignette=0.4)
    k = ease(float(np.clip(lt / (dur * 0.6), 0, 1)))
    hx, hy = 0, -330
    s = 1.0 + 0.18 * k + 0.02 * np.sin(T * 9) * k
    brain(cv, hx, hy + 20, 1.25 * s, hot=0.6 * k)
    cv.shape(subtract(ellipse(hx, hy, 330, 360), ellipse(hx, hy, 300, 330)), (hx - 340, hy - 370, hx + 340, hy + 370), BONE, ow=4)   # the skull
    cv.shape(subtract(rbox(hx, hy + 360, 190, 80, 60), rbox(hx, hy + 340, 160, 60, 50)), (hx - 200, hy + 270, hx + 200, hy + 450), BONE, ow=4, alpha=0.9)
    if k > 0.6:
        for q in range(8):                                                     # pressure pushing out on the bone
            a = q * np.pi / 4 + 0.2
            p0 = (hx + np.cos(a) * 240, hy + np.sin(a) * 260)
            p1 = (hx + np.cos(a) * 300, hy + np.sin(a) * 325)
            arrows(cv, [(p0, p1)], (255, 90, 80), 10)
    if lt > dur * 0.6:
        hook_text(cv, 'NOWHERE TO GO', lt, y=-800, size=100, pop_t=dur * 0.6, color=(255, 90, 80))
    return cv


def b7_danger(lt, dur, T):
    """The jug alone on the bench with a warning label, a red alarm pulsing: TOO MUCH, TOO FAST."""
    cv = Canvas(0, -150, 1.2)
    gym(cv, T)
    pulse = 0.5 + 0.5 * np.sin(T * 7)
    jug(cv, -40, -330, 1.6, level=0.3, T=T)
    cv.shape(poly([(-40, -150), (40, -10), (-120, -10)]), (-122, -152, 42, -8), ramp('#ffd23f'), ow=4, shadow=0)
    label(cv, '!', -40, -50, 100, (40, 34, 50), stroke=0)
    cv.glow(circle(-40, -250, 260), (-300, -510, 220, 10), '#ff2a1a', 80, 0.25 * pulse)
    box(cv, 0, -700, 330, 56, DARK, r=26)
    label(cv, 'TOO MUCH, TOO FAST', 0, -692, 64, (255, 90, 80))
    return cv


def b8_marathon(lt, dur, T):
    """A marathon runner powering past the water table, cups flying."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#7fc0f0', '#d8f0ff', vignette=0.2)
    box(cv, 0, 600, 700, 400, ramp('#8a8a90', '#6a6a70', '#aaaab0'), r=0, ow=0, shadow=0)   # road
    for k in range(6):
        x = -600 + ((-T * 400 + k * 240) % 1200)
        box(cv, x, 520, 50, 8, ramp('#ffffff'), r=3, ow=0, shadow=0)
    box(cv, 0, -560, 380, 60, ramp('#ffffff', '#d8dde4', '#ffffff'), r=10)     # banner
    label(cv, 'MILE 20', 0, -552, 70, (200, 40, 40), stroke=0)
    tx = 330 - ((T * 200) % 900)
    box(cv, tx, 220, 140, 20, WOOD, r=4)                                       # water table with cups
    for c in range(4):
        box(cv, tx - 90 + c * 60, 180, 18, 26, ramp('#ffffff'), r=4, shadow=0)
    bob = 18 * abs(np.sin(T * 9))
    sw = 50 * np.sin(T * 9)
    guy(cv, -60, 760 - bob, 1.35, face='worried', arms=((30 + sw * 0.5, 90), (30 - sw * 0.5, 90)), shirt=ramp('#3fbf6a', '#25804a', '#7fe8a0'))
    box(cv, -60, 380 - bob, 60, 40, ramp('#ffffff'), r=4, shadow=0)
    label(cv, '42', -60, 390 - bob, 44, (40, 34, 50), stroke=0)
    for q in range(3):
        ph = (T * 1.2 + q / 3) % 1
        drop(cv, -200 + q * 140, -140 - bob + 80 * ph, 12, a=1 - ph)
    hook_text(cv, 'RARE', lt, y=-790, size=170, pop_t=dur * 0.25, color=(255, 255, 255))
    return cv


BEATS = [b0_hook, b1_kidneys, b2_flood, b3_salt, b4_cells, b5_sick, b6_skull, b7_danger, b8_marathon]

if __name__ == '__main__':
    run(BEATS)
