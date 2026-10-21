#!/usr/bin/env python3
"""Do you really swallow spiders in your sleep? Opens on a spider already walking across the pillow toward a sleeping
man's open mouth; loops back into that walk (the last line plays over the start of it)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

SPID = ramp('#3a2a22', '#1a110c', '#6e5040')
SPIDLEG = ramp('#2e211a', '#140c08', '#5a4030')
MOUTHC = ramp('#5a1f2a', '#3a0f18', '#7a3040')
CAV = ramp('#8a2a3a', '#5a1420', '#b04a5a')
TONGUE = ramp('#f08a9a', '#c05a6a', '#ffb8c4')
TEETH = ramp('#fbfaf4', '#d4cfbe', '#ffffff')
SHEETC = ('#e8eef6', '#c8d4e4')
BREATH = flat(hexc('#ff8a3a'))
BLANK = ramp('#4f7fd8', '#2f559a', '#8fb4ff')
CARD = ramp('#fffdf4', '#e0dccb', '#ffffff')
STAMP = flat(hexc('#e2302a'))
INKT = (40, 34, 50)
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


def spider(cv, x, y, s, T, ang=0.0, walk=1.0, a=1.0, worried=False):
    """Top-down cartoon house spider. ang = direction it faces (0 = up the screen), legs step when walk > 0."""
    c, sn = np.cos(ang), np.sin(ang)
    R = lambda lx, ly: (x + (lx * c - ly * sn) * s, y + (lx * sn + ly * c) * s)
    for sx in (-1, 1):
        for k, (hy, base) in enumerate(((-18, -55), (-6, -18), (6, 18), (18, 55))):
            ph = T * 9 * walk + k * np.pi / 2 + (0 if sx > 0 else np.pi)
            th = np.radians(base + 14 * np.sin(ph) * min(walk, 1))
            d1 = np.array([sx * np.cos(th), np.sin(th)])
            hip = np.array([sx * 22, hy])
            knee = hip + d1 * 62 + np.array([0, -14])
            th2 = th + np.radians(28 * np.sign(base))
            foot = knee + np.array([sx * np.cos(th2), np.sin(th2)]) * 74
            line(cv, [R(*hip), R(*knee), R(*foot)], 11 * s, SPIDLEG, ow=3, flat=False, a=a)
    ax, ay = R(0, 62)
    cv.shape(rotell(ax, ay, 46 * s, 58 * s, np.degrees(ang)), (ax - 64 * s, ay - 64 * s, ax + 64 * s, ay + 64 * s), SPID, alpha=a)   # abdomen
    hx, hy = R(0, 0)
    disc(cv, hx, hy, 36 * s, SPID, alpha=a)                                                       # head
    for sx in (-1, 1):                                                                            # big cartoon eyes
        ex, ey = R(sx * 14, -14)
        disc(cv, ex, ey, 11 * s, ramp('#ffffff'), ow=2.5, shadow=0, alpha=a)
        px_, py_ = R(sx * 14, -17)
        cv.shape(circle(px_, py_, 5 * s), (px_ - 6 * s, py_ - 6 * s, px_ + 6 * s, py_ + 6 * s), ramp('#000000'), ow=0, shadow=0, flat=True, alpha=a)
        if worried:
            b0_, b1_ = R(sx * 6, -30), R(sx * 24, -26)
            line(cv, [b0_, b1_], 4 * s, flat(hexc('#ffffff')), a=a)


def zzz(cv, x, y, T, a=1.0):
    for q in range(3):
        ph = (T * 0.45 + q / 3) % 1
        label(cv, 'Z', x + 60 * ph + 20 * np.sin(T * 2 + q), y - 260 * ph, int(50 + 50 * ph), (220, 230, 255), a=a * min(1, (1 - ph) * 2.5))


S0, Y0 = 2.2, 382                                     # close-up bed: head centre (0, -150), mouth at (0, MOUTH_Y)
MOUTH_Y = Y0 + 520 * S0 - 708 * S0


def sleeper(cv, T, breath=1.0):
    """Close on his face from above, head on the pillow, mouth hanging open."""
    cv.background('#1c2a4a', '#0e1630', vignette=0.3)
    box(cv, 0, Y0 + 250 * S0, 430 * S0, 760 * S0, ramp('#a8693a', '#6e4122', '#d08f58'), r=40 * S0)
    box(cv, 0, Y0 + 260 * S0, 400 * S0, 730 * S0, ramp('#f4f1ea'), r=30 * S0)
    box(cv, 0, Y0 - 380 * S0, 300 * S0, 110 * S0, ramp('#ffffff', '#d8dde4', '#ffffff'), r=80 * S0)
    label(cv, 'LIKE  &  SUBSCRIBE', 0, -640, 42, (120, 150, 200), a=0.8, stroke=0)        # embroidered on the pillowcase
    sub_phone(cv, -410, -500, 1.15, T)                                         # his phone on the pillow
    guy(cv, 0, Y0 + 520 * S0, S0, face='snore', legs=False, ground=False, arms=((12, 0), (12, 0)))
    box(cv, 0, Y0 + 520 * S0, 390 * S0, 480 * S0, BLANK, r=60 * S0)
    for k in range(4):
        line(cv, [(-360 * S0, Y0 + (150 + k * 220) * S0), (360 * S0, Y0 + (170 + k * 220) * S0)], 6 * S0, flat(hexc('#2f559a')), a=0.5)
    label(cv, 'LIKE  \u2022  SUBSCRIBE  \u2022  LIKE  \u2022  SUBSCRIBE', 0, 840, 36, (200, 218, 255), a=0.85, stroke=0)   # knitted into the blanket
    zzz(cv, -230, MOUTH_Y - 150, T, 0.9 * breath)


def path(u, p0, p1):
    u = float(np.clip(u, 0, 1))
    return p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """Before 0 (the loop line) the spider sets off from the top corner; on frame one it's mid-walk to his mouth."""
    cv = Canvas(0, 0, 1.0)
    sleeper(cv, T)
    p0, p1 = (500, -700), (150, -80)
    u = (lt + 2.79) / (2.79 + dur)
    x, y = path(u, p0, p1)
    ang = np.arctan2(p1[0] - p0[0], -(p1[1] - p0[1]))
    spider(cv, x, y, 0.9, T, ang=ang, walk=1.0)
    if lt >= 0:
        hook_text(cv, '8 A YEAR?', lt, y=-780, size=170, color=(255, 236, 80))
    return cv


