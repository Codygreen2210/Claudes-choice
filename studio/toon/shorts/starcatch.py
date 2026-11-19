#!/usr/bin/env python3
"""SpaceX catches Starship back from orbit (Flight 15, Nov 14 2026; 'starship catch', a top rising YouTube search that week).
Opens on the ship dropping out of the sky, engines blazing, the tower's arms swinging in. Then: the launch (ship on its
booster), the booster's low-fuel alarm and its end in the Gulf, 14 laps of Earth in ~22 hours, the fiery way home (belly
hotter than lava), the ~18,000 black tiles, the belly-flop with four flaps beside a skydiver, the flip and engine burn,
the hover and the chopsticks closing, why catching matters (rockets thrown away vs. flown again like a plane), and the
payoff: a first, 'almost magic'.
Facts: EarthSky (Nov 2026: IFT-15, Ship 42 caught by the tower arms 'chopsticks'/Mechazilla on Nov 14 at Starbase after 14
orbits; booster aborted its return and was lost over the Gulf; first orbital upper stage caught in the air; NASA's Jared
Isaacman: 'Almost magic'). Daily Wire (Nov 2026: launch Nov 13 from Starbase, booster low-fuel alarm, ~22 hours, reuse 'like
an aircraft'). Wikipedia, Starship spacecraft (52.1 m tall; ~18,000 hexagonal tiles rated ~1,400 C / 2,600 F; four flaps).
Migflug (belly-first re-entry, flip upright before landing; orbital entry ~1,377 C)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403
import eas as E

DIVE = {}
STEEL = ramp('#d8dde4', '#9aa2ae', '#ffffff')
TILE = ramp('#26282e', '#121418', '#3e424c')
BOOST = ramp('#c8ccd2', '#7a808a', '#eef2f6')
TOWC = ramp('#4a4f58', '#2a2e34', '#6a707a')
FIRE = ramp('#ffd25a', '#ff7a1a', '#fff4c0')
SKY_DAY = ('#7ab8f0', '#d8ecff')
SKY_DUSK = ('#f2a65a', '#4a2a6a')
SPACE = ('#0a0e1e', '#000004')


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def _rot(pts, x, y, ang):
    c, s_ = np.cos(ang), np.sin(ang)
    return [(x + px * c - py * s_, y + px * s_ + py * c) for px, py in pts]


def flame(cv, x, y, s, ang, k, T, length=1.0):
    """engine plume pointing 'down' in the ship's frame (local +y)"""
    if k <= 0:
        return
    L = (260 + 40 * np.sin(T * 30)) * s * k * length
    for w, col, a in ((70, '#ff7a1a', 0.55), (45, '#ffd25a', 0.85), (20, '#fff8e0', 1.0)):
        pts = _rot([(-w * s, 0), (w * s, 0), (0, L * (w / 70) ** 0.3)], x, y, ang)
        cv.shape(poly(pts), pbox(pts, 10), ramp(col), ow=0, shadow=0, alpha=a)
    gx, gy = _rot([(0, L * 0.4)], x, y, ang)[0]
    cv.glow(circle(gx, gy, 60 * s), (gx - 300 * s, gy - 300 * s, gx + 300 * s, gy + 300 * s), '#ff8a2a', 80 * s, 0.5 * k)


