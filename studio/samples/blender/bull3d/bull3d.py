# The Brazen Bull, as a museum walk: the bronze bull turns on its turntable; Sicily and the ruler Phalaris; the workshop - plans, the model,
# the door, locked, the fire, the sound rings; a game board - the inventor pawn goes in, the people rise, the king goes in; the record -
# written 500 years later, MADE UP?; the twist - a real bronze bull rides to Carthage and back; the Roman writer; a river statue; lost. One shot.
#   python3 bull3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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
C.caustics_reflective = False; C.caustics_refractive = False; C.sample_clamp_indirect = 1.5; C.sample_clamp_direct = 12.0; C.blur_glossy = 0.6
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

# ================================================================ props: the bronze bull, game pieces, little helpers
def bronze_mat(name, base=(0.33, 0.18, 0.075), patina=(0.07, 0.17, 0.13), amt=0.5):
    """old bronze: warm metal, darker in the hollows of a big noise, with spots of green patina (rougher, not metal)"""
    m = mat(name, base, 0.3, 1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    v = coord(nt, 'Object'); big = tnoise(nt, v, 3.5, 6.0); fine = tnoise(nt, v, 30.0, 4.0)
    pat = ramp_v(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', big, 0.8), math_(nt, 'MULTIPLY', fine, 0.2)), 0.56, 0.72)
    pat = math_(nt, 'MULTIPLY', pat, amt)
    col = mixc(nt, math_(nt, 'MULTIPLY', fine, 0.5), base, tuple(c * 0.55 for c in base))
    nt.links.new(mixc(nt, pat, col, patina), b.inputs['Base Color'])
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, pat), b.inputs['Metallic'])
    nt.links.new(math_(nt, 'ADD', 0.36, math_(nt, 'MULTIPLY', pat, 1.2)), b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.004
    nt.links.new(fine, bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


BULL_NPZ = np.load(asset('bull.npz'))
def bull_mesh(name='bullme'):
    """the bull's body: a smooth sculpt made by assets/bull_sdf.py (body along +x, head at +x, feet on z = 0, horns, ears, tail included)"""
    v, f = BULL_NPZ['v'], BULL_NPZ['f']
    me = bpy.data.meshes.new(name); me.vertices.add(len(v)); me.vertices.foreach_set('co', v.ravel())
    me.loops.add(f.size); me.loops.foreach_set('vertex_index', f.ravel()); me.polygons.add(len(f))
    me.polygons.foreach_set('loop_start', np.arange(0, f.size, 3, dtype=np.int32)); me.polygons.foreach_set('loop_total', np.full(len(f), 3, np.int32))
    me.update(); me.validate(); me.polygons.foreach_set('use_smooth', np.ones(len(f), bool)); return me


BULL_ME = None
def bull(name, m, loc=(0, 0, 0), s=1.0, parent=None, door=True):
    """a bronze bull with dark eyes and a hinged door in its -y flank (opens outward, toward -y). Returns (root, door hinge, door hole)"""
    global BULL_ME
    if BULL_ME is None: BULL_ME = bull_mesh()
    rt = empty(name, parent, loc=loc); rt.scale = (s, s, s)
    body = obj(name + '_b', BULL_ME, None, (0, 0, 0), rt); body.data = BULL_ME
    if not BULL_ME.materials: BULL_ME.materials.append(m)
    body.material_slots[0].link = 'OBJECT'; body.material_slots[0].material = m
    for k, p_ in enumerate(BULL_NPZ['eyes']): prim('uv_sphere', f'{name}_ey{k}', M_EYE, rt, loc=tuple(p_), segments=12, ring_count=8, radius=0.016)
    for k, p_ in enumerate(BULL_NPZ['nose']): prim('uv_sphere', f'{name}_ns{k}', M_BLACK, rt, loc=tuple(p_), segments=10, ring_count=6, radius=1.0, scale=(0.008, 0.012, 0.012))
    hinge = hole = None
    if door:
        # the door: a riveted bronze hatch on the flat flank plate (y = -0.211), hinged on its back (-x) edge
        DX0, DX1, DZ0, DZ1, DY = -0.19, 0.07, 0.52, 0.74, -0.211
        hole = box(name + '_hole', (DX1 - DX0 - 0.016, 0.02, DZ1 - DZ0 - 0.016), ((DX0 + DX1) / 2, DY + 0.008, (DZ0 + DZ1) / 2), M_HOLE, parent=rt)
        for (a_, b_) in (((DX0, DZ0), (DX1, DZ0)), ((DX1, DZ0), (DX1, DZ1)), ((DX1, DZ1), (DX0, DZ1)), ((DX0, DZ1), (DX0, DZ0))):
            tube(f'{name}_df{a_[0]}{a_[1]}{b_[1]}', [(a_[0], DY, a_[1]), (b_[0], DY, b_[1])], 0.008, m, rt, seg=8)
        hinge = empty(name + '_dh', rt, loc=(DX0 + 0.004, DY - 0.008, 0))
        box(name + '_dp', (DX1 - DX0 - 0.014, 0.012, DZ1 - DZ0 - 0.014), ((DX1 - DX0) / 2, 0, (DZ0 + DZ1) / 2), m, bv=0.004, parent=hinge)
        for k in range(4):
            for zz in (DZ0 + 0.028, DZ1 - 0.028):
                prim('uv_sphere', f'{name}_rv{k}{zz}', m, hinge, loc=(0.03 + (DX1 - DX0 - 0.06) * k / 3, -0.007, zz), segments=8, ring_count=5, radius=0.008)
        tube(name + '_dk', [(DX1 - DX0 - 0.045, -0.006, (DZ0 + DZ1) / 2 - 0.025), (DX1 - DX0 - 0.045, -0.03, (DZ0 + DZ1) / 2), (DX1 - DX0 - 0.045, -0.006, (DZ0 + DZ1) / 2 + 0.025)], 0.006, m, hinge, seg=8)
        hole.hide_render = True
    return rt, hinge, hole


def piece(name, kind, m, loc, s=1.0, parent=None):
    """a game piece about 0.12 tall (pawn) or 0.16 (king), base on z = 0"""
    rt = empty(name, parent or HALL, loc=loc); rt.scale = (s, s, s)
    if kind == 'pawn':
        lathe(name + '_l', [(0.0, 0.0), (0.034, 0.0), (0.034, 0.01), (0.026, 0.018), (0.014, 0.05), (0.011, 0.075), (0.022, 0.082), (0.012, 0.088), (0.0, 0.088)], 24, m, rt)
        prim('uv_sphere', name + '_h', m, rt, loc=(0, 0, 0.105), segments=16, ring_count=10, radius=0.022)
    else:
        lathe(name + '_l', [(0.0, 0.0), (0.04, 0.0), (0.04, 0.012), (0.03, 0.022), (0.016, 0.08), (0.014, 0.11), (0.028, 0.118), (0.02, 0.126), (0.024, 0.14), (0.0, 0.14)], 24, m, rt)
        for k in range(5):
            a = 2 * math.pi * k / 5; prim('cone', f'{name}_pt{k}', m, rt, loc=(0.018 * math.cos(a), 0.018 * math.sin(a), 0.152), vertices=8, radius1=0.008, radius2=0.001, depth=0.026)
    return rt


def low_z(root):
    """lowest point of a prop (all its meshes, modifiers applied) in the root's own frame, as built"""
    bpy.context.view_layer.update(); inv = root.matrix_world.inverted(); z = 1e9
    for o in [root] + list(root.children_recursive):
        if o.type != 'MESH': continue
        mw = inv @ o.matrix_world
        dg = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = dg.to_mesh()
        for v in me.vertices: z = min(z, (mw @ v.co).z)
        dg.to_mesh_clear()
    return z


def flames(name, parent, n, spread, seed, z0=0.0):
    """little fire: cones that grow and flicker (see fire_step)"""
    gf_ = random.Random(seed); out = []
    for k in range(n):
        fx, fy = gf_.uniform(-spread[0], spread[0]), gf_.uniform(-spread[1], spread[1])
        o = prim('cone', f'{name}{k}', M_FLAME if k % 3 else M_FLAME2, parent, loc=(fx, fy, z0), vertices=10, radius1=1.0, radius2=0.0, depth=1.0)
        out.append((o, gf_.uniform(0.025, 0.045), gf_.uniform(0.09, 0.2), gf_.uniform(0, 6), gf_.uniform(0, 0.4), z0))
    return out


def fire_step(fl, t, t0, scale=1.0):
    fi = smooth(t0 - 0.05, t0 + 0.45, t)
    for o, r_, h_, ph, dl, z0 in fl:
        f_ = 0.75 + 0.25 * math.sin(t * 23 + ph) + 0.15 * wob(t, 9, ph)
        k_ = fi * smooth(t0 + dl * 0.5, t0 + dl * 0.5 + 0.3, t) * scale
        o.scale = (max(1e-4, r_ * k_), max(1e-4, r_ * k_), max(1e-4, h_ * k_ * f_)); o.location.z = z0 + 0.5 * h_ * k_ * f_
    return fi

# ================================================================ set: a museum hall (x -4..30.8), the bull's story in exhibits along the back wall
def brick_mat(name, c1, c2, mortar, scale=1.0, rough=0.85, plane='xz', bump=0.6, row=0.5, w=0.5, mortar_w=0.02, seed=0.0):
    m = mat(name, c1, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    if plane == 'xz': mp.inputs['Rotation'].default_value = (math.pi / 2, 0, 0)
    mp.inputs['Location'].default_value = (seed, seed * 0.7, 0)
    br = nt.nodes.new('ShaderNodeTexBrick'); nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
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
M_WOODF = brick_mat('woodfloor', (0.30, 0.17, 0.08), (0.24, 0.13, 0.06), (0.12, 0.06, 0.03), 1.0, rough=0.35, plane='xy', bump=0.25, row=0.16, w=1.8, mortar_w=0.006, seed=2.0)
M_WOODF.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.35
M_PLASTER = noisy(mat('plaster', (0.50, 0.47, 0.43), 0.8), 3.0, 0.12)
M_WAINS = noisy(mat('wains', (0.13, 0.05, 0.035), 0.6, coat=0.06), 20.0, 0.15)
M_CEIL = noisy(mat('ceil', (0.30, 0.29, 0.27), 0.9), 2.0, 0.1)
M_BRASS = mat('brass', (0.78, 0.55, 0.22), 0.28, 1.0)
M_WOOD = noisy(mat('wood', (0.26, 0.14, 0.065), 0.55, coat=0.15), 14.0, 0.3)
M_WOODDK = noisy(mat('wooddk', (0.08, 0.045, 0.025), 0.5, coat=0.12), 14.0, 0.3)
M_PAPER = noisy(mat('paper', (0.80, 0.74, 0.60), 0.8), 8.0, 0.08)
M_PARCH = noisy(mat('parch', (0.72, 0.6, 0.4), 0.85), 6.0, 0.18)
M_INK = mat('ink', (0.01, 0.01, 0.012), 0.3); M_GREY = mat('greyink', (0.22, 0.22, 0.22), 0.6)
M_GOLD = mat('gold', (0.85, 0.62, 0.25), 0.25, 1.0)
M_PLAQ = mat('plaq', (0.06, 0.05, 0.045), 0.5); M_GILT = mat('gilt', (0.9, 0.7, 0.32), 0.3, 1.0)
M_BLACK = mat('blackm', (0.02, 0.02, 0.02), 0.6); M_IRON = noisy(mat('iron', (0.06, 0.06, 0.065), 0.55, 0.8), 30.0, 0.3)
M_RED = mat('red', (0.55, 0.04, 0.04), 0.6); M_WHITE = mat('white', (0.85, 0.84, 0.80), 0.6)
M_STAMP = mat('stamp', (0.75, 0.04, 0.03), 0.6)
M_GREENINK = mat('greenink', (0.02, 0.32, 0.07), 0.5)
M_REDV = noisy(mat('redv', (0.42, 0.02, 0.03), 0.8, sheen=0.5), 40.0, 0.2)
M_STEEL = mat('steel', (0.6, 0.61, 0.63), 0.25, 1.0); M_LEATHER = noisy(mat('leather', (0.16, 0.08, 0.035), 0.45, coat=0.2), 40.0, 0.2)
M_BRONZE = bronze_mat('bronze'); M_EYE = mat('eye', (0.01, 0.01, 0.01), 0.05, coat=1.0); M_HOLE = emis('hole', (0, 0, 0), 0.0)
M_MARBLE = noisy(mat('marble', (0.82, 0.8, 0.76), 0.3, coat=0.2), 5.0, 0.08)
M_STONE = noisy(mat('stone', (0.2, 0.18, 0.16), 0.85), 9.0, 0.3)
M_SEA = noisy(mat('sea', (0.08, 0.22, 0.38), 0.5), 4.0, 0.15); M_LAND = noisy(mat('land', (0.68, 0.56, 0.36), 0.8), 7.0, 0.15)
M_BLUEP = noisy(mat('bluep', (0.03, 0.12, 0.32), 0.7), 5.0, 0.12); M_CHALK = mat('chalk', (0.85, 0.9, 0.95), 0.6)
M_SQ1 = mat('sq1', (0.75, 0.68, 0.52), 0.4); M_SQ2 = mat('sq2', (0.16, 0.09, 0.05), 0.4)
M_PAWNW = mat('pawnw', (0.82, 0.78, 0.68), 0.35, coat=0.3); M_PAWNB = noisy(mat('pawnb', (0.35, 0.2, 0.09), 0.4, coat=0.3), 20.0, 0.3)
M_FLAME = emis('flame', (1.0, 0.42, 0.06), 9.0); M_FLAME2 = emis('flame2', (1.0, 0.8, 0.25), 12.0)
M_STEAM = mat('steam', (0.85, 0.85, 0.85), 0.95, alpha=0.14); M_STEAM.blend_method = 'BLEND'
M_RING = emis_mix('ringm', (1.0, 0.75, 0.35), 6.0, 'fade')
M_WATER = mat('water', (0.06, 0.25, 0.32), 0.04, trans=0.15, ior=1.33, coat=0.6)
_wnt = M_WATER.node_tree; _wb = _wnt.nodes['Principled BSDF']; WATER_MAP = _wnt.nodes.new('ShaderNodeMapping'); _wnt.links.new(coord(_wnt, 'Object'), WATER_MAP.inputs['Vector'])
_wbp = _wnt.nodes.new('ShaderNodeBump'); _wbp.inputs['Strength'].default_value = 0.3; _wbp.inputs['Distance'].default_value = 0.01
_wnt.links.new(tnoise(_wnt, WATER_MAP.outputs['Vector'], 7.0, 3.0, 1.5), _wbp.inputs['Height']); _wnt.links.new(_wbp.outputs['Normal'], _wb.inputs['Normal'])
M_RIPPLE = mat('ripple', (0.8, 0.9, 0.95), 0.1, alpha=0.5); M_RIPPLE.blend_method = 'BLEND'

# ---------------------------------------------------------------- the museum hall
HX0, HX1 = -4.0, 30.8; HW = HX1 - HX0; HC = (HX0 + HX1) / 2
HALL = empty('hall')
box('hfloor', (HW, 13.0, 0.2), (HC, -0.9, -0.1), M_WOODF, parent=HALL)
box('hback', (HW, 0.3, 6.0), (HC, 5.55, 3.0), M_PLASTER, parent=HALL)
box('hwains', (HW, 0.06, 1.0), (HC, 5.38, 0.5), M_WAINS, bv=0.01, parent=HALL)
box('hrail', (HW, 0.08, 0.05), (HC, 5.36, 1.02), M_GILT, parent=HALL)
box('hfront', (HW, 0.3, 6.0), (HC, -7.55, 3.0), M_PLASTER, parent=HALL)
box('hleft', (0.3, 13.0, 6.0), (HX0 - 0.15, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hright', (0.3, 13.0, 6.0), (HX1 + 0.15, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hceil', (HW, 13.4, 0.3), (HC, -0.9, 6.15), M_CEIL, parent=HALL)
for xb in range(-3, 31, 3): box(f'beam{xb}', (0.3, 13.0, 0.35), (xb + 0.5, -0.9, 5.83), M_WOOD, bv=0.01, parent=HALL)
RAIL = box('rail', (HW - 0.8, 0.08, 0.06), (HC, 0.4, 5.55), M_BLACK, parent=HALL)
MUSEUM_LIGHTS = []                                  # (light, base energy)
SPOTS = {}
def track_spot(key_, x, target, e=900, size=0.12, ang=46):
    p = Vector((x, 0.4, 5.45)); can = prim('cylinder', f'can{key_}', M_BLACK, HALL, loc=p, vertices=16, radius=0.07, depth=0.22)
    can.rotation_mode = 'QUATERNION'; can.rotation_quaternion = (Vector(target) - p).to_track_quat('-Z', 'Y')
    lt = light_at(f'spot{key_}', 'SPOT', p, target, e, (1.0, 0.92, 0.80), size); lt.data.spot_size = R(ang); lt.data.spot_blend = 0.6
    MUSEUM_LIGHTS.append((lt, e)); SPOTS[key_] = (lt, e); return lt
for k, xa in enumerate((-1.0, 5.4, 11.8, 18.2, 24.6, 29.8)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 330, (1.0, 0.93, 0.84), 3.0), 330))


def wall_sign(name, x, z, body, w=1.6, h=0.42, size=0.2, m_bg=None, m_txt=None, y=5.37):
    P_ = empty(name, HALL, loc=(x, y, z))
    box(name + 'b', (w, 0.02, h), (0, 0, 0), m_bg or M_PLAQ, bv=0.006, parent=P_)
    box(name + 'f', (w + 0.05, 0.016, h + 0.05), (0, 0.006, 0), M_GILT, bv=0.006, parent=P_)
    text3d(name + 't', body, size, (0, -0.012, 0), (R(90), 0, 0), m_txt or M_GILT, P_, extrude=0.003); return P_


def tent_card(name, loc, body, size, m_txt, w=0.24, h=0.12, rz=0.0, m_card=None):
    """a little folded card standing on a table, text on its front (-y) face; pivot at its base"""
    c_ = empty(name, HALL, loc=loc); c_.rotation_euler = (0, 0, rz)
    for s_ in (-1, 1): box(f'{name}{s_}', (w, 0.004, h), (0, s_ * h * 0.2, h * 0.48), m_card or M_PAPER, rot=(R(-12 * s_), 0, 0), parent=c_)
    text3d(name + 't', body, size, (0, -h * 0.2 - 0.009, h * 0.47), (R(78), 0, 0), m_txt, c_, extrude=0.001); return c_


PLAT_Z = 0.12
M_PLATM = noisy(mat('platm', (0.10, 0.06, 0.04), 0.5, coat=0.2), 10.0, 0.2)
def platform(x, w, d=1.5, y=4.15):
    box(f'plat{x}', (w, d, PLAT_Z), (x, y, PLAT_Z / 2), M_PLATM, bv=0.01, parent=HALL)


def puffs(name, n, m=None):
    return [prim('uv_sphere', f'{name}{k}', m or M_STEAM, HALL, loc=(0, 0, -50), segments=14, ring_count=8, radius=1.0) for k in range(n)]


# ================================================================ exhibit 0: the Brazen Bull on its turntable (x = 0)
X0, Y0 = 0.0, 3.75
lathe('dais0', [(0.0, 0.0), (1.08, 0.0), (1.08, 0.12), (1.04, 0.15), (0.0, 0.15)], 64, M_STONE, HALL, loc=(X0, Y0, 0))
TT0 = empty('tt0', HALL, loc=(X0, Y0, 0.15))
lathe('tt0d', [(0.0, 0.0), (0.98, 0.0), (0.98, 0.035), (0.0, 0.035)], 64, M_WOODDK, TT0)
for k in range(16): box(f'tt0s{k}', (0.12, 0.02, 0.006), (0.92 * math.cos(2 * math.pi * k / 16), 0.92 * math.sin(2 * math.pi * k / 16), 0.037), M_GILT, rot=(0, 0, 2 * math.pi * k / 16), parent=TT0)
BULL0, DH0, _ = bull('bull0', M_BRONZE, (0.06, 0, 0.035), 1.22, TT0, door=True)
STEAM0 = puffs('st0_', 10)
wall_sign('sg0', X0, 2.9, 'THE BRAZEN BULL', 2.3, 0.42, 0.17)
PLQ0 = empty('plq0', HALL, loc=(X0 - 0.16, Y0 - 1.085, 0.11))
box('plq0b', (0.34, 0.012, 0.07), (0.16, 0, 0), M_GILT, bv=0.004, parent=PLQ0)
text3d('plq0t', 'LEGEND', 0.04, (0.16, -0.008, 0), (R(90), 0, 0), M_INK, PLQ0, extrude=0.001)
prim('uv_sphere', 'plq0s', M_BRASS, HALL, loc=(X0 - 0.16, Y0 - 1.093, 0.11), segments=8, ring_count=6, radius=0.007)
track_spot('e0', X0, (X0, Y0, 0.8), 1100, ang=44)

# ================================================================ exhibit 1: Sicily - a wall map with a pin; the ruler's bust; the year (x = 3.6)
X1 = 3.6
MAP1 = empty('map1', HALL, loc=(X1 + 0.38, 5.35, 1.66))
box('map1s', (1.2, 0.02, 0.86), (0, 0, 0), M_SEA, bv=0.005, parent=MAP1)
box('map1f', (1.26, 0.018, 0.92), (0, 0.008, 0), M_GILT, bv=0.006, parent=MAP1)
MAP1.scale = (1.25, 1.25, 1.25)
def flat_poly(name, pts, m, parent, y=-0.014, th=0.008):
    """a flat island shape on a wall map (local x-z plane), standing out toward -y"""
    vs = [(x_, y, z_) for x_, z_ in pts] + [(x_, y + th, z_) for x_, z_ in pts]; n = len(pts)
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=False)
SICILY = [(-0.42, 0.12), (-0.2, 0.17), (0.05, 0.16), (0.28, 0.19), (0.38, 0.2), (0.33, 0.07), (0.3, -0.06), (0.36, -0.2), (0.24, -0.26),
          (0.1, -0.18), (-0.06, -0.12), (-0.22, -0.06), (-0.36, -0.02), (-0.44, 0.06)]
flat_poly('sic1', SICILY, M_LAND, MAP1)
flat_poly('ita1', [(0.42, 0.43), (0.5, 0.3), (0.47, 0.24), (0.55, 0.22), (0.6, 0.3), (0.6, 0.43)], M_LAND, MAP1)
text3d('map1t', 'SICILY', 0.1, (-0.02, -0.026, 0.03), (R(90), 0, 0), M_INK, MAP1, extrude=0.001)
PIN1_REST = Vector((-0.06, -0.03, -0.1))           # Akragas, on the south coast
PIN1 = empty('pin1', MAP1)
tube('pin1n', [(0, 0, 0), (0, -0.05, 0)], 0.003, M_STEEL, PIN1, seg=6)
prim('uv_sphere', 'pin1h', M_STAMP, PIN1, loc=(0, -0.055, 0), segments=12, ring_count=8, radius=0.022)
YEAR1 = wall_sign('sg1', X1 + 0.38, 2.6, '570 BC', 0.9, 0.36, 0.17)
def marble_bust(name, x, y, h, label, crown=False, beard=False, s=1.25):
    """a marble bust on a column (top at h): shoulders, neck, a head with brow, nose, ears and a hair cap. Returns (root, the bust part)"""
    rt = empty(name, HALL, loc=(x, y, 0))
    lathe(name + 'c', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.06), (0.13, 0.1), (0.11, h - 0.08), (0.18, h - 0.04), (0.18, h), (0.0, h)], 32, M_MARBLE, rt)
    box(name + 'nb', (0.34, 0.012, 0.06), (0, -0.12, h - 0.25), M_GILT, bv=0.003, parent=rt)
    text3d(name + 'nt', label, 0.036, (0, -0.127, h - 0.25), (R(90), 0, 0), M_INK, rt, extrude=0.001)
    up = empty(name + 'u', rt, loc=(0, 0, h)); up.scale = (s, s, s)
    lathe(name + 't', [(0.0, 0.0), (0.07, 0.0), (0.07, 0.04), (0.2, 0.1), (0.23, 0.2), (0.16, 0.3), (0.06, 0.34), (0.0, 0.34)], 28, M_MARBLE, up).scale = (1.0, 0.6, 1.0)
    lathe(name + 'n', [(0.0, 0.3), (0.056, 0.3), (0.05, 0.43), (0.0, 0.43)], 16, M_MARBLE, up)
    def sph(n_, loc, r, sc): return prim('uv_sphere', name + n_, M_MARBLE, up, loc=loc, segments=24, ring_count=14, radius=r, scale=sc)
    sph('h', (0, 0, 0.52), 0.105, (0.88, 1.0, 1.12)); sph('jw', (0, -0.035, 0.455), 0.07, (0.95, 0.95, 0.7))
    sph('no', (0, -0.1, 0.515), 0.02, (0.75, 1.0, 1.5)); sph('br', (0, -0.07, 0.565), 0.075, (1.05, 0.5, 0.28))
    sph('hc', (0, 0.018, 0.57), 0.108, (0.93, 1.0, 0.78))
    for sx in (-1, 1): sph(f'ea{sx}', (0.094 * sx, 0.0, 0.52), 0.026, (0.4, 0.8, 1.2))
    if beard: sph('bd', (0, -0.055, 0.44), 0.065, (1.0, 0.75, 0.85))
    if crown:
        lathe(name + 'k', [(0.093, 0.0), (0.105, 0.0), (0.105, 0.04), (0.093, 0.04)], 32, M_GOLD, up, loc=(0, 0.01, 0.58))
        for k in range(6):
            a_ = 2 * math.pi * k / 6; prim('cone', f'{name}p{k}', M_GOLD, up, loc=(0.1 * math.cos(a_), 0.01 + 0.1 * math.sin(a_), 0.64), vertices=8, radius1=0.017, radius2=0.002, depth=0.05)
    return rt, up
