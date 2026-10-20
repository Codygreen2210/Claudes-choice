import os
"""Shared kit for the narrated toon Shorts.

Picture: run(BEATS, times.json, lines.json, out.mp4) renders beats timed to the narration.
  BEATS[i] is fn(lt, dur, T) -> Canvas. The LAST beat must be the opening beat run up to its own
  start (pass loop_fn=BEATS[0]); it is drawn as BEATS[0](T - total, ...) so the final frame is the
  frame just before frame one: seamless loop. Every Short opens mid-action (house rule).
Sound: Mix(times) gives put(), circular folding, voice ducking and a fixed-gain finish.
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import *          # noqa: F401,F403
import common

for _f in ('/usr/share/fonts/opentype/inter/Inter-Black.otf', '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'):
    if os.path.exists(_f):
        common.FONT = _f
        break

# ------------------------------------------------------------------ the house look: soft 3D
# Smooth round shading (shapes read like soft clay), a gloss highlight, warm bounce light, soft shadows,
# then a finish pass on every frame: light bloom on the bright bits and a fixed paper grain.
import fast as _fast
LOOK = os.environ.get('TOON_LOOK', 'soft3d')
if LOOK == 'soft3d':
    _fast.lib.set_style(1, 30.0); _fast.SOFT[0] = True

_GRAIN = None


def finish_look(cv):
    global _GRAIN
    if LOOK != 'soft3d':
        return
    img = cv.img
    if _GRAIN is None:                       # fixed paper-fibre grain: same every frame, so it never crawls
        g = np.random.default_rng(11).standard_normal((H // 2, W // 2)).astype(np.float32)
        im = Image.fromarray(np.uint8(np.clip(128 + g * 40, 0, 255))).resize((W, H), Image.BICUBIC)
        _GRAIN = (np.asarray(im, np.float32) / 255 - 0.5)[..., None] * 0.035
    small = Image.fromarray(np.uint8(np.clip(img, 0, 1) * 255)).resize((W // 8, H // 8), Image.BILINEAR)
    b = np.asarray(small, np.float32) / 255
    b = np.clip(b - 0.72, 0, 1) * 2.2
    bl = Image.fromarray(np.uint8(np.clip(b, 0, 1) * 255)).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
    img += np.asarray(bl, np.float32) / 255 * 0.22
    img += _GRAIN


BLUE = ramp('#3d7fd8', '#2a559a', '#7fb4ff')
ORANGE = ramp('#ff8a2a', '#c4561a', '#ffbf7a')
YELLOW = ramp('#ffd23f', '#d09a10', '#fff08a')
GREEN = ramp('#3fbf6a', '#25804a', '#7fe8a0')
PINK = ramp('#ff8f9a', '#d0566a', '#ffc4cc')
DARK = ramp('#2b2f38', '#191c22', '#454b57')
STEEL = ramp('#a7b0ba', '#6d7782', '#dfe6ec')
WATER = ramp('#3fa9e0', '#2378b0', '#8fd6ff')


# ------------------------------------------------------------------ small drawing helpers
def pop(t, t0, dur=0.25):
    """0 before t0, then a scale that overshoots and settles at 1."""
    k = np.clip((t - t0) / dur, 0, 1)
    if k <= 0:
        return 0
    return 1 + 0.25 * np.sin(k * np.pi) * (1 - k) * 3 if k < 1 else 1



def arrows(cv, pairs, col=(255, 255, 255), w=12):
    c = flat(np.array(col, np.float32) / 255.0)
    for a, b in pairs:
        line(cv, [a, b], w, c, ow=3)
        d = np.array(b, float) - np.array(a, float); d /= (np.linalg.norm(d) + 1e-6); n = np.array([-d[1], d[0]])
        tip = np.array(b, float)
        line(cv, [tuple(tip - d * 36 + n * 24), tuple(tip), tuple(tip - d * 36 - n * 24)], w, c, ow=3)


def thermo(cv, x, y, val, lo=70, hi=130, h=700, label_=True, unit='°F'):
    """Big thermometer, val in degrees, fills red."""
    k = np.clip((val - lo) / (hi - lo), 0, 1)
    box(cv, x, y, 60, h / 2 + 30, ramp('#f4f1ea'), r=60)
    disc(cv, x, y + h / 2 + 30, 95, ramp('#f4f1ea'))
    disc(cv, x, y + h / 2 + 30, 72, ramp('#e2483d'))
    top = y + h / 2 - k * h
    if k > 0.01:
        box(cv, x, (top + y + h / 2 + 30) / 2, 32, (y + h / 2 + 30 - top) / 2, ramp('#e2483d'), r=30, ow=0)
    if label_:
        label(cv, f'{int(val)}{unit}', x, y - h / 2 - 110, 84, (255, 236, 80))


def meter(cv, x, y, w, k, col, title, a=1.0):
    """Horizontal bar meter with a title, k in 0..1."""
    box(cv, x, y, w / 2 + 10, 46, DARK, r=30, alpha=a)
    if k > 0.01:
        box(cv, x - w / 2 + w * k / 2, y, w * k / 2, 34, col, r=24, ow=0, alpha=a)
    label(cv, title, x, y - 90, 54, (255, 255, 255), a=a)


def heart_icon(cv, x, y, s, beat=0.0):
    sc = s * (1 + 0.12 * beat)
    cv.shape(heart(x, y, 200 * sc), (x - 130 * sc, y - 130 * sc, x + 130 * sc, y + 130 * sc), ramp('#e2483d'))


def brain(cv, x, y, s, hot=0.0):
    col = ramp('#f6a5b4', '#d0708a', '#ffd0da')
    blobs = [circle(x + dx * s, y + dy * s, r * s) for dx, dy, r in
             ((-110, -20, 110), (0, -60, 125), (110, -20, 110), (-60, 60, 100), (70, 60, 100))]
    cv.shape(smooth(40 * s, *blobs), (x - 230 * s, y - 190 * s, x + 230 * s, y + 170 * s), col,
             tint=('#ff3a2a', float(hot)) if hot > 0 else None)
    for k in range(5):
        pts = [(x + (-170 + k * 80 + 30 * np.sin(u * 6 + k)) * s, y + (-120 + u * 240) * s) for u in np.linspace(0, 1, 8)]
        line(cv, pts, 6 * s, flat(hexc('#c0607a')))


def rewind(cv, T, k):
    """Rewind look for k in 0..1 (1 = full): desaturate, sideways streaks, label."""
    if k <= 0:
        return
    g = cv.img.mean(2, keepdims=True)
    cv.img = np.ascontiguousarray(cv.img * (1 - 0.6 * k) + g * 0.6 * k, dtype=np.float32)
    speed_lines(cv, T, k, vertical=False)
    label(cv, 'REWIND', cv.cx, cv.cy + 820 / cv.zoom, 60 / cv.zoom, (255, 255, 255), a=k)


def caption(cv, txt, k, words_at_once=2):
    """His style: 1-2 big words at a time, centred low, following the voice."""
    words = txt.split()
    if not words:
        return
    k = float(np.clip(k, 0, 0.999))
    i = int(k * len(words))
    j0 = (i // words_at_once) * words_at_once
    shown = ' '.join(words[j0:j0 + words_at_once])
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    size = 104
    f = ImageFont.truetype(common.FONT, size)
    while d.textlength(shown, font=f) > W - 120 and size > 60:
        size -= 6; f = ImageFont.truetype(common.FONT, size)
    tw = d.textlength(shown, font=f)
    d.text(((W - tw) / 2, H - 620), shown, font=f, fill=(255, 255, 255, 255), stroke_width=12, stroke_fill=(20, 14, 26, 255))
    cv.overlay(im)


def sky_bg(cv, ground=None, gcol='#5fbf4a'):
    """His look: clean bright sky, optional flat green ground."""
    cv.background('#3fa2ee', '#bfe6ff', vignette=0.18)
    if ground is not None:
        box(cv, cv.cx, ground + 1000, 1600, 1000, ramp(gcol), r=0, ow=0, shadow=0)


# ------------------------------------------------------------------ a whole hand (palm toward us, fingers up)
NAIL = ramp('#ffd8d2', '#e0a49a', '#fff2ee')
BONEC = ramp('#f4ecd8', '#cbbf9e', '#ffffff')
FINGERS = (  # name, base x, length, radius, lean (deg)
    ('index', -110, 240, 39, -9), ('middle', -37, 268, 40, -2), ('ring', 37, 246, 38, 5), ('pinky', 107, 196, 34, 13))


def hand(cv, x, y, s=1.0, wr=0.0, spread=1.0, xray=0.0, vessels=0.0, nerve=None, skin=None, arm=True, tint=None):
    """Right hand seen palm-on, wrist at (x, y). wr: wrinkles 0..1, a number or a dict per finger
    ('index', 'middle', 'ring', 'pinky', 'thumb'). nerve: a finger name drawn with a cut nerve (stays smooth).
    Returns tip positions by finger name."""
    skin = SKIN if skin is None else skin
    P = lambda px, py: (x + px * s, y + py * s)
    parts, tips, segs = [], {}, {}
    palm = rbox(*P(0, -255), 160 * s, 165 * s, 95 * s)
    parts.append(palm)
    if arm:
        parts.append(capsule(*P(0, -120), *P(0, 700), 118 * s, 128 * s))
    for name, bx, L, r, lean in FINGERS:
        a = np.radians(lean * spread)
        b = P(bx, -385)
        t = (b[0] + np.sin(a) * L * s, b[1] - np.cos(a) * L * s)
        parts.append(capsule(b[0], b[1], t[0], t[1], r * s, r * s * 0.9))
        tips[name] = t; segs[name] = (b, t, r * s, a)
    a = np.radians(-52 - 10 * (spread - 1))
    b = P(-140, -215); L = 200
    t = (b[0] + np.sin(a) * L * s, b[1] - np.cos(a) * L * s)
    parts.append(capsule(b[0], b[1], t[0], t[1], 42 * s, 36 * s))
    tips['thumb'] = t; segs['thumb'] = (b, t, 40 * s, a)
    f = smooth(26 * s, *parts)
    bb = (x - 330 * s, y - 720 * s, x + 330 * s, y + (720 if arm else 40) * s)
    cv.shape(f, bb, skin, alpha=1 - 0.55 * xray, tint=tint)
    for name, bx, L, r, lean in FINGERS:                     # knuckle creases
        b, t, rr, a = segs[name]
        for u in (0.36, 0.66):
            cx, cy = b[0] + (t[0] - b[0]) * u, b[1] + (t[1] - b[1]) * u
            ca, sa = np.cos(a), np.sin(a)
            line(cv, [(cx - ca * rr * 0.45, cy - sa * rr * 0.45), (cx + ca * rr * 0.45, cy + sa * rr * 0.45)], 3.5 * s,
                 flat(hexc('#c98a6e')), a=0.55 * (1 - xray))
    if xray > 0:
        for name, (b, t, rr, a) in segs.items():
            n = 3 if name != 'thumb' else 2
            for k in range(n):
                u0, u1 = k / n + 0.03, (k + 1) / n - 0.04
                A = (b[0] + (t[0] - b[0]) * u0, b[1] + (t[1] - b[1]) * u0)
                B = (b[0] + (t[0] - b[0]) * u1, b[1] + (t[1] - b[1]) * u1)
                cv.shape(capsule(A[0], A[1], B[0], B[1], rr * 0.42, rr * 0.36), bbox_of([A, B], rr), BONEC, ow=3, alpha=xray)
    if vessels > 0:
        for name, (b, t, rr, a) in segs.items():
            if name == 'thumb':
                continue
            ww = rr * 0.36 * (1 - 0.65 * vessels)
            for side in (-1, 1):
                off = (np.cos(a) * rr * 0.45 * side, np.sin(a) * rr * 0.45 * side)
                line(cv, [(b[0] + off[0], b[1] + off[1] + 120 * s), (t[0] + off[0] * 0.6, t[1] + off[1] * 0.6 + rr * 0.5)], ww,
                     ramp('#d8343a', '#9a1f24', '#ff6a6a'), ow=2.5, flat=False)
    if nerve:
        b, t, rr, a = segs[nerve]
        line(cv, [(b[0], b[1] + 200 * s), (t[0], t[1] + rr * 0.6)], 9 * s, flat(hexc('#ffd23f')), ow=2.5)
        cx, cy = b[0] + (t[0] - b[0]) * 0.1, b[1] + (t[1] - b[1]) * 0.1 + 60 * s
        for dd in (-1, 1):
            line(cv, [(cx - 34 * s, cy - 28 * s * dd), (cx + 34 * s, cy + 28 * s * dd)], 11 * s, flat(hexc('#e2483d')), ow=3)
    for name, (b, t, rr, a) in segs.items():                 # nails and the wrinkly pads
        ca, sa = np.cos(a), np.sin(a)
        if xray < 0.9 and name != 'thumb':
            nx, ny = t[0] - sa * (-rr * 0.35), t[1] + ca * (-rr * 0.35) + rr * 0.15
            cv.shape(rotell(nx, ny, rr * 0.55, rr * 0.62, np.degrees(a)), (nx - rr, ny - rr, nx + rr, ny + rr), NAIL, ow=2.5,
                     alpha=0.9 * (1 - xray), shadow=0)
        w = wr.get(name, 0.0) if isinstance(wr, dict) else wr
        if name == nerve:
            w = 0.0
        if w > 0:
            Lf = np.hypot(t[0] - b[0], t[1] - b[1])
            for k in range(5):
                u = 1 - (0.07 + k * 0.07) * 260 * s / Lf
                cx, cy = b[0] + (t[0] - b[0]) * u, b[1] + (t[1] - b[1]) * u
                pts = []
                for q in np.linspace(-0.82, 0.82, 9):
                    wob = rr * 0.11 * w * np.sin(q * 9 + k * 1.7 + len(name))
                    pts.append((cx + ca * rr * q - sa * wob, cy + sa * rr * q + ca * wob))
                line(cv, pts, 3.2 * s + 1.5, flat(hexc('#b8705a')), a=min(1, w * 1.3) * (1 - xray) * 0.85)
    return tips


# ------------------------------------------------------------------ Blip, the sidekick
# A little round buddy in the bottom corner of every Short. He reacts to each line: lines.json can set
# "pal": happy | shock | gross | think | wink | hide (default happy).
BLIP = False             # sidekick off (Cody's call); the drawing stays here in case
PAL_BODY = ramp('#46d0b4', '#1f8f7a', '#9af2de')


def blip(cv, T, mood='happy', since=1.0, sx=None, sy=None, size=1.0):
    if mood == 'hide':
        return
    z = cv.zoom
    sx = W - 165 if sx is None else sx
    sy = H - 270 if sy is None else sy
    k = min(since / 0.25, 1.0)                                  # reacts with a little squash-and-pop when the line starts
    pop_ = 1 + 0.18 * np.sin(np.pi * k) * (1 - k) * 2
    bob = 10 * np.sin(T * 3.1)
    if mood == 'shock':
        bob -= 26 * np.sin(np.pi * k)
    wx = lambda px: (px - W / 2) / z + cv.cx
    wy = lambda py: (py - H / 2) / z + cv.cy
    r = 82 * size * pop_ / z
    x, y = wx(sx), wy(sy + bob)
    sq = 1 + 0.06 * np.sin(T * 6.2)
    line(cv, [(x + 10 / z, y - r * 0.9), (x + 30 / z, y - r * 1.45)], 9 / z, DARK, ow=2)          # antenna
    disc(cv, x + 32 / z, y - r * 1.5, 16 / z * size, ORANGE, ow=3)
    cv.shape(rotell(x, y, r * sq, r / sq, 0), (x - r * 1.2, y - r * 1.2, x + r * 1.2, y + r * 1.2), PAL_BODY, ow=5)
    for d in (-1, 1):                                           # little arms
        if mood == 'shock':
            pts = [(x + d * r * 0.85, y), (x + d * r * 1.35, y - r * 0.6)]
        elif mood == 'think' and d == 1:
            pts = [(x + r * 0.85, y + r * 0.1), (x + r * 0.35, y + r * 0.55)]
        else:
            pts = [(x + d * r * 0.85, y + r * 0.1), (x + d * r * 1.25, y + r * 0.45 + 8 / z * np.sin(T * 4 + d))]
        line(cv, pts, 14 / z * size, PAL_BODY, ow=3)
    blink = (T % 3.7) < 0.12
    ey = y - r * 0.12
    for d in (-1, 1):
        ex = x + d * r * 0.36
        if blink or (mood == 'wink' and d == 1):
            line(cv, [(ex - r * 0.16, ey), (ex + r * 0.16, ey)], 7 / z, DARK, ow=0)
            continue
        er = r * (0.27 if mood == 'shock' else 0.22)
        disc(cv, ex, ey, er, ramp('#ffffff'), ow=4, shadow=0)
        lx = {'think': (0.35, -0.45), 'gross': (0, 0.3)}.get(mood, (0.15, 0.1))
        disc(cv, ex + er * lx[0] * 0.5, ey + er * lx[1] * 0.5, er * 0.5, DARK, ow=0, shadow=0)
        disc(cv, ex + er * 0.05, ey - er * 0.2, er * 0.15, ramp('#ffffff'), ow=0, shadow=0, flat=True)
    my = y + r * 0.42
    if mood == 'shock':
        cv.shape(rotell(x, my, r * 0.17, r * 0.22, 0), (x - r * 0.3, my - r * 0.3, x + r * 0.3, my + r * 0.3), ramp('#5a1f2a'), ow=3, shadow=0)
    elif mood == 'gross':
        line(cv, [(x - r * 0.3, my), (x - r * 0.1, my - r * 0.08), (x + r * 0.1, my + r * 0.04), (x + r * 0.3, my - r * 0.04)], 7 / z, DARK, ow=0)
    elif mood == 'think':
        line(cv, [(x - r * 0.18, my), (x + r * 0.18, my - r * 0.05)], 7 / z, DARK, ow=0)
    else:
        line(cv, [(x - r * 0.28, my - r * 0.06), (x - r * 0.12, my + r * 0.1), (x + r * 0.12, my + r * 0.1), (x + r * 0.28, my - r * 0.06)], 8 / z, DARK, ow=0)
    if mood in ('happy', 'wink'):
        for d in (-1, 1):
            disc(cv, x + d * r * 0.62, y + r * 0.2, r * 0.12, ramp('#ff8f9a'), ow=0, shadow=0, flat=True, alpha=0.6)


# ------------------------------------------------------------------ the paper fold (scene change)
# The old picture folds away like a page from the right edge, showing its pale paper back,
# and the new picture is underneath. Ties to the channel name: History Unfoldz.
FOLD = 0.42
_PAPER = None


def paper_fold(new_img, old_img, k):
    global _PAPER
    if _PAPER is None:
        g = np.random.default_rng(5).standard_normal((H // 3, W // 3)).astype(np.float32)
        im = Image.fromarray(np.uint8(np.clip(128 + g * 30, 0, 255))).resize((W, H), Image.BICUBIC)
        _PAPER = np.array([0.96, 0.93, 0.86], np.float32) + (np.asarray(im, np.float32) / 255 - 0.5)[..., None] * 0.06
    e = k * k * (3 - 2 * k)
    xf = W * (1 - e) + 60 * np.sin(np.pi * e)                  # the fold line sweeps right to left
    xs = np.arange(W, dtype=np.float32)
    out = new_img.copy()
    old_side = xs < xf
    out[:, old_side] = old_img[:, old_side]
    flap0 = max(0.0, 2 * xf - W)                               # the folded-over part, lying on top
    fl = (xs >= flap0) & (xs < xf)
    if fl.any():
        u = (xf - xs[fl]) / max(W - xf, 1)                     # 0 at the crease, 1 at the old right edge
        shade = (0.78 + 0.22 * np.sin(np.clip(u, 0, 1) * np.pi * 0.5))[None, :, None]
        out[:, fl] = _PAPER[:, fl] * shade
        edge = np.exp(-(xs[fl] - flap0) / 6.0)[None, :, None] * 0.35   # thin dark edge on the flap
        out[:, fl] *= 1 - edge
    sh = (xs >= xf) & (xs < xf + 90)                            # soft shadow under the crease
    if sh.any():
        out[:, sh] *= (1 - 0.35 * np.exp(-(xs[sh] - xf) / 30.0))[None, :, None]
    cr = (xs < xf) & (xs > xf - 40)                             # crease highlight on the old page
    if cr.any():
        out[:, cr] *= (1 - 0.25 * np.exp(-(xf - xs[cr]) / 12.0))[None, :, None]
    return out


# ------------------------------------------------------------------ camera moves on the middle beats
# A slow push-in across each beat, plus a quick punch-in every ~3.5 s, drifting a different way each beat,
# so no scene ever sits still. Never on the opening beat or the loop beat (keeps the seam clean).
MOVES = False
PUNCH = 3.5


def camera_move(cv, lt, d, i):
    import cv2
    k = int(lt // PUNCH)
    u = min((lt - k * PUNCH) / 0.18, 1.0)
    u = u * u * (3 - 2 * u)
    z = min(1.0 + 0.04 * lt / max(d, 0.1) + 0.035 * (k - 1 + u if k else 0), 1.09)
    ang = i * 2.1
    px = np.cos(ang) * 40 * lt / max(d, 0.1)
    py = abs(np.sin(ang)) * 30 * lt / max(d, 0.1)
    if z <= 1.0005 and abs(px) < 0.5 and abs(py) < 0.5:
        return
    M = np.float32([[z, 0, (1 - z) * W / 2 + px], [0, z, (1 - z) * H * 0.3 + py]])   # zoom about a point high up, so top text stays on screen
    cv.img = np.ascontiguousarray(cv2.warpAffine(cv.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))


# ------------------------------------------------------------------ render
def _beat_frame(i, T, lt, d, TM, LINES, BEATS):
    import common as _c
    n = len(TM['starts'])
    total = TM['total']
    _c.HOOK_NOW[0] = (i == 0)
    if i == n - 1:
        cv = BEATS[0](T - total, TM['durs'][0], T - total)     # the opening, on its own clock, just before frame one
    else:
        cv = BEATS[i](lt, d, T)
    _c.HOOK_NOW[0] = False
    finish_look(cv)
    if MOVES and 0 < i < n - 1:
        camera_move(cv, lt, d, i)
    if BLIP:
        blip(cv, T, LINES[i].get('pal', 'happy'), lt)
    v0, v1 = TM['voice'][i]
    caption(cv, LINES[i]['text'], (T - v0) / max(v1 - v0, 0.3) + 0.05)
    return cv


# ------------------------------------------------------------------ the call to action before the loop
# A YouTube-style SUBSCRIBE button pops in near the end, a finger taps it, it flips to SUBSCRIBED with a bell
# shake, and it is gone before the last frame so the loop seam stays clean. The sound (tap + ding) is added in Mix.
CTA = True
MUSIC_DROP = 10.0                                            # extra dB the music sits under the voice (Zack D style)
CTA_START, CTA_END, CTA_TAP = 2.8, 0.4, 0.75          # seconds before the end; tap is seconds after it appears


def cta(cv, T, total):
    t = T - (total - CTA_START)
    life = CTA_START - CTA_END
    if not CTA or t < 0 or t > life:
        return
    from PIL import ImageDraw as _D, ImageFont as _F
    k_in = min(t / 0.22, 1.0)
    sc = 0.5 + 0.5 * ease(k_in) + 0.12 * np.sin(np.pi * k_in) * (1 - k_in)
    a = min(1.0, (life - t) / 0.25)
    done = t > CTA_TAP
    press = 1 - 0.08 * max(0.0, 1 - abs(t - CTA_TAP) / 0.12)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = _D.Draw(im)
    bw, bh = 640 * sc * press, 150 * sc * press
    cx, cy = W / 2, H * 0.84                                   # low, under the captions, clear of the hook words
    col = (40, 40, 46) if done else (230, 33, 23)
    d.rounded_rectangle([cx - bw / 2 + 8, cy - bh / 2 + 12, cx + bw / 2 + 8, cy + bh / 2 + 12], radius=bh / 2, fill=(0, 0, 0, int(90 * a)))
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=bh / 2, fill=col + (int(255 * a),),
                        outline=(20, 14, 26, int(255 * a)), width=8)
    txt = 'SUBSCRIBED' if done else 'SUBSCRIBE'
    f = _F.truetype(common.FONT, int(72 * sc * press))
    tw = d.textlength(txt, font=f)
    tx = cx - tw / 2 + (30 * sc if done else 0)
    d.text((tx, cy - 46 * sc * press), txt, font=f, fill=(255, 255, 255, int(255 * a)))
    if done:                                                    # little bell, shaking just after the tap
        sh = 14 * np.sin((t - CTA_TAP) * 40) * max(0.0, 1 - (t - CTA_TAP) / 0.6)
        bx, by = cx - tw / 2 - 30 * sc + sh, cy
        d.pieslice([bx - 34 * sc, by - 40 * sc, bx + 34 * sc, by + 30 * sc], 180, 360, fill=(255, 210, 63, int(255 * a)))
        d.rectangle([bx - 34 * sc, by - 6 * sc, bx + 34 * sc, by + 22 * sc], fill=(255, 210, 63, int(255 * a)))
        d.ellipse([bx - 10 * sc, by + 18 * sc, bx + 10 * sc, by + 38 * sc], fill=(255, 210, 63, int(255 * a)))
    if t < CTA_TAP + 0.35:                                       # the finger coming in to tap
        u = ease(min(1.0, t / CTA_TAP))
        fx, fy = cx + 380 - 260 * u, cy + 230 - 150 * u
        r = 46 * (1 - 0.15 * max(0.0, 1 - abs(t - CTA_TAP) / 0.12))
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(255, 255, 255, int(235 * a)), outline=(20, 14, 26, int(255 * a)), width=7)
        if abs(t - CTA_TAP) < 0.18:
            rr = 60 + 300 * (t - CTA_TAP + 0.18)
            d.ellipse([fx - rr, fy - rr, fx + rr, fy + rr], outline=(255, 255, 255, int(160 * a * (1 - abs(t - CTA_TAP) / 0.18))), width=6)
    cv.overlay(im)


def frame(T, TM, LINES, BEATS):
    n = len(TM['starts'])
    for i, (t0, d) in enumerate(zip(TM['starts'], TM['durs'])):
        if t0 <= T < t0 + d or i == n - 1:
            lt = T - t0
            cv = _beat_frame(i, T, lt, d, TM, LINES, BEATS)
            if 0 < i < n - 1 and lt < FOLD and LOOK == 'soft3d':   # never across the loop seam
                p0, pd = TM['starts'][i - 1], TM['durs'][i - 1]
                old = _beat_frame(i - 1, t0 - 1e-3, pd - 1e-3, pd, TM, LINES, BEATS)
                cv.img = paper_fold(cv.img, old.img, lt / FOLD)
            elif 0 < i < n - 1 and lt < 0.08:
                cv.flash('#ffffff', 0.25 * (1 - lt / 0.08))
            cta(cv, T, TM['total'])
            return cv


def run(BEATS):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('times'); ap.add_argument('lines'); ap.add_argument('out')
    ap.add_argument('--cover')
    ap.add_argument('--still', type=float); ap.add_argument('--sheet', action='store_true')
    a = ap.parse_args()
    TM = json.load(open(a.times)); LINES = json.load(open(a.lines))
    assert len(BEATS) == len(LINES) - 1, f'{len(BEATS)} beats for {len(LINES)} lines (last line reuses beat 0)'
    if a.sheet:                                   # one still per beat, for checking
        ims = []
        for t0, d in zip(TM['starts'], TM['durs']):
            ims.append(Image.fromarray(frame(t0 + d * 0.75, TM, LINES, BEATS).to_uint8()).resize((216, 384)))
        cols = 8
        sh = Image.new('RGB', (216 * cols, 384 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sh.paste(im, ((i % cols) * 216, (i // cols) * 384))
        sh.save(a.out); return
    if a.still is not None:
        Image.fromarray(frame(a.still, TM, LINES, BEATS).to_uint8()).save(a.out); return
    cover = a.cover or os.path.splitext(a.out)[0] + '_cover.png'   # frame one, saved to check and to use as the thumbnail
    Image.fromarray(frame(0.0, TM, LINES, BEATS).to_uint8()).save(cover)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    for i in range(int(round(TM['total'] * FPS))):
        ff.stdin.write(frame(i / FPS, TM, LINES, BEATS).to_uint8().tobytes())
    ff.stdin.close(); ff.wait()


# ------------------------------------------------------------------ sound
class Mix:
    """Circular mix: anything placed past the end folds back onto the start."""
    SR = 44100

    def __init__(self, times_path, studio_root=None):
        root = studio_root or os.environ.get('STUDIO_ROOT')
        sys.path.insert(0, root)
        from studio.instruments import synth as S
        self.S = S
        self.K = os.path.join(root, 'studio', 'sfx', 'samples')
        self.TM = json.load(open(times_path))
        self.B, self.DUR, self.D = self.TM['starts'], self.TM['durs'], self.TM['total']
        self.N = int(round(self.D * self.SR)); self.PAD = 6 * self.SR
        self.fx = np.zeros((2, self.N + self.PAD)); self.mus = np.zeros((2, self.N + self.PAD))
        self._c = {}

    def ld(self, p):
        t = tempfile.mktemp(suffix='.wav')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ac', '1', '-ar', str(self.SR), t])
        import soundfile as sf
        x, _ = sf.read(t); os.unlink(t); return x

    def k(self, cat, i=0):
        d = os.path.join(self.K, cat); fs = sorted(os.listdir(d)); p = os.path.join(d, fs[i % len(fs)])
        if p not in self._c:
            self._c[p] = self.ld(p)
        return self._c[p]

    def put(self, buf, x, t, db, pan=0.0):
        x = np.asarray(x, float)
        if x.ndim == 1:
            x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
        a = int(t * self.SR) % self.N; b = min(self.N + self.PAD, a + x.shape[1])
        buf[:, a:b] += x[:, :b - a] * 10 ** (db / 20)

    def fx_(self, x, t, db, pan=0.0):
        self.put(self.fx, x, t, db, pan)

    def mu(self, x, t, db, pan=0.0):
        self.put(self.mus, x, t, db, pan)

    # sound makers
    def env(self, n, a=0.02, r=0.1):
        t = np.arange(n) / self.SR
        return np.clip(t / a, 0, 1) * np.clip((n / self.SR - t) / r, 0, 1)

    def noise(self, dur, lo, hi, seed=1, a=0.1, r=0.2):
        n = int(dur * self.SR)
        return self.S.norm(self.S.bp(np.random.default_rng(seed).standard_normal(n), lo, hi)) * self.env(n, a, r)

    def rumble(self, dur, f=45, seed=2):
        n = int(dur * self.SR); t = np.arange(n) / self.SR
        x = self.S.lp(np.random.default_rng(seed).standard_normal(n), 120) * 3 + np.sin(2 * np.pi * f * t) * 0.6
        return self.S.norm(x) * self.env(n, 0.4, 0.6)

    def tick(self):
        return self.S.pop_note(98, 0.035)

    def heartbeat(self, t0, t1, bpm0, bpm1, db):
        t = t0
        while t < t1:
            p = (t - t0) / max(t1 - t0, 1e-6)
            hb = self.S.impact(0.35)
            self.fx_(hb, t, db); self.fx_(hb * 0.6, t + 0.2, db - 3)
            t += 60 / (bpm0 + (bpm1 - bpm0) * p)

    def swishes(self, db=-17):
        for i in range(1, len(self.B) - 1):
            S = self.S
            self.fx_(S.whoosh(0.45, 300 if i % 2 else 3000, 3000 if i % 2 else 300), self.B[i] - 0.2, db)

    def drone(self, t0, t1, root=33, db=-18):
        S = self.S
        n = int((t1 - t0 + 0.8) * self.SR); t = np.arange(n) / self.SR
        f = S.mtof(root)
        x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.003 * t) + 0.25 * S.lp(np.random.default_rng(int(root)).standard_normal(n), 200)
        x *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.15 * t)
        self.mu(S.norm(x) * self.env(n, 0.8, 0.8), t0, db)

    def pad(self, notes, t0, t1, db, bright=1400, a=0.6, r=0.8):
        self.mu(self.S.soft_pad(notes, t1 - t0 + r, a=a, r=r, bright=bright), t0, db)

    def strings(self, notes, t0, t1, db, c0=300, c1=4000):
        S = self.S; n = t1 - t0
        ss = S.supersaw(notes, n + 0.3, cutoff=max(c0, c1), cut_arr=np.linspace(c0, c1, int((n + 0.3) * self.SR)))
        self.mu(ss[:, :int(n * self.SR)], t0, db)

    def clock(self, t0, t1, db=-24, step=0.625):
        t, i = t0, 0
        while t < t1:
            self.mu(self.S.pop_note(103 if i % 2 else 98, 0.03), t, db, 0.3 if i % 2 else -0.3); t += step; i += 1

    def shape(self, t0, t1, db, ramp=0.3):
        """Story-level loudness: lift or sink a whole section (quiet before a reveal, open up for the payoff)."""
        if not hasattr(self, '_shape'):
            self._shape = []
        self._shape.append((t0, t1, db, ramp))

    def light_score(self, key=60, db=-20, seed=1):
        """Curious, bright bed for 'how it works' Shorts: warm pad + soft plucked line + light tick, seamless around the loop."""
        S = self.S; D = self.D; rng = np.random.default_rng(seed)
        chords = [[key - 12, key - 5, key, key + 4], [key - 15, key - 8, key - 3, key + 4], [key - 19, key - 12, key - 7, key - 3], [key - 17, key - 10, key - 5, key + 2]]
        bar = 2.5
        n = int(np.ceil(D / bar)) + 1
        for i in range(n):
            c = chords[i % 4]
            self.mu(S.soft_pad(c, bar + 0.6, a=0.3, r=0.6, bright=2200), i * bar, db - 3)
            for j in range(4):
                self.mu(S.pluck(c[(j + i) % 4] + 12, 0.3), i * bar + j * bar / 4 + 0.05, db - 2, 0.3 * np.sin(j))
            for j in range(8):
                self.mu(S.hat(), i * bar + j * bar / 8, db - 12, 0.3)

    def finish(self, narration, out):
        """Fold tails, put the voice on top (bed 7 dB under while talking), shape, one fixed gain to -14 LUFS."""
        import soundfile as sf, pyloudnorm as pyln
        if CTA and not getattr(self, '_cta_done', False):         # the SUBSCRIBE tap: a click and a two-note ding
            self._cta_done = True
            tt = self.D - CTA_START
            self.fx_(self.S.whoosh(0.25, 600, 2400), tt - 0.02, -20)
            tap = tt + CTA_TAP
            self.fx_(self.S.pop_note(92, 0.05), tap, -12)
            self.fx_(self.S.bell(88, 0.9, dec=0.35), tap + 0.06, -15)
            self.fx_(self.S.bell(93, 1.0, dec=0.4), tap + 0.16, -16)
        S, N, PAD, SR = self.S, self.N, self.PAD, self.SR
        fx, mus = self.fx, self.mus
        fx[:, :PAD] += fx[:, N:N + PAD]; mus[:, :PAD] += mus[:, N:N + PAD]
        fx, mus = fx[:, :N], mus[:, :N]
        v = self.ld(narration)[:N]
        vo = np.zeros((2, N)); vo[:, :len(v)] += v
        e = np.convolve(np.abs(vo[0]), np.ones(2205) / 2205, 'same')
        act = np.convolve(np.clip(e / (np.percentile(e, 95) + 1e-9) * 3, 0, 1), np.ones(4410) / 4410, 'same')
        fxb, mub = S.hp(fx, 45) * (1 - 0.5 * act), S.hp(mus, 55) * (1 - 0.6 * act)
        rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-9
        talk = act > 0.5
        g = 10 ** (-7 / 20) / rms((fxb + mub)[:, talk])               # sound effects stay where they were
        vo = vo / rms(vo[:, talk]); bed = fxb * g + mub * g * 10 ** (-MUSIC_DROP / 20)   # music sits well under the voice
        mix = bed + vo
        sh = np.zeros(N)
        for t0, t1, db, r in getattr(self, '_shape', []):
            a, b = int(t0 * SR), int(t1 * SR); w = np.zeros(N); w[a:b] = 1
            sh += db * np.convolve(w, np.ones(int(r * SR)) / int(r * SR), 'same')
        mix = mix * 10 ** (sh / 20)
        mix = np.tanh(mix / np.max(np.abs(mix)) * 0.9) / np.tanh(0.9)
        raw, eq = out + '.raw.wav', out + '.eq.wav'
        sf.write(raw, mix.T, SR)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'equalizer=f=450:t=o:w=1.2:g=-4,highshelf=f=5000:g=2', '-ar', str(SR), eq])
        y, _ = sf.read(eq)
        y = y * 10 ** ((-14 - pyln.Meter(SR).integrated_loudness(y)) / 20)
        lim = 10 ** (-2 / 20)
        if np.max(np.abs(y)) > lim:
            y = np.tanh(y / lim) * lim
        n = int(0.01 * SR); w = np.linspace(0, 1, n)[:, None]
        y[-n:] = y[-n:] * (1 - w) + y[:1] * w
        sf.write(out, y, SR)
        os.unlink(raw); os.unlink(eq)
