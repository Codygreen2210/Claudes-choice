"""Plugs the C kernels (libfastk.so) into toon2d: same pictures, much less Python per pixel.
Imported at the end of toon2d.py; falls back to the numpy path if the library is missing."""
import ctypes, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SO = os.path.join(HERE, 'libfastk.so')
SRC = os.path.join(HERE, 'fastk.c')
if not os.path.exists(SO) or os.path.getmtime(SO) < os.path.getmtime(SRC):
    subprocess.run(['gcc', '-O3', '-march=native', '-ffast-math', '-shared', '-fPIC', SRC, '-o', SO, '-lm'], check=True)
lib = ctypes.CDLL(SO)

F = ctypes.POINTER(ctypes.c_float)
U8 = ctypes.POINTER(ctypes.c_ubyte)
i_, f_ = ctypes.c_int, ctypes.c_float
lib.sdf_circle.argtypes = [F, i_, i_, F, F, f_, f_, f_]
lib.sdf_capsule.argtypes = [F, i_, i_, F, F, f_, f_, f_, f_, f_, f_]
lib.sdf_polyline.argtypes = [F, i_, i_, F, F, F, i_, f_]
lib.shade.argtypes = [F, i_, i_, i_, i_, i_, F, F, F, f_, f_, f_, f_, f_, f_, i_, F, F, F, F, f_, F, F]
lib.glow.argtypes = [F, i_, i_, i_, i_, i_, F, F, f_, f_, F, f_]
lib.overlay.argtypes = [F, i_, i_, i_, i_, i_, U8, i_]
lib.sdf_rbox.argtypes = [F, i_, i_, F, F, f_, f_, f_, f_, f_]
lib.sdf_ellipse.argtypes = [F, i_, i_, F, F, f_, f_, f_, f_, f_, f_]
lib.shade2.argtypes = [F, i_, i_, i_, i_, i_, F, i_, i_, i_, i_, i_, i_, F,
                       f_, f_, f_, f_, f_, f_, i_, F, F, F, F, f_, F, F]
lib.to_u8.argtypes = [F, U8, ctypes.c_size_t]
lib.add_light.argtypes = [F, i_, i_, i_, i_, i_, U8, i_, i_, f_]
lib.flash.argtypes = [F, ctypes.c_size_t, f_, f_, f_, f_]
lib.sdf_heart.argtypes = [F, i_, i_, F, F, f_, f_, f_]
lib.smin.argtypes = [F, F, ctypes.c_size_t, f_]


def P(a):
    return None if a is None else a.ctypes.data_as(F)


def c32(a):
    return np.ascontiguousarray(a, dtype=np.float32)


def grid(X, Y):
    X, Y = np.asarray(X), np.asarray(Y)
    if X.ndim == 2 and Y.ndim == 2 and X.shape[0] == 1 and Y.shape[1] == 1:
        return c32(X[0]), c32(Y[:, 0])
    return None


def cfield(slow, call):
    """Wrap a C SDF kernel: use it on separable grids, fall back to numpy otherwise."""
    def f(X, Y):
        g = grid(X, Y)
        if g is None:
            return slow(X, Y)
        xs, ys = g
        out = np.empty((len(ys), len(xs)), np.float32)
        call(out, xs, ys)
        return out
    return f


def ensure(self):
    if not self.img.flags['C_CONTIGUOUS'] or self.img.dtype != np.float32:
        self.img = c32(self.img)


