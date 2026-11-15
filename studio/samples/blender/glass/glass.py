# The glass floor cracks: Skydeck Chicago's Ledge (103rd floor, 1,353 ft). Blender Cycles, ONE continuous camera move (no cuts),
# camera resting about half the time, close-ups on the glass, real textures and sky light (Poly Haven), people kept small.
#   python3 glass.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
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

# ================================================================ the set: the Ledge on the 103rd floor, the tower, Chicago 412 m below
# World: the tower face is the plane y = 0 (inside the building is y > 0); the Ledge box sticks out toward -y. Ground z = 0.
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
Z0 = 412.4                                   # top of the Ledge floor: 1,353 ft
BW, BD, BH = 3.05, 1.31, 3.05                # box: 10 ft wide, sticks out 4.3 ft, 10 ft tall
T_CRACK0 = 0.0                               # frame one: a crack shoots across under his shoes
T_LAYERS = word_t(2, 4)                      # "three layers"
T_HEAT = word_t(3, 1)                        # "heated"
T_BLAST = word_t(3, 4)                       # "blasted with cold air"
T_COAT = word_t(4, 5)                        # "coating"
T_SHOES = word_t(4, 9)                       # "millions of shoes"
T_HIT = word_t(5, 4) + 0.05                  # "hits it too hard"
T_SPLINTER = word_t(6, 5)                    # "splintered"
T_FEET = word_t(6, 12)                       # "under people's feet"
T_NEVER = word_t(7, 11)                      # "never broke"
T_TONS = word_t(8, 7)                        # "five tons"
T_CARS = word_t(9, 3)                        # "parking two and a half cars"
T_AIR = word_t(9, 13)                        # "1,300 feet in the air"

# ---- sky: Poly Haven partly-cloudy sky HDRI (light + reflections) and a warm afternoon sun from the south-west
_wn = W_.node_tree; _env = _wn.nodes.new('ShaderNodeTexEnvironment')
_env.image = bpy.data.images.load(asset('kloofendal_48d_partly_cloudy_puresky/kloofendal_48d_partly_cloudy_puresky_2k.hdr'))
_mp = _wn.nodes.new('ShaderNodeMapping'); _mp.inputs['Rotation'].default_value = (0, 0, R(-70))
_wn.links.new(coord(_wn, 'Generated'), _mp.inputs['Vector']); _wn.links.new(_mp.outputs[0], _env.inputs['Vector'])
_wn.links.new(_env.outputs['Color'], WBG.inputs['Color']); WBG.inputs['Strength'].default_value = 1.0
SUN = light_at('sun', 'SUN', (0, 0, 1000), (0, 0, 0), 3.6, (1.0, 0.93, 0.82), 0.02); SUN.rotation_mode = 'XYZ'; SUN.rotation_euler = (R(52), 0, R(-32))
SUN.data.angle = R(1.0)
HAZE = (0.58, 0.66, 0.78)
def haze(m, far=2600.0, amt=0.85):
    """aerial perspective: things far from the camera fade toward the sky colour (cheap, no volume)"""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; cd = nt.nodes.new('ShaderNodeCameraData')
    k = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'EXPONENT', math_(nt, 'DIVIDE', cd.outputs['View Distance'], -far))), amt)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*HAZE, 1); em.inputs['Strength'].default_value = 1.0
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(k, mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ---- the tower: Willis Tower's nine bundled tubes in black glass and dark aluminium (we stand on the west face of a 108-floor tube)
def curtain_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    _geo = nt.nodes.new('ShaderNodeNewGeometry'); p = sepz(nt, _geo.outputs['Position'])                     # world position: pieces line up
    u = math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'ADD', p.outputs['X'], p.outputs['Y']), 1.524))       # 5-ft mullions
    v = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['Z'], 3.93))                                       # a floor every 3.93 m
    mull = math_(nt, 'MAXIMUM', math_(nt, 'GREATER_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.465),
                    math_(nt, 'LESS_THAN', v, 0.22))                                                         # mullion or spandrel band
    nt.links.new(mixc(nt, mull, (0.020, 0.018, 0.016), (0.035, 0.032, 0.030)), b.inputs['Base Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', mull, 0.5), 0.04), b.inputs['Roughness'])
    nt.links.new(math_(nt, 'SUBTRACT', 0.85, math_(nt, 'MULTIPLY', mull, 0.6)), b.inputs['Metallic'])
    b.inputs['Coat Weight'].default_value = 0.3; return m
CURTAIN = curtain_mat('curtain')
TUBE = 22.86; _tx = [-TUBE * 1.5, -TUBE * 0.5, TUBE * 0.5]; _ty = [TUBE * 0.5, TUBE * 1.5, TUBE * 2.5]
_th = [[442, 442, 368], [368, 368, 270], [270, 200, 200]]                  # floors 108 / 90 / 66 / 50 as metres
for i_ in range(3):
    for j_ in range(3):
        h_ = _th[j_][i_] if not (i_ == 1 and j_ == 0) else 442
        box(f'tube{i_}{j_}', (TUBE, TUBE, h_), (_tx[i_] + TUBE * 0.5, _ty[j_], h_ / 2), CURTAIN)
# our face (y = 0) gets a hole for the Ledge opening: the tube in front is split around it
TOWER = [o for o in bpy.data.objects if o.name.startswith('tube')]
_front = bpy.data.objects['tube10']; _front.hide_render = True                       # replace the front middle tube with pieces round the box
_fx0, _fx1 = _tx[1], _tx[1] + TUBE
for nm_, (x0, x1, z0, z1) in {'tf_l': (_fx0, -BW / 2, 0, 442), 'tf_r': (BW / 2, _fx1, 0, 442), 'tf_lo': (-BW / 2, BW / 2, 0, Z0 - 0.04), 'tf_hi': (-BW / 2, BW / 2, Z0 + BH, 442)}.items():
    box(nm_, (x1 - x0, TUBE, z1 - z0), ((x0 + x1) / 2, TUBE / 2, (z0 + z1) / 2), CURTAIN)
