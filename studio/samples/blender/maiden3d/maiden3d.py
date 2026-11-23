# The iron maiden myth: a spiked door slams in a torchlit dungeon that turns out to be a museum diorama; the 1793 story of a 1515 coin forger,
# 278 years with no record, a maiden pieced together from museum parts, a copy crated for the 1893 Chicago World's Fair, and a real one found under leaves in Baghdad, 2003. One continuous shot.
#   python3 maiden3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join(HERE, 'assets', n), os.path.join('/root/vt/n38/g9', n), os.path.join('/root/vt/assets', n)) if os.path.exists(p_))
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

def ramp_v(nt, fac, a_, b_):
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = a_; mr.inputs['From Max'].default_value = b_
    mr.interpolation_type = 'SMOOTHSTEP'; nt.links.new(fac, mr.inputs['Value']); return mr.outputs['Result']


# ================================================================ the iron maiden (built in parts so it can fly apart and come back together)
def iron_mat(name, rust=0.3, base=(0.05, 0.05, 0.055), rust_col=(0.085, 0.036, 0.017), seed=0.0, paint=None):
    """dark forged iron with rust blooms and pitting; paint (rgb) = old paint left in the low spots"""
    m = mat(name, base, 0.42, 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    co = coord(nt, 'Object'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed * 3.1, seed * 1.7, seed * 0.9); nt.links.new(co, mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 7.0, 10.0, 0.4); fine = tnoise(nt, mp.outputs['Vector'], 38.0, 4.0)
    f_ = math_(nt, 'ADD', math_(nt, 'MULTIPLY', big, 0.8), math_(nt, 'MULTIPLY', fine, 0.2))
    rf = ramp_v(nt, f_, 0.62 - rust * 0.25, 0.70 - rust * 0.18)                     # 0 = bare iron, 1 = rust
    rc = mixc(nt, tnoise(nt, mp.outputs['Vector'], 14.0, 6.0), rust_col, tuple(c * 0.55 for c in rust_col))
    ic = mixc(nt, fine, base, tuple(c * 1.6 for c in base))
    if paint: ic = mixc(nt, ramp_v(nt, big, 0.30, 0.42), paint, ic)
    nt.links.new(mixc(nt, rf, ic, rc), b.inputs['Base Color'])
    mt = nt.nodes.new('ShaderNodeMapRange'); mt.inputs['To Min'].default_value = 0.85; mt.inputs['To Max'].default_value = 0.05; nt.links.new(rf, mt.inputs['Value']); nt.links.new(mt.outputs['Result'], b.inputs['Metallic'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.38; mr.inputs['To Max'].default_value = 0.92; nt.links.new(rf, mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.004
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', tnoise(nt, mp.outputs['Vector'], 90.0, 3.0), 0.6), math_(nt, 'MULTIPLY', rf, 0.6)), bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal']); return m


def arc_shell(name, prof, a0, a1, seg, ex, ey, m, thick=0.025, parent=None, origin=(0, 0, 0)):
    """open surface of revolution between angles a0..a1 (degrees, from +x toward +y), stretched ex/ey; solidified inward"""
    o_ = Vector(origin); vs = []; fs = []
    for r_, z_ in prof:
        for k in range(seg + 1):
            an = math.radians(a0 + (a1 - a0) * k / seg); vs.append(Vector((r_ * ex * math.cos(an), r_ * ey * math.sin(an), z_)) - o_)
    w = seg + 1
    for i in range(len(prof) - 1):
        for k in range(seg): fs.append((i * w + k, (i + 1) * w + k, (i + 1) * w + k + 1, i * w + k + 1))
    o = mesh(name, vs, fs, m, parent, loc=o_)
    sd = o.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = thick; sd.offset = -1.0; sd.use_even_offset = True
    bv = o.modifiers.new('bv', 'BEVEL'); bv.width = 0.004; bv.segments = 2; bv.limit_method = 'ANGLE'
    return o


def prof_r(prof, z):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1: return lerp(r0, r1, (z - z0) / max(1e-6, z1 - z0))
    return prof[-1][0] if z > prof[-1][1] else prof[0][0]


MAIDEN_PROF = [(0.40, 0.10), (0.445, 0.16), (0.455, 0.30), (0.44, 0.52), (0.41, 0.80), (0.375, 1.08), (0.362, 1.26), (0.385, 1.40), (0.39, 1.48)]
MAIDEN_TOP = [(0.39, 1.48), (0.375, 1.53), (0.31, 1.58), (0.21, 1.615), (0.13, 1.63)]
EX, EY = 1.0, 0.80
DOOR_A = 60.0                                     # each door spans 60 degrees of the front


def build_maiden(tag, m_iron, m_dark=None, base_m=None, spikes=True, head=True, face_rust=0.4):
    """returns dict: root (feet at origin, facing -y), parts {name: obj} parented to root, doors (L, R) with hinge origins"""
    root = empty('maiden_' + tag); P = {}
    m_dark = m_dark or m_iron
    # the back shell (240 degrees behind the doors) and the doors (front 120 degrees, split down the middle)
    back = arc_shell(f'{tag}_back', MAIDEN_PROF, -90 + DOOR_A, 270 - DOOR_A, 40, EX, EY, m_iron, 0.03, root); P['back'] = back
    doors = []
    for side, (a0, a1, ah) in (('L', (270 - DOOR_A, 270.0, 270 - DOOR_A)), ('R', (-90.0, -90 + DOOR_A, -90 + DOOR_A))):
        rh = 0.455; hp = Vector((rh * EX * math.cos(math.radians(ah)), rh * EY * math.sin(math.radians(ah)), 0.0))
        dpiv = empty(f'{tag}_door{side}', root, loc=hp); P['door' + side] = dpiv
        d = arc_shell(f'{tag}_doorpanel{side}', [(r_ + 0.004, z_) for r_, z_ in MAIDEN_PROF], a0, a1, 14, EX, EY, m_iron, 0.03, dpiv, origin=hp)
        d.location = (0, 0, 0)
        # iron bands and rivets on the door face
        for zb in (0.22, 0.62, 1.02, 1.38):
            rb = prof_r(MAIDEN_PROF, zb) + 0.012
            pts = [Vector((rb * EX * math.cos(math.radians(a0 + (a1 - a0) * k / 10)), rb * EY * math.sin(math.radians(a0 + (a1 - a0) * k / 10)), zb)) - hp for k in range(11)]
            tube(f'{tag}_band{side}{zb}', pts, 0.016, m_dark, dpiv, seg=8)
            for k in range(1, 10, 2):
                an = math.radians(a0 + (a1 - a0) * k / 10); pr = Vector(((rb + 0.012) * EX * math.cos(an), (rb + 0.012) * EY * math.sin(an), zb)) - hp
                prim('uv_sphere', f'{tag}_rv{side}{zb}{k}', m_dark, dpiv, loc=pr, segments=10, ring_count=6, radius=0.013)
        # the spikes on the inside: rows pointing in toward the body
        if spikes:
            for zi, zs in enumerate((0.32, 0.55, 0.78, 1.0, 1.22)):
                n_ = 3 if zi % 2 == 0 else 2
                for k in range(n_):
                    an = math.radians(a0 + (a1 - a0) * (k + 0.5 + (0 if zi % 2 == 0 else 0.5)) / (n_ + (0 if zi % 2 == 0 else 1)))
                    rr = prof_r(MAIDEN_PROF, zs) - 0.03; pin = Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), zs))
                    inward = -Vector((math.cos(an) / EX, math.sin(an) / EY, 0)).normalized()
                    sp = prim('cone', f'{tag}_sp{side}{zi}{k}', m_dark, dpiv, loc=pin - hp + inward * 0.075, vertices=10, radius1=0.016, radius2=0.0015, depth=0.15)
                    sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = inward.to_track_quat('Z', 'Y')
        # the hinge knuckles on the outer edge
        for zk in (0.2, 0.55, 0.9, 1.25):
            rk = prof_r(MAIDEN_PROF, zk) + 0.012; pk = Vector((rk * EX * math.cos(math.radians(ah)), rk * EY * math.sin(math.radians(ah)), zk)) - hp
            prim('cylinder', f'{tag}_hk{side}{zk}', m_dark, dpiv, loc=pk, vertices=14, radius=0.024, depth=0.12)
        # a ring handle near the meeting edge, and the hasp
        an = math.radians(a1 - 10 if side == 'L' else a0 + 10); rr = prof_r(MAIDEN_PROF, 0.95) + 0.03
        hp2 = Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), 0.95)) - hp
        prim('uv_sphere', f'{tag}_boss{side}', m_dark, dpiv, loc=hp2, segments=14, ring_count=8, radius=0.022, scale=(1, 0.6, 1))
        rg = tube(f'{tag}_ring{side}', [hp2 + Vector((0.035 * math.sin(2 * math.pi * k / 16), -0.008, -0.04 + 0.035 * math.cos(2 * math.pi * k / 16))) for k in range(17)], 0.006, m_dark, dpiv, seg=6, caps=False)
        if side == 'R':
            an = math.radians(-90 + 3); rr = prof_r(MAIDEN_PROF, 0.72) + 0.02
            box(f'{tag}_hasp', (0.05, 0.012, 0.14), Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), 0.72)) - hp, m_dark, bv=0.004, parent=dpiv)
        doors.append(dpiv)
    # back-shell bands, rivets and spikes
    for zb in (0.22, 0.62, 1.02, 1.38):
        rb = prof_r(MAIDEN_PROF, zb) + 0.01; a0, a1 = -90 + DOOR_A, 270 - DOOR_A
        pts = [(rb * EX * math.cos(math.radians(a0 + (a1 - a0) * k / 30)), rb * EY * math.sin(math.radians(a0 + (a1 - a0) * k / 30)), zb) for k in range(31)]
        tube(f'{tag}_bandB{zb}', pts, 0.016, m_dark, back, seg=8)
        for k in range(1, 30, 3):
            an = math.radians(a0 + (a1 - a0) * k / 30)
            prim('uv_sphere', f'{tag}_rvB{zb}{k}', m_dark, back, loc=((rb + 0.012) * EX * math.cos(an), (rb + 0.012) * EY * math.sin(an), zb), segments=10, ring_count=6, radius=0.013)
    if spikes:
        for zi, zs in enumerate((0.45, 0.85, 1.2)):
            for k in range(3):
                an = math.radians(90 + (k - 1) * 28); rr = prof_r(MAIDEN_PROF, zs) - 0.035
                pin = Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), zs)); inward = -Vector((math.cos(an) / EX, math.sin(an) / EY, 0)).normalized()
                sp = prim('cone', f'{tag}_spB{zi}{k}', m_dark, back, loc=pin + inward * 0.075, vertices=10, radius1=0.016, radius2=0.0015, depth=0.15)
                sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = inward.to_track_quat('Z', 'Y')
    # shoulders and the cowl
    top = lathe(f'{tag}_top', MAIDEN_TOP, 48, m_iron, root); top.scale = (EX, EY, 1); P['top'] = top
    sd = top.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.02
    # base: a heavy iron foot ring and a plank floor inside
    ft = lathe(f'{tag}_foot', [(0.0, 0.0), (0.47, 0.0), (0.48, 0.02), (0.475, 0.10), (0.44, 0.11), (0.0, 0.11)], 48, m_dark, root); ft.scale = (EX, EY, 1); P['foot'] = ft
    bevel(ft, 0.006, 2)
    if head:
        hd = empty(f'{tag}_head', root, loc=(0, 0, 1.60)); P['head'] = hd
        lathe(f'{tag}_neck', [(0.0, 0.0), (0.11, 0.0), (0.10, 0.06), (0.095, 0.08), (0.0, 0.08)], 32, m_iron, hd)
        build_face(tag, hd, m_iron, m_dark)
    P['root'] = root; P['doors'] = doors
    if base_m:
        pl = box(f'{tag}_plinth', (1.15, 0.95, 0.10), (0, 0, -0.05), base_m, bv=0.01, parent=root); P['plinth'] = pl
    return P


