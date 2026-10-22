#!/usr/bin/env python3
"""Why you should never hold in a sneeze. Opens on him already pinching his nose, red and shaking; loops back into it
(the last line plays over the sneeze building up and his hand flying to his nose)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403
from common import arm_pts

WALL = ('#f2d9a8', '#d8b47a')
FLOOR = ramp('#a8693a', '#6e4122', '#d08f58')
NOSEC = ramp('#f2b48c', '#c97f62', '#ffd9bd')
NOSTRIL = ramp('#5a2a22', '#3a1410', '#7a3a30')
DUST = ramp('#b8a890', '#8a7a60', '#e0d4c0')
SPRAY = ramp('#6fc8ff', '#2a8ad0', '#c8ecff')
XR = ramp('#a8c8f0', '#6a8fb8', '#d8ecff')
PRESS = (255, 90, 80)
TISSUE = ramp('#f4b0b8', '#c97a86', '#ffd4da')
DRUM = ramp('#ffd0c8', '#e0a098', '#fff0ec')
HOSP = ('#d8f0ec', '#a8d8d0')

GX, GY, GS = 0, 959, 1.6                       # the close-up: head centre at (0, -260)
NOSE = (GX, GY - 740 * GS)


def living_room(cv, T):
    """His living room: warm wall, window, a LIKE & SUBSCRIBE poster and a framed bell (the Easter eggs)."""
    cv.background(*WALL, vignette=0.25)
    box(cv, 0, 860, 700, 260, FLOOR, r=0, ow=0, shadow=0)
    box(cv, 0, 590, 700, 14, ramp('#8a5a30'), r=0, ow=0, shadow=0)            # skirting board
    sub_poster(cv, -400, -470, 0.9, T=T)
    box(cv, 400, -480, 105, 105, WOOD, r=8)
    box(cv, 400, -480, 88, 88, ramp('#2a3a6a', '#1a2448', '#4a5a9a'), r=4, ow=0, shadow=0)
    bell_icon(cv, 400, -500, 56)
    label(cv, 'HIT THE BELL', 400, -415, 22, (255, 236, 80), stroke=2)
    doormat(cv, 300, 820, 0.9)
    box(cv, -420, 690, 110, 22, WOOD, r=6)                                   # side table with his phone
    line(cv, [(-500, 700), (-500, 960)], 14, WOOD, ow=3, flat=False); line(cv, [(-340, 700), (-340, 960)], 14, WOOD, ow=3, flat=False)
    sub_phone(cv, -420, 640, 0.55, T)


def holder(cv, lt, T, swell=0.0, s=GS, x=GX, y=GY):
    """Him holding it in. lt < -0.15: the sneeze building (head back, 'ahh'); then his hand slams onto his nose."""
    k = ease(float(np.clip((lt + 0.6) / 0.5, 0, 1)))
    rest = arm_pts(1, (104, -590), 12, 0)[1]
    tx, ty = rest[0] + (NOSE_L[0] - rest[0]) * k, rest[1] + 12 + (NOSE_L[1] - rest[1] - 12) * k
    right = reach(1, tx, ty)
    shake_ = (0.3 + 0.7 * swell) * float(lt > -0.15)
    jx = 7 * shake_ * np.sin(T * 53); jy = 4 * shake_ * np.cos(T * 41)
    red = float(np.clip(0.05 + 0.1 * swell, 0, 0.15)) * float(lt > -0.15)
    face = 'worried' if lt < -0.15 else 'hold'
    tilt = -0.25 * (1 - k) if lt < 0 else 0.0
    guy(cv, x + jx, y + jy, s, face=face, arms=((12, 0), right), tint=('#ff3a2a', red) if red > 0 else None, tilt_head=tilt,
        look=(0, -1) if lt < -0.15 else (0, 0))
    if k > 0.05:                                                              # forearm and hand drawn over his face, not behind it
        el, hd = arm_pts(1, (104, -590), *right)
        P = lambda px, py: (x + jx + px * s, y + jy + py * s)
        A, Bh = P(*el), P(*hd)
        cv.shape(capsule(A[0], A[1], Bh[0], Bh[1], 30 * s, 28 * s), bbox_of([A, Bh], 32 * s), SKIN)
        Hc = P(hd[0], hd[1] + 12)
        disc(cv, Hc[0], Hc[1], 34 * s, SKIN)
    if k > 0.6:                                                               # pinching fingers over the nose
        nx, ny = x + jx + NOSE_L[0] * s, y + jy + NOSE_L[1] * s
        for sx in (-1, 1):
            cv.shape(capsule(nx + sx * 18 * s, ny - 18 * s, nx + sx * 10 * s, ny + 14 * s, 12 * s), (nx - 40 * s, ny - 40 * s, nx + 40 * s, ny + 40 * s), SKIN)
    if lt > -0.15:
        for q in range(3):                                                    # sweat
            ph = (T * 1.1 + q / 3) % 1
            drop(cv, x + (-120 + q * 120) * s, y - (860 - 90 * ph) * s, 14, a=1 - ph)


NOSE_L = (6, -738)                               # his nose, in guy units


def ring_seg(cv, cx, cy, r0, r1, a0, a1, col, n=24):
    """A slice of a ring (angles in radians, 0 = right, going counter-clockwise up)."""
    aa = np.linspace(a0, a1, n)
    pts = [(cx + np.cos(a) * r1, cy - np.sin(a) * r1) for a in aa] + [(cx + np.cos(a) * r0, cy - np.sin(a) * r0) for a in aa[::-1]]
    cv.shape(poly(pts), (cx - r1 - 4, cy - r1 - 4, cx + r1 + 4, cy + r1 + 4), col, ow=3, shadow=0)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    living_room(cv, T)
    holder(cv, lt, T, swell=0.5 + 0.3 * np.sin(T * 3))
    if lt >= -0.15:
        hook_text(cv, 'HOLD IT!', lt + 0.15, y=-780, size=170, color=(255, 236, 80))
    return cv


def b1_nose(lt, dur, T):
    """Right up his nose: dust drifting in, nose hairs twitching."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#f2b48c', '#c97f62', vignette=0.3)
    cy = -60
    cv.shape(smooth(60, capsule(0, cy - 700, 0, cy - 120, 110, 150), circle(0, cy, 210), circle(-180, cy + 50, 120), circle(180, cy + 50, 120)),
             (-330, cy - 820, 330, cy + 200), NOSEC)
    for sx in (-1, 1):
        nx, ny = sx * 100, cy + 120
        cv.shape(ellipse(nx, ny, 62, 42), (nx - 66, ny - 46, nx + 66, ny + 46), NOSTRIL, ow=3, shadow=0)
        for h in range(4):                                                    # nose hairs
            hx = nx - 36 + h * 24
            line(cv, [(hx, ny + 30), (hx + 8 * np.sin(T * 9 + h), ny - 6)], 4, flat(hexc('#2a1a12')))
    for q in range(14):                                                       # dust floating up into the nostrils
        ph = (lt * 0.35 + q / 14) % 1
        sx = -1 if q % 2 else 1
        x = sx * 100 + (1 - ph) * (sx * 260 * np.cos(q) + 60 * np.sin(T + q))
        y = cy + 130 + (1 - ph) * (420 + 60 * np.sin(q * 3))
        disc(cv, x, y, 12 + 6 * (q % 3), DUST, ow=2.5, shadow=0, alpha=min(1, ph * 4) * (1 - ph * 0.6))
    ph = (lt * 0.35 + 0.5) % 1                                                # a little gold bell drifting in with the dust
    bell_icon(cv, 100 + (1 - ph) * 300, cy + 130 + (1 - ph) * 380, 30)
    thumb_icon(cv, -100 - (1 - ph) * 280, cy + 140 + (1 - ph) * 330, 26)
    hook_text(cv, 'TICKLE', lt, y=-760, size=150, pop_t=dur * 0.45, color=(255, 236, 80))
    return cv


