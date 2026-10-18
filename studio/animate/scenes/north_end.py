#!/usr/bin/env python3
"""North End, from above: a clay town built in code from real clay textures, and a
molasses flood that is actually simulated (it runs down the streets, splits around
blocks, knocks over the houses nearest the tank and bends the elevated railway).

    python3 studio/animate/scenes/north_end.py out.mp4 [--secs 5.07] [--lens 0.55]

Textures (studio/animate/textures): cobble, slate, shingle, tankside, molasses_clay.
They were cut from the stills of the same shoot, so the town reads as the same clay set.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from animate import FPS, H, STEP, W  # noqa: E402
from molasses import MOL_LITE, MOL_MID, Syrup, flow_noise, grain, vignette, writer  # noqa: E402

TEX = os.path.join(HERE, '..', 'textures')
MW, MH = 1400, 2490                  # map size; the camera frames part of it
CELL = 10                             # simulation cell size in map pixels
LIGHT = np.array([-0.55, -0.65, 0.52])   # top-left, matches the stills
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def tex(name):
    return cv2.imread(os.path.join(TEX, name)).astype(np.float32)


def tiled(t, h, w, scale=1.0, off=(0, 0)):
    th, tw = t.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(t, ((xx / scale + off[0]) % tw).astype(np.float32), ((yy / scale + off[1]) % th).astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def soft_shadow(canvas, mask, dx=16, dy=20, blur=9, strength=0.45):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    sh = cv2.GaussianBlur(cv2.warpAffine(mask, M, (canvas.shape[1], canvas.shape[0])), (0, 0), blur)
    return canvas * (1 - strength * sh[..., None])


# ------------------------------------------------------------------ town layout
def layout(rng):
    """Returns ground, building list, tank, rail polyline. All in map pixels."""
    shore = 300 + 40 * np.sin(np.arange(MW) / 140) + 15 * np.sin(np.arange(MW) / 37)
    streets_h = [(600, 700), (1180, 1250), (1760, 1830), (2300, 2370)]     # (y0, y1)
    streets_v = [(250, 320), (760, 830), (1180, 1250)]
    diag = ((830, 1250), (1180, 2370), 70)                                  # a crooked lane
    tank = dict(c=(470, 440), r=150)
    buildings = []
    ys = [700] + [b for a, b in streets_h[1:]]
    ye = [a for a, b in streets_h[1:]] + [MH]
    xs = [0] + [b for a, b in streets_v]
    xe = [a for a, b in streets_v] + [MW]
    for by0, by1 in zip(ys, ye):
        for bx0, bx1 in zip(xs, xe):
            y = by0 + 14
            while y < by1 - 60:
                hgt = rng.integers(110, 190)
                x = bx0 + 14
                while x < bx1 - 60:
                    wid = rng.integers(90, 170)
                    x1, y1 = min(x + wid, bx1 - 14), min(y + hgt, by1 - 14)
                    if x1 - x > 50 and y1 - y > 50:
                        buildings.append(dict(r=(x, y, x1, y1), roof=rng.choice(['slate', 'shingle', 'shingle', 'slate']),
                                              tint=rng.choice([0, 1, 2, 3]), axis=int(rng.integers(0, 2))))
                    x = x1 + rng.integers(8, 22)
                y += hgt + rng.integers(10, 26)
    # waterfront row between the tank lot and Commercial Street
    for x in range(700, MW - 100, 150):
        buildings.append(dict(r=(x, 380, x + 128, 560), roof='shingle', tint=int(rng.integers(0, 4)), axis=0, waterfront=True))
    # houses right next to the tank: these are the ones the flood takes
    for (x, y) in ((250, 470), (90, 420), (660, 390)):
        buildings.append(dict(r=(x - 60, y - 45, x + 60, y + 50), roof='shingle', tint=1, axis=1, crush=True))
    # drop anything sitting on the crooked lane
    (ax, ay), (bx, by), lw = diag
    def on_lane(r):
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        t = np.clip(((cx - ax) * (bx - ax) + (cy - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0, 1)
        px, py = ax + t * (bx - ax), ay + t * (by - ay)
        return np.hypot(cx - px, cy - py) < lw / 2 + max(r[2] - r[0], r[3] - r[1]) / 2
    buildings = [b for b in buildings if b.get('crush') or not on_lane(b['r'])]
    rail = np.array([(0, 650), (MW, 650)], np.float32)                     # elevated line over Commercial St
    return shore, streets_h, streets_v, diag, tank, buildings, rail


TINTS = [np.array([1.0, 1.0, 1.0]), np.array([0.78, 0.86, 1.12]), np.array([0.85, 0.95, 1.05]), np.array([1.05, 1.0, 0.92])]


def draw_building(canvas, b, roofs, ox=0, oy=0, rot=0.0, sink=0.0):
    """One clay block: roof texture, gable split in light and shade, ridge, bevel. Returns (img, mask) patch placed on canvas."""
    x0, y0, x1, y1 = b['r']
    w, h = x1 - x0, y1 - y0
    pad = 30
    rs = roofs[b['roof']]
    oy_, ox_ = (x0 * 7 + y0 * 3) % max(1, rs.shape[0] - h), (y0 * 5 + x0) % max(1, rs.shape[1] - w)
    patch = rs[oy_:oy_ + h, ox_:ox_ + w] if rs.shape[0] >= h and rs.shape[1] >= w else cv2.resize(rs, (w, h))
    patch = patch * TINTS[b['tint']][None, None, :]
    m = np.zeros((h, w), np.float32)
    cv2.rectangle(m, (3, 3), (w - 4, h - 4), 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 2.2)
    # gable: one slope toward the light, one away
    if b['axis'] == 0:
        half = np.r_[np.full(h // 2, 1.12), np.full(h - h // 2, 0.82)][:, None]
        ridge = np.exp(-((np.arange(h) - h / 2) / 2.2) ** 2)[:, None]
    else:
        half = np.r_[np.full(w // 2, 1.12), np.full(w - w // 2, 0.82)][None, :]
        ridge = np.exp(-((np.arange(w) - w / 2) / 2.2) ** 2)[None, :]
    patch = patch * half[..., None] * (1 - 0.35 * ridge[..., None])
    # bevel: rim lit top-left, dark bottom-right
    e = cv2.GaussianBlur(m, (0, 0), 4)
    gy, gx = np.gradient(e)
    bev = np.clip(-(gx * LIGHT[0] + gy * LIGHT[1]) * 9, -0.3, 0.3)
    patch = np.clip(patch * (1 + bev[..., None]) * (1 - sink * 0.7), 0, 255)
    full = np.zeros((h + 2 * pad, w + 2 * pad, 3), np.float32); fm = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    full[pad:pad + h, pad:pad + w] = patch; fm[pad:pad + h, pad:pad + w] = m * (1 - sink)
    cx, cy = x0 + w / 2 + ox, y0 + h / 2 + oy
    R = cv2.getRotationMatrix2D(((w + 2 * pad) / 2, (h + 2 * pad) / 2), rot, 1.0)
    R[0, 2] += cx - (w + 2 * pad) / 2; R[1, 2] += cy - (h + 2 * pad) / 2
    img = cv2.warpAffine(full, R, (canvas.shape[1], canvas.shape[0]))
    msk = cv2.warpAffine(fm, R, (canvas.shape[1], canvas.shape[0]))
    return img, msk


def build_town(rng):
    shore, sh, sv, diag, tank, blds, rail = layout(rng)
    cob = tex('cobble.png')
    ground = cv2.GaussianBlur(tiled(cob, MH, MW, scale=0.45), (0, 0), 1.2)
    gm_ = ground.mean(2, keepdims=True)
    ground = (ground * 0.45 + gm_ * 0.55) * 0.8
    # blocks (between streets) are packed earth/yards, darker and smoother than the cobbles
    yard = cv2.GaussianBlur(tiled(cob, MH, MW, scale=0.6), (0, 0), 3) * np.array([0.62, 0.7, 0.78])
    streets = np.zeros((MH, MW), np.float32)
    for a, b in sh:
        streets[a:b] = 1
    for a, b in sv:
        streets[:, a:b] = 1
    (ax, ay), (bx, by), lw = diag
    cv2.line(streets, (ax, ay), (bx, by), 1.0, lw)
    streets[:700, :] = 1                                     # waterfront lot is open ground
    streets = cv2.GaussianBlur(streets, (0, 0), 3)
    ground = ground * streets[..., None] + yard * (1 - streets[..., None])
    # curbs: a soft dark line where street meets yard
    curb = np.abs(cv2.Laplacian(streets, cv2.CV_32F, ksize=5))
    ground = ground * (1 - np.clip(curb * 0.35, 0, 0.4)[..., None])
    # harbor: cold grey-green water with clay ripples, a wooden wharf
    yy, xx = np.mgrid[0:MH, 0:MW].astype(np.float32)
    water = (yy < shore[None, :]).astype(np.float32)
    rip = flow_noise((MH, MW), 0, 4, 22)
    wcol = np.array([92, 92, 70], np.float32) * (0.9 + 0.1 * rip)[..., None]
    wcol = wcol * (0.75 + 0.25 * np.clip(yy / 300, 0, 1))[..., None]
    wm = cv2.GaussianBlur(water, (0, 0), 4)[..., None]
    ground = ground * (1 - wm) + wcol * wm
    for x in (980, 1180):                                    # piers
        cv2.rectangle(ground, (x, 60), (x + 70, 330), (40, 62, 88), -1)
        for y in range(70, 330, 16):
            cv2.line(ground, (x, y), (x + 70, y), (28, 44, 66), 2)
    ground = np.ascontiguousarray(ground)
    # passable mask for the flood
    block = np.zeros((MH, MW), np.uint8)
    roofs = {'slate': tiled(tex('slate.png'), 400, 400, 0.7), 'shingle': tiled(tex('shingle.png'), 400, 400, 0.7)}
    static = ground.copy()
    movers = []
    allm = np.zeros((MH, MW), np.float32)
    for b in blds:
        x0, y0, x1, y1 = b['r']
        if b.get('crush'):
            movers.append(b)
            continue
        block[y0 + 6:y1 - 6, x0 + 6:x1 - 6] = 1
        img, m = draw_building(static, b, roofs)
        allm = np.maximum(allm, m)
        static = static * (1 - m[..., None]) + img * m[..., None]
    static = soft_shadow(static, allm)
    # re-draw roofs over their own shadow
    for b in blds:
        if not b.get('crush'):
            img, m = draw_building(static, b, roofs)
            static = static * (1 - m[..., None]) + img * m[..., None]
    return dict(ground=ground, static=static, block=block, streets=streets, movers=movers, roofs=roofs, tank=tank, rail=rail, shore=shore)


def draw_tank(canvas, tank, burst, t):
    """Tank from above: its side texture wrapped into rings; once burst, a torn ring with the middle gone."""
    side = tex('tankside.png')
    cx, cy = tank['c']; r = tank['r']
    s = int(r * 2 + 80)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - s / 2
    rr = np.hypot(xx, yy); ang = np.arctan2(yy, xx)
    my = np.clip(rr / r, 0, 1) * (side.shape[0] - 1)
    mx = (ang / (2 * np.pi) + 0.5) * (side.shape[1] - 1)
    img = cv2.remap(side, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR)
    light = 1 + 0.25 * (-(xx * LIGHT[0] + yy * LIGHT[1]) / (rr + 1e-3)) * np.clip(rr / r, 0, 1)
    img = img * light[..., None]
    m = np.clip((r - rr) / 2.5, 0, 1)
    rim = np.exp(-((rr - r + 8) / 5) ** 2)
    img = img * (1 + 0.35 * rim[..., None])
    if burst > 0:                                              # top blown off: only a jagged ring remains
        jag = r * (0.62 + 0.12 * np.sin(ang * 7) + 0.06 * np.sin(ang * 19 + 1))
        hole = np.clip((jag * (0.4 + 0.6 * min(1, burst * 3)) - rr) / 3, 0, 1)
        m = m * (1 - hole)
        img = img * (1 - 0.4 * np.exp(-((rr - jag) / 6) ** 2))[..., None]
    x0, y0 = int(cx - s / 2), int(cy - s / 2)
    sub = canvas[y0:y0 + s, x0:x0 + s]
    sub[:] = sub * (1 - m[..., None]) + img * m[..., None]


def draw_rail(canvas, rail, bend_x, bend_amt):
    """Elevated railway: steel deck with cross ties, shadow cast on the street; bends where the flood hit."""
    xs = np.arange(0, MW, 4, dtype=np.float32)
    y = rail[0, 1] + bend_amt * np.exp(-((xs - bend_x) / 140) ** 2) + 0.0 * xs
    deck = np.zeros(canvas.shape[:2], np.float32)
    pts = np.c_[xs, y].astype(np.int32)
    cv2.polylines(deck, [pts], False, 1.0, 34, cv2.LINE_AA)
    sh = cv2.GaussianBlur(cv2.warpAffine(deck, np.float32([[1, 0, 26], [0, 1, 40]]), (MW, MH)), (0, 0), 6)
    out = canvas * (1 - 0.45 * sh[..., None])
    col = np.zeros_like(canvas); col[:] = (52, 56, 60)
    for x in range(0, MW, 22):                                 # ties
        yy0 = int(rail[0, 1] + bend_amt * np.exp(-((x - bend_x) / 140) ** 2))
        cv2.line(col, (x, yy0 - 17), (x, yy0 + 17), (34, 36, 40), 5)
    for off in (-12, 12):                                      # rails, lit edge on top
        cv2.polylines(col, [np.c_[xs, y + off].astype(np.int32)], False, (95, 100, 106), 4, cv2.LINE_AA)
    return out * (1 - deck[..., None]) + col * deck[..., None]


# ------------------------------------------------------------------ flood sim
class Flood:
    def __init__(self, town):
        self.gh, self.gw = MH // CELL, MW // CELL
        open_ = cv2.resize(town['streets'], (self.gw, self.gh), interpolation=cv2.INTER_AREA) > 0.5
        blk = cv2.resize(town['block'].astype(np.float32), (self.gw, self.gh), interpolation=cv2.INTER_AREA) > 0.5
        self.wall = (~open_) | blk
        self.wall[0, :] = self.wall[-1, :] = True; self.wall[:, 0] = self.wall[:, -1] = True
        self.h = np.zeros((self.gh, self.gw), np.float32)
        cx, cy = town['tank']['c']; r = town['tank']['r']
        yy, xx = np.mgrid[0:self.gh, 0:self.gw]
        self.src = np.hypot(xx * CELL - cx, yy * CELL - cy) < r * 0.8
        self.water = (yy * CELL) < (town['shore'][np.clip(xx * CELL, 0, MW - 1)] - 10)

    def step(self, dt, inject, sub=24):
        """Virtual-pipe shallow water: flux keeps its momentum, so the front races down streets."""
        if not hasattr(self, 'f'):
            self.f = np.zeros((4, self.gh, self.gw), np.float32)
        dirs = ((0, 1), (0, -1), (1, 0), (-1, 0))
        h = self.h
        k, damp = 0.045, 0.985
        for _ in range(sub):
            if inject > 0:
                h[self.src] += inject * dt / sub
            H0 = np.where(self.wall, 1e4, h)
            tot = np.zeros_like(h)
            for j, (dy, dx) in enumerate(dirs):
                nb = np.roll(np.roll(H0, -dy, 0), -dx, 1)
                self.f[j] = np.maximum(0, self.f[j] * damp + k * (H0 - nb))
                self.f[j][self.wall] = 0
                tot += self.f[j]
            scale = np.where(tot > h, h / (tot + 1e-9), 1.0)
            for j, (dy, dx) in enumerate(dirs):
                self.f[j] *= scale
                h = h - self.f[j] + np.roll(np.roll(self.f[j], dy, 0), dx, 1)
            h[self.wall] = 0
            h[self.water] *= 0.9995
        self.h = np.clip(h, 0, None)

    def depth_map(self):
        d = cv2.resize(self.h, (MW, MH), interpolation=cv2.INTER_CUBIC)
        return cv2.GaussianBlur(np.clip(d, 0, None), (0, 0), 5)


def render_flood(canvas, d, syrup, t, tank_c):
    m = np.clip((d - 0.04) / 0.06, 0, 1)
    gy, gx = np.gradient(cv2.GaussianBlur(d, (0, 0), 9) * 120)
    nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1)
    nx, ny = -gx * nz, -gy * nz
    diff = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    hx, hy, hz = LIGHT[0], LIGHT[1], LIGHT[2] + 1
    hn = np.sqrt(hx * hx + hy * hy + hz * hz)
    spec = np.clip((nx * hx + ny * hy + nz * hz) / hn, 0, 1) ** 40
    yy, xx = np.mgrid[0:MH, 0:MW].astype(np.float32)
    dist = np.hypot(xx - tank_c[0], yy - tank_c[1])
    ang = np.arctan2(yy - tank_c[1], xx - tank_c[0])
    wn = flow_noise((MH, MW), t, 9, 140) * 22
    tx = syrup.sample(xx * 0.55 + wn + dist * 0.15, yy * 0.4 + wn * 0.5 - 220 * t)
    shade = 0.55 + 0.6 * diff
    col = tx * shade[..., None] + spec[..., None] * np.array([150, 200, 235]) * 0.45
    edge = np.exp(-((m - 0.5) / 0.22) ** 2)                    # bright meniscus at the leading edge
    col = col + (MOL_LITE - col) * (edge * 0.25)[..., None]
    shadow = cv2.GaussianBlur(m, (0, 0), 6)                     # it sits on the ground: dark contact ring outside
    canvas = canvas * (1 - 0.35 * np.clip(shadow - m, 0, 1)[..., None])
    return canvas * (1 - m[..., None]) + col * m[..., None], m


# ------------------------------------------------------------------ people
class People:
    def __init__(self, rng, n=70):
        self.rng = rng
        street_ys = [650, 1215, 1795]
        self.p = []
        for _ in range(n):
            if rng.random() < 0.6:
                x, y = rng.uniform(40, MW - 40), rng.choice(street_ys) + rng.normal(0, 15)
            else:
                x, y = rng.choice([285, 795, 1215]) + rng.normal(0, 12), rng.uniform(720, MH - 60)
            self.p.append(dict(x=x, y=y, alive=True, col=[(40, 60, 120), (60, 50, 45), (70, 90, 110), (35, 40, 50)][int(rng.integers(0, 4))]))

    def step(self, dt, d, flood_wall):
        for q in self.p:
            if not q['alive']:
                continue
            xi, yi = int(np.clip(q['x'], 0, MW - 1)), int(np.clip(q['y'], 0, MH - 1))
            if d[yi, xi] > 0.08:
                q['alive'] = False
                continue
            # run away from the tank, stay on open ground
            vx, vy = (q['x'] - 470), (q['y'] - 440)
            n = np.hypot(vx, vy) + 1e-6
            sp = 70 + 40 * self.rng.random()
            nx, ny = q['x'] + vx / n * sp * dt, q['y'] + vy / n * sp * dt
            if not flood_wall[int(np.clip(ny, 0, MH - 1)), int(np.clip(nx, 0, MW - 1))]:
                q['x'], q['y'] = nx, ny

    def draw(self, canvas, t):
        for q in self.p:
            if not q['alive']:
                continue
            x, y = int(q['x']), int(q['y'])
            cv2.ellipse(canvas, (x + 6, y + 8), (12, 9), 20, 0, 360, (30, 34, 38), -1, cv2.LINE_AA)       # shadow
            cv2.ellipse(canvas, (x, y), (12, 8), 0, 0, 360, q['col'], -1, cv2.LINE_AA)                     # shoulders
            cv2.circle(canvas, (x, y), 6, (40, 42, 48), -1, cv2.LINE_AA)                                   # hat
            cv2.circle(canvas, (x - 2, y - 2), 2, (90, 95, 105), -1, cv2.LINE_AA)


# ------------------------------------------------------------------ shot
def render(out, secs=5.07, lens=0.55, seed=3):
    rng = np.random.default_rng(seed)
    town = build_town(rng)
    syrup = Syrup(town['static'][700:, :])
    flood = Flood(town)
    people = People(rng)
    tank_c = town['tank']['c']
    for _ in range(3):                                           # it is already pouring out when we cut in
        flood.step(1 / 24, 16)
    vig = vignette()
    ff = writer(out)
    frame = None
    crushed = {id(b): dict(t=None, ox=0, oy=0, rot=0) for b in town['movers']}
    bend_hit = None
    drip_x = np.sort(np.linspace(-20, W + 20, 26) + rng.normal(0, 8, 26))
    drip_v = rng.uniform(0.6, 1.4, 26)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for i in range(int(secs * FPS)):
        t = i / FPS
        if i % STEP == 0:
            dt = STEP / FPS
            flood.step(dt, 18 if t < 3.0 else 0)
            d = flood.depth_map()
            canvas = town['static'].copy()
            canvas, fm = render_flood(canvas, d, syrup, t, tank_c)
            draw_tank(canvas, town['tank'], 1.0, t)
            # houses by the tank: shove, spin and sink once the flood is deep around them
            for b in town['movers']:
                st = crushed[id(b)]
                x0, y0, x1, y1 = b['r']
                local = d[y0:y1, x0:x1].mean()
                if st['t'] is None and local > 0.12:
                    st['t'] = t
                sink = 0.0
                if st['t'] is not None:
                    k = t - st['t']
                    vx, vy = (x0 + x1) / 2 - tank_c[0], (y0 + y1) / 2 - tank_c[1]
                    n = np.hypot(vx, vy) + 1e-6
                    st['ox'] = vx / n * 160 * min(1, k * 1.5); st['oy'] = vy / n * 160 * min(1, k * 1.5)
                    st['rot'] = 35 * min(1, k * 1.2) * (1 if vx > 0 else -1)
                    sink = min(0.85, k * 0.55)
                img, m = draw_building(canvas, b, town['roofs'], st['ox'], st['oy'], st['rot'], sink)
                canvas = soft_shadow(canvas, m * (1 - sink), 10, 13, 6, 0.35)
                canvas = canvas * (1 - m[..., None]) + img * m[..., None]
            people.step(dt, d, town['block'] > 0)
            people.draw(canvas, t)
            # rail bends when the flood front passes under it near the tank
            under = d[650, 300:700].max()
            if bend_hit is None and under > 0.15:
                bend_hit = t
            bend = 0 if bend_hit is None else 70 * min(1, (t - bend_hit) * 2.5)
            canvas = draw_rail(canvas, town['rail'], 520, bend)
            # camera: start tight on the tank, pull back to show the flood running through town
            e = t / secs
            e = 1 - (1 - e) ** 2.2
            zoom = 1.75 - 0.95 * e                     # map px -> screen px
            cx = tank_c[0] + (MW / 2 - tank_c[0]) * e
            cy = tank_c[1] + 260 + (MH * 0.47 - tank_c[1] - 260) * e
            jx, jy = rng.normal(0, 1.3, 2)
            M = np.float32([[zoom, 0, W / 2 - zoom * cx + jx], [0, zoom, H / 2 - zoom * cy + jy]])
            fr = cv2.warpAffine(canvas, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            if t < lens:                                  # the blast on the lens slides off first
                q = t / lens
                lm = np.zeros((H, W), np.float32)
                for k2 in range(len(drip_x) - 1):
                    top = (q ** 1.6) * H * 1.3 * drip_v[k2]
                    cv2.rectangle(lm, (int(drip_x[k2]), int(top)), (int(drip_x[k2 + 1]) + 2, H), 1.0, -1)
                    cv2.circle(lm, (int((drip_x[k2] + drip_x[k2 + 1]) / 2), int(top)), int((drip_x[k2 + 1] - drip_x[k2]) * 0.6), 1.0, -1)
                lm = cv2.GaussianBlur(lm, (0, 0), 10)[..., None]
                fr = fr * (1 - lm) + syrup.sample(xx * 0.8, yy * 0.5 - 900 * t) * 0.8 * lm
            frame = grain(fr * vig, rng).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--secs', type=float, default=5.07)
    ap.add_argument('--lens', type=float, default=0.55)
    a = ap.parse_args()
    render(a.out, a.secs, a.lens)
