"""The 3D guy, sculpted in code (signed-distance masses blended like clay), meshed, skinned and exported for three.js.

   python3 character.py out_dir

Rest pose: A-pose (arms 40 deg out, elbows 8 deg bent, legs 4 deg apart), facing -z, y up, metres.
Bone lengths match studio/samples/web/main.js (torso 0.52, upper arm 0.30, forearm 0.27, thigh 0.43, shin 0.42).
Every mass is tagged with the bone it belongs to; skin weights come from how close each vertex is to each mass
(the same smooth blend that fuses the clay), so joints bend smoothly instead of capsules crossing.
"""
import json, math, os, sys, time
import numpy as np
from skimage import measure
import trimesh
import fast_simplification

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
A_DEG, ELB_DEG, LEG_DEG = 40.0, 8.0, 4.0


def v(*a):
    return np.array(a, np.float64)


def nrm(a):
    return a / np.linalg.norm(a)


def rot(axis, deg):
    axis = nrm(np.asarray(axis, float)); a = math.radians(deg)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


# ------------------------------------------------------------------ skeleton (rest, world positions)
B = {}          # name -> dict(pos, parent, tail)


def bone(name, parent, head, tail):
    B[name] = dict(parent=parent, head=np.asarray(head, float), tail=np.asarray(tail, float))


HIP = v(0, 0.95, 0)
bone('hips', None, HIP, HIP + v(0, 0.11, 0))
bone('spine1', 'hips', HIP + v(0, 0.11, 0.004), HIP + v(0, 0.23, 0.008))
bone('spine2', 'spine1', HIP + v(0, 0.23, 0.008), HIP + v(0, 0.35, 0.006))
bone('chest', 'spine2', HIP + v(0, 0.35, 0.006), HIP + v(0, 0.52, 0))
bone('neck', 'chest', HIP + v(0, 0.52, 0), HIP + v(0, 0.585, 0))
bone('head', 'neck', HIP + v(0, 0.585, 0), HIP + v(0, 0.80, 0))
bone('jaw', 'head', v(0, 1.585, -0.005), v(0, 1.53, -0.075))
for s, S in ((1, 'R'), (-1, 'L')):            # R = +x side (the rig's 'N' side), L = -x ('F')
    sh = HIP + v(0.2 * s, 0.455, 0)
    bone('clav' + S, 'chest', HIP + v(0.03 * s, 0.45, -0.01), sh)
    adir = v(s * math.sin(math.radians(A_DEG)), -math.cos(math.radians(A_DEG)), 0)
    el = sh + adir * 0.30
    fdir = rot(v(1, 0, 0) * 1.0, -ELB_DEG) @ adir if False else nrm(adir + v(0, 0, -math.tan(math.radians(ELB_DEG))))
    wr = el + fdir * 0.27
    bone('uarm' + S, 'clav' + S, sh, el)
    bone('farm' + S, 'uarm' + S, el, wr)
    bone('hand' + S, 'farm' + S, wr, wr + fdir * 0.09)
    # hand frame: u along the hand, n = palm normal (faces the body), w = across the knuckles (index at -z/front)
    u = fdir
    n = nrm(np.cross(u, v(0, 0, 1)) * s)            # palm faces inward
    if n[0] * s > 0:
        n = -n
    w = nrm(np.cross(n, u))
    if w[2] > 0:
        w = -w
    for fi, (fname, off, ln) in enumerate((('index', -0.026, 0.09), ('middle', -0.009, 0.098), ('ring', 0.008, 0.092), ('pinky', 0.024, 0.075))):
        base = wr + u * 0.088 + w * off
        bone(f'{fname}1{S}', 'hand' + S, base, base + u * ln * 0.55)
        bone(f'{fname}2{S}', f'{fname}1{S}', base + u * ln * 0.55, base + u * ln)
    tb = wr + u * 0.03 + w * -0.03 + n * 0.012
    tdir = nrm(u * 0.7 + w * -0.6 + n * 0.25)
    bone('thumb1' + S, 'hand' + S, tb, tb + tdir * 0.045)
    bone('thumb2' + S, 'thumb1' + S, tb + tdir * 0.045, tb + tdir * 0.08)
    hp = HIP + v(0.09 * s, 0, 0)
    ldir = v(s * math.sin(math.radians(LEG_DEG)), -math.cos(math.radians(LEG_DEG)), 0)
    kn = hp + ldir * 0.43
    an = kn + ldir * 0.42
    bone('thigh' + S, 'hips', hp, kn)
    bone('shin' + S, 'thigh' + S, kn, an)
    bone('foot' + S, 'shin' + S, an, an + v(0, -0.06, -0.15))