BUST1, BUSTUP = marble_bust('bust1', X1 - 0.62, 4.6, 1.0, 'PHALARIS', crown=True, beard=True)
BUSTUP_REST = BUSTUP.location.copy()
track_spot('e1', X1, (X1, 4.9, 1.5), 950, ang=52)

# ================================================================ exhibit 2: the workshop - plans, the model bull on a stand over a fire pit (x = 7.2)
X2, Y2 = 7.2, 4.0
platform(X2, 2.2)
STAND_Z = PLAT_Z + 0.62
for sx in (-1, 1):
    for sy in (-1, 1): tube(f'st2l{sx}{sy}', [(X2 + 0.36 * sx, Y2 + 0.22 * sy, PLAT_Z), (X2 + 0.33 * sx, Y2 + 0.2 * sy, STAND_Z)], 0.016, M_IRON, HALL, seg=8)
for k in range(7): tube(f'st2g{k}', [(X2 - 0.34, Y2 - 0.2 + 0.4 * k / 6, STAND_Z), (X2 + 0.34, Y2 - 0.2 + 0.4 * k / 6, STAND_Z)], 0.009, M_IRON, HALL, seg=6)
for sy in (-1, 1): tube(f'st2r{sy}', [(X2 - 0.36, Y2 + 0.21 * sy, STAND_Z), (X2 + 0.36, Y2 + 0.21 * sy, STAND_Z)], 0.013, M_IRON, HALL, seg=8)
lathe('pit2', [(0.0, PLAT_Z), (0.3, PLAT_Z), (0.32, PLAT_Z + 0.08), (0.26, PLAT_Z + 0.09), (0.0, PLAT_Z + 0.05)], 32, noisy(mat('ash', (0.035, 0.03, 0.028), 0.9), 20.0, 0.4), HALL, loc=(X2, Y2, 0))
for k in range(5):
    a_ = R(36 * k + 10); prim('cylinder', f'log2{k}', M_WOODDK, HALL, loc=(X2 + 0.07 * math.cos(a_), Y2 + 0.07 * math.sin(a_), PLAT_Z + 0.1), rot=(0, R(90), a_), vertices=12, radius=0.028, depth=0.36)
