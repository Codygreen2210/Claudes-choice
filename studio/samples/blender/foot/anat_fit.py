# Fits the atlas leg (anat_build.py output) onto the MakeHuman man's right leg (man.blend, rest pose), and weights it to his rig, so
# bones stay rigid on their own rig bone and nerves/arteries/muscles bend smoothly at the joints like his skin does.
# Each leg segment (thigh, shin, foot, toes) gets its own fit: joint centres matched (hip = femoral head, knee = condyles,
# ankle = talar dome), length scaled to his bone, girth scaled to his skin. Vertices near a joint blend the two fits.
#   python3 anat_fit.py man.blend leg_r.blend OUT.blend [L]      (L = mirror the atlas leg onto his LEFT leg, bones and muscles only)
import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
SIDE = 'L' if sys.argv[-1] == 'L' else 'R'
args_ = sys.argv[:-1] if SIDE == 'L' else sys.argv
man_f, leg_f, out = args_[-3], args_[-2], args_[-1]
bpy.ops.wm.open_mainfile(filepath=man_f)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; RB = RIG.data.bones
with bpy.data.libraries.load(leg_f) as (s, d): d.objects = list(s.objects)
A = {o.name: o for o in d.objects}
for o in A.values(): bpy.context.scene.collection.objects.link(o)
if SIDE == 'L':                                         # mirror the atlas right leg to a left leg (x -> -x, faces flipped)
    for n in list(A):
        o = A[n]
        if o['kind'] not in ('bone', 'muscle', 'tendon'): bpy.data.objects.remove(o); del A[n]; continue
        o.data.transform(Matrix.Scale(-1, 4, (1, 0, 0))); o.data.flip_normals(); o.name = n + '.L'; o.data.name = o.name
    A = {n[:-2]: o for n, o in ((o.name, o) for o in A.values())}
SX = 'L' if SIDE == 'L' else 'R'
def V(o): return np.array([v.co[:] for v in o.data.vertices])
sm = lambda x: x * x * (3 - 2 * x)
def ramp(x, a, b): return sm(np.clip((x - a) / (b - a), 0, 1))
# ---------------- atlas landmarks
fem = V(A['Femur']); tal = V(A['Talus']); tib = V(A['Tibia'])
top = fem[fem[:, 2] > fem[:, 2].max() - 0.06]; head_pts = top[top[:, 0] > np.percentile(top[:, 0], 40)] if SIDE == 'R' else top[top[:, 0] < np.percentile(top[:, 0], 60)]   # femoral head: medial top
def sphere_fit(P):
    Am = np.c_[2 * P, np.ones(len(P))]; f = (P ** 2).sum(1); c, *_ = np.linalg.lstsq(Am, f, rcond=None); return c[:3], math.sqrt(c[3] + (c[:3] ** 2).sum())
hipA, rh = sphere_fit(head_pts)
low = fem[fem[:, 2] < fem[:, 2].min() + 0.03]; kneeA = np.array([low[:, 0].mean(), low[:, 1].mean() + 0.008, fem[:, 2].min() + 0.024])
ttop = tal[tal[:, 2] > tal[:, 2].max() - 0.015]; ankA = np.array([ttop[:, 0].mean(), ttop[:, 1].mean(), tal[:, 2].max() - 0.02])
toe = V(A['Distal phalanx of second finger of foot']); toeA = toe[np.argmin(toe[:, 1])]
print('atlas hip', hipA.round(3), 'r', round(rh, 3), 'knee', kneeA.round(3), 'ankle', ankA.round(3), 'toe', toeA.round(3))
# ---------------- his landmarks (rest pose)
hipM = np.array(RB[f'upperleg01.{SX}'].head_local); kneeM = np.array(RB[f'lowerleg01.{SX}'].head_local); ankM = np.array(RB[f'foot.{SX}'].head_local)
toeM = np.array(RB[f'toe2-3.{SX}'].tail_local)
print('his   hip', hipM.round(3), 'knee', kneeM.round(3), 'ankle', ankM.round(3), 'toe', toeM.round(3))
def frame(axis, ref):
    x = axis / np.linalg.norm(axis); y = ref - x * ref.dot(x); y /= np.linalg.norm(y); z = np.cross(x, y); return np.c_[x, y, z]
