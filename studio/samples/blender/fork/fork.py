# A fork in the microwave: why it sparks. Blender Cycles, ONE continuous camera move (no cuts), resting on each idea,
# close-ups inside the oven, real kitchen background and counter (prop studio, CC0), real-recording sound.
#   python3 fork.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join(HERE, 'assets', n), os.path.join('/root/vt/n45/boat', n), os.path.join('/root/vt/assets', n)) if os.path.exists(p_))
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
C.max_bounces = 8; C.diffuse_bounces = 2; C.glossy_bounces = 2; C.transmission_bounces = 7; C.volume_bounces = 0; C.transparent_max_bounces = 24
C.use_adaptive_sampling = True; C.adaptive_threshold = 0.05; C.adaptive_min_samples = 8
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

# ---------------------------------------------------------------- compositor: a soft bloom round bright things (the Sun, the vent, glows)
GLARE = None
try:
    ct_ = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); S.compositing_node_group = ct_
    rl_ = ct_.nodes.new('CompositorNodeRLayers'); GLARE = ct_.nodes.new('CompositorNodeGlare'); GLARE.inputs['Type'].default_value = 'Bloom'
    for k_, v_ in (('Threshold', 1.2), ('Strength', 0.35), ('Size', 0.6)):
        try: GLARE.inputs[k_].default_value = v_
        except Exception: pass
    out_ = ct_.nodes.new('NodeGroupOutput'); ct_.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ct_.links.new(rl_.outputs['Image'], GLARE.inputs['Image']); ct_.links.new(GLARE.outputs['Image'], out_.inputs[0]); print('glow on')
except Exception as e_: print('glow skipped', e_)
def bloom(strength=0.35, thresh=1.2):
    if GLARE is None: return
    try: GLARE.inputs['Strength'].default_value = strength; GLARE.inputs['Threshold'].default_value = thresh
    except Exception: pass

