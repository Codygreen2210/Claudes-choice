# What if the Sun blinked out? (Blender, Cycles), shot in FIRST PERSON: "you" are the camera (only your hands and forearms show).
# Sets far apart in one scene: space (the Sun, Earth on its orbit, frozen Earth by Pluto), the back porch over a yard with a pond and
# a lake (day / night / frost), and the ocean cutaway under the ice with a hot vent and its microbes. No gore, nobody hurt.
#   python3 sunz.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
# Needs man.blend (../foot/man_build.py) beside it or in /root/vt/n44/sun/zack; earth_col.jpg (tools: real coastlines from the GLOBE land mask).
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n44/sun/zack', n)) if os.path.exists(p_))
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

# ================================================================ numbers (Live Science with T. Cronin (MIT) and M. Summers (GMU))
LIGHT_MIN = 8 + 20 / 60                 # sunlight takes 8 min 20 s to get here (the gravity change too)
# Earth drops ~36 F a day at first, most places under freezing in 2-3 days, ponds in a week, lakes in months,
# the ocean stays liquid under the ice for years, vents keep chemical life going, Earth ends near -400 F (Pluto ~ -380 F)

# ================================================================ space (far from the yard): stars, the Sun, Earth, Pluto
SP = Vector((0, 200000, 0))
STARS = bpy.data.materials.new('stars'); STARS.use_nodes = True; _sn = STARS.node_tree; _sn.nodes.remove(_sn.nodes['Principled BSDF'])
star_shader(_sn, (0.0015, 0.002, 0.006), 420.0)
_sn.nodes['Emission'].inputs['Strength'].default_value = 1.0
SKYBALL = prim('uv_sphere', 'starsphere', STARS, loc=SP, segments=64, ring_count=32, radius=3000)
SKYBALL.visible_shadow = False; SKYBALL.visible_diffuse = False; SKYBALL.visible_glossy = False
NEB = bpy.data.materials.new('nebula'); NEB.use_nodes = True; _nb = NEB.node_tree; _nb.nodes.remove(_nb.nodes['Principled BSDF']); NEB.blend_method = 'BLEND'
_ne = _nb.nodes.new('ShaderNodeEmission'); _nf = tnoise(_nb, coord(_nb, 'Generated'), 3.0, 6, 1.5)
_nb.links.new(ramp(_nb, _nf, [(0.45, (0.0, 0.0, 0.0)), (0.62, (0.05, 0.02, 0.09)), (0.75, (0.02, 0.05, 0.12))]), _ne.inputs['Color'])
_ne.inputs['Strength'].default_value = 0.1; _nt_ = _nb.nodes.new('ShaderNodeBsdfTransparent'); _nad = _nb.nodes.new('ShaderNodeAddShader')
_nb.links.new(_ne.outputs[0], _nad.inputs[0]); _nb.links.new(_nt_.outputs[0], _nad.inputs[1]); _nb.links.new(_nad.outputs[0], _nb.nodes['Material Output'].inputs['Surface'])
NEBULA = prim('uv_sphere', 'nebula', NEB, loc=SP, segments=48, ring_count=24, radius=2900); NEBULA.visible_shadow = False; NEBULA.hide_render = True

