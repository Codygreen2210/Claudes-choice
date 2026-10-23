#!/usr/bin/env python3
"""What would really happen if you fell into lava, told height by height on the way down (260 ft rim, Erta Ale numbers).
Opens with the camera already falling with him; loops back into it (the last line plays over him on the rim, slipping)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

LAVA = ramp('#ff7a1a', '#d8400a', '#ffd23f')
CRUST = ramp('#3a2a28', '#1e1414', '#5a4440')
ROCKV = ramp('#4a3a3a', '#2a2020', '#6a5a58')
SKYV = ('#3a1a20', '#8a2a1a')
FLAME = ramp('#ff8a2a', '#e24a1a', '#ffd23f')
BAG = ramp('#3a5a3a', '#203a20', '#5a7a5a')
LAKE_Y = 260
RIM = (-330, -300)                               # where he stands on the rim (his feet)


def crater(cv, T, shimmer=0.0):
    """Inside the crater: red smoky sky, dark rock walls, a lava lake with drifting crust plates and popping bubbles.
    A warning sign on the rim carries the one Easter egg (a little thumbs-up sticker)."""
    cv.background(*SKYV, vignette=0.3)
    for i in range(5):                                                         # smoke drifting up
        x = -400 + i * 200 + 40 * np.sin(T * 0.4 + i)
        y = -700 - ((T * 30 + i * 90) % 200)
        cloud(cv, x, y, 110, a=0.35, col=ramp('#5a3a3a', '#3a2424', '#7a5a5a'))
    left = [(-560, -300), (-420, -310), (-330, -296), (-240, -300), (-200, -150), (-230, 0), (-180, LAKE_Y), (-560, LAKE_Y)]
    right = [(560, -380), (420, -400), (330, -370), (280, -200), (300, -40), (230, LAKE_Y), (560, LAKE_Y)]
    for pts in (left, right):                                                  # jagged cliff walls with rock layers
        cv.shape(poly(pts), bbox_of(pts, 4), ROCKV, ow=4, shadow=0, bevel=10)
    for k in range(6):
        yy = -240 + k * 85
        line(cv, [(-560, yy), (-380, yy + 12), (-230 + 10 * (k % 2), yy - 6)], 5, flat(hexc('#2a1e1e')), a=0.6)
        line(cv, [(560, yy - 60), (420, yy - 48), (300, yy - 64)], 5, flat(hexc('#2a1e1e')), a=0.6)
    line(cv, [(-470, -360), (-470, -300)], 8, WOOD, ow=2, flat=False)          # the warning sign
    box(cv, -470, -390, 60, 34, ramp('#ffd23f', '#d09a10', '#fff08a'), r=6)
    label(cv, 'DANGER', -470, -384, 22, (60, 30, 10), stroke=0)
    thumb_icon(cv, -430, -360, 11)
    box(cv, 0, LAKE_Y + 360, 700, 360, LAVA, r=0, ow=0, shadow=0)             # the lake
    rng = np.random.default_rng(4)
    for q in range(9):                                                         # crust plates drifting
        cx = -500 + ((q * 140 + T * 18) % 1100)
        cy = LAKE_Y + 60 + (q % 3) * 130
        pts = [(cx + np.cos(a) * (60 + 20 * rng.random()), cy + np.sin(a) * (24 + 10 * rng.random())) for a in np.linspace(0, 2 * np.pi, 7)[:-1]]
        cv.shape(poly(pts), bbox_of(pts, 4), CRUST, ow=3, shadow=0)
    for q in range(5):                                                         # bubbles popping
        ph = (T * 0.6 + q / 5) % 1
        bx = -400 + q * 200 + 30 * np.sin(q)
        disc(cv, bx, LAKE_Y + 40 + q * 30, 10 + 30 * ph, ramp('#ffd23f', '#ff8a2a', '#fff6a0'), ow=2, shadow=0, alpha=1 - ph)
    cv.glow(rbox(0, LAKE_Y, 600, 10, 5), (-600, LAKE_Y - 40, 600, LAKE_Y + 40), '#ff6a1a', 120, 0.55)
    if shimmer > 0:
        import cv2
        H_, W_ = cv.img.shape[:2]
        yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
        cv.img = np.ascontiguousarray(cv2.remap(cv.img, xx + shimmer * 5 * np.sin(yy / 24 + T * 9), yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))


def faller(cv, x, y, s, T, fire=0.0, face='scream'):
    flail = 20 * np.sin(T * 12)
    guy(cv, x, y, s, face=face, arms=((150 + flail, 30), (150 - flail, 30)), tint=('#ff6a1a', 0.25 * fire) if fire > 0 else None)
    if fire > 0:                                                               # cartoon flames licking up from his shoes and legs
        for q in range(6):
            ph = (T * 3 + q / 6) % 1
            fx = x + (-60 + q * 24) * s
            fy = y - (20 + 200 * ph) * s
            cv.shape(smooth(8, circle(fx, fy, (34 - 16 * ph) * s), circle(fx, fy - 26 * s, (18 - 8 * ph) * s)), (fx - 40 * s, fy - 60 * s, fx + 40 * s, fy + 40 * s),
                     FLAME, ow=2.5, shadow=0, alpha=fire * (1 - ph))


def fall_pos(lt):
    """Standing on the rim until lt = -0.6, then falling toward the middle of the lake."""
    if lt < -1.0:
        return RIM[0], RIM[1], False
    u = lt + 1.0
    x = RIM[0] + 330 * (1 - np.exp(-u * 1.5))
    y = RIM[1] + 100 * u
    return x, y, True


# ---------------------------------------------------------------- the fall, by the numbers
# Erta Ale-style lava lake: rim 80 m (260 ft) above the lava (Smithsonian GVP, 2001), lake ~60 m wide (2009),
# crust ~474 C with glowing cracks ~1,000 C. Radiant heat at height h over a disk: E * R^2 / (R^2 + h^2).
H_M, LAKE_R = 80.0, 30.0
E_SURF = 0.9 * 5.67e-8 * (0.9 * (474 + 273.15) ** 4 + 0.1 * (1000 + 273.15) ** 4) / 1000.0     # ~27.7 kW/m^2
SUN = 1.0                                                                       # clear-day sun ~1 kW/m^2 (WHOI)


def heat_kw(h_ft):
    h = h_ft * 0.3048
    return E_SURF * LAKE_R ** 2 / (LAKE_R ** 2 + h ** 2)


def speed_mph(h_ft):
    return np.sqrt(2 * 9.81 * max(0.0, H_M - h_ft * 0.3048)) * 2.237


def tumbler(cv, x, y, s, T, fire=0.0, face='scream', speed=1.0, xray=0.0, heat=0.0):
    """Him falling for real: the whole body tumbles and rolls, arms and legs flailing, smeared by the speed."""
    ang = 38 * np.sin(T * 1.9) + 14 * np.sin(T * 4.3)
    hip = (x, y - 400 * s)
    if xray > 0:
        draw = lambda L: xray_body(L, x, y, s, T, heat=heat, solid=True)
    else:
        draw = lambda L: faller(L, x, y, s, T, fire=fire, face=face)
    layer_xform(cv, draw, hip[0], hip[1], angle=ang, blur=int(6 + 14 * speed))


def fall_scene(cv, T, h_ft, face='scream', fire=0.0, show_guy=True, hud=True, xray=0.0, slow=1.0):
    """Falling camera: rock walls tearing up past him, wind streaks, shake, and the lava lake rising toward him."""
    q = heat_kw(h_ft)
    hot = float(np.clip(q / E_SURF, 0, 1))
    v = speed_mph(h_ft)
    cv.background('#3a1a20', '#8a2a1a', vignette=0.3)
    off = (T * slow * (900 + 40 * v)) % 1960                                   # walls rush by FAST
    for sx in (-1, 1):
        x0 = sx * 560; x1 = sx * 330
        pts = [(x0, -980), (x1, -980), (x1, 980), (x0, 980)]
        cv.shape(poly(pts), bbox_of(pts, 4), ROCKV, ow=4, shadow=0, bevel=10)
        for k in range(9):
            yy = -980 + ((k * 230 - off) % 1960)
            line(cv, [(x0, yy), ((x0 + x1) / 2, yy + 14 * sx), (x1 + sx * 6, yy - 8)], 6, flat(hexc('#2a1e1e')), a=0.7)
            line(cv, [(x1 + sx * 2, yy), (x1 + sx * 2, yy + 120)], 10, flat(hexc('#6a5a58')), a=0.25)   # smear
    lake_y = 220 + h_ft * 2.8
    if lake_y < 1000:
        box(cv, 0, lake_y + 500, 700, 500, LAVA, r=0, ow=0, shadow=0)
        for q_ in range(7):
            cx = -480 + ((q_ * 160 + T * 18) % 960)
            cy = lake_y + 50 + (q_ % 3) * 110
            pts = [(cx + np.cos(a) * 70, cy + np.sin(a) * 26) for a in np.linspace(0, 2 * np.pi, 7)[:-1]]
            cv.shape(poly(pts), bbox_of(pts, 4), CRUST, ow=3, shadow=0)
        cv.glow(rbox(0, lake_y, 600, 10, 5), (-600, lake_y - 40, 600, lake_y + 40), '#ff6a1a', 140, 0.4 + 0.5 * hot)
    for q_ in range(int(10 + v / 4)):                                          # wind streaks
        x = -300 + (q_ * 73) % 600
        y = 960 - ((T * slow * (1400 + v * 40) + q_ * 157) % 1960)
        line(cv, [(x, y), (x, y + 90 + v * 2.5)], 3, flat(hexc('#ffd8b0')), a=0.4)
    if show_guy:
        gx, gy = 30 * np.sin(T * 1.3), 220 + 25 * np.sin(T * 2.1)
        tumbler(cv, gx, gy, 0.72, T, fire=fire, face=face, speed=min(1, v / 90) * slow, xray=xray, heat=hot)
        if hot > 0.3 and xray == 0:
            cv.flash('#ff6a1a', 0.12 * hot)
    import cv2
    H_, W_ = cv.img.shape[:2]
    sh = (v / 90) * 10 * slow                                                  # camera shake with speed
    dx_, dy_ = sh * np.sin(T * 47), sh * np.cos(T * 41)
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    cv.img = np.ascontiguousarray(cv2.remap(cv.img, (xx + dx_ + 6 * hot * np.sin(yy / 22 + T * 9)).astype(np.float32), (yy + dy_).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
    if hud:
        hud_(cv, h_ft, v, q)


# ---------------------------------------------------------------- x-ray damage
XRB = ramp('#5f86b8', '#2f4f78', '#a8c8f0')
BONEX = ramp('#f4f8ff', '#b8c8dc', '#ffffff')


def xray_body(cv, x, y, s, T, heat=0.0, breaks=0.0, solid=False):
    """See-through body with his skeleton. heat glows his skin from below; breaks draws red fracture lines."""
    P = lambda px, py: (x + px * s, y + py * s)
    body = smooth(30 * s, circle(*P(0, -762), 105 * s), rbox(*P(0, -490), 115 * s, 110 * s, 60 * s),
                  capsule(*P(-104, -590), *P(-240, -760), 40 * s), capsule(*P(104, -590), *P(240, -760), 40 * s),
                  capsule(*P(-50, -380), *P(-56, -20), 48 * s), capsule(*P(50, -380), *P(56, -20), 48 * s))
    if solid:                                                                  # on a keyed layer: opaque, heat turns it from blue to red
        c0, c1 = np.array([0.18, 0.29, 0.47]), np.array([0.85, 0.22, 0.08])
        c = c0 + (c1 - c0) * float(np.clip(heat, 0, 1))
        hx_ = '#%02x%02x%02x' % tuple(int(v * 255) for v in c)
        cv.shape(body, (x - 300 * s, y - 900 * s, x + 300 * s, y + 20 * s), ramp(hx_), ow=4, shadow=0)
    else:
        cv.shape(body, (x - 300 * s, y - 900 * s, x + 300 * s, y + 20 * s), XRB, ow=4, alpha=0.45, shadow=0)
        if heat > 0:
            cv.glow(body, (x - 300 * s, y - 900 * s, x + 300 * s, y + 20 * s), '#ff4a1a', 40 * s, 0.9 * heat)
    cv.shape(subtract(circle(*P(0, -770), 82 * s), circle(*P(0, -770), 66 * s)), (x - 90 * s, y - 860 * s, x + 90 * s, y - 680 * s), BONEX, ow=2.5, shadow=0)   # skull
    for sx in (-1, 1):
        disc(cv, *P(sx * 30, -770), 16 * s, ramp('#2f4f78'), ow=0, shadow=0)
    for k in range(10):                                                        # spine
        disc(cv, *P(0, -660 + k * 30), 12 * s, BONEX, ow=2, shadow=0)
    for k in range(5):                                                         # ribs
        yy = -590 + k * 34
        for sx in (-1, 1):
            line(cv, [P(0, yy), P(sx * 70, yy - 6), P(sx * 92, yy + 20)], 7 * s, BONEX, a=0.95)
    cv.shape(subtract(ellipse(*P(0, -360), 80 * s, 40 * s), ellipse(*P(0, -350), 44 * s, 22 * s)), (x - 90 * s, y - 410 * s, x + 90 * s, y - 310 * s), BONEX, ow=2.5, shadow=0)   # pelvis
    for sx in (-1, 1):
        line(cv, [P(sx * 104, -590), P(sx * 175, -680)], 11 * s, BONEX, ow=2, flat=False)        # arms
        line(cv, [P(sx * 175, -680), P(sx * 236, -760)], 9 * s, BONEX, ow=2, flat=False)
        line(cv, [P(sx * 44, -350), P(sx * 52, -200)], 14 * s, BONEX, ow=2, flat=False)          # thigh
        line(cv, [P(sx * 52, -190), P(sx * 56, -30)], 12 * s, BONEX, ow=2, flat=False)           # shin
    if breaks > 0:                                                             # fractures: legs, pelvis, spine, skull
        for (bx, by), seed in (((-50, -260), 1), ((54, -110), 2), ((0, -360), 3), ((0, -540), 4), ((20, -800), 5)):
            if breaks > seed / 6:
                p0 = P(bx - 22, by - 14); p1 = P(bx + 22, by + 14)
                pts = jagged(p0, p1, seed, depth=3, rough=0.6)
                line(cv, pts, 7 * s, flat(hexc('#ff2a2a')))
                cv.glow(circle(*P(bx, by), 20 * s), (x + (bx - 40) * s, y + (by - 40) * s, x + (bx + 40) * s, y + (by + 40) * s), '#ff2a2a', 20 * s, 0.6)


def skin_layers(cv, T, k):
    """Cross-section of skin: epidermis, dermis, fat, muscle. A burn front eats down through them as k goes 0..1."""
    cv.background('#1a0a0c', '#0a0406', vignette=0.35)
    layers = (('EPIDERMIS', 40, ramp('#f8c8b0', '#d8a088', '#ffe0d0')), ('DERMIS', 150, ramp('#f08a8a', '#c05a5a', '#ffb0b0')),
              ('FAT', 160, ramp('#ffe28a', '#d8b850', '#fff2c0')), ('MUSCLE', 260, ramp('#c8404a', '#8a2028', '#e8707a')))
    y = -360
    tops = []
    for name, h, col in layers:
        box(cv, 0, y + h / 2, 470, h / 2, col, r=4, ow=3, shadow=0)
        label(cv, name, -300, y + h / 2 + 8, 30, (255, 255, 255))
        tops.append(y); y += h
    for q in range(8):                                                         # flames on top
        ph = (T * 2 + q * 0.37) % 1
        flame(cv, -400 + q * 115, -380 - 20 * ph, 50 * (1 - 0.3 * ph), T + q)
    depth = -360 + k * 340
    if depth > -360:
        cv.shape(rbox(0, (-360 + depth) / 2, 470, (depth + 360) / 2 + 1, 4), (-480, -370, 480, depth + 10), ramp('#3a1410', '#1a0806', '#5a2a20'), ow=0, shadow=0, alpha=0.85)
    for txt, d_, yy in (('1ST DEGREE', 0.12, -340), ('2ND DEGREE', 0.45, -240), ('3RD DEGREE', 0.95, -40)):
        if k > d_:
            box(cv, 300, yy, 150, 32, DARK, r=14)
            label(cv, txt, 300, yy + 8, 40, (255, 200, 120))


def hud_(cv, h_ft, v, q):
    """Height, speed and heat read-outs, top of screen under the hook word."""
    for x, txt, col in ((-250, f'{int(round(h_ft))} FT', (255, 255, 255)), (0, f'{int(round(v))} MPH', (255, 236, 80)),
                        (250, f'{int(q / SUN)} SUNS' if q >= 9.5 else f'{q / SUN:.1f} SUNS', (255, 140, 40))):
        box(cv, x, -620, 118, 44, DARK, r=20)
        label(cv, txt, x, -612, 46, col)
    k = float(np.clip(q / E_SURF, 0, 1))
    box(cv, 0, -540, 360, 14, DARK, r=8)
    if k > 0.01:
        box(cv, -360 + 360 * k, -540, 360 * k, 10, ramp('#ffd23f') if k < 0.4 else ramp('#ff4a1a'), r=6, ow=0, shadow=0)


def flame(cv, x, y, r, T):
    """A cartoon flame: round base, flickering pointed tip, yellow core."""
    if r < 2:
        return
    w = r * 0.35 * np.sin(T * 9)
    outer = smooth(r * 0.4, circle(x, y, r), poly([(x - r * 0.85, y - r * 0.2), (x + r * 0.85, y - r * 0.2), (x + w, y - r * 2.6)]))
    cv.shape(outer, (x - r * 1.1, y - r * 2.8, x + r * 1.1, y + r * 1.1), FLAME, ow=3, shadow=0)
    inner = smooth(r * 0.3, circle(x, y + r * 0.15, r * 0.55), poly([(x - r * 0.45, y), (x + r * 0.45, y), (x + w * 0.6, y - r * 1.5)]))
    cv.shape(inner, (x - r * 0.7, y - r * 1.7, x + r * 0.7, y + r * 0.8), ramp('#fff6a0', '#ffd23f', '#ffffff'), ow=0, shadow=0)


def suns_row(cv, n, y, T, size=26):
    """Little suns stacked up beside him (left side first, then right), never over his head."""
    n = int(n)
    for i in range(n):
        side = -1 if i % 2 == 0 else 1
        j = i // 2
        r_, c_ = divmod(j, 3)
        sun(cv, side * (180 + c_ * 52), y + r_ * 56, size, T)


def dose_meter(cv, k):
    """The heat dose for the whole fall stays under the PAIN line."""
    box(cv, 300, -150, 50, 300, DARK, r=20)
    pain_y = -150 + 300 - 600 * (92 / 290) * 0.95
    fill = 600 * (85 / 290) * 0.95 * k
    if fill > 2:
        box(cv, 300, 150 - fill / 2 + 0, 34, fill / 2, ramp('#ffd23f'), r=14, ow=0, shadow=0)
    line(cv, [(240, pain_y), (360, pain_y)], 6, flat(hexc('#ff4a1a')))
    label(cv, 'PAIN', 300, pain_y - 30, 34, (255, 120, 90))
    label(cv, 'HEAT DOSE', 300, 200, 34, (255, 255, 255))


# ---------------------------------------------------------------- beats

def rim_shot(cv, T, lt0, slip_at):
    """On the rim, peering over; at slip_at his foot goes and he pitches forward off the edge (tumbling)."""
    crater(cv, T)
    if lt0 < slip_at:
        lean = float(np.clip((lt0 - slip_at + 1.4) / 1.2, 0, 1))
        guy(cv, RIM[0] + 30 * lean, RIM[1], 0.6, face='worried', look=(1, 1), arms=((12, 0), (40 * lean, 20)))
    else:
        u = lt0 - slip_at
        x = RIM[0] + 30 + 260 * u
        y = RIM[1] + 900 * u * u
        layer_xform(cv, lambda L: faller(L, x, y, 0.6, T, face='scream'), x, y - 240, angle=-140 * u, blur=int(4 + 30 * u))
        if u < 0.3:
            label(cv, 'SLIP!', RIM[0] + 160, RIM[1] - 420, 70, (255, 255, 255))


def b0_hook(lt, dur, T):
    """The loop line: on the rim; he slips at lt = -1.0, pitches over, and the camera whips down to fall with him."""
    slip, whip0, whip1 = -1.0, -0.55, -0.25
    if lt < whip0:
        cv = Canvas(0, 0, 1.0)
        rim_shot(cv, T, lt, slip)
        return cv
    h = 260 - 2.0 * max(0.0, lt - whip0)
    fall = Canvas(0, 0, 1.0)
    fall_scene(fall, T, h)
    if lt < whip1:
        rim = Canvas(0, 0, 1.0)
        rim_shot(rim, T, lt, slip)
        fall = whip(rim, fall, (lt - whip0) / (whip1 - whip0))
    hook_text(fall, '260 FEET', lt - whip0, y=-800, size=160, color=(255, 140, 40))
    return fall


def b1_suns(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    h = 254 - 14 * lt / dur
    fall_scene(cv, T, h)
    k = float(np.clip((lt - 0.4) / 0.6, 0, 1))
    if k > 0:
        suns_row(cv, 3, -330, T, size=24 * k + 1)
    hook_text(cv, '3+ SUNS', lt, y=-800, size=170, pop_t=dur * 0.45, color=(255, 214, 63))
    return cv


def b2_speed(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    h = 238 - 38 * ease(float(np.clip(lt / (dur * 0.85), 0, 1)))
    fall_scene(cv, T, h)
    hook_text(cv, '40+ MPH', lt, y=-800, size=170, pop_t=dur * 0.6, color=(255, 236, 80))
    return cv


def b3_deadly(lt, dur, T):
    """X-ray: his skin glowing hot on the way down, the heat level that kills in about a minute."""
    cv = Canvas(0, 0, 1.0)
    h = 200 - 100 * ease(float(np.clip(lt / (dur * 0.6), 0, 1)))
    fall_scene(cv, T, h, xray=1.0)
    cv.flash('#0e1430', 0.0)
    label(cv, 'SKIN HEATING UP', 0, -440, 54, (255, 120, 80))
    if lt > dur * 0.55:
        hook_text(cv, 'DEADLY HEAT', lt, y=-800, size=130, pop_t=dur * 0.55, color=(255, 90, 40))
    return cv


def b4_twentysix(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    h = 100 - 80 * ease(float(np.clip(lt / (dur * 0.5), 0, 1)))
    fall_scene(cv, T, h, face='pain')
    if lt > dur * 0.5:
        n = int(26 * min(1, (lt - dur * 0.5) / (dur * 0.35)))
        suns_row(cv, n, -380, T, size=20)
        hook_text(cv, '26 SUNS', lt, y=-800, size=170, pop_t=dur * 0.5, color=(255, 140, 40))
    return cv


def b5_twist(lt, dur, T):
    """Freeze-frame slow motion just above the lava: a 4-second stopwatch, his heat dose still under the PAIN line."""
    cv = Canvas(0, 0, 1.0)
    h = 20 - 12 * lt / dur
    fall_scene(cv, T * 0.15 + 3.0, h, face='shock', slow=0.15)
    cx, cy = -300, -200
    disc(cv, cx, cy - 115, 14, STEEL)
    disc(cv, cx, cy, 100, ramp('#ffffff', '#d8dde4', '#ffffff'))
    a = 2 * np.pi * min(1, lt / (dur * 0.6)) * (4 / 60) * 15
    line(cv, [(cx, cy), (cx + np.sin(a) * 80, cy - np.cos(a) * 80)], 8, flat(hexc('#e2302a')))
    label(cv, '4 SEC', cx, cy + 150, 54, (255, 255, 255))
    dose_meter(cv, min(1, lt / (dur * 0.6)))
    label(cv, 'SLOW MOTION', 0, 600, 40, (255, 255, 255))
    if lt > dur * 0.45:
        hook_text(cv, 'TOO FAST', lt, y=-800, size=170, pop_t=dur * 0.45, color=(127, 255, 160))
    return cv


def b6_slam(lt, dur, T):
    """He slams onto the lava at almost 90 mph: SMACK, then an x-ray of what that impact does to his bones."""
    cv = Canvas(0, 0, 1.0)
    t_hit, t_x = 0.3, 1.1
    if lt < t_hit:
        fall_scene(cv, T, 8 * (1 - lt / t_hit), face='shock')
        return cv
    fall_scene(cv, T, 0.0, show_guy=False, hud=False)
    e = lt - t_hit
    dent = float(np.exp(-e * 3))
    cv.shape(ellipse(0, 230, 220 * (1 + 0.3 * (1 - dent)), 40), (-300, 180, 300, 280), ramp('#d8400a', '#a82a0a', '#ff8a2a'), ow=3, shadow=0)
    if lt < t_x:
        layer_xform(cv, lambda L: guy(L, 0, 240, 0.75, face='shock', arms=((90, 0), (90, 0))), 0, 240, sx=1 + 0.25 * dent, sy=1 - 0.3 * dent)   # squash on impact
        for q_ in range(3):
            ph = (e * 1.2 + q_ / 3) % 1
            r = 120 + 320 * ph
            cv.shape(subtract(ellipse(0, 240, r, r * 0.22), ellipse(0, 240, r - 10, r * 0.22 - 6)), (-r - 2, 240 - r * 0.25, r + 2, 240 + r * 0.25 + 12),
                     ramp('#ffd23f'), ow=0, shadow=0, flat=True, alpha=1 - ph)
        hook_text(cv, 'SMACK', lt, y=-800, size=190, pop_t=t_hit, color=(255, 255, 255))
        label(cv, '3X DENSER: NO SINKING', 0, -440, 50, (255, 170, 60))
        if lt < t_hit + 0.08:
            cv.flash('#ffffff', 0.6)
    else:
        cv.flash('#0e1430', 0.75)
        xray_body(cv, 0, 260, 0.8, T, breaks=float(np.clip((lt - t_x) / 1.2, 0, 1)))
        badge(cv, '89 MPH IMPACT', y=-620, col=(255, 90, 80), w=520)
        hook_text(cv, 'BONES BREAK', lt, y=-800, size=140, pop_t=t_x + 0.3, color=(255, 90, 80))
    return cv


def b7_flames(lt, dur, T):
    """On the surface he bursts into flames; then a skin cross-section shows the burn eating down through the layers."""
    split = dur * 0.4
    if lt < split:
        cv = Canvas(0, 0, 1.0)
        fall_scene(cv, T, 0.0, show_guy=False, hud=False)
        k = float(np.clip(lt / (split * 0.7), 0, 1))
        guy(cv, 0, 240, 0.75, face='scream', arms=((150, 30), (150, 30)), tint=('#ff6a1a', 0.35 * k))
        for q_ in range(9):
            ph = (T * 1.8 + q_ * 0.29) % 1
            flame(cv, -170 + q_ * 42 + 8 * np.sin(T * 6 + q_), 250 - 40 * ph - 30 * (q_ % 3), (46 + 18 * (q_ % 2)) * (1 - 0.4 * ph) * k, T + q_)
        badge(cv, '~2,000°F', y=-620, col=(255, 140, 40), w=360)
        hook_text(cv, 'FLAMES', lt, y=-800, size=180, pop_t=0.3, color=(255, 90, 40))
        return cv
    cv = Canvas(0, 0, 1.0)
    skin_layers(cv, T, float(np.clip((lt - split) / ((dur - split) * 0.85), 0, 1)))
    hook_text(cv, 'BURNS', lt, y=-800, size=170, pop_t=split, color=(255, 120, 60))
    return cv


def b8_bag(lt, dur, T):
    """2002: one continuous move. The scientist heaves the bag, the camera whips down with it, it hits, lava bursts up."""
    t_throw, w0, w1 = dur * 0.30, dur * 0.30, dur * 0.42
    def rim(T_, lt_):
        cv = Canvas(0, 0, 1.0)
        crater(cv, T_)
        k = float(np.clip(lt_ / t_throw, 0, 1))
        guy(cv, RIM[0] + 20, RIM[1], 0.6, face='calm', coat=True, glasses=True, shirt=COAT, arms=((60 + 80 * k, 40), (60 + 80 * k, 40)))
        bx = RIM[0] + 120 + 260 * k * k
        by = RIM[1] - 560 * 0.6 + 600 * max(0, k - 0.6) ** 2
        layer_xform(cv, lambda L: L.shape(smooth(20, ellipse(bx, by, 60, 70), circle(bx, by - 70, 22)), (bx - 65, by - 95, bx + 65, by + 75), BAG), bx, by, angle=90 * k)
        badge(cv, '2002', y=-760, x=250, col=(255, 236, 80), w=240)
        return cv
    if lt < w0:
        return rim(T, lt)
    fall_k = float(np.clip((lt - w0) / (dur * 0.33), 0, 1))
    h = 260 * (1 - fall_k ** 2)
    cv = Canvas(0, 0, 1.0)
    if fall_k < 1:
        fall_scene(cv, T, h, show_guy=False, hud=False)
        layer_xform(cv, lambda L: L.shape(smooth(20, ellipse(0, 200, 60, 70), circle(0, 130, 22)), (-65, 100, 65, 275), BAG), 0, 200, angle=200 * fall_k, blur=20)
    else:
        fall_scene(cv, T, 0.0, show_guy=False, hud=False)
        e = lt - (w0 + dur * 0.33)
        cv.shape(ellipse(0, 235, 170, 36), (-180, 195, 180, 275), ramp('#d8400a', '#a82a0a', '#ff8a2a'), ow=3, shadow=0)
        cv.shape(smooth(20, ellipse(0, 215, 70, 46), circle(0, 175, 22)), (-75, 150, 75, 265), ramp('#2a2a2a'))
        rng = np.random.default_rng(8)
        for q_ in range(30):
            vx, vy = rng.uniform(-300, 300), rng.uniform(-1000, -500)
            px_, py_ = vx * e, 230 + vy * e + 900 * e * e
            if py_ < 240:
                disc(cv, px_, py_, 14 + (q_ % 3) * 6, LAVA, ow=2.5, shadow=0)
        hook_text(cv, 'BURST', lt, y=-800, size=190, pop_t=w0 + dur * 0.33, color=(255, 140, 40))
        label(cv, '66 LB BAG', 0, -440, 54, (255, 255, 255))
    if lt < w1:
        cv = whip(rim(T, lt), cv, (lt - w0) / (w1 - w0))
    return cv


BEATS = [b0_hook, b1_suns, b2_speed, b3_deadly, b4_twentysix, b5_twist, b6_slam, b7_flames, b8_bag]

if __name__ == '__main__':
    run(BEATS)
