# Sucked into a tornado, built and rendered in Blender (Cycles): a man by a trailer on open prairie gets lifted into a tornado;
# the funnel (a twisting see-through shell with rain bands), the inflow (glowing air streams spiralling in along the ground and up
# the core), debris (boards, shingles, rocks, glass) flying around him in slow motion, a 200+ mph readout, the 2006 Matt Suter case
# (pulled from a trailer, carried 1,307 ft: a top-down map with the path), what to do (lowest room, no windows, cover your head).
#   python3 torn.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]      (stride.json / redo.json beside it: see ../ele/ele.py)
# Needs man.blend (../foot/man_build.py) beside it or in /root/vt/n42/torn.
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
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n42/torn', n), os.path.join('/root/vt/n42/cramp', n)) if os.path.exists(p_))
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
# ================================================================ OPEN PRAIRIE under a storm (z up, metres). The trailer sits at the origin,
# the tornado comes in from +y. Grass ground, a fence line, power poles, far tree line; a green-grey sky with a dark storm base overhead
def grass_mat():
    m = mat('grass', (0.2, 0.26, 0.1), 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.08; nz.inputs['Detail'].default_value = 8; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 6.0; nz2.inputs['Detail'].default_value = 4; nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.11, 0.13, 0.05, 1); cr.color_ramp.elements[1].color = (0.32, 0.33, 0.14, 1)
    nt.links.new(math_(nt, 'ADD', nz.outputs['Fac'], math_(nt, 'MULTIPLY', nz2.outputs['Fac'], 0.35)), cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5; nt.links.new(nz2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
GROUND = prim('plane', 'ground', grass_mat(), size=4000)
# grass tufts near the action (one mesh): thin bent blades that lean with the wind ('wind' prop drives a shader-free lean via shape key)
def tufts(name, n, area, seed, m):
    rr = random.Random(seed); vs, fs = [], []; lean = []
    for i in range(n):
        cx, cy = rr.uniform(area[0], area[1]), rr.uniform(area[2], area[3])
        for b_ in range(5):
            a_ = rr.uniform(0, 2 * math.pi); h = rr.uniform(0.18, 0.5); w = 0.012; x0, y0 = cx + 0.04 * math.cos(a_), cy + 0.04 * math.sin(a_)
            dx, dy = -math.sin(a_) * w, math.cos(a_) * w; k = len(vs)
            vs += [(x0 - dx, y0 - dy, 0), (x0 + dx, y0 + dy, 0), (x0 + 0.3 * h * math.cos(a_), y0 + 0.3 * h * math.sin(a_), h)]; fs.append((k, k + 1, k + 2))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); o = obj(name, me, m)
    sk0 = o.shape_key_add(name='basis'); sk = o.shape_key_add(name='wind')
    for i, v in enumerate(o.data.vertices):
        z = v.co.z
        if z > 0: sk.data[i].co = v.co + Vector((-0.25 * z, -0.6 * z, -0.35 * z))
    return o
TUFT_M = mat('tuft', (0.3, 0.32, 0.12), 0.8); TUFT_M.node_tree.nodes['Principled BSDF'].inputs['Subsurface Weight'].default_value = 0.2
TUFTS = tufts('tufts', 2600, (-14, 14, -16, 10), 3, TUFT_M)
# fence and power poles (wood), wires
WOOD_M = noisy(mat('wood', (0.3, 0.22, 0.14), 0.8), 30, 0.3); WIRE_M = mat('wire', (0.05, 0.05, 0.05), 0.4)
FENCE = []
for i in range(30):
    x = -30 + i * 3.0; FENCE.append(box('post%d' % i, (0.1, 0.1, 1.3), (x, -24.0 + 0.05 * math.sin(i), 0.65), WOOD_M, rot=(0, 0, R(3 * math.sin(i * 1.7)))))
for z in (0.5, 0.9, 1.2): FENCE.append(box('rail%.1f' % z, (90, 0.015, 0.015), (15, -24.0, z), WIRE_M))
POLES = []
for i in range(8):
    x = -60 + i * 35; POLES.append(box('pole%d' % i, (0.28, 0.28, 10), (x, 18, 5), WOOD_M)); POLES.append(box('arm%d' % i, (0.15, 2.2, 0.15), (x, 18, 9.3), WOOD_M))
for i in range(7):
    for dy in (-0.9, 0.9):
        x0, x1 = -60 + i * 35, -60 + (i + 1) * 35; pts = [Vector((x0 + (x1 - x0) * k / 12, 18 + dy, 9.4 - 1.2 * math.sin(math.pi * k / 12))) for k in range(13)]
        POLES.append(tube('wire%d%d' % (i, dy > 0), pts, 0.012, WIRE_M, seg=5))
# far tree line: lumpy dark shapes on the horizon
TREE_M = mat('trees', (0.05, 0.07, 0.04), 0.9); TREES = []
_tr = random.Random(8)
for i in range(70):
    a_ = _tr.uniform(-math.pi, math.pi); d = _tr.uniform(640, 820); x, y = d * math.cos(a_), d * math.sin(a_)
    TREES.append(prim('ico_sphere', 'tree%d' % i, TREE_M, loc=(x, y, _tr.uniform(5, 9)), subdivisions=2, radius=_tr.uniform(8, 16), scale=(1.4, 1.4, _tr.uniform(0.7, 1.1))))
# the trailer (mobile home): long box on skirting, siding lines, windows (warm light inside), a door with steps, a satellite dish
TR = V3(0.0, 0.0, 0.0); TRL, TRW, TRH = 14.0, 4.2, 2.6
SIDING = noisy(mat('siding', (0.78, 0.76, 0.68), 0.6), 3.0, 0.12)
_st = SIDING.node_tree; _wv = _st.nodes.new('ShaderNodeTexWave'); _wv.wave_type = 'BANDS'; _wv.bands_direction = 'Z'; _wv.inputs['Scale'].default_value = 8.0
_tc = _st.nodes.new('ShaderNodeTexCoord'); _st.links.new(_tc.outputs['Object'], _wv.inputs['Vector'])
_bp = _st.nodes.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.3; _st.links.new(_wv.outputs['Fac'], _bp.inputs['Height']); _st.links.new(_bp.outputs['Normal'], _st.nodes['Principled BSDF'].inputs['Normal'])
TRAILER = [box('trailer', (TRL, TRW, TRH), TR + V3(0, 0, 0.75 + TRH / 2), SIDING, 0.04),
           box('skirt', (TRL - 0.2, TRW - 0.2, 0.75), TR + V3(0, 0, 0.375), mat('skirt', (0.5, 0.48, 0.44), 0.7)),
           box('roof', (TRL + 0.2, TRW + 0.3, 0.12), TR + V3(0, 0, 0.75 + TRH + 0.05), mat('roof', (0.6, 0.6, 0.6), 0.4, metal=0.6), 0.02)]
WIN_GLOW = emis('trailer_window', (1.0, 0.75, 0.42), 6.0)
for i, x in enumerate((-5.0, -2.0, 2.5, 5.2)):
    TRAILER.append(box('twin%d' % i, (1.0, 0.03, 0.8), TR + V3(x, -TRW / 2 - 0.01, 2.2), WIN_GLOW))
    TRAILER.append(box('twinf%d' % i, (1.1, 0.04, 0.9), TR + V3(x, -TRW / 2 - 0.005, 2.2), mat('trim', (0.9, 0.9, 0.88), 0.5)))
TRAILER.append(box('door', (0.9, 0.04, 2.0), TR + V3(0.4, -TRW / 2 - 0.02, 1.75), mat('door', (0.55, 0.52, 0.48), 0.5)))
TRAILER.append(box('steps', (1.2, 0.9, 0.6), TR + V3(0.4, -TRW / 2 - 0.5, 0.3), WOOD_M))
# the sky: a dome with storm clouds (noise), green-grey, darker overhead; low cloud base
def sky_mat():
    m = bpy.data.materials.new('sky'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 0.02), nz.inputs['W'])
    up = math_(nt, 'MAXIMUM', sx.outputs['Z'], 0.0)
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.035, 0.05, 0.045, 1); cr.color_ramp.elements[1].color = (0.28, 0.34, 0.3, 1)
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[1].position = 0.75
    nt.links.new(math_(nt, 'SUBTRACT', nz.outputs['Fac'], math_(nt, 'MULTIPLY', up, 0.45)), cr.inputs['Fac'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cr.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
SKY = prim('uv_sphere', 'sky', sky_mat(), segments=64, ring_count=32, radius=900); SKY['tt'] = 0.0
for p_ in SKY.data.polygons: p_.use_smooth = True
SKY.visible_shadow = False
# ---- the TORNADO at TC (moves): a funnel shell that twists (bands in the shader run around it), a dusty debris cloud at its foot
TC0 = V3(10.0, 160.0, 0.0)
def funnel_mat():
    m = bpy.data.materials.new('funnel'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    ang = math_(nt, 'ARCTAN2', sx.outputs['Y'], sx.outputs['X'])
    twist = math_(nt, 'ADD', ang, math_(nt, 'ADD', math_(nt, 'MULTIPLY', sx.outputs['Z'], 0.02), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 3.0)))
    cxyz = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', twist, 1.6), cxyz.inputs['X']); nt.links.new(math_(nt, 'MULTIPLY', sx.outputs['Z'], 0.03), cxyz.inputs['Y'])
    nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 0.3), cxyz.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.65
    nt.links.new(cxyz.outputs['Vector'], nz.inputs['Vector'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    dens = math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 0.3), math_(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 1.1, 0.35))
    dens = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', dens, objattr(nt, 'dens')), 0.0), 1.0)
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.025, 0.028, 0.026, 1); cr.color_ramp.elements[1].color = (0.2, 0.19, 0.17, 1)
    nt.links.new(nz.outputs['Fac'], cr.inputs['Fac'])
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(cr.outputs['Color'], df.inputs['Color'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cr.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 0.25
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(df.outputs['BSDF'], ad.inputs[0]); nt.links.new(em.outputs['Emission'], ad.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(dens, mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(ad.outputs['Shader'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
FUN_M = funnel_mat()
def funnel_mesh(name, prof, seg=96):
    vs, fs = [], []; n = len(prof)
    for z, r in prof:
        for k in range(seg): a_ = 2 * math.pi * k / seg; vs.append((r * math.cos(a_), r * math.sin(a_), z))
    for i in range(n - 1):
        for k in range(seg): a0 = i * seg + k; a1 = i * seg + (k + 1) % seg; fs.append((a0, a1, a1 + seg, a0 + seg))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    return me
_prof = [(z, 22 + 0.00012 * z * z + 6 * math.sin(z * 0.02)) for z in np.linspace(0, 560, 60)] + [(600, 300), (640, 600)]
FUNNEL = obj('funnel', funnel_mesh('funnel', _prof), FUN_M, loc=TC0); FUNNEL['tt'] = 0.0; FUNNEL['dens'] = 1.0; FUNNEL.visible_shadow = False
FUN2 = obj('funnel_outer', funnel_mesh('funnel_outer', [(z, r * 1.45 + 8) for z, r in _prof[:-2]]), FUN_M, loc=TC0); FUN2['tt'] = 0.0; FUN2['dens'] = 0.45; FUN2.visible_shadow = False
WALLCLOUD = prim('cylinder', 'wallcloud', mat('wallcloud', (0.06, 0.07, 0.065), 0.9), loc=TC0 + V3(0, 0, 560), vertices=96, radius=700, depth=60)
for v in WALLCLOUD.data.vertices: v.co.z += mnoise.noise(v.co * 0.008) * 25
SUNL = bpy.data.lights.new('storm_sun', 'SUN'); SUNL.energy = 1.6; SUNL.color = (0.75, 0.85, 0.8); SUNL.angle = R(25)
SUN_O = bpy.data.objects.new('storm_sun', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_euler = (R(50), R(-20), R(200))
RIMO = light_at('rim', 'AREA', (-14, 26, 9), (0, 0, 3), 4000, (0.8, 0.9, 1.0), 6.0)
FLASH = light_at('lightning', 'AREA', (60, 120, 300), (0, 0, 0), 0.0, (0.75, 0.82, 1.0), 40.0)
KEYF = light_at('front_key', 'AREA', (-2.0, -13.0, 4.0), (2.6, -4.6, 1.4), 900, (0.85, 0.92, 1.0), 4.0)
OUT_L = [SUN_O, RIMO, FLASH, KEYF]
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.04, 0.05, 0.045, 1); WBG.inputs['Strength'].default_value = 1.0
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.05; CAM.data.clip_end = 3000
S.view_settings.view_transform = 'AgX'
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
retint(SHORTS_M, (0.2, 0.25, 0.36), 0.35, 0.95, 0.6)                 # navy pants
retint(SHIRT_M, (0.62, 0.2, 0.16), 0.35, 0.9, 0.5)                   # the same brick-red tee (the channel's guy)
# ================================================================ DEBRIS: one mesh of many pieces (boards, shingles, rocks, glass), each moved
# and turned by numpy every frame. swirl(centre, ...) puts them on a spinning, rising cloud around a point (the funnel or the man)
class Swarm:
    KINDS = {'board': ((1.6, 0.14, 0.035), 0), 'shingle': ((0.33, 0.25, 0.01), 1), 'rock': ((0.08, 0.07, 0.06), 2), 'glass': ((0.22, 0.16, 0.006), 3), 'dust': ((0.05, 0.05, 0.05), 2)}
    def __init__(self, name, mix, seed, mats):
        rr = np.random.default_rng(seed); parts = []
        for k, n in mix:
            for _ in range(n): parts.append(k)
        self.n = len(parts); V, F, MI = [], [], []; self.local = []
        for i, k in enumerate(parts):
            (sx, sy, sz), mi = self.KINDS[k]; s = rr.uniform(0.6, 1.3)
            if k in ('rock', 'dust'):
                bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); pts = np.array([v.co[:] for v in bm.verts]) * np.array([sx, sy, sz]) * s * rr.uniform(0.7, 1.3, (1, 3))
                fs = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
            elif k == 'glass':
                pts = np.array([[0, 0, 0], [sx, rr.uniform(-0.3, 0.3) * sy, 0], [rr.uniform(0.2, 0.8) * sx, sy, 0], [0, 0, sz], [sx, 0, sz], [0.5 * sx, sy, sz]]) * s; pts -= pts.mean(0)
                fs = [[0, 1, 2], [3, 5, 4], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]]
            else:
                x, y, z = sx * s / 2, sy * s / 2, sz / 2; pts = np.array([[a, b, c] for a in (-x, x) for b in (-y, y) for c in (-z, z)])
                fs = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
            b0 = sum(len(p) for p in self.local); self.local.append(pts); F += [[b0 + j for j in f] for f in fs]; MI += [mi] * len(fs)
        self.counts = [len(p) for p in self.local]; self.L = np.concatenate(self.local)
        self.owner = np.repeat(np.arange(self.n), self.counts)
        me = bpy.data.meshes.new(name); me.from_pydata(self.L.tolist(), [], F); me.update()
        for m_ in mats: me.materials.append(m_)
        me.polygons.foreach_set('material_index', MI); me.update()
        self.o = obj(name, me); self.o.visible_shadow = True
        self.rad = rr.uniform(0.3, 1.0, self.n); self.ph = rr.uniform(0, 2 * math.pi, self.n); self.hz = rr.uniform(0, 1, self.n)
        self.spin = rr.normal(size=(self.n, 3)) * 3.0; self.sp = rr.uniform(0.7, 1.3, self.n)
    def set(self, P, ang):
        """P: (n,3) centres; ang: (n,3) euler angles"""
        cx, cy, cz = np.cos(ang).T; sx, sy, sz = np.sin(ang).T
        Rm = np.empty((self.n, 3, 3))
        Rm[:, 0, 0] = cy * cz; Rm[:, 0, 1] = sx * sy * cz - cx * sz; Rm[:, 0, 2] = cx * sy * cz + sx * sz
        Rm[:, 1, 0] = cy * sz; Rm[:, 1, 1] = sx * sy * sz + cx * cz; Rm[:, 1, 2] = cx * sy * sz - sx * cz
        Rm[:, 2, 0] = -sy; Rm[:, 2, 1] = sx * cy; Rm[:, 2, 2] = cx * cy
        W = np.einsum('vij,vj->vi', Rm[self.owner], self.L) + P[self.owner]
        self.o.data.vertices.foreach_set('co', W.reshape(-1).astype(np.float32)); self.o.data.update()
    def swirl(self, c, t, r0, r1, h, w, slow=1.0, inward=0.0, lift=0.0):
        """a spinning cloud around c: radius r0..r1, height 0..h, turning w rad/s (inner faster); slow = time scale (slow motion)"""
        r = r0 + (r1 - r0) * self.rad; r = r * (1 - inward * 0.5)
        a = self.ph + t * slow * w * self.sp * (r1 / np.maximum(r, 0.1)) ** 0.5
        z = (self.hz * h + t * slow * lift * self.sp) % max(h, 1e-3)
        P = np.stack([c.x + r * np.cos(a), c.y + r * np.sin(a), c.z + z], 1); self.set(P, self.spin * t * slow); return P
WOODD_M = noisy(mat('debris_wood', (0.4, 0.3, 0.2), 0.8), 20, 0.4); SHING_M = noisy(mat('shingle', (0.15, 0.14, 0.14), 0.9), 40, 0.3)
ROCK_M = noisy(mat('rock', (0.28, 0.25, 0.22), 0.9), 60, 0.4); GLASS_M = mat('glassd', (0.85, 0.95, 1.0), 0.02, trans=1.0, ior=1.5)
DEB_MATS = [WOODD_M, SHING_M, ROCK_M, GLASS_M]
NEAR = Swarm('debris_near', [('board', 14), ('shingle', 40), ('rock', 70), ('glass', 30)], 1, DEB_MATS)        # around him, close up
FAR = Swarm('debris_far', [('board', 60), ('shingle', 160), ('dust', 900)], 2, DEB_MATS)                       # around the funnel
DUSTC = prim('cylinder', 'dust_cloud', None, loc=TC0, vertices=64, radius=60, depth=40)
DUSTC.data.materials.append(FUN_M); DUSTC['tt'] = 0.0; DUSTC['dens'] = 0.8; DUSTC.visible_shadow = False
for v in DUSTC.data.vertices: v.co.z += 20; v.co *= Vector((1, 1, 1)) * (1 + 0.15 * mnoise.noise(v.co * 0.05))
# ---- INFLOW: glowing air streams that spiral in along the ground and climb the core ('arc' bands run along them)
def stream_mat():
    m = bpy.data.materials.new('stream'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'
    ph = math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', arc.outputs['Fac'], 0.025), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), objattr(nt, 'speed')))
    band = math_(nt, 'POWER', math_(nt, 'MULTIPLY_ADD', math_(nt, 'SINE', math_(nt, 'MULTIPLY', ph, 6.2832)), 0.5, 0.5), 4.0)
    show = math_(nt, 'LESS_THAN', arc.outputs['Fac'], objattr(nt, 'reach'))
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.45, 0.85, 1.0, 1)
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY_ADD', band, 14.0, 1.5), show), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY', show, math_(nt, 'MULTIPLY_ADD', band, 0.6, 0.35)), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
STR_M = stream_mat()
def stream_lines(n=14):
    vs, fs, av = [], [], []; SEG = 6
    for j in range(n):
        a0 = 2 * math.pi * j / n; pts = []
        for k in range(260):
            s = k / 259
            if s < 0.6: u = s / 0.6; r = 260 * (1 - u) ** 1.6 + 26; a = a0 + 9.0 * u ** 1.8; z = 2 + 6 * u
            else: u = (s - 0.6) / 0.4; r = 26 * (1 - 0.35 * u); a = a0 + 9.0 + 14 * u; z = 8 + 520 * u ** 1.2
            pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
        arc = [0.0]
        for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
        base = len(vs); up = Vector((0, 0, 1))
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized(); x = d.cross(up)
            x = x.normalized() if x.length > 1e-4 else Vector((1, 0, 0)); y = d.cross(x); rw = 0.9 + 1.5 * (i / len(pts))
            for q in range(SEG): aa = 2 * math.pi * q / SEG; vs.append(tuple(p + (x * math.cos(aa) + y * math.sin(aa)) * rw)); av.append(arc[i])
        for i in range(len(pts) - 1):
            for q in range(SEG): a_ = base + i * SEG + q; b_ = base + i * SEG + (q + 1) % SEG; fs.append((a_, b_, b_ + SEG, a_ + SEG))
    me = bpy.data.meshes.new('streams'); me.from_pydata(vs, [], fs); me.update(); at = me.attributes.new('arc', 'FLOAT', 'POINT'); at.data.foreach_set('value', av)
    o = obj('streams', me, STR_M, loc=TC0); o['tt'] = 0.0; o['speed'] = 1.2; o['reach'] = 0.0; o.visible_shadow = False; return o
STREAMS = stream_lines()
# ---- the SHELTER: a small interior closet (no windows), one bare bulb that swings, towels on a shelf, a door ajar
CL = V3(300.0, 0.0, 0.0)
CLOSET = [box('cl_floor', (1.6, 1.6, 0.05), CL + V3(0, 0, -0.025), noisy(mat('cl_floor', (0.35, 0.27, 0.2), 0.6), 20, 0.3))]
CW_M = noisy(mat('cl_wall', (0.62, 0.6, 0.55), 0.85), 4, 0.08)
for nm, sz, lc in (('cl_wl', (0.05, 1.6, 2.4), V3(-0.8, 0, 1.2)), ('cl_wr', (0.05, 1.6, 2.4), V3(0.8, 0, 1.2)), ('cl_wb', (1.6, 0.05, 2.4), V3(0, 0.8, 1.2)), ('cl_ceil', (1.6, 1.6, 0.05), V3(0, 0, 2.42))):
    CLOSET.append(box(nm, sz, CL + lc, CW_M))
CLOSET.append(box('cl_shelf', (1.5, 0.4, 0.03), CL + V3(0, 0.6, 1.75), WOOD_M))
for i in range(4): CLOSET.append(box('towel%d' % i, (0.32, 0.36, 0.12), CL + V3(-0.55 + i * 0.36, 0.6, 1.83), mat('towel%d' % i, [(0.7, 0.3, 0.25), (0.25, 0.4, 0.6), (0.85, 0.82, 0.7), (0.4, 0.55, 0.35)][i], 0.95, sheen=0.6)))
BULB = empty('bulb_pivot', loc=CL + V3(0, 0, 2.4))
prim('cylinder', 'bulb_cord', mat('cord', (0.05, 0.05, 0.05), 0.5), BULB, loc=(0, 0, -0.15), vertices=8, radius=0.004, depth=0.3)
prim('uv_sphere', 'bulb_glass', emis('bulb_e', (1.0, 0.78, 0.5), 40.0), BULB, loc=(0, 0, -0.33), segments=16, ring_count=8, radius=0.04)
BLT = bpy.data.lights.new('bulb_light', 'POINT'); BLT.energy = 260; BLT.color = (1.0, 0.78, 0.5); BLT.shadow_soft_size = 0.04
BLO = bpy.data.objects.new('bulb_light', BLT); S.collection.objects.link(BLO); BLO.parent = BULB; BLO.location = (0, 0, -0.33)
CLOSET += [BULB, BLO] + [o for o in bpy.data.objects if o.parent == BULB]
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

# ---- keeping him out of the floor and his hand out of his side (measured on the posed skin, every frame)
def body_eval():
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); rp = rp.reshape(-1, 3); oe.to_mesh_clear()
    M_ = np.array(BODY.matrix_world); return co @ M_[:3, :3].T + M_[:3, 3], rp
def suit_bvh():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles(); M = SUIT.matrix_world
    T_ = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles]); oe.to_mesh_clear(); return T_
