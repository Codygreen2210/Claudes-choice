#!/usr/bin/env python3
"""Why you should never sleep in your contacts. Opens as he nods off in bed, phone glowing on his chest, eyes just shut;
loops back into it (the last line plays over him scrolling, eyes getting heavy)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

SCL = ramp('#ffffff', '#dfe4ea', '#ffffff')
IRIS = ramp('#4a8ad8', '#2a5a9a', '#8ac0ff')
LENS = flat(hexc('#9fe0ff'))
SKINE = ramp('#f2b48c', '#c97f62', '#ffd9bd')
GERM_ = ramp('#7fd34f', '#4f9a2a', '#b6f08a')
AMEBA = ramp('#c8a0e8', '#8a5ab8', '#ecd8ff')
O2C = ramp('#bfe6ff', '#7fb6d9', '#eaf7ff')
BED_Y, BED_S = -330, 0.95


def eye(cv, x, y, r, T, lid=0.0, lens=1.0, cloudy=0.0, red=0.0, dim=0.0, look=(0, 0)):
    """A big close-up eye: white, blue iris, pupil, glossy cornea, the contact lens rim, and a lid that closes (lid 0..1)."""
    cv.shape(ellipse(x, y, r * 1.5, r * 0.95), (x - r * 1.6, y - r, x + r * 1.6, y + r), SCL, ow=4)
    if red > 0:
        for a in (0.3, 0.9, 2.4, 3.0, 3.6, 5.6):
            p0 = (x + np.cos(a) * r * 1.4, y + np.sin(a) * r * 0.85)
            p1 = (x + np.cos(a + 0.2) * r * 0.75, y + np.sin(a + 0.2) * r * 0.55)
            line(cv, [p0, ((p0[0] + p1[0]) / 2 + 10, (p0[1] + p1[1]) / 2), p1], 4, flat(hexc('#e2302a')), a=red)
    ix, iy = x + look[0] * r * 0.3, y + look[1] * r * 0.2
    disc(cv, ix, iy, r * 0.55, IRIS, ow=3)
    disc(cv, ix, iy, r * 0.25, ramp('#0a0a14'), ow=0, shadow=0)
    if dim > 0:
        cv.shape(circle(ix, iy, r * 0.62), (ix - r * 0.7, iy - r * 0.7, ix + r * 0.7, iy + r * 0.7), ramp('#5a6a80'), ow=0, shadow=0, flat=True, alpha=0.45 * dim)
    if cloudy > 0:
        cv.shape(circle(ix, iy, r * 0.6), (ix - r * 0.7, iy - r * 0.7, ix + r * 0.7, iy + r * 0.7), ramp('#f4f4f8'), ow=0, shadow=0, alpha=0.8 * cloudy)
    cv.shape(subtract(circle(ix, iy, r * 0.74), circle(ix, iy, r * 0.69)), (ix - r * 0.8, iy - r * 0.8, ix + r * 0.8, iy + r * 0.8), LENS, ow=0, shadow=0, flat=True, alpha=0.8 * lens)
    disc(cv, ix - r * 0.22, iy - r * 0.22, r * 0.1, ramp('#ffffff'), ow=0, shadow=0, alpha=0.9)
    if lid > 0:                                                                # the lid sliding down over it
        edge = y - r * 0.95 + lid * r * 1.95
        cv.shape(inter(ellipse(x, y, r * 1.55, r * 1.0), lambda X, Y, E=edge: Y - E), (x - r * 1.6, y - r * 1.05, x + r * 1.6, edge + 4), SKINE, ow=4)
        for q in range(7):
            lx = x - r * 1.1 + q * r * 0.37
            ly = edge + 0 * q
            line(cv, [(lx, ly), (lx + (q - 3) * 4, ly + 26 * (1 - abs(q - 3) / 5))], 5, flat(hexc('#2a1a12')))


def o2(cv, x, y, s=1.0, a=1.0):
    disc(cv, x, y, 22 * s, O2C, ow=2.5, shadow=0, alpha=a)
    label(cv, 'O2', x, y + 6 * s, int(22 * s), (30, 70, 110), a=a, stroke=0)


def bedroom(cv, T, eyes='calm', glow=1.0, tilt=0.0):
    """Top-down: him in bed, phone glowing on his chest. The pillowcase says LIKE: the one Easter egg."""
    cv.background('#1c2238', '#0e1220', vignette=0.35)
    box(cv, 0, BED_Y + 250 * BED_S, 430 * BED_S, 760 * BED_S, ramp('#a8693a', '#6e4122', '#d08f58'), r=40 * BED_S)
    box(cv, 0, BED_Y + 260 * BED_S, 400 * BED_S, 730 * BED_S, ramp('#d8dce8'), r=30 * BED_S)
    box(cv, 0, BED_Y - 380 * BED_S, 300 * BED_S, 110 * BED_S, ramp('#e8ecf4', '#c0c8d8', '#ffffff'), r=80 * BED_S)
    label(cv, 'LIKE', 150, BED_Y - 440 * BED_S, 26, (150, 165, 200), a=0.7, stroke=0)
    guy(cv, 0, BED_Y + 520 * BED_S, BED_S, face=eyes, legs=False, ground=False, tilt_head=tilt, look=(0, 1) if eyes == 'calm' else (0, 0))
    box(cv, 0, BED_Y + 520 * BED_S, 390 * BED_S, 480 * BED_S, ramp('#4f7fd8', '#2f559a', '#8fb4ff'), r=60 * BED_S)
    px, py = 0, BED_Y + 60 * BED_S                                             # the phone, face up on his chest
    box(cv, px, py, 46, 82, DARK, r=12)
    box(cv, px, py, 40, 74, ramp('#bfe6ff', '#7fb6d9', '#eaf7ff'), r=8, ow=0, shadow=0, alpha=0.4 + 0.6 * glow)
    hy = BED_Y + 520 * BED_S - 762 * BED_S
    cv.glow(circle(0, hy + 160, 40), (-120, hy + 40, 120, hy + 280), '#9fd8ff', 50, 0.12 * glow)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """Close on his face on the pillow. lt < 0: scrolling, blinking, lenses glinting. At lt = -0.4 his eyes shut;
    frame one: asleep, the lenses still showing as blue rings under his lids, the phone light on his face."""
    hy = BED_Y + 520 * BED_S - 762 * BED_S
    cv = Canvas(0, hy + 30, 2.4)
    asleep = lt > -0.4
    blink = (not asleep) and ((lt % 0.9) < 0.12)
    bedroom(cv, T, eyes='closed' if (asleep or blink) else 'calm', glow=1.0 if not asleep else max(0.5, 1 - 0.25 * (lt + 0.4)),
            tilt=-0.12 * float(np.clip((lt + 0.4) / 0.5, 0, 1)) if asleep else 0.0)
    tilt = -0.12 * float(np.clip((lt + 0.4) / 0.5, 0, 1)) if asleep else 0.0
    pulse = 0.85 + 0.15 * np.sin(T * 4)
    for sx in (-1, 1):                                                         # the lenses, glowing through
        ex, ey = (sx * 34 + tilt * 30) * BED_S, BED_Y + 520 * BED_S - 768 * BED_S + (0 if asleep else 3)
        cv.glow(subtract(circle(ex, ey, 19), circle(ex, ey, 14)), (ex - 22, ey - 22, ex + 22, ey + 22), '#5ac8ff', 6, 0.6 * pulse)
        cv.shape(subtract(circle(ex, ey, 19), circle(ex, ey, 14)), (ex - 21, ey - 21, ex + 21, ey + 21), ramp('#7fd8ff'), ow=0, shadow=0, flat=True, alpha=pulse)
    if asleep:
        for q in range(3):
            ph = (lt * 0.5 + 0.3 + q / 3) % 1
            label(cv, 'Z', 60 + 20 * ph, hy - 40 - 70 * ph, int(22 + 14 * ph), (200, 215, 255), a=min(1, (1 - ph) * 2))
        hook_text(cv, 'CONTACTS IN', lt + 0.4, y=-800, size=140, color=(159, 224, 255))
    return cv


def b1_oxygen(lt, dur, T):
    """Close on the open eye: oxygen bubbles drift in from the air and soak into the cornea."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#f2b48c', '#c97f62', vignette=0.3)
    eye(cv, 0, -250, 260, T, look=(0.2 * np.sin(T), 0))
    for q in range(8):
        ph = (lt * 0.5 + q / 8) % 1
        a = q * 0.8
        o2(cv, np.cos(a) * (520 - 380 * ph), -250 + np.sin(a) * (420 - 300 * ph), 1.2, a=min(1, (1 - ph) * 3))
    label(cv, 'CORNEA', 0, -560, 60, (255, 255, 255))
    arrows(cv, [((0, -520), (0, -440))], (255, 255, 255), 10)
    return cv


