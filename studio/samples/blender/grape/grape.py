# Grapes in the microwave: why a grape makes plasma. Blender Cycles, ONE continuous camera move (no cuts),
# resting on each idea; inside the oven, out past the twelve wrecked microwaves, back in to the grapes and the water balls.
#   python3 grape.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
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

# ================================================================ the set: a lab with a steel wire rack of microwaves, ours on the second shelf
# World: our shelf top is z = 0, the microwave's front face is the plane y = -0.20 (we look at it from -y), x is left/right.
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_SPARK = word_t(1, 3)                         # "shoots out": the plasma ball
T_STOP = B[3] - 0.15                           # the oven beeps off; the plasma dies; the plate stops
T_SKIN = word_t(3, 8)                          # "strip of skin": current runs along the skin
T_OUT = B[4] + 0.35                            # the camera goes out through the door
T_ZAP = word_t(4, 6)                           # "zapping grapes": the rack's windows flash one after another
T_WRECK = word_t(5, 1)                         # "wrecked twelve microwaves": smoke and scorch
T_SWAP = B[4] + 1.2                            # (off camera) the plate gets the two whole grapes and the water balls
T_WHOLE = word_t(6, 5)                         # "sparked"
T_BEAD = word_t(7, 3)                          # "balls of almost pure water"
T_WAVE = B[8] + 0.15                           # the waves come in from the waveguide
T_SHRINK = word_t(8, 3)                        # "shrink"
T_TRAP = word_t(8, 14)                         # "traps them"
T_CRAM = word_t(9, 8)                          # "crammed into one tiny spot"
T_RIP = word_t(10, 5)                          # "rips atoms apart"
T_ALL = word_t(11, 9)                          # "the water": the whole grapes go too
T_MELT = word_t(12, 8)                         # "a hole melted"
T_RESET = B[13] + 0.7                          # set back up for the loop while the camera is out front
CAM.data.clip_start = 0.002

# ---- the lab: a real interior (Poly Haven HDRI) for light and reflections; a steel wire rack, a concrete floor, a painted wall
P.hdri('ph:cayley_interior', 0.9, 205)
RACK_M = mat('rack', (0.55, 0.56, 0.58), 0.35, 1.0)
SHELF_Z = [-0.40, 0.0, 0.40, 0.80]; COL_X = [-0.56, 0.0, 0.56]; FLOOR_Z = -0.55
for i_, z_ in enumerate(SHELF_Z):
    box(f'shelf{i_}', (1.72, 0.50, 0.02), (0, 0.02, z_ - 0.012), RACK_M, bv=0.003)
    for k_ in range(9): box(f'wire{i_}_{k_}', (0.006, 0.50, 0.006), (-0.84 + 0.21 * k_, 0.02, z_ - 0.026), RACK_M)
for px_ in (-0.865, 0.865):
    for py_ in (-0.225, 0.265): box(f'post{px_}{py_}', (0.025, 0.025, 1.62), (px_, py_, FLOOR_Z + 0.81), RACK_M, bv=0.004)
box('lab_floor', (6.0, 6.0, 0.02), (0, -1.5, FLOOR_Z - 0.01), mat('labfloor', (0.30, 0.31, 0.32), 0.55))
WALL = box('lab_wall', (6.0, 0.02, 5.0), (0, 0.42, 1.6), mat('labwall', (0.62, 0.66, 0.68), 0.7))
noisy(WALL.data.materials[0], 6.0, 0.08, 0.05)
KEY = light_at('key', 'AREA', (-0.9, -0.9, 1.1), (0, 0, 0.15), 60, (1.0, 0.94, 0.86), 1.0)
RIM = light_at('rim', 'AREA', (0.8, 0.5, 0.9), (0, 0, 0.15), 25, (0.85, 0.9, 1.0), 0.6)

_N0 = set(bpy.data.objects.keys())               # everything made from here to the end of this part is the microwave (copied onto the rack)
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
MW_OBJS = [o for o in bpy.data.objects if o.name not in _N0 and o.type != 'LIGHT']

# ================================================================ the grape props: a cut grape on a white plate, two whole grapes, two water
# balls, the plasma, sparks, the microwaves coming in and getting trapped, the hot spot, the atoms, the rack's eleven other microwaves.
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))

# ---- the turntable: 5 turns a minute while it runs, stopped from the beep, set going again off camera for the loop
RPM = 5.0
W_TT = 2 * math.pi * RPM / 60.0; A0_TT = R(-20)
def tt_angle(t):
    if t < T_STOP: return A0_TT + W_TT * t
    if t < T_RESET: return A0_TT + W_TT * T_STOP
    return A0_TT + W_TT * (t - END)
def tt_mat(t): return Matrix.Translation(TT_C) @ Matrix.Rotation(tt_angle(t), 4, 'Z')
TH_S = tt_angle(T_STOP)

# ---- a white plate centered on the turntable (red grapes pop on it); its top is local z = 0.0215
PLATE_M = mat('plate', (0.035, 0.05, 0.075), 0.12, coat=1.0)                 # dark slate blue: red grapes, clear water and the glow all pop on it
PLATE = lathe('plate', [(0.0, 0.0205), (0.06, 0.0205), (0.068, 0.022), (0.088, 0.031), (0.095, 0.0325), (0.096, 0.031), (0.086, 0.0265), (0.066, 0.0225),
                        (0.058, 0.0215), (0.0, 0.0215)], 64, PLATE_M, TT)
