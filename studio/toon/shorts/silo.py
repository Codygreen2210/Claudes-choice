#!/usr/bin/env python3
"""Why you should never stand on grain in a silo. Toon engine v3, timed to the narration.

    python3 studio/toon/shorts/silo.py times.json out.mp4 [--still T out.png]

Seamless loop: the last beat shows the opening shot running up to its own start (same scene,
same clock), so the final frame is the frame just before frame one, and the last words
"...and that's" run into the first, "why you should never stand on grain in a silo."
Facts: Great Plains Center for Agricultural Health via Beef Magazine (4 s to the knees, 20 s
to full burial, body weight + 600 lb to free someone waist deep, crusted "bridged" grain).
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import *          # noqa: F401,F403
import common

for _f in ('/usr/share/fonts/opentype/inter/Inter-Black.otf', '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'):
    if os.path.exists(_f):
        common.FONT = _f
        break

GRAIN = ramp('#e2b84c', '#a9802a', '#ffe08a')
CRUST = ramp('#9c7a3a', '#6b5224', '#c29d58')
STEEL = ramp('#a7b0ba', '#6d7782', '#dfe6ec')
DARK = ramp('#2b2f38', '#191c22', '#454b57')
ORANGE = ramp('#ff8a2a', '#c4561a', '#ffbf7a')
YEL = ramp('#ffd23f', '#d09a10', '#fff08a')
BLUE = ramp('#3d7fd8', '#2a559a', '#7fb4ff')
GREENR = ramp('#3fbf6a', '#25804a', '#7fe8a0')
WALL_X = 470
FLOOR = 1100


# ------------------------------------------------------------------ the silo set
def surface(level, funnel, fw=420, t=0.0, crack=None):
    def ys(X):
        dip = funnel * np.clip(1 - np.abs(X) / fw, 0, 1) ** 1.6
        ripple = 6 * np.sin(X * 0.035 + t * 3) * (0.3 + min(funnel / 300, 1))
        return level + dip + ripple
    return ys


def silo_inside(cv, T, level=300, funnel=0.0, guy_x=0.0, sink=0.0, face='happy', arms=((20, 0), (20, 0)),
                guy=True, flow=0.0, crust=False, void=None, tube=None, hole=True, jump=0.0, tint_dark=0.0,
                shirt=None):
    cv.background('#2b2a35', '#121117', vignette=0.45)
    # back wall: corrugated steel lit from a hatch above
    box(cv, 0, 300, WALL_X + 60, 1100, DARK, r=10, shadow=0, ow=3)
    for x in range(-WALL_X, WALL_X + 1, 56):
        line(cv, [(x, -800), (x, FLOOR)], 6, flat(hexc('#3a3f4a')))
    cv.glow(circle(0, -900, 60), (-80, -980, 80, -820), '#fff2c0', 140, 0.55)
    ys = surface(level, funnel, t=T)
    # the person (drawn before the grain so the grain buries them)
    if guy:
        gy = ys(np.array([guy_x]))[0] + sink - 60 * jump
        common.guy(cv, guy_x, gy, 0.62, face=face, arms=arms, shirt=shirt or ORANGE)
    # grain body
    def f(X, Y):
        return np.maximum(ys(X) - Y, np.abs(X) - WALL_X)
    if void is not None:                         # crusted top with a hollow pocket under it
        vx, vy, vr, cave = void
        hollow = rotell(vx, vy, vr, vr * 0.45, 0)
        f0 = f
        f = lambda X, Y: np.maximum(f0(X, Y), -hollow(X, Y)) if cave < 1 else f0(X, Y)
    cv.shape(f, (-WALL_X - 10, level - 60, WALL_X + 10, FLOOR + 40), GRAIN, ow=5, bevel=70, shadow=0.25)
    if crust:
        cf = lambda X, Y: np.maximum(np.maximum(ys(X) - Y, Y - ys(X) - 46), np.abs(X) - WALL_X)
        cv.shape(cf, (-WALL_X - 10, level - 40, WALL_X + 10, level + 60), CRUST, ow=4, bevel=20, shadow=0)
    # kernels: specks that drift with the flow toward the centre and down
    def kern(i, v, tt):
        x0 = (v[0] - 0.5) * 2 * WALL_X
        depth = v[1] * (FLOOR - level)
        x = x0 * (1 - (flow * (tt * 0.25 + v[2])) % 1 * 0.6) if flow > 0 else x0
        y = ys(np.array([x]))[0] + 20 + depth + (flow * tt * 120 * (1 - v[1])) % 80
        if y > FLOOR or abs(x) > WALL_X - 10:
            return None
        return x, y, 0.55
    specks(cv, T, kern, 220, (150, 110, 40), 6, seed=3)
    if hole:
        box(cv, 0, FLOOR + 20, 90, 30, DARK, r=12, ow=4)
    if tint_dark > 0:
        cv.img = np.ascontiguousarray(cv.img * (1 - 0.55 * tint_dark), dtype=np.float32)
    return ys


def floor_out(cv, T, rate):
    """Auger under the hole and kernels streaming out of the bin."""
    box(cv, 0, FLOOR + 160, 600, 70, DARK, r=30)
    ang = T * 900 * rate
    for k in range(9):
        x = -520 + k * 130
        a = np.radians(ang + k * 40)
        line(cv, [(x, FLOOR + 160 - 50 * np.cos(a)), (x + 60, FLOOR + 160 + 50 * np.cos(a))], 10, STEEL, ow=3)
    if rate > 0:
        specks(cv, T, lambda i, v, tt: ((v[0] - 0.5) * 120, FLOOR + 40 + ((tt * 700 + v[1] * 160) % 160), 1.0),
               60, (230, 180, 70), 9, seed=9)


def timer(cv, label_, k=1.0, color=(255, 90, 80)):
    y = cv.cy - 640 / cv.zoom                      # pinned near the top of the screen whatever the camera does
    box(cv, 0, y, 230 / cv.zoom, 85 / cv.zoom, DARK, r=26, shadow=0.3)
    label(cv, label_, 0, y + 10 / cv.zoom, 96 / cv.zoom, color)


def arrows(cv, pts, col=(255, 255, 255), w=12):
    for (a, b) in pts:
        line(cv, [a, b], w, flat(np.array(col) / 255.0), ow=3)
        d = np.array(b) - np.array(a); d = d / (np.linalg.norm(d) + 1e-6); n = np.array([-d[1], d[0]])
        tip = np.array(b)
        line(cv, [tuple(tip - d * 36 + n * 24), tuple(tip), tuple(tip - d * 36 - n * 24)], w, flat(np.array(col) / 255.0), ow=3)


# ------------------------------------------------------------------ beats: fn(lt, dur, T) -> Canvas
def b0_hook(lt, dur, T):
    """Opening shot. Also used, run up to its own start, as the last beat (lt < 0)."""
    z = 0.95 + 0.04 * np.clip((lt + 3) / 5, 0, 1)
    cv = Canvas(0, 150, z)
    silo_inside(cv, T, face='happy', arms=((30, 10), (150, 40)))
    if lt >= 0:
        hook_text(cv, 'NEVER STAND HERE', lt, y=-640, size=96, pop_t=0.12, color=(255, 236, 80))
    return cv


def b1_solid(lt, dur, T):
    cv = Canvas(0, 150, 0.99)
    j = abs(np.sin(lt * 5.5)) * (lt < dur * 0.8)
    silo_inside(cv, T, face='happy', arms=((150, 30), (150, 30)), jump=j)
    label(cv, 'LOOKS SOLID', 0, -560, 70, (255, 255, 255))
    return cv


def b2_hole(lt, dur, T):
    cy = keys(lt, [(0, 150), (dur * 0.6, 900)])
    cv = Canvas(0, cy, 1.0)
    silo_inside(cv, T, flow=1.0)
    floor_out(cv, T, 1.0)
    if lt > dur * 0.4:
        label(cv, 'DRAINING', 0, FLOOR - 120, 70, (255, 214, 64))
    return cv


def b3_funnel(lt, dur, T):
    cy = keys(lt, [(0, 900), (0.6, 300), (dur, 250)])
    cv = Canvas(0, cy, 0.95)
    fd = 260 * ease(np.clip(lt / dur, 0, 1))
    gx = 0.0
    ys = silo_inside(cv, T, funnel=fd, guy_x=gx, sink=30 * lt / dur, face='worried', flow=1.0)
    if lt > 0.4:
        arrows(cv, [((-380, ys(np.array([-380]))[0] - 40), (-120, ys(np.array([-120]))[0] - 40)),
                    ((380, ys(np.array([380]))[0] - 40), (120, ys(np.array([120]))[0] - 40))], (255, 230, 120))
    hook_text(cv, 'FUNNEL', lt, y=-620, pop_t=dur * 0.5)
    return cv


def b4_knees(lt, dur, T):
    cv = Canvas(0, 260, 1.15)
    silo_inside(cv, T, funnel=260, guy_x=0, sink=60 + 180 * ease(np.clip(lt / dur, 0, 1)), face='shock',
                arms=((60, 40), (60, 40)), flow=1.0)
    s = min(4.0, lt / dur * 4 + 0.01)
    timer(cv, f'{s:0.1f} SEC')
    return cv


def b5_stuck(lt, dur, T):
    cv = Canvas(0, 300, 1.2)
    wob = np.sin(lt * 14) * 25
    silo_inside(cv, T, funnel=260, guy_x=0, sink=250 + 20 * lt / dur, face='scream',
                arms=((140 + wob, 40), (140 - wob, 40)), flow=1.0)
    for k in range(2):
        yy = 520 + 30 * np.sin(lt * 10 + k)
        arrows(cv, [((-60 + 240 * k, yy), (-60 + 240 * k, yy - 90))], (255, 90, 80), 10)
    label(cv, 'STUCK', 0, -560, 80, (255, 90, 80))
    return cv


def b6_gone(lt, dur, T):
    cv = Canvas(0, 250, 1.0)
    k = ease(np.clip(lt / (dur * 0.7), 0, 1))
    silo_inside(cv, T, funnel=260 * (1 - 0.4 * k), guy_x=0, sink=270 + 700 * k, face='scream',
                arms=((175, 0), (170, 10)), flow=1.0 - k, tint_dark=0.6 * k)
    timer(cv, f'{min(20, 4 + 16 * k):0.0f} SEC')
    return cv


def xray_body(cv, cx, top, s, squeeze, cracks, T):
    """Glowing x-ray skeleton of the chest: spine, ribs that bow inward with squeeze, lungs that flatten."""
    bone = flat(hexc('#e8f4ff'))
    glow = '#9fd8ff'
    sp = [(cx, top + 40 * s), (cx, top + 620 * s)]
    line(cv, sp, 16 * s, bone)
    for i in range(7):                                         # vertebra knobs
        dot(cv, cx, top + (90 + i * 75) * s, 14 * s, bone)
    # lungs: soft translucent shapes that get pressed flat
    lw = (1 - 0.45 * squeeze)
    for sx in (-1, 1):
        cv.shape(rotell(cx + sx * 95 * s * lw, top + 260 * s, 80 * s * lw, 150 * s, sx * 8),
                 (cx + sx * 95 * s - 120 * s, top + 90 * s, cx + sx * 95 * s + 120 * s, top + 430 * s),
                 ramp('#5f8fb8', '#3d6688', '#9cc6ea'), ow=0, shadow=0, alpha=0.55, rim=0, spec=0)
    # ribs: arcs from the spine, pushed inward at their outer ends
    for i in range(6):
        y0 = top + (110 + i * 62) * s
        for sx in (-1, 1):
            reach = (210 - i * 8) * s * (1 - 0.32 * squeeze)
            pts = [(cx + sx * (12 + reach * u), y0 + 40 * s * np.sin(u * 2.6) + 50 * s * u * u) for u in np.linspace(0, 1, 9)]
            line(cv, pts, 9 * s, bone)
            if cracks > i / 6:
                cxk, cyk = pts[6]
                cv.glow(circle(cxk, cyk, 10 * s), (cxk - 30, cyk - 30, cxk + 30, cyk + 30), '#ff4a3a', 26 * s, 0.9)
                line(cv, [(cxk - 12 * s, cyk - 16 * s), (cxk + 4 * s, cyk), (cxk - 6 * s, cyk + 6 * s), (cxk + 12 * s, cyk + 18 * s)], 4 * s,
                     flat(hexc('#ff5a4a')))
    # collarbones and skull outline
    for sx in (-1, 1):
        line(cv, [(cx, top + 60 * s), (cx + sx * 190 * s, top + 40 * s)], 12 * s, bone)
    cv.shape(subtract(circle(cx, top - 150 * s, 120 * s), circle(cx, top - 150 * s, 104 * s)),
             (cx - 125 * s, top - 275 * s, cx + 125 * s, top - 25 * s), bone, ow=0, shadow=0, flat=True)
    cv.glow(circle(cx, top + 250 * s, 260 * s), (cx - 300 * s, top - 20 * s, cx + 300 * s, top + 560 * s), glow, 60 * s, 0.12)


def b7_chest(lt, dur, T):
    """Half sunk, the camera pushes in, the frame turns to x-ray: the grain's weight crushing the chest."""
    z = keys(lt, [(0, 1.0), (0.7, 1.75)])
    cv = Canvas(0, 380, z)
    silo_inside(cv, T, guy_x=0, sink=330, face='pain', arms=((60, 20), (60, 20)), flow=0.2)
    k = ease(np.clip((lt - 0.6) / 0.45, 0, 1))
    if k > 0:
        g = cv.img.mean(2, keepdims=True)
        xr = (1 - g) * 0.35 * np.array([0.55, 0.75, 1.0], np.float32) + np.array([0.02, 0.05, 0.10], np.float32)
        cv.img = np.ascontiguousarray(cv.img * (1 - k) + xr * k, dtype=np.float32)
        squeeze = 0.5 + 0.5 * np.sin(np.clip(lt - 1.0, 0, None) * 2.2 - 1.57)
        squeeze = min(1.0, (lt - 0.6) / (dur * 0.6)) * (0.7 + 0.3 * squeeze)
        cracks = np.clip((lt - dur * 0.45) / (dur * 0.35), 0, 1)
        xray_body(cv, 0, 230, 0.55, squeeze, cracks, T)
        # the grain's weight: arrows bearing down and in from every side
        for sx in (-1, 1):
            for yy in (300, 420):
                x0 = sx * 330
                arrows(cv, [((x0, yy), (sx * (230 - 60 * squeeze), yy))], (255, 150, 90), 10)
        for xx in (-210, 210):
            arrows(cv, [((xx, 120), (xx, 210 + 20 * squeeze))], (255, 150, 90), 10)
        label(cv, 'X-RAY', 0, 650, 44, (159, 216, 255), a=k)
    hook_text(cv, 'CRUSHING WEIGHT', lt, y=-640, size=92, pop_t=dur * 0.5, color=(255, 90, 80))
    return cv