# ---- the Skydeck room behind the box: floor, ceiling, back wall, warm lights (mostly seen through the glass)
DECK_FLOOR = box('deck_floor', (BW + 0.6, 6.0, 0.1), (0, 3.0, Z0 - 0.05), noisy(mat('deckfloor', (0.10, 0.10, 0.11), 0.35), 30, 0.25))
box('deck_ceil', (BW + 0.6, 6.0, 0.1), (0, 3.0, Z0 + BH + 0.05), mat('deckceil', (0.35, 0.35, 0.36), 0.8))
box('deck_back', (BW + 0.6, 0.1, BH), (0, 6.0, Z0 + BH / 2), mat('deckback', (0.12, 0.12, 0.13), 0.6))
for sx_ in (-1, 1): box(f'deck_side{sx_}', (0.1, 6.0, BH), (sx_ * (BW / 2 + 0.3), 3.0, Z0 + BH / 2), mat(f'deckside{sx_}', (0.16, 0.16, 0.17), 0.6))
IN_LT = light_at('in_lt', 'AREA', (0, 2.5, Z0 + BH - 0.05), (0, 2.5, Z0), 400, (1.0, 0.86, 0.68), 2.0); IN_LT.visible_camera = False; IN_LT.visible_glossy = False

# ---- the Ledge: three 1/2-inch tempered glass layers laminated with clear interlayers, a thin clear coating on top;
# glass walls on three sides and a glass roof, thin dark metal edge trim. Low-iron glass, green only when seen edge-on.
def glass_mat(name, ior=1.52, absorb=0.6, tint=(0.80, 0.95, 0.90)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1, 1, 1, 1); b.inputs['Roughness'].default_value = 0.0; b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = ior
    b.inputs['Base Color'].default_value = (*[0.985 + 0.015 * c for c in tint], 1)    # a faint low-iron tint (a volume tint cost 5x the render time)
    # heat glow (tempering): object property 'heat' 0..1 adds an orange-hot emission
    em_c = nt.nodes.new('ShaderNodeBlackbody'); em_c.inputs['Temperature'].default_value = 1150
    nt.links.new(em_c.outputs[0], b.inputs['Emission Color']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'heat'), 0.45), b.inputs['Emission Strength'])
    return m
GLASS_M = glass_mat('glass'); INTER_M = glass_mat('interlayer', 1.48, 0.2, (0.95, 0.97, 0.92))
_ib = INTER_M.node_tree.nodes['Principled BSDF']; _ib.inputs['Roughness'].default_value = 0.25; _ib.inputs['Transmission Weight'].default_value = 0.85   # the interlayer reads as a thin pale line edge-on
WALL_M = glass_mat('wallglass', 1.52, 0.6)
TRIM_M = mat('trim', (0.06, 0.06, 0.065), 0.35, 0.8)
TG, TI, TC = 0.0127, 0.0015, 0.0015            # glass, interlayer, coating thickness (m)
LAYERS = []                                    # (object, rest z) top to bottom: coating, glass, inter, glass, inter, glass
_z = Z0
for k_, (nm_, th_, m_) in enumerate((('coat', TC, None), ('g1', TG, GLASS_M), ('i1', TI, INTER_M), ('g2', TG, GLASS_M), ('i2', TI, INTER_M), ('g3', TG, GLASS_M))):
    if nm_ == 'coat': m_ = None
    o = box('layer_' + nm_, (BW - 0.004, BD + 0.10, th_), (0, -BD / 2 + 0.05, _z - th_ / 2), m_ if m_ else mat('tmp', (1, 1, 1), 0.1)); o['heat'] = 0.0
    LAYERS.append([o, _z - th_ / 2]); _z -= th_ + 0.0003                   # hairline gaps: touching glass faces render black in Cycles
SLAB_BOT = _z
# the floor as one piece of glass for every shot except the layer close-ups: laminated layers are index-matched (no internal
# reflections), but separate boxes with air between them reflect at every face and the floor turned into a mirror
SLAB = box('slab', (BW - 0.004, BD + 0.10, LAYERS[1][1] + TG / 2 - SLAB_BOT), (0, -BD / 2 + 0.05, (LAYERS[1][1] + TG / 2 + SLAB_BOT) / 2), GLASS_M); SLAB['heat'] = 0.0
for sx_ in (-1, 1): tube(f'trim_b{sx_}', [(sx_ * BW / 2, 0.05, SLAB_BOT - 0.012), (sx_ * BW / 2, -BD, SLAB_BOT - 0.012)], 0.012, TRIM_M, seg=8)
tube('trim_bf', [(-BW / 2, -BD, SLAB_BOT - 0.012), (BW / 2, -BD, SLAB_BOT - 0.012)], 0.012, TRIM_M, seg=8)
WALLS = [box('wall_f', (BW, 0.038, BH), (0, -BD - 0.019, Z0 + BH / 2), WALL_M), box('roof', (BW, BD, 0.038), (0, -BD / 2, Z0 + BH + 0.019), WALL_M)]
for sx_ in (-1, 1): WALLS.append(box(f'wall_s{sx_}', (0.038, BD, BH), (sx_ * (BW / 2 + 0.019), -BD / 2, Z0 + BH / 2), WALL_M))
for o in WALLS: o['heat'] = 0.0
for sx_ in (-1, 1):
    for zz_ in (Z0 + BH + 0.04, Z0 + 0.005):
        tube(f'trim_{sx_}_{zz_:.0f}', [(sx_ * (BW / 2 + 0.04), 0.0, zz_), (sx_ * (BW / 2 + 0.04), -BD - 0.04, zz_)], 0.015, TRIM_M, seg=8)
    tube(f'trim_v{sx_}', [(sx_ * (BW / 2 + 0.04), -BD - 0.04, Z0), (sx_ * (BW / 2 + 0.04), -BD - 0.04, Z0 + BH + 0.04)], 0.015, TRIM_M, seg=8)
tube('trim_ft', [(-BW / 2 - 0.04, -BD - 0.04, Z0 + BH + 0.04), (BW / 2 + 0.04, -BD - 0.04, Z0 + BH + 0.04)], 0.015, TRIM_M, seg=8)

# ---- Chicago below: a street grid, blocks of buildings (one big mesh, window shader), the river, cars on the streets
def window_city(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    p = sepz(nt, coord(nt, 'Object'))
    u = math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'ADD', p.outputs['X'], p.outputs['Y']), 3.0))
    v = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['Z'], 3.8))
    win = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.33), math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', v, 0.55)), 0.3))
    var = tnoise(nt, coord(nt, 'Object'), 0.004, 2.0)
    wall = mixc(nt, var, (0.62, 0.58, 0.52), (0.30, 0.31, 0.34))
    nt.links.new(mixc(nt, win, wall, (0.10, 0.14, 0.18)), b.inputs['Base Color'])
    nt.links.new(mixc(nt, win, (0.8, 0.8, 0.8), (0.12, 0.12, 0.12)), b.inputs['Roughness'])
    return haze(m)
