# Roman self-healing concrete: a crack splits a wall of the Pantheon in the rain; inside, lime lumps turn the rainwater into crystals that seal it.
# One continuous shot: the crack, the lime lumps up close, quicklime steaming in the mixing pit, crystals sealing the crack, the two test blocks, the Pantheon. Loops.
#   python3 rome3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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
# ================================================================ timing + the set: a paved square in Rome in the rain, the Pantheon (rotunda, stepped dome,
# portico), a mixing trough with quicklime, a test bench with two concrete blocks, town blocks and hills far off
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_CRACK = 0.05                        # the crack shoots across the wall (frame one)
T_DIVE1 = B[2] + 0.15                 # into the crack ("full of little white lumps")
T_IN1 = T_DIVE1 + 0.75                # inside: the cut face of the concrete
T_OUT1 = B[4] - 0.25                  # into a white lump ...
T_PIT = T_OUT1 + 0.35                 # ... and out of the quicklime heap in the trough
T_POUR = word_t(4, 4)                 # "quicklime": he tips the bucket
T_STEAM = T_POUR + 0.35
T_DIVE2 = B[5] + 0.05                 # "watch the crack": back to the wall, into the crack
T_IN2 = T_DIVE2 + 0.8
T_WATER = B[6] - 0.1                  # rainwater fills the crack
T_CRYS = B[7]                         # crystals grow across it
T_SEAL = B[8] - 0.35                  # sealed
T_OUT2 = B[8] + 0.05                  # out through the crack of the left test block
T_BENCH = T_OUT2 + 0.7
T_HEAL0 = B[8] + 1.6; T_HEAL1 = word_t(8, 18)   # left block's crack whitens; "the water stopped"
T_REV = B[10] + 0.1                   # rise to the Pantheon
T_RESET = B[11] + 1.0                 # (camera far up) the square goes back to frame one
T_BACK = B[12] + 0.2
print('T', round(T_POUR, 2), round(T_HEAL1, 2), round(T_REV, 2), round(END, 2))
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

def ground_mesh(name, size, n, height_fn, m):
    vs = []; fs = []
    for j in range(n + 1):
        for i in range(n + 1):
            x_ = -size / 2 + size * i / n; y_ = -size / 2 + size * j / n; vs.append((x_, y_, height_fn(x_, y_)))
    for j in range(n):
        for i in range(n): a_ = j * (n + 1) + i; fs.append((a_, a_ + 1, a_ + n + 2, a_ + n + 1))
    return mesh(name, vs, fs, m)

# ---------------------------------------------------------------- sky: soft grey rain light
P.hdri('ph:kloofendal_overcast', 1.0, 40)
try:   # the camera sees a plain grey rain sky (the photo's lake and hills are not Rome); the photo still lights everything
    wnt = S.world.node_tree; bg_ = next(n for n in wnt.nodes if n.type == 'BACKGROUND'); lp_ = wnt.nodes.new('ShaderNodeLightPath')
    gv = wnt.nodes.new('ShaderNodeTexCoord'); sz = sepz(wnt, gv.outputs['Generated'])
    hor = math_(wnt, 'POWER', math_(wnt, 'MAXIMUM', sz.outputs['Z'], 0.0), 0.5)
    sky = ramp(wnt, hor, [(0.0, (0.62, 0.64, 0.66)), (0.35, (0.50, 0.53, 0.57)), (1.0, (0.36, 0.39, 0.44))])
    skyb = wnt.nodes.new('ShaderNodeBackground'); wnt.links.new(sky, skyb.inputs['Color']); skyb.inputs['Strength'].default_value = 1.0
    mxs = wnt.nodes.new('ShaderNodeMixShader'); wnt.links.new(lp_.outputs['Is Camera Ray'], mxs.inputs['Fac'])
    wout = next(n for n in wnt.nodes if n.type == 'OUTPUT_WORLD'); wnt.links.new(bg_.outputs[0], mxs.inputs[1]); wnt.links.new(skyb.outputs[0], mxs.inputs[2])
    wnt.links.new(mxs.outputs[0], wout.inputs['Surface'])
except Exception as e_: print('sky swap skipped', e_)
SUNL = bpy.data.objects.new('sunl', bpy.data.lights.new('sunl', 'SUN')); S.collection.objects.link(SUNL)
SUNL.data.energy = 0.6; SUNL.data.color = (0.9, 0.93, 1.0); SUNL.data.angle = R(20); SUNL.rotation_euler = (R(50), 0, R(210))
try:
    S.world.mist_settings.start = 30; S.world.mist_settings.depth = 400
except Exception: pass

# ---------------------------------------------------------------- the square: wet stone paving, dark and shiny in the rain
PAVE = pbr('acg:PavingStones054', 0.32, 'pave', tint=(0.78, 0.74, 0.68), rough_add=-0.35, bump=0.8); haze(PAVE, 700.0, (0.62, 0.64, 0.66))
GROUND = ground_mesh('ground', 1400, 120, lambda x_, y_: smooth(160, 600, math.hypot(x_, y_ - 40)) * 22 * (0.5 + 0.5 * mnoise.noise(Vector((x_ / 300, y_ / 300, 0.4)))), PAVE)

# ---------------------------------------------------------------- the Pantheon: brick-faced concrete rotunda, stepped dome with the oculus, granite portico
PC = Vector((0, 40.0, 0)); RO = 28.0; DH = 22.0
BRICK = pbr('ph:brick_wall_005', 0.42, 'brick', 'Object', tint=(1.0, 0.86, 0.74), rough_add=-0.15, boxp=True); haze(BRICK, 900.0, (0.62, 0.64, 0.66))
CONC = pbr('acg:Concrete048', 0.25, 'dome', 'Object', tint=(0.92, 0.9, 0.86), boxp=True); haze(CONC, 900.0, (0.62, 0.64, 0.66))
TRAV = pbr('acg:Travertine009', 0.6, 'trav', 'Object', tint=(1.0, 0.97, 0.9), boxp=True); haze(TRAV, 900.0, (0.62, 0.64, 0.66))
def ring_wall(name, r_out, r_in, z0, z1, m, seg=180):
    vs = []; fs = []
    for k in range(seg):
        a_ = 2 * math.pi * k / seg
        for r_, z_ in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)): vs.append((PC.x + r_ * math.cos(a_), PC.y + r_ * math.sin(a_), z_))
    for k in range(seg):
        k2 = (k + 1) % seg
        for j in range(4): j2 = (j + 1) % 4; fs.append((k * 4 + j, k2 * 4 + j, k2 * 4 + j2, k * 4 + j2))
    return mesh(name, vs, fs, m, smooth_=True)
DRUM = ring_wall('drum', RO, RO - 6.0, 0.0, DH, BRICK)
for k, (z_, h_) in enumerate(((7.4, 0.5), (14.6, 0.6), (DH - 0.6, 0.8))):        # cornices
    ring_wall(f'cornice{k}', RO + 0.35, RO - 1.0, z_, z_ + h_, TRAV)
# dome: the outer shell steps up in rings, then a smooth cap round the open oculus
prof = []
for k in range(7): r_ = RO - 1.2 - 1.7 * k; prof += [(r_, DH + 1.15 * k), (r_, DH + 1.15 * (k + 1))]
for k in range(1, 13):
    u = k / 12; a_ = R(32 + 52 * u); prof.append((4.6 + (RO - 13.2 - 4.6) * (1 - u) ** 1.3, DH + 8.05 + 7.0 * math.sin(R(90 * u))))
