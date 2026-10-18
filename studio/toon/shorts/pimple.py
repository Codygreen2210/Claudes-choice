#!/usr/bin/env python3
"""Why You Should Never Pop a Pimple Near Your Nose (the danger triangle).

    python3 studio/toon/shorts/pimple.py times.json lines.json out.mp4 [--sheet | --still T]

Opens mid-action: two fingers squeeze a pimple by the nose and a red line races up a vein toward the brain.
Ends on the fingers closing in, running up to frame one: "Because once you squeeze..." -> "this pimple has a road to your brain."
Facts: Cleveland Clinic. The triangle runs from the bridge of the nose to the corners of the mouth; some veins there
drain back to the cavernous sinus behind the eyes; infection can (very rarely) cause a clot there; warning signs are
swelling and fever; antibiotics usually fix it if caught early; warm washcloth or patch instead of squeezing.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

FACE_Y = 0
GERM = ramp('#7fd34f', '#4f9a2a', '#b6f08a')
VEIN = ramp('#5a7fd8', '#3a58a0', '#8fb0ff')
BLOODC = ramp('#d83a3a', '#9a2222', '#ff7070')


def big_face(cv, T, xray=0.0, swell=0.0, fever=0.0, pimple=1.0, squeeze=0.0, triangle=0.0):
    """Huge face, front view: head fills the frame. xray fades to a blue see-through with veins."""
    cv.background('#f3e6d6', '#d9c3a8', vignette=0.35)
    s = 4.2
    tint = ('#ff4a3a', 0.35 * fever) if fever > 0 else None
    # head
    cv.shape(ellipse(0, FACE_Y, 118 * s, 140 * s), (-118 * s, FACE_Y - 140 * s, 118 * s, FACE_Y + 140 * s), SKIN, tint=tint, bevel=120)
    # hair
    cv.shape(inter(ellipse(0, FACE_Y - 40 * s, 128 * s, 120 * s), lambda X, Y: Y - (FACE_Y - 70 * s)),
             (-130 * s, FACE_Y - 170 * s, 130 * s, FACE_Y - 60 * s), HAIR)
    # eyes (one swells shut when sick)
    for sx in (-1, 1):
        ex, ey = sx * 42 * s, FACE_Y - 20 * s
        sw = swell if sx == -1 else 0.0
        cv.shape(ellipse(ex, ey, 26 * s, (16 - 13 * sw) * s), (ex - 27 * s, ey - 17 * s, ex + 27 * s, ey + 17 * s), WHITE, ow=4, bevel=10)
        if sw < 0.8:
            dot(cv, ex, ey, 8 * s * (1 - sw))
        if sw > 0:
            cv.shape(ellipse(ex, ey + 4 * s, 34 * s, 26 * s), (ex - 35 * s, ey - 22 * s, ex + 35 * s, ey + 30 * s),
                     ramp('#e48a7a', '#b05a50', '#ffb0a0'), ow=3, alpha=0.75 * sw)
    # nose and mouth
    cv.shape(capsule(0, FACE_Y - 10 * s, 0, FACE_Y + 25 * s, 12 * s, 18 * s), (-20 * s, FACE_Y - 20 * s, 20 * s, FACE_Y + 45 * s), SKIN, tint=tint)
    line(cv, [(-30 * s, FACE_Y + 62 * s), (0, FACE_Y + 70 * s), (30 * s, FACE_Y + 62 * s)], 5 * s)
    # the pimple, on the side of the nose
    px, py = 22 * s, FACE_Y + 18 * s
    if pimple > 0:
        r = 7 * s * pimple * (1 + 0.25 * squeeze)
        disc(cv, px, py, r, ramp('#e2483d'), ow=3)
        disc(cv, px - 1 * s, py - 1.5 * s, r * 0.45, ramp('#fff4c0'), ow=0, shadow=0)
    if triangle > 0:
        tri = [(0, FACE_Y - 45 * s), (-34 * s, FACE_Y + 64 * s), (34 * s, FACE_Y + 64 * s), (0, FACE_Y - 45 * s)]
        k = int(triangle * 4) + 1
        line(cv, tri[:max(2, k)], 9, flat(hexc('#ff3a2a')), ow=4)
        cv.shape(poly(tri[:3]), pbox(tri, 0), ramp('#ff3a2a'), ow=0, shadow=0, alpha=0.18 * triangle, flat=True)
    if xray > 0:
        g = cv.img.mean(2, keepdims=True)
        xr = g * 0.55 * np.array([0.55, 0.8, 1.0], np.float32) + np.array([0.03, 0.06, 0.12], np.float32)   # bright stays bright: the face reads as a see-through x-ray
        cv.img = np.ascontiguousarray(cv.img * (1 - xray) + xr * xray, dtype=np.float32)
    return px, py, s


def vein_path(s):
    """From the pimple up along the nose, behind the eye, to the pool of veins by the brain."""
    return [(22 * s, FACE_Y + 18 * s), (30 * s, FACE_Y - 2 * s), (36 * s, FACE_Y - 30 * s), (24 * s, FACE_Y - 52 * s),
            (8 * s, FACE_Y - 70 * s), (0, FACE_Y - 92 * s)]


def draw_veins(cv, s, k=1.0, red=0.0, T=0.0):
    pts = vein_path(s)
    n = max(2, int(k * len(pts) + 0.999))
    line(cv, pts[:n], 18, VEIN, ow=4)
    line(cv, [(22 * s, FACE_Y + 18 * s), (36 * s, FACE_Y + 70 * s), (40 * s, FACE_Y + 140 * s)], 18, VEIN, ow=4, a=0.5)   # the safe way down
    if red > 0:
        m = max(2, int(red * len(pts) + 0.999))
        line(cv, pts[:m], 22, BLOODC, ow=4)
        tip = pts[m - 1]
        cv.glow(circle(tip[0], tip[1], 20), (tip[0] - 60, tip[1] - 60, tip[0] + 60, tip[1] + 60), '#ff3a2a', 40, 0.8)


def pool(cv, s, clot=0.0, T=0.0):
    x, y = 0, FACE_Y - 100 * s
    cv.shape(rotell(x, y, 46 * s, 20 * s, 0), (x - 50 * s, y - 24 * s, x + 50 * s, y + 24 * s), VEIN, ow=4, alpha=0.9)
    if clot > 0:
        disc(cv, x + 10 * s, y, 14 * s * clot, ramp('#7a1a1a', '#4a0a0a', '#b03030'), ow=4)


def fingers(cv, x, y, s, close):
    gap = (40 - 26 * close) * s
    for sx in (-1, 1):
        fx = x + sx * gap
        cv.shape(capsule(fx + sx * 20 * s, y + 120 * s, fx, y + 6 * s, 22 * s, 18 * s), (fx - 50 * s, y - 20 * s, fx + 50 * s, y + 150 * s), SKIN)
        cv.shape(ellipse(fx, y + 4 * s, 13 * s, 9 * s), (fx - 14 * s, y - 6 * s, fx + 14 * s, y + 14 * s), ramp('#f8d8c8'), ow=3, bevel=8)


# ------------------------------------------------------------------ beats
def b0_hook(lt, dur, T):
    """Fingers squeeze, the pimple bursts inward, a red line races up the vein. Run up to its start, it's also the last beat."""
    p = lt + 2.0
    cv = Canvas(90, -120, 1.15)
    sq = float(np.clip(p / 2.0, 0, 1))
    xr = ease(np.clip((lt - 0.35) / 0.35, 0, 1)) if lt >= 0 else 0.0
    px, py, s = big_face(cv, T, xray=xr * 0.85, pimple=1.0 - 0.5 * xr, squeeze=sq)
    if xr > 0:
        draw_veins(cv, s, 1.0, red=ease(np.clip((lt - 0.45) / 1.0, 0, 1)), T=T)
        pool(cv, s)
        brain(cv, 0, FACE_Y - 150 * s, 1.0, hot=0.4 * xr)
    fingers(cv, px, py, s, sq)
    if lt >= 0:
        hook_text(cv, 'ROAD TO YOUR BRAIN', lt, y=-660, size=88, pop_t=0.0, color=(255, 90, 80))
    return cv


