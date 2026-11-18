# Pyramid stone on a sled: workers drag a 2.5-ton block across dry desert sand; a man on the sled front pours water and it slides.
# One continuous shot: dry sand piles up, water bridges between grains (macro), half the crew lets go, the tomb painting payoff. Loops.
#   python3 pyr3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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
# ================================================================ timing + the set: open desert at midday, the Great Pyramid half built far down the
# road, a limestone wall along the left of the road that carries the tomb painting (the payoff)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_PYR = B[1] + 0.1                    # rise to the pyramid
T_PILE = B[2]                         # "dry sand piles up": the camera is down at the runner
T_STUCK = word_t(2, 15)               # "gets stuck": the sled stops dead
T_CLIMB = word_t(3, 3)                # "climbs onto the front of the sled"
T_UP = T_CLIMB + 0.9                  # standing on the sled
T_POUR = word_t(4, 1)                 # "pours": water starts
T_DIVE = B[5] + 0.15                  # into the wet sand
T_IN = T_DIVE + 0.9                   # among the grains
T_OUT = B[6] - 0.05                   # back up out of the sand
T_GO = T_POUR + 1.2                   # the sled breaks loose on the wet sand
T_HALF = word_t(7, 17)                # "cut the pull in half"
T_LETGO = word_t(8, 4)                # "half as many men": the back two rows let go
T_SOAK = B[9] + 0.1                   # too much water: he dumps it
T_RIGHT = word_t(9, 10)               # "just right": back to a steady pour
T_WALL = B[10] + 0.2                  # the camera turns to the wall
T_RESET = B[10] + 2.6                 # (camera on the wall) the road goes back to frame one
T_BACK = B[12] + 0.2                  # the camera comes back to the start
print('T', round(T_STUCK, 2), round(T_CLIMB, 2), round(T_POUR, 2), round(T_GO, 2), round(T_LETGO, 2), round(T_SOAK, 2), round(T_WALL, 2), round(END, 2))

# ---------------------------------------------------------------- materials from photo sets, mapped by object coordinates (the meshes here have no UVs)
def pbr(pid, scale=1.0, name=None, coord_='Object', tint=None, rough_add=0.0, bump=1.0, boxp=False):
    d = P._dir(pid); m = bpy.data.materials.new(name or pid.split(':', 1)[-1]); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale); nt.links.new(coord(nt, coord_), mp.inputs['Vector'])
    def tex(pats, nc):
        f = P._one(d, *pats)
        if not f: return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f, check_existing=True); n.image.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
        n.projection = 'BOX' if boxp else 'FLAT'; n.projection_blend = 0.25; nt.links.new(mp.outputs[0], n.inputs['Vector']); return n
    c = tex(['*_diff_*.*', '*_Color.*', '*_col_*.*', '*diffuse*.*'], False)
    col = c.outputs['Color'] if c else None
    if col is not None and tint is not None:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        nt.links.new(col, mx.inputs['A']); mx.inputs['B'].default_value = (*tint, 1); col = mx.outputs['Result']
    if col is not None: nt.links.new(col, b.inputs['Base Color'])
    r = tex(['*_rough_*.*', '*_Roughness.*'], True)
    if r:
        if rough_add: nt.links.new(math_(nt, 'ADD', r.outputs['Color'], rough_add), b.inputs['Roughness'])
        else: nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    nmi = tex(['*_nor_gl_*.*', '*_NormalGL.*'], True)
    if nmi:
        nn = nt.nodes.new('ShaderNodeNormalMap'); nn.inputs['Strength'].default_value = bump; nt.links.new(nmi.outputs['Color'], nn.inputs['Color']); nt.links.new(nn.outputs['Normal'], b.inputs['Normal'])
    return m
def haze(m, dist=900.0, col=(0.78, 0.74, 0.66)):
    """far things fade into the bright desert air"""
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); out = nt.nodes['Material Output']
    cd = nt.nodes.new('ShaderNodeCameraData'); f = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'EXPONENT', math_(nt, 'DIVIDE', cd.outputs['View Distance'], -dist)))
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = 1.0
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(f, mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface']); return m

# ---------------------------------------------------------------- sky + sun
ENV = P.hdri('ph:goegap', 0.65, 205)
# the camera sees a clean desert sky instead of the photo (its hills are not Egypt); the photo still lights everything
try:
    wnt = S.world.node_tree; bg_ = next(n for n in wnt.nodes if n.type == 'BACKGROUND'); lp_ = wnt.nodes.new('ShaderNodeLightPath')
    gv = wnt.nodes.new('ShaderNodeTexCoord'); sz = sepz(wnt, gv.outputs['Generated'])
    hor = math_(wnt, 'POWER', math_(wnt, 'MAXIMUM', sz.outputs['Z'], 0.0), 0.45)
    sky = ramp(wnt, hor, [(0.0, (0.92, 0.86, 0.74)), (0.12, (0.62, 0.74, 0.86)), (0.55, (0.24, 0.45, 0.78)), (1.0, (0.12, 0.30, 0.66))])
    skyb = wnt.nodes.new('ShaderNodeBackground'); wnt.links.new(sky, skyb.inputs['Color']); skyb.inputs['Strength'].default_value = 1.0
    mxs = wnt.nodes.new('ShaderNodeMixShader'); wnt.links.new(lp_.outputs['Is Camera Ray'], mxs.inputs['Fac'])
    wout = next(n for n in wnt.nodes if n.type == 'OUTPUT_WORLD'); wnt.links.new(bg_.outputs[0], mxs.inputs[1]); wnt.links.new(skyb.outputs[0], mxs.inputs[2])
    wnt.links.new(mxs.outputs[0], wout.inputs['Surface'])
except Exception as e_: print('sky swap skipped', e_)
SUN = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(SUN)
SUN.data.energy = 3.4; SUN.data.color = (1.0, 0.94, 0.84); SUN.data.angle = R(1.2); SUN.rotation_euler = (R(38), R(0), R(81))

# ---------------------------------------------------------------- ground: hard-packed desert sand, with low dunes far off
SAND = pbr('ph:dense_sand', 0.45, 'sand', tint=(1.05, 0.93, 0.78), bump=0.8); haze(SAND, 1100.0)
def ground_mesh(name, size, n, height_fn, m):
    vs = []; fs = []
    for j in range(n + 1):
        for i in range(n + 1):
            x_ = -size / 2 + size * i / n; y_ = -size / 2 + size * j / n; vs.append((x_, y_, height_fn(x_, y_)))
    for j in range(n):
        for i in range(n): a_ = j * (n + 1) + i; fs.append((a_, a_ + 1, a_ + n + 2, a_ + n + 1))
    return mesh(name, vs, fs, m)
def dunes(x_, y_):
    r_ = math.hypot(x_, y_ - 20); k = smooth(60, 220, r_)
    return k * (6.0 * mnoise.noise(Vector((x_ / 140, y_ / 140, 0.3))) + 2.0 * mnoise.noise(Vector((x_ / 45, y_ / 45, 1.7))) + 4.0)
GROUND = ground_mesh('ground', 1800, 160, dunes, SAND)
NEAR = ground_mesh('near', 40, 2, lambda x_, y_: 0.0, SAND); NEAR.location = (0, 8, 0.002)        # the road itself: dead flat

# ---------------------------------------------------------------- the Great Pyramid, half built, far down the road; a long ramp up its face
LIME = pbr('ph:large_sandstone_blocks', 0.06, 'pyr', tint=(1.3, 1.1, 0.82), boxp=True); haze(LIME, 1400.0)
PYC = Vector((70, 430, 0)); PB_ = 230.0; PH_FULL = 146.0; PH_NOW = 92.0
hb = PB_ / 2; ht = hb * (1 - PH_NOW / PH_FULL)
pv = [(-hb, -hb, 0), (hb, -hb, 0), (hb, hb, 0), (-hb, hb, 0), (-ht, -ht, PH_NOW), (ht, -ht, PH_NOW), (ht, ht, PH_NOW), (-ht, ht, PH_NOW)]
PYR = mesh('pyramid', pv, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], LIME, smooth_=False, loc=PYC)
# stepped courses on the faces (a few big ledges read as stone layers from this far)
for k in range(1, 9):
    z_ = PH_NOW * k / 9; hk = hb * (1 - z_ / PH_FULL) + 0.6
    box(f'course{k}', (hk * 2, hk * 2, 0.9), (PYC.x, PYC.y, z_), LIME)