def install(T):
    """v1: C SDFs for circle/capsule/polyline, C shading, glow, overlay, cached background."""
    np_circle, np_capsule, np_polyline = T.circle, T.capsule, T.polyline

    def circle(cx, cy, r):
        return cfield(np_circle(cx, cy, r), lambda o, xs, ys: lib.sdf_circle(P(o), len(ys), len(xs), P(xs), P(ys), cx, cy, r))

    def capsule(ax, ay, bx, by, r, r2=None):
        r2 = r if r2 is None else r2
        return cfield(np_capsule(ax, ay, bx, by, r, r2),
                      lambda o, xs, ys: lib.sdf_capsule(P(o), len(ys), len(xs), P(xs), P(ys), ax, ay, bx, by, r, r2))

    def polyline(pts, r):
        arr = c32(np.array(pts, dtype=np.float64).reshape(-1, 2))
        return cfield(np_polyline(pts, r),
                      lambda o, xs, ys: lib.sdf_polyline(P(o), len(ys), len(xs), P(xs), P(ys), P(arr), len(arr), r))

    T.circle, T.capsule, T.polyline = circle, capsule, polyline

    Canvas = T.Canvas
    np_shape = Canvas.shape
    LIGHT, INK = c32(T.LIGHT), c32(T.INK)

    def reg_info(self, bbox):
        reg = self.region(bbox)
        if reg is None:
            return None
        sl, X, Y = reg
        return sl, X, Y, sl[0].start, sl[1].start, sl[0].stop - sl[0].start, sl[1].stop - sl[1].start

    def shape(self, sdf, bbox, rmp, ow=4.0, bevel=38.0, shadow=0.22, shadow_off=(10, 16),
              alpha=1.0, rim=0.32, spec=0.35, mask=None, flat=False, tint=None):
        tint_col, tint_amt = None, 0.0
        if tint is not None:
            tc, ta = tint
            if not np.isscalar(ta):
                return np_shape(self, sdf, bbox, rmp, ow, bevel, shadow, shadow_off, alpha, rim, spec, mask, flat, tint)
            tint_col = c32(T.hexc(tc) if isinstance(tc, str) else tc)
            tint_amt = float(ta)
        z = self.zoom
        pad = max(ow + 3, 30) / z
        info = reg_info(self, (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad + shadow_off[0] / z, bbox[3] + pad + shadow_off[1] / z))
        if info is None:
            return
        sl, X, Y, y0, x0, h, w = info
        ensure(self)
        d = c32(np.broadcast_to(sdf(X, Y) * z, (h, w)))
        dsh = c32(np.broadcast_to(sdf(X - shadow_off[0] / z, Y - shadow_off[1] / z) * z, (h, w))) if shadow > 0 else None
        md = c32(np.broadcast_to(mask(X, Y) * z, (h, w))) if mask is not None else None
        dark, mid, light = (c32(c) for c in rmp)
        lib.shade(P(self.img), T.W, y0, x0, h, w, P(d), P(dsh), P(md), ow, bevel, shadow, alpha, rim, spec, int(flat),
                  P(dark), P(mid), P(light), P(tint_col), tint_amt, P(LIGHT), P(INK))

    def glow(self, sdf, bbox, color, radius=30.0, intensity=1.0, core='#fffbe6', core_w=0.0):
        z = self.zoom
        pad = radius * 4 / z
        info = reg_info(self, (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad))
        if info is None:
            return
        sl, X, Y, y0, x0, h, w = info
        ensure(self)
        d = c32(np.broadcast_to(sdf(X, Y) * z, (h, w)))
        lib.glow(P(self.img), T.W, y0, x0, h, w, P(d), P(c32(T.hexc(color))), float(radius), float(intensity),
                 P(c32(T.hexc(core))), float(max(core_w, -1e30)))

    def overlay(self, rgba):
        a = rgba.getchannel('A').getbbox()
        if a is None:
            return
        x0, y0, x1, y1 = a
        crop = np.ascontiguousarray(np.asarray(rgba.crop(a), dtype=np.uint8))
        ensure(self)
        lib.overlay(P(self.img), T.W, y0, x0, y1 - y0, x1 - x0, crop.ctypes.data_as(U8), (x1 - x0) * 4)

    cache = {}

    def background(self, top, bottom, vignette=0.35, glow=None):
        vkey = ('v', vignette)
        if vkey not in cache:
            yy, xx = np.ogrid[0:T.H, 0:T.W]
            r = np.sqrt(((xx - T.W / 2) / (T.W * 0.62)) ** 2 + ((yy - T.H / 2) / (T.H * 0.62)) ** 2)
            cache[vkey] = c32((1 - (vignette or 0) * T.sstep(0.55, 1.25, r))[..., None])
        key = (top, bottom, vignette)
        if key not in cache:
            t = np.linspace(0, 1, T.H, dtype=np.float32)[:, None, None]
            cache[key] = c32(T.mixc(T.hexc(top), T.hexc(bottom), t) * np.ones((1, T.W, 1), np.float32) * cache[vkey])
        self.img = cache[key].copy()
        if glow is not None:
            gx, gy, gr, gc, gs = glow
            if 'g4' not in cache:
                cache['g4'] = np.mgrid[0:T.H:4, 0:T.W:4].astype(np.float32)
            yy, xx = cache['g4']
            g = np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * gr * gr)).astype(np.float32)
            g = np.asarray(T.Image.fromarray((g * 255).astype(np.uint8)).resize((T.W, T.H), T.Image.BILINEAR), np.float32) / 255
            self.img += (g[..., None] * cache[vkey]) * (T.hexc(gc) * gs)

    Canvas.shape, Canvas.glow, Canvas.overlay, Canvas.background = shape, glow, overlay, background


