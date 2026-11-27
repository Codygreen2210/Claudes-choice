# The Hope Diamond's real story, as a museum walk: the necklace rises in its case (lights flicker, the glass cracks: "cursed");
# a rough stone from India is cut into the French Blue for King Louis XIV; the 1792 crown-jewel theft (the case is emptied, it vanishes);
# a smaller blue diamond turns up in London and a scan outline of the French Blue fits round it; a catalog and the HOPE nameplate;
# curse newspapers get a MADE UP stamp, the jeweler's counter sells it; the twist - mailed in a plain package in 1958; it glows red. One shot.
#   python3 hope3d.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]
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

# ================================================================ props: cut gems, necklace, cloth, dress forms
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
    return o


def cloth_mat(name, c, rough=0.85, sheen=0.5, weave=180.0, seed=0.0):
    """wool / velvet / linen: base colour with a fine weave bump and a little colour drift"""
    m = mat(name, c, rough, sheen=sheen); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed, seed * 0.7, seed * 0.3); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 6.0, 4.0)
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', big, 0.5), c, tuple(x * 0.7 for x in c)), b.inputs['Base Color'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = weave; wv.inputs['Distortion'].default_value = 2.0; nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(math_(nt, 'ADD', wv.outputs['Fac'], tnoise(nt, mp.outputs['Vector'], 90.0, 3.0)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def gem_mat(name, col, emit_col=None, glow_col=(1.0, 0.28, 0.05)):
    """a cut gem: clear, high-IOR, tinted; a faint emission of its own colour so it reads in a dim case; object property 'glow'
    (0..1) mixes in a red-orange emission (the Hope's phosphorescence)"""
    m = mat(name, col, 0.0, trans=1.0, ior=2.42); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = 0.8
    ec = emit_col or tuple(c * 0.9 for c in col)
    g = objattr(nt, 'glow'); c_ = mixc(nt, math_(nt, 'POWER', g, 0.4), ec, glow_col)
    nt.links.new(c_, b.inputs['Emission Color'])
    nt.links.new(math_(nt, 'ADD', 0.35, math_(nt, 'MULTIPLY', g, 7.0)), b.inputs['Emission Strength'])
    return m


def gem_mesh(name, rfn, rx, ry, n=16, table=0.56, crown=0.17, pav=0.44, girdle=0.015):
    """a faceted stone, table up (+z), girdle at z = 0. rfn(theta) shapes the outline (1 = round); sizes in metres (rx, ry = half width).
    Rings are offset half a step from each other and split into triangles so the flat shading reads as facets."""
    D = 2 * max(rx, ry); vs = []; rings = []
    def ring(rr, z, off):
        idx = []
        for k in range(n):
            th = 2 * math.pi * (k + off) / n; r_ = rfn(th) * rr
            idx.append(len(vs)); vs.append((rx * r_ * math.cos(th), ry * r_ * math.sin(th), z))
        return idx
    culet = len(vs); vs.append((0, 0, -pav * D))
    rings.append(ring(0.52, -pav * D * 0.5, 0.5))
    rings.append(ring(1.0, -girdle * D, 0.0)); rings.append(ring(1.0, girdle * D, 0.0))
    rings.append(ring(0.8, crown * D * 0.55, 0.5)); rings.append(ring(table, crown * D, 0.0))
    fs = [(culet, rings[0][(k + 1) % n], rings[0][k]) for k in range(n)]
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(n):
            k2 = (k + 1) % n; fs.append((a_[k], a_[k2], b_[k])); fs.append((a_[k2], b_[k2], b_[k]))
    fs.append(tuple(rings[-1]))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.validate(); me.update()
    for p_ in me.polygons: p_.use_smooth = False
    return me


ROUND = lambda th: 1.0
def CUSHION(th, p=3.2):
    c, s = abs(math.cos(th)), abs(math.sin(th)); return 1.0 / (c ** p + s ** p) ** (1.0 / p) * 0.93
def SHIELD(th): return 1.0 + 0.13 * math.cos(3 * (th + math.pi / 2))     # a rounded triangle, point down (-y in the mesh)


def gem_obj(name, me, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), glow=0.0):
    o = obj(name, me, None, loc, parent); o.data = me
    if not me.materials: me.materials.append(m)
    o.rotation_euler = rot; o['glow'] = glow; return o


def rough_stone(name, m, r, parent=None, loc=(0, 0, 0), seed=3):
    """an uncut crystal: a lumpy octahedron-ish blob, flat shaded"""
    gr = random.Random(seed); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    for v in bm.verts:
        d = v.co.normalized(); oct_ = 1.0 / (abs(d.x) + abs(d.y) + abs(d.z)) * 1.35
        v.co = d * r * (0.55 * oct_ + 0.45) * gr.uniform(0.85, 1.12); v.co.z *= 0.8
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = False
    o = obj(name, me, m, loc, parent); o['glow'] = 0.0; return o


def necklace(name, parent, m_hope, m_white, m_plat, hope_me, small_me, loc=(0, 0, 0)):
    """the Hope necklace laid on a display board: the board's face is the local x-z plane, facing -y.
    A loop of white diamonds, a pendant of sixteen white diamonds round the blue stone. Returns (root, hope object)."""
    root = empty(name, parent, loc=loc)
    n = 34
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n; x = 0.15 * math.sin(a); z = 0.1 + 0.19 * math.cos(a)
        gem_obj(f'{name}_l{k}', small_me, m_white, root, loc=(x, -0.006, z), rot=(R(90), 0, a))
        tube(f'{name}_lk{k}', [(x, -0.002, z), (0.15 * math.sin(a + math.pi / n), -0.002, 0.1 + 0.19 * math.cos(a + math.pi / n))], 0.0022, m_plat, root, seg=6)
    PZ = -0.165
    tube(f'{name}_bail', [(0, -0.004, -0.092), (0, -0.006, -0.11)], 0.006, m_plat, root, seg=8)
    rim = lathe(f'{name}_rim', [(0.043, -0.004), (0.05, -0.004), (0.05, 0.004), (0.043, 0.004)], 32, m_plat, root, loc=(0, -0.006, PZ)); rim.rotation_euler = (R(90), 0, 0)
    rim.scale = (1.0, 0.86, 1.0)
    for k in range(16):
        a = 2 * math.pi * k / 16; gem_obj(f'{name}_p{k}', small_me, m_white, root, loc=(0.064 * math.cos(a), -0.007, PZ + 0.056 * math.sin(a)), rot=(R(90), 0, a))
    hope = gem_obj(f'{name}_hope', hope_me, m_hope, root, loc=(0, -0.008, PZ), rot=(R(90), 0, 0))
    return root, hope


