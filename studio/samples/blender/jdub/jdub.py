# Jalen Williams injury (Thunder vs Clippers, Oct 25 2026), Blender (Cycles), ONE continuous shot: he comes down from a dunk on his left
# leg, the foot stays planted, his body crashes over it, he ends up sitting on the court; the skin turns to x-ray, the landing is
# replayed slow on his left leg: tibia + fibula clamp the ankle (talus), the twist snaps the fibula, the talus pops out (dislocation);
# surgeons put it back and fix the bone; x-ray fades out and the play rewinds into the loop.
#   python3 jdub.py OUTDIR F0 F1 [--samples 24] [--scale 0.75] [--only f,f]
# Needs man.blend (../foot/man_build.py) and anat_l.blend (../foot/anat_build.py + anat_fit.py) beside it or in /root/vt/n60/jdub.
# Needs man.blend (../foot/man_build.py) beside it or in /root/vt/n60/jdub.
import sys, os, math, json, argparse, random
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n60/jdub', n)) if os.path.exists(p_))
TM = json.load(open(os.path.join(HERE, 'times.json'))); B, DUR, TOTAL = TM['starts'], TM['durs'], TM['total']
FPS = 30
STRIDE = json.load(open(os.path.join(HERE, 'stride.json'))) if os.path.exists(os.path.join(HERE, 'stride.json')) else None
REDO = json.load(open(os.path.join(HERE, 'redo.json'))) if os.path.exists(os.path.join(HERE, 'redo.json')) else None
def beat_at(t):
    for i in range(len(B) - 1, -1, -1):
        if t >= B[i]: return i
    return 0
clamp = lambda x, lo, hi: max(lo, min(hi, x))
sm = lambda x: x * x * (3 - 2 * x)
def smooth(e0, e1, x): return sm(clamp((x - e0) / (e1 - e0), 0, 1))
lerp = lambda p, q, k: p + (q - p) * k
def h1(n): return (math.sin(n * 127.1 + 311.7) * 43758.5453) % 1.0
def wob(t, f, seed=0.0): return mnoise.noise(Vector((t * f, seed, seed * 1.7)))
R = math.radians
V3 = lambda *p: Vector(p)

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('cycles', default_set=False)
S = bpy.context.scene; S.render.engine = 'CYCLES'; S.render.fps = FPS
S.render.resolution_x = int(1080 * a.scale); S.render.resolution_y = int(1920 * a.scale); S.render.resolution_percentage = 100
C = S.cycles; C.device = 'CPU'; C.samples = a.samples; C.use_denoising = os.environ.get('NODN') is None; C.denoiser = 'OPENIMAGEDENOISE'
C.max_bounces = 6; C.diffuse_bounces = 2; C.glossy_bounces = 2; C.transmission_bounces = 4; C.volume_bounces = 0; C.transparent_max_bounces = 24
C.use_adaptive_sampling = True; C.adaptive_threshold = 0.03; C.adaptive_min_samples = 12
C.caustics_reflective = False; C.caustics_refractive = False; C.sample_clamp_indirect = 6.0
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'; S.view_settings.exposure = 0.0

