#!/usr/bin/env python3
"""What happens if an elevator cable snaps (Short #6), animated in code.

    python3 studio/animate/scenes/elevator.py out.mp4 [--cues cues.json] [--only 0,9]

Everything is drawn as clay: each shape is a mask that gets puffed into a soft
lit lump (light from top-left, like the stills), with a thumbprint texture and a
contact shadow. Bricks, steel and people come from textures cut out of our stills.
Beat times live in CUES; swap in the real voice timings once the voice is recorded.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..'))
from animate import FPS, H, STEP, W, ease  # noqa: E402

TEX = os.path.join(HERE, '..', 'textures')
FONT = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
LIGHT = np.array([-0.55, -0.65, 0.52]); LIGHT /= np.linalg.norm(LIGHT)

# beat start times (seconds); the voice will move these
CUES = dict(snap=0.0, rewind=3.0, cables=6.0, cutall=10.0, black=14.0, bomber=17.0, lobby=21.0,
            frayed=26.0, fall=29.0, pit=33.0, crash=38.0, medal=44.0, doors=48.0, end=52.0)
FLOOR = 430                    # world px per floor


# ------------------------------------------------------------------ clay painter
_thumb = None


def thumb():
    global _thumb
    if _thumb is None:
        r = np.random.default_rng(2)
        n = cv2.GaussianBlur(r.normal(0, 1, (H + 64, W + 64)).astype(np.float32), (0, 0), 3)
        n2 = cv2.GaussianBlur(r.normal(0, 1, (H + 64, W + 64)).astype(np.float32), (0, 0), 12)
        _thumb = (n / n.std() * 0.035 + n2 / n2.std() * 0.05)
    return _thumb


def clay(canvas, mask, color, puff=10, spec=0.18, shadow=(14, 18, 0.35), tex=None, alpha=1.0):
    """Paint `mask` (float HxW, 0..1) onto canvas as a lit clay lump of `color` (BGR) or texture."""
    ys, xs = np.where(mask > 0.02)
    if len(ys) == 0:
        return canvas
    pad = puff * 3 + 30
    y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + pad)
    m = mask[y0:y1, x0:x1].astype(np.float32)
    sub = canvas[y0:y1, x0:x1]
    if shadow:
        dx, dy, st = shadow
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        sh = cv2.GaussianBlur(cv2.warpAffine(m, M, (m.shape[1], m.shape[0])), (0, 0), max(2, puff * 0.8))
        sub *= (1 - st * sh * alpha)[..., None]
    hgt = cv2.GaussianBlur(m, (0, 0), puff)
    gy, gx = np.gradient(hgt * puff * 2.2)
    nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
    nx, ny = -gx * nz, -gy * nz
    dif = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    hv = np.array([LIGHT[0], LIGHT[1], LIGHT[2] + 1]); hv /= np.linalg.norm(hv)
    sp = np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1) ** 30
    base = tex[y0:y1, x0:x1] if tex is not None else np.broadcast_to(np.array(color, np.float32), m.shape + (3,))
    th = thumb()[y0:y1, x0:x1]
    col = base * (0.45 + 0.7 * dif)[..., None] * (1 + th)[..., None] + spec * 255 * sp[..., None]
    a = (np.clip(m, 0, 1) * alpha)[..., None]
    canvas[y0:y1, x0:x1] = sub * (1 - a) + col * a
    return canvas


def rect_mask(x0, y0, x1, y1, r=6):
    m = np.zeros((H, W), np.float32)
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    if x1 <= x0 or y1 <= y0:
        return m
    cv2.rectangle(m, (x0 + r, y0), (x1 - r, y1), 1.0, -1)
    cv2.rectangle(m, (x0, y0 + r), (x1, y1 - r), 1.0, -1)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        cv2.circle(m, (cx, cy), r, 1.0, -1, cv2.LINE_AA)
    return m


def line_mask(pts, w):
    m = np.zeros((H, W), np.float32)
    cv2.polylines(m, [np.asarray(pts, np.int32)], False, 1.0, int(max(1, w)), cv2.LINE_AA)
    return m


def tiled(t, h, w, scale=1.0, oy=0.0, ox=0.0):
    th, tw = t.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(t, ((xx / scale + ox) % tw).astype(np.float32), ((yy / scale + oy) % th).astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def text(canvas, s, cx, cy, size, fill=(255, 255, 255), stroke=(20, 20, 20), sw=10, alpha=1.0, rot=0):
    f = ImageFont.truetype(FONT, int(size))
    tmp = Image.new('RGBA', (W, int(size * 1.8)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), s, font=f, stroke_width=sw)
    tw = bb[2] - bb[0]
    d.text(((W - tw) / 2 - bb[0], int(size * 0.2)), s, font=f, fill=fill[::-1] + (255,), stroke_width=sw, stroke_fill=stroke[::-1] + (255,))
    if rot:
        tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=False)
    arr = np.array(tmp).astype(np.float32)
    rgb, a = arr[..., :3][..., ::-1], arr[..., 3:] / 255 * alpha
    y0 = int(cy - arr.shape[0] / 2); x0 = int(cx - W / 2)
    ys, ye = max(0, y0), min(H, y0 + arr.shape[0]); xs, xe = max(0, x0), min(W, x0 + W)
    if ye <= ys or xe <= xs:
        return canvas
    sub = canvas[ys:ye, xs:xe]
    canvas[ys:ye, xs:xe] = sub * (1 - a[ys - y0:ye - y0, xs - x0:xe - x0]) + rgb[ys - y0:ye - y0, xs - x0:xe - x0] * a[ys - y0:ye - y0, xs - x0:xe - x0]
    return canvas


def pop(t, t0, dur=0.25):
    """0 -> overshoot -> 1 scale for things that pop in."""
    k = np.clip((t - t0) / dur, 0, 1)
    return 0 if k <= 0 else 1 + 0.25 * np.sin(k * np.pi) * (1 - k) * 3 if k < 1 else 1


# ------------------------------------------------------------------ assets
class Assets:
    def __init__(self):
        r = lambda n: cv2.imread(os.path.join(TEX, n), cv2.IMREAD_UNCHANGED)
        brick = r('cobble.png').astype(np.float32)
        wl = cv2.GaussianBlur(tiled(brick, 1400, W, 0.8), (0, 0), 2.5)
        g = wl.mean(2, keepdims=True)
        self.wall = (wl * 0.25 + g * 0.75) * np.array([0.62, 0.64, 0.68])
        steel = r('tankside.png').astype(np.float32)
        g = steel.mean(2, keepdims=True)
        self.steel = (steel * 0.25 + g * 0.75) * np.array([1.0, 1.0, 1.05])          # grey riveted steel
        self.rust = steel
        self.people = [r('person_0.png'), r('person_1.png')]
        self.slate = r('slate.png').astype(np.float32)


# ------------------------------------------------------------------ shaft scene (side cutaway)
def shaft(cv_, A, car_y, cam_y, cables='intact', glow=None, brakes=0.0, sparks=0.0, speed=0.0, hair=0.0,
          frayed=0.0, whip=None, coil=0.0, air=0.0, pit=False, dust=0.0, counter=None, rng=None, t=0.0):
    """car_y: world y of car top (down is +). cam_y: world y at screen centre."""
    oy = cam_y - H / 2
    # back wall: shaft bricks, scrolled with the camera, darker at the edges
    wall = A.wall[(np.arange(H) + int(oy * 0.9)) % A.wall.shape[0]]
    cv_[:] = wall
    vig = np.linspace(0.65, 1, 200)
    cv_[:, :200] *= vig[None, :, None]; cv_[:, -200:] *= vig[::-1][None, :, None]
    # speed streaks on the wall when falling fast
    if speed > 0.05:
        for k in range(int(30 * speed)):
            x = rng.uniform(80, W - 80); y = rng.uniform(0, H); ln = 200 + 900 * speed
            cv2.line(cv_, (int(x), int(y)), (int(x), int(y - ln)), (200, 205, 210), 2, cv2.LINE_AA)
    # floors: concrete slabs with door gaps and painted numbers
    f0 = int(oy // FLOOR) - 1
    for f in range(f0, f0 + H // FLOOR + 3):
        y = f * FLOOR - oy
        slab = rect_mask(0, y, 150, y + 46, 4) + rect_mask(W - 150, y, W, y + 46, 4)
        clay(cv_, np.clip(slab, 0, 1), (120, 125, 130), puff=6, spec=0.08, shadow=(6, 10, 0.4))
        num = 76 - f
        if 0 < num < 100:
            text(cv_, str(num), 75, y + 120, 54, fill=(230, 230, 225), stroke=(40, 40, 40), sw=4, alpha=0.85)
    # guide rails
    for x in (200, W - 220):
        clay(cv_, rect_mask(x, 0, x + 22, H, 3), (95, 100, 108), puff=4, spec=0.35, shadow=(5, 0, 0.35))
    # pit at the bottom
    pit_y = 76 * FLOOR - oy + 40
    if pit and pit_y < H + 400:
        cv2.rectangle(cv_, (0, int(pit_y)), (W, H), (40, 44, 50), -1)
        clay(cv_, rect_mask(150, pit_y + 300, W - 150, pit_y + 360, 6), (110, 105, 100), puff=8, spec=0.05)
        # buffer springs
        for x in (360, W - 420):
            pts = [(x + 30 + 26 * np.sin(k * 0.9), pit_y + 300 - k * 7) for k in range(30)]
            clay(cv_, line_mask(pts, 10), (60, 140, 200), puff=4, spec=0.4, shadow=(4, 6, 0.3))
    cy = car_y - oy                        # car top on screen
    cx0, cx1 = 240, W - 260
    ch = 560
    # cables above the car
    cab_x = np.linspace(cx0 + 200, cx1 - 200, 6)
    if cables == 'intact' or cables == 'glow':
        for i, x in enumerate(cab_x):
            g = 0 if glow is None else glow[i]
            col = (60, 62, 66) if g <= 0 else (int(60 + 120 * g), int(62 + 190 * g), int(66 + 189 * g))
            clay(cv_, rect_mask(x - 7, -50, x + 7, cy + 4, 3), col, puff=3, spec=0.5, shadow=(5, 0, 0.3))
            if g > 0:
                gl = cv2.GaussianBlur(rect_mask(x - 7, -50, x + 7, cy, 3), (0, 0), 18) * g
                cv_ += (np.array([120, 230, 255], np.float32) * 0.9 * gl[..., None])
    elif cables in ('snapped', 'cut'):
        if whip is not None and whip < 0.6:
            for i, x in enumerate(cab_x):
                top_end = (cy - 200) - 2600 * whip - i * 40
                pts = [(x + 30 * np.sin(j * 0.6 + whip * 30 + i), top_end - j * 60) for j in range(20)]
                clay(cv_, line_mask(pts, 12), (60, 62, 66), puff=3, spec=0.5, shadow=(5, 0, 0.3))
        for i, x in enumerate(cab_x):
            stub = 60 + 40 * np.sin(i * 1.7)
            clay(cv_, rect_mask(x - 7, cy - stub, x + 7, cy + 4, 3), (60, 62, 66), puff=3, spec=0.5, shadow=(5, 0, 0.3))
            # frayed end: splayed strands
            for s in range(5):
                a = (s - 2) * 0.35 + 0.15 * np.sin(t * 9 + s + i)
                p0 = (x, cy - stub); p1 = (x + np.sin(a) * 26, cy - stub - np.cos(a) * 26)
                cv2.line(cv_, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (110, 112, 118), 3, cv2.LINE_AA)
    # car: steel box, front cut away to show inside
    car = rect_mask(cx0, cy, cx1, cy + ch, 14)
    clay(cv_, car, None, puff=12, spec=0.25, shadow=(18, 22, 0.45),
         tex=tiled(A.steel, H, W, 0.9, oy=-cy))
    inner = rect_mask(cx0 + 46, cy + 70, cx1 - 46, cy + ch - 46, 10)
    clay(cv_, inner, (95, 135, 175), puff=6, spec=0.05, shadow=None)
    cv_ += cv2.GaussianBlur(inner, (0, 0), 60)[..., None] * np.array([30, 60, 90])
    clay(cv_, rect_mask(cx0 + 46, cy + ch - 90, cx1 - 46, cy + ch - 46, 4), (60, 88, 120), puff=5, spec=0.05, shadow=None)
    # passenger (clay cutout), hair lifts when falling
    p = A.people[1]
    ph = 330
    pw = int(p.shape[1] * ph / p.shape[0])
    lift = int(-50 * hair)
    pr = cv2.resize(p, (pw, ph))
    px, py = int((cx0 + cx1) / 2 - pw / 2), int(cy + ch - 90 - ph + lift)
    a = pr[..., 3:].astype(np.float32) / 255
    y0, y1, x0, x1 = max(0, py), min(H, py + ph), max(0, px), min(W, px + pw)
    if y1 > y0 and x1 > x0:
        cv_[y0:y1, x0:x1] = cv_[y0:y1, x0:x1] * (1 - a[y0 - py:y1 - py, x0 - px:x1 - px]) + pr[y0 - py:y1 - py, x0 - px:x1 - px, :3] * a[y0 - py:y1 - py, x0 - px:x1 - px]
    # safety brakes: wedges that swing out of the car sides and bite the rails
    if brakes > 0:
        for side in (-1, 1):
            bx = (cx0 - 10) if side < 0 else (cx1 + 10)
            reach = 40 * brakes
            pts = np.array([(bx, cy + 60), (bx + side * reach, cy + 40), (bx + side * reach, cy + 140), (bx, cy + 150)], np.int32)
            m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [pts], 1.0)
            clay(cv_, m, (40, 160, 230), puff=5, spec=0.4, shadow=(6, 8, 0.4))
    if sparks > 0:
        for k in range(int(90 * sparks)):
            side = rng.choice([200 + 11, W - 220 + 11])
            sy = cy + 100
            ang = rng.uniform(-np.pi, 0) if side < W / 2 else rng.uniform(-np.pi, 0)
            ln = rng.uniform(20, 120) * sparks
            sx2, sy2 = side + np.cos(ang) * ln * (1 if side > W / 2 else -1), sy + np.sin(ang) * ln - rng.uniform(-60, 90)
            cv2.line(cv_, (int(side), int(sy)), (int(sx2), int(sy2)), (120, 220, 255), 2, cv2.LINE_AA)
        fl = cv2.GaussianBlur(rect_mask(150, cy + 40, W - 150, cy + 170, 10), (0, 0), 40) * sparks
        cv_ += np.array([90, 170, 255], np.float32) * fl[..., None] * 0.6
    # coiled loose cable under the car (Betty's fall)
    if coil > 0:
        base_y = pit_y + 300
        top = cy + ch
        n = int(14 * coil) + 2
        for i in range(n):
            yv = base_y - (base_y - top) * i / n
            m = np.zeros((H, W), np.float32)
            cv2.ellipse(m, (W // 2, int(yv)), (220, 26), 0, 0, 360, 1.0, 9, cv2.LINE_AA)
            clay(cv_, m, (60, 62, 66), puff=3, spec=0.5, shadow=(4, 6, 0.3))
    if air > 0:
        for k in range(6):
            ax = 300 + k * 100
            ayb = cy + ch + 60
            off = ((t * 220 + k * 40) % 160)
            for side in (-1, 1):
                p0 = (W / 2 + side * (k * 40), ayb + 30)
                p1 = (W / 2 + side * (k * 40 + 220 + off), ayb + 60 - off * 0.2)
                m = np.zeros((H, W), np.float32)
                cv2.arrowedLine(m, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 1.0, 12, cv2.LINE_AA, tipLength=0.25)
                clay(cv_, m * air, (230, 170, 70), puff=3, spec=0.3, shadow=None)
    if dust > 0:
        for k in range(70):
            r_ = rng.uniform(40, 220) * (0.5 + dust)
            dx = rng.normal(0, 380 * dust); dy = -abs(rng.normal(0, 260 * dust))
            m = np.zeros((H, W), np.float32)
            cv2.circle(m, (int(W / 2 + dx), int(cy + ch + dy)), int(r_), 1.0, -1)
            clay(cv_, cv2.GaussianBlur(m, (0, 0), 20), (150, 160, 170), puff=20, spec=0.0, shadow=None, alpha=0.35 * (1.2 - dust * 0.6))
    if counter is not None:                     # floor counter box, top of frame
        clay(cv_, rect_mask(W / 2 - 170, 150, W / 2 + 170, 330, 18), (30, 30, 35), puff=8, spec=0.2)
        text(cv_, f'{int(counter):02d}', W / 2, 240, 120, fill=(60, 160, 255), stroke=(10, 20, 40), sw=4)
        text(cv_, 'FLOORS FALLEN', W / 2, 375, 44, fill=(230, 230, 230), stroke=(20, 20, 20), sw=5)
    return cv_


# ------------------------------------------------------------------ skyline / bomber
class City:
    def __init__(self, A, rng):
        self.A = A
        self.bld = []
        x = -60
        while x < W + 60:
            w = rng.integers(90, 200); h = rng.integers(500, 1100)
            self.bld.append((x, w, h, rng.uniform(0.4, 1.0)))
            x += w + rng.integers(-10, 20)
        self.fog = cv2.GaussianBlur(rng.normal(0, 1, (H // 8, W // 8)).astype(np.float32), (0, 0), 4)

    def draw(self, cv_, t, hit=None, plane_x=None, shake=0.0, rng=None, fade=1.0):
        cv_[:] = np.linspace(120, 175, H)[:, None, None] * np.array([1.0, 1.0, 1.02])          # grey sky
        ground = H - 240
        for (x, w, h, d) in sorted(self.bld, key=lambda b: b[3]):
            col = np.array([95, 100, 110]) * (0.7 + 0.3 * d)
            clay(cv_, rect_mask(x, ground - h * d, x + w, ground + 10, 6), tuple(col), puff=7, spec=0.05, shadow=None)
            for wy in range(int(ground - h * d + 30), ground - 20, 46):         # windows
                for wx in range(int(x + 14), int(x + w - 20), 34):
                    cv2.rectangle(cv_, (wx, wy), (wx + 14, wy + 20), (70, 80, 90), -1)
        # the Empire State Building: stepped tower, centre
        ex = W / 2
        tiers = [(300, 700), (220, 980), (150, 1180), (90, 1300), (40, 1420), (10, 1520)]
        for wd, ht in tiers:
            clay(cv_, rect_mask(ex - wd, ground - ht, ex + wd, ground + 10, 8), (130, 135, 140), puff=9, spec=0.12, shadow=(12, 14, 0.35))
        for wy in range(ground - 1160, ground - 30, 40):
            for wx in range(int(ex - 130), int(ex + 130), 30):
                cv2.rectangle(cv_, (wx, wy), (wx + 10, wy + 18), (80, 88, 98), -1)
        if plane_x is not None:
            py = ground - 960 + (plane_x - ex) * 0.05
            m = np.zeros((H, W), np.float32)
            cv2.ellipse(m, (int(plane_x), int(py)), (170, 30), 0, 0, 360, 1.0, -1)               # fuselage
            cv2.fillPoly(m, [np.array([(plane_x - 40, py), (plane_x + 50, py), (plane_x - 30, py + 120), (plane_x - 90, py + 120)], np.int32)], 1.0)
            cv2.fillPoly(m, [np.array([(plane_x + 130, py - 10), (plane_x + 170, py - 90), (plane_x + 185, py - 90), (plane_x + 175, py)], np.int32)], 1.0)
            clay(cv_, m, (70, 85, 80), puff=6, spec=0.3, shadow=None)
            for ex_ in (-60, 30):
                cv2.circle(cv_, (int(plane_x + ex_), int(py + 60)), 26, (50, 55, 50), -1, cv2.LINE_AA)
        if hit is not None and hit > 0:
            cx, cy = ex + 40, ground - 950
            fire = np.zeros((H, W), np.float32)
            for k in range(40):
                r_ = rng.uniform(30, 160) * min(1, hit * 2)
                cv2.circle(fire, (int(cx + rng.normal(0, 120 * min(1, hit))), int(cy + rng.normal(0, 60) - 120 * hit * rng.random())), int(r_), 1.0, -1)
            fire = cv2.GaussianBlur(fire, (0, 0), 16)
            col = np.where(fire[..., None] > 0.6, np.array([80, 200, 255]), np.array([30, 110, 240]))
            glow = cv2.GaussianBlur(fire, (0, 0), 90)[..., None]
            cv_[:] = cv_ * (1 - fire[..., None] * 0.9) + col * fire[..., None] * 0.9 + glow * np.array([40, 110, 220]) * 0.8
            if hit < 0.15:
                cv_ += 255 * (1 - hit / 0.15) * 0.7
        fog = cv2.resize(self.fog, (W, H)) + np.sin(np.arange(W) / 200 + t * 0.4)[None, :] * 0.3
        fogm = np.clip(0.55 + fog * 0.25, 0, 0.85)[..., None] * np.linspace(0.6, 1.0, H)[:, None, None]
        cv_[:] = cv_ * (1 - fogm) + 190 * fogm
        cv_ *= fade
        return cv_


# ------------------------------------------------------------------ lobby (rescue)
def lobby(cv_, A, t, k):
    cv_[:] = tiled(A.slate, H, W, 1.4) * 0.75
    cv_[:H - 500] = cv_[:H - 500] * 0.6 + np.array([60, 85, 120]) * 0.4                          # dim marble-ish wall
    clay(cv_, rect_mask(240, 360, W - 240, H - 480, 10), (40, 120, 190), puff=10, spec=0.3)        # brass frame
    clay(cv_, rect_mask(290, 410, W - 290, H - 500, 6), (35, 35, 40), puff=4, spec=0.05, shadow=None)
    glowm = cv2.GaussianBlur(rect_mask(290, 410, W - 290, H - 500, 6), (0, 0), 50)
    cv_ += glowm[..., None] * np.array([40, 120, 200]) * 0.4
    # floor indicator arrow
    clay(cv_, rect_mask(W / 2 - 120, 220, W / 2 + 120, 320, 30), (30, 140, 220), puff=8, spec=0.4)
    # rescuers walking her in: two clay figures, seen from behind, step in sync
    for j, (p, xoff) in enumerate(zip(A.people, (-130, 130))):
        ph = int(900 - 260 * k)
        pw = int(p.shape[1] * ph / p.shape[0])
        bob = int(14 * abs(np.sin(t * 7 + j)))
        px = int(W / 2 + xoff * (1 - 0.4 * k) - pw / 2)
        py = int(H - 120 - ph - bob - 300 * k)
        pr = cv2.resize(p, (pw, ph))
        a = pr[..., 3:].astype(np.float32) / 255
        y0, y1, x0, x1 = max(0, py), min(H, py + ph), max(0, px), min(W, px + pw)
        if y1 > y0 and x1 > x0:
            cv_[y0:y1, x0:x1] = cv_[y0:y1, x0:x1] * (1 - a[y0 - py:y1 - py, x0 - px:x1 - px]) + pr[y0 - py:y1 - py, x0 - px:x1 - px, :3] * a[y0 - py:y1 - py, x0 - px:x1 - px]
    # her: a smaller figure in operator navy between them
    p = A.people[1]
    ph = int(780 - 230 * k); pw = int(p.shape[1] * ph / p.shape[0])
    pr = cv2.resize(p, (pw, ph)).astype(np.float32)
    pr[..., :3] = pr[..., :3] * np.array([1.3, 0.75, 0.55]) * 0.8                                 # navy uniform tint
    px = int(W / 2 - pw / 2); py = int(H - 150 - ph - 300 * k + 10 * np.sin(t * 7))
    a = pr[..., 3:] / 255
    y0, y1, x0, x1 = max(0, py), min(H, py + ph), max(0, px), min(W, px + pw)
    if y1 > y0 and x1 > x0:
        cv_[y0:y1, x0:x1] = cv_[y0:y1, x0:x1] * (1 - a[y0 - py:y1 - py, x0 - px:x1 - px]) + pr[y0 - py:y1 - py, x0 - px:x1 - px, :3] * a[y0 - py:y1 - py, x0 - px:x1 - px]
    return cv_


# ------------------------------------------------------------------ medal and doors
def medal(cv_, t, k):
    cv_[:] = np.linspace(40, 15, H)[:, None, None] * np.array([1.2, 1.0, 0.9])
    rays = np.zeros((H, W), np.float32)
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        a2 = a + t * 0.3
        cv2.fillPoly(rays, [np.array([(W / 2, H / 2), (W / 2 + np.cos(a2) * 1600, H / 2 + np.sin(a2) * 1600),
                                      (W / 2 + np.cos(a2 + 0.08) * 1600, H / 2 + np.sin(a2 + 0.08) * 1600)], np.int32)], 1.0)
    cv_ += cv2.GaussianBlur(rays, (0, 0), 8)[..., None] * np.array([30, 120, 190]) * 0.5 * k
    s = pop(t, 0.0, 0.5) if k > 0 else 0
    spin = np.cos(np.clip(1 - t / 1.2, 0, 1) * np.pi * 3)                                          # spins in, settles
    r = int(360 * s)
    if r > 5:
        m = np.zeros((H, W), np.float32)
        cv2.ellipse(m, (W // 2, H // 2), (max(4, int(r * abs(spin))), r), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        clay(cv_, m, (40, 170, 230), puff=18, spec=0.6, shadow=(20, 26, 0.5))
        inner = np.zeros((H, W), np.float32)
        cv2.ellipse(inner, (W // 2, H // 2), (max(2, int(r * 0.78 * abs(spin))), int(r * 0.78)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        clay(cv_, inner, (30, 145, 210), puff=10, spec=0.5, shadow=None)
        if abs(spin) > 0.6:
            text(cv_, '75', W / 2, H / 2 - 50, 230 * abs(spin), fill=(40, 120, 175), stroke=(20, 70, 110), sw=3)
            text(cv_, 'FLOORS', W / 2, H / 2 + 120, 90 * abs(spin), fill=(40, 120, 175), stroke=(20, 70, 110), sw=2)
        # ribbon
        rb = np.zeros((H, W), np.float32)
        cv2.fillPoly(rb, [np.array([(W / 2 - 160, H / 2 - r - 400), (W / 2 - 40, H / 2 - r - 400), (W / 2 + 30, H / 2 - r + 30), (W / 2 - 90, H / 2 - r + 30)], np.int32)], 1.0)
        cv2.fillPoly(rb, [np.array([(W / 2 + 160, H / 2 - r - 400), (W / 2 + 40, H / 2 - r - 400), (W / 2 - 30, H / 2 - r + 30), (W / 2 + 90, H / 2 - r + 30)], np.int32)], 1.0)
        clay(cv_, rb, (60, 40, 190), puff=8, spec=0.2, shadow=(10, 12, 0.4))
    text(cv_, "STILL A WORLD RECORD", W / 2, H - 330, 74, alpha=min(1, max(0, (t - 0.8) * 3)))
    return cv_


def doors(cv_, A, t, close):
    cv_[:] = tiled(A.slate, H, W, 1.4) * 0.55
    # inside the car: warm light, then doors slide shut from both sides
    clay(cv_, rect_mask(200, 300, W - 200, H - 300, 10), (110, 150, 190), puff=10, spec=0.2)
    gap = (W - 400) / 2 * (1 - close)
    steel = tiled(A.steel, H, W, 1.2)
    clay(cv_, rect_mask(200, 300, W / 2 - gap + 2, H - 300, 6), None, tex=steel, puff=8, spec=0.35)
    clay(cv_, rect_mask(W / 2 + gap - 2, 300, W - 200, H - 300, 6), None, tex=steel, puff=8, spec=0.35)
    # indicator light that dings on
    on = 1.0 if close > 0.95 else 0.25
    clay(cv_, rect_mask(W / 2 - 60, 170, W / 2 + 60, 250, 30), (60 * on, 170 * on + 40, 255 * on), puff=6, spec=0.5)
    return cv_


# ------------------------------------------------------------------ the timeline
def render(out, cues=CUES, only=None):
    rng = np.random.default_rng(6)
    A = Assets()
    city = City(A, rng)
    C = cues
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', out], stdin=subprocess.PIPE)
    vig = cv2.GaussianBlur(np.pad(np.ones((H - 400, W - 300), np.float32), ((200, 200), (150, 150))), (0, 0), 160)
    vig = (0.72 + 0.28 * vig)[..., None]
    start_y = 10 * FLOOR                       # car top, world px (floor 66)
    frame = None
    t0 = 0 if only is None else C[list(C)[only[0]]]
    t1 = C['end'] if only is None else C[list(C)[only[1]]]
    for i in range(int(t0 * FPS), int(t1 * FPS)):
        t = i / FPS
        if i % STEP:
            ff.stdin.write(frame.tobytes()); continue
        cv_ = np.zeros((H, W, 3), np.float32)
        shake = 0.0
        tint = None
        if t < C['rewind']:                                         # 1. the snap
            k = t - C['snap']
            fall = max(0, k - 0.7)
            car = start_y + 0.5 * 2600 * fall ** 2
            shaft(cv_, A, car, start_y + 250 + (car - start_y) * 0.75, cables='intact' if k < 0.7 else 'snapped', hair=min(1, fall * 3),
                  speed=min(1, fall * 1.5), whip=(k - 0.7) if k > 0.7 else None, rng=rng, t=t)
            shake = 14 if 0.7 < k < 1.0 else 3 * min(1, fall)
            s = pop(t, C['snap'] + 0.15, 0.3)
            if s:
                text(cv_, 'CABLE SNAPS', W / 2, 520, 140 * s, fill=(255, 255, 255), stroke=(10, 10, 10), sw=12, rot=4)
        elif t < C['cables']:                                       # 2. freeze, rewind
            k = (t - C['rewind']) / (C['cables'] - C['rewind'])
            back = ease(min(1, max(0, (k - 0.15) / 0.6)))
            fall_end = C['rewind'] - C['snap'] - 0.7
            car = start_y + 0.5 * 2600 * fall_end ** 2 * (1 - back)
            shaft(cv_, A, car, car + 250, cables='intact' if back > 0.95 else 'snapped', rng=rng, t=t)
            tint = 'rewind' if back < 0.98 else 'soft'
        elif t < C['cutall']:                                       # 3. six cables, each one enough
            k = t - C['cables']
            glow = [min(1, max(0, (k - 0.4 - j * 0.45) * 4)) for j in range(6)]
            if k > 3.3:
                glow = [1 if j == 3 else 0.15 for j in range(6)]
            shaft(cv_, A, start_y, start_y + 250, cables='glow', glow=glow, rng=rng, t=t)
            tint = 'soft'
            s = pop(t, C['cables'] + 0.4 + 6 * 0.45, 0.3)
            if s:
                text(cv_, 'x6', W - 170, 560, 110 * s, fill=(110, 230, 255), sw=8)
        elif t < C['black']:                                        # 4. cut them all: brakes
            k = t - C['cutall']
            fall = np.clip(k - 0.5, 0, 0.55)
            stop = k > 1.05
            car = start_y + 0.5 * 2600 * fall ** 2
            br = 0 if k < 0.95 else min(1, (k - 0.95) * 10)
            shaft(cv_, A, car, start_y + 250, cables='intact' if k < 0.5 else 'cut', brakes=br, whip=(k - 0.5) if k > 0.5 else None,
                  sparks=max(0, 1 - (k - 1.0) * 1.5) if k > 0.95 else 0, hair=0 if stop else min(1, fall * 3), rng=rng, t=t)
            shake = 22 * np.exp(-(k - 1.05) * 4) if stop else (6 if k > 0.5 else 0)
            tint = 'soft'
            s = pop(t, C['cutall'] + 1.1, 0.3)
            if s:
                text(cv_, 'SAFETY BRAKES', W / 2, H - 300, 88 * s, fill=(110, 230, 255), sw=10)
        elif t < C['bomber']:                                       # 5. black, fade up 1945
            k = (t - C['black']) / (C['bomber'] - C['black'])
            city.draw(cv_, t, fade=ease(max(0, (k - 0.3) / 0.7)))
            s = pop(t, C['black'] + 1.2, 0.4)
            if s:
                text(cv_, 'NEW YORK, 1945', W / 2, 420, 100 * s, alpha=min(1, (k - 0.35) * 3))
        elif t < C['lobby']:                                        # 6. the bomber
            k = t - C['bomber']
            hit_t = 2.0
            px = -300 + (W / 2 + 340) * min(1, k / hit_t)
            city.draw(cv_, t, hit=(k - hit_t) if k > hit_t else None, plane_x=px if k < hit_t + 0.05 else None, rng=rng)
            shake = 26 * np.exp(-(k - hit_t) * 2.5) if k > hit_t else 0
        elif t < C['frayed']:                                       # 7. rescuers walk her in
            k = (t - C['lobby']) / (C['frayed'] - C['lobby'])
            lobby(cv_, A, t, ease(k))
        elif t < C['fall']:                                         # 8. push up: cables already cut
            k = (t - C['frayed']) / (C['fall'] - C['frayed'])
            car = 1 * FLOOR
            shaft(cv_, A, car, car + 250 - 520 * ease(k), cables='snapped', rng=rng, t=t)
            s = pop(t, C['frayed'] + 1.4, 0.3)
            if s:
                text(cv_, 'ALREADY CUT', W / 2, H - 260, 120 * s, fill=(80, 80, 255), sw=10, rot=-3)
        elif t < C['pit']:                                          # 9. the 75-floor fall
            k = (t - C['fall']) / (C['pit'] - C['fall'])
            car = 1 * FLOOR + (73 * FLOOR) * k ** 1.6
            shaft(cv_, A, car, car + 250, cables='snapped', speed=min(1, k * 3), hair=1, rng=rng, t=t,
                  counter=max(1, int(75 * k ** 1.6)))
            shake = 4 + 6 * k
        elif t < C['crash']:                                        # 10. coil + air cushion
            k = (t - C['pit']) / (C['crash'] - C['pit'])
            car = 74 * FLOOR + 380 * (1 - (1 - k) ** 2)
            shaft(cv_, A, car, 74 * FLOOR + 500, cables='snapped', coil=min(1, k * 1.6), air=min(1, k * 3), pit=True,
                  hair=1 - k * 0.6, rng=rng, t=t, counter=75)
            tint = 'soft'
            for j, lbl in enumerate(('COILED CABLE', 'AIR CUSHION')):
                s = pop(t, C['pit'] + 0.6 + j * 2.2, 0.3)
                if s:
                    text(cv_, lbl, W / 2, 440 + j * 140, 84 * s, fill=(110, 230, 255) if j == 0 else (80, 190, 255), sw=8)
        elif t < C['medal']:                                        # 11. crash, dust, survived
            k = t - C['crash']
            car = 74 * FLOOR + 380 + min(1, k * 8) * 80
            shaft(cv_, A, car, 74 * FLOOR + 500, cables='snapped', coil=1, pit=True, dust=min(1.2, k * 0.8), rng=rng, t=t, counter=75)
            shake = 30 * np.exp(-k * 4)
            s = pop(t, C['crash'] + 2.2, 0.35)
            if s:
                text(cv_, 'SURVIVED', W / 2, H / 2 - 200, 190 * s, fill=(120, 255, 140), stroke=(20, 40, 20), sw=14, rot=-5)
        elif t < C['doors']:                                        # 12. medal
            medal(cv_, t - C['medal'], 1.0)
        else:                                                       # 13. modern elevator, doors close
            k = (t - C['doors']) / (C['end'] - C['doors'])
            doors(cv_, A, t, ease(min(1, k * 1.6)))
            if k > 0.92:
                cv_ = cv_ * (1 - (k - 0.92) / 0.08)                 # dip to black, loops into the snap
        if tint == 'rewind':
            g = cv_.mean(2, keepdims=True)
            cv_ = (cv_ * 0.3 + g * 0.7) * np.array([1.1, 1.0, 0.85])
            for y in range(int((t * 900) % 60), H, 60):
                cv_[y:y + 4] += 40
        elif tint == 'soft':
            cv_ = cv_ * 0.9 + np.array([200, 190, 170]) * 0.1
        if shake:
            M = np.float32([[1.03, 0, -W * 0.015 + rng.normal(0, shake)], [0, 1.03, -H * 0.015 + rng.normal(0, shake)]])
            cv_ = cv2.warpAffine(cv_, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        cv_ = cv_ * vig
        frame = np.clip(cv_ + rng.normal(0, 4, cv_.shape), 0, 255).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--cues')
    ap.add_argument('--only', help='beat index range a,b, e.g. 0,3 renders snap..cutall')
    a = ap.parse_args()
    c = dict(CUES)
    if a.cues:
        c.update(json.load(open(a.cues)))
    render(a.out, c, [int(x) for x in a.only.split(',')] if a.only else None)