MODEL_S = 0.62
MODEL2, DH2, HOLE2 = bull('bull2', M_BRONZE, (X2 - 0.04, Y2, -50), MODEL_S, HALL, door=True)
MODEL2_REST = Vector((X2 - 0.04, Y2, STAND_Z + 0.009))
FIRE2 = flames('fl2_', None, 12, (0.13, 0.1), 31, 0.0); FIRE2_ROOT = empty('fire2', HALL, loc=(X2, Y2, PLAT_Z + 0.12))
for o, *_ in FIRE2: o.parent = FIRE2_ROOT
FIRELT2 = light_at('firelt2', 'POINT', (X2, Y2 - 0.1, PLAT_Z + 0.35), (X2, Y2, 0), 0.0, (1.0, 0.5, 0.15), 0.1)
# the padlock that snaps onto the door (bull local coords: the door's front edge)
LOCK2 = empty('lock2', MODEL2, loc=(0.095, -0.245, 0.63))
box('lk2b', (0.05, 0.02, 0.045), (0, 0, -0.02), M_BRASS, bv=0.006, parent=LOCK2)
tube('lk2s', [(-0.016, 0, 0.0), (-0.016, 0, 0.03), (0.0, 0, 0.042), (0.016, 0, 0.03), (0.016, 0, 0.0)], 0.005, M_STEEL, LOCK2, seg=8)
# brass pipes in its nostrils, and the sound rings that come out of them
PIPES2 = []
for k, p_ in enumerate(BULL_NPZ['nose']):
    pp = empty(f'pipe2{k}', MODEL2, loc=tuple(p_)); pp.rotation_euler = (0, R(90), R(8) * (1 if k else -1))
    prim('cone', f'pipe2c{k}', M_BRASS, pp, loc=(0, 0, 0.045), vertices=16, radius1=0.012, radius2=0.03, depth=0.09)
    PIPES2.append(pp)
