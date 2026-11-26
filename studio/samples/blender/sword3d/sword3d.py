# The heavy sword myth: a giant cartoon sword slams onto a museum dial scale (40 lb). It's yanked away; a real sword reads 3 lb, a
# two-hander 9.5; a sword balances on a knife edge and spins; a 1746 book calls swords heavy and a new book gets an 'UP TO 30 LB' stamp;
# the twist - a real 7-foot parade sword (almost 15 lb) flies into a guard's hands; a museum wall hangs it as a 'sword of war'. One shot.
#   python3 sword3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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

# ================================================================ props: swords, dial scales, cloth
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

def cloth_mat(name, c, rough=0.85, sheen=0.5, weave=180.0, seed=0.0):
    """wool / linen: base colour with a fine weave bump and a little colour drift"""
    m = mat(name, c, rough, sheen=sheen); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed, seed * 0.7, seed * 0.3); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 6.0, 4.0)
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', big, 0.5), c, tuple(x * 0.7 for x in c)), b.inputs['Base Color'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = weave; wv.inputs['Distortion'].default_value = 2.0; nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(math_(nt, 'ADD', wv.outputs['Fac'], tnoise(nt, mp.outputs['Vector'], 90.0, 3.0)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


M_LINEN = cloth_mat('linen', (0.80, 0.78, 0.72), 0.8, 0.3, 240.0, 3.0)
M_REDC = cloth_mat('redcl', (0.50, 0.04, 0.03), 0.9, 0.6, 90.0, 7.0)
M_YELC = cloth_mat('yelcl', (0.75, 0.52, 0.08), 0.85, 0.5, 90.0, 8.0)
M_BERET = cloth_mat('beret', (0.02, 0.02, 0.022), 0.9, 0.6, 60.0, 1.0)
M_DUMMY = noisy(mat('dummy', (0.42, 0.40, 0.37), 0.7, sheen=0.3), 6.0, 0.15)
M_LEATHER = noisy(mat('leather', (0.06, 0.035, 0.02), 0.45, coat=0.2), 40.0, 0.2)


