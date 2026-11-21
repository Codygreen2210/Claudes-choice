#!/usr/bin/env python3
"""The city isn't really there (GTA 6 was YouTube's top search, Nov 20-21 2026: 'gta 6 gameplay no commentary').
How big open-world games fake a giant city: only nearby chunks loaded (streaming), nothing outside the camera's view drawn
(frustum culling), blocky far copies swapped for detailed ones up close (level of detail), buildings hidden behind others
skipped (occlusion culling), all redone up to 60 times a second, and pop-in when it runs late. Payoff: the city only exists
where you look. Nothing here is Rockstar's: a generic top-down neon city of our own; no game art, logos or claims about
GTA 6's engine internals (every big 3D game does these).
Opens on a car racing through the city at night, buildings behind it melting to ghost outlines.
Facts: vidIQ YouTube Trends (top rising searches, all GTA 6). Epic Games, 'Visibility and Occlusion Culling in Unreal Engine'
(frustum culling removes objects outside the camera's view; occlusion culling hides objects blocked by others; distance
culling; pop-in when the camera moves fast). Meta Developers, 'Open World Games and Asset Streaming' (only nearby parts in
memory; far things lower fidelity or not loaded; LOD swaps by distance). GamesRadar, 'The secret technical tricks...' (culling
= 'only rendering what the player can see'; LOD; 'pop'). Engadget (GTA 6 is 212GB)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

DIVE = {}
NIGHT = ('#141a3a', '#04060f')
ROAD = ramp('#1c2030', '#10121c', '#2a3048')
ROOFS = ['#ff6ab0', '#5ad8ff', '#ffd05a', '#9a7aff', '#5aff9a', '#ff8a5a']
GHOST = '#5ad8ff'
CARC = ramp('#ff3a5a', '#b01a30', '#ff8aa0')
CONE = '#fff4c0'

# ---------------------------------------------------------------- the city (top-down)
BLK = 260                                                                     # block pitch
_r = np.random.default_rng(21)
CITY = []                                                                     # (x, y, half-size, height, colour, id)
for gx in range(-5, 6):
    for gy in range(-8, 9):
        for q in range(2 if _r.random() < 0.5 else 1):
            hs = _r.uniform(50, 85) if q == 0 else _r.uniform(30, 45)
            ox = _r.uniform(-30, 30) if q == 0 else _r.uniform(-40, 40)
            CITY.append((gx * BLK + ox + (0 if q == 0 else 60), gy * BLK + _r.uniform(-20, 20) + (0 if q == 0 else 55), hs,
                         _r.uniform(0.4, 1.0), ROOFS[int(_r.integers(len(ROOFS)))], len(CITY)))


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def in_cone(px, py, cx, cy, ang, half=np.radians(38), rng=900):
    dx, dy = px - cx, py - cy
    d = np.hypot(dx, dy)
    if d > rng:
        return 0.0
    if d < 90:
        return 1.0
    a = np.arctan2(dy, dx) - ang
    a = (a + np.pi) % (2 * np.pi) - np.pi
    return float(np.clip((half - abs(a)) / np.radians(8), 0, 1))


def streets(cv, glow=1.0):
    cv.background(*NIGHT, vignette=0.4)
    for g in range(-6, 7):
        x = g * BLK + BLK / 2
        box(cv, x, 0, 34, 2600, ROAD, r=0, ow=0, shadow=0)
        box(cv, 0, x, 2600, 34, ROAD, r=0, ow=0, shadow=0)
    for g in range(-6, 7):                                                    # faint neon lane lines
        x = g * BLK + BLK / 2
        line(cv, [(x, -2600), (x, 2600)], 3, flat(hexc('#3a4a8a')), a=0.6 * glow)
        line(cv, [(-2600, x), (2600, x)], 3, flat(hexc('#3a4a8a')), a=0.6 * glow)


def building(cv, x, y, hs, h, col, k=1.0, detail=1.0):
    """roof seen from above, a little 3D lean (south face), shadow; k fades it in (0 = gone)"""
    if k <= 0.01:
        return
    lean = 26 * h
    box(cv, x + 18, y + 18, hs, hs, ramp('#000000'), r=10, ow=0, shadow=0, alpha=0.35 * k)                 # shadow
    face = [(x - hs, y + hs - lean), (x + hs, y + hs - lean), (x + hs, y + hs), (x - hs, y + hs)]
    cv.shape(poly(face), pbox(face, 6), ramp(col, col, col), ow=3, shadow=0, alpha=0.55 * k)
    box(cv, x, y - lean / 2, hs, hs - 0.0, ramp(col, col, '#ffffff'), r=10, ow=4, alpha=k)
    if detail > 0.3:
        box(cv, x - hs * 0.35, y - lean / 2 - hs * 0.35, hs * 0.25, hs * 0.25, ramp('#ffffff'), r=4, ow=2, alpha=0.5 * k * detail)
        for j in range(3):
            dot(cv, x + hs * (-0.5 + 0.5 * j), y - lean / 2 + hs * 0.55, 6, flat(hexc('#fff4c0')), a=0.9 * k * detail)
    cv.glow(rbox(x, y - lean / 2, hs, hs, 10), (x - hs - 60, y - hs - 60, x + hs + 60, y + hs + 60), col, 30, 0.35 * k)


def ghost(cv, x, y, hs, a=0.6):
    pts = [(x - hs, y - hs), (x + hs, y - hs), (x + hs, y + hs), (x - hs, y + hs), (x - hs, y - hs)]
    for i in range(4):                                                        # dashed outline
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for t in np.linspace(0, 1, 6)[:-1]:
            line(cv, [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), (x0 + (x1 - x0) * (t + 0.1), y0 + (y1 - y0) * (t + 0.1))], 4, flat(hexc(GHOST)), a=a)


def car(cv, x, y, ang, s=1.0):
    c, s_ = np.cos(ang), np.sin(ang)
    R = lambda px, py: (x + (px * c - py * s_) * s, y + (px * s_ + py * c) * s)
    body_ = [R(-55, -28), R(55, -28), R(65, 0), R(55, 28), R(-55, 28)]
    cv.shape(poly(body_), pbox(body_, 8), CARC, ow=4)
    win = [R(-10, -20), R(25, -20), R(25, 20), R(-10, 20)]
    cv.shape(poly(win), pbox(win, 6), ramp('#1a2a4a'), ow=2, shadow=0)
    for sd in (-1, 1):
        hx, hy = R(64, sd * 16)
        dot(cv, hx, hy, 7, flat(hexc('#fff8e0')))


def cone(cv, x, y, ang, half=np.radians(38), rng=900, a=1.0):
    pts = [(x, y)] + [(x + rng * np.cos(ang + t), y + rng * np.sin(ang + t)) for t in np.linspace(-half, half, 16)]
    cv.shape(poly(pts), pbox(pts, 6), ramp(CONE), ow=0, shadow=0, alpha=0.16 * a)
    for t in (-half, half):
        line(cv, [(x, y), (x + rng * np.cos(ang + t), y + rng * np.sin(ang + t))], 5, flat(hexc(CONE)), a=0.55 * a)


def city_view(cv, cx, cy, ang, T, cull=1.0, ghosts=True, cone_a=1.0, rng=900):
    """draw the city: in the cone at full, outside it fading to ghosts by `cull`"""
    streets(cv)
    vx0, vx1 = cv.cx - 560 / cv.zoom - 120, cv.cx + 560 / cv.zoom + 120
    vy0, vy1 = cv.cy - 960 / cv.zoom - 120, cv.cy + 960 / cv.zoom + 120
    for (x, y, hs, h, col, i) in CITY:
        if not (vx0 < x < vx1 and vy0 < y < vy1):
            continue
        v = in_cone(x, y, cx, cy, ang, rng=rng)
        k = 1.0 - cull * (1.0 - v)
        if ghosts and k < 0.6:
            ghost(cv, x, y, hs, a=0.5 * (1 - k))
        building(cv, x, y, hs, h, col, k=k)
    cone(cv, cx, cy, ang, a=cone_a, rng=rng)


# ---------------------------------------------------------------- beats
def b0_race(lt, dur, T):
    """Frame one: the car already racing through the night city; everything behind it melting to ghosts."""
    t = lt + 2.0
    cy = 600 - t * 260; cx = 130 + 40 * np.sin(t * 0.6)
    ang = -np.pi / 2 + 0.06 * np.cos(t * 0.6)
    cv = Canvas(cx, cy + 150, 0.95)                                        # car above the captions, the dead city behind it
    city_view(cv, cx, cy, ang, T, cull=1.0)
    car(cv, cx, cy, ang, 1.4)
    hook_text(cv, 'NOT THERE', lt, y=-800, size=150, color=(90, 216, 255), pop_t=-10.0)   # up the whole time, so the loop's last frame matches frame one
    return cv


def b1_memory(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1a3a', '#06060f', vignette=0.4)
    box(cv, 0, 380, 330, 130, ramp('#f4f6fa', '#c8ccd4', '#ffffff'), r=40, ow=5)          # the console
    box(cv, 0, 380, 300, 14, ramp('#1a1e26'), r=6, ow=0, shadow=0)
    cv.glow(rbox(0, 380, 300, 14, 6), (-500, 200, 500, 560), '#5ab8ff', 50, 0.6)
    box(cv, 0, 70, 220, 140, ramp('#1a2a4a', '#0e1830', '#2a4070'), r=24, ow=5)          # its memory: a box that's too small
    label(cv, 'MEMORY', 0, 70, 70, (154, 208, 255), stroke=0)
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    rr = np.random.default_rng(3)
    for j in range(int(26 * k)):                                              # city blocks raining in and spilling over
        x = rr.uniform(-480, 480); y = -900 + (lt * 900 + j * 97) % 1100
        building(cv, x, y, rr.uniform(30, 55), 0.6, ROOFS[j % 6], k=1.0, detail=0.0)
    slabel(cv, '212 GB', 0, -560, 150, WHT)
    slabel(cv, "WON'T FIT", 0, -400, 100, (255, 90, 90), a=float(np.clip((lt - dur * 0.4) / 0.3, 0, 1)))
    return cv


def b2_chunks(lt, dur, T):
    cy = 300 - lt * 220; cx = 0
    cv = Canvas(0, cy - 200, 0.55)
    streets(cv)
    for (x, y, hs, h, col, i) in CITY:
        d = max(abs(x - cx), abs(y - cy))
        k = float(np.clip((720 - d) / 120, 0, 1))                             # only the chunk around the car is loaded
        if k < 1:
            ghost(cv, x, y, hs, a=0.25)
        building(cv, x, y, hs, h, col, k=k, detail=0.0)
    pts = [(cx - 720, cy - 720), (cx + 720, cy - 720), (cx + 720, cy + 720), (cx - 720, cy + 720), (cx - 720, cy - 720)]
    line(cv, pts, 12, flat(hexc('#5aff8a')), a=0.8)
    car(cv, cx, cy, -np.pi / 2, 1.8)
    slabel(cv, 'LOADED', 0, -820, 120, (90, 255, 140))
    slabel(cv, 'NOT LOADED', 0, 760, 90, (90, 216, 255))
    return cv


def b3_cone(lt, dur, T):
    cx, cy, ang = 130, 200, -np.pi / 2 + 0.25
    cv = Canvas(cx, cy - 150, 0.75)
    k = ease(np.clip((lt - 0.3) / (dur * 0.5), 0, 1))
    city_view(cv, cx, cy, ang, T, cull=k)
    car(cv, cx, cy, ang, 1.6)
    hook_text(cv, 'NOT DRAWN', lt, y=-800, size=150, color=(255, 90, 90), pop_t=dur * 0.5)
    return cv


def b4_turn(lt, dur, T):
    cx, cy = 130, 200
    k = ease(np.clip((lt - 0.2) / (dur * 0.55), 0, 1))
    ang = -np.pi / 2 + 0.25 + np.pi * k
    cv = Canvas(cx, cy, 0.75)
    city_view(cv, cx, cy, ang, T, cull=1.0)
    car(cv, cx, cy, ang, 1.6)
    if 0.2 < k < 0.95:                                                        # sparkles where the city rebuilds
        rr = np.random.default_rng(int(T * 20))
        for j in range(14):
            a = ang + rr.uniform(-0.6, 0.6); d = rr.uniform(150, 800)
            dot(cv, cx + d * np.cos(a), cy + d * np.sin(a), rr.uniform(6, 14), flat(hexc('#fff4c0')))
    sbadge(cv, 'TURN AROUND', -800, (255, 236, 80))
    return cv


def b5_lod(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a2a5a', '#0a0a1a', vignette=0.35)
    box(cv, 0, 700, 1400, 300, ROAD, r=0, ow=0, shadow=0)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))                                 # the building rushes toward you
    s = 0.35 + 0.95 * k
    x, base = 0, 520
    lvl = 0 if k < 0.35 else (1 if k < 0.7 else 2)
    col = '#ff6ab0'
    W, H = 220 * s, 520 * s
    if lvl == 0:                                                              # a blocky stand-in
        box(cv, x, base - H / 2, W, H / 2, ramp(col, '#a83a70', col), r=4, ow=5)
    else:
        box(cv, x, base - H / 2, W, H / 2, ramp(col, '#a83a70', '#ffb0d8'), r=16 * s, ow=5)
        box(cv, x, base - H - 30 * s, W * 0.5, 30 * s, ramp(col), r=8 * s, ow=4)
        rows, cols = (4, 3) if lvl == 1 else (8, 5)
        for r_ in range(rows):
            for c in range(cols):
                wx = x - W * 0.75 + c * (1.5 * W / max(cols - 1, 1))
                wy = base - H + (r_ + 0.5) * (H / rows)
                box(cv, wx, wy, W * 0.08, H * 0.05, ramp('#fff4c0' if (r_ + c) % 3 else '#2a3a6a'), r=4, ow=2)
        if lvl == 2:
            line(cv, [(x - W, base - H * 0.98), (x + W, base - H * 0.98)], 10 * s, flat(hexc('#5ad8ff')))
            cv.glow(rbox(x, base - H * 0.98, W, 5 * s, 4), (x - W - 100, base - H - 100, x + W + 100, base - H + 100), '#5ad8ff', 40, 0.7)
    tag = ['FAR: BLOCKY', 'CLOSER: BETTER', 'CLOSE: DETAILED'][lvl]
    slabel(cv, tag, 0, -820, 100, (255, 236, 80))
    return cv


def b6_hidden(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a2a5a', '#06080f', vignette=0.35)
    box(cv, 0, 760, 1400, 300, ROAD, r=0, ow=0, shadow=0)
    k = float(np.clip((lt - dur * 0.3) / 0.4, 0, 1))
    for j, (bx, h) in enumerate(((-260, 900), (-60, 1000), (180, 850), (380, 950))):   # the ones hidden behind
        if k < 1:
            box(cv, bx, 620 - h / 2, 90, h / 2, ramp(ROOFS[j + 1]), r=10, ow=4, alpha=1 - k)
        pts = [(bx - 90, 620 - h), (bx + 90, 620 - h), (bx + 90, 620), (bx - 90, 620), (bx - 90, 620 - h)]
        for i in range(4):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            for t in np.linspace(0, 1, 7)[:-1]:
                line(cv, [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), (x0 + (x1 - x0) * (t + 0.08), y0 + (y1 - y0) * (t + 0.08))], 5, flat(hexc(GHOST)), a=0.7 * k)
    box(cv, 0, 620 - 330, 420, 330, ramp('#ff6ab0', '#a83a70', '#ffb0d8'), r=20, ow=6)      # the big one in front
    for r_ in range(6):
        for c in range(5):
            box(cv, -320 + c * 160, 90 + r_ * 85, 40, 22, ramp('#fff4c0' if (r_ * c) % 4 else '#2a3a6a'), r=4, ow=2)
    eye_x, eye_y = 0, 840
    cv.shape(ellipse(eye_x, eye_y, 90, 50), (eye_x - 100, eye_y - 60, eye_x + 100, eye_y + 60), WHITE, ow=4)
    disc(cv, eye_x, eye_y, 30, INKC, ow=0)
    hook_text(cv, 'SKIPPED', lt, y=-800, size=160, color=(90, 216, 255), pop_t=dur * 0.35)
    return cv


def b7_sixty(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1a4a', '#0a0614', vignette=0.4)
    n = int(lt * 60)
    for j in range(6):                                                        # a stack of frames flipping past
        idx = n - j
        if idx < 0:
            continue
        a = 1.0 - j * 0.16
        off = j * 26
        box(cv, off, -40 + off, 280, 380, ramp('#1a2040', '#0a1020', '#2a3460'), r=26, ow=5, alpha=a)
        label(cv, str(idx % 60 + 1), off, -40 + off, 220, (154, 208, 255), a=a)
    slabel(cv, '60 TIMES', 0, -760, 140, (255, 236, 80))
    slabel(cv, 'EVERY SECOND', 0, -630, 90, WHT)
    return cv


def b8_popin(lt, dur, T):
    cx, cy, ang = 0, 260 - lt * 160, -np.pi / 2
    cv = Canvas(0, cy - 260, 0.8)
    streets(cv)
    for (x, y, hs, h, col, i) in CITY:
        v = in_cone(x, y, cx, cy, ang, rng=900)
        late = (i % 4 == 0)                                                   # some arrive a beat late: pop
        if late and v > 0:
            pk = float(np.clip((lt * 3 + (i % 7) * 0.2) % 1.6 - 0.6, 0, 1))
            s_ = 1.0 + 0.4 * np.sin(np.pi * pk) if pk < 1 else 1.0
            building(cv, x, y, hs * s_, h, col, k=v * (1.0 if pk > 0 else 0.0))
        else:
            building(cv, x, y, hs, h, col, k=v)
    cone(cv, cx, cy, ang)
    car(cv, cx, cy, ang, 1.5)
    hook_text(cv, 'POP IN!', lt, y=-800, size=160, color=(255, 236, 80), pop_t=dur * 0.45)
    return cv


def b9_only(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cx, cy, ang = 0, 200, -np.pi / 2
    cv = Canvas(0, cy - 200 * (1 - k), 0.85 - 0.3 * k)                         # pull way back: a lit sliver in the dark
    cv.background('#020308', '#000000', vignette=0.5)
    for (x, y, hs, h, col, i) in CITY:
        v = in_cone(x, y, cx, cy, ang, rng=900)
        if v > 0:
            building(cv, x, y, hs, h, col, k=v)
        elif k > 0.3:
            dot(cv, x, y, 8, flat(hexc('#1a2a4a')), a=0.6)
    cone(cv, cx, cy, ang)
    car(cv, cx, cy, ang, 1.4)
    hook_text(cv, 'ONLY WHERE YOU LOOK', lt, y=-800, size=76, color=(255, 236, 80), pop_t=dur * 0.45)
    return cv


BEATS = [b0_race, b1_memory, b2_chunks, b3_cone, b4_turn, b5_lod, b6_hidden, b7_sixty, b8_popin, b9_only]

if __name__ == '__main__':
    run(BEATS)