def face_mesh(name, m, parent, loc, R=(0.118, 0.122, 0.158), seg=72, rings=56):
    """the head as one sculpted surface: a calm woman's face hammered from iron (brow, closed eyes, nose, lips, chin)"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    def g(x, z, cx, cz, wx, wz): return math.exp(-((x - cx) / wx) ** 2 - ((z - cz) / wz) ** 2)
    for v in bm.verts:
        n = v.co.copy(); x, y, z = n.x * R[0], n.y * R[1], n.z * R[2]
        zz = z + 0.19 - 0.0                                                         # in the old face coordinates (head origin at the neck)
        x *= 1.0 - 0.22 * smooth(0.17, 0.07, zz) - 0.05 * smooth(0.12, 0.26, zz)    # narrower jaw and temples
        f = max(0.0, -n.y) ** 1.5                                                   # features only on the front
        d = 0.0
        for sx in (-1, 1):
            d += 0.016 * g(x, zz, sx * 0.040, 0.233, 0.024, 0.008)                  # brow ridge
            d -= 0.026 * g(x, zz, sx * 0.041, 0.210, 0.019, 0.013)                  # eye socket
            d += 0.016 * g(x, zz, sx * 0.041, 0.206, 0.015, 0.0062)                # closed lid
            d += 0.010 * g(x, zz, sx * 0.056, 0.176, 0.022, 0.018)                  # cheekbone
            d += 0.010 * g(x, zz, sx * 0.0135, 0.163, 0.006, 0.006)                 # nostril wing
        d += 0.042 * g(x, zz, 0.0, 0.172, 0.0105, 0.013) + 0.022 * g(x, zz, 0.0, 0.200, 0.0075, 0.024)   # nose tip, bridge
        d += 0.014 * g(x, zz, 0.0, 0.134, 0.022, 0.0058) + 0.015 * g(x, zz, 0.0, 0.119, 0.019, 0.0065)   # upper, lower lip
        d -= 0.008 * g(x, zz, 0.0, 0.1265, 0.025, 0.0024) - 0.006 * g(x, zz, 0.0, 0.147, 0.006, 0.008)   # the line of the mouth, the groove under the nose (-)
        d += 0.016 * g(x, zz, 0.0, 0.094, 0.021, 0.015)                             # chin
        v.co = Vector((x, y, z)) + n * d * f
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return obj(name, me, m, loc, parent)


def build_face(tag, hd, m_iron, m_dark):
    """the maiden's head under a hooded cowl"""
    face_mesh(f'{tag}_face', m_iron, hd, (0, 0.0, 0.19))
    a0, a1 = -90 + 50, 270 - 50
    cowl = arc_shell(f'{tag}_cowl', [(0.015, 0.372), (0.075, 0.362), (0.118, 0.335), (0.142, 0.29), (0.150, 0.23), (0.148, 0.16), (0.152, 0.10), (0.18, 0.05), (0.24, 0.015), (0.31, -0.005)],
                     a0, a1, 40, 1.0, 1.0, m_iron, 0.014, hd)
    subsurf(cowl, 1)
    tube(f'{tag}_collar', [(0.215 * math.cos(math.radians(k * 15)) * EX, 0.215 * math.sin(math.radians(k * 15)) * EY, -0.005) for k in range(25)], 0.016, m_dark, hd, seg=8)

# ================================================================ set: a museum hall (x -4..24) with four exhibits, a window out to a Baghdad courtyard (x 24..48)
def brick_mat(name, c1, c2, mortar, scale=1.0, rough=0.85, plane='xz', bump=0.6, row=0.5, w=0.5, mortar_w=0.02, seed=0.0, wob_=0.0):
    """bricks / stone blocks / planks on a wall or floor: object coords in metres; plane picks the two axes the pattern runs in"""
    m = mat(name, c1, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    if plane == 'xz': mp.inputs['Rotation'].default_value = (math.pi / 2, 0, 0)
    elif plane == 'yz': mp.inputs['Rotation'].default_value = (math.pi / 2, 0, math.pi / 2)
    mp.inputs['Location'].default_value = (seed, seed * 0.7, 0)
    br = nt.nodes.new('ShaderNodeTexBrick')
    if wob_:
        nzv = nt.nodes.new('ShaderNodeTexNoise'); nzv.inputs['Scale'].default_value = 2.5; nt.links.new(mp.outputs['Vector'], nzv.inputs['Vector'])
        sub = nt.nodes.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; nt.links.new(nzv.outputs['Color'], sub.inputs[0]); sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        sc_ = nt.nodes.new('ShaderNodeVectorMath'); sc_.operation = 'SCALE'; nt.links.new(sub.outputs[0], sc_.inputs[0]); sc_.inputs['Scale'].default_value = wob_
        ad = nt.nodes.new('ShaderNodeVectorMath'); ad.operation = 'ADD'; nt.links.new(mp.outputs['Vector'], ad.inputs[0]); nt.links.new(sc_.outputs[0], ad.inputs[1])
        nt.links.new(ad.outputs[0], br.inputs['Vector'])
    else: nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
    br.inputs['Scale'].default_value = scale; br.inputs['Mortar Size'].default_value = mortar_w; br.inputs['Brick Width'].default_value = w; br.inputs['Row Height'].default_value = row
    br.inputs['Color1'].default_value = (*c1, 1); br.inputs['Color2'].default_value = (*c2, 1); br.inputs['Mortar'].default_value = (*mortar, 1)
    br.inputs['Mortar Smooth'].default_value = 0.3; br.offset = 0.5
    nz = tnoise(nt, mp.outputs['Vector'], 6.0, 8.0); dirt = tnoise(nt, mp.outputs['Vector'], 1.3, 4.0)
    col = mixc(nt, math_(nt, 'MULTIPLY', nz, 0.45), br.outputs['Color'], tuple(c * 0.55 for c in c2))
    col = mixc(nt, ramp_v(nt, dirt, 0.45, 0.75), col, tuple(c * 0.6 for c in c1))
    nt.links.new(col, b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.02
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', br.outputs['Fac'], -1.0), math_(nt, 'MULTIPLY', tnoise(nt, mp.outputs['Vector'], 25.0, 6.0), 0.25)), bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal']); return m


