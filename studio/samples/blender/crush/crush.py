# Trapped under a building (the Brooklyn collapse, Nov 11 2026), built and rendered in Blender (Cycles): a corner store's ceiling
# comes down on him; pinned on his back with a beam and a rubble mound over his legs; rescuers dig in (light and bricks pulled
# away from the void); x-ray: the crushed leg muscles break down, potassium builds up, the weight comes off and it rushes to the
# heart (crush syndrome); an IV drips in before the lift; outside: a three-story brick building at the edge of a dug-out lot
# tips into the pit, the shared wall leaves the next building's rooms open; night: light towers, a drone, flashlight beams.
#   python3 crush.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]      (stride.json / redo.json beside it: see ../ele/ele.py)
# Needs man.blend (../foot/man_build.py) beside it or in /root/vt/n43/crush.
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
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n43/crush', n)) if os.path.exists(p_))
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
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1); WBG.inputs['Strength'].default_value = 1.0
SKYTEX = wnt.nodes.new('ShaderNodeTexSky'); SKYTEX.sun_elevation = R(5); SKYTEX.sun_rotation = R(245)
SKYBG = wnt.nodes.new('ShaderNodeBackground'); SKYBG.inputs['Strength'].default_value = 0.0; wnt.links.new(SKYTEX.outputs['Color'], SKYBG.inputs['Color'])
WADD = wnt.nodes.new('ShaderNodeAddShader'); wnt.links.new(WBG.outputs['Background'], WADD.inputs[0]); wnt.links.new(SKYBG.outputs['Background'], WADD.inputs[1])
wnt.links.new(WADD.outputs['Shader'], wnt.nodes['World Output'].inputs['Surface'])
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.03; CAM.data.clip_end = 3000

