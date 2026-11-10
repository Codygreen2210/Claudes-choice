# Kidney stone, built and rendered in Blender (Cycles): a man at his kitchen counter drops to his knees with a stabbing pain in his side;
# the real anatomy (Z-Anatomy atlas, CC BY-SA 4.0, from BodyParts3D) fitted inside him: both kidneys, the funnel inside each (renal
# pelvis), the ureters, the bladder, the aorta / vena cava and the renal vessels, spine, ribs and pelvis; a close-up inside the
# kidney (waste packed tight in too little water, calcium and oxalate joining into crystals, crystals stacking into a jagged stone);
# a close-up inside the ureter (the stone scraping the wall and plugging it, the wall squeezing in waves); pee backing up; a small
# stone passing; a glass of water.
#   python3 stone.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]      (stride.json / redo.json beside it: see ../ele/ele.py)
# Needs man.blend (../foot/man_build.py) and anat.blend (anat_build.py) beside it or in /root/vt/n42/stone.
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n42/stone', n), os.path.join('/root/vt/n42/cramp', n)) if os.path.exists(p_))
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
# ================================================================ THE KITCHEN at night (z up, metres). He stands at the origin facing -y; the
# counter runs along his left (+x); the wall behind it has a window; warm light over the counter, cool night through the window
CX0, CX1, CY0, CY1, CTOP = 0.43, 1.05, -2.2, 1.3, 0.9                 # counter block: front face at CX0, top at CTOP
def tile_mat():
    m = mat('floor', (0.5, 0.42, 0.34), 0.35); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.5; br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 0.9; br.inputs['Row Height'].default_value = 0.14
    br.inputs['Color1'].default_value = (0.34, 0.22, 0.13, 1); br.inputs['Color2'].default_value = (0.42, 0.28, 0.17, 1); br.inputs['Mortar'].default_value = (0.1, 0.07, 0.05, 1)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 4.0; nz.inputs['Detail'].default_value = 8
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (30, 1.5, 1)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.6
    nt.links.new(br.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Coat Weight'].default_value = 0.3; return m
FLOOR = box('floor', (7, 7, 0.1), (0, 0, -0.05), tile_mat())
WALL_M = noisy(mat('wall', (0.3, 0.36, 0.36), 0.85), 3.0, 0.08)
CAB_M = noisy(mat('cabinet', (0.16, 0.24, 0.3), 0.45, coat=0.2), 60.0, 0.1); TOP_M = noisy(mat('countertop', (0.82, 0.8, 0.76), 0.18, coat=0.5), 25.0, 0.2)
STEEL_M = mat('steel', (0.75, 0.76, 0.78), 0.22, metal=1.0); DARK_M = mat('dark', (0.03, 0.03, 0.035), 0.5)
WX = 1.08                                                              # the wall behind the counter
WALLS = [box('wall_side', (0.1, 7, 3), (WX + 0.05, 0, 1.5), WALL_M), box('wall_back', (7, 0.1, 3), (0, 1.75, 1.5), WALL_M)]
KIT = [box('cab_base', (CX1 - CX0 - 0.04, CY1 - CY0, CTOP - 0.14), ((CX0 + CX1) / 2 + 0.02, (CY0 + CY1) / 2, 0.1 + (CTOP - 0.14) / 2), CAB_M, 0.004),
       box('cab_kick', (CX1 - CX0 - 0.12, CY1 - CY0, 0.1), ((CX0 + CX1) / 2 + 0.06, (CY0 + CY1) / 2, 0.05), DARK_M),
       box('countertop', (CX1 - CX0 + 0.03, CY1 - CY0, 0.04), ((CX0 + CX1) / 2 - 0.015, (CY0 + CY1) / 2, CTOP - 0.02), TOP_M, 0.006)]
for i in range(6):                                                    # door fronts with steel pulls
    y = CY0 + (i + 0.5) * (CY1 - CY0) / 6
    KIT.append(box('door%d' % i, (0.018, (CY1 - CY0) / 6 - 0.012, CTOP - 0.2), (CX0 + 0.012, y, 0.1 + (CTOP - 0.14) / 2), CAB_M, 0.006))
    KIT.append(box('pull%d' % i, (0.012, 0.012, 0.14), (CX0 - 0.004, y + (0.2 if i % 2 == 0 else -0.2), 0.68), STEEL_M, 0.004))
# the sink and tap (he was getting a glass of water), the glass under the tap
SK = V3(0.78, -1.15, CTOP)
KIT += [box('sink_rim', (0.42, 0.56, 0.006), SK + V3(0, 0, 0.003), STEEL_M, 0.002), box('sink_hole', (0.38, 0.52, 0.004), SK + V3(0, 0, 0.0065), mat('basin', (0.55, 0.56, 0.58), 0.3, metal=0.8))]
KIT.append(tube('tap', [SK + V3(0.19, 0, 0.0), SK + V3(0.19, 0, 0.2), SK + V3(0.17, 0, 0.26), SK + V3(0.12, 0, 0.29), SK + V3(0.06, 0, 0.29), SK + V3(0.02, 0, 0.27), SK + V3(0.01, 0, 0.24)], 0.011, STEEL_M, seg=14))
subsurf(KIT[-1], 2)
KIT.append(prim('cylinder', 'tap_base', STEEL_M, loc=SK + V3(0.19, 0, 0.012), vertices=24, radius=0.022, depth=0.024))
KIT.append(box('tap_lever', (0.012, 0.07, 0.01), SK + V3(0.19, 0.045, 0.06), STEEL_M, 0.003))
def clear_mat(name, col, alpha, emit=0.0):
    m = mat(name, col, 0.03, coat=0.5, emit=col, estr=emit); nt = m.node_tree; b = nt.nodes['Principled BSDF']; lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.4
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.5, alpha), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(b.outputs['BSDF'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface']); return m
def glass_mat(): return clear_mat('glass', (0.9, 0.95, 1.0), 0.1)
GL = SK + V3(0.01, 0, 0.0075)                                          # the glass stands in the sink under the spout
GLASS_O = lathe('glass', [(0.0, 0.004), (0.031, 0.004), (0.036, 0.13), (0.0345, 0.13), (0.0295, 0.008), (0.0, 0.008)], 40, glass_mat(), loc=GL)
WATER_M = clear_mat('water', (0.45, 0.75, 1.0), 0.35, 0.5)
WATER = prim('cylinder', 'water', WATER_M, loc=GL + V3(0, 0, 0.0085), vertices=40, radius=0.029, depth=1.0)   # scaled in z each frame (origin moved to its base)
for v in WATER.data.vertices: v.co.z += 0.5
STREAM = prim('cylinder', 'stream', WATER_M, loc=GL, vertices=16, radius=0.0045, depth=1.0)
for v in STREAM.data.vertices: v.co.z += 0.5
KIT += [GLASS_O, WATER, STREAM]
for o in (GLASS_O, WATER, STREAM): o.visible_shadow = False
GLAMP = None
# things on the counter and the wall: a kettle, a fruit bowl, a knife block, a wall clock (3:12), a window with night outside
KIT.append(lathe('kettle', [(0.0, 0.0), (0.085, 0.0), (0.09, 0.02), (0.08, 0.15), (0.05, 0.2), (0.02, 0.215), (0.0, 0.215)], 40, STEEL_M, loc=(0.82, 0.25, CTOP))); subsurf(KIT[-1], 1)
KIT.append(tube('kettle_handle', [(0.82, 0.18, CTOP + 0.2), (0.82, 0.14, CTOP + 0.24), (0.82, 0.14, CTOP + 0.1), (0.82, 0.17, CTOP + 0.05)], 0.008, DARK_M, seg=10)); subsurf(KIT[-1], 2)
KIT.append(lathe('bowl', [(0.0, 0.006), (0.07, 0.006), (0.13, 0.07), (0.125, 0.07), (0.068, 0.012), (0.0, 0.012)], 40, mat('bowl', (0.85, 0.82, 0.75), 0.3, coat=0.4), loc=(0.78, 0.85, CTOP)))
_fr = random.Random(4)
for i in range(5):
    KIT.append(prim('uv_sphere', 'fruit%d' % i, noisy(mat('fruit%d' % i, [(0.85, 0.35, 0.05), (0.75, 0.08, 0.06), (0.8, 0.6, 0.1)][i % 3], 0.4), 90, 0.2),
                    loc=(0.78 + 0.05 * math.cos(i * 1.3), 0.85 + 0.05 * math.sin(i * 1.3), CTOP + 0.05 + (0.035 if i == 4 else 0)), segments=24, ring_count=12, radius=0.036))
KIT.append(box('block', (0.1, 0.14, 0.2), (0.9, -0.35, CTOP + 0.1), noisy(mat('wood', (0.4, 0.25, 0.13), 0.5), 20, 0.3), 0.008, rot=(0, R(-12), 0)))
WIN_Y, WIN_Z = -1.15, 1.55
KIT.append(box('win_glow', (0.02, 0.9, 0.8), (WX - 0.005, WIN_Y, WIN_Z), emis('night', (0.06, 0.1, 0.22), 1.5)))
FRAME_M = mat('frame', (0.85, 0.85, 0.82), 0.5)
for dy, dz, sy, sz in ((0, 0.42, 0.98, 0.05), (0, -0.42, 0.98, 0.05), (0.47, 0, 0.05, 0.89), (-0.47, 0, 0.05, 0.89), (0, 0, 0.03, 0.8), (0, 0, 0.9, 0.03)):
    KIT.append(box('winf', (0.05, sy, sz), (WX - 0.02, WIN_Y + dy, WIN_Z + dz), FRAME_M, 0.004))
KIT.append(box('shelf', (0.2, 1.3, 0.03), (WX - 0.1, 0.55, 1.5), noisy(mat('shelfwood', (0.35, 0.22, 0.12), 0.5), 20, 0.3), 0.004))
for i in range(6):
    KIT.append(lathe('jar%d' % i, [(0.0, 0.0), (0.04, 0.0), (0.042, 0.1), (0.03, 0.12), (0.03, 0.135), (0.0, 0.135)], 24,
                     mat('jar%d' % i, [(0.7, 0.5, 0.2), (0.3, 0.45, 0.3), (0.75, 0.72, 0.65), (0.5, 0.2, 0.15)][i % 4], 0.25, coat=0.5), loc=(WX - 0.1, 0.05 + i * 0.2, 1.515)))
KIT.append(prim('cylinder', 'clock', mat('clock', (0.9, 0.9, 0.86), 0.4), loc=(0.3, 1.69, 1.95), rot=(R(90), 0, 0), vertices=48, radius=0.16, depth=0.03))
KIT.append(box('clock_h', (0.012, 0.004, 0.08), (0.3 - 0.008, 1.672, 1.985), DARK_M, rot=(0, R(-96 + 90), 0)))
KIT.append(box('clock_m', (0.008, 0.004, 0.12), (0.3 + 0.045, 1.672, 1.975), DARK_M, rot=(0, R(72), 0)))
# pendant lamp over the counter
KIT.append(lathe('pendant', [(0.0, 0.16), (0.03, 0.16), (0.16, 0.0), (0.155, 0.0), (0.028, 0.15), (0.0, 0.15)], 40, mat('pendant', (0.1, 0.12, 0.13), 0.4, metal=0.6), loc=(0.72, -0.2, 2.0)))
KIT.append(prim('cylinder', 'pendant_cord', DARK_M, loc=(0.72, -0.2, 2.58), vertices=8, radius=0.004, depth=0.85))
KIT.append(prim('uv_sphere', 'bulb', emis('bulb', (1.0, 0.72, 0.42), 30.0), loc=(0.72, -0.2, 2.06), segments=16, ring_count=8, radius=0.03))
ROOM = [FLOOR] + WALLS + KIT
SOLIDS = [KIT[0], KIT[2]]                                              # what he must not sink into (cabinet, countertop)
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
PEND = light_at('pendant_light', 'SPOT', (0.72, -0.2, 2.02), (0.6, -0.3, 0.0), 170, (1.0, 0.74, 0.46), 0.06); PEND.data.spot_size = R(125); PEND.data.spot_blend = 0.5
MOON = light_at('moon', 'AREA', (WX - 0.1, WIN_Y, WIN_Z), (-0.6, -0.5, 0.6), 110, (0.55, 0.7, 1.0), 0.8)
FILL = light_at('fill', 'AREA', (-1.6, -2.4, 2.0), (0, -0.3, 0.8), 30, (0.6, 0.7, 1.0), 2.5)
RIMK = light_at('rim', 'AREA', (-0.8, 1.3, 1.9), (0, -0.3, 0.9), 45, (1.0, 0.8, 0.6), 1.0)
ROOM_L = [PEND, MOON, FILL, RIMK]
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.01, 0.012, 0.02, 1); WBG.inputs['Strength'].default_value = 1.0
XL = light_at('xray_key', 'AREA', (-0.9, -1.4, 1.5), (0, -0.5, 0.9), 40, (0.85, 0.9, 1.0), 1.5); XL.hide_render = True
XL2 = light_at('xray_rim', 'AREA', (0.8, 0.5, 1.2), (0, -0.5, 0.9), 30, (0.7, 0.8, 1.0), 1.2); XL2.hide_render = True
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.005
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HAIR = bpy.data.objects['Human.short02']; HEADBITS = [o for o in bpy.data.objects if o.name.startswith('Human.') and o not in (BODY, SUIT, RIG)]
RB = RIG.data.bones; PB = RIG.pose.bones
KNEE_Z = RB['lowerleg01.R'].head_local.z
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
    for p_ in o.data.polygons: p_.use_smooth = True
sol = SUIT.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0035; sol.offset = 1.0
subsurf(BODY, 1); subsurf(SUIT, 1)
BODY.add_rest_position_attribute = True
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
retint(SHORTS_M, (0.2, 0.25, 0.36), 0.35, 0.95, 0.6)                 # navy shorts
retint(SHIRT_M, (0.62, 0.2, 0.16), 0.35, 0.9, 0.5)                   # the same brick-red tee (the channel's guy)
# x-ray look: glass skin; 'pain' (0..1) lights his right side red around the kidney; 'tt' = time for its flicker
def xray_skin_mat():
    m = bpy.data.materials.new('xskin'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    xx = math_(nt, 'ADD', sx.outputs['X'], 0.09); zz = math_(nt, 'SUBTRACT', sx.outputs['Z'], 1.07)
    side = math_(nt, 'EXPONENT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', xx, xx), -120.0), math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', zz, zz), -70.0)))
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 40.0
    nt.links.new(rp.outputs['Vector'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 5.0), nz.inputs['W'])
    hot = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', side, objattr(nt, 'pain')), math_(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 0.8, 0.6))
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.0)
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.inputs['A'].default_value = (0.35, 0.62, 1.0, 1); base.inputs['B'].default_value = (1.0, 0.16, 0.08, 1)
    nt.links.new(math_(nt, 'MINIMUM', hot, 1.0), base.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(base.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 1.0, 0.02), math_(nt, 'MULTIPLY', hot, 0.5)), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 0.5, 0.04), math_(nt, 'MULTIPLY', hot, 0.12)), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
