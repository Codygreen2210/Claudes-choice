# Frozen turkey in a deep fryer: one continuous shot on a backyard deck at dusk. The ice inside melts, the water sinks, flashes to steam,
# shoves the oil over the rim onto the burner, and a fireball climbs the porch roof; then the right way, out on the lawn. Loops.
#   python3 fryer3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join(HERE, 'assets', n), os.path.join('/root/vt/n45/boat', n), os.path.join('/root/vt/n38/g9', n), os.path.join('/root/vt/assets', n)) if os.path.exists(p_))
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
C.max_bounces = 6; C.diffuse_bounces = 2; C.glossy_bounces = 2; C.transmission_bounces = 5; C.volume_bounces = 0; C.transparent_max_bounces = 14
C.volume_step_rate = 2.5; C.volume_max_steps = 160
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
    elif kind == 'cylinder':
        r_ = kw.get('radius', 1.0); bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=kw.get('vertices', 32), radius1=r_, radius2=r_, depth=kw.get('depth', 2.0))
    elif kind == 'cone':
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=kw.get('vertices', 32), radius1=kw.get('radius1', 1.0), radius2=kw.get('radius2', 0.0), depth=kw.get('depth', 2.0))
    elif kind == 'circle':
        bmesh.ops.create_circle(bm, cap_ends=kw.get('fill_type', 'NOTHING') != 'NOTHING', segments=kw.get('vertices', 32), radius=kw.get('radius', 1.0))
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
# ================================================================ timing + the set: a backyard deck at dusk under a porch roof (the wrong place to fry),
# the house wall with a lit window, a lawn out to the fence; a second fryer far out on the grass (the right way)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_TOUCH = word_t(0, 10)          # skin meets the oil ("going into oil")
T_FLASH = word_t(1, 5)                # "flashes into steam"
T_XR0 = B[2] + 0.3                    # x-ray on (into the meat)
T_MELT = word_t(3, 8)                 # "as that ice melts"
T_DRIP = word_t(3, 10)                # "drips out"
T_SINK = word_t(4, 7)                 # "sinks straight to the bottom"
T_BOT = word_t(5, 4)                  # "right over the flame"
T_212 = word_t(5, 15)                 # "two hundred twelve": the drops start to boil
T_POP = word_t(6, 5) - 0.1            # "turns to steam": one drop blows into a bubble
T_1700 = word_t(6, 9)                 # "seventeen hundred times"
T_SURGE = word_t(7, 3)                # "blasts up through the oil"
T_XR1 = B[7] + 0.8                    # x-ray off: the pot goes solid again
T_OVER = word_t(7, 11)                # "over the edge"
T_POUR = B[8] + 0.2                   # oil pours down the side
T_HIT = word_t(8, 10)                 # "onto the burner"
T_CATCH = word_t(9, 3)                # "catches fire"
T_RACE = word_t(9, 7)                 # flames race up the oil
T_BALL = word_t(10, 4)                # "a fireball swallows the pot"
T_ROOF = word_t(10, 9)                # "climbs up the porch roof"
T_STATS = B[11]
T_SAFE = B[12] + 0.3                  # the camera turns out to the lawn fryer
T_RESET = B[13] + 0.6                 # (camera faces away from the deck) everything goes back to frame one
print('T', round(T_TOUCH, 2), round(T_POP, 2), round(T_OVER, 2), round(T_CATCH, 2), round(T_BALL, 2), round(T_RESET, 2), round(END, 2))

# ---------------------------------------------------------------- world: dusk sky
P.hdri('ph:qwantani_dusk_2', 0.6, 150)
DECK_Z = 0.45; WALL_Y = 3.2
# lawn: big ground with the leafy grass set, a wavy edge of grass clumps, a fence line
GRASS = P.material('ph:leafy_grass', scale=0.45, name='lawn')
lawn = prim('plane', 'lawn', GRASS, loc=(0, -8, 0), size=60.0)
try:
    b_ = GRASS.node_tree.nodes['Principled BSDF']; lk = next(l for l in GRASS.node_tree.links if l.to_socket == b_.inputs['Base Color'])
    mg = GRASS.node_tree.nodes.new('ShaderNodeMix'); mg.data_type = 'RGBA'; mg.blend_type = 'MULTIPLY'; mg.inputs['Factor'].default_value = 1.0
    GRASS.node_tree.links.new(lk.from_socket, mg.inputs['A']); mg.inputs['B'].default_value = (0.42, 0.75, 0.30, 1)
    hs = GRASS.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 1.35; GRASS.node_tree.links.new(mg.outputs['Result'], hs.inputs['Color'])
    GRASS.node_tree.links.new(hs.outputs['Color'], b_.inputs['Base Color'])
except Exception as e_: print('lawn tint skipped', e_)
fence_m = mat('fence', (0.42, 0.31, 0.20), 0.85); noisy(fence_m, 3.0, 0.25, 0.1)
for i in range(70):
    x_ = -17 + i * 0.5
    box(f'picket{i}', (0.09, 0.02, 1.5), (x_, -20.0, 0.75), fence_m)
for z_ in (0.35, 1.15): box(f'rail{z_}', (35, 0.04, 0.09), (0, -19.97, z_), fence_m)
for k in range(9):
    for s_ in (-1, 1):
        box(f'side{k}{s_}', (0.02, 2.0, 1.5), (s_ * 17, -20 + 2.0 * k + 1.0, 0.75), fence_m)
# trees behind the fence (dark masses against the dusk)
tree_m = mat('treeleaf', (0.03, 0.06, 0.03), 0.9); bark_m = mat('bark', (0.06, 0.045, 0.035), 0.9)
for k in range(9):
    x_ = -15 + k * 3.7 + 1.2 * h1(k); y_ = -22.5 - 2.0 * h1(k + 4)
    tube(f'trunk{k}', [(x_, y_, 0), (x_, y_, 2.5)], 0.18, bark_m, seg=8)
    for j in range(4):
        b_ = prim('ico_sphere', f'crown{k}_{j}', tree_m, loc=(x_ + (h1(k * 7 + j) - 0.5) * 2, y_ + (h1(k * 3 + j) - 0.5), 3.2 + 1.4 * h1(k + j)),
                  scale=(1.9 + h1(j), 1.7, 1.6 + h1(k)), subdivisions=3)
        dp = b_.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new(f'tc{k}{j}', 'CLOUDS'); tx.noise_scale = 0.6; dp.texture = tx; dp.strength = 0.6

# ---------------------------------------------------------------- the house: plank siding, a window with warm light, a back door
SIDING = P.material('ph:weathered_plank_siding', scale=1.2, name='siding')
try:
    b_ = SIDING.node_tree.nodes['Principled BSDF']; lk = next(l for l in SIDING.node_tree.links if l.to_socket == b_.inputs['Base Color'])
    hs = SIDING.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.35; hs.inputs['Value'].default_value = 1.35
    SIDING.node_tree.links.new(lk.from_socket, hs.inputs['Color']); SIDING.node_tree.links.new(hs.outputs['Color'], b_.inputs['Base Color'])
except Exception as e_: print('siding tint skipped', e_)
house = box('house_wall', (12.0, 0.25, 5.4), (0.0, WALL_Y + 0.125, 2.7), SIDING)
trim_m = mat('trim', (0.85, 0.84, 0.80), 0.45)
WIN_GLOW = emis('window_glow', (1.0, 0.72, 0.42), 3.5)
for wx in (-2.4, 2.6):
    box(f'win{wx}', (1.2, 0.05, 1.3), (wx, WALL_Y - 0.01, 1.95), WIN_GLOW)
    for dz in (-0.68, 0.68): box(f'winsill{wx}{dz}', (1.42, 0.12, 0.08), (wx, WALL_Y - 0.04, 1.95 + dz), trim_m)
    for dx in (-0.66, 0.66): box(f'winjamb{wx}{dx}', (0.08, 0.1, 1.42), (wx + dx, WALL_Y - 0.03, 1.95), trim_m)
    box(f'winmull{wx}', (0.04, 0.06, 1.3), (wx, WALL_Y - 0.03, 1.95), trim_m); box(f'winbar{wx}', (1.2, 0.06, 0.04), (wx, WALL_Y - 0.03, 1.95), trim_m)
door_m = mat('door', (0.35, 0.10, 0.08), 0.5, coat=0.4)
box('door', (0.95, 0.06, 2.1), (0.3, WALL_Y - 0.02, DECK_Z + 1.05), door_m, bv=0.01)
box('door_glass', (0.55, 0.07, 0.6), (0.3, WALL_Y - 0.025, DECK_Z + 1.55), WIN_GLOW)
for dx in (-0.52, 0.52): box(f'doorjamb{dx}', (0.09, 0.1, 2.2), (0.3 + dx, WALL_Y - 0.03, DECK_Z + 1.1), trim_m)
box('doorhead', (1.14, 0.1, 0.1), (0.3, WALL_Y - 0.03, DECK_Z + 2.2), trim_m)
box('doorknob', (0.05, 0.08, 0.05), (0.66, WALL_Y - 0.08, DECK_Z + 1.0), mat('brass', (0.85, 0.62, 0.3), 0.25, 1.0))
lamp = box('porch_lamp', (0.14, 0.12, 0.22), (1.05, WALL_Y - 0.08, DECK_Z + 1.9), emis('lamp_glow', (1.0, 0.75, 0.45), 6.0), bv=0.01)
light_at('porch_lamp_l', 'POINT', (1.05, WALL_Y - 0.3, DECK_Z + 1.85), (1.05, 0, 0), 25, (1.0, 0.72, 0.45), 0.08)
for wx in (-2.4, 2.6): light_at(f'winlight{wx}', 'AREA', (wx, WALL_Y - 0.15, 1.95), (wx, -3, 1.3), 30, (1.0, 0.72, 0.45), 1.1)
# ---------------------------------------------------------------- the deck: boards, joists, rails, steps down to the lawn
DECKM = P.material('ph:wood_floor_deck', scale=1.0, name='deckwood')
DX0, DX1, DY0 = -4.2, 3.6, -0.6
deck = box('deck', (DX1 - DX0, WALL_Y - DY0, 0.06), ((DX0 + DX1) / 2, (WALL_Y + DY0) / 2, DECK_Z - 0.03), DECKM)
rail_m = mat('railwood', (0.40, 0.27, 0.16), 0.75); noisy(rail_m, 6.0, 0.25, 0.1)
box('deck_fascia', (DX1 - DX0, 0.04, DECK_Z), ((DX0 + DX1) / 2, DY0 - 0.02, DECK_Z / 2), rail_m)
box('deck_fascia_l', (0.04, WALL_Y - DY0, DECK_Z), (DX0 - 0.02, (WALL_Y + DY0) / 2, DECK_Z / 2), rail_m)
# rails: along the front (gap for the steps at x 1.7..2.9) and the left side
def rail_run(p0, p1, nm):
    p0 = Vector(p0); p1 = Vector(p1); L_ = (p1 - p0).length; d_ = (p1 - p0).normalized(); n_ = int(L_ / 0.12)
    for k in range(n_ + 1):
        q = p0 + d_ * (k * L_ / max(n_, 1)); box(f'{nm}bal{k}', (0.04, 0.04, 0.82), (q.x, q.y, DECK_Z + 0.43), rail_m)
    mid = (p0 + p1) / 2; ang = math.atan2(d_.y, d_.x)
    box(f'{nm}top', (L_ + 0.1, 0.14, 0.05), (mid.x, mid.y, DECK_Z + 0.88), rail_m, rot=(0, 0, ang))
    box(f'{nm}bot', (L_, 0.08, 0.05), (mid.x, mid.y, DECK_Z + 0.06), rail_m, rot=(0, 0, ang))
    for q in (p0, p1): box(f'{nm}post{q.x:.1f}', (0.1, 0.1, 1.0), (q.x, q.y, DECK_Z + 0.5), rail_m)
