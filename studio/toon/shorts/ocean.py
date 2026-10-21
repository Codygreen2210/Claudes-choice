#!/usr/bin/env python3
"""What really happens when you drink the ocean. Opens on a man knee-deep in the sea, already sucking it up a bendy straw; loops back into it."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403
from jump import guy_r, SHIRTS

SEA = ramp('#2f86d8', '#1a5a9e', '#7cc4ff')
SEA_FRONT = ramp('#3a95e6', '#2168b0', '#8fd0ff')
LAND = ramp('#5fbf4a', '#3d8a30', '#9ee07a')
KID = ramp('#b8404e', '#7a2030', '#e47a88')
SALTC = ramp('#ffffff', '#cfd8e2', '#ffffff')
PEE = ramp('#ffe066', '#d0a820', '#fff2a8')
WHITE_FLAT = flat(hexc('#ffffff'))
STRIPE = flat(hexc('#e8343a'))
WAT = flat(hexc('#3fa9f0'))
BLUEM = ramp('#7fd2ff', '#3fa9e0', '#bfeaff')
REDM = ramp('#e2483d', '#a82a22', '#ff8a7a')


def mixhex(a, b, t):
    ca, cb = [np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) for h in (a, b)]
    c = ca + (cb - ca) * t
    return '#%02x%02x%02x' % tuple(int(v) for v in c)


def sea(cv, T, y0=60, amp=16, ramp_=SEA, foam=True, x0=None, x1=None):
    x0 = cv.cx - 640 / cv.zoom if x0 is None else x0
    x1 = cv.cx + 640 / cv.zoom if x1 is None else x1
    f, bb = wave_surface(y0, amp, 0.011, T * 2.0, x0=x0, x1=x1, y1=cv.cy + 1060 / cv.zoom)
    cv.shape(f, bb, ramp_, ow=4, shadow=0)
    if foam:
        xs = np.linspace(x0, x1, 40)
        ys = y0 + amp * np.sin(xs * 0.011 + T * 2.0) + amp * 0.4 * np.sin(xs * 0.011 * 2.3 - T * 2.0 * 1.7)
        line(cv, list(zip(xs, ys + 4)), 9, WHITE_FLAT, a=0.75)


def salt(cv, x, y, s=1.0, a=1.0):
    cv.shape(rbox(x, y, 20 * s, 20 * s, 5 * s), (x - 24 * s, y - 24 * s, x + 24 * s, y + 24 * s), SALTC, ow=3, alpha=a)


def straw(cv, mouth, tip, T, flow=1.0, w=40):
    """A real bendy straw: short end in his lips, accordion bend, long run down into the water.
    Clear plastic with red spiral stripes, and you can see the sea water racing up the middle."""
    mx, my = mouth
    bx, by = mx + w * 2.2, my - w * 1.2                                     # the bend
    d = np.array([tip[0] - bx, tip[1] - by], float); L = np.hypot(*d); u = d / L; nrm = np.array([-u[1], u[0]])
    d2 = np.array([bx - mx, by - my], float); u2 = d2 / np.hypot(*d2); n2 = np.array([-u2[1], u2[0]])
    short = [(mx, my), (bx, by)]
    long_ = [(bx, by), tuple(tip)]
    body = ramp('#f7fcff', '#bcd2e2', '#ffffff')
    line(cv, long_, w, body, ow=4, flat=False)
    line(cv, short, w, body, ow=4, flat=False)
    line(cv, long_, w * 0.42, WAT, a=0.75 * flow); line(cv, short, w * 0.42, WAT, a=0.75 * flow)   # sea water inside
    for seg, uu, nn in ((long_, u, nrm), (short, u2, n2)):                  # spiral stripes
        a0 = np.array(seg[0]); ln = np.hypot(*(np.array(seg[1]) - a0))
        for t in np.arange(w * 0.9, ln - w * 0.4, w * 0.95):
            c = a0 + uu * t
            line(cv, [tuple(c - nn * w * 0.42 - uu * w * 0.18), tuple(c + nn * w * 0.42 + uu * w * 0.18)], w * 0.2, STRIPE, a=0.95)
    for k in range(5):                                                      # accordion ridges at the bend
        p = np.array([bx, by]) + (u - u2) * 0.0 + u * (k * w * 0.2 - w * 0.4)
        line(cv, [tuple(p - nrm * w * 0.5), tuple(p + nrm * w * 0.5)], w * 0.1, flat(hexc('#8fa6b8')), a=0.95)
    for q in range(7):                                                      # slugs of water shooting up
        ph = (T * 2.4 * flow + q / 7) % 1
        p = np.array(tip) + (np.array(long_[0]) - np.array(tip)) * ph
        disc(cv, p[0], p[1], w * 0.16, ramp('#d8f2ff'), ow=0, shadow=0, alpha=0.95 * flow)


def lips(cv, x, y, s):
    cv.shape(subtract(rotell(x, y, 30 * s, 24 * s, 0), circle(x, y, 13 * s)), (x - 34 * s, y - 28 * s, x + 34 * s, y + 28 * s),
             ramp('#e0707a', '#b04a56', '#ff9aa4'), ow=3, shadow=0)


def suck_rings(cv, tip, T, big=1.0):
    for k in range(3):                                                      # water being pulled in at the tip
        ph = (T * 1.4 + k / 3) % 1
        rr = ((1 - ph) * 110 + 20) * big
        cv.shape(subtract(rotell(tip[0], tip[1] + 6, rr, rr * 0.28, 0), rotell(tip[0], tip[1] + 6, rr - 8, rr * 0.28 - 6, 0)),
                 (tip[0] - 150, tip[1] - 50, tip[0] + 150, tip[1] + 60), WHITE_FLAT, ow=0, shadow=0, flat=True, alpha=0.85 * ph)


def beach_shot(cv, T, face='puff', flow=1.0, sweat=0.0, sky=('#5fb4f0', '#d8f0ff'), show_sun=True, hair=None, bald=False, glasses=False):
    """Close on him, waist deep, straw in his lips, the sea and a clear horizon behind."""
    cv.background(sky[0], sky[1], vignette=0.2)
    if show_sun:
        sun(cv, 390, -440, 70, T)
    far = ramp('#2a78c8', '#185896', '#5aa6ea')
    f, bb = wave_surface(-110, 3, 0.02, T * 0.6, x0=-700, x1=700, y1=1100)
    cv.shape(f, bb, far, ow=3, shadow=0)
    for k in range(6):                                                      # sun glint on the water
        yy = -88 + k * 30; ww = 22 + k * 10
        line(cv, [(390 - ww + 10 * np.sin(T * 2 + k), yy), (390 + ww + 10 * np.sin(T * 2 + k), yy)], 5, WHITE_FLAT, a=0.45 - k * 0.06)
    cv.shape(poly([(-470, -150), (-430, -150), (-430, -230)]), (-480, -240, -420, -140), ramp('#ffffff'), ow=3, shadow=0)   # far-off sailboat
    box(cv, -440, -132, 46, 10, ramp('#c05a3a'), r=6, ow=3, shadow=0)
    s = 1.55; gx, gy = -170, 921
    bob = 6 * np.sin(T * 2.0)
    guy(cv, gx, gy + bob, s, face=face, arms=((20, 10), (-5.6, 105)), hair=hair or HAIR, bald=bald, glasses=glasses)   # right hand lands on the straw
    mouth = (gx, gy + bob - 708 * s + 6)
    tip = (320, 372)
    straw(cv, mouth, tip, T, flow)
    lips(cv, mouth[0], mouth[1], s * 0.8)
    disc(cv, 179, 184 + bob, 50, SKIN, ow=3.5)                                # his hand wrapped round the straw
    for f in range(3):
        line(cv, [(150, 160 + bob + f * 22), (205, 168 + bob + f * 22)], 4, flat(hexc('#c98a6e')), a=0.8)
    sea(cv, T + 0.7, y0=300, amp=12, ramp_=SEA_FRONT, foam=True)
    suck_rings(cv, tip, T)
    for q in range(int(3 * sweat)):
        ph = (T * 1.2 + q / 3) % 1
        drop(cv, gx - 120 + q * 110, mouth[1] - 140 + 120 * ph, 15, a=1 - ph)
    return mouth


def kidney(cv, x, y, s, side):
    """Bean-shaped kidney, dent facing the middle, with the tube that carries pee down."""
    f = subtract(rotell(x, y, 105 * s, 165 * s, 0), circle(x - side * 118 * s, y, 58 * s))
    cv.shape(f, (x - 130 * s, y - 185 * s, x + 130 * s, y + 185 * s), KID)
    line(cv, [(x - side * 70 * s, y + 20 * s), (x - side * 150 * s, y + 160 * s), (x - side * 170 * s, y + 330 * s)], 14 * s, PEE, ow=3, flat=False)


def glass(cv, x, y, fill, col, label_txt):
    box(cv, x, y, 120, 200, ramp('#e6f6ff', '#a8d4ee', '#ffffff'), r=26, alpha=0.5)
    if fill > 0:
        h = 180 * min(fill, 1.0)
        box(cv, x, y + 180 - h, 104, h, col, r=20, ow=0, shadow=0, alpha=0.95)
    label(cv, label_txt, x, y - 260, 70, WHT)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """He's already slurping the sea on frame one; before 0 it's the same slurp (the loop)."""
    cv = Canvas(0, 0, 1.0)
    beach_shot(cv, T)
    if lt >= 0:
        hook_text(cv, 'GULP', lt, y=-780, size=190, color=(127, 210, 255))
    return cv


def b1_blood(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a1a26', '#2a0a12', vignette=0.35)
    vessel(cv, 60, x0=-800, x1=800, r=230)
    for q in range(9):                                                      # red blood cells flowing
        x = -700 + ((T * 260 + q * 170) % 1400)
        cv.shape(rotell(x, 60 + 70 * np.sin(q * 2.1), 50, 30, 0.3), (x - 60, -20, x + 60, 140), ramp('#d8343a', '#9a1f24', '#ff7070'), ow=3)
    n = int(1 + 14 * ease(np.clip(lt / (dur * 0.7), 0, 1)))
    for q in range(n):                                                      # salt pouring in
        ph = min(1.0, (lt - q * 0.12) / 0.5) if lt > q * 0.12 else 0
        x = -300 + (q % 7) * 100; y = -400 + 400 * ease(ph) + 40 * (q // 7)
        salt(cv, x, y, 1.1)
    badge(cv, 'SALT', y=-560, col=WHT, w=260)
    return cv


def plump_cell(cv, x, y, r, k, T, seed=0):
    """A body cell: juicy and round at k=0, a dark wrinkled raisin at k=1."""
    wob = 1 + 0.025 * np.sin(T * 3 + seed)
    rr = r * (1 - 0.32 * k) * wob
    wr = 0.055 * k

    def f(X, Y):
        a = np.arctan2(Y - y, X - x)
        return np.sqrt((X - x) ** 2 + (Y - y) ** 2) - rr * (1 + wr * np.sin(7 * a + seed) + wr * 0.6 * np.sin(11 * a + 2 * seed))
    c0 = np.array([255, 150, 185]); c1 = np.array([120, 45, 75])
    c = c0 + (c1 - c0) * k
    col = ramp('#%02x%02x%02x' % tuple(c.astype(int)), '#%02x%02x%02x' % tuple((c * 0.6).astype(int)), '#%02x%02x%02x' % tuple(np.minimum(c * 1.25, 255).astype(int)))
    cv.shape(f, (x - rr * 1.3, y - rr * 1.3, x + rr * 1.3, y + rr * 1.3), col, ow=4)
    disc(cv, x + rr * 0.15, y + rr * 0.1, rr * 0.28, ramp('#7a2a50', '#4a1430', '#a84a78'), ow=3, shadow=0)   # nucleus
    if k > 0.35:                                                            # deep raisin creases
        for w in range(3):
            a0 = w * 2.1 + seed
            line(cv, [(x + np.cos(a0) * rr * 0.2, y + np.sin(a0) * rr * 0.2), (x + np.cos(a0 + 0.4) * rr * 0.75, y + np.sin(a0 + 0.4) * rr * 0.75)],
                 6, flat(hexc('#3a0e22')), a=min(1, (k - 0.35) * 2.5))


def b2_cells(lt, dur, T):
    k = ease(np.clip((lt - 0.5) / (dur * 0.65), 0, 1))
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a1a26', '#2a0a12', vignette=0.35)
    for j, (cx, cy) in enumerate(((-230, -160), (230, -160), (0, 200))):
        for q in range(5):                                                  # water squeezed out of each cell
            ph = (lt * 0.8 + q / 5 + j * 0.13) % 1
            a = q * 1.26 + j
            dist = 150 * (1 - 0.42 * k) + 30 + 170 * ph
            drop(cv, cx + np.cos(a) * dist, cy + np.sin(a) * dist, 17, a=(1 - ph) * float(lt > 0.4))
        plump_cell(cv, cx, cy, 165, k, T, seed=j)
    for q in range(8):                                                      # the salt doing it
        salt(cv, -350 + q * 100, 480 + 20 * np.sin(q + T), 0.75)
    label(cv, 'YOUR CELLS', 0, -440, 64, (255, 190, 210))
    hook_text(cv, 'RAISINS', lt, y=-720, size=150, pop_t=dur * 0.55, color=(255, 160, 190))
    return cv


def b3_kidneys(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    kidney(cv, -220, 80, 1.15, -1)
    kidney(cv, 220, 80, 1.15, 1)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    meter(cv, 0, -600, 520, k, BLUEM, 'OCEAN SALT')
    meter(cv, 0, -430, 520, min(k, 0.57), PEE if k < 0.57 else REDM, 'KIDNEY MAX')
    for q in range(6):
        ph = (lt * 1.2 + q / 6) % 1
        salt(cv, -220 + 440 * (q % 2), -260 + 300 * ph, 0.7, a=1 - ph)
    if k > 0.6:
        label(cv, "CAN'T KEEP UP", 0, -280, 64, RED)
    return cv


def b4_glasses(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    glass(cv, -230, -40, 1 - k, ramp('#7fd0ff', '#3fa9e0', '#bfeaff'), 'IN')
    glass(cv, 230, -40, 1.25 * k, PEE, 'OUT')
    line(cv, [(80, -40), (380, -40)], 6, flat(hexc('#ffffff')), a=0.9)
    arrows(cv, [((-80, -40), (80, -40))], YEL, 16)
    if k > 0.8:
        label(cv, 'MORE OUT THAN IN', 0, -480, 64, YEL)
    return cv


def b5_thirsty(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.85), 0, 1))
    cv = Canvas(0, 0, 1.0)
    beach_shot(cv, T, face='puff' if k < 0.6 else 'worried', flow=1.0 - 0.6 * k, sweat=1.0, show_sun=False)
    meter(cv, 300, -190, 280, 1 - 0.92 * k, BLUEM if k < 0.6 else REDM, 'WATER')
    bx, by = 300, -460                                                      # his shrinking brain
    cloud(cv, bx, by, 120)
    brain(cv, bx, by, 0.45 * (1 - 0.45 * k))
    if k > 0.6:
        vignette_red(cv, 0.35 * (k - 0.6) / 0.4)
    badge(cv, 'THIRSTIER', y=-640, col=RED, w=380)
    return cv


def b6_world(lt, dur, T):
    z = 1.25 - 0.25 * ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, -40, z)
    cv.background('#0b1430', '#1b2350', vignette=0.3)
    x, y, r = 0, 60, 300
    disc(cv, x, y, r, SEA, bevel=r * 0.5)
    for a, rr, d in ((0.3, 0.42, 0.45), (2.2, 0.35, 0.5), (4.0, 0.3, 0.4), (5.2, 0.22, 0.6)):
        cv.shape(circle(x + np.cos(a) * r * d, y + np.sin(a) * r * d, r * rr), (x - r, y - r, x + r, y + r), LAND, ow=3, shadow=0, flat=True,
                 mask=lambda X, Y: np.sqrt((X - x) ** 2 + (Y - y) ** 2) - r)
    for i in range(26):                                                     # people all around the planet
        a = -np.pi + i * 2 * np.pi / 26
        if np.sin(a) > 0.45:
            continue
        px, py = x + np.cos(a) * (r + 6), y + np.sin(a) * (r + 6)
        guy_r(cv, px, py, 0.16, np.degrees(a) + 90, SHIRTS[i % 6], 0.0)
    badge(cv, f'{int(8_000_000_000 * ease(np.clip(lt / (dur * 0.5), 0, 1))):,}', y=-600, col=(127, 210, 255), w=520)
    label(cv, 'HELPERS', 0, -480, 64, WHT)
    return cv


def b7_years(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.75), 0, 1))
    ph = 0.5 + 0.5 * np.sin(lt * 7)                                         # day-night time-lapse
    q = round(ph * 6) / 6
    cv = Canvas(0, 0, 1.0)
    hair = ramp(mixhex('#5a3a22', '#e8e8e8', min(1, k * 1.6)), mixhex('#3a2412', '#b8b8b8', min(1, k * 1.6)), mixhex('#7a5232', '#ffffff', min(1, k * 1.6)))
    beach_shot(cv, T, flow=1.0, sky=(mixhex('#5fb4f0', '#0b1430', q), mixhex('#d8f0ff', '#2a3570', q)), show_sun=False,
               hair=hair, bald=k > 0.8, glasses=k > 0.45)
    for w in range(5):                                                      # cobweb growing in the corner
        a = w * 0.35
        line(cv, [(540, -900), (540 - np.cos(a) * 260 * k, -900 + np.sin(a) * 260 * k)], 3, WHITE_FLAT, a=0.7 * k)
    badge(cv, f'{int(200_000_000 * k):,} YEARS', y=-560, col=YEL, w=600)
    if k > 0.95:
        hook_text(cv, '200 MILLION YEARS', lt, y=-760, size=92, pop_t=dur * 0.78, color=YEL)
    return cv


def b8_back(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    sea(cv, T, y0=240)
    box(cv, -420, 160, 300, 150, ramp('#f2d79a', '#c9a866', '#fff0c8'), r=60)   # beach
    toilet(cv, -300, -40, 0.62, swirl=lt, T=T, handle=min(1, lt * 2))
    pipe = [(-300, 30), (-300, 140), (-60, 140), (80, 270)]
    line(cv, pipe, 36, STEEL, ow=4, flat=False)
    for q in range(6):
        u = (lt * 0.9 + q / 6) % 1
        seg = u * 3; i = min(int(seg), 2); f = seg - i
        disc(cv, pipe[i][0] + (pipe[i + 1][0] - pipe[i][0]) * f, pipe[i][1] + (pipe[i + 1][1] - pipe[i][1]) * f, 13, PEE, ow=2)
    arrows(cv, [((300, 180), (300, -160))], WHT, 14)
    cloud(cv, 120, -330, 110)
    for q in range(4):                                                      # rain falling back down
        ph = (lt * 1.3 + q / 4) % 1
        drop(cv, -60 + q * 60, -240 + 260 * ph, 12, a=1 - ph)
    label(cv, 'RIGHT BACK', 0, -600, 90, (127, 210, 255))
    return cv


# where the camera dives into, for the cut INTO each beat (screen px): his mouth -> his blood -> a cell
DIVE = {1: (370, 790), 2: (540, 1020), 3: (540, 1000), 6: (370, 790)}

BEATS = [b0_hook, b1_blood, b2_cells, b3_kidneys, b4_glasses, b5_thirsty, b6_world, b7_years, b8_back]

if __name__ == '__main__':
    run(BEATS)
