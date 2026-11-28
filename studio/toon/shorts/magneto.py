#!/usr/bin/env python3
"""'To me, my X-Men' (vidIQ's #1 rising YouTube search, week of Nov 26 2026, from the Avengers: Doomsday trailers).
The real science of a metal-bending magnet power. No Marvel art at all: no characters, costumes, helmets or logos; our own
horseshoe magnet, MRI, frog and lab. Hyped look (owner, Nov 21): vivid colour, flash + punch + confetti on every hit.
Opens on a storm of nails, wrenches and paper clips flying into a giant glowing magnet ('TO ME!'); the movie trick of pulling
iron out of blood; an MRI ~21,000x Earth's field; an oxygen tank ripped away and flung in; paper clips at 40 mph; your body's
~4 g of iron = one small nail; that iron isn't the kind magnets grab, your blood stays put in an MRI; but magnets CAN lift
you: the floating frog in a magnet ~10x an MRI, water pushing back, frog fine; payoff: the scientist won a joke prize for it,
then a real Nobel Prize ten years later.
Facts: vidIQ YouTube Trending (Nov 26 2026). ComicBookClubLive (Jan 6 2026: 'To Me, My X-Men' trailer). UCSF Radiology (1.5 T
MRI ~21,000x Earth's field; oxygen tanks, gurneys pulled in; paper clips up to ~40 mph). ScienceInsights (3-4 g iron, about
a small nail). McGill Reporter 'Ask an expert' (body iron 'is not ferromagnetic'; the MRI doesn't pull it). Harvard Gazette
(Apr 2024: frog levitated in a 10 T magnet, ~10x an MRI, by diamagnetism; unharmed). NPR (Oct 5 2010: Andre Geim, Ig Nobel
2000 for levitating frogs, Nobel Prize in Physics 2010 for graphene; first to win both)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403
from cullcity import hype   # the hyped look: colour boost, flash, punch, confetti, speed lines

DIVE = {}
MAGR = ramp('#ff2a3a', '#b01020', '#ff8a90')
TIPS = ramp('#e8eef6', '#a8b0bc', '#ffffff')
STEELC = ramp('#c8d0dc', '#8a92a0', '#f0f4fa')
FIELD = ['#2ae0ff', '#ff3ad0', '#ffd21a']
BLOOD = ramp('#e2283a', '#9a1020', '#ff7a88')
FROG = ramp('#5adf5a', '#2a9a2a', '#a0ff90')
MRIC = ramp('#f4f6fa', '#c8ccd8', '#ffffff')


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def horseshoe(cv, x, y, s, ang=0.0, glow=1.0):
    """a big red horseshoe magnet, open end pointing down (ang rotates), silver tips"""
    c, s_ = np.cos(ang), np.sin(ang)
    R = lambda px, py: (x + (px * c - py * s_) * s, y + (px * s_ + py * c) * s)
    arc = [R(170 * np.cos(t), -60 - 170 * np.sin(t)) for t in np.linspace(0, np.pi, 24)]
    line(cv, arc, 120 * s, MAGR, ow=6)
    for sd in (-1, 1):
        line(cv, [R(sd * 170, -60), R(sd * 170, 120)], 120 * s, MAGR, ow=6)
        px, py = R(sd * 170, 175)
        box(cv, px, py, 62 * s, 50 * s, TIPS, r=10 * s, ow=5)
    if glow > 0:
        gx, gy = R(0, 260)
        cv.glow(circle(gx, gy, 120 * s), (gx - 500 * s, gy - 400 * s, gx + 500 * s, gy + 500 * s), '#2ae0ff', 140 * s, 0.6 * glow)


def field_lines(cv, x, y, s, T, a=1.0, n=5, ang=0.0):
    for k in range(n):
        r = (80 + 60 * k) * s
        ph = (T * 1.5 + k * 0.2) % 1
        pts = [(x + r * np.cos(t), y + r * 0.9 * np.sin(t) + 60 * s) for t in np.linspace(0.15, np.pi - 0.15, 20)]
        line(cv, pts, 6, flat(hexc(FIELD[k % 3])), a=a * (0.5 + 0.5 * np.sin(np.pi * ph)))


def nail(cv, x, y, s, ang):
    c, s_ = np.cos(ang), np.sin(ang)
    p0 = (x - 60 * s * c, y - 60 * s * s_); p1 = (x + 60 * s * c, y + 60 * s * s_)
    line(cv, [p0, p1], 14 * s, STEELC, ow=3)
    disc(cv, p0[0], p0[1], 14 * s, STEELC, ow=3)


def wrench(cv, x, y, s, ang):
    c, s_ = np.cos(ang), np.sin(ang)
    p0 = (x - 80 * s * c, y - 80 * s * s_); p1 = (x + 80 * s * c, y + 80 * s * s_)
    line(cv, [p0, p1], 24 * s, STEELC, ow=3)
    disc(cv, p1[0], p1[1], 30 * s, STEELC, ow=3)
    disc(cv, p1[0] + 12 * s * c, p1[1] + 12 * s * s_, 14 * s, ramp('#1a1a2a'), ow=0)


def clip(cv, x, y, s, ang):
    c, s_ = np.cos(ang), np.sin(ang)
    pts = []
    for t in np.linspace(0, 1, 18):
        u = t * 3.2
        px = (-40 + 80 * (u % 1 if int(u) % 2 == 0 else 1 - u % 1)) * s
        py = (-18 + 12 * int(u)) * s
        pts.append((x + px * c - py * s_, y + px * s_ + py * c))
    line(cv, pts, 6 * s, ramp('#b0b8c8'), ow=2)


def mri(cv, x, y, s, T, glow=1.0):
    """an MRI: a big white ring with a bed through it"""
    cv.glow(circle(x, y, 300 * s), (x - 700 * s, y - 700 * s, x + 700 * s, y + 700 * s), '#2ae0ff', 160 * s, 0.4 * glow)
    disc(cv, x, y, 330 * s, MRIC, ow=6)
    disc(cv, x, y, 170 * s, ramp('#1a2a4a', '#0a1428', '#2a4070'), ow=5)
    box(cv, x, y + 380 * s, 300 * s, 40 * s, MRIC, r=10 * s, ow=4)
    box(cv, x, y + 100 * s, 360 * s, 26 * s, ramp('#2ae0ff', '#1a8ab0', '#8af0ff'), r=10 * s, ow=4)        # the bed
    on = (T * 2) % 1 < 0.6
    disc(cv, x + 250 * s, y - 220 * s, 18 * s, ramp('#2aff8a' if on else '#1a4a2a'), ow=3)


def tank(cv, x, y, s, ang):
    c, s_ = np.cos(ang), np.sin(ang)
    R = lambda px, py: (x + (px * c - py * s_) * s, y + (px * s_ + py * c) * s)
    pts = [R(-50, -170), R(50, -170), R(50, 170), R(-50, 170)]
    cv.shape(poly(pts), pbox(pts, 8), ramp('#3ad05a', '#1a8a3a', '#8af0a0'), ow=5)
    top = [R(-30, -230), R(30, -230), R(30, -170), R(-30, -170)]
    cv.shape(poly(top), pbox(top, 6), STEELC, ow=4)
    lx, ly = R(0, 0)
    label(cv, 'O2', lx, ly, 70 * s, WHT)


def frog(cv, x, y, s, T, happy=True):
    b = 6 * np.sin(T * 3)
    cv.shape(ellipse(x, y + b, 150 * s, 100 * s), (x - 170 * s, y - 120 * s, x + 170 * s, y + 120 * s), FROG, ow=5)
    for sd in (-1, 1):
        disc(cv, x + sd * 70 * s, y - 85 * s + b, 42 * s, FROG, ow=5)
        disc(cv, x + sd * 70 * s, y - 85 * s + b, 26 * s, WHITE, ow=3)
        dot(cv, x + sd * 72 * s, y - 82 * s + b, 12 * s, INKC)
        line(cv, [(x + sd * 110 * s, y + 50 * s + b), (x + sd * 190 * s, y + 120 * s + b + 10 * np.sin(T * 4 + sd))], 22 * s, FROG, ow=4)
        line(cv, [(x + sd * 80 * s, y + 80 * s + b), (x + sd * 120 * s, y + 160 * s + b)], 18 * s, FROG, ow=4)
    if happy:
        pts = [(x - 60 * s + 120 * s * u, y + 10 * s + b + 30 * s * np.sin(np.pi * u)) for u in np.linspace(0, 1, 12)]
        line(cv, pts, 8 * s, INKC)


def cell(cv, x, y, r, T, locked=True):
    cv.shape(ellipse(x, y, r, r * 0.8), (x - r - 10, y - r - 10, x + r + 10, y + r + 10), BLOOD, ow=4)
    cv.shape(ellipse(x, y, r * 0.5, r * 0.35), (x - r, y - r, x + r, y + r), ramp('#b01828'), ow=0, shadow=0)
    if locked:
        for k in range(4):                                                    # iron atoms held inside rings
            a = k * np.pi / 2 + T * 0.5
            ax, ay = x + r * 0.55 * np.cos(a), y + r * 0.45 * np.sin(a)
            pts = [(ax + 18 * np.cos(t), ay + 18 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 10)]
            line(cv, pts, 5, flat(hexc('#ffe9a0')))
            dot(cv, ax, ay, 8, flat(hexc('#ff8a2a')))


# ---------------------------------------------------------------- beats
def b0_tome(lt, dur, T):
    """Frame one: a storm of metal already flying up into a giant glowing magnet."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a1aa8', '#0a0630', vignette=0.35)
    tl = lt + 5
    horseshoe(cv, 0, -560, 1.25)
    field_lines(cv, 0, -300, 1.6, tl)
    rr = np.random.default_rng(7)
    for j in range(34):
        u = ((tl * 0.55) + j / 34) % 1
        x0 = rr.uniform(-520, 520); y0 = 1000
        x = x0 * (1 - u ** 1.6); y = y0 + (-330 - y0) * u ** 1.4
        ang = rr.uniform(0, 6.28) + tl * rr.uniform(3, 8)
        kind = j % 3
        s = 1.2 * (1 - 0.4 * u)
        (nail, wrench, clip)[kind](cv, x, y, s, ang)
    hook_text(cv, 'TO ME!', lt, y=-800, size=170, color=(255, 210, 26), pop_t=-10.0)
    return cv


