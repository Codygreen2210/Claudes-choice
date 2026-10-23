#!/usr/bin/env python3
"""What really happens when a vampire bat bites you. Opens as a vampire bat touches down on a sleeping man's bare foot,
wings still folding; loops back into it (the last line plays over the bat swooping in to land)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

FUR = ramp('#6a4a3a', '#3a2418', '#9a7a62')
WING = ramp('#3a2a30', '#1e1418', '#5a4450')
EARIN = ramp('#c88a90', '#9a5a60', '#e8b0b4')
NOSEC = ramp('#d88a8a', '#a85a5a', '#f0b0b0')
BLOOD = ramp('#c8102e', '#8a0a1e', '#ff4a5a')
SHEETN = ('#9aa8c8', '#6a7898')
BLANKN = ramp('#3a5a9a', '#24406e', '#5a7ac0')
SKINN = ramp('#e8b090', '#b07a62', '#ffd2b8')
TONGUE = ramp('#f08a9a', '#c05a6a', '#ffb8c4')
DRAC = ramp('#5adcc8', '#2a9a8a', '#a8fff0')
CLOT = flat(hexc('#ffd23f'))
CAVE = ('#2a2230', '#120e16')
ROCK = ramp('#4a4050', '#2a2430', '#6a6070')


def bat(cv, x, y, s, T, wings=0.0, flap=0.0, mouth=0.0, lick=0.0, full=0.0, flip=False, thin=0.0, sad=0.0, glow_nose=0.0):
    """A cartoon common vampire bat, front view. wings 0 folded .. 1 spread (flap beats them), flip hangs it upside down."""
    fy = -1 if flip else 1
    P = lambda dx, dy: (x + dx * s, y + fy * dy * s)
    bw = (1 + 0.55 * full - 0.25 * thin)
    if wings > 0.05:                                                           # spread wings with finger bones
        for sx in (-1, 1):
            beat = np.sin(T * 16) * flap
            sh = P(sx * 34, -10)
            tip = P(sx * (60 + 150 * wings), -10 - (60 + 70 * beat) * wings)
            mid = P(sx * (40 + 110 * wings), 40 + 30 * beat * wings)
            low = P(sx * 30, 60)
            scal = [P(sx * (40 + 110 * wings) + sx * 20 * np.sin(u * 3.14), 40 + 20 * u + 30 * beat * wings) for u in np.linspace(0, 1, 4)]
            pts = [sh, tip, mid] + scal[1:] + [low]
            cv.shape(poly(pts), bbox_of(pts, 6), WING, ow=3.5, shadow=0)
            for f in (tip, mid):
                line(cv, [sh, f], 4 * s, flat(hexc('#140c10')), a=0.9)
    else:                                                                      # folded wings like a cape, thumbs up top
        for sx in (-1, 1):
            pts = [P(sx * 20, -30), P(sx * 62 * bw, 0), P(sx * 56 * bw, 60), P(sx * 26, 70)]
            cv.shape(poly(pts), bbox_of(pts, 6), WING, ow=3.5, shadow=0)
            disc(cv, *P(sx * 60 * bw, -8), 7 * s, WING, ow=2, shadow=0)
    body_col = FUR if full < 0.3 else ramp('#8a3a3a', '#5a1a1a', '#b05a5a')
    cv.shape(ellipse(*P(0, 20 + 8 * full), 40 * s * bw, 52 * s * (1 + 0.3 * full - 0.15 * thin)), (x - 70 * s * bw, y - 60 * s, x + 70 * s * bw, y + 100 * s) if not flip else
             (x - 70 * s * bw, y - 100 * s, x + 70 * s * bw, y + 60 * s), body_col)
    for sx in (-1, 1):                                                         # ears
        pts = [P(sx * 12, -70), P(sx * 46, -140), P(sx * 38, -62)]
        cv.shape(poly(pts), bbox_of(pts, 6), FUR, ow=3, shadow=0)
        pts2 = [P(sx * 20, -74), P(sx * 42, -122), P(sx * 34, -70)]
        cv.shape(poly(pts2), bbox_of(pts2, 4), EARIN, ow=0, shadow=0)
    hx, hy = P(0, -58)
    disc(cv, hx, hy, 36 * s, FUR)
    nx, ny = P(0, -50)
    cv.shape(rbox(nx, ny, 12 * s, 8 * s, 5 * s), (nx - 14 * s, ny - 10 * s, nx + 14 * s, ny + 10 * s), NOSEC, ow=2.5, shadow=0)
    if glow_nose > 0:
        cv.glow(circle(nx, ny, 10 * s), (nx - 20 * s, ny - 20 * s, nx + 20 * s, ny + 20 * s), '#ff7a3a', 30 * s, glow_nose)
    for sx in (-1, 1):                                                         # eyes
        ex, ey = P(sx * 14, -66)
        cv.shape(circle(ex, ey, 6.5 * s), (ex - 8 * s, ey - 8 * s, ex + 8 * s, ey + 8 * s), ramp('#000000'), ow=0, shadow=0, flat=True)
        disc(cv, ex + 2 * s, ey - 2 * s * fy, 2 * s, ramp('#ffffff'), ow=0, shadow=0)
        if sad > 0:
            line(cv, [P(sx * 6, -78), P(sx * 22, -74 + 6 * sad)], 3 * s, flat(hexc('#140c10')))
    mx, my = P(0, -34)
    if mouth > 0:
        cv.shape(ellipse(mx, my, 11 * s, 8 * s * mouth + 2 * s), (mx - 13 * s, my - 12 * s, mx + 13 * s, my + 12 * s), ramp('#2a0a10'), ow=2, shadow=0)
        for sx in (-1, 1):                                                     # the two razor front teeth
            pts = [P(sx * 3, -40), P(sx * 9, -40), P(sx * 5, -27)]
            cv.shape(poly(pts), bbox_of(pts, 3), ramp('#ffffff'), ow=1.5, shadow=0)
    if lick > 0:
        L = (14 + 16 * abs(np.sin(T * 10))) * lick
        line(cv, [P(0, -30), P(0, -30 + L)], 8 * s, TONGUE, ow=2, flat=False)


BED_Y, BED_S = -470, 0.62
FEET_Y = BED_Y + 1000 * BED_S                     # where the blanket ends and his feet stick out
RFOOT = (45, FEET_Y + 40)


def feet(cv, T, col=None, twitch=0.0, cut=0.0, bleed=0.0):
    col = SKINN if col is None else col
    for sx in (-1, 1):
        fx = sx * 45
        tw = 5 * np.sin(T * 7) * twitch * (sx > 0)
        cv.shape(smooth(14, capsule(fx, FEET_Y - 30, fx, FEET_Y + 60, 36, 40), ellipse(fx, FEET_Y + 72, 42, 34)), (fx - 50, FEET_Y - 70, fx + 50, FEET_Y + 110), col)
        for i, dx in enumerate((-26, -12, 2, 15, 27)):                         # toes
            disc(cv, fx + sx * dx * -1 if sx < 0 else fx + dx, FEET_Y + 104 - abs(dx) * 0.25 + tw, 9 + (i == 0) * 3, col, shadow=0)
    if cut > 0:
        cv.shape(ellipse(RFOOT[0] + 4, RFOOT[1] + 6, 5 * cut, 3.5 * cut), (RFOOT[0] - 4, RFOOT[1] - 2, RFOOT[0] + 12, RFOOT[1] + 14), BLOOD, ow=1.5, shadow=0)
    if bleed > 0:
        cv.shape(smooth(4, circle(RFOOT[0] + 4, RFOOT[1] + 9, 7 * bleed), circle(RFOOT[0] + 8, RFOOT[1] + 22 * bleed, 4.5 * bleed)), (RFOOT[0] - 8, RFOOT[1] - 4, RFOOT[0] + 20, RFOOT[1] + 34), BLOOD, ow=1.5, shadow=0)


def bedroom(cv, T, twitch=0.0, cut=0.0, bleed=0.0, thermal=False):
    """Top-down: him asleep with his feet sticking out the end of the blanket, a nightstand with his phone (the one Easter egg)."""
    if thermal:
        cv.background('#000000', '#000000', vignette=0.0)
    else:
        cv.background('#2a2238', '#16121e', vignette=0.35)
        for k in range(-8, 9):                                                 # floorboards
            line(cv, [(k * 90, -960), (k * 90, 960)], 3, flat(hexc('#3a3048')), a=0.6)
        box(cv, 0, 420, 420, 300, ramp('#4a2a3a', '#2a1620', '#6a3a50'), r=30, shadow=0)   # rug
        box(cv, 380, -700, 95, 95, WOOD, r=10)                                  # nightstand + phone
        sub_phone(cv, 380, -700, 0.7, T)
    white = ramp('#ffffff')
    bed(cv, T, 0, BED_Y, BED_S, face='snore', blanket=True)
    feet(cv, T, col=white if thermal else None, twitch=twitch, cut=cut, bleed=bleed)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """lt < 0: the bat swoops in over the bed and lands on his foot at lt = -0.35. Frame one: wings still folding."""
    cv = Canvas(0, 0, 1.0)
    bedroom(cv, T, twitch=1.0)
    land = -0.35
    bx0, by0 = RFOOT[0] + 10, RFOOT[1] - 40
    if lt < land:
        u = ease(float(np.clip((lt + 2.9) / (2.9 + land), 0, 1)))
        bx, by = 460 - (460 - bx0) * u + 80 * np.sin(u * 5), -820 + (by0 + 820) * u
        bat(cv, bx, by, 1.15 - 0.25 * u, T, wings=1.0, flap=1.0)
    else:
        k = ease(float(np.clip((lt - land) / 0.7, 0, 1)))
        bat(cv, bx0, by0 - 4 * abs(np.sin(T * 5)), 0.9, T, wings=0.8 * (1 - k), flap=0.4 * (1 - k))
    if lt >= land:
        hook_text(cv, 'VAMPIRE BAT', lt - land, y=-830, size=130, color=(255, 80, 90))
    return cv


def b1_heat(lt, dur, T):
    """Heat vision: the sleeping man glows in hot colours, the veins in his feet brightest of all."""
    import cv2
    cv = Canvas(0, 0, 1.0)
    bedroom(cv, T, thermal=True)
    g = np.clip(cv.img.mean(axis=2) * (0.92 + 0.08 * np.sin(T * 6)), 0, 1)
    col = cv2.applyColorMap((g * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)[..., ::-1].astype(np.float32) / 255.0
    cv.img = np.ascontiguousarray(col)
    for sx in (-1, 1):                                                         # veins glowing in his feet
        for k in range(2):
            fx = sx * 45 + (k - 0.5) * 22
            pts = [(fx, FEET_Y - 10), (fx + 4, FEET_Y + 40), (fx, FEET_Y + 80)]
            cv.glow(polyline(pts, 3), bbox_of(pts, 10), '#ffe14d', 16, 0.8 + 0.2 * np.sin(T * 8 + k))
    k = ease(float(np.clip(lt / (dur * 0.8), 0, 1)))
    bat(cv, 420 - 260 * k, -760 + 640 * k, 0.9, T, wings=1.0, flap=1.0, glow_nose=1.0)
    hook_text(cv, 'HEAT VISION', lt, y=-830, size=130, pop_t=dur * 0.3, color=(255, 170, 60))
    return cv


def b2_teeth(lt, dur, T):
    """Close on the bat's face over the skin: it shaves the hair, then two razor teeth flash and nick a tiny hole."""
    cv = Canvas(RFOOT[0], RFOOT[1] + 40, 3.0)
    k_shave = float(np.clip(lt / (dur * 0.45), 0, 1))
    k_cut = ease(float(np.clip((lt - dur * 0.55) / 0.3, 0, 1)))
    bedroom(cv, T, cut=k_cut)
    for q in range(8):                                                         # little hairs flicking away
        u = float(np.clip(k_shave * 1.4 - q * 0.08, 0, 1))
        hx, hy = RFOOT[0] - 8 + q * 3, RFOOT[1] + q * 2
        line(cv, [(hx + 50 * u, hy - 40 * u), (hx + 50 * u + 3, hy - 40 * u - 8)], 1.5, flat(hexc('#4a3020')), a=1 - u * 0.8)
    dip = 18 * abs(np.sin(T * 8)) * (k_shave < 1)
    bx, by = RFOOT[0] + 4, RFOOT[1] - 30 + dip * 0.4 + 6 * k_cut
    bat(cv, bx, by, 0.55, T, mouth=0.4 + 0.6 * k_cut)
    if 0.2 < k_cut < 0.95:
        cv.glow(circle(bx, by - 19, 3), (bx - 6, by - 25, bx + 6, by - 13), '#ffffff', 8, 1.2)
    hook_text(cv, 'RAZOR TEETH', lt, y=-800, size=130, pop_t=dur * 0.55, color=(255, 255, 255))
    return cv


