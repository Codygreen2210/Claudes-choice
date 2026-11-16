# An egg in the microwave: why a reheated hard boiled egg blows up. Blender Cycles, ONE continuous camera move (no cuts),
# resting on each idea; inside the oven, then down on the kitchen floor with the engineers' eggs, microphone and thermometer.
#   python3 egg.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
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
T_STOP = B[1] - 0.25                           # the oven beeps off at the end of line 0
T_DOOR = word_t(1, 1)                          # "comes out": the door swings open
T_TOUCH = word_t(2, 5)                         # "touches"
T_BANG1 = word_t(2, 9)                         # "blows apart"
T_GRID = word_t(4, 6)                          # "almost a hundred eggs"
T_MIC = word_t(5, 8)                           # "microphone"
T_STAB = word_t(5, 11)                         # "stabbed it"
T_BANG2 = word_t(6, 1)                         # "The loudest"
T_JET = word_t(6, 8)                           # "a jet plane"
T_XRAY = word_t(7, 5)                          # "the trick"
T_DROPS = word_t(8, 0)                         # "Tiny drops"
T_HOT = word_t(8, 12)                          # "heat up past boiling"
T_POKE = word_t(9, 2)                          # "poke it"
T_FLASH = word_t(9, 6)                         # "flashes to steam"
T_CHAIN = word_t(9, 10)                        # "sets off all the others"
T_BOIL = word_t(10, 6)                         # "boils apart"
T_ROUL = word_t(11, 6)                         # "blew up"
T_RESET = B[5] + 0.5                           # the oven is set up again while the camera is down on the floor (it can't see the oven)
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
cbox('mw_bot', (MW_W, MW_D, 0.032), (0, -0.0, 0.016))          # top sits just under the cavity floor (no z-fight)
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

# ================================================================ the egg props: a peeled hard boiled egg on a plate in the oven, the fork,
# the kitchen floor with the engineers' hundred eggs, a microphone a foot from the test egg, a meat thermometer, the x-ray egg.
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))

# ---- the door swings on a hinge at its left edge (rotate the hinge about z; negative opens it toward us)
HINGE = empty('hinge', loc=(DOOR_X0, -MW_D / 2 - 0.004, 0)); DOOR.parent = HINGE; DOOR.location = (-DOOR_X0, 0, 0)

# ---- the plate (centered on the turntable) and the egg
CERAMIC = mat('ceramic', (0.05, 0.22, 0.30), 0.10, coat=1.0)                # deep teal: the white egg pops on it
PLATE = lathe('plate', [(0.0, 0.0205), (0.06, 0.0205), (0.068, 0.022), (0.088, 0.031), (0.095, 0.0325), (0.096, 0.031), (0.086, 0.0265), (0.066, 0.0225),
                        (0.058, 0.0215), (0.0, 0.0215)], 64, CERAMIC, TT)
EGG_L, EGG_R = 0.0285, 0.0215                                                # a large egg: 5.7 cm long, 4.3 cm wide
def egg_mesh(name, seg=48):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co; k = 1.0 - 0.12 * x                                    # the narrow end is +x
        v.co = Vector((x * EGG_L, y * EGG_R * k, z * EGG_R * k))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return me
