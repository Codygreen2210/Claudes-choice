#!/usr/bin/env python3
"""What happens when you eat the world's hottest pepper. Opens a beat after the bite: face going red, flames out of his
mouth, steam out of his ears; loops back into it (the last line plays over him lifting the pepper to his mouth)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

PEPX = ramp('#d8cc30', '#9a9010', '#f4f080')
JALA = ramp('#3f8a3a', '#25602a', '#6fb86a')
STEM = ramp('#3f8a3a', '#25602a', '#6fb86a')
FLAME = ramp('#ff8a2a', '#e24a1a', '#ffd23f')
FLAME2 = ramp('#ffd23f', '#ff8a2a', '#fff6a0')
CAPS = ramp('#ff6a2a', '#c43a10', '#ffb07a')
TONGUE = ramp('#f08a9a', '#c05a6a', '#ffb8c4')
MILK = ramp('#ffffff', '#dfe6ee', '#ffffff')
WALLK = ('#f6e3c0', '#e8c890')
ARTERY = ramp('#e2302a', '#a01a14', '#ff7a6a')
GX, GY, GS = -40, 960, 1.5
MOUTH = (GX, GY - 708 * GS)


def pepper(cv, x, y, s, ang=0.0, bite=0.0, col=None):
    """Wrinkly yellow Pepper X, stem at (x, y), body running along ang (radians). bite trims the far end."""
    col = PEPX if col is None else col
    c, sn = np.cos(ang), np.sin(ang)
    L = 230 * s * (1 - 0.3 * bite)
    blobs = []
    for u, r in ((0.2, 52), (0.45, 50), (0.7, 40), (0.9, 26)):
        if u * 230 * s > L + 10:
            continue
        blobs.append(circle(x + c * 230 * s * u, y + sn * 230 * s * u, r * s))
    body = smooth(26 * s, *blobs)
    if bite > 0:                                                               # flat bitten end
        body = inter(body, lambda X, Y: (X - x) * c + (Y - y) * sn - L)
    cv.shape(body, (x - 260 * s, y - 260 * s, x + 260 * s, y + 260 * s), col)
    for k in range(3):                                                         # wrinkles
        u = 0.25 + 0.2 * k
        if u * 230 * s < L:
            px_, py_ = x + c * 230 * s * u, y + sn * 230 * s * u
            line(cv, [(px_ - sn * 30 * s, py_ + c * 30 * s), (px_ + sn * 10 * s + c * 14 * s, py_ - c * 10 * s + sn * 14 * s)], 4 * s, flat(hexc('#9a9010')), a=0.8)
    line(cv, [(x, y), (x - c * 40 * s - sn * 20 * s, y - sn * 40 * s + c * 20 * s)], 18 * s, STEM, ow=3, flat=False)
    disc(cv, x, y, 22 * s, STEM, shadow=0)


def kitchen(cv, T):
    """His kitchen: tiles, a fridge with SUBSCRIBE / thumbs-up magnets, a LIKE & SUBSCRIBE poster (Easter eggs)."""
    cv.background(*WALLK, vignette=0.25)
    for k in range(6):
        line(cv, [(-560, -200 + k * 70), (560, -200 + k * 70)], 3, flat(hexc('#d8b880')), a=0.6)
    box(cv, 400, -330, 150, 420, ramp('#f4f6f8', '#c8d0d8', '#ffffff'), r=24)    # fridge
    line(cv, [(260, -440), (540, -440)], 5, flat(hexc('#a8b0b8')))
    line(cv, [(280, -560), (280, -480)], 10, STEEL, ow=2, flat=False)
    sub_button(cv, 400, -620, 170, size=24)
    thumb_icon(cv, 360, -300, 34)
    bell_icon(cv, 440, -310, 34)
    sticky(cv, 410, -170, 0.6, ['BUY MILK', '+ SUB'])
    sub_poster(cv, -400, -560, 0.8, T=T)


def table(cv, T):
    box(cv, 0, 700, 700, 320, WOOD, r=10)
    for i, x in enumerate((-380, -300)):                                       # hot sauce bottles with a LIKE label
        box(cv, x, 330, 34, 80, ramp('#c42a1a', '#8a1a10', '#ff6a4a'), r=10)
        box(cv, x, 250, 14, 26, ramp('#2a2a2a'), r=4, shadow=0)
        box(cv, x, 340, 30, 22, ramp('#fff6d8'), r=4, ow=0, shadow=0)
        label(cv, 'LIKE', x, 346, 18, (200, 40, 40), stroke=0)


def eater(cv, lt, T, red=None):
    """Him at the table. lt < -0.3: raising the pepper. Then the bite: red face, flames, steam."""
    bitten = lt > -0.3
    k = ease(float(np.clip((lt + 2.6) / 2.2, 0, 1)))
    if not bitten:
        tx, ty = 120 + (40 - 120) * k, -380 + (-690 + 380) * k
    else:
        tx, ty = 150, -640
    right = reach(1, tx, ty)
    heat = float(np.clip((lt + 0.3) / 0.5, 0, 1)) if bitten else 0.0
    heat = heat if red is None else red
    face = 'calm' if not bitten else 'scream'
    jx = 5 * np.sin(T * 47) * heat
    guy(cv, GX + jx, GY, GS, face=face, arms=((12, 0), right), tint=('#ff3a2a', 0.5 * heat) if heat > 0 else None, look=(1, 0) if not bitten else (0, 0))
    H = front_arm(cv, GX + jx, GY, GS, 1, *right)
    pepper(cv, H[0] + 10, H[1] - 20, 0.75, ang=np.pi + 0.35, bite=1.0 if bitten else 0.0)
    if heat > 0:
        mx, my = GX + jx, GY - 708 * GS
        fl = 1 + 0.08 * np.sin(T * 31) + 0.05 * np.sin(T * 53)                  # dragon breath: a flame cone out of his mouth
        L = 430 * fl
        def cone(w0, w1, Lc, col):
            top = [(mx - 30 - Lc * u, my - 10 - (w0 + (w1 - w0) * u) - 46 * abs(np.sin(u * 14 + T * 22)) * u) for u in np.linspace(0, 1, 22)]
            bot = [(mx - 30 - Lc * u, my - 10 + (w0 + (w1 - w0) * u) + 30 * abs(np.sin(u * 11 + T * 19)) * u) for u in np.linspace(1, 0, 22)]
            tip = [(mx - 30 - Lc - 60 - 30 * np.sin(T * 17), my - 10 - w1 * 0.4), (mx - 30 - Lc - 20, my - 10), (mx - 30 - Lc - 70 - 30 * np.cos(T * 13), my - 10 + w1 * 0.4)]
            cv.shape(poly(top + tip[:1] + [top[-1]] + tip[1:] + bot), (mx - Lc - 160, my - w1 - 90, mx, my + w1 + 70), col, ow=3, shadow=0, alpha=min(1.0, 2 * heat))
        cone(26, 120, L, ramp('#ff5a1a', '#d8300a', '#ffa040'))
        cone(14, 70, L * 0.8, FLAME)
        cone(6, 30, L * 0.55, FLAME2)
        for sx in (-1, 1):                                                     # steam out of his ears
            ph = (T * 1.4 + (sx > 0) * 0.5) % 1
            cloud(cv, mx + sx * (150 + 80 * ph) * GS / 1.5, my - 100 - 120 * ph, 30 + 30 * ph, a=0.8 * heat * (1 - ph))


def arteries(cv, x, y, s, squeeze=0.0, T=0.0):
    """A few big arteries over the brain; squeeze 0..1 narrows them."""
    w = (16 - 11 * squeeze) * s
    paths = [[(-20, 160), (-40, 60), (-120, -20), (-200, -60)], [(-40, 60), (20, -40), (60, -140)], [(20, 160), (60, 60), (150, 0), (220, -50)],
             [(60, 60), (40, -60), (-40, -150)], [(-120, -20), (-150, -120)], [(150, 0), (170, -110)]]
    for p in paths:
        pts = [(x + px_ * s, y + py_ * s) for px_, py_ in p]
        line(cv, pts, w, ARTERY, ow=3, flat=False)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    kitchen(cv, T)
    eater(cv, lt, T)
    table(cv, T)
    if lt >= -0.3:
        hook_text(cv, 'PEPPER X', lt + 0.3, y=-790, size=170, color=(255, 120, 40))
    return cv


def b1_compare(lt, dur, T):
    """A jalapeno next to Pepper X, and the heat bars: 538 times hotter."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1810', '#1a0a06', vignette=0.35)
    k = ease(float(np.clip((lt - 0.3) / (dur * 0.6), 0, 1)))
    pepper(cv, -250, -430, 0.85, ang=np.pi / 2 + 0.2, col=JALA)
    pepper(cv, 200, -470, 1.3, ang=np.pi / 2 - 0.15)
    label(cv, 'JALAPENO', -250, -120, 50, (180, 255, 170))
    label(cv, 'PEPPER X', 200, -120, 50, (255, 236, 80))
    meter(cv, 0, 70, 600, 0.04, ramp('#3f8a3a'), '5,000')
    meter(cv, 0, 230, 600, k, ramp('#ff6a2a', '#c43a10', '#ffb07a'), f'{int(round(2690000 * k / 10000)) * 10000:,}')
    if k > 0.98:
        hook_text(cv, f'{round(2690000 / 5000)}X HOTTER', lt, y=-790, size=130, pop_t=dur * 0.68, color=(255, 120, 40))
    neon_sign(cv, 0, 720, 'SUBSCRIBE', '#ff8a3a', T)
    return cv