def text3d(name, body, size, loc, rot, m, parent=None, extrude=0.004, align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude; cu.align_x = align; cu.align_y = 'CENTER'
    try: cu.font = bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf')
    except Exception: pass
    o = bpy.data.objects.new(name, cu); S.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; o.data.materials.append(m)
    if parent: o.parent = parent
    return o


# ---------------------------------------------------------------- materials
M_IRON = iron_mat('iron', 0.32); M_IRDK = iron_mat('irondk', 0.22, base=(0.035, 0.035, 0.04), seed=2.0)
M_IRON2 = iron_mat('iron2', 0.42, seed=5.0); M_IRON4 = iron_mat('iron4', 0.62, seed=9.0, rust_col=(0.10, 0.045, 0.02))
M_STONE = brick_mat('stone', (0.11, 0.10, 0.09), (0.065, 0.06, 0.055), (0.03, 0.028, 0.026), 1.4, plane='xz', bump=1.6, row=0.36, w=0.55, mortar_w=0.05, wob_=0.12)
M_STONEY = brick_mat('stoney', (0.11, 0.10, 0.09), (0.065, 0.06, 0.055), (0.03, 0.028, 0.026), 1.4, plane='yz', bump=1.6, row=0.36, w=0.55, mortar_w=0.05, seed=3.0, wob_=0.12)
M_FLAG = brick_mat('flag', (0.13, 0.12, 0.11), (0.09, 0.085, 0.08), (0.035, 0.032, 0.03), 0.9, plane='xy', bump=0.7, row=0.55, w=0.7, mortar_w=0.03, seed=1.0)
M_WOODF = brick_mat('woodfloor', (0.30, 0.17, 0.08), (0.24, 0.13, 0.06), (0.12, 0.06, 0.03), 1.0, rough=0.35, plane='xy', bump=0.25, row=0.16, w=1.8, mortar_w=0.006, seed=2.0)
M_WOODF.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.35
M_PLASTER = noisy(mat('plaster', (0.52, 0.48, 0.42), 0.8), 3.0, 0.12)
M_WAINS = noisy(mat('wains', (0.12, 0.07, 0.04), 0.45, coat=0.3), 20.0, 0.15)
M_CEIL = noisy(mat('ceil', (0.30, 0.29, 0.27), 0.9), 2.0, 0.1)
M_BRASS = mat('brass', (0.78, 0.55, 0.22), 0.28, 1.0)
M_VELVET = mat('velvet', (0.32, 0.015, 0.03), 0.75, sheen=0.8)
M_WOOD = noisy(mat('wood', (0.26, 0.14, 0.065), 0.55, coat=0.15), 14.0, 0.3)
M_WOODRAW = noisy(mat('woodraw', (0.40, 0.29, 0.17), 0.85), 10.0, 0.3)
M_PAPER = noisy(mat('paper', (0.78, 0.70, 0.55), 0.8), 8.0, 0.08)
M_INK = mat('ink', (0.01, 0.01, 0.012), 0.3)
M_GOLD = mat('gold', (0.85, 0.62, 0.25), 0.25, 1.0); M_SILV = mat('silver', (0.72, 0.72, 0.74), 0.3, 1.0)
M_WAX = mat('wax', (0.85, 0.80, 0.68), 0.5, trans=0.2, sheen=0.3)
M_FLAME = emis_mix('flame', (1.0, 0.55, 0.18), 22.0)
M_STRAW = noisy(mat('straw', (0.55, 0.42, 0.18), 0.8), 30.0, 0.3)
M_PLAQ = mat('plaq', (0.06, 0.05, 0.045), 0.5); M_GILT = mat('gilt', (0.9, 0.7, 0.32), 0.3, 1.0)
M_BLACK = mat('blackm', (0.02, 0.02, 0.02), 0.6)
M_GLASS = mat('glass', (0.9, 0.95, 1.0), 0.02, trans=1.0, ior=1.45)
M_POSTER = mat('poster', (0.80, 0.70, 0.50), 0.8)
M_RED = mat('red', (0.55, 0.04, 0.04), 0.6); M_WHITE = mat('white', (0.85, 0.84, 0.80), 0.6); M_BLUE = mat('blue', (0.05, 0.10, 0.35), 0.6)
M_SAND = brick_mat('sandg', (0.42, 0.33, 0.22), (0.37, 0.29, 0.19), (0.30, 0.23, 0.15), 0.7, plane='xy', bump=0.3, row=0.6, w=0.6, mortar_w=0.015, seed=4.0)
M_SANDW = brick_mat('sandw', (0.66, 0.54, 0.38), (0.60, 0.48, 0.33), (0.50, 0.40, 0.28), 1.2, plane='yz', bump=0.4, row=0.3, w=0.6, mortar_w=0.012, seed=6.0)
M_SANDWX = brick_mat('sandwx', (0.66, 0.54, 0.38), (0.60, 0.48, 0.33), (0.50, 0.40, 0.28), 1.2, plane='xz', bump=0.4, row=0.3, w=0.6, mortar_w=0.012, seed=7.0)
M_PALM = noisy(mat('palm', (0.30, 0.22, 0.13), 0.9), 18.0, 0.35); M_FROND = noisy(mat('frond', (0.10, 0.22, 0.06), 0.6, sheen=0.2), 12.0, 0.3)
M_LEAF = [noisy(mat(f'leaf{i}', c, 0.75), 20.0, 0.3) for i, c in enumerate(((0.42, 0.28, 0.09), (0.30, 0.18, 0.06), (0.50, 0.38, 0.12), (0.22, 0.14, 0.05)))]
for m_ in M_LEAF: m_.node_tree.nodes['Principled BSDF'].inputs['Subsurface Weight'].default_value = 0.0

# ---------------------------------------------------------------- the museum hall
HALL = empty('hall')
box('hfloor', (28.4, 13.0, 0.2), (10.0, -0.9, -0.1), M_WOODF, parent=HALL)
box('hback', (28.4, 0.3, 6.0), (10.0, 5.55, 3.0), M_PLASTER, parent=HALL)
box('hwains', (28.4, 0.06, 1.0), (10.0, 5.38, 0.5), M_WAINS, bv=0.01, parent=HALL)
box('hfront', (28.4, 0.3, 6.0), (10.0, -7.55, 3.0), M_PLASTER, parent=HALL)
box('hleft', (0.3, 13.0, 6.0), (-4.35, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hceil', (28.4, 13.4, 0.3), (10.0, -0.9, 6.15), M_CEIL, parent=HALL)
for xb in range(-3, 24, 3): box(f'beam{xb}', (0.3, 13.0, 0.35), (xb + 0.5, -0.9, 5.83), M_WOOD, bv=0.01, parent=HALL)
# the end wall at x = 24 with a tall arched window (an opening the camera flies through)
WX = 24.0; WY0, WY1, WZ0, WZ1 = -1.3, 1.3, 1.0, 4.2
box('hend_l', (0.4, 7.4 - 1.3 + 0.0, 6.0), (WX, -7.4 + (7.4 - 1.3) / 2 - 0.3, 3.0), M_PLASTER, parent=HALL)
box('hend_r', (0.4, 5.7 - 1.3, 6.0), (WX, 1.3 + (5.7 - 1.3) / 2, 3.0), M_PLASTER, parent=HALL)
box('hend_b', (0.4, 2.6, 1.0), (WX, 0.0, 0.5), M_PLASTER, parent=HALL)
box('hend_t', (0.4, 2.6, 6.0 - WZ1), (WX, 0.0, WZ1 + (6.0 - WZ1) / 2), M_PLASTER, parent=HALL)
for s_ in (-1, 1): box(f'wjamb{s_}', (0.5, 0.12, WZ1 - WZ0 + 0.1), (WX, s_ * 1.36, (WZ0 + WZ1) / 2), M_WOOD, bv=0.01, parent=HALL)
box('wsill', (0.7, 2.9, 0.1), (WX, 0, WZ0 - 0.05), M_WOOD, bv=0.01, parent=HALL); box('whead', (0.5, 2.9, 0.12), (WX, 0, WZ1 + 0.05), M_WOOD, bv=0.01, parent=HALL)
for s_ in (-1, 1):                                          # the casements, swung open outward
    cp_ = empty(f'case{s_}', HALL, loc=(WX + 0.2, s_ * 1.3, WZ0)); cp_.rotation_euler = (0, 0, s_ * R(70))
    box(f'casef{s_}', (0.05, 1.3, WZ1 - WZ0), (0, -s_ * 0.65, (WZ1 - WZ0) / 2), M_WOOD, parent=cp_)
    for k in range(1, 4): box(f'casem{s_}{k}', (0.06, 1.3, 0.04), (0, -s_ * 0.65, (WZ1 - WZ0) * k / 4), M_WOOD, parent=cp_)
    box(f'caseg{s_}', (0.01, 1.2, WZ1 - WZ0 - 0.1), (0, -s_ * 0.65, (WZ1 - WZ0) / 2), M_GLASS, parent=cp_)
# museum track lights (fixtures) along a rail, one per exhibit
RAIL = box('rail', (26.0, 0.08, 0.06), (10.0, 0.4, 5.55), M_BLACK, parent=HALL)
MUSEUM_LIGHTS = []
def track_spot(x, target, e=900, size=0.12):
    p = Vector((x, 0.4, 5.45)); can = prim('cylinder', f'can{x}', M_BLACK, HALL, loc=p, vertices=16, radius=0.07, depth=0.22)
    can.rotation_mode = 'QUATERNION'; can.rotation_quaternion = (Vector(target) - p).to_track_quat('-Z', 'Y')
    lt = light_at(f'spot{x}', 'SPOT', p, target, e, (1.0, 0.92, 0.80), size); lt.data.spot_size = R(48); lt.data.spot_blend = 0.6
    MUSEUM_LIGHTS.append((lt, e)); return lt
for xs, tg in ((-1.4, (0, 2.0, 1.2)), (1.4, (0, 2.0, 1.2)), (6.4, (7.0, 3.0, 0.9)), (8.6, (7.8, 5.2, 2.8)), (12.4, (13.0, 2.8, 1.0)), (14.0, (13.4, 2.8, 1.2)),
               (18.4, (19.0, 2.8, 1.0)), (20.0, (19.0, 2.6, 1.3))):
    track_spot(xs, tg)
for k, xa in enumerate((2.0, 9.0, 16.0, 22.0)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 350, (1.0, 0.93, 0.84), 3.0), 350))

# ---------------------------------------------------------------- exhibit 1: the dungeon diorama (x = 0)
DUN = empty('dungeon')
box('dstage', (4.8, 3.9, 0.3), (0, 1.85, 0.15), M_FLAG, bv=0.02, parent=DUN)
box('dback', (4.8, 0.4, 3.9), (0, 3.95, 0.3 + 1.95), M_STONE, parent=DUN)
for s_ in (-1, 1): box(f'dside{s_}', (0.4, 3.9, 3.9), (s_ * 2.4, 1.85, 0.3 + 1.95), M_STONEY, parent=DUN)
box('dlintel', (5.2, 0.5, 0.5), (0, 0.0, 4.15), M_STONE, bv=0.02, parent=DUN)
for s_ in (-1, 1):                                          # stone pillars at the front corners (the diorama's frame)
    box(f'dpil{s_}', (0.5, 0.5, 4.4), (s_ * 2.4, 0.0, 2.2), M_STONEY, bv=0.02, parent=DUN)
g0_ = random.Random(5)
# a barred window high on the back wall, moonlight
box('dwin', (0.7, 0.1, 0.5), (0.0, 3.76, 3.1), M_BLACK, parent=DUN)
for k in range(4): tube(f'dbar{k}', [(-0.25 + k * 0.166, 3.72, 2.85), (-0.25 + k * 0.166, 3.72, 3.35)], 0.014, M_IRDK, DUN, seg=8)
MOON = light_at('moon', 'AREA', (0.0, 3.6, 3.1), (0.0, 1.0, 0.6), 90, (0.55, 0.68, 1.0), 0.6)
# chains and shackles on the back wall
def chain(name, top, n, parent, m, link=0.055):
    for k in range(n):
        p = Vector(top) + Vector((0, 0, -k * link * 1.55))
        bmt = bpy.data.meshes.new(f'{name}{k}'); bm = bmesh.new(); seg_ = 12; ring = 6; R0, r0 = link * 0.55, link * 0.16
        for i in range(seg_):
            u = 2 * math.pi * i / seg_
            for j in range(ring):
                v = 2 * math.pi * j / ring; c_ = Vector((math.cos(u) * (R0 + r0 * math.cos(v)) * 0.6, r0 * math.sin(v), math.sin(u) * (R0 + r0 * math.cos(v))))
                bm.verts.new(c_)
        bm.verts.ensure_lookup_table()
        for i in range(seg_):
            for j in range(ring): bm.faces.new([bm.verts[i * ring + j], bm.verts[((i + 1) % seg_) * ring + j], bm.verts[((i + 1) % seg_) * ring + (j + 1) % ring], bm.verts[i * ring + (j + 1) % ring]])
        bm.to_mesh(bmt); bm.free()
        for pp in bmt.polygons: pp.use_smooth = True
        o = obj(f'{name}{k}', bmt, m, p, parent); o.rotation_euler = (0, 0, (math.pi / 2) * (k % 2))
for s_ in (-1, 1):
    prim('cylinder', f'ring{s_}', M_IRDK, DUN, loc=(s_ * 1.3, 3.72, 2.9), rot=(R(90), 0, 0), vertices=16, radius=0.045, depth=0.05)
    chain(f'chain{s_}', (s_ * 1.3, 3.70, 2.83), 14, DUN, M_IRDK)
    tube(f'shack{s_}', [(s_ * 1.3 + 0.06 * math.cos(2 * math.pi * k / 14), 3.70, 1.62 + 0.06 * math.sin(2 * math.pi * k / 14)) for k in range(15)], 0.013, M_IRDK, DUN, seg=8, caps=False)
# torches in iron brackets on the side walls
TORCH = []
for s_ in (-1, 1):
    bx = s_ * 2.16; by = 1.05; bz = 2.25
    tube(f'tbrk{s_}', [(s_ * 2.2, by, bz - 0.25), (bx - s_ * 0.05, by, bz - 0.2), (bx - s_ * 0.12, by, bz - 0.05)], 0.018, M_IRDK, DUN, seg=8)
    st = tube(f'tstick{s_}', [(bx - s_ * 0.16, by, bz - 0.32), (bx - s_ * 0.10, by, bz + 0.12)], lambda u: 0.022 + 0.012 * u, M_WOOD, DUN, seg=10)
    lathe(f'tcup{s_}', [(0.03, 0.0), (0.06, 0.05), (0.075, 0.13), (0.07, 0.135)], 16, M_IRDK, DUN, loc=(bx - s_ * 0.10, by, bz + 0.02))
    fl = lathe(f'tflame{s_}', [(0.0, 0.0), (0.055, 0.04), (0.06, 0.10), (0.04, 0.2), (0.015, 0.3), (0.0, 0.34)], 16, M_FLAME, DUN, loc=(bx - s_ * 0.10, by, bz + 0.12))
    lt = light_at(f'tlight{s_}', 'POINT', (bx - s_ * 0.22, by, bz + 0.3), (0, by, 0), 70, (1.0, 0.55, 0.22), 0.08)
    TORCH.append((fl, lt))
BRAZ = lathe('brazier', [(0.0, 0.55), (0.24, 0.55), (0.30, 0.68), (0.32, 0.70), (0.0, 0.70)], 24, M_IRDK, DUN, loc=(-1.25, 0.75, 0.3))
for k in range(3): tube(f'brleg{k}', [(-1.25 + 0.22 * math.cos(2.1 * k), 0.75 + 0.22 * math.sin(2.1 * k), 0.85), (-1.25 + 0.3 * math.cos(2.1 * k), 0.75 + 0.3 * math.sin(2.1 * k), 0.3)], 0.018, M_IRDK, DUN, seg=8)
M_COAL = mat('coal', (0.03, 0.02, 0.02), 0.9, emit=(1.0, 0.28, 0.05), estr=4.0)
for k in range(22): prim('ico_sphere', f'coal{k}', M_COAL, DUN, loc=(-1.25 + g0_.uniform(-0.2, 0.2), 0.75 + g0_.uniform(-0.2, 0.2), 1.0 + g0_.uniform(0, 0.05)), subdivisions=1, radius=g0_.uniform(0.035, 0.06))
BRAZF = lathe('brflame', [(0.0, 0.0), (0.16, 0.05), (0.14, 0.18), (0.06, 0.36), (0.0, 0.45)], 16, M_FLAME, DUN, loc=(-1.25, 0.75, 1.02))
BRAZL = light_at('brlight', 'POINT', (-1.15, 0.7, 1.55), (0, 2, 1), 120, (1.0, 0.5, 0.2), 0.15)
FILL = light_at('dfill', 'AREA', (0.0, -1.5, 2.8), (0.0, 2.0, 1.2), 45, (0.6, 0.65, 0.8), 2.0)
# straw on the stage floor, a bucket, a stool
g_ = random.Random(3)
for k in range(140):
    a_ = g_.uniform(0, 2 * math.pi); r_ = g_.uniform(0.5, 1.9); p = Vector((math.cos(a_) * r_ * 1.0, 2.0 + math.sin(a_) * r_ * 0.8, 0.305))
    if abs(p.x) > 2.1 or p.y > 3.65 or p.y < 0.2: continue
    d_ = Vector((math.cos(g_.uniform(0, 6.3)), math.sin(g_.uniform(0, 6.3)), 0.04)).normalized() * g_.uniform(0.12, 0.3)
    tube(f'straw{k}', [p, p + d_ * 0.5 + Vector((0, 0, 0.012)), p + d_], 0.0035, M_STRAW, DUN, seg=4, caps=False)
lathe('bucket', [(0.0, 0.0), (0.15, 0.0), (0.19, 0.34), (0.20, 0.35), (0.0, 0.35)], 24, M_WOODRAW, DUN, loc=(1.55, 3.1, 0.3))
for zb_ in (0.06, 0.28): tube(f'bkband{zb_}', [(1.55 + (0.158 + zb_ * 0.11) * math.cos(2 * math.pi * k / 24), 3.1 + (0.158 + zb_ * 0.11) * math.sin(2 * math.pi * k / 24), 0.3 + zb_) for k in range(25)], 0.008, M_IRDK, DUN, seg=6)
box('stool', (0.42, 0.42, 0.06), (-1.5, 2.9, 0.75), M_WOODRAW, bv=0.01, parent=DUN)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): box(f'stleg{sx_}{sy_}', (0.05, 0.05, 0.45), (-1.5 + sx_ * 0.16, 2.9 + sy_ * 0.16, 0.5), M_WOODRAW, parent=DUN)
# the museum front: brass posts, velvet rope, a placard
for k, xp in enumerate((-2.0, 0.0, 2.0)):
    lathe(f'post{k}', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.04, 0.06), (0.025, 0.08), (0.025, 0.88), (0.045, 0.92), (0.05, 0.96), (0.0, 1.0)], 24, M_BRASS, HALL, loc=(xp, -0.55, 0))
