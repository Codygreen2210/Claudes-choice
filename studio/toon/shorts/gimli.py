#!/usr/bin/env python3
"""The Gimli Glider (Air Canada 143, July 23 1983), toon engine v3.

    python3 studio/toon/shorts/gimli.py out.mp4 [--from 0 --to 80] [--still 12.3 out.png]

The script is a list of beats: (line, scene). Beat lengths come from the words
(about 2.7 words a second plus a breath) until a real voice gives word timings;
the last line runs straight back into the first, so the Short loops.
Facts: Wikipedia "Gimli Glider" (Transport Canada board of inquiry, 1985).
"""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import *          # noqa: F401,F403  (engine: Canvas, guy, shapes, text)
import common

for _f in ('/usr/share/fonts/opentype/inter/Inter-Black.otf', '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'):
    if os.path.exists(_f):
        common.FONT = _f
        break
FONTB = common.FONT

# ------------------------------------------------------------------ palette
SKY_T, SKY_B = '#3f8ad8', '#bfe3ff'
PLANE = ramp('#eef1f4', '#b9c1cb', '#ffffff')
TAIL = ramp('#d8322b', '#9a1d1a', '#ff6a5c')
DARKG = ramp('#38404c', '#22272f', '#5a6472')
GREY = ramp('#9aa6b2', '#5f6b78', '#d6dee6')
CLOUD = ramp('#ffffff', '#d7e4f0', '#ffffff')
GRASS = ramp('#5fae4a', '#3d7a30', '#8fd36f')
TARMAC = ramp('#4b4f57', '#33363d', '#6a707a')
YELLOW = ramp('#ffd23f', '#d09a10', '#fff08a')
GREEN = ramp('#3fbf6a', '#25804a', '#7fe8a0')
BLUE = ramp('#3d7fd8', '#2a559a', '#7fb4ff')
ORANGE = ramp('#ff8a2a', '#c4561a', '#ffbf7a')
PURPLE = ramp('#7a4fd0', '#4f3292', '#a985ff')
BOARD = ramp('#2f4a3a', '#1f3328', '#47705a')
CHALK = (255, 255, 255)


# ------------------------------------------------------------------ helpers
def xform(f, ox, oy, s, deg):
    """Place a local-space SDF at (ox, oy), scale s, rotation deg."""
    c, sn = np.cos(np.radians(deg)), np.sin(np.radians(deg))

    def g(X, Y):
        x, y = (X - ox) / s, (Y - oy) / s
        u, v = x * c + y * sn, -x * sn + y * c
        return f(u, v) * s
    return g


def xbox(bb, ox, oy, s, deg):
    c, sn = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    pts = [(bb[0], bb[1]), (bb[2], bb[1]), (bb[0], bb[3]), (bb[2], bb[3])]
    out = [(ox + (u * c - v * sn) * s, oy + (u * sn + v * c) * s) for u, v in pts]
    return pbox(out, 4)


def put(cv, f, bb, rmp, X, **kw):
    """Draw local shape f with local bbox bb under transform X=(ox, oy, s, deg)."""
    cv.shape(xform(f, *X), xbox(bb, *X), rmp, **kw)


def cloud(cv, x, y, s, a=1.0):
    blobs = [circle(x + dx * s, y + dy * s, r * s) for dx, dy, r in
             ((-120, 10, 70), (-40, -30, 95), (60, -10, 85), (140, 20, 60), (0, 30, 80))]
    cv.shape(smooth(30 * s, *blobs), (x - 200 * s, y - 130 * s, x + 210 * s, y + 110 * s), CLOUD,
             ow=0, bevel=60 * s, shadow=0, alpha=a, rim=0.1, spec=0.0)


def sky(cv, t, speed=420, seed=3, n=7):
    cv.background(SKY_T, SKY_B, vignette=0.25)
    rng = np.random.default_rng(seed)
    for i in range(n):
        x0, y0, s, k = rng.uniform(-900, 900), rng.uniform(-900, 900), rng.uniform(0.6, 1.3), rng.uniform(0.6, 1.4)
        span = 2600
        x = ((x0 - t * speed * k) + 1300) % span - 1300 + cv.cx
        cloud(cv, x, y0 + cv.cy, s, a=0.92)