# ---- the Sun: boiling surface (4D noise, w = time), dark limb, corona, loops of glowing gas; it shudders, pinches and blinks out
SUN_C = SP + Vector((0, 0, 0)); SUN_R = 10.0
SUN_M = bpy.data.materials.new('sun_surf'); SUN_M.use_nodes = True; _su = SUN_M.node_tree; _su.nodes.remove(_su.nodes['Principled BSDF'])
_se = _su.nodes.new('ShaderNodeEmission')
def _n4(nt, scale, detail, w_attr, dist=0.0):
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nz.inputs['Distortion'].default_value = dist; nt.links.new(coord(nt, 'Object'), nz.inputs['Vector']); nt.links.new(objattr(nt, w_attr), nz.inputs['W']); return nz.outputs['Fac']
_g1 = _n4(_su, 0.9, 8, 'w', 0.6)                                           # granulation
_vo = _su.nodes.new('ShaderNodeTexVoronoi'); _vo.voronoi_dimensions = '4D'; _vo.feature = 'DISTANCE_TO_EDGE'; _vo.inputs['Scale'].default_value = 3.2
_su.links.new(coord(_su, 'Object'), _vo.inputs['Vector']); _su.links.new(objattr(_su, 'w'), _vo.inputs['W'])
_cell = math_(_su, 'MINIMUM', math_(_su, 'MULTIPLY', _vo.outputs['Distance'], 5.0), 1.0)
_g = math_(_su, 'ADD', math_(_su, 'MULTIPLY', _g1, 0.72), math_(_su, 'MULTIPLY', _cell, 0.28))
_lw = _su.nodes.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.5
_limb = math_(_su, 'POWER', math_(_su, 'SUBTRACT', 1.0, _lw.outputs['Facing']), 0.55)                     # 1 at the middle, dark at the rim
_heat = objattr(_su, 'heat')                                                                                 # 1 normal .. 0 a dying red ember
_cA = ramp(_su, _g, [(0.2, (0.6, 0.08, 0.0)), (0.45, (1.0, 0.32, 0.02)), (0.65, (1.0, 0.6, 0.08)), (0.85, (1.0, 0.85, 0.3))])
_cB = ramp(_su, _g, [(0.25, (0.25, 0.02, 0.0)), (0.6, (0.7, 0.1, 0.01)), (0.9, (1.0, 0.35, 0.05))])
_col = mixc(_su, _heat, _cB, _cA)
_su.links.new(_col, _se.inputs['Color'])
_su.links.new(math_(_su, 'MULTIPLY', math_(_su, 'MULTIPLY', math_(_su, 'MULTIPLY_ADD', _limb, 0.8, 0.25), objattr(_su, 'bright')), 0.9), _se.inputs['Strength'])
_su.links.new(_se.outputs[0], _su.nodes['Material Output'].inputs['Surface'])
SUN = prim('uv_sphere', 'sun', SUN_M, loc=SUN_C, segments=96, ring_count=48, radius=SUN_R); SUN['w'] = 0.0; SUN['heat'] = 1.0; SUN['bright'] = 1.0
SUN.visible_shadow = False
def glow_shell(name, col, power, strength, attr='a'):
    """an additive fresnel glow shell (corona, shock ring, atmosphere)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    if power > 0: f_ = math_(nt, 'POWER', lw.outputs['Facing'], power)                  # rim glow
    else: f_ = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), -power), math_(nt, 'MULTIPLY', lw.outputs['Facing'], 4.0))   # a halo ring: 0 at the middle and the edge
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', f_, objattr(nt, attr)), strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(e_.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
HALO_M = bpy.data.materials.new('halo_m'); HALO_M.use_nodes = True; _hn = HALO_M.node_tree; _hn.nodes.remove(_hn.nodes['Principled BSDF']); HALO_M.blend_method = 'BLEND'
_hg = _hn.nodes.new('ShaderNodeTexGradient'); _hg.gradient_type = 'SPHERICAL'; _hn.links.new(coord(_hn, 'Object'), _hg.inputs['Vector'])
_hf = math_(_hn, 'POWER', _hg.outputs['Fac'], 2.6); _he = _hn.nodes.new('ShaderNodeEmission')
_hn.links.new(mixc(_hn, _hf, (1.0, 0.18, 0.01), (1.0, 0.55, 0.12)), _he.inputs['Color'])
_hn.links.new(math_(_hn, 'MULTIPLY', _hf, math_(_hn, 'MULTIPLY', objattr(_hn, 'a'), 2.2)), _he.inputs['Strength'])
_ht = _hn.nodes.new('ShaderNodeBsdfTransparent'); _ha = _hn.nodes.new('ShaderNodeAddShader')
_hn.links.new(_he.outputs[0], _ha.inputs[0]); _hn.links.new(_ht.outputs[0], _ha.inputs[1]); _hn.links.new(_ha.outputs[0], _hn.nodes['Material Output'].inputs['Surface'])
CORONA = prim('plane', 'corona', HALO_M, loc=SUN_C + Vector((0, 0.5, 0)), rot=(R(90), 0, 0), size=2.0)     # a soft glow card behind the Sun (unit radius, scaled)
CORONA.visible_shadow = False; CORONA_R = SUN_R * 2.6
CORONA['a'] = 1.0; CORONA.visible_shadow = False
SHOCK = prim('torus', 'shock', emis_mix('shock_m', (1.0, 0.8, 0.5), 9.0, 'a'), loc=SUN_C, rot=(R(90), 0, 0), major_radius=1.0, minor_radius=0.025, major_segments=128, minor_segments=12)
SHOCK['a'] = 0.0; SHOCK.visible_shadow = False
PROM_M = bpy.data.materials.new('prom'); PROM_M.use_nodes = True; _pm = PROM_M.node_tree; _pm.nodes.remove(_pm.nodes['Principled BSDF'])
_pe = _pm.nodes.new('ShaderNodeEmission'); _pe.inputs['Color'].default_value = (1.0, 0.22, 0.03, 1)
_pm.links.new(math_(_pm, 'MULTIPLY', math_(_pm, 'MULTIPLY_ADD', tnoise(_pm, coord(_pm, 'Object'), 2.0, 4), 1.4, 0.2), math_(_pm, 'MULTIPLY', objattr(_pm, 'a'), 0.9)), _pe.inputs['Strength'])
_pm.links.new(_pe.outputs[0], _pm.nodes['Material Output'].inputs['Surface'])
PROMS = []
random.seed(41)
for k in range(0):                                                 # loops of glowing gas standing off the limb (seen edge-on)
    a0 = 0.6 + k * 1.57 + random.uniform(-0.3, 0.3); span = random.uniform(0.45, 0.7); hgt = random.uniform(0.12, 0.2); pts = []
    for i in range(17):
        u = i / 16; a_ = a0 + span * (u - 0.5); h_ = SUN_R * (1.0 + hgt * math.sin(math.pi * u))
        pts.append((h_ * math.cos(a_), 0.0, h_ * math.sin(a_)))
    o = tube(f'prom_{k}', pts, lambda u: 0.35 + 0.3 * math.sin(math.pi * u), PROM_M, seg=10); o.parent = None
    o.location = SUN_C; o['a'] = 1.0; o['ph'] = random.uniform(0, 6.3); o.visible_shadow = False; PROMS.append(o)
EMBER = prim('uv_sphere', 'ember', emis_mix('ember_m', (1.0, 0.12, 0.02), 3.0, 'a'), loc=SUN_C, segments=32, ring_count=16, radius=1.0); EMBER['a'] = 0.0
SPACE_FILL = light_at('space_fill', 'AREA', SP + Vector((60, -40, 30)), SP, 0.0, (0.55, 0.65, 1.0), 40)

def sun_story(c):
    """c = seconds from frame one (it runs on past the end into the loop). Shudder from -0.6, pinch at 1.15-1.4, blink out at 1.4."""
    w = 0.9 * c; SUN['w'] = w                                       # the surface boils visibly
    for o in PROMS: o['a'] = 1.0
    if c < 1.15:
        k = smooth(-1.6, 1.15, c)                                  # already shuddering on frame one: pulses, flickers, reddens, shrinks
        pul = 1.0 + 0.06 * k * math.sin(2 * math.pi * 2.6 * c) + 0.025 * k * wob(c, 9.0, 2.0)
        r_ = (1.0 - 0.3 * k) * pul; SUN['heat'] = 1.0 - 0.75 * k; SUN['bright'] = (1.0 - 0.1 * k) * (1.0 + 0.18 * k * math.sin(2 * math.pi * 2.6 * c + 1.0))
        CORONA['a'] = 1.0 - 0.3 * k; SHOCK['a'] = 0.0; sh_r = 1.0
        for o in PROMS: o['a'] = 1.0 + 0.6 * k
    elif c < 1.4:                                                  # the pinch: falls in on itself, one hot flare
        k = smooth(1.15, 1.4, c); r_ = lerp(0.72, 0.04, k * k)
        SUN['heat'] = lerp(0.55, 0.9, k); SUN['bright'] = lerp(0.85, 2.6, k); CORONA['a'] = (1.0 - k) * 0.7; SHOCK['a'] = 0.0; sh_r = 1.0
        for o in PROMS: o['a'] = 1.6 * (1 - k)
    else:                                                          # gone; the last light leaves as an expanding shell
        r_ = 0.0; SUN['bright'] = 0.0; CORONA['a'] = 0.0
        k = c - 1.4; sh_r = SUN_R * (0.3 + 3.2 * k + 2.0 * k * k); SHOCK['a'] = 1.4 * math.exp(-1.6 * k) * smooth(0.0, 0.03, k)
        for o in PROMS: o['a'] = 0.0
    SUN.scale = (max(r_, 1e-4),) * 3; SUN.hide_render = r_ < 0.01
    CORONA.scale = (max(r_, 1e-4) * CORONA_R * (1 + 0.04 * wob(c, 2.0, 7.0)),) * 3; CORONA.hide_render = CORONA['a'] < 0.01
    for o in PROMS:
        o.scale = (max(r_, 1e-4),) * 3; o.hide_render = o['a'] < 0.01 or r_ < 0.05
        o.rotation_euler = (0, 0.03 * wob(c, 0.6, o['ph']), 0)
    SHOCK.scale = (sh_r,) * 3; SHOCK.hide_render = SHOCK['a'] < 0.005
    EMBER['a'] = (smooth(1.3, 1.42, c) * math.exp(-1.2 * max(c - 1.42, 0.0))) if c > 1.3 else 0.0; EMBER.scale = (lerp(0.9, 0.35, smooth(1.4, 2.6, c)),) * 3; EMBER.hide_render = EMBER['a'] < 0.01
    return r_

# ---- Earth: real coastlines (earth_col.jpg), clouds, a thin blue air shell, city lights at night, frost over everything later
EARTH_C = SP + Vector((0, 0, 0)); ER = 1.0
EIMG = bpy.data.images.load(asset('earth_col.jpg'))
EARTH_M = mat('earth_m', (0.1, 0.2, 0.4), 0.6); _em = EARTH_M.node_tree; _eb = _em.nodes['Principled BSDF']
_et = _em.nodes.new('ShaderNodeTexImage'); _et.image = EIMG; _et.interpolation = 'Cubic'
_euv = coord(_em, 'UV'); _em.links.new(_euv, _et.inputs['Vector'])
_ecol = mixc(_em, math_(_em, 'MULTIPLY', tnoise(_em, coord(_em, 'Object'), 6.0, 8), 0.25), _et.outputs['Color'], (0.06, 0.07, 0.05))
# frost: white-blue ice with faint cracks; a noisy front so it can creep
_fr = objattr(_em, 'frost'); _fn = tnoise(_em, coord(_em, 'Object'), 2.5, 6)
_fk = math_(_em, 'MINIMUM', math_(_em, 'MAXIMUM', math_(_em, 'MULTIPLY', math_(_em, 'SUBTRACT', math_(_em, 'MULTIPLY_ADD', _fr, 1.4, -0.2), _fn), 6.0), 0.0), 1.0)
_icec = ramp(_em, tnoise(_em, coord(_em, 'Object'), 9.0, 6), [(0.3, (0.55, 0.66, 0.78)), (0.55, (0.86, 0.9, 0.96)), (0.75, (0.95, 0.97, 1.0))])
_icec = mixc(_em, 0.42, _icec, _et.outputs['Color'])
_em.links.new(mixc(_em, _fk, _ecol, _icec), _eb.inputs['Base Color'])
_em.links.new(mixc(_em, _fk, (0.55, 0.55, 0.55, 1), (0.25, 0.25, 0.25, 1)), _eb.inputs['Roughness'])
# city lights on land (the night side), only where it isn't frozen
_city = math_(_em, 'MULTIPLY', math_(_em, 'GREATER_THAN', tnoise(_em, coord(_em, 'Object'), 70.0, 3), 0.64), math_(_em, 'GREATER_THAN', tnoise(_em, coord(_em, 'Object'), 3.0, 3), 0.48))
_sxc = sepz(_em, _et.outputs['Color']); _land2 = math_(_em, 'GREATER_THAN', math_(_em, 'SUBTRACT', _sxc.outputs['Y'], _sxc.outputs['Z']), 0.04)
_em.links.new(math_(_em, 'MULTIPLY', math_(_em, 'MULTIPLY', math_(_em, 'MULTIPLY', _city, _land2), objattr(_em, 'city')), math_(_em, 'SUBTRACT', 1.0, _fk)), _eb.inputs['Emission Strength'])
_eb.inputs['Emission Color'].default_value = (1.0, 0.7, 0.35, 1)
EARTH = prim('uv_sphere', 'earth', EARTH_M, loc=EARTH_C, segments=128, ring_count=64, radius=ER); EARTH['frost'] = 0.0; EARTH['city'] = 0.0
EARTH.rotation_mode = 'XYZ'
CLD_M = mat('cld_m', (1, 1, 1), 0.9); CLD_M.blend_method = 'BLEND'; _cn = CLD_M.node_tree
_cn.links.new(math_(_cn, 'MULTIPLY', math_(_cn, 'MINIMUM', math_(_cn, 'MAXIMUM', math_(_cn, 'MULTIPLY', math_(_cn, 'SUBTRACT', tnoise(_cn, coord(_cn, 'Object'), 2.2, 8, 0.8), 0.56), 5.0), 0.0), 1.0), objattr(_cn, 'a')), _cn.nodes['Principled BSDF'].inputs['Alpha'])
CLOUDS = prim('uv_sphere', 'clouds', CLD_M, loc=EARTH_C, segments=96, ring_count=48, radius=ER * 1.012); CLOUDS['a'] = 0.8; CLOUDS.parent = EARTH; CLOUDS.location = (0, 0, 0)
ATM = prim('uv_sphere', 'atm', glow_shell('atm_m', (0.3, 0.55, 1.0), 3.0, 2.0), loc=EARTH_C, segments=96, ring_count=48, radius=ER * 1.04); ATM['a'] = 1.0; ATM.parent = EARTH; ATM.location = (0, 0, 0)
ATM.visible_shadow = False
EARTH_PARTS = [EARTH, CLOUDS, ATM]

# ---- the orbit: a ghost circle (dashed) where Earth would have gone, and a glowing trail that goes dead straight
ORB_R = 22.0
DASH_M = emis_mix('dash_m', (0.6, 0.8, 1.0), 2.0, 'a')
_orb_pts = []
DASHES = []
for k in range(90):
    a0_ = 2 * math.pi * k / 90; a1_ = a0_ + 2 * math.pi / 90 * 0.55
    pts = [(ORB_R * math.cos(a0_ + (a1_ - a0_) * j / 3), ORB_R * math.sin(a0_ + (a1_ - a0_) * j / 3), 0) for j in range(4)]
    o = tube(f'dash_{k}', pts, 0.06, DASH_M, seg=6); o.location = SUN_C; o['a'] = 0.0; o.visible_shadow = False; DASHES.append(o)
TRAIL_M = emis_mix('trail_m', (0.45, 0.85, 1.0), 4.0, 'a')
TRAIL = None
def trail_set(pts):
    """rebuild the trail tube along pts (world), thin at the old end"""
    global TRAIL
    if TRAIL is not None:
        me_ = TRAIL.data; bpy.data.objects.remove(TRAIL); bpy.data.meshes.remove(me_)
    TRAIL = tube('trail', pts, lambda u: 0.03 + 0.17 * u, TRAIL_M, seg=10); TRAIL['a'] = 1.0; TRAIL.visible_shadow = False
    return TRAIL

# ---- Pluto: tan and rust with its big pale heart (texture made here), much smaller than Earth
def pluto_image(w=1024, h=512):
    u = (np.arange(w) + 0.5) / w; v = (np.arange(h) + 0.5) / h; U, Vv = np.meshgrid(u, v)
    lon = (U - 0.5) * 2 * np.pi; lat = (Vv - 0.5) * np.pi
    rng = np.random.default_rng(7); acc = np.zeros((h, w), np.float32)
    for o_, amp in ((4, 1.0), (8, 0.5), (16, 0.3), (32, 0.18), (64, 0.1)):
        ph = rng.random(4) * 6.28; acc += amp * np.sin(o_ * lon + ph[0] + 2 * np.sin(o_ * 0.7 * lat + ph[1])) * np.cos(o_ * lat * 0.9 + ph[2])
    acc = (acc - acc.min()) / (np.ptp(acc) + 1e-9)
    tan = np.array([0.62, 0.48, 0.34]); rust = np.array([0.33, 0.16, 0.08]); pale = np.array([0.82, 0.78, 0.7])
    c = tan[None, None] * (0.75 + 0.5 * acc[..., None])
    belt = np.clip(1 - np.abs(lat + 0.15) / 0.35, 0, 1) * (acc > 0.45)                 # the dark rusty belt near the equator
    c = c * (1 - belt[..., None] * 0.8) + rust * belt[..., None] * 0.8
    from PIL import Image as _I, ImageDraw as _D, ImageFilter as _F                # the heart, facing lon 0 (classic heart curve)
    hm = _I.new('L', (w, h), 0); tt = np.linspace(0, 2 * np.pi, 200); hx = 16 * np.sin(tt) ** 3; hy = 13 * np.cos(tt) - 5 * np.cos(2 * tt) - 2 * np.cos(3 * tt) - np.cos(4 * tt)
    lat0 = 0.12; sc_ = 0.027; plon = hx * sc_ / np.cos(lat0 + hy * sc_); plat = lat0 + hy * sc_
    _D.Draw(hm).polygon([((lo / (2 * np.pi) + 0.5) * w, (la_ / np.pi + 0.5) * h) for lo, la_ in zip(plon, plat)], fill=255)
    heart = np.asarray(hm.filter(_F.GaussianBlur(3))).astype(np.float32) / 255.0
    c = c * (1 - heart[..., None]) + pale * heart[..., None]
    c = c * (0.9 + 0.2 * acc[..., None])
    img = bpy.data.images.new('pluto_tex', w, h); img.colorspace_settings.name = 'sRGB'
    px = np.concatenate([np.clip(c, 0, 1) ** 2.2, np.ones((h, w, 1))], axis=2).astype(np.float32)   # image rows bottom-up
    img.pixels.foreach_set(px.ravel()); img.pack(); return img
PLUTO_M = mat('pluto_m', (0.6, 0.5, 0.4), 0.85); _pl = PLUTO_M.node_tree; _pt = _pl.nodes.new('ShaderNodeTexImage'); _pt.image = pluto_image()
_pl.links.new(coord(_pl, 'UV'), _pt.inputs['Vector']); _pl.links.new(_pt.outputs['Color'], _pl.nodes['Principled BSDF'].inputs['Base Color'])
_pb = _pl.nodes.new('ShaderNodeBump'); _pb.inputs['Strength'].default_value = 0.25; _pl.links.new(tnoise(_pl, coord(_pl, 'Object'), 18.0, 8), _pb.inputs['Height'])
_pl.links.new(_pb.outputs['Normal'], _pl.nodes['Principled BSDF'].inputs['Normal'])
PLUTO = prim('uv_sphere', 'pluto', PLUTO_M, loc=SP + Vector((0, 0, -60)), segments=96, ring_count=48, radius=0.42); PLUTO.rotation_mode = 'XYZ'
PLUTO_KEY = light_at('pluto_key', 'AREA', SP + Vector((-30, -25, 20)), SP, 0.0, (0.75, 0.82, 1.0), 12)
SPACE = [SKYBALL, SUN, CORONA, SHOCK, EMBER, PLUTO] + PROMS + EARTH_PARTS + DASHES

# ================================================================ the yard (at the origin): you stand on a back porch looking north (+y)
# over a lawn with a pond, trees, two neighbours' houses and a lake. Day (low golden sun), night (stars, porch lamp, lit windows),
# frost (one shared amount freezes every surface), the pond and the lake skin over with ice.
DECK_Z = 0.6; RAIL_Y = 1.2; RAIL_Z = DECK_Z + 1.0
EYE = Vector((0.0, -0.3, DECK_Z + 1.53))
SUN_DIR = Vector((math.sin(R(16)) * math.cos(R(15)), math.cos(R(16)) * math.cos(R(15)), math.sin(R(15)))).normalized()
MOON_DIR = Vector((math.sin(R(-24)) * math.cos(R(24)), math.cos(R(-24)) * math.cos(R(24)), math.sin(R(24)))).normalized()

# ---- frost: one node group shared by every outdoor material; FROST_AMT drives all of it
FG = bpy.data.node_groups.new('frost', 'ShaderNodeTree')
FG.interface.new_socket('Color', in_out='INPUT', socket_type='NodeSocketColor'); FG.interface.new_socket('Rough', in_out='INPUT', socket_type='NodeSocketFloat')
FG.interface.new_socket('Color', in_out='OUTPUT', socket_type='NodeSocketColor'); FG.interface.new_socket('Rough', in_out='OUTPUT', socket_type='NodeSocketFloat')
FG.interface.new_socket('Mask', in_out='OUTPUT', socket_type='NodeSocketFloat')
_gi = FG.nodes.new('NodeGroupInput'); _go = FG.nodes.new('NodeGroupOutput'); FROST_AMT = FG.nodes.new('ShaderNodeValue'); FROST_AMT.outputs[0].default_value = 0.0
_fz = tnoise(FG, coord(FG, 'Object'), 3.0, 6, 0.5)
_fz2 = FG.nodes.new('ShaderNodeTexVoronoi'); _fz2.inputs['Scale'].default_value = 40.0; FG.links.new(coord(FG, 'Object'), _fz2.inputs['Vector'])
_fm = math_(FG, 'MINIMUM', math_(FG, 'MAXIMUM', math_(FG, 'MULTIPLY', math_(FG, 'SUBTRACT', math_(FG, 'MULTIPLY', FROST_AMT.outputs[0], 1.7), math_(FG, 'ADD', _fz, 0.3)), 7.0), 0.0), 1.0)
_fc = mixc(FG, math_(FG, 'MULTIPLY', _fz2.outputs['Distance'], 1.4), (0.92, 0.95, 1.0), (0.7, 0.78, 0.88))
FG.links.new(mixc(FG, _fm, _gi.outputs['Color'], _fc), _go.inputs['Color'])
FG.links.new(math_(FG, 'ADD', math_(FG, 'MULTIPLY', _gi.outputs['Rough'], math_(FG, 'SUBTRACT', 1.0, _fm)), math_(FG, 'MULTIPLY', _fm, 0.42)), _go.inputs['Rough'])
FG.links.new(_fm, _go.inputs['Mask'])
def frostify(m):
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); g = nt.nodes.new('ShaderNodeGroup'); g.node_tree = FG
    for k in ('Base Color', 'Roughness'):
        lk = next((l for l in nt.links if l.to_socket == b.inputs[k]), None); gin = g.inputs['Color' if k == 'Base Color' else 'Rough']
        if lk: nt.links.new(lk.from_socket, gin); nt.links.remove(lk)
        else: gin.default_value = b.inputs[k].default_value
        nt.links.new(g.outputs['Color' if k == 'Base Color' else 'Rough'], b.inputs[k])
    return m

# ---- materials
WOOD = frostify(noisy(mat('deck_wood', (0.36, 0.22, 0.13), 0.7), 2.0, 0.3, 0.1))
_wn = WOOD.node_tree; _ww = _wn.nodes.new('ShaderNodeTexWave'); _ww.wave_type = 'BANDS'; _ww.bands_direction = 'Y'; _ww.inputs['Scale'].default_value = 3.0
_ww.inputs['Distortion'].default_value = 8.0; _ww.inputs['Detail'].default_value = 3; _wn.links.new(coord(_wn), _ww.inputs['Vector'])
_wbm = _wn.nodes.new('ShaderNodeBump'); _wbm.inputs['Strength'].default_value = 0.25; _wn.links.new(_ww.outputs['Fac'], _wbm.inputs['Height'])
_wn.links.new(_wbm.outputs['Normal'], _wn.nodes['Principled BSDF'].inputs['Normal'])
RAILW = frostify(mat('rail_white', (0.78, 0.76, 0.72), 0.45))
GRASS = noisy(mat('grass', (0.09, 0.2, 0.035), 0.92), 0.15, 0.4, 0.05)
_gn2 = GRASS.node_tree; _gb2 = _gn2.nodes['Principled BSDF']; _gbm2 = _gn2.nodes.new('ShaderNodeBump'); _gbm2.inputs['Strength'].default_value = 0.5
_gn2.links.new(tnoise(_gn2, coord(_gn2), 60.0, 8), _gbm2.inputs['Height']); _gn2.links.new(_gbm2.outputs['Normal'], _gb2.inputs['Normal'])
frostify(GRASS)
ROCK = frostify(noisy(mat('rock', (0.33, 0.31, 0.29), 0.85), 6.0, 0.4))
BARK = frostify(mat('bark', (0.12, 0.08, 0.05), 0.9))
LEAF = [frostify(noisy(mat(f'leaf{k}', c_, 0.8, sheen=0.4), 3.0, 0.35)) for k, c_ in enumerate(((0.07, 0.19, 0.04), (0.11, 0.24, 0.05), (0.16, 0.22, 0.04)))]
PINE = frostify(noisy(mat('pine', (0.03, 0.1, 0.04), 0.85), 5.0, 0.3))
SIDING = [frostify(noisy(mat(f'siding{k}', c_, 0.7), 1.5, 0.15)) for k, c_ in enumerate(((0.62, 0.6, 0.52), (0.45, 0.52, 0.58)))]
ROOF = frostify(noisy(mat('roof', (0.12, 0.11, 0.11), 0.8), 4.0, 0.3))
HILL = frostify(noisy(mat('hill', (0.06, 0.12, 0.05), 0.95), 0.05, 0.4))
WIN_M = bpy.data.materials.new('window'); WIN_M.use_nodes = True; _wi = WIN_M.node_tree; _wib = _wi.nodes['Principled BSDF']
_wib.inputs['Base Color'].default_value = (0.05, 0.06, 0.07, 1); _wib.inputs['Roughness'].default_value = 0.08
_wib.inputs['Emission Color'].default_value = (1.0, 0.72, 0.4, 1); _wi.links.new(math_(_wi, 'MULTIPLY', objattr(_wi, 'lit'), 2.6), _wib.inputs['Emission Strength'])

# ---- the porch: plank deck, white railing with balusters and posts (one post carries the thermometer)
YARD = []
for k in range(26):                                                # planks running out toward the yard
    x_ = -3.0 + k * 0.235; YARD.append(box(f'plank{k}', (0.22, 4.0, 0.04), (x_, -0.8, DECK_Z - 0.02), WOOD, bv=0.006))
YARD.append(box('deck_frame', (6.4, 0.2, 0.6), (0, RAIL_Y + 0.1, DECK_Z / 2), WOOD))
POSTS_X = [-3.0, -1.55, -0.32, 1.25, 3.0]
for i, x_ in enumerate(POSTS_X):
    YARD.append(box(f'post{i}', (0.09, 0.09, 1.12), (x_, RAIL_Y, DECK_Z + 0.56), RAILW, bv=0.008))
    YARD.append(box(f'cap{i}', (0.12, 0.12, 0.03), (x_, RAIL_Y, DECK_Z + 1.135), RAILW, bv=0.006))
YARD.append(box('toprail', (6.1, 0.1, 0.045), (0, RAIL_Y, RAIL_Z), RAILW, bv=0.008))
YARD.append(box('botrail', (6.1, 0.06, 0.04), (0, RAIL_Y, DECK_Z + 0.1), RAILW, bv=0.005))
for k in range(48):
    x_ = -2.94 + k * 0.125
    if min(abs(x_ - p_) for p_ in POSTS_X) < 0.07: continue
    YARD.append(box(f'bal{k}', (0.035, 0.035, 0.88), (x_, RAIL_Y, DECK_Z + 0.56), RAILW))
# ---- the lawn, sloping gently down to the lake; the pond is a dish cut into it
def ground_z(x, y):
    z = -0.025 * max(y - 2.0, 0.0) - 0.0004 * x * x
    if y > 24: z -= 0.07 * (y - 24) ** 1.3
    return z
_vs, _fs = [], []; _NX, _NY = 90, 90; _xs = np.linspace(-60, 60, _NX); _ys = [1.3 + 34.0 * (j / (_NY - 1)) ** 1.15 for j in range(_NY)]
PC = Vector((1.6, 8.5)); PRX, PRY = 2.8, 1.9
for j, y_ in enumerate(_ys):
    for i, x_ in enumerate(_xs):
        z_ = ground_z(x_, y_); d_ = math.hypot((x_ - PC.x) / (PRX + 0.6), (y_ - PC.y) / (PRY + 0.6))
        if d_ < 1.0: z_ -= 0.35 * (1 - d_ * d_)
        _vs.append((x_, y_, z_))
for j in range(_NY - 1):
    for i in range(_NX - 1): a0 = j * _NX + i; _fs.append((a0, a0 + 1, a0 + _NX + 1, a0 + _NX))
LAWN = mesh('lawn', _vs, _fs, GRASS); YARD.append(LAWN)
# ---- water: dark glassy water with moving ripples; property 'ice' grows an ice sheet in from the shore
def water_mat(name, mode):
    m = mat(name, (0.01, 0.025, 0.03), 0.04, ior=1.33); nt = m.node_tree; b = nt.nodes['Principled BSDF']; oc = coord(nt, 'Object')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 3.0 if mode == 'pond' else 0.6
    nz.inputs['Detail'].default_value = 4; nt.links.new(oc, nz.inputs['Vector']); nt.links.new(objattr(nt, 'w'), nz.inputs['W'])
    bm_ = nt.nodes.new('ShaderNodeBump'); bm_.inputs['Strength'].default_value = 0.12; nt.links.new(nz.outputs['Fac'], bm_.inputs['Height'])
    sx = sepz(nt, oc)
    if mode == 'pond':                                            # elliptical distance: 1 at the shore, 0 in the middle
        dd = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'POWER', math_(nt, 'DIVIDE', sx.outputs['X'], PRX), 2.0), math_(nt, 'POWER', math_(nt, 'DIVIDE', sx.outputs['Y'], PRY), 2.0)))
        edge = math_(nt, 'SUBTRACT', 1.0, dd)
    else:                                                         # the lake: from its near shore (local y 0) out
        edge = math_(nt, 'DIVIDE', sx.outputs['Y'], 400.0)
    jag = tnoise(nt, oc, 1.4 if mode == 'pond' else 0.08, 4)
    ice = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', objattr(nt, 'ice'), math_(nt, 'ADD', edge, math_(nt, 'MULTIPLY', jag, 0.18))), 40.0), 0.0), 1.0)
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 2.2 if mode == 'pond' else 0.25; nt.links.new(oc, vo.inputs['Vector'])
    crack = math_(nt, 'LESS_THAN', vo.outputs['Distance'], 0.025)
    icec = mixc(nt, tnoise(nt, oc, 4.0 if mode == 'pond' else 0.3, 5), (0.55, 0.68, 0.78), (0.8, 0.86, 0.92)); icec = mixc(nt, math_(nt, 'MULTIPLY', crack, 0.6), icec, (0.95, 0.97, 1.0))
    nt.links.new(mixc(nt, ice, (0.01, 0.025, 0.03), icec), b.inputs['Base Color'])
    nt.links.new(mixc(nt, ice, (0.04, 0.04, 0.04, 1), (0.25, 0.25, 0.25, 1)), b.inputs['Roughness'])
    nm = nt.nodes.new('ShaderNodeMix'); nm.data_type = 'VECTOR'
    nt.links.new(ice, nm.inputs['Factor']); nt.links.new(bm_.outputs['Normal'], nm.inputs[4]); nm.inputs[5].default_value = (0, 0, 1)
    nt.links.new(nm.outputs[1], b.inputs['Normal'])
    edgeglow = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', ice, math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', objattr(nt, 'ice'), math_(nt, 'ADD', edge, math_(nt, 'MULTIPLY', jag, 0.18)))), 12.0), 1.0))), objattr(nt, 'front'))
    b.inputs['Emission Color'].default_value = (0.7, 0.9, 1.0, 1); nt.links.new(edgeglow, b.inputs['Emission Strength'])         # the freezing edge glints
    return m
POND_M = water_mat('pond_w', 'pond')
_pv, _pf = [], []; _pn = 64
for i in range(_pn):
    a_ = 2 * math.pi * i / _pn; _pv.append(((PRX + 0.25) * math.cos(a_), (PRY + 0.25) * math.sin(a_), 0))
_pv.append((0, 0, 0)); _pf = [(i, (i + 1) % _pn, _pn) for i in range(_pn)]
POND = mesh('pond', _pv, _pf, POND_M, loc=(PC.x, PC.y, ground_z(PC.x, PC.y) - 0.12)); POND['ice'] = 0.0; POND['w'] = 0.0; POND['front'] = 0.0
subsurf(POND, 3); YARD.append(POND)
random.seed(12)
for k in range(30):                                                # stones round the pond
    a_ = 2 * math.pi * k / 30 + random.uniform(-0.05, 0.05); rr = 1.0 + random.uniform(0.0, 0.1)
    x_, y_ = PC.x + (PRX + 0.15) * rr * math.cos(a_), PC.y + (PRY + 0.15) * rr * math.sin(a_)
    YARD.append(prim('ico_sphere', f'pstone{k}', ROCK, loc=(x_, y_, ground_z(x_, y_) - 0.06), subdivisions=2, radius=random.uniform(0.16, 0.3), scale=(1.2, 1, 0.55)))
for k in range(26):                                                # cattails on the far bank
    a_ = R(random.uniform(40, 140)); x_, y_ = PC.x + (PRX + 0.1) * math.cos(a_) * random.uniform(0.85, 1.0), PC.y + (PRY + 0.1) * math.sin(a_) * random.uniform(0.85, 1.0)
    h_ = random.uniform(0.7, 1.2); lean = (random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), h_)
    z0 = ground_z(x_, y_) - 0.15; YARD.append(tube(f'reed{k}', [(x_, y_, z0), (x_ + lean[0], y_ + lean[1], z0 + h_)], 0.007, LEAF[0], seg=5))
    YARD.append(prim('cylinder', f'cat{k}', BARK, loc=(x_ + lean[0] * 0.9, y_ + lean[1] * 0.9, z0 + h_ * 0.88), radius=0.018, depth=0.14, vertices=8))
# ---- the lake beyond the lawn, a far shore of hills and dark pines
LAKE_Y = 33.0; LAKE_Z = ground_z(0, LAKE_Y) + 0.15
LAKE_M = water_mat('lake_w', 'lake')
LAKE = mesh('lake', [(-500, 0, 0), (500, 0, 0), (500, 700, 0), (-500, 700, 0)], [(0, 1, 2, 3)], LAKE_M, loc=(0, LAKE_Y - 3.0, LAKE_Z)); LAKE['ice'] = 0.0; LAKE['w'] = 0.0; LAKE['front'] = 0.0
YARD.append(LAKE)
_hv, _hf = [], []; _HN = 160
for i in range(_HN):
    x_ = -900 + 1800 * i / (_HN - 1); h_ = 30 + 26 * mnoise.noise(Vector((x_ * 0.004, 0.3, 0))) + 12 * mnoise.noise(Vector((x_ * 0.015, 1.1, 0)))
    _hv += [(x_, 520 + 30 * mnoise.noise(Vector((x_ * 0.01, 2, 0))), LAKE_Z - 2), (x_, 600, LAKE_Z + h_)]
for i in range(_HN - 1): _hf.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
YARD.append(mesh('hills', _hv, _hf, HILL))
def pine(name, at, h):
    out = [prim('cylinder', name + '_t', BARK, loc=Vector(at) + Vector((0, 0, h * 0.15)), radius=h * 0.025, depth=h * 0.3, vertices=8)]
    for j in range(4):
        z_ = h * (0.2 + 0.2 * j); r_ = h * (0.26 - 0.05 * j)
        out.append(prim('cone', f'{name}_c{j}', PINE, loc=Vector(at) + Vector((0, 0, z_ + h * 0.15)), radius1=r_, radius2=0.0, depth=h * 0.36, vertices=12))
    return out
def leafy(name, at, h):
    out = [prim('cylinder', name + '_t', BARK, loc=Vector(at) + Vector((0, 0, h * 0.25)), radius=h * 0.035, depth=h * 0.5, vertices=8)]
    for j in range(5):
        p_ = Vector(at) + Vector((random.uniform(-0.18, 0.18) * h, random.uniform(-0.18, 0.18) * h, h * random.uniform(0.55, 0.85)))
        o = prim('ico_sphere', f'{name}_l{j}', random.choice(LEAF), loc=p_, subdivisions=3, radius=h * random.uniform(0.2, 0.28))
        d_ = o.modifiers.new('lumpy', 'DISPLACE'); tx = bpy.data.textures.new(f'{name}_tx{j}', 'CLOUDS'); tx.noise_scale = 0.35 * h / 6; d_.texture = tx; d_.strength = 0.35 * h / 6
        out.append(o)
    return out
random.seed(31)
for k, (x_, y_, h_) in enumerate([(-7.5, 7.0, 7.5), (-10.0, 13.0, 9.0), (-15.0, 18.5, 7.5), (8.5, 6.5, 7.0), (10.5, 13.5, 8.5), (16.0, 19.0, 7.0), (-4.5, 27, 8), (5.5, 29, 9)]):
    YARD += leafy(f'tree{k}', (x_, y_, ground_z(x_, y_)), h_)
for k in range(46):                                                # pines along the shore, on both sides of the open view
    x_ = random.choice([-1, 1]) * random.uniform(9, 70); y_ = random.uniform(24, 34)
    YARD += pine(f'pine{k}', (x_, y_, ground_z(x_, y_)), random.uniform(6, 12))
for k in range(140):                                               # far shore pines (dark shapes against the hills)
    x_ = random.uniform(-420, 420); y_ = random.uniform(505, 560)
    YARD += pine(f'fpine{k}', (x_, y_, LAKE_Z - 1), random.uniform(14, 26))
# ---- two neighbours' houses (windows light up after the blackout)
WINDOWS = []
def house(name, at, w, d, h, yaw, m):
    g = empty(name, loc=at); g.rotation_euler = (0, 0, yaw); out = [g]
    out.append(box(name + '_b', (w, d, h), (0, 0, h / 2), m, parent=g))
    rv = [(-w / 2 - 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, d / 2 + 0.3, h), (-w / 2 - 0.3, d / 2 + 0.3, h), (0, -d / 2 - 0.3, h + 2.2), (0, d / 2 + 0.3, h + 2.2)]
    out.append(mesh(name + '_r', rv, [(0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4)], ROOF, parent=g, smooth_=False))
    for row in range(2):
        for i in range(3):
            wo = box(f'{name}_w{row}{i}', (1.0, 0.06, 1.2), (-w / 2 + w * (i + 0.5) / 3, -d / 2 - 0.01, 1.3 + row * 2.4), WIN_M, parent=g); wo['lit'] = 0.0; WINDOWS.append(wo); out.append(wo)
    return out
YARD += house('house_l', Vector((-9.5, 21, ground_z(-9.5, 21))), 9, 7, 5.2, R(18), SIDING[0])
YARD += house('house_r', Vector((11.5, 25, ground_z(11.5, 25))), 8, 7, 4.8, R(-22), SIDING[1])
for k, o in enumerate(WINDOWS): o['on_t'] = 0.25 + 0.9 * h1(k + 3)            # each window comes on at its own moment after the blackout

# ---- sky: day gradient (bright toward the sun), the Sun's disk, a pale day Moon; night: stars on a dome round the yard
_wt = W_.node_tree; _wtc = _wt.nodes.new('ShaderNodeTexCoord'); _wsx = _wt.nodes.new('ShaderNodeSeparateXYZ'); _wt.links.new(_wtc.outputs['Generated'], _wsx.inputs['Vector'])
SKYR = _wt.nodes.new('ShaderNodeValToRGB'); _el = SKYR.color_ramp.elements
_el[0].position = 0.45; _el[0].color = (0.55, 0.5, 0.42, 1); _el[1].position = 0.8; _el[1].color = (0.05, 0.16, 0.55, 1)
_e2 = _el.new(0.505); _e2.color = (0.92, 0.72, 0.5, 1); _e3 = _el.new(0.56); _e3.color = (0.3, 0.48, 0.85, 1)
_wmr = _wt.nodes.new('ShaderNodeMapRange'); _wmr.inputs['From Min'].default_value = -1.0; _wmr.inputs['From Max'].default_value = 1.0
_wt.links.new(_wsx.outputs['Z'], _wmr.inputs['Value']); _wt.links.new(_wmr.outputs['Result'], SKYR.inputs['Fac'])
_wsun = _wt.nodes.new('ShaderNodeVectorMath'); _wsun.operation = 'DOT_PRODUCT'; _wt.links.new(_wtc.outputs['Generated'], _wsun.inputs[0]); _wsun.inputs[1].default_value = SUN_DIR
_wgl = math_(_wt, 'POWER', math_(_wt, 'MAXIMUM', _wsun.outputs['Value'], 0.0), 18.0)
SKY_DAYK = _wt.nodes.new('ShaderNodeValue'); SKY_DAYK.outputs[0].default_value = 1.0
_wday = mixc(_wt, math_(_wt, 'MULTIPLY', _wgl, 0.6), SKYR.outputs['Color'], (1.0, 0.8, 0.5))
_wnight = (0.008, 0.014, 0.035)
_wt.links.new(mixc(_wt, SKY_DAYK.outputs[0], _wnight, _wday), WBG.inputs['Color'])
WBG.inputs['Strength'].default_value = 1.0
SUN_DISK = prim('uv_sphere', 'sun_disk', emis('sun_disk_m', (1.0, 0.82, 0.55), 60.0), loc=SUN_DIR * 4000, segments=32, ring_count=16, radius=58)
SUN_DISK.visible_shadow = False; SUN_DISK.visible_diffuse = False; SUN_DISK.visible_glossy = True
SUN_GLOW = prim('plane', 'sun_glow', HALO_M, loc=SUN_DIR * 3990, size=2.0); SUN_GLOW.scale = (300, 300, 300); SUN_GLOW['a'] = 1.0; SUN_GLOW.visible_shadow = False
SUN_GLOW.rotation_mode = 'QUATERNION'; SUN_GLOW.rotation_quaternion = (-SUN_DIR).to_track_quat('Z', 'Y')
MOON_M = mat('moon_m', (0.6, 0.6, 0.58), 0.95); _mn = MOON_M.node_tree; _mb = _mn.nodes['Principled BSDF']
_mn.links.new(mixc(_mn, math_(_mn, 'GREATER_THAN', tnoise(_mn, coord(_mn), 2.5, 5), 0.55), (0.75, 0.75, 0.72), (0.45, 0.45, 0.45)), _mb.inputs['Emission Color'])
_mn.links.new(math_(_mn, 'MULTIPLY', objattr(_mn, 'lit'), 2.5), _mb.inputs['Emission Strength'])
MOON = prim('uv_sphere', 'moon', MOON_M, loc=MOON_DIR * 3000, segments=48, ring_count=24, radius=110); MOON['lit'] = 0.35; MOON.visible_shadow = False
YSTARS = bpy.data.materials.new('ystars'); YSTARS.use_nodes = True; _ys_ = YSTARS.node_tree; _ys_.nodes.remove(_ys_.nodes['Principled BSDF'])
star_shader(_ys_, (0.0, 0.0, 0.0), 300.0)
YDOME = prim('uv_sphere', 'ydome', YSTARS, loc=(0, 0, 0), segments=64, ring_count=32, radius=6000); YDOME.visible_shadow = False
YDOME.visible_diffuse = False; YDOME.visible_glossy = False
SUNL = bpy.data.lights.new('sunlight', 'SUN'); SUNL.energy = 3.6; SUNL.color = (1.0, 0.86, 0.66); SUNL.angle = R(0.6)
SUN_O = bpy.data.objects.new('sunlight', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_mode = 'QUATERNION'; SUN_O.rotation_quaternion = (-SUN_DIR).to_track_quat('-Z', 'Y')
NIGHTL = bpy.data.lights.new('nightfill', 'SUN'); NIGHTL.energy = 0.0; NIGHTL.color = (0.45, 0.6, 1.0); NIGHTL.angle = R(8)
NIGHT_O = bpy.data.objects.new('nightfill', NIGHTL); S.collection.objects.link(NIGHT_O); NIGHT_O.rotation_mode = 'QUATERNION'; NIGHT_O.rotation_quaternion = (-MOON_DIR).to_track_quat('-Z', 'Y')   # night light comes from the Moon's side
PORCH = light_at('porch', 'POINT', (0.9, -1.6, DECK_Z + 2.4), (0, 2, 1), 0.0, (1.0, 0.68, 0.38), 0.06)
YARD += [SUN_DISK, SUN_GLOW, MOON, YDOME]

# ---- the thermometer on the post left of you: white board, ticks, glass tube, red column (steps down with the °F readout)
TPOST = Vector((POSTS_X[2], RAIL_Y - 0.047, DECK_Z + 0.8))
THERM = []
_tb = box('th_board', (0.08, 0.012, 0.36), TPOST + Vector((0, -0.006, 0)), mat('th_white', (0.9, 0.9, 0.86), 0.35), bv=0.004); THERM.append(_tb)
for k in range(13):
    w_ = 0.026 if k % 2 == 0 else 0.016
    THERM.append(box(f'th_tick{k}', (w_, 0.002, 0.0028), TPOST + Vector((-0.02 + (0.026 - w_) / 2 * 0, -0.013, -0.12 + 0.02 * k)), mat('th_ink', (0.03, 0.03, 0.03), 0.6)))
GLASS = mat('glass', (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=1.45)
THERM.append(prim('cylinder', 'th_tube', GLASS, loc=TPOST + Vector((0.012, -0.018, 0.02)), radius=0.0065, depth=0.29, vertices=16))
RED = mat('th_red', (0.75, 0.02, 0.02), 0.25, emit=(0.6, 0.0, 0.0), estr=0.4)
THERM.append(prim('uv_sphere', 'th_bulb', RED, loc=TPOST + Vector((0.012, -0.018, -0.135)), radius=0.012, segments=16, ring_count=8))
TH_COL = prim('cylinder', 'th_col', RED, loc=TPOST + Vector((0.012, -0.018, -0.13)), radius=0.0035, depth=1.0, vertices=12); THERM.append(TH_COL)
THERM.append(box('th_screw', (0.01, 0.004, 0.01), TPOST + Vector((0, -0.013, 0.165)), STEEL if 'STEEL' in globals() else mat('steel', (0.5, 0.5, 0.52), 0.4, 1.0)))
def therm_set(f_):
    """column height for f_ degrees F: the scale runs -20 F (bottom tick) to 100 F (top tick)"""
    h_ = clamp((f_ + 20) / 120.0, 0.02, 1.0) * 0.24 + 0.01
    TH_COL.scale = (1, 1, h_); TH_COL.location = TPOST + Vector((0.012, -0.018, -0.13 + h_ / 2))
therm_set(70)
YARD += THERM
WATER_W = [POND, LAKE]

def yard_mode(day, frost=0.0, t=0.0):
    """day 1 = sunny; 0 = the blackout night. frost 0..1 everywhere."""
    SKY_DAYK.outputs[0].default_value = day; SUNL.energy = 3.6 * day
    SUN_DISK.hide_render = day < 0.5; SUN_GLOW.hide_render = day < 0.5
    NIGHTL.energy = 0.3 * (1 - day); PORCH.data.energy = 0.0 if day > 0.5 else 110.0
    YDOME.hide_render = day > 0.5; FROST_AMT.outputs[0].default_value = frost
    for o in CLOUDS_D if 'CLOUDS_D' in globals() else []: o.hide_render = day < 0.5
    for o in WATER_W: o['w'] = 0.25 * t
YARD_ALL = YARD + [o for o in []]

# ================================================================ you: the MakeHuman man seen from his own eyes (head hidden, camera at the eyes)
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HEADBITS = [o for o in bpy.data.objects if o.name.startswith('Human.') and o not in (BODY, SUIT, RIG)]
for o in HEADBITS: o.hide_render = True                                 # hair, brows, lashes, eyes: never seen from inside the head
RB = RIG.data.bones; PB = RIG.pose.bones
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
    for p_ in o.data.polygons: p_.use_smooth = True
sol = SUIT.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0035; sol.offset = 1.0
BODY.add_rest_position_attribute = True
# hide the head and neck (every vertex mostly weighted to neck01 or anything above it)
def _desc(bn):
    out = {bn}
    for c_ in RB[bn].children: out |= _desc(c_.name)
    return out
_HEADB = _desc('neck01'); _vgn = {g.index: g.name for g in BODY.vertex_groups}
_hw = np.zeros(len(BODY.data.vertices))
for v in BODY.data.vertices: _hw[v.index] = sum(g.weight for g in v.groups if _vgn[g.group] in _HEADB)
_keep = BODY.vertex_groups.new(name='fpv_keep'); _keep.add([i for i in range(len(_hw)) if _hw[i] < 0.35], 1.0, 'REPLACE')
_mk = BODY.modifiers.new('fpv_head', 'MASK'); _mk.vertex_group = 'fpv_keep'
subsurf(BODY, 1); subsurf(SUIT, 1)
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
retint(SHORTS_M, (0.2, 0.25, 0.36), 0.35, 0.95, 0.6)
retint(SHIRT_M, (0.62, 0.2, 0.16), 0.35, 0.9, 0.5)                   # the channel's guy: brick-red tee

# ---- the cold-weather look: a quilted puffer sleeve shell (his own arm faces, pushed out, bending with him) and knit gloves painted on his hands
_ARMB = {b_ for s_ in ('L', 'R') for b_ in ('clavicle.' + s_, 'shoulder01.' + s_, 'upperarm01.' + s_, 'upperarm02.' + s_, 'lowerarm01.' + s_, 'lowerarm02.' + s_)}
_HANDB = set()
for s_ in ('L', 'R'): _HANDB |= _desc('wrist.' + s_)
def _wsum(v, names): return sum(g.weight for g in v.groups if _vgn.get(g.group, '') in names)
_aw = np.array([_wsum(v, _ARMB) for v in BODY.data.vertices]); _hd = np.array([_wsum(v, _HANDB) for v in BODY.data.vertices])
_wz = np.array([v.co.z for v in BODY.data.vertices])
_jf = [p_.index for p_ in BODY.data.polygons if np.mean(_aw[list(p_.vertices)]) > 0.5 and np.mean(_hd[list(p_.vertices)]) < 0.15 and np.mean(_wz[list(p_.vertices)]) < 1.36]
def _copy_faces(src, faces, name):
    bm = bmesh.new(); bm.from_mesh(src.data); keep = set(faces)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    for g in src.vertex_groups: o.vertex_groups.new(name=g.name)
    # vertex weights survive bmesh (deform layer); make sure the groups exist with the same names (done above)
    o.parent = src.parent; o.matrix_world = src.matrix_world.copy()
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG; md.use_deform_preserve_volume = True
    for p_ in me.polygons: p_.use_smooth = True
    return o
JACKET = _copy_faces(BODY, _jf, 'jacket')
_dsp = JACKET.modifiers.new('puff', 'DISPLACE'); _dsp.strength = 0.024; _dsp.mid_level = 0.0; _dsp.direction = 'NORMAL'
_sl = JACKET.modifiers.new('thick', 'SOLIDIFY'); _sl.thickness = 0.006; _sl.offset = -1.0
subsurf(JACKET, 1)
JACKET.add_rest_position_attribute = True
JACKET_M = mat('puffer', (0.03, 0.06, 0.14), 0.5, sheen=0.1, coat=0.2); _jn = JACKET_M.node_tree; _jb = _jn.nodes['Principled BSDF']
_ra = _jn.nodes.new('ShaderNodeAttribute'); _ra.attribute_name = 'rest_position'
_rx = sepz(_jn, _ra.outputs['Vector']); _cmb = _jn.nodes.new('ShaderNodeCombineXYZ')
_jn.links.new(math_(_jn, 'ABSOLUTE', _rx.outputs['X']), _cmb.inputs[0]); _jn.links.new(_rx.outputs['Y'], _cmb.inputs[1]); _jn.links.new(_rx.outputs['Z'], _cmb.inputs[2])
_vd = _jn.nodes.new('ShaderNodeVectorMath'); _vd.operation = 'DISTANCE'; _jn.links.new(_cmb.outputs[0], _vd.inputs[0]); _vd.inputs[1].default_value = (0.18, -0.017, 1.296)
_qs = math_(_jn, 'SINE', math_(_jn, 'MULTIPLY', _vd.outputs['Value'], 2 * math.pi / 0.075))          # quilting: a seam every 7.5 cm down the arm
_puff = math_(_jn, 'POWER', math_(_jn, 'ABSOLUTE', _qs), 0.35)
_jbm = _jn.nodes.new('ShaderNodeBump'); _jbm.inputs['Strength'].default_value = 0.6; _jbm.inputs['Distance'].default_value = 0.01
_jn.links.new(_puff, _jbm.inputs['Height']); _jn.links.new(_jbm.outputs['Normal'], _jb.inputs['Normal'])
_jcol = mixc(_jn, _puff, (0.008, 0.015, 0.04), (0.03, 0.06, 0.14)); _jn.links.new(_jcol, _jb.inputs['Base Color'])
JACKET.data.materials.append(JACKET_M)
GLOVE_M = mat('glove', (0.42, 0.08, 0.06), 0.9, sheen=0.8)                # red knit gloves
_gn = GLOVE_M.node_tree; _gb = _gn.nodes['Principled BSDF']
_gw = _gn.nodes.new('ShaderNodeTexWave'); _gw.inputs['Scale'].default_value = 140.0; _gw.inputs['Distortion'].default_value = 2.0
_gra = _gn.nodes.new('ShaderNodeAttribute'); _gra.attribute_name = 'rest_position'; _gn.links.new(_gra.outputs['Vector'], _gw.inputs['Vector'])
_gbm = _gn.nodes.new('ShaderNodeBump'); _gbm.inputs['Strength'].default_value = 0.5; _gbm.inputs['Distance'].default_value = 0.002
_gn.links.new(_gw.outputs['Fac'], _gbm.inputs['Height']); _gn.links.new(_gbm.outputs['Normal'], _gb.inputs['Normal'])
_gn.links.new(mixc(_gn, _gw.outputs['Fac'], (0.3, 0.05, 0.04), (0.5, 0.1, 0.07)), _gb.inputs['Base Color'])
BODY.data.materials.append(GLOVE_M); _GLOVE_I = len(BODY.data.materials) - 1
_mi0 = np.zeros(len(BODY.data.polygons), np.int32); BODY.data.polygons.foreach_get('material_index', _mi0)
_glove_f = np.array([np.mean(_hd[list(p_.vertices)]) > 0.5 for p_ in BODY.data.polygons])
_mi1 = np.where(_glove_f, _GLOVE_I, _mi0).astype(np.int32)
COLD = [False]
def dress(cold):
    """cold: puffer sleeves on, gloves on; warm: tee and bare hands"""
    if COLD[0] != cold or cold is None: BODY.data.polygons.foreach_set('material_index', _mi1 if cold else _mi0); BODY.data.update()
    COLD[0] = cold; JACKET.hide_render = (not cold) or BODY.hide_render
dress(None); dress(False)
FROST_SLEEVE = None                                                  # filled in by the frost part (the sleeve and gloves frost over)

# ---- rig controls (from crush/60_pose.py): IK to the wrists, wrist turned by a Copy Rotation, fingers by curl
def ik(bone, target, pole, chain, pole_angle=R(-90)):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TGT = {k: empty('tgt_' + k) for k in ('ankR', 'ankL', 'poleR', 'poleL', 'handR', 'handL', 'poleArmR', 'poleArmL')}
for s_ in ('R', 'L'):
    ik('lowerleg02.' + s_, TGT['ank' + s_], TGT['pole' + s_], 4)
    for bn in ('lowerleg02.', 'upperleg02.'):
        pb = PB[bn + s_]; pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = True
    ik('lowerarm02.' + s_, TGT['hand' + s_], TGT['poleArm' + s_], 4)
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
def fingers(s_, curl, spread=0.0, thumb=None):
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            nm = f'finger{f_}-{seg}.{s_}'
            if nm in PB:
                c__ = (thumb if thumb is not None else curl) if f_ == 1 else curl
                ang = (10, 15, 8)[seg - 1] if f_ == 1 else (40, 55, 30)[seg - 1]; rot(nm, ang * c__, 0, (f_ - 3) * spread * (1 if seg == 1 else 0))
def wpos(bn, tail=False):
    pb = PB[bn]; return RIG.matrix_world @ (pb.tail if tail else pb.head)
HIP0 = (RB['upperleg01.R'].head_local + RB['upperleg01.L'].head_local) * 0.5
EYE0 = (RB['eye.L'].head_local + RB['eye.R'].head_local) * 0.5
PALM_D = 0.068; PALM_T = 0.013
def place_hand(s_, contact, fdir, pdir, w_rot=1.0):
    """middle of his palm on 'contact', fingers along fdir, palm facing pdir"""
    d = Vector(fdir).normalized(); n = Vector(pdir); n = (n - d * n.dot(d)).normalized()
    TGT['hand' + s_].location = Vector(contact) - n * PALM_T - d * PALM_D
    O, e_, c_ = HAND[s_]; c_.influence = w_rot; e_.rotation_quaternion = hand_quat(s_, d, n)
def palm_point(s_):
    """world middle of the palm and its frame (fingers d, palm normal n) from the posed bones"""
    w = wpos('wrist.' + s_); f3 = wpos('finger3-1.' + s_); d = (f3 - w).normalized()
    M_ = (RIG.matrix_world @ PB['finger3-1.' + s_].matrix).to_3x3(); n = M_.col[2]; n = (n - d * n.dot(d)).normalized()
    return w + d * PALM_D + n * PALM_T, d, n

# ---- first person: put him so his eyes sit at the camera, facing where the camera faces (heading only); hands in camera space
def cam_axes():
    M_ = CAM.rotation_quaternion.to_matrix(); return M_.col[0], M_.col[1], -M_.col[2]          # right, up, forward
def cam_pt(x, y, z):
    """camera space (x right, y up, z forward, metres) -> world"""
    r_, u_, f_ = cam_axes(); return CAM.location + r_ * x + u_ * y + f_ * z
def cam_dir(x, y, z):
    r_, u_, f_ = cam_axes(); return (r_ * x + u_ * y + f_ * z).normalized()
HANDS_DOWN = {'R': None, 'L': None}
def fpv(spine=0.0, eye_back=0.04, hide=False):
    """place the body under the camera. eye_back: the camera sits this far in front of the eyes (inside the hidden head)"""
    for o in (BODY, SUIT): o.hide_render = hide
    JACKET.hide_render = hide or not COLD[0]
    if hide: return
    r_, u_, f_ = cam_axes(); fh = Vector((f_.x, f_.y, 0)).normalized()
    th = math.atan2(fh.x, -fh.y); RIG.rotation_euler = (0, 0, th)
    RIG.location = Vector((0, 0, 0)); bpy.context.view_layer.update()
    for n, k in (('spine03', 0.3), ('spine02', 0.35), ('spine01', 0.35)): rot(n, spine * k)
    eye = RIG.matrix_world @ EYE0; RIG.location = CAM.location - fh * eye_back - (eye - RIG.location) + Vector((0, 0, 0))
    bpy.context.view_layer.update()
    hipw = RIG.matrix_world @ HIP0; rt = Vector((math.cos(th), math.sin(th), 0))
    for s_, sg in (('R', -1), ('L', 1)):                                # feet under the hips (never seen, keeps the legs calm)
        TGT['ank' + s_].location = hipw + rt * (0.11 * sg) - Vector((0, 0, 0.82)) - fh * 0.02
        TGT['pole' + s_].location = hipw + rt * (0.11 * sg) - Vector((0, 0, 0.4)) + fh * 0.6
    for s_, sg in (('R', -1), ('L', 1)): TGT['poleArm' + s_].location = hipw + rt * (0.7 * sg) - fh * 0.35 + Vector((0, 0, 0.1))
def arm_down(s_):
    """a relaxed arm hanging at his side, out of the shot"""
    O, e_, c_ = HAND[s_]; c_.influence = 0.0; sg = -1 if s_ == 'R' else 1
    th = RIG.rotation_euler.z; rt = Vector((math.cos(th), math.sin(th), 0)); fh = Vector((-math.sin(th), math.cos(th), 0)) * -1
    TGT['hand' + s_].location = (RIG.matrix_world @ HIP0) + rt * (0.24 * sg) + Vector((0, 0, -0.02)) + fh * 0.05
    fingers(s_, 0.3)

# ================================================================ the ocean under the ice: a cut-open block on a dark stage (house x-ray look),
# then down to a hot vent on the sea floor with tube worms, and a close look at the microbes living off its chemicals
SS = Vector((0, -200000, 0))
BW, BD, BH = 7.0, 3.0, 9.0                                          # the block: width, depth, height of the water
ICE_T = 1.1
# ice lid: white-blue, cracked, a little see-through at the cut
ICE_M = mat('ice_lid', (0.75, 0.85, 0.95), 0.25, trans=0.35, ior=1.31); _in = ICE_M.node_tree; _ib = _in.nodes['Principled BSDF']
_ivo = _in.nodes.new('ShaderNodeTexVoronoi'); _ivo.feature = 'DISTANCE_TO_EDGE'; _ivo.inputs['Scale'].default_value = 0.8; _ivo.inputs['Randomness'].default_value = 1.0; _in.links.new(coord(_in), _ivo.inputs['Vector'])
_icr = math_(_in, 'MULTIPLY', math_(_in, 'LESS_THAN', _ivo.outputs['Distance'], 0.02), math_(_in, 'GREATER_THAN', tnoise(_in, coord(_in), 1.2, 3), 0.45))
_in.links.new(mixc(_in, _icr, mixc(_in, tnoise(_in, coord(_in), 3.0, 6), (0.55, 0.72, 0.88), (0.85, 0.92, 0.98)), (1.0, 1.0, 1.0)), _ib.inputs['Base Color'])
_ib.inputs['Emission Color'].default_value = (0.5, 0.75, 1.0, 1); _in.links.new(math_(_in, 'MULTIPLY', _icr, 0.8), _ib.inputs['Emission Strength'])
SEA = []
ICE_LID = box('ice_lid', (BW, BD, ICE_T), SS + Vector((0, 0, ICE_T / 2)), ICE_M, bv=0.03); SEA.append(ICE_LID)
SNOW_M = mat('snow', (0.9, 0.92, 0.96), 0.6); SEA.append(box('snow_top', (BW, BD, 0.08), SS + Vector((0, 0, ICE_T + 0.04)), SNOW_M, bv=0.03))
# water: a see-through glowing blue block, brighter at the top, deep blue at the bottom; currents swirl inside
WATER_M = bpy.data.materials.new('sea_water'); WATER_M.use_nodes = True; _wn2 = WATER_M.node_tree; _wb2 = _wn2.nodes['Principled BSDF']; WATER_M.blend_method = 'BLEND'
_wz = sepz(_wn2, coord(_wn2, 'Generated'))
_wcol = ramp(_wn2, _wz.outputs['Z'], [(0.0, (0.0, 0.02, 0.08)), (0.6, (0.02, 0.15, 0.38)), (1.0, (0.08, 0.35, 0.6))])
_wsw = _wn2.nodes.new('ShaderNodeTexNoise'); _wsw.noise_dimensions = '4D'; _wsw.inputs['Scale'].default_value = 0.6; _wsw.inputs['Distortion'].default_value = 3.0
_wn2.links.new(coord(_wn2, 'Object'), _wsw.inputs['Vector']); _wn2.links.new(objattr(_wn2, 'w'), _wsw.inputs['W'])
_wn2.links.new(_wcol, _wb2.inputs['Base Color']); _wn2.links.new(_wcol, _wb2.inputs['Emission Color'])
_wn2.links.new(math_(_wn2, 'MULTIPLY_ADD', _wsw.outputs['Fac'], 1.4, 0.15), _wb2.inputs['Emission Strength'])
_wb2.inputs['Alpha'].default_value = 0.88; _wb2.inputs['Roughness'].default_value = 0.35; _wb2.inputs['Specular IOR Level'].default_value = 0.15
WATER = box('sea_water', (BW, BD, BH), SS + Vector((0, 0, -BH / 2)), WATER_M); WATER['w'] = 0.0; SEA.append(WATER)
# the sea floor slab and its rocky top
FLOOR_M = noisy(mat('seafloor', (0.12, 0.1, 0.09), 0.9), 2.0, 0.4)
SEA.append(box('floor_slab', (BW, BD, 0.9), SS + Vector((0, 0, -BH - 0.45)), FLOOR_M, bv=0.03))
CURR_M = emis_mix('current', (0.5, 0.85, 1.0), 3.0, 'a')
CURRENTS = []
random.seed(77)
for k in range(28):                                                 # streaks riding slow loops: the water is still moving
    o = prim('uv_sphere', f'cur{k}', CURR_M, segments=10, ring_count=6, radius=0.05, scale=(1.0, 1.0, 1.0)); o['a'] = 0.0
    o['ph'] = (random.uniform(-2.6, 2.6), random.uniform(-1.0, 1.0), random.uniform(-BH + 1.2, -1.0), random.uniform(0.6, 1.6), random.uniform(0, 6.28), random.uniform(0.25, 0.6))
    o.visible_shadow = False; o.rotation_mode = 'QUATERNION'; CURRENTS.append(o)
def fish(name, at, size, col):
    m = mat(name + '_m', col, 0.4, emit=col, estr=0.6)
    body = prim('uv_sphere', name, m, loc=at, segments=16, ring_count=10, radius=size, scale=(2.4, 0.55, 0.9))
    tail = mesh(name + '_tail', [(-size * 2.2, 0, 0), (-size * 3.3, 0, size * 0.8), (-size * 3.3, 0, -size * 0.8)], [(0, 1, 2)], m, parent=body)
    tail.location = (0, 0, 0); body.rotation_mode = 'XYZ'; return [body, tail]
FISH = []
for k in range(5):
    FISH.append(fish(f'fish{k}', SS + Vector((0, 0, -3 - k)), random.uniform(0.09, 0.15), (0.35, 0.6, 0.7)))
SEA += CURRENTS + [p_ for f_ in FISH for p_ in f_]
def sea_set(t, a_cur=1.0):
    WATER['w'] = 0.12 * t
    for o in CURRENTS:
        x0, y0, z0, r_, ph, sp = o['ph']; a_ = ph + sp * t * 2.0
        p_ = Vector((x0 + r_ * math.cos(a_), y0, z0 + 0.6 * r_ * math.sin(a_))); p_.x = clamp(p_.x, -BW / 2 + 0.2, BW / 2 - 0.2)
        o.location = SS + p_; tg = Vector((-math.sin(a_), 0, 0.6 * math.cos(a_))).normalized()
        o.rotation_quaternion = tg.to_track_quat('X', 'Z'); o.scale = (3.5, 0.6, 0.6); o['a'] = a_cur
    for k, (b_, tl) in enumerate(FISH):
        u_ = (0.08 * t * (1 + 0.3 * k) + h1(k + 1)) % 1.0; dirn = 1 if k % 2 == 0 else -1
        x_ = (-BW / 2 + 0.4 + (BW - 0.8) * u_) * dirn; b_.location = SS + Vector((x_, -0.3 + 0.5 * h1(k + 7), -1.6 - 1.4 * k + 0.15 * math.sin(t * 2 + k)))
        b_.rotation_euler = (0, 0.1 * math.sin(t * 3 + k), 0 if dirn > 0 else math.pi)

# ---- the vent (on the sea floor of its own stage, far below the block): a chimney with glowing cracks, black smoke, tube worms
VS = SS + Vector((0, 0, -400))
CHIM_M = mat('chimney', (0.08, 0.07, 0.065), 0.85); _cm = CHIM_M.node_tree; _cb = _cm.nodes['Principled BSDF']
_cvo = _cm.nodes.new('ShaderNodeTexVoronoi'); _cvo.feature = 'DISTANCE_TO_EDGE'; _cvo.inputs['Scale'].default_value = 2.2; _cm.links.new(coord(_cm), _cvo.inputs['Vector'])
_cz = sepz(_cm, coord(_cm, 'Object'))
_ccr = math_(_cm, 'MULTIPLY', math_(_cm, 'POWER', math_(_cm, 'MAXIMUM', math_(_cm, 'SUBTRACT', 1.0, math_(_cm, 'MULTIPLY', _cvo.outputs['Distance'], 12.0)), 0.0), 2.0),
             math_(_cm, 'MAXIMUM', math_(_cm, 'SUBTRACT', 1.0, math_(_cm, 'DIVIDE', _cz.outputs['Z'], 3.4)), 0.15))
_cb.inputs['Emission Color'].default_value = (1.0, 0.38, 0.05, 1); _cm.links.new(math_(_cm, 'MULTIPLY', math_(_cm, 'MULTIPLY', _ccr, math_(_cm, 'GREATER_THAN', tnoise(_cm, coord(_cm), 0.9, 2), 0.5)), 5.0), _cb.inputs['Emission Strength'])
_cmn = _cm.nodes.new('ShaderNodeBump'); _cmn.inputs['Strength'].default_value = 0.6; _cm.links.new(tnoise(_cm, coord(_cm), 5.0, 8), _cmn.inputs['Height']); _cm.links.new(_cmn.outputs['Normal'], _cb.inputs['Normal'])
VENT = []
_prof = [(0.0, 0.0), (0.95, 0.0), (0.8, 0.5), (0.62, 1.2), (0.55, 2.0), (0.42, 2.8), (0.36, 3.3), (0.28, 3.5), (0.18, 3.5), (0.12, 3.2)]
CHIM = lathe('chimney', _prof, 40, CHIM_M, loc=VS); _cd = CHIM.modifiers.new('lumps', 'DISPLACE'); _ctx = bpy.data.textures.new('chim_tx', 'CLOUDS'); _ctx.noise_scale = 0.35
_cd.texture = _ctx; _cd.strength = 0.25; subsurf(CHIM, 1); VENT.append(CHIM)
for k, (dx, dy, sc_) in enumerate([(-1.6, 0.4, 0.55), (1.5, -0.2, 0.45), (0.8, 1.4, 0.35)]):
    o = lathe(f'chim_s{k}', [(r_ * sc_, z_ * sc_) for r_, z_ in _prof], 32, CHIM_M, loc=VS + Vector((dx, dy, 0))); _md = o.modifiers.new('lumps', 'DISPLACE'); _md.texture = _ctx; _md.strength = 0.15; VENT.append(o)
SEAFLOOR = lathe('vent_floor', [(0, -0.2), (6, -0.1), (40, 0.2), (200, 2.0)], 64, FLOOR_M, loc=VS); VENT.append(SEAFLOOR)
_sfb = FLOOR_M.node_tree; _sfbm = _sfb.nodes.new('ShaderNodeBump'); _sfbm.inputs['Strength'].default_value = 0.5
_sfb.links.new(tnoise(_sfb, coord(_sfb), 3.0, 8), _sfbm.inputs['Height']); _sfb.links.new(_sfbm.outputs['Normal'], _sfb.nodes['Principled BSDF'].inputs['Normal'])
# black smoke: soft cards that rise and grow, lit orange from below
SMOKE_M = bpy.data.materials.new('smoke'); SMOKE_M.use_nodes = True; _sm = SMOKE_M.node_tree; _smb = _sm.nodes['Principled BSDF']; SMOKE_M.blend_method = 'BLEND'
_smg = _sm.nodes.new('ShaderNodeTexGradient'); _smg.gradient_type = 'SPHERICAL'; _sm.links.new(coord(_sm, 'Object'), _smg.inputs['Vector'])
_smn = _sm.nodes.new('ShaderNodeTexNoise'); _smn.noise_dimensions = '4D'; _smn.inputs['Scale'].default_value = 2.5; _smn.inputs['Detail'].default_value = 6
_sm.links.new(coord(_sm, 'Object'), _smn.inputs['Vector']); _sm.links.new(objattr(_sm, 'w'), _smn.inputs['W'])
_sma = math_(_sm, 'MULTIPLY', math_(_sm, 'MULTIPLY', math_(_sm, 'POWER', _smg.outputs['Fac'], 1.2), math_(_sm, 'MAXIMUM', math_(_sm, 'SUBTRACT', math_(_sm, 'MULTIPLY', _smn.outputs['Fac'], 2.0), 0.6), 0.0)), objattr(_sm, 'a'))
_sm.links.new(math_(_sm, 'MINIMUM', _sma, 1.0), _smb.inputs['Alpha']); _smb.inputs['Base Color'].default_value = (0.18, 0.17, 0.17, 1); _smb.inputs['Roughness'].default_value = 1.0
_smb.inputs['Emission Color'].default_value = (1.0, 0.35, 0.08, 1); _sm.links.new(math_(_sm, 'MULTIPLY', objattr(_sm, 'glow'), 1.0), _smb.inputs['Emission Strength'])
SMOKE = []
for k in range(14):
    o = prim('plane', f'smoke{k}', SMOKE_M, size=2.0); o['a'] = 0.0; o['w'] = h1(k) * 10; o['glow'] = 0.0; o['ph'] = h1(k + 20); o.visible_shadow = False
    o.rotation_mode = 'QUATERNION'; SMOKE.append(o)
VENT += SMOKE
# tube worms: white tubes with red plumes, swaying
WORM_T = mat('worm_tube', (0.85, 0.82, 0.75), 0.6); WORM_P = mat('worm_plume', (0.75, 0.04, 0.04), 0.4, sheen=0.6)
WORMS = []
random.seed(55)
_clumps = [(-1.15, -0.55), (1.2, -0.75), (-0.2, -1.05), (0.55, 0.9), (-1.0, 0.8)]
for k in range(44):
    cx_, cy_ = _clumps[k % len(_clumps)]; base = VS + Vector((cx_ + random.uniform(-0.28, 0.28), cy_ + random.uniform(-0.2, 0.2), 0.0)); h_ = random.uniform(0.45, 1.1)
    t_ = tube(f'worm{k}', [(0, 0, 0), (0, 0, h_ * 0.5), (0, 0, h_)], 0.05, WORM_T, seg=10); t_.location = base
    p_ = prim('uv_sphere', f'plume{k}', WORM_P, loc=(0, 0, h_ + 0.09), segments=14, ring_count=8, radius=0.1, scale=(1, 1, 1.5)); p_.parent = t_
    t_.rotation_mode = 'XYZ'; t_['ph'] = random.uniform(0, 6.3); WORMS.append(t_); VENT += [t_, p_]
VENT_L = light_at('vent_light', 'POINT', VS + Vector((0, -0.4, 2.2)), VS, 0.0, (1.0, 0.45, 0.12), 0.4)
VENT_FILL = light_at('vent_fill', 'AREA', VS + Vector((-4, -6, 6)), VS + Vector((0, 0, 1.5)), 0.0, (0.3, 0.5, 1.0), 4)
def vent_set(t):
    for k, o in enumerate(SMOKE):
        age = (o['ph'] + 0.35 * t) % 1.0; z_ = 3.2 + 6.0 * age; sc_ = 0.35 + 2.2 * age
        o.location = VS + Vector((0.25 * math.sin(k * 1.7 + t * 0.6) * age, -0.05 * k, z_)); o.scale = (sc_, sc_, sc_)
        o['a'] = smooth(0.0, 0.08, age) * (1 - smooth(0.7, 1.0, age)) * 0.85; o['w'] = h1(k) * 10 + 0.4 * t; o['glow'] = 1.5 * (1 - smooth(0.0, 0.5, age))
        o.rotation_quaternion = (CAM.location - o.location).to_track_quat('Z', 'Y')
    for o in WORMS: o.rotation_euler = (0.12 * math.sin(t * 1.3 + o['ph']), 0.12 * math.cos(t * 1.1 + o['ph']), 0)

# ---- the microbes up close (their own little stage): a rock face, rod-shaped microbes glowing green, chemical specks drifting in and eaten
MS = SS + Vector((0, 0, -900))
MROCK_M = noisy(mat('mrock', (0.1, 0.08, 0.07), 0.9), 3.0, 0.4); _mr = MROCK_M.node_tree; _mrb = _mr.nodes['Principled BSDF']
_mrm = _mr.nodes.new('ShaderNodeBump'); _mrm.inputs['Strength'].default_value = 0.35; _mr.links.new(tnoise(_mr, coord(_mr), 1.5, 10), _mrm.inputs['Height']); _mr.links.new(_mrm.outputs['Normal'], _mrb.inputs['Normal'])
_mrb.inputs['Emission Color'].default_value = (1.0, 0.4, 0.08, 1)
_mr.links.new(math_(_mr, 'MULTIPLY', math_(_mr, 'POWER', math_(_mr, 'MAXIMUM', math_(_mr, 'SUBTRACT', tnoise(_mr, coord(_mr), 0.8, 3), 0.55), 0.0), 1.5), 3.0), _mrb.inputs['Emission Strength'])
_mv, _mf = [], []; _MN = 60
for j in range(_MN):
    for i in range(_MN):
        x_ = -1.5 + 3.0 * i / (_MN - 1); y_ = -1.5 + 3.0 * j / (_MN - 1); _mv.append((x_, y_, 0.12 * mnoise.noise(Vector((x_ * 1.3, y_ * 1.3, 0.5))) + 0.05 * mnoise.noise(Vector((x_ * 4, y_ * 4, 2)))))
for j in range(_MN - 1):
    for i in range(_MN - 1): a0 = j * _MN + i; _mf.append((a0, a0 + 1, a0 + _MN + 1, a0 + _MN))
MROCK = mesh('mrock', _mv, _mf, MROCK_M, loc=MS); subsurf(MROCK, 1)
MICRO_M = mat('microbe', (0.1, 0.55, 0.3), 0.3, trans=0.15, emit=(0.25, 1.0, 0.5), estr=0.8); _mi = MICRO_M.node_tree; _mib = _mi.nodes['Principled BSDF']
_mlw = _mi.nodes.new('ShaderNodeLayerWeight'); _mlw.inputs['Blend'].default_value = 0.4
_mi.links.new(math_(_mi, 'ADD', math_(_mi, 'MULTIPLY', _mlw.outputs['Facing'], 2.5), math_(_mi, 'MULTIPLY', math_(_mi, 'GREATER_THAN', tnoise(_mi, coord(_mi, 'Object'), 9.0, 2), 0.62), 1.5)), _mib.inputs['Emission Strength'])
MICROBES = []
random.seed(91)
_mrM = MROCK.matrix_world
def rock_pt(x_, y_, lift=0.0):
    z_ = 0.12 * mnoise.noise(Vector((x_ * 1.3, y_ * 1.3, 0.5))) + 0.05 * mnoise.noise(Vector((x_ * 4, y_ * 4, 2)))
    return MS + Vector((x_, y_, z_ + lift)), Vector((0, 0, 1))
for k in range(80):
    x_, y_ = random.gauss(0, 0.35), random.gauss(0, 0.35); p_, n_ = rock_pt(x_, y_, 0.028)
    o = prim('uv_sphere', f'mic{k}', MICRO_M, loc=p_, segments=20, ring_count=14, radius=0.021, scale=(1, 1, random.uniform(2.0, 3.2)))
    o.rotation_mode = 'XYZ'; o['ph'] = random.uniform(0, 6.3); o['rot0'] = (R(random.uniform(60, 120)), 0, random.uniform(0, 6.3)); o['p0'] = p_; MICROBES.append(o)
CHEM_M = emis('chem', (1.0, 0.8, 0.15), 6.0)
CHEMS = []
for k in range(70):
    o = prim('ico_sphere', f'chem{k}', CHEM_M, subdivisions=1, radius=0.011); o['tgt'] = k % len(MICROBES); o['ph'] = h1(k + 40); o.visible_shadow = False; CHEMS.append(o)
MIC_L = light_at('mic_light', 'AREA', MS + Vector((0, -2.2, 1.6)), MS, 0.0, (0.5, 0.7, 1.0), 2.0)
MIC_KICK = light_at('mic_kick', 'POINT', MS + Vector((0.8, 0.6, -0.6)), MS, 0.0, (1.0, 0.45, 0.12), 0.3)
MICRO_ALL = [MROCK] + MICROBES + CHEMS
def micro_set(t):
    for o in MICROBES:
        ph = o['ph']; r0 = o['rot0']; o.rotation_euler = (r0[0] + 0.25 * math.sin(t * 3.1 + ph), r0[1] + 0.2 * math.sin(t * 2.3 + ph * 2), r0[2] + 0.3 * math.sin(t * 1.7 + ph))
        o.location = Vector(o['p0']) + Vector((0.01 * math.sin(t * 2 + ph), 0.01 * math.cos(t * 1.6 + ph), 0))
    for o in CHEMS:
        tg = MICROBES[o['tgt']]; age = (o['ph'] + 0.5 * t) % 1.0; src = Vector(tg['p0']) + Vector((0.3 * math.sin(o['ph'] * 20), -0.35, 0.45))
        o.location = src.lerp(tg.location, sm(age)); s_ = 1.0 - smooth(0.85, 1.0, age); o.scale = (max(s_, 0.01),) * 3; o.hide_render = s_ < 0.05
SEA_ALL = SEA + VENT + MICRO_ALL
SEA_KEY = light_at('sea_key', 'AREA', SS + Vector((-5, -10, 6)), SS + Vector((0, 0, -2)), 4000, (0.7, 0.85, 1.0), 6)

# ================================================================ props and effects
# ---- the stopwatch that lies in your open left hand: chrome case, crown and loop, white dial, ticks, a red sweep hand
SW_R = 0.028; SW_T = 0.013
CHROME = mat('chrome', (0.8, 0.78, 0.74), 0.22, 1.0)
DIAL_M = mat('dial', (0.95, 0.94, 0.9), 0.45, emit=(1.0, 0.98, 0.94), estr=0.25)
INK = mat('sw_ink', (0.03, 0.03, 0.03), 0.5)
HAND_RED = mat('sw_red', (0.85, 0.05, 0.03), 0.3, emit=(0.6, 0.0, 0.0), estr=0.3)
SWATCH = empty('stopwatch'); SWATCH.rotation_mode = 'QUATERNION'
SW = [lathe('sw_case', [(0, -SW_T / 2), (SW_R * 0.9, -SW_T / 2), (SW_R, -SW_T * 0.25), (SW_R, SW_T * 0.3), (SW_R * 0.93, SW_T / 2), (SW_R * 0.88, SW_T / 2)], 48, CHROME, SWATCH)]
SW.append(lathe('sw_dial', [(0, SW_T / 2 - 0.0005), (SW_R * 0.88, SW_T / 2 - 0.0005)], 48, DIAL_M, SWATCH))
for k in range(60):                                                 # minute/second ticks (longer every 5)
    a_ = 2 * math.pi * k / 60; L_ = 0.0045 if k % 5 == 0 else 0.0022; r_ = SW_R * 0.82 - L_ / 2
    o = box(f'sw_tick{k}', (0.0007 if k % 5 else 0.0011, L_, 0.0004), (r_ * math.sin(a_), r_ * math.cos(a_), SW_T / 2), INK, rot=(0, 0, -a_), parent=SWATCH); SW.append(o)
SW_SUB = lathe('sw_sub', [(0.0058, SW_T / 2 + 0.0001), (0.0066, SW_T / 2 + 0.0001), (0.0066, SW_T / 2 + 0.0003)], 32, INK, SWATCH); SW_SUB.location = (0, -0.010, 0); SW.append(SW_SUB)
SW_HAND = empty('sw_hand_pivot', SWATCH); SW_HAND.rotation_mode = 'XYZ'
SW.append(box('sw_hand', (0.0009, SW_R * 0.95, 0.0005), (0, SW_R * 0.33, SW_T / 2 + 0.0008), HAND_RED, parent=SW_HAND))
SW.append(prim('cylinder', 'sw_hub', HAND_RED, parent=SWATCH, loc=(0, 0, SW_T / 2 + 0.0009), radius=0.0018, depth=0.0012, vertices=16))
SW.append(prim('cylinder', 'sw_stem', CHROME, parent=SWATCH, loc=(0, SW_R + 0.003, 0), rot=(R(90), 0, 0), radius=0.003, depth=0.007, vertices=16))
SW.append(prim('cylinder', 'sw_crown', CHROME, parent=SWATCH, loc=(0, SW_R + 0.0075, 0), rot=(R(90), 0, 0), radius=0.0045, depth=0.004, vertices=24))
SW.append(prim('torus', 'sw_loop', CHROME, parent=SWATCH, loc=(0, SW_R + 0.0145, 0), rot=(0, R(90), 0), major_radius=0.0065, minor_radius=0.0012, major_segments=24, minor_segments=8))
SW_ALL = [SWATCH, SW_HAND] + SW
def stopwatch_set(on, pos=None, quat=None, secs=0.0):
    for o in SW: o.hide_render = not on
    if not on: return
    SWATCH.location = pos; SWATCH.rotation_quaternion = quat; SW_HAND.rotation_euler = (0, 0, -2 * math.pi * (secs % 60.0) / 60.0)

# ---- breath: soft white puffs that leave from just under the lens, roll forward and fade
BREATH_M = bpy.data.materials.new('breath'); BREATH_M.use_nodes = True; _bn = BREATH_M.node_tree; _bb = _bn.nodes['Principled BSDF']; BREATH_M.blend_method = 'BLEND'
_bg = _bn.nodes.new('ShaderNodeTexGradient'); _bg.gradient_type = 'SPHERICAL'; _bn.links.new(coord(_bn, 'Object'), _bg.inputs['Vector'])
_bz = _bn.nodes.new('ShaderNodeTexNoise'); _bz.noise_dimensions = '4D'; _bz.inputs['Scale'].default_value = 3.0; _bz.inputs['Detail'].default_value = 5
_bn.links.new(coord(_bn, 'Object'), _bz.inputs['Vector']); _bn.links.new(objattr(_bn, 'w'), _bz.inputs['W'])
_ba = math_(_bn, 'MULTIPLY', math_(_bn, 'MULTIPLY', math_(_bn, 'POWER', _bg.outputs['Fac'], 1.5), math_(_bn, 'MAXIMUM', math_(_bn, 'SUBTRACT', math_(_bn, 'MULTIPLY', _bz.outputs['Fac'], 2.2), 0.7), 0.0)), objattr(_bn, 'a'))
_bn.links.new(math_(_bn, 'MINIMUM', math_(_bn, 'MULTIPLY', _ba, 0.6), 0.5), _bb.inputs['Alpha']); _bb.inputs['Base Color'].default_value = (0.9, 0.93, 0.98, 1); _bb.inputs['Roughness'].default_value = 1.0
_bb.inputs['Emission Color'].default_value = (0.8, 0.88, 1.0, 1); _bb.inputs['Emission Strength'].default_value = 0.35
BREATH = []
for k in range(4):
    o = prim('plane', f'breath{k}', BREATH_M, size=2.0); o['a'] = 0.0; o['w'] = 3.0 * k; o.visible_shadow = False; o.rotation_mode = 'QUATERNION'; BREATH.append(o)
def breath_set(t, starts, amt=1.0):
    """puffs that start at the given times (seconds); each lives 1.3 s"""
    for k, o in enumerate(BREATH):
        o.hide_render = True
        if k >= len(starts): continue
        age = (t - starts[k]) / 1.3
        if not (0.0 <= age <= 1.0): continue
        o.hide_render = False; o['a'] = amt * smooth(0.0, 0.12, age) * (1 - smooth(0.45, 1.0, age)); o['w'] = 3.0 * k + 0.8 * age
        o.location = cam_pt(0.02 * math.sin(k * 2.1), -0.1 + 0.07 * age, 0.17 + 0.3 * age); s_ = 0.045 + 0.12 * age; o.scale = (s_, s_ * 0.7, s_)
        o.rotation_quaternion = CAM.rotation_quaternion @ Quaternion((0, 0, 1), 0.6 * k + 0.3 * age)

# ---- ice crystals glittering down through the porch light (day 3)
XTAL_M = mat('xtal', (0.9, 0.95, 1.0), 0.05, emit=(0.8, 0.9, 1.0), estr=1.5)
XTALS = []
random.seed(66)
for k in range(70):
    o = prim('ico_sphere', f'xtal{k}', XTAL_M, subdivisions=1, radius=random.uniform(0.0018, 0.0035)); o['ph'] = (random.uniform(-1.2, 1.2), random.uniform(0.4, 3.5), random.uniform(0, 1), random.uniform(0.25, 0.5))
    o.visible_shadow = False; XTALS.append(o)
def xtal_set(t, on):
    for o in XTALS:
        o.hide_render = not on
        if not on: continue
        x_, z_, p0, sp = o['ph']; y_ = 1.2 - 2.4 * ((p0 + sp * t * 0.35) % 1.0)
        o.location = cam_pt(x_ * z_ * 0.55 + 0.03 * math.sin(t * 2 + p0 * 9), y_ * z_ * 0.55, z_)

# ---- birds crossing the day sky (two flapping wings each)
BIRD_M = mat('bird', (0.03, 0.03, 0.035), 0.8)
BIRDS = []
for k in range(4):
    b_ = empty(f'bird{k}'); b_.rotation_mode = 'XYZ'; wings = []
    for sg in (-1, 1):
        w_ = mesh(f'bird{k}_w{sg}', [(0, -0.12, 0), (0, 0.12, 0), (sg * 0.55, 0.0, 0.0)], [(0, 1, 2)], BIRD_M, parent=b_); w_.rotation_mode = 'XYZ'; wings.append(w_)
    bod = prim('uv_sphere', f'bird{k}_b', BIRD_M, parent=b_, segments=8, ring_count=6, radius=0.09, scale=(0.6, 2.2, 0.6)); BIRDS.append((b_, wings, bod))
def birds_set(t, on):
    for k, (b_, wings, bod) in enumerate(BIRDS):
        for o in wings + [bod]: o.hide_render = not on
        if not on: continue
        u_ = t * 0.035 + 0.17 * k; b_.location = Vector((-60 + 120 * (u_ % 1.0) + 3 * k, 70 + 6 * k, 22 + 2.5 * k + 1.5 * math.sin(t * 0.8 + k)))
        b_.rotation_euler = (0, 0, R(-90)); b_.scale = (4, 4, 4); fl = 0.6 * math.sin(t * 9 + k * 1.3)
        wings[0].rotation_euler = (0, fl, 0); wings[1].rotation_euler = (0, -fl, 0)

# ---- soft clouds low in the day sky
CLOUD_M = bpy.data.materials.new('cloud_card'); CLOUD_M.use_nodes = True; _cc = CLOUD_M.node_tree; _ccb = _cc.nodes['Principled BSDF']; CLOUD_M.blend_method = 'BLEND'
_ccg = _cc.nodes.new('ShaderNodeTexGradient'); _ccg.gradient_type = 'SPHERICAL'; _cc.links.new(coord(_cc, 'Object'), _ccg.inputs['Vector'])
_ccn = tnoise(_cc, coord(_cc, 'Object'), 2.2, 7, 0.3)
_cc.links.new(math_(_cc, 'MINIMUM', math_(_cc, 'MULTIPLY', math_(_cc, 'POWER', _ccg.outputs['Fac'], 0.8), math_(_cc, 'MAXIMUM', math_(_cc, 'SUBTRACT', math_(_cc, 'MULTIPLY', _ccn, 2.6), 1.05), 0.0)), 1.0), _ccb.inputs['Alpha'])
_ccb.inputs['Base Color'].default_value = (1.0, 0.95, 0.9, 1); _ccb.inputs['Roughness'].default_value = 1.0
_ccb.inputs['Emission Color'].default_value = (1.0, 0.85, 0.7, 1); _ccb.inputs['Emission Strength'].default_value = 0.6
CLOUDS_D = []
random.seed(18)
for k in range(9):
    az = R(random.uniform(-40, 40)); el = R(random.uniform(6, 22)); d_ = random.uniform(1800, 2600)
    p_ = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))) * d_
    o = prim('plane', f'cloud{k}', CLOUD_M, loc=p_, size=2.0); s_ = random.uniform(160, 320); o.scale = (s_ * 2.2, s_, s_)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (-p_).to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), random.uniform(-0.15, 0.15)); o.visible_shadow = False; CLOUDS_D.append(o)
YARD += CLOUDS_D
frostify(JACKET_M); frostify(GLOVE_M)                               # the sleeve and gloves frost over with everything else

# ================================================================ the story: one shot per line (times from times.json)
END = TOTAL
LIGHTS = {'yard': [SUN_O, NIGHT_O, PORCH], 'space': [SPACE_FILL, PLUTO_KEY], 'sea': [SEA_KEY, VENT_L, VENT_FILL, MIC_L, MIC_KICK]}
GROUPS = {'space': SPACE, 'yard': YARD, 'sea': SEA, 'vent': VENT, 'micro': MICRO_ALL}
def mode(which):
    """show one stage, hide the rest (and their lights)"""
    on = {'space': ('space',), 'yard': ('yard',), 'sea': ('sea',), 'vent': ('vent',), 'micro': ('micro',)}[which]
    for g, objs in GROUPS.items(): show(objs, g in on)
    for g, ls in LIGHTS.items():
        for o in ls: o.hide_render = not ((g == 'yard' and which == 'yard') or (g == 'space' and which == 'space') or (g == 'sea' and which in ('sea', 'vent', 'micro')))
    if which != 'yard': SKY_DAYK.outputs[0].default_value = 0.0
    if TRAIL is not None: TRAIL.hide_render = True
    stopwatch_set(False); breath_set(0, []); xtal_set(0, False); birds_set(0, False); fpv(hide=True)
def punch(lt, lens):
    """the house punch cut: lands a little zoomed in and settles in 0.2 s"""
    return lens * (1.0 + 0.07 * (1.0 - smooth(0.0, 0.2, lt)))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x, 0, 1); return x ** 3
def yaw_pitch(yaw, pitch, base=None):
    """a look target from the eye: yaw right of north, pitch up (degrees)"""
    e_ = EYE if base is None else base; return e_ + Vector((math.sin(R(yaw)) * math.cos(R(pitch)), math.cos(R(yaw)) * math.cos(R(pitch)), math.sin(R(pitch))))
def handheld(t, amt=1.0):
    return Vector((wob(t, 0.35, 1.0) * 0.6, 0.0, wob(t, 0.3, 2.0) * 0.45)) * amt, wob(t, 0.25, 5.0) * 0.6 * amt   # (yaw, pitch) wobble in degrees, roll
def fpv_look(t, yaw, pitch, lens, fstop=8.0, focus_d=4.0, amt=1.0, roll=0.0):
    w_, rl = handheld(t, amt); yy, pp = yaw + w_.x, pitch + w_.z
    look(EYE, yaw_pitch(yy, pp), lens=lens, fstop=fstop, roll=R(rl + roll))
    CAM.data.dof.focus_distance = focus_d

# ---- shot 0 (and the loop tail): the Sun, close, shuddering, then gone
def cam0(c):
    """frame one's camera, a slow push; c = seconds from frame one"""
    return SUN_C + Vector((0.6 * math.sin(0.35 * c), -46.0 + 7.0 * c, -1.0)), SUN_C + Vector((0.0, 0.0, -1.6)) + Vector((0.0, 0.0, 0.25 * c))
