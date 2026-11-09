# How far his body sinks into the couch / table / floor, per frame:  python3 clipchk.py F0 F1 STEP
# Prints frames where any part of him is more than 1 cm inside furniture (lower legs, thighs/seat, feet, hands separately).
import sys, os, runpy
f0, f1, st = (int(x) for x in sys.argv[1:4])
sys.argv = ['foot.py', '/tmp/x', '0', '1', '--scale', '0.2', '--samples', '4']
g = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'foot.py'), run_name='lib')
bpy = g['bpy']; from mathutils.bvhtree import BVHTree; from mathutils import Vector
def bvh(objs):
    dg = bpy.context.evaluated_depsgraph_get(); vs, ps = [], []
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); b = len(vs); vs += [oe.matrix_world @ v.co for v in me.vertices]
        ps += [tuple(b + i for i in p.vertices) for p in me.polygons]; oe.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps)
FURN = [o for o in g['COUCH'] + g['TABLE'] if o.type == 'MESH']
BODY = g['BODY']; RIG = g['RIG']
FB = None
def inside(p):
    loc, nor, i, d = FB.find_nearest(p, 0.2)
    if loc is None: return 0.0
    return d if (p - loc).dot(nor) < 0 else 0.0
bad = 0
for f in range(f0, f1, st):
    g['frame'](f); FB = bvh(FURN)                 # rebuilt each frame: the cushion dents under him
    if g['BODY'].material_slots[0].material == g['XSKIN']: continue          # x-ray beats: no furniture on screen
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh()
    rest = me.attributes.get('rest_position')
    worst = {}
    for v in me.vertices:
        p = oe.matrix_world @ v.co; d = inside(p)
        if d < 0.01: continue
        rz = rest.data[v.index].vector.z if rest else 1.0
        part = 'foot' if rz < 0.1 else 'shin' if rz < 0.47 else 'thigh/seat' if rz < 0.95 else 'arm/hand/torso'
        worst[part] = max(worst.get(part, 0), d)
    oe.to_mesh_clear()
    if worst: bad += 1; print('frame', f, ' '.join(f'{k} {v * 100:.1f}cm' for k, v in sorted(worst.items())), flush=True)
print('frames with clipping:', bad)