def steel_mat(name, base=(0.62, 0.63, 0.65), rough=0.2, seed=0.0, dark=0.0):
    """polished steel with long grind lines along the blade (x) and a few dull patches"""
    m = mat(name, base, rough, 1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2.0, 90.0, 90.0); mp.inputs['Location'].default_value = (seed, seed, 0)
    nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    grind = tnoise(nt, mp.outputs['Vector'], 1.0, 3.0); blot = tnoise(nt, coord(nt, 'Object'), 9.0, 4.0)
    nt.links.new(mixc(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', grind, 0.5), math_(nt, 'MULTIPLY', blot, 0.3 + dark)), base, tuple(c * 0.6 for c in base)), b.inputs['Base Color'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough * 0.6; mr.inputs['To Max'].default_value = rough * 1.9
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', grind, 0.6), math_(nt, 'MULTIPLY', blot, 0.4)), mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m


def blade_mesh(name, L, w0, t0, parent, m, point=0.12, taper=0.65, wavy=0.0, xoff=0.0):
    """a flat blade along +x from the guard (x = 0) to the point; diamond section (edges at +-y, ridge at +-z)"""
    n = 40; vs = []; fs = []
    for i in range(n + 1):
        u = i / n; w = w0 * (1 - taper * u)
        if u > 1 - point: w *= math.sqrt(max(0.0, (1 - u) / point))
        t = t0 * (1 - 0.55 * u) * (w / max(w0 * (1 - taper * u), 1e-6)) ** 0.5
        yw = wavy * w0 * math.sin(u * 60) if wavy else 0.0
        x = xoff + L * u; vs += [(x, -w + yw * 0.0, 0), (x, 0, t), (x, w, 0), (x, 0, -t)]
        vs[-4] = (x, -w - yw, 0); vs[-2] = (x, w + yw, 0)
    for i in range(n):
        for k in range(4): k2 = (k + 1) % 4; fs.append((4 * i + k, 4 * i + k2, 4 * (i + 1) + k2, 4 * (i + 1) + k))
    fs.append((3, 2, 1, 0))
    o = mesh(name, vs, fs, m, parent, smooth_=False)
    for p_ in o.data.polygons: p_.use_smooth = False
    return o


def sword(name, parent, L, w0, t0, guard, grip, pom, m_blade, m_hilt, m_grip, kind='arming', loc=(0, 0, 0)):
    """root at the middle of the crossguard; blade along +x, grip along -x; lies flat (guard along y)"""
    root = empty(name, parent, loc=loc)
    if kind == 'myth':                                   # the cartoon sword everyone pictures: huge, slab-thick, a gold hilt with a gem
        blade_mesh(f'{name}_bl', L, w0, t0, root, m_blade, point=0.18, taper=0.25)
        box(f'{name}_gd', (0.09, guard, 0.07), (-0.045, 0, 0), m_hilt, bv=0.02, parent=root)
        for s_ in (-1, 1): prim('uv_sphere', f'{name}_gb{s_}', m_hilt, root, loc=(-0.045, s_ * guard / 2, 0), segments=16, ring_count=8, radius=0.05)
        tube(f'{name}_gr', [(-0.09, 0, 0), (-0.09 - grip, 0, 0)], 0.035, m_grip, root, seg=16)
        for k in range(6): tube(f'{name}_wr{k}', [(-0.1 - grip * k / 6, 0, 0), (-0.1 - grip * (k + 0.5) / 6, 0, 0)], 0.039, m_hilt if k % 2 else m_grip, root, seg=16)
        prim('uv_sphere', f'{name}_pm', m_hilt, root, loc=(-0.09 - grip - pom * 0.8, 0, 0), segments=20, ring_count=10, radius=pom)
        prim('uv_sphere', f'{name}_gem', M_GEM, root, loc=(-0.045, 0, 0.055), segments=12, ring_count=6, radius=0.03, scale=(1, 1, 0.6))
        return root
    blade_mesh(f'{name}_bl', L, w0, t0, root, m_blade, point=0.10 if kind != 'bearing' else 0.06, taper=0.62 if kind != 'bearing' else 0.4,
               wavy=0.0)
    gz = 0.013 if kind == 'arming' else 0.016
    if kind == 'bearing':                                # a long ricasso with parrying lugs, side rings, a big flared guard
        for s_ in (-1, 1):
            tube(f'{name}_lug{s_}', [(0.24, s_ * w0 * 0.9, 0), (0.25, s_ * (w0 + 0.05), 0), (0.29, s_ * (w0 + 0.07), 0)], 0.009, m_hilt, root, seg=8)
            lathe(f'{name}_ring{s_}', [(0.045, -0.006), (0.058, -0.006), (0.058, 0.006), (0.045, 0.006)], 24, m_hilt, root, loc=(0.05, s_ * 0.06, 0)).rotation_euler = (R(90), 0, 0)
        pts = [(0.0, -guard / 2 - 0.0, 0)] + [(-0.02 * math.sin(math.pi * u), -guard / 2 + guard * u, 0) for u in (0.2, 0.5, 0.8)] + [(0.0, guard / 2, 0)]
        tube(f'{name}_gd', [(0.03, -guard / 2, 0), (-0.02, -guard / 4, 0), (-0.03, 0, 0), (-0.02, guard / 4, 0), (0.03, guard / 2, 0)], lambda u: 0.016 + 0.01 * abs(u - 0.5) * 2, m_hilt, root, seg=10)
        for s_ in (-1, 1): prim('uv_sphere', f'{name}_gk{s_}', m_hilt, root, loc=(0.035, s_ * guard / 2, 0), segments=12, ring_count=6, radius=0.03)
        box(f'{name}_blk', (0.06, 0.07, 0.04), (-0.02, 0, 0), m_hilt, bv=0.01, parent=root)
        tube(f'{name}_gr', [(-0.05, 0, 0), (-0.05 - grip, 0, 0)], lambda u: 0.02 + 0.006 * math.sin(math.pi * u), M_VELV, root, seg=14)
        for k in range(5): lathe(f'{name}_band{k}', [(0.022, -0.008), (0.028, -0.006), (0.028, 0.006), (0.022, 0.008)], 16, m_hilt, root, loc=(-0.05 - grip * (k + 0.5) / 5, 0, 0)).rotation_euler = (0, R(90), 0)
        prim('uv_sphere', f'{name}_pm', m_hilt, root, loc=(-0.05 - grip - pom * 0.9, 0, 0), segments=20, ring_count=10, radius=pom, scale=(1.35, 1, 1))
        return root
    box(f'{name}_gd', (0.022, guard, 2 * gz), (-0.011, 0, 0), m_hilt, bv=0.006, parent=root)
    for s_ in (-1, 1): prim('uv_sphere', f'{name}_gk{s_}', m_hilt, root, loc=(-0.011, s_ * guard / 2, 0), segments=10, ring_count=6, radius=gz * 1.15)
    tube(f'{name}_gr', [(-0.022, 0, 0), (-0.022 - grip, 0, 0)], lambda u: 0.0145 + 0.003 * math.sin(math.pi * u), m_grip, root, seg=14)
    p_ = lathe(f'{name}_pm', [(0.0, -0.011), (pom * 0.75, -0.011), (pom, -0.006), (pom, 0.006), (pom * 0.75, 0.011), (0.0, 0.011)], 28, m_hilt, root, loc=(-0.022 - grip - pom * 0.85, 0, 0))
    # a wheel pommel: the disc lies in the blade's plane (its faces point the same way as the blade's flats)
    return root


def low_z(root):
    """lowest point of a prop (all its meshes) in the root's own frame, as built (for resting it on a surface)"""
    bpy.context.view_layer.update(); inv = root.matrix_world.inverted(); z = 1e9
    for o in [root] + list(root.children_recursive):
        if o.type != 'MESH': continue
        mw = inv @ o.matrix_world
        dg = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = dg.to_mesh()
        for v in me.vertices: z = min(z, (mw @ v.co).z)
        dg.to_mesh_clear()
    return z


def dial_scale(name, parent, loc, pan='round', pan_w=0.62, maxv=50, H=0.95, m_body=None):
    """a big museum dial scale: iron foot and column, a white dial facing -y, a red needle, a brass pan on top.
    returns (root, needle pivot, pan top z). needle angle for v pounds: -135 + 270 v / maxv degrees from straight up"""
    root = empty(name, parent, loc=loc); mb = m_body or M_ENAM
    box(f'{name}_foot', (0.7, 0.5, 0.08), (0, 0, 0.04), M_IRONB, bv=0.015, parent=root)
    box(f'{name}_col', (0.5, 0.36, H - 0.1), (0, 0, 0.08 + (H - 0.1) / 2), mb, bv=0.02, parent=root)
    for z_ in (0.1, H - 0.04): box(f'{name}_trim{z_}', (0.53, 0.39, 0.03), (0, 0, z_), M_BRASS, bv=0.008, parent=root)
    DZ = H * 0.58; dy = -0.18
    d_ = lathe(f'{name}_bez', [(0.0, 0.0), (0.205, 0.0), (0.225, 0.012), (0.225, 0.035), (0.205, 0.04), (0.19, 0.03), (0.0, 0.03)], 48, M_BRASS, root, loc=(0, dy, DZ))
    d_.rotation_euler = (R(90), 0, 0)
    face = prim('cylinder', f'{name}_face', M_DIAL, root, loc=(0, dy - 0.031, DZ), rot=(R(90), 0, 0), vertices=48, radius=0.19, depth=0.004)
    st, nst = (2, 10) if maxv >= 40 else (1, 5)
    for k in range(maxv // st + 1):
        v = st * k; a = R(-135 + 270 * v / maxv); big = v % nst == 0; r_ = 0.165
        box(f'{name}_tk{k}', (0.004 if not big else 0.007, 0.002, 0.022 if not big else 0.04), (r_ * math.sin(a), dy - 0.035, DZ + r_ * math.cos(a)), M_INK, rot=(0, a, 0), parent=root)
        if big: text3d(f'{name}_n{v}', str(v), 0.034, (0.118 * math.sin(a), dy - 0.035, DZ + 0.118 * math.cos(a)), (R(90), 0, 0), M_INK, root, extrude=0.0005)
    text3d(f'{name}_lb', 'LB', 0.03, (0, dy - 0.035, DZ - 0.085), (R(90), 0, 0), M_RED, root, extrude=0.0005)
    piv = empty(f'{name}_piv', root, loc=(0, dy - 0.042, DZ))
    box(f'{name}_ndl', (0.007, 0.003, 0.17), (0, 0, 0.065), M_NEEDLE, parent=piv)
    tube(f'{name}_ndt', [(0, 0, -0.03), (0, 0, 0.0)], 0.006, M_NEEDLE, piv, seg=8)
    prim('cylinder', f'{name}_hub', M_BRASS, piv, loc=(0, -0.004, 0), rot=(R(90), 0, 0), vertices=20, radius=0.016, depth=0.008)
    box(f'{name}_glass', (0.39, 0.002, 0.39), (0, dy - 0.05, DZ), M_GLASSD, parent=root).hide_render = True
    top = H + 0.03
    if pan == 'round':
        lathe(f'{name}_pan', [(0.0, 0.0), (pan_w / 2 - 0.02, 0.0), (pan_w / 2, 0.015), (pan_w / 2 + 0.005, 0.04), (pan_w / 2 - 0.01, 0.04), (pan_w / 2 - 0.03, 0.012), (0.0, 0.012)], 48, M_BRASS, root, loc=(0, 0, top))
        prim('cylinder', f'{name}_stem', M_BRASS, root, loc=(0, 0, top - 0.01), vertices=16, radius=0.04, depth=0.04)
        return root, piv, top + 0.012
    box(f'{name}_pan', (pan_w, 0.34, 0.03), (0, 0, top + 0.015), M_BRASS, bv=0.01, parent=root)
    for s_ in (-1, 1): box(f'{name}_lip{s_}', (pan_w, 0.02, 0.03), (0, s_ * 0.16, top + 0.04), M_BRASS, bv=0.006, parent=root)
    prim('cylinder', f'{name}_stem', M_BRASS, root, loc=(0, 0, top - 0.01), vertices=16, radius=0.05, depth=0.04)
    return root, piv, top + 0.03


def needle_angle(v, maxv=50): return R(-135 + 270 * v / maxv)
def dress_form(name, parent, loc, head=True, legs=False, h=1.0):
    """a museum dress form on a pole: torso (shoulders at about 1.5 * h), neck, head; legs optional (for breeches)"""
    f_ = empty(name, parent, loc=loc)
    lathe(f'{name}_base', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.03), (0.03, 0.05), (0.025, 0.85 if not legs else 0.42), (0.0, 0.85 if not legs else 0.42)], 20, M_BLACK, f_)
    lathe(f'{name}_torso', [(0.0, 0.85), (0.13, 0.86), (0.155, 0.95), (0.135, 1.12), (0.16, 1.30), (0.19, 1.42), (0.12, 1.50), (0.05, 1.53), (0.0, 1.53)], 28, M_DUMMY, f_).scale = (1.0, 0.68, 1.0)
    if legs:
        for s_ in (-1, 1): lathe(f'{name}_leg{s_}', [(0.0, 0.42), (0.055, 0.42), (0.06, 0.6), (0.075, 0.8), (0.08, 0.88), (0.0, 0.88)], 16, M_DUMMY, f_, loc=(s_ * 0.075, 0, 0))
    if head:
        lathe(f'{name}_neck', [(0.0, 1.5), (0.045, 1.5), (0.04, 1.62), (0.0, 1.62)], 16, M_DUMMY, f_)
        prim('uv_sphere', f'{name}_head', M_DUMMY, f_, loc=(0, 0, 1.72), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
    return f_


def garment(name, prof, m, parent, sx=1.0, sy=0.72, seg=32, open_front=0.0):
    """a body garment as a lathe shell (radius, z) scaled to the form's oval; open_front cuts a slit at the front (-y) for a coat"""
    if open_front <= 0:
        o = lathe(name, prof, seg, m, parent); o.scale = (sx, sy, 1.0)
    else:
        o = arc_shell(name, [(r, z) for r, z in prof], 270 + open_front / 2 - 360, 270 - open_front / 2, seg, sx, sy, m, 0.008, parent)
    return o


def collar(name, parent, z, r0=0.06, r1=0.17, m=None):
    """a flat white falling-band collar: a disc ring dropping toward the front"""
    vs = []; fs = []; n = 32
    for i in range(n + 1):
        a = math.pi * (0.0 + 1.0 * i / n) + math.pi                      # front half (y < 0)
        for r_, dz in ((r0, 0.0), (r1, -0.05 - 0.04 * math.sin(a - math.pi))):
            vs.append((r_ * math.cos(a), r_ * math.sin(a) * 0.75, z + dz))
    for i in range(n): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    o = mesh(name, vs, fs, m or M_LINEN, parent); o.modifiers.new('sd', 'SOLIDIFY').thickness = 0.006; return o

# ================================================================ set: a museum hall (x -4..24), sword exhibits along the back wall
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
for xs, tg in ((0.0, (0.0, 3.6, 0.9)), (1.6, (1.6, 3.6, 0.9)), (4.0, (4.0, 3.6, 1.1)), (7.4, (8.0, 5.3, 2.6)), (8.6, (8.6, 4.4, 1.2)),
               (12.0, (12.0, 4.3, 1.6)), (13.6, (13.6, 3.5, 1.0)), (16.5, (16.5, 3.9, 1.5)), (20.3, (20.3, 5.3, 2.4))):
    track_spot(xs, tg)
for k, xa in enumerate((2.0, 9.0, 16.0, 22.0)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 350, (1.0, 0.93, 0.84), 3.0), 350))
G = random.Random(7)


