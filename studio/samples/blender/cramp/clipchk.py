# Clip and spin check for the charley horse Short, every frame (room, x-ray and close-up beats):  python3 clipchk.py F0 F1 STEP
#  bed:   any skin or clothes below the (dented) duvet top by more than 3 mm, or inside the headboard / nightstand / pillow
#  hands: hand skin inside his right leg (the calf he grabs, the knee, the foot) by more than 3 mm
#  arms:  forearm or hand skin inside his trunk (shirt, shorts) or his left leg by more than 4 mm
#  spin:  a foot, a hand or his head turning more than 14 deg in one frame (camera cuts are listed separately)
import sys, os, runpy, json, math
f0, f1, st = (int(x) for x in sys.argv[1:4])
sys.argv = ['cramp.py', '/tmp/x', '0', '1', '--scale', '0.2', '--samples', '4']
g = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cramp.py'), run_name='lib')
bpy, np, BODY, SUIT, RIG, PB = g['bpy'], g['np'], g['BODY'], g['SUIT'], g['RIG'], g['PB']
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def evald(o, rest=False):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    rp = None
    if rest: rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); rp = rp.reshape(-1, 3)
    tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('vertices', tri); tri = tri.reshape(-1, 3); oe.to_mesh_clear()
    M_ = np.array(o.matrix_world); return co @ M_[:3, :3].T + M_[:3, 3], rp, tri
def bvh(w, tri): return BVHTree.FromPolygons([Vector(p) for p in w], tri.tolist())
WHERE = {}
def inside(T_, pts, step=1, tag=None, rest=None):
    worst = 0.0
    for k, p in enumerate(pts[::step]):
        p = Vector(p); loc, nor, _, d = T_.find_nearest(p, 0.06)
        if loc is not None and (p - loc).dot(nor) < 0 and d > worst:
            worst = d
            if tag and rest is not None: WHERE[tag] = tuple(round(float(x), 2) for x in rest[k * step])
    return worst
SOLIDS = [o for o in g['BED'] if o.name in ('headboard',)] + [g['NSTAND'][0]]
prev = {}; out = {}; bad = []
for f in range(f0, f1, st):
    g['frame'](f); t = f / 30; nb = g['beat_at'](t)
    rec = {'beat': nb}
    if nb not in (4, 5, 6) and not (nb == 7 and t - g['B'][7] < 0.4):
        wb, rp, tb = evald(BODY, True); ws, _, ts = evald(SUIT)
        # bed: skin/clothes under the dented duvet top
        dv, _, _ = evald(g['DUVET']); top = g['DUV_TOP_MASK']
        DXS, DYS, DX = g['DXS'], g['DYS'], g['DX']
        Z = dv[:, 2].reshape(len(DYS), len(DXS)) if False else None
        rest = g['DUV_REST']; dz = np.array([v.co.z for v in g['DUVET'].data.vertices]).reshape(len(DYS), len(DXS))
        P = np.vstack([wb, ws]); i = np.round((P[:, 0] - DXS[0]) / DX).astype(int); j = np.round((P[:, 1] - DYS[0]) / DX).astype(int)
        ok = (i >= 0) & (i < len(DXS)) & (j >= 0) & (j < len(DYS))
        okt = ok.copy(); okt[ok] = top.reshape(len(DYS), len(DXS))[j[ok], i[ok]]
        pen_bed = float(np.max(dz[j[okt], i[okt]] - P[okt, 2])) if okt.any() else -1.0
        rec['bed'] = round(pen_bed * 1000, 1)
        # hands in the right leg
        leg = (rp[:, 0] < -0.035) & (rp[:, 2] < 0.52) & (np.abs(rp[:, 0]) < 0.3)
        TL = bvh(wb, tb[leg[tb].all(1)])
        hands = np.where((np.abs(rp[:, 0]) > 0.4) & (rp[:, 2] < 1.02))[0]
        rec['hand'] = round(inside(TL, wb[hands], 2) * 1000, 1)
        # arms in the trunk (clothes) or the left leg
        TT = bvh(ws, ts); legL = (rp[:, 0] > 0.035) & (rp[:, 2] < 0.52)
        TLL = bvh(wb, tb[legL[tb].all(1)])
        arms = np.where(np.abs(rp[:, 0]) > 0.33)[0]
        WHERE.clear(); rec['arm'] = round(max(inside(TT, wb[arms], 3, 'trunk', rp[arms]), inside(TLL, wb[arms], 3, 'legL', rp[arms])) * 1000, 1)
        if rec['arm'] > 4: rec['arm_at'] = dict(WHERE)
        # the solid furniture
        sp = 0.0
        for o in SOLIDS:
            wo, _, to = evald(o); sp = max(sp, inside(bvh(wo, to), np.vstack([wb[::3], ws[::3]])))
        rec['solid'] = round(sp * 1000, 1)
        if rec['bed'] > 3 or rec['hand'] > 3 or rec['arm'] > 4 or rec['solid'] > 2: bad.append(f)
    # spin: world turn of feet, hands, head since the previous checked frame
    for bn in ('foot.R', 'foot.L', 'wrist.R', 'wrist.L', 'head'):
        q = (RIG.matrix_world @ PB[bn].matrix).to_quaternion()
        if bn in prev and prev[bn][0] == f - st:
            d = math.degrees(prev[bn][1].rotation_difference(q).angle); d = min(d, 360 - d) / st
            if d > 14 and g['beat_at']((f - st) / 30) == nb: rec.setdefault('spin', []).append((bn, round(d, 1)))
        prev[bn] = (f, q)
    if rec.get('spin'): bad.append(f)
    out[f] = rec; print(f, rec, flush=True)
json.dump(out, open(f'/root/vt/n42/cramp/clip_{f0}_{f1}.json', 'w'))
print('BAD frames', sorted(set(bad)))