def b1_movie(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#a81a4a', '#2a0618', vignette=0.35)
    pts = [(-560, 300 + 40 * np.sin(x / 80)) for x in range(0, 1)]
    box(cv, -60, 300, 640, 120, ramp('#ff5a6a', '#c8283a', '#ff9aa8'), r=120, ow=5)       # a blood vessel
    for j in range(6):
        u = (T * 0.4 + j / 6) % 1
        cell(cv, -560 + 1120 * u, 300 + 30 * np.sin(j), 46, T, locked=True)
    k = float(np.clip((lt - 0.4) / (dur * 0.6), 0, 1))
    horseshoe(cv, 0, -540, 0.8, glow=k)
    rr = np.random.default_rng(3)
    for j in range(int(30 * k)):                                              # 'movie' iron streaming out
        u = (T * 0.9 + j / 30) % 1
        x = rr.uniform(-400, 400) * (1 - u); y = 300 + (-330 - 300) * u
        dot(cv, x, y, 12, flat(hexc('#ffb02a')))
    sbadge(cv, 'IN THE MOVIES', -800, (255, 154, 168))
    return cv


def b2_mri(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#0a8ad8', '#1a0a5a', vignette=0.3)
    disc(cv, -330, -560, 90, ramp('#2a6ad8', '#123a8a', '#6ab0ff'), ow=4)                  # little Earth with its weak field
    for k in range(2):
        pts = [(-330 + (110 + 25 * k) * np.cos(t), -560 + (110 + 25 * k) * np.sin(t) * 0.8) for t in np.linspace(0, 2 * np.pi, 30)]
        line(cv, pts, 3, flat(hexc('#9ad8ff')), a=0.6)
    mri(cv, 80, 60, 1.1, T)
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    for j in range(6):
        r = (380 + 60 * j) * (0.6 + 0.4 * ((T * 0.8 + j / 6) % 1))
        pts = [(80 + r * np.cos(t), 60 + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 40)]
        line(cv, pts, 6, flat(hexc(FIELD[j % 3])), a=0.5 * k)
    slabel(cv, '%s x' % format(int(21000 * k), ','), 160, -700, 130, (255, 236, 80))
    slabel(cv, 'EARTH', -330, -420, 50, WHT)
    return cv


def b3_tank(lt, dur, T):
    sx_, sy_ = shake(max(lt - dur * 0.45, 0), 0.0, 16, 2.0, 40) if lt > dur * 0.45 else (0, 0)
    cv = Canvas(sx_, sy_, 1.0)
    cv.background('#1aa8a0', '#0a2a5a', vignette=0.3)
    mri(cv, 0, -320, 1.0, T)
    u = float(np.clip((lt - dur * 0.4) / 0.45, 0, 1))
    # he holds the tank out in front with both hands (one fixed pose, so nothing can snap); the magnet rips it away
    guy(cv, 300, 900, 0.75, face='shock' if u > 0.05 else 'calm',
        arms=(reach(-1, -170, -520), reach(1, -60, -520)))
    tx = 160 - 160 * u ** 2; ty = 520 - 820 * u ** 2
    if u < 1:
        tank(cv, tx, ty, 0.8, -1.4 + 2.6 * u)
    else:
        tank(cv, 0, -300, 0.55, 1.3)
    hook_text(cv, 'YANK!', lt, y=-800, size=170, color=(255, 236, 80), pop_t=dur * 0.42)
    return cv


def b4_clips(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#ff2a8a', '#3a0a5a', vignette=0.3)
    mri(cv, 0, -460, 0.75, T)
    rr = np.random.default_rng(11)
    for j in range(24):
        u = ((T * 1.4) + j / 24) % 1
        x0 = rr.uniform(-480, 480); y0 = 820
        x = x0 * (1 - u); y = y0 + (-460 - y0) * u
        clip(cv, x, y, 1.6, np.arctan2(-460 - y0, -x0) + 0.3)
        line(cv, [(x, y), (x + x0 * 0.12, y + 140)], 4, flat(hexc('#ffffff')), a=0.5)
    sp = int(40 * ease(np.clip(lt / (dur * 0.6), 0, 1)))
    box(cv, 0, -820, 230, 90, ramp('#0a0a1a'), r=24, ow=5)
    label(cv, '%d MPH' % sp, 0, -820, 110, (255, 236, 80), stroke=0)
    return cv


def b5_nail(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#ff8a1a', '#a81a3a', vignette=0.3)
    guy(cv, -200, 860, 0.85, face='happy', arms=(reach(-1, -200, -560), reach(1, 300, -700)))
    k = ease(np.clip((lt - 0.3) / (dur * 0.5), 0, 1))
    rr = np.random.default_rng(4)
    for j in range(int(40 * (1 - k))):                                        # iron dust gathering into one nail
        dot(cv, 160 + rr.uniform(-160, 160) * (1 - k), 140 + rr.uniform(-160, 160) * (1 - k), 10, flat(hexc('#ffb02a')))
    if k > 0.3:
        nail(cv, 160, 140, 2.2 * k, -0.6)
        cv.glow(circle(160, 140, 120), (-200, -200, 520, 480), '#ffe14d', 80, 0.6 * k)
    slabel(cv, '4 GRAMS', 0, -760, 150, WHT)
    slabel(cv, '= 1 SMALL NAIL', 0, -610, 90, (255, 236, 80), a=float(np.clip((lt - dur * 0.5) / 0.3, 0, 1)))
    return cv


def b6_stays(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a6ad8', '#3a0a6a', vignette=0.3)
    for j, (x, y) in enumerate(((-300, -480), (0, -560), (300, -470), (-150, -300), (170, -290))):
        cell(cv, x, y + 8 * np.sin(T * 2 + j), 70, T, locked=True)
    for k in range(4):                                                        # field sweeping past, nothing moves
        u = (T * 0.8 + k / 4) % 1
        x = -600 + 1200 * u
        line(cv, [(x, -800), (x + 60, -100)], 8, flat(hexc(FIELD[k % 3])), a=0.6)
    mri(cv, 0, 320, 0.7, T)
    guy(cv, 0, 470, 0.4, face='happy', arms=(reach(-1, -60, -350), reach(1, 60, -350)))
    sbadge(cv, 'BLOOD STAYS PUT', -800, (154, 255, 190))
    return cv


def b7_but(lt, dur, T):
    sx_, sy_ = shake(lt, 0.0, 10, 2.5, 30)
    cv = Canvas(sx_, sy_, 1.0 + 0.08 * ease(np.clip(lt / dur, 0, 1)))
    cv.background('#2a0a5a', '#05020e', vignette=0.5)
    horseshoe(cv, 0, -300, 1.3, glow=1.0)
    field_lines(cv, 0, -40, 2.0, T * 2)
    rr = np.random.default_rng(int(T * 15))
    for j in range(3):                                                        # crackling arcs
        pts = [(-210, 0)] + [(-210 + 420 * u, rr.uniform(-60, 60)) for u in np.linspace(0.1, 0.9, 6)] + [(210, 0)]
        line(cv, pts, 6, flat(hexc('#9af0ff')), a=0.8)
    hook_text(cv, 'BUT...', lt, y=-800, size=180, color=(42, 224, 255), pop_t=0.2)
    return cv


def b8_frog(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1ad88a', '#0a3a5a', vignette=0.3)
    box(cv, 0, -40, 300, 760, ramp('#e8eef6', '#a8b0bc', '#ffffff'), r=40, ow=6)        # the tall magnet, a tube through it
    box(cv, 0, -40, 170, 680, ramp('#0a1a3a', '#050a18', '#1a2a5a'), r=30, ow=4)
    for k in range(5):
        u = (T * 0.7 + k / 5) % 1
        line(cv, [(-150, 640 - 1360 * u), (150, 640 - 1360 * u)], 6, flat(hexc(FIELD[k % 3])), a=0.7 * np.sin(np.pi * u))
    k = ease(np.clip((lt - 0.3) / (dur * 0.5), 0, 1))
    fy = 520 - 640 * k + 20 * np.sin(T * 2.5) * k
    frog(cv, 0, fy, 0.75, T)
    cv.glow(ellipse(0, fy, 160, 110), (-400, fy - 300, 400, fy + 300), '#a0ff90', 80, 0.5 * k)
    hook_text(cv, 'FLOATING!', lt, y=-820, size=150, color=(255, 236, 80), pop_t=dur * 0.55)
    return cv


def b9_water(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2ab0ff', '#1a2a8a', vignette=0.3)
    fy = -200 + 18 * np.sin(T * 2.5)
    frog(cv, 0, fy, 1.4, T)
    k = float(np.clip(lt / (dur * 0.4), 0, 1))
    for sd in (-1, 0, 1):                                                     # water pushing up vs gravity pulling down
        x = sd * 220
        line(cv, [(x, 520), (x, 260 - 60 * k)], 30, ramp('#2ae0ff', '#1a8ab0', '#8af0ff'), ow=4)
        pts = [(x - 50, 280 - 60 * k), (x, 200 - 60 * k), (x + 50, 280 - 60 * k)]
        cv.shape(poly(pts), pbox(pts, 6), ramp('#2ae0ff'), ow=4)
    line(cv, [(360, -560), (360, -380)], 26, ramp('#ff7a2a', '#c84a10', '#ffb080'), ow=4)
    pts = [(315, -400), (360, -330), (405, -400)]
    cv.shape(poly(pts), pbox(pts, 6), ramp('#ff7a2a'), ow=4)
    label(cv, 'GRAVITY', 340, -620, 44, (255, 180, 120))
    slabel(cv, 'WATER PUSHES BACK', 0, -800, 74, WHT)
    slabel(cv, 'FROG: TOTALLY FINE', 0, 660, 80, (154, 255, 140), a=float(np.clip((lt - dur * 0.6) / 0.3, 0, 1)))
    return cv


def b10_nobel(lt, dur, T):
    cv = Canvas(0, 0, 1.0 + 0.05 * ease(np.clip(lt / dur, 0, 1)))
    cv.background('#ffb01a', '#a83a1a', vignette=0.35)
    k = float(np.clip((lt - dur * 0.42) / 0.3, 0, 1))
    if k < 1:                                                                 # the joke prize: a rubber-chicken-ish trophy
        box(cv, 0, 0, 160, 200, ramp('#c8c0b0', '#8a8070', '#f0e8d8'), r=20, ow=5, alpha=1 - k)
        label(cv, 'JOKE', 0, -40, 90, (60, 50, 40), stroke=0, a=1 - k)
        label(cv, 'PRIZE', 0, 60, 90, (60, 50, 40), stroke=0, a=1 - k)
        slabel(cv, '2000', 0, -620, 120, WHT, a=1 - k)
    if k > 0:
        cv.glow(circle(0, -40, 260), (-700, -700, 700, 600), '#ffe14d', 180, 0.7 * k)
        disc(cv, 0, -40, 240 * k, ramp('#ffd23f', '#d09a10', '#fff08a'), ow=6)
        disc(cv, 0, -40, 190 * k, ramp('#e8b020', '#b07a10', '#ffe070'), ow=0, shadow=0)
        label(cv, 'NOBEL', 0, -60, 90 * k, (120, 70, 10), stroke=0)
        label(cv, 'PRIZE', 0, 30, 70 * k, (120, 70, 10), stroke=0)
        slabel(cv, '2010', 0, -620, 120, WHT, a=k)
    frog(cv, 330, 520, 0.6, T)
    hook_text(cv, 'REAL NOBEL!', lt, y=-800, size=126, color=(255, 255, 255), pop_t=dur * 0.5)
    return cv


BEATS = [hype(b0_tome, (0.5,), speed=True), hype(b1_movie, (-0.45,)), hype(b2_mri, (-0.7,)), hype(b3_tank, (-0.42,)),
         hype(b4_clips, (-0.6,), speed=True), hype(b5_nail, (-0.5,)), hype(b6_stays, (-0.3,)), hype(b7_but, (0.2,)),
         hype(b8_frog, (-0.55,)), hype(b9_water, (-0.6,)), hype(b10_nobel, (-0.45, -0.5))]

if __name__ == '__main__':
    run(BEATS)