XSKIN = xray_skin_mat()
BODY['pain'] = 0.0; BODY['tt'] = 0.0
BODY_MATS = [sl.material for sl in BODY.material_slots]
PUFF = BODY.modifiers.new('xray_puff', 'DISPLACE'); PUFF.strength = 0.0; PUFF.mid_level = 0.0      # skin 4 mm fuller in x-ray (anatomy stays inside)
bpy.context.view_layer.objects.active = BODY
while BODY.modifiers.find('xray_puff') > BODY.modifiers.find('Armature') + 1: bpy.ops.object.modifier_move_up(modifier='xray_puff')
# ================================================================ HIS URINARY SYSTEM (anat.blend: fitted in his rest space). His trunk stays
# straight in every x-ray shot (he leans from the hips), so the organs ride on the rig as one rigid piece
ANAT = []
with bpy.data.libraries.load(asset('anat.blend'), link=False) as (_s, _d): _d.objects = list(_s.objects)
for o in _d.objects:
    S.collection.objects.link(o); o.parent = RIG; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, 0, 0)
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False; ANAT.append(o)
AN = {o.name: o for o in ANAT}
def kind(k): return [o for o in ANAT if o['kind'] == k]
def bone_mat():
    m = mat('bone', (0.86, 0.82, 0.72), 0.55, sheen=0.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (0.75, 0.85, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY', lw.outputs['Facing'], 1.2), b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
BONE_M = bone_mat()

for o in kind('bone'): o.data.materials.clear(); o.data.materials.append(BONE_M)
def organ_mat(name, col, alpha, rim=(1.0, 0.6, 0.5), pain_col=(1.0, 0.12, 0.05)):
    """soft translucent organ: you see the funnel and the stone through the kidney; 'pain' (object prop) makes it throb red"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.35; b.inputs['Coat Weight'].default_value = 0.4
    b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Radius'].default_value = (0.01, 0.004, 0.003)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35; pn = objattr(nt, 'pain')
    ec = nt.nodes.new('ShaderNodeMix'); ec.data_type = 'RGBA'; ec.inputs['A'].default_value = (*rim, 1); ec.inputs['B'].default_value = (*pain_col, 1); nt.links.new(pn, ec.inputs['Factor'])
    nt.links.new(ec.outputs['Result'], b.inputs['Emission Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', lw.outputs['Facing'], 0.8), math_(nt, 'MULTIPLY', pn, 2.5)), b.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.6, alpha), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(b.outputs['BSDF'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
def flow_mat(name, col, glow_col, kind_):
    """tubes: bright bands run along 'arc' (m). props: glow, flow (bands strength), speed, tt; ureters also 'fillto' (m: full of held-back pee above this)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.35; b.inputs['Coat Weight'].default_value = 0.3
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'
    ph = math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', arc.outputs['Fac'], 45.0 if kind_ == 'ureter' else 30.0), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), objattr(nt, 'speed')))
    band = math_(nt, 'POWER', math_(nt, 'MULTIPLY_ADD', math_(nt, 'SINE', math_(nt, 'MULTIPLY', ph, 6.2832)), 0.5, 0.5), 3.0)
    st = math_(nt, 'ADD', objattr(nt, 'glow'), math_(nt, 'MULTIPLY', band, objattr(nt, 'flow')))
    if kind_ == 'ureter':
        full = math_(nt, 'LESS_THAN', arc.outputs['Fac'], objattr(nt, 'fillto')); st = math_(nt, 'ADD', st, math_(nt, 'MULTIPLY', full, 3.0))
    b.inputs['Emission Color'].default_value = (*glow_col, 1); nt.links.new(st, b.inputs['Emission Strength']); return m
KID_M = organ_mat('kidney', (0.42, 0.11, 0.08), 0.42); PELV_M = organ_mat('renal_pelvis', (0.95, 0.78, 0.5), 0.55, rim=(1.0, 0.85, 0.45), pain_col=(1.0, 0.8, 0.1))
BLAD_M = organ_mat('bladder', (0.9, 0.62, 0.5), 0.4, rim=(1.0, 0.8, 0.5))
URE_M = flow_mat('ureter', (0.95, 0.75, 0.55), (1.0, 0.8, 0.2), 'ureter'); ART_M = flow_mat('artery', (0.75, 0.08, 0.06), (1.0, 0.2, 0.1), 'artery'); VEIN_M = flow_mat('vein', (0.12, 0.2, 0.6), (0.3, 0.45, 1.0), 'vein')
for k_, m_ in (('kidney', KID_M), ('pelvis', PELV_M), ('bladder', BLAD_M), ('ureter', URE_M), ('artery', ART_M), ('vein', VEIN_M)):
    for o in kind(k_):
        o.data.materials.clear(); o.data.materials.append(m_); o['pain'] = 0.0; o['glow'] = 0.3; o['flow'] = 0.0; o['speed'] = 1.0; o['tt'] = 0.0; o['fillto'] = -1.0
KIDR, KIDL, PELR, PELL, BLAD, URER, UREL = (AN[n] for n in ('Kidney.r', 'Kidney.l', 'Renal pelvis.r', 'Renal pelvis.l', 'Urinary bladder', 'Ureter.r', 'Ureter.l'))
def centre(o): return sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
KC, PC, BC = centre(KIDR), centre(PELR), centre(BLAD)                # rig (rest) space
for o in (KIDR, PELR):                                                # so they can swell about their own middle
    c_ = centre(o)
    for v in o.data.vertices: v.co -= c_
    o.location = c_; o['home'] = list(c_)
_uv = np.array([v.co[:] for v in URER.data.vertices]).reshape(-1, 10, 3).mean(1)
URE_CL = [Vector(p) for p in _uv]                                     # the right ureter's centre line, kidney end first
URE_ARC = [0.0]
for i in range(1, len(URE_CL)): URE_ARC.append(URE_ARC[-1] + (URE_CL[i] - URE_CL[i - 1]).length)
URE_LEN = URE_ARC[-1]
def ure_pt(s):
    """point at arc length s (m) down the right ureter (rig space); s < 0 = still up in the kidney's funnel"""
    if s <= 0: return URE_CL[0].lerp(PC + V3(0.006, 0, 0.012), clamp(-s / 0.03, 0, 1))
    s = min(s, URE_LEN - 1e-5); i = int(np.searchsorted(URE_ARC, s)) - 1; i = clamp(i, 0, len(URE_CL) - 2)
    return URE_CL[i].lerp(URE_CL[i + 1], (s - URE_ARC[i]) / max(URE_ARC[i + 1] - URE_ARC[i], 1e-9))
# ---- the stone: a clump of sharp crystals (calcium oxalate: little two-ended pyramids), yellow-brown
def crystal_mesh(name, n, seed, spread=1.0, size=1.0):
    rr = random.Random(seed); vs, fs = [], []
    for i in range(n):
        d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized(); c = Vector((d.x * 1.0, d.y * 0.8, d.z * 0.75)) * spread * rr.uniform(0.25, 1.0)
        s = size * rr.uniform(0.35, 0.75); ax = (d + Vector((rr.gauss(0, 0.5), rr.gauss(0, 0.5), rr.gauss(0, 0.5)))).normalized()
        u = ax.orthogonal().normalized(); w = ax.cross(u); b0 = len(vs)
        vs += [c + ax * s * 1.25, c - ax * s * 0.9] + [c + (u * math.cos(a_) + w * math.sin(a_)) * s * 0.62 for a_ in (0.4, 1.97, 3.54, 5.11)]
        for k in range(4): k2 = (k + 1) % 4; fs += [(b0, b0 + 2 + k, b0 + 2 + k2), (b0 + 1, b0 + 2 + k2, b0 + 2 + k)]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in vs], [], fs); me.update(); return me