def placard(name, loc, rz, body, size=0.07):
    P_ = empty(name, HALL, loc=loc); P_.rotation_euler = (0, 0, R(rz))
    for xs_ in (-0.12, 0.12): box(f'{name}leg{xs_}', (0.03, 0.03, 0.9), (xs_, 0, 0.45), M_BRASS, parent=P_)
    pb = box(f'{name}board', (0.6, 0.03, 0.4), (0, -0.02, 0.98), M_PLAQ, bv=0.005, parent=P_); pb.rotation_euler = (R(-35), 0, 0)
    text3d(f'{name}txt', body, size, (0, -0.045, 1.0), (R(55), 0, 0), M_GILT, P_, extrude=0.002); return P_


def wall_banner(name, x, body, w=2.4):
    box(name, (w, 0.02, 0.5), (x, 5.38, 3.6), M_RED, parent=HALL)
    text3d(name + 'txt', body, 0.3, (x, 5.36, 3.6), (R(90), 0, 0), M_GILT, HALL, extrude=0.008)


PLAT_Z = 0.15
M_PLAT = noisy(mat('platm', (0.20, 0.12, 0.07), 0.6, coat=0.1), 10.0, 0.2)


# ---------------------------------------------------------------- sword-room materials
M_BLADE = steel_mat('blade', seed=1.0); M_BLADE2 = steel_mat('blade2', (0.58, 0.59, 0.61), 0.24, seed=4.0)
M_BLADEM = steel_mat('bladem', (0.55, 0.56, 0.60), 0.16, seed=7.0, dark=0.15)
M_HILTI = mat('hilti', (0.10, 0.10, 0.11), 0.35, 1.0)
M_GEM = mat('gem', (0.55, 0.02, 0.05), 0.05, trans=0.6, coat=1.0)
M_VELV = cloth_mat('velv', (0.30, 0.02, 0.03), 0.8, 0.8, 120.0, 2.0)
M_ENAM = noisy(mat('enam', (0.03, 0.10, 0.06), 0.3, coat=0.6), 6.0, 0.15)
M_ENAMR = noisy(mat('enamr', (0.28, 0.03, 0.03), 0.3, coat=0.6), 6.0, 0.15)
M_IRONB = mat('ironb', (0.03, 0.03, 0.032), 0.45, 0.6)
M_DIAL = noisy(mat('dial', (0.86, 0.84, 0.76), 0.35, coat=0.4), 5.0, 0.06)
M_NEEDLE = mat('needle', (0.65, 0.03, 0.02), 0.35, coat=0.5)
M_GLASSD = mat('glassd', (0.9, 0.95, 1.0), 0.02, trans=1.0)
M_TAPE = mat('tape', (0.85, 0.65, 0.05), 0.45)
M_STAMP = mat('stamp', (0.75, 0.04, 0.03), 0.6)
M_BOOK = cloth_mat('book', (0.03, 0.06, 0.20), 0.6, 0.2, 260.0, 9.0)
M_PANEL = cloth_mat('panel', (0.20, 0.015, 0.02), 0.85, 0.8, 200.0, 3.0)
for xp, w_, d_ in ((0.8, 3.6, 1.8), (4.0, 1.4, 1.4), (12.8, 3.8, 2.2), (16.5, 2.4, 1.6), (20.3, 1.6, 1.4)):
    box(f'plat{xp}', (w_, d_, PLAT_Z), (xp, 3.9 if xp != 20.3 else 4.45, PLAT_Z / 2), M_PLAT, bv=0.01, parent=HALL)
wall_banner('ban1', 0.8, 'SWORDS', 2.6)


def sword_on(sw, x, y, top):
    """rest a lying sword (guard at x) on a surface at height top: the lowest point just touches"""
    sw.location = (x, y, 0.0); sw.rotation_euler = (0, 0, 0); z0 = low_z(sw); sw.location = (x, y, top - z0 + 0.001); return sw.location.copy()


# ================================================================ exhibit 1: two dial scales (x = 0 and 1.6) - the myth sword, a real sword, a two-hander
S1X, S2X, SY = 0.0, 1.6, 3.6
SC1, ND1, TOP1 = dial_scale('sc1', HALL, (S1X, SY, PLAT_Z)); TOP1 += PLAT_Z
SC2, ND2, TOP2 = dial_scale('sc2', HALL, (S2X, SY, PLAT_Z), m_body=M_ENAMR); TOP2 += PLAT_Z
MYTH = sword('myth', None, 1.25, 0.14, 0.035, 0.5, 0.3, 0.075, M_BLADEM, M_GILT, M_LEATHER, kind='myth')
MYTH_P = sword_on(MYTH, S1X - 0.4, SY + 0.14, TOP1); MYTH_RZ = R(-20)          # lies a little across the pan so the gold hilt shows
ARM = sword('arm', None, 0.76, 0.026, 0.0035, 0.2, 0.1, 0.03, M_BLADE, M_HILTI, M_LEATHER)
ARM_P = sword_on(ARM, S1X - 0.2, SY, TOP1)
TWO = sword('two', None, 1.05, 0.027, 0.004, 0.36, 0.27, 0.035, M_BLADE2, M_HILTI, M_LEATHER)
TWO_P = sword_on(TWO, S2X - 0.25, SY, TOP2)
placard('plaq1', (S1X - 0.95, 2.75, 0), 12, 'WHAT DID A\nSWORD WEIGH?')