def suit_minz():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); oe.to_mesh_clear(); M_ = np.array(SUIT.matrix_world)
    return float((co @ M_[:3, :3].T + M_[:3, 3])[:, 2].min())
def ground(kneel=0.0, passes=4):
    """feet: each ankle goes up or down until that foot just touches the floor. knees: the hips rise if a knee is under the floor,
    and (kneeling) sink until the knees rest on it"""
    for _ in range(passes):
        W, RP = body_eval(); moved = 0.0
        for s_, sg in (('R', -1.0), ('L', 1.0)):
            mn = float(W[(RP[:, 2] < 0.1) & (RP[:, 0] * sg > 0), 2].min()); d = clamp(0.001 - mn, -0.03, 0.03)
            if abs(d) > 0.0004: TGT['ank' + s_].location.z += d; moved = max(moved, abs(d))
        m_ = (RP[:, 2] > 0.25) & (RP[:, 2] < 0.75); kn = min(float(W[m_, 2].min()) if m_.any() else 9.0, suit_minz())      # knees: skin below the shorts, and the shorts
        d = (0.001 - kn) if (kn < 0.001 or kneel > 0.97) else 0.0; d = clamp(d, -0.03, 0.03)
        if abs(d) > 0.0004: RIG.location.z += d; moved = max(moved, abs(d))
        if moved < 0.0005: break
        bpy.context.view_layer.update()