def b1_triangle(lt, dur, T):
    cv = Canvas(0, -60, 0.95)
    big_face(cv, T, triangle=np.clip(lt / 1.2, 0, 1))
    rewind(cv, T, 1 - lt / 0.45)
    return cv


def b2_name(lt, dur, T):
    cv = Canvas(0, -60, 0.95)
    big_face(cv, T, triangle=1.0)
    hook_text(cv, 'DANGER TRIANGLE', lt, y=-680, size=100, pop_t=0.2, color=(255, 70, 60))
    return cv


def xray_scene(lt, dur, T, k=1.0, red=0.0, clot=0.0, germs=0.0, zoom=0.8, cy=-100):
    cv = Canvas(40, cy, zoom)
    px, py, s = big_face(cv, T, xray=0.85, pimple=0.6)
    draw_veins(cv, s, k, red=red, T=T)
    pool(cv, s, clot)
    brain(cv, 0, FACE_Y - 150 * s, 1.0)
    if germs > 0:
        pts = vein_path(s)
        for i in range(int(14 * germs)):
            u = ((T * 0.25 + i / 14) % 1) * germs
            seg = u * (len(pts) - 1); j = int(seg); f = seg - j
            j = min(j, len(pts) - 2)
            gx = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f + 8 * np.sin(i * 3)
            gy = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f
            disc(cv, gx, gy, 12, GERM, ow=3)
    return cv, s


def b3_veins(lt, dur, T):
    cv, s = xray_scene(lt, dur, T, k=np.clip(lt / (dur * 0.6), 0, 1) * 0.3)
    arrows(cv, [((40 * 4.2, FACE_Y + 70 * 4.2), (40 * 4.2, FACE_Y + 160 * 4.2))], (120, 255, 140), 10)
    label(cv, 'NORMAL WAY: DOWN', 100, FACE_Y + 175 * 4.2, 60, (120, 255, 140))
    return cv


