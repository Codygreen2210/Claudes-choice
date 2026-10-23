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


def fall_scene(cv, T, h_ft, face='scream', fire=0.0, show_guy=True, hud=True):
    """Falling camera: rock walls rush up past him, the lava lake rises toward his feet as h_ft drops to 0."""
    q = heat_kw(h_ft)
    hot = float(np.clip(q / E_SURF, 0, 1))
    cv.background('#3a1a20', '#8a2a1a', vignette=0.3)
    off = (260 - h_ft) * 7.0
    for sx in (-1, 1):                                                         # the crater walls, scrolling up
        x0 = sx * 560; x1 = sx * 330
        pts = [(x0, -980), (x1 + sx * 20 * np.sin(0.0), -980), (x1, 980), (x0, 980)]
        cv.shape(poly(pts), bbox_of(pts, 4), ROCKV, ow=4, shadow=0, bevel=10)
        for k in range(9):
            yy = -980 + ((k * 230 - off) % 1960)
            line(cv, [(x0, yy), ((x0 + x1) / 2, yy + 14 * sx), (x1 + sx * 6, yy - 8)], 6, flat(hexc('#2a1e1e')), a=0.7)
    lake_y = 220 + h_ft * 2.8
    if lake_y < 1000:
        box(cv, 0, lake_y + 500, 700, 500, LAVA, r=0, ow=0, shadow=0)
        for q_ in range(7):
            cx = -480 + ((q_ * 160 + T * 18) % 960)
            cy = lake_y + 50 + (q_ % 3) * 110
            pts = [(cx + np.cos(a) * 70, cy + np.sin(a) * 26) for a in np.linspace(0, 2 * np.pi, 7)[:-1]]
            cv.shape(poly(pts), bbox_of(pts, 4), CRUST, ow=3, shadow=0)
        cv.glow(rbox(0, lake_y, 600, 10, 5), (-600, lake_y - 40, 600, lake_y + 40), '#ff6a1a', 140, 0.4 + 0.5 * hot)
    v = speed_mph(h_ft)
    for q_ in range(int(6 + v / 6)):                                           # wind streaks rushing up
        x = -300 + (q_ * 73) % 600
        y = 960 - ((T * (300 + v * 30) + q_ * 157) % 1960)
        line(cv, [(x, y), (x, y + 60 + v * 1.5)], 3, flat(hexc('#ffd8b0')), a=0.35)
    if show_guy:
        faller(cv, 0, 200, 0.75, T, fire=fire, face=face)
        if hot > 0.3:
            cv.flash('#ff6a1a', 0.12 * hot)
    if hot > 0.1:
        import cv2
        H_, W_ = cv.img.shape[:2]
        yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
        cv.img = np.ascontiguousarray(cv2.remap(cv.img, xx + 6 * hot * np.sin(yy / 22 + T * 9), yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
    if hud:
        hud_(cv, h_ft, v, q)


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

def b0_hook(lt, dur, T):
    """lt < -1.0: on the rim, peering over (the loop line). Then he slips and the camera falls with him."""
    cv = Canvas(0, 0, 1.0)
    if lt < -1.0:
        crater(cv, T)
        lean = float(np.clip((lt + 2.5) / 1.2, 0, 1))
        guy(cv, RIM[0] + 30 * lean, RIM[1], 0.6, face='worried', look=(1, 1), arms=((12, 0), (40 * lean, 20)))
        if lt > -1.3:
            label(cv, 'SLIP!', RIM[0] + 160, RIM[1] - 420, 70, (255, 255, 255))
    else:
        h = 260 - 2.0 * (lt + 1.0)
        fall_scene(cv, T, h)
        hook_text(cv, '260 FEET', lt + 1.0, y=-800, size=160, color=(255, 140, 40))
    return cv


def b1_suns(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    h = 252 - 14 * lt / dur
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
    cv = Canvas(0, 0, 1.0)
    h = 200 - 100 * ease(float(np.clip(lt / (dur * 0.6), 0, 1)))
    fall_scene(cv, T, h, face='pain')
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
    """Slow motion just above the lava: a 4-second stopwatch, and his heat dose still under the PAIN line."""
    cv = Canvas(0, 0, 1.0)
    h = 20 - 12 * lt / dur
    fall_scene(cv, T * 0.25, h, face='shock')
    cx, cy = -300, -200
    disc(cv, cx, cy - 115, 14, STEEL)
    disc(cv, cx, cy, 100, ramp('#ffffff', '#d8dde4', '#ffffff'))
    a = 2 * np.pi * min(1, lt / (dur * 0.6)) * (4 / 60) * 15
    line(cv, [(cx, cy), (cx + np.sin(a) * 80, cy - np.cos(a) * 80)], 8, flat(hexc('#e2302a')))
    label(cv, '4 SEC', cx, cy + 150, 54, (255, 255, 255))
    dose_meter(cv, min(1, lt / (dur * 0.6)))
    if lt > dur * 0.45:
        hook_text(cv, 'TOO FAST', lt, y=-800, size=170, pop_t=dur * 0.45, color=(127, 255, 160))
    return cv


def b6_slam(lt, dur, T):
    """He hits the lava at almost 90 mph: SMACK, a dent, rings, and he stays on top."""
    cv = Canvas(0, 0, 1.0)
    t_hit = 0.35
    if lt < t_hit:
        fall_scene(cv, T, 8 * (1 - lt / t_hit), face='shock')
    else:
        fall_scene(cv, T, 0.0, show_guy=False, hud=False)
        e = lt - t_hit
        dent = float(np.exp(-e * 3))
        cv.shape(ellipse(0, 230, 220 * (1 + 0.3 * (1 - dent)), 40), (-300, 180, 300, 280), ramp('#d8400a', '#a82a0a', '#ff8a2a'), ow=3, shadow=0)
        guy(cv, 0, 240 + 18 * dent, 0.75, face='shock', arms=((90, 0), (90, 0)))
        for q_ in range(3):
            ph = (e * 1.2 + q_ / 3) % 1
            r = 120 + 320 * ph
            cv.shape(subtract(ellipse(0, 240, r, r * 0.22), ellipse(0, 240, r - 10, r * 0.22 - 6)), (-r - 2, 240 - r * 0.25, r + 2, 240 + r * 0.25 + 12),
                     ramp('#ffd23f'), ow=0, shadow=0, flat=True, alpha=1 - ph)
        hud_(cv, 0, speed_mph(0), heat_kw(0))
        hook_text(cv, 'SMACK', lt, y=-800, size=190, pop_t=t_hit, color=(255, 255, 255))
        label(cv, '3X DENSER', 0, -440, 60, (255, 170, 60))
    return cv


def b7_flames(lt, dur, T):
    """On the surface: rock near 2,000 degrees, and he bursts into (cartoon) flames."""
    cv = Canvas(0, 0, 1.0)
    fall_scene(cv, T, 0.0, show_guy=False, hud=False)
    k = float(np.clip(lt / (dur * 0.5), 0, 1))
    guy(cv, 0, 240, 0.75, face='scream', arms=((150, 30), (150, 30)), tint=('#ff6a1a', 0.35 * k))
    for q_ in range(9):                                                        # flames licking up all round him
        ph = (T * 1.8 + q_ * 0.29) % 1
        fx = -170 + q_ * 42 + 8 * np.sin(T * 6 + q_)
        fy = 250 - 40 * ph - 30 * (q_ % 3)
        flame(cv, fx, fy, (46 + 18 * (q_ % 2)) * (1 - 0.4 * ph) * k, T + q_)
    badge(cv, '~2,000°F', y=-620, col=(255, 140, 40), w=360)
    hook_text(cv, 'FLAMES', lt, y=-800, size=180, pop_t=dur * 0.3, color=(255, 90, 40))
    return cv


def b8_bag(lt, dur, T):
    """2002: the scientist heaves the bag off the same rim; it hits, dents, and the lava bursts up around it."""
    cv = Canvas(0, 0, 1.0)
    crater(cv, T)
    split = dur * 0.45
    if lt < split:
        k = float(np.clip(lt / (split * 0.8), 0, 1))
        guy(cv, RIM[0] + 20, RIM[1], 0.6, face='calm', coat=True, glasses=True, shirt=COAT, arms=((60 + 80 * k, 40), (60 + 80 * k, 40)))
        bx = RIM[0] + 120 + 260 * k * k
        by = RIM[1] - 560 * 0.6 + 1200 * max(0, k - 0.5) ** 2
        cv.shape(smooth(20, ellipse(bx, by, 60, 70), circle(bx, by - 70, 22)), (bx - 65, by - 95, bx + 65, by + 75), BAG)
        badge(cv, '2002', y=-760, x=250, col=(255, 236, 80), w=240)
    else:
        e = lt - split
        cv.shape(ellipse(60, LAKE_Y + 30, 160, 34), (-110, LAKE_Y - 10, 230, LAKE_Y + 70), ramp('#d8400a', '#a82a0a', '#ff8a2a'), ow=3, shadow=0)
        cv.shape(smooth(20, ellipse(60, LAKE_Y + 10, 70, 46), circle(60, LAKE_Y - 30, 22)), (-15, LAKE_Y - 60, 135, LAKE_Y + 60), ramp('#2a2a2a'))
        rng = np.random.default_rng(8)
        for q_ in range(28):
            vx, vy = rng.uniform(-260, 260), rng.uniform(-900, -500)
            px_, py_ = 60 + vx * e, LAKE_Y + vy * e + 900 * e * e
            if py_ < LAKE_Y + 30:
                disc(cv, px_, py_, 14 + (q_ % 3) * 6, LAVA, ow=2.5, shadow=0)
        hook_text(cv, 'BURST', lt, y=-800, size=190, pop_t=split, color=(255, 140, 40))
    return cv


BEATS = [b0_hook, b1_suns, b2_speed, b3_deadly, b4_twentysix, b5_twist, b6_slam, b7_flames, b8_bag]

if __name__ == '__main__':
    run(BEATS)