EGG_ME = egg_mesh('egg')
def egg_white_mat(name='egg_white'):
    m = mat(name, (0.93, 0.92, 0.86), 0.22, coat=0.5); b = N(m)['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.45; b.inputs['Subsurface Radius'].default_value = (1.0, 0.85, 0.6); b.inputs['Subsurface Scale'].default_value = 0.004
    return m
EGG_M = egg_white_mat(); EGG_ME.materials.append(EGG_M)            # shared mesh: one material on the mesh, objects add none
YOLK_M = noisy(mat('yolk', (0.95, 0.60, 0.07), 0.8), 600.0, 0.18, 0.1)
EGG_LOCAL = Vector((0.02, 0.0, 0.0215 + EGG_R))                            # on the plate, a little off center so it travels as the plate turns
EGG1 = obj('egg1', EGG_ME, None, loc=EGG_LOCAL, parent=TT); EGG1.rotation_euler = (0, 0, R(70))

# ---- the fork: 19 cm stainless; FORKP sits at the tine tips and its local +x points the way the fork is going
FORK_M = mat('stainless', (0.80, 0.80, 0.82), 0.16, 1.0, coat=0.2)
def flat_shape(name, outline, th, m, parent, loc=(0, 0, 0)):
    bm = bmesh.new(); vs = [bm.verts.new((x, y, 0.0)) for x, y in outline]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, th), verts=[e for e in ex['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj(name, me, m, loc=loc, parent=parent); md = o.modifiers.new('bv', 'BEVEL'); md.width = th * 0.45; md.segments = 3; md.limit_method = 'ANGLE'
    o.modifiers.new('wn', 'WEIGHTED_NORMAL')
    for p_ in me.polygons: p_.use_smooth = True
    return o
FORKP = empty('forkp'); FORKP.rotation_mode = 'QUATERNION'
_fi = empty('fork_in', FORKP, loc=(-0.19, 0, -0.0011))
_h = [(0.0, 0.0105), (0.012, 0.0118), (0.05, 0.0095), (0.098, 0.0042), (0.118, 0.0036), (0.135, 0.0062), (0.148, 0.0118), (0.152, 0.0122)]
FORK_PARTS = [flat_shape('fork_body', [(x, y) for x, y in _h] + [(x, -y) for x, y in reversed(_h)], 0.0024, FORK_M, _fi)]
for k_ in range(4):
    yc = -0.0092 + 0.00613 * k_; w = 0.0021
    FORK_PARTS.append(flat_shape(f'tine{k_}', [(0.150, yc - w), (0.182, yc - w * 0.9), (0.190, yc), (0.182, yc + w * 0.9), (0.150, yc + w)], 0.0022, FORK_M, _fi))

def obj_coords(m, rot=(0, 0, 0)):
    nt = m.node_tree; tc = next(n for n in nt.nodes if n.type == 'TEX_COORD'); mp = next(n for n in nt.nodes if n.type == 'MAPPING')
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); mp.inputs['Rotation'].default_value = rot; return m
for o_ in bpy.data.objects:
    if o_.name == 'cabinet': obj_coords(o_.data.materials[0], (R(90), 0, 0))
    if o_.name == 'counter': obj_coords(o_.data.materials[0])
# ---- the kitchen floor (the cabinet stands on it) and a light for it
FLOOR_Z = -0.90
box('floor', (4.0, 4.0, 0.02), (0, -0.9, FLOOR_Z - 0.01), obj_coords(P.material('ph:oak_veneer_01', scale=1.5)))
box('toekick', (1.6, 0.02, 0.09), (0, -0.215, FLOOR_Z + 0.045), mat('toe', (0.05, 0.05, 0.05), 0.6))
FKEY = light_at('floor_key', 'AREA', (-0.55, -1.95, -0.25), (0.0, -1.0, -0.9), 16, (1.0, 0.95, 0.88), 0.9)
FFILL = light_at('floor_fill', 'AREA', (0.9, -1.4, -0.45), (0.0, -1.0, -0.9), 5, (0.85, 0.9, 1.0), 0.6)

# ---- the engineers' eggs: almost a hundred, in rows on the floor; the test egg A with the microphone a foot away; egg B for the x-ray
FLOOR_EGG_Z = FLOOR_Z + EGG_R
GRID = []; _rr = random.Random(11)
for j_ in range(10):
    for i_ in range(10):
        if (i_, j_) in ((0, 0), (9, 0)): continue                                       # 98 of them: "almost a hundred"
        p = Vector((-0.34 + 0.0755 * i_ + _rr.uniform(-0.01, 0.01), -0.42 - 0.072 * j_ + _rr.uniform(-0.008, 0.008), FLOOR_EGG_Z))
        o = obj(f'gegg{len(GRID)}', EGG_ME, None, loc=p); o.rotation_euler = (0, 0, _rr.uniform(0, math.pi)); GRID.append(o)
A_C = Vector((0.05, -1.24, FLOOR_EGG_Z)); B_C = Vector((-0.17, -1.21, FLOOR_EGG_Z))
EGGA = obj('egga', EGG_ME, None, loc=A_C); EGGA.rotation_euler = (0, 0, R(100))
# egg B: its white turns to glass for the x-ray ('xr'), the yolk shows through, the trapped drops glow inside it
EGGX_M = xray_mat('egg_x', (0.93, 0.92, 0.86), 0.22)
EGGB = obj('eggb', egg_mesh('eggb'), EGGX_M, loc=B_C); EGGB.rotation_euler = (0, 0, R(-8)); EGGB['xr'] = 0.0
def yolk_x_mat():
    m = mat('yolk_x', (0.95, 0.60, 0.07), 0.7); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (1.0, 0.42, 0.08, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'heat'), 2.5), b.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', objattr(nt, 'xr'), 0.6)), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