def install_v2(T):
    """v2: shared shadow field, C rbox/ellipse, C output, light and flash."""
    install(T)
    np_rbox, np_rotell = T.rbox, T.rotell

    def rbox(cx, cy, hw, hh, r):
        return cfield(np_rbox(cx, cy, hw, hh, r),
                      lambda o, xs, ys: lib.sdf_rbox(P(o), len(ys), len(xs), P(xs), P(ys), cx, cy, hw, hh, r))

    def rotell(cx, cy, rx, ry, deg):
        c, s = float(np.cos(np.radians(deg))), float(np.sin(np.radians(deg)))
        return cfield(np_rotell(cx, cy, rx, ry, deg),
                      lambda o, xs, ys: lib.sdf_ellipse(P(o), len(ys), len(xs), P(xs), P(ys), cx, cy, rx, ry, c, s))

    T.rbox, T.rotell = rbox, rotell
    T.ellipse = lambda cx, cy, rx, ry: rotell(cx, cy, rx, ry, 0.0)

    Canvas = T.Canvas
    v1_shape = Canvas.shape
    LIGHT, INK = c32(T.LIGHT), c32(T.INK)
    W, H = T.W, T.H

    def shape(self, sdf, bbox, rmp, ow=4.0, bevel=38.0, shadow=0.22, shadow_off=(10, 16),
              alpha=1.0, rim=0.32, spec=0.35, mask=None, flat=False, tint=None):
        sox, soy = shadow_off
        if (tint is not None and not np.isscalar(tint[1])) or (shadow > 0 and (sox != int(sox) or soy != int(soy))):
            return v1_shape(self, sdf, bbox, rmp, ow, bevel, shadow, shadow_off, alpha, rim, spec, mask, flat, tint)
        sox, soy = (int(sox), int(soy)) if shadow > 0 else (0, 0)
        tint_col, tint_amt = None, 0.0
        if tint is not None:
            tint_col = c32(T.hexc(tint[0]) if isinstance(tint[0], str) else tint[0])
            tint_amt = float(tint[1])
        z = self.zoom
        pad = max(ow + 3, 30) / z
        ax0, ay0 = self.to_px(bbox[0] - pad, bbox[1] - pad)
        ax1, ay1 = self.to_px(bbox[2] + pad + sox / z, bbox[3] + pad + soy / z)
        x0, y0 = max(int(np.floor(ax0)), 0), max(int(np.floor(ay0)), 0)
        x1, y1 = min(int(np.ceil(ax1)), W), min(int(np.ceil(ay1)), H)
        if x1 <= x0 or y1 <= y0:
            return
        ex0, ey0 = x0 - sox, y0 - soy  # field also covers where the shadow comes from
        xs = ((np.arange(ex0, x1, dtype=np.float32) + 0.5 - W / 2) / z + self.cx)[None, :]
        ys = ((np.arange(ey0, y1, dtype=np.float32) + 0.5 - H / 2) / z + self.cy)[:, None]
        fh, fw = y1 - ey0, x1 - ex0
        df = c32(np.broadcast_to(sdf(xs, ys) * z, (fh, fw)))
        h, w = y1 - y0, x1 - x0
        md = None
        if mask is not None:
            md = c32(np.broadcast_to(mask(xs[:, x0 - ex0:], ys[y0 - ey0:, :]) * z, (h, w)))
        ensure(self)
        dark, mid, light = (c32(c) for c in rmp)
        lib.shade2(P(self.img), W, y0, x0, h, w, P(df), fw, fh, x0 - ex0, y0 - ey0, sox, soy, P(md),
                   ow, bevel, shadow, alpha, rim, spec, int(flat), P(dark), P(mid), P(light),
                   P(tint_col), tint_amt, P(LIGHT), P(INK))

    def to_uint8(self):
        ensure(self)
        out = np.empty((H, W, 3), np.uint8)
        lib.to_u8(P(self.img), out.ctypes.data_as(U8), out.size)
        return out

    def add_light(self, im, strength=1.0):
        box = im.getbbox()
        if box is None:
            return
        crop = np.ascontiguousarray(np.asarray(im.crop(box), dtype=np.uint8))
        ch = crop.shape[2]
        x0, y0, x1, y1 = box
        ensure(self)
        lib.add_light(P(self.img), W, y0, x0, y1 - y0, x1 - x0, crop.ctypes.data_as(U8), (x1 - x0) * ch, ch, float(strength))

    def flash(self, color, amt):
        if amt > 0:
            ensure(self)
            r, g, b = (float(v) for v in T.hexc(color))
            lib.flash(P(self.img), W * H, r, g, b, float(amt))

    Canvas.shape, Canvas.to_uint8, Canvas.add_light, Canvas.flash = shape, to_uint8, add_light, flash