CITY_M = window_city('city'); ROOF_M = haze(noisy(mat('roofs', (0.30, 0.30, 0.30), 0.85), 0.05, 0.4))
GROUND_M = haze(noisy(mat('ground', (0.16, 0.16, 0.17), 0.9), 0.02, 0.3)); RIVER_M = haze(mat('river', (0.05, 0.10, 0.09), 0.08))
LAKE_M = haze(mat('lake', (0.06, 0.16, 0.22), 0.06))
prim('plane', 'ground', GROUND_M, loc=(0, 0, 0), size=1, scale=(16000, 16000, 1))
box('river', (6000, 60, 0.3), (0, -150, 0.2), RIVER_M)                         # the south branch of the Chicago River, in front of the tower
box('lake', (16000, 7000, 0.3), (0, 6200, 0.2), LAKE_M)                        # Lake Michigan far behind the tower
_bm = bmesh.new(); _rr = random.Random(5); _cx = []
for gx in range(-30, 31):
    for gy in range(-30, 25):
        x0 = gx * 120.0; y0 = gy * 120.0
        if -130 < y0 < -110 or (-90 < x0 < 90 and -60 < y0 < 90): continue          # river and the tower's own block
        d = math.hypot(x0, y0)
        for k in range(_rr.randint(2, 4)):
            w_ = _rr.uniform(25, 50); dd = _rr.uniform(25, 50); hx = x0 + _rr.uniform(-35, 35); hy = y0 + _rr.uniform(-35, 35)
            hmax = 230 * math.exp(-d / 1400) + 18
            h_ = max(10.0, _rr.random() ** 2.2 * hmax)
            r_ = bmesh.ops.create_cube(_bm, size=1.0)
            for v in r_['verts']: v.co = Vector((hx + v.co.x * w_, hy + v.co.y * dd, (v.co.z + 0.5) * h_))
CITY_ME = bpy.data.meshes.new('city'); _bm.to_mesh(CITY_ME); _bm.free(); CITY = obj('city', CITY_ME, CITY_M)
CITY.data.materials.append(ROOF_M)
for p_ in CITY.data.polygons:
    if p_.normal.z > 0.9: p_.material_index = 1
ROAD_M = haze(mat('road', (0.07, 0.07, 0.075), 0.7)); LINE_M = haze(mat('lane', (0.75, 0.72, 0.6), 0.6))
for g in range(-30, 31):
    box(f'road_x{g}', (7400, 16, 0.05), (0, g * 120 + 60, 0.08), ROAD_M); box(f'road_y{g}', (16, 7400, 0.05), (g * 120 + 60, 0, 0.08), ROAD_M)
# cars: strips of little cars per lane, each strip slides along its road (wrapped), so the streets move from frame one
CAR_COLS = [(0.6, 0.6, 0.62), (0.08, 0.08, 0.09), (0.55, 0.06, 0.05), (0.9, 0.9, 0.9), (0.10, 0.18, 0.40), (0.35, 0.35, 0.37)]
CAR_MS = [haze(mat(f'carp{i}', c, 0.3, 0.6, coat=1.0)) for i, c in enumerate(CAR_COLS)]
LANES = []
for li, (axis, g, side) in enumerate([(ax, g, sd) for ax in 'xy' for g in range(-6, 6) for sd in (-1, 1)]):
    bm_ = bmesh.new(); rr_ = random.Random(li * 13 + 1); n_ = 0
    for k in range(60):
        if rr_.random() < 0.45: continue
        s_ = k * 25.0 - 750; L_ = rr_.uniform(4.2, 5.0)
        c_ = bmesh.ops.create_cube(bm_, size=1.0)
        for v in c_['verts']:
            if axis == 'x': v.co = Vector((s_ + v.co.x * L_, g * 120 + 60 + side * 3.0 + v.co.y * 1.8, 0.75 + v.co.z * 1.3))
            else: v.co = Vector((g * 120 + 60 + side * 3.0 + v.co.x * 1.8, s_ + v.co.y * L_, 0.75 + v.co.z * 1.3))
        n_ += 1
    me_ = bpy.data.meshes.new(f'lane{li}'); bm_.to_mesh(me_); bm_.free(); o = obj(f'lane{li}', me_, CAR_MS[li % len(CAR_MS)])
    LANES.append((o, axis, side * (11 + 3 * (li % 3))))
def city_at(t):
    for o, axis, v in LANES:
        d = (v * t) % 25.0
        o.location = (d, 0, 0) if axis == 'x' else (0, d, 0)

TRIMS = [o for o in bpy.data.objects if o.name.startswith('trim')]