def b1_mouth(lt, dur, T):
    """Right at his big open mouth: eight spiders drop in, one after another."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#f2b48c', '#c97f62', vignette=0.3)
    cx, cy = 0, -60
    cv.shape(ellipse(cx, cy, 470, 380), (-480, cy - 390, 480, cy + 390), ramp('#d8606e', '#a83a4a', '#ff9aa8'))   # lips
    cv.shape(ellipse(cx, cy, 395, 305), (-400, cy - 310, 400, cy + 310), ramp('#3a0f18', '#1a060a', '#5a1a28'), ow=3)  # dark inside
    cv.shape(ellipse(cx, cy + 210, 300, 130), (-310, cy + 70, 310, cy + 350), TONGUE, ow=3)
    line(cv, [(cx, cy + 120), (cx, cy + 260)], 8, flat(hexc('#c05a6a')), a=0.7)
    cv.shape(capsule(cx, cy - 300, cx, cy - 190, 34, 26), (cx - 40, cy - 310, cx + 40, cy - 150), ramp('#e07080', '#b04a5a', '#ff9aa8'))   # uvula
    for j in range(6):                                                        # top teeth along the upper lip
        tx = -275 + j * 110
        ty = cy - 285 + 0.0006 * tx * tx * 0.9
        box(cv, tx, ty, 46, 46, TEETH, r=14)
    n = int(np.clip(lt / (dur * 0.75), 0, 1) * 8 + 0.001)
    for i in range(n):
        t0 = i * dur * 0.75 / 8
        f = ease(float(np.clip((lt - t0) / 0.25, 0, 1)))
        tx, ty = -210 + (i % 4) * 140, cy + 20 + (i // 4) * 110
        spider(cv, tx, -900 + (ty + 900) * f, 0.4, T, ang=np.pi + 0.3 * np.sin(i), walk=0.5)
    badge(cv, f'{n} SPIDER' + ('' if n == 1 else 'S'), y=-690, col=(255, 236, 80), w=470)
    return cv


def b2_mountain(lt, dur, T):
    """A tiny spider on the sheet, staring up at him: a huge, shaking blanket mountain with his head on top."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1c2a4a', '#0e1630', vignette=0.3)
    jx, jy = 6 * np.sin(T * 31), 4 * np.sin(T * 23)
    cv.shape(ellipse(jx, -330 + jy, 330, 120), (-340 + jx, -460 + jy, 340 + jx, -200 + jy), ramp('#ffffff', '#d8dde4', '#ffffff'))   # pillow
    hs = 1.5
    sub_poster(cv, -390, -420, 0.9, T=T)                                         # posters on his bedroom wall
    box(cv, 395, -420, 110, 110, WOOD, r=8)
    box(cv, 395, -420, 92, 92, ramp('#2a3a6a', '#1a2448', '#4a5a9a'), r=4, ow=0, shadow=0)
    bell_icon(cv, 395, -440, 60)
    label(cv, 'HIT THE BELL', 395, -350, 24, (255, 236, 80), stroke=2)
    guy(cv, jx, -330 + 762 * hs + jy, hs, face='snore', legs=False, ground=False)
    mtn = smooth(120, poly([(-760 + jx, 900), (jx, -170 + jy), (760 + jx, 900)]), ellipse(jx, 500, 700, 380))
    cv.shape(mtn, (-800, -200, 800, 960), BLANK)                               # the blanket mountain
    for k in range(3):
        yy = 60 + k * 130
        line(cv, [(-120 - k * 120 + jx, yy + jy), (120 + k * 120 + jx, yy + 20 + jy)], 6, flat(hexc('#2f559a')), a=0.5)
    for sx in (-1, 1):                                                         # shake marks
        for k in range(3):
            xx = sx * (330 + k * 34)
            line(cv, [(xx, -40 + k * 60), (xx + sx * 44, -64 + k * 60)], 8, flat(hexc('#ffffff')), a=0.55 + 0.4 * np.sin(T * 20 + k))
    box(cv, 0, 760, 700, 200, ramp(*SHEETC), r=0, ow=0, shadow=0)
    spider(cv, -250, 600, 0.36, T, ang=0.4, walk=0.0, worried=True)
    label(cv, '!', -250, 470, 90, (255, 236, 80))
    hook_text(cv, 'MOUNTAIN', lt, y=-720, size=150, pop_t=dur * 0.45, color=(255, 236, 80))
    return cv