def install_v2b(T):
    """v2 plus a C heart and blurs that only touch the occupied part of a layer."""
    install_v2(T)
    np_heart = T.heart

    def heart(cx, cy, s):
        return cfield(np_heart(cx, cy, s), lambda o, xs, ys: lib.sdf_heart(P(o), len(ys), len(xs), P(xs), P(ys), cx, cy, s))
    T.heart = heart

    from PIL import Image, ImageFilter
    orig_filter = Image.Image.filter
    if getattr(orig_filter, '_toon', False):
        return

    def filter(self, f):
        if isinstance(f, ImageFilter.GaussianBlur) and self.size == (T.W, T.H):
            box = self.getbbox()
            if box is None:
                return self.copy()
            m = int(f.radius * 3) + 2
            x0, y0, x1, y1 = max(box[0] - m, 0), max(box[1] - m, 0), min(box[2] + m, T.W), min(box[3] + m, T.H)
            if (x1 - x0) * (y1 - y0) < 0.8 * T.W * T.H:
                out = Image.new(self.mode, self.size, (0,) * len(self.getbands()))
                out.paste(orig_filter(self.crop((x0, y0, x1, y1)), f), (x0, y0))
                return out
        return orig_filter(self, f)
    filter._toon = True
    Image.Image.filter = filter


def install_v3(T):
    """v3: flat-top shortcut (in shade2), C smooth unions, in-place unions."""
    install_v2b(T)

    def union(*fs):
        def f(X, Y):
            d = fs[0](X, Y)
            for g in fs[1:]:
                e = g(X, Y)
                if isinstance(d, np.ndarray) and d.shape == np.shape(e) and d.dtype == np.float32 and d.flags.writeable:
                    np.minimum(d, e, out=d)
                else:
                    d = np.minimum(d, e)
            return d
        return f

    def smooth(k, *fs):
        def f(X, Y):
            d = fs[0](X, Y)
            for g in fs[1:]:
                e = g(X, Y)
                shp = np.broadcast_shapes(np.shape(d), np.shape(e))
                d = c32(np.broadcast_to(d, shp)).copy()
                e = c32(np.broadcast_to(e, shp))
                lib.smin(P(d), P(e), d.size, float(k))
            return d
        return f

    T.union, T.smooth = union, smooth
