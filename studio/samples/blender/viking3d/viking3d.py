# Viking horns myth: a wave smashes over a longship bow where a horned helmet sits; it is a museum diorama. The 1943 Gjermundbu grave and its
# nine-piece hornless helmet, horns snagging in a fight, the 1876 Bayreuth opera stage and Doepler's costumes, a shelf of horned helmets,
# and out the window to a Danish bog where two Bronze Age horned helmets turn up. One continuous shot.
#   python3 viking3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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

def bronze_mat(name, patina=0.45, seed=0.0):
    """old bronze: warm metal, green-blue patina in the low spots, dark grime"""
    m = mat(name, (0.55, 0.36, 0.16), 0.32, 1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed * 2.3, seed * 1.1, seed * 0.4); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 9.0, 8.0, 0.3); fine = tnoise(nt, mp.outputs['Vector'], 45.0, 4.0)
    pf = ramp_v(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', big, 0.8), math_(nt, 'MULTIPLY', fine, 0.2)), 0.62 - patina * 0.3, 0.70 - patina * 0.2)
    metal_c = mixc(nt, fine, (0.62, 0.40, 0.17), (0.40, 0.25, 0.10))
    pat_c = mixc(nt, tnoise(nt, mp.outputs['Vector'], 20.0, 5.0), (0.16, 0.34, 0.27), (0.07, 0.17, 0.12))
    nt.links.new(mixc(nt, pf, metal_c, pat_c), b.inputs['Base Color'])
    mt = nt.nodes.new('ShaderNodeMapRange'); mt.inputs['To Min'].default_value = 1.0; mt.inputs['To Max'].default_value = 0.0; nt.links.new(pf, mt.inputs['Value']); nt.links.new(mt.outputs['Result'], b.inputs['Metallic'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.28; mr.inputs['To Max'].default_value = 0.85; nt.links.new(pf, mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.003
    nt.links.new(math_(nt, 'ADD', tnoise(nt, mp.outputs['Vector'], 120.0, 3.0), math_(nt, 'MULTIPLY', pf, 0.5)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def horn_mat(name, base=(0.55, 0.45, 0.30), tip=(0.08, 0.05, 0.03)):
    """cow horn: cream at the root, dark at the tip (Generated z of the tube runs root -> tip), fine growth rings"""
    m = mat(name, base, 0.35, coat=0.4); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    g = sepz(nt, coord(nt, 'Generated'))
    zz = math_(nt, 'ADD', math_(nt, 'MULTIPLY', g.outputs['Z'], objattr(nt, 'tz')), math_(nt, 'MULTIPLY', g.outputs['X'], objattr(nt, 'tx')))
    zz = math_(nt, 'ADD', zz, objattr(nt, 'toff'))
    rings = tnoise(nt, coord(nt, 'Object'), 60.0, 2.0)
    c_ = ramp(nt, zz, [(0.0, base), (0.55, tuple(c * 0.85 for c in base)), (0.85, (0.35, 0.25, 0.15)), (1.0, tip)])
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', rings, 0.25), c_, tuple(c * 0.7 for c in base)), b.inputs['Base Color'])
    return m


def steel_mat(name, seed=0.0):
    m = iron_mat(name, 0.06, base=(0.32, 0.31, 0.30), rust_col=(0.12, 0.06, 0.03), seed=seed)
    return m


def horn_tube(name, side, parent, m, length=1.0, up=1.0):
    """a curved horn out of the side of a helmet: out, up, then forward; side = -1 / +1 (x direction); root at origin"""
    pts = []
    for i in range(16):
        u = i / 15
        pts.append(Vector((side * (0.03 + 0.13 * u - 0.02 * u * u) * length, -0.06 * u * u * length, (0.02 * u + 0.17 * u * u * up) * length)))
    o = tube(name, pts, lambda u: (0.040 - 0.036 * u ** 0.7) * length, m, parent, seg=16)
    o['tz'] = 0.75; o['tx'] = 0.25 if side > 0 else -0.25; o['toff'] = 0.25 if side < 0 else 0.0; o['tipdir'] = 1.0
    return o


DOME = [(0.0, 0.205), (0.05, 0.200), (0.09, 0.185), (0.12, 0.155), (0.14, 0.11), (0.150, 0.055), (0.152, 0.0)]


def horned_helmet(name, parent, m_metal, m_trim, m_horn, wings=False):
    """the opera / myth helmet: polished dome, brass brow band and cross straps, rivets, nose guard, two horns (or wings). base at origin, faces -y"""
    root = empty(name, parent)
    lathe(name + '_dome', DOME, 40, m_metal, root)
    lathe(name + '_brow', [(0.150, -0.005), (0.160, -0.005), (0.162, 0.04), (0.152, 0.04)], 40, m_trim, root)
    for k in range(2):
        a_ = math.pi / 2 * k
        arc = []
        for i in range(21):
            th = -math.pi / 2 + math.pi * i / 20; rr = dome_r(abs(th))                 # follow the dome surface at polar angle th
            arc.append(Vector((math.cos(a_) * rr[0] * math.copysign(1, th), math.sin(a_) * rr[0] * math.copysign(1, th), rr[1])))
        tube(f'{name}_strap{k}', arc, 0.009, m_trim, root, seg=8)
    for i in range(16):
        an = 2 * math.pi * i / 16; prim('uv_sphere', f'{name}_rv{i}', m_trim, root, loc=(0.163 * math.cos(an), 0.163 * math.sin(an), 0.018), segments=8, ring_count=5, radius=0.007)
    box(name + '_nose', (0.03, 0.012, 0.11), (0, -0.158, -0.035), m_trim, bv=0.004, parent=root)
    if wings:
        for s_ in (-1, 1):
            wr = empty(f'{name}_wing{s_}', root, loc=(s_ * 0.13, 0.0, 0.10)); wr.rotation_euler = (0, s_ * R(-25), 0)
            for f_ in range(7):
                L_ = 0.10 + 0.03 * f_; an = R(30 + 9 * f_)
                vs = [(0, 0, 0), (s_ * L_ * math.cos(an) * 0.4, 0.015, L_ * math.sin(an) * 0.4 + 0.01), (s_ * L_ * math.cos(an), 0.03 + 0.012 * f_, L_ * math.sin(an))]
                fe = mesh(f'{name}_feather{s_}{f_}', vs, [(0, 1, 2)], m_trim if f_ % 2 else m_metal, wr, smooth_=False); fe.modifiers.new('sd', 'SOLIDIFY').thickness = 0.004
    else:
        for s_ in (-1, 1):
            hr = empty(f'{name}_hroot{s_}', root, loc=(s_ * 0.118, 0.0, 0.105))
            horn_tube(f'{name}_horn{s_}', s_, hr, m_horn)
            lathe(f'{name}_hcol{s_}', [(0.036, -0.012), (0.040, 0.0), (0.040, 0.02), (0.034, 0.03)], 20, m_trim, hr).rotation_euler = (0, s_ * R(70), 0)
    return root


def dome_r(th):
    """point on the DOME profile at polar angle th (0 = top, pi/2 = rim): returns (radius, z)"""
    best = None
    for (r0, z0), (r1, z1) in zip(DOME, DOME[1:]):
        for j in range(9):
            u = j / 8; r_ = lerp(r0, r1, u); z_ = lerp(z0, z1, u); a_ = math.atan2(r_, max(z_, 1e-5) * 1.0)
            if best is None or abs(a_ - th) < best[0]: best = (abs(a_ - th), r_ + 0.006, z_ + 0.004)
    return best[1], best[2]


# ---- the Gjermundbu helmet (Norway, 950-975): rounded iron cap of four plates, brow band, two crossing bands, a small spike, the spectacle guard.
#      nine pieces, so it can lift out of the grave and come together
GJ = [(0.0, 0.235), (0.05, 0.230), (0.09, 0.212), (0.12, 0.182), (0.142, 0.135), (0.155, 0.075), (0.160, 0.02), (0.160, 0.0)]
GJ_EY = 1.16


def gjermundbu(tag, m_iron, m_dark):
    root = empty('gj_' + tag); P = {}
    for k in range(4):
        a0 = 45 + 90 * k
        P[f'plate{k}'] = arc_shell(f'{tag}_plate{k}', GJ, a0 + 1.5, a0 + 90 - 1.5, 14, 1.0, GJ_EY, m_iron, 0.006, root)
    P['brow'] = lathe(f'{tag}_brow', [(0.158, -0.004), (0.170, -0.004), (0.171, 0.036), (0.159, 0.036)], 48, m_dark, root); P['brow'].scale = (1, GJ_EY, 1)
    for k, a_ in enumerate((0.0, math.pi / 2)):
        arc = []
        for i in range(25):
            th = -math.pi / 2 + math.pi * i / 24; rr = gj_r(abs(th)); sx = math.copysign(1, th)
            arc.append(Vector((math.cos(a_) * rr[0] * sx, math.sin(a_) * rr[0] * sx * GJ_EY, rr[1])))
        P[f'band{k}'] = tube(f'{tag}_band{k}', arc, 0.012, m_dark, root, seg=6)
        P[f'band{k}'].scale = (1, 1, 1)
        for i in range(2, 24, 3): prim('uv_sphere', f'{tag}_rv{k}_{i}', m_dark, P[f'band{k}'], loc=arc[i] * 1.03, segments=8, ring_count=5, radius=0.006)
    P['spike'] = prim('cone', f'{tag}_spike', m_dark, root, loc=(0, 0, 0.255), vertices=12, radius1=0.022, radius2=0.004, depth=0.045)
    # the spectacle guard: two eye rings, a brow bar, a nose bar, hanging below the brow band at the front
    sg = empty(f'{tag}_spect', root, loc=(0, -0.172 * GJ_EY + 0.005, -0.005)); P['spect'] = sg
    for s_ in (-1, 1):
        ring = [Vector((s_ * 0.042 + 0.034 * math.cos(2 * math.pi * i / 20), -0.004 * math.cos(2 * math.pi * i / 20) ** 2, -0.045 + 0.030 * math.sin(2 * math.pi * i / 20))) for i in range(21)]
        tube(f'{tag}_eye{s_}', ring, 0.0075, m_dark, sg, seg=6, caps=False)
    tube(f'{tag}_nosebar', [(0, -0.004, 0.0), (0, -0.012, -0.065), (0, -0.016, -0.10)], lambda u: 0.009 - 0.003 * u, m_dark, sg, seg=6)
    tube(f'{tag}_browbar', [(-0.09, 0.012, -0.012), (0, -0.003, -0.012), (0.09, 0.012, -0.012)], 0.007, m_dark, sg, seg=6)
    return root, P


def gj_r(th):
    best = None
    for (r0, z0), (r1, z1) in zip(GJ, GJ[1:]):
        for j in range(9):
            u = j / 8; r_ = lerp(r0, r1, u); z_ = lerp(z0, z1, u); a_ = math.atan2(r_, max(z_, 1e-5))
            if best is None or abs(a_ - th) < best[0]: best = (abs(a_ - th), r_ + 0.008, z_ + 0.006)
    return best[1], best[2]


# ---- the Veksø helmets (Denmark, about 900 BC): bronze cap with a crest ridge, two long S-curved horns, a beaked face with big round eyes
VK = [(0.0, 0.175), (0.06, 0.170), (0.10, 0.150), (0.13, 0.112), (0.146, 0.06), (0.150, 0.0)]


def vekso(tag, m_br, m_br2):
    root = empty('vk_' + tag)
    lathe(f'{tag}_cap', VK, 40, m_br, root)
    lathe(f'{tag}_rim', [(0.148, -0.006), (0.160, -0.006), (0.160, 0.012), (0.148, 0.012)], 40, m_br2, root)
    # crest ridge, front to back
    cr = []
    for i in range(21):
        th = -math.pi / 2 * 0.92 + math.pi * 0.92 * i / 20; r_ = 0.175 + 0.02 * math.cos(th) ** 2
        cr.append(Vector((0, math.sin(th) * r_ * 0.86, math.cos(th) * r_ * 0.98)))
    tube(f'{tag}_crest', cr, lambda u: 0.010 + 0.010 * math.sin(math.pi * u), m_br2, root, seg=8)
    # the face: a beak (nose) and two big eyes as raised rings with bosses
    face = empty(f'{tag}_face', root, loc=(0, -0.148, 0.07)); face.rotation_euler = (R(-15), 0, 0)
    tube(f'{tag}_beak', [(0, 0.0, 0.03), (0, -0.015, -0.01), (0, -0.006, -0.05)], lambda u: 0.012 - 0.008 * u, m_br2, face, seg=8)
    for s_ in (-1, 1):
        ring = [Vector((s_ * 0.042 + 0.024 * math.cos(2 * math.pi * i / 20), -0.002, 0.008 + 0.024 * math.sin(2 * math.pi * i / 20))) for i in range(21)]
        tube(f'{tag}_eyer{s_}', ring, 0.005, m_br2, face, seg=6, caps=False)
        prim('uv_sphere', f'{tag}_eyeb{s_}', m_br2, face, loc=(s_ * 0.042, -0.006, 0.008), segments=12, ring_count=8, radius=0.012)
    # the horns: out of the sides, up, then out and forward in a long S (the lyre shape), with little knob tips
    for s_ in (-1, 1):
        pts = []
        for i in range(24):
            u = i / 23
            x = s_ * (0.13 + 0.10 * u + 0.12 * math.sin(math.pi * u * 0.9) * 0.6)
            y = -0.10 * math.sin(math.pi * u) * 0.5 - 0.06 * u
            z = 0.06 + 0.46 * u - 0.06 * math.sin(math.pi * u * 1.6) * u
            pts.append(Vector((x, y, z)))
        tube(f'{tag}_horn{s_}', pts, lambda u: 0.038 - 0.022 * u, m_br, root, seg=14)
        prim('uv_sphere', f'{tag}_knob{s_}', m_br2, root, loc=pts[-1] + Vector((0, 0, 0.01)), segments=12, ring_count=8, radius=0.022)
        for j in (4, 9, 14): tube(f'{tag}_hring{s_}{j}', [pts[j] + Vector((0.032 * math.cos(2 * math.pi * i / 12), 0.018 * math.sin(2 * math.pi * i / 12), 0)) for i in range(13)], 0.004, m_br2, root, seg=5, caps=False)
    return root

# ================================================================ set: a museum hall (x -4..24) with five exhibits, a window out to a Danish bog (x 24..70)
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
for xs, tg in ((-1.6, (-0.3, 1.8, 1.4)), (1.6, (0.2, 1.8, 1.4)), (6.6, (7.5, 2.6, 0.6)), (8.6, (7.5, 2.4, 1.0)), (11.2, (11.1, 2.6, 1.3)),
               (15.4, (16.3, 2.4, 1.6)), (17.2, (16.3, 2.4, 1.6)), (21.4, (21.4, 5.0, 1.6))):
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


# ================================================================ exhibit 1: the longship bow in a storm (x = 0), a diorama with a painted sky all round
SHIP_Y = 1.7; WATER_Z = 0.55
DIO = empty('dio')
box('dstage', (4.8, 3.9, 0.3), (0, 1.85, 0.15), M_WOOD, bv=0.02, parent=DIO)
box('dlintel', (5.3, 0.5, 0.55), (0, -0.05, 4.4), M_WOOD, bv=0.02, parent=DIO)
for s_ in (-1, 1): box(f'dpil{s_}', (0.45, 0.5, 4.7), (s_ * 2.5, -0.05, 2.35), M_WOOD, bv=0.02, parent=DIO)
# the sky: a curved painted backdrop (half cylinder behind, flat at the sides), stormy clouds, lightning flashes light it up
M_SKY = bpy.data.materials.new('stormsky'); M_SKY.use_nodes = True; nt_ = M_SKY.node_tree; nt_.nodes.remove(nt_.nodes['Principled BSDF'])
e_ = nt_.nodes.new('ShaderNodeEmission'); co_ = coord(nt_, 'Object'); sz_ = sepz(nt_, co_)
cl_ = tnoise(nt_, co_, 0.9, 10.0, 0.6); cl2_ = tnoise(nt_, co_, 3.0, 6.0, 0.2)
hz_ = ramp_v(nt_, sz_.outputs['Z'], 0.4, 4.0)
c_ = ramp(nt_, math_(nt_, 'ADD', math_(nt_, 'MULTIPLY', cl_, 0.75), math_(nt_, 'MULTIPLY', cl2_, 0.25)), [(0.30, (0.012, 0.016, 0.026)), (0.5, (0.05, 0.06, 0.08)), (0.62, (0.12, 0.13, 0.15)), (0.75, (0.20, 0.21, 0.24))])
c_ = mixc(nt_, math_(nt_, 'MULTIPLY', math_(nt_, 'SUBTRACT', 1.0, hz_), 0.5), c_, (0.10, 0.13, 0.16))
nt_.links.new(c_, e_.inputs['Color'])
nt_.links.new(math_(nt_, 'ADD', 1.0, math_(nt_, 'MULTIPLY', objattr(nt_, 'flash'), 3.5)), e_.inputs['Strength'])
nt_.links.new(e_.outputs[0], nt_.nodes['Material Output'].inputs['Surface'])
RC, RCY = 2.38, 1.65; vs = []; fs = []; NS = 40
path = [Vector((-RC, -0.1)), Vector((-RC, RCY))] + [Vector((-RC * math.cos(math.pi * k / NS), RCY + RC * math.sin(math.pi * k / NS))) for k in range(1, NS)] + [Vector((RC, RCY)), Vector((RC, -0.1))]
for i, p in enumerate(path): vs += [(p.x, p.y, 0.3), (p.x, p.y, 4.3)]
for i in range(len(path) - 1): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
CYC = mesh('cyclo', vs, fs, M_SKY, DIO, smooth_=True); CYC['flash'] = 0.0
CYT = mesh('cyctop', [(p.x, p.y, 4.29) for p in path], [tuple(range(len(path)))], M_SKY, DIO, smooth_=False); CYT['flash'] = 0.0
# the sea: a grid that moves every frame (frame() sets the heights)
M_SEA = mat('sea', (0.02, 0.07, 0.08), 0.06, coat=0.3); nt_ = M_SEA.node_tree
foam_ = math_(nt_, 'MAXIMUM', ramp_v(nt_, tnoise(nt_, coord(nt_, 'Object'), 4.0, 8.0, 1.2), 0.62, 0.78),
              math_(nt_, 'MULTIPLY', ramp_v(nt_, sepz(nt_, coord(nt_, 'Object')).outputs['Z'], WATER_Z + 0.85, WATER_Z + 1.3), ramp_v(nt_, tnoise(nt_, coord(nt_, 'Object'), 6.0, 8.0, 2.0), 0.45, 0.62)))
nt_.links.new(mixc(nt_, math_(nt_, 'MULTIPLY', foam_, 0.9), mixc(nt_, ramp_v(nt_, sepz(nt_, coord(nt_, 'Object')).outputs['Z'], WATER_Z + 0.2, WATER_Z + 1.0), (0.02, 0.07, 0.08), (0.06, 0.20, 0.19)), (0.62, 0.68, 0.70)), nt_.nodes['Principled BSDF'].inputs['Base Color'])
nt_.links.new(math_(nt_, 'ADD', 0.05, math_(nt_, 'MULTIPLY', foam_, 0.6)), nt_.nodes['Principled BSDF'].inputs['Roughness'])
SNX, SNY = 72, 60; vs = []; fs = []
for j in range(SNY):
    for i in range(SNX): vs.append((-RC + 2 * RC * i / (SNX - 1), -0.05 + (RCY + RC + 0.05) * j / (SNY - 1), WATER_Z))
for j in range(SNY - 1):
    for i in range(SNX - 1): a_ = j * SNX + i; fs.append((a_, a_ + 1, a_ + SNX + 1, a_ + SNX))
SEA = mesh('sea', vs, fs, M_SEA, DIO); SEA_XY = np.array([(v[0], v[1]) for v in vs])
box('seabase', (4.76, 3.9, 0.3), (0, 1.85, 0.42), mat('deep', (0.003, 0.012, 0.014), 0.5), parent=DIO)


def sea_h(x, y, t):
    """sea height (numpy x, y): long swells across, chop, and the big crest that breaks on the far side of the bow at t = 0"""
    h = 0.07 * np.sin(1.7 * x + 0.9 * y - 2.1 * t) + 0.045 * np.sin(2.9 * x - 1.6 * y - 3.3 * t + 1.0) + 0.02 * np.sin(7.0 * x + 5.0 * y - 6.0 * t)
    cy = max(2.78, 3.55 - 2.6 * (t + 0.25))                                        # the crest rolls in toward the far rail
    dy = y - cy; prof = np.where(dy < 0, np.exp(-(dy / 0.18) ** 2), np.exp(-(dy / 0.45) ** 2))      # steep front, long back
    amp = 1.45 * (1 - math.exp(-max(0.0, t + 0.45) * 5.0)) * math.exp(-max(0.0, t - 0.2) * 2.6)
    crest = amp * prof * (0.78 + 0.22 * np.sin(3.1 * x + 1.3)) * np.exp(-((x + 0.35) / 2.2) ** 2) * np.clip((y - 2.66) / 0.14, 0, 1)
    return h + crest


# the bow section of the ship: lapstrake planks, ribs, deck, gunwale rail, the stem rising into a dragon's neck and head
M_HULL = [noisy(mat(f'hull{k}', c, 0.6, coat=0.1), 9.0, 0.35) for k, c in enumerate(((0.14, 0.085, 0.045), (0.11, 0.065, 0.035), (0.16, 0.10, 0.055)))]
M_DECK = brick_mat('deck', (0.30, 0.21, 0.12), (0.26, 0.18, 0.10), (0.08, 0.05, 0.03), 1.0, rough=0.7, plane='xy', bump=0.3, row=0.14, w=2.2, mortar_w=0.01, seed=5.0)
M_PAINTR = noisy(mat('paintred', (0.45, 0.05, 0.03), 0.55), 15.0, 0.3); M_PAINTY = noisy(mat('painty', (0.75, 0.52, 0.10), 0.55), 15.0, 0.3)
SX0, SX1 = -1.65, 2.05
def hx(u): return SX0 + (SX1 - SX0) * u
def hw(u): return 0.95 * math.sin(min(1.0, u / 0.6) * math.pi / 2) ** 0.9
def hzk(u): return 0.32 + 0.95 * max(0.0, 1 - u / 0.3) ** 2
def hzg(u): return 1.38 + 1.5 * max(0.0, 1 - u / 0.32) ** 2
def hull_pt(u, v, s_, out=0.0):
    w_ = hw(u); zk, zg = hzk(u), hzg(u); sv = math.sin(v * math.pi / 2)
    return Vector((hx(u), SHIP_Y + s_ * (w_ * sv ** 0.6 + out), zk + (zg - zk) * v ** 1.3))
SHIP = empty('ship', DIO)
NU, K = 48, 9
for s_ in (-1, 1):
    for k in range(K):
        vs = []; fs = []
        for i in range(NU + 1):
            u = 0.004 + 0.996 * i / NU
            for j in range(3):
                v = (k + j / 2 * 1.08) / K; v = min(v, 1.0); vs.append(hull_pt(u, v, s_, 0.014 * (1 - j / 2)))
        for i in range(NU):
            for j in range(2): a_ = i * 3 + j; fs.append((a_, a_ + 3, a_ + 4, a_ + 1) if s_ > 0 else (a_, a_ + 1, a_ + 4, a_ + 3))
        st = mesh(f'strake{s_}{k}', vs, fs, M_HULL[k % 3], SHIP); sd = st.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.022; sd.offset = 0.0
    tube(f'rail{s_}', [hull_pt(0.004 + 0.996 * i / 40, 1.0, s_, 0.01) + Vector((0, 0, 0.01)) for i in range(41)], 0.034, M_WOOD, SHIP, seg=10)
for i in range(1, 9):                                           # ribs inside the hull
    u = 0.12 + 0.11 * i
    if u > 0.99: break
    tube(f'rib{i}', [hull_pt(u, v, s_, -0.03) for s_, v in [(-1, 1.0 - k / 10) for k in range(10)] + [(1, k / 10) for k in range(11)]], 0.028, M_WOOD, SHIP, seg=8)
DECK_Z = 0.82
def deck_w(u):
    zk, zg = hzk(u), hzg(u)
    if DECK_Z <= zk: return 0.0
    v = ((DECK_Z - zk) / (zg - zk)) ** (1 / 1.3); return hw(u) * math.sin(min(1.0, v) * math.pi / 2) ** 0.6 - 0.02
vs = []; fs = []
us = [0.06 + 0.94 * i / 40 for i in range(41)]
for u in us: w_ = deck_w(u); vs += [(hx(u), SHIP_Y - w_, DECK_Z), (hx(u), SHIP_Y + w_, DECK_Z)]
for i in range(40): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
dk = mesh('deck', vs, fs, M_DECK, SHIP, smooth_=False); dk.modifiers.new('sd', 'SOLIDIFY').thickness = 0.03
for i in range(1, 6): box(f'thwart{i}', (0.09, 2 * deck_w(0.2 + 0.15 * i) - 0.05, 0.05), (hx(0.2 + 0.15 * i), SHIP_Y, DECK_Z + 0.32), M_WOOD, bv=0.01, parent=SHIP)
# the stem: up the bow, then the neck curls up and forward into the head
stem = [hull_pt(0.30 - 0.3 * i / 10, 0.0, 1) for i in range(11)] + [hull_pt(0.0, v, 1) for v in (0.25, 0.5, 0.75, 1.0)]
top = stem[-1]
neck = [top + Vector((-0.05 - 0.12 * u - 0.10 * u * u, 0, 0.25 * u + 0.35 * math.sin(u * math.pi * 0.7))) for u in [i / 8 for i in range(1, 9)]]
tube('stem', stem + neck, lambda u: 0.07 - 0.025 * u, M_HULL[1], SHIP, seg=12)
HEAD_P = neck[-1]
HEAD = empty('dhead', SHIP, loc=HEAD_P)
tube('dskull', [(0.05, 0, 0.0), (-0.08, 0, 0.04), (-0.22, 0, 0.03), (-0.36, 0, 0.0)], lambda u: 0.09 - 0.055 * u, M_HULL[2], HEAD, seg=14)
tube('djaw', [(-0.04, 0, -0.04), (-0.18, 0, -0.08), (-0.33, 0, -0.10)], lambda u: 0.045 - 0.02 * u, M_HULL[2], HEAD, seg=10)
for k in range(6):
    for s_ in (-1, 1):
        prim('cone', f'dtooth{k}{s_}', M_WHITE, HEAD, loc=(-0.12 - 0.04 * k, s_ * 0.03, -0.035), rot=(R(180), 0, 0), vertices=6, radius1=0.008, radius2=0.0, depth=0.03)
for s_ in (-1, 1):
    prim('uv_sphere', f'deye{s_}', mat(f'deye{s_}', (0.9, 0.6, 0.05), 0.2, emit=(1.0, 0.55, 0.05), estr=1.5), HEAD, loc=(-0.10, s_ * 0.065, 0.075), segments=12, ring_count=8, radius=0.022)
    tube(f'dfrill{s_}', [(0.0, s_ * 0.05, 0.08), (0.08, s_ * 0.09, 0.16), (0.2, s_ * 0.11, 0.18), (0.26, s_ * 0.09, 0.10)], lambda u: 0.018 - 0.012 * u, M_PAINTR, HEAD, seg=6)
tube('dcurl', [(0.06 + 0.1 * math.cos(a_), 0, 0.12 + 0.1 * math.sin(a_) * (1 - a_ / 12)) for a_ in [i * 0.5 for i in range(16)]], 0.014, M_PAINTY, HEAD, seg=6)
for i, z_ in enumerate((0.3, 0.6)):
    p_ = neck[int(z_ * 7)]; tube(f'dband{i}', [p_ + Vector((0.075 * math.cos(2 * math.pi * k / 16), 0.075 * math.sin(2 * math.pi * k / 16), 0)) for k in range(17)], 0.014, M_PAINTY, SHIP, seg=6, caps=False)
# shields along the rails (painted halves, iron boss)
def shield_mat(name, c1, c2):
    m = mat(name, c1, 0.6); nt = m.node_tree; sx = sepz(nt, coord(nt, 'Object'))
    st_ = math_(nt, 'GREATER_THAN', sx.outputs['X'], 0.0); nt.links.new(mixc(nt, st_, c1, c2), nt.nodes['Principled BSDF'].inputs['Base Color']); return noisy(m, 12.0, 0.25)
SHM = [shield_mat('shA', (0.50, 0.06, 0.04), (0.80, 0.62, 0.15)), shield_mat('shB', (0.05, 0.05, 0.05), (0.78, 0.76, 0.70)), shield_mat('shC', (0.08, 0.20, 0.42), (0.78, 0.76, 0.70))]
for s_ in (-1, 1):
    for k in range(9):
        u = 0.36 + 0.075 * k
        if u > 0.99: break
        p_ = hull_pt(u, 1.0, s_, 0.04) + Vector((0, 0, -0.14))
        sh = prim('cylinder', f'shield{s_}{k}', SHM[(k + (s_ > 0)) % 3], SHIP, loc=p_, rot=(R(90), 0, R(15) * s_), vertices=32, radius=0.2, depth=0.02)
        bs = prim('uv_sphere', f'boss{s_}{k}', M_IRDK, SHIP, loc=p_ + Vector((0, s_ * 0.015, 0)), segments=12, ring_count=6, radius=0.045)
# the mast and a striped sail, the yard across
MAST_X = hx(0.74)
tube('mast', [(MAST_X, SHIP_Y, DECK_Z), (MAST_X, SHIP_Y, 4.05)], 0.06, M_WOOD, SHIP, seg=12)
tube('yard', [(MAST_X - 0.06, SHIP_Y - 1.35, 3.55), (MAST_X - 0.06, SHIP_Y + 1.35, 3.55)], 0.035, M_WOOD, SHIP, seg=10)
M_SAIL = mat('sail', (0.7, 0.66, 0.55), 0.85, sheen=0.4); nt_ = M_SAIL.node_tree; sy_ = sepz(nt_, coord(nt_, 'Object'))
stp = math_(nt_, 'GREATER_THAN', math_(nt_, 'FRACT', math_(nt_, 'MULTIPLY', sy_.outputs['Y'], 2.2)), 0.5)
nt_.links.new(mixc(nt_, stp, (0.72, 0.66, 0.52), (0.48, 0.05, 0.03)), nt_.nodes['Principled BSDF'].inputs['Base Color'])
SAIL_N = (14, 10); vs = []; fs = []
for j in range(SAIL_N[1] + 1):
    for i in range(SAIL_N[0] + 1): vs.append((MAST_X - 0.1, SHIP_Y - 1.3 + 2.6 * i / SAIL_N[0], 3.52 - 1.45 * j / SAIL_N[1]))
for j in range(SAIL_N[1]):
    for i in range(SAIL_N[0]): a_ = j * (SAIL_N[0] + 1) + i; fs.append((a_, a_ + 1, a_ + SAIL_N[0] + 2, a_ + SAIL_N[0] + 1))
SAIL = mesh('sail', vs, fs, M_SAIL, SHIP); SAIL_V0 = np.array(vs); SAIL.modifiers.new('sd', 'SOLIDIFY').thickness = 0.008
for s_ in (-1, 1): tube(f'stay{s_}', [(MAST_X, SHIP_Y, 3.9), hull_pt(0.95, 1.0, s_)], 0.008, M_STRAW, SHIP, seg=5)
tube('forestay', [(MAST_X, SHIP_Y, 3.95), hull_pt(0.05, 1.0, 1)], 0.008, M_STRAW, SHIP, seg=5)
# oars out of the near side, down into the sea
for k in range(4):
    u = 0.5 + 0.12 * k; p0 = hull_pt(u, 0.88, -1)
    tube(f'oar{k}', [p0 + Vector((0.2, 0.35, 0.25)), p0 + Vector((-0.25, -1.05, -0.62))], 0.022, M_WOODRAW, SHIP, seg=8)
# on deck: a sea chest and the horned helmet on it, coiled rope, a lantern on a post
CHEST_P = Vector((hx(0.36), SHIP_Y - 0.05, DECK_Z))
box('chest', (0.62, 0.40, 0.36), CHEST_P + Vector((0, 0, 0.18)), M_WOOD, bv=0.02, parent=SHIP)
box('chestlid', (0.64, 0.42, 0.05), CHEST_P + Vector((0, 0, 0.385)), M_WOOD, bv=0.015, parent=SHIP)
for xs_ in (-0.22, 0.22): box(f'chband{xs_}', (0.04, 0.43, 0.42), CHEST_P + Vector((xs_, 0, 0.2)), M_IRDK, parent=SHIP)
M_STEEL = steel_mat('steel', 1.0); M_HORN = horn_mat('horn')
HELM1 = horned_helmet('helm1', SHIP, M_STEEL, M_BRASS, M_HORN); HELM1.location = CHEST_P + Vector((0.0, 0.0, 0.42)); HELM1.rotation_euler = (0, 0, R(18))
for k in range(3):
    tube(f'rope{k}', [CHEST_P + Vector((0.55 + (0.16 - 0.03 * k) * math.cos(a_), 0.15 + (0.16 - 0.03 * k) * math.sin(a_), 0.03 + 0.025 * k)) for a_ in [i * 0.4 for i in range(17)]], 0.018, M_STRAW, SHIP, seg=6, caps=False)
LPOST = hull_pt(0.22, 1.0, -1) + Vector((0, 0.08, 0))
tube('lpost', [LPOST, LPOST + Vector((0, 0, 0.75))], 0.025, M_WOOD, SHIP, seg=8)
LANT = empty('lantern', SHIP, loc=LPOST + Vector((0.0, 0.18, 0.66)))
tube('lhook', [LPOST + Vector((0, 0, 0.74)), LPOST + Vector((0, 0.18, 0.74)), LPOST + Vector((0, 0.18, 0.69))], 0.008, M_IRDK, SHIP, seg=5)
lathe('lbody', [(0.0, -0.16), (0.07, -0.16), (0.07, -0.02), (0.04, 0.0), (0.0, 0.0)], 12, M_IRDK, LANT)
lathe('lglass', [(0.06, -0.15), (0.065, -0.15), (0.065, -0.03), (0.06, -0.03)], 12, emis('lglow', (1.0, 0.6, 0.25), 6.0), LANT)
LLIGHT = light_at('llight', 'POINT', LANT.location + Vector((0, 0, -0.1)), (0, 0, 0), 30, (1.0, 0.6, 0.28), 0.04); LLIGHT.parent = SHIP
STORM_KEY = light_at('stormkey', 'AREA', (-1.2, 3.4, 4.0), (-0.3, 1.7, 1.0), 160, (0.55, 0.68, 1.0), 1.5)
STORM_FILL = light_at('stormfill', 'AREA', (1.5, -0.6, 2.6), (-0.3, 1.7, 1.2), 25, (0.5, 0.6, 0.8), 2.0)
BOLT = light_at('bolt', 'AREA', (0.0, 3.0, 4.15), (0.0, 1.5, 0.5), 0.0, (0.75, 0.82, 1.0), 2.5)
# museum front: brass posts, velvet rope, a placard
for k, xp in enumerate((-2.0, 0.0, 2.0)):
    lathe(f'post{k}', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.04, 0.06), (0.025, 0.08), (0.025, 0.88), (0.045, 0.92), (0.05, 0.96), (0.0, 1.0)], 24, M_BRASS, HALL, loc=(xp, -0.75, 0))
for k in range(2):
    x0, x1 = -2.0 + 2 * k, 2.0 * k
    tube(f'vrope{k}', [(lerp(x0, x1, u), -0.75, 0.9 - 0.22 * math.sin(math.pi * u)) for u in [i / 16 for i in range(17)]], 0.022, M_VELVET, HALL, seg=10)
placard('plaq1', (1.2, -1.2, 0), -12, 'VIKING HELMET\nHORNED?')

# ================================================================ exhibit 2: the grave mound at Gjermundbu, cut open (x = 7.5)
GX, GCY = 7.5, 3.7; GRX, GRY, GH, GYC = 1.9, 1.5, 1.05, 3.0; PLAT_Z = 0.15
box('gplat', (4.6, 3.6, PLAT_Z), (GX, 3.25, PLAT_Z / 2), noisy(mat('gdirt', (0.20, 0.14, 0.08), 0.95), 6.0, 0.35), parent=HALL)
def mound_h(x, y):
    q = ((x - GX) / GRX) ** 2 + ((y - GCY) / GRY) ** 2
    return GH * max(0.0, 1 - q) ** 0.75 if q < 1 else 0.0
M_GRASS = noisy(mat('grass', (0.14, 0.20, 0.06), 0.8, sheen=0.3), 9.0, 0.35); M_GRASS2 = noisy(mat('grass2', (0.20, 0.26, 0.08), 0.8), 20.0, 0.3)
M_SOIL = mat('soil', (0.18, 0.11, 0.06), 0.95); nt_ = M_SOIL.node_tree; zz_ = sepz(nt_, coord(nt_, 'Object'))
band_ = math_(nt_, 'SINE', math_(nt_, 'MULTIPLY', math_(nt_, 'ADD', zz_.outputs['Z'], math_(nt_, 'MULTIPLY', tnoise(nt_, coord(nt_, 'Object'), 3.0, 4.0), 0.15)), 28.0))
c_ = ramp(nt_, math_(nt_, 'ADD', math_(nt_, 'MULTIPLY', band_, 0.3), math_(nt_, 'MULTIPLY', tnoise(nt_, coord(nt_, 'Object'), 25.0, 6.0), 0.6)), [(0.1, (0.07, 0.045, 0.025)), (0.45, (0.20, 0.12, 0.06)), (0.7, (0.30, 0.20, 0.11)), (0.95, (0.38, 0.30, 0.20))])
nt_.links.new(c_, nt_.nodes['Principled BSDF'].inputs['Base Color'])
bp_ = nt_.nodes.new('ShaderNodeBump'); bp_.inputs['Strength'].default_value = 0.8; nt_.links.new(tnoise(nt_, coord(nt_, 'Object'), 30.0, 8.0), bp_.inputs['Height']); nt_.links.new(bp_.outputs['Normal'], nt_.nodes['Principled BSDF'].inputs['Normal'])
NXM, NYM = 44, 30; vs = []; fs = []
for j in range(NYM + 1):
    for i in range(NXM + 1):
        x_ = GX - GRX + 2 * GRX * i / NXM; y_ = GYC + (GCY + GRY - GYC) * j / NYM; vs.append((x_, y_, PLAT_Z + mound_h(x_, y_) - 0.01))
for j in range(NYM):
    for i in range(NXM): a_ = j * (NXM + 1) + i; fs.append((a_, a_ + 1, a_ + NXM + 2, a_ + NXM + 1))
mesh('mound', vs, fs, M_GRASS, HALL)
vs = []; fs = []
for i in range(NXM + 1):
    x_ = GX - GRX + 2 * GRX * i / NXM; vs += [(x_, GYC, PLAT_Z - 0.01), (x_, GYC, PLAT_Z + mound_h(x_, GYC))]
for i in range(NXM): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
mesh('moundcut', vs, fs, M_SOIL, HALL, smooth_=False)
for k in range(420):                                             # grass tufts on top
    x_ = G.uniform(GX - GRX, GX + GRX); y_ = G.uniform(GYC + 0.03, GCY + GRY)
    h_ = mound_h(x_, y_)
    if h_ < 0.04: continue
    p_ = Vector((x_, y_, PLAT_Z + h_ - 0.01)); d_ = Vector((G.uniform(-0.3, 0.3), G.uniform(-0.3, 0.3), 1)).normalized() * G.uniform(0.07, 0.16)
    tube(f'gt{k}', [p_, p_ + d_ * 0.6, p_ + d_ + Vector((d_.x, d_.y, 0)) * 0.4], lambda u: 0.006 * (1 - u) + 0.001, M_GRASS2 if k % 3 else M_GRASS, HALL, seg=3, caps=False)
# the grave in the trench: stone outline, a sword, an axe, a shield boss, spurs, and the helmet in nine pieces
M_STONEG = noisy(mat('gstone', (0.17, 0.155, 0.13), 0.9), 8.0, 0.4)
for k in range(26):
    a_ = 2 * math.pi * k / 26; p_ = Vector((GX + 0.95 * math.cos(a_), 2.55 + 0.42 * math.sin(a_), PLAT_Z + 0.02))
    st_ = prim('ico_sphere', f'gst{k}', M_STONEG, HALL, loc=p_, subdivisions=2, radius=1.0, scale=(G.uniform(0.05, 0.085), G.uniform(0.04, 0.07), G.uniform(0.03, 0.05)))
    st_.rotation_euler = (0, 0, G.uniform(0, 3))
GFLOOR = box('gfloor', (2.0, 0.9, 0.02), (GX, 2.55, PLAT_Z + 0.005), M_SOIL, parent=HALL)
M_RUST = iron_mat('rust', 0.75, seed=4.0, rust_col=(0.11, 0.05, 0.022))
tube('gsword', [(GX + 0.55, 2.42, PLAT_Z + 0.035), (GX - 0.35, 2.5, PLAT_Z + 0.035)], lambda u: 0.022 - 0.012 * u, M_RUST, HALL, seg=6)
box('gguard', (0.03, 0.13, 0.025), (GX + 0.5, 2.425, PLAT_Z + 0.04), M_RUST, parent=HALL)
box('gaxe', (0.16, 0.03, 0.12), (GX - 0.62, 2.7, PLAT_Z + 0.025), M_RUST, bv=0.01, rot=(R(90), 0, R(20)), parent=HALL)
prim('uv_sphere', 'gboss', M_RUST, HALL, loc=(GX + 0.7, 2.7, PLAT_Z + 0.01), segments=16, ring_count=8, radius=0.075, scale=(1, 1, 0.6))
for k in range(30): prim('ico_sphere', f'gmail{k}', M_RUST, HALL, loc=(GX - 0.25 + 0.06 * (k % 6), 2.7 + 0.05 * (k // 6) - 0.1, PLAT_Z + 0.02), subdivisions=1, radius=0.025, scale=(1, 1, 0.3))
for k in range(9):                                               # loose soil heaps either side of the trench
    s_ = -1 if k < 5 else 1; p_ = Vector((GX + s_ * G.uniform(1.25, 1.75), G.uniform(2.0, 2.9), PLAT_Z))
    prim('ico_sphere', f'heap{k}', M_SOIL, HALL, loc=p_, subdivisions=3, radius=1.0, scale=(G.uniform(0.2, 0.32), G.uniform(0.18, 0.28), G.uniform(0.1, 0.18)))
SHOVEL = empty('shovel', HALL); SHOVEL_P = Vector((GX - 1.45, 2.35, PLAT_Z + 0.1))
tube('shaft', [(0, 0, 0.18), (0, 0, 1.15)], 0.02, M_WOODRAW, SHOVEL, seg=8)
tube('shgrip', [(-0.08, 0, 1.15), (0.08, 0, 1.15)], 0.018, M_WOODRAW, SHOVEL, seg=8)
sb = box('shblade', (0.22, 0.02, 0.26), (0, 0, 0.06), M_RUST, bv=0.01, parent=SHOVEL)
CLODS = [prim('ico_sphere', f'clod{k}', M_SOIL, None, loc=(0, 0, -50), subdivisions=1, radius=G.uniform(0.02, 0.045)) for k in range(26)]
CLOD_V = [Vector((G.uniform(-1.6, -0.6), G.uniform(-0.4, 0.4), G.uniform(1.8, 2.8))) for k in range(26)]
# the house he was building: a bare timber frame at the back corner
for k, (xa, ya) in enumerate(((GX - 2.05, 4.3), (GX - 1.25, 4.3), (GX - 2.05, 4.95), (GX - 1.25, 4.95))): box(f'hpost{k}', (0.08, 0.08, 1.3), (xa, ya, PLAT_Z + 0.65), M_WOODRAW, parent=HALL)
for k, (a_, b_) in enumerate((((GX - 1.65, 4.3), (0.9, 0.08)), ((GX - 1.65, 4.95), (0.9, 0.08)))): box(f'hbeam{k}', (b_[0], b_[1], 0.08), (a_[0], a_[1], PLAT_Z + 1.3), M_WOODRAW, parent=HALL)
for k in range(2): box(f'hside{k}', (0.08, 0.73, 0.08), (GX - 2.05 + 0.8 * k, 4.62, PLAT_Z + 1.3), M_WOODRAW, parent=HALL)
# the display stand where the helmet comes together
STAND_P = Vector((GX, 2.05, PLAT_Z))
lathe('gstand', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.05), (0.05, 0.08), (0.045, 0.85), (0.08, 0.9), (0.09, 0.93), (0.0, 0.93)], 24, M_WOOD, HALL, loc=STAND_P)
GJ_TOP = STAND_P + Vector((0, 0, 0.93 + 0.012))
# (no wall banner: the label says it)
placard('plaq2', (GX + 1.55, 1.0, 0), -14, 'GJERMUNDBU\nHELMET, 950s')

# ================================================================ exhibit 3: why horns don't work - a test head, a horned helmet, a swinging sword (x = 11.2)
DX = 11.2
box('dplat', (2.4, 2.4, PLAT_Z), (DX, 2.9, PLAT_Z / 2), M_WOOD, bv=0.01, parent=HALL)
M_DUMMY = noisy(mat('dummy', (0.42, 0.40, 0.37), 0.7, sheen=0.3), 6.0, 0.15)
HEAD_C = Vector((DX - 0.2, 2.7, 1.42))
lathe('tbase', [(0.0, 0.0), (0.22, 0.0), (0.22, 0.04), (0.04, 0.07), (0.035, 1.12), (0.0, 1.12)], 24, M_BLACK, HALL, loc=(HEAD_C.x, HEAD_C.y, PLAT_Z))
lathe('tneck', [(0.0, 0.0), (0.055, 0.0), (0.05, 0.14), (0.0, 0.14)], 20, M_DUMMY, HALL, loc=(HEAD_C.x, HEAD_C.y, 1.23))
hd = prim('uv_sphere', 'thead', M_DUMMY, HALL, loc=HEAD_C, segments=32, ring_count=16, radius=0.1, scale=(0.95, 1.05, 1.22))
HELM2 = horned_helmet('helm2', None, M_STEEL, M_BRASS, M_HORN)
HELM2_P0 = HEAD_C + Vector((0, 0, 0.05)); HELM2.location = HELM2_P0; HELM2.rotation_mode = 'QUATERNION'
PIV = Vector((DX + 0.62, 2.72, 2.35))
SWORD = empty('sword', HALL, loc=PIV)                       # the arm swings round local y; the blade points along local -z
lathe('pivpost', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.04), (0.05, 0.07), (0.045, PIV.z - PLAT_Z), (0.0, PIV.z - PLAT_Z)], 20, M_IRDK, HALL, loc=(PIV.x + 0.12, PIV.y + 0.12, PLAT_Z))
prim('cylinder', 'pivhub', M_BRASS, HALL, loc=PIV + Vector((0.0, 0.06, 0)), rot=(R(90), 0, 0), vertices=20, radius=0.045, depth=0.08)
box('sarm', (0.04, 0.03, 0.18), (0, 0, -0.09), M_IRDK, parent=SWORD)
box('sgrip', (0.035, 0.035, 0.16), (0, 0, -0.26), M_WOOD, parent=SWORD)
box('sguard', (0.16, 0.035, 0.03), (0, 0, -0.35), M_BRASS, bv=0.005, parent=SWORD)
bl = mesh('sblade', [(-0.028, 0, -0.36), (0.028, 0, -0.36), (0.022, 0, -1.02), (0.0, 0, -1.08), (-0.022, 0, -1.02)], [(0, 1, 2, 3, 4)], M_STEEL, SWORD, smooth_=False)
bl.modifiers.new('sd', 'SOLIDIFY').thickness = 0.008
placard('plaq3', (DX + 1.0, 1.25, 0), -10, 'HORNS IN\nA FIGHT?')

# ================================================================ exhibit 4: the opera stage, Bayreuth 1876 (x = 16.3)
OX = 16.3; OZ = 0.9; OYF = 1.45
box('ostage', (4.0, 2.8, OZ), (OX, OYF + 1.4, OZ / 2), M_WOOD, bv=0.02, parent=HALL)
box('ofloor', (3.6, 2.6, 0.02), (OX, OYF + 1.35, OZ + 0.01), brick_mat('ofl', (0.20, 0.13, 0.07), (0.17, 0.11, 0.06), (0.05, 0.03, 0.02), 1.0, rough=0.5, plane='xy', bump=0.2, row=0.12, w=3.0, mortar_w=0.008, seed=8.0), parent=HALL)
M_PROS = noisy(mat('pros', (0.30, 0.04, 0.05), 0.6), 10.0, 0.2)
for s_ in (-1, 1):
    box(f'opil{s_}', (0.32, 0.3, 3.15), (OX + s_ * 1.92, OYF - 0.05, OZ + 1.575), M_PROS, bv=0.02, parent=HALL)
    box(f'opilg{s_}', (0.38, 0.06, 3.15), (OX + s_ * 1.92, OYF - 0.21, OZ + 1.575), M_GILT, bv=0.01, parent=HALL)
box('ohead', (4.2, 0.3, 0.8), (OX, OYF - 0.05, OZ + 3.55), M_PROS, bv=0.02, parent=HALL)
box('oheadg', (4.26, 0.06, 0.12), (OX, OYF - 0.21, OZ + 3.2), M_GILT, bv=0.01, parent=HALL)
text3d('ohtxt', 'BAYREUTH 1876', 0.24, (OX, OYF - 0.24, OZ + 3.55), (R(90), 0, 0), M_GILT, HALL, extrude=0.01)
# curtains: pleated velvet, two halves that draw apart to the sides (frame() squeezes them)
CURT = []
for s_ in (-1, 1):
    piv_ = empty(f'curt{s_}', HALL, loc=(OX + s_ * 1.78, OYF + 0.05, OZ)); vs = []; fs = []; nx_, nz_ = 40, 12
    for j in range(nz_ + 1):
        for i in range(nx_ + 1):
            x_ = -s_ * 1.78 * i / nx_; vs.append((x_, 0.05 * math.sin(i * math.pi / 2.5) * (0.6 + 0.4 * j / nz_), 3.12 * j / nz_))
    for j in range(nz_):
        for i in range(nx_): a_ = j * (nx_ + 1) + i; fs.append((a_, a_ + 1, a_ + nx_ + 2, a_ + nx_ + 1))
    c_ = mesh(f'curtm{s_}', vs, fs, M_VELVET, piv_); c_.modifiers.new('sd', 'SOLIDIFY').thickness = 0.015; CURT.append(piv_)
vs = []; fs = []
for i in range(81):
    x_ = OX - 2.0 + 4.0 * i / 80; y_ = OYF + 0.0 + 0.04 * math.sin(i * math.pi / 2.0); vs += [(x_, y_, OZ + 2.75 + 0.06 * math.sin(i * math.pi / 8) ** 2), (x_, y_, OZ + 3.15)]
for i in range(80): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
val = mesh('valance', vs, fs, M_VELVET, HALL); val.modifiers.new('sd', 'SOLIDIFY').thickness = 0.015
for k in range(11):
    prim('uv_sphere', f'fl{k}', emis(f'flm{k}', (1.0, 0.75, 0.45), 4.0), HALL, loc=(OX - 1.6 + 0.32 * k, OYF + 0.12, OZ + 0.03), segments=10, ring_count=6, radius=0.025)
FOOT = light_at('footl', 'AREA', (OX, OYF + 0.15, OZ + 0.12), (OX, OYF + 1.4, OZ + 1.2), 60, (1.0, 0.72, 0.42), 2.5)
# the painted backdrop: a dusk sky, mountains, a castle on the peak (Valhalla), side wings of painted trees
M_DROP = bpy.data.materials.new('drop'); M_DROP.use_nodes = True; nt_ = M_DROP.node_tree; nt_.nodes.remove(nt_.nodes['Principled BSDF'])
e_ = nt_.nodes.new('ShaderNodeEmission'); zz_ = sepz(nt_, coord(nt_, 'Object'))
c_ = ramp(nt_, ramp_v(nt_, zz_.outputs['Z'], OZ + 0.6, OZ + 3.0), [(0.0, (0.85, 0.40, 0.12)), (0.25, (0.62, 0.22, 0.16)), (0.55, (0.22, 0.10, 0.24)), (1.0, (0.03, 0.03, 0.09))])
c_ = mixc(nt_, math_(nt_, 'MULTIPLY', tnoise(nt_, coord(nt_, 'Object'), 2.0, 5.0), 0.25), c_, (0.95, 0.80, 0.60))
nt_.links.new(c_, e_.inputs['Color']); e_.inputs['Strength'].default_value = 0.6; nt_.links.new(e_.outputs[0], nt_.nodes['Material Output'].inputs['Surface'])
box('odrop', (3.7, 0.04, 3.1), (OX, OYF + 2.6, OZ + 1.55), M_DROP, parent=HALL)
M_MTN = mat('mtn', (0.05, 0.04, 0.07), 0.9); M_MTN2 = mat('mtn2', (0.10, 0.07, 0.10), 0.9)
for row_, (m_, yy, hs) in enumerate(((M_MTN2, OYF + 2.55, (0.9, 1.4, 1.1, 1.6, 0.8)), (M_MTN, OYF + 2.5, (0.5, 0.95, 1.5, 0.7, 0.55)))):
    pts = [(OX - 1.85, OZ)] + [(OX - 1.85 + 3.7 * (k + 0.5) / len(hs) + 0.2 * row_, OZ + h_) for k, h_ in enumerate(hs)] + [(OX + 1.85, OZ)]
    vs = [(x_, yy, z_) for x_, z_ in pts]; mesh(f'mtn{row_}', vs, [tuple(range(len(vs)))[::-1]], m_, HALL, smooth_=False)
for k, (dx_, w_, h_) in enumerate(((-0.12, 0.08, 0.35), (0.0, 0.14, 0.25), (0.12, 0.08, 0.32), (-0.05, 0.05, 0.42), (0.06, 0.04, 0.4))):
    box(f'castle{k}', (w_, 0.03, h_), (OX + 0.3 + 1.0 * 0.0 + dx_, OYF + 2.45, OZ + 1.55 + h_ / 2), M_MTN, parent=HALL)
M_WINGT = [noisy(mat(f'wingm{k}', c, 0.9), 6.0, 0.4) for k, c in enumerate(((0.025, 0.05, 0.03), (0.04, 0.07, 0.035)))]
for s_ in (-1, 1):
    for k in range(2):
        vs = [(0, 0, 0), (s_ * -0.75, 0, 0)]; fs = []
        for tier in range(4):
            w_ = 0.42 - 0.08 * tier; zb = 0.25 + 0.55 * tier; cx_ = s_ * -0.38
            vs += [(cx_ - w_, 0, zb), (cx_ + w_, 0, zb), (cx_, 0, zb + 0.75)]; fs.append((2 + 3 * tier, 3 + 3 * tier, 4 + 3 * tier))
        vs += [(s_ * -0.36, 0, 0), (s_ * -0.40, 0, 0), (s_ * -0.40, 0, 0.3), (s_ * -0.36, 0, 0.3)]; n_ = len(vs); fs.append((n_ - 4, n_ - 3, n_ - 2, n_ - 1))
        tr_ = mesh(f'wing{s_}{k}', vs, fs, M_WINGT[k], HALL, smooth_=False, loc=(OX + s_ * (1.8 - 0.05 * k), OYF + 0.8 + 0.7 * k, OZ))
        tr_.rotation_euler = (0, 0, s_ * R(-20)); tr_.modifiers.new('sd', 'SOLIDIFY').thickness = 0.01
# three costume figures on stage: dress forms with capes, wearing Doepler's horned and winged helmets
M_TUNIC = [noisy(mat('tunic0', (0.30, 0.30, 0.32), 0.45, 0.8), 60.0, 0.25), noisy(mat('tunic1', (0.30, 0.18, 0.08), 0.7, sheen=0.4), 20.0, 0.2), noisy(mat('tunic2', (0.10, 0.18, 0.12), 0.7, sheen=0.4), 20.0, 0.2)]
M_CAPE = [noisy(mat(f'cape{k}', c, 0.8, sheen=0.6), 8.0, 0.2) for k, c in enumerate(((0.35, 0.04, 0.03), (0.06, 0.08, 0.25), (0.30, 0.22, 0.06)))]
FIG = []
for k, fx in enumerate((-0.85, 0.0, 0.85)):
    base_ = Vector((OX + fx, OYF + 1.45 - 0.15 * abs(fx), OZ)); f_ = empty(f'fig{k}', HALL, loc=base_); f_.rotation_euler = (0, 0, R(-12 * fx))
    lathe(f'figbase{k}', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.03), (0.03, 0.05), (0.025, 0.85), (0.0, 0.85)], 20, M_BLACK, f_)
    lathe(f'figtorso{k}', [(0.0, 0.85), (0.13, 0.86), (0.16, 0.95), (0.14, 1.12), (0.17, 1.30), (0.20, 1.42), (0.12, 1.50), (0.05, 1.53), (0.0, 1.53)], 28, M_TUNIC[k], f_).scale = (1.0, 0.7, 1.0)
    lathe(f'figneck{k}', [(0.0, 1.5), (0.045, 1.5), (0.04, 1.62), (0.0, 1.62)], 16, M_DUMMY, f_)
    prim('uv_sphere', f'fighead{k}', M_DUMMY, f_, loc=(0, 0, 1.72), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
    belt_ = lathe(f'figbelt{k}', [(0.145, 1.10), (0.155, 1.10), (0.155, 1.14), (0.145, 1.14)], 28, M_BRASS, f_); belt_.scale = (1.0, 0.72, 1.0)
    vs = []; fs = []; ncx, ncz = 12, 8
    for j in range(ncz + 1):
        for i in range(ncx + 1):
            an = math.pi * (0.1 + 0.8 * i / ncx); rr = 0.2 + 0.12 * j / ncz
            vs.append((rr * math.cos(an) * 1.1, rr * math.sin(an) * 0.75 + 0.02 + 0.03 * math.sin(i * 1.7), 1.45 - 0.62 * j / ncz))
    for j in range(ncz):
        for i in range(ncx): a_ = j * (ncx + 1) + i; fs.append((a_, a_ + 1, a_ + ncx + 2, a_ + ncx + 1))
    cp_ = mesh(f'figcape{k}', vs, fs, M_CAPE[k], f_); cp_.modifiers.new('sd', 'SOLIDIFY').thickness = 0.01
    hm = horned_helmet(f'oh{k}', f_, M_STEEL, M_GOLD if k == 1 else M_BRASS, M_HORN, wings=(k == 1)); hm.location = (0, 0, 1.765)
    if k != 1:
        tube(f'spear{k}', [(0.24 * (1 if k == 2 else -1), 0.05, 0.0), (0.24 * (1 if k == 2 else -1), 0.05, 2.15)], 0.012, M_WOOD, f_, seg=6)
        prim('cone', f'spearh{k}', M_STEEL, f_, loc=(0.24 * (1 if k == 2 else -1), 0.05, 2.22), vertices=8, radius1=0.025, radius2=0.0, depth=0.14)
    FIG.append(f_)
OSPOTS = []
M_BEAM = bpy.data.materials.new('beam'); M_BEAM.use_nodes = True; nt_ = M_BEAM.node_tree; nt_.nodes.remove(nt_.nodes['Principled BSDF']); M_BEAM.blend_method = 'BLEND'
e_ = nt_.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (1.0, 0.92, 0.75, 1); e_.inputs['Strength'].default_value = 1.0
lw_ = nt_.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.5; gz_ = sepz(nt_, coord(nt_, 'Generated'))
af_ = math_(nt_, 'MULTIPLY', math_(nt_, 'MULTIPLY', objattr(nt_, 'a'), math_(nt_, 'POWER', math_(nt_, 'SUBTRACT', 1.0, lw_.outputs['Facing']), 3.0)), math_(nt_, 'ADD', 0.3, math_(nt_, 'MULTIPLY', gz_.outputs['Z'], 0.7)))
tr_ = nt_.nodes.new('ShaderNodeBsdfTransparent'); mx_ = nt_.nodes.new('ShaderNodeMixShader'); nt_.links.new(af_, mx_.inputs['Fac'])
nt_.links.new(tr_.outputs[0], mx_.inputs[1]); nt_.links.new(e_.outputs[0], mx_.inputs[2]); nt_.links.new(mx_.outputs[0], nt_.nodes['Material Output'].inputs['Surface'])
for k, fx in enumerate((-0.85, 0.0, 0.85)):
    src_ = Vector((OX + fx * 0.6, OYF - 0.4, OZ + 3.3)); tg_ = Vector((OX + fx, OYF + 1.4 - 0.15 * abs(fx), OZ + 1.5))
    lt = light_at(f'ospot{k}', 'SPOT', src_, tg_, 0.0, (1.0, 0.93, 0.78), 0.05); lt.data.spot_size = R(16); lt.data.spot_blend = 0.3
    cone_ = prim('cone', f'obeam{k}', M_BEAM, None, loc=(src_ + tg_) / 2, vertices=24, radius1=0.33, radius2=0.03, depth=(tg_ - src_).length)
    cone_.rotation_mode = 'QUATERNION'; cone_.rotation_quaternion = (src_ - tg_).to_track_quat('Z', 'Y'); cone_['a'] = 0.0
    OSPOTS.append((lt, cone_))
# Doepler's costume sketch on an easel, stage right
EASEL = empty('easel', HALL, loc=(OX + 3.0, 1.05, 0)); EASEL.rotation_euler = (0, 0, R(-22))
for s_ in (-1, 1): tube(f'easleg{s_}', [(s_ * 0.32, 0.0, 0.0), (s_ * 0.08, 0.05, 1.95)], 0.02, M_WOODRAW, EASEL, seg=6)
tube('easback', [(0, 0.45, 0.0), (0, -0.03, 1.8)], 0.02, M_WOODRAW, EASEL, seg=6)
box('eastray', (0.75, 0.06, 0.03), (0, -0.06, 0.85), M_WOODRAW, parent=EASEL)
SK = empty('sketch', EASEL, loc=(0, -0.1, 1.28)); SK.rotation_euler = (R(-8), 0, 0)
box('skpaper', (0.62, 0.008, 0.82), (0, 0, 0), noisy(mat('skp', (0.60, 0.54, 0.42), 0.85), 8.0, 0.1), parent=SK)
M_PENC = mat('pencil', (0.08, 0.07, 0.06), 0.8)
def sk_line(name, pts2, r=0.0035):
    return tube(name, [(x_, -0.006, z_) for x_, z_ in pts2], r, M_PENC, SK, seg=4)
sk_line('skdome', [(0.13 * math.cos(math.pi * i / 16), 0.0 + 0.12 * math.sin(math.pi * i / 16)) for i in range(17)])
sk_line('skbrow', [(-0.135, 0.0), (0.135, 0.0)]); sk_line('skbrow2', [(-0.135, -0.025), (0.135, -0.025)])
sk_line('sknose', [(0.0, -0.025), (0.0, -0.11)])
for s_ in (-1, 1):
    sk_line(f'skhorn{s_}a', [(s_ * (0.1 + 0.1 * u + 0.03 * u * u), 0.06 + 0.04 * u + 0.17 * u * u) for u in [i / 10 for i in range(11)]])
    sk_line(f'skhorn{s_}b', [(s_ * (0.12 + 0.08 * u + 0.03 * u * u), 0.03 + 0.04 * u + 0.18 * u * u + 0.012 * (1 - u)) for u in [i / 10 for i in range(11)]])
text3d('sktxt', 'C. E. DOEPLER', 0.045, (0, -0.007, -0.27), (R(90), 0, 0), M_PENC, SK, extrude=0.0005)
text3d('sktxt2', 'Ring, 1876', 0.04, (0, -0.007, -0.33), (R(90), 0, 0), M_PENC, SK, extrude=0.0005)


# ================================================================ exhibit 5: a shelf of horned helmets - the look takes over (x = 21.4)
SHX = 21.4
box('shback', (2.6, 0.06, 2.2), (SHX, 5.33, 1.85), M_WOOD, parent=HALL)
for k, zs in enumerate((0.95, 1.6, 2.25, 2.9)): box(f'shelf{k}', (2.6, 0.42, 0.04), (SHX, 5.12, zs), M_WOOD, bv=0.01, parent=HALL)
for s_ in (-1, 1): box(f'shside{s_}', (0.05, 0.42, 2.2), (SHX + s_ * 1.3, 5.12, 1.85), M_WOOD, parent=HALL)
SHELF = []
M_TRIMS = [M_BRASS, M_GOLD, M_IRDK]
for row_, zs in enumerate((0.97, 1.62, 2.27)):
    for col in range(4):
        h_ = horned_helmet(f'sh{row_}{col}', None, M_STEEL if (row_ + col) % 3 else M_IRON2, M_TRIMS[(row_ * 4 + col) % 3], M_HORN, wings=((row_ * 4 + col) % 5 == 3))
        h_.location = (SHX - 0.93 + 0.62 * col, 5.08, zs); h_.rotation_euler = (0, 0, R(-8 + 6 * col)); h_.scale = (0.0,) * 3
        SHELF.append(h_)


# ================================================================ outside the window: a Danish peat bog at sundown (x 24..80); the peat cut where the two bronze helmets turn up
BOG = empty('bog'); BZ = -0.55; WTR = -0.70
M_PEAT = mat('peat', (0.09, 0.06, 0.035), 0.9); nt_ = M_PEAT.node_tree; co_ = coord(nt_, 'Object')
f1_ = tnoise(nt_, co_, 0.35, 6.0, 0.5); f2_ = tnoise(nt_, co_, 2.5, 8.0)
c_ = ramp(nt_, math_(nt_, 'ADD', math_(nt_, 'MULTIPLY', f1_, 0.7), math_(nt_, 'MULTIPLY', f2_, 0.3)), [(0.3, (0.035, 0.025, 0.015)), (0.45, (0.07, 0.075, 0.025)), (0.55, (0.11, 0.10, 0.035)), (0.65, (0.09, 0.05, 0.045)), (0.8, (0.14, 0.11, 0.05))])
nt_.links.new(c_, nt_.nodes['Principled BSDF'].inputs['Base Color'])
bp_ = nt_.nodes.new('ShaderNodeBump'); bp_.inputs['Strength'].default_value = 0.6; nt_.links.new(tnoise(nt_, co_, 14.0, 8.0), bp_.inputs['Height']); nt_.links.new(bp_.outputs['Normal'], nt_.nodes['Principled BSDF'].inputs['Normal'])
M_PEATCUT = noisy(mat('peatcut', (0.05, 0.03, 0.018), 0.95), 18.0, 0.35)
M_BOGW = mat('bogwater', (0.01, 0.012, 0.01), 0.03, coat=0.5)
CUT = (31.2, 33.6, -0.75, 0.75); CUT_Z = BZ - 0.48                      # the peat cut trench: x0, x1, y0, y1, floor
def bog_h(x, y):
    n_ = mnoise.noise(Vector((x * 0.18, y * 0.18, 0.3))) * 0.22 + mnoise.noise(Vector((x * 0.6, y * 0.6, 1.7))) * 0.06
    pool = 0.0
    for (px, py, pr) in ((29.0, 3.6, 1.8), (36.5, -3.2, 2.4), (41.0, 4.5, 3.0), (47.0, -1.0, 3.5), (27.8, -3.2, 1.3), (55.0, 6.0, 5.0)):
        d_ = math.hypot(x - px, y - py) / pr
        if d_ < 1.4: pool = min(pool, -0.42 * (1 - min(1.0, d_) ** 2) + 0.02)
    flat = max(0.0, 1.0 - max(abs(x - 32.4) - 2.0, abs(y) - 1.5, 0.0) / 1.5)          # flatter round the cut
    return BZ + (n_ * (1 - flat) + 0.02 * n_ * flat) + pool * (1 - flat)
NXB, NYB = 150, 120; X0B, X1B, Y0B, Y1B = 24.3, 80.0, -26.0, 26.0
vs = []; fs = []
for j in range(NYB + 1):
    for i in range(NXB + 1):
        u = i / NXB; x_ = X0B + (X1B - X0B) * u ** 1.6; y_ = Y0B + (Y1B - Y0B) * j / NYB; vs.append((x_, y_, bog_h(x_, y_)))
for j in range(NYB):
    for i in range(NXB):
        a_ = j * (NXB + 1) + i; cx_ = (vs[a_][0] + vs[a_ + 1][0]) / 2; cy_ = (vs[a_][1] + vs[a_ + NXB + 1][1]) / 2
        if CUT[0] < cx_ < CUT[1] and CUT[2] < cy_ < CUT[3]: continue
        fs.append((a_, a_ + 1, a_ + NXB + 2, a_ + NXB + 1))
mesh('bogground', vs, fs, M_PEAT, BOG)
for k, (px, py, pr) in enumerate(((29.0, 3.6, 1.8), (36.5, -3.2, 2.4), (41.0, 4.5, 3.0), (47.0, -1.0, 3.5), (27.8, -3.2, 1.3), (55.0, 6.0, 5.0))):
    prim('cylinder', f'pool{k}', M_BOGW, BOG, loc=(px, py, WTR), vertices=40, radius=pr * 1.05, depth=0.01)
box('bogunder', (1.0, Y1B - Y0B, 3.0), (24.2, 0, -2.05), M_PEATCUT, parent=BOG)
# the trench: dark cut walls, a wet floor
CW = CUT[1] - CUT[0]; CH = CUT[3] - CUT[2]; CXc = (CUT[0] + CUT[1]) / 2
box('cutfloor', (CW, CH, 0.04), (CXc, 0, CUT_Z - 0.02), M_PEATCUT, parent=BOG)
for k, (sz_, lc_) in enumerate((((CW, 0.1, 0.62), (CXc, CUT[2] - 0.05, CUT_Z + 0.27)), ((CW, 0.1, 0.62), (CXc, CUT[3] + 0.05, CUT_Z + 0.27)),
                               ((0.1, CH + 0.2, 0.62), (CUT[0] - 0.05, 0, CUT_Z + 0.27)), ((0.1, CH + 0.2, 0.62), (CUT[1] + 0.05, 0, CUT_Z + 0.27)))):
    box(f'cutwall{k}', sz_, lc_, M_PEATCUT, parent=BOG)
box('cutpool', (CW - 0.1, CH - 0.1, 0.01), (CXc, 0, CUT_Z + 0.012), M_BOGW, parent=BOG)
# stacks of cut peat drying beside the trench
for k in range(46):
    st_ = k // 12; i_ = k % 12; x_ = 34.3 + 0.32 * (i_ % 6) + 0.16 * (st_ % 2); y_ = -0.6 + 0.28 * (i_ // 6) + 0.7 * (st_ // 2)
    box(f'peatb{k}', (0.28, 0.13, 0.1), (x_ + G.uniform(-0.02, 0.02), y_, bog_h(x_, y_) + 0.05 + 0.1 * (st_ // 2)), M_PEATCUT, bv=0.01, rot=(0, 0, G.uniform(-0.1, 0.1)), parent=BOG)
# the two bronze helmets, side by side on the trench floor, under a slab of peat that lifts away
M_BRZ = bronze_mat('bronze', 0.42); M_BRZ2 = bronze_mat('bronze2', 0.55, seed=3.0)
VK1 = vekso('vk1', M_BRZ, M_BRZ2); VK2 = vekso('vk2', M_BRZ2, M_BRZ)
VK1.location = (CXc - 0.42, -0.05, CUT_Z + 0.02); VK1.rotation_euler = (R(-6), R(4), R(-20))
VK2.location = (CXc + 0.48, 0.08, CUT_Z + 0.02); VK2.rotation_euler = (R(5), R(-3), R(25))
SLAB = empty('slab', BOG, loc=(CXc, 0, CUT_Z + 0.62))
box('slabm', (CW - 0.06, CH - 0.06, 0.18), (0, 0, -0.09), M_PEATCUT, bv=0.02, parent=SLAB)
box('slabtop', (CW - 0.06, CH - 0.06, 0.03), (0, 0, 0.005), M_PEAT, parent=SLAB)
M_SLABGR = noisy(mat('slabgr', (0.36, 0.30, 0.13), 0.7), 15.0, 0.3)
for k in range(60):
    p_ = Vector((G.uniform(-CW / 2 + 0.1, CW / 2 - 0.1), G.uniform(-CH / 2 + 0.1, CH / 2 - 0.1), 0.02)); d_ = Vector((G.uniform(-0.2, 0.2), G.uniform(-0.2, 0.2), 1)).normalized() * G.uniform(0.08, 0.2)
    tube(f'slabgr{k}', [p_, p_ + d_ * 0.6, p_ + d_ + Vector((d_.x, d_.y, 0)) * 0.5], lambda u: 0.005 * (1 - u) + 0.001, M_SLABGR, SLAB, seg=3, caps=False)
SPADE = empty('spade', SLAB, loc=(-CW / 2 + 0.35, -0.2, 0.0)); SPADE.rotation_euler = (R(-25), R(30), 0)
box('spblade', (0.16, 0.02, 0.3), (0, 0, -0.1), M_RUST, bv=0.005, parent=SPADE)
tube('spshaft', [(0, 0, 0.05), (0, 0, 1.25)], 0.02, M_WOODRAW, SPADE, seg=8)
tube('spgrip', [(-0.07, 0, 1.25), (0.07, 0, 1.25)], 0.017, M_WOODRAW, SPADE, seg=8)
DRIPS = [prim('ico_sphere', f'drip{k}', mat('dripm', (0.05, 0.04, 0.03), 0.05, trans=0.3), None, loc=(0, 0, -50), subdivisions=1, radius=G.uniform(0.008, 0.016)) for k in range(24)]
DRIP_P = [Vector((G.uniform(-CW / 2 + 0.1, CW / 2 - 0.1), G.uniform(-CH / 2 + 0.1, CH / 2 - 0.1), -0.18)) for k in range(24)]
# cotton grass, reeds, heather tufts, far trees
M_COTTON = mat('cotton', (0.92, 0.90, 0.86), 0.9, sheen=1.0); M_STALK = mat('stalk', (0.32, 0.30, 0.14), 0.8); M_REED = noisy(mat('reed', (0.42, 0.36, 0.16), 0.7), 15.0, 0.3)
M_HEATH = noisy(mat('heath', (0.10, 0.05, 0.07), 0.9), 25.0, 0.3)
COTTON = []
for k in range(520):
    x_ = 25.5 + 22.0 * G.random() ** 1.3; y_ = G.uniform(-9.0, 9.0)
    if CUT[0] - 0.3 < x_ < CUT[1] + 0.3 and CUT[2] - 0.3 < y_ < CUT[3] + 1.3: continue
    if 28.3 < x_ < 32.0 and -2.6 < y_ < -0.3: continue                        # keep the camera's way in clear
    z_ = bog_h(x_, y_)
    if z_ < WTR + 0.01: continue
    h_ = G.uniform(0.25, 0.5); lean_ = Vector((G.uniform(-0.06, 0.06), G.uniform(-0.06, 0.06), 0))
    p_ = Vector((x_, y_, z_))
    if k % 3 == 0:
        tube(f'cs{k}', [p_, p_ + lean_ * 0.5 + Vector((0, 0, h_ * 0.5)), p_ + lean_ + Vector((0, 0, h_))], 0.003, M_STALK, BOG, seg=3, caps=False)
        o = prim('ico_sphere', f'ch{k}', M_COTTON, BOG, loc=p_ + lean_ + Vector((0, 0, h_ + 0.012)), subdivisions=2, radius=0.016, scale=(1, 1, 1.4)); COTTON.append((o, o.location.copy(), G.uniform(0, 6)))
    elif k % 3 == 1:
        for b_ in range(4):
            d_ = Vector((G.uniform(-0.1, 0.1), G.uniform(-0.1, 0.1), 1)).normalized() * h_ * 0.8
            tube(f'rd{k}{b_}', [p_, p_ + d_ * 0.6, p_ + d_ + Vector((d_.x, d_.y, 0)) * 0.6], lambda u: 0.006 * (1 - u) + 0.001, M_REED, BOG, seg=3, caps=False)
    else:
        prim('ico_sphere', f'ht{k}', M_HEATH, BOG, loc=p_ + Vector((0, 0, 0.02)), subdivisions=2, radius=1.0, scale=(G.uniform(0.05, 0.11), G.uniform(0.05, 0.11), G.uniform(0.04, 0.07)))
M_TREE = noisy(mat('tree', (0.035, 0.06, 0.03), 0.9), 3.0, 0.3)
for k in range(70):
    x_ = G.uniform(58, 78); y_ = G.uniform(-24, 24); h_ = G.uniform(3.0, 7.0)
    prim('cone', f'tree{k}', M_TREE, BOG, loc=(x_, y_, bog_h(x_, y_) + h_ / 2), vertices=10, radius1=h_ * 0.28, radius2=0.0, depth=h_)
# mist: soft glowing sheets low over the bog
M_MIST = bpy.data.materials.new('mist'); M_MIST.use_nodes = True; nt_ = M_MIST.node_tree; nt_.nodes.remove(nt_.nodes['Principled BSDF']); M_MIST.blend_method = 'BLEND'
gen_ = sepz(nt_, coord(nt_, 'Generated'))
fade_ = math_(nt_, 'MULTIPLY', math_(nt_, 'MULTIPLY', math_(nt_, 'SINE', math_(nt_, 'MULTIPLY', gen_.outputs['X'], math.pi)), math_(nt_, 'SINE', math_(nt_, 'MULTIPLY', gen_.outputs['Y'], math.pi))), 0.22)
fade_ = math_(nt_, 'MULTIPLY', fade_, tnoise(nt_, coord(nt_, 'Object'), 0.4, 3.0))
e_ = nt_.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (1.0, 0.82, 0.62, 1); e_.inputs['Strength'].default_value = 0.9
tr_ = nt_.nodes.new('ShaderNodeBsdfTransparent'); mx_ = nt_.nodes.new('ShaderNodeMixShader'); nt_.links.new(fade_, mx_.inputs['Fac'])
nt_.links.new(tr_.outputs[0], mx_.inputs[1]); nt_.links.new(e_.outputs[0], mx_.inputs[2]); nt_.links.new(mx_.outputs[0], nt_.nodes['Material Output'].inputs['Surface'])
MIST = []
for k, (x_, w_, z_) in enumerate(((38.0, 14.0, -0.35), (44.0, 18.0, -0.25), (51.0, 22.0, -0.15), (58.0, 30.0, 0.0), (66.0, 40.0, 0.2))):
    o = prim('plane', f'mist{k}', M_MIST, BOG, loc=(x_, 0, z_ + 0.9), rot=(R(90), 0, R(90)), size=1.0, scale=(w_ * 2.4, 2.2 + 0.4 * k, 1)); MIST.append(o)
SUN = light_at('sun', 'SUN', (80, 10, 6), (30, 0, 0), 4.0, (1.0, 0.72, 0.45), 0.02); SUN.data.angle = R(1.5)
BOGFILL = light_at('bogfill', 'AREA', (29.0, -3.0, 2.5), (32.3, 0, CUT_Z), 0.0, (0.6, 0.7, 0.9), 3.0)
SKY = W_.node_tree.nodes.new('ShaderNodeTexSky')
try:
    SKY.sky_type = 'MULTIPLE_SCATTERING'; SKY.sun_elevation = R(4); SKY.sun_rotation = R(8); SKY.altitude = 30; SKY.air_density = 2.0
    for k_, v_ in (('dust_density', 4.0), ('aerosol_density', 4.0)):
        try: setattr(SKY, k_, v_)
        except Exception: pass
except Exception as e_: print('sky', e_)
W_.node_tree.links.new(SKY.outputs['Color'], WBG.inputs['Color']); WBG.inputs['Strength'].default_value = 0.0
# ================================================================ moving bits: sea spray, rain, the Gjermundbu pieces' flight paths, the helmet knocked off
GA = random.Random(21)
M_SPRAY = mat('spray', (0.70, 0.76, 0.80), 0.3, emit=(0.45, 0.52, 0.6), estr=0.15, alpha=0.75); M_SPRAY.blend_method = 'BLEND'
M_PUFF = mat('puff', (0.75, 0.80, 0.83), 0.9); nt_ = M_PUFF.node_tree; M_PUFF.blend_method = 'BLEND'
lw_ = nt_.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.5
soft_ = math_(nt_, 'POWER', math_(nt_, 'SUBTRACT', 1.0, lw_.outputs['Facing']), 2.5)
nt_.links.new(math_(nt_, 'MULTIPLY', objattr(nt_, 'a'), soft_), nt_.nodes['Principled BSDF'].inputs['Alpha'])
SPRAY = []                                                         # (obj, p0, v, t0, kind)
for k in range(700):
    u = GA.uniform(0.22, 0.52); p0 = hull_pt(u, 1.0, 1, 0.05) + Vector((0, GA.uniform(0.0, 0.25), GA.uniform(-0.05, 0.25)))
    v = Vector((GA.gauss(0.2, 0.5), -GA.uniform(1.0, 3.4), GA.uniform(1.2, 3.4))); t0 = GA.uniform(-0.12, 0.55)
    o = prim('ico_sphere', f'spr{k}', M_SPRAY, None, loc=(0, 0, -50), subdivisions=1, radius=GA.uniform(0.0025, 0.007)); o.rotation_mode = 'QUATERNION'; SPRAY.append((o, p0, v, t0, 0))
for k in range(40):
    u = GA.uniform(0.22, 0.52); p0 = hull_pt(u, 1.0, 1, 0.05) + Vector((0, GA.uniform(0.0, 0.2), GA.uniform(0.0, 0.3)))
    v = Vector((GA.gauss(0.2, 0.3), -GA.uniform(0.6, 1.8), GA.uniform(0.8, 2.2))); t0 = GA.uniform(0.0, 0.5)
    o = prim('ico_sphere', f'puff{k}', M_PUFF, None, loc=(0, 0, -50), subdivisions=2, radius=GA.uniform(0.06, 0.14)); o['a'] = 0.0; SPRAY.append((o, p0, v, t0, 1))
M_RAIN = emis_mix('rain', (0.7, 0.78, 0.9), 0.22, 'a')
RAIN = []
for k in range(240):
    o = box(f'rain{k}', (0.0022, 0.0022, 0.13), (0, 0, -50), M_RAIN); o['a'] = 0.0; o.rotation_euler = (R(8), R(-6), 0)
    RAIN.append((o, Vector((GA.uniform(-2.3, 2.3), GA.uniform(-0.1, 3.9), 0)), GA.uniform(0, 4.0), GA.uniform(6.5, 8.5)))
# the Gjermundbu helmet: assembled on the stand; each piece starts in the grave (offset from its place, turned) and flies home in turn
GJR, GJP = gjermundbu('a', M_RUST, iron_mat('rustdk', 0.6, base=(0.04, 0.035, 0.03), seed=6.0, rust_col=(0.09, 0.04, 0.02)))
GJR.location = GJ_TOP
GJ_REST = {nm: (o.location.copy(), o.rotation_euler.copy()) for nm, o in GJP.items()}
GJ_ORDER = ['brow', 'plate0', 'plate1', 'plate2', 'plate3', 'band0', 'band1', 'spike', 'spect']
GJ_FROM = {}
for k, nm in enumerate(GJ_ORDER):
    gp = Vector((GX - 0.75 + 1.5 * GA.random(), 2.35 + 0.4 * GA.random(), PLAT_Z + 0.05)) - GJ_TOP          # a spot in the grave
    eu = Vector((GA.uniform(-2.2, 2.2), GA.uniform(-1.4, 1.4), GA.uniform(-3, 3)))
    GJ_FROM[nm] = (gp, eu, 0.15 + 0.3 * k, 0.75)
# the test helmet knocked off the head: it tumbles once and a bit round HAXIS and lands at rest on its rim and one horn
TI = B[4] + 0.55; HV = Vector((-1.0, -0.5, 1.4)); HAXIS = Vector((0.12, 1.0, 0.08)).normalized()
HELM2.location = (0, 0, 0); HELM2.rotation_quaternion = (1, 0, 0, 0); bpy.context.view_layer.update()
H2V_HORN, H2V_BODY = [], []
for o in HELM2.children_recursive:
    if o.type != 'MESH': continue
    mw_ = o.matrix_world
    (H2V_HORN if '_horn' in o.name else H2V_BODY).extend(mw_ @ v.co for v in o.data.vertices)
H2V_ALL = H2V_HORN + H2V_BODY
def h2_minz(q, vs): return min((q @ v).z for v in vs)
best_ = None
for a_ in range(70, 135):
    q_ = Quaternion(HAXIS, R(a_)); zh, zb = h2_minz(q_, H2V_HORN), h2_minz(q_, H2V_BODY)
    sc_ = abs(zh - zb)
    if best_ is None or sc_ < best_[0]: best_ = (sc_, a_, min(zh, zb))
H2_A = R(best_[1]); H2_Z = PLAT_Z - best_[2] + 0.002                 # final roll angle and root height at rest
QF = Quaternion(HAXIS, H2_A)
_a, _b, _c = -4.9, HV.z, HELM2_P0.z - H2_Z
T_LAND = (-_b - math.sqrt(_b * _b - 4 * _a * _c)) / (2 * _a)
HW = (H2_A + 2 * math.pi) / T_LAND
HELM2.location = HELM2_P0
print('helm2 rest angle', best_[1], 'gap', round(best_[0], 4), 'land after', round(T_LAND, 3), 'land x', round(HELM2_P0.x + HV.x * T_LAND, 2))
def helm2_pose(t):
    tau = t - TI
    if tau <= 0: return HELM2_P0.copy(), Quaternion()
    if tau < T_LAND:
        p_ = HELM2_P0 + HV * tau + Vector((0, 0, -4.9 * tau * tau)); q_ = Quaternion(HAXIS, HW * tau)
        p_.z = max(p_.z, PLAT_Z + 0.002 - h2_minz(q_, H2V_ALL)); return p_, q_          # never through the platform
    d_ = tau - T_LAND; xy_ = HELM2_P0 + HV * T_LAND + Vector((HV.x, HV.y, 0)) * 0.12 * (1 - math.exp(-d_ * 8))
    bounce = 0.05 * abs(math.sin(d_ * 18)) * math.exp(-d_ * 9); wob_ = 0.12 * math.sin(d_ * 22) * math.exp(-d_ * 7)
    q_ = Quaternion(HAXIS, H2_A + wob_)
    return Vector((xy_.x, xy_.y, PLAT_Z + 0.002 - h2_minz(q_, H2V_ALL) + bounce)), q_
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
    key(0.0, (-0.08, 0.98, 1.66), (-0.42, 2.75, 1.42), 24),             # on deck, the helmet in front: the wave smashes over the far rail
    key(0.8, (-0.02, 0.92, 1.68), (-0.40, 2.75, 1.45), 24),
    key(2.7, (1.05, -0.85, 2.05), (-0.55, 1.75, 1.75), 24),              # out to the side: the whole bow, the dragon, the storm
    key(B[1] - 0.05, (0.95, -0.95, 2.05), (-0.55, 1.75, 1.75), 24),
    key(B[1] + 1.7, (1.5, -6.4, 2.45), (0.4, 1.6, 1.85), 24),            # pull way back: a diorama in a museum
    key(B[2] - 0.05, (1.6, -6.5, 2.47), (0.45, 1.6, 1.85), 24),
    key(B[2] + 1.3, (8.6, -1.25, 2.15), (7.3, 2.6, 0.75), 26),           # the grave mound, cut open; the shovel digs
    key(B[3] - 0.05, (8.5, -1.15, 2.1), (7.3, 2.6, 0.78), 26),
    key(B[3] + 0.9, (7.95, 0.40, 1.55), (7.5, 2.25, 1.02), 28),          # the nine pieces fly up onto the stand
    key(B[4] - 0.55, (7.88, 0.50, 1.50), (7.5, 2.2, 1.06), 28),
    key(B[4] + 0.25, (11.1, 0.3, 1.65), (11.1, 2.65, 1.38), 24),         # the sword hooks the horn, the helmet flies off
    key(B[5] - 0.05, (11.0, 0.4, 1.6), (10.9, 2.6, 1.3), 24),
    key(B[5] + 1.0, (16.3, -2.6, 2.35), (16.3, 2.0, 2.4), 24),           # the opera stage: the curtains open
    key(B[6] - 0.05, (16.3, -2.4, 2.32), (16.3, 2.0, 2.4), 24),
    key(B[6] + 0.9, (18.83, -0.08, 1.42), (19.27, 0.98, 1.28), 28),       # Doepler's sketch on the easel
    key(B[6] + 1.45, (18.8, -0.05, 1.43), (19.27, 0.98, 1.28), 28),
    key(B[6] + 2.25, (16.3, -0.6, 2.1), (16.3, 2.8, 2.25), 28),          # the costumes in the spotlights
    key(B[7] - 0.05, (16.33, -0.5, 2.08), (16.3, 2.8, 2.25), 28),
    key(B[7] + 0.8, (21.4, 1.3, 1.9), (21.4, 5.1, 1.75), 26),            # the shelf fills with horned helmets
    key(B[8] - 0.05, (21.4, 1.45, 1.88), (21.4, 5.1, 1.75), 26),
    key(B[8] + 0.7, (22.3, 0.2, 2.6), (26.0, 0.0, 2.4), 22),             # turn to the window ...
    key(B[8] + 1.5, (24.6, 0.0, 2.3), (31.5, 0.0, -0.4), 22),            # ... and out over the bog
    key(B[8] + 2.6, (30.1, -1.6, 0.5), (32.4, 0.0, -0.85), 26),         # the peat cut: the slab lifts, two bronze helmets
    key(B[9] - 0.05, (30.5, -1.35, 0.32), (32.4, 0.0, -0.85), 28),
    key(TOTAL, (31.1, -0.95, -0.02), (32.4, 0.0, -0.85), 32),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)

def flash(t):
    f_ = 0.0
    for t0, d_, a_ in ((0.42, 0.05, 0.8), (0.55, 0.06, 0.5), (2.85, 0.08, 1.0), (3.02, 0.05, 0.6)):
        if t0 <= t < t0 + d_: f_ = max(f_, a_ * (1 - (t - t0) / d_) ** 0.5)
    return f_

SHIP_C = Vector((0.2, SHIP_Y, 0.6))
def ship_pose(t):
    hit = 4.0 * math.exp(-max(0.0, t - 0.05) * 2.2) * math.sin(max(0.0, t - 0.05) * 5.0) if t > 0.05 else 0.0
    eu = Euler((R(2.2 * math.sin(1.25 * t + 0.3) + hit), R(1.3 * math.sin(0.85 * t + 1.0)), 0)); m3 = eu.to_matrix()
    return SHIP_C + Vector((0, 0, 0.03 * math.sin(1.1 * t))) - m3 @ SHIP_C, eu

def slab_pose(t):
    u = smooth(B[8] + 2.5, B[8] + 3.7, t)
    p0 = Vector((CXc, 0, CUT_Z + 0.62)); p1 = Vector((CXc + 0.1, 2.15, BZ + 0.17))
    lift = 0.55 * math.sin(math.pi * min(1.0, u * 1.15))
    p_ = p0.lerp(p1, sm(clamp((u - 0.25) / 0.75, 0, 1))) + Vector((0, 0, lift))
    return p_, Euler((R(-20) * math.sin(math.pi * u) + R(6) * u, R(4) * u, R(5) * u))

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- the storm on the ship: sea, rocking, sail, spray, rain, lightning, lantern
    xy = SEA_XY; z_ = WATER_Z + sea_h(xy[:, 0], xy[:, 1], t)
    co_ = np.column_stack([xy, z_]).astype(np.float32).ravel(); SEA.data.vertices.foreach_set('co', co_); SEA.data.update()
    loc_, eu_ = ship_pose(t); SHIP.location = loc_; SHIP.rotation_euler = eu_
    sv = SAIL_V0.copy(); ni, nj = SAIL_N[0] + 1, SAIL_N[1] + 1
    ii = np.tile(np.arange(ni), nj) / (ni - 1); jj = np.repeat(np.arange(nj), ni) / (nj - 1)
    sv[:, 0] -= (0.28 + 0.04 * math.sin(t * 2.7)) * np.sin(np.pi * ii) * np.sin(np.pi * (0.15 + 0.85 * jj)) * (1 + 0.08 * np.sin(t * 5 + jj * 6))
    SAIL.data.vertices.foreach_set('co', sv.astype(np.float32).ravel()); SAIL.data.update()
    rattle = 0.012 * math.exp(-max(0.0, t - 0.08) * 6) * math.sin(t * 60) if t > 0.08 else 0.0
    HELM1.location = CHEST_P + Vector((0.0, rattle * 0.5, 0.42 + abs(rattle))); HELM1.rotation_euler = (rattle * 2, -rattle * 3, R(18))
    M_ = Matrix.Translation(loc_) @ eu_.to_matrix().to_4x4()
    for o, p0, v, t0, kind in SPRAY:
        tau = t - t0
        if tau < 0 or tau > 1.3 or t > B[1] + 0.5: o.location = (0, 0, -50); continue
        p_ = M_ @ p0 + v * tau + Vector((0, 0, -4.9 * tau * tau)) * (0.6 if kind else 1.0)
        if p_.z < DECK_Z + 0.02 and abs(p_.y - SHIP_Y) < 0.9: o.location = (0, 0, -50); continue
        if p_.z < WATER_Z: o.location = (0, 0, -50); continue
        o.location = p_
        if not kind:
            vel = v + Vector((0, 0, -9.8 * tau)); o.rotation_quaternion = vel.to_track_quat('Z', 'Y'); o.scale = (1, 1, 1 + vel.length * 1.6)
        if kind: o['a'] = 0.22 * math.exp(-tau * 2.5) * min(1.0, tau * 8); o.scale = (1 + 2.0 * tau,) * 3
    rf = 1 - smooth(B[1] + 0.1, B[1] + 0.8, t)
    for o, p0, ph, sp in RAIN:
        if rf <= 0.001: o.location = (0, 0, -50); continue
        z = 4.2 - ((t * sp + ph * 1.3) % 4.0); o.location = (p0.x + 0.35 * (4.2 - z) * 0.14, p0.y - 0.3 * (4.2 - z) * 0.1, z); o['a'] = rf
    fl = flash(t); BOLT.data.energy = 1800 * fl; CYC['flash'] = fl; CYT['flash'] = fl
    LLIGHT.data.energy = 30 * (1 + 0.25 * wob(t, 8, 3)); STORM_KEY.data.energy = 160 + 800 * fl
    # ---- the museum lights come up as the diorama is revealed
    ml = smooth(B[1] + 0.1, B[1] + 0.9, t)
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * ml; lt.hide_render = ml < 0.002
    STORM_FILL.data.energy = 25 * (1 - 0.5 * ml)
    # ---- the shovel digs three times, throwing clods
    for c_ in range(3):
        s0 = B[2] + 0.25 + 1.25 * c_
        for k in range(8):
            o = CLODS[c_ * 8 + k]; tr = s0 + 0.72 + 0.02 * k; tau = t - tr
            if tau < 0: o.location = (0, 0, -50); continue
            p0 = SHOVEL_P + Vector((-0.05, 0.0, 0.55)) + Vector((0.03 * (k % 3), 0.02 * (k % 2), 0)); v = CLOD_V[c_ * 8 + k]
            T_ = (v.z + math.sqrt(v.z * v.z + 2 * 9.8 * (p0.z - PLAT_Z - 0.03))) / 9.8; tt = min(tau, T_)
            o.location = p0 + v * tt + Vector((0, 0, -4.9 * tt * tt))
    sd = 0.0; tilt = R(12); lift = 0.0
    for c_ in range(3):
        s = (t - (B[2] + 0.25 + 1.25 * c_)) / 1.0
        if 0 <= s <= 1.0:
            sd = 0.14 * smooth(0.0, 0.25, s) * (1 - smooth(0.4, 0.6, s)); lift = 0.42 * smooth(0.4, 0.72, s) * (1 - smooth(0.8, 1.0, s))
            tilt = R(12) + R(38) * smooth(0.3, 0.5, s) * (1 - smooth(0.62, 0.78, s)) - R(30) * smooth(0.62, 0.74, s) * (1 - smooth(0.8, 1.0, s))
    SHOVEL.location = SHOVEL_P + Vector((0.12 * lift, 0, -sd + lift)); SHOVEL.rotation_euler = (0, tilt, 0)
    # ---- the nine pieces fly from the grave up onto the stand
    for nm, (off, eu, ts, du) in GJ_FROM.items():
        o = GJP[nm]; l0, r0 = GJ_REST[nm]; u = smooth(B[3] + ts, B[3] + ts + du, t)
        lift_ = 0.35 * math.sin(math.pi * u)
        o.location = l0 + off * (1 - u) + Vector((0, 0, lift_)); o.rotation_euler = (r0.x + eu.x * (1 - u), r0.y + eu.y * (1 - u), r0.z + eu.z * (1 - u))
    # ---- the sword swings down, hooks the horn, the helmet flies off and lands
    s = clamp((t - (TI - 0.4)) / 0.4, 0, 1); ft = clamp((t - TI) / 0.3, 0, 1)
    th = R(200) - R(160) * s * s - R(25) * (1 - (1 - ft) ** 2) + R(6) * math.sin(clamp(t - TI - 0.3, 0, 1) * 14) * math.exp(-max(0.0, t - TI - 0.3) * 5) * (ft >= 1)
    SWORD.rotation_euler = (0, th, 0)
    hp_, hq_ = helm2_pose(t); HELM2.location = hp_; HELM2.rotation_quaternion = hq_
    # ---- the opera: curtains draw apart, then the spotlights snap on
    uc = smooth(B[5] + 0.25, B[5] + 1.35, t)
    for c_ in CURT: c_.scale = (1 - 0.8 * uc, 1, 1)
    for k, (lt, cone_) in enumerate(OSPOTS):
        on = smooth(B[6] + 1.7 + 0.18 * k, B[6] + 1.78 + 0.18 * k, t); lt.data.energy = 900 * on; cone_['a'] = 0.12 * on; lt.hide_render = on < 0.001
        cone_.hide_render = on < 0.001
    # ---- the shelf fills, one helmet after another
    for k, h_ in enumerate(SHELF):
        u = clamp((t - (B[7] + 0.2 + 0.16 * k)) / 0.28, 0, 1); sc = 0.8 * (u * u * (3 - 2 * u) + 0.25 * math.sin(math.pi * u)) if u > 0 else 0.0
        h_.scale = (max(sc, 0.0001),) * 3; h_.hide_render = u <= 0.0
    # ---- outside: the slab of peat lifts, drips fall, the grass sways; the sky lights the room as we go out
    sp_, se_ = slab_pose(t); SLAB.location = sp_; SLAB.rotation_euler = se_
    for k, o in enumerate(DRIPS):
        tr = B[8] + 2.65 + 0.04 * k
        if t < tr or t > tr + 1.2: o.location = (0, 0, -50); continue
        ps_, pe_ = slab_pose(tr); p0 = Matrix.Translation(ps_) @ pe_.to_matrix().to_4x4() @ DRIP_P[k]; tau = t - tr
        p_ = p0 + Vector((0, 0, -4.9 * tau * tau))
        o.location = p_ if p_.z > CUT_Z + 0.02 else (0, 0, -50)
    for o, p0, ph in COTTON: o.location = p0 + Vector((0.02 * math.sin(t * 1.7 + ph), 0.015 * math.cos(t * 1.3 + ph), 0))
    for k, o in enumerate(MIST): o.location.y = 0.3 * math.sin(t * 0.2 + k)
    out = smooth(B[8] + 0.4, B[8] + 1.6, t)
    WBG.inputs['Strength'].default_value = 0.01 + 0.35 * out; BOGFILL.data.energy = 120 * out
    # ---- camera, with a little life in it (a jolt when the wave hits)
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3) + (shake(t, 0.035, 4.0, 13.0) * math.exp(-max(0, t - 0.08) * 5.0) if t > 0.08 else Vector())
    look(cp, ct, lens, 5.6 if t < B[8] + 1.5 else 8.0)
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