def b3_vibes(lt, dur, T):
    """Inside his chest: heart thumping, lungs heaving, snores, all sending out shakes."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#0e1a30', '#060c18', vignette=0.35)
    for k in range(4):                                                         # vibration rings
        ph = (lt * 0.9 + k / 4) % 1
        r = 180 + 420 * ph
        cv.shape(subtract(circle(0, -120, r), circle(0, -120, r - 10)), (-r - 2, -120 - r - 2, r + 2, -120 + r + 2), flat(hexc('#7fd2ff')),
                 ow=0, shadow=0, flat=True, alpha=0.6 * (1 - ph))
    chest(cv, 0, -40, 0.8, T, dia=0.5 + 0.5 * np.sin(T * 2.4), lung=0.5 + 0.5 * np.sin(T * 2.4))
    beat = max(0, np.sin(T * 2 * np.pi * 1.2)) ** 4
    heart_icon(cv, 40, -150, 0.55, beat)
    label(cv, 'THUMP', 300, -330, 56, (255, 120, 110), a=float(beat > 0.2))
    label(cv, 'HEAVE', -300, -330, 56, (180, 220, 255))
    if lt > dur * 0.55:
        hook_text(cv, 'SNORE', lt, y=-720, size=150, pop_t=dur * 0.55, color=(220, 230, 255))
    return cv


def b4_danger(lt, dur, T):
    """Close on the spider: shakes rolling in through its legs, and it reads danger."""
    cv = Canvas(0, 0, 1.0)
    cv.background(*SHEETC, vignette=0.25)
    k = float(np.clip(lt / (dur * 0.5), 0, 1))
    for q in range(5):                                                         # waves rolling in from the left
        ph = (lt * 0.7 + q / 5) % 1
        xx = -700 + 900 * ph
        pts = [(xx + 18 * np.sin(yy * 0.02 + T * 8), yy) for yy in np.linspace(-500, 300, 20)]
        line(cv, pts, 8, flat(hexc('#3fa2ee')), a=0.6 * (1 - ph))
    box(cv, 330, 640, 150, 110, ramp('#ffffff', '#dfe6ee', '#ffffff'), r=8)    # mattress tag
    line(cv, [(180, 640), (120, 640)], 10, flat(hexc('#c8d0d8')))
    label(cv, 'DO NOT REMOVE', 330, 585, 26, (200, 60, 50), stroke=0)
    label(cv, 'UNTIL YOU', 330, 630, 30, (40, 34, 50), stroke=0)
    label(cv, 'SUBSCRIBE', 330, 690, 46, (230, 33, 23), stroke=0)
    jit = 6 * np.sin(T * 47) * k
    spider(cv, 60 + jit, -80, 2.0, T, ang=-0.3, walk=0.15, worried=k > 0.5)
    if lt > dur * 0.5:
        badge(cv, 'DANGER!', y=-660, col=(255, 90, 80), w=420)
    return cv


def b5_breath(lt, dur, T):
    """Back on his face: a hot gust out of his mouth sends the spider tumbling away."""
    cv = Canvas(0, 0, 1.0)
    sleeper(cv, T, breath=0.0)
    k = ease(float(np.clip((lt - dur * 0.25) / (dur * 0.6), 0, 1)))
    gust = float(np.clip((lt - dur * 0.15) / 0.3, 0, 1))
    base = np.arctan2(-588, 430)                                               # aimed up and right, where the spider gets blown
    for q in range(9):                                                         # hot breath streaks
        ph = (lt * 1.8 + q / 9) % 1
        a0 = base + (q - 4) * 0.09
        r0, r1 = 90 + 460 * ph, 230 + 460 * ph
        line(cv, [(np.cos(a0) * r0, MOUTH_Y + np.sin(a0) * r0), (np.cos(a0) * r1, MOUTH_Y + np.sin(a0) * r1)],
             24, BREATH, a=0.9 * gust * (1 - 0.7 * ph))
    x, y = path(k, (150, -80), (430, -620))
    spider(cv, x, y, 0.9 - 0.3 * k, T, ang=2.4 + 9 * k, walk=0.0, worried=True)
    if lt > dur * 0.3:
        hook_text(cv, 'WHOOSH', lt, y=-780, size=150, pop_t=dur * 0.3, color=(255, 190, 120))
    return cv


def b6_year(lt, dur, T):
    """The whole bed from above while a year flips by: just two spiders wander across."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#b07a48', '#8a5a30', vignette=0.3)                          # wood floor
    for k in range(-8, 9):
        line(cv, [(k * 90, -960), (k * 90, 960)], 4, flat(hexc('#7a4e28')), a=0.5)
    box(cv, 0, 120, 470, 560, ramp('#c04a5a', '#8a2a3a', '#e07a8a'), r=30, shadow=0)   # rug
    for sx in (-1, 1):                                                          # nightstands
        box(cv, sx * 410, -380, 95, 95, WOOD, r=10)
    disc(cv, -410, -380, 48, YELLOW, ow=3)                                      # lamp
    cv.glow(circle(-410, -380, 40), (-460, -430, -360, -330), '#ffe08a', 40, 0.5)
    sub_phone(cv, 410, -380, 0.8, T)
    box(cv, 0, 760, 300, 110, ramp('#6a4a2a', '#4a3018', '#8a6a4a'), r=14)      # doormat
    label(cv, 'SUBSCRIBE', 0, 778, 70, (255, 214, 120), stroke=0)
    bed(cv, T, 0, -90, 0.7, face='snore', blanket=True)
    k = float(np.clip(lt / (dur * 0.92), 0, 1))
    for (k0, k1, yy) in ((0.12, 0.42, -120), (0.55, 0.88, 220)):
        if k0 < k < k1:
            u = (k - k0) / (k1 - k0)
            spider(cv, -480 + 960 * u, yy, 0.5, T, ang=np.pi / 2, walk=1.0)
    badge(cv, MONTHS[min(int(k * 12), 11)], y=-660, col=(127, 210, 255), w=260)
    n = int(k > 0.27) + int(k > 0.72)
    label(cv, f'SPIDERS: {n}', 0, -520, 64, (255, 236, 80))
    return cv