for k in range(2):
    x0, x1 = -2.0 + 2 * k, 2.0 * k
    tube(f'rope{k}', [(lerp(x0, x1, u), -0.55, 0.9 - 0.22 * math.sin(math.pi * u)) for u in [i / 16 for i in range(17)]], 0.022, M_VELVET, HALL, seg=10)
PLQ1 = empty('plaq1', HALL, loc=(1.15, -1.0, 0)); PLQ1.rotation_euler = (0, 0, R(-12))
for xs_ in (-0.12, 0.12): box(f'plqleg{xs_}', (0.03, 0.03, 0.9), (xs_, 0, 0.45), M_BRASS, parent=PLQ1)
pb = box('plqboard', (0.6, 0.03, 0.4), (0, -0.02, 0.98), M_PLAQ, bv=0.005, parent=PLQ1); pb.rotation_euler = (R(-35), 0, 0)
t_ = text3d('plqtxt', 'IRON MAIDEN\n"MEDIEVAL"?', 0.07, (0, -0.045, 1.0), (R(55), 0, 0), M_GILT, PLQ1, extrude=0.002)

# ---------------------------------------------------------------- exhibit 2: the writer's desk, 1793 (x = 7); the timeline above it
DESK = empty('desk')
box('rug', (3.0, 2.2, 0.01), (7.0, 3.0, 0.005), noisy(mat('rug', (0.30, 0.07, 0.05), 0.95), 6.0, 0.3), parent=DESK)
box('desktop', (1.5, 0.8, 0.05), (7.0, 3.1, 0.78), M_WOOD, bv=0.01, parent=DESK)
box('deskapron', (1.4, 0.7, 0.12), (7.0, 3.1, 0.69), M_WOOD, bv=0.005, parent=DESK)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): tube(f'dleg{sx_}{sy_}', [(7.0 + sx_ * 0.68, 3.1 + sy_ * 0.33, 0.63), (7.0 + sx_ * 0.66, 3.1 + sy_ * 0.31, 0.3), (7.0 + sx_ * 0.67, 3.1 + sy_ * 0.32, 0.0)], lambda u: 0.03 - 0.012 * u, M_WOOD, DESK, seg=10)
box('chairseat', (0.5, 0.5, 0.05), (7.1, 3.85, 0.47), M_WOOD, bv=0.01, parent=DESK); box('chairback', (0.5, 0.05, 0.6), (7.1, 4.1, 0.8), M_WOOD, bv=0.01, parent=DESK)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): box(f'chleg{sx_}{sy_}', (0.04, 0.04, 0.47), (7.1 + sx_ * 0.21, 3.85 + sy_ * 0.21, 0.23), M_WOOD, parent=DESK)
# the open book (two curved pages) and the line of writing that grows
BOOK = empty('book', DESK, loc=(6.95, 3.02, 0.805)); BOOK.rotation_euler = (0, 0, R(6))
for s_ in (-1, 1):
    vs = []; fs = []; nu, nv = 10, 2
    for i in range(nu + 1):
        u = i / nu; x_ = s_ * (0.01 + 0.2 * u); z_ = 0.03 * math.sin(math.pi * (0.15 + 0.7 * u)) - 0.012 * u
        for j in range(nv + 1): vs.append((x_, -0.14 + 0.28 * j / nv, z_))
    for i in range(nu):
        for j in range(nv): a_ = i * (nv + 1) + j; fs.append((a_, a_ + nv + 1, a_ + nv + 2, a_ + 1) if s_ > 0 else (a_, a_ + 1, a_ + nv + 2, a_ + nv + 1))
    pg = mesh(f'page{s_}', vs, fs, M_PAPER, BOOK); sd = pg.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.012