def stone_mat(name='stone'):
    m = mat(name, (0.5, 0.33, 0.12), 0.5, coat=0.2); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    noisy(m, 300.0, 0.45, 0.2); b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.3, 0.2, 0.1)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (1.0, 0.75, 0.3, 1); nt.links.new(math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.6, objattr(nt, 'glow')), b.inputs['Emission Strength']); return m
STONE_M = stone_mat()
STONE = obj('stone', crystal_mesh('stone', 70, 5, 0.0042, 0.0032), STONE_M, parent=RIG); STONE['glow'] = 4.0; STONE.visible_shadow = False
for p_ in STONE.data.polygons: p_.use_smooth = False
SMALL = obj('stone_small', crystal_mesh('stone_small', 30, 9, 0.0011, 0.0009), STONE_M, parent=RIG); SMALL['glow'] = 1.5; SMALL.visible_shadow = False
HALO = prim('uv_sphere', 'stone_halo', emis('halo', (1.0, 0.8, 0.3), 25.0), parent=RIG, segments=12, ring_count=6, radius=0.0024)
XRAY_OBJS = ANAT + [STONE, SMALL, HALO]
# ================================================================ INSIDE THE KIDNEY (a set of its own far from the room, at MO): the hollow
# where pee collects. Waste floats in it: calcium (white) and oxalate (blue-green) specks. Less water -> the same specks in half the
# room. They join into sharp two-ended crystals; the crystals stack into a stone.
MO = V3(40.0, 0.0, 1.0)
def cave_mat():
    m = mat('kidney_wall', (0.55, 0.13, 0.1), 0.3, coat=0.6); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    b.inputs['Subsurface Weight'].default_value = 0.4; b.inputs['Subsurface Radius'].default_value = (0.2, 0.06, 0.04)
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 5.0; nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14.0; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector']); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.05
    nt.links.new(math_(nt, 'ADD', vo.outputs['Distance'], math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.4)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.62, 0.16, 0.12, 1); mx.inputs['B'].default_value = (0.3, 0.05, 0.05, 1)
    nt.links.new(vo.outputs['Distance'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color']); return m
CAVE = prim('ico_sphere', 'kidney_cave', cave_mat(), loc=MO, subdivisions=5, radius=1.0, scale=(0.85, 1.3, 1.1))
bpy.context.view_layer.objects.active = CAVE; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
_cr = random.Random(21)
for v in CAVE.data.vertices:
    n = mnoise.noise(v.co * 2.2) * 0.14 + mnoise.noise(v.co * 5.0) * 0.05; v.co *= 1.0 + n
class Specks:
    """many small balls in one mesh, moved by numpy each frame"""
    def __init__(self, name, n, r, m, seed):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); base = np.array([v.co[:] for v in bm.verts]); faces = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
        self.base = base; self.n = n; self.nv = len(base); rr = np.random.default_rng(seed)
        d = rr.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1)[:, None]; self.p0 = d * (rr.random(n)[:, None] ** 0.45) * np.array([0.42, 0.34, 0.5])
        self.r = r * rr.uniform(0.7, 1.3, n); self.seed = rr.random(n) * 100
        vs = (self.p0[:, None, :] + base[None] * self.r[:, None, None]).reshape(-1, 3); fs = [[i * self.nv + k for k in f] for i in range(n) for f in faces]
        me = bpy.data.meshes.new(name); me.from_pydata(vs.tolist(), [], fs); me.update()
        for p in me.polygons: p.use_smooth = True
        self.o = obj(name, me, m, loc=MO); self.o.visible_shadow = False
    def set(self, P, Sc):
        vs = (P[:, None, :] + self.base[None] * (self.r * Sc)[:, None, None]).reshape(-1); self.o.data.vertices.foreach_set('co', vs.astype(np.float32)); self.o.data.update()
