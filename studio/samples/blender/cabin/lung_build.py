# Lungs for the cabin-pressure Short (adapted from ../stone/anat_build.py, same fit). Original header:
# Real anatomy for the kidney stone Short: cuts the urinary system out of the Z-Anatomy atlas (CC BY-SA 4.0, Gauthier Kervyn & Marcin
# Zielinski, models derived from BodyParts3D, DBCLS) and fits it inside the MakeHuman man's REST pose: both kidneys, their renal pelvis
# (the funnel), both ureters (curves -> tubes of real size, ~4 mm; each vertex gets 'arc' = metres down from the kidney), the bladder,
# the aorta / vena cava with the renal arteries and veins (tubes, 'arc' = metres from the aorta), and the bones around them (spine,
# ribs, pelvis). The atlas and the man share axes (x- = his right, y+ = his back, z up); the fit is a scale and shift per axis
# (hips to hips, spine tips just under the skin of his back), checked against his skin.
#   python3 anat_build.py /root/anat/Z-Anatomy/Startup.blend MAN.blend OUT.blend
import bpy, sys, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src, man, out = sys.argv[-3:]
bpy.ops.wm.open_mainfile(filepath=src)
OB = bpy.data.objects
NUM = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth', 'Eleventh', 'Twelfth']
BONES = [f'Vertebra {k}' for k in ['T%d' % i for i in range(1, 13)] + ['L%d' % i for i in range(1, 6)]] + ['Sacrum', 'Coccyx', 'Hip bone.l', 'Hip bone.r'] + \
        [f'{n} rib.{s}' for n in NUM for s in 'lr'] + ['Intervertebral disc ' + k for k in ('T10-T11', 'T11-T12', 'T12-L1', 'L1-L2', 'L2-L3', 'L3-L4', 'L4-L5', 'L5-S1')]
ORGANS = [('Superior lobe of right lung', 'lung'), ('Middle lobe of right lung', 'lung'), ('Inferior lobe of right lung', 'lung'),
          ('Superior lobe of left lung', 'lung'), ('Inferior lobe of left lung', 'lung'), ('Trachea', 'trachea'), ('Diaphragm', 'diaphragm')]
BONES = BONES + ['Sternum', 'Manubrium of sternum', 'Body of sternum', 'Clavicle.l', 'Clavicle.r'] + [f'Vertebra C{i}' for i in range(5, 8)]
TUBES_OLD = [('Ureter.r', 0.0021, 'ureter'), ('Ureter.l', 0.0021, 'ureter'), ('Abdominal aorta', 0.0085, 'artery'), ('Right renal artery', 0.0028, 'artery'), ('Left renal artery', 0.0028, 'artery'),
         ('Common iliac artery.l', 0.0045, 'artery'), ('Common iliac artery.r', 0.0045, 'artery'),
         ('Intrarenal arteries of right kidney', 0.0011, 'artery'), ('Intrarenal arteries of left kidney', 0.0011, 'artery'),
         ('Inferior vena cava (abdominal part)', 0.0095, 'vein'), ('Right renal vein', 0.0035, 'vein'), ('Left renal vein', 0.0035, 'vein'),
         ('Common iliac vein.l', 0.005, 'vein'), ('Common iliac vein.r', 0.005, 'vein'),
         ('Intrarenal veins of right kidney', 0.0012, 'vein'), ('Intrarenal veins of left kidney', 0.0012, 'vein')]
dg = bpy.context.evaluated_depsgraph_get(); made = []
def new_obj(name, me, kind, srcname):
    o = bpy.data.objects.new(name, me); o['kind'] = kind; o['src'] = srcname; made.append(o); return o
def copy_mesh(o):
    oe = o.evaluated_get(dg); m = oe.to_mesh(); M = oe.matrix_world
    me = bpy.data.meshes.new('a_' + o.name); vs = [tuple(M @ v.co) for v in m.vertices]; fs = [tuple(p.vertices) for p in m.polygons]
    me.from_pydata(vs, [], fs); me.update(); oe.to_mesh_clear()
    for p in me.polygons: p.use_smooth = True
    return me
def splines(o):
    """every spline of a curve as a list of world points (resampled)"""
    oe = o.evaluated_get(dg); M = o.matrix_world; out_ = []
    for sp in o.data.splines:
        if sp.type == 'BEZIER':
            pts = []; bp = sp.bezier_points
            for i in range(len(bp) - 1):
                a_, b_ = bp[i], bp[i + 1]
                for k in range(8):
                    t = k / 8; u = 1 - t
                    pts.append(M @ (a_.co * u ** 3 + a_.handle_right * 3 * u * u * t + b_.handle_left * 3 * u * t * t + b_.co * t ** 3))
            pts.append(M @ bp[-1].co)
        else: pts = [M @ Vector(p.co[:3]) for p in sp.points]
        if len(pts) >= 2: out_.append(pts)
    return out_