prof.append((4.6, DH + 15.2)); prof.append((4.25, DH + 15.0)); prof.append((4.25, DH + 13.0))
DOME = lathe('dome', [(r_, z_) for r_, z_ in prof], 120, CONC, loc=PC)
CAP = lathe('domecap', [(RO - 0.1, DH), (RO - 1.2, DH), (RO - 1.2, DH + 0.1)], 120, TRAV, loc=PC)
DARK = mat('inside', (0.02, 0.02, 0.02), 0.9)
prim('cylinder', 'oculus_dark', DARK, loc=PC + Vector((0, 0, DH + 12.4)), radius=4.3, depth=0.2, vertices=48)
# portico on the west side (-x): a block, 8 columns across the front and 2 more rows, a gabled roof
PX0 = PC.x - RO + 1.0
box('porch_block', (10.0, 34.0, DH - 3.0), (PX0 - 3.0, PC.y, (DH - 3.0) / 2), BRICK, bv=0.05)
GRAN = mat('granite', (0.42, 0.38, 0.36), 0.45, coat=0.2); noisy(GRAN, 30.0, 0.25, 0.1)
for row, xx in enumerate((PX0 - 22.0, PX0 - 17.0, PX0 - 12.0)):
    for k in range(8):
        if row > 0 and k not in (0, 1, 2, 5, 6, 7): continue
        y_ = PC.y - 15.4 + 4.4 * k
        prim('cylinder', f'col{row}_{k}', GRAN, loc=(xx, y_, 0.6 + 5.9), radius=0.75, depth=11.8, vertices=32)
        box(f'cap{row}_{k}', (1.9, 1.9, 0.7), (xx, y_, 12.75), TRAV, bv=0.05); box(f'base{row}_{k}', (1.8, 1.8, 0.6), (xx, y_, 0.3), TRAV, bv=0.05)
box('entab', (17.0, 34.0, 2.4), (PX0 - 13.5, PC.y, 14.3), TRAV, bv=0.05)
mesh('pediment', [(PX0 - 22.6, PC.y - 17.2, 15.5), (PX0 - 22.6, PC.y + 17.2, 15.5), (PX0 - 22.6, PC.y, 21.3), (PX0 - 5.0, PC.y - 17.2, 15.5), (PX0 - 5.0, PC.y + 17.2, 15.5), (PX0 - 5.0, PC.y, 21.3)],
     [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (0, 2, 5, 3), (1, 4, 5, 2)], TRAV, smooth_=False)
mesh('roof', [(PX0 - 23.2, PC.y - 17.8, 15.4), (PX0 - 23.2, PC.y + 17.8, 15.4), (PX0 - 23.2, PC.y, 21.7), (PX0 - 4.0, PC.y - 17.8, 15.4), (PX0 - 4.0, PC.y + 17.8, 15.4), (PX0 - 4.0, PC.y, 21.7)],
     [(0, 2, 5, 3), (1, 4, 5, 2)], mat('rooflead', (0.34, 0.33, 0.32), 0.55, metal=0.4), smooth_=False)
box('steps', (6.0, 36.0, 0.6), (PX0 - 25.0, PC.y, 0.3), TRAV, bv=0.04)
# the town round the square: plain blocks with tiled roofs, and hills
STUC = mat('stucco', (0.68, 0.55, 0.42), 0.85); noisy(STUC, 3.0, 0.2, 0.1); haze(STUC, 600.0, (0.62, 0.64, 0.66))
TILE = mat('tiles', (0.52, 0.24, 0.14), 0.7); noisy(TILE, 6.0, 0.2, 0.1); haze(TILE, 600.0, (0.62, 0.64, 0.66))
rng_ = random.Random(3)
for k in range(46):
    a_ = rng_.uniform(0, 2 * math.pi); r_ = rng_.uniform(62, 200); cx, cy = PC.x + r_ * math.cos(a_), PC.y + r_ * math.sin(a_)
    if cx < PC.x - 40 and abs(cy - PC.y) < 40: continue                     # keep the front of the portico open
    w_, d_, h_ = rng_.uniform(10, 26), rng_.uniform(10, 26), rng_.uniform(8, 18)
    b_ = box(f'house{k}', (w_, d_, h_), (cx, cy, h_ / 2), STUC); b_.rotation_euler.z = a_
    r2 = mesh(f'hroof{k}', [(-w_ / 2 - 0.5, -d_ / 2 - 0.5, h_), (w_ / 2 + 0.5, -d_ / 2 - 0.5, h_), (w_ / 2 + 0.5, d_ / 2 + 0.5, h_), (-w_ / 2 - 0.5, d_ / 2 + 0.5, h_), (0, -d_ / 2 - 0.5, h_ + 3), (0, d_ / 2 + 0.5, h_ + 3)],
              [(0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4)], TILE, smooth_=False, loc=(cx, cy, 0)); r2.rotation_euler.z = a_

# ---------------------------------------------------------------- the crack spot: on the drum facing the camera's start, 1 to 1.7 m up
CRACK_A = -math.pi / 2                                       # the point of the drum nearest the square (y = PC.y - RO)
def wall_pt(u_, v_, out=0.0):
    """u along the wall (m, +x), v height (m); on the curved drum face"""
    a_ = CRACK_A + u_ / RO; r_ = RO + out; return Vector((PC.x + r_ * math.cos(a_), PC.y + r_ * math.sin(a_), v_))
WALL_N = Vector((0, -1, 0))

# ---------------------------------------------------------------- the mixing trough (right of the crack, out from the wall) and the test bench (left)
WOOD = pbr('ph:wood_planks', 1.2, 'wood', 'Object', tint=(0.85, 0.72, 0.58), boxp=True)
TR_C = Vector((2.3, PC.y - RO - 1.9, 0.0))
TROUGH = empty('trough', loc=TR_C)
for nm_, sz, lc in (('tb', (1.6, 0.9, 0.06), (0, 0, 0.12)), ('tf', (1.6, 0.06, 0.38), (0, -0.45, 0.3)), ('tk', (1.6, 0.06, 0.38), (0, 0.45, 0.3)),
                    ('tl', (0.06, 0.9, 0.38), (-0.8, 0, 0.3)), ('tr', (0.06, 0.9, 0.38), (0.8, 0, 0.3))):
    box(nm_, sz, lc, WOOD, bv=0.01, parent=TROUGH)
for sx in (-0.7, 0.7):
    for sy in (-0.38, 0.38): box(f'tleg{sx}{sy}', (0.08, 0.08, 0.12), (sx, sy, 0.06), WOOD, parent=TROUGH)
LIMEW = mat('quicklime', (0.86, 0.85, 0.80), 0.92); noisy(LIMEW, 14.0, 0.25, 0.05)
HEAP = prim('ico_sphere', 'heap', LIMEW, parent=TROUGH, loc=(0.1, 0.0, 0.16), scale=(0.62, 0.36, 0.2), subdivisions=4)
for v in HEAP.data.vertices: v.co *= 1.0 + 0.18 * mnoise.noise(v.co * 4.0) + 0.06 * mnoise.noise(v.co * 15.0)
for k in range(30):
    prim('ico_sphere', f'limelump{k}', LIMEW, parent=TROUGH, loc=(-0.6 + 1.25 * h1(k), -0.32 + 0.64 * h1(k + 5), 0.17 + 0.05 * h1(k + 9)), scale=(1, 0.9, 0.7), radius=0.025 + 0.03 * h1(k + 2), subdivisions=1)
LIMEWATER = mat('limewater', (0.72, 0.74, 0.70), 0.08, trans=0.3, ior=1.33)
POOLT = box('tpool', (1.48, 0.82, 0.02), (0, 0, 0.15), LIMEWATER, parent=TROUGH)
HOE = tube('hoe', [(0.0, 0.0, 0.0), (0.0, 0.0, 1.5)], 0.018, WOOD); box('hoeblade', (0.24, 0.02, 0.16), (0, 0, 0), mat('iron', (0.2, 0.19, 0.18), 0.5, metal=0.8), parent=HOE)
HOE.location = TR_C + Vector((-1.05, 0.3, 0.0)); HOE.rotation_euler = (R(-12), R(14), 0)
# test bench
BENCH_C = Vector((-2.5, PC.y - RO - 1.6, 0.0))
BENCH = empty('bench', loc=BENCH_C)
box('btop', (1.5, 0.7, 0.07), (0, 0, 0.82), WOOD, bv=0.01, parent=BENCH)
for sx in (-0.65, 0.65):
    for sy in (-0.28, 0.28): box(f'bleg{sx}{sy}', (0.07, 0.07, 0.8), (sx, sy, 0.4), WOOD, parent=BENCH)
