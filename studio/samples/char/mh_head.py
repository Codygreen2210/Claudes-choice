"""Reference head for the 3D guy: the MakeHuman base mesh (hm08, CC0 1.0, github.com/makehumancommunity/makehuman)
with its macro targets for an average 25-year-old man (universal male / young / average muscle + weight, the three
ethnic targets mixed equally).  Placed on our skeleton (eye midpoint on our eye line) and scaled uniformly so head
breadth/length match ANSUR II and eye spacing matches Farkas (S = 0.104: 149 / 192 / 61 mm).

    python3 mh_head.py /path/to/makehuman/makehuman/data     # once: -> assets/mh_head_mesh.npz (small, in the repo)
    head_grid()                                               # character.py: 1 mm signed-distance grid, cached in
                                                              #   assets/.cache/ (built from the mesh in ~1 min)
"""
import sys, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MESH = os.path.join(HERE, 'assets', 'mh_head_mesh.npz')
CACHE = os.path.join(HERE, 'assets', '.cache', 'mh_head_sdf.npz')
S = 0.104
HC = np.array([0, 1.640, 0.0]); EYE_MID = HC + np.array([0, 0.002, -0.0762])


def build_mesh(D):
    def load_obj(p):
        V, F, G = [], [], []; g = None
        for ln in open(p):
            if ln.startswith('v '): V.append([float(t) for t in ln.split()[1:4]])
            elif ln.startswith('g '): g = ln.split()[1]
            elif ln.startswith('f '): F.append([int(t.split('/')[0]) - 1 for t in ln.split()[1:]]); G.append(g)
        return np.array(V), F, G

    def target(name):
        d = {}
        for ln in open(f'{D}/targets/macrodetails/{name}.target'):
            if ln.startswith('#') or not ln.strip(): continue
            t = ln.split(); d[int(t[0])] = np.array([float(x) for x in t[1:4]])
        return d
    V, F, G = load_obj(f'{D}/3dobjs/base.obj')
    for n, w in {'universal-male-young-averagemuscle-averageweight': 1.0,
                 'caucasian-male-young': 1 / 3, 'african-male-young': 1 / 3, 'asian-male-young': 1 / 3}.items():
        for i, dv in target(n).items(): V[i] += w * dv
    eyes = {s: V[np.unique([i for f, g in zip(F, G) if g == f'joint-{s}-eye' for i in f])].mean(0) for s in 'lr'}
    mid = (eyes['l'] + eyes['r']) / 2
    R = np.diag([-1.0, 1.0, -1.0])                  # MakeHuman faces +z, we face -z (a half turn, not a mirror)
    X = lambda P: (np.asarray(P) - mid) @ R.T * S + EYE_MID + np.array([0, 0, 0.0017])   # its lids fit our eyeballs
    tri = np.array([[f[0], f[k], f[k + 1]] for f, g in zip(F, G) if g == 'body' for k in range(1, len(f) - 1)])
    Vt = X(V)
    keep = np.all(Vt[tri][:, :, 1] > HC[1] - 0.155, axis=1)             # head and upper neck
    Fh = tri[keep]; used = np.unique(Fh); remap = -np.ones(len(Vt), int); remap[used] = np.arange(len(used))
    import igl, trimesh
    Vh, Fh = igl.loop(Vt[used], remap[Fh], 1)
    # drop the inside of the mouth, nose and eye sockets (faces the outside can't see); the winding number then
    # closes those openings and we carve our own eye sockets, nostrils and lip line
    C = Vh[Fh].mean(1); N = trimesh.Trimesh(Vh, Fh, process=False).face_normals
    ao = igl.ambient_occlusion(Vh, Fh, C + N * 1e-4, N, 96)
    Fh = Fh[ao < 0.75]
    used = np.unique(Fh); remap = -np.ones(len(Vh), int); remap[used] = np.arange(len(used)); Vt, Fh = Vh, remap[Fh]
    os.makedirs(os.path.dirname(MESH), exist_ok=True)
    np.savez_compressed(MESH, V=Vt[used].astype(np.float32), F=Fh.astype(np.int32),
                        note='MakeHuman hm08 base mesh + macrodetails targets, CC0 1.0 (github.com/makehumancommunity/makehuman)')
    print('saved', MESH, len(used), 'verts')


def head_grid(step=0.001):
    if os.path.exists(CACHE) and os.path.getmtime(CACHE) > os.path.getmtime(MESH):
        z = np.load(CACHE)
        return z['grid'].astype(np.float32) * float(z['unit']), z['lo'], float(z['step'])
    import igl
    z = np.load(MESH); V, F = z['V'].astype(np.float64), z['F'].astype(np.int64)
    V, F = igl.loop(V, F, 1)                                            # the smooth limit surface
    lo = V.min(0) - 0.006; hi = V.max(0) + 0.006; lo[1] = HC[1] - 0.15
    xs, ys, zs = (np.arange(lo[i], hi[i] + step, step) for i in range(3))
    Q = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), -1).reshape(-1, 3)
    d = np.empty(len(Q))
    print('building the reference-head distance grid (once, ~1 min)...', flush=True)
    for i in range(0, len(Q), 2_000_000):
        q = Q[i:i + 2_000_000]
        ud = np.sqrt(igl.point_mesh_squared_distance(q, V, F)[0])
        w = igl.fast_winding_number(V, F, q)                            # copes with the open neck
        d[i:i + 2_000_000] = np.where(w > 0.5, -ud, ud)
    grid = np.round(np.clip(d, -0.03, 0.03) * 1e5).astype(np.int16).reshape(len(xs), len(ys), len(zs))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    np.savez_compressed(CACHE, grid=grid, lo=np.array([xs[0], ys[0], zs[0]]), step=step, unit=1e-5)
    return grid.astype(np.float32) * 1e-5, np.array([xs[0], ys[0], zs[0]]), step


if __name__ == '__main__':
    build_mesh(sys.argv[1])
