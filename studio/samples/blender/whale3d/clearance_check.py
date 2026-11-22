# clearance check (not a render): run as  cat parts/[0-8]*.py clearance_check.py > _c.py; CF0=0 CF1=716 CSTEP=5 python3 _c.py /tmp/x 0 0
# reports the whale under the sand, the diver inside the whale's solid parts, and the diver poking out of the shut mouth

# ================================================================ clearance check (not a render): whale vs floor, diver vs whale
import numpy as np
from mathutils.bvhtree import BVHTree
STEP = int(os.environ.get('CSTEP', '3')); F0 = int(os.environ.get('CF0', '0')); F1 = int(os.environ.get('CF1', str(int((T_SPIT + 0.2) * FPS))))
def wmesh(objs, dg):
    V = []; P = []
    for o in objs:
        if o.hide_render: continue
        e = o.evaluated_get(dg); m = e.to_mesh(); mw = e.matrix_world
        off = len(V); V += [mw @ v.co for v in m.vertices]; P += [[off + i for i in p.vertices] for p in m.polygons]; e.to_mesh_clear()
    return V, P
dg = bpy.context.evaluated_depsgraph_get()
fv, fp = wmesh([FLOOR] + ROCKS, dg); FB = BVHTree.FromPolygons(fv, fp)
def ground(x, y):
    h = FB.ray_cast(Vector((x, y, FLOOR_Z + 20)), Vector((0, 0, -1)))
    return h[0].z if h[0] else FLOOR_Z
DV = DIVER
dobjs = [DV.body, DV.suit] + [o for o in DV.gear if o.type == 'MESH']
for f in range(F0, F1, STEP):
    frame(f); dg = bpy.context.evaluated_depsgraph_get(); t = f / FPS
    bv, bp = wmesh([HB['body']], dg); jv, jp = wmesh([HB['jaw']], dg)
    BB = BVHTree.FromPolygons(bv, bp); JB = BVHTree.FromPolygons(jv, jp); WB = BVHTree.FromPolygons(bv + jv, bp + [[i + len(bv) for i in p] for p in jp])
    # whale under the sand
    pen = 0.0; npen = 0
    for v in jv[::7] + bv[::7]:
        if v.z < FLOOR_Z + 2.0:
            g = ground(v.x, v.y)
            if v.z < g: npen += 1; pen = max(pen, g - v.z)
    # diver inside the whale's solid parts, or sticking out of the shut mouth
    dv = []; dn = []
    for o in dobjs:
        if o.hide_render: continue
        e = o.evaluated_get(dg); m = e.to_mesh(); mw = e.matrix_world; pts = [mw @ v.co for v in m.vertices]; e.to_mesh_clear()
        dv += pts; dn += [o.name] * len(pts)
    Mi = HB['root'].matrix_world.inverted(); bad = {}
    def inside(B, p):
        n = 0; q = p.copy(); d = Vector((0.0123, 1.0, 0.0371)).normalized()
        for _ in range(12):
            h = B.ray_cast(q, d)
            if not h[0]: break
            n += 1; q = h[0] + d * 1e-4
        return n % 2 == 1
    inbody = injaw = out = 0; near = 0
    for p, nm in list(zip(dv, dn))[::9]:
        if (p - bv[0]).length > 30: continue
        near += 1
        if inside(BB, p): inbody += 1; bad.setdefault('U:' + nm.split('_')[-1], []).append(Mi @ p)
        elif inside(JB, p): injaw += 1; bad.setdefault('J:' + nm.split('_')[-1], []).append(Mi @ p)
        elif TE + 0.45 < t < T_SPIT - 0.15:
            enc = all(WB.ray_cast(p, Vector(d))[0] is not None for d in ((0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)))
            if not enc: out += 1; bad.setdefault('O:' + nm.split('_')[-1], []).append(Mi @ p)
    print(f'CLR f{f:4d} t{t:5.2f} sand_pen {pen:.2f}m n{npen} | diver pts {near} in_upper {inbody} in_jaw {injaw} poking_out {out}', flush=True)
    for k, ps in sorted(bad.items(), key=lambda kv: -len(kv[1]))[:6]:
        a_ = np.array([tuple(q) for q in ps]); print(f'   {k:14s} {len(ps):4d}  x {a_[:,0].min():6.2f}..{a_[:,0].max():6.2f}  y {a_[:,1].min():5.2f}..{a_[:,1].max():5.2f}  z {a_[:,2].min():5.2f}..{a_[:,2].max():5.2f}', flush=True)
