"""A golden retriever for the 3D Shorts: one smooth skinned body (signed distance shapes -> marching cubes), floppy ears as
their own pieces, a dog skeleton and skin weights blended between the shapes. Facing +z, standing, root on the floor.
    python3 char/dog.py            -> web/char/dog.json   (bones, meshes: position, normal, color, skin index/weight, index)"""
import json, os, time
import numpy as np
from skimage import measure
import trimesh
import fast_simplification

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web', 'char', 'dog.json')
GOLD, LIGHT, NOSE, PAD = (0.80, 0.56, 0.27), (0.90, 0.74, 0.47), (0.06, 0.04, 0.04), (0.18, 0.12, 0.1)

# ------------------------------------------------------------------ skeleton (head positions; each bone points at its first child)
BONES = [('body', None, (0, 0.45, -0.05)), ('chest', 'body', (0, 0.45, 0.15)), ('neck', 'chest', (0, 0.56, 0.31)), ('head', 'neck', (0, 0.7, 0.42)),
         ('jaw', 'head', (0, 0.668, 0.49)), ('earR', 'head', (-0.088, 0.765, 0.415)), ('earL', 'head', (0.088, 0.765, 0.415))]
for S, sx in (('R', -1), ('L', 1)):
    BONES += [('F1' + S, 'chest', (sx * 0.085, 0.42, 0.21)), ('F2' + S, 'F1' + S, (sx * 0.085, 0.23, 0.225)), ('F3' + S, 'F2' + S, (sx * 0.085, 0.05, 0.235)),
              ('B1' + S, 'body', (sx * 0.09, 0.45, -0.28)), ('B2' + S, 'B1' + S, (sx * 0.09, 0.27, -0.2)), ('B3' + S, 'B2' + S, (sx * 0.09, 0.13, -0.31)), ('B4' + S, 'B3' + S, (sx * 0.09, 0.04, -0.295))]
TAIL = [(0, 0.53, -0.4), (0, 0.5, -0.47), (0, 0.45, -0.53), (0, 0.39, -0.58), (0, 0.32, -0.61), (0, 0.25, -0.62)]
for i in range(5):
    BONES.append(('t%d' % (i + 1), 'body' if i == 0 else 't%d' % i, TAIL[i]))
BI = {b[0]: i for i, b in enumerate(BONES)}


# ------------------------------------------------------------------ shapes
def ell(c, r):
    c, r = np.asarray(c, np.float32), np.asarray(r, np.float32)
    def f(P):
        q = (P - c) / r
        k0 = np.linalg.norm(q, axis=-1); k1 = np.linalg.norm(q / r, axis=-1)
        return k0 * (k0 - 1) / np.maximum(k1, 1e-6)
    return f


def cone(a, b, ra, rb):                                         # round cone (capsule with two radii)
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    def f(P):
        ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        return np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - (ra + (rb - ra) * t)
    return f


B = dict((n, np.array(h, np.float32)) for n, _, h in BONES)
PARTS = []                                                      # (name, sdf, bone, color, k)
def part(name, f, bone, col=GOLD, k=0.035): PARTS.append((name, f, bone, col, k))

part('torso', cone((0, 0.47, -0.27), (0, 0.46, 0.15), 0.14, 0.15), 'body')
part('chest', ell((0, 0.43, 0.19), (0.14, 0.18, 0.16)), 'chest')
part('brisket', ell((0, 0.37, 0.12), (0.11, 0.1, 0.15)), 'chest', LIGHT)
part('belly', ell((0, 0.4, -0.07), (0.11, 0.08, 0.17)), 'body')
part('rump', ell((0, 0.47, -0.27), (0.135, 0.14, 0.15)), 'body')
part('neck', cone((0, 0.5, 0.24), (0, 0.68, 0.385), 0.095, 0.08), 'neck')
part('ruff', ell((0, 0.52, 0.31), (0.09, 0.11, 0.08)), 'neck', LIGHT, 0.04)
part('skull', ell((0, 0.728, 0.42), (0.082, 0.078, 0.1)), 'head', k=0.03)
part('muzzle', cone((0, 0.703, 0.49), (0, 0.688, 0.625), 0.05, 0.04), 'head', LIGHT, 0.025)
part('cheeks', ell((0, 0.69, 0.47), (0.075, 0.05, 0.06)), 'head', GOLD, 0.03)
part('jaw', cone((0, 0.665, 0.48), (0, 0.66, 0.605), 0.035, 0.027), 'jaw', LIGHT, 0.012)
part('nose', ell((0, 0.7, 0.662), (0.027, 0.021, 0.02)), 'head', NOSE, 0.008)
for S, sx in (('R', -1), ('L', 1)):
    x = sx * 0.085
    part('fu' + S, cone((x, 0.44, 0.21), (x, 0.23, 0.225), 0.05, 0.04), 'F1' + S, k=0.03)
    part('fl' + S, cone((x, 0.23, 0.225), (x, 0.055, 0.235), 0.038, 0.034), 'F2' + S, k=0.02)
    part('fp' + S, ell((x, 0.03, 0.255), (0.04, 0.028, 0.055)), 'F3' + S, LIGHT, 0.015)
    part('feather' + S, ell((x, 0.34, 0.19), (0.04, 0.09, 0.05)), 'F1' + S, LIGHT, 0.03)
    x = sx * 0.09
    part('th' + S, ell((x, 0.39, -0.25), (0.068, 0.13, 0.095)), 'B1' + S, k=0.04)
    part('st' + S, cone((x, 0.28, -0.205), (x, 0.13, -0.31), 0.048, 0.036), 'B2' + S, k=0.02)
    part('mt' + S, cone((x, 0.13, -0.31), (x, 0.045, -0.29), 0.034, 0.032), 'B3' + S, k=0.015)
    part('bp' + S, ell((x, 0.03, -0.272), (0.04, 0.027, 0.052)), 'B4' + S, LIGHT, 0.015)
