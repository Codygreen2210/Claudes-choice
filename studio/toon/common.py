"""Shared kit for the Shorts: the everyman with posable arms, faces, polygon SDFs,
hook text, particles, x-ray inset, camera shake and the cut-list player."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from toon2d import *

FPS = 30
YEL = '#ffe14d'
FONT = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
if not os.path.exists(FONT):
    for _f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
               '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        if os.path.exists(_f):
            FONT = _f
            break
INKC = (INK, INK, INK)

SKIN = ramp('#f2b48c', '#c97f62', '#ffd9bd')
SHIRT = ramp('#24b3a3', '#147a77', '#5fe0cc')
JEANS = ramp('#3d5f94', '#26395f', '#5f86c2')
SHOE = ramp('#2c2b38', '#17161f', '#4a4860')
HAIR = ramp('#3b2a22', '#221712', '#5e4436')
WHITE = ramp('#f4f1ea', '#c9c3b8', '#ffffff')
COAT = ramp('#f2f5f7', '#c4ccd4', '#ffffff')
RED = ramp('#e2483d', '#a82a26', '#ff8070')
METAL = ramp('#9aa6b2', '#5f6b78', '#d6dee6')
DARKM = ramp('#4a5361', '#2c323c', '#707b8a')
WOOD = ramp('#a8693a', '#6e4122', '#d08f58')
GLASS = ramp('#bfe6ff', '#7fb6d9', '#eaf7ff')


def flat(c):
    c = hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)
    return (c, c, c)


# ------------------------------------------------------------------ geometry helpers
def poly(pts):
    """Signed distance to a closed polygon (negative inside)."""
    P = np.array(pts, np.float32)

    def f(X, Y):
        X = np.asarray(X, np.float32); Y = np.asarray(Y, np.float32)
        shp = np.broadcast(X, Y).shape
        d = np.full(shp, 1e9, np.float32)
        s = np.ones(shp, np.float32)
        for i in range(len(P)):
            vi, vj = P[i], P[i - 1]
            ex, ey = vj[0] - vi[0], vj[1] - vi[1]
            wx, wy = X - vi[0], Y - vi[1]
            h = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey + 1e-9), 0, 1)
            bx, by = wx - ex * h, wy - ey * h
            d = np.minimum(d, bx * bx + by * by)
            c1 = Y >= vi[1]; c2 = Y < vj[1]; c3 = ex * wy > ey * wx
            flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
            s = np.where(flip, -s, s)
        return s * np.sqrt(d)
    return f


def pbox(pts, pad=0):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def box(cv, cx, cy, hw, hh, rmp, r=10, **kw):
    cv.shape(rbox(cx, cy, hw, hh, r), (cx - hw, cy - hh, cx + hw, cy + hh), rmp, **kw)


def disc(cv, x, y, r, rmp, **kw):
    cv.shape(circle(x, y, r), (x - r, y - r, x + r, y + r), rmp, **kw)


def dot(cv, x, y, r, col=INKC, a=1.0):
    cv.shape(circle(x, y, r), (x - r, y - r, x + r, y + r), col, ow=0, shadow=0, flat=True, alpha=a)


def line(cv, pts, w, col=INKC, a=1.0, **kw):
    kw.setdefault('ow', 0); kw.setdefault('shadow', 0); kw.setdefault('flat', True)
    cv.shape(polyline(pts, w), bbox_of(pts, w), col, alpha=a, **kw)


def wave_surface(y0, amp, k, phase, x0=-3000, x1=3000, y1=4000):
    """Liquid body below a wavy surface."""
    def f(X, Y):
        s = y0 + amp * np.sin(X * k + phase) + amp * 0.4 * np.sin(X * k * 2.3 - phase * 1.7)
        return np.maximum(s - Y, np.maximum(x0 - X, X - x1))
    return f, (x0, y0 - amp * 1.5, x1, y1)


# ------------------------------------------------------------------ the everyman (posable)
def arm_pts(sx, sh, a1, a2, l1=125, l2=135):
    """sx=-1 left / 1 right; angles in degrees, 0 = straight down, positive swings outward."""
    r1 = np.radians(a1); r2 = np.radians(a1 + a2)
    ex, ey = sh[0] + sx * np.sin(r1) * l1, sh[1] + np.cos(r1) * l1
    hx, hy = ex + sx * np.sin(r2) * l2, ey + np.cos(r2) * l2
    return (ex, ey), (hx, hy)


def guy(cv, x, y, s=1.0, face='calm', arms=((12, 0), (12, 0)), shirt=SHIRT, pants=JEANS, hair=HAIR,
        woman=False, coat=False, mask=None, ow=4.5, shadow=0.22, legs=True, tilt_head=0.0, look=(0, 0),
        tint=None, ground=True, bald=False, glasses=False):
    P = lambda px, py: (x + px * s, y + py * s)
    kw = dict(ow=ow, bevel=max(26 * s * cv.zoom, 6), shadow=shadow, mask=mask)

    def cap(a, b, r, rmp, r2=None):
        A, B = P(*a), P(*b)
        rr = r * s; rr2 = (r if r2 is None else r2) * s
        cv.shape(capsule(A[0], A[1], B[0], B[1], rr, rr2), bbox_of([A, B], max(rr, rr2)), rmp,
                 tint=tint if rmp is SKIN else None, **kw)

    def cir(c, r, rmp):
        C = P(*c)
        cv.shape(circle(C[0], C[1], r * s), (C[0] - r * s, C[1] - r * s, C[0] + r * s, C[1] + r * s), rmp,
                 tint=tint if rmp is SKIN else None, **kw)

    if ground and legs:
        cv.shape(ellipse(x, y + 4 * s, 150 * s, 22 * s), (x - 150 * s, y - 18 * s, x + 150 * s, y + 26 * s),
                 ramp('#000000'), ow=0, shadow=0, alpha=0.25, flat=True, mask=mask)
    if legs:
        for sx in (-1, 1):
            cap((sx * 78, -16), (sx * 38, -16), 27, SHOE)
        for sx in (-1, 1):
            cap((sx * 50, -370), (sx * 56, -48), 47, pants, 44)
    hx = tilt_head * 30
    if woman:  # long hair behind the head
        H0 = P(hx, -730)
        cv.shape(rbox(H0[0], H0[1] + 30 * s, 138 * s, 125 * s, 80 * s),
                 (H0[0] - 140 * s, H0[1] - 100 * s, H0[0] + 140 * s, H0[1] + 160 * s), hair, **kw)
    cap((0, -700), (0, -640), 30, SKIN)
    cap((0, -592), (0, -396), 112, shirt, 104)
    if coat:
        for sx in (-1, 1):
            a, b = P(sx * 30, -600), P(sx * 60, -400)
            line(cv, [a, b], 5 * s, flat(hexc('#9aa4ad')), mask=mask)
    sh_y = -590
    for sx, (a1, a2) in zip((-1, 1), arms):
        sh = (sx * 104, sh_y)
        el, hd = arm_pts(sx, sh, a1, a2)
        cap(sh, el, 41, shirt, 36)
        cap(el, hd, 30, SKIN, 28)
        cir((hd[0], hd[1] + 12), 34, SKIN)
    for sx in (-1, 1):
        cir((hx + sx * 98, -760), 22, SKIN)
    cir((hx, -762), 100, SKIN)
    if not bald:
        hh = P(hx, -762)
        blobs = [circle(*P(hx - 62, -826), 52 * s), circle(*P(hx, -846), 60 * s), circle(*P(hx + 62, -826), 52 * s),
                 circle(*P(hx - 88, -792), 32 * s), circle(*P(hx + 88, -792), 32 * s)]
        cut = lambda X, Y: Y - (hh[1] - 30 * s) - 16 * s * np.sin((X - hh[0]) / (19 * s) + 0.6) \
            - np.maximum(np.abs(X - hh[0]) - 70 * s, 0) * 0.9
        cv.shape(inter(smooth(18 * s, *blobs), cut), (hh[0] - 160 * s, hh[1] - 130 * s, hh[0] + 160 * s, hh[1]), hair, **kw)
    face_draw(cv, x + hx * s, y, s, face, look, mask)
    if glasses:
        for sx in (-1, 1):
            ex, ey = P(hx + sx * 36, -770)
            cv.shape(subtract(circle(ex, ey, 30 * s), circle(ex, ey, 24 * s)),
                     (ex - 30 * s, ey - 30 * s, ex + 30 * s, ey + 30 * s), INKC, ow=0, shadow=0, flat=True)


def face_draw(cv, x, y, s, face, look=(0, 0), mask=None):
    P = lambda px, py: (x + px * s, y + py * s)
    lx, ly = look[0] * 8, look[1] * 8
    k = dict(ow=0, shadow=0, flat=True, mask=mask)
    if face in ('shock', 'scream'):
        for sx in (-1, 1):
            ex, ey = P(sx * 36, -772)
            cv.shape(circle(ex, ey, 24 * s), (ex - 24 * s, ey - 24 * s, ex + 24 * s, ey + 24 * s), WHITE,
                     ow=3.5, bevel=8, shadow=0, rim=0, mask=mask)
            dot(cv, ex + lx * s, ey + ly * s, 8 * s)
        mx, my = P(0, -708)
        ry = 26 if face == 'shock' else 36
        cv.shape(ellipse(mx, my, 20 * s, ry * s), (mx - 20 * s, my - ry * s, mx + 20 * s, my + ry * s),
                 ramp('#5a1f2a'), ow=3.5, bevel=8, shadow=0, rim=0, mask=mask)
        return
    if face in ('pain', 'squint'):
        for sx in (-1, 1):
            a, b, c = P(sx * 52, -784), P(sx * 26, -772), P(sx * 52, -760)
            line(cv, [a, b, c], 5 * s, mask=mask)
    elif face == 'closed':
        for sx in (-1, 1):
            a, b, c = P(sx * 50, -768), P(sx * 34, -762), P(sx * 18, -768)
            line(cv, [a, b, c], 5 * s, mask=mask)
    else:
        for sx in (-1, 1):
            ex, ey = P(sx * 34 + lx, -768 + ly)
            cv.shape(ellipse(ex, ey, 10 * s, 13 * s), (ex - 10 * s, ey - 13 * s, ex + 10 * s, ey + 13 * s), INKC, **k)
    if face == 'worried':
        for sx in (-1, 1):
            line(cv, [P(sx * 52, -800), P(sx * 20, -808)], 5 * s, mask=mask)
    if face == 'puff':
        for sx in (-1, 1):
            C = P(sx * 58, -722)
            cv.shape(circle(C[0], C[1], 34 * s), (C[0] - 34 * s, C[1] - 34 * s, C[0] + 34 * s, C[1] + 34 * s),
                     ramp('#f59a86', '#d9705f', '#ffc4b4'), ow=3, bevel=14, shadow=0, rim=0, mask=mask)
        line(cv, [P(-10, -712), P(10, -712)], 5 * s, mask=mask)
    elif face in ('happy', 'smile'):
        line(cv, [P(-28, -722), P(0, -704), P(28, -722)], 5.5 * s, mask=mask)
    elif face == 'pain':
        mx, my = P(0, -712)
        cv.shape(rbox(mx, my, 26 * s, 9 * s, 8 * s), (mx - 26 * s, my - 9 * s, mx + 26 * s, my + 9 * s),
                 ramp('#5a1f2a'), ow=3, bevel=5, shadow=0, rim=0, mask=mask)
    elif face == 'worried':
        line(cv, [P(-24, -706), P(0, -716), P(24, -706)], 5 * s, mask=mask)
    elif face == 'drink':
        pass
    else:
        line(cv, [P(-24, -716), P(0, -706), P(24, -716)], 5 * s, mask=mask)


# ------------------------------------------------------------------ overlays and text
HOOK_NOW = [False]


def hook_text(cv, txt, lt, y=-620, size=118, color=(255, 236, 80), pop_t=0.0, dur=None):
    """0-3 words, top third, pops in; screen coordinates (y relative to centre)."""
    if HOOK_NOW[0] and lt >= 0:          # opening beat: the hook word is up and full size on frame one
        pop_t, dur = 0.0, None
    if lt < pop_t or (dur is not None and lt > pop_t + dur):
        return
    k = 1.0 if HOOK_NOW[0] else min((lt - pop_t) / 0.18, 1.0)
    sc = 0.6 + 0.4 * ease(k) + 0.08 * np.sin(np.pi * min(k, 1))
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, int(size * sc))
    wdt = d.textlength(txt, font=font)
    px, py = W / 2, H / 2 + y
    d.text((px - wdt / 2, py - size * sc * 0.6), txt, font=font, fill=color + (255,),
           stroke_width=12, stroke_fill=(20, 14, 26, 255))
    cv.overlay(im)


def label(cv, txt, x, y, size=60, color=(255, 255, 255), a=1.0):
    """World-space small label (used sparingly, not as captions)."""
    if a <= 0:
        return
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, max(int(size * cv.zoom), 6))
    px, py = cv.to_px(x, y)
    wdt = d.textlength(txt, font=font)
    d.text((px - wdt / 2, py - size * cv.zoom * 0.6), txt, font=font, fill=color + (int(255 * a),),
           stroke_width=int(8 * cv.zoom), stroke_fill=(20, 14, 26, int(255 * a)))
    cv.overlay(im)


def bubbles(cv, t, x0, x1, y0, y1, n=30, rmin=6, rmax=18, speed=160, seed=1, col=(255, 255, 255), a=150, wobble=12):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    xs = rng.uniform(x0, x1, n); ph = rng.uniform(0, 1, n); rs = rng.uniform(rmin, rmax, n); sp = rng.uniform(0.6, 1.4, n)
    span = y1 - y0
    for xx, p, r, k in zip(xs, ph, rs, sp):
        yy = y1 - ((p * span + t * speed * k) % span)
        xw = xx + wobble * np.sin(t * 3 + p * 20)
        px, py = cv.to_px(xw, yy)
        rr = r * cv.zoom
        d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=col + (a,), width=max(2, int(3 * cv.zoom)))
        d.ellipse([px - rr * 0.45, py - rr * 0.6, px - rr * 0.1, py - rr * 0.25], fill=col + (a,))
    cv.overlay(im)


def specks(cv, t, pts_fn, n, color, size, seed=0, a=255):
    """Generic particles: pts_fn(i, rng_vals, t) -> (x, y, alpha) in world coords or None."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    vals = rng.uniform(0, 1, (n, 4))
    for i in range(n):
        r = pts_fn(i, vals[i], t)
        if r is None:
            continue
        x, y, al = r
        px, py = cv.to_px(x, y)
        rr = size * cv.zoom * (0.6 + 0.8 * vals[i][3])
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=tuple(color) + (int(a * al),))
    cv.overlay(im)


