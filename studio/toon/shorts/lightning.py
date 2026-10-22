#!/usr/bin/env python3
"""What happens when you get struck by lightning. Opens a split second after the bolt hits his umbrella: white flash fading,
him lit up and crackling; loops back into it (the last line plays over him walking through the storm)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

BOLT = '#fff6a0'
GRASS = ramp('#3d8a50', '#25603a', '#5fae6e')
UMB = ramp('#3a3a4a', '#1e1e2a', '#5a5a6e')
BARN = ramp('#b03a2e', '#7a2018', '#d8604e')
SKINC = ramp('#f2b48c', '#c97f62', '#ffd9bd')
FERN = flat(hexc('#d8404a'))
GX, GY, GS = -20, 880, 1.3
HAND_L = (150, -560)                              # his umbrella hand, guy units


def storm(cv, T, flash=0.0, rain=1.0):
    """Stormy field: dark clouds, rolling hill, a red barn that says SUBSCRIBE, a fence with a LIKE poster (Easter eggs)."""
    cv.background('#2a3048', '#5a6680', vignette=0.3)
    for i, (x, y, r) in enumerate(((-380, -820, 200), (-60, -860, 240), (300, -820, 220), (520, -760, 160), (-560, -720, 150))):
        cloud(cv, x + 20 * np.sin(T * 0.3 + i), y, r, col=ramp('#3a4058', '#262a3c', '#5a6278'))
    cv.shape(ellipse(0, 60, 900, 380), (-900, -320, 900, 440), GRASS, ow=3, shadow=0)
    box(cv, 0, 600, 700, 380, GRASS, r=0, ow=0, shadow=0)
    bx, by = 330, -300                                                          # the barn
    box(cv, bx, by, 120, 80, BARN, r=6)
    cv.shape(poly([(bx - 135, by - 80), (bx + 135, by - 80), (bx, by - 170)]), (bx - 137, by - 172, bx + 137, by - 78), ramp('#5a2a20'), ow=3, shadow=0)
    box(cv, bx, by - 30, 92, 22, ramp('#ffffff'), r=4, shadow=0)
    label(cv, 'SUBSCRIBE', bx, by - 22, 30, (176, 40, 30), stroke=0)
    box(cv, bx, by + 40, 34, 40, ramp('#5a2a20'), r=4, shadow=0)
    for k in range(5):                                                          # fence with a poster on it
        x = -520 + k * 70
        line(cv, [(x, -230), (x, -150)], 10, WOOD, ow=2, flat=False)
    line(cv, [(-540, -210), (-240, -210)], 8, WOOD, ow=2, flat=False); line(cv, [(-540, -170), (-240, -170)], 8, WOOD, ow=2, flat=False)
    sub_poster(cv, -380, -300, 0.55, T=T)
    if rain > 0:
        for q in range(40):
            x = -540 + (q * 97) % 1080
            y = -960 + ((T * 1400 + q * 211) % 1920)
            line(cv, [(x, y), (x - 10, y + 50)], 3, flat(hexc('#c8d8f0')), a=0.5 * rain)
    if flash > 0:
        cv.flash('#ffffff', flash)


def umbrella_guy(cv, T, x=GX, y=GY, s=GS, face='calm', zap=0.0, look=(0, -1)):
    right = reach(1, *HAND_L)
    guy(cv, x, y, s, face=face, arms=((12, 0), right), tint=('#8fd8ff', 0.6 * zap) if zap > 0 else None, look=look)
    hx, hy = x + HAND_L[0] * s, y + HAND_L[1] * s
    tip = (hx, hy - 420 * s)
    line(cv, [(hx, hy + 30 * s), tip], 10 * s, STEEL, ow=3, flat=False)          # metal pole
    cx, cy = hx, hy - 330 * s
    cv.shape(inter(ellipse(cx, cy + 40 * s, 260 * s, 150 * s), lambda X, Y: Y - (cy + 40 * s)), (cx - 262 * s, cy - 112 * s, cx + 262 * s, cy + 42 * s), UMB)
    front_arm(cv, x, y, s, 1, *right)
    if zap > 0:
        hx_, hy_ = x, y - 762 * s
        for j, dx in enumerate((-70, -35, 0, 35, 70)):                          # hair on end
            line(cv, [(hx_ + dx * s, hy_ - 110 * s), (hx_ + dx * 1.4 * s, hy_ - (190 + 20 * (j % 2)) * s)], 7 * s, HAIR, ow=2.5, a=zap)
        for q in range(5):                                                      # crackles around him
            a0 = q * 1.25 + T * 9
            p0 = (x + np.cos(a0) * 260 * s, y - 450 * s + np.sin(a0) * 380 * s)
            pts = jagged(p0, (p0[0] + 60, p0[1] + 50), int(abs(T) * 30) + q, depth=3, rough=0.6)
            line(cv, pts, 5, flat(hexc(BOLT)), a=zap)
    return tip


def bolt(cv, p0, p1, seed, a=1.0, w=16):
    pts = jagged(p0, p1, seed, depth=6, rough=0.28)
    cv.glow(polyline(pts, w * 0.5), bbox_of(pts, w), '#9fd8ff', 60, 0.9 * a)
    line(cv, pts, w, flat(hexc(BOLT)), a=a)


def fern_segments(seed=3):
    """A branching Lichtenberg-style fern: list of (p0, p1, depth)."""
    rng = np.random.default_rng(seed)
    out = []

    def grow(p, ang, L, d):
        if d > 6 or L < 10:
            return
        q = (p[0] + np.cos(ang) * L, p[1] + np.sin(ang) * L)
        out.append((p, q, d))
        grow(q, ang + rng.uniform(-0.25, 0.25), L * 0.82, d + 1)
        if rng.random() < 0.85:
            grow(q, ang + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9), L * 0.6, d + 1)
    for k in range(4):
        grow((-300, 200 - k * 30), -0.9 + k * 0.45, 150, 0)
    return out


FERN_SEGS = fern_segments()


def skin_close(cv, T, grow=1.0, fade=0.0):
    """Close on the skin of his back: the red fern pattern spreading, then fading."""
    cv.background('#f2b48c', '#c97f62', vignette=0.3)
    a = 1 - fade
    for p, q, d in FERN_SEGS:
        if d / 7 > grow:
            continue
        line(cv, [p, q], max(3, 22 - d * 3), FERN, a=a * (0.9 - d * 0.06))
    box(cv, 330, 650, 100, 36, ramp('#f2d0a0', '#d8b080', '#fff0d0'), r=14)     # a bandage, with a little message
    label(cv, 'SUBSCRIBE', 330, 660, 30, (176, 40, 30), stroke=0)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """lt < 0: walking through the storm under his umbrella. At lt = -0.08 the bolt hits; frame one is the flash fading."""
    cv = Canvas(0, 0, 1.0)
    hit = lt > -0.3
    u = float(np.clip((lt + 0.3) / 0.8, 0, 1))
    uf = float(np.clip((lt + 0.3) / 0.4, 0, 1))
    flash = (1 - uf) ** 3 * 0.7 if hit else (0.35 if -1.4 < lt < -1.3 else 0.0)
    storm(cv, T)
    walk = 6 * abs(np.sin(lt * 6)) if not hit else 0
    tip = umbrella_guy(cv, T, y=GY - walk, face='shock' if hit else 'calm', zap=(1 - 0.5 * u) if hit else 0.0, look=(0, -1))
    if hit and u < 0.9:
        bolt(cv, (tip[0] - 80, -960), tip, int(lt * 25) % 3 + 7, a=1 - u)
    if flash > 0:
        cv.flash('#ffffff', flash)
    if hit:
        hook_text(cv, 'ZAP!', lt + 0.3, y=-780, size=200, color=(255, 236, 80))
    return cv


def b1_heat(lt, dur, T):
    """Close on the bolt: the counter runs up to 50,000 degrees."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#141a30', '#0a0e1c', vignette=0.4)
    bolt(cv, (-80, -960), (60, 500), int(T * 12) % 5, a=1.0, w=40)
    k = ease(float(np.clip(lt / (dur * 0.7), 0, 1)))
    deg = int(round(50000 * k / 100)) * 100
    badge(cv, f'{deg:,}°F', y=-560, col=(255, 140, 60), w=520)
    if k > 0.99:
        hook_text(cv, 'HOT', lt, y=-780, size=170, pop_t=dur * 0.72, color=(255, 120, 60))
    neon_sign(cv, 0, 720, 'SUBSCRIBE', '#ff8a3a', T)
    return cv


