"""Measure the sculpted body (nude, under the clothes) like an anthropometrist and compare with real adult men.
    python3 measure.py [module]      (module defaults to character; prints a table, writes measure.json)
Girths come from cross-sections of the body SDF (marching squares on a 0.5 mm grid); limb girths are cut square to the
bone; breadths/depths are the section's extent.  Targets: Heinz et al. 2003 (bdims, 247 active men, 177.7 cm),
ANSUR II 2012 (head/face, 4,082 men) and NIOSH 2005 (face, 2,544 men), scaled to our 175 cm stature."""
import sys, json, importlib
import numpy as np
from skimage import measure as skm

C = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else 'character')
v = C.v; H = C.H; T = C.T
STAT = 1.75; K = STAT / 1.777          # bdims sample stature -> ours
BODY = {'head', 'torso', 'armR', 'armL', 'handR', 'handL', 'legR', 'legL'}


def gsdf(groups, P):
    """Group SDF with each mass evaluated only near itself (fast)."""
    d = np.full(len(P), C.BIG)
    for op in ('add', 'sub', 'post'):
        for m in C.MASSES:
            if m.op != op or m.group not in groups:
                continue
            sel = np.where((P >= m.lo - 0.03).all(1) & (P <= m.hi + 0.03).all(1))[0]
            if len(sel) == 0:
                continue
            x = m.sd(P[sel])
            d[sel] = C.smax(d[sel], -x, m.k) if op == 'sub' else C.smin(d[sel], x, m.k)
    return d


def section(groups, origin, n, half=0.25, step=0.001):
    """Cross-section of the SDF in the plane through origin with normal n -> list of contours (in plane coords)."""
    n = C.nrm(n); a = C.nrm(np.cross(n, [0, 0, 1] if abs(n[2]) < 0.9 else [1, 0, 0])); b = np.cross(n, a)
    g = np.arange(-half, half, step)
    U, Vv = np.meshgrid(g, g, indexing='ij')
    P = origin + U[..., None] * a + Vv[..., None] * b
    d = gsdf(groups, P.reshape(-1, 3)).reshape(U.shape)
    cs = skm.find_contours(d, 0.0)
    return [(c * step - half) for c in cs], a, b


def girth_at(groups, origin, n, pick='center', half=0.25):
    cs, a, b = section(groups, origin, n, half)
    if not cs:
        return None, None
    closed = [c for c in cs if np.linalg.norm(c[0] - c[-1]) < 0.003]
    cs = closed or cs
    if pick == 'center':                       # the loop around the origin (a limb), else the biggest (the trunk)
        c = min(cs, key=lambda c: np.linalg.norm(c.mean(0)))
    else:
        c = max(cs, key=lambda c: np.ptp(c[:, 0]) * np.ptp(c[:, 1]))
    from scipy.spatial import ConvexHull               # a tape measure bridges hollows: girth = convex hull perimeter
    h = c[ConvexHull(c).vertices]
    per = np.sum(np.linalg.norm(np.diff(np.vstack([h, h[:1]]), axis=0), axis=1))
    return per, (np.ptp(c[:, 0]), np.ptp(c[:, 1]))


def trunk(y, groups=None):
    """Horizontal girth of the trunk at height y (arms excluded): breadth (x) and depth (z) too."""
    per, (bx, bz) = girth_at(groups or {'torso'}, v(0, y, 0), v(0, 1, 0), 'center', 0.3)
    return per, bx, bz


def limb(bone, t, groups):
    a, b = H(bone), T(bone)
    per, _ = girth_at(groups, a + (b - a) * t, b - a, 'center', 0.12)
    return per


def extent(groups, y0, y1, axis, zlim=None):
    """Max extent along an axis of the body between heights y0..y1 (a breadth)."""
    best = 0
    for y in np.linspace(y0, y1, 9):
        cs, _, _ = section(groups, v(0, y, 0), v(0, 1, 0), 0.2, 0.0005)
        for c in cs:
            # plane coords: a = (x?) — work in world instead
            pass
    return best


