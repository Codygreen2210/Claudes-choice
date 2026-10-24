#!/usr/bin/env python3
"""How to survive falling through ice (the 1-10-1 rule). Opens mid-plunge: the ice has just given way and he's dropping
into the hole in a burst of water and ice chunks; loops back into it (the last line plays over him walking out onto the ice)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

JACKET = ramp('#e2483d', '#a82a26', '#ff8070')
BEANIE = ramp('#3d7fd8', '#2a559a', '#7fb4ff')
ICEP = ramp('#e6f4ff', '#b8d4ea', '#ffffff')
ICES = ramp('#bfe2f6', '#8ab8d8', '#e6f6ff')
WATERD = ramp('#1a4a7a', '#0e2e52', '#2a6aa0')
PINE = ramp('#2a6a4a', '#1a4a32', '#3a8a5e')
SNOW = ramp('#ffffff', '#d8e4f0', '#ffffff')
CARROT = ramp('#ff8a2a', '#c4561a', '#ffbf7a')
LUNGW = ramp('#3fa9e0', '#2378b0', '#8fd6ff')
ICE_Y, SLAB_Y, WL = -80, -20, -50                # ice surface front edge, slab bottom, water line in the hole
GS = 0.9
GY_IN = WL + 375 * GS                            # his feet when he's in the hole (water at mid chest)


def beanie(cv, hx, hy, s):
    cv.shape(inter(circle(hx, hy - 10 * s, 112 * s), lambda X, Y: Y - (hy - 40 * s)), (hx - 115 * s, hy - 125 * s, hx + 115 * s, hy - 35 * s), BEANIE)
    box(cv, hx, hy - 42 * s, 112 * s, 20 * s, ramp('#2a559a'), r=10 * s)
    disc(cv, hx, hy - 128 * s, 28 * s, ramp('#ffffff', '#d8e4f0', '#ffffff'))
    thumb_icon(cv, hx + 50 * s, hy - 80 * s, 22 * s, ramp('#ffd23f', '#d09a10', '#fff08a'))     # thumbs-up patch on his hat


def wguy(cv, x, y, s, T, face='calm', arms=((12, 0), (12, 0)), cold=0.0, look=(0, 0), ground=True):
    guy(cv, x, y, s, face=face, arms=arms, shirt=JACKET, tint=('#5aa8ff', cold) if cold > 0 else None, look=look, ground=ground)
    beanie(cv, x, y - 762 * s, s)


def breath(cv, x, y, T, a=1.0):
    for q in range(2):
        ph = (T * 0.8 + q / 2) % 1
        cloud(cv, x + 40 + 80 * ph, y - 30 * ph, 26 + 30 * ph, a=a * 0.7 * (1 - ph))


def lake_back(cv, T, hole=True, cracks=0.0, cx=0.0):
    """Far shore with pines, a THIN ICE / SUBSCRIBE sign and a snowman (Easter eggs), the ice, the water under it."""
    cv.background('#8fb0d0', '#e0eaf4', vignette=0.2)
    for i, x in enumerate(range(-560, 600, 80)):
        h = 130 + 50 * ((i * 37) % 3)
        cv.shape(poly([(x - 50, -300), (x + 50, -300), (x, -300 - h)]), (x - 52, -302 - h, x + 52, -298), PINE, ow=3, shadow=0)
        cv.shape(poly([(x - 16, -300 - h * 0.72), (x + 16, -300 - h * 0.72), (x, -300 - h)]), (x - 18, -302 - h, x + 18, -298 - h * 0.7), SNOW, ow=2, shadow=0)
    box(cv, 0, -300, 700, 22, SNOW, r=8, shadow=0)
    line(cv, [(-400, -300), (-400, -440)], 10, WOOD, ow=3, flat=False)           # the sign
    box(cv, -400, -470, 110, 62, ramp('#fff6d8', '#e0d4a8', '#ffffff'), r=8)
    label(cv, 'THIN ICE', -400, -500, 34, (200, 40, 40), stroke=0)
    sub_button(cv, -400, -448, 170, size=24)
    sx_, sy_ = 400, -300                                                         # the snowman
    disc(cv, sx_, sy_ - 50, 58, SNOW); disc(cv, sx_, sy_ - 135, 44, SNOW); disc(cv, sx_, sy_ - 205, 32, SNOW)
    for ex in (-10, 10):
        dot(cv, sx_ + ex, sy_ - 212, 5)
    cv.shape(poly([(sx_, sy_ - 205), (sx_ + 40, sy_ - 200), (sx_, sy_ - 196)]), (sx_, sy_ - 210, sx_ + 42, sy_ - 192), CARROT, ow=2, shadow=0)
    line(cv, [(sx_ - 40, sy_ - 140), (sx_ - 110, sy_ - 190)], 6, WOOD, ow=2, flat=False)
    sticky(cv, sx_ - 125, sy_ - 225, 0.55, ['HIT', 'LIKE'])
    cv.shape(poly([(-560, -300), (560, -300), (560, ICE_Y), (-560, ICE_Y)]), (-560, -302, 560, ICE_Y + 2), ICEP, ow=0, shadow=0)
    for k in range(5):
        line(cv, [(-500 + k * 230, -250 + k * 30), (-380 + k * 230, -240 + k * 30)], 4, flat(hexc('#c8dcee')), a=0.8)
    if cracks > 0:
        for j in range(6):
            a = j * 1.05 + 0.3
            L = 40 + 160 * cracks
            line(cv, [(cx, -150), (cx + np.cos(a) * L * 0.5 + 10 * np.sin(j * 3), -150 + np.sin(a) * L * 0.12), (cx + np.cos(a) * L, -150 + np.sin(a) * L * 0.22)],
                 4, flat(hexc('#5a7a9a')))
    if hole:
        cv.shape(ellipse(cx, -150, 175, 34), (cx - 180, -186, cx + 180, -114), WATERD, ow=3, shadow=0)
    box(cv, 0, 500, 700, 520, WATERD, r=0, ow=0, shadow=0)


def lake_front(cv, T, hole=True, cx=0.0):
    """The water over his legs, the front edge of the ice, and falling snow."""
    box(cv, 0, 450, 700, 500, WATERD, r=0, ow=0, shadow=0, alpha=0.72)
    fx = 620 - ((T * 140) % 1500)                                              # a fish towing a SUBSCRIBE banner (Easter egg)
    fy = 690 + 14 * np.sin(T * 3)
    line(cv, [(fx + 60, fy), (fx + 110, fy)], 3, flat(hexc('#d8e4f0')))
    box(cv, fx + 215, fy, 105, 28, ramp('#ffffff', '#d8e4f0', '#ffffff'), r=6, shadow=0)
    label(cv, 'SUBSCRIBE', fx + 215, fy + 6, 34, (220, 40, 40), stroke=0)
    cv.shape(smooth(8, ellipse(fx, fy, 60, 30), poly([(fx + 45, fy), (fx + 95, fy - 30), (fx + 95, fy + 30)])), (fx - 64, fy - 34, fx + 98, fy + 34), ramp('#ff9a3a', '#c86a1a', '#ffc88a'), shadow=0)
    dot(cv, fx - 32, fy - 6, 6)
    if hole:
        box(cv, (-560 + cx - 160) / 2, (ICE_Y + SLAB_Y) / 2, (cx - 160 + 560) / 2, (SLAB_Y - ICE_Y) / 2, ICES, r=4, shadow=0)
        box(cv, (cx + 160 + 560) / 2, (ICE_Y + SLAB_Y) / 2, (560 - cx - 160) / 2, (SLAB_Y - ICE_Y) / 2, ICES, r=4, shadow=0)
    else:
        box(cv, 0, (ICE_Y + SLAB_Y) / 2, 560, (SLAB_Y - ICE_Y) / 2, ICES, r=4, shadow=0)
    for q in range(14):
        x = -520 + (q * 83) % 1040 + 20 * np.sin(T + q)
        y = -960 + ((T * 90 + q * 140) % 1000)
        disc(cv, x, y, 6 + (q % 3) * 2, SNOW, ow=0, shadow=0, alpha=0.9)


def in_hole(cv, T, face='calm', cold=0.0, bob=1.0):
    y = GY_IN + 8 * np.sin(T * 2) * bob
    arms = (reach(-1, -280, (-95 - y) / GS), reach(1, 280, (-95 - y) / GS))
    wguy(cv, 0, y, GS, T, face=face, arms=arms, cold=cold, ground=False)
    return y


def stopwatch(cv, x, y, r, k, txt):
    disc(cv, x, y - r - 14, 18, STEEL)
    disc(cv, x, y, r, ramp('#ffffff', '#d8dde4', '#ffffff'))
    for t in range(12):
        a = t * np.pi / 6
        line(cv, [(x + np.sin(a) * r * 0.78, y - np.cos(a) * r * 0.78), (x + np.sin(a) * r * 0.9, y - np.cos(a) * r * 0.9)], 4, flat(hexc('#3a3a4a')))
    a = 2 * np.pi * k
    line(cv, [(x, y), (x + np.sin(a) * r * 0.75, y - np.cos(a) * r * 0.75)], 8, flat(hexc('#e2302a')))
    dot(cv, x, y, 8)
    label(cv, txt, x, y + r + 50, 46, (40, 50, 80), stroke=0)


def belly_guy(cv, x, y, s, T, kick=1.0, cold=0.0):
    """Him flat on his belly, side view, head to the right: arms reaching forward, legs kicking behind."""
    for k_, sgn in ((0, 1), (1, -1)):                                          # legs, kicking
        ph = np.sin(T * 9 + k_ * np.pi) * kick
        line(cv, [(x - 110 * s, y + 10 * s), (x - 330 * s, y + (10 + 40 * ph) * s)], 64 * s, JEANS, ow=4, flat=False)
        disc(cv, x - 360 * s, y + (10 + 44 * ph) * s, 30 * s, SHOE)
    line(cv, [(x - 140 * s, y), (x + 110 * s, y)], 124 * s, JACKET, ow=4, flat=False)
    for k_ in (0, 1):                                                          # arms reaching out on the ice
        yy = y - 10 * s + k_ * 14 * s
        line(cv, [(x + 80 * s, yy), (x + 300 * s, yy + 20 * s)], 52 * s, JACKET, ow=4, flat=False)
        disc(cv, x + 320 * s, yy + 22 * s, 30 * s, SKIN)
    hx, hy = x + 200 * s, y - 40 * s
    disc(cv, hx, hy, 80 * s, SKIN)
    cv.shape(inter(circle(hx - 10 * s, hy - 10 * s, 84 * s), lambda X, Y: Y - (hy - 30 * s) + (X - hx) * 0.6), (hx - 95 * s, hy - 95 * s, hx + 75 * s, hy + 20 * s), BEANIE)
    disc(cv, hx - 70 * s, hy - 80 * s, 22 * s, ramp('#ffffff', '#d8e4f0', '#ffffff'))
    cv.shape(ellipse(hx + 40 * s, hy - 6 * s, 9 * s, 12 * s), (hx + 30 * s, hy - 20 * s, hx + 50 * s, hy + 8 * s), INKC, ow=0, shadow=0, flat=True)
    line(cv, [(hx + 30 * s, hy + 34 * s), (hx + 58 * s, hy + 30 * s)], 5 * s)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """lt < 0: he walks out onto the ice and it cracks under him. From lt = -0.3 he drops; frame one is mid-plunge."""
    cv = Canvas(0, 0, 1.0)
    walk_x = -320 + 320 * ease(float(np.clip((lt + 2.1) / 1.8, 0, 1)))
    falling = lt > -0.3
    cracks = float(np.clip((lt + 1.0) / 0.7, 0, 1))
    lake_back(cv, T, hole=falling, cracks=0 if falling else cracks, cx=0)
    if not falling:
        y = -150 - 6 * abs(np.sin(lt * 7))
        wguy(cv, walk_x, y, GS, T, face='calm' if cracks < 0.4 else 'worried', look=(0, 1) if cracks > 0.4 else (1, 0))
    else:
        u = float(np.clip((lt + 0.3) / 0.55, 0, 1))
        y = -150 + (GY_IN - -150) * ease(u) + 30 * np.sin(np.pi * u) * (u > 0.8)
        up = ease(float(np.clip((lt + 0.3) / 0.35, 0, 1)))       # arms up over ~10 frames: fast, but a body can do it
        wguy(cv, 0, y, GS, T, face='scream', arms=((150 * up, 30 * up), (150 * up, 30 * up)), look=(0, -1), ground=False)
    lake_front(cv, T, hole=falling)
    if falling:
        rng = np.random.default_rng(2)
        u = float(np.clip((lt + 0.3) / 1.2, 0, 1))
        for q in range(26):                                                     # splash and ice chunks
            vx, vy = rng.uniform(-520, 520), rng.uniform(-900, -400)
            px_, py_ = vx * u, -110 + vy * u + 1500 * u * u
            if q % 3 == 0:
                box(cv, px_, py_, 16, 12, ICES, r=3, shadow=0, alpha=1 - u)
            else:
                disc(cv, px_, py_, 10 + (q % 4) * 3, ramp('#8fd6ff', '#3fa9e0', '#d8f2ff'), ow=2, shadow=0, alpha=1 - u)
        hook_text(cv, 'CRACK!', lt + 0.3, y=-780, size=180, color=(255, 255, 255))
    return cv


def b1_gasp(lt, dur, T):
    """Close on his face: the cold hits, he gasps hard."""
    cv = Canvas(0, -330, 2.2)
    lake_back(cv, T)
    jx = 3 * np.sin(T * 47)
    y = in_hole(cv, T + jx * 0, face='scream', cold=0.25)
    lake_front(cv, T)
    for q in range(3):                                                         # air rushing into his mouth
        ph = (lt * 2.2 + q / 3) % 1
        mx, my = 0, y - 708 * GS
        arrows(cv, [((mx + 160 - 120 * ph, my - 60 + 50 * ph), (mx + 110 - 120 * ph, my - 30 + 50 * ph))], (255, 255, 255), 8)
    hook_text(cv, 'GASP!', lt, y=-780, size=180, pop_t=dur * 0.4, color=(255, 255, 255))
    return cv


def b2_lungs(lt, dur, T):
    """Inside his chest: one gasp underwater and the lungs start filling up."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#0e1a30', '#060c18', vignette=0.35)
    x, y, s = 0, -60, 0.85
    chest(cv, x, y, s, T, lung=0.9)
    k = ease(float(np.clip((lt - dur * 0.3) / (dur * 0.6), 0, 1)))
    level = y + 170 * s - 330 * s * k
    for sx in (-1, 1):
        lung = rotell(x + sx * 140 * s, y - 60 * s, 125 * s * 1.075, 230 * s, sx * 6)
        cv.shape(inter(lung, lambda X, Y, L=level: L - Y), (x + sx * 140 * s - 190 * s, y - 380 * s, x + sx * 140 * s + 190 * s, y + 300 * s),
                 LUNGW, ow=0, shadow=0, alpha=0.8 * float(k > 0))
    if k > 0.4:
        badge(cv, 'WATER IN', y=-760, col=(127, 210, 255), w=400)
    neon_sign(cv, 0, 720, 'SUBSCRIBE', '#3fa9ff', T)
    return cv