# ================================================================ exhibit 2: the balance - a sword teeters on a knife edge at its balance point (x = 4.0)
BALX, BALY = 4.0, 3.6
lathe('baltab', [(0.0, 0.0), (0.25, 0.0), (0.25, 0.03), (0.04, 0.06), (0.035, 0.8), (0.3, 0.8), (0.3, 0.85), (0.0, 0.85)], 32, M_WOOD, HALL, loc=(BALX, BALY, PLAT_Z))
prim('cylinder', 'baltop', M_VELV, HALL, loc=(BALX, BALY, PLAT_Z + 0.855), vertices=32, radius=0.29, depth=0.012)
tube('balpost', [(BALX, BALY, PLAT_Z + 0.86), (BALX, BALY, PLAT_Z + 1.08)], 0.012, M_BRASS, HALL, seg=12)
box('balknife', (0.022, 0.06, 0.022), (BALX, BALY, PLAT_Z + 1.08), M_BRASS, rot=(0, R(45), 0), parent=HALL)
PEG = Vector((BALX, BALY, PLAT_Z + 1.08 + 0.0156))
BSW = sword('bsw', None, 0.76, 0.026, 0.0035, 0.2, 0.1, 0.03, M_BLADE, M_HILTI, M_LEATHER)
BAL_PIV = Vector((0.12, 0.0, -0.0035 * (1 - 0.55 * 0.12 / 0.76)))        # the balance point on the blade's underside, in the sword's frame
placard('plaq2', (BALX + 0.75, 2.85, 0), -12, 'BALANCED\nNEAR THE HILT')

# ================================================================ exhibit 3: the old book on the wall (1746) and a new book on a stand (x = 8.0)
BKX = 8.0
PAGE = empty('page', HALL, loc=(BKX, 5.33, 2.65))
box('pgframe', (1.32, 0.04, 1.52), (0, 0.01, 0), M_GILT, bv=0.01, parent=PAGE)
box('pgpaper', (1.2, 0.02, 1.4), (0, -0.015, 0), noisy(mat('pgp', (0.62, 0.52, 0.34), 0.85), 6.0, 0.18), parent=PAGE)
text3d('pghead', 'THE USE OF THE', 0.07, (0, -0.03, 0.56), (R(90), 0, 0), M_INK, PAGE, extrude=0.001)
text3d('pghead1', 'BROAD SWORD', 0.1, (0, -0.03, 0.45), (R(90), 0, 0), M_INK, PAGE, extrude=0.001)
YEAR = text3d('pgyear', '1746', 0.09, (0, -0.03, 0.31), (R(90), 0, 0), M_STAMP, PAGE, extrude=0.001)
SCRIB = []
for k in range(4):
    z_ = 0.17 - 0.08 * k; L_ = 0.8 + 0.15 * G.random(); pts = []
    for i in range(60):
        u = i / 59; pts.append(Vector((-0.5 + L_ * u, -0.031, z_ + 0.012 * math.sin(u * 70 + k) + 0.006 * math.sin(u * 180 + k * 2))))
    o = tube(f'scr{k}', pts, 0.0035, M_INK, PAGE, seg=4); SCRIB.append((o, -0.5, L_))
QUOTE = [text3d('pgq0', '"The Sword was', 0.085, (-0.5, -0.031, -0.2), (R(90), 0, 0), M_INK, PAGE, extrude=0.001, align='LEFT'),
         text3d('pgq1', '... heavy"', 0.11, (-0.5, -0.031, -0.36), (R(90), 0, 0), M_INK, PAGE, extrude=0.001, align='LEFT')]
QUOTE_W = [0.75, 0.62]
QUILL = empty('quill', PAGE, loc=(0, -0.08, 0))
tube('qshaft', [(0, 0, 0), (0.05, -0.04, 0.3)], lambda u: 0.004 + 0.002 * u, M_LINEN, QUILL, seg=6)
vs = []; fs = []
for i in range(12):
    u = i / 11; c_ = Vector((0.05, -0.04, 0.3)) * (0.25 + 0.75 * u); w_ = 0.035 * math.sin(math.pi * u) ** 0.7
    vs += [tuple(c_ + Vector((-w_, 0.0, 0.0))), tuple(c_ + Vector((w_ * 0.6, 0.0, 0.0)))]
for i in range(11): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
mesh('qvane', vs, fs, noisy(mat('feather', (0.85, 0.84, 0.80), 0.8, sheen=0.6), 40.0, 0.2), QUILL, smooth_=False)
# the new book: a red hardcover on a wooden stand, a red stamp slams onto it
box('bkped', (0.42, 0.42, 0.95), (BKX + 0.6, 4.45, PLAT_Z + 0.475), M_WOOD, bv=0.01, parent=HALL)
BOOK = empty('book', HALL, loc=(BKX + 0.6, 4.45, PLAT_Z + 0.95)); BOOK.rotation_euler = (R(-12), 0, R(-8))
box('bkstand', (0.3, 0.05, 0.03), (0, -0.06, 0.015), M_WOOD, parent=BOOK)
box('bkcov', (0.27, 0.035, 0.36), (0, 0, 0.19), M_BOOK, bv=0.006, parent=BOOK)
box('bkpages', (0.255, 0.03, 0.345), (0.006, 0.002, 0.19), M_PAPER, parent=BOOK)
text3d('bkt', 'KNIGHTS', 0.05, (0, -0.019, 0.31), (R(90), 0, 0), M_GILT, BOOK, extrude=0.001)
text3d('bkt2', 'and their\nweapons', 0.028, (0, -0.019, 0.24), (R(90), 0, 0), M_GILT, BOOK, extrude=0.001)
STAMP = empty('stamp', BOOK, loc=(0, -0.022, 0.12)); STAMP.rotation_euler = (0, R(-10), 0)
text3d('stmp', 'UP TO\n30 LB!', 0.05, (0, -0.004, 0), (R(90), 0, 0), M_STAMP, STAMP, extrude=0.002)
box('stmpb', (0.2, 0.002, 0.13), (0, 0.0, 0.0), M_STAMP, parent=STAMP).hide_render = True

# ================================================================ exhibit 4: the real giant - a 7-foot bearing sword on its stand, a tape measure, a long scale (x = 12.0)
GX, GY = 12.0, 4.4
box('gstand', (0.4, 0.34, 0.16), (GX, GY, PLAT_Z + 0.08), M_WOOD, bv=0.01, parent=HALL)
GIANT = sword('giant', None, 1.59, 0.038, 0.005, 0.55, 0.42, 0.05, M_BLADE2, M_GILT, M_LEATHER, kind='bearing')
M_UP = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0))).to_4x4()     # blade up, flats facing the camera (-y)
GIANT.location = (0, 0, 0); GIANT.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
_gx = [ (GIANT.matrix_world.inverted() @ o.matrix_world @ v.co).x for o in GIANT.children_recursive if o.type == 'MESH' for v in o.data.vertices ]
G_XMIN, G_XMAX = min(_gx), max(_gx)                              # pommel end and point, in the sword's frame
G_UP = Matrix.Translation((GX, GY, PLAT_Z + 0.16 - G_XMIN + 0.002)) @ M_UP
GIANT.matrix_basis = G_UP
TAPE = empty('tape', HALL, loc=(GX + 0.25, GY - 0.05, 0))
G_H = G_XMAX - G_XMIN                                             # its length: 2.16 m, seven feet
box('tapeb', (0.035, 0.004, G_H), (0, 0, G_H / 2), M_TAPE, parent=TAPE)
for k in range(1, 8):
    z_ = 0.3048 * k; box(f'tapet{k}', (0.02, 0.006, 0.006), (-0.008, -0.002, z_), M_INK, parent=TAPE)
    text3d(f'tapen{k}', str(k), 0.025, (0.006, -0.004, z_ - 0.02), (R(90), 0, 0), M_INK, TAPE, extrude=0.0005)