YOLKB = prim('uv_sphere', 'yolkb', yolk_x_mat(), loc=B_C + Vector((-0.002, 0, 0.0)), scale=(0.0118, 0.0118, 0.0118), segments=32, ring_count=16)
YOLKB['xr'] = 0.0; YOLKB['heat'] = 0.0
def drop_mat():
    m = bpy.data.materials.new('drop'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    c_ = mixc(nt, objattr(nt, 'h'), (0.45, 0.75, 1.0), (1.0, 0.5, 0.12)); c_ = mixc(nt, objattr(nt, 'f'), c_, (1.0, 0.95, 0.85))
    e_ = nt.nodes.new('ShaderNodeEmission'); nt.links.new(c_, e_.inputs['Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'ADD', 3.0, math_(nt, 'MULTIPLY', objattr(nt, 'h'), 5.0)), math_(nt, 'MULTIPLY', objattr(nt, 'f'), 30.0)), e_.inputs['Strength'])
    nt.links.new(e_.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
DROP_M = drop_mat(); DROPS = []
_rr = random.Random(5)
while len(DROPS) < 42:
    p = Vector((_rr.uniform(-1, 1), _rr.uniform(-1, 1), _rr.uniform(-1, 1)))
    if p.length > 1.0: continue
    d = prim('ico_sphere', f'drop{len(DROPS)}', DROP_M, loc=YOLKB.location + p * 0.0092, subdivisions=2, radius=_rr.uniform(0.0009, 0.0014))
    d['h'] = 0.0; d['f'] = 0.0; d['home'] = tuple(d.location); d.hide_render = True; DROPS.append(d)
POKE_B = B_C + Vector((0.004, 0.0, EGG_R))                                     # where the thermometer goes into egg B (the top)
_dd = [(Vector(x['home']) - POKE_B).length for x in DROPS]
DROP0 = min(range(len(DROPS)), key=lambda i: _dd[i]); _dmax = max(_dd); _dmin = min(_dd)

# ---- the microphone a foot from egg A, on a little stand, pointing at it
MIC_M = mat('mic', (0.03, 0.03, 0.035), 0.35, 0.6); GRILLE_M = mat('grille', (0.22, 0.22, 0.23), 0.45, 1.0)
MIC = empty('mic', loc=A_C + Vector((0.30, 0.0, 0.045))); MIC.rotation_euler = (0, R(-12), 0)
prim('uv_sphere', 'mic_grille', GRILLE_M, MIC, scale=(0.011, 0.011, 0.011), segments=24, ring_count=12)
tube('mic_body', [(0.008, 0, 0), (0.05, 0, 0), (0.095, 0, 0)], lambda u: 0.0095 - 0.003 * u, MIC_M, MIC)
MIC_STAND = []
_hub = A_C + Vector((0.35, 0.0, 0.025))
MIC_STAND.append(tube('mic_rod', [_hub + Vector((0, 0, 0.012)), _hub + Vector((0, 0, -0.01)), _hub + Vector((0, 0, -0.03))], 0.0025, MIC_M))
for k_ in range(3):
    a_ = R(90 + 120 * k_); MIC_STAND.append(tube(f'mic_leg{k_}', [_hub, _hub + Vector((math.cos(a_) * 0.03, math.sin(a_) * 0.03, -0.024)), _hub + Vector((math.cos(a_) * 0.05, math.sin(a_) * 0.05, -0.0455))], 0.0018, MIC_M))
tube('mic_cable', [A_C + Vector((0.395, 0, 0.04)), A_C + Vector((0.43, 0.02, 0.0)), A_C + Vector((0.47, 0.05, -0.0205)), A_C + Vector((0.7, 0.2, -0.0205))], 0.0022, MIC_M)

# ---- the meat thermometer: THERM sits at the probe tip, the probe runs up its local +z to a round dial
THERM = empty('therm'); THERM.rotation_euler = (R(-14), R(10), 0)
_tm = mat('probe', (0.82, 0.82, 0.84), 0.2, 1.0)
lathe('probe', [(0.0, 0.0), (0.0019, 0.009), (0.0019, 0.125), (0.0, 0.125)], 24, _tm, THERM)
lathe('dial_case', [(0.0, 0.124), (0.008, 0.124), (0.024, 0.128), (0.025, 0.134), (0.024, 0.140), (0.0, 0.140)], 48, _tm, THERM)
_dial = lathe('dial_face', [(0.0, 0.1405), (0.0215, 0.1405), (0.0215, 0.1406), (0.0, 0.1406)], 48, mat('dialface', (0.95, 0.95, 0.93), 0.4), THERM)
box('needle', (0.002, 0.016, 0.0008), (0.0, 0.006, 0.1412), mat('needle', (0.85, 0.05, 0.03), 0.4), parent=THERM)

# ================================================================ bursts: chunks of white and yolk that fly, hit walls and floor, and slide to a stop
def soft_glow(name, col, strength, attr=None, power=2.5):
    # emission that fades to clear toward its silhouette, so a sphere or tube reads as a soft halo, not a disc
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power)
    if attr: fac = math_(nt, 'MULTIPLY', fac, objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')          # additive: a see-through glow
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
CHUNK_ME = {False: [], True: []}
_rr = random.Random(21)
for yolk_ in (False, True):
    for k_ in range(8):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); fl = _rr.uniform(0.35, 0.7)
        for v in bm.verts: v.co = Vector((v.co.x * _rr.uniform(0.7, 1.3), v.co.y * _rr.uniform(0.7, 1.3), v.co.z * fl))
        me = bpy.data.meshes.new(f'chunk{int(yolk_)}{k_}'); bm.to_mesh(me); bm.free(); [setattr(p_, 'use_smooth', True) for p_ in me.polygons]; me.materials.append(YOLK_M if yolk_ else EGG_M); CHUNK_ME[yolk_].append(me)
STEAM_M = soft_glow('steam', (0.85, 0.87, 0.9), 0.15, 'g', 3.0)
POP_LT = light_at('pop_lt', 'POINT', (0, 0, 0), (0, 0, 0), 0.0, (1.0, 0.92, 0.8), 0.01)
BURSTS = []
class Burst:
    def __init__(s, name, t0, c, nW, nY, seed, spd=(0.5, 1.8), up=0.7, box_=None, floor=None, size=1.0, steam=4, flash=1.0):
        rr = random.Random(seed); s.t0, s.c, s.box, s.floor, s.flash = t0, Vector(c), box_, floor, flash; s.parts = []; s.steam = []
        for i in range(nW + nY):
            yolk = i >= nW; d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized()
            p0 = Vector((d.x * EGG_L, d.y * EGG_R, d.z * EGG_R)) * (0.35 if yolk else 0.8)
            v = (d + Vector((0, 0, up))).normalized() * rr.uniform(*spd) * (0.8 if yolk else 1.0)
            r = (rr.uniform(0.0018, 0.0042) if yolk else rr.uniform(0.0025, 0.0075)) * size
            o = obj(f'{name}_c{i}', CHUNK_ME[yolk][rr.randrange(8)], None); o.scale = (r, r, r); o.hide_render = True
            s.parts.append((o, p0, v, r, Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1))) * rr.uniform(8, 25)))
        for i in range(steam):
            o = prim('uv_sphere', f'{name}_st{i}', STEAM_M, scale=(1, 1, 1), segments=20, ring_count=10); o['g'] = 0.0; o.hide_render = True
            s.steam.append((o, Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(0.2, 1))).normalized() * rr.uniform(0.01, 0.04) * size, rr.uniform(0.014, 0.03) * size, rr.uniform(0.9, 1.6)))
        BURSTS.append(s)
    def floor_at(s, x, y): return s.floor(x, y) if callable(s.floor) else s.floor
    def update(s, t):
        on = t >= s.t0; dt = max(0.0, t - s.t0); k = 3.0; g = 9.8; h = (1 - math.exp(-k * dt)) / k
        for o, p0, v, r, spin in s.parts:
            o.hide_render = not on
            if not on: continue
            x = s.c.x + p0.x + v.x * h; y = s.c.y + p0.y + v.y * h; z = s.c.z + p0.z + (v.z + g / k) * h - g * dt / k
            if s.box:
                (x0, x1), (y0, y1), z1 = s.box
                x = clamp(x, x0 + r, x1 - r); y = min(y, y1 - r); z = min(z, z1 - r)
            fz = s.floor_at(x, y) + r * 0.55
            if z < fz: z = fz
            o.location = (x, y, z); o.rotation_euler = (spin.x * h, spin.y * h, spin.z * h)
        for o, dv, rad, life in s.steam:
            u = dt / life; o.hide_render = not on or u > 1.0
            if o.hide_render: continue
            sc = rad * (0.4 + 1.6 * ease_out(u * 1.5)); o.scale = (sc, sc, sc); o.location = s.c + dv * (1 + 6 * u) + Vector((0, 0, 0.05 * u))
            o['g'] = (1 - u) ** 1.5 * ease_out(dt / 0.05)
    def light(s, t): return s.flash * max(0.0, 1 - (t - s.t0) / 0.18) if t >= s.t0 else 0.0

