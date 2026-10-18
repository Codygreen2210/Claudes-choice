#!/usr/bin/env python3
"""Why You Should Never Breathe Fast Before Swimming Underwater (shallow water blackout).

    python3 studio/toon/shorts/swim.py times.json lines.json out.mp4 [--sheet | --still T]

Opens mid-action: a swimmer gliding along the pool floor goes limp. Ends on that same swim
running up to frame one, with "...Because" into "this swimmer is about to pass out".
Facts: shallow-water blackout (fast breathing lowers CO2, the urge to breathe comes from CO2,
oxygen runs out first, blackout with no warning).
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

CAP = ramp('#e2483d', '#a82a26', '#ff8070')
TRUNKS = ramp('#3d5f94', '#26395f', '#5f86c2')
CO2C = ramp('#9aa3ad', '#6a737d', '#d0d6dc')
FLOOR_Y = 520


def pool(cv, T, dark=0.0):
    cv.background('#2f8fd0', '#145a8e', vignette=0.4)
    # floor tiles
    box(cv, cv.cx, FLOOR_Y + 300, 1400, 300, ramp('#7cc8e8', '#4c9cc4', '#a8e2f6'), r=0, ow=0, shadow=0)
    for x in range(int(cv.cx) - 1400, int(cv.cx) + 1400, 120):
        xx = x - (x % 120)
        line(cv, [(xx, FLOOR_Y), (xx, FLOOR_Y + 600)], 4, flat(hexc('#5aa8cf')))
    line(cv, [(cv.cx - 1400, FLOOR_Y + 2), (cv.cx + 1400, FLOOR_Y + 2)], 8, flat(hexc('#2c6f99')))
    # lane line on the floor
    box(cv, cv.cx, FLOOR_Y + 120, 1400, 18, ramp('#1d3f66'), r=8, ow=0, shadow=0)
    # moving light ripples
    for k in range(7):
        pts = [(cv.cx - 700 + u * 1400, cv.cy - 700 + k * 190 + 30 * np.sin(u * 9 + T * 1.5 + k)) for u in np.linspace(0, 1, 14)]
        line(cv, pts, 5, flat(hexc('#7fd0ff')), a=0.35)
    if dark > 0:
        cv.img = np.ascontiguousarray(cv.img * (1 - 0.55 * dark), dtype=np.float32)


def swimmer(cv, x, y, s, t, limp=0.0, roll=0.0, face='calm', big=1.0):
    """Swimming left, seen from the side. limp 0..1 stops the kick and lets the arms trail."""
    kick = (1 - limp) * np.sin(t * 9)
    sk = SKIN
    # legs (behind), kicking
    for k, ph in enumerate((0, np.pi)):
        a = 0.35 * np.sin(t * 9 + ph) * (1 - limp) + 0.15 * limp
        hip = (x + 150 * s, y + 10 * s)
        knee = (hip[0] + 110 * s, hip[1] + np.sin(a) * 60 * s + 10 * s * k)
        foot = (knee[0] + 110 * s, knee[1] + np.sin(a * 1.5) * 50 * s + 20 * limp * s)
        line(cv, [hip, knee, foot], 26 * s * big, sk, ow=4)
    # body
    cv.shape(capsule(x - 70 * s, y + roll * 20 * s, x + 170 * s, y + 10 * s, 52 * s * big, 46 * s * big),
             (x - 140 * s, y - 70 * s, x + 240 * s, y + 80 * s), sk)
    cv.shape(capsule(x + 110 * s, y + 8 * s, x + 190 * s, y + 12 * s, 50 * s * big), (x + 50 * s, y - 50 * s, x + 250 * s, y + 70 * s), TRUNKS)
    # arms: reaching forward while swimming, trailing back when limp
    for k in range(2):
        sh = (x - 40 * s, y - 10 * s)
        if limp < 0.5:
            a = np.radians(180 + 20 * np.sin(t * 4.5 + k * np.pi))
            hand = (sh[0] + np.cos(a) * 200 * s, sh[1] + np.sin(a) * 200 * s)
        else:
            hand = (sh[0] + 60 * s, sh[1] + 150 * s + 20 * k * s)
        line(cv, [sh, hand], 24 * s * big, sk, ow=4)
    # head with cap
    hx, hy = x - 120 * s, y - 20 * s + 30 * limp * s
    disc(cv, hx, hy, 62 * s, sk)
    cv.shape(subtract(circle(hx, hy, 66 * s), offset(rbox(hx, hy + 40 * s, 80 * s, 40 * s, 10 * s), 0, 0)),
             (hx - 70 * s, hy - 70 * s, hx + 70 * s, hy + 10 * s), CAP, ow=4)
    if limp > 0.5:
        line(cv, [(hx - 38 * s, hy + 6 * s), (hx - 14 * s, hy + 10 * s)], 5 * s)      # eye shut
    else:
        dot(cv, hx - 28 * s, hy + 4 * s, 8 * s)
    if face == 'puff':
        disc(cv, hx - 50 * s, hy + 26 * s, 16 * s, PINK, ow=3)


def air_bubbles(cv, T, x, y, rate=1.0, seed=1):
    if rate <= 0:
        return
    bubbles(cv, T, x - 30, x + 30, y - 700, y, n=int(8 * rate) + 1, rmin=6, rmax=16, speed=320, seed=seed, a=170)


# ------------------------------------------------------------------ beats
def b0_hook(lt, dur, T):
    """Mid-action: gliding along the pool floor, then he goes limp. Run up to its start, it is also the last beat."""
    p = lt + 3.0
    x = 520 - p * 230
    limp = ease(np.clip((lt - 0.55) / 0.5, 0, 1)) if lt >= 0 else 0.0
    cv = Canvas(x + 60, 260 + 25 * limp, 1.2)
    pool(cv, T)
    swimmer(cv, x, FLOOR_Y - 120 + 40 * limp, 1.0, T, limp=limp, roll=limp)
    air_bubbles(cv, T, x - 140, FLOOR_Y - 140, rate=1 - limp)
    if lt >= 0:
        hook_text(cv, 'NO WARNING', lt, y=-640, size=110, pop_t=0.0, color=(255, 236, 80))
    return cv


def edge(cv, T, pant=1.0, x=0):
    cv.background('#bfe6ff', '#eaf6ff', vignette=0.25)
    box(cv, 0, 700, 1300, 420, WATER, r=0, ow=0, shadow=0)
    for k in range(4):
        pts = [(-700 + u * 1400, 300 + 14 * np.sin(u * 10 + T * 2 + k)) for u in np.linspace(0, 1, 16)]
        line(cv, pts, 6, flat(hexc('#9fe0ff')))
    box(cv, 0, 230, 1300, 40, ramp('#e8e2d4'), r=6)
    br = abs(np.sin(T * 5.5 * pant))
    guy(cv, x, 210, 0.75, face='puff' if br > 0.5 else 'calm', arms=((20 + 15 * br, 0), (20 + 15 * br, 0)), shirt=TRUNKS)
    if pant > 0:
        for k in range(3):
            ph = (T * 2.2 + k / 3) % 1
            disc(cv, x - 110 - ph * 220, -380 - ph * 60, 26 + 40 * ph, ramp('#ffffff'), ow=0, alpha=0.6 * (1 - ph), shadow=0)


def b1_breaths(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    edge(cv, T, 1.0)
    label(cv, 'FAST BREATHS', 0, -760, 76, (255, 120, 60))
    rewind(cv, T, 1 - lt / 0.45)
    return cv


def b2_jump(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    k = np.clip(lt / 0.8, 0, 1)
    if k < 1:
        edge(cv, T, 0, x=-80 + 300 * k)
    else:
        cv.background('#2f8fd0', '#145a8e', vignette=0.4)
        bubbles(cv, T, -400, 400, -900, 900, n=40, rmin=8, rmax=26, speed=500, seed=4, a=160)
        swimmer(cv, 0, 0, 1.0, T, face='calm')
    if 0.7 < lt < 1.1:
        cv.flash('#ffffff', 0.5 * (1 - (lt - 0.7) / 0.4))
    hook_text(cv, 'STAY DOWN LONGER?', lt, y=-640, size=86, pop_t=1.0)
    return cv


def xray_head(cv, T, alarm=0.0, co2=0.0, air=1.0, z=1.0):
    cv.background('#0f1a2c', '#1c2f4d', vignette=0.45)
    # body outline
    cv.shape(capsule(0, 320, 0, 900, 260, 300), (-320, 40, 320, 1220), ramp('#3c5f86', '#2a4566', '#5f86b0'), ow=4, alpha=0.6, shadow=0)
    disc(cv, 0, -200, 230, ramp('#3c5f86', '#2a4566', '#5f86b0'), ow=4, alpha=0.6, shadow=0)
    brain(cv, 0, -230, 0.85)
    for sx in (-1, 1):
        cv.shape(rotell(sx * 110, 520, 95, 180 * (0.7 + 0.3 * air), sx * 8), (sx * 110 - 120, 320, sx * 110 + 120, 720), PINK, ow=4, alpha=0.85)
    # alarm bell above the head
    ring = alarm * np.sin(T * 30) * 12
    cv.shape(xform_bell(0 + ring, -620), (-120, -760, 120, -500), YELLOW if alarm > 0 else ramp('#6f7782'))
    if alarm > 0:
        for sx in (-1, 1):
            line(cv, [(sx * 150, -660), (sx * 210, -700)], 8, flat(hexc('#ffe14d')))
            line(cv, [(sx * 160, -600), (sx * 230, -600)], 8, flat(hexc('#ffe14d')))


def xform_bell(x, y):
    return smooth(20, rbox(x, y, 90, 70, 60), rbox(x, y + 70, 120, 20, 10), circle(x, y + 105, 22))


def b3_trick(lt, dur, T):
    cv = Canvas(0, 0, keys(lt, [(0, 0.9), (dur, 1.05)]))
    xray_head(cv, T)
    hook_text(cv, 'THE TRICK', lt, y=-760, pop_t=0.4, color=(120, 220, 255))
    return cv


def b4_alarm(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    xray_head(cv, T, alarm=1.0 if (lt % 1.0) < 0.6 else 0.0)
    label(cv, 'BREATHE NOW!', 0, -870, 70, (255, 230, 90))
    meter(cv, 0, 650, 700, 0.9, GREEN, 'AIR LEFT')
    return cv


def b5_co2(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    xray_head(cv, T, alarm=1.0 if k > 0.85 and (lt % 0.5) < 0.3 else 0.0)
    # blood vessel full of grey CO2 bubbles building up
    box(cv, 0, 640, 520, 90, ramp('#c0394a', '#8a2232', '#e86070'), r=80)
    rng = np.random.default_rng(3)
    for i in range(int(30 * k)):
        bx = (rng.uniform(-480, 480) + T * 200) % 960 - 480
        disc(cv, bx, 640 + rng.uniform(-45, 45), rng.uniform(14, 26), CO2C, ow=3)
    label(cv, 'CO2', 0, 520, 70, (220, 225, 230))
    return cv


def b6_dump(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    edge(cv, T, 1.2)
    # grey CO2 puffs leaving with every breath
    for k in range(4):
        ph = (T * 2.0 + k / 4) % 1
        disc(cv, -150 - ph * 300, -400 - ph * 160, 30 + 50 * ph, CO2C, ow=3, alpha=0.8 * (1 - ph))
    label(cv, 'CO2 OUT', -250, -760, 70, (220, 225, 230))
    # the alarm bell, crossed out
    cv.shape(xform_bell(330, -700), (210, -840, 450, -580), ramp('#6f7782'))
    if lt > dur * 0.4:
        line(cv, [(220, -820), (440, -580)], 18, flat(hexc('#e2483d')), ow=4)
        hook_text(cv, 'ALARM OFF', lt, y=700, pop_t=dur * 0.45, color=(255, 90, 80))
    return cv


def two_meters(cv, air, co2):
    y0 = cv.cy - 520 / cv.zoom
    meter(cv, cv.cx, y0, 760, air, GREEN if air > 0.3 else ramp('#e2483d'), 'AIR')
    meter(cv, cv.cx, y0 + 230, 760, co2, ramp('#9aa3ad'), 'BREATHE ALARM')
    line(cv, [(cv.cx + 130, y0 + 180), (cv.cx + 130, y0 + 280)], 8, flat(hexc('#ffe14d')))


def b7_air_down(lt, dur, T):
    cv = Canvas(0, 300, 1.0)
    pool(cv, T)
    x = 300 - lt * 160
    swimmer(cv, x, FLOOR_Y - 120, 1.0, T)
    air_bubbles(cv, T, x - 140, FLOOR_Y - 140, 0.5)
    k = lt / dur
    two_meters(cv, 0.7 - 0.45 * k, 0.15 + 0.1 * k)
    return cv


def b8_empty(lt, dur, T):
    cv = Canvas(0, 300, 1.05)
    pool(cv, T)
    swimmer(cv, 0, FLOOR_Y - 120, 1.0, T, limp=0)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    two_meters(cv, 0.25 * (1 - k), 0.25 + 0.05 * k)
    if k >= 1:
        hook_text(cv, 'EMPTY', lt, y=-200, pop_t=dur * 0.6, color=(255, 90, 80))
        cv.vignette(0.5 * np.clip((lt - dur * 0.6) / 0.3, 0, 1))
    return cv


def b9_sleep(lt, dur, T):
    limp = ease(np.clip(lt / 0.8, 0, 1))
    cv = Canvas(0, 300, 1.25)
    pool(cv, T, dark=0.5 * limp)
    swimmer(cv, 0, FLOOR_Y - 120 + 60 * limp, 1.0, T, limp=limp, roll=limp)
    for k in range(3):
        ph = (T * 0.6 + k / 3) % 1
        label(cv, 'z', -160 + ph * 80, 330 - ph * 260, 60 + 50 * ph, (255, 255, 255), a=(1 - ph) * limp)
    return cv


def b10_breathe_in(lt, dur, T):
    cv = Canvas(-160, 440, 2.2)
    pool(cv, T, dark=0.4)
    swimmer(cv, 0, FLOOR_Y - 60, 1.0, T, limp=1, roll=1)
    hx, hy = -120, FLOOR_Y - 50
    # water rushing in at the mouth
    specks(cv, T, lambda i, v, tt: (hx - 60 - 160 * ((tt * 1.4 + v[0]) % 1) * (1 - 0.0), hy + 30 + (v[1] - 0.5) * 120 * (1 - (tt * 1.4 + v[0]) % 1),
                                    1 - (tt * 1.4 + v[0]) % 1), 40, (160, 220, 255), 6, seed=5)
    arrows(cv, [((hx - 240, hy + 30), (hx - 70, hy + 30))], (120, 200, 255), 8)
    return cv


def b11_brain(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1420', '#2c1f30', vignette=0.45)
    k = np.clip(lt / (dur * 0.9), 0, 1)
    brain(cv, 0, -40, 1.6, hot=0.6 * k)
    for i in range(int(k * 8)):
        a = i * 0.8
        line(cv, [(np.cos(a) * 120, -40 + np.sin(a) * 80), (np.cos(a) * 260, -40 + np.sin(a) * 180)], 6, flat(hexc('#ff5a4a')))
    box(cv, 0, -700, 230, 85, DARK, r=26)
    label(cv, f'{int(k * 4)}:{int((k * 240) % 60):02d}', 0, -690, 96, (255, 90, 80))
    label(cv, 'NO AIR', 0, 560, 80, (255, 90, 80))
    return cv


def b12_strong(lt, dur, T):
    cv = Canvas(0, 300, 1.0)
    pool(cv, T)
    swimmer(cv, 260 - lt * 260, FLOOR_Y - 140, 1.15, T * 1.4, big=1.3)
    hook_text(cv, 'STRONG SWIMMERS', lt, y=-640, size=90, pop_t=0.3, color=(255, 236, 80))
    return cv


def b13_rules(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2f8fd0', '#145a8e', vignette=0.35)
    items = [('BREATHE NORMAL', GREEN, -560), ('NEVER SWIM ALONE', YELLOW, -180), ('PULL THEM UP', ORANGE, 200)]
    for i, (txt, col, y) in enumerate(items):
        t0 = i * dur * 0.28
        s_ = pop(lt, t0, 0.3)
        if s_:
            box(cv, 0, y, 430 * s_, 120 * s_, col, r=50)
            label(cv, txt, 0, y + 10, 70 * s_, (255, 255, 255))
    return cv


BEATS = [b0_hook, b1_breaths, b2_jump, b3_trick, b4_alarm, b5_co2, b6_dump, b7_air_down, b8_empty,
         b9_sleep, b10_breathe_in, b11_brain, b12_strong, b13_rules]

if __name__ == '__main__':
    run(BEATS)