TAPE_Z0 = PLAT_Z + 0.16 - 0.002                                   # the tape runs from the pommel's foot
box('tapebox', (0.09, 0.07, 0.07), (GX + 0.25, GY - 0.05, PLAT_Z + 0.035), M_TAPE, bv=0.01, parent=HALL)
TAG = empty('tag7', HALL, loc=(GX + 0.5, GY - 0.06, TAPE_Z0 + G_H))
box('tagb', (0.4, 0.01, 0.16), (0, 0, 0), M_STAMP, bv=0.01, parent=TAG)
text3d('tagt', '7 FT', 0.11, (0, -0.007, 0), (R(90), 0, 0), M_WHITE, TAG, extrude=0.001)
GLX, GLY = 13.6, 3.45
SC3, ND3, TOP3 = dial_scale('sc3', HALL, (GLX, GLY, PLAT_Z), pan='long', pan_w=2.5, maxv=20); TOP3 += PLAT_Z
GIANT.matrix_basis = Matrix.Identity(4); G_FLAT = sword_on(GIANT, GLX - 0.62, GLY, TOP3); G_FLATM = GIANT.matrix_basis.copy()
GIANT.matrix_basis = G_UP
placard('plaq4', (GX - 0.75, 2.75, 0), 12, 'BEARING SWORD\n1500s')

# ================================================================ exhibit 5: the parade - two guards in red and yellow, one carries the giant sword (x = 16.5)
PX, PY = 16.5, 3.9
def guard(name, x):
    f_ = dress_form(name, HALL, (x, PY, PLAT_Z))
    prof = [(0.17, 0.62), (0.175, 0.85), (0.15, 1.0), (0.16, 1.18), (0.19, 1.34), (0.205, 1.42), (0.14, 1.5), (0.06, 1.545)]
    arc_shell(f'{name}_l', prof, 90, 270, 20, 1.0, 0.72, M_REDC, 0.008, f_); arc_shell(f'{name}_r', prof, -90, 90, 20, 1.0, 0.72, M_YELC, 0.008, f_)
    collar(f'{name}_col', f_, 1.535, 0.05, 0.13)
    lathe(f'{name}_beret', [(0.0, 0.03), (0.08, 0.03), (0.15, 0.015), (0.16, 0.0), (0.11, -0.01), (0.0, -0.005)], 28, M_BERET, f_, loc=(0.01, 0, 1.83)).rotation_euler = (R(-6), R(12), 0)
    prim('uv_sphere', f'{name}_feather', M_WHITE, f_, loc=(0.12, 0.02, 1.88), segments=10, ring_count=6, radius=0.05, scale=(1.6, 0.4, 0.6))
    hands = Vector((0.0, -0.21, 1.13))
    for s_ in (-1, 1):
        tube(f'{name}_sl{s_}', [(s_ * 0.19, 0, 1.43), (s_ * 0.2, -0.05, 1.27), (s_ * 0.12, -0.17, 1.15), (s_ * 0.035, -0.205, 1.13)], lambda u: 0.055 - 0.02 * u, M_REDC if s_ < 0 else M_YELC, f_, seg=12)
        prim('uv_sphere', f'{name}_hand{s_}', M_DUMMY, f_, loc=(s_ * 0.022, -0.212, 1.13 + s_ * 0.035), segments=12, ring_count=8, radius=0.032)
    return f_, hands
GD1, HANDS1 = guard('gd1', PX - 0.45)
GD2, HANDS2 = guard('gd2', PX + 0.45)
# the second guard's banner on a pole (a cloth that ripples)
POLE = tube('pole', [(0.0, -0.21, 0.03), (0.0, -0.21, 2.55)], 0.016, M_WOOD, GD2, seg=10)
prim('cone', 'poletip', M_GOLD, GD2, loc=(0.0, -0.21, 2.6), vertices=12, radius1=0.03, radius2=0.0, depth=0.1)
FLAG_W, FLAG_H, FLN, FLM = 0.7, 0.45, 14, 8
vs = [(0.016 + FLAG_W * i / FLN, -0.21, 2.5 - FLAG_H * j / FLM) for j in range(FLM + 1) for i in range(FLN + 1)]
fs = [(j * (FLN + 1) + i, j * (FLN + 1) + i + 1, (j + 1) * (FLN + 1) + i + 1, (j + 1) * (FLN + 1) + i) for j in range(FLM) for i in range(FLN)]
FLAG = mesh('flag', vs, fs, cloth_mat('flagc', (0.55, 0.40, 0.05), 0.8, 0.5, 100.0, 4.0), GD2); FLAG.modifiers.new('sd', 'SOLIDIFY').thickness = 0.004
FLAG_REST = [Vector(v) for v in vs]
PSIGN = placard('plaq5', (PX + 1.05, 2.8, 0), -12, 'CARRIED IN\nPARADES')
PSTAMP = empty('pstamp', PSIGN, loc=(0, -0.06, 0.98)); PSTAMP.rotation_euler = (R(55), 0, R(-8))
text3d('pstmp', 'NOT FOR\nBATTLE', 0.075, (0, 0, 0), (0, 0, 0), M_STAMP, PSTAMP, extrude=0.003)

# ================================================================ exhibit 6: the museum wall - a fan of real swords and a parade sword hung as if for war (x = 20.3)
WDX = 20.3
box('wpanel', (2.0, 0.03, 2.4), (WDX, 5.37, 2.65), M_PANEL, bv=0.01, parent=HALL)
box('wpanelf', (2.1, 0.02, 2.5), (WDX, 5.385, 2.65), M_GILT, bv=0.01, parent=HALL)
def wall_mat(a, x, z):
    """a sword hung on the wall at angle a (from +x, in the wall plane), flats facing the room"""
    xa = Vector((math.cos(a), 0, math.sin(a))); za = Vector((0, -1, 0)); ya = za.cross(xa)
    m_ = Matrix((xa, ya, za)).transposed().to_4x4(); m_.translation = (x, 5.3, z); return m_
WSW = []                                                    # (object, rest matrix) - they drop onto their pins in turn
for k, (a_, x_, z_, kind) in enumerate(((R(60), WDX - 0.7, 1.75, 'arm'), (R(120), WDX + 0.7, 1.75, 'arm'), (R(75), WDX - 0.45, 2.1, 'two'), (R(105), WDX + 0.45, 2.1, 'two'))):
    o = sword(f'ws{k}', None, 0.76 if kind == 'arm' else 1.05, 0.026, 0.004, 0.2 if kind == 'arm' else 0.36, 0.1 if kind == 'arm' else 0.27, 0.032,
              M_BLADE if k % 2 else M_BLADE2, M_HILTI, M_LEATHER)
    WSW.append((o, wall_mat(a_, x_, z_)))