def b3_draculin(lt, dur, T):
    """Inside the cut: clot strands try to form, the bat's spit (draculin) melts them, the blood keeps coming."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a0a14', '#1a0408', vignette=0.4)
    vessel(cv, -60, x0=-800, x1=800, r=200)
    for q in range(10):                                                        # red cells streaming toward the cut
        x = -700 + ((T * 300 + q * 150) % 1400)
        cv.shape(rotell(x, -60 + 80 * np.sin(q * 2.3), 48, 28, 20 * np.sin(q)), (x - 60, -160, x + 60, 40), BLOOD, ow=3)
    k = float(np.clip(lt / (dur * 0.9), 0, 1))
    clot = min(1.0, k / 0.35) if k < 0.35 else max(0.0, 1 - (k - 0.35) / 0.25)
    for q in range(6):                                                         # yellow clot strands trying to knit
        a = q * 0.6
        line(cv, [(220 + np.cos(a) * 30, -160 + np.sin(a) * 40), (360 + np.cos(a + 1) * 60, 40 + np.sin(a + 2) * 50)], 6, CLOT, a=clot)
    for q in range(8):                                                         # draculin drops raining in
        ph = (lt * 0.9 + q / 8) % 1
        if k > 0.25:
            disc(cv, 220 + (q * 37) % 180, -500 + 420 * ph, 16, DRAC, ow=2.5, shadow=0, alpha=min(1, (k - 0.25) * 4) * (1 - ph * 0.5))
    badge(cv, 'DRACULIN', y=-680, col=(90, 220, 200), w=420)
    if k > 0.6:
        hook_text(cv, 'NO CLOTS', lt, y=-830, size=110, pop_t=dur * 0.6, color=(90, 220, 200))
    return cv


def b4_lap(lt, dur, T):
    """It laps, it doesn't suck: tongue flicking at the drop, a timer running to 20 minutes."""
    cv = Canvas(RFOOT[0], RFOOT[1] + 40, 3.0)
    bedroom(cv, T, cut=1.0, bleed=0.7 + 0.1 * np.sin(T * 4))
    bat(cv, RFOOT[0] + 4, RFOOT[1] - 24, 0.55, T, mouth=0.6, lick=1.0)
    k = float(np.clip(lt / (dur * 0.85), 0, 1))
    cx, cy = RFOOT[0] + 100, RFOOT[1] - 170
    disc(cv, cx, cy, 52, ramp('#ffffff', '#d8dde4', '#ffffff'))
    if k > 0.02:
        cv.shape(poly([(cx, cy)] + [(cx + np.sin(a) * 46, cy - np.cos(a) * 46) for a in np.linspace(0, 2 * np.pi * k, 30)]), (cx - 52, cy - 52, cx + 52, cy + 52),
                 ramp('#e2302a'), ow=0, shadow=0, alpha=0.85)
    label(cv, f'{int(20 * k)} MIN', cx, cy + 80, 30, (255, 255, 255))
    hook_text(cv, 'LAP LAP LAP', lt, y=-800, size=130, pop_t=dur * 0.25, color=(255, 120, 140))
    return cv


