#!/usr/bin/env python3
"""The week America's systems kept crashing (Google's top US searches Nov 17 2026: 'nsa' #1, 'apple outage' #2).
Opens on a jet rolling to a stop while the departures board flips to CANCELED; the little router in El Dorado, Arkansas
flooding the network; the old radar computer drowning in calls; the map: 17 of 22 air traffic centers going red; Monday's
bank lockout; today's NSA network down; Apple's update breaking iCloud sign-in; 'were we hacked?' stamped NO; one mistake
spreading through a data center like dominoes; the 2024 CrowdStrike crash: screens going blue by the millions; the payoff:
it all came from one bad file.
Facts: FAA 'Nationwide Ground Stop: Q&A' (Nov 13 2026: ~1,000 connection attempts every 4-5 s from a new router at El
Dorado, AR; 17 of 22 centers; ~12,462 flights canceled; no sign of a cyberattack). BNN Bloomberg live (Nov 17): Monday's
software bug at Chase and other banks; NSA network 'temporary degradation' during scheduled maintenance; Apple's internal
update; DNI and DHS: not a cyberattack. 24/7 Wall St (Apple status page): iCloud sign-in 'All users are affected'.
IBM (July 2024): CrowdStrike's faulty update hit ~8.5 million Windows devices; flights, hospitals and banks; 'not a
cyberattack'."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403
import eas as E

DIVE = {}
ALR = (255, 70, 60)
JET = ramp('#f4f6fa', '#b8c0cc', '#ffffff')
TAR = ramp('#3a3f48', '#22262c', '#555b66')
BOXC = ramp('#2b2f38', '#191c22', '#454b57')
BEIGE = ramp('#e8dcc0', '#b8a888', '#fff4dc')
BLUE_S = ramp('#1a6ad8', '#0f4aa0', '#3a8af0')
RACK = ramp('#3a4050', '#22262f', '#566070')


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def jet(cv, x, y, s, tilt=0.0):
    """side view airliner, nose to the right"""
    pts = [(x - 330 * s, y - 20 * s), (x + 250 * s, y - 40 * s), (x + 330 * s, y), (x + 250 * s, y + 40 * s), (x - 330 * s, y + 30 * s)]
    cv.shape(poly(pts), pbox(pts, 8), JET, ow=5)
    tail = [(x - 330 * s, y - 20 * s), (x - 380 * s, y - 170 * s), (x - 290 * s, y - 170 * s), (x - 220 * s, y - 25 * s)]
    cv.shape(poly(tail), pbox(tail, 8), ramp('#1a4f9a', '#0d2a5a', '#3a72c8'), ow=5)
    wing = [(x - 40 * s, y + 10 * s), (x - 170 * s, y + 110 * s), (x - 90 * s, y + 110 * s), (x + 60 * s, y + 10 * s)]
    cv.shape(poly(wing), pbox(wing, 8), ramp('#c8d0dc', '#8a92a0', '#e8eef6'), ow=4)
    box(cv, x - 60 * s, y + 70 * s, 50 * s, 22 * s, METAL, r=18 * s)              # engine
    for j in range(8):
        disc(cv, x - 200 * s + j * 50 * s, y - 8 * s, 9 * s, ramp('#2a5a9a'), ow=2)
    for wx in (x - 150 * s, x + 200 * s):
        line(cv, [(wx, y + 35 * s), (wx, y + 80 * s)], 8 * s, DARK)
        disc(cv, wx, y + 90 * s, 16 * s, DARK, ow=2)


def board(cv, x, y, s, T, flip):
    """departures board: rows flip from ON TIME to CANCELED one by one"""
    box(cv, x, y, 420 * s, 300 * s, BOXC, r=20 * s, ow=5)
    label(cv, 'DEPARTURES', x, y - 250 * s, 56 * s, (255, 210, 80), stroke=0)
    cities = ['DALLAS', 'DENVER', 'CHICAGO', 'ATLANTA', 'NEW YORK', 'MIAMI']
    for i, c in enumerate(cities):
        yy = y - 160 * s + i * 76 * s
        box(cv, x, yy, 390 * s, 32 * s, ramp('#101218'), r=6 * s, ow=0, shadow=0)
        label(cv, c, x - 200 * s, yy, 40 * s, (230, 230, 240), stroke=0)
        f = float(np.clip(flip * 7 - i, 0, 1))
        if f < 0.5:
            label(cv, 'ON TIME', x + 210 * s, yy, 40 * s, (90, 255, 140), stroke=0)
        else:
            label(cv, 'CANCELED', x + 200 * s, yy, 40 * s, (255, 80, 60), stroke=0)


def router(cv, x, y, s, T, angry=0.0):
    jx = 8 * angry * np.sin(T * 60)
    box(cv, x + jx, y, 240 * s, 80 * s, BOXC, r=24 * s, ow=5)
    for sd in (-1, 1):                                                        # antennas
        line(cv, [(x + jx + sd * 170 * s, y - 60 * s), (x + jx + sd * 220 * s, y - 280 * s)], 14 * s, BOXC, ow=3)
    for j in range(6):                                                        # blinking lights
        on = ((T * (6 + 8 * angry) + j * 0.37) % 1) < 0.5
        disc(cv, x + jx - 150 * s + j * 60 * s, y + 30 * s, 12 * s, ramp('#5aff8a' if not angry or j % 2 else '#ff5a3a') if on else ramp('#204a30'), ow=2)
    ey = y - 20 * s                                                           # a little face
    for sd in (-1, 1):
        disc(cv, x + jx + sd * 60 * s, ey, 18 * s, WHITE, ow=3)
        dot(cv, x + jx + sd * 60 * s, ey + 2 * s, 8 * s, INKC)
        if angry > 0.3:
            line(cv, [(x + jx + sd * 30 * s, ey - 30 * s), (x + jx + sd * 85 * s, ey - 42 * s)], 7 * s, INKC)
    mw = 30 * s + 40 * s * angry
    cv.shape(ellipse(x + jx, ey + 34 * s, mw, 8 * s + 22 * s * angry), (x + jx - mw - 10, ey, x + jx + mw + 10, ey + 80 * s), DARK, ow=3)


def envelope(cv, x, y, s, a=1.0, col='#ffd23f'):
    box(cv, x, y, 34 * s, 22 * s, ramp(col), r=4 * s, ow=3, alpha=a)
    line(cv, [(x - 34 * s, y - 22 * s), (x, y + 4 * s), (x + 34 * s, y - 22 * s)], 4 * s, INKC, a=a)


def old_pc(cv, x, y, s, T, stress=0.0):
    jx = 5 * stress * np.sin(T * 47)
    box(cv, x + jx, y, 260 * s, 210 * s, BEIGE, r=30 * s, ow=5)
    box(cv, x + jx, y - 10 * s, 200 * s, 160 * s, ramp('#0a1a12', '#050e08', '#123222'), r=20 * s, ow=0, shadow=0)
    cx_, cy_ = x + jx, y - 10 * s
    for r in (50, 100, 150):                                                  # a radar screen
        line(cv, [(cx_ + r * s * np.cos(t), cy_ + r * s * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 40)], 3 * s, flat(hexc('#2a8a4a')))
    a = T * 2.5
    line(cv, [(cx_, cy_), (cx_ + 150 * s * np.cos(a), cy_ + 150 * s * np.sin(a))], 5 * s, flat(hexc('#5aff8a')))
    if stress > 0.4:                                                          # glitch bars
        rr = np.random.default_rng(int(T * 15))
        for j in range(5):
            yy = cy_ + rr.uniform(-140, 140) * s
            box(cv, cx_, yy, 200 * s, rr.uniform(4, 14) * s, ramp('#ff5a3a' if j % 2 else '#ffffff'), r=0, ow=0, shadow=0, alpha=0.6 * stress)
    box(cv, x + jx, y + 260 * s, 300 * s, 40 * s, BEIGE, r=10 * s)
    if stress > 0.6:                                                          # smoke
        for j in range(5):
            u = (T * 0.7 + j / 5) % 1
            disc(cv, x + jx + 120 * s + 40 * np.sin(j + T), y - 230 * s - 300 * s * u, (30 + 50 * u) * s, ramp('#8a8a90', '#5a5a60', '#b0b0b8'), ow=0, shadow=0, alpha=0.6 * (1 - u))


def phone(cv, x, y, s, T, kind='bank', k=1.0):
    box(cv, x, y, 190 * s, 360 * s, DARK, r=46 * s, ow=5)
    box(cv, x, y, 170 * s, 330 * s, ramp('#f4f6fa', '#d8dce4', '#ffffff') if kind != 'blue' else BLUE_S, r=34 * s, ow=0, shadow=0)
    if kind == 'bank':
        label(cv, 'MY BANK', x, y - 230 * s, 54 * s, (30, 60, 120), stroke=0)
        box(cv, x, y - 60 * s, 120 * s, 30 * s, ramp('#e0e4ea'), r=8 * s, ow=2)
        box(cv, x, y + 10 * s, 120 * s, 30 * s, ramp('#e0e4ea'), r=8 * s, ow=2)
        if k > 0.5:
            disc(cv, x, y + 140 * s, 70 * s, ramp('#ff5a3a', '#c83a20', '#ff9a80'), ow=4)
            label(cv, '!', x, y + 145 * s, 90 * s, WHT, stroke=0)
            label(cv, "CAN'T SIGN IN", x, y + 260 * s, 38 * s, (220, 40, 30), stroke=0)
    elif kind == 'cloud':
        cl = ramp('#9ad0ff', '#5a9ae0', '#d0ecff')
        jx = 0 if k < 0.5 else 6 * np.sin(T * 40)
        for dx, dy, r in ((-60, 0, 60), (0, -30, 80), (60, 0, 60)):
            disc(cv, x + dx + jx, y - 100 * s + dy * s, r * s, cl, ow=4)
        if k > 0.5:                                                           # it cracks
            line(cv, [(x + jx, y - 190 * s), (x - 20 * s + jx, y - 120 * s), (x + 15 * s + jx, y - 90 * s), (x - 10 * s + jx, y - 40 * s)], 8 * s, INKC)
        label(cv, 'SIGN IN', x, y + 80 * s, 50 * s, (40, 40, 60), stroke=0)
        if k > 0.5:
            label(cv, 'FAILED', x, y + 170 * s, 66 * s, (220, 40, 30), stroke=0)


def rack(cv, x, y, s, bad, T):
    box(cv, x, y, 90 * s, 380 * s, RACK, r=14 * s, ow=4)
    for j in range(9):
        yy = y - 320 * s + j * 80 * s
        box(cv, x, yy, 76 * s, 28 * s, ramp('#1a1e26'), r=6 * s, ow=0, shadow=0)
        for q in range(3):
            on = ((T * 5 + j * 0.3 + q * 0.21) % 1) < 0.6
            col = ('#ff3a2a' if bad else '#5aff8a') if on else '#203028'
            disc(cv, x - 50 * s + q * 22 * s, yy, 7 * s, ramp(col), ow=0, shadow=0)
    if bad:
        cv.glow(rbox(x, y, 90 * s, 380 * s, 14 * s), (x - 200 * s, y - 500 * s, x + 200 * s, y + 500 * s), '#ff3a2a', 50 * s, 0.35)


def bsod(cv, x, y, s, k):
    box(cv, x, y, 70 * s, 50 * s, BOXC, r=8 * s, ow=3)
    box(cv, x, y, 62 * s, 42 * s, BLUE_S if k > 0.5 else ramp('#d8e8f8'), r=4 * s, ow=0, shadow=0)
    if k > 0.5:
        label(cv, ':(', x - 20 * s, y - 8 * s, 34 * s, WHT, stroke=0)
    box(cv, x, y + 62 * s, 12 * s, 12 * s, BOXC, r=2 * s, ow=0)


def hooded(cv, x, y, s):
    """a faceless hacker in a hoodie (shadow figure)"""
    H = ramp('#1a1a22', '#0a0a10', '#2e2e3a')
    cv.shape(rbox(x, y + 150 * s, 160 * s, 180 * s, 70 * s), (x - 170 * s, y - 40 * s, x + 170 * s, y + 340 * s), H, ow=4)
    disc(cv, x, y - 30 * s, 110 * s, H, ow=4)
    cv.shape(ellipse(x, y - 10 * s, 70 * s, 80 * s), (x - 80 * s, y - 100 * s, x + 80 * s, y + 80 * s), ramp('#000000'), ow=0, shadow=0)
    for sd in (-1, 1):
        disc(cv, x + sd * 25 * s, y - 20 * s, 9 * s, ramp('#5aff8a'), ow=0, shadow=0)


# ---------------------------------------------------------------- beats
def b0_ground(lt, dur, T):
    """Frame one: a jet already rolling, braking hard; the board flipping to CANCELED row by row."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#f2a65a', '#6a3a7a', vignette=0.3)
    box(cv, 0, 560, 1400, 440, TAR, r=0, ow=0, shadow=0)
    for j in range(8):                                                       # runway dashes sliding by
        x = ((j * 240 - (lt + 0.6) * 500 * max(0.0, 1 - lt / 2.2)) % 1600) - 800
        box(cv, x, 300, 60, 10, ramp('#f4f1ea'), r=3, ow=0, shadow=0)
    u = float(np.clip((lt + 0.6) / 2.6, 0, 1))
    jx = -700 + 760 * (1 - (1 - u) ** 2.4)
    jet(cv, jx, 170, 1.0)
    if u < 1:
        for j in range(4):                                                   # brake smoke
            disc(cv, jx - 190 - j * 60, 265 + 6 * np.sin(T * 9 + j), 30 + 14 * j, ramp('#d8d8dc', '#a0a0a8', '#ffffff'), ow=0, shadow=0, alpha=max(0.0, 0.7 - j * 0.15) * (1 - u))
    board(cv, 0, -440, 0.85, T, float(np.clip(lt / (dur * 0.8), 0, 1)))
    hook_text(cv, 'GROUNDED!', lt, y=-820, size=150, color=ALR)
    return cv