WG = sword('wgiant', None, 1.59, 0.038, 0.005, 0.55, 0.42, 0.05, M_BLADE2, M_GILT, M_LEATHER, kind='bearing')
WSW.append((WG, wall_mat(R(90), WDX, 1.55)))
for o, m_ in WSW:
    o.matrix_basis = m_
    for d_ in (0.25, 0.6): prim('cylinder', f'{o.name}_pin{d_}', M_BRASS, HALL, loc=m_ @ Vector((d_ if o.name != 'wgiant' else d_ * 1.6, 0, 0.0)) + Vector((0, 0.03, 0)), rot=(R(90), 0, 0), vertices=10, radius=0.008, depth=0.06)
PLQ = empty('plq', HALL, loc=(WDX, 5.24, 1.3))
box('plqb', (0.8, 0.02, 0.2), (0, 0, 0), M_PLAQ, bv=0.005, parent=PLQ)
box('plqf', (0.84, 0.024, 0.24), (0, 0.004, 0), M_GILT, bv=0.005, parent=PLQ)
text3d('plqt', 'SWORD OF WAR', 0.075, (0, -0.012, 0), (R(90), 0, 0), M_GILT, PLQ, extrude=0.002)
text3d('plqt2', 'PARADE SWORD', 0.075, (0, 0.016, 0), (R(-90), 0, 0), M_STAMP, PLQ, extrude=0.002)
STRIKE = box('strike', (0.68, 0.004, 0.02), (0, -0.016, 0), M_STAMP, parent=PLQ)
SC4, ND4, TOP4 = dial_scale('sc4', HALL, (WDX + 0.0, 4.5, PLAT_Z)); TOP4 += PLAT_Z
MYTH_P2 = Vector((WDX - 0.4, 4.5 + 0.14, MYTH_P.z - TOP1 + TOP4))
# ================================================================ moving bits: event times (each on its word), needles, glints, confetti
T_HIT = 0.55                                   # "slams onto a scale"
T_YANK = B[1] + 0.3                            # "no knight ever..." - the myth sword is yanked away
T_ARM = B[2] + 0.75                            # "a real fighting sword" lands: 3 lb
T_TWO = B[2] + 2.55                            # "the big two-handed ones": 9.5 lb
T_BAL = B[3] + 0.6; T_SPIN = B[3] + 2.3       # drops onto the knife edge; "moved fast" - a quick spin
T_YEAR = B[4] + 0.6; T_QUOTE = B[4] + 2.1      # "seventeen hundreds"; "heavy and clumsy"
T_STAMP = B[4] + 4.95                          # "up to thirty pounds"
T_TAPE0, T_TAPE1 = B[5] + 2.05, B[5] + 2.85    # "seven feet long"
T_TIP0, T_TIPL = B[5] + 3.0, B[5] + 3.45       # the giant tips onto the long scale; "almost fifteen pounds"
T_CARRY0, T_CARRY1 = B[6] + 0.2, B[6] + 1.0    # "only carried in parades": it flies into the guard's hands
T_MARCH = B[6] + 1.0
T_CONF = B[6] + 1.45                           # "to show off": confetti
T_PSTAMP = B[6] + 2.5                          # "too big to use in battle"
T_HANG = [B[7] + 0.75 + 0.16 * k for k in range(4)] + [B[7] + 1.45]   # "hang these parade swords"
T_WAR = B[7] + 2.0; T_STRIKE = B[7] + 3.0; T_FLIP = B[7] + 3.25       # "made for war"; "keeps the myth alive"
T_END = B[8] + 0.05; T_ENDL = B[8] + 0.33; T_POP = B[8] + 0.95       # the myth sword drops on the last scale; the needle spins off


def needle_v(t, evs):
    """spring needle: each event (t0, target) pulls the reading from where it was to the target, with an overshoot and a settle"""
    tp = None; v0 = vt = 0.0
    for t0, tgt in evs:
        if t < t0: break
        val = vt + (v0 - vt) * math.exp(-3.4 * (t0 - tp)) * math.cos(9.0 * (t0 - tp)) if tp is not None else 0.0
        tp, v0, vt = t0, val, tgt
    if tp is None: return 0.0
    d = t - tp; return max(-1.2, vt + (v0 - vt) * math.exp(-3.4 * d) * math.cos(9.0 * d))


EV1 = [(T_HIT, 40.0), (T_YANK + 0.1, 0.0), (T_ARM, 3.0)]
EV2 = [(T_TWO, 9.5)]
EV3 = [(T_TIPL, 14.7), (T_CARRY0 + 0.1, 0.0)]

M_GLINT = emis('glintm', (1.0, 0.95, 0.8), 25.0)
def glint(name):
    vs = [(0, 0, 0)]; fs = []
    for i in range(8):
        a = math.pi / 4 * i; r_ = 0.07 if i % 2 == 0 else 0.012; vs.append((r_ * math.cos(a), 0, r_ * math.sin(a)))
    for i in range(8): fs.append((0, 1 + i, 1 + (i + 1) % 8))
    o = mesh(name, vs, fs, M_GLINT, None, smooth_=False, loc=(0, 0, -50)); o.scale = (0.0,) * 3; return o
GLS_O = [glint(f'gl{k}') for k in range(3)]
GEM_W = MYTH_P + Vector((-0.042, 0.015 - 0.06, 0.07))
GLS = [(0, T_HIT + 0.02, GEM_W, 1.1), (1, T_ARM + 0.05, ARM_P + Vector((0.3, -0.02, 0.01)), 0.8), (2, T_TWO + 0.05, TWO_P + Vector((0.45, -0.02, 0.01)), 0.8),
       (0, B[3] + 1.2, PEG + Vector((-0.12 - 0.022 - 0.1 - 0.025, -0.03, 0.0)), 0.8),
       (1, B[5] + 0.95, Vector((GX, GY - 0.04, TAPE_Z0 + 1.2)), 1.1), (2, B[5] + 1.3, Vector((GX, GY - 0.04, TAPE_Z0 + G_H - 0.05)), 1.0),
       (0, T_TIPL + 0.05, G_FLAT + Vector((0.6, -0.04, 0.01)), 1.0), (1, T_WAR, Vector((WDX, 5.2, 2.4)), 1.0), (2, T_WAR + 0.35, Vector((WDX + 0.32, 5.21, 1.3)), 0.8),
       (0, T_ENDL + 0.03, MYTH_P2 + Vector((-0.042, 0.015 - 0.06, 0.07)), 1.1)]

# confetti for the parade
GA = random.Random(23); M_CONF = [mat(f'conf{k}', c, 0.5) for k, c in enumerate(((0.7, 0.05, 0.04), (0.85, 0.62, 0.08), (0.9, 0.88, 0.8), (0.85, 0.65, 0.25)))]
CONF = []
for k in range(80):
    sz = GA.uniform(0.018, 0.03); o = mesh(f'cf{k}', [(-sz, 0, -sz * 0.6), (sz, 0, -sz * 0.6), (sz, 0, sz * 0.6), (-sz, 0, sz * 0.6)], [(0, 1, 2, 3)], M_CONF[k % 4], None, smooth_=False)
    o.modifiers.new('sd', 'SOLIDIFY').thickness = 0.001
    CONF.append((o, GA.uniform(-1.3, 1.3), GA.uniform(2.9, 3.6), GA.uniform(0.0, 0.35), GA.uniform(0.7, 1.2), GA.uniform(0, 6.3), GA.uniform(3.6, 4.1)))