def seg_T(a0, a1, m0, m1, ref, cross=None):
    """similarity per segment: joint centres matched, length scaled; cross = ((sy, oy), (sz, oz)) fits the atlas cross-section to his"""
    Fa = frame(a1 - a0, ref); Fm = frame(m1 - m0, ref)
    sl = np.linalg.norm(m1 - m0) / np.linalg.norm(a1 - a0)
    (sy, oy), (sz, oz) = cross if cross else ((sl, 0.0), (sl, 0.0))
    S = np.diag([sl, sy, sz]); Rm = Fm @ S @ Fa.T
    T = np.eye(4); T[:3, :3] = Rm; T[:3, 3] = m0 - Rm @ a0 + Fm @ np.array([0.0, oy, oz]); return T
FWD = np.array([0.0, -1.0, 0.0]); UP = np.array([0.0, 0.0, 1.0])
_bg = BODY.vertex_groups['body'].index
bodyv = np.array([(BODY.matrix_world @ v.co)[:] for v in BODY.data.vertices if any(g.group == _bg and g.weight > 0.5 for g in v.groups)])
# his skin (rest pose, clothes mask off) for inside/outside tests
for md in BODY.modifiers:
    if md.type == 'MASK' and md.name.startswith('Delete'): md.show_viewport = md.show_render = False
_dg = bpy.context.evaluated_depsgraph_get(); _be = BODY.evaluated_get(_dg); _bm = _be.to_mesh()
SKIN = BVHTree.FromPolygons([BODY.matrix_world @ v.co for v in _bm.vertices], [tuple(p.vertices) for p in _bm.polygons]); _be.to_mesh_clear()
def signed(P):
    out_ = np.empty(len(P))
    for i, p in enumerate(P):
        loc, nor, idx, dist = SKIN.find_nearest(Vector(p)); out_[i] = dist if (Vector(p) - loc).dot(nor) > 0 else -dist
    return out_
from scipy.optimize import minimize
def fit_cross(names, a0, a1, m0, m1, ref, marg, n=1500, seed=1):
    """cross-section scale + shift (in the segment's own frame) that keeps these parts at least marg under his skin, as big as fits"""
    P = np.vstack([V(A[k]) for k in names]); rng = np.random.default_rng(seed); P = P[rng.choice(len(P), min(n, len(P)), replace=False)]
    sl = np.linalg.norm(m1 - m0) / np.linalg.norm(a1 - a0); Ph = np.c_[P, np.ones(len(P))]
    def cost(x):
        T = seg_T(a0, a1, m0, m1, ref, cross=((x[0], x[1]), (x[2], x[3])))
        d = signed((Ph @ T.T)[:, :3]) + marg
        pen = (np.maximum(d, 0) ** 2).mean() / marg ** 2
        reg = 20 * ((x[0] - sl) ** 2 + (x[2] - sl) ** 2) + 2000 * (x[1] ** 2 + x[3] ** 2) + 200 * (max(0, 0.75 * sl - x[0]) ** 2 + max(0, 0.75 * sl - x[2]) ** 2)
        return pen + reg
    r = minimize(cost, [sl, 0.0, sl, 0.0], method='Nelder-Mead', options={'xatol': 1e-4, 'fatol': 1e-6, 'maxiter': 400})
    x = r.x; T = seg_T(a0, a1, m0, m1, ref, cross=((x[0], x[1]), (x[2], x[3]))); d = signed((Ph @ T.T)[:, :3])
    print('  fit', names[0], 'scale fwd/side %.3f %.3f shift mm %.1f %.1f | len scale %.3f | worst %.1f mm out' % (x[0], x[2], x[1] * 1000, x[3] * 1000, sl, d.max() * 1000))
    return ((x[0], x[1]), (x[2], x[3]))
SHIN_P = ['Tibialis anterior muscle', 'Extensor digitorum longus', 'Fibularis longus muscle', 'Fibularis brevis muscle', 'Lateral head of gastrocnemius',
          'Medial head of gastrocnemius', 'Soleus muscle', 'Tibia', 'Fibula', 'Calcaneal tendon']