def dress_form(name, parent, loc, head=True, h=1.0, m=None):
    """a museum dress form on a pole: torso (shoulders at about 1.5), neck, head"""
    md = m or M_DUMMY; f_ = empty(name, parent, loc=loc)
    lathe(f'{name}_base', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.03), (0.03, 0.05), (0.025, 0.85), (0.0, 0.85)], 20, M_BLACK, f_)
    lathe(f'{name}_torso', [(0.0, 0.85), (0.13, 0.86), (0.155, 0.95), (0.135, 1.12), (0.16, 1.30), (0.19, 1.42), (0.12, 1.50), (0.05, 1.53), (0.0, 1.53)], 28, md, f_).scale = (1.0, 0.68, 1.0)
    if head:
        lathe(f'{name}_neck', [(0.0, 1.5), (0.045, 1.5), (0.04, 1.62), (0.0, 1.62)], 16, md, f_)
        prim('uv_sphere', f'{name}_head', md, f_, loc=(0, 0, 1.72), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
    return f_


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


def rest_on(o, top, gap=0.001):
    """move o (keeping x, y and its rotation) so its lowest world point sits on height top"""
    bpy.context.view_layer.update(); dg = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = dg.to_mesh()
    z = min((o.matrix_world @ v.co).z for v in me.vertices); dg.to_mesh_clear()
    for c in o.children_recursive:
        if c.type != 'MESH': continue
        dc = c.evaluated_get(bpy.context.evaluated_depsgraph_get()); mc = dc.to_mesh(); z = min(z, min((c.matrix_world @ v.co).z for v in mc.vertices)); dc.to_mesh_clear()
    o.location.z += top - z + gap; return o.location.copy()

# ================================================================ set: a museum hall (x -4..26), the Hope's story in exhibits along the back wall
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
M_WAINS = noisy(mat('wains', (0.06, 0.07, 0.12), 0.45, coat=0.3), 20.0, 0.15)
M_CEIL = noisy(mat('ceil', (0.30, 0.29, 0.27), 0.9), 2.0, 0.1)
M_BRASS = mat('brass', (0.78, 0.55, 0.22), 0.28, 1.0)
M_WOOD = noisy(mat('wood', (0.26, 0.14, 0.065), 0.55, coat=0.15), 14.0, 0.3)
M_WOODDK = noisy(mat('wooddk', (0.08, 0.045, 0.025), 0.5, coat=0.12), 14.0, 0.3)
M_PAPER = noisy(mat('paper', (0.80, 0.74, 0.60), 0.8), 8.0, 0.08)
M_NEWS = noisy(mat('news', (0.78, 0.76, 0.70), 0.85), 10.0, 0.1)
M_INK = mat('ink', (0.01, 0.01, 0.012), 0.3); M_GREY = mat('greyink', (0.22, 0.22, 0.22), 0.6)
M_GOLD = mat('gold', (0.85, 0.62, 0.25), 0.25, 1.0); M_PLAT = mat('plat', (0.80, 0.80, 0.82), 0.15, 1.0)
M_PLAQ = mat('plaq', (0.06, 0.05, 0.045), 0.5); M_GILT = mat('gilt', (0.9, 0.7, 0.32), 0.3, 1.0)
M_BLACK = mat('blackm', (0.02, 0.02, 0.02), 0.6)
M_GLASS = mat('glass', (0.92, 0.96, 1.0), 0.02, trans=1.0, ior=1.45)
M_RED = mat('red', (0.55, 0.04, 0.04), 0.6); M_WHITE = mat('white', (0.85, 0.84, 0.80), 0.6)
M_STAMP = mat('stamp', (0.75, 0.04, 0.03), 0.6)
M_DUMMY = noisy(mat('dummy', (0.42, 0.40, 0.37), 0.7, sheen=0.3), 6.0, 0.15)
M_NAVYV = cloth_mat('navyv', (0.012, 0.016, 0.05), 0.8, 0.8, 140.0, 2.0)
M_REDV = cloth_mat('redv', (0.30, 0.015, 0.025), 0.8, 0.8, 120.0, 4.0)
M_ROYAL = cloth_mat('royal', (0.02, 0.05, 0.28), 0.8, 0.5, 120.0, 5.0)
M_CORK = noisy(mat('cork', (0.40, 0.27, 0.15), 0.9), 60.0, 0.35)
M_KRAFT = noisy(mat('kraft', (0.45, 0.30, 0.16), 0.85), 18.0, 0.2)
M_STRING = mat('string', (0.75, 0.68, 0.52), 0.8)
M_UNIF = cloth_mat('unif', (0.10, 0.14, 0.24), 0.85, 0.4, 150.0, 6.0)
M_LEATHER = noisy(mat('leather', (0.16, 0.08, 0.035), 0.45, coat=0.2), 40.0, 0.2)
M_STEEL = mat('steel', (0.6, 0.61, 0.63), 0.25, 1.0)
M_YELLOW = mat('yellow', (0.85, 0.62, 0.03), 0.5)
M_HOPE = gem_mat('hope', (0.05, 0.16, 0.85), (0.08, 0.22, 1.0), glow_col=(1.0, 0.1, 0.02))
M_WHITE_D = gem_mat('whited', (0.95, 0.97, 1.0), (0.9, 0.92, 1.0))
M_ROUGH = mat('roughst', (0.10, 0.14, 0.55), 0.45, trans=0.7, ior=2.42); M_ROUGH.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (0.1, 0.12, 0.6, 1)
M_ROUGH.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.4
M_SPINEL = gem_mat('spinel', (0.8, 0.04, 0.06)); M_EMER = gem_mat('emer', (0.04, 0.6, 0.15))
M_GHOST = emis('ghost', (0.2, 0.9, 1.0), 6.0)
M_CHECK = emis('check', (0.15, 1.0, 0.25), 5.0)
M_SPARK = emis('spark', (1.0, 0.7, 0.3), 30.0)
M_UVTUBE = emis('uvtube', (0.45, 0.15, 1.0), 12.0)

HOPE_ME = gem_mesh('hope_me', CUSHION, 0.0425, 0.036, n=16)
SMALL_ME = gem_mesh('small_me', ROUND, 0.0075, 0.0075, n=8)
FB_ME = gem_mesh('fb_me', SHIELD, 0.088, 0.08, n=18)
GHOST_ME = gem_mesh('ghost_me', SHIELD, 0.088, 0.08, n=18)
HOPEB_ME = gem_mesh('hopeb_me', CUSHION, 0.068, 0.058, n=16)

# ---------------------------------------------------------------- the museum hall
HALL = empty('hall')
box('hfloor', (30.8, 13.0, 0.2), (11.0, -0.9, -0.1), M_WOODF, parent=HALL)
box('hback', (30.8, 0.3, 6.0), (11.0, 5.55, 3.0), M_PLASTER, parent=HALL)
box('hwains', (30.8, 0.06, 1.0), (11.0, 5.38, 0.5), M_WAINS, bv=0.01, parent=HALL)
box('hrail', (30.8, 0.08, 0.05), (11.0, 5.36, 1.02), M_GILT, parent=HALL)
box('hfront', (30.8, 0.3, 6.0), (11.0, -7.55, 3.0), M_PLASTER, parent=HALL)
box('hleft', (0.3, 13.0, 6.0), (-4.35, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hright', (0.3, 13.0, 6.0), (26.35, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hceil', (30.8, 13.4, 0.3), (11.0, -0.9, 6.15), M_CEIL, parent=HALL)
for xb in range(-3, 27, 3): box(f'beam{xb}', (0.3, 13.0, 0.35), (xb + 0.5, -0.9, 5.83), M_WOOD, bv=0.01, parent=HALL)
RAIL = box('rail', (30.0, 0.08, 0.06), (11.0, 0.4, 5.55), M_BLACK, parent=HALL)
MUSEUM_LIGHTS = []                                  # (light, base energy)
SPOTS = {}
def track_spot(key_, x, target, e=900, size=0.12, ang=46):
    p = Vector((x, 0.4, 5.45)); can = prim('cylinder', f'can{key_}', M_BLACK, HALL, loc=p, vertices=16, radius=0.07, depth=0.22)
    can.rotation_mode = 'QUATERNION'; can.rotation_quaternion = (Vector(target) - p).to_track_quat('-Z', 'Y')
    lt = light_at(f'spot{key_}', 'SPOT', p, target, e, (1.0, 0.92, 0.80), size); lt.data.spot_size = R(ang); lt.data.spot_blend = 0.6
    MUSEUM_LIGHTS.append((lt, e)); SPOTS[key_] = (lt, e); return lt
for k, xa in enumerate((1.5, 8.5, 15.5, 22.5)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 330, (1.0, 0.93, 0.84), 3.0), 330))
G = random.Random(7)


def wall_sign(name, x, z, body, w=1.6, h=0.42, size=0.2, m_bg=None, m_txt=None):
    P_ = empty(name, HALL, loc=(x, 5.37, z))
    box(name + 'b', (w, 0.02, h), (0, 0, 0), m_bg or M_PLAQ, bv=0.006, parent=P_)
    box(name + 'f', (w + 0.05, 0.016, h + 0.05), (0, 0.006, 0), M_GILT, bv=0.006, parent=P_)
    text3d(name + 't', body, size, (0, -0.012, 0), (R(90), 0, 0), m_txt or M_GILT, P_, extrude=0.003); return P_


PLAT_Z = 0.12
M_PLAT = noisy(mat('platm', (0.10, 0.06, 0.04), 0.5, coat=0.2), 10.0, 0.2)
def platform(x, w, d=1.5, y=4.15):
    box(f'plat{x}', (w, d, PLAT_Z), (x, y, PLAT_Z / 2), M_PLAT, bv=0.01, parent=HALL)


def glass_case(name, x, y, w=0.62, d=0.56, z0=1.0, h=0.66):
    """a pedestal and a glass case on it: four panes, a lid and brass corner posts. Returns (root, front pane z range)"""
    rt = empty(name, HALL, loc=(x, y, 0))
    box(f'{name}_ped', (w + 0.08, d + 0.08, z0), (0, 0, z0 / 2), M_WOODDK, bv=0.012, parent=rt)
    box(f'{name}_pedt', (w + 0.12, d + 0.12, 0.03), (0, 0, z0 - 0.015), M_GILT, bv=0.006, parent=rt)
    box(f'{name}_slot', (0.54, 0.24, 0.004), (0, 0.02, z0 + 0.002), M_NAVYV, parent=rt)
    t_ = 0.008
    box(f'{name}_gf', (w, t_, h), (0, -d / 2, z0 + h / 2), M_GLASS, parent=rt)
    box(f'{name}_gb', (w, t_, h), (0, d / 2, z0 + h / 2), M_GLASS, parent=rt)
    for s_ in (-1, 1): box(f'{name}_gs{s_}', (t_, d, h), (s_ * w / 2, 0, z0 + h / 2), M_GLASS, parent=rt)
    box(f'{name}_gt', (w, d, t_), (0, 0, z0 + h), M_GLASS, parent=rt)
    for sx in (-1, 1):
        for sy in (-1, 1): box(f'{name}_post{sx}{sy}', (0.014, 0.014, h), (sx * w / 2, sy * d / 2, z0 + h / 2), M_BRASS, parent=rt)
    for sy in (-1, 1): box(f'{name}_tr{sy}', (w, 0.014, 0.014), (0, sy * d / 2, z0 + h), M_BRASS, parent=rt)
    for sx in (-1, 1): box(f'{name}_tr{sx}x', (0.014, d, 0.014), (sx * w / 2, 0, z0 + h), M_BRASS, parent=rt)
    return rt