def tube_mesh(name, lines, r, arcs):
    """lines: list of point lists; arcs: matching list of arc values per point"""
    vs, fs, av = [], [], []; SEG = 10
    for pts, arc in zip(lines, arcs):
        n = len(pts); base = len(vs); up = Vector((0, 0, 1))
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            x = d.cross(up); x = x.normalized() if x.length > 1e-4 else d.cross(Vector((1, 0, 0))).normalized(); y = d.cross(x); up = y.cross(d) if False else up
            for k in range(SEG):
                a_ = 2 * math.pi * k / SEG; vs.append(tuple(p + (x * math.cos(a_) + y * math.sin(a_)) * r)); av.append(arc[i])
        for i in range(n - 1):
            for k in range(SEG):
                a0 = base + i * SEG + k; a1 = base + i * SEG + (k + 1) % SEG; fs.append((a0, a1, a1 + SEG, a0 + SEG))
    me = bpy.data.meshes.new('a_' + name); me.from_pydata(vs, [], fs); me.update()
    at = me.attributes.new('arc', 'FLOAT', 'POINT'); at.data.foreach_set('value', av)
    for p in me.polygons: p.use_smooth = True
    return me
for n in BONES:
    if n in OB: new_obj(n, copy_mesh(OB[n]), 'bone', n)
    else: print('MISSING', n)
for n, k in ORGANS: new_obj(n, copy_mesh(OB[n]), k, n)
CL = {}
TUBES = []
for n, r, k in TUBES:
    if n not in OB: print('MISSING', n); continue
    L_ = splines(OB[n])
    if k == 'ureter':                                                        # one line, kidney end first (top), arc = metres from the top
        pts = max(L_, key=len)
        if pts[0].z < pts[-1].z: pts = pts[::-1]
        arc = [0.0]
        for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
        L_, A_ = [pts], [arc]; CL[n] = pts
    else:
        A_ = []
        for pts in L_:
            arc = [0.0]
            for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
            A_.append(arc)
    o = new_obj(n, tube_mesh(n, L_, r, A_), k, n)
print('ureter pts', {k: (len(v), [round(x, 3) for x in v[0]], [round(x, 3) for x in v[-1]]) for k, v in CL.items()})
# ---- the man (rest pose) and the fit
with bpy.data.libraries.load(man, link=False) as (s_, d_): d_.objects = ['Human', 'Human.rig']
BODY, RIG = d_.objects
HIPM = (RIG.data.bones['upperleg01.R'].head_local.z + RIG.data.bones['upperleg01.L'].head_local.z) / 2
SX, SY, SZ = 0.9, 0.9, 0.93; TY = -0.045; Z0A = 0.86
def fit(p): return Vector((p.x * SX, p.y * SY + TY, HIPM + (p.z - Z0A) * SZ))
for o in made:
    for v in o.data.vertices: v.co = fit(v.co)
    o.data.update()
CLF = {k: [tuple(fit(p)) for p in v] for k, v in CL.items()}
# check: everything under his skin?
bm = BODY.data; tris = []
bm.calc_loop_triangles(); T = BVHTree.FromPolygons([v.co.copy() for v in bm.vertices], [tuple(t.vertices) for t in bm.loop_triangles])
def inside(p):
    """ray parity (two directions must agree, else trust the nearer-surface side)"""
    res = []
    for d in (Vector((0.31, 0.2, 0.93)).normalized(), Vector((-0.4, 0.87, 0.29)).normalized()):
        n = 0; q = p.copy()
        while True:
            loc, nor, idx, dist = T.ray_cast(q, d)
            if loc is None: break
            n += 1; q = loc + d * 1e-5
        res.append(n % 2 == 1)
    return res[0] or res[1]
worst = {}
for o in made:
    w = 0.0; cnt = 0
    for v in list(o.data.vertices)[::5]:
        if not inside(v.co):
            loc, nor, _, d = T.find_nearest(v.co, 0.1); w = max(w, d if loc is not None else 0.1); cnt += 1
    if cnt: worst[o.name.replace('.001', '')] = (round(w * 1000, 1), cnt)
print('OUTSIDE SKIN (mm):', worst)
import json
for o in list(bpy.data.objects):
    if o not in made: bpy.data.objects.remove(o)
sc = bpy.context.scene
for o in made: sc.collection.objects.link(o); o.name = o['src']
sc['ureters'] = json.dumps(CLF)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('saved', len(made), 'objects')