rail_run((DX0, DY0, 0), (1.6, DY0, 0), 'rf'); rail_run((3.0, DY0, 0), (DX1, DY0, 0), 'rf2'); rail_run((DX0, DY0, 0), (DX0, WALL_Y - 0.1, 0), 'rl')
for k in range(3):
    box(f'step{k}', (1.4, 0.32, 0.05), (2.3, DY0 - 0.18 - 0.3 * k, DECK_Z - 0.15 * (k + 1)), DECKM)
# ---------------------------------------------------------------- the porch roof over the deck: posts, beam, rafters, a shingled top, a gutter
ROOF_Z0, ROOF_Z1 = 2.75, 2.45             # at the wall, at the front beam
POSTS_X = (-3.9, -1.2, 1.55, 3.3)
for px in POSTS_X: box(f'rpost{px}', (0.13, 0.13, ROOF_Z1 - DECK_Z), (px, DY0 + 0.15, (ROOF_Z1 + DECK_Z) / 2), rail_m)
box('beam', (DX1 - DX0 + 0.3, 0.16, 0.22), ((DX0 + DX1) / 2, DY0 + 0.15, ROOF_Z1 + 0.04), rail_m)
pitch = math.atan2(ROOF_Z0 - ROOF_Z1, WALL_Y - DY0)
RAFTERS = []
for k in range(15):
    x_ = DX0 + 0.05 + k * (DX1 - DX0 - 0.1) / 14
    RAFTERS.append(box(f'rafter{k}', (0.05, (WALL_Y - DY0) / math.cos(pitch) + 0.3, 0.14), (x_, (WALL_Y + DY0) / 2 - 0.15, (ROOF_Z0 + ROOF_Z1) / 2 + 0.16),
                       rail_m, rot=(pitch, 0, 0)))
ceil_m = mat('beadboard', (0.78, 0.76, 0.70), 0.6); noisy(ceil_m, 60.0, 0.06, 0.05)
ROOF_UNDER = box('roof_under', (DX1 - DX0 + 0.3, (WALL_Y - DY0) / math.cos(pitch) + 0.3, 0.02), ((DX0 + DX1) / 2, (WALL_Y + DY0) / 2 - 0.15, (ROOF_Z0 + ROOF_Z1) / 2 + 0.24),
                 ceil_m, rot=(pitch, 0, 0))
SHING = P.material('ph:grey_roof_01', scale=0.8, name='shingles')
ROOF_TOP = box('roof_top', (DX1 - DX0 + 0.4, (WALL_Y - DY0) / math.cos(pitch) + 0.45, 0.05), ((DX0 + DX1) / 2, (WALL_Y + DY0) / 2 - 0.2, (ROOF_Z0 + ROOF_Z1) / 2 + 0.28),
               SHING, rot=(pitch, 0, 0))
gut_m = mat('gutter', (0.88, 0.88, 0.86), 0.35, 0.3)
box('gutter', (DX1 - DX0 + 0.4, 0.12, 0.1), ((DX0 + DX1) / 2, DY0 - 0.32, ROOF_Z1 + 0.22), gut_m)
box('downspout', (0.07, 0.07, ROOF_Z1 + 0.2), (DX1 + 0.15, DY0 - 0.32, (ROOF_Z1 + 0.2) / 2), gut_m)
# string lights along the beam (warm bulbs, a catenary)
BULB = emis('bulb', (1.0, 0.78, 0.45), 9.0)
wire_pts = []
for k in range(41):
    u = k / 40; x_ = lerp(DX0 + 0.1, DX1 - 0.1, u); sag = 0.22 * (1 - (2 * ((u * 4) % 1) - 1) ** 2)
    wire_pts.append((x_, DY0 + 0.05, ROOF_Z1 - 0.1 - sag))
tube('lightwire', wire_pts, 0.004, mat('wire', (0.02, 0.02, 0.02), 0.5), seg=5)
for k in range(2, 40, 3):
    q = wire_pts[k]; prim('uv_sphere', f'bulb{k}', BULB, loc=(q[0], q[1], q[2] - 0.05), scale=(0.025, 0.025, 0.035), segments=10, ring_count=6)
# ---------------------------------------------------------------- props on the deck and the lawn
try:
    P.place('ph:wooden_picnic_table', loc=(-2.7, 1.6, DECK_Z), rot_deg=5, height=0.76)
    P.place('ph:metal_trash_can', loc=(-3.7, 2.8, DECK_Z), rot_deg=20, height=0.75)
    P.place('ph:potted_plant_02', loc=(3.15, 2.85, DECK_Z), rot_deg=40, height=0.9)
    P.place('ph:potted_plant_02', loc=(-3.75, DY0 + 0.35, DECK_Z), rot_deg=-60, height=0.75)
    P.place('ph:garden_hose_wall_mounted_01', loc=(-1.6, WALL_Y - 0.05, 0.9), rot_deg=180, height=0.5)
    P.place('ph:garden_gloves_01', loc=(-2.5, 1.55, DECK_Z + 0.77), rot_deg=30, height=0.04)
    P.place('ph:Lantern_01', loc=(-2.95, 1.7, DECK_Z + 0.77), rot_deg=0, height=0.32)
except Exception as e_: print('prop skipped', e_)
for k in range(60):                                   # grass clumps near the deck edge and out by the safe fryer
    x_ = -6 + 14 * h1(k + 3); y_ = -1.0 - 12 * h1(k + 41)
    try: P.place('ph:grass_medium_01', loc=(x_, y_, 0), rot_deg=360 * h1(k + 9), height=0.18 + 0.12 * h1(k + 2))
    except Exception: break
# light: a low warm key (last of the sun), a cool fill, a rim from behind the house
light_at('sun_key', 'SUN', (5, -6, 4), (0, 0, 0), 1.6, (1.0, 0.62, 0.38))
light_at('cool_fill', 'AREA', (-5, -6, 4), (0, 1, 1), 280, (0.55, 0.65, 1.0), 6)
light_at('pot_key', 'AREA', (0.9, 0.0, 1.75), (0.0, 1.05, 1.0), 70, (1.0, 0.9, 0.8), 1.2)
# ================================================================ the fryer: burner stand + blue jets, propane tank and hose, aluminium stockpot, oil,
# the turkey (frozen: frost on the skin; x-ray: ghost skin with an ice core), poultry rack and lift hook
STEEL = mat('steel', (0.30, 0.30, 0.32), 0.38, 1.0); noisy(STEEL, 30.0, 0.15, 0.12)
CAST = mat('castiron', (0.05, 0.05, 0.055), 0.6, 0.7); noisy(CAST, 50.0, 0.3, 0.15)
HOSE = mat('hose', (0.03, 0.03, 0.035), 0.55)
BRASS = bpy.data.materials.get('brass') or mat('brass', (0.85, 0.62, 0.3), 0.25, 1.0)