HO_LOG = []
# feet: turned in the world (flat on the floor, or tipped up onto the toes by 'phi'), whatever the shin does
FOOT = {}
for s_ in ('R', 'L'):
    e_ = empty('tgt_foot' + s_); e_.rotation_mode = 'QUATERNION'
    c_ = PB['foot.' + s_].constraints.new('COPY_ROTATION'); c_.target = e_; c_.owner_space = c_.target_space = 'WORLD'
    FOOT[s_] = (e_, RB['foot.' + s_].matrix_local.to_3x3(), c_)
def feet_flat(on=True, phi=0.0):
    for s_ in 'RL':
        e_, M0, c_ = FOOT[s_]; c_.influence = 1.0 if on else 0.0; e_.rotation_quaternion = (Matrix.Rotation(R(phi), 3, 'X') @ M0).to_quaternion()
# ================================================================ HIS POSES (all built from the hip, a body turn, and hands/feet in his own frame)
def rigM(hip, rot):
    Rm = Euler(tuple(R(x) for x in rot)).to_matrix(); return Matrix.Translation(Vector(hip) - Rm @ HIP0) @ Rm.to_4x4()
def body(hip, rot, ankR, ankL, handR, handL, space='rig', neck=0.0, head=0.0, jaw=0.0, lids=0.0, curl=(0.3, 0.3), pk=(1.0, 1.0),
         palm=None, spine=0.0, kneel_pole=False):
    """space: 'rig' = ankles/hands in his own (rest) frame, moving with him; 'world' for ankles (planted)"""
    M = rigM(hip, rot); M3 = M.to_3x3()
    aR = M @ Vector(ankR) if space == 'rig' else Vector(ankR); aL = M @ Vector(ankL) if space == 'rig' else Vector(ankL)
    kp = V3(0, -2.0, 0.4) if not kneel_pole else V3(0, -2.0, -0.6)
    set_pose(hip, rot, spine, neck, head, 0.0, 0.0, ankR=aR, poleR=M @ (V3(-0.15, 0, 0.5) + kp), ankL=aL, poleL=M @ (V3(0.15, 0, 0.5) + kp),
             curlR=curl[0], curlL=curl[1], lids=lids, jaw=jaw, poleArmR=M @ V3(-0.8, 0.6 * pk[0], 1.0), poleArmL=M @ V3(0.8, 0.6 * pk[1], 1.0))
    for s_, hp_ in (('R', handR), ('L', handL)):
        if palm and s_ in palm:
            c_, fd, pd = palm[s_]; place_hand(s_, M @ Vector(c_), M3 @ Vector(fd), M3 @ Vector(pd), 1.0)
        else: TGT['hand' + s_].location = M @ Vector(hp_); HAND[s_][2].influence = 0.0
    bpy.context.view_layer.update(); return M
