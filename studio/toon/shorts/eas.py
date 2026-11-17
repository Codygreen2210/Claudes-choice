#!/usr/bin/env python3
"""The Emergency Alert System (Google's #1 US search on Nov 17 2026, the day of the nationwide test).
Opens on the living-room TV and radio screaming the alarm, him launching off the couch; the 'only a test' screen and the
quiet phone; the President's red button (a hand, no face); the message racing across the map to ~80 stations; one
station's sealed shelter riding out a storm; stations listening and passing it on like dominoes; the buzz is code read
by a little decoder box; 9 of 10 Americans in 10 minutes; 2011's flop (music instead of the alert); 1962's missile
scare that started it; the payoff: the button, dusty under glass, never used for real.
Facts: FEMA/IPAWS EAS fact sheet (ready.gov, 2020): President can address the public within 10 minutes; PEP stations
reach 90%+ of Americans; only the President activates the national level; messages carry a coded header. NPR (Feb 19
2013): nearly 80 PEP stations with shelters built to ride out hurricanes, tornadoes and an EMP; started by Kennedy after
the Cuban missile crisis (EBS, 1963). Wikipedia (EAS, National Periodic Test): each station monitors at least two others
(47 CFR 11.52) and relays in a daisy chain; 2011 test: about half got it via IPAWS, DirecTV played Lady Gaga music;
no president has used it for real. NBC DFW / Audacy (Nov 2026): test Nov 17, TV + radio only, phones left out.
Sound note: the real EAS attention tones and data bursts are never used (FCC rules); our alarm is our own."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

DIVE = {}
ALR = (255, 70, 60)
MAPC = ramp('#5fbf6a', '#2f8a44', '#9ae8a8')
SEA = ('#1a4f8a', '#0d2a52')
TOWERC = ramp('#e2483d', '#a82a26', '#ff8070')
CONC = ramp('#9aa0a8', '#636a74', '#c8ced6')
TVC = ramp('#2b2f38', '#191c22', '#454b57')
COUCH = ramp('#7a5ad0', '#4f3a9a', '#a890ff')
OLD = ramp('#b08a5a', '#7a5a30', '#d8b888')
BTN = ramp('#ff3a2a', '#b01a10', '#ff9a88')


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


# ---------------------------------------------------------------- the map
_US = [(-124.7, 48.4), (-123, 49), (-95, 49), (-89.6, 48), (-84.8, 46.5), (-83, 46), (-82.5, 43), (-79, 43.3), (-76, 44),
       (-75, 45), (-71.5, 45), (-69, 47.4), (-67, 45), (-70, 43.5), (-70.6, 42), (-74, 40.5), (-75.5, 39), (-76, 37),
       (-75.5, 35.2), (-78, 33.8), (-81, 31.5), (-80, 27), (-80.4, 25.2), (-81.8, 26.5), (-82.7, 28), (-83.5, 29.9),
       (-85.5, 29.7), (-89, 30.3), (-89.5, 29), (-91, 29.4), (-94, 29.6), (-97.2, 27.8), (-97.4, 26), (-99.5, 27.5),
       (-101.4, 29.8), (-103, 29), (-104.5, 29.7), (-106.5, 31.8), (-108.2, 31.3), (-111, 31.3), (-114.8, 32.5),
       (-117.1, 32.5), (-118.5, 34), (-120.6, 34.6), (-122.5, 37.5), (-124, 40.3), (-124.4, 43), (-124, 46.3)]


def proj(lon, lat, s=1.0, ox=0.0, oy=0.0):
    return ox + (lon + 96.0) * 17.5 * s, oy + (38.0 - lat) * 22.0 * s


def _inside(px, py, pts):
    c = False
    for i in range(len(pts)):
        x0, y0 = pts[i]; x1, y1 = pts[i - 1]
        if (y0 > py) != (y1 > py) and px < (x1 - x0) * (py - y0) / (y1 - y0) + x0:
            c = not c
    return c


_rr = np.random.default_rng(80)
STATIONS = []
while len(STATIONS) < 80:                                                   # about 80 PEP stations, spread over the map
    lon, lat = _rr.uniform(-124, -68), _rr.uniform(26, 48.5)
    if _inside(lon, lat, _US) and all((lon - a) ** 2 + (lat - b) ** 2 > 2.2 for a, b in STATIONS):
        STATIONS.append((lon, lat))
DC = (-77.0, 38.9)


def usmap(cv, s=1.0, ox=0.0, oy=0.0):
    pts = [proj(lo, la, s, ox, oy) for lo, la in _US]
    cv.shape(poly(pts), pbox(pts, 10), MAPC, ow=5)


def mini_tower(cv, x, y, s, lit=0.0, T=0.0):
    pts = [(x - 14 * s, y), (x, y - 60 * s), (x + 14 * s, y)]
    line(cv, pts, 5 * s, TOWERC, ow=2)
    line(cv, [(x - 8 * s, y - 24 * s), (x + 8 * s, y - 24 * s)], 4 * s, TOWERC, ow=1)
    c = (255, 80, 60) if lit > 0.5 else (90, 90, 100)
    if lit > 0:
        cv.glow(circle(x, y - 62 * s, 10 * s), (x - 60 * s, y - 120 * s, x + 60 * s, y), '#ff5a3a', 22 * s, lit * (0.7 + 0.3 * np.sin(T * 14)))
    disc(cv, x, y - 62 * s, 9 * s, ramp('#%02x%02x%02x' % c), ow=2)


def waves(cv, x, y, T, r0=60, n=3, col='#ff5a3a', a=1.0, spd=1.6, span=240, w=8):
    for k in range(n):
        u = (T * spd + k / n) % 1
        r = r0 + span * u
        aa = a * (1 - u)
        for sd in (-1, 1):
            arc = [(x + sd * r * np.cos(t), y + r * np.sin(t)) for t in np.linspace(-0.7, 0.7, 9)]
            line(cv, arc, w, flat(hexc(col)), a=aa)


def tower(cv, x, y, s, T, lit=0.0):
    """a lattice radio tower, a blinking light on top"""
    h = 620 * s
    L, R_ = (x - 90 * s, y), (x + 90 * s, y)
    top = (x, y - h)
    line(cv, [L, top, R_], 14 * s, TOWERC, ow=3)
    for k in range(1, 7):
        f = k / 7; yy = y - h * f; hw = 90 * s * (1 - f)
        line(cv, [(x - hw, yy), (x + hw, yy)], 9 * s, TOWERC, ow=2)
        if k < 6:
            f2 = (k + 1) / 7; yy2 = y - h * f2; hw2 = 90 * s * (1 - f2)
            line(cv, [(x - hw, yy), (x + hw2, yy2)], 6 * s, TOWERC, ow=2)
    blink = 0.5 + 0.5 * np.sin(T * 6)
    cv.glow(circle(x, y - h - 10 * s, 16 * s), (x - 90 * s, y - h - 100 * s, x + 90 * s, y - h + 80 * s), '#ff5a3a', 30 * s, 0.4 + 0.6 * max(blink, lit))
    disc(cv, x, y - h - 10 * s, 16 * s, BTN, ow=3)
    if lit > 0:
        waves(cv, x, y - h - 10 * s, T, r0=50 * s, a=lit, span=300 * s, w=10 * s)


def tv(cv, x, y, s, T, mode='alert', k=1.0):
    """flat TV on a stand. mode: alert (red/white flashing bars + ALERT), test (only-a-test card), off, party, static"""
    box(cv, x, y + 300 * s, 30 * s, 60 * s, TVC, r=6 * s)
    box(cv, x, y + 360 * s, 170 * s, 14 * s, TVC, r=6 * s)
    box(cv, x, y, 420 * s, 260 * s, TVC, r=26 * s, ow=5)
    sw, sh = 390 * s, 230 * s
    if mode == 'alert':
        on = (T * 4) % 1 < 0.5
        box(cv, x, y, sw, sh, ramp('#d81e1e' if on else '#ffffff'), r=10 * s, ow=0, shadow=0)
        for j in range(5):
            box(cv, x, y - sh + (2 * j + 1) * sh / 5, sw, sh / 10, ramp('#ffffff' if on else '#d81e1e'), r=0, ow=0, shadow=0, alpha=0.9)
        cv.glow(rbox(x, y, sw, sh, 10 * s), (x - sw - 200 * s, y - sh - 200 * s, x + sw + 200 * s, y + sh + 200 * s), '#ff3a2a', 120 * s, 0.6 * k)
        label(cv, 'EMERGENCY', x, y - 50 * s, 92 * s, (255, 255, 255), stroke=10)
        label(cv, 'ALERT', x, y + 70 * s, 120 * s, (255, 236, 80), stroke=12)
    elif mode == 'test':
        box(cv, x, y, sw, sh, ramp('#1d3f8a', '#12285a', '#3a62b8'), r=10 * s, ow=0, shadow=0)
        box(cv, x, y + sh - 50 * s, sw, 40 * s, ramp('#ffd23f'), r=0, ow=0, shadow=0)
        label(cv, 'THIS IS ONLY', x, y - 70 * s, 70 * s, WHT, stroke=0)
        label(cv, 'A TEST', x, y + 30 * s, 110 * s, WHT, stroke=0)
        off = (T * 260) % (sw * 2)
        label(cv, 'NO ACTION NEEDED  •  NO ACTION NEEDED', x + sw - off, y + sh - 52 * s, 40 * s, (20, 14, 26), stroke=0)
    elif mode == 'party':
        box(cv, x, y, sw, sh, ramp('#3a1a6a', '#1a0a3a', '#6a3ab0'), r=10 * s, ow=0, shadow=0)
        for j in range(6):
            a = -1.0 + j * 0.4 + 0.3 * np.sin(T * 2 + j)
            pts = [(x, y - sh), (x + np.sin(a) * sw * 1.3, y + sh), (x + np.sin(a + 0.15) * sw * 1.3, y + sh)]
            cv.shape(poly(pts), (x - sw, y - sh, x + sw, y + sh), ramp('#ff7ad0' if j % 2 else '#7ad0ff'), ow=0, shadow=0, alpha=0.35)
        disc(cv, x, y - sh * 0.45, 50 * s, ramp('#e8e8f0', '#9a9ab0', '#ffffff'), ow=3)
        for j in range(5):
            u = (T * 0.8 + j / 5) % 1
            nx, ny = x - sw * 0.7 + j * sw * 0.35, y + sh * 0.6 - u * sh * 1.2
            NC = ramp('#ffe678', '#c8a830', '#fff4c0'); aa = float(np.sin(np.pi * u))
            disc(cv, nx, ny, 22 * s, NC, ow=3, alpha=aa)
            line(cv, [(nx + 18 * s, ny), (nx + 18 * s, ny - 70 * s)], 7 * s, NC, ow=2, a=aa)
    elif mode == 'static':
        rr = np.random.default_rng(int(T * 30))
        box(cv, x, y, sw, sh, ramp('#606068'), r=10 * s, ow=0, shadow=0)
        for j in range(160):
            dot(cv, x + rr.uniform(-sw, sw), y + rr.uniform(-sh, sh), rr.uniform(4, 12) * s, flat(hexc('#ffffff' if rr.random() < 0.5 else '#20202a')), a=0.8)
    else:
        box(cv, x, y, sw, sh, ramp('#101218'), r=10 * s, ow=0, shadow=0)


def radio(cv, x, y, s, T, loud=0.0):
    jx = 6 * loud * np.sin(T * 50)
    box(cv, x + jx, y, 170 * s, 100 * s, OLD, r=24 * s, ow=4)
    disc(cv, x - 80 * s + jx, y, 62 * s, ramp('#4a3020', '#2a1810', '#7a5a40'), ow=3)
    for j in range(4):
        line(cv, [(x - 130 * s + jx, y - 30 * s + j * 20 * s), (x - 30 * s + jx, y - 30 * s + j * 20 * s)], 4 * s, flat(hexc('#2a1810')), a=0.8)
    box(cv, x + 80 * s + jx, y - 30 * s, 60 * s, 26 * s, ramp('#ffe9a0'), r=6 * s, ow=2)
    disc(cv, x + 60 * s + jx, y + 50 * s, 18 * s, DARK, ow=2)
    disc(cv, x + 110 * s + jx, y + 50 * s, 18 * s, DARK, ow=2)
    line(cv, [(x + 120 * s + jx, y - 100 * s), (x + 200 * s + jx, y - 260 * s)], 6 * s, METAL, ow=2)
    if loud > 0:
        waves(cv, x + jx, y - 20 * s, T, r0=200 * s, a=loud, span=200 * s, w=10 * s, spd=2.2)


def room(cv):
    cv.background('#3a2a5a', '#1a1230', vignette=0.35)
    box(cv, 0, 760, 1400, 420, WOOD, r=0, ow=0, shadow=0)                      # floor
    box(cv, 0, 345, 1400, 8, ramp('#2a1a10'), r=0, ow=0, shadow=0, alpha=0.6)


def red_button(cv, x, y, s, press=0.0, dust=0.0, dome=True, T=0.0, glow=1.0):
    box(cv, x, y + 70 * s, 260 * s, 60 * s, DARKM, r=20 * s, ow=4)                 # the base
    label(cv, 'NATIONAL ALERT', x, y + 74 * s, 34 * s, (255, 210, 80), stroke=0)
    cv.glow(ellipse(x, y - 10 * s + 20 * s * press, 150 * s, 70 * s), (x - 320 * s, y - 220 * s, x + 320 * s, y + 160 * s), '#ff3a2a', 60 * s, 0.6 * glow * (1 - dust))
    cv.shape(ellipse(x, y + 10 * s, 170 * s, 60 * s), (x - 180 * s, y - 60 * s, x + 180 * s, y + 80 * s), DARK, ow=4)
    yy = y - 30 * s + 26 * s * press
    cv.shape(ellipse(x, yy, 140 * s, 70 * s), (x - 150 * s, yy - 80 * s, x + 150 * s, yy + 80 * s), BTN, ow=4)
    if dust > 0:
        rr = np.random.default_rng(9)
        for j in range(60):
            dot(cv, x + rr.uniform(-130, 130) * s, yy + rr.uniform(-50, 40) * s, rr.uniform(3, 8) * s, flat(hexc('#c8bca8')), a=0.7 * dust)
    if dome:
        cv.shape(ellipse(x, y - 60 * s, 230 * s, 200 * s), (x - 240 * s, y - 270 * s, x + 240 * s, y + 150 * s), GLASS, ow=4, shadow=0, alpha=0.28)
        line(cv, [(x - 150 * s, y - 180 * s), (x - 90 * s, y - 230 * s)], 12 * s, flat(hexc('#ffffff')), a=0.6)
        if dust > 0:
            rr = np.random.default_rng(4)
            for j in range(90):
                a = rr.uniform(np.pi, 2 * np.pi); rad = rr.uniform(0.7, 1.0)
                dot(cv, x + 230 * s * rad * np.cos(a), y - 60 * s + 200 * s * rad * np.sin(a), rr.uniform(3, 7) * s, flat(hexc('#d8ccb8')), a=0.55 * dust)


def cobweb(cv, x, y, s, a=1.0):
    C = flat(hexc('#e8e8f0'))
    for k in range(6):
        ang = np.pi / 2 * k / 5
        line(cv, [(x, y), (x + 260 * s * np.cos(ang), y + 260 * s * np.sin(ang))], 3 * s, C, a=0.7 * a)
    for r in (70, 130, 190, 250):
        pts = [(x + r * s * np.cos(np.pi / 2 * k / 5), y + r * s * np.sin(np.pi / 2 * k / 5)) for k in range(6)]
        line(cv, pts, 3 * s, C, a=0.6 * a)


def person(cv, x, y, s, lit):
    col = ramp('#ffd23f', '#d09a10', '#fff08a') if lit else ramp('#5a6070', '#3a404c', '#7a8090')
    disc(cv, x, y - 70 * s, 34 * s, col, ow=3)
    cv.shape(rbox(x, y + 20 * s, 50 * s, 50 * s, 30 * s), (x - 60 * s, y - 40 * s, x + 60 * s, y + 80 * s), col, ow=3)
    if lit:
        cv.glow(circle(x, y - 20 * s, 60 * s), (x - 120 * s, y - 140 * s, x + 120 * s, y + 100 * s), '#ffe14d', 30 * s, 0.35)


def clock(cv, x, y, r, k):
    disc(cv, x, y, r, ramp('#f4f1ea', '#c9c3b8', '#ffffff'), ow=6)
    a0 = -np.pi / 2
    if k > 0:                                                                   # the ten-minute wedge filling up
        n = 24; pts = [(x, y)] + [(x + (r - 18) * np.cos(a0 + 2 * np.pi * (10 / 60) * k * j / n), y + (r - 18) * np.sin(a0 + 2 * np.pi * (10 / 60) * k * j / n)) for j in range(n + 1)]
        cv.shape(poly(pts), pbox(pts, 4), ramp('#ff5a3a', '#c83a20', '#ff9a80'), ow=0, shadow=0, alpha=0.85)
    for j in range(12):
        a = a0 + 2 * np.pi * j / 12
        line(cv, [(x + (r - 30) * np.cos(a), y + (r - 30) * np.sin(a)), (x + (r - 12) * np.cos(a), y + (r - 12) * np.sin(a))], 8, INKC)
    a = a0 + 2 * np.pi * (10 / 60) * k
    line(cv, [(x, y), (x + (r - 40) * np.cos(a), y + (r - 40) * np.sin(a))], 14, DARK, ow=2)
    disc(cv, x, y, 18, DARK, ow=2)


def missile(cv, x, y, s, a=1.0):
    body_ = [(x - 26 * s, y), (x - 26 * s, y - 300 * s), (x, y - 380 * s), (x + 26 * s, y - 300 * s), (x + 26 * s, y)]
    cv.shape(poly(body_), pbox(body_, 6), ramp('#d8dce4', '#8a92a0', '#ffffff'), ow=4, alpha=a)
    for sd in (-1, 1):
        fin = [(x + sd * 26 * s, y - 20 * s), (x + sd * 80 * s, y + 30 * s), (x + sd * 26 * s, y - 100 * s)]
        cv.shape(poly(fin), pbox(fin, 6), ramp('#e2483d', '#a82a26', '#ff8070'), ow=4, alpha=a)


# ---------------------------------------------------------------- beats
def b0_alarm(lt, dur, T):
    """Frame one: the TV is already flashing red, the radio rattling, and he's flying up off the couch."""
    sx_, sy_ = shake(max(lt, 0), 0.0, 22, 1.2, 50)
    cv = Canvas(sx_, -120 + sy_, 0.95)
    room(cv)
    tv(cv, 0, -300, 1.0, T, 'alert')
    radio(cv, 330, 180, 0.9, T, loud=1.0)
    box(cv, 330, 300, 230, 20, WOOD, r=6)
    box(cv, -40, 560, 520, 150, COUCH, r=60)                                     # couch back
    box(cv, -40, 700, 560, 90, COUCH, r=46)
    u = float(np.clip((lt + 0.4) / 0.7, 0, 1))
    hop = 260 * np.sin(np.pi * min(u, 1.0)) if u < 1 else 60 * abs(np.sin(lt * 9)) * np.exp(-(lt - 0.3) * 2)
    guy(cv, -120, 820 - hop, 0.85, face='shock', arms=(reach(-1, -220, -760), reach(1, 220, -760)))
    rr = np.random.default_rng(3)
    for j in range(10):                                                         # popcorn flying
        ph = ((lt + 0.4) * 1.3 + j * 0.1) % 1.6
        px, py = -120 + rr.uniform(-300, 300), 500 - 700 * ph + 500 * ph * ph
        disc(cv, px, py, 18, ramp('#fff4c0', '#e0c880', '#ffffff'), ow=2)
    hook_text(cv, 'ALERT!', lt, y=-800, size=170, color=ALR)
    return cv