def b2_tongue(lt, dur, T):
    """On his tongue: no fire at all, just capsaicin drops landing."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a1a26', '#2a0a12', vignette=0.4)
    for j in range(7):                                                         # his top teeth
        box(cv, -330 + j * 110, -800, 48, 70, ramp('#fbfaf4', '#d4cfbe', '#ffffff'), r=16)
    cv.shape(ellipse(0, 60, 460, 600), (-470, -550, 470, 670), TONGUE)
    line(cv, [(0, -460), (0, 400)], 10, flat(hexc('#c05a6a')), a=0.6)
    rng = np.random.default_rng(5)
    for px_, py_ in rng.uniform([-380, -420], [380, 420], (40, 2)):            # taste bumps
        if (px_ / 470) ** 2 + (py_ / 550) ** 2 < 0.9:
            disc(cv, px_, py_, 9, ramp('#ff9aaa'), ow=0, shadow=0)
    for q in range(16):                                                        # capsaicin raining down
        ph = (lt * 0.7 + q / 16) % 1
        x = -380 + (q * 53) % 760
        disc(cv, x, -700 + 900 * ph, 14, CAPS, ow=2.5, shadow=0, alpha=min(1, ph * 5))
    fx, fy = 0, -560                                                           # crossed-out fire
    cv.shape(smooth(10, circle(fx, fy, 70), circle(fx, fy - 60, 40)), (fx - 80, fy - 110, fx + 80, fy + 80), FLAME)
    line(cv, [(fx - 110, fy - 110), (fx + 110, fy + 90)], 22, flat(hexc('#ffffff')))
    if lt > dur * 0.5:
        badge(cv, 'CAPSAICIN', y=-760, col=(255, 140, 60), w=480)
    xray_tag(cv, 360, 720, ('TONGUE:', 'SUBSCRIBED'))
    return cv


def b3_sensor(lt, dur, T):
    """The heat sensor on a nerve: capsaicin clicks in, the sensor fires, the brain reads FIRE."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1030', '#0a0618', vignette=0.35)
    k = float(np.clip(lt / (dur * 0.4), 0, 1))
    line(cv, [(-500, 200), (-200, 150), (0, 50), (120, -150), (100, -330)], 22, flat(hexc('#ffd23f')), a=0.8)   # the nerve
    for i, (sx, sy) in enumerate(((-380, 190), (-230, 160))):                  # sensors on the nerve
        box(cv, sx, sy - 40, 46, 34, ramp('#7a5ad0', '#4a3aa0', '#a890ff'), r=12)
        cv.shape(rbox(sx, sy - 70, 16, 18, 6), (sx - 18, sy - 90, sx + 18, sy - 50), ramp('#1a1030'), ow=0, shadow=0, flat=True)
        dy = -260 + 190 * ease(k)
        disc(cv, sx, sy + dy, 16, CAPS, ow=2.5, shadow=0)
        if k >= 1:
            cv.glow(rbox(sx, sy - 40, 46, 34, 12), (sx - 50, sy - 80, sx + 50, sy), '#ff6a2a', 30, 0.7 + 0.3 * np.sin(T * 14))
    if k >= 1:                                                                 # the signal racing up
        ph = (lt * 2) % 1
        cv.glow(circle(-200 + 300 * ph, 150 - 300 * ph, 16), (-240, -180, 140, 190), '#ffe14d', 30, 1.0)
    brain(cv, 120, -520, 0.75, hot=0.7 * k)
    for q in range(4):
        ph = (T * 2 + q / 4) % 1
        fx = 40 + q * 55
        cv.shape(smooth(8, circle(fx, -650 - 60 * ph, 24 * (1 - ph) + 6), circle(fx, -680 - 60 * ph, 14 * (1 - ph) + 4)), (fx - 34, -720 - 60 * ph, fx + 34, -620 - 60 * ph),
                 FLAME, ow=2, shadow=0, alpha=k * (1 - ph))
    label(cv, 'HEAT SENSOR', -300, 330, 52, (200, 180, 255))
    if k >= 1:
        hook_text(cv, 'FAKE FIRE', lt, y=-800, size=140, pop_t=dur * 0.45, color=(255, 120, 40))
    neon_sign(cv, 0, 720, 'HIT LIKE', '#3fa9ff', T)
    return cv


