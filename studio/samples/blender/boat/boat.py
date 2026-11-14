# Tanker hits a docked riverboat in New Orleans (Nov 13 2026), Blender Cycles, ONE continuous camera move (no cuts).
# The Atlantic Asphalt tanker loses steering below the Crescent City Connection and hits the American Heritage paddlewheeler's
# river side; the bow goes into the dining room, the boat floods, leans, rolls onto its side; people in life jackets, rescuers. No gore.
#   python3 boat.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n45/boat', n)) if os.path.exists(p_))
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

# ================================================================ the set: river, wharf, port building, city, the Crescent City Connection
# World axes: the river runs along x (current toward -x), the wharf face is the line y = 20 (land is y > 20), water is z = 0.
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_HIT = word_t(3, 2) + 0.05                     # "smashes"
T_SHAKE = word_t(4, 4)                          # "shake"
T_POUR = word_t(5, 5)                           # "pouring"
T_LEAN = word_t(6, 4)                           # "starts to lean"
T_ROLL = word_t(9, 2)                           # "rolls over"
T_JUMP = word_t(10, 1)                          # "jump"
T_POLICE = word_t(8, 7)                         # "police"

# ---- sky: a clear November noon over the river, sun high in the south-west
_wn = W_.node_tree; WBG.inputs['Strength'].default_value = 1.0
_sky = ramp(_wn, sepz(_wn, coord(_wn, 'Generated')).outputs['Z'], [(0.0, (0.55, 0.62, 0.70)), (0.5, (0.62, 0.72, 0.85)), (0.53, (0.42, 0.58, 0.82)), (1.0, (0.16, 0.33, 0.66))])
_wn.links.new(_sky, WBG.inputs['Color'])
SUN = light_at('sun', 'SUN', (0, 0, 100), (60, 90, 0), 4.2, (1.0, 0.95, 0.86), 0.02)
SUN.data.angle = R(1.2)

# ---- the river: brown-green Mississippi water with moving chop (noise in 4D: w = time), deeper colour far out
def river_mat():
    m = bpy.data.materials.new('river'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.13, 0.11, 0.06, 1); b.inputs['Roughness'].default_value = 0.06; b.inputs['Specular IOR Level'].default_value = 0.6
    co = coord(nt, 'Object'); w_ = objattr(nt, 'tw')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.62
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 2.2, 1.0); nt.links.new(co, mp.inputs['Vector']); nt.links.new(mp.outputs[0], nz.inputs['Vector'])
    nt.links.new(w_, nz.inputs['W'])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.35; bm.inputs['Distance'].default_value = 0.25
    nt.links.new(nz.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    # muddy colour streaks
    nz2 = tnoise(nt, co, 0.02, 3.0); c_ = mixc(nt, nz2, (0.16, 0.13, 0.07), (0.09, 0.09, 0.05)); nt.links.new(c_, b.inputs['Base Color'])
    return m
RIVER_M = river_mat()
RIVER = prim('plane', 'river', RIVER_M, loc=(0, -300, 0), size=1, scale=(3000, 700, 1)); RIVER['tw'] = 0.0
for p in RIVER.data.polygons: p.use_smooth = False
FAR_SHORE = box('farshore', (3000, 300, 6), (0, -800, 2), mat('levee', (0.20, 0.27, 0.12), 0.9))
for i in range(60):                                                     # tree line on the west bank
    x_ = -1400 + i * 48 + h1(i) * 20
    prim('ico_sphere', f'ftree{i}', mat(f'ft{i}', (0.10 + 0.05 * h1(i + 3), 0.20 + 0.06 * h1(i + 4), 0.08), 0.9), loc=(x_, -680 - 30 * h1(i + 9), 12), scale=(18, 14, 12), subdivisions=2)

# ---- the wharf: concrete deck on piles at y 20..80, black rubber fenders on its face, yellow edge line, bollards
CONC = noisy(mat('concrete', (0.36, 0.35, 0.32), 0.85), 2.0, 0.18)
WHARF = box('wharf', (420, 70, 3.6), (0, 55, 1.6), CONC)
box('wharf_face', (420, 0.6, 5.0), (0, 20.3, 0.9), noisy(mat('wharf_face', (0.30, 0.29, 0.26), 0.9), 1.5, 0.3))
BLACK_RUB = mat('rubber', (0.025, 0.025, 0.025), 0.75)
for i in range(30):
    box(f'fender{i}', (1.6, 1.2, 3.2), (-200 + i * 14, 19.95, 1.4), BLACK_RUB, bv=0.3)
YEL = mat('yellow', (0.85, 0.65, 0.05), 0.6)
box('edge_line', (420, 0.35, 0.02), (0, 21.0, 3.41), YEL)
for i in range(22):
    if abs(-180 + i * 17 - 6) < 3: continue                              # leave the gangway's landing clear
    lathe(f'bollard{i}', [(0.0, 0), (0.32, 0), (0.32, 0.55), (0.45, 0.65), (0.0, 0.7)], 16, mat(f'bol{i}', (0.06, 0.06, 0.07), 0.5, 0.6), loc=(-180 + i * 17, 21.8, 3.4))
# the gangway: a ramp from the wharf to the riverboat's main deck door (starboard side)
GANG_M = mat('gangway', (0.70, 0.71, 0.72), 0.35, 0.8)
_ga = math.atan2(0.88, 4.1); GANG = box('gangway', (2.6, 4.25, 0.2), (6, 20.45, 3.97), GANG_M, rot=(-_ga, 0, 0))
for sx in (-1.25, 1.25):
    box(f'gang_rail{sx}', (0.08, 4.25, 0.08), (6 + sx, 20.45, 4.97), GANG_M, rot=(-_ga, 0, 0))
    for k in range(4):
        yk = 18.6 + 1.25 * k; zk = 4.3 + 0.2 - 0.88 * (yk - 18.4) / 4.1
        box(f'gang_post{sx}{k}', (0.06, 0.06, 0.95), (6 + sx, yk, zk + 0.45), GANG_M)
# the Port NOLA building and the warehouses behind the wharf
def windows_mat(name, wall, glass, rows=0.42, cols=0.33):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    co = coord(nt, 'Object'); sx = sepz(nt, co)
    u = math_(nt, 'FRACT', math_(nt, 'MULTIPLY', math_(nt, 'ADD', sx.outputs['X'], sx.outputs['Y']), cols))
    v = math_(nt, 'FRACT', math_(nt, 'MULTIPLY', sx.outputs['Z'], rows))
    win = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.12), 0.0)
    win = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.36), math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', v, 0.5)), 0.3))
    nt.links.new(mixc(nt, win, wall, glass), b.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.8; rr.inputs['To Max'].default_value = 0.08; nt.links.new(win, rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], b.inputs['Roughness']); return m
PORT_BLDG = box('port_bldg', (70, 30, 24), (30, 110, 12), windows_mat('portb', (0.78, 0.76, 0.70), (0.12, 0.20, 0.28)))
box('port_roof', (72, 32, 1), (30, 110, 24.5), mat('roof', (0.35, 0.36, 0.38), 0.6))
for i, (x_, w_, h_) in enumerate([(-120, 90, 12), (-30, 60, 10), (110, 80, 14), (200, 70, 11), (-200, 60, 12)]):
    box(f'whse{i}', (w_, 40, h_), (x_, 70 + 20 * (i % 2), h_ / 2 + 3.4), mat(f'wh{i}', (0.55 + 0.1 * h1(i), 0.52, 0.48), 0.8))
# the city behind: towers of the CBD upriver past the bridge
for i in range(26):
    x_ = -560 + i * 34 + 15 * h1(i + 20); hgt = 40 + 160 * h1(i + 40) ** 1.6
    box(f'tower{i}', (24 + 10 * h1(i), 24, hgt), (x_, 380 + 120 * h1(i + 60), hgt / 2), windows_mat(f'tw{i}', (0.62 + 0.15 * h1(i + 7), 0.62, 0.64), (0.14, 0.22, 0.32)))
for i in range(40):
    x_ = -900 + i * 45; y_ = 160 + 160 * h1(i + 80)
    prim('ico_sphere', f'ctree{i}', mat(f'ct{i}', (0.12, 0.24 + 0.05 * h1(i), 0.09), 0.9), loc=(x_, y_, 10), scale=(12, 12, 10), subdivisions=2)

# ---- the Crescent City Connection: twin cantilever truss bridges across the river upstream (x ~ -330), grey steel
STEEL_G = mat('bridge_steel', (0.50, 0.53, 0.56), 0.45, 0.7)
def bridge(x0, name):
    ys = [-780 + 20 * i for i in range(int(1300 / 20) + 1)]
    def top(y): return 52 + 58 * math.exp(-((y + 330) / 150) ** 2) + 58 * math.exp(-((y - 60) / 150) ** 2) - 10 * math.exp(-((y + 135) / 80) ** 2)
    for sx in (-7, 7):
        tube(f'{name}_bot{sx}', [(x0 + sx, y, 46) for y in ys], 0.9, STEEL_G, seg=8)
        tube(f'{name}_top{sx}', [(x0 + sx, y, top(y)) for y in ys], 0.9, STEEL_G, seg=8)
        for i, y in enumerate(ys[:-1]):
            tube(f'{name}_v{sx}_{i}', [(x0 + sx, y, 46), (x0 + sx, y, top(y))], 0.45, STEEL_G, seg=6)
            y2 = ys[i + 1]; tube(f'{name}_d{sx}_{i}', [(x0 + sx, y, 46), (x0 + sx, y2, top(y2))] if i % 2 else [(x0 + sx, y, top(y)), (x0 + sx, y2, 46)], 0.4, STEEL_G, seg=6)
    box(f'{name}_deck', (15, 1300, 1.2), (x0, -130, 46.5), mat(f'{name}_dm', (0.30, 0.30, 0.32), 0.7))
    for yt in (-330, 60):
        for sx in (-7, 7):
            tube(f'{name}_pier{yt}{sx}', [(x0 + sx, yt, -2), (x0 + sx, yt, 46)], 2.2, CONC, seg=10)