CA = Specks('calcium', 150, 0.011, mat('calcium', (0.95, 0.95, 0.92), 0.3, emit=(1.0, 0.98, 0.9), estr=0.6), 1)
OX = Specks('oxalate', 150, 0.008, mat('oxalate', (0.25, 0.85, 0.75), 0.3, emit=(0.2, 0.9, 0.75), estr=0.9), 2)
class Cluster:
    """sharp two-ended crystals in one mesh; each has a free spot (where it forms), a home in the stone, a size"""
    def __init__(self, name, n, seed, spread, size, m, loc):
        rr = random.Random(seed); V, H = [], []; fs = []
        for i in range(n):
            d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized(); c = Vector((d.x, d.y * 0.8, d.z * 0.75)) * spread * (rr.uniform(0.0, 0.35) if i < 8 else rr.uniform(0.45, 1.0))
            s = size * rr.uniform(0.55, 1.0); ax = (d + Vector((rr.gauss(0, 0.5), rr.gauss(0, 0.5), rr.gauss(0, 0.5)))).normalized(); u = ax.orthogonal().normalized(); w = ax.cross(u)
            V.append([ax * s * 1.25, -ax * s * 0.9] + [(u * math.cos(a_) + w * math.sin(a_)) * s * 0.62 for a_ in (0.4, 1.97, 3.54, 5.11)]); H.append(c)
            b0 = i * 6
            for k in range(4): k2 = (k + 1) % 4; fs += [(b0, b0 + 2 + k, b0 + 2 + k2), (b0 + 1, b0 + 2 + k2, b0 + 2 + k)]
        self.V = np.array([[v[:] for v in c] for c in V]); self.H = np.array([h[:] for h in H]); self.n = n
        rg = np.random.default_rng(seed); d = rg.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1)[:, None]
        self.F = d * rg.uniform(0.16, 0.36, n)[:, None] * np.array([1.0, 0.8, 1.25]); self.spin = rg.uniform(-2, 2, (n, 3))
        me = bpy.data.meshes.new(name); me.from_pydata((self.H[:, None, :] + self.V).reshape(-1, 3).tolist(), [], fs); me.update()
        self.o = obj(name, me, m, loc=loc); self.o['glow'] = 0.3
    def set(self, attach, grow, t=0.0):
        """attach 0..1 per crystal (free spot -> home), grow 0..1 (size)"""
        a_ = attach[:, None]; P = self.F * (1 - a_) + self.H * a_
        ang = (1 - attach) * (t * 0.8 + 1.0); c_, s_ = np.cos(ang * self.spin[:, 0])[:, None, None], np.sin(ang * self.spin[:, 0])[:, None, None]
        V = self.V.copy(); x = V[:, :, 0:1] * c_ - V[:, :, 1:2] * s_; y = V[:, :, 0:1] * s_ + V[:, :, 1:2] * c_; V[:, :, 0:1] = x; V[:, :, 1:2] = y
        vs = (P[:, None, :] + V * grow[:, None, None]).reshape(-1); self.o.data.vertices.foreach_set('co', vs.astype(np.float32)); self.o.data.update()
def crystal_mat():
    m = stone_mat('crystal'); return m
NCR = 90
BIG = Cluster('macro_stone', NCR, 5, 0.105, 0.062, crystal_mat(), MO)
_ord = np.argsort(np.linalg.norm(BIG.H, axis=1)); BIG.rank = np.empty(NCR); BIG.rank[_ord] = np.arange(NCR) / (NCR - 1)        # inner ones attach first
# each speck's crystal (first 16 crystals form in beat 4): it flies to that crystal's free spot and is used up
FIRST = _ord[:16]
for sp_ in (CA, OX): sp_.to = BIG.F[FIRST[np.arange(sp_.n) % 16]]
MK = light_at('macroA_key', 'AREA', MO + V3(-0.5, -0.7, 0.6), MO, 11, (1.0, 0.9, 0.7), 0.6); MR = light_at('macroA_rim', 'AREA', MO + V3(0.6, 0.6, -0.2), MO, 12, (1.0, 0.75, 0.35), 0.8)
MF = light_at('macroA_fill', 'POINT', MO + V3(0, 0, 0), MO + V3(0, 0, 1), 2.5, (1.0, 0.8, 0.4), 0.3)
MACRO_A = [CAVE, CA.o, OX.o, BIG.o, MK, MR, MF]
def macro_a(pack, join, stack, t):
    """pack: specks crowd into less water; join: specks -> first crystals; stack: crystals -> the stone"""
    for sp_ in (CA, OX):
        drift = np.stack([np.sin(t * 0.7 + sp_.seed), np.cos(t * 0.6 + sp_.seed * 1.7), np.sin(t * 0.5 + sp_.seed * 2.3)], 1) * 0.02
        P = sp_.p0 * (1 - 0.5 * pack) + drift * (1 - 0.6 * pack)
        kj = np.clip((join * 1.6 - (sp_.seed % 1.0) * 0.6), 0, 1); kj = kj * kj * (3 - 2 * kj)
        P = P * (1 - kj[:, None]) + sp_.to * kj[:, None]; sp_.set(P, 1.0 - kj ** 3)
    first = np.zeros(NCR, bool); first[FIRST] = True
    grow = np.where(first, np.clip(join * 1.5 - 0.3 - BIG.rank * 1.5, 0, 1), np.clip((stack * 1.25 - BIG.rank) * 6.0, 0, 1))
    att = np.clip((stack * 1.25 - BIG.rank) * 5.0 - 0.15, 0, 1); att = att * att * (3 - 2 * att)
    BIG.set(att, grow * (0.75 + 0.25 * att), t); BIG.o['glow'] = 0.25 + 0.3 * stack
    MF.data.color = Vector((1.0, 0.86, 0.5)).lerp(Vector((1.0, 0.55, 0.12)), pack)