RINGS2 = []
for k in range(6):
    o = lathe(f'ring2{k}', [(0.8, -0.06), (1.0, -0.06), (1.0, 0.06), (0.8, 0.06)], 40, M_RING, HALL, loc=(0, 0, -50)); o.rotation_euler = (0, R(90), 0); o['fade'] = 0.0
    RINGS2.append(o)
STEAM2 = puffs('st2_', 8)
# the plans: a blueprint unrolls down the wall
SCRL2 = empty('scrl2', HALL, loc=(X2 + 0.05, 5.34, 2.55))
prim('cylinder', 'scrl2rod', M_WOODDK, HALL, loc=(X2 + 0.05, 5.33, 2.56), rot=(0, R(90), 0), vertices=12, radius=0.025, depth=1.2)
SHEET2 = empty('sheet2', SCRL2)
box('sh2b', (1.05, 0.006, 0.75), (0, 0, -0.375), M_BLUEP, parent=SHEET2)
def chalk_line(name, pts, par, r=0.0045):
    return tube(name, [(x_, -0.006, z_) for x_, z_ in pts], r, M_CHALK, par, seg=5)
_bo = [(-0.36, -0.3), (-0.36, -0.52), (-0.33, -0.66), (-0.3, -0.66), (-0.3, -0.5), (0.18, -0.5), (0.2, -0.66), (0.24, -0.66), (0.25, -0.48),
       (0.3, -0.38), (0.38, -0.36), (0.44, -0.42), (0.47, -0.37), (0.41, -0.28), (0.34, -0.2), (0.22, -0.16), (0.05, -0.18), (-0.25, -0.18), (-0.36, -0.3)]
chalk_line('sh2o', _bo, SHEET2)
for s_ in (-1, 1): chalk_line(f'sh2h{s_}', [(0.36, -0.22), (0.4 + 0.02 * s_, -0.14), (0.46 + 0.03 * s_, -0.1)], SHEET2, 0.004)
chalk_line('sh2d', [(-0.17, -0.27), (0.02, -0.27), (0.02, -0.42), (-0.17, -0.42), (-0.17, -0.27)], SHEET2, 0.004)
text3d('sh2t', 'BRONZE BULL', 0.05, (0.0, -0.007, -0.08), (R(90), 0, 0), M_CHALK, SHEET2, extrude=0.0006)
text3d('sh2d2', 'DOOR', 0.032, (-0.075, -0.007, -0.345), (R(90), 0, 0), M_CHALK, SHEET2, extrude=0.0006)
SCRL2.scale = (1, 1, 1e-4)
wall_sign('sg2', X2 - 0.95, 2.35, 'ATHENS\nWORKSHOP', 0.8, 0.42, 0.11)
track_spot('e2', X2, (X2, 4.2, 1.2), 1000, ang=50)

# ================================================================ exhibit 3: the game board - the king, the inventor pawn, the people, a little bronze bull (x = 10.6)
X3, Y3 = 10.6, 4.05
box('tab3', (0.9, 0.7, 0.76), (X3, Y3, 0.38), M_WOODDK, bv=0.012, parent=HALL)
box('tab3t', (0.96, 0.76, 0.03), (X3, Y3, 0.775), M_WOOD, bv=0.006, parent=HALL)
TOP3 = 0.79
SQ = 0.075
for i in range(8):
    for j in range(8): box(f'sq3_{i}{j}', (SQ, SQ, 0.008), (X3 + (i - 3.5) * SQ, Y3 + (j - 3.5) * SQ, TOP3 + 0.004), M_SQ1 if (i + j) % 2 else M_SQ2, parent=HALL)
box('sq3f', (8 * SQ + 0.04, 8 * SQ + 0.04, 0.006), (X3, Y3, TOP3 + 0.003), M_GILT, parent=HALL)
TOP3 += 0.008
TOK3, DH3, HOLE3 = bull('bull3', M_BRONZE, (X3 + 0.17, Y3 + 0.12, TOP3), 0.24, HALL, door=True)
KING3 = piece('king3', 'king', M_GOLD, (X3 - 0.08, Y3 - 0.06, TOP3), 1.15)
INV3 = piece('inv3', 'pawn', M_PAWNB, (X3 - 0.22, Y3 - 0.12, TOP3), 1.0)
CROWD3 = []
for k in range(9):
    a_ = R(120 + 25 * k); p_ = Vector((X3 - 0.08 + 0.2 * math.cos(a_), Y3 - 0.06 + 0.17 * math.sin(a_), TOP3))
    if p_.y < Y3 - 0.29: p_.y = Y3 - 0.29
    CROWD3.append((piece(f'crowd3{k}', 'pawn', M_PAWNW, p_, 0.92), p_))
wall_sign('sg3', X3, 2.35, 'THE LEGEND', 1.1, 0.4, 0.14)
track_spot('e3', X3, (X3, Y3, 0.8), 950, ang=40)

# ================================================================ exhibit 4: the record - a lectern and an old book; a timeline on the wall (x = 14.0)
X4 = 14.0
platform(X4, 1.8)
box('lect4', (0.62, 0.46, 0.95), (X4 - 0.42, 4.0, PLAT_Z + 0.475), M_WOODDK, bv=0.01, parent=HALL)
BK4 = empty('bk4', HALL, loc=(X4 - 0.42, 4.0, PLAT_Z + 1.0)); BK4.rotation_euler = (R(32), 0, 0); BK4.scale = (1.75, 1.75, 1.75)
box('bk4sp', (0.02, 0.24, 0.02), (0, 0, 0.0), M_LEATHER, parent=BK4)
PG4 = []
for s_ in (-1, 1):
    pv = empty(f'bk4pv{s_}', BK4, loc=(0, 0, 0.012))
    box(f'bk4c{s_}', (0.2, 0.26, 0.012), (s_ * 0.1, 0, 0), M_WOODDK, bv=0.003, parent=pv)
    box(f'bk4p{s_}', (0.19, 0.25, 0.01), (s_ * 0.1, 0, 0.011), M_PARCH, parent=pv)
    PG4.append((pv, s_))