# ================================================================ THE STORE (z up, metres): a Brooklyn corner store, ground floor of the
# three-story building. Floor x -3..3, y -4..4, ceiling 3.1. He stands in the aisle at M0 facing the front (-y, the camera side).
SX, SY, SH = 3.0, 4.0, 3.1
M0 = V3(0.15, 0.4, 0.0)
def tile_mat(name, c0, c1, scale=2.5):
    m = mat(name, c0, 0.35); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    ck = nt.nodes.new('ShaderNodeTexChecker'); ck.inputs['Scale'].default_value = scale; ck.inputs['Color1'].default_value = (*c0, 1); ck.inputs['Color2'].default_value = (*c1, 1)
    nt.links.new(tc.outputs['Object'], ck.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14.0; nz.inputs['Detail'].default_value = 8; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.35
    nt.links.new(ck.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.25; mr.inputs['To Max'].default_value = 0.6; nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m
def brick_mat(name, base=(0.42, 0.16, 0.1), mortar=(0.55, 0.52, 0.46), scale=1.0, dirt=0.0):
    """running-bond brick from a brick texture in object space"""
    m = mat(name, base, 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    bk = nt.nodes.new('ShaderNodeTexBrick'); bk.inputs['Color1'].default_value = (*base, 1); bk.inputs['Color2'].default_value = tuple(c * 0.72 for c in base) + (1,)
    bk.inputs['Mortar'].default_value = (*mortar, 1); bk.inputs['Scale'].default_value = 1.0; bk.inputs['Mortar Size'].default_value = 0.012
    bk.inputs['Brick Width'].default_value = 0.2; bk.inputs['Row Height'].default_value = 0.068; bk.offset = 0.5
    nt.links.new(mp.outputs['Vector'], bk.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6; nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.4 + dirt
    nt.links.new(bk.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.invert = True; nt.links.new(bk.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
FLOOR_M = tile_mat('floor_tile', (0.62, 0.6, 0.55), (0.2, 0.21, 0.22))
WALL_M = noisy(mat('wall', (0.72, 0.7, 0.62), 0.8), 6.0, 0.12)
CEIL_M = noisy(mat('ceiling_tile', (0.78, 0.77, 0.72), 0.9), 60.0, 0.15)
PLASTER_M = noisy(mat('plaster', (0.7, 0.68, 0.62), 0.95), 25.0, 0.25)
WOOD_M = noisy(mat('joist', (0.42, 0.3, 0.19), 0.75), 18.0, 0.35, 0.15)
OLDWOOD_M = noisy(mat('old_wood', (0.3, 0.22, 0.15), 0.85), 25.0, 0.4)
BRICK_M = brick_mat('brick', dirt=0.1)
LOOSE_BRICK_M = noisy(mat('loose_brick', (0.45, 0.17, 0.1), 0.9), 22.0, 0.35, 0.1)
STEEL_M = noisy(mat('steel', (0.25, 0.25, 0.26), 0.45, metal=0.8), 30.0, 0.3)
SHELF_M = noisy(mat('shelf', (0.85, 0.85, 0.83), 0.4, metal=0.3), 30.0, 0.08)
TUBE_GLOW = emis('fluor', (0.92, 0.97, 1.0), 4.5)
FRIDGE_GLOW = emis('fridge', (0.85, 0.93, 1.0), 4.0)
STORE = []
STORE.append(box('floor', (2 * SX, 2 * SY, 0.1), V3(0, 0, -0.05), FLOOR_M))
STORE.append(box('ceiling', (2 * SX, 2 * SY, 0.05), V3(0, 0, SH + 0.025), CEIL_M))
STORE.append(box('wall_back', (2 * SX, 0.2, SH), V3(0, SY + 0.1, SH / 2), WALL_M))
STORE.append(box('wall_L', (0.2, 2 * SY, SH), V3(-SX - 0.1, 0, SH / 2), BRICK_M))
STORE.append(box('wall_R', (0.2, 2 * SY, SH), V3(SX + 0.1, 0, SH / 2), WALL_M))
# the front: big window (night-blue street glow) and the door frame
STORE.append(box('front_low', (2 * SX, 0.2, 0.7), V3(0, -SY - 0.1, 0.35), WALL_M))
STORE.append(box('front_top', (2 * SX, 0.2, 0.5), V3(0, -SY - 0.1, SH - 0.25), WALL_M))
STORE.append(box('front_glass', (2 * SX, 0.02, SH - 1.2), V3(0, -SY - 0.15, 0.7 + (SH - 1.2) / 2), emis('street', (0.9, 0.75, 0.55), 1.4)))
# ceiling grid lights (fluorescent troffers)
TROFFERS = []
for i, y in enumerate((-2.6, -0.8, 1.0, 2.8)):
    for x in (-1.5, 1.5):
        TROFFERS.append(box('troffer%d%s' % (i, 'L' if x < 0 else 'R'), (0.6, 1.2, 0.03), V3(x, y, SH - 0.02), TUBE_GLOW))
STORE += TROFFERS
# shelves: two gondola runs along y (x = -1.6, +1.6) and a wall run; rows of colourful product boxes
_rs = random.Random(4); PRODUCT_M = [noisy(mat('prod%d' % i, c, 0.45), 40.0, 0.15) for i, c in enumerate(
    [(0.8, 0.12, 0.08), (0.95, 0.75, 0.1), (0.1, 0.35, 0.8), (0.15, 0.6, 0.25), (0.9, 0.45, 0.1), (0.85, 0.85, 0.82), (0.5, 0.15, 0.55)])]
def gondola(name, x0, y0, y1, face):
    out = [box(name + '_base', (0.5, y1 - y0, 0.12), V3(x0, (y0 + y1) / 2, 0.06), SHELF_M),
           box(name + '_back', (0.04, y1 - y0, 1.6), V3(x0 - 0.2 * face, (y0 + y1) / 2, 0.8), SHELF_M)]
    for k, z in enumerate((0.12, 0.55, 0.98, 1.4)):
        out.append(box(name + '_s%d' % k, (0.42, y1 - y0, 0.025), V3(x0, (y0 + y1) / 2, z), SHELF_M))
        y = y0 + 0.03
        while y < y1 - 0.12:
            w = _rs.uniform(0.08, 0.2); h = _rs.uniform(0.14, 0.32); d_ = _rs.uniform(0.12, 0.3)
            out.append(box(name + '_p%d_%.2f' % (k, y), (d_, w, h), V3(x0 + 0.04 * face, y + w / 2, z + 0.0125 + h / 2), _rs.choice(PRODUCT_M)))
            y += w + 0.012
    return out
STORE += gondola('gL', -1.55, -2.8, 2.6, 1) + gondola('gR', 1.75, -2.8, 2.6, -1)
# cold cases on the back wall (glowing glass doors) with bottles
for i in range(4):
    x = -2.2 + i * 1.3
    STORE.append(box('fridge%d' % i, (1.2, 0.05, 1.9), V3(x, SY - 0.6, 1.05), FRIDGE_GLOW))
    STORE.append(box('fridge_fr%d' % i, (1.25, 0.65, 0.12), V3(x, SY - 0.33, 2.05), STEEL_M))
    STORE.append(box('fridge_mull%d' % i, (0.05, 0.06, 1.95), V3(x + 0.6, SY - 0.64, 1.05), STEEL_M))
# counter by the front
STORE.append(box('counter', (1.8, 0.6, 1.0), V3(-1.8, -3.0, 0.5), noisy(mat('counter', (0.5, 0.42, 0.33), 0.5), 10.0, 0.2), 0.01))
STORE.append(box('register', (0.35, 0.3, 0.25), V3(-1.8, -3.0, 1.13), mat('reg', (0.08, 0.08, 0.09), 0.4)))
# interior light (sources are the troffers; a fill keeps faces readable)
STORE_L = [light_at('store_fill', 'AREA', V3(0.0, -2.6, 2.6), M0 + V3(0, 0, 1.2), 160, (1.0, 0.95, 0.88), 2.0),
           light_at('store_back', 'AREA', V3(0.0, SY - 0.8, 1.4), M0 + V3(0, 0, 1.2), 60, (0.85, 0.93, 1.0), 2.4)]
# after the collapse: the room is dark, one gap above lets a cold shaft of light in (rescue lights outside), a dust haze
GAP_L = light_at('gap_light', 'SPOT', V3(0.3, 0.6, 4.2), M0 + V3(0.0, -0.3, 0.0), 0.0, (0.82, 0.9, 1.0), 0.15)
GAP_L.data.spot_size = R(48); GAP_L.data.spot_blend = 0.6
TORCH_L = [light_at('torch%d' % i, 'SPOT', V3(0.0, 0.0, 4.0), M0, 0.0, (1.0, 0.93, 0.8), 0.04) for i in range(3)]
for o in TORCH_L: o.data.spot_size = R(16); o.data.spot_blend = 0.35
STORE += STORE_L + [GAP_L] + TORCH_L
# ================================================================ OUTSIDE (a block of Flatbush, built far from the store: origin at X0).
# The building line is y = 0, the street in front (-y). N = the next building (x -8..0, stands), C = the three-story building that
# falls (x 0..7), LOT = the dug-out lot next to it (x 7..19, a 4 m pit). C falls sideways into the pit; its side wall goes with it and
# leaves N's rooms open. No signs, no logos.
X0 = V3(200, 0, 0)
OUT = []
ASPHALT_M = noisy(mat('asphalt', (0.07, 0.07, 0.075), 0.75), 8.0, 0.35, 0.1)
WALK_M = noisy(mat('sidewalk', (0.45, 0.44, 0.42), 0.8), 4.0, 0.2)
DIRT_M = noisy(mat('dirt', (0.3, 0.22, 0.15), 0.95), 3.0, 0.35, 0.05)
TAN_BRICK_M = brick_mat('tan_brick', (0.55, 0.42, 0.3), (0.62, 0.6, 0.55))
RED_BRICK_M = brick_mat('red_brick', (0.36, 0.1, 0.06), (0.42, 0.4, 0.36), dirt=0.25)
FAR_BRICK_M = brick_mat('far_brick', (0.38, 0.26, 0.2), (0.5, 0.48, 0.45))
GLASS_M = mat('glass', (0.05, 0.06, 0.07), 0.05, metal=0.0, coat=1.0)
WINDOW_LIT = emis('window_lit', (1.0, 0.72, 0.4), 3.0)
TRIM_M = mat('trim_out', (0.15, 0.14, 0.13), 0.5)
OUT.append(box('street', (220, 30, 0.1), X0 + V3(0, -15, -0.05), ASPHALT_M))
OUT.append(box('sidewalk', (220, 3.0, 0.15), X0 + V3(0, -1.5, 0.075), WALK_M))
OUT.append(box('far_walk', (220, 3.0, 0.15), X0 + V3(0, -15.5, 0.075), WALK_M))
LINE_M = emis('lane_line', (0.75, 0.6, 0.2), 0.25)
for k in range(-12, 13): OUT.append(box('dash%d' % k, (2.4, 0.12, 0.01), X0 + V3(k * 5.0, -9.0, 0.005), LINE_M))
def windows(name, x0, x1, y_face, z0, floors, fh, face_dir, m_wall_frame=TRIM_M, lit_p=0.35, seed=0):
    rr = random.Random(seed); out = []; n = max(1, int((x1 - x0) / 1.8))
    for f in range(floors):
        for i in range(n):
            x = x0 + (i + 0.5) * (x1 - x0) / n; z = z0 + f * fh + fh * 0.55
            out.append(box(f'{name}_w{f}_{i}', (0.95, 0.06, 1.5), V3(x, y_face + 0.03 * face_dir, z), WINDOW_LIT if rr.random() < lit_p else GLASS_M))
            out.append(box(f'{name}_s{f}_{i}', (1.1, 0.16, 0.08), V3(x, y_face + 0.06 * face_dir, z - 0.78), m_wall_frame))
    return out
# across the street: a row of buildings to look past
for i in range(10):
    x = -40 + i * 9.5; h = random.Random(i).choice((10, 13, 16))
    OUT.append(box('far%d' % i, (9.3, 12, h), X0 + V3(x, -23, h / 2), FAR_BRICK_M))
    OUT += windows('far%d' % i, X0.x + x - 4.4, X0.x + x + 4.4, -17.0, 3.5, int((h - 3.5) / 3.2), 3.2, -1, lit_p=0.45, seed=i)
# up and down the block (beyond N and the lot)
for i, (x0, x1, h) in enumerate(((-30, -17, 12), (-17, -8, 10), (19, 28, 13), (28, 40, 10))):
    OUT.append(box('row%d' % i, (x1 - x0, 15, h), X0 + V3((x0 + x1) / 2, 7.5, h / 2), TAN_BRICK_M if i % 2 else FAR_BRICK_M))
    OUT += windows('row%d' % i, X0.x + x0 + 0.5, X0.x + x1 - 0.5, -0.0, 3.4, int((h - 3.4) / 3.2), 3.2, -1, lit_p=0.4, seed=10 + i)
# N: four floors; front, back and far side are walls; the side toward C (x = 0) is open inside behind C's wall
NH, NF = 13.0, 3.2
OUT.append(box('N_front', (8.0, 0.3, NH), X0 + V3(-4.0, 0.15, NH / 2), TAN_BRICK_M))
OUT.append(box('N_back', (8.0, 0.3, NH), X0 + V3(-4.0, 14.85, NH / 2), TAN_BRICK_M))
OUT.append(box('N_far', (0.3, 15, NH), X0 + V3(-7.85, 7.5, NH / 2), TAN_BRICK_M))
OUT.append(box('N_roof', (8.2, 15.2, 0.3), X0 + V3(-4.0, 7.5, NH), mat('roof_tar', (0.08, 0.08, 0.08), 0.8)))
OUT += windows('N', X0.x - 7.5, X0.x - 0.5, -0.0, 3.4, 3, NF, -1, lit_p=0.5, seed=3)
OUT.append(box('N_shop', (7.0, 0.05, 2.4), X0 + V3(-4.0, -0.03, 1.3), WINDOW_LIT))
ROOM = []                                                              # what shows when the wall is gone
PAINT = [noisy(mat('paint%d' % i, c, 0.85), 5.0, 0.08) for i, c in enumerate(((0.75, 0.68, 0.55), (0.55, 0.65, 0.72), (0.78, 0.6, 0.6), (0.6, 0.7, 0.55)))]
for f in range(4):
    z = f * NF
    ROOM.append(box('N_floor%d' % f, (8.0, 15, 0.25), X0 + V3(-4.0, 7.5, z + 0.125), noisy(mat('slab%d' % f, (0.5, 0.48, 0.45), 0.9), 6.0, 0.2)))
    for r, (y0, y1) in enumerate(((0.3, 5.5), (5.5, 10.0), (10.0, 14.7))):
        ROOM.append(box(f'N_rw{f}_{r}', (0.12, y1 - y0, NF - 0.25), X0 + V3(-3.2, (y0 + y1) / 2, z + 0.25 + (NF - 0.25) / 2), PAINT[(f + r) % 4]))
        ROOM.append(box(f'N_div{f}_{r}', (3.2, 0.12, NF - 0.25), X0 + V3(-1.6, y1, z + 0.25 + (NF - 0.25) / 2), PAINT[(f + r + 1) % 4]))
# the bedroom on the second floor (a bed, a lamp), a closet full of clothes next to it, like the photos described
BZ = NF + 0.25
ROOM.append(box('bed', (1.9, 1.5, 0.45), X0 + V3(-2.1, 3.0, BZ + 0.225), noisy(mat('bedding', (0.85, 0.85, 0.9), 0.9), 8.0, 0.15), 0.06, ss=1))
ROOM.append(box('headboard', (0.1, 1.6, 0.9), X0 + V3(-3.1, 3.0, BZ + 0.45), noisy(mat('headb', (0.35, 0.22, 0.15), 0.6), 10.0, 0.2)))
ROOM.append(box('pillow', (0.45, 0.6, 0.15), X0 + V3(-2.8, 3.0, BZ + 0.52), mat('pillow', (0.95, 0.95, 0.95), 0.9), 0.05, ss=1))
ROOM.append(box('lamp', (0.25, 0.25, 0.3), X0 + V3(-2.9, 4.2, BZ + 0.75), emis('lamp', (1.0, 0.8, 0.5), 5.0)))
CL_Y = 6.2
ROOM.append(box('closet_rod', (0.03, 2.4, 0.03), X0 + V3(-1.5, CL_Y + 1.2, BZ + 1.85), STEEL_M))
_cr = random.Random(7); CLOTH_C = [(0.15, 0.2, 0.45), (0.7, 0.1, 0.1), (0.1, 0.1, 0.1), (0.85, 0.85, 0.8), (0.3, 0.5, 0.3), (0.55, 0.45, 0.35), (0.9, 0.6, 0.2)]
CLOTH_M = [noisy(mat('cloth%d' % i, c, 0.95, sheen=0.5), 30.0, 0.2) for i, c in enumerate(CLOTH_C)]
y = CL_Y + 0.1
while y < CL_Y + 2.3:
    w = _cr.uniform(0.05, 0.11); h = _cr.uniform(0.7, 1.15)
    ROOM.append(box('cloth%.2f' % y, (0.5, w, h), X0 + V3(-1.5, y, BZ + 1.85 - h / 2), _cr.choice(CLOTH_M), 0.015)); y += w + 0.01
ROOM.append(box('dresser', (0.5, 1.0, 0.9), X0 + V3(-2.9, 8.4, BZ + 0.45), noisy(mat('dresser', (0.45, 0.32, 0.2), 0.5), 10.0, 0.2), 0.02))
OUT += ROOM
# C: three floors, red brick, the store at street level. Built as loose chunks that fall; each chunk keeps its own start and end place.
SLAB_M = noisy(mat('slab_c', (0.24, 0.2, 0.17), 0.9), 7.0, 0.35, 0.05)
CW, CD, CF, CH = 7.0, 14.0, 3.3, 9.9
CHUNKS = []
def chunk(name, size, loc, m):
    o = box(name, size, X0 + loc, m, 0.03); o.rotation_mode = 'QUATERNION'; CHUNKS.append(o); bpy.context.view_layer.update(); return o
for f in range(3):
    z = f * CF + CF / 2
    for i in range(4):                                                 # front wall panels (store glass on the ground floor)
        x = (i + 0.5) * CW / 4
        if f == 0:
            o = chunk(f'C_front0_{i}', (CW / 4, 0.3, CF), V3(x, 0.15, z), RED_BRICK_M)
            g_ = box(f'C_glass{i}', (CW / 4 - 0.2, 0.04, 2.2), X0 + V3(x, -0.02, 1.3), WINDOW_LIT); g_.parent = o; g_.matrix_parent_inverse = o.matrix_world.inverted()
        else:
            o = chunk(f'C_front{f}_{i}', (CW / 4, 0.3, CF), V3(x, 0.15, z), RED_BRICK_M)
            w_ = box(f'C_win{f}_{i}', (0.95, 0.06, 1.5), X0 + V3(x, -0.03, z + 0.15), WINDOW_LIT if (f + i) % 3 == 0 else GLASS_M); w_.parent = o; w_.matrix_parent_inverse = o.matrix_world.inverted()
            s_ = box(f'C_sill{f}_{i}', (1.1, 0.14, 0.08), X0 + V3(x, -0.06, z - 0.62), TRIM_M); s_.parent = o; s_.matrix_parent_inverse = o.matrix_world.inverted()
    for j in range(8):                                                 # the side over the pit, and the shared wall with N
        y_ = (j + 0.5) * CD / 8
        chunk(f'C_side{f}_{j}', (0.3, CD / 8, CF), V3(CW - 0.15, y_, z), RED_BRICK_M)
        chunk(f'C_party{f}_{j}', (0.3, CD / 8, CF), V3(0.15, y_, z), RED_BRICK_M)
    for i in range(4): chunk(f'C_back{f}_{i}', (CW / 4, 0.3, CF), V3((i + 0.5) * CW / 4, CD - 0.15, z), RED_BRICK_M)
    for i in range(2):
        for j in range(3): chunk(f'C_slab{f}_{i}{j}', (CW / 2 - 0.4, CD / 3 - 0.3, 0.3), V3((i + 0.5) * CW / 2, (j + 0.5) * CD / 3, (f + 1) * CF - 0.15), SLAB_M)
OUT.append(box('C_cornice', (CW + 0.2, 0.5, 0.4), X0 + V3(CW / 2, 0.0, CH + 0.2), TRIM_M)); C_CORNICE = OUT[-1]; C_CORNICE.rotation_mode = 'QUATERNION'; CHUNKS.append(C_CORNICE)
OUT.append(box('awning', (CW - 0.4, 1.1, 0.12), X0 + V3(CW / 2, -0.55, 2.75), noisy(mat('awning', (0.12, 0.3, 0.18), 0.8), 6.0, 0.15)))
AWNING = OUT[-1]; AWNING.rotation_mode = 'QUATERNION'; CHUNKS.append(AWNING)
# the lot: a pit with dirt walls, a plywood fence on the street, a ramp
LX0, LX1, LY0, LY1, PD = 7.3, 18.6, 0.5, 14.3, 3.0
OUT.append(box('pit_floor', (LX1 - LX0, LY1 - LY0, 0.2), X0 + V3((LX0 + LX1) / 2, (LY0 + LY1) / 2, -PD - 0.1), DIRT_M))
OUT.append(box('pit_wN', (LX1 - LX0, 0.4, PD), X0 + V3((LX0 + LX1) / 2, LY1 + 0.2, -PD / 2), DIRT_M))
OUT.append(box('pit_wS', (LX1 - LX0, 0.4, PD), X0 + V3((LX0 + LX1) / 2, LY0 - 0.2, -PD / 2), DIRT_M))
OUT.append(box('pit_wE', (0.4, LY1 - LY0, PD), X0 + V3(LX1 + 0.2, (LY0 + LY1) / 2, -PD / 2), DIRT_M))
OUT.append(box('pit_wW', (0.4, LY1 - LY0, PD), X0 + V3(LX0 - 0.2, (LY0 + LY1) / 2, -PD / 2), DIRT_M))
OUT.append(box('lot_rim', (12, 15, 0.1), X0 + V3(13.0, 7.5, -0.05), DIRT_M)); OUT[-1].hide_render = True    # (the pit cuts the ground; only its rim shows)
for i, (x0, x1, y0, y1) in enumerate(((7.0, 19.0, 0.0, 0.5), (7.0, 19.0, 14.3, 15.0), (18.6, 19.0, 0.5, 14.3), (7.0, 7.3, 0.5, 14.3))):
    OUT.append(box('rim%d' % i, (x1 - x0, y1 - y0, 0.1), X0 + V3((x0 + x1) / 2, (y0 + y1) / 2, -0.05), DIRT_M))
PLY_M = noisy(mat('plywood', (0.6, 0.48, 0.3), 0.8), 4.0, 0.3)
for i in range(5): OUT.append(box('ply%d' % i, (2.4, 0.04, 2.4), X0 + V3(7.4 + 1.2 + i * 2.42, -0.15, 1.2), PLY_M))
for k in range(9):                                                     # shoring piles along the pit wall
    OUT.append(box('pile%d' % k, (0.25, 0.25, PD + 0.4), X0 + V3(LX0 + 0.1, LY0 + 0.6 + k * 1.6, -PD / 2 + 0.2), STEEL_M))
# where every chunk ends up: dropped one by one into a height map of the pit and the lot (so they stack, not overlap much)
_hm_res = 0.25; _hx0, _hy0 = -0.5, -0.5; _hnx, _hny = int(21 / _hm_res), int(16 / _hm_res)
HM = np.zeros((_hnx, _hny))
for i in range(_hnx):
    for j in range(_hny):
        x, y = _hx0 + i * _hm_res, _hy0 + j * _hm_res
        if LX0 < x < LX1 and LY0 < y < LY1: HM[i, j] = -PD
_er = random.Random(17)
C_T0, C_T1, C_REL = {}, {}, {}
for o in sorted(CHUNKS, key=lambda o_: (o_.location.z, -o_.location.x)):
    C_T0[o.name] = (o.location.copy(), o.rotation_quaternion.copy())
    lx = o.location.x - X0.x; ly = o.location.y - X0.y; lz = o.location.z
    tx = _er.uniform(LX0 + 1.2, LX1 - 1.2) if _er.random() < 0.8 else _er.uniform(LX0 + 0.8, LX0 + 4.0); ty = clamp(ly + _er.uniform(-2.5, 2.5), LY0 + 1.0, LY1 - 1.0)
    if lz < 2.0 and lx < 3.0: tx = clamp(lx + _er.uniform(0.5, 3.5), 0.6, 9.0)          # the bottom of the street-side ends up in a heap on its own lot
    dims = o.dimensions; flat = sorted(dims)[::-1]
    i0 = int((tx - flat[0] / 2 - _hx0) / _hm_res); i1 = int((tx + flat[0] / 2 - _hx0) / _hm_res) + 1
    j0 = int((ty - flat[1] / 2 - _hy0) / _hm_res); j1 = int((ty + flat[1] / 2 - _hy0) / _hm_res) + 1
    i0, j0 = max(i0, 0), max(j0, 0); i1, j1 = min(i1, _hnx), min(j1, _hny)
    base = float(HM[i0:i1, j0:j1].mean()) if i1 > i0 and j1 > j0 else 0.0
    zt = base + flat[2] / 2
    if i1 > i0 and j1 > j0: HM[i0:i1, j0:j1] = np.maximum(HM[i0:i1, j0:j1] + flat[2] * 0.9, base + flat[2] * 0.6)
    # lay it down flat (its thinnest side up), with a tilt and a random turn
    d_ = o.dimensions; thin = int(np.argmin([d_.x, d_.y, d_.z]))
    q_flat = {0: Euler((0, R(90), 0)), 1: Euler((R(90), 0, 0)), 2: Euler((0, 0, 0))}[thin].to_quaternion()
    q = Euler((R(_er.uniform(-18, 18)), R(_er.uniform(-18, 18)), R(_er.uniform(0, 360)))).to_quaternion() @ q_flat
    C_T1[o.name] = (X0 + V3(tx, ty, zt), q); C_REL[o.name] = _er.uniform(0.0, 0.35) + 0.25 * clamp(1 - lz / CH, 0, 1) * 0 + 0.3 * clamp((7 - lx) / 7, 0, 1)
PIVOT = X0 + V3(CW, 0, 0)
def c_collapse(k):
    """k 0..1 over the collapse beat: lean toward the pit, then the chunks break off and fall in"""
    lean = R(14) * smooth(0.0, 0.4, k)
    Rl = Matrix.Rotation(-lean, 4, 'Y')
    for o in CHUNKS:
        p0, q0 = C_T0[o.name]; p1, q1 = C_T1[o.name]
        pl = PIVOT + (Rl @ (p0 - PIVOT).to_4d()).to_3d() if True else p0; ql = Rl.to_quaternion() @ q0
        s_ = 0.22 + 0.45 * C_REL[o.name]; f = clamp((k - s_) / 0.42, 0, 1); f2 = f * f
        p = pl.lerp(p1, f2); p.z += 1.2 * math.sin(math.pi * f) * (1 - f)
        o.location = p; o.rotation_quaternion = ql.slerp(q1, sm(f))
def c_rest():
    for o in CHUNKS: o.location, o.rotation_quaternion = C_T1[o.name]
def c_intact():
    for o in CHUNKS: o.location, o.rotation_quaternion = C_T0[o.name]
# rescue gear for the night: light towers, a fire truck with flashing lights, a drone, flashlight beams
RED_PAINT = noisy(mat('truck_red', (0.6, 0.03, 0.03), 0.35, coat=0.8), 10.0, 0.08)
TRUCK = [box('truck_body', (9.0, 2.5, 2.6), X0 + V3(26.0, -6.0, 1.7), RED_PAINT, 0.1),
         box('truck_cab', (2.4, 2.5, 2.9), X0 + V3(32.0, -6.0, 1.85), RED_PAINT, 0.15),
         box('truck_wind', (0.05, 2.2, 1.0), X0 + V3(33.2, -6.0, 2.5), GLASS_M),
         box('truck_ladder', (8.5, 1.0, 0.25), X0 + V3(25.5, -6.0, 3.15), mat('ladder', (0.75, 0.75, 0.78), 0.3, metal=0.8)),
         box('truck_stripe', (11.5, 2.52, 0.18), X0 + V3(27.0, -6.0, 1.2), mat('stripe', (0.9, 0.9, 0.85), 0.4))]
for i, x in enumerate((23.0, 25.0, 31.5)):
    for sy in (-1, 1): TRUCK.append(prim('cylinder', f'wheel{i}{sy}', mat('tire', (0.03, 0.03, 0.03), 0.8), loc=X0 + V3(x, -6.0 + 1.25 * sy, 0.5), rot=(R(90), 0, 0), radius=0.5, depth=0.35))
BAR_R = emis('bar_red', (1.0, 0.05, 0.03), 0.0); BAR_W = emis('bar_white', (1.0, 0.95, 0.9), 0.0)
TRUCK += [box('lightbar_r', (0.3, 1.0, 0.15), X0 + V3(32.6, -6.45, 3.4), BAR_R), box('lightbar_w', (0.3, 1.0, 0.15), X0 + V3(32.6, -5.55, 3.4), BAR_W)]
TRUCK_L = [light_at('truck_red_l', 'POINT', X0 + V3(32.6, -6.6, 3.8), X0, 0.0, (1.0, 0.08, 0.04), 0.3), light_at('truck_wht_l', 'POINT', X0 + V3(32.6, -5.4, 3.8), X0, 0.0, (1.0, 0.9, 0.8), 0.3)]
TOWER_M = mat('tower', (0.85, 0.75, 0.1), 0.5)
TOWERS, TOWER_L = [], []
for i, (x, y) in enumerate(((5.5, -2.5), (19.5, -2.0))):
    TOWERS.append(box('mast%d' % i, (0.15, 0.15, 7.5), X0 + V3(x, y, 3.75), STEEL_M))
    TOWERS.append(box('lamps%d' % i, (1.4, 0.3, 0.6), X0 + V3(x, y, 7.6), emis('lamps%d' % i, (1.0, 0.95, 0.85), 30.0), rot=(R(-35), 0, 0)))
    TOWER_L.append(light_at('tower_l%d' % i, 'SPOT', X0 + V3(x, y + 0.3, 7.4), X0 + V3(11.5 - 2 * i, 7.0, -2.5), 0.0, (1.0, 0.94, 0.85), 0.6))
    TOWER_L[-1].data.spot_size = R(70); TOWER_L[-1].data.spot_blend = 0.4
DRONE = [box('drone_body', (0.35, 0.35, 0.12), V3(0, 0, 0), mat('drone', (0.1, 0.1, 0.11), 0.4), 0.03)]
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        a_ = box(f'drone_arm{sx_}{sy_}', (0.36, 0.04, 0.03), V3(sx_ * 0.16, sy_ * 0.16, 0), DRONE[0].data.materials[0], rot=(0, 0, R(45 * sx_ * sy_))); a_.parent = DRONE[0]; DRONE.append(a_)
        r_ = prim('cylinder', f'drone_rot{sx_}{sy_}', mat('rotor', (0.2, 0.2, 0.22), 0.5, alpha=0.5), loc=V3(sx_ * 0.3, sy_ * 0.3, 0.05), radius=0.13, depth=0.005); r_.parent = DRONE[0]; DRONE.append(r_)
DRONE_RED = emis('drone_red', (1.0, 0.1, 0.05), 0.0); DRONE_GRN = emis('drone_grn', (0.1, 1.0, 0.2), 0.0)
for i, (mx_, px_) in enumerate(((DRONE_RED, -0.3), (DRONE_GRN, 0.3))):
    b_ = prim('uv_sphere', 'drone_led%d' % i, mx_, loc=V3(px_, 0.3, -0.03), radius=0.03); b_.parent = DRONE[0]; DRONE.append(b_)
DRONE_SPOT = light_at('drone_spot', 'SPOT', V3(0, 0, -0.1), V3(0, 0, -5), 0.0, (0.9, 0.95, 1.0), 0.05); DRONE_SPOT.parent = DRONE[0]
DRONE_SPOT.location = V3(0, 0, -0.1); DRONE_SPOT.rotation_quaternion = Quaternion((1, 0, 0, 0)); DRONE_SPOT.data.spot_size = R(30); DRONE_SPOT.data.spot_blend = 0.5
def beam_mat(name):
    """a flashlight beam through dusty night air: a cone that fades along its length and at its edges"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sx.inputs['Vector'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    a_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', sx.outputs['Z'], 1.6), math_(nt, 'POWER', lw.outputs['Facing'], 3.0)), 0.7)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.95, 0.8, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'on'), 3.0), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY', a_, objattr(nt, 'on')), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
BEAMS_M = beam_mat('torch_beam')
TBEAMS = []
for i in range(5):
    o = prim('cone', 'tbeam%d' % i, BEAMS_M, radius1=0.9, radius2=0.03, depth=7.0, vertices=24); o.visible_shadow = False; o['on'] = 0.0; o.rotation_mode = 'QUATERNION'
    TBEAMS.append(o)
def torch(o, src, dst, on):
    """cone apex at src pointing at dst (length = distance)"""
    d_ = Vector(dst) - Vector(src); L_ = d_.length; o.scale = (L_ / 7.0 * 0.6 + 0.4, L_ / 7.0 * 0.6 + 0.4, L_ / 7.0)
    o.rotation_quaternion = (-d_).to_track_quat('Z', 'Y'); o.location = Vector(src) + d_ * 0.5; o['on'] = on
STREETL = [light_at('streetlamp%d' % i, 'POINT', X0 + V3(x, -3.0, 7.5), X0, 0.0, (1.0, 0.6, 0.25), 0.3) for i, x in enumerate((-14, 3, 22))]
for i, x in enumerate((-14, 3, 22)):
    OUT.append(box('lpole%d' % i, (0.15, 0.15, 7.5), X0 + V3(x, -2.7, 3.75), STEEL_M)); OUT.append(box('lhead%d' % i, (0.6, 0.3, 0.18), X0 + V3(x, -3.0, 7.55), emis('lhead%d' % i, (1.0, 0.65, 0.3), 0.0)))
SUN_L = bpy.data.lights.new('dusk_sun', 'SUN'); SUN_L.energy = 2.5; SUN_L.color = (1.0, 0.7, 0.45); SUN_L.angle = R(3)
SUN_O = bpy.data.objects.new('dusk_sun', SUN_L); S.collection.objects.link(SUN_O); SUN_O.rotation_euler = (R(78), 0, R(-115))
SKY_M = bpy.data.materials.new('sky_out'); SKY_M.use_nodes = True
OUT_GEAR = TRUCK + TRUCK_L + TOWERS + TOWER_L + DRONE + [DRONE_SPOT] + TBEAMS
OUTSET = OUT + CHUNKS + OUT_GEAR + STREETL + [SUN_O]
OUTSET = list(dict.fromkeys(OUTSET))
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
# sneakers painted onto his feet (every face mostly weighted to the foot and toe bones), so nothing can clip through them
SHOE_M = noisy(mat('sneaker', (0.07, 0.07, 0.08), 0.6), 60.0, 0.15); SOLE_M = mat('sole', (0.85, 0.85, 0.82), 0.7)
BODY.data.materials.append(SHOE_M); BODY.data.materials.append(SOLE_M); _shoe_i = len(BODY.data.materials) - 2
_vgn = {g.index: g.name for g in BODY.vertex_groups}
_footw = np.zeros(len(BODY.data.vertices))
for v in BODY.data.vertices:
    _footw[v.index] = sum(g.weight for g in v.groups if _vgn[g.group].startswith(('foot.', 'toe')))
for p_ in BODY.data.polygons:
    w_ = float(np.mean([_footw[i] for i in p_.vertices]))
    if w_ > 0.45:
        zc = sum(BODY.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices)
        p_.material_index = _shoe_i + 1 if zc < 0.018 else _shoe_i
# ================================================================ THE CEILING COMES DOWN (collapse clock cc: 0 = frame one; pieces with
# a negative release time are already falling at frame one, so the end of the last beat runs straight into it)
G_ = 9.81
# ceiling tiles (a grid; the middle ones drop), joists above them (the middle ones break and sag), bricks from the floor above
CEIL_TILES = []; _rc = random.Random(11)
for i in range(10):
    for j in range(7):
        x = -SX + 0.3 + i * 0.6; y = -SY + 0.6 + j * 1.2 - 0.0
        if j == 6: continue
        o = box('ctile%d_%d' % (i, j), (0.58, 1.18, 0.025), V3(x, y, SH - 0.0125), CEIL_M)
        CEIL_TILES.append(o)
STORE[1].hide_render = True                                         # the solid ceiling is replaced by the tile grid
VOID_M = mat('void', (0.03, 0.028, 0.025), 0.95)
STORE.append(box('above', (2 * SX, 2 * SY, 0.05), V3(0, 0, SH + 0.6), VOID_M)); ABOVE = STORE[-1]     # the dark underside of the floor above
JOISTS = [box('joist%d' % k, (0.06, 2 * SY, 0.26), V3(-SX + 0.2 + k * 0.4, 0, SH + 0.2), WOOD_M) for k in range(15)]
STORE += JOISTS
for o in JOISTS: o['x0'] = o.location.x
PIECES = []                                                          # (object, p0, v0, rot0, w, release, rest_z)
def add_piece(o, p0, s_, v0=(0, 0, 0), w=(0, 0, 0), rest=None):
    o.rotation_mode = 'XYZ'; PIECES.append(dict(o=o, p0=Vector(p0), v0=Vector(v0), r0=Vector(o.rotation_euler), w=Vector(w), s=s_, rest=rest)); return o
def far_from_him(x, y, r=0.55): return (Vector((x, y)) - M0.xy).length > r
# the tiles over the middle fall first, the one right over his head last (still above him when the beat cuts)
DROP_TILES = []
for o in CEIL_TILES:
    x, y = o.location.x, o.location.y
    if abs(x - M0.x) < 1.3 and abs(y - M0.y) < 2.6:
        over_him = abs(x - M0.x) < 0.31 and abs(y - M0.y) < 0.6
        s_ = 1.5 if over_him else _rc.uniform(-0.75, 1.1)
        near = (Vector((x, y)) - M0.xy).length < 1.05
        w = (0, 0, 0) if over_him else ((_rc.uniform(-0.4, 0.4), _rc.uniform(-0.4, 0.4), 0) if near else (_rc.uniform(-3, 3), _rc.uniform(-3, 3), _rc.uniform(-1, 1)))
        add_piece(o, o.location.copy(), s_, (0, 0, 0) if near else (_rc.uniform(-0.3, 0.3), _rc.uniform(-0.3, 0.3), 0), w, 0.02); DROP_TILES.append(o)
        if over_him: HEAD_TILE = o
# bricks and plaster chunks raining down from the gap (kept out of a circle round him; he isn't hit on screen)
BRICKS = []
for k in range(90):
    while True:
        x = _rc.uniform(-1.05, 1.25); y = M0.y + _rc.uniform(-2.4, 2.0)
        if far_from_him(x, y, 0.62): break
    if _rc.random() < 0.7:
        o = box('fbrick%d' % k, (0.2, 0.095, 0.06), V3(x, y, SH + 0.3), LOOSE_BRICK_M, 0.006); rz = 0.03
    else:
        s3 = _rc.uniform(0.12, 0.3); o = prim('ico_sphere', 'chunk%d' % k, PLASTER_M, loc=V3(x, y, SH + 0.3), subdivisions=1, radius=s3, scale=(1, _rc.uniform(0.5, 1), _rc.uniform(0.3, 0.6))); rz = s3 * 0.35
    o.rotation_euler = (_rc.uniform(0, 6), _rc.uniform(0, 6), _rc.uniform(0, 6))
    add_piece(o, V3(x, y, SH + _rc.uniform(0.1, 0.9)), _rc.uniform(-0.8, 1.6), (_rc.uniform(-0.4, 0.4), _rc.uniform(-0.4, 0.4), _rc.uniform(-1, 0)),
              (_rc.uniform(-8, 8), _rc.uniform(-8, 8), _rc.uniform(-4, 4)), rz); BRICKS.append(o)
# the troffer over him swings down on one wire and sparks (its glow flickers)
SWING = TROFFERS[3]; SWING['y0'] = SWING.location.y
FALLERS = [p['o'] for p in PIECES]
def fall(cc):
    """place every falling piece at collapse-clock time cc"""
    for p in PIECES:
        tau = cc - p['s']; o = p['o']
        if tau <= 0: o.location = p['p0']; o.rotation_euler = p['r0']; continue
        z = p['p0'].z + p['v0'].z * tau - 0.5 * G_ * tau * tau
        if z <= p['rest']:                                          # landed: solve the landing time, freeze there
            a_, b_, c_ = -0.5 * G_, p['v0'].z, p['p0'].z - p['rest']; tl = (-b_ - math.sqrt(b_ * b_ - 4 * a_ * c_)) / (2 * a_); tau = tl; z = p['rest']
        o.location = V3(p['p0'].x + p['v0'].x * tau, p['p0'].y + p['v0'].y * tau, z); o.rotation_euler = p['r0'] + p['w'] * tau
    for o in JOISTS:                                                  # middle joists crack and sag in a V
        k = max(0.0, 1 - abs(o['x0'] - M0.x) / 1.3)
        o.rotation_euler = (0, R(9) * k * (1 if o['x0'] > M0.x else -1) * smooth(-0.9, 0.4, cc), 0); o.location.z = SH + 0.2 - 0.32 * k * smooth(-0.9, 0.6, cc)
    a_ = smooth(-0.3, 0.6, cc); SWING.rotation_euler = (R(-55) * a_ + R(6) * math.sin(cc * 9) * a_, 0, 0); SWING.location.z = SH - 0.02 - 0.32 * a_
# grit: one mesh of small specks raining through the gap (moved every frame)
NGRIT = 500; _gr = np.random.default_rng(5)
GR_P0 = np.stack([_gr.uniform(-1.1, 1.3, NGRIT), M0.y + _gr.uniform(-2.6, 2.2, NGRIT), SH + _gr.uniform(0.0, 0.6, NGRIT)], 1)
GR_S = _gr.uniform(-1.0, 3.5, NGRIT); GR_R = _gr.uniform(0.004, 0.014, NGRIT); GR_V = _gr.uniform(0.2, 1.0, NGRIT)
_tet = np.array([(1, 1, 1), (-1, -1, 1), (-1, 1, -1), (1, -1, -1)], float) / 1.732
GRIT = mesh('grit', [tuple(v) for v in np.repeat(GR_P0, 4, 0) + np.tile(_tet, (NGRIT, 1)) * np.repeat(GR_R, 4)[:, None]],
            [(4 * i, 4 * i + 1, 4 * i + 2) for i in range(NGRIT)] + [(4 * i, 4 * i + 3, 4 * i + 1) for i in range(NGRIT)] + [(4 * i, 4 * i + 2, 4 * i + 3) for i in range(NGRIT)] + [(4 * i + 1, 4 * i + 3, 4 * i + 2) for i in range(NGRIT)],
            mat('grit', (0.55, 0.52, 0.47), 0.95), smooth_=False)
GRIT.visible_shadow = False
def grit(cc, rate=1.0):
    tau = np.clip(cc - GR_S, 0, None) * GR_V
    P = GR_P0.copy(); P[:, 2] = np.where(tau > 0, GR_P0[:, 2] - (0.5 * G_ * (tau % 0.95) ** 2) * rate, GR_P0[:, 2]); P[:, 2] = np.maximum(P[:, 2], 0.01)
    V_ = np.repeat(P, 4, 0) + np.tile(_tet, (NGRIT, 1)) * np.repeat(GR_R, 4)[:, None]; GRIT.data.vertices.foreach_set('co', V_.ravel().astype(np.float32)); GRIT.data.update()
# dust: soft see-through cards that billow (noise moves with 'tt'); kept in front of the far wall
def dust_mat(name, col=(0.62, 0.58, 0.52), dens=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 0.25), nz.inputs['W'])
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; nt.links.new(tc.outputs['Generated'], gr.inputs['Vector'])
    # generated coords run 0..1; centre the sphere
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-0.5, -0.5, -0.5); mp.inputs['Scale'].default_value = (2, 2, 2)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
    a_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', gr.outputs['Fac'], 1.5), math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.38), 0.0)), objattr(nt, 'dens'))
    a_ = math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', a_, 4.0 * dens), 0.85)
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = (*col, 1)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = 0.08
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(df.outputs['BSDF'], ad.inputs[0]); nt.links.new(em.outputs['Emission'], ad.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(a_, mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(ad.outputs['Shader'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None; return m
DUST_M = dust_mat('dust')
DUST = []
for k in range(5):
    o = prim('plane', 'dust%d' % k, DUST_M, size=1.0); o.scale = (3.2, 3.2, 1); o['tt'] = 0.0; o['dens'] = 0.0; o.visible_shadow = False
    o['k'] = k; DUST.append(o)
def dust(cc_or_t, dens, center, cam_pos, spread=1.0, rise=0.0):
    """cards face the camera, spread round 'center'"""
    for o in DUST:
        k = o['k']; off = V3(math.sin(k * 2.1) * 0.9, math.cos(k * 1.7) * 0.9, 0.3 * (k - 2)) * spread + V3(0, 0, rise * (0.3 + 0.2 * k) * cc_or_t)
        o.location = Vector(center) + off; d_ = Vector(cam_pos) - o.location; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d_.to_track_quat('Z', 'Y')
        o['tt'] = cc_or_t + k * 3.1; o['dens'] = dens; o.scale = (3.2 * spread, 3.2 * spread, 1)
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
# ================================================================ HIS POSES (built from the hip, a body turn, and hands/feet in his own frame)
def body_eval():
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); rp = rp.reshape(-1, 3); oe.to_mesh_clear()
    M_ = np.array(BODY.matrix_world); return co @ M_[:3, :3].T + M_[:3, 3], rp
FOOT = {}
for s_ in ('R', 'L'):
    e_ = empty('tgt_foot' + s_); e_.rotation_mode = 'QUATERNION'
    c_ = PB['foot.' + s_].constraints.new('COPY_ROTATION'); c_.target = e_; c_.owner_space = c_.target_space = 'WORLD'
    FOOT[s_] = (e_, RB['foot.' + s_].matrix_local.to_3x3(), c_)
def feet_flat(on=True, phi=0.0):
    for s_ in 'RL':
        e_, M0_, c_ = FOOT[s_]; c_.influence = 1.0 if on else 0.0; e_.rotation_quaternion = (Matrix.Rotation(R(phi), 3, 'X') @ M0_).to_quaternion()
def rigM(hip, rot):
    Rm = Euler(tuple(R(x) for x in rot)).to_matrix(); return Matrix.Translation(Vector(hip) - Rm @ HIP0) @ Rm.to_4x4()
def body(hip, rot, ankR, ankL, handR, handL, space='rig', neck=0.0, head=0.0, jaw=0.0, lids=0.0, curl=(0.3, 0.3), pk=(1.0, 1.0),
         palm=None, spine=0.0, kneel_pole=False, head_yaw=0.0):
    M = rigM(hip, rot); M3 = M.to_3x3()
    aR = M @ Vector(ankR) if space == 'rig' else Vector(ankR); aL = M @ Vector(ankL) if space == 'rig' else Vector(ankL)
    kp = V3(0, -2.0, 0.4) if not kneel_pole else V3(0, -2.0, -0.6)
    set_pose(hip, rot, spine, neck, head, head_yaw, 0.0, ankR=aR, poleR=M @ (V3(-0.15, 0, 0.5) + kp), ankL=aL, poleL=M @ (V3(0.15, 0, 0.5) + kp),
             curlR=curl[0], curlL=curl[1], lids=lids, jaw=jaw, poleArmR=M @ V3(-0.8, 0.6 * pk[0], 1.0), poleArmL=M @ V3(0.8, 0.6 * pk[1], 1.0))
    for s_, hp_ in (('R', handR), ('L', handL)):
        if palm and s_ in palm:
            c_, fd, pd = palm[s_]; place_hand(s_, M @ Vector(c_), M3 @ Vector(fd), M3 @ Vector(pd), 1.0)
        else: TGT['hand' + s_].location = M @ Vector(hp_); HAND[s_][2].influence = 0.0
    bpy.context.view_layer.update(); return M
STAND_HIP = 0.93
def stand(t, look_up=0.0, brace=0.0, yaw=0.0):
    """in the aisle at M0, facing -y (+yaw turns him); look_up tips his head back to the ceiling; brace: knees bend, arms over his head"""
    x, y = M0.x, M0.y
    hip = V3(x, y, STAND_HIP - 0.1 * brace); rot = (4 * brace + 1.5 * wob(t, 3, 1) * brace, 0, yaw)
    Rz = Matrix.Rotation(R(yaw), 3, 'Z'); aR = V3(x, y, 0) + Rz @ V3(-0.14, 0.02, 0.09); aL = V3(x, y, 0) + Rz @ V3(0.14, 0.02, 0.09)
    hR = V3(-0.27, 0.02, 0.86).lerp(V3(-0.14, -0.2, 1.86), brace); hL = V3(0.27, 0.02, 0.86).lerp(V3(0.14, -0.18, 1.84), brace)
    for s_ in 'RL': FOOT[s_][2].influence = 1.0; FOOT[s_][0].rotation_quaternion = (Rz @ FOOT[s_][1]).to_quaternion()
    body(hip, rot, aR, aL, hR, hL, space='world', neck=-14 * look_up + 6 * brace, head=-18 * look_up, jaw=0.25 * look_up + 0.25 * brace,
         lids=0.45 * brace, curl=(0.25 + 0.45 * brace,) * 2, pk=(1 - 1.6 * brace, 1 - 1.6 * brace))
    ground(0.0)
PIN_HIP = V3(M0.x, M0.y, 0.12)
def pinned(t, wince=0.0, look=0.0, armL=None):
    """on his back on the store floor, head toward +y; right arm out on the floor by his shoulder (the IV goes in there), left hand
    on his chest; legs straight under the rubble. Small moves only (the mound and the beam are built round this pose)"""
    feet_flat(False); hip = PIN_HIP.copy(); rot = (-88, 0, 0)
    aR, aL = V3(-0.13, 0.04, 0.1), V3(0.15, 0.02, 0.1)
    hR = V3(-0.62, 0.06, 1.22); hL = armL if armL is not None else V3(0.45, 0.06, 0.95)
    body(hip, rot, aR, aL, hR, hL, neck=lerp(-6, 8, look) + 3 * wob(t, 0.6, 2), head=lerp(0, 14, look), head_yaw=8 * wob(t, 0.4, 5),
         lids=lerp(0.35, 0.85, wince), jaw=lerp(0.1, 0.45, wince), curl=(0.35, 0.55), pk=(0.4, 0.4))
def deform(rest_pt, bone):
    """a point given in his rest space, carried along by one bone (world)"""
    pb = PB[bone]; return RIG.matrix_world @ (pb.matrix @ RB[bone].matrix_local.inverted()) @ Vector(rest_pt)
def ground(kneel=0.0, passes=4):
    for _ in range(passes):
        W, RP = body_eval(); moved = 0.0
        for s_, sg in (('R', -1.0), ('L', 1.0)):
            mn = float(W[(RP[:, 2] < 0.1) & (RP[:, 0] * sg > 0), 2].min()); d = clamp(0.001 - mn, -0.03, 0.03)
            if abs(d) > 0.0004: TGT['ank' + s_].location.z += d; moved = max(moved, abs(d))
        if moved < 0.0005: break
        bpy.context.view_layer.update()

# ================================================================ THE PILE ON HIM (built once, round the pinned pose, so nothing goes through him)
def skin_points():
    """posed skin of the body and the clothes (world, numpy)"""
    out = []
    for o in (BODY, SUIT):
        dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
        co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); oe.to_mesh_clear(); M_ = np.array(o.matrix_world)
        out.append(co @ M_[:3, :3].T + M_[:3, 3])
    return np.concatenate(out)
pinned(0.0); bpy.context.view_layer.update()
_W, _RP = body_eval(); BODY_MINZ = float(_W[:, 2].min()); RIG.location.z += 0.003 - BODY_MINZ; PIN_HIP.z += 0.003 - BODY_MINZ; bpy.context.view_layer.update()
SKIN = skin_points()
MOUND_Y1 = M0.y - 0.16                                       # the mound covers him from mid-thigh (this y) down past his feet
GX0, GX1, GY0, GY1, GH = M0.x - 0.95, M0.x + 0.95, M0.y - 1.45, MOUND_Y1, 0.02
nx_, ny_ = int(round((GX1 - GX0) / GH)) + 1, int(round((GY1 - GY0) / GH)) + 1
TOP = np.full((nx_, ny_), -1.0)
_ix = np.round((SKIN[:, 0] - GX0) / GH).astype(int); _iy = np.round((SKIN[:, 1] - GY0) / GH).astype(int)
_ok = (_ix >= 0) & (_ix < nx_) & (_iy >= 0) & (_iy < ny_)
np.maximum.at(TOP, (_ix[_ok], _iy[_ok]), SKIN[_ok, 2])
from scipy.ndimage import maximum_filter, gaussian_filter
COVER = maximum_filter(TOP, size=7); COVER = np.where(COVER > 0, COVER + 0.04, 0.0)
_xs = np.linspace(GX0, GX1, nx_)[:, None]; _ys = np.linspace(GY0, GY1, ny_)[None, :]
_rn = np.random.default_rng(3)
PROF = 0.36 * np.exp(-((_xs - M0.x) / 0.5) ** 2) * (0.8 + 0.2 * np.sin(_ys * 7.0)) * np.clip((GY1 - _ys) / 0.12, 0, 1) ** 0.5
PROF *= np.clip((_ys - GY0) / 0.35, 0, 1) ** 0.7
PROF += gaussian_filter(_rn.normal(0, 0.05, (nx_, ny_)), 1.2) * (PROF > 0.02)
H = np.maximum(gaussian_filter(np.maximum(COVER, PROF), 1.0), COVER)
H = np.maximum(H, 0.0)
def mound_h(x, y):
    i = int(round((x - GX0) / GH)); j = int(round((y - GY0) / GH))
    if 0 <= i < nx_ and 0 <= j < ny_: return float(H[i, j])
    return 0.0
_vs = [(GX0 + i * GH, GY0 + j * GH, float(H[i, j]) - 0.004) for i in range(nx_) for j in range(ny_)]
_fs = [(i * ny_ + j, (i + 1) * ny_ + j, (i + 1) * ny_ + j + 1, i * ny_ + j + 1) for i in range(nx_ - 1) for j in range(ny_ - 1)]
def rubble_mat():
    m = mat('rubble', (0.42, 0.36, 0.3), 0.95); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 22.0; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); el = cr.color_ramp.elements
    el[0].color = (0.32, 0.12, 0.08, 1); el[1].color = (0.62, 0.6, 0.55, 1); el.new(0.45).color = (0.25, 0.22, 0.2, 1); el.new(0.7).color = (0.48, 0.2, 0.12, 1)
    nt.links.new(vo.outputs['Color'], cr.inputs['Fac']) if False else nt.links.new(vo.outputs['Distance'], cr.inputs['Fac'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60.0; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.5
    nt.links.new(cr.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.9; bp.inputs['Distance'].default_value = 0.03
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
RUBBLE_M = rubble_mat()
MOUND = mesh('mound', _vs, _fs, RUBBLE_M)
MOUND_H0 = np.array(_vs)[:, 2].copy()
# bricks and chunks sitting on the mound (above it; the mound is above him), and strewn round him on the floor (not on him)
PILE = []
_pr = random.Random(21); _occ = np.zeros((int(4.0 / 0.05), int(6.0 / 0.05)), bool)
def on_body(x, y, r=0.16):
    d = np.hypot(SKIN[:, 0] - x, SKIN[:, 1] - y); return bool((d < r).any())
for k in range(70):
    x = M0.x + _pr.uniform(-0.75, 0.75); y = _pr.uniform(GY0 + 0.1, GY1 - 0.05)
    h0 = mound_h(x, y)
    if h0 < 0.04: continue
    hz = max(h0, mound_h(x + 0.1, y), mound_h(x - 0.1, y), mound_h(x, y + 0.05), mound_h(x, y - 0.05))
    o = box('pbrick%d' % k, (0.2, 0.095, 0.06), V3(x, y, hz + 0.028), LOOSE_BRICK_M, 0.006, rot=(R(_pr.uniform(-12, 12)), R(_pr.uniform(-12, 12)), R(_pr.uniform(0, 180))))
    PILE.append(o)
for k in range(140):
    x = M0.x + _pr.uniform(-1.3, 1.3); y = M0.y + _pr.uniform(-2.0, 1.9)
    if on_body(x, y, 0.22) or (GX0 < x < GX1 and GY0 < y < GY1 + 0.15): continue
    if _pr.random() < 0.65: o = box('fbr%d' % k, (0.2, 0.095, 0.06), V3(x, y, 0.03), LOOSE_BRICK_M, 0.006, rot=(0, 0, R(_pr.uniform(0, 180))))
    else:
        s3 = _pr.uniform(0.08, 0.22); o = prim('ico_sphere', 'fch%d' % k, PLASTER_M, loc=V3(x, y, s3 * 0.25), subdivisions=1, radius=s3, scale=(1, _pr.uniform(0.6, 1), 0.35))
    PILE.append(o)
# the broken ceiling tiles leaning on the pile, a cracked joist on the floor beyond his head
for k in range(8):
    x = M0.x + _pr.choice((-1, 1)) * _pr.uniform(0.6, 1.2); y = M0.y + _pr.uniform(-1.6, 1.6)
    if on_body(x, y, 0.5): continue
    PILE.append(box('ptile%d' % k, (0.58, 0.58, 0.025), V3(x, y, 0.18), CEIL_M, rot=(R(_pr.uniform(-35, 35)), R(_pr.uniform(-35, 35)), R(_pr.uniform(0, 90)))))
# THE BEAM: a heavy timber across his thighs, resting on the mound's top edge, the far end down on the floor
BEAM_Y = MOUND_Y1 - 0.12
_xB = M0.x + 1.75; _xL = M0.x - 0.6
_hs = [(x_, max(mound_h(x_, y_) for y_ in np.linspace(BEAM_Y - 0.11, BEAM_Y + 0.11, 12))) for x_ in np.linspace(_xL, _xB, 120)]
_slope = max(h_ / max(_xB - x_, 1e-3) for x_, h_ in _hs) + 0.004           # the beam's underside just touches the highest point of the pile
_zL = _slope * (_xB - _xL); _len = math.hypot(_xB - _xL, _zL); _ang = math.atan2(_zL, _xB - _xL)
BEAM = box('beam', (_len, 0.2, 0.24), V3(0, 0, 0), OLDWOOD_M, 0.01)
_mid = V3((_xL + _xB) / 2, BEAM_Y, _zL / 2); _nrm = V3(math.sin(_ang), 0, math.cos(_ang))
BEAM.rotation_euler = (0, _ang, 0); BEAM.location = _mid + _nrm * 0.12
BEAM0 = BEAM.matrix_world.copy()
STRAP_M = noisy(mat('rebar', (0.3, 0.16, 0.08), 0.7, metal=0.6), 50.0, 0.4)
REBAR = tube('rebar', [V3(M0.x - 0.95, M0.y + 0.6, 0.0), V3(M0.x - 0.85, M0.y + 0.55, 0.9), V3(M0.x - 0.7, M0.y + 0.45, 1.3), V3(M0.x - 0.5, M0.y + 0.4, 1.45)], 0.012, STRAP_M, seg=8)
PINNED_SET = [MOUND, BEAM] + PILE
# ================================================================ X-RAY: see-through skin; the crushed legs ('crush' 0..1) glow a sick red-purple,
# yellow specks (potassium) build up in them, and when the weight comes off they run up the leg veins to the heart
def xray_skin_mat():
    m = bpy.data.materials.new('xskin'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    leg = nt.nodes.new('ShaderNodeMapRange'); leg.inputs['From Min'].default_value = 0.72; leg.inputs['From Max'].default_value = 0.6
    nt.links.new(sx.outputs['Z'], leg.inputs['Value'])                                    # 1 below mid-thigh, 0 above
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 28.0; nz.inputs['Detail'].default_value = 3
    nt.links.new(rp.outputs['Vector'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 1.5), nz.inputs['W'])
    hot = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', leg.outputs['Result'], objattr(nt, 'crush')), math_(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 1.2, 0.3))
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.0)
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.inputs['A'].default_value = (0.35, 0.62, 1.0, 1); base.inputs['B'].default_value = (0.85, 0.08, 0.35, 1)
    nt.links.new(math_(nt, 'MINIMUM', hot, 1.0), base.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(base.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 1.0, 0.02), math_(nt, 'MULTIPLY', hot, 0.9)), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 0.5, 0.04), math_(nt, 'MULTIPLY', hot, 0.3)), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
XSKIN = xray_skin_mat()
BODY['crush'] = 0.0; BODY['tt'] = 0.0
BODY_MATS = [sl.material for sl in BODY.material_slots]
def ghost_mat(name, col=(0.7, 0.8, 1.0), k=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 1.5), k), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 1.5), 0.6), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
GHOST_M = ghost_mat('ghost', (0.75, 0.85, 1.0), 0.8)
# vessels: the leg veins and the big vein up to the heart (his rest space, carried by the bones of the pinned pose)
def bone_for(c):
    side = 'L' if c.x > 0 else 'R'
    if c.z > 1.15: return 'spine01'
    if c.z > 0.95: return 'spine03'
    if c.z > 0.86: return 'root' if abs(c.x) < 0.06 else 'upperleg01.' + side
    if c.z > 0.5: return 'upperleg02.' + side
    if c.z > 0.12: return 'lowerleg02.' + side
    return 'foot.' + side
def smooth_pts(ctrl, n=40):
    out_ = []
    for i in range(n):
        u = i / (n - 1) * (len(ctrl) - 1); k = min(int(u), len(ctrl) - 2); f = u - k
        p0 = Vector(ctrl[max(k - 1, 0)]); p1 = Vector(ctrl[k]); p2 = Vector(ctrl[k + 1]); p3 = Vector(ctrl[min(k + 2, len(ctrl) - 1)])
        out_.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return out_
def flow_mat(name, col, dash=40.0):
    """a vessel: a dim tube with bright pulses running along it ('ph' moves them, 'glow' = brightness); UV x = metres along it"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    uv = nt.nodes.new('ShaderNodeUVMap'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv.outputs['UV'], sx.inputs['Vector'])
    sn = math_(nt, 'SINE', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', sx.outputs['X'], dash), objattr(nt, 'ph')))
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.2; mr.inputs['From Max'].default_value = 1.0; mr.inputs['To Min'].default_value = 0.35; mr.inputs['To Max'].default_value = 3.0
    nt.links.new(sn, mr.inputs['Value'])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', mr.outputs['Result'], objattr(nt, 'glow')), em.inputs['Strength'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
VEIN_M = flow_mat('vein', (0.25, 0.35, 1.0), 30.0)
def vtube(name, pts, r, m):
    o = tube(name, pts, r, m, None, seg=10)
    me = o.data; uvl = me.uv_layers.new(name='UVMap'); seg = 10; arc = [0.0]
    for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; ring = min(vi // seg, len(pts) - 1); uvl.data[li].uv = (arc[ring], (vi % seg) / seg)
    o['ph'] = 0.0; o['glow'] = 1.0; o.visible_shadow = False; return o, arc
pinned(0.0)
def wpath(rest_pts): return [deform(p_, bone_for(Vector(p_))) for p_ in rest_pts]
VEINS = {}
for s_, sg in (('L', 1), ('R', -1)):
    rp_ = smooth_pts([(sg * 0.2, 0.01, 0.1), (sg * 0.185, 0.02, 0.3), (sg * 0.17, 0.02, 0.47), (sg * 0.15, -0.01, 0.62), (sg * 0.12, -0.01, 0.82), (sg * 0.07, 0.02, 0.9), (0.012, 0.03, 0.94)], 46)
    VEINS[s_] = vtube('legvein' + s_, wpath(rp_), 0.0085, VEIN_M)
_cava_rest = smooth_pts([(0.012, 0.03, 0.94), (0.025, 0.025, 1.1), (0.03, -0.01, 1.22), (0.03, -0.04, 1.26)], 30)
CAVA = vtube('vena_cava', wpath(_cava_rest), 0.012, VEIN_M)
def organ_mat(name, c0, c1, prop):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*c1, 1); mx.inputs['B'].default_value = (*c0, 1); nt.links.new(objattr(nt, prop), mx.inputs['Factor'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    st = nt.nodes.new('ShaderNodeMapRange'); st.inputs['To Min'].default_value = 3.0; st.inputs['To Max'].default_value = 0.9; nt.links.new(lw.outputs['Facing'], st.inputs['Value'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mx.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'MULTIPLY', st.outputs['Result'], math_(nt, 'MULTIPLY_ADD', objattr(nt, 'flash'), 0.35, 1.0)), em.inputs['Strength'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
HEART_M = organ_mat('heart', (1.0, 0.18, 0.05), (0.85, 0.05, 0.05), 'kk')
HEART_C = deform(V3(0.025, -0.06, 1.25), 'spine01')
HEART = prim('uv_sphere', 'heart', HEART_M, None, loc=(0, 0, 0), segments=48, ring_count=24, radius=1.0)
for v in HEART.data.vertices:                                     # bend a ball into a heart: two lobes on top, a point at the bottom
    x, y, z = v.co; zz = z
    w = 1.0 - 0.55 * max(0.0, -zz) ** 1.3; dip = 0.28 * math.exp(-(x / 0.28) ** 2) * max(0.0, zz) ** 2
    v.co = Vector((x * 0.055 * w * (1 + 0.15 * max(0.0, zz)), y * 0.04 * w, (z - dip) * 0.06 - 0.012 * max(0.0, -zz) ** 2))
tx_ = bpy.data.textures.new('heart_n', 'CLOUDS'); tx_.noise_scale = 0.03; d_ = HEART.modifiers.new('bump', 'DISPLACE'); d_.texture = tx_; d_.strength = 0.006; d_.texture_coords = 'LOCAL'
HEART.location = HEART_C; HEART.rotation_euler = (R(20) - R(88), R(-25), R(15)); HEART['kk'] = 0.0; HEART['flash'] = 0.0; HEART.visible_shadow = False
# potassium specks: one mesh of tiny bright balls, moved every frame
NK = 260; _kr = np.random.default_rng(9)
_legv = np.where((_RP[:, 2] > 0.08) & (_RP[:, 2] < 0.6))[0]
def leg_spots():
    W_, RP_ = body_eval(); idx = _kr.choice(_legv, NK, replace=False)
    out = []
    for i in idx:
        s_ = 'L' if RP_[i, 0] > 0 else 'R'; bn = 'lowerleg02.' + s_ if RP_[i, 2] < 0.45 else 'upperleg02.' + s_
        a_ = np.array(wpos(bn)); b_ = np.array(wpos(bn, True)); p_ = W_[i]; ab = b_ - a_; k = np.clip(np.dot(p_ - a_, ab) / np.dot(ab, ab), 0, 1); c_ = a_ + ab * k
        out.append((c_ + (p_ - c_) * _kr.uniform(0.25, 0.7), s_, float(RP_[i, 2])))
    return out
KSPOTS = leg_spots()
K_P0 = np.array([k_[0] for k_ in KSPOTS]); K_SIDE = [k_[1] for k_ in KSPOTS]; K_Z = np.array([k_[2] for k_ in KSPOTS])
K_ORDER = _kr.permutation(NK) / NK                                  # when each speck shows up (0..1 of the build-up)
_ico = bpy.data.meshes.new('kico'); _bm = bmesh.new(); bmesh.ops.create_icosphere(_bm, subdivisions=1, radius=1.0); _bm.to_mesh(_ico); _bm.free()
ICO_V = np.array([v.co[:] for v in _ico.vertices]); ICO_F = [tuple(p_.vertices) for p_ in _ico.polygons]; NI = len(ICO_V)
K_M = emis('potassium', (1.0, 0.85, 0.15), 14.0)
KMESH = mesh('potassium', [tuple(v) for v in np.tile(ICO_V * 0.005, (NK, 1))], [tuple(i + k * NI for i in f) for k in range(NK) for f in ICO_F], K_M, smooth_=True)
KMESH.visible_shadow = False
_VPTS = {s_: [deform(p_, bone_for(Vector(p_))) for p_ in smooth_pts([(sg * 0.2, 0.01, 0.1), (sg * 0.185, 0.02, 0.3), (sg * 0.17, 0.02, 0.47), (sg * 0.15, -0.01, 0.62), (sg * 0.12, -0.01, 0.82), (sg * 0.07, 0.02, 0.9), (0.012, 0.03, 0.94)], 46)]
         + wpath(_cava_rest)[1:] + [HEART_C] for s_, sg in (('L', 1), ('R', -1))}
_VARC = {}
for s_, P_ in _VPTS.items():
    a_ = [0.0]
    for i in range(1, len(P_)): a_.append(a_[-1] + (P_[i] - P_[i - 1]).length)
    _VARC[s_] = np.array(a_)
def along(side, d):
    P_, A_ = _VPTS[side], _VARC[side]; d = clamp(d, 0, A_[-1]); i = int(np.searchsorted(A_, d)); i = clamp(i, 1, len(P_) - 1)
    f = (d - A_[i - 1]) / max(A_[i] - A_[i - 1], 1e-6); return np.array(P_[i - 1].lerp(P_[i], f))
def k_entry(i):
    """where speck i joins its leg vein: the vein point at the speck's own height in the leg (arc from the foot)"""
    return clamp((K_Z[i] - 0.1) / 0.84, 0.0, 1.0) * float(_VARC[K_SIDE[i]][45])
K_ENTRY = np.array([k_entry(i) for i in range(NK)])
def specks(t, amt, run=-1.0, size=0.006):
    """amt 0..1: how many specks have built up; run >= 0: seconds since the weight came off (they race to the heart)"""
    P = np.zeros((NK, 3)); sc = np.zeros(NK)
    for i in range(NK):
        on = amt > K_ORDER[i]; sc[i] = size * (0.7 + 0.6 * ((i * 37) % 10) / 10) if on else 0.0
        j = np.array([wob(t, 1.3, i * 0.37), wob(t, 1.3, i * 0.37 + 9), wob(t, 1.3, i * 0.37 + 17)]) * 0.006
        if run < 0: P[i] = K_P0[i] + j; continue
        d0 = run - 0.25 * K_ORDER[i]                              # they leave in a rush, a few at a time
        if d0 <= 0: P[i] = K_P0[i] + j; continue
        u0 = min(d0 / 0.25, 1.0); ve = along(K_SIDE[i], K_ENTRY[i])
        if u0 < 1.0: P[i] = K_P0[i] + (ve - K_P0[i]) * sm(u0) + j; continue
        d = K_ENTRY[i] + (d0 - 0.25) * 1.9; A_end = float(_VARC[K_SIDE[i]][-1])
        if d >= A_end: P[i] = np.array(HEART_C) + np.array([wob(t, 2, i), wob(t, 2, i + 5), wob(t, 2, i + 11)]) * 0.04; sc[i] *= max(0.0, 1.0 - (d - A_end) * 3.0); continue
        P[i] = along(K_SIDE[i], d) + j * 0.5
    V_ = np.repeat(P, NI, 0) + np.tile(ICO_V, (NK, 1)) * np.repeat(sc, NI)[:, None]
    KMESH.data.vertices.foreach_set('co', V_.ravel().astype(np.float32)); KMESH.data.update()
XRAY = [HEART, KMESH, CAVA[0]] + [v[0] for v in VEINS.values()]
for o in XRAY: o.hide_render = True
BEAM_MATS = [BEAM.material_slots[0].material]
def xray(on):
    for o in XRAY: o.hide_render = not on
    for o in (SUIT, HAIR) + tuple(HEADBITS): o.hide_render = on
    for i_, sl in enumerate(BODY.material_slots): sl.material = XSKIN if on else BODY_MATS[i_]
    BEAM.material_slots[0].material = GHOST_M if on else BEAM_MATS[0]
# IV: a bag hung on the bent rebar, a line down to the inside of his right forearm, taped; fluid runs down it ('ph')
def iv_build():
    pinned(0.0)
    a_ = Vector(wpos('lowerarm02.R')); b_ = Vector(wpos('wrist.R')); mid = a_.lerp(b_, 0.55)
    W_, RP_ = body_eval(); d = np.linalg.norm(W_ - np.array(mid), axis=1); near = W_[d < 0.05]; top = near[np.argmax(near[:, 2])]
    entry = Vector(top) + V3(0, 0, 0.004)
    bag_c = V3(M0.x - 0.48, M0.y + 0.4, 1.28)
    BAG_M = mat('ivbag', (0.85, 0.9, 0.95), 0.08, trans=0.9, ior=1.4)
    bag = box('iv_bag', (0.13, 0.04, 0.22), bag_c, BAG_M, 0.02, ss=2)
    FLUID_M = emis('iv_fluid', (0.75, 0.9, 1.0), 1.2)
    fluid = box('iv_fluid', (0.11, 0.025, 0.16), bag_c - V3(0, 0, 0.02), FLUID_M, 0.015)
    hook = tube('iv_hook', [bag_c + V3(0, 0, 0.11), bag_c + V3(0, 0, 0.17), V3(M0.x - 0.5, M0.y + 0.4, 1.45)], 0.003, STEEL_M, seg=6)
    chamber = box('iv_chamber', (0.022, 0.022, 0.06), bag_c - V3(0, 0, 0.16), BAG_M, 0.008, ss=1)
    p0 = bag_c - V3(0, 0, 0.19); p3 = entry; c1 = p0 + V3(0.02, -0.05, -0.45); c2 = entry + V3(0.0, 0.0, 0.18)
    pts = [p0 * (1 - u) ** 3 + c1 * 3 * u * (1 - u) ** 2 + c2 * 3 * u * u * (1 - u) + p3 * u ** 3 for u in np.linspace(0, 1, 50)]
    line_m = flow_mat('iv_flow', (0.7, 0.9, 1.0), 25.0)
    line, arc = vtube('iv_line', pts, 0.0028, line_m); line.visible_shadow = True
    tape = box('iv_tape', (0.045, 0.035, 0.003), entry + V3(0, 0, 0.002), mat('tape', (0.9, 0.9, 0.86), 0.7), 0.003)
    DROP = prim('uv_sphere', 'iv_drop', mat('drop', (0.8, 0.9, 1.0), 0.05, trans=1.0, ior=1.33), loc=bag_c - V3(0, 0, 0.14), segments=12, ring_count=8, radius=0.004)
    return [bag, fluid, hook, chamber, line, tape, DROP], line, DROP, bag_c
IV, IV_LINE, IV_DROP, IV_BAG = iv_build()
for o in IV: o.hide_render = True
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
HEAD_W = deform(V3(0, -0.02, 1.62), 'head')
# bricks round his head and shoulder that the rescuers pull away (B2): stacked on the floor pile, never on him
DIG = []; _dg = random.Random(33)
for k in range(9):
    for _ in range(40):
        x = HEAD_W.x + _dg.uniform(-0.55, 0.55); y = HEAD_W.y + _dg.uniform(-0.2, 0.55)
        if not on_body(x, y, 0.13): break
    o = box('dig%d' % k, (0.2, 0.095, 0.06), V3(x, y, 0.03 + 0.065 * (k % 3)), LOOSE_BRICK_M, 0.006, rot=(0, 0, R(_dg.uniform(0, 180)))); o['p0'] = o.location.copy(); o['s'] = 0.15 + 0.22 * k; DIG.append(o)
INBEAMS = []
for i in range(3):
    o = prim('cone', 'inbeam%d' % i, BEAMS_M, radius1=0.9, radius2=0.03, depth=7.0, vertices=24); o.visible_shadow = False; o['on'] = 0.0; o.rotation_mode = 'QUATERNION'; o.hide_render = True
    INBEAMS.append(o)
STORESET = list(dict.fromkeys(STORE + CEIL_TILES + FALLERS + [GRIT] + PINNED_SET + [REBAR] + IV + DIG))
EMIS_STR = {m_: m_.node_tree.nodes['Emission'].inputs['Strength'] for m_ in (TUBE_GLOW, FRIDGE_GLOW, STORE[7].data.materials[0], BAR_R, BAR_W, DRONE_RED, DRONE_GRN)}
def glow(m_, v): EMIS_STR[m_].default_value = v
STREET_GLASS = STORE[7].data.materials[0]
def show(objs, on):
    for o in objs: o.hide_render = not on
def mode(which):
    """store | fall | pinned | xray | dusk | night"""
    inside = which in ('store', 'fall', 'pinned', 'xray')
    show(OUTSET, not inside); show(STORESET, inside and which != 'xray'); show(MAN, which != 'dusk' and which != 'night'); show(DUST, False)
    show(XRAY, False); show(IV, False); show(INBEAMS, False)
    if inside:
        before = which in ('store', 'fall')
        show(FALLERS + [GRIT], before); show(CEIL_TILES, True); show(PINNED_SET + DIG, which == 'pinned'); REBAR.hide_render = which != 'pinned'
        for o in DROP_TILES: o.hide_render = not before
        glow(TUBE_GLOW, 4.5 if before else 0.0); glow(FRIDGE_GLOW, 4.0 if before else 0.25); glow(STREET_GLASS, 1.4 if before else 0.35)
        for o in STORE_L: o.data.energy = (90 if o.name == 'store_fill' else 40) if before else (18 if o.name == 'store_fill' else 6)
        GAP_L.data.energy = 0.0 if before else 260.0
        for o in TORCH_L: o.data.energy = 0.0
        WBG.inputs['Color'].default_value = (0, 0, 0, 1); SUN_O.hide_render = True
    xray(which == 'xray')
    if which in ('pinned', 'xray'):
        fall(6.0); BEAM.matrix_world = BEAM0; BEAM.hide_render = False; ABOVE.hide_render = True
        for o in DIG: o.location = Vector(o['p0']); o.rotation_euler.x = 0.0
    if which == 'xray':
        show(XRAY, True); BEAM.hide_render = False; WBG.inputs['Color'].default_value = (0.0, 0.0, 0.004, 1)
    if which == 'dusk':
        WBG.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1); SKYBG.inputs['Strength'].default_value = 0.35; SUN_O.hide_render = False
        for o in STREETL: o.data.energy = 0.0
        show(OUT_GEAR, False); c_intact()
    elif which == 'night':
        WBG.inputs['Color'].default_value = (0.012, 0.016, 0.03, 1); WBG.inputs['Strength'].default_value = 1.0; SUN_O.hide_render = True
        for o in STREETL: o.data.energy = 900.0
        show(OUT_GEAR, True); c_rest()
        for o in TOWER_L: o.data.energy = 3500.0
    else: WBG.inputs['Strength'].default_value = 1.0
    if which != 'dusk': SKYBG.inputs['Strength'].default_value = 0.0
def night_fx(t):
    """flashing truck lights, blinking drone, flashlight beams sweeping the pile"""
    fl = 1.0 if (t * 2.6) % 1.0 < 0.5 else 0.0
    glow(BAR_R, 40 * fl); glow(BAR_W, 40 * (1 - fl)); TRUCK_L[0].data.energy = 1500 * fl; TRUCK_L[1].data.energy = 1200 * (1 - fl)
    bl = 1.0 if (t * 1.3) % 1.0 < 0.15 else 0.0; glow(DRONE_RED, 30 * bl); glow(DRONE_GRN, 30 * bl)
    srcs = [V3(8.0, 1.0, 0.8), V3(11.0, 0.2, 0.9), V3(16.5, 1.2, 0.6), V3(7.6, 9.0, -1.5), V3(14.0, 13.5, -1.0)]
    for i, o in enumerate(TBEAMS):
        a_ = t * (0.5 + 0.13 * i) + i * 1.7
        dst = V3(11.0 + 3.5 * math.sin(a_), 7.0 + 4.0 * math.cos(a_ * 0.8), -2.5 + 0.8 * math.sin(a_ * 1.3))
        torch(o, X0 + srcs[i], X0 + dst, 0.9)
def drone_at(p, t):
    DRONE[0].location = p + V3(0.05 * wob(t, 0.7, 1), 0.05 * wob(t, 0.7, 2), 0.06 * wob(t, 0.9, 3)); DRONE[0].rotation_euler = (R(3 * wob(t, 1, 4)), R(3 * wob(t, 1, 5)), R(20))
    DRONE_SPOT.data.energy = 120.0
    for o in DRONE:
        if o.name.startswith('drone_rot'): o.rotation_euler = (0, 0, t * 120.0)
def store_lights_flicker(t, k):
    """the power failing as the ceiling comes down (k 0..1)"""
    fl = 1.0 - k * (0.5 + 0.5 * (1 if math.sin(t * 47.0) * math.sin(t * 13.0) > 0.1 else 0))
    glow(TUBE_GLOW, 4.5 * max(fl, 0.05))
def cam_b0(u):
    return M0 + V3(0.55, -2.25, 0.55).lerp(V3(0.45, -1.9, 0.5), u), M0 + V3(0.0, 0.0, 2.05).lerp(V3(0.0, 0.1, 2.25), u), 17.0
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    S.view_settings.exposure = 0.0
    for o in DUST: o['dens'] = 0.0
    if nb in (0, 12):                                       # the store: before and as the ceiling comes down (B12 runs into B0)
        cc = t if nb == 0 else t - TOTAL
        mode('fall' if cc > -1.2 else 'store'); fall(cc); grit(cc, 1.0)
        if cc > -1.2: store_lights_flicker(t, smooth(-1.2, 0.8, cc))
        look_up = 1.0 if nb == 0 else smooth(-1.4, -0.5, cc); brace = smooth(0.15, 1.1, cc) if nb == 0 else 0.0
        yaw = 0.0 if nb == 0 else lerp(70, 0, smooth(-2.4, -1.5, cc))
        stand(t, look_up, brace, yaw)
        show(DUST, True); dust(t, 0.35 * smooth(-0.8, 1.2, cc), M0 + V3(0, 0.6, 1.4), CAM.location, 1.0)
        if nb == 0:
            cp, ct, ln = cam_b0(u); look(cp + shake(t, 0.035 * smooth(-0.5, 0.5, cc)), ct, ln, 5.6, focus=M0 + V3(0, 0, 1.6))
        else:
            k = smooth(0.0, 1.0, u); cp0, ct0, ln0 = cam_b0(0.0)
            cp = (M0 + V3(1.4, -3.4, 1.55)).lerp(cp0, sm(k)); ct = (M0 + V3(-0.4, 0.4, 1.2)).lerp(ct0, sm(smooth(0.35, 1.0, u)))
            look(cp + shake(t, 0.02 * smooth(-1.0, 0.0, cc)), ct, lerp(28, ln0, sm(k)), 5.6, focus=M0 + V3(0, 0, 1.5))
    elif nb in (1, 2, 4, 9):                                # pinned in the dark
        mode('pinned'); pinned(t, wince=0.6 if nb != 9 else 0.4, look=0.35 if nb == 1 else 0.1)
        hd = deform(V3(0, -0.02, 1.62), 'head'); legs = V3(M0.x, M0.y - 0.6, 0.25)
        show(DUST, True); dust(t, 0.25, M0 + V3(0, -0.2, 1.0), CAM.location, 0.8, rise=0.02)
        if nb == 1:                                         # high and to the side: him, the beam, the pile on his legs
            cp = M0 + V3(0.95, -1.75, 2.15).lerp(V3(0.85, -1.5, 1.95), u); look(cp + shake(t, 0.01), M0 + V3(-0.05, 0.05, 0.12), 19, 8.0, focus=M0 + V3(0, -0.2, 0.2))
            GAP_L.data.energy = 260 * (0.8 + 0.2 * wob(t, 2, 1))
        elif nb == 2:                                       # light breaks in from above; bricks round his head are pulled away
            for o in DIG:
                k = smooth(o['s'], o['s'] + 0.5, u * 2.4); o.location = Vector(o['p0']) + V3(0.1 * k, 0.15 * k, 2.2 * k * k); o.rotation_euler.x = 1.5 * k
            GAP_L.data.energy = 400 + 2600 * smooth(0.0, 0.9, u); S.view_settings.exposure = 0.5
            for i, o in enumerate(TORCH_L):
                a_ = t * 1.3 + i * 2.1; o.location = M0 + V3(0.5 * math.sin(a_), 0.6 + 0.4 * math.cos(a_), 3.6)
                tg = hd + V3(0.3 * math.sin(a_ * 1.7), 0.3 * math.cos(a_), 0); on = smooth(0.1 + 0.15 * i, 0.4 + 0.15 * i, u)
                o.rotation_quaternion = (tg - o.location).to_track_quat('-Z', 'Y'); o.data.energy = 260 * on
                INBEAMS[i].hide_render = False; torch(INBEAMS[i], o.location, tg, 1.4 * on)
            look(hd + V3(0.62, 0.32, 0.12), hd + V3(-0.35, -0.25, 0.85), 16, 4.0, focus=hd)
        elif nb == 4:                                       # the warning: slow push from his face down to the beam on his legs
            k = sm(u); cp = (hd + V3(0.75, -0.2, 0.55)).lerp(V3(M0.x + 0.75, M0.y - 0.55, 0.75), k)
            look(cp, hd.lerp(V3(M0.x, BEAM_Y, 0.35), smooth(0.1, 0.8, u)), 24, 5.0, focus=hd.lerp(V3(M0.x, BEAM_Y, 0.3), k))
            GAP_L.data.energy = 200; S.view_settings.exposure = -0.3 * smooth(0.4, 1.0, u)
        else:                                               # the IV goes in before the lift; drops fall in the chamber, fluid runs down
            show(IV, True); IV_LINE['ph'] = t * 6.0; IV_LINE['glow'] = 0.9
            dk = (t * 2.2) % 1.0; IV_DROP.location = IV_BAG - V3(0, 0, 0.135 + 0.04 * dk * dk)
            for i, o in enumerate(TORCH_L[:1]): o.location = IV_BAG + V3(0.6, -0.6, 1.2); o.rotation_quaternion = (IV_BAG - o.location).to_track_quat('-Z', 'Y'); o.data.energy = 120
            GAP_L.data.energy = 600
            arm = Vector(wpos('lowerarm02.R')); look(arm + V3(0.95, -1.15, 0.75).lerp(V3(0.85, -1.0, 0.85), u), arm.lerp(IV_BAG, 0.5), 22, 5.6, focus=arm.lerp(IV_BAG, 0.3))
            if u > 0.8: BEAM.matrix_world = Matrix.Translation(V3(0, 0, 0.06 * smooth(0.8, 1.0, u))) @ BEAM0
            else: BEAM.matrix_world = BEAM0
    elif nb in (5, 6, 7, 8):                                # x-ray: crush syndrome
        mode('xray'); pinned(t, wince=0.5); BODY['tt'] = t
        for v_ in VEINS.values(): v_[0]['ph'] = t * 4.0; v_[0]['glow'] = 0.6
        CAVA[0]['ph'] = t * 4.0; CAVA[0]['glow'] = 0.6; HEART['kk'] = 0.0; HEART['flash'] = 0.0
        bt = (t * 1.2) % 1.0; hb = 0.06 * math.exp(-((bt - 0.1) / 0.06) ** 2)
        legc = V3(M0.x, M0.y - 0.45, 0.2)
        if nb == 5:
            BODY['crush'] = 0.25 + 0.75 * smooth(0.0, 0.9, u); specks(t, 0.45 * smooth(0.2, 1.0, u), size=0.011); BEAM.matrix_world = BEAM0
            look(legc + V3(1.15, -1.25, 0.95).lerp(V3(0.95, -1.05, 0.8), u), legc + V3(0, 0.1, 0.05), 22, 8.0, focus=legc)
        elif nb == 6:
            BODY['crush'] = 1.0; specks(t, 0.45 + 0.55 * smooth(0.0, 0.85, u), size=0.012); BEAM.matrix_world = BEAM0
            th = V3(M0.x, M0.y - 0.45, 0.14); look(th + V3(0.45, -0.75, 0.38).lerp(V3(0.38, -0.62, 0.32), u), th + V3(0, 0.1, 0), 26, 4.0, focus=th)
        elif nb == 7:                                       # the weight comes off: the beam lifts away, the specks race up to the heart
            BODY['crush'] = 1.0 - 0.5 * smooth(0.2, 1.0, u)
            lift = smooth(0.0, 0.35, u); BEAM.matrix_world = Matrix.Translation(V3(0.25 * lift, 0, 0.9 * lift)) @ BEAM0
            run = lt - 0.25; specks(t, 1.0, run if run > 0 else -1.0, 0.012)
            for v_ in list(VEINS.values()) + [CAVA]: v_[0]['glow'] = 0.6 + 1.6 * smooth(0.15, 0.4, u); v_[0]['ph'] = t * 14.0
            mid = V3(M0.x, M0.y + 0.1, 0.18); look(mid + V3(0.6, -1.0, 1.25).lerp(V3(0.65, -0.1, 1.3), sm(u)), mid + V3(0, 0.35 * u, 0), 24, 11.0, focus=mid)
            HEART['kk'] = smooth(0.6, 1.0, u)
        else:                                               # the heart can't keep a beat: it flutters and stutters
            BEAM.hide_render = True; specks(t, 1.0, 3.0 + lt, 0.012)
            seq = [0.0, 0.18, 0.31, 0.62, 0.7, 0.78, 1.05, 1.5, 1.58, 2.2, 2.32, 2.4, 2.9, 3.05]
            hb = sum(0.09 * math.exp(-((lt - s_) / 0.045) ** 2) for s_ in seq) if lt < 2.6 else 0.02 * math.sin(lt * 40) * (1 - smooth(2.6, 3.4, lt))
            HEART['kk'] = 1.0; HEART['flash'] = 3.0 * hb / 0.09
            look(HEART_C + V3(0.42, -0.32, 0.3).lerp(V3(0.3, -0.22, 0.22), u) + shake(t, 0.004), HEART_C, 30, 4.0, focus=HEART_C)
            S.view_settings.exposure = 0.0
        HEART.scale = Vector((1.0, 1.0, 1.0)) * (1.0 + 2.2 * hb)
    elif nb == 10:                                          # outside, late afternoon: C leans and falls into the dug-out lot next door
        mode('dusk'); c_collapse(smooth(0.05, 1.0, u))
        show(DUST, True); dust(t, 0.7 * smooth(0.35, 0.8, u), X0 + V3(11.0, 6.0, 2.0 + 3 * u), CAM.location, 4.0, rise=0.3)
        look(X0 + V3(4.0, -14.0, 1.6).lerp(V3(5.0, -13.2, 1.8), u) + shake(t, 0.06 * smooth(0.25, 0.6, u)), X0 + V3(6.0, 5.0, 4.6), 15, 16.0)
    elif nb == 11:                                          # night: lights on the pile, the open rooms next door, a drone over the pit
        mode('night'); night_fx(t); drone_at(X0 + V3(9.5, 3.0, float(HM.max()) + 4.0), t)
        cp = X0 + V3(13.0, -11.0, 9.5).lerp(V3(11.5, -10.5, 9.0), u)
        look(cp, X0 + V3(3.0, 6.0, 2.5), 18, 16.0)
    elif nb == 3:                                           # outside at night: the drone hangs in front of us, beams sweep the pile
        mode('night'); night_fx(t); dp = X0 + V3(10.0, 1.5, 7.5); drone_at(dp, t)
        look(X0 + V3(9.0, -3.5, 12.5).lerp(V3(9.3, -3.0, 12.0), u), X0 + V3(12.0, 7.0, -2.5), 20, 16.0)
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