def shot_sun(t, c):
    mode('space'); r_ = sun_story(c); bloom(0.45, 0.9); S.view_settings.exposure = 0.0
    EARTH.hide_render = True; CLOUDS.hide_render = True; ATM.hide_render = True; PLUTO.hide_render = True; show(DASHES, False)
    cp, ct = cam0(c)
    if c < 0:                                                          # the loop tail: pulled back out of the Sun's face onto frame one's camera
        k = ease_out((c + 0.45) / 0.45); cp0, ct0 = cam0(0.0)
        cp = (SUN_C + Vector((0.0, -15.5, -0.6))).lerp(cp, k); ct = (SUN_C + Vector((0, 0, -0.3))).lerp(ct, k)
    sh = shake(c, 0.6, 3.0) * math.exp(-2.5 * max(c - 1.4, 0)) * smooth(1.32, 1.42, c) if c > 1.3 else Vector()
    look(cp + sh, ct + sh, lens=30.0, fstop=16.0)

# ---- shots 1, 2 and 10: the sunny yard from your eyes
T_BO = B[2] + 0.1457 * DUR[2]                                       # lights out, on the word (the label lands with it)
T_MOON = B[2] + 0.62 * DUR[2]                                       # "Moon goes dark"
SW_T0, SW_T1 = 2.347, 5.444                                         # the burned-in 8:20 countdown
WATCH_CURL, WATCH_THUMB, WATCH_SLIDE, WATCH_LIFT = 0.7, 0.55, -0.003, 0.019             # fingers wrap the watch's top edge (tuned with handchk.py)
def watch_hand(t, lift=0.0, drop=0.0):
    """left hand open, palm up and toward you, the stopwatch lying in it; drop 0..1 lowers it out of the shot"""
    fd = cam_dir(0.12, 1.0, 0.35); pd = cam_dir(0.05, 0.3, -1.0)       # palm turned to you, fingers up: the dial faces the camera
    c_ = cam_pt(-0.03 + 0.004 * wob(t, 0.8, 9.0), -0.06 + lift - 0.3 * ease_in(drop), 0.27 + 0.003 * wob(t, 0.7, 4.0))
    place_hand('L', c_, fd, pd); fingers('L', WATCH_CURL, thumb=WATCH_THUMB); return c_, fd, pd