def display_board(name, parent, loc, tilt=R(-18), w=0.5, h=0.56):
    """an angled navy velvet board with the necklace on it; the root's local x-z plane is the board face (facing -y)"""
    bd = empty(name, parent, loc=loc); bd.rotation_euler = (tilt, 0, 0)
    box(f'{name}_v', (w, 0.03, h), (0, 0.015, 0.03), M_NAVYV, bv=0.01, parent=bd)
    tube(f'{name}_leg', [(0, 0.05, -0.25), (0, 0.16, -0.32)], 0.012, M_BRASS, bd, seg=8)
    return bd


# ================================================================ exhibit 0: the Hope Diamond in its case (x = 0) - it rises, the lights flicker, the glass cracks
X0, Y0 = 0.0, 3.75
CASE0 = glass_case('case0', X0, Y0)
BD0 = display_board('bd0', HALL, (X0, Y0 + 0.02, 1.31))
NK0, HOPE0 = necklace('nk0', BD0, M_HOPE, M_WHITE_D, M_PLAT, HOPE_ME, SMALL_ME)
BD0_REST = BD0.location.copy()
PLQ0 = empty('plq0', HALL, loc=(X0 - 0.13, Y0 - 0.327, 0.78))           # the pedestal plaque hangs from its left screw
box('plq0b', (0.3, 0.012, 0.09), (0.13, 0, 0), M_GILT, bv=0.004, parent=PLQ0)
text3d('plq0t', 'HOPE DIAMOND', 0.032, (0.13, -0.008, 0), (R(90), 0, 0), M_INK, PLQ0, extrude=0.001)
prim('uv_sphere', 'plq0s', M_BRASS, HALL, loc=(X0 - 0.13, Y0 - 0.335, 0.78), segments=8, ring_count=6, radius=0.007)
CRACK = []                                     # a zig-zag crack across the front pane, drawn in segments
cp_ = Vector((X0 + 0.22, Y0 - 0.285, 1.52)); gr_ = random.Random(5)
for k in range(9):
    nxt = cp_ + Vector((-0.055 + gr_.uniform(-0.02, 0.02), 0, -0.035 + gr_.uniform(-0.03, 0.03)))
    CRACK.append(tube(f'crk{k}', [cp_, nxt], 0.0018, M_WHITE, HALL, seg=5, caps=True)); cp_ = nxt
    if k == 3: br_ = cp_.copy()
CRACK.append(tube('crkb', [br_, br_ + Vector((0.03, 0, -0.07))], 0.0016, M_WHITE, HALL, seg=5))
for o in CRACK: o.hide_render = True
track_spot('e0', X0, (X0, Y0, 1.2), 1000, ang=40)
wall_sign('sg0', X0, 2.75, 'THE HOPE DIAMOND', 2.2, 0.42, 0.17)

# ================================================================ exhibit 1: from India to King Louis XIV - a rough stone is cut into the French Blue (x = 3.4)
X1 = 3.4
platform(X1, 2.0)
lathe('col1', [(0.0, PLAT_Z), (0.2, PLAT_Z), (0.2, PLAT_Z + 0.05), (0.09, PLAT_Z + 0.09), (0.08, 0.92), (0.2, 0.95), (0.2, 1.0), (0.0, 1.0)], 32, M_WOODDK, HALL, loc=(X1 - 0.2, 3.85, 0))
CUSH1 = box('cush1', (0.36, 0.36, 0.07), (X1 - 0.2, 3.85, 1.035), M_REDV, bv=0.03, parent=HALL); subsurf(CUSH1, 2)
CUSH1_TOP = 1.06
for sx in (-1, 1):
    for sy in (-1, 1): prim('uv_sphere', f'tass{sx}{sy}', M_GOLD, HALL, loc=(X1 - 0.2 + sx * 0.18, 3.85 + sy * 0.18, 1.035), segments=8, ring_count=6, radius=0.014)
ROUGH = rough_stone('rough', M_ROUGH, 0.095, HALL, loc=(X1 - 0.2, 3.85, CUSH1_TOP + 0.04))
FB1 = gem_obj('fb1', FB_ME, M_HOPE, HALL, loc=(X1 - 0.2, 3.85, CUSH1_TOP + 0.023), rot=(R(-12), 0, 0))
FB1_REST = rest_on(FB1, CUSH1_TOP - 0.004)
ROUGH_REST = rest_on(ROUGH, CUSH1_TOP - 0.006)
# the cutting wheel beside the cushion
WHEEL_C = Vector((X1 + 0.13, 3.85, 1.15))
lathe('whst', [(0.0, PLAT_Z), (0.12, PLAT_Z), (0.12, PLAT_Z + 0.04), (0.03, PLAT_Z + 0.06), (0.025, 1.03), (0.0, 1.03)], 20, M_WOODDK, HALL, loc=(X1 + 0.13, 3.95, 0))
box('whfork', (0.03, 0.03, 0.14), (X1 + 0.13, 3.95, 1.08), M_STEEL, parent=HALL)
tube('whaxle', [(X1 + 0.13, 3.84, 1.15), (X1 + 0.13, 3.96, 1.15)], 0.008, M_STEEL, HALL, seg=8)
WHEEL = empty('wheel', HALL, loc=WHEEL_C)
wl_ = lathe('whd', [(0.0, -0.012), (0.085, -0.012), (0.09, -0.006), (0.09, 0.006), (0.085, 0.012), (0.0, 0.012)], 40, M_STEEL, WHEEL); wl_.rotation_euler = (R(90), 0, 0)
for k in range(6): box(f'whsp{k}', (0.15, 0.004, 0.01), (0, -0.016, 0), M_BRASS, rot=(0, R(30 * k), 0), parent=WHEEL)
prim('cylinder', 'whhub', M_BRASS, WHEEL, loc=(0, -0.018, 0), rot=(R(90), 0, 0), vertices=16, radius=0.022, depth=0.02)
SPARKS = []
gs_ = random.Random(11)
for k in range(28):
    o = prim('uv_sphere', f'spk{k}', M_SPARK, HALL, loc=(0, 0, -50), segments=6, ring_count=4, radius=0.005)
    SPARKS.append((o, gs_.uniform(-1.6, -0.3), gs_.uniform(-0.6, 0.3), gs_.uniform(0.4, 1.6), gs_.uniform(0, 0.55)))
# King Louis XIV: a royal banner unrolls on the wall and a crown lands on a small stand
BAN1 = empty('ban1', HALL, loc=(X1 + 0.2, 5.36, 2.6))
box('ban1c', (1.4, 0.015, 1.05), (0, 0, -0.53), M_ROYAL, parent=BAN1)
box('ban1g', (1.46, 0.012, 1.11), (0, 0.004, -0.53), M_GILT, parent=BAN1)
text3d('ban1t', 'KING\nLOUIS XIV', 0.19, (0, -0.012, -0.5), (R(90), 0, 0), M_GILT, BAN1, extrude=0.004)
prim('cylinder', 'ban1rod', M_GOLD, HALL, loc=(X1 + 0.2, 5.35, 2.61), rot=(0, R(90), 0), vertices=12, radius=0.018, depth=1.65)
box('crst', (0.22, 0.22, 0.62), (X1 + 0.58, 4.25, PLAT_Z + 0.31), M_WOODDK, bv=0.01, parent=HALL)
box('crstv', (0.2, 0.2, 0.03), (X1 + 0.58, 4.25, PLAT_Z + 0.635), M_REDV, bv=0.01, parent=HALL)
def crown(name, r=0.1, h=0.07):
    c_ = empty(name)
    lathe(f'{name}_band', [(r * 0.92, 0.0), (r, 0.0), (r, h), (r * 0.92, h)], 40, M_GOLD, c_)
    for k in range(5):
        a = 2 * math.pi * k / 5; prim('cone', f'{name}_pt{k}', M_GOLD, c_, loc=(r * 0.97 * math.cos(a), r * 0.97 * math.sin(a), h + 0.035), vertices=10, radius1=0.022, radius2=0.004, depth=0.07)
        prim('uv_sphere', f'{name}_pb{k}', M_GOLD, c_, loc=(r * 0.97 * math.cos(a), r * 0.97 * math.sin(a), h + 0.075), segments=8, ring_count=5, radius=0.01)
        prim('ico_sphere', f'{name}_gm{k}', M_SPINEL if k % 2 else M_HOPE, c_, loc=(r * 1.0 * math.cos(a + 0.63), r * 1.0 * math.sin(a + 0.63), h * 0.5), subdivisions=1, radius=0.012)
    prim('uv_sphere', f'{name}_cap', M_REDV, c_, loc=(0, 0, h * 0.6), segments=16, ring_count=8, radius=r * 0.88, scale=(1, 1, 0.75))
    return c_
CROWN1 = crown('crown1'); CROWN1_REST = Vector((X1 + 0.58, 4.25, PLAT_Z + 0.65))
track_spot('e1', X1, (X1, 3.95, 1.0), 950, ang=50)