def speed_lines(cv, t, amt=1.0, color=(255, 255, 255), vertical=True, seed=4, n=26):
    if amt <= 0:
        return
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    for k in range(n):
        x = rng.uniform(0, W); L = rng.uniform(200, 600); sp = rng.uniform(2500, 4500)
        y = (rng.uniform(0, H) - t * sp) % (H + L) - L
        if vertical:
            d.line([(x, y), (x, y + L)], fill=tuple(color) + (int(90 * amt),), width=4)
        else:
            d.line([(y * W / H, x * H / W), (y * W / H + L, x * H / W)], fill=tuple(color) + (int(90 * amt),), width=4)
    cv.overlay(im)


def ring_lens(cv, inner, cx, cy, r, ring='#ffe14d', k=1.0):
    """Composite canvas `inner` inside a circle (screen px), with a bright ring: the x-ray push-in."""
    if k <= 0:
        return
    rr = r * ease(k)
    yy, xx = np.ogrid[0:H, 0:W]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    m = np.clip(rr - dist, 0, 1)[..., None].astype(np.float32)
    cv.img = np.ascontiguousarray(cv.img * (1 - m) + inner.img * m, dtype=np.float32)
    ringm = (np.clip(1 - np.abs(rr - dist) / 7, 0, 1)[..., None]).astype(np.float32)
    inkm = (np.clip(1 - np.abs(rr + 9 - dist) / 4, 0, 1)[..., None]).astype(np.float32)
    cv.img = cv.img + (hexc(ring) - cv.img) * ringm
    cv.img = np.ascontiguousarray(cv.img + (INK - cv.img) * inkm, dtype=np.float32)


