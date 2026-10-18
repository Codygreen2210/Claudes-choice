#!/usr/bin/env python3
"""What Happens If You Get Locked in a Hot Car.

    python3 studio/toon/shorts/hotcar.py times.json lines.json out.mp4 [--sheet | --still T]

Opens mid-action: the door slams, the lock clicks, the temperature starts racing.
Ends on that same shot running up to frame one: "Because when that door shuts," -> "this car is about to turn into an oven."
Facts: cars can get ~20 F hotter in 10 minutes; kids heat 3-5x faster; cracked windows barely help;
heatstroke at a body temperature of 104 F.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *          # noqa: F401,F403

CARC = ramp('#3d7fd8', '#2a559a', '#7fb4ff')
GLASS = ramp('#bfe6ff', '#7fb6d9', '#eaf7ff')
ASPHALT = ramp('#4b4f57', '#33363d', '#6a707a')


def sky(cv, T, heat=0.0):
    top = '#ffb35c' if heat > 0.5 else '#7cc4ff'
    cv.background(top, '#fff2c8', vignette=0.25)
    sx, sy = cv.cx - 330, cv.cy - 720
    cv.glow(circle(sx, sy, 90), (sx - 100, sy - 100, sx + 100, sy + 100), '#ffd23f', 160, 0.9, core='#fff6c0', core_w=0)
    for k in range(12):
        a = k * np.pi / 6 + T * 0.3
        line(cv, [(sx + np.cos(a) * 130, sy + np.sin(a) * 130), (sx + np.cos(a) * 200, sy + np.sin(a) * 200)], 10, flat(hexc('#ffd23f')))
    box(cv, cv.cx, cv.cy + 760, 1400, 420, ASPHALT, r=0, ow=0, shadow=0)


def heat_waves(cv, x, y, w, T, a=0.6):
    for k in range(4):
        xx = x - w / 2 + k * w / 3
        pts = [(xx + 18 * np.sin(u * 10 + T * 6 + k), y - u * 260) for u in np.linspace(0, 1, 10)]
        line(cv, pts, 7, flat(hexc('#ff7a3a')), a=a)


def car(cv, x, y, s, T, door=0.0, person=True, kid=False, dog=False, crack=0.0, broken=0.0, inside_heat=0.0):
    """Side view, facing right. door: 0 shut, 1 open (front door swings out)."""
    cv.shape(poly([(x - 260 * s, y - 80 * s), (x - 170 * s, y - 230 * s), (x + 150 * s, y - 230 * s), (x + 260 * s, y - 80 * s)]),
             (x - 270 * s, y - 240 * s, x + 270 * s, y - 70 * s), CARC)
    # people over the cabin, under the body and glass: only heads show in the windows
    if person:
        guy(cv, x + 100 * s, y + 140 * s, 0.38 * s, face='worried' if inside_heat > 0.4 else 'calm', legs=False, ground=False,
            arms=((10, 0), (10, 0)), shirt=ORANGE)
    if kid:
        guy(cv, x - 120 * s, y + 68 * s, 0.26 * s, face='worried', legs=False, ground=False, arms=((10, 0), (10, 0)), shirt=PINK)
    if dog:
        disc(cv, x - 10 * s, y - 140 * s, 38 * s, ramp('#b07a45'))
        disc(cv, x - 40 * s, y - 165 * s, 16 * s, ramp('#7a5230'))
    box(cv, x, y, 420 * s, 95 * s, CARC, r=60 * s)
    for wx0, wx1 in ((-235, -20), (10, 235)):
        cv.shape(poly([(x + wx0 * s, y - 90 * s), (x + (wx0 + 70) * s if wx0 < 0 else x + wx0 * s, y - 215 * s),
                       (x + (wx1 - 0) * s if wx0 < 0 else x + (wx1 - 70) * s, y - 215 * s), (x + wx1 * s, y - 90 * s)]),
                 (x + wx0 * s - 5, y - 220 * s, x + wx1 * s + 5, y - 85 * s), GLASS, ow=4, shadow=0, alpha=0.42)
    if inside_heat > 0:
        cv.glow(rbox(x, y - 150 * s, 200 * s, 50 * s, 30 * s), (x - 240 * s, y - 240 * s, x + 240 * s, y - 60 * s), '#ff5a2a', 40 * s, 0.5 * inside_heat)
    if crack > 0:
        box(cv, x + 120 * s, y - 220 * s, 100 * s, 6 * s * crack + 2, DARK, r=3, ow=0, shadow=0)
    if broken > 0:
        cx, cy = x - 120 * s, y - 150 * s
        for k in range(8):
            a = k * np.pi / 4 + 0.3
            line(cv, [(cx, cy), (cx + np.cos(a) * 110 * s * broken, cy + np.sin(a) * 60 * s * broken)], 4, flat(hexc('#ffffff')))
    for wx in (-260, 260):
        disc(cv, x + wx * s, y + 90 * s, 70 * s, DARK)
        disc(cv, x + wx * s, y + 90 * s, 30 * s, STEEL, ow=3)
    if door > 0:
        dx = x + 10 * s
        w = 220 * s * door                                   # shrinks to nothing as it shuts, so the slam at frame one is seamless
        cv.shape(poly([(dx, y - 80 * s), (dx + w, y - 80 * s - 40 * s * door), (dx + w, y + 80 * s - 40 * s * door), (dx, y + 80 * s)]),
                 (min(dx, dx + w) - 5, y - 130 * s, max(dx, dx + w) + 5, y + 90 * s), CARC)


# ------------------------------------------------------------------ beats
def b0_hook(lt, dur, T):
    """Door slams, lock clicks, temperature races. Run up to its start (door still open), it is also the last beat."""
    door = float(np.clip(-lt / 0.6, 0, 1)) if lt < 0 else 0.0
    slam = lt >= 0 and lt < 0.25
    cv = Canvas(0, 80, 1.05)
    sky(cv, T)
    temp = 80 + max(0.0, lt) * 9
    car(cv, -60, 350, 1.25, T, door=door, inside_heat=np.clip(lt / 3, 0, 1) if lt > 0 else 0)
    heat_waves(cv, -60, 100, 420, T, a=0.5 if lt > 0 else 0.2)
    thermo(cv, 400, -150, temp, h=560)
    if lt >= 0:
        label(cv, 'LOCKED', -60, -240, 70, (255, 90, 80), a=float(np.clip(1 - (lt - 1.0) / 0.5, 0, 1)))
        hook_text(cv, 'OVEN', lt, y=-680, size=140, pop_t=0.25, color=(255, 120, 60))
    if slam:
        cv.flash('#ffffff', 0.25 * (1 - lt / 0.25))
    return cv


def b1_outside(lt, dur, T):
    cv = Canvas(0, 0, 0.9)
    sky(cv, T)
    car(cv, 0, 450, 1.1, T, person=False)
    for x in (-500, 500):
        disc(cv, x, 420, 120, GREEN, ow=4)
        box(cv, x, 600, 20, 120, ramp('#7a5230'), r=6)
    thermo(cv, 0, -350, 80, h=420)
    label(cv, 'OUTSIDE', 0, -720, 70, (255, 255, 255))
    rewind(cv, T, 1 - lt / 0.45)
    return cv


def b2_trapped(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky(cv, T)
    car(cv, 0, 300, 1.6, T, inside_heat=0.4 + 0.4 * lt / dur)
    for k in range(3):
        ph = ((T * 0.8 + k / 3) % 1)
        x0, y0 = -560 + 200 * k, -720
        x1, y1 = x0 + 520 * ph, y0 + 700 * ph
        arrows(cv, [((x0, y0), (x1, y1))], (255, 210, 60), 10)
    for k in range(3):                                       # heat bouncing around inside
        a = T * 3 + k * 2.1
        arrows(cv, [((np.cos(a) * 120, 60 + np.sin(a) * 40), (np.cos(a + 1.2) * 200, 60 + np.sin(a + 1.2) * 60))], (255, 90, 60), 9)
    hook_text(cv, 'TRAPPED', lt, y=-640, pop_t=dur * 0.5, color=(255, 90, 60))
    return cv


def b3_ten_min(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky(cv, T, heat=lt / dur)
    k = ease(np.clip(lt / (dur * 0.85), 0, 1))
    thermo(cv, -220, 40, 80 + 20 * k, h=800)
    box(cv, 260, -260, 230, 85, DARK, r=26)
    label(cv, f'{int(k * 10)} MIN', 260, -250, 90, (255, 214, 64))
    if k > 0.95:
        label(cv, '+20°F', 260, 0, 120, (255, 90, 60))
    return cv


def inside_cam(cv, T, heat, face='worried', sweat=0.0, fog=0.0):
    cv.background('#5b3a2a', '#2a1a14', vignette=0.45)
    box(cv, 0, 380, 520, 380, ramp('#3b3f4a'), r=60)                         # seat
    guy(cv, 0, 640, 1.0, face=face, legs=False, ground=False, arms=((15, 0), (15, 0)), shirt=ORANGE,
        tint=('#ff5a3a', 0.35 * heat))
    if sweat > 0:
        for k in range(int(6 * sweat) + 1):
            ph = (T * 0.7 + k * 0.37) % 1
            x = -110 + (k * 53) % 220
            y = -420 + ph * 260 * (1 - 0.8 * fog)
            cv.shape(rotell(x, y, 10, 16, 0), (x - 12, y - 18, x + 12, y + 18), ramp('#9fe0ff'), ow=3, shadow=0)
    if fog > 0:
        cv.img = np.ascontiguousarray(cv.img * (1 - 0.35 * fog) + np.array([0.85, 0.8, 0.75], np.float32) * 0.35 * fog, dtype=np.float32)


def b4_sweat(lt, dur, T):
    cv = Canvas(0, -150, 1.0)
    inside_cam(cv, T, 0.4, sweat=np.clip(lt / 0.8, 0, 1))
    hook_text(cv, 'SWEAT', lt, y=-680, pop_t=0.3, color=(120, 210, 255))
    return cv


def b5_cant_dry(lt, dur, T):
    cv = Canvas(0, -150, 1.0)
    inside_cam(cv, T, 0.6, sweat=1.0, fog=np.clip(lt / 1.0, 0, 1))
    hook_text(cv, "CAN'T DRY", lt, y=-680, pop_t=dur * 0.5, color=(255, 90, 80))
    return cv


def b6_heart(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1418', '#1a0a0c', vignette=0.45)
    bpm = 80 + 70 * lt / dur
    beat = max(0, np.sin(T * bpm / 60 * 2 * np.pi)) ** 4
    heart_icon(cv, 0, -100, 1.6, beat)
    box(cv, 0, 420, 260, 85, DARK, r=26)
    label(cv, f'{int(bpm)} BPM', 0, 430, 90, (255, 90, 80))
    for k in range(4):
        a = k * np.pi / 2 + 0.6
        arrows(cv, [((np.cos(a) * 260, -100 + np.sin(a) * 260), (np.cos(a) * 460, -100 + np.sin(a) * 460))], (255, 150, 90), 10)
    return cv


def b7_heatstroke(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1418', '#1a0a0c', vignette=0.45)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    thermo(cv, 0, 0, 98.6 + (104 - 98.6) * k, lo=95, hi=106, h=900)
    label(cv, 'BODY', 0, 680, 60, (255, 255, 255))
    if k > 0.98:
        hook_text(cv, 'HEATSTROKE', lt, y=-720, size=120, pop_t=dur * 0.62, color=(255, 60, 50))
    return cv


def b8_pass_out(lt, dur, T):
    cv = Canvas(0, -150, 1.0)
    k = np.clip(lt / dur, 0, 1)
    inside_cam(cv, T, 0.9, face='pain' if k < 0.7 else 'closed', sweat=1.0 - k, fog=0.5)
    for j in range(5):                                        # dizzy stars
        a = T * 4 + j * 1.25
        label(cv, '*', np.cos(a) * 200, -560 + np.sin(a) * 60, 80, (255, 230, 90), a=float(np.clip(1.3 - k * 1.5, 0, 1)))
    if k > 0.6:
        cv.vignette(1.6 * (k - 0.6))
    return cv


def b9_kids(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1418', '#1a0a0c', vignette=0.45)
    k = np.clip(lt / (dur * 0.8), 0, 1)
    thermo(cv, -260, -40, 98.6 + 1.2 * k, lo=95, hi=106, h=700)
    thermo(cv, 260, -40, 98.6 + 5.2 * k, lo=95, hi=106, h=700)
    guy(cv, -260, 860, 0.38, face='worried', shirt=ORANGE)
    guy(cv, 260, 860, 0.24, face='worried', shirt=PINK)
    hook_text(cv, '3 TO 5X FASTER', lt, y=-720, size=96, pop_t=dur * 0.5, color=(255, 90, 60))
    return cv


def b10_crack(lt, dur, T):
    cv = Canvas(120, 120, 1.6)
    sky(cv, T, heat=1)
    car(cv, 0, 300, 1.4, T, crack=1.0, inside_heat=0.9)
    for k in range(3):
        ph = (T * 1.2 + k / 3) % 1
        disc(cv, 170 + ph * 60, -20 - ph * 120, 8 + 6 * ph, ramp('#ff7a3a'), ow=0, alpha=0.6 * (1 - ph), shadow=0)
    hook_text(cv, 'BARELY HELPS', lt, y=-640, size=96, pop_t=dur * 0.45, color=(255, 236, 80))
    return cv


def b11_never(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    sky(cv, T, heat=1)
    car(cv, 0, 380, 1.4, T, person=False, kid=True, dog=True, inside_heat=0.8)
    s_ = pop(lt, 0.5, 0.3)
    if s_:
        disc(cv, 0, -300, 210 * s_, ramp('#e2483d'))
        disc(cv, 0, -300, 165 * s_, ramp('#ffffff'), ow=0, shadow=0)
        line(cv, [(-120 * s_, -300 - 120 * s_), (120 * s_, -300 + 120 * s_)], 34, flat(hexc('#e2483d')), ow=0)
        label(cv, 'NO', 0, -470 - 60 * s_, 70, (255, 255, 255))
    label(cv, 'NOT EVEN 1 MINUTE', 0, 760, 66, (255, 255, 255))
    return cv


def b12_escape(lt, dur, T):
    cv = Canvas(0, -100, 1.0)
    sky(cv, T, heat=1)
    k = lt / dur
    car(cv, 0, 380, 1.5, T, broken=float(np.clip((k - 0.55) / 0.15, 0, 1)), inside_heat=0.7)
    if k < 0.5:
        for j in range(3):
            line(cv, [(80 + j * 40, -160), (140 + j * 60, -260)], 10, flat(hexc('#ffe14d')))
        label(cv, 'HONK!', 230, -330, 90, (255, 236, 80))
    else:
        label(cv, 'SIDE WINDOW', -180, -330, 80, (120, 255, 140))
        label(cv, 'NOT THE FRONT', -180, -230, 60, (255, 255, 255))
    return cv


BEATS = [b0_hook, b1_outside, b2_trapped, b3_ten_min, b4_sweat, b5_cant_dry, b6_heart, b7_heatstroke,
         b8_pass_out, b9_kids, b10_crack, b11_never, b12_escape]

if __name__ == '__main__':
    run(BEATS)