# ================================================================ the crack in the wall (a dark slit that shoots across the brick face), the two test
# blocks on the bench (each split by a crack, water fed from a clay funnel, dripping out the bottom into a bowl), the worker's bucket
class Ribbon:
    """a flat strip of fixed vertex count; set() takes centre points, widths and a normal and rebuilds it"""
    def __init__(self, name, n, m, parent=None):
        self.n = n; vs = [(i * 0.01, 0, 0) for i in range(n)] + [(i * 0.01, 0, 0.001) for i in range(n)]
        fs = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        self.o = mesh(name, vs, fs, m, parent, smooth_=False)
    def set(self, pts, ws, nrm):
        n = self.n; co_l = []; co_r = []
        for i in range(n):
            a_ = pts[max(i - 1, 0)]; b_ = pts[min(i + 1, n - 1)]; tg = (b_ - a_); tg = tg.normalized() if tg.length > 1e-9 else Vector((1, 0, 0))
            side = nrm.cross(tg).normalized() * ws[i] * 0.5
            co_l.extend(pts[i] - side); co_r.extend(pts[i] + side)
        self.o.data.vertices.foreach_set('co', co_l + co_r); self.o.data.update()
def jag(p0, p1, n, amp, seed, branch_amp=0.0):
    """a jagged crack path from p0 to p1 (2D tuples), n points"""
    rr = random.Random(seed); pts = []; off = 0.0
    for i in range(n):
        u = i / (n - 1); off = off * 0.55 + rr.uniform(-1, 1) * amp
        x_ = lerp(p0[0], p1[0], u); y_ = lerp(p0[1], p1[1], u) + off * math.sin(math.pi * u) ** 0.3
        pts.append((x_, y_))
    return pts
CRACKM = mat('crackdark', (0.012, 0.010, 0.009), 0.9)
# the wall crack: main run plus two short branches
WC_N = 70
WC_PATH = jag((-1.55, 1.70), (1.45, 0.98), WC_N, 0.055, 11)
WC_W = [0.004 + 0.012 * math.sin(math.pi * i / (WC_N - 1)) ** 0.6 * (0.7 + 0.6 * h1(i)) for i in range(WC_N)]
WCRACK = Ribbon('wallcrack', WC_N, CRACKM)
WC_BR = [(jag(WC_PATH[18], (WC_PATH[18][0] + 0.25, WC_PATH[18][1] + 0.38), 16, 0.03, 21), 0.30, 0.45),
         (jag(WC_PATH[44], (WC_PATH[44][0] + 0.12, WC_PATH[44][1] - 0.42), 16, 0.03, 23), 0.62, 0.78)]
WBR = [Ribbon(f'wallbranch{k}', 16, CRACKM) for k in range(len(WC_BR))]
def crack_pts(path, g, n):
    """the first fraction g of the path, resampled to n points (the rest bunched at the tip)"""
    m_ = len(path) - 1; out = []
    for i in range(n):
        s_ = g * m_ * i / (n - 1); j = min(int(s_), m_ - 1); k = s_ - j
        out.append((lerp(path[j][0], path[j + 1][0], k), lerp(path[j][1], path[j + 1][1], k)))
    return out
def set_wall_crack(g, wid=1.0):
    pts = [wall_pt(u_, v_, 0.004) for u_, v_ in crack_pts(WC_PATH, max(g, 0.002), WC_N)]
    ws = [WC_W[i] * wid * min(1.0, (1 - i / (WC_N - 1)) * 8 + 0.15) if g < 0.999 else WC_W[i] * wid for i in range(WC_N)]
    WCRACK.set(pts, ws, WALL_N); WCRACK.o.hide_render = g < 0.003
    for k, (bp, g0, g1) in enumerate(WC_BR):
        gb = clamp((g - g0) / (g1 - g0), 0, 1)
        WBR[k].set([wall_pt(u_, v_, 0.004) for u_, v_ in crack_pts(bp, max(gb, 0.002), 16)], [0.007 * wid * (1 - i / 16) for i in range(16)], WALL_N)
        WBR[k].o.hide_render = gb < 0.01
# chips knocked off where it split: a few dark flecks and a small spall
SPALL = []
for k in range(14):
    u_, v_ = WC_PATH[4 + k * 4]
    o = prim('ico_sphere', f'chip{k}', BRICK, scale=(1, 0.6, 1), radius=0.008 + 0.006 * h1(k), subdivisions=1); SPALL.append((o, k))

# ---- the test blocks: two concrete cylinders on little wooden grates over bowls, a clay funnel above each
TCONC = pbr('acg:Concrete048', 2.2, 'tconc', 'Object', tint=(0.86, 0.84, 0.80), boxp=True)
CLAY = mat('clay', (0.48, 0.22, 0.12), 0.8); noisy(CLAY, 30.0, 0.2, 0.1)
TB_R = 0.075; TB_H = 0.30; TB_Z0 = 0.855 + 0.09
TBLOCK = []
for k, dx in enumerate((-0.33, 0.33)):
    c = BENCH_C + Vector((dx, 0.0, 0.0))
    blk = prim('cylinder', f'tblock{k}', TCONC, loc=(c.x, c.y, TB_Z0 + TB_H / 2), radius=TB_R, depth=TB_H, vertices=48); bevel(blk, 0.004, 2)
    for sy in (-0.045, 0.045): box(f'grate{k}{sy}', (0.22, 0.022, 0.03), (c.x, c.y + sy, TB_Z0 - 0.015), WOOD)
    for sx in (-0.09, 0.09): box(f'gleg{k}{sx}', (0.025, 0.12, 0.06), (c.x + sx, c.y, TB_Z0 - 0.06), WOOD)
    bowl = lathe(f'bowl{k}', [(0.0, 0.0), (0.07, 0.0), (0.095, 0.03), (0.10, 0.045), (0.092, 0.045), (0.085, 0.032), (0.06, 0.008), (0.0, 0.008)], 40, CLAY, loc=(c.x, c.y, 0.89))
    fun = lathe(f'funnel{k}', [(0.012, 0.0), (0.016, 0.0), (0.02, 0.06), (0.075, 0.13), (0.07, 0.135), (0.014, 0.065), (0.008, 0.0)], 36, CLAY, loc=(c.x, c.y, TB_Z0 + TB_H + 0.12))
    stand = tube(f'fstand{k}', [(c.x + 0.14, c.y + 0.06, 0.89), (c.x + 0.14, c.y + 0.06, TB_Z0 + TB_H + 0.24), (c.x + 0.07, c.y + 0.03, TB_Z0 + TB_H + 0.24)], 0.008, WOOD, seg=8)
    cm = mat(f'tcrack{k}', (0.015, 0.013, 0.012), 0.9)
    # crack down the front of the block (facing -y), from the top rim to the bottom
    path = jag((0.0, TB_H / 2), (0.01, -TB_H / 2), 30, 0.008, 40 + k)
    rb = Ribbon(f'tcrack{k}', 30, cm)
    pts = []
    for x_, z_ in path:
        a_ = -math.pi / 2 + x_ / TB_R; pts.append(Vector((c.x + (TB_R + 0.0015) * math.cos(a_), c.y + (TB_R + 0.0015) * math.sin(a_), TB_Z0 + TB_H / 2 + z_)))
    rb.set(pts, [0.0035 + 0.002 * h1(i + 7 * k) for i in range(30)], Vector((0, -1, 0)))
    TBLOCK.append({'c': c, 'blk': blk, 'crack': rb, 'cm': cm, 'pts': pts, 'top': Vector((c.x, c.y, TB_Z0 + TB_H)), 'bottom': Vector((c.x, c.y - 0.01, TB_Z0 - 0.005)),
                   'funnel': Vector((c.x, c.y, TB_Z0 + TB_H + 0.12)), 'bowl': Vector((c.x, c.y, 0.89))})

