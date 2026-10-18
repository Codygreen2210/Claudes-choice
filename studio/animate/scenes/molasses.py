#!/usr/bin/env python3
"""Molasses flood: two code-animated shots, built on the animate engine.

    python3 studio/animate/scenes/molasses.py tank  tank_still.webp  out.mp4
    python3 studio/animate/scenes/molasses.py wave  street_still.webp out.mp4

tank: slow push in, rivets pop off one by one (bolt, spark, leak), the middle of the
      tank bulges, then blows out toward the camera: steel shards fly at the lens and
      a burst of molasses fills the frame.
wave: starts with molasses running off the lens (stitches to the tank shot), then a
      glossy wall rolls down the street over the camera. The syrup is a real clay
      texture (textures/molasses_clay.png) that is flowed, lit, colour-matched and
      depth-blurred to sit inside the same photo as the street.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..'))
from animate import FPS, H, STEP, W, ease, load, place, split_layers  # noqa: E402

MOL_MID = np.array([16, 38, 74], np.float32)       # BGR, used for small drawn bits
MOL_LITE = np.array([110, 170, 225], np.float32)


# ------------------------------------------------------------------ shared bits
def writer(out):
    return subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', out],
                            stdin=subprocess.PIPE)


def grain(frame, rng, amt=4):
    return np.clip(frame + rng.normal(0, amt, frame.shape), 0, 255)


def vignette():
    v = cv2.GaussianBlur(np.pad(np.ones((H - 400, W - 300), np.float32), ((200, 200), (150, 150))), (0, 0), 160)
    return (0.72 + 0.28 * v)[..., None]


class Syrup:
    """The clay molasses texture, colour-matched to a plate, sampled with a flow."""

    def __init__(self, plate=None):
        t = cv2.imread(os.path.join(HERE, '..', 'textures', 'molasses_clay.png')).astype(np.float32)
        if plate is not None:                       # pull its grade toward the plate so it sits in the same photo
            pm, ps = plate.reshape(-1, 3).mean(0), plate.reshape(-1, 3).std(0)
            tm, ts = t.reshape(-1, 3).mean(0), t.reshape(-1, 3).std(0)
            matched = (t - tm) / (ts + 1e-6) * (ts * 0.6 + ps * 0.4) + tm * 0.85 + pm * 0.15
            t = 0.65 * t + 0.35 * matched
        self.t = np.clip(t, 0, 255)
        self.th, self.tw = self.t.shape[:2]

    def sample(self, mx, my):
        return cv2.remap(self.t, (mx % self.tw).astype(np.float32), (my % self.th).astype(np.float32),
                         cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def flow_noise(shape, t, seed, scale=60, speed=(0, 0)):
    """Smooth moving noise in -1..1, cheap: sum of a few sines with seeded phases."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    n = np.zeros(shape, np.float32)
    for k in range(4):
        a = r.uniform(0, np.pi); f = scale * r.uniform(0.6, 1.6); ph = r.uniform(0, 6.28)
        n += np.sin((xx * np.cos(a) + yy * np.sin(a)) / f + ph + t * r.uniform(1, 3))
    return n / 4