# ================================================================ exhibit 2: 1792 - the French crown jewels case is emptied by thieves (x = 6.8)
X2 = 6.8
platform(X2, 1.9)
box('tab2', (1.0, 0.6, 0.86), (X2, 3.95, PLAT_Z + 0.43), M_WOODDK, bv=0.012, parent=HALL)
box('tab2v', (0.94, 0.54, 0.02), (X2, 3.95, PLAT_Z + 0.87), M_REDV, parent=HALL)
TOP2 = PLAT_Z + 0.88
LID2 = empty('lid2', HALL, loc=(X2, 3.95 + 0.3, TOP2 + 0.16))                # hinged at the back edge
box('lid2g', (0.98, 0.6, 0.008), (0, -0.3, 0), M_GLASS, parent=LID2)
for sy in (0.0, -0.6): box(f'lid2f{sy}', (1.0, 0.02, 0.02), (0, sy, 0), M_GILT, parent=LID2)
for sx in (-0.5, 0.5): box(f'lid2s{sx}', (0.02, 0.6, 0.02), (sx, -0.3, 0), M_GILT, parent=LID2)
for sx in (-0.5, 0.5):
    for sy in (-0.3, 0.3): box(f'tab2w{sx}{sy}', (0.012, 0.012, 0.16), (X2 + sx, 3.95 + sy, TOP2 + 0.08), M_GILT, parent=HALL)
box('tab2gf', (0.98, 0.006, 0.15), (X2, 3.95 - 0.3, TOP2 + 0.08), M_GLASS, parent=HALL)
for sx in (-1, 1): box(f'tab2gs{sx}', (0.006, 0.58, 0.15), (X2 + sx * 0.49, 3.95, TOP2 + 0.08), M_GLASS, parent=HALL)
box('tab2gb', (0.98, 0.006, 0.15), (X2, 3.95 + 0.3, TOP2 + 0.08), M_GLASS, parent=HALL)
CROWN2 = crown('crown2', 0.075, 0.05); CROWN2.location = (X2 - 0.27, 3.98, TOP2)
JEWELS2 = [CROWN2]
for k, (mm, dx) in enumerate(((M_SPINEL, -0.06), (M_EMER, 0.1), (M_WHITE_D, 0.27))):
    o = gem_obj(f'j2_{k}', gem_mesh(f'j2me{k}', ROUND if k != 0 else SHIELD, 0.042, 0.036, n=12), mm, HALL, loc=(X2 + dx, 3.9 + 0.04 * k, TOP2 + 0.012), rot=(0, 0, 0))
    JEWELS2.append(o)
# the French Blue in its gold setting (the Golden Fleece badge, simplified to a gold frame) at the front
FB2R = empty('fb2r', HALL, loc=(X2 + 0.02, 3.78, TOP2 + 0.013))
lathe('fb2set', [(0.092, -0.006), (0.106, -0.006), (0.106, 0.008), (0.092, 0.008)], 32, M_GOLD, FB2R).scale = (1.0, 0.92, 1.0)
gem_obj('fb2', FB_ME, M_HOPE, FB2R, loc=(0, 0, 0.0), rot=(0, 0, 0))
for k in range(4): prim('uv_sphere', f'fb2b{k}', M_GOLD, FB2R, loc=(0.112 * math.cos(math.pi / 2 * k + 0.78), 0.104 * math.sin(math.pi / 2 * k + 0.78), 0), segments=8, ring_count=5, radius=0.013)
POOF = []
gp_ = random.Random(19)
for k in range(22):
    o = gem_obj(f'poof{k}', SMALL_ME, M_WHITE_D, HALL, loc=(0, 0, -50)); POOF.append((o, Vector((gp_.uniform(-1, 1), gp_.uniform(-1, 1), gp_.uniform(-0.3, 1.2))).normalized() * gp_.uniform(0.25, 0.5), gp_.uniform(0, 6)))
SIGN2 = wall_sign('sg2', X2, 2.4, 'FRENCH CROWN\nJEWELS', 1.5, 0.62, 0.15)
YEAR2 = text3d('yr2', '1792', 0.3, (X2, 5.37, 1.7), (R(90), 0, 0), M_GILT, HALL, extrude=0.012)
STAMP2 = empty('stamp2', SIGN2, loc=(0.05, -0.03, 0.0)); STAMP2.rotation_euler = (0, R(-9), 0)
text3d('stamp2t', 'STOLEN', 0.17, (0, 0, 0), (R(90), 0, 0), M_STAMP, STAMP2, extrude=0.004)
track_spot('e2', X2, (X2, 3.95, 1.0), 950, ang=44)

# ================================================================ exhibit 3: London, twenty years later - a smaller blue diamond; the scan outline of the French Blue fits round it (x = 10.2)
X3 = 10.2
platform(X3, 1.6)
lathe('col3', [(0.0, PLAT_Z), (0.18, PLAT_Z), (0.18, PLAT_Z + 0.05), (0.08, PLAT_Z + 0.09), (0.07, 0.96), (0.17, 0.99), (0.17, 1.03), (0.0, 1.03)], 32, M_WOODDK, HALL, loc=(X3, 3.85, 0))
box('tray3', (0.34, 0.34, 0.025), (X3, 3.85, 1.042), M_NAVYV, bv=0.008, parent=HALL)
TOP3 = 1.055
HOPE3 = gem_obj('hope3', HOPEB_ME, M_HOPE, HALL, loc=(X3, 3.85, TOP3 + 0.016), rot=(0, 0, 0))
HOPE3_REST = rest_on(HOPE3, TOP3 - 0.004)
GHOST = obj('ghost', GHOST_ME, M_GHOST, (X3, 3.85, TOP3 + 0.6), HALL)
wf_ = GHOST.modifiers.new('wf', 'WIREFRAME'); wf_.thickness = 0.0022; wf_.use_replace = True
GHOST.scale = (1e-4,) * 3
CHECK3 = empty('check3', HALL, loc=(X3 + 0.13, 3.7, 1.21))
tube('chk3a', [(-0.045, 0, 0.0), (-0.012, 0, -0.035), (0.055, 0, 0.05)], 0.008, M_CHECK, CHECK3, seg=8)
CHECK3.scale = (1e-4,) * 3
wall_sign('sg3', X3, 1.75, 'LONDON\n1812', 1.0, 0.5, 0.14)
track_spot('e3', X3, (X3, 3.85, 1.05), 950, ang=40)

# ================================================================ exhibit 4: the Hope family - a catalog opens, the HOPE nameplate letters drop in (x = 13.4)
X4 = 13.4
platform(X4, 1.8)
box('lect4', (0.56, 0.42, 1.0), (X4 - 0.28, 3.95, PLAT_Z + 0.5), M_WOODDK, bv=0.01, parent=HALL)
BK4 = empty('bk4', HALL, loc=(X4 - 0.28, 3.95, PLAT_Z + 1.02)); BK4.rotation_euler = (R(22), 0, 0); BK4.scale = (1.55, 1.55, 1.55)
box('bk4sp', (0.02, 0.24, 0.02), (0, 0, 0.0), M_NAVYV, parent=BK4)
PG4 = []
for s_ in (-1, 1):
    pv = empty(f'bk4pv{s_}', BK4, loc=(0, 0, 0.012))
    box(f'bk4c{s_}', (0.2, 0.26, 0.012), (s_ * 0.1, 0, 0), M_NAVYV, bv=0.003, parent=pv)
    box(f'bk4p{s_}', (0.19, 0.25, 0.01), (s_ * 0.1, 0, 0.011), M_PAPER, parent=pv)
    PG4.append((pv, s_))
text3d('bk4t', 'THE HOPE\nCOLLECTION\n1839', 0.022, (-0.1, 0.0, 0.0175), (0, 0, 0), M_INK, PG4[0][0], extrude=0.0005)
gem_obj('bk4gem', HOPE_ME, M_HOPE, PG4[1][0], loc=(0.1, 0.02, 0.035), rot=(0, 0, 0))
for k in range(3): box(f'bk4l{k}', (0.12, 0.006, 0.001), (0.1, -0.06 - 0.022 * k, 0.017), M_GREY, parent=PG4[1][0])
NAME4 = empty('name4', HALL, loc=(X4 + 0.25, 5.36, 1.95))
box('nm4b', (1.4, 0.02, 0.55), (0, 0, 0), M_PLAQ, bv=0.006, parent=NAME4)
box('nm4f', (1.46, 0.016, 0.61), (0, 0.006, 0), M_GILT, bv=0.006, parent=NAME4)
LET4 = [text3d(f'nm4l{k}', ch, 0.36, (-0.42 + 0.28 * k, -0.02, 0.03), (R(90), 0, 0), M_GILT, NAME4, extrude=0.02) for k, ch in enumerate('HOPE')]
LET4_REST = [o.location.copy() for o in LET4]
SUB4 = text3d('nm4s', 'HENRY PHILIP HOPE', 0.06, (0, -0.014, -0.2), (R(90), 0, 0), M_GILT, NAME4, extrude=0.002)
track_spot('e4', X4, (X4, 4.4, 1.5), 950, ang=50)