HAND = {S: dict(u=None) for S in 'RL'}


# ------------------------------------------------------------------ signed-distance masses
def sd_ell(P, c, r, R=None):
    q = P - c
    if R is not None:
        q = q @ R                       # into the mass's own frame (columns = axes)
    k0 = np.linalg.norm(q / r, axis=-1)
    k1 = np.linalg.norm(q / (r * r), axis=-1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def sd_cone(P, a, b, ra, rb):
    ab = b - a; L2 = ab @ ab
    t = np.clip(((P - a) @ ab) / L2, 0, 1)
    return np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - (ra + (rb - ra) * t)


def frame_along(u, up=(0, 0, -1)):
    u = nrm(u); a = np.asarray(up, float)
    if abs(a @ u) > 0.95:
        a = np.array([1.0, 0, 0])
    x = nrm(np.cross(a, u)); z = np.cross(u, x)
    return np.stack([x, u, z], 1)       # columns: x, y(=u), z


MASSES = []     # (name, bone, group, fn(P) -> sd)


def mass(name, bone_, group, fn):
    MASSES.append((name, bone_, group, fn))


H = lambda n: B[n]['head']; T = lambda n: B[n]['tail']
# torso
mass('pelvis', 'hips', 'torso', lambda P: sd_ell(P, HIP + v(0, -0.01, 0.005), v(0.165, 0.11, 0.115)))
mass('belly', 'spine1', 'torso', lambda P: sd_ell(P, HIP + v(0, 0.12, -0.005), v(0.15, 0.12, 0.112)))
mass('ribs', 'spine2', 'torso', lambda P: sd_ell(P, HIP + v(0, 0.27, 0.005), v(0.168, 0.15, 0.118)))
mass('chest', 'chest', 'torso', lambda P: sd_ell(P, HIP + v(0, 0.38, 0.01), v(0.178, 0.11, 0.115)))
for s, S in ((1, 'R'), (-1, 'L')):
    mass('pec' + S, 'chest', 'torso', lambda P, s=s: sd_ell(P, HIP + v(0.075 * s, 0.375, -0.07), v(0.075, 0.055, 0.04)))
    mass('lat' + S, 'spine2', 'torso', lambda P, s=s: sd_ell(P, HIP + v(0.12 * s, 0.31, 0.03), v(0.06, 0.12, 0.07)))
mass('traps', 'chest', 'torso', lambda P: sd_ell(P, HIP + v(0, 0.47, 0.025), v(0.13, 0.05, 0.065)))
mass('neck', 'neck', 'torso', lambda P: sd_cone(P, HIP + v(0, 0.47, 0.012), HIP + v(0, 0.63, 0.0), 0.056, 0.05))
# head (big, friendly cartoon proportions)
HC = v(0, 1.605, 0)
mass('cranium', 'head', 'head', lambda P: sd_ell(P, HC + v(0, 0.035, 0.012), v(0.108, 0.12, 0.118)))
mass('face', 'head', 'head', lambda P: sd_ell(P, HC + v(0, -0.01, -0.038), v(0.095, 0.098, 0.085)))
mass('cheekR', 'head', 'head', lambda P: sd_ell(P, HC + v(0.052, -0.025, -0.07), v(0.04, 0.035, 0.035)))
mass('cheekL', 'head', 'head', lambda P: sd_ell(P, HC + v(-0.052, -0.025, -0.07), v(0.04, 0.035, 0.035)))
mass('jaw', 'jaw', 'head', lambda P: sd_ell(P, HC + v(0, -0.07, -0.05), v(0.072, 0.045, 0.06)))
mass('chin', 'jaw', 'head', lambda P: sd_ell(P, HC + v(0, -0.088, -0.085), v(0.036, 0.026, 0.028)))
mass('nose', 'head', 'head', lambda P: sd_ell(P, HC + v(0, 0.0, -0.118), v(0.02, 0.032, 0.024), frame_along(v(0, 1, -0.45))))
mass('noseTip', 'head', 'head', lambda P: sd_ell(P, HC + v(0, -0.022, -0.126), v(0.024, 0.019, 0.02)))
mass('earR', 'head', 'head', lambda P: sd_ell(P, HC + v(0.11, 0.0, 0.008), v(0.013, 0.033, 0.023)))
mass('earL', 'head', 'head', lambda P: sd_ell(P, HC + v(-0.11, 0.0, 0.008), v(0.013, 0.033, 0.023)))
mass('browR', 'head', 'head', lambda P: sd_ell(P, HC + v(0.045, 0.06, -0.093), v(0.035, 0.012, 0.02)))
mass('browL', 'head', 'head', lambda P: sd_ell(P, HC + v(-0.045, 0.06, -0.093), v(0.035, 0.012, 0.02)))
EYE = {'R': HC + v(0.043, 0.03, -0.078), 'L': HC + v(-0.043, 0.03, -0.078)}
EYE_R = 0.031
MOUTH_Y = HC[1] - 0.052
for nm, dy, rr in (('lipU', 0.0045, v(0.03, 0.009, 0.014)), ('lipL', -0.005, v(0.027, 0.0095, 0.014))):
    mass(nm, 'head' if nm == 'lipU' else 'jaw', 'head', lambda P, dy=dy, rr=rr: sd_ell(P, v(0, MOUTH_Y + dy, -0.103), rr))
# arms
for s, S in ((1, 'R'), (-1, 'L')):
    sh, el, wr = H('uarm' + S), H('farm' + S), H('hand' + S)
    au, fu = nrm(el - sh), nrm(wr - el)
    mass('delt' + S, 'uarm' + S, 'arm' + S, lambda P, sh=sh, au=au, s=s: sd_ell(P, sh + au * 0.035 + v(0.012 * s, 0.01, 0), v(0.068, 0.085, 0.07), frame_along(au)))
    mass('uarm' + S, 'uarm' + S, 'arm' + S, lambda P, sh=sh, el=el: sd_cone(P, sh, el, 0.058, 0.044))
    mass('bicep' + S, 'uarm' + S, 'arm' + S, lambda P, sh=sh, au=au: sd_ell(P, sh + au * 0.15 + v(0, 0, -0.016), v(0.042, 0.075, 0.04), frame_along(au)))
    mass('farm' + S, 'farm' + S, 'arm' + S, lambda P, el=el, wr=wr: sd_cone(P, el, wr, 0.043, 0.03))
    mass('fmus' + S, 'farm' + S, 'arm' + S, lambda P, el=el, fu=fu: sd_ell(P, el + fu * 0.07, v(0.044, 0.075, 0.04), frame_along(fu)))
    # hand: palm, knuckles, fingers, thumb (separate fine mesh)
    hu = nrm(T('hand' + S) - H('hand' + S))
    hn = nrm(np.cross(hu, v(0, 0, 1)) * s)
    if hn[0] * s > 0:
        hn = -hn
    hw = nrm(np.cross(hn, hu))
    if hw[2] > 0:
        hw = -hw
    HAND[S] = dict(u=hu, n=hn, w=hw)
    Rp = np.stack([hw, hu, hn], 1)
    mass('palm' + S, 'hand' + S, 'hand' + S, lambda P, wr=wr, hu=hu, Rp=Rp: sd_ell(P, wr + hu * 0.048, v(0.045, 0.052, 0.018), Rp))
    mass('wrist' + S, 'farm' + S, 'hand' + S, lambda P, wr=wr, hu=hu: sd_cone(P, wr - hu * 0.05, wr + hu * 0.01, 0.031, 0.028))
    for f, r0 in (('index', 0.0105), ('middle', 0.011), ('ring', 0.0105), ('pinky', 0.0092)):
        a1, b1, b2 = H(f'{f}1{S}'), T(f'{f}1{S}'), T(f'{f}2{S}')
        mass(f'{f}1{S}', f'{f}1{S}', 'hand' + S, lambda P, a=a1, b=b1, r=r0: sd_cone(P, a - (b - a) * 0.15, b, r, r * 0.95))
        mass(f'{f}2{S}', f'{f}2{S}', 'hand' + S, lambda P, a=b1, b=b2, r=r0: sd_cone(P, a, b, r * 0.95, r * 0.85))
    t0, t1, t2 = H('thumb1' + S), T('thumb1' + S), T('thumb2' + S)
    mass('thumb1' + S, 'thumb1' + S, 'hand' + S, lambda P, a=t0, b=t1: sd_cone(P, a, b, 0.016, 0.0125))
    mass('thumb2' + S, 'thumb2' + S, 'hand' + S, lambda P, a=t1, b=t2: sd_cone(P, a, b, 0.0125, 0.0105))
# legs
for s, S in ((1, 'R'), (-1, 'L')):
    hp, kn, an = H('thigh' + S), H('shin' + S), H('foot' + S)
    tu, su = nrm(kn - hp), nrm(an - kn)
    mass('thigh' + S, 'thigh' + S, 'leg' + S, lambda P, hp=hp, kn=kn: sd_cone(P, hp + v(0, 0.02, 0), kn, 0.088, 0.058))
    mass('quad' + S, 'thigh' + S, 'leg' + S, lambda P, hp=hp, tu=tu: sd_ell(P, hp + tu * 0.2 + v(0, 0, -0.022), v(0.07, 0.15, 0.06), frame_along(tu)))
    mass('knee' + S, 'shin' + S, 'leg' + S, lambda P, kn=kn: sd_ell(P, kn + v(0, 0.0, -0.012), v(0.055, 0.05, 0.05)))
    mass('shin' + S, 'shin' + S, 'leg' + S, lambda P, kn=kn, an=an: sd_cone(P, kn, an, 0.055, 0.038))
    mass('calf' + S, 'shin' + S, 'leg' + S, lambda P, kn=kn, su=su: sd_ell(P, kn + su * 0.12 + v(0, 0, 0.022), v(0.05, 0.11, 0.05), frame_along(su)))
    fu = nrm(T('foot' + S) - an)
    mass('foot' + S, 'foot' + S, 'foot' + S, lambda P, an=an: sd_ell(P, an + v(0, -0.055, -0.045), v(0.05, 0.04, 0.12)))


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def group_sd(P, groups, k=0.02, skip=()):
    d = None
    for name, bn, g, fn in MASSES:
        if g in groups and name not in skip:
            x = fn(P)
            d = x if d is None else smin(d, x, k)
    return d


def body_sd(P):
    torso = group_sd(P, {'torso'}, 0.04)
    head = group_sd(P, {'head'}, 0.025)
    d = smin(torso, head, 0.03)
    for S in 'RL':
        d = smin(d, group_sd(P, {'arm' + S}, 0.03), 0.025)
    legR, legL = group_sd(P, {'legR'}, 0.03), group_sd(P, {'legL'}, 0.03)
    d = smin(d, legR, 0.03)
    d = smin(d, legL, 0.03)
    return d


# carving: eye sockets, mouth line, nostrils
def carve_face(P, d):
    for S in 'RL':
        d = np.maximum(d, -(np.linalg.norm(P - EYE[S], axis=-1) - (EYE_R + 0.004)))
    mouth = sd_ell(P, v(0, MOUTH_Y, -0.112), v(0.03, 0.0055, 0.045))      # a real opening between the lips
    d = np.maximum(d, -mouth)
    for s in (1, -1):
        d = np.maximum(d, -(np.linalg.norm(P - (HC + v(0.011 * s, -0.035, -0.128)), axis=-1) - 0.0055))
    return d


# ------------------------------------------------------------------ meshing
def mesh_sdf(fn, lo, hi, step, name):
    t0 = time.time()
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    n = np.ceil((hi - lo) / step).astype(int) + 1
    xs, ys, zs = [lo[i] + np.arange(n[i]) * step for i in range(3)]
    vol = np.empty((n[0], n[1], n[2]), np.float32)
    X, Z = np.meshgrid(xs, zs, indexing='ij')
    for j, y in enumerate(ys):                       # one slab at a time keeps memory small
        P = np.stack([X, np.full_like(X, y), Z], -1)
        vol[:, j, :] = fn(P)
    verts, faces, _, _ = measure.marching_cubes(vol, 0.0, spacing=(step, step, step))
    verts += lo
    m = clean_smooth(trimesh.Trimesh(verts, faces, process=True), step, 6)
    print(f'  {name}: {len(m.faces)} tris raw in {time.time() - t0:.1f}s', flush=True)
    return m


def clean_smooth(m, step, iters):
    """Drop degenerate faces and loose crumbs, then Taubin-smooth with a leash (a vertex may not wander > 2 cells)."""
    m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
    parts = [p for p in m.split(only_watertight=False) if len(p.faces) >= 200]
    m = trimesh.util.concatenate(parts) if len(parts) > 1 else parts[0]
    v0 = m.vertices.copy()
    trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=iters)
    bad = np.linalg.norm(m.vertices - v0, axis=1) > 2 * step
    if bad.any():
        v = m.vertices.copy(); v[bad] = v0[bad]; m.vertices = v
    return m