def b4_back(lt, dur, T):
    cv, s = xray_scene(lt, dur, T, k=np.clip(lt / (dur * 0.7), 0, 1))
    if lt > dur * 0.6:
        label(cv, 'RIGHT BY YOUR BRAIN', 0, FACE_Y - 100 * s - 120, 54, (255, 214, 64))
    return cv


def b5_squeeze(lt, dur, T):
    cv = Canvas(90, 0, 2.4)
    px, py, s = big_face(cv, T, xray=0.5, pimple=1.0, squeeze=np.clip(lt / 1.0, 0, 1))
    fingers(cv, px, py, s, np.clip(lt / 1.0, 0, 1))
    k = np.clip((lt - 0.8) / 0.8, 0, 1)
    for i in range(int(8 * k) + 1):
        a = i * 0.8
        disc(cv, px + 6 * np.cos(a) * 3, py - 30 * k * (1 + i % 3), 9, GERM, ow=3)
    arrows(cv, [((px, py + 30), (px, py - 70 * k - 20))], (127, 211, 79), 8)
    hook_text(cv, 'GERMS GO IN', lt, y=-680, pop_t=dur * 0.5, color=(127, 211, 79))
    return cv


def b6_ride(lt, dur, T):
    cv, s = xray_scene(lt, dur, T, k=1.0, red=np.clip(lt / dur, 0, 1), germs=np.clip(lt / (dur * 0.7), 0, 1), zoom=0.95, cy=-160)
    return cv


def b7_clot(lt, dur, T):
    cv, s = xray_scene(lt, dur, T, k=1.0, red=1.0, clot=ease(np.clip((lt - 0.4) / 1.0, 0, 1)), zoom=1.25, cy=-300)
    hook_text(cv, 'CLOT', lt, y=-680, size=140, pop_t=0.8, color=(255, 70, 60))
    label(cv, 'VERY RARE', 0, -120, 60, (255, 255, 255), a=float(np.clip(lt - 1.2, 0, 1)))
    return cv


def b8_sick(lt, dur, T):
    cv = Canvas(0, -60, 0.95)
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    big_face(cv, T, swell=k, fever=k * 0.8)
    thermo(cv, 380, -380, 98.6 + 5 * k, lo=95, hi=106, h=420)
    if k > 0.6:
        brain(cv, -330, -760, 0.5, hot=0.8)
    return cv


def b9_good(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#bff0d0', '#eafff2', vignette=0.25)
    s_ = pop(lt, 0.2, 0.35)
    if s_:
        box(cv, 0, -200, 320 * s_, 130 * s_, ramp('#f4f1ea'), r=120)
        box(cv, -160 * s_, -200, 160 * s_, 130 * s_, ramp('#e2483d'), r=120)
    label(cv, 'SUPER RARE', 0, 160, 90, (40, 140, 80))
    label(cv, 'MEDICINE CAN FIX IT', 0, 300, 64, (40, 90, 60), a=float(np.clip((lt - dur * 0.5) * 2, 0, 1)))
    return cv


def b10_instead(lt, dur, T):
    cv = Canvas(0, -60, 0.95)
    big_face(cv, T, pimple=1.0 - 0.6 * np.clip(lt / dur, 0, 1))
    k = np.clip(lt / (dur * 0.45), 0, 1)
    if lt < dur * 0.5:
        box(cv, 140, 120, 220, 120 * k + 1, ramp('#ffffff'), r=40)                         # warm washcloth
        for j in range(3):
            ph = (T * 0.8 + j / 3) % 1
            line(cv, [(80 + j * 60, -20 - ph * 120), (100 + j * 60, -80 - ph * 120)], 8, flat(hexc('#ffffff')), a=1 - ph)
        label(cv, 'WARM CLOTH', 0, -640, 80, (255, 140, 60))
    else:
        disc(cv, 92, 76, 50, ramp('#f6e2c8'), ow=4, alpha=0.95)                           # pimple patch
        label(cv, 'PATCH', 0, -640, 90, (60, 160, 255))
    return cv


def b11_doctor(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#dff1ff', '#f6fbff', vignette=0.25)
    guy(cv, -220, 780, 0.75, face='worried', shirt=ORANGE)
    guy(cv, 240, 780, 0.8, face='happy', coat=True, shirt=ramp('#f4f1ea'), arms=((15, 0), (120, 60)))
    box(cv, 240, 430, 40, 14, ramp('#e2483d'), r=5)
    box(cv, 240, 430, 14, 40, ramp('#e2483d'), r=5)
    label(cv, 'SWELLING + FEVER?', 0, -700, 70, (255, 90, 80))
    label(cv, 'SEE A DOCTOR', 0, -590, 90, (40, 120, 220))
    return cv


BEATS = [b0_hook, b1_triangle, b2_name, b3_veins, b4_back, b5_squeeze, b6_ride, b7_clot, b8_sick,
         b9_good, b10_instead, b11_doctor]

if __name__ == '__main__':
    run(BEATS)
