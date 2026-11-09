# Why your foot falls asleep, built and rendered in Blender (Cycles): a man on his couch with his legs crossed for an hour, the
# real anatomy of his leg (Z-Anatomy atlas, CC BY-SA 4.0, from BodyParts3D) fitted inside him: the common fibular nerve wrapping
# the fibula just under the skin, pinched by his other knee; its blood supply cut off; signals failing; foot drop when he stands;
# blood rushing back and the nerve misfiring (pins and needles).
#   python3 foot.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]      (stride.json / redo.json beside it: see ../ele/ele.py)
# Needs man.blend (man_build.py), anat.blend + anat_l.blend (anat_build.py + anat_fit.py) beside it or in /root/vt/n41/foot.
import sys, os, math, json, argparse
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n41/foot', n)) if os.path.exists(p_))
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

# ================================================================ THE ROOM (z up, metres; couch along x, he faces -y toward the TV)
WOOD = mat('floor', (0.33, 0.2, 0.11), 0.42, coat=0.25)
def floor_mat():
    m = WOOD; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 1.4; br.inputs['Row Height'].default_value = 0.16; br.offset = 0.37; br.squash_frequency = 1
    br.inputs['Color1'].default_value = (0.36, 0.22, 0.12, 1); br.inputs['Color2'].default_value = (0.27, 0.16, 0.085, 1); br.inputs['Mortar'].default_value = (0.08, 0.05, 0.03, 1)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 6.0; wv.inputs['Distortion'].default_value = 9.0; wv.inputs['Detail'].default_value = 4
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 12.0, 1.0); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.35
    nt.links.new(br.outputs['Color'], mx.inputs['A']); nt.links.new(wv.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    return m
floor_mat()
FLOOR = box('floor', (9, 9, 0.02), (0, 0, -0.01), WOOD)
RUG_M = noisy(mat('rug', (0.42, 0.36, 0.3), 0.95, sheen=0.6), 900.0, 0.25, 0.05)
def rug_mat():
    m = RUG_M; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    bx = math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', sx.outputs['X']), 1.0), math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', sx.outputs['Y']), 0.7))
    band = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', bx, 0.82), math_(nt, 'LESS_THAN', bx, 0.9))
    edge = math_(nt, 'GREATER_THAN', bx, 0.95)
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.16, 0.2, 0.26, 1); mx.inputs['B'].default_value = (0.62, 0.52, 0.38, 1)
    nt.links.new(math_(nt, 'MAXIMUM', band, edge), mx.inputs['Factor'])
    old = next(l for l in nt.links if l.to_socket == b.inputs['Base Color']); nz_mix = old.from_node
    nt.links.new(mx.outputs['Result'], nz_mix.inputs['A']); return m
rug_mat()
RUG = box('rug', (2.0, 1.4, 0.012), (0.1, -1.2, 0.006), RUG_M, bv=0.004)
WALL_M = noisy(mat('wall', (0.42, 0.40, 0.37), 0.9), 30.0, 0.04)
WALLB = box('wall_back', (9, 0.1, 3.0), (0, 0.98, 1.5), WALL_M)
WALLS = box('wall_side', (0.1, 9, 3.0), (-2.3, 0, 1.5), WALL_M)
TRIM_M = mat('trim', (0.82, 0.8, 0.76), 0.4)
BASEB = [box('base_back', (9, 0.02, 0.1), (0, 0.92, 0.05), TRIM_M), box('base_side', (0.02, 9, 0.1), (-2.24, 0, 0.05), TRIM_M)]
# window on the side wall: night outside, light curtains
WIN = box('window', (0.03, 1.1, 1.3), (-2.24, -1.2, 1.55), emis('night', (0.02, 0.05, 0.12), 1.0))
WINF = [box('winframe%d' % k, (0.05, 1.18 if k < 2 else 0.05, 0.05 if k < 2 else 1.38), (-2.23, -1.2 + (0 if k < 2 else (-0.57 if k == 2 else 0.57)), 1.55 + (0.67 if k == 0 else -0.67 if k == 1 else 0)), TRIM_M) for k in range(4)]
CURT_M = noisy(mat('curtain', (0.55, 0.5, 0.42), 0.9, sheen=0.5), 200.0, 0.1)
def curtain(name, y0):
    vs, fs = [], []; nx, nz = 24, 16
    for j in range(nz + 1):
        for i in range(nx + 1):
            yy = y0 + i / nx * 0.42; vs.append((-2.18 + 0.025 * math.sin(i / nx * math.pi * 7), yy, 0.35 + j / nz * 2.35))
    for j in range(nz):
        for i in range(nx): fs.append((j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i))
    return mesh(name, vs, fs, CURT_M)
CURTS = [curtain('curtL', -1.95), curtain('curtR', -0.87)]
# ---- the couch
COUCH_M = noisy(mat('couch', (0.12, 0.15, 0.2), 0.92, sheen=0.8), 700.0, 0.18, 0.05)
N(COUCH_M)['Principled BSDF'].inputs['Sheen Tint'].default_value = (0.5, 0.55, 0.7, 1)
LEG_M = mat('couch_leg', (0.08, 0.05, 0.03), 0.35)
CW, SEAT_Z = 2.2, 0.47                                   # couch width, top of the seat cushions
CY = 0.26                                                # couch centre (front of the seat at y ~ -0.04: his shins clear it)
COUCH = [box('couch_base', (CW, 0.84, 0.24), (0, CY + 0.08, 0.22), COUCH_M, bv=0.03),
         box('couch_back', (CW, 0.2, 0.55), (0, CY + 0.42, 0.62), COUCH_M, bv=0.06, ss=1),
         box('couch_armL', (0.2, 0.86, 0.36), (CW / 2 + 0.06, CY + 0.08, 0.42), COUCH_M, bv=0.06, ss=1),
         box('couch_armR', (0.2, 0.86, 0.36), (-CW / 2 - 0.06, CY + 0.08, 0.42), COUCH_M, bv=0.06, ss=1)]
for k in range(3):
    x0 = (k - 1) * 0.7
    sc = box('seat%d' % k, (0.69, 0.6, 0.14), (x0, CY - 0.0, SEAT_Z - 0.07), COUCH_M, bv=0.035, ss=2); COUCH.append(sc)
    if k == 1: SEAT_MID = sc
    c = box('backc%d' % k, (0.66, 0.24, 0.48), (x0, CY + 0.26, 0.75), COUCH_M, bv=0.08, ss=2); c.rotation_euler = (R(-12), 0, 0); COUCH.append(c)
for sx in (-1, 1):
    for sy in (-1, 1): COUCH.append(prim('cylinder', 'cleg', LEG_M, loc=(sx * (CW / 2 + 0.05), CY + 0.08 + sy * 0.36, 0.05), vertices=16, radius=0.025, depth=0.1))
# the middle cushion gives under him: a soft dent (shape key 'sit', 0 = empty, 1 = he's sitting)
_bm = bmesh.new(); _bm.from_mesh(SEAT_MID.data); bmesh.ops.subdivide_edges(_bm, edges=_bm.edges[:], cuts=14, use_grid_fill=True); _bm.to_mesh(SEAT_MID.data); _bm.free()
SEAT_MID.shape_key_add(name='basis'); SIT = SEAT_MID.shape_key_add(name='sit'); SIT.value = 0.0
for i, v in enumerate(SEAT_MID.data.vertices):
    if True:
        wx = math.exp(-(v.co.x / 0.27) ** 2 * 1.4)                                  # both thighs and his seat, front edge to the back
        wy = sm(clamp((v.co.y + 0.37) / 0.07, 0, 1)) * (1 - sm(clamp((v.co.y - 0.12) / 0.14, 0, 1)))
        SIT.data[i].co = v.co - V3(0, 0, 0.042 * wx * wy * clamp((v.co.z + 0.07) / 0.14, 0, 1))      # bottom stays, top sinks most