def plane(cv, x, y, s=1.0, deg=0.0, eng=(1, 1), smoke=0.0, t=0.0, gear=0.0, nose_gear=0.0, rat=0.0, shadow=0.22):
    """Side view jet facing right. eng: 0..1 exhaust glow per engine. gear: main gear down, nose_gear down."""
    X = (x, y, s, deg)
    kw = dict(ow=5, shadow=shadow)
    # far wing + far engine (behind)
    put(cv, poly([(-40, 20), (90, 20), (-120, -150), (-170, -150)]), (-180, -160, 100, 30), ramp('#c9d0d8', '#9aa3ad', '#e4e9ee'), X, **kw)
    # tail fin and stabiliser
    put(cv, poly([(-330, -40), (-470, -290), (-395, -290), (-240, -40)]), (-480, -300, -230, -30), TAIL, X, bevel=30, **kw)
    put(cv, rotell(-410, 18, 120, 20, -4), (-540, -10, -280, 45), PLANE, X, **kw)
    # body
    body = smooth(30, capsule(-440, -6, 330, 0, 52, 68), ellipse(370, 8, 88, 62))
    put(cv, body, (-500, -80, 470, 80), PLANE, X, bevel=50, **kw)
    put(cv, rbox(-40, 34, 380, 7, 4), (-430, 24, 345, 44), TAIL, X, ow=0, shadow=0, flat=True)
    for wx in range(-330, 300, 34):
        put(cv, rbox(wx, -14, 9, 12, 7), (wx - 10, -27, wx + 10, -1), DARKG, X, ow=0, shadow=0, flat=True)
    put(cv, poly([(370, -36), (420, -34), (438, -12), (382, -14)]), (360, -40, 445, -8), DARKG, X, ow=3, shadow=0, bevel=8)
    # gear
    if gear > 0:
        L = 90 * gear
        put(cv, rbox(-20, 60 + L / 2, 9, L / 2, 4), (-30, 50, -10, 70 + L), DARKG, X, ow=3, shadow=0)
        put(cv, circle(-20, 62 + L, 26), (-48, 34 + L, 8, 90 + L), DARKG, X, ow=3, shadow=0, bevel=10)
    if nose_gear > 0:
        L = 70 * nose_gear
        put(cv, rbox(330, 60 + L / 2, 7, L / 2, 3), (320, 50, 340, 70 + L), DARKG, X, ow=3, shadow=0)
        put(cv, circle(330, 60 + L, 20), (308, 38 + L, 352, 82 + L), DARKG, X, ow=3, shadow=0, bevel=8)
    if rat > 0:                                  # ram air turbine dropping out of the belly
        L = 70 * rat
        put(cv, rbox(160, 60 + L / 2, 6, L / 2, 3), (150, 50, 170, 70 + L), GREY, X, ow=3, shadow=0)
        ang = t * 2200
        for k in range(2):
            a = np.radians(ang + k * 180)
            put(cv, capsule(160, 62 + L, 160 + np.cos(a) * 34, 62 + L + np.sin(a) * 6, 6), (120, 50 + L, 200, 75 + L),
                YELLOW, X, ow=3, shadow=0, bevel=6)
    # near wing + engine
    put(cv, poly([(-60, 30), (100, 30), (-160, 190), (-215, 190)]), (-225, 20, 110, 200), PLANE, X, bevel=24, **kw)
    put(cv, capsule(-120, 100, 30, 100, 40, 36), (-170, 55, 75, 145), GREY, X, bevel=24, **kw)
    put(cv, ellipse(32, 100, 12, 34), (18, 64, 46, 136), DARKG, X, ow=3, shadow=0)
    for k, e in enumerate(eng):                  # exhaust heat shimmer when running
        if e > 0:
            cx, cy = -170, 100
            wx, wy = cv.to_px(*_apply(cx, cy, X))
            cv.glow(circle(*_apply(cx - 10, cy, X), 16 * s), (_apply(cx, cy, X)[0] - 40, _apply(cx, cy, X)[1] - 40,
                    _apply(cx, cy, X)[0] + 40, _apply(cx, cy, X)[1] + 40), '#ff9a3a', 24 * s, 0.5 * e)
            break
    if smoke > 0:
        bx, by = _apply(-170, 100, X)
        specks(cv, t, lambda i, v, tt: (bx - (v[0] * 300 + (tt * 400 + v[1] * 300) % 300) * s, by + (v[2] - 0.5) * 60 * s - v[0] * 40 * s,
                                        smoke * (1 - v[0])), 18, (90, 90, 95), 26 * s, seed=7, a=200)