# ---------------------------------------------------------------- fast primitives (bmesh, no bpy.ops): this scene has thousands of parts
def prim(kind, name, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), **kw):
    bm = bmesh.new()
    if kind == 'cube': bmesh.ops.create_cube(bm, size=kw.get('size', 2.0))
    elif kind == 'uv_sphere': bmesh.ops.create_uvsphere(bm, u_segments=kw.get('segments', 32), v_segments=kw.get('ring_count', 16), radius=kw.get('radius', 1.0))
    elif kind == 'ico_sphere': bmesh.ops.create_icosphere(bm, subdivisions=kw.get('subdivisions', 2), radius=kw.get('radius', 1.0))
    elif kind == 'plane':
        h = kw.get('size', 2.0) / 2; vs_ = [bm.verts.new((x_ * h, y_ * h, 0)) for x_, y_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; bm.faces.new(vs_)
    else: raise ValueError(kind)
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    smooth_ = kind in ('uv_sphere', 'ico_sphere')
    for p in me.polygons: p.use_smooth = smooth_
    o = obj(name, me, m, loc, parent); o.rotation_euler = rot; return o

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

def emis_mix(name, col, strength, alpha_attr=None):
    """emission over transparent; object property alpha_attr (0..1) fades it"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    if alpha_attr: nt.links.new(objattr(nt, alpha_attr), mx.inputs['Fac'])
    else: mx.inputs['Fac'].default_value = 1.0
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.03; CAM.data.clip_end = 1e6
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5
def look(cp, ct, lens=35, fstop=8.0, focus=None, up=None, roll=0.0):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    if up is None: q = d.to_track_quat('-Z', 'Y')
    else:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0, f=7.0): return Vector((wob(t, f, seed), wob(t, f, seed + 3.3), wob(t, f, seed + 6.1))) * amt
def show(objs, on):
    for o in objs: o.hide_render = not on
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; WBG = W_.node_tree.nodes['Background']
WBG.inputs['Color'].default_value = (0, 0, 0, 1); WBG.inputs['Strength'].default_value = 0.0

# ================================================================ the set: a kitchen counter and a modern microwave built to real size
# World: the counter top is z = 0, the microwave's front face is the plane y = -0.20 (we look at it from -y), x is left/right.
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_START = word_t(0, 9)                         # "pressing start"
T_EXPLODE = word_t(1, 7)                       # "explode"
T_METAL = word_t(2, 10)                        # "made of metal"
T_BOUNCE = word_t(3, 2)                        # "bounce the waves"
T_FOOD = word_t(3, 15)                         # "water in your food"
T_SHAPE = word_t(4, 7)                         # "its shape"
T_SHOVE = word_t(5, 2)                         # "shove tiny charges"
T_PILE = word_t(5, 13)                         # "pile up at the sharp tips"
T_AIR = word_t(6, 6)                           # "the air around the tips breaks down"
T_SPARK = word_t(6, 19)                        # "as a spark"
T_BOLT = word_t(7, 3)                          # "tiny bolt of lightning"
T_PAPER = word_t(8, 4)                         # "paper nearby"
T_FIRE = word_t(8, 14)                         # "start a fire"
T_SPOON = word_t(9, 3)                         # "smooth spoon"
T_BARELY = word_t(9, 11)                       # "barely sparks"
T_POINTS = word_t(10, 9)                       # "it's the points"
CAM.data.clip_start = 0.002

# ---- the kitchen: a real interior (Poly Haven HDRI) for light, reflections and the view behind; a marble counter, a tiled wall
P.hdri('ph:cayley_interior', 0.9, 205)
COUNTER = box('counter', (1.6, 0.65, 0.04), (0, 0.02, -0.02), P.material('acg:Marble016', scale=1.4), bv=0.004)
box('counter_edge', (1.6, 0.03, 0.04), (0, -0.315, -0.02), mat('edge', (0.86, 0.86, 0.85), 0.2, coat=0.6))
box('cabinet', (1.6, 0.6, 0.86), (0, 0.04, -0.47), P.material('ph:kitchen_wood', scale=1.2))
WALL = box('backsplash', (1.6, 0.02, 0.6), (0, 0.36, 0.3), mat('tile', (0.92, 0.92, 0.90), 0.15, coat=0.4))
_wn = WALL.data.materials[0].node_tree; _wb = _wn.nodes['Principled BSDF']; _p = sepz(_wn, coord(_wn, 'Object'))
_gx = math_(_wn, 'LESS_THAN', math_(_wn, 'ABSOLUTE', math_(_wn, 'SUBTRACT', math_(_wn, 'FRACT', math_(_wn, 'DIVIDE', _p.outputs['X'], 0.15)), 0.5)), 0.485)
_gz = math_(_wn, 'LESS_THAN', math_(_wn, 'ABSOLUTE', math_(_wn, 'SUBTRACT', math_(_wn, 'FRACT', math_(_wn, 'DIVIDE', _p.outputs['Z'], 0.075)), 0.5)), 0.47)
_wn.links.new(mixc(_wn, math_(_wn, 'MULTIPLY', _gx, _gz), (0.55, 0.55, 0.53), (0.92, 0.92, 0.90)), _wb.inputs['Base Color'])
KEY = light_at('key', 'AREA', (-0.9, -0.9, 1.1), (0, 0, 0.15), 60, (1.0, 0.94, 0.86), 1.0)
RIM = light_at('rim', 'AREA', (0.8, 0.5, 0.9), (0, 0, 0.15), 25, (0.85, 0.9, 1.0), 0.6)

# ---- the microwave: 50 x 40 x 30 cm. Brushed steel case, black glass door with the dotted metal screen inside it,
# white enamel cavity (34 x 33 x 21 cm), a glass turntable, the mica cover of the waveguide on the right wall, a warm bulb.
MW_W, MW_D, MW_H = 0.50, 0.40, 0.30
CX0, CX1, CY0, CY1, CZ0, CZ1 = -0.225, 0.115, -0.185, 0.165, 0.035, 0.245     # the cavity box
STEEL = mat('steel', (0.62, 0.63, 0.64), 0.28, 1.0); noisy(STEEL, 900.0, 0.05, 0.08)
ENAMEL = mat('enamel', (0.86, 0.86, 0.84), 0.25, coat=0.3); ENAMEL_M = ENAMEL
CASE = []
def cbox(n, size, loc, m=STEEL, bv=0.0): o = box(n, size, loc, m, bv=bv); CASE.append(o); return o
cbox('mw_top', (MW_W, MW_D, 0.012), (0, -0.0, MW_H - 0.006), bv=0.004)
cbox('mw_bot', (MW_W, MW_D, 0.035), (0, -0.0, 0.0175))
cbox('mw_left', (0.012, MW_D, MW_H), (-MW_W / 2 + 0.006, 0, MW_H / 2), bv=0.003)
cbox('mw_right', (0.012, MW_D, MW_H), (MW_W / 2 - 0.006, 0, MW_H / 2), bv=0.003)
cbox('mw_back', (MW_W, 0.012, MW_H), (0, MW_D / 2 - 0.006, MW_H / 2))
for i_ in range(4): cbox(f'mw_foot{i_}', (0.03, 0.03, 0.008), ((-1) ** i_ * 0.2, (-1) ** (i_ // 2) * 0.16, -0.002), mat('foot', (0.02, 0.02, 0.02), 0.8))
# the cavity: five enamel walls (the x-ray beat turns them see-through by the 'xr' property)
def xray_mat(name, base, rough, metal=0.0):
    m = mat(name, base, rough, metal); nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    gl = nt.nodes.new('ShaderNodeBsdfPrincipled'); gl.inputs['Base Color'].default_value = (0.75, 0.85, 1.0, 1); gl.inputs['Metallic'].default_value = 1.0; gl.inputs['Roughness'].default_value = 0.22
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    ghost = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(lw.outputs['Facing'], ghost.inputs['Fac']); nt.links.new(tr.outputs[0], ghost.inputs[1]); nt.links.new(gl.outputs[0], ghost.inputs[2])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(ghost.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface']); return m
CAV_M = xray_mat('cavity', (0.86, 0.86, 0.84), 0.25)
CAV = [box('cav_floor', (CX1 - CX0, CY1 - CY0, 0.004), ((CX0 + CX1) / 2, (CY0 + CY1) / 2, CZ0 - 0.002), CAV_M),
       box('cav_top', (CX1 - CX0, CY1 - CY0, 0.004), ((CX0 + CX1) / 2, (CY0 + CY1) / 2, CZ1 + 0.002), CAV_M),
       box('cav_left', (0.004, CY1 - CY0, CZ1 - CZ0), (CX0 - 0.002, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2), CAV_M),
       box('cav_right', (0.004, CY1 - CY0, CZ1 - CZ0), (CX1 + 0.002, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2), CAV_M),
       box('cav_back', (CX1 - CX0, 0.004, CZ1 - CZ0), ((CX0 + CX1) / 2, CY1 + 0.002, (CZ0 + CZ1) / 2), CAV_M)]
for o in CAV: o['xr'] = 0.0
WG = box('waveguide', (0.003, 0.07, 0.05), (CX1 - 0.0005, 0.02, 0.19), mat('mica', (0.72, 0.62, 0.45), 0.6))   # where the waves come in
# the control panel (right of the door): black glass, a green clock, the keypad
PANEL_M = mat('panel', (0.012, 0.012, 0.014), 0.12, coat=1.0)
box('panel', (MW_W / 2 - CX1 - 0.02, 0.006, MW_H - 0.05), ((CX1 + 0.02 + MW_W / 2) / 2 + 0.005, -MW_D / 2 - 0.003, MW_H / 2), PANEL_M)
CLOCK = box('clock', (0.07, 0.002, 0.018), (0.185, -MW_D / 2 - 0.0065, 0.245), emis('clock', (0.2, 1.0, 0.45), 4.0))
for r_ in range(4):
    for c_ in range(3):
        box(f'key{r_}{c_}', (0.016, 0.003, 0.010), (0.163 + 0.022 * c_, -MW_D / 2 - 0.007, 0.205 - 0.022 * r_), mat(f'kp{r_}{c_}', (0.25, 0.25, 0.26), 0.4))
START_BTN = box('start_btn', (0.06, 0.003, 0.016), (0.185, -MW_D / 2 - 0.007, 0.095), mat('startb', (0.25, 0.55, 0.30), 0.4))
# the door: frame + glass with the dotted screen (holes much smaller than the 12 cm waves, so they can't get out)
DOOR_X0, DOOR_X1 = -MW_W / 2 + 0.008, CX1 + 0.02
DOOR_M = mat('doorframe', (0.02, 0.02, 0.022), 0.15, coat=1.0)
def door_glass_mat():
    m = bpy.data.materials.new('doorglass'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1); b.inputs['Roughness'].default_value = 0.05; b.inputs['Coat Weight'].default_value = 1.0
    p = sepz(nt, coord(nt, 'Object'))
    u = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['X'], 0.004)); v = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['Z'], 0.004))
    hole = math_(nt, 'LESS_THAN', math_(nt, 'ADD', math_(nt, 'POWER', math_(nt, 'SUBTRACT', u, 0.5), 2.0), math_(nt, 'POWER', math_(nt, 'SUBTRACT', v, 0.5), 2.0)), 0.09)
    see = math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', hole, 0.8), objattr(nt, 'xr'))        # see through the holes (and fully in x-ray)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(see, mx.inputs['Fac'])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
DOOR = empty('door', loc=(0, -MW_D / 2 - 0.004, 0))
for nm_, sz, lc in (('door_l', (0.03, 0.012, MW_H - 0.02), (DOOR_X0 + 0.015, 0, MW_H / 2)), ('door_r', (0.03, 0.012, MW_H - 0.02), (DOOR_X1 - 0.015, 0, MW_H / 2)),
                    ('door_t', (DOOR_X1 - DOOR_X0, 0.012, 0.035), ((DOOR_X0 + DOOR_X1) / 2, 0, MW_H - 0.0275)), ('door_b', (DOOR_X1 - DOOR_X0, 0.012, 0.035), ((DOOR_X0 + DOOR_X1) / 2, 0, 0.0275))):
    o = box(nm_, sz, lc, DOOR_M, bv=0.002, parent=DOOR); o['xr'] = 0.0
DGLASS = box('door_glass', (DOOR_X1 - DOOR_X0 - 0.06, 0.004, MW_H - 0.09), ((DOOR_X0 + DOOR_X1) / 2, 0, MW_H / 2), door_glass_mat(), parent=DOOR); DGLASS['xr'] = 0.0
HANDLE = box('handle', (0.016, 0.03, 0.2), (DOOR_X1 - 0.03, -0.018, MW_H / 2), STEEL, bv=0.006, parent=DOOR)
# inside light (the bulb behind the top right) and the turntable
BULB = light_at('bulb', 'POINT', (CX1 - 0.03, CY0 + 0.06, CZ1 - 0.01), (0, 0, 0), 4.0, (1.0, 0.82, 0.55), 0.01)
TT_C = Vector(((CX0 + CX1) / 2, (CY0 + CY1) / 2 + 0.005, CZ0))
TT = empty('turntable', loc=TT_C)
TT_GLASS = mat('tt_glass', (0.72, 0.86, 0.82), 0.14, trans=0.92, ior=1.5)          # green-edged tray glass, a touch frosted so it reads as a surface
lathe('tt_plate', [(0.0, 0.012), (0.132, 0.012), (0.135, 0.016), (0.135, 0.02), (0.0, 0.02)], 64, TT_GLASS, TT)
lathe('tt_ring', [(0.07, 0.0), (0.075, 0.0), (0.075, 0.011), (0.07, 0.011)], 32, mat('ring', (0.08, 0.08, 0.08), 0.5), loc=TT_C)

# ================================================================ on the turntable: a plate of leftover pasta, the fork and a spoon, a takeout box
# All built to real size. Everything on the turntable is parented to TT so it turns with it (3 turns a minute).
CERAMIC = mat('ceramic', (0.05, 0.22, 0.30), 0.10, coat=1.0)                # a deep teal plate: the silver fork pops on it
PLATE_C = Vector((0.03, 0.0, 0.0))
PLATE = lathe('plate', [(0.0, 0.0205), (0.06, 0.0205), (0.068, 0.022), (0.088, 0.031), (0.095, 0.0325), (0.096, 0.031), (0.086, 0.0265), (0.066, 0.0225),
                        (0.058, 0.0215), (0.0, 0.0215)], 64, CERAMIC, TT)
PLATE.location = PLATE_C
for p_ in PLATE.data.polygons: p_.use_smooth = True
# leftover mac and cheese: ~170 little curved macaroni on a low mound; 'heat' makes it glow warm (the food soaking up the waves)
def food_mat():
    m = mat('mac', (0.95, 0.68, 0.20), 0.32, coat=0.6); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    v = tnoise(nt, coord(nt, 'Object'), 60.0, 3.0); nt.links.new(mixc(nt, v, (0.78, 0.30, 0.02), (0.96, 0.52, 0.05)), b.inputs['Base Color'])
    b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (1.0, 0.6, 0.2); b.inputs['Subsurface Scale'].default_value = 0.002
    nt.links.new(objattr(nt, 'heat_col'), b.inputs['Emission Color']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'heat'), 2.5), b.inputs['Emission Strength']); return m
FOOD_M = food_mat()
FOOD = prim('uv_sphere', 'food', FOOD_M, TT, loc=(PLATE_C.x + 0.005, PLATE_C.y + 0.035, 0.0215), scale=(0.034, 0.028, 0.011), segments=32, ring_count=16)
for v in FOOD.data.vertices:
    if v.co.z < 0: v.co.z *= 0.05
FOOD['heat'] = 0.0; FOOD['heat_col'] = (1.0, 0.45, 0.12, 1.0)
for p_ in FOOD.data.polygons: p_.use_smooth = True
_mb = bmesh.new(); _rr = random.Random(9)
for i_ in range(170):
    a_ = _rr.uniform(0, 2 * math.pi); r_ = 0.034 * math.sqrt(_rr.random()); x_ = r_ * math.cos(a_); y_ = r_ * math.sin(a_) * 0.82
    zt = 0.011 * max(0.0, 1 - (x_ / 0.034) ** 2 - (y_ / 0.028) ** 2) ** 0.5 + _rr.uniform(0.0, 0.004)
    ring = bmesh.ops.create_circle(_mb, cap_ends=False, segments=8, radius=0.0019)['verts']; pts = []
    for k in range(6):                                                           # a bent tube: 6 rings round a 100-degree arc
        th = math.radians(-50 + 20 * k); c_ = Vector((0.006 * math.sin(th), 0.006 * (1 - math.cos(th)), 0)); pts.append((c_, th))
    rings = []
    for c_, th in pts:
        vs = [_mb.verts.new(c_ + Matrix.Rotation(th, 3, 'Z') @ Vector((0, v.co.x, v.co.y))) for v in ring]; rings.append(vs)
    bmesh.ops.delete(_mb, geom=ring, context='VERTS')
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(8): _mb.faces.new((r0[k], r0[(k + 1) % 8], r1[(k + 1) % 8], r1[k]))
    M = Matrix.Translation((PLATE_C.x + 0.005 + x_, PLATE_C.y + 0.035 + y_, 0.0215 + zt)) @ Euler((_rr.uniform(-0.6, 0.6), _rr.uniform(-0.6, 0.6), _rr.uniform(0, 6.3))).to_matrix().to_4x4()
    bmesh.ops.transform(_mb, matrix=M, verts=[v for r in rings for v in r])
_mm = bpy.data.meshes.new('macaroni'); _mb.to_mesh(_mm); _mb.free(); MAC = obj('macaroni', _mm, FOOD_M, parent=TT)
for p_ in _mm.polygons: p_.use_smooth = True
MAC['heat'] = 0.0; MAC['heat_col'] = (1.0, 0.45, 0.12, 1.0)
# ---- the fork: stainless, 19 cm, four pointed tines; local x runs from the handle end (0) to the tine tips (0.19)
FORK_M = mat('stainless', (0.80, 0.80, 0.82), 0.16, 1.0, coat=0.2)
def flat_shape(name, outline, th, m, parent, loc=(0, 0, 0)):
    bm = bmesh.new(); vs = [bm.verts.new((x, y, 0.0)) for x, y in outline]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, th), verts=[e for e in ex['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj(name, me, m, loc=loc, parent=parent); md = o.modifiers.new('bv', 'BEVEL'); md.width = th * 0.45; md.segments = 3; md.limit_method = 'ANGLE'
    o.modifiers.new('wn', 'WEIGHTED_NORMAL')
    for p_ in me.polygons: p_.use_smooth = True
    return o
FORK = empty('fork', TT, loc=(0.173, -0.045, 0.0369)); FORK.rotation_euler = (0, R(4.9), R(172))        # handle resting on the rim, tines lying on the flat of the plate
_h = [(0.0, 0.0105), (0.012, 0.0118), (0.05, 0.0095), (0.098, 0.0042), (0.118, 0.0036), (0.135, 0.0062), (0.148, 0.0118), (0.152, 0.0122)]
FORK_BODY = flat_shape('fork_body', [(x, y) for x, y in _h] + [(x, -y) for x, y in reversed(_h)], 0.0024, FORK_M, FORK)
TINE_TIPS = []
for k_ in range(4):
    yc = -0.0092 + 0.00613 * k_; w = 0.0021
    o = flat_shape(f'tine{k_}', [(0.150, yc - w), (0.182, yc - w * 0.9), (0.190, yc), (0.182, yc + w * 0.9), (0.150, yc + w)], 0.0022, FORK_M, FORK)
    TINE_TIPS.append(Vector((0.1895, yc, 0.0011)))
# ---- the spoon: smooth, no points (an oval bowl and a round-ended handle), lying beside the fork
SPOON = empty('spoon', TT, loc=(0.13, 0.055, 0.0345)); SPOON.rotation_euler = (0, R(2.0), R(176))
_sh = [(0.0, 0.006), (0.01, 0.0095), (0.06, 0.0085), (0.105, 0.0035), (0.12, 0.004)]
flat_shape('spoon_handle', [(x, y) for x, y in _sh] + [(x, -y) for x, y in reversed(_sh)], 0.0022, FORK_M, SPOON)
SB = prim('uv_sphere', 'spoon_bowl', FORK_M, SPOON, loc=(0.145, 0, 0.004), scale=(0.028, 0.019, 0.0065), segments=40, ring_count=20)
for v in SB.data.vertices:
    if v.co.z > 0.25: v.co.z = 0.25 - (v.co.z - 0.25) * 0.35                     # dished in on top: a real spoon bowl, smooth all round
# ---- the takeout box: white folded paperboard, wider at the top, with a thin wire handle stapled through its sides
PAPER_M = mat('paper', (0.92, 0.91, 0.87), 0.85)
_pn = PAPER_M.node_tree; _pz = sepz(_pn, coord(_pn, 'Object')).outputs['Z']
_band = math_(_pn, 'MULTIPLY', math_(_pn, 'GREATER_THAN', _pz, 0.028), math_(_pn, 'LESS_THAN', _pz, 0.046))
_pn.links.new(mixc(_pn, _band, (0.92, 0.91, 0.87), (0.72, 0.06, 0.05)), _pn.nodes['Principled BSDF'].inputs['Base Color'])
CARTON = empty('carton', TT, loc=(-0.098, 0.055, 0.02)); CARTON.rotation_euler = (0, 0, R(25))
_bm = bmesh.new()
bot = [(-0.026, -0.022), (0.026, -0.022), (0.026, 0.022), (-0.026, 0.022)]; top = [(-0.036, -0.03), (0.036, -0.03), (0.036, 0.03), (-0.036, 0.03)]
vb = [_bm.verts.new((x, y, 0.0)) for x, y in bot]; vt = [_bm.verts.new((x, y, 0.075)) for x, y in top]
_bm.faces.new(vb[::-1])
for i_ in range(4): _bm.faces.new((vb[i_], vb[(i_ + 1) % 4], vt[(i_ + 1) % 4], vt[i_]))
for sy in (-1, 1):                                                               # the folded top flaps (closed into a peak)
    a_ = _bm.verts.new((-0.036, sy * 0.03, 0.075)); b_ = _bm.verts.new((0.036, sy * 0.03, 0.075)); c_ = _bm.verts.new((0.036, sy * 0.004, 0.098)); d_ = _bm.verts.new((-0.036, sy * 0.004, 0.098))
    _bm.faces.new((a_, b_, c_, d_))
_me = bpy.data.meshes.new('carton'); _bm.to_mesh(_me); _bm.free(); CART = obj('carton_body', _me, PAPER_M, parent=CARTON)
sol = CART.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.0012
WIRE_M = mat('wire', (0.7, 0.7, 0.72), 0.25, 1.0)
WIRE_ENDS = [Vector((-0.0335, 0.0, 0.065)), Vector((0.0335, 0.0, 0.065))]
tube('carton_wire', [Vector((-0.0345, 0.0, 0.065)), Vector((-0.03, 0.0, 0.11)), Vector((0.0, 0.0, 0.135)), Vector((0.03, 0.0, 0.11)), Vector((0.0345, 0.0, 0.065))], 0.0009, WIRE_M, CARTON, seg=8)
# ---- the flame on the box (crossed sheets with a moving noise mask) and its light
def flame_mat():
    m = bpy.data.materials.new('flame'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    p = sepz(nt, coord(nt, 'Generated')); u = math_(nt, 'SUBTRACT', p.outputs['X'], 0.5); v = p.outputs['Y']          # the plane stands up: Y runs base to tip
    vec = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', p.outputs['X'], 3.0), vec.inputs['X'])
    nt.links.new(math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', v, 2.0), math_(nt, 'MULTIPLY', objattr(nt, 'ft'), 3.5)), vec.inputs['Y']); nt.links.new(objattr(nt, 'ft'), vec.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4.0; nt.links.new(vec.outputs[0], nz.inputs['Vector'])
    width = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, v), 0.42)
    edge = math_(nt, 'SUBTRACT', width, math_(nt, 'ADD', math_(nt, 'ABSOLUTE', u), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.5), 0.5)))
    shape = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', edge, 0.07), 0.0), 1.0)          # soft edges, not a cut-out
    k = math_(nt, 'MULTIPLY', shape, objattr(nt, 'fa'))
    col = ramp(nt, v, [(0.0, (1.0, 0.75, 0.25)), (0.35, (1.0, 0.38, 0.04)), (1.0, (0.7, 0.06, 0.01))])
    e_ = nt.nodes.new('ShaderNodeEmission'); nt.links.new(col, e_.inputs['Color']); e_.inputs['Strength'].default_value = 4.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', k, 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
FLAME_M = flame_mat(); FLAMES = []
for k_ in range(3):
    f = prim('plane', f'flame{k_}', FLAME_M, CARTON, loc=(0.036, -0.012 + 0.012 * k_, 0.07), rot=(R(90), 0, R(90 + 55 * k_ - 55)), scale=(0.024, 0.045, 1), size=1)
    bpy.context.view_layer.update(); f.data.transform(Matrix.Translation((0, 0.0225, 0))); f['ft'] = 0.0; f['fa'] = 0.0; f.hide_render = True; FLAMES.append(f)   # base at the origin (scale already applied)
FIRE_LT = light_at('fire_lt', 'POINT', (0, 0, 0), (0, 0, 0), 0.0, (1.0, 0.55, 0.2), 0.006); FIRE_LT.parent = CARTON; FIRE_LT.location = (0.04, 0.0, 0.09)

# ================================================================ the physics shown: waves bouncing off the walls, charges sloshing, the spark
# ---- waves: a glass "slice" through the cavity shows the wave crests spreading out of the waveguide and bouncing off every wall.
# Each wall is a mirror, so the bounces are rings from mirror-image sources (reflected across the walls); a ring exists only where
# the front has had time to arrive, so the first ring travels out, then its reflections appear one by one. Strength: 'wv'.
def wave_mat():
    m = bpy.data.materials.new('waves'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    g = nt.nodes.new('ShaderNodeNewGeometry'); p = sepz(nt, g.outputs['Position']); X, Z = p.outputs['X'], p.outputs['Z']
    sx, sz = CX1, 0.19; t_ = objattr(nt, 'wt'); c_ = 0.09; lam = 0.03
    xs = [sx, 2 * CX0 - sx, 2 * CX1 - (2 * CX0 - sx)]; zs = [sz, 2 * CZ0 - sz, 2 * CZ1 - sz]
    tot = None
    for ix, x0 in enumerate(xs):
        for iz, z0 in enumerate(zs):
            dx = math_(nt, 'SUBTRACT', X, x0); dz = math_(nt, 'SUBTRACT', Z, z0)
            d = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dz, dz)))
            front = math_(nt, 'LESS_THAN', d, math_(nt, 'MULTIPLY', t_, c_))
            ph = math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', d, math_(nt, 'MULTIPLY', t_, c_)), lam))
            crest = math_(nt, 'POWER', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', ph, 2.0), 1.0)), 14.0)
            amp = 1.0 / (1 + 1.6 * (ix + iz))
            term = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', crest, front), amp)
            tot = term if tot is None else math_(nt, 'ADD', tot, term)
    k = math_(nt, 'MULTIPLY', math_(nt, 'MINIMUM', tot, 1.0), objattr(nt, 'wv'))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (0.25, 0.65, 1.0, 1); e_.inputs['Strength'].default_value = 5.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(k, mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
WAVES = box('waves', (CX1 - CX0 - 0.004, 0.0005, CZ1 - CZ0 - 0.004), ((CX0 + CX1) / 2, CY0 + 0.012, (CZ0 + CZ1) / 2), wave_mat())     # just inside the door; WAVES['wv'] = 0.0; WAVES['wt'] = 0.0
WAVES.visible_shadow = False; WAVES.visible_diffuse = False; WAVES.visible_glossy = False
# ---- charges: little glowing specks in the fork that slosh back and forth with the waves, then crowd into the tine tips
CHG_M = emis('charge', (1.0, 0.78, 0.25), 6.0)
CHARGES = []
_rr = random.Random(4)
for i_ in range(46):
    o = prim('uv_sphere', f'chg{i_}', CHG_M, FORK, loc=(0, 0, 0), scale=(0.0006, 0.0006, 0.0006), segments=8, ring_count=6)
    o.visible_shadow = False; x0 = _rr.uniform(0.01, 0.15); k_ = _rr.randrange(4)
    CHARGES.append((o, x0, _rr.uniform(-1, 1), k_, _rr.uniform(0, 6.28)))
def soft_glow(name, col, strength, attr=None, power=2.5):
    # emission that fades to clear toward its silhouette, so a sphere or tube reads as a soft halo, not a disc
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power)
    if attr: fac = math_(nt, 'MULTIPLY', fac, objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')          # additive: a see-through glow
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
GLOW_M = soft_glow('tipglow', (0.65, 0.45, 1.0), 4.0, 'g', 3.0)
HALO_M = soft_glow('arc_halo', (0.45, 0.6, 1.0), 8.0, None, 2.0)
TIP_GLOW = []
for k_, tp in enumerate(TINE_TIPS):
    o = prim('uv_sphere', f'tipglow{k_}', GLOW_M, FORK, loc=tp, scale=(0.0022, 0.0022, 0.0022), segments=16, ring_count=8); o['g'] = 0.0; o.visible_shadow = False; TIP_GLOW.append(o)
# ---- arcs: jagged white-blue lightning between tine tips (or a wire end and the paper), rebuilt every frame, with a flash light
ARC_M = emis('arc', (0.85, 0.9, 1.0), 22.0)
ARC_LT = light_at('arc_lt', 'POINT', (0, 0, 0), (0, 0, 0), 0.0, (0.75, 0.82, 1.0), 0.004)
ARC_OBJS = []
def clear_arcs():
    for o in ARC_OBJS: bpy.data.objects.remove(o, do_unlink=True)
    ARC_OBJS.clear()
def arc(p0, p1, seed, r=0.0007, branches=2):
    rr = random.Random(seed); pts = [p0]; n = 9; d = (p1 - p0); L_ = d.length; side = d.cross(Vector((0, 0, 1))).normalized() if abs(d.normalized().z) < 0.9 else Vector((1, 0, 0))
    up = side.cross(d).normalized()
    for i in range(1, n):
        u = i / n; j = math.sin(u * math.pi) * L_ * 0.28
        pts.append(p0 + d * u + side * rr.uniform(-j, j) * 0.7 + Vector((0, 0, 1)) * (math.sin(u * math.pi) * L_ * 0.45 + rr.uniform(-j, j) * 0.3))   # bows up off the plate
    pts.append(p1); o = tube(f'arc{len(ARC_OBJS)}', pts, r, ARC_M, seg=6); o.visible_shadow = False; ARC_OBJS.append(o)
    h = tube(f'arch{len(ARC_OBJS)}', pts, r * 3.5, HALO_M, seg=8); h.visible_shadow = False; h.visible_diffuse = False; h.visible_glossy = False; ARC_OBJS.append(h)
    for b in range(branches):
        i0 = rr.randrange(2, n - 2); q = pts[i0]; dd = (side * rr.uniform(-1, 1) + up * rr.uniform(-0.5, 1)).normalized() * L_ * rr.uniform(0.2, 0.4)
        bp = [q, q + dd * 0.5 + side * rr.uniform(-1, 1) * L_ * 0.05, q + dd]; ob = tube(f'arcb{len(ARC_OBJS)}', bp, r * 0.5, ARC_M, seg=5); ob.visible_shadow = False; ARC_OBJS.append(ob)
    return pts

# ================================================================ timing, the turntable, the camera (one take: rests on each idea, flies between them)
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))
RPM = 2.4
def tt_angle(t): return R(-40) + 2 * math.pi * RPM / 60.0 * t
def tt_mat(t): return Matrix.Translation(TT_C) @ Matrix.Rotation(tt_angle(t), 4, 'Z')
# keys: (time, frame, position, target, lens, f-stop). frame 't' = riding on the turntable (inside the oven, close on the fork),
# 'w' = the world (outside, the oven on the counter). Every key is a rest: the camera eases in and out of it.
K = [
    (0.00, 't', (0.060, -0.110, 0.066), (0.002, -0.024, 0.024), 52, 110),     # frame one: the fork's tips already sparking
    (2.55, 't', (0.064, -0.113, 0.069), (0.002, -0.024, 0.024), 52, 110),
    (4.05, 'w', (-0.02, -0.95, 0.20), (-0.02, 0.0, 0.15), 40, 8),             # out through the door: the oven on the counter
    (5.45, 'w', (-0.01, -0.90, 0.19), (-0.02, 0.0, 0.15), 40, 8),
    (6.45, 'w', (-0.03, -0.56, 0.16), (-0.05, 0.0, 0.135), 35, 8),            # closer; the walls show their metal
    (8.20, 'w', (-0.035, -0.52, 0.155), (-0.05, 0.0, 0.135), 35, 8),
    (9.20, 'w', (-0.055, -0.40, 0.14), (-0.055, 0.0, 0.14), 32, 8),           # square on to the slice: the waves bouncing
    (12.45, 'w', (-0.055, -0.38, 0.137), (-0.055, 0.0, 0.14), 32, 8),
    (13.75, 't', (0.082, -0.118, 0.073), (0.002, -0.024, 0.024), 50, 110),    # in through the door to the fork's shape
    (14.75, 't', (0.079, -0.115, 0.070), (0.002, -0.024, 0.024), 50, 110),
    (17.30, 't', (0.057, -0.108, 0.063), (0.001, -0.024, 0.023), 55, 110),    # slowly closer while the charges slosh
    (19.85, 't', (0.047, -0.103, 0.060), (-0.001, -0.024, 0.023), 55, 110),    # right on the tips as they pile up
    (21.60, 't', (0.043, -0.100, 0.058), (-0.001, -0.024, 0.023), 55, 110),
    (24.35, 't', (0.039, -0.097, 0.056), (-0.001, -0.024, 0.023), 55, 110),   # hold close through the spark
    (25.55, 't', (0.070, -0.120, 0.090), (-0.010, 0.005, 0.030), 38, 64),     # back: lightning right next to the dinner
    (26.65, 't', (0.074, -0.122, 0.092), (-0.010, 0.005, 0.030), 38, 64),
    (27.85, 't', (0.004, -0.008, 0.112), (-0.080, 0.058, 0.068), 22, 64),     # the takeout box and its wire handle
    (31.00, 't', (0.008, -0.012, 0.108), (-0.080, 0.058, 0.068), 22, 64),
    (32.00, 't', (0.020, -0.060, 0.130), (0.025, 0.062, 0.026), 34, 64),     # the smooth spoon
    (34.05, 't', (0.016, -0.056, 0.126), (0.025, 0.062, 0.026), 34, 64),
    (35.25, 't', (0.070, -0.120, 0.100), (-0.012, 0.020, 0.026), 38, 64),     # fork and spoon together: it's the points
    (36.90, 't', (0.073, -0.122, 0.098), (-0.012, 0.020, 0.026), 38, 64),
    (38.60, 'w', (-0.10, -0.80, 0.22), (-0.05, 0.0, 0.14), 35, 8),            # out to the kitchen
    (39.60, 'w', (-0.09, -0.78, 0.215), (-0.05, 0.0, 0.14), 35, 8),
    (END, 't', (0.060, -0.110, 0.066), (0.002, -0.024, 0.024), 52, 110),      # back in to frame one (loop)
]
def key_world(k, t):
    _, fr, p, q, ln, fs = k
    if fr == 'w': return Vector(p), Vector(q)
    M = tt_mat(t); return M @ Vector(p), M @ Vector(q)
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    u = clamp((t - ts[i]) / (ts[i + 1] - ts[i]), 0, 1); s = u * u * (3 - 2 * u)            # zero speed at every key (rests)
    return vs[i] * (1 - s) + vs[i + 1] * s
def cam_at(t):
    ts = [k[0] for k in K]; pq = [key_world(k, t) for k in K]
    p = herm(ts, [a_ for a_, _ in pq], t); q = herm(ts, [b_ for _, b_ in pq], t)
    ln = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[5], 0, 0)) for k in K], t).x
    inside = p.y > -0.19
    sh = shake(t, 0.0006 if inside else 0.002, 5.0, 0.6)
    for ts_, amp in BIG_FLASH:
        if ts_ < t < ts_ + 0.35: sh += shake(t, amp * (1 - (t - ts_) / 0.35), 2.0, 16.0)
    return p + sh, q + sh * 0.5, ln, fs

# ---- the spark schedule: (time, kind, a, b) kind 'tt' = between tine tips a and b, 'wire' = at the carton's wire end a
SPARKS = [(0.05, 'tt', 1, 2), (0.80, 'tt', 0, 1), (1.62, 'tt', 2, 3), (2.40, 'tt', 1, 2),
          (T_EXPLODE - 0.15, 'tt', 0, 1), (T_EXPLODE, 'tt', 1, 3), (T_EXPLODE + 0.2, 'tt', 2, 3),
          (T_SPARK, 'tt', 1, 2), (T_SPARK + 0.32, 'tt', 0, 1), (T_BOLT - 0.1, 'tt', 2, 3), (T_BOLT + 0.35, 'tt', 0, 2), (T_BOLT + 0.8, 'tt', 1, 3),
          (T_BOLT + 1.25, 'tt', 0, 1), (T_BOLT + 1.7, 'tt', 2, 3)]
SPARKS += [(T_PAPER + 0.45 + 0.33 * i_, 'wire', 1, 0) for i_ in range(int((T_FIRE - T_PAPER) / 0.33))]
SPARKS += [(31.6, 'tt', 1, 2), (32.9, 'tt', 0, 1), (T_POINTS - 0.1, 'tt', 0, 1), (T_POINTS + 0.1, 'tt', 2, 3), (T_POINTS + 0.35, 'tt', 1, 2),
           (38.1, 'tt', 1, 2), (39.3, 'tt', 0, 1), (40.25, 'tt', 2, 3)]
SPARK_LEN = 0.12
BIG_FLASH = [(T_EXPLODE, 0.004), (T_SPARK, 0.0018)]

def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    TT.rotation_euler = (0, 0, tt_angle(t))
    for o in [x for x in bpy.data.objects if x.name == 'tt_ring']: o.rotation_euler = (0, 0, tt_angle(t))
    BULB.data.energy = 6.0
    # x-ray: the door clears whenever the camera flies through it or looks in; the enamel walls show bare metal for "made of metal"
    door = max(win(t, 2.65, 3.95, 0.12), win(t, T_METAL - 1.4, 13.55, 0.35), win(t, 37.35, 38.45, 0.12), ease_io((t - 39.65) / 0.12))
    for o in DOOR.children: o['xr'] = door
    walls = win(t, T_METAL - 1.0, T_SHAPE - 0.2, 0.5)
    for o in CAV: o['xr'] = walls
    # waves out of the waveguide, bouncing; the food soaks them up and warms
    WAVES['wv'] = win(t, T_BOUNCE - 0.5, T_SHAPE - 0.6, 0.4); WAVES['wt'] = max(0.0, t - (T_BOUNCE - 0.6)); WAVES.hide_render = WAVES['wv'] < 0.01
    FOOD['heat'] = MAC['heat'] = 0.55 * win(t, T_FOOD - 0.5, T_SHAPE + 0.8, 0.6)
    # charges in the fork: slosh with the waves, then crowd into the tips, then gone with the spark
    on = T_SHOVE - 0.4 < t < T_SPARK + 0.25
    pile = ease_io((t - (T_PILE - 0.4)) / 1.4)
    for o, x0, yy, k_, ph in CHARGES:
        o.hide_render = not on
        if not on: continue
        tip = TINE_TIPS[k_]
        xs = clamp(x0 + 0.018 * math.sin(2 * math.pi * 1.1 * t + ph), 0.006, 0.186)
        w = 0.0092 if xs < 0.098 else (0.0040 if xs < 0.135 else 0.0105)
        ys = (yy * w * 0.7) if xs < 0.15 else (tip.y + yy * 0.0008)
        xp = tip.x - 0.003 - 0.016 * ((ph * 7.3) % 1.0) ** 1.6; yp = tip.y + yy * 0.8 * min(0.0019, 0.0003 + (tip.x - xp) * 0.22)
        o.location = (xs + (xp - xs) * pile, ys + (yp - ys) * pile, 0.0026)
        s_ = 1.0; o.scale = (s_, s_, s_)
    g = 0.0 if t > T_SPARK - 0.02 else 0.35 * ease_io((t - T_PILE) / 1.2) + 0.65 * ease_io((t - T_AIR) / (T_SPARK - T_AIR))
    g += 0.6 * win(t, T_POINTS - 0.5, T_POINTS + 0.7, 0.2)
    for o in TIP_GLOW: o['g'] = g; o.hide_render = g < 0.01
    # the arcs live for a few frames each; a light flashes with them
    clear_arcs(); fl = 0.0; fpos = None
    Mf = FORK.matrix_world.copy(); Mc = CARTON.matrix_world.copy()
    for i_, (ts_, kind, a_, b_) in enumerate(SPARKS):
        if ts_ <= t < ts_ + SPARK_LEN:
            u = (t - ts_) / SPARK_LEN; seed = i_ * 31 + int(t * 120)
            if kind == 'tt':
                p0 = Mf @ TINE_TIPS[a_]; p1 = Mf @ TINE_TIPS[b_]
                rr_ = random.Random(i_ * 7 + int(t * 60)); fly = Mf @ (TINE_TIPS[a_] + Vector((0.006 + 0.004 * rr_.random(), rr_.uniform(-0.004, 0.004), 0.004 + 0.004 * rr_.random())))
                arc(p0, fly, seed + 5, 0.0006, 1)
            else: p0 = Mc @ WIRE_ENDS[a_]; p1 = Mc @ (WIRE_ENDS[a_] + Vector((0.004 if a_ else -0.004, -0.008, -0.016)))
            arc(p0, p1, seed, 0.00045 * (1.4 if ts_ in [x for x, _ in BIG_FLASH] else 1.0)); fl = max(fl, 1 - u); fpos = (p0 + p1) / 2
    ARC_LT.data.energy = 0.35 * fl
    if fpos is not None: ARC_LT.location = fpos
    # the paper catches: a small flame grows on the box corner, then dies down to a lick
    fa = ease_out((t - (T_FIRE - 0.35)) / 0.7) * (1 - 0.65 * ease_io((t - 31.0) / 2.0))
    for f in FLAMES: f['fa'] = fa; f['ft'] = t; f.hide_render = fa < 0.01
    FIRE_LT.data.energy = 0.35 * fa * (0.8 + 0.2 * math.sin(t * 37) * math.sin(t * 13))

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, fs = cam_at(tt_); look(cp, ct, ln, fs); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
    cp, ct, ln, fs = cam_at(t)
    if not (t > d and t < END - d): look(cp, ct, ln, fs)
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

