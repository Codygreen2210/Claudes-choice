#!/usr/bin/env python3
"""animate: turn one still into a short clay-style moving shot, on CPU.

    python3 studio/animate/animate.py still.webp out.mp4 --move tilt_up --fx snow --secs 5

How it works:
  1. cut the subject from the still (rembg) and paint over the hole to get a clean back plate
  2. move a virtual camera; the back plate moves less than the subject, so you get real depth
  3. add code-drawn weather/effects, stop-motion stepping (on twos), per-frame clay jitter, grain

Moves: push_in, pull_out, tilt_up, tilt_down, pan_left, pan_right, drift, shake
Effects (comma list): snow, rain, dust, shake, flicker, none
"""
from __future__ import annotations

import argparse
import subprocess

import cv2
import numpy as np

W, H = 1080, 1920
FPS = 24
STEP = 2            # hold each drawn frame twice: stop-motion "on twos"


def load(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        from PIL import Image
        img = cv2.cvtColor(np.array(Image.open(path).convert('RGB')), cv2.COLOR_RGB2BGR)
    # cover-fit into 1080x1920 with 12% overscan so the camera has room to move
    s = max(W / img.shape[1], H / img.shape[0]) * 1.12
    return cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)


def split_layers(img: np.ndarray):
    """Return (back plate, subject BGR, subject alpha 0..1)."""
    from rembg import new_session, remove
    rgba = remove(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), session=new_session('u2net'))
    a = rgba[..., 3].astype(np.float32) / 255
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    hole = (cv2.dilate((a > 0.1).astype(np.uint8), np.ones((25, 25), np.uint8)) * 255)
    small = 0.35   # inpaint at low res, it is slow at full size
    bs = cv2.inpaint(cv2.resize(img, None, fx=small, fy=small), cv2.resize(hole, None, fx=small, fy=small), 9, cv2.INPAINT_TELEA)
    back = cv2.resize(bs, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    back = np.where(hole[..., None] > 0, cv2.GaussianBlur(back, (0, 0), 2), img)
    return back, img, a


def ease(t):
    return t * t * (3 - 2 * t)


def camera(move: str, t: float):
    """t in 0..1 -> (zoom, dx, dy) in output pixels for the subject layer."""
    e = ease(t)
    return {
        'push_in':   (1.00 + 0.10 * e, 0, 0),
        'pull_out':  (1.10 - 0.10 * e, 0, 0),
        'tilt_up':   (1.03, 0, -110 + 220 * e),
        'tilt_down': (1.03, 0, 110 - 220 * e),
        'pan_left':  (1.04, 70 - 140 * e, 0),
        'pan_right': (1.04, -70 + 140 * e, 0),
        'drift':     (1.02 + 0.03 * e, -25 + 50 * e, 10 - 20 * e),
        'shake':     (1.05, 0, 0),
    }[move]


def place(layer: np.ndarray, zoom: float, dx: float, dy: float, border=cv2.BORDER_REFLECT) -> np.ndarray:
    h, w = layer.shape[:2]
    M = np.float32([[zoom, 0, W / 2 - zoom * w / 2 + dx], [0, zoom, H / 2 - zoom * h / 2 + dy]])
    return cv2.warpAffine(layer, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)


class Particles:
    def __init__(self, kind: str, rng):
        n = {'snow': 260, 'rain': 420, 'dust': 140}[kind]
        self.kind, self.rng = kind, rng
        self.p = np.c_[rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(0.4, 1.0, n)]

    def draw(self, frame, dt):
        x, y, d = self.p.T
        if self.kind == 'snow':
            y += 90 * d * dt; x += 25 * np.sin(y / 60 + d * 9) * dt
        elif self.kind == 'rain':
            y += 1500 * d * dt; x -= 200 * d * dt
        else:
            y -= 12 * d * dt; x += 18 * np.sin(y / 80 + d * 7) * dt
        y %= H; x %= W
        over = frame.copy()
        for xi, yi, di in zip(x.astype(int), y.astype(int), d):
            if self.kind == 'snow':
                cv2.circle(over, (xi, yi), int(2 + 4 * di), (235, 235, 240), -1, cv2.LINE_AA)
            elif self.kind == 'rain':
                cv2.line(over, (xi, yi), (xi - int(6 * di), yi + int(30 * di)), (200, 205, 210), 1, cv2.LINE_AA)
            else:
                cv2.circle(over, (xi, yi), int(1 + 2 * di), (170, 190, 210), -1, cv2.LINE_AA)
        a = {'snow': 0.75, 'rain': 0.35, 'dust': 0.4}[self.kind]
        return cv2.addWeighted(over, a, frame, 1 - a, 0)


def render(still, out, move='push_in', fx='none', secs=5.0, seed=7, depth=0.55):
    rng = np.random.default_rng(seed)
    img = load(still)
    back, subj, a = split_layers(img)
    fxs = [f for f in fx.split(',') if f and f != 'none']
    parts = [Particles(k, rng) for k in fxs if k in ('snow', 'rain', 'dust')]
    vign = cv2.GaussianBlur(np.pad(np.ones((H - 400, W - 300), np.float32), ((200, 200), (150, 150))), (0, 0), 160)
    vign = (0.72 + 0.28 * vign)[..., None]
    n = int(secs * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', out],
                          stdin=subprocess.PIPE)
    frame = None
    for i in range(n):
        if i % STEP == 0:
            t = i / max(1, n - 1)
            z, dx, dy = camera(move, t)
            jx, jy = rng.normal(0, 1.2, 2)                      # clay jitter: hand-moved camera
            if move == 'shake' or 'shake' in fxs:
                k = 1 - t * 0.6
                jx += rng.normal(0, 9 * k); jy += rng.normal(0, 9 * k)
            # back plate moves less (it is further away)
            bz = 1 + (z - 1) * depth
            b = place(back, bz, dx * depth + jx * 0.5, dy * depth + jy * 0.5)
            # subject breathes a touch so it never looks frozen
            sz = z * (1 + 0.004 * np.sin(i / FPS * 2 * np.pi * 0.6))
            s = place(subj, sz, dx + jx, dy + jy)
            al = place(a, sz, dx + jx, dy + jy, border=cv2.BORDER_CONSTANT)[..., None]
            frame = (s * al + b * (1 - al))
            frame = frame * vign
            if 'flicker' in fxs:
                frame *= 1 + rng.normal(0, 0.025)
            frame = np.clip(frame + rng.normal(0, 4, frame.shape), 0, 255).astype(np.uint8)  # grain
            for p in parts:
                frame = p.draw(frame, STEP / FPS)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('still'); ap.add_argument('out')
    ap.add_argument('--move', default='push_in')
    ap.add_argument('--fx', default='none')
    ap.add_argument('--secs', type=float, default=5.0)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--depth', type=float, default=0.55, help='how much less the back plate moves (0 = locked, 1 = same)')
    a = ap.parse_args()
    render(a.still, a.out, a.move, a.fx, a.secs, a.seed, a.depth)