# pot: brushed aluminium; object prop xr (0..1) turns it into a see-through ghost with lit edges
def pot_mat(name):
    m = mat(name, (0.93, 0.93, 0.95), 0.40, 0.88); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    try: b.inputs['Anisotropic'].default_value = 0.6
    except Exception: pass
    nz = tnoise(nt, coord(nt, 'Object'), 900.0, 1.0)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.36; mr.inputs['To Max'].default_value = 0.44
    nt.links.new(nz, mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    out = nt.nodes['Material Output']; tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.55, 0.8, 1.0, 1); fr = nt.nodes.new('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.08
    rim = math_(nt, 'POWER', fr.outputs['Facing'], 3.0); em_s = nt.nodes.new('ShaderNodeMath'); em_s.operation = 'MULTIPLY'
    nt.links.new(rim, em_s.inputs[0]); em_s.inputs[1].default_value = 1.2; nt.links.new(em_s.outputs[0], em.inputs['Strength'])
    ghost = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr.outputs[0], ghost.inputs[0]); nt.links.new(em.outputs[0], ghost.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac'])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(ghost.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def oil_mat(name, hot=0.0):
    m = mat(name, (0.95, 0.62, 0.12), 0.06, 0.0, trans=1.0, ior=1.47); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (1.0, 0.55, 0.12, 1); b.inputs['Emission Strength'].default_value = 0.08 + hot
    try: b.inputs['Transmission Weight'].default_value = 0.92
    except Exception: pass
    return m

def skin_mat(name, frost=True):
    """raw turkey skin with goose bumps; object props frost (white crystals) and xr (ghost) and cook (browning)"""
    m = mat(name, (0.93, 0.77, 0.68), 0.42); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.35; b.inputs['Subsurface Radius'].default_value = (0.9, 0.35, 0.25)
    try: b.inputs['Subsurface Scale'].default_value = 0.02
    except Exception: pass
    co = coord(nt, 'Object'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 140.0; nt.links.new(co, vo.inputs['Vector'])
    goose = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', vo.outputs['Distance'], 2.6), 1.0)), 4.0)
    blot = tnoise(nt, co, 9.0, 4.0)
    base = mixc(nt, blot, (0.92, 0.64, 0.50), (0.80, 0.48, 0.40))
    cook = objattr(nt, 'cook'); base = mixc(nt, cook, base, (0.62, 0.36, 0.13))
    fz = objattr(nt, 'frost'); vf = nt.nodes.new('ShaderNodeTexVoronoi'); vf.inputs['Scale'].default_value = 260.0; nt.links.new(co, vf.inputs['Vector'])
    crys = math_(nt, 'MULTIPLY', fz, math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', tnoise(nt, co, 22.0, 6.0), 0.5), 0.0), 2.4))
    col = mixc(nt, math_(nt, 'MINIMUM', crys, 1.0), base, (0.93, 0.96, 1.0))
    nt.links.new(col, b.inputs['Base Color'])
    nt.links.new(math_(nt, 'ADD', 0.40, math_(nt, 'MULTIPLY', fz, -0.15)), b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.0006
    nt.links.new(math_(nt, 'ADD', goose, math_(nt, 'MULTIPLY', fz, math_(nt, 'MULTIPLY', vf.outputs['Distance'], 1.5))), bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    try: b.inputs['Coat Weight'].default_value = 0.0
    except Exception: pass
    # x-ray ghost: faint pink rim + see-through
    out = nt.nodes['Material Output']; tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (1.0, 0.55, 0.45, 1); lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.25
    es = math_(nt, 'ADD', 0.15, math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 1.4), 5.0)); nt.links.new(es, em.inputs['Strength'])
    gh = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr.outputs[0], gh.inputs[0]); nt.links.new(em.outputs[0], gh.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac'])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(gh.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def blob_union(name, parts, voxel=0.0055, m=None):
    """join ellipsoids/capsules and voxel-remesh them into one smooth skin"""
    objs = []
    for kind, a_, b_, r_ in parts:
        if kind == 'e':
            o = prim('uv_sphere', name + '_p', None, loc=a_, scale=b_, segments=24, ring_count=14, radius=1.0); objs.append(o)
        else:
            pts = [Vector(a_).lerp(Vector(b_), u) for u in np.linspace(0, 1, 8)]
            o = tube(name + '_c', [tuple(p) for p in pts], (lambda u, r0=r_[0], r1=r_[1]: lerp(r0, r1, u)), None, seg=14); objs.append(o)
            for p_, rr in ((a_, r_[0]), (b_, r_[1])): objs.append(prim('uv_sphere', name + '_cap', None, loc=p_, scale=(rr, rr, rr), segments=14, ring_count=8, radius=1.0))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); o = bpy.context.active_object; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    rm = o.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel
    sm_ = o.modifiers.new('sm', 'SMOOTH'); sm_.factor = 0.8; sm_.iterations = 6
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); old = o.data
    o.modifiers.clear(); o.data = me; bpy.data.meshes.remove(old)
    for p in o.data.polygons: p.use_smooth = True
    if m: o.data.materials.append(m)
    return o

def build_turkey(name, m_skin):
    """upright on the rack, neck end down, drumsticks up; origin at the bottom; breast faces -y"""
    parts = [('e', (0, 0.01, 0.17), (0.125, 0.108, 0.16), None), ('e', (0, -0.04, 0.16), (0.112, 0.09, 0.135), None),
             ('e', (0, 0.02, 0.045), (0.068, 0.062, 0.055), None), ('e', (0, 0.05, 0.27), (0.09, 0.06, 0.06), None)]
    for s in (-1, 1):
        parts += [('e', (s * 0.098, 0.0, 0.25), (0.058, 0.07, 0.08), None),
                  ('c', (s * 0.095, -0.03, 0.29), (s * 0.035, -0.115, 0.335), (0.04, 0.02)),
                  ('e', (s * 0.03, -0.12, 0.338), (0.019, 0.019, 0.017), None),
                  ('e', (s * 0.112, 0.03, 0.105), (0.034, 0.055, 0.075), None)]
    o = blob_union(name, parts, m=m_skin)
    o['frost'] = 1.0; o['xr'] = 0.0; o['cook'] = 0.0
    # knuckle ends of the drumsticks (bone tips), a little darker
    knk = mat('knuckle', (0.92, 0.86, 0.80), 0.4)
    for s in (-1, 1): prim('uv_sphere', f'{name}_knk{s}', knk, parent=o, loc=(s * 0.026, -0.128, 0.342), scale=(0.014, 0.014, 0.012), segments=12, ring_count=8)
    tube(f'{name}_twine', [(-0.04, -0.112, 0.33), (0, -0.13, 0.334), (0.04, -0.112, 0.33)], 0.0025, mat('twine', (0.85, 0.80, 0.68), 0.8), o, seg=6)
    return o

ICE_M = mat('ice', (0.6, 0.85, 1.0), 0.05, trans=0.85, ior=1.31, emit=(0.3, 0.6, 1.0), estr=0.45)
WATER_M = mat('waterdrop', (0.45, 0.75, 1.0), 0.04, trans=0.6, ior=1.33, emit=(0.25, 0.55, 1.0), estr=1.2)
STEAMB_M = mat('steambubble', (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=0.72, emit=(0.8, 0.9, 1.0), estr=0.05)

def build_fryer(name, at, safe=False):
    F = {'at': Vector(at)}; X, Y, Z = at
    root = empty(name, loc=at); F['root'] = root
    # stand: a ring on three splayed legs, a cross brace, the burner head with its jet ring
    RING_Z = 0.32
    tube(f'{name}_ring', [(0.2 * math.cos(2 * math.pi * k / 40), 0.2 * math.sin(2 * math.pi * k / 40), RING_Z) for k in range(41)], 0.011, STEEL, root, seg=8, caps=False)
    for k in range(3):
        a_ = 2 * math.pi * k / 3 + 0.5
        tube(f'{name}_leg{k}', [(0.2 * math.cos(a_), 0.2 * math.sin(a_), RING_Z), (0.29 * math.cos(a_), 0.29 * math.sin(a_), 0.0)], 0.012, STEEL, root, seg=8)
        prim('cylinder', f'{name}_foot{k}', HOSE, root, loc=(0.29 * math.cos(a_), 0.29 * math.sin(a_), 0.008), scale=(0.022, 0.022, 0.008), vertices=12)
        tube(f'{name}_brace{k}', [(0.24 * math.cos(a_), 0.24 * math.sin(a_), 0.17), (0.04 * math.cos(a_), 0.04 * math.sin(a_), 0.17)], 0.008, STEEL, root, seg=6)
    for k in range(3):
        a_ = 2 * math.pi * k / 3 + 0.5 + math.pi / 3
        box(f'{name}_tab{k}', (0.05, 0.02, 0.02), (0.185 * math.cos(a_), 0.185 * math.sin(a_), RING_Z + 0.012), STEEL, rot=(0, 0, a_), parent=root)
    lathe(f'{name}_burner', [(0.0, 0.13), (0.075, 0.13), (0.08, 0.155), (0.072, 0.17), (0.04, 0.172), (0.0, 0.172)], 32, CAST, root)
    tube(f'{name}_venturi', [(0.0, 0.0, 0.15), (0.0, -0.12, 0.15), (0.0, -0.24, 0.165)], 0.016, CAST, root, seg=10)
    lathe(f'{name}_valve', [(0.0, 0.0), (0.02, 0.0), (0.02, 0.04), (0.0, 0.04)], 12, BRASS, root, loc=(0, -0.27, 0.145))
    # blue jets: little cones around the burner head (flicker set per frame)
    jet_m = bpy.data.materials.get('jet')
    if jet_m is None:
        jet_m = emis_mix('jet', (0.06, 0.22, 1.0), 2.0, 'ja'); ntj = jet_m.node_tree; mxj = next(n for n in ntj.nodes if n.type == 'MIX_SHADER')
        zj = sepz(ntj, coord(ntj, 'Generated')).outputs['Z']; fadej = math_(ntj, 'MULTIPLY', math_(ntj, 'POWER', math_(ntj, 'SUBTRACT', 1.0, zj), 1.5), 0.75)
        for l in list(ntj.links):
            if l.to_socket == mxj.inputs['Fac']: ntj.links.remove(l)
        ntj.links.new(fadej, mxj.inputs['Fac'])
        ej = next(n for n in ntj.nodes if n.type == 'EMISSION'); ntj.links.new(mixc(ntj, zj, (0.35, 0.55, 1.0), (0.02, 0.08, 0.9)), ej.inputs['Color'])
    JETS = []
    for k in range(18):
        a_ = 2 * math.pi * k / 18
        j = prim('cone', f'{name}_jet{k}', jet_m, root, loc=(0.062 * math.cos(a_), 0.062 * math.sin(a_), 0.2), vertices=8, radius1=1.0, depth=2.0); j.scale = (0.008, 0.008, 0.03)
        j.rotation_euler = (0.5 * math.sin(a_) * -1 * 0, 0, 0); j['ja'] = 1.0; JETS.append(j)
    F['jets'] = JETS
    blue_l = light_at(f'{name}_burnlight', 'POINT', (X, Y, Z + 0.22), (X, Y, Z + 1), 18, (0.35, 0.5, 1.0), 0.05); F['burnlight'] = blue_l
    # the pot
    POT_Z = RING_Z + 0.012; PH = 0.42; PR = 0.17; F['pot_z'] = Z + POT_Z; F['pr'] = PR; F['ph'] = PH
    pm = pot_mat(f'{name}_potm')
    prof = [(0.0, 0.0), (PR - 0.012, 0.0), (PR, 0.01), (PR, PH - 0.006), (PR + 0.006, PH), (PR + 0.003, PH + 0.006), (PR - 0.004, PH + 0.004), (PR - 0.004, 0.006), (0.0, 0.006)]
    pot = lathe(f'{name}_pot', prof, 96, pm, root, loc=(0, 0, POT_Z)); pot['xr'] = 0.0; F['pot'] = pot
    for s in (-1, 1):
        tube(f'{name}_handle{s}', [(s * PR, -0.045, POT_Z + PH - 0.07), (s * (PR + 0.045), -0.04, POT_Z + PH - 0.065), (s * (PR + 0.05), 0, POT_Z + PH - 0.06),
                                   (s * (PR + 0.045), 0.04, POT_Z + PH - 0.065), (s * PR, 0.045, POT_Z + PH - 0.07)], 0.007, pm, pot, seg=8)
    # thermometer clipped to the rim: dial + probe
    if not safe:
        tube(f'{name}_probe', [(0.12, -0.11, POT_Z + PH + 0.05), (0.11, -0.1, POT_Z + 0.15)], 0.003, STEEL, pot, seg=6)
        dial = lathe(f'{name}_dial', [(0.0, 0.0), (0.028, 0.0), (0.03, 0.01), (0.0, 0.012)], 24, STEEL, pot, loc=(0.12, -0.11, POT_Z + PH + 0.05))
        dial.rotation_euler = (R(75), 0, R(-48));
        face_m = mat('dialface', (0.95, 0.95, 0.92), 0.4)
        df = prim('cylinder', f'{name}_dialface', face_m, dial, loc=(0, 0, 0.0115), scale=(0.025, 0.025, 0.001), vertices=24)
        box(f'{name}_needle', (0.002, 0.02, 0.001), (0.0, 0.006, 0.0135), mat('needle', (0.8, 0.05, 0.03), 0.4), parent=dial)
    # oil: the top surface (ripples by bump + bubbles), and the body (seen in x-ray)
    OIL_M = oil_mat(f'{name}_oilm')
    nt = OIL_M.node_tree; b = nt.nodes['Principled BSDF']; wv = nt.nodes.new('ShaderNodeTexNoise'); wv.inputs['Scale'].default_value = 40.0
    nt.links.new(coord(nt, 'Object'), wv.inputs['Vector']); w4 = nt.nodes.new('ShaderNodeValue'); wv.noise_dimensions = '4D'
    nt.links.new(objattr(nt, 'ph'), wv.inputs['W']); bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Distance'].default_value = 0.002
    nt.links.new(objattr(nt, 'boil'), bp.inputs['Strength']); nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    top = prim('circle', f'{name}_oiltop', OIL_M, root, loc=(0, 0, POT_Z + 0.2), radius=PR - 0.005, vertices=64, fill_type='NGON')
    top['ph'] = 0.0; top['boil'] = 0.05; F['oiltop'] = top
    OB_M = bpy.data.materials.get('oilbody_m')
    if OB_M is None:
        OB_M = bpy.data.materials.new('oilbody_m'); OB_M.use_nodes = True; nt2 = OB_M.node_tree; nt2.nodes.remove(nt2.nodes['Principled BSDF'])
        tr2 = nt2.nodes.new('ShaderNodeBsdfTransparent'); tr2.inputs['Color'].default_value = (0.97, 0.66, 0.24, 1)
        em2 = nt2.nodes.new('ShaderNodeEmission'); em2.inputs['Color'].default_value = (1.0, 0.55, 0.12, 1); em2.inputs['Strength'].default_value = 0.06
        gl2 = nt2.nodes.new('ShaderNodeBsdfGlossy'); gl2.inputs['Roughness'].default_value = 0.05; lw2 = nt2.nodes.new('ShaderNodeLayerWeight'); lw2.inputs['Blend'].default_value = 0.15
        mx2 = nt2.nodes.new('ShaderNodeMixShader'); nt2.links.new(lw2.outputs['Fresnel'], mx2.inputs['Fac']); nt2.links.new(tr2.outputs[0], mx2.inputs[1]); nt2.links.new(gl2.outputs[0], mx2.inputs[2])
        ad2 = nt2.nodes.new('ShaderNodeAddShader'); nt2.links.new(mx2.outputs[0], ad2.inputs[0]); nt2.links.new(em2.outputs[0], ad2.inputs[1])
        nt2.links.new(ad2.outputs[0], nt2.nodes['Material Output'].inputs['Surface'])
    body = prim('cylinder', f'{name}_oilbody', OB_M, root, loc=(0, 0, POT_Z + 0.1), vertices=64); body.scale = (PR - 0.006, PR - 0.006, 0.1)
    body.hide_render = True; F['oilbody'] = body
    # the turkey on its rack
    sk = skin_mat(f'{name}_skin')
    tk = build_turkey(f'{name}_turkey', sk); tk.parent = root; F['turkey'] = tk
    if safe: tk['frost'] = 0.0; tk['cook'] = 0.85
    rack = empty(f'{name}_rack', root); tk.parent = rack; tk.location = (0, 0, 0.012); F['rack'] = rack
    lathe(f'{name}_rackplate', [(0.0, 0.0), (0.095, 0.0), (0.1, 0.012), (0.095, 0.014), (0.0, 0.006)], 32, STEEL, rack)
    for k in range(6):
        a_ = 2 * math.pi * k / 6; tube(f'{name}_rackwire{k}', [(0.09 * math.cos(a_), 0.09 * math.sin(a_), 0.01), (0.03 * math.cos(a_), 0.03 * math.sin(a_), 0.10)], 0.0035, STEEL, rack, seg=6)
    tube(f'{name}_rackrod', [(0, 0, 0.0), (0, 0, 0.50)], 0.006, STEEL, rack, seg=8)
    tube(f'{name}_rackloop', [(0.022 * math.cos(2 * math.pi * k / 20), 0, 0.522 + 0.022 * math.sin(2 * math.pi * k / 20)) for k in range(21)], 0.004, STEEL, rack, seg=6, caps=False)
    # ice core (inside the breast) + the melt water that runs out of the bottom
    if not safe:
        ice = prim('ico_sphere', f'{name}_ice', ICE_M, tk, loc=(0, -0.01, 0.16), subdivisions=2); ice.scale = (0.085, 0.07, 0.11)
        for p_ in ice.data.polygons: p_.use_smooth = False
        dp = ice.modifiers.new('d', 'DISPLACE'); tx_ = bpy.data.textures.new('icetx', 'VORONOI'); tx_.noise_scale = 0.05; dp.texture = tx_; dp.strength = 0.012
        ice.hide_render = True; F['ice'] = ice
        # rack hook: a J-hook in the loop, long rod up to a T-handle (held at frame one, then left leaning on the rim)
        hk = empty(f'{name}_hook', rack, loc=(0, 0, 0.522)); F['hook'] = hk
        tube(f'{name}_hookj', [(0.0, 0.0, -0.02), (0.012, 0, -0.03), (0.02, 0, -0.012), (0.012, 0, 0.012), (-0.04, 0, 0.05), (-0.2, 0, 0.09), (-0.44, 0, 0.11)], 0.0055, STEEL, hk, seg=8)
        tube(f'{name}_hookT', [(-0.44, -0.12, 0.11), (-0.44, 0.12, 0.11)], 0.012, mat('grip', (0.08, 0.08, 0.09), 0.6), hk, seg=10)
    else:
        tk['frost'] = 0.0
    # hose from the valve to the tank regulator
    return F

FRY = build_fryer('fryer', (0.0, 1.05, DECK_Z))
SAFE = build_fryer('safe', (3.6, -8.6, 0.0), safe=True)
try:
    TANK = P.place('ph:propane_tank', loc=(0.62, 1.42, DECK_Z), rot_deg=30, height=0.55, name='tank')
    TANK2 = P.place('ph:propane_tank', loc=(4.2, -8.25, 0.0), rot_deg=-20, height=0.55, name='tank2')
except Exception as e_: print('tank skipped', e_)
def hose(nm, p0, p1, sag=0.08):
    p0 = Vector(p0); p1 = Vector(p1); pts = []
    for u in np.linspace(0, 1, 24):
        q = p0.lerp(p1, u); q.z -= sag * 4 * u * (1 - u) + 0.0; pts.append(tuple(q))
    tube(nm, pts, 0.008, HOSE, seg=8)
for F_, tk_ in ((FRY, (0.62, 1.42, DECK_Z)), (SAFE, (4.2, -8.25, 0.0))):
    a0 = F_['at'] + Vector((0, -0.27, 0.165)); top_ = Vector(tk_) + Vector((0, 0, 0.6))
    hose(F_['root'].name + '_hose', a0, top_, sag=0.35)
    lathe(F_['root'].name + '_reg', [(0.0, 0.0), (0.025, 0.0), (0.03, 0.03), (0.0, 0.035)], 16, BRASS, loc=tuple(top_))
# ================================================================ the man: house MakeHuman model (man.blend), live rig. IK hands on the hook's T-handle
# (palms down, fingers wrapped round the bar), then he lets go, flinches and backs away from the fire with his arms up.
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
MANCOL = bpy.data.collections.new('man'); S.collection.children.link(MANCOL)
for o in _dst.objects: MANCOL.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
PB = RIG.pose.bones
try:
    with bpy.data.libraries.load(asset('pilot.blend'), link=False) as (_s2, _d2):
        _d2.objects = ['Human.shoes05']
    SHOES = _d2.objects[0]; MANCOL.objects.link(SHOES); SHOES.parent = RIG; SHOES.matrix_parent_inverse.identity()
    for md in SHOES.modifiers:
        if md.type == 'ARMATURE': md.object = RIG
    _bvg2 = {g.index: g.name for g in BODY.vertex_groups}
    fg = BODY.vertex_groups.new(name='under_shoes')
    for v in BODY.data.vertices:
        w = sum(g.weight for g in v.groups if any(_bvg2.get(g.group, '').startswith(k) for k in ('foot', 'toe')))
        if w > 0.3 and v.co.z < 0.13: fg.add([v.index], 1.0, 'REPLACE')
    mk = BODY.modifiers.new('hide_feet', 'MASK'); mk.vertex_group = 'under_shoes'; mk.invert_vertex_group = True
    BODY.modifiers.move(len(BODY.modifiers) - 1, 0)
    print('shoes on')
except Exception as e_: print('shoes skipped', e_)
for o in MANCOL.objects:
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
MAN = empty('man_root', loc=(-0.98, 1.08, DECK_Z)); MAN.rotation_euler = (0, 0, math.pi / 2)        # faces +x (the pot)
RIG.parent = MAN; RIG.location = (0, 0, 0); RIG.rotation_euler = (0, 0, 0)
# shirt: dark red flannel tint on the top half, jeans stay; an apron = his shirt's front torso faces pushed out
SH_SRC = SUIT.data.materials[0]; SHIRT = SH_SRC.copy(); SHIRT.name = 'flannel'; SUIT.data.materials.append(SHIRT)
for p_ in SUIT.data.polygons:
    if sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) > 0.93: p_.material_index = 1
def retint(m, col, keep=0.35, rough=0.9, sheen=0.4):
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    src = lk.from_socket if lk else None
    bw = nt.nodes.new('ShaderNodeRGBToBW'); mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - keep; mr.inputs['To Max'].default_value = 1.0 + keep * 0.3
    if src: nt.links.new(src, bw.inputs['Color']); nt.links.new(bw.outputs['Val'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mul.inputs['A'])
    else: mul.inputs['A'].default_value = (1, 1, 1, 1)
    mul.inputs['B'].default_value = (*col, 1); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Tint'].default_value = (*col, 1)
    # flannel check: a plaid of two wave bands
    try:
        co = coord(nt, 'Object'); sx = sepz(nt, co)
        bx = math_(nt, 'GREATER_THAN', math_(nt, 'SINE', math_(nt, 'MULTIPLY', sx.outputs['X'], 70.0)), 0.55)
        bz = math_(nt, 'GREATER_THAN', math_(nt, 'SINE', math_(nt, 'MULTIPLY', sx.outputs['Z'], 70.0)), 0.55)
        pl = math_(nt, 'MAXIMUM', bx, bz)
        mm = nt.nodes.new('ShaderNodeMix'); mm.data_type = 'RGBA'; nt.links.new(pl, mm.inputs['Factor']); nt.links.new(mul.outputs['Result'], mm.inputs['A'])
        mm.inputs['B'].default_value = (0.06, 0.04, 0.04, 1); nt.links.new(mm.outputs['Result'], b.inputs['Base Color'])
    except Exception as e_: print('plaid skipped', e_)
    return m
retint(SHIRT, (0.55, 0.08, 0.06), 0.3)
_vgn = {g.index: g.name for g in SUIT.vertex_groups}
_ARM = {b_ + s_ for s_ in ('.L', '.R') for b_ in ('clavicle', 'shoulder01', 'upperarm01', 'upperarm02', 'lowerarm01', 'lowerarm02', 'wrist')}
def _armw(v): return sum(g.weight for g in v.groups if _vgn.get(g.group, '') in _ARM)
_af = [p_.index for p_ in SUIT.data.polygons if 0.62 < sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) < 1.36
       and sum(SUIT.data.vertices[i].co.y for i in p_.vertices) / len(p_.vertices) < -0.02 and max(_armw(SUIT.data.vertices[i]) for i in p_.vertices) < 0.2]
_bm = bmesh.new(); _bm.from_mesh(SUIT.data); _keep = set(_af)
bmesh.ops.delete(_bm, geom=[f for f in _bm.faces if f.index not in _keep], context='FACES'); _bm.normal_update()
for v in _bm.verts: v.co += v.normal * 0.016
_am = bpy.data.meshes.new('apron'); _bm.to_mesh(_am); _bm.free()
APRON = bpy.data.objects.new('apron', _am); MANCOL.objects.link(APRON); APRON.parent = SUIT.parent; APRON.matrix_parent_inverse = SUIT.matrix_parent_inverse.copy()
APRON.matrix_world = SUIT.matrix_world.copy()
for g in SUIT.vertex_groups: APRON.vertex_groups.new(name=g.name)
_md = APRON.modifiers.new('arm', 'ARMATURE'); _md.object = RIG
_sol = APRON.modifiers.new('thick', 'SOLIDIFY'); _sol.thickness = 0.006; _sol.offset = 1.0
AP_M = mat('apronm', (0.16, 0.17, 0.19), 0.85, sheen=0.3); noisy(AP_M, 160.0, 0.15, 0.05); APRON.data.materials.append(AP_M)
# work gloves: paint the hands by bone weights (a glove material on the body's hand faces)
GLOVE = mat('glove', (0.62, 0.48, 0.30), 0.8, sheen=0.4); noisy(GLOVE, 90.0, 0.2, 0.1)
BODY.data.materials.append(GLOVE); _gi = len(BODY.data.materials) - 1
_bvg = {g.index: g.name for g in BODY.vertex_groups}
def _handw(v): return sum(g.weight for g in v.groups if any(_bvg.get(g.group, '').startswith(k) for k in ('wrist', 'finger', 'metacarpal')))
for p_ in BODY.data.polygons:
    if min(_handw(BODY.data.vertices[i]) for i in p_.vertices) > 0.5: p_.material_index = _gi

# ---- IK
def ik(bone, target, pole, chain=4, pole_angle=0.0):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TG = {k: empty('tg_' + k) for k in ('hR', 'hL', 'pR', 'pL', 'rotR', 'rotL')}
IKR = ik('wrist.R', TG['hR'], TG['pR'], 5, R(-90)); IKL = ik('wrist.L', TG['hL'], TG['pL'], 5, R(-90))
def _hand_frame(side):
    b = RIG.data.bones
    d = (b['finger3-1.' + side].head_local - b['wrist.' + side].head_local).normalized()
    n = b['finger3-1.' + side].matrix_local.to_3x3().col[2]; n = (n - d * n.dot(d)).normalized()
    a = d.cross(n); th = b['finger1-1.' + side].head_local - b['finger3-1.' + side].head_local
    return Matrix((a, d, n)).transposed(), (1.0 if th.dot(a) > 0 else -1.0)
HAND = {}
for s_ in ('R', 'L'):
    Hr, ts = _hand_frame(s_); Wr = RIG.data.bones['wrist.' + s_].matrix_local.to_3x3(); TG['rot' + s_].rotation_mode = 'QUATERNION'
    c = PB['wrist.' + s_].constraints.new('COPY_ROTATION'); c.target = TG['rot' + s_]; c.owner_space = c.target_space = 'WORLD'
    HAND[s_] = (Hr.transposed() @ Wr, ts, c)
def grip(side, bar_pt, w):
    """palm on top of a horizontal bar, fingers curling over its far side; returns the wrist IK target (world)"""
    O, ts, con = HAND[side]; con.influence = w
    fwd = (MAN.matrix_world.to_3x3().normalized() @ Vector((0, -1, 0))).normalized()     # his front, in the world
    d = (fwd * 0.72 + Vector((0, 0, -0.69))).normalized()                                 # toward the fingers: forward and down over the bar
    n = (Vector((0, 0, -1)) * 0.72 - fwd * 0.69).normalized()                             # palm faces down (and a little back) onto the bar
    a = d.cross(n)
    TG['rot' + side].rotation_quaternion = (Matrix((a, d, n)).transposed() @ O).to_quaternion()
    return Vector(bar_pt) - n * 0.032 - d * 0.05
FING = {s_: [f'finger{f_}-{g}.{s_}' for f_ in range(1, 6) for g in (1, 2, 3)] for s_ in ('L', 'R')}
def fingers(side, w):
    for nm in FING[side]:
        if nm not in PB: continue
        f_ = int(nm[6]); seg = int(nm[8])
        held = (14, 20, 12)[seg - 1] if f_ == 1 else (40, 62, 38)[seg - 1]; loose = (6, 8, 5)[seg - 1] if f_ == 1 else (12, 16, 10)[seg - 1]
        pb = PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(lerp(loose, held, w)), 0, 0)