def watch_on(c_, fd, pd, secs):
    bpy.context.view_layer.update()
    pp, d_, n_ = palm_point('L')
    up = pd.normalized(); y_ = (fd - up * fd.dot(up)).normalized(); x_ = y_.cross(up)
    q = Matrix((x_, y_, up)).transposed().to_quaternion()
    stopwatch_set(True, c_ + up * WATCH_LIFT - y_ * WATCH_SLIDE, q, secs)
def shade_hand(k):
    """right hand raised at arm's length toward the Sun, back of the hand to you, fingers spread: the light glows between them (k 0..1)"""
    kk = sm(clamp(k, 0, 1))
    lo = cam_pt(0.22, -0.5, 0.3); hi = cam_pt(-0.05, -0.035, 0.44)
    c_ = lo.lerp(hi, kk); fd = cam_dir(0.3, 0.6, 0.8).lerp(cam_dir(0.06, 1.0, 0.08), kk).normalized(); pd = cam_dir(-0.5, 0.0, 0.6).lerp(cam_dir(-0.05, 0.0, 1.0), kk).normalized()
    place_hand('R', c_, fd, pd, w_rot=1.0); fingers('R', lerp(0.35, 0.06, kk), spread=lerp(0.0, 9.0, kk), thumb=0.0)