PZ = 0.0215
# ---- red grape skin: deep red-purple, a little see-through at the edges, glossy, with the dusty bloom
GA, GB, GC = 0.0115, 0.0092, 0.0090                                           # a grape: 2.3 cm long, 1.8 cm wide
def grape_mat(name='grape'):
    m = mat(name, (0.11, 0.008, 0.032), 0.24, coat=0.8); b = N(m)['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (1.0, 0.25, 0.35); b.inputs['Subsurface Scale'].default_value = 0.002
    noisy(m, 320.0, 0.22, 0.14); return m
GRAPE_M = grape_mat()
def ell_mesh(name, a_, b_, c_, half=False, seg=40):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        if half: z = max(z, 0.0)
        v.co = Vector((x * a_, y * b_, z * c_))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return me
# the cut grape: two halves cut face down, a little apart, still joined at one end by a strip of skin
CG_LOCAL = Vector((0.010, 0.004, PZ))
CG = empty('cutgrape', TT, loc=CG_LOCAL); CG.rotation_euler = (0, 0, R(15))
HALF_ME = ell_mesh('grape_half', GA, GB, GC, half=True); HALF_ME.materials.append(GRAPE_M)
HY = GB + 0.0022
HALVES = [obj('half0', HALF_ME, None, loc=(0, -HY, 0), parent=CG), obj('half1', HALF_ME, None, loc=(0, HY, 0), parent=CG)]
BX = -GA + 0.0016
BRIDGE_PTS = [(BX, -0.0040, 0.0010), (BX - 0.0004, -0.0020, 0.0030), (BX - 0.0006, 0.0, 0.0036), (BX - 0.0004, 0.0020, 0.0030), (BX, 0.0040, 0.0010)]
BRIDGE = tube('bridge', BRIDGE_PTS, 0.0011, GRAPE_M, CG, seg=12)
JUNC_L = Vector((BX - 0.0006, 0.0, 0.0036))                                     # where the spark starts (cut grape's local frame)
def junc_world(t): return tt_mat(t) @ (CG_LOCAL + Matrix.Rotation(R(15), 3, 'Z') @ JUNC_L)
CUT_PARTS = HALVES + [BRIDGE]

# ---- after the swap: two whole grapes touching, and two water balls touching, side by side across the front of the plate
def to_local(wx, wy):
    v = Matrix.Rotation(-TH_S, 3, 'Z') @ Vector((wx - TT_C.x, wy - TT_C.y, 0)); return v
WHOLE_C = Vector((TT_C.x - 0.034, TT_C.y - 0.024, TT_C.z + PZ + GB))
BEAD_R = 0.0095
BEAD_C = Vector((TT_C.x + 0.030, TT_C.y - 0.024, TT_C.z + PZ + BEAD_R))
GRAPE_ME = ell_mesh('grape_whole', GB, GA, GB); GRAPE_ME.materials.append(GRAPE_M)          # long axis front to back
WHOLE = []
for sx_ in (-1, 1):
    lp = to_local(WHOLE_C.x + sx_ * GB * 0.995, WHOLE_C.y); o = obj(f'whole{sx_}', GRAPE_ME, None, loc=(lp.x, lp.y, PZ + GB), parent=TT)
    o.rotation_euler = (0, 0, -TH_S); WHOLE.append(o)
WATER_M = mat('water_ball', (0.80, 0.93, 1.0), 0.02, trans=1.0, ior=1.33, coat=0.3)
BEADS = []
for sx_ in (-1, 1):
    lp = to_local(BEAD_C.x + sx_ * BEAD_R * 0.995, BEAD_C.y)
    BEADS.append(prim('uv_sphere', f'bead{sx_}', WATER_M, TT, loc=(lp.x, lp.y, PZ + BEAD_R), scale=(BEAD_R,) * 3, segments=48, ring_count=24))
CONTACT_W = WHOLE_C.copy(); CONTACT_B = BEAD_C.copy()
BEAD_W = [BEAD_C + Vector((-BEAD_R, 0, 0)), BEAD_C + Vector((BEAD_R, 0, 0))]

# ================================================================ glows, smoke
def soft_glow(name, col, strength, attr=None, power=2.5):
    # emission that fades to clear toward its silhouette, so a sphere reads as a soft halo, not a disc
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power)
    if attr: fac = math_(nt, 'MULTIPLY', fac, objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
def glow_line(name, col, strength, attr='g'):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, attr), strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', objattr(nt, attr), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
def smoke_mat(name, col=(0.16, 0.16, 0.17), dens=0.75):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 1.0
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), 2.6), math_(nt, 'MULTIPLY', objattr(nt, 'g'), dens))
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fac, mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
SMOKE_M = smoke_mat('smoke', (0.24, 0.24, 0.25), 0.7)
def decal(name, m, loc, sx, sy, rot=(0, 0, 0)):
    o = prim('plane', name, m, loc=loc, size=2.0, rot=rot); o.scale = (sx, sy, 1.0); return o