# shockwave from egg A: a flat ring along the floor and a faint bubble, both swelling past the microphone
def edge_glow(name, col, strength, attr, power=3.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], power), objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
WAVE_M = edge_glow('shock', (0.75, 0.88, 1.0), 3.0, 'g', 2.5)
SHOCK = prim('uv_sphere', 'shock', WAVE_M, loc=A_C, segments=48, ring_count=24); SHOCK['g'] = 0.0; SHOCK.hide_render = True
SHOCK_RING = lathe('shock_ring', [(1.0 + 0.012 * math.cos(2 * math.pi * k / 12), 0.012 * math.sin(2 * math.pi * k / 12)) for k in range(13)], 96, soft_glow('ring', (0.8, 0.9, 1.0), 6.0, 'g', 1.0))
SHOCK_RING['g'] = 0.0; SHOCK_RING.hide_render = True
# the glass turntable would throw a black shadow over the whole oven floor (no caustics): let light through it
for o_ in bpy.data.objects:
    if o_.name == 'tt_plate': o_.visible_shadow = False

# ================================================================ timing, the turntable, the camera (one take: rests on each idea, flies between them)
RPM = 5.0
W_TT = 2 * math.pi * RPM / 60.0; A0_TT = R(-40)
def tt_angle(t):
    if t < T_STOP: return A0_TT + W_TT * t
    if t < T_RESET: return A0_TT + W_TT * T_STOP
    return A0_TT + W_TT * (t - END)                     # set going again off camera, so the end runs straight into frame one
