# What happens if you drop a ball down a hole through the Earth (Blender, Cycles). No people. Four sets far apart in one scene:
# a farm field with a round shaft and a concrete collar (day), the inside of the tunnel (walls stream past; rock, then the glowing
# mantle, then the white-hot core), a cutaway Earth in space (layers to scale, the tunnel on the cut edge, the ball as a glowing dot),
# and the far side at night (the same collar, stars, moonlight). A vacuum tunnel: ~38 min end to end, over 17,895 mph at the middle
# (Klotz 2015 / Live Science). The ball pops out, stops, falls back; the end rises out of the first hole into frame one (the loop).
#   python3 hole.py OUTDIR F0 F1 [--samples 40] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
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

# ================================================================ numbers (checked: Live Science / Klotz 2015, NASA, Gizmodo 2013)
G = 9.81
TRIP_MIN = 38.0                        # one way, real (layered) Earth, no air
VMAX_MPH = 17895                       # "speeds over 8 km/s (17,895 mph)"
HR = 1.5                               # shaft radius, m
BALL_R = 0.35

# ================================================================ helpers
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
def mixc(nt, fac, a_, b_):
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    if isinstance(fac, (int, float)): mx.inputs['Factor'].default_value = fac
    else: nt.links.new(fac, mx.inputs['Factor'])
    for k, v in (('A', a_), ('B', b_)):
        if isinstance(v, tuple): mx.inputs[k].default_value = v if len(v) == 4 else (*v, 1)
        else: nt.links.new(v, mx.inputs[k])
    return mx.outputs['Result']
def ramp(nt, fac, stops, interp='LINEAR'):
    r_ = nt.nodes.new('ShaderNodeValToRGB'); el = r_.color_ramp.elements; r_.color_ramp.interpolation = interp
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1); el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p_, c_ in stops[1:-1]: e_ = el.new(p_); e_.color = (*c_, 1)
    nt.links.new(fac, r_.inputs['Fac']); return r_.outputs['Color']
def coord(nt, kind='Object'):
    tc = nt.nodes.new('ShaderNodeTexCoord'); return tc.outputs[kind]
def sepz(nt, vec):
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(vec, sx.inputs[0]); return sx
def tnoise(nt, vec, scale, detail=6.0, dist=0.0):
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nz.inputs['Distortion'].default_value = dist; nt.links.new(vec, nz.inputs['Vector']); return nz.outputs['Fac']
def ring_mesh(name, zs, r, rr, m, parent=None, seg=40, segr=8, loc=(0, 0, 0)):
    """many thin rings (tori) inside a shaft, one mesh"""
    vs, fs = [], []
    for z0 in zs:
        b0 = len(vs)
        for i in range(seg):
            a_ = 2 * math.pi * i / seg
            for j in range(segr):
                c_ = 2 * math.pi * j / segr; R_ = r + rr * math.cos(c_)
                vs.append((R_ * math.cos(a_), R_ * math.sin(a_), z0 + rr * math.sin(c_)))
        for i in range(seg):
            for j in range(segr):
                i2, j2 = (i + 1) % seg, (j + 1) % segr
                fs.append((b0 + i * segr + j, b0 + i2 * segr + j, b0 + i2 * segr + j2, b0 + i * segr + j2))
    return mesh(name, vs, fs, m, parent, loc=loc)

