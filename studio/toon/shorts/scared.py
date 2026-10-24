#!/usr/bin/env python3
"""Can you actually be scared to death? Opens mid-jump-scare: a sheet ghost lunges out of a closet and he's already
leaping and screaming; loops back into the lunge."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *
import rigsafe          # noqa: F401,F403

NIGHT = ('#1a1236', '#3a2a5e')
GHOSTC = ramp('#f6f4ff', '#c8c2e0', '#ffffff')
DOORC = ramp('#5a3a2a', '#3a2418', '#7a5038')
KID = ramp('#b8404e', '#7a2030', '#e47a88')
ADR = ramp('#ffd23f', '#d09a10', '#fff08a')
GRAYHAIR = ramp('#d8d8dc', '#a0a0a8', '#ffffff')
HOOD = ramp('#3a3f4a', '#22262e', '#5a6070')
WF = flat(hexc('#ffffff'))


def ghost(cv, x, y, s, T, a=1.0):
    """Classic sheet ghost: round head, flowing body, wavy hem, black eyes and a wide-open mouth."""
    def f(X, Y):
        body = smooth(40 * s, circle(x, y - 120 * s, 150 * s), rbox(x, y + 60 * s, 150 * s, 190 * s, 60 * s))(X, Y)
        hem = Y - (y + 220 * s + 26 * s * np.sin((X - x) / (34 * s) + T * 6))
        return np.maximum(body, hem)
    cv.shape(f, (x - 170 * s, y - 280 * s, x + 170 * s, y + 280 * s), GHOSTC, ow=5, alpha=a)
    for sx in (-1, 1):
        cv.shape(rotell(x + sx * 55 * s, y - 140 * s, 26 * s, 38 * s, 0), (x + sx * 55 * s - 30 * s, y - 180 * s, x + sx * 55 * s + 30 * s, y - 100 * s),
                 ramp('#1a1236'), ow=0, shadow=0, flat=True, alpha=a)
    cv.shape(rotell(x, y - 40 * s, 40 * s, 60 * s, 0), (x - 45 * s, y - 105 * s, x + 45 * s, y + 25 * s), ramp('#1a1236'), ow=0, shadow=0, flat=True, alpha=a)


def scared_guy(cv, T, x, y, s, jump=0.0, shake=0.0, arms=((150, 40), (150, 40))):
    sx_ = shake * 10 * np.sin(T * 60)
    yy = y - 120 * jump
    guy(cv, x + sx_, yy, s, face='scream', arms=arms)
    hx, hy = x + sx_, yy - 762 * s                                          # hair standing straight up
    for k in range(7):
        a = -0.9 + k * 0.3
        line(cv, [(hx + np.sin(a) * 80 * s, hy - 70 * s), (hx + np.sin(a) * 120 * s, hy - (150 + 20 * np.sin(k * 2.1)) * s)], 16 * s, HAIR, ow=3, flat=False)
    for k in range(3):                                                      # sweat flying off
        ph = (T * 2.5 + k / 3) % 1
        drop(cv, hx + (k - 1) * 120 * s + (k - 1) * 120 * ph, hy - 40 * s + 80 * ph, 12, a=1 - ph)


def kidney(cv, x, y, s, side, gland=0.0, T=0.0):
    f = subtract(rotell(x, y, 105 * s, 165 * s, 0), circle(x - side * 118 * s, y, 58 * s))
    cv.shape(f, (x - 130 * s, y - 185 * s, x + 130 * s, y + 185 * s), KID)
    g = 1 + 0.12 * gland * np.sin(T * 14)                                   # the adrenal gland cap on top
    cv.shape(poly([(x - 80 * s * g, y - 140 * s), (x + 80 * s * g, y - 140 * s), (x + 10 * s, y - 250 * s * g)]),
             (x - 100 * s, y - 280 * s, x + 100 * s, y - 120 * s), ADR, ow=4)


def ecg(cv, x, y, w, h, lt, mode):
    """Heart monitor. mode 0 = normal beats, 1 = wild quiver, blended by mode."""
    box(cv, x, y, w / 2 + 16, h / 2 + 16, ramp('#14181e', '#0a0c10', '#262c36'), r=20)
    xs = np.linspace(x - w / 2, x + w / 2, 90)
    u = (xs - xs[0]) / w * 4 + lt * 1.5
    norm = np.where((u % 1) < 0.08, -h * 0.42 * np.sin((u % 1) / 0.08 * np.pi), 0.0)
    wild = h * 0.25 * np.sin(u * 23) * np.sin(u * 7.3 + lt * 9)
    ys = y + norm * (1 - mode) + wild * mode
    line(cv, list(zip(xs, ys)), 6, flat(hexc('#3fe07a')), a=0.95)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """He's already mid-leap, screaming, on frame one; before 0 the ghost bursts out of the closet (the loop)."""
    cv = Canvas(0, 0, 1.0)
    cv.background(*NIGHT, vignette=0.45)
    box(cv, 0, 700, 1300, 420, ramp('#2a2040', '#1a1430', '#3a2e58'), r=0, ow=0, shadow=0)      # floor
    box(cv, 300, -60, 210, 380, DOORC, r=18)                                # the closet
    box(cv, 300, -60, 175, 345, ramp('#0a0614'), r=12, ow=3, shadow=0)
    lunge = ease(np.clip((lt + 0.5) / 0.45, 0, 1))
    ghost(cv, 300 - 170 * lunge, -80 - 40 * lunge, 0.9 + 0.35 * lunge, T)
    jump = max(0.0, np.sin(np.clip((lt + 0.12) / 0.5, 0, 1) * np.pi)) if lt > -0.12 else 0.0
    scared = 1.0 if lt > -0.12 else 0.0
    if scared:
        k_up = ease(float(np.clip((lt + 0.12) / 0.3, 0, 1)))            # arms fly up over ~9 frames, not in one
        scared_guy(cv, T, -200, 560, 1.25, jump=jump, shake=1.0, arms=rigsafe.blend_pose(((12, 0), (12, 0)), ((150, 40), (150, 40)), k_up))
    else:
        guy(cv, -200, 560, 1.25, face='calm', arms=((12, 0), (12, 0)))
    if lt >= 0:
        hook_text(cv, 'BOO!', lt, y=-790, size=200, color=(235, 230, 255))
    return cv