bridge(-330, 'ccc_a'); bridge(-362, 'ccc_b')

# ================================================================ the ships
def loft(name, stations, m, parent=None, seg=24, cap_top=True):
    """stations: list of (x, half_breadth, keel_z, deck_z, boxiness n). Section: superellipse, deck edge to keel to deck edge."""
    vs = []; fs = []; K = seg + 1
    for (x_, b_, kz, dz, n_) in stations:
        for k in range(K):
            th = math.pi * k / seg; c_, s_ = math.cos(th), math.sin(th)
            y_ = b_ * math.copysign(abs(c_) ** (2 / n_), c_); z_ = dz - (dz - kz) * abs(s_) ** (2 / n_)
            vs.append((x_, y_, z_))
    for i in range(len(stations) - 1):
        for k in range(seg): fs.append((i * K + k, i * K + k + 1, (i + 1) * K + k + 1, (i + 1) * K + k))
    if cap_top:
        fs.append(tuple(i * K for i in range(len(stations))) + tuple(i * K + seg for i in range(len(stations)))[::-1])
    fs.append(tuple(range(K))[::-1]); fs.append(tuple((len(stations) - 1) * K + k for k in range(K)))
    return mesh(name, vs, fs, m, parent)

def hull_paint(name, top, boot, below, waterline=0.4, deck_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    z_ = sepz(nt, coord(nt, 'Object')).outputs['Z']
    c_ = mixc(nt, math_(nt, 'GREATER_THAN', z_, waterline), mixc(nt, math_(nt, 'GREATER_THAN', z_, waterline - 2.5), below, boot), top)
    nz = tnoise(nt, coord(nt, 'Object'), 0.6, 6.0)                       # streaks and wear
    c_ = mixc(nt, math_(nt, 'MULTIPLY', nz, 0.25), c_, (0.25, 0.18, 0.12)); nt.links.new(c_, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55; b.inputs['Metallic'].default_value = 0.3; return m

# ---- the Atlantic Asphalt: ~160 m asphalt tanker, black hull, red bottom, green deck, white house aft. Origin = stem at the waterline.
TK = empty('tanker')
_TL = 160.0
def tk_station(x_):
    """x_ from the stem (0) aft (negative)"""
    u = -x_
    if u < 28: b_ = 12.4 * (math.sin(math.pi / 2 * u / 28)) ** 0.75 + 0.25; n_ = 1.6 + 3.0 * u / 28
    elif u > _TL - 14: b_ = 12.4 - 3.0 * ((u - (_TL - 14)) / 14) ** 2; n_ = 4.6
    else: b_ = 12.4; n_ = 6.0
    deck = 6.5 + 3.0 * max(0, 1 - u / 22) ** 2 + 1.2 * max(0, (u - (_TL - 30)) / 30)
    keel = -8.0 + 6.5 * max(0, 1 - u / 9) ** 1.5
    return (x_ + (0.0 if u > 9 else 0.0), b_, keel, deck, n_)
stns = [tk_station(-u) for u in [0, 0.6, 1.5, 3, 5, 8, 12, 17, 23, 28, 40, 70, 100, 130, 146, 152, 156, 160]]
# rake: the stem leans forward at the top (the deck edge at the stem is ahead of the waterline point)
TK_HULL = loft('tk_hull', stns, hull_paint('tk_paint', (0.035, 0.20, 0.10), (0.45, 0.06, 0.05), (0.40, 0.07, 0.05), waterline=0.9), TK, seg=28)
for v in TK_HULL.data.vertices:
    if v.co.x > -12: v.co.x += 0.16 * max(0.0, v.co.z) * max(0, 1 + v.co.x / 12)
GREEN_DECK = mat('tk_deck', (0.17, 0.30, 0.20), 0.75)
for (x0, x1) in ((-150, -26),):
    box('tk_deck', (x1 - x0, 24.2, 0.3), ((x0 + x1) / 2, 0, 6.55), GREEN_DECK, parent=TK)
WHITE_P = noisy(mat('white_paint', (0.82, 0.82, 0.80), 0.5), 3.0, 0.08)
# the house aft: five levels, bridge windows all round, wings
for lv in range(5):
    w_ = 21 - lv * 1.0; ln = 18 - lv * 1.2
    box(f'tk_house{lv}', (ln, w_, 2.9), (-146 + ln / 2 - 3, 0, 8.5 + lv * 2.9), WHITE_P, bv=0.1, parent=TK)
TK_GLASS = mat('tk_glass', (0.05, 0.08, 0.10), 0.05, 0.0)
box('tk_bridge_win', (13.3, 17.1, 1.3), (-142.4, 0, 20.9), TK_GLASS, parent=TK)
box('tk_wings', (4, 25.0, 0.4), (-139.0, 0, 20.0), WHITE_P, parent=TK)
FUN = box('tk_funnel', (6, 5, 9), (-144, 0, 26.0), mat('funnel', (0.06, 0.06, 0.07), 0.5), bv=0.6, parent=TK)
box('tk_funnel_band', (6.1, 5.1, 1.6), (-144, 0, 28.5), mat('fband', (0.60, 0.08, 0.05), 0.5), bv=0.6, parent=TK)
box('tk_mast', (0.6, 0.6, 8), (-138.5, 0, 25.5), WHITE_P, parent=TK)
# deck: pipes along the length, the manifold midships, a fore mast, asphalt heating trunk
PIPE_M = mat('pipe', (0.30, 0.34, 0.30), 0.5, 0.5)
def tk_deck_z(u): return 6.5 + 3.0 * max(0, 1 - u / 22) ** 2 + 1.2 * max(0, (u - (_TL - 30)) / 30)
for yy in (-4.4, -3.6, 3.6, 4.4):
    tube(f'tk_pipe{yy}', [(-128, yy, 6.85), (-26, yy, 6.85)], 0.28, PIPE_M, TK, seg=8)
    for k in range(9): box(f'tk_pipe_sup{yy}{k}', (0.3, 0.3, 0.35), (-125 + 12 * k, yy, 6.7), PIPE_M, parent=TK)
box('tk_trunk', (100, 6, 1.2), (-80, 0, 7.3), GREEN_DECK, bv=0.2, parent=TK)
for i in range(6):
    box(f'tk_hatch{i}', (2.2, 2.2, 0.7), (-40 - i * 16, 7.0, 6.85), GREEN_DECK, bv=0.2, parent=TK)
box('tk_manifold', (3, 20, 1.4), (-78, 0, 7.2), mat('manif', (0.75, 0.55, 0.08), 0.5), parent=TK)
tube('tk_foremast', [(-14, 0, tk_deck_z(14) - 0.2), (-14, 0, 19)], 0.35, mat('fmast', (0.85, 0.75, 0.10), 0.5), TK, seg=10)
for sy in (-1, 1):
    us = [24, 18, 12, 8, 5, 3, 1.6]
    tube(f'tk_frail{sy}', [(-u, sy * (tk_station(-u)[1] - 0.3), tk_deck_z(u) + 1.0) for u in us], 0.06, WHITE_P, TK, seg=6)
    for u in us: tube(f'tk_frailp{sy}{u}', [(-u, sy * (tk_station(-u)[1] - 0.3), tk_deck_z(u) - 0.1), (-u, sy * (tk_station(-u)[1] - 0.3), tk_deck_z(u) + 1.0)], 0.04, WHITE_P, TK, seg=6)
# white name on the bow (two thin bars stand in for the lettering at this size), white draft marks
TK.rotation_mode = 'XYZ'

# ---- the American Heritage: 90 m stern paddlewheeler, white decks with white rails, red wheel, twin black stacks.
# Parented to RB (pivot on the centre line at the waterline; a positive x-rotation lists her toward the river and rolls her over).
RB_PIV = Vector((0, 11.0, 0.0))
RB = empty('rb', loc=RB_PIV); RB.rotation_mode = 'XYZ'
RBL = empty('rb_local', RB, loc=-RB_PIV)                                 # children are placed in world-at-rest coordinates under this
def rbx(name, size, loc, m, bv=0.0, rot=(0, 0, 0)): return box(name, size, loc, m, bv, rot, RBL)
RB_WHITE = noisy(mat('rb_white', (0.86, 0.86, 0.84), 0.45), 4.0, 0.05)
RB_HULLM = hull_paint('rb_hullp', (0.88, 0.88, 0.86), (0.20, 0.20, 0.22), (0.12, 0.12, 0.13), waterline=0.0)
RB_CY = 11.0                                                             # centre line y
stR = []
for x_ in (-45, -44, -40, -20, 0, 20, 34, 39, 42, 44.5, 45.5):
    b_ = 8.0 if x_ < 30 else 8.0 * math.sqrt(max(0.02, 1 - ((x_ - 30) / 15.8) ** 2))
    stR.append((x_, b_, -2.0 + (0.8 if x_ > 40 else 0.0), 1.5, 8.0 if x_ < 30 else 3.0))
RB_HULL = loft('rb_hull', stR, RB_HULLM, RBL, seg=20)
for v in RB_HULL.data.vertices: v.co.y += RB_CY
DECK_M = mat('rb_deckm', (0.55, 0.50, 0.44), 0.7)
CARPET = noisy(mat('carpet', (0.20, 0.08, 0.07), 0.95), 18.0, 0.35)
GLASS_IN = mat('rb_glass', (0.55, 0.65, 0.70), 0.03, 0.0, trans=1.0, ior=1.2); GLASS_IN.surface_render_method = 'DITHERED'
CEIL = mat('ceiling', (0.90, 0.88, 0.82), 0.6)
GOLD = mat('gold', (0.85, 0.62, 0.22), 0.3, 1.0)
LEVELS = [(1.5, 4.3, -38, 38), (4.3, 7.1, -37, 36), (7.1, 9.9, -33, 30), (9.9, 12.7, -27, 27)]   # z0, z1, x0, x1 of each cabin
WALK = 1.6                                                               # walkway between the cabin wall and the rail
HIT_X = (-9.0, 6.0)                                                     # the stretch of the river-side wall the bow breaks
BREAK = []                                                               # parts hidden once the bow comes through
HOLE = []                                                                # torn plates shown after
def wall_run(name, x0, x1, y_, z0, z1, lvl, breakable=True, door=None):
    """a cabin wall along x at y_: lower band, posts and glass, upper band; split at the hit zone so it can break; door = an open doorway"""
    xs = [x0]
    for xb in list(HIT_X if breakable else ()) + list(door or ()):
        if x0 < xb < x1: xs.append(xb)
    xs = sorted(xs) + [x1]; out = []
    for a_, b_ in zip(xs[:-1], xs[1:]):
        inhit = breakable and a_ >= HIT_X[0] - 1e-6 and b_ <= HIT_X[1] + 1e-6
        grp = []
        h_ = z1 - z0
        if door and a_ >= door[0] - 1e-6 and b_ <= door[1] + 1e-6:      # the doorway: only the header above it
            out.append(rbx(f'{name}_door', (b_ - a_, 0.18, h_ * 0.16), ((a_ + b_) / 2, y_, z1 - h_ * 0.08), RB_WHITE))
            for xp in (a_, b_): out.append(rbx(f'{name}_jamb{xp:.0f}', (0.22, 0.24, h_), (xp, y_, (z0 + z1) / 2), RB_WHITE))
            continue
        grp.append(rbx(f'{name}_lo{a_:.0f}', (b_ - a_, 0.18, h_ * 0.30), ((a_ + b_) / 2, y_, z0 + h_ * 0.15), RB_WHITE))
        grp.append(rbx(f'{name}_hi{a_:.0f}', (b_ - a_, 0.18, h_ * 0.22), ((a_ + b_) / 2, y_, z1 - h_ * 0.11), RB_WHITE))
        grp.append(rbx(f'{name}_gl{a_:.0f}', (b_ - a_, 0.04, h_ * 0.48), ((a_ + b_) / 2, y_, z0 + h_ * 0.54), GLASS_IN))
        n_ = max(1, int((b_ - a_) / 2.6))
        for k in range(n_ + 1):
            grp.append(rbx(f'{name}_post{a_:.0f}_{k}', (0.22, 0.24, h_ * 0.5), (a_ + (b_ - a_) * k / n_, y_, z0 + h_ * 0.54), RB_WHITE))
        if inhit: BREAK.extend(grp)
        out += grp
    return out
def rail_run(name, x0, x1, y_, z0, breakable=True, gap=None):
    xs = sorted([x0] + [xb for xb in HIT_X if x0 < xb < x1] + ([g_ for g_ in gap if x0 < g_ < x1] if gap else []) + [x1])
    for a_, b_ in zip(xs[:-1], xs[1:]):
        if gap and a_ >= gap[0] - 1e-6 and b_ <= gap[1] + 1e-6: continue    # the gate for the gangway
        inhit = breakable and a_ >= HIT_X[0] - 1e-6 and b_ <= HIT_X[1] + 1e-6
        g = [rbx(f'{name}_top{a_:.0f}', (b_ - a_, 0.12, 0.12), ((a_ + b_) / 2, y_, z0 + 1.05), RB_WHITE),
             rbx(f'{name}_mid{a_:.0f}', (b_ - a_, 0.05, 0.05), ((a_ + b_) / 2, y_, z0 + 0.55), RB_WHITE)]
        for k in range(int((b_ - a_) / 1.2) + 1):
            g.append(rbx(f'{name}_p{a_:.0f}_{k}', (0.07, 0.07, 1.05), (a_ + k * 1.2, y_, z0 + 0.52), RB_WHITE))
        if inhit: BREAK.extend(g)
for li, (z0, z1, x0, x1) in enumerate(LEVELS):
    yp, ys = RB_CY - 8.0 + WALK, RB_CY + 8.0 - WALK                       # river-side and dock-side cabin walls
    rbx(f'deck{li}', (x1 - x0 + 2 * WALK + 2, 16.0, 0.25), ((x0 + x1) / 2, RB_CY, z0 - 0.12), DECK_M if li else CARPET)
    wall_run(f'wp{li}', x0, x1, yp, z0, z1, li, breakable=li <= 2)
    wall_run(f'ws{li}', x0, x1, ys, z0, z1, li, breakable=False, door=(-2.6, 0.6) if li == 0 else None)
    rbx(f'wend_a{li}', (0.2, ys - yp, z1 - z0), (x0, RB_CY, (z0 + z1) / 2), RB_WHITE)
    rbx(f'wend_b{li}', (0.2, ys - yp, z1 - z0), (x1, RB_CY, (z0 + z1) / 2), RB_WHITE)
    rbx(f'ceil{li}', (x1 - x0, ys - yp, 0.1), ((x0 + x1) / 2, RB_CY, z1 - 0.06), CEIL)
    rail_run(f'rp{li}', x0 - WALK, x1 + WALK, RB_CY - 7.9, z0, breakable=li <= 2)
    rail_run(f'rs{li}', x0 - WALK, x1 + WALK, RB_CY + 7.9, z0, breakable=False, gap=(4.6, 7.4) if li == 1 else None)
    # the deck overhang above the walkway (the next deck), with a gold trim line
    rbx(f'trim_p{li}', (x1 - x0 + 2 * WALK, 0.12, 0.18), ((x0 + x1) / 2, RB_CY - 8.0, z1 - 0.02), GOLD)
    rbx(f'trim_s{li}', (x1 - x0 + 2 * WALK, 0.12, 0.18), ((x0 + x1) / 2, RB_CY + 8.0, z1 - 0.02), GOLD)
rbx('sundeck', (58, 16, 0.25), (0, RB_CY, 12.7), DECK_M)

rail_run('rtop_p', -29, 29, RB_CY - 7.9, 12.75, False); rail_run('rtop_s', -29, 29, RB_CY + 7.9, 12.75, False)
PH = rbx('pilothouse', (6, 8, 2.8), (19, RB_CY, 14.2), RB_WHITE, bv=0.1)
rbx('ph_glass', (6.1, 8.1, 0.9), (19, RB_CY, 14.6), mat('phg', (0.06, 0.09, 0.12), 0.05))
rbx('ph_roof', (7, 9, 0.3), (19, RB_CY, 15.75), mat('phroof', (0.40, 0.08, 0.07), 0.5))
STACK_M = mat('stack', (0.03, 0.03, 0.035), 0.45)
for sy in (-3.5, 3.5):
    s_ = tube(f'stack{sy}', [(25, RB_CY + sy, 12.8), (25, RB_CY + sy, 22.5)], 0.75, STACK_M, RBL, seg=16)
    lathe(f'crown{sy}', [(0.75, 0), (1.2, 0.6), (1.35, 1.0), (1.2, 1.15), (0.0, 1.15)], 20, GOLD, RBL, loc=(25, RB_CY + sy, 22.5))
# the stern paddlewheel: red buckets on two rims, inside a white housing frame
PW = empty('paddlewheel', RBL, loc=(-50.2, RB_CY, 2.4)); PW.rotation_mode = 'XYZ'
RED = mat('wheel_red', (0.62, 0.05, 0.04), 0.5)
for sy in (-5.5, 5.5):
    tube(f'pw_rim{sy}', [(4.4 * math.cos(2 * math.pi * k / 40), sy, 4.4 * math.sin(2 * math.pi * k / 40)) for k in range(41)], 0.12, RED, PW, seg=8, caps=False)
for k in range(16):
    a_ = 2 * math.pi * k / 16
    box(f'pw_bucket{k}', (0.12, 11.4, 1.0), (4.0 * math.cos(a_), 0, 4.0 * math.sin(a_)), RED, rot=(0, -a_ + math.pi / 2, 0), parent=PW)
    tube(f'pw_spoke{k}', [(0, -5.5, 0), (4.2 * math.cos(a_), -5.5, 4.2 * math.sin(a_))], 0.08, RED, PW, seg=6)
    tube(f'pw_spoke2{k}', [(0, 5.5, 0), (4.2 * math.cos(a_), 5.5, 4.2 * math.sin(a_))], 0.08, RED, PW, seg=6)
tube('pw_axle', [(0, -6, 0), (0, 6, 0)], 0.35, RED, PW, seg=10)
for sy in (-6.2, 6.2):
    rbx(f'pw_arm{sy}', (8.5, 0.5, 0.6), (-47.5, RB_CY + sy, 4.0), RB_WHITE)
# ---- the dining room on the main deck: white cloth tables, chairs, a buffet, ceiling lights; the bow comes through its river-side wall
TABLES = []
CLOTH = mat('cloth', (0.93, 0.93, 0.90), 0.8, sheen=0.4); CHAIR_M = mat('chair', (0.32, 0.18, 0.09), 0.6)
for i in range(7):
    for j in range(3):
        cx, cy = -30 + i * 9.0, RB_CY - 4.0 + j * 4.0
        if j == 0 and -12 < cx < 3: continue                              # the bow comes in here
        g = empty(f'table{i}_{j}', RBL, loc=(cx, cy, 1.5)); g.rotation_mode = 'XYZ'
        lathe(f'tcloth{i}_{j}', [(0.0, 0.78), (0.75, 0.78), (0.78, 0.74), (0.80, 0.25), (0.0, 0.25)], 24, CLOTH, g)
        tube(f'tleg{i}_{j}', [(0, 0, 0), (0, 0, 0.3)], 0.06, CHAIR_M, g, seg=8)
        for k in range(4):
            a_ = math.pi / 4 + k * math.pi / 2; c = empty(f'chair{i}_{j}_{k}', g, loc=(1.05 * math.cos(a_), 1.05 * math.sin(a_), 0)); c.rotation_euler = (0, 0, a_)
            box(f'cseat{i}{j}{k}', (0.45, 0.45, 0.06), (0, 0, 0.46), CHAIR_M, parent=c)
            box(f'cback{i}{j}{k}', (0.06, 0.45, 0.5), (0.22, 0, 0.72), CHAIR_M, parent=c)
            for lx, ly in ((-0.18, -0.18), (-0.18, 0.18), (0.18, -0.18), (0.18, 0.18)):
                box(f'cleg{i}{j}{k}{lx}{ly}', (0.04, 0.04, 0.46), (lx, ly, 0.23), CHAIR_M, parent=c)
        for k in range(3):                                               # glasses and plates on the table
            a_ = k * 2.1; lathe(f'glass{i}{j}{k}', [(0.0, 0.79), (0.035, 0.79), (0.04, 0.95), (0.0, 0.95)], 10, GLASS_IN, g, loc=(0.4 * math.cos(a_), 0.4 * math.sin(a_), 0))
        TABLES.append((g, cx, cy))
for i in range(6):
    rbx(f'ceil_light{i}', (3.0, 0.8, 0.06), (-27 + i * 10, RB_CY, 4.18), emis(f'cl{i}', (1.0, 0.92, 0.78), 6.0))
IN_LT = light_at('in_lt', 'AREA', (-6, RB_CY, 4.05), (-6, RB_CY, 0), 6500, (1.0, 0.9, 0.78), 1.0); IN_LT.parent = RBL
IN_LT.data.shape = 'RECTANGLE'; IN_LT.data.size = 64; IN_LT.data.size_y = 10
UP_LT = light_at('up_lt', 'AREA', (-6, RB_CY, 2.9), (-6, RB_CY, 9), 3500, (1.0, 0.93, 0.82), 1.0); UP_LT.parent = RBL
UP_LT.data.shape = 'RECTANGLE'; UP_LT.data.size = 64; UP_LT.data.size_y = 8
rbx('buffet', (10, 1.0, 1.0), (-8, RB_CY + 5.6, 2.0), mat('buffet', (0.35, 0.20, 0.10), 0.4))
rbx('bar_top', (10.2, 1.1, 0.06), (-8, RB_CY + 5.6, 2.53), mat('marble', (0.86, 0.84, 0.80), 0.15))
# the torn steel round the hole (shown after the hit): bent white plates pushed inward, ragged edges
for k in range(9):
    xk = HIT_X[0] + 0.6 + k * (HIT_X[1] - HIT_X[0] - 1.2) / 8; zk = 1.6 + 2.6 * h1(k + 3)
    HOLE.append(rbx(f'torn{k}', (0.35 + 0.4 * h1(k), 0.06, 0.4 + 0.5 * h1(k + 1)), (xk, RB_CY - 6.3 + 0.5 * h1(k + 7), zk), RB_WHITE,
                    rot=(R(-30 + 60 * h1(k + 2)), R(-40 + 80 * h1(k + 5)), R(-60 + 120 * h1(k + 9)))))
for o in HOLE: o.hide_render = True
HOLE.clear()
def ragged(name, x0, x1, z0, z1, y_, seed):
    r_ = random.Random(seed); pts = []
    for k in range(28):
        a_ = 2 * math.pi * k / 28; rx = (x1 - x0) / 2 * (0.75 + 0.25 * r_.random()); rz = (z1 - z0) / 2 * (0.75 + 0.25 * r_.random())
        pts.append(((x0 + x1) / 2 + rx * math.cos(a_), y_, (z0 + z1) / 2 + rz * math.sin(a_)))
    vs = [((x0 + x1) / 2, y_, (z0 + z1) / 2)] + pts; fs = [(0, 1 + k, 1 + (k + 1) % 28) for k in range(28)]
    return mesh(name, vs, fs, mat(name + 'm', (0.02, 0.018, 0.015), 0.9), RBL, smooth_=False)
HOLE.append(ragged('hull_hole', -12.5, 0.5, -1.4, 1.48, RB_CY - 8.0 - 0.03, 5))
for o in HOLE: o.hide_render = True

# ================================================================ people: the house MakeHuman man (man.blend), posed on his rig and BAKED into
# shared meshes (one per pose and phase), so a crowd costs one mesh per pose. Clothes recoloured per person (object-level materials).
# A life vest is a shell of his own shirt pushed out (it deforms with him, so nothing pokes through).
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
MANCOL = bpy.data.collections.new('man_src'); S.collection.children.link(MANCOL)
for o in _dst.objects: MANCOL.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HAIR = bpy.data.objects['Human.short02']; EYES = bpy.data.objects['Human.high-poly']
LASH = bpy.data.objects['Human.eyelashes01']; BROW = bpy.data.objects['Human.eyebrow001']
PB = RIG.pose.bones
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
for o in MANCOL.objects: o.hide_render = True; o.hide_viewport = False
SHORTS_SRC = SUIT.data.materials[0]; SHIRT_SRC = SHORTS_SRC.copy(); SHIRT_SRC.name = 'shirt_src'; SUIT.data.materials.append(SHIRT_SRC)
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
    return m
# the vest: his shirt's torso faces (not the sleeves), pushed out along their normals, bright orange with a reflective band
_vgn = {g.index: g.name for g in SUIT.vertex_groups}
_ARM = {b_ + s_ for s_ in ('.L', '.R') for b_ in ('clavicle', 'shoulder01', 'upperarm01', 'upperarm02', 'lowerarm01', 'lowerarm02', 'wrist')}
def _armw(v): return sum(g.weight for g in v.groups if _vgn.get(g.group, '') in _ARM)
_vf = [p_.index for p_ in SUIT.data.polygons if 1.0 < sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) < 1.42
       and max(_armw(SUIT.data.vertices[i]) for i in p_.vertices) < 0.25]
_bm = bmesh.new(); _bm.from_mesh(SUIT.data); _keep = set(_vf)
bmesh.ops.delete(_bm, geom=[f for f in _bm.faces if f.index not in _keep], context='FACES')
_bm.normal_update()
for v in _bm.verts: v.co += v.normal * 0.028
_vm = bpy.data.meshes.new('vest'); _bm.to_mesh(_vm); _bm.free()
VEST = bpy.data.objects.new('vest', _vm); MANCOL.objects.link(VEST); VEST.parent = SUIT.parent; VEST.matrix_world = SUIT.matrix_world.copy()
for g in SUIT.vertex_groups: VEST.vertex_groups.new(name=g.name)
_md = VEST.modifiers.new('arm', 'ARMATURE'); _md.object = RIG
_sol = VEST.modifiers.new('thick', 'SOLIDIFY'); _sol.thickness = 0.03; _sol.offset = 1.0
VEST_M = mat('lifevest', (1.0, 0.28, 0.02), 0.55)
_vn = VEST_M.node_tree; _vb = _vn.nodes['Principled BSDF']; _vz = sepz(_vn, coord(_vn, 'Object')).outputs['Z']
_band = math_(_vn, 'MULTIPLY', math_(_vn, 'GREATER_THAN', _vz, 1.18), math_(_vn, 'LESS_THAN', _vz, 1.23))
_vn.links.new(mixc(_vn, _band, (1.0, 0.28, 0.02), (0.92, 0.92, 0.90)), _vb.inputs['Base Color'])
VEST.data.materials.append(VEST_M); VEST.hide_render = True

# ---- poses: bone rotations (radians). Front is -Y; legs swing forward with -X, arms forward with +X, L arm out with +Z, R arm out with -Z
POSE_BONES = ['upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'upperarm01.L', 'upperarm01.R', 'lowerarm01.L', 'lowerarm01.R', 'spine01', 'spine03', 'neck01', 'foot.L', 'foot.R']
def set_pose(d):
    for n in POSE_BONES:
        b = PB[n]; b.rotation_mode = 'XYZ'; b.rotation_euler = d.get(n, (0, 0, 0))
def p_stand(ph=0.0):
    return {'upperarm01.L': (0.05 * math.sin(ph), 0, -0.38), 'upperarm01.R': (0.05 * math.sin(ph + 1), 0, 0.38), 'lowerarm01.L': (0.15, 0, 0), 'lowerarm01.R': (0.15, 0, 0)}
def p_gait(ph, leg, knee, arm, elbow, lean):
    s_ = math.sin(ph)
    return {'upperleg01.L': (-leg * s_, 0, 0), 'upperleg01.R': (leg * s_, 0, 0),
            'lowerleg01.L': (knee * max(0.0, math.sin(ph - 1.2)) + 0.1, 0, 0), 'lowerleg01.R': (knee * max(0.0, math.sin(ph + math.pi - 1.2)) + 0.1, 0, 0),
            'upperarm01.L': (-arm * s_, 0, -0.42), 'upperarm01.R': (arm * s_, 0, 0.42), 'lowerarm01.L': (elbow, 0, 0), 'lowerarm01.R': (elbow, 0, 0),
            'spine01': (lean, 0, 0)}
def p_brace(ph=0.0):
    return {'upperarm01.L': (0.5, 0, 0.25 + 0.08 * math.sin(ph)), 'upperarm01.R': (0.5, 0, -0.25 - 0.08 * math.sin(ph)), 'lowerarm01.L': (0.9, 0, 0), 'lowerarm01.R': (0.9, 0, 0),
            'upperleg01.L': (-0.25, 0, 0.06), 'upperleg01.R': (-0.25, 0, -0.06), 'lowerleg01.L': (0.45, 0, 0), 'lowerleg01.R': (0.45, 0, 0), 'spine01': (0.15, 0, 0)}
def p_climb(ph):
    s_ = math.sin(ph)
    return {'upperarm01.L': (1.9 + 0.35 * s_, 0, -0.2), 'upperarm01.R': (1.9 - 0.35 * s_, 0, 0.2), 'lowerarm01.L': (0.6, 0, 0), 'lowerarm01.R': (0.6, 0, 0),
            'upperleg01.L': (-0.5 - 0.3 * s_, 0, 0), 'upperleg01.R': (-0.2 + 0.3 * s_, 0, 0), 'lowerleg01.L': (0.7, 0, 0), 'lowerleg01.R': (0.4, 0, 0), 'spine01': (0.3, 0, 0)}
def p_tread(ph):
    s_ = math.sin(ph); c_ = math.cos(ph)
    return {'upperarm01.L': (0.4 + 0.35 * s_, 0, 0.55 + 0.3 * c_), 'upperarm01.R': (0.4 - 0.35 * s_, 0, -0.55 - 0.3 * c_), 'lowerarm01.L': (0.5, 0, 0), 'lowerarm01.R': (0.5, 0, 0),
            'upperleg01.L': (-0.4 - 0.3 * s_, 0, 0.1), 'upperleg01.R': (-0.4 + 0.3 * s_, 0, -0.1), 'lowerleg01.L': (0.9 + 0.3 * c_, 0, 0), 'lowerleg01.R': (0.9 - 0.3 * c_, 0, 0)}
def p_jump(ph=0.0):
    return {'upperarm01.L': (2.7, 0, 0.1), 'upperarm01.R': (2.7, 0, -0.1), 'lowerarm01.L': (0.1, 0, 0), 'lowerarm01.R': (0.1, 0, 0),
            'upperleg01.L': (-0.9, 0, 0.05), 'upperleg01.R': (-0.6, 0, -0.05), 'lowerleg01.L': (1.3, 0, 0), 'lowerleg01.R': (1.0, 0, 0), 'spine01': (0.25, 0, 0)}
def p_wave(ph):
    d = p_stand(); d['upperarm01.R'] = (0.3, 0, -2.5); d['lowerarm01.R'] = (0.2, 0, -0.45 * math.sin(ph) - 0.2); return d
POSES = {'stand': (1, p_stand), 'walk': (6, lambda ph: p_gait(ph, 0.42, 0.7, 0.35, 0.3, 0.04)), 'run': (6, lambda ph: p_gait(ph, 0.85, 1.4, 0.8, 1.3, 0.22)),
         'brace': (2, p_brace), 'climb': (4, p_climb), 'tread': (4, p_tread), 'jump': (1, p_jump), 'wave': (4, p_wave)}
PARTS = [BODY, SUIT, HAIR, EYES, LASH, BROW]
def bake(name, vest):
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); mats = []
    for o in PARTS + ([VEST] if vest else []):
        ev = o.evaluated_get(dg); me = ev.to_mesh(); nf0 = len(bm.faces); nv0 = len(bm.verts)
        bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts[nv0:])
        for f in bm.faces[nf0:]: f.material_index += len(mats); f.smooth = True
        mats += list(o.data.materials); ev.to_mesh_clear()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in mats: me.materials.append(m_)
    return me