def b4_cool(lt, dur, T):
    """Close on his face: sweat, runny nose, beet red."""
    cv = Canvas(GX, -200, 1.7)
    kitchen(cv, T)
    eater(cv, 1.5, T, red=1.0)
    hx, hy = GX, GY - 762 * GS
    for q in range(4):                                                         # sweat
        ph = (T * 1.2 + q / 4) % 1
        drop(cv, hx + (-110 + q * 70), hy - 110 + 90 * ph, 13, a=1 - ph)
    ph = (T * 0.9) % 1                                                         # runny nose
    drop(cv, hx + 4, hy + 30 + 40 * ph, 10, a=1)
    label(cv, 'SWEAT', hx - 200, hy - 170, 34, (255, 255, 255))
    label(cv, 'RED FACE', hx + 200, hy + 50, 34, (255, 255, 255))
    return cv


def b5_water(lt, dur, T):
    """A glass of water: the oily capsaicin just floats on top. Red X."""
    cv = Canvas(0, 0, 1.0)
    kitchen(cv, T)
    table(cv, T)
    gx, gy = -40, -40
    box(cv, gx, gy, 150, 240, ramp('#e6f6ff', '#a8d4ee', '#ffffff'), r=30, alpha=0.6)
    box(cv, gx, gy + 40, 132, 190, ramp('#7fd0ff', '#3fa9e0', '#bfeaff'), r=24, ow=0, alpha=0.8)
    for q in range(7):                                                         # oil drops sitting on top
        disc(cv, gx - 100 + q * 33, gy - 150 + 6 * np.sin(T * 3 + q), 14, CAPS, ow=2.5, shadow=0)
    if lt > dur * 0.4:
        line(cv, [(gx - 190, gy - 290), (gx + 190, gy + 290)], 30, flat(hexc('#e2302a')))
        line(cv, [(gx + 190, gy - 290), (gx - 190, gy + 290)], 30, flat(hexc('#e2302a')))
        hook_text(cv, 'NOPE', lt, y=-790, size=170, pop_t=dur * 0.4, color=(255, 90, 80))
    return cv