def tt_mat(t): return Matrix.Translation(TT_C) @ Matrix.Rotation(tt_angle(t), 4, 'Z')
E1 = tt_mat(T_STOP) @ EGG_LOCAL                       # where the oven egg sits once the plate stops
EM = TT_C + Vector((0, 0, EGG_LOCAL.z))              # the middle of its little circle
# keys: (time, position, target, lens, f-stop), all in the world. Every key is a rest: the camera eases in and out of it.
K = [
    (0.00, (-0.005, -0.135, 0.118), (-0.055, -0.005, 0.074), 30, 64),      # frame one: the egg turning in the running oven
    (2.90, (-0.012, -0.128, 0.112), (-0.055, -0.005, 0.074), 30, 64),
    (4.60, (-0.035, -0.360, 0.150), (-0.055, -0.005, 0.070), 38, 32),      # out through the opening door: it looks totally normal
    (5.30, (-0.034, -0.370, 0.152), (-0.055, -0.005, 0.070), 38, 32),
    (T_TOUCH - 0.25, (0.020, -0.160, 0.115), tuple(E1), 34, 64),            # in close as the fork touches it
    (T_BANG1 + 0.9, (0.024, -0.166, 0.118), tuple(E1), 34, 64),
    (9.60, (-0.010, -0.240, 0.140), (-0.055, 0.000, 0.070), 30, 32),       # egg all over the oven
    (11.00, (-0.050, -0.620, 0.200), (-0.050, 0.000, 0.120), 35, 16),
    (13.20, (0.000, -1.620, -0.500), (0.000, -0.780, -0.880), 28, 16),     # down to the floor: almost a hundred eggs
    (15.20, (0.004, -1.660, -0.520), (0.000, -0.780, -0.880), 28, 16),
    (16.60, (-0.140, -1.320, -0.830), (0.170, -1.240, -0.875), 30, 22),     # the test egg, the microphone a foot away, the thermometer
    (19.00, (-0.142, -1.322, -0.828), (0.170, -1.240, -0.875), 30, 22),
    (21.00, (-0.150, -1.335, -0.822), (0.170, -1.240, -0.875), 30, 22),     # hold through the bang
    (23.60, (-0.170, -1.370, -0.835), (-0.170, -1.210, -0.878), 38, 32),   # egg B: the x-ray
    (25.40, (-0.170, -1.366, -0.837), (-0.170, -1.210, -0.878), 38, 32),
    (27.40, (-0.170, -1.338, -0.846), (-0.171, -1.210, -0.878), 40, 45),   # into the yolk: the trapped drops
    (30.20, (-0.170, -1.334, -0.848), (-0.171, -1.210, -0.878), 40, 45),
    (31.00, (-0.166, -1.338, -0.838), (-0.170, -1.210, -0.872), 40, 45),   # the poke and the chain
    (T_BOIL - 0.05, (-0.166, -1.342, -0.838), (-0.170, -1.210, -0.872), 40, 45),
    (T_BOIL + 0.90, (-0.160, -1.380, -0.825), (-0.170, -1.210, -0.874), 36, 32),
    (38.60, (0.000, -1.700, -0.420), (0.000, -0.760, -0.890), 26, 16),     # high over the rows: egg roulette
    (42.30, (0.020, -1.720, -0.400), (0.000, -0.760, -0.890), 26, 16),
    (44.40, (-0.050, -0.800, 0.200), (-0.050, 0.000, 0.130), 35, 16),      # back up: the oven running again
    (45.00, (-0.048, -0.780, 0.198), (-0.050, 0.000, 0.130), 35, 16),
    (END, (-0.005, -0.135, 0.118), (-0.055, -0.005, 0.074), 30, 64),
]
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    u = clamp((t - ts[i]) / (ts[i + 1] - ts[i]), 0, 1); s = u * u * (3 - 2 * u)            # zero speed at every key (rests)
    return vs[i] * (1 - s) + vs[i + 1] * s