def man_pose(spine=0.0, neck=0.0, head=0.0, head_yaw=0.0, legs=None):
    for n, k in (('spine03', 0.3), ('spine02', 0.3), ('spine01', 0.4)):
        pb = PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(spine * k), 0, 0)
    for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)):
        pb = PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(neck * k), R(head_yaw * k * 0.5), 0)
    pb = PB['head']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(head), R(head_yaw * 0.5), 0)
    for nm in ('upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'foot.L', 'foot.R'):
        pb = PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (legs or {}).get(nm, (0, 0, 0))
def man_world(p): return MAN.matrix_world @ Vector(p)
KNK = ('finger2-1', 'finger3-1', 'finger4-1', 'finger5-1')
def knuckles(side):
    ps = [RIG.matrix_world @ PB[k + '.' + side].head for k in KNK if k + '.' + side in PB]
    return sum(ps, Vector()) / len(ps)
def grip_fix(want, w, iters=3):
    """closed loop: nudge each wrist target until the knuckle line sits where it should on the bar"""
    if w <= 0.01: return
    for _ in range(iters):
        bpy.context.view_layer.update()
        for s_, p in want.items():
            err = p - knuckles(s_); TG['h' + s_].location += err * w
    bpy.context.view_layer.update()
# ================================================================ effects
POT_Z0 = FRY['pot_z']; PR_ = FRY['pr']; PH_ = FRY['ph']; FX, FY = FRY['at'].x, FRY['at'].y
FLOOR_Z = POT_Z0 + 0.006; RIM_Z = POT_Z0 + PH_
OIL0 = POT_Z0 + 0.20                              # oil level before the turkey goes in

# ---- volume puffs (steam white, smoke dark): density from a noise ball; object props dens + ph
def puff_mat(name, col, dark=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (*col, 1)
    co = coord(nt, 'Object'); ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(co, ln.inputs[0])
    fall = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, ln.outputs['Value']), 0.0)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 5.0
    nt.links.new(co, nz.inputs['Vector']); nt.links.new(objattr(nt, 'ph'), nz.inputs['W'])
    d_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', fall, 0.8), math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.32), 0.0)), objattr(nt, 'dens'))
    nt.links.new(math_(nt, 'MULTIPLY', d_, 60.0 if not dark else 40.0), pv.inputs['Density'])
    if dark: pv.inputs['Anisotropy'].default_value = 0.1
    else: pv.inputs['Anisotropy'].default_value = 0.35
    nt.links.new(pv.outputs[0], out.inputs['Volume']); return m