THIGH_P = ['Femur', 'Vastus lateralis muscle', 'Long head of biceps femoris', 'Short head of biceps femoris']
FOOT_P = ['Calcaneus', 'Talus', 'Navicular bone', 'Cuboid bone', 'First metatarsal bone', 'Fifth metatarsal bone', 'Tendon of extensor digitorum longus'] + \
         [f'Proximal phalanx of {n} finger of foot' for n in ('first', 'second', 'third', 'fourth', 'fifth')]
T_thigh = seg_T(hipA, kneeA, hipM, kneeM, FWD, cross=fit_cross(THIGH_P, hipA, kneeA, hipM, kneeM, FWD, 0.008))
T_shin = seg_T(kneeA, ankA, kneeM, ankM, FWD, cross=fit_cross(SHIN_P, kneeA, ankA, kneeM, ankM, FWD, 0.005))
T_foot = seg_T(ankA, toeA, ankM, toeM, UP, cross=fit_cross(FOOT_P, ankA, toeA, ankM, toeM, UP, 0.003))
# ---------------- per-vertex weights (atlas space): pelvis / thigh / shin / foot, blended near the joints
ax_t = (kneeA - hipA) / np.linalg.norm(kneeA - hipA); ax_s = (ankA - kneeA) / np.linalg.norm(ankA - kneeA)
def seg_weights(P):
    d_hip = (P - hipA) @ ax_t                       # >0 below the hip
    d_knee = (P - kneeA) @ ax_s                     # >0 below the knee
    d_ank = (P - ankA) @ ax_s                       # >0 below the ankle
    w_shin = ramp(d_knee, -0.02, 0.025)
    w_foot = ramp(d_ank, -0.012, 0.02) * ramp(-(P[:, 1] - ankA[1]) + 0.05, 0.0, 0.03 + 0 * P[:, 1]) ** 0   # whole foot below the ankle
    w_pel = 1 - ramp(d_hip, -0.04, 0.02)
    w_th = (1 - w_shin) * (1 - w_pel); w_sh = w_shin * (1 - w_foot); w_ft = w_shin * w_foot; w_pl = w_pel * (1 - w_shin)
    W = np.c_[w_pl, w_th, w_sh, w_ft]; return W / np.maximum(W.sum(1, keepdims=True), 1e-9)
GROUPS = [f'pelvis.{SX}', f'upperleg02.{SX}', f'lowerleg01.{SX}', f'foot.{SX}']
TS = [T_thigh, T_thigh, T_shin, T_foot]      # pelvis part rides the thigh fit near the hip (only the sciatic's top)
RIGID = {'Femur': 1, 'Hip bone': 0, 'Patella': None, 'Tibia': 2, 'Fibula': 2}
TOE_BONE = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5}
SEGN = {'Proximal': 1, 'Middle': 2, 'Distal': 3}
def apply(o, W, extra=None):
    P = V(o); Ph = np.c_[P, np.ones(len(P))]
    out_ = np.zeros_like(P)
    for k, T in enumerate(TS): out_ += W[:, k:k + 1] * (Ph @ T.T)[:, :3]
    for v, p in zip(o.data.vertices, out_): v.co = Vector(p)
    o.vertex_groups.clear()
    for k, g in enumerate(GROUPS):
        vg = o.vertex_groups.new(name=g)
        for i in np.nonzero(W[:, k] > 1e-4)[0]: vg.add([int(i)], float(W[i, k]), 'REPLACE')
    if extra:
        for g, idx, w in extra:
            vg = o.vertex_groups.get(g) or o.vertex_groups.new(name=g)
            vg.add(idx, w, 'REPLACE')
