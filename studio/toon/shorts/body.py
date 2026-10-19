"""Shared pieces for the body Shorts (hiccups, yawning, diarrhea, gum, dreams): gut tube, stomach,
throat, x-ray chest, germs, toilet, bed, dream bubble, dog, yawning guy. Camera moves are on."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403
import kit
kit.MOVES = True

GUTC = ramp('#f08aa0', '#c45a72', '#ffc0cc')
GUTIN = ramp('#c45a72', '#9a3a52', '#e07890')
POOP = ramp('#8a5a2a', '#5e3a18', '#b07a40')
SLOP = ramp('#a8763a', '#7a5226', '#d0a060')
ACID = ramp('#9be15d', '#5fa83a', '#d4ff9a')
LUNG = ramp('#f59aa8', '#c96478', '#ffc8d0')
MUSC = ramp('#e2685a', '#a83a32', '#ff9a88')
GERM = ramp('#7fd34f', '#4f9a2a', '#b6f08a')
GUMC = ramp('#ff7fbf', '#d04a90', '#ffc0e0')
XRAYC = ramp('#5f86b8', '#2f4f78', '#a8c8f0')
PORC = ramp('#f4f6f8', '#c8d0d8', '#ffffff')
WATERC = ramp('#7fd0ff', '#3fa9e0', '#bfeaff')
BONEW = flat(hexc('#e8f4ff'))
RED = (255, 90, 80)
YEL = (255, 236, 80)
WHT = (255, 255, 255)


def badge(cv, txt, y=-560, col=YEL, w=None, x=0):
    w = w or 40 + 34 * len(txt)
    box(cv, x, y, w / 2, 62, DARK, r=26)
    label(cv, txt, x, y + 10, 86, col)


# ------------------------------------------------------------------ gut
def tube(cv, y, x0=-1000, x1=1000, r=190, rings=(), ring_k=1.0):
    """Gut tube cut open lengthwise. rings: x positions where the muscle squeezes in."""
    box(cv, (x0 + x1) / 2, y, (x1 - x0) / 2, r, GUTC, r=r * 0.9)
    box(cv, (x0 + x1) / 2, y, (x1 - x0) / 2, r * 0.7, GUTIN, r=r * 0.65, ow=0, shadow=0)
    for x in rings:
        for sy in (-1, 1):
            cv.shape(rotell(x, y + sy * r * 0.72, 70, r * 0.42 * ring_k + 2, 0), (x - 80, y - r, x + 80, y + r), GUTC, ow=3)


def lump(cv, x, y, r, col=None, squish=0.0, ow=4):
    col = POOP if col is None else col
    cv.shape(rotell(x, y, r * (1 + 0.3 * squish), r * (1 - 0.25 * squish), 0), (x - r * 1.4, y - r * 1.4, x + r * 1.4, y + r * 1.4), col, ow=ow)


def drop(cv, x, y, r, a=1.0):
    f = smooth(r * 0.5, circle(x, y, r), capsule(x, y - r * 0.3, x, y - r * 1.9, r * 0.2, r * 0.05))
    cv.shape(f, (x - r * 1.3, y - r * 2.2, x + r * 1.3, y + r * 1.3), WATERC, ow=3, alpha=a)


def germ(cv, x, y, r, T, seed=0, angry=True):
    rng = np.random.default_rng(seed)
    for k in range(9):
        a = k * 2 * np.pi / 9 + 0.3 * np.sin(T * 3 + seed)
        line(cv, [(x + np.cos(a) * r * 0.8, y + np.sin(a) * r * 0.8), (x + np.cos(a) * r * 1.35, y + np.sin(a) * r * 1.35)],
             r * 0.13, GERM, ow=3, flat=False)
        disc(cv, x + np.cos(a) * r * 1.4, y + np.sin(a) * r * 1.4, r * 0.13, GERM, ow=2.5)
    wob = 1 + 0.05 * np.sin(T * 5 + rng.uniform(0, 6))
    cv.shape(rotell(x, y, r * wob, r / wob, 0), (x - r * 1.2, y - r * 1.2, x + r * 1.2, y + r * 1.2), GERM, ow=4)
    for sx in (-1, 1):
        disc(cv, x + sx * r * 0.32, y - r * 0.08, r * 0.2, ramp('#ffffff'), ow=3, shadow=0)
        dot(cv, x + sx * r * 0.28, y - r * 0.04, r * 0.09)
        if angry:
            line(cv, [(x + sx * r * 0.55, y - r * 0.42), (x + sx * r * 0.12, y - r * 0.26)], r * 0.08, INKC)
    line(cv, [(x - r * 0.25, y + r * 0.38), (x, y + r * 0.3), (x + r * 0.25, y + r * 0.38)], r * 0.07, INKC)


def stomach(cv, x, y, s, T, acid=0.45, acid_on=True):
    """J-shaped stomach, cut open, with acid sloshing at the bottom. Returns the inside sdf."""
    out = smooth(60 * s, circle(x - 60 * s, y - 40 * s, 230 * s), circle(x + 120 * s, y + 120 * s, 200 * s),
                 capsule(x - 160 * s, y - 330 * s, x - 120 * s, y - 120 * s, 70 * s))
    inn = smooth(50 * s, circle(x - 60 * s, y - 40 * s, 190 * s), circle(x + 120 * s, y + 120 * s, 160 * s),
                 capsule(x - 160 * s, y - 360 * s, x - 120 * s, y - 120 * s, 40 * s))
    bb = (x - 330 * s, y - 420 * s, x + 360 * s, y + 360 * s)
    cv.shape(out, bb, GUTC)
    cv.shape(inn, bb, GUTIN, ow=0, shadow=0)
    if acid_on and acid > 0:
        lvl = y + 300 * s - acid * 500 * s
        surf = lambda X, Y: (lvl + 12 * s * np.sin(X / (40 * s) + T * 3)) - Y
        cv.shape(inter(inn, surf), bb, ACID, ow=0, shadow=0, alpha=0.85)
        for k in range(7):
            ph = (T * 0.8 + k / 7) % 1
            bx = x - 120 * s + k * 50 * s
            by = y + 260 * s - ph * (300 * s - (300 * s - (y + 300 * s - lvl)))
            disc(cv, bx, y + 250 * s - ph * (y + 250 * s - lvl), 10 * s * (0.6 + ph), ramp('#eaffd0'), ow=2, alpha=1 - ph)
    return inn


def toilet(cv, x, y, s=1.0, swirl=0.0, T=0.0, handle=0.0):
    box(cv, x, y - 380 * s, 230 * s, 150 * s, PORC, r=40 * s)                       # tank
    line(cv, [(x - 200 * s, y - 330 * s), (x - 270 * s, y - 330 * s + 40 * s * handle)], 20 * s, STEEL, ow=3, flat=False)
    cv.shape(capsule(x, y - 120 * s, x, y + 60 * s, 170 * s, 120 * s), (x - 200 * s, y - 300 * s, x + 200 * s, y + 200 * s), PORC)
    cv.shape(rotell(x, y - 200 * s, 290 * s, 90 * s, 0), (x - 300 * s, y - 300 * s, x + 300 * s, y - 100 * s), PORC)
    cv.shape(rotell(x, y - 200 * s, 230 * s, 60 * s, 0), (x - 240 * s, y - 270 * s, x + 240 * s, y - 130 * s), WATERC, ow=3, shadow=0)
    if swirl > 0:
        for k in range(10):
            a = T * 9 + k * 0.63
            rr = 200 * s * (1 - (k / 10) * 0.8)
            disc(cv, x + np.cos(a) * rr, y - 200 * s + np.sin(a) * rr * 0.26, 10 * s, ramp('#ffffff'), ow=0, alpha=swirl * 0.8, shadow=0)


# ------------------------------------------------------------------ chest and throat
def chest(cv, x, y, s, T, dia=0.0, lung=0.5, twitch=0.0, xr=True):
    """X-ray chest: ribs, lungs and the diaphragm dome under them. dia 0 = up/relaxed, 1 = yanked down."""
    if xr:
        torso = smooth(80 * s, capsule(x - 330 * s, y - 380 * s, x + 330 * s, y - 380 * s, 120 * s),
                       rbox(x, y + 200 * s, 360 * s, 560 * s, 200 * s), capsule(x, y - 560 * s, x, y - 420 * s, 90 * s))
        cv.shape(torso, (x - 480 * s, y - 680 * s, x + 480 * s, y + 800 * s), ramp('#a8c8f0', '#6a8fb8', '#d8ecff'), ow=4, alpha=0.35)
    lw = 0.85 + 0.25 * lung
    for sx in (-1, 1):
        cv.shape(rotell(x + sx * 140 * s, y - 60 * s + 30 * s * dia, 125 * s * lw, (230 + 50 * dia) * s, sx * 6),
                 (x + sx * 140 * s - 190 * s, y - 380 * s, x + sx * 140 * s + 190 * s, y + 300 * s), LUNG, ow=3, alpha=0.9)
    line(cv, [(x, y - 420 * s), (x, y - 330 * s)], 46 * s, ramp('#f4c0c8'), ow=3, flat=False)          # windpipe
    for sx in (-1, 1):
        line(cv, [(x, y - 330 * s), (x + sx * 110 * s, y - 230 * s)], 26 * s, ramp('#f4c0c8'), ow=3, flat=False)
    for i in range(6):                                                                                    # ribs
        y0 = y - (260 - i * 70) * s
        for sx in (-1, 1):
            pts = [(x + sx * (14 + 300 * u) * s, y0 + (40 * np.sin(u * 2.6) + 60 * u * u) * s) for u in np.linspace(0, 1, 9)]
            line(cv, pts, 11 * s, BONEW, a=0.85)
    line(cv, [(x, y - 330 * s), (x, y + 260 * s)], 18 * s, BONEW, a=0.85)
    h = (150 - 120 * dia) * s
    jit = twitch * 14 * s * np.sin(T * 60)
    base = y + (230 + 60 * dia) * s
    pts = [(x + u * 330 * s, base - h * (1 - u * u) + jit * (1 - u * u)) for u in np.linspace(-1, 1, 21)]
    line(cv, pts, 40 * s, MUSC, ow=4, flat=False)
    if twitch > 0:
        cv.glow(circle(x, base - h, 60 * s), (x - 300 * s, base - h - 200 * s, x + 300 * s, base - h + 200 * s), '#ff4a3a', 50 * s, 0.6 * twitch)
    return base - h


def throat(cv, x, y, s, shut=0.0):
    """Side view of the windpipe with the flap (the vocal cords) at the top. shut 0 open, 1 slammed shut."""
    box(cv, x, y + 300 * s, 120 * s, 520 * s, ramp('#f4b0b8', '#c97a86', '#ffd4da'), r=110 * s)
    box(cv, x, y + 300 * s, 80 * s, 520 * s, ramp('#7a2a3a', '#4e1a26', '#9a4050'), r=70 * s, ow=0, shadow=0)
    for k in range(8):
        box(cv, x, y - 100 * s + k * 120 * s, 104 * s, 14 * s, ramp('#ffd4da'), r=8 * s, ow=2, shadow=0, alpha=0.8)
    for sx in (-1, 1):                                   # flaps hinge on the walls: up along the wall when open, flat across when shut
        a = np.radians(90 * (1 - shut))
        px, py = x + sx * 80 * s, y - 220 * s
        tx, ty = px - sx * np.cos(a) * 92 * s, py - np.sin(a) * 92 * s
        line(cv, [(px, py), (tx, ty)], 30 * s, MUSC, ow=3, flat=False)


# ------------------------------------------------------------------ people, beds, dreams, dogs
def yawn_guy(cv, x, y, s, k, stretch=True, **kw):
    """guy() with a yawn: eyes squeeze, the mouth opens into a big oval, arms reach up."""
    arms = ((20 + 140 * k, 30 * k), (20 + 140 * k, 30 * k)) if stretch else kw.pop('arms', ((15, 0), (15, 0)))
    guy(cv, x, y, s, face='closed' if k > 0.35 else 'calm', arms=arms, **kw)
    if k > 0.05:
        mx, my = x, y - 702 * s
        rx, ry = (18 + 16 * k) * s, (8 + 52 * k) * s
        cv.shape(ellipse(mx, my, rx, ry), (mx - rx - 4, my - ry - 4, mx + rx + 4, my + ry + 4), ramp('#5a1f2a'), ow=3.5, shadow=0, rim=0)
        if k > 0.4:
            cv.shape(ellipse(mx, my + ry * 0.45, rx * 0.6, ry * 0.3), (mx - rx, my, mx + rx, my + ry), ramp('#e8707a'), ow=0, shadow=0)


def bed(cv, T, x=0, y=300, s=1.0, face='closed', blanket=True, lock=0.0):
    """Top-down: a guy asleep under a blanket, head on a pillow."""
    box(cv, x, y + 250 * s, 430 * s, 760 * s, ramp('#a8693a', '#6e4122', '#d08f58'), r=40 * s)      # frame
    box(cv, x, y + 260 * s, 400 * s, 730 * s, ramp('#f4f1ea'), r=30 * s)                              # sheet
    box(cv, x, y - 380 * s, 300 * s, 110 * s, ramp('#ffffff', '#d8dde4', '#ffffff'), r=80 * s)       # pillow
    br = 1 + 0.02 * np.sin(T * 1.6)
    guy(cv, x, y + 520 * s, s * br, face=face, legs=False, ground=False, arms=((12, 0), (12, 0)))
    if blanket:
        box(cv, x, y + 520 * s, 390 * s, 480 * s, ramp('#4f7fd8', '#2f559a', '#8fb4ff'), r=60 * s)
        for k in range(4):
            line(cv, [(x - 360 * s, y + (150 + k * 220) * s), (x + 360 * s, y + (170 + k * 220) * s)], 6 * s, flat(hexc('#2f559a')), a=0.5)
    if lock > 0:
        for sx in (-1, 1):
            line(cv, [(x - 420 * s, y + (330 + sx * 180) * s), (x + 420 * s, y + (330 + sx * 180) * s)], 26 * s, STEEL, ow=4, flat=False, a=lock)
        box(cv, x, y + 330 * s, 90 * s, 80 * s, YELLOW, r=16 * s, alpha=lock)
        cv.shape(subtract(capsule(x, y + 250 * s, x, y + 250 * s, 64 * s), capsule(x, y + 250 * s, x, y + 250 * s, 40 * s)),
                 (x - 70 * s, y + 180 * s, x + 70 * s, y + 320 * s), STEEL, ow=3, alpha=lock)
        dot(cv, x, y + 330 * s, 16 * s)


def cloud(cv, x, y, r, a=1.0, col=None):
    col = ramp('#ffffff', '#d8e4f4', '#ffffff') if col is None else col
    f = smooth(r * 0.25, circle(x - r * 0.55, y + r * 0.1, r * 0.55), circle(x, y - r * 0.2, r * 0.65),
               circle(x + r * 0.55, y + r * 0.1, r * 0.55), circle(x, y + r * 0.3, r * 0.5))
    cv.shape(f, (x - r * 1.2, y - r * 0.95, x + r * 1.2, y + r * 0.9), col, alpha=a)


def dream_bubble(cv, hx, hy, x, y, r, k):
    """Bubble growing out of a head at (hx, hy) toward (x, y)."""
    if k <= 0:
        return
    for j, u in enumerate((0.25, 0.5)):
        cloud(cv, hx + (x - hx) * u, hy + (y - hy) * u, r * (0.12 + 0.1 * j) * min(1, k * 2), a=min(1, k * 3))
    cloud(cv, x, y, r * ease(np.clip(k, 0, 1)), a=1.0)


def dog(cv, x, y, s, yawn=0.0, T=0.0):
    FUR = ramp('#d8a060', '#a8703a', '#f4c890')
    cv.shape(capsule(x - 160 * s, y - 160 * s, x + 120 * s, y - 160 * s, 90 * s), (x - 270 * s, y - 270 * s, x + 230 * s, y - 50 * s), FUR)
    for dx in (-140, -70, 60, 120):
        line(cv, [(x + dx * s, y - 120 * s), (x + dx * s, y)], 30 * s, FUR, ow=3, flat=False)
    line(cv, [(x - 240 * s, y - 180 * s), (x - 330 * s, y - 260 * s + 20 * s * np.sin(T * 8))], 22 * s, FUR, ow=3, flat=False)
    hx, hy = x + 190 * s, y - 300 * s
    disc(cv, hx, hy, 105 * s, FUR)
    cv.shape(rotell(hx + 90 * s, hy + 40 * s, 80 * s, 55 * s, 10), (hx, hy - 30 * s, hx + 190 * s, hy + 110 * s), FUR)
    disc(cv, hx + 160 * s, hy + 20 * s, 20 * s, DARK)
    for sx in (-1, 1):
        cv.shape(rotell(hx - 40 * s + sx * 50 * s, hy - 60 * s, 30 * s, 70 * s, sx * 25), (hx - 150 * s, hy - 160 * s, hx + 70 * s, hy + 40 * s),
                 ramp('#8a5a2a'), ow=3)
    if yawn > 0.1:
        line(cv, [(hx + 10 * s, hy + 10 * s), (hx + 40 * s, hy + 10 * s)], 6 * s, INKC)
        my = hy + 70 * s
        cv.shape(ellipse(hx + 100 * s, my, 60 * s, 50 * s * yawn), (hx + 30 * s, my - 60 * s, hx + 170 * s, my + 60 * s), ramp('#5a1f2a'), ow=3, shadow=0)
        cv.shape(ellipse(hx + 100 * s, my + 25 * s * yawn, 30 * s, 18 * s * yawn), (hx + 60 * s, my, hx + 140 * s, my + 50 * s), ramp('#ff7f8a'), ow=0, shadow=0)
    else:
        dot(cv, hx + 30 * s, hy - 10 * s, 12 * s)


def jolt(lt, t0, amt=60):
    """A hiccup jolt: a quick upward kick that settles."""
    if lt < t0:
        return 0.0
    u = lt - t0
    return -amt * np.exp(-u / 0.12) * np.cos(u * 30)
