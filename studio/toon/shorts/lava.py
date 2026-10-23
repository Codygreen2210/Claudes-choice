#!/usr/bin/env python3
"""What would really happen if you fell into lava. Opens mid-fall: he's just slipped off the crater rim and is dropping
toward a glowing lava lake; loops back into it (the last line plays over him peeking over the edge)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

LAVA = ramp('#ff7a1a', '#d8400a', '#ffd23f')
CRUST = ramp('#3a2a28', '#1e1414', '#5a4440')
ROCKV = ramp('#4a3a3a', '#2a2020', '#6a5a58')
SKYV = ('#3a1a20', '#8a2a1a')
FLAME = ramp('#ff8a2a', '#e24a1a', '#ffd23f')
BAG = ramp('#3a5a3a', '#203a20', '#5a7a5a')
LAKE_Y = 260
RIM = (-330, -300)                               # where he stands on the rim (his feet)


def crater(cv, T, shimmer=0.0):
    """Inside the crater: red smoky sky, dark rock walls, a lava lake with drifting crust plates and popping bubbles.
    A warning sign on the rim carries the one Easter egg (a little thumbs-up sticker)."""
    cv.background(*SKYV, vignette=0.3)
    for i in range(5):                                                         # smoke drifting up
        x = -400 + i * 200 + 40 * np.sin(T * 0.4 + i)
        y = -700 - ((T * 30 + i * 90) % 200)
        cloud(cv, x, y, 110, a=0.35, col=ramp('#5a3a3a', '#3a2424', '#7a5a5a'))
    left = [(-560, -300), (-420, -310), (-330, -296), (-240, -300), (-200, -150), (-230, 0), (-180, LAKE_Y), (-560, LAKE_Y)]
    right = [(560, -380), (420, -400), (330, -370), (280, -200), (300, -40), (230, LAKE_Y), (560, LAKE_Y)]
    for pts in (left, right):                                                  # jagged cliff walls with rock layers
        cv.shape(poly(pts), bbox_of(pts, 4), ROCKV, ow=4, shadow=0, bevel=10)
    for k in range(6):
        yy = -240 + k * 85
        line(cv, [(-560, yy), (-380, yy + 12), (-230 + 10 * (k % 2), yy - 6)], 5, flat(hexc('#2a1e1e')), a=0.6)
        line(cv, [(560, yy - 60), (420, yy - 48), (300, yy - 64)], 5, flat(hexc('#2a1e1e')), a=0.6)
    line(cv, [(-470, -360), (-470, -300)], 8, WOOD, ow=2, flat=False)          # the warning sign
    box(cv, -470, -390, 60, 34, ramp('#ffd23f', '#d09a10', '#fff08a'), r=6)
    label(cv, 'DANGER', -470, -384, 22, (60, 30, 10), stroke=0)
    thumb_icon(cv, -430, -360, 11)
    box(cv, 0, LAKE_Y + 360, 700, 360, LAVA, r=0, ow=0, shadow=0)             # the lake
    rng = np.random.default_rng(4)
    for q in range(9):                                                         # crust plates drifting
        cx = -500 + ((q * 140 + T * 18) % 1100)
        cy = LAKE_Y + 60 + (q % 3) * 130
        pts = [(cx + np.cos(a) * (60 + 20 * rng.random()), cy + np.sin(a) * (24 + 10 * rng.random())) for a in np.linspace(0, 2 * np.pi, 7)[:-1]]
        cv.shape(poly(pts), bbox_of(pts, 4), CRUST, ow=3, shadow=0)
    for q in range(5):                                                         # bubbles popping
        ph = (T * 0.6 + q / 5) % 1
        bx = -400 + q * 200 + 30 * np.sin(q)
        disc(cv, bx, LAKE_Y + 40 + q * 30, 10 + 30 * ph, ramp('#ffd23f', '#ff8a2a', '#fff6a0'), ow=2, shadow=0, alpha=1 - ph)
    cv.glow(rbox(0, LAKE_Y, 600, 10, 5), (-600, LAKE_Y - 40, 600, LAKE_Y + 40), '#ff6a1a', 120, 0.55)
    if shimmer > 0:
        import cv2
        H_, W_ = cv.img.shape[:2]
        yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
        cv.img = np.ascontiguousarray(cv2.remap(cv.img, xx + shimmer * 5 * np.sin(yy / 24 + T * 9), yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))


def faller(cv, x, y, s, T, fire=0.0, face='scream'):
    flail = 20 * np.sin(T * 12)
    guy(cv, x, y, s, face=face, arms=((150 + flail, 30), (150 - flail, 30)), tint=('#ff6a1a', 0.25 * fire) if fire > 0 else None)
    if fire > 0:                                                               # cartoon flames licking up from his shoes and legs
        for q in range(6):
            ph = (T * 3 + q / 6) % 1
            fx = x + (-60 + q * 24) * s
            fy = y - (20 + 200 * ph) * s
            cv.shape(smooth(8, circle(fx, fy, (34 - 16 * ph) * s), circle(fx, fy - 26 * s, (18 - 8 * ph) * s)), (fx - 40 * s, fy - 60 * s, fx + 40 * s, fy + 40 * s),
                     FLAME, ow=2.5, shadow=0, alpha=fire * (1 - ph))


def fall_pos(lt):
    """Standing on the rim until lt = -0.6, then falling toward the middle of the lake."""
    if lt < -1.0:
        return RIM[0], RIM[1], False
    u = lt + 1.0
    x = RIM[0] + 330 * (1 - np.exp(-u * 1.5))
    y = RIM[1] + 100 * u
    return x, y, True


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    crater(cv, T)
    x, y, falling = fall_pos(lt)
    if falling:
        faller(cv, x, y, 0.6, T)
        hook_text(cv, 'LAVA', lt + 1.0, y=-800, size=200, color=(255, 140, 40))
    else:
        lean = float(np.clip((lt + 2.0) / 1.0, 0, 1))
        guy(cv, x + 20 * lean, y, 0.6, face='worried', look=(1, 1), arms=((12, 0), (40 * lean, 20)))
    return cv


def b1_heat(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    crater(cv, T, shimmer=1.0)
    k = ease(float(np.clip(lt / (dur * 0.7), 0, 1)))
    thermo(cv, 330, -320, 2000 * k, lo=0, hi=2200, h=600, label_=False)
    badge(cv, f'{int(round(2000 * k / 50)) * 50:,}°F', y=-760, x=200, col=(255, 140, 40), w=380)
    m = k
    cv.shape(smooth(20, rbox(-150, -100 + 60 * m, 90, 90 * (1 - 0.7 * m), 20), ellipse(-150, -10, 90 + 60 * m, 14 + 10 * m)), (-260, -200, -40, 20),
             ramp('#6a5a58') if m < 0.5 else ramp('#ff8a2a', '#d8400a', '#ffd23f'))
    label(cv, 'ROCK', -150, -260, 50, (255, 255, 255))
    return cv


def b2_movie(lt, dur, T):
    """IN MOVIES: a film-strip frame, and a guy sinking into lava like it's a pool."""
    cv = Canvas(0, 0, 1.0)
    crater(cv, T)
    k = ease(float(np.clip(lt / (dur * 0.8), 0, 1)))
    guy(cv, 0, LAKE_Y + 150 + 500 * k, 0.7, face='scream', arms=((150, 30), (150, 30)))
    box(cv, 0, LAKE_Y + 360, 700, 360, LAVA, r=0, ow=0, shadow=0, alpha=0.85)
    for q in range(3):
        ph = (lt * 1.5 + q / 3) % 1
        r = 60 + 200 * ph
        cv.shape(subtract(ellipse(0, LAKE_Y + 10, r, r * 0.25), ellipse(0, LAKE_Y + 10, r - 10, r * 0.25 - 6)), (-r - 2, LAKE_Y - r * 0.3, r + 2, LAKE_Y + r * 0.3 + 12), ramp('#ffd23f'), ow=0, shadow=0, flat=True, alpha=1 - ph)
    for sx in (-1, 1):                                                         # film strip edges
        box(cv, sx * 500, 0, 40, 960, ramp('#141414'), r=0, ow=0, shadow=0)
        for q in range(12):
            box(cv, sx * 500, -900 + q * 160 + (T * 200) % 160, 16, 26, ramp('#e8e0d0'), r=4, ow=0, shadow=0)
    box(cv, 0, -790, 260, 60, ramp('#141414'), r=12)
    label(cv, 'IN MOVIES', 0, -782, 70, (255, 255, 255))
    return cv