def world_section(groups, y, half=0.12, step=0.0005, xr=None, zr=None):
    xs = np.arange(-half, half, step); zs = np.arange(-half, half, step)
    X, Z = np.meshgrid(xs, zs, indexing='ij')
    P = np.stack([X, np.full_like(X, y), Z], -1)
    d = gsdf(groups, P.reshape(-1, 3)).reshape(X.shape)
    inside = d < 0
    if xr is not None: inside &= (X >= xr[0]) & (X <= xr[1])
    if zr is not None: inside &= (Z >= zr[0]) & (Z <= zr[1])
    return X[inside], Z[inside]


def run():
    HC, HIP = C.HC, C.HIP
    out = {}
    def put(name, val, tgt, src):
        out[name] = dict(ours=round(val * 1000, 1) if val is not None else None, target=round(tgt, 1), src=src)
    # trunk girths (cm targets from bdims, scaled)
    ys = np.arange(0.85, 1.36, 0.01)
    tg = [(y,) + trunk(y) for y in ys]
    chest = max([r for r in tg if 1.20 < r[0] < 1.32], key=lambda r: r[1])
    waist = min([r for r in tg if 1.02 < r[0] < 1.15], key=lambda r: r[1])
    hip = max([r for r in tg if 0.84 < r[0] < 0.98], key=lambda r: r[1])
    navel = min(tg, key=lambda r: abs(r[0] - (HIP[1] + 0.09)))
    put('chest girth', chest[1], 1010 * K, 'bdims che_gi'); put('chest breadth', chest[2], 299 * K, 'bdims che_di (ref: bony caliper; skin with lats reads wider)'); put('chest depth', chest[3], 208 * K * 1.2, 'bdims che_de x1.2 (ref: bony caliper)')
    put('waist girth (narrowest)', waist[1], 845 * K, 'bdims wai_gi'); put('navel girth', navel[1], 877 * K, 'bdims nav_gi')
    put('hip girth (buttocks)', hip[1], 978 * K, 'bdims hip_gi')
    # neck
    ng = min((trunk(y, {'torso'}) for y in (1.49, 1.51, 1.53)), key=lambda r: r[0])
    put('neck girth', ng[0], 397, 'ANSUR II (approx.)')
    # shoulder girth at deltoids: horizontal section at the deltoid bulge incl. arms
    sg = max(girth_at(BODY, v(0, y, 0), v(0, 1, 0), 'big', 0.35)[0] or 0 for y in np.arange(1.33, 1.41, 0.01))
    put('shoulder girth', sg, 1165 * K, 'bdims sho_gi (ref: arms down; our A-pose section cuts the arms obliquely)')
    # biacromial: distance between the acromion masses' tops (bony)
    put('biacromial breadth', np.linalg.norm(H('uarmR') - H('uarmL')) + 0.02, 412 * K, 'bdims bia_di')
    # limb girths
    for S in 'R':
        put('upper arm girth (mid)', limb('uarm' + S, 0.55, {'arm' + S}), 344 * K * 0.92, 'bdims bic_gi flexed x0.92 = relaxed')
        put('forearm girth (max)', max(limb('farm' + S, t, {'arm' + S, 'hand' + S}) for t in (0.15, 0.2, 0.25, 0.3)), 282 * K, 'bdims for_gi')
        put('wrist girth', limb('farm' + S, 0.97, {'arm' + S, 'hand' + S}), 172 * K, 'bdims wri_gi')
        put('thigh girth (top)', limb('thigh' + S, 0.15, {'leg' + S}), 565 * K, 'bdims thi_gi')
        put('knee girth', limb('thigh' + S, 0.99, {'leg' + S}), 372 * K, 'bdims kne_gi')
        put('calf girth (max)', max(limb('shin' + S, t, {'leg' + S}) for t in (0.2, 0.25, 0.3, 0.35)), 372 * K, 'bdims cal_gi')
        put('ankle girth (min)', min(limb('shin' + S, t, {'leg' + S}) for t in (0.82, 0.86, 0.9)), 232 * K, 'bdims ank_gi')
    # head and face (ANSUR II / NIOSH)
    X, Z = world_section({'head'}, HC[1] + 0.03)
    put('head breadth', np.ptp(X), 154.3, 'ANSUR II'); put('head length', np.ptp(Z), 199.5, 'ANSUR II')
    hc = girth_at({'head'}, HC + v(0, 0.03, 0), v(0, 1, -0.12), 'big', 0.15)[0]
    put('head circumference', hc, 574.4, 'ANSUR II')
    bz = max(np.ptp(world_section({'head'}, HC[1] + dy, zr=(-0.2, -0.02))[0]) for dy in np.arange(-0.03, 0.005, 0.005))   # in front of the ears
    put('bizygomatic breadth', bz, 143.5, 'NIOSH (ANSUR II 142.6)')
    bg = max(np.ptp(world_section({'head'}, HC[1] + dy, zr=(-0.03, 0.03))[0]) for dy in np.arange(-0.095, -0.065, 0.005))
    put('bigonial breadth', bg, 120.4, 'NIOSH')
    # vertical face: sellion (deepest point of the nasal bridge at eye level) to menton (lowest point of chin)
    def front_z(y, x=0.0):
        zs = np.arange(-0.14, 0.0, 0.0003); P = np.stack([np.full_like(zs, x), np.full_like(zs, y), zs], 1)
        d = gsdf({'head'}, P); i = np.argmax(d < 0); return zs[i] if d[i] < 0 else None
    yy = np.arange(HC[1] - 0.15, HC[1] + 0.04, 0.001)
    fz = np.array([(lambda z: 1 if z is None else z)(front_z(y)) for y in yy])
    chin_y = yy[np.argmax(fz < C.HC[2] - 0.055)]              # lowest point of the face front (not the neck)
    eye_band = (yy > C.EYE['R'][1] - 0.005) & (yy < C.HC[1] + 0.018)      # between the pupils and the brow ridge
    sel_y = yy[eye_band][np.argmax(fz[eye_band])]
    put('menton-sellion length', sel_y - chin_y, 122.7, 'NIOSH (ANSUR II 122.6)')
    nz = (yy > C.HC[1] - 0.065) & (yy < C.HC[1] - 0.015)
    ti = np.argmin(np.where(nz, fz, 1)); tip, tip_y = fz[ti], yy[ti]
    below = (yy > tip_y - 0.022) & (yy < tip_y)
    si = np.argmax(np.where(below, fz, -1)); sn, sn_y = fz[si], yy[si]   # subnasale: the deepest point below the tip
    put('nose protrusion', np.hypot(sn - tip, sn_y - tip_y), 21.1, 'NIOSH / Farkas sn-prn (direct)')
    def run_width(y, z):                                       # the solid run through the midline at (y, z)
        xs_ = np.arange(0, 0.05, 0.0003); P = np.stack([xs_, np.full_like(xs_, y), np.full_like(xs_, z)], 1)
        d = gsdf({'head'}, P); j = np.argmax(d > 0); return 2 * xs_[j]
    nb = max(run_width(tip_y + dy, tip + dz) for dy in (-0.004, -0.002, 0.0) for dz in (0.017,))      # the alae, in front of the cheeks
    put('nose breadth', nb, 36.6, 'NIOSH')
    put('lip length (mouth width)', 2 * C.LIP_HELPERS[0].prm[1][0] if C.LIP_HELPERS else None, 51.1, 'NIOSH (lip paint extent)')
    put('interpupillary', abs(C.EYE['R'][0] - C.EYE['L'][0]), 64.5, 'NIOSH (ANSUR II 64.0)')
    return out


if __name__ == '__main__':
    out = run()
    print(f"{'measure':28s} {'ours':>8s} {'target':>8s}   off")
    for k, r in out.items():
        o, t = r['ours'], r['target']
        off = (o - t) / t * 100 if o else float('nan')
        flag = '' if abs(off) <= 5 else ('  <-- small' if off < 0 else '  <-- big')
        if 'ref' in r['src']: flag = '  (ref only)'
        print(f"{k:28s} {o!s:>8} {t:8.1f}  {off:+5.1f}%{flag}")
    json.dump(out, open('measure.json', 'w'), indent=1)