def ship(cv, x, y, s, ang=0.0, fire=0.0, heat=0.0, T=0.0, flaps=0.0):
    """Starship (upper stage), center at (x,y), nose up at ang=0; black tiles on its belly (+x side)"""
    H, Wd = 420, 40
    body_ = [(-Wd, -H * 0.42), (Wd, -H * 0.42), (Wd, H * 0.5), (-Wd, H * 0.5)]
    nose = [(-Wd, -H * 0.42)] + [(-Wd * np.cos(t), -H * 0.42 - 90 * np.sin(t)) for t in np.linspace(0, np.pi, 12)][1:-1] + [(Wd, -H * 0.42)]
    sc = [(px * s, py * s) for px, py in body_]; nc = [(px * s, py * s) for px, py in nose]
    if heat > 0:                                                              # the plasma glow on the belly side
        hx, hy = _rot([(Wd * s + 30 * s, 0)], x, y, ang)[0]
        cv.glow(circle(hx, hy, 120 * s), (hx - 500 * s, hy - 500 * s, hx + 500 * s, hy + 500 * s), '#ff6a2a', 160 * s, 0.9 * heat)
        cv.glow(circle(hx, hy, 60 * s), (hx - 300 * s, hy - 300 * s, hx + 300 * s, hy + 300 * s), '#ff9ad8', 80 * s, 0.6 * heat)
    for fx, fy, side in ((-Wd, -H * 0.33, -1), (Wd, -H * 0.33, 1), (-Wd, H * 0.40, -1), (Wd, H * 0.40, 1)):   # four flaps
        fl = 0.35 * flaps * np.sin(T * 3 + fx)
        pts = [(fx, fy - 40), (fx + side * 38, fy - 30 + 20 * fl * 10), (fx + side * 38, fy + 40), (fx, fy + 50)]
        cv.shape(poly(_rot([(px * s, py * s) for px, py in pts], x, y, ang)), pbox(_rot([(px * s, py * s) for px, py in pts], x, y, ang), 6), TILE, ow=3)
    cv.shape(poly(_rot(sc, x, y, ang)), pbox(_rot(sc, x, y, ang), 6), STEEL, ow=4)
    cv.shape(poly(_rot(nc, x, y, ang)), pbox(_rot(nc, x, y, ang), 6), STEEL, ow=4)
    belly = [(Wd * 0.35, -H * 0.42), (Wd, -H * 0.42), (Wd, H * 0.5), (Wd * 0.35, H * 0.5)]
    bc = _rot([(px * s, py * s) for px, py in belly], x, y, ang)
    cv.shape(poly(bc), pbox(bc, 6), TILE, ow=0, shadow=0)
    bx, by = _rot([(0, H * 0.5 * s)], x, y, ang)[0]
    flame(cv, bx, by, s, ang, fire, T)


def booster(cv, x, y, s, ang=0.0, fire=0.0, T=0.0, alarm=0.0):
    H, Wd = 560, 40
    pts = [(-Wd, -H / 2), (Wd, -H / 2), (Wd, H / 2), (-Wd, H / 2)]
    p = _rot([(px * s, py * s) for px, py in pts], x, y, ang)
    cv.shape(poly(p), pbox(p, 6), BOOST, ow=4)
    for sd in (-1, 1):                                                        # grid fins
        f = _rot([(sd * Wd * s, -H / 2 * s + 20 * s), (sd * (Wd + 30) * s, -H / 2 * s + 10 * s), (sd * (Wd + 30) * s, -H / 2 * s + 60 * s), (sd * Wd * s, -H / 2 * s + 60 * s)], x, y, ang)
        cv.shape(poly(f), pbox(f, 6), TOWC, ow=3)
    if alarm > 0 and (T * 4) % 1 < 0.5:
        lx, ly = _rot([(0, -H * 0.3 * s)], x, y, ang)[0]
        cv.glow(circle(lx, ly, 30 * s), (lx - 200 * s, ly - 200 * s, lx + 200 * s, ly + 200 * s), '#ff2a1a', 70 * s, alarm)
        disc(cv, lx, ly, 22 * s, ramp('#ff3a2a'), ow=3)
    bx, by = _rot([(0, H / 2 * s)], x, y, ang)[0]
    flame(cv, bx, by, s * 1.4, ang, fire, T)