# ---- the worker's bucket
BUCKET = P.place('ph:wooden_bucket_01', loc=(0, 0, 0), height=0.32, name='bucket')
BUCKET_ROOT = empty('bucket_root'); BUCKET.parent = BUCKET_ROOT
BK_H = BUCKET['size'][2]; BK_R = max(BUCKET['size'][0], BUCKET['size'][1]) / 2
WATERM = mat('water', (0.8, 0.88, 0.95), 0.03, trans=1.0, ior=1.33)
BK_WATER = prim('cylinder', 'bucketwater', WATERM, parent=BUCKET_ROOT, loc=(0, 0, BK_H * 0.72), radius=BK_R * 0.86, depth=0.004, vertices=32)
print('bucket', round(BK_H, 3), round(BK_R, 3))
# ================================================================ the worker: the house MakeHuman man (man.blend) in a short-sleeved undyed wool
# tunic (a flared skirt to the knee plus a shell lifted off his own chest and upper arms, so it bends with him), a belt, bare legs, sandals-free.
_BVG_KEYS = ('foot', 'toe')
def _retint_skin(m, col):
    """the MakeHuman skin is a node group: push its colour mix-in toward a sun-browned tone"""
    g = next((n for n in m.node_tree.nodes if n.type == 'GROUP'), None)
    if g is None: return
    g.inputs['colorMixIn'].default_value = (*col, 1); g.inputs['colorMixInStrength'].default_value = 0.95
    g.inputs['Roughness'].default_value = 0.5
LINEN = mat('wool', (0.46, 0.38, 0.28), 0.97, sheen=0.5); noisy(LINEN, 160.0, 0.12, 0.05)
BELT = mat('belt', (0.16, 0.09, 0.05), 0.75, sheen=0.2)
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
def make_shell(name, body, rig, col):
    """the tunic's top: the body's own chest, back and upper-arm faces, pushed out 1.4 cm, with the body's skin weights copied"""
    me_b = body.data; vg = {g.index: g.name for g in body.vertex_groups}
    def wmap(v): return {vg[g.group]: g.weight for g in v.groups if g.group in vg}
    keep = set()
    for v in me_b.vertices:
        w = wmap(v); z_ = v.co.z
        arm = w.get('upperarm01.L', 0) + w.get('upperarm01.R', 0) + w.get('upperarm02.L', 0) + w.get('upperarm02.R', 0)
        low = w.get('lowerarm01.L', 0) + w.get('lowerarm01.R', 0) + w.get('lowerarm02.L', 0) + w.get('lowerarm02.R', 0) + w.get('wrist.L', 0) + w.get('wrist.R', 0)
        if w.get('body', 0) > 0.5 and 0.93 < z_ < 1.43 and low < 0.05 and (arm < 0.3 or z_ > 1.17) and abs(v.co.x) < 0.33: keep.add(v.index)
    ms = [i for i, m_ in enumerate(me_b.materials) if m_ and 'body' in m_.name]
    faces = [p_ for p_ in me_b.polygons if p_.material_index in ms and all(i in keep for i in p_.vertices)]
    used = sorted({i for p_ in faces for i in p_.vertices}); rid = {i: k for k, i in enumerate(used)}
    vs = [tuple(me_b.vertices[i].co + me_b.vertices[i].normal * 0.022) for i in used]
    fs = [tuple(rid[i] for i in p_.vertices) for p_ in faces]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = rig; o.matrix_parent_inverse = body.matrix_parent_inverse.copy(); o.matrix_basis = body.matrix_basis.copy()
    o.data.materials.append(LINEN); groups = {}
    for k, i in enumerate(used):
        for gn, w in wmap(me_b.vertices[i]).items():
            if w <= 0: continue
            if gn not in groups: groups[gn] = o.vertex_groups.new(name=gn)
            groups[gn].add([k], w, 'REPLACE')
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig; md.use_deform_preserve_volume = True
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.006; sol.offset = 1.0
    # hide the body under it for good (nothing can poke through)
    inner = [i for i in used if all(j in keep for j in [i])]
    hg = body.vertex_groups.new(name='under_tunic'); hg.add([i for i in used if 0.96 < me_b.vertices[i].co.z < 1.40 and abs(me_b.vertices[i].co.x) < 0.17], 1.0, 'REPLACE')
    mk = body.modifiers.new('hide_under_tunic', 'MASK'); mk.vertex_group = 'under_tunic'; mk.invert_vertex_group = True; body.modifiers.move(len(body.modifiers) - 1, 0)
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
        self.shell = make_shell(name + '_shell', self.body, self.rig, self.col)
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
# ================================================================ effects: rain round the camera, the bucket's pour, steam off the slaking lime, the drips
# under the test blocks, and the inside-the-concrete set (cut face with aggregate and white lime lumps, the crack, water, crystals)
WORKER = Man('worker', (0.62, 0.42, 0.30))
# ---- rain: thin streaks in a box that follows the camera
RAIN_N = 2600; RAIN_BOX = (7.0, 7.0, 6.0); RAIN_V = 7.5
RAINM = mat('rain', (0.85, 0.9, 0.95), 0.15, alpha=0.32)
try: RAINM.surface_render_method = 'BLENDED'
except Exception: pass
_rr = random.Random(9)
RAIN_SEED = [(_rr.random(), _rr.random(), _rr.random(), 0.16 + 0.12 * _rr.random()) for _ in range(RAIN_N)]
_rv = []; _rf = []
for i in range(RAIN_N):
    b0 = len(_rv); _rv += [(0, 0, 0)] * 4; _rf.append((b0, b0 + 1, b0 + 2, b0 + 3))
RAIN = mesh('rain', _rv, _rf, RAINM, smooth_=False)
def set_rain(t, cam, on=1.0):
    co = []; cx, cy, cz = cam
    nshow = int(RAIN_N * on)
    for i, (a_, b_, c_, L_) in enumerate(RAIN_SEED):
        if i >= nshow: co.extend((cx, cy, cz - 50) * 4); continue
        x_ = cx + (a_ - 0.5) * RAIN_BOX[0]; y_ = cy + (b_ - 0.5) * RAIN_BOX[1]
        z_ = cz + (((c_ * RAIN_BOX[2] - RAIN_V * t) % RAIN_BOX[2]) - RAIN_BOX[2] / 2)
        if z_ < 0.0: z_ += RAIN_BOX[2]
        dx, dy = x_ - cx, y_ - cy; d_ = math.hypot(dx, dy) + 1e-6; px, py = -dy / d_ * 0.0012, dx / d_ * 0.0012
        tx, ty = 0.04 * L_, 0.02 * L_
        co.extend((x_ - px, y_ - py, z_, x_ + px, y_ + py, z_, x_ + px + tx, y_ + py + ty, z_ + L_, x_ - px + tx, y_ - py + ty, z_ + L_))
    RAIN.data.vertices.foreach_set('co', co); RAIN.data.update()
