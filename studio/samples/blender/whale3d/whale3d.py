# A humpback whale scoops up a lobster diver off Cape Cod (Michael Packard, 2021): the myth, the mouth, the throat, 30-40 seconds in the dark,
# spat out at the surface, no broken bones, and the one whale that could swallow you (a sperm whale gulping a giant squid). One continuous shot.
#   python3 whale3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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

def ramp_v(nt, fac, a_, b_):
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = a_; mr.inputs['From Max'].default_value = b_
    mr.interpolation_type = 'SMOOTHSTEP'; nt.links.new(fac, mr.inputs['Value']); return mr.outputs['Result']


# ================================================================ the set: Cape Cod Bay, about 14 m (45 ft) deep. Green-blue water as a volume under a
# rolling ocean surface, sun shafts through it (a shadow-only ripple screen just under the surface), a sandy bottom with ripples, rocks and weed,
# a bright sky above for the surface shots, and a lobster boat.
SEA_Z = 0.0; FLOOR_Z = -13.7
# ---- the sky (seen above water and through the surface from below)
sky = W_.node_tree.nodes.new('ShaderNodeTexSky')
try: sky.sky_type = 'MULTIPLE_SCATTERING'
except Exception: pass
for k_, v_ in (('sun_elevation', R(48)), ('sun_rotation', R(140)), ('altitude', 10.0), ('air_density', 1.0), ('dust_density', 2.0)):
    try: setattr(sky, k_, v_)
    except Exception: pass
W_.node_tree.links.new(sky.outputs['Color'], WBG.inputs['Color']); WBG.inputs['Strength'].default_value = 0.3
SUN = light_at('sun', 'SUN', (0, 0, 50), (math.cos(R(140)) * -0.9, math.sin(R(140)) * -0.9, 0), 3.2, (1.0, 0.96, 0.9), 0.02)
SUN.data.angle = R(1.2)
# ---- the ocean surface: an ocean-modifier grid, glass from both sides, but it lets the sun's shadow rays through
SURF = prim('plane', 'surface', None, loc=(0, 0, SEA_Z), size=1.0)
oc = SURF.modifiers.new('ocean', 'OCEAN'); oc.geometry_mode = 'GENERATE'; oc.repeat_x = 1; oc.repeat_y = 1; oc.size = 1.0
oc.spatial_size = 120; oc.resolution = 10; oc.wave_scale = 0.4; oc.choppiness = 0.9; oc.wind_velocity = 7.0; oc.random_seed = 3
SURFM = bpy.data.materials.new('sea_surface'); SURFM.use_nodes = True; nt = SURFM.node_tree; b_ = nt.nodes['Principled BSDF']
b_.inputs['Base Color'].default_value = (0.05, 0.25, 0.26, 1); b_.inputs['Roughness'].default_value = 0.04; b_.inputs['Transmission Weight'].default_value = 1.0
b_.inputs['IOR'].default_value = 1.333
lp = nt.nodes.new('ShaderNodeLightPath'); tr_ = nt.nodes.new('ShaderNodeBsdfTransparent'); mx_ = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Shadow Ray'], mx_.inputs['Fac']); nt.links.new(b_.outputs[0], mx_.inputs[1]); nt.links.new(tr_.outputs[0], mx_.inputs[2])
nt.links.new(mx_.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
SURF.data.materials.append(SURFM)
for p_ in SURF.data.polygons: p_.use_smooth = True
# a darker, bluer open sea out past the ocean tile
_fv = []; _ff = []
for k in range(64):
    a_ = 2 * math.pi * k / 64; _fv += [(59.0 * math.cos(a_), 59.0 * math.sin(a_), 0.0), (2500 * math.cos(a_), 2500 * math.sin(a_), 0.0)]
for k in range(64): k2 = (k + 1) % 64; _ff.append((2 * k, 2 * k2, 2 * k2 + 1, 2 * k + 1))
FARSEAM = mat('farsea', (0.02, 0.07, 0.09), 0.08, coat=0.6)
FARSEA = mesh('farsea', _fv, _ff, FARSEAM, smooth_=False, loc=(0, 0, SEA_Z - 0.05))
# ---- the water: green-blue, light scatters forward; deeper is darker
WATERV = bpy.data.materials.new('water_vol'); WATERV.use_nodes = True; nt = WATERV.node_tree; out_ = nt.nodes['Material Output']
nt.nodes.remove(nt.nodes['Principled BSDF'])
vs_ = nt.nodes.new('ShaderNodeVolumeScatter'); vs_.inputs['Color'].default_value = (0.40, 0.75, 0.70, 1); vs_.inputs['Density'].default_value = 0.034
try: vs_.inputs['Anisotropy'].default_value = 0.75
except Exception: pass
va_ = nt.nodes.new('ShaderNodeVolumeAbsorption'); va_.inputs['Color'].default_value = (0.22, 0.62, 0.58, 1); va_.inputs['Density'].default_value = 0.055
ad_ = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(vs_.outputs[0], ad_.inputs[0]); nt.links.new(va_.outputs[0], ad_.inputs[1])
nt.links.new(ad_.outputs[0], out_.inputs['Volume'])
VOL = box('water', (600, 600, 140), (0, 0, SEA_Z - 70.03), WATERV)
VOLM_DEEP = None
# ---- sun shafts: a ripple screen a little under the surface, seen only by shadow rays
GOBO = bpy.data.materials.new('gobo'); GOBO.use_nodes = True; nt = GOBO.node_tree; out_ = nt.nodes['Material Output']; nt.nodes.remove(nt.nodes['Principled BSDF'])
lp = nt.nodes.new('ShaderNodeLightPath'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 1.1
vo.voronoi_dimensions = '4D'; GOBO_W = vo.inputs['W']
GOBO_MAP = nt.nodes.new('ShaderNodeMapping'); nt.links.new(coord(nt, 'Object'), GOBO_MAP.inputs['Vector'])
wn_ = nt.nodes.new('ShaderNodeTexNoise'); wn_.inputs['Scale'].default_value = 0.6; nt.links.new(GOBO_MAP.outputs['Vector'], wn_.inputs['Vector'])
vd_ = nt.nodes.new('ShaderNodeVectorMath'); vd_.operation = 'ADD'; nt.links.new(GOBO_MAP.outputs['Vector'], vd_.inputs[0]); nt.links.new(wn_.outputs['Color'], vd_.inputs[1])
nt.links.new(vd_.outputs[0], vo.inputs['Vector'])
mask_ = ramp_v(nt, vo.outputs['Distance'], 0.015, 0.09)
fac_ = math_(nt, 'MULTIPLY', lp.outputs['Is Shadow Ray'], math_(nt, 'MULTIPLY', mask_, 0.62))
tr_ = nt.nodes.new('ShaderNodeBsdfTransparent'); df_ = nt.nodes.new('ShaderNodeBsdfDiffuse'); df_.inputs['Color'].default_value = (0, 0, 0, 1)
mx_ = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fac_, mx_.inputs['Fac']); nt.links.new(tr_.outputs[0], mx_.inputs[1]); nt.links.new(df_.outputs[0], mx_.inputs[2])
nt.links.new(mx_.outputs[0], out_.inputs['Surface'])
SCREEN = prim('plane', 'gobo', GOBO, loc=(0, 0, SEA_Z - 0.6), size=300)
# ---- the bottom: sand with ripples and patches of darker silt, rocks, weed
SAND = mat('sand', (0.42, 0.38, 0.30), 0.95); nt = SAND.node_tree; b_ = nt.nodes['Principled BSDF']; co = coord(nt, 'Object')
wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 0.9; wv.inputs['Distortion'].default_value = 3.0; wv.inputs['Detail'].default_value = 3.0
nt.links.new(co, wv.inputs['Vector'])
bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5; bp.inputs['Distance'].default_value = 0.05
nt.links.new(math_(nt, 'ADD', wv.outputs['Fac'], math_(nt, 'MULTIPLY', tnoise(nt, co, 9.0, 8.0), 0.6)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b_.inputs['Normal'])
nt.links.new(mixc(nt, ramp_v(nt, tnoise(nt, co, 0.12, 4.0), 0.45, 0.62), (0.42, 0.38, 0.30), (0.22, 0.22, 0.18)), b_.inputs['Base Color'])
FLOOR = prim('plane', 'floor', SAND, loc=(0, 0, FLOOR_Z), size=400)
sub_ = FLOOR.modifiers.new('sub', 'SUBSURF'); sub_.subdivision_type = 'SIMPLE'; sub_.levels = sub_.render_levels = 6
tx_ = bpy.data.textures.new('dunes', 'CLOUDS'); tx_.noise_scale = 14.0
dp_ = FLOOR.modifiers.new('disp', 'DISPLACE'); dp_.texture = tx_; dp_.strength = 1.4; dp_.texture_coords = 'GLOBAL'
ROCKM = mat('rock', (0.20, 0.19, 0.17), 0.85); noisy(ROCKM, 3.0, 0.45, 0.1)
rr_ = random.Random(11); ROCKS = []
for j in range(70):
    x_, y_ = rr_.uniform(-60, 60), rr_.uniform(-40, 60); r0 = rr_.uniform(0.3, 1.6)
    o = prim('ico_sphere', f'rock{j}', ROCKM, loc=(x_, y_, FLOOR_Z + 0.2), radius=r0, subdivisions=3)
    o.scale = (rr_.uniform(0.8, 1.4), rr_.uniform(0.8, 1.3), rr_.uniform(0.4, 0.8)); o.rotation_euler = (0, 0, rr_.uniform(0, 6))
    dd = o.modifiers.new('d', 'DISPLACE'); dd.texture = tx_; dd.strength = 0.35 * r0; ROCKS.append(o)
WEEDM = mat('weed', (0.18, 0.22, 0.06), 0.6, trans=0.25, sheen=0.3)
WEED = []
for j in range(60):
    x_, y_ = rr_.uniform(-30, 30), rr_.uniform(-20, 40); h_ = rr_.uniform(0.8, 2.6)
    pts = [(x_ + 0.15 * math.sin(k * 0.9 + j), y_ + 0.1 * math.cos(k * 0.7 + j), FLOOR_Z + 0.4 + h_ * k / 9) for k in range(10)]
    o = tube(f'weed{j}', pts, lambda u: 0.035 * (1 - 0.7 * u) + 0.01, WEEDM, seg=6); o.scale = (1.0, 1.0, 1.0); WEED.append((o, j))
# ---- the lobster boat at the surface: a 35 ft Down East hull (high flared bow, low stern), wheelhouse forward with windows, a mast with
# radar and antennas, a hauler and davit on the starboard side, stacked traps, painted buoys, rails, an exhaust stack, hull numbers.
BOAT = empty('boat_root', loc=(14.0, 10.0, SEA_Z))
HULLM = mat('hull', (0.80, 0.81, 0.80), 0.25, coat=0.6); noisy(HULLM, 4.0, 0.06, 0.05)
BOTM = mat('bottom', (0.42, 0.07, 0.05), 0.6); BOOTM = mat('boot', (0.06, 0.12, 0.30), 0.35, coat=0.5)
DECKM = mat('deck', (0.58, 0.56, 0.50), 0.75); noisy(DECKM, 18.0, 0.18, 0.1)
TRIMM = mat('trim', (0.06, 0.12, 0.30), 0.35, coat=0.5); GLASSB = mat('bglass', (0.02, 0.03, 0.04), 0.03, coat=1.0)
STEEL = mat('steel', (0.7, 0.7, 0.72), 0.2, metal=1.0); RUBBER = mat('rubber', (0.03, 0.03, 0.03), 0.7)
L_B = 10.6
def hull_sec(u):
    """u 0 = transom .. 1 = stem: half-beam, sheer height, keel depth, flare"""
    b = 1.85 * (1 - (max(0.0, u - 0.45) / 0.55) ** 2.2) ** 0.75 * (1 - 0.08 * (1 - u) ** 3)
    h = 1.05 + 0.75 * u ** 2.4; k = 0.55 + 0.25 * math.sin(math.pi * min(u, 0.9) / 0.9) ** 0.5 - 0.3 * u ** 6
    return b, h, k
hv = []; hf = []; NH = 60; NSC = 14
for i in range(NH):
    u = i / (NH - 1); x_ = -L_B / 2 + L_B * u; b, h, k = hull_sec(u)
    ring = []
    for j in range(NSC):                                                   # keel -> chine -> flared topsides -> sheer, starboard side
        v = j / (NSC - 1)
        y_ = b * (math.sin(v * math.pi / 2) ** 0.55) * (0.9 + 0.1 * v) + 0.05 * v ** 3
        z_ = -k + (k + h) * (v ** 1.5)
        ring.append((x_, max(y_, 0.02), z_))
    hv += ring + [(x_, -y_, z_) for (x_, y_, z_) in ring[::-1]]
NR2 = 2 * NSC
for i in range(NH - 1):
    for j in range(NR2 - 1): hf.append((i * NR2 + j, i * NR2 + j + 1, (i + 1) * NR2 + j + 1, (i + 1) * NR2 + j))
hf.append(tuple(range(NR2))[::-1])                                          # the transom
HULL = mesh('hull', hv, hf, HULLM, BOAT); HULL.data.materials.append(BOTM); HULL.data.materials.append(BOOTM)
for p_ in HULL.data.polygons:
    zc = sum(HULL.data.vertices[v].co.z for v in p_.vertices) / len(p_.vertices)
    p_.material_index = 1 if zc < 0.05 else (2 if zc < 0.18 else 0)
HULL.modifiers.new('th', 'SOLIDIFY').thickness = 0.05; subsurf(HULL, 1)
# decks: the cockpit sole aft, the foredeck up at the sheer
deck_pts = []
for i in range(30):
    u = i / 29 * 0.62; b, h, k = hull_sec(u); deck_pts.append((-L_B / 2 + L_B * u, b * 0.96))
dv = [(x_, y_, 0.55) for x_, y_ in deck_pts] + [(x_, -y_, 0.55) for x_, y_ in deck_pts[::-1]]
mesh('cockpit_sole', dv, [tuple(range(len(dv)))], DECKM, BOAT, smooth_=False)
fd = []
for i in range(30):
    u = 0.62 + 0.37 * i / 29; b, h, k = hull_sec(u); fd.append((-L_B / 2 + L_B * u, b * 0.97, h - 0.03))
fv_ = [(x_, y_, z_) for x_, y_, z_ in fd] + [(x_, -y_, z_) for x_, y_, z_ in fd[::-1]]
mesh('foredeck', fv_, [tuple(range(len(fv_)))], DECKM, BOAT, smooth_=False)
# rub rail and cap rail along the sheer
for sy in (1, -1):
    rail = [(-L_B / 2 + L_B * u, sy * (hull_sec(u)[0] + 0.06), hull_sec(u)[1]) for u in [i / 40 for i in range(41)]]
    tube(f'caprail{sy}', rail, 0.045, TRIMM, BOAT, seg=8)
    tube(f'rubrail{sy}', [(x_, y_ + sy * 0.02, z_ - 0.35) for (x_, y_, z_) in rail], 0.035, RUBBER, BOAT, seg=8)
# wheelhouse with windows all round, a roof with an overhang, a mast, radar and antennas
HX = 1.2
house = box('house', (2.9, 2.9, 1.9), (HX, 0, 0.55 + 0.95), HULLM, bv=0.07, parent=BOAT)
box('roof', (3.6, 3.2, 0.12), (HX - 0.2, 0, 2.52), HULLM, bv=0.04, parent=BOAT)
for k_, (pos, size) in enumerate((((HX + 1.46, 0, 1.95), (0.04, 2.5, 0.7)), ((HX, 1.46, 1.95), (2.2, 0.04, 0.6)), ((HX, -1.46, 1.95), (2.2, 0.04, 0.6)))):
    box(f'win{k_}', size, pos, GLASSB, parent=BOAT)
for yy in (-0.85, 0.0, 0.85): box(f'mull{yy}', (0.06, 0.06, 0.72), (HX + 1.48, yy, 1.95), TRIMM, parent=BOAT)
box('stripe_house', (2.95, 2.95, 0.08), (HX, 0, 1.52), TRIMM, parent=BOAT)
tube('mast', [(HX - 0.6, 0, 2.55), (HX - 0.6, 0, 4.3)], 0.05, STEEL, BOAT, seg=10)
box('radar_arm', (1.6, 0.14, 0.12), (HX - 0.6, 0, 4.0), mat('radar', (0.9, 0.9, 0.88), 0.4), bv=0.03, parent=BOAT)
prim('cylinder', 'radar_base', mat('radarb', (0.9, 0.9, 0.88), 0.4), BOAT, loc=(HX - 0.6, 0, 3.85), radius=0.16, depth=0.22, vertices=18)
for yy in (0.9, -0.9): tube(f'whip{yy}', [(HX - 1.6, yy, 2.58), (HX - 1.7, yy, 5.2)], lambda u: 0.02 * (1 - 0.7 * u), mat('whip', (0.92, 0.92, 0.9), 0.4), BOAT, seg=6)
prim('uv_sphere', 'light', emis('masthead', (1.0, 1.0, 0.95), 2.0), BOAT, loc=(HX - 0.6, 0, 4.35), radius=0.06, segments=10, ring_count=6)
# exhaust stack, hauler on its davit, bait barrel
tube('exhaust', [(HX - 1.3, 1.25, 1.0), (HX - 1.3, 1.25, 3.0)], 0.09, STEEL, BOAT, seg=12)
tube('davit', [(HX - 1.7, 1.75, 1.1), (HX - 1.7, 1.75, 2.6), (HX - 1.7, 2.1, 2.8), (HX - 1.7, 2.35, 2.6)], 0.045, STEEL, BOAT, seg=10)
prim('cylinder', 'block', STEEL, BOAT, loc=(HX - 1.7, 2.35, 2.5), radius=0.11, depth=0.06, vertices=16, rot=(R(90), 0, 0))
prim('cylinder', 'hauler', mat('hauler', (0.75, 0.75, 0.78), 0.25, metal=1.0), BOAT, loc=(HX - 1.7, 1.55, 1.3), radius=0.2, depth=0.18, vertices=24, rot=(R(90), 0, 0))
prim('cylinder', 'barrel', mat('barrel', (0.15, 0.32, 0.6), 0.5), BOAT, loc=(-2.6, -1.0, 0.95), radius=0.28, depth=0.8, vertices=20)
# lobster traps: green vinyl-coated wire boxes, stacked
TRAPM = mat('trap', (0.08, 0.30, 0.10), 0.5)
_trap = prim('cube', 'trap_src', TRAPM, size=1.0, scale=(1.15, 0.58, 0.42)); _sb = _trap.modifiers.new('sub', 'SUBSURF'); _sb.subdivision_type = 'SIMPLE'; _sb.levels = _sb.render_levels = 3
_wf = _trap.modifiers.new('wire', 'WIREFRAME'); _wf.thickness = 0.012; _trap.parent = BOAT; _trap.location = (-1.4, -0.7, 0.78)
for k_, (x_, y_, z_) in enumerate(((-1.4, 0.7, 0.78), (-2.8, -0.7, 0.78), (-2.8, 0.7, 0.78), (-1.4, -0.7, 1.21), (-2.8, 0.7, 1.21), (-4.0, 0.0, 0.78))):
    t_ = _trap.copy(); S.collection.objects.link(t_); t_.parent = BOAT; t_.location = (x_, y_, z_); t_.rotation_euler = (0, 0, R(3 * k_ - 6))
# painted buoys hung on the house side and on the rail
BUOYM = [mat('buoy_a', (0.95, 0.45, 0.05), 0.5), mat('buoy_b', (0.95, 0.95, 0.9), 0.5), mat('buoy_c', (0.08, 0.35, 0.75), 0.5)]
for k_ in range(5):
    bz = lathe(f'buoy{k_}', [(0.0, 0.0), (0.09, 0.05), (0.13, 0.2), (0.13, 0.45), (0.08, 0.6), (0.02, 0.62)], 16, BUOYM[k_ % 3], BOAT, loc=(HX - 1.45, -1.47 - 0.01 * k_, 1.0 + 0.0))
    bz.location = (HX - 1.4 + 0.33 * k_, -1.5, 1.05); bz.data.materials.append(BUOYM[(k_ + 1) % 3])
    for p_ in bz.data.polygons:
        zc = sum(bz.data.vertices[v].co.z for v in p_.vertices) / len(p_.vertices); p_.material_index = 1 if 0.25 < zc < 0.4 else 0
    tube(f'buoyspindle{k_}', [(HX - 1.4 + 0.33 * k_, -1.5, 1.65), (HX - 1.4 + 0.33 * k_, -1.5, 0.95)], 0.012, mat('spindle', (0.6, 0.45, 0.25), 0.7), BOAT, seg=6)
# the dive flag on a float (red with a white stripe)
FLAGM = mat('diveflag', (0.75, 0.04, 0.03), 0.6); FLOAT = empty('float', loc=(-3.0, 6.0, SEA_Z))
prim('uv_sphere', 'floatball', mat('floatball', (0.9, 0.35, 0.05), 0.4), FLOAT, loc=(0, 0, 0.12), radius=0.28, segments=16, ring_count=10)
tube('flagpole', [(0, 0, 0.2), (0, 0, 1.4)], 0.015, mat('pole', (0.8, 0.8, 0.8), 0.4), FLOAT, seg=8)
fl_ = box('flag', (0.02, 0.6, 0.45), (0, 0.32, 1.15), FLAGM, parent=FLOAT)
box('flagstripe', (0.025, 0.7, 0.08), (0, 0.32, 1.15), mat('flagw', (0.9, 0.9, 0.9), 0.6), parent=FLOAT, rot=(R(-37), 0, 0))

# ================================================================ the humpback: lofted from real proportions (about 14 m long), a hinged lower jaw and
# pleated throat pouch that balloons when it gulps, baleen hanging from the upper jaw, long white flippers, knobby tubercles on the head, flukes.
# Local frame: the snout tip is at x = 0, the whale faces +x, the tail runs to -x; z is up. Shape keys open the jaw, swell the pouch, bend the tail.
def interp_tab(tab, s, col):
    """smooth (Catmull-Rom) through the table, so the body has no ribs at the stations"""
    n = len(tab)
    if s <= tab[0][0]: return tab[0][col]
    if s >= tab[-1][0]: return tab[-1][col]
    i = max(j for j in range(n - 1) if tab[j][0] <= s)
    x0, x1 = tab[i][0], tab[i + 1][0]; u = (s - x0) / (x1 - x0)
    p1, p2 = tab[i][col], tab[i + 1][col]
    p0 = tab[i - 1][col] if i > 0 else p1 - (p2 - p1); p3 = tab[i + 2][col] if i + 2 < n else p2 + (p2 - p1)
    h0 = (x1 - tab[i - 1][0]) if i > 0 else 2 * (x1 - x0); h1_ = (tab[i + 2][0] - x0) if i + 2 < n else 2 * (x1 - x0)
    m1 = (p2 - p0) / h0 * (x1 - x0); m2 = (p3 - p1) / h1_ * (x1 - x0)
    u2, u3 = u * u, u * u * u
    return (2 * u3 - 3 * u2 + 1) * p1 + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2 + (u3 - u2) * m2

def xray_mix(m, glow=(0.35, 0.75, 1.0), prop='xr'):
    """blend the surface toward a see-through glowing x-ray shell, driven by the object's property 'xr' (0..1)"""
    nt = m.node_tree; out_ = nt.nodes['Material Output']; src = out_.inputs['Surface'].links[0].from_socket
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*glow, 1)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 2.2), 2.4), em.inputs['Strength'])
    add = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, prop), mx.inputs['Fac'])
    nt.links.new(src, mx.inputs[1]); nt.links.new(add.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out_.inputs['Surface'])
    return m