# ================================================================ INSIDE THE URETER (cut open lengthwise, at UO; pee runs down = -z): a thin
# muscle tube with a folded lining. The stone comes down, scrapes the lining, jams where the tube is narrow. Pee fills the tube
# above it; the wall squeezes in waves that run down into the stone.
UO = V3(60.0, 0.0, 1.0)
NS_, NT_ = 150, 40; S_AX = np.linspace(-1.25, 1.25, NS_); TH = np.linspace(R(-2), R(182), NT_)      # the far half of the tube (near half cut away)
def wall_mat():
    m = mat('ureter_wall', (0.86, 0.45, 0.42), 0.3, coat=0.5); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    b.inputs['Subsurface Weight'].default_value = 0.35; b.inputs['Subsurface Radius'].default_value = (0.08, 0.03, 0.02)
    sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 5; mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (60, 60, 1.5)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    # scrape marks: thin red streaks along the tube, only between where the stone came in (z0) and where it is now (zs)
    below = math_(nt, 'LESS_THAN', sp.outputs['Z'], objattr(nt, 'z0')); above = math_(nt, 'GREATER_THAN', sp.outputs['Z'], objattr(nt, 'zs'))
    streak = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', below, above), math_(nt, 'GREATER_THAN', nz.outputs['Fac'], 0.56))
    streak = math_(nt, 'MULTIPLY', streak, objattr(nt, 'scrape'))
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.86, 0.45, 0.42, 1); mx.inputs['B'].default_value = (0.75, 0.05, 0.04, 1)
    nt.links.new(streak, mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value = (1.0, 0.1, 0.05, 1); nt.links.new(math_(nt, 'MULTIPLY', streak, 1.2), b.inputs['Emission Strength'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.02; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal']); return m
def _grid_faces(ns, nt, off=0, flip=False):
    fs = []
    for i in range(ns - 1):
        for k in range(nt - 1):
            a0 = off + i * nt + k; q = (a0, a0 + 1, a0 + nt + 1, a0 + nt); fs.append(q[::-1] if flip else q)
    return fs
_N = NS_ * NT_
_fs = _grid_faces(NS_, NT_, 0, True) + _grid_faces(NS_, NT_, _N, False)
for i in range(NS_ - 1):                                              # the two cut faces (lining to outside)
    for k in (0, NT_ - 1):
        a0 = i * NT_ + k; q = (a0, a0 + NT_, a0 + NT_ + _N, a0 + _N); _fs.append(q if k == 0 else q[::-1])
_me = bpy.data.meshes.new('ureter_cut'); _me.from_pydata([(0, 0, 0)] * (2 * _N), [], _fs); _me.update()
for p in _me.polygons: p.use_smooth = True
UWALL = obj('ureter_cut', _me, wall_mat(), loc=UO); UWALL['z0'] = 9.0; UWALL['zs'] = 9.0; UWALL['scrape'] = 0.0
PEE_M = bpy.data.materials.new('pee'); PEE_M.use_nodes = True; _nt = PEE_M.node_tree; _b = _nt.nodes['Principled BSDF']
_b.inputs['Base Color'].default_value = (1.0, 0.78, 0.1, 1); _b.inputs['Roughness'].default_value = 0.05; _b.inputs['Emission Color'].default_value = (1.0, 0.7, 0.05, 1); _b.inputs['Emission Strength'].default_value = 0.9
_tr = _nt.nodes.new('ShaderNodeBsdfTransparent'); _mx = _nt.nodes.new('ShaderNodeMixShader'); _mx.inputs['Fac'].default_value = 0.5
_nt.links.new(_tr.outputs['BSDF'], _mx.inputs[1]); _nt.links.new(_b.outputs['BSDF'], _mx.inputs[2]); _nt.links.new(_mx.outputs['Shader'], _nt.nodes['Material Output'].inputs['Surface'])
NPT = 24; _me2 = bpy.data.meshes.new('pee'); _me2.from_pydata([(0, 0, 0)] * (NS_ * NPT), [], [(i * NPT + k, i * NPT + (k + 1) % NPT, (i + 1) * NPT + (k + 1) % NPT, (i + 1) * NPT + k) for i in range(NS_ - 1) for k in range(NPT)]); _me2.update()
for p in _me2.polygons: p.use_smooth = True
PEE = obj('pee', _me2, PEE_M, loc=UO); PEE.visible_shadow = False
USTONE = Cluster('ureter_stone', 80, 5, 0.085, 0.05, stone_mat('stone_u'), UO); USTONE.set(np.ones(80), np.ones(80)); USTONE.o['glow'] = 0.15
USMALL = Cluster('ureter_small', 40, 9, 0.034, 0.022, stone_mat('stone_s'), UO); USMALL.set(np.ones(40), np.ones(40)); USMALL.o['glow'] = 0.15
RS_BIG, RS_SMALL, R_LUM = 0.118, 0.045, 0.07
UK = light_at('macroB_key', 'AREA', UO + V3(-0.9, -1.3, 0.7), UO, 70, (1.0, 0.93, 0.85), 1.0); UR_ = light_at('macroB_rim', 'AREA', UO + V3(0.9, 0.5, -0.4), UO, 50, (1.0, 0.6, 0.4), 1.0)
UBACK = box('macroB_back', (6, 0.1, 6), UO + V3(0, 1.2, 0), mat('back', (0.03, 0.012, 0.014), 0.9))
MACRO_B = [UWALL, PEE, USTONE.o, USMALL.o, UK, UR_, UBACK]
def lumen(z, t, zs, rs, narrow, back, wave):
    """inner radius along the tube (z down = downstream). zs = stone centre, rs = its radius; narrow: tube tight below the stone;
    back: 0..1 tube swollen with held pee above it; wave: 0..1 strength of the squeeze waves running down"""
    r = np.full_like(z, R_LUM)
    r = r * (1 - 0.42 * narrow * (1 / (1 + np.exp((z - (zs - rs * 0.6)) * 30))))            # narrow part below the stone
    r = r * (1 + 0.5 * back * (1 / (1 + np.exp(-(z - (zs + rs * 0.5)) * 14))))              # swollen above it
    for j in range(3):                                                                      # squeeze rings travelling down
        zw = 1.4 - ((t * 0.75 + j / 3.0) % 1.0) * 2.8
        amp = wave * 0.45 * (1.0 if zw > zs + rs * 0.6 else 0.25)
        r = r * (1 - amp * np.exp(-((z - zw) / 0.11) ** 2))
    if rs > 0: r = np.maximum(r, np.sqrt(np.clip(rs * rs - (z - zs) ** 2, 0, None)) * 0.985)     # the wall wraps the stone
    return r
def ureter_set(t, zs, rs, narrow=1.0, back=0.0, wave=0.0, z0=9.0, scrape=0.0, pee_to=None):
    z = -S_AX; ri = lumen(z, t, zs, rs, narrow, back, wave)
    fold = 1 + 0.07 * np.cos(TH[None, :] * 6 + z[:, None] * 2.0) * np.clip(1.6 - ri[:, None] / R_LUM, 0.2, 1.0)
    RI = ri[:, None] * fold; RO = np.maximum(ri[:, None] + 0.038, 0.118 + 0.0 * RI)
    def ring(Rr): return np.stack([Rr * np.cos(TH)[None, :], Rr * np.sin(TH)[None, :], np.repeat(z[:, None], NT_, 1)], 2).reshape(-1, 3)
    vs = np.concatenate([ring(RI), ring(RO)]).reshape(-1).astype(np.float32); UWALL.data.vertices.foreach_set('co', vs); UWALL.data.update()
    UWALL['zs'] = float(zs); UWALL['z0'] = float(z0); UWALL['scrape'] = float(scrape)
    # the pee: fills the lumen from the top down to 'pee_to' (default: everywhere, a thin stream when nothing is stuck)
    a2 = np.linspace(0, 2 * math.pi, NPT, endpoint=False); top = 9.0 if pee_to is None else pee_to
    rp = np.where(z > top, ri * 0.93, ri * 0.0 + 0.002)
    vp = np.stack([rp[:, None] * np.cos(a2)[None, :], rp[:, None] * np.sin(a2)[None, :], np.repeat(z[:, None], NPT, 1)], 2).reshape(-1).astype(np.float32)
    PEE.data.vertices.foreach_set('co', vp); PEE.data.update()
from mathutils.bvhtree import BVHTree
def ik(bone, target, pole, chain, pole_angle=R(-90)):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TGT = {k: empty('tgt_' + k) for k in ('ankR', 'ankL', 'poleR', 'poleL', 'handR', 'handL', 'poleArmR', 'poleArmL')}
for s_ in ('R', 'L'):
    ik('lowerleg02.' + s_, TGT['ank' + s_], TGT['pole' + s_], 4)
    for bn in ('lowerleg02.', 'upperleg02.'):
        pb = PB[bn + s_]; pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = True
    ik('lowerarm02.' + s_, TGT['hand' + s_], TGT['poleArm' + s_], 4)      # the arm reaches the WRIST JOINT; the hand then turns freely about it
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
def fingers(s_, curl, spread=0.0):
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            nm = f'finger{f_}-{seg}.{s_}'
            if nm in PB: ang = (10, 15, 8)[seg - 1] if f_ == 1 else (40, 55, 30)[seg - 1]; rot(nm, ang * curl, 0, (f_ - 3) * spread * (1 if seg == 1 else 0))
def wpos(bn, tail=False):
    pb = PB[bn]; return RIG.matrix_world @ (pb.tail if tail else pb.head)
def bone_world(bn, tail=False): return wpos(bn, tail)
HIP0 = (RB['upperleg01.R'].head_local + RB['upperleg01.L'].head_local) * 0.5
PALM_D = 0.068                                         # wrist joint to the middle of the palm (m, measured on his rest pose)
PALM_T = 0.013                                         # palm skin above the hand bones
def set_pose(hip, rig_rot=(0, 0, 0), spine=0.0, neck=0.0, head=0.0, head_yaw=0.0, side_lean=0.0,
             ankR=None, poleR=None, footR=(0, 0, 0), toesR=0.0, ankL=None, poleL=None, footL=(0, 0, 0), toesL=0.0,
             curlR=0.3, curlL=0.3, lids=0.0, jaw=0.0, poleArmR=None, poleArmL=None):
    """hip = where the centre of his hip joints goes (world); the rig turns about it"""
    RIG.rotation_euler = tuple(R(x) for x in rig_rot)
    RIG.location = Vector(hip) - RIG.rotation_euler.to_matrix() @ HIP0
    for n, k in (('spine03', 0.3), ('spine02', 0.35), ('spine01', 0.35)): rot(n, spine * k, 0, side_lean * k)
    for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)): rot(n, neck * k, head_yaw * k * 0.5)
    rot('head', head, head_yaw * 0.5)
    rot('orbicularis03.R', LID_SIGN * 26 * lids); rot('orbicularis03.L', LID_SIGN * 26 * lids)
    rot('orbicularis04.R', -LID_SIGN * 8 * lids); rot('orbicularis04.L', -LID_SIGN * 8 * lids)
    rot('jaw', JAW_SIGN * 16 * jaw)
    TGT['ankR'].location = ankR; TGT['ankL'].location = ankL; TGT['poleR'].location = poleR; TGT['poleL'].location = poleL
    rot('foot.R', *footR); rot('foot.L', *footL)
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            for s_, tc in (('R', toesR), ('L', toesL)):
                nm = f'toe{f_}-{seg}.{s_}'
                if nm in PB: rot(nm, tc * (28 if seg == 1 else 22))
    TGT['poleArmR'].location = poleArmR if poleArmR is not None else RIG.matrix_world @ V3(-0.7, 0.35, 1.0)
    TGT['poleArmL'].location = poleArmL if poleArmL is not None else RIG.matrix_world @ V3(0.7, 0.35, 1.0)
    fingers('R', curlR); fingers('L', curlL)
    bpy.context.view_layer.update()
LID_SIGN = -1.0; JAW_SIGN = 1.0                          # tested: lids close with a negative turn, the jaw opens with a positive one
def place_hand(s_, contact, fdir, pdir, w_rot=1.0):
    """put the middle of his palm on 'contact', fingers along fdir, palm facing pdir (into the surface)"""
    d = Vector(fdir).normalized(); n = Vector(pdir); n = (n - d * n.dot(d)).normalized()
    TGT['hand' + s_].location = Vector(contact) - n * PALM_T - d * PALM_D
    O, e_, c_ = HAND[s_]; c_.influence = w_rot; e_.rotation_quaternion = hand_quat(s_, d, n)

# ---- keeping him out of the floor and his hand out of his side (measured on the posed skin, every frame)
def body_eval():
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); rp = rp.reshape(-1, 3); oe.to_mesh_clear()
    M_ = np.array(BODY.matrix_world); return co @ M_[:3, :3].T + M_[:3, 3], rp
