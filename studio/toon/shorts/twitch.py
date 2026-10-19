#!/usr/bin/env python3
"""Eye twitch. Opens on a huge close-up eye, the lower lid already jumping; loops back into it."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

IRIS = ramp('#4f8fd8', '#2a5a9a', '#9fd0ff')
NERVE = flat(hexc('#ffd23f'))


def tw(lt, rate=7.0, on=1.0):
    """Twitch amount: quick random jumps of the lower lid."""
    if on <= 0:
        return 0.0
    k = int(lt * rate)
    ph = lt * rate - k
    r = np.random.default_rng(k).uniform(0.4, 1.0) if np.random.default_rng(k + 99).random() > 0.3 else 0.0
    return on * r * np.exp(-ph * 4) * (0.6 + 0.4 * np.sin(ph * 40))


def eye(cv, x, y, s, T, twitch=0.0, look=(0.0, 0.0), xray=0.0, blink=0.0, red=0.0, brow=True, patch=(620, 520)):
    """Big cartoon eye on a patch of face. twitch lifts the lower lid in quick jumps."""
    pw, ph_ = patch
    face = rbox(x, y, pw * s, ph_ * s, min(pw, ph_) * 0.5 * s)
    cv.shape(face, (x - (pw + 20) * s, y - (ph_ + 20) * s, x + (pw + 20) * s, y + (ph_ + 20) * s), SKIN, ow=0, shadow=0)
    W_ = ramp('#ffffff', '#dfe4ea', '#ffffff') if red <= 0 else ramp('#ffe4e4', '#f0b8b8', '#ffffff')
    cv.shape(rotell(x, y, 300 * s, 170 * s, 0), (x - 310 * s, y - 180 * s, x + 310 * s, y + 180 * s), W_, ow=5)
    if red > 0:
        for k in range(6):
            a = k * 1.05
            line(cv, [(x + np.cos(a) * 280 * s, y + np.sin(a) * 140 * s), (x + np.cos(a) * 190 * s, y + np.sin(a) * 100 * s)], 4 * s,
                 flat(hexc('#e2483d')), a=red)
    ix, iy = x + look[0] * 90 * s, y + look[1] * 50 * s
    disc(cv, ix, iy, 115 * s, IRIS, ow=4)
    disc(cv, ix, iy, 55 * s, DARK, ow=0, shadow=0)
    disc(cv, ix + 35 * s, iy - 40 * s, 22 * s, ramp('#ffffff'), ow=0, shadow=0, flat=True)
    top = y - 170 * s + blink * 340 * s                                  # upper lid
    cv.shape(lambda X, Y: np.maximum(face(X, Y), Y - (top + 40 * s * (1 - ((X - x) / (330 * s)) ** 2))),
             (x - (pw + 20) * s, y - (ph_ + 20) * s, x + (pw + 20) * s, top + 60 * s), SKIN, ow=0, shadow=0.15)
    line(cv, [(x + u * 310 * s, top + 40 * s * (1 - u * u)) for u in np.linspace(-1, 1, 15)], 9 * s, INKC)
    for k in range(7):                                                   # lashes
        u = -0.75 + k * 0.25
        px, py = x + u * 310 * s, top + 40 * s * (1 - u * u)
        line(cv, [(px, py), (px + u * 30 * s, py - 50 * s)], 7 * s, INKC)
    lo = y + 170 * s - twitch * 70 * s                                   # lower lid, jumping up
    cv.shape(lambda X, Y: np.maximum(face(X, Y), (lo - 30 * s * (1 - ((X - x) / (330 * s)) ** 2)) - Y),
             (x - (pw + 20) * s, lo - 40 * s, x + (pw + 20) * s, y + (ph_ + 20) * s), SKIN, ow=0, shadow=0)
    line(cv, [(x + u * 300 * s, lo - 30 * s * (1 - u * u)) for u in np.linspace(-1, 1, 15)], 6 * s, flat(hexc('#c97f62')))
    if twitch > 0.25:
        for k in range(3):
            line(cv, [(x - 340 * s - k * 10 * s, lo + (k - 1) * 30 * s), (x - 400 * s - k * 10 * s, lo + (k - 1) * 40 * s)], 7 * s, INKC, a=twitch)
            line(cv, [(x + 340 * s + k * 10 * s, lo + (k - 1) * 30 * s), (x + 400 * s + k * 10 * s, lo + (k - 1) * 40 * s)], 7 * s, INKC, a=twitch)
    if brow:
        line(cv, [(x - 330 * s, y - 330 * s), (x, y - 380 * s), (x + 330 * s, y - 320 * s)], 40 * s, HAIR, ow=3, flat=False)
    if xray > 0:
        ring = subtract(rotell(x, y, 470 * s, 330 * s, 0), rotell(x, y, 330 * s, 190 * s, 0))
        cv.shape(ring, (x - 480 * s, y - 340 * s, x + 480 * s, y + 340 * s), MUSC, ow=4, alpha=0.75 * xray,
                 tint=('#ff3a2a', float(min(1, twitch * 1.5))) if twitch > 0 else None)
        for k in range(24):
            a = k * 2 * np.pi / 24
            line(cv, [(x + np.cos(a) * 350 * s, y + np.sin(a) * 210 * s), (x + np.cos(a) * 450 * s, y + np.sin(a) * 315 * s)], 5 * s,
                 flat(hexc('#a83a32')), a=0.6 * xray)


def nerve(cv, x0, y0, x1, y1, T, fire=0.0, k=1.0, s=1.0):
    pts = [(x0 + (x1 - x0) * u + 40 * np.sin(u * 7) * s, y0 + (y1 - y0) * u) for u in np.linspace(0, 1, 12)]
    n = max(2, int(len(pts) * k))
    line(cv, pts[:n], 14 * s, NERVE, ow=3)
    if fire > 0:
        rng = np.random.default_rng(int(T * 9))
        for j in range(3):
            u = (T * 2.5 + j / 3 + rng.uniform(0, 0.1)) % 1
            p = pts[min(int(u * (n - 1)), n - 1)]
            cv.glow(circle(p[0], p[1], 16 * s), (p[0] - 80, p[1] - 80, p[0] + 80, p[1] + 80), '#ffd23f', 40 * s, fire)


def b0_hook(lt, dur, T):
    """The lower lid is already jumping on frame one; before 0 the eye is calm (the loop)."""
    t = tw(lt + 0.4, 7, 1.0) if lt >= -0.05 else 0.0
    cv = Canvas(0, 60, 1.0)
    sky_bg(cv)
    eye(cv, 0, 60, 1.0, T, patch=(1600, 1800), twitch=max(t, 0.9 if 0 <= lt < 0.12 else 0), look=(0.1 * np.sin(T), 0))
    if lt >= 0:
        hook_text(cv, 'TWITCH', lt, y=-720, size=160, color=YEL)
    return cv


def b1_ring(lt, dur, T):
    k = ease(np.clip(lt / 0.6, 0, 1))
    bl = max(0, np.sin(np.clip((lt - dur * 0.5) / 0.4, 0, 1) * np.pi))
    cv = Canvas(0, 60, 0.95)
    sky_bg(cv)
    eye(cv, 0, 60, 1.0, T, xray=k, blink=bl, patch=(1600, 1800))
    label(cv, 'EYELID MUSCLE', 0, -420, 76, (255, 150, 140), a=k)
    return cv


def b2_nerve(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv = Canvas(0, 60, 0.9)
    sky_bg(cv)
    eye(cv, 60, 260, 0.8, T, xray=1.0, patch=(1600, 1800))
    brain(cv, -330, -680, 0.9)
    nerve(cv, -260, -560, 60, 120, T, fire=0.5 if k >= 1 else 0, k=k)
    label(cv, 'NERVE', 210, -360, 80, YEL)
    return cv


def b3_misfire(lt, dur, T):
    cv = Canvas(0, 60, 0.9)
    sky_bg(cv)
    stress = ease(np.clip(lt / 0.6, 0, 1))
    eye(cv, 60, 260, 0.8, T, xray=1.0, twitch=tw(lt, 6, stress * 0.6), patch=(1600, 1800))
    brain(cv, -330, -680, 0.9, hot=0.6 * stress)
    nerve(cv, -260, -560, 60, 120, T, fire=stress)
    for j in range(4):                                                   # sparks flying off the nerve
        ph = (lt * 2 + j / 4) % 1
        a = j * 1.6 + lt
        disc(cv, -100 + np.cos(a) * 140 * ph, -220 + np.sin(a) * 140 * ph, 10, YELLOW, ow=0, alpha=1 - ph)
    hook_text(cv, 'MISFIRE', lt, y=-760, size=140, pop_t=dur * 0.5, color=RED)
    return cv


def b4_jump(lt, dur, T):
    t = tw(lt, 9, 1.0)
    cv = Canvas(0, 150, 1.5)
    sky_bg(cv)
    eye(cv, 0, 60, 1.0, T, xray=0.6, twitch=t, patch=(1600, 1800))
    nerve(cv, -500, -500, -250, 140, T, fire=1.0)
    if t > 0.4:
        cv.flash('#ffd23f', 0.08)
    return cv


def b5_triggers(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky_bg(cv)
    items = ['coffee', 'phone', 'dry']
    for j, it in enumerate(items):
        u = ease(np.clip((lt - j * dur * 0.25) / 0.4, 0, 1))
        if u <= 0:
            continue
        x = -330 + j * 330
        sc = 0.6 + 0.4 * u
        if it == 'coffee':
            box(cv, x, 0, 95 * sc, 130 * sc, ramp('#f4f1ea'), r=30 * sc)
            box(cv, x, -100 * sc, 80 * sc, 20 * sc, ramp('#6e4122'), r=10 * sc, ow=0)
            cv.shape(subtract(circle(x + 120 * sc, 0, 55 * sc), circle(x + 120 * sc, 0, 30 * sc)), (x + 60 * sc, -60 * sc, x + 180 * sc, 60 * sc), ramp('#f4f1ea'))
            for q in range(3):
                ph = (lt + q / 3) % 1
                line(cv, [(x - 40 + q * 40, -150 - ph * 80), (x - 30 + q * 40, -200 - ph * 80)], 8, flat(hexc('#ffffff')), a=1 - ph)
        elif it == 'phone':
            box(cv, x, 0, 80 * sc, 150 * sc, DARK, r=20 * sc)
            box(cv, x, 0, 66 * sc, 130 * sc, ramp('#7fd0ff', '#3fa9e0', '#bfeaff'), r=12 * sc, ow=0)
            cv.glow(circle(x, 0, 60 * sc), (x - 200, -200, x + 200, 200), '#7fd0ff', 60, 0.3)
        else:
            drop(cv, x, 40 * sc, 50 * sc)
            line(cv, [(x - 70 * sc, -100 * sc), (x + 70 * sc, 100 * sc)], 18 * sc, flat(hexc('#e2483d')), ow=3)
        label(cv, ['COFFEE', 'SCREENS', 'DRY EYES'][j], x, 230, 52, WHT, a=u)
    label(cv, 'MAKES IT WORSE', 0, -500, 84, RED)
    return cv


def b6_cant_see(lt, dur, T):
    cv = Canvas(0, -300, 1.05)
    sky_bg(cv, ground=0)
    guy(cv, -250, 0, 0.95, face='worried', arms=((20, 100), (12, 0)))
    guy(cv, 250, 0, 0.95, face='calm', shirt=ORANGE, arms=((12, 0), (12, 0)))
    cloud(cv, -250, -1000, 230)
    eye(cv, -250, -1000, 0.36, T, twitch=tw(lt, 8, 1.0), brow=False, patch=(380, 260))       # how it feels: huge
    dot(cv, -250 + 34 * 0.95, -770 * 0.95, 3)
    label(cv, 'FEELS HUGE', -250, -1250, 54, YEL)
    label(cv, '???', 250, -980, 70, WHT)
    return cv


def b7_days(lt, dur, T):
    k = np.clip(lt / (dur * 0.8), 0, 1)
    cv = Canvas(0, 60, 0.9)
    sky_bg(cv)
    eye(cv, 0, 160, 0.8, T, patch=(1600, 1800), twitch=tw(lt, 7, max(0, 1 - k * 1.3)))
    badge(cv, f'DAY {1 + int(k * 3)}', y=-480, col=(120, 255, 140))
    if k > 0.85:
        hook_text(cv, 'GONE', lt, y=-760, size=140, pop_t=dur * 0.7, color=(120, 255, 140))
    return cv


def b8_fix(lt, dur, T):
    cv = Canvas(0, 60, 0.9)
    night = ease(np.clip(lt / (dur * 0.6), 0, 1))
    cv.background('#3fa2ee' if night < 0.5 else '#1b2350', '#bfe6ff' if night < 0.5 else '#3a3f7a', vignette=0.2)
    bed(cv, T, 0, 420, 0.9, face='closed')
    box(cv, 380, -40, 70, 90, ramp('#f4f1ea'), r=20)                     # coffee pushed away
    line(cv, [(300, -140), (460, 60)], 16, flat(hexc('#e2483d')), ow=3)
    for j in range(3):
        ph = (lt * 0.7 + j / 3) % 1
        label(cv, 'Z', 250 + 40 * j, -300 - 200 * ph, 50 + 20 * j, WHT, a=1 - ph)
    hook_text(cv, 'REST', lt, y=-800, size=150, pop_t=0.5, color=(120, 255, 140))
    return cv


BEATS = [b0_hook, b1_ring, b2_nerve, b3_misfire, b4_jump, b5_triggers, b6_cant_see, b7_days, b8_fix]

if __name__ == '__main__':
    run(BEATS)