def shot_day(t, b):
    lt = t - B[b]
    mode('yard'); dress(False); birds_set(t, True); show(CLOUDS_D, True)
    POND['ice'] = 0.0; LAKE['ice'] = 0.0; POND['front'] = 0.0; LAKE['front'] = 0.0; therm_set(72)
    MOON.hide_render = True; bloom(0.42, 1.1); S.view_settings.exposure = 0.0
    if b == 1 or (b == 2 and t < T_BO):
        yard_mode(1.0, 0.0, t); for_w(0.0)
        fpv_look(t, 9.0, -7.0, punch(lt, 24.0) if b == 1 else 24.0, 8.0, 0.33)
        fpv(); arm_down('R'); c_, fd, pd = watch_hand(t)
        k = clamp((t - SW_T0) / (SW_T1 - SW_T0), 0, 1); watch_on(c_, fd, pd, 480.0 * k)
    elif b == 2:                                                        # lights out: night in one frame, windows and the porch lamp come on, look up at the Moon
        yard_mode(0.0, 0.0, t); dt = t - T_BO; for_w(dt)
        NIGHTL.energy = 0.3 + 0.9 * (1 - smooth(T_MOON, T_MOON + 0.25, t))   # moonlight still on for a moment: a cool rim on your hand
        PORCH.data.energy = 110.0 * smooth(0.3, 0.38, dt); birds_set(t, False); show(CLOUDS_D, False)
        MOON.hide_render = False; MOON['lit'] = 0.35 * (1 - smooth(T_MOON, T_MOON + 0.25, t))
        k = smooth(T_BO + 0.25, T_BO + 0.85, t)
        fpv_look(t, lerp(9.0, -18.0, k), lerp(-7.0, 13.0, k), 24.0, 8.0, lerp(0.33, 8.0, k))
        fpv(); arm_down('R'); c_, fd, pd = watch_hand(t, drop=smooth(T_BO + 0.15, T_BO + 0.7, t))
        if k < 0.6: watch_on(c_, fd, pd, 0.0)
        S.view_settings.exposure = 0.35
    else:                                                               # shot 10: the sunshine is back; shade your eyes, look at the Sun, then dive into it
        yard_mode(1.0, 0.0, t); for_w(0.0)
        k = smooth(B[10] + 0.1, B[10] + 0.95, t); zk = smooth(END - 1.0, END - 0.45, t)
        fpv_look(t, lerp(9.0, 15.0, k), lerp(-7.0, 9.0, k), punch(lt, 24.0) * (1.0 + 5.0 * ease_in(zk)), 8.0, 0.3 + 3.0 * k, amt=1.0 - zk)
        fpv(); arm_down('L'); shade_hand(smooth(B[10] + 0.05, B[10] + 0.85, t) * (1 - smooth(END - 1.55, END - 1.05, t)))
        S.view_settings.exposure = 2.5 * ease_in(zk); bloom(0.3 + 1.2 * zk, 1.2 - 0.6 * zk)