def b8_force(lt, dur, T):
    cv = Canvas(0, 150, 0.9)
    silo_inside(cv, T, guy_x=0, sink=150, face='pain', arms=((175, 0), (175, 0)), flow=0)
    pull = ease(np.clip(lt / (dur * 0.6), 0, 1))
    line(cv, [(0, -80), (0, -760)], 10, flat(hexc('#d9c29a')), ow=4)
    disc(cv, 0, -760, 50, STEEL)
    # pull gauge
    gx, gy = 300, -560
    disc(cv, gx, gy, 150, STEEL)
    disc(cv, gx, gy, 125, ramp('#f4f1ea'), ow=3, bevel=10)
    a = np.radians(-210 + 240 * pull)
    line(cv, [(gx, gy), (gx + np.cos(a) * 105, gy + np.sin(a) * 105)], 8, flat(hexc('#e2483d')))
    dot(cv, gx, gy, 14)
    if pull > 0.6:
        label(cv, 'YOUR WEIGHT', gx - 40, gy + 230, 54, (255, 255, 255))
        label(cv, '+ 600 LB', gx - 40, gy + 300, 82, (255, 214, 64))
    return cv


def b9_crust(lt, dur, T):
    cv = Canvas(0, 250, 0.95)
    reveal = ease(np.clip((lt - 0.8) / 0.8, 0, 1))
    silo_inside(cv, T, guy=False, crust=True, void=(0, 600, 330 * max(reveal, 0.01), 0), hole=True)
    if reveal > 0.3:
        label(cv, 'EMPTY POCKET', 0, 610, 66, (255, 214, 64), a=reveal)
    hook_text(cv, 'CRUST', lt, y=-560, pop_t=0.3, color=(255, 236, 80))
    return cv


