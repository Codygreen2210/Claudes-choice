#!/usr/bin/env python3
"""How Scabs Work. Opens on a knee scraping along the ground; ends on the knee sliding in again."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

PLT = ramp('#f2c94c', '#c9992a', '#fff0a0')        # platelets
RBC = ramp('#d8343a', '#9a1f24', '#ff6a6a')
FIB = flat(hexc('#fff3c8'))
SCAB = ramp('#7a3a22', '#4e2414', '#a8603a')
NEWSKIN = ramp('#ffb0a8', '#e07c74', '#ffd6d0')
TOP = -40                      # skin surface in the cutaway


def cutaway(cv, T, gap=1.0, fill=0.0, scab=0.0, scabc=0.0, newskin=0.0, bleed=0.0):
    """Skin seen from the side with a V-shaped cut in the middle."""
    sky_bg(cv)
    w = 230 * gap
    skin = lambda X, Y: np.maximum(np.maximum(TOP - Y, Y - 700), -poly([(-w, TOP - 5), (w, TOP - 5), (0, TOP + 330 * gap)])(X, Y))
    cv.shape(skin, (-700, TOP - 10, 700, 710), SKIN, bevel=50)
    box(cv, 0, 520, 700, 180, ramp('#f6d9a8'), r=0, ow=3, shadow=0)            # fat layer
    for x in (-420, 380):
        line(cv, [(x, 600), (x + 40, 300), (x + 10, 120)], 22, ramp('#c0394a'), ow=3)  # vessels
    if newskin > 0:
        for sx in (-1, 1):
            cv.shape(poly([(sx * w, TOP), (sx * w * (1 - newskin), TOP), (0, TOP + 330 * gap * (1 - newskin) + 10), (sx * w * 0.3, TOP + 330 * gap)]),
                     (-w - 5, TOP - 5, w + 5, TOP + 340), NEWSKIN, ow=3)
    if bleed > 0:
        cv.shape(poly([(-w * 0.9, TOP + 10), (w * 0.9, TOP + 10), (0, TOP + 320 * gap)]), (-w, TOP, w, TOP + 330), RBC, ow=3, alpha=bleed)
        for k in range(3):
            ph = (T * 0.9 + k / 3) % 1
            disc(cv, -60 + k * 60, TOP - 10 - 120 * ph * 0, 18 + 6 * k, RBC, alpha=bleed)
    if scab > 0:
        cv.shape(smooth(30, rbox(0, TOP - 20, w + 40, 40, 30), poly([(-w, TOP), (w, TOP), (0, TOP + 300 * gap)])),
                 (-w - 50, TOP - 70, w + 50, TOP + 310), SCAB if scabc > 0.5 else RBC, ow=4, alpha=scab,
                 tint=('#5a2a18', float(scabc)) if scabc else None)


def b0_hook(lt, dur, T):
    """A leg slides across the ground; the scrape bleeds. Before 0 it's the slide coming in (the loop)."""
    p = lt + 1.5
    cv = Canvas(20, 230, 1.7)
    sky_bg(cv, ground=420)
    slide = min(p / 1.5, 1.0)
    x = -900 + 900 * ease(slide)
    cv.shape(capsule(x - 500, 200, x + 120, 300, 110, 95), (x - 620, 80, x + 230, 410), SKIN)
    cv.shape(capsule(x - 800, 160, x - 480, 200, 120), (x - 930, 30, x - 350, 330), JEANS)
    specks(cv, T, lambda i, v, tt: (x + 150 - v[0] * 300, 400 - v[1] * 120 * slide, (1 - slide * 0.7) if p < 1.5 else 0.2), 30, (170, 140, 110), 9, seed=2)
    if lt >= 0:
        r = ease(np.clip(lt / 0.6, 0, 1))
        cv.shape(rotell(40, 250, 120 * r + 1, 40 * r + 1, 8), (-90, 200, 170, 300), RBC, ow=3)
        for k in range(4):
            dy = 60 * ((lt * 0.8 + k / 4) % 1)
            disc(cv, -40 + k * 40, 285 + dy * r, 14 * r, RBC, ow=2)
        hook_text(cv, 'BODY SHIELD', lt, y=-640, pop_t=0.1, color=(255, 236, 80))
    return cv


def b1_platelets(lt, dur, T):
    cv = Canvas(0, 200, 1.45)
    cutaway(cv, T, bleed=0.8)
    for i in range(14):
        u = ((lt * 0.7 + i / 14) % 1)
        sx = -1 if i % 2 else 1
        x = sx * (420 - 250 * u); y = 450 - 380 * u + 20 * np.sin(i)
        cv.shape(rotell(x, y, 26, 12, 30 * sx), (x - 30, y - 30, x + 30, y + 30), PLT, ow=3)
    label(cv, 'PLATELETS', 0, -560, 76, (255, 220, 90))
    return cv