def b3_dense(lt, dur, T):
    """A balance: a person-sized block of lava outweighs him three times over."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1418', '#140a0c', vignette=0.35)
    k = ease(float(np.clip(lt / (dur * 0.6), 0, 1)))
    tilt = 0.32 * k
    cx, cy = 0, -250
    line(cv, [(cx, cy), (cx, 200)], 20, STEEL, ow=3, flat=False)
    box(cv, cx, 210, 120, 24, STEEL, r=8)
    L = 360
    lx, ly = cx - np.cos(tilt) * L, cy - np.sin(tilt) * L
    rx, ry = cx + np.cos(tilt) * L, cy + np.sin(tilt) * L
    line(cv, [(lx, ly), (rx, ry)], 16, STEEL, ow=3, flat=False)
    disc(cv, cx, cy, 24, STEEL)
    for px_, py_ in ((lx, ly), (rx, ry)):
        line(cv, [(px_, py_), (px_, py_ + 140)], 4, flat(hexc('#c8ccd4')))
        box(cv, px_, py_ + 150, 120, 14, STEEL, r=6)
    guy(cv, lx, ly + 136, 0.3, face='worried')
    box(cv, rx, ry + 60, 80, 90, LAVA, r=12)
    cv.glow(rbox(rx, ry + 60, 80, 90, 12), (rx - 90, ry - 40, rx + 90, ry + 160), '#ff6a1a', 40, 0.6)
    label(cv, 'YOU', lx, ly - 140, 54, (255, 255, 255))
    label(cv, 'LAVA', rx, ry - 70, 54, (255, 170, 60))
    if k > 0.95:
        hook_text(cv, '3X DENSER', lt, y=-790, size=160, pop_t=dur * 0.62, color=(255, 140, 40))
    return cv


def b4_thick(lt, dur, T):
    """Two pours side by side: water rushes down, lava oozes like cold honey."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1418', '#140a0c', vignette=0.35)
    k = float(np.clip(lt / dur, 0, 1))
    for sx, col, speed, name in ((-1, ramp('#5ac0ff', '#2a8ad0', '#a8e4ff'), 1.0, 'WATER'), (1, LAVA, 0.12, 'LAVA')):
        x = sx * 240
        box(cv, x, -560, 90, 50, STEEL, r=10)
        reach_ = min(1.0, k * 6 * speed + 0.05)
        top, bot = -510, -510 + 900 * reach_
        w = 26 if sx < 0 else 70
        line(cv, [(x, top), (x, bot)], w, col, ow=3, flat=False)
        if sx > 0:
            disc(cv, x, bot + 20, 60, col, ow=3)
        label(cv, name, x, -680, 56, (255, 255, 255))
    hook_text(cv, 'THICK', lt, y=-810, size=170, pop_t=dur * 0.35, color=(255, 140, 40))
    return cv