def _apply(u, v, X):
    ox, oy, s, deg = X
    c, sn = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return ox + (u * c - v * sn) * s, oy + (u * sn + v * c) * s


def gauge(cv, x, y, r, val, lbl, dead=False):
    disc(cv, x, y, r, DARKG)
    disc(cv, x, y, r * 0.82, ramp('#15181d'), ow=0, bevel=10)
    if dead:
        label(cv, '- - -', x, y + 10, int(r * 0.5), (120, 130, 140))
    else:
        a = np.radians(-220 + 260 * val)
        line(cv, [(x, y), (x + np.cos(a) * r * 0.7, y + np.sin(a) * r * 0.7)], 7, flat(hexc('#ff5a4a')))
        dot(cv, x, y, 12, flat(hexc('#e8e8e8')))
    label(cv, lbl, x, y + r + 50, 44, (230, 235, 240))


def chalk(cv, txt, x, y, size, color=CHALK, a=1.0):
    label(cv, txt, x, y, size, color, a)


def caption(cv, txt, lt, dur):
    """Burned-in caption: the beat's line, words appear as they would be spoken."""
    if not txt:
        return
    words = txt.split()
    k = int(np.clip(lt / max(dur - 0.35, 0.3), 0, 1) * len(words) + 0.999)
    shown = ' '.join(words[:max(k, 1)])
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONTB, 58)
    lines, cur = [], ''
    for w in shown.split():
        test = (cur + ' ' + w).strip()
        if d.textlength(test, font=f) > W - 160:
            lines.append(cur); cur = w
        else:
            cur = test
    lines.append(cur)
    y = H - 430 - 70 * (len(lines) - 1)
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text(((W - tw) / 2, y), ln, font=f, fill=(255, 255, 255, 255), stroke_width=9, stroke_fill=(20, 14, 26, 255))
        y += 72
    cv.overlay(im)


# ------------------------------------------------------------------ scenes: fn(lt, dur, T) -> Canvas
def s_cruise(lt, dur, T, dying=False, alt=41000):
    cv = Canvas(0, 0, 1.0)
    sky(cv, T)
    bob = 10 * np.sin(T * 1.7)
    e = 1.0 if not dying else float(np.clip(1 - (lt - 0.8) / 0.6, 0, 1))
    plane(cv, 0, 60 + bob, 1.05, -2, eng=(e, e), smoke=0 if not dying else float(np.clip((lt - 0.8) * 2, 0, 1) * (lt < dur)), t=T)
    a = alt if not dying else alt
    box(cv, 0, -700, 260, 70, DARKG, r=24, shadow=0.3)
    label(cv, f'{int(a):,} FT', 0, -690, 70, (255, 214, 64))
    return cv