def flail(t, k=1.0, seed=0.0):
    """limbs thrown about by the wind (rig space)"""
    w = lambda f, s_: wob(t, f, seed + s_) * k
    return dict(ankR=V3(-0.2 + 0.12 * w(1.3, 1), 0.15 + 0.25 * w(1.1, 2), 0.12 + 0.18 * w(0.9, 3)), ankL=V3(0.26 + 0.12 * w(1.2, 4), -0.12 + 0.3 * w(1.0, 5), 0.2 + 0.2 * w(0.8, 6)),
                handR=V3(-0.68 + 0.12 * w(1.5, 7), 0.12 + 0.3 * w(1.2, 8), 1.45 + 0.2 * w(1.0, 9)), handL=V3(0.62 + 0.12 * w(1.4, 10), 0.25 + 0.3 * w(1.3, 11), 1.25 + 0.25 * w(0.9, 12)))
STAND_HIP = 0.93
def stand(x, y, yaw, t, brace=0.0, lift=0.0):
    """on his feet by the trailer, facing yaw (deg); brace: knees bend, arms come up over his face; lift: heels leave the ground"""
    hip = V3(x, y, STAND_HIP - 0.12 * brace + lift); rot = (6 * brace + 3 * wob(t, 2, 1) * brace, 0, yaw)
    Rz = Matrix.Rotation(R(yaw), 3, 'Z'); aR = V3(x, y, 0) + Rz @ V3(-0.14, 0.02, 0.09 + lift * 0.9); aL = V3(x, y, 0) + Rz @ V3(0.14, 0.02, 0.09 + lift * 0.9)
    hR = V3(-0.28, 0.02, 0.86).lerp(V3(-0.1, -0.32, 1.62), brace); hL = V3(0.28, 0.02, 0.86).lerp(V3(0.12, -0.33, 1.6), brace)
    Rq = Matrix.Rotation(R(yaw), 3, 'Z')
    for s_ in 'RL': FOOT[s_][2].influence = 1.0; FOOT[s_][0].rotation_quaternion = (Rq @ FOOT[s_][1]).to_quaternion()
    body(hip, rot, aR, aL, hR, hL, space='world', neck=8 * brace, jaw=0.3 * brace, lids=0.5 * brace, curl=(0.3 + 0.5 * brace,) * 2)
    if lift < 0.01: ground(0.0)