THROW = box('pillow', (0.42, 0.14, 0.4), (0.82, CY + 0.2, 0.7), noisy(mat('pillow', (0.55, 0.32, 0.18), 0.9, sheen=0.7), 600.0, 0.15), bv=0.08, ss=2); THROW.rotation_euler = (R(-15), R(8), R(-12))
# ---- TV and stand
STAND = box('tv_stand', (1.7, 0.42, 0.5), (0.0, -2.75, 0.25), noisy(mat('stand', (0.09, 0.07, 0.06), 0.45), 40.0, 0.2), bv=0.01)
TVB = box('tv', (1.3, 0.04, 0.75), (0.0, -2.78, 0.95), mat('tv_black', (0.01, 0.01, 0.012), 0.25), bv=0.008)
def tv_mat():
    """a made-up game on screen: sky, hills, a little runner; 'tv' (object property) = game time"""
    m = bpy.data.materials.new('tv_screen'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sx.inputs['Vector'])
    tt = objattr(nt, 'tv'); xs = math_(nt, 'ADD', sx.outputs['X'], math_(nt, 'MULTIPLY', tt, 0.15))
    hill = nt.nodes.new('ShaderNodeTexWave'); hill.wave_type = 'BANDS'; hill.inputs['Scale'].default_value = 3.0; hill.inputs['Distortion'].default_value = 2.0
    cmb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(xs, cmb.inputs['X']); nt.links.new(sx.outputs['Z'], cmb.inputs['Y']); nt.links.new(cmb.outputs['Vector'], hill.inputs['Vector'])
    sky = nt.nodes.new('ShaderNodeMix'); sky.data_type = 'RGBA'; sky.inputs['A'].default_value = (0.1, 0.45, 1.0, 1); sky.inputs['B'].default_value = (0.25, 0.85, 0.35, 1)
    hz = math_(nt, 'LESS_THAN', sx.outputs['Z'], math_(nt, 'ADD', math_(nt, 'MULTIPLY', hill.outputs['Fac'], 0.25), 0.25))
    nt.links.new(hz, sky.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(sky.outputs['Result'], em.inputs['Color']); em.inputs['Strength'].default_value = 2.2
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m
TVS = prim('plane', 'tv_screen', tv_mat(), loc=(0.0, -2.755, 0.95), rot=(R(90), 0, 0), size=1, scale=(1.24, 0.69, 1)); TVS['tv'] = 0.0
# ---- coffee table, can, bowl
TBL_M = noisy(mat('table', (0.25, 0.15, 0.08), 0.35, coat=0.3), 30.0, 0.15)
TABLE = [box('table_top', (1.1, 0.55, 0.04), (0.15, -1.2, 0.42), TBL_M, bv=0.008)] + \
        [box('tleg%d' % k, (0.04, 0.04, 0.4), (0.15 + sx * 0.5, -1.2 + sy * 0.23, 0.2), TBL_M) for k, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1)))]
CAN_M = mat('can', (0.55, 0.05, 0.04), 0.25, metal=0.8)
CAN = lathe('can', [(0.0, 0.0), (0.028, 0.0), (0.033, 0.012), (0.033, 0.105), (0.027, 0.122), (0.0, 0.122)], 32, CAN_M, loc=(0.45, -1.1, 0.44))
BOWL = lathe('bowl', [(0.0, 0.0), (0.05, 0.0), (0.09, 0.03), (0.11, 0.07), (0.105, 0.072), (0.085, 0.032), (0.0, 0.006)], 40, mat('bowl', (0.7, 0.68, 0.62), 0.3), loc=(-0.15, -1.25, 0.44))
# ---- lamp
LAMP_M = mat('lamp_metal', (0.05, 0.05, 0.05), 0.3, metal=0.8)
LAMP = [lathe('lamp_base', [(0.0, 0.0), (0.16, 0.0), (0.15, 0.02), (0.0, 0.03)], 32, LAMP_M, loc=(1.55, 0.55, 0.0)),
        prim('cylinder', 'lamp_pole', LAMP_M, loc=(1.55, 0.55, 0.8), vertices=12, radius=0.012, depth=1.6)]
SHADE_M = mat('shade', (0.9, 0.82, 0.65), 0.8, trans=0.3, emit=(1.0, 0.72, 0.42), estr=2.5)
LAMP.append(lathe('lamp_shade', [(0.2, 1.45), (0.14, 1.75)], 40, SHADE_M, loc=(1.55, 0.55, 0.0)))
def area(name, loc, rot, size, energy, col):
    lt = bpy.data.lights.new(name, 'AREA'); lt.size = size; lt.energy = energy; lt.color = col
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
LAMP_L = bpy.data.objects.new('lamp_light', bpy.data.lights.new('lamp_light', 'POINT')); S.collection.objects.link(LAMP_L)
LAMP_L.location = (1.55, 0.55, 1.55); LAMP_L.data.energy = 140; LAMP_L.data.color = (1.0, 0.72, 0.45); LAMP_L.data.shadow_soft_size = 0.15
TV_L = area('tv_light', (0.0, -2.6, 0.95), (R(-90), 0, 0), 1.2, 60, (0.55, 0.75, 1.0))
FILL = area('fill', (-1.2, -1.6, 2.2), (R(45), 0, R(-35)), 2.0, 70, (0.75, 0.82, 1.0))
ROOM = [FLOOR, RUG, WALLB, WALLS, WIN, STAND, TVB, TVS, CAN, BOWL, THROW] + BASEB + WINF + CURTS + COUCH + TABLE + LAMP
# world
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.012, 0.016, 0.03, 1); WBG.inputs['Strength'].default_value = 1.0
# x-ray room: dark blue gradient behind the leg, a soft key for the bones
XL = area('xray_key', (-0.6, -1.2, 1.4), (R(55), 0, R(-30)), 1.5, 35, (0.85, 0.9, 1.0)); XL.hide_render = True
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True

# ================================================================ THE MAN (MakeHuman, man_build.py): t-shirt, jean shorts, barefoot
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HAIR = bpy.data.objects['Human.short02']; HEADBITS = [o for o in bpy.data.objects if o.name.startswith('Human.') and o not in (BODY, SUIT, RIG)]
RB = RIG.data.bones; PB = RIG.pose.bones
KNEE_Z = RB['lowerleg01.R'].head_local.z
# jeans -> shorts: cut the legs a hand above the knee, keep his skin from there down
bm_ = bmesh.new(); bm_.from_mesh(SUIT.data)
kill = [f for f in bm_.faces if min(v.co.z for v in f.verts) < KNEE_Z + 0.075]          # a straight hem: anything reaching below goes
bmesh.ops.delete(bm_, geom=kill, context='FACES'); bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context='VERTS')
_seen = set()
for f0_ in list(bm_.faces):                                                                   # drop leftover scraps (small loose islands)
    if f0_ in _seen or not f0_.is_valid: continue
    isl, st_ = [], [f0_]; _seen.add(f0_)
    while st_:
        f_ = st_.pop(); isl.append(f_)
        for e_ in f_.edges:
            for g_ in e_.link_faces:
                if g_ not in _seen: _seen.add(g_); st_.append(g_)
    if len(isl) < 60: bmesh.ops.delete(bm_, geom=isl, context='FACES')
bm_.to_mesh(SUIT.data); bm_.free()
_dg = BODY.vertex_groups.get('Delete.male_casualsuit06')
if _dg: _dg.remove([v.index for v in BODY.data.vertices if v.co.z < KNEE_Z + 0.13])
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
    for p_ in o.data.polygons: p_.use_smooth = True