# ---- a stream of water (bucket pour, funnels)
class Stream:
    def __init__(self, name, n=20, seg=10):
        self.n = n; self.seg = seg; self.o = tube(name, [(0, 0, -i * 0.05) for i in range(n)], 0.02, WATERM, seg=seg, caps=True)
    def set(self, p0, v0, r0, t, zfloor, wob_amt=1.0):
        g = Vector((0, 0, -9.8)); pts = []
        tz = (v0.z + math.sqrt(max(v0.z ** 2 - 2 * g.z * (p0.z - zfloor), 0))) / -g.z
        for i in range(self.n):
            tau = tz * i / (self.n - 1); p = p0 + v0 * tau + 0.5 * g * tau * tau
            p += Vector((wob(t - tau, 9, i * 0.1), wob(t - tau, 9, 3 + i * 0.1), 0)) * 0.004 * wob_amt * (i / self.n); pts.append(p)
        co = []; T0 = (pts[1] - pts[0]).normalized(); up = Vector((1, 0, 0)) if abs(T0.x) < 0.9 else Vector((0, 1, 0)); Nn = T0.cross(up).normalized()
        for i, p in enumerate(pts):
            T = (pts[min(i + 1, self.n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
            rr = r0 * (1.0 - 0.4 * i / (self.n - 1)) * (1 + 0.12 * wob(t * 3 - i * 0.2, 7, i))
            for k in range(self.seg): co.extend(p + (Nn * math.cos(2 * math.pi * k / self.seg) + Bn * math.sin(2 * math.pi * k / self.seg)) * rr)
        self.o.data.vertices.foreach_set('co', co); self.o.data.update(); return pts[-1]
POUR = Stream('pour', 24, 12)
FSTREAM = [Stream(f'fstream{k}', 10, 8) for k in range(2)]
DRIPS = [[prim('uv_sphere', f'drip{k}_{j}', WATERM, radius=0.005, segments=10, ring_count=6) for j in range(4)] for k in range(2)]
for row in DRIPS:
    for d_ in row: d_.scale = (1, 1, 1.4)
WETTOP = [prim('cylinder', f'wettop{k}', WATERM, loc=TBLOCK[k]['top'] + Vector((0, 0, 0.002)), radius=TB_R * 0.9, depth=0.003, vertices=32) for k in range(2)]
BOWLW = [prim('cylinder', f'bowlwater{k}', WATERM, loc=TBLOCK[k]['bowl'] + Vector((0, 0, 0.012)), radius=0.075, depth=0.002, vertices=32) for k in range(2)]
# a bright wet trickle down each block's crack (it shrinks away on the healed one)
TTRICKLE = []
for k in range(2):
    rb = Ribbon(f'trickle{k}', 30, WATERM); TTRICKLE.append(rb)
# ---- steam off the slaking lime: soft volume puffs that rise, swell and thin out
STEAMM = bpy.data.materials.new('steam'); STEAMM.use_nodes = True; nt = STEAMM.node_tree; out_ = nt.nodes['Material Output']
for n in list(nt.nodes):
    if n.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n)
pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1)
gd = nt.nodes.new('ShaderNodeTexCoord')
# density: falls off from the puff's centre, broken up by noise, scaled by the object's 'dens'
vl = nt.nodes.new('ShaderNodeVectorMath'); vl.operation = 'LENGTH'; nt.links.new(gd.outputs['Object'], vl.inputs[0])
fall = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, vl.outputs['Value']), 0.0)
nz = tnoise(nt, gd.outputs['Object'], 2.5, 4.0)
dn = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', fall, math_(nt, 'ADD', nz, -0.15)), objattr(nt, 'dens'))
nt.links.new(dn, pv.inputs['Density']); nt.links.new(pv.outputs[0], out_.inputs['Volume'])
STEAM = []
for k in range(26):
    o = prim('ico_sphere', f'steam{k}', STEAMM, subdivisions=2, radius=1.0); o['dens'] = 0.0; STEAM.append(o)

# ---- inside the concrete (about 100x): a cut face full of aggregate and white lime lumps, split by the crack
MICRO = Vector((0.0, -3000.0, 0.0))
CONCM = pbr('acg:Concrete048', 0.35, 'concface', 'Object', tint=(0.30, 0.26, 0.21), boxp=True)
noisy(CONCM, 1.2, 0.18, 0.1); noisy(CONCM, 26.0, 0.35, 0.1)
SLAB_W, SLAB_D = 26.0, 4.0
CR_N = 60
CR_PATH = [(x_, z_) for z_, x_ in jag((14.0, 0.0), (-14.0, 0.0), CR_N, 0.45, 5)]       # top to bottom, wandering in x
# force it through the big lime lump at the middle
CR_PATH = [(x_ * (0.25 + 0.75 * min(1.0, abs(z_) / 3.0)), z_) for x_, z_ in CR_PATH]
CR_W = [0.20 + 0.10 * h1(i + 3) for i in range(CR_N)]
def cr_x(z_):
    for i in range(CR_N - 1):
        (x0, z0), (x1, z1) = CR_PATH[i], CR_PATH[i + 1]
        if z1 <= z_ <= z0: k = (z0 - z_) / max(z0 - z1, 1e-6); return lerp(x0, x1, k), lerp(CR_W[i], CR_W[i + 1], k)
    return CR_PATH[-1][0], CR_W[-1]
def prism(name, z_hi, z_lo, y0, y1, wscale, m, n=CR_N):
    """the crack's shape between two heights, as a closed solid from y0 to y1 (a cutter, the water, the calcite fill)"""
    vs = []; fs = []
    zs = [lerp(z_hi, z_lo, i / (n - 1)) for i in range(n)]
    for z_ in zs:
        x_, w_ = cr_x(z_); w_ *= wscale
        for yy in (y0, y1): vs += [(MICRO.x + x_ - w_ / 2, MICRO.y + yy, MICRO.z + z_), (MICRO.x + x_ + w_ / 2, MICRO.y + yy, MICRO.z + z_)]
    for i in range(n - 1):
        a_ = i * 4; b_ = (i + 1) * 4
        fs += [(a_, a_ + 1, b_ + 1, b_), (a_ + 2, b_ + 2, b_ + 3, a_ + 3), (a_, b_, b_ + 2, a_ + 2), (a_ + 1, a_ + 3, b_ + 3, b_ + 1)]
    fs += [(0, 2, 3, 1), ((n - 1) * 4, (n - 1) * 4 + 1, (n - 1) * 4 + 3, (n - 1) * 4 + 2)]
    return mesh(name, vs, fs, m, smooth_=False)
GAPM = mat('gapwall', (0.11, 0.095, 0.08), 0.95); noisy(GAPM, 3.0, 0.3, 0.1)
GAP_D = 2.6
def build_slab():
    """the cut face as two halves with the crack between them: front quads, crack walls (dark), the crack's floor, back and sides"""
    zs = [lerp(13.0, -13.0, i / 80) for i in range(81)]; H = SLAB_W / 2; y0 = MICRO.y; y1 = MICRO.y + SLAB_D
    vs = []; fs = []; mi = []
    def v(x_, y_, z_): vs.append((MICRO.x + x_, y_, MICRO.z + z_)); return len(vs) - 1
    for side in (-1, 1):
        for i in range(80):
            za, zb = zs[i], zs[i + 1]; xa, wa = cr_x(za); xb, wb = cr_x(zb)
            ea, eb = xa + side * wa / 2, xb + side * wb / 2; oa = side * H
            # front: from the crack edge out to the slab edge
            q = [v(ea, y0, za), v(oa, y0, za), v(oa, y0, zb), v(eb, y0, zb)]
            fs.append(tuple(q) if side > 0 else tuple(reversed(q))); mi.append(0)
            # crack wall going in GAP_D
            q = [v(ea, y0, za), v(eb, y0, zb), v(eb, y0 + GAP_D, zb), v(ea, y0 + GAP_D, za)]
            fs.append(tuple(q) if side > 0 else tuple(reversed(q))); mi.append(1)
    for i in range(80):      # the floor of the crack
        za, zb = zs[i], zs[i + 1]; xa, wa = cr_x(za); xb, wb = cr_x(zb)
        q = [v(xa - wa / 2, y0 + GAP_D, za), v(xb - wb / 2, y0 + GAP_D, zb), v(xb + wb / 2, y0 + GAP_D, zb), v(xa + wa / 2, y0 + GAP_D, za)]
        fs.append(tuple(q)); mi.append(1)
    q = [v(-H, y1, -H), v(H, y1, -H), v(H, y1, H), v(-H, y1, H)]; fs.append(tuple(q)); mi.append(0)   # back
    me = bpy.data.meshes.new('slab'); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new('slab', me); S.collection.objects.link(o); o.data.materials.append(CONCM); o.data.materials.append(GAPM)
    for p_, m_ in zip(me.polygons, mi): p_.material_index = m_
    me.validate(); me.update(); return o