def b2_alarm(lt, dur, T):
    """A nerve zaps the alarm from his nose to his brain, then his chest clamps down."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1030', '#0a0618', vignette=0.35)
    k1 = float(np.clip(lt / (dur * 0.4), 0, 1))
    k2 = ease(float(np.clip((lt - dur * 0.45) / (dur * 0.3), 0, 1)))
    path = [(-330, -130), (-300, -260), (-200, -360), (-90, -420)]
    line(cv, path, 14, flat(hexc('#ffd23f')), a=0.5)
    seg = k1 * 3; i = min(int(seg), 2); f = seg - i
    zx = path[i][0] + (path[i + 1][0] - path[i][0]) * f; zy = path[i][1] + (path[i + 1][1] - path[i][1]) * f
    if k1 < 1:
        cv.glow(circle(zx, zy, 16), (zx - 30, zy - 30, zx + 30, zy + 30), '#ffe14d', 40, 1.2)
    cv.shape(smooth(30, capsule(-340, -260, -340, -150, 40, 60), circle(-340, -110, 70)), (-420, -300, -260, -30), NOSEC)   # his nose
    brain(cv, 40, -500, 0.75, hot=0.6 * k1)
    if k1 >= 1:
        arrows(cv, [((40, -330), (40, -170))], (255, 236, 80), 14)
    chest(cv, 40, 130, 0.42, T, dia=k2, lung=1 - 0.6 * k2, twitch=k2 * float(k2 < 1))
    label(cv, 'NERVE', -380, -330, 52, (255, 236, 80))
    neon_sign(cv, 0, 700, 'SUBSCRIBE', '#ff3a6a', T)
    if k2 > 0.5:
        badge(cv, 'SQUEEZE', y=-760, col=(255, 90, 80), w=420)
    return cv


def b3_spray(lt, dur, T):
    """What a normal sneeze does: ACHOO, a spray cone flying across the room, past the 26-foot mark."""
    cv = Canvas(0, 0, 1.0)
    living_room(cv, T)
    s, x, y = 0.75, -340, 560
    guy(cv, x, y, s, face='scream', arms=((20, 10), (20, 10)), tilt_head=0.3)
    mx, my = x + 0.3 * 30 * s, y - 708 * s
    k = float(np.clip(lt / (dur * 0.6), 0, 1))
    rng = np.random.default_rng(4)
    for q in range(120):                                                      # the spray
        t0 = q / 120 * 0.5
        u = float(np.clip((k - t0) / 0.5, 0, 1))
        if u <= 0:
            continue
        ang = rng.uniform(-0.35, 0.25)
        dist = 920 * u * rng.uniform(0.6, 1.0)
        disc(cv, mx + np.cos(ang) * dist, my + np.sin(ang) * dist + 160 * u * u, 9 + 9 * rng.random(), SPRAY, ow=2, shadow=0, alpha=0.95)
    box(cv, 120, 650, 440, 26, ramp('#ffd23f', '#d09a10', '#fff08a'), r=6)  # tape measure on the floor
    for t in range(7):
        tx = -300 + t * 140
        line(cv, [(tx, 630), (tx, 670)], 5, flat(hexc('#3a2a10')))
    if k > 0.85:
        badge(cv, '26 FEET', y=-260, x=200, col=(127, 210, 255), w=360)
    hook_text(cv, 'ACHOO!', lt, y=-780, size=170, pop_t=0.05, color=(255, 255, 255))
    return cv


def b4_stuck(lt, dur, T):
    """Back on him holding it: the air ricochets around inside his head."""
    cv = Canvas(0, 0, 1.0)
    living_room(cv, T)
    k = float(np.clip(lt / dur, 0, 1))
    holder(cv, 1.0, T, swell=0.6 + 0.4 * k)
    hx, hy = GX, GY - 762 * GS
    for q in range(5):                                                        # trapped air bouncing round his head
        a = T * (3 + q * 0.6) + q * 1.3
        p0 = (hx + np.cos(a) * 120, hy + np.sin(a) * 120)
        p1 = (hx + np.cos(a + 0.6) * 120, hy + np.sin(a + 0.6) * 120)
        arrows(cv, [(p0, p1)], PRESS, 10)
    if lt > dur * 0.35:
        hook_text(cv, 'STUCK!', lt, y=-780, size=170, pop_t=dur * 0.35, color=PRESS)
    return cv


def b5_throat(lt, dur, T):
    """X-ray of his head and neck: the blast rams up his throat and out the tubes to his ears."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#0e1a30', '#060c18', vignette=0.35)
    cv.shape(smooth(60, circle(0, -470, 250), rbox(0, -80, 120, 260, 60)), (-260, -730, 260, 190), XR, ow=4, alpha=0.3)
    throat(cv, 0, -230, 0.42)
    k = float(np.clip(lt / (dur * 0.5), 0, 1))
    for sx in (-1, 1):                                                        # tubes up to the ears
        line(cv, [(sx * 40, -330), (sx * 150, -420), (sx * 245, -450)], 24, TISSUE, ow=3, flat=False)
        glow = 0.4 + 0.6 * (0.5 + 0.5 * np.sin(T * 12)) * k
        cv.shape(subtract(ellipse(sx * 285, -452, 48, 80), ellipse(sx * 290, -452, 26, 52)), (sx * 285 - 52, -536, sx * 285 + 52, -368), SKIN)   # his ears
        cv.shape(ellipse(sx * 262, -452, 24, 44), (sx * 262 - 30, -500, sx * 262 + 30, -400), DRUM, ow=3)
        cv.glow(ellipse(sx * 262, -452, 22, 40), (sx * 262 - 30, -500, sx * 262 + 30, -400), '#ff3a2a', 40, glow)
    for q in range(4):                                                        # the blast moving up
        ph = (lt * 1.4 + q / 4) % 1
        yy = 300 - 600 * ph
        arrows(cv, [((0, yy), (0, yy - 90))], PRESS, 14)
    for sx in (-1, 1):
        ph = (lt * 1.4) % 1
        arrows(cv, [((sx * 60, -340), (sx * (60 + 150 * ph), -340 - 100 * ph))], PRESS, 10)
    label(cv, 'EARS', -285, -600, 50, (255, 200, 200))
    label(cv, 'EARS', 285, -600, 50, (255, 200, 200))
    label(cv, 'THROAT', 0, 230, 50, (255, 200, 200))
    xray_tag(cv, 360, 700, ('PATIENT:', 'SUBSCRIBER'))
    return cv