BAKED = {}
NEED = {False: ('stand', 'walk', 'run', 'brace', 'tread', 'jump'), True: ('stand', 'brace', 'climb', 'tread', 'wave')}
for vest_, modes in NEED.items():
    for md_ in modes:
        n_, fn = POSES[md_]
        for k in range(n_):
            set_pose(fn(2 * math.pi * k / n_)); bpy.context.view_layer.update(); BAKED[(vest_, md_, k)] = bake(f'man_{md_}{k}{"v" if vest_ else ""}', vest_)
set_pose({}); bpy.context.view_layer.update()
SLOT_SKIN = 0; SLOT_SHORTS = len(BODY.data.materials); SLOT_SHIRT = SLOT_SHORTS + 1
SKINS = [(0.95, 0.80, 0.70), (0.70, 0.52, 0.40), (0.48, 0.33, 0.24), (0.98, 0.86, 0.76), (0.82, 0.64, 0.50)]
SHIRTS = [(0.15, 0.30, 0.60), (0.80, 0.80, 0.78), (0.62, 0.15, 0.13), (0.20, 0.45, 0.30), (0.85, 0.72, 0.38), (0.30, 0.30, 0.34), (0.55, 0.38, 0.62), (0.90, 0.55, 0.60)]
SHIRT_M = [retint(SHIRT_SRC.copy(), c) for c in SHIRTS]
SHORTS_M = [retint(SHORTS_SRC.copy(), c) for c in ((0.12, 0.13, 0.20), (0.42, 0.37, 0.28), (0.20, 0.20, 0.22), (0.30, 0.34, 0.45))]
POLICE_M = retint(SHIRT_SRC.copy(), (0.05, 0.07, 0.17), 0.3); POLICE_P = retint(SHORTS_SRC.copy(), (0.05, 0.07, 0.15), 0.3)
CREW_M = retint(SHIRT_SRC.copy(), (0.95, 0.95, 0.95), 0.25); CREW_P = retint(SHORTS_SRC.copy(), (0.08, 0.08, 0.10), 0.3)
BAG_M = [mat('bag0', (0.10, 0.10, 0.12), 0.5), mat('bag1', (0.45, 0.10, 0.10), 0.5), mat('bag2', (0.15, 0.25, 0.45), 0.5)]
PEOPLE = []
def figure(name, seed, kind='guest', parent=None, loc=(0, 0, 0), yaw=0.0, scale=1.0, vest=False, bag=False):
    """yaw = the direction he faces, measured from +x (like the old figures)"""
    r_ = random.Random(seed); me = BAKED[(vest, 'stand', 0)]
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.location = loc; o.rotation_mode = 'XYZ'; o.rotation_euler = (0, 0, yaw + math.pi / 2)
    if parent: o.parent = parent
    sc = scale * r_.uniform(0.95, 1.06); o.scale = (sc, sc, sc)
    for i_, m_ in ((SLOT_SHIRT, POLICE_M if kind == 'police' else CREW_M if kind == 'crew' else SHIRT_M[r_.randrange(len(SHIRT_M))]),
                   (SLOT_SHORTS, POLICE_P if kind == 'police' else CREW_P if kind == 'crew' else SHORTS_M[r_.randrange(len(SHORTS_M))])):
        o.material_slots[i_].link = 'OBJECT'; o.material_slots[i_].material = m_
    if bag:                                                              # a roller bag at his side, handle in his hand's reach
        b_ = box(name + '_bag', (0.36, 0.22, 0.52), (0.42, 0.10, 0.27), BAG_M[r_.randrange(3)], bv=0.04, parent=o)
        tube(name + '_bagh', [(0.42, 0.10, 0.53), (0.42, 0.10, 0.80)], 0.012, BAG_M[0], o, seg=6)
    p = dict(root=o, seed=seed, kind=kind, vest=vest); PEOPLE.append(p); return p
