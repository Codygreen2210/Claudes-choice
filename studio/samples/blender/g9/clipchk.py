# how much of the pilot's hands goes inside the stick/throttle grips, per frame: python3 clipchk.py f0-f1[,f0-f1...]
import sys, os, runpy
rng = []
for a in sys.argv[1].split(','):
    x, y = a.split('-'); rng += list(range(int(x), int(y) + 1))
sys.argv = ['g9.py', '/tmp/x', '0', '1', '--scale', '0.2', '--samples', '4']
g = runpy.run_path('/home/claude/claudes-choice/studio/samples/blender/g9/g9.py', run_name='lib')
bpy = g['bpy']; from mathutils.bvhtree import BVHTree
def tree(objs, near=None, rad=0.3):
    dg = bpy.context.evaluated_depsgraph_get(); vs, ps = [], []
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); M = oe.matrix_world; b = len(vs)
        vs += [M @ v.co for v in me.vertices]
        for p in me.polygons:
            if near is None or any((vs[b + i] - near).length < rad for i in p.vertices): ps.append(tuple(b + i for i in p.vertices))
        oe.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps) if ps else None
R_PARTS = [g['SGRIP']] + [o for o in g['STK'] if o.type == 'MESH']
L_PARTS = [g['TGRIP']] + [o for o in bpy.data.objects if o.parent == g['THR'] and o.type == 'MESH' and o not in (g['TGRIP'],)]
for f in rng:
    g['frame'](f); bpy.context.view_layer.update()
    st = g['STICK'].matrix_world.translation; th = g['THR'].matrix_world.translation
    out = []
    for nm, parts, c in (('R', R_PARTS, st), ('L', L_PARTS, th)):
        tb = tree([g['BODY'], g['SUIT']], c, 0.3); tg = tree(parts)
        out.append(f'{nm}:{len(tb.overlap(tg)) if tb and tg else 0}')
    print('frame', f, ' '.join(out), flush=True)
