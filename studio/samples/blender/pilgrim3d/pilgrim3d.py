# Pilgrim buckles myth: a buckled black hat drops onto a Pilgrim at the harvest table; it is a museum diorama. Brewster's 1644 inventory
# writes itself, his clothes fly onto stands, the buckles pop off, the price of black dye and a portrait in Sunday best, an 1800s artist
# paints the buckles on, and the same trick on a Santa suit. One continuous shot.
#   python3 pilgrim3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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

# ================================================================ props
# ================================================================ props: iron, bronze, horn; the three helmet kinds
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


M_FELT = cloth_mat('felt', (0.018, 0.017, 0.017), 0.9, 0.6, 60.0, 1.0)
M_BLACKCL = cloth_mat('blackcloth', (0.022, 0.021, 0.022), 0.75, 0.5, 200.0, 2.0)
M_LINEN = cloth_mat('linen', (0.80, 0.78, 0.72), 0.8, 0.3, 240.0, 3.0)
M_VIOLET = cloth_mat('violet', (0.22, 0.07, 0.28), 0.8, 0.6, 180.0, 4.0)
M_GREENC = cloth_mat('greencl', (0.10, 0.20, 0.06), 0.85, 0.5, 180.0, 5.0)
M_BLUEC = cloth_mat('bluecl', (0.04, 0.09, 0.30), 0.8, 0.5, 180.0, 6.0)
M_REDC = cloth_mat('redcl', (0.50, 0.04, 0.03), 0.9, 0.6, 90.0, 7.0)
M_SANTA = cloth_mat('santa', (0.55, 0.015, 0.02), 0.8, 0.7, 150.0, 8.0)
M_FUR = mat('fur', (0.88, 0.87, 0.84), 0.95, sheen=1.0); nt_ = M_FUR.node_tree
bp_ = nt_.nodes.new('ShaderNodeBump'); bp_.inputs['Strength'].default_value = 0.6; nt_.links.new(tnoise(nt_, coord(nt_, 'Object'), 160.0, 6.0), bp_.inputs['Height']); nt_.links.new(bp_.outputs['Normal'], nt_.nodes['Principled BSDF'].inputs['Normal'])
M_LEATHER = noisy(mat('leather', (0.025, 0.022, 0.02), 0.4, coat=0.3), 40.0, 0.2)
M_BUCKLE = mat('buckle', (0.95, 0.75, 0.32), 0.15, 1.0)
M_DUMMY = noisy(mat('dummy', (0.42, 0.40, 0.37), 0.7, sheen=0.3), 6.0, 0.15)


def buckle(name, parent, w=0.11, h=0.085, bar=0.012, depth=0.012, loc=(0, 0, 0), rot=(0, 0, 0)):
    """a square gold buckle in the x-z plane (faces -y): four bars, a centre pin"""
    b_ = empty(name, parent, loc=loc); b_.rotation_euler = rot
    for k, (sz, lc) in enumerate((((w, depth, bar), (0, 0, h / 2 - bar / 2)), ((w, depth, bar), (0, 0, -h / 2 + bar / 2)),
                                  ((bar, depth, h), (-w / 2 + bar / 2, 0, 0)), ((bar, depth, h), (w / 2 - bar / 2, 0, 0)))):
        box(f'{name}_b{k}', sz, lc, M_BUCKLE, bv=bar * 0.3, parent=b_)
    box(f'{name}_pin', (bar * 0.5, depth * 0.8, h - bar), (0, -depth * 0.2, 0), M_BUCKLE, parent=b_)
    return b_


def capotain(name, parent, m=None, with_buckle=True):
    """the tall 'Pilgrim' hat: a tapered crown, flat-ish brim, black band, (the myth's) gold buckle. base at origin"""
    root = empty(name, parent)
    lathe(f'{name}_brim', [(0.0, 0.0), (0.21, -0.004), (0.235, 0.004), (0.232, 0.014), (0.20, 0.012), (0.0, 0.012)], 48, m or M_FELT, root)
    lathe(f'{name}_crown', [(0.0, 0.0), (0.112, 0.0), (0.108, 0.06), (0.100, 0.16), (0.094, 0.22), (0.090, 0.235), (0.07, 0.245), (0.0, 0.248)], 40, m or M_FELT, root)
    lathe(f'{name}_band', [(0.112, 0.008), (0.117, 0.008), (0.114, 0.055), (0.109, 0.055)], 40, M_LEATHER, root)
    bk = buckle(f'{name}_bk', root, 0.072, 0.056, 0.009, 0.008, loc=(0, -0.118, 0.032)) if with_buckle else None
    return root, bk


def shoe(name, parent, with_buckle=True):
    root = empty(name, parent)
    prim('uv_sphere', f'{name}_toe', M_LEATHER, root, loc=(0, -0.07, 0.035), segments=20, ring_count=10, radius=1.0, scale=(0.045, 0.09, 0.035))
    prim('uv_sphere', f'{name}_heel', M_LEATHER, root, loc=(0, 0.06, 0.04), segments=20, ring_count=10, radius=1.0, scale=(0.042, 0.06, 0.045))
    box(f'{name}_sole', (0.095, 0.26, 0.015), (0, 0, 0.007), M_LEATHER, bv=0.005, parent=root)
    bk = buckle(f'{name}_bk', root, 0.05, 0.04, 0.007, 0.006, loc=(0, -0.05, 0.068), rot=(R(-35), 0, 0)) if with_buckle else None
    return root, bk


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

# ================================================================ set: a museum hall (x -4..24) with seven exhibits along the back wall
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
for xs, tg in ((-1.6, (-0.4, 2.2, 1.5)), (1.6, (0.3, 2.2, 1.5)), (8.4, (9.0, 3.7, 1.3)), (10.6, (9.8, 3.7, 1.3)), (9.4, (9.4, 5.3, 2.7)),
               (13.0, (13.0, 3.4, 1.0)), (16.2, (16.2, 3.6, 1.6)), (19.4, (19.4, 2.9, 1.4)), (22.3, (22.4, 3.4, 1.4))):
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


def leaf_mesh(name, m, parent=None, size=0.05):
    vs = [(0, -size, 0), (size * 0.45, -size * 0.3, 0.004), (size * 0.5, size * 0.3, 0.0), (0, size, 0.004), (-size * 0.5, size * 0.3, 0.0), (-size * 0.45, -size * 0.3, 0.004)]
    o = mesh(name, vs, [(0, 1, 2, 3, 4, 5)], m, parent, smooth_=False); o.modifiers.new('sd', 'SOLIDIFY').thickness = 0.002; return o


