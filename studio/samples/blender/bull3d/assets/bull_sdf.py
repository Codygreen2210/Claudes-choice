"""Builds the bronze bull's body mesh from a smooth signed-distance sculpt (smooth unions of ellipsoids and round cones),
then marching cubes -> bull.npz (verts, faces, plus the eye / nostril / flank points the scene uses). Run once, locally:
    python3 bull_sdf.py        (needs numpy, scikit-image; the farm only reads bull.npz)
Body along +x (head at +x), feet on z = 0, about 1.4 long, 1.05 tall at the horn tips."""
import os, numpy as np
from skimage import measure
HERE = os.path.dirname(os.path.abspath(__file__))
H = 0.0065
xs = np.arange(-0.68, 0.9, H); ys = np.arange(-0.34, 0.34 + H, H); zs = np.arange(-0.02, 1.12, H)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k): return -smin(-a, -b, k)


def ell(c, r):
    px, py, pz = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    return (np.sqrt(px * px + py * py + pz * pz) - 1.0) * min(r)


def rcone(a, b, ra, rb):
    """round cone: a segment a->b with radius ra at a, rb at b"""
    a = np.array(a, float); b = np.array(b, float); ba = b - a; L2 = ba @ ba
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    h = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0, 1)
    dx, dy, dz = px - ba[0] * h, py - ba[1] * h, pz - ba[2] * h
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * h)


def chain(pts, k=0.02):
    d = None
    for (p0, r0), (p1, r1) in zip(pts, pts[1:]):
        e = rcone(p0, p1, r0, r1); d = e if d is None else smin(d, e, k)
    return d


body = ell((0.0, 0, 0.62), (0.44, 0.215, 0.22))
body = smin(body, ell((0.25, 0, 0.63), (0.25, 0.225, 0.26)), 0.06)          # chest
body = smin(body, ell((0.19, 0, 0.8), (0.22, 0.16, 0.11)), 0.06)            # shoulder hump
body = smin(body, ell((-0.3, 0, 0.67), (0.21, 0.205, 0.2)), 0.06)          # rump
body = smin(body, ell((0.36, 0, 0.5), (0.13, 0.07, 0.13)), 0.05)            # dewlap
body = smin(body, rcone((0.3, 0, 0.72), (0.55, 0, 0.76), 0.2, 0.135), 0.06)  # neck
body = smin(body, rcone((0.56, 0, 0.79), (0.75, 0, 0.64), 0.118, 0.09), 0.05)  # head, face sloping down
body = smin(body, ell((0.765, 0, 0.635), (0.05, 0.075, 0.06)), 0.03)        # muzzle
def rbox(c, hs, r):
    qx, qy, qz = np.abs(X - c[0]) - hs[0], np.abs(Y - c[1]) - hs[1], np.abs(Z - c[2]) - hs[2]
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - r


body = smin(body, rbox((-0.06, 0, 0.63), (0.17, 0.19, 0.14), 0.02), 0.04)   # flat side plates round the door (both flanks)
body = smax(body, np.abs(Y) - 0.212, 0.02)                                   # flat flanks: the door sits on the -y one at y = -0.212
for sy in (-1, 1):
    y = 0.11 * sy
    body = smin(body, chain([((0.27, y, 0.62), 0.1), ((0.29, y, 0.3), 0.056), ((0.3, y, 0.05), 0.048)], 0.02), 0.05)   # fore leg
    body = smin(body, chain([((-0.32, y, 0.64), 0.118), ((-0.39, y, 0.3), 0.054), ((-0.35, y, 0.05), 0.046)], 0.02), 0.05)  # hind leg
    for x_ in (0.3, -0.35): body = smin(body, ell((x_ + 0.012, y, 0.03), (0.055, 0.045, 0.035)), 0.015)                  # hooves
    body = smin(body, ell((0.575, 0.14 * sy, 0.84), (0.028, 0.065, 0.026)), 0.012)                                     # ears
    body = smin(body, chain([((0.6, 0.05 * sy, 0.85), 0.032), ((0.62, 0.17 * sy, 0.9), 0.023), ((0.67, 0.25 * sy, 0.98), 0.013), ((0.73, 0.26 * sy, 1.05), 0.004)], 0.01), 0.015)  # horns
body = smin(body, chain([((-0.49, 0, 0.8), 0.022), ((-0.58, 0, 0.64), 0.016), ((-0.57, 0, 0.36), 0.013)], 0.01), 0.02)       # tail
body = smin(body, ell((-0.57, 0, 0.3), (0.03, 0.03, 0.065)), 0.02)
for sy in (-1, 1):                                                           # eye sockets and nostrils, pressed in
    body = smax(body, -ell((0.655, 0.098 * sy, 0.765), (0.022, 0.03, 0.02)), 0.01)
    body = smax(body, -ell((0.81, 0.035 * sy, 0.63), (0.02, 0.016, 0.016)), 0.008)
body = np.maximum(body, -Z)                                                  # flat feet
v, f, n, _ = measure.marching_cubes(body, 0.0, spacing=(H, H, H))
v += np.array([xs[0], ys[0], zs[0]])
f = f[:, ::-1]                                                               # outward winding for Blender
print('verts', len(v), 'faces', len(f), 'x', v[:, 0].min(), v[:, 0].max(), 'z', v[:, 2].max())
np.savez_compressed(os.path.join(HERE, 'bull.npz'), v=v.astype(np.float32), f=f.astype(np.int32),
                    eyes=np.array([[0.652, -0.088, 0.765], [0.652, 0.088, 0.765]], np.float32),
                    nose=np.array([[0.8, -0.035, 0.63], [0.8, 0.035, 0.63]], np.float32))