# ================================================================ exhibit 5: the curse - newspaper scare stories, a MADE UP stamp; the jeweler's counter sells it (x = 16.8)
X5 = 16.8
platform(X5 + 0.55, 1.6)
BOARD5 = empty('board5', HALL, loc=(X5 - 0.45, 5.36, 2.45))
box('bd5', (1.6, 0.03, 1.1), (0, 0, 0), M_CORK, bv=0.01, parent=BOARD5)
box('bd5f', (1.66, 0.025, 1.16), (0, 0.006, 0), M_WOOD, bv=0.01, parent=BOARD5)
NEWS = []
for k, (hd, dx, dz, rz) in enumerate((('CURSED\nGEM!', -0.48, 0.12, 6), ('BAD LUCK\nSTONE', 0.02, -0.08, -5), ('DOOMED\nDIAMOND', 0.5, 0.14, 4))):
    np_ = empty(f'news{k}', BOARD5, loc=(dx, -0.03 - 0.004 * k, dz)); np_.rotation_euler = (0, R(rz), 0)
    box(f'nw{k}', (0.46, 0.004, 0.6), (0, 0, 0), M_NEWS, parent=np_)
    text3d(f'nwh{k}', hd, 0.07, (0, -0.004, 0.17), (R(90), 0, 0), M_INK, np_, extrude=0.0008)
    box(f'nwr{k}', (0.42, 0.003, 0.006), (0, -0.003, 0.27), M_INK, parent=np_)
    for j in range(7):
        for c in range(2): box(f'nwl{k}{j}{c}', (0.18, 0.002, 0.012), (-0.105 + 0.21 * c, -0.003, -0.02 - 0.035 * j), M_GREY, parent=np_)
    NEWS.append((np_, np_.location.copy(), np_.rotation_euler.copy()))
STAMP5 = empty('stamp5', BOARD5, loc=(0.0, -0.06, 0.0)); STAMP5.rotation_euler = (0, R(-12), 0)
text3d('stamp5t', 'MADE UP', 0.24, (0, 0, 0), (R(90), 0, 0), M_STAMP, STAMP5, extrude=0.005)
box('stamp5b', (1.05, 0.003, 0.3), (0, 0.004, 0), M_STAMP, parent=STAMP5).hide_render = True
# the jeweler's counter: a glass-topped wooden counter; the necklace on its board; a SOLD tag, a little heap of gold coins
CX5 = X5 + 0.55
box('ctr5', (1.2, 0.55, 0.82), (CX5, 4.0, PLAT_Z + 0.41), M_WOODDK, bv=0.012, parent=HALL)
box('ctr5t', (1.24, 0.59, 0.03), (CX5, 4.0, PLAT_Z + 0.835), M_WOODDK, bv=0.006, parent=HALL)
TOP5 = PLAT_Z + 0.85
BD5 = display_board('bd5n', HALL, (CX5 - 0.15, 4.08, TOP5 + 0.33), tilt=R(-16))
NK5, HOPE5 = necklace('nk5', BD5, M_HOPE, M_WHITE_D, M_PLAT, HOPE_ME, SMALL_ME)
wall_sign('sg5', CX5 + 0.1, 2.75, 'PARIS\n1910', 0.9, 0.5, 0.14)
TAG5 = empty('tag5', HALL, loc=(CX5 + 0.2, 3.95, TOP5 + 0.3))
tube('tag5s', [(0, 0, 0), (0.0, 0, -0.12)], 0.0015, M_STRING, TAG5, seg=5)
box('tag5b', (0.22, 0.004, 0.12), (0, 0, -0.18), M_PAPER, bv=0.004, parent=TAG5)
text3d('tag5t', 'SOLD', 0.065, (0, -0.004, -0.18), (R(90), 0, 0), M_STAMP, TAG5, extrude=0.001)
lathe('tag5post', [(0.0, TOP5), (0.03, TOP5), (0.03, TOP5 + 0.01), (0.006, TOP5 + 0.012), (0.006, TOP5 + 0.32), (0.0, TOP5 + 0.32)], 12, M_BRASS, HALL, loc=(CX5 + 0.2, 3.97, 0))
COINS = []
gc_ = random.Random(3)
for k in range(9):
    o = prim('cylinder', f'coin{k}', M_GOLD, HALL, loc=(0, 0, -50), vertices=20, radius=0.032, depth=0.006)
    COINS.append((o, Vector((CX5 + 0.43 + gc_.uniform(-0.07, 0.07), 3.86 + gc_.uniform(-0.035, 0.035), TOP5 + 0.0031 + 0.0062 * (k % 3))), gc_.uniform(-0.4, 0.4), 0.07 * k))
track_spot('e5a', X5 - 0.45, (X5 - 0.45, 5.3, 2.4), 800, ang=40)
track_spot('e5b', CX5, (CX5, 4.0, 1.1), 900, ang=44)