def b2_sun(lt, dur, T):
    """The sun's surface vs the bolt: five times hotter."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#0a0a1e', '#000008', vignette=0.3)
    for q in range(30):
        disc(cv, -520 + (q * 151) % 1040, -900 + (q * 233) % 1500, 3 + q % 3, ramp('#ffffff'), ow=0, shadow=0)
    sun(cv, -250, -330, 150, T)
    bolt(cv, (250, -560), (230, -120), int(T * 10) % 4, w=24)
    k = ease(float(np.clip(lt / (dur * 0.6), 0, 1)))
    meter(cv, 0, 120, 600, 0.2 * k, YELLOW, 'SUN SURFACE')
    box(cv, 0, 260, 310, 46, DARK, r=30)
    if k > 0.01:
        box(cv, -300 + 300 * k, 260, 300 * k, 34, ramp('#9fd8ff', '#5aa8e0', '#e0f4ff'), r=24, ow=0)
    label(cv, 'LIGHTNING', 0, 170, 54, (255, 255, 255))
    if k > 0.98:
        hook_text(cv, '5X HOTTER', lt, y=-780, size=150, pop_t=dur * 0.62, color=(255, 236, 80))
    label(cv, 'LIKE IF YOU KNEW', 0, 720, 30, (140, 150, 190), stroke=0, a=0.8)
    return cv


def b3_through(lt, dur, T):
    """An x-ray look: the current runs from the umbrella down through his body to the ground."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#0e1430', '#060a18', vignette=0.4)
    s, x, y = 1.1, 0, 760
    guy(cv, x, y, s, face='shock', tint=('#2a3a6a', 0.75), arms=((12, 0), (150, 20)))
    k = float(np.clip(lt / (dur * 0.6), 0, 1))
    path = [(x + 150, y - 900 * s), (x + 120, y - 640 * s), (x + 40, y - 560 * s), (x, y - 450 * s), (x - 30, y - 330 * s), (x - 50, y - 150 * s), (x - 60, y - 20 * s)]
    n = max(2, int(len(path) * k + 1))
    pts = []
    for a_, b_ in zip(path[:n - 1], path[1:n]):
        pts += jagged(a_, b_, int(T * 20), depth=3, rough=0.25)
    if len(pts) > 1:
        cv.glow(polyline(pts, 6), bbox_of(pts, 20), '#9fd8ff', 50, 1.0)
        line(cv, pts, 10, flat(hexc(BOLT)))
    hook_text(cv, 'SPLIT SECOND', lt, y=-780, size=120, pop_t=dur * 0.55, color=(159, 216, 255))
    xray_tag(cv, -360, 720, ('LIKE', '+ SUBSCRIBE'))
    return cv