ND4_REST = ND4.location.copy()
# ================================================================ animation and the one continuous camera move
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
    key(0.0, (0.0, 2.45, 2.1), (0.0, 3.6, 1.12), 24),                     # the myth sword slams onto the scale (looking down on the pan)
    key(0.9, (0.0, 2.5, 2.05), (0.0, 3.6, 1.08), 24),
    key(2.3, (0.0, 2.85, 0.98), (0.0, 3.6, 0.72), 28),                    # in on the dial: forty pounds
    key(B[1] - 0.1, (0.0, 2.88, 0.97), (0.0, 3.6, 0.72), 28),
    key(B[1] + 0.75, (0.15, 2.0, 2.1), (0.1, 3.6, 0.95), 24),             # back: it's yanked away
    key(B[2] + 0.4, (0.12, 2.05, 2.05), (0.1, 3.6, 0.95), 24),            # a real sword lands: three pounds
    key(B[2] + 1.85, (0.15, 2.1, 2.0), (0.1, 3.6, 0.95), 24),
    key(B[2] + 2.4, (1.6, 2.1, 2.0), (1.6, 3.6, 0.95), 24),               # the two-hander on the red scale
    key(B[3] - 0.1, (1.62, 2.15, 1.98), (1.6, 3.6, 0.95), 24),
    key(B[3] + 0.55, (4.0, 2.55, 1.85), (4.0, 3.6, 1.1), 24),             # the balance, from above
    key(B[4] - 0.1, (4.02, 2.6, 1.83), (4.0, 3.6, 1.1), 24),
    key(B[4] + 0.75, (8.0, 3.35, 2.55), (8.0, 5.3, 2.6), 28),             # the 1746 page writes itself
    key(B[4] + 3.3, (8.02, 3.4, 2.53), (8.0, 5.3, 2.6), 28),
    key(B[4] + 4.0, (8.5, 3.0, 1.85), (8.58, 4.6, 1.4), 26),              # down: the new book gets its stamp
    key(B[5] - 0.1, (8.52, 3.05, 1.83), (8.58, 4.6, 1.4), 26),
    key(B[5] + 0.7, (12.0, 2.65, 0.85), (12.0, 4.4, 0.95), 22),           # low on the giant's hilt
    key(B[5] + 2.3, (12.1, 1.95, 1.5), (12.05, 4.4, 1.5), 20),            # up its length: seven feet
    key(B[5] + 2.95, (12.12, 1.93, 1.5), (12.05, 4.4, 1.5), 20),
    key(B[5] + 3.5, (13.3, 1.3, 2.25), (13.3, 3.6, 1.0), 20),             # it tips onto the long scale: almost fifteen
    key(B[6] - 0.1, (13.32, 1.33, 2.23), (13.3, 3.6, 1.0), 20),
    key(B[6] + 0.95, (16.5, 1.55, 1.75), (16.5, 3.8, 1.65), 22),          # it flies to the parade guard
    key(B[7] - 0.1, (16.52, 1.6, 1.73), (16.5, 3.8, 1.65), 22),
    key(B[7] + 0.7, (20.3, 2.3, 2.1), (20.3, 5.3, 2.25), 22),             # the museum wall
    key(B[7] + 2.6, (20.3, 2.4, 2.05), (20.3, 5.3, 2.2), 22),
    key(B[7] + 3.2, (20.3, 3.2, 1.6), (20.3, 5.3, 1.45), 24),             # in on the plaque: struck out, flipped
    key(B[8] - 0.05, (20.3, 3.15, 1.62), (20.3, 5.3, 1.45), 24),
    key(B[8] + 0.5, (20.2, 2.45, 2.15), (20.15, 4.5, 1.1), 22),           # back and up: the myth sword breaks the last scale
    key(TOTAL, (20.2, 2.35, 2.18), (20.15, 4.5, 1.1), 22),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)
FAR = Matrix.Translation((0, 0, -60))


def drop(t, t_land, rest, h=1.3, fall=0.45):
    """a prop dropped onto a surface: falls h (accelerating), lands at t_land, two little bounces; None before it appears"""
    if t < t_land - fall: return None, 0.0
    if t < t_land: u = (t - (t_land - fall)) / fall; return rest + Vector((0, 0, h * (1 - u * u))), 1.0 - u
    d = t - t_land; return rest + Vector((0, 0, 0.03 * abs(math.sin(d * 14)) * math.exp(-d * 7))), 0.0


def blend_m(m0, m1, u, lift=0.0):
    l0, q0, _ = m0.decompose(); l1, q1, _ = m1.decompose()
    return Matrix.Translation(l0.lerp(l1, u) + Vector((0, 0, lift * math.sin(math.pi * u)))) @ q0.slerp(q1, u).to_matrix().to_4x4()