def b2_starve(lt, dur, T):
    """The lid closes over the lens; oxygen bubbles bounce off; the cornea goes dim."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#f2b48c', '#c97f62', vignette=0.3)
    k = ease(float(np.clip(lt / (dur * 0.35), 0, 1)))
    dim = float(np.clip((lt - dur * 0.35) / (dur * 0.5), 0, 1))
    eye(cv, 0, -250, 260, T, lid=0.55 * k, dim=dim)
    for q in range(8):
        ph = (lt * 0.7 + q / 8) % 1
        a = q * 0.8
        r = 520 - 200 * (1 - abs(ph * 2 - 1))                                   # bounce off and drift away
        o2(cv, np.cos(a) * r, -250 + np.sin(a) * r * 0.8, 1.2, a=0.9)
    meter(cv, 0, 150, 520, 1 - 0.85 * dim, ramp('#bfe6ff') if dim < 0.5 else ramp('#e2483d'), 'OXYGEN')
    if dim > 0.6:
        hook_text(cv, 'STARVING', lt, y=-790, size=160, pop_t=dur * 0.7, color=(255, 90, 80))
    return cv


def germ_(cv, x, y, r, T, seed=0, col=None):
    germ(cv, x, y, r, T, seed=seed)


def b3_germs(lt, dur, T):
    """The weak, dim cornea: germs crowd round and slip in."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#f2b48c', '#c97f62', vignette=0.3)
    eye(cv, 0, -250, 260, T, lid=0.55, dim=1.0)
    k = float(np.clip(lt / (dur * 0.8), 0, 1))
    for q in range(6):
        a = q * 1.05 + 0.3
        rr = 480 - 330 * k * (0.6 + 0.4 * (q % 2))
        germ(cv, np.cos(a) * rr, -250 + np.sin(a) * rr * 0.75, 44, T, seed=q)
    hook_text(cv, 'GERMS', lt, y=-790, size=170, pop_t=dur * 0.35, color=(127, 211, 79))
    return cv


