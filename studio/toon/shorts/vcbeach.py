#!/usr/bin/env python3
"""GTA 6's most-hyped spot (Vice City's beach) is copied from Miami's South Beach, and that beach was built by hand.
No Rockstar art: our own neon beach strip, our own car, no logos/characters/game scenes.
Opens on a pink convertible cruising the neon strip; ~800 historic 1920s-30s buildings lighting up; rewind to 1912: the beach
melts away; the mangrove swamp and mosquito swarm (white clothes turned black); Carl Fisher, 1913; mangroves chopped by
hand, then a dredge sucking sand off the bay floor and spraying it over the swamp; 6 million cubic yards = ~1,800 Olympic
pools; Rosie the elephant on the job; the sea still eating it: trucks dumping fresh sand; the payoff: you're cruising a copy
of a beach people built by hand.
Facts: Red Bull 'GTA 6 locations ranked' (Vice City most anticipated); Forbes (Oct 27 2026: Ocean Beach = South Beach /
Ocean Drive per Rockstar). Greater Miami & Miami Beach (Art Deco District: ~800 historic buildings, 1920s-30s, neon).
American Heritage 'The Man Who Invented Miami Beach' (mangrove swamps; 'Mosquitoes blackened our white clothing'; dredged sand
from the bay bottom; Rosie the elephant helped with construction). WorldAtlas citing historian Polly Redford (from summer
1913: ~6 million cubic yards of fill dredged from Biscayne Bay; laborers cleared mangroves by hand). Daily Star/AFP (Jan
2020: Army Corps renourishment, 100-250 truckloads a day). 6M yd3 / 3,270 yd3 per Olympic pool = ~1,835."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

DIVE = {}
PASTELS = ['#ffb0c8', '#9ae0d8', '#ffe0a0', '#c8b0ff', '#a0d8ff', '#ffc8a0']
NEONS = ['#ff4ad0', '#4ae8ff', '#ffe04a', '#9a6aff', '#4aff9a']
SAND = ramp('#f0d8a0', '#c8a868', '#fff0c8')
MUD = ramp('#4a5a2a', '#2a3418', '#6a7a40')
MANG = ramp('#3a6a2a', '#1f4018', '#5a8a40')
ROOT = ramp('#6a4a2a', '#3a2814', '#8a6a4a')
CAR = ramp('#ff6ab0', '#c83a80', '#ffa0d0')
GREY = ramp('#9a9aa8', '#6a6a78', '#c8c8d4')
WATER = ramp('#3ab0d8', '#1a6a9a', '#7ad8f0')


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def deco(cv, x, base, w, h, i, lit=1.0, a=1.0):
    """an old-style pastel hotel with a stepped top and neon trim (our own design)"""
    col = PASTELS[i % len(PASTELS)]; neon = NEONS[i % len(NEONS)]
    box(cv, x, base - h / 2, w / 2, h / 2, ramp(col), r=6, ow=4, alpha=a)
    box(cv, x, base - h - 30, w * 0.3, 30, ramp(col), r=4, ow=4, alpha=a)                 # stepped top
    box(cv, x, base - h - 75, w * 0.12, 20, ramp(col), r=4, ow=3, alpha=a)
    for r_ in range(int(h // 90)):
        for c in (-1, 0, 1):
            box(cv, x + c * w * 0.28, base - 60 - r_ * 90, w * 0.08, 24, ramp('#2a4a6a' if lit < 0.5 else '#ffe9a0'), r=4, ow=2, alpha=a)
    if lit > 0:
        line(cv, [(x - w / 2 + 6, base - h + 20), (x + w / 2 - 6, base - h + 20)], 10, flat(hexc(neon)), a=lit * a)
        cv.glow(rbox(x, base - h + 20, w / 2, 6, 4), (x - w, base - h - 100, x + w, base - h + 140), neon, 30, 0.7 * lit * a)
        line(cv, [(x, base - h + 40), (x, base - 40)], 8, flat(hexc(neon)), a=lit * a * 0.9)


def palm(cv, x, base, h, lean=0.1, T=0.0, col='#2a1a3a'):
    P = ramp(col)
    tx, ty = x + lean * h, base - h
    line(cv, [(x, base), (x + lean * h * 0.6, base - h * 0.5), (tx, ty)], 22, P, ow=0)
    for k in range(9):                                                        # fronds: arcs out and over, drooping at the tips
        a = np.pi * (0.02 + 0.96 * k / 8) + 0.06 * np.sin(T * 2 + k)
        dx, dy = np.cos(a), -np.sin(a) * 0.55
        pts = [(tx + dx * d, ty + dy * d + 0.0024 * d * d) for d in np.linspace(0, 210, 7)]
        line(cv, pts, 14, P, ow=0)
        for d in (70, 120, 170):
            px, py = tx + dx * d, ty + dy * d + 0.0024 * d * d
            line(cv, [(px, py), (px + dx * 22, py + 34)], 7, P, ow=0)


def car(cv, x, y, s, T, moving=True):
    b = 4 * np.sin(T * 14) if moving else 0
    pts = [(x - 200 * s, y), (x - 190 * s, y - 50 * s), (x - 60 * s, y - 60 * s), (x - 10 * s, y - 100 * s), (x + 60 * s, y - 100 * s),
           (x + 90 * s, y - 60 * s), (x + 200 * s, y - 50 * s), (x + 210 * s, y)]
    cv.shape(poly([(px, py + b) for px, py in pts]), pbox(pts, 14), CAR, ow=5)
    box(cv, x + 20 * s, y - 80 * s + b, 40 * s, 14 * s, ramp('#9ad8ff'), r=6 * s, ow=3, alpha=0.8)
    for wx in (x - 120 * s, x + 130 * s):
        disc(cv, wx, y + 10 * s, 42 * s, DARK, ow=4)
        a = -T * 12
        line(cv, [(wx - 26 * s * np.cos(a), y + 10 * s - 26 * s * np.sin(a)), (wx + 26 * s * np.cos(a), y + 10 * s + 26 * s * np.sin(a))], 6 * s, METAL)
    cv.glow(circle(x + 210 * s, y - 25 * s, 14 * s), (x + 100 * s, y - 120 * s, x + 420 * s, y + 80 * s), '#fff4c0', 40 * s, 0.6)


def strip(cv, T, scroll, lit_k=1.0, a=1.0):
    """the neon beach strip at sunset: hotels scrolling by, palms in front, sidewalk"""
    cv.background('#ff7ab0', '#2a1050', vignette=0.3)
    cv.glow(circle(0, -500, 200), (-600, -900, 600, -100), '#ffb050', 160, 0.6)
    disc(cv, 0, -500, 180, ramp('#ffd060', '#ff8a40', '#fff0a0'), ow=0, shadow=0)
    for j in range(7):
        x = ((j * 300 - scroll) % 2100) - 1050
        lit = float(np.clip(lit_k * 7 - j, 0, 1))
        deco(cv, x, 320, 250, 420 + 80 * (j % 3), j, lit=lit, a=a)
    box(cv, 0, 420, 1400, 110, ramp('#f4c0d0', '#c890a8', '#ffe0ec'), r=0, ow=0, shadow=0)    # sidewalk
    box(cv, 0, 700, 1400, 200, ramp('#3a3a48', '#22222c', '#55556a'), r=0, ow=0, shadow=0)    # road
    for j in range(8):
        x = ((j * 260 - scroll * 1.4) % 2080) - 1040
        box(cv, x, 700, 60, 8, ramp('#ffe04a'), r=3, ow=0, shadow=0)
    for j in range(4):
        x = ((j * 520 + 130 - scroll * 1.2) % 2080) - 1040
        palm(cv, x, 470, 640, 0.08 * (1 if j % 2 else -1), T)


def mangrove(cv, x, base, s, T, chop=0.0):
    """a mangrove: tangled arching roots into the water, a bushy top; chop>0 tips it over"""
    ang = 1.3 * ease(chop)
    if ang > 1.25:
        return
    def R(px, py):
        c, s_ = np.cos(ang), np.sin(ang)
        dx, dy = px - x, py - base
        return (x + dx * c - dy * s_, base + dx * s_ + dy * c)
    for k in range(5):
        dx = (-100 + 50 * k) * s
        line(cv, [R(x, base - 140 * s), R(x + dx * 0.6, base - 60 * s), R(x + dx, base + 10 * s)], 10 * s, ROOT, ow=2)
    line(cv, [R(x, base - 140 * s), R(x, base - 300 * s)], 18 * s, ROOT, ow=3)
    for dx, dy, r in ((-70, -330, 80), (0, -390, 100), (70, -330, 80), (0, -290, 70)):
        px, py = R(x + dx * s, base + dy * s)
        disc(cv, px, py, r * s, MANG, ow=3)


def mosquitoes(cv, x, y, n, T, spread=300, seed=1):
    rr = np.random.default_rng(seed)
    for j in range(n):
        ph = rr.uniform(0, 6.28); fx = rr.uniform(1.5, 3.5); fy = rr.uniform(1.5, 3.5)
        px = x + spread * np.sin(T * fx + ph) * rr.uniform(0.3, 1.0)
        py = y + spread * 0.6 * np.cos(T * fy + ph * 1.3) * rr.uniform(0.3, 1.0)
        dot(cv, px, py, 6, INKC)
        dot(cv, px - 6, py - 5, 4, flat(hexc('#c8d0e0')), a=0.6)
        dot(cv, px + 6, py - 5, 4, flat(hexc('#c8d0e0')), a=0.6)


def elephant(cv, x, y, s, T):
    b = 6 * np.sin(T * 4)
    cv.shape(ellipse(x, y - 200 * s, 230 * s, 150 * s), (x - 250 * s, y - 360 * s, x + 250 * s, y - 40 * s), GREY, ow=5)
    for lx in (-150, -60, 60, 150):
        box(cv, x + lx * s, y - 50 * s, 40 * s, 80 * s, GREY, r=14 * s, ow=4)
    hx, hy = x + 230 * s, y - 260 * s + b
    cv.shape(ellipse(hx - 50 * s, hy + 10 * s, 90 * s, 120 * s), (hx - 150 * s, hy - 120 * s, hx + 50 * s, hy + 140 * s), ramp('#8a8a98'), ow=4)   # the ear
    disc(cv, hx, hy, 100 * s, GREY, ow=5)
    line(cv, [(hx + 70 * s, hy + 30 * s), (hx + 130 * s, hy + 130 * s), (hx + 120 * s + 20 * s * np.sin(T * 3), hy + 230 * s)], 34 * s, GREY, ow=4)
    disc(cv, hx + 30 * s, hy - 25 * s, 12 * s, INKC)
    cv.shape(ellipse(hx - 10 * s, hy - 100 * s, 60 * s, 18 * s), (hx - 80 * s, hy - 130 * s, hx + 60 * s, hy - 70 * s), ramp('#f0d890'), ow=3)   # a straw hat
    box(cv, hx - 10 * s, hy - 125 * s, 36 * s, 22 * s, ramp('#f0d890'), r=6 * s, ow=3)


def truck(cv, x, y, s, tip=0.0):
    box(cv, x + 150 * s, y - 80 * s, 70 * s, 70 * s, ramp('#ffb020', '#c88010', '#ffd080'), r=12 * s, ow=4)   # cab
    box(cv, x + 170 * s, y - 110 * s, 34 * s, 26 * s, ramp('#9ad8ff'), r=4 * s, ow=2)
    a = np.radians(-35 * tip)
    pts = [(-200, -170), (60, -170), (60, -20), (-200, -20)]
    c, s_ = np.cos(a), np.sin(a)
    pv = [(x + 60 * s + (px - 60) * s * c - (py + 20) * s * s_, y - 20 * s + (px - 60) * s * s_ + (py + 20) * s * c) for px, py in pts]
    cv.shape(poly(pv), pbox(pv, 8), ramp('#ffb020', '#c88010', '#ffd080'), ow=4)
    for wx in (x - 120 * s, x + 150 * s):
        disc(cv, wx, y, 40 * s, DARK, ow=4)


# ---------------------------------------------------------------- beats
def b0_cruise(lt, dur, T):
    """Frame one: the pink convertible already cruising the neon strip at sunset."""
    cv = Canvas(0, 0, 1.0)
    tl = lt + 5                                                              # beat clock, not global: a clean loop seam
    strip(cv, tl, scroll=(lt + 3) * 320)
    car(cv, -40, 660, 1.6, tl)
    sbadge(cv, 'VICE CITY = MIAMI', -800, (255, 120, 220))
    return cv


def b1_neon(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    k = float(np.clip(lt / (dur * 0.7), 0, 1))
    strip(cv, T, scroll=600 + lt * 40, lit_k=k)
    n = int(800 * ease(k))
    slabel(cv, '%d BUILDINGS' % n, 0, -800, 110, (255, 236, 80))
    slabel(cv, '1920s - 30s', 0, -680, 80, WHT, a=float(np.clip((lt - dur * 0.4) / 0.3, 0, 1)))
    return cv


def b2_rewind(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    k = ease(np.clip(lt / (dur * 0.75), 0, 1))
    strip(cv, T, scroll=640 - lt * 600, lit_k=1 - k, a=1 - k)
    if k > 0:                                                                 # the swamp coming back up through it
        box(cv, 0, 600, 1400, 520, MUD, r=0, ow=0, shadow=0, alpha=k)
    yr = int(2026 - (2026 - 1912) * k)
    box(cv, 0, -560, 260, 110, ramp('#0a0a12'), r=20, ow=5)
    label(cv, str(yr), 0, -560, 130, (255, 210, 80), stroke=0)
    hook_text(cv, "DIDN'T EXIST", lt, y=-800, size=130, color=(255, 120, 90), pop_t=dur * 0.55)
    return cv


def b3_swamp(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#8aa070', '#3a4a2a', vignette=0.4)
    box(cv, 0, 620, 1400, 520, MUD, r=0, ow=0, shadow=0)
    for j, x in enumerate((-420, -120, 200, 470)):
        mangrove(cv, x, 330 + 30 * (j % 2), 1.0 + 0.15 * (j % 2), T)
    k = float(np.clip((lt - dur * 0.35) / (dur * 0.5), 0, 1))               # a man in white, going black with bugs
    guy(cv, 0, 760, 0.7, face='worried', arms=(reach(-1, -200, -620), reach(1, 200, -640)), shirt=ramp('#f4f4f4', '#c8c8c8', '#ffffff'))
    rr = np.random.default_rng(4)
    for j in range(int(140 * k)):
        dot(cv, rr.uniform(-110, 110), 760 - rr.uniform(150, 520), 7, INKC)
    mosquitoes(cv, 0, -200, 60, T, spread=480)
    mosquitoes(cv, 0, 380, 30, T * 1.3, spread=200, seed=2)
    sbadge(cv, 'MOSQUITO SWAMP', -800, (200, 230, 120))
    return cv


def b4_fisher(lt, dur, T):
    cv = Canvas(0, -60, 1.05)
    cv.background('#f0d8a0', '#a08050', vignette=0.45)                        # sepia, old-photo feel
    box(cv, 0, 640, 1400, 420, MUD, r=0, ow=0, shadow=0)
    for x in (-460, 420):
        mangrove(cv, x, 360, 0.9, T)
    guy(cv, -120, 760, 0.85, face='happy', arms=(reach(-1, -160, -560), reach(1, 300, -880)),
        shirt=ramp('#e8dcc0', '#b8a888', '#fff4dc'))
    hy = 760 - 0.85 * 820                                                    # a straw boater hat
    cv.shape(ellipse(-120, hy, 130, 26), (-260, hy - 40, 20, hy + 40), ramp('#f0d890', '#c0a050', '#fff0b0'), ow=4)
    box(cv, -120, hy - 30, 70, 34, ramp('#f0d890', '#c0a050', '#fff0b0'), r=8, ow=4)
    box(cv, -120, hy - 14, 72, 10, ramp('#2a2a40'), r=2, ow=0, shadow=0)
    k = ease(np.clip((lt - 0.4) / 0.5, 0, 1))                                 # his dream: a city floating up
    for j in range(5):
        deco(cv, 120 + j * 90, -340, 80, 160 + 40 * (j % 3), j, lit=0.0, a=0.6 * k)
    cv.glow(ellipse(300, -440, 300, 200), (-100, -800, 700, -100), '#fff4d0', 100, 0.4 * k)
    sbadge(cv, '1913: CARL FISHER', -800, (120, 80, 40))
    return cv


def b5_dredge(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#a8d8f0', '#e8f4ff', vignette=0.3)
    box(cv, 0, 700, 1400, 360, WATER, r=0, ow=0, shadow=0)                   # the bay
    chop = lt < dur * 0.4
    if chop:
        for j, x in enumerate((-380, -100, 180, 440)):
            c = float(np.clip((lt - 0.2 - j * 0.25) / 0.35, 0, 1))
            mangrove(cv, x, 380, 0.9, T, chop=c)
            sw = np.sin(T * 6 + j) * (1 - c)                                   # workers stay put (steady figures); the swing stops when the tree is down
            guy(cv, x - 150, 700, 0.5, face='calm' if c < 1 else 'happy', arms=(reach(-1, -60, -360), reach(1, 150 + 30 * sw, -440, bend=1)))
            line(cv, [(x - 30, 330 + 34 * sw), (x - 60, 290 + 34 * sw)], 14, ROOT, ow=3)
        sbadge(cv, 'CHOPPED BY HAND', -800, (200, 230, 120))
    else:
        k = float(np.clip((lt - dur * 0.4) / (dur * 0.55), 0, 1))
        box(cv, 300, 560, 220, 60, ramp('#c84a2a', '#8a2a14', '#ff7a5a'), r=14, ow=5)         # the dredge barge
        box(cv, 330, 460, 70, 60, ramp('#e8e4dc'), r=8, ow=4)
        line(cv, [(380, 400), (380, 300)], 18, DARK, ow=3)
        line(cv, [(220, 600), (180, 820)], 20, METAL, ow=3)                                     # sucking pipe
        line(cv, [(100, 520), (-80, 300), (-200, 280)], 26, METAL, ow=3)                        # spray pipe
        rr = np.random.default_rng(int(T * 20))
        for j in range(30):                                                                       # sand spray arcing out
            u = rr.random()
            px = -200 - 400 * u; py = 280 - 260 * u + 420 * u * u
            dot(cv, px, py, rr.uniform(8, 16), SAND)
        h = 260 * k
        box(cv, -420, 640 - h / 2, 380, h / 2 + 10, SAND, r=40, ow=4)          # new land rising
        slabel(cv, 'SAND FROM THE BAY', 0, -800, 84, (255, 210, 80))
    return cv


def b6_pools(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a5a8a', '#0e2440', vignette=0.4)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    slabel(cv, '%s YD³' % format(int(6000000 * k), ','), 0, -800, 110, (255, 236, 80))
    k2 = ease(np.clip((lt - dur * 0.3) / (dur * 0.6), 0, 1))
    n = int(60 * k2)
    for j in range(60):
        x = -450 + (j % 6) * 180; y = -560 + (j // 6) * 110
        filled = j < n
        box(cv, x, y, 70, 34, WATER if not filled else SAND, r=8, ow=3)
        for q in range(3):
            line(cv, [(x - 50 + q * 50, y - 34), (x - 50 + q * 50, y + 34)], 3, flat(hexc('#ffffff')), a=0.5)
    slabel(cv, '= 1,800 POOLS', 0, 640, 110, (154, 220, 255), a=k2)
    return cv


def b7_rosie(lt, dur, T):
    cv = Canvas(0, -80, 1.0)
    cv.background('#f0d8a0', '#a08050', vignette=0.45)
    box(cv, 0, 560, 1400, 420, SAND, r=0, ow=0, shadow=0)
    x = -200 + 120 * ease(np.clip(lt / dur, 0, 1))
    elephant(cv, x, 520, 1.2, T)
    box(cv, x - 420, 440, 110, 70, WOOD, r=10, ow=4)                          # a cart of lumber she's pulling
    for j in range(3):
        line(cv, [(x - 520, 380 + j * 20), (x - 320, 380 + j * 20)], 14, ramp('#c8a060'), ow=2)
    line(cv, [(x - 310, 440), (x - 200, 400)], 6, ROOT)
    for wx in (x - 480, x - 360):
        disc(cv, wx, 520, 30, DARK, ow=3)
    hook_text(cv, 'ROSIE!', lt, y=-800, size=170, color=(255, 210, 80), pop_t=0.3)
    return cv


def b8_trucks(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#7ac0f0', '#e0f0ff', vignette=0.25)
    box(cv, 0, 760, 1400, 300, WATER, r=0, ow=0, shadow=0)
    for j in range(4):                                                        # waves pulling at the beach
        u = (T * 0.5 + j / 4) % 1
        x = 560 - 1100 * u
        line(cv, [(x - 120, 470 + 20 * np.sin(u * 9)), (x, 450), (x + 120, 470)], 10, flat(hexc('#ffffff')), a=0.8)
    box(cv, 0, 380, 1400, 120, SAND, r=0, ow=0, shadow=0)
    u = (lt * 0.5) % 1
    tip = float(np.clip((u - 0.3) / 0.2, 0, 1)) * float(np.clip((0.95 - u) / 0.15, 0, 1))
    truck(cv, 60, 260, 1.4, tip)
    if tip > 0.3:
        rr = np.random.default_rng(int(T * 20))
        for j in range(30):
            dot(cv, -250 - rr.uniform(0, 120), 140 + rr.uniform(0, 160), rr.uniform(8, 18), SAND)
    cnt = min(250, int(250 * lt / (dur * 0.8)))
    slabel(cv, '%d LOADS A DAY' % cnt, 0, -800, 100, (255, 210, 80))
    slabel(cv, 'THE SEA EATS IT', 0, -680, 80, WHT, a=float(np.clip(lt / 0.4, 0, 1)))
    return cv


def b9_byhand(lt, dur, T):
    cv = Canvas(0, 0, 1.0 + 0.05 * ease(np.clip(lt / dur, 0, 1)))
    strip(cv, T, scroll=(lt + 40) * 320)
    car(cv, -40, 660, 1.6, T)
    hook_text(cv, 'BUILT BY HAND', lt, y=-800, size=118, color=(255, 236, 80), pop_t=dur * 0.5)
    return cv


BEATS = [b0_cruise, b1_neon, b2_rewind, b3_swamp, b4_fisher, b5_dredge, b6_pools, b7_rosie, b8_trucks, b9_byhand]

if __name__ == '__main__':
    run(BEATS)