def s_engine(lt, dur, T):
    """Engine front view: fan spinning down to a stop."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2b3240', '#4d586c', vignette=0.4)
    disc(cv, 0, 0, 420, GREY, bevel=60)
    disc(cv, 0, 0, 360, ramp('#1d2128'), ow=0, bevel=20)
    spin = 900 * max(0, 1 - lt / (dur * 0.8)) ** 2
    ang0 = (T * spin) % 360 if spin > 0 else 0
    ang0 = 1500 * (1 - (1 - min(lt / (dur * 0.8), 1)) ** 3)
    for k in range(18):
        a = np.radians(ang0 + k * 20)
        p0 = (np.cos(a) * 70, np.sin(a) * 70); p1 = (np.cos(a + 0.35) * 340, np.sin(a + 0.35) * 340)
        cv.shape(capsule(p0[0], p0[1], p1[0], p1[1], 18, 30), bbox_of([p0, p1], 32), METAL, ow=3, shadow=0, bevel=14)
    disc(cv, 0, 0, 90, DARKG, bevel=40)
    hook_text(cv, 'SILENCE', lt, y=-700, pop_t=dur * 0.7, color=(255, 255, 255))
    return cv


def s_board(lt, dur, T, mode='math'):
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a3d2b', '#3a271c', vignette=0.4)
    box(cv, 0, -40, 470, 620, WOOD, r=20)
    box(cv, 0, -40, 430, 580, BOARD, r=10, ow=3, bevel=20, shadow=0)
    if mode == 'math':
        chalk(cv, '2 + 2 = 4', -40, -400, 90, a=0.35)
        chalk(cv, 'x  =  ?', 60, -240, 90, a=0.35)
        k = np.clip(lt / 0.5, 0, 1)
        chalk(cv, '1.77', 0, 40, int(200 * (0.7 + 0.3 * k)), (255, 230, 120))
        box(cv, 0, 260, 300, 8, flat(hexc('#ffffff')), r=4, ow=0, shadow=0)
        hook_text(cv, 'MATH MISTAKE', lt, y=-760, pop_t=0.25, color=(255, 90, 80))
    else:                                        # the unit swap
        chalk(cv, '1.77', -180, -300, 150)
        k1, k2 = np.clip((lt - 0.4) / 0.3, 0, 1), np.clip((lt - dur * 0.45) / 0.3, 0, 1)
        if k1 > 0:
            chalk(cv, 'POUNDS', 180, -300, int(90 * k1), (130, 200, 255))
        if k2 > 0:
            chalk(cv, '1.77', -180, 60, 150)
            chalk(cv, 'KILOS', 180, 60, int(90 * k2), (255, 160, 90))
            line(cv, [(-330, 240), (330, -120)], 22 * k2, flat(hexc('#ff4a3a')), ow=4)
            line(cv, [(-330, -120), (330, 240)], 22 * k2, flat(hexc('#ff4a3a')), ow=4)
        hook_text(cv, 'LB  vs  KG', lt, y=-760, pop_t=0.3)
    guy(cv, 400, 760, 0.55, face='worried' if mode == 'units' else 'calm', arms=((150, 30), (15, 0)), coat=False)
    return cv


def s_gauges(lt, dur, T):
    """Montreal, earlier: rewind lines, then the cockpit panel with blank fuel gauges."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#262b35', '#3b4352', vignette=0.45)
    box(cv, 0, 80, 520, 560, DARKG, r=40)
    for i, (gx, gy, lbl) in enumerate(((-250, -180, 'SPEED'), (250, -180, 'ALT'), (-250, 300, 'FUEL L'), (250, 300, 'FUEL R'))):
        dead = 'FUEL' in lbl
        gauge(cv, gx, gy, 150, 0.5 + 0.2 * np.sin(T * 2 + i), lbl, dead=dead)
        if dead and int(T * 3) % 2 == 0:
            cv.glow(circle(gx, gy, 150), (gx - 160, gy - 160, gx + 160, gy + 160), '#ff3a2a', 20, 0.35)
    hook_text(cv, 'GAUGES DEAD', lt, y=-720, pop_t=0.4, color=(255, 90, 80))
    if lt < 0.6:                                  # rewind wipe in
        cv.flash('#ffffff', 0.5 * (1 - lt / 0.6))
        speed_lines(cv, T, 1.0 - lt / 0.6, vertical=False)
    label(cv, 'MONTREAL', 0, -820, 54, (200, 210, 225))
    return cv


def tarmac(cv, T):
    cv.background('#9fd2ff', '#e9f6ff', vignette=0.25)
    box(cv, 0, 760, 1200, 520, TARMAC, r=0, ow=0, shadow=0)
    for x in range(-900, 900, 260):
        box(cv, x + (T * 0) % 260, 640, 70, 8, flat(hexc('#f2e27a')), r=4, ow=0, shadow=0)