box('bookcover', (0.46, 0.31, 0.01), (0, 0, -0.012), noisy(mat('leather', (0.25, 0.08, 0.04), 0.6), 30, 0.3), parent=BOOK)
INKLINES = []
for k in range(7):                                         # lines of writing on the right page; they grow as the quill moves
    o = box(f'ink{k}', (0.16, 0.004, 0.0015), (0.03 + 0.08, 0.10 - k * 0.032, 0.036), M_INK, parent=BOOK); INKLINES.append(o)
QUILL = empty('quill', DESK)
tube('qshaft', [(0, 0, 0), (0.01, 0.0, 0.06), (0.03, 0.005, 0.30)], lambda u: 0.0035 * (1 - 0.5 * u), M_WHITE, QUILL, seg=6)
vs = []; fs = []
for i in range(13):
    u = i / 12; z_ = 0.08 + 0.24 * u; w_ = 0.028 * math.sin(math.pi * min(1, u * 1.15)) + 0.002
    vs += [(0.008 + 0.02 * u - w_, 0.002, z_), (0.008 + 0.02 * u + w_ * 0.6, 0.002, z_)]
for i in range(12): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
vane = mesh('qvane', vs, fs, noisy(mat('feather', (0.86, 0.84, 0.78), 0.7, sheen=0.6), 40, 0.15), QUILL); sd = vane.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.002
lathe('inkwell', [(0.0, 0.0), (0.045, 0.0), (0.05, 0.04), (0.03, 0.06), (0.018, 0.075), (0.02, 0.085), (0.0, 0.085)], 24, M_GLASS, DESK, loc=(7.35, 2.95, 0.805))
lathe('inkin', [(0.0, 0.0), (0.04, 0.0), (0.04, 0.035), (0.0, 0.035)], 16, M_INK, DESK, loc=(7.35, 2.95, 0.808))
lathe('candlehold', [(0.0, 0.0), (0.08, 0.0), (0.085, 0.01), (0.02, 0.02), (0.018, 0.05), (0.03, 0.055), (0.0, 0.06)], 24, M_BRASS, DESK, loc=(7.55, 3.3, 0.805))
lathe('candle', [(0.0, 0.0), (0.022, 0.0), (0.022, 0.20), (0.016, 0.215), (0.0, 0.215)], 16, M_WAX, DESK, loc=(7.55, 3.3, 0.86))
CFLAME = lathe('cflame', [(0.0, 0.0), (0.009, 0.01), (0.011, 0.025), (0.006, 0.045), (0.0, 0.06)], 12, M_FLAME, DESK, loc=(7.55, 3.3, 1.08))
CLIGHT = light_at('clight', 'POINT', (7.55, 3.3, 1.13), (7.0, 3.0, 0.8), 25, (1.0, 0.62, 0.3), 0.03)
# the forger's coins and a two-part coin mould
COINS = []
for k in range(9):
    c_ = prim('cylinder', f'coin{k}', M_SILV if k % 3 else M_GOLD, DESK, loc=(6.45 + (0.07 if k > 5 else 0), 3.0 + (0.06 if k > 5 else 0), 0.81 + 0.0065 * (k if k <= 5 else k - 6)), vertices=28, radius=0.022, depth=0.005)
    COINS.append(c_)
for k in range(4):
    a_ = 0.9 * k; prim('cylinder', f'coinf{k}', M_SILV, DESK, loc=(6.32 + 0.06 * math.cos(a_), 3.2 + 0.05 * math.sin(a_), 0.808), vertices=28, radius=0.022, depth=0.005)
box('mouldA', (0.09, 0.07, 0.04), (6.40, 2.82, 0.825), M_IRDK, bv=0.006, parent=DESK); box('mouldB', (0.09, 0.07, 0.04), (6.52, 2.80, 0.825), M_IRDK, bv=0.006, parent=DESK).rotation_euler = (0, 0, R(18))
prim('cylinder', 'mouldhole', M_BLACK, DESK, loc=(6.40, 2.82, 0.846), vertices=20, radius=0.022, depth=0.002)
PLQ2 = empty('plaq2', HALL, loc=(8.25, 1.75, 0)); PLQ2.rotation_euler = (0, 0, R(-10))
for xs_ in (-0.1, 0.1): box(f'plq2leg{xs_}', (0.03, 0.03, 0.85), (xs_, 0, 0.42), M_BRASS, parent=PLQ2)
pb = box('plq2board', (0.5, 0.03, 0.34), (0, -0.02, 0.92), M_PLAQ, bv=0.005, parent=PLQ2); pb.rotation_euler = (R(-35), 0, 0)
text3d('plq2txt', 'THE STORY\n1793', 0.075, (0, -0.045, 0.94), (R(55), 0, 0), M_GILT, PLQ2, extrude=0.002)
# the timeline rail on the wall: 1515 ...... 1793
TL = empty('timeline', HALL)
box('tlbar', (2.8, 0.04, 0.05), (7.5, 5.38, 2.8), M_BLACK, parent=TL)
TLFILL = box('tlfill', (1.0, 0.03, 0.08), (6.1 + 0.5, 5.36, 2.8), emis('tlglow', (1.0, 0.25, 0.12), 6.0), parent=TL)
for xp, yr in ((6.1, '1515'), (8.9, '1793')):
    box(f'tltick{yr}', (0.04, 0.04, 0.35), (xp, 5.38, 2.8), M_GILT, parent=TL)
    text3d(f'tltxt{yr}', yr, 0.42, (xp, 5.35, 3.3), (R(90), 0, 0), M_GILT, TL, extrude=0.01)
text3d('tltxt_q', 'NO RECORD', 0.3, (7.5, 5.35, 2.3), (R(90), 0, 0), emis('redtxt', (0.9, 0.12, 0.08), 2.5), TL, extrude=0.006)

# ---------------------------------------------------------------- exhibit 3: the workshop, where a maiden is pieced together (x = 13)
SHOP = empty('shop')
box('shopplat', (4.2, 3.0, 0.15), (13.4, 3.0, 0.075), M_WOODRAW, bv=0.01, parent=SHOP)
box('bench', (1.8, 0.7, 0.08), (15.0, 3.6, 0.85), M_WOODRAW, bv=0.01, parent=SHOP)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): box(f'bleg{sx_}{sy_}', (0.08, 0.08, 0.7), (15.0 + sx_ * 0.8, 3.6 + sy_ * 0.28, 0.5), M_WOODRAW, parent=SHOP)
tube('hammerh', [(14.5, 3.5, 0.91), (14.62, 3.5, 0.91)], 0.025, M_IRDK, SHOP, seg=10); tube('hammerg', [(14.56, 3.5, 0.91), (14.6, 3.2, 0.905)], 0.012, M_WOOD, SHOP, seg=8)
tube('tongs1', [(15.3, 3.4, 0.9), (15.6, 3.6, 0.9), (15.75, 3.75, 0.9)], 0.008, M_IRDK, SHOP, seg=6); tube('tongs2', [(15.3, 3.45, 0.9), (15.6, 3.58, 0.9), (15.78, 3.7, 0.9)], 0.008, M_IRDK, SHOP, seg=6)
for k in range(3):                                          # old museum pieces on the bench: a helmet, a door panel, a box of nails
    pass