BIG_FLASH = [(T_BANG1, 0.004), (T_BANG2, 0.006), (T_BOIL, 0.003)]
def cam_at(t):
    ts = [k[0] for k in K]
    p = herm(ts, [Vector(k[1]) for k in K], t); q = herm(ts, [Vector(k[2]) for k in K], t)
    ln = herm(ts, [Vector((k[3], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x
    close = p.z > -0.2 and p.y > -0.3
    sh = shake(t, 0.0006 if close else 0.0015, 5.0, 0.6)
    for ts_, amp in BIG_FLASH:
        if ts_ < t < ts_ + 0.35: sh += shake(t, amp * (1 - (t - ts_) / 0.35), 2.0, 16.0)
    return p + sh, q + sh * 0.5, ln, fs
_tc = [t_ / 100 for t_ in range(4400, int(END * 100))]
T_IN = next((t_ for t_ in _tc if herm([k[0] for k in K], [Vector(k[1]) for k in K], t_).y > -MW_D / 2 - 0.02), END - 0.3)   # the end flight goes in through the door

# ---- the bursts: the oven egg, test egg A, x-ray egg B, and about one in three of the floor eggs (egg roulette)
def oven_floor(x, y):
    if y < CY0: return 0.0 if y < -MW_D / 2 - 0.01 else CZ0
    dxy = math.hypot(x - TT_C.x, y - TT_C.y)
    if dxy < 0.096: return TT_C.z + 0.0215
    if dxy < 0.135: return TT_C.z + 0.02
    return CZ0
BURST1 = Burst('b1', T_BANG1, E1, 70, 26, 3, spd=(0.3, 1.2), up=0.5, box_=((CX0, CX1), (CY0 - 0.05, CY1), CZ1), floor=oven_floor, size=0.9, steam=2, flash=1.0)
BURSTA = Burst('ba', T_BANG2, A_C, 70, 26, 7, spd=(0.6, 2.2), up=0.6, floor=FLOOR_Z, size=1.0, steam=0, flash=1.4)
BURSTB = Burst('bb', T_BOIL, B_C, 60, 26, 8, spd=(0.5, 1.8), up=0.6, floor=FLOOR_Z, size=1.0, steam=0, flash=1.2)
_rr = random.Random(33); ROUL = []
_pick = _rr.sample(range(len(GRID)), 33)
_tr0, _tr1 = T_ROUL - 0.15, B[13] + 0.6
for k_, gi in enumerate(_pick):
    t0 = _tr0 + (_tr1 - _tr0) * (k_ + _rr.uniform(-0.3, 0.3)) / len(_pick)
    ROUL.append((GRID[gi], Burst(f'r{k_}', t0, GRID[gi].location.copy(), 14, 5, 100 + k_, spd=(0.35, 1.1), up=0.8, floor=FLOOR_Z, size=0.8, steam=0, flash=0.35)))
ROUL_T = {id(o): b.t0 for o, b in ROUL}

# ---- the thermometer's path (tip position), eased between keys; hidden before and after
A_TOP = A_C + Vector((0, 0, EGG_R))
TK = [(T_MIC - 1.2, A_TOP + Vector((-0.03, 0.04, 0.26))), (T_STAB - 0.15, A_TOP + Vector((0, 0, 0.03))), (T_STAB, A_TOP + Vector((0, 0, -0.012))),
      (T_BANG2, A_TOP + Vector((0, 0, -0.012))), (T_BANG2 + 0.3, A_TOP + Vector((0, 0, 0.08))), (T_POKE - 0.5, POKE_B + Vector((0, 0, 0.04))),
      (T_POKE, POKE_B + Vector((0, 0, -0.008))), (T_BOIL, POKE_B + Vector((0, 0, -0.008))), (T_BOIL + 0.7, POKE_B + Vector((0.02, 0.03, 0.26)))]
THERM_KIDS = list(THERM.children)
def therm_at(t):
    ts = [k[0] for k in TK]; return herm(ts, [k[1] for k in TK], t)

def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    a_ = tt_angle(t); TT.rotation_euler = (0, 0, a_)
    for o in [x for x in bpy.data.objects if x.name == 'tt_ring']: o.rotation_euler = (0, 0, a_)
    BULB.data.energy = 6.0
    # the door: shut while it runs, swings open at "comes out", shut again (off camera) for the loop; see-through as the camera flies in at the end
    HINGE.rotation_euler = (0, 0, -R(108) * ease_io((t - (T_DOOR - 0.25)) / 0.5) if t < T_RESET else 0.0)
    door = ease_io((t - (T_IN - 0.4)) / 0.2)
    for o in DOOR.children: o['xr'] = door
    for o in CAV: o['xr'] = 0.0
    # the oven egg, then its burst; set back up for the loop
    EGG1.hide_render = T_BANG1 <= t < T_RESET
    BURST1.update(t if t < T_RESET else -1.0)
    # the fork comes in through the open door, touches, presses, and jumps back with the bang
    u = (E1 - (E1 + Vector((0.07, -0.30, 0.10)))).normalized(); p_far = E1 - u * 0.33; p_touch = E1 - u * 0.0235
    fv = T_DOOR + 0.3 < t < T_BANG1 + 0.7
    for o in FORK_PARTS: o.hide_render = not fv
    s_ = ease_io((t - (T_DOOR + 0.4)) / max(0.3, T_TOUCH - T_DOOR - 0.4))
    tip = p_far.lerp(p_touch, s_) + u * 0.004 * ease_io((t - T_TOUCH) / max(0.1, T_BANG1 - T_TOUCH))
    if t > T_BANG1: tip = tip - u * 0.12 * ease_out((t - T_BANG1) / 0.25) + Vector((0, 0, 0.03)) * ease_out((t - T_BANG1) / 0.25)
    FORKP.location = tip; FORKP.rotation_quaternion = u.to_track_quat('X', 'Z')
    # the floor: the test egg A, its bang and the shockwave past the microphone
    EGGA.hide_render = t >= T_BANG2
    BURSTA.update(t)
    dt = t - T_BANG2; on = 0 <= dt < 0.6
    SHOCK.hide_render = True; SHOCK_RING.hide_render = not on
    if on:
        r_ = 0.03 + 0.9 * dt; g_ = (1 - dt / 0.6) ** 1.5
        SHOCK.scale = (r_, r_, r_ * 0.75); SHOCK.location = A_C; SHOCK['g'] = 0.15 * g_
        SHOCK_RING.scale = (r_, r_, r_); SHOCK_RING.location = (A_C.x, A_C.y, FLOOR_Z + 0.002); SHOCK_RING['g'] = g_
    mic0 = A_C + Vector((0.30, 0.0, 0.045)); hit = dt - 0.29
    MIC.location = mic0 + (shake(t, 0.004 * math.exp(-hit / 0.18), 9.0, 30.0) if hit > 0 else Vector())
    # the thermometer
    tv = TK[0][0] < t < TK[-1][0]
    for o in THERM_KIDS: o.hide_render = not tv
    THERM.location = therm_at(t) if tv else Vector((0, 0, -5))
    # egg B: x-ray, drops, heat, the chain of steam flashes, then it boils apart
    xr = ease_io((t - T_XRAY) / 0.6); gone = t >= T_BOIL
    EGGB['xr'] = YOLKB['xr'] = xr; EGGB.hide_render = YOLKB.hide_render = gone
    chain = ease_io((t - T_CHAIN) / max(0.2, T_BOIL - T_CHAIN))
    jig = shake(t, 0.0012 * chain, 4.0, 28.0)
    EGGB.location = B_C + jig; YOLKB.location = B_C + Vector((-0.002, 0, 0)) + jig
    YOLKB['heat'] = 0.7 * ease_io((t - T_HOT) / 1.5) + 0.5 * chain
    for i, d in enumerate(DROPS):
        vis = xr > 0.3 and T_DROPS - 0.3 < t < T_BOIL; d.hide_render = not vis
        if not vis: continue
        sc = ease_out((t - (T_DROPS + 0.03 * i)) / 0.3); h = ease_io((t - (T_HOT + 0.02 * i)) / 1.2)
        ti = T_FLASH if i == DROP0 else T_CHAIN + (_dd[i] - _dmin) / max(1e-6, _dmax - _dmin) * 0.55
        f = max(0.0, 1 - (t - ti) / 0.3) if t >= ti else 0.0
        grow = 1 + 1.8 * ease_out((t - ti) / 0.15) if t >= ti else 1.0
        d.scale = (sc * grow,) * 3; d['h'] = h; d['f'] = f
        d.location = Vector(d['home']) + jig + Vector((wob(t, 9, i), wob(t, 9, i + 50), wob(t, 9, i + 90))) * 0.0005 * h
    BURSTB.update(t)
    # egg roulette: about one in three of the floor eggs goes off
    for o, b in ROUL: o.hide_render = t >= b.t0; b.update(t)
    # one flash light at whichever burst is brightest right now
    best = max(BURSTS, key=lambda b: b.light(t)); L_ = best.light(t)
    POP_LT.location = best.c + Vector((0, 0, 0.03)); POP_LT.data.energy = 6.0 * L_

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