# ================================================================ exhibit 6: 1958 - a plain brown package, stamps, the mailman (x = 20.4)
X6 = 20.4
platform(X6 + 0.3, 2.0)
box('tab6', (1.1, 0.6, 0.72), (X6, 3.95, PLAT_Z + 0.36), M_WOOD, bv=0.012, parent=HALL)
TOP6 = PLAT_Z + 0.72
PKG = empty('pkg', HALL)
PW, PD, PH = 0.46, 0.32, 0.15
box('pkgb', (PW, PD, PH), (0, 0, PH / 2), M_KRAFT, bv=0.006, parent=PKG)
for sx_, sy_ in ((PW + 0.006, 0.008), (0.008, PD + 0.006)): box(f'pkgs{sx_}', (sx_, sy_, PH + 0.006), (0, 0, PH / 2), M_STRING, parent=PKG)
LABEL6 = empty('label6', PKG, loc=(-0.09, 0.0, PH + 0.0035))
box('lab6b', (0.2, 0.13, 0.002), (0, 0, 0), M_PAPER, parent=LABEL6)
text3d('lab6t', 'SMITHSONIAN\nWASHINGTON DC', 0.016, (0, 0, 0.0016), (0, 0, 0), M_INK, LABEL6, extrude=0.0003)
FRAG6 = empty('frag6', PKG, loc=(0.0, -PD / 2 - 0.0035, PH / 2)); FRAG6.rotation_euler = (R(90), 0, 0)
box('frg6b', (0.22, 0.065, 0.002), (0, 0, 0), M_STAMP, parent=FRAG6)
text3d('frg6t', 'FRAGILE', 0.04, (0, 0, 0.0016), (0, 0, 0), M_WHITE, FRAG6, extrude=0.0004)
STAMPS6 = []
for k in range(6):
    st = empty(f'pst{k}', PKG, loc=(0.075 + 0.05 * (k % 3), 0.07 - 0.065 * (k // 3), PH + 0.0035))
    box(f'pstb{k}', (0.042, 0.052, 0.002), (0, 0, 0), M_WHITE, parent=st); box(f'psti{k}', (0.032, 0.042, 0.002), (0, 0, 0.0006), M_STAMP, parent=st)
    STAMPS6.append(st)
PKG_REST = Vector((X6 - 0.05, 3.88, TOP6))
YEAR6 = wall_sign('sg6', X6, 2.2, '1958', 1.1, 0.5, 0.3)
TAG6 = empty('tag6', HALL, loc=(X6 + 0.3, 3.82, TOP6))
box('tag6b', (0.2, 0.012, 0.11), (0, 0, 0.11), M_PAPER, bv=0.004, parent=TAG6)
text3d('tag6t', '$2.44', 0.05, (0, -0.007, 0.115), (R(90), 0, 0), M_INK, TAG6, extrude=0.001)
box('tag6s', (0.012, 0.012, 0.06), (0, 0.0, 0.03), M_BRASS, parent=TAG6)
# the CURSE warning sign on the table, flicked flat when the mailman shrugs it off
CS6 = empty('cs6', HALL, loc=(X6 - 0.43, 3.86, TOP6)); CS6.scale = (1.45, 1.45, 1.45)
box('cs6p', (0.012, 0.012, 0.1), (0, 0, 0.05), M_BRASS, parent=CS6)
tri_ = mesh('cs6t', [(-0.09, 0, 0.1), (0.09, 0, 0.1), (0, 0, 0.255)], [(0, 1, 2)], M_YELLOW, CS6, smooth_=False); tri_.modifiers.new('sd', 'SOLIDIFY').thickness = 0.008
text3d('cs6x', 'CURSE!', 0.024, (0, -0.007, 0.142), (R(90), 0, 0), M_INK, CS6, extrude=0.0008)
# the mailman: a dress form in a postal uniform, cap and satchel
MM = dress_form('mm', HALL, (X6 + 0.95, 4.05, PLAT_Z), m=M_DUMMY)
lathe('mm_coat', [(0.165, 0.7), (0.17, 0.85), (0.15, 1.0), (0.16, 1.18), (0.19, 1.34), (0.205, 1.42), (0.14, 1.5), (0.06, 1.545)], 28, M_UNIF, MM).scale = (1.0, 0.72, 1.0)
lathe('mm_cap', [(0.0, 0.07), (0.1, 0.07), (0.105, 0.02), (0.1, 0.0), (0.0, 0.0)], 24, M_UNIF, MM, loc=(0, 0.01, 1.8))
box('mm_brim', (0.14, 0.09, 0.008), (0, -0.1, 1.805), M_BLACK, parent=MM)
box('mm_badge', (0.04, 0.005, 0.03), (0, -0.098, 1.84), M_GILT, parent=MM)
tube('mm_strap', [(0.17, -0.02, 1.43), (0.05, -0.13, 1.22), (-0.15, -0.14, 0.98)], 0.012, M_LEATHER, MM, seg=8)
box('mm_bag', (0.26, 0.09, 0.22), (-0.17, -0.12, 0.88), M_LEATHER, bv=0.015, parent=MM)
box('mm_flap', (0.27, 0.095, 0.1), (-0.17, -0.125, 0.95), M_LEATHER, bv=0.012, parent=MM)
track_spot('e6', X6 + 0.2, (X6 + 0.2, 4.0, 1.1), 950, ang=52)

# ================================================================ exhibit 8: today, the Smithsonian - the package bursts open, the necklace rises; ultraviolet light, it glows red (x = 23.8)
X8, Y8 = 23.8, 3.75
CASE8 = glass_case('case8', X8, Y8)
BD8 = display_board('bd8', HALL, (X8, Y8 + 0.02, 1.31))
NK8, HOPE8 = necklace('nk8', BD8, M_HOPE, M_WHITE_D, M_PLAT, HOPE_ME, SMALL_ME)
BD8_REST = BD8.location.copy()
wall_sign('sg8', X8, 2.75, 'SMITHSONIAN', 2.0, 0.42, 0.18, m_bg=mat('navyp', (0.02, 0.03, 0.08), 0.5))
SCRAPS = []
gsc_ = random.Random(29)
for k in range(10):
    o = box(f'scrap{k}', (gsc_.uniform(0.07, 0.13), gsc_.uniform(0.05, 0.1), 0.004), (0, 0, -50), M_KRAFT, parent=HALL)
    SCRAPS.append((o, Vector((gsc_.uniform(-1.0, 1.0), gsc_.uniform(-0.9, 0.2), gsc_.uniform(1.0, 2.2))), Vector((gsc_.uniform(-9, 9), gsc_.uniform(-9, 9), gsc_.uniform(-5, 5)))))
UVL = empty('uvl', HALL, loc=(X8 + 0.5, Y8 - 0.2, 0))
lathe('uvst', [(0.0, 0.0), (0.12, 0.0), (0.12, 0.03), (0.02, 0.05), (0.016, 1.45), (0.0, 1.45)], 16, M_BLACK, UVL)
UVH = empty('uvh', UVL, loc=(0, 0, 1.5)); UVH.rotation_euler = (0, R(-35), 0)
box('uvhb', (0.08, 0.3, 0.06), (0, 0, 0), M_BLACK, bv=0.01, parent=UVH)
UVT = prim('cylinder', 'uvtube', M_UVTUBE, UVH, loc=(-0.035, 0, 0), rot=(R(90), 0, 0), vertices=10, radius=0.012, depth=0.26)
UVLIGHT = light_at('uvlight', 'AREA', (X8 + 0.44, Y8 - 0.22, 1.5), (X8, Y8, 1.25), 0.0, (0.45, 0.12, 1.0), 0.3)
track_spot('e8', X8, (X8, Y8, 1.2), 1000, ang=40)
# ================================================================ moving bits: event times (each on its word), glints
T_RISE0, T_RISE1 = -0.35, 0.5                  # the necklace rises in its case (frame 0 is mid-rise)
T_FLICK0, T_FLICK1 = 2.35, 3.15                # "bad luck": the lights flicker
T_CRACK = 2.6; T_PLQ = 2.95                    # the glass cracks; the plaque drops crooked
T_ROUGH = B[1] + 0.95                          # "bought it": the rough stone lands on the cushion
T_BAN = B[1] + 2.4; T_CROWN = B[1] + 2.75      # "King Louis": the banner unrolls, a crown lands
T_WHEEL = B[1] + 3.55; T_CUT = B[1] + 4.6      # "had it cut": the wheel spins up, sparks; "the French Blue": the stone becomes the cut gem
T_YEAR2 = B[2] + 0.2; T_LID = B[2] + 1.2       # "1792"; "thieves": the lid flips open
T_STAMP2 = B[2] + 1.65                         # "stole": STOLEN stamp
T_YANK = [B[2] + 1.55, B[2] + 1.8, B[2] + 2.05, B[2] + 2.4]   # the jewels are snatched up one by one (crown on "crown")
T_VANISH = B[2] + 3.9                          # "vanished": the French Blue is gone in a sparkle
T_HOPE3 = B[3] + 1.45                          # "blue diamond": the smaller stone pops up in London
T_SCAN0, T_FIT = B[3] + 3.2, B[3] + 4.35       # "scientists": the French Blue's outline comes down; "cut from": it fits round it
T_CHECK = B[3] + 4.85                          # "stolen one": a green check
T_BOOK0, T_BOOK1 = B[4] + 0.55, B[4] + 1.1     # "banker": the catalog opens
T_LET = B[4] + 1.95; T_SUB4 = B[4] + 2.5      # "Hope": H-O-P-E drop in
T_NEWS = [B[5] + 0.12, B[5] + 0.36, B[5] + 0.6]   # "the curse": the scare papers slap onto the board
T_STAMP5 = B[5] + 1.2                          # "made up"
T_SOLD = B[5] + 5.3; T_COIN = B[5] + 5.8       # "sell it": SOLD tag; "rich buyer": coins
T_PKG = B[6] + 0.4                             # "twist": the plain package thuds onto the table
T_YEAR6 = B[6] + 1.05; T_LABEL = B[6] + 3.3; T_FRAG = B[6] + 4.75
T_STAMPS = [B[7] + 0.15 + 0.12 * k for k in range(6)]          # "postage": stamps slap on
T_TAG6 = B[7] + 1.0                            # "two dollars and forty-four cents"
T_SHAKE0, T_SHAKE1 = B[7] + 3.7, B[7] + 4.35   # "didn't believe": the mailman shakes his head
T_CURSE6 = B[7] + 4.4                          # "curse": the CURSE sign falls flat
T_FLY0, T_FLY1 = B[7] + 4.55, B[8] + 0.2       # the package flies to the last case
T_BURST = B[8] + 0.4; T_RISE8 = B[8] + 0.95    # it bursts open; the necklace rises
T_DIM0, T_DIM1 = B[8] + 1.15, B[8] + 1.45      # "ultraviolet": the room goes dark
T_UV = B[8] + 1.5; T_GLOW1 = B[8] + 2.2; T_COAL = B[8] + 2.95
T_UVOFF = B[9] + 0.2; T_LUP = B[9] + 0.6       # "follow": the lamp goes off, the lights come back, the red glow lingers and fades

M_GLINT = emis('glintm', (1.0, 0.97, 0.9), 25.0)
def glint(name):
    vs = [(0, 0, 0)]; fs = []
    for i in range(8):
        a = math.pi / 4 * i; r_ = 0.07 if i % 2 == 0 else 0.012; vs.append((r_ * math.cos(a), 0, r_ * math.sin(a)))
    for i in range(8): fs.append((0, 1 + i, 1 + (i + 1) % 8))
    o = mesh(name, vs, fs, M_GLINT, None, smooth_=False, loc=(0, 0, -50)); o.scale = (0.0,) * 3; return o
GLS_O = [glint(f'gl{k}') for k in range(3)]
bpy.context.view_layer.update()
def wpos(o, off=(0, 0, 0)): return o.matrix_world @ Vector(off)
HOPE0_W = wpos(HOPE0) + Vector((0, -0.03, 0.01)); HOPE8_W = wpos(HOPE8) + Vector((0, -0.03, 0.01))
GLS = [(0, T_RISE1 + 0.05, HOPE0_W, 0.9), (1, 1.6, HOPE0_W + Vector((0.12, 0, 0.36)), 0.6),
       (2, T_CUT + 0.05, FB1_REST + Vector((0.0, -0.05, 0.03)), 1.0), (0, T_CROWN + 0.05, CROWN1_REST + Vector((0.05, -0.1, 0.12)), 0.7),
       (1, T_HOPE3 + 0.05, HOPE3_REST + Vector((0.01, -0.04, 0.03)), 0.8), (2, T_CHECK + 0.05, HOPE3_REST + Vector((-0.02, -0.04, 0.03)), 0.9),
       (0, T_SUB4 + 0.05, Vector((X4 + 0.32 + 0.45, 5.33, 2.4)), 0.8), (1, T_SOLD - 0.2, wpos(HOPE5) + Vector((0, -0.03, 0.01)), 0.8),
       (2, T_RISE8 + 0.05, HOPE8_W, 0.9), (0, T_LUP + 0.3, HOPE8_W + Vector((0.1, 0, 0.3)), 0.7), (1, TOTAL - 0.8, HOPE8_W, 0.9)]
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
    key(0.0, (X0, 2.8, 1.4), (X0, 3.75, 1.24), 34),                        # the necklace rises in its case
    key(1.4, (X0, 2.9, 1.37), (X0, 3.75, 1.22), 34),
    key(2.2, (X0 + 0.05, 2.45, 1.55), (X0, 3.75, 1.15), 26),               # back: the lights flicker, the glass cracks, the plaque drops
    key(B[1] - 0.15, (X0 + 0.05, 2.47, 1.55), (X0, 3.75, 1.15), 26),
    key(B[1] + 0.7, (X1 + 0.15, 2.5, 1.6), (X1 + 0.15, 4.4, 1.5), 24),    # India to France: stone, banner, crown
    key(B[1] + 3.5, (X1 + 0.15, 2.55, 1.6), (X1 + 0.15, 4.4, 1.5), 24),
    key(B[1] + 4.15, (X1 - 0.08, 3.0, 1.48), (X1 - 0.06, 3.85, 1.1), 32),  # in on the wheel: the French Blue
    key(B[2] - 0.15, (X1 - 0.08, 3.03, 1.47), (X1 - 0.06, 3.85, 1.1), 32),
    key(B[2] + 0.7, (X2, 2.75, 1.75), (X2, 4.1, 1.15), 26),                # 1792: the crown jewels case
    key(B[2] + 3.2, (X2, 2.8, 1.73), (X2, 4.1, 1.15), 26),
    key(B[2] + 3.75, (X2 + 0.02, 3.05, 1.5), (X2 + 0.02, 3.8, 1.0), 34),  # in: the French Blue vanishes
    key(B[3] - 0.15, (X2 + 0.02, 3.07, 1.49), (X2 + 0.02, 3.8, 1.0), 34),
    key(B[3] + 0.75, (X3, 2.95, 1.6), (X3, 3.85, 1.12), 32),               # London: a smaller blue stone
    key(B[3] + 3.0, (X3, 3.0, 1.58), (X3, 3.85, 1.12), 32),
    key(B[3] + 3.6, (X3, 3.12, 1.5), (X3, 3.85, 1.14), 36),                # the scan outline fits round it
    key(B[4] - 0.15, (X3, 3.13, 1.5), (X3, 3.85, 1.14), 36),
    key(B[4] + 0.7, (X4 - 0.26, 3.12, 1.68), (X4 - 0.28, 3.95, 1.12), 30), # the catalog opens
    key(B[4] + 1.45, (X4 - 0.25, 3.14, 1.67), (X4 - 0.28, 3.95, 1.12), 30),
    key(B[4] + 1.95, (X4 + 0.1, 2.85, 1.72), (X4 + 0.2, 5.36, 1.8), 28),   # up to the nameplate: H-O-P-E
    key(B[5] - 0.15, (X4 + 0.1, 2.88, 1.72), (X4 + 0.2, 5.36, 1.8), 28),
    key(B[5] + 0.6, (X5 - 0.45, 3.0, 2.2), (X5 - 0.45, 5.36, 2.4), 26),    # the scare papers, MADE UP
    key(B[5] + 1.85, (X5 - 0.45, 3.05, 2.2), (X5 - 0.45, 5.36, 2.4), 26),
    key(B[5] + 2.6, (CX5 + 0.12, 2.8, 1.75), (CX5 + 0.12, 4.0, 1.15), 26), # the jeweler's counter: SOLD
    key(B[6] - 0.15, (CX5 + 0.12, 2.83, 1.74), (CX5 + 0.12, 4.0, 1.15), 26),
    key(B[6] + 0.6, (X6 - 0.12, 2.75, 1.68), (X6 - 0.12, 4.0, 1.05), 26),  # 1958: the plain package
    key(B[7] - 0.1, (X6 - 0.1, 2.78, 1.67), (X6 - 0.12, 4.0, 1.05), 26),
    key(B[7] + 0.45, (X6 + 0.08, 3.0, 1.45), (X6 + 0.08, 3.9, 0.9), 28),   # in: stamps, $2.44
    key(B[7] + 2.4, (X6 + 0.08, 3.02, 1.44), (X6 + 0.08, 3.9, 0.9), 28),
    key(B[7] + 3.1, (X6 + 0.28, 2.2, 1.85), (X6 + 0.28, 4.0, 1.3), 22),    # wide: the mailman shrugs off the curse
    key(B[7] + 4.5, (X6 + 0.3, 2.22, 1.85), (X6 + 0.3, 4.0, 1.3), 22),
    key(B[8] + 0.55, (X8 + 0.1, 2.65, 1.62), (X8 + 0.05, 3.75, 1.35), 26), # the last case: it bursts open, the necklace rises
    key(B[8] + 1.4, (X8 + 0.12, 2.8, 1.48), (X8 + 0.05, 3.75, 1.3), 26),   # ultraviolet: it glows red
    key(B[9] + 0.1, (X8 + 0.12, 2.86, 1.46), (X8 + 0.05, 3.75, 1.3), 26),
    key(TOTAL, (X8 + 0.05, 2.45, 1.65), (X8, 3.75, 1.3), 24),
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


J2_REST = [o.location.copy() for o in JEWELS2]; LID2_REST = LID2.location.copy(); FB2R_REST = FB2R.location.copy()
NEWS_REST = [(o.location.copy(), o.rotation_euler.copy()) for o, _, _ in NEWS]
PKG_TOP8 = Vector((X8, Y8, 1.0 + 0.66 + 0.006))
def wheel_angle(t):
    a = 0.0; n = 160; t0 = T_WHEEL
    if t <= t0: return 0.0
    dt = (t - t0) / n
    for i in range(n):
        tt = t0 + (i + 0.5) * dt; w = 32.0 * smooth(T_WHEEL, T_WHEEL + 0.45, tt) * (1 - smooth(T_CUT + 0.4, T_CUT + 1.3, tt)); a += w * dt
    return a


def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- lights: a flicker on "bad luck"; the crown-jewel spot dims after the theft; the room goes dark for the ultraviolet lamp
    fl = 1.0
    if T_FLICK0 < t < T_FLICK1: fl = (1.0, 0.12, 0.9, 0.3, 0.08, 1.0, 0.2, 0.7)[int((t - T_FLICK0) * 11) % 8]
    dim = 1.0 - 0.9 * smooth(T_DIM0, T_DIM1, t) * (1.0 - smooth(T_UVOFF, T_LUP, t))
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * fl * dim
    lt2, e2 = SPOTS['e2']; lt2.data.energy = e2 * fl * (1 - 0.7 * smooth(T_VANISH + 0.2, T_VANISH + 0.7, t)) * dim
    # ---- exhibit 0: the necklace rises; the glass cracks; the plaque drops crooked
    u = smooth(T_RISE0, T_RISE1, t); BD0.location = BD0_REST + Vector((0, 0, -0.65 * (1 - u) + 0.012 * math.sin(math.pi * u)))
    for k, o in enumerate(CRACK): o.hide_render = t < T_CRACK + 0.03 * k
    PLQ0.rotation_euler = (0, spring(t - T_PLQ, R(24)), 0)
    # ---- exhibit 1: the rough stone lands; banner and crown; the wheel spins, sparks fly; the stone becomes the French Blue
    p_, w_ = drop(t, T_ROUGH, ROUGH_REST, 0.9, 0.4)
    if p_ is None or t > T_CUT + 0.06: ROUGH.location = FAR
    else:
        jit = Vector((wob(t, 40, 1) * 0.003, 0, 0)) * smooth(T_WHEEL + 0.3, T_WHEEL + 0.5, t)
        ROUGH.location = p_ + jit; ROUGH.rotation_euler = (R(30) * w_, R(-20) * w_, R(40) * w_)
        s = 1.0 - smooth(T_CUT - 0.06, T_CUT + 0.06, t); ROUGH.scale = (max(s, 1e-4),) * 3
    s = pop(t, T_CUT, 0.22, 0.35); FB1.scale = (s, s, s); FB1.location = FB1_REST if t >= T_CUT else FAR
    BAN1.scale = (1.0, 1.0, pop(t, T_BAN, 0.35, 0.08))
    p_, w_ = drop(t, T_CROWN, CROWN1_REST, 0.9, 0.38)
    CROWN1.location = p_ if p_ is not None else FAR; CROWN1.rotation_euler = (R(8) * w_, R(-6) * w_, R(60) * w_)
    WHEEL.rotation_euler = (0, wheel_angle(t), 0)
    for o, vx, vy, vz, dl in SPARKS:
        on = T_WHEEL + 0.35 < t < T_CUT
        if not on: o.location = FAR; continue
        d = (t - T_WHEEL - 0.35 - dl) % 0.5
        o.location = Vector((X1 + 0.04, 3.83, 1.13)) + Vector((vx * d, vy * d * 0.3 - 0.05 * d, vz * d - 4.9 * d * d))
        o.scale = (1.0 - d / 0.5,) * 3
    # ---- exhibit 2: 1792 - the lid flips up, STOLEN, the jewels are snatched one by one; the French Blue vanishes in a sparkle
    YEAR2.scale = (pop(t, T_YEAR2),) * 3
    d = t - T_LID
    if d < 0: LID2.location = LID2_REST; LID2.rotation_euler = (0, 0, 0)
    elif d < 1.0: LID2.location = LID2_REST + Vector((0.1 * d, 0.3 * d, 0.5 * d + 6.0 * d * d)); LID2.rotation_euler = (-R(80) * min(1, d / 0.3), R(25) * d, 0)
    else: LID2.location = FAR
    STAMP2.scale = slam(t, T_STAMP2)
    for k, (o, r0) in enumerate(zip(JEWELS2, J2_REST)):
        ty = T_YANK[(k - 1) % 4]; d = t - ty
        if d < 0: o.location = r0; o.rotation_euler = (0, 0, 0); continue
        if d > 1.2: o.location = FAR; continue
        sx = (-1, 1, -1, 1)[k]; o.location = r0 + Vector((0.12 * sx * d, 0.25 * d, 0.6 * d + 7.0 * d * d)); o.rotation_euler = (R(200) * d, R(140) * d * sx, R(260) * d)
    s = 1.0 - smooth(T_VANISH, T_VANISH + 0.16, t); FB2R.scale = (max(s, 1e-4),) * 3
    FB2R.location = FB2R_REST + Vector((0, 0, 0.03 * smooth(T_VANISH - 0.15, T_VANISH, t)))
    for o, v, ph in POOF:
        d = t - T_VANISH
        if not 0 < d < 0.7: o.location = FAR; continue
        o.location = FB2R_REST + Vector((0, 0, 0.03)) + v * d * (1.0 - 0.5 * d); s = math.sin(math.pi * d / 0.7) * 0.9; o.scale = (s, s, s); o.rotation_euler = (ph + 9 * d, ph, 7 * d)
    # ---- exhibit 3: London - the smaller blue stone pops up; the French Blue's outline comes down and fits round it; a green check
    s = pop(t, T_HOPE3, 0.22, 0.35); HOPE3.scale = (s, s, s); HOPE3.location = HOPE3_REST + Vector((0, 0, 0.04 * math.sin(math.pi * clamp((t - T_HOPE3) / 0.3, 0, 1))))
    if t < T_SCAN0: GHOST.scale = (1e-4,) * 3
    else:
        u = smooth(T_SCAN0 + 0.15, T_FIT, t); s = pop(t, T_SCAN0, 0.2, 0.2) * (1 + 0.06 * math.sin(math.pi * clamp((t - T_CHECK) / 0.3, 0, 1)))
        GHOST.scale = (s, s, s); GHOST.location = HOPE3_REST + Vector((0, 0, 0.42 * (1 - u))); GHOST.rotation_euler = (0, 0, R(70) * (1 - u))
    CHECK3.scale = (pop(t, T_CHECK, 0.22, 0.4),) * 3
    # ---- exhibit 4: the catalog opens; H-O-P-E drop onto the nameplate
    e = smooth(T_BOOK0, T_BOOK1, t)
    for pv, s_ in PG4:
        if s_ > 0: pv.rotation_euler = (0, -R(178) * (1 - e), 0); pv.location.z = 0.012 + 0.026 * (1 - e)
    bpy.data.objects['bk4gem'].hide_render = e < 0.6
    for k, (o, r0) in enumerate(zip(LET4, LET4_REST)):
        d = t - (T_LET + 0.1 * k)
        if d < -0.15: o.location = r0 + Vector((0, -0.5, 0.6)); o.scale = (1e-4,) * 3; continue
        o.scale = (1, 1, 1)
        if d < 0: u = (d + 0.15) / 0.15; o.location = r0 + Vector((0, -0.25 * (1 - u), 0.5 * (1 - u * u)))
        else: o.location = r0 + Vector((0, 0, 0.02 * abs(math.sin(d * 18)) * math.exp(-d * 9)))
    SUB4.scale = (pop(t, T_SUB4),) * 3
    # ---- exhibit 5: the scare papers fly onto the board; MADE UP; at the counter a SOLD tag swings on and coins drop
    for k, (np_, (r0, e0)) in enumerate(zip([n[0] for n in NEWS], NEWS_REST)):
        d = t - T_NEWS[k]
        if d < -0.28: np_.location = FAR; continue
        if d < 0:
            u = sm((d + 0.28) / 0.28); np_.location = r0.lerp(r0 + Vector((-0.4 + 0.4 * k, -1.5, 0.6)), 1 - u)
            np_.rotation_euler = (e0.x + R(70) * (1 - u), e0.y + R(200) * (1 - u) * (1 if k % 2 else -1), e0.z)
        else:
            np_.location = r0; np_.rotation_euler = e0; sq = 0.05 * math.exp(-d * 14) * math.cos(d * 40); np_.scale = (1 + sq, 1, 1 - sq)
    STAMP5.scale = slam(t, T_STAMP5)
    s = pop(t, T_SOLD, 0.2, 0.3); TAG5.scale = (s, s, s); TAG5.rotation_euler = (R(18) * math.exp(-3 * max(0, t - T_SOLD)) * math.sin(9 * max(0, t - T_SOLD)), 0, 0)
    for o, rest, rz, dl in COINS:
        p_, w_ = drop(t, T_COIN + dl, rest, 0.5, 0.3)
        o.location = p_ if p_ is not None else FAR; o.rotation_euler = (R(160) * w_, R(90) * w_, rz)
    # ---- exhibit 6: the plain package thuds down; 1958; the address label, FRAGILE, the stamps, $2.44; the mailman shakes his head, CURSE falls
    PKG.scale = (1, 1, 1)
    if t < T_FLY0:
        p_, w_ = drop(t, T_PKG, PKG_REST, 0.9, 0.35)
        PKG.location = p_ if p_ is not None else FAR; PKG.rotation_euler = (R(12) * w_, R(-8) * w_, R(-25) * w_)
    elif t < T_FLY1:
        u = sm((t - T_FLY0) / (T_FLY1 - T_FLY0)); uh = u ** 1.6; PKG.location = PKG_REST.lerp(PKG_TOP8, uh) + Vector((0, 0, 1.5 * math.sin(math.pi * u)))
        PKG.rotation_euler = (R(25) * math.sin(math.pi * u), 0, R(360) * u)
    elif t < T_BURST:
        d = t - T_FLY1; PKG.location = PKG_TOP8 + Vector((0, 0, 0.02 * abs(math.sin(d * 14)) * math.exp(-d * 7))); PKG.rotation_euler = (0, 0, 0)
        sq = 0.08 * smooth(T_BURST - 0.15, T_BURST, t); PKG.scale = (1 + sq, 1 + sq, 1 - sq)
    else: PKG.location = FAR
    YEAR6.scale = (pop(t, T_YEAR6, 0.25, 0.25),) * 3
    LABEL6.scale = slam(t, T_LABEL); FRAG6.scale = slam(t, T_FRAG)
    for st, ts in zip(STAMPS6, T_STAMPS): st.scale = slam(t, ts)
    s = pop(t, T_TAG6, 0.22, 0.3); TAG6.scale = (s, s, s); TAG6.rotation_euler = (0, R(10) * math.exp(-3 * max(0, t - T_TAG6)) * math.sin(10 * max(0, t - T_TAG6)), 0)
    a_ = 0.0
    if T_SHAKE0 < t < T_SHAKE1 + 0.2: d = t - T_SHAKE0; a_ = R(16) * math.sin(2 * math.pi * 2.6 * d) * math.sin(math.pi * clamp(d / (T_SHAKE1 + 0.2 - T_SHAKE0), 0, 1))
    MM.rotation_euler = (0, 0, a_)
    d = t - T_CURSE6
    CS6.rotation_euler = (-R(88) * clamp(d / 0.22, 0, 1) ** 2 + (R(4) * math.exp(-d * 10) * abs(math.sin(d * 25)) if d > 0.22 else 0.0), 0, 0) if d > 0 else (0, 0, 0)
    # ---- exhibit 8: the package bursts; the necklace rises; ultraviolet - it glows red like a hot coal, and keeps glowing after the lamp goes off
    for o, v, w in SCRAPS:
        d = t - T_BURST
        if not 0 < d < 1.3: o.location = FAR; continue
        pz = PKG_TOP8.z + 0.06 + v.z * d - 4.9 * d * d
        if pz < 0.02: o.location = FAR; continue
        o.location = Vector((PKG_TOP8.x + v.x * d * 0.6, PKG_TOP8.y + v.y * d * 0.6, pz)); o.rotation_euler = tuple(w * d)
    u = smooth(T_BURST + 0.05, T_RISE8, t); BD8.location = BD8_REST + Vector((0, 0, -0.65 * (1 - u) + 0.012 * math.sin(math.pi * u)))
    uv = (T_UV < t < T_UVOFF) and not (T_UV + 0.06 < t < T_UV + 0.12)
    UVLIGHT.data.energy = 70.0 * uv; UVT.hide_render = not uv
    g = smooth(T_UV + 0.1, T_GLOW1, t) * (1 + 0.25 * math.sin(math.pi * clamp((t - T_COAL) / 0.5, 0, 1)))
    if t > T_UVOFF: g = math.exp(-(t - T_UVOFF) / 0.9)
    HOPE8['glow'] = g
    # ---- glints
    for g_ in GLS_O: g_.hide_render = True; g_.scale = (0.0,) * 3
    for gi, t0, pw, sz in GLS:
        u = clamp((t - t0) / 0.35, 0, 1)
        if 0 < u < 1: g_ = GLS_O[gi]; s = math.sin(math.pi * u) * sz; g_.scale = (s, s, s); g_.rotation_euler = (0, u * 1.2, 0); g_.location = pw; g_.hide_render = False
    # ---- camera, with a nod on each thud
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.005, 1.0, 1.3)
    for tn, a_ in ((T_CROWN, 0.006), (T_STAMP5, 0.01), (T_PKG, 0.012), (T_FLY1, 0.008), (T_BURST, 0.01)):
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
    def ubox(root):
        pts = [o.matrix_world @ Vector(c) for o in [root] + list(root.children_recursive) if o.type in ('MESH', 'FONT') for c in o.bound_box]
        return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    for f in range(int(T_FLY0 * FPS), int(T_FLY1 * FPS) + 1):
        frame(f); a0, a1 = ubox(PKG); b0, b1 = ubox(MM)
        if all(a0[i] < b1[i] and b0[i] < a1[i] for i in range(3)): print('PKG HITS MAILMAN', f, a0.z, b1.z)
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