def for_w(dt):
    for o in WINDOWS: o['lit'] = 1.0 if dt > o['on_t'] else 0.0

# ---- shot 3: Earth on its orbit, the Sun gone; it breaks off along a straight line
ORB_C = SP; ORB_R2 = 30.0; E_R3 = 2.4; W3 = 0.45; T_BRK = B[3] + 0.3498 * DUR[3]
def earth3(t):
    if t < T_BRK: a_ = W3 * (t - T_BRK); return ORB_C + Vector((ORB_R2 * math.cos(a_), ORB_R2 * math.sin(a_), 0.0))
    return ORB_C + Vector((ORB_R2, ORB_R2 * W3 * (t - T_BRK), 0.0))
def shot_orbit(t):
    mode('space'); lt = t - B[3]; sun_story(9.0); show(PROMS, False); SUN.hide_render = True; CORONA.hide_render = True; EMBER.hide_render = True; SHOCK.hide_render = True
    PLUTO.hide_render = True; bloom(0.3, 1.0); S.view_settings.exposure = 0.3
    e_ = earth3(t); EARTH.location = e_; EARTH.scale = (E_R3,) * 3; EARTH['frost'] = 0.0; EARTH['city'] = 1.0; EARTH.rotation_euler = (R(-20), R(15), 0.4 * t)
    for k, o in enumerate(DASHES):
        a_ = 2 * math.pi * k / 90; o.location = ORB_C; o.scale = (ORB_R2 / ORB_R, ORB_R2 / ORB_R, 1.0); o['a'] = 0.55
    pts = []                                                         # the trail: the last bit of orbit, then the straight run
    for i in range(40):
        tt = t - 1.6 + 1.6 * i / 39; p_ = earth3(tt); pts.append(p_ - Vector((0, 0, 0.02)))
    tr = trail_set(pts); tr['a'] = 1.0
    SPACE_FILL.location = e_ + Vector((-25, -18, 22)); SPACE_FILL.rotation_quaternion = (e_ - SPACE_FILL.location).to_track_quat('-Z', 'Y'); SPACE_FILL.data.energy = 30000
    yc = (e_ - ORB_C).y + 4.0
    cp = ORB_C + Vector((ORB_R2 - 9.0, yc - 26.0, 36.0)); ct = ORB_C + Vector((ORB_R2 - 6.0, yc + 2.0, 0.0))
    look(cp, ct, lens=punch(lt, 26.0), fstop=16.0, up=(0, 1, 0.6))