# ---------------------------------------------------------------- materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, estr=0.0, alpha=1.0, sheen=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior; b.inputs['Coat Weight'].default_value = coat; b.inputs['Alpha'].default_value = alpha
    b.inputs['Sheen Weight'].default_value = sheen
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    return m
def N(m): return m.node_tree.nodes
def L(m, a_, b_): m.node_tree.links.new(a_, b_)
def noisy(m, scale=40.0, amt=0.15, rough_amt=0.1, coord='Object'):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6; nt.links.new(tc.outputs[coord], nz.inputs['Vector'])
    base = b.inputs['Base Color'].default_value[:]; mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs['A'].default_value = base; mx.inputs['B'].default_value = tuple(c * (1 - amt) for c in base[:3]) + (1,)
    nt.links.new(nz.outputs['Fac'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    r0 = b.inputs['Roughness'].default_value; mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = max(0, r0 - rough_amt); mr.inputs['To Max'].default_value = r0 + rough_amt
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness']); return m
def emis(name, col, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = strength
    nt.links.new(e_.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m
def objattr(nt, name):
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = name; return at.outputs['Fac']
def math_(nt, op, a_, b_=None, c_=None):
    m_ = nt.nodes.new('ShaderNodeMath'); m_.operation = op
    for i, v in enumerate((a_, b_, c_)):
        if v is None: continue
        if isinstance(v, (int, float)): m_.inputs[i].default_value = v
        else: nt.links.new(v, m_.inputs[i])
    return m_.outputs['Value']

# ---------------------------------------------------------------- geometry helpers
def obj(name, me, m=None, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.location = loc
    if m: o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def mesh(name, vs, fs, m=None, parent=None, smooth_=True, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.validate(); me.update()
    if smooth_:
        for p in me.polygons: p.use_smooth = True
    return obj(name, me, m, loc, parent)
def empty(name, parent=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); S.collection.objects.link(o); o.location = loc
    if parent: o.parent = parent
    return o
def prim(kind, name, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), **kw):
    getattr(bpy.ops.mesh, 'primitive_' + kind + '_add')(location=(0, 0, 0), **kw); o = bpy.context.active_object; o.name = name
    o.scale = scale; bpy.ops.object.transform_apply(scale=True)
    o.location = loc; o.rotation_euler = rot
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o
def bevel(o, w, seg=3):
    md = o.modifiers.new('bv', 'BEVEL'); md.width = w; md.segments = seg; md.limit_method = 'ANGLE'; return o
def subsurf(o, lv=2):
    md = o.modifiers.new('ss', 'SUBSURF'); md.levels = lv; md.render_levels = lv; return o
def box(name, size, loc, m, bv=0.0, rot=(0, 0, 0), parent=None, ss=0):
    o = prim('cube', name, m, parent, loc=loc, rot=rot, size=1, scale=size)
    if bv: bevel(o, bv, 4)
    if ss: subsurf(o, ss)
    return o
def tube(name, pts, r, m, parent=None, seg=16, caps=True):
    pts = [Vector(p) for p in pts]; n = len(pts); rings = []; T0 = (pts[1] - pts[0]).normalized()
    up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized(); Bn = T0.cross(Nn)
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        rr = r(i / (n - 1)) if callable(r) else r
        rings.append([pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
    vs = [p for ring in rings for p in ring]; fs = []
    for i in range(n - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    if caps: fs.append(tuple(range(seg))[::-1]); fs.append(tuple((n - 1) * seg + k for k in range(seg)))
    return mesh(name, vs, fs, m, parent)
def lathe(name, prof, seg=48, m=None, parent=None, loc=(0, 0, 0)):
    """profile (r, z) turned about local z"""
    vs = [(r_ * math.cos(2 * math.pi * k / seg), r_ * math.sin(2 * math.pi * k / seg), z_) for r_, z_ in prof for k in range(seg)]; fs = []
    for i in range(len(prof) - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    return mesh(name, vs, fs, m, parent, loc=loc)
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
# ================================================================ camera + world
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.012, 0.014, 0.02, 1); WBG.inputs['Strength'].default_value = 1.0
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.03; CAM.data.clip_end = 3000
# ================================================================ THE COURT (an NBA arena: hardwood, Thunder-blue paint, the hoop, stands)
# Court frame: the hoop is at y = +HOOP_Y and faces -y; he comes down just in front of it, facing the hoop (+y).
HOOP_Y = 2.2; RIM_Z = 3.05
COURT = []
def wood_mat():
    m = bpy.data.materials.new('wood'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.28; b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.08
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    # boards 5.7 cm wide running along y, staggered butt joints; each board its own shade
    bx = math_(nt, 'FLOOR', math_(nt, 'DIVIDE', sx.outputs['X'], 0.057))
    by = math_(nt, 'FLOOR', math_(nt, 'DIVIDE', math_(nt, 'ADD', sx.outputs['Y'], math_(nt, 'MULTIPLY', math_(nt, 'FRACT', math_(nt, 'MULTIPLY', bx, 0.618)), 2.4)), 2.4))
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '2D'; cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(bx, cb.inputs['X']); nt.links.new(by, cb.inputs['Y'])
    nt.links.new(cb.outputs['Vector'], wn.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.55, 0.33, 0.16, 1); ramp.color_ramp.elements[1].color = (0.78, 0.52, 0.28, 1)
    nt.links.new(wn.outputs['Value'], ramp.inputs['Fac'])
    grain = nt.nodes.new('ShaderNodeTexWave'); grain.bands_direction = 'Y'; grain.inputs['Scale'].default_value = 3.0; grain.inputs['Distortion'].default_value = 12.0; grain.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], grain.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; nt.links.new(ramp.outputs['Color'], mx.inputs['A'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.85; nt.links.new(grain.outputs['Fac'], mr.inputs['Value'])
    cc = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(mr.outputs['Result'], cc.inputs[i]) for i in range(3)]; nt.links.new(cc.outputs['Color'], mx.inputs['B']); mx.inputs['Factor'].default_value = 1.0
    # the paint: the blue lane (4.9 m wide, 5.8 m from the baseline), white lines 5 cm, the restricted-area arc
    X, Y = sx.outputs['X'], sx.outputs['Y']; ax = math_(nt, 'ABSOLUTE', X)
    base_y = HOOP_Y + 1.2
    def lt_(a_, b_): return math_(nt, 'LESS_THAN', a_, b_)
    def gt_(a_, b_): return math_(nt, 'GREATER_THAN', a_, b_)
    lane = math_(nt, 'MULTIPLY', lt_(ax, 2.45), math_(nt, 'MULTIPLY', lt_(Y, base_y), gt_(Y, base_y - 5.8)))
    edge = math_(nt, 'MULTIPLY', lane, math_(nt, 'MAXIMUM', gt_(ax, 2.40), lt_(Y, base_y - 5.75)))
    dx = X; dy = math_(nt, 'SUBTRACT', Y, HOOP_Y); dr = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dy, dy)))
    arc = math_(nt, 'MULTIPLY', lt_(math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', dr, 1.22)), 0.025), lt_(Y, HOOP_Y))
    base_l = lt_(math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', Y, base_y)), 0.025)
    white = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MAXIMUM', edge, arc), base_l), 1.0)
    pm = nt.nodes.new('ShaderNodeMix'); pm.data_type = 'RGBA'; nt.links.new(mx.outputs['Result'], pm.inputs['A']); pm.inputs['B'].default_value = (0.0, 0.1, 0.3, 1)
    nt.links.new(math_(nt, 'MULTIPLY', lane, 0.93), pm.inputs['Factor'])
    wm = nt.nodes.new('ShaderNodeMix'); wm.data_type = 'RGBA'; nt.links.new(pm.outputs['Result'], wm.inputs['A']); wm.inputs['B'].default_value = (0.9, 0.9, 0.88, 1)
    nt.links.new(white, wm.inputs['Factor']); nt.links.new(wm.outputs['Result'], b.inputs['Base Color']); return m
FLOOR = mesh('floor', [(-16, -14, 0), (16, -14, 0), (16, 5, 0), (-16, 5, 0)], [(0, 1, 2, 3)], wood_mat(), smooth_=False); COURT.append(FLOOR)
# beyond the baseline: dark blue apron, the stanchion, the padded base
APRON = mesh('apron', [(-16, HOOP_Y + 1.2, 0.001), (16, HOOP_Y + 1.2, 0.001), (16, 12, 0.001), (-16, 12, 0.001)], [(0, 1, 2, 3)], mat('apron', (0.01, 0.06, 0.16), 0.5), smooth_=False); COURT.append(APRON)
PAD_M = mat('pad', (0.0, 0.18, 0.42), 0.55, sheen=0.3); STEEL_M = mat('steel', (0.15, 0.15, 0.17), 0.35, 0.9)
COURT.append(box('stanch_base', (1.2, 2.2, 0.9), V3(0, HOOP_Y + 3.6, 0.45), PAD_M, 0.06))
COURT.append(box('stanch_post', (0.32, 0.32, 3.2), V3(0, HOOP_Y + 3.0, 2.0), PAD_M, 0.04))
COURT.append(box('stanch_arm', (0.24, 2.4, 0.3), V3(0, HOOP_Y + 1.9, 3.55), PAD_M, 0.04, rot=(R(-12), 0, 0)))
GLASS_M = mat('glass', (0.9, 0.95, 1.0), 0.03, trans=1.0, ior=1.5)
BB = box('backboard', (1.83, 0.025, 1.07), V3(0, HOOP_Y + 0.38, RIM_Z + 0.35), GLASS_M, 0.004); COURT.append(BB)
LINE_W = emis('bbline', (1.0, 1.0, 1.0), 1.2)
for (sz, lc) in (((1.83, 0.03, 0.05), V3(0, HOOP_Y + 0.37, RIM_Z + 0.86)), ((1.83, 0.03, 0.05), V3(0, HOOP_Y + 0.37, RIM_Z - 0.16)),
                 ((0.05, 0.03, 1.07), V3(-0.89, HOOP_Y + 0.37, RIM_Z + 0.35)), ((0.05, 0.03, 1.07), V3(0.89, HOOP_Y + 0.37, RIM_Z + 0.35)),
                 ((0.59, 0.03, 0.05), V3(0, HOOP_Y + 0.365, RIM_Z + 0.43)), ((0.59, 0.03, 0.05), V3(0, HOOP_Y + 0.365, RIM_Z + 0.0)),
                 ((0.05, 0.03, 0.45), V3(-0.29, HOOP_Y + 0.365, RIM_Z + 0.21)), ((0.05, 0.03, 0.45), V3(0.29, HOOP_Y + 0.365, RIM_Z + 0.21))):
    COURT.append(box('bbl', sz, lc, LINE_W))
RIM_M = mat('rim', (0.95, 0.28, 0.03), 0.35, 0.6)
bpy.ops.mesh.primitive_torus_add(major_radius=0.2286, minor_radius=0.0095, major_segments=48, minor_segments=10, location=(0, HOOP_Y, RIM_Z))
RIM = bpy.context.active_object; RIM.name = 'rim'; RIM.data.materials.append(RIM_M); COURT.append(RIM)
COURT.append(box('rim_mount', (0.12, 0.17, 0.08), V3(0, HOOP_Y + 0.29, RIM_Z - 0.03), RIM_M, 0.01))
NET_M = mat('net', (0.97, 0.97, 0.97), 0.8)
for k in range(12):                                                     # net cords: zig-zag down and in
    a0 = 2 * math.pi * k / 12; a1 = a0 + math.pi / 12
    pts = [V3(0.225 * math.cos(a0), HOOP_Y + 0.225 * math.sin(a0), RIM_Z - 0.01), V3(0.18 * math.cos(a1), HOOP_Y + 0.18 * math.sin(a1), RIM_Z - 0.2),
           V3(0.14 * math.cos(a0), HOOP_Y + 0.14 * math.sin(a0), RIM_Z - 0.4)]
    COURT.append(tube('net%d' % k, pts, 0.004, NET_M, seg=6))
    pts2 = [V3(0.225 * math.cos(a1 + math.pi / 12), HOOP_Y + 0.225 * math.sin(a1 + math.pi / 12), RIM_Z - 0.01), V3(0.18 * math.cos(a1), HOOP_Y + 0.18 * math.sin(a1), RIM_Z - 0.2),
            V3(0.14 * math.cos(a1 + math.pi / 12), HOOP_Y + 0.14 * math.sin(a1 + math.pi / 12), RIM_Z - 0.4)]
    COURT.append(tube('netb%d' % k, pts2, 0.004, NET_M, seg=6))
# the ball, knocked loose (bounces away in the first beat)
def ball_mat():
    m = noisy(mat('ball', (0.62, 0.17, 0.03), 0.7), 260.0, 0.22); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    X, Y, Z = sx.outputs['X'], sx.outputs['Y'], sx.outputs['Z']
    def ln(v): return math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', v), 0.004)
    curve = math_(nt, 'SUBTRACT', math_(nt, 'ABSOLUTE', X), math_(nt, 'MULTIPLY_ADD', math_(nt, 'MULTIPLY', Z, Z), 3.5, 0.045))   # the two curved seams
    seam = math_(nt, 'MINIMUM', math_(nt, 'ADD', math_(nt, 'ADD', ln(X), ln(Z)), ln(curve)), 1.0)
    src = next(l.from_socket for l in nt.links if l.to_socket == b.inputs['Base Color'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(src, mx.inputs['A']); mx.inputs['B'].default_value = (0.02, 0.015, 0.01, 1)
    nt.links.new(seam, mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color']); return m
BALL_M = ball_mat()
BALL = prim('uv_sphere', 'ball', BALL_M, radius=0.12, segments=32, ring_count=16); COURT.append(BALL)
BSEAM = emis('seam', (0.02, 0.02, 0.02), 0.0)
# the stands: tiers of seated fans (rounded bodies, heads with hair, some arms up), out of focus behind him.
# A few template meshes are shared by every fan (linked copies), so the crowd is big but quick to build.
FANS = []; _r = random.Random(8)
SHIRTS = [(0.0, 0.25, 0.6), (0.9, 0.3, 0.05), (0.85, 0.85, 0.85), (0.05, 0.05, 0.07), (0.6, 0.1, 0.1), (0.0, 0.35, 0.7), (0.0, 0.25, 0.6), (0.85, 0.85, 0.85)]
FAN_MS = [noisy(mat('fan%d' % i, c, 0.85, sheen=0.4), 30.0, 0.15) for i, c in enumerate(SHIRTS)]
SKINS = [mat('fs%d' % i, c, 0.5) for i, c in enumerate([(0.45, 0.3, 0.22), (0.25, 0.15, 0.1), (0.62, 0.45, 0.35), (0.14, 0.08, 0.05)])]
HAIR_M = mat('fhair', (0.02, 0.015, 0.012), 0.6)
SEAT_M = mat('seat', (0.02, 0.035, 0.08), 0.6)
def _tmpl(kind, m, **kw):
    o = prim(kind, '_t', m, **kw); me = o.data; bpy.data.objects.remove(o); return me
_torso = [_tmpl('uv_sphere', m, radius=1.0, segments=16, ring_count=10, scale=(0.21, 0.15, 0.3)) for m in FAN_MS]
_head = [_tmpl('uv_sphere', m, radius=0.105, segments=14, ring_count=8) for m in SKINS]
_hair = _tmpl('uv_sphere', HAIR_M, radius=0.112, segments=14, ring_count=8, scale=(1.0, 1.0, 0.75))
_arm = [_tmpl('cylinder', m, radius=0.05, depth=0.5, vertices=8) for m in FAN_MS]
def _put(me, loc, rot=(0, 0, 0)):
    o = bpy.data.objects.new('fan', me); S.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; o.visible_shadow = False; FANS.append(o); return o
FLASH_M = emis('flash', (1.0, 0.97, 0.9), 0.0)
_fn = FLASH_M.node_tree.nodes['Emission']; FLASH_M.node_tree.links.new(math_(FLASH_M.node_tree, 'MULTIPLY', objattr(FLASH_M.node_tree, 'fl'), 400.0), _fn.inputs['Strength'])
FLASHES = []
def stand(x0, x1, y0, dy, rows, rot_):
    face = 1.0 if dy < 0 else -1.0                                # fans face the court
    for r_ in range(rows):
        z = 0.5 + r_ * 0.45; yy = y0 + r_ * dy
        COURT.append(box('tier', (abs(x1 - x0), 0.9, 0.45), V3((x0 + x1) / 2, yy, z - 0.225), SEAT_M) if rot_ == 0 else
                     box('tier', (0.9, abs(x1 - x0), 0.45), V3(yy, (x0 + x1) / 2, z - 0.225), SEAT_M))
        x = x0
        while x < x1:
            if _r.random() < 0.9:
                P = (lambda a_, b_, c_: V3(a_, b_, c_)) if rot_ == 0 else (lambda a_, b_, c_: V3(b_, a_, c_))
                lean = _r.uniform(-0.12, 0.12); ti = _r.randrange(len(FAN_MS)); hz = z + 0.3 + _r.uniform(-0.03, 0.05)
                rz = 0.0 if rot_ == 0 else R(90)
                _put(_torso[ti], P(x, yy, hz), (lean * 0.5, 0, rz + lean))
                hp = P(x, yy, hz + 0.39); _put(_head[_r.randrange(4)], hp)
                if _r.random() < 0.7: _put(_hair, hp + V3(0, 0, 0.025))
                if _r.random() < 0.18:                           # arms up, cheering
                    for sd in (-1, 1):
                        _put(_arm[ti], P(x + sd * 0.2, yy, hz + 0.45), (0, sd * R(-15), rz) if rot_ == 0 else (sd * R(15), 0, rz))
                if _r.random() < 0.05:                           # a phone up: flashes now and then
                    fo = prim('uv_sphere', 'fl', FLASH_M, loc=P(x + 0.12, yy + face * 0.25, hz + 0.3), radius=0.02, segments=6, ring_count=4)
                    fo['fl'] = 0.0; fo.visible_shadow = False; FLASHES.append(fo)
            x += _r.uniform(0.48, 0.58)
stand(-10.0, 10.0, HOOP_Y + 6.5, 0.9, 12, 0)
stand(-14.0, 5.0, -9.5, -0.9, 12, 1)
stand(-14.0, 9.5, 11.0, 0.9, 12, 1)                              # the far side: fills the right of the wide shot
COURT += FANS
# ---- the upper bowl: a dark wall over the stands, a glowing LED ribbon (Thunder blue + orange, scrolling) along its foot,
# a far upper deck of tiny lit specks (crowd too far to model), and rows of hanging light rigs that bloom out of focus
WALL_M = mat('wall', (0.008, 0.01, 0.018), 0.7)
def ribbon_mat():
    m = emis('ribbon', (1, 1, 1), 1.0); nt = m.node_tree; e_ = nt.nodes['Emission']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    u_ = math_(nt, 'ADD', math_(nt, 'ADD', sx.outputs['X'], sx.outputs['Y']), objattr(nt, 'scroll'))
    band = math_(nt, 'GREATER_THAN', math_(nt, 'FRACT', math_(nt, 'DIVIDE', u_, 3.0)), 0.5)
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.0, 0.35, 1.0, 1); col.inputs['B'].default_value = (1.0, 0.35, 0.02, 1)
    nt.links.new(band, col.inputs['Factor']); nt.links.new(col.outputs['Result'], e_.inputs['Color']); e_.inputs['Strength'].default_value = 6.0; return m
RIB_M = ribbon_mat(); RIBBONS = []
def deck_mat():
    m = bpy.data.materials.new('deck'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.01, 0.012, 0.02, 1)
    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 9.0
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.12; ramp.color_ramp.elements[1].color = (0, 0, 0, 1); el = ramp.color_ramp.elements.new(0.0); el.color = (0.9, 0.85, 0.75, 1)
    nt.links.new(vo.outputs['Distance'], ramp.inputs['Fac'])
    tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], tint.inputs['A']); nt.links.new(vo.outputs['Color'], tint.inputs['B'])
    nt.links.new(tint.outputs['Result'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 0.6; return m
DECK_M = deck_mat(); LAMP_M = emis('lamp', (1.0, 0.96, 0.88), 40.0)
def bowl(x0, x1, y0, rot_, out):
    """wall + ribbon + upper deck + light rigs above a stand; out = which way is away from the court (+1/-1)"""
    zt = 0.5 + 12 * 0.45; L_ = abs(x1 - x0); c = (x0 + x1) / 2; yb = y0 + out * 12 * 0.9
    P = (lambda a_, b_, c_: V3(a_, b_, c_)) if rot_ == 0 else (lambda a_, b_, c_: V3(b_, a_, c_))
    SZ = (lambda a_, b_, c_: (a_, b_, c_)) if rot_ == 0 else (lambda a_, b_, c_: (b_, a_, c_))
    COURT.append(box('wall', SZ(L_ + 6, 0.3, 4.0), P(c, yb + out * 0.6, zt + 1.6), WALL_M))
    rb = box('ribbon', SZ(L_ + 6, 0.05, 0.55), P(c, yb + out * 0.42, zt + 0.55), RIB_M); rb['scroll'] = 0.0; rb.visible_shadow = False; COURT.append(rb); RIBBONS.append(rb)
    dk = box('deck', SZ(L_ + 10, 0.2, 9.0), P(c, yb + out * 4.0, zt + 7.5), DECK_M, rot=(R(-out * 35), 0, 0) if rot_ == 0 else (0, R(out * 35), 0)); COURT.append(dk)
    for k in range(int(L_ // 2.2) + 3):                           # the hanging light rigs: a row of bright fixtures high up
        lp = box('lamp', (0.35, 0.35, 0.18), P(x0 - 3 + k * 2.2 + 1.1, yb - out * 1.5, zt + 4.8), LAMP_M); lp.visible_shadow = False; COURT.append(lp)
bowl(-10.0, 10.0, HOOP_Y + 6.5, 0, 1)
bowl(-14.0, 5.0, -9.5, 1, -1)
bowl(-14.0, 9.5, 11.0, 1, 1)
# the arena lights: big soft overheads (an NBA court is lit flat and bright) and a warm rim light from the stands side
LIGHTS = [light_at('over1', 'AREA', V3(-2.0, 0.0, 12.0), V3(0, 0.5, 0), 4200, (1.0, 0.97, 0.92), 8.0),
          light_at('over2', 'AREA', V3(3.0, -4.0, 12.0), V3(0, 0.5, 0), 3000, (1.0, 0.97, 0.92), 8.0),
          light_at('rimL', 'AREA', V3(-6.0, 6.0, 5.0), V3(0, 0.6, 1.0), 900, (1.0, 0.85, 0.7), 3.0),
          light_at('fill', 'AREA', V3(-5.0, -5.0, 2.5), V3(0, 0.6, 0.8), 170, (0.8, 0.88, 1.0), 4.0),
          light_at('back', 'AREA', V3(2.5, 6.5, 6.0), V3(0.45, 1.25, 0.9), 1400, (0.75, 0.85, 1.0), 2.0)]
for _o in LIGHTS: _o['e0'] = _o.data.energy
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HAIR = bpy.data.objects['Human.short02']; HEADBITS = [o for o in bpy.data.objects if o.name.startswith('Human.') and o not in (BODY, SUIT, RIG)]
RB = RIG.data.bones; PB = RIG.pose.bones
KNEE_Z = RB['lowerleg01.R'].head_local.z
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
    for p_ in o.data.polygons: p_.use_smooth = True
# ---- the kit: the casual suit cut down to a basketball tank and shorts (Thunder home whites, #8). Cut faces are deleted from the suit,
# so the skin under them shows; nothing new is laid on top, so nothing can clip.
_vgs = {g.index: g.name for g in SUIT.vertex_groups}
_bm = bmesh.new(); _bm.from_mesh(SUIT.data); _dl = _bm.verts.layers.deform.active
def _armw(v):
    d_ = v[_dl]; return sum(w for gi, w in d_.items() if _vgs[gi].startswith(('upperarm', 'lowerarm')))
_cut = []
for f_ in _bm.faces:
    zc = sum(v.co.z for v in f_.verts) / len(f_.verts)
    aw = sum(_armw(v) for v in f_.verts) / len(f_.verts)
    xc = abs(sum(v.co.x for v in f_.verts) / len(f_.verts))
    if zc < KNEE_Z + 0.13: _cut.append(f_)                        # shorts end a hand above the knee
    elif aw > 0.25 and zc > 1.0: _cut.append(f_)                   # sleeves off: a tank top
    elif zc > 1.34 and xc > 0.085: _cut.append(f_)                 # wide tank shoulders: open over the shoulder caps
bmesh.ops.delete(_bm, geom=_cut, context='FACES'); _bm.to_mesh(SUIT.data); _bm.free(); SUIT.data.update()
# the skin under the cut-away cloth: MakeHuman hides body faces under the suit ('Delete.male_casualsuit06' mask). Take the legs below the
# shorts and the arms back out of that group (with 3 cm of overlap under the cloth edges so no gap can open)
_dg_ = BODY.vertex_groups.get('Delete.male_casualsuit06'); _bvg = {g.index: g.name for g in BODY.vertex_groups}
if _dg_ is not None:
    _free = []
    for v in BODY.data.vertices:
        aw = sum(g.weight for g in v.groups if _bvg[g.group].startswith(('upperarm', 'lowerarm')))
        sw = sum(g.weight for g in v.groups if _bvg[g.group].startswith(('shoulder', 'clavicle')))
        if v.co.z < KNEE_Z + 0.10 or (aw > 0.05 and v.co.z > 1.0) or (v.co.z > 1.28 and abs(v.co.x) > 0.075) or sw > 0.35: _free.append(v.index)
    _dg_.remove(_free)
sol = SUIT.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0035; sol.offset = 1.0
subsurf(BODY, 1); subsurf(SUIT, 1)
BODY.add_rest_position_attribute = True; SUIT.add_rest_position_attribute = True
def kit_mat():
    """white mesh jersey + shorts; Thunder blue and orange trim at the hems, side panels; a blue #8 front and back (rest-space rings)"""
    m = bpy.data.materials.new('kit'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.62; b.inputs['Sheen Weight'].default_value = 0.4
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector']); X, Y, Z = sx.outputs['X'], sx.outputs['Y'], sx.outputs['Z']
    ax = math_(nt, 'ABSOLUTE', X)
    def band(v, lo, hi): return math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', v, lo), math_(nt, 'LESS_THAN', v, hi))
    hem = KNEE_Z + 0.13
    blue = math_(nt, 'MAXIMUM', band(Z, hem, hem + 0.035), band(ax, 0.19, 0.40))               # shorts hem + side panels
    orng = band(Z, hem + 0.035, hem + 0.05)
    # the number 8: two stacked rings, on the chest (y < 0) and the back (y > 0)
    def ring(cz, r):
        dx = X; dz = math_(nt, 'SUBTRACT', Z, cz)
        d = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dz, dz)))
        return math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', d, r)), 0.012)
    eight = math_(nt, 'MAXIMUM', ring(1.205, 0.033), ring(1.135, 0.04))
    torso = band(Z, 1.06, 1.27)
    num = math_(nt, 'MULTIPLY', eight, torso)
    blue = math_(nt, 'MAXIMUM', blue, num)
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.86, 0.87, 0.88, 1); col.inputs['B'].default_value = (0.0, 0.19, 0.45, 1)
    nt.links.new(blue, col.inputs['Factor'])
    col2 = nt.nodes.new('ShaderNodeMix'); col2.data_type = 'RGBA'; nt.links.new(col.outputs['Result'], col2.inputs['A']); col2.inputs['B'].default_value = (0.85, 0.16, 0.05, 1)
    nt.links.new(orng, col2.inputs['Factor'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900.0; nt.links.new(rp.outputs['Vector'], nz.inputs['Vector'])
    mesh_ = nt.nodes.new('ShaderNodeMix'); mesh_.data_type = 'RGBA'; mesh_.blend_type = 'MULTIPLY'; nt.links.new(col2.outputs['Result'], mesh_.inputs['A'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.9; mr.inputs['To Max'].default_value = 1.03; nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    cc = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(mr.outputs['Result'], cc.inputs[i]) for i in range(3)]
    nt.links.new(cc.outputs['Color'], mesh_.inputs['B']); mesh_.inputs['Factor'].default_value = 1.0
    nt.links.new(mesh_.outputs['Result'], b.inputs['Base Color']); return m
KIT_M = kit_mat(); SUIT.data.materials.clear(); SUIT.data.materials.append(KIT_M)
# his skin a deep brown (multiply over the MakeHuman skin texture, keeping its detail)
def skin_tone(m, col):
    nt = m.node_tree; g_ = next((n for n in nt.nodes if n.type == 'GROUP'), None)
    if g_ is not None:
        nt = g_.node_tree
        if nt.get('toned'): return
        nt['toned'] = 1
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    if lk: nt.links.new(lk.from_socket, mul.inputs['A'])
    else: mul.inputs['A'].default_value = b.inputs['Base Color'].default_value[:]
    mul.inputs['B'].default_value = (*col, 1); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    if 'Subsurface Weight' in b.inputs: b.inputs['Subsurface Weight'].default_value = 0.08
def hair_dark(m):
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED' or n.type == 'BSDF_HAIR_PRINCIPLED':
            if 'Base Color' in n.inputs:
                lk = next((l for l in nt.links if l.to_socket == n.inputs['Base Color']), None)
                if lk: nt.links.remove(lk)
                n.inputs['Base Color'].default_value = (0.012, 0.009, 0.008, 1)
if 'Human.short02' in bpy.data.materials: hair_dark(bpy.data.materials['Human.short02'])
for nm in ('Human.body', 'Human.ears', 'Human.lips', 'Human.nipple'):
    if nm in bpy.data.materials: skin_tone(bpy.data.materials[nm], (0.3, 0.19, 0.13))
# sneakers painted onto his feet (every face mostly weighted to the foot and toe bones), so nothing can clip through them; white socks above
SHOE_M = noisy(mat('sneaker', (0.0, 0.2, 0.45), 0.5), 60.0, 0.12); SOLE_M = mat('sole', (0.92, 0.92, 0.9), 0.6); SOCK_M = noisy(mat('sock', (0.9, 0.9, 0.9), 0.9, sheen=0.5), 300.0, 0.08)
BODY.data.materials.append(SHOE_M); BODY.data.materials.append(SOLE_M); BODY.data.materials.append(SOCK_M); _shoe_i = len(BODY.data.materials) - 3
_vgn = {g.index: g.name for g in BODY.vertex_groups}
_footw = np.zeros(len(BODY.data.vertices))
for v in BODY.data.vertices:
    _footw[v.index] = sum(g.weight for g in v.groups if _vgn[g.group].startswith(('foot.', 'toe')))
for p_ in BODY.data.polygons:
    w_ = float(np.mean([_footw[i] for i in p_.vertices])); zc = sum(BODY.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices)
    if w_ > 0.45:
        p_.material_index = _shoe_i + 1 if zc < 0.018 else _shoe_i
    elif zc < 0.2 and zc > 0.0: p_.material_index = _shoe_i + 2
# ================================================================ HIS LEFT LEG'S BONES (anat_l.blend: the Z-Anatomy left leg, fitted in his rest space)
ANAT = []
with bpy.data.libraries.load(asset('anat_l.blend'), link=False) as (_s, _d): _d.objects = list(_s.objects)
for o in _d.objects:
    if o['kind'] != 'bone': continue
    S.collection.objects.link(o); o.parent = RIG; o.matrix_world = Matrix.Identity(4)
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False; o.add_rest_position_attribute = True; ANAT.append(o)
AN = {o.name: o for o in ANAT}
TIB, FIB, TAL = AN['Tibia.L'], AN['Fibula.L'], AN['Talus.L']
FOOTB = [o for o in ANAT if o not in (TIB, FIB) and o.name not in ('Femur.L', 'Patella.L', 'Hip bone.L')]
def bone_mat(name):
    """bone: warm ivory with a cool x-ray rim; 'hi' lights it yellow (named on screen), 'crack' (fibula) burns red around the break"""
    m = mat(name, (0.86, 0.82, 0.72), 0.5); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    band = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', sx.outputs['Z'], FIB_CUT)), 0.03)), 0.0), 2.0)
    crack = math_(nt, 'MULTIPLY', band, objattr(nt, 'crack'))
    hi = objattr(nt, 'hi')
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.7, 0.85, 1.0, 1); col.inputs['B'].default_value = (1.0, 0.8, 0.2, 1)
    nt.links.new(math_(nt, 'MINIMUM', hi, 1.0), col.inputs['Factor'])
    col2 = nt.nodes.new('ShaderNodeMix'); col2.data_type = 'RGBA'; nt.links.new(col.outputs['Result'], col2.inputs['A']); col2.inputs['B'].default_value = (1.0, 0.12, 0.05, 1)
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', crack, 3.0), 1.0), col2.inputs['Factor'])
    nt.links.new(col2.outputs['Result'], b.inputs['Emission Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'ADD', math_(nt, 'MULTIPLY', lw.outputs['Facing'], 0.9), math_(nt, 'MULTIPLY', hi, 1.6)), math_(nt, 'MULTIPLY', crack, 8.0)),
                 b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
FIB_CUT = 0.17                                                   # the break: low on the fibula, a hand above the ankle (rest z, m)
for o in ANAT:
    o.data.materials.clear(); o.data.materials.append(bone_mat('bone_' + o.name)); o['hi'] = 0.0; o['crack'] = 0.0
# ---- the break and the dislocation as shape keys in his rest space (the armature carries them into any pose)
def _keys(o):
    if o.data.shape_keys is None: o.shape_key_add(name='Basis')
    return o.shape_key_add(name='k', from_mix=False)
_fx = sum(v.co.x for v in FIB.data.vertices) / len(FIB.data.vertices)
_low = [v for v in FIB.data.vertices if v.co.z < FIB_CUT]; _cx = sum(v.co.x for v in _low) / len(_low); _cy = sum(v.co.y for v in _low) / len(_low)
KB = _keys(FIB)
for v in FIB.data.vertices:
    p = v.co.copy()
    if p.z < FIB_CUT:                                             # the low piece: tips out about the break and slides out with the ankle
        q = p - V3(_cx, _cy, FIB_CUT); q = Matrix.Rotation(R(-14), 3, 'Y') @ q; KB.data[v.index].co = V3(_cx, _cy, FIB_CUT) + q + V3(0.016, -0.004, -0.006)
    else:
        k = clamp((p.z - FIB_CUT) / 0.03, 0, 1); KB.data[v.index].co = p + V3(-0.004 * (1 - k), 0.0, 0.0)
FIB_KEY = FIB.data.shape_keys.key_blocks['k']
DISL = []
for o in [TAL] + FOOTB:                                           # the talus and the whole foot shift out of the ankle socket
    kb = _keys(o)
    for v in o.data.vertices:
        p = v.co; kb.data[v.index].co = p + V3(0.026, 0.006, -0.008) + (Matrix.Rotation(R(-10), 3, 'Y') @ (p - V3(0.19, -0.03, 0.06)) - (p - V3(0.19, -0.03, 0.06)))
    DISL.append(o.data.shape_keys.key_blocks['k'])
def injury(brk, disl):
    FIB_KEY.value = brk
    for k in DISL: k.value = disl
# ---- x-ray: every material on him gets a mix to a see-through blue glow; 'xr' (on the object) runs it 0..1
def xray_wrap(m):
    if m is None or m.get('xw'): return
    m['xw'] = 1; nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); lk = next((l for l in nt.links if l.to_socket == out.inputs['Surface']), None)
    if lk is None: return
    src = lk.from_socket
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.4
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.2)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.35, 0.62, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY_ADD', fz, 1.4, 0.02), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gm = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY_ADD', fz, 0.55, 0.03), 1.0), gm.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], gm.inputs[1]); nt.links.new(em.outputs['Emission'], gm.inputs[2])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac']); nt.links.new(src, mx.inputs[1]); nt.links.new(gm.outputs['Shader'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
MAN = [BODY, SUIT, HAIR] + HEADBITS
for o in MAN:
    o['xr'] = 0.0
    for sl in o.material_slots: xray_wrap(sl.material)
def xray(k):
    for o in MAN: o['xr'] = k
    for o in ANAT: o.hide_render = k < 0.02
from mathutils.bvhtree import BVHTree
def ik(bone, target, pole, chain, pole_angle=R(-90)):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TGT = {k: empty('tgt_' + k) for k in ('ankR', 'ankL', 'poleR', 'poleL', 'handR', 'handL', 'poleArmR', 'poleArmL')}
for s_ in ('R', 'L'):
    ik('lowerleg02.' + s_, TGT['ank' + s_], TGT['pole' + s_], 4)
    for bn in ('lowerleg02.', 'upperleg02.'):
        pb = PB[bn + s_]; pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = True
    ik('lowerarm02.' + s_, TGT['hand' + s_], TGT['poleArm' + s_], 4)      # the arm reaches the WRIST JOINT; the hand then turns freely about it
RIG.rotation_mode = 'XYZ'
def _hand_frame(side):
    b = RB; d = (b['finger3-1.' + side].head_local - b['wrist.' + side].head_local).normalized()
    n = b['finger3-1.' + side].matrix_local.to_3x3().col[2]; n = (n - d * n.dot(d)).normalized()
    return Matrix((d.cross(n), d, n)).transposed()
HAND = {}
for s_ in ('R', 'L'):
    Hr = _hand_frame(s_); Wr = RB['wrist.' + s_].matrix_local.to_3x3()
    e_ = empty('tgt_rot' + s_); e_.rotation_mode = 'QUATERNION'
    c_ = PB['wrist.' + s_].constraints.new('COPY_ROTATION'); c_.target = e_; c_.owner_space = c_.target_space = 'WORLD'; c_.influence = 0.0
    HAND[s_] = (Hr.transposed() @ Wr, e_, c_)
def hand_quat(s_, fdir, pdir):
    O, e_, c_ = HAND[s_]; d = Vector(fdir).normalized(); n = Vector(pdir); n = (n - d * n.dot(d)).normalized(); a_ = d.cross(n)
    return (Matrix((a_, d, n)).transposed() @ O).to_quaternion()
def rot(bn, x=0.0, y=0.0, z=0.0):
    pb = PB[bn]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(x), R(y), R(z))
def fingers(s_, curl, spread=0.0):
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            nm = f'finger{f_}-{seg}.{s_}'
            if nm in PB: ang = (10, 15, 8)[seg - 1] if f_ == 1 else (40, 55, 30)[seg - 1]; rot(nm, ang * curl, 0, (f_ - 3) * spread * (1 if seg == 1 else 0))
def wpos(bn, tail=False):
    pb = PB[bn]; return RIG.matrix_world @ (pb.tail if tail else pb.head)
def bone_world(bn, tail=False): return wpos(bn, tail)
HIP0 = (RB['upperleg01.R'].head_local + RB['upperleg01.L'].head_local) * 0.5
PALM_D = 0.068                                         # wrist joint to the middle of the palm (m, measured on his rest pose)
PALM_T = 0.013                                         # palm skin above the hand bones
def set_pose(hip, rig_rot=(0, 0, 0), spine=0.0, neck=0.0, head=0.0, head_yaw=0.0, side_lean=0.0,
             ankR=None, poleR=None, footR=(0, 0, 0), toesR=0.0, ankL=None, poleL=None, footL=(0, 0, 0), toesL=0.0,
             curlR=0.3, curlL=0.3, lids=0.0, jaw=0.0, poleArmR=None, poleArmL=None):
    """hip = where the centre of his hip joints goes (world); the rig turns about it"""
    RIG.rotation_euler = tuple(R(x) for x in rig_rot)
    RIG.location = Vector(hip) - RIG.rotation_euler.to_matrix() @ HIP0
    for n, k in (('spine03', 0.3), ('spine02', 0.35), ('spine01', 0.35)): rot(n, spine * k, 0, side_lean * k)
    for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)): rot(n, neck * k, head_yaw * k * 0.5)
    rot('head', head, head_yaw * 0.5)
    rot('orbicularis03.R', LID_SIGN * 26 * lids); rot('orbicularis03.L', LID_SIGN * 26 * lids)
    rot('orbicularis04.R', -LID_SIGN * 8 * lids); rot('orbicularis04.L', -LID_SIGN * 8 * lids)
    rot('jaw', JAW_SIGN * 16 * jaw)
    TGT['ankR'].location = ankR; TGT['ankL'].location = ankL; TGT['poleR'].location = poleR; TGT['poleL'].location = poleL
    rot('foot.R', *footR); rot('foot.L', *footL)
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            for s_, tc in (('R', toesR), ('L', toesL)):
                nm = f'toe{f_}-{seg}.{s_}'
                if nm in PB: rot(nm, tc * (28 if seg == 1 else 22))
    TGT['poleArmR'].location = poleArmR if poleArmR is not None else RIG.matrix_world @ V3(-0.7, 0.35, 1.0)
    TGT['poleArmL'].location = poleArmL if poleArmL is not None else RIG.matrix_world @ V3(0.7, 0.35, 1.0)
    fingers('R', curlR); fingers('L', curlL)
    bpy.context.view_layer.update()
LID_SIGN = -1.0; JAW_SIGN = 1.0                          # tested: lids close with a negative turn, the jaw opens with a positive one
def place_hand(s_, contact, fdir, pdir, w_rot=1.0):
    """put the middle of his palm on 'contact', fingers along fdir, palm facing pdir (into the surface)"""
    d = Vector(fdir).normalized(); n = Vector(pdir); n = (n - d * n.dot(d)).normalized()
    TGT['hand' + s_].location = Vector(contact) - n * PALM_T - d * PALM_D
    O, e_, c_ = HAND[s_]; c_.influence = w_rot; e_.rotation_quaternion = hand_quat(s_, d, n)
def look(cp, ct, lens=35, fstop=8.0, focus=None, roll=0.0, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    q = d.to_track_quat('-Z', 'Y')
    if up is not None:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0): return Vector((wob(t, 7.0, seed), wob(t, 7.0, seed + 3.3), wob(t, 7.0, seed + 6.1))) * amt
def eval_centroid(o, idx=None):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    vs = me.vertices if idx is None else [me.vertices[i] for i in idx]; c = sum((oe.matrix_world @ v.co for v in vs), Vector()) / len(vs); oe.to_mesh_clear(); return c
def ease(a_, b_, k): return a_.lerp(b_, sm(clamp(k, 0, 1)))
# ================================================================ HIM: the landing as story time s (seconds of the real play)
BASE = V3(0.45, 1.25, 0.0)                     # where he comes down; he faces the hoop (+y)
def Wd(x, y, z): return BASE + V3(-x, -y, z)    # his own frame (he faces -y, left = +x) -> the court
KEYS = [  # s, pose (his frame: left = +x, forward = -y)
    (0.00, dict(hip=(0.0, 0.02, 1.45), lean=-6, side=0, spine=6, head=-8, ankL=(0.11, -0.04, 0.66), poleL=(0.15, -1.0, 0.95), ankR=(-0.12, 0.17, 0.92), poleR=(-0.15, -1.0, 1.3),
                handL=(0.17, -0.2, 2.25), handR=(-0.13, -0.24, 2.3), ev=0.0, plant=0.0)),
    (0.45, dict(hip=(0.03, 0.0, 0.93), lean=6, side=-4, spine=12, head=0, ankL=(0.13, -0.03, 0.075), poleL=(0.2, -1.0, 0.6), ankR=(-0.14, 0.2, 0.42), poleR=(-0.2, -1.0, 0.8),
                handL=(0.47, -0.12, 1.55), handR=(-0.44, -0.16, 1.6), ev=0.0, plant=1.0)),
    (0.72, dict(hip=(0.22, 0.03, 0.55), lean=12, side=-22, spine=16, head=6, ankL=(0.13, -0.03, 0.075), poleL=(-0.6, -1.0, 0.45), ankR=(-0.2, 0.12, 0.2), poleR=(-0.3, -1.0, 0.6),
                handL=(0.62, -0.25, 0.95), handR=(-0.5, -0.3, 1.05), ev=1.0, plant=1.0)),
    (1.10, dict(hip=(0.32, 0.10, 0.2), lean=-18, side=-8, spine=8, head=10, ankL=(0.26, -0.55, 0.085), poleL=(0.45, -1.0, 0.75), ankR=(-0.1, -0.32, 0.085), poleR=(-0.3, -1.0, 1.0),
                handL=(0.68, 0.3, 0.06), handR=(-0.02, 0.3, 0.06), ev=1.0, plant=0.0)),
    (1.80, dict(hip=(0.32, 0.12, 0.12), lean=-24, side=-4, spine=6, head=16, ankL=(0.32, -0.66, 0.085), poleL=(0.4, -1.0, 1.0), ankR=(0.0, -0.38, 0.085), poleR=(-0.25, -1.0, 1.25),
                handL=(0.68, 0.38, 0.0), handR=(-0.03, 0.38, 0.0), ev=1.0, plant=0.0)),
]
S_END = KEYS[-1][0]
def pose_at(s):
    s = clamp(s, 0.0, S_END)
    for i in range(len(KEYS) - 1):
        if s <= KEYS[i + 1][0]: break
    s0, P0 = KEYS[i]; s1, P1 = KEYS[i + 1]; k = sm((s - s0) / (s1 - s0))
    out = {}
    for key in P0:
        a_, b_ = P0[key], P1[key]
        out[key] = tuple(lerp(x, y, k) for x, y in zip(a_, b_)) if isinstance(a_, tuple) else lerp(a_, b_, k)
    return out
EV_ROLL, EV_TURN = 38.0, 30.0                   # the foot rolled out and turned out ('his left foot bent out to the side')
def hand_floor(side, p, w):
    O, e_, c_ = HAND[side]
    if w <= 0.01: c_.influence = 0.0; TGT['hand' + side].location = p; return
    place_hand(side, p + V3(0, 0, PALM_T + 0.004), V3(0, 1, 0) if side == 'L' else V3(0, 1, 0), V3(0, 0, -1), w)
    TGT['hand' + side].location = TGT['hand' + side].location.lerp(p, 1 - w)
# ---- nothing through the floor: after posing, lift each foot / hand target (or the whole body) by however far its skin dips under z=0
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'SUBSURF' or md.name.startswith('Delete'): md.show_viewport = False
_vgB = {g.index: g.name for g in BODY.vertex_groups}
def _idx(pref):
    return np.array([v.index for v in BODY.data.vertices if sum(g.weight for g in v.groups if _vgB[g.group].startswith(pref)) > 0.5], dtype=np.int64)
PART_IDX = {'ankL': _idx(('foot.L', 'toe1-', 'toe2-', 'toe3-', 'toe4-', 'toe5-')), 'handL': _idx(('wrist.L', 'finger', 'metacarpal')),
            'handR': _idx(('wrist.R',)), 'ankR': _idx(('foot.R',))}
for k_ in ('ankL', 'ankR', 'handL', 'handR'):                       # toes / fingers split by side
    sd = k_[-1]; PART_IDX[k_] = np.array([i for i in _idx(('foot.' + sd, 'toe', 'wrist.' + sd, 'finger', 'metacarpal')) if
        any(_vgB[g.group].endswith('.' + sd) and g.weight > 0.3 for g in BODY.data.vertices[i].groups) and
        any(_vgB[g.group].startswith(('foot', 'toe')) if k_.startswith('ank') else _vgB[g.group].startswith(('wrist', 'finger', 'metacarpal')) for g in BODY.data.vertices[i].groups)], dtype=np.int64)
FLOOR_EPS = 0.005
def _zs(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); oe.to_mesh_clear(); co = co.reshape(-1, 3)
    M = np.array(oe.matrix_world); return co @ M[:3, :3].T + M[:3, 3]
_NB = None
def unfloor():
    global _NB
    if _NB is None:
        _NB = len(_zs(BODY))
        for k_ in PART_IDX: PART_IDX[k_] = PART_IDX[k_][PART_IDX[k_] < _NB]
    for _ in range(6):
        P = _zs(BODY); lift = False
        for k_, idx in PART_IDX.items():
            if len(idx) == 0: continue
            z = P[idx, 2].min()
            if z < FLOOR_EPS: TGT[k_].location.z += FLOOR_EPS - z; lift = True
        rest = min(P[:, 2].min(), _zs(SUIT)[:, 2].min())
        if not lift and rest < FLOOR_EPS:
            RIG.location.z += FLOOR_EPS - rest; lift = True
            for k_ in PART_IDX: TGT[k_].location.z += FLOOR_EPS - rest
        if not lift: break
        bpy.context.view_layer.update()
def pose(s, evk=1.0, wince=0.0):
    P = pose_at(s); ev = P['ev'] * evk
    hip = Wd(*P['hip'])
    set_pose(hip, rig_rot=(P['lean'], P['side'], 180.0), spine=P['spine'], neck=P['head'] * 0.5, head=P['head'] * 0.5,
             ankL=Wd(*P['ankL']), poleL=Wd(*P['poleL']), footL=(0, -EV_ROLL * ev, -EV_TURN * ev), toesL=0.0,
             ankR=Wd(*P['ankR']), poleR=Wd(*P['poleR']), footR=(0, 0, 0), curlR=0.35, curlL=0.35, jaw=0.25 * wince, lids=0.25 * wince,
             poleArmR=Wd(-0.9, 0.5, 1.2), poleArmL=Wd(0.9, 0.5, 1.2))
    seat = smooth(1.0, 1.6, s)
    hand_floor('L', Wd(*P['handL']), seat); hand_floor('R', Wd(*P['handR']), seat)
    bpy.context.view_layer.update(); unfloor()
# ---- the ball: knocked off his hand, falls and bounces away toward the corner (a function of s, so it rewinds too)
def ball_at(s):
    p0 = Wd(-0.05, -0.45, 2.45); v = V3(-1.1, 1.4, 0.6); g = 9.8; r = 0.12   # back under the hoop: out of the lens and never across his face
    t_ = s; z0 = p0.z; vz = v.z; x = p0.x; y = p0.y
    while True:                                                   # bounces lose 30% each time
        tf = (vz + math.sqrt(vz * vz + 2 * g * (z0 - r))) / g
        if t_ < tf or vz < 0.4 and tf < 0.02: break
        t_ -= tf; x += v.x * tf; y += v.y * tf; vz = -(vz - g * tf) * 0.7; z0 = r; v = V3(v.x * 0.85, v.y * 0.85, vz)
        if abs(vz) < 0.4: return V3(x + v.x * t_ * 0.5, y + v.y * t_ * 0.5, r)
    return V3(x + v.x * t_, y + v.y * t_, max(r, z0 + vz * t_ - 0.5 * g * t_ * t_))
# ================================================================ the story: one continuous shot
def shin_mid():
    return (wpos('lowerleg01.L') + wpos('foot.L')) * 0.5
def ankle_pt(): return wpos('foot.L') + V3(0, 0, 0.02)
CAM_WIDE = (V3(-2.05, -0.35, 1.5), V3(0.3, 1.35, 1.5), 26.0)
def cam_follow(tgt, off, lens): return (tgt + off, tgt, lens)
def cam_blend(A, Bc, k):
    k = sm(clamp(k, 0, 1)); return (A[0].lerp(Bc[0], k), A[1].lerp(Bc[1], k), lerp(A[2], Bc[2], k))
def story_s(t):
    nb = beat_at(t); lt = t - B[nb]; u = lt / DUR[nb]
    if nb == 0:
        if u < 0.15: return lerp(0.0, 0.36, u / 0.15)
        if u < 0.6: return lerp(0.36, 0.74, (u - 0.15) / 0.45)            # slow motion through the landing
        return lerp(0.74, S_END, sm((u - 0.6) / 0.4))
    if nb == 1: return S_END
    if nb == 2: return lerp(S_END, 0.45, sm(clamp(lt / 1.5, 0, 1)))       # x-ray replay: rewind to the moment his foot lands
    if nb == 3: return 0.45
    if nb == 4: return lerp(0.45, 0.62, sm(u))                           # super slow: the body keeps going, the ankle twists
    if nb in (5, 6): return 0.62 + 0.04 * (u if nb == 5 else 1.0)
    if nb == 7: return lerp(0.66, S_END, sm(clamp(lt / 1.8, 0, 1)))
    if nb in (8, 9, 10): return S_END
    return lerp(S_END, 0.0, sm(clamp(lt / max(DUR[11] - 0.25, 0.1), 0, 1)))   # the rewind into the loop
def trk(t, pts):
    """piecewise smooth track over global time; flat before the first and after the last point"""
    if t <= pts[0][0]: return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1: return lerp(v0, v1, sm((t - t0) / max(t1 - t0, 1e-6)))
    return pts[-1][1]
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; u = lt / DUR[nb]
    s = story_s(t)
    evk = 1.0; brk = 0.0; disl = 0.0; xr = 0.0; crack = 0.0
    hi = {TIB: 0.0, FIB: 0.0, TAL: 0.0}
    if nb in (2, 3): evk = smooth(0.4, 1.4, 1.5 - lt) if nb == 2 else 0.0      # rewinding: the foot straightens as the play goes back
    if nb == 4: evk = smooth(0.15, 1.0, u)
    if nb >= 5: brk = 1.0 if nb > 5 else smooth(0.3, 0.42, lt)
    if nb >= 6: disl = smooth(0.45, 1.2, lt) if nb == 6 else 1.0
    if nb == 9: disl = 1.0 - smooth(0.2, 1.0, lt); brk = 1.0 - smooth(1.0, 2.0, lt); evk = 1.0 - smooth(0.2, 1.2, lt)
    if nb == 10: evk = 0.0
    if nb == 11: evk = 0.0
    if nb in (2, 3, 4, 5, 6, 7, 8, 9): xr = smooth(0.0, 0.9, lt) if nb == 2 else 1.0
    if nb == 10: xr = 1.0 - smooth(0.4, 1.6, lt)
    hi[TIB] = trk(t, [(B[2] + 1.6, 0), (B[2] + 2.0, 1), (B[2] + 3.4, 1), (B[2] + 3.8, 0.55), (B[4] + 0.2, 0.55), (B[4] + 0.8, 0.0)])
    hi[FIB] = trk(t, [(B[2] + 3.4, 0), (B[2] + 3.8, 1), (B[3] + 0.4, 0.55), (B[4] + 0.8, 0.45), (B[6] + 0.3, 0.45), (B[6] + 0.8, 0.0),
                      (B[9] + 1.6, 0.0), (B[9] + 2.1, 0.8), (B[10] + 0.3, 0.8), (B[10] + 1.2, 0.0)])
    hi[TAL] = trk(t, [(B[3] + 0.2, 0), (B[3] + 0.7, 1), (B[4] + 0.2, 1), (B[4] + 0.8, 0.0), (B[6] + 0.3, 0.0), (B[6] + 0.6, 1.0), (B[7] + 1.0, 1.0), (B[7] + 1.8, 0.5), (B[9] + 1.0, 0.5), (B[9] + 1.6, 0.0)])
    crack = trk(t, [(B[4] + 0.4 * DUR[4], 0.0), (B[4] + DUR[4], 0.35), (B[5] + 0.3, 0.35), (B[5] + 0.4, 1.0), (B[5] + 0.6, 1.0), (B[5] + 1.4, 0.4), (B[9] + 1.0, 0.4), (B[9] + 2.0, 0.0)])
    pose(s, evk, wince=1.0 if s > 0.7 and xr < 0.5 else 0.3)
    injury(brk, disl); xray(xr)
    for o in LIGHTS: o.data.energy = o['e0'] * (1.0 - 0.85 * xr)
    for i_, o in enumerate(FLASHES): o['fl'] = 1.0 if h1(f * 0.37 + i_ * 7.13) > 0.992 else 0.0      # phone flashes in the crowd
    for o in RIBBONS: o['scroll'] = -t * 1.2
    WBG.inputs['Strength'].default_value = 1.0 - 0.8 * xr
    for o, v in hi.items(): o['hi'] = v
    FIB['crack'] = crack
    BALL.location = ball_at(s); BALL.rotation_euler = (s * 9.0, s * 4.0, 0)
    BALL.hide_render = 2 <= nb <= 9                                      # the x-ray close-ups: keep the loose ball out of the background
    # ---- the one camera move
    wide = CAM_WIDE; sm_ = shin_mid(); ank = ankle_pt()
    if nb == 0:
        cp, ct, ln = wide; c = (cp + V3(0.25 * u, 0.15 * u, -0.1 * u), ct.lerp(Wd(0.2, 0.0, 0.7), smooth(0.6, 1.0, u)), lerp(ln, 24, u))
        c = (c[0] + shake(t, 0.03 * smooth(0.3, 0.45, u) * (1 - smooth(0.5, 0.7, u))), c[1], c[2])
    elif nb == 1:
        A = (wide[0] + V3(0.25, 0.15, -0.1), Wd(0.2, 0.0, 0.7), 24.0); Bc = cam_follow(sm_, V3(-0.85, -0.55, 0.45), 32.0)
        c = cam_blend(A, Bc, smooth(0.15, 1.0, u))
    elif nb in (2, 3):
        Bc0 = cam_follow(sm_, V3(-0.85, -0.55, 0.45), 32.0); Bc1 = cam_follow(sm_ + V3(0, 0, -0.05), V3(-0.9, -0.3, 0.12), 35.0)
        c = cam_blend(Bc0, Bc1, smooth(0.0, 1.8, lt)) if nb == 2 else Bc1
    elif nb in (4, 5, 6):
        Bc1 = cam_follow(sm_ + V3(0, 0, -0.05), V3(-0.9, -0.3, 0.12), 35.0); Bc2 = cam_follow(ank + V3(0, 0, 0.06), V3(-0.62, -0.26, 0.1), 40.0)
        c = cam_blend(Bc1, Bc2, smooth(0.0, 1.6, lt)) if nb == 4 else Bc2
        if nb == 5: c = (c[0] + shake(t, 0.012 * smooth(0.3, 0.35, lt) * (1 - smooth(0.4, 1.0, lt)), 3), c[1], c[2])
    elif nb in (7, 8, 9):
        Bc2 = cam_follow(ank + V3(0, 0, 0.06), V3(-0.62, -0.26, 0.1), 40.0); Bc3 = cam_follow(sm_ + V3(0, 0.08, 0), V3(-0.95, -0.05, 0.5), 30.0)
        c = cam_blend(Bc2, Bc3, smooth(0.0, 2.0, lt)) if nb == 7 else Bc3
    elif nb == 10:
        Bc3 = cam_follow(sm_ + V3(0, 0.08, 0), V3(-0.95, -0.05, 0.5), 30.0); A = (V3(-2.2, -0.2, 1.1), Wd(0.25, -0.1, 0.45), 24.0)
        c = cam_blend(Bc3, A, smooth(0.8, DUR[10], lt))
    else:
        A = (V3(-2.2, -0.2, 1.1), Wd(0.25, -0.1, 0.45), 24.0)
        c = cam_blend(A, (wide[0], wide[1], wide[2]), smooth(0.0, DUR[11] - 0.25, lt))
    look(c[0], c[1], c[2], 2.8 if c[2] < 28 else 3.5, focus=c[1])      # shallow focus: the arena melts behind him
# ================================================================ render
if __name__ == '__main__':
    if a.blend: bpy.ops.wm.save_as_mainfile(filepath=a.blend)
    os.makedirs(a.out, exist_ok=True)
    N_ = int(round(TOTAL * FPS))
    if a.only: todo = [int(x) for x in a.only.split(',')]; names = todo
    elif REDO:
        job = a.f0 // REDO['ch']; todo = REDO['frames'][job::REDO['jobs']]; names = [a.f0 + i for i in range(len(todo))]
    elif STRIDE:
        J = STRIDE['jobs']; job = a.f0 // STRIDE['ch']; todo = list(range(job, N_, J)); names = [a.f0 + i for i in range(len(todo))]
    else: todo = list(range(a.f0, min(a.f1, N_))); names = todo
    for f, nm in zip(todo, names):
        frame(f); S.render.filepath = os.path.join(a.out, f'f_{nm:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', f, '->', nm, flush=True)