def b4_shoes(lt, dur, T):
    """The jolt throws him up, and his shoes go flying."""
    cv = Canvas(0, 0, 1.0)
    storm(cv, T)
    k = float(np.clip(lt / (dur * 0.7), 0, 1))
    jump = -160 * np.sin(np.pi * k)
    guy(cv, -20, 600 + jump, 1.0, face='scream', arms=((150, 20), (150, 20)), tint=('#8fd8ff', 0.3 * (1 - k)), legs=True)
    for sx in (-1, 1):                                                          # the shoes flying off, spinning
        sxp = -20 + sx * (60 + 380 * k); syp = 590 - 700 * k + 900 * k * k
        cv.shape(rotell(sxp, syp, 44, 24, np.degrees(T * 12 * sx)), (sxp - 50, syp - 50, sxp + 50, syp + 50), SHOE)
    hook_text(cv, 'SHOES OFF!', lt, y=-780, size=150, pop_t=dur * 0.3, color=(255, 255, 255))
    return cv


def b5_heart(lt, dur, T):
    """The heart: a steady beat, then the shock throws it off, then flat."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1418', '#1a0a0c', vignette=0.45)
    t_hit = dur * 0.45
    hitk = float(np.clip((lt - t_hit) / 0.3, 0, 1))
    beat = max(0, np.sin(T * 2 * np.pi * 1.2)) ** 4 * (1 - hitk)
    jx = hitk * 12 * np.sin(T * 80) * (lt < t_hit + 0.8)
    heart_icon(cv, jx, -380, 1.2 + 0.1 * beat, beat)
    if hitk > 0:
        bolt(cv, (60, -960), (20, -460), int(T * 20) % 3, a=float(lt < t_hit + 0.5), w=18)
    box(cv, 0, 120, 420, 130, ramp('#0e1a14', '#06100a', '#1a2a20'), r=24)
    xs = np.linspace(-390, 390, 120)
    pts = []
    for xx in xs:
        t = lt - (390 - xx) / 780 * 2.4
        if t < t_hit:
            ph = (t * 1.2) % 1
            v = 1.0 if 0.45 < ph < 0.48 else (-0.45 if 0.48 <= ph < 0.52 else 0.0)
        elif t < t_hit + 0.8:
            v = 0.6 * np.sin(t * 41) + 0.3 * np.sin(t * 67)
        else:
            v = 0.0
        pts.append((xx, 120 - v * 70))
    line(cv, pts, 7, flat(hexc('#5dff8a')))
    label(cv, 'LIKE-O-GRAPH 3000', 0, 225, 26, (120, 200, 140), stroke=0)
    if lt > t_hit + 0.8:
        hook_text(cv, 'STOP', lt, y=-780, size=170, pop_t=t_hit + 0.8, color=(255, 90, 80))
    return cv


def b6_survive(lt, dur, T):
    """Ten little people: nine get a thumbs up (they survive)."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a7aa8', '#bcd4ee', vignette=0.25)
    box(cv, 0, 500, 700, 460, GRASS, r=0, ow=0, shadow=0)
    k = float(np.clip((lt - dur * 0.35) / (dur * 0.5), 0, 1))
    for i in range(10):
        r_, c_ = divmod(i, 5)
        x, y = -360 + c_ * 180, -60 + r_ * 330
        alive = i != 7
        guy(cv, x, y, 0.32, face='happy' if alive else 'closed', tint=None if alive else ('#808080', 0.6), shirt=SHIRT)
        if alive and k > i / 10:
            thumb_icon(cv, x + 40, y - 330, 30)                                 # each survivor gets a like
    badge(cv, '9 OUT OF 10', y=-620, col=(127, 255, 160), w=460)
    if k > 0.3:
        hook_text(cv, 'SURVIVE', lt, y=-790, size=150, pop_t=dur * 0.5, color=(127, 255, 160))
    return cv