def b10_cave(lt, dur, T):
    cv = Canvas(0, 300, 1.0)
    k = np.clip((lt - dur * 0.4) / 0.35, 0, 1)
    gx = 0.0
    fall = 600 * k ** 2
    if k > 0:
        # the crust gives way: the surface drops into the pocket
        silo_inside(cv, T, guy_x=gx, sink=fall + 120 * k, face='scream', arms=((170, 0), (170, 0)),
                    funnel=420 * ease(k), crust=k < 0.5, void=(0, 600, 330, 1))
    else:
        silo_inside(cv, T, guy_x=gx, face='calm', arms=((15, 0), (15, 0)), crust=True, void=(0, 600, 330, 0),
                    jump=abs(np.sin(lt * 6)) * 0.3)
    if 0.3 < k < 0.9:
        cv.flash('#ffffff', 0.25 * (1 - k))
    return cv


def b11_tube(lt, dur, T):
    cv = Canvas(0, 250, 1.05)
    silo_inside(cv, T, guy_x=0, sink=380, face='worried', arms=((60, 20), (60, 20)))
    drop = ease(np.clip(lt / (dur * 0.6), 0, 1))
    y0 = -900 + 1100 * drop
    for sx in (-1, 1):
        box(cv, sx * 230, y0 + 300, 22, 380, STEEL, r=8, ow=5)
    if drop > 0.8:
        arrows(cv, [((-420, 420), (-280, 420)), ((420, 420), (280, 420))], (120, 200, 255))
        label(cv, 'RESCUE TUBE', 0, -560, 70, (120, 200, 255))
    return cv