GAPM = mat('gapwall', (0.09, 0.08, 0.07), 0.95); noisy(GAPM, 3.0, 0.3, 0.1)
SLAB = build_slab()
def cut(o):
    """tear a lump in two along the crack: push each vertex to its side, drop the faces that straddle it"""
    bpy.context.view_layer.update(); bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world.copy(); Mi = M.inverted(); side = {}
    for v in bm.verts:
        w = M @ v.co; x_, w_ = cr_x(w.z - MICRO.z); sd = 1 if (w.x - MICRO.x) > x_ else -1; side[v.index] = sd
    kill = [f for f in bm.faces if len({side[v.index] for v in f.verts}) > 1]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    for v in bm.verts:
        w = M @ v.co; x_, w_ = cr_x(w.z - MICRO.z); dx = (w.x - MICRO.x) - x_
        if abs(dx) < w_ / 2: w.x = MICRO.x + x_ + (w_ / 2 if dx > 0 else -w_ / 2); v.co = Mi @ w
    bm.to_mesh(o.data); bm.free()
# aggregate (volcanic tuff and brick bits) and lime lumps sitting in the face; anything the crack crosses is cut too
LIMEC = mat('limeclast', (0.93, 0.92, 0.88), 0.85); noisy(LIMEC, 6.0, 0.08, 0.05)
AGGM = [mat('tuff', (0.42, 0.33, 0.25), 0.8), mat('brickbit', (0.55, 0.24, 0.14), 0.75), mat('lava', (0.18, 0.17, 0.17), 0.7), mat('tuff2', (0.55, 0.47, 0.36), 0.85)]
for m_ in AGGM: noisy(m_, 5.0, 0.2, 0.1)
rr = random.Random(17); PLACED = []
def lump(name, m, c, rx, rz, seed, sub=3):
    o = prim('ico_sphere', name, m, loc=(MICRO.x + c[0], MICRO.y + 0.02, MICRO.z + c[1]), scale=(rx, 0.22 * min(rx, rz) + 0.05, rz), subdivisions=sub)
    o.rotation_euler.y = rr.uniform(0, 6.28)
    for v in o.data.vertices: v.co *= 1.0 + 0.22 * mnoise.noise(v.co * 2.2 + Vector((seed, 0, 0))) + 0.06 * mnoise.noise(v.co * 9.0 + Vector((0, seed, 0)))
    x_, w_ = cr_x(c[1])
    if abs(c[0] - x_) < max(rx, rz) * 1.3 + w_: cut(o)
    return o
BIG = lump('bigclast', LIMEC, (0.0, 0.0), 1.05, 1.25, 3.0, 4); BIG.scale.y = 0.45
PLACED.append(((0.0, 0.0), 1.3))
LIMES = [BIG]
for kind, count, rmin, rmax in (('agg', 70, 0.5, 1.9), ('lime', 46, 0.12, 0.55)):
    for k in range(count * 6):
        if (kind == 'agg' and len(PLACED) >= count + 1) or (kind == 'lime' and len(LIMES) >= count + 1): break
        c = (rr.uniform(-11, 11), rr.uniform(-11, 11)); r_ = rr.uniform(rmin, rmax)
        if any(math.hypot(c[0] - q[0], c[1] - q[1]) < r_ + qr + 0.12 for q, qr in PLACED): continue
        PLACED.append((c, r_))
        if kind == 'agg': lump(f'agg{k}', AGGM[k % 4], c, r_ * rr.uniform(0.7, 1.3), r_ * rr.uniform(0.6, 1.1), k * 1.7)
        else: LIMES.append(lump(f'lime{k}', LIMEC, c, r_ * rr.uniform(0.8, 1.2), r_ * rr.uniform(0.7, 1.1), k * 2.3 + 50))
SANDM = [mat('sandbit0', (0.30, 0.26, 0.21), 0.8), mat('sandbit1', (0.62, 0.57, 0.48), 0.8), mat('sandbit2', (0.16, 0.14, 0.13), 0.7)]
for k in range(420):
    c = (rr.uniform(-12, 12), rr.uniform(-12, 12)); r_ = rr.uniform(0.04, 0.13)
    if any(math.hypot(c[0] - q[0], c[1] - q[1]) < r_ + qr for q, qr in PLACED): continue
    x_, w_ = cr_x(c[1])
    if abs(c[0] - x_) < w_ + r_: continue
    o = prim('ico_sphere', f'aggs{k}', SANDM[k % 3], loc=(MICRO.x + c[0], MICRO.y + 0.01, MICRO.z + c[1]), scale=(r_, r_ * 0.5, r_ * rr.uniform(0.7, 1.2)), subdivisions=1)
# the water that runs down into the crack, and the calcite that grows out of it
CWATERM = mat('crackwater', (0.35, 0.62, 0.95), 0.05, trans=0.35, ior=1.33, coat=0.8, emit=(0.2, 0.45, 0.9), estr=0.35)
CWATER = prism('crackwater', 14.5, 14.0, 0.02, 2.4, 0.97, CWATERM)
def set_crack_water(z_lo, z_hi=14.5):
    tmp = prism('_tmpw', z_hi, max(z_lo, -14.5), 0.02, 2.4, 0.97, CWATERM)
    co = [0.0] * (len(tmp.data.vertices) * 3); tmp.data.vertices.foreach_get('co', co); CWATER.data.vertices.foreach_set('co', co); CWATER.data.update()
    bpy.data.objects.remove(tmp, do_unlink=True)
CALCM = mat('calcite', (0.97, 0.96, 0.92), 0.12, trans=0.15, ior=1.6, coat=0.6, emit=(1.0, 0.98, 0.92), estr=0.15)
CRYS = []
for i in range(520):
    z_ = rr.uniform(-12.5, 12.5); x_, w_ = cr_x(z_); side = 1 if i % 2 else -1; yy = rr.uniform(0.03, 0.45)
    o = box(f'xtal{i}', (1.0, 1.0, 1.0), (MICRO.x + x_ + side * w_ / 2, MICRO.y + yy, MICRO.z + z_), CALCM)
    o.rotation_euler = (rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), rr.uniform(0, 6.28)); o['sz'] = w_ * rr.uniform(0.55, 1.0); o['z'] = z_; o['side'] = side
    o['t0'] = rr.random(); o.scale = (1e-3,) * 3; o.hide_render = True; CRYS.append(o)
CFILL = prism('calcfill', 14.4, -14.4, 0.01, 2.0, 1.0, CALCM); CFILL.hide_render = True
# a dark room round the set so the open sky does not flatten it; only the two lamps light it
ROOM = box('microroom', (60.0, 60.0, 60.0), MICRO + Vector((0, -10.0, 0)), mat('roomdark', (0.012, 0.011, 0.010), 0.95))
for p_ in ROOM.data.polygons: p_.flip()
MICRO_OBJS = [SLAB, CWATER, CFILL, ROOM] + CRYS + [o for o in bpy.data.objects if o.name.startswith(('agg', 'lime', 'bigclast'))]
MLIGHT = light_at('microlight', 'AREA', MICRO + Vector((-9.0, -5.0, 13.0)), MICRO, 1300.0, (1.0, 0.96, 0.9), 5.0)
MLIGHT2 = light_at('microlight2', 'AREA', MICRO + Vector((10.0, -12.0, -4.0)), MICRO, 220.0, (0.8, 0.88, 1.0), 6.0)
# ================================================================ the story, frame by frame
def local_t(t): return t - END if t >= T_RESET else t
CP_I = 35
CRACK_PT = wall_pt(*WC_PATH[CP_I], 0.0)
TB_PT = TBLOCK[0]['pts'][15]
MCRACK = lambda z_: MICRO + Vector((cr_x(z_)[0], 0.0, z_))