def b5_smack(lt, dur, T):
    """He lands on top: SMACK, the surface dents, rings spread, and he doesn't go under."""
    cv = Canvas(0, 0, 1.0)
    crater(cv, T)
    t_hit = dur * 0.3
    if lt < t_hit:
        u = lt / t_hit
        faller(cv, 0, -200 + (LAKE_Y + 30 + 200) * u * u, 0.7, T)
    else:
        dent = float(np.exp(-(lt - t_hit) * 3))
        cv.shape(ellipse(0, LAKE_Y + 30, 220 * (1 + 0.3 * (1 - dent)), 40), (-300, LAKE_Y - 20, 300, LAKE_Y + 80), ramp('#d8400a', '#a82a0a', '#ff8a2a'), ow=3, shadow=0)
        guy(cv, 0, LAKE_Y + 40 + 20 * dent, 0.7, face='shock', arms=((90, 0), (90, 0)))
        for q in range(3):
            ph = ((lt - t_hit) * 1.2 + q / 3) % 1
            r = 120 + 300 * ph
            cv.shape(subtract(ellipse(0, LAKE_Y + 40, r, r * 0.22), ellipse(0, LAKE_Y + 40, r - 10, r * 0.22 - 6)), (-r - 2, LAKE_Y - r * 0.25 + 30, r + 2, LAKE_Y + r * 0.25 + 50),
                     ramp('#ffd23f'), ow=0, shadow=0, flat=True, alpha=1 - ph)
        hook_text(cv, 'SMACK', lt, y=-800, size=190, pop_t=t_hit, color=(255, 255, 255))
    return cv