# ================================================================ exhibit 1: the harvest table (x = 0), a diorama with a painted autumn sky all round
DIO = empty('dio')
box('dstage', (4.8, 3.9, 0.3), (0, 1.85, 0.15), M_WOOD, bv=0.02, parent=DIO)
box('dlintel', (5.3, 0.5, 0.55), (0, -0.05, 4.4), M_WOOD, bv=0.02, parent=DIO)
for s_ in (-1, 1): box(f'dpil{s_}', (0.45, 0.5, 4.7), (s_ * 2.5, -0.05, 2.35), M_WOOD, bv=0.02, parent=DIO)
M_AUT = bpy.data.materials.new('autumnsky'); M_AUT.use_nodes = True; nt_ = M_AUT.node_tree; nt_.nodes.remove(nt_.nodes['Principled BSDF'])
e_ = nt_.nodes.new('ShaderNodeEmission'); co_ = coord(nt_, 'Object'); sz_ = sepz(nt_, co_)
sky_ = ramp(nt_, ramp_v(nt_, sz_.outputs['Z'], 1.2, 4.3), [(0.0, (0.95, 0.70, 0.42)), (0.35, (0.75, 0.72, 0.68)), (1.0, (0.32, 0.48, 0.72))])
cl_ = tnoise(nt_, co_, 1.2, 6.0, 0.4)
sky_ = mixc(nt_, math_(nt_, 'MULTIPLY', ramp_v(nt_, cl_, 0.55, 0.75), 0.45), sky_, (0.95, 0.90, 0.85))
tl_ = math_(nt_, 'ADD', 1.15, math_(nt_, 'MULTIPLY', tnoise(nt_, co_, 1.6, 5.0, 0.5), 1.1))                   # the tree line's ragged top
tree_ = math_(nt_, 'LESS_THAN', sz_.outputs['Z'], tl_)
fol_ = ramp(nt_, tnoise(nt_, co_, 3.5, 4.0, 0.3), [(0.3, (0.05, 0.035, 0.02)), (0.42, (0.28, 0.07, 0.02)), (0.52, (0.55, 0.20, 0.04)), (0.62, (0.62, 0.42, 0.08)), (0.72, (0.18, 0.20, 0.06)), (0.8, (0.06, 0.06, 0.03))])
fol_ = mixc(nt_, math_(nt_, 'MULTIPLY', math_(nt_, 'SUBTRACT', 1.0, ramp_v(nt_, sz_.outputs['Z'], 0.3, 1.8)), 0.55), fol_, (0.03, 0.025, 0.015))
c_ = mixc(nt_, tree_, sky_, fol_)
nt_.links.new(c_, e_.inputs['Color']); e_.inputs['Strength'].default_value = 0.9
nt_.links.new(e_.outputs[0], nt_.nodes['Material Output'].inputs['Surface'])
RC, RCY = 2.38, 1.65; vs = []; fs = []; NS = 40
path = [Vector((-RC, -0.1)), Vector((-RC, RCY))] + [Vector((-RC * math.cos(math.pi * k / NS), RCY + RC * math.sin(math.pi * k / NS))) for k in range(1, NS)] + [Vector((RC, RCY)), Vector((RC, -0.1))]
for i, p in enumerate(path): vs += [(p.x, p.y, 0.3), (p.x, p.y, 4.3)]
for i in range(len(path) - 1): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
mesh('cyclo', vs, fs, M_AUT, DIO, smooth_=True)
mesh('cyctop', [(p.x, p.y, 4.29) for p in path], [tuple(range(len(path)))], M_AUT, DIO, smooth_=False)
M_GRND = mat('grnd', (0.20, 0.17, 0.08), 0.9); nt_ = M_GRND.node_tree
c_ = ramp(nt_, tnoise(nt_, coord(nt_, 'Object'), 4.0, 8.0), [(0.35, (0.10, 0.08, 0.04)), (0.5, (0.22, 0.20, 0.08)), (0.65, (0.30, 0.24, 0.10)), (0.8, (0.18, 0.12, 0.05))])
nt_.links.new(c_, nt_.nodes['Principled BSDF'].inputs['Base Color'])
box('dground', (4.76, 3.9, 0.02), (0, 1.85, 0.31), M_GRND, parent=DIO)
G = random.Random(11)
M_LEAVES = [mat(f'leaf{k}', c, 0.6, sheen=0.3) for k, c in enumerate(((0.65, 0.18, 0.03), (0.80, 0.45, 0.06), (0.55, 0.08, 0.03), (0.75, 0.62, 0.12), (0.40, 0.22, 0.05)))]
for k in range(140):                                              # leaves on the ground
    p_ = Vector((G.uniform(-2.2, 2.2), G.uniform(0.0, 3.6), 0.322)); lf = leaf_mesh(f'gl{k}', M_LEAVES[k % 5], DIO, G.uniform(0.03, 0.05)); lf.location = p_; lf.rotation_euler = (G.uniform(-0.2, 0.2), G.uniform(-0.2, 0.2), G.uniform(0, 6.3))
# the log cabin wall, a rail fence
for k in range(9): tube(f'log{k}', [(-2.3, 3.35, 0.42 + 0.21 * k), (-0.75, 3.35, 0.42 + 0.21 * k)], 0.105, M_WOODRAW if k % 2 else noisy(mat(f'logm{k}', (0.30, 0.20, 0.11), 0.85), 8.0, 0.35), DIO, seg=12)
box('cabdoor', (0.55, 0.05, 1.25), (-1.3, 3.24, 0.95), M_WOOD, bv=0.01, parent=DIO)
for k in range(4): tube(f'fpost{k}', [(0.7 + 0.5 * k, 3.4, 0.3), (0.7 + 0.5 * k, 3.4, 1.15)], 0.04, M_WOODRAW, DIO, seg=8)
for z_ in (0.62, 0.95): tube(f'frail{z_}', [(0.6, 3.4, z_), (2.3, 3.42, z_ + 0.03)], 0.03, M_WOODRAW, DIO, seg=8)
# the table and the feast
TBL = Vector((0.0, 1.95, 0.3)); TOPZ = TBL.z + 0.78
box('ttop', (2.0, 0.78, 0.06), (TBL.x, TBL.y, TOPZ - 0.03), M_WOODRAW, bv=0.01, parent=DIO)
for s_ in (-1, 1):
    box(f'tleg{s_}', (0.08, 0.6, 0.72), (TBL.x + s_ * 0.8, TBL.y, TBL.z + 0.36), M_WOODRAW, parent=DIO)
    box(f'bench{s_}', (0.7, 0.28, 0.05), (TBL.x + s_ * 0.6, TBL.y - 0.62, TBL.z + 0.45), M_WOODRAW, bv=0.01, parent=DIO)
    for s2 in (-1, 1): box(f'bleg{s_}{s2}', (0.05, 0.22, 0.43), (TBL.x + s_ * 0.6 + s2 * 0.28, TBL.y - 0.62, TBL.z + 0.215), M_WOODRAW, parent=DIO)
M_PEWTER = mat('pewter', (0.48, 0.47, 0.46), 0.35, 1.0)
M_TURKEY = noisy(mat('turkey', (0.42, 0.19, 0.06), 0.35, coat=0.6), 12.0, 0.3)
lathe('platter', [(0.0, 0.0), (0.24, 0.0), (0.27, 0.03), (0.26, 0.035), (0.22, 0.012), (0.0, 0.012)], 32, M_PEWTER, DIO, loc=(TBL.x, TBL.y - 0.02, TOPZ))
TK = empty('turkey', DIO, loc=(TBL.x, TBL.y - 0.02, TOPZ + 0.11))
prim('uv_sphere', 'tkbody', M_TURKEY, TK, segments=32, ring_count=16, radius=1.0, scale=(0.17, 0.13, 0.1))
for s_ in (-1, 1):
    tube(f'tkleg{s_}', [(s_ * 0.06, -0.08, -0.02), (s_ * 0.09, -0.17, 0.03), (s_ * 0.08, -0.22, 0.06)], lambda u: 0.045 - 0.03 * u, M_TURKEY, TK, seg=12)
    prim('uv_sphere', f'tkknob{s_}', M_LINEN, TK, loc=(s_ * 0.08, -0.235, 0.065), segments=10, ring_count=6, radius=0.018)
    prim('uv_sphere', f'tkwing{s_}', M_TURKEY, TK, loc=(s_ * 0.14, 0.03, -0.01), segments=16, ring_count=8, radius=1.0, scale=(0.04, 0.08, 0.05))