# ---- shot 4: night, the thermometer on the post drops in steps; your breath fogs
TEMPS = [(B[4], 59), (10.395, 59), (10.475, 47), (10.893, 47), (10.973, 35), (11.391, 35), (11.471, 23), (99, 23)]
def temp_at(t):
    for (t0, f0), (t1, f1) in zip(TEMPS, TEMPS[1:]):
        if t0 <= t < t1: return lerp(f0, f1, sm((t - t0) / (t1 - t0)))
    return 23
def shot_therm(t):
    lt = t - B[4]; mode('yard'); yard_mode(0.0, 0.08 * smooth(B[4] + 1.2, B[5], t), t); for_w(9.0)
    MOON.hide_render = True; POND['ice'] = 0.0; LAKE['ice'] = 0.0; therm_set(temp_at(t)); bloom(0.3, 1.2); S.view_settings.exposure = 0.45
    w_, rl = handheld(t, 0.6)
    tg = TPOST + Vector((0.01, 0.0, 0.02)); cp = EYE + Vector((0.0, 0.05, -0.05))
    d_ = (tg - cp).normalized(); side = d_.cross(Vector((0, 0, 1))).normalized()
    look(cp, tg + side * (w_.x * 0.02) + Vector((0, 0, w_.z * 0.02)), lens=punch(lt, lerp(38.0, 44.0, sm(lt / DUR[4]))), fstop=5.6, roll=R(rl))
    CAM.data.dof.focus_distance = (tg - cp).length
    breath_set(t, [B[4] + 0.12, B[4] + 1.2], 1.0)