def tower(cv, x, y, s, arm=0.0, arm_y=-1000):
    """the launch tower (y = ground); its two arms ('chopsticks') swing in toward the ship at arm=1, spread apart at arm=0"""
    h = 1300 * s
    box(cv, x, y - h / 2, 70 * s, h / 2, TOWC, r=6 * s, ow=4)
    for j in range(16):
        yy = y - h + j * h / 16
        line(cv, [(x - 70 * s, yy), (x + 70 * s, yy + h / 16)], 6 * s, ramp('#2a2e34'))
    ay = y + arm_y * s
    box(cv, x, ay, 90 * s, 40 * s, ramp('#3a3f48'), r=8 * s, ow=4)          # the carriage
    L = 230 * s
    for sd in (-1, 1):
        ang = np.radians(sd * 38 * (1 - arm))
        x0, y0 = x - 70 * s, ay + sd * 18 * s
        line(cv, [(x0, y0), (x0 - L * np.cos(ang), y0 + L * np.sin(ang))], 30 * s, ramp('#e2b03d', '#a8801a', '#ffd870'), ow=4)
    box(cv, x, y + 20 * s, 260 * s, 30 * s, ramp('#9aa0a8', '#636a74', '#c8ced6'), r=6 * s)


def ground_scene(cv, sky=SKY_DAY, gy=760):
    cv.background(*sky, vignette=0.3)
    box(cv, 0, gy + 200, 1400, 220, ramp('#c8b080', '#9a8050', '#e8d0a0'), r=0, ow=0, shadow=0)    # Texas sand
    box(cv, 0, gy + 20, 1400, 30, ramp('#8a7a5a'), r=0, ow=0, shadow=0)


def smoke(cv, x, y, s, T, k, n=10):
    rr = np.random.default_rng(12)
    for j in range(n):
        u = (T * 0.4 + j / n) % 1
        dx = rr.uniform(-1, 1) * (100 + 500 * u) * s
        disc(cv, x + dx, y - 40 * u * s, (60 + 160 * u) * s, ramp('#e8e4dc', '#b0aaa0', '#ffffff'), ow=0, shadow=0, alpha=k * (0.85 - 0.6 * u))


def earth(cv, x, y, r):
    cv.glow(circle(x, y, r), (x - r - 200, y - r - 200, x + r + 200, y + r + 200), '#5ab8ff', 90, 0.6)
    disc(cv, x, y, r, ramp('#2a6ad8', '#123a8a', '#6ab0ff'), ow=4)
    rr = np.random.default_rng(3)
    for j in range(9):
        a = rr.uniform(0, 2 * np.pi); d = rr.uniform(0, 0.7) * r
        cv.shape(ellipse(x + d * np.cos(a), y + d * np.sin(a), rr.uniform(0.15, 0.3) * r, rr.uniform(0.1, 0.2) * r), (x - r, y - r, x + r, y + r), ramp('#4aa860', '#2a7a40', '#7ad890'), ow=0, shadow=0)


def stars(cv, n=60, seed=7):
    rr = np.random.default_rng(seed)
    for j in range(n):
        dot(cv, rr.uniform(-560, 560), rr.uniform(-1000, 1000), rr.uniform(2, 5), flat(hexc('#ffffff')), a=rr.uniform(0.3, 0.9))


def skydiver(cv, x, y, s, T):
    C = ramp('#ff7a2a', '#c84a10', '#ffb080')
    cv.shape(rbox(x, y, 70 * s, 26 * s, 20 * s), (x - 80 * s, y - 40 * s, x + 80 * s, y + 40 * s), C, ow=3)
    disc(cv, x + 90 * s, y - 6 * s, 26 * s, ramp('#3a3f48'), ow=3)
    for sd in (-1, 1):
        line(cv, [(x + 40 * s, y), (x + 70 * s, y + sd * 70 * s + 6 * np.sin(T * 9))], 14 * s, C, ow=2)
        line(cv, [(x - 60 * s, y), (x - 120 * s, y + sd * 50 * s + 6 * np.sin(T * 9 + 1))], 14 * s, C, ow=2)