M_PUMP = mat('pump', (0.75, 0.30, 0.04), 0.5); nt_ = M_PUMP.node_tree
bp_ = nt_.nodes.new('ShaderNodeBump'); bp_.inputs['Strength'].default_value = 0.4; nt_.links.new(tnoise(nt_, coord(nt_, 'Object'), 30.0, 4.0), bp_.inputs['Height']); nt_.links.new(bp_.outputs['Normal'], nt_.nodes['Principled BSDF'].inputs['Normal'])
M_STEM = mat('stem', (0.20, 0.16, 0.06), 0.8)
def pumpkin(name, loc, r, parent):
    prof = []
    for i in range(13):
        a = math.pi * i / 12; prof.append((r * math.sin(a) * 1.15, r * 0.85 * (1 - math.cos(a))))
    vs = []; fs = []; seg = 48
    for r_, z_ in prof:
        for k in range(seg):
            an = 2 * math.pi * k / seg; rib = 1.0 - 0.06 * abs(math.cos(an * 5)) ** 0.5
            vs.append((r_ * rib * math.cos(an), r_ * rib * math.sin(an), z_))
    for i in range(len(prof) - 1):
        for k in range(seg): fs.append((i * seg + k, i * seg + (k + 1) % seg, (i + 1) * seg + (k + 1) % seg, (i + 1) * seg + k))
    o = mesh(name, vs, fs, M_PUMP, parent, loc=loc)
    tube(name + 'st', [Vector(loc) + Vector((0, 0, r * 1.65)), Vector(loc) + Vector((0.01, 0.01, r * 1.65 + r * 0.35))], r * 0.12, M_STEM, parent, seg=6)
    return o
for k, (lc, r_) in enumerate((((TBL.x + 0.7, TBL.y + 0.1, TOPZ), 0.11), ((TBL.x - 0.72, TBL.y + 0.15, TOPZ), 0.09), ((1.3, 1.25, 0.32), 0.16), ((-1.4, 1.1, 0.32), 0.13), ((1.6, 1.6, 0.32), 0.1))):
    pumpkin(f'pk{k}', lc, r_, DIO)
M_CORN = noisy(mat('corn', (0.85, 0.62, 0.12), 0.5), 120.0, 0.35); M_HUSK = noisy(mat('husk', (0.70, 0.62, 0.40), 0.8), 20.0, 0.3)
for k in range(4):
    x0 = TBL.x + 0.32 + 0.06 * k; y0 = TBL.y - 0.15 + 0.07 * k
    tube(f'corn{k}', [(x0, y0, TOPZ + 0.03), (x0 + 0.18, y0 + 0.05, TOPZ + 0.03)], lambda u: 0.028 * math.sin(math.pi * (0.2 + 0.7 * u)) + 0.008, M_CORN, DIO, seg=10)
    tube(f'husk{k}', [(x0 - 0.02, y0, TOPZ + 0.03), (x0 - 0.12, y0 - 0.03, TOPZ + 0.02)], lambda u: 0.025 * (1 - u) + 0.004, M_HUSK, DIO, seg=6)
