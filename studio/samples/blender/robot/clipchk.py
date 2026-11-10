# Clip check for the robot Short (no rendering):  python3 clipchk.py F0 F1 STEP
#  floor: a foot below the bench top     tray/copier/jig: a foot inside them     body: a foot, gripper or arm of one robot inside the other's drum
#  grip: a gripper below the bench       spin: a robot turning more than 10 deg in one frame (camera cuts listed separately)
import sys, os, runpy, json, math
f0, f1, st = (int(x) for x in sys.argv[1:4])
sys.argv = ['robot.py', '/tmp/x', '0', '1', '--scale', '0.1', '--samples', '1']
g = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'robot.py'), run_name='lib')
bpy, ROB, KID = g['bpy'], g['ROB'], g['KID']
from mathutils import Vector
TRAY = (g['TRAY_C'].x - 0.08, g['TRAY_C'].x + 0.08, g['TRAY_C'].y - 0.055, g['TRAY_C'].y + 0.055, 0.018)
CP = g['COPIER_C']; COPB = (CP.x - 0.06, CP.x + 0.06, CP.y - 0.025, CP.y + 0.025, 0.012)
C_POS = g['C_POS']
def feet(Rb):
    out = []
    for k, (hip, fem, tib, a) in enumerate(Rb['legs']):
        ob = next(o for o_, o in Rb['parts'] if o.name.endswith(f'_foot{k}'))
        if not ob.hide_render: out.append((k, tib.matrix_world @ Vector((0.063, 0, 0))))
    return out
def arm_pts(Rb):
    out = []
    for k, (sh, up, fo, wr, fingers) in enumerate(Rb['arms']):
        ob = next(o for o_, o in Rb['parts'] if o.name.endswith(f'_wrist{k}'))
        if ob.hide_render: continue
        a_, b_, c_ = up.matrix_world.translation, fo.matrix_world.translation, wr.matrix_world @ Vector((0.02, 0, 0))
        out += [(k, a_.lerp(b_, s)) for s in (0.5, 1.0)] + [(k, b_.lerp(c_, s)) for s in (0.5, 1.0)]
    return out
def in_box(p, b, r=0.004): return b[0] - r < p.x < b[1] + r and b[2] - r < p.y < b[3] + r and p.z < b[4] + r
def in_drum(p, Rb, r=0.0):
    c = Rb['root'].matrix_world.translation; z0, z1 = c.z - 0.024, c.z + 0.002
    return math.hypot(p.x - c.x, p.y - c.y) < 0.05 + r and z0 - r < p.z < z1 + r
prev = {}; out = {}; bad = []
for f in range(f0, f1, st):
    g['frame'](f); bpy.context.view_layer.update(); t = f / 30; nb = g['beat_at'](t); rec = {'beat': nb}
    if nb in (8, 9): out[f] = rec; continue
    for nm, Rb, other in (('rob', ROB, KID), ('kid', KID, ROB)):
        vis = not Rb['parts'][0][1].hide_render
        if not vis: continue
        for k, p in feet(Rb):
            if p.z < 0.0034 - 0.0006: rec.setdefault('floor', []).append((nm, k, round(p.z * 1000, 1)))
            if in_box(p, TRAY): rec.setdefault('tray', []).append((nm, k))
            if in_box(p, COPB): rec.setdefault('copier', []).append((nm, k))
            if nm == 'rob' and math.hypot(p.x - C_POS.x, p.y - C_POS.y) < 0.034: rec.setdefault('jig', []).append((nm, k))
            if not other['parts'][0][1].hide_render and in_drum(p, other, 0.004): rec.setdefault('body', []).append((nm, 'foot', k))
        for k, p in arm_pts(Rb):
            if p.z < 0.002: rec.setdefault('grip', []).append((nm, k, round(p.z * 1000, 1)))
            if not other['parts'][0][1].hide_render and in_drum(p, other, 0.002): rec.setdefault('body', []).append((nm, 'arm', k))
        y = Rb['root'].rotation_euler.z
        if nm in prev and prev[nm][0] == f - st and g['beat_at']((f - st) / 30) == nb:
            d = abs(math.degrees(y - prev[nm][1])) / st
            if d > 10: rec.setdefault('spin', []).append((nm, round(d, 1)))
        prev[nm] = (f, y)
    if any(k in rec for k in ('floor', 'tray', 'copier', 'jig', 'body', 'grip', 'spin')): bad.append(f); print(f, rec, flush=True)
    out[f] = rec
json.dump(out, open(f'/root/vt/n42/robot/clip_{f0}_{f1}.json', 'w'))
print('BAD frames', bad)