def airborne(hip, rot, t, k=1.0, seed=0.0, jaw=0.6):
    feet_flat(False)
    f = flail(t, k, seed); body(hip, rot, f['ankR'], f['ankL'], f['handR'], f['handL'], neck=15 * wob(t, 1, seed), head=10 * wob(t, 1.3, seed), jaw=jaw, lids=0.6, curl=(0.6, 0.6), pk=(-1, -1))
def lying(x, y, sit, t):
    """on his back in the grass, head toward +y; sit 0..1: pushes up on his hands to sitting"""
    feet_flat(False); a = lerp(-88, -35, sm(sit)); hip = V3(x, y, 0.12 + 0.02 * sit); rot = (a, 0, 180)
    M = rigM(hip, rot)
    aR, aL = V3(-0.16, 0.05, 0.1), V3(0.2, 0.0, 0.12)
    hR = V3(-0.4, 0.15, 0.95).lerp(V3(-0.3, 0.32, 0.85), sit); hL = V3(0.42, 0.1, 0.9).lerp(V3(0.3, 0.32, 0.85), sit)
    body(hip, rot, aR, aL, hR, hL, neck=lerp(-5, 15, sit), head=lerp(0, 10, sit), lids=lerp(1.0, 0.1, smooth(0.0, 0.5, sit)), jaw=0.2, curl=(0.5, 0.5), kneel_pole=False)
    W, RP = body_eval(); mn = float(W[:, 2].min()); RIG.location.z += 0.002 - mn; bpy.context.view_layer.update()