sol = SUIT.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0035; sol.offset = 1.0
subsurf(BODY, 1); subsurf(SUIT, 1)
BODY.add_rest_position_attribute = True
def retint(m, col, keep=0.55, rough=0.85, sheen=0.35):
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    src = lk.from_socket if lk else None
    bw = nt.nodes.new('ShaderNodeRGBToBW'); mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - keep; mr.inputs['To Max'].default_value = 1.0 + keep * 0.3
    if src: nt.links.new(src, bw.inputs['Color']); nt.links.new(bw.outputs['Val'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mul.inputs['A'])
    mul.inputs['B'].default_value = (*col, 1); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Tint'].default_value = (*col, 1)
    return m
SHORTS_M = SUIT.data.materials[0]; SHIRT_M = SHORTS_M.copy(); SHIRT_M.name = 'shirt'; SUIT.data.materials.append(SHIRT_M)
for p_ in SUIT.data.polygons:
    if sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) > 0.93: p_.material_index = 1
retint(SHORTS_M, (0.42, 0.5, 0.62), 0.6)                            # faded denim shorts (the asset's own folds and seams)
retint(SHIRT_M, (0.62, 0.2, 0.16), 0.35, 0.9, 0.5)                   # a worn brick-red tee
# x-ray look for his whole body: glass skin, see-through; 'pins' sparkles on the top of his right foot; 'dead' greys the foot
def xray_skin_mat():
    m = bpy.data.materials.new('xskin'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    # top of the right foot (rest space): x < -0.13, y < 0.0, 0.02 < z < 0.11
    foot = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', sx.outputs['X'], -0.125), math_(nt, 'LESS_THAN', sx.outputs['Z'], 0.12))
    foot = math_(nt, 'MULTIPLY', foot, math_(nt, 'LESS_THAN', sx.outputs['Y'], 0.01))
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.feature = 'F1'; vor.inputs['Scale'].default_value = 260.0; vor.voronoi_dimensions = '4D'
    nt.links.new(rp.outputs['Vector'], vor.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 9.0), vor.inputs['W'])
    spark = math_(nt, 'LESS_THAN', vor.outputs['Distance'], 0.12)
    rnd = math_(nt, 'GREATER_THAN', vor.outputs['Color'] if False else vor.outputs['Distance'], -1.0)
    pins = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', spark, foot), objattr(nt, 'pins'))
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.0)
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.inputs['A'].default_value = (0.35, 0.62, 1.0, 1); base.inputs['B'].default_value = (0.42, 0.45, 0.5, 1)
    nt.links.new(math_(nt, 'MULTIPLY', foot, objattr(nt, 'dead')), base.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(base.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'MULTIPLY_ADD', fz, 1.1, 0.03), em.inputs['Strength'])
    em2 = nt.nodes.new('ShaderNodeEmission'); em2.inputs['Color'].default_value = (1.0, 0.92, 0.55, 1); em2.inputs['Strength'].default_value = 14.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MULTIPLY_ADD', fz, 0.55, 0.05), mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
    mx2 = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(pins, mx2.inputs['Fac']); nt.links.new(mx.outputs['Shader'], mx2.inputs[1]); nt.links.new(em2.outputs['Emission'], mx2.inputs[2])
    nt.links.new(mx2.outputs['Shader'], out.inputs['Surface']); return m
XSKIN = xray_skin_mat()
BODY['pins'] = 0.0; BODY['tt'] = 0.0; BODY['dead'] = 0.0
BODY_MATS = [sl.material for sl in BODY.material_slots]
PUFF = BODY.modifiers.new('xray_puff', 'DISPLACE'); PUFF.strength = 0.0; PUFF.mid_level = 0.0      # skin 4 mm fuller in x-ray (anatomy stays inside)
bpy.context.view_layer.objects.active = BODY
while BODY.modifiers.find('xray_puff') > BODY.modifiers.find('Armature') + 1: bpy.ops.object.modifier_move_up(modifier='xray_puff')
_pg_ = BODY.vertex_groups.new(name='puff')                       # not under the soles: the fuller x-ray skin must not sink into the floor
for v in BODY.data.vertices: _pg_.add([v.index], min(1.0, max(0.0, (v.co.z - 0.004) / 0.03)), 'REPLACE')
PUFF.vertex_group = 'puff'

# ================================================================ HIS ANATOMY (anat.blend / anat_l.blend: fitted in his rest space, weighted to his rig)
ANAT = []
for f_ in ('anat.blend', 'anat_l.blend'):
    with bpy.data.libraries.load(asset(f_), link=False) as (_s, _d): _d.objects = list(_s.objects)
    for o in _d.objects:
        S.collection.objects.link(o); o.parent = RIG; o.matrix_world = Matrix.Identity(4)
        md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG; md.use_deform_preserve_volume = (o['kind'] != 'bone')
        for p_ in o.data.polygons: p_.use_smooth = True
        o.visible_shadow = False; ANAT.append(o)
AN = {o.name: o for o in ANAT}
def kind(k, side='R'): return [o for o in ANAT if o['kind'] == k and (o.name.endswith('.L') == (side == 'L'))]
# ---- x-ray materials
def bone_mat():
    m = mat('bone', (0.86, 0.82, 0.72), 0.55, sheen=0.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (0.75, 0.85, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY', lw.outputs['Facing'], 1.2), b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
BONE_M = bone_mat()
def muscle_mat(name, col):
    """red muscle with fibres; 'act' = lit up (working), 'dim' = how much it's faded back"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.45; b.inputs['Coat Weight'].default_value = 0.3
    rp = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 140.0; wv.inputs['Distortion'].default_value = 3.0; nt.links.new(rp.outputs['Object'], wv.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*col, 1); mx.inputs['B'].default_value = tuple(c * 0.6 for c in col) + (1,)
    nt.links.new(math_(nt, 'MULTIPLY', wv.outputs['Fac'], 0.6), mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value = (1.0, 0.25, 0.18, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'act'), 3.0), b.inputs['Emission Strength'])
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', objattr(nt, 'dim'), 0.85)), b.inputs['Alpha'])
    return m
MUS_M = muscle_mat('muscle', (0.42, 0.12, 0.11)); MUS_KEY = muscle_mat('muscle_key', (0.7, 0.1, 0.08))
TEND_M = mat('tendon', (0.85, 0.82, 0.75), 0.3, coat=0.5)
def tree_mat(name, col, kind_):
    """nerve or artery: glows; pulses run down 'arc' (m from the hip). Object props: ph (pulse travel, m), glow, pulse (0..1),
    block (arc where it's pinched; past it the glow drops by 'dead'), spark (misfiring flicker), tt (time)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'; arc = arc.outputs['Fac']
    rel = math_(nt, 'SUBTRACT', objattr(nt, 'ph'), arc)                     # distance behind the pulse front
    saw = math_(nt, 'FRACT', math_(nt, 'DIVIDE', rel, 0.16))                 # pulses every 16 cm
    comet = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, saw), 10.0)        # bright head, fading tail
    front = math_(nt, 'GREATER_THAN', rel, 0.0)
    pul = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', comet, front), math_(nt, 'MULTIPLY', objattr(nt, 'pulse'), 9.0))
    past = math_(nt, 'GREATER_THAN', arc, objattr(nt, 'block'))
    kill = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', past, objattr(nt, 'dead')))
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '2D'; nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 2
    cmb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', arc, 60.0), cmb.inputs['X']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 14.0), cmb.inputs['Y'])
    nt.links.new(cmb.outputs['Vector'], nz.inputs['Vector'])
    spk = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.55), 0.0), 1.5), math_(nt, 'MULTIPLY', objattr(nt, 'spark'), 120.0))
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.4
    rim = math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.8, 0.6)
    strength = math_(nt, 'MULTIPLY', math_(nt, 'ADD', math_(nt, 'ADD', math_(nt, 'MULTIPLY', rim, objattr(nt, 'glow')), pul), spk), kill)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(strength, em.inputs['Strength'])
    dk = nt.nodes.new('ShaderNodeBsdfDiffuse'); dk.inputs['Color'].default_value = (0.25, 0.24, 0.22, 1) if kind_ == 'nerve' else (0.2, 0.03, 0.03, 1)
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(em.outputs['Emission'], ad.inputs[0]); nt.links.new(dk.outputs['BSDF'], ad.inputs[1])
    nt.links.new(ad.outputs['Shader'], out.inputs['Surface']); return m