def b3_minute(lt, dur, T):
    cv = Canvas(0, -250, 1.4)
    lake_back(cv, T)
    y = in_hole(cv, T, face='closed' if (T % 2.2) > 1.1 else 'calm', cold=0.15)
    lake_front(cv, T)
    breath(cv, 0, y - 708 * GS, T)
    stopwatch(cv, 236, -690, 72, float(np.clip(lt / dur, 0, 1)), '')
    hook_text(cv, '1 MINUTE', lt, y=-780, size=150, pop_t=dur * 0.45, color=(255, 236, 80))
    return cv


def b4_ten(lt, dur, T):
    cv = Canvas(0, -200, 1.2)
    k = float(np.clip(lt / (dur * 0.85), 0, 1))
    lake_back(cv, T)
    y = in_hole(cv, T, face='worried', cold=0.15 + 0.4 * k, bob=1 - k)
    rng = np.random.default_rng(6)
    for q in range(int(18 * k)):                                               # frost on his sleeves
        sx = 1 if q % 2 else -1
        px_ = sx * rng.uniform(100, 260); py_ = rng.uniform(-200, -100)
        disc(cv, px_, py_, 6, SNOW, ow=0, shadow=0)
    lake_front(cv, T)
    badge(cv, f'{1 + int(9 * k)} MIN', y=-720, x=250, col=(127, 210, 255), w=230)
    if k > 0.95:
        hook_text(cv, '10 MINUTES', lt, y=-800, size=130, pop_t=dur * 0.82, color=(127, 210, 255))
    return cv