def b1_test(lt, dur, T):
    cv = Canvas(0, -160, 1.15)
    room(cv)
    tv(cv, 0, -320, 1.0, T, 'test')
    box(cv, 0, 360, 420, 40, WOOD, r=10)                                        # coffee table
    px, py = 120, 300
    box(cv, px, py, 70, 34, DARK, r=12)                                         # the phone, lying quiet
    box(cv, px, py, 60, 26, ramp('#101218'), r=8, ow=0, shadow=0)
    for j in range(3):
        ph = (lt * 0.6 + j / 3) % 1
        label(cv, 'z', px + 60 + 30 * j, py - 60 - 160 * ph, 44 + 14 * j, WHT, a=1 - ph)
    slabel(cv, 'PHONES: QUIET', 0, 520, 90, (120, 255, 160), a=ease(np.clip((lt - dur * 0.45) / 0.3, 0, 1)))
    return cv


def b2_button(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1d3f8a', '#0a1a3a', vignette=0.4)
    for j in range(7):                                                          # flag stripes behind
        box(cv, 0, -900 + j * 120, 700, 60, ramp('#c8202a' if j % 2 == 0 else '#f4f1ea'), r=0, ow=0, shadow=0, alpha=0.35)
    box(cv, -330, -700, 250, 200, ramp('#1a2f6a'), r=0, ow=0, shadow=0, alpha=0.5)
    box(cv, 0, 420, 700, 260, WOOD, r=20)                                       # the desk
    red_button(cv, 0, 80, 1.3, press=float(np.clip((lt - dur * 0.6) / 0.15, 0, 1)), T=T)
    k = ease(np.clip((lt - 0.2) / (dur * 0.5), 0, 1))                           # a hand in a suit sleeve comes in
    hx, hy = 520 - 470 * k, -560 + 420 * k
    line(cv, [(900, -1000), (hx + 60, hy - 60)], 120, ramp('#2b2f38', '#191c22', '#454b57'), ow=4)
    line(cv, [(hx + 70, hy - 70), (hx + 40, hy - 40)], 110, WHITE, ow=4)
    disc(cv, hx, hy, 70, SKIN, ow=4)
    line(cv, [(hx - 20, hy + 20), (hx - 60, hy + 90)], 36, SKIN, ow=4)
    sbadge(cv, 'ONLY THE PRESIDENT', -760, (255, 210, 80))
    return cv


def b3_map(lt, dur, T):
    cv = Canvas(0, -40, 1.0)
    cv.background(*SEA, vignette=0.35)
    s = 0.98
    usmap(cv, s)
    ox, oy = proj(*DC, s)
    R = 1200 * ease(np.clip((lt - 0.2) / (dur * 0.7), 0, 1))
    if 0 < R < 1190:
        cv.glow(circle(ox, oy, R), (ox - R - 80, oy - R - 80, ox + R + 80, oy + R + 80), '#ff5a3a', 26, 0.6)
    n_lit = 0
    for lo, la in STATIONS:
        x, y = proj(lo, la, s)
        d = np.hypot(x - ox, y - oy); lit = float(np.clip((R - d) / 60, 0, 1)); n_lit += lit > 0.5
        mini_tower(cv, x, y + 14, 0.75, lit, T)
    disc(cv, ox, oy, 22, BTN, ow=3)
    slabel(cv, '%d STATIONS' % max(n_lit, 1) if n_lit < 80 else '~80 STATIONS', 0, -700, 120, (255, 120, 90))
    return cv


def b4_bunker(lt, dur, T):
    cv = Canvas(0, 60, 1.0); U = -300
    flash = 1.0 if (lt % 1.7) < 0.08 else 0.0
    cv.background('#3a4458' if flash else '#1e2433', '#0e1220', vignette=0.3)
    rr = np.random.default_rng(int(T * 20))
    for j in range(40):                                                         # rain
        x = rr.uniform(-560, 560); y = rr.uniform(-1000, -380)
        line(cv, [(x, y), (x - 30, y + 90)], 4, flat(hexc('#9ab8e8')), a=0.5)
    if flash:
        pts = [(-300, -1000), (-240, -760), (-320, -700), (-200, -420)]
        line(cv, pts, 14, flat(hexc('#fff8c0')), a=1.0)
    tower(cv, 260, -60 + U, 0.7, T, lit=0.8)
    box(cv, 0, 560 + U, 1400, 620, ramp('#6a4a2a', '#3a2814', '#8a6a4a'), r=0, ow=0, shadow=0)     # the ground, cut away
    box(cv, -60, 520 + U, 400, 280, CONC, r=30)                                     # the shelter: thick concrete
    box(cv, -60, 520 + U, 330, 210, ramp('#2a3040', '#1a1e28', '#3a4256'), r=16, ow=0, shadow=0)
    box(cv, -200, 640 + U, 80, 70, ramp('#e2b03d', '#a8801a', '#ffd870'), r=10)    # generator
    for j in range(3):
        line(cv, [(-250 + 30 * j, 600 + U), (-250 + 30 * j, 680 + U)], 5, DARK)
    box(cv, 90, 640 + U, 110, 30, WOOD, r=6)                                        # the mic desk
    line(cv, [(90, 610 + U), (90, 540 + U)], 8, METAL, ow=2)
    disc(cv, 90, 525 + U, 22, DARK, ow=2)
    on = (T * 2) % 1 < 0.6
    label(cv, 'ON AIR', 60, 380 + U, 44, (255, 80, 60) if on else (90, 40, 40), stroke=0)
    k = ease(np.clip((lt - 0.3) / 0.6, 0, 1))                                   # the heavy round door swings shut
    dx = 270 + 80 * (1 - k)
    cv.shape(ellipse(dx, 520 + U, 40 + 60 * k, 150), (dx - 110, 360 + U, dx + 110, 680 + U), METAL, ow=5)
    if k > 0.6:
        for j in range(4):
            a = j * np.pi / 2 + k * 2
            line(cv, [(dx, 520 + U), (dx + 50 * k * np.cos(a), 520 + U + 100 * np.sin(a))], 10, DARKM, ow=2)
    hook_text(cv, 'BUILT TO LAST', lt, y=-800, size=130, color=(160, 210, 255), pop_t=0.35)
    return cv


def b5_chain(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a3a6a', '#101830', vignette=0.35)
    box(cv, 0, 600, 1400, 360, ramp('#3a6a3a', '#1f3f1f', '#5a8a5a'), r=0, ow=0, shadow=0)
    xs = [-420, -140, 140, 420]
    u = float(np.clip((lt - dur * 0.35) / (dur * 0.5), 0, 1))
    for i, x in enumerate(xs):
        lit = float(np.clip(u * 4.5 - i, 0, 1))
        tower(cv, x, 250, 0.6, T + i, lit=lit)
        if lit == 0 and i > 0:                                                  # listening: little ear-dots
            for k in range(3):
                dot(cv, x - 60 - 20 * k, -120, 6, flat(hexc('#9ae8ff')), a=0.4 + 0.4 * np.sin(T * 6 - k))
    for j in range(12):                                                         # dominoes falling in step
        x = -500 + j * 90
        f = float(np.clip(u * 13 - j, 0, 1))
        ang = np.radians(-75 * ease(f))
        cx, cy = x + 60 * np.sin(-ang) * 0.5, 820
        pts = [(x + np.cos(ang) * dx - np.sin(ang) * dy, 820 + np.sin(ang) * dx + np.cos(ang) * dy) for dx, dy in ((-24, 0), (24, 0), (24, -200), (-24, -200))]
        cv.shape(poly(pts), pbox(pts, 6), ramp('#f4f1ea', '#c9c3b8', '#ffffff'), ow=3)
        for dy in (-55, -145):
            dot(cv, x - np.sin(ang) * dy, 820 + np.cos(ang) * dy, 8, INKC)
    hook_text(cv, 'PASS IT ON!', lt, y=-800, size=140, color=(255, 120, 90), pop_t=dur * 0.35)
    if lt < dur * 0.35:
        sbadge(cv, 'ALWAYS LISTENING', -760, (154, 232, 255))
    return cv


def b6_code(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#102030', '#060c14', vignette=0.4)
    box(cv, 0, -360, 500, 180, ramp('#0a1a12', '#050e08', '#123222'), r=24, ow=5)   # scope screen
    pts = []
    for j in range(120):                                                        # buzzy bursts
        x = -470 + j * 7.9
        burst = ((x + T * 300) % 300) < 180
        y = -360 + (70 * np.sign(np.sin(j * 1.9 + T * 40)) if burst else 0)
        pts.append((x, y))
    line(cv, pts, 6, flat(hexc('#5aff8a')), a=0.95)
    k = float(np.clip((lt - 0.4) / 1.0, 0, 1))
    rr = np.random.default_rng(int(T * 10))
    for j in range(int(18 * k)):                                                # it turns into code
        ph = ((T * 0.5 + j / 18) % 1)
        x = -400 + 800 * ph; y = -100 + 60 * np.sin(j)
        label(cv, '1' if rr.random() < 0.5 else '0', x, y + 200 * ph, 54, (90, 255, 140), a=min(1, 2 * (1 - ph)))
    box(cv, 0, 380, 300, 170, METAL, r=26, ow=5)                                # the decoder box
    box(cv, 0, 350, 230, 80, ramp('#0a1a12'), r=10, ow=0, shadow=0)
    words = ['TORNADO', 'FLOOD', 'AMBER', 'TEST']
    wsel = words[min(int(lt / max(dur, 0.1) * 6) % 4, 3)] if lt < dur * 0.7 else 'TEST'
    label(cv, wsel, 0, 360, 72, (90, 255, 140), stroke=0)
    for j in range(3):
        disc(cv, -150 + j * 60, 480, 16, ramp('#5aff8a' if (T * 3 + j) % 1 < 0.5 else '#204a30'), ow=2)
    sbadge(cv, "IT'S CODE", -780, (90, 255, 140))
    return cv


def b7_reach(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1a4a', '#120a24', vignette=0.35)
    k = ease(np.clip((lt - 0.2) / (dur * 0.7), 0, 1))
    clock(cv, 0, -500, 250, k)
    slabel(cv, '10 MIN', 0, -180, 110, (255, 120, 90))
    for i in range(10):
        x = -405 + i * 90
        person(cv, x, 100, 1.05, lit=(i < 9 and i < k * 11))
    slabel(cv, '9 OUT OF 10', 0, 640, 120, YEL, a=ease(np.clip((lt - dur * 0.4) / 0.3, 0, 1)))
    return cv


def b8_fail(lt, dur, T):
    cv = Canvas(0, -160, 1.1)
    room(cv)
    party = lt > dur * 0.45
    tv(cv, 0, -320, 1.0, T, 'party' if party else 'static')
    guy(cv, 260, 820, 0.8, face='worried', arms=(reach(-1, 60, -620), reach(1, 140, -700)), tilt_head=-0.15)
    if not party:
        slabel(cv, '2011 TEST', 0, -790 + 160, 110, (255, 160, 90))
    else:
        hook_text(cv, 'OOPS!', lt, y=-780, size=150, color=(255, 122, 208), pop_t=dur * 0.45)
    return cv


def b9_cuba(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#6a2a1a', '#200a08', vignette=0.45)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    missile(cv, 0, 760 - 900 * k, 1.1)
    for j in range(10):                                                         # the smoke trail
        y = 800 - 900 * k + 60 + j * 60
        disc(cv, 20 * np.sin(j * 1.3 + T * 3), y, 50 + 6 * j, ramp('#c8c0b8', '#8a8078', '#f0e8e0'), ow=2, alpha=max(0.0, 0.9 - j * 0.08))
    box(cv, -280, 520, 200, 150, OLD, r=40, ow=5)                               # an old 1960s TV in the corner
    box(cv, -300, 520, 140, 110, ramp('#c8ccd0', '#8a9098', '#f0f4f8'), r=30, ow=0, shadow=0)
    label(cv, 'WARNING', -300, 520, 46, (40, 40, 48), stroke=0)
    line(cv, [(-330, 370), (-400, 260)], 6, METAL)
    line(cv, [(-250, 370), (-180, 260)], 6, METAL)
    sbadge(cv, '1962: MISSILE SCARE', -780, (255, 160, 90))
    return cv


def b10_never(lt, dur, T):
    cv = Canvas(0, 0, 1.0 + 0.08 * ease(np.clip(lt / dur, 0, 1)))
    cv.background('#141820', '#05070a', vignette=0.6)
    cv.glow(ellipse(0, -100, 420, 900), (-600, -1000, 600, 800), '#fff4d0', 140, 0.25)        # a lone spotlight
    box(cv, 0, 420, 360, 90, WOOD, r=16)
    red_button(cv, 0, 200, 1.4, dust=1.0, glow=0.3, T=T)
    cobweb(cv, -540, -960, 1.6)
    cobweb(cv, 260, 50, 0.6, a=0.8)
    sy = -300 + 40 * np.sin(T * 1.5)                                            # a spider letting itself down
    line(cv, [(130, -960), (130, sy)], 2, flat(hexc('#e8e8f0')), a=0.7)
    disc(cv, 130, sy, 18, DARK, ow=2)
    for j in range(4):
        for sd in (-1, 1):
            line(cv, [(130, sy), (130 + sd * 30, sy - 12 + 8 * j), (130 + sd * 40, sy + 4 + 8 * j)], 3, INKC)
    hook_text(cv, 'NEVER USED', lt, y=-780, size=150, color=(255, 236, 80), pop_t=0.3)
    return cv


BEATS = [b0_alarm, b1_test, b2_button, b3_map, b4_bunker, b5_chain, b6_code, b7_reach, b8_fail, b9_cuba, b10_never]

if __name__ == '__main__':
    run(BEATS)