text3d('bk4t', 'THE BULL\nOF PHALARIS', 0.02, (-0.1, 0.03, 0.0175), (0, 0, 0), M_INK, PG4[0][0], extrude=0.0005)
for k in range(5): box(f'bk4la{k}', (0.13, 0.006, 0.001), (-0.1, -0.03 - 0.02 * k, 0.017), M_GREY, parent=PG4[0][0])
for k in range(8): box(f'bk4l{k}', (0.13, 0.006, 0.001), (0.1, 0.08 - 0.022 * k, 0.017), M_GREY, parent=PG4[1][0])
STAMP4 = empty('stamp4', BK4, loc=(0.03, 0.0, 0.03)); STAMP4.rotation_euler = (0, 0, R(12))
text3d('stamp4t', 'MADE UP?', 0.055, (0, 0, 0), (0, 0, 0), M_STAMP, STAMP4, extrude=0.002)
QM4 = empty('qm4', HALL, loc=(X4 - 0.42, 4.1, PLAT_Z + 1.62))
text3d('qm4t', '?', 0.45, (0, 0, 0), (R(90), 0, 0), M_STAMP, QM4, extrude=0.04)
TL4 = empty('tl4', HALL, loc=(X4 + 0.32, 5.36, 1.95)); TL4.scale = (0.9, 0.9, 0.9)
box('tl4b', (1.5, 0.02, 0.7), (0, 0, 0), M_PLAQ, bv=0.006, parent=TL4)
box('tl4f', (1.56, 0.016, 0.76), (0, 0.006, 0), M_GILT, bv=0.006, parent=TL4)
for sx, tx in ((-1, '570 BC\nTHE RULER'), (1, '60 BC\nSTORY WRITTEN')):
    box(f'tl4m{sx}', (0.025, 0.012, 0.16), (0.55 * sx, -0.014, -0.08), M_GILT, parent=TL4)
    text3d(f'tl4t{sx}', tx, 0.055, (0.55 * sx, -0.016, -0.24), (R(90), 0, 0), M_GILT, TL4, extrude=0.002)
TLBAR = empty('tlbar', TL4, loc=(-0.55, -0.016, -0.08))
box('tl4bar', (1.1, 0.012, 0.03), (0.55, 0, 0), M_STAMP, parent=TLBAR); TLBAR.scale = (1e-4, 1, 1)
TLTXT = text3d('tl4y', '500 YEARS', 0.09, (0, -0.016, 0.12), (R(90), 0, 0), M_GILT, TL4, extrude=0.003)
track_spot('e4', X4, (X4, 4.6, 1.5), 950, ang=52)

# ================================================================ exhibit 5: the twist - a table map; the bull token rides to Carthage and home (x = 17.6)
X5, Y5 = 17.6, 4.0
box('tab5', (1.4, 0.9, 0.8), (X5, Y5, 0.4), M_WOODDK, bv=0.012, parent=HALL)
box('tab5t', (1.46, 0.96, 0.03), (X5, Y5, 0.815), M_WOOD, bv=0.006, parent=HALL)
TOP5 = 0.83
MAP5 = empty('map5', HALL, loc=(X5, Y5, TOP5))
box('map5s', (1.3, 0.8, 0.006), (0, 0, 0.003), M_SEA, parent=MAP5)
def flat_xy(name, pts, m, parent, z=0.006, th=0.006):
    vs = [(x_, y_, z) for x_, y_ in pts] + [(x_, y_, z + th) for x_, y_ in pts]; n = len(pts)
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=False)
flat_xy('sic5', [(p_[0] * 0.6 + 0.22, p_[1] * 0.6 + 0.2) for p_ in SICILY], M_LAND, MAP5)
flat_xy('ita5', [(0.5, 0.4), (0.5, 0.34), (0.53, 0.3), (0.6, 0.32), (0.64, 0.4)], M_LAND, MAP5)
flat_xy('afr5', [(-0.65, -0.4), (-0.65, -0.05), (-0.5, -0.02), (-0.36, -0.06), (-0.27, -0.1), (-0.22, -0.06), (-0.17, -0.13), (-0.18, -0.22),
                 (-0.08, -0.26), (0.05, -0.3), (0.2, -0.34), (0.4, -0.36), (0.65, -0.33), (0.65, -0.4)], M_LAND, MAP5)
AKR5 = Vector((0.18, 0.1, 0.012)); CAR5 = Vector((-0.24, -0.12, 0.012))
for nm_, p_, tx_ in (('ak5', AKR5, 'AKRAGAS'), ('ca5', CAR5, 'CARTHAGE')):
    prim('cylinder', nm_ + 'd', M_STAMP, MAP5, loc=tuple(p_ + Vector((0, 0, 0.002))), vertices=16, radius=0.016, depth=0.006)
CARLBL5 = text3d('ca5t', 'CARTHAGE', 0.045, (-0.26, -0.2, 0.017), (0, 0, 0), M_INK, MAP5, extrude=0.001)
text3d('ak5t', 'SICILY', 0.04, (0.24, 0.27, 0.016), (0, 0, 0), M_INK, MAP5, extrude=0.001)
def arc5(u, bend=0.16):
    p_ = AKR5.lerp(CAR5, u); d = (CAR5 - AKR5); nrm = Vector((-d.y, d.x, 0)).normalized()
    return p_ + nrm * bend * math.sin(math.pi * u)
DOTS5 = [prim('uv_sphere', f'dot5{k}', M_INK, MAP5, loc=tuple(arc5((k + 1) / 12) + Vector((0, 0, 0.0))), segments=8, ring_count=5, radius=0.006) for k in range(11)]
TOK5, _, _ = bull('bull5', M_BRONZE, (0, 0, 0), 0.17, MAP5, door=False)
REAL5 = empty('real5', HALL, loc=(X5 + 0.44, Y5 - 0.43, TOP5 + 0.005)); REAL5.rotation_euler = (R(-58), 0, R(4))
box('rl5b', (0.36, 0.006, 0.14), (0, 0, 0.07), M_WHITE, bv=0.004, parent=REAL5)
box('rl5f', (0.38, 0.004, 0.16), (0, 0.004, 0.07), M_GREENINK, parent=REAL5)
text3d('rl5t', 'REAL', 0.09, (0, -0.006, 0.07), (R(90), 0, 0), M_GREENINK, REAL5, extrude=0.002)
CARD5A = tent_card('cd5a', (X5 - 0.42, Y5 + 0.36, TOP5), '406 BC', 0.05, M_INK, 0.22, 0.11)
CARD5B = tent_card('cd5b', (X5 + 0.0, Y5 + 0.36, TOP5), '146 BC', 0.05, M_STAMP, 0.22, 0.11)
# a Roman helmet with a red crest, dropped by Carthage
HELM5 = empty('helm5', HALL)
lathe('hl5d', [(0.0, 0.12), (0.05, 0.118), (0.085, 0.1), (0.1, 0.06), (0.105, 0.0), (0.112, -0.005), (0.112, 0.0), (0.0, 0.0)], 32, M_STEEL, HELM5).scale = (1.0, 1.12, 1.0)
for sx in (-1, 1): box(f'hl5c{sx}', (0.012, 0.06, 0.08), (0.1 * sx, -0.03, -0.035), M_BRASS, rot=(0, R(-8 * sx), 0), parent=HELM5)
tube('hl5r', [(0, 0.11, 0.11), (0, 0.04, 0.17), (0, -0.05, 0.16), (0, -0.1, 0.11)], 0.022, M_REDV, HELM5, seg=10)
HELM5_REST = Vector((X5 - 0.36, Y5 - 0.27, TOP5 + 0.006 + 0.005)); HELM5.location = (0, 0, -60)
wall_sign('sg5', X5, 2.35, 'THE REAL BULL', 1.4, 0.4, 0.14)
track_spot('e5', X5, (X5, Y5, 0.85), 950, ang=44)

# ================================================================ exhibit 6: the Roman writer - a marble bust; a scroll unrolls (x = 21.0)
X6 = 21.0
BUST6, _ = marble_bust('bust6', X6 - 0.35, 4.6, 1.0, 'CICERO')
SCRL6 = empty('scrl6', HALL, loc=(X6 + 0.42, 5.34, 2.2))
prim('cylinder', 'scrl6rod', M_WOODDK, HALL, loc=(X6 + 0.42, 5.32, 2.21), rot=(0, R(90), 0), vertices=12, radius=0.022, depth=0.78)
box('sc6b', (0.66, 0.006, 0.8), (0, 0, -0.4), M_PARCH, parent=SCRL6)
text3d('sc6t', 'A REMINDER\nOF HOW CRUEL\nTHEIR OLD\nRULERS WERE', 0.058, (0, -0.007, -0.38), (R(90), 0, 0), M_INK, SCRL6, extrude=0.0008)
ROLL6 = prim('cylinder', 'scrl6bot', M_WOODDK, HALL, loc=(X6 + 0.42, 5.31, 2.2), rot=(0, R(90), 0), vertices=12, radius=0.026, depth=0.74)
SCRL6.scale = (1, 1, 1e-4)
wall_sign('sg6', X6, 2.75, 'ROME', 0.8, 0.36, 0.15)
track_spot('e6', X6, (X6, 4.8, 1.5), 950, ang=48)