lathe('helmet', [(0.0, 0.2), (0.08, 0.19), (0.13, 0.14), (0.15, 0.05), (0.16, 0.0)], 24, M_IRON2, SHOP, loc=(15.5, 3.75, 0.89))
box('nailbox', (0.3, 0.2, 0.1), (14.8, 3.8, 0.94), M_WOODRAW, bv=0.005, parent=SHOP)
for k in range(12): tube(f'nail{k}', [(14.68 + 0.02 * k, 3.75 + 0.01 * (k % 3), 0.97), (14.68 + 0.02 * k + 0.01, 3.80, 1.04)], 0.004, M_IRDK, SHOP, seg=4)
box('banner3', (2.4, 0.02, 0.5), (13.2, 5.38, 3.6), M_RED, parent=SHOP)
text3d('ban3txt', 'NUREMBERG', 0.3, (13.2, 5.36, 3.6), (R(90), 0, 0), M_GILT, SHOP, extrude=0.008)

# ---------------------------------------------------------------- exhibit 4: the shipping crate, Chicago 1893 (x = 19)
CRATE = empty('crate')
CX, CY = 19.0, 2.8
for s_ in (-1, 1):                                          # side walls of slats
    for k in range(6): box(f'crs{s_}{k}', (0.05, 1.3, 0.36), (CX + s_ * 0.68, CY, 0.2 + k * 0.4), M_WOODRAW, bv=0.006, parent=CRATE)
for k in range(6): box(f'crb{k}', (1.4, 0.05, 0.36), (CX, CY + 0.65, 0.2 + k * 0.4), M_WOODRAW, bv=0.006, parent=CRATE)
box('crtop', (1.46, 1.36, 0.06), (CX + 1.05, CY - 0.1, 0.72), M_WOODRAW, bv=0.006, rot=(0, R(-62), 0), parent=CRATE); box('crbase', (1.46, 1.36, 0.1), (CX, CY, 0.05), M_WOODRAW, bv=0.006, parent=CRATE)
for s_ in (-1, 1):
    for xx in (-0.66, 0.66): box(f'crpost{s_}{xx}', (0.08, 0.08, 2.4), (CX + xx, CY + s_ * 0.64, 1.2), M_WOODRAW, bv=0.006, parent=CRATE)
lid = empty('crlid', CRATE, loc=(CX - 1.55, CY - 0.2, 0)); lid.rotation_euler = (R(-10), 0, R(-75))
for k in range(5): box(f'crl{k}', (1.4, 0.05, 0.4), (0, 0, 0.22 + k * 0.44), M_WOODRAW, bv=0.006, parent=lid)
box('crlx', (0.08, 0.06, 2.2), (0, -0.04, 1.1), M_WOODRAW, parent=lid).rotation_euler = (0, R(31), 0)
text3d('crtxt', 'CHICAGO', 0.2, (CX + 0.71, CY, 1.3), (R(90), 0, R(90)), M_BLACK, CRATE, extrude=0.002)
text3d('crtxt2', 'FRAGILE', 0.11, (CX + 0.71, CY, 0.95), (R(90), 0, R(90)), M_RED, CRATE, extrude=0.002)
for k in range(60):
    p = Vector((CX + g_.uniform(-0.6, 0.6), CY + g_.uniform(-0.55, 0.55), 0.11)); d_ = Vector((g_.uniform(-1, 1), g_.uniform(-1, 1), 0.05)).normalized() * g_.uniform(0.1, 0.25)
    tube(f'cstraw{k}', [p, p + d_ * 0.5 + Vector((0, 0, 0.015)), p + d_], 0.004, M_STRAW, CRATE, seg=4, caps=False)
# poster and bunting
box('poster', (2.6, 0.02, 1.4), (19.0, 5.38, 3.4), M_POSTER, parent=CRATE)
box('posterband', (2.6, 0.025, 0.28), (19.0, 5.37, 3.95), M_RED, parent=CRATE)
text3d('posttxt1', "WORLD'S FAIR", 0.24, (19.0, 5.355, 3.95), (R(90), 0, 0), M_WHITE, CRATE, extrude=0.004)
text3d('posttxt2', 'CHICAGO 1893', 0.3, (19.0, 5.355, 3.45), (R(90), 0, 0), M_BLUE, CRATE, extrude=0.004)
text3d('posttxt3', 'SEE THE IRON MAIDEN', 0.13, (19.0, 5.355, 2.95), (R(90), 0, 0), M_RED, CRATE, extrude=0.004)
FLAGS = []
for row_, (z0, y0) in enumerate(((4.6, 1.0), (4.4, 3.4))):
    pts = [(16.6 + 4.8 * u, y0, z0 - 0.35 * math.sin(math.pi * u)) for u in [i / 20 for i in range(21)]]; tube(f'bstr{row_}', pts, 0.006, M_WHITE, CRATE, seg=6)
    for k in range(12):
        u = (k + 0.5) / 12; p = Vector((16.6 + 4.8 * u, y0, z0 - 0.35 * math.sin(math.pi * u)))
        f_ = mesh(f'flag{row_}{k}', [(-0.12, 0, 0), (0.12, 0, 0), (0, 0, -0.26)], [(0, 1, 2)], (M_RED, M_WHITE, M_BLUE)[k % 3], CRATE, smooth_=False, loc=p)
        sd = f_.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.004; FLAGS.append((f_, k + row_ * 7))

# ---------------------------------------------------------------- outside: a courtyard in Baghdad (x 24..48), sun and sky
YARD = empty('yard')
box('yground', (30.0, 34.0, 0.2), (39.0, 0.0, -0.11), M_SAND, parent=YARD)
box('ybldg', (1.0, 30.0, 9.0), (46.0, 0.0, 4.5), M_SANDW, parent=YARD)
for k in range(-5, 6):                                      # arches (dark recesses with pointed heads) along the building
    y_ = k * 2.4
    box(f'yarch{k}', (0.3, 1.4, 2.6), (45.45, y_, 1.3), mat(f'ydark{k}', (0.06, 0.05, 0.04), 0.9), parent=YARD)
    ar = mesh(f'yarchh{k}', [(45.42, y_ - 0.7, 2.6), (45.42, y_ + 0.7, 2.6), (45.42, y_, 3.3)], [(0, 1, 2)], bpy.data.materials[f'ydark{k}'], YARD, smooth_=False)
    box(f'ywin{k}', (0.3, 0.9, 1.0), (45.45, y_, 5.5), bpy.data.materials[f'ydark{k}'], parent=YARD)
box('ybldg2', (16.0, 1.0, 7.0), (36.0, 10.5, 3.5), M_SANDWX, parent=YARD)
box('ycornice', (1.4, 30.0, 0.4), (45.8, 0.0, 9.1), M_SANDW, bv=0.02, parent=YARD)
box('ywall', (16.0, 0.6, 2.4), (33.0, -9.5, 1.2), M_SANDWX, parent=YARD)
def palm(name, base, h, lean, seed):
    gg = random.Random(seed); pts = [Vector(base) + Vector((lean[0] * u * u * h, lean[1] * u * u * h, u * h)) for u in [i / 12 for i in range(13)]]
    tube(name + 'tr', pts, lambda u: 0.22 - 0.09 * u, M_PALM, YARD, seg=14)
    for i in range(1, 12): tube(f'{name}ring{i}', [pts[i] + Vector((0.2 * math.cos(2 * math.pi * k / 14), 0.2 * math.sin(2 * math.pi * k / 14), 0)) * (1 - 0.4 * i / 12) for k in range(15)], 0.018, M_PALM, YARD, seg=5, caps=False)
    top = pts[-1]
    for k in range(13):
        a_ = 2 * math.pi * k / 13 + gg.uniform(-0.2, 0.2); dr = Vector((math.cos(a_), math.sin(a_), 0)); L_ = gg.uniform(2.2, 3.0)
        spine = [top + dr * (L_ * u) + Vector((0, 0, 0.6 * math.sin(math.pi * u * 0.8) - 1.1 * u * u)) for u in [i / 10 for i in range(11)]]
        vs = []; fs = []
        for i, sp in enumerate(spine):
            u = i / 10; w_ = 0.42 * math.sin(math.pi * min(1, 0.15 + u)) + 0.02; side = dr.cross(Vector((0, 0, 1)))
            vs += [sp + side * w_ + Vector((0, 0, -0.12 * w_)), sp, sp - side * w_ + Vector((0, 0, -0.12 * w_))]
        for i in range(10): fs += [(3 * i, 3 * i + 1, 3 * i + 4, 3 * i + 3), (3 * i + 1, 3 * i + 2, 3 * i + 5, 3 * i + 4)]
        fr = mesh(f'{name}fr{k}', vs, fs, M_FROND, YARD); sd = fr.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.01
palm('palm1', (38.0, 6.0, 0.0), 7.5, (0.08, -0.05), 1); palm('palm2', (41.5, -5.5, 0.0), 8.5, (-0.06, 0.07), 2); palm('palm3', (30.0, 7.5, 0.0), 6.5, (0.1, 0.0), 3)
SUN = light_at('sun', 'SUN', (40, -20, 30), (32, 0, 0), 3.2, (1.0, 0.92, 0.78), 0.02); SUN.data.angle = R(1.2)
SKY = W_.node_tree.nodes.new('ShaderNodeTexSky')
try:
    SKY.sky_type = 'MULTIPLE_SCATTERING'; SKY.sun_elevation = R(38); SKY.sun_rotation = R(120); SKY.altitude = 50; SKY.air_density = 1.4
    for k_, v_ in (('dust_density', 3.0), ('aerosol_density', 3.0)):
        try: setattr(SKY, k_, v_)
        except Exception: pass