M_BREAD = noisy(mat('bread', (0.55, 0.32, 0.12), 0.6), 20.0, 0.25)
for k in range(2): prim('uv_sphere', f'bread{k}', M_BREAD, DIO, loc=(TBL.x - 0.45 + 0.16 * k, TBL.y - 0.1 + 0.12 * k, TOPZ + 0.04), segments=20, ring_count=10, radius=1.0, scale=(0.09, 0.06, 0.05))
M_APPLE = mat('apple', (0.55, 0.05, 0.04), 0.35, coat=0.4)
for k in range(6): prim('uv_sphere', f'apple{k}', M_APPLE, DIO, loc=(TBL.x - 0.3 + 0.05 * (k % 3), TBL.y + 0.22 + 0.05 * (k // 3), TOPZ + 0.03), segments=14, ring_count=8, radius=0.03)
for k, xp in enumerate((-0.55, 0.45, -0.25, 0.25)):
    lathe(f'plate{k}', [(0.0, 0.0), (0.1, 0.0), (0.12, 0.018), (0.11, 0.02), (0.08, 0.006), (0.0, 0.006)], 24, M_PEWTER, DIO, loc=(TBL.x + xp, TBL.y - 0.3, TOPZ))
    lathe(f'mug{k}', [(0.0, 0.0), (0.04, 0.0), (0.042, 0.1), (0.036, 0.1), (0.034, 0.008), (0.0, 0.008)], 18, M_PEWTER, DIO, loc=(TBL.x + xp + 0.14, TBL.y - 0.2, TOPZ))
# the two Pilgrims (dress forms) in the myth's black and white
PIL = dress_form('pilgrim', DIO, (TBL.x + 0.15, TBL.y + 0.6, 0.31))
garment('pdoub', [(0.17, 0.95), (0.165, 1.12), (0.185, 1.30), (0.21, 1.42), (0.145, 1.505), (0.06, 1.545)], M_BLACKCL, PIL)
garment('pbreech', [(0.15, 0.55), (0.2, 0.7), (0.19, 0.95)], M_BLACKCL, PIL)
collar('pcollar', PIL, 1.535, 0.055, 0.19)
for s_ in (-1, 1): tube(f'psleeve{s_}', [(s_ * 0.2, 0, 1.43), (s_ * 0.23, 0.0, 1.2), (s_ * 0.22, -0.03, 0.98)], lambda u: 0.055 - 0.01 * u, M_BLACKCL, PIL, seg=12)
for s_ in (-1, 1): prim('uv_sphere', f'pcuff{s_}', M_LINEN, PIL, loc=(s_ * 0.22, -0.03, 0.97), segments=12, ring_count=6, radius=1.0, scale=(0.05, 0.05, 0.02))
HEAD_TOP = PIL.location + Vector((0, 0, 1.72 + 0.06))
PW = dress_form('pwife', DIO, (TBL.x - 0.95, TBL.y + 0.75, 0.31))
garment('pwdress', [(0.30, 0.0), (0.26, 0.4), (0.2, 0.85), (0.16, 1.02), (0.185, 1.30), (0.20, 1.42), (0.14, 1.505), (0.06, 1.545)], M_BLACKCL, PW)
arc_shell('pwapron', [(0.215, 0.25), (0.19, 0.6), (0.17, 1.0)], 215, 325, 16, 1.0, 0.75, M_LINEN, 0.006, PW)
collar('pwcollar', PW, 1.535, 0.055, 0.17)
lathe('pwcoif', [(0.0, 1.86), (0.06, 1.85), (0.10, 1.80), (0.108, 1.72), (0.11, 1.66), (0.0, 1.66)], 24, M_LINEN, PW).scale = (1.02, 1.12, 1.0)
HAT1, HB1 = capotain('hat1', None)
HAT1_P = HEAD_TOP.copy()
LIGHT_SUN = light_at('dsun', 'AREA', (-1.8, 3.6, 3.6), (0.2, 2.0, 1.2), 260, (1.0, 0.72, 0.45), 1.5)
light_at('dfill', 'AREA', (1.4, -0.6, 2.6), (0.0, 2.2, 1.6), 60, (0.85, 0.88, 1.0), 2.0)
for k, xp in enumerate((-2.0, 0.0, 2.0)):
    lathe(f'post{k}', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.04, 0.06), (0.025, 0.08), (0.025, 0.88), (0.045, 0.92), (0.05, 0.96), (0.0, 1.0)], 24, M_BRASS, HALL, loc=(xp, -0.75, 0))
for k in range(2):
    x0, x1 = -2.0 + 2 * k, 2.0 * k
    tube(f'vrope{k}', [(lerp(x0, x1, u), -0.75, 0.9 - 0.22 * math.sin(math.pi * u)) for u in [i / 16 for i in range(17)]], 0.022, M_VELVET, HALL, seg=10)
placard('plaq1', (1.2, -1.2, 0), -12, 'THE FIRST\nTHANKSGIVING')

# ================================================================ exhibit 2/3: Brewster's inventory on the wall, his clothes flying onto four stands below (x = 9.4)
EX = 9.4
box('cplat', (3.6, 2.2, PLAT_Z), (EX, 4.2, PLAT_Z / 2), M_PLAT, bv=0.01, parent=HALL)
PAGE = empty('page', HALL, loc=(EX, 5.33, 2.75))
box('pgframe', (1.32, 0.04, 1.52), (0, 0.01, 0), M_GILT, bv=0.01, parent=PAGE)
box('pgpaper', (1.2, 0.02, 1.4), (0, -0.015, 0), noisy(mat('pgp', (0.62, 0.52, 0.34), 0.85), 6.0, 0.18), parent=PAGE)
text3d('pghead', 'INVENTORY', 0.085, (0, -0.03, 0.55), (R(90), 0, 0), M_INK, PAGE, extrude=0.001)
text3d('pghead2', 'Wm. Brewster, 1644', 0.06, (0, -0.03, 0.44), (R(90), 0, 0), M_INK, PAGE, extrude=0.001)
SCRIB = []                                                         # scribbled lines (the long list), written during B2
for k in range(6):
    z_ = 0.32 - 0.075 * k; L_ = 0.75 + 0.15 * G.random(); pts = []
    for i in range(60):
        u = i / 59; pts.append(Vector((-0.5 + L_ * u, -0.031, z_ + 0.012 * math.sin(u * 70 + k) + 0.006 * math.sin(u * 180 + k * 2))))
    o = tube(f'scr{k}', pts, 0.0035, M_INK, PAGE, seg=4); SCRIB.append((o, -0.5, L_))
ITEMS_TXT = ['a violet coat', 'green pants', 'a blue suit', 'a red cap']
ITEMT = []
for k, tx in enumerate(ITEMS_TXT):
    z_ = -0.17 - 0.115 * k
    o = text3d(f'itm{k}', tx, 0.07, (-0.48, -0.031, z_), (R(90), 0, 0), M_INK, PAGE, extrude=0.001, align='LEFT'); ITEMT.append(o)
QUILL = empty('quill', PAGE, loc=(0, -0.08, 0))
tube('qshaft', [(0, 0, 0), (0.05, -0.04, 0.3)], lambda u: 0.004 + 0.002 * u, M_LINEN, QUILL, seg=6)
vs = []; fs = []
for i in range(12):
    u = i / 11; c_ = Vector((0.05, -0.04, 0.3)) * (0.25 + 0.75 * u); w_ = 0.035 * math.sin(math.pi * u) ** 0.7
    vs += [tuple(c_ + Vector((-w_, 0.0, 0.0))), tuple(c_ + Vector((w_ * 0.6, 0.0, 0.0)))]
for i in range(11): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
mesh('qvane', vs, fs, noisy(mat('feather', (0.85, 0.84, 0.80), 0.8, sheen=0.6), 40.0, 0.2), QUILL, smooth_=False)
# the four stands: a coat form, a breeches form, a suit form, a cap head
STAND_X = [EX - 1.15, EX - 0.38, EX + 0.38, EX + 1.15]; STY = 3.9
F_COAT = dress_form('fcoat', HALL, (STAND_X[0], STY, PLAT_Z), head=False)
F_PANT = dress_form('fpant', HALL, (STAND_X[1], STY, PLAT_Z), head=False, legs=True)
F_SUIT = dress_form('fsuit', HALL, (STAND_X[2], STY, PLAT_Z), head=False, legs=True)
F_CAP = empty('fcap', HALL, loc=(STAND_X[3], STY, PLAT_Z))
lathe('fcapbase', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.03, 0.05), (0.025, 1.2), (0.0, 1.2)], 20, M_BLACK, F_CAP)
prim('uv_sphere', 'fcaphead', M_DUMMY, F_CAP, loc=(0, 0, 1.32), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
CL = {}                                                            # the four garments, each an empty that flies in
CL['coat'] = empty('cl_coat', F_COAT)
garment('coatm', [(0.25, 0.55), (0.215, 0.85), (0.18, 1.08), (0.195, 1.30), (0.22, 1.42), (0.15, 1.51), (0.07, 1.55)], M_VIOLET, CL['coat'], open_front=34)
for s_ in (-1, 1): tube(f'coatsl{s_}', [(s_ * 0.21, 0, 1.43), (s_ * 0.245, 0.0, 1.2), (s_ * 0.24, -0.02, 0.95)], lambda u: 0.06 - 0.008 * u, M_VIOLET, CL['coat'], seg=12)
for k in range(6): prim('uv_sphere', f'coatbtn{k}', M_PEWTER, CL['coat'], loc=(0.03, -0.155, 1.42 - 0.08 * k), segments=8, ring_count=5, radius=0.009)
CL['pants'] = empty('cl_pants', F_PANT)
for s_ in (-1, 1): lathe(f'pantleg{s_}', [(0.075, 0.52), (0.10, 0.6), (0.112, 0.74), (0.105, 0.88)], 18, M_GREENC, CL['pants'], loc=(s_ * 0.075, 0, 0))
garment('pantseat', [(0.19, 0.8), (0.18, 0.92), (0.16, 1.0)], M_GREENC, CL['pants'])
for s_ in (-1, 1): lathe(f'pantgart{s_}', [(0.078, 0.515), (0.084, 0.515), (0.084, 0.54), (0.078, 0.54)], 18, M_LEATHER, CL['pants'], loc=(s_ * 0.075, 0, 0))
CL['suit'] = empty('cl_suit', F_SUIT)
garment('suitd', [(0.17, 0.95), (0.165, 1.12), (0.185, 1.30), (0.21, 1.42), (0.145, 1.505), (0.06, 1.545)], M_BLUEC, CL['suit'])
for s_ in (-1, 1):
    lathe(f'suitleg{s_}', [(0.075, 0.52), (0.10, 0.6), (0.112, 0.74), (0.105, 0.88)], 18, M_BLUEC, CL['suit'], loc=(s_ * 0.075, 0, 0))
    tube(f'suitsl{s_}', [(s_ * 0.2, 0, 1.43), (s_ * 0.23, 0.0, 1.2), (s_ * 0.22, -0.03, 0.98)], lambda u: 0.055 - 0.01 * u, M_BLUEC, CL['suit'], seg=12)
garment('suitseat', [(0.19, 0.8), (0.18, 0.92), (0.17, 0.97)], M_BLUEC, CL['suit'])
collar('suitcol', CL['suit'], 1.535, 0.055, 0.15)
for k in range(7): prim('uv_sphere', f'suitbtn{k}', M_PEWTER, CL['suit'], loc=(0, -0.128, 1.44 - 0.065 * k), segments=8, ring_count=5, radius=0.008)
CL['cap'] = empty('cl_cap', F_CAP)
lathe('capm', [(0.0, 1.47), (0.05, 1.465), (0.09, 1.43), (0.108, 1.36), (0.112, 1.31), (0.0, 1.31)], 24, M_REDC, CL['cap']).scale = (1.0, 1.1, 1.0)
lathe('capband', [(0.112, 1.29), (0.12, 1.29), (0.122, 1.35), (0.113, 1.35)], 24, M_REDC, CL['cap']).scale = (1.0, 1.1, 1.0)
placard('plaq2', (EX + 1.9, 2.5, 0), -14, "BREWSTER'S\nCLOTHES, 1644")

# ================================================================ exhibit 4: the buckles pop off (x = 13.0)
BX = 13.0
box('bplat', (2.0, 1.8, PLAT_Z), (BX, 3.6, PLAT_Z / 2), M_PLAT, bv=0.01, parent=HALL)
BH = empty('bhead', HALL, loc=(BX - 0.35, 3.6, PLAT_Z))
lathe('bhbase', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.03, 0.05), (0.025, 1.05), (0.0, 1.05)], 20, M_BLACK, BH)
prim('uv_sphere', 'bhhead', M_DUMMY, BH, loc=(0, 0, 1.17), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
HAT2, HB2 = capotain('hat2', BH); HAT2.location = (0, 0, 1.23)
box('shoeplinth', (0.6, 0.45, 0.45), (BX + 0.45, 3.55, PLAT_Z + 0.225), M_WOOD, bv=0.01, parent=HALL)
SH = []
for k, s_ in enumerate((-1, 1)):
    r_, b_ = shoe(f'shoe{k}', HALL); r_.location = (BX + 0.45 + s_ * 0.08, 3.5, PLAT_Z + 0.45); r_.rotation_euler = (0, 0, s_ * R(-8)); SH.append((r_, b_))
BUCKLES = [HB2, SH[0][1], SH[1][1]]
placard('plaq4', (BX + 1.1, 2.4, 0), -12, 'BUCKLES?')

# ================================================================ exhibit 5: the price of black - dye jars and coins, a portrait in Sunday best (x = 16.2)
DX = 16.2
box('dtab', (1.8, 0.7, 0.05), (DX, 3.7, 0.95), M_WOOD, bv=0.01, parent=HALL)
for s_ in (-1, 1):
    for s2 in (-1, 1): box(f'dtl{s_}{s2}', (0.05, 0.05, 0.93), (DX + s_ * 0.82, 3.7 + s2 * 0.28, 0.465), M_WOOD, parent=HALL)
DYES = [((0.55, 0.06, 0.04), 'MADDER'), ((0.06, 0.12, 0.42), 'WOAD'), ((0.75, 0.62, 0.10), 'WELD'), ((0.28, 0.07, 0.32), 'ORCHIL'), ((0.015, 0.015, 0.018), 'BLACK')]
for k, (c_, nm) in enumerate(DYES):
    x_ = DX - 0.66 + 0.33 * k; base_ = Vector((x_, 3.62, 0.975))
    lathe(f'jar{k}', [(0.0, 0.0), (0.07, 0.0), (0.11, 0.04), (0.125, 0.085), (0.115, 0.09), (0.10, 0.05), (0.0, 0.03)], 28, M_WOOD, HALL, loc=base_)
    lathe(f'dye{k}', [(0.0, 0.14), (0.04, 0.13), (0.08, 0.105), (0.112, 0.08), (0.0, 0.08)], 24, noisy(mat(f'dyem{k}', tuple(min(1.0, x * 1.4) for x in c_), 0.95), 60.0, 0.45), HALL, loc=base_)
    text3d(f'jarl{k}', nm, 0.03, base_ + Vector((0, -0.16, 0.002)), (R(20), 0, 0), M_INK, HALL, extrude=0.001)
    sw = box(f'swatch{k}', (0.24, 0.01, 0.32), (x_, 4.12, 1.28), cloth_mat(f'swm{k}', c_ if k < 4 else (0.02, 0.02, 0.022), seed=float(k)), parent=HALL)
    tube(f'peg{k}', [(x_, 4.1, 1.45), (x_, 4.25, 1.45)], 0.01, M_WOOD, HALL, seg=6)
COINS = []
for k in range(10):
    o = prim('cylinder', f'coin{k}', M_GOLD, HALL, loc=(DX + 0.6 + 0.004 * math.sin(k * 2.1), 3.42, 0.982 + 0.015 * k), vertices=28, radius=0.045, depth=0.013); o.scale = (0.0,) * 3; COINS.append(o)
PORT = empty('portrait', HALL, loc=(DX, 5.33, 2.75))
box('poframe', (1.0, 0.06, 1.3), (0, 0.0, 0), M_GILT, bv=0.02, parent=PORT)
M_PTBG = noisy(mat('ptbg', (0.10, 0.08, 0.05), 0.8), 4.0, 0.4)
box('pocanv', (0.84, 0.02, 1.14), (0, -0.03, 0), M_PTBG, parent=PORT)
M_SKIN = noisy(mat('pskin', (0.62, 0.42, 0.30), 0.6), 15.0, 0.15); M_HAIR = noisy(mat('phair', (0.12, 0.08, 0.05), 0.8), 30.0, 0.3)
def flat(name, pts2, m, parent, y=-0.042, smooth=False):
    o = mesh(name, [(x_, y, z_) for x_, z_ in pts2], [tuple(range(len(pts2)))][::1], m, parent, smooth_=smooth); return o
flat('pobody', [(-0.38, -0.57), (0.38, -0.57), (0.36, -0.25), (0.24, -0.08), (0.08, -0.02), (-0.08, -0.02), (-0.24, -0.08), (-0.36, -0.25)], M_BLACKCL, PORT)
flat('pocollar', [(-0.16, -0.03), (0.16, -0.03), (0.12, -0.14), (0.0, -0.18), (-0.12, -0.14)], M_LINEN, PORT, y=-0.044)
flat('poface', [(0.13 * math.sin(2 * math.pi * i / 24), 0.13 + 0.17 * math.cos(2 * math.pi * i / 24)) for i in range(24)], M_SKIN, PORT, y=-0.043)
flat('pohair', [(-0.14, 0.13), (-0.15, 0.26), (-0.09, 0.32), (0.0, 0.33), (0.09, 0.32), (0.15, 0.26), (0.14, 0.13), (0.12, 0.2), (0.0, 0.26), (-0.12, 0.2)], M_HAIR, PORT, y=-0.0435)
for s_ in (-1, 1): flat(f'poeye{s_}', [(s_ * 0.05 + 0.018 * math.cos(2 * math.pi * i / 10), 0.17 + 0.008 * math.sin(2 * math.pi * i / 10)) for i in range(10)], M_INK, PORT, y=-0.0445)
flat('pomouth', [(-0.035, 0.035), (0.035, 0.035), (0.03, 0.045), (-0.03, 0.045)], noisy(mat('plip', (0.35, 0.15, 0.12), 0.6), 10.0, 0.1), PORT, y=-0.0445)
for k in range(5): prim('uv_sphere', f'pobtn{k}', M_GOLD, PORT, loc=(0, -0.045, -0.22 - 0.07 * k), segments=8, ring_count=5, radius=0.012, scale=(1, 0.3, 1))
text3d('potxt', 'PORTRAIT, 1651', 0.05, (0, -0.04, -0.72), (R(90), 0, 0), M_GILT, PORT, extrude=0.002)

# ================================================================ exhibit 6: an 1800s artist paints the buckles on (x = 19.4)
AX = 19.4
EASEL = empty('easel', HALL, loc=(AX, 3.0, 0)); EASEL.rotation_euler = (0, 0, R(-8))
for s_ in (-1, 1): tube(f'easleg{s_}', [(s_ * 0.38, 0.0, 0.0), (s_ * 0.1, 0.06, 2.05)], 0.022, M_WOODRAW, EASEL, seg=6)
tube('easback', [(0, 0.5, 0.0), (0, 0.04, 1.9)], 0.022, M_WOODRAW, EASEL, seg=6)
box('eastray', (0.95, 0.07, 0.035), (0, -0.07, 0.86), M_WOODRAW, parent=EASEL)
CANV = empty('canvas', EASEL, loc=(0, -0.11, 1.27)); CANV.rotation_euler = (R(-8), 0, 0)
box('cvframe', (0.92, 0.03, 0.78), (0, 0.01, 0), M_WOODRAW, parent=CANV)
M_CSKY = noisy(mat('csky', (0.55, 0.50, 0.42), 0.9), 5.0, 0.3); M_CGRD = noisy(mat('cgrd', (0.30, 0.25, 0.12), 0.9), 7.0, 0.3)
flat('cvsky', [(-0.44, 0.0), (0.44, 0.0), (0.44, 0.37), (-0.44, 0.37)], M_CSKY, CANV, y=-0.006)
flat('cvgrd', [(-0.44, -0.37), (0.44, -0.37), (0.44, 0.02), (0.2, 0.05), (-0.1, 0.01), (-0.44, 0.04)], M_CGRD, CANV, y=-0.007)
PAINT = []                                                         # the strokes, in order: two figures in black, collars, faces, hats, then the buckles
for k, fx in enumerate((-0.17, 0.17)):
    PAINT.append(flat(f'cvbody{k}', [(fx - 0.1, -0.33), (fx + 0.1, -0.33), (fx + 0.09, 0.0), (fx + 0.05, 0.07), (fx - 0.05, 0.07), (fx - 0.09, 0.0)], M_BLACKCL, CANV, y=-0.009))
    PAINT.append(flat(f'cvcol{k}', [(fx - 0.06, 0.07), (fx + 0.06, 0.07), (fx + 0.04, 0.03), (fx, 0.015), (fx - 0.04, 0.03)], M_LINEN, CANV, y=-0.010))
    PAINT.append(flat(f'cvface{k}', [(fx + 0.035 * math.sin(2 * math.pi * i / 16), 0.11 + 0.042 * math.cos(2 * math.pi * i / 16)) for i in range(16)], M_SKIN, CANV, y=-0.010))
for k, fx in enumerate((-0.17, 0.17)):
    PAINT.append(flat(f'cvhat{k}', [(fx - 0.075, 0.145), (fx + 0.075, 0.145), (fx + 0.075, 0.158), (fx + 0.042, 0.158), (fx + 0.036, 0.26), (fx - 0.036, 0.26), (fx - 0.042, 0.158), (fx - 0.075, 0.158)], M_FELT, CANV, y=-0.011))
for k, fx in enumerate((-0.17, 0.17)):
    PAINT.append(flat(f'cvbk{k}', [(fx - 0.02, 0.163), (fx + 0.02, 0.163), (fx + 0.02, 0.193), (fx - 0.02, 0.193)], M_BUCKLE, CANV, y=-0.013))
    PAINT.append(flat(f'cvshoebk{k}', [(fx - 0.06, -0.345), (fx - 0.03, -0.345), (fx - 0.03, -0.325), (fx - 0.06, -0.325)], M_BUCKLE, CANV, y=-0.013))
PAINT_C = [Vector((sum(v.co.x for v in o.data.vertices) / len(o.data.vertices), 0, sum(v.co.z for v in o.data.vertices) / len(o.data.vertices))) for o in PAINT]
BRUSH = empty('brush', CANV, loc=(0, -0.05, 0))
tube('brhandle', [(0, 0, 0.0), (0.06, -0.12, 0.28)], lambda u: 0.006 + 0.004 * u, M_RED, BRUSH, seg=8)
tube('brferrule', [(0, 0, 0.0), (-0.006, 0.012, -0.03)], 0.007, M_SILV, BRUSH, seg=8)
prim('cone', 'brtip', M_BLACKCL, BRUSH, loc=(-0.008, 0.016, -0.045), rot=(R(160), 0, 0), vertices=8, radius1=0.007, radius2=0.0, depth=0.03)
PAL = empty('palette', HALL, loc=(AX + 0.62, 2.85, 0.92))
prim('cylinder', 'palm', M_WOODRAW, PAL, vertices=24, radius=0.16, depth=0.01, scale=(1.3, 1.0, 1))
for k, c_ in enumerate(((0.02, 0.02, 0.02), (0.85, 0.84, 0.8), (0.9, 0.7, 0.2), (0.6, 0.4, 0.3), (0.4, 0.3, 0.15))):
    prim('uv_sphere', f'pal{k}', mat(f'palc{k}', c_, 0.3), PAL, loc=(0.14 * math.cos(k * 0.9), 0.1 * math.sin(k * 0.9), 0.008), segments=10, ring_count=6, radius=0.025, scale=(1, 1, 0.35))
box('ptab', (0.5, 0.4, 0.04), (AX + 0.62, 2.85, 0.88), M_WOOD, parent=HALL)
for s_ in (-1, 1): box(f'ptl{s_}', (0.04, 0.04, 0.86), (AX + 0.62 + s_ * 0.2, 2.85, 0.43), M_WOOD, parent=HALL)
placard('plaq6', (AX - 1.1, 2.0, 0), 12, 'PAINTED\n1800s')

# ================================================================ exhibit 7: the same trick on Santa - a red suit with a big buckled belt, a Pilgrim hat beside it (x = 22.3)
SX = 22.3
box('splat', (2.6, 2.0, PLAT_Z), (SX, 3.8, PLAT_Z / 2), M_PLAT, bv=0.01, parent=HALL)
F_SANTA = dress_form('fsanta', HALL, (SX + 0.25, 3.8, PLAT_Z))
garment('scoat', [(0.27, 0.6), (0.25, 0.85), (0.24, 1.05), (0.235, 1.20), (0.23, 1.32), (0.225, 1.42), (0.15, 1.51), (0.07, 1.55)], M_SANTA, F_SANTA)
lathe('sfurhem', [(0.27, 0.56), (0.30, 0.56), (0.30, 0.66), (0.27, 0.66)], 32, M_FUR, F_SANTA).scale = (1.0, 0.72, 1.0)
box('sfurfront', (0.07, 0.03, 0.88), (0.0, -0.18, 1.06), M_FUR, bv=0.02, parent=F_SANTA)
lathe('sbelt', [(0.242, 1.0), (0.25, 1.0), (0.25, 1.085), (0.242, 1.085)], 40, M_LEATHER, F_SANTA).scale = (1.0, 0.74, 1.0)
SBK = buckle('sbuckle', F_SANTA, 0.15, 0.115, 0.016, 0.016, loc=(0, -0.19, 1.0425))
for s_ in (-1, 1):
    tube(f'ssl{s_}', [(s_ * 0.22, 0, 1.43), (s_ * 0.26, 0.0, 1.2), (s_ * 0.25, -0.03, 0.98)], lambda u: 0.07 - 0.01 * u, M_SANTA, F_SANTA, seg=12)
    lathe(f'scuff{s_}', [(0.06, 0.0), (0.075, 0.0), (0.075, 0.06), (0.06, 0.06)], 16, M_FUR, F_SANTA, loc=(s_ * 0.25, -0.03, 0.93))
lathe('shat', [(0.0, 2.15), (0.03, 2.1), (0.07, 1.98), (0.105, 1.85), (0.115, 1.78), (0.0, 1.78)], 24, M_SANTA, F_SANTA)
lathe('shatfur', [(0.11, 1.74), (0.135, 1.74), (0.135, 1.81), (0.11, 1.81)], 24, M_FUR, F_SANTA)
prim('uv_sphere', 'shatpom', M_FUR, F_SANTA, loc=(0, 0, 2.17), segments=12, ring_count=8, radius=0.035)
for k, s_ in enumerate((-1, 1)):
    bt = empty(f'sboot{k}', HALL, loc=(SX + 0.25 + s_ * 0.12, 3.45, PLAT_Z))
    lathe(f'sbootl{k}', [(0.0, 0.0), (0.06, 0.0), (0.065, 0.25), (0.07, 0.3), (0.0, 0.3)], 16, M_LEATHER, bt)
    prim('uv_sphere', f'sboott{k}', M_LEATHER, bt, loc=(0, -0.08, 0.04), segments=16, ring_count=8, radius=1.0, scale=(0.05, 0.1, 0.045))
    lathe(f'sbootf{k}', [(0.07, 0.28), (0.085, 0.28), (0.085, 0.34), (0.07, 0.34)], 16, M_FUR, bt)
    buckle(f'sbootbk{k}', bt, 0.05, 0.04, 0.007, 0.006, loc=(0, -0.066, 0.18))
PH = empty('phstand', HALL, loc=(SX - 0.55, 3.8, PLAT_Z))
lathe('phbase', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.03, 0.05), (0.025, 1.1), (0.0, 1.1)], 20, M_BLACK, PH)
prim('uv_sphere', 'phhead', M_DUMMY, PH, loc=(0, 0, 1.22), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
HAT3, HB3 = capotain('hat3', PH); HAT3.location = (0, 0, 1.28); HAT3.rotation_euler = (0, 0, R(10))
TREE = empty('xtree', HALL, loc=(SX + 1.05, 4.2, PLAT_Z))
M_PINE = noisy(mat('pine', (0.03, 0.10, 0.04), 0.8), 20.0, 0.3)
for k in range(4): prim('cone', f'xt{k}', M_PINE, TREE, loc=(0, 0, 0.4 + 0.32 * k), vertices=16, radius1=0.42 - 0.08 * k, radius2=0.05, depth=0.6)
TLIGHTS = []
for k in range(24):
    h_ = 0.25 + 1.2 * k / 24; r_ = 0.42 * (1 - h_ / 1.75) + 0.03; a_ = k * 2.4
    o = prim('uv_sphere', f'xl{k}', emis(f'xlm{k}', ((1.0, 0.3, 0.2), (1.0, 0.85, 0.3), (0.3, 0.6, 1.0))[k % 3], 6.0), TREE, loc=(r_ * math.cos(a_), r_ * math.sin(a_), h_), segments=8, ring_count=5, radius=0.018); TLIGHTS.append(o)
prim('ico_sphere', 'xstar', emis('xstarm', (1.0, 0.85, 0.4), 8.0), TREE, loc=(0, 0, 1.78), subdivisions=1, radius=0.06)
placard('plaq7', (SX - 1.2, 2.5, 0), 12, 'SAME\nTRICK')
# ================================================================ moving bits: falling leaves, the garments' flights, the buckles' flights, the glints
GA = random.Random(23)
LEAVES = []
for k in range(55):
    lf = leaf_mesh(f'fl{k}', M_LEAVES[k % 5], None, GA.uniform(0.028, 0.045)); lf.rotation_mode = 'XYZ'
    LEAVES.append((lf, GA.uniform(-2.2, 2.2), GA.uniform(0.2, 3.5), GA.uniform(0, 3.9), GA.uniform(0.28, 0.45), GA.uniform(0, 6.3)))
ITEM_T = [B[3] + 1.55, B[3] + 2.4, B[3] + 3.05, B[3] + 3.65]          # violet coat, green pants, blue suit, red cap (as they're said)
ORDER = ['coat', 'pants', 'suit', 'cap']; FORMS = {'coat': F_COAT, 'pants': F_PANT, 'suit': F_SUIT, 'cap': F_CAP}
FLY = {}
for k, nm in enumerate(ORDER):
    z_ = -0.17 - 0.115 * k
    src = Vector((EX - 0.15, 5.25, 2.75 + z_)); ctr = Vector((0, 0, 1.1 if nm != 'cap' else 1.38))
    FLY[nm] = (src - FORMS[nm].location - ctr, ITEM_T[k], ctr)
BUCK_T = [B[4] + 0.18, B[4] + 0.36, B[4] + 0.5]
BUCK_V = [Vector((-0.35, -0.7, 2.0)), Vector((-0.25, -0.6, 1.8)), Vector((0.3, -0.6, 1.9))]
BUCK_REST = [(b.location.copy(), b.rotation_euler.copy()) for b in BUCKLES]
BUCK_FLOOR = [-(1.23 + 0.032) + PLAT_Z * 0.0 + 0.006, -0.068 + 0.006, -0.068 + 0.006]   # local z of the floor under each buckle
M_GLINT = emis('glintm', (1.0, 0.95, 0.8), 25.0)
def glint(name, loc):
    vs = [(0, 0, 0)]; fs = []
    for i in range(8):
        a = math.pi / 4 * i; r_ = 0.07 if i % 2 == 0 else 0.012; vs.append((r_ * math.cos(a), 0, r_ * math.sin(a)))
    for i in range(8): fs.append((0, 1 + i, 1 + (i + 1) % 8))
    o = mesh(name, vs, fs, M_GLINT, None, smooth_=False, loc=loc); o.scale = (0.0,) * 3; return o
GL1 = glint('gl1', Vector((SX + 0.25 + 0.05, 3.8 - 0.21, PLAT_Z + 1.07)))
GL2 = glint('gl2', Vector((SX - 0.55 + 0.02, 3.8 - 0.13, PLAT_Z + 1.28 + 0.045)))
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
    key(0.0, (0.12, 1.15, 2.2), (0.12, 2.55, 2.25), 30),                  # the buckled hat drops onto the Pilgrim's head
    key(0.9, (0.14, 1.2, 2.18), (0.12, 2.55, 2.22), 30),
    key(3.0, (0.75, -0.2, 1.85), (0.0, 2.3, 1.45), 26),                    # back a little: the harvest table, the two Pilgrims in black
    key(B[1] - 0.05, (0.7, -0.25, 1.85), (0.0, 2.3, 1.45), 26),
    key(B[1] + 1.7, (1.4, -6.4, 2.45), (0.4, 1.6, 1.85), 24),             # pull way back: a diorama in a museum
    key(B[2] - 0.05, (1.5, -6.5, 2.47), (0.45, 1.6, 1.85), 24),
    key(B[2] + 1.2, (EX, 3.05, 2.75), (EX, 5.3, 2.72), 30),               # the inventory page writes itself
    key(B[3] - 0.05, (EX, 3.1, 2.73), (EX, 5.3, 2.72), 30),
    key(B[3] + 1.2, (EX, 0.4, 2.05), (EX, 4.2, 1.6), 22),                 # back: the page and four stands; the clothes fly in
    key(B[4] - 0.45, (EX, 0.5, 2.0), (EX, 4.2, 1.6), 22),
    key(B[4] + 0.3, (BX + 0.05, 2.1, 1.45), (BX + 0.05, 3.5, 1.15), 24),  # the buckles pop off
    key(B[5] - 0.05, (BX + 0.05, 2.15, 1.43), (BX + 0.05, 3.5, 1.15), 24),
    key(B[5] + 0.7, (DX + 0.16, 1.95, 1.6), (DX + 0.16, 3.7, 1.1), 24),                 # the dye jars, coins stack by the black
    key(B[5] + 1.9, (DX + 0.16, 1.97, 1.62), (DX + 0.16, 3.7, 1.12), 24),
    key(B[5] + 3.0, (DX, 2.6, 2.55), (DX, 5.3, 2.8), 28),                 # up to the portrait in Sunday black
    key(B[6] - 0.05, (DX + 0.02, 2.65, 2.55), (DX, 5.3, 2.8), 28),
    key(B[6] + 0.9, (AX - 0.05, 1.6, 1.45), (AX, 2.95, 1.33), 25),        # the 1800s artist paints the buckles on
    key(B[7] - 0.05, (AX - 0.03, 1.65, 1.43), (AX, 2.95, 1.33), 25),
    key(B[7] + 0.9, (SX - 0.35, 1.45, 1.75), (SX - 0.1, 3.6, 1.45), 23),  # the same buckle on Santa
    key(B[8] - 0.05, (SX - 0.32, 1.5, 1.73), (SX - 0.1, 3.6, 1.45), 23),
    key(TOTAL, (SX - 0.25, 2.1, 1.55), (SX - 0.15, 3.6, 1.4), 26),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- the hat drops onto the Pilgrim, bounces, settles
    T_HIT = 0.32
    if t < T_HIT:
        u = (t + 0.25) / (T_HIT + 0.25); HAT1.location = HAT1_P + Vector((0, 0, 1.0 * (1 - u * u))); HAT1.rotation_euler = (R(8) * (1 - u), R(-6) * (1 - u), R(50) * (1 - u))
        HAT1.scale = (1, 1, 1)
    else:
        d = t - T_HIT; b_ = 0.035 * abs(math.sin(d * 13)) * math.exp(-d * 7)
        HAT1.location = HAT1_P + Vector((0, 0, b_)); w_ = R(3) * math.sin(d * 17) * math.exp(-d * 6); HAT1.rotation_euler = (w_, -w_ * 0.6, 0)
        sq = 0.12 * math.exp(-d * 18) * math.cos(d * 30); HAT1.scale = (1 + sq * 0.5, 1 + sq * 0.5, 1 - sq)
    # ---- leaves drift down through the diorama (fade out once the room is lit)
    lf_on = t < B[1] + 0.9
    for o, x0, y0, ph, sp, rot in LEAVES:
        if not lf_on: o.location = (0, 0, -50); continue
        z = 4.2 - ((t * sp + ph) % 3.85)
        o.location = (x0 + 0.15 * math.sin(t * 2.1 + rot), y0 + 0.08 * math.cos(t * 1.7 + rot), z)
        o.rotation_euler = (math.sin(t * 3 + rot) * 0.9, math.cos(t * 2.4 + rot) * 0.7, t * 1.5 + rot)
    # ---- the museum lights come up as the diorama is revealed
    ml = smooth(B[1] + 0.1, B[1] + 0.9, t)
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * ml; lt.hide_render = ml < 0.002
    # ---- the page: scribbled lines during B2, then the four items as they're named; the quill follows the writing
    qp = Vector((0.35, -0.08, -0.62)); qa = 0.0
    for k, (o, x0, L_) in enumerate(SCRIB):
        s = clamp((t - (B[2] + 0.25 + 0.5 * k)) / 0.45, 0, 1)
        o.scale = (max(s, 0.0001), 1, 1); o.location.x = x0 * (1 - s); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((x0 + L_ * s, -0.08, 0.32 - 0.075 * k)); qa = 1.0
    for k, o in enumerate(ITEMT):
        s = clamp((t - (ITEM_T[k] - 0.2)) / 0.4, 0, 1); o.scale = (max(s, 0.0001), 1, 1); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((-0.48 + 0.42 * s, -0.08, -0.17 - 0.115 * k)); qa = 1.0
    QUILL.location = qp + Vector((0, 0, 0.008 * math.sin(t * 60) * qa)); QUILL.rotation_euler = (0, R(-10) + 0.15 * math.sin(t * 25) * qa, 0)
    # ---- the clothes fly off the page onto their stands, growing as they come, a turn and a flutter
    for nm, (off, t0, ctr) in FLY.items():
        o = CL[nm]; u = smooth(t0, t0 + 0.6, t)
        if u <= 0: o.scale = (0.0001,) * 3; o.hide_render = True; continue
        o.hide_render = False; s = 0.15 + 0.85 * u
        lift = 0.25 * math.sin(math.pi * u)
        pos = off * (1 - u) + Vector((0, 0, lift)); rz = R(200) * (1 - u) ** 1.5; tilt = R(25) * math.sin(math.pi * u)
        m_ = Matrix.Translation(ctr + pos) @ Euler((tilt, 0, rz)).to_matrix().to_4x4() @ Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-ctr)
        o.matrix_basis = m_
        if 0.999 > u > 0.9: pass
        settle = 0.03 * math.sin((t - t0 - 0.6) * 20) * math.exp(-(t - t0 - 0.6) * 9) if t > t0 + 0.6 else 0.0
        if settle: o.matrix_basis = Matrix.Translation(ctr) @ Euler((0, 0, settle)).to_matrix().to_4x4() @ Matrix.Translation(-ctr)
    # ---- the buckles pop off the hat and the shoes, spin, and land on the floor
    for k, b_ in enumerate(BUCKLES):
        l0, r0 = BUCK_REST[k]; tau = t - BUCK_T[k]
        if tau <= 0: b_.location = l0; b_.rotation_euler = r0; continue
        p_ = l0 + BUCK_V[k] * tau + Vector((0, 0, -4.9 * tau * tau))
        if p_.z <= BUCK_FLOOR[k]:
            tl = (BUCK_V[k].z + math.sqrt(BUCK_V[k].z ** 2 + 2 * 9.8 * (l0.z - BUCK_FLOOR[k]))) / 9.8
            p_ = l0 + BUCK_V[k] * tl + Vector((0, 0, -4.9 * tl * tl)); p_.z = BUCK_FLOOR[k]
            b_.location = p_; b_.rotation_euler = (R(90), 0, R(30) * k); continue
        b_.location = p_; b_.rotation_euler = (r0.x + tau * 14, r0.y + tau * 6, r0.z + tau * 9)
    # ---- the coins stack up beside the black dye
    for k, o in enumerate(COINS):
        u = clamp((t - (B[5] + 0.5 + 0.11 * k)) / 0.18, 0, 1); s = u * u * (3 - 2 * u) + 0.25 * math.sin(math.pi * u)
        o.scale = (max(s, 0.0001), max(s, 0.0001), max(s, 0.0001)); o.hide_render = u <= 0
    # ---- the artist paints: each stroke grows from its middle; the brush goes where the paint goes
    bp = Vector((0.3, -0.05, -0.2)); act = 0.0
    for k, o in enumerate(PAINT):
        t0 = B[6] + 0.3 + 0.3 * k; s = clamp((t - t0) / 0.28, 0, 1); c_ = PAINT_C[k]
        o.scale = (max(s, 0.0001), 1, max(s, 0.0001)); o.location = Vector((c_.x * (1 - s), 0, c_.z * (1 - s))); o.hide_render = s <= 0
        if t0 - 0.12 <= t <= t0 + 0.3: bp = Vector((c_.x, -0.05, c_.z)); act = 1.0
    BRUSH.location = bp + Vector((0.01 * math.sin(t * 40) * act, 0, 0.008 * math.cos(t * 33) * act))
    # ---- Santa: the tree twinkles, the two buckles glint
    for k, o in enumerate(TLIGHTS): o.scale = (0.7 + 0.3 * math.sin(t * 5 + k * 1.7),) * 3
    for g_, t0 in ((GL1, B[7] + 1.4), (GL2, B[7] + 2.4), (GL1, B[8] + 0.6), (GL2, B[8] + 1.2)):
        u = clamp((t - t0) / 0.35, 0, 1)
        if 0 < u < 1: s = math.sin(math.pi * u); g_.scale = (s, s, s); g_.rotation_euler = (0, u * 1.2, 0); g_.hide_render = False
    if all(not (0 < (t - t0) < 0.35) for t0 in (B[7] + 1.4, B[8] + 0.6)): GL1.hide_render = True
    if all(not (0 < (t - t0) < 0.35) for t0 in (B[7] + 2.4, B[8] + 1.2)): GL2.hide_render = True
    # ---- camera, with a little life in it (a nod when the hat lands)
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3) + (shake(t, 0.02, 4.0, 13.0) * math.exp(-max(0, t - 0.32) * 6.0) if t > 0.32 else Vector())
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