NERVE_M = tree_mat('nerve', (1.0, 0.82, 0.25), 'nerve'); NERVE_HERO = tree_mat('nerve_hero', (1.0, 0.62, 0.08), 'nerve'); ART_M = tree_mat('artery', (1.0, 0.1, 0.06), 'artery')
for o in ANAT:
    k = o['kind']; o.data.materials.clear()
    o.data.materials.append({'bone': BONE_M, 'muscle': MUS_M, 'tendon': TEND_M, 'nerve': NERVE_M, 'artery': ART_M}[k])
    for p_, v in (('act', 0.0), ('dim', 0.0), ('ph', 0.0), ('glow', 1.0), ('pulse', 0.0), ('block', 9.0), ('dead', 0.0), ('spark', 0.0), ('tt', 0.0)): o[p_] = v
KEY_MUS = [AN[n] for n in ('Tibialis anterior muscle', 'Extensor digitorum longus', 'Extensor hallucis longus') if n in AN]
for o in KEY_MUS: o.data.materials[0] = MUS_KEY
NERVES = kind('nerve'); ARTS = kind('artery'); BONES_R = kind('bone'); BONES_L = kind('bone', 'L'); MUS_R = kind('muscle') + kind('tendon'); MUS_L = kind('muscle', 'L') + kind('tendon', 'L')
CFN = AN['Common fibular nerve']
# compositor: a soft glow around bright things (nerve signals, sparks)
S.use_nodes = True if hasattr(S, 'use_nodes') else None
try:
    ct_ = S.compositing_node_group if hasattr(S, 'compositing_node_group') else None
    if ct_ is None and hasattr(bpy.data, 'node_groups') and hasattr(S, 'compositing_node_group'):
        ct_ = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); S.compositing_node_group = ct_
    if ct_ is None: ct_ = S.node_tree
    rl_ = ct_.nodes.get('Render Layers') or ct_.nodes.new('CompositorNodeRLayers')
    gl_ = ct_.nodes.new('CompositorNodeGlare')
    for ty_ in ('Bloom', 'Fog Glow'):
        try: gl_.inputs['Type'].default_value = ty_; break
        except Exception: pass
    for k_, v_ in (('Threshold', 1.5), ('Strength', 0.35), ('Size', 0.55), ('Quality', 'High')):
        try: gl_.inputs[k_].default_value = v_
        except Exception: pass
    print('glare type', gl_.inputs['Type'].default_value)
    out_ = next((n for n in ct_.nodes if n.bl_idname in ('CompositorNodeComposite', 'NodeGroupOutput')), None)
    if out_ is None:
        out_ = ct_.nodes.new('NodeGroupOutput'); ct_.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ct_.links.new(rl_.outputs['Image'], gl_.inputs['Image']); ct_.links.new(gl_.outputs['Image'], out_.inputs[0])
    print('compositor glow on')
except Exception as e_: print('compositor glow skipped', e_)
# the pinch point: where the common fibular nerve wraps the fibular neck (rest space): lowest-lateral bend of the nerve
_cv = [v.co for v in CFN.data.vertices]
_fib = AN['Fibula']; _ftop = max(v.co.z for v in _fib.data.vertices)
_neck_i = [v.index for v in _fib.data.vertices if _ftop - 0.06 < v.co.z < _ftop - 0.035]; _neck = [_fib.data.vertices[i].co for i in _neck_i]
FIB_NECK = sum(_neck, Vector()) / len(_neck)
_arc = CFN.data.attributes['arc'].data
_near = min(range(len(_cv)), key=lambda i: (_cv[i] - FIB_NECK).length)
PINCH_ARC = _arc[_near].value; PINCH_P = _cv[_near].copy()
print('pinch arc %.3f at' % PINCH_ARC, tuple(round(x, 3) for x in PINCH_P))
# the nerve flattens under the other knee: shape key squashing it toward the fibula over +-2 cm of its length
CFN.shape_key_add(name='basis'); SQ = CFN.shape_key_add(name='squash'); SQ.value = 0.0
_ctr = {}
for i, v in enumerate(CFN.data.vertices):
    s_ = round(_arc[i].value * 250); _ctr.setdefault(s_, []).append(v.co)
_ctr = {k: sum(vs, Vector()) / len(vs) for k, vs in _ctr.items()}
_ndir = (PINCH_P - FIB_NECK).normalized()
for i, v in enumerate(CFN.data.vertices):
    w = math.exp(-((_arc[i].value - PINCH_ARC) / 0.012) ** 2)
    c = _ctr[round(_arc[i].value * 250)]; d = v.co - c; along = d.dot(_ndir)
    SQ.data[i].co = v.co - _ndir * along * 0.55 * w + (d - _ndir * along) * 0.25 * w
# ---- the nerve's own tiny blood vessels (vasa nervorum): fine vessels winding along the common fibular nerve
VASA_M = tree_mat('vasa', (1.0, 0.12, 0.08), 'artery')
VASA = []
_keys = sorted(_ctr)
def ctr_at(s_):
    k = min(_keys, key=lambda k_: abs(k_ / 250 - s_)); return _ctr[k]