def whale_skin(name, dark, light, belly_z, pleats=False, rough=0.38):
    """dark back, a mottled white belly below belly_z (object space), wet coat; pleats: long grooves down the throat"""
    m = mat(name, dark, rough, coat=0.25); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    co = coord(nt, 'Object'); sx = sepz(nt, co)
    nz = tnoise(nt, co, 0.9, 8.0, 0.4); nz2 = tnoise(nt, co, 6.0, 4.0)
    edge = math_(nt, 'ADD', sx.outputs['Z'], math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz, 0.5), 0.7))
    wfac = math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, edge, belly_z - 0.08, belly_z + 0.08))
    blot = ramp_v(nt, nz2, 0.62, 0.70)                                  # dark blotches on the white
    wfac = math_(nt, 'MULTIPLY', wfac, math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', blot, 0.85)))
    mott = mixc(nt, math_(nt, 'MULTIPLY', ramp_v(nt, tnoise(nt, co, 3.0, 6.0), 0.45, 0.75), 0.35), dark, tuple(c * 1.9 for c in dark))
    col = mixc(nt, wfac, mott, light)
    # scars: thin pale rake marks (orca teeth, rope) in patches
    sc = nt.nodes.new('ShaderNodeTexWave'); sc.wave_type = 'BANDS'; sc.bands_direction = 'Z'; sc.inputs['Scale'].default_value = 6.0
    sc.inputs['Distortion'].default_value = 2.0; sc.inputs['Detail'].default_value = 1.0; nt.links.new(co, sc.inputs['Vector'])
    scar = math_(nt, 'MULTIPLY', ramp_v(nt, sc.outputs['Fac'], 0.975, 0.995), ramp_v(nt, tnoise(nt, co, 0.35, 2.0), 0.69, 0.72))
    col = mixc(nt, math_(nt, 'MULTIPLY', scar, 0.7), col, (0.55, 0.56, 0.58))
    nt.links.new(col, b.inputs['Base Color'])
    if pleats:
        wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 1.35
        wv.inputs['Distortion'].default_value = 0.25; wv.inputs['Detail'].default_value = 2.0; nt.links.new(co, wv.inputs['Vector'])
        gro = ramp_v(nt, wv.outputs['Fac'], 0.0, 0.18)                 # thin grooves
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.55; bp.inputs['Distance'].default_value = 0.03
        nt.links.new(math_(nt, 'MULTIPLY', gro, wfac), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
        nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, gro), math_(nt, 'MULTIPLY', wfac, 0.55)), col, tuple(c * 0.45 for c in light)), b.inputs['Base Color'])
    else:
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; bp.inputs['Distance'].default_value = 0.02
        nt.links.new(tnoise(nt, co, 14.0, 6.0), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(math_(nt, 'ADD', rough, math_(nt, 'MULTIPLY', nz2, 0.12)), b.inputs['Roughness'])
    return xray_mix(m)

# ---- proportions (s = 0 snout tip .. 1 fluke notch): half-width, top, belly, mouth line
HB_L = 14.0
HB_TAB = [  # s,   ry,   top,   belly,  mouth
    (0.000, 0.30, 0.02, -0.10, -0.10), (0.020, 0.54, 0.13, -0.16, -0.16), (0.060, 0.76, 0.30, -0.24, -0.24), (0.120, 0.96, 0.50, -0.32, -0.32),
    (0.190, 1.16, 0.72, -0.40, -0.40), (0.250, 1.38, 0.95, -0.95, -0.46), (0.300, 1.56, 1.12, -1.40, -0.48), (0.360, 1.68, 1.24, -1.66, -0.48),
    (0.450, 1.72, 1.28, -1.68, -0.48), (0.550, 1.58, 1.24, -1.50, -0.48), (0.650, 1.22, 1.10, -1.16, -0.48), (0.750, 0.76, 0.92, -0.86, -0.48),
    (0.850, 0.38, 0.70, -0.62, -0.48), (0.930, 0.20, 0.44, -0.42, -0.48), (1.000, 0.08, 0.12, -0.12, -0.48)]
JAW_TAB = [  # s,   ry,   bottom  (the lower jaw and pleated pouch; it runs a little past the snout and tucks into the belly by s 0.58)
    (-0.012, 0.36, -0.20), (0.030, 0.68, -0.48), (0.090, 0.96, -0.82), (0.160, 1.22, -1.10), (0.240, 1.44, -1.40), (0.320, 1.62, -1.64),
    (0.420, 1.72, -1.715), (0.500, 1.62, -1.62), (0.580, 1.32, -1.22)]
HINGE_S = 0.255
def hb_mouth(s): return interp_tab(HB_TAB, s, 4)
def hb_upper_section(s, nseg):
    ry, zt, zb, zm = (interp_tab(HB_TAB, s, k) for k in (1, 2, 3, 4))
    flat = 1.0 - smooth(0.22, 0.33, s)                                   # the head's underside is the palate (flat at the mouth line)
    bot = lerp(zb, zm, flat); zc = (zt + bot) / 2 if flat < 0.5 else lerp(zm, 0.0, smooth(0.25, 0.4, s))
    pts = []
    for k in range(nseg):
        th = 2 * math.pi * k / nseg; c_, s_ = math.cos(th), math.sin(th)
        y_ = ry * (abs(c_) ** 0.82) * (1 if c_ >= 0 else -1)
        if s_ >= 0: z_ = zc + (zt - zc) * (s_ ** 0.9)
        else:
            sb = (-s_) ** (0.9 if flat < 0.5 else 0.25)
            z_ = zc - (zc - bot) * sb
        if s_ < 0 and flat > 0.5: y_ *= 1.0 - 0.04 * (-s_)
        pts.append((y_, z_))
    return pts


# ---- small surface details built right into a mesh's vertex list (so shape keys carry them): domes and barnacles
def add_dome(vs, fs, c, n, r, h, seg=10, rings=4):
    """a knob (tubercle) of radius r rising h out of the surface at c along normal n; returns its face indices"""
    c = Vector(c); n = Vector(n).normalized(); a_ = n.orthogonal().normalized(); b_ = n.cross(a_)
    f0 = len(fs); b0 = len(vs)
    for i in range(rings):
        u = i / rings; rr = r * math.cos(u * math.pi / 2); zz = h * math.sin(u * math.pi / 2) - h * 0.45
        for k in range(seg):
            th = 2 * math.pi * k / seg; vs.append(tuple(c + (a_ * math.cos(th) + b_ * math.sin(th)) * rr + n * zz))
    vs.append(tuple(c + n * (h * 0.55))); top = len(vs) - 1
    for i in range(rings - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((b0 + i * seg + k, b0 + i * seg + k2, b0 + (i + 1) * seg + k2, b0 + (i + 1) * seg + k))
    for k in range(seg): fs.append((b0 + (rings - 1) * seg + k, b0 + (rings - 1) * seg + (k + 1) % seg, top))
    return list(range(f0, len(fs)))
def add_barnacle(vs, fs, c, n, r, h, seg=9):
    """an acorn barnacle: a ridged cone with a dark slot in its top"""
    c = Vector(c); n = Vector(n).normalized(); a_ = n.orthogonal().normalized(); b_ = n.cross(a_)
    f0 = len(fs); b0 = len(vs)
    prof = [(r, -h * 0.4), (r * 0.98, 0.0), (r * 0.62, h * 0.85), (r * 0.42, h), (r * 0.30, h * 0.72)]
    for (rr, zz) in prof:
        for k in range(seg):
            th = 2 * math.pi * k / seg; rk = rr * (1 + 0.12 * math.cos(th * 3 + r * 40))
            vs.append(tuple(c + (a_ * math.cos(th) + b_ * math.sin(th)) * rk + n * zz))
    vs.append(tuple(c + n * h * 0.45)); bot = len(vs) - 1
    for i in range(len(prof) - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((b0 + i * seg + k, b0 + i * seg + k2, b0 + (i + 1) * seg + k2, b0 + (i + 1) * seg + k))
    L_ = len(prof) - 1
    for k in range(seg): fs.append((b0 + L_ * seg + k, b0 + L_ * seg + (k + 1) % seg, bot))
    return list(range(f0, len(fs)))

def build_humpback(name, mbody, mjaw, mmouth, mbaleen, mfin, mbarn, mfringe):
    root = empty(name + '_root')
    L = HB_L; NS, NA = 170, 84
    rr = random.Random(4)
    # ---------------- upper body (skull, back, tail stock), with knobs on the rostrum, a splash guard, blowholes
    ss = [(0.5 * (1 - math.cos(math.pi * i / (NS - 1)))) ** 1.15 for i in range(NS)]
    vs = []; fs = []
    for s in ss:
        for (y_, z_) in hb_upper_section(s, NA): vs.append((-s * L, y_, z_))
    for i in range(NS - 1):
        for k in range(NA): k2 = (k + 1) % NA; fs.append((i * NA + k, i * NA + k2, (i + 1) * NA + k2, (i + 1) * NA + k))
    vs.append((0.02, 0, -0.04)); tip = len(vs) - 1
    for k in range(NA): fs.append((tip, (k + 1) % NA, k))
    tl = len(vs); vs.append((-L - 0.02, 0, 0.0))
    for k in range(NA): fs.append(((NS - 1) * NA + k, (NS - 1) * NA + (k + 1) % NA, tl))
    nbase = len(fs); barn_faces = []
    def top_pt(s, frac):
        ry, zt, zm = interp_tab(HB_TAB, s, 1), interp_tab(HB_TAB, s, 2), interp_tab(HB_TAB, s, 4)
        y_ = ry * frac; zc = zm if s < 0.25 else 0.0
        z_ = zc + (zt - zc) * max(0.0, 1 - abs(frac) ** 2.2) ** 0.5
        return Vector((-s * L, y_, z_)), Vector((0, y_ / max(ry, 1e-3) * 0.8, 1.0)).normalized()
    # tubercles: a row down the middle of the rostrum and scattered rows either side
    for j in range(64):
        s = 0.012 + 0.215 * (j / 63) if j < 18 else 0.012 + 0.21 * rr.random()
        frac = 0.0 if j < 18 else rr.choice((-1, 1)) * rr.uniform(0.25, 0.9)
        p, n = top_pt(s, frac); r_ = 0.045 + 0.03 * rr.random()
        add_dome(vs, fs, p, n, r_, r_ * 0.9)
    # splash guard ridge in front of the blowholes
    for j in range(9):
        p, n = top_pt(0.198, (j - 4) / 14.0); add_dome(vs, fs, p + Vector((0.02 * abs(j - 4), 0, 0)), n, 0.09, 0.06, seg=8, rings=3)
    body = mesh(name + '_body', vs, fs, mbody, root); subsurf(body, 2)
    # ---------------- lower jaw + pleated pouch: real grooves cut into the hull, knobs and barnacles on the chin, floor ridges
    NJ, NB, NF = 120, 176, 30
    js = [lerp(JAW_TAB[0][0], JAW_TAB[-1][0], (i / (NJ - 1)) ** 1.1) for i in range(NJ)]
    jv = []; jf = []; mi = []
    NP = 44
    for s in js:
        ry = interp_tab(JAW_TAB, s, 1); zb = interp_tab(JAW_TAB, s, 2); zm = hb_mouth(max(s, 0.0)) - 0.02 * (1 - smooth(0.0, 0.05, s))
        fade = smooth(0.02, 0.07, s) * (1 - smooth(0.46, 0.56, s))
        ring = []
        for k in range(NB + 1):
            th = math.pi * k / NB; c_, s_ = math.cos(th), math.sin(th)
            y_ = ry * (abs(c_) ** 0.75) * (1 if c_ >= 0 else -1); z_ = zm - (zm - zb) * (s_ ** 0.8)
            vent = smooth(0.25, 0.55, s_)                                  # grooves only on the underside
            g = (0.5 + 0.5 * math.cos(2 * math.pi * NP * th / math.pi)) ** 8
            zc = (zm + zb) / 2; rad = Vector((0, y_, z_ - zc)); rl = rad.length or 1.0
            d = 0.038 * g * vent * fade
            ring.append((y_ - y_ / rl * d, z_ - (z_ - zc) / rl * d))
        dip = 0.28 * smooth(0.0, 0.12, s) * (1 - smooth(0.38, 0.55, s))
        for k in range(1, NF):
            u = k / NF; y_ = -ry * 0.74 * math.cos(math.pi * u)
            ridge = 0.015 * math.sin(u * math.pi * 9) * smooth(0.04, 0.12, s)        # the floor of the mouth: soft ridges
            ring.append((y_, zm - 0.04 - 0.05 * (1 - smooth(0.0, 0.05, s)) - dip * math.sin(math.pi * u) ** 1.5 + ridge))
        for (y_, z_) in ring: jv.append((-s * L, y_, z_))
    NR = NB + 1 + NF - 1
    for i in range(NJ - 1):
        for k in range(NR):
            k2 = (k + 1) % NR; jf.append((i * NR + k, i * NR + k2, (i + 1) * NR + k2, (i + 1) * NR + k)); mi.append(1 if (NB < k < NR - 1 and js[i] > 0.045) else 0)
    jf.append(tuple(range(NR))[::-1]); mi.append(0); jf.append(tuple((NJ - 1) * NR + k for k in range(NR))); mi.append(0)
    def jaw_pt(s, th):
        ry = interp_tab(JAW_TAB, s, 1); zb = interp_tab(JAW_TAB, s, 2); zm = hb_mouth(max(s, 0.0))
        c_, s_ = math.cos(th), math.sin(th); y_ = ry * (abs(c_) ** 0.75) * (1 if c_ >= 0 else -1); z_ = zm - (zm - zb) * (s_ ** 0.8)
        zc = (zm + zb) / 2; return Vector((-s * L, y_, z_)), Vector((0, y_, z_ - zc)).normalized()
    for j in range(40):                                                    # knobs along the lower lip and on the chin
        s = 0.0 + 0.07 * rr.random(); th = rr.choice((rr.uniform(0.08, 0.5), rr.uniform(2.64, 3.06)))
        p, n = jaw_pt(s, th); r_ = 0.04 + 0.025 * rr.random(); f_ = add_dome(jv, jf, p, n, r_, r_ * 0.9); mi += [0] * len(f_)
    for j in range(130):                                                   # barnacle clusters on the chin
        cl = j // 13; cs_ = 0.002 + 0.035 * h1(cl * 3.1); ct_ = 1.57 + 0.9 * (h1(cl * 7.7) - 0.5) * 2.0
        s = max(-0.01, cs_ + 0.012 * (rr.random() - 0.5)); th = clamp(ct_ + 0.12 * (rr.random() - 0.5), 0.1, math.pi - 0.1)
        p, n = jaw_pt(s, th); r_ = 0.018 + 0.026 * rr.random(); f_ = add_barnacle(jv, jf, p, n, r_, r_ * 1.1); mi += [2] * len(f_)
    jaw = mesh(name + '_jaw', jv, jf, mjaw, root); jaw.data.materials.append(mmouth); jaw.data.materials.append(mbarn)
    for p_, m_ in zip(jaw.data.polygons, mi): p_.material_index = m_
    subsurf(jaw, 1)
    hx = -HINGE_S * L; hz = hb_mouth(HINGE_S)
    jaw.shape_key_add(name='Basis'); ko = jaw.shape_key_add(name='open'); ke = jaw.shape_key_add(name='engulf')
    ang = R(58)
    for i, v in enumerate(jaw.data.vertices):
        x_, y_, z_ = v.co; s = -x_ / L
        w = 1.0 - smooth(0.24, 0.50, s); a_ = ang * w; dx, dz = x_ - hx, z_ - hz
        ko.data[i].co = Vector((hx + dx * math.cos(a_) + dz * math.sin(a_), y_ * (1 + 0.05 * w), hz - dx * math.sin(a_) + dz * math.cos(a_)))
        bal = smooth(0.06, 0.14, s) * (1 - smooth(0.42, 0.58, s))
        low = clamp((hb_mouth(max(s, 0)) - z_) / 1.2, 0, 1)
        edge = min(1.0, abs(y_) / max(interp_tab(JAW_TAB, s, 1), 1e-3)) ** 4
        ke.data[i].co = Vector((x_, y_ * (1 + 0.32 * bal * low), z_ - bal * (0.95 * (1 - edge) + 0.6 * low ** 1.2)))
    # ---------------- baleen: ~300 plates a side, each curved, dark on the outside and fading to a cream fringe of bristles inside
    bv = []; bf = []; fv = []; ff = []
    NBAL = 300
    for side in (1, -1):
        for j in range(NBAL):
            s = 0.012 + 0.245 * j / (NBAL - 1); x_ = -s * L; ry = interp_tab(HB_TAB, s, 1) * 0.80; zm = hb_mouth(s)
            ln = 0.16 + 0.60 * math.sin(math.pi * min(1.0, (s - 0.01) / 0.25)) ** 0.7; wd = 0.10 + 0.12 * smooth(0.0, 0.2, s)
            ryj = interp_tab(JAW_TAB, s, 1); zbj = interp_tab(JAW_TAB, s, 2); cth = min(1.0, (ry / max(ryj, 1e-3)) ** (1 / 0.75))
            room = (zm - zbj) * (math.sqrt(max(0.0, 1 - cth * cth)) ** 0.8) - 0.06        # stay inside the shut lower jaw
            ln = max(0.05, min(ln, room))
            p0 = len(bv); bend = 0.03 * math.sin(j * 0.7)
            for (u, v) in ((0, 0), (1, 0), (1, 0.5), (0.95, 1), (0, 1)):
                bv.append((x_ + bend * v, side * (ry - wd * u * (1 - 0.45 * v)), zm + 0.02 - ln * v * (1 - 0.18 * u)))
            q = [p0, p0 + 1, p0 + 2, p0 + 3, p0 + 4]; bf.append(tuple(q) if side > 0 else tuple(q[::-1]))
            # the fringe: fine bristles hanging off the inner edge
            for b in range(4):
                v0 = 0.15 + 0.2 * b; yb = side * (ry - wd * (1 - 0.45 * v0)); zb_ = zm + 0.02 - ln * v0 * 0.82
                q0 = len(fv); fv += [(x_, yb, zb_), (x_ + 0.012, yb, zb_), (x_ + 0.012, yb - side * 0.10, zb_ - 0.10), (x_, yb - side * 0.10, zb_ - 0.10)]
                ff.append((q0, q0 + 1, q0 + 2, q0 + 3))
    baleen = mesh(name + '_baleen', bv, bf, mbaleen, root, smooth_=False)
    sol = baleen.modifiers.new('th', 'SOLIDIFY'); sol.thickness = 0.006
    fringe = mesh(name + '_fringe', fv, ff, mfringe, root, smooth_=False)
    # ---------------- eyes with lids, blowholes
    eyes = []
    EYEM = mat('whale_eye', (0.035, 0.018, 0.01), 0.05, coat=1.0)
    for side in (1, -1):
        s = 0.262; y_ = side * interp_tab(HB_TAB, s, 1) * 0.93; z_ = hb_mouth(s) + 0.2
        e = prim('uv_sphere', f'{name}_eye{side}', EYEM, root, loc=(-s * L, y_, z_), radius=0.07, segments=20, ring_count=12)
        for k_, (dz, sc) in enumerate(((0.045, (1.25, 0.55, 0.55)), (-0.045, (1.2, 0.5, 0.45)))):
            lid = prim('uv_sphere', f'{name}_lid{side}{k_}', mbody, root, loc=(-s * L, y_ - side * 0.025, z_ + dz), radius=0.12, segments=18, ring_count=10); lid.scale = sc
            eyes.append(lid)
        eyes.append(e)
    for side in (1, -1):
        s = 0.212; z_ = interp_tab(HB_TAB, s, 2)
        bh = prim('uv_sphere', f'{name}_blow{side}', mat('blowhole', (0.005, 0.005, 0.006), 0.4), root, loc=(-s * L, side * 0.09, z_ + 0.004), radius=0.13, segments=16, ring_count=8)
        bh.scale = (1.0, 0.22, 0.10); bh.rotation_euler = (0, 0, side * R(14)); eyes.append(bh)
    # ---------------- dorsal fin: a small hooked fin on a hump
    s0 = 0.64; zt0 = interp_tab(HB_TAB, s0, 2); dvs = []; dfs = []
    for i in range(12):
        u = i / 11; x0 = -s0 * L + 0.7 - 1.5 * u; h_ = 0.48 * math.sin(math.pi * u ** 0.8) ** 1.4; th_ = 0.13 * (1 - u * 0.6)
        for (yy, zz) in ((-th_, -0.1), (0, h_), (th_, -0.1), (0, -0.3)): dvs.append((x0 - 0.18 * (zz / 0.5) ** 2 * (zz > 0), yy, zt0 + zz))
    for i in range(11):
        for k in range(4): k2 = (k + 1) % 4; dfs.append((i * 4 + k, i * 4 + k2, (i + 1) * 4 + k2, (i + 1) * 4 + k))
    dfs.append((0, 1, 2, 3)[::-1]); dfs.append(tuple(44 + k for k in range(4)))
    dorsal = mesh(name + '_dorsal', dvs, dfs, mbody, root); subsurf(dorsal, 2)
    # ---------------- flippers: a third of the body long, a hydrofoil section, a row of knobs on the leading edge, barnacles near the tip
    fins = {}
    for side in (1, -1):
        piv = empty(f'{name}_finpiv{side}', root, loc=(-0.29 * L, side * 1.36, -1.0))
        n = 64; fv_ = []; ff_ = []; sec = 12
        for i in range(n):
            u = i / (n - 1); span = 4.6 * u
            knob = sum(math.exp(-((u - kk / 11.0) / 0.018) ** 2) for kk in range(2, 11)) * 0.07 * smooth(0.1, 0.25, u)
            chord = lerp(1.30, 0.30, u ** 1.1); th = lerp(0.17, 0.04, u)
            for k in range(sec):
                a_ = 2 * math.pi * k / sec; cx = -0.5 * (1 - math.cos(a_)); cz = th * 0.5 * math.sin(a_) * (1 - 0.6 * (-cx)) * 1.6
                lead = knob if k in (0, 1, sec - 1) else 0.0
                fv_.append((cx * chord + 0.25 * chord + lead, side * span, cz))
        for i in range(n - 1):
            for k in range(sec):
                k2 = (k + 1) % sec; q = (i * sec + k, i * sec + k2, (i + 1) * sec + k2, (i + 1) * sec + k); ff_.append(q if side > 0 else q[::-1])
        cap = tuple((n - 1) * sec + k for k in range(sec)); ff_.append(cap if side > 0 else cap[::-1])
        fmi = [0] * len(ff_)
        for j in range(26):
            u = rr.uniform(0.55, 0.98); chord = lerp(1.30, 0.30, u ** 1.1)
            p = Vector((0.25 * chord + 0.01, side * 4.6 * u, rr.uniform(-0.02, 0.02))); n_ = Vector((1, 0, rr.uniform(-0.6, 0.6))).normalized()
            r_ = 0.014 + 0.018 * rr.random(); f_ = add_barnacle(fv_, ff_, p, n_, r_, r_ * 1.1); fmi += [1] * len(f_)
        fo = mesh(f'{name}_fin{side}', fv_, ff_, mfin, piv); fo.data.materials.append(mbarn)
        for p_, m_ in zip(fo.data.polygons, fmi): p_.material_index = m_
        subsurf(fo, 1)
        fo.rotation_euler = (R(-16) * side, R(22), R(-52) * side)
        fins[side] = piv
    # ---------------- flukes: swept wings, a deep notch, a ragged trailing edge
    fpiv = empty(name + '_flukepiv', root, loc=(-L + 0.15, 0, 0.0))
    n = 56; fv_ = []; ff_ = []; sec = 10
    for side in (1, -1):
        b0 = len(fv_)
        for i in range(n):
            u = i / (n - 1); span = 2.3 * u; sweep = -0.6 * u ** 1.5; chord = lerp(1.05, 0.28, u ** 1.2)
            ser = (0.045 * abs(math.sin(u * 2 * math.pi * 11)) + 0.02 * h1(i * 1.7)) * smooth(0.04, 0.12, u); th = lerp(0.15, 0.03, u)
            notch = 0.22 * (1 - smooth(0.0, 0.08, u))
            for k in range(sec):
                a_ = 2 * math.pi * k / sec; cx = -0.5 * (1 - math.cos(a_)); cz = th * 0.5 * math.sin(a_) * 1.5
                fv_.append((sweep + cx * chord + 0.25 - (ser + notch) * (-cx) ** 3, side * (0.04 + span), cz))
        for i in range(n - 1):
            for k in range(sec):
                k2 = (k + 1) % sec; q = (b0 + i * sec + k, b0 + i * sec + k2, b0 + (i + 1) * sec + k2, b0 + (i + 1) * sec + k); ff_.append(q if side > 0 else q[::-1])
        cap = tuple(b0 + (n - 1) * sec + k for k in range(sec)); ff_.append(cap if side > 0 else cap[::-1])
    for k in range(sec):
        k2 = (k + 1) % sec; ff_.append((k2, k, n * sec + k, n * sec + k2))
    flukes = mesh(name + '_flukes', fv_, ff_, mfin, fpiv); subsurf(flukes, 1)
    # body shape keys: the tail bends up / down (the flukes follow)
    body.shape_key_add(name='Basis'); ku = body.shape_key_add(name='tail_up')
    for i, v in enumerate(body.data.vertices):
        s = -v.co.x / L; ku.data[i].co = v.co + Vector((0, 0, tail_bend(s)))
    return dict(root=root, body=body, jaw=jaw, baleen=baleen, fringe=fringe, fins=fins, fpiv=fpiv, flukes=flukes, eyes=eyes, dorsal=dorsal, L=L)

def tail_bend(s): return 1.1 * smooth(0.42, 1.0, s) ** 1.8          # how far the body lifts at s for tail_up = 1 (m)
def tail_slope(s, ds=0.01): return (tail_bend(min(s + ds, 1)) - tail_bend(s - ds)) / (2 * ds * HB_L)

HB_DARK = (0.030, 0.034, 0.040); HB_WHITE = (0.80, 0.82, 0.84)
HBM = whale_skin('hb_skin', HB_DARK, HB_WHITE, -1.05)
HBJ = whale_skin('hb_jaw', HB_DARK, HB_WHITE, -0.85, pleats=True)
HBMOUTH = mat('hb_mouth', (0.30, 0.17, 0.17), 0.6, coat=0.3); noisy(HBMOUTH, 6.0, 0.35, 0.1); xray_mix(HBMOUTH)
HBBAL = mat('hb_baleen', (0.035, 0.03, 0.028), 0.75); nt = HBBAL.node_tree
nt.links.new(mixc(nt, ramp_v(nt, sepz(nt, coord(nt, 'Generated')).outputs['Z'], 0.0, 1.0), (0.30, 0.26, 0.20), (0.025, 0.022, 0.02)), nt.nodes['Principled BSDF'].inputs['Base Color'])
xray_mix(HBBAL)
HBFRINGE = mat('hb_fringe', (0.62, 0.55, 0.42), 0.9, trans=0.3, sheen=0.6); xray_mix(HBFRINGE)
HBBARN = mat('hb_barnacle', (0.72, 0.70, 0.64), 0.85); noisy(HBBARN, 60.0, 0.45, 0.1); xray_mix(HBBARN)
HBFIN = whale_skin('hb_fin', (0.06, 0.065, 0.07), (0.86, 0.87, 0.88), 0.03)
HB = build_humpback('hb', HBM, HBJ, HBMOUTH, HBBAL, HBFIN, HBBARN, HBFRINGE)

def humpback_set(loc, yaw=0.0, pitch=0.0, roll=0.0, open_=0.0, engulf=0.0, tail=0.0, fin=0.0, xr=0.0, scale=1.0):
    r_ = HB['root']; r_.location = loc; r_.rotation_mode = 'XYZ'; r_.rotation_euler = (roll, -pitch, yaw); r_.scale = (scale,) * 3
    HB['jaw'].data.shape_keys.key_blocks['open'].value = open_
    HB['jaw'].data.shape_keys.key_blocks['engulf'].value = engulf
    HB['body'].data.shape_keys.key_blocks['tail_up'].slider_min = -1.0
    HB['body'].data.shape_keys.key_blocks['tail_up'].value = tail
    tb = tail_bend(1.0) * tail; ang = math.atan(tail_slope(0.985) * tail)
    HB['fpiv'].location = (-HB_L + 0.15, 0, tb); HB['fpiv'].rotation_euler = (0, -ang * 1.4, 0)
    for side, piv in HB['fins'].items(): piv.rotation_euler = (side * R(14) * fin, R(6) * fin, side * R(8) * fin)
    for o in [c for c in HB['root'].children_recursive if c.type == 'MESH']:
        o['xr'] = xr
    for o in [HB['baleen'], HB['fringe']]: o.hide_render = xr > 0.2 or open_ < 0.04
    for o in HB['eyes']: o.hide_render = xr > 0.2

# ================================================================ the sperm whale (about 15 m): a huge square head a third of its length, wrinkled
# dark skin, a thin under-slung lower jaw lined with teeth that drops open, and a throat wide enough to take a giant squid whole (shown in x-ray).
# Same local frame as the humpback: snout at x = 0 facing +x.
SW_L = 15.0
SW_TAB = [  # s,   ry,   top,   bottom   (the head: a tall square block a third of the body; the body behind it lower and narrower)
    (0.000, 0.95, 1.55, -1.20), (0.012, 1.10, 1.85, -1.38), (0.050, 1.20, 2.00, -1.48), (0.180, 1.25, 2.05, -1.52), (0.300, 1.28, 1.95, -1.55),
    (0.360, 1.26, 1.60, -1.52), (0.440, 1.24, 1.32, -1.45), (0.560, 1.10, 1.20, -1.30), (0.660, 0.88, 1.08, -1.06), (0.760, 0.60, 0.92, -0.84),
    (0.860, 0.35, 0.68, -0.58), (0.940, 0.20, 0.42, -0.37), (1.000, 0.08, 0.14, -0.14)]
SW_HINGE = 0.30
def build_sperm(name, mskin, mmouth, mteeth, mthroat):
    root = empty(name + '_root'); L = SW_L; NS, NA = 100, 56
    ss = [(0.5 * (1 - math.cos(math.pi * i / (NS - 1)))) ** 1.1 for i in range(NS)]
    vs = []; fs = []
    for s in ss:
        ry, zt, zb = (interp_tab(SW_TAB, s, k) for k in (1, 2, 3)); zc = (zt + zb) / 2
        ex = lerp(0.22, 0.85, smooth(0.28, 0.45, s))                    # boxy head, round body
        bump = 0.05 * math.sin(s * 70) * smooth(0.5, 0.7, s) * (1 - smooth(0.85, 0.95, s))   # the knuckles on the back
        for k in range(NA):
            th = 2 * math.pi * k / NA; c_, s_ = math.cos(th), math.sin(th)
            y_ = ry * (abs(c_) ** ex) * (1 if c_ >= 0 else -1)
            z_ = zc + (zt - zc + (bump if s_ > 0.9 else 0)) * (abs(s_) ** ex) * (1 if s_ >= 0 else -1) if s_ >= 0 else zc - (zc - zb) * (abs(s_) ** ex)
            vs.append((-s * L, y_, z_))
    for i in range(NS - 1):
        for k in range(NA): k2 = (k + 1) % NA; fs.append((i * NA + k, i * NA + k2, (i + 1) * NA + k2, (i + 1) * NA + k))
    vs.append((0.03, 0, 0.0)); tip = len(vs) - 1
    for k in range(NA): fs.append((tip, (k + 1) % NA, k))
    tl = len(vs); vs.append((-L - 0.02, 0, 0.0))
    for k in range(NA): fs.append(((NS - 1) * NA + k, (NS - 1) * NA + (k + 1) % NA, tl))
    body = mesh(name + '_body', vs, fs, mskin, root); subsurf(body, 1)
    # the dorsal hump
    s0 = 0.62; zt0 = interp_tab(SW_TAB, s0, 2)
    hump = tube(name + '_hump', [(-s0 * L + 0.6, 0, zt0 - 0.1), (-s0 * L, 0, zt0 + 0.25), (-s0 * L - 0.7, 0, zt0 - 0.05)], lambda u: 0.3 * math.sin(math.pi * min(max(u, 0.05), 0.95)), mskin, root, seg=12)
    # lower jaw: a narrow rod under the head, teeth along its top, on a hinge
    jpiv = empty(name + '_jawpiv', root, loc=(-SW_HINGE * L, 0, -1.30))
    n = 40; jv = []; jf = []
    for i in range(n):
        u = i / (n - 1); x_ = SW_HINGE * L - u * (SW_HINGE * L - 0.45); w = lerp(0.42, 0.20, u); h_ = lerp(0.36, 0.20, u)
        for (yy, zz) in ((-w, 0.0), (-w * 0.9, -h_ * 0.7), (0.0, -h_), (w * 0.9, -h_ * 0.7), (w, 0.0), (0.0, 0.06)):
            jv.append((x_, yy, zz))
    for i in range(n - 1):
        for k in range(6): k2 = (k + 1) % 6; jf.append((i * 6 + k, i * 6 + k2, (i + 1) * 6 + k2, (i + 1) * 6 + k))
    jf.append(tuple(range(6))[::-1]); jf.append(tuple((n - 1) * 6 + k for k in range(6)))
    jaw = mesh(name + '_jaw', jv, jf, mskin, jpiv); jaw.location = (0, 0, 0); subsurf(jaw, 1)
    teeth = []
    for side in (1, -1):
        for j in range(22):
            u = 0.06 + 0.88 * j / 21; x_ = SW_HINGE * L - u * (SW_HINGE * L - 0.45); w = lerp(0.42, 0.20, u) * 0.7
            tt = prim('cone', f'{name}_tooth{side}_{j}', mteeth, jpiv, loc=(x_, side * w, 0.11), radius1=0.045, radius2=0.004, depth=0.18, vertices=10)
            tt.rotation_euler = (side * R(-10), 0, 0); teeth.append(tt)
    # the upper mouth: a pale groove under the head where the jaw closes into
    gr = box(name + '_groove', (SW_HINGE * L - 0.5, 0.55, 0.06), (-(SW_HINGE * L) / 2 - 0.2, 0, -1.30), mmouth, bv=0.02, parent=root)
    # the throat ring (x-ray only): big enough for a person
    thr = prim('cylinder', name + '_throat', mthroat, root, loc=(-SW_HINGE * L - 0.5, 0, -0.6), radius=0.55, depth=0.08, vertices=40)
    thr.rotation_euler = (0, R(90), 0); thr.hide_render = True
    # flippers (small) and flukes
    fins = []
    for side in (1, -1):
        piv = empty(f'{name}_fpiv{side}', root, loc=(-0.36 * L, side * 1.2, -1.0))
        fo = tube(f'{name}_flip{side}', [(0, 0, 0), (-0.4, side * 0.6, -0.25), (-0.9, side * 1.0, -0.45)], lambda u: 0.32 * (1 - 0.75 * u), mskin, piv, seg=10)
        fo.scale = (1, 1, 0.35); fins.append(piv)
    fpiv = empty(name + '_flukepiv', root, loc=(-L + 0.1, 0, 0))
    fv = []; ff = []; n = 24
    for side in (1, -1):
        b0 = len(fv)
        for i in range(n):
            u = i / (n - 1); span = 2.2 * u; chord = lerp(1.1, 0.25, u ** 1.3); th = lerp(0.14, 0.03, u)
            for (cx, cz) in [(0.0, 0.0), (-0.3, th * 0.5), (-1.0, 0.0), (-0.3, -th * 0.5)]:
                fv.append((-0.5 * u ** 1.4 + cx * chord + 0.25, side * (0.05 + span), cz))
        for i in range(n - 1):
            for k in range(4):
                k2 = (k + 1) % 4; q_ = (b0 + i * 4 + k, b0 + i * 4 + k2, b0 + (i + 1) * 4 + k2, b0 + (i + 1) * 4 + k); ff.append(q_ if side > 0 else q_[::-1])
    flukes = mesh(name + '_flukes', fv, ff, mskin, fpiv); subsurf(flukes, 1)
    # eye
    eyes = [prim('uv_sphere', f'{name}_eye{s_}', mat('sw_eye', (0.01, 0.01, 0.01), 0.05, coat=1.0), root, loc=(-0.36 * L, s_ * 1.2, -0.95), radius=0.06, segments=12, ring_count=8) for s_ in (1, -1)]
    body.shape_key_add(name='Basis'); ku = body.shape_key_add(name='tail_up')
    for i, v in enumerate(body.data.vertices): ku.data[i].co = v.co + Vector((0, 0, tail_bend(-v.co.x / L)))
    return dict(root=root, body=body, jaw=jaw, jpiv=jpiv, teeth=teeth, throat=thr, fins=fins, fpiv=fpiv, flukes=flukes, L=L)

SWSKIN = mat('sw_skin', (0.075, 0.068, 0.064), 0.45, coat=0.2); nt = SWSKIN.node_tree; b_ = nt.nodes['Principled BSDF']; co = coord(nt, 'Object')
wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 3.0; wv.inputs['Distortion'].default_value = 7.0
wv.inputs['Detail'].default_value = 4.0; nt.links.new(co, wv.inputs['Vector'])
bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.45; bp.inputs['Distance'].default_value = 0.04
nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b_.inputs['Normal'])
nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', ramp_v(nt, tnoise(nt, co, 1.2, 6.0), 0.4, 0.7), 0.5), (0.075, 0.068, 0.064), (0.16, 0.15, 0.14)), b_.inputs['Base Color'])
xray_mix(SWSKIN, (0.45, 0.8, 1.0))
SWMOUTH = mat('sw_mouth', (0.78, 0.74, 0.70), 0.5); xray_mix(SWMOUTH)
SWTEETH = mat('sw_teeth', (0.92, 0.9, 0.84), 0.3, coat=0.5); xray_mix(SWTEETH)
THROATM = emis_mix('throat_glow', (1.0, 0.85, 0.3), 6.0, 'alpha')
SW = build_sperm('sw', SWSKIN, SWMOUTH, SWTEETH, THROATM)

def sperm_set(loc, yaw=0.0, pitch=0.0, roll=0.0, jaw=0.0, tail=0.0, xr=0.0, throat=0.0):
    r_ = SW['root']; r_.location = loc; r_.rotation_mode = 'XYZ'; r_.rotation_euler = (roll, -pitch, yaw)
    SW['jpiv'].rotation_euler = (0, R(62) * jaw, 0)
    SW['body'].data.shape_keys.key_blocks['tail_up'].slider_min = -1.0; SW['body'].data.shape_keys.key_blocks['tail_up'].value = tail
    tb = tail_bend(1.0) * tail; ang = math.atan(tail_slope(0.985) * tail)
    SW['fpiv'].location = (-SW_L + 0.1, 0, tb); SW['fpiv'].rotation_euler = (0, -ang * 1.4, 0)
    for o in SW['root'].children_recursive:
        if o.type == 'MESH': o['xr'] = xr
    SW['throat'].hide_render = throat < 0.03; SW['throat']['alpha'] = throat
def sperm_show(on):
    for o in [SW['root']] + list(SW['root'].children_recursive):
        if o.type == 'MESH': o.hide_render = not on or (o is SW['throat'] and o.hide_render)

# ================================================================ the giant squid (about 10 m with its feeding tentacles): a red mantle with fins,
# big eyes, eight arms and two long tentacles that curl
SQM = mat('squid', (0.55, 0.12, 0.08), 0.35, coat=0.6, sheen=0.3); noisy(SQM, 8.0, 0.35, 0.1); xray_mix(SQM, (1.0, 0.6, 0.4))
SQ = empty('squid_root')
SQ_MANTLE = lathe('squid_mantle', [(0.01, 2.4), (0.18, 2.3), (0.32, 2.0), (0.38, 1.4), (0.36, 0.6), (0.30, 0.15), (0.26, 0.0)], 24, SQM, SQ)
SQ_MANTLE.rotation_euler = (0, R(90), 0)                                  # mantle points +x
for s_ in (1, -1):
    fn = prim('uv_sphere', f'squid_fin{s_}', SQM, SQ, loc=(2.05, s_ * 0.28, 0), radius=0.35, segments=12, ring_count=8); fn.scale = (1.0, 0.9, 0.12)
SQ_HEAD = prim('uv_sphere', 'squid_head', SQM, SQ, loc=(-0.15, 0, 0), radius=0.3, segments=16, ring_count=10); SQ_HEAD.scale = (1.0, 1.05, 0.95)
for s_ in (1, -1):
    prim('uv_sphere', f'squid_eye{s_}', mat('squid_eye', (0.02, 0.02, 0.03), 0.05, coat=1.0), SQ, loc=(-0.15, s_ * 0.26, 0.05), radius=0.12, segments=14, ring_count=8)
SQ_ARMS = []
for j in range(10):
    a_ = 2 * math.pi * j / 10; ln = 6.0 if j in (2, 7) else 2.0
    SQ_ARMS.append((tube(f'squid_arm{j}', [(-0.3 - ln * k / 15, 0.15 * math.cos(a_), 0.15 * math.sin(a_)) for k in range(16)], lambda u: 0.07 * (1 - 0.85 * u) + 0.008, SQM, SQ, seg=8), a_, ln))
for o, a_, ln in SQ_ARMS: o['a'] = a_; o['ln'] = ln
def squid_set(loc, rot, t, curl=1.0, xr=0.0, scale=1.0):
    SQ.location = loc; SQ.rotation_mode = 'XYZ'; SQ.rotation_euler = rot; SQ.scale = (scale,) * 3
    for o, a_, ln in SQ_ARMS:
        co = []; n = 16
        for k in range(n):
            u = k / (n - 1); r0 = 0.15 + 0.25 * u * curl
            ang = a_ + 0.6 * curl * u * math.sin(t * 2.2 + a_ * 3)
            p = Vector((-0.3 - ln * u * (1 - 0.25 * curl * u), r0 * math.cos(ang), r0 * math.sin(ang)))
            p += Vector((0, 0.25 * u * u * math.sin(t * 3.1 + a_ * 2 + u * 4), 0.25 * u * u * math.cos(t * 2.7 + a_ * 2 + u * 4))) * curl
            co.append(p)
        rebuild_tube(o, co, lambda u: 0.07 * (1 - 0.85 * u) + 0.008, 8)
    for o in [SQ] + list(SQ.children_recursive):
        if o.type == 'MESH': o['xr'] = xr
def squid_show(on):
    for o in SQ.children_recursive:
        if o.type == 'MESH': o.hide_render = not on
def rebuild_tube(o, pts, r, seg):
    pts = [Vector(p) for p in pts]; n = len(pts); T0 = (pts[1] - pts[0]).normalized()
    up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized(); co = []
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        rr = r(i / (n - 1))
        for k in range(seg): co.extend(pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * rr)
    o.data.vertices.foreach_set('co', co); o.data.update()
# ================================================================ the diver: the house MakeHuman man in a full 7 mm wetsuit and hood (no face shows: a
# twin-lens mask and regulator cover it), a BC vest with straps, pockets and an inflator hose, a steel tank with a first stage, an octopus and a
# pressure gauge, a weight belt, a dive knife on his calf, ribbed fins, and a mesh catch bag with lobsters in it. IK arms, a flutter kick.
GLOW_D = (1.0, 0.62, 0.22)
def wetsuit_mat():
    m = mat('neoprene', (0.016, 0.017, 0.02), 0.55, sheen=0.25); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    g = coord(nt, 'Generated'); sx = sepz(nt, g); ob = sepz(nt, coord(nt, 'Object'))
    # blue shoulder/chest panel, rubber knee pads, light stitch seams at the waist, the sides and round the arms
    panel = math_(nt, 'MULTIPLY', ramp_v(nt, sx.outputs['Z'], 0.80, 0.81), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, sx.outputs['Z'], 0.865, 0.875)))
    knee = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', ramp_v(nt, sx.outputs['Z'], 0.245, 0.255), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, sx.outputs['Z'], 0.315, 0.325))),
                 ramp_v(nt, math_(nt, 'MULTIPLY', ob.outputs['Y'], -1.0), 0.0, 0.03))
    seam = math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', ramp_v(nt, sx.outputs['Z'], 0.585, 0.587), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, sx.outputs['Z'], 0.589, 0.591))),
                 math_(nt, 'MULTIPLY', ramp_v(nt, math_(nt, 'ABSOLUTE', ob.outputs['X']), 0.150, 0.152), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, math_(nt, 'ABSOLUTE', ob.outputs['X']), 0.154, 0.156))))
    col = mixc(nt, panel, (0.016, 0.017, 0.02), (0.02, 0.09, 0.22))
    col = mixc(nt, knee, col, (0.05, 0.05, 0.05)); col = mixc(nt, math_(nt, 'MULTIPLY', seam, 0.8), col, (0.22, 0.22, 0.24))
    nt.links.new(col, b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.004
    tx = nt.nodes.new('ShaderNodeTexNoise'); tx.inputs['Scale'].default_value = 900.0; nt.links.new(coord(nt, 'Object'), tx.inputs['Vector'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', tx.outputs['Fac'], 0.3), math_(nt, 'MULTIPLY', knee, math_(nt, 'MULTIPLY', ramp_v(nt, tnoise(nt, coord(nt, 'Object'), 260.0, 1.0), 0.4, 0.6), 1.0))), bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return xray_mix(m, GLOW_D)
NEO = wetsuit_mat()
NEO_PANEL = mat('neo_panel', (0.03, 0.10, 0.24), 0.5, sheen=0.2); xray_mix(NEO_PANEL, GLOW_D)
BCDM = mat('bcd', (0.025, 0.026, 0.03), 0.6, sheen=0.3); noisy(BCDM, 220.0, 0.3, 0.1); xray_mix(BCDM, GLOW_D)
WEBM = mat('webbing', (0.02, 0.02, 0.022), 0.8, sheen=0.4); noisy(WEBM, 400.0, 0.35, 0.1); xray_mix(WEBM, GLOW_D)
TANKM = mat('tank', (0.32, 0.34, 0.36), 0.35, metal=0.6, coat=0.5); noisy(TANKM, 30.0, 0.15, 0.1); xray_mix(TANKM, GLOW_D)
TANKBAND = mat('tankband', (0.85, 0.62, 0.05), 0.35, coat=0.5); xray_mix(TANKBAND, GLOW_D)
FINM = mat('fins', (0.02, 0.02, 0.025), 0.4, coat=0.3); xray_mix(FINM, GLOW_D)
FINB = mat('fin_blade', (0.04, 0.22, 0.58), 0.3, coat=0.5, trans=0.2); xray_mix(FINB, GLOW_D)
MASKG = mat('mask_glass', (0.01, 0.015, 0.02), 0.01, coat=1.0); xray_mix(MASKG, GLOW_D)
SKIRT = mat('mask_skirt', (0.02, 0.02, 0.025), 0.35, trans=0.3, coat=0.4); xray_mix(SKIRT, GLOW_D)
METAL = mat('metal', (0.75, 0.75, 0.78), 0.18, metal=1.0); xray_mix(METAL, GLOW_D)
OCTOM = mat('octo', (0.95, 0.78, 0.05), 0.35, coat=0.4); xray_mix(OCTOM, GLOW_D)
GAUGEF = mat('gauge_face', (0.92, 0.92, 0.88), 0.2, coat=1.0); xray_mix(GAUGEF, GLOW_D)
LEADM = mat('lead', (0.30, 0.31, 0.32), 0.55, metal=0.4); xray_mix(LEADM, GLOW_D)
BAGM = mat('bag', (0.95, 0.78, 0.1), 0.6); xray_mix(BAGM, GLOW_D)
LOBM = mat('lobster', (0.16, 0.10, 0.05), 0.35, coat=0.6); noisy(LOBM, 25.0, 0.4, 0.1); xray_mix(LOBM, GLOW_D)
KNIFEM = mat('knife', (0.75, 0.76, 0.78), 0.15, metal=1.0); xray_mix(KNIFEM, GLOW_D)
BONEM = emis('bones', (0.85, 0.95, 1.0), 4.0)
BRUISEM = emis_mix('bruise', (0.55, 0.12, 0.65), 1.8, 'alpha')

def bone_parent(o, rig, bone, world_pos, world_rot=None):
    """parent to a bone, keeping the rotation/scale the object already has, placed at world_pos (rest pose)"""
    bpy.context.view_layer.update()
    RS = o.matrix_world.to_3x3() if world_rot is None else world_rot
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = rig.matrix_world @ Matrix.Translation(Vector(world_pos)) @ RS.to_4x4()

def make_vest(name, body, rig, col):
    """the BC vest: the body's torso faces (chest, back, sides) pushed out ~2.5 cm, keeping his skin weights so it bends with him"""
    me_b = body.data; vg = {g.index: g.name for g in body.vertex_groups}
    def wmap(v): return {vg[g.group]: g.weight for g in v.groups if g.group in vg}
    keep = set()
    for v in me_b.vertices:
        w = wmap(v); z_ = v.co.z
        arm = sum(w.get(k, 0) for k in ('upperarm01.L', 'upperarm01.R', 'upperarm02.L', 'upperarm02.R', 'clavicle.L', 'clavicle.R'))
        if 0.98 < z_ < 1.40 and abs(v.co.x) < 0.24 and arm < 0.25 and not (v.co.y < -0.05 and abs(v.co.x) < 0.07 and z_ > 1.12): keep.add(v.index)
    ms = [i for i, m_ in enumerate(me_b.materials) if m_ and 'body' in m_.name] or [0]
    faces = [p_ for p_ in me_b.polygons if all(i in keep for i in p_.vertices)]
    used = sorted({i for p_ in faces for i in p_.vertices}); rid = {i: k for k, i in enumerate(used)}
    vs = [tuple(me_b.vertices[i].co + me_b.vertices[i].normal * 0.026) for i in used]
    fs = [tuple(rid[i] for i in p_.vertices) for p_ in faces]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = rig; o.matrix_parent_inverse = body.matrix_parent_inverse.copy(); o.matrix_basis = body.matrix_basis.copy()
    o.data.materials.append(BCDM); groups = {}
    for k, i in enumerate(used):
        for gn, w in wmap(me_b.vertices[i]).items():
            if w <= 0: continue
            if gn not in groups: groups[gn] = o.vertex_groups.new(name=gn)
            groups[gn].add([k], w, 'REPLACE')
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig; md.use_deform_preserve_volume = True
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.012; sol.offset = 1.0
    return o

class Diver:
    def __init__(self, name):
        with bpy.data.libraries.load(asset('man.blend'), link=False) as (_s, _d):
            _d.objects = [n for n in _s.objects if n.startswith('Human')]
        self.col = bpy.data.collections.new(name); S.collection.children.link(self.col)
        for o in _d.objects: self.col.objects.link(o)
        objs = list(_d.objects)
        self.rig = next(o for o in objs if o.type == 'ARMATURE'); self.PB = self.rig.pose.bones
        self.body = next(o for o in objs if o.name == 'Human')
        self.suit = next(o for o in objs if 'casualsuit' in o.name)
        for o in objs:
            if o.type == 'MESH' and o not in (self.body, self.suit): o.hide_render = o.hide_viewport = True     # hair, brows, lashes, eyes
        for ob in (self.body, self.suit):
            ob.data.materials.clear(); ob.data.materials.append(NEO)
            for md in ob.modifiers:
                if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
        for p_ in self.body.data.polygons: p_.material_index = 0
        sol = self.suit.modifiers.new('neo', 'SOLIDIFY'); sol.thickness = 0.004
        self.root = empty(name + '_root'); self.rig.parent = self.root; self.rig.location = (0, 0, 0); self.rig.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        self.gear = []
        g_ = self.gear
        def bp_(o, bone, pos=(0, 0, 0)): bone_parent(o, self.rig, bone, pos); g_.append(o); return o
        # mask: twin lenses in a hard frame, a soft skirt sealing round the face, a split strap with buckles
        for sx_ in (1, -1):
            fr = prim('cylinder', name + f'_lensframe{sx_}', FINM, radius=0.036, depth=0.022, vertices=24); fr.scale = (1.0, 1.0, 1.0); fr.rotation_euler = (R(90), 0, 0)
            fr.scale = (1.15, 0.95, 1.0); fr.rotation_euler = (R(90), 0, 0); bp_(fr, 'head', (sx_ * 0.036, -0.158, 1.533))
            ln = prim('cylinder', name + f'_lens{sx_}', MASKG, radius=0.031, depth=0.006, vertices=24); ln.scale = (1.15, 0.95, 1.0)
            ln.rotation_euler = (R(90), 0, 0); bp_(ln, 'head', (sx_ * 0.036, -0.170, 1.533))
        sk = prim('cube', name + '_skirt', SKIRT, size=1.0, scale=(0.155, 0.05, 0.078)); bevel(sk, 0.024, 4); bp_(sk, 'head', (0.0, -0.138, 1.524))
        nose = prim('cube', name + '_nosepocket', SKIRT, size=1.0, scale=(0.04, 0.04, 0.035)); bevel(nose, 0.012, 3); bp_(nose, 'head', (0.0, -0.162, 1.497))
        for k_, z_ in enumerate((1.545, 1.515)):
            st = tube(name + f'_strap{k_}', [(0.082 * math.cos(a_), -0.035 + 0.115 * math.sin(a_), z_ + 0.03 * math.sin(a_) * (k_ - 0.5)) for a_ in [math.pi * (1.0 + kk / 18) for kk in range(19)]][::-1] +
                      [], 0.007, WEBM, seg=6)
            bp_(st, 'head')
        for sx_ in (1, -1):
            bk = prim('cube', name + f'_buckle{sx_}', FINM, size=1.0, scale=(0.012, 0.03, 0.04)); bevel(bk, 0.004, 2); bp_(bk, 'head', (sx_ * 0.082, -0.12, 1.53))
        # regulator second stage: body, purge button, exhaust tee, mouthpiece; the hose over his right shoulder to the first stage
        rb = prim('cylinder', name + '_reg', FINM, radius=0.032, depth=0.045, vertices=20); rb.rotation_euler = (R(90), 0, 0); bp_(rb, 'head', (-0.012, -0.178, 1.455))
        pg = prim('cylinder', name + '_purge', mat('purge', (0.6, 0.6, 0.62), 0.3, metal=0.5), radius=0.024, depth=0.008, vertices=16); pg.rotation_euler = (R(90), 0, 0); bp_(pg, 'head', (-0.012, -0.203, 1.455))
        ex = prim('cube', name + '_exhaust', FINM, size=1.0, scale=(0.07, 0.025, 0.02)); bevel(ex, 0.008, 2); bp_(ex, 'head', (-0.012, -0.185, 1.425))
        bp_(tube(name + '_lp', [(-0.04, -0.175, 1.455), (-0.12, -0.15, 1.44), (-0.17, -0.04, 1.42), (-0.15, 0.10, 1.47), (-0.06, 0.22, 1.54), (0.0, 0.23, 1.57)], 0.0085, FINM, seg=8), 'neck01')
        # octopus (yellow backup) clipped at the chest on its own hose; inflator hose (corrugated) down the left shoulder
        oc_ = prim('cylinder', name + '_octo', OCTOM, radius=0.03, depth=0.042, vertices=18); oc_.rotation_euler = (R(80), 0, 0); bp_(oc_, 'spine02', (0.07, -0.16, 1.18))
        bp_(tube(name + '_octohose', [(0.07, -0.15, 1.19), (0.13, -0.11, 1.28), (0.15, 0.04, 1.36), (0.06, 0.19, 1.47), (0.02, 0.19, 1.50)], 0.008, OCTOM, seg=8), 'spine02')
        infl = [(0.12, -0.13, 1.08 + 0.02 * kk) for kk in range(1)]
        ip = [(0.13, -0.12, 1.06), (0.15, -0.11, 1.18), (0.15, -0.06, 1.33), (0.12, 0.05, 1.41)]
        bp_(tube(name + '_inflator', ip, lambda u: 0.014 * (1 + 0.18 * math.sin(u * 2 * math.pi * 22)), FINM, seg=10), 'spine02')
        bp_(prim('cube', name + '_inflhead', FINM, size=1.0, scale=(0.03, 0.03, 0.07)), 'spine02', (0.13, -0.125, 1.03))
        # pressure gauge console on its hose, hanging at the left hip
        bp_(tube(name + '_hp', [(0.05, 0.21, 1.54), (0.17, 0.12, 1.30), (0.20, 0.0, 1.05), (0.19, -0.06, 0.92)], 0.008, FINM, seg=8), 'spine03')
        gc = prim('cylinder', name + '_gauge', FINM, radius=0.038, depth=0.03, vertices=24); gc.rotation_euler = (R(90), 0, 0); bp_(gc, 'spine03', (0.19, -0.075, 0.90))
        gf = prim('cylinder', name + '_gaugeface', GAUGEF, radius=0.03, depth=0.004, vertices=24); gf.rotation_euler = (R(90), 0, 0); bp_(gf, 'spine03', (0.19, -0.092, 0.90))
        # BC vest: the torso's own shape pushed out, with a back plate, shoulder straps, a chest strap, a cummerbund, two pockets
        self.vest = make_vest(name + '_vest', self.body, self.rig, self.col); g_.append(self.vest)
        for sx_ in (1, -1):
            bp_(tube(name + f'_shstrap{sx_}', [(sx_ * 0.09, 0.10, 1.43), (sx_ * 0.13, -0.02, 1.44), (sx_ * 0.135, -0.135, 1.33), (sx_ * 0.12, -0.15, 1.15), (sx_ * 0.11, -0.14, 1.00)],
                       0.018, WEBM, seg=6), 'spine02')
            qr = prim('cube', name + f'_qr{sx_}', FINM, size=1.0, scale=(0.045, 0.02, 0.05)); bevel(qr, 0.006, 2); bp_(qr, 'spine02', (sx_ * 0.135, -0.155, 1.30))
            pk = prim('cube', name + f'_pocket{sx_}', BCDM, size=1.0, scale=(0.09, 0.05, 0.12)); bevel(pk, 0.02, 3); bp_(pk, 'spine03', (sx_ * 0.17, -0.10, 0.99))
            dr = prim('uv_sphere', name + f'_dring{sx_}', METAL, radius=0.012, segments=10, ring_count=6); dr.scale = (1, 0.4, 1); bp_(dr, 'spine02', (sx_ * 0.13, -0.16, 1.24))
        bp_(tube(name + '_chest', [(-0.13, -0.155, 1.27), (0.0, -0.17, 1.27), (0.13, -0.155, 1.27)], 0.01, WEBM, seg=6), 'spine02')
        bp_(tube(name + '_cummer', [(0.175 * math.cos(a_), -0.005 + 0.135 * math.sin(a_), 1.03) for a_ in [2 * math.pi * kk / 36 for kk in range(37)]], lambda u: 0.032, BCDM, seg=8, caps=False), 'spine03')
        # tank: a steel cylinder with a domed top, a yellow band, a valve, a first stage with ports, the cam band to the vest
        tk = lathe(name + '_tank', [(0.0, -0.36), (0.07, -0.355), (0.088, -0.33), (0.089, 0.24), (0.075, 0.31), (0.04, 0.345), (0.022, 0.36), (0.0, 0.36)], 32, TANKM)
        bp_(tk, 'spine02', (0.0, 0.225, 1.13))
        tb = prim('cylinder', name + '_tankband', TANKBAND, radius=0.0905, depth=0.05, vertices=32); bp_(tb, 'spine02', (0.0, 0.225, 1.33))
        vl = prim('cylinder', name + '_valve', METAL, radius=0.022, depth=0.07, vertices=16); bp_(vl, 'spine02', (0.0, 0.225, 1.52))
        kn = prim('cylinder', name + '_knob', FINM, radius=0.022, depth=0.016, vertices=16); bp_(kn, 'spine02', (0.0, 0.225, 1.565))
        fs_ = prim('cylinder', name + '_first', METAL, radius=0.026, depth=0.06, vertices=16); fs_.rotation_euler = (R(90), 0, 0); bp_(fs_, 'spine02', (0.0, 0.19, 1.515))
        for k_, a_ in enumerate((0.0, 1.5, 3.1, 4.6)):
            pt = prim('cylinder', name + f'_port{k_}', METAL, radius=0.008, depth=0.03, vertices=8)
            pt.rotation_euler = (0, R(90), a_); bp_(pt, 'spine02', (0.03 * math.cos(a_), 0.18, 1.515 + 0.03 * math.sin(a_)))
        for z_ in (0.98, 1.22):
            bp_(tube(name + f'_cam{z_}', [(0.093 * math.cos(a_), 0.225 + 0.093 * math.sin(a_), z_) for a_ in [2 * math.pi * kk / 24 for kk in range(25)]], 0.012, WEBM, seg=6, caps=False), 'spine02')
        # weight belt: webbing, lead blocks, a steel buckle
        bp_(tube(name + '_belt', [(0.168 * math.cos(a_), -0.005 + 0.128 * math.sin(a_), 0.955) for a_ in [2 * math.pi * kk / 40 for kk in range(41)]], 0.016, WEBM, seg=6, caps=False), 'spine04' if 'spine04' in self.rig.data.bones else 'spine03')
        for k_, a_ in enumerate((0.55, 1.0, 2.15, 2.6)):
            ld = prim('cube', name + f'_lead{k_}', LEADM, size=1.0, scale=(0.06, 0.035, 0.05)); bevel(ld, 0.008, 2)
            ld.rotation_euler = (0, 0, -a_ + math.pi / 2); bp_(ld, 'spine04' if 'spine04' in self.rig.data.bones else 'spine03', (0.17 * math.cos(-a_), -0.005 + 0.13 * math.sin(-a_), 0.955))
        bk = prim('cube', name + '_beltbuckle', METAL, size=1.0, scale=(0.06, 0.012, 0.045)); bevel(bk, 0.005, 2); bp_(bk, 'spine04' if 'spine04' in self.rig.data.bones else 'spine03', (0.0, -0.135, 0.955))
        # dive knife strapped to the inside of his right calf
        sh = prim('cube', name + '_sheath', FINM, size=1.0, scale=(0.035, 0.02, 0.17)); bevel(sh, 0.008, 2); bp_(sh, 'lowerleg01.R', (-0.10, -0.05, 0.36))
        hd_ = prim('cylinder', name + '_knifehandle', mat('knife_handle', (0.9, 0.35, 0.05), 0.4), radius=0.012, depth=0.09, vertices=10); bp_(hd_, 'lowerleg01.R', (-0.10, -0.05, 0.49))
        for z_ in (0.30, 0.42):
            bp_(tube(name + f'_kstrap{z_}', [(-0.165 + 0.065 * math.cos(a_), -0.03 + 0.06 * math.sin(a_), z_) for a_ in [2 * math.pi * kk / 20 for kk in range(21)]], 0.006, WEBM, seg=5, caps=False), 'lowerleg01.R')
        # fins: an open-heel foot pocket with a spring strap, a long blade with side rails, ribs and vents
        self.fins = {}
        for s_, x0 in (('L', 0.17), ('R', -0.17)):
            pk = prim('cube', name + '_footpocket' + s_, FINM, size=1.0, scale=(0.115, 0.25, 0.09)); bevel(pk, 0.032, 4); bp_(pk, 'foot.' + s_, (x0, -0.085, 0.05))
            bp_(tube(name + '_spring' + s_, [(x0 + 0.06, 0.02, 0.06), (x0 + 0.04, 0.085, 0.07), (x0, 0.10, 0.075), (x0 - 0.04, 0.085, 0.07), (x0 - 0.06, 0.02, 0.06)],
                     0.011, METAL, seg=8), 'foot.' + s_)
            n_ = 14; fv = []; ff = []
            for i in range(n_):
                u = i / (n_ - 1); w = lerp(0.10, 0.135, u) + 0.02 * math.sin(math.pi * u)
                for xx in (-1, -0.33, 0.33, 1): fv.append((x0 + xx * w, -0.19 - 0.56 * u, 0.03 - 0.025 * u - 0.012 * abs(xx) * u))
            for i in range(n_ - 1):
                for c_ in range(3): ff.append((i * 4 + c_, i * 4 + c_ + 1, (i + 1) * 4 + c_ + 1, (i + 1) * 4 + c_))
            bl = mesh(name + '_blade' + s_, fv, ff, FINB, smooth_=True); so = bl.modifiers.new('th', 'SOLIDIFY'); so.thickness = 0.01; subsurf(bl, 1)
            bp_(bl, 'foot.' + s_); self.fins[s_] = bl
            for xx in (-1, 1):
                bp_(tube(name + f'_rail{s_}{xx}', [(x0 + xx * 0.105, -0.15, 0.045), (x0 + xx * 0.125, -0.45, 0.02), (x0 + xx * 0.135, -0.74, 0.0)], lambda u: 0.014 * (1 - 0.5 * u), FINM, seg=8), 'foot.' + s_)
            for xx in (-0.45, 0.45):
                bp_(tube(name + f'_rib{s_}{xx}', [(x0 + xx * 0.1, -0.2, 0.038), (x0 + xx * 0.115, -0.55, 0.012)], 0.006, FINM, seg=6), 'foot.' + s_)
        # catch bag: a yellow mesh bag on a stainless frame handle, two lobsters inside
        bg = prim('uv_sphere', name + '_bag', BAGM, radius=0.15, segments=20, ring_count=12); bg.scale = (0.85, 0.85, 1.45)
        wf = bg.modifiers.new('net', 'WIREFRAME'); wf.thickness = 0.007; bp_(bg, 'wrist.L', (0.52, -0.26, 0.74)); self.bag = bg
        bp_(tube(name + '_baghandle', [(0.47, -0.26, 0.93), (0.52, -0.26, 0.97), (0.57, -0.26, 0.93)], 0.008, METAL, seg=6), 'wrist.L')
        for k_ in range(2):
            lc = Vector((0.52 + 0.04 * (k_ - 0.5), -0.26 + 0.03 * k_, 0.70 + 0.09 * k_))
            lb = prim('uv_sphere', name + f'_lobster{k_}', LOBM, radius=0.045, segments=14, ring_count=8); lb.scale = (0.55, 0.55, 1.6); bp_(lb, 'wrist.L', lc)
            for sx_ in (1, -1):
                cl = prim('uv_sphere', name + f'_claw{k_}{sx_}', LOBM, radius=0.028, segments=10, ring_count=6); cl.scale = (0.7, 0.5, 1.5)
                bp_(cl, 'wrist.L', lc + Vector((sx_ * 0.04, 0, 0.09)))
        # x-ray bones: glowing rods along the main bones (shown only in the x-ray beat), a skull, ribs
        self.bones = []
        for bn in ('upperarm01.L', 'upperarm02.L', 'lowerarm01.L', 'lowerarm02.L', 'upperarm01.R', 'upperarm02.R', 'lowerarm01.R', 'lowerarm02.R',
                   'upperleg01.L', 'upperleg02.L', 'lowerleg01.L', 'lowerleg02.L', 'upperleg01.R', 'upperleg02.R', 'lowerleg01.R', 'lowerleg02.R',
                   'spine01', 'spine02', 'spine03', 'spine04', 'spine05', 'neck01', 'neck02', 'clavicle.L', 'clavicle.R', 'pelvis.L', 'pelvis.R', 'foot.L', 'foot.R'):
            if bn not in self.rig.data.bones: continue
            b = self.rig.data.bones[bn]; L_ = (b.tail_local - b.head_local).length
            r_ = 0.022 if 'leg' in bn else (0.016 if 'arm' in bn else 0.02)
            ro = tube(name + '_xb_' + bn, [(0, 0, 0), (0, L_ * 0.5, 0), (0, L_, 0)], lambda u: r_ * (1.35 - 0.6 * math.sin(math.pi * u)), BONEM, seg=8)
            ro.parent = self.rig; ro.parent_type = 'BONE'; ro.parent_bone = bn; ro.matrix_parent_inverse.identity()
            ro.location = (0, -L_, 0)                                            # bone parenting puts the origin at the tail
            self.bones.append(ro)
        sk = prim('uv_sphere', name + '_xskull', BONEM, radius=0.085, segments=16, ring_count=10); sk.scale = (0.85, 1.0, 1.05)
        bone_parent(sk, self.rig, 'head', (0.0, -0.06, 1.57)); self.bones.append(sk)
        for j in range(6):
            z_ = 1.36 - 0.045 * j; rw = 0.12 + 0.012 * min(j, 3)
            rb = tube(name + f'_xrib{j}', [(rw * math.cos(a_), 0.02 + 0.09 * math.sin(a_), z_ - 0.03 * abs(math.cos(a_))) for a_ in [math.pi * (1 + k / 14) for k in range(15)]], 0.008, BONEM, seg=6)
            bone_parent(rb, self.rig, 'spine02', (0, 0, 0)); self.bones.append(rb)
        for o in self.bones: o.hide_render = True
        # bruises: soft purple patches that fade in over the x-ray
        self.bruises = []
        for j, (bn, off) in enumerate((('upperarm01.L', (0.04, 0, 0)), ('spine02', (0.08, -0.12, 0.0)), ('upperleg01.R', (-0.03, -0.08, 0)), ('spine04', (-0.1, -0.1, 0)),
                                      ('lowerleg01.L', (0.04, -0.05, 0)), ('upperarm02.R', (-0.04, -0.03, 0)), ('upperleg02.L', (0.06, -0.05, 0)))):
            if bn not in self.rig.data.bones: continue
            b = self.rig.data.bones[bn]; p = (b.head_local + b.tail_local) / 2 + Vector(off)
            bz = prim('uv_sphere', name + f'_bruise{j}', BRUISEM, radius=0.045 + 0.015 * (j % 3), segments=12, ring_count=8); bz.scale = (1.0, 1.0, 0.6)
            bone_parent(bz, self.rig, bn, p); bz['alpha'] = 0.0; bz.hide_render = True; self.bruises.append(bz)
        # IK arms
        self.tg = {k: empty(f'{name}_{k}') for k in ('hR', 'hL', 'pR', 'pL')}
        for s_ in ('R', 'L'):
            c = self.PB['wrist.' + s_].constraints.new('IK'); c.target = self.tg['h' + s_]; c.pole_target = self.tg['p' + s_]; c.chain_count = 5; c.pole_angle = R(-90); c.use_tail = True
        self.parts = [self.body, self.suit] + self.gear
    def world(self, p): return self.root.matrix_world @ Vector(p)
    def place(self, pos, fwd, up):
        """his head points along fwd (his body's up axis), his chest faces -up... we pass 'up' as where his back points"""
        Z = Vector(fwd).normalized(); Y = Vector(up).normalized(); Y = (Y - Z * Y.dot(Z)).normalized(); X = Y.cross(Z)
        self.root.matrix_world = Matrix.Translation(Vector(pos)) @ Matrix((X, Y, Z)).transposed().to_4x4()
    def kick(self, t, amp=1.0, f=1.6, bend=1.0):
        for s_, ph in (('L', 0.0), ('R', math.pi)):
            w = math.sin(2 * math.pi * f * t + ph)
            for nm, rot in (('upperleg01.' + s_, (R(-6 + 16 * amp * w), 0, 0)), ('lowerleg01.' + s_, (R((14 + 12 * amp * (1 + math.sin(2 * math.pi * f * t + ph - 0.9))) * bend), 0, 0)),
                            ('foot.' + s_, (R(48 + 10 * amp * w), 0, 0))):
                pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rot
    def legs(self, up=0.0, knee=0.0, foot=45.0, spread=0.0):
        for s_, sg in (('L', 1), ('R', -1)):
            for nm, rot in (('upperleg01.' + s_, (R(up), 0, R(sg * spread))), ('lowerleg01.' + s_, (R(knee), 0, 0)), ('foot.' + s_, (R(foot), 0, 0))):
                pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rot
    def spine(self, bend=0.0, head=0.0, twist=0.0):
        for n, k in (('spine03', 0.3), ('spine02', 0.3), ('spine01', 0.4)):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(bend * k), R(twist * k), 0)
        for n in ('neck01', 'head'):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(head * 0.5), 0, 0)
    def hands(self, hl, hr, pl=None, pr=None):
        self.tg['hL'].location = self.world(hl); self.tg['hR'].location = self.world(hr)
        self.tg['pL'].location = self.world(pl or (0.9, 0.4, 1.0)); self.tg['pR'].location = self.world(pr or (-0.9, 0.4, 1.0))
    def xray(self, v, bones=0.0, bruise=0.0):
        for o in self.parts: o['xr'] = v
        for o in self.bones: o.hide_render = bones < 0.05
        for o in self.bruises: o.hide_render = bruise < 0.05; o['alpha'] = bruise
    def show(self, on):
        for o in self.parts: o.hide_render = not on
        if not on:
            for o in self.bones + self.bruises: o.hide_render = True
DIVER = Diver('diver')

# ================================================================ effects: a school of sand lance the whale is feeding on, the diver's bubbles, the
# splash when the whale breaks the surface, a measuring bar across the open mouth, the throat ring, and the old-story "man in the belly" vignette.
# ---- the school: slim silver fish in one mesh, moved every frame
FISHM = mat('fish', (0.72, 0.76, 0.80), 0.18, metal=0.85, coat=0.6)
FISH_N = 360; _rf = random.Random(21); FISH = []
_fv = []; _ff = []
for i in range(FISH_N):
    b0 = len(_fv); _fv += [(0, 0, 0)] * 6
    _ff += [(b0, b0 + 1, b0 + 2), (b0, b0 + 2, b0 + 3), (b0, b0 + 3, b0 + 4), (b0, b0 + 4, b0 + 1), (b0 + 2, b0 + 5, b0 + 3), (b0 + 4, b0 + 5, b0 + 1)]
    FISH.append((_rf.random(), _rf.random(), _rf.random(), _rf.uniform(0.12, 0.2)))
SCHOOL = mesh('school', _fv, _ff, FISHM, smooth_=False)
def set_school(t, center, radius, swirl=0.6, scatter_from=None, scatter=0.0, gulp=None, gulp_k=0.0, on=1.0):
    co = []; nshow = int(FISH_N * on)
    for i, (a_, b_, c_, L_) in enumerate(FISH):
        if i >= nshow: co.extend((0, 0, -500) * 6); continue
        ang = 2 * math.pi * a_ + swirl * t * (0.8 + 0.4 * b_); rr = radius * (0.35 + 0.65 * b_ ** 0.5)
        p = Vector(center) + Vector((rr * math.cos(ang), rr * math.sin(ang) * 0.8, (c_ - 0.5) * radius * 0.7 + 0.3 * math.sin(t * 1.3 + i)))
        d = Vector((-math.sin(ang), math.cos(ang) * 0.8, 0.05 * math.cos(t + i))).normalized()
        if scatter_from is not None and scatter > 0:
            away = (p - Vector(scatter_from)); dist = away.length + 1e-3; push = scatter * 6.0 / (1 + 0.15 * dist)
            p = p + away.normalized() * push; d = (d + away.normalized() * scatter * 2).normalized()
        if gulp is not None and gulp_k > 0 and h1(i * 3.1) < 0.55:
            p = p.lerp(Vector(gulp) + Vector(((h1(i) - 0.5) * 1.5, (h1(i + 7) - 0.5) * 1.5, (h1(i + 9) - 0.5))), gulp_k);
        s_ = d.cross(Vector((0, 0, 1))).normalized(); u_ = s_.cross(d)
        nose = p + d * L_ * 0.5; tail = p - d * L_ * 0.5
        co.extend((*nose, *(p + s_ * L_ * 0.08), *(p + u_ * L_ * 0.12), *(p - s_ * L_ * 0.08), *(p - u_ * L_ * 0.1), *(tail + u_ * L_ * 0.06 * math.sin(t * 20 + i))))
    SCHOOL.data.vertices.foreach_set('co', co); SCHOOL.data.update()
# ---- bubbles: from the regulator, wobbling up, growing
BUBM = mat('bubble', (0.9, 0.95, 1.0), 0.0, trans=1.0, ior=1.0 / 1.33, coat=0.0)
BUBS = [prim('uv_sphere', f'bub{j}', BUBM, radius=1.0, segments=12, ring_count=8) for j in range(40)]
def set_bubbles(t, src, on=True, rate=1.0, ceiling=SEA_Z - 0.1, spread=1.0):
    for j, o in enumerate(BUBS):
        per = 2.6; ph = ((t * rate + j * per / len(BUBS)) % per) / per
        burst = int((t * rate + j * per / len(BUBS)) / per)
        p = Vector(src) + Vector((0.25 * wob(t, 2.0, j) * ph * spread, 0.25 * wob(t, 2.2, j + 5) * ph * spread, 4.5 * ph))
        r_ = (0.012 + 0.03 * h1(j + burst * 13)) * (1 + 1.5 * ph)
        o.location = p; o.scale = (r_ * 1.2, r_ * 1.2, r_ * 0.8)
        o.hide_render = (not on) or p.z > ceiling or h1(j * 7 + burst) > 0.85
# ---- the splash: white water thrown up as the head breaks the surface, falling back, and a foam patch
SPRAYM = mat('spray', (0.95, 0.97, 1.0), 0.1, trans=0.6, ior=1.33)
FOAMM = mat('foam', (0.92, 0.94, 0.95), 0.6); _nt = FOAMM.node_tree; _out = _nt.nodes['Material Output']; _src = _out.inputs['Surface'].links[0].from_socket
_tr = _nt.nodes.new('ShaderNodeBsdfTransparent'); _mx = _nt.nodes.new('ShaderNodeMixShader')
_g = coord(_nt, 'Generated'); _rad = _nt.nodes.new('ShaderNodeVectorMath'); _rad.operation = 'DISTANCE'; _nt.links.new(_g, _rad.inputs[0]); _rad.inputs[1].default_value = (0.5, 0.5, 0.5)
_mask = math_(_nt, 'MULTIPLY', ramp_v(_nt, tnoise(_nt, coord(_nt, 'Object'), 2.5, 8.0, 1.5), 0.45, 0.6), math_(_nt, 'SUBTRACT', 1.0, ramp_v(_nt, _rad.outputs['Value'], 0.25, 0.5)))
_nt.links.new(_mask, _mx.inputs['Fac']); _nt.links.new(_tr.outputs[0], _mx.inputs[1]); _nt.links.new(_src, _mx.inputs[2]); _nt.links.new(_mx.outputs[0], _out.inputs['Surface'])
SPRAY = [prim('ico_sphere', f'spray{j}', SPRAYM, radius=1.0, subdivisions=1) for j in range(160)]
SPRAY_SEED = [(random.Random(j).uniform(0, 2 * math.pi), random.Random(j + 99).uniform(2.0, 8.0), random.Random(j + 7).uniform(1.0, 4.5), random.Random(j + 3).uniform(0.015, 0.06)) for j in range(160)]
FOAM = prim('cylinder', 'foam', FOAMM, radius=1.0, depth=0.05, vertices=48)
def set_splash(t, t0, center, on=True):
    age = t - t0
    for j, o in enumerate(SPRAY):
        ang, up, out, r_ = SPRAY_SEED[j]; a_ = age - 0.25 * h1(j)
        if (not on) or a_ < 0 or a_ > 2.4: o.hide_render = True; continue
        p = Vector(center) + Vector((math.cos(ang) * out * a_, math.sin(ang) * out * a_, up * a_ - 4.9 * a_ * a_))
        o.hide_render = p.z < SEA_Z - 0.3; o.location = p; o.scale = (r_, r_, r_ * 1.4)
    FOAM.hide_render = (not on) or age < 0.1
    if not FOAM.hide_render:
        r_ = 2.5 + 5.0 * smooth(0.0, 2.5, age); FOAM.location = Vector(center) + Vector((0, 0, SEA_Z + 0.06 - center[2])); FOAM.scale = (r_, r_ * 0.8, 1)
# ---- the measuring bar across the open mouth (about 10 ft = 3 m), with arrow ends
MEASM = emis_mix('measure', (1.0, 0.85, 0.15), 6.0, 'alpha')
MEAS = empty('measure_root')
MEAS_BAR = tube('meas_bar', [(0, 0, -1.5), (0, 0, 1.5)], 0.035, MEASM, MEAS, seg=10)
MEAS_TIPS = [prim('cone', f'meas_tip{k}', MEASM, MEAS, loc=(0, 0, s_ * 1.42), rot=(R(0 if s_ > 0 else 180), 0, 0), radius1=0.12, radius2=0.0, depth=0.22, vertices=16) for k, s_ in enumerate((1, -1))]
def set_measure(p0, p1, a_):
    on = a_ > 0.02
    for o in [MEAS_BAR] + MEAS_TIPS: o.hide_render = not on; o['alpha'] = a_
    if not on: return
    c = (Vector(p0) + Vector(p1)) / 2; d = (Vector(p1) - Vector(p0)); MEAS.location = c
    MEAS.rotation_mode = 'QUATERNION'; MEAS.rotation_quaternion = d.to_track_quat('Z', 'Y'); s_ = d.length / 3.0; MEAS.scale = (1, 1, s_ * smooth(0, 1, a_))
# ---- the throat ring: about the size of a fist, stretching to about 15 in (38 cm)
RINGM = emis_mix('ring', (1.0, 0.85, 0.3), 8.0, 'alpha')
RING = prim('cylinder', 'throat_ring', RINGM, radius=1.0, depth=0.02, vertices=48)
RING_IN = prim('cylinder', 'throat_hole', emis('hole', (0.0, 0.0, 0.0), 0.0), radius=0.9, depth=0.03, vertices=48)
FIST = empty('fist_root')
# ---- the old-story vignette: a little man sitting by a fire in the whale's belly (x-ray)
MYTHM = emis_mix('myth', (1.0, 0.75, 0.35), 3.5, 'alpha')
MYTH = empty('myth_root')
MYTH_PARTS = [prim('uv_sphere', 'myth_head', MYTHM, MYTH, loc=(0, 0, 0.72), radius=0.13, segments=14, ring_count=8),
              tube('myth_torso', [(0, 0, 0.6), (0.02, 0, 0.32)], lambda u: 0.11, MYTHM, MYTH, seg=10),
              tube('myth_thighL', [(0.02, 0.08, 0.32), (0.32, 0.1, 0.3), (0.34, 0.1, 0.02)], 0.05, MYTHM, MYTH, seg=8),
              tube('myth_thighR', [(0.02, -0.08, 0.32), (0.32, -0.1, 0.3), (0.34, -0.1, 0.02)], 0.05, MYTHM, MYTH, seg=8),
              tube('myth_armL', [(0.0, 0.12, 0.56), (0.18, 0.18, 0.42), (0.36, 0.1, 0.42)], 0.04, MYTHM, MYTH, seg=8),
              tube('myth_armR', [(0.0, -0.12, 0.56), (0.18, -0.18, 0.42), (0.36, -0.1, 0.42)], 0.04, MYTHM, MYTH, seg=8)]
FIREM = emis_mix('fire', (1.0, 0.45, 0.08), 12.0, 'alpha')
MYTH_FIRE = [prim('cone', f'myth_flame{k}', FIREM, MYTH, loc=(0.75 + 0.06 * k, 0.05 * (k - 1), 0.12), radius1=0.09, radius2=0.0, depth=0.3, vertices=10) for k in range(3)]
STOMACHM = emis_mix('stomach', (0.9, 0.35, 0.3), 1.2, 'alpha')
STOMACH = prim('uv_sphere', 'stomach', STOMACHM, radius=1.0, segments=24, ring_count=14)
def set_myth(t, loc, a_, yaw):
    on = a_ > 0.02
    for o in MYTH_PARTS + MYTH_FIRE + [STOMACH]: o.hide_render = not on; o['alpha'] = a_ * (0.35 if o is STOMACH else 1.0)
    if not on: return
    MYTH.location = loc; MYTH.rotation_euler = (0, 0, yaw); STOMACH.location = Vector(loc) + Vector((0, 0, 0.55)); STOMACH.scale = (1.7, 1.25, 1.1)
    STOMACH.rotation_euler = (0, 0, yaw)
    for k, o in enumerate(MYTH_FIRE): o.scale = (1, 1, 0.8 + 0.4 * abs(wob(t, 9, k)))

# ================================================================ the story, frame by frame
# beats: 0 the lunge | 1 it really happened (x-ray, he's inside) | 2 the old story (man in the belly) | 3 mouth opens ~10 ft (ghost jaw + bar)
# 4 throat the size of a fist (ring) | 5 30-40 s in the dark | 6 rises, shakes, spits him out | 7 bruised, no broken bones (x-ray)
# 8 the sperm whale gulps a giant squid whole | 9 it swims past; subscribe
TE = 2.5                                   # the gulp
T_SPIT = B[6] + 1.95
T_SURF = B[6] + 0.95                       # the snout breaks the surface
DIV_IN = Vector((-2.95, 0.0, -1.0))        # where he lies inside the closed mouth (whale-local): feet by the throat, head toward the snout
DIR0 = Vector((math.cos(R(12)), 0, math.sin(R(12))))
def diver_free(t): return Vector((0.35 * t, 0.0, -11.2))
CATCH_LOCAL = Vector((-1.9, 0.0, -0.62))
def rotm(yaw, pitch, roll): return Euler((roll, -pitch, yaw), 'XYZ').to_matrix()
S_TE = diver_free(TE) - rotm(0, R(12), 0) @ CATCH_LOCAL
def hb_pose(t):
    """the humpback's pose at t: loc, yaw, pitch, roll, open, engulf, tail, fin"""
    v = 2.6
    if t < TE: s_ = v * (t - TE)
    else: tau = t - TE; s_ = v * 1.4 * (1 - math.exp(-tau / 1.4)) + 0.45 * tau
    loc = S_TE + DIR0 * s_; pitch = R(12); yaw = 0.0; roll = 0.0
    open_ = 0.95 * (1 - smooth(TE - 0.35, TE + 0.45, t)); engulf = smooth(TE - 0.5, TE + 0.4, t) * (1 - 0.2 * smooth(TE + 2.0, TE + 5.0, t))
    tail = 0.55 * math.sin(2 * math.pi * 0.42 * t) * (1 if t < TE + 1 else 0.6)
    fin = 0.6 + 0.4 * math.sin(2 * math.pi * 0.3 * t)
    if t > B[6] - 0.2:                                                   # pitch up, power to the surface, shake, spit, sink back
        u = smooth(B[6] - 0.2, B[6] + 0.7, t)
        pitch = lerp(R(12), R(62), u) - R(20) * smooth(T_SPIT + 0.2, T_SPIT + 1.5, t)
        rise = 9.0 * smooth(B[6], T_SURF + 0.5, t) - 2.6 * smooth(T_SPIT + 0.3, T_SPIT + 2.5, t)
        loc = loc + Vector((1.2 * u, 0, rise))
        roll = R(24) * math.sin(2 * math.pi * 1.6 * (t - T_SURF)) * smooth(T_SURF + 0.2, T_SURF + 0.5, t) * (1 - smooth(T_SPIT + 0.2, T_SPIT + 0.6, t))
        open_ = 0.45 * smooth(T_SPIT - 0.15, T_SPIT + 0.05, t) * (1 - smooth(T_SPIT + 0.5, T_SPIT + 1.2, t))
        engulf = engulf * (1 - smooth(T_SPIT - 0.1, T_SPIT + 0.4, t))
        tail = 0.9 * math.sin(2 * math.pi * 0.9 * t) * (1 - smooth(T_SURF, T_SURF + 0.5, t))
    return loc, yaw, pitch, roll, open_, engulf, tail, fin
def hb_matrix(t):
    loc, yaw, pitch, roll = hb_pose(t)[:4]; return Matrix.Translation(loc) @ rotm(yaw, pitch, roll).to_4x4()

# ---- the ghost jaw (beat 3): a glowing copy that swings open while the real one stays shut on him
GHOSTM = bpy.data.materials.new('ghost'); GHOSTM.use_nodes = True; nt = GHOSTM.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
lw_ = nt.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.4
em_ = nt.nodes.new('ShaderNodeEmission'); em_.inputs['Color'].default_value = (1.0, 0.85, 0.25, 1)
nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw_.outputs['Facing'], 1.4), math_(nt, 'MULTIPLY', objattr(nt, 'alpha'), 12.0)), math_(nt, 'MULTIPLY', objattr(nt, 'alpha'), 0.6)), em_.inputs['Strength'])
tr_ = nt.nodes.new('ShaderNodeBsdfTransparent'); ad_ = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr_.outputs[0], ad_.inputs[0]); nt.links.new(em_.outputs[0], ad_.inputs[1])
nt.links.new(ad_.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
GHOST = HB['jaw'].copy(); GHOST.data = HB['jaw'].data.copy(); GHOST.name = 'ghost_jaw'; S.collection.objects.link(GHOST)
GHOST.data.materials.clear(); GHOST.data.materials.append(GHOSTM); GHOST.parent = HB['root']
for c in list(GHOST.children): pass
GHOST.hide_render = True
def jaw_tip_open(a_):
    hx = -HINGE_S * HB_L; hz = hb_mouth(HINGE_S); x_, z_ = 0.12, -0.26; ang = R(58) * a_; dx, dz = x_ - hx, z_ - hz
    return Vector((hx + dx * math.cos(ang) + dz * math.sin(ang), 0.0, hz - dx * math.sin(ang) + dz * math.cos(ang)))

# ---- a dim light inside the mouth so his struggle reads in the dark (beat 5)
MOUTH_LT = light_at('mouth_light', 'POINT', (0, 0, 0), (0, 0, -1), 0.0, (0.55, 0.85, 0.75), 0.4)
# ---- deep water past the drop-off (beats 8-9): darker, bluer, a soft light from above on the sperm whale
DEEPV = bpy.data.materials.new('deep_vol'); DEEPV.use_nodes = True; nt = DEEPV.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
va2 = nt.nodes.new('ShaderNodeVolumeAbsorption'); va2.inputs['Color'].default_value = (0.12, 0.30, 0.55, 1); va2.inputs['Density'].default_value = 0.022
nt.links.new(va2.outputs[0], nt.nodes['Material Output'].inputs['Volume'])
DEEP_X = 48.0
DEEPBOX = box('deep', (500, 600, 260), (DEEP_X + 250 + 6, 0, -14 - 130), DEEPV)
CLIFFM = mat('cliff', (0.14, 0.13, 0.12), 0.9); noisy(CLIFFM, 1.5, 0.45, 0.1)
CLIFF = prim('plane', 'cliff', CLIFFM, loc=(DEEP_X, 0, FLOOR_Z - 60), rot=(0, R(90), 0), size=120)
cs_ = CLIFF.modifiers.new('sub', 'SUBSURF'); cs_.subdivision_type = 'SIMPLE'; cs_.levels = cs_.render_levels = 5
cd_ = CLIFF.modifiers.new('disp', 'DISPLACE'); cd_.texture = tx_; cd_.strength = 2.5
FLOOR.scale = (1.0, 1.0, 1.0); FLOOR.location = (DEEP_X - 200, 0, FLOOR_Z)
SW_LT = light_at('sw_light', 'SPOT', (DEEP_X + 34, -4, 0.0), (DEEP_X + 36, 0, -28), 0.0, (0.6, 0.8, 1.0), 2.0)
SW_LT.data.spot_size = R(70); SW_LT.data.spot_blend = 0.8
FILL_LT = light_at('deep_fill', 'AREA', (0, 0, -30), (1, 0, -30), 0.0, (0.75, 0.88, 1.0), 4.0)
try: FILL_LT.visible_camera = False
except Exception: pass
SW_HOME = Vector((DEEP_X + 40, 4.0, -26.0))
def sw_pose(t):
    t0 = B[8] - 0.3; u = t - t0
    loc = SW_HOME + Vector((-2.2 * u, -0.6 * u, 0.25 * u)); yaw = R(185) + R(4) * math.sin(u * 0.8)
    jaw = smooth(B[8] + 1.2, B[8] + 1.7, t) * (1 - smooth(B[8] + 2.6, B[8] + 3.2, t))
    return loc, yaw, R(-3), 0.0, jaw, 0.5 * math.sin(2 * math.pi * 0.35 * t)

# ---- camera keys: world (lunge, surface, deep) and whale-local (riding along while he's inside)
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
T_A = 4.6                                  # world -> whale-local
T_B = B[6] + 0.35                          # whale-local -> world (out of the mouth, up to the surface)
LK = [   # whale-local camera keys
    key(T_A, (-0.6, -4.8, 0.2), (-1.8, 0.0, -0.6), 26),                     # the shut mouth from the side (the screen dips to black)
    key(B[1] + 0.2, (-0.9, -5.6, 0.3), (-2.0, 0.0, -0.6), 26),
    key(B[1] + 1.6, (-2.4, -8.6, 0.9), (-3.0, 0.0, -0.45), 28),             # pull back: x-ray, he's in there
    key(B[2] - 0.2, (-2.9, -8.8, 1.0), (-3.6, 0.0, -0.45), 28),
    key(B[2] + 1.1, (-6.2, -6.4, 0.6), (-6.8, 0.0, -0.55), 30),             # along to the belly: the old story
    key(B[3] - 0.3, (-6.4, -6.2, 0.5), (-6.9, 0.0, -0.6), 30),
    key(B[3] + 0.8, (3.6, -6.4, 0.6), (-1.6, 0.0, -1.3), 24),               # front quarter: the mouth's ten-foot gape (ghost)
    key(B[4] - 0.2, (3.7, -6.2, 0.6), (-1.6, 0.0, -1.35), 24),
    key(B[4] + 0.9, (-2.7, -3.3, -0.55), (-3.2, 0.0, -0.9), 30),            # in close, from outside: him, and the fist-sized throat behind his fins
    key(B[5] - 0.25, (-2.9, -3.1, -0.55), (-3.35, 0.0, -0.9), 30),
    key(B[5] + 0.6, (-1.0, -3.4, -0.3), (-2.1, 0.0, -1.0), 26),             # in the dark with him (dim x-ray)
    key(B[6] - 0.3, (-1.3, -3.0, -0.35), (-2.1, 0.0, -1.0), 26),
    key(T_B, (1.6, -5.5, -0.8), (-2.5, 0.0, -0.4), 24),                     # back out as it powers up
]
def world_keys_lunge():
    D0 = diver_free(0.0)
    return [key(0.0, D0 + Vector((4.2, 2.3, -0.45)), D0 + Vector((-1.4, 0.0, -0.85)), 26),          # ahead of him, looking back: the mouth coming up behind
            key(TE - 0.6, diver_free(TE) + Vector((4.2, 2.8, 0.6)), diver_free(TE) + Vector((-1.0, -0.2, -0.3)), 24),
            key(TE + 0.5, diver_free(TE) + Vector((5.5, 6.0, 1.4)), diver_free(TE) + Vector((0.2, 0.0, -0.2)), 22)]
def surf_keys():
    sp = hb_matrix(T_SPIT) @ Vector((0.5, 0, -0.4)); land = DIVER_LAND
    return [key(T_SURF + 0.1, Vector((sp.x + 4.0, sp.y - 8.0, 0.9)), Vector((sp.x, sp.y, 2.2)), 22),      # at the waterline: up it comes
            key(T_SPIT + 0.4, Vector((sp.x + 4.2, sp.y - 8.4, 1.2)), Vector((sp.x + 1.2, sp.y - 1.2, 2.4)), 22),
            key(T_LAND + 0.15, Vector((sp.x + 4.6, sp.y - 8.6, 1.3)), DIVER_LAND + Vector((0, 0, 0.3)), 24),
            key(B[7] + 0.2, land + Vector((0.8, -1.9, 2.6)), land + Vector((0.9, 0.1, 0.1)), 30),       # down to him floating on his back
            key(B[8] - 0.4, land + Vector((0.9, -1.7, 2.4)), land + Vector((0.9, 0.1, 0.1)), 30)]
def deep_keys():
    land = DIVER_LAND
    return [key(B[8] - 0.4, land + Vector((0.9, -1.7, 2.4)), land + Vector((0.9, 0.1, 0.1)), 30),
            key(B[8] + 0.55, Vector((DEEP_X + 16, -6.0, -18.0)), Vector((DEEP_X + 36, 3.0, -25.0)), 24),   # dive: over the drop-off, into the deep
            key(B[8] + 1.5, Vector((DEEP_X + 27.5, -5.2, -24.2)), Vector((DEEP_X + 37, 3.0, -26.0)), 26),   # it comes at us, jaw dropping, the squid
            key(B[9] - 0.3, Vector((DEEP_X + 27.0, -6.2, -24.5)), Vector((DEEP_X + 33, 3.0, -26.0)), 26),   # x-ray: down the throat
            key(B[9] + 2.6, Vector((DEEP_X + 22, -8.5, -21.5)), Vector((DEEP_X + 28, 2.0, -25.0)), 26),
            key(TOTAL, Vector((DEEP_X + 20.5, -9.0, -19.5)), Vector((DEEP_X + 25, 1.0, -22.0)), 26)]
DIVER_LAND = None
def diver_spit(t):
    p0 = hb_matrix(T_SPIT) @ Vector((0.4, 0, -0.4)); v0 = Vector((3.0, -2.6, 6.5)); tau = t - T_SPIT
    p = p0 + v0 * tau + Vector((0, 0, -4.9 * tau * tau))
    return p
_tl = (v0z := 6.5); _z0 = (hb_matrix(T_SPIT) @ Vector((0.4, 0, -0.4))).z
T_LAND = T_SPIT + (_tl + math.sqrt(_tl * _tl + 2 * 4.9 * max(_z0 - SEA_Z, 0))) / 9.8
DIVER_LAND = Vector((diver_spit(T_LAND).x + 0.6, diver_spit(T_LAND).y - 0.4, SEA_Z + 0.32))
print('T_LAND', round(T_LAND - T_SPIT, 3), flush=True)

def camera(t):
    if t < T_A:
        ks = world_keys_lunge(); M = hb_matrix(T_A)
        ks.append(key(T_A, M @ LK[0][1], M @ LK[0][2], LK[0][3])); return interp(ks, t)
    if t < T_B:
        cp, ct, lens = interp(LK, t); M = hb_matrix(t); return M @ cp, M @ ct, lens
    if t < B[8] - 0.4:
        M = hb_matrix(T_B); ks = [key(T_B, M @ LK[-1][1], M @ LK[-1][2], LK[-1][3])]
        # rise with the head to the surface (just under it), then break out above
        mh = hb_matrix(T_SURF - 0.1) @ Vector((-1.0, 0, 0))
        ks.append(key(T_SURF - 0.25, Vector((mh.x + 4.0, mh.y - 7.5, -0.9)), Vector((mh.x, mh.y, mh.z + 1.0)), 22))
        ks += surf_keys(); return interp(ks, t)
    return interp(deep_keys(), t)

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---------------- the humpback
    loc, yaw, pitch, roll, open_, engulf, tail, fin = hb_pose(t)
    xr = 0.82 * smooth(B[1] + 0.5, B[1] + 1.4, t) * (1 - smooth(B[6] - 0.25, B[6] + 0.25, t)) * (1 - 0.35 * smooth(B[3] - 0.2, B[3] + 0.3, t) * (1 - smooth(B[4] - 0.2, B[4] + 0.3, t)))
    dark = smooth(B[5] - 0.1, B[5] + 0.6, t) * (1 - smooth(B[6] - 0.3, B[6] + 0.2, t))
    SUN.data.energy = 3.2 * (1 - 0.82 * dark); WBG.inputs['Strength'].default_value = 0.3 * (1 - 0.8 * dark)
    humpback_set(loc, yaw, pitch, roll, open_, engulf, tail, fin, xr=xr)
    on_hb = t < B[8] + 0.6
    for o in [HB['root']] + list(HB['root'].children_recursive):
        if o.type == 'MESH' and o is not GHOST: o.hide_render = not on_hb
    bpy.context.view_layer.update()
    M = hb_matrix(t)
    # ghost jaw + measuring bar (beat 3)
    ga = smooth(B[3] + 0.05, B[3] + 0.5, t) * (1 - smooth(B[4] + 0.1, B[4] + 0.6, t))
    GHOST.hide_render = ga < 0.02; GHOST['alpha'] = ga
    GHOST.data.shape_keys.key_blocks['open'].value = smooth(B[3] + 0.2, B[3] + 1.2, t); GHOST.data.shape_keys.key_blocks['engulf'].value = 0.0
    set_measure(M @ Vector((0.15, 0.0, -0.12)), M @ jaw_tip_open(GHOST.data.shape_keys.key_blocks['open'].value), ga * smooth(B[3] + 0.9, B[3] + 1.3, t))
    # throat ring (beat 4): fist size, stretching to about 15 in
    ra = smooth(B[4] + 0.4, B[4] + 0.8, t) * (1 - smooth(B[5] - 0.2, B[5] + 0.2, t))
    RING.hide_render = RING_IN.hide_render = ra < 0.02; RING['alpha'] = ra
    rr_ = lerp(0.05, 0.19, smooth(B[4] + 1.6, B[4] + 2.6, t))
    if ra >= 0.02:
        rp = M @ Vector((-3.62, 0.0, -0.80)); q_ = (M.to_3x3() @ Vector((1, 0, 0))).to_track_quat('Z', 'Y')
        for o, k in ((RING, 1.0), (RING_IN, 0.86)):
            o.location = rp; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = q_; o.scale = (rr_ * k, rr_ * k, 1.0)
    # the old story (beat 2)
    ma = smooth(B[2] + 0.2, B[2] + 0.7, t) * (1 - smooth(B[3] - 0.25, B[3] + 0.15, t))
    set_myth(t, M @ Vector((-6.9, 0.0, -1.25)), ma, yaw + math.pi * 0.5)
    # ---------------- the diver
    D = DIVER; D.show(True)
    if t < TE - 0.1:
        p = diver_free(t); D.place(p, (1, 0, 0), (0, 0, 1)); D.kick(t, 1.0); D.spine(6, 22)
        D.hands((0.28, -0.42, 1.60), (-0.22, -0.40, 0.95))
    elif t < T_SPIT:
        u = smooth(TE - 0.1, TE + 0.9, t)
        pl = CATCH_LOCAL.lerp(DIV_IN, u); fw = Vector((1, 0, -0.08 * u)).normalized()
        up_ = Vector((0, 0.25 * u, 1))
        squirm = smooth(B[5], B[5] + 0.4, t) * (1 - smooth(B[6] - 0.3, B[6], t))
        D.place(M @ pl, M.to_3x3() @ fw, M.to_3x3() @ up_)
        D.kick(t, 0.4 + 1.2 * squirm, 2.2); D.spine(10 + 14 * squirm * math.sin(t * 5), 25)
        D.hands((0.30, -0.25 + 0.15 * squirm * math.sin(t * 6), 1.72), (-0.30, -0.25 + 0.15 * squirm * math.cos(t * 6), 1.72))
    elif t < T_LAND:
        p = diver_spit(t); tau = t - T_SPIT
        D.place(p, (math.cos(tau * 5), 0.4 * math.sin(tau * 3), math.sin(tau * 5)), (0.2, 1.0, 0.3 * math.sin(tau * 4)))
        D.legs(-20 + 30 * math.sin(tau * 9), 35, 40, 12); D.spine(-10, 10)
        D.hands((0.55, -0.1, 1.85), (-0.55, -0.1, 1.85))
    else:
        tau = t - T_LAND; bob = 0.06 * math.sin(t * 1.7)
        p = DIVER_LAND + Vector((0.05 * tau, 0.02 * tau, bob)) + Vector((0, 0, -0.6 * math.exp(-tau * 3)))
        D.place(p, (1, 0.15, 0.0), (0, 0, -1)); D.legs(6, 18, 40, 8); D.spine(-4, -8)
        D.hands((0.40, 0.05, 1.10), (-0.40, 0.05, 1.10))
    dx = smooth(B[7] + 0.4, B[7] + 1.0, t) * (1 - smooth(B[8] - 0.4, B[8] + 0.1, t))
    if t > B[1] and t < B[6]: D.xray(0.8 * smooth(B[1] + 0.5, B[1] + 1.4, t), 0.0, 0.0)
    else: D.xray(0.75 * dx, dx, dx)
    D.show(t < B[8] + 0.8)
    bpy.context.view_layer.update()
    # bubbles from the regulator (under water only)
    head = D.root.matrix_world @ Vector((0, -0.17, 1.46))
    set_bubbles(t, head, on=head.z < SEA_Z - 0.4 and not (TE + 0.1 < t < T_SPIT), rate=1.0)
    # ---------------- the sea, the school, the splash, the boat
    set_school(t, diver_free(0.0) + Vector((1.5, 1.0, 0.8)), 4.5, swirl=0.5, scatter_from=(M @ Vector((-1.5, 0, -0.5))) if t > 1.2 else None,
               scatter=smooth(1.4, TE, t), gulp=M @ Vector((-2.0, 0, -0.8)), gulp_k=smooth(TE - 0.6, TE, t) * (1 - smooth(TE + 0.2, TE + 0.3, t)), on=1.0 if t < B[3] else 0.0)
    SCHOOL.hide_render = t > B[3]
    set_splash(t, T_SURF + 0.05, hb_matrix(T_SURF + 0.3) @ Vector((0.0, 0, 0)), on=T_SURF < t < B[8])
    oc.time = 2.0 + t * 0.9
    GOBO_MAP.inputs['Location'].default_value = (t * 0.35, t * 0.18, 0.0); GOBO_W.default_value = t * 0.35
    BOAT.location = DIVER_LAND + Vector((13.0 - 1.5 * smooth(B[7], B[8], t), 11.0, SEA_Z - DIVER_LAND.z)); BOAT.rotation_euler = (R(2) * math.sin(t), R(1.5) * math.sin(t * 1.3), R(-30))
    FLOAT.location = DIVER_LAND + Vector((-3.0, 4.0, SEA_Z - DIVER_LAND.z + 0.05 * math.sin(t * 1.5)))
    for o, j in WEED:
        o.rotation_euler = (R(4) * math.sin(t * 0.8 + j), R(4) * math.cos(t * 0.7 + j), 0)
    # ---------------- the deep: the sperm whale and the giant squid
    deep_on = t > B[8] - 0.4
    sperm_show(deep_on); squid_show(deep_on)
    SW_LT.data.energy = 90000.0 * smooth(B[8] - 0.2, B[8] + 0.6, t); FILL_LT.data.energy = 9000.0 * smooth(B[8] + 0.2, B[8] + 0.8, t)
    if t > B[8] - 0.4: SW_LT.location = SW['root'].matrix_world @ Vector((-3.0, -2.5, 7.5)); SW_LT.rotation_mode = 'QUATERNION'; SW_LT.rotation_quaternion = (SW['root'].matrix_world @ Vector((-4.0, 0, -1.0)) - SW_LT.location).to_track_quat('-Z', 'Y')
    if deep_on:
        sl, sy, sp_, sr, sj, stl = sw_pose(t)
        swx = smooth(B[8] + 2.6, B[8] + 3.1, t)
        sperm_set(sl, sy, sp_, sr, sj, stl, xr=0.8 * swx, throat=swx)
        bpy.context.view_layer.update()
        Ms = SW['root'].matrix_world
        g = smooth(B[8] + 1.55, B[8] + 2.6, t)                             # the squid: in front of the jaw, then pulled in and down the throat
        sq0 = Ms @ Vector((3.6, 0.6, -1.2)); sq1 = Ms @ Vector((-SW_HINGE * SW_L - 1.5, 0, -0.6)); sq2 = Ms @ Vector((-SW_HINGE * SW_L - 5.5, 0, -0.4))
        sq = sq0.lerp(sq1, g).lerp(sq2, smooth(B[8] + 2.7, B[9] + 1.5, t))
        heading = (Ms.to_3x3() @ Vector((-1, 0, 0)))
        squid_set(sq, (0, 0, math.atan2(heading.y, heading.x) + math.pi), t, curl=1.0 - 0.7 * g, xr=0.0, scale=1.0)
    else:
        sperm_set(SW_HOME, xr=0.0)
    # ---------------- light inside the mouth (only while we're in there), camera
    MOUTH_LT.location = M @ Vector((-0.8, 0.2, -0.6)); MOUTH_LT.data.energy = 40.0 * smooth(B[5] - 0.2, B[5] + 0.3, t) * (1 - smooth(B[6] - 0.2, B[6] + 0.3, t))
    cp, ct, lens = camera(t)
    if t > B[8]: FILL_LT.location = cp + (cp - ct).normalized() * 1.5 + Vector((0, 0, 2.0)); FILL_LT.rotation_mode = 'QUATERNION'; FILL_LT.rotation_quaternion = (ct - FILL_LT.location).to_track_quat('-Z', 'Y')
    if os.environ.get('DBGPOS'): print('DBG t', round(t,2), 'whale', tuple(round(x,2) for x in HB['root'].matrix_world.translation), 'Mcalc', tuple(round(x,2) for x in M.translation), 'diver', tuple(round(x,2) for x in DIVER.root.matrix_world.translation), 'rig', tuple(round(x,2) for x in DIVER.rig.matrix_world.translation), flush=True)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = Vector(q_[0:3]), Vector(q_[3:6]), q_[6]
    sh = shake(t, 0.05 * smooth(TE - 0.3, TE, t) * (1 - smooth(TE + 0.4, TE + 1.0, t)) + 0.06 * smooth(T_SURF - 0.1, T_SURF, t) * (1 - smooth(T_SPIT + 0.5, T_SPIT + 1.2, t)), 3.0)
    look(cp + sh, ct + sh, lens, 11.0)
    S.view_settings.exposure = -0.9 * smooth(-0.3, 0.3, cp.z - SEA_Z) - 7.0 * smooth(TE + 1.6, TE + 2.1, t) * (1 - smooth(TE + 2.4, TE + 3.0, t))
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