# ================================================================ the coating and its cracks, the tempering (heat + air), shoes, the ball, the cars
# Coating cracks are a shader on the thin top layer (object space): two spiderwebs (radial lines + broken rings) and a fine
# craze of "thousands of pieces"; each grows by an object property so the frame code can drive them: w0 (the opening crack by
# his shoes), w1 (the hit), cz (the 2019 splinter spreading over the whole floor from the hit).
COAT = LAYERS[0][0]
def coat_mat():
    m = bpy.data.materials.new('coating'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1, 1, 1, 1); b.inputs['Roughness'].default_value = 0.03; b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.5
    p = sepz(nt, coord(nt, 'Object')); X, Y = p.outputs['X'], p.outputs['Y']
    def web(cx, cy, prop, seed, n_rad=17.0):
        dx = math_(nt, 'SUBTRACT', X, cx); dy = math_(nt, 'SUBTRACT', Y, cy)
        r = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dy, dy)))
        ang = math_(nt, 'ARCTAN2', dy, dx)
        wig = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', tnoise(nt, coord(nt, 'Object'), 9.0 + seed, 3.0), 0.5), 0.5)
        f = math_(nt, 'FRACT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'ADD', ang, wig), n_rad / (2 * math.pi)), seed * 0.37))
        dl = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 0.5, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', f, 0.5))), 2 * math.pi / n_rad), r)
        rad = math_(nt, 'LESS_THAN', dl, 0.0011)
        g = math_(nt, 'FRACT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'LOGARITHM', math_(nt, 'ADD', r, 0.012), 2.718), 4.0), math_(nt, 'MULTIPLY', wig, 0.6)))
        dr = math_(nt, 'MULTIPLY', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', 0.5, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', g, 0.5))), 4.0), r)
        brk = math_(nt, 'GREATER_THAN', tnoise(nt, coord(nt, 'Object'), 23.0 + seed, 2.0), 0.47)
        ring = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', dr, 0.0009), brk)
        inside = math_(nt, 'LESS_THAN', r, objattr(nt, prop))
        return math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', rad, ring), inside), r
    w0, _ = web(0.25, -0.02, 'w0', 1.0)                                   # under his feet
    w1, r1 = web(-0.55, 0.15, 'w1', 2.0, 21.0)
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 55.0; nt.links.new(coord(nt, 'Object'), vo.inputs['Vector'])
    cz = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', vo.outputs['Distance'], 0.022), math_(nt, 'LESS_THAN', r1, objattr(nt, 'cz')))
    scm = nt.nodes.new('ShaderNodeMapping'); scm.inputs['Scale'].default_value = (60.0, 2.0, 1.0); scm.inputs['Rotation'].default_value = (0, 0, 0.3)
    nt.links.new(coord(nt, 'Object'), scm.inputs['Vector'])
    scn = nt.nodes.new('ShaderNodeTexNoise'); scn.inputs['Scale'].default_value = 3.0; scn.inputs['Detail'].default_value = 1.0; nt.links.new(scm.outputs[0], scn.inputs['Vector'])
    scuff = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', scn.outputs['Fac'], 0.72), math_(nt, 'MULTIPLY', objattr(nt, 'sc'), 0.35))
    mask = math_(nt, 'MAXIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MAXIMUM', w0, w1), cz), scuff)
    cr = nt.nodes.new('ShaderNodeBsdfPrincipled'); cr.inputs['Base Color'].default_value = (0.95, 0.97, 0.98, 1); cr.inputs['Roughness'].default_value = 0.25
    cr.inputs['Transmission Weight'].default_value = 0.35; cr.inputs['Coat Weight'].default_value = 0.0
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(mask, mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(cr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
COAT.data.materials.clear(); COAT.data.materials.append(coat_mat())
for k_ in ('w0', 'w1', 'cz', 'sc'): COAT[k_] = 0.0
# the coating slides on during "on top sits a thin clear coating" (it is there from frame one too; it lifts away for the layer shot)

# ---- tempering: hot glow (glass 'heat' property) and blasts of cold air (blue streaks above and below the slab)
def air_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    p = sepz(nt, coord(nt, 'Object'))
    st = nt.nodes.new('ShaderNodeTexNoise'); st.inputs['Scale'].default_value = 6.0; st.inputs['Detail'].default_value = 3.0
    cv = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', p.outputs['X'], 0.4), math_(nt, 'MULTIPLY', objattr(nt, 'tw'), -3.0)), cv.inputs['X'])
    nt.links.new(math_(nt, 'MULTIPLY', p.outputs['Y'], 9.0), cv.inputs['Y']); nt.links.new(p.outputs['Z'], cv.inputs['Z']); nt.links.new(cv.outputs[0], st.inputs['Vector'])
    k = math_(nt, 'MULTIPLY', math_(nt, 'POWER', st.outputs['Fac'], 3.0), objattr(nt, 'a'))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (0.55, 0.80, 1.0, 1); e_.inputs['Strength'].default_value = 6.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', k, 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
AIR = []
for k_, zz in enumerate((Z0 + 0.03, SLAB_BOT - 0.03)):
    o = box(f'air{k_}', (BW, BD, 0.02), (0, -BD / 2, zz), air_mat(f'air{k_}')); o['a'] = 0.0; o['tw'] = 0.0; AIR.append(o)

# ---- sneakers (the shoes walking over the coating, and his feet)
SOLE_M = mat('sole', (0.78, 0.76, 0.72), 0.7); LACE_M = mat('lace', (0.95, 0.95, 0.95), 0.7)
UPPER_MS = [noisy(mat(f'upper{i}', c, 0.65, sheen=0.3), 300, 0.12) for i, c in enumerate([(0.08, 0.08, 0.09), (0.55, 0.06, 0.05), (0.85, 0.85, 0.85), (0.12, 0.20, 0.42), (0.40, 0.33, 0.25)])]
def sneaker(name, um, parent=None, loc=(0, 0, 0), yaw=0.0, s=1.0):
    """one rounded shoe: a foot-shaped body (wider at the toes, narrow heel, flat bottom), the bottom band is a thin
    off-white midsole, the rest the upper colour. No separate sole slab (it read as a white board under the feet)."""
    root = empty(name, parent, loc); root.rotation_euler = (0, 0, yaw); root.scale = (s, s, s)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        w = 0.050 * (1.0 + 0.18 * (-y)) if y < 0 else 0.050 * (1.0 - 0.22 * y)                    # toes (-y) wider than the heel
        h = 0.075 if y > -0.35 else 0.075 * (1 - 0.55 * (-y - 0.35) / 0.65)                      # lower toe box
        z = max(z, -0.15) * h + 0.15 * h
        v.co = Vector((x * w, y * 0.138, max(0.0, z)))
    bm.normal_update(); me = bpy.data.meshes.new(name + '_m'); bm.to_mesh(me); bm.free()
    o = obj(name + '_body', me, um, parent=root); me.materials.append(SOLE_M)
    for p_ in me.polygons:
        p_.use_smooth = True
        if sum(me.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) < 0.010: p_.material_index = 1
    tube(name + '_lace', [(0.0, -0.015, 0.088), (0.0, -0.065, 0.074)], 0.009, LACE_M, root, seg=6)
    return root
STEPS = []                                                       # shoes landing on the coating one after another (beat 4)
for i in range(8):
    sh = sneaker(f'step{i}', UPPER_MS[i % len(UPPER_MS)], loc=(-1.1 + 0.32 * i, -0.45 - 0.35 * (i % 2), Z0), yaw=R(-8 + 16 * h1(i)))
    STEPS.append(sh)

# ---- the ball that hits the coating too hard (a bowling ball: the classic drop test)
BALL_M = mat('ball', (0.05, 0.08, 0.30), 0.12, coat=1.0)
_bn = BALL_M.node_tree; _bb = _bn.nodes['Principled BSDF']
_bn.links.new(mixc(_bn, tnoise(_bn, coord(_bn, 'Object'), 6.0, 8.0, 4.0), (0.03, 0.04, 0.20), (0.25, 0.05, 0.45)), _bb.inputs['Base Color'])
BALL = prim('uv_sphere', 'ball', BALL_M, loc=(-0.55, -BD / 2 + 0.05 + 0.15, Z0 + 3), radius=0.109, segments=48, ring_count=24)
for k_, (hx, hz) in enumerate(((0.0, 0.07), (-0.022, 0.03), (0.022, 0.03))):
    prim('uv_sphere', f'hole{k_}', mat(f'hole{k_}', (0.01, 0.01, 0.01), 0.6), BALL, loc=(hx, -0.105, hz), scale=(0.011, 0.006, 0.011), segments=12, ring_count=8)

# ---- the payoff: the floor stretches into a long glass shelf and two and a half cars are parked on it
SHELF = box('shelf', (8.0, 14.0, 0.04), (0, -7.0, Z0 - 0.02), GLASS_M); SHELF.hide_render = True
PAINTS = [mat('paint0', (0.55, 0.04, 0.04), 0.25, 0.4, coat=1.0), mat('paint1', (0.85, 0.85, 0.87), 0.25, 0.4, coat=1.0), mat('paint2', (0.06, 0.16, 0.42), 0.25, 0.4, coat=1.0)]
TIRE_M = mat('tire', (0.02, 0.02, 0.02), 0.85); RIM_M = mat('rim', (0.7, 0.7, 0.72), 0.25, 1.0); WIN_M = mat('carwin', (0.02, 0.03, 0.04), 0.05, coat=1.0)
LAMP_M = mat('lamp', (1.0, 0.95, 0.85), 0.1, emit=(1.0, 0.95, 0.85), estr=1.0); TAIL_M = mat('tail', (0.6, 0.02, 0.02), 0.2)
def car(name, paint, half=False):
    root = empty(name)
    L_ = 4.6; ln = L_ / 2 if half else L_; y0 = -L_ / 2; y1 = y0 + ln
    box(name + '_body', (1.80, ln, 0.62), (0, (y0 + y1) / 2, 0.62), paint, bv=0.10, parent=root)
    cab_y1 = min(y1, 1.0) if not half else min(y1, 0.0)
    if cab_y1 > -1.3: box(name + '_cab', (1.62, cab_y1 + 1.3, 0.55), (0, (cab_y1 - 1.3) / 2, 1.18), WIN_M, bv=0.12, parent=root)
    for wy in (-1.45, 1.45):
        if half and wy > 0: continue
        for wx in (-0.86, 0.86):
            prim('uv_sphere', f'{name}_t{wx}{wy}', TIRE_M, root, loc=(wx, wy, 0.33), scale=(0.11, 0.33, 0.33), segments=24, ring_count=12)
            prim('uv_sphere', f'{name}_r{wx}{wy}', RIM_M, root, loc=(wx * 1.05, wy, 0.33), scale=(0.04, 0.2, 0.2), segments=16, ring_count=8)
    for lx in (-0.62, 0.62):
        box(f'{name}_hl{lx}', (0.32, 0.04, 0.12), (lx, y0 + 0.01, 0.72), LAMP_M, parent=root)
        if not half: box(f'{name}_tl{lx}', (0.32, 0.04, 0.12), (lx, y1 - 0.01, 0.74), TAIL_M, parent=root)
    if half: box(name + '_cut', (1.78, 0.02, 0.6), (0, y1, 0.62), mat(name + '_cutm', (0.25, 0.25, 0.27), 0.6, 0.6), parent=root)
    return root
# the cars: Poly Haven's CC0 "covered_car" (a real car under a fitted cover), two whole and one cut in half (bisected, capped dark)
def covered_car(name, half=False):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=asset('covered_car/covered_car_1k.gltf'))
    new_ = [o for o in bpy.data.objects if o not in before]; root = empty(name)
    for o in new_:
        if o.type != 'MESH': o.hide_render = True; continue
        mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
        if half:
            bm_ = bmesh.new(); bm_.from_mesh(o.data)
            bmesh.ops.bisect_plane(bm_, geom=bm_.verts[:] + bm_.edges[:] + bm_.faces[:], plane_co=(0, 0.0, 0), plane_no=(0, 1, 0), clear_outer=True)
            bm_.to_mesh(o.data); bm_.free()
            if not o.data.vertices: o.hide_render = True
    if half: box(name + '_cap', (1.74, 0.02, 1.2), (0.05, -0.01, 0.75), mat(name + '_capm', (0.05, 0.05, 0.055), 0.8), parent=root)
    return root
CARS = [covered_car('car0'), covered_car('car1'), covered_car('car2', half=True)]
CAR_REST = [(-2.1, -6.0), (2.1, -6.6), (0.0, -11.2)]
def show_tree(o, on):
    st_ = [o]
    while st_:
        x = st_.pop(); x.hide_render = not on; st_.extend(x.children)

# ================================================================ people: the house MakeHuman man (man.blend) with the CC0 middle-age skin, sneakers on
# his feet (parented to the foot bones), posed on his rig and baked per pose (see the boat Short). Kids are the same man scaled.
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
# skin: the CC0 middle-age male skin with stubble (MakeHuman community skins02), as approved on the face test
_skd = next((d for d in (os.path.join(HERE, 'assets', 'jartur'), '/root/vt/mh/packs/keep/r2/skins/jartur69_middleage_slavic_male_with_genitals_and_beard') if os.path.isdir(d)), None)
if _skd:
    _ski = bpy.data.images.load(os.path.join(_skd, 'Jartur_mid_old_Slavic_Male_with_Genitals_and_Beard_lsdif_lighter_2k.jpg'))
    for mn in ('Human.body', 'Human.ears', 'Human.lips'):
        m = bpy.data.materials.get(mn)
        if not m: continue
        t = m.node_tree; [t.nodes.remove(n) for n in list(t.nodes) if n.bl_idname != 'ShaderNodeOutputMaterial']
        b = t.nodes.new('ShaderNodeBsdfPrincipled'); t.links.new(b.outputs[0], t.nodes['Material Output'].inputs['Surface'])
        im = t.nodes.new('ShaderNodeTexImage'); im.image = _ski; t.links.new(im.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.45; b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2); b.inputs['Subsurface Scale'].default_value = 0.012
# hair: MakeHuman's own short02, darkened (owner: "put the old hair back on")
_hm = bpy.data.materials.get('Human.short02')
if _hm:
    t = _hm.node_tree; hb_ = next(n for n in t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    src_ = hb_.inputs['Base Color'].links[0].from_socket if hb_.inputs['Base Color'].links else None
    mx_ = t.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs['Factor'].default_value = 1.0
    if src_: t.links.new(src_, mx_.inputs[6])
    mx_.inputs[7].default_value = (0.16, 0.10, 0.07, 1); t.links.new(mx_.outputs[2], hb_.inputs['Base Color']); hb_.inputs['Roughness'].default_value = 0.6
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
# sneakers on his feet: built round each foot's own vertices (rest pose), parented to the foot bone so they walk with him
def _foot_box(side):
    vg = BODY.vertex_groups.get('foot' + side); pts = []
    for v in BODY.data.vertices:
        if vg and any(g.group == vg.index and g.weight > 0.4 for g in v.groups): pts.append(BODY.matrix_world @ v.co)
    for nm in [g.name for g in BODY.vertex_groups if g.name.startswith('toe') and g.name.endswith(side)]:
        gi_ = BODY.vertex_groups[nm].index; pts += [BODY.matrix_world @ v.co for v in BODY.data.vertices if any(g.group == gi_ and g.weight > 0.4 for g in v.groups)]
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0.0)), (max(xs) - min(xs), max(ys) - min(ys), max(zs))
FEET_SHOES = []
_FB = {sd: _foot_box(sd) for sd in ('.L', '.R')}
# the bare feet go: their faces are removed from the body so no toes ever poke out of a shoe as it bends (the shoe IS the foot)
_bmf = bmesh.new(); _bmf.from_mesh(BODY.data); _dl = _bmf.verts.layers.deform.verify()
_footg = {g.index for g in BODY.vertex_groups if g.name.startswith(('foot', 'toe'))}
_kill = [f for f in _bmf.faces if all(sum(w for gi_, w in v[_dl].items() if gi_ in _footg) > 0.5 for v in f.verts)]
bmesh.ops.delete(_bmf, geom=_kill, context='FACES'); _bmf.to_mesh(BODY.data); _bmf.free(); print('feet faces removed', len(_kill))
for side in ('.L', '.R'):
    c_, (wx_, ly_, hz_) = _FB[side]
    sh = sneaker('shoe' + side, UPPER_MS[0], loc=(c_.x, c_.y + 0.005, -0.004), s=1.0); sh.scale = ((wx_ + 0.018) / 0.10, (ly_ + 0.02) / 0.276, max(1.0, (hz_ + 0.012) / 0.09))
    bpy.context.view_layer.update(); mw = sh.matrix_world.copy(); sh.parent = RIG; sh.parent_type = 'BONE'; sh.parent_bone = 'foot' + side; sh.matrix_world = mw
    FEET_SHOES.append(sh)
