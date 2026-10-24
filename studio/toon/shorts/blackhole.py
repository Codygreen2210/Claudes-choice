#!/usr/bin/env python3
"""What happens if you fall into a black hole. Opens with an astronaut already drifting toward a glowing black hole,
tether snapped and flailing; loops back into it (the last line plays over the tether snapping off his ship)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

SUIT = ramp('#f4f6f8', '#b8c0cc', '#ffffff')
VISOR = ramp('#7ab8e8', '#3a6a9a', '#c8e8ff')
DISK1 = ramp('#ffb03a', '#e2601a', '#fff0a0')
SHIP = ramp('#c8ccd4', '#8a909a', '#eef0f4')
BH = (0, 250)                                    # the black hole's centre in the main shots


def stars(cv, T, n=70, pull=0.0, cx=0.0, cy=0.0):
    rng = np.random.default_rng(1)
    for q in range(n):
        x, y = rng.uniform(-560, 560), rng.uniform(-980, 980)
        if pull > 0:                                                           # streaks toward the hole
            dx, dy = cx - x, cy - y
            d = np.hypot(dx, dy) + 1e-6
            ph = (T * 0.4 + q / n) % 1
            x, y = x + dx * ph * pull, y + dy * ph * pull
            line(cv, [(x, y), (x + dx / d * 30 * pull, y + dy / d * 30 * pull)], 3, flat(hexc('#ffffff')), a=0.7 * (1 - ph))
        else:
            disc(cv, x, y, 2 + (q % 3), ramp('#ffffff'), ow=0, shadow=0, alpha=0.5 + 0.5 * np.sin(T * 3 + q))


def black_hole(cv, x, y, r, T):
    """A black hole: glowing tilted disk wrapping round it, a thin bright ring, a pure black middle."""
    cv.glow(circle(x, y, r * 1.1), (x - r * 2.5, y - r * 1.5, x + r * 2.5, y + r * 1.5), '#ff8a2a', r * 0.6, 0.6)
    spin = T * 0.6
    for k, (rx, ry, col, a) in enumerate(((r * 2.3, r * 0.5, DISK1, 0.95), (r * 1.9, r * 0.38, ramp('#fff0a0', '#ffd23f', '#ffffff'), 0.8))):
        cv.shape(subtract(ellipse(x, y, rx, ry), ellipse(x, y, rx * 0.62, ry * 0.62)), (x - rx - 4, y - ry - 4, x + rx + 4, y + ry + 4), col, ow=0, shadow=0, alpha=a)
    for q in range(10):                                                        # bright clumps orbiting in the disk
        a = spin + q * 0.63
        disc(cv, x + np.cos(a) * r * 1.6, y + np.sin(a) * r * 0.36, r * 0.06, ramp('#ffffff'), ow=0, shadow=0, alpha=0.7)
    cv.shape(subtract(circle(x, y - r * 0.05, r * 1.18), circle(x, y - r * 0.05, r * 1.05)), (x - r * 1.2, y - r * 1.25, x + r * 1.2, y + r * 1.15), ramp('#ffe8a0'), ow=0, shadow=0, flat=True, alpha=0.9)
    disc(cv, x, y, r, ramp('#000000', '#000000', '#0a0a0a'), ow=0, shadow=0)
    cv.shape(inter(subtract(ellipse(x, y, r * 2.3, r * 0.5), ellipse(x, y, r * 1.43, r * 0.31)), lambda X, Y: (y - Y) * -1), (x - r * 2.4, y - 4, x + r * 2.4, y + r * 0.55), DISK1, ow=0, shadow=0, alpha=0.95)   # front half of the disk in front


def astronaut(cv, x, y, s, T, face='scream', flail=1.0, alpha_tint=None):
    """Him in a white suit with a round glass helmet."""
    f = 25 * np.sin(T * 7) * flail
    guy(cv, x, y, s, face=face, arms=((110 + f, 40), (110 - f, 40)), shirt=SUIT, pants=SUIT, tint=alpha_tint)
    hx, hy = x, y - 762 * s
    box(cv, x - 150 * s, y - 470 * s, 40 * s, 90 * s, SUIT, r=16 * s)         # backpack edge
    cv.shape(subtract(circle(hx, hy, 140 * s), circle(hx, hy, 122 * s)), (hx - 142 * s, hy - 142 * s, hx + 142 * s, hy + 142 * s), SUIT, ow=3)
    cv.shape(circle(hx, hy, 122 * s), (hx - 124 * s, hy - 124 * s, hx + 124 * s, hy + 124 * s), VISOR, ow=0, shadow=0, alpha=0.25)
    cv.shape(ellipse(hx - 50 * s, hy - 60 * s, 30 * s, 18 * s), (hx - 82 * s, hy - 80 * s, hx - 18 * s, hy - 40 * s), ramp('#ffffff'), ow=0, shadow=0, alpha=0.6)


def ship(cv, x, y, s, T):
    """His spaceship (with one little thumbs-up decal on the hull: the Easter egg)."""
    cv.shape(smooth(30 * s, rbox(x, y, 220 * s, 70 * s, 50 * s), ellipse(x + 200 * s, y, 90 * s, 60 * s)), (x - 240 * s, y - 80 * s, x + 300 * s, y + 80 * s), SHIP)
    for k in range(3):
        disc(cv, x - 80 * s + k * 90 * s, y - 10 * s, 22 * s, VISOR, ow=3, shadow=0)
    thumb_icon(cv, x + 150 * s, y + 20 * s, 18 * s)
    cv.glow(circle(x - 240 * s, y, 30 * s), (x - 300 * s, y - 50 * s, x - 180 * s, y + 50 * s), '#5ac8ff', 30, 0.7 + 0.3 * np.sin(T * 20))


def stretched(cv, draw, cx, cy, sx, sy):
    """Draw something on a magenta key layer, then stretch it (sx wide, sy tall) about (cx, cy) onto the canvas."""
    import cv2
    layer = Canvas(cv.cx, cv.cy, cv.zoom)
    layer.background('#ff00ff', '#ff00ff', vignette=0.0)
    draw(layer)
    img = layer.img
    key = np.array([1.0, 0.0, 1.0], np.float32)
    mask = (np.abs(img - key).sum(axis=2) > 0.6).astype(np.uint8)
    mask = cv2.GaussianBlur(cv2.erode(mask, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.0)
    H_, W_ = img.shape[:2]
    px, py = cv.to_px(cx, cy)
    M = np.float32([[sx, 0, px * (1 - sx)], [0, sy, py * (1 - sy)]])
    img2 = cv2.warpAffine(img, M, (W_, H_), flags=cv2.INTER_LINEAR, borderValue=(1, 0, 1))
    m2 = cv2.warpAffine(mask, M, (W_, H_), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
    cv.img = np.ascontiguousarray(cv.img * (1 - m2) + img2 * m2)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """lt < 0: floating on a tether by his ship. The tether snaps at lt = -0.6; frame one he's drifting down, flailing."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T)
    black_hole(cv, BH[0], BH[1], 200, T)
    ship(cv, 260, -720, 0.8, T)
    snapped = lt > -0.6
    if not snapped:
        ax, ay = 40 + 30 * np.sin(lt * 1.5), -280
        line(cv, [(80, -720), (ax + 60, ay - 300)], 4, flat(hexc('#e0e4ea')))
        astronaut(cv, ax, ay, 0.55, T, face='happy', flail=0.2)
    else:
        u = lt + 0.6
        ax, ay = 40 - 40 * (1 - np.exp(-u)), -280 + 50 * u + 6 * u * u
        line(cv, [(80, -720), (110 - 40 * u, -640 + 30 * u)], 4, flat(hexc('#e0e4ea')))   # the snapped tether, floating off
        astronaut(cv, ax, ay, 0.55, T, face='scream')
        hook_text(cv, 'BLACK HOLE', lt + 0.6, y=-830, size=140, color=(255, 176, 58))
    return cv