except Exception as e_: print('sky', e_)
W_.node_tree.links.new(SKY.outputs['Color'], WBG.inputs['Color']); WBG.inputs['Strength'].default_value = 0.0
# the leaf pile it was hidden under, and loose leaves
LEAVES = []
def leaf(name, p, rot, sc, m, parent):
    vs = [(0, -0.5, 0), (0.18, -0.25, 0.02), (0.22, 0.05, 0.03), (0.12, 0.35, 0.02), (0, 0.5, 0), (-0.12, 0.35, 0.02), (-0.22, 0.05, 0.03), (-0.18, -0.25, 0.02), (0, 0, 0.04)]
    fs = [(8, i, (i + 1) % 8) for i in range(8)]
    o = mesh(name, [Vector(v) * sc for v in vs], fs, m, parent, loc=p); o.rotation_euler = rot; return o
LP = Vector((32.0, 0.0, 0.0))
for k in range(1500):
    a_ = g_.uniform(0, 2 * math.pi); r_ = abs(g_.gauss(0, 0.62)); p = LP + Vector((0.55 + math.cos(a_) * r_ * 1.6, math.sin(a_) * r_ * 1.0, 0))
    if p.x < LP.x - 0.55 and abs(p.y) < 0.45: continue                       # keep the face clear
    hgt = max(0.0, 0.9 * math.exp(-(r_ / 0.65) ** 2)) * g_.uniform(0.55, 1.0)
    o = leaf(f'pile{k}', p + Vector((0, 0, 0.01 + hgt)), (g_.uniform(-0.7, 0.7), g_.uniform(-0.7, 0.7), g_.uniform(0, 6.3)), g_.uniform(0.12, 0.2), M_LEAF[k % 4], YARD)
    LEAVES.append((o, o.location.copy(), o.rotation_euler.copy(), k))

# ================================================================ the four maidens
M1 = build_maiden('m1', M_IRON, M_IRDK); M1['root'].location = (0.0, 2.0, 0.3)                     # the dungeon one (the myth)
M2 = build_maiden('m2', M_IRON2, M_IRDK, base_m=M_WOODRAW); M2['root'].location = (13.0, 2.9, 0.25) # pieced together in the shop
M3 = build_maiden('m3', M_IRON, M_IRDK); M3['root'].location = (CX, CY - 0.05, 0.1)                 # the copy in the crate for Chicago
M4 = build_maiden('m4', M_IRON4, M_IRDK); M4['root'].location = (LP.x + 1.0, LP.y, 0.37)           # Baghdad: on its back under the leaves
M4['root'].rotation_mode = 'QUATERNION'
M4['root'].rotation_quaternion = Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0))).to_quaternion()     # up -> -x (head toward the window), front -> +z (face up)
for d, s_ in zip(M3['doors'], (-1, 1)): d.rotation_euler = (0, 0, s_ * R(108))
for d, s_ in zip(M4['doors'], (-1, 1)): d.rotation_euler = (0, 0, s_ * R(4))
M3IN = light_at('m3in', 'POINT', (CX, CY - 0.05, 1.3), (CX, CY, 0), 0.0, (1.0, 0.8, 0.55), 0.1)
# the shop maiden's parts: where each sits before it's put together (offset from its place, rotation, a little lift on the way)
M2_REST = {}
for nm in ('foot', 'back', 'top', 'head', 'doorL', 'doorR', 'plinth'):
    o = M2[nm]; M2_REST[nm] = (o.location.copy(), o.rotation_euler.copy())
M2_FROM = {     # name: (offset, euler, start time from B4, duration)
    'plinth': (Vector((0, 0, 0)), Vector((0, 0, 0)), 0.0, 0.01),
    'foot': (Vector((-1.25, -0.55, -0.12)), Vector((0, 0, R(30))), 0.25, 0.7),
    'back': (Vector((1.55, 0.55, -0.18)), Vector((0, 0, R(-55))), 0.55, 0.9),
    'top': (Vector((1.95, 0.6, -0.72)), Vector((R(12), 0, R(40))), 1.25, 0.75),
    'head': (Vector((2.45, 0.6, -0.7)), Vector((0, R(-20), R(70))), 1.75, 0.75),
    'doorL': (Vector((-1.6, 0.9, -0.12)), Vector((0, 0, R(-75))), 2.3, 0.85),
    'doorR': (Vector((-1.15, -0.95, -0.12)), Vector((0, 0, R(60))), 2.75, 0.85),
}
# dust that bursts out of the seam when the door slams
M_DUST = mat('dust', (0.55, 0.50, 0.44), 0.95); nt_ = M_DUST.node_tree; M_DUST.blend_method = 'BLEND'
nt_.links.new(objattr(nt_, 'a'), nt_.nodes['Principled BSDF'].inputs['Alpha'])
DUST = []
gd = random.Random(11)
for k in range(70):
    z0 = gd.uniform(0.35, 1.9); v = Vector((gd.uniform(-0.9, 0.9), gd.uniform(-1.4, -0.3), gd.uniform(-0.1, 0.5))); r0 = gd.uniform(0.008, 0.025)
    o = prim('ico_sphere', f'dust{k}', M_DUST, None, loc=(0, 0, -50), subdivisions=1, radius=r0); o['a'] = 0.0
    DUST.append((o, Vector((gd.uniform(-0.05, 0.05), 2.0 - 0.37, z0 + 0.3)), v, gd.uniform(0.6, 1.0)))
# sparks drifting up from the torches
EMB = []
M_EMB = emis_mix('ember', (1.0, 0.45, 0.12), 12.0, 'a')
for k in range(24):
    o = prim('ico_sphere', f'emb{k}', M_EMB, None, loc=(0, 0, -50), subdivisions=1, radius=0.006); o['a'] = 0.0
    EMB.append((o, k % 2, gd.uniform(0, 3.0), gd.uniform(0.25, 0.6), gd.uniform(-0.1, 0.1), gd.uniform(-0.1, 0.1)))
# a tape measure along the Baghdad maiden (7 feet)
TAPE = box('tape', (1.0, 0.035, 0.006), (0, 0, 0), emis('tapeglow', (1.0, 0.82, 0.1), 3.0)); TAPE.location = (-50, 0, 0)
TAPE_ENDS = []
for k in range(2): o = box(f'tapeend{k}', (0.012, 0.09, 0.07), (-50, 0, 0), emis(f'tapee{k}', (1.0, 0.82, 0.1), 3.0)); TAPE_ENDS.append(o)
# loose leaves skittering over the courtyard in the wind
LOOSE = []
for k in range(26):
    p = Vector((gd.uniform(26.5, 37.0), gd.uniform(-4.5, 4.5), 0.01))
    o = leaf(f'loose{k}', p, (0, 0, gd.uniform(0, 6.3)), gd.uniform(0.09, 0.14), M_LEAF[k % 4], None)
    LOOSE.append((o, p.copy(), gd.uniform(0.5, 1.4), gd.uniform(0, 6.3)))
# framed pictures along the hall
for k, (xf, wf, hf) in enumerate(((3.3, 1.0, 1.3), (10.6, 1.2, 0.9), (16.3, 0.9, 1.2), (22.3, 1.1, 1.4))):
    box(f'frame{k}', (wf + 0.14, 0.06, hf + 0.14), (xf, 5.36, 2.5), M_GILT, bv=0.02, parent=HALL)
    cv = box(f'canvas{k}', (wf, 0.02, hf), (xf, 5.32, 2.5), brick_mat(f'canvasm{k}', (0.18, 0.14, 0.09), (0.10, 0.12, 0.10), (0.15, 0.10, 0.06), 0.4 + 0.3 * k, rough=0.6, plane='xz', bump=0.05, row=0.4, w=1.3, mortar_w=0.2, seed=k * 1.3), parent=HALL)

# ================================================================ animation and the one continuous camera move
T_SLAM = 0.45
def key(t, p, q, lens): return (t, Vector(p), Vector(q), lens)
def interp(keys, t):
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0.0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0.0
    else:
        i = max(j for j in range(len(keys)) if keys[j][0] <= t); k0, k1 = keys[i], keys[i + 1]; u = sm((t - k0[0]) / (k1[0] - k0[0]))
    c0, c1 = k0[1], k1[1]; a0, a1 = k0[2], k1[2]
    d0 = (a0 - c0).normalized(); d1 = (a1 - c1).normalized(); cp = c0.lerp(c1, u); dr = d0.slerp(d1, u) if d0.dot(d1) > -0.99 else d1
    fl = lerp((a0 - c0).length, (a1 - c1).length, u)
    return cp, cp + dr * fl, lerp(k0[3], k1[3], u)