def b6_milk(lt, dur, T):
    """A carton of milk: casein blobs grab the oil drops and carry them off."""
    cv = Canvas(0, 0, 1.0)
    kitchen(cv, T)
    table(cv, T)
    cx, cy = -250, -150                                                        # the carton (brand: LIKE MILK)
    box(cv, cx, cy, 110, 210, MILK, r=12)
    cv.shape(poly([(cx - 110, cy - 210), (cx + 110, cy - 210), (cx, cy - 300)]), (cx - 112, cy - 302, cx + 112, cy - 208), MILK, ow=4, shadow=0)
    box(cv, cx, cy - 20, 100, 70, ramp('#3d7fd8', '#2a559a', '#7fb4ff'), r=8, shadow=0)
    label(cv, 'LIKE', cx, cy - 40, 46, (255, 255, 255), stroke=0)
    label(cv, 'MILK', cx, cy + 10, 40, (255, 255, 255), stroke=0)
    label(cv, 'NOW WITH SUBSCRIBE', cx, cy + 120, 16, (40, 60, 110), stroke=0)
    k = float(np.clip(lt / (dur * 0.9), 0, 1))
    for q in range(5):                                                         # casein scrubbers carrying oil away
        u = float(np.clip(k * 1.6 - q * 0.15, 0, 1))
        x = 60 + q * 80 + 220 * u
        y = -260 + q * 70 - 500 * u * u
        disc(cv, x, y, 34, MILK, ow=3)
        dot(cv, x - 10, y - 6, 4); dot(cv, x + 10, y - 6, 4)
        disc(cv, x + 26, y + 20, 14, CAPS, ow=2.5, shadow=0, alpha=1 - 0.6 * u)
    if lt > dur * 0.35:
        disc(cv, 260, 150, 70, ramp('#3fbf6a', '#25804a', '#7fe8a0'))
        line(cv, [(225, 150), (250, 180), (295, 120)], 16, flat(hexc('#ffffff')))
        hook_text(cv, 'MILK!', lt, y=-790, size=180, pop_t=dur * 0.35, color=(255, 255, 255))
    return cv