def b5_hour(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    k = ease(float(np.clip(lt / (dur * 0.6), 0, 1)))
    lake_back(cv, T)
    in_hole(cv, T, face='worried', cold=0.4)
    lake_front(cv, T)
    a = 2 * np.pi * k
    wall_clock(cv, 300, -620, 110, np.radians(30 * k) + 0.0, a)
    if k > 0.98:
        hook_text(cv, '1 HOUR', lt, y=-790, size=170, pop_t=dur * 0.6, color=(255, 236, 80))
    return cv


def b6_slide(lt, dur, T):
    """He floats flat, kicks, and slides out onto the ice on his belly."""
    cv = Canvas(60, -200, 1.3)
    k = ease(float(np.clip((lt - dur * 0.2) / (dur * 0.7), 0, 1)))
    lake_back(cv, T)
    bx, by = -40 + 230 * k, -40 - 75 * k
    belly_guy(cv, bx, by, 0.8, T, kick=1 - 0.7 * k, cold=0.3)
    lake_front(cv, T)
    if k < 0.7:
        for q in range(3):                                                     # kick splashes
            ph = (lt * 2 + q / 3) % 1
            disc(cv, bx - 300 + 30 * q, WL - 60 * ph, 10, ramp('#8fd6ff'), ow=2, shadow=0, alpha=1 - ph)
    label(cv, 'KICK', bx - 280, -230, 56, (255, 255, 255))
    arrows(cv, [((bx + 60, -330), (bx + 260, -330))], (255, 236, 80), 14)
    label(cv, 'SLIDE', bx + 160, -390, 56, (255, 236, 80))
    return cv


def b7_roll(lt, dur, T):
    """He stays low and rolls away from the hole. A little standing figure gets a red X."""
    cv = Canvas(120, -260, 1.25)
    k = ease(float(np.clip(lt / (dur * 0.9), 0, 1)))
    lake_back(cv, T)
    bx = 110 + 150 * k
    belly_guy(cv, bx, -115 - 6 * np.sin(T * 10), 0.8, T, kick=0.0)
    lake_front(cv, T)
    for q in range(3):                                                         # roll marks
        a = T * 6 + q * 2.1
        arrows(cv, [((bx + np.cos(a) * 120, -280 + np.sin(a) * 40), (bx + np.cos(a + 0.7) * 120, -280 + np.sin(a + 0.7) * 40))], (255, 236, 80), 10)
    label(cv, 'ROLL', bx, -420, 64, (255, 236, 80))
    sx_, sy_ = -50, -600                                                       # do not stand up
    box(cv, sx_, sy_, 110, 140, ramp('#ffffff', '#d8dde4', '#ffffff'), r=16)
    disc(cv, sx_, sy_ - 70, 24, DARK, ow=0); line(cv, [(sx_, sy_ - 45), (sx_, sy_ + 30)], 18, DARK, ow=0)
    line(cv, [(sx_, sy_ + 30), (sx_ - 25, sy_ + 100)], 14, DARK, ow=0); line(cv, [(sx_, sy_ + 30), (sx_ + 25, sy_ + 100)], 14, DARK, ow=0)
    line(cv, [(sx_ - 80, sy_ - 100), (sx_ + 80, sy_ + 100)], 18, flat(hexc('#e2302a'))); line(cv, [(sx_ + 80, sy_ - 100), (sx_ - 80, sy_ + 100)], 18, flat(hexc('#e2302a')))
    label(cv, "DON'T STAND", sx_, sy_ + 190, 46, (255, 90, 80))
    return cv


def b8_rule(lt, dur, T):
    """The 1-10-1 rule on three cards, plus a SAVE THIS / SUBSCRIBE sticky."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1c3050', '#0e1a30', vignette=0.3)
    badge(cv, '1-10-1 RULE', y=-660, col=(127, 210, 255), w=520)
    for i, (n, unit, t0) in enumerate((('1', 'MINUTE', 0.35), ('10', 'MINUTES', 0.55), ('1', 'HOUR', 0.75))):
        f = float(np.clip((lt - dur * t0) / 0.15, 0, 1))
        if f <= 0:
            continue
        sc = 0.7 + 0.3 * ease(f)
        x = -330 + i * 330
        box(cv, x, -250, 140 * sc, 190 * sc, ramp('#ffffff', '#d8e4f0', '#ffffff'), r=24 * sc)
        label(cv, n, x, -290, int(150 * sc), (30, 60, 110), stroke=0)
        label(cv, unit, x, -140, int(40 * sc), (30, 60, 110), stroke=0)
    sticky(cv, 0, 660, 1.2, ['SAVE THIS', '+ SUBSCRIBE'])
    return cv


# the cut that goes INSIDE him: in through his gasping mouth to his lungs (screen px)
DIVE = {2: (540, 1000)}

BEATS = [b0_hook, b1_gasp, b2_lungs, b3_minute, b4_ten, b5_hour, b6_slide, b7_roll, b8_rule]

if __name__ == '__main__':
    run(BEATS)