RAMP = mesh('ramp', [(-14, -hb - 150, 0), (14, -hb - 150, 0), (14, -hb + 30, PH_NOW * 0.9), (-14, -hb + 30, PH_NOW * 0.9), (-14, -hb + 30, 0), (14, -hb + 30, 0)],
            [(0, 1, 2, 3), (1, 5, 2), (0, 3, 4), (3, 2, 5, 4)], LIME, smooth_=False, loc=PYC + Vector((-30, 0, 0)))
# a second, finished pyramid off to the side (scale and age)
pv2 = [(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0), (0, 0, 76)]
mesh('pyr2', pv2, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], LIME, smooth_=False, loc=(-260, 640, 0))

# ---------------------------------------------------------------- the wall on the left of the road, and the tomb painting on it
WALLX = -5.6; WALL_Y0, WALL_Y1 = -6.0, 22.0; WALL_H = 3.4
WALLM = pbr('ph:plaster_stone_wall_01', 0.4, 'wallm', 'Object', tint=(1.08, 0.98, 0.82), boxp=True)
WALL = box('wall', (1.2, WALL_Y1 - WALL_Y0, WALL_H), (WALLX - 0.6, (WALL_Y0 + WALL_Y1) / 2, WALL_H / 2), WALLM, bv=0.04)
box('wallcap', (1.4, WALL_Y1 - WALL_Y0 + 0.2, 0.18), (WALLX - 0.6, (WALL_Y0 + WALL_Y1) / 2, WALL_H + 0.09), WALLM, bv=0.03)
PAINT_W, PAINT_H = 6.6, 6.6 * 1600 / 4096; PAINT_C = Vector((WALLX + 0.004, 11.0, 0.35 + PAINT_H / 2))
pm = bpy.data.materials.new('painting'); pm.use_nodes = True; nt = pm.node_tree; b = nt.nodes['Principled BSDF']
it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(os.path.join(HERE, 'painting.png')); it.interpolation = 'Cubic'
nt.links.new(coord(nt, 'UV'), it.inputs['Vector']); nt.links.new(it.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.88
wn = tnoise(nt, coord(nt, 'Object'), 26.0, 8.0); bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.18; nt.links.new(wn, bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
_pv = [(0, -PAINT_W / 2, -PAINT_H / 2), (0, PAINT_W / 2, -PAINT_H / 2), (0, PAINT_W / 2, PAINT_H / 2), (0, -PAINT_W / 2, PAINT_H / 2)]
PAINT = mesh('paintplane', _pv, [(0, 1, 2, 3)], pm, smooth_=False, loc=PAINT_C)
_uv = PAINT.data.uv_layers.new(name='UV')
for li, (u_, v_) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): _uv.data[li].uv = (u_, v_)
def paint_pt(u_, v_):
    """a point on the painting from its picture coords (0..1 left to right, 0..1 top to bottom), 3 cm out from the wall"""
    return PAINT_C + Vector((0.03, (u_ - 0.5) * PAINT_W, (0.5 - v_) * PAINT_H))
# a few loose stones and a basket by the wall, scattered rubble on the road edge
ROCKM = pbr('ph:rock_surface', 1.2, 'rockm', tint=(1.1, 0.98, 0.8), boxp=True)
for k in range(26):
    x_ = -3.2 - 2.0 * h1(k) if k % 2 else 2.6 + 3.0 * h1(k + 9); y_ = -4 + 26 * h1(k + 3)
    s_ = 0.08 + 0.25 * h1(k + 7) ** 2
    o = prim('ico_sphere', f'rub{k}', ROCKM, loc=(x_, y_, s_ * 0.3), scale=(s_ * (1 + h1(k)), s_, s_ * 0.6), subdivisions=2); o.rotation_euler = (0, 0, h1(k + 1) * 6)
# ================================================================ the stone and its sled: a 2.5-ton limestone block (1.0 x 1.2 x 0.85 m, about a cubic
# metre) lashed onto a wooden sled with two runners curling up at the front, a plank deck ahead of the stone for the water man
WOOD = pbr('ph:rough_wood', 1.6, 'wood', 'Object', tint=(0.95, 0.80, 0.62), boxp=True)
STONEM = pbr('ph:rock_surface', 0.9, 'stone', 'Object', tint=(1.22, 1.12, 0.94), boxp=True, bump=0.7)
ROPEM = pbr('acg:Rope001', 9.0, 'rope', 'Object', tint=(1.0, 0.86, 0.62), boxp=True)
SLED = empty('sled')
RUN_X = 0.40; RUN_W = 0.12; RUN_H = 0.15; DECK_TOP = 0.28
def sweep_rect(name, path, w, h, x0, m, parent):
    """a beam of w (x) by h (normal to the path), swept along a (y, z) path; the path is the beam's bottom edge"""
    vs = []; fs = []; n = len(path)
    for i, (y_, z_) in enumerate(path):
        a_ = path[max(i - 1, 0)]; b_ = path[min(i + 1, n - 1)]; ty, tz = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(ty, tz); ny, nz = -tz / L_, ty / L_
        for dx, k in ((-w / 2, 0), (w / 2, 0), (w / 2, 1), (-w / 2, 1)): vs.append((x0 + dx, y_ + ny * h * k, z_ + nz * h * k))
    for i in range(n - 1):
        for k in range(4): k2 = (k + 1) % 4; fs.append((i * 4 + k, i * 4 + k2, (i + 1) * 4 + k2, (i + 1) * 4 + k))
    fs.append((0, 3, 2, 1)); fs.append(tuple((n - 1) * 4 + k for k in range(4)))
    return mesh(name, vs, fs, m, parent, smooth_=False)
RUN_PATH = [(-1.25, 0.0), (0.6, 0.0)] + [(0.6 + 0.42 * math.sin(R(90 * k / 8)), 0.40 * (1 - math.cos(R(90 * k / 8)))) for k in range(1, 9)]
RUNNERS = [sweep_rect(f'runner{s_}', RUN_PATH, RUN_W, RUN_H, s_ * RUN_X, WOOD, SLED) for s_ in (-1, 1)]
for o in RUNNERS: bevel(o, 0.012, 2)
for k, y_ in enumerate((-1.05, -0.62, -0.18, 0.26)):
    box(f'cross{k}', (RUN_X * 2 + 0.28, 0.13, 0.12), (0, y_, RUN_H + 0.06), WOOD, bv=0.01, parent=SLED)
for k in range(5):
    box(f'plank{k}', (RUN_X * 2 + 0.22, 0.105, 0.045), (0, 0.42 + k * 0.112, DECK_TOP - 0.02), WOOD, bv=0.008, parent=SLED)
box('frontbar', (RUN_X * 2 + 0.34, 0.11, 0.11), (0, 0.98, 0.30), WOOD, bv=0.012, parent=SLED)   # the ropes tie on here
for s_ in (-1, 1): box(f'peg{s_}', (0.05, 0.05, 0.22), (s_ * (RUN_X + 0.06), 0.98, 0.36), WOOD, bv=0.01, parent=SLED)
BLK_C = Vector((0, -0.42, DECK_TOP + 0.425)); BLK_S = (1.0, 1.2, 0.85)
BLOCK = box('block', BLK_S, BLK_C, STONEM, bv=0.035, parent=SLED)
# chisel marks: a little bump noise on the stone
try:
    nt = STONEM.node_tree; b_ = nt.nodes['Principled BSDF']; bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35
    nt.links.new(tnoise(nt, coord(nt, 'Object'), 9.0, 4.0), bp.inputs['Height'])
    nn = next((l.from_node for l in nt.links if l.to_socket == b_.inputs['Normal']), None)
    if nn: nt.links.new(nn.outputs['Normal'], bp.inputs['Normal'])
    nt.links.new(bp.outputs['Normal'], b_.inputs['Normal'])
except Exception as e_: print('stone bump skipped', e_)
# lashings: two rope bands round the stone and the cross beams
def band(name, y_, parent):
    hx, hz = BLK_S[0] / 2 + 0.015, BLK_S[2] / 2 + 0.015; z0 = BLK_C.z; pts = []
    for k in range(41):
        a_ = 2 * math.pi * k / 40; c_, s_ = math.cos(a_), math.sin(a_)
        r_ = 1.0 / max(abs(c_) / hx, abs(s_) / (hz + 0.12 * (s_ < 0))) ; pts.append((r_ * c_ * 0.995, y_, z0 + r_ * s_))
    return tube(name, pts, 0.016, ROPEM, parent, seg=8, caps=False)
for k, y_ in enumerate((-0.82, -0.02)): band(f'lash{k}', y_, SLED)
# a rope tube we can move every frame (same vertex count, new points)
class Rope:
    def __init__(self, name, n=24, r=0.017, seg=8):
        self.n, self.seg, self.r = n, seg, r
        self.o = tube(name, [(0, i * 0.1, 0) for i in range(n)], r, ROPEM, seg=seg, caps=True)
    def set(self, pts):
        pts = [Vector(p) for p in pts]; n, seg = self.n, self.seg
        # resample the polyline to n evenly spaced points
        L_ = [0.0]
        for i in range(1, len(pts)): L_.append(L_[-1] + (pts[i] - pts[i - 1]).length)
        tot = L_[-1] or 1.0; rs = []; j = 0
        for i in range(n):
            s_ = tot * i / (n - 1)
            while j < len(pts) - 2 and L_[j + 1] < s_: j += 1
            k = (s_ - L_[j]) / max(L_[j + 1] - L_[j], 1e-6); rs.append(pts[j].lerp(pts[j + 1], min(max(k, 0), 1)))
        T0 = (rs[1] - rs[0]).normalized(); up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized(); co = []
        for i in range(n):
            T = (rs[min(i + 1, n - 1)] - rs[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
            for k in range(seg): co.extend(rs[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * self.r)
        self.o.data.vertices.foreach_set('co', co); self.o.data.update()
def sag(a_, b_, droop, n=10):
    a_, b_ = Vector(a_), Vector(b_); return [a_.lerp(b_, i / (n - 1)) - Vector((0, 0, droop * 4 * (i / (n - 1)) * (1 - i / (n - 1)))) for i in range(n)]
# the water jar: a round clay jar with a short neck and two lug handles
CLAY = mat('clay', (0.42, 0.17, 0.08), 0.8); noisy(CLAY, 30.0, 0.2, 0.1)
try:   # two dark painted bands round the jar's shoulder
    nt = CLAY.node_tree; b_ = nt.nodes['Principled BSDF']; zz = sepz(nt, coord(nt, 'Object')).outputs['Z']
    bd = math_(nt, 'MAXIMUM', math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', zz, 0.075)), 0.012), math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', zz, 0.105)), 0.007))
    lk = next(l for l in nt.links if l.to_socket == b_.inputs['Base Color']); nt.links.new(mixc(nt, bd, lk.from_socket, (0.05, 0.03, 0.02)), b_.inputs['Base Color'])
except Exception as e_: print('jar bands skipped', e_)
JAR = lathe('jar', [(0.0, -0.19), (0.09, -0.185), (0.16, -0.12), (0.18, -0.02), (0.165, 0.07), (0.11, 0.14), (0.065, 0.17), (0.06, 0.21), (0.075, 0.225), (0.06, 0.23), (0.05, 0.20), (0.04, 0.0)], 32, CLAY)
for s_ in (-1, 1):
    tube(f'jarlug{s_}', [(s_ * 0.15, 0, 0.08), (s_ * 0.2, 0, 0.06), (s_ * 0.2, 0, 0.0), (s_ * 0.17, 0, -0.03)], 0.016, CLAY, JAR, seg=8)
JAR_MOUTH = Vector((0, 0, 0.23))              # in the jar's own space
WATERM = mat('water', (0.8, 0.9, 1.0), 0.03, trans=1.0, ior=1.33)
# ================================================================ the crew: the house MakeHuman man (man.blend), loaded once per worker. Bare chest,
# a white linen kilt (cut from his trousers), bare feet, sun-browned skin, black hair. IK hands with a fist on the rope or the jar.
_BVG_KEYS = ('foot', 'toe')
def _retint_skin(m, col):
    """the MakeHuman skin is a node group: push its colour mix-in toward a sun-browned tone"""
    g = next((n for n in m.node_tree.nodes if n.type == 'GROUP'), None)
    if g is None: return
    g.inputs['colorMixIn'].default_value = (*col, 1); g.inputs['colorMixInStrength'].default_value = 0.95
    g.inputs['Roughness'].default_value = 0.5
LINEN = mat('linen', (0.62, 0.58, 0.48), 0.95, sheen=0.4); noisy(LINEN, 220.0, 0.08, 0.04)
BELT = mat('belt', (0.50, 0.44, 0.34), 0.9, sheen=0.3)
def make_kilt(name, rig, col):
    # rings: (z, rx, ry) in the rig's rest space (he faces -y); pleats as small ripples round the hem
    rings = [(1.000, 0.150, 0.118), (0.960, 0.162, 0.128), (0.900, 0.188, 0.150), (0.840, 0.205, 0.165), (0.760, 0.222, 0.185), (0.680, 0.238, 0.205), (0.620, 0.248, 0.215)]
    seg = 48; vs = []; fs = []; cy = 0.012
    for i, (z_, rx, ry) in enumerate(rings):
        u = i / (len(rings) - 1)
        for k in range(seg):
            a_ = 2 * math.pi * k / seg; pl = 1.0 + 0.035 * u * math.sin(a_ * 14)
            vs.append((rx * pl * math.cos(a_), cy + ry * pl * math.sin(a_), z_ + (0.03 * u if math.sin(a_) < -0.3 else 0.0) * max(0, -math.sin(a_))))
    for i in range(len(rings) - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = rig; o.matrix_parent_inverse.identity(); o.data.materials.append(LINEN)
    gr = o.vertex_groups.new(name='root'); gl = o.vertex_groups.new(name='upperleg01.L'); gR = o.vertex_groups.new(name='upperleg01.R')
    for i, v in enumerate(me.vertices):
        u = clamp((1.0 - v.co.z) / 0.38, 0, 1); x_ = v.co.x; leg = 0.45 * u * u * min(1.0, abs(x_) / 0.12)
        gr.add([i], 1.0 - leg, 'REPLACE')
        (gl if x_ > 0 else gR).add([i], leg, 'REPLACE')
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.008; sol.offset = 1.0
    bt = tube(name + '_belt', [(0.152 * math.cos(2 * math.pi * k / 40), 0.012 + 0.120 * math.sin(2 * math.pi * k / 40), 0.985) for k in range(41)], 0.016, BELT, seg=8, caps=False)
    bt.parent = rig; bt.matrix_parent_inverse.identity(); col.objects.link(bt); S.collection.objects.unlink(bt)
    gb = bt.vertex_groups.new(name='root'); gb.add(list(range(len(bt.data.vertices))), 1.0, 'REPLACE'); mb = bt.modifiers.new('arm', 'ARMATURE'); mb.object = rig
    return o
HAIRM = mat('hairblack', (0.018, 0.014, 0.012), 0.55, sheen=0.3)
class Man:
    def __init__(self, name, skin=(0.55, 0.36, 0.24), loc=(0, 0, 0), yaw=math.pi):
        with bpy.data.libraries.load(asset('man.blend'), link=False) as (_s, _d):
            _d.objects = [n for n in _s.objects if n.startswith('Human')]
        self.col = bpy.data.collections.new(name); S.collection.children.link(self.col)
        for o in _d.objects: self.col.objects.link(o)
        objs = list(_d.objects)
        self.rig = next(o for o in objs if o.type == 'ARMATURE')
        self.body = next(o for o in objs if o.type == 'MESH' and any(m_.type == 'MASK' and m_.name.startswith('Delete') for m_ in o.modifiers))
        suit = next(o for o in objs if 'casualsuit' in o.name); hair = next((o for o in objs if 'short02' in o.name), None)
        self.PB = self.rig.pose.bones
        # body: show the chest (the trousers' delete mask off), hide the groin under the kilt for good, brown the skin
        for m_ in self.body.modifiers:
            if m_.type == 'MASK' and m_.name.startswith('Delete'): m_.show_render = m_.show_viewport = False
        gi = [i for i, m_ in enumerate(self.body.data.materials) if m_ and 'genital' in m_.name]
        hg = self.body.vertex_groups.new(name='hide_groin')
        hv = set()
        for p_ in self.body.data.polygons:
            if p_.material_index in gi: hv.update(p_.vertices)
        if hv: hg.add(list(hv), 1.0, 'REPLACE')
        mk = self.body.modifiers.new('hide_groin', 'MASK'); mk.vertex_group = 'hide_groin'; mk.invert_vertex_group = True; self.body.modifiers.move(len(self.body.modifiers) - 1, 0)
        for m_ in self.body.data.materials:
            if m_ and ('body' in m_.name or 'ears' in m_.name or 'lips' in m_.name or 'nipple' in m_.name): _retint_skin(m_, skin)
        # kilt (shendyt): a flared linen wrap from the waist to above the knee, skinned to the hips with a little pull from each thigh
        suit.hide_render = True; suit.hide_viewport = True
        self.kilt = make_kilt(name + '_kilt', self.rig, self.col)
        if hair:
            hair.data.materials.clear(); hair.data.materials.append(HAIRM)
        for o in self.col.objects:
            for md in o.modifiers:
                if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
        self.root = empty(name + '_root', loc=loc); self.root.rotation_euler = (0, 0, yaw)
        self.rig.parent = self.root; self.rig.location = (0, 0, 0); self.rig.rotation_euler = (0, 0, 0)
        # IK arms and hand rotation
        self.tg = {k: empty(f'{name}_{k}') for k in ('hR', 'hL', 'pR', 'pL', 'rotR', 'rotL')}
        self.ikc = {}
        for s_ in ('R', 'L'):
            c = self.PB['wrist.' + s_].constraints.new('IK'); c.target = self.tg['h' + s_]; c.pole_target = self.tg['p' + s_]; c.chain_count = 5; c.pole_angle = R(-90); c.use_tail = True
            self.ikc[s_] = c
        self.hand = {}
        for s_ in ('R', 'L'):
            b = self.rig.data.bones
            d_ = (b['finger3-1.' + s_].head_local - b['wrist.' + s_].head_local).normalized()
            n_ = b['finger3-1.' + s_].matrix_local.to_3x3().col[2]; n_ = (n_ - d_ * n_.dot(d_)).normalized(); a_ = d_.cross(n_)
            Hr = Matrix((a_, d_, n_)).transposed(); Wr = b['wrist.' + s_].matrix_local.to_3x3(); self.tg['rot' + s_].rotation_mode = 'QUATERNION'
            c = self.PB['wrist.' + s_].constraints.new('COPY_ROTATION'); c.target = self.tg['rot' + s_]; c.owner_space = c.target_space = 'WORLD'
            self.hand[s_] = (Hr.transposed() @ Wr, c)
    def world(self, p): return self.root.matrix_world @ Vector(p)
    def fwd(self): return (self.root.matrix_world.to_3x3().normalized() @ Vector((0, -1, 0))).normalized()
    def right(self): return (self.root.matrix_world.to_3x3().normalized() @ Vector((-1, 0, 0))).normalized()
    def orient(self, s_, d_, n_, w=1.0):
        """hand frame: d = where the straight fingers point, n = out of the palm (toward what it holds)"""
        O, con = self.hand[s_]; con.influence = w; d_ = Vector(d_).normalized(); n_ = (Vector(n_) - d_ * Vector(n_).dot(d_)).normalized(); a_ = d_.cross(n_)
        self.tg['rot' + s_].rotation_quaternion = (Matrix((a_, d_, n_)).transposed() @ O).to_quaternion()
    def fingers(self, s_, w, thumb=1.0):
        for f_ in range(1, 6):
            for g in (1, 2, 3):
                nm = f'finger{f_}-{g}.{s_}'
                if nm not in self.PB: continue
                held = (14, 20, 12)[g - 1] if f_ == 1 else (55, 75, 50)[g - 1]; loose = (6, 8, 5)[g - 1] if f_ == 1 else (12, 16, 10)[g - 1]
                pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(lerp(loose, held, w * (thumb if f_ == 1 else 1.0))), 0, 0)
    def pose(self, spine=0.0, neck=0.0, head=0.0, head_yaw=0.0, legs=None, twist=0.0):
        for n, k in (('spine03', 0.3), ('spine02', 0.3), ('spine01', 0.4)):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(spine * k), R(twist * k), 0)
        for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(neck * k), R(head_yaw * k * 0.5), 0)
        pb = self.PB['head']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(head), R(head_yaw * 0.5), 0)
        for nm in ('upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'foot.L', 'foot.R'):
            pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (legs or {}).get(nm, (0, 0, 0))
    def bone(self, nm, tail=False):
        pb = self.PB[nm]; return self.rig.matrix_world @ (pb.tail if tail else pb.head)
    def knuckles(self, s_):
        ps = [self.bone(k + '.' + s_) for k in ('finger2-1', 'finger3-1', 'finger4-1', 'finger5-1') if k + '.' + s_ in self.PB]
        return sum(ps, Vector()) / len(ps)
    def palm(self, s_):
        return (self.bone('wrist.' + s_) + self.knuckles(s_)) / 2
def walk_legs(ph, amp, bend=1.0, plant=0.0):
    """a stride: ph is the leg phase (radians), amp the swing in degrees; plant > 0 braces both legs (straining, stuck)"""
    out = {}
    for s_, off in (('L', 0.0), ('R', math.pi)):
        sw = math.sin(ph + off); lift = max(0.0, math.cos(ph + off))
        up = -amp * sw - plant * (14 if s_ == 'L' else -10)
        knee = (8 + 40 * lift * bend) * (1 - 0.3 * plant) + plant * (18 if s_ == 'L' else 4)
        out['upperleg01.' + s_] = (R(up), 0, 0); out['lowerleg01.' + s_] = (R(knee), 0, 0); out['foot.' + s_] = (R(-0.4 * up - 0.3 * knee + 10 * lift), 0, 0)
    return out
# ---------------------------------------------------------------- eight haulers in a V ahead of the sled (four rows of two), each on his own rope over
# the inner shoulder; the water man beside the sled, who climbs onto its front deck with the jar
TIE = {1: Vector((0.46, 0.98, 0.42)), -1: Vector((-0.46, 0.98, 0.42))}
HAUL = []
for k in range(4):
    for s_ in (1, -1):
        tone = (0.36 + 0.06 * h1(k * 2 + s_), 0.20 + 0.04 * h1(k * 3 + s_), 0.12 + 0.03 * h1(k + s_))
        m_ = Man(f'haul{k}{"r" if s_ > 0 else "l"}', tone)
        m_.row, m_.side = k, s_; m_.off = Vector((s_ * (0.50 + 0.46 * k), 2.35 + 1.05 * k, 0.0))
        m_.rope = Rope(f'rope{k}{s_}', 30, 0.016); m_.seed = k * 2.3 + s_ * 1.1; HAUL.append(m_)
WATERMAN = Man('waterman', (0.34, 0.19, 0.11))
# ================================================================ effects: the sand pile in front of the runners, the wet strip the water leaves,
# the puddle when he dumps too much, the water stream and its splashes, and the grain-scale set (water bridges between grains)
# ---- the pile of dry sand the runners shove ahead of them: one mound per runner, joined by a low ridge
BERM_M = SAND
def mound(name, w, l, n=14):
    vs = []; fs = []
    for j in range(n + 1):
        for i in range(n + 1):
            u = -1 + 2 * i / n; v = -1 + 2 * j / n; r_ = min(1.0, math.hypot(u, v)); hgt = (1 - r_ * r_) ** 1.4 * (1.0 + 0.25 * mnoise.noise(Vector((u * 2.3, v * 2.3, 0.7))))
            vs.append((u * w / 2, v * l / 2 + 0.25 * l * (1 - r_) * (v > 0), max(hgt, 0.0)))
    for j in range(n):
        for i in range(n): a_ = j * (n + 1) + i; fs.append((a_, a_ + 1, a_ + n + 2, a_ + n + 1))
    return mesh(name, vs, fs, BERM_M)
BERMS = []
for s_ in (-1, 1):
    o = mound(f'berm{s_}', 0.42, 0.46); o.parent = SLED; o.location = (s_ * RUN_X, 0.83, -0.004); BERMS.append(o)
RIDGE = mound('ridge', 1.15, 0.30); RIDGE.parent = SLED; RIDGE.location = (0, 0.86, -0.004)
# grains rolling off the pile while they strain (little clumps that tumble down its sides)
GRAINS = []
for k in range(26):
    g = prim('ico_sphere', f'grain{k}', SAND, scale=(1, 1, 0.8), radius=0.012 + 0.012 * h1(k), subdivisions=1); g.parent = SLED; GRAINS.append(g)

# ---- wet sand, painted straight into the road's own sand (a strip behind the pour, the fresh spot, the soaked patch), driven by
# numbers on the road object: wy0..wy1 strip, (sy, sr) spot, (ky, kr) soak
ROADM = pbr('ph:dense_sand', 0.45, 'road', tint=(1.05, 0.93, 0.78), bump=0.8)
def _road_wet(m):
    nt = m.node_tree; b_ = nt.nodes['Principled BSDF']
    lk = next(l for l in nt.links if l.to_socket == b_.inputs['Base Color']); base = lk.from_socket
    rk = next(l for l in nt.links if l.to_socket == b_.inputs['Roughness']); rough = rk.from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry'); ps = sepz(nt, geo.outputs['Position']); X, Y = ps.outputs['X'], ps.outputs['Y']
    nz = tnoise(nt, geo.outputs['Position'], 2.2, 3.0); nz2 = math_(nt, 'SUBTRACT', nz, 0.5)
    def band(v, lo, hi, soft):           # 1 inside [lo, hi] with soft edges
        a1 = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', v, lo), soft), 0.0), 1.0)
        a2 = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', hi, v), soft), 0.0), 1.0)
        return math_(nt, 'MULTIPLY', a1, a2)
    ax = math_(nt, 'ADD', math_(nt, 'ABSOLUTE', X), math_(nt, 'MULTIPLY', nz2, 0.16))
    strip = math_(nt, 'MULTIPLY', band(ax, -1.0, 0.60, 0.07), band(math_(nt, 'ADD', Y, math_(nt, 'MULTIPLY', nz2, 0.12)), objattr(nt, 'wy0'), objattr(nt, 'wy1'), 0.08))
    def disc(cy, rr, sy_):
        dx = math_(nt, 'MULTIPLY', X, 0.8); dy = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', Y, cy), sy_)
        d_ = math_(nt, 'ADD', math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dy, dy))), math_(nt, 'MULTIPLY', nz2, 0.14))
        return math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', rr, d_), 0.06), 0.0), 1.0)
    spot = disc(objattr(nt, 'sy'), objattr(nt, 'sr'), 1.15); soak = disc(objattr(nt, 'ky'), objattr(nt, 'kr'), 0.85)
    wet = math_(nt, 'MAXIMUM', strip, spot); m['wetnode'] = wet.node.name; m['stripnode'] = strip.node.name; m['spotnode'] = spot.node.name
    # darken by scaling the colour (a plain multiply: base * (1 - 0.78 wet) * (1 - 0.6 soak)), a touch warmer in the wet
    def mr(v, o1):
        n_ = nt.nodes.new('ShaderNodeMapRange'); n_.inputs['From Min'].default_value = 0.0; n_.inputs['From Max'].default_value = 1.0
        n_.inputs['To Min'].default_value = 1.0; n_.inputs['To Max'].default_value = o1; nt.links.new(v, n_.inputs['Value']); return n_.outputs['Result']
    k_ = math_(nt, 'MULTIPLY', mr(wet, 0.30), mr(soak, 0.55))
    vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'SCALE'; nt.links.new(base, vm.inputs[0]); nt.links.new(k_, vm.inputs['Scale'])
    c2 = vm.outputs['Vector']
    nt.links.new(c2, b_.inputs['Base Color'])
    r1 = math_(nt, 'ADD', math_(nt, 'MULTIPLY', rough, math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MAXIMUM', wet, soak))), math_(nt, 'ADD', math_(nt, 'MULTIPLY', wet, 0.92), math_(nt, 'MULTIPLY', soak, 0.0)))
    try: nt.links.new(math_(nt, 'MULTIPLY', mr(math_(nt, 'MAXIMUM', wet, soak), 0.3), 0.5), b_.inputs['Specular IOR Level'])
    except Exception as e_: print('spec skipped', e_)
    nt.links.new(r1, b_.inputs['Roughness'])
    return m
_road_wet(ROADM)
NEAR.data.materials[0] = ROADM
for k_, v_ in (('wy0', 0.0), ('wy1', -1.0), ('sy', 0.0), ('sr', -1.0), ('ky', 0.0), ('kr', -1.0)): NEAR[k_] = v_
POOLM = mat('pool', (0.07, 0.05, 0.03), 0.06, coat=0.6)
POOL = lathe('pool', [(0.0, 0.010), (0.6, 0.010), (0.85, 0.008), (0.95, 0.004), (1.0, 0.0)], 40, POOLM)
# ---- the stream from the jar and the splash where it lands
class Stream:
    def __init__(self, n=22):
        self.n = n; self.seg = 10; self.o = tube('stream', [(0, 0, -i * 0.05) for i in range(n)], 0.02, WATERM, seg=10, caps=True)
    def set(self, p0, v0, r0, t, wob_amt=1.0):
        g = Vector((0, 0, -9.8)); pts = []; tau = 0.0
        tz = (v0.z + math.sqrt(max(v0.z ** 2 - 2 * g.z * (p0.z - 0.0), 0))) / -g.z
        for i in range(self.n):
            tau = tz * i / (self.n - 1); p = p0 + v0 * tau + 0.5 * g * tau * tau
            p += Vector((wob(t - tau, 9, i * 0.1), wob(t - tau, 9, 3 + i * 0.1), 0)) * 0.006 * wob_amt * (i / self.n)
            pts.append(p)
        co = []; T0 = (pts[1] - pts[0]).normalized(); up = Vector((1, 0, 0)); Nn = T0.cross(up).normalized()
        for i, p in enumerate(pts):
            T = (pts[min(i + 1, self.n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
            rr = r0 * (1.0 - 0.45 * i / (self.n - 1)) * (1 + 0.15 * wob(t * 3 - i * 0.2, 7, i))
            for k in range(self.seg): co.extend(p + (Nn * math.cos(2 * math.pi * k / self.seg) + Bn * math.sin(2 * math.pi * k / self.seg)) * rr)
        self.o.data.vertices.foreach_set('co', co); self.o.data.update(); return pts[-1]
STREAM = Stream()
DROPS = [prim('uv_sphere', f'drop{k}', WATERM, radius=0.007 + 0.006 * h1(k + 40), segments=10, ring_count=6) for k in range(18)]
for d_ in DROPS: d_.scale = (1, 1, 1.25)
SPLASH = lathe('splash', [(0.0, 0.0), (0.03, 0.003), (0.05, 0.012), (0.06, 0.022), (0.064, 0.02), (0.056, 0.008), (0.04, 0.002)], 28, WATERM)

# ---- grain scale: a bed of sand grains (rounded, chipped quartz) floating high above the desert, with water bridges that grow
# between touching grains; the camera dives into the wet sand and comes out here, then flies back up
MICRO = Vector((40, -60, 400)); GR = 0.06          # 1 grain ~ 0.12 m across here (real grains are ~0.25 mm)
QUARTZ = mat('quartz', (0.55, 0.36, 0.18), 0.32, coat=0.3); noisy(QUARTZ, 18.0, 0.3, 0.15)
QUARTZ2 = mat('quartz2', (0.42, 0.27, 0.14), 0.38, coat=0.2); noisy(QUARTZ2, 22.0, 0.3, 0.15)
BRIDGEM = mat('bridge', (0.30, 0.62, 1.0), 0.03, trans=0.45, ior=1.33, coat=0.8, emit=(0.25, 0.55, 1.0), estr=0.6)
rng = random.Random(5); GRS = []
bed = prim('plane', 'microbed', mat('microbedm', (0.12, 0.08, 0.05), 0.9), loc=MICRO + Vector((0, 0, -GR * 1.2)), size=40.0)
for k in range(1400):
    for _ in range(30):
        p = MICRO + Vector((rng.uniform(-0.95, 0.95), rng.uniform(-0.95, 0.95), 0)); r_ = GR * rng.uniform(0.7, 1.3)
        p.z += rng.uniform(-1.0, 1.4) * GR
        if all((p - q).length > (r_ + rq) * 0.93 for q, rq in GRS[-400:]): break
    else: continue
    GRS.append((p, r_))
    if len(GRS) >= 650: break
for k, (p, r_) in enumerate(GRS):
    o = prim('ico_sphere', f'g{k}', QUARTZ if k % 3 else QUARTZ2, loc=p, scale=(r_ * rng.uniform(0.85, 1.2), r_ * rng.uniform(0.8, 1.1), r_ * rng.uniform(0.7, 1.0)), subdivisions=3)
    o.rotation_euler = (rng.uniform(0, 6), rng.uniform(0, 6), rng.uniform(0, 6))
    for v in o.data.vertices: v.co *= 1.0 + 0.10 * mnoise.noise(v.co * (2.2 / r_) + Vector((k, 0, 0)))
    for pp in o.data.polygons: pp.use_smooth = True
# water bridges: a pinched neck between every close pair near the middle of the bed
BRIDGES = []
def neck(name, a_, ra, b_, rb):
    ax = (b_ - a_); L_ = ax.length; d_ = ax / L_; seg = 18; rings = 9; vs = []; fs = []
    up = Vector((0, 0, 1)) if abs(d_.z) < 0.9 else Vector((1, 0, 0)); n1 = d_.cross(up).normalized(); n2 = d_.cross(n1)
    s0 = ra * 0.55; s1 = L_ - rb * 0.55
    for i in range(rings):
        u = i / (rings - 1); s_ = lerp(s0, s1, u); rr = min(ra, rb) * (0.74 - 0.26 * math.sin(math.pi * u))
        for k in range(seg): a2 = 2 * math.pi * k / seg; vs.append(a_ + d_ * s_ + (n1 * math.cos(a2) + n2 * math.sin(a2)) * rr)
    for i in range(rings - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    o = mesh(name, [tuple(v - a_) for v in vs], fs, BRIDGEM, loc=a_); return o
for i, (p, r_) in enumerate(GRS):
    if (p - MICRO).length > 0.9: continue
    for j in range(i + 1, len(GRS)):
        q, rq = GRS[j]
        if (p - q).length < (r_ + rq) * 1.12 and len(BRIDGES) < 320:
            o = neck(f'br{i}_{j}', p, r_, q, rq); o['d'] = (p - MICRO).length; BRIDGES.append(o)
print('grains', len(GRS), 'bridges', len(BRIDGES))

# ================================================================ the story, frame by frame
DT = 1.0 / FPS
def speed(t):
    """sled speed (m/s) along +y.  t < 0 is the run-up into the loop (same crawl as frame one)"""
    if t < T_STUCK:
        crawl = 0.16 * (0.35 + 0.65 * max(0.0, math.sin(2 * math.pi * t / 1.7 + 0.6)) ** 2)
        return crawl * (1 - smooth(T_STUCK - 1.4, T_STUCK, t))
    if t < T_GO: return 0.0
    v = 0.55 * smooth(T_GO, T_GO + 1.6, t)
    v *= 1 - 0.75 * smooth(T_SOAK + 0.3, T_SOAK + 1.0, t) * (1 - smooth(T_RIGHT, T_RIGHT + 1.0, t))
    return v
_SY = [0.0]
for i in range(int(TOTAL * FPS) + 3): _SY.append(_SY[-1] + speed(i * DT) * DT)
def local_t(t): return t - END if t >= T_RESET else t
def sled_y(t):
    tl = local_t(t)
    if tl < 0: return 0.0 + tl * 0.11                        # the crawl before frame one (average speed of the opening)
    i = tl * FPS; i0 = int(i); k = i - i0; return lerp(_SY[min(i0, len(_SY) - 1)], _SY[min(i0 + 1, len(_SY) - 1)], k)
def rel(t, p): return Vector((p[0], sled_y(t) + p[1], p[2]))
def dist_walked(t): return sled_y(t)

def state(t):
    tl = local_t(t); st = {}
    st['tl'] = tl
    st['v'] = speed(tl) if tl >= 0 else 0.11
    st['dry'] = 1.0 - smooth(T_GO - 0.4, T_GO + 0.8, tl) if tl >= 0 else 1.0
    st['stuck'] = (smooth(T_STUCK - 1.0, T_STUCK, tl) * (1 - smooth(T_GO - 0.3, T_GO + 0.6, tl))) if tl >= 0 else 0.0
    st['berm'] = (0.45 + 0.55 * smooth(0, T_STUCK, tl)) * (1 - smooth(T_GO, T_GO + 1.3, tl)) if tl >= 0 else 0.45 + 0.08 * tl
    st['climb'] = smooth(T_CLIMB, T_UP, tl) if tl >= 0 else 0.0
    st['pour'] = smooth(T_POUR - 0.3, T_POUR + 0.4, tl) if tl >= 0 else 0.0
    st['soak'] = (smooth(T_SOAK, T_SOAK + 0.5, tl) * (1 - smooth(T_RIGHT - 0.2, T_RIGHT + 0.5, tl))) if tl >= 0 else 0.0
    st['letgo'] = smooth(T_LETGO - 0.2, T_LETGO + 0.6, tl) if tl >= 0 else 0.0
    st['bog'] = (smooth(T_SOAK + 0.4, T_SOAK + 1.2, tl) * (1 - smooth(T_RIGHT, T_RIGHT + 1.0, tl))) if tl >= 0 else 0.0
    return st

def hauler(m_, t, st):
    sy = sled_y(t); k = m_.row; s_ = m_.side
    let = st['letgo'] if k >= 2 else 0.0
    # where he stands: on his rope's length ahead of the sled; after letting go he stops, steps out to the side and watches
    tl = st['tl']; ty = T_LETGO - 0.2
    if let > 0 and tl >= ty:
        y_ = sled_y(ty) + m_.off.y + 0.25 * smooth(ty, ty + 0.8, tl); x_ = m_.off.x + s_ * 0.75 * smooth(ty + 0.2, ty + 1.4, tl)
    else: y_ = sy + m_.off.y; x_ = m_.off.x
    m_.root.location = (x_, y_, 0.0)
    strain = st['stuck']; dry = st['dry']
    lean = (26 + 14 * strain + 3 * wob(t, 1.3, m_.seed)) * (1 - let) + 2 * let
    body = (9 + 7 * strain) * (1 - let)
    m_.root.rotation_euler = (R(body), 0, math.pi + s_ * R(8) * (1 - let) - s_ * R(35) * smooth(T_LETGO + 0.6, T_LETGO + 1.6, tl) * (k >= 2))
    walked = (dist_walked(t) if not (let > 0 and tl >= ty) else dist_walked(ty) + 0.25 * smooth(ty, ty + 0.8, tl))
    ph = walked * 2 * math.pi / 1.25 + m_.seed
    amp = 24 * clamp(st['v'] / 0.25, 0.25, 1.0) * (1 - strain) * (1 - 0.8 * smooth(ty + 1.0, ty + 1.6, tl) * (k >= 2))
    legs = walk_legs(ph, amp, 1.0, strain)
    m_.pose(spine=lean, neck=-lean * 0.45, head=-lean * 0.35 + 4 * strain, head_yaw=-s_ * 30 * smooth(T_LETGO + 0.8, T_LETGO + 1.8, tl) * (k >= 2), legs=legs)
    bpy.context.view_layer.update()
    inner = 'L' if s_ > 0 else 'R'; outer = 'R' if s_ > 0 else 'L'
    sh = m_.bone('shoulder01.' + inner); fw = m_.fwd(); rt = m_.right(); up = Vector((0, 0, 1)); inw = -rt if s_ > 0 else rt
    sh_top = sh + up * 0.07 - fw * 0.01 + inw * 0.01
    h1_ = sh + fw * 0.13 - up * 0.05 + inw * 0.01; h2_ = sh + fw * 0.19 - up * 0.24 + inw * 0.03
    rest_ = {'R': m_.world((-0.28, -0.05, 0.85)), 'L': m_.world((0.28, -0.05, 0.85))}
    for s2, hp in ((inner, h1_), (outer, h2_)):
        m_.tg['h' + s2].location = hp.lerp(rest_[s2], let)
        m_.tg['p' + s2].location = m_.world((0.7 if s2 == 'L' else -0.7, 0.35, 0.9))
        m_.orient(s2, rt if s2 == 'L' else -rt, -fw, 1.0 - let)
        m_.fingers(s2, 1.0 - 0.85 * let)
    bpy.context.view_layer.update()
    tie = rel(t, TIE[s_]) + Vector((0, 0, 0.02 * k))
    if let < 0.5:
        p1 = m_.palm(inner); p2 = m_.palm(outer)
        pts = sag(tie, sh_top - fw * 0.06, 0.02 + 0.06 * (1 - strain) * (1 - dry * 0.5), 12)
        pts += [sh_top + fw * 0.06, p1, p2, p2 + (p2 - p1).normalized() * 0.08 - up * 0.22]
    else:     # dropped: the rope lies on the sand, dragged along by the sled
        far = tie + Vector((s_ * 0.5, 2.6 + 0.4 * k, 0)); far.z = 0.02
        pts = [tie, tie + Vector((s_ * 0.06, 0.25, -0.3)), tie.lerp(far, 0.4) + Vector((0, 0, -tie.z + 0.02)), far]
    m_.rope.set(pts)

def waterman(t, st):
    m_ = WATERMAN; tl = st['tl']; c = st['climb']; up = Vector((0, 0, 1))
    beside = rel(t, (-1.05, 0.25, 0.0)); deck = rel(t, (0.12, 0.70, DECK_TOP + 0.005))
    hop = math.sin(math.pi * c) * 0.18
    m_.root.location = beside.lerp(deck, sm(c)) + up * hop - Vector((0, 0, 0.03 * st['bog']))
    m_.root.rotation_euler = (0, 0, math.pi - R(25) * (1 - c))
    pour = st['pour']; soak = st['soak']
    lift = math.sin(math.pi * clamp((tl - T_CLIMB) / (T_UP - T_CLIMB), 0, 1)) if tl >= 0 else 0.0
    legs = {'upperleg01.R': (R(-55 * lift), 0, 0), 'lowerleg01.R': (R(80 * lift), 0, 0), 'upperleg01.L': (R(-8 * lift), 0, 0)}
    m_.pose(spine=6 + 14 * pour + 8 * soak, neck=-4 - 4 * pour, head=4 + 10 * pour, legs=legs)
    bpy.context.view_layer.update()
    fw = m_.fwd()
    # the jar: held at the belly, then out in front and tipped forward
    tilt = R(78) * pour + R(34) * soak + R(4) * wob(t, 1.1, 3) * pour
    jc = m_.world((0, -0.36 - 0.12 * pour, 1.16 - 0.08 * pour - 0.04 * soak))
    JAR.location = jc; JAR.rotation_euler = (-tilt, 0, 0)
    bpy.context.view_layer.update()
    Mj = JAR.matrix_world
    for s_, sx in (('R', 1), ('L', -1)):
        lug = Mj @ Vector((sx * 0.205, 0, 0.03)); ctr = Mj @ Vector((0, 0, 0.03))
        m_.tg['h' + s_].location = lug + (lug - ctr).normalized() * 0.035
        m_.tg['p' + s_].location = m_.world((0.7 if s_ == 'L' else -0.7, 0.35, 0.9))
        m_.orient(s_, -(Mj.to_3x3() @ Vector((0, 0, 1))), ctr - lug, 1.0)
        m_.fingers(s_, 0.85)
    bpy.context.view_layer.update()
    return Mj

def fx(t, st, Mj):
    sy = sled_y(t); tl = st['tl']
    SLED.location = (0, sy, -0.03 * st['bog'])
    b = st['berm']
    for o in BERMS: o.scale = (1.0, 1.0 + 0.3 * b, max(b, 0.0) * 0.13 + 1e-4); o.hide_render = b < 0.02
    RIDGE.scale = (1.0, 1.0, max(b, 0.0) * 0.07 + 1e-4); RIDGE.hide_render = b < 0.02
    # grains tumbling off the piles while it inches along or they strain
    act = st['dry'] * (0.4 + 0.6 * clamp(st['v'] / 0.12 + st['stuck'], 0, 1)) * (b > 0.05)
    for k, g in enumerate(GRAINS):
        per = 0.9 + 0.5 * h1(k); u = ((t + h1(k + 3) * per) % per) / per; s_ = -1 if k % 2 else 1; side = 1 if (k // 2) % 2 else -1
        p = Vector((s_ * RUN_X + side * (0.06 + 0.14 * u), 0.98 + 0.08 * u + 0.05 * h1(k + 9), b * 0.13 * (1 - u) ** 1.5 + 0.01))
        g.location = p; g.rotation_euler = (u * 9, u * 7, 0); g.hide_render = act < 0.3 or u > 0.95
    # wet sand (painted into the road): strip behind the pour, the fresh spot, the soak
    pour = st['pour']
    started = tl >= T_POUR - 0.3 and tl >= 0
    y_hit = sy + 1.50
    if started:
        y0 = sled_y(T_POUR) + 1.50; sp = smooth(T_POUR + 0.1, T_POUR + 1.0, tl)
        NEAR['wy0'] = y0 - 0.15; NEAR['wy1'] = y_hit + 0.35 if y_hit - y0 > 0.1 else y0 - 1.0
        NEAR['sy'] = y_hit + 0.02; NEAR['sr'] = 0.14 + 0.60 * sp
    else: NEAR['wy0'], NEAR['wy1'], NEAR['sr'] = 0.0, -1.0, -1.0
    if tl >= T_SOAK and tl >= 0:
        ys = sled_y(T_SOAK + 0.5) + 1.55; g_ = smooth(T_SOAK + 0.1, T_SOAK + 1.4, tl)
        NEAR['ky'] = ys; NEAR['kr'] = 0.05 + 0.62 * g_
        POOL.hide_render = g_ < 0.02; POOL.location = (0.0, ys, 0.002); POOL.scale = (0.42 * g_ + 0.01, 0.55 * g_ + 0.01, 1.0 + 0.6 * st['soak'])
    else: NEAR['kr'] = -1.0; POOL.hide_render = True
    # the stream
    flow = pour * (1.0 + 1.3 * st['soak'])
    on = flow > 0.05 and tl >= 0
    STREAM.o.hide_render = not on; SPLASH.hide_render = True
    if on:
        mouth = Mj @ JAR_MOUTH; lip = (Mj.to_3x3() @ Vector((0, 0, 1))).normalized()
        v0 = lip * (0.35 + 0.45 * st['soak']) + Vector((0, st['v'], 0))
        hit = STREAM.set(mouth + lip * 0.01, v0, 0.015 + 0.014 * flow, t, 1.0)
        SPLASH.location = (hit.x, hit.y, 0.0); SPLASH.scale = (0.9 + 0.8 * st['soak'],) * 2 + (0.8 + 0.5 * wob(t, 8, 1) * 0.3 + 0.6 * st['soak'],)
        for k, d_ in enumerate(DROPS):
            per = 0.35 + 0.25 * h1(k); u = ((t + h1(k + 1) * per) % per) / per; a_ = 2 * math.pi * h1(k + 7)
            sp_ = (0.35 + 0.5 * h1(k + 11)) * (1 + st['soak']); up_ = 1.2 + 0.8 * h1(k + 13)
            tt = u * per
            d_.location = hit + Vector((math.cos(a_) * sp_ * tt, math.sin(a_) * sp_ * tt, max(up_ * tt - 4.9 * tt * tt, 0.0) + 0.006))
            d_.hide_render = u > 0.92 or h1(k + 20) > 0.55 + 0.45 * flow
    else:
        for d_ in DROPS: d_.hide_render = True
    # grain-scale bridges grow from the middle out while he says it
    gb = smooth(T_IN - 0.3, B[5] + DUR[5] - 0.6, t)
    for o in BRIDGES:
        k = clamp(gb * 2.0 - o['d'] / 0.9, 0.0, 1.0); o.hide_render = k < 0.02 or not (T_DIVE < t < T_OUT + 0.6); o.scale = (k, k, k) if k > 0 else (1e-3,) * 3

# ---- camera: keys of (time, pos, target, lens). A 'rel' tuple rides along with the sled; a Vector is a fixed spot in the world.
PYR_AIM = PYC + Vector((0, 0, 42))
def P_(t, p): return rel(t, p) if isinstance(p, tuple) else Vector(p)
HOLD = lambda t0, t1, p, q, lens: [(t0, p, q, lens), (t1, p, q, lens)]
pp = lambda u_, v_: paint_pt(u_, v_)
K = [
    (0.0, (1.15, 7.3, 1.25), (0.05, 2.1, 0.95), 30),
    (T_PYR - 0.3, (0.95, 7.0, 1.20), (0.05, 2.2, 0.95), 30),
    (T_PYR + 0.55, (1.9, 4.6, 3.6), (0.0, 1.2, 0.6), 28),             # up and over the crew
    (T_PYR + 1.6, (-1.6, -3.4, 3.6), (0.4, 20.0, 0.4), 26),           # up behind the stone: the crew, the road, the pyramid
    (B[2] - 0.6, (-1.5, -3.1, 3.5), (0.4, 20.0, 0.5), 27),
    (B[2] + 0.9, (0.98, 1.95, 0.30), (0.38, 0.86, 0.06), 30),          # down at the runner: the pile building, stuck
    (B[3] - 0.25, (0.92, 1.88, 0.27), (0.38, 0.86, 0.05), 30),
    (B[3] + 0.9, (2.05, 2.35, 1.15), (0.25, 0.70, 0.95), 30),          # he climbs onto the front deck
    (B[4] - 0.2, (1.95, 2.25, 1.05), (0.20, 0.85, 0.80), 30),
    (B[4] + 0.6, (2.3, 2.65, 1.55), (0.10, 0.95, 0.85), 28),          # the pour hits the sand, the dark spot spreads
    (T_DIVE, (1.9, 2.30, 1.10), (0.05, 1.30, 0.25), 28),
    (T_DIVE + 0.75, (0.10, 1.50, 0.07), (0.05, 1.47, 0.0), 30),        # down into the wet sand
]
MK = [   # grain scale (world spots at the micro set)
    (T_DIVE + 0.75, MICRO + Vector((0.20, -0.25, 1.9)), MICRO + Vector((0.1, -0.05, 0.0)), 30),
    (T_IN + 0.6, MICRO + Vector((0.36, -0.66, 0.34)), MICRO + Vector((0.02, 0.02, 0.03)), 30),
    (T_OUT - 0.5, MICRO + Vector((0.28, -0.52, 0.28)), MICRO + Vector((0.0, 0.05, 0.03)), 30),
    (T_OUT, MICRO + Vector((0.30, -0.45, 1.6)), MICRO + Vector((0.0, 0.1, 0.0)), 30),
]
K2 = [
    (T_OUT, (0.0, 2.75, 0.22), (0.05, 1.10, 0.30), 30),                 # back up out of the sand, the sled sliding at us over it
    (B[6] + 1.6, (2.7, 1.2, 1.05), (0.0, 0.8, 0.45), 30),
    (B[7] - 0.3, (2.9, 1.5, 1.15), (0.0, 1.0, 0.50), 30),
    (B[7] + 1.0, (3.7, 3.2, 1.8), (0.0, 2.3, 0.70), 28),                # wide side: pull halved
    (B[8] - 0.2, (3.6, 3.6, 1.9), (0.0, 2.5, 0.70), 28),
    (B[8] + 0.6, (4.4, 10.2, 3.1), (0.0, 3.0, 0.60), 28),               # from the front: the back rows let go
    (B[9] - 0.2, (4.3, 10.0, 3.0), (0.0, 3.0, 0.60), 28),
    (B[9] + 0.8, (2.0, 2.7, 1.25), (0.10, 1.20, 0.40), 28),             # too much: the puddle
    (B[10] - 0.1, (1.9, 2.6, 1.20), (0.10, 1.25, 0.40), 28),
]
def wall_keys():
    return [
        (T_WALL + 1.5, pp(0.70, 0.45) + Vector((3.4, 0.0, 0.1)), pp(0.66, 0.47), 25),   # the wall: rows of men hauling
        (T_WALL + 3.0, pp(0.60, 0.45) + Vector((3.3, 0.0, 0.1)), pp(0.56, 0.47), 25),
        (B[11] - 0.3, pp(0.26, 0.40) + Vector((3.5, 0.0, 0.0)), pp(0.25, 0.42), 25),    # the giant statue
        (B[11] + 1.0, pp(0.37, 0.70) + Vector((1.15, 0.0, 0.0)), pp(0.365, 0.72), 30),   # the man on the front, pouring
        (B[12] - 0.1, pp(0.37, 0.71) + Vector((1.05, 0.0, 0.0)), pp(0.365, 0.73), 30),
    ]
def interp(keys, t, sy_t):
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0.0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0.0
    else:
        i = max(j for j in range(len(keys)) if keys[j][0] <= t); k0, k1 = keys[i], keys[i + 1]; u = sm((t - k0[0]) / (k1[0] - k0[0]))
    def ev(p):
        if isinstance(p, tuple) and len(p) == 2 and p[0] == 'aim': return Vector(p[1])
        return P_(t, p)
    c0, c1 = ev(k0[1]), ev(k1[1]); a0, a1 = ev(k0[2]), ev(k1[2])
    # aim at far things by direction (so a target 400 m away blends cleanly with one 1 m away)
    d0 = (a0 - c0).normalized(); d1 = (a1 - c1).normalized(); cp = c0.lerp(c1, u); dr = d0.slerp(d1, u) if d0.dot(d1) > -0.99 else d1
    fl = lerp((a0 - c0).length if (a0 - c0).length < 60 else 6.0, (a1 - c1).length if (a1 - c1).length < 60 else 6.0, u)
    return cp, cp + dr * fl, lerp(k0[3], k1[3], u)
def camera(t):
    if t < T_DIVE + 0.75: return interp(K, t, None)
    if t < T_OUT: return interp(MK, t, None)
    if t < T_WALL: return interp(K2, t, None)
    last = K2[-1]; wk = [(T_WALL, rel(t, last[1]), rel(t, last[2]), last[3])] + wall_keys()
    if t < B[12] - 0.1: return interp(wk, t, None)
    # back to frame one: swing round from the wall to the opening view (the road was reset while we looked at the wall)
    cp0, ct0, l0 = interp(wk, B[12] - 0.1, None); st_ = (END - 0.0)
    cp1, ct1, l1 = interp(K, 0.0, None) if False else (rel(t, K[0][1]), rel(t, K[0][2]), K[0][3])
    u = sm(clamp((t - (B[12] - 0.1)) / (END - (B[12] - 0.1)), 0, 1)); u = sm(u)
    mid = cp0.lerp(cp1, u) + Vector((0.6, 0, 0.8)) * math.sin(math.pi * u)
    d0 = (ct0 - cp0).normalized(); d1 = (ct1 - cp1).normalized()
    return mid, mid + d0.slerp(d1, u) * lerp((ct0 - cp0).length, (ct1 - cp1).length, u), lerp(l0, l1, u)

def frame(f):
    t = f / FPS; S.frame_set(f); st = state(t)
    for m_ in HAUL: hauler(m_, t, st)
    Mj = waterman(t, st)
    fx(t, st, Mj)
    cp, ct, lens = camera(t)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = rel(t, q_[0:3]), rel(t, q_[3:6]), q_[6]
    cp = cp + shake(t, 0.006 * st['stuck'] * (t < T_DIVE), 2.0, 6.0)
    look(cp, ct, lens, 16.0)
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