def b4_odds(lt, dur, T):
    """Two eyes side by side: lens out = 1 germ, slept in lens = 8 germs, piling up one by one."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1c2238', '#0e1220', vignette=0.35)
    eye(cv, -250, -330, 130, T, lens=0.0)
    eye(cv, 250, -330, 130, T, lid=0.3, dim=0.6)
    label(cv, 'LENS OUT', -250, -500, 44, (180, 255, 190))
    label(cv, 'SLEPT IN IT', 250, -500, 44, (255, 160, 150))
    germ(cv, -250, -60, 34, T, seed=1)
    n = 1 + int(7 * float(np.clip(lt / (dur * 0.7), 0, 1)))
    for i in range(n):
        r_, c_ = divmod(i, 4)
        germ(cv, 130 + c_ * 80, -80 + r_ * 90, 30, T, seed=i + 3)
    if n >= 8:
        hook_text(cv, 'UP TO 8X', lt, y=-800, size=170, pop_t=dur * 0.72, color=(255, 90, 80))
    return cv


def scope(cv, k_in=1.0):
    """Microscope view: everything outside a circle goes black."""
    import cv2
    H_, W_ = cv.img.shape[:2]
    m = np.zeros((H_, W_), np.float32)
    cv2.circle(m, (W_ // 2, int(H_ * 0.40)), int(460 * k_in), 1.0, -1, lineType=cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 6)
    cv.img *= m[..., None]


def ameba(cv, x, y, r, T, a=1.0, mouth=0.0):
    """Acanthamoeba: a wobbly purple blob with spiky arms."""
    def f(X, Y):
        ang = np.arctan2(Y - y, X - x)
        return np.hypot(X - x, Y - y) - r * (1 + 0.12 * np.sin(5 * ang + T * 2) + 0.06 * np.sin(9 * ang - T * 3))
    for q in range(12):                                                        # the spikes
        ang = q * 0.52 + 0.2 * np.sin(T + q)
        p0 = (x + np.cos(ang) * r * 0.95, y + np.sin(ang) * r * 0.95)
        p1 = (x + np.cos(ang) * r * 1.35, y + np.sin(ang) * r * 1.35)
        line(cv, [p0, p1], 8, AMEBA, ow=2.5, flat=False, a=a)
    cv.shape(f, (x - r * 1.3, y - r * 1.3, x + r * 1.3, y + r * 1.3), AMEBA, alpha=a)
    disc(cv, x + r * 0.2, y - r * 0.1, r * 0.3, ramp('#7a4aa0', '#4a2a70', '#a87ad0'), ow=3, shadow=0, alpha=a)
    for sx in (-1, 1):
        ex, ey = x - r * 0.25 + sx * r * 0.18, y - r * 0.25
        disc(cv, ex, ey, r * 0.1, ramp('#ffffff'), ow=2, shadow=0, alpha=a)
        dot(cv, ex + 2, ey + 2, r * 0.05, a=a)
        line(cv, [(ex - sx * r * 0.12, ey - r * 0.16), (ex + sx * r * 0.1, ey - r * 0.1)], 5, flat(hexc('#2a1440')), a=a)   # angry brows
    if mouth > 0:
        cv.shape(ellipse(x - r * 0.25, y + r * 0.15, r * 0.2, r * 0.12 * mouth), (x - r * 0.5, y, x, y + r * 0.35), ramp('#2a1440'), ow=2, shadow=0, alpha=a)


def b5_nightmare(lt, dur, T):
    """A microscope view slowly opening on something moving in the dark."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a3a2a', '#141c14', vignette=0.0)
    k = ease(float(np.clip(lt / (dur * 0.8), 0, 1)))
    ameba(cv, 60 * np.sin(T * 0.7), -190, 150, T, a=0.25 + 0.3 * k)
    scope(cv, 0.4 + 0.6 * k)
    return cv