# ---- poses: bone rotations (radians). Front is -Y; legs swing forward with -X, arms forward with +X, L arm out with +Z, R arm out with -Z
POSE_BONES = ['upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'upperarm01.L', 'upperarm01.R', 'lowerarm01.L', 'lowerarm01.R', 'spine01', 'spine03', 'neck01', 'foot.L', 'foot.R']
def set_pose(d):
    for n in POSE_BONES:
        b = PB[n]; b.rotation_mode = 'XYZ'; b.rotation_euler = d.get(n, (0, 0, 0))
def p_stand(ph=0.0):
    return {'upperarm01.L': (0.04 * math.sin(ph), 0, -0.55), 'upperarm01.R': (0.04 * math.sin(ph + 1), 0, 0.55), 'lowerarm01.L': (0, 0, -0.15), 'lowerarm01.R': (0, 0, 0.15)}   # arms down at his sides (rest is an A-pose; checked on a front render)
def p_gait(ph, leg, knee, arm, elbow, lean):
    s_ = math.sin(ph)
    return {'upperleg01.L': (-leg * s_, 0, 0), 'upperleg01.R': (leg * s_, 0, 0),
            'lowerleg01.L': (knee * max(0.0, math.sin(ph - 1.2)) + 0.1, 0, 0), 'lowerleg01.R': (knee * max(0.0, math.sin(ph + math.pi - 1.2)) + 0.1, 0, 0),
            'upperarm01.L': (-arm * s_, 0, -0.5), 'upperarm01.R': (arm * s_, 0, 0.5), 'lowerarm01.L': (elbow, 0, 0), 'lowerarm01.R': (elbow, 0, 0),
            'spine01': (lean, 0, 0)}
def p_brace(ph=0.0):
    return {'upperarm01.L': (0.45, 0, -0.35 + 0.05 * math.sin(ph)), 'upperarm01.R': (0.45, 0, 0.35 - 0.05 * math.sin(ph)), 'lowerarm01.L': (0.9, 0, 0), 'lowerarm01.R': (0.9, 0, 0),
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
         'brace': (2, p_brace), 'look': (1, lambda ph=0.0: dict(p_stand(), **{'neck01': (0.55, 0, 0), 'spine03': (0.2, 0, 0)})), 'climb': (4, p_climb), 'tread': (4, p_tread), 'jump': (1, p_jump), 'wave': (4, p_wave)}
PARTS = [BODY, SUIT, HAIR, EYES, LASH, BROW]
def _shoe_parts(): return [c for s_ in FEET_SHOES for c in s_.children_recursive if c.type == 'MESH']
def bake(name, vest):
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); mats = []
    for o in PARTS + _shoe_parts():
        ev = o.evaluated_get(dg); me = ev.to_mesh(); nf0 = len(bm.faces); nv0 = len(bm.verts)
        bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts[nv0:])
        for f in bm.faces[nf0:]: f.material_index += len(mats); f.smooth = True
        mats += list(o.data.materials); ev.to_mesh_clear()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in mats: me.materials.append(m_)
    return me