# ------------------------------------------------------------------ tank
def tank(still, out, cues):
    rng = np.random.default_rng(11)
    img = load(still)
    back, subj, a = split_layers(img)
    m = (a > 0.5).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    tm = cv2.GaussianBlur((lab == k).astype(np.float32), (0, 0), 1.2)
    x0, y0, w0, h0 = stats[k, :4]
    cx, ym = x0 + w0 / 2, y0 + h0 * 0.52                       # blast centre: halfway up
    other = np.clip(a - tm, 0, 1)
    plate = subj * other[..., None] + back * (1 - other[..., None])
    syrup = Syrup(plate)
    band = h0 * 0.17
    ih, iw = img.shape[:2]
    rows = np.arange(ih, dtype=np.float32)[:, None]
    top_m = tm * (rows < ym - band)
    bot_m = tm * (rows > ym + band)
    mid_m = tm * (np.abs(rows - ym) <= band)

    # shards: jittered grid over the middle band, each a polygon of the tank texture
    shards = []
    cols, rws = 6, 3
    gx = np.linspace(x0 - 4, x0 + w0 + 4, cols + 1)
    gy = np.linspace(ym - band, ym + band, rws + 1)
    J = lambda: rng.normal(0, w0 * 0.025)
    pts = [[(gx[c] + (J() if 0 < c < cols else 0), gy[r] + (J() if 0 < r < rws else 0)) for c in range(cols + 1)] for r in range(rws + 1)]
    for r in range(rws):
        for c in range(cols):
            poly = np.array([pts[r][c], pts[r][c + 1], pts[r + 1][c + 1], pts[r + 1][c]], np.float32)
            pm = np.zeros((ih, iw), np.float32)
            cv2.fillPoly(pm, [poly.astype(np.int32)], 1.0)
            pm *= mid_m
            if pm.sum() < 50:
                continue
            ctr = poly.mean(0)
            d = ctr - np.array([cx, ym]); d /= np.linalg.norm(d) + 1e-6
            facing = 1 - abs((ctr[0] - cx) / (w0 / 2))           # shards from the front face come at the lens
            shards.append(dict(m=pm, c=ctr, v=d * rng.uniform(500, 1300) + rng.normal(0, 150, 2),
                               zv=rng.uniform(0.6, 1.4) + 3.5 * facing ** 2, w=rng.normal(0, 260)))

    pops = []
    for i, t0 in enumerate(cues['rivets']):
        px = cx + (rng.uniform(0.18, 0.42) * w0) * (-1 if i % 2 else 1)
        py = y0 + h0 * rng.uniform(0.25, 0.75)
        bolts = [(rng.uniform(-1, 1) * 900 + (300 if px > cx else -300), rng.uniform(-900, -300)) for _ in range(4)]
        pops.append((t0, px, py, bolts))

    # blast blobs: metaballs thrown out of the centre, growing as they come at the camera
    blobs = [dict(a=rng.uniform(0, 2 * np.pi), s=rng.uniform(250, 1100), r=rng.uniform(40, 120), born=rng.uniform(0, 0.25),
                  z=rng.uniform(1.5, 5)) for _ in range(90)]

    secs, split, bulge = cues['secs'], cues['split'], cues['bulge']
    vig = vignette()
    ff = writer(out)
    frame = None
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for i in range(int(secs * FPS)):
        t = i / FPS
        if i % STEP == 0:
            z = 1.0 + 0.07 * ease(min(1, t / split))
            jx, jy = rng.normal(0, 1.2, 2)
            if t > cues['rivets'][0]:
                amp = 4 + 6 * max(0, min(1, (t - bulge) / (split - bulge))) + (30 * np.exp(-(t - split) * 3) if t > split else 0)
                jx += rng.normal(0, amp); jy += rng.normal(0, amp)
            Msc = np.float32([[z, 0, W / 2 - z * iw / 2 + jx], [0, z, H / 2 - z * ih / 2 + jy]])
            to_scr = lambda p: (Msc[0, 0] * p[0] + Msc[0, 2], Msc[1, 1] * p[1] + Msc[1, 2])
            fr = place(plate, z * (1 + 0.45 * (z - 1)), jx * 0.5, jy * 0.5).astype(np.float32)
            scx, scy = to_scr((cx, ym))

            if t < split:
                # whole tank, with the middle swelling before it goes
                b = 0 if t < bulge else ease((t - bulge) / (split - bulge))
                timg, tmask = subj, tm
                if b > 0:
                    dy = (rows - ym) / (band * 2.2)
                    sw = np.exp(-dy ** 2) * 0.09 * b
                    xsrc = (cx + (np.arange(iw)[None, :] - cx) / (1 + sw)).astype(np.float32)
                    ysrc = np.repeat(rows, iw, 1).astype(np.float32)
                    timg = cv2.remap(subj, xsrc, ysrc, cv2.INTER_LINEAR)
                    tmask = cv2.remap(tm, xsrc, ysrc, cv2.INTER_LINEAR)
                hl = cv2.warpAffine(timg, Msc, (W, H)).astype(np.float32)
                hm = cv2.warpAffine(tmask, Msc, (W, H))[..., None]
                fr = fr * (1 - hm) + hl * hm
                if b > 0.3:                                            # seams glow with syrup pushing through
                    for sy in (ym - band * 0.6, ym, ym + band * 0.6):
                        _, py = to_scr((0, sy))
                        x1, _ = to_scr((x0 + w0 * 0.1, 0)); x2, _ = to_scr((x0 + w0 * 0.9, 0))
                        cv2.line(fr, (int(x1), int(py)), (int(x2), int(py)), MOL_MID.tolist(), int(2 + 6 * b), cv2.LINE_AA)
            else:
                d = t - split
                # lower section stays, upper section lurches up and tips back
                bl = cv2.warpAffine(subj, Msc, (W, H)).astype(np.float32)
                bm = cv2.warpAffine(bot_m, Msc, (W, H))[..., None]
                R = cv2.getRotationMatrix2D((float(cx), float(ym - band)), 9 * ease(min(1, d / 0.5)), 1.0)
                R[1, 2] += -60 * d + 500 * d * d
                A = (np.vstack([Msc, [0, 0, 1]]) @ np.vstack([R, [0, 0, 1]]))[:2]
                tl = cv2.warpAffine(subj, A, (W, H)).astype(np.float32)
                tmk = cv2.warpAffine(top_m, A, (W, H))[..., None]
                fr = fr * (1 - bm) + bl * bm
                fr = fr * (1 - tmk) + tl * tmk
                # flash
                if d < 0.12:
                    f = np.exp(-((xx - scx) ** 2 + (yy - scy) ** 2) / (2 * (200 + 2500 * d) ** 2))[..., None] * (1 - d / 0.12)
                    fr = fr + (np.array([150, 210, 255]) - fr) * f * 0.85
                # molasses blast: metaballs flying out and toward the lens
                gm = np.zeros((H, W), np.float32)
                for bb in blobs:
                    dd = d - bb['born']
                    if dd <= 0:
                        continue
                    zz = 1 + bb['z'] * dd ** 1.5 * 3
                    bx = scx + np.cos(bb['a']) * bb['s'] * dd * zz
                    by = scy + np.sin(bb['a']) * bb['s'] * dd * zz * 0.8 + 400 * dd * dd
                    cv2.circle(gm, (int(bx), int(by)), int(bb['r'] * z * zz * (0.4 + dd * 2)), 1.0, -1)
                core = int((60 + 2600 * d ** 1.6) * z)
                cv2.circle(gm, (int(scx), int(scy)), core, 1.0, -1)
                gm = cv2.GaussianBlur(gm, (0, 0), 18)
                gm = np.clip((gm - 0.3) * 5, 0, 1)[..., None]
                rr = np.sqrt((xx - scx) ** 2 + (yy - scy) ** 2) + 1
                ang = np.arctan2(yy - scy, xx - scx)
                tex = syrup.sample(ang * 90 + flow_noise((H, W), d, 3, 120) * 20, rr * 0.35 - 600 * d)
                cb = np.clip(1 - rr / 180, 0, 1)[..., None]
                tex = tex * (1 - cb) + cv2.GaussianBlur(tex, (0, 0), 12) * cb
                shade = (0.75 + 0.35 * np.clip(1 - rr / (core + 400), 0, 1))[..., None]
                fr = fr * (1 - gm) + tex * shade * gm
                # shards on top, flying out and growing as they come at the camera
                for s in shards:
                    sz = 1 + s['zv'] * d ** 1.3 * 2.2
                    cxx, cyy = s['c']
                    R = cv2.getRotationMatrix2D((float(cxx), float(cyy)), s['w'] * d, sz)
                    R[0, 2] += s['v'][0] * d * (0.6 + sz * 0.4)
                    R[1, 2] += s['v'][1] * d * (0.6 + sz * 0.4) + 900 * d * d
                    A = (np.vstack([Msc, [0, 0, 1]]) @ np.vstack([R, [0, 0, 1]]))[:2]
                    sm = cv2.warpAffine(s['m'], A, (W, H))
                    if sm.max() < 0.05:
                        continue
                    si = cv2.warpAffine(subj, A, (W, H)).astype(np.float32)
                    if sz > 2.5:                                        # close to the lens: motion blur
                        si = cv2.blur(si, (9, 9)); sm = cv2.blur(sm, (9, 9))
                    fr = fr * (1 - sm[..., None]) + si * 0.85 * sm[..., None]
            # rivets: bolt, spark flash, leak that keeps dripping (until the blast)
            for (t0, px, py, bolts) in pops:
                if t < t0 or t > split:
                    continue
                dt = t - t0
                p = to_scr((px, py))
                if dt < 0.12:
                    cv2.circle(fr, (int(p[0]), int(p[1])), int(30 - 150 * dt), (120, 220, 255), -1, cv2.LINE_AA)
                for vx, vy in bolts:
                    bx, by = p[0] + vx * dt, p[1] + vy * dt + 1600 * dt * dt
                    if 0 <= bx < W and 0 <= by < H:
                        cv2.line(fr, (int(bx), int(by)), (int(bx - vx * 0.03), int(by - vy * 0.03)), (40, 40, 45), 5, cv2.LINE_AA)
                        cv2.circle(fr, (int(bx), int(by)), 6, (70, 75, 80), -1, cv2.LINE_AA)
                drip = min(260, 160 * dt + 40)
                cv2.line(fr, (int(p[0]), int(p[1])), (int(p[0]), int(p[1] + drip)), MOL_MID.tolist(), 14, cv2.LINE_AA)
                cv2.circle(fr, (int(p[0]), int(p[1] + drip)), 10, MOL_MID.tolist(), -1, cv2.LINE_AA)
                cv2.line(fr, (int(p[0]) - 3, int(p[1])), (int(p[0]) - 3, int(p[1] + drip * 0.8)), MOL_LITE.tolist(), 2, cv2.LINE_AA)
            frame = grain(fr * vig, rng).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()