def pose(p, mode, t, phase=0.0):
    n_, _ = POSES[mode]; v_ = p['vest']
    if (v_, mode, 0) not in BAKED: mode = 'stand' if (v_, 'stand', 0) in BAKED else mode; n_ = POSES[mode][0]
    rate = {'walk': 1.8, 'run': 2.8, 'climb': 1.4, 'tread': 1.0, 'wave': 2.0, 'brace': 0.5}.get(mode, 0.0)
    k = int(((t * rate + phase + p['seed'] * 0.137) % 1.0) * n_) if n_ > 1 else 0
    p['root'].data = BAKED[(v_, mode, k)]
def place(p, loc, yaw=None):
    p['root'].location = loc
    if yaw is not None: p['root'].rotation_euler = (0, 0, yaw + math.pi / 2)
def face(p, yaw): p['root'].rotation_euler = (0, 0, yaw + math.pi / 2)

# ---- the cast
# passengers waiting to get off (main-deck walkway on the dock side, boat frame), and some already on the wharf with bags
GUESTS = [figure(f'g{i}', 100 + i, parent=RBL, loc=(2 + 1.2 * i + 0.4 * h1(i), RB_CY + 7.15 - 0.3 * h1(i + 50), 1.5), yaw=math.pi * (0.5 if i % 3 else 0.0) + 0.3 * (h1(i + 9) - 0.5)) for i in range(12)]
WALKERS = [figure(f'w{i}', 200 + i, loc=(6 + 1.0 * (i % 2), 23.4 + 1.8 * i, 3.4), yaw=math.pi / 2, bag=True) for i in range(5)]
CREW = figure('crew0', 7, 'crew', RBL, loc=(-6.5, RB_CY + 1.0, 1.5), yaw=0.2)
DINERS = []
# on the high side in life vests (deck 2 and 3 walkways, dock side), boat frame
HIGH = []
for i in range(24):
    lv = (1, 2)[i % 2]; z0 = LEVELS[lv][0]
    HIGH.append(figure(f'h{i}', 400 + i, parent=RBL, loc=(-30 + 2.4 * i + 0.5 * h1(i), RB_CY + 7.25, z0), yaw=math.pi / 2 + 0.3 * (h1(i + 2) - 0.5), vest=True))