def b7_squeeze(lt, dur, T):
    """His brain's arteries squeezing tight, thunderclap headache bolts."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1030', '#0a0618', vignette=0.4)
    k = ease(float(np.clip(lt / (dur * 0.55), 0, 1)))
    brain(cv, 0, -280, 1.5, hot=0.3 * k)
    arteries(cv, 0, -280, 1.5, squeeze=k)
    if k > 0.4:
        for q in range(4):
            a = q * np.pi / 2 + 0.6
            p0 = (np.cos(a) * 360, -280 + np.sin(a) * 300)
            pts = jagged(p0, (p0[0] * 1.35, -280 + (p0[1] + 280) * 1.35), int(T * 12) + q, depth=3, rough=0.5)
            line(cv, pts, 10, flat(hexc('#ffe14d')), a=0.5 + 0.5 * np.sin(T * 20 + q))
    if lt > dur * 0.6:
        hook_text(cv, 'HEADACHE', lt, y=-790, size=150, pop_t=dur * 0.6, color=(255, 236, 80))
    xray_tag(cv, -360, 720, ('BRAIN SCAN', 'LIKE + SUB'))
    return cv


def b8_back(lt, dur, T):
    """Five weeks pass on a calendar and the arteries open back up."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1030', '#0a0618', vignette=0.4)
    k = ease(float(np.clip(lt / (dur * 0.8), 0, 1)))
    brain(cv, -60, -260, 1.3)
    arteries(cv, -60, -260, 1.3, squeeze=1 - k)
    box(cv, 370, -620, 95, 110, ramp('#ffffff', '#d8dde4', '#ffffff'), r=8)
    box(cv, 370, -705, 95, 24, ramp('#e2302a'), r=6, shadow=0)
    label(cv, 'WEEK', 370, -699, 24, (255, 255, 255), stroke=0)
    label(cv, str(1 + int(4 * k)), 370, -600, 90, (40, 34, 50), stroke=0)
    label(cv, 'TO DO: SUBSCRIBE', 370, -540, 15, (200, 40, 40), stroke=0)
    if k > 0.95:
        badge(cv, 'BACK TO NORMAL', y=150, col=(127, 255, 160), w=620)
    return cv


# the cut that goes INSIDE him: into his mouth, onto the tongue (screen px)
DIVE = {2: (540 + int(MOUTH[0]), int(960 + MOUTH[1]))}

BEATS = [b0_hook, b1_compare, b2_tongue, b3_sensor, b4_cool, b5_water, b6_milk, b7_squeeze, b8_back]

if __name__ == '__main__':
    run(BEATS)