def worker(t, tl):
    m_ = WORKER; up = Vector((0, 0, 1))
    m_.root.location = TR_C + Vector((0.0, -0.80, 0.0)); m_.root.rotation_euler = (0, 0, math.pi)
    pour = smooth(T_POUR - 0.5, T_POUR + 0.4, tl) * (1 - smooth(T_POUR + 2.6, T_POUR + 3.4, tl)) if tl >= 0 else 0.0
    look_ = (1 - smooth(4.5, 6.0, tl)) * smooth(0.25, 0.9, tl) if tl >= 0 else 0.0   # he turns to look at the crack
    sway = wob(t, 0.7, 2) * 2.0
    m_.pose(spine=4 + 14 * pour, neck=-3 - 4 * pour, head=4 + 10 * pour + 6 * look_, head_yaw=-55 * look_ + sway, twist=-12 * look_)
    bpy.context.view_layer.update()
    fw = m_.fwd(); rt = m_.right()
    tilt = R(105) * pour + R(4) * wob(t, 1.1, 3) * pour
    c = m_.world((0.0, -0.36 - 0.22 * pour, 0.78 + 0.28 * pour))
    yaw = Matrix.Rotation(math.pi, 4, 'Z'); tip = Matrix.Rotation(-tilt, 4, rt)
    BUCKET_ROOT.matrix_world = Matrix.Translation(c - (tip.to_3x3() @ Vector((0, 0, BK_H * 0.5)))) @ tip @ yaw
    bpy.context.view_layer.update()
    Mb = BUCKET_ROOT.matrix_world
    for s_, sx in (('R', -1), ('L', 1)):
        rim = Mb @ Vector((sx * BK_R * 1.02, 0, BK_H * 0.80)); ctr = Mb @ Vector((0, 0, BK_H * 0.80))
        m_.tg['h' + s_].location = rim + (rim - ctr).normalized() * 0.02
        m_.tg['p' + s_].location = m_.world((0.7 if s_ == 'L' else -0.7, 0.35, 0.9))
        m_.orient(s_, -(Mb.to_3x3() @ Vector((0, 0, 1))).normalized(), (ctr - rim), 1.0)
        m_.fingers(s_, 0.85)
    bpy.context.view_layer.update()
    return pour, Mb

def fx(t, st):
    tl = st['tl']
    # the wall crack
    g = smooth(T_CRACK, T_CRACK + 0.55, tl) if tl >= 0 else 0.0
    set_wall_crack(g, 0.8 + 0.2 * smooth(0.5, 3.5, tl) if tl >= 0 else 0.8)
    for o, k in SPALL:
        u_, v_ = WC_PATH[4 + k * 4]; on = g > (4 + k * 4) / WC_N
        o.hide_render = not on
        if on:
            age = max(tl - T_CRACK - (4 + k * 4) / WC_N * 0.55, 0.0); fall = min(age, 0.6)
            p = wall_pt(u_ + 0.01 * h1(k), v_ - 0.01, 0.01) + Vector((0, -0.25 * fall, -4.9 * fall * fall))
            p.z = max(p.z, 0.008); o.location = p; o.rotation_euler = (age * 9, age * 5, 0)
    # the pour, the steam
    pour, Mb = st['pour'], st['Mb']
    lip = Mb @ Vector((0, -BK_R * 0.98, BK_H * 0.95)); lipd = (Mb.to_3x3() @ Vector((0, -0.4, 1.0))).normalized()
    BK_WATER.hide_render = pour > 0.75
    on = pour > 0.45 and tl >= 0
    POUR.o.hide_render = not on
    if on: POUR.set(lip, lipd * 0.6, 0.014 + 0.02 * pour, t, TR_C.z + 0.18)
    st_on = smooth(T_STEAM, T_STEAM + 0.6, tl) * (1 - smooth(T_DIVE2 + 1.0, T_DIVE2 + 2.0, tl)) if tl >= 0 else 0.0
    for k, o in enumerate(STEAM):
        per = 2.4; ph = ((t + h1(k) * per) % per) / per
        base = TR_C + Vector((-0.45 + 0.9 * h1(k + 3), -0.25 + 0.5 * h1(k + 5), 0.22))
        o.location = base + Vector((0.18 * wob(t, 0.4, k), 0.12 * wob(t, 0.5, k + 9), 1.7 * ph ** 0.8))
        r_ = 0.10 + 0.55 * ph; o.scale = (r_, r_, r_ * 0.85)
        o['dens'] = 16.0 * st_on * (1 - ph) ** 1.5 * smooth(0.0, 0.12, ph)
        o.hide_render = o['dens'] < 0.02
    # the test blocks: water from the funnels; the left one heals and stops dripping, the right keeps running
    bench_on = (tl >= T_OUT2 - 1.0 and tl < T_RESET) if tl >= 0 else False
    heal = smooth(T_HEAL0, T_HEAL1, tl)
    for k, tb in enumerate(TBLOCK):
        f0 = tb['funnel']; s_on = bench_on
        FSTREAM[k].o.hide_render = not s_on
        if s_on: FSTREAM[k].set(f0, Vector((0, 0, -0.1)), 0.004, t, tb['top'].z + 0.002)
        h = heal if k == 0 else 0.0
        cm = tb['cm'].node_tree.nodes['Principled BSDF']
        c0 = Vector((0.015, 0.013, 0.012)); c1 = Vector((0.80, 0.78, 0.72)); cc = c0.lerp(c1, h)
        cm.inputs['Base Color'].default_value = (*cc, 1); cm.inputs['Roughness'].default_value = 0.9 - 0.4 * h
        WETTOP[k].hide_render = not s_on; WETTOP[k].scale = (1.0 + 0.08 * h, 1.0 + 0.08 * h, 1.0)
        tr = TTRICKLE[k]; tr.set([p + Vector((0, -0.0025, 0)) for p in tb['pts']], [0.0055 * (1 - h)] * 30, Vector((0, -1, 0))); tr.o.hide_render = (not s_on) or h > 0.97
        rate = (1 - h)
        for j, d_ in enumerate(DRIPS[k]):
            per = 0.42; u = ((t + j * per / 4 + 0.13 * k) % per) / per
            src = tb['bottom']; fall = (src.z - tb['bowl'].z - 0.01)
            d_.location = src + Vector((0, 0, -fall * u * u))
            d_.hide_render = (not s_on) or (h1(j + int(t / per) * 7 + k) > rate) or u > 0.97
        BOWLW[k].hide_render = not bench_on
    # inside the concrete: water runs in, turns milky with lime, crystals grow and seal it
    zw = lerp(14.5, -14.5, smooth(T_WATER, T_WATER + 1.4, t))
    set_crack_water(zw if T_WATER <= t else 14.45)
    CWATER.hide_render = t < T_WATER
    milk = smooth(T_WATER + 0.9, B[7] - 0.2, t)
    wb = CWATERM.node_tree.nodes['Principled BSDF']; wb.inputs['Base Color'].default_value = (*Vector((0.35, 0.62, 0.95)).lerp(Vector((0.86, 0.88, 0.88)), milk), 1)
    wb.inputs['Transmission Weight'].default_value = 0.35 - 0.3 * milk; wb.inputs['Roughness'].default_value = 0.05 + 0.25 * milk
    wb.inputs['Emission Color'].default_value = (*Vector((0.2, 0.45, 0.9)).lerp(Vector((0.7, 0.72, 0.72)), milk), 1)
    span = T_SEAL - T_CRYS
    for o in CRYS:
        s0 = T_CRYS + span * (0.55 * (14.0 - o['z']) / 28.0 + 0.3 * o['t0']); k = smooth(s0, s0 + span * 0.45, t)
        o.hide_render = k < 0.02; sz = o['sz'] * k; o.scale = (sz, sz * 0.8, sz * 1.2)
    CFILL.hide_render = t < T_SEAL - 0.2