def b1_router(lt, dur, T):
    cv = Canvas(0, -80, 1.15)
    cv.background('#2a3a5a', '#101830', vignette=0.35)
    box(cv, 0, 380, 900, 260, ramp('#5a4a3a', '#3a2a1a', '#7a6a5a'), r=0, ow=0, shadow=0)    # shelf
    box(cv, 0, 100, 500, 40, WOOD, r=10)
    angry = float(np.clip((lt - dur * 0.5) / 0.4, 0, 1))
    router(cv, 0, 0, 1.0, T, angry)
    if angry > 0:
        E.waves(cv, 0, -40, T, r0=280, n=3, col='#ff5a3a', a=angry, span=260, w=12, spd=2.4)
    sbadge(cv, 'ARKANSAS', -760, (255, 210, 80))
    slabel(cv, 'ONE NEW ROUTER', 0, -560, 90, WHT)
    return cv


def b2_flood(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a2a3a', '#0a1018', vignette=0.35)
    stress = float(np.clip(lt / (dur * 0.7), 0, 1))
    router(cv, -330, -420, 0.6, T, 1.0)
    old_pc(cv, 230, 120, 0.95, T, stress)
    rr = np.random.default_rng(5)
    n = int(14 + 50 * stress)
    for j in range(n):                                                       # the flood of calls
        u = (T * (0.9 + rr.uniform(0, 0.8)) + rr.uniform(0, 1)) % 1
        x = -330 + (560 + rr.uniform(-80, 80)) * u; y = -420 + 540 * u + rr.uniform(-160, 160) * np.sin(np.pi * u)
        envelope(cv, x, y, 1.1, a=min(1.0, 3 * (1 - u)))
    cnt = int(1000 * ease(np.clip(lt / (dur * 0.6), 0, 1)))
    slabel(cv, '%s CALLS' % format(cnt, ','), 0, -760, 110, (255, 210, 80))
    slabel(cv, 'EVERY 5 SECONDS', 0, -640, 70, WHT)
    return cv


CENTERS = [(-122, 37.5), (-118, 34), (-112, 33.4), (-111.9, 40.7), (-104.9, 39.7), (-122.3, 47.6), (-97, 32.8), (-95.4, 29.8),
           (-96.6, 40.8), (-94.6, 39.1), (-87.9, 41.9), (-84.4, 33.7), (-81.4, 28.5), (-80.2, 25.8), (-86.8, 36.2), (-81.7, 41.5),
           (-77, 38.9), (-73.9, 40.8), (-71.4, 42.4), (-93.3, 44.9), (-90.2, 38.6), (-106.6, 35.1)]           # 22 centers


def b3_map(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    cv.background(*E.SEA, vignette=0.35)
    E.usmap(cv, 0.98)
    k = ease(np.clip((lt - 0.1) / (dur * 0.55), 0, 1))
    bad = [i for i in range(22) if i not in (1, 7, 12, 13, 21)]              # 17 of 22 go red
    for i, (lo, la) in enumerate(CENTERS):
        x, y = E.proj(lo, la, 0.98)
        red = i in bad and bad.index(i) < k * 17.5
        jx = 5 * np.sin(T * 40 + i) if red else 0
        if red:
            cv.glow(circle(x + jx, y, 20), (x - 70, y - 70, x + 70, y + 70), '#ff3a2a', 26, 0.7)
        disc(cv, x + jx, y, 17, ramp('#ff3a2a' if red else '#5aff8a'), ow=3)
    n = int(sum(1 for i in bad if bad.index(i) < k * 17.5))
    slabel(cv, '%d OF 22 CENTERS' % n, 0, -680, 100, (255, 120, 90))
    c = int(12000 * ease(np.clip((lt - dur * 0.55) / (dur * 0.4), 0, 1)))
    if c > 0:
        slabel(cv, '%s+ CANCELED' % format(c, ','), 0, 620, 88, (255, 80, 60))
    return cv


def b4_bank(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    cv.background('#2a5a4a', '#0e2a20', vignette=0.35)
    k = float(np.clip((lt - 0.5) / 0.3, 0, 1))
    phone(cv, -160, -150, 1.2, T, 'bank', k)
    guy(cv, 300, 900, 0.85, face='worried' if k > 0.5 else 'calm', arms=(reach(-1, -150, -600), reach(1, 120, -720)))
    sbadge(cv, 'MONDAY: BANKS', -780, (154, 255, 190))
    return cv


def b5_nsa(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#141a28', '#05070c', vignette=0.45)
    box(cv, 0, 260, 520, 330, ramp('#2a3040', '#161a24', '#3a4256'), r=10, ow=5)           # the building
    for r_ in range(4):
        for c in range(7):
            on = ((T * 1.3 + r_ * 0.4 + c * 0.17) % 1) < 0.5 and lt < dur * 0.4
            box(cv, -390 + c * 130, 50 + r_ * 110, 40, 30, ramp('#ffe9a0' if on else '#1a1e28'), r=4, ow=0, shadow=0)
    for sd in (-1, 1):                                                        # dishes
        cv.shape(ellipse(sd * 330, -170, 110, 60), (sd * 330 - 120, -240, sd * 330 + 120, -100), METAL, ow=4)
        line(cv, [(sd * 330, -120), (sd * 330, -60)], 14, METAL, ow=2)
    off = lt > dur * 0.4
    box(cv, 0, -520, 330, 120, ramp('#0a0a12'), r=20, ow=5)
    label(cv, 'OFFLINE' if off else 'ONLINE', 0, -520, 110, (255, 70, 60) if off else (90, 255, 140), stroke=0)
    k = ease(np.clip((lt - dur * 0.5) / 0.25, 0, 1))
    if k > 0:
        x, y = W2(cv, 0, -300)
        label(cv, 'TOP SECRET', x, y, 100 * (2 - k), (255, 70, 60), a=k)
    sbadge(cv, 'TODAY: NSA', -780, (255, 210, 80))
    return cv


def b6_apple(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    cv.background('#3a3a4a', '#14141c', vignette=0.35)
    k = float(np.clip((lt - dur * 0.35) / 0.3, 0, 1))
    phone(cv, 0, -120, 1.35, T, 'cloud', k)
    cnt = int(1000000 * ease(np.clip((lt - dur * 0.45) / (dur * 0.4), 0, 1)))
    sbadge(cv, 'APPLE: ONE UPDATE', -780, (154, 208, 255))
    if k > 0.5:
        slabel(cv, 'ALL USERS', 0, 600, 130, (255, 80, 60))
    return cv


def b7_hacked(lt, dur, T):
    cv = Canvas(0, -40, 1.0)
    cv.background('#2a1a3a', '#0e0814', vignette=0.45)
    hooded(cv, 0, -200, 1.6)
    for j in range(16):                                                       # green code rain
        x = -480 + j * 64; y = -900 + ((T * 300 + j * 137) % 1300)
        label(cv, '1' if j % 3 else '0', x, y, 46, (90, 255, 140), a=0.35)
    k = float(np.clip((lt - dur * 0.6) / 0.15, 0, 1))
    if k > 0:
        s_ = 1.6 - 0.6 * k
        x, y = W2(cv, 0, -180)
        cv.shape(rbox(x, y, 360 * s_, 130 * s_, 30), (x - 400 * s_, y - 160 * s_, x + 400 * s_, y + 160 * s_), ramp('#e2483d', '#a82a26', '#ff8070'), ow=6, alpha=k)
        label(cv, 'NOT HACKED', x, y, 120 * s_, WHT, a=k)
    slabel(cv, 'HACKED?', 0, -760, 130, (255, 210, 80))
    return cv


def b8_spread(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    cv.background('#141c2a', '#060a10', vignette=0.4)
    box(cv, 0, 620, 1400, 300, ramp('#2a3040'), r=0, ow=0, shadow=0)
    u = float(np.clip((lt - dur * 0.3) / (dur * 0.6), 0, 1))
    for i in range(7):
        x = -480 + i * 160
        rack(cv, x, 220, 1.0, bad=(i < u * 8), T=T + i)
    k = ease(np.clip((lt - 0.2) / 0.5, 0, 1))                                 # the one bad file drops in
    disc(cv, -480, -500 + 380 * k, 34, ramp('#ff3a2a', '#b01a10', '#ff9a88'), ow=4)
    hook_text(cv, 'ONE MISTAKE', lt, y=-800, size=140, color=(255, 120, 90), pop_t=0.3)
    return cv


def b9_crowd(lt, dur, T):
    cv = Canvas(0, -60, 1.0)
    cv.background('#1a2030', '#080a10', vignette=0.4)
    k = float(np.clip((lt - 0.3) / (dur * 0.7), 0, 1))
    for r_ in range(8):
        for c in range(7):
            x = -420 + c * 140; y = -440 + r_ * 130
            d = np.hypot(c - 3, r_ - 3.5) / 5.0
            bsod(cv, x, y, 0.95, 1.0 if d < k * 1.2 else 0.0)
    cnt = int(8500000 * ease(k))
    slabel(cv, format(cnt, ','), 0, 620, 120, (90, 160, 255))
    sbadge(cv, '2024: CROWDSTRIKE', -780, (154, 208, 255))
    return cv


def b10_file(lt, dur, T):
    cv = Canvas(0, 0, 1.0 + 0.1 * ease(np.clip(lt / dur, 0, 1)))
    cv.background('#0a1a3a', '#03060e', vignette=0.55)
    icons = [('PLANES', -330, (255, 120, 90)), ('HOSPITALS', 0, (255, 160, 200)), ('BANKS', 330, (154, 255, 190))]
    for nm, x, col in icons:                                                  # frozen: blue tint + ice
        box(cv, x, -560, 140, 90, BLUE_S, r=20, ow=4)
        label(cv, nm, x, -560, 46, WHT, stroke=0)
        label(cv, 'FROZEN', x, -440, 40, (180, 220, 255), stroke=0)
    k = ease(np.clip((lt - 0.4) / 0.6, 0, 1))
    fx, fy, s = 0, 40, 1.0 + 0.6 * k                                         # the one bad file
    cv.glow(rbox(fx, fy, 160 * s, 200 * s, 20), (fx - 400 * s, fy - 400 * s, fx + 400 * s, fy + 400 * s), '#ff3a2a', 90 * s, 0.6 + 0.3 * np.sin(T * 5))
    pts = [(fx - 150 * s, fy - 190 * s), (fx + 70 * s, fy - 190 * s), (fx + 150 * s, fy - 110 * s), (fx + 150 * s, fy + 190 * s), (fx - 150 * s, fy + 190 * s)]
    cv.shape(poly(pts), pbox(pts, 8), ramp('#f4f6fa', '#c8ccd4', '#ffffff'), ow=6)
    for j in range(4):
        line(cv, [(fx - 100 * s, fy - 60 * s + j * 60 * s), (fx + 100 * s, fy - 60 * s + j * 60 * s)], 10 * s, flat(hexc('#ff5a3a')))
    hook_text(cv, 'ONE BAD FILE', lt, y=-800, size=140, color=(255, 90, 70), pop_t=dur * 0.45)
    return cv


BEATS = [b0_ground, b1_router, b2_flood, b3_map, b4_bank, b5_nsa, b6_apple, b7_hacked, b8_spread, b9_crowd, b10_file]

if __name__ == '__main__':
    run(BEATS)
