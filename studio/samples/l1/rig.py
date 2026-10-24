"""Level 1: hand-drawn 2D rig. Jointed skeleton (FK, absolute bone angles), cel-shaded fills,
variable-width ink that boils on twos, painted face.  All drawing is cv2 on uint8/float32 RGB."""
import math
import numpy as np
import cv2

SS = 2  # supersample factor for the character layer

# bone lengths in metres
L = dict(torso=0.52, neck=0.09, head=0.135, ua=0.30, fa=0.27, hand=0.075, th=0.43, sh=0.42, foot=0.25)

SKIN = np.array([236, 184, 150]) / 255
SKIN_SH = np.array([196, 128, 104]) / 255
SHIRT = np.array([38, 186, 168]) / 255
SHIRT_SH = np.array([22, 112, 120]) / 255
JEANS = np.array([58, 92, 170]) / 255
JEANS_SH = np.array([34, 50, 108]) / 255
SHOE = np.array([60, 48, 52]) / 255
SHOE_SH = np.array([30, 22, 30]) / 255
HAIR = np.array([110, 66, 40]) / 255
HAIR_SH = np.array([64, 34, 22]) / 255
INK = np.array([28, 16, 30]) / 255
RIM = np.array([255, 140, 50]) / 255


def ang(d):
    return np.array([math.cos(math.radians(d)), math.sin(math.radians(d))])


def _hash_noise(seed, n):
    r = np.random.default_rng(seed)
    return r.standard_normal(n)