def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- the myth sword: drops and slams (frame one is already falling), is yanked away, comes back at the end for the last scale
    if t < T_YANK:
        p_, w_ = drop(t, T_HIT, MYTH_P, 0.6, T_HIT + 0.25)                 # at frame 0 it's already in view, falling
        MYTH.location = p_; MYTH.rotation_euler = (R(10) * w_, R(-8) * w_, MYTH_RZ + R(25) * w_)
        if t > T_HIT: d = t - T_HIT; MYTH.rotation_euler = (R(2.5) * math.sin(d * 16) * math.exp(-d * 6), 0, MYTH_RZ)
    elif t < T_YANK + 1.1:
        d = t - T_YANK; MYTH.location = MYTH_P + Vector((0.25 * d, 0.1 * d, 0.4 * d + 5.0 * d * d)); MYTH.rotation_euler = (R(30) * d, R(-20) * d, MYTH_RZ + R(200) * d * d)
    elif t < T_END: MYTH.location = (0, 0, -60)
    else:
        p_, w_ = drop(t, T_ENDL, MYTH_P2, 1.3, T_ENDL - T_END)
        MYTH.location = p_; MYTH.rotation_euler = (R(8) * w_, R(-6) * w_, MYTH_RZ - R(30) * w_)
        if t > T_ENDL: d = t - T_ENDL; MYTH.rotation_euler = (R(2.5) * math.sin(d * 16) * math.exp(-d * 6), 0, MYTH_RZ)
    # ---- the needles
    ND1.rotation_euler = (0, needle_angle(needle_v(t, EV1)), 0)
    ND2.rotation_euler = (0, needle_angle(needle_v(t, EV2)), 0)
    ND3.rotation_euler = (0, needle_angle(needle_v(t, EV3), 20), 0)
    ND4.location = ND4_REST; ND4.rotation_euler = (0, needle_angle(0), 0)
    if t > T_ENDL:
        d = t - T_ENDL; a_ = needle_angle(0) + R(300) * smooth(0, 0.25, d) + R(360) * 2.2 * smooth(0.2, T_POP - T_ENDL, d) ** 1.5
        if t < T_POP: ND4.rotation_euler = (0, a_, 0)
        else:
            e = t - T_POP; ND4.location = ND4_REST + Vector((0.5 * e, -1.3 * e, 2.2 * e - 4.9 * e * e)); ND4.rotation_euler = (R(500) * e, a_ + R(900) * e, 0)
            if ND4.location.z < -0.6: ND4.location = (0, 0, -60)
    # ---- the real sword and the two-hander drop onto their scales
    for sw, rest, tl in ((ARM, ARM_P, T_ARM), (TWO, TWO_P, T_TWO)):
        p_, w_ = drop(t, tl, rest, 1.3, 0.45)
        if p_ is None: sw.location = (0, 0, -60); continue
        sw.location = p_; sw.rotation_euler = (R(6) * w_, R(-4) * w_, R(-20) * w_)
    # ---- the balance: drops onto the knife edge, teeters, settles level; a quick spin for "moved fast"
    if t < T_BAL - 0.4: BSW.matrix_basis = FAR
    else:
        if t < T_BAL: u = (t - (T_BAL - 0.4)) / 0.4; off = Vector((0, 0, 0.9 * (1 - u * u))); th = R(10); ph = R(20) * (1 - u)
        else:
            d = t - T_BAL; off = Vector(); th = R(13) * math.exp(-2.0 * d) * math.cos(7.5 * d) + 0.0
            ph = R(360) * smooth(T_SPIN, T_SPIN + 0.55, t) ** 1.0
            if t > T_SPIN + 0.55: e = t - T_SPIN - 0.55; th += R(5) * math.exp(-4 * e) * math.sin(10 * e)
        BSW.matrix_basis = Matrix.Translation(PEG + off) @ Matrix.Rotation(ph, 4, 'Z') @ Matrix.Rotation(th, 4, 'Y') @ Matrix.Translation(-BAL_PIV)
    # ---- the 1746 page: the year pops in, lines scribble, the quote writes itself; the quill follows
    u = smooth(T_YEAR, T_YEAR + 0.25, t); s = u + 0.3 * math.sin(math.pi * u); YEAR.scale = (max(s, 1e-4),) * 3; YEAR.hide_render = u <= 0
    qp = Vector((0.4, -0.08, -0.62)); qa = 0.0
    for k, (o, x0, L_) in enumerate(SCRIB):
        s = clamp((t - (B[4] + 1.0 + 0.28 * k)) / 0.26, 0, 1)
        o.scale = (max(s, 0.0001), 1, 1); o.location.x = x0 * (1 - s); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((x0 + L_ * s, -0.08, 0.17 - 0.08 * k)); qa = 1.0
    for k, o in enumerate(QUOTE):
        s = clamp((t - (T_QUOTE + 0.45 * k)) / 0.4, 0, 1); o.scale = (max(s, 0.0001), 1, 1); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((-0.5 + QUOTE_W[k] * s, -0.08, -0.2 - 0.16 * k)); qa = 1.0
    QUILL.location = qp + Vector((0, 0, 0.008 * math.sin(t * 60) * qa)); QUILL.rotation_euler = (0, R(-10) + 0.15 * math.sin(t * 25) * qa, 0)
    # ---- the stamps slam on
    for st, t0, sg in ((STAMP, T_STAMP, 1.0), (PSTAMP, T_PSTAMP, 1.0)):
        u = clamp((t - t0) / 0.12, 0, 1)
        if u <= 0: st.scale = (1e-4,) * 3; continue
        d = t - t0 - 0.12; sq = 0.1 * math.exp(-d * 16) * math.cos(d * 40) if d > 0 else 0.0
        s = 2.4 - 1.4 * u * u; st.scale = (s * (1 + sq), s, s * (1 - sq))
    # ---- the giant: the tape measure runs up its length, the 7 FT tag pops; it tips onto the long scale, then flies to the guard
    TAPE.location.z = TAPE_Z0 - G_H * (1 - smooth(T_TAPE0, T_TAPE1, t))
    u = smooth(T_TAPE1, T_TAPE1 + 0.2, t); s = u + 0.35 * math.sin(math.pi * u); TAG.scale = (max(s, 1e-4),) * 3
    mb = max(0.0, t - T_MARCH) if t > T_MARCH else 0.0
    for gd, x0, ph in ((GD1, PX - 0.45, 0.0), (GD2, PX + 0.45, 0.5)):
        if t < T_MARCH: gd.location = (x0, PY, PLAT_Z); gd.rotation_euler = (0, 0, 0); continue
        st_ = (t - T_MARCH) * 2.2 + ph; amp = smooth(T_MARCH, T_MARCH + 0.3, t)
        gd.location = (x0 + 0.025 * math.sin(math.pi * st_) * amp, PY, PLAT_Z + 0.03 * abs(math.sin(math.pi * st_)) * amp); gd.rotation_euler = (0, R(3) * math.sin(math.pi * st_) * amp, 0)
    bpy.context.view_layer.update()
    G_HOLD = Matrix.Translation(GD1.matrix_world @ (HANDS1 + Vector((0, 0, 0.26)))) @ GD1.matrix_world.to_quaternion().to_matrix().to_4x4() @ M_UP
    if t < T_TIP0: GIANT.matrix_basis = G_UP
    elif t < T_TIPL: u = (t - T_TIP0) / (T_TIPL - T_TIP0); GIANT.matrix_basis = blend_m(G_UP, G_FLATM, u * u, 0.15)
    elif t < T_CARRY0: d = t - T_TIPL; GIANT.matrix_basis = Matrix.Translation((0, 0, 0.02 * abs(math.sin(d * 14)) * math.exp(-d * 7))) @ G_FLATM
    elif t < T_CARRY1: u = sm((t - T_CARRY0) / (T_CARRY1 - T_CARRY0)); GIANT.matrix_basis = blend_m(G_FLATM, G_HOLD, u, 0.6)
    else: GIANT.matrix_basis = G_HOLD
    # ---- the banner ripples once the parade starts; confetti falls for "show off"
    me = FLAG.data; amp = 0.3 + 0.7 * smooth(T_MARCH, T_MARCH + 0.5, t)
    for i, v in enumerate(FLAG_REST):
        x = v.x - 0.016; me.vertices[i].co = (v.x - 0.02 * (x / FLAG_W) * amp, v.y + 0.045 * math.sin(6.5 * x - 7.0 * t) * (x / FLAG_W) * amp, v.z - 0.02 * (x / FLAG_W) ** 2)
    me.update()
    for o, x0, y0, dl, sp, rot, z0 in CONF:
        d = t - T_CONF - dl; z = z0 - sp * d
        if d < 0 or z < PLAT_Z + 0.02: o.location = (0, 0, -60); continue
        o.location = (PX + x0 + 0.08 * math.sin(3.1 * d + rot), y0 + 0.05 * math.cos(2.3 * d + rot), z)
        o.rotation_euler = (rot + 6.0 * d, rot * 0.5 + 4.0 * d, rot + 2.0 * d)
    # ---- the wall: the swords drop onto their pins in turn; the plaque is struck out and flipped
    for k, (o, m_) in enumerate(WSW):
        d = t - T_HANG[k]
        if d < 0: o.matrix_basis = FAR @ m_; continue
        z = 0.3 * (1 - min(1.0, d / 0.2) ** 2) if d < 0.2 else 0.012 * abs(math.sin(25 * (d - 0.2))) * math.exp(-10 * (d - 0.2))
        o.matrix_basis = Matrix.Translation((0, 0, z)) @ m_
    u = smooth(T_STRIKE, T_STRIKE + 0.25, t); STRIKE.scale = (max(u, 1e-4), 1, 1); STRIKE.hide_render = u <= 0
    u = smooth(T_FLIP, T_FLIP + 0.35, t); PLQ.rotation_euler = (math.pi * u + R(12) * math.sin(math.pi * u), 0, 0)
    # ---- glints
    for g_ in GLS_O: g_.hide_render = True; g_.scale = (0.0,) * 3
    for gi, t0, pw, sz in GLS:
        u = clamp((t - t0) / 0.35, 0, 1)
        if 0 < u < 1: g_ = GLS_O[gi]; s = math.sin(math.pi * u) * sz; g_.scale = (s, s, s); g_.rotation_euler = (0, u * 1.2, 0); g_.location = pw; g_.hide_render = False
    # ---- camera, with a nod on each big landing
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3)
    for tn, a_ in ((T_HIT, 0.02), (T_TIPL, 0.012), (T_ENDL, 0.015), (T_POP, 0.008)):
        if t > tn: cp = cp + shake(t, a_, 4.0, 13.0) * math.exp(-(t - tn) * 6.0)
    look(cp, ct, lens, 5.6)
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