def b2_plug(lt, dur, T):
    cv = Canvas(0, 200, 1.59)
    cutaway(cv, T, bleed=0.6 * (1 - lt / dur))
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    rng = np.random.default_rng(3)
    for i in range(int(24 * k) + 2):
        a = rng.uniform(0, 1); sx = -1 if i % 2 else 1
        x = sx * 230 * (1 - a) * (0.3 + 0.7 * (1 - k * 0.6)); y = TOP + 330 * a * 0.9
        cv.shape(rotell(x, y, 24, 14, rng.uniform(0, 180)), (x - 30, y - 30, x + 30, y + 30), PLT, ow=3)
    hook_text(cv, 'PLUG', lt, y=-640, size=130, pop_t=dur * 0.5)
    return cv


def threads(cv, k, T, n=10):
    for i in range(n):
        a = i / n
        y0 = TOP + 20 + 280 * a
        w = 230 * (1 - a * 0.95)
        L = k * 2 * w
        pts = [(-w + u * L, y0 + 18 * np.sin(u * 9 + i + T)) for u in np.linspace(0, 1, 10)]
        line(cv, pts, 5, FIB, ow=2)


def b3_threads(lt, dur, T):
    cv = Canvas(0, 200, 1.67)
    cutaway(cv, T, bleed=0.3)
    threads(cv, ease(np.clip(lt / (dur * 0.8), 0, 1)), T)
    label(cv, 'STICKY THREADS', 0, -540, 70, (255, 243, 200))
    return cv


def b4_net(lt, dur, T):
    cv = Canvas(0, 200, 1.67)
    cutaway(cv, T, bleed=0.0)
    threads(cv, 1.0, T)
    rng = np.random.default_rng(5)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    for i in range(int(30 * k)):
        a = rng.uniform(0.05, 0.9); w = 230 * (1 - a)
        x = rng.uniform(-w * 0.8, w * 0.8); y = TOP + 300 * a
        disc(cv, x, y, 16, RBC, ow=3)
    if k > 0.9:
        hook_text(cv, 'BLEEDING STOPS', lt, y=-640, size=96, pop_t=dur * 0.62, color=(120, 255, 140))
    return cv


def b5_dry(lt, dur, T):
    cv = Canvas(0, 200, 1.59)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cutaway(cv, T, scab=1.0, scabc=k)
    for j in range(3):
        ph = (T * 0.7 + j / 3) % 1
        line(cv, [(-120 + j * 120, TOP - 90 - ph * 160), (-100 + j * 120, TOP - 150 - ph * 160)], 7, flat(hexc('#ffffff')), a=(1 - ph) * (1 - k))
    if k > 0.95:
        hook_text(cv, 'SCAB', lt, y=-640, size=140, pop_t=dur * 0.62)
    return cv


def b6_newskin(lt, dur, T):
    cv = Canvas(0, 200, 1.59)
    cutaway(cv, T, scab=0.5, scabc=1, newskin=ease(np.clip(lt / dur, 0, 1)) * 0.9)
    for sx in (-1, 1):
        arrows(cv, [((sx * 420, TOP + 140), (sx * 220, TOP + 140))], (255, 160, 150), 12)
    label(cv, 'NEW SKIN', 0, -540, 80, (255, 160, 150))
    return cv


def b7_falls(lt, dur, T):
    cv = Canvas(0, 200, 1.45)
    cutaway(cv, T, gap=0.05, newskin=1.0)
    k = ease(np.clip((lt - 0.4) / 1.2, 0, 1))
    put_y = TOP - 30 - 900 * k * k
    cv.shape(xform_rot(rbox(0, 0, 200, 34, 30), 0, put_y, 120 * k), (-260, put_y - 260, 260, put_y + 260), SCAB, ow=4)
    return cv


def xform_rot(f, x, y, deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return lambda X, Y: f((X - x) * c + (Y - y) * s, -(X - x) * s + (Y - y) * c)


def b8_pick(lt, dur, T):
    cv = Canvas(0, 200, 1.52)
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    cutaway(cv, T, gap=0.6, newskin=0.5, scab=1.0 - k, scabc=1.0, bleed=k * 0.9)
    fx, fy = 120 - 60 * k, TOP - 180 - 200 * k
    cv.shape(capsule(fx + 300, fy - 300, fx, fy, 60, 48), (fx - 70, fy - 370, fx + 370, fy + 70), SKIN)
    if k > 0.8:
        hook_text(cv, "DON'T PICK IT", lt, y=-640, size=100, pop_t=dur * 0.55, color=(255, 70, 60))
    return cv


BEATS = [b0_hook, b1_platelets, b2_plug, b3_threads, b4_net, b5_dry, b6_newskin, b7_falls, b8_pick]

if __name__ == '__main__':
    run(BEATS)