# ================================================================ materials
def rock_wall(name, glow=True):
    """tunnel rock in bands along z; with 'depth' (0 rock .. 0.5 mantle .. 1 core) it turns dark red with glowing cracks, then white-hot"""
    m = mat(name, (0.3, 0.27, 0.24), 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']; oc = coord(nt)
    sz = sepz(nt, oc); band = tnoise(nt, oc, 0.9, 4, 3.0)
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 0.35; wv.inputs['Distortion'].default_value = 6.0
    wv.inputs['Detail'].default_value = 4; nt.links.new(oc, wv.inputs['Vector'])
    rockc = ramp(nt, wv.outputs['Fac'], [(0.0, (0.16, 0.13, 0.11)), (0.45, (0.36, 0.31, 0.26)), (0.7, (0.25, 0.2, 0.16)), (1.0, (0.45, 0.4, 0.34))])
    rockc = mixc(nt, math_(nt, 'MULTIPLY', band, 0.5), rockc, (0.12, 0.1, 0.09))
    if not glow: nt.links.new(rockc, b.inputs['Base Color']); return m
    d = objattr(nt, 'depth')
    mant = math_(nt, 'MULTIPLY_ADD', d, 3.0, -0.6); mant = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', mant, 0.0), 1.0)      # 0.2..0.53
    core = math_(nt, 'MULTIPLY_ADD', d, 3.3, -2.3); core = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', core, 0.0), 1.0)      # 0.7..1.0
    mantc = mixc(nt, wv.outputs['Fac'], (0.09, 0.025, 0.015), (0.2, 0.05, 0.02))
    base = mixc(nt, mant, rockc, mantc); base = mixc(nt, core, base, (0.12, 0.04, 0.015)); nt.links.new(base, b.inputs['Base Color'])
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 1.6; nt.links.new(oc, vo.inputs['Vector'])
    crack = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo.outputs['Distance'], 14.0)), 0.0), 2.0)
    flick = tnoise(nt, oc, 0.6, 3)
    ecol = mixc(nt, core, (1.0, 0.32, 0.05), mixc(nt, flick, (1.0, 0.22, 0.02), (1.0, 0.5, 0.08)))
    nt.links.new(ecol, b.inputs['Emission Color'])
    estr = math_(nt, 'ADD', math_(nt, 'MULTIPLY', crack, math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', mant, math_(nt, 'SUBTRACT', 1.0, core)), 2.2)), math_(nt, 'MULTIPLY', core, math_(nt, 'MULTIPLY_ADD', math_(nt, 'POWER', flick, 3.0), 0.9, 0.04)))
    estr = math_(nt, 'ADD', estr, math_(nt, 'MULTIPLY', mant, 0.12))
    nt.links.new(estr, b.inputs['Emission Strength']); return m
def lamp_ring_mat(name):
    """the light rings in the shaft: fade out once the walls glow on their own"""
    m = emis(name, (1.0, 0.9, 0.75), 9.0); nt = m.node_tree; e_ = nt.nodes['Emission']
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY_ADD', objattr(nt, 'depth'), -3.0, 1.0), 0.0), 9.0), e_.inputs['Strength'])
    return m
CONC = noisy(mat('concrete', (0.36, 0.355, 0.34), 0.9), 3.0, 0.25, 0.08)
STEEL = mat('steel', (0.45, 0.45, 0.47), 0.55, 1.0)
YEL = mat('yellow', (0.9, 0.62, 0.04), 0.5)
BALL_M = mat('ball', (0.85, 0.12, 0.03), 0.22, coat=0.6)
_bn = BALL_M.node_tree; _bz = sepz(_bn, coord(_bn))
_st = math_(_bn, 'LESS_THAN', math_(_bn, 'ABSOLUTE', _bz.outputs['Z']), 0.05)
_bn.links.new(mixc(_bn, _st, (0.85, 0.12, 0.03), (0.92, 0.92, 0.9)), _bn.nodes['Principled BSDF'].inputs['Base Color'])

def collar(name, at, parent=None):
    """concrete collar round the hole, a steel lip, a yellow safety band, four short bollards"""
    pr = [(HR, -2.0), (HR, 0.3), (HR + 0.04, 0.36), (HR + 0.5, 0.36), (HR + 0.62, 0.3), (HR + 0.75, 0.0), (HR + 0.8, -0.1)]
    out = [lathe(name, pr, 64, CONC, parent, loc=at)]
    out.append(lathe(name + '_lip', [(HR - 0.02, 0.3), (HR - 0.02, 0.38), (HR + 0.06, 0.38), (HR + 0.06, 0.36)], 64, STEEL, parent, loc=at))
    out.append(lathe(name + '_band', [(HR + 0.18, 0.361), (HR + 0.36, 0.361)], 64, YEL, parent, loc=at))
    for k in range(4):
        a_ = math.pi / 4 + k * math.pi / 2; p = Vector(at) + Vector((math.cos(a_), math.sin(a_), 0)) * (HR + 1.4)
        out.append(prim('cylinder', f'{name}_post{k}', YEL, loc=p + Vector((0, 0, 0.45)), radius=0.09, depth=0.9, vertices=16))
    return out
def shaft(name, at, depth, ring_every, ring_mat, wall_mat):
    s_ = lathe(name, [(0, -depth), (HR, -depth), (HR, -2.0)], 48, wall_mat, loc=at)
    rg = ring_mesh(name + '_rings', [-3.0 - ring_every * k for k in range(int((depth - 4) / ring_every))], HR - 0.03, 0.035, ring_mat, loc=at)
    s_['depth'] = 0.0; rg['depth'] = 0.0; return s_, rg

# ================================================================ set 1: the farm field, day (at the origin)
DS = Vector((0, 0, 0))
GRASS = noisy(mat('grass', (0.15, 0.27, 0.07), 0.92, sheen=0.4), 0.08, 0.35, 0.05)
_gn = GRASS.node_tree; _gb = _gn.nodes['Principled BSDF']; _bm = _gn.nodes.new('ShaderNodeBump'); _bm.inputs['Strength'].default_value = 0.35
_gn.links.new(tnoise(_gn, coord(_gn), 30.0, 8), _bm.inputs['Height']); _gn.links.new(_bm.outputs['Normal'], _gb.inputs['Normal'])
GROUND = lathe('ground', [(HR + 0.78, -0.08), (6, 0.0), (60, 0.0), (400, 0.0), (4000, -20.0)], 96, GRASS, loc=DS)
DIRT = noisy(mat('dirt', (0.3, 0.22, 0.14), 0.95), 4.0, 0.3, 0.05)
APRON = lathe('apron', [(HR + 0.79, -0.06), (HR + 2.6, 0.005)], 64, DIRT, loc=DS)
COL_D = collar('collar_d', DS)
SHAFT_D, RINGS_D = shaft('shaft_d', DS, 420.0, 7.0, lamp_ring_mat('ringlamp_d'), rock_wall('rock_d', glow=False))
random.seed(5)
for k in range(46):                                                # trees on the field edge: a trunk and a few round crowns
    a_ = random.uniform(0, 2 * math.pi); d_ = random.uniform(28, 160) if k < 30 else random.uniform(160, 420)
    tx_, ty_ = math.cos(a_) * d_, math.sin(a_) * d_; hh = random.uniform(7, 14)
    prim('cylinder', f'trunk_{k}', mat('bark', (0.12, 0.08, 0.05), 0.9), loc=(tx_, ty_, hh * 0.3), radius=0.25, depth=hh * 0.6, vertices=8)
    for j in range(3):
        prim('ico_sphere', f'crown_{k}_{j}', mat(f'leaf_{(k + j) % 3}', (0.07 + 0.03 * ((k + j) % 3), 0.19 + 0.04 * ((k + j) % 3), 0.05), 0.85, sheen=0.5),
             loc=(tx_ + random.uniform(-1.5, 1.5), ty_ + random.uniform(-1.5, 1.5), hh * random.uniform(0.62, 0.85)), subdivisions=2, radius=hh * random.uniform(0.25, 0.36))
FENCE = mat('fence', (0.42, 0.36, 0.28), 0.9)
for k in range(40):                                                # a wire fence line across the back of the field
    x_ = -60 + k * 3.2; prim('cylinder', f'fpost_{k}', FENCE, loc=(x_, 22, 0.6), radius=0.06, depth=1.2, vertices=6)
for z_ in (0.55, 0.95): tube(f'fwire_{z_}', [(-60, 22, z_), (65, 22, z_)], 0.008, STEEL, seg=4)
for k in range(6):                                                 # hay bales
    a_ = 1.2 + k * 0.5; prim('cylinder', f'bale_{k}', noisy(mat('hay', (0.62, 0.5, 0.26), 0.95), 6.0, 0.3), loc=(math.cos(a_) * (14 + k), math.sin(a_) * (14 + k), 0.6),
                             rot=(R(90), 0, a_), radius=0.6, depth=1.2, vertices=24)

# ================================================================ set 2: inside the tunnel (far below the field, closed tube)
TS = Vector((3000, 0, -5000))
TUBE_LEN = 900.0; RING_P = 9.0
TWALL = rock_wall('rock_t')
TUBE = lathe('tube', [(0, -TUBE_LEN / 2), (HR, -TUBE_LEN / 2), (HR, TUBE_LEN / 2), (0, TUBE_LEN / 2)], 64, TWALL, loc=TS)
TRINGS = ring_mesh('tube_rings', [-TUBE_LEN / 2 + 4 + RING_P * k for k in range(int((TUBE_LEN - 8) / RING_P))], HR - 0.03, 0.035, lamp_ring_mat('ringlamp_t'), loc=TS)
TUBE['depth'] = 0.0; TRINGS['depth'] = 0.0
SPARK_M = bpy.data.materials.new('spark'); SPARK_M.use_nodes = True; _pn = SPARK_M.node_tree; _pn.nodes.remove(_pn.nodes['Principled BSDF'])
_pe = _pn.nodes.new('ShaderNodeEmission'); _pd = objattr(_pn, 'depth')
_pn.links.new(mixc(_pn, math_(_pn, 'MINIMUM', math_(_pn, 'MULTIPLY', _pd, 3.0), 1.0), (0.85, 0.8, 0.7), (1.0, 0.45, 0.08)), _pe.inputs['Color'])
_pn.links.new(math_(_pn, 'MULTIPLY_ADD', _pd, 10.0, 1.5), _pe.inputs['Strength']); _pn.links.new(_pe.outputs[0], _pn.nodes['Material Output'].inputs['Surface'])
SPARK_W = 34.0; random.seed(21); SPARKS = []
for k in range(60):                                                # dust in the rock, embers lower down: streaks that show the speed
    a_ = random.uniform(0, 2 * math.pi); r_ = random.uniform(0.45, 1.35); o = prim('ico_sphere', f'spark_{k}', SPARK_M, subdivisions=1, radius=random.uniform(0.008, 0.02))
    o['ph'] = (math.cos(a_) * r_, math.sin(a_) * r_, random.uniform(0, SPARK_W), random.uniform(0.8, 1.25)); o['depth'] = 0.0; o.visible_shadow = False; SPARKS.append(o)
def sparks_set(soff, depth, bases=None):
    for i, o in enumerate(SPARKS):
        x_, y_, z0, sp = o['ph']; zz = z0 + soff * sp; bz = bases[i] if bases else math.floor(zz / SPARK_W) * SPARK_W
        o.location = TS + Vector((x_, y_, zz - bz - SPARK_W * 0.55)); o['depth'] = depth
def spark_bases(soff): return [math.floor((o['ph'][2] + soff * o['ph'][3]) / SPARK_W) * SPARK_W for o in SPARKS]
def tube_set(off, depth):
    for o in (TUBE, TRINGS): o.location = TS + Vector((0, 0, off)); o['depth'] = depth

# ================================================================ set 3: the cutaway Earth in space
CS = Vector((0, 40000, 0)); RE = 10.0
STARS = bpy.data.materials.new('stars'); STARS.use_nodes = True; _sn = STARS.node_tree; _sn.nodes.remove(_sn.nodes['Principled BSDF'])
def star_shader(nt, base, dens_scale=180.0, thresh=0.985, power=40.0):
    e_ = nt.nodes.new('ShaderNodeEmission'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = dens_scale
    nt.links.new(coord(nt, 'Generated'), vo.inputs['Vector']); vo2 = nt.nodes.new('ShaderNodeTexVoronoi'); vo2.inputs['Scale'].default_value = dens_scale * 0.37
    nt.links.new(coord(nt, 'Generated'), vo2.inputs['Vector'])
    s1 = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo.outputs['Distance'], 9.0)), 0.0), power)
    s2 = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo2.outputs['Distance'], 7.0)), 0.0), power * 0.6)
    st = math_(nt, 'ADD', math_(nt, 'MULTIPLY', s1, 2.5), math_(nt, 'MULTIPLY', s2, 6.0))
    col = base if not isinstance(base, tuple) else None
    c_ = mixc(nt, math_(nt, 'MINIMUM', st, 1.0), base, (1.0, 0.97, 0.92))
    nt.links.new(c_, e_.inputs['Color']); e_.inputs['Strength'].default_value = 1.0
    nt.links.new(e_.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
star_shader(_sn, (0.002, 0.003, 0.008))
SKYBALL = prim('uv_sphere', 'starsphere', STARS, loc=CS, segments=48, ring_count=24, radius=600)
SKYBALL.visible_shadow = True
SUN_C = light_at('sun_c', 'AREA', CS + Vector((90, -60, 55)), CS, 3.0e5, (1.0, 0.95, 0.88), 25)
FILL_C = light_at('fill_c', 'AREA', CS + Vector((-40, -70, -10)), CS, 1.2e4, (0.5, 0.6, 1.0), 30)
# the surface: oceans and land, a quarter wedge cut out (x > 0, y < 0)
def earth_shell(name, r, m, lon0=0.0, lon1=270.0, nlon=180, nlat=90):
    vs, fs = [], []
    for i in range(nlat + 1):
        th = math.pi * i / nlat
        for j in range(nlon + 1):
            ph = R(lon0 + (lon1 - lon0) * j / nlon); vs.append((r * math.sin(th) * math.cos(ph), r * math.sin(th) * math.sin(ph), r * math.cos(th)))
    for i in range(nlat):
        for j in range(nlon): a0 = i * (nlon + 1) + j; fs.append((a0, a0 + 1, a0 + nlon + 2, a0 + nlon + 1))
    return mesh(name, vs, fs, m, loc=CS)
EARTH_M = mat('earth', (0.03, 0.1, 0.32), 0.35); _en = EARTH_M.node_tree; _eb = _en.nodes['Principled BSDF']
_land = tnoise(_en, coord(_en), 0.22, 7, 0.4)
_lm = math_(_en, 'GREATER_THAN', _land, 0.53)
_lc = ramp(_en, tnoise(_en, coord(_en), 0.9, 5), [(0.3, (0.1, 0.22, 0.05)), (0.55, (0.35, 0.3, 0.14)), (0.8, (0.2, 0.3, 0.08))])
_ez = sepz(_en, coord(_en)); _ice = math_(_en, 'GREATER_THAN', math_(_en, 'ABSOLUTE', _ez.outputs['Z']), RE * 0.9)
_c1 = mixc(_en, _lm, (0.02, 0.08, 0.3), _lc); _c1 = mixc(_en, _ice, _c1, (0.85, 0.88, 0.92))
_en.links.new(_c1, _eb.inputs['Base Color']); _en.links.new(math_(_en, 'MULTIPLY_ADD', _lm, 0.6, 0.25), _eb.inputs['Roughness'])
EARTH = earth_shell('earth', RE, EARTH_M)
CLOUD_M = mat('clouds', (1, 1, 1), 0.9, alpha=1.0); _cn = CLOUD_M.node_tree; CLOUD_M.blend_method = 'BLEND'
_cn.links.new(math_(_cn, 'MULTIPLY', math_(_cn, 'GREATER_THAN', tnoise(_cn, coord(_cn), 0.6, 6, 1.0), 0.6), 0.85), _cn.nodes['Principled BSDF'].inputs['Alpha'])
CLOUDS = earth_shell('clouds', RE * 1.012, CLOUD_M)
# the two cut faces, colored by depth: crust, mantle (red to orange), outer core (orange), inner core (yellow-white)
CUT_M = mat('cut', (0.5, 0.2, 0.1), 0.8); _un = CUT_M.node_tree; _ub = _un.nodes['Principled BSDF']
_len = nt_ = None
_vl = _un.nodes.new('ShaderNodeVectorMath'); _vl.operation = 'LENGTH'; _un.links.new(coord(_un), _vl.inputs[0])
_rr = math_(_un, 'DIVIDE', _vl.outputs['Value'], RE)
_rr = math_(_un, 'ADD', _rr, math_(_un, 'MULTIPLY', tnoise(_un, coord(_un), 1.6, 4), 0.012))
CUT_STOPS = [(0.0, (1.0, 0.95, 0.75)), (0.185, (1.0, 0.85, 0.45)), (0.195, (1.0, 0.55, 0.12)), (0.54, (0.95, 0.38, 0.06)),
             (0.552, (0.75, 0.16, 0.04)), (0.97, (0.38, 0.06, 0.03)), (0.982, (0.33, 0.24, 0.17)), (1.0, (0.3, 0.22, 0.15))]
_cc = ramp(_un, _rr, CUT_STOPS); _un.links.new(_cc, _ub.inputs['Base Color']); _un.links.new(_cc, _ub.inputs['Emission Color'])
_es = ramp(_un, _rr, [(0.0, (0.75, 0.75, 0.75)), (0.19, (0.5, 0.5, 0.5)), (0.54, (0.35, 0.35, 0.35)), (0.56, (0.14, 0.14, 0.14)), (0.97, (0.06, 0.06, 0.06)), (0.98, (0.0, 0.0, 0.0))])
_sxe = sepz(_un, _es); _core_boost = objattr(_un, 'boost')
_un.links.new(math_(_un, 'MULTIPLY', _sxe.outputs['X'], math_(_un, 'ADD', 1.0, _core_boost)), _ub.inputs['Emission Strength'])
def half_disk(name, plane, nr=60, na=120):
    vs, fs = [], []
    for i in range(nr + 1):
        r_ = RE * i / nr
        for j in range(na + 1):
            al = math.pi * j / na; h_, z_ = r_ * math.sin(al), r_ * math.cos(al)
            vs.append((h_, 0, z_) if plane == 'xz' else (0, -h_, z_))
    for i in range(nr):
        for j in range(na): a0 = i * (na + 1) + j; fs.append((a0, a0 + 1, a0 + na + 2, a0 + na + 1))
    o = mesh(name, vs, fs, CUT_M, loc=CS, smooth_=False); o['boost'] = 0.0; return o
CUTS = [half_disk('cut_xz', 'xz'), half_disk('cut_yz', 'yz')]
ATM_M = bpy.data.materials.new('atm'); ATM_M.use_nodes = True; _an = ATM_M.node_tree; _an.nodes.remove(_an.nodes['Principled BSDF']); ATM_M.blend_method = 'BLEND'
_ae = _an.nodes.new('ShaderNodeEmission'); _ae.inputs['Color'].default_value = (0.35, 0.6, 1.0, 1); _ae.inputs['Strength'].default_value = 2.5
_at = _an.nodes.new('ShaderNodeBsdfTransparent'); _am = _an.nodes.new('ShaderNodeMixShader'); _lw = _an.nodes.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.25
_pw = math_(_an, 'POWER', _lw.outputs['Facing'], 3.0); _an.links.new(_pw, _am.inputs['Fac'])
_an.links.new(_at.outputs[0], _am.inputs[1]); _an.links.new(_ae.outputs[0], _am.inputs[2]); _an.links.new(_am.outputs[0], _an.nodes['Material Output'].inputs['Surface'])
ATM = earth_shell('atmosphere', RE * 1.035, ATM_M, nlon=120, nlat=60); ATM.visible_shadow = False
# the tunnel along the cut edge (x = y = 0): dark outside the core, the core part can melt shut
TUN_M = mat('tunnel', (0.02, 0.02, 0.025), 0.4, emit=(0.4, 0.75, 1.0), estr=0.6)
TUN_OUT = [tube('tun_top', [CS + Vector((0, 0, RE * 1.01)), CS + Vector((0, 0, RE * 0.546))], 0.07, TUN_M, seg=16),
           tube('tun_bot', [CS + Vector((0, 0, -RE * 0.546)), CS + Vector((0, 0, -RE * 1.01))], 0.07, TUN_M, seg=16)]
TUNI_M = mat('tunnel_core', (0.02, 0.02, 0.025), 0.4, emit=(1.0, 0.55, 0.15), estr=0.0); _ti = TUNI_M.node_tree
_ti.links.new(math_(_ti, 'MULTIPLY_ADD', objattr(_ti, 'heat'), 14.0, 0.0), _ti.nodes['Principled BSDF'].inputs['Emission Strength'])
_ti.links.new(mixc(_ti, objattr(_ti, 'heat'), (0.4, 0.75, 1.0), (1.0, 0.55, 0.15)), _ti.nodes['Principled BSDF'].inputs['Emission Color'])
TUN_IN = tube('tun_core', [CS + Vector((0, 0, RE * 0.546)), CS + Vector((0, 0, -RE * 0.546))], 0.07, TUNI_M, seg=16); TUN_IN['heat'] = 0.0
DOT = prim('uv_sphere', 'dot', emis('dot_m', (1.0, 0.2, 0.04), 7.0), loc=CS, segments=24, ring_count=12, radius=0.34)
TRAIL_M = bpy.data.materials.new('trail'); TRAIL_M.use_nodes = True; _tn = TRAIL_M.node_tree; _tn.nodes.remove(_tn.nodes['Principled BSDF']); TRAIL_M.blend_method = 'BLEND'
_te = _tn.nodes.new('ShaderNodeEmission'); _te.inputs['Color'].default_value = (1.0, 0.5, 0.15, 1); _te.inputs['Strength'].default_value = 3.0
_tt = _tn.nodes.new('ShaderNodeBsdfTransparent'); _tm = _tn.nodes.new('ShaderNodeMixShader')
_tz = sepz(_tn, coord(_tn, 'Generated')); _tn.links.new(math_(_tn, 'POWER', math_(_tn, 'SUBTRACT', 1.0, _tz.outputs['Z']), 2.0), _tm.inputs['Fac'])
_tn.links.new(_tt.outputs[0], _tm.inputs[1]); _tn.links.new(_te.outputs[0], _tm.inputs[2]); _tn.links.new(_tm.outputs[0], _tn.nodes['Material Output'].inputs['Surface'])
TRAIL = prim('cylinder', 'trail', TRAIL_M, loc=CS, radius=0.2, depth=1.0, vertices=16); TRAIL.visible_shadow = False
MELT = prim('ico_sphere', 'melt_glow', emis('melt_m', (1.0, 0.7, 0.3), 0.0), loc=CS, subdivisions=3, radius=RE * 0.56); MELT.hide_render = True
def earth_dot(m_):
    """the ball in the cutaway: m_ minutes into the trip (0 top .. 38 bottom .. 76 top), uniform-Earth shape for the drawing"""
    z = RE * math.cos(math.pi * m_ / TRIP_MIN); v = math.sin(math.pi * m_ / TRIP_MIN)
    DOT.location = CS + Vector((0, 0, z)); L_ = 3.2 * abs(v); dirn = 1 if (m_ % (2 * TRIP_MIN)) < TRIP_MIN else -1
    TRAIL.scale = (1, 1, max(L_, 1e-3)); TRAIL.location = CS + Vector((0, 0, z + dirn * L_ / 2)); TRAIL.rotation_euler = (0 if dirn > 0 else math.pi, 0, 0)
    TRAIL.hide_render = L_ < 0.05

# ================================================================ set 4: the far side, night (a dome of stars blocks the sun)
NS = Vector((20000, 0, 0))
NIGHT = bpy.data.materials.new('night'); NIGHT.use_nodes = True; _nn = NIGHT.node_tree; _nn.nodes.remove(_nn.nodes['Principled BSDF'])
_nz = sepz(_nn, coord(_nn, 'Generated'))
_nsky = ramp(_nn, _nz.outputs['Z'], [(0.5, (0.05, 0.07, 0.14)), (0.56, (0.018, 0.028, 0.07)), (1.0, (0.004, 0.006, 0.022))])
star_shader(_nn, _nsky, 140.0)
DOME = prim('uv_sphere', 'dome', NIGHT, loc=NS, segments=64, ring_count=32, radius=700)
MOON = prim('uv_sphere', 'moon', emis('moon_m', (0.95, 0.95, 0.9), 4.0), loc=NS + Vector((-250, 480, 300)), segments=32, ring_count=16, radius=18)
MOON.visible_shadow = False
MOONL = light_at('moonlight', 'AREA', NS + Vector((-120, 230, 150)), NS, 2.2e5, (0.62, 0.72, 1.0), 40)
SAND = noisy(mat('sand', (0.38, 0.33, 0.25), 0.95), 0.5, 0.35, 0.05)
_sn2 = SAND.node_tree; _sb2 = _sn2.nodes['Principled BSDF']; _bm2 = _sn2.nodes.new('ShaderNodeBump'); _bm2.inputs['Strength'].default_value = 0.4
_sn2.links.new(tnoise(_sn2, coord(_sn2), 9.0, 6), _bm2.inputs['Height']); _sn2.links.new(_bm2.outputs['Normal'], _sb2.inputs['Normal'])
GROUND_N = lathe('ground_n', [(HR + 0.78, -0.08), (6, 0.0), (80, 0.3), (720, 4.0)], 96, SAND, loc=NS)
COL_N = collar('collar_n', NS)
SHAFT_N, RINGS_N = shaft('shaft_n', NS, 120.0, 7.0, lamp_ring_mat('ringlamp_n'), rock_wall('rock_n', glow=False))
random.seed(9)
SCRUB = mat('scrub', (0.06, 0.09, 0.04), 0.9)
for k in range(70):
    a_ = random.uniform(0, 2 * math.pi); d_ = random.uniform(9, 160)
    prim('ico_sphere', f'bush_{k}', SCRUB, loc=NS + Vector((math.cos(a_) * d_, math.sin(a_) * d_, 0.2 + 0.0004 * d_ * d_ / 8)), subdivisions=2,
         radius=random.uniform(0.4, 1.4), scale=(1, 1, random.uniform(0.45, 0.8)))
for k in range(9):                                                 # rocks
    a_ = random.uniform(0, 2 * math.pi); d_ = random.uniform(5, 30)
    r_ = prim('ico_sphere', f'rock_{k}', noisy(mat('rk', (0.25, 0.23, 0.21), 0.9), 3.0, 0.3), loc=NS + Vector((math.cos(a_) * d_, math.sin(a_) * d_, 0.1)),
              subdivisions=2, radius=random.uniform(0.3, 0.9), scale=(1, 0.8, 0.5))

# ================================================================ the ball (moves between sets)
BALL = prim('uv_sphere', 'ball', BALL_M, segments=48, ring_count=24, radius=BALL_R); BALL.rotation_mode = 'XYZ'

# ================================================================ light for the day field: a clear midday-ish sun, sky gradient
SUNL = bpy.data.lights.new('sun', 'SUN'); SUNL.energy = 3.4; SUNL.color = (1.0, 0.95, 0.86); SUNL.angle = R(0.8)
SUN_O = bpy.data.objects.new('sun', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_mode = 'QUATERNION'
SUN_O.rotation_quaternion = (-Vector((-0.35, -0.55, 0.9))).to_track_quat('-Z', 'Y')
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Strength'].default_value = 1.0
_tc = wnt.nodes.new('ShaderNodeTexCoord'); _sx = wnt.nodes.new('ShaderNodeSeparateXYZ'); wnt.links.new(_tc.outputs['Generated'], _sx.inputs['Vector'])
SKYR = wnt.nodes.new('ShaderNodeValToRGB'); _el = SKYR.color_ramp.elements
_el[0].position = 0.0; _el[0].color = (0.4, 0.42, 0.4, 1); _el[1].position = 0.8; _el[1].color = (0.1, 0.28, 0.75, 1)
_e2 = _el.new(0.5); _e2.color = (0.8, 0.86, 0.94, 1); _e3 = _el.new(0.57); _e3.color = (0.42, 0.6, 0.92, 1)
_mr = wnt.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = -1.0; _mr.inputs['From Max'].default_value = 1.0
wnt.links.new(_sx.outputs['Z'], _mr.inputs['Value']); wnt.links.new(_mr.outputs['Result'], SKYR.inputs['Fac']); wnt.links.new(SKYR.outputs['Color'], WBG.inputs['Color'])
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.02; CAM.data.clip_end = 9000
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5
def look(cp, ct, lens=35, fstop=8.0, focus=None, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    if up is None: q = d.to_track_quat('-Z', 'Y')
    else:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length

# ================================================================ motion
END = TOTAL
def lerpv(a_, b_, k): return Vector(a_).lerp(Vector(b_), k)
def shake(t, amt, seed=0.0): return Vector((wob(t, 19.0, seed), wob(t, 19.0, seed + 3.3), wob(t, 19.0, seed + 6.1))) * amt
# story clock (minutes into the trip) and speed, shown on screen and used for the cutaway dot
T_CEN = B[4]; T_OUT = B[6] + 0.6
def story_min(t):
    if t < B[2]: return 0.0
    if t < T_CEN: return 19.0 * (t - B[2]) / (T_CEN - B[2])
    if t < B[5]: return 19.0
    return min(TRIP_MIN, 19.0 + 19.0 * (t - B[5]) / (T_OUT - B[5]))
def mph(m_): return VMAX_MPH * math.sin(math.pi * min(m_, TRIP_MIN) / TRIP_MIN)

# ---- day hole: one parabola, apex ZA at t = -TA (frame one) and again at END - TA (the loop)
ZA = 2.4; TA = 0.42
def ball_day(t, at_end=False):
    tau = (t - END + TA) if at_end else (t + TA)
    z = ZA - 0.5 * G * tau * tau; BALL.location = DS + Vector((0, 0, z)); BALL.rotation_euler = (2.2 * tau, 0.6, 0.0); return BALL.location.copy(), -G * tau
CAM0 = DS + Vector((4.4, -6.6, 3.3)); TGT0 = DS + Vector((0, 0, 0.6)); LENS0 = 28.0
def cam_shaft_follow(zb, above=4.6):
    return DS + Vector((0.0, -0.45, zb + above))

# ---- night hole: the same throw, slowed down at the top (beat 7)
ZN = 3.0
def warp(t):
    if t < B[7]: return t
    if t < B[8]: return B[7] + 0.3 * (t - B[7])
    return B[7] + 0.3 * DUR[7] + (t - B[8])
T_AP = B[7] + 0.5 * DUR[7]
def ball_night(t):
    tau = warp(t) - warp(T_AP); z = ZN - 0.5 * G * tau * tau
    BALL.location = NS + Vector((0, 0, z)); BALL.rotation_euler = (2.2 * tau, 0.6, 0.0); return BALL.location.copy()

# ---- tunnel: the walls stream up past a still ball; visual speed follows the real speed curve
VVIS = 420.0                                                       # wall speed (m/s on screen) at the middle of the Earth
def wall_off(t):
    """integral of the on-screen wall speed: beats 2-4 (speeding up to the middle, then the center beat at top speed)"""
    m_ = story_min(t); T1 = T_CEN - B[2]
    if t < B[2]: return 0.0
    if t < T_CEN: return VVIS * T1 / 19.0 * TRIP_MIN / math.pi * (1 - math.cos(math.pi * m_ / TRIP_MIN))
    return VVIS * T1 / 19.0 * TRIP_MIN / math.pi + VVIS * (t - T_CEN)
def tunnel_depth(t):
    if t < B[3]: return 0.0
    if t < B[4]:
        u = (t - B[3]) / DUR[3]                                    # rock, then mantle, then core, on the words
        return 0.45 * smooth(0.25, 0.42, u) + 0.55 * smooth(0.55, 0.78, u)
    return 1.0

def state(t):
    t = clamp(t, 0.0, END - 1e-4); b = beat_at(t)
    BALL.hide_render = False; MELT.hide_render = True
    for c_ in CUTS: c_['boost'] = 0.0
    TUN_IN.scale = (1, 1, 1); TUN_IN['heat'] = 0.0
    for o in SPARKS: o.hide_render = b not in (2, 3, 4)
    if b == 0:                                                       # the drop: the ball falls into the hole, the camera dives in after it
        p, v = ball_day(t)
        k1 = smooth(0.2, 0.9, t); k2 = smooth(0.35, 1.4, t)
        f_ = cam_shaft_follow(p.z)
        cp = Vector((lerp(CAM0.x, f_.x, k1), lerp(CAM0.y, f_.y, k1), lerp(CAM0.z, f_.z, k2)))
        up = lerpv((0, 0, 1), (0, 1, 0), smooth(0.4, 1.0, t)).normalized()
        look(cp, lerpv(TGT0, p, k1), lens=lerp(LENS0, 30.0, k2), fstop=lerp(11.0, 5.6, k2), focus=p, up=up)
    elif b == 1:                                                     # the cutaway: the whole trip, 7,918 miles
        u = (t - B[1]) / DUR[1]; earth_dot(0.0); BALL.location = DS + Vector((0, 0, -2000))
        ang = R(-45 + 10 * u); d_ = lerp(37.0, 31.0, sm(u))
        cp = CS + Vector((math.cos(ang) * d_, math.sin(ang) * d_, d_ * 0.16))
        look(cp, CS + Vector((0, 0, -0.4)), lens=30, fstop=16.0, up=(0, 0, 1))
    elif b in (2, 3, 4):                                             # inside: the walls stream past
        d_ = tunnel_depth(t); off = wall_off(t); tube_set(off, d_)
        BALL.location = TS + shake(t, 0.03, 1.0); BALL.rotation_euler = (7.0 * t, 0.9 * t, 0.3)
        sh = shake(t, 0.025 + 0.035 * d_, 4.0)
        if b == 2:
            u = (t - B[2]) / DUR[2]
            look(TS + Vector((0.32, -0.7, lerp(3.6, 2.6, sm(u)))) + sh, TS, lens=22, fstop=5.6, focus=BALL.location, up=(0, 1, 0))
        elif b == 3:
            u = (t - B[3]) / DUR[3]; ang = R(-60 + 70 * u)
            cp = TS + Vector((math.cos(ang) * 1.05, math.sin(ang) * 1.05, lerp(1.6, 0.9, u))) + sh
            look(cp, TS + Vector((0, 0, -0.5)), lens=16, fstop=4.0, focus=BALL.location, up=(0, 0, 1))
        else:
            u = (t - B[4]) / DUR[4]; ang = R(10 + 25 * u)
            cp = TS + Vector((math.cos(ang) * 1.25, math.sin(ang) * 1.25, -1.6)) + sh          # from below: the ball coming at you, embers streaking past
            look(cp, TS + Vector((0, 0, 0.6)), lens=lerp(16, 19, u), fstop=4.0, focus=BALL.location, up=(0, 0, 1))
    elif b == 5:                                                     # the cutaway again: past the middle, slowing down
        u = (t - B[5]) / DUR[5]; earth_dot(story_min(t)); BALL.location = DS + Vector((0, 0, -2000))
        ang = R(-40 + 14 * u); d_ = lerp(30.0, 27.0, u)
        cp = CS + Vector((math.cos(ang) * d_, math.sin(ang) * d_, d_ * lerp(0.1, -0.12, u)))
        look(cp, CS + Vector((0, 0, lerp(-1.0, -3.5, u))), lens=30, fstop=16.0, up=(0, 0, 1))
    elif b == 6:                                                     # the far side, night: rising up the shaft, out into the stars
        p = ball_night(t)
        zc = min(p.z + 4.2, 1.1); k1 = smooth(B[7] - 0.75, B[7] + 0.25, t)
        f_ = NS + Vector((0.55, -0.85, zc)); end_ = NS + Vector((2.3, -3.3, 0.9))
        cp = lerpv(f_, end_, k1); up = lerpv((0, 1, 0), (0, 0, 1), k1).normalized()
        look(cp, p, lens=lerp(28, 30, k1), fstop=lerp(5.6, 8.0, k1), focus=p, up=up)
    elif b == 7:                                                     # it stops at the top (slow motion)
        p = ball_night(t); u = (t - B[7]) / DUR[7]
        cp = NS + Vector((lerp(2.3, 1.7, sm(u)), lerp(-3.3, -2.7, sm(u)), lerp(0.9, 2.2, sm(u))))
        look(cp, p, lens=lerp(30, 38, sm(u)), fstop=8.0, focus=p, up=(0, 0, 1))
    elif b == 8:                                                     # and falls all the way back
        p = ball_night(t); u = (t - B[8]) / DUR[8]; k = sm(u)
        cp = NS + Vector((lerp(1.7, 0.35, k), lerp(-2.7, -0.9, k), lerp(2.2, 5.0, k)))
        look(cp, p, lens=lerp(38, 30, k), fstop=8.0, focus=p, up=lerpv((0, 0, 1), (0, 1, 0), k).normalized())
    elif b == 9:                                                     # the core is as hot as the Sun: the middle of the hole melts shut
        u = (t - B[9]) / DUR[9]; BALL.location = DS + Vector((0, 0, -2000)); DOT.hide_render = True; TRAIL.hide_render = True
        mk = smooth(0.45, 0.85, u); TUN_IN.scale = (max(1 - mk, 0.02), max(1 - mk, 0.02), 1); TUN_IN['heat'] = smooth(0.1, 0.45, u) * (1 - 0.7 * mk)
        for c_ in CUTS: c_['boost'] = 0.3 * smooth(0.15, 0.6, u)
        ang = R(-40 - 8 * u); d_ = lerp(31.0, 21.0, sm(u))
        cp = CS + Vector((math.cos(ang) * d_, math.sin(ang) * d_, d_ * 0.12))
        look(cp, CS + Vector((0, 0, 0)), lens=lerp(30, 32, u), fstop=16.0, up=(0, 0, 1))
    else:                                                            # back home: up out of the first hole and into frame one (the loop)
        p, v = ball_day(t, at_end=True)
        k1 = smooth(END - 1.55, END - 0.12, t)
        f_ = cam_shaft_follow(p.z, 4.2); f_.z = min(f_.z, 1.0)
        cp = lerpv(f_, CAM0, k1); up = lerpv((0, 1, 0), (0, 0, 1), smooth(END - 1.55, END - 0.7, t)).normalized()
        look(cp, lerpv(p, TGT0, k1), lens=lerp(30.0, LENS0, k1), fstop=lerp(5.6, 11.0, k1), focus=p, up=up)
    if b not in (9,):
        DOT.hide_render = b not in (1, 5)
        if b not in (1, 5): TRAIL.hide_render = True

bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
ANIM = [CAM, BALL, DOT, TRAIL]
def frame(f):
    t = f / FPS; d = 0.25 / FPS
    for o in ANIM + [TUBE, TRINGS] + SPARKS: o.animation_data_clear()
    if beat_at(max(0.0, t - d)) == beat_at(min(END - 1e-4, t + d)) == beat_at(t):
        base = 0.0
        if beat_at(t) in (2, 3, 4): base = math.floor(wall_off(t) / RING_P) * RING_P; sb = spark_bases(0.15 * wall_off(t))   # wrap by whole steps, same for both keys
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            state(tt_)
            if beat_at(t) in (2, 3, 4): tube_set(wall_off(tt_) - base - 200.0, tunnel_depth(tt_)); sparks_set(0.15 * wall_off(tt_), tunnel_depth(tt_), sb)
            for o in ANIM + ([TUBE, TRINGS] + SPARKS if beat_at(t) in (2, 3, 4) else []):
                o.keyframe_insert('location', frame=kf)
                o.keyframe_insert('rotation_quaternion' if o.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=kf)
                if o is TRAIL: o.keyframe_insert('scale', frame=kf)
    S.frame_set(f); state(t)
    if beat_at(t) in (2, 3, 4):
        base = math.floor(wall_off(t) / RING_P) * RING_P; tube_set(wall_off(t) - base - 200.0, tunnel_depth(t)); sparks_set(0.15 * wall_off(t), tunnel_depth(t))
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