def b6_gauge(lt, dur, T):
    """A pressure dial: a normal sneeze sits low, a held one swings to 20 times."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1418', '#140a0c', vignette=0.4)
    cx, cy, R = 0, -80, 380
    box(cv, cx, cy - 20, R + 40, R * 0.62, DARK, r=60)
    for a0, a1, c in ((np.pi, np.pi * 0.66, ramp('#3fbf6a')), (np.pi * 0.66, np.pi * 0.33, ramp('#ffd23f')), (np.pi * 0.33, 0, ramp('#e2483d'))):
        ring_seg(cv, cx, cy, R - 70, R, a1, a0, c)
    k = ease(float(np.clip((lt - dur * 0.15) / (dur * 0.5), 0, 1)))
    val = 1 + 19 * k
    a = np.pi * (1 - (val - 1) / 19) + 0.03 * np.sin(T * 30) * k
    line(cv, [(cx, cy), (cx + np.cos(a) * (R - 90), cy - np.sin(a) * (R - 90))], 22, ramp('#ffffff'), ow=4, flat=False)
    disc(cv, cx, cy, 40, STEEL)
    label(cv, 'LIKE-O-METER', cx, cy - 150, 34, (200, 210, 225), stroke=0)
    neon_sign(cv, 0, 720, 'HIT LIKE', '#3fa9ff', T)
    label(cv, '1X', cx - R + 20, cy + 70, 56, (180, 255, 190))
    label(cv, '20X', cx + R - 30, cy + 70, 56, (255, 120, 110))
    badge(cv, f'{int(round(val))}X PRESSURE', y=180, col=(255, 236, 80) if val < 19.5 else (255, 90, 80), w=560)
    if k > 0.99:
        hook_text(cv, '20 TIMES', lt, y=-760, size=150, pop_t=dur * 0.66, color=(255, 90, 80))
    return cv


def b7_torn(lt, dur, T):
    """First the tear in his throat, then a week in a hospital bed."""
    cv = Canvas(0, 0, 1.0)
    split = dur * 0.55
    if lt < split:
        cv.background('#3a1020', '#14060c', vignette=0.4)
        throat(cv, 0, -520, 0.9)
        k = ease(float(np.clip(lt / (split * 0.5), 0, 1)))
        pts = [(110, -380 + 0 * k), (70, -330), (115, -280), (70, -230), (110, -180)]
        n = 1 + int(4 * k)
        line(cv, pts[:n + 1], 16, flat(hexc('#ff2a1a')))
        for q in range(4):                                                    # air leaking out of the hole
            ph = (lt * 1.6 + q / 4) % 1
            disc(cv, 130 + 200 * ph, -300 + 40 * np.sin(q * 2 + T * 3), 14 + 10 * ph, ramp('#d8f2ff'), ow=2, shadow=0, alpha=k * (1 - ph))
        if k > 0.6:
            badge(cv, 'TORN', y=-760, col=(255, 90, 80), w=260)
        xray_tag(cv, -360, 700, ('LIKE', '+ SUBSCRIBE'))
    else:
        cv.background(*HOSP, vignette=0.25)
        bed(cv, T, 0, -60, 0.62, face='pain', blanket=True)
        line(cv, [(330, -470), (330, -40)], 10, STEEL, ow=3, flat=False)      # IV pole and bag
        box(cv, 330, -440, 46, 64, ramp('#e8f6ff', '#a8d4ee', '#ffffff'), r=14, alpha=0.9)
        for b_, (bx, by, c) in enumerate(((-370, -520, SUBRED), (-300, -600, ramp('#3d7fd8')))):   # get-well balloons
            line(cv, [(bx, by + 90), (-330, -120)], 3, flat(hexc('#444444')))
            cv.shape(ellipse(bx, by, 70, 86), (bx - 72, by - 88, bx + 72, by + 90), c)
        label(cv, 'GET WELL', -370, -545, 26, (255, 255, 255), stroke=0)
        label(cv, 'SUBSCRIBE', -370, -510, 24, (255, 255, 255), stroke=0)
        thumb_icon(cv, -300, -590, 34, ramp('#ffffff', '#d8dde4', '#ffffff'))
        box(cv, 0, 470, 120, 80, ramp('#fff6d8', '#e0d4a8', '#ffffff'), r=8)   # the chart on the foot of the bed
        label(cv, 'CHART', 0, 430, 26, (40, 34, 50), stroke=0)
        label(cv, 'NEEDS MORE', 0, 470, 24, (40, 34, 50), stroke=0)
        label(cv, 'SUBSCRIBERS', 0, 505, 24, (200, 40, 40), stroke=0)
        days = 1 + int(6.999 * float(np.clip((lt - split) / ((dur - split) * 0.8), 0, 1)))
        badge(cv, f'DAY {days}', y=-760, col=(127, 210, 255), w=300)
    return cv


def b8_eardrum(lt, dur, T):
    """A big ear, the canal running in, and the eardrum bulging until it pops."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1830', '#140a18', vignette=0.35)
    ex, ey = -270, -160
    box(cv, 40, ey, 330, 60, TISSUE, r=55)                                   # the ear canal
    box(cv, 40, ey, 300, 38, ramp('#7a2a3a', '#4e1a26', '#9a4050'), r=36, ow=0, shadow=0)
    ear = subtract(smooth(30, ellipse(ex, ey - 40, 190, 280), circle(ex + 20, ey + 230, 90)), ellipse(ex + 50, ey - 40, 105, 190))
    cv.shape(ear, (ex - 200, ey - 330, ex + 200, ey + 330), SKIN)
    cv.shape(subtract(ellipse(ex + 30, ey - 60, 120, 205), ellipse(ex + 50, ey - 50, 92, 175)), (ex - 100, ey - 270, ex + 160, ey + 160), SKIN, alpha=0.9)
    k = float(np.clip(lt / (dur * 0.45), 0, 1))
    popped = lt > dur * 0.45
    dx = 330
    bulge = 1 + 0.35 * k * (0.9 + 0.1 * np.sin(T * 30)) if not popped else 1.0
    cv.shape(ellipse(dx, ey, 34 * bulge, 110), (dx - 50, ey - 115, dx + 50, ey + 115), DRUM, ow=4)
    if popped:
        for a in (0.4, 1.6, 2.8, 4.0, 5.2):
            line(cv, [(dx, ey), (dx + np.cos(a) * 30, ey + np.sin(a) * 100)], 7, flat(hexc('#c0202a')))
        hook_text(cv, 'POP!', lt, y=-760, size=190, pop_t=dur * 0.45, color=(255, 90, 80))
    for q in range(3):                                                        # air ramming down the canal
        ph = (lt * 1.6 + q / 3) % 1
        xx = -120 + 380 * ph
        arrows(cv, [((xx, ey), (xx + 70, ey))], PRESS, 10)
    line(cv, [(ex + 20, ey + 300), (ex + 20, ey + 345)], 4, flat(hexc('#d09a10')))   # a little gold bell earring
    bell_icon(cv, ex + 20, ey + 380, 34)
    label(cv, 'EARDRUM', dx, ey + 200, 52, (255, 200, 200))
    neon_sign(cv, 0, 720, 'SUBSCRIBE', '#ff3a6a', T)
    return cv


# the cuts that go INSIDE him: up his nose, and down into his throat (screen px)
DIVE = {1: (540, int(960 + NOSE[1])), 5: (540, int(960 + GY - 650 * GS))}

BEATS = [b0_hook, b1_nose, b2_alarm, b3_spray, b4_stuck, b5_throat, b6_gauge, b7_torn, b8_eardrum]

if __name__ == '__main__':
    run(BEATS)