def suit_bvh():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles(); M = SUIT.matrix_world
    T_ = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles]); oe.to_mesh_clear(); return T_
def suit_minz():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); oe.to_mesh_clear(); M_ = np.array(SUIT.matrix_world)
    return float((co @ M_[:3, :3].T + M_[:3, 3])[:, 2].min())
def ground(kneel=0.0, passes=4):
    """feet: each ankle goes up or down until that foot just touches the floor. knees: the hips rise if a knee is under the floor,
    and (kneeling) sink until the knees rest on it"""
    for _ in range(passes):
        W, RP = body_eval(); moved = 0.0
        for s_, sg in (('R', -1.0), ('L', 1.0)):
            mn = float(W[(RP[:, 2] < 0.1) & (RP[:, 0] * sg > 0), 2].min()); d = clamp(0.001 - mn, -0.03, 0.03)
            if abs(d) > 0.0004: TGT['ank' + s_].location.z += d; moved = max(moved, abs(d))
        m_ = (RP[:, 2] > 0.25) & (RP[:, 2] < 0.75); kn = min(float(W[m_, 2].min()) if m_.any() else 9.0, suit_minz())      # knees: skin below the shorts, and the shorts
        d = (0.001 - kn) if (kn < 0.001 or kneel > 0.97) else 0.0; d = clamp(d, -0.03, 0.03)
        if abs(d) > 0.0004: RIG.location.z += d; moved = max(moved, abs(d))
        if moved < 0.0005: break
        bpy.context.view_layer.update()
HO_LOG = []
# feet: turned in the world (flat on the floor, or tipped up onto the toes by 'phi'), whatever the shin does
FOOT = {}
for s_ in ('R', 'L'):
    e_ = empty('tgt_foot' + s_); e_.rotation_mode = 'QUATERNION'
    c_ = PB['foot.' + s_].constraints.new('COPY_ROTATION'); c_.target = e_; c_.owner_space = c_.target_space = 'WORLD'
    FOOT[s_] = (e_, RB['foot.' + s_].matrix_local.to_3x3())
def hand_out(sides=('R',), passes=6, keep=0.0015):
    """a hand that sank into his shirt/shorts is pushed back out along the cloth's normal"""
    T_ = suit_bvh()
    for _ in range(passes):
        W, RP = body_eval(); moved = False
        for s_ in sides:
            sg = -1.0 if s_ == 'R' else 1.0; hm = np.where(RP[:, 0] * sg > 0.44)[0]; pen, nrm = 0.0, Vector()
            for i in hm[::2]:
                p = Vector(W[i]); loc, nor, _, d = T_.find_nearest(p, 0.05)
                if loc is not None and (p - loc).dot(nor) < 0 and d > pen: pen, nrm = d, nor
            if pen > 0.0005: TGT['hand' + s_].location += nrm * (pen + keep); moved = True; HO_LOG.append((s_, round(pen, 4)))
        if not moved: return
        bpy.context.view_layer.update()
def hand_on_top(passes=5):
    """his left hand rests on the countertop: lowest point of the hand (fingertips, heel of the palm) just touching it"""
    for _ in range(passes):
        W, RP = body_eval(); m_ = (RP[:, 0] > 0.36) & (W[:, 0] > CX0 - 0.002)
        if not m_.any(): return
        d = clamp(CTOP + 0.001 - float(W[m_, 2].min()), -0.02, 0.02)
        if abs(d) < 0.0004: return
        TGT['handL'].location.z += d; bpy.context.view_layer.update()
# ================================================================ THE POSES. S: standing at the counter. A: the pain hits (bends, grabs his
# right side). B: on his knees (toes tucked under), left hand holding the counter, right hand pressed to his side.
TOE_SIGN = 1.0
BALL_Y = -0.13                                                        # where the balls of his feet stay planted (world y)
FLANK = V3(-0.142, -0.035, 1.065)                                     # rig space: his right side over the kidney
def P_S():
    return dict(hip=V3(0, 0, 0.858), rot=V3(0, 0, 0), neck=5.0, head=0.0, phi=0.0, pole=V3(0.19, -1.5, 0.5), lids=0.0, jaw=0.0, toe=0.0,
                hR=('rig', V3(-0.25, 0.0, 0.78), V3(0, -0.2, -1), V3(1, 0, 0), 0.0), paR=V3(-0.5, 0.9, 1.0), curlR=0.35,
                hL=('world', V3(CX0 + 0.04, -0.1, CTOP + 0.004), V3(0.12, -1, 0), V3(0, 0, -1), 1.0), paL=V3(0.5, 0.9, 1.1), curlL=-0.2, kneel=0.0)
def P_A():
    return dict(hip=V3(0, 0.02, 0.8), rot=V3(14, 0, -3), neck=22.0, head=12.0, phi=0.0, pole=V3(0.19, -1.5, 0.5), lids=1.0, jaw=0.5, toe=0.0,
                hR=('rig', FLANK, V3(0.1, -0.75, -0.65), V3(1, 0, 0), 1.0), paR=V3(-0.7, 0.7, 1.2), curlR=0.3,
                hL=('world', V3(CX0 + 0.04, -0.16, CTOP + 0.004), V3(0.12, -1, 0), V3(0, 0, -1), 1.0), paL=V3(0.5, 0.9, 1.1), curlL=-0.2, kneel=0.0)