# ================================================================ exhibit 7: a river statue - a bronze bull on a rock in a stone pool of running water (x = 24.2)
X7, Y7 = 24.2, 4.0
for nm_, sz_, lc_ in (('pool7a', (1.5, 0.06, 0.34), (X7, Y7 - 0.37, 0.17)), ('pool7b', (1.5, 0.06, 0.34), (X7, Y7 + 0.37, 0.17)),
                      ('pool7c', (0.06, 0.8, 0.34), (X7 - 0.72, Y7, 0.17)), ('pool7d', (0.06, 0.8, 0.34), (X7 + 0.72, Y7, 0.17))):
    box(nm_, sz_, lc_, M_STONE, bv=0.012, parent=HALL)
WATER7 = box('water7', (1.38, 0.68, 0.02), (X7, Y7, 0.28), M_WATER, parent=HALL)
box('pool7in', (1.38, 0.68, 0.02), (X7, Y7, 0.08), mat('poolbt', (0.05, 0.08, 0.08), 0.8), parent=HALL)
lathe('rock7', [(0.0, 0.05), (0.26, 0.05), (0.27, 0.2), (0.22, 0.38), (0.0, 0.4)], 12, M_STONE, HALL, loc=(X7, Y7, 0)).scale = (1.3, 0.8, 1.0)
STAT7, _, _ = bull('bull7', M_BRONZE, (0, 0, -60), 0.55, HALL, door=False)
STAT7_REST = Vector((X7 - 0.02, Y7, 0.4))
RIPS7 = [lathe(f'rip7{k}', [(0.94, 0.0), (1.0, 0.0), (1.0, 0.003), (0.94, 0.003)], 40, M_RIPPLE, HALL, loc=(0, 0, -60)) for k in range(6)]
SPL7 = puffs('spl7_', 10, M_RIPPLE)
wall_sign('sg7', X7, 2.35, 'RIVER GOD?', 1.3, 0.4, 0.15)
track_spot('e7', X7, (X7, Y7, 0.4), 950, ang=44)

# ================================================================ exhibit 8: lost - an empty plinth (x = 27.6)
X8, Y8 = 27.6, 4.0
box('plin8', (0.8, 0.8, 0.9), (X8, Y8, 0.45), M_MARBLE, bv=0.015, parent=HALL)
box('plin8t', (0.86, 0.86, 0.04), (X8, Y8, 0.92), M_MARBLE, bv=0.01, parent=HALL)
box('dust8', (0.62, 0.3, 0.002), (X8, Y8, 0.941), mat('dust8m', (0.62, 0.6, 0.56), 0.95), parent=HALL)
box('plq8b', (0.42, 0.012, 0.1), (X8, Y8 - 0.407, 0.62), M_GILT, bv=0.003, parent=HALL)
text3d('plq8t', 'LOCATION\nUNKNOWN', 0.032, (X8, Y8 - 0.414, 0.62), (R(90), 0, 0), M_INK, HALL, extrude=0.001)
QM8 = empty('qm8', HALL, loc=(X8, Y8, 1.32))
text3d('qm8t', '?', 0.5, (0, 0, 0), (R(90), 0, 0), M_GILT, QM8, extrude=0.04)
GHOST8, _, _ = bull('bull8', mat('ghost8', (0.9, 0.85, 0.7), 0.5, alpha=0.18), (0, 0, -60), 0.5, HALL, door=False)
wall_sign('sg8', X8, 2.6, 'LOST', 1.0, 0.4, 0.2)
track_spot('e8', X8, (X8, Y8, 0.95), 1000, ang=36)
# ================================================================ moving bits: event times (each pinned to its word; see events.py / events.json)
EV = json.load(open(os.path.join(HERE, 'events.json')))
T_STEAM0, T_FLICK0, T_FLICK1, T_PLQ = EV['STEAM0'], EV['FLICK0'], EV['FLICK1'], EV['PLQ']
T_YEAR1, T_BUST, T_PIN = EV['YEAR1'], EV['BUST'], EV['PIN']
T_SCROLL, T_MODEL, T_HOLLOW, T_DOOR = EV['SCROLL'], EV['MODEL'], EV['HOLLOW'], EV['DOOR']
T_SHUT, T_LOCK, T_FIRE = EV['SHUT'], EV['LOCK'], EV['FIRE']
T_PIPES, T_RINGS, T_MOO = EV['PIPES'], EV['RINGS'], EV['MOO']
T_DISG, T_INV, T_TEST = EV['DISG'], EV['INV'], EV['TEST']
T_ROSE, T_KINGIN, T_SHUT6 = EV['ROSE'], EV['KINGIN'], EV['SHUT6']
T_QMARK, T_BOOK, T_TL0, T_TL1, T_MADEUP = EV['QMARK'], EV['BOOK'], EV['TL0'], EV['TL1'], EV['MADEUP']
T_REAL, T_CARRY, T_CARTH = EV['REAL'], EV['CARRY'], EV['CARTH']
T_YEAR10, T_HELM, T_BACK = EV['YEAR10'], EV['HELM'], EV['BACK']
T_WRITER, T_REMIND = EV['WRITER'], EV['REMIND']
T_STATUE, T_RIVER = EV['STATUE'], EV['RIVER']
T_LOST, T_QM13 = EV['LOST'], EV['QM13']
bpy.context.view_layer.update()
def wpos(o, off=(0, 0, 0)): return o.matrix_world @ Vector(off)
# the little board bull's door, in world space: the spot in front of it on the board, and the door's middle
DOOR3_FRONT = wpos(TOK3, (-0.06, -0.62, 0.0)); DOOR3_MID = wpos(TOK3, (-0.06, -0.2, 0.63))
INV3_REST = INV3.location.copy(); KING3_REST = KING3.location.copy()
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
    key(0.0, (X0 + 1.0, 1.75, 1.2), (X0 + 0.15, Y0, 0.95), 28),            # the bull turns on its turntable (we glide round it)
    key(1.7, (X0 + 0.15, 0.95, 1.42), (X0, Y0, 0.92), 28),
    key(B[1] - 0.15, (X0 + 0.12, 1.0, 1.42), (X0, Y0, 0.92), 28),
    key(B[1] + 0.7, (X1 - 0.08, 2.25, 1.55), (X1 - 0.08, 5.3, 1.5), 24),   # Sicily: the year, the ruler's bust, the pin
    key(B[2] - 0.15, (X1 - 0.06, 2.28, 1.55), (X1 - 0.08, 5.3, 1.5), 24),
    key(B[2] + 0.7, (X2, 2.3, 1.62), (X2, 4.6, 1.38), 24),                 # the workshop: the plans, the model drops in
    key(T_DOOR - 0.55, (X2, 2.34, 1.61), (X2, 4.6, 1.38), 24),
    key(T_DOOR - 0.05, (X2 - 0.06, 2.85, 1.25), (X2 - 0.06, 4.0, 1.1), 28),  # in on the door
    key(T_FIRE - 0.45, (X2 - 0.06, 2.88, 1.25), (X2 - 0.06, 4.0, 1.1), 28),
    key(T_FIRE + 0.1, (X2 + 0.05, 2.6, 1.18), (X2 + 0.05, 4.0, 0.85), 26),  # back: the fire underneath
    key(B[4] + 0.15, (X2 + 0.06, 2.63, 1.18), (X2 + 0.05, 4.0, 0.85), 26),
    key(B[4] + 0.75, (X2 + 0.85, 2.9, 1.22), (X2 + 0.45, 4.0, 1.12), 28),   # the head: pipes, sound rings
    key(B[5] - 0.15, (X2 + 0.87, 2.93, 1.22), (X2 + 0.45, 4.0, 1.12), 28),
    key(B[5] + 0.7, (X3 + 0.1, 3.1, 1.44), (X3 + 0.1, 4.13, 0.85), 28),   # the game board
    key(T_ROSE - 0.3, (X3 + 0.11, 3.13, 1.43), (X3 + 0.1, 4.13, 0.85), 28),
    key(T_ROSE + 0.4, (X3 + 0.11, 3.2, 1.39), (X3 + 0.1, 4.13, 0.85), 29),  # a touch closer as the people rise
    key(B[7] - 0.15, (X3 + 0.12, 3.22, 1.38), (X3 + 0.1, 4.13, 0.85), 29),
    key(B[7] + 0.7, (X4 - 0.15, 2.3, 1.6), (X4 - 0.15, 5.0, 1.48), 25),    # the record: ?, the book, 500 years, MADE UP?
    key(B[9] - 0.15, (X4 - 0.13, 2.35, 1.59), (X4 - 0.15, 5.0, 1.48), 25),
    key(B[9] + 0.7, (X5, 2.78, 2.02), (X5, 3.98, 0.84), 23),                # the map: REAL, to Carthage and home
    key(B[11] - 0.15, (X5 + 0.02, 2.81, 2.0), (X5, 3.98, 0.84), 23),
    key(B[11] + 0.65, (X6, 2.5, 1.65), (X6, 5.0, 1.6), 24),                # the Roman writer
    key(B[12] - 0.15, (X6 + 0.02, 2.53, 1.65), (X6, 5.0, 1.6), 24),
    key(B[12] + 0.65, (X7, 2.55, 1.35), (X7, 4.0, 0.55), 24),              # the river statue
    key(B[13] - 0.15, (X7 + 0.02, 2.58, 1.34), (X7, 4.0, 0.55), 24),
    key(B[13] + 0.7, (X8, 2.3, 1.5), (X8, 4.0, 1.15), 24),                 # lost
    key(TOTAL, (X8, 2.6, 1.45), (X8, 4.0, 1.15), 24),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)