BAKED = {}
NEED = {False: ('stand', 'walk', 'brace', 'look')}
for vest_, modes in NEED.items():
    for md_ in modes:
        n_, fn = POSES[md_]
        for k in range(n_):
            set_pose(fn(2 * math.pi * k / n_)); bpy.context.view_layer.update(); BAKED[(vest_, md_, k)] = bake(f'man_{md_}{k}{"v" if vest_ else ""}', vest_)
set_pose({}); bpy.context.view_layer.update()
SLOT_SKIN = 0; SLOT_SHORTS = len(BODY.data.materials); SLOT_SHIRT = SLOT_SHORTS + 1
SLOT_UPPER = sum(len(o.data.materials) for o in PARTS) + 1    # each sneaker: sole, upper, lace (left shoe's upper slot)
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


def show_fig(p, on):
    stack = [p['root']]
    while stack:
        o = stack.pop(); o.hide_render = not on; stack.extend(o.children)
# ---- the cast: him (on the Ledge from frame one), and the 2019 group (a mum and two kids, plus him) for the splinter
HIM = figure('him', 3, loc=(0.25, -0.62, Z0), yaw=-math.pi / 2)
GROUP = [figure('mum', 21, loc=(-0.75, -0.55, Z0), yaw=-math.pi / 2 + 0.3), figure('kid1', 22, loc=(-0.2, -0.85, Z0), yaw=-math.pi / 2 - 0.2, scale=0.68),
         figure('kid2', 23, loc=(0.75, -0.95, Z0), yaw=-math.pi / 2 + 0.1, scale=0.6)]
for p in GROUP: show_fig(p, False)

CROWD = [figure(f'c{i}', 40 + i, loc=(-1.1 + 0.42 * i, 1.5, Z0), yaw=-math.pi / 2) for i in range(6)]
for p in CROWD: show_fig(p, False)
for c in _shoe_parts(): c.hide_render = True