def b7_fake(lt, dur, T):
    """The 'fun fact' card, question marks, then a red MADE UP stamp."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#c08a52', '#9a6a3a', vignette=0.35)                        # corkboard
    rng = np.random.default_rng(5)
    for px_, py_ in rng.uniform([-540, -960], [540, 960], (160, 2)):
        disc(cv, px_, py_, 4, ramp('#8a5a2a'), ow=0, shadow=0, flat=True)
    sticky(cv, -330, 640, 1.1, ['DON\'T', 'FORGET TO', 'SUBSCRIBE'])
    sub_poster(cv, 320, 650, 0.85, top='SMASH LIKE')
    box(cv, 0, -250, 400, 250, CARD, r=30)
    disc(cv, 0, -485, 14, SUBRED, ow=2.5, shadow=0)
    label(cv, 'FUN FACT:', 0, -420, 58, (200, 60, 50), stroke=0)
    label(cv, 'YOU SWALLOW', 0, -320, 66, INKT, stroke=0)
    label(cv, '8 SPIDERS', 0, -225, 86, INKT, stroke=0)
    label(cv, 'A YEAR', 0, -130, 66, INKT, stroke=0)
    for q, (qx, qy) in enumerate(((-420, -520), (420, -480), (-400, 170), (400, 190), (0, -560))):
        t0 = dur * (0.15 + 0.07 * q)
        if lt > t0:
            label(cv, '?', qx + 10 * np.sin(T * 3 + q), qy, int(110 * min(1, (lt - t0) / 0.15)), (255, 236, 80))
    t_st = dur * 0.6
    if lt > t_st:
        f = min(1.0, (lt - t_st) / 0.12)
        sc = 1.6 - 0.6 * ease(f)
        cv.shape(subtract(rbox(0, 20, 360 * sc, 95 * sc, 24 * sc), rbox(0, 20, 340 * sc, 77 * sc, 16 * sc)),
                 (-370 * sc, 20 - 100 * sc, 370 * sc, 20 + 100 * sc), STAMP, ow=0, shadow=0, flat=True, alpha=0.95)
        label(cv, 'MADE UP', 0, 35, int(120 * sc), (226, 48, 42))
    return cv


def b8_fluke(lt, dur, T):
    """Back on his face: the spider turns round on the pillow and walks off."""
    cv = Canvas(0, 0, 1.0)
    sleeper(cv, T)
    turn = ease(float(np.clip(lt / (dur * 0.3), 0, 1)))
    u = ease(float(np.clip((lt - dur * 0.3) / (dur * 0.7), 0, 1)))
    x, y = path(u, (260, -360), (640, -700))
    spider(cv, x, y, 0.9, T, ang=-2.6 + (2.6 + 0.84) * turn, walk=1.0)
    badge(cv, 'RARE FLUKE', y=-680, col=(127, 210, 255), w=480)
    return cv


# the cuts that go INSIDE something: into his open mouth, and down into his chest (screen px)
DIVE = {1: (540, int(960 + MOUTH_Y)), 3: (540, 1000)}

BEATS = [b0_hook, b1_mouth, b2_mountain, b3_vibes, b4_danger, b5_breath, b6_year, b7_fake, b8_fluke]

if __name__ == '__main__':
    run(BEATS)