FAR = Vector((0, 0, -60))


def drop(t, t_land, rest, h=1.0, fall=0.4):
    """a prop dropped onto a surface: falls h, lands at t_land, two little bounces; None before it appears"""
    if t < t_land - fall: return None, 0.0
    if t < t_land: u = (t - (t_land - fall)) / fall; return rest + Vector((0, 0, h * (1 - u * u))), 1.0 - u
    d = t - t_land; return rest + Vector((0, 0, 0.02 * abs(math.sin(d * 14)) * math.exp(-d * 7))), 0.0


def pop(t, t0, dur=0.25, over=0.3):
    u = clamp((t - t0) / dur, 0, 1); return max(1e-4, u + over * math.sin(math.pi * u)) if u > 0 else 1e-4


def slam(t, t0):
    """stamp scale: 2.4x down to 1 in 0.12 s, a squash wobble after; 1e-4 before"""
    u = clamp((t - t0) / 0.12, 0, 1)
    if u <= 0: return (1e-4,) * 3
    d = t - t0 - 0.12; sq = 0.1 * math.exp(-d * 16) * math.cos(d * 40) if d > 0 else 0.0
    s = 2.4 - 1.4 * u * u; return (s * (1 + sq), s, s * (1 - sq))


def spring(d, amp, k=6.0, w=14.0): return amp * (1 - math.exp(-k * d) * math.cos(w * d)) if d > 0 else 0.0


def door_angle(t, opens, shuts, full=R(-105)):
    """door swing: list of (t, target) open/shut moves; an opening eases with a little overshoot, a shut slams with a bounce"""
    a = 0.0
    for t0, tgt, kind in sorted([(x, full, 'o') for x in opens] + [(x, 0.0, 's') for x in shuts]):
        d = t - t0
        if d <= 0: break
        if kind == 'o': u = clamp(d / 0.35, 0, 1); a = a + (tgt - a) * (sm(u) + 0.12 * math.sin(math.pi * u))
        else:
            u = clamp(d / 0.14, 0, 1); a = a * (1 - u * u)
            if u >= 1: a = R(-7) * math.exp(-(d - 0.14) * 12) * abs(math.sin((d - 0.14) * 30))
    return a


def puff_at(o, p, s):
    o.location = p; o.scale = (s * 1.25, s, s)


NOSE = [Vector(tuple(p_)) for p_ in BULL_NPZ['nose']]
BK_CLOSED = True