def b1_light(lt, dur, T):
    """Beams of light fired past the hole bend in and vanish."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T)
    black_hole(cv, 0, 0, 170, T)
    k = float(np.clip(lt / (dur * 0.8), 0, 1))
    for q in range(5):                                                         # light rays curving in
        y0 = -420 + q * 120
        pts = []
        for u in np.linspace(0, min(1, k * 1.4 - q * 0.08), 30):
            x = -560 + 700 * u
            pull = np.exp(-((x) ** 2) / 90000) * (300 - abs(y0)) * 0.9 * u
            pts.append((x, y0 + (0 - y0) * min(1, u ** 2 * 1.1) * (1 - abs(y0) / 900)))
        if len(pts) > 1:
            line(cv, pts, 8, flat(hexc('#fff6a0')), a=0.9)
    hook_text(cv, 'NOT EVEN LIGHT', lt, y=-800, size=110, pop_t=dur * 0.5, color=(255, 246, 160))
    return cv


def b2_tidal(lt, dur, T):
    """Near a small black hole: a big arrow pulls his feet, a little one pulls his head."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T)
    black_hole(cv, 0, 560, 90, T)
    astronaut(cv, 0, 260, 0.6, T, face='worried', flail=0.5)
    k = ease(float(np.clip(lt / (dur * 0.5), 0, 1)))
    arrows(cv, [((0, 280), (0, 280 + 160 * k))], (255, 90, 80), 26)
    arrows(cv, [((0, -240), (0, -240 + 50 * k))], (255, 200, 120), 12)
    label(cv, 'FEET', 170, 330, 56, (255, 90, 80))
    label(cv, 'HEAD', 170, -230, 44, (255, 200, 120))
    box(cv, 0, -760, 300, 58, DARK, r=26)
    label(cv, 'SMALL BLACK HOLE', 0, -752, 60, (255, 176, 58))
    return cv