STEAM_M = puff_mat('steam', (0.92, 0.93, 0.95)); SMOKE_M = puff_mat('smoke', (0.05, 0.045, 0.045), True)
class Puffs:
    def __init__(s, name, m, n, seed):
        s.o = []; s.n = n; s.r = random.Random(seed)
        for k in range(n):
            o = prim('ico_sphere', f'{name}{k}', m, scale=(1, 1, 1), subdivisions=2, radius=1.0); o.hide_render = True; o['dens'] = 0.0; o['ph'] = h1(k + seed) * 10; s.o.append(o)
        s.p = [(s.r.random(), s.r.random(), s.r.random(), s.r.random()) for _ in range(n)]
    def update(s, t, src, t0, t1, life, rise, size, spread, dens=1.0, drift=(0, 0, 0)):
        """emit from src(k, u) between t0 and t1, each puff lives `life` s, rises `rise` m/s, grows to `size`"""
        for k, o in enumerate(s.o):
            u0, u1, u2, u3 = s.p[k]; te = t0 + (t1 - t0) * (k + u0 * 0.7) / s.n; age = t - te
            if t1 <= t0 or age < 0 or age > life: o.hide_render = True; continue
            a_ = age / life; o.hide_render = False
            base = Vector(src(k, u1)); o.location = base + Vector(((u2 - 0.5) * spread * a_, (u3 - 0.5) * spread * a_, rise * age)) + Vector(drift) * age
            sc = size * (0.25 + 0.75 * math.sqrt(a_)) * (0.7 + 0.6 * u1); o.scale = (sc, sc, sc * 1.15)
            o['dens'] = dens * smooth(0, 0.15, a_) * (1 - smooth(0.45, 1.0, a_)); o['ph'] = u0 * 10 + age * 0.6

# ---- flame cards: emission over clear, a licking tongue shape from noise; object props amt (0..1), ph, seed
def flame_card_mat(name, strength=7.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    uv = coord(nt, 'Generated'); sx = sepz(nt, uv); x_ = sx.outputs['X']; y_ = sx.outputs['Y']
    cx = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', x_, 0.5))
    width = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, y_), 0.5)                 # narrows to the top
    body = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', cx, math_(nt, 'MAXIMUM', width, 0.02))), 0.0)
    cm = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', x_, 3.0), cm.inputs['X'])
    nt.links.new(math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', y_, 2.2), math_(nt, 'MULTIPLY', objattr(nt, 'ph'), 2.6)), cm.inputs['Y']); nt.links.new(objattr(nt, 'seed'), cm.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.4; nz.inputs['Detail'].default_value = 6.0; nz.inputs['Distortion'].default_value = 0.6
    nt.links.new(cm.outputs[0], nz.inputs['Vector'])
    hmask = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', objattr(nt, 'amt'), y_), 0.0)
    f_ = math_(nt, 'MULTIPLY', math_(nt, 'ADD', math_(nt, 'MULTIPLY', body, 0.55), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.4), 1.6)), math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', hmask, 6.0), 1.0))
    a_ = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', f_, 0.46), 3.2), 0.0), 1.0)
    col = ramp(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', a_, 0.7), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, y_), 0.3)),
               [(0.0, (0.55, 0.05, 0.0)), (0.35, (1.0, 0.28, 0.02)), (0.7, (1.0, 0.62, 0.12)), (1.0, (1.0, 0.92, 0.6))])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(col, em.inputs['Color']); nt.links.new(math_(nt, 'MULTIPLY', a_, strength), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(a_, mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    try: m.cycles.emission_sampling = 'NONE'
    except Exception: pass
    return m
FLAME_M = flame_card_mat('flame', 2.4)
def card(name, base, h, w, yaw, parent=None):
    o = prim('plane', name, FLAME_M, parent, size=1.0)
    for v in o.data.vertices: v.co = Vector(((v.co.x) * w, 0.0, (v.co.y + 0.5) * h))
    o.location = base; o.rotation_euler = (0, 0, yaw); o['amt'] = 0.0; o['ph'] = 0.0; o['seed'] = random.random() * 20; o.hide_render = True
    return o

# ---- the fire volume (fireball): emission + smoke from a stretched noise ball; object props fire, ph
def fire_vol_mat(name, es=220.0, thr=0.44, dens=55.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (0.03, 0.025, 0.02, 1)
    co = coord(nt, 'Object'); sx = sepz(nt, co)
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(co, ln.inputs[0])
    fall = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, ln.outputs['Value']), 0.0), 1.6)
    rise = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sx.outputs['X'], rise.inputs['X']); nt.links.new(sx.outputs['Y'], rise.inputs['Y'])
    nt.links.new(math_(nt, 'SUBTRACT', sx.outputs['Z'], math_(nt, 'MULTIPLY', objattr(nt, 'ph'), 1.4)), rise.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.4; nz.inputs['Detail'].default_value = 8.0; nz.inputs['Distortion'].default_value = 1.0
    nt.links.new(rise.outputs[0], nz.inputs['Vector'])
    d_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', fall, math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], thr), 0.0)), objattr(nt, 'fire'))
    nt.links.new(math_(nt, 'MULTIPLY', d_, dens), pv.inputs['Density'])
    hot = math_(nt, 'MULTIPLY', math_(nt, 'POWER', fall, 0.5), math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], thr - 0.02), 0.0))
    hot = math_(nt, 'MULTIPLY', hot, math_(nt, 'SUBTRACT', 1.15, math_(nt, 'MULTIPLY', math_(nt, 'ADD', sx.outputs['Z'], 1.0), 0.45)))
    col = ramp(nt, math_(nt, 'MULTIPLY', hot, 5.0), [(0.0, (0.35, 0.06, 0.0)), (0.3, (1.0, 0.30, 0.02)), (0.6, (1.0, 0.52, 0.06)), (0.85, (1.0, 0.70, 0.18)), (1.0, (1.0, 0.86, 0.45))])
    nt.links.new(col, pv.inputs['Emission Color']); nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', hot, objattr(nt, 'fire')), es), pv.inputs['Emission Strength'])
    nt.links.new(pv.outputs[0], out.inputs['Volume']); return m