def crouch(t, shake_=0.0):
    """in the closet: down on his knees and folded forward, both hands locked over the back of his head"""
    feet_flat(False); hip = CL + V3(0.0, -0.05, 0.42); rot = (68 + 2 * wob(t, 6, 3) * shake_, 0, 0)
    M = rigM(hip, rot); Mi = M.inverted()
    aR = Mi @ (CL + V3(-0.13, 0.32, 0.07)); aL = Mi @ (CL + V3(0.13, 0.32, 0.07))
    body(hip, rot, aR, aL, V3(-0.06, 0.15, 1.6), V3(0.06, 0.15, 1.62), neck=30, head=12, lids=1.0, jaw=0.1, curl=(0.15, 0.15),
         palm={'R': (V3(-0.03, 0.09, 1.71), V3(1, 0.2, -0.2), V3(0, -0.3, -1)), 'L': (V3(0.03, 0.09, 1.71), V3(-1, 0.2, -0.2), V3(0, -0.3, -1))}, kneel_pole=True)
    ground(1.0)
# ================================================================ THE MAP (2006): his trailer, the path the tornado carried him (398 m = 1,307 ft,
# a glowing dashed arc that draws itself), where he landed
LAND = TR + V3(240.0, 318.0, 0.0)                                       # 398 m from the trailer
def path_mat():
    m = bpy.data.materials.new('path'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'
    dash = math_(nt, 'LESS_THAN', math_(nt, 'FRACT', math_(nt, 'MULTIPLY', arc.outputs['Fac'], 0.06)), 0.6)
    show = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', arc.outputs['Fac'], objattr(nt, 'reach')), dash)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.82, 0.25, 1); em.inputs['Strength'].default_value = 25.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(show, mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
def path_obj():
    pts = []
    for k in range(200):
        s = k / 199; p = TR.lerp(LAND, s) + V3(0, 0, 60 * math.sin(math.pi * s) + 1.0); p += V3(-25 * math.sin(math.pi * s), 15 * math.sin(2 * math.pi * s), 0); pts.append(p)
    vs, fs, av = [], [], []; SEG = 8; arc = [0.0]
    for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized(); x = d.cross(V3(0, 0, 1)).normalized(); y = d.cross(x)
        for q in range(SEG): aa = 2 * math.pi * q / SEG; vs.append(tuple(p + (x * math.cos(aa) + y * math.sin(aa)) * 2.2)); av.append(arc[i])
    for i in range(len(pts) - 1):
        for q in range(SEG): a_ = i * SEG + q; b_ = i * SEG + (q + 1) % SEG; fs.append((a_, b_, b_ + SEG, a_ + SEG))
    me = bpy.data.meshes.new('path'); me.from_pydata(vs, [], fs); me.update(); at = me.attributes.new('arc', 'FLOAT', 'POINT'); at.data.foreach_set('value', av)
    o = obj('path', me, path_mat()); o['reach'] = 0.0; o.visible_shadow = False; return o, pts, arc
PATH, PATH_PTS, PATH_ARC = path_obj()
PIN0 = prim('cylinder', 'pin_start', emis('pin0', (1.0, 0.3, 0.2), 30.0), loc=TR + V3(0, 0, 1), vertices=32, radius=7, depth=1.5)
PIN1 = prim('cylinder', 'pin_end', emis('pin1', (0.3, 1.0, 0.4), 30.0), loc=LAND + V3(0, 0, 1), vertices=32, radius=7, depth=1.5)
DOT = prim('uv_sphere', 'flying_dot', emis('dot', (1.0, 0.95, 0.8), 60.0), segments=16, ring_count=8, radius=4.5)
MAPSET = [PATH, PIN0, PIN1, DOT]
def path_at(s):
    s = clamp(s, 0, 1) * PATH_ARC[-1]; i = int(np.searchsorted(PATH_ARC, s)) - 1; i = clamp(i, 0, len(PATH_PTS) - 2)
    return PATH_PTS[i].lerp(PATH_PTS[i + 1], (s - PATH_ARC[i]) / max(PATH_ARC[i + 1] - PATH_ARC[i], 1e-9))
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
# ================================================================ MODES and the story
MAN = [BODY, SUIT, HAIR] + HEADBITS
OUTDOOR = [GROUND, TUFTS, SKY, WALLCLOUD, FUNNEL, FUN2, DUSTC, NEAR.o, FAR.o] + FENCE + POLES + TREES + TRAILER + OUT_L
def mode(which):
    for o in OUTDOOR + CLOSET + MAPSET + [STREAMS]: o.hide_render = True
    for o in MAN: o.hide_render = which == 'map'
    if which in ('out', 'map'):
        for o in OUTDOOR: o.hide_render = False
    if which == 'map':
        for o in MAPSET: o.hide_render = False
        NEAR.o.hide_render = True
    if which == 'closet':
        for o in CLOSET: o.hide_render = False
    WBG.inputs['Color'].default_value = (0.04, 0.05, 0.045, 1) if which != 'closet' else (0.0, 0.0, 0.0, 1)
def storm(t, tc, near_c=None, near_slow=1.0, far_slow=1.0, near_r=(1.2, 5.0), dens=1.0, wind=1.0):
    for o in (FUNNEL, FUN2, DUSTC): o.location = tc; o['tt'] = t
    FUNNEL['dens'] = dens; FUN2['dens'] = 0.45 * dens; DUSTC['dens'] = 0.8 * dens; SKY['tt'] = t; WALLCLOUD.location = tc + V3(0, 0, 560)
    FAR.swirl(tc + V3(0, 0, 1), t, 18, 70, 140, 0.55, far_slow, lift=6.0)
    if near_c is not None: NEAR.o.hide_render = False; NEAR.swirl(near_c - V3(0, 0, 2.5), t, near_r[0], near_r[1], 6.0, 1.6, near_slow, lift=1.2)
    else: NEAR.o.hide_render = True
    TUFTS.data.shape_keys.key_blocks['wind'].value = clamp(wind * (0.6 + 0.4 * wob(t, 3, 2)), 0, 1)
M0 = V3(2.6, -4.6, 0.0); YAW0 = 0.0
BRACE_T = dict(ankR=V3(-0.14, 0.02, 0.09), ankL=V3(0.14, 0.02, 0.09), handR=V3(-0.1, -0.32, 1.62), handL=V3(0.12, -0.33, 1.6))
def lift_off(v, t):
    """0..1: off his feet and tumbling up (B0); v<0 = still braced, rising onto his toes (end of B11, the loop)"""
    k = smooth(0.08, 0.45, v); up = 0.05 + 7.5 * smooth(0.0, 1.0, v) ** 1.5
    hip = M0 + V3(0.0, 4.0 * smooth(0.1, 1.0, v), STAND_HIP + up); rot = (6 + lerp(0, -75, smooth(0.1, 1.0, v)) + 20 * wob(t, 1.5, 4) * k, 25 * wob(t, 1.1, 5) * k, YAW0 + 120 * smooth(0.15, 1.0, v) ** 1.3)
    f = flail(t, 1.0, 2.0); tg = {n: BRACE_T[n].lerp(f[n], k) for n in f}
    feet_flat(False); body(hip, rot, tg['ankR'], tg['ankL'], tg['handR'], tg['handL'], neck=8 + 10 * k, jaw=0.3 + 0.4 * k, lids=0.5 + 0.2 * k, curl=(0.8 - 0.3 * k,) * 2, pk=(1 - 2 * k, 1 - 2 * k))
    return hip
def cam_b0(v):
    return M0 + V3(1.3, -3.1, 0.45).lerp(V3(2.2, -5.0, 0.3), smooth(0, 1, v)), M0 + V3(-0.1, 0.4, 1.35).lerp(V3(0.0, 3.5, 5.5), smooth(0, 1, v)), lerp(22, 20, v)
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    S.view_settings.exposure = 0.0; FLASH.data.energy = 0.0
    if nb == 0:                                             # he is ripped off the ground: rising, tumbling, junk all around him
        mode('out'); hip = lift_off(u, t); storm(t, V3(4, 34, 0), near_c=hip, dens=1.0)
        cp, ct, ln = cam_b0(u); look(cp + shake(t, 0.05), ct.lerp(hip + V3(0, 0, 0.2), 0.6 + 0.35 * smooth(0.3, 1.0, u)), ln, 4.0, focus=hip)
    elif nb == 1:                                           # the inflow: air spiralling in along the ground, faster as it squeezes in
        mode('out'); STREAMS.hide_render = False; STREAMS['tt'] = t; STREAMS['reach'] = 120 + 700 * smooth(0.0, 1.0, u); storm(t, TC0, dens=0.9)
        a_ = lerp(-0.9, -0.55, u); cp = TC0 + V3(520 * math.sin(a_), -520 * math.cos(a_), 150); look(cp, TC0 + V3(0, 0, 70), 30, 16.0)
        FUNNEL['dens'] = 0.75
    elif nb == 2:                                           # up the middle: inside the funnel looking up, he goes up with it
        mode('out'); tc = V3(0, 0, 0) + M0
        hip = M0 + V3(0, 0, 14 + 22 * u); airborne(hip, (-40 + 90 * u, 20, 180 + 200 * u), t, 1.0, 3.0); storm(t, tc, near_c=hip, dens=1.0, near_r=(2, 9))
        look(hip + V3(1.2, -2.2, -6.0), hip + V3(0, 0, 1.5), 22, 8.0, focus=hip); S.view_settings.exposure = 0.4
    elif nb == 3:                                           # over 200 mph: the whole tornado, junk orbiting it
        mode('out'); storm(t, TC0, dens=1.0); look(TC0 + V3(-230, -300, 8).lerp(V3(-190, -250, 12), u) + shake(t, 0.4), TC0 + V3(0, 0, 110), 26, 16.0)
    elif nb in (4, 5, 6):                                   # slow motion up in it: him tumbling, boards / glass / rocks going past
        mode('out'); slow = 0.25; ts = B[4] + (t - B[4]) * slow
        hip = M0 + V3(0, 4, 10 + 2.0 * (t - B[4]) * slow); airborne(hip, (-80 + 40 * (t - B[4]) * slow, 15, 300 + 70 * (t - B[4]) * slow), ts, 1.0, 2.0)
        storm(ts, V3(4, 34, 0), near_c=hip, near_slow=1.0, dens=1.0, near_r=(0.9, 4.0))
        if nb == 4: a_ = 0.4 + 0.5 * u; look(hip + V3(3.8 * math.sin(a_), -3.8 * math.cos(a_), -0.8), hip + V3(0, 0, 0.1), 32, 5.6, focus=hip)
        elif nb == 5: a_ = 0.9 + 0.7 * u; look(hip + V3(2.6 * math.sin(a_), -2.6 * math.cos(a_), 0.3 - 0.6 * u), hip, 28, 4.0, focus=hip)
        else:                                               # a board comes straight at the camera and just misses
            NEAR_B = 0; ang = np.zeros((NEAR.n, 3)); P = NEAR.swirl(hip - V3(0, 0, 2.5), ts, 0.9, 4.0, 6.0, 1.6, 1.0, lift=1.2)
            cp = hip + V3(0.6, -3.6, 0.2); P[0] = np.array(hip + V3(2.5, 3.0, 0.4)).copy() * 0 + np.array((hip + V3(4.0, 6.0, 0.3)).lerp(cp + V3(0.35, -0.6, 0.15), smooth(0.05, 0.75, u)))
            angs = NEAR.spin * ts; angs[0] = (0.3, 0.2, R(60) + 3.0 * u); NEAR.set(P, angs)
            look(cp, hip + V3(0, 0, 0.1), 30, 4.0, focus=hip)
    elif nb == 7:                                           # 2006: pulled out through the trailer's door
        mode('out'); S.view_settings.exposure = -0.9; FLASH.data.energy = 2.5e6 * max(0.0, 1 - abs(u - 0.3) * 14) + 1.2e6 * max(0.0, 1 - abs(u - 0.38) * 20)
        for o in TRAILER: o.hide_render = False
        v = smooth(0.25, 1.0, u); door = V3(0.4, -TRW / 2 - 0.4, 0)
        hip = door + V3(0, -0.3 - 9 * v, 1.0 + 6 * v ** 1.4); airborne(hip, (-60 * v, 10, 200 + 160 * v), t, 0.4 + 0.6 * v, 5.0)
        storm(t, V3(0, 42, 0), near_c=hip if v > 0.05 else None, dens=1.0)
        look(door + V3(-4.0, -6.5, 1.2).lerp(V3(-4.5, -8.5, 1.6), u), (door + V3(0, -1, 1.6)).lerp(hip, 0.7), 24, 6.0, focus=hip)
    elif nb == 8:                                           # carried 1,307 ft: the map, the path draws itself, a light rides it
        mode('map'); v = smooth(0.05, 0.9, u); PATH['reach'] = PATH_ARC[-1] * v; DOT.location = path_at(v) + V3(0, 0, 3)
        storm(t, TR + V3(-40, -90, 0) + (LAND - TR) * (0.3 + 0.7 * v), dens=0.6); NEAR.o.hide_render = True
        for o in (FUNNEL, FUN2, DUSTC, FAR.o): o.hide_render = True
        WALLCLOUD.hide_render = SKY.hide_render = True; mid = TR.lerp(LAND, 0.5); look(mid + V3(-40, -300, 520), mid, 34, 64.0)
    elif nb == 9:                                           # he lands in a field and comes to
        mode('out'); FUNNEL.hide_render = FUN2.hide_render = DUSTC.hide_render = True; NEAR.o.hide_render = FAR.o.hide_render = True
        lying(LAND.x, LAND.y, smooth(0.35, 1.0, u), t); TUFTS.location = LAND - V3(0, 0, 0)
        hd = RIG.matrix_world @ V3(0, 0, 1.4); look(hd + V3(1.8, -1.3, 0.45).lerp(V3(1.5, -1.0, 0.65), u), hd.lerp(RIG.matrix_world @ HIP0, 0.4), 30, 4.0, focus=hd)
        SKY['tt'] = t
    elif nb == 10:                                          # the lowest room, no windows, hands over his head
        mode('closet'); S.view_settings.exposure = 0.8; crouch(t, 1.0); BULB.rotation_euler = (R(18) * math.sin(t * 3.1), R(10) * math.sin(t * 2.3 + 1), 0)
        hd = RIG.matrix_world @ V3(0, 0.05, 1.55); look(CL + V3(0.62, -0.72, 1.55) + shake(t, 0.012), hd.lerp(CL + V3(0, 0, 0.6), 0.4), 18, 4.0, focus=hd)
    else:                                                   # back outside: the wind picks up, then his heels come up (= frame one)
        mode('out'); wind = smooth(0.0, 0.8, u)
        tc = V3(4, 34, 0).lerp(V3(4, 34, 0), 1.0) + V3(-25 * (1 - u), 20 * (1 - u), 0)
        if u < 0.72: stand(M0.x, M0.y, YAW0, t, brace=smooth(0.2, 0.6, u)); hip = RIG.matrix_world @ HIP0
        else: hip = lift_off(lerp(-0.0, 0.0, u), t) if False else lift_off(0.0, t)
        storm(t, tc, near_c=hip if u > 0.5 else None, dens=1.0, wind=wind)
        cp0, ct0, ln0 = cam_b0(0.0); k = smooth(0.0, 0.9, u)
        look(cp0 + V3(-0.6, -1.5, 0.4) * (1 - k) + shake(t, 0.02 + 0.03 * k), (M0 + V3(-0.5, 1.5, 1.6)).lerp(ct0, k), lerp(26, ln0, k), 4.0, focus=hip)

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