def b6_fire(lt, dur, T):
    """The real killer: falling through air so hot the heat ripples, and he catches fire before he lands."""
    cv = Canvas(0, 0, 1.0)
    crater(cv, T, shimmer=1.6)
    k = float(np.clip(lt / (dur * 0.7), 0, 1))
    faller(cv, 30 * np.sin(T), 80 + 100 * k, 0.8, T, fire=k)
    cv.flash('#ff4a1a', 0.18 * k)
    if k > 0.5:
        hook_text(cv, 'TOO HOT', lt, y=-800, size=180, pop_t=dur * 0.4, color=(255, 90, 40))
    return cv


def b7_test(lt, dur, T):
    """2002: a scientist on the rim heaves a big trash bag over the edge."""
    cv = Canvas(0, 0, 1.0)
    crater(cv, T)
    k = float(np.clip(lt / (dur * 0.5), 0, 1))
    guy(cv, RIM[0] + 20, RIM[1], 0.6, face='calm', coat=True, glasses=True, shirt=COAT, arms=((60 + 80 * k, 40), (60 + 80 * k, 40)))
    bx = RIM[0] + 120 + 260 * k * k
    by = RIM[1] - 560 * 0.6 + 900 * max(0, k - 0.5) ** 2
    cv.shape(smooth(20, ellipse(bx, by, 70, 80), circle(bx, by - 80, 26)), (bx - 75, by - 110, bx + 75, by + 85), BAG)
    label(cv, '66 LB', bx, by + 10, 34, (230, 240, 230), stroke=0)
    badge(cv, '2002', y=-760, x=250, col=(255, 236, 80), w=240)
    return cv


def b8_burst(lt, dur, T):
    """The bag hits: it dents the surface and the lava bursts up all around it."""
    cv = Canvas(0, 0, 1.0)
    crater(cv, T)
    t_hit = dur * 0.25
    if lt < t_hit:
        u = lt / t_hit
        by = -300 + (LAKE_Y + 10 + 300) * u * u
        cv.shape(smooth(20, ellipse(60, by, 70, 80), circle(60, by - 80, 26)), (-15, by - 110, 135, by + 85), BAG)
    else:
        e = lt - t_hit
        cv.shape(ellipse(60, LAKE_Y + 30, 160, 34), (-110, LAKE_Y - 10, 230, LAKE_Y + 70), ramp('#d8400a', '#a82a0a', '#ff8a2a'), ow=3, shadow=0)
        cv.shape(smooth(20, ellipse(60, LAKE_Y + 10, 70, 46), circle(60, LAKE_Y - 30, 22)), (-15, LAKE_Y - 60, 135, LAKE_Y + 60), ramp('#2a2a2a'))
        rng = np.random.default_rng(8)
        for q in range(28):                                                    # lava fountaining up around it
            vx, vy = rng.uniform(-260, 260), rng.uniform(-900, -500)
            px_, py_ = 60 + vx * e, LAKE_Y + vy * e + 900 * e * e
            if py_ < LAKE_Y + 30:
                disc(cv, px_, py_, 14 + (q % 3) * 6, LAVA, ow=2.5, shadow=0)
        hook_text(cv, 'BURST', lt, y=-800, size=190, pop_t=t_hit, color=(255, 140, 40))
    return cv


BEATS = [b0_hook, b1_heat, b2_movie, b3_dense, b4_thick, b5_smack, b6_fire, b7_test, b8_burst]

if __name__ == '__main__':
    run(BEATS)
