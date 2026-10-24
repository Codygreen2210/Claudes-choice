"""Shaded-2D renderer: flat shapes defined as signed distance fields, lit as if
they were puffy 3D objects (toon bands, rim light, soft drop shadow, ink outline).
World units are pixels at zoom 1; y points down; origin is the screen centre."""
import os as _os_size
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# TOON_SIZE lets tools (rigcheck) run every beat on a tiny canvas; renders always use 1080x1920
W, H = (int(v) for v in _os_size.environ.get('TOON_SIZE', '1080x1920').split('x'))
INK = np.array([0.10, 0.07, 0.12], np.float32)
LIGHT = np.array([-0.50, -0.62, 0.60], np.float32)
LIGHT /= np.linalg.norm(LIGHT)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def ramp(base, dark=None, light=None):
    b = hexc(base) if isinstance(base, str) else np.asarray(base, np.float32)
    d = hexc(dark) if isinstance(dark, str) else (b * np.array([0.62, 0.66, 0.82]) if dark is None else dark)
    l = hexc(light) if isinstance(light, str) else (np.clip(b * 1.10 + np.array([0.08, 0.06, 0.03]), 0, 1) if light is None else light)
    return (np.asarray(d, np.float32), b, np.asarray(l, np.float32))


def mixc(a, b, t):
    return a + (b - a) * t


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- SDF primitives
def circle(cx, cy, r):
    return lambda X, Y: np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) - r


def capsule(ax, ay, bx, by, r, r2=None):
    r2 = r if r2 is None else r2
    bax, bay = bx - ax, by - ay
    bb = bax * bax + bay * bay + 1e-9

    def f(X, Y):
        pax, pay = X - ax, Y - ay
        h = np.clip((pax * bax + pay * bay) / bb, 0, 1)
        return np.sqrt((pax - bax * h) ** 2 + (pay - bay * h) ** 2) - (r + (r2 - r) * h)
    return f


def ellipse(cx, cy, rx, ry):
    m = min(rx, ry)
    return lambda X, Y: (np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2) - 1) * m


def rotell(cx, cy, rx, ry, deg):
    c, sn = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    m = min(rx, ry)

    def f(X, Y):
        x, y = X - cx, Y - cy
        u, v = x * c + y * sn, -x * sn + y * c
        return (np.sqrt((u / rx) ** 2 + (v / ry) ** 2) - 1) * m
    return f


def scaled(f, cx, cy, s):
    return lambda X, Y: f(cx + (X - cx) / s, cy + (Y - cy) / s) * s


def rbox(cx, cy, hw, hh, r):
    def f(X, Y):
        qx = np.abs(X - cx) - hw + r
        qy = np.abs(Y - cy) - hh + r
        return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r
    return f


def heart(cx, cy, s):
    """Inigo Quilez heart, point down, size s (approx width)."""
    def f(X, Y):
        px = np.abs(X - cx) / s
        py = -(Y - cy) / s + 0.62
        a = np.sqrt((px - 0.25) ** 2 + (py - 0.75) ** 2) - np.sqrt(2) / 4
        m = 0.5 * np.maximum(px + py, 0)
        b = np.sqrt(np.minimum((px - 0) ** 2 + (py - 1) ** 2, (px - m) ** 2 + (py - m) ** 2)) * np.sign(px - py)
        return np.where(py + px > 1, a, b) * s
    return f


def union(*fs):
    def f(X, Y):
        d = fs[0](X, Y)
        for g in fs[1:]:
            d = np.minimum(d, g(X, Y))
        return d
    return f


def smooth(k, *fs):
    def f(X, Y):
        d = fs[0](X, Y)
        for g in fs[1:]:
            e = g(X, Y)
            h = np.clip(0.5 + 0.5 * (e - d) / k, 0, 1)
            d = e + (d - e) * h - k * h * (1 - h)
        return d
    return f


def inter(a, b):
    return lambda X, Y: np.maximum(a(X, Y), b(X, Y))


def subtract(a, b):
    return lambda X, Y: np.maximum(a(X, Y), -b(X, Y))