def b5_full(lt, dur, T):
    """The bat swells up round and red on a little scale: +60%."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#141a30', '#0a0e1c', vignette=0.35)
    k = ease(float(np.clip(lt / (dur * 0.7), 0, 1)))
    box(cv, 0, 180, 200, 30, STEEL, r=10)                                     # the scale
    box(cv, 0, 260, 160, 60, ramp('#e8e8f0', '#b0b0c0', '#ffffff'), r=14)
    pct = int(round(60 * k))
    label(cv, f'+{pct}%', 0, 272, 60, (200, 30, 40), stroke=0)
    wob = 6 * np.sin(T * 6) * k
    bat(cv, wob, 40 - 40 * k, 1.9 + 0.2 * k, T, full=k, wings=0.0)
    if k > 0.95:
        hook_text(cv, 'HALF ITS WEIGHT', lt, y=-800, size=110, pop_t=dur * 0.72, color=(255, 80, 90))
    return cv


def cave(cv, T):
    cv.background(*CAVE, vignette=0.4)
    for i, x in enumerate(range(-600, 640, 120)):                              # stalactites
        h = 120 + 60 * ((i * 7) % 3)
        cv.shape(poly([(x - 50, -960), (x + 50, -960), (x + 6, -960 + h + 80)]), (x - 52, -962, x + 52, -960 + h + 82), ROCK, ow=3, shadow=0)
    box(cv, 0, -820, 700, 120, ROCK, r=0, ow=0, shadow=0)
    box(cv, 0, 760, 700, 260, ROCK, r=0, ow=0, shadow=0)


def b6_starve(lt, dur, T):
    """One bat hanging alone, getting thinner, as two moons cross the cave mouth: 2 nights."""
    cv = Canvas(0, 0, 1.0)
    cave(cv, T)
    k = float(np.clip(lt / (dur * 0.8), 0, 1))
    for i in range(2):                                                         # two nights go by
        u = float(np.clip(k * 2 - i, 0, 1))
        if 0 < u < 1:
            moon(cv, -400 + 800 * u, -560 - 120 * np.sin(np.pi * u), 50)
    line(cv, [(0, -700), (0, -470)], 6, flat(hexc('#6a6070')))
    bat(cv, 0, -250 + 8 * np.sin(T * 2), 2.3, T, flip=True, thin=k, sad=k)
    badge(cv, f'NIGHT {1 + int(k > 0.5)}', y=200, col=(200, 200, 255), w=300)
    if k > 0.85:
        hook_text(cv, '2 NIGHTS', lt, y=-800, size=160, pop_t=dur * 0.7, color=(255, 80, 90))
    return cv


def share(cv, lt, dur, T, giver_x, taker_x, label_txt):
    cave(cv, T)
    for x in (giver_x, taker_x):
        line(cv, [(x, -700), (x, -500)], 6, flat(hexc('#6a6070')))
    k = float(np.clip((lt - 0.4) / (dur * 0.6), 0, 1))
    bat(cv, giver_x, -300, 1.9, T, flip=True, full=1 - 0.5 * k, mouth=0.5)
    bat(cv, taker_x, -300, 1.9, T, flip=True, thin=1 - k, full=0.5 * k, mouth=0.5, sad=1 - k)
    for q in range(3):                                                         # blood passed across, drop by drop
        ph = ((lt * 1.2 + q / 3) % 1)
        if 0 < k < 1:
            x = giver_x + (taker_x - giver_x) * ph
            y = -200 - 90 * np.sin(np.pi * ph)
            disc(cv, x, y, 12, BLOOD, ow=2, shadow=0)
    if k > 0.6:
        for q in range(3):                                                     # little hearts
            ph = (T * 0.8 + q / 3) % 1
            hx = (giver_x + taker_x) / 2 + 40 * np.sin(q * 2)
            cv.shape(heart(hx, -480 - 160 * ph, 40), (hx - 30, -520 - 160 * ph, hx + 30, -440 - 160 * ph), ramp('#ff6a8a'), ow=2, shadow=0, alpha=1 - ph)
    label(cv, label_txt, 0, 180, 80, (255, 200, 210))


def b7_share(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    share(cv, lt, dur, T, -200, 200, 'SHARING')
    return cv


def b8_payback(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    share(cv, lt, dur, T, 200, -200, 'PAYBACK')
    return cv


BEATS = [b0_hook, b1_heat, b2_teeth, b3_draculin, b4_lap, b5_full, b6_starve, b7_share, b8_payback]

if __name__ == '__main__':
    run(BEATS)