# ================================================================ timing and the camera (one take: rests on each idea, moves between them)
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))
V = TM['voice']; Zf = Z0
# keys: (time, position, target, lens, f-stop)
K = [
    (0.00, (1.05, -1.25, Zf + 1.05), (0.20, -0.62, Zf + 0.02), 24, 8),        # frame one: low in the box, the crack shooting out from his feet
    (1.90, (1.10, -1.25, Zf + 1.20), (0.15, -0.60, Zf + 0.20), 24, 8),        # rest, a slow rise
    (3.70, (9.0, -5.0, Zf + 1.8), (0.00, -1.0, Zf - 3.5), 24, 8),        # outside: him in the glass box on the tower, Chicago far below
    (5.70, (9.5, -5.4, Zf + 1.5), (0.00, -1.0, Zf - 3.9), 24, 8),        # rest
    (6.70, (-0.75, -1.10, Zf + 1.60), (-0.45, -2.40, 0.0), 24, 5),            # in the box beside him, straight down through the cracking floor
    (8.80, (-0.72, -1.05, Zf + 1.25), (-0.45, -2.40, 0.0), 24, 5),            # rest, pushing down
    (9.90, (1.80, -1.62, Zf + 0.10), (1.40, -1.22, Zf - 0.04), 50, 11),       # the slab's edge: the layers
    (13.30, (1.82, -1.64, Zf + 0.10), (1.40, -1.22, Zf - 0.04), 50, 11),      # rest (layers part and press back)
    (18.40, (1.86, -1.68, Zf + 0.11), (1.40, -1.22, Zf - 0.04), 50, 11),    # rest through the heat and the air
    (19.70, (1.40, -1.22, Zf + 0.20), (0.00, -0.55, Zf), 28, 8),              # up to the top surface: the coating, the shoes
    (23.30, (1.30, -1.18, Zf + 0.24), (-0.10, -0.55, Zf), 28, 8),             # rest
    (24.30, (0.55, -1.20, Zf + 0.36), (-0.55, -0.46, Zf), 30, 8),             # the ball comes down
    (26.30, (0.45, -1.15, Zf + 0.30), (-0.55, -0.46, Zf), 30, 8),             # rest on the web
    (27.40, (-1.80, -0.80, Zf + 0.07), (-1.30, -0.48, Zf - 0.02), 45, 11),  # at the edge: only the top layer cracked
    (28.90, (-1.82, -0.82, Zf + 0.07), (-1.30, -0.48, Zf - 0.02), 45, 11),  # rest
    (30.40, (0.10, 2.60, Zf + 1.55), (0.00, -0.70, Zf + 0.55), 24, 8),        # inside the Skydeck behind the group (backs to us)
    (34.40, (0.05, 2.30, Zf + 1.45), (0.00, -0.70, Zf + 0.40), 24, 8),        # rest while it splinters
    (35.60, (0.35, -0.95, Zf - 1.30), (0.20, -0.55, Zf + 0.20), 22, 8),       # under the box, looking up through the floor
    (38.40, (0.30, -0.90, Zf - 1.20), (0.15, -0.55, Zf + 0.20), 22, 8),       # rest: cracked top, glass whole
    (39.40, (0.90, 0.80, Zf + 1.25), (0.00, -0.70, Zf), 28, 8),               # the empty cracked floor
    (41.80, (0.80, 0.70, Zf + 1.20), (0.00, -0.70, Zf), 28, 8),               # rest
    (43.20, (6.50, -15.0, Zf + 4.0), (0.00, -6.50, Zf + 0.5), 30, 8),         # the shelf and the cars
    (44.90, (9.00, -20.0, Zf + 3.0), (0.00, -7.00, Zf + 0.5), 30, 8),         # rest
    (46.60, (150.0, -450.0, 200.0), (0.00, -6.00, 215.0), 30, 8),      # way out: the shelf on the tower, the street far below
    (47.60, (156.0, -462.0, 196.0), (0.00, -6.00, 215.0), 30, 8),      # rest
    (END, (1.05, -1.25, Zf + 1.05), (0.20, -0.62, Zf + 0.02), 24, 8),         # back to frame one (loop)
]
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    t0, t1 = ts[i], ts[i + 1]; u = clamp((t - t0) / (t1 - t0), 0, 1)
    def tan(j):
        if j in REST: return vs[j] * 0                                     # zero speed at a rest key: it eases in and out, no overshoot
        a_, b_ = max(0, j - 1), min(n - 1, j + 1)
        return (vs[b_] - vs[a_]) / (ts[b_] - ts[a_]) * (t1 - t0)
    m0, m1 = tan(i), tan(i + 1); u2, u3 = u * u, u * u * u
    return vs[i] * (2 * u3 - 3 * u2 + 1) + m0 * (u3 - 2 * u2 + u) + vs[i + 1] * (-2 * u3 + 3 * u2) + m1 * (u3 - u2)