def b6_reveal(lt, dur, T):
    """There it is: Acanthamoeba, with little icons for where it lives: water, soil, air."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a3a2a', '#141c14', vignette=0.0)
    ameba(cv, 0, -190, 230, T, mouth=0.6 + 0.4 * np.sin(T * 3))
    scope(cv, 1.0)
    for i, (txt, x) in enumerate((('WATER', -300), ('SOIL', 0), ('AIR', 300))):
        t0 = dur * (0.45 + 0.13 * i)
        if lt > t0:
            sc = min(1, (lt - t0) / 0.15)
            if i == 0:
                drop(cv, x, 200, 34 * sc)
            elif i == 1:
                cv.shape(ellipse(x, 210, 70 * sc, 36 * sc), (x - 72, 170, x + 72, 250), ramp('#8a5a2a', '#5e3a18', '#b07a40'))
            else:
                cloud(cv, x, 200, 60 * sc)
            label(cv, txt, x, 300, int(46 * sc), (255, 255, 255))
    box(cv, 0, -790, 410, 62, DARK, r=26)
    label(cv, 'ACANTHAMOEBA', 0, -782, 80, (200, 160, 232))
    return cv


def b7_damage(lt, dur, T):
    """It burrows into the cornea: the eye goes red, pain bolts, then the iris clouds over."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#f2b48c', '#c97f62', vignette=0.35)
    k = float(np.clip(lt / (dur * 0.8), 0, 1))
    eye(cv, 0, -250, 260, T, red=min(1, k * 2), cloudy=max(0, (k - 0.5) * 2), lens=0.4)
    ameba(cv, 60 + 20 * np.sin(T * 3), -250 + 10 * np.cos(T * 4), 60, T, a=1 - 0.5 * k, mouth=1.0)
    if k > 0.2:
        for q in range(4):
            a = q * np.pi / 2 + 0.7
            p0 = (np.cos(a) * 420, -250 + np.sin(a) * 300)
            pts = jagged(p0, (p0[0] * 1.25, -250 + (p0[1] + 250) * 1.25), int(T * 12) + q, depth=3, rough=0.5)
            line(cv, pts, 10, flat(hexc('#ffe14d')), a=0.5 + 0.5 * np.sin(T * 20 + q))
    if k > 0.6:
        hook_text(cv, 'BLINDNESS', lt, y=-790, size=150, pop_t=dur * 0.6, color=(255, 90, 80))
    return cv


def b8_out(lt, dur, T):
    """Bathroom mirror: he pops the lenses out into the case before bed. Green check."""
    cv = Canvas(0, -150, 1.2)
    cv.background('#d8e8ec', '#b0c8d0', vignette=0.25)
    box(cv, 0, -300, 330, 420, ramp('#cfe6f0', '#9fc0d0', '#eaf6ff'), r=20)   # mirror
    k = float(np.clip(lt / (dur * 0.7), 0, 1))
    right = reach_move(1, min(1, k * 1.6), (40, -770))
    guy(cv, 0, 700, 1.15, face='calm', arms=((12, 0), right))
    front_arm(cv, 0, 700, 1.15, 1, *right)
    box(cv, 0, 360, 380, 40, ramp('#f4f6f8', '#c8d0d8', '#ffffff'), r=10)      # sink counter
    for sx in (-1, 1):                                                         # the lens case
        disc(cv, 220 + sx * 34, 320, 28, ramp('#3fbf6a', '#25804a', '#7fe8a0'))
    if k > 0.7:
        disc(cv, 220, 160, 50, ramp('#3fbf6a', '#25804a', '#7fe8a0'))
        line(cv, [(195, 160), (215, 182), (250, 135)], 12, flat(hexc('#ffffff')))
        hook_text(cv, 'TAKE THEM OUT', lt, y=-800, size=120, pop_t=dur * 0.7, color=(127, 255, 160))
    return cv


BEATS = [b0_hook, b1_oxygen, b2_starve, b3_germs, b4_odds, b5_nightmare, b6_reveal, b7_damage, b8_out]

if __name__ == '__main__':
    run(BEATS)