def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- lights: a flicker on "cruelest"; the writer's spot comes up; the last spot stutters on "lost"
    fl = 1.0
    if T_FLICK0 < t < T_FLICK1: fl = (1.0, 0.12, 0.9, 0.3, 0.08, 1.0, 0.2, 0.7)[int((t - T_FLICK0) * 11) % 8]
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * fl
    lt6, e6 = SPOTS['e6']; lt6.data.energy = e6 * (0.25 + 0.75 * smooth(T_WRITER - 0.1, T_WRITER + 0.3, t))
    lt8, e8 = SPOTS['e8']; FIRELT2.data.energy = 0.0
    if T_LOST < t < T_LOST + 0.5: lt8.data.energy = e8 * (1.0, 0.3, 0.8, 0.15, 1.0, 0.5)[int((t - T_LOST) * 12) % 6]
    # ---- exhibit 0: the turntable turns; steam from the nose (a big snort on "brazen"); LEGEND swings on its screw
    TT0.rotation_euler = (0, 0, R(-48) + R(24) * t)
    bpy.context.view_layer.update()
    for k, o in enumerate(STEAM0):
        if t > B[2]: o.location = FAR; continue
        nk = NOSE[k % 2]; d = (t + 0.27 * k) % 1.35; big = 1.0 + 1.6 * smooth(T_STEAM0 - 0.05, T_STEAM0 + 0.1, t) * (1 - smooth(T_STEAM0 + 0.6, T_STEAM0 + 1.4, t))
        p = wpos(BULL0, nk + Vector((0.03 + 0.22 * d * big, 0.03 * (k % 2 * 2 - 1) * d, -0.04 * d + 0.12 * d * d)))
        puff_at(o, p, (0.02 + 0.045 * d) * (1 - d / 1.35) ** 0.5 * big * 1.22)
    PLQ0.rotation_euler = (0, spring(t - T_PLQ, R(-22)), 0)
    # ---- exhibit 1: 570 BC; the ruler's bust rises; the pin drops onto Akragas
    YEAR1.scale = (pop(t, T_YEAR1, 0.25, 0.25),) * 3
    u = smooth(T_BUST - 0.25, T_BUST + 0.2, t); BUSTUP.location = BUSTUP_REST + Vector((0, 0, -0.7 * (1 - u) + 0.02 * math.sin(math.pi * u)))
    BUSTUP.scale = (max(1e-4, min(1.0, u * 3)),) * 3
    d = t - T_PIN
    if d < -0.3: PIN1.location = PIN1_REST + Vector((0, -0.8, 0.4)); PIN1.scale = (1e-4,) * 3
    else:
        PIN1.scale = (1, 1, 1); u = clamp((d + 0.3) / 0.3, 0, 1); PIN1.location = PIN1_REST + Vector((0, -0.8 * (1 - u * u), 0.4 * (1 - u)))
        if d > 0: PIN1.location = PIN1_REST + Vector((0, 0.006 * math.exp(-d * 9) * math.sin(d * 40), 0))
    # ---- exhibit 2: the plans unroll; the model bull drops on its stand; the door creaks, swings open; slams; padlock; fire; pipes, rings
    u = smooth(T_SCROLL, T_SCROLL + 0.55, t); SCRL2.scale = (1, 1, max(1e-4, u))
    p_, w_ = drop(t, T_MODEL, MODEL2_REST, 0.8, 0.36)
    MODEL2.location = p_ if p_ is not None else FAR; MODEL2.rotation_euler = (R(4) * w_, R(-3) * w_, R(12) * w_)
    a_ = door_angle(t, [T_DOOR], [T_SHUT])
    if T_HOLLOW < t < T_SHUT: a_ = min(a_, R(-12) * smooth(T_HOLLOW, T_HOLLOW + 0.4, t) * (1 + 0.15 * math.sin((t - T_HOLLOW) * 18) * math.exp(-(t - T_HOLLOW) * 4)))
    DH2.rotation_euler = (0, 0, a_); HOLE2.hide_render = abs(a_) < R(1.5)
    LOCK2.scale = (pop(t, T_LOCK, 0.18, 0.4),) * 3
    fi = fire_step(FIRE2, t, T_FIRE); FIRELT2.data.energy = 22.0 * fi * (0.7 + 0.3 * math.sin(t * 19) * wob(t, 6, 2.0))
    for k, pp in enumerate(PIPES2): pp.scale = (pop(t, T_PIPES + 0.08 * k, 0.22, 0.35),) * 3
    bpy.context.view_layer.update()
    for k, o in enumerate(RINGS2):
        d = t - T_RINGS - 0.22 * k
        if d < 0 or d > 1.1 or t > B[5] + 0.3: o.location = FAR; continue
        nk = NOSE[k % 2]; o.location = wpos(MODEL2, nk + Vector((0.12 + 0.55 * d, 0.0, 0.0)))
        r_ = (0.025 + 0.09 * d) * MODEL_S * 1.6; o.scale = (r_, r_, r_ * 0.5); o['fade'] = 1.0 - d / 1.1
        o.rotation_euler = (0, R(90), 0)
    for k, o in enumerate(STEAM2):
        if t < T_FIRE + 0.3 or t > B[5] + 0.3: o.location = FAR; continue
        nk = NOSE[k % 2]; d = (t - T_FIRE + 0.33 * k) % 1.6
        puff_at(o, wpos(MODEL2, nk + Vector((0.08 + 0.3 * d, 0, 0.1 * d * d))), (0.012 + 0.035 * d) * (1 - d / 1.6) ** 0.5)
    # ---- exhibit 3: the king shakes; the inventor pawn is pushed into the little bull; the people rise up; the king goes in
    sh = 0.0
    if T_DISG < t < T_DISG + 0.7: d = t - T_DISG; sh = R(12) * math.sin(d * 30) * math.sin(math.pi * d / 0.7)
    d6 = t - T_KINGIN
    if d6 < -0.2: KING3.location = KING3_REST; KING3.rotation_euler = (0, sh, 0); KING3.scale = (1.15,) * 3
    elif d6 < 0.3:
        u = sm(clamp((d6 + 0.2) / 0.5, 0, 1)); KING3.location = KING3_REST.lerp(DOOR3_FRONT, u) + Vector((0, 0, 0.06 * math.sin(math.pi * u))); KING3.scale = (1.15,) * 3
    else:
        u = clamp((d6 - 0.3) / 0.25, 0, 1); KING3.location = DOOR3_FRONT.lerp(DOOR3_MID - Vector((0, 0, 0.03)), sm(u)); KING3.scale = (max(1e-4, 1.15 * (1 - u)),) * 3
    d5 = t - T_INV
    if d5 < 0: INV3.location = INV3_REST; INV3.scale = (1, 1, 1)
    elif d5 < 0.32: u = sm(d5 / 0.32); INV3.location = INV3_REST.lerp(DOOR3_FRONT, u) + Vector((0, 0, 0.05 * math.sin(math.pi * u))); INV3.scale = (1, 1, 1)
    else:
        u = clamp((t - T_TEST) / 0.25, 0, 1); INV3.location = DOOR3_FRONT.lerp(DOOR3_MID - Vector((0, 0, 0.03)), sm(u)); INV3.scale = (max(1e-4, 1 - u),) * 3
    a3 = door_angle(t, [T_INV - 0.15, T_KINGIN - 0.2], [T_TEST + 0.3, T_SHUT6 + 0.12])
    DH3.rotation_euler = (0, 0, a3); HOLE3.hide_render = abs(a3) < R(1.5)
    for k, (o, p0) in enumerate(CROWD3):
        s = pop(t, T_ROSE + 0.05 * k, 0.22, 0.35); o.scale = (s * 0.92,) * 3
        push = smooth(T_KINGIN - 0.3, T_KINGIN + 0.3, t) * 0.05
        o.location = p0 + (KING3_REST - p0).normalized() * push + Vector((0, 0, 0.03 * max(0, math.sin(math.pi * clamp((t - T_ROSE - 0.05 * k) / 0.3, 0, 1)))))
    # ---- exhibit 4: ? pops; the book opens; the 500-year line grows; MADE UP?
    QM4.scale = (pop(t, T_QMARK, 0.25, 0.3),) * 3; QM4.rotation_euler = (0, 0, R(8) * math.sin(t * 2.2))
    e = smooth(T_BOOK, T_BOOK + 0.55, t)
    for pv, s_ in PG4:
        if s_ > 0: pv.rotation_euler = (0, -R(178) * (1 - e), 0); pv.location.z = 0.012 + 0.026 * (1 - e)
    TLBAR.scale = (max(1e-4, smooth(T_TL0, T_TL1 + 0.2, t)), 1, 1)
    TLTXT.scale = (pop(t, T_TL1 + 0.15, 0.25, 0.3),) * 3
    STAMP4.scale = slam(t, T_MADEUP)
    # ---- exhibit 5: REAL; CARTHAGE and 406 BC; the token rides to Carthage; 146 BC, the helmet drops; it rides home
    REAL5.scale = slam(t, T_REAL)
    CARLBL5.scale = (pop(t, T_CARTH, 0.22, 0.3),) * 3; CARD5A.scale = (pop(t, T_CARTH + 0.1, 0.22, 0.3),) * 3
    CARD5B.scale = (pop(t, T_YEAR10, 0.22, 0.3),) * 3
    u1 = sm(clamp((t - T_CARRY) / 1.1, 0, 1)); u2 = sm(clamp((t - T_BACK) / 1.0, 0, 1))
    if t < T_BACK: u = u1; mv = 0 < t - T_CARRY < 1.1
    else: u = 1 - u2; mv = 0 < t - T_BACK < 1.0
    p_ = arc5(u); hop = 0.012 * abs(math.sin(t * 22)) if mv else 0.0
    du = 0.02; dv = arc5(min(1, u + du)) - arc5(max(0, u - du))
    if t >= T_BACK: dv = -dv
    rz = math.atan2(dv.y, dv.x) if dv.length > 1e-6 else math.atan2(-0.22, -0.42)
    if t < T_CARRY: rz = math.atan2(-0.22, -0.42)
    TOK5.location = p_ + Vector((0, 0, hop)); TOK5.rotation_euler = (0, 0, rz)
    p_, w_ = drop(t, T_HELM, HELM5_REST, 0.7, 0.32)
    HELM5.location = p_ if p_ is not None else FAR; HELM5.rotation_euler = (R(25) * w_, R(-15) * w_, R(-20) + R(60) * w_)
    # ---- exhibit 6: the scroll unrolls
    u = smooth(T_REMIND - 0.1, T_REMIND + 0.5, t); SCRL6.scale = (1, 1, max(1e-4, u)); ROLL6.location.z = 2.2 - 0.8 * u
    # ---- exhibit 7: the statue drops onto its rock with a splash; the water starts to run, ripples spread
    p_, w_ = drop(t, T_STATUE, STAT7_REST, 0.9, 0.36)
    STAT7.location = p_ if p_ is not None else FAR; STAT7.rotation_euler = (0, 0, R(-18) + R(10) * w_)
    WATER_MAP.inputs['Location'].default_value = (0.04 * t + 0.9 * max(0.0, t - T_RIVER) * smooth(T_RIVER, T_RIVER + 0.5, t), 0.02 * t, 0.15 * t)
    for k, o in enumerate(RIPS7):
        t0 = (T_STATUE if k < 2 else T_RIVER + 0.25 * (k - 2)); d = t - t0 - 0.12 * (k % 2)
        if d < 0 or d > 1.4: o.location = FAR; continue
        c_ = Vector((X7 + (0.0 if k < 2 else -0.45 + 0.3 * (k - 2)), Y7 + (0.0 if k < 2 else 0.12 * ((k % 2) * 2 - 1)), 0.292))
        o.location = c_; r_ = 0.12 + 0.35 * d; o.scale = (r_, r_ * 0.85, 1)
    for k, o in enumerate(SPL7):
        d = t - T_STATUE
        if not 0 < d < 0.7: o.location = FAR; continue
        a_ = 2 * math.pi * k / len(SPL7); v = Vector((math.cos(a_) * 0.6, math.sin(a_) * 0.35, 1.4))
        p = Vector((X7, Y7, 0.31)) + Vector((v.x * d, v.y * d, v.z * d - 4.9 * d * d))
        if p.z < 0.28: o.location = FAR; continue
        puff_at(o, p, 0.018 * (1 - d / 0.7) + 0.004)
    # ---- exhibit 8: a ghost of the bull shows on the empty plinth and fades; the ? pops
    g = smooth(T_LOST - 0.05, T_LOST + 0.25, t) * (1 - smooth(T_LOST + 0.9, T_LOST + 1.5, t))
    if g < 0.01: GHOST8.location = FAR
    else: GHOST8.location = (X8 - 0.03, Y8, 0.942); GHOST8.rotation_euler = (0, 0, R(-20))
    bpy.data.materials['ghost8'].node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.3 * g
    QM8.scale = (pop(t, T_QM13, 0.25, 0.35),) * 3; QM8.rotation_euler = (0, 0, R(10) * math.sin(t * 2.0))
    # ---- camera, with a nod on each thud
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.005, 1.0, 1.3)
    for tn, a_ in ((T_MODEL, 0.008), (T_SHUT, 0.01), (T_TEST + 0.3, 0.006), (T_SHUT6 + 0.12, 0.008), (T_MADEUP, 0.008), (T_REAL, 0.008), (T_HELM, 0.008), (T_STATUE, 0.01)):
        if t > tn: cp = cp + shake(t, a_, 4.0, 13.0) * math.exp(-(t - tn) * 6.0)
    look(cp, ct, lens, 8.0)
    bpy.context.view_layer.update()
# ================================================================ CAMCHECK=1: fly the camera through every frame and report any frame where it comes within 6 cm of a prop's box
if os.environ.get('CAMCHECK'):
    N_ = int(round(TOTAL * FPS)); skip = ('hfloor', 'hback', 'hfront', 'hleft', 'hright', 'hceil', 'hwains', 'hrail', 'rail')
    hits = {}
    for f in range(N_):
        frame(f); cp = CAM.matrix_world.translation
        for o in S.objects:
            if o.type not in ('MESH', 'FONT') or o.name in skip or o.name.startswith('beam') or o.hide_render: continue
            if o.matrix_world.translation.z < -20: continue
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))); hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
            if all(lo[i] - 0.06 < cp[i] < hi[i] + 0.06 for i in range(3)): hits.setdefault(o.name, []).append(f)
    for k_, v_ in hits.items(): print('CAMHIT', k_, v_[0], v_[-1], len(v_))
    print('CAMCHECK done', len(hits)); sys.exit(0)
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