for n, o in A.items():
    P = V(o); kind = o['kind']
    if n == 'Hip bone': W = np.tile([1, 0, 0, 0], (len(P), 1)).astype(float); TS_ = None
    elif n in ('Femur',): W = np.tile([0, 1, 0, 0], (len(P), 1)).astype(float)
    elif n in ('Tibia', 'Fibula'): W = np.tile([0, 0, 1, 0], (len(P), 1)).astype(float)
    elif n == 'Patella': W = np.tile([0, 0.55, 0.45, 0], (len(P), 1)).astype(float)
    elif kind == 'bone': W = np.tile([0, 0, 0, 1], (len(P), 1)).astype(float)
    else: W = seg_weights(P)
    if n == 'Hip bone':                               # pelvis: placed by the thigh fit's translation only at the hip
        P2 = P - hipA + hipM
        for v, p in zip(o.data.vertices, P2): v.co = Vector(p)
        o.vertex_groups.clear(); vg = o.vertex_groups.new(name=f'pelvis.{SX}'); vg.add(list(range(len(P))), 1.0, 'REPLACE'); continue
    apply(o, W)
    if kind == 'bone' and 'phalanx' in n:             # toe bones ride his toe bones
        w = n.split(' of ')[1].split(' ')[0]; dgt = TOE_BONE[w]; sg = SEGN[n.split(' ')[0]]
        if dgt == 1: sg = 1 if sg == 1 else 2
        bn = f'toe{dgt}-{sg}.{SX}'; o.vertex_groups.clear(); vg = o.vertex_groups.new(name=bn); vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    o.data.update()
# ---------------- cut the parts that run up into the pelvis (the shots show the leg from the buttock down), and push anything still
# poking out back under his skin (displacement smoothed over the mesh so shapes don't dent)
import bmesh
ZCUT = hipM[2] - 0.05
for n in list(A):
    o = A[n]
    if n == 'Hip bone':
        bpy.data.objects.remove(o); del A[n]; continue
    if o['kind'] in ('nerve', 'artery', 'muscle'):
        bm_ = bmesh.new(); bm_.from_mesh(o.data)
        kill = [f for f in bm_.faces if min(v.co.z for v in f.verts) > ZCUT]
        if kill: bmesh.ops.delete(bm_, geom=kill, context='FACES')
        loose = [v for v in bm_.verts if not v.link_faces]
        if loose: bmesh.ops.delete(bm_, geom=loose, context='VERTS')
        bm_.to_mesh(o.data); bm_.free()
        if not len(o.data.vertices): bpy.data.objects.remove(o); del A[n]
MARGIN = 0.003
for n, o in A.items():
    me = o.data; P = np.array([v.co[:] for v in me.vertices]); D = np.zeros_like(P)
    for i, p in enumerate(P):
        loc, nor, idx, dist = SKIN.find_nearest(Vector(p)); sd = dist if (Vector(p) - loc).dot(nor) > 0 else -dist
        if sd > -MARGIN: D[i] = -np.array(nor[:]) * (sd + MARGIN)
    if not D.any(): continue
    nb = [[] for _ in range(len(P))]
    for e in me.edges: i, j = e.vertices; nb[i].append(j); nb[j].append(i)
    need = np.linalg.norm(D, axis=1)
    for it in range(12):                                  # spread the push to neighbours, never below what each vertex needs
        Dn = np.array([D[i] if not nb[i] else (D[i] + D[nb[i]].mean(0)) * 0.5 for i in range(len(P))])
        keep = np.linalg.norm(Dn, axis=1) < need
        Dn[keep] = D[keep]; D = Dn
    for v, p in zip(me.vertices, P + D): v.co = Vector(p)
    me.update()
# ---------------- how much sticks out of his skin (signed distance to the body surface, rest pose)
for md in BODY.modifiers:
    if md.type == 'MASK' and md.name.startswith('Delete'): md.show_viewport = md.show_render = False
dg = bpy.context.evaluated_depsgraph_get(); be = BODY.evaluated_get(dg); bm = be.to_mesh()
bvh = BVHTree.FromPolygons([BODY.matrix_world @ v.co for v in bm.vertices], [tuple(p.vertices) for p in bm.polygons]); be.to_mesh_clear()
for n, o in sorted(A.items()):
    outs = []
    for v in list(o.data.vertices)[::3]:
        loc, nor, idx, dist = bvh.find_nearest(v.co)
        if loc is not None and (v.co - loc).dot(nor) > 0: outs.append(dist)
    if outs: print(f'OUT {o["kind"]:6} {n:45} {len(outs):5} verts outside, max {max(outs) * 1000:.1f} mm')
for o in A.values(): o['fit'] = 1
bpy.data.libraries.write(out, set(A.values()), fake_user=True)
print('wrote', out)