# ------------------------------------------------------------------ wave
def wave(still, out, cues):
    rng = np.random.default_rng(21)
    img = load(still)
    _, _, pa = split_layers(img)
    pm = (pa > 0.5).astype(np.uint8)
    npl, plab, pst, _ = cv2.connectedComponentsWithStats(pm)
    syrup = Syrup(img)
    secs = cues['secs']
    lens = cues['lens']                                   # seconds of syrup sliding off the lens at the start
    vp = (W / 2, H * 0.47)
    xs = np.arange(W, dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    drops = []
    vig = vignette()
    ff = writer(out)
    frame = None
    drip_x = np.sort(np.linspace(-20, W + 20, 26) + rng.normal(0, 8, 26))
    drip_v = rng.uniform(0.6, 1.4, 26)
    for i in range(int(secs * FPS)):
        t = i / FPS
        if i % STEP == 0:
            p = (t / secs) ** 1.7
            jx, jy = rng.normal(0, 1.2 + 12 * p * p, 2)
            z0 = 1.0 + 0.04 * t / secs
            Mz = np.float32([[z0, 0, W / 2 - z0 * img.shape[1] / 2 + jx], [0, z0, H / 2 - z0 * img.shape[0] / 2 + jy]])
            fr = cv2.warpAffine(img, Mz, (W, H), borderMode=cv2.BORDER_REFLECT).astype(np.float32)

            foot = vp[1] + 25 + (H * 1.2 - vp[1]) * p
            hgt = 50 + 2400 * p ** 1.55
            half = 110 + W * 1.25 * p
            e = np.clip((half - np.abs(xs - vp[0])) / (0.3 * half), 0, 1)
            edge = e * e * (3 - 2 * e)
            sc = 0.25 + 1.2 * p
            lobes = (np.sin(xs / (55 * sc + 10) + t * 4.0) * 0.35 + np.sin(xs / (120 * sc + 20) - t * 2.6) * 0.45
                     + np.sin(xs / (240 * sc + 30) + t * 1.3) * 0.6)
            crest = foot - hgt * edge * (1 + 0.12 * lobes)
            footl = foot + (np.sin(xs / 70 + t * 3) * 8 + np.sin(xs / 31 - t * 5) * 4) * (0.3 + p)
            body = ((yy > crest[None, :]) & (yy < footl[None, :]) & (edge[None, :] > 0.01)).astype(np.float32)
            body = cv2.GaussianBlur(body, (0, 0), 1.5 + 2 * (1 - p))

            span = np.maximum(footl - crest, 1)[None, :]
            v = np.clip((yy - crest[None, :]) / span, 0, 1)
            texscale = 1.0 / (1.3 + 2.8 * p)
            warp = flow_noise((H, W), t, 7, 160) * 10
            tu = xx * texscale + warp + v * 140 + np.sin(yy / 230 + t) * 40
            tv = (v ** 0.7) * 260 - t * 160 * (1.3 - v) + warp * 0.3
            tex = syrup.sample(tu, tv)
            lip = np.exp(-((v - 0.04) / 0.05) ** 2)
            curl = np.exp(-((v - 0.16) / 0.07) ** 2)
            occl = np.clip((v - 0.75) / 0.25, 0, 1)
            light = (1.0 + 0.45 * lip - 0.45 * curl - 0.35 * occl) * (0.75 + 0.25 * min(1, p * 3))
            tex = tex * light[..., None]
            blur = 2.5 * (1 - min(1, p * 2.2))
            if blur > 0.3:
                tex = cv2.GaussianBlur(tex, (0, 0), blur)
            sh = np.exp(-((yy - footl[None, :] - 18 * (0.3 + p)) / (16 * (0.3 + p))) ** 2) * (edge[None, :] > 0.01)
            fr = fr * (1 - 0.45 * sh[..., None])
            fr = fr * (1 - body[..., None]) + tex * body[..., None]

            front = np.zeros(img.shape[:2], np.float32)
            for c in range(1, npl):
                if (pst[c, 1] + pst[c, 3]) * z0 + Mz[1, 2] > foot + 10:
                    front[plab == c] = 1
            if front.any():
                fm = cv2.warpAffine(cv2.GaussianBlur(front, (0, 0), 1), Mz, (W, H))[..., None]
                fr = fr * (1 - fm) + cv2.warpAffine(img, Mz, (W, H)).astype(np.float32) * fm

            for _ in range(int(4 + 26 * p)):
                x = rng.uniform(vp[0] - half, vp[0] + half)
                xi = int(np.clip(x, 0, W - 1))
                if edge[xi] > 0.2:
                    drops.append([x, crest[xi], rng.normal(0, 90), rng.uniform(-600, -200) * (0.4 + p), rng.uniform(3, 7 + 22 * p)])
            keep = []
            for d in drops:
                ox, oy = d[0], d[1]
                d[0] += d[2] * STEP / FPS; d[1] += d[3] * STEP / FPS; d[3] += 2400 * STEP / FPS
                if d[1] < H + 60:
                    keep.append(d)
                    cv2.circle(fr, (int(d[0]), int(d[1])), int(d[4]), MOL_MID.tolist(), -1, cv2.LINE_AA)
                    cv2.circle(fr, (int(d[0] - d[4] * 0.35), int(d[1] - d[4] * 0.35)), max(1, int(d[4] * 0.28)), MOL_LITE.tolist(), -1, cv2.LINE_AA)
            drops = keep[-900:]

            if t < lens:
                q = t / lens
                lm = np.zeros((H, W), np.float32)
                for k2 in range(len(drip_x) - 1):
                    top = (q ** 1.6) * H * 1.3 * drip_v[k2]
                    cv2.rectangle(lm, (int(drip_x[k2]), int(top)), (int(drip_x[k2 + 1]) + 2, H), 1.0, -1)
                    cv2.circle(lm, (int((drip_x[k2] + drip_x[k2 + 1]) / 2), int(top)), int((drip_x[k2 + 1] - drip_x[k2]) * 0.6), 1.0, -1)
                lm = cv2.GaussianBlur(lm, (0, 0), 10)[..., None]
                lt = syrup.sample(xx * 0.8, yy * 0.5 - 900 * t) * 0.8
                fr = fr * (1 - lm) + lt * lm
            frame = grain(fr * vig, rng).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('shot', choices=['tank', 'wave'])
    ap.add_argument('still'); ap.add_argument('out')
    ap.add_argument('--cues', default='{}', help='JSON, e.g. {"rivets":[2.45,2.75],"bulge":3.9,"split":4.75,"secs":5.35}')
    a = ap.parse_args()
    c = {'tank': {'rivets': [2.45, 2.75, 3.05, 3.35, 3.65], 'bulge': 3.9, 'split': 4.75, 'secs': 5.35},
         'wave': {'secs': 5.07, 'lens': 0.55}}[a.shot]
    c.update(json.loads(a.cues))
    (tank if a.shot == 'tank' else wave)(a.still, a.out, c)
