"""Level 1 sample: hand-drawn 2D. Painted backgrounds, jointed rig on twos, boiling ink, perspective tunnel shot.
   python3 l1.py out.mp4 [first_frame last_frame]"""
import sys, os, math, subprocess
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ovl import overlay, W, H, FPS, DUR
from rig import Pose, keyed, joints, Ink, composite, draw_guy, limb_poly, ellipse_poly, ease, INK, SS

R = np.random.default_rng(11)


# ------------------------------------------------------------------ noise
def vnoise(h, w, cell, seed, oct=4):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(oct):
        gh, gw = max(int(h / cell) + 3, 3), max(int(w / cell) + 3, 3)
        g = r.random((gh, gw)).astype(np.float32)
        up = cv2.resize(g, (int(gw * cell), int(gh * cell)), interpolation=cv2.INTER_CUBIC)[:h, :w]
        out += up * amp; tot += amp; amp *= 0.5; cell /= 2
    return out / tot


def n1(x, seed, f=1.0):
    r = np.random.default_rng(seed); k = r.random(64)
    xs = np.asarray(x) * f
    i = np.floor(xs).astype(int); u = xs - i; u = u * u * (3 - 2 * u)
    return k[i % 64] * (1 - u) + k[(i + 1) % 64] * u - 0.5


def strokes(img, n, size, seed, angle_fn, region=None, jit=0.06, alpha_len=(1.0, 3.5)):
    """Stamp n brush strokes, colour sampled from img itself (+ value jitter)."""
    r = np.random.default_rng(seed)
    h, w = img.shape[:2]
    xs, ys = r.integers(0, w, n), r.integers(0, h, n)
    for x, y in zip(xs, ys):
        if region is not None and not region[y, x]:
            continue
        c = img[y, x].astype(np.float32) * (1 + r.normal(0, jit)) + r.normal(0, jit * 0.4, 3)
        L = size * r.uniform(*alpha_len); Wd = size * r.uniform(0.35, 0.7)
        a = angle_fn(x, y) + r.normal(0, 12)
        cv2.ellipse(img, (int(x), int(y)), (int(L), max(int(Wd), 1)), a, 0, 360, tuple(np.clip(c, 0, 1).tolist()), -1, cv2.LINE_AA)