def b3_noodle(lt, dur, T):
    """Spaghettification: he gets pulled long and thin."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T, pull=0.4, cx=0, cy=700)
    black_hole(cv, 0, 700, 90, T)
    k = ease(float(np.clip(lt / (dur * 0.6), 0, 1)))
    stretched(cv, lambda L: astronaut(L, 0, 240, 0.55, T, face='scream'), 0, 0, 1 - 0.65 * k, 1 + 1.1 * k)
    if lt > dur * 0.55:
        box(cv, 0, -800, 420, 62, DARK, r=26)
        label(cv, 'SPAGHETTIFICATION', 0, -792, 66, (255, 236, 80))
    return cv


def b4_giant(lt, dur, T):
    """A giant black hole fills the bottom of the screen; he floats across the dashed edge in one piece."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T)
    black_hole(cv, 0, 760, 420, T)
    k = float(np.clip(lt / (dur * 0.85), 0, 1))
    for q in range(28):                                                        # the edge, dashed
        a = np.pi + q * np.pi / 27
        if q % 2 == 0:
            line(cv, [(np.cos(a) * 520, 760 + np.sin(a) * 520), (np.cos(a + 0.05) * 520, 760 + np.sin(a + 0.05) * 520)], 8, flat(hexc('#ffffff')), a=0.8)
    label(cv, 'THE EDGE', 330, 180, 46, (255, 255, 255))
    astronaut(cv, 0, -40 + 320 * k, 0.4, T, face='shock', flail=0.4)
    hook_text(cv, 'IN ONE PIECE', lt, y=-800, size=120, pop_t=dur * 0.55, color=(127, 255, 160))
    return cv