def decimate(m, target):
    if len(m.faces) <= target:
        return m
    p, f = fast_simplification.simplify(m.vertices.astype(np.float32), m.faces.astype(np.int64), 1 - target / len(m.faces))
    m2 = trimesh.Trimesh(p, f, process=True)
    return clean_smooth(m2, 0.004, 2)


def keep_faces(m, keep_vert):
    fk = keep_vert[m.faces].all(1)
    m2 = m.submesh([np.where(fk)[0]], append=True)
    return m2


# ------------------------------------------------------------------ skin weights from the masses
BONES = list(B.keys())


def weights(V, groups=None, extra=None):
    """Each vertex binds to the masses it's closest to (soft-min over the masses' distance), summed per bone."""
    ms = [m for m in MASSES if groups is None or m[2] in groups]
    D = np.stack([fn(V) for _, _, _, fn in ms], 1)                  # (n, masses)
    dmin = D.min(1, keepdims=True)
    W = np.exp(-(D - dmin) / 0.012)
    bw = np.zeros((len(V), len(BONES)))
    for j, (_, bn, _, _) in enumerate(ms):
        bw[:, BONES.index(bn)] += W[:, j]
    if extra is not None:
        bw = extra(V, bw)
    idx = np.argsort(-bw, 1)[:, :4]
    w = np.take_along_axis(bw, idx, 1)
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    w[w < 0.01] = 0
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    return idx.astype(np.uint16), w.astype(np.float32)


