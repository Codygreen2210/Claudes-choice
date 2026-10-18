#!/usr/bin/env python3
"""Molasses flood: two code-animated shots, built on the animate engine.

    python3 studio/animate/scenes/molasses.py tank  tank_still.webp  out.mp4
    python3 studio/animate/scenes/molasses.py wave  street_still.webp out.mp4

tank: push in, rivets pop off one by one (bolt, spark, leak), a crack runs down the
      middle, then the two halves peel apart and molasses bursts out.
wave: a glossy brown wave rises out of the far end of the street and rolls over
      the camera, droplets flying off the crest.
Timings are seconds and can be changed with --cues to match the voice.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from animate import FPS, H, STEP, W, ease, load, place, split_layers  # noqa: E402

MOL_DARK = np.array([6, 12, 22], np.float32)     # BGR
MOL_MID = np.array([16, 38, 74], np.float32)
MOL_LITE = np.array([110, 170, 225], np.float32)


def writer(out):
    return subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', out],
                            stdin=subprocess.PIPE)


_NOISE = {}


def _streaks(sx, sy, seed=5):
    key = (sx, sy, seed)
    if key not in _NOISE:
        r = np.random.default_rng(seed)
        n = cv2.GaussianBlur(r.normal(0, 1, (H * 2, W)).astype(np.float32), (0, 0), sigmaX=sx, sigmaY=sy)
        n2 = cv2.GaussianBlur(r.normal(0, 1, (H * 2, W)).astype(np.float32), (0, 0), sigmaX=sx * 4, sigmaY=sy * 3)
        n = n / n.std() + 0.8 * n2 / n2.std()
        _NOISE[key] = n / n.std()
    return _NOISE[key]


def molasses_tex(t, flow=(0, 1), scale=1.0, speed=420):
    """Full-frame glossy molasses: long streaks that slide in the flow direction (down = +1)."""
    n = _streaks(9 * scale, 26 * scale)
    off = int(speed * t * flow[1]) % H
    n = np.roll(n, off, axis=0)[:H]
    shade = np.clip(0.45 + 0.2 * n, 0, 1)
    col = MOL_DARK + (MOL_MID - MOL_DARK) * shade[..., None]
    ridge = np.exp(-((n - 2.0) / 0.12) ** 2)                      # thin glossy ridges, like light on syrup
    return col + (MOL_LITE - col) * ridge[..., None] * 0.85


def grain(frame, rng, amt=4):
    return np.clip(frame + rng.normal(0, amt, frame.shape), 0, 255)


def vignette():
    v = cv2.GaussianBlur(np.pad(np.ones((H - 400, W - 300), np.float32), ((200, 200), (150, 150))), (0, 0), 160)
    return (0.72 + 0.28 * v)[..., None]


# ------------------------------------------------------------------ tank
def tank(still, out, cues):
    rng = np.random.default_rng(11)
    img = load(still)
    back, subj, a = split_layers(img)
    m = (a > 0.5).astype(np.uint8)
    # keep the biggest blob: that is the tank, not the little people
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    tm = (lab == k).astype(np.float32)
    x0, y0, w0, h0 = stats[k, :4]
    cx = x0 + w0 // 2
    tm = cv2.GaussianBlur(tm, (0, 0), 1.2)
    other = np.clip(a - tm, 0, 1)                                    # people and small stuff stay put
    left = tm * (np.arange(img.shape[1])[None, :] < cx)
    right = tm * (np.arange(img.shape[1])[None, :] >= cx)
    # back plate without the tank (people kept)
    plate = subj * other[..., None] + back * (1 - other[..., None])

    # rivet pop points: on the tank's rivet bands, left and right faces
    pops = []
    for i, t0 in enumerate(cues['rivets']):
        px = cx + (rng.uniform(0.18, 0.42) * w0) * (-1 if i % 2 else 1)
        py = y0 + h0 * rng.uniform(0.2, 0.7)
        bolts = [(rng.uniform(-1, 1) * 900 + (300 if px > cx else -300), rng.uniform(-900, -300)) for _ in range(4)]
        pops.append((t0, px, py, bolts))
    crack_x = cx + rng.normal(0, 6, 40).cumsum() * 0.6
    crack_y = np.linspace(y0 + 10, y0 + h0, 40)

    secs, split = cues['secs'], cues['split']
    vig = vignette()
    ff = writer(out)
    frame = None
    nfr = int(secs * FPS)
    for i in range(nfr):
        t = i / FPS
        if i % STEP == 0:
            z = 1.0 + 0.07 * ease(min(1, t / split))
            jx, jy = rng.normal(0, 1.2, 2)
            if t > cues['rivets'][0]:
                k2 = 4 + (14 if t > split else 0) * np.exp(-(t - split) * 2.5) if t > split else 4
                jx += rng.normal(0, k2); jy += rng.normal(0, k2)
            ang = 0 if t < split else 22 * ease(min(1, (t - split) / 0.5))   # degrees each half falls open
            spread = 0 if t < split else 90 * ease(min(1, (t - split) / 0.5))
            base = place(plate, z * (1 + 0.45 * (z - 1)), jx * 0.5, jy * 0.5)
            fr = base.astype(np.float32)
            Msc = np.float32([[z, 0, W / 2 - z * img.shape[1] / 2 + jx], [0, z, H / 2 - z * img.shape[0] / 2 + jy]])
            pivot_y = y0 + h0
            # gush behind/between the halves
            if t > split:
                g = min(1, (t - split) / 0.7)
                gx, gy = cx, y0 + h0 * 0.45
                gm = np.zeros(img.shape[:2], np.float32)
                for j in range(70):
                    rj = np.random.default_rng(j)
                    born = rj.uniform(0, 0.5)
                    if t - split < born:
                        continue
                    d = t - split - born
                    vx = rj.normal(0, 1) * w0 * 0.9
                    vy = rj.uniform(-0.6, 0.3) * h0
                    bx = gx + vx * d
                    by = y0 + h0 * rj.uniform(0.15, 0.8) + vy * d + 1.4 * h0 * d * d
                    rad = int(w0 * (0.08 + 0.22 * min(1, d * 2.5)) * rj.uniform(0.6, 1.3))
                    by = min(by, pivot_y + 30 + d * 300)
                    cv2.circle(gm, (int(bx), int(by)), rad, 1.0, -1)
                spill = int(pivot_y - 20 - 260 * g)
                cv2.ellipse(gm, (int(gx), int(pivot_y + 40)), (int(w0 * (0.4 + 2.5 * g)), int(80 + 500 * g)), 0, 180, 360, 1.0, -1)
                cv2.rectangle(gm, (0, int(pivot_y + 40)), (img.shape[1], img.shape[0]), float(min(1, g * 1.6)), -1)
                gm = cv2.GaussianBlur(gm, (0, 0), 14)
                gm = np.clip((gm - 0.35) * 6, 0, 1)
                gm = cv2.warpAffine(cv2.GaussianBlur(gm, (0, 0), 6), Msc, (W, H))[..., None]
                fr = fr * (1 - gm) + molasses_tex(t, (0.0, 1.0), speed=700) * gm
            for half, sgn in ((left, -1), (right, 1)):
                px = cx + sgn * w0 * 0.5
                R = cv2.getRotationMatrix2D((float(px), float(pivot_y)), -sgn * ang, 1.0)
                R[0, 2] += sgn * spread
                R3 = np.vstack([R, [0, 0, 1]])
                A = np.vstack([Msc, [0, 0, 1]]) @ R3
                hl = cv2.warpAffine(subj, A[:2], (W, H), flags=cv2.INTER_LINEAR)
                hm = cv2.warpAffine(half, A[:2], (W, H))[..., None]
                fr = fr * (1 - hm) + hl * hm
            # crack running down the middle before the split
            if cues['crack'] <= t < split + 0.15:
                c = min(1, (t - cues['crack']) / (split - cues['crack']))
                kpts = int(2 + c * (len(crack_y) - 2))
                pts = np.c_[crack_x[:kpts], crack_y[:kpts]]
                pts = (np.c_[pts, np.ones(len(pts))] @ Msc.T).astype(np.int32)
                ov = fr.copy()
                cv2.polylines(ov, [pts], False, (MOL_MID * 1.3).tolist(), int(6 + 10 * c), cv2.LINE_AA)
                cv2.polylines(ov, [pts], False, (5, 8, 12), 3, cv2.LINE_AA)
                fr = ov
            # rivets: bolt, spark flash, leak that keeps dripping
            for (t0, px, py, bolts) in pops:
                if t < t0 or t > split + 0.1:
                    continue
                dt = t - t0
                p = np.array([px, py, 1.0]) @ Msc.T
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
    _, _, pa = split_layers(img)                       # people and props stay in front until the wave reaches them
    pm = (pa > 0.5).astype(np.uint8)
    npl, plab, pst, _ = cv2.connectedComponentsWithStats(pm)
    secs = cues['secs']
    vp = (W / 2, H * 0.47)                        # where the street disappears
    xs = np.arange(W, dtype=np.float32)
    drops = []
    vig = vignette()
    ff = writer(out)
    frame = None
    for i in range(int(secs * FPS)):
        t = i / FPS
        if i % STEP == 0:
            p = (t / secs) ** 1.8                                     # accelerates toward camera
            jx, jy = rng.normal(0, 1.2 + 10 * p * p, 2)
            base = place(img, 1.0 + 0.04 * t / secs, jx, jy).astype(np.float32)
            foot = vp[1] + 30 + (H * 1.15 - vp[1]) * p                # leading edge on the ground
            hgt = 60 + 2300 * p ** 1.6                                 # wave height on screen
            half = 120 + W * 1.2 * p                                   # how wide it spans
            wob = (np.sin(xs / 37 + t * 5) * 14 + np.sin(xs / 91 - t * 3) * 30 + np.sin(xs / 160 + t * 2) * 45) * (0.4 + 1.5 * p)
            e = np.clip((half - np.abs(xs - vp[0])) / (0.25 * half), 0, 1)
            edge = e * e * (3 - 2 * e)                                  # flat-topped wall with rounded ends
            crest = foot - hgt * edge + wob * edge
            footl = foot + wob * 0.3
            yy = np.arange(H, dtype=np.float32)[:, None]
            body = ((yy > crest[None, :]) & (yy < footl[None, :] + 4) & (edge[None, :] > 0)).astype(np.float32)
            body = cv2.GaussianBlur(body, (0, 0), 2)[..., None]
            tex = molasses_tex(t, (0.0, 1.0), scale=1.0, speed=500)
            # darker deep down, amber lit lip along the crest
            depth = np.clip((yy - crest[None, :]) / (hgt + 1), 0, 1)[..., None]
            tex = tex * (1.15 - 0.55 * depth)
            lip = np.exp(-((yy - crest[None, :] - 20 - 30 * p) / (14 + 40 * p)) ** 2)[..., None] * (edge[None, :, None] > 0)
            tex = tex + (np.array([40, 90, 160], np.float32) - tex) * lip * 0.85
            fr = base * (1 - body) + tex * body
            # anything whose feet are still in front of the wave front stays on top
            z0 = 1.0 + 0.04 * t / secs
            Mz = np.float32([[z0, 0, W / 2 - z0 * img.shape[1] / 2 + jx], [0, z0, H / 2 - z0 * img.shape[0] / 2 + jy]])
            front = np.zeros(img.shape[:2], np.float32)
            for c in range(1, npl):
                bot = (pst[c, 1] + pst[c, 3]) * z0 + Mz[1, 2]
                if bot > foot + 10:
                    front[plab == c] = 1
            if front.any():
                fm = cv2.warpAffine(cv2.GaussianBlur(front, (0, 0), 1), Mz, (W, H))[..., None]
                fp = cv2.warpAffine(img, Mz, (W, H)).astype(np.float32)
                fr = fr * (1 - fm) + fp * fm
            # curl: a dark overhang just under the lip
            curl = np.exp(-((yy - crest[None, :] - 60 - 40 * p) / (18 + 30 * p)) ** 2)[..., None] * body
            fr = fr * (1 - 0.6 * curl)
            # foam-free brown droplets thrown off the crest
            for _ in range(int(6 + 30 * p)):
                x = rng.uniform(vp[0] - half, vp[0] + half)
                xi = int(np.clip(x, 0, W - 1))
                if edge[xi] > 0.05:
                    drops.append([x, crest[xi], rng.normal(0, 120), rng.uniform(-700, -250) * (0.5 + p), rng.uniform(4, 9 + 20 * p)])
            keep = []
            for d in drops:
                d[0] += d[2] * STEP / FPS; d[1] += d[3] * STEP / FPS; d[3] += 2200 * STEP / FPS
                if d[1] < H + 50:
                    keep.append(d)
                    cv2.circle(fr, (int(d[0]), int(d[1])), int(d[4]), MOL_MID.tolist(), -1, cv2.LINE_AA)
                    cv2.circle(fr, (int(d[0] - d[4] * 0.3), int(d[1] - d[4] * 0.3)), max(1, int(d[4] * 0.3)), MOL_LITE.tolist(), -1, cv2.LINE_AA)
            drops = keep[-900:]
            frame = grain(fr * vig, rng).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('shot', choices=['tank', 'wave'])
    ap.add_argument('still'); ap.add_argument('out')
    ap.add_argument('--cues', default='{}', help='JSON, e.g. {"rivets":[2.45,2.75],"crack":3.8,"split":4.75,"secs":5.35}')
    a = ap.parse_args()
    c = {'tank': {'rivets': [2.45, 2.75, 3.05, 3.35, 3.65], 'crack': 3.8, 'split': 4.75, 'secs': 5.35},
         'wave': {'secs': 5.07}}[a.shot]
    c.update(json.loads(a.cues))
    (tank if a.shot == 'tank' else wave)(a.still, a.out, c)