def paper(h, w):
    g = 1 - 0.05 * vnoise(h, w, 3, 5, 3) - 0.03 * vnoise(h, w, 40, 6, 2)
    fib = cv2.resize(np.random.default_rng(7).random((h // 6, w // 1)).astype(np.float32), (w, h))
    g -= 0.025 * (fib > 0.985)
    return np.clip(g, 0.85, 1.0)[..., None] * np.array([1.0, 0.985, 0.95], np.float32)


PAPER = paper(H, W)

# ------------------------------------------------------------------ shot A world painting (world metres, y up)
PX = 260
WX0, WX1, WY0, WY1 = -4.0, 7.0, -9.0, 5.0
CHUNK = np.array([(-0.26, 0.01), (0.04, 0.02), (0.08, -0.08), (0.01, -0.24), (-0.13, -0.3), (-0.22, -0.15)])


def face_x(y):
    return 0.03 + 0.14 * n1(y, 3, 1.6) + 0.025 * y


def top_y(x):
    return 0.0 + 0.05 * n1(x, 4, 2.0) + 0.02 * n1(x, 9, 7)


def far_top(x):
    return 0.88 + 0.16 * n1(x, 5, 0.8) + 0.035 * n1(x, 8, 2.2)


def build_painting():
    w, h = int((WX1 - WX0) * PX), int((WY1 - WY0) * PX)
    xs = WX0 + (np.arange(w) + 0.5) / PX
    ys = WY1 - (np.arange(h) + 0.5) / PX
    X, Y = np.meshgrid(xs, ys)
    img = np.zeros((h, w, 3), np.float32)
    # sky: dusk, glow low
    k = np.clip((Y - 0.5) / 4.5, 0, 1)[..., None]
    img[:] = (1 - k) * np.array([0.78, 0.38, 0.30]) + k * np.array([0.16, 0.12, 0.28])
    cl = vnoise(h, w, 420, 21, 3)
    bands = cv2.resize(np.random.default_rng(24).random((40, 6)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    img = img * (0.88 + 0.16 * cl[..., None] + 0.08 * bands[..., None])
    hz = np.exp(-((Y - 0.95) / 0.5) ** 2)[..., None]
    img = img + hz * np.array([0.35, 0.12, 0.02])
    sky = Y > far_top(X)
    # far wall: hazy, lit from below
    gl = np.clip((-Y + 1.5) / 7.5, 0, 1)[..., None]
    ribs = cv2.resize(np.random.default_rng(25).random((8, int((WX1 - WX0) * 3))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    rock = (0.55 * vnoise(h, w, 120, 22, 3) + 0.45 * ribs)[..., None]
    far = (np.array([0.24, 0.16, 0.24]) * (0.7 + 0.6 * rock)) * (1 - gl) + np.array([0.95, 0.42, 0.16]) * gl * (0.75 + 0.5 * rock)
    far = far * 0.7 + np.array([0.42, 0.2, 0.26]) * 0.3
    img = np.where(sky[..., None], img, far)
    # near rim rock
    near = (X < face_x(Y)) & (Y < top_y(X))
    cx = (X > CHUNK[:, 0].min() - 0.02) & (X < CHUNK[:, 0].max() + 0.02) & (Y > -0.32) & (Y < 0.03)
    chunk_m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(chunk_m, [np.round(np.stack([(CHUNK[:, 0] - WX0) * PX, (WY1 - CHUNK[:, 1]) * PX], 1)).astype(np.int32)], 1)
    near &= ~(chunk_m.astype(bool))
    rr = vnoise(h, w, 50, 23)[..., None]
    lit_face = np.clip(1 - (face_x(Y) - X) / 0.6, 0, 1)[..., None] * np.clip(-Y / 2, 0.2, 1)[..., None]
    top_lit = np.clip(1 - (top_y(X) - Y) / 0.25, 0, 1)[..., None]
    nr = np.array([0.17, 0.13, 0.19]) * (0.65 + 0.7 * rr) + top_lit * np.array([0.25, 0.2, 0.32]) + lit_face * np.array([0.7, 0.28, 0.08])
    img = np.where(near[..., None], nr, img)
    img = np.clip(img, 0, 1).astype(np.float32)
    # brushwork
    sk = img.copy()
    strokes(sk, 5000, 34, 31, lambda x, y: 0, region=sky, jit=0.03, alpha_len=(1.5, 3.5))
    strokes(img, 9000, 15, 32, lambda x, y: 90, region=~sky & ~near, jit=0.035, alpha_len=(0.8, 1.6))
    sm = cv2.GaussianBlur(sky.astype(np.float32), (0, 0), 2.0)[..., None]
    img = sk * sm + img * (1 - sm)
    strokes(img, 12000, 12, 33, lambda x, y: -25, region=near, jit=0.05)
    strokes(img, 12000, 6, 34, lambda x, y: -25, region=near, jit=0.07)
    img = cv2.GaussianBlur(img, (0, 0), 1.3)
    # ink: rim silhouette + far wall line + cracks
    def to_p(px, py):
        return np.stack([(np.asarray(px) - WX0) * PX, (WY1 - np.asarray(py)) * PX], 1)
    lay = np.zeros((h, w), np.float32)
    xx = np.linspace(WX0, -0.26, 300); top = to_p(xx, top_y(xx))
    yy = np.linspace(-0.3, WY0, 400); face = to_p(face_x(yy), yy)
    for pts, th in ((top, 9), (face, 10)):
        for i in range(len(pts) - 1):
            t = th * (0.7 + 0.6 * abs(n1(i * 0.05, 40)))
            cv2.line(lay, tuple(np.int32(pts[i])), tuple(np.int32(pts[i + 1])), 1.0, int(t), cv2.LINE_AA)
    xf = np.linspace(WX0, WX1, 400); fp = to_p(xf, far_top(xf))
    farlay = np.zeros((h, w), np.float32)
    cv2.polylines(farlay, [np.int32(fp)], False, 1.0, 5, cv2.LINE_AA)
    r = np.random.default_rng(41)
    for _ in range(60):          # cracks in the near rock
        x0, y0 = r.uniform(-3.8, -0.3), r.uniform(-8, -0.1)
        if not (x0 < face_x(y0) - 0.1 and y0 < top_y(x0) - 0.05):
            continue
        pts = [(x0, y0)]; a = r.uniform(-2.2, -0.6)
        for _ in range(r.integers(4, 10)):
            a += r.normal(0, 0.5); pts.append((pts[-1][0] + 0.09 * math.cos(a), pts[-1][1] + 0.09 * math.sin(a)))
        cv2.polylines(lay, [np.int32(to_p(*np.array(pts).T))], False, 0.9, 4, cv2.LINE_AA)
    for _ in range(50):          # far-wall strata (light, hazy)
        x0, y0 = r.uniform(0.5, 7), r.uniform(-8.5, 0.8)
        pts = to_p(np.linspace(x0, x0 + r.uniform(0.6, 1.8), 12), y0 + 0.08 * np.sin(np.linspace(0, 3, 12)))
        cv2.polylines(farlay, [np.int32(pts)], False, 0.6, 3, cv2.LINE_AA)
    img = img * (1 - lay[..., None]) + INK * lay[..., None]
    img = img * (1 - 0.45 * farlay[..., None]) + np.array([0.3, 0.14, 0.22]) * 0.45 * farlay[..., None]
    return np.clip(img, 0, 1).astype(np.float32)


# ------------------------------------------------------------------ shot B tunnel texture (angle x depth)
TEX_PXM = 40
F_PX, RC = 520.0, 30.0


def build_tunnel():
    hA, wD = 1536, int(92 * TEX_PXM)
    d = np.arange(wD) / TEX_PXM
    band = 0.6 + 0.4 * (n1(d, 51, 0.7) + 0.5)
    base = np.array([0.30, 0.22, 0.28])
    rr = vnoise(hA, wD, 70, 52)
    img = base * (0.55 + 0.8 * rr[..., None]) * band[None, :, None]
    img = img.astype(np.float32)
    strokes(img, 26000, 10, 53, lambda x, y: 0)     # along depth = radial on screen
    strokes(img, 9000, 8, 54, lambda x, y: 90)
    lay = np.zeros((hA, wD), np.float32)
    r = np.random.default_rng(55)
    for _ in range(320):        # cracks: radial streaks on screen
        y0, x0 = r.uniform(0, hA), r.uniform(0, wD)
        ln = r.uniform(40, 240)
        pts = np.stack([x0 + np.linspace(0, ln, 8), y0 + np.cumsum(r.normal(0, 4, 8))], 1)
        cv2.polylines(lay, [np.int32(pts)], False, 1.0, int(r.integers(2, 5)), cv2.LINE_AA)
    for k in range(0, wD, 90):  # strata ledges: rings on screen
        y = np.arange(0, hA, 16)
        pts = np.stack([k + 14 * n1(y * 0.02, 56 + k) + r.normal(0, 1, len(y)), y], 1)
        cv2.polylines(lay, [np.int32(pts)], False, 0.8, 3, cv2.LINE_AA)
    img = img * (1 - lay[..., None]) + INK * lay[..., None]
    return np.clip(img, 0, 1)


# ------------------------------------------------------------------ choreography
def P(hip, **k):
    return Pose(hip, **k)


KEYS_A = [
    (0.00, P((-0.43, 0.925), torso=81, head=64, uaN=-82, faN=-70, uaF=-100, faF=-96, thN=-73, shN=-77, thF=-101, shF=-104, mouth=0.05)),
    (0.62, P((-0.39, 0.915), torso=73, head=50, uaN=-70, faN=-48, uaF=-104, faF=-92, thN=-72, shN=-79, thF=-99, shF=-104, mouth=0.1)),
    (0.76, P((-0.38, 0.91), torso=72, head=52, uaN=-68, faN=-46, uaF=-104, faF=-92, thN=-72, shN=-79, thF=-99, shF=-104, mouth=0.2)),
    (0.88, P((-0.31, 0.80), torso=64, head=98, uaN=35, faN=72, uaF=140, faF=112, thN=-48, shN=-82, thF=-112, shF=-104, mouth=0.85)),
    (1.06, P((-0.15, 0.60), torso=38, head=78, uaN=112, faN=150, uaF=22, faF=-12, thN=-42, shN=-66, thF=-128, shF=-146, mouth=1.0)),
    (1.30, P((0.12, 0.34), torso=4, head=30, uaN=176, faN=205, uaF=124, faF=146, thN=-152, shN=-174, thF=172, shF=150, mouth=1.0)),
]
T_AIR = 1.30
V_AIR = np.array([0.9, -1.2])
G = 9.81
CUT = 1.86


def hip_air(t):
    tau = t - T_AIR
    p0 = KEYS_A[-1][1].hip
    return p0 + V_AIR * tau + np.array([0, -0.5 * G * tau * tau])


def pose_A(t):
    if t <= T_AIR:
        return keyed(KEYS_A, t)
    p = Pose.lerp(KEYS_A[-1][1], KEYS_A[-1][1], 0)
    tau = t - T_AIR
    p.hip = hip_air(t)
    rot = -70 * tau
    for k in Pose.KEYS[:11] + ['ftF']:
        setattr(p, k, getattr(p, k) + rot)
    p.uaN += 25 * math.sin(tau * 14); p.faN += 35 * math.sin(tau * 14 + 1)
    p.uaF += 25 * math.sin(tau * 12 + 2); p.faF += 30 * math.sin(tau * 12 + 3)
    p.thN += 18 * math.sin(tau * 9); p.shN += 25 * math.sin(tau * 9 + 1)
    p.thF += 18 * math.sin(tau * 9 + 2); p.shF += 25 * math.sin(tau * 9 + 3)
    return p


def pose_B(t):
    w = t * 1.0
    roll = 14 * math.sin(1.4 * t) + 6 * math.sin(3.1 * t)
    p = P((0, 0), torso=90 + roll, head=90 + roll + 10 * math.sin(4 * t),
          uaN=148 + 22 * math.sin(9 * w), faN=172 + 34 * math.sin(9 * w + 1.2),
          uaF=32 - 22 * math.sin(9 * w + 0.6), faF=8 - 34 * math.sin(9 * w + 1.8),
          thN=-112 + 14 * math.sin(7 * w), shN=-102 + 22 * math.sin(7 * w + 1),
          thF=-68 - 14 * math.sin(7 * w + 2), shF=-78 - 22 * math.sin(7 * w + 3),
          mouth=0.9 + 0.1 * math.sin(11 * t))
    for k in ('uaN', 'faN', 'uaF', 'faF', 'thN', 'shN', 'thF', 'shF'):
        setattr(p, k, getattr(p, k) + roll)
    return p


def depth(t):  # metres below the rim (hip)
    if t <= T_AIR:
        return 0.0
    return -(hip_air(t)[1])


def speed(t):
    if t <= T_AIR:
        return 0.0
    tau = t - T_AIR
    return math.hypot(V_AIR[0], -V_AIR[1] + G * tau)


# ------------------------------------------------------------------ rendering
class Cam:
    def __init__(self):
        self.c = np.array([0.06, 0.72]); self.s = 395.0; self.last = -1


def cam_A(t, st):
    if t < 0.76:
        tgt = np.array([0.06 + 0.05 * t, 0.72]); s = 395 + 25 * t
        st.c = tgt; st.s = s
    else:
        hp = pose_A(t).hip
        tgt = hp + np.array([0.3, -0.2])
        a = 1 - math.exp(-(1 / FPS) * 7.0)
        st.c = st.c + (tgt - st.c) * a
        st.s += (340 - st.s) * a
    sh = np.zeros(2)
    if 0.76 <= t < 1.2:
        k = 1 - (t - 0.76) / 0.44
        sh = np.array([math.sin(t * 91), math.cos(t * 77)]) * 11 * k * k
    return st.c.copy(), st.s, sh


def warm(c, k):
    return np.clip(c * (1 - k) + np.array([1.0, 0.55, 0.3], np.float32) * c * 1.4 * k, 0, 1)


def frame_A(t, i, PAINT, st, cam=None):
    c, s, sh = cam if cam is not None else cam_A(t, st)
    # world->screen
    def to_px(v):
        return np.array([W / 2 + (v[0] - c[0]) * s + sh[0], H / 2 - (v[1] - c[1]) * s + sh[1]])
    # painting -> screen affine
    a = s / PX
    tx = W / 2 + (WX0 - c[0]) * s + sh[0]
    ty = H / 2 - (WY1 - c[1]) * s + sh[1]
    M = np.float32([[a, 0, tx], [0, a, ty]])
    img = cv2.warpAffine(PAINT, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # flicker of the lava glow from below
    fl = 1 + 0.05 * math.sin(t * 13) + 0.03 * math.sin(t * 29)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = img * (1 + (fl - 1) * yy)
    tq = math.floor(t * 15) / 15                 # character on twos
    p = pose_A(tq)
    J = joints(p)
    pts = np.array([to_px(v) for v in J.values()])
    x0, y0 = (pts.min(0) - 0.45 * s).astype(int); x1, y1 = (pts.max(0) + 0.45 * s).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    k_air = np.clip((t - 0.9) / 0.9, 0, 1)
    ink = Ink((y1 - y0) * SS, (x1 - x0) * SS, boil_seed=i // 2, light=(0.55, 0.83), rim=(-0.6, -0.8),
              rim_col=np.array([0.62, 0.6, 0.95]), rim_amt=0.55, ink_px=3.0)
    loc = lambda v: to_px(v) - np.array([x0, y0])
    # rock chunk + pebbles
    if t < 0.76:
        ch = [loc(v) for v in CHUNK]
    else:
        tau = t - 0.76
        ctr = CHUNK.mean(0)
        rot = -2.2 * tau
        cr, sr = math.cos(rot), math.sin(rot)
        off = np.array([0.35 * tau, -0.5 * G * tau * tau])
        ch = [loc(ctr + off + np.array([cr * (v[0] - ctr[0]) - sr * (v[1] - ctr[1]), sr * (v[0] - ctr[0]) + cr * (v[1] - ctr[1])])) for v in CHUNK]
    ch = np.array(ch)
    r = np.random.default_rng(3)
    peb = []
    if t >= 0.76:
        tau = t - 0.76
        for j in range(9):
            v0 = np.array([r.uniform(-0.2, 0.9), r.uniform(-0.2, 1.2)])
            p0 = np.array([r.uniform(-0.25, 0.05), r.uniform(-0.1, 0.02)])
            pp = p0 + v0 * tau + np.array([0, -0.5 * G * tau * tau])
            peb.append((loc(pp), r.uniform(0.018, 0.04) * s))
    draw_guy(ink, J, loc, s, front=False, face_turn=0.62 if t < 0.82 else 0.35, mouth=p.mouth,
             look=(0.6, -0.6) if t < 0.8 else (0.0, 0.5), hair_wind=(0, k_air * 1.0) if t > 1.0 else (0, 0), T=t, flap=k_air)
    rockc = np.array([0.24, 0.19, 0.26]); rocksh = np.array([0.12, 0.09, 0.14])
    ink.part(ch, rockc, rocksh, size=0.3 * s, ink_w=1.3)
    for (q, rad) in peb:
        ink.part(ellipse_poly(q, rad, rad * 0.8, n=7, wob=0.2), rockc, rocksh, size=rad * 2, ink_w=0.8)
    sub = composite(img[y0:y1, x0:x1], ink)
    img[y0:y1, x0:x1] = sub
    # warm bounce on him grows as he drops toward the glow
    return img


def sparks(img, t, seed, n=24, area=(0, 1)):
    r = np.random.default_rng(seed)
    lay = np.zeros(img.shape[:2], np.float32)
    for j in range(n):
        ph = r.random(); sp = r.uniform(0.25, 0.6)
        u = (t * sp + ph) % 1.0
        x = r.uniform(0, W) + 40 * math.sin(t * 2 + j)
        y = H * (area[1] - (area[1] - area[0]) * u)
        cv2.circle(lay, (int(x), int(y)), int(r.uniform(3, 7)), 1.0, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 2) * 1.6 + lay
    return img + lay[..., None] * np.array([1.0, 0.6, 0.2], np.float32)


def smoke(img, t, seed, n=6):
    r = np.random.default_rng(seed)
    lay = np.zeros((H // 4, W // 4), np.float32)
    for j in range(n):
        x = r.uniform(0.2, 1.0) * W / 4 + 10 * math.sin(t + j)
        y = (H / 4) * (1.1 - ((t * r.uniform(0.04, 0.08) + r.random()) % 1.0) * 1.3)
        cv2.ellipse(lay, (int(x), int(y)), (int(r.uniform(40, 90)), int(r.uniform(18, 40))), r.uniform(-20, 20), 0, 360, 1.0, -1)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 9), (W, H))[..., None] * 0.22
    return img * (1 - lay) + np.array([0.75, 0.5, 0.5], np.float32) * lay


MAPY = {}


def frame_B(t, i, TEX, st):
    d = depth(t)
    D = d + 5.5
    v = speed(t)
    cx, cy = 540 + 26 * math.sin(t * 1.3), 820 + 18 * math.sin(t * 0.9)
    A, Rn = TEX.shape[0], 1320
    r = np.arange(Rn, dtype=np.float32) + 1
    z = F_PX * RC / r
    vv = D - z
    acc = np.zeros((A, Rn, 3), np.float32)
    ns = 5
    mapy = MAPY.get((A, Rn))
    if mapy is None:
        mapy = MAPY[(A, Rn)] = np.ascontiguousarray(np.broadcast_to(np.arange(A, dtype=np.float32)[:, None], (A, Rn)))
    for k in range(ns):
        vk = vv - v * (k / ns) / FPS
        mapx = np.ascontiguousarray(np.broadcast_to((np.clip(vk, 0, None) * TEX_PXM).astype(np.float32)[None, :], (A, Rn)))
        acc += cv2.remap(TEX, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    wall = acc / ns
    jag = 0.5 + 0.9 * (n1(np.arange(A) / A * 40, 61) + 0.5)
    sky_m = (vv[None, :] - jag[:, None]) < 0
    glow = np.exp(-(80 - np.clip(vv, 0, 80)) / 30)[None, :, None]
    near_c = np.exp(-z / 14)[None, :, None]
    amb = np.array([0.42, 0.36, 0.55], np.float32); gc = np.array([1.25, 0.55, 0.2], np.float32)
    lit = wall * (amb * 0.8 + gc * (2.2 * glow + 1.8 * near_c))
    rr = (r / Rn)[None, :, None]
    sky = np.array([0.30, 0.18, 0.36], np.float32) * (1 - rr) + np.array([0.85, 0.42, 0.32], np.float32) * rr
    sky = np.broadcast_to(sky, (A, Rn, 3))
    pol = np.where(sky_m[..., None], sky, lit).astype(np.float32)
    # inked rim silhouette
    edge = np.abs(vv[None, :] - jag[:, None]) < (0.06 + 0.002 * r[None, :])
    pol[edge] = INK
    img = cv2.warpPolar(pol, (W, H), (cx, cy), Rn, cv2.WARP_INVERSE_MAP + cv2.WARP_POLAR_LINEAR + cv2.INTER_LINEAR)
    # radial speed lines (drawn, light)
    rs = np.random.default_rng(i // 2)
    lay = np.zeros((H, W), np.float32)
    for j in range(int(10 + v * 1.2)):
        a = rs.uniform(0, 2 * math.pi); r0 = rs.uniform(260, 900); ln = rs.uniform(120, 420) * min(v / 20, 1.4)
        p0 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a)); p1 = (cx + (r0 + ln) * math.cos(a), cy + (r0 + ln) * math.sin(a))
        cv2.line(lay, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 1.0, int(rs.integers(2, 6)), cv2.LINE_AA)
    img = img * (1 - 0.55 * lay[..., None]) + np.array([1.0, 0.85, 0.65], np.float32) * 0.55 * lay[..., None]
    img = smoke(img, t, 71, 5)
    # the guy, front view, from below
    tq = math.floor(t * 15) / 15
    p = pose_B(tq)
    s = 560 + 25 * (t - CUT)
    hipc = np.array([540 + 14 * math.sin(t * 2.1), 1040 + 10 * math.sin(t * 1.7)])
    J = joints(p, front=True)
    to_px = lambda q: hipc + np.array([q[0], -q[1]]) * s
    pts = np.array([to_px(q) for q in J.values()])
    x0, y0 = (pts.min(0) - 0.4 * s).astype(int); x1, y1 = (pts.max(0) + 0.4 * s).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    gk = min(1.0, 0.35 + d / 80)
    ink = Ink((y1 - y0) * SS, (x1 - x0) * SS, boil_seed=1000 + i // 2, light=(0.15, 0.99), rim=(0.0, -1.0),
              rim_col=np.array([0.55, 0.5, 0.95]), rim_amt=0.6, ink_px=3.4)
    loc = lambda q: to_px(q) - np.array([x0, y0])
    draw_guy(ink, J, loc, s, front=True, face_turn=0.0, mouth=p.mouth, look=(0.0, -0.4), hair_wind=(0, -1.0), T=t, flap=0.0)
    lay = composite(np.zeros((y1 - y0, x1 - x0, 3), np.float32), ink)
    a = cv2.resize(ink.alpha, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)[..., None]
    lay = warm(lay, 0.25 + 0.45 * gk)
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + lay * a
    img = sparks(img, t, 81, 18)
    return img


def finish(img, t):
    img = np.clip(img, 0, 1.2)
    img = img / (1 + 0.15 * np.clip(img - 0.85, 0, None))
    img = img * PAPER
    return np.clip(img * 255, 0, 255).astype(np.uint8)


VIG = None
PAINT = TEX = CAMS = None


def cached_backgrounds():
    """The painted backdrops take ~12 s to build; keep them on disk, keyed by the code that makes them."""
    import hashlib, inspect, os
    src = ''.join(inspect.getsource(f) for f in (vnoise, n1, strokes, face_x, top_y, far_top, build_painting, build_tunnel))
    key = hashlib.sha1((src + repr((PX, WX0, WX1, WY0, WY1, TEX_PXM, CHUNK.tolist()))).encode()).hexdigest()[:12]
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache'); os.makedirs(d, exist_ok=True)
    fp, ft = os.path.join(d, f'paint_{key}.npy'), os.path.join(d, f'tunnel_{key}.npy')
    if os.path.exists(fp) and os.path.exists(ft):
        return np.load(fp), np.load(ft)
    P, T = build_painting(), build_tunnel()
    np.save(fp, P); np.save(ft, T)
    return P, T


def render_frame(i):
    t = i / FPS
    if t < CUT:
        img = frame_A(t, i, PAINT, None, CAMS[i])
        img = sparks(img, t, 91, 14, area=(0.45, 1.05))
        img = smoke(img, t, 72, 4)
        if t > CUT - 2 / FPS:   # hand-drawn smear frames into the cut
            img = cv2.blur(img, (1, 61))
    else:
        img = frame_B(t, i, TEX, None)
        if t < CUT + 2 / FPS:
            img = cv2.blur(img, (1, 61))
    img = np.clip(img * VIG, 0, None)
    return overlay(finish(img, t), t).tobytes()


def main():
    import multiprocessing as mp
    global PAINT, TEX, CAMS, VIG
    out = sys.argv[1]
    f0, f1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, int(DUR * FPS))
    PAINT, TEX = cached_backgrounds()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    VIG = (1 - 0.35 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2))[..., None]
    st = Cam(); CAMS = {}
    for i in range(0, f1):            # the follow camera has memory, so walk it in order first (cheap)
        t = i / FPS
        if t < CUT:
            CAMS[i] = cam_A(t, st)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    with mp.get_context('fork').Pool(int(os.environ.get('JOBS', os.cpu_count() or 2))) as pool:   # frames on every core
        for k, fr in enumerate(pool.imap(render_frame, range(f0, f1), chunksize=2)):
            ff.stdin.write(fr)
            if k % 15 == 0:
                print('frame', f0 + k, flush=True)
    ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    main()