def P_B():
    return dict(hip=V3(0, -0.6, 0.47), rot=V3(20, 0, -5), neck=32.0, head=14.0, phi=88.0, pole=V3(0.19, -2.2, 0.1), lids=1.0, jaw=0.6, toe=-80.0,
                hR=('rig', FLANK, V3(0.1, -0.75, -0.65), V3(1, 0, 0), 1.0), paR=V3(-0.7, 0.7, 1.2), curlR=0.35,
                hL=('world', V3(CX0 + 0.04, -0.74, CTOP + 0.004), V3(0.12, -1, 0), V3(0, 0, -1), 1.0), paL=V3(0.55, 0.6, 1.1), curlL=-0.2, kneel=1.0)
def _mix(a_, b_, k):
    if isinstance(a_, tuple): return (a_[0],) + tuple(_mix(x, y, k) for x, y in zip(a_[1:], b_[1:]))
    return a_ + (b_ - a_) * k
def blend(PA, PB_, k): return {n: _mix(PA[n], PB_[n], k) for n in PA}
def ankle_for(phi, sg):
    """ankle over the planted ball of the foot: phi = how far the foot has tipped up onto its toes (deg)"""
    c_, s_ = math.cos(R(phi)), math.sin(R(phi)); return V3(sg * 0.135, BALL_Y + 0.13 * c_ - 0.06 * s_, 0.012 + 0.055 * c_ + 0.133 * s_)
def apply(P, shudder=0.0, t=0.0, lift=0.0):
    rot = P['rot'] + V3(wob(t, 3.0, 1.0), wob(t, 3.0, 2.0), wob(t, 3.0, 3.0)) * shudder
    set_pose(P['hip'], tuple(rot), 0.0, P['neck'], P['head'], 0.0, 0.0,
             ankR=ankle_for(P['phi'], -1), poleR=V3(-P['pole'].x, P['hip'].y + P['pole'].y, P['pole'].z), ankL=ankle_for(P['phi'], 1), poleL=V3(P['pole'].x, P['hip'].y + P['pole'].y, P['pole'].z),
             curlR=P['curlR'], curlL=P['curlL'], lids=P['lids'], jaw=P['jaw'])
    for s_ in 'RL': FOOT[s_][0].rotation_quaternion = (Matrix.Rotation(R(P['phi']), 3, 'X') @ FOOT[s_][1]).to_quaternion()
    for f_ in range(1, 6):
        for s_ in 'RL':
            if f'toe{f_}-1.{s_}' in PB: rot_ = TOE_SIGN * min(P['phi'], 82.0); PB[f'toe{f_}-1.{s_}'].rotation_mode = 'XYZ'; PB[f'toe{f_}-1.{s_}'].rotation_euler = (R(rot_), 0, 0)
            for seg in (2, 3):
                if f'toe{f_}-{seg}.{s_}' in PB: PB[f'toe{f_}-{seg}.{s_}'].rotation_mode = 'XYZ'; PB[f'toe{f_}-{seg}.{s_}'].rotation_euler = (0, 0, 0)
    M = RIG.matrix_world.copy(); M3 = M.to_3x3()
    for s_, key, pk in (('R', 'hR', 'paR'), ('L', 'hL', 'paL')):
        sp, c, fd, pd, w = P[key]
        if sp == 'rig': c, fd, pd = M @ c, M3 @ fd, M3 @ pd
        if s_ == 'R' and lift: c = c + (M3 @ V3(-1, 0.2, 0)) * lift
        place_hand(s_, c, fd, pd, w); TGT['poleArm' + s_].location = M @ P[pk]
    bpy.context.view_layer.update()
    ground(P['kneel']); hand_out(('R',)); hand_on_top()
PS, PA_, PB2 = P_S(), P_A(), P_B()
K0 = 0.07                                                              # frame one: already going down
def man_pose(nb, u, t):
    """which pose at this moment"""
    if nb == 11:
        k = smooth(0.12, 0.8, u); P = blend(PS, PA_, k); lift = 0.04 * math.sin(math.pi * k)
        if u > 0.8: P = blend(PA_, PB2, K0 * smooth(0.8, 1.0, u))
        apply(P, 0.6 * k, t, lift); return
    if nb == 0:
        v = clamp(u / 0.4, 0, 1); k = K0 + (1 - K0) * v ** 1.7; bounce = math.exp(-max(u - 0.4, 0) * 9) * math.sin(max(u - 0.4, 0) * 30) * 0.02 if u > 0.4 else 0.0
        P = blend(PA_, PB2, min(k, 1.0)); P['hip'] = P['hip'] + V3(0, 0, 0.0); P['rot'] = P['rot'] + V3(120 * bounce + 6 * smooth(0.4, 0.9, u), 0, 0)
        apply(P, 0.8 + 0.6 * smooth(0.4, 0.6, u), t); return
    apply(PB2 | {'rot': PB2['rot'] + V3(6, 0, 0)}, 1.0, t)
def look(cp, ct, lens=35, fstop=8.0, focus=None, roll=0.0, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    q = d.to_track_quat('-Z', 'Y')
    if up is not None:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0): return Vector((wob(t, 7.0, seed), wob(t, 7.0, seed + 3.3), wob(t, 7.0, seed + 6.1))) * amt
def eval_centroid(o, idx=None):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    vs = me.vertices if idx is None else [me.vertices[i] for i in idx]; c = sum((oe.matrix_world @ v.co for v in vs), Vector()) / len(vs); oe.to_mesh_clear(); return c
def ease(a_, b_, k): return a_.lerp(b_, sm(clamp(k, 0, 1)))
# ================================================================ MODES and the story
MAN = [BODY, SUIT, HAIR] + HEADBITS
def room_mode(man=True):
    for o in ROOM: o.hide_render = False
    for o in MAN: o.hide_render = not man
    for i, sl in enumerate(BODY.material_slots): sl.material = BODY_MATS[i]
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = True
    PUFF.strength = 0.0
    for o in XRAY_OBJS + MACRO_A + MACRO_B: o.hide_render = True
    for lt in ROOM_L: lt.hide_render = False
    XL.hide_render = XL2.hide_render = True
    WBG.inputs['Color'].default_value = (0.01, 0.012, 0.02, 1)
def xray_mode():
    for o in ROOM + MACRO_A + MACRO_B: o.hide_render = True
    BODY.hide_render = False
    for o in [SUIT, HAIR] + HEADBITS: o.hide_render = True
    for i, sl in enumerate(BODY.material_slots): sl.material = XSKIN
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = False
    PUFF.strength = 0.004
    for o in XRAY_OBJS: o.hide_render = False
    for lt in ROOM_L: lt.hide_render = True
    XL.hide_render = XL2.hide_render = False
    WBG.inputs['Color'].default_value = (0.004, 0.012, 0.035, 1)
def macro_mode(which):
    for o in ROOM + MAN + XRAY_OBJS + MACRO_A + MACRO_B + ROOM_L + [XL, XL2]: o.hide_render = True
    for o in (MACRO_A if which == 'a' else MACRO_B): o.hide_render = False
    WBG.inputs['Color'].default_value = (0.05, 0.02, 0.004, 1) if which == 'a' else (0.012, 0.004, 0.005, 1)
def organs(t, art=0.0, pee=0.0, glow=0.3, pain=0.0, swell=0.0, fillto=-1.0, bones=1.0):
    for o in kind('artery') + kind('vein'): o['tt'] = t; o['flow'] = art; o['speed'] = 1.6; o['glow'] = 0.15 + 0.2 * art
    for o in kind('ureter'): o['tt'] = t; o['flow'] = pee * 2.0; o['speed'] = 1.2; o['glow'] = 0.25 + 0.3 * pee; o['fillto'] = -1.0
    URER['fillto'] = fillto
    for o in kind('kidney') + kind('pelvis') + kind('bladder'): o['pain'] = 0.0
    KIDR['pain'] = pain; PELR['pain'] = min(1.0, swell * 1.2)
    KIDR.scale = (1 + 0.05 * swell,) * 3; PELR.scale = (1 + 0.3 * swell, 1 + 0.3 * swell, 1 + 0.12 * swell)
    BODY['pain'] = pain; BODY['tt'] = t
def stone_at(s, t, small_s=None):
    p = ure_pt(s); STONE.location = p; STONE.rotation_euler = (t * 0.7 + s * 60, s * 90, t * 0.4); HALO.location = p; STONE.hide_render = HALO.hide_render = False
    SMALL.hide_render = small_s is None
    if small_s is not None: SMALL.location = ure_pt(small_s); SMALL.rotation_euler = (small_s * 80, t, 0)