FIREVOL_M = fire_vol_mat('firevol', 330.0, 0.5, 40.0)
def fire_sleeve_mat(name):
    """fire hugging the pot: a ring-shaped density round its side, cut off above the flame front (object prop front, local z)"""
    m = fire_vol_mat(name); nt = m.node_tree; pv = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    co = coord(nt, 'Object'); sx = sepz(nt, co); rr = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sx.outputs['X'], sx.outputs['X']), math_(nt, 'MULTIPLY', sx.outputs['Y'], sx.outputs['Y'])))
    ring = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', rr, 0.62)), 3.2)), 0.0)
    hm = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', objattr(nt, 'front'), sx.outputs['Z']), 3.0), 0.0), 1.0)
    lk = next(l for l in nt.links if l.to_socket == pv.inputs['Density']); src = lk.from_socket; nt.links.remove(lk)
    nt.links.new(math_(nt, 'MULTIPLY', src, math_(nt, 'MULTIPLY', ring, hm)), pv.inputs['Density'])
    lk = next(l for l in nt.links if l.to_socket == pv.inputs['Emission Strength']); src = lk.from_socket; nt.links.remove(lk)
    nt.links.new(math_(nt, 'MULTIPLY', src, math_(nt, 'MULTIPLY', ring, hm)), pv.inputs['Emission Strength'])
    return m
SLEEVE = prim('cylinder', 'fire_sleeve', fire_sleeve_mat('firesleeve'), loc=(0, 0, 0), vertices=48, radius=1.0, depth=2.0)
SLEEVE.location = (0.0, 1.05, DECK_Z + 0.55); SLEEVE.scale = (0.34, 0.34, 0.55); SLEEVE['fire'] = 0.0; SLEEVE['ph'] = 0.0; SLEEVE['front'] = -1.0; SLEEVE.hide_render = True
FIREBALLS = []
for k in range(4):
    o = prim('ico_sphere', f'fireball{k}', FIREVOL_M, subdivisions=3, radius=1.0); o.hide_render = True; o['fire'] = 0.0; o['ph'] = 0.0; FIREBALLS.append(o)

# ---- steam: the flash at the skin, wisps off hot oil; smoke from the roof
STEAM_FLASH = Puffs('stflash', STEAM_M, 18, 3)
STEAM_SURGE = Puffs('stsurge', STEAM_M, 14, 5)
SMOKE = Puffs('smoke', SMOKE_M, 16, 7)
# ---- melt water: drops that run out of the bottom of the bird and sink; the hero drop blows up into a bubble 12x wide (1,700x the space)
DROPS = []
dr = random.Random(11)
for k in range(16):
    o = prim('uv_sphere', f'drop{k}', WATER_M, segments=16, ring_count=10, radius=1.0); o.hide_render = True
    ang = -1.75 + dr.uniform(-1.3, 1.3); rr = dr.uniform(0.128, 0.148)
    DROPS.append(dict(o=o, ang=ang, rr=rr, t0=T_DRIP + 0.25 * k + dr.uniform(0, 0.2), r=dr.uniform(0.0045, 0.0075), wob=dr.uniform(0, 6.28)))
HERO = DROPS[2]; HERO['rr'] = 0.112; HERO['ang'] = -1.75; HERO['r'] = 0.0045
BUBBLES = []
for k in range(40):
    o = prim('uv_sphere', f'bub{k}', STEAMB_M, segments=16, ring_count=10, radius=1.0); o.hide_render = True
    BUBBLES.append(dict(o=o, ang=dr.uniform(0, 6.28), rr=dr.uniform(0.0, 0.15), t0=T_SURGE - 0.2 + dr.uniform(0, 1.6), r=dr.uniform(0.012, 0.035), v=dr.uniform(0.35, 0.7)))
# surface bubbles on the oil (fizz) round the turkey
FIZZ = []
OILB_M = mat('oilbub', (1.0, 0.75, 0.3), 0.05, trans=0.5, ior=1.4)
for k in range(70):
    o = prim('uv_sphere', f'fizz{k}', OILB_M, segments=10, ring_count=6, radius=1.0); o.hide_render = True
    FIZZ.append(dict(o=o, ang=dr.uniform(0, 6.28), rr=dr.uniform(0.08, 0.16), ph=dr.uniform(0, 1), sp=dr.uniform(1.5, 3.5), r=dr.uniform(0.003, 0.009)))
# ---- the boil-over: foam dome over the pot, a sheet of oil running down the outside, streams onto the burner
FOAM_M = mat('foam', (0.98, 0.82, 0.48), 0.25, trans=0.25, ior=1.4, emit=(1.0, 0.6, 0.2), estr=0.05)
nt = FOAM_M.node_tree; vb = nt.nodes.new('ShaderNodeTexVoronoi'); vb.inputs['Scale'].default_value = 90.0; vb.voronoi_dimensions = '4D'
nt.links.new(coord(nt, 'Object'), vb.inputs['Vector']); nt.links.new(objattr(nt, 'ph'), vb.inputs['W'])
bpn = nt.nodes.new('ShaderNodeBump'); bpn.inputs['Strength'].default_value = 0.8; nt.links.new(vb.outputs['Distance'], bpn.inputs['Height']); nt.links.new(bpn.outputs['Normal'], nt.nodes['Principled BSDF'].inputs['Normal'])
FOAM = prim('uv_sphere', 'foam', FOAM_M, segments=48, ring_count=24, radius=1.0)
for v in FOAM.data.vertices:
    if v.co.z < 0: v.co.z = 0.0
dpf = FOAM.modifiers.new('d', 'DISPLACE'); txf = bpy.data.textures.new('foamtx', 'CLOUDS'); txf.noise_scale = 0.25; dpf.texture = txf; dpf.strength = 0.18; dpf.texture_coords = 'OBJECT'
FOAM.hide_render = True; FOAM['ph'] = 0.0
SHEET_M = oil_mat('sheet', 0.0); SHEET_M.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.12
_nt = SHEET_M.node_tree; _gp0 = _nt.nodes.new('ShaderNodeNewGeometry').outputs['Position']
_vs = _nt.nodes.new('ShaderNodeVectorMath'); _vs.operation = 'SUBTRACT'; _nt.links.new(_gp0, _vs.inputs[0]); _vs.inputs[1].default_value = (0.0, 1.05, 0.0); _sx = sepz(_nt, _vs.outputs[0])
_ang = _nt.nodes.new('ShaderNodeMath'); _ang.operation = 'ARCTAN2'; _nt.links.new(_sx.outputs['Y'], _ang.inputs[0]); _nt.links.new(_sx.outputs['X'], _ang.inputs[1])
_cm = _nt.nodes.new('ShaderNodeCombineXYZ'); _nt.links.new(math_(_nt, 'MULTIPLY', _ang.outputs[0], 2.2), _cm.inputs['X']); _nt.links.new(math_(_nt, 'MULTIPLY', _sx.outputs['Z'], 0.35), _cm.inputs['Y'])
_st = tnoise(_nt, _cm.outputs[0], 2.5, 2.0); _al = math_(_nt, 'MINIMUM', math_(_nt, 'MAXIMUM', math_(_nt, 'MULTIPLY', math_(_nt, 'SUBTRACT', _st, 0.55), 9.0), 0.0), 1.0)
_tr = _nt.nodes.new('ShaderNodeBsdfTransparent'); _mx = _nt.nodes.new('ShaderNodeMixShader'); _nt.links.new(_al, _mx.inputs['Fac'])
_nt.links.new(_tr.outputs[0], _mx.inputs[1]); _nt.links.new(_nt.nodes['Principled BSDF'].outputs[0], _mx.inputs[2]); _nt.links.new(_mx.outputs[0], _nt.nodes['Material Output'].inputs['Surface'])
def sheet_mesh():
    segs, rows = 96, 24; vs = []; fs = []
    for i in range(rows + 1):
        for k in range(segs):
            a_ = 2 * math.pi * k / segs; vs.append((math.cos(a_), math.sin(a_), -i / rows))
    for i in range(rows):
        for k in range(segs): k2 = (k + 1) % segs; fs.append((i * segs + k, i * segs + k2, (i + 1) * segs + k2, (i + 1) * segs + k))
    return mesh('oilsheet', vs, fs, SHEET_M)
SHEET = sheet_mesh(); SHEET.hide_render = True
# rivulets: oil running down the outside of the pot in wiggly streams (rebuilt each frame to their current length)
RIV_M = oil_mat('rivulet', 0.05); RIV_M.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.08
RIVS = []
for k in range(11):
    a0 = -2.7 + 2.6 * (k / 10) + 0.15 * h1(k); RIVS.append(dict(a=a0, w=h1(k + 30), sp=0.75 + 0.45 * h1(k + 31), r=0.0035 + 0.004 * h1(k + 32), o=mesh(f'riv{k}', [(0, 0, 0)] * 3, [(0, 1, 2)], RIV_M)))