# ---- shot 5: day 3, everything frosts over (and your sleeve); ice crystals glitter in the porch light
def check_hand(t):
    c_ = cam_pt(0.02 + 0.003 * wob(t, 0.7, 2.0), -0.045, 0.46); place_hand('L', c_, cam_dir(1.0, 0.25, 0.55), cam_dir(0.0, -1.0, 0.3)); fingers('L', 0.28, thumb=0.2)
def shot_frost(t):
    lt = t - B[5]; u = lt / DUR[5]; mode('yard'); dress(True)
    fr = lerp(0.12, 1.0, smooth(0.05, 0.85, u)); yard_mode(0.0, fr, t); for_w(9.0); MOON.hide_render = True
    POND['ice'] = 0.0; LAKE['ice'] = 0.0; therm_set(23); bloom(0.3, 1.2); S.view_settings.exposure = 0.45
    fpv_look(t, lerp(-4.0, 2.0, sm(u)), -11.0, punch(lt, 24.0), 8.0, 0.33)
    fpv(); arm_down('R'); check_hand(t)
    xtal_set(t, True); breath_set(t, [B[5] + 0.3, B[5] + 1.5], 1.0)

# ---- shot 6: the pond freezes in a blink, then the lake starts to; dive into the lake ice
P_FREEZE = (B[6] + 0.05, B[6] + 1.0)
def shot_ponds(t):
    lt = t - B[6]; u = lt / DUR[6]; mode('yard'); yard_mode(0.0, 1.0, t); for_w(9.0); MOON.hide_render = True; therm_set(5)
    pk = smooth(*P_FREEZE, t); POND['ice'] = 1.25 * pk; POND['front'] = 3.0 * (1 - smooth(0.9, 1.0, pk))
    lk = smooth(B[6] + 1.05, B[6] + 1.95, t); LAKE['ice'] = 0.04 + 0.32 * lk; LAKE['front'] = 3.0
    bloom(0.35, 1.0); S.view_settings.exposure = 0.55
    k = smooth(B[6] + 0.95, B[6] + 1.5, t); dv = smooth(END * 0 + B[7] - 0.38, B[7], t)
    pond_t = Vector((PC.x, PC.y, ground_z(PC.x, PC.y))); lake_t = Vector((2.0, 80.0, LAKE_Z))
    tg = pond_t.lerp(lake_t, sm(k)); cp = EYE + Vector((0, 0.15, 0)); w_, rl = handheld(t, 1.0 - dv)
    d_ = (tg - cp); cp = cp + d_ * (0.92 * ease_in(dv))
    look(cp, tg + Vector((w_.x * 0.06, 0, w_.z * 0.06)), lens=punch(lt, lerp(36.0, 30.0, k)) * (1 + 1.5 * ease_in(dv)), fstop=8.0, roll=R(rl))
    CAM.data.dof.focus_distance = (tg - cp).length

# ---- shot 7: the ocean under the ice, cut open: the lid of ice, the water still moving
def shot_sea(t):
    lt = t - B[7]; u = lt / DUR[7]; mode('sea'); sea_set(t); bloom(0.35, 1.0); S.view_settings.exposure = 0.0
    SEA_KEY.data.energy = 4000
    k = ease_out(lt / 0.75); dv = smooth(B[8] - 0.36, B[8], t)
    top = SS + Vector((0.4, -1.2, ICE_T + 5.5)); side = SS + Vector((3.0, -13.0, -0.8)).lerp(Vector((2.6, -12.0, -2.4)), sm(u))
    cp = top.lerp(side, k); ct = (SS + Vector((0, 0, ICE_T))).lerp(SS + Vector((0, 0, -3.0)), k)
    bot = SS + Vector((0.3, 0, -BH + 0.4)); cp = cp.lerp(bot + Vector((0, -2.0, 0.6)), ease_in(dv)); ct = ct.lerp(bot, sm(dv))
    look(cp, ct, lens=lerp(22.0, 32.0, k) * (1 + 0.8 * ease_in(dv)), fstop=11.0)

# ---- shot 8: the vent on the sea floor (tube worms, black smoke), then the microbes living off its chemicals
T_MIC = B[8] + 1.8
def shot_vent(t):
    lt = t - B[8]
    if t < T_MIC:
        mode('vent'); vent_set(t); VENT_L.data.energy = 300; VENT_FILL.data.energy = 600; bloom(0.4, 1.0); S.view_settings.exposure = 0.2
        k = ease_out(lt / 1.0)
        cp = (VS + Vector((0.6, -3.0, 8.5))).lerp(VS + Vector((1.5, -6.2, 1.7)), k) + Vector((0.4 * math.sin(lt * 0.5), 0, 0))
        ct = (VS + Vector((0, 0, 3.0))).lerp(VS + Vector((0, 0, 2.2)), k)
        look(cp, ct, lens=lerp(22.0, 26.0, k), fstop=8.0)
    else:
        mode('micro'); micro_set(t); MIC_L.data.energy = 60; MIC_KICK.data.energy = 25; bloom(0.35, 1.1); S.view_settings.exposure = 0.2
        u = (t - T_MIC) / (B[9] - T_MIC); p_, n_ = rock_pt(0.0, 0.0, 0.0)
        a_ = R(-8 + 16 * u); off = Vector((math.sin(a_) * 0.85, -math.cos(a_) * 0.85, 0.75)) * lerp(1.25, 1.0, sm(u))
        look(p_ + off, p_ + Vector((0, 0.05, 0.02)), lens=punch(t - T_MIC, 40.0), fstop=5.6, focus=p_)

# ---- shot 9: frozen Earth drifts in beside Pluto
C9 = SP + Vector((0.0, -520.0, 0.0))
def shot_pluto(t):
    lt = t - B[9]; u = lt / DUR[9]; mode('space'); sun_story(9.0); SUN.hide_render = True; CORONA.hide_render = True; EMBER.hide_render = True; SHOCK.hide_render = True
    show(DASHES, False); bloom(0.25, 1.1); S.view_settings.exposure = 0.0
    k = ease_out(lt / 2.6)
    EARTH.location = C9 + Vector((lerp(4.8, 0.75, k), 9.0, 0.95)); EARTH.scale = (1.6,) * 3; EARTH['frost'] = lerp(0.75, 1.0, smooth(0.0, 0.5, u)); EARTH['city'] = 0.0
    EARTH.rotation_euler = (R(-15), R(10), -0.6 + 0.12 * t)
    PLUTO.hide_render = False; PLUTO.location = C9 + Vector((-0.6, 4.5, -0.22)); PLUTO.rotation_euler = (R(8), 0, R(270) + 0.05 * lt)
    PLUTO_KEY.location = C9 + Vector((-7.0, 1.0, 5.0)); PLUTO_KEY.rotation_quaternion = ((C9 + Vector((0, 6, 0))) - PLUTO_KEY.location).to_track_quat('-Z', 'Y'); PLUTO_KEY.data.energy = 4500; PLUTO_KEY.data.size = 6
    SPACE_FILL.location = C9 + Vector((6, 3, -3)); SPACE_FILL.rotation_quaternion = ((C9 + Vector((0, 7, 0))) - SPACE_FILL.location).to_track_quat('-Z', 'Y'); SPACE_FILL.data.energy = 1500
    a_ = R(2.0 * math.sin(0.4 * lt))
    look(C9 + Vector((0.15 * u, 0.25 * u, 0.0)), C9 + Vector((0.12, 6.0, 0.18)), lens=punch(lt, 35.0), fstop=16.0, roll=a_)

def state(t):
    t = clamp(t, 0.0, END - 1e-4); b = beat_at(t)
    S.render.use_motion_blur = True
    if b == 0: shot_sun(t, t)
    elif b in (1, 2): shot_day(t, b)
    elif b == 3: shot_orbit(t)
    elif b == 4: shot_therm(t)
    elif b == 5: shot_frost(t)
    elif b == 6: shot_ponds(t)
    elif b == 7: shot_sea(t)
    elif b == 8: shot_vent(t)
    elif b == 9: shot_pluto(t)
    else:
        if t >= END - 0.45: shot_sun(t, t - END)
        else: shot_day(t, 10)
    bpy.context.view_layer.update()

def cut_at(t, d):
    """a camera cut sits between t - d and t + d: no blur keys across it"""
    cuts = list(B[1:]) + [T_MIC, END - 0.45]
    return any(t - d < c_ <= t + d for c_ in cuts)
def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear(); CAM.data.animation_data_clear()
    if not cut_at(t, d) and t > d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            state(tt_); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
            CAM.data.keyframe_insert('lens', frame=kf)
    S.frame_set(f); state(t)
    if CAM.animation_data:                                              # the lens and camera come from the keys; everything else is set for t
        pass
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