def burn_mat(name, axes='XY'):
    # a scorch mark, radius 1 in object space: black hole ('hr'), a glowing ember rim ('e'), brown char fading out; 'g' fades it all
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    p = sepz(nt, coord(nt, 'Object')); u_ = p.outputs[axes[0]]; v_ = p.outputs[axes[1]]
    nz = tnoise(nt, coord(nt, 'Object'), 6.0, 4.0)
    r = math_(nt, 'ADD', math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', u_, u_), math_(nt, 'MULTIPLY', v_, v_))), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz, 0.5), 0.35))
    hr = objattr(nt, 'hr'); inhole = math_(nt, 'LESS_THAN', r, hr)
    rim = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', r, math_(nt, 'ADD', hr, 0.08))), 0.22)), 0.0)
    b.inputs['Roughness'].default_value = 0.9
    nt.links.new(mixc(nt, inhole, ramp(nt, r, [(0.0, (0.0, 0.0, 0.0)), (0.55, (0.02, 0.012, 0.008)), (1.0, (0.12, 0.07, 0.03))]), (0.0, 0.0, 0.0)), b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value = (1.0, 0.38, 0.06, 1)
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', rim, 2.0), objattr(nt, 'e')), 40.0), b.inputs['Emission Strength'])
    alpha = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'POWER', math_(nt, 'MINIMUM', r, 1.0), 3.0)), objattr(nt, 'g'))
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', alpha, 0.0), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ================================================================ plasma: a hot yellow core, a violet halo and flickering tongues that rise to the roof
def plasma_glow(name, col, strength, power, opac):
    # glow that also covers what's behind it (a mix, not an add), so its color holds up against the white oven walls
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power), objattr(nt, 'g'))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', fac, opac), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
PL_CORE = plasma_glow('pl_core', (1.0, 0.58, 0.14), 7.5, 1.1, 2.0)
PL_HALO = plasma_glow('pl_halo', (0.55, 0.12, 1.0), 2.2, 1.6, 0.9)
PL_TONG = plasma_glow('pl_tongue', (1.0, 0.38, 0.06), 4.5, 1.2, 1.4)
PLASMAS = []
class Plasma:
    def __init__(s, name, origin, t0, t1, top, size, seed, drift=None, rise=0.45):
        s.origin, s.t0, s.t1, s.top, s.size, s.seed, s.drift, s.rise = origin, t0, t1, top, size, seed, drift, rise
        s.core = prim('uv_sphere', name + '_core', PL_CORE, segments=24, ring_count=12); s.halo = prim('uv_sphere', name + '_halo', PL_HALO, segments=24, ring_count=12)
        s.tongues = [prim('uv_sphere', f'{name}_t{i}', PL_TONG, segments=16, ring_count=8) for i in range(5)]
        s.objs = [s.core, s.halo] + s.tongues
        for o in s.objs: o.hide_render = True; o['g'] = 0.0
        PLASMAS.append(s)
    def g(s, t):
        if not (s.t0 <= t < s.t1 + 0.12): return 0.0
        return ease_out((t - s.t0) / 0.08) * (1 - ease_io((t - s.t1) / 0.12)) * (0.8 + 0.2 * wob(t, 17, s.seed))
    def center(s, t):
        o = s.origin(s.t0) if callable(s.origin) else s.origin
        k = ease_out((t - s.t0) / s.rise); c = Vector((o.x, o.y, o.z + (s.top - o.z) * k))
        if s.drift is not None: c = c.lerp(s.drift, ease_io((t - s.t0 - s.rise) / 1.2))
        return c + Vector((wob(t, 2.2, s.seed), wob(t, 2.2, s.seed + 9), 0)) * 0.004 * k
    def update(s, t):
        g_ = s.g(t)
        for o in s.objs: o.hide_render = g_ <= 0.0
        if g_ <= 0.0: return
        c = s.center(t); r = s.size * (0.35 + 0.65 * ease_out((t - s.t0) / 0.15)) * (1 + 0.14 * wob(t, 7, s.seed + 3))
        s.core.location = c; s.core.scale = (r * 0.55, r * 0.55, r * 0.62); s.core['g'] = g_
        s.halo.location = c; s.halo.scale = (r * 1.25, r * 1.25, r * 1.4); s.halo['g'] = g_ * (0.85 + 0.15 * wob(t, 23, s.seed + 5))
        for i, o in enumerate(s.tongues):
            a_ = 2 * math.pi * i / 5 + t * 5.0 + s.seed; ph = wob(t, 11, s.seed + 20 + i)
            o.location = c + Vector((math.cos(a_) * r * 0.5, math.sin(a_) * r * 0.5, r * (0.3 + 0.5 * ph)))
            sc = r * (0.32 + 0.12 * ph); o.scale = (sc, sc, sc * 1.8); o['g'] = g_ * (0.6 + 0.4 * wob(t, 19, s.seed + 40 + i))
    def light(s, t): return s.g(t) * s.size / 0.018

# ---- sparks: short bright streaks thrown off a point (drag + gravity), pooled per spot
SPARK_M = glow_line('spark', (1.0, 0.72, 0.35), 14.0)
SPARKS = []
class Sparks:
    def __init__(s, name, origin, t0, t1, n, seed, spd=(0.15, 0.55), up=0.6, life=(0.12, 0.30), size=1.0, grav=9.8):
        rr = random.Random(seed); s.origin = origin; s.items = []; s.grav = grav
        for i in range(n):
            o = prim('uv_sphere', f'{name}_{i}', SPARK_M, segments=8, ring_count=4); o.hide_render = True; o.rotation_mode = 'QUATERNION'; o['g'] = 1.0
            d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized() + Vector((0, 0, up))
            s.items.append((o, rr.uniform(t0, t1), rr.uniform(*life), d.normalized() * rr.uniform(*spd), rr.uniform(0.00025, 0.0005) * size))
        SPARKS.append(s)
    def update(s, t):
        for o, tb, lf, v, r in s.items:
            dt = t - tb; on = 0 <= dt < lf; o.hide_render = not on
            if not on: continue
            k = 6.0; h = (1 - math.exp(-k * dt)) / k; c = s.origin(tb) if callable(s.origin) else s.origin
            p = c + Vector((v.x * h, v.y * h, (v.z + s.grav / k) * h - s.grav * dt / k))
            vel = Vector((v.x, v.y, v.z + s.grav / k)) * math.exp(-k * dt) - Vector((0, 0, s.grav / k))
            o.location = p; ln = max(r * 1.5, vel.length / FPS * 0.6)
            o.scale = (r, r, ln); o.rotation_quaternion = vel.normalized().to_track_quat('Z', 'Y') if vel.length > 1e-6 else Quaternion()
            o['g'] = 1.0 - (dt / lf) ** 2