def b5_inside(lt, dur, T):
    """Inside: deep red dark, a countdown from 13, and the stretching starting right at the end."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a0610', '#06000a', vignette=0.5)
    k = float(np.clip(lt / (dur * 0.92), 0, 1))
    secs = max(0, 13 - int(13 * k))
    stretch = max(0.0, (k - 0.8) / 0.2)
    stretched(cv, lambda L: astronaut(L, 0, 320, 0.55, T, face='shock'), 0, 0, 1 - 0.4 * stretch, 1 + 0.6 * stretch)
    box(cv, 0, -560, 150, 120, DARK, r=30)
    label(cv, str(secs), 0, -520, 160, (255, 90, 80))
    label(cv, 'SECONDS LEFT', 0, -390, 44, (255, 200, 200))
    return cv


def b6_friends(lt, dur, T):
    """His friends at the ship window, watching: far away, he's stuck at the edge."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T)
    black_hole(cv, 0, 300, 220, T)
    astronaut(cv, 0, -10, 0.22, T, face='shock', flail=0.05)                   # tiny, stuck at the rim
    box(cv, 0, -600, 330, 200, SHIP, r=40)                                     # the window
    box(cv, 0, -600, 300, 170, ramp('#1a2a4a', '#0e1830', '#2a3a6a'), r=30, ow=0, shadow=0)
    for i, x in enumerate((-110, 110)):
        guy(cv, x, -250, 0.5, face='shock' if i == 0 else 'worried', look=(0, 1), shirt=ramp('#3d7fd8') if i == 0 else ramp('#e2483d'))
    box(cv, 0, -340, 330, 90, SHIP, r=20)                                      # hull under the window hides their legs
    if lt > dur * 0.45:
        hook_text(cv, 'NEVER FALLS IN', lt, y=-840, size=110, pop_t=dur * 0.45, color=(255, 236, 80))
    return cv


def b7_frozen(lt, dur, T):
    """Close on him at the edge: slowing, reddening, frozen, a stopped clock beside him."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T * 0.1)
    black_hole(cv, 0, 760, 420, T * 0.05)
    k = float(np.clip(lt / (dur * 0.7), 0, 1))
    # his own motion slows to a stop: fade the flail's size, never warp its clock (warping T spun the arms)
    astronaut(cv, 0, 120 + 40 * (1 - np.exp(-lt * 2)), 0.45, T, face='shock', flail=1 - k, alpha_tint=('#ff3a2a', 0.5 * k))
    wall_clock(cv, 330, -420, 100, 1.2 + 0.4 * (1 - k) * lt, 3.0 + 4 * (1 - k) * lt)
    if k > 0.6:
        hook_text(cv, 'FOREVER', lt, y=-800, size=170, pop_t=dur * 0.55, color=(255, 120, 100))
    return cv


def b8_younger(lt, dur, T):
    """Two clocks: his and his friends'. His runs slow: 36 minutes younger."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#06060e', '#0a0a1a', vignette=0.3)
    stars(cv, T)
    k = ease(float(np.clip(lt / (dur * 0.7), 0, 1)))
    for i, (x, name, rate) in enumerate(((-250, 'YOU', 1.0), (250, 'FRIENDS', 1.1))):
        mins = 360 * rate * k
        wall_clock(cv, x, -330, 160, np.radians(mins * 0.5), np.radians(mins * 6))
        label(cv, name, x, -110, 60, (255, 255, 255))
    if k > 0.95:
        badge(cv, '36 MIN YOUNGER', y=120, col=(127, 255, 160), w=620)
    box(cv, 0, -770, 260, 54, DARK, r=24)
    label(cv, '6-HOUR TRIP', 0, -762, 56, (255, 176, 58))
    return cv


BEATS = [b0_hook, b1_light, b2_tidal, b3_noodle, b4_giant, b5_inside, b6_friends, b7_frozen, b8_younger]

if __name__ == '__main__':
    run(BEATS)