def offset(f, dx, dy, grow=0.0):
    return lambda X, Y: f(X - dx, Y - dy) - grow


def polyline(pts, r):
    caps = [capsule(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r) for i in range(len(pts) - 1)]
    return union(*caps)


def bbox_of(pts, pad):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, cx=0.0, cy=0.0, zoom=1.0):
        self.cx, self.cy, self.zoom = cx, cy, zoom
        self.img = np.zeros((H, W, 3), np.float32)

    def to_px(self, x, y):
        return (x - self.cx) * self.zoom + W / 2, (y - self.cy) * self.zoom + H / 2

    def region(self, bbox):
        x0, y0 = self.to_px(bbox[0], bbox[1])
        x1, y1 = self.to_px(bbox[2], bbox[3])
        px0, py0 = max(int(np.floor(x0)), 0), max(int(np.floor(y0)), 0)
        px1, py1 = min(int(np.ceil(x1)), W), min(int(np.ceil(y1)), H)
        if px1 <= px0 or py1 <= py0:
            return None
        xs = ((np.arange(px0, px1, dtype=np.float32) + 0.5 - W / 2) / self.zoom + self.cx)[None, :]
        ys = ((np.arange(py0, py1, dtype=np.float32) + 0.5 - H / 2) / self.zoom + self.cy)[:, None]
        return (slice(py0, py1), slice(px0, px1)), xs, ys

    # background: vertical gradient + vignette
    def background(self, top, bottom, vignette=0.35, glow=None):
        t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        self.img[:] = mixc(hexc(top), hexc(bottom), t)
        if glow is not None:  # (x, y, radius, color, strength) in screen px
            gx, gy, gr, gc, gs = glow
            yy, xx = np.mgrid[0:H:4, 0:W:4]
            g = np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * gr * gr)).astype(np.float32)
            g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
            self.img += g[..., None] * hexc(gc) * gs
        if vignette:
            self.vignette(vignette)

    def vignette(self, amt):
        yy, xx = np.ogrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        self.img *= (1 - amt * sstep(0.55, 1.25, r))[..., None].astype(np.float32)

    def shape(self, sdf, bbox, rmp, ow=4.0, bevel=38.0, shadow=0.22, shadow_off=(10, 16),
              alpha=1.0, rim=0.32, spec=0.35, mask=None, flat=False, tint=None):
        z = self.zoom
        pad = max(ow + 3, 30) / z
        reg = self.region((bbox[0] - pad, bbox[1] - pad, bbox[2] + pad + shadow_off[0] / z, bbox[3] + pad + shadow_off[1] / z))
        if reg is None:
            return
        sl, X, Y = reg
        dst = self.img[sl]
        if shadow > 0:
            ds = sdf(X - shadow_off[0] / z, Y - shadow_off[1] / z) * z
            a = sstep(14, -14, ds) * shadow * alpha
            if mask is not None:
                a = a * sstep(1, -1, mask(X, Y) * z)
            dst *= (1 - a)[..., None]
        d = sdf(X, Y) * z
        if d.shape != dst.shape[:2]:
            d = np.broadcast_to(d, dst.shape[:2])
        m = 1.0 if mask is None else np.clip(0.5 - mask(X, Y) * z, 0, 1)
        if ow > 0:
            a_ink = (np.clip(0.5 - (d - ow), 0, 1) * alpha * m)[..., None]
            dst += (INK - dst) * a_ink
        a_f = (np.clip(0.5 - d, 0, 1) * alpha * m)
        if not np.any(a_f > 0):
            return
        dark, mid, light = rmp
        if flat:
            col = np.broadcast_to(mid, dst.shape).copy()
        else:
            s = np.maximum(-d, 0) / bevel
            u = np.clip(1 - s, 0, 1)
            slope = np.where(s < 1, u / np.sqrt(np.maximum(1 - u * u, 0.02)), 0.0)
            slope = np.minimum(slope, 5.0)
            gy, gx = np.gradient(d)
            gl = np.sqrt(gx * gx + gy * gy) + 1e-6
            nx, ny = gx / gl * slope, gy / gl * slope
            nz = np.ones_like(nx)
            nl = np.sqrt(nx * nx + ny * ny + nz * nz)
            nx, ny, nz = nx / nl, ny / nl, nz / nl
            lam = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
            t1 = sstep(0.30, 0.34, lam)[..., None]
            t2 = sstep(0.86, 0.90, lam)[..., None]
            col = mixc(mixc(dark, mid, t1), light, t2)
            if spec > 0:
                sp = sstep(0.975, 0.985, lam)[..., None] * spec
                col = mixc(col, np.array([1, 1, 1], np.float32), sp)
            if rim > 0:
                back = -(nx * LIGHT[0] + ny * LIGHT[1]) / (np.sqrt(LIGHT[0] ** 2 + LIGHT[1] ** 2))
                r = (sstep(0.55, 0.62, 1 - nz) * sstep(0.2, 0.5, back))[..., None] * rim
                col = col + r * np.array([0.55, 0.75, 1.0], np.float32)
        if tint is not None:  # (color, amount array or float)
            tc, ta = tint
            ta = ta if np.isscalar(ta) else np.broadcast_to(ta, dst.shape[:2])[..., None]
            col = mixc(col, hexc(tc) if isinstance(tc, str) else tc, ta)
        dst += (col - dst) * a_f[..., None]

    def glow(self, sdf, bbox, color, radius=30.0, intensity=1.0, core='#fffbe6', core_w=0.0):
        z = self.zoom
        pad = radius * 4 / z
        reg = self.region((bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad))
        if reg is None:
            return
        sl, X, Y = reg
        d = sdf(X, Y) * z
        dst = self.img[sl]
        g = np.exp(-np.maximum(d, 0) / radius) * intensity
        dst += g[..., None] * hexc(color)
        a = np.clip(0.5 - (d - core_w), 0, 1)[..., None] * min(intensity, 1.0)
        dst += (hexc(core) - dst) * a

    def flash(self, color, amt):
        if amt > 0:
            self.img += (hexc(color) - self.img) * amt

    def overlay(self, rgba):
        """rgba: PIL RGBA image W x H."""
        a = np.asarray(rgba, np.float32) / 255
        self.img += (a[..., :3] - self.img) * a[..., 3:4]

    def add_light(self, rgb_img, strength=1.0):
        self.img += np.asarray(rgb_img, np.float32)[..., :3] / 255 * strength

    def to_uint8(self):
        return (np.clip(self.img, 0, 1) * 255 + 0.5).astype(np.uint8)