def rw(p): return RIG.matrix_world @ Vector(p)
CAM0 = (V3(-1.75, -2.35, 0.95), V3(0.05, -0.2, 0.92), 30.0)            # frame one and the loop's last frame
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    xr = nb in (1, 2, 6, 8)
    PUFF.strength = 0.004 if xr else 0.0
    S.view_settings.exposure = 0.0
    if nb in (0, 1, 2, 6, 8, 11): man_pose(nb, u, t)
    WATER.scale = (1, 1, 0.02); STREAM.hide_render = True
    if nb == 0:                                             # he drops to his knees at the counter, hand to his side
        room_mode()
        cp, ct, ln = CAM0; k = smooth(0.0, 0.75, u)
        look(cp.lerp(V3(-1.25, -2.3, 0.5), k) + shake(t, 0.004 + 0.02 * math.exp(-abs(u - 0.4) * 14)), ct.lerp(V3(0.02, -0.55, 0.62), k), lerp(ln, 36, k), 5.6, focus=rw((0, 0, 1.1)))
    elif nb in (1, 2, 6, 8):
        xray_mode(); STONE.hide_render = HALO.hide_render = SMALL.hide_render = True
        tor = rw((0.0, -0.05, 1.04)); kid = rw(KC)
        if nb == 1:                                         # into him: the right kidney, deep under the ribs at his back
            organs(t, glow=0.3); KIDR['pain'] = 0.35 + 0.25 * math.sin(t * 5); k = smooth(0.0, 1.0, u)
            look(rw((-0.55, -1.6, 1.25)).lerp(rw((-0.32, -0.75, 1.16)), k), tor.lerp(kid, k), lerp(40, 55, k), 8.0, focus=kid)
        elif nb == 2:                                       # blood in (red), cleaned; the waste goes down both ureters to the bladder (yellow)
            organs(t, art=smooth(0.0, 0.3, u) * 1.4, pee=smooth(0.3, 0.6, u), glow=0.3); BLAD['pain'] = 0.0
            mid = rw((0.0, -0.05, 0.98)); k = smooth(0.2, 1.0, u)
            look(rw((-0.3, -0.95, 1.2)).lerp(rw((-0.12, -1.25, 1.02)), k), rw(KC + V3(0.04, 0, -0.01)).lerp(mid, k), lerp(50, 46, k), 9.0, focus=mid)
        elif nb == 6:                                       # the stone breaks loose from the funnel and drops into the ureter
            s = lerp(-0.03, 0.05, smooth(0.15, 0.85, u) ** 1.4); organs(t, pee=0.4, glow=0.25, pain=smooth(0.6, 1.0, u) * 0.8); stone_at(s, t)
            p = rw(ure_pt(s)); k = smooth(0, 1, u)
            look(rw(KC + V3(-0.16, -0.5, 0.06)).lerp(rw(KC + V3(-0.1, -0.42, -0.02)), k), rw(KC + V3(0.01, 0, -0.03)).lerp(p, 0.5), 70, 9.0, focus=p)
        else:                                               # pee backs up above the stone, the funnel swells, the pain comes in waves
            sw = smooth(0.0, 0.6, u); wave = 0.5 + 0.5 * math.sin(lt * 2 * math.pi * 1.25 - 1.2)
            organs(t, pee=0.2, glow=0.25, pain=0.25 + 0.75 * wave, swell=sw * (0.85 + 0.15 * wave), fillto=0.05 * sw + 0.001); stone_at(0.05, t * 0.2)
            UREL['flow'] = 1.6
            k = smooth(0, 1, u); look(rw((-0.42, -1.05, 1.22)).lerp(rw((-0.5, -1.3, 1.16)), k) + shake(t, 0.004 * wave), rw(KC + V3(0.03, 0, -0.07)), 55, 9.0, focus=kid)
    elif nb in (3, 4, 5):
        macro_mode('a')
        pack = smooth(0.1, 0.9, u) if nb == 3 else 1.0; join = smooth(0.0, 0.9, u) if nb == 4 else (1.0 if nb == 5 else 0.0); stack = smooth(0.0, 0.92, u) if nb == 5 else 0.0
        macro_a(pack, join, stack, t)
        WBG.inputs['Color'].default_value = tuple(Vector((0.09, 0.06, 0.012)).lerp(Vector((0.07, 0.025, 0.002)), pack)) + (1,)
        a_ = 0.5 + t * 0.12; rad = lerp(0.66, 0.58, pack) if nb == 3 else (lerp(0.58, 0.62, u) if nb == 4 else lerp(0.62, 0.5, smooth(0, 1, u)))
        look(MO + V3(math.sin(a_) * rad, -math.cos(a_) * rad, 0.1 + 0.05 * math.sin(t * 0.5)), MO, 42, 6.0 if nb == 3 else 8.0)
    elif nb in (7, 9):
        macro_mode('b'); USMALL.o.hide_render = True; USTONE.o.hide_render = False
        if nb == 7:                                         # it scrapes down the lining and jams where the tube is tight
            v = smooth(0.0, 0.62, u); zs = lerp(1.0, 0.05, 1 - (1 - v) ** 2.2); jam = smooth(0.62, 0.7, u); back = smooth(0.66, 1.0, u)
            ureter_set(t, zs, RS_BIG, narrow=1.0, back=0.75 * back, wave=0.0, z0=1.0, scrape=1.0, pee_to=zs + RS_BIG * 0.3 if back > 0 else None)
            USTONE.o.location = UO + V3(0, 0.005, zs) + shake(t, 0.004 * (1 - jam)); USTONE.o.rotation_euler = (zs * 2.2, zs * 1.1, 0.3)
            look(UO + V3(0.1, -1.55, 0.25).lerp(V3(0.06, -1.25, 0.12), smooth(0, 1, u)) + shake(t, 0.01 * math.exp(-abs(u - 0.64) * 16)), UO + V3(0, 0, clamp(zs * 0.75, 0.08, 0.6)), 50, 9.0)
        elif u < 0.48:                                      # a small stone: the squeeze waves carry it down and out
            v = u / 0.48; zs = lerp(1.0, -1.0, v); USTONE.o.hide_render = True; USMALL.o.hide_render = False
            ureter_set(t, zs, RS_SMALL, narrow=0.0, back=0.0, wave=0.7)
            USMALL.o.location = UO + V3(0.01, 0.01, zs); USMALL.o.rotation_euler = (t * 3, t * 2, 0)
            look(UO + V3(0.05, -1.5, 0.1 + zs * 0.55), UO + V3(0, 0, zs * 0.55), 50, 9.0)
        else:                                               # a big one: stuck. the waves hit it and it does not move
            ureter_set(t, 0.05, RS_BIG, narrow=1.0, back=0.9, wave=1.0, z0=1.4, scrape=1.0, pee_to=0.05 + RS_BIG * 0.3)
            USTONE.o.location = UO + V3(0, 0.005, 0.05) + shake(t, 0.002); USTONE.o.rotation_euler = (0.11, 0.055, 0.3)
            look(UO + V3(0.06, -1.3, 0.14) + shake(t, 0.003), UO + V3(0, 0, 0.1), 50, 9.0)
    elif nb == 10:                                          # water: the glass under the tap fills
        room_mode(man=False); lv = smooth(0.0, 0.95, u); S.view_settings.exposure = -1.3
        WATER.scale = (1, 1, 0.012 + 0.1 * lv); STREAM.hide_render = False; top = GL.z + 0.0085 + 0.012 + 0.1 * lv
        STREAM.location = (GL.x, GL.y, top - 0.002); STREAM.scale = (1 + 0.15 * math.sin(t * 40), 1 + 0.15 * math.cos(t * 33), (SK.z + 0.24) - top + 0.002)
        look(GL + V3(-0.42, -0.36, 0.22).lerp(V3(-0.34, -0.3, 0.2), smooth(0, 1, u)), GL + V3(0, 0, 0.09), 50, 4.0)
    else:                                                   # back at the counter: the pain starts, his hand goes to his side (= frame one)
        room_mode()
        cp, ct, ln = CAM0; k = smooth(0.0, 0.9, u)
        look(V3(-1.5, -2.5, 1.2).lerp(cp, k) + shake(t, 0.004), V3(0.08, -0.15, 1.0).lerp(ct, k), lerp(34, ln, k), 5.6, focus=rw((0, 0, 1.1)))

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

