#!/usr/bin/env python3
"""What's going viral on YouTube right now (week of Oct 19, 2026). Toon engine v3, timed to the narration.

    python3 studio/toon/shorts/viral.py times.json viral.json out.mp4 [--still T out.png] [--sheet]

Opens mid-action: the globe is already spinning and pins are popping, the TV is blasting light.
The last beat is the opening running up to its own start, so the last words "...because right now"
run into "a video game trailer just took over YouTube". Nothing branded is drawn (no logos, no
game characters, no real people) - generic TV, phone, blocks and chart only.
Facts (checked Oct 19, 2026): TrendTube weekly global report (GTA VI launch trailer #1, trending in 105+
countries; Olivia Rodrigo "expectations" feat. Chappell Roan #2; MrBeast Gaming "$10,000 Every Day You
Survive In Minecraft" #3); GTA VI release Nov 19 (launch trailer five weeks before); hype.ad Entertainment
Oct 2026 (challenges #1, 393.2M views); Metricool 2026 (61%+ of organic views from the Shorts feed);
Tubefilter Top 50 week of 10/18/2026 (39 of 50 channels mostly Shorts).
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

OCEAN = ramp('#3d8fe0', '#24589a', '#8fc8ff')
LAND = ramp('#5fc95a', '#2f8a3a', '#a6f08a')
SCREEN = ramp('#1b1d26', '#0e0f15', '#2c2f3c')
CASH = ramp('#4fc26a', '#2a8044', '#9af0a8')
GOLD = ramp('#ffd23f', '#d09a10', '#fff08a')
GRASS = ramp('#5fbf4a', '#3a8a2c', '#9ae37a')
DIRT = ramp('#9a6a3a', '#6a4422', '#c08a52')
LEAF = ramp('#2f9a4a', '#1e6a32', '#5fd07a')
TRUNK = ramp('#8a5a32', '#5a3a1e', '#b07a48')
GREY = ramp('#9aa3ad', '#6a737d', '#c9d0d8')
REDR = ramp('#e2483d', '#a82a26', '#ff8070')
PURP = ramp('#8a5ad8', '#5a35a0', '#c09aff')


def clip01(x):
    return float(np.clip(x, 0, 1))


def popk(lt, t0, d=0.25):
    """0 -> overshoot -> 1 scale for something popping in at t0."""
    k = clip01((lt - t0) / d)
    if k <= 0:
        return 0.0
    return ease(k) + 0.22 * np.sin(np.pi * k) * (1 - k) * 2


# ------------------------------------------------------------------ props
def globe(cv, x, y, r, T, pins=0, seed=3):
    disc(cv, x, y, r, OCEAN, ow=6)
    rim = circle(x, y, r * 0.985)
    off = (T * 140) % 1400
    blobs = []
    for k in (-1, 0, 1):
        bx = x - off + k * 1400
        for dx, dy, rx, ry, a in ((-300, -160, 190, 130, 20), (-180, 120, 120, 200, -10), (180, -60, 230, 150, 5),
                                  (420, 200, 110, 90, 30), (640, -220, 160, 120, -20), (900, 80, 210, 140, 15)):
            blobs.append(rotell(bx + dx * r / 330, y + dy * r / 330, rx * r / 330, ry * r / 330, a))
    land = inter(rim, union(*blobs))
    cv.shape(land, (x - r, y - r, x + r, y + r), LAND, ow=3, shadow=0)
    cv.shape(subtract(circle(x, y, r * 1.0), circle(x + r * 0.18, y - r * 0.12, r * 0.98)), (x - r, y - r, x + r, y + r),
             ramp('#000000'), ow=0, shadow=0, alpha=0.18, flat=True)            # night side shading
    rng = np.random.default_rng(seed)
    for i in range(int(pins)):
        a = rng.uniform(0, 2 * np.pi); rr = r * np.sqrt(rng.uniform(0.02, 0.8))
        px, py = x + np.cos(a) * rr, y + np.sin(a) * rr
        k = clip01(pins - i)                                         # the newest pin is still popping
        s = ease(k) + 0.3 * np.sin(np.pi * k) * (1 - k)
        if s <= 0.01:
            continue
        line(cv, [(px, py), (px, py - 46 * s)], 7, flat(hexc('#2b2f38')))
        disc(cv, px, py - 50 * s, 17 * s, REDR, ow=3, shadow=0.15)


def palm(cv, x, y, h, T, s=1.0, sdf_clip=None):
    sway = 10 * np.sin(T * 1.8 + x * 0.01)
    pts = [(x + sway * u * u, y - h * u) for u in np.linspace(0, 1, 6)]
    line(cv, pts, 9 * s, flat(hexc('#1a1022')))
    tx, ty = pts[-1]
    for k in range(6):
        a = -np.pi / 2 + (k - 2.5) * 0.55 + 0.05 * np.sin(T * 2 + k)
        L = 70 * s
        lp = [(tx + np.cos(a) * L * u, ty + np.sin(a) * L * u + 28 * s * u * u) for u in np.linspace(0, 1, 5)]
        line(cv, lp, 8 * s, flat(hexc('#1a1022')))


def tv(cv, x, y, hw, hh, T, lt, shine=1.0, car=True):
    """Big TV playing a sunset-city trailer: sun sinking, palms swaying, a car racing across."""
    if shine > 0:
        cv.glow(rbox(x, y, hw, hh, 30), (x - hw, y - hh, x + hw, y + hh), '#ff9a4a', 60, 0.5 * shine)
    box(cv, x, y, hw + 34, hh + 34, DARK, r=40)
    box(cv, x, y + hh + 70, 40, 40, DARK, r=10)
    box(cv, x, y + hh + 110, 160, 16, DARK, r=10)
    scr = rbox(x, y, hw, hh, 18)
    cv.shape(scr, (x - hw, y - hh, x + hw, y + hh), ramp('#ff7a5a', '#8a3aa0', '#ffc07a'), ow=3, shadow=0, flat=True)
    # sky bands
    for j, c in enumerate(('#3a1f5e', '#7a2f7a', '#d4507a', '#ff8a5a')):
        yy = y - hh + j * hh * 0.42
        cv.shape(inter(scr, rbox(x, yy + hh * 0.21, hw, hh * 0.21, 0)), (x - hw, yy, x + hw, yy + hh * 0.42),
                 flat(hexc(c)), ow=0, shadow=0, flat=True)
    sy = y + hh * 0.05 + 20 * np.sin(T * 0.4)
    cv.glow(inter(scr, circle(x + hw * 0.1, sy, hh * 0.32)), (x - hw, y - hh, x + hw, y + hh), '#ffd27a', 30, 0.6)
    cv.shape(inter(scr, circle(x + hw * 0.1, sy, hh * 0.32)), (x - hw, y - hh, x + hw, y + hh), ramp('#ffd23f', '#ff9a2a', '#fff2b0'),
             ow=0, shadow=0)
    # skyline + road
    for j, (bx, bw, bh) in enumerate(((-0.8, 0.12, 0.55), (-0.6, 0.09, 0.8), (-0.42, 0.11, 0.45), (0.45, 0.1, 0.7), (0.65, 0.13, 0.5), (0.85, 0.08, 0.9))):
        X0 = x + bx * hw; top = y + hh * 0.45 - bh * hh
        cv.shape(inter(scr, rbox(X0, (top + y + hh * 0.45) / 2, bw * hw, (y + hh * 0.45 - top) / 2, 4)),
                 (X0 - bw * hw, top, X0 + bw * hw, y + hh * 0.45), flat(hexc('#2a1838')), ow=0, shadow=0, flat=True)
    cv.shape(inter(scr, rbox(x, y + hh * 0.72, hw, hh * 0.28, 0)), (x - hw, y + hh * 0.44, x + hw, y + hh), flat(hexc('#1a1022')),
             ow=0, shadow=0, flat=True)
    for k in range(6):                                                   # road dashes rushing past
        dx = ((k * 0.4 - (T * 1.6) % 0.4 * 1) % 2.4 - 1.2) * hw
        cv.shape(inter(scr, rbox(x + dx, y + hh * 0.74, hw * 0.06, 5, 3)), (x - hw, y + hh * 0.7, x + hw, y + hh * 0.8),
                 flat(hexc('#ffd27a')), ow=0, shadow=0, flat=True)
    for px in (-0.72, -0.3, 0.32, 0.7):
        palm(cv, x + px * hw, y + hh * 0.46, hh * 0.55, T, s=hh / 300)
    if car:                                                               # car zooms across, wraps around
        cx = x + ((T * 0.55) % 1.6 - 0.8) * hw * 1.5
        cy = y + hh * 0.66
        body = union(rbox(cx, cy, hw * 0.16, hh * 0.06, 10), rbox(cx - hw * 0.02, cy - hh * 0.08, hw * 0.08, hh * 0.05, 12))
        cv.shape(inter(scr, body), (cx - hw * 0.2, cy - hh * 0.15, cx + hw * 0.2, cy + hh * 0.08), ramp('#ff4a8a', '#b02a5a', '#ff9ac0'), ow=3, shadow=0)
        for wx in (-0.1, 0.1):
            cv.shape(inter(scr, circle(cx + wx * hw, cy + hh * 0.06, hh * 0.04)), (cx - hw * 0.2, cy, cx + hw * 0.2, cy + hh * 0.12),
                     flat(hexc('#111111')), ow=0, shadow=0, flat=True)
    cv.shape(subtract(rbox(x, y, hw, hh, 18), rbox(x + 30, y + 30, hw, hh, 18)), (x - hw, y - hh, x + hw, y + hh),
             ramp('#ffffff'), ow=0, shadow=0, alpha=0.12, flat=True)          # glass glare


def phone(cv, x, y, s=1.0):
    box(cv, x, y, 230 * s, 450 * s, DARK, r=60 * s)
    box(cv, x, y, 205 * s, 420 * s, ramp('#f4f6f8', '#c8d0d8', '#ffffff'), r=42 * s, ow=0, shadow=0)
    return rbox(x, y, 205 * s, 420 * s, 42 * s)


def note(cv, x, y, s=1.0, col=None):
    col = col or PURP
    disc(cv, x - 40 * s, y + 90 * s, 46 * s, col, ow=4)
    disc(cv, x + 90 * s, y + 60 * s, 46 * s, col, ow=4)
    line(cv, [(x + 2 * s, y + 90 * s), (x + 2 * s, y - 110 * s)], 14 * s, col, ow=3, flat=False)
    line(cv, [(x + 132 * s, y + 60 * s), (x + 132 * s, y - 140 * s)], 14 * s, col, ow=3, flat=False)
    line(cv, [(x + 2 * s, y - 110 * s), (x + 132 * s, y - 140 * s)], 30 * s, col, ow=3, flat=False)


def cash(cv, x, y, n, lt=0.0, last_t=0.0):
    for i in range(n):
        dy = 0.0
        if i == n - 1:                                                    # newest bundle drops in
            k = clip01((lt - last_t) / 0.3)
            dy = -260 * (1 - k) ** 2
        yy = y - i * 44 + dy
        box(cv, x, yy, 120, 22, CASH, r=8, ow=3.5)
        box(cv, x, yy, 30, 22, ramp('#f4f1ea'), r=2, ow=0, shadow=0)


def blocks_ground(cv, y, T, scroll=0.0):
    S = 120
    off = scroll % S
    for i in range(-6, 7):
        bx = i * S - off
        box(cv, bx, y + S / 2, S / 2 - 2, S / 2 - 2, GRASS, r=4, ow=3)
        for j in (1, 2, 3, 4):
            box(cv, bx, y + S / 2 + j * S, S / 2 - 2, S / 2 - 2, DIRT, r=4, ow=3, shadow=0)


def block_tree(cv, x, y):
    S = 60
    for j in range(3):
        box(cv, x, y - S / 2 - j * S, S / 2 - 2, S / 2 - 2, TRUNK, r=3, ow=3, shadow=0)
    for dx, dy in ((-1, 0), (0, 0), (1, 0), (-1, -1), (0, -1), (1, -1), (0, -2)):
        box(cv, x + dx * S, y - 3.5 * S + dy * S, S / 2 - 2, S / 2 - 2, LEAF, r=3, ow=3, shadow=0)


def runner(cv, x, y, s, T, face='happy', shirt=None):
    """The everyman running: bob, pumping arms."""
    ph = T * 9
    bob = abs(np.sin(ph)) * 18 * s
    a1 = 40 * np.sin(ph); a2 = -40 * np.sin(ph)
    guy(cv, x, y - bob, s, face=face, arms=((60 + a1, 40), (60 + a2, 40)), shirt=shirt or ORANGE)


def play_tile(cv, x, y, s, on):
    col = REDR if on > 0.5 else GREY
    sc = s * (1 + 0.25 * np.sin(np.pi * clip01(on)) * (1 - clip01(on)) * 2 if 0 < on < 1 else 1)
    box(cv, x, y, 44 * sc, 32 * sc, col, r=12 * sc, ow=3)
    tri = poly([(x - 12 * sc, y - 16 * sc), (x - 12 * sc, y + 16 * sc), (x + 16 * sc, y)])
    cv.shape(tri, (x - 14 * sc, y - 18 * sc, x + 18 * sc, y + 18 * sc), ramp('#ffffff'), ow=0, shadow=0, flat=True)


def person_icon(cv, x, y, s, on):
    col = YELLOW if on > 0.5 else GREY
    disc(cv, x, y - 46 * s, 26 * s, col, ow=3)
    cv.shape(rbox(x, y + 18 * s, 40 * s, 32 * s, 26 * s), (x - 40 * s, y - 14 * s, x + 40 * s, y + 50 * s), col, ow=3)


# ------------------------------------------------------------------ beats
def b0_hook(lt, dur, T):
    """Frame one: globe spinning, pins already popping fast, TV blasting the trailer in front."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1f5e', '#ff8a5a', vignette=0.25)
    spin = 1 + 0.3 * np.sin(T * 2)
    for k in range(12):                                                   # light rays turning behind the globe
        a = k * np.pi / 6 + T * 0.6
        tip = [(0, -390), (np.cos(a - 0.08) * 1400, -390 + np.sin(a - 0.08) * 1400), (np.cos(a + 0.08) * 1400, -390 + np.sin(a + 0.08) * 1400)]
        cv.shape(poly(tip), pbox(tip), flat(hexc('#ffe7a0')), ow=0, shadow=0, flat=True, alpha=0.12 * spin)
    pins = np.clip((lt + 3.2) * 9.0, 0, 48)
    globe(cv, 0, -390, 270, T, pins=pins)
    tv(cv, 0, 60, 250, 140, T, lt, shine=1.0)
    n = int(np.clip((lt + 3.2) * 24, 0, 105))
    label(cv, f'{n} COUNTRIES' if n < 100 else '100+ COUNTRIES', 0, -710, 64, (255, 236, 80))
    if lt >= 0:
        hook_text(cv, 'GOING VIRAL', lt, y=-830, size=130, color=(255, 255, 255))
    return cv