# ---- the old idea: current runs through the skin like an antenna: blue dots along the halves' tops and over the strip, the skin glows blue
CUR_M = soft_glow('current', (0.05, 0.4, 1.0), 3.0, 'g', 0.8)
SKIN_GLOW_M = soft_glow('skinglow', (0.1, 0.4, 1.0), 0.7, 'g', 3.5)
SKIN_GLOW = [obj(f'skinglow{i}', HALF_ME, None, loc=h.location, parent=CG) for i, h in enumerate(HALVES)]
for o in SKIN_GLOW: o.data = HALF_ME.copy(); o.data.materials.clear(); o.data.materials.append(SKIN_GLOW_M); o.scale = (1.06, 1.06, 1.06); o['g'] = 0.0; o.hide_render = True
_path = [Vector((x_, -HY, GC * math.sqrt(max(0.0, 1 - (x_ / GA) ** 2)) + 0.0006)) for x_ in [GA * 0.85 - i * GA * 1.7 / 10 for i in range(11)]]
_path += [Vector(p_) + Vector((0, 0, 0.0012)) for p_ in BRIDGE_PTS]
_path += [Vector((x_, HY, GC * math.sqrt(max(0.0, 1 - (x_ / GA) ** 2)) + 0.0006)) for x_ in [-GA * 0.85 + i * GA * 1.7 / 10 for i in range(11)]]
_plen = [0.0]
for i in range(1, len(_path)): _plen.append(_plen[-1] + (_path[i] - _path[i - 1]).length)
def path_at(sv):
    sv = sv % _plen[-1]; i = next(j for j in range(1, len(_plen)) if _plen[j] >= sv); k = (sv - _plen[i - 1]) / max(1e-9, _plen[i] - _plen[i - 1])
    return _path[i - 1].lerp(_path[i], k)
CUR_DOTS = [prim('uv_sphere', f'cur{i}', CUR_M, CG, scale=(0.0007,) * 3, segments=12, ring_count=6) for i in range(18)]
for o in CUR_DOTS: o['g'] = 0.0; o.hide_render = True

# ---- the waves: wiggly beams from the waveguide (right wall) into each water ball, long in the air, squeezed tight inside the water
WAVE_M = glow_line('wave', (0.15, 0.75, 1.0), 3.0)
WAVES = []
for i_, bc in enumerate(BEAD_W):
    o = obj(f'wave{i_}', bpy.data.meshes.new(f'wave{i_}'), WAVE_M); o['g'] = 0.0; o.hide_render = True
    WAVES.append((o, Vector((CX1 - 0.003, bc.y + (0.012 if i_ else -0.010), 0.150 - 0.02 * i_)), bc))
LAM_AIR, LAM_W = 0.030, 0.0055
def wave_points(S0, C, head, ph):
    d = C - S0; Lt = d.length + BEAD_R * 0.75; u_ = d.normalized(); n_ = u_.cross(Vector((0, 1, 0))); n_ = n_.normalized() if n_.length > 1e-6 else Vector((0, 0, 1))
    pts = []; phase = 0.0; s_ = 0.0; ds = 0.0004
    while s_ < min(head, Lt):
        p = S0 + u_ * s_; inside = (p - C).length < BEAD_R * 0.98
        lam = LAM_W if inside else LAM_AIR; amp = 0.0011 if inside else 0.0042
        taper = clamp(s_ / 0.01, 0, 1) * clamp((head - s_) / 0.004, 0, 1)
        pts.append(p + n_ * amp * taper * math.sin(phase - ph)); phase += 2 * math.pi * ds / lam; s_ += ds
    return pts