def jagged(p0, p1, seed, depth=5, rough=0.32):
    """Midpoint-displacement lightning path."""
    rng = np.random.default_rng(seed)
    pts = [np.array(p0, float), np.array(p1, float)]
    disp = np.linalg.norm(pts[1] - pts[0]) * rough
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            mvec = (a + b) / 2
            dvec = b - a
            n = np.array([-dvec[1], dvec[0]]) / (np.linalg.norm(dvec) + 1e-9)
            new += [mvec + n * rng.uniform(-disp, disp), b]
        pts = new
        disp *= 0.5
    return [tuple(p) for p in pts]


def ease(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def keys(t, ks):
    """Piecewise eased interpolation of [(time, value), ...]."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks[:-1], ks[1:]):
        if t <= t1:
            return lerp(v0, v1, ease((t - t0) / (t1 - t0)))
    return ks[-1][1]


# ---------------------------------------------------------------- fast path (C kernels), off with TOON_FAST=0
import os as _os, sys as _sys
if _os.environ.get('TOON_FAST', '1') != '0':
    try:
        import fast as _fast
        ({'v1': _fast.install, 'v2': _fast.install_v2b, 'v3': _fast.install_v3}[_os.environ.get('TOON_ENGINE', 'v3')])(_sys.modules[__name__])
    except Exception as _e:  # keep rendering with numpy if the compiler or library is unavailable
        print('fast path unavailable:', _e)