def shake(lt, t0, amt=30, dur=0.5, freq=40):
    if lt < t0 or lt > t0 + dur:
        return 0.0, 0.0
    e = 1 - (lt - t0) / dur
    return amt * e * np.sin(lt * freq), amt * e * np.cos(lt * freq * 1.3)


def vignette_red(cv, amt):
    if amt > 0:
        cv.vignette(amt)


# ------------------------------------------------------------------ cut-list player
def make_frame(CUTS, IRIS=None, FLASH=None, DUR=None):
    IRIS = IRIS or {}
    FLASH = FLASH or {}

    def frame(t):
        for i, (a, b, fn) in enumerate(CUTS):
            if a <= t < b or (i == len(CUTS) - 1 and t >= a):
                cv = fn(t)
                if a in IRIS and t < a + IRIS[a][0] and i > 0:
                    dur, (cx, cy) = IRIS[a]
                    k = ease((t - a) / dur)
                    prev = CUTS[i - 1][2](t)
                    yy, xx = np.ogrid[0:H, 0:W]
                    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                    r = k * 1.3 * H
                    m = np.clip((r - dist) / 6, 0, 1)[..., None].astype(np.float32)
                    ring = (np.clip(1 - np.abs(r - dist) / 14, 0, 1)[..., None] * (1 - k)).astype(np.float32)
                    cv.img = prev.img * (1 - m) + cv.img * m
                    cv.img = np.ascontiguousarray(cv.img + (hexc(YEL) - cv.img) * ring, dtype=np.float32)
                for ft, (fd, fc) in FLASH.items():
                    if ft <= t < ft + fd:
                        cv.flash(fc, 0.55 * (1 - (t - ft) / fd))
                return cv
        return CUTS[-1][2](t)
    return frame


class Words:
    """Look up word start/end times from words_t.json: w.at('slime'), w.at('metal', 2), w.end('metal')."""
    def __init__(self, path='words_t.json'):
        import json, re
        self.w = json.load(open(path))
        self.k = [re.sub(r"[^a-z0-9']", '', x['text'].lower()) for x in self.w]

    def _find(self, word, n=1, after=0.0):
        c = 0
        for i, k in enumerate(self.k):
            if k == word.lower() and self.w[i]['start'] >= after:
                c += 1
                if c == n:
                    return self.w[i]
        raise KeyError(word)

    def at(self, word, n=1, after=0.0):
        return self._find(word, n, after)['start']

    def end(self, word, n=1, after=0.0):
        return self._find(word, n, after)['end']

    @property
    def last(self):
        return self.w[-1]['end']


def hand_pos(x, y, s, sx, a1, a2):
    """World position of a guy() hand for side sx (-1 left, 1 right) and arm angles."""
    el, hd = arm_pts(sx, (sx * 104, -590), a1, a2)
    return x + hd[0] * s, y + (hd[1] + 12) * s