def b7_fern(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    skin_close(cv, T, grow=ease(float(np.clip(lt / (dur * 0.7), 0, 1))))
    hook_text(cv, 'FERN', lt, y=-780, size=170, pop_t=dur * 0.55, color=(255, 255, 255))
    return cv


def b8_fade(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    k = float(np.clip((lt - dur * 0.35) / (dur * 0.6), 0, 1))
    skin_close(cv, T, grow=1.0, fade=0.85 * k)
    box(cv, 380, -560, 95, 110, ramp('#ffffff', '#d8dde4', '#ffffff'), r=8)    # calendar: days going by
    box(cv, 380, -645, 95, 24, ramp('#e2302a'), r=6, shadow=0)
    label(cv, 'DAY', 380, -639, 26, (255, 255, 255), stroke=0)
    label(cv, str(1 + int(3 * k)), 380, -540, 90, (40, 34, 50), stroke=0)
    label(cv, 'TO DO: SUBSCRIBE', 380, -480, 15, (200, 40, 40), stroke=0)
    box(cv, -60, -760, 380, 58, DARK, r=26)
    label(cv, 'LICHTENBERG FIGURE', -60, -752, 60, (255, 236, 80))
    return cv


# the cut that goes INSIDE him: through his chest to the heart (screen px)
DIVE = {5: (540, 1000)}

BEATS = [b0_hook, b1_heat, b2_sun, b3_through, b4_shoes, b5_heart, b6_survive, b7_fern, b8_fade]

if __name__ == '__main__':
    run(BEATS)