def set_tube(o, pts, r, seg=8):
    me = o.data; me.clear_geometry()
    if len(pts) < 3: return False
    n = len(pts); T0 = (pts[1] - pts[0]).normalized(); up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized()
    vs = []; fs = []
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        vs += [pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    me.from_pydata([tuple(v) for v in vs], [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    return True
# trapped: a wavy glowing ring inside each ball (facing the camera), spinning; two per ball
RING_M = glow_line('ring', (0.15, 0.78, 1.0), 3.2)
def ring_mesh(name, R0, lobes, amp, r=0.00035, seg=6, n=160):
    pts = [Vector((R0 * (1 + amp * math.sin(lobes * 2 * math.pi * i / n)) * math.cos(2 * math.pi * i / n), 0, R0 * (1 + amp * math.sin(lobes * 2 * math.pi * i / n)) * math.sin(2 * math.pi * i / n))) for i in range(n)]
    pts.append(pts[0]); pts.append(pts[1])
    o = obj(name, bpy.data.meshes.new(name), RING_M); set_tube(o, pts, r, seg); return o
RINGS = []
for i_, bc in enumerate(BEAD_W):
    for j_, (R0, lob) in enumerate(((0.0060, 7), (0.0037, 5))):
        o = ring_mesh(f'ring{i_}{j_}', R0, lob, 0.12); o.rotation_mode = 'XYZ'; o['g'] = 0.0; o.hide_render = True; RINGS.append((o, bc, i_, j_))
# the hot spot where the balls touch, and five atoms in it that get ripped apart
HOT_M = soft_glow('hot', (0.75, 0.92, 1.0), 9.0, 'g', 1.0)
HOT = prim('uv_sphere', 'hotspot', HOT_M, loc=CONTACT_B, segments=20, ring_count=10); HOT['g'] = 0.0; HOT.hide_render = True
NUC_M = mat('nucleus', (0.95, 0.35, 0.12), 0.35, emit=(1.0, 0.45, 0.15), estr=2.0)
ELEC_M = soft_glow('electron', (0.2, 0.7, 1.0), 8.0, None, 0.8)
ATOMS = []; _rr = random.Random(7)
for k_ in range(5):
    a_ = 2 * math.pi * k_ / 5 + 0.4; home = CONTACT_B + Vector((math.cos(a_) * 0.0034, -0.0085, math.sin(a_) * 0.0034))
    nuc = prim('uv_sphere', f'nuc{k_}', NUC_M, loc=home, segments=16, ring_count=8)
    els = [prim('uv_sphere', f'el{k_}{j_}', ELEC_M, segments=10, ring_count=5) for j_ in range(2)]
    ATOMS.append((nuc, els, home, Vector((_rr.uniform(-1, 1), _rr.uniform(-1, 1), _rr.uniform(-1, 1))).normalized(), _rr.uniform(0, 6.28)))
    for o in [nuc] + els: o.hide_render = True

# ================================================================ the rack: eleven more microwaves (ours is the middle of the second shelf)
COPIES = []
_order = random.Random(4).sample(range(11), 11)
WIN_GLOW = soft_glow('winglow', (1.0, 0.5, 0.35), 5.0, 'g', 1.2)
_slots = [(c_, r_) for r_ in range(4) for c_ in range(3) if not (c_ == 1 and r_ == 1)]
for n_, (c_, r_) in enumerate(_slots):
    off = Vector((COL_X[c_], 0.0, SHELF_Z[r_])); root = empty(f'mw{n_}', loc=off); mp = {}
    for o in MW_OBJS:
        c = o.copy(); S.collection.objects.link(c); mp[o] = c
    for o, c in mp.items():
        c.parent = mp[o.parent] if o.parent in mp else root
    for k_ in ('xr',):
        for c in mp.values():
            if k_ in c: c[k_] = 0.0
    glow = prim('uv_sphere', f'mw{n_}_glow', WIN_GLOW, loc=off + Vector((TT_C.x, TT_C.y, 0.09)), scale=(0.035,) * 3, segments=16, ring_count=8); glow['g'] = 0.0; glow.hide_render = True
    top = decal(f'mw{n_}_scorch', burn_mat(f'scorch{n_}', 'XY'), off + Vector((-0.04, 0.0, MW_H + 0.0006)), 0.09, 0.09); top['g'] = 0.0; top['hr'] = 0.30; top['e'] = 0.0
    soot = decal(f'mw{n_}_soot', burn_mat(f'soot{n_}', 'XY'), off + Vector((-0.05, -MW_D / 2 - 0.0125, MW_H - 0.02)), 0.15, 0.05, (R(90), 0, 0))
    soot['g'] = 0.0; soot['hr'] = -1.0; soot['e'] = 0.0
    puffs = [prim('uv_sphere', f'mw{n_}_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(7)]
    for o in puffs: o['g'] = 0.0; o.hide_render = True
    tz = T_ZAP - 0.55 + 0.11 * _order[n_]; tw = T_WRECK - 0.15 + 0.07 * _order[n_]
    COPIES.append(dict(off=off, glow=glow, top=top, soot=soot, puffs=puffs, tz=tz, tw=tw, seed=n_ * 13.0))
MAIN_GLOW = prim('uv_sphere', 'main_glow', WIN_GLOW, loc=Vector((TT_C.x, TT_C.y, 0.09)), scale=(0.035,) * 3, segments=16, ring_count=8); MAIN_GLOW['g'] = 0.0; MAIN_GLOW.hide_render = True
MAIN_PUFFS = [prim('uv_sphere', f'main_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(7)]
for o in MAIN_PUFFS: o['g'] = 0.0; o.hide_render = True
WIDE = light_at('wide', 'AREA', (0.3, -2.2, 1.7), (0, 0, 0.35), 0.0, (1.0, 0.96, 0.9), 2.5)

# ---- our oven's roof melting through: a scorch that glows, opens to a black hole with an ember rim; smoke under the roof; drips
HOLE_C = Vector(((CONTACT_W.x + CONTACT_B.x) / 2, CONTACT_B.y + 0.01, CZ1 - 0.0004))
HOLE = decal('hole', burn_mat('hole', 'XY'), HOLE_C, 0.045, 0.045); HOLE['g'] = 0.0; HOLE['hr'] = 0.0; HOLE['e'] = 0.0
HOLE.hide_render = True
ROOF_SMOKE = [prim('uv_sphere', f'roof_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(6)]
for o in ROOF_SMOKE: o['g'] = 0.0; o.hide_render = True
OUT_SMOKE = [prim('uv_sphere', f'out_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(8)]
for o in OUT_SMOKE: o['g'] = 0.0; o.hide_render = True
PL_LT = light_at('plasma_lt', 'POINT', (0, 0, 0.1), (0, 0, 0), 0.0, (1.0, 0.45, 0.25), 0.008)
for o_ in bpy.data.objects:
    if o_.name.startswith('tt_plate'): o_.visible_shadow = False
# ================================================================ the camera (one take: rests on each idea, flies between them) and the story's state
BR_W = junc_world(T_STOP)                                    # the strip of skin once the plate stops
MID = (CONTACT_W + CONTACT_B) / 2
P0, Q0 = (-0.040, -0.120, 0.105), (-0.055, -0.005, 0.062)
def off(p, d): return tuple(Vector(p) + Vector(d))
# keys: (time, position, target, lens, f-stop), all in the world. Every key is a rest: the camera eases in and out of it.
K = [
    (0.00, P0, Q0, 38, 32),                                                          # frame one: the cut grape turning in the running oven
    (2.75, (-0.043, -0.118, 0.103), Q0, 38, 32),
    (3.70, (-0.046, -0.176, 0.085), (-0.055, 0.020, 0.135), 28, 32),                  # back and up as the plasma shoots to the roof
    (4.50, (-0.047, -0.178, 0.084), (-0.055, 0.020, 0.145), 28, 32),
    (7.20, (-0.050, -0.180, 0.085), (-0.055, 0.020, 0.146), 28, 32),
    (8.30, off(BR_W, (0.014, -0.074, 0.040)), tuple(BR_W), 36, 32),                   # in on the strip of skin: the antenna idea
    (10.75, off(BR_W, (0.012, -0.071, 0.039)), tuple(BR_W), 36, 32),
    (11.20, (-0.050, -0.170, 0.120), (-0.050, 0.000, 0.100), 30, 32),                 # out through the door glass
    (11.80, (0.000, -0.800, 0.220), (0.000, 0.000, 0.200), 30, 16),
    (12.80, (0.000, -2.750, 0.330), (0.000, 0.000, 0.350), 26, 16),                   # the whole rack: twelve microwaves
    (15.00, (0.012, -2.700, 0.338), (0.000, 0.000, 0.350), 26, 16),
    (15.55, (-0.040, -0.420, 0.120), (WHOLE_C.x, 0.000, 0.080), 32, 16),              # back in to the two whole grapes
    (16.05, off(WHOLE_C, (0.010, -0.075, 0.032)), off(WHOLE_C, (0, 0, 0.004)), 36, 32),
    (17.20, off(WHOLE_C, (0.012, -0.073, 0.031)), off(WHOLE_C, (0, 0, 0.004)), 36, 32),
    (17.75, off(BEAD_C, (0.002, -0.075, 0.030)), off(BEAD_C, (0, 0, 0.003)), 36, 32),  # across to the water balls
    (19.05, off(BEAD_C, (0.003, -0.074, 0.030)), off(BEAD_C, (0, 0, 0.003)), 36, 32),
    (19.70, off(BEAD_C, (0.016, -0.090, 0.022)), off(BEAD_C, (0.014, 0, 0.004)), 32, 32),  # the waves come in from the right
    (22.70, off(BEAD_C, (0.017, -0.088, 0.021)), off(BEAD_C, (0.014, 0, 0.004)), 32, 32),
    (23.40, off(CONTACT_B, (0.001, -0.042, 0.010)), tuple(CONTACT_B), 45, 45),        # right in on the spot where they touch
    (26.30, off(CONTACT_B, (0.001, -0.039, 0.009)), tuple(CONTACT_B), 45, 45),
    (27.40, off(BEAD_C, (-0.004, -0.150, 0.040)), off(BEAD_C, (-0.004, 0, 0.080)), 28, 32),   # follow the plasma up
    (28.40, off(MID, (0.000, -0.148, 0.048)), off(MID, (0, 0, 0.095)), 22, 32),        # both pairs going: it was the water
    (29.90, off(MID, (0.002, -0.146, 0.048)), off(MID, (0, 0, 0.098)), 22, 32),
    (30.80, off(MID, (0.000, -0.145, 0.062)), (HOLE_C.x, HOLE_C.y, CZ1 - 0.012), 22, 32),   # up at the roof: a hole melts through
    (32.50, off(MID, (0.002, -0.143, 0.063)), (HOLE_C.x, HOLE_C.y, CZ1 - 0.012), 22, 32),
    (33.30, (-0.030, -0.950, 0.230), (-0.040, 0.000, 0.170), 30, 16),                 # out front for the share line: smoke out of the roof
    (33.85, (-0.028, -0.940, 0.228), (-0.040, 0.000, 0.170), 30, 16),
    (END, P0, Q0, 38, 32),                                                           # and back in to frame one
]
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    u = clamp((t - ts[i]) / (ts[i + 1] - ts[i]), 0, 1); s = u * u * (3 - 2 * u)
    return vs[i] * (1 - s) + vs[i + 1] * s
BIG = [(T_SPARK, 0.0012), (T_WRECK, 0.010), (T_RIP, 0.0006), (T_MELT, 0.0010)]
def cam_raw(t):
    ts = [k[0] for k in K]; return herm(ts, [Vector(k[1]) for k in K], t)
def cam_at(t):
    ts = [k[0] for k in K]
    p = herm(ts, [Vector(k[1]) for k in K], t); q = herm(ts, [Vector(k[2]) for k in K], t)
    ln = herm(ts, [Vector((k[3], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x
    close = p.y > -0.3
    sh = shake(t, 0.00025 if close else 0.002, 5.0, 0.6)
    for ts_, amp in BIG:
        if ts_ < t < ts_ + 0.35: sh += shake(t, amp * (1 - (t - ts_) / 0.35), 2.0, 16.0)
    return p + sh, q + sh * 0.5, ln, fs
# the four times the camera goes through the door glass (it turns clear around each)
FRONT = -MW_D / 2 - 0.004
_tc = [i_ / 200 for i_ in range(int(END * 200))]
CROSS = [t_ for a_, b_ in zip(_tc, _tc[1:]) for t_ in (a_,) if (cam_raw(a_).y - FRONT) * (cam_raw(b_).y - FRONT) < 0]
print('door crossings', [round(x, 2) for x in CROSS])

# ---- plasma, sparks, the waves
P1 = Plasma('p1', junc_world, T_SPARK, T_STOP, CZ1 - 0.022, 0.018, 1.0, rise=0.5)
PW = Plasma('pw', CONTACT_W + Vector((0, -0.002, GB * 0.9)), T_WHOLE, T_WHOLE + 0.55, CONTACT_W.z + 0.02, 0.008, 2.0, rise=0.4)
PB = Plasma('pb', CONTACT_B + Vector((0, -0.002, BEAD_R * 0.9)), T_BEAD, T_BEAD + 0.55, CONTACT_B.z + 0.02, 0.008, 3.0, rise=0.4)
P2 = Plasma('p2', CONTACT_B + Vector((0, -0.002, 0.002)), T_RIP, T_RESET, CZ1 - 0.024, 0.017, 4.0, drift=Vector((HOLE_C.x + 0.012, HOLE_C.y, CZ1 - 0.024)), rise=0.6)
P3 = Plasma('p3', CONTACT_W + Vector((0, -0.002, GB * 0.9)), T_ALL, T_RESET, CZ1 - 0.026, 0.016, 5.0, drift=Vector((HOLE_C.x - 0.012, HOLE_C.y, CZ1 - 0.026)), rise=0.6)
S0 = Sparks('s0', junc_world, 1.7, T_SPARK + 0.1, 26, 1, spd=(0.08, 0.3), life=(0.06, 0.16), size=0.8)
S1 = Sparks('s1', junc_world, T_SPARK - 0.05, T_STOP - 0.2, 60, 2, spd=(0.15, 0.6))
SW = Sparks('sw', CONTACT_W + Vector((0, -0.003, GB * 0.8)), T_WHOLE - 0.25, T_WHOLE + 0.5, 30, 3)
SB = Sparks('sb', CONTACT_B + Vector((0, -0.003, BEAD_R * 0.8)), T_BEAD - 0.25, T_BEAD + 0.5, 30, 4)
S2 = Sparks('s2', CONTACT_B + Vector((0, -0.004, 0.001)), T_RIP - 0.05, T_RIP + 0.9, 50, 5, spd=(0.2, 0.7))
S3 = Sparks('s3', CONTACT_W + Vector((0, -0.003, GB * 0.8)), T_ALL - 0.1, T_ALL + 0.8, 35, 6)
SD = Sparks('sd', HOLE_C + Vector((0, 0, -0.002)), T_MELT, T_RESET, 40, 7, spd=(0.02, 0.12), up=-1.5, life=(0.25, 0.5), size=1.2)
SKIN_ON = (T_SKIN - 0.6, B[4] - 0.1)
T_IN1 = CROSS[1] if len(CROSS) > 1 else 15.4

def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    a_ = tt_angle(t); TT.rotation_euler = (0, 0, a_)
    for o in [x for x in bpy.data.objects if x.name == 'tt_ring']: o.rotation_euler = (0, 0, a_)
    BULB.data.energy = 6.0
    door = max([win(t, c_ - 0.28, c_ + 0.22, 0.12) for c_ in CROSS] + [0.0])
    for o in DOOR.children: o['xr'] = door
    for o in CAV: o['xr'] = 0.0
    reset = t >= T_RESET
    swapped = T_SWAP <= t < T_RESET
    for o in CUT_PARTS: o.hide_render = swapped
    for o in WHOLE + BEADS: o.hide_render = not swapped
    # the old idea: current racing through the skin (it moves back and forth, like in an antenna)
    sk = win(t, *SKIN_ON, 0.3)
    for o in SKIN_GLOW: o.hide_render = True; o['g'] = sk * (0.7 + 0.3 * wob(t, 12, 1.0))
    for i, o in enumerate(CUR_DOTS):
        o.hide_render = sk <= 0
        if sk > 0:
            sv = _plen[-1] * (0.5 + 0.48 * math.sin(2 * math.pi * 1.1 * t + i * 0.52)); o.location = path_at(sv); o['g'] = sk
    # plasma and sparks
    for p in PLASMAS: p.update(t)
    for s in SPARKS: s.update(t)
    best = max(PLASMAS, key=lambda p: p.light(t)); Lp = sum(p.light(t) for p in PLASMAS)
    PL_LT.location = best.center(t) if Lp > 0 else Vector((0, 0, -5)); PL_LT.data.energy = 0.3 * Lp
    # the waves in, the trapped rings, the hot spot, the atoms
    wg = ease_io((t - T_WAVE) / 0.2) * (1 - ease_io((t - (T_TRAP + 0.3)) / 0.5))
    for i, (o, S_, C_) in enumerate(WAVES):
        on = wg > 0 and t < T_TRAP + 0.85; o.hide_render = not on
        if on: o.hide_render = not set_tube(o, wave_points(S_, C_, 0.20 * (t - T_WAVE), 2 * math.pi * 2.5 * t), 0.00045); o['g'] = wg
    ring_g = ease_io((t - (T_SHRINK + 0.2)) / 0.8) * (1 - ease_io((t - T_RIP) / 0.25)) if t < T_RESET else 0.0
    cram = ease_io((t - (T_CRAM - 0.6)) / 1.0)
    for o, bc, i, j in RINGS:
        o.hide_render = ring_g <= 0
        if ring_g <= 0: continue
        toward = CONTACT_B - bc
        o.location = bc + toward * 0.55 * cram; sc = 1 - 0.55 * cram; o.scale = (sc, sc, sc)
        o.rotation_euler = (0, (1 if (i + j) % 2 else -1) * t * (3.0 + j), 0); o['g'] = ring_g * (1 + 1.5 * cram) * (0.85 + 0.15 * wob(t, 20, i * 3 + j))
    hot = cram * (1 - ease_io((t - (T_RIP + 0.2)) / 0.3)) if t < T_RESET else 0.0
    HOT.hide_render = hot <= 0
    if hot > 0:
        r_ = 0.0008 + 0.0022 * hot * (1 + 0.15 * wob(t, 25, 9.0)); HOT.scale = (r_, r_, r_); HOT['g'] = hot * (1 + 0.6 * ease_io((t - (T_RIP - 0.5)) / 0.5))
    av = T_CRAM - 0.3 < t < T_RIP + 0.6
    for k_, (nuc, els, home, dirv, ph) in enumerate(ATOMS):
        for o in [nuc] + els: o.hide_render = not av
        if not av: continue
        sc = ease_out((t - (T_CRAM - 0.3 + 0.06 * k_)) / 0.3); jig = Vector((wob(t, 8, k_), wob(t, 8, k_ + 30), wob(t, 8, k_ + 60))) * 0.0003 * (1 + 2 * cram)
        rip = t - T_RIP
        nuc.location = home + jig + (dirv * 0.012 * ease_out(rip / 0.5) if rip > 0 else Vector())
        ns = 0.0008 * sc * (1 - ease_io((rip - 0.3) / 0.3) if rip > 0 else 1); nuc.scale = (ns,) * 3
        for j_, e in enumerate(els):
            a2 = ph + j_ * math.pi + t * 2 * math.pi * 3.0; orb = Vector((math.cos(a2), 0.35 * math.sin(a2 * 0.5), math.sin(a2))) * 0.0021
            if j_: orb = Vector((orb.z, orb.y, -orb.x))
            p = home + jig + orb
            if rip > 0:
                fly = (orb.normalized() + dirv * 0.3).normalized(); p = p + fly * 0.05 * ease_out(rip / 0.45)
            e.location = p; es = 0.00035 * sc * (1 - ease_io((rip - 0.35) / 0.2) if rip > 0 else 1); e.scale = (es,) * 3
    # the rack: windows flash as each oven zaps grapes, then smoke and scorch as they get wrecked
    for c in COPIES + [dict(off=Vector(), glow=MAIN_GLOW, top=None, soot=None, puffs=MAIN_PUFFS, tz=T_ZAP - 0.55 + 0.11 * 5.5, tw=T_WRECK - 0.15 + 0.07 * 5.5, seed=99.0)]:
        zg = win(t, c['tz'], c['tz'] + 0.32, 0.06) * (0.75 + 0.25 * wob(t, 30, c['seed'])) if T_OUT < t < T_IN1 else 0.0
        c['glow'].hide_render = zg <= 0; c['glow']['g'] = zg
        dw = t - c['tw']; wr = dw > 0 and t < T_RESET
        if c['top'] is not None:
            c['top'].hide_render = not wr; c['top']['g'] = ease_out(dw / 0.25) if wr else 0.0; c['top']['e'] = max(0.0, 1 - dw / 1.2) if wr else 0.0
            c['soot'].hide_render = not wr; c['soot']['g'] = 0.85 * ease_out(dw / 0.3) if wr else 0.0
        top0 = c['off'] + Vector((-0.04, -0.02, MW_H))
        for j_, o in enumerate(c['puffs']):
            u = (dw - 0.06 * j_) / 1.9; on = 0 < u < 1 and T_OUT < t < T_IN1 + 0.3; o.hide_render = not on
            if not on: continue
            sc = 0.05 + 0.17 * ease_out(u); o.scale = (sc, sc, sc * 0.9)
            o.location = top0 + Vector((0.08 * wob(j_ * 0.7, 1, c['seed']), -0.03 + 0.04 * wob(j_ * 0.7, 1, c['seed'] + 4), 0.03 + 0.32 * ease_out(u) + 0.035 * j_))
            o['g'] = ease_out(u / 0.08) * (1 - u) ** 1.3
    WIDE.data.energy = 140.0 * win(t, T_OUT - 0.1, T_IN1 + 0.2, 0.4)
    # our oven's roof: glows, then melts open; smoke gathers under it
    hv = B[12] - 0.3 < t < T_RESET; HOLE.hide_render = not hv
    if hv:
        HOLE['g'] = ease_out((t - (B[12] - 0.3)) / 0.6); HOLE['e'] = 0.4 + 0.6 * ease_io((t - (B[12] - 0.3)) / 1.0) * (0.85 + 0.15 * wob(t, 18, 2.0))
        HOLE['hr'] = 0.55 * ease_out((t - T_MELT) / 0.6) if t > T_MELT else 0.0
    for j_, o in enumerate(OUT_SMOKE):
        u = (t - (T_MELT + 0.3 + 0.22 * j_)) / 1.8; u = u % 1.0 if u > 0 else u; on = t > T_MELT + 0.3 + 0.22 * j_ and t < T_RESET; o.hide_render = not on
        if not on: continue
        sc = 0.02 + 0.05 * ease_out(u); o.scale = (sc * 1.6, sc, sc * 0.8)
        o.location = Vector((HOLE_C.x + 0.06 * wob(j_ * 0.7, 1, 3.0), HOLE_C.y - 0.24 * ease_out(u), MW_H + 0.015 + 0.06 * ease_out(u) + 0.05 * max(0.0, u - 0.6)))
        o['g'] = 0.7 * ease_out(u / 0.15) * (1 - u) * (1 - ease_io((t - (T_RESET - 0.35)) / 0.35))
    for j_, o in enumerate(ROOF_SMOKE):
        u = (t - (T_MELT - 0.4 + 0.15 * j_)) / 2.2; on = 0 < u and t < T_RESET; o.hide_render = not on
        if not on: continue
        a2 = 2 * math.pi * j_ / 6; sc = 0.012 + 0.03 * ease_out(u); o.scale = (sc, sc, sc * 0.6)
        o.location = HOLE_C + Vector((math.cos(a2) * 0.03 * ease_out(u), math.sin(a2) * 0.025 * ease_out(u) - 0.01, -0.012 - 0.004 * j_ % 3))
        o['g'] = 0.35 * ease_out(u / 0.2) * clamp(1.4 - u * 0.5, 0, 1)

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

