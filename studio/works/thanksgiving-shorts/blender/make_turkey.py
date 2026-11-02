# Sculpt the turkey as a smooth union of shapes (signed distance field) and save the mesh: turkey_raw.npz (cavity open), turkey_roast.npz
import numpy as np
from skimage import measure

def ell(p, c, r):
    q = (p - np.array(c)) / np.array(r)
    k0 = np.linalg.norm(q, axis=-1); k1 = np.linalg.norm(q / np.array(r), axis=-1)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)

def cap(p, a, b, ra, rb):
    a, b = np.array(a), np.array(b); pa = p - a; ba = b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - (ra + (rb - ra) * h)

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

def smax(a, b, k): return -smin(-a, -b, k)

st = 0.0035
xs = np.arange(-0.32, 0.27, st); ys = np.arange(-0.22, 0.22, st); zs = np.arange(-0.14, 0.2, st)
P = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), -1)

def build(cavity):
    d = ell(P, (0, 0, 0), (0.19, 0.145, 0.105))
    d = smin(d, ell(P, (0.07, 0, 0.045), (0.15, 0.13, 0.085)), 0.04)
    for s in (-1, 1):
        d = smin(d, ell(P, (-0.1, s * 0.105, 0.02), (0.1, 0.062, 0.072)), 0.035)
        d = smin(d, cap(P, (-0.13, s * 0.1, 0.03), (-0.225, s * 0.07, 0.075), 0.05, 0.026), 0.03)
        d = smin(d, ell(P, (-0.238, s * 0.066, 0.081), (0.026, 0.024, 0.024)), 0.012)
        d = smin(d, ell(P, (0.06, s * 0.135, -0.025), (0.11, 0.035, 0.055)), 0.02)
    d = smax(d, -(P[..., 2] + 0.085), 0.02)                  # flat back it rests on
    if cavity:
        d = smax(d, -ell(P, (-0.2, 0, 0.0), (0.06, 0.045, 0.045)), 0.012)
    v, f, n, _ = measure.marching_cubes(d, 0.0, spacing=(st, st, st))
    v += np.array([xs[0], ys[0], zs[0]])
    return v.astype(np.float32), f.astype(np.int32)

for name, cav in (('turkey_raw', True), ('turkey_roast', False)):
    v, f = build(cav); np.savez_compressed(name + '.npz', v=v, f=f); print(name, v.shape, f.shape)