CK = [
    key(0.0, (0.95, 0.05, 1.15), (-0.05, 1.8, 1.15), 22),              # close on the doors as they swing shut
    key(T_SLAM + 0.15, (0.85, -0.05, 1.18), (-0.02, 1.8, 1.15), 22),
    key(2.6, (0.25, -0.35, 1.45), (0.0, 2.0, 1.25), 24),                 # ease back: the whole maiden, torches, chains
    key(B[1] - 0.05, (0.2, -0.55, 1.5), (0.0, 2.0, 1.25), 24),
    key(B[1] + 1.7, (0.9, -6.0, 2.1), (0.25, 1.5, 1.6), 24),             # pull way back: it's a museum diorama
    key(B[2] - 0.05, (1.0, -6.15, 2.12), (0.3, 1.5, 1.6), 24),
    key(B[2] + 1.35, (6.45, 1.55, 1.5), (6.92, 3.05, 0.82), 28),         # the writer's desk, 1793: quill, coins, the mould
    key(B[3] - 0.05, (6.5, 1.65, 1.48), (6.92, 3.05, 0.82), 28),
    key(B[3] + 1.0, (7.5, 0.3, 2.6), (7.5, 5.2, 2.85), 20),              # up to the timeline: 1515 .. 1793
    key(B[4] - 0.05, (7.5, 0.2, 2.6), (7.5, 5.2, 2.85), 20),
    key(B[4] + 1.0, (12.3, -0.9, 1.75), (13.25, 2.9, 1.2), 22),          # the workshop: the parts come together
    key(B[5] - 0.05, (12.45, -0.75, 1.72), (13.15, 2.9, 1.2), 22),
    key(B[5] + 1.0, (18.3, -1.2, 1.85), (19.0, 2.7, 1.55), 24),          # the crate for Chicago, 1893
    key(B[6] - 0.05, (18.4, -1.1, 1.82), (19.0, 2.7, 1.55), 24),
    key(B[6] + 0.85, (19.0, 1.25, 1.32), (19.0, 2.95, 1.05), 22),        # look inside: empty
    key(B[7] - 0.05, (19.0, 1.35, 1.3), (19.0, 2.95, 1.05), 22),
    key(B[7] + 0.7, (19.9, -0.3, 1.9), (24.0, 0.0, 2.3), 22),            # back out and turn to the window ...
    key(B[7] + 1.55, (24.1, 0.0, 2.45), (30.0, 0.0, 1.0), 22),           # ... and out into the sun
    key(B[7] + 2.6, (28.3, -3.0, 2.3), (32.2, 0.1, 0.45), 26),           # Baghdad: the leaf pile, the iron face
    key(B[8] - 0.05, (28.5, -2.9, 2.25), (32.2, 0.1, 0.45), 26),
    key(TOTAL, (31.0, -1.7, 2.1), (31.35, 0.0, 0.5), 28),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])

def camera(t): return interp(CK, t)

def door_angle(t):
    if t < T_SLAM: u = t / T_SLAM; return 105.0 * (1 - u ** 2.2)
    d = t - T_SLAM; return 3.5 * math.exp(-d * 9.0) * abs(math.sin(d * 28.0))

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- maiden 1: the slam
    a1 = door_angle(t)
    for d, s_ in zip(M1['doors'], (-1, 1)): d.rotation_euler = (0, 0, s_ * R(a1))
    for o, p0, v, s_ in DUST:
        tau = t - T_SLAM - 0.01
        if tau < 0 or tau > 2.4: o.location = (0, 0, -50); o['a'] = 0.0; continue
        dsp = (1 - math.exp(-tau * 3.0)) / 3.0
        o.location = p0 + v * dsp + Vector((0, 0, -0.06 * tau)); o['a'] = 0.3 * s_ * math.exp(-tau * 1.6) * min(1, tau * 30); o.scale = (0.6 + 0.8 * tau,) * 3
    # torches, embers, candle
    for k, (fl, lt) in enumerate(TORCH):
        w_ = wob(t, 6.0, k * 3.1); fl.scale = (1 + 0.12 * w_, 1 + 0.12 * wob(t, 7.0, k + 9), 1 + 0.22 * wob(t, 9.0, k + 4)); lt.data.energy = 260 * (1 + 0.25 * w_)
    for o, side, ph, sp, dx, dy in EMB:
        fl, _ = TORCH[side]; p0 = fl.matrix_world.translation; u = ((t * sp + ph) % 1.2)
        o.location = p0 + Vector((dx + 0.05 * math.sin(t * 3 + ph * 5), dy, 0.25 + u * 0.9)); o['a'] = max(0.0, 1 - u / 1.2) * (0.6 + 0.4 * math.sin(t * 20 + ph * 9))
    BRAZF.scale = (1 + 0.1 * wob(t, 6, 11), 1 + 0.1 * wob(t, 6, 12), 1 + 0.25 * wob(t, 9, 13)); BRAZL.data.energy = 120 * (1 + 0.25 * wob(t, 7, 11))
    CFLAME.scale = (1 + 0.1 * wob(t, 8, 2), 1 + 0.1 * wob(t, 8, 5), 1 + 0.18 * wob(t, 10, 7)); CLIGHT.data.energy = 25 * (1 + 0.2 * wob(t, 8, 2))
    # ---- the museum lights come up as the diorama is revealed
    ml = smooth(B[1] + 0.1, B[1] + 0.9, t)
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * ml; lt.hide_render = ml < 0.002
    FILL.data.energy = 45 * (1 - 0.6 * ml); MOON.data.energy = 90 * (1 - 0.7 * ml)
    WBG.inputs['Strength'].default_value = 0.012 + 0.10 * smooth(B[6], B[7] + 1.0, t)
    # ---- the desk: the quill writes, a coin spins
    w0 = B[2] + 0.5; per = 0.62
    for k, o in enumerate(INKLINES):
        u = clamp((t - w0 - k * per) / per, 0, 1); o.scale = (max(u, 0.001), 1, 1); o.location.x = 0.03 + 0.08 * u; o.hide_render = u <= 0.0
    kq = int(clamp((t - w0) // per, 0, len(INKLINES) - 1)); uq = clamp((t - w0 - kq * per) / per, 0, 1)
    if t < w0: kq, uq = 0, 0.0
    tip = BOOK.matrix_world @ Vector((0.03 + 0.16 * uq, 0.10 - kq * 0.032, 0.04 + 0.004 * abs(math.sin(t * 22))))
    QUILL.location = tip; QUILL.rotation_euler = (R(-28), R(22) + 0.08 * math.sin(t * 22), R(-30))
    cn = COINS[-1]; sp_ = smooth(B[2] + 0.2, B[2] + 0.5, t) * (1 - smooth(B[3] + 1.0, B[3] + 2.0, t))
    cn.location = (6.62, 2.86, 0.81 + 0.02 * sp_); cn.rotation_euler = (R(80) * sp_ * (0.6 + 0.4 * math.cos(t * 3)), 0, t * 14 * sp_)
    # ---- the timeline: 1515 -> 1793 fills in
    u = smooth(B[3] + 0.6, B[3] + 3.0, t); TLFILL.scale = (max(2.8 * u, 0.001), 1, 1); TLFILL.location.x = 6.1 + 1.4 * u; TLFILL.hide_render = u <= 0.001
    # ---- the shop maiden comes together from old parts
    for nm, (off, eu, ts, du) in M2_FROM.items():
        o = M2[nm]; l0, r0 = M2_REST[nm]; u = smooth(B[4] + ts, B[4] + ts + du, t)
        lift = 0.45 * math.sin(math.pi * u) if du > 0.05 else 0.0
        o.location = l0 + off * (1 - u) + Vector((0, 0, lift)); o.rotation_euler = (r0.x + eu.x * (1 - u), r0.y + eu.y * (1 - u), r0.z + eu.z * (1 - u))
    for d, s_ in zip(M2['doors'], (-1, 1)):
        nm = 'door' + ('L' if s_ < 0 else 'R'); off, eu, ts, du = M2_FROM[nm]; u = smooth(B[4] + ts, B[4] + ts + du, t)
        sh = smooth(B[4] + 3.65, B[4] + 3.95, t)                       # last: both doors swing shut
        d.rotation_euler = (0, 0, M2_REST[nm][1].z + eu.z * (1 - u) + s_ * R(80) * (1 - sh))
    # ---- the crate: bunting sways; inside the copy a warm light during the look in
    for fo, k in FLAGS: fo.rotation_euler = (0.18 * math.sin(t * 2.2 + k * 0.7), 0, 0.08 * math.sin(t * 1.7 + k))
    M3IN.data.energy = 60.0 * smooth(B[6] - 0.3, B[6] + 0.6, t) * (1 - smooth(B[7] + 0.6, B[7] + 1.2, t))
    # ---- outside: wind in the leaves, the tape measure
    for o, p0, sp, ph in LOOSE:
        tau = max(0.0, t - B[7]); dx = sp * tau * 0.6 + 0.05 * math.sin(t * 3 + ph)
        o.location = p0 + Vector((dx, 0.25 * math.sin(tau * 1.3 + ph), 0.02 + 0.05 * abs(math.sin(tau * 4 + ph)))); o.rotation_euler = (0.3 * math.sin(tau * 5 + ph), 0.2 * math.cos(tau * 4 + ph), ph + tau * 2.0 * sp)
    for o, l0, r0, k in LEAVES[:60]:
        o.rotation_euler = (r0.x + 0.12 * math.sin(t * 3.0 + k), r0.y + 0.1 * math.cos(t * 2.6 + k * 1.3), r0.z)
    ut = smooth(B[7] + 3.0, B[7] + 4.2, t) * (1 - smooth(B[8] - 0.1, B[8] + 0.3, t)); L_ = 2.05
    x0 = M4['root'].location.x; TAPE.location = (x0 - L_ * ut / 2, -0.62, 0.012); TAPE.scale = (max(L_ * ut, 0.001), 1, 1); TAPE.hide_render = ut < 0.002
    for k, o in enumerate(TAPE_ENDS): o.location = (x0 - (L_ * ut if k else 0.0), -0.62, 0.04); o.hide_render = ut < 0.002
    # ---- camera, with a little life in it
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3) + (shake(t, 0.03, 4.0, 14.0) * math.exp(-max(0, t - T_SLAM) * 6.0) if t > T_SLAM else Vector())
    look(cp, ct, lens, 5.6 if t < B[7] + 1.0 else 8.0)
    bpy.context.view_layer.update()
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