for j in range(5):
    pts = []; a0 = PINCH_ARC - 0.07 + 0.01 * j; a1 = PINCH_ARC + 0.08 - 0.008 * j
    for i in range(60):
        s_ = lerp(a0, a1, i / 59); c = ctr_at(s_); c2 = ctr_at(s_ + 0.004); tng = (c2 - c).normalized()
        side = tng.cross(Vector((0, 0, 1))).normalized(); up_ = tng.cross(side)
        ang = j * 1.3 + i / 59 * 7.0 + 0.6 * math.sin(i * 0.4 + j)
        pts.append(c + (side * math.cos(ang) + up_ * math.sin(ang)) * 0.003)
    o = tube('vasa%d' % j, pts, 0.0006, VASA_M, seg=6); o.parent = RIG
    for p_, v in (('ph', 0.0), ('glow', 1.0), ('pulse', 0.0), ('block', 9.0), ('dead', 0.0), ('spark', 0.0), ('tt', 0.0)): o[p_] = v
    at = o.data.attributes.new('arc', 'FLOAT', 'POINT')
    for i_, v in enumerate(o.data.vertices): at.data[i_].value = lerp(a0, a1, (i_ // 6) / 59)
    # ride the nerve: copy the nerve's bone weights from its nearest vertex
    for g in CFN.vertex_groups: o.vertex_groups.new(name=g.name)
    for v in o.data.vertices:
        nv = min(range(0, len(_cv), 3), key=lambda i: (_cv[i] - v.co).length)
        for g in CFN.data.vertices[nv].groups: o.vertex_groups[CFN.vertex_groups[g.group].name].add([v.index], g.weight, 'REPLACE')
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG; o.visible_shadow = False; VASA.append(o)
TREE = NERVES + ARTS + VASA
for o in ANAT + VASA: o.hide_render = True

# ================================================================ POSING: legs by IK to the ankles (knee and hip hinge), feet and toes by hand
def ik(bone, target, pole, chain, pole_angle=R(-90)):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TGT = {k: empty('tgt_' + k) for k in ('ankR', 'ankL', 'poleR', 'poleL', 'handR', 'handL', 'poleArmR', 'poleArmL')}
for s_ in ('R', 'L'):
    ik('lowerleg02.' + s_, TGT['ank' + s_], TGT['pole' + s_], 4)
    for bn in ('lowerleg02.', 'upperleg02.'):
        pb = PB[bn + s_]; pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = True
    ik('wrist.' + s_, TGT['hand' + s_], TGT['poleArm' + s_], 5)
RIG.rotation_mode = 'XYZ'
# hands flat on a surface: turn the wrist (Copy Rotation after the IK) so the palm faces down, fingers forward (from g9's hold())
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
def flat_hands(w, fwd=Vector((0.0, -1.0, -0.08))):
    """palms down on a surface (w = 0..1)"""
    for s_, sg in (('R', -1), ('L', 1)):
        O, e_, c_ = HAND[s_]; c_.influence = w
        d = (Vector(fwd) + Vector((0.25 * sg, 0, 0))).normalized(); n = Vector((0, 0, -1.0)); n = (n - d * n.dot(d)).normalized(); a_ = d.cross(n)
        e_.rotation_quaternion = (Matrix((a_, d, n)).transposed() @ O).to_quaternion()
def rot(bn, x=0.0, y=0.0, z=0.0):
    pb = PB[bn]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(x), R(y), R(z))
# ---- a game controller (generic, no marks)
PAD_M = noisy(mat('pad', (0.04, 0.04, 0.045), 0.42), 300.0, 0.1, 0.08)
PAD = empty('pad')
_pb = box('pad_body', (0.15, 0.06, 0.03), (0, 0, 0), PAD_M, bv=0.012, parent=PAD, ss=1)
_pg = [box('pad_grip%d' % k, (0.045, 0.07, 0.035), (sx * 0.055, 0.035, -0.006), PAD_M, bv=0.016, parent=PAD, ss=1) for k, sx in enumerate((-1, 1))]
for g_ in _pg: g_.rotation_euler = (R(10), 0, R(-14 * (1 if g_.location.x < 0 else -1)))
_sticks = [prim('cylinder', 'pad_stick%d' % k, mat('stick', (0.02, 0.02, 0.02), 0.6), PAD, loc=(sx * 0.035, 0.012, 0.022), vertices=16, radius=0.009, depth=0.012) for k, sx in enumerate((-1, 1))]
_btn = [prim('cylinder', 'pad_btn%d' % k, mat('btn%d' % k, c_, 0.3), PAD, loc=(0.045 + dx, -0.012 + dy, 0.017), vertices=12, radius=0.004, depth=0.006)
        for k, (dx, dy, c_) in enumerate(((0.0, 0.008, (0.1, 0.5, 0.15)), (0.009, 0.0, (0.6, 0.08, 0.06)), (-0.009, 0.0, (0.1, 0.2, 0.6)), (0.0, -0.008, (0.6, 0.5, 0.05))))]
PADS = [_pb] + _pg + _sticks + _btn
def fingers(s_, curl):
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            nm = f'finger{f_}-{seg}.{s_}'
            if nm in PB: ang = (10, 15, 8)[seg - 1] if f_ == 1 else (40, 55, 30)[seg - 1]; rot(nm, ang * curl)
def wpos(bn, tail=False):
    pb = PB[bn]; return RIG.matrix_world @ (pb.tail if tail else pb.head)
HIP0 = (RB['upperleg01.R'].head_local + RB['upperleg01.L'].head_local) * 0.5
SEATED = dict(rig=V3(0.0, 0.24, -0.29), back=-13.0, lean=-2.0)
DY = SEATED['rig'].y - 0.17                               # the crossed pose was solved with him 7 cm further forward
def set_pose(rig_loc, rig_rot=(0, 0, 0), spine=0.0, neck=0.0, head=0.0, head_yaw=0.0, side_lean=0.0,
             ankR=None, poleR=None, footR=(0, 0, 0), toesR=0.0, ankL=None, poleL=None, footL=(0, 0, 0), toesL=0.0,
             handR=None, handL=None, pad=1.0, curl=0.8, armR_out=0.0):
    RIG.rotation_euler = tuple(R(x) for x in rig_rot)
    RIG.location = Vector(rig_loc) + HIP0 - RIG.rotation_euler.to_matrix() @ HIP0          # rotate about his hips, not his feet
    for n, k in (('spine03', 0.3), ('spine02', 0.35), ('spine01', 0.35)): rot(n, spine * k, 0, side_lean * k)
    for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)): rot(n, neck * k, head_yaw * k * 0.5)
    rot('head', head, head_yaw * 0.5)
    TGT['ankR'].location = ankR; TGT['ankL'].location = ankL; TGT['poleR'].location = poleR; TGT['poleL'].location = poleL
    rot('foot.R', *footR); rot('foot.L', *footL)
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            for s_, tc in (('R', toesR), ('L', toesL)):
                nm = f'toe{f_}-{seg}.{s_}'
                if nm in PB: rot(nm, tc * (25 if seg == 1 else 18))
    TGT['handR'].location = handR; TGT['handL'].location = handL
    TGT['poleArmR'].location = RIG.matrix_world @ V3(-0.6, 0.35, 1.0); TGT['poleArmL'].location = RIG.matrix_world @ V3(0.6, 0.35, 1.0)
    fingers('R', curl); fingers('L', curl)
    bpy.context.view_layer.update()
    if pad < 0.5: PAD.matrix_world = PAD_REST
    else:
        hr, hl = wpos('wrist.R', True), wpos('wrist.L', True); mid = (hr + hl) * 0.5
        xa = (hl - hr).normalized(); ya = xa.cross(Vector((0, 0, 1))).normalized() * -1; za = xa.cross(ya)
        PAD.matrix_world = Matrix.Translation(mid + za * 0.02 + ya * -0.025) @ Matrix((xa, ya, za)).transposed().to_4x4() @ Matrix.Rotation(R(-35), 4, 'X')
    bpy.context.view_layer.update()

# ---- feet never go through the floor (owner, Nov 9: "his foot through the floor multiple times"). After a pose is set, find the
# lowest skin point of each foot (rest_position picks the foot, whatever the Mask/subsurf did to the vertex order) and lift that
# leg's ankle target until the foot rests on the floor or the rug. Toes curled or pointed down then lift the heel, like a real foot.
import numpy as np
FLOOR_LOG = {}                                                   # how far each foot was lifted this frame (m), for the re-render list
PLANT = {}                                                       # feet set flat on the floor this frame: side -> (weight, pitch, roll, own local rotation)
def floor_top(x, y): return np.where((x > -0.9) & (x < 1.1) & (y > -1.9) & (y < -0.5), 0.012, 0.0)    # rug (box 'rug') else wood
DORSI_MAX = 25.0                                                 # how far an ankle bends up (deg); past it the heel comes up off the floor
def plant(s_, w, pitch=0.0, roll=0.0, own=None):
    """turn the foot so it lies flat on the floor (in the world, not relative to the shin), w = 0..1 blend from its own pose.
    pitch + = toes down, roll = about the foot's long axis. The ankle never bends up past DORSI_MAX: the heel lifts instead
    (floor_fix then raises the ankle so the ball of the foot rests on the floor) and the toes bend up to stay flat."""
    pb = PB['foot.' + s_]; pb.rotation_mode = 'XYZ'
    if own is None: own = pb.rotation_euler.copy()
    PLANT[s_] = (w, pitch, roll, own)
    if w <= 0.0: pb.rotation_euler = own; return
    bpy.context.view_layer.update()
    MW = RIG.matrix_world.to_3x3(); R0 = RB['foot.' + s_].matrix_local.to_3x3()
    yc = MW @ pb.matrix.to_3x3().col[1]; y0 = R0.col[1]
    yaw = math.atan2(yc.y, yc.x) - math.atan2(y0.y, y0.x)
    Wd = Matrix.Rotation(yaw, 3, 'Z') @ R0 @ Matrix.Rotation(R(pitch), 3, 'X') @ Matrix.Rotation(R(roll), 3, 'Y')
    A = (MW.inverted() @ Wd).to_4x4(); A.translation = pb.matrix.translation
    pb.matrix = A; bpy.context.view_layer.update()
    e = pb.rotation_euler.copy(); over = max(0.0, R(-DORSI_MAX) - e.x); e.x += over
    pb.rotation_euler = own.to_quaternion().slerp(e.to_quaternion(), w).to_euler('XYZ')
    for f_ in range(1, 6):
        nm = f'toe{f_}-1.{s_}'
        if nm in PB and over > 0: PB[nm].rotation_euler.x = -over * w
    bpy.context.view_layer.update()