class Pose:
    """Absolute bone angles (degrees, maths convention, y up) + hip position (world metres)."""
    KEYS = ['torso', 'head', 'uaN', 'faN', 'uaF', 'faF', 'thN', 'shN', 'thF', 'shF', 'ftN', 'ftF', 'mouth', 'brow', 'look']

    def __init__(self, hip, **k):
        self.hip = np.array(hip, float)
        for key in self.KEYS:
            setattr(self, key, k.get(key, 0.0))

    @staticmethod
    def lerp(a, b, u):
        p = Pose(a.hip + (b.hip - a.hip) * u)
        for key in Pose.KEYS:
            setattr(p, key, getattr(a, key) + (getattr(b, key) - getattr(a, key)) * u)
        return p


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def keyed(keys, t):
    """keys: list of (time, Pose).  Smooth-step between keys (holds at ends)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
        if t <= t1:
            return Pose.lerp(p0, p1, ease((t - t0) / (t1 - t0)))
    return keys[-1][1]


def joints(p, front=False):
    """World joint positions from a pose."""
    J = {}
    hip = p.hip
    J['hip'] = hip
    tv = ang(p.torso)
    J['neck'] = hip + tv * L['torso']
    J['sho'] = hip + tv * L['torso'] * 0.88
    J['headc'] = J['neck'] + ang(p.head) * L['head']
    side = np.array([-tv[1], tv[0]])            # perpendicular to the torso
    if front:
        shN, shF = J['sho'] + side * 0.19, J['sho'] - side * 0.19
        hpN, hpF = hip + side * 0.09, hip - side * 0.09
    else:
        shN, shF = J['sho'] + side * 0.01, J['sho'] - side * 0.01
        hpN, hpF = hip, hip
    for s, sh, hp in (('N', shN, hpN), ('F', shF, hpF)):
        J['sh' + s] = sh
        J['el' + s] = sh + ang(getattr(p, 'ua' + s)) * L['ua']
        J['wr' + s] = J['el' + s] + ang(getattr(p, 'fa' + s)) * L['fa']
        J['hd' + s] = J['wr' + s] + ang(getattr(p, 'fa' + s)) * L['hand']
        J['hp' + s] = hp
        J['kn' + s] = hp + ang(getattr(p, 'th' + s)) * L['th']
        J['an' + s] = J['kn' + s] + ang(getattr(p, 'sh' + s)) * L['sh']
    return J


# ------------------------------------------------------------------ shapes (screen px, y down)
def limb_poly(a, b, wa, wb, bulge=0.0, n=10):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    ln = np.hypot(*d) + 1e-6
    u = d / ln
    nv = np.array([-u[1], u[0]])
    s = np.linspace(0, 1, n)
    w = wa + (wb - wa) * s + bulge * np.sin(np.pi * s)
    left = a + np.outer(s, d) + np.outer(w, nv)
    right = a + np.outer(s, d) - np.outer(w, nv)
    th = math.atan2(u[1], u[0])
    capb = [b + wb * np.array([math.cos(th + math.pi / 2 - k), math.sin(th + math.pi / 2 - k)]) for k in np.linspace(0, math.pi, 9)]
    capa = [a + wa * np.array([math.cos(th - math.pi / 2 - k), math.sin(th - math.pi / 2 - k)]) for k in np.linspace(0, math.pi, 9)]
    return np.vstack([left, capb[1:-1], right[::-1], capa[1:-1]])


def ellipse_poly(c, rx, ry, rot=0.0, n=40, wob=None):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = rx * np.cos(t), ry * np.sin(t)
    if wob is not None:
        x, y = x * (1 + wob * np.sin(3 * t + 1)), y * (1 + wob * np.sin(2 * t))
    cr, sr = math.cos(rot), math.sin(rot)
    return np.stack([c[0] + x * cr - y * sr, c[1] + x * sr + y * cr], 1)


class Ink:
    """Draws parts onto a supersampled RGB layer with cel shading and boiling variable-width ink."""

    def __init__(self, h, w, boil_seed, light=(0.6, -0.8), rim=(0.3, 0.95), rim_col=RIM, rim_amt=0.0, ink_px=3.2):
        self.h, self.w = h, w
        self.col = np.zeros((h, w, 3), np.float32)
        self.alpha = np.zeros((h, w), np.float32)
        self.seed = boil_seed
        self.light = np.array(light, float) / np.hypot(*light)
        self.rimv = np.array(rim, float) / np.hypot(*rim)
        self.rim_col = np.asarray(rim_col, np.float32)
        self.rim_amt = rim_amt
        self.ink_px = ink_px
        self.k = 0

    def _boil(self, pts, amt=1.3):
        self.k += 1
        r = np.random.default_rng(self.seed * 7919 + self.k)
        n = len(pts)
        # smooth jitter: low-frequency so lines wobble, not fizz
        j = r.standard_normal((max(n // 6, 3), 2))
        idx = np.linspace(0, len(j) - 1, n)
        jj = np.stack([np.interp(idx, np.arange(len(j)), j[:, 0]), np.interp(idx, np.arange(len(j)), j[:, 1])], 1)
        return pts + jj * amt * SS

    def _bbox(self, pts, pad):
        x0, y0 = np.floor(pts.min(0) - pad).astype(int); x1, y1 = np.ceil(pts.max(0) + pad).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, self.w), min(y1, self.h)
        return x0, y0, x1, y1

    def _mask(self, pts, box=None):
        if box is None:
            box = (0, 0, self.w, self.h)
        x0, y0, x1, y1 = box
        m = np.zeros((max(y1 - y0, 1), max(x1 - x0, 1)), np.uint8)
        cv2.fillPoly(m, [np.round((pts - [x0, y0]) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
        return m.astype(np.float32) / 255

    @staticmethod
    def _shift(m, v):
        M = np.float32([[1, 0, v[0]], [0, 1, v[1]]])
        return cv2.warpAffine(m, M, (m.shape[1], m.shape[0]))

    def _put(self, box, colr, m):
        x0, y0, x1, y1 = box
        if x1 <= x0 or y1 <= y0:
            return
        c = self.col[y0:y1, x0:x1]
        self.col[y0:y1, x0:x1] = c * (1 - m[..., None]) + colr * m[..., None]
        self.alpha[y0:y1, x0:x1] = np.maximum(self.alpha[y0:y1, x0:x1], m)

    def part(self, pts, base, shade, ink_w=1.0, cel=0.14, size=None, boil=True, ink=True, rim=True, clip=None):
        pts = np.asarray(pts, float) * SS
        if boil:
            pts = self._boil(pts)
        if size is None:
            x0, y0 = pts.min(0); x1, y1 = pts.max(0)
            size = max(x1 - x0, y1 - y0)
        else:
            size = size * SS
        d = max(size * cel, 2.0)
        box = self._bbox(pts, 4)
        if box[2] <= box[0] or box[3] <= box[1]:
            return None
        m = self._mask(pts, box)
        lit = self._shift(m, self.light * d) * m
        colr = np.where(lit[..., None] > 0.5, np.asarray(base, np.float32), np.asarray(shade, np.float32))
        if rim and self.rim_amt > 0:
            rb = m * (1 - self._shift(m, -self.rimv * max(size * 0.06, 2)))
            colr = colr * (1 - rb[..., None] * self.rim_amt) + self.rim_col * rb[..., None] * self.rim_amt
        self._put(box, colr, m)
        if ink:
            self.outline(pts, ink_w)
        return m

    def outline(self, pts, w=1.0, closed=True, col=INK):
        """Variable-width ink: thicker on the shadow side, tapered by a slow noise."""
        pts = np.asarray(pts, float)
        if closed:
            pts = np.vstack([pts, pts[:1]])
        seg = np.diff(pts, axis=0)
        ln = np.hypot(seg[:, 0], seg[:, 1])
        tot = ln.sum()
        n = max(int(tot / (1.2 * SS)), 4)
        s = np.concatenate([[0], np.cumsum(ln)])
        q = np.linspace(0, tot, n)
        P = np.stack([np.interp(q, s, pts[:, 0]), np.interp(q, s, pts[:, 1])], 1)
        tg = np.gradient(P, axis=0)
        nrm = np.stack([tg[:, 1], -tg[:, 0]], 1)
        nrm /= np.hypot(nrm[:, 0], nrm[:, 1])[:, None] + 1e-6
        dark = np.clip(-(nrm @ self.light), 0, 1)
        r = np.random.default_rng(self.seed * 31 + self.k)
        wob = np.interp(np.linspace(0, 9, n), np.arange(10), 0.75 + 0.5 * r.random(10))
        th = self.ink_px * SS * w * (0.55 + 0.9 * dark) * wob
        if not closed:  # taper the ends like a brush
            e = np.minimum(np.linspace(0, 1, n), np.linspace(1, 0, n))
            th *= np.clip(e * 5, 0.15, 1)
        box = self._bbox(P, th.max() + 3)
        x0, y0, x1, y1 = box
        if x1 <= x0 or y1 <= y0:
            return
        lay = np.zeros((y1 - y0, x1 - x0), np.uint8)
        for (x, y), t in zip(P - [x0, y0], th):
            cv2.circle(lay, (int(x * 4), int(y * 4)), max(int(t * 4 / 2), 2), 255, -1, cv2.LINE_AA, shift=2)
        a = lay.astype(np.float32) / 255
        self._put(box, np.asarray(col, np.float32), a)

    def stroke(self, pts, w=1.0, col=INK):
        self.outline(np.asarray(pts, float) * SS, w, closed=False, col=col)

    def fill(self, pts, col, a=1.0):
        pts = np.asarray(pts, float) * SS
        box = self._bbox(pts, 3)
        if box[2] <= box[0] or box[3] <= box[1]:
            return
        m = self._mask(pts, box) * a
        self._put(box, np.asarray(col, np.float32), m)


def composite(dst, ink):
    """dst float32 HxWx3 (0..1). ink layer is SS-times bigger; downsample with area filter."""
    h, w = dst.shape[:2]
    c = cv2.resize(ink.col, (w, h), interpolation=cv2.INTER_AREA)
    a = cv2.resize(ink.alpha, (w, h), interpolation=cv2.INTER_AREA)[..., None]
    return dst * (1 - a) + c * a


# ------------------------------------------------------------------ the guy
def draw_guy(ink, J, to_px, scale, front=False, face_turn=0.6, mouth=1.0, look=(0.3, -0.2), hair_wind=(0, 0), T=0.0, flap=0.0):
    """J: world joints. to_px: world->screen function. scale: px per metre (screen)."""
    P = {k: np.asarray(to_px(v), float) for k, v in J.items()}
    s = scale
    W_ = lambda m: m * s

    def leg(sd):
        dm = 0.78 if (sd == 'F' and not front) else 1.0
        ink.part(limb_poly(P['hp' + sd], P['kn' + sd], W_(0.085), W_(0.07), W_(0.012)), JEANS * dm, JEANS_SH * dm, size=W_(0.4))
        ink.part(limb_poly(P['kn' + sd], P['an' + sd], W_(0.068), W_(0.052), W_(0.01)), JEANS * dm, JEANS_SH * dm, size=W_(0.35))
        # shoe: toe direction = perpendicular to shin, pointing the way he faces
        sv = P['an' + sd] - P['kn' + sd]; sv /= np.hypot(*sv) + 1e-6
        toe = np.array([-sv[1], sv[0]]) if not front else sv
        if not front and toe[0] < 0:
            toe = -toe
        if front:
            ink.part(ellipse_poly(P['an' + sd] + sv * W_(0.05), W_(0.07), W_(0.1), math.atan2(sv[1], sv[0]) + math.pi / 2), SHOE, SHOE_SH, size=W_(0.2))
        else:
            heel = P['an' + sd] - toe * W_(0.05) + sv * W_(0.04)
            tip = P['an' + sd] + toe * W_(0.21) + sv * W_(0.05)
            ink.part(limb_poly(heel, tip, W_(0.055), W_(0.045)), SHOE, SHOE_SH, size=W_(0.2))

    def arm(sd):
        dm = 0.78 if (sd == 'F' and not front) else 1.0
        ink.part(limb_poly(P['sh' + sd], P['el' + sd], W_(0.07), W_(0.058), W_(0.012)), SHIRT * dm, SHIRT_SH * dm, size=W_(0.3))
        ink.part(limb_poly(P['el' + sd], P['wr' + sd], W_(0.05), W_(0.04), W_(0.008)), SKIN * dm, SKIN_SH * dm, size=W_(0.25))
        hv = P['hd' + sd] - P['wr' + sd]; hv /= np.hypot(*hv) + 1e-6
        c = P['wr' + sd] + hv * W_(0.05)
        ink.part(ellipse_poly(c, W_(0.06), W_(0.048), math.atan2(hv[1], hv[0])), SKIN, SKIN_SH, size=W_(0.12))
        # spread fingers (open hand, panic)
        for k in (-40, -12, 15, 42):
            a0 = math.atan2(hv[1], hv[0]) + math.radians(k)
            d = np.array([math.cos(a0), math.sin(a0)])
            ink.part(limb_poly(c + d * W_(0.03), c + d * W_(0.095), W_(0.017), W_(0.014)), SKIN, SKIN_SH, size=W_(0.06), ink_w=0.7)

    def torso():
        hp, nk = P['hip'], P['neck']
        tv = (nk - hp) / (np.hypot(*(nk - hp)) + 1e-6)
        if front:
            pts = limb_poly(hp, P['sho'], W_(0.15), W_(0.2), W_(0.025))
        else:
            pts = limb_poly(hp, P['sho'], W_(0.12), W_(0.13), W_(0.035))
        # shirt hem flapping in the wind
        if flap:
            h = np.array([-tv[1], tv[0]])
            ph = np.linspace(0, 1, 7)
            hem = [hp + h * W_(0.17) * (1 - 2 * u) - tv * W_(0.02 + 0.05 * flap * (0.5 + 0.5 * math.sin(T * 31 + u * 9))) for u in ph]
            pts = np.vstack([pts, hem])
        ink.part(pts, SHIRT, SHIRT_SH, size=W_(0.45))
        # belt line
        sv = np.array([-tv[1], tv[0]])
        w = 0.15 if front else 0.12
        ink.stroke([hp + tv * W_(0.07) + sv * W_(w), hp + tv * W_(0.08) - sv * W_(w)], 0.6)
        ink.part(limb_poly(P['neck'] - tv * W_(0.03), P['neck'] + (P['headc'] - P['neck']) * 0.4, W_(0.045), W_(0.045)), SKIN, SKIN_SH, size=W_(0.1))

    def head():
        hc = P['headc']
        hv = P['headc'] - P['neck']; hv /= np.hypot(*hv) + 1e-6
        rot = math.atan2(hv[1], hv[0]) + math.pi / 2          # head 'up' along hv
        up = hv
        rt = np.array([-up[1], up[0]]) * -1
        if np.dot(rt, [1, 0]) < 0 and not front:
            rt = -rt
        # hair behind (streaming)
        hw = np.asarray(hair_wind, float)
        spikes = []
        for i, a in enumerate(np.linspace(-1.6, 1.6, 9)):
            base = hc + (up * math.cos(a) + rt * math.sin(a)) * W_(0.13)
            tip = hc + (up * math.cos(a) + rt * math.sin(a)) * W_(0.2 + 0.03 * (i % 2)) + hw * W_(0.08) * (1 + 0.3 * math.sin(T * 25 + i))
            spikes += [base, tip]
        ink.part(np.array(spikes + [hc - up * W_(0.02) - rt * W_(0.12), hc - up * W_(0.02) + rt * W_(0.12)]), HAIR, HAIR_SH, size=W_(0.3), ink_w=0.9)
        # skull + jaw
        ink.part(ellipse_poly(hc, W_(0.125), W_(0.145), rot, wob=0.04), SKIN, SKIN_SH, size=W_(0.3))
        # ear (side view)
        if not front:
            ink.part(ellipse_poly(hc - rt * W_(0.035) * face_turn, W_(0.03), W_(0.042), rot), SKIN, SKIN_SH, size=W_(0.06), ink_w=0.8)
        # hair cap on top
        cap = [hc + (up * math.cos(a) + rt * math.sin(a)) * W_(0.15) for a in np.linspace(-1.75, 1.75, 14)]
        cap += [hc + up * W_(0.05) + rt * W_(0.13), hc + up * W_(0.09) + rt * W_(0.0), hc + up * W_(0.05) - rt * W_(0.13)]
        ink.part(np.array(cap), HAIR, HAIR_SH, size=W_(0.25), ink_w=0.9)
        # face
        fx = face_turn
        ec = hc + rt * W_(0.055) * fx * 1.4 + up * W_(0.01)
        lk = np.asarray(look, float)
        for e, sz in ((-1, 0.75 if fx > 0.3 else 1.0), (1, 1.0)):
            p = ec + rt * W_(0.052) * e * (1 - 0.35 * abs(fx))
            if fx > 0.3 and e < 0:
                p = p - rt * W_(0.01)
            eye = ellipse_poly(p, W_(0.033) * sz, W_(0.042), rot)
            ink.part(eye, np.ones(3), np.ones(3) * 0.86, ink_w=0.8, rim=False)
            pp = p + (rt * lk[0] + up * lk[1]) * W_(0.013)
            ink.fill(ellipse_poly(pp, W_(0.0085) * sz, W_(0.0095), rot, n=16), INK)
            ink.fill(ellipse_poly(pp + (rt + up) * W_(0.004), W_(0.004), W_(0.004), n=10), np.ones(3))
            # brows up (fear)
            # worried brows: inner ends pushed up
            b0 = p + up * W_(0.085) - rt * W_(0.028) * sz
            b1 = p + up * W_(0.062) + rt * W_(0.03) * sz
            if e < 0:
                b0, b1 = p + up * W_(0.062) - rt * W_(0.03) * sz, p + up * W_(0.085) + rt * W_(0.028) * sz
            ink.stroke([b0, (b0 + b1) / 2 + up * W_(0.008), b1], 1.2)
        # nose
        nb = ec + rt * W_(0.03) * fx - up * W_(0.035)
        ink.stroke([ec + rt * W_(0.02) * fx, nb + rt * W_(0.025) * max(fx, 0.2), nb - rt * W_(0.005)], 0.8)
        # mouth: open scream with teeth and tongue
        mc = ec + rt * W_(0.012) * fx - up * W_(0.085)
        mo = 0.25 + 0.75 * mouth
        mc = mc - up * W_(0.012) * mo
        mpts = ellipse_poly(mc, W_(0.032), W_(0.05) * mo, rot, n=28)
        ink.part(mpts, np.array([70, 20, 34]) / 255, np.array([50, 12, 26]) / 255, ink_w=0.9, rim=False)
        ink.fill(ellipse_poly(mc + up * W_(0.038) * mo, W_(0.025), W_(0.009), rot, n=16), np.array([1, 1, .97]))
        ink.fill(ellipse_poly(mc - up * W_(0.03) * mo, W_(0.022), W_(0.014) * mo, rot, n=16), np.array([226, 98, 110]) / 255)

    if front:
        for sd in ('F', 'N'):
            leg(sd)
        torso()
        head()
        for sd in ('F', 'N'):
            arm(sd)
    else:
        arm('F'); leg('F')
        torso()
        leg('N')
        head()
        arm('N')
