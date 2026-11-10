# The machine that builds itself (Claude's pick): a brass clockwork robot on a workbench builds an exact copy of itself, part by part, from
# the plans on its punched paper tape: a real watch-style movement (mainspring barrel, wheel train with meshing teeth, lever escapement,
# balance and hairspring ticking 5 times a second), six legs and two arms on working linkages (2-link IK), a tape reader, a tape copier.
# The copy gets a copy of the tape, winds up, wakes, and reaches for the next wheel (the loop). Then: von Neumann (1948), DNA (1953), cells.
#   python3 robot.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]      (stride.json / redo.json beside it)
import sys, os, math, json, argparse
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n42/robot', n)) if os.path.exists(p_))
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
import numpy as np, random
C.max_bounces = 8; C.glossy_bounces = 4; C.transmission_bounces = 6
# ================================================================ MATERIALS: brushed brass, steel, blued screws, rubies, glass, walnut
def metal(name, col, rough=0.25, aniso=0.0, scratch=0.0, scale=400.0):
    m = mat(name, col, rough, metal=1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    if aniso:
        b.inputs['Anisotropic'].default_value = aniso
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 1.0, 40.0)                 # stretched: fine brushing lines
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = max(0.02, rough - 0.08 - scratch); mr.inputs['To Max'].default_value = rough + 0.06
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    bw = nt.nodes.new('ShaderNodeMix'); bw.data_type = 'RGBA'; bw.inputs['A'].default_value = (*col, 1); bw.inputs['B'].default_value = tuple(c * 0.82 for c in col) + (1,)
    nt.links.new(nz.outputs['Fac'], bw.inputs['Factor']); nt.links.new(bw.outputs['Result'], b.inputs['Base Color']); return m
BRASS = metal('brass', (0.86, 0.62, 0.3), 0.26, 0.4)
GILT = metal('gilt', (0.98, 0.76, 0.42), 0.18, 0.2, scale=900.0)
STEEL = metal('steel', (0.66, 0.67, 0.7), 0.16, 0.3, scale=1200.0)
DSTEEL = metal('dark_steel', (0.16, 0.16, 0.18), 0.28, 0.2)
BLUED = metal('blued', (0.06, 0.16, 0.5), 0.2, 0.0, scale=2000.0)
COPPER = metal('copper', (0.9, 0.45, 0.3), 0.3, 0.3)
RATCH = metal('ratchet_steel', (0.36, 0.37, 0.41), 0.22, 0.5, scale=1500.0)
RUBY = mat('ruby', (0.95, 0.04, 0.08), 0.02, trans=1.0, ior=1.77)
N(RUBY)['Principled BSDF'].inputs['Emission Color'].default_value = (1.0, 0.05, 0.08, 1); N(RUBY)['Principled BSDF'].inputs['Emission Strength'].default_value = 0.15
GLASS = mat('glass', (0.97, 0.98, 1.0), 0.0, trans=1.0, ior=1.5)
def eye_mat():
    """the lens's iris: amber rings that glow by the object prop 'on' (0..1)"""
    m = bpy.data.materials.new('eye'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    rr = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sx.outputs['Y'], sx.outputs['Y']), math_(nt, 'MULTIPLY', sx.outputs['Z'], sx.outputs['Z'])))
    ring = math_(nt, 'POWER', math_(nt, 'ABSOLUTE', math_(nt, 'SINE', math_(nt, 'MULTIPLY', rr, 1800.0))), 6.0)
    b.inputs['Base Color'].default_value = (0.08, 0.05, 0.02, 1); b.inputs['Roughness'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (1.0, 0.55, 0.12, 1)
    core = math_(nt, 'LESS_THAN', rr, 0.0025)
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'ADD', math_(nt, 'MULTIPLY', ring, 9.0), math_(nt, 'MULTIPLY', core, 40.0)), objattr(nt, 'on')), b.inputs['Emission Strength'])
    return m
