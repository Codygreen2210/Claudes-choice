#!/usr/bin/env python3
"""Why onions make you cry. Opens on the knife chopping, him crying buckets; inside the onion: cells like water balloons,
the knife bursts them, two things that were kept apart mix, enzymes grab the sulfur, a gas rises (the onion's alarm vs a
hungry critter), drifts into his eye, a little acid in the tear film, the sting, the tear floodgates; the fixes (chill it,
a fan). Loops back into the chop.
Facts: The Conversation, 'Why onions make us cry (and why some don't)': cutting ruptures cells, enzymes (alliinase,
lachrymatory-factor synthase) act on sulfur compounds making propanethial S-oxide, a volatile gas; it reaches the eyes,
forms a little sulfenic acid in the tear film, irritates, tears follow; chilling slows the enzymes; a cooker hood /
moving air draws the gas away. Defence against animals: Chemistry World / Discover."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403
import pepper as PP

DIVE = {1: (180, 520), 6: (540, 700)}
GRN = (120, 255, 140)
GAS = (190, 255, 120)
ONI = ramp('#f4e2b8', '#c9a46a', '#fff4d8')
SKINO = ramp('#c9853a', '#8a5420', '#e8a860')
CELLW = ramp('#fff6dc', '#e2cc98', '#ffffff')
ENZ = ramp('#ff7ad0', '#c03a98', '#ffc0ea')
SULF = ramp('#ffe14d', '#c8a020', '#fff4a0')
TEAR = ramp('#9fdcff', '#4fa8e0', '#e0f6ff')
GX, GY, GS = 0, 640, 1.0
BOARD = (60, GY - 470)       # cutting board centre (world)


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def onion_half(cv, x, y, s=1.0, cut=1.0):
    """an onion on its side, cut face showing rings; cut 0..1 how far sliced"""
    cv.shape(ellipse(x, y, 120 * s, 105 * s), (x - 130 * s, y - 115 * s, x + 130 * s, y + 115 * s), SKINO, ow=4)
    cv.shape(ellipse(x + 20 * s, y, 92 * s, 92 * s), (x - 80 * s, y - 100 * s, x + 120 * s, y + 100 * s), ONI, ow=3)
    for r in (70, 50, 30, 12):
        cv.shape(subtract(ellipse(x + 22 * s, y, r * s, r * s), ellipse(x + 22 * s, y, (r - 5) * s, (r - 5) * s)),
                 (x - 60 * s, y - 80 * s, x + 110 * s, y + 80 * s), ramp('#e6cf9a'), ow=0, shadow=0, flat=True)
    for k in range(int(5 * cut)):                                          # slices already off
        sx = x - 150 * s - k * 34 * s
        cv.shape(ellipse(sx, y + 10 * s, 14 * s, 80 * s), (sx - 20 * s, y - 80 * s, sx + 20 * s, y + 100 * s), ONI, ow=3)


def knife(cv, x, y, s=1.0, ang=0.0):
    c, sn = np.cos(np.radians(ang)), np.sin(np.radians(ang))
    def P(u, v): return (x + (u * c - v * sn) * s, y + (u * sn + v * c) * s)
    blade = [P(0, -6), P(-230, -10), P(-250, 30), P(0, 34)]
    cv.shape(poly(blade), pbox(blade, 4), ramp('#e8eef4', '#a8b4c0', '#ffffff'), ow=4)
    hnd = [P(0, -8), P(110, -6), P(115, 30), P(0, 34)]
    cv.shape(poly(hnd), pbox(hnd, 4), ramp('#3a2a20', '#20140c', '#5a4030'), ow=4)


def gas_puffs(cv, x, y, T, a=1.0, n=7, spread=120, rise=420, s=1.0):
    for k in range(n):
        u = (T * 0.5 + k / n) % 1
        px = x + np.sin(u * 7 + k * 1.7) * spread * s * (0.3 + u)
        py = y - u * rise * s
        r = (20 + 40 * u) * s
        cv.glow(circle(px, py, r), (px - r * 2, py - r * 2, px + r * 2, py + r * 2), '#c0ff80', 30, 0.5 * a * (1 - u))
        disc(cv, px, py, r, ramp('#d8ff9a', '#9ad860', '#f0ffd0'), ow=0, shadow=0, alpha=0.55 * a * (1 - u))


def tears(cv, x, y, T, a=1.0, s=1.0, n=2, gush=0.0):
    for side in (-1, 1):
        ex = x + side * 34 * s
        for k in range(n):
            u = (T * 1.6 + k / n + (0.5 if side > 0 else 0)) % 1
            dot(cv, ex + side * 6 * s, y + u * 140 * s, (9 + 4 * gush) * s, flat(hexc('#7fd0ff')), a=a * (1 - u * 0.6))
        if gush > 0:                                                       # streams
            line(cv, [(ex, y + 10 * s), (ex + side * 8 * s, y + 60 * s), (ex + side * 6 * s, y + 110 * s)], 6 * s * gush, TEAR, ow=2, flat=False, a=a)


def chopper(cv, lt, T, cry=1.0, chill=False, fan=0.0):
    PP.kitchen(cv, T)
    box(cv, 0, GY - 440, 560, 60, WOOD, r=10)                              # counter
    box(cv, GX - 100, GY - 462, 300, 18, ramp('#e0b070', '#a87838', '#f4d090'), r=8)
    chop = abs(np.sin(T * 7.5))
    sx = 5 * np.sin(T * 31) * cry
    hly = -520 - 70 * chop                                                 # knife hand, his own units: elbow-down path, no flips
    right = reach(1, 230, hly)
    left = reach(-1, -40, -500)
    guy(cv, GX + sx - 140, GY, GS, face='pain' if cry > 0.5 else ('worried' if cry > 0.25 else 'happy'), arms=(left, right))
    OX = GX - 140 + 30                                                     # the onion sits between his hands
    onion_half(cv, OX + 40, GY - 520, 0.6, cut=1.0)
    knife(cv, GX + sx - 140 + 230, GY + hly + 6, 0.8, ang=-20 + 14 * chop)
    if chill:
        for k in range(6):
            a = T * 2 + k
            dot(cv, OX + 40 + 90 * np.cos(a), GY - 520 + 60 * np.sin(a), 6, flat(hexc('#e8f8ff')), a=0.9)
    gas_puffs(cv, OX + 40, GY - 580, T, a=0.9 * cry, rise=380 if fan == 0 else 200, spread=60)
    if fan > 0:
        fx, fy = 380, GY - 560
        box(cv, fx, fy + 90, 20, 90, METAL, r=6)
        cv.shape(circle(fx, fy, 95), (fx - 100, fy - 100, fx + 100, fy + 100), ramp('#dfe6ee', '#9aa6b4', '#ffffff'), ow=4)
        for k in range(3):
            a = T * 25 + k * 2.1
            line(cv, [(fx, fy), (fx + 75 * np.cos(a), fy + 75 * np.sin(a))], 26, ramp('#7fc0ff'), ow=2)
        for k in range(4):                                                 # wind lines, gas blown away
            u = (T * 1.5 + k / 4) % 1
            line(cv, [(fx - 120 - 400 * u, fy - 60 + 40 * k), (fx - 200 - 400 * u, fy - 60 + 40 * k)], 6, flat(hexc('#ffffff')), a=0.7 * (1 - u))
    hx, hy2 = GX + sx - 140, GY - 762 * GS
    tears(cv, hx, hy2 + 20, T, a=cry, gush=cry)


def cells(cv, T, burst=0.0, mix=0.0, enz=0.0, gas=0.0, bx=-60, n=5):
    """Cells of onion flesh as water balloons. burst: knife has passed (cells on the left of bx pop)."""
    cv.background('#3a2a12', '#1a1006', vignette=0.4)
    for i in range(-2, 3):
        for j in range(-3, 4):
            x, y = i * 230 + (j % 2) * 115, j * 200
            broke = burst > 0 and x < bx + (burst - 0.5) * 1200
            if not broke:
                wob = 6 * np.sin(T * 3 + i + j)
                cv.shape(rbox(x, y, 100 + wob, 85 - wob, 60), (x - 120, y - 100, x + 120, y + 100), CELLW, ow=4, alpha=0.95)
                disc(cv, x - 30, y - 10, 22, SULF, ow=3)                       # the sulfur stuff, one side
                disc(cv, x + 34, y + 14, 20, ENZ, ow=3)                        # the enzyme, kept apart by a wall
                line(cv, [(x, y - 70), (x, y + 70)], 6, flat(hexc('#c9a46a')), a=0.8)
            else:
                for k in range(3):                                          # popped balloon scraps + spill
                    a = k * 1.05 + i
                    line(cv, [(x + 60 * np.cos(a), y + 50 * np.sin(a)), (x + 95 * np.cos(a + 0.2), y + 80 * np.sin(a + 0.2))], 8, CELLW[0] if False else flat(hexc('#fff6dc')), a=0.8)
                mx = mix * 20
                disc(cv, x - 30 + mx, y - 10, 20, SULF, ow=3)
                disc(cv, x + 34 - mx, y + 14 - mx * 0.5, 18, ENZ, ow=3)
                if enz > 0:
                    for k in range(3):                                      # enzyme pac-man chomps the sulfur into gas
                        g = (T * 1.2 + k / 3 + (i + j) * 0.13) % 1
                        if g < enz:
                            dot(cv, x + 10, y - 20 - g * 260 * gas, 12 + 14 * g, flat(hexc('#c8ff80')), a=0.9 * (1 - g))


def critter(cv, x, y, s, T, scared=0.0):
    """A hungry gopher, sniffing, then recoiling"""
    jx = -60 * s * scared
    cv.shape(ellipse(x + jx, y, 90 * s, 70 * s), (x + jx - 100 * s, y - 80 * s, x + jx + 100 * s, y + 80 * s), ramp('#a8763a', '#6a4418', '#d8a060'), ow=4)
    cv.shape(circle(x + jx + 70 * s, y - 40 * s, 52 * s), (x + jx + 10 * s, y - 100 * s, x + jx + 130 * s, y + 20 * s), ramp('#b8864a', '#7a5428', '#e8b070'), ow=4)
    disc(cv, x + jx + 85 * s, y - 55 * s, 10 * s, DARK, ow=0, shadow=0)
    disc(cv, x + jx + 120 * s, y - 32 * s, 9 * s, ramp('#3a2020'), ow=0, shadow=0)
    box(cv, x + jx + 104 * s, y - 8 * s, 14 * s, 14 * s, ramp('#ffffff'), r=3 * s)
    if scared > 0:
        tears(cv, x + jx + 85 * s, y - 50 * s, T, a=scared, s=0.6, n=2)


def eyeball(cv, x, y, r, T, gas=0.0, acid=0.0, sting=0.0, flood=0.0):
    cv.background('#2a1520', '#12080e', vignette=0.45)
    cv.shape(ellipse(x, y, r, r * 0.7), (x - r, y - r, x + r, y + r), WHITE, ow=5)
    for k in range(int(8 * sting)):                                        # red veins come in as it stings
        a = k * 0.8 + 0.3
        pts = [(x + r * 0.95 * np.cos(a), y + r * 0.66 * np.sin(a)), (x + r * 0.7 * np.cos(a + 0.1), y + r * 0.45 * np.sin(a + 0.15)),
               (x + r * 0.55 * np.cos(a - 0.05), y + r * 0.36 * np.sin(a - 0.1))]
        line(cv, pts, 6, flat(hexc('#e8403a')), a=sting)
    disc(cv, x, y, r * 0.38, ramp('#7a5a2a', '#4a3410', '#b08a4a'), ow=3)
    disc(cv, x, y, r * 0.17, DARK, ow=0, shadow=0)
    disc(cv, x - r * 0.12, y - r * 0.12, r * 0.06, flat(hexc('#ffffff')), ow=0, shadow=0)
    cv.shape(subtract(ellipse(x, y - 20, r * 1.02, r * 0.74), ellipse(x, y, r, r * 0.7)), (x - r - 10, y - r, x + r + 10, y), TEAR, ow=0, shadow=0, alpha=0.6)
    if gas > 0:
        gas_puffs(cv, x, y + r * 1.4, T, a=gas, n=8, spread=200, rise=r * 1.8)
    if acid > 0:
        for k in range(10):
            a = k * 0.63 + T * 0.3
            px, py = x + r * 0.8 * np.cos(a), y + r * 0.55 * np.sin(a)
            cv.glow(circle(px, py, 14), (px - 50, py - 50, px + 50, py + 50), '#c8ff40', 24, acid * (0.6 + 0.4 * np.sin(T * 9 + k)))
            dot(cv, px, py, 10, flat(hexc('#d8ff60')), a=acid)
    if flood > 0:                                                          # the tear gland up top floods it
        gx, gy = x + r * 0.6, y - r * 0.85
        cv.shape(ellipse(gx, gy, 90, 50), (gx - 100, gy - 60, gx + 100, gy + 60), ramp('#ff9ab0', '#c86a80', '#ffd0dc'), ow=4)
        for k in range(10):
            u = (T * 1.4 + k / 10) % 1
            dot(cv, gx - 40 - u * r * 1.2, gy + 30 + u * r * 1.0 + 20 * np.sin(k), 16, flat(hexc('#7fd0ff')), a=flood * (1 - u * 0.4))
        line(cv, [(x - r * 0.9, y + r * 0.5), (x - r * 0.95, y + r * 1.4)], 30 * flood, TEAR, ow=2, flat=False)


# ---------------------------------------------------------------- beats
def b0_hook(lt, dur, T):
    k = ease(float(np.clip((lt + 0.6) / 1.2, 0, 1)))
    cv = Canvas(-40, GY - 640 - 40 * k, 1.35 + 0.15 * k)
    chopper(cv, lt, T, cry=1.0)
    hook_text(cv, 'ONION TEARS', lt, y=-800, size=124, color=GAS, pop_t=-0.25 if lt < 0 else 0.0)
    return cv


def b1_cells(lt, dur, T):
    cv = Canvas(0, 0, 0.9 + 0.08 * ease(np.clip(lt / dur, 0, 1)))
    cells(cv, T)
    slabel(cv, 'MILLIONS OF CELLS', 0, -760, 100, YEL, a=ease(np.clip((lt - 0.3) / 0.3, 0, 1)))
    return cv


def b2_smash(lt, dur, T):
    sx_, sy_ = shake(lt, 0.4, 24, 0.5)
    cv = Canvas(sx_, sy_, 0.9)
    b = float(np.clip((lt - 0.1) / 2.6, 0, 1))
    cells(cv, T, burst=b, mix=ease(np.clip((lt - 1.6) / 1.0, 0, 1)), bx=200)
    kx = -700 + 1600 * b
    knife(cv, kx + 120, 240, 2.4, ang=-90)
    hook_text(cv, 'SMASH!', lt, y=-760, size=150, pop_t=0.4, color=(255, 90, 80))
    return cv


def b3_enzymes(lt, dur, T):
    cv = Canvas(0, 0, 1.4)
    cells(cv, T, burst=1.0, mix=1.0, enz=ease(np.clip(lt / 0.8, 0, 1)), gas=0.4, bx=600)
    slabel(cv, 'ENZYMES + SULFUR', 0, -760, 92, (255, 140, 220))
    return cv


def b4_gas(lt, dur, T):
    cv = Canvas(0, -200 - 120 * ease(np.clip(lt / dur, 0, 1)), 1.0)
    cells(cv, T, burst=1.0, mix=1.0, enz=1.0, gas=1.0, bx=600)
    gas_puffs(cv, 0, -100, T, a=1.0, n=10, spread=300, rise=900)
    hook_text(cv, 'GAS!', lt, y=-760, size=150, pop_t=0.3, color=GAS)
    return cv


def b5_alarm(lt, dur, T):
    cv = Canvas(-170, 330, 1.6)
    cv.background('#7ac0ff', '#c8e8ff', vignette=0.2)
    box(cv, 0, 520, 900, 260, ramp('#6a4a28', '#4a3018', '#8a6a40'), r=0, ow=0, shadow=0)
    for k in range(5):
        line(cv, [(-60 + 30 * k, 300), (-80 + 30 * k, 180)], 12, ramp('#4fb84f', '#2a7a2a', '#8ae08a'), ow=2, flat=False)
    onion_half(cv, 0, 380, 1.2, cut=0)
    bite = lt > 1.0
    scared = ease(np.clip((lt - 1.1) / 0.4, 0, 1))
    critter(cv, -320 + 100 * ease(np.clip(lt / 1.0, 0, 1)), 380, 1.2, T, scared=scared)
    if bite:
        gas_puffs(cv, -60, 300, T, a=1.0, n=8, spread=160, rise=500)
    if (T * 4) % 1 < 0.5 and bite:
        slabel(cv, 'ALARM!', 0, -760, 140, (255, 90, 80))
    elif not bite:
        slabel(cv, 'SNACK?', 0, -760, 120, YEL)
    return cv


def b6_drift(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    eyeball(cv, 0, -40, 330, T, gas=ease(np.clip(lt / 0.5, 0, 1)), acid=0.0)
    slabel(cv, 'INTO YOUR EYES', 0, -760, 100, GAS)
    return cv


def b7_acid(lt, dur, T):
    sx_, sy_ = shake(lt, 0.6, 14, 0.5)
    cv = Canvas(sx_, sy_, 1.15)
    a = ease(np.clip(lt / 0.5, 0, 1))
    eyeball(cv, 0, -40, 330, T, gas=0.5, acid=a, sting=ease(np.clip((lt - 0.5) / 0.6, 0, 1)))
    hook_text(cv, 'ACID!', lt, y=-760, size=150, pop_t=0.3, color=(220, 255, 60))
    return cv


def b8_flood(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    eyeball(cv, 0, -40, 330, T, acid=0.6 * (1 - ease(np.clip(lt / dur, 0, 1))), sting=0.8, flood=ease(np.clip(lt / 0.5, 0, 1)))
    slabel(cv, 'FLOODGATES OPEN', 0, -760, 96, (127, 208, 255))
    return cv


def b9_chill(lt, dur, T):
    cv = Canvas(-40, GY - 600, 1.35)
    cry = 1.0 - 0.8 * ease(np.clip((lt - 1.0) / 1.2, 0, 1))
    chopper(cv, lt, T, cry=cry, chill=True)
    sbadge(cv, 'CHILL IT FIRST', -760, (127, 208, 255))
    return cv


def b10_fan(lt, dur, T):
    cv = Canvas(40, GY - 600, 1.2)
    chopper(cv, lt, T, cry=0.15, fan=1.0)
    sbadge(cv, 'USE A FAN', -760, GRN)
    return cv


BEATS = [b0_hook, b1_cells, b2_smash, b3_enzymes, b4_gas, b5_alarm, b6_drift, b7_acid, b8_flood, b9_chill, b10_fan]

if __name__ == '__main__':
    run(BEATS)