for i in range(5):
    r0, r1 = 0.038 - 0.003 * i, 0.035 - 0.003 * i
    part('tail%d' % i, cone(TAIL[i], TAIL[i + 1], r0, r1), 't%d' % (i + 1), GOLD if i < 2 else LIGHT, 0.02)
    part('tf%d' % i, ell(np.add(TAIL[i], TAIL[i + 1]) / 2 + np.array([0, -0.02, -0.01]), (0.03, 0.03, 0.045)), 't%d' % (i + 1), LIGHT, 0.02)


def smin_all(ds, ks):                                           # smooth union of all parts (order-independent enough here)
    d = ds[0]
    for x, k in zip(ds[1:], ks[1:]):
        h = np.clip(0.5 + 0.5 * (x - d) / k, 0, 1)
        d = x * (1 - h) + d * h - k * h * (1 - h)
    return d


def mesh(parts, lo, hi, step):
    lo, hi = np.asarray(lo, np.float32), np.asarray(hi, np.float32)
    n = np.ceil((hi - lo) / step).astype(int) + 1
    xs, ys, zs = [lo[i] + np.arange(n[i], dtype=np.float32) * step for i in range(3)]
    vol = np.empty(tuple(n), np.float32)
    for j, y in enumerate(ys):
        X, Z = np.meshgrid(xs, zs, indexing='ij'); P = np.stack([X, np.full_like(X, y), Z], -1)
        vol[:, j, :] = smin_all([p[1](P) for p in parts], [p[4] for p in parts])
    v, f, _, _ = measure.marching_cubes(vol, 0.0, spacing=(step, step, step))
    m = trimesh.Trimesh(v + lo, f, process=True)
    trimesh.smoothing.filter_taubin(m, iterations=12)
    return m


def skin(V, parts):
    """Each vertex blends the bones of the shapes it sits closest to (softmin over the shapes' distances)."""
    D = np.stack([p[1](V) for p in parts], -1)                    # (n, parts)
    w = np.exp(-(D - D.min(-1, keepdims=True)) / 0.012)
    W = np.zeros((len(V), len(BONES)), np.float32); C = np.zeros((len(V), 3), np.float32)
    for j, p in enumerate(parts):
        W[:, BI[p[2]]] += w[:, j]; C += w[:, j:j + 1] * np.array(p[3], np.float32)
    C /= w.sum(-1, keepdims=True)
    idx = np.argsort(-W, axis=1)[:, :4]; sw = np.take_along_axis(W, idx, 1); sw /= sw.sum(1, keepdims=True)
    return idx, sw, C


def pack(name, m, parts=None, bone=None, color=GOLD):
    V = np.asarray(m.vertices, np.float32)
    if parts:
        si, sw, C = skin(V, parts)
    else:
        si = np.zeros((len(V), 4), int); si[:, 0] = BI[bone]; sw = np.zeros((len(V), 4), np.float32); sw[:, 0] = 1; C = np.tile(np.array(color, np.float32), (len(V), 1))
    N = np.asarray(m.vertex_normals, np.float32)
    r = lambda a, d=4: np.round(a, d).ravel().tolist()
    return {'name': name, 'pos': r(V), 'nrm': r(N, 3), 'col': r(C, 3), 'si': si.astype(int).ravel().tolist(), 'sw': r(sw, 3), 'idx': np.asarray(m.faces, int).ravel().tolist()}


if __name__ == '__main__':
    t0 = time.time()
    body = mesh(PARTS, (-0.2, -0.01, -0.7), (0.2, 0.86, 0.7), 0.005)
    v, f = fast_simplification.simplify(np.asarray(body.vertices, np.float32), np.asarray(body.faces, np.int32), target_reduction=0.75)
    body = trimesh.Trimesh(v, f, process=True); trimesh.smoothing.filter_taubin(body, iterations=4)
    print('body', len(body.faces), 'tris', round(time.time() - t0, 1), 's')
    meshes = [pack('body', body, PARTS)]
    for S, sx in (('R', -1), ('L', 1)):                           # floppy ears: hang from the ear bone, a little away from the skull
        ear = [(None, ell((sx * 0.1, 0.705, 0.415), (0.022, 0.07, 0.052)), 'ear' + S, GOLD, 0.01), (None, ell((sx * 0.094, 0.75, 0.415), (0.024, 0.03, 0.045)), 'ear' + S, GOLD, 0.02)]
        m = mesh(ear, (sx * 0.1 - 0.05, 0.6, 0.33), (sx * 0.1 + 0.05, 0.8, 0.5), 0.003)
        meshes.append(pack('ear' + S, m, bone='ear' + S, color=GOLD))
    out = {'bones': [{'name': n, 'parent': p, 'head': list(h)} for n, p, h in BONES], 'meshes': meshes}
    json.dump(out, open(OUT, 'w'), separators=(',', ':'))
    print('wrote', OUT, round(os.path.getsize(OUT) / 1e6, 1), 'MB', round(time.time() - t0, 1), 's')