POLICE = [figure(f'p{i}', 500 + i, 'police', loc=(60 + 6 * i, 28 + 2 * (i % 2), 3.4), yaw=math.pi) for i in range(5)]
SWIM = [figure(f's{i}', 600 + i, loc=(-12 + 3.4 * i, -6, -1.25), yaw=h1(i + 60) * 6.28, vest=True) for i in range(14)]
RESC = [figure(f'r{i}', 700 + i, 'police', loc=(0, 0, 0), yaw=-math.pi / 2) for i in range(2)]
def show_fig(p, on):
    stack = [p['root']]
    while stack:
        o = stack.pop(); o.hide_render = not on; stack.extend(o.children)
for p in SWIM + RESC: show_fig(p, False)

# ================================================================ water effects, rescue boats, ambulances
def foam_mat(name, attr='a', scale=3.0, thr=0.8, radial=True):
    """white foam with a noisy edge over transparent; object property attr (0..1) sets how much shows"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    b.inputs['Base Color'].default_value = (0.92, 0.90, 0.84, 1); b.inputs['Roughness'].default_value = 0.6
    co = coord(nt, 'Generated'); sx = sepz(nt, co)
    rad = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'ADD', math_(nt, 'POWER', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', sx.outputs['X'], 0.5), 2.0), 2.0),
                                                                                    math_(nt, 'POWER', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', sx.outputs['Y'], 0.5), 2.0), 2.0)), 0.5), 1.0))
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    nt.links.new(coord(nt, 'Object'), nz.inputs['Vector']); nt.links.new(objattr(nt, 'tw'), nz.inputs['W'])
    al = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', math_(nt, 'ADD', math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.9), math_(nt, 'MULTIPLY', rad, 0.6 if radial else 0.0)), thr), objattr(nt, attr))
    nt.links.new(al, b.inputs['Alpha']); return m
FOAM_M = foam_mat('foam', scale=9.0, thr=0.95)
BOW_FOAM = prim('plane', 'bow_foam', FOAM_M, TK, loc=(-2, 0, 0.06), size=1, scale=(26, 36, 1)); BOW_FOAM['a'] = 1.0; BOW_FOAM['tw'] = 0.0
# the bow wave: a curling ridge of white water peeling off each side of the stem
WAVE_M = foam_mat('bowwave', scale=6.0, thr=0.22, radial=False); BOW_WAVE = []
for sy in (-1, 1):
    vs = []; fs = []
    for i in range(14):
        u = i / 13; x_ = -u * 34; yb = (12.4 * (math.sin(math.pi / 2 * min(u * 34, 28) / 28)) ** 0.75 + 0.3) * sy
        out = (0.6 + 4.0 * u) * sy; hgt = 1.6 * (1 - u) ** 1.3 + 0.1
        vs += [(x_, yb, hgt), (x_, yb + out * 0.5, hgt * 0.75), (x_, yb + out, 0.0)]
        if i: fs += [(3 * i - 3, 3 * i - 2, 3 * i + 1, 3 * i), (3 * i - 2, 3 * i - 1, 3 * i + 2, 3 * i + 1)]
    o = mesh(f'bow_wave{sy}', vs, fs, WAVE_M, TK); o['a'] = 1.0; o['tw'] = 0.0; BOW_WAVE.append(o)
HIT_FOAM = prim('plane', 'hit_foam', foam_mat('hitfoam', scale=7.0, thr=0.9), loc=(-4, 2.0, 0.08), size=1, scale=(30, 22, 1)); HIT_FOAM['a'] = 0.0; HIT_FOAM['tw'] = 0.0
ROLL_FOAM = prim('plane', 'roll_foam', foam_mat('rollfoam', scale=6.0, thr=0.9), loc=(-2, -2.0, 0.09), size=1, scale=(110, 40, 1)); ROLL_FOAM['a'] = 0.0; ROLL_FOAM['tw'] = 0.0
# splash: a burst of droplets (small spheres) thrown from a point, falling under gravity; shared drop meshes reused per burst
DROP_M = mat('drop', (0.88, 0.86, 0.80), 0.35)
class Burst:
    def __init__(s, name, n, seed, speed=9.0, up=1.0, size=0.18, spread=1.0, dirv=(0, 0, 1)):
        r_ = random.Random(seed); s.d = []; s.v = []; s.size = size
        for i in range(n):
            o = prim('ico_sphere', f'{name}{i}', DROP_M, loc=(0, 0, -50), size=1, scale=(size * (0.5 + r_.random()),) * 3, subdivisions=1); o.hide_render = True
            dv = Vector(dirv).normalized(); rv = Vector((r_.gauss(0, 1), r_.gauss(0, 1), r_.gauss(0, 1))) * spread
            v = (dv + rv).normalized() * speed * (0.5 + r_.random()); v.z = abs(v.z) * up + 2.0; s.d.append(o); s.v.append(v)
    def at(s, origin, t):
        for o, v in zip(s.d, s.v):
            if t < 0 or t > 2.2: o.hide_render = True; continue
            p = Vector(origin) + v * t + Vector((0, 0, -4.9 * t * t)); o.location = p; o.hide_render = p.z < -0.3
            vel = v + Vector((0, 0, -9.8 * t)); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = vel.to_track_quat('Z', 'Y')
            o.scale = (1, 1, 1 + vel.length * 0.016 / s.size)                # stretched along its path: reads as a streak, not a ball
HIT_SPLASH = Burst('hs', 120, 1, 11.0, 1.4, 0.06, 0.9, (0.2, -1.0, 0.4))
ROLL_SPLASH = Burst('rs', 140, 2, 9.0, 1.2, 0.07, 1.2, (0, -1.0, 0.6))
JUMP_SPLASH = [Burst(f'js{k}', 18, 10 + k, 4.0, 1.5, 0.12, 0.7) for k in range(2)]
GLASS_BITS = Burst('gb', 40, 3, 6.0, 0.6, 0.025, 0.8, (0.1, 1.0, 0.2))
for o in GLASS_BITS.d: o.data.materials[0] = GLASS_IN
# the flood inside the dining room: a sheet of river pouring through the hole and a rising pool on the carpet (boat frame)
def pour_mat():
    m = bpy.data.materials.new('pour'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    b.inputs['Base Color'].default_value = (0.16, 0.13, 0.07, 1); b.inputs['Roughness'].default_value = 0.04; b.inputs['Transmission Weight'].default_value = 0.5; b.inputs['IOR'].default_value = 1.33
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 5.0; nz.inputs['Detail'].default_value = 6
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.0, 0.6, 0.25); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector']); nt.links.new(mp.outputs[0], nz.inputs['Vector'])
    nt.links.new(objattr(nt, 'tw'), nz.inputs['W'])
    nt.links.new(mixc(nt, math_(nt, 'POWER', nz.outputs['Fac'], 3.0), (0.14, 0.11, 0.06), (0.62, 0.58, 0.48)), b.inputs['Base Color'])
    al = math_(nt, 'MULTIPLY', math_(nt, 'ADD', 0.55, math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.5)), objattr(nt, 'a'))
    nt.links.new(al, b.inputs['Alpha'])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.6; nt.links.new(nz.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    return m
POUR_M = pour_mat()
POUR = []
for k in range(3):                                                       # three falling sheets at the hole, curving in and down
    xk = HIT_X[0] + 2.0 + k * 3.6
    pts = [(xk, RB_CY - 6.6 + 1.6 * (u / 7) ** 0.7, 3.2 - 1.7 * (u / 7) ** 1.6) for u in range(8)]
    vs = []; fs = []
    for i, p_ in enumerate(pts):
        vs += [(p_[0] - 1.3, p_[1], p_[2]), (p_[0] + 1.3, p_[1], p_[2])]
        if i: fs.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    o = mesh(f'pour{k}', vs, fs, POUR_M, RBL); o['a'] = 0.0; o['tw'] = 0.0; POUR.append(o)
FLOOD = rbx('flood', (75.0, 12.6, 0.02), (0, RB_CY, 1.52), mat('flood', (0.20, 0.16, 0.09), 0.04, trans=0.3, ior=1.33))
FLOOD.hide_render = True
# rescue boats: an orange Coast Guard response boat and a grey harbor police boat with blue lights; ambulances with flashing lights on the wharf
CG_ORANGE = mat('cg_orange', (0.95, 0.35, 0.05), 0.5); CG_GREY = mat('cg_grey', (0.55, 0.57, 0.60), 0.5)
def small_boat(name, hull_m, cab_m, light_col):
    g = empty(name); g.rotation_mode = 'XYZ'
    loft(name + '_h', [(-5, 1.6, -0.6, 0.9, 6), (0, 1.7, -0.7, 1.0, 6), (3, 1.4, -0.6, 1.1, 4), (5, 0.3, 0.0, 1.3, 2)], hull_m, g, seg=14)
    box(name + '_cab', (2.6, 2.2, 1.4), (-0.8, 0, 1.7), cab_m, bv=0.15, parent=g)
    box(name + '_win', (2.65, 2.25, 0.5), (-0.8, 0, 2.0), mat(name + 'w', (0.05, 0.07, 0.09), 0.05), parent=g)
    lt = box(name + '_lt', (0.5, 1.0, 0.18), (-0.8, 0, 2.5), emis(name + 'le', light_col, 0.0), parent=g)
    return g, lt
CG_BOAT, CG_LT = small_boat('cgboat', CG_ORANGE, mat('cgw', (0.92, 0.92, 0.92), 0.5), (1.0, 0.25, 0.1))
PD_BOAT, PD_LT = small_boat('pdboat', CG_GREY, CG_GREY, (0.1, 0.3, 1.0))
CG_WAKE = prim('plane', 'cg_wake', foam_mat('cgwake', scale=2.0), CG_BOAT, loc=(-7, 0, -0.85), size=1, scale=(12, 5, 1)); CG_WAKE['a'] = 1.0; CG_WAKE['tw'] = 0.0
PD_WAKE = prim('plane', 'pd_wake', foam_mat('pdwake', scale=2.0), PD_BOAT, loc=(-7, 0, -0.85), size=1, scale=(12, 5, 1)); PD_WAKE['a'] = 1.0; PD_WAKE['tw'] = 0.0
AMBS = []
for i in range(3):
    g = empty(f'amb{i}', loc=(22 + 9 * i, 34 + 1.5 * i, 3.4)); g.rotation_euler = (0, 0, 0.1 * i)
    box(f'amb{i}_body', (6.5, 2.4, 2.6), (0, 0, 1.6), mat(f'ambw{i}', (0.94, 0.94, 0.92), 0.4), bv=0.15, parent=g)
    box(f'amb{i}_stripe', (6.55, 2.45, 0.35), (0, 0, 1.4), mat(f'ambr{i}', (0.80, 0.08, 0.06), 0.4), parent=g)
    box(f'amb{i}_cab', (1.8, 2.3, 1.2), (3.6, 0, 1.0), mat(f'ambw{i}b', (0.94, 0.94, 0.92), 0.4), bv=0.15, parent=g)
    for w_ in (-2.2, 2.2):
        for sy in (-1.1, 1.1):
            tube(f'amb{i}_wh{w_}{sy}', [(w_, sy - 0.15, 0.4), (w_, sy + 0.15, 0.4)], 0.42, BLACK_RUB, g, seg=12)
    l1 = box(f'amb{i}_l1', (0.3, 0.6, 0.2), (2.9, -0.6, 3.0), emis(f'aml1{i}', (1.0, 0.1, 0.05), 0.0), parent=g)
    l2 = box(f'amb{i}_l2', (0.3, 0.6, 0.2), (2.9, 0.6, 3.0), emis(f'aml2{i}', (0.2, 0.3, 1.0), 0.0), parent=g)
    AMBS.append((g, l1, l2))
def flash(o, on, t, rate=3.0, ph=0.0, peak=40.0):
    nd = o.data.materials[0].node_tree.nodes['Emission']
    nd.inputs['Strength'].default_value = (peak if (math.sin(2 * math.pi * rate * t + ph) > 0.2) else 0.4) if on else 0.0

# ================================================================ motion: the tanker, the riverboat, the people, and ONE continuous camera move
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
# ---- the tanker: swings from 22 to 52 degrees while it closes on the riverboat's river side, hits at T_HIT, crushes in, then drifts back
C_HIT = Vector((-4.0, 1.8, 0.0)); V_TK = 3.2; PEN = 4.5; T_BACK = 12.6
def tk_psi_pre(t): return R(lerp(22.0, 52.0, ease_io(clamp(t, -2, T_HIT) / T_HIT)))
_tk_tab = {}
def _tk_pre(t):
    """stem position before the hit: integrate back from the contact point"""
    key = round(t * 120)
    if key in _tk_tab: return _tk_tab[key]
    n = max(1, int((T_HIT - t) * 120)); dt = (T_HIT - t) / n; p = C_HIT.copy(); s_ = T_HIT
    for _ in range(n):
        s_ -= dt; a_ = tk_psi_pre(s_); p -= Vector((math.cos(a_), math.sin(a_), 0)) * V_TK * dt
    _tk_tab[key] = p; return p
def tk_pose(t):
    hit_dir = Vector((math.cos(R(52)), math.sin(R(52)), 0))
    if t < T_HIT: return _tk_pre(t), tk_psi_pre(t)
    p = C_HIT + hit_dir * PEN * ease_out((t - T_HIT) / 0.5)
    k = ease_io((t - T_BACK) / 7.0); p = p - hit_dir * 30.0 * k + Vector((-25.0, 0, 0)) * k
    return p, R(52) - R(7) * k
def tk_matrix(t):
    p, a_ = tk_pose(t); return Matrix.Translation(p) @ Matrix.Rotation(a_, 4, 'Z')
# ---- the riverboat: shoved and rocked by the hit, settles, lists toward the river, rolls onto her side and sinks to a sliver
def rb_theta(t):
    th = 0.0
    if t > T_HIT: th += R(3.5) * math.exp(-(t - T_HIT) / 1.3) * math.sin(2 * math.pi * 0.9 * (t - T_HIT))
    th += R(3) * ease_io((t - 14.6) / 1.4) + R(9) * ease_io((t - 16.0) / 3.5) + R(8) * ease_io((t - 19.5) / 2.9)
    th += R(64) * ease_io((t - (T_ROLL - 0.15)) / 2.3) - R(2) * ease_io((t - (T_ROLL + 2.1)) / 0.8)
    return th
def rb_off(t):
    o = Vector((0, 0, 0))
    if t > T_HIT: o.y += 0.18 * ease_out((t - T_HIT) / 0.35) - 0.12 * ease_io((t - T_HIT - 0.35) / 1.0); o.x += 0.3 * ease_out((t - T_HIT) / 0.5)
    o.z -= 0.4 * ease_io((t - T_HIT - 1) / 4) + 0.8 * ease_io((t - 14) / 8) + 5.0 * ease_io((t - T_ROLL) / 3.2)
    o.z += 0.08 * math.sin(2 * math.pi * 0.23 * t)
    return o
def rb_matrix(t):
    return Matrix.Translation(RB_PIV + rb_off(t)) @ Matrix.Rotation(rb_theta(t), 4, 'X') @ Matrix.Translation(-RB_PIV)

# ---- people standing on the capsized hull's dock side (world, after the roll)
ONTOP = [figure(f'o{i}', 800 + i, loc=(-24 + 7.5 * i, 12.4, 2.1), yaw=math.pi / 2 + h1(i + 3), vest=True) for i in range(7)]
# ---- the camera: one key list, every key in a frame ('w' world, 'b' boat, 'tk' tanker, 'k0' = frame one's pose kept beside the tanker)
K = [
    (0.0, 'w', (-11.0, -22.0, 2.0), (-22.0, -5.0, 4.0), 16),
    (1.4, 'w', (-3.0, -20.0, 4.0), (-15, -2, 4.5), 18),
    (2.9, 'w', (40.0, -10.0, 18.0), (10, 15, 4), 24),
    (4.2, 'w', (20.0, 36.0, 12.0), (6, 20, 3), 24),
    (5.6, 'w', (-10.0, -70.0, 120.0), (-25, -15, 0), 20),
    (7.0, 'w', (28.0, -38.0, 20.0), (-3, 2, 3), 22),
    (T_HIT, 'w', (16.0, -14.0, 6.0), (-3, 3, 3), 24),
    (9.1, 'w', (8.0, -4.0, 4.0), (0, 4, 3), 24),
    (10.0, 'b', (4.2, 2.2, 3.2), (2, 9, 3), 22),
    (10.8, 'b', (3.0, 7.2, 3.1), (-4, 5.5, 2.6), 20),
    (12.2, 'b', (2.0, 10.0, 3.0), (-8, 7.5, 2.4), 22),
    (13.6, 'b', (1.5, 10.5, 2.7), (-3, 5.6, 2.0), 22),
    (15.2, 'b', (0.0, 12.0, 2.9), (-3, 6.0, 1.8), 20),
    (16.6, 'b', (-1.0, 14.5, 3.1), (-1, 19, 3.2), 20),
    (17.6, 'b', (-1.0, 17.5, 3.4), (-1, 26, 4), 22),
    (18.6, 'b', (-1.0, 23.5, 7.5), (-6, 14, 7.5), 22),
    (20.3, 'w', (20.0, 52.0, 14.0), (-4, 14, 5), 24),
    (21.6, 'w', (48.0, 40.0, 30.0), (-4, 4, 2), 18),
    (22.8, 'w', (40.0, -40.0, 16.0), (-2, 4, 3), 22),
    (24.4, 'w', (18.0, -30.0, 5.0), (5, -10, 0.5), 24),
    (25.7, 'w', (24.0, -38.0, 6.0), (12, -20, 0.5), 26),
    (27.3, 'w', (-30.0, -120.0, 70.0), (0, 0, 0), 22),
    (29.0, 'w', (120.0, -150.0, 60.0), (-100, 30, 10), 22),
    (31.0, 'w', (110.0, -30.0, 40.0), (-120, 60, 15), 22),
    (32.6, 'w', (58.0, 64.0, 12.0), (30, 36, 3), 24),
    (33.6, 'w', (44.0, 62.0, 18.0), (28, 36, 3), 24),
    (34.6, 'w', (-40.0, -60.0, 45.0), (-100, -110, 20), 24),
    (35.4, 'tk', (-118.0, -22.0, 26.0), (-143.5, 0, 21), 28),
    (36.5, 'tk', (-128.0, -15.0, 22.5), (-143.5, 0, 20.9), 32),
    (37.8, 'w', (-60.0, -80.0, 20.0), (-40, -20, 3), 22),
    (END, 'k0', (-11.0, -22.0, 2.0), (-22.0, -5.0, 4.0), 16),
]
_M0 = None
def key_world(k, t):
    global _M0
    tk_, fr, p, q, ln = k; p = Vector(p); q = Vector(q)
    if fr == 'b': M = rb_matrix(t)
    elif fr == 'tk': M = tk_matrix(t)
    elif fr == 'k0':
        if _M0 is None: _M0 = tk_matrix(0.0).inverted()
        M = tk_matrix(t) @ _M0
    else: return p, q, ln
    return M @ p, M @ q, ln
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    t0, t1 = ts[i], ts[i + 1]; u = clamp((t - t0) / (t1 - t0), 0, 1)
    def tan(j):
        a_, b_ = max(0, j - 1), min(n - 1, j + 1)
        return (vs[b_] - vs[a_]) / (ts[b_] - ts[a_]) * (t1 - t0)
    m0, m1 = tan(i), tan(i + 1); u2, u3 = u * u, u * u * u
    return vs[i] * (2 * u3 - 3 * u2 + 1) + m0 * (u3 - 2 * u2 + u) + vs[i + 1] * (-2 * u3 + 3 * u2) + m1 * (u3 - u2)
def cam_at(t):
    ts = [k[0] for k in K]; W = [key_world(k, t) for k in K]
    p = herm(ts, [w[0] for w in W], t); q = herm(ts, [w[1] for w in W], t); ln = herm(ts, [Vector((w[2], 0, 0)) for w in W], t).x
    # inside the boat (keys 'b'), the camera leans with her (60 %)
    wb = sum(math.exp(-((t - k[0]) / 0.9) ** 2) for k in K if k[1] == 'b'); wb = clamp(wb, 0, 1)
    up = Vector((0, 0, 1)); th = rb_theta(t) * 0.6 * wb
    up = Vector((0, -math.sin(th), math.cos(th)))
    sh = Vector((0, 0, 0))
    if t > T_HIT: sh += shake(t, 0.45 * math.exp(-(t - T_HIT) / 0.6), 1.0, 11.0)
    if T_SHAKE - 0.2 < t < T_SHAKE + 1.2: sh += shake(t, 0.05, 2.0, 9.0)
    sh += shake(t, 0.06, 5.0, 0.8)                                       # a drone's slow drift
    return p + sh, q + sh * 0.5, ln, up

# ---- what everything does at time t
def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    p_, a_ = tk_pose(t); TK.location = p_; TK.rotation_euler = (0, 0, a_ + R(0.6) * math.sin(0.4 * t))
    M = rb_matrix(t); RB.matrix_world = Matrix.Translation(RB_PIV) @ (Matrix.Translation(-RB_PIV) @ M @ Matrix.Translation(RB_PIV))
    tw = t * 0.18
    for o in (RIVER, BOW_FOAM, HIT_FOAM, ROLL_FOAM, CG_WAKE, PD_WAKE, *BOW_WAVE): o['tw'] = tw
    for o in POUR: o['tw'] = t * 1.6
    BOW_FOAM['a'] = 1.0 if t < T_HIT else lerp(1.0, 0.25, ease_io((t - T_HIT) / 2.0))
    for o in BOW_WAVE: o['a'] = 1.0 if t < T_HIT else lerp(1.0, 0.0, ease_io((t - T_HIT) / 1.5)); o.hide_render = o['a'] < 0.02
    HIT_FOAM['a'] = ease_out((t - T_HIT) / 0.3) * (1 - ease_io((t - T_HIT - 2.5) / 3.0)) if t > T_HIT else 0.0
    ROLL_FOAM['a'] = ease_out((t - T_ROLL - 0.6) / 0.6) * (1 - 0.6 * ease_io((t - T_ROLL - 3.5) / 4.0)) if t > T_ROLL + 0.6 else 0.0
    broken = t > T_HIT + 0.06
    for o in BREAK: o.hide_render = broken
    for o in HOLE: o.hide_render = not broken
    HIT_SPLASH.at((-4.5, 2.0, 0.8), t - T_HIT)
    ROLL_SPLASH.at((-4.0, -4.0, 0.3), t - T_ROLL - 1.0)
    GLASS_BITS.at(M @ Vector((-6.0, 4.8, 2.9)), t - T_HIT)
    pa = ease_io((t - (T_BACK + 0.9)) / 0.8) * (1 - ease_io((t - T_ROLL) / 0.6))
    for o in POUR: o['a'] = pa; o.hide_render = pa < 0.01
    SUN.visible_glossy = not (33.5 <= t < 35.4)                          # the high pass looks straight down-sun: no big soft sun blob on the river
    lo = 1 - ease_io((t - T_ROLL) / 0.8)                               # power dies as she rolls (else the cabin lights glow up through the water)
    IN_LT.data.energy = 6500 * lo; UP_LT.data.energy = 3500 * lo; IN_LT.hide_render = UP_LT.hide_render = lo < 0.01
    FLOOD.hide_render = not (T_BACK + 1.0 < t < T_ROLL + 1.0); FLOOD.location.z = 1.52 + 0.9 * ease_io((t - T_BACK - 1.0) / 7.0)
    # tables slide toward the river side as she lists
    for g, cx, cy in TABLES:
        sl = clamp(rb_theta(t) - R(4), 0, R(30)) * 9.0
        ymin = 7.9 if -13 < cx < 4 else 6.2                                # stop short of the river-side wall (and the bow)
        g.location = (cx + 0.3 * h1(cx + cy) * sl, max(ymin, cy - sl * (0.6 + 0.4 * h1(cx * 3 + cy))), 1.5); g.rotation_euler = (0, 0, 0.25 * sl * (h1(cx + 2 * cy) - 0.5))
    # people
    for i, p in enumerate(GUESTS):
        show_fig(p, t < 17.0); pose(p, 'brace' if t > T_HIT else 'stand', t)
    for i, p in enumerate(WALKERS):
        y_ = 23.4 + 1.8 * i + 0.9 * min(t, T_HIT); p['root'].location = (6 + 1.0 * (i % 2), y_, 3.4)
        face(p, math.pi / 2 if t < T_HIT + 0.3 else -math.pi / 2 + 0.3 * (h1(i) - 0.5))
        pose(p, 'walk' if t < T_HIT else 'brace', t)
    show_fig(CREW, t < 18.0)
    if t < T_SHAKE: CREW['root'].location = (-6.5, RB_CY + 1.0, 1.5); face(CREW, 0.2); pose(CREW, 'stand', t)
    elif t < T_POUR: face(CREW, 0.2 - 1.6 * ease_io((t - T_SHAKE) / 0.6)); pose(CREW, 'stand', t)
    else:
        k = ease_io((t - T_POUR) / 3.0); CREW['root'].location = (-6.5 - 3 * k, RB_CY + 1.0 + 5.0 * k, 1.5); face(CREW, math.atan2(5.0, -3.0)); pose(CREW, 'run' if k < 1 else 'stand', t)
    for p in DINERS: show_fig(p, False)
    for i, p in enumerate(HIGH):
        on = 17.0 < t < T_ROLL + 0.9; show_fig(p, on)
        if on: pose(p, 'climb' if t < 19.3 else 'brace', t)
    for i, p in enumerate(POLICE):
        k = clamp((t - (T_POLICE - 1.2)) / 4.5, 0, 1)
        p['root'].location = (lerp(70 + 6 * i, 6 + 4 * i, k), 24 + 2 * (i % 2), 3.4); face(p, math.pi if k < 1 else -math.pi / 2)
        pose(p, 'run' if 0 < k < 1 else 'stand', t)
    for i, p in enumerate(SWIM):
        on = t > T_ROLL + 0.9; show_fig(p, on)
        if on:
            k = ease_out((t - T_ROLL - 0.9) / 1.5)
            p['root'].location = (-12 + 3.4 * i + 2 * h1(i), -6 - 9 * h1(i + 30) - 3 * k, -1.25 + 0.08 * math.sin(2 * math.pi * 0.6 * t + i)); pose(p, 'tread', t)
    for i, p in enumerate(ONTOP):
        on = t > T_ROLL + 2.3; show_fig(p, on)
        if on:                                                           # standing on the dock-side hull plating, now facing the sky
            q = M @ Vector((-24 + 7.5 * i, RB_CY + 8.0, -0.35 + 0.5 * h1(i))); p['root'].location = q; pose(p, 'wave' if i % 3 == 0 else 'stand', t)
    # rescue boats come in from the river; two rescuers jump from the police boat; ambulances flash on the wharf
    ka = ease_out((t - (T_ROLL - 0.6)) / 3.0)
    CG_BOAT.location = (lerp(-20, -2, ka), lerp(-140, -24, ka), 0.0 + 0.1 * math.sin(2.1 * t)); CG_BOAT.rotation_euler = (0.03 * math.sin(1.7 * t), 0, math.atan2(116, 18) if ka < 0.98 else R(40))
    PD_BOAT.location = (lerp(70, 14, ka), lerp(-130, -26, ka), 0.0 + 0.1 * math.sin(1.9 * t + 1)); PD_BOAT.rotation_euler = (0.03 * math.sin(1.5 * t), 0, math.atan2(104, -56) if ka < 0.98 else R(120))
    CG_WAKE['a'] = 1 - ka * 0.8; PD_WAKE['a'] = 1 - ka * 0.8
    for b_, lt in ((CG_BOAT, CG_LT), (PD_BOAT, PD_LT)): flash(lt, t > T_ROLL - 0.6, t, 2.5)
    for i, p in enumerate(RESC):
        on = i < 2 and t > T_JUMP - 0.6; show_fig(p, on)
        if on:
            u = (t - T_JUMP) / 0.9; base = PD_BOAT.matrix_world @ Vector((-2.6 + 1.2 * i, 1.3, 0.95))
            if u < 0: p['root'].location = base; pose(p, 'stand', t)
            else:
                uu = min(u, 1.0); p['root'].location = base + Vector((0.6 * uu, 4.0 * uu, 2.2 * uu - 4.4 * uu * uu * 1.0 - (1.2 if u > 1 else 0)))
                pose(p, 'jump' if u < 1 else 'tread', t)
            face(p, math.pi / 2)
    for k_, js in enumerate(JUMP_SPLASH): js.at(PD_BOAT.location + Vector((-0.6 + 1.6 * k_, 5.8, -0.2)), t - T_JUMP - 0.9)
    for g, l1, l2 in AMBS:
        flash(l1, t > 22.0, t, 2.0, 0.0); flash(l2, t > 22.0, t, 2.0, math.pi); show_fig({'root': g}, t > 21.0)
    # camera
    cp, ct, ln, up = cam_at(t); look(cp, ct, ln, 8.0 if not (9.8 < t < 18.0) else 4.0, up=up)
    bpy.context.view_layer.update()

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear(); CAM.data.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, up = cam_at(tt_); look(cp, ct, ln, up=up); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
if os.environ.get('TOPCAM'):                                             # debug: a top-down plan view of the whole layout
    _frame0 = frame
    def frame(f):
        _frame0(f); CAM.animation_data_clear(); CAM.data.type = 'ORTHO'; CAM.data.ortho_scale = float(os.environ['TOPCAM'])
        CAM.location = (-30, -20, 600); CAM.rotation_mode = 'XYZ'; CAM.rotation_euler = (0, 0, 0); CAM.data.dof.use_dof = False
if os.environ.get('CHKCAM'):                                             # debug: a fixed close-up camera for clipping checks
    _frame1 = frame; _cks = [[float(v) for v in c.split(',')] for c in os.environ['CHKCAM'].split(';')]
    def frame(f):
        _frame1(f); CAM.animation_data_clear(); c = _cks[int(os.environ.get('CHKI', '0'))]
        look(Vector(c[:3]), Vector(c[3:6]), c[6], 11.0)
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