def state(t):
    tl = local_t(t); return {'tl': tl}

# ---- camera
def key(t, p, q, lens): return (t, Vector(p), Vector(q), lens)
CP_V = Vector(CRACK_PT)
K = [
    key(0.0, (0.60, 9.15, 1.55), (0.05, 12.0, 1.30), 24),
    key(B[1] - 0.2, (0.48, 9.45, 1.50), (0.05, 12.0, 1.30), 24),
    key(B[1] + 1.4, CP_V + Vector((0.25, -1.05, 0.12)), CP_V + Vector((0.0, 0, -0.02)), 30),      # in close: rain running into the crack
    key(T_DIVE1, CP_V + Vector((0.12, -0.70, 0.06)), CP_V, 30),
    key(T_DIVE1 + 0.6, CP_V + Vector((0.0, 0.05, 0.0)), CP_V + Vector((0, 1, 0)), 30),            # into the crack
]
LP = LIMES[3] if len(LIMES) > 3 else LIMES[-1]
LPV = LP.location.copy()
MK1 = [
    key(T_DIVE1 + 0.6, MCRACK(1.6) + Vector((0, -0.25, 0)), MCRACK(1.6) + Vector((0, 1.0, 0)), 26),
    key(T_IN1 + 0.9, MICRO + Vector((1.6, -9.5, 1.2)), MICRO + Vector((0.4, 0, 0.2)), 30),           # the cut face: lumps of lime everywhere
    key(B[3] + 0.4, MICRO + Vector((-0.6, -8.8, -0.4)), MICRO + Vector((-0.6, 0, -0.4)), 30),
    key(T_OUT1 - 0.6, LPV + Vector((0.3, -3.0, 0.3)), LPV, 30),
    key(T_OUT1, LPV + Vector((0.0, -0.25, 0.0)), LPV, 30),                                          # into a white lump
]
HEAPV = TR_C + Vector((0.1, 0.0, 0.25))
K2 = [
    key(T_OUT1, HEAPV + Vector((0.0, -0.06, 0.02)), HEAPV + Vector((0.0, 1.0, 0.0)), 30),           # out of the quicklime heap
    key(T_PIT + 0.9, TR_C + Vector((-1.25, -1.45, 1.55)), TR_C + Vector((0.0, -0.2, 0.55)), 28),     # the trough: he pours, it steams
    key(T_DIVE2 - 0.9, TR_C + Vector((-1.10, -1.30, 1.45)), TR_C + Vector((0.0, -0.1, 0.5)), 28),
    key(T_DIVE2 - 0.1, CP_V + Vector((0.18, -0.9, 0.1)), CP_V, 30),
    key(T_DIVE2 + 0.5, CP_V + Vector((0.0, 0.05, 0.0)), CP_V + Vector((0, 1, 0)), 30),               # into the crack again
]
MK2 = [
    key(T_DIVE2 + 0.5, MCRACK(1.4) + Vector((0, -0.2, 0)), MCRACK(1.4) + Vector((0, 1.0, 0)), 26),
    key(T_IN2 + 0.7, MICRO + Vector((0.9, -4.6, 0.7)), MICRO + Vector((0.0, 0, 0.0)), 30),           # the crack runs through a lime lump
    key(B[6] + 0.2, MICRO + Vector((0.7, -4.2, 0.6)), MICRO + Vector((0.0, 0, 0.1)), 30),
    key(B[7] - 0.2, MICRO + Vector((0.5, -3.0, 0.9)), MICRO + Vector((0.0, 0.6, 0.0)), 30),          # water in, milky
    key(T_SEAL - 0.1, MICRO + Vector((0.35, -2.2, 0.35)), MICRO + Vector((0.0, 0.8, 0.0)), 30),      # crystals close it up
    key(T_OUT2, MCRACK(-0.2) + Vector((0, -0.3, 0)), MCRACK(-0.2) + Vector((0, 1.0, 0)), 30),
]
TBV = Vector(TB_PT)
K3 = [
    key(T_OUT2, TBV + Vector((0.0, -0.03, 0.0)), TBV + Vector((0, 1, 0)), 30),                       # out of the left test block's crack
    key(T_BENCH + 0.8, BENCH_C + Vector((0.0, -1.85, 1.42)), BENCH_C + Vector((0.0, 0.0, 1.02)), 30),
    key(B[9] - 0.3, BENCH_C + Vector((0.0, -1.75, 1.38)), BENCH_C + Vector((0.0, 0.0, 1.02)), 30),
    key(B[9] + 0.7, BENCH_C + Vector((0.45, -0.85, 1.18)), BENCH_C + Vector((0.33, 0.0, 1.0)), 32),   # the right block keeps dripping
    key(T_REV, BENCH_C + Vector((0.43, -0.88, 1.18)), BENCH_C + Vector((0.33, 0.0, 1.0)), 32),
    key(B[11] - 0.3, PC + Vector((-58.0, -78.0, 34.0)), PC + Vector((-12.0, 0.0, 16.0)), 30),        # up and back: the Pantheon
    key(B[12] - 0.3, PC + Vector((-34.0, -46.0, 66.0)), PC + Vector((0.0, 0.0, 30.0)), 30),          # over the dome and its oculus
    key(END, K[0][1], K[0][2], K[0][3]),                                                             # back down to frame one
]
def interp(keys, t):
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0.0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0.0
    else:
        i = max(j for j in range(len(keys)) if keys[j][0] <= t); k0, k1 = keys[i], keys[i + 1]; u = sm((t - k0[0]) / (k1[0] - k0[0]))
    c0, c1 = k0[1], k1[1]; a0, a1 = k0[2], k1[2]
    d0 = (a0 - c0).normalized(); d1 = (a1 - c1).normalized(); cp = c0.lerp(c1, u); dr = d0.slerp(d1, u) if d0.dot(d1) > -0.99 else d1
    fl = lerp((a0 - c0).length, (a1 - c1).length, u)
    return cp, cp + dr * fl, lerp(k0[3], k1[3], u)
def camera(t):
    if t < T_DIVE1 + 0.6: return interp(K, t), False
    if t < T_OUT1: return interp(MK1, t), True
    if t < T_DIVE2 + 0.5: return interp(K2, t), False
    if t < T_OUT2: return interp(MK2, t), True
    return interp(K3, t), False

def frame(f):
    t = f / FPS; S.frame_set(f); st = state(t); tl = st['tl']
    st['pour'], st['Mb'] = worker(t, tl)
    fx(t, st)
    (cp, ct, lens), micro = camera(t)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = Vector(q_[0:3]), Vector(q_[3:6]), q_[6]; micro = (cp - MICRO).length < 60
    for o in MICRO_OBJS: o.hide_render = (not micro) or o.hide_render if o in CRYS or o in (CWATER, CFILL) else (not micro)
    rain_on = 0.0 if micro else (1.0 - smooth(T_REV, T_REV + 1.2, t) * (1 - smooth(END - 2.4, END - 0.6, t)))
    RAIN.hide_render = rain_on < 0.01
    if rain_on >= 0.01: set_rain(t, cp, rain_on)
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