def floor_fix(margin=0.0, passes=5):
    for _ in range(passes):
        dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
        co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co)
        rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); oe.to_mesh_clear()
        co = co.reshape(-1, 3); rp = rp.reshape(-1, 3); M_ = np.array(BODY.matrix_world)
        w = co @ M_[:3, :3].T + M_[:3, 3]; pen = floor_top(w[:, 0], w[:, 1]) + margin - w[:, 2]
        moved = False
        for s_, side in (('R', rp[:, 0] < 0), ('L', rp[:, 0] > 0)):
            p_ = float(pen[side & (rp[:, 2] < 0.16)].max())
            down = PLANT.get(s_, (0,))[0] >= 0.99                       # a planted foot also comes DOWN onto the floor (no floating)
            if p_ > 0.001 or (down and p_ < -0.001):
                TGT['ank' + s_].location.z += p_; FLOOR_LOG[s_] = FLOOR_LOG.get(s_, 0.0) + p_; moved = True
        if not moved: return
        bpy.context.view_layer.update()
        for s_, (w, pitch, roll, own) in list(PLANT.items()):           # the shin moved: lay the planted feet flat again
            if w > 0: plant(s_, w, pitch, roll, own)

# ---- the poses of the story (world space). He sits on the middle cushion; right leg crossed over the left knee.
CROSS = dict(ank=V3(0.292, -0.336, 0.272), pole=V3(1.043, -1.3, 1.069))          # right ankle / knee pole with the right knee over the left
def seated(cross=1.0, look_down=0.0, pad=1.0, t=0.0):
    SIT.value = 1.0; flat_hands(0.0)
    rl = SEATED['rig']
    ankL = V3(0.16, -0.29, 0.075); poleL = V3(0.2, -1.5, 0.6)
    flat_R = V3(-0.16, -0.30, 0.075); pole_flat = V3(-0.2, -1.5, 0.6)
    ankR = flat_R.lerp(CROSS['ank'], cross) + V3(0, -0.05, 0.12) * math.sin(math.pi * cross); poleR = pole_flat.lerp(CROSS['pole'], cross)
    hands_y = 0.01; hz = 0.66 + 0.03 * cross
    sway = 0.004 * math.sin(t * 2.1)
    set_pose(rl, (SEATED['back'], 0, 0), spine=SEATED['lean'] + 6 * look_down, neck=6 + 10 * look_down, head=8 + 12 * look_down, side_lean=-2 * cross,
             ankR=ankR, poleR=poleR, footR=(22 * cross, 0, 0), toesR=0.1, ankL=ankL, poleL=poleL, footL=(-2, 0, 0),
             handR=V3(-0.09 + sway, hands_y, hz), handL=V3(0.11 + sway, hands_y, hz), pad=pad)
    floor_fix()

def standing(s, t=0.0):
    """getting up off the couch (s 0..1): lean, rise, step with the dead right foot, it folds, he lurches onto the coffee table.
    roll = how far the ankle rolls over (degrees, + = sole turns in)"""
    k_lean = smooth(0.0, 0.22, s) - smooth(0.32, 0.55, s) * 0.85        # lean forward to get up, then straighten
    k_up = smooth(0.12, 0.5, s)                                        # hips up off the cushion
    SIT.value = 1.0 - smooth(0.1, 0.32, s)
    k_step = smooth(0.55, 0.78, s)                                     # right foot swings forward
    k_land = smooth(0.74, 0.86, s); k_roll = smooth(0.8, 0.94, s); k_fall = smooth(0.84, 1.0, s)
    hip = (HIP0 + SEATED['rig']).lerp(V3(0.0, -0.22, 0.86), k_up) + V3(0.03, -0.1, 0.0) * k_step + V3(-0.06, -0.3, -0.2) * k_fall
    back = lerp(SEATED['back'], 0.0, smooth(0.0, 0.3, s)) + 32 * k_lean + 38 * k_fall
    ankL = V3(0.15, -0.26, 0.075) + V3(0.0, -0.05, 0.0) * k_fall
    lift = 0.13 * math.sin(math.pi * k_step) * (1 - k_land)
    ankR = V3(-0.15, -0.27, 0.075).lerp(V3(-0.12, -0.58, 0.095), k_step) + V3(0, 0, lift) + V3(0.02, 0.03, -0.035) * k_roll
    drop = 38 * k_step - 10 * k_land                                   # foot drop: the toes hang (no muscle lifting them)
    footR = (drop, 0.0, 0.0)
    rollR = 34 * k_roll
    hands_push = V3(0.0, 0.05, 0.5)
    hR = V3(-0.3, 0.02, 0.6).lerp(V3(-0.32, -0.2, 0.95), smooth(0.4, 0.7, s)).lerp(V3(-0.26, -0.96, 0.545), k_fall)
    hL = V3(0.3, 0.02, 0.6).lerp(V3(0.3, -0.2, 0.95), smooth(0.4, 0.7, s)).lerp(V3(0.24, -0.98, 0.545), k_fall)
    set_pose(hip - HIP0, (back, 0, -6 * k_fall), spine=-8 * k_lean + 10 * k_fall, neck=10 * k_fall, head=12 * k_fall + 6, side_lean=-8 * k_roll,
             ankR=ankR, poleR=V3(-0.25, -1.6, 0.9), footR=footR, toesR=0.9 * k_step, ankL=ankL, poleL=V3(0.25, -1.6, 0.9), footL=(-4 - 20 * k_fall, 0, 0),
             handR=hR, handL=hL, pad=0.0, curl=0.25 * (1 - k_fall))
    flat_hands(k_fall); bpy.context.view_layer.update()
    plant('L', 1.0)                                                    # the good foot stays flat on the floor (heel lifts as he lurches)
    wR = clamp(1.0 - smooth(0.55, 0.62, s) + k_land, 0.0, 1.0)         # dead foot: on the floor, swings up (toes hanging), slaps down
    plant('R', wR, 0.0, ROLL_SIGN * rollR)                             # ... and rolls over onto its outside edge
    floor_fix()
ROLL_SIGN = 1.0
PAD_REST = Matrix.Translation(V3(0.42, 0.05, SEAT_Z + 0.025)) @ Matrix.Rotation(R(20), 4, 'Z')

# ================================================================ X-RAY MODE and the story's controls
XFLOOR_M = mat('xfloor', (0.01, 0.015, 0.03), 0.6)
def xray_mode(on, left_bones=True, muscles=0.55):
    for o in ROOM: o.hide_render = on
    FLOOR.hide_render = False; FLOOR.material_slots[0].material = XFLOOR_M if on else WOOD
    for o in (SUIT, HAIR) + tuple(HEADBITS): o.hide_render = on
    for o in [PAD] + PADS: o.hide_render = on
    for i, sl in enumerate(BODY.material_slots): sl.material = XSKIN if on else BODY_MATS[i]
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = not on
    PUFF.strength = 0.004 if on else 0.0
    for o in ANAT + VASA: o.hide_render = not on
    for o in BONES_L: o.hide_render = not (on and left_bones)
    for o in MUS_L: o.hide_render = True
    for o in MUS_R: o['dim'] = muscles
    WBG.inputs['Color'].default_value = (0.004, 0.012, 0.035, 1) if on else (0.012, 0.016, 0.03, 1)
    XL.hide_render = not on
    for lt in (LAMP_L, TV_L, FILL): lt.hide_render = on