def jaw_extra(V, bw):
    """Below the lip line and in front of the ears, the face rides on the jaw (with a soft edge)."""
    hi, ja = BONES.index('head'), BONES.index('jaw')
    y, z = V[:, 1], V[:, 2]
    k = np.clip((MOUTH_Y + 0.002 - y) / 0.012, 0, 1) * np.clip((0.03 - z) / 0.04, 0, 1) * np.clip((y - (HC[1] - 0.14)) / 0.02, 0, 1)
    tot = bw[:, hi] + bw[:, ja]
    bw[:, ja] = tot * k
    bw[:, hi] = tot * (1 - k)
    return bw


def spine_extra(V, bw):
    """Spread the torso along the spine chain by height, so bending the back is smooth, not hinged."""
    names = ['hips', 'spine1', 'spine2', 'chest']
    ys = [HIP[1] + 0.0, HIP[1] + 0.12, HIP[1] + 0.25, HIP[1] + 0.40]
    idx = [BONES.index(n) for n in names]
    tot = bw[:, idx].sum(1)
    y = V[:, 1]
    g = np.stack([np.exp(-((y - yy) / 0.075) ** 2) for yy in ys], 1)
    g /= g.sum(1, keepdims=True)
    for j, b in enumerate(idx):
        bw[:, b] = tot * g[:, j]
    return bw