def s_dipstick(lt, dur, T):
    cv = Canvas(0, -100, 0.9)
    tarmac(cv, T)
    plane(cv, 150, 320, 1.6, 0, eng=(0, 0), gear=1, nose_gear=1, t=T)
    pull = np.clip((lt - 0.6) / 1.4, 0, 1)
    sx, sy = -150, 470
    line(cv, [(sx, sy - 160 * pull), (sx, sy + 260 - 160 * pull)], 10, flat(hexc('#d9dde2')), ow=4)
    guy(cv, -420, 900, 0.65, face='calm', arms=((150, 10), (120, 20)), shirt=ORANGE)
    if pull > 0.9:
        label(cv, 'MEASURED BY HAND', 0, -760, 74, (255, 230, 90))
    return cv


def s_tank(lt, dur, T):
    """Fuel needed vs fuel loaded."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1f2a3a', '#33465f', vignette=0.4)
    need, have = 22300, 10100
    top, bot = -620, 620
    box(cv, 0, 0, 260, 660, GLASS, r=40, alpha=0.5, shadow=0.3)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    lvl = bot - (bot - top) * (have / need) * k
    f, bb = wave_surface(lvl, 10, 0.03, T * 4, x0=-245, x1=245, y1=640)
    cv.shape(f, bb, ORANGE, ow=3, shadow=0, bevel=30)
    line(cv, [(-300, top), (300, top)], 6, flat(hexc('#7fe08a')), ow=3)
    label(cv, 'NEEDED  22,300 kg', 0, top - 70, 56, (130, 240, 150))
    if k > 0.95:
        label(cv, 'LOADED  10,100 kg', 0, lvl - 60, 56, (255, 200, 120))
        hook_text(cv, 'LESS THAN HALF', lt, y=760, pop_t=dur * 0.62, color=(255, 90, 80))
    return cv


def s_cabin(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#ece3d4', '#b9ab95', vignette=0.45)
    shirts = [SHIRT, RED, BLUE, ORANGE, PURPLE, GREEN]
    rng = np.random.default_rng(5)
    for row, (y, s) in enumerate(((150, 0.45), (500, 0.6), (920, 0.78))):
        for i, x in enumerate(np.linspace(-430, 430, 4 - (row == 2))):
            box(cv, x, y - 200 * s, 120 * s * 1.4, 220 * s, ramp('#2d4f8a'), r=30)
            guy(cv, x + rng.normal(0, 6), y + 200 * s, s, face=['worried', 'shock', 'worried'][row], legs=False,
                arms=((25 + 10 * np.sin(T * 9 + i), 0), (25, 0)), shirt=shirts[(row * 3 + i) % 6], woman=bool((row + i) % 2),
                ground=False)
    hook_text(cv, '69 ON BOARD', lt, y=-760, pop_t=0.3)
    return cv


def s_captain(lt, dur, T):
    cv = Canvas(0, -150, 1.0)
    cv.background('#2a3140', '#495570', vignette=0.4)
    guy(cv, -170, 700, 1.0, face='happy', arms=((40, 70), (40, 70)), shirt=ramp('#f4f1ea'), bald=False)
    label(cv, 'CAPT. BOB PEARSON', -170, 830, 50, (255, 230, 120))
    # thought bubble with a glider
    k = ease(np.clip((lt - 0.5) / 0.5, 0, 1))
    if k > 0:
        for (bx, by, br) in ((90, -320, 26), (150, -420, 40)):
            disc(cv, bx, by, br * k, CLOUD, ow=4)
        cv.shape(smooth(40, circle(260, -760, 230 * k), circle(80, -720, 160 * k), circle(430, -700, 170 * k)),
                 (-100, -1000, 620, -540), CLOUD, ow=5, shadow=0.15)
        gx = 260 + 60 * np.sin(T * 1.4)
        put(cv, capsule(-150, 0, 150, 0, 18, 26), (-170, -30, 170, 30), YELLOW, (gx, -760, k, 0), ow=4, shadow=0)
        put(cv, capsule(-10, 0, 10, 0, 6), (-260, -12, 260, 12), YELLOW, (gx, -770, k, 0), ow=4, shadow=0)
        put(cv, rbox(0, 0, 250, 8, 6), (-260, -12, 260, 12), YELLOW, (gx - 10, -772, k, 0), ow=4, shadow=0)
        hook_text(cv, 'GLIDER PILOT', lt, y=640, pop_t=1.0, color=(120, 230, 255))
    return cv


def s_rat(lt, dur, T):
    cv = Canvas(120, 40, 1.9)
    sky(cv, T, speed=300)
    plane(cv, 0, 0, 1.0, -3, eng=(0, 0), rat=ease(np.clip(lt / 0.6, 0, 1)), t=T)
    if lt > 0.8:
        label(cv, 'RAM AIR TURBINE', 160, 220, 40, (255, 230, 90))
    hook_text(cv, 'BACKUP POWER', lt, y=-720, pop_t=1.2)
    return cv


def s_map(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#7cc4e8', '#4a9cc8', vignette=0.35)
    land = smooth(80, circle(-120, -100, 420), circle(200, 250, 380), circle(-260, 420, 300), circle(150, -520, 300))
    cv.shape(land, (-700, -900, 700, 800), GRASS, ow=6, bevel=60)
    lake = smooth(40, ellipse(120, -80, 90, 300), ellipse(170, 230, 70, 160))
    cv.shape(lake, (0, -420, 280, 420), ramp('#5ab2e2'), ow=4, bevel=30, shadow=0)
    label(cv, 'MANITOBA', -260, -380, 50, (255, 255, 255))
    p0, p1 = (420, -820), (-30, 60)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    n = 20
    pts = [(p0[0] + (p1[0] - p0[0]) * j / n, p0[1] + (p1[1] - p0[1]) * j / n + 80 * np.sin(j / n * np.pi)) for j in range(n + 1)]
    m = max(2, int(k * n) + 1)
    for j in range(0, m - 1, 2):
        line(cv, [pts[j], pts[j + 1]], 8, flat(hexc('#ffffff')))
    px, py = pts[m - 1]
    put(cv, capsule(-40, 0, 40, 0, 12), (-45, -15, 45, 15), PLANE, (px, py, 1, 110), ow=3)
    if k > 0.9:
        disc(cv, p1[0], p1[1], 20, RED)
        hook_text(cv, 'GIMLI', lt, y=150, pop_t=dur * 0.85, color=(255, 236, 80))
    return cv


def racecar(cv, x, y, s, col, T):
    box(cv, x, y, 120 * s, 32 * s, col, r=24 * s)
    box(cv, x + 10 * s, y - 34 * s, 50 * s, 22 * s, GLASS, r=14 * s, ow=4)
    for wx in (-70, 75):
        disc(cv, x + wx * s, y + 30 * s, 26 * s, DARKG)


def s_race(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#9fd2ff', '#e9f6ff', vignette=0.25)
    box(cv, 0, 600, 1200, 700, GRASS, r=0, ow=0, shadow=0)
    box(cv, 0, 380, 1200, 170, TARMAC, r=0, ow=4, shadow=0)
    for x in range(-900, 900, 220):
        box(cv, x - (T * 600) % 220, 380, 60, 8, flat(hexc('#ffffff')), r=4, ow=0, shadow=0)
    # campers and crowd behind
    for i, x in enumerate((-430, -150, 260)):
        box(cv, x, 120, 120, 70, ramp(['#e9e2cf', '#d8ecf0', '#f0d7c8'][i]), r=20)
        disc(cv, x - 60, 200, 26, DARKG); disc(cv, x + 60, 200, 26, DARKG)
    for i, x in enumerate(np.linspace(-480, 480, 7)):
        guy(cv, x, 920 + 30 * (i % 2), 0.38, face='happy' if lt < dur * 0.6 else 'shock',
            arms=((150, 20), (150, 20)) if lt < dur * 0.6 else ((170, 0), (170, 0)), shirt=[SHIRT, RED, BLUE, ORANGE][i % 4])
    for i, (col, off) in enumerate(((RED, 0), (BLUE, 520), (YELLOW, 1040))):
        x = ((T * 900 + off) % 1800) - 900
        racecar(cv, x, 370 - 40 * (i == 1), 0.9, col, T)
    hook_text(cv, 'RACE DAY', lt, y=-760, pop_t=0.3)
    # the jet's shadow sweeping over once the voice says nobody knew
    if lt > dur * 0.55:
        k = (lt - dur * 0.55) / (dur * 0.45)
        sxx = -1400 + 2600 * k
        cv.shape(xform(smooth(20, capsule(-300, 0, 300, 0, 50), poly([(-60, 0), (60, 0), (-80, 220), (-140, 220)]),
                              poly([(-60, 0), (60, 0), (-80, -220), (-140, -220)])), sxx, 520, 1.2, 0),
                 (sxx - 400, 220, sxx + 400, 820), ramp('#000000'), ow=0, shadow=0, alpha=0.3, flat=True)
    return cv


def s_slip(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky(cv, T, speed=250)
    roll = keys(lt, [(0, -2), (0.8, -28), (dur - 0.6, -28), (dur, -6)])
    y = keys(lt, [(0, -500), (dur, 300)])
    plane(cv, 60, y, 0.85, roll, eng=(0, 0), gear=1, t=T)
    speed_lines(cv, T, 0.7)
    hook_text(cv, 'SIDESLIP', lt, y=-760, pop_t=0.6)
    label(cv, 'DROPPING FAST', 0, 700, 60, (255, 255, 255))
    return cv


def s_landing(lt, dur, T):
    """Touchdown, nose gear folds, nose scrapes with sparks, stops short of the crowd."""
    slide = 1 - (1 - np.clip(lt / (dur * 0.85), 0, 1)) ** 2
    x = -900 + 1300 * slide
    cv = Canvas(x * 0.6, 0, 0.8)
    cv.background('#9fd2ff', '#e9f6ff', vignette=0.3)
    box(cv, x * 0.6, 760, 1600, 520, TARMAC, r=0, ow=0, shadow=0)
    for xx in range(-2400, 2400, 300):
        box(cv, xx, 620, 80, 8, flat(hexc('#f2e27a')), r=4, ow=0, shadow=0)
    for i, gx in enumerate(np.linspace(800, 1300, 5)):        # crowd at the end of the strip
        guy(cv, gx, 700, 0.45, face='shock', arms=((160, 10), (160, 10)), shirt=[RED, BLUE, ORANGE, SHIRT, PURPLE][i])
    folded = lt > 0.5
    deg = 0 if not folded else 6 * min(1, (lt - 0.5) / 0.2)
    plane(cv, x, 470, 1.0, deg, eng=(0, 0), gear=1, nose_gear=0 if folded else 1, t=T, shadow=0.3)
    if folded and slide < 0.99:
        nx, ny = _apply(390, 60, (x, 470, 1.0, deg))
        specks(cv, T, lambda i, v, tt: (nx - v[0] * 380 - ((tt * 900 + v[1] * 380) % 380), ny - v[2] * 120 + ((tt * 900 + v[1] * 380) % 380) * 0.2 * v[3], 1 - v[0]),
               60, (255, 210, 90), 7, seed=11)
    if lt > dur * 0.86:
        hook_text(cv, 'STOPPED', lt, y=-720, pop_t=dur * 0.86, color=(120, 255, 140))
    return cv


def s_slides(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#ffd27a', '#ff9a5a', vignette=0.3)
    box(cv, 0, 700, 1200, 400, TARMAC, r=0, ow=0, shadow=0)
    plane(cv, 200, 260, 1.4, 6, eng=(0, 0), gear=1, t=T)
    cv.shape(poly([(-120, 300), (-60, 300), (-420, 640), (-500, 640)]), (-510, 290, -50, 650), YELLOW, ow=5)
    for i in range(4):
        k = ((lt * 0.9 + i * 0.3) % 1.2) / 1.2
        gx, gy = -100 - 360 * k, 260 + 360 * k
        guy(cv, gx, gy, 0.3, face='happy', arms=((160, 10), (160, 10)), shirt=[RED, BLUE, ORANGE, SHIRT][i])
    for i, x in enumerate((-300, 0, 300)):
        guy(cv, x, 980, 0.6, face='happy', arms=((165, 10), (150, 30)), shirt=[GREEN, PURPLE, RED][i])
    hook_text(cv, 'NOBODY DIED', lt, y=-760, pop_t=0.3, color=(120, 255, 140))
    return cv


def s_outro(lt, dur, T):
    """Board again, then dissolve back to the cruising jet so it loops."""
    cv = s_board(lt + 2, dur + 2, T, mode='units')
    k = np.clip((lt - (dur - 0.75)) / 0.6, 0, 1)                   # fully on the jet a few frames before the cut
    if k > 0:
        nxt = s_cruise(0, 1, T - timeline()[1])          # same clock as frame one, so the loop is seamless
        cv.img = np.ascontiguousarray(cv.img * (1 - k) + nxt.img * k, dtype=np.float32)
    return cv


# ------------------------------------------------------------------ the script (line, scene, extra hold)
BEATS = [
    ("This plane ran out of fuel at forty-one thousand feet.", lambda lt, d, T: s_cruise(lt, d, T, dying=True), 0.4),
    ("Both engines went quiet.", s_engine, 0.6),
    ("And it all came down to one math mistake.", s_board, 0.4),
    ("Earlier that day in Montreal, the plane's fuel gauges were broken.", s_gauges, 0.3),
    ("So the crew measured the fuel by hand, with a dipstick.", s_dipstick, 0.3),
    ("The number they used was in pounds. But they treated it like kilograms.",
     lambda lt, d, T: s_board(lt, d, T, mode='units'), 0.5),
    ("So the jet took off with less than half the fuel it needed.", s_tank, 0.5),
    ("Over Ontario, the engines shut down one after the other.", lambda lt, d, T: s_cruise(lt, d, T, dying=True, alt=35000), 0.3),
    ("Sixty-nine people were now riding in a giant glider.", s_cabin, 0.4),
    ("But the captain had a secret. He flew gliders for fun.", s_captain, 0.5),
    ("A tiny propeller dropped out of the belly, just to keep the controls working.", s_rat, 0.3),
    ("He aimed for an old air force base in Gimli, Manitoba.", s_map, 0.3),
    ("What nobody knew? The old runway was now a racetrack, and it was race day.", s_race, 0.6),
    ("Coming in too high, he turned the jet sideways to drop like a rock.", s_slip, 0.4),
    ("The nose wheel never locked. It folded, and the nose scraped the runway like a brake.", s_landing, 0.5),
    ("It stopped before reaching the crowd. Nobody died.", s_slides, 0.6),
    ("So the next time someone says a little math doesn't matter, remember the day", s_outro, 0.0),
]
WPS = 2.7


def timeline():
    tj = os.environ.get('GIMLI_TIMES')
    if tj and os.path.exists(tj):                       # retime to the recorded voice
        import json
        d = json.load(open(tj))
        return [(t0, du, fn, l) for (l, fn, h), t0, du in zip(BEATS, d['starts'], d['durs'])], d['total']
    t, out = 0.0, []
    for line_, fn, hold in BEATS:
        d = len(line_.split()) / WPS + 0.35 + hold
        out.append((t, d, fn, line_))
        t += d
    return out, t


def render_frame(T, TL):
    for (t0, d, fn, line_) in TL:
        if t0 <= T < t0 + d:
            lt = T - t0
            cv = fn(lt, d, T)
            caption(cv, line_, lt, d)
            if lt < 0.12 and t0 > 0:                 # quick white pop on each cut
                cv.flash('#ffffff', 0.35 * (1 - lt / 0.12))
            return cv
    cv = TL[-1][2](TL[-1][1], TL[-1][1], T)
    return cv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--from', dest='t0', type=float, default=0)
    ap.add_argument('--to', dest='t1', type=float, default=None)
    ap.add_argument('--still', type=float, default=None)
    a = ap.parse_args()
    TL, total = timeline()
    if a.still is not None:
        Image.fromarray(render_frame(a.still, TL).to_uint8()).save(a.out); return
    t1 = total if a.t1 is None else min(a.t1, total)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    for i in range(int(a.t0 * FPS), int(t1 * FPS)):
        ff.stdin.write(render_frame(i / FPS, TL).to_uint8().tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    main()