FIB_TREE = [AN[n] for n in ('Common fibular nerve', 'Deep fibular nerve', 'Superficial fibular nerve', 'Muscular branches of deep fibular nerve',
            'Dorsal digital branches of deep fibular nerve', 'Dorsal digital branches of superficial fibular nerve', 'Medial dorsal cutaneous nerve of foot',
            'Intermediate dorsal cutaneous nerve of foot', 'Sural communicating branch of common fibular nerve') if n in AN]
UP_N = [AN['Sciatic nerve']]
for o in FIB_TREE + UP_N: o.data.materials[0] = NERVE_HERO
OTHER_N = [o for o in NERVES if o not in FIB_TREE and o not in UP_N]
PINCH = PINCH_ARC - 0.01
def nerves(t, glow=1.0, other=0.35, pulse=0.0, speed=1.6, dead=0.0, spark=0.0, block=9.0):
    for o in NERVES:
        main = o in FIB_TREE or o in UP_N
        o['glow'] = (glow * 1.25 if o in FIB_TREE else glow * 0.9) if main else other; o['pulse'] = pulse if main else pulse * 0.25; o['ph'] = t * speed
        o['dead'] = dead if o in FIB_TREE else 0.0; o['block'] = block; o['spark'] = spark if o in FIB_TREE else spark * 0.2; o['tt'] = t
def arteries(t, glow=0.5, pulse=0.3, speed=0.9, front=9.0, dead=0.0):
    for o in ARTS: o['glow'] = glow; o['pulse'] = pulse; o['ph'] = min(t * speed, front) if front < 9 else t * speed; o['dead'] = dead; o['block'] = front; o['tt'] = t
def vasa(t, flow=1.0, glow=1.0):
    for o in VASA: o['glow'] = 0.1 + (glow * 2.0 - 0.1) * flow; o['pulse'] = 2.0 * flow; o['ph'] = t * 0.12; o['tt'] = t
def look(cp, ct, lens=35, fstop=8.0, focus=None, roll=0.0, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    q = d.to_track_quat('-Z', 'Y')
    if up is not None:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0): return Vector((wob(t, 7.0, seed), wob(t, 7.0, seed + 3.3), wob(t, 7.0, seed + 6.1))) * amt
def pinch_world():
    dg = bpy.context.evaluated_depsgraph_get(); oe = CFN.evaluated_get(dg); me = oe.to_mesh(); arc = me.attributes['arc'].data
    ps = [oe.matrix_world @ v.co for v in me.vertices if abs(arc[v.index].value - PINCH) < 0.006]; oe.to_mesh_clear()
    return sum(ps, Vector()) / len(ps)
def bone_world(bn, tail=False): return wpos(bn, tail)
def eval_centroid(o, idx=None):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    vs = me.vertices if idx is None else [me.vertices[i] for i in idx]; c = sum((oe.matrix_world @ v.co for v in vs), Vector()) / len(vs); oe.to_mesh_clear(); return c
def pinch_view():
    """(pinch point, a camera direction that sees the nerve on the fibula and the other knee pressing on it)"""
    pw = pinch_world(); neck = eval_centroid(_fib, _neck_i); pat = eval_centroid(AN['Patella.L'])
    out_ = (pw - neck).normalized(); kd = (pat - pw).normalized()
    side = out_.cross(kd).normalized()
    if side.dot(CAM_HINT) < 0: side = -side
    d = (side * 0.8 + out_ * 0.35 - kd * 0.25).normalized(); return pw, d, pat
CAM_HINT = V3(0.4, -1.0, 0.3)
_tib = AN['Tibia']
def leg_frame():
    """right shin frame in the world: K knee, A ankle, sd down the shin, lat toward his fibula (outside), fr toward his shin's front"""
    K = bone_world('lowerleg01.R'); A = bone_world('foot.R'); sd = (A - K).normalized()
    lat = eval_centroid(_fib) - eval_centroid(_tib); lat = (lat - sd * lat.dot(sd)).normalized(); fr = sd.cross(lat).normalized()
    pat = eval_centroid(AN['Patella'])
    if (pat - K).dot(fr) < 0: fr = -fr
    return K, A, sd, lat, fr
def shin_up(): return (bone_world('lowerleg01.R') - bone_world('foot.R')).normalized()        # frame the right shin upright
def ease(a_, b_, k): return a_.lerp(b_, sm(clamp(k, 0, 1)))
# where his get-up starts and ends inside the loop: frame 0 = s 0.12 (already leaning, hands pushing); the last beat ends at s 0.115
S0 = 0.42
B0_CAM = (V3(-1.0, -0.95, 0.2), V3(-0.12, -0.45, 0.32), 24)
def b0_cam(t, k):
    cp, ct, lens = B0_CAM
    return cp + V3(0.2, -0.15, -0.06) * k + shake(t, 0.006), ct + V3(0.0, -0.15, -0.18) * k, lens + 6 * k

