# Clip and spin check for the kidney stone Short, every frame he is on screen (beats 0, 1, 2, 6, 8, 11):  python3 clipchk.py F0 F1 STEP
#  floor:  skin or clothes below the floor by more than 2 mm      float: a foot more than 6 mm above it (both feet stay planted)
#  solid:  skin or clothes inside the cabinet / countertop        hand: right-hand skin inside his shirt or trousers by more than 3 mm
#  spin:   a foot, a hand or his head turning more than 14 deg in one frame
import sys, os, runpy, json, math
f0, f1, st = (int(x) for x in sys.argv[1:4])
sys.argv = ['stone.py', '/tmp/x', '0', '1', '--scale', '0.2', '--samples', '4']
g = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stone.py'), run_name='lib')
bpy, np, BODY, SUIT, RIG, PB = g['bpy'], g['np'], g['BODY'], g['SUIT'], g['RIG'], g['PB']
from mathutils import Vector
CX0, CX1, CY0, CY1, CTOP = g['CX0'], g['CX1'], g['CY0'], g['CY1'], g['CTOP']
def suit_w():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); oe.to_mesh_clear(); M_ = np.array(SUIT.matrix_world); return co @ M_[:3, :3].T + M_[:3, 3]
prev = {}; out = {}; bad = []
for f in range(f0, f1, st):
    t = f / 30; nb = g['beat_at'](t)
    if nb not in (0, 1, 2, 6, 8, 11): continue
    g['frame'](f); bpy.context.view_layer.update(); rec = {'beat': nb}
    W, RP = g['body_eval'](); Ws = suit_w(); P = np.vstack([W, Ws])
    rec['floor'] = round(float(-P[:, 2].min()) * 1000, 1)
    ft = [float(W[(RP[:, 2] < 0.1) & (RP[:, 0] * sg > 0), 2].min()) for sg in (-1, 1)]; rec['float'] = round(max(ft) * 1000, 1)
    inb = (P[:, 0] > CX0 - 0.0) & (P[:, 1] > CY0) & (P[:, 1] < CY1) & (P[:, 2] < CTOP - 0.003)
    rec['solid'] = round(float(np.minimum(P[inb, 0] - CX0, CTOP - P[inb, 2]).max()) * 1000, 1) if inb.any() else 0.0
    T_ = g['suit_bvh'](); hm = np.where(RP[:, 0] < -0.44)[0]; pen = 0.0
    for i in hm[::2]:
        p = Vector(W[i]); loc, nor, _, d = T_.find_nearest(p, 0.05)
        if loc is not None and (p - loc).dot(nor) < 0: pen = max(pen, d)
    rec['hand'] = round(pen * 1000, 1)
    for bn in ('foot.R', 'foot.L', 'wrist.R', 'wrist.L', 'head'):
        q = (RIG.matrix_world @ PB[bn].matrix).to_quaternion()
        if bn in prev and prev[bn][0] == f - st and g['beat_at']((f - st) / 30) == nb:
            d = math.degrees(prev[bn][1].rotation_difference(q).angle); d = min(d, 360 - d) / st
            if d > 14: rec.setdefault('spin', []).append((bn, round(d, 1)))
        prev[bn] = (f, q)
    if rec['floor'] > 2 or rec['float'] > 6 or rec['solid'] > 2 or rec['hand'] > 3 or rec.get('spin'): bad.append(f)
    out[f] = rec; print(f, rec, flush=True)
json.dump(out, open(f'/root/vt/n42/stone/clip_{f0}_{f1}.json', 'w'))
print('BAD frames', bad)