# ---------------------------------------------------------------- beats
def b0_hook(lt, dur, T):
    """Frame one: the ship already dropping, engines roaring; the arms swing in and close on it."""
    cv = Canvas(0, 0, 1.0)
    ground_scene(cv, SKY_DUSK)
    u = float(np.clip((lt + 0.5) / (dur * 0.75), 0, 1))
    sy = -760 + 600 * (1 - (1 - u) ** 2)
    arm = ease(np.clip((u - 0.65) / 0.3, 0, 1))
    tower(cv, 300, 760, 1.0, arm=arm)
    ship(cv, 20, sy, 1.25, 0.0, fire=1.0 - 0.6 * arm, T=T)
    smoke(cv, 20, 760, 1.0, T, 0.5 * u)
    hook_text(cv, 'CAUGHT!', lt, y=-800, size=170, color=(255, 210, 80), pop_t=dur * 0.6)
    return cv


def b1_launch(lt, dur, T):
    k = ease(np.clip(lt / dur, 0, 1))
    sx_, sy_ = shake(lt, 0.0, 14, 1.5, 40)
    cv = Canvas(sx_, sy_ - 120 * k, 1.0)
    ground_scene(cv, SKY_DAY)
    tower(cv, 300, 760, 1.0, arm=0.0)
    y = 230 - 520 * k ** 1.6
    booster(cv, 20, y + 340, 1.0, fire=1.0, T=T)
    ship(cv, 20, y - 150, 1.0, T=T)
    smoke(cv, 20, 760, 1.2, T, 1.0, n=14)
    sbadge(cv, 'SOUTH TEXAS', -760, (255, 210, 80))
    return cv