def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    FLOOR_LOG.clear(); PLANT.clear()
    xray_mode(False); PUFF.strength = 0.004 if (2 <= nb <= 8 or (nb == 9 and u < 0.62) or (nb == 10 and u < 0.5)) else 0.0; TVS['tv'] = t; BODY['pins'] = 0.0; BODY['dead'] = 0.0; BODY['tt'] = t; SQ.value = 0.0
    nerves(t); arteries(t); vasa(t)
    for o in KEY_MUS: o['act'] = 0.0
    if nb == 0:                                             # he gets up, the foot folds, he lurches into the table
        s_ = S0 + (1.0 - S0) * smooth(0.0, 0.95, u) ** 0.85
        standing(s_, t); cp, ct, lens = b0_cam(t, smooth(0.0, 1.0, u)); look(cp, ct, lens, 3.2, focus=bone_world('foot.R'))
    elif nb == 1:                                           # an hour earlier: legs crossed, gaming
        seated(1.0, t=t)
        cp = ease(V3(-1.25, -1.75, 1.05), V3(0.75, -1.05, 0.72), u) + shake(t, 0.004); ct = ease(V3(0.0, -0.1, 0.7), V3(0.12, -0.22, 0.52), u)
        look(cp, ct, lerp(30, 42, sm(u)), 4.0)
    elif nb == 2:                                           # x-ray: the nerve wraps the fibula right where his knee presses
        seated(1.0, t=t); xray_mode(True, muscles=0.93); pw = pinch_world(); K, A, sd, lat, fr = leg_frame()
        nerves(t, glow=1.4, other=0.25, pulse=0.25); arteries(t, glow=0.3, pulse=0.15)
        cp = pw + (lat * 0.75 + fr * 0.65 - sd * 0.15).normalized() * lerp(0.42, 0.22, sm(u)) + shake(t, 0.002)
        look(cp, pw, lerp(35, 42, sm(u)), 5.0, up=-sd)
    elif nb == 3:                                           # the muscles it runs (lift the foot), the skin it feels (top of the foot)
        k = smooth(0.1, 0.45, u); kd = smooth(0.15, 0.45, u) - smooth(0.6, 0.85, u)
        seated(1.0, t=t); rot('foot.R', 22 - 45 * kd, 0, 0); bpy.context.view_layer.update(); floor_fix()
        xray_mode(True, muscles=0.25); nerves(t, glow=1.2, other=0.2, pulse=0.5); arteries(t, glow=0.25, pulse=0.1)
        for o in KEY_MUS: o['act'] = kd
        BODY['pins'] = 0.0
        K, A, sd, lat, fr = leg_frame(); tib = K.lerp(A, lerp(0.4, 1.05, smooth(0.45, 0.9, u))) + fr * 0.02 * smooth(0.45, 0.9, u)
        cp = tib + (fr * 0.85 + lat * 0.45).normalized() * 0.4 + shake(t, 0.002); look(cp, tib, 32, 5.0, up=-sd)
    elif nb == 4:                                           # signals racing down the nerve
        seated(1.0, t=t); xray_mode(True, muscles=0.65); nerves(t, glow=0.9, other=0.2, pulse=1.4, speed=1.4); arteries(t, glow=0.2, pulse=0.05)
        k = smooth(0.0, 1.0, u); K, A, sd, lat, fr = leg_frame(); a0 = bone_world('upperleg02.R').lerp(K, 0.55)
        tgt = a0.lerp(A, k); cp = tgt + (lat * 0.65 + fr * 0.6).normalized() * 0.4 + shake(t, 0.003); look(cp, tgt, 30, 5.0, up=-sd)
    elif nb == 5:                                           # macro: the knee squeezes the nerve and pinches its blood vessels shut
        seated(1.0, t=t); xray_mode(True, muscles=0.96); pw = pinch_world(); K, A, sd, lat, fr = leg_frame()
        sq = smooth(0.1, 0.5, u); SQ.value = sq
        nerves(t, glow=1.3, other=0.15, pulse=0.6); arteries(t, glow=0.2, pulse=0.05); vasa(t, flow=1.0 - smooth(0.35, 0.8, u), glow=1.6)
        cp = pw + (lat * 0.75 + fr * 0.7 - sd * 0.2).normalized() * lerp(0.17, 0.11, sm(u)) + shake(t, 0.0005); look(cp, pw, 45, 7.0, up=-sd)
    elif nb == 6:                                           # starved: the nerve goes dark past the pinch, the foot goes quiet
        seated(1.0, t=t); xray_mode(True, muscles=0.7); SQ.value = 1.0; vasa(t, flow=0.0)
        kd = smooth(0.0, 0.6, u)
        nerves(t, glow=1.1, other=0.2, pulse=1.0 - 0.6 * kd, speed=1.4, dead=0.9 * kd, block=PINCH); arteries(t, glow=0.2, pulse=0.05)
        BODY['dead'] = smooth(0.3, 0.9, u)
        K, A, sd, lat, fr = leg_frame(); a0 = pinch_world(); a1 = bone_world('foot.R', True); tgt = a0.lerp(a1, smooth(0.15, 0.9, u))
        cp = tgt + (lat * 0.5 + fr * 0.75).normalized() * lerp(0.3, 0.42, sm(u)) + shake(t, 0.002); look(cp, tgt, 32, 5.0, up=-sd)
    elif nb == 7:                                           # slow motion, x-ray: he stands, the dead foot drops and the toes drag
        s_ = lerp(0.58, 0.9, smooth(0.0, 1.0, u)); standing(s_, t)
        xray_mode(True, left_bones=False, muscles=0.5); nerves(t, glow=1.0, other=0.2, pulse=0.0, dead=0.9, block=PINCH); arteries(t, glow=0.25, pulse=0.05)
        BODY['dead'] = 1.0
        for o in KEY_MUS: o['dim'] = 0.25
        fw = bone_world('foot.R'); cp = fw + V3(-0.62, -0.28, 0.12) + shake(t, 0.003); look(cp, fw + V3(0, -0.06, -0.02), 30, 4.0)
    elif nb == 8:                                           # pressure off: blood rushes back down the leg
        standing(0.62, t); xray_mode(True, left_bones=False, muscles=0.75)
        kf = smooth(0.0, 0.8, u)
        arteries(t, glow=0.5 + 1.2 * kf, pulse=2.0, speed=1.1, front=lerp(0.45, 1.25, kf)); vasa(t, flow=kf, glow=1.6)
        nerves(t, glow=0.9, other=0.2, dead=0.9 * (1 - kf), block=PINCH); BODY['dead'] = 1.0 - kf
        kn = bone_world('lowerleg01.R'); fw = bone_world('foot.R'); tgt = kn.lerp(fw, smooth(0.0, 1.0, u))
        cp = tgt + V3(-0.42, -0.4, 0.1) + shake(t, 0.003); look(cp, tgt, 30, 4.5)
    elif nb == 9:                                           # pins and needles: the waking nerve fires at random
        if u < 0.62:
            standing(0.62, t); xray_mode(True, left_bones=False, muscles=0.6)
            nerves(t, glow=0.7, other=0.2, pulse=0.0, spark=1.0); arteries(t, glow=0.6, pulse=0.6); BODY['pins'] = 1.0
            fw = bone_world('foot.R'); cp = fw + ease(V3(-0.3, -0.35, 0.3), V3(-0.22, -0.25, 0.2), u / 0.62) + shake(t, 0.004); look(cp, fw + V3(0, -0.05, 0), 32, 4.0)
        else:                                               # he shakes the foot out
            k = (u - 0.62) / 0.38; standing(0.62, t)
            rot('foot.R', 10 + 25 * math.sin(t * 19), 15 * math.sin(t * 13), 0); rot('lowerleg01.R', 0, 0, 0); bpy.context.view_layer.update()
            TGT['ankR'].location = TGT['ankR'].location + V3(0.0, -0.05, 0.1 + 0.03 * math.sin(t * 17)); bpy.context.view_layer.update(); floor_fix()
            cp = V3(-0.95, -1.6, 0.75) + shake(t, 0.006); look(cp, V3(-0.05, -0.35, 0.55), 30, 5.0)
    elif nb == 10:                                          # back on the couch, wiggling it awake
        seated(0.0, t=t, pad=0.0); rot('foot.R', 12 * math.sin(t * 9), 8 * math.sin(t * 6), 0)
        for f_ in range(1, 6): rot(f'toe{f_}-1.R', 20 + 18 * math.sin(t * 11 + f_))
        bpy.context.view_layer.update(); floor_fix()
        if u < 0.5:
            xray_mode(True, left_bones=False, muscles=0.5); nerves(t, glow=1.1, other=0.25, pulse=0.9, speed=1.4, spark=0.5 * (1 - u / 0.5))
            arteries(t, glow=0.6, pulse=0.5); BODY['pins'] = 0.6 * (1 - u / 0.5)
            fw = bone_world('foot.R'); cp = fw + V3(-0.35, -0.42, 0.25); look(cp, fw, 30, 4.0)
        else:
            cp = ease(V3(-1.3, -1.5, 0.95), V3(-1.1, -1.4, 0.55), (u - 0.5) / 0.5) + shake(t, 0.004); look(cp, V3(-0.05, -0.2, 0.55), 30, 4.0)
    else:                                                   # loop: shakes it out and gets up again (runs into frame 0)
        k = smooth(0.35, 1.0, u)
        if k <= 0: seated(0.0, t=t, pad=0.0)
        else: standing(S0 * smooth(0.0, 1.0, (u - 0.35) / 0.65) ** 1.1 * 0.96, t)
        cp0 = V3(-1.15, -1.45, 0.62); cpe, cte, lense = B0_CAM
        cp = ease(cp0, cpe, smooth(0.0, 0.95, u)) + shake(t, 0.006 * smooth(0.5, 1.0, u)); ct = ease(V3(-0.05, -0.25, 0.45), cte, smooth(0.0, 0.95, u))
        look(cp, ct, lerp(30, lense, smooth(0.0, 0.95, u)), lerp(4.0, 3.2, u), focus=bone_world('foot.R') if u > 0.6 else None)

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