# ------------------------------------------------------------------ build all pieces
def main():
    pieces = {}
    t0 = time.time()
    # head + neck (fine), face carved
    head_fn = lambda P: carve_face(P, smin(group_sd(P, {'head'}, 0.025), group_sd(P, {'torso'}, 0.04), 0.03))
    m = mesh_sdf(head_fn, (-0.135, 1.40, -0.16), (0.135, 1.775, 0.15), 0.0022, 'head')
    m = keep_faces(m, m.vertices[:, 1] > 1.415)
    pieces['skin_head'] = (decimate(m, 30000), {'head', 'torso'}, lambda V, bw: jaw_extra(V, spine_extra(V, bw)))
    # hair: skull shell above the hairline, with tufts
    def hair_fn(P):
        c = HC + v(0, 0.035, 0.012)
        q = (P - c) / v(0.118, 0.13, 0.128)
        r = np.linalg.norm(q, axis=-1)
        d = (r - 1.0) * 0.12
        th = np.arctan2(q[..., 0], -q[..., 2]); ph = np.arccos(np.clip(q[..., 1] / np.maximum(r, 1e-6), -1, 1))
        d -= 0.012 * np.maximum(np.sin(th * 7 + ph * 3) * np.sin(ph * 6 + 1.0), 0) ** 1.5   # tufts
        y, z = P[..., 1], P[..., 2]
        line = np.where(z < -0.02, HC[1] + 0.098 - 0.03 * np.clip((np.abs(P[..., 0]) - 0.05) / 0.05, 0, 1), HC[1] + 0.0 - 0.06 * np.clip(z / 0.1, 0, 1))
        d = np.maximum(d, line - y)
        d = np.maximum(d, -(sd_ell(P, HC + v(0, -0.01, -0.038), v(0.097, 0.1, 0.087))))      # keep off the face
        return d
    m = mesh_sdf(hair_fn, (-0.14, 1.55, -0.15), (0.14, 1.79, 0.15), 0.0022, 'hair')
    pieces['hair'] = (decimate(m, 12000), {'head'}, None)
    # arms below the sleeves (skin)
    for s, S in ((1, 'R'), (-1, 'L')):
        sh, el = H('uarm' + S), H('farm' + S)
        au = nrm(el - sh); cut = sh + au * 0.12            # inside the sleeve
        fn = lambda P, S=S, cut=cut, au=au: np.maximum(group_sd(P, {'arm' + S}, 0.03), -((P - cut) @ au))
        lo = np.minimum(sh, H('hand' + S)) - 0.09; hi = np.maximum(sh, H('hand' + S)) + 0.09
        m = mesh_sdf(fn, lo, hi, 0.003, 'arm' + S)
        pieces['skin_arm' + S] = (decimate(m, 9000), {'arm' + S}, None)
        hu = HAND[S]['u']; wr = H('hand' + S)
        hlo = np.minimum.reduce([H(b) for b in BONES if b.endswith(S) and (b.startswith(('index', 'middle', 'ring', 'pinky', 'thumb')) or b == 'hand' + S)] + [T(b) for b in BONES if b.endswith(S) and b.startswith(('index', 'middle', 'ring', 'pinky', 'thumb'))] + [wr - hu * 0.06]) - 0.03
        hhi = np.maximum.reduce([H(b) for b in BONES if b.endswith(S) and (b.startswith(('index', 'middle', 'ring', 'pinky', 'thumb')) or b == 'hand' + S)] + [T(b) for b in BONES if b.endswith(S) and b.startswith(('index', 'middle', 'ring', 'pinky', 'thumb'))] + [wr - hu * 0.06]) + 0.03
        m = mesh_sdf(lambda P, S=S: group_sd(P, {'hand' + S}, 0.012), hlo, hhi, 0.0016, 'hand' + S)
        pieces['skin_hand' + S] = (decimate(m, 9000), {'hand' + S, 'arm' + S}, None)
    # shirt: torso + upper arms to mid-bicep, inflated; hem, collar
    def shirt_fn(P):
        y = P[..., 1]
        d = group_sd(P, {'torso'}, 0.04, skip={'neck'}) - (0.016 + 0.022 * np.clip((HIP[1] + 0.12 - y) / 0.14, 0, 1))   # loosens toward the hem
        for s, S in ((1, 'R'), (-1, 'L')):
            sh, el = H('uarm' + S), H('farm' + S)
            au = nrm(el - sh); cut = sh + au * 0.16
            arm = np.maximum(group_sd(P, {'arm' + S}, 0.03) - 0.013, (P - cut) @ au)
            d = smin(d, arm, 0.03)
        d = np.maximum(d, (HIP[1] - 0.045) - P[..., 1])                      # hem (over the waistband)
        d = np.maximum(d, -(sd_cone(P, HIP + v(0, 0.44, 0.012), HIP + v(0, 0.7, 0), 0.066, 0.066)))   # collar opening
        band = np.abs(sd_cone(P, HIP + v(0, 0.495, 0.012), HIP + v(0, 0.515, 0.008), 0.072, 0.07)) - 0.009   # ribbed collar band
        band = np.maximum(band, np.abs(P[..., 1] - (HIP[1] + 0.505)) - 0.016)
        return smin(d, band, 0.006)
    m = mesh_sdf(shirt_fn, (-0.36, 0.80, -0.2), (0.36, 1.50, 0.2), 0.0035, 'shirt')
    pieces['shirt'] = (decimate(m, 16000), {'torso', 'armR', 'armL'}, spine_extra)
    # jeans: pelvis + legs, waist to ankle
    def jeans_fn(P):
        d = smin(group_sd(P, {'torso'}, 0.04) - 0.0, smin(group_sd(P, {'legR'}, 0.03), group_sd(P, {'legL'}, 0.03), 0.03) - 0.012, 0.03)
        d = np.maximum(d, P[..., 1] - (HIP[1] + 0.04))                         # waist (under the shirt)
        d = np.maximum(d, 0.115 - P[..., 1])                                   # cuffs
        return d
    m = mesh_sdf(jeans_fn, (-0.25, 0.08, -0.18), (0.25, 1.05, 0.18), 0.0035, 'jeans')
    pieces['jeans'] = (decimate(m, 16000), {'torso', 'legR', 'legL'}, spine_extra)
    # shoes
    for s, S in ((1, 'R'), (-1, 'L')):
        an = H('foot' + S)
        def shoe_fn(P, an=an):
            upper = sd_ell(P, an + v(0, -0.052, -0.05), v(0.056, 0.05, 0.135)) - 0.003
            collar = sd_cone(P, an + v(0, -0.02, 0.005), an + v(0, 0.035, 0.005), 0.05, 0.047)
            d = smin(upper, collar, 0.03)
            sole = sd_ell(P, an + v(0, -0.088, -0.05), v(0.06, 0.018, 0.14))
            d = smin(d, sole, 0.01)
            return np.maximum(d, -P[..., 1] + 0.0)
        m = mesh_sdf(shoe_fn, an + v(-0.09, -0.12, -0.22), an + v(0.09, 0.07, 0.12), 0.003, 'shoe' + S)
        pieces['shoe' + S] = (decimate(m, 5000), {'foot' + S, 'leg' + S}, None)
    # ---- export
    manifest = dict(bones=[dict(name=n, parent=B[n]['parent'], head=B[n]['head'].tolist(), tail=B[n]['tail'].tolist()) for n in BONES],
                    eyes={S: EYE[S].tolist() for S in 'RL'}, eyeR=EYE_R, mouthY=float(MOUTH_Y), headC=HC.tolist(),
                    hands={S: {k: HAND[S][k].tolist() for k in 'unw'} for S in 'RL'}, meshes=[])
    blob = bytearray()
    for name, (m, groups, extra) in pieces.items():
        V = np.asarray(m.vertices, np.float64)
        if name.startswith('shoe'):
            S = name[-1]
            si = np.full((len(V), 4), BONES.index('foot' + S), np.uint16); sw = np.zeros((len(V), 4), np.float32); sw[:, 0] = 1
            ab = np.clip((V[:, 1] - (H('foot' + S)[1] + 0.01)) / 0.03, 0, 1)    # collar blends into the shin
            si[:, 1] = BONES.index('shin' + S); sw[:, 0] = 1 - ab; sw[:, 1] = ab
        elif name == 'hair':
            si = np.full((len(V), 4), BONES.index('head'), np.uint16); sw = np.zeros((len(V), 4), np.float32); sw[:, 0] = 1
        else:
            si, sw = weights(V, groups, extra)
        F = np.asarray(m.faces, np.uint32)
        ent = dict(name=name, nv=len(V), nf=len(F))
        for key, arr in (('pos', V.astype(np.float32)), ('idx', F), ('si', si), ('sw', sw)):
            while len(blob) % 4:
                blob.append(0)
            ent[key] = len(blob); blob += arr.tobytes()
        manifest['meshes'].append(ent)
        print(f'{name}: {len(V)} verts {len(F)} tris', flush=True)
    open(os.path.join(OUT, 'guy.bin'), 'wb').write(bytes(blob))
    json.dump(manifest, open(os.path.join(OUT, 'guy.json'), 'w'))
    print(f'done in {time.time() - t0:.0f}s, {len(blob) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