def b1_trailer(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    cv.background('#2a1f5e', '#5a2f7a', vignette=0.3)
    push = 1 + 0.12 * ease(clip01(lt / dur))
    tv(cv, 0, -260, 420 * push, 260 * push, T, lt, shine=1.2)
    for j, xx in enumerate((-300, 0, 300)):                               # three fans leaning in, backs to us
        lean = 8 * np.sin(T * 2 + j)
        guy(cv, xx + lean, 520, 0.55, face='calm', shirt=(SHIRT, ORANGE, BLUE)[j], arms=((70, 70), (70, 70)), legs=False)
    label(cv, 'LAUNCH TRAILER', 0, -640, 66, (255, 236, 80))
    c = popk(lt, dur * 0.42)                                              # the calendar pops in on "November 19th"
    if c > 0:
        cx, cy = 330, 70
        box(cv, cx, cy, 120 * c, 120 * c, ramp('#f4f1ea'), r=16 * c)
        box(cv, cx, cy - 85 * c, 120 * c, 36 * c, REDR, r=14 * c, ow=0)
        label(cv, 'NOV', cx, cy - 80 * c, 40 * c, (255, 255, 255))
        label(cv, '19', cx, cy + 30 * c, 110 * c, (40, 30, 50))
        if lt - dur * 0.42 < 0.6:                                        # pages flipping off
            for q in range(3):
                u = clip01((lt - dur * 0.42 - q * 0.12) / 0.4)
                if 0 < u < 1:
                    box(cv, cx + 200 * u, cy - 200 * u + 300 * u * u, 100, 100, ramp('#f4f1ea'), r=12, alpha=1 - u)
    hook_text(cv, 'GTA 6', lt, y=-780, size=150, pop_t=0.4, color=(255, 236, 80))
    return cv


def b2_song(lt, dur, T):
    cv = Canvas(0, -80, 1.0)
    sky_bg(cv)
    for k in range(3):                                                     # sound rings pulsing out
        ph = (T * 0.9 + k / 3) % 1
        cv.shape(subtract(circle(-250, -560, 120 + 260 * ph), circle(-250, -560, 108 + 260 * ph)), (-700, -1000, 200, -100),
                 ramp('#ffffff'), ow=0, shadow=0, flat=True, alpha=0.5 * (1 - ph))
    bob = 30 * np.sin(T * 4)
    note(cv, -270, -580 + bob, 1.0 + 0.06 * np.sin(T * 8))
    scr = phone(cv, 190, -160, 0.95)
    rows = ['GAME', 'SONG', 'VLOG', 'PRANK', 'COOK', 'NEWS']
    climb = ease(clip01((lt - dur * 0.45) / (dur * 0.35)))                 # SONG climbs from #5 to #2
    pos = {'GAME': 0, 'VLOG': 1, 'PRANK': 2, 'COOK': 3, 'SONG': 4, 'NEWS': 5}
    sp = 4 - 3 * climb
    for name in sorted(pos, key=lambda n_: n_ == 'SONG'):                  # SONG drawn last, lifted off the list
        p = pos[name]
        hl = name == 'SONG'
        if hl:
            p = sp
        elif 1 <= p <= 3:
            p = p + clip01(p + 1 - sp)                                      # the ones it passes slide down one
        yy = -480 + p * 120
        lift = 40 * np.sin(np.pi * climb) if hl else 0
        box(cv, 190 - lift, yy, 180, 50, PURP if hl else ramp('#e3e8ee', '#b8c0c8', '#ffffff'), r=18, ow=3, shadow=0.3 if hl else 0)
        label(cv, f'#{int(round(p)) + 1}', 60 - lift, yy + 6, 44, (255, 255, 255) if hl else (60, 66, 80))
        label(cv, name, 220 - lift, yy + 6, 44, (255, 255, 255) if hl else (60, 66, 80))
    if climb > 0.05:
        arrows(cv, [((420, 60), (420, -330))], col=(120, 255, 140), w=16)
    hook_text(cv, 'TRENDING', lt, y=-830, size=120, pop_t=0.3, color=(255, 255, 255))
    return cv


def b3_survive(lt, dur, T):
    days = int(lt / (dur / 5)) + 1
    ph = (lt / (dur / 5)) % 1
    # quick day / night each "day": dusk ramps in late, dawn ramps out, never a hard flip (no strobe)
    night = 0.7 * ease(np.clip((ph - 0.62) / 0.16, 0, 1)) * (1 - ease(np.clip((ph - 0.9) / 0.1, 0, 1)))
    cv = Canvas(0, -120, 1.0)
    top = mixc(hexc('#3fa2ee'), hexc('#121a3a'), night); bot = mixc(hexc('#bfe6ff'), hexc('#3a3f7a'), night)
    cv.img[:] = mixc(top, bot, np.linspace(0, 1, H, dtype=np.float32)[:, None, None])
    a = np.pi * (1 - np.clip(ph / 0.8, 0, 1))                              # sun arcs across, then sets
    if ph < 0.8:
        disc(cv, np.cos(a) * 480, -380 - np.sin(a) * 420, 70, YELLOW, ow=0, shadow=0)
    if night > 0.05:
        disc(cv, 300, -560, 50, ramp('#e8eef8'), ow=0, shadow=0, alpha=night / 0.7)
    scroll = lt * 260
    for tx in (-200, 500, 1200):
        block_tree(cv, ((tx - scroll * 0.6) % 1500) - 700, 120)
    blocks_ground(cv, 120, T, scroll)
    runner(cv, -160, 120, 0.55, T)
    last_t = (days - 1) * dur / 5
    cash(cv, 260, 90, days, lt, last_t)
    k = popk(lt, last_t, 0.2)
    label(cv, '+$10,000', 260, 60 - days * 44 - 80, 60 * max(k, 0.01), (120, 255, 140), a=min(1, k))
    badge(cv, f'DAY {days}', y=-640, col=(255, 236, 80))
    return cv


def b4_challenges(lt, dur, T):
    cv = Canvas(0, -100, 1.0)
    sky_bg(cv)
    data = (('CHALLENGE', 393, YELLOW), ('CONTEST', 240, BLUE), ('ADVENTURE', 168, GREEN), ('COMEDY', 66, PINK))
    base = 60
    g = ease(clip01(lt / (dur * 0.45)))
    tops = []
    for i, (nm, v, col) in enumerate(data):
        x = -360 + i * 240
        h = 540 * v / 393 * g
        if h > 4:
            box(cv, x, base - h / 2, 90, h / 2, col, r=14, ow=4)
        label(cv, nm, x, base + 50, 32, (255, 255, 255))
        if h > 120:
            label(cv, f'{v}M', x, base - h / 2 + 12, 40, (40, 30, 50))
        tops.append((x, base - h))
    box(cv, 0, base + 8, 520, 10, DARK, r=4, ow=0)
    j = clip01((lt - dur * 0.5) / 0.5)                                     # the everyman jumps onto the top bar
    if j > 0:
        x0, y0 = tops[0]
        sx, sy = -500, base
        px = sx + (x0 - sx) * ease(j)
        py = sy + (y0 - sy) * j - 380 * np.sin(np.pi * j)
        cheer = j >= 1
        guy(cv, px, py, 0.34, face='happy', shirt=ORANGE,
            arms=((150, 160), (150, 160)) if cheer else ((80, 40), (80, 40)))
        if cheer:
            u = popk(lt, dur * 0.5 + 0.5, 0.25)                             # trophy up
            tx, ty = px + 75, py - 390
            cv.shape(union(subtract(circle(tx, ty, 46 * u), rbox(tx, ty - 40 * u, 60 * u, 40 * u, 0)), rbox(tx, ty + 60 * u, 12 * u, 24 * u, 4),
                           rbox(tx, ty + 88 * u, 36 * u, 10 * u, 4)), (tx - 60, ty - 60, tx + 60, ty + 110), GOLD, ow=3)
            rng = np.random.default_rng(4)
            for q in range(26):                                          # confetti
                age = lt - dur * 0.5 - 0.5 - q * 0.02
                if age <= 0:
                    continue
                vx, vy = rng.uniform(-420, 420), rng.uniform(-900, -400)
                cx_, cy_ = x0 + vx * age, y0 - 300 + vy * age + 900 * age * age
                c = ('#ffd23f', '#ff5a8a', '#3fd0ff', '#7fe8a0')[q % 4]
                box(cv, cx_, cy_, 14, 8, flat(hexc(c)), r=3, ow=0, shadow=0, flat=True)
    hook_text(cv, '#1 THIS MONTH', lt, y=-840, size=110, pop_t=0.3, color=(255, 255, 255))
    return cv


def b5_shorts(lt, dur, T):
    cv = Canvas(0, -100, 1.0)
    sky_bg(cv)
    scr = phone(cv, -220, -200, 0.95)
    sw = (lt * 1.6) % 1                                                   # vertical videos swiping up inside the phone
    for q in range(3):
        yy = -200 + (q - sw) * 820 * 0.95
        col = (ORANGE, PURP, GREEN)[(q + int(lt * 1.6)) % 3]
        cv.shape(inter(scr, rbox(-220, yy, 190, 395, 30)), (-420, -620, -20, 220), col, ow=3, shadow=0)
        cv.shape(inter(scr, circle(-220, yy - 40, 60)), (-420, -620, -20, 220), ramp('#ffffff'), ow=0, shadow=0, alpha=0.8)
    th = 1 - abs(((lt * 1.6) % 1) - 0.5) * 2                              # the thumb flicking
    disc(cv, -100, 100 - 180 * th, 50, SKIN, ow=4)
    for i in range(10):                                                    # 6 out of 10 light up
        cx_, cy_ = 150 + (i % 2) * 170, -520 + (i // 2) * 160
        on = clip01((lt - 0.8 - i * 0.35) / 0.25) if i < 6 else 0.0
        person_icon(cv, cx_, cy_, 0.95, on)
    if lt > 0.8 + 5 * 0.35 + 0.2:
        hook_text(cv, '6 IN 10 VIEWS', lt, y=-840, size=110, pop_t=0.8 + 5 * 0.35 + 0.2, color=(255, 236, 80))
    return cv


def b6_channels(lt, dur, T):
    cv = Canvas(0, -100, 1.0)
    sky_bg(cv)
    n_on = int(np.clip((lt - 0.4) / 2.6 * 39, 0, 39))
    order = np.random.default_rng(9).permutation(50)
    on_set = set(order[:n_on].tolist())
    for i in range(50):
        x = -400 + (i % 5) * 200
        y = -620 + (i // 5) * 82
        t_on = 0.4 + (np.where(order == i)[0][0]) * 2.6 / 39
        on = clip01((lt - t_on) / 0.2) if i in on_set or (lt - t_on) > 0 and np.where(order == i)[0][0] < 39 else 0.0
        play_tile(cv, x, y, 0.95, on)
    label(cv, 'TOP 50 GROWING CHANNELS', 0, -700, 50, (255, 255, 255))
    k = popk(lt, 3.1)
    if k > 0:
        badge(cv, '39 OF 50', y=-820, col=(255, 236, 80), w=440)
    return cv


def b7_recipe(lt, dur, T):
    cv = Canvas(0, -100, 1.0)
    sky_bg(cv)
    t1, t2, t3 = dur * 0.30, dur * 0.48, dur * 0.62
    # 1. the reveal: a gift box, lid flies off, burst of light
    k1 = popk(lt, t1)
    if k1 > 0:
        x, y = -330, -260
        lid = clip01((lt - t1 - 0.25) / 0.35)
        if lid > 0:
            cv.glow(circle(x, y - 80, 60), (x - 100, y - 160, x + 100, y), '#fff2a0', 70, lid)
        box(cv, x, y, 110 * k1, 90 * k1, REDR, r=12)
        box(cv, x, y, 18 * k1, 90 * k1, GOLD, r=4, ow=0)
        box(cv, x - 40 * lid, y - 110 * k1 - 220 * lid + 300 * lid * lid, 125 * k1, 26 * k1, REDR, r=10)
        label(cv, 'REVEAL', x, y + 170, 52, (255, 255, 255))
    # 2. the goal: a target, a dart thunks in
    k2 = popk(lt, t2)
    if k2 > 0:
        x, y = 0, -540
        for r_, c in ((120, REDR), (86, ramp('#f4f1ea')), (52, REDR), (20, ramp('#f4f1ea'))):
            disc(cv, x, y, r_ * k2, c, ow=3, shadow=0.1 if r_ == 120 else 0)
        f = clip01((lt - t2 - 0.2) / 0.25)
        dx = x + 420 * (1 - f); dy = y - 160 * (1 - f)
        wob = 6 * np.sin((lt - t2 - 0.45) * 40) * np.exp(-max(lt - t2 - 0.45, 0) * 6) if f >= 1 else 0
        line(cv, [(dx, dy), (dx + 150, dy - 60 + wob)], 12, flat(hexc('#2b2f38')))
        cv.shape(poly([(dx + 140, dy - 56), (dx + 190, dy - 100), (dx + 170, dy - 50)]), (dx + 130, dy - 110, dx + 200, dy - 40), GOLD, ow=3)
        label(cv, 'GOAL', x, y + 180, 52, (255, 255, 255))
    # 3. a reason to keep watching: play button, bar filling
    k3 = popk(lt, t3)
    if k3 > 0:
        x, y = 330, -260
        box(cv, x, y, 120 * k3, 84 * k3, REDR, r=30 * k3)
        cv.shape(poly([(x - 30 * k3, y - 40 * k3), (x - 30 * k3, y + 40 * k3), (x + 44 * k3, y)]), (x - 40, y - 50, x + 50, y + 50),
                 ramp('#ffffff'), ow=0, shadow=0, flat=True)
        p = clip01((lt - t3 - 0.2) / 1.2)
        box(cv, x, y + 120, 130, 12, DARK, r=6, ow=0)
        if p > 0:
            box(cv, x - 130 + 130 * p, y + 120, 130 * p, 12, REDR, r=6, ow=0)
        label(cv, 'KEEP WATCHING', x, y + 190, 44, (255, 255, 255))
    hook_text(cv, 'THE RECIPE', lt, y=-840, size=120, pop_t=0.2, color=(255, 236, 80))
    return cv


BEATS = [b0_hook, b1_trailer, b2_song, b3_survive, b4_challenges, b5_shorts, b6_channels, b7_recipe]

if __name__ == '__main__':
    run(BEATS)