EYE_M = eye_mat()
def walnut_mat():
    m = mat('walnut', (0.22, 0.12, 0.06), 0.42, coat=0.35); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 6.0; wv.inputs['Distortion'].default_value = 2.5; wv.inputs['Detail'].default_value = 8; wv.inputs['Detail Scale'].default_value = 2.0
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.25, 6.0, 1.0); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.11, 0.055, 0.025, 1); cr.color_ramp.elements[1].color = (0.3, 0.17, 0.08, 1)
    nt.links.new(wv.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 300.0; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.3; mr.inputs['To Max'].default_value = 0.6
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness']); return m
WALNUT = walnut_mat()
def tape_mat():
    """paper tape: 'tu' (attribute) = position along the tape (m); holes from a fixed bit pattern; holes exist only where the punch has
    been ('punched' prop, m along the tape: holes for tu < punched); 'lit' highlights the row under the reader at 'readat' (m)"""
    m = bpy.data.materials.new('tape'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    b.inputs['Base Color'].default_value = (0.86, 0.8, 0.66, 1); b.inputs['Roughness'].default_value = 0.8; b.inputs['Sheen Weight'].default_value = 0.3
    tu0 = nt.nodes.new('ShaderNodeAttribute'); tu0.attribute_type = 'GEOMETRY'; tu0.attribute_name = 'tu'; tu0 = tu0.outputs['Fac']; tu = math_(nt, 'ADD', tu0, objattr(nt, 'off'))
    tv = nt.nodes.new('ShaderNodeAttribute'); tv.attribute_type = 'GEOMETRY'; tv.attribute_name = 'tv'; tv = tv.outputs['Fac']   # -1..1 across
    row = math_(nt, 'FLOOR', math_(nt, 'DIVIDE', tu, 0.0025)); col = math_(nt, 'ROUND', math_(nt, 'MULTIPLY', math_(nt, 'ADD', tv, 1.0), 2.5))
    cu = math_(nt, 'SUBTRACT', math_(nt, 'FRACT', math_(nt, 'DIVIDE', tu, 0.0025)), 0.5); cv = math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', math_(nt, 'ADD', tv, 1.0), 2.5), col)
    d = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', cu, cu), math_(nt, 'MULTIPLY', cv, cv)))
    bit = math_(nt, 'GREATER_THAN', math_(nt, 'FRACT', math_(nt, 'MULTIPLY', math_(nt, 'SINE', math_(nt, 'ADD', math_(nt, 'MULTIPLY', row, 12.9898), math_(nt, 'MULTIPLY', col, 78.233))), 43758.55)), 0.45)
    sprocket = math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', col, 2.0)), 0.5)          # the small feed hole down the middle
    hole_r = math_(nt, 'ADD', math_(nt, 'MULTIPLY', sprocket, 0.12), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, sprocket), 0.26))
    is_hole = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', d, hole_r), math_(nt, 'MAXIMUM', bit, sprocket))
    is_hole = math_(nt, 'MULTIPLY', is_hole, math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', tv), 0.96))
    is_hole = math_(nt, 'MULTIPLY', is_hole, math_(nt, 'LESS_THAN', tu, objattr(nt, 'punched')))
    lit = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', tu0, objattr(nt, 'readat'))), 0.0013), objattr(nt, 'lit'))
    b.inputs['Emission Color'].default_value = (1.0, 0.6, 0.2, 1); nt.links.new(math_(nt, 'MULTIPLY', lit, 2.0), b.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(is_hole, mx.inputs['Fac']); nt.links.new(b.outputs['BSDF'], mx.inputs[1]); nt.links.new(tr.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
TAPE_M = tape_mat()

# ================================================================ PARTS: gears with real teeth, arbors, jewels, screws
def _ring_mesh(name, outer, inner, z0, z1):
    """a flat part: outer 2D loop, inner 2D loop (same count), extruded from z0 to z1"""
    n = len(outer); vs = []
    for z in (z0, z1):
        vs += [(x, y, z) for x, y in outer] + [(x, y, z) for x, y in inner]
    fs = []
    for i in range(n):
        j = (i + 1) % n
        fs.append((n * 2 + i, n * 2 + j, n * 3 + j, n * 3 + i))          # top
        fs.append((i, n + i, n + j, j))                                   # bottom
        fs.append((i, j, n * 2 + j, n * 2 + i))                           # outer wall
        fs.append((n + i, n * 3 + i, n * 3 + j, n + j))                   # inner wall
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.validate(); me.update(); return me
def gear_outline(n, m, kind='wheel'):
    rp = m * n / 2; ra = rp + (0.95 if kind == 'wheel' else 0.8) * m; rf = rp - 1.25 * m; p = 2 * math.pi / n; pts = []
    for k in range(n):
        a = k * p
        if kind == 'ratchet':                                            # saw teeth: a long ramp, a straight drop (the click rides up, snaps down)
            prof = [(-0.5, rf), (0.36, ra), (0.42, ra - 0.12 * m), (0.46, rf + 0.1 * m), (0.5, rf)]
        elif kind == 'escape':                                           # club teeth leaning forward
            prof = [(-0.5, rf), (-0.12, rf), (0.12, rp + 0.3 * m), (0.3, ra), (0.4, ra - 0.3 * m), (0.22, rp), (0.36, rf + 0.3 * m), (0.5, rf)]
        else:
            prof = [(-0.5, rf), (-0.3, rf), (-0.24, rf + 0.6 * m), (-0.2, rp), (-0.13, ra - 0.25 * m), (-0.06, ra), (0.06, ra), (0.13, ra - 0.25 * m),
                    (0.2, rp), (0.24, rf + 0.6 * m), (0.3, rf), (0.5, rf)]
        for fa, r in prof[:-1]: pts.append((r * math.cos(a + fa * p), r * math.sin(a + fa * p)))
    return pts, rp, ra, rf
def gear(name, n, m, thick, mt=BRASS, spokes=5, kind='wheel', parent=None, z=0.0):
    """a toothed wheel (spoked) or a solid pinion, in the xy plane, axis z, from z to z + thick"""
    outer, rp, ra, rf = gear_outline(n, m, kind)
    if spokes and rp > 0.004:
        rin = rf - max(0.0012, 0.12 * rp); inner = [(rin * math.cos(math.atan2(y, x)), rin * math.sin(math.atan2(y, x))) for x, y in outer]
        me = _ring_mesh(name, outer, inner, z, z + thick); o = obj(name, me, mt, parent=parent)
        bm = bmesh.new(); bm.from_mesh(me)
        rh = max(0.0015, 0.18 * rp); hub = [(rh * math.cos(2 * math.pi * i / 32), rh * math.sin(2 * math.pi * i / 32)) for i in range(32)]
        hb = [(0.0006 * math.cos(2 * math.pi * i / 32), 0.0006 * math.sin(2 * math.pi * i / 32)) for i in range(32)]
        hm = _ring_mesh('h', hub, hb, z - 0.0002, z + thick + 0.0002)
        bm2 = bmesh.new(); bm2.from_mesh(hm); _merge(bm, bm2); bpy.data.meshes.remove(hm)
        w = max(0.0006, 0.09 * rp)
        for s_ in range(spokes):
            a = 2 * math.pi * s_ / spokes; c, s = math.cos(a), math.sin(a)
            r0, r1 = rh * 0.9, rin + 0.0003
            quad = [(r0, -w / 2), (r1, -w / 2 * 0.7), (r1, w / 2 * 0.7), (r0, w / 2)]
            ql = [(x * c - y * s, x * s + y * c) for x, y in quad]
            vs = [(x, y, z + thick * 0.15) for x, y in ql] + [(x, y, z + thick * 0.85) for x, y in ql]
            sm_ = bmesh.new(); vv = [sm_.verts.new(v) for v in vs]
            for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): sm_.faces.new([vv[i] for i in f])
            _merge(bm, sm_)
        bm.to_mesh(me); bm.free()
    else:
        inner = [(0.0005 * math.cos(math.atan2(y, x)), 0.0005 * math.sin(math.atan2(y, x))) for x, y in outer]
        o = obj(name, _ring_mesh(name, outer, inner, z, z + thick), mt, parent=parent)
    bv = o.modifiers.new('bv', 'BEVEL'); bv.width = min(0.00012, m * 0.12); bv.segments = 2; bv.limit_method = 'ANGLE'; bv.harden_normals = False
    o['rp'] = rp; return o
def _merge(bm, other):
    mp = {}
    for v in other.verts: mp[v] = bm.verts.new(v.co)
    for f in other.faces:
        try: bm.faces.new([mp[v] for v in f.verts])
        except ValueError: pass
    other.free()
def cyl(name, r, z0, z1, mt, parent=None, seg=24, loc=(0, 0, 0)):
    return lathe(name, [(0.0, z0), (r, z0), (r, z1), (0.0, z1)], seg, mt, parent, loc=loc)
def jewel(name, parent, loc, r=0.0011):
    o = lathe(name, [(0.0, -0.0004), (r, -0.0004), (r * 1.05, 0.0), (r * 0.7, 0.0005), (0.0, 0.0005)], 20, RUBY, parent, loc=loc); return o
def screw(name, parent, loc, r=0.0012, mt=None):
    o = lathe(name, [(0.0, 0.0), (r, 0.0), (r, 0.0004), (r * 0.85, 0.0007), (0.0, 0.00075)], 20, mt or BLUED, parent, loc=loc)
    sl = box(name + '_slot', (r * 2.1, r * 0.28, 0.0004), (0, 0, 0.0007), DSTEEL, parent=o); return o

def solid(name, outline, z0, z1, mt, parent=None, bvw=0.00025):
    bm = bmesh.new(); bot = [bm.verts.new((x, y, z0)) for x, y in outline]; top = [bm.verts.new((x, y, z1)) for x, y in outline]
    bm.faces.new(bot[::-1]); bm.faces.new(top); n = len(outline)
    for i in range(n): j = (i + 1) % n; bm.faces.new((bot[i], bot[j], top[j], top[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = obj(name, me, mt, parent=parent)
    bv = o.modifiers.new('bv', 'BEVEL'); bv.width = bvw; bv.segments = 3; bv.limit_method = 'ANGLE'; return o
def hull(pts):
    pts = sorted(set((round(x, 7), round(y, 7)) for x, y in pts))
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
def blob(centres, r):
    return hull([(cx + r_ * math.cos(2 * math.pi * k / 40), cy + r_ * math.sin(2 * math.pi * k / 40)) for (cx, cy), r_ in zip(centres, r if isinstance(r, list) else [r] * len(centres)) for k in range(40)])

# ================================================================ THE ROBOT (built twice: the builder and the copy). Local frame: +x forward,
# z up, z = 0 the top of its body drum (the movement plate). Movement: mainspring barrel -> centre -> third -> fourth -> escape wheel, a
# lever (pallet fork) with ruby pallets, a balance wheel with its hairspring. Tooth counts and pitch radii mesh exactly (module per pair).
LAYOUT = {}
def _layout():
    B_ = Vector((-0.02, -0.012)); C_ = B_ + 0.021 * Vector((math.cos(R(20)), math.sin(R(20))))
    T_ = C_ + 0.0144 * Vector((math.cos(R(80)), math.sin(R(80)))); F_ = T_ + 0.0119 * Vector((math.cos(R(10)), math.sin(R(10))))
    E_ = F_ + 0.00945 * Vector((math.cos(R(-60)), math.sin(R(-60)))); P_ = E_ + 0.0085 * Vector((math.cos(R(-40)), math.sin(R(-40))))
    BL = P_ + 0.012 * (P_ - E_).normalized()
    rot = Matrix.Rotation(math.pi, 2)                                   # turned so the balance sits at the back
    for k, v in (('barrel', B_), ('centre', C_), ('third', T_), ('fourth', F_), ('escape', E_), ('fork', P_), ('balance', BL)): LAYOUT[k] = rot @ v
_layout()
#        name     teeth module  z    thick  | pinion teeth (module = the wheel it drives into)
TRAIN = [('barrel', 72, 0.0005, 0.0030, 0.0022, None, None),
         ('centre', 64, 0.0004, 0.0060, 0.0011, 12, 0.0005),
         ('third', 60, 0.00035, 0.0085, 0.0010, 8, 0.0004),
         ('fourth', 56, 0.0003, 0.0108, 0.0009, 8, 0.00035),
         ('escape', 15, 0.00085, 0.0132, 0.0008, 7, 0.0003)]
RATIO = {'barrel': (12 / 72) * (8 / 64) * (8 / 60) * (7 / 56), 'centre': -(8 / 64) * (8 / 60) * (7 / 56), 'third': (8 / 60) * (7 / 56), 'fourth': -(7 / 56), 'escape': 1.0}
def tape_path():
    """spool 0 (full) -> straight up to the reader drum -> over its top (the pins ride here, x = 0) -> down to spool 1 (take-up)"""
    P = [Vector((-0.011 + 0.0069 * math.cos(a_), 0, 0.012 + 0.0069 * math.sin(a_))) for a_ in np.linspace(math.pi * 0.95, math.pi * 0.5, 7)]
    a0 = P[-1]; a1 = Vector((0.0033 * math.cos(math.pi * 0.75), 0, 0.024 + 0.0033 * math.sin(math.pi * 0.75)))
    P += [a0.lerp(a1, k / 6) for k in range(1, 7)]
    P += [Vector((0.0033 * math.cos(a_), 0, 0.024 + 0.0033 * math.sin(a_))) for a_ in np.linspace(math.pi * 0.75, math.pi * 0.25, 13)[1:]]
    b0 = P[-1]; b1 = Vector((0.011, 0, 0.012 + 0.0044))
    P += [b0.lerp(b1, k / 6) for k in range(1, 7)]
    P += [Vector((0.011 + 0.0044 * math.cos(a_), 0, 0.012 + 0.0044 * math.sin(a_))) for a_ in np.linspace(math.pi * 0.5, math.pi * 0.05, 6)[1:]]
    return P
_tp = tape_path(); TU_TOP = sum((_tp[i] - _tp[i - 1]).length for i in range(1, 19))              # tape length to the drum top (P[18] = straight up)
PIN_Y = [(c / 2.5 - 1.0) * 0.0051 for c in (1, 2, 3, 4)]               # the hole columns across the tape (column 2 = the small feed holes)
PIN_Z = 0.0274                                                         # pins ride on the tape on top of the drum
ROW = 0.0025
def tape_bit(row, col):
    """the same hash the tape shader uses (float32), so a pin drops exactly where the picture has a hole"""
    if col == 2: return True
    v = np.float32(math.sin(np.float32(row) * np.float32(12.9898) + np.float32(col) * np.float32(78.233))) * np.float32(43758.55)
    return float(v - math.floor(v)) > 0.45
def hole_depth(coord, col, deep=0.0009):
    """how far a pin at pattern coordinate 'coord' (m) on column 'col' sinks: into the hole when one passes under it"""
    row = math.floor(coord / ROW); cu = abs(coord / ROW - row - 0.5); r_ = 0.12 if col == 2 else 0.26
    return deep * (1.0 - smooth(r_ * 0.45, r_ * 0.95, cu)) if tape_bit(row, col) else 0.0
AL1, AL2 = 0.068, 0.066                                              # arm: upper and fore lengths (long, so it can reach the copy)
def build_robot(tag, loc, yaw=0.0):
    Rb = {'parts': []}
    root = empty(tag + '_root', loc=loc); root.rotation_euler = (0, 0, yaw); Rb['root'] = root
    def part(o, order=None):
        if order is not None: Rb['parts'].append((order, o))
        return o
    # body drum with rivets, the movement plate on top (gilt, perlage), a ring of rivets
    drum = part(lathe(tag + '_drum', [(0.0, -0.024), (0.046, -0.024), (0.05, -0.02), (0.05, -0.002), (0.049, 0.0), (0.0, 0.0)], 64, BRASS, root), 0)
    for k in range(24):
        a = 2 * math.pi * k / 24; part(prim('uv_sphere', tag + '_rivet', DSTEEL, root, loc=(0.0502 * math.cos(a), 0.0502 * math.sin(a), -0.012), segments=8, ring_count=5, radius=0.0012), 1)
    plate = part(cyl(tag + '_plate', 0.047, 0.0, 0.002, GILT, root, 64), 2)
    # the wheels: each turns about its own arbor (an empty), wheel + pinion + arbor + jewels
    Rb['wheels'] = {}
    for nm, n, m, z, th, pn, pm in TRAIN:
        c = LAYOUT[nm]; arb = empty(f'{tag}_{nm}', root, loc=(c.x, c.y, 0.0)); Rb['wheels'][nm] = arb
        g = part(gear(f'{tag}_{nm}_wheel', n, m, th, GILT if nm == 'barrel' else BRASS, 0 if nm in ('escape',) else (4 if nm != 'barrel' else 0),
                      'escape' if nm == 'escape' else 'wheel', arb, z), 10 + len(Rb['wheels']))
        if nm == 'barrel':
            part(cyl(f'{tag}_barrel_drum', 0.0168, z - 0.0035, z + 0.0002, GILT, arb, 64), 10)
            part(cyl(f'{tag}_barrel_cap', 0.0158, z + 0.0022, z + 0.0028, BRASS, arb, 64), 10)
            for k in range(3): part(screw(f'{tag}_bscrew{k}', arb, (0.009 * math.cos(2.1 * k), 0.009 * math.sin(2.1 * k), z + 0.0028), 0.0011), 10)
        if pn: part(gear(f'{tag}_{nm}_pinion', pn, pm, 0.0016, STEEL, 0, 'wheel', arb, z - 0.0028 if nm != 'escape' else z - 0.0024), 10 + len(Rb['wheels']))
        part(cyl(f'{tag}_{nm}_arbor', 0.0006, 0.0, 0.0205, STEEL, arb, 12), 10 + len(Rb['wheels']))
    # pallet fork (lever) and balance
    P_ = LAYOUT['fork']; E_ = LAYOUT['escape']; BL = LAYOUT['balance']
    fork = empty(tag + '_fork', root, loc=(P_.x, P_.y, 0.0)); Rb['fork'] = fork
    d_e = (E_ - P_).normalized(); d_b = (BL - P_).normalized()
    arm_pts = [(0, 0), (d_b.x * 0.008, d_b.y * 0.008), (d_e.x * 0.0035 + d_e.y * 0.0042, d_e.y * 0.0035 - d_e.x * 0.0042), (d_e.x * 0.0035 - d_e.y * 0.0042, d_e.y * 0.0035 + d_e.x * 0.0042)]
    part(solid(tag + '_fork_body', blob(arm_pts, [0.0009, 0.0006, 0.0006, 0.0006]), 0.0130, 0.0138, STEEL, fork), 20)
    for sg in (-1, 1):
        q = Vector((d_e.x * 0.0052 + sg * d_e.y * 0.0042, d_e.y * 0.0052 - sg * d_e.x * 0.0042))
        pal = part(box(f'{tag}_pallet{sg}', (0.0018, 0.0007, 0.0008), (q.x, q.y, 0.0134), RUBY, parent=fork), 20)
        pal.rotation_euler = (0, 0, math.atan2(d_e.y, d_e.x) + sg * 0.5)
    part(cyl(tag + '_fork_arbor', 0.0005, 0.0, 0.0205, STEEL, fork, 12), 20)
    bal = empty(tag + '_balance', root, loc=(BL.x, BL.y, 0.0)); Rb['balance'] = bal
    rim_o = [(0.011 * math.cos(2 * math.pi * i / 96), 0.011 * math.sin(2 * math.pi * i / 96)) for i in range(96)]
    rim_i = [(0.0098 * math.cos(2 * math.pi * i / 96), 0.0098 * math.sin(2 * math.pi * i / 96)) for i in range(96)]
    part(obj(tag + '_balance_rim', _ring_mesh(tag + '_rim', rim_o, rim_i, 0.0156, 0.0168), GILT, parent=bal), 21)
    for k in range(2): part(box(f'{tag}_balarm{k}', (0.0198, 0.0012, 0.0008), (0, 0, 0.016), GILT, rot=(0, 0, k * math.pi / 2), parent=bal), 21)
    for k in range(16):
        a = 2 * math.pi * k / 16; s_ = part(cyl(f'{tag}_tscrew{k}', 0.0005, 0.0, 0.0011, GILT, bal, 10, loc=(0.0114 * math.cos(a), 0.0114 * math.sin(a), 0.0162)), 21)
        s_.rotation_euler = (0, math.pi / 2, a); s_.rotation_mode = 'ZYX'
    part(cyl(tag + '_roller', 0.0018, 0.0128, 0.0136, STEEL, bal, 24), 21)
    part(cyl(tag + '_rollerpin', 0.0003, 0.0121, 0.0136, RUBY, bal, 10, loc=(0.0014, 0, 0)), 21)
    part(cyl(tag + '_bal_staff', 0.0004, 0.0, 0.0215, STEEL, bal, 12), 21)
    # hairspring: a curve redrawn every frame (it winds and unwinds as the balance swings)
    hs = bpy.data.curves.new(tag + '_hs', 'CURVE'); hs.dimensions = '3D'; hs.bevel_depth = 0.00011; hs.bevel_resolution = 2
    sp = hs.splines.new('POLY'); sp.points.add(239)
    hso = bpy.data.objects.new(tag + '_hairspring', hs); S.collection.objects.link(hso); hso.parent = root; hso.location = (BL.x, BL.y, 0.0146)
    hso.data.materials.append(BLUED); Rb['hairspring'] = hso; part(hso, 22)
    # bridges (gilt, skeleton shapes over the train), jewels at every pivot, blued screws
    c = {k: LAYOUT[k] for k in LAYOUT}
    zb = 0.0205
    br1 = part(solid(tag + '_bridge_barrel', blob([(c['barrel'].x, c['barrel'].y), (c['barrel'].x - 0.016, c['barrel'].y + 0.014)], [0.008, 0.004]), zb, zb + 0.0018, GILT, root), 30)
    # winding: a steel ratchet wheel on the barrel arbor over the bridge, a blued click that lets it turn one way only
    rat = part(gear(tag + '_ratchet', 30, 0.0006, 0.0011, RATCH, 0, 'ratchet', Rb['wheels']['barrel'], zb + 0.0019), 30)
    part(box(tag + '_ratsq', (0.0022, 0.0022, 0.0012), (0, 0, zb + 0.0034), DSTEEL, bv=0.0002, parent=Rb['wheels']['barrel']), 30)
    cpv = Vector((c['barrel'].x, c['barrel'].y)) + 0.0142 * Vector((math.cos(R(-50)), math.sin(R(-50))))
    clk = empty(tag + '_click', root, loc=(cpv.x, cpv.y, zb + 0.0019)); clk.rotation_euler = (0, 0, R(40 + 15)); Rb['click'] = clk; clk['base'] = R(55)
    part(box(tag + '_clickarm', (0.0062, 0.0011, 0.001), (0.0028, 0, 0.0005), BLUED, bv=0.0002, parent=clk), 30)
    part(screw(tag + '_clickscrew', clk, (0, 0, 0.001), 0.0009), 30)
    br2 = part(solid(tag + '_bridge_train', blob([(c[k].x, c[k].y) for k in ('centre', 'third', 'fourth', 'escape')], 0.0032), zb, zb + 0.0018, GILT, root), 31)
    cock = part(solid(tag + '_balance_cock', blob([(c['balance'].x, c['balance'].y), (c['balance'].x - 0.004, c['balance'].y - 0.012)], [0.0042, 0.0034]), zb + 0.001, zb + 0.0028, GILT, root), 32)
    for k in ('barrel', 'centre', 'third', 'fourth', 'escape'): part(jewel(f'{tag}_jewel_{k}', root, (c[k].x, c[k].y, zb + 0.0018)), 31)
    part(jewel(tag + '_jewel_bal', root, (c['balance'].x, c['balance'].y, zb + 0.0028), 0.0013), 32)
    part(jewel(tag + '_jewel_fork', root, (c['fork'].x, c['fork'].y, zb + 0.0001), 0.0008), 31)
    for k, (x, y, z) in enumerate([(c['barrel'].x - 0.016, c['barrel'].y + 0.014, zb + 0.0018), (c['centre'].x - 0.003, c['centre'].y - 0.0035, zb + 0.0018),
                                    (c['escape'].x + 0.0035, c['escape'].y - 0.002, zb + 0.0018), (c['balance'].x - 0.004, c['balance'].y - 0.012, zb + 0.0028)]):
        part(screw(f'{tag}_brscrew{k}', root, (x, y, z)), 33)
    # head: brass dome with a big lens; the iris glows amber when it's awake ('on' on the iris)
    head = empty(tag + '_head', root, loc=(0.052, 0.0, -0.004)); Rb['head'] = head
    hd = part(prim('uv_sphere', tag + '_headdome', BRASS, head, loc=(0, 0, 0), segments=48, ring_count=24, radius=0.017, scale=(0.9, 1.0, 0.85)), 60)
    part(lathe(tag + '_lensrim', [(0.0112, -0.0015), (0.0118, -0.0015), (0.0118, 0.0018), (0.0102, 0.0024), (0.0098, 0.0012), (0.0112, 0.0012)], 48, DSTEEL, head, loc=(0.0145, 0, 0.001)), 60)
    hd2 = Rb['parts'][-1][1]; hd2.rotation_euler = (0, math.pi / 2, 0)
    lens = part(prim('uv_sphere', tag + '_lens', GLASS, head, loc=(0.0152, 0, 0.001), segments=32, ring_count=16, radius=0.0102, scale=(0.45, 1, 1)), 60)
    iris = part(cyl(tag + '_iris', 0.0085, -0.0003, 0.0003, EYE_M, head, 48, loc=(0.0142, 0, 0.001)), 60); iris.rotation_euler = (0, math.pi / 2, 0); iris['on'] = 0.0
    Rb['iris'] = iris
    for sg in (-1, 1): part(cyl(f'{tag}_ear{sg}', 0.004, -0.002, 0.002, BRASS, head, 24, loc=(0, sg * 0.0165, 0.002)), 60).rotation_euler = (math.pi / 2, 0, 0)
    # legs: 6, around the drum. Each: hip (yaw) -> femur (pitch) -> knee -> tibia (pitch) -> foot
    Rb['legs'] = []
    for k, ang in enumerate((40, 90, 140, -140, -90, -40)):
        a = R(ang); hip = empty(f'{tag}_hip{k}', root, loc=(0.05 * math.cos(a), 0.05 * math.sin(a), -0.013)); hip.rotation_euler = (0, 0, a)
        fem = empty(f'{tag}_fem{k}', hip, loc=(0.006, 0, 0)); tib = empty(f'{tag}_tib{k}', fem, loc=(0.048, 0, 0))
        o = 40 + k
        part(cyl(f'{tag}_hipcap{k}', 0.0055, -0.004, 0.004, BRASS, hip, 24), o)
        part(prim('cylinder', f'{tag}_hipgear{k}', BRASS, hip, loc=(0.003, 0, 0.0045), vertices=24, radius=0.004, depth=0.0012), o)
        for sg in (-1, 1): part(box(f'{tag}_fplate{k}{sg}', (0.052, 0.0014, 0.007), (0.024, sg * 0.0034, 0), BRASS, bv=0.0006, parent=fem), o)
        part(cyl(f'{tag}_knee{k}', 0.0032, -0.005, 0.005, STEEL, tib, 20), o).rotation_euler = (math.pi / 2, 0, 0)
        part(lathe(f'{tag}_tibrod{k}', [(0.0, 0.0), (0.0024, 0.0), (0.0018, 0.06), (0.0, 0.06)], 16, STEEL, tib), o).rotation_euler = (0, math.pi / 2, 0)
        part(prim('uv_sphere', f'{tag}_foot{k}', DSTEEL, tib, loc=(0.063, 0, 0), segments=16, ring_count=8, radius=0.0042, scale=(1, 1, 0.8)), o)
        part(cyl(f'{tag}_fpin{k}', 0.0012, -0.005, 0.005, STEEL, fem, 12), o).rotation_euler = (math.pi / 2, 0, 0)
        Rb['legs'].append((hip, fem, tib, a))
    # arms: 2 at the front sides. shoulder (yaw) -> upper (pitch) -> fore (pitch) -> wrist (pitch) -> two fingers (slide)
    Rb['arms'] = []
    for k, sg in enumerate((1, -1)):
        sh = empty(f'{tag}_sh{k}', root, loc=(0.036, sg * 0.036, -0.004)); up = empty(f'{tag}_up{k}', sh, loc=(0, 0, 0.006))
        fo = empty(f'{tag}_fo{k}', up, loc=(AL1, 0, 0)); wr = empty(f'{tag}_wr{k}', fo, loc=(AL2, 0, 0))
        o = 50 + k
        part(cyl(f'{tag}_turret{k}', 0.0068, -0.006, 0.006, BRASS, sh, 32), o)
        for s2 in (-1, 1): part(box(f'{tag}_uplate{k}{s2}', (AL1 + 0.004, 0.0013, 0.0065), (AL1 / 2, s2 * 0.0042, 0), BRASS, bv=0.0006, parent=up), o)
        part(cyl(f'{tag}_elbow{k}', 0.0034, -0.0055, 0.0055, STEEL, fo, 20), o).rotation_euler = (math.pi / 2, 0, 0)
        part(lathe(f'{tag}_forerod{k}', [(0.0, 0.0), (0.0026, 0.0), (0.0021, AL2 - 0.002), (0.0, AL2 - 0.002)], 16, STEEL, fo), o).rotation_euler = (0, math.pi / 2, 0)
        part(box(f'{tag}_wrist{k}', (0.01, 0.009, 0.006), (0.004, 0, 0), BRASS, bv=0.001, parent=wr), o)
        fingers = []
        for s2 in (-1, 1):
            fg = empty(f'{tag}_fg{k}{s2}', wr, loc=(0.009, s2 * 0.0025, 0)); fingers.append((fg, s2))
            part(box(f'{tag}_finger{k}{s2}', (0.014, 0.0011, 0.004), (0.007, 0, 0), STEEL, bv=0.0004, parent=fg), o)
            part(box(f'{tag}_fpad{k}{s2}', (0.005, 0.0006, 0.0034), (0.0115, -s2 * 0.0008, 0), DSTEEL, parent=fg), o)
        Rb['arms'].append((sh, up, fo, wr, fingers))
    # backpack: the tape reader. Two spools, a reader drum with five pins; the tape runs spool -> drum -> spool
    bp = empty(tag + '_pack', root, loc=(-0.066, 0.0, 0.004)); Rb['pack'] = bp
    part(box(tag + '_packbase', (0.034, 0.03, 0.006), (0.0, 0, -0.012), BRASS, bv=0.0012, parent=bp), 70)
    for sg in (-1, 1):
        part(box(f'{tag}_packcheek{sg}', (0.034, 0.002, 0.03), (0.0, sg * 0.0085, 0.004), BRASS, bv=0.0008, parent=bp), 70)
    spools = []
    for k, xx in enumerate((-0.011, 0.011)):
        sp_ = empty(f'{tag}_spool{k}', bp, loc=(xx, 0, 0.012)); sp_.rotation_euler = (math.pi / 2, 0, 0); spools.append(sp_)
        for sg in (-1, 1): part(cyl(f'{tag}_flange{k}{sg}', 0.0085, -0.0003, 0.0003, BRASS, sp_, 32, loc=(0, 0, sg * 0.0062)), 71)
        part(cyl(f'{tag}_hubs{k}', 0.0025, -0.0062, 0.0062, STEEL, sp_, 16), 71)
    Rb['spools'] = spools
    roll = [part(cyl(f'{tag}_roll{k}', 0.0068 - 0.0025 * k, -0.0058, 0.0058, TAPE_M, spools[k], 48), 72) for k in range(2)]
    for r_ in roll: r_['punched'] = 9.0; r_['off'] = 0.0; r_['lit'] = 0.0; r_['readat'] = 0.0
    drum_r = empty(tag + '_reader', bp, loc=(0.0, 0, 0.024)); drum_r.rotation_euler = (math.pi / 2, 0, 0)
    part(cyl(tag + '_readdrum', 0.0032, -0.0058, 0.0058, STEEL, drum_r, 32), 71)
    pins = []
    for k, cy in enumerate(PIN_Y):
        pn_ = empty(f'{tag}_pin{k}', bp, loc=(0.0, cy, PIN_Z)); pins.append(pn_)
        part(cyl(f'{tag}_pinrod{k}', 0.00022 if k == 1 else 0.00034, 0.0, 0.0072, STEEL, pn_, 8), 71)
        part(prim('uv_sphere', f'{tag}_pinball{k}', BLUED, pn_, loc=(0, 0, 0.0072), segments=10, ring_count=6, radius=0.00075), 71)
    part(box(tag + '_pinguide', (0.0035, 0.0175, 0.0012), (0.0, 0, PIN_Z + 0.005), BRASS, bv=0.0003, parent=bp), 71)
    Rb['pins'] = pins
    # the tape strip: from the top of spool 0, over the drum, down to spool 1 (a ribbon with 'tu' = metres along, 'tv' across)
    path = tape_path()
    tape = ribbon(tag + '_tape', path, 0.0102, bp); part(tape, 72); Rb['tape'] = tape
    for r_ in [tape]: r_['punched'] = 9.0; r_['off'] = 0.0; r_['lit'] = 0.0; r_['readat'] = TU_TOP
    Rb['parts'].sort(key=lambda x: x[0])
    return Rb
def ribbon(name, path, w, parent):
    vs, tus, tvs = [], [], []; acc = 0.0
    for i, p in enumerate(path):
        if i: acc += (p - path[i - 1]).length
        for sg in (-1, 1): vs.append((p.x, sg * w / 2, p.z)); tus.append(acc); tvs.append(sg * 1.0)
    fs = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(path) - 1)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); o = obj(name, me, TAPE_M, parent=parent)
    a1 = me.attributes.new('tu', 'FLOAT', 'POINT'); a1.data.foreach_set('value', tus); a2 = me.attributes.new('tv', 'FLOAT', 'POINT'); a2.data.foreach_set('value', tvs)
    sol = o.modifiers.new('th', 'SOLIDIFY'); sol.thickness = 0.00012; return o

# ================================================================ THE WORKBENCH (z = 0 the bench top; metres)
BENCH = box('bench', (1.6, 0.8, 0.05), (0.05, 0.0, -0.025), WALNUT, bv=0.004)
FLOOR = box('floor', (8, 8, 0.02), (0, 0, -0.76), mat('floor', (0.12, 0.1, 0.09), 0.7))
WALL = box('wall', (4, 0.05, 2.0), (0, 0.42, 0.6), noisy(mat('wall', (0.32, 0.3, 0.27), 0.9), 40.0, 0.06))
PEG_M = noisy(mat('pegboard', (0.42, 0.33, 0.22), 0.8), 200.0, 0.1)
PEG = box('pegboard', (1.2, 0.012, 0.55), (0.05, 0.39, 0.36), PEG_M)
for i in range(22):
    for j in range(10): prim('cylinder', 'peghole', mat('hole', (0.03, 0.025, 0.02), 0.9), loc=(-0.5 + i * 0.05, 0.383, 0.12 + j * 0.05), rot=(math.pi / 2, 0, 0), vertices=8, radius=0.004, depth=0.002)
TOOLS = []
for k, (x, ln, col) in enumerate(((-0.35, 0.16, (0.7, 0.1, 0.08)), (-0.28, 0.14, (0.1, 0.25, 0.6)), (-0.2, 0.12, (0.85, 0.65, 0.1)))):    # screwdrivers
    TOOLS.append(cyl('drv_h%d' % k, 0.009, 0.0, 0.06, mat('drvh%d' % k, col, 0.3, coat=0.6), None, 20, loc=(x, 0.37, 0.48)))
    TOOLS.append(cyl('drv_s%d' % k, 0.0025, -ln, 0.0, STEEL, None, 12, loc=(x, 0.37, 0.48)))
TWEEZ = [box('tweez%d' % s_, (0.004, 0.0015, 0.12), (-0.1 + 0.003 * s_, 0.372, 0.43), STEEL, rot=(0, R(2 * s_), 0)) for s_ in (-1, 1)]
# the parts tray (walnut, 3 x 2 compartments) with loose gears, screws and springs in it
TRAY_C = Vector((0.03, 0.135, 0.0))
TRAY = [box('tray_base', (0.16, 0.11, 0.004), TRAY_C + Vector((0, 0, 0.002)), WALNUT, bv=0.001)]
for k in range(4): TRAY.append(box('tray_x%d' % k, (0.004, 0.11, 0.018), TRAY_C + Vector((-0.078 + k * 0.052, 0, 0.009)), WALNUT, bv=0.0008))
for k in range(3): TRAY.append(box('tray_y%d' % k, (0.16, 0.004, 0.018), TRAY_C + Vector((0, -0.053 + k * 0.053, 0.009)), WALNUT, bv=0.0008))
_rng = random.Random(5)
LOOSE = []
for ci in range(3):
    for cj in range(2):
        cc = TRAY_C + Vector((-0.052 + ci * 0.052, -0.026 + cj * 0.052, 0.004))
        for q in range(9 if (ci, cj) != (1, 0) else 4):
            n_ = _rng.choice((24, 30, 40, 48)); g_ = gear('loose_%d_%d_%d' % (ci, cj, q), n_, 0.0004, 0.0009, _rng.choice((BRASS, BRASS, GILT, STEEL)), 4 if n_ > 24 else 0)
            g_.location = cc + Vector((_rng.uniform(-0.016, 0.016), _rng.uniform(-0.016, 0.016), 0.0006 + q * 0.0011)); g_.rotation_euler = (_rng.uniform(-0.2, 0.2), _rng.uniform(-0.2, 0.2), _rng.uniform(0, 6.3))
            LOOSE.append(g_)
PICK_HOME = TRAY_C + Vector((0.0, -0.026, 0.0105))                    # the next centre wheel waits in the near middle compartment (wheel, pinion, arbor)
PICK = empty('pick', loc=PICK_HOME - Vector((0, 0, 0.006)))
gear('pick_wheel', 64, 0.0004, 0.0011, BRASS, 4, 'wheel', PICK, 0.006); gear('pick_pinion', 12, 0.0005, 0.0016, STEEL, 0, 'wheel', PICK, 0.0032)
cyl('pick_arbor', 0.0006, 0.0, 0.0205, STEEL, PICK, 12)
# desk lamp (articulated) and the light: warm lamp key, cool window fill, a rim from behind
LAMP_M = metal('lamp', (0.08, 0.09, 0.1), 0.35)
LAMPG = [cyl('lamp_base', 0.07, 0.0, 0.012, LAMP_M, None, 40, loc=(0.42, 0.22, 0.0)), cyl('lamp_post', 0.006, 0.0, 0.32, LAMP_M, None, 12, loc=(0.42, 0.22, 0.0))]
_arm2 = cyl('lamp_arm', 0.005, 0.0, 0.3, LAMP_M, None, 12, loc=(0.42, 0.22, 0.32)); _arm2.rotation_euler = (R(-40), R(-35), 0); LAMPG.append(_arm2)
_shade = lathe('lamp_shade', [(0.02, 0.0), (0.075, -0.09), (0.072, -0.092), (0.018, -0.002)], 48, LAMP_M, None, loc=(0.26, 0.08, 0.5)); _shade.rotation_euler = (R(25), R(-30), 0); LAMPG.append(_shade)
def light_at(name, kind, loc, target, energy, col, size=0.3, spot=None):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    if spot: lt.spot_size = spot; lt.spot_blend = 0.6
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
KEY = light_at('lamp_key', 'SPOT', (0.25, 0.06, 0.47), (0.05, -0.08, 0.0), 22, (1.0, 0.76, 0.5), 0.03, R(70))
FILLL = light_at('window_fill', 'AREA', (-0.9, -0.6, 0.8), (0.05, -0.05, 0.03), 22, (0.55, 0.68, 1.0), 1.4)
RIM = light_at('rim', 'AREA', (-0.25, 0.35, 0.35), (0.05, -0.08, 0.03), 18, (1.0, 0.88, 0.75), 0.5)
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; WBG = W_.node_tree.nodes['Background']; WBG.inputs['Color'].default_value = (0.012, 0.011, 0.012, 1)
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.002
SHOP = [BENCH, FLOOR, WALL, PEG, KEY, FILLL, RIM] + TOOLS + TWEEZ + TRAY + LOOSE + LAMPG + [o for o in bpy.data.objects if o.name.startswith('peghole')]

# ================================================================ THE TWO ROBOTS
P_HOME = Vector((-0.02, -0.04, 0.0)); P_YAW = 0.0                   # where the builder stands at frame one (tray on its left, the copy ahead)
C_POS = Vector((0.11, -0.07, 0.0)); C_YAW = R(90)                   # where the copy is built (on a little three-pin jig; its pack faces the front)
P_ASIDE = Vector((0.11, -0.27, 0.0)); P_ASIDE_YAW = R(90)           # where the builder works from once the copy has legs (facing its pack)
STAND_Z = 0.048; CROUCH_Z = 0.034
ROB = build_robot('par', P_HOME + Vector((0, 0, STAND_Z)), P_YAW)
KID = build_robot('kid', C_POS + Vector((0, 0, CROUCH_Z)), C_YAW)
JIG = [cyl('jig_base', 0.03, 0.0, 0.003, BRASS, None, 40, loc=(C_POS.x, C_POS.y, 0.0))] + \
      [cyl('jig_pin%d' % k, 0.0025, 0.0, CROUCH_Z - 0.024, STEEL, None, 12, loc=(C_POS.x + 0.022 * math.cos(2.1 * k), C_POS.y + 0.022 * math.sin(2.1 * k), 0.0)) for k in range(3)]
SHOP += JIG
# ---- the tape copier on the bench: the builder's tape (back) and a blank tape (front) run side by side under an open bridge. On the
#      back tape four pins ride and drop into its holes; each pin is linked by a rocker to a punch over the blank tape: pin drops, punch strikes
COPIER_C = Vector((-0.17, -0.2, 0.0)); CTZ = 0.0202                  # the tapes run flat at this height over the die bed
COP = [box('cop_base', (0.12, 0.05, 0.012), COPIER_C + Vector((0, 0, 0.006)), BRASS, bv=0.002),
       box('cop_die', (0.03, 0.044, 0.008), COPIER_C + Vector((0, 0, 0.016)), DSTEEL, bv=0.0008)]
for sg in (-1, 1): COP.append(box('cop_post%d' % sg, (0.007, 0.004, 0.033), COPIER_C + Vector((0, sg * 0.024, 0.0365)), BRASS, bv=0.0008))
COP.append(box('cop_bridge', (0.009, 0.054, 0.004), COPIER_C + Vector((0, 0, 0.053)), BRASS, bv=0.0008))
COP.append(box('cop_chute', (0.014, 0.012, 0.004), COPIER_C + Vector((0.0, -0.028, 0.011)), DSTEEL, bv=0.0006, rot=(R(-25), 0, 0)))
for k in range(2):
    COP.append(cyl('cop_roller%d' % k, 0.004, -0.022, 0.022, STEEL, None, 24, loc=COPIER_C + Vector((-0.045 + 0.09 * k, 0, CTZ - 0.0041)))); COP[-1].rotation_euler = (math.pi / 2, 0, 0)
    for sg in (-1, 1): COP.append(box('cop_cheek%d%d' % (k, sg), (0.012, 0.003, 0.012), COPIER_C + Vector((-0.045 + 0.09 * k, sg * 0.0235, 0.016)), BRASS, bv=0.0006))
def straight_tape(name, x0, x1, z, y, w=0.0102):
    pts = [Vector((x0 + (x1 - x0) * k / 60, 0, z)) for k in range(61)]; o = ribbon(name, pts, w, None); o.location = (0, y, 0); return o
TAPE_A = straight_tape('cop_tape_src', COPIER_C.x - 0.07, COPIER_C.x + 0.07, CTZ, COPIER_C.y + 0.009)
TAPE_B = straight_tape('cop_tape_new', COPIER_C.x - 0.07, COPIER_C.x + 0.07, CTZ, COPIER_C.y - 0.009)
for o in (TAPE_A, TAPE_B): o['punched'] = 9.0; o['off'] = 0.0; o['lit'] = 0.0; o['readat'] = 0.07
CPINS, PUNCH, ROCK = [], [], []
for k, cy in enumerate(PIN_Y):
    pn_ = empty('cpin%d' % k, loc=COPIER_C + Vector((0, 0.009 + cy, CTZ + 0.0002))); CPINS.append(pn_)
    cyl('cpinrod%d' % k, 0.00022 if k == 1 else 0.00034, 0.0, 0.035, STEEL, pn_, 8); prim('uv_sphere', 'cpinball%d' % k, BLUED, pn_, loc=(0, 0, 0.035), segments=10, ring_count=6, radius=0.00075)
    pu = empty('punch%d' % k, loc=COPIER_C + Vector((0, -0.009 + cy, CTZ + 0.003))); PUNCH.append(pu)
    cyl('punchrod%d' % k, 0.00024 if k == 1 else 0.00045, 0.0, 0.033, STEEL, pu, 10); cyl('punchcap%d' % k, 0.0009, 0.0325, 0.035, DSTEEL, pu, 12)
    ROCK.append(cyl('rocker%d' % k, 0.00028, 0.0, 1.0, BLUED, None, 8))           # a rod from the pin's top to the punch's top (stretched each frame)
CHIP_M = mat('chip', (0.86, 0.8, 0.66), 0.8)
CHIPS = [prim('cylinder', 'chip%d' % k, CHIP_M, None, loc=(0, 0, -1), vertices=10, radius=0.0006, depth=0.00012) for k in range(30)]
_cr = random.Random(11)
CHIPPILE = [prim('cylinder', 'chippile%d' % k, CHIP_M, None, loc=COPIER_C + Vector((_cr.gauss(0.0, 0.006), -0.036 + _cr.gauss(0, 0.004), 0.00006 + 0.00012 * (k % 3))),
                 rot=(_cr.uniform(-0.3, 0.3), _cr.uniform(-0.3, 0.3), 0), vertices=10, radius=0.0006, depth=0.00012) for k in range(60)]
COPIER = COP + [TAPE_A, TAPE_B] + [o for o in bpy.data.objects if o.name.startswith(('cpin', 'punch'))] + ROCK + CHIPS + CHIPPILE
SHOP += COPIER
def rod_between(o, p, q):
    d = q - p; o.location = p; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); o.scale = (1, 1, d.length)
def copier(lt, run=True):
    """the tapes move (holes come out of the punch on the blank tape); pins sink where the source tape has holes; punches strike"""
    off = -0.06 + lt * 0.02 if run else 0.0
    TAPE_A['off'] = off; TAPE_B['off'] = off; TAPE_B['punched'] = 0.07 + off
    TAPE_A['lit'] = 1.0 if run else 0.0
    coord = 0.07 + off; fired = []
    for k, (pn_, pu, rk) in enumerate(zip(CPINS, PUNCH, ROCK)):
        d = hole_depth(coord, k + 1, 0.0011) if run else 0.0; pn_.location.z = CTZ + 0.0002 - d
        hit = d / 0.0011; pu.location.z = CTZ + 0.003 - 0.0042 * hit; fired.append(hit)
        rod_between(rk, pn_.location + Vector((0, 0, 0.035)), pu.location + Vector((0, 0, 0.035)))
    return fired
# ---- DNA (1953): two strands wound into a double helix with rungs; and a cell splitting (metaballs) -- both in a dark set of their own
DO = Vector((0.0, 3.0, 0.3))
def helix_strand(name, ph, mt, n=220, turns=4.0, r=0.03, h=0.24):
    pts = [Vector((r * math.cos(ph + 2 * math.pi * turns * k / (n - 1)), r * math.sin(ph + 2 * math.pi * turns * k / (n - 1)), -h / 2 + h * k / (n - 1))) for k in range(n)]
    o = tube(name, pts, 0.0035, mt, seg=10); o.location = DO; return o, pts
STRAND_M = mat('strand', (0.9, 0.82, 0.62), 0.35, coat=0.5, emit=(1.0, 0.7, 0.35), estr=0.4)
DNA = []
_s1, P1 = helix_strand('dna_a', 0.0, STRAND_M); _s2, P2 = helix_strand('dna_b', math.pi * 0.8, STRAND_M); DNA += [_s1, _s2]
BASE_COLS = [(0.95, 0.3, 0.2), (0.25, 0.6, 1.0), (0.3, 0.9, 0.4), (1.0, 0.8, 0.2)]
for k in range(0, 220, 6):
    a_, b_ = P1[k], P2[k]; mid = (a_ + b_) * 0.5
    for half, (p, q) in enumerate(((a_, mid), (mid, b_))):
        cm = mat('base%d' % ((k // 6 + half) % 4), BASE_COLS[(k // 6 + half * 2) % 4], 0.35, emit=BASE_COLS[(k // 6 + half * 2) % 4], estr=1.2)
        o = tube('rung%d_%d' % (k, half), [p, q], 0.0016, cm, seg=8); o.location = DO; DNA.append(o)
DNA_ROOT = empty('dna_root', loc=DO)
for o in DNA: o.parent = DNA_ROOT; o.location = (0, 0, 0)
# a cell splitting, drawn like a glowing microscope image: a clear membrane (metaballs that pinch in two), four chromosomes (each two
# sister copies joined in an X) lined up in the middle, spindle fibres from the two poles pull the copies apart, one of each to each side
CO = Vector((0.0, 6.0, 0.3))
CELL_M = bpy.data.materials.new('cell'); CELL_M.use_nodes = True; _nt = CELL_M.node_tree; _cb = _nt.nodes['Principled BSDF']
_cb.inputs['Base Color'].default_value = (0.7, 0.85, 1.0, 1); _cb.inputs['Transmission Weight'].default_value = 1.0; _cb.inputs['Roughness'].default_value = 0.08
_cb.inputs['IOR'].default_value = 1.12
_lw = _nt.nodes.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.25
_cb.inputs['Emission Color'].default_value = (0.25, 0.6, 1.0, 1); L(CELL_M, math_(_nt, 'MULTIPLY', math_(_nt, 'POWER', _lw.outputs['Facing'], 3.0), 2.2), _cb.inputs['Emission Strength'])
_vol = _nt.nodes.new('ShaderNodeVolumePrincipled'); _vol.inputs['Color'].default_value = (0.4, 0.7, 1.0, 1); _vol.inputs['Density'].default_value = 3.0
_vol.inputs['Emission Color'].default_value = (0.15, 0.35, 0.8, 1); _vol.inputs['Emission Strength'].default_value = 0.6
L(CELL_M, _vol.outputs['Volume'], _nt.nodes['Material Output'].inputs['Volume'])
mb = bpy.data.metaballs.new('cell'); mb.resolution = 0.006; mb.render_resolution = 0.003; mb.threshold = 0.6
CELL = bpy.data.objects.new('cell', mb); S.collection.objects.link(CELL); CELL.location = CO; mb.materials.append(CELL_M)
CB = [mb.elements.new() for _ in range(2)]
for e in CB: e.radius = 0.1; e.stiffness = 2.0
CHR_M = mat('chromosome', (1.0, 0.35, 0.12), 0.4, emit=(1.0, 0.32, 0.08), estr=5.0)
SPN_M = mat('spindle', (0.6, 1.0, 0.7), 0.5, emit=(0.45, 1.0, 0.6), estr=4.0)
CEN_M = mat('centrosome', (1.0, 1.0, 0.8), 0.3, emit=(1.0, 0.95, 0.7), estr=20.0)
ORG_M = mat('organelle', (0.3, 1.0, 0.7), 0.4, emit=(0.25, 0.9, 0.6), estr=2.0)
_xr = random.Random(7)
CHROMS = []                                                           # (chromatid object, side -1/+1, plate spot, tilt)
for i in range(4):
    th = 2 * math.pi * i / 4 + 0.4; spot = Vector((0.0, 0.026 * math.cos(th), 0.026 * math.sin(th))); ln = _xr.uniform(0.011, 0.016)
    for sg in (-1, 1):
        pts = [Vector((sg * (0.0016 + 0.0028 * (zz / ln) ** 2), 0.0, zz)) for zz in np.linspace(-ln, ln, 18)]
        o = tube('chromatid%d_%d' % (i, sg), pts, lambda u_: 0.0021 * (0.55 + 0.45 * math.sin(math.pi * u_) ** 0.4), CHR_M, seg=12); o.location = CO
        CHROMS.append((o, sg, spot, (_xr.uniform(-0.5, 0.5), th)))
POLES = [prim('uv_sphere', 'centrosome%d' % k, CEN_M, None, loc=CO, segments=16, ring_count=8, radius=0.0035) for k in range(2)]
SPINDLE = [cyl('spindle%d' % k, 0.00035, 0.0, 1.0, SPN_M, None, 6) for k in range(len(CHROMS) + 12)]
ORGS = []
for k in range(70):
    d = Vector((_xr.gauss(0, 1), _xr.gauss(0, 1), _xr.gauss(0, 1))).normalized() * _xr.uniform(0.035, 0.07)
    ORGS.append((prim('uv_sphere', 'organelle%d' % k, ORG_M, None, loc=CO, segments=10, ring_count=6, radius=_xr.uniform(0.0015, 0.0035)), d, -1 if d.x < 0 else 1))
NUCS = []
CELLSET = [CELL] + [c[0] for c in CHROMS] + POLES + SPINDLE + [o for o, _, _ in ORGS]
VKEY = light_at('void_key', 'AREA', DO + Vector((-0.4, -0.5, 0.5)), DO, 30, (1.0, 0.9, 0.8), 0.6)
VRIM = light_at('void_rim', 'AREA', DO + Vector((0.4, 0.5, 0.2)), DO, 30, (0.5, 0.7, 1.0), 0.6)
CKEY = light_at('cell_key', 'AREA', CO + Vector((-0.4, -0.5, 0.5)), CO, 12, (0.8, 0.9, 1.0), 0.8)
CRIM = light_at('cell_rim', 'AREA', CO + Vector((0.5, 0.5, 0.1)), CO, 30, (0.4, 0.65, 1.0), 0.8)
# DNA: drifting specks around it (out of focus, they read as soft glints)
_dr = random.Random(3); SPECK_M = mat('speck', (0.6, 0.8, 1.0), 0.5, emit=(0.55, 0.75, 1.0), estr=6.0)
SPECKS = [prim('uv_sphere', 'speck%d' % k, SPECK_M, None, loc=DO + Vector((_dr.uniform(-0.25, 0.25), _dr.uniform(-0.15, 0.35), _dr.uniform(-0.2, 0.2))),
               segments=8, ring_count=4, radius=_dr.uniform(0.0006, 0.0018)) for k in range(70)]
DNA += SPECKS
VOID = DNA + [DNA_ROOT, VKEY, VRIM] + CELLSET + [CKEY, CRIM]
MZ = Matrix.Rotation(-math.pi / 2, 3, 'Y'); CELL.rotation_euler = (0, -math.pi / 2, 0)       # the cell divides along the frame's tall side
def cz(v): return CO + MZ @ Vector(v)
def mitosis(k, t):
    """k 0..1: chromosomes on the middle plate -> sister copies pulled to the two poles -> the cell pinches in two (top and bottom)"""
    pull = smooth(0.12, 0.75, k); pinch = smooth(0.35, 1.0, k)
    CB[0].co = (-0.075 * pinch, 0, 0); CB[1].co = (0.075 * pinch, 0, 0)
    for e in CB: e.radius = 0.1 - 0.022 * pinch
    pole = [cz((sg * (0.062 + 0.03 * pinch), 0, 0)) for sg in (-1, 1)]
    for o, pp in zip(POLES, pole): o.location = pp
    for i, (o, sg, spot, (tilt, th)) in enumerate(CHROMS):
        sep = pull
        ctr = Vector((sg * (0.0005 + 0.058 * sep), spot.y * (1 - 0.55 * sep), spot.z * (1 - 0.55 * sep))) + Vector((0, wob(t, 0.7, i + sg), wob(t, 0.7, i + 5 + sg))) * 0.0012
        o.matrix_world = Matrix.Translation(cz(ctr)) @ MZ.to_4x4() @ Euler((th + tilt, R(-28) * sg * sep, 0)).to_matrix().to_4x4()
    for j, sp_ in enumerate(SPINDLE):
        if j < len(CHROMS):
            o, sg, _, _ = CHROMS[j]; rod_between(sp_, pole[0 if sg < 0 else 1], o.matrix_world.translation)
        else:                                                         # the astral rays out from each pole
            jj = j - len(CHROMS); sg = -1 if jj < 6 else 1; a_ = 2 * math.pi * (jj % 6) / 6 + 0.3
            p0 = pole[0 if sg < 0 else 1]; rod_between(sp_, p0, p0 + MZ @ Vector((sg * 0.012, 0.016 * math.cos(a_), 0.016 * math.sin(a_))))
    for o, d, sg in ORGS: o.location = cz(Vector((sg * 0.075 * pinch, 0, 0)) + d * (1 - 0.2 * pinch) + Vector((wob(t, 0.4, d.x * 9), wob(t, 0.4, d.y * 9), wob(t, 0.4, d.z * 9))) * 0.003)
# compositor glow
try:
    ct_ = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); S.compositing_node_group = ct_
    rl_ = ct_.nodes.new('CompositorNodeRLayers'); gl_ = ct_.nodes.new('CompositorNodeGlare'); gl_.inputs['Type'].default_value = 'Bloom'
    for k_, v_ in (('Threshold', 1.4), ('Strength', 0.3), ('Size', 0.5)):
        try: gl_.inputs[k_].default_value = v_
        except Exception: pass
    out_ = ct_.nodes.new('NodeGroupOutput'); ct_.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ct_.links.new(rl_.outputs['Image'], gl_.inputs['Image']); ct_.links.new(gl_.outputs['Image'], out_.inputs[0]); print('glow on')
except Exception as e_: print('glow skipped', e_)

# ================================================================ MOTION
FB = 2.5                                                            # balance: 2.5 swings a second = 5 ticks a second
def movement(Rb, t, amp=1.0, run=1.0):
    """balance swings (amp 0..1 of 220 deg); every tick (the balance passing the middle) the fork flips and the escape wheel steps half a
    tooth; the rest of the train follows by its tooth ratios. run = 0 -> stopped"""
    ph = 2 * math.pi * FB * t; ba = R(220) * amp * math.sin(ph)
    Rb['balance'].rotation_euler = (0, 0, ba)
    beats = 2 * FB * t; nb_ = math.floor(beats); fr = beats - nb_
    step = (nb_ + smooth(0.0, 0.12, fr)) * run if amp > 0.05 else 0.0
    esc = -(2 * math.pi / 15) * 0.5 * step
    for nm, arb in Rb['wheels'].items(): arb.rotation_euler = (0, 0, esc * RATIO[nm])
    click(Rb)
    sgn = 1.0 if (nb_ % 2 == 0) else -1.0
    Rb['fork'].rotation_euler = (0, 0, R(9) * amp * (sgn * (2 * smooth(0.0, 0.1, fr) - 1)) * (1 if amp > 0.05 else 0))
    # hairspring: inner end turns with the balance, outer end fixed; the coils open and close
    pts = Rb['hairspring'].data.splines[0].points; n = len(pts); turns = 9.0
    for i, p in enumerate(pts):
        s_ = i / (n - 1); r_ = 0.0011 + (0.0072 - 0.0011) * s_; th = 2 * math.pi * turns * s_ + ba * (1 - s_)
        r_ *= 1.0 - 0.06 * (ba / R(220)) * (1 - s_) * s_ * 4
        p.co = (r_ * math.cos(th), r_ * math.sin(th), 0.0, 1.0)
def click(Rb):
    ph = -Rb['wheels']['barrel'].rotation_euler.z / (2 * math.pi / 30); fr = ph - math.floor(ph)
    Rb['click'].rotation_euler = (0, 0, Rb['click']['base'] + R(9) * (smooth(0.0, 0.85, fr) - smooth(0.88, 1.0, fr) * 1.0) * 0.6)
def two_link(dx, dz, L1, L2):
    D = min(math.hypot(dx, dz), L1 + L2 - 1e-5); a = math.atan2(dz, dx)
    b = math.acos(clamp((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1)); th1 = a + b
    kx, kz = L1 * math.cos(th1), L1 * math.sin(th1); th2 = math.atan2(dz - kz, dx - kx); return th1, th2
def legs(Rb, feet):
    """feet: 6 world points (foot centres); hips swing to face them; femur up, tibia down (knees high, like a spider)"""
    root = Rb['root']; Mi = root.matrix_world.inverted()
    for (hip, fem, tib, a), fw in zip(Rb['legs'], feet):
        fl = Mi @ fw; hx, hy, hz = hip.location
        yaw = math.atan2(fl.y - hy, fl.x - hx); hip.rotation_euler = (0, 0, yaw)
        d = math.hypot(fl.x - hx, fl.y - hy) - 0.006; th1, th2 = two_link(d, fl.z - hz, 0.048, 0.063)
        fem.rotation_euler = (0, -th1, 0); tib.rotation_euler = (0, -(th2 - th1), 0)
def foot_home(Rb, k, pos=None, yaw=None, spread=0.112):
    hip, fem, tib, a = Rb['legs'][k]; r = Rb['root']
    p = pos if pos is not None else r.location; y_ = yaw if yaw is not None else r.rotation_euler.z
    return Vector((p.x + spread * math.cos(y_ + a), p.y + spread * math.sin(y_ + a), 0.0042))
def walk_feet(Rb, p0, y0, p1, y1, k_, stride=0.03, lift=0.012):
    """tripod gait from pose (p0, y0) to (p1, y1) as k_ goes 0 -> 1: legs 0,2,4 then 1,3,5 swing, stepping to their home spots"""
    dist = (p1 - p0).length + abs(y1 - y0) * 0.06; nst = max(1, int(math.ceil(dist / stride))); cyc = k_ * nst
    feet = []
    for k in range(6):
        g = k % 2; c = cyc - 0.5 * g; i0 = max(0, min(nst, math.floor(c))); fr = c - math.floor(c) if 0 <= c < nst else (1.0 if c >= nst else 0.0)
        def pose_at(j): kk = clamp(j / nst, 0, 1); return p0.lerp(p1, kk), lerp(y0, y1, kk)
        pa, ya = pose_at(i0 + 0.5 * g); pb, yb = pose_at(i0 + 1 + 0.5 * g)
        fa = foot_home(Rb, k, pa, ya); fb = foot_home(Rb, k, pb, yb)
        sw = smooth(0.0, 1.0, fr) if c < nst else 1.0
        f = fa.lerp(fb, sw); f.z += lift * math.sin(math.pi * clamp(fr, 0, 1)) * (1 if 0 <= c < nst else 0); feet.append(f)
    return feet
def arm(Rb, k, grip, pitch=-80.0, open_=0.5):
    """reach: gripper centre to 'grip' (world), pointing 'pitch' deg (down negative); fingers open 0..1"""
    sh, up, fo, wr, fingers = Rb['arms'][k]; Mi = Rb['root'].matrix_world.inverted(); g = Mi @ grip
    sx, sy, sz = sh.location; yaw = math.atan2(g.y - sy, g.x - sx); sh.rotation_euler = (0, 0, yaw)
    pr = R(pitch); wpt = (math.hypot(g.x - sx, g.y - sy) - 0.02 * math.cos(pr), g.z - (sz + 0.006) - 0.02 * math.sin(pr))
    th1, th2 = two_link(wpt[0], wpt[1], AL1, AL2)
    up.rotation_euler = (0, -th1, 0); fo.rotation_euler = (0, -(th2 - th1), 0); wr.rotation_euler = (0, -(pr - th2), 0)
    for fg, s2 in fingers: fg.location = (0.009, s2 * (0.0011 + 0.0036 * open_), 0)
def grip_point(Rb, k):
    bpy.context.view_layer.update()                                  # the arm was just posed: bring the wrist's world matrix up to date
    sh, up, fo, wr, fingers = Rb['arms'][k]; return wr.matrix_world @ Vector((0.02, 0, 0))
def arm_rest(Rb, k, t=0.0):
    r = Rb['root']; fwd = Vector((math.cos(r.rotation_euler.z), math.sin(r.rotation_euler.z), 0)); side = Vector((-fwd.y, fwd.x, 0)) * (1 if k == 0 else -1)
    arm(Rb, k, r.location + fwd * 0.07 + side * 0.045 + Vector((0, 0, 0.0 + 0.003 * math.sin(t * 2 + k))), -60, 0.3)
def place_root(Rb, p, yaw, z, pitch=0.0):
    Rb['root'].location = (p.x, p.y, z); Rb['root'].rotation_euler = (0, pitch, yaw)
    Rb['root'].matrix_world = Matrix.Translation((p.x, p.y, z)) @ Euler((0, pitch, yaw)).to_matrix().to_4x4()   # (now, not at the next depsgraph update: legs/arms/cameras read it this frame)
# ---- the copy, part by part. Groups (orders) in build order; 'built' = how many groups are in
KID_ORDERS = sorted(set(o for o, _ in KID['parts']))
def kid_show(n_groups, drop=None, height=0.04):
    """first n groups shown; 'drop' = (group, k) or a list of them: that group is still coming down from above (k 0..1), straight down in
    the world whatever it hangs from (legs, spools)"""
    show = set(KID_ORDERS[:n_groups]); drops = dict([drop] if isinstance(drop, tuple) else (drop or []))
    if drops: bpy.context.view_layer.update()
    for o_, ob in KID['parts']:
        ob.hide_render = o_ not in show and o_ not in drops
        if 'home' not in ob: ob['home'] = list(ob.location)
        h = Vector(ob['home']); dz = height * (1 - sm(clamp(drops[o_], 0, 1))) if o_ in drops else 0.0
        if dz: ob.hide_render = ob.hide_render or drops[o_] <= 0.0
        ob.location = h + (ob.parent.matrix_world.to_3x3().inverted() @ Vector((0, 0, dz)) if dz else Vector())
GROUP_OF = {nm: o for o, nm in ((0, 'drum'), (2, 'plate'), (10, 'barrel'), (11, 'centre'), (12, 'third'), (13, 'fourth'), (14, 'escape'))}
def n_upto(order): return sum(1 for o in KID_ORDERS if o <= order)
def carried(Rb_arm, obj_, k):
    """the part rides between the gripper fingers"""
    g = grip_point(Rb_arm, k); sh, up, fo, wr, fingers = Rb_arm['arms'][k]
    obj_.matrix_world = Matrix.Translation(g - wr.matrix_world.to_3x3().col[2].normalized() * 0.0) @ wr.matrix_world.to_3x3().to_4x4() @ Matrix.Rotation(math.pi / 2, 4, 'Y')

# ================================================================ CAMERA, MODES
def look(cp, ct, lens=50, fstop=8.0, focus=None, roll=0.0):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'; q = d.to_track_quat('-Z', 'Y')
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0): return Vector((wob(t, 5.0, seed), wob(t, 5.0, seed + 3.3), wob(t, 5.0, seed + 6.1))) * amt
def ease(a_, b_, k): return a_.lerp(b_, sm(clamp(k, 0, 1)))
PICKSET = [o for o in bpy.data.objects if o.parent == PICK]
def mode(which):
    shop = which == 'shop'; kid = set(ob for _, ob in KID['parts'])
    for o in SHOP + [ob for _, ob in ROB['parts']] + PICKSET: o.hide_render = not shop
    for o in kid: o.hide_render = o.hide_render if shop else True
    for o in VOID: o.hide_render = True
    if which == 'dna':
        for o in DNA + [VKEY, VRIM]: o.hide_render = False
    if which == 'cell':
        for o in CELLSET + [CKEY, CRIM]: o.hide_render = False
    WBG.inputs['Color'].default_value = (0.012, 0.011, 0.012, 1) if shop else (0.002, 0.005, 0.016, 1)
def rworld(Rb, v): return Rb['root'].matrix_world @ Vector(v)
def hp(x, y, z): return P_HOME + Vector((x, y, z))                            # the builder's home frame (it faces +x there)
def kp(x, y, z, yaw=None):                                                  # the copy's jig frame (its +x = where its head points)
    c_, s_ = math.cos(C_YAW if yaw is None else yaw), math.sin(C_YAW if yaw is None else yaw); return C_POS + Vector((c_ * x - s_ * y, s_ * x + c_ * y, z))
TAPE_SPD = 0.008                                                            # m/s the plans move through the reader (one row = 2.5 mm)
def reader(Rb, t, run=1.0, lit=1.0):
    """the tape runs from spool 0 to spool 1; the four pins ride the tape on the drum and drop into every hole that passes"""
    off = -t * TAPE_SPD * run; Rb['tape']['off'] = off; Rb['tape']['lit'] = lit
    for k_, sp_ in enumerate(Rb['spools']): sp_.rotation_euler = (math.pi / 2, 0, -off / (0.0069 if k_ == 0 else 0.0044))
    for k_, pn_ in enumerate(Rb['pins']): pn_.location.z = PIN_Z - (hole_depth(TU_TOP + off, k_ + 1) if run > 0 else 0.0)
def arbor_to(Rb_kid, nm, M=None):
    """a copy's wheel (its arbor empty, so wheel + pinion + arbor rod move together) goes to world matrix M, or back home on the plate"""
    arb = Rb_kid['wheels'][nm]
    if 'home' not in arb: arb['home'] = list(arb.location)
    if M is None: arb.location = Vector(arb['home']); arb.rotation_euler = (0, 0, 0); return
    arb.matrix_world = M
def held_at(Rb, k, z_off):
    """world matrix that puts a wheel's arbor so the wheel (at height z_off on its arbor) sits between the fingers, lying flat"""
    g = grip_point(Rb, k); yaw_ = Rb['root'].rotation_euler.z + Rb['arms'][k][0].rotation_euler.z
    return Matrix.Translation(g - Vector((0, 0, z_off + 0.0005))) @ Matrix.Rotation(yaw_, 4, 'Z')
def carry(Rb, k, p0, p1, u, lift=0.05, t0=0.0, t1=1.0, pitch=-85, from_above=False):
    """pick at p0, carry in an arc, set down at p1 over u in [t0, t1]: reach (first 30%), grip, carry, set, open. Returns (phase, grip pt)"""
    v = clamp((u - t0) / (t1 - t0), 0, 1); above0 = p0 + Vector((0, 0, 0.014)); above1 = p1 + Vector((0, 0, 0.014))
    kr = smooth(0.0, 0.25, v); kg = smooth(0.25, 0.34, v); kc = smooth(0.34, 0.86, v); ks = smooth(0.86, 0.93, v); ko = smooth(0.93, 1.0, v)
    if v < 0.34 and from_above: g = above0.lerp(p0, smooth(0.0, 0.27, v))          # (frame one: already over the wheel, going down)
    elif v < 0.34: g = ease(rworld(Rb, (0.1, 0.06 if k == 0 else -0.06, 0.0)), above0, kr * 1.4).lerp(p0, smooth(0.18, 0.27, v))
    elif v < 0.86: g = p0.lerp(p1, kc) + Vector((0, 0, lift * math.sin(math.pi * kc)))
    else: g = p1 + Vector((0, 0, 0.012 * ko))
    arm(Rb, k, g, pitch, 0.85 - 0.62 * kg + 0.62 * ko)
    return (0 if v < 0.27 else (1 if v < 0.93 else 2)), g
def kid_legs_tucked(Rb): legs(Rb, [foot_home(Rb, k, spread=0.086) + Vector((0, 0, 0.009)) for k in range(6)])
def cam_b0(u):
    """the opening shot (and the last one, for the loop): low over the bench, close on the arm over the tray, easing back to show the copy"""
    k = smooth(0.0, 1.0, u)
    cp = hp(0.34, 0.2, 0.12).lerp(hp(0.38, -0.12, 0.22), k); ct = hp(0.035, 0.035, 0.04).lerp(hp(0.06, 0.0, 0.03), k)
    return cp, ct, lerp(34, 32, k)

def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    mode('shop')
    # defaults: builder at home, standing, ticking, reading; the copy on its jig, built up to its barrel; the next wheel in the tray
    home = nb <= 4
    if home:
        place_root(ROB, P_HOME, P_YAW, STAND_Z + 0.0012 * math.sin(t * 2.2)); legs(ROB, [foot_home(ROB, k) for k in range(6)])
    else:
        place_root(ROB, P_ASIDE, P_ASIDE_YAW, STAND_Z + 0.0012 * math.sin(t * 2.2)); legs(ROB, [foot_home(ROB, k) for k in range(6)])
    movement(ROB, t); arm_rest(ROB, 0, t); arm_rest(ROB, 1, t); reader(ROB, t); ROB['iris']['on'] = 1.0
    place_root(KID, C_POS, C_YAW, CROUCH_Z); movement(KID, t, 0.0, 0.0); KID['iris']['on'] = 0.0; kid_legs_tucked(KID)
    arm_rest(KID, 0); arm_rest(KID, 1); reader(KID, 0.0, 0.0, 0.0); KID['tape']['punched'] = 9.0
    for nm in KID['wheels']: arbor_to(KID, nm)
    PICK.location = PICK_HOME - Vector((0, 0, 0.006)); PICK.rotation_euler = (0, 0, 0)
    for o in PICKSET: o.hide_render = False
    copier(0.0, run=False)
    for c in CHIPS: c.location = (0, 0, -1)
    if nb == 0:                                             # picks the next wheel out of the tray and sets it on the copy's plate
        kid_show(n_upto(10)); place = rworld(KID, (LAYOUT['centre'].x, LAYOUT['centre'].y, 0.0))
        ph, g = carry(ROB, 0, PICK_HOME + Vector((0, 0, 0.0)), place + Vector((0, 0, 0.0065)), u, 0.055, 0.0, 0.92, from_above=True)
        if ph == 1: kid_show(n_upto(11)); arbor_to(KID, 'centre', held_at(ROB, 0, 0.006)); [setattr(o, 'hide_render', True) for o in PICKSET]
        elif ph == 2: kid_show(n_upto(11)); [setattr(o, 'hide_render', True) for o in PICKSET]
        else: kid_show(n_upto(10))
        cp, ct, ln = cam_b0(u); look(cp + shake(t, 0.0015), ct, ln, 9.0, focus=g)
    elif nb == 1:                                           # the plans: punched tape running over the reader; pins drop into the holes
        kid_show(n_upto(11)); [setattr(o, 'hide_render', True) for o in PICKSET]
        rd = rworld(ROB, (-0.066, 0.0, 0.004 + PIN_Z))
        cp = rworld(ROB, (-0.066 - 0.028, -0.062, 0.004 + PIN_Z + 0.04)).lerp(rworld(ROB, (-0.066 - 0.016, -0.046, 0.004 + PIN_Z + 0.028)), smooth(0, 1, u))
        look(cp + shake(t, 0.0004), rd + Vector((0, 0, 0.002)), lerp(46, 58, sm(u)), 16.0, focus=rd)
    elif nb == 2:                                           # one row -> one part: the builder sets the third wheel in
        kid_show(n_upto(12)); [setattr(o, 'hide_render', True) for o in PICKSET]
        place = rworld(KID, (LAYOUT['third'].x, LAYOUT['third'].y, 0.0))
        ph, g = carry(ROB, 0, PICK_HOME + Vector((0.004, 0.002, -0.0005)), place + Vector((0, 0, 0.009)), u, 0.05, 0.05, 0.95)
        if ph < 2: arbor_to(KID, 'third', held_at(ROB, 0, 0.0085) if ph == 1 else Matrix.Translation(PICK_HOME + Vector((0.004, 0.002, -0.009))))
        look(hp(0.32, 0.18, 0.2).lerp(hp(0.3, 0.14, 0.17), u), hp(0.07, 0.02, 0.03).lerp(g, 0.2), 34, 10.0, focus=g)
    elif nb == 3:                                           # gears go in and mesh: two drop in, then the builder's own train turning
        if u < 0.45:
            kid_show(n_upto(12), drop=[(13, smooth(0.0, 0.22, u)), (14, smooth(0.16, 0.4, u))], height=0.03)
            pc = rworld(KID, (0.0, 0.0, 0.012)); look(rworld(KID, (0.05, -0.075, 0.04)), pc, 50, 14.0)
        else:
            kid_show(n_upto(14)); movement(ROB, t * 6.0, 1.0)              # (sped up so you see every wheel turn)
            m3 = (LAYOUT['third'] + LAYOUT['fourth']) * 0.5; mp = rworld(ROB, (m3.x, m3.y, 0.009))
            look(rworld(ROB, (m3.x - 0.014, m3.y - 0.016, 0.036)).lerp(rworld(ROB, (m3.x - 0.011, m3.y - 0.012, 0.03)), smooth(0.45, 1, u)), mp, 50, 32.0)
    elif nb == 4:                                           # its heart: the balance swinging, the lever ticking, the hairspring breathing
        kid_show(n_upto(14))
        bl = rworld(ROB, (LAYOUT['balance'].x, LAYOUT['balance'].y, 0.0155))
        look(rworld(ROB, (LAYOUT['balance'].x + 0.016, LAYOUT['balance'].y + 0.04, 0.05)).lerp(rworld(ROB, (LAYOUT['balance'].x + 0.01, LAYOUT['balance'].y + 0.03, 0.04)), smooth(0, 1, u)),
             bl, 60, 22.0)
    elif nb == 5:                                           # time-lapse: every part of the copy goes in -- but the plans don't
        late = [o for o in KID_ORDERS if o > 14 and o < 72]; nl = len(late)
        drops = [(o, smooth(0.04 + 0.5 * i / nl, 0.04 + 0.5 * (i + 1.4) / nl, u)) for i, o in enumerate(late)]
        kid_show(n_upto(14), drop=drops, height=0.035)
        for k in range(2):                                                   # the builder's arms a blur of work
            jit = Vector((wob(t, 7.0, k * 3), wob(t, 7.0, k * 3 + 1), 0.6 * abs(wob(t, 7.0, k * 3 + 2)))) * 0.03
            arm(ROB, k, kp(-0.03 * (1 - 2 * k), -0.05, 0.05) + jit if u < 0.6 else rworld(ROB, (0.07, 0.045 * (1 - 2 * k), 0.0)), -80, 0.5 + 0.4 * math.sin(t * 40 + k))
        if u >= 0.6: arm_rest(ROB, 0, t); arm_rest(ROB, 1, t)
        reader(KID, 0.0, 0.0, 0.0)
        k = smooth(0, 1, u); look(kp(-0.06, -0.2, 0.075).lerp(kp(-0.02, -0.16, 0.06), k), kp(-0.012, 0.0, 0.03), 40, 9.0, focus=kp(-0.03, 0.0, 0.04))
    elif nb == 6:                                           # the copier: the old tape at the back, a blank one in front, holes appear
        kid_show(len(KID_ORDERS) - 1)
        fired = copier(lt, run=True)
        for j, c in enumerate(CHIPS):                                        # punched-out chips drop out of the chute
            tj = (lt * 5 + j * 0.37) % 1.0; sx = (h1(j) - 0.5) * 0.01
            c.location = COPIER_C + Vector((sx + 0.004 * tj, -0.026 - 0.012 * tj, 0.013 - 0.013 * tj * tj)); c.rotation_euler = (j + tj * 9, j * 0.7, 0)
        hd = COPIER_C + Vector((0.0, 0.0, CTZ + 0.004)); k = smooth(0, 1, u)
        look(COPIER_C + Vector((0.035, -0.075, 0.12)).lerp(Vector((0.026, -0.058, 0.095)), k) + shake(t, 0.0005), COPIER_C + Vector((0.0, -0.003, 0.026)), 40, 14.0, focus=hd)
    elif nb == 7:                                           # 1948: the copied tape goes into the copy's empty pack
        kid_show(len(KID_ORDERS) - 1); ins = smooth(0.1, 0.72, u)
        kid_show(len(KID_ORDERS) - 1, drop=(72, max(ins, 0.001)), height=0.035)
        top = rworld(KID, (-0.066, 0.0, 0.004 + PIN_Z + 0.002)) + Vector((0, 0, 0.035 * (1 - sm(ins))))
        grip = top if u < 0.72 else top + Vector((0, 0, 0.03 * smooth(0.72, 0.95, u)))
        arm(ROB, 0, grip, -88, 0.12 if u < 0.72 else 0.12 + 0.6 * smooth(0.72, 0.8, u)); arm_rest(ROB, 1, t)
        pk = rworld(KID, (-0.066, 0.0, 0.03))
        look(Vector((0.25, -0.17, 0.1)).lerp(Vector((0.235, -0.165, 0.09)), smooth(0, 1, u)), Vector((0.11, -0.158, 0.056)), 30, 10.0, focus=pk)
    elif nb == 8:                                           # DNA, 1953: the same idea, two strands that each carry the plans
        mode('dna'); DNA_ROOT.rotation_euler = (0, 0, t * 0.9); DNA_ROOT.location = DO
        look(DO + Vector((0.0, -0.32, 0.06)) * lerp(1.15, 0.9, u), DO + Vector((0, 0, 0.02)), 50, 5.0)
    elif nb == 9:                                           # your cells: the copies get pulled apart, one cell becomes two
        mode('cell'); mitosis(smooth(0.0, 0.95, u), t)
        look(CO + Vector((0.0, -0.42, 0.03)) * lerp(1.05, 0.95, u), CO, 50, 6.0)
    elif nb == 10:                                          # wound up: the ratchet clicks round, the balance starts, the eye lights, it stands
        kid_show(len(KID_ORDERS))
        wind = smooth(0.0, 0.4, u); live = smooth(0.4, 0.58, u); up_ = smooth(0.74, 0.98, u)
        KID['wheels']['barrel'].rotation_euler = (0, 0, -wind * 4.0)
        movement(KID, t, live, 1.0 if live > 0.05 else 0.0); KID['wheels']['barrel'].rotation_euler = (0, 0, -wind * 4.0); click(KID)
        KID['iris']['on'] = smooth(0.7, 0.86, u); reader(KID, t - B[10], live, live)
        place_root(KID, C_POS, C_YAW, lerp(CROUCH_Z, STAND_Z, up_))
        legs(KID, [foot_home(KID, k, spread=lerp(0.086, 0.112, up_)) + Vector((0, 0, 0.009 * (1 - up_))) for k in range(6)])
        bz = rworld(KID, (LAYOUT['barrel'].x, LAYOUT['barrel'].y, 0.0225))
        if u < 0.4:
            look(rworld(KID, (LAYOUT['barrel'].x + 0.012, LAYOUT['barrel'].y - 0.03, 0.06)), bz, 55, 18.0)
        elif u < 0.72:
            bl = rworld(KID, (LAYOUT['balance'].x, LAYOUT['balance'].y, 0.0155))
            look(rworld(KID, (LAYOUT['balance'].x + 0.014, LAYOUT['balance'].y + 0.036, 0.046)), bl, 60, 22.0)
        else:
            k = smooth(0.72, 1, u); hd = rworld(KID, (0.05, 0, -0.004))
            look(kp(0.2, -0.07, 0.06).lerp(kp(0.17, -0.06, 0.075), k), hd.lerp(rworld(KID, (0.02, 0, 0.0)), 0.4), 38, 9.0, focus=hd)
    else:                                                   # the copy walks to the tray and reaches for the next wheel (= frame one)
        kid_show(len(KID_ORDERS)); KID['iris']['on'] = 1.0
        kw = smooth(0.0, 0.6, u); movement(KID, t, 1.0); reader(KID, t - B[10])
        p = C_POS.lerp(P_HOME, sm(kw)); yw = lerp(C_YAW, P_YAW, sm(kw))
        place_root(KID, p, yw, STAND_Z + 0.0012 * math.sin(t * 2.2) * smooth(0.6, 1.0, u) + 0.0018 * math.sin(kw * 30) * (1 - smooth(0.85, 1, kw)))
        legs(KID, walk_feet(KID, C_POS, C_YAW, P_HOME, P_YAW, kw))
        k1 = smooth(0.6, 1.0, u)
        g = ease(rworld(KID, (0.1, 0.06, 0.0)), PICK_HOME + Vector((0, 0, 0.014)), k1)
        arm(KID, 0, g, -85, 0.85); arm_rest(KID, 1, t)
        for o in ROB['parts']: pass
        cp0, ct0, ln0 = cam_b0(0.0); kc = smooth(0.25, 1.0, u)
        cpa = kp(0.22, 0.12, 0.08); cta = rworld(KID, (0.03, 0.0, 0.0))
        look(cpa.lerp(cp0, kc) + shake(t, 0.0015 * kc), cta.lerp(ct0, kc), lerp(36, ln0, kc), 9.0, focus=grip_point(KID, 0) if kc > 0.5 else cta)

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