REST = set(range(len(K)))                                           # every key eases in and out: the camera arrives and rests
def cam_at(t):
    ts = [k[0] for k in K]; P = [Vector(k[1]) for k in K]; Q = [Vector(k[2]) for k in K]
    p = herm(ts, P, t); q = herm(ts, Q, t); ln = herm(ts, [Vector((k[3], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x
    sh = shake(t, 0.004, 5.0, 0.6) * (1.0 if p.z > Zf - 2 else 25.0)              # a hand-held breath (bigger when far out)
    if T_HIT < t < T_HIT + 0.5: sh += shake(t, 0.012 * (1 - (t - T_HIT) / 0.5), 2.0, 14.0)
    if T_SPLINTER < t < T_SPLINTER + 0.6: sh += shake(t, 0.02 * (1 - (t - T_SPLINTER) / 0.6), 3.0, 12.0)
    look_down = 6.2 < t < 9.3
    return p + sh, q + sh * 0.5, ln, fs, (Vector((0, 1, 0)) if look_down else None)

# ---- what everything does at time t
def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    city_at(t)
    # the edge trims would sit between the camera and the slab in the cross-section shots: out of the way then
    for o in TRIMS + WALLS: o.hide_render = (9.3 < t < 19.2) or (26.8 < t < 29.6)
    # cracks: the opening crack at his feet (frame one), cleared once we leave him; the hit's web; the 2019 splinter
    COAT['w0'] = 0.0 if t > 9.0 else 0.18 + 0.55 * ease_out(t / 1.4) + 0.3 * ease_io((t - 6.6) / 1.6)   # already running at frame one
    COAT['w1'] = 0.0 if t < T_HIT else 0.06 + 0.42 * ease_out((t - T_HIT) / 0.25)
    COAT['cz'] = 0.0 if t < T_SPLINTER else 2.6 * ease_out((t - T_SPLINTER) / 1.3)
    if t > 46.8: COAT['w1'] = COAT['cz'] = 0.0                                  # far away: the floor is whole again for the loop
    # the layers: the coating lifts away, the three glass layers part (exploded) and press back; the coating returns on "coating"
    layered = 9.3 < t < 20.4 or 26.8 < t < 29.6                         # separate layers only in the close-ups
    SLAB.hide_render = layered
    for o, _ in LAYERS[1:]: o.hide_render = not layered
    part = win(t, T_LAYERS - 0.6, 12.6, 0.7)
    coat_off = win(t, 9.4, T_COAT, 0.6)
    for k_, (o, z_) in enumerate(LAYERS):
        o.location.z = z_ - 0.028 * part * k_ + (0.06 * coat_off if k_ == 0 else 0.0)
        o.location.x = (1.8 * coat_off if k_ == 0 else 0.0)
        if k_ == 0: o.hide_render = coat_off > 0.97
    # tempering: glow then the cold blast
    heat = ease_io((t - (T_HEAT - 0.2)) / 1.0) * (1 - ease_io((t - (T_BLAST + 0.3)) / 1.4))
    for o, _ in LAYERS[1:]: o['heat'] = heat
    SLAB['heat'] = heat
    for o in AIR: o['a'] = win(t, T_BLAST - 0.1, T_BLAST + 2.3, 0.3); o['tw'] = t; o.hide_render = o['a'] < 0.01
    # "millions of shoes": a time-lapse crowd hurrying in and out over the floor, scuffs flashing on the coating and fading
    cr_on = T_COAT + 0.3 < t < 23.7
    for i_, p in enumerate(CROWD):
        show_fig(p, cr_on)
        if not cr_on: continue
        ph = ((t - T_COAT) * 0.9 + i_ * 0.37) % 1.0; y_ = 1.4 - 2.4 * math.sin(ph * math.pi)        # out to the glass and back in
        p['root'].location = (-1.1 + 0.42 * i_, y_, Z0); face(p, -math.pi / 2 if ph < 0.5 else math.pi / 2); pose(p, 'walk', t * 2.5)
    COAT['sc'] = win(t, T_SHOES - 0.3, 23.5, 0.4) * (0.6 + 0.4 * math.sin(t * 9))
    for i_, sh in enumerate(STEPS):
        show_tree(sh, False); continue
        tl = T_SHOES - 0.4 + 0.16 * i_; u = t - tl
        on = -0.35 < u < 0.75; show_tree(sh, on)
        sh.location.z = Zf + 0.002 + (0.18 * ease_io(-u / 0.35) if u < 0 else 0.0) + (0.22 * ease_io((u - 0.45) / 0.3) if u > 0.45 else 0.0)
    # the ball: dropped from 1.2 m, hits at T_HIT, one small hop, rolls off toward the room
    td = math.sqrt(2 * 1.2 / 9.81); show_tree(BALL, T_HIT - td - 0.05 < t < 26.8)
    if t < T_HIT: bz = 1.2 - 0.5 * 9.81 * max(0.0, t - (T_HIT - td)) ** 2
    else: u = t - T_HIT; bz = max(0.0, 0.9 * u - 0.5 * 9.81 * u * u)
    BALL.location = (-0.55 + 0.12 * max(0.0, t - T_HIT - 0.2), -0.455 + 0.08 * max(0.0, t - T_HIT - 0.2), Zf + 0.109 + bz)
    BALL.rotation_euler = (0.0, 1.1 * max(0.0, t - T_HIT - 0.2), 0.0)
    # people: him from frame one until we go to the layers, back for the loop; the 2019 group for the splinter
    show_fig(HIM, t < 9.2 or t > 47.0); pose(HIM, 'look', t)
    grp_on = 28.6 < t < 39.2
    for i_, p in enumerate(GROUP + [HIM]):
        if p is HIM and not grp_on: continue
        if p is not HIM: show_fig(p, grp_on)
        if not grp_on: continue
        base = p['root']['home'] if 'home' in p['root'] else None
        if base is None: p['root']['home'] = tuple(p['root'].location); base = p['root']['home']
        back = ease_io((t - (T_NEVER - 1.8 + 0.25 * i_)) / 2.2)
        p['root'].location = (base[0], base[1] + 2.4 * back, base[2])
        if t < T_SPLINTER + 0.15: pose(p, 'look', t)
        elif back <= 0.0: pose(p, 'brace', t)
        elif back < 1.0: face(p, math.pi / 2); pose(p, 'walk', t)
        else: pose(p, 'stand', t)
    if grp_on: show_fig(HIM, True); HIM['root'].location = (0.25, HIM['root'].location.y, Zf)
    else: HIM['root'].location = (0.25, -0.62, Zf); face(HIM, -math.pi / 2)
    # the payoff: the floor stretches into a long shelf, two and a half cars drop onto it
    sh_on = T_CARS - 0.9 < t < 47.4; SHELF.hide_render = not sh_on
    SHELF.scale.y = max(0.02, ease_out((t - (T_CARS - 0.9)) / 0.7)); SHELF.location.y = -0.1 - 7.0 * SHELF.scale.y
    for i_, (c, (cx, cy)) in enumerate(zip(CARS, CAR_REST)):
        tl = T_CARS + 0.35 * i_; on = tl - 0.45 < t < 47.4; show_tree(c, on)
        u = t - tl; z = 2.4 * ease_io(-u / 0.45) if u < 0 else 0.03 * math.exp(-u * 6) * math.sin(u * 30)
        c.location = (cx, cy, Zf + z); c.rotation_euler = (0, 0, R(4 - 8 * h1(i_)))
    # Skydeck light only while it matters (it can glow through the glass at night shots; it is day, keep it gentle)
    IN_LT.data.energy = 400

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear(); CAM.data.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, fs, up = cam_at(tt_); look(cp, ct, ln, fs, up=up); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
    cp, ct, ln, fs, up = cam_at(t)
    if not (t > d and t < END - d): look(cp, ct, ln, fs, up=up)
if os.environ.get('CHKCAM'):                                             # debug: a fixed camera for checks  "x,y,z,tx,ty,tz,lens"
    _frame1 = frame; _cks = [[float(v) for v in c.split(',')] for c in os.environ['CHKCAM'].split(';')]
    def frame(f):
        _frame1(f); CAM.animation_data_clear(); c = _cks[int(os.environ.get('CHKI', '0'))]
        look(Vector(c[:3]), Vector(c[3:6]), c[6], 8.0)
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