for rv in RIVS: rv['o'].hide_render = True
def set_tube(o, pts, r, seg=8):
    pts = [Vector(p) for p in pts]; n = len(pts)
    if n < 2: o.hide_render = True; return
    rings = []; T0 = (pts[1] - pts[0]).normalized(); up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized()
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        rr = r(i / (n - 1)) if callable(r) else r
        rings.append([pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
    vs = [tuple(p) for ring in rings for p in ring]; fs = []
    for i in range(n - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    me = o.data; me.clear_geometry(); me.from_pydata(vs, [], fs); me.update()
    for p in me.polygons: p.use_smooth = True
    o.hide_render = False
SHEET_BASE = [Vector(v.co) for v in SHEET.data.vertices]
STREAMS = []
for k in range(7):
    a_ = -1.4 + 0.45 * k + 0.2 * h1(k); STREAMS.append(dict(a=a_, o=None, t0=T_POUR + 0.15 * k + 0.2 * h1(k + 5)))
# ---- fire: cards up the outside of the pot (racing up the oil), cards over the top, a ring on the roof, the fireball volumes, lights
POT_CARDS = []
for k in range(18):
    a_ = 2 * math.pi * k / 18; base = Vector((FX + (PR_ + 0.02) * math.cos(a_), FY + (PR_ + 0.02) * math.sin(a_), DECK_Z + 0.15))
    POT_CARDS.append(card(f'pcard{k}', base, 0.75, 0.24, a_ + math.pi / 2))
TOP_CARDS = []
for k in range(14):
    a_ = math.pi * k / 14; r_ = 0.06 * h1(k)
    TOP_CARDS.append(card(f'tcard{k}', Vector((FX + r_ * math.cos(a_ * 2), FY + r_ * math.sin(a_ * 2), RIM_Z - 0.05)), 1.6, 0.7, a_))
ROOF_CARDS = []
for k in range(24):
    x_ = FX - 1.6 + 3.2 * (k / 23) + 0.1 * h1(k); y_ = FY - 0.9 + 1.6 * h1(k + 3)
    zr = ROOF_Z1 + (ROOF_Z0 - ROOF_Z1) * (y_ - DY0) / (WALL_Y - DY0) + 0.2
    c_ = card(f'rcard{k}', Vector((x_, y_, zr - 0.32)), 0.55, 0.5, h1(k + 8) * 3.14); ROOF_CARDS.append((c_, math.hypot(x_ - FX, y_ - FY)))
FIRE_L = [light_at(f'fire_l{k}', 'POINT', (FX, FY, RIM_Z + 0.3 + 0.5 * k), (FX, FY, 0), 0.0, (1.0, 0.45, 0.12), 0.35) for k in range(3)]
# roof underside burn: char + embers growing out from above the pot
nt = ceil_m.node_tree; bb = nt.nodes['Principled BSDF']
lk = next((l for l in nt.links if l.to_socket == bb.inputs['Base Color']), None); src = lk.from_socket if lk else None
gpos = nt.nodes.new('ShaderNodeNewGeometry').outputs['Position']
dv = nt.nodes.new('ShaderNodeVectorMath'); dv.operation = 'DISTANCE'; nt.links.new(gpos, dv.inputs[0]); dv.inputs[1].default_value = (FX, FY, ROOF_Z1 + 0.3)
burnr = objattr(nt, 'burnr')
ch = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', math_(nt, 'ADD', burnr, math_(nt, 'MULTIPLY', tnoise(nt, gpos, 3.0), 0.5)), dv.outputs['Value']), 3.0), 0.0), 1.0)
basec = src if src else (0.78, 0.76, 0.70)
nt.links.new(mixc(nt, ch, basec, (0.02, 0.015, 0.012)), bb.inputs['Base Color'])
emb = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', ch, math_(nt, 'POWER', tnoise(nt, gpos, 40.0, 3.0), 4.0)), objattr(nt, 'glow'))
bb.inputs['Emission Color'].default_value = (1.0, 0.3, 0.04, 1); nt.links.new(math_(nt, 'MULTIPLY', emb, 60.0), bb.inputs['Emission Strength'])
ROOF_UNDER['burnr'] = 0.0; ROOF_UNDER['glow'] = 0.0
for rf in RAFTERS: rf.data.materials.clear(); rf.data.materials.append(ceil_m); rf['burnr'] = 0.0; rf['glow'] = 0.0
# ================================================================ per frame: the story state, then the one continuous camera
RACK0 = 0.80; RACK_BOT = FRY['pot_z'] - DECK_Z + 0.002          # rack-plate heights (fryer local)
OILL0 = 0.532                                                  # oil top (fryer local) before the turkey
def story(t):
    """state numbers at story time t (t < 0 = just before frame one: the loop's run-in)"""
    st = {}
    st['rack'] = RACK0 - (RACK0 - OILL0 + 0.012) / T_TOUCH * t if t < T_TOUCH else lerp(OILL0 - 0.012, RACK_BOT, smooth(T_TOUCH, B[2] + 0.6, t))
    st['oil'] = OILL0 + 0.07 * smooth(T_TOUCH, B[2] + 0.6, t) + (0.752 - 0.6 - 0.07) * smooth(T_SURGE, T_OVER, t) * (1 - smooth(T_BALL + 2.0, T_BALL + 5, t)) * 1.0
    st['frost'] = 1.0 - smooth(T_TOUCH, T_TOUCH + 1.3, t)
    st['boil'] = 0.15 + 0.85 * math.exp(-max(0.0, t - T_TOUCH) * 0.9) * (t > T_TOUCH) + 0.25 * (t > T_TOUCH) + 0.6 * smooth(T_SURGE - 0.3, T_SURGE + 0.4, t)
    st['xr'] = smooth(T_XR0 - 0.3, T_XR0 + 0.4, t) * (1 - smooth(T_XR1 - 0.4, T_XR1 + 0.3, t))
    st['ice'] = 1.0 - 0.6 * smooth(T_MELT - 0.5, T_SINK + 1.5, t)
    st['foam'] = smooth(T_SURGE + 0.2, T_OVER, t) * (1 - smooth(T_BALL + 1.5, T_BALL + 3.5, t))
    st['sheet'] = smooth(T_OVER - 0.2, T_HIT + 0.2, t)
    st['catch'] = smooth(T_CATCH - 0.15, T_CATCH + 0.4, t)
    st['race'] = smooth(T_CATCH + 0.1, T_RACE + 1.0, t)
    st['ball'] = smooth(T_BALL - 0.3, T_BALL + 0.9, t)
    st['roof'] = smooth(T_ROOF - 0.4, T_ROOF + 3.5, t) + 0.25 * smooth(T_ROOF + 3.5, END, t)
    st['let_go'] = smooth(T_SURGE - 0.15, T_SURGE + 0.25, t)
    st['back'] = 0.55 * smooth(T_SURGE - 0.1, T_SURGE + 0.7, t) + 0.9 * smooth(T_BALL - 0.2, T_BALL + 1.2, t)
    return st

def place_drop(d, t, st):
    o = d['o']; r0 = d['r']
    if t < d['t0'] or t > T_SURGE + 1.2 or st['xr'] < 0.02 and t < T_SURGE - 0.5: o.hide_render = True; return
    o.hide_render = False
    c = Vector((FX + d['rr'] * math.cos(d['ang']), FY + d['rr'] * math.sin(d['ang']), 0))
    top = DECK_Z + st['rack'] + 0.09 + 0.16 * h1(d['wob'] * 7); age = t - d['t0']
    z = top - 0.05 * age - 0.06 * age * age; z = max(z, FLOOR_Z + r0 * 0.8)
    c0 = Vector((FX + 0.112 * math.cos(d['ang']), FY + 0.112 * math.sin(d['ang']), 0)); c = c0.lerp(c, min(1.0, age * 1.5))
    shiv = smooth(T_212 - 0.3, T_212 + 0.4, t) * 0.0015
    p = Vector((c.x + shiv * math.sin(t * 61 + d['wob']), c.y + shiv * math.cos(t * 53 + d['wob']), z))
    r = r0 * (1 + 0.15 * shiv * 400 * abs(math.sin(t * 40 + d['wob'])))
    if d is HERO and t > T_POP:
        g = smooth(T_POP, T_POP + 1.0, t); r = lerp(r0, r0 * 12.0, g)                       # 12x wider = ~1,700x the space
        lift = 0.55 * max(0.0, t - (T_1700 + 0.7)) ** 1.6; p.z = FLOOR_Z + r * 0.92 + lift
        if p.z > DECK_Z + st['oil'] - r * 0.5: o.hide_render = True; return
        if o.material_slots[0].material != STEAMB_M: o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = STEAMB_M
    elif t > T_SURGE - 0.1 and d is not HERO:
        g = smooth(T_SURGE - 0.1, T_SURGE + 0.4, t); r = lerp(r0, r0 * 7.0, g); p.z = FLOOR_Z + r + 1.1 * max(0.0, t - T_SURGE - 0.1) ** 1.3
        if o.material_slots[0].material != STEAMB_M: o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = STEAMB_M
        if p.z > DECK_Z + st['oil']: o.hide_render = True; return
    else:
        if o.material_slots[0].link == 'OBJECT': o.material_slots[0].material = WATER_M
    v_ = Vector((p.x - FX, p.y - FY, 0)); lim = PR_ - 0.008 - r
    if v_.length > lim: v_ = v_.normalized() * max(lim, 0.0); p = Vector((FX + v_.x, FY + v_.y, p.z))
    o.location = p; o.scale = (r, r, r * (0.92 if z <= FLOOR_Z + r0 else 1.08))

def state(t):
    st = story(t)
    # turkey + rack + oil
    FRY['rack'].location = (0, 0, st['rack']); TK = FRY['turkey']; TK['frost'] = st['frost']; TK['xr'] = st['xr']
    FRY['pot']['xr'] = st['xr'] * 0.92
    FRY['oiltop'].location = (0, 0, st['oil']); FRY['oiltop']['boil'] = 0.04 + 0.5 * st['boil']; FRY['oiltop']['ph'] = t * 0.7
    body = FRY['oilbody']; body.hide_render = st['xr'] < 0.02; hb = (st['oil'] - (FRY['pot_z'] - DECK_Z + 0.006)); body.scale = (PR_ - 0.006, PR_ - 0.006, hb / 2)
    body.location = (0, 0, FRY['pot_z'] - DECK_Z + 0.006 + hb / 2)
    ice = FRY['ice']; ice.hide_render = st['xr'] < 0.05; s_ = st['ice']; ice.scale = (0.085 * s_, 0.07 * s_, 0.11 * s_)
    # the hook: held, then let go -> it tips onto the rim
    FRY['hook'].rotation_euler = (0, R(-22) * st['let_go'], 0)
    # fizz on the surface
    oz = DECK_Z + st['oil']; bo = st['boil']
    for k, b_ in enumerate(FIZZ):
        on = bo > 0.18 and (k / len(FIZZ)) < bo * 0.9 and t < T_BALL + 2.5
        if not on: b_['o'].hide_render = True; continue
        u = (t * b_['sp'] + b_['ph']) % 1.0; a_ = b_['ang'] + 0.3 * math.sin(t + k)
        b_['o'].hide_render = False; b_['o'].location = (FX + b_['rr'] * math.cos(a_), FY + b_['rr'] * math.sin(a_), oz + 0.002)
        r = b_['r'] * math.sin(math.pi * u) * (0.6 + 0.6 * bo); b_['o'].scale = (r, r, r * 0.6)
    # steam: the flash off the frozen skin, then the boil-over cloud
    STEAM_FLASH.update(t, lambda k, u: (FX + 0.14 * math.cos(k * 2.4), FY + 0.14 * math.sin(k * 2.4), oz + 0.02), T_TOUCH - 0.1, T_TOUCH + 1.6, 2.2, 0.35, 0.16, 0.25, 0.9)
    STEAM_SURGE.update(t, lambda k, u: (FX + 0.1 * math.cos(k * 1.7), FY + 0.1 * math.sin(k * 1.7), DECK_Z + 0.78), T_SURGE, T_CATCH, 2.0, 0.45, 0.24, 0.4, 1.0)
    for d in DROPS: place_drop(d, t, st)
    for b_ in BUBBLES:
        o = b_['o']; age = t - b_['t0']
        if age < 0 or t > T_BALL + 1 or t < T_SURGE - 0.4: o.hide_render = True; continue
        z = FLOOR_Z + b_['r'] + b_['v'] * age ** 1.2
        if z > oz - 0.01: o.hide_render = True; continue
        o.hide_render = False; r = b_['r'] * (1 + 1.5 * min(age, 1.0)); rr = min(b_['rr'], PR_ - 0.008 - r)
        o.location = (FX + rr * math.cos(b_['ang']), FY + rr * math.sin(b_['ang']), z); o.scale = (r, r, r * 1.1)
    # foam dome + the sheet down the outside + the pour onto the burner
    FOAM.hide_render = st['foam'] < 0.02
    if not FOAM.hide_render:
        f_ = st['foam']; FOAM.location = (FX, FY, oz - 0.01); FOAM.scale = (PR_ + 0.02 * f_, PR_ + 0.02 * f_, 0.02 + 0.13 * f_); FOAM['ph'] = t * 1.5
    SHEET.hide_render = True
    for k, rv in enumerate(RIVS):
        prog = clamp(st['sheet'] * rv['sp'] * 1.15 - 0.1 * rv['w'], 0, 1)
        if prog < 0.02: rv['o'].hide_render = True; continue
        L_ = (PH_ + 0.01) * prog; n_ = max(3, int(24 * prog)); pts = []
        for i in range(n_):
            u = i / (n_ - 1); z = RIM_Z + 0.004 - L_ * u; a_ = rv['a'] + 0.05 * math.sin(z * 40 + rv['w'] * 6) + 0.02 * math.sin(z * 97)
            rr = PR_ + 0.003 + (0.012 if z > RIM_Z - 0.01 else 0.0)
            pts.append((FX + rr * math.cos(a_), FY + rr * math.sin(a_), z))
        set_tube(rv['o'], pts, lambda u, r0=rv['r']: r0 * (1.2 - 0.5 * u + 0.4 * max(0, u - 0.92) * 10), seg=8)
    for k, sm_ in enumerate(STREAMS):
        if sm_['o'] is None:
            sm_['o'] = tube(f'stream{k}', [(0, 0, 0), (0, 0, -0.5), (0, 0, -1.0)], lambda u: 0.0045 * (1 - 0.5 * u), SHEET_M, seg=8)
        o = sm_['o']; on = t > sm_['t0'] and t < T_BALL + 4.0
        o.hide_render = not on
        if on:
            ln = min(1.0, (t - sm_['t0']) * 2.2) * (FRY['pot_z'] - DECK_Z - 0.02); a_ = sm_['a']
            o.location = (FX + (PR_ + 0.004) * math.cos(a_), FY + (PR_ + 0.004) * math.sin(a_), FRY['pot_z']); o.scale = (1, 1, max(ln, 0.001))
    # burner jets flicker (and in the safe fryer)
    for F_ in (FRY, SAFE):
        for k, j in enumerate(F_['jets']):
            j['ja'] = 0.85 + 0.15 * math.sin(t * 37 + k * 2.1); j.scale = (0.008, 0.008, 0.03 * (0.85 + 0.25 * wob(t, 9, k)))
        F_['burnlight'].data.energy = 16 * (0.85 + 0.15 * wob(t, 7, 1))
    SAFE['oiltop']['boil'] = 0.25; SAFE['oiltop']['ph'] = t * 0.5; SAFE['rack'].location = (0, 0, RACK_BOT); SAFE['oiltop'].location = (0, 0, OILL0 + 0.07)
    # fire
    ca, ra, ba = st['catch'], st['race'], st['ball']
    front = 0.12 + 1.0 * ra                                            # height of the flame front up the pot side (m above the deck)
    for c_ in POT_CARDS + TOP_CARDS: c_.hide_render = True
    for c_, _d in ROOF_CARDS: c_.hide_render = True
    SLEEVE.hide_render = ca < 0.02; SLEEVE['fire'] = ca * (0.6 + 0.4 * ra) + 0.5 * ba; SLEEVE['ph'] = t * 1.1
    SLEEVE['front'] = -1.0 + 2.0 * min(1.0, (front + 0.25 * ba) / 0.96)
    for k, fb in enumerate(FIREBALLS):
        g = ba * (1.0 if k < 2 else st['roof']); fb.hide_render = g < 0.02; fb['fire'] = g; fb['ph'] = t * (0.9 + 0.2 * k)
        if k == 0: fb.location = (FX, FY, RIM_Z + 0.25 + 0.2 * ba); fb.scale = (0.4 + 0.3 * ba, 0.4 + 0.3 * ba, 0.5 + 0.45 * ba)
        elif k == 1: fb.location = (FX, FY - 0.05, RIM_Z + 0.75 + 0.45 * ba); fb.scale = (0.45 + 0.45 * ba, 0.45 + 0.45 * ba, 0.55 + 0.5 * ba)
        elif k == 2: fb.location = (FX, FY - 0.2, ROOF_Z1 + 0.05); fb.scale = (0.6 + 0.9 * st['roof'], 0.6 + 0.5 * st['roof'], 0.28)
        else: fb.location = (FX + 0.4, DY0 - 0.2, ROOF_Z1 + 0.6); fb.scale = (0.5 + 0.6 * st['roof'], 0.4, 0.5 + 0.4 * st['roof'])
    rf = st['roof']
    for o in [ROOF_UNDER] + RAFTERS: o['burnr'] = 1.8 * min(rf, 1.0) + 0.6 * max(rf - 1, 0) - 0.05; o['glow'] = min(1.0, rf * 1.5)
    for c_, dist in ROOF_CARDS:
        amt = smooth(dist - 0.2, dist + 0.3, 1.8 * rf); c_.hide_render = amt < 0.02; c_['amt'] = amt * (0.8 + 0.2 * wob(t, 3, dist)); c_['ph'] = t + c_['seed']
    SMOKE.update(t, lambda k, u: (FX - 1.2 + 2.4 * u, DY0 - 0.35, ROOF_Z1 + 0.3), T_ROOF, END + 3, 4.5, 0.55, 0.9, 0.8, 0.8, (0.08, -0.05, 0))
    flick = 0.75 + 0.25 * wob(t, 6, 2)
    FIRE_L[0].data.energy = (25 * ca + 90 * ra + 320 * ba) * flick; FIRE_L[0].location = (FX, FY - 0.25, DECK_Z + 0.4 + 0.5 * ra + 0.6 * ba)
    FIRE_L[1].data.energy = 450 * ba * flick; FIRE_L[1].location = (FX, FY - 0.3, RIM_Z + 0.9)
    FIRE_L[2].data.energy = 380 * min(rf, 1.0) * flick; FIRE_L[2].location = (FX, FY - 0.5, ROOF_Z1 - 0.2)
    # the man: hands on the T-handle while he lowers it; lets go, flinches back, backs away arms up
    lg = st['let_go']; bk = st['back']
    MAN.location = (-0.98 - bk, 1.08 + 0.15 * smooth(T_BALL, T_BALL + 1.2, t), DECK_Z)
    bpy.context.view_layer.update()
    hk = FRY['hook'].matrix_world
    want = {}
    for s_, dy in (('R', -0.06), ('L', 0.06)):
        bar = hk @ Vector((-0.44, dy, 0.11))
        tgt = grip(s_, bar, 1.0 - lg)
        want[s_] = bar + Vector((0, 0, 0.026))                          # knuckle line just over the bar
        up = man_world((0.3 if s_ == 'L' else -0.3, -0.42, 1.62))     # arms up in front of the face
        TG['h' + s_].location = tgt.lerp(up, lg)
        TG['p' + s_].location = man_world((0.75 if s_ == 'L' else -0.75, 0.25, 1.0))
        fingers(s_, 1.0 - 0.8 * lg)
    stepb = smooth(T_SURGE - 0.1, T_SURGE + 0.5, t) * (1 - smooth(T_SURGE + 0.5, T_SURGE + 1.0, t)) + smooth(T_BALL - 0.2, T_BALL + 0.4, t) * (1 - smooth(T_BALL + 0.4, T_BALL + 1.0, t))
    man_pose(spine=18 * (1 - lg) - 14 * lg, neck=15 * (1 - lg) - 10 * lg, head=12 * (1 - lg) - 6 * lg, head_yaw=-25 * smooth(T_BALL + 1, T_BALL + 2, t),
         legs={'upperleg01.R': (R(28 * stepb), 0, 0), 'lowerleg01.R': (R(35 * stepb), 0, 0), 'upperleg01.L': (R(-8 * stepb), 0, 0)})
    grip_fix(want, 1.0 - lg)

# ---- camera: (time, position, target, lens); rests on each beat, one unbroken move
POT_C = Vector((FX, FY, 0)); ZR = RIM_Z
def potp(dx, dy, z): return (FX + dx, FY + dy, z)
K = [
    (0.0, potp(0.60, -0.78, ZR + 0.22), potp(-0.02, 0.0, ZR + 0.04), 32),
    (T_TOUCH + 0.3, potp(0.52, -0.64, ZR + 0.14), potp(-0.02, 0.0, ZR - 0.06), 34),
    (B[2] - 0.2, potp(0.48, -0.60, ZR + 0.10), potp(-0.02, 0.0, ZR - 0.10), 34),
    (B[2] + 1.2, potp(0.30, -0.62, ZR - 0.16), potp(0.0, 0.0, ZR - 0.22), 36),          # into the meat (x-ray): the ice core
    (B[3] - 0.4, potp(0.30, -0.60, ZR - 0.18), potp(0.0, 0.0, ZR - 0.24), 36),
    (B[3] + 1.0, potp(0.24, -0.62, ZR - 0.28), potp(0.0, -0.03, ZR - 0.30), 34),        # the melt water running out
    (B[4] - 0.3, potp(0.24, -0.62, ZR - 0.29), potp(0.0, -0.03, ZR - 0.31), 34),
    (B[4] + 1.0, potp(0.22, -0.60, ZR - 0.34), potp(0.0, -0.06, ZR - 0.38), 34),        # sinking to the floor
    (B[5] - 0.3, potp(0.22, -0.60, ZR - 0.35), potp(0.0, -0.06, ZR - 0.39), 34),
    (B[5] + 1.0, potp(0.24, -0.62, ZR - 0.50), potp(0.0, -0.06, ZR - 0.44), 34),        # under: the flame right below the floor
    (B[6] - 0.3, potp(0.24, -0.62, ZR - 0.50), potp(0.0, -0.06, ZR - 0.44), 34),
    (T_POP + 0.2, potp(0.10, -0.42, ZR - 0.37), potp(0.112 * math.cos(-1.75), 0.112 * math.sin(-1.75), ZR - 0.38), 40),     # the bubble
    (B[7] - 0.2, potp(0.12, -0.46, ZR - 0.34), potp(0.08, -0.08, ZR - 0.34), 40),
    (T_OVER - 0.2, potp(0.62, -0.78, ZR + 0.22), potp(0.0, 0.0, ZR - 0.02), 30),        # out: foaming over the top
    (B[8] + 0.2, potp(0.62, -0.78, ZR + 0.18), potp(0.0, 0.0, ZR - 0.08), 30),
    (T_HIT + 0.3, potp(0.55, -0.62, DECK_Z + 0.30), potp(0.0, 0.0, DECK_Z + 0.28), 30),  # down the side to the burner
    (T_CATCH + 0.2, potp(0.55, -0.62, DECK_Z + 0.30), potp(0.0, 0.0, DECK_Z + 0.30), 30),
    (T_RACE + 1.0, potp(0.85, -0.95, ZR + 0.15), potp(0.0, 0.0, ZR - 0.05), 28),        # up with the flames
    (T_BALL + 1.6, (1.7, -2.1, 2.25), (0.0, 1.15, 1.55), 26),                            # wide: the fireball and the roof, over the railing
    (B[11] + 0.4, (1.85, -2.4, 2.3), (0.0, 1.2, 1.6), 26),
    (B[12] - 0.3, (2.0, -2.7, 2.35), (0.0, 1.2, 1.65), 26),
    (T_SAFE + 1.6, (2.75, -6.55, 1.05), (3.6, -8.6, 0.62), 32),                          # out on the lawn: the right way
    (B[13] + 0.9, (2.8, -6.6, 1.02), (3.6, -8.6, 0.6), 32),
    (END - 0.75, (1.15, -1.35, 1.82), (0.0, 1.05, 1.25), 30),                           # over the railing on the way back in
    (END, None, None, 32),
]
K[-1] = (END, K[0][1], K[0][2], K[0][3])
KT = [k[0] for k in K]
def cam_at(t):
    i = max(j for j in range(len(K)) if KT[j] <= t) if t < END else len(K) - 2
    i = min(i, len(K) - 2); a_, b_ = K[i], K[i + 1]; u = sm(clamp((t - a_[0]) / max(b_[0] - a_[0], 1e-6), 0, 1))
    p = Vector(a_[1]).lerp(Vector(b_[1]), u); q = Vector(a_[2]).lerp(Vector(b_[2]), u); ln = lerp(a_[3], b_[3], u)
    return p, q, ln
def frame(f):
    t = f / FPS; tt = t if t < T_RESET else t - END
    state(tt)
    cp, ct, ln = cam_at(t)
    look(cp + shake(t, 0.004, 1.3, 1.1) * (1 + 2.5 * smooth(T_BALL - 0.2, T_BALL + 0.6, t) * (1 - smooth(T_BALL + 1.5, T_BALL + 3, t))), ct, ln, fstop=16.0)
    bloom(0.35 + 0.35 * smooth(T_CATCH, T_BALL, t) * (t < T_RESET), 1.1)
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