def b1_brain(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#141a3a', '#2a1f4e', vignette=0.4)
    brain(cv, 40, -60, 2.1)
    on = ease(np.clip((lt - 0.6) / 0.3, 0, 1))
    blink = 0.6 + 0.4 * np.sin(lt * 14)
    ax, ay = 40, 70                                                         # the amygdala, deep inside
    cv.glow(circle(ax, ay, 46), (ax - 240, ay - 240, ax + 240, ay + 240), '#ff3a3a', 110, 1.0 * on * blink)
    cv.shape(rotell(ax, ay, 46, 30, 20), (ax - 60, ay - 50, ax + 60, ay + 50), ramp('#ff4a4a', '#b02020', '#ff9a9a'), ow=4)
    for q in range(5):                                                      # signal racing in from the eye
        ph = (lt * 1.6 + q / 5) % 1
        disc(cv, -400 + (ax - 40 + 400) * ph, 300 + (ay - 300) * ph, 12, ramp('#ffe066'), ow=0, shadow=0)
    disc(cv, -400, 300, 60, ramp('#ffffff', '#d8dde4', '#ffffff'), ow=4)    # his eye
    disc(cv, -400, 300, 26, ramp('#3a2a1a'), ow=0, shadow=0)
    label(cv, 'AMYGDALA', ax, ay + 130, 60, (255, 120, 120), a=on)
    if on > 0.5:
        hook_text(cv, 'ALARM', lt, y=-720, size=170, pop_t=0.75, color=(255, 80, 80))
    return cv


def b2_glands(lt, dur, T):
    k = ease(np.clip((lt - 0.8) / (dur * 0.6), 0, 1))
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a1a26', '#2a0a12', vignette=0.35)
    vessel(cv, 330, x0=-700, x1=700, r=120)
    kidney(cv, -240, -40, 1.0, -1, gland=k, T=T)
    kidney(cv, 240, -40, 1.0, 1, gland=k, T=T)
    for q in range(4):                                                      # nerve signal arriving from above
        ph = (lt * 2 + q / 4) % 1
        line(cv, [(0, -700 + 500 * ph), (25, -660 + 500 * ph), (-15, -620 + 500 * ph), (10, -580 + 500 * ph)], 8, flat(hexc('#ffe066')), a=1 - ph)
    for q in range(int(26 * k)):                                            # adrenaline pouring into the blood
        side = -1 if q % 2 else 1
        ph = ((lt * 1.1 + q * 0.137) % 1)
        x = side * 240 + side * 20 * np.sin(q) - side * 200 * ph
        y = -270 + 600 * ph
        disc(cv, x, y, 14, ADR, ow=2)
    badge(cv, 'ADRENALINE', y=-620, col=YEL, w=480)
    return cv


def b3_body(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#141a3a', '#2a1f4e', vignette=0.35)
    beat = max(0, np.sin(lt * 13)) ** 3
    heart_icon(cv, 0, -470, 1.15, beat)
    label(cv, 'HEART', 0, -270, 56, WHT)
    p = ease(np.clip((lt - 1.4) / 0.8, 0, 1))                               # pupils blowing wide
    disc(cv, -270, 20, 140, ramp('#ffffff', '#d8dde4', '#ffffff'), ow=5)
    disc(cv, -270, 20, 76, ramp('#4a8ad8', '#2a5a9e', '#8ac0ff'), ow=0, shadow=0)
    disc(cv, -270, 20, 24 + 44 * p, ramp('#0a0a10'), ow=0, shadow=0)
    disc(cv, -300, -15, 14, ramp('#ffffff'), ow=0, shadow=0)
    label(cv, 'PUPILS', -270, 210, 56, WHT)
    m = ease(np.clip((lt - 2.6) / 0.8, 0, 1))                               # an arm flexing, bicep pumping up
    pump = 1 + 0.06 * m * np.sin(lt * 10)
    line(cv, [(130, 110), (330, 110)], 70, SKIN, ow=4, flat=False)
    line(cv, [(330, 110), (350, -90)], 60, SKIN, ow=4, flat=False)
    disc(cv, 352, -110, 52, SKIN, ow=4)
    cv.shape(rotell(230, 80, 85 * (0.75 + 0.35 * m) * pump, 55 * (0.75 + 0.45 * m) * pump, 0), (120, -20, 340, 160), SKIN)
    for q in range(5):
        ph = (lt * 1.5 + q / 5) % 1
        disc(cv, 140 + 180 * ph, 110 + 10 * np.sin(q), 9, ramp('#ff4a4a'), ow=0, shadow=0, alpha=m)
    label(cv, 'MUSCLES', 270, 210, 56, WHT)
    return cv


def b4_gut(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a3a1a', '#4a5a2a', vignette=0.35)
    stomach(cv, -60, -60, 0.95, T, acid=0.35)
    st = ease(np.clip((lt - 0.4) / 0.4, 0, 1))
    sx, sy = 260, -420                                                      # a big STOP sign on the gut
    oct_ = poly([(sx + 120 * st * np.cos(a), sy + 120 * st * np.sin(a)) for a in np.arange(8) * np.pi / 4 + np.pi / 8])
    cv.shape(oct_, (sx - 130, sy - 130, sx + 130, sy + 130), ramp('#e2483d', '#a82a22', '#ff8a7a'), ow=5)
    if st > 0.6:
        label(cv, 'STOP', sx, sy + 8, 64, WHT)
    later = ease(np.clip((lt - dur * 0.6) / 0.5, 0, 1))
    if later > 0:
        toilet(cv, 250, 300, 0.45 * later, T=T)
        label(cv, 'LATER...', 250, 90, 54, YEL, a=later)
    hook_text(cv, 'SICK', lt, y=-760, size=160, pop_t=dur * 0.3, color=(160, 230, 90))
    return cv


def b5_toxic(lt, dur, T):
    k = ease(np.clip(lt / (dur * 0.75), 0, 1))
    cv = Canvas(0, 0, 1.0)
    cv.background('#141a3a', '#2a1f4e', vignette=0.35)
    gx, gy, s_ = 0, 700, 1.1
    sh = 6 * k * np.sin(T * 50)
    guy(cv, gx + sh, gy, s_, face='scream', arms=((40, 30), (40, 30)))
    hx, hy = gx + sh + 10, gy - 520 * s_                                   # his heart, glowing through his shirt
    cv.glow(circle(hx, hy, 60), (hx - 260, hy - 260, hx + 260, hy + 260), '#ff3a3a', 120, 0.5 + 0.5 * k)
    beat = max(0, np.sin(lt * (14 + 10 * k))) ** 3
    heart_icon(cv, hx, hy, 0.5, beat)
    for q in range(int(30 * k)):                                            # adrenaline swarming the heart
        a = q * 2.4 + lt * 2
        r = 220 - 110 * ((lt * 0.8 + q * 0.07) % 1)
        disc(cv, hx + np.cos(a) * r, hy + np.sin(a) * r, 11, ADR, ow=2)
    meter(cv, 0, -560, 520, k, ADR if k < 0.75 else ramp('#e2483d', '#a82a22', '#ff8a7a'), 'ADRENALINE')
    if k > 0.75:
        hook_text(cv, 'TOXIC', lt, y=-760, size=170, pop_t=dur * 0.6, color=(255, 80, 80))
    return cv


def b6_quiver(lt, dur, T):
    k = ease(np.clip((lt - 1.2) / (dur * 0.5), 0, 1))
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a0a14', '#1a0408', vignette=0.4)
    q = k * 14 * np.sin(lt * 70)
    heart_icon(cv, q, 60 + q * 0.5, 1.6, 0.3 * (1 - k) * max(0, np.sin(lt * 12)))
    for i in range(int(4 + 26 * min(1, lt / 1.2))):                         # calcium flooding in
        a = i * 2.39
        r = 360 - 160 * ((lt * 0.9 + i * 0.05) % 1)
        disc(cv, np.cos(a) * r, 60 + np.sin(a) * r, 13, ramp('#e8f4ff', '#a8c4e0', '#ffffff'), ow=2)
    label(cv, 'CALCIUM', -300, -250, 52, (200, 225, 255))
    ecg(cv, 0, -520, 600, 150, lt, k)
    if k > 0.6:
        label(cv, 'DEADLY QUIVER', 0, -380, 64, RED)
    return cv


def b7_chase(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    flash = (lt * 4) % 1 < 0.5
    cv.background('#0e1430', '#1e2448', vignette=0.4)
    cv.glow(circle(-640, -700, 200), (-900, -1000, -300, -400), '#e2483d' if flash else '#3d6fe2', 260, 0.9)
    box(cv, 0, 620, 1300, 420, ramp('#2a2f3a'), r=0, ow=0, shadow=0)        # street
    box(cv, 300, 0, 260, 220, ramp('#c8b090', '#9a8060', '#e8d0b0'), r=10)  # her house
    cv.shape(poly([(20, -220), (580, -220), (300, -420)]), (0, -430, 600, -210), ramp('#7a3a2a'), ow=4)
    box(cv, 300, 90, 60, 130, DOORC, r=8)
    box(cv, 170, -50, 50, 50, ramp('#ffe8a0'), r=6)
    run_ = lt * 2.2
    gx = -560 + 520 * ease(np.clip(lt / (dur * 0.8), 0, 1))
    guy(cv, gx, 560, 0.7, face='worried', arms=((60 + 40 * np.sin(run_ * 6), 40), (60 - 40 * np.sin(run_ * 6), 40)), shirt=HOOD)
    badge(cv, '2008', y=-640, col=WHT, w=260)
    label(cv, 'NORTH CAROLINA', 0, -520, 50, (200, 205, 230))
    return cv


def b8_verdict(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1f3e', '#4a3a5e', vignette=0.4)
    guy(cv, -230, 520, 0.85, face='shock', woman=True, hair=GRAYHAIR, glasses=True, arms=((30, 60), (30, 60)), shirt=ramp('#b07ab0'))
    crack = ease(np.clip((lt - 0.4) / 0.6, 0, 1))
    heart_icon(cv, -230, -420, 0.6, 0)
    if crack > 0:
        line(cv, [(-230, -480), (-250, -440), (-215, -410), (-240, -370), (-230, -340)], 7, flat(hexc('#2a0a10')), a=crack)
    label(cv, 'AGE 79', -230, -600, 56, WHT)
    guy(cv, 250, 520, 0.85, face='worried', shirt=ramp('#ff8a2a', '#c05a10', '#ffb070'), arms=((12, 0), (12, 0)))
    bars = ease(np.clip((lt - 1.2) / 0.5, 0, 1))
    for i in range(6):                                                      # prison bars slam down
        x = 70 + i * 80
        line(cv, [(x, -600 - 300 * (1 - bars)), (x, 560 - 300 * (1 - bars))], 22, STEEL, ow=4, flat=False, a=bars)
    if bars > 0.9:
        hook_text(cv, 'LIFE IN PRISON', lt, y=-760, size=120, pop_t=1.5, color=(255, 210, 63))
    return cv


# the cuts that go INSIDE him: through his eye into his brain, and into his chest to the heart (screen px)
DIVE = {1: (385, 555), 6: (550, 1088)}

BEATS = [b0_hook, b1_brain, b2_glands, b3_body, b4_gut, b5_toxic, b6_quiver, b7_chase, b8_verdict]

if __name__ == '__main__':
    run(BEATS)