def b2_booster(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a3a7a', '#5a9ad8', vignette=0.3)
    sep = ease(np.clip(lt / (dur * 0.35), 0, 1))
    ship(cv, 160, -560 - 400 * sep, 0.7, fire=1.0, T=T)
    u = float(np.clip((lt - dur * 0.3) / (dur * 0.6), 0, 1))
    bx = 40 - 400 * u; by = -260 + 960 * u * u; ang = -1.6 * u
    if u < 0.97:
        booster(cv, bx, by, 0.95, ang, fire=0.4 * (1 - u), T=T, alarm=1.0)
    box(cv, 0, 860, 1400, 160, ramp('#1a6ab0', '#0d3a70', '#3a8ad0'), r=0, ow=0, shadow=0)     # the Gulf
    if u > 0.9:                                                               # the end of it
        k = (u - 0.9) / 0.1
        cv.glow(circle(-400, 760, 80 + 200 * k), (-900, 300, 100, 1100), '#ff7a1a', 120, 0.9 * (1 - 0.5 * k))
        for j in range(8):
            a = -np.pi * j / 7
            disc(cv, -400 + 160 * k * np.cos(a), 760 + 160 * k * np.sin(a), 40, ramp('#ffffff', '#b0c8e0', '#ffffff'), ow=2)
    slabel(cv, 'LOW FUEL!', 0, -760 + 160, 120, (255, 80, 60), a=float(np.clip((lt - dur * 0.25) / 0.2, 0, 1)) * (0.6 + 0.4 * ((T * 4) % 1 < 0.5)))
    return cv


def b3_orbit(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background(*SPACE, vignette=0.4)
    stars(cv)
    earth(cv, 0, 80, 330)
    a = (lt / dur) * 2 * np.pi * 2.5 - np.pi / 2
    R = 460
    pts = [(R * np.cos(t), 80 + R * 0.45 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 60)]
    line(cv, pts, 4, flat(hexc('#9ad0ff')), a=0.5)
    sx, sy = R * np.cos(a), 80 + R * 0.45 * np.sin(a)
    if np.sin(a) > -0.3 or abs(sx) > 330:
        ship(cv, sx, sy, 0.3, ang=a + np.pi / 2, T=T)
    n = min(14, 1 + int(14 * lt / (dur * 0.85)))
    slabel(cv, 'LAP %d' % n, 0, -620, 120, (154, 208, 255))
    slabel(cv, '22 HOURS', 0, 640, 100, (255, 210, 80), a=float(np.clip((lt - dur * 0.5) / 0.3, 0, 1)))
    return cv


def b4_reentry(lt, dur, T):
    sx_, sy_ = shake(lt, 0.0, 10, 2.0, 35)
    cv = Canvas(sx_, sy_, 1.0)
    cv.background('#2a0a2a', '#ff6a2a', vignette=0.45)
    rr = np.random.default_rng(int(T * 24))
    for j in range(26):                                                       # streaks of hot air
        x = rr.uniform(-560, 560); y = rr.uniform(-1000, 1000)
        line(cv, [(x, y), (x + 40, y - 260)], 6, flat(hexc('#ffd0a0')), a=0.4)
    heat = ease(np.clip(lt / (dur * 0.5), 0, 1))
    ship(cv, -60, -120, 1.1, ang=np.radians(90), heat=heat, T=T)
    for j in range(14):                                                       # sparks peeling off
        u = (T * 1.6 + j / 14) % 1
        dot(cv, 120 + 600 * u, -60 + rr.uniform(-200, 200) * u - 300 * u, 8 * (1 - u) + 2, flat(hexc('#fff0a0')), a=1 - u)
    slabel(cv, 'HOTTER THAN LAVA', 0, -760, 84, (255, 180, 80), a=float(np.clip((lt - dur * 0.35) / 0.3, 0, 1)))
    return cv


def b5_tiles(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1a0a', '#ff7a2a', vignette=0.5)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    R = 62
    for r_ in range(-7, 8):
        for c in range(-5, 6):
            x = c * R * 1.75 + (r_ % 2) * R * 0.87; y = -160 + r_ * R * 1.5
            if np.hypot(x / 1.0, (y + 160) / 1.3) > 520 * (0.3 + 0.7 * k):
                continue
            hexp = [(x + R * 0.95 * np.cos(np.pi / 6 + j * np.pi / 3), y + R * 0.95 * np.sin(np.pi / 6 + j * np.pi / 3)) for j in range(6)]
            cv.shape(poly(hexp), pbox(hexp, 6), TILE, ow=4)
    cv.glow(rbox(0, -160, 520, 600, 40), (-900, -1000, 900, 700), '#ff8a2a', 120, 0.35 + 0.15 * np.sin(T * 4))
    cnt = int(18000 * k)
    slabel(cv, '%s TILES' % format(cnt, ','), 0, -800, 120, (255, 236, 80))
    slabel(cv, 'STEEL STAYS COOL', 0, 640, 90, (154, 220, 255), a=float(np.clip((lt - dur * 0.6) / 0.3, 0, 1)))
    return cv


def b6_bellyflop(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#5a9ad8', '#d8ecff', vignette=0.25)
    rr = np.random.default_rng(int(T * 8))
    for j in range(5):                                                       # clouds rushing up
        u = (T * 0.6 + j / 5) % 1
        x = -400 + j * 200; y = 1000 - 2000 * u
        for dx, r in ((-60, 70), (0, 100), (70, 70)):
            disc(cv, x + dx, y, r, ramp('#ffffff', '#d8e4f0', '#ffffff'), ow=0, shadow=0, alpha=0.8)
    ship(cv, 0, -330, 1.15, ang=np.radians(90), T=T, flaps=1.0)
    skydiver(cv, 0, 120, 1.3, T)
    sbadge(cv, 'BELLY FLOP', -780, (255, 210, 80))
    slabel(cv, '4 FLAPS', 0, -560, 90, WHT, a=float(np.clip((lt - dur * 0.45) / 0.3, 0, 1)))
    return cv


def b7_flip(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    ground_scene(cv, SKY_DUSK, gy=900)
    f = ease(np.clip((lt - 0.2) / (dur * 0.45), 0, 1))
    ang = np.radians(90 * (1 - f))
    burn = float(np.clip((lt - 0.15) / 0.2, 0, 1))
    ship(cv, 0, -150 + 120 * f, 1.15, ang=ang, fire=burn, T=T, flaps=1 - f)
    hook_text(cv, 'FLIP!', lt, y=-800, size=170, color=(255, 210, 80), pop_t=0.3)
    return cv


def b8_catch(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    ground_scene(cv, SKY_DUSK)
    u = float(np.clip(lt / (dur * 0.55), 0, 1))
    sy = -380 + 220 * ease(u)
    arm = ease(np.clip((lt - dur * 0.5) / (dur * 0.3), 0, 1))
    tower(cv, 300, 760, 1.0, arm=arm)
    ship(cv, 20, sy, 1.25, fire=1.0 - 0.9 * arm, T=T)
    smoke(cv, 20, 760, 1.0, T, 0.6 * (1 - arm))
    if arm > 0.95:
        hook_text(cv, 'CHOPSTICKS', lt, y=-800, size=140, color=(255, 210, 80), pop_t=dur * 0.8)
    return cv


def b9_reuse(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a2a4a', '#0a1020', vignette=0.4)
    k = float(np.clip((lt - dur * 0.45) / 0.3, 0, 1))
    # left: an old rocket going in the trash
    box(cv, -270, -60, 150, 190, METAL, r=20, ow=5)                          # the can
    for j in range(4):
        line(cv, [(-370 + j * 65, -220), (-370 + j * 65, 100)], 6, ramp('#6a707a'))
    ty = -680 + 420 * ease(np.clip(lt / (dur * 0.4), 0, 1))
    booster(cv, -270, ty, 0.45, ang=0.4, T=T)
    box(cv, -270, -250, 170, 26, METAL, r=8, ow=4)
    label(cv, 'USED ONCE', -270, 640, 60, (255, 120, 90))
    # right: the ship refueled, back up again, a loop arrow
    ship(cv, 270, -220 - 140 * k * np.sin(T * 2) ** 2, 0.7, fire=k, T=T)
    pts = [(270 + 230 * np.cos(t), -240 + 330 * np.sin(t)) for t in np.linspace(0.3, 2 * np.pi - 0.3, 30)]
    line(cv, pts, 12, flat(hexc('#5aff8a')), a=k)
    label(cv, 'FLY AGAIN', 270, 640, 60, (90, 255, 140), a=k)
    sbadge(cv, 'LIKE AN AIRPLANE', -780, (154, 255, 190))
    return cv


def b10_magic(lt, dur, T):
    cv = Canvas(0, 0, 1.0 + 0.06 * ease(np.clip(lt / dur, 0, 1)))
    ground_scene(cv, SKY_DUSK)
    tower(cv, 300, 760, 1.0, arm=1.0)
    ship(cv, 20, -160, 1.25, T=T)
    rr = np.random.default_rng(2)
    for j in range(16):                                                       # sparkles
        ph = (T * 0.8 + j / 16) % 1
        x = rr.uniform(-480, 480); y = rr.uniform(-700, 300)
        dot(cv, x, y, 10 * np.sin(np.pi * ph), flat(hexc('#fff4c0')), a=np.sin(np.pi * ph))
    hook_text(cv, 'FIRST EVER', lt, y=-800, size=150, color=(255, 210, 80), pop_t=0.3)
    slabel(cv, '"ALMOST MAGIC"', 0, -620, 90, WHT, a=float(np.clip((lt - dur * 0.6) / 0.3, 0, 1)))
    return cv


BEATS = [b0_hook, b1_launch, b2_booster, b3_orbit, b4_reentry, b5_tiles, b6_bellyflop, b7_flip, b8_catch, b9_reuse, b10_magic]

if __name__ == '__main__':
    run(BEATS)