def b12_scoop(lt, dur, T):
    cv = Canvas(0, 250, 1.05)
    up = ease(np.clip(lt / dur, 0, 1))
    silo_inside(cv, T, guy_x=0, sink=380 - 260 * up, face='happy' if up > 0.6 else 'worried', arms=((60, 20), (60, 20)))
    for sx in (-1, 1):
        box(cv, sx * 230, 500, 22, 380, STEEL, r=8, ow=5)
    by = 520 - 320 * ((lt * 1.6) % 1)
    box(cv, 140, by, 60, 50, BLUE, r=12)
    line(cv, [(140, by - 50), (140, -700)], 6, flat(hexc('#d9c29a')))
    return cv


def b13_cut(lt, dur, T):
    """Outside the silo: cutters open holes low on the wall and the grain pours out."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#9fd2ff', '#e9f6ff', vignette=0.25)
    box(cv, 0, 900, 1200, 300, ramp('#5fae4a'), r=0, ow=0, shadow=0)
    box(cv, 0, 100, 380, 820, STEEL, r=30)
    for x in range(-340, 341, 48):
        line(cv, [(x, -680), (x, 880)], 5, flat(hexc('#8a939d')))
    cv.shape(ellipse(0, -720, 400, 110), (-400, -830, 400, -610), STEEL, ow=5)
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    for i, hx in enumerate((-220, 0, 220)):
        if k > i / 3:
            cv.shape(poly([(hx - 60, 560), (hx + 60, 560), (hx, 700)]), (hx - 70, 550, hx + 70, 710), DARK, ow=4, shadow=0)
            pour = ease(np.clip((lt - dur * 0.5) / (dur * 0.4), 0, 1))
            if pour > 0:
                cv.shape(smooth(40, capsule(hx, 640, hx + (i - 1) * 160, 900, 30, 60), ellipse(hx + (i - 1) * 160, 920, 160 * pour, 50)),
                         (hx - 260, 600, hx + 420, 980), GRAIN, ow=4)
            else:
                specks(cv, T, lambda j, v, tt: (hx + (v[0] - 0.5) * 120, 600 + (v[1] - 0.5) * 120, 1.0), 20, (255, 210, 90), 7, seed=i)
    label(cv, 'DRAIN IT', 0, -880, 84, (255, 255, 255))
    return cv


BEATS = [b0_hook, b1_solid, b2_hole, b3_funnel, b4_knees, b5_stuck, b6_gone, b7_chest, b8_force,
         b9_crust, b10_cave, b11_tube, b12_scoop, b13_cut, None]       # last: the opening shot, running up to its start


def caption(cv, txt, k):
    words = txt.split()
    shown = ' '.join(words[:max(1, int(np.ceil(np.clip(k, 0, 1) * len(words))))])
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(common.FONT, 60)
    lines_, cur = [], ''
    for w in shown.split():
        test = (cur + ' ' + w).strip()
        if d.textlength(test, font=f) > W - 160:
            lines_.append(cur); cur = w
        else:
            cur = test
    lines_.append(cur)
    y = H - 440 - 74 * (len(lines_) - 1)
    for ln in lines_:
        tw = d.textlength(ln, font=f)
        d.text(((W - tw) / 2, y), ln, font=f, fill=(255, 255, 255, 255), stroke_width=9, stroke_fill=(20, 14, 26, 255))
        y += 74
    cv.overlay(im)


def render_frame(T, TM, LINES):
    total = TM['total']
    for i, (t0, d) in enumerate(zip(TM['starts'], TM['durs'])):
        if t0 <= T < t0 + d or i == len(TM['starts']) - 1:
            lt = T - t0
            if BEATS[i] is None:
                cv = b0_hook(T - total, 1.0, T - total)     # opening shot on the opening clock, just before frame one
            else:
                cv = BEATS[i](lt, d, T)
            v0, v1 = TM['voice'][i]
            caption(cv, LINES[i]['text'], (T - v0) / max(v1 - v0, 0.3) + 0.05)
            if lt < 0.1 and i > 0 and BEATS[i] is not None:
                cv.flash('#ffffff', 0.3 * (1 - lt / 0.1))
            return cv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('times'); ap.add_argument('lines'); ap.add_argument('out')
    ap.add_argument('--still', type=float)
    a = ap.parse_args()
    TM = json.load(open(a.times)); LINES = json.load(open(a.lines))
    if a.still is not None:
        Image.fromarray(render_frame(a.still, TM, LINES).to_uint8()).save(a.out); return
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    for i in range(int(round(TM['total'] * FPS))):
        ff.stdin.write(render_frame(i / FPS, TM, LINES).to_uint8().tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    main()
