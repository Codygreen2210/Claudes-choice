# What happens if you drop a penny off the Empire State Building (Blender, Cycles). No people: a stone-and-glass skyscraper
# (setbacks on the sides, the front a flat cliff of piers 1,250 ft / 381 m to the roof), a city of blocks around it, a sidewalk
# with scored concrete, a lamp post, a hydrant, taxis. A real-size penny (19.05 mm, 1.52 mm) falls with air drag (terminal ~25 mph,
# reached in ~15 m), tumbles, gets lifted by wind along the tower, lands 35 s later and settles like a spinning coin. A "no air"
# ghost penny falls the vacuum way. A 16 lb bowling ball (terminal ~186 mph, ~151 mph after 381 m, ~9.6 s) cracks the sidewalk.
#   python3 penny.py OUTDIR F0 F1 [--samples 40] [--scale 1.0] [--only f,f]     (stride.json / redo.json beside it)
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
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

# ================================================================ physics (numbers checked in the notes: vt penny 25 mph, ball 16 lb 8.5 in)
G = 9.81
VT_P = 25 * 0.44704                    # penny terminal speed, m/s
VT_B = 83.0                            # 16 lb bowling ball, Cd 0.47: ~186 mph
def fall_d(tau, vt): return vt * vt / G * math.log(math.cosh(G * max(tau, 0.0) / vt))
def fall_v(tau, vt): return vt * math.tanh(G * max(tau, 0.0) / vt)

# ================================================================ more material helpers
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
def pos_xyz(nt):
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sx.inputs[0]); return sx
def mixc(nt, fac, a_, b_):
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    if isinstance(fac, (int, float)): mx.inputs['Factor'].default_value = fac
    else: nt.links.new(fac, mx.inputs['Factor'])
    for k, v in (('A', a_), ('B', b_)):
        if isinstance(v, tuple): mx.inputs[k].default_value = v if len(v) == 4 else (*v, 1)
        else: nt.links.new(v, mx.inputs[k])
    return mx.outputs['Result']
def facade(name, base, glass=(0.035, 0.05, 0.075), lit=0.015, floor=3.8, bay=1.5, sill=0.3, mull=0.16, seed=0.0):
    """windows in a grid on any wall facing x or y (world position based): stone/brick between, dark glass, a few lit rooms"""
    m = mat(name, base, 0.85); nt = m.node_tree; b = N(m)['Principled BSDF']; sx = pos_xyz(nt)
    u = math_(nt, 'ADD', sx.outputs['X'], sx.outputs['Y'])
    fu = math_(nt, 'FRACT', math_(nt, 'DIVIDE', u, bay)); fz = math_(nt, 'FRACT', math_(nt, 'DIVIDE', sx.outputs['Z'], floor))
    win = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', fz, sill), math_(nt, 'GREATER_THAN', fu, mull))
    _g = nt.nodes.new('ShaderNodeNewGeometry'); _ns = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(_g.outputs['Normal'], _ns.inputs[0])
    roof = math_(nt, 'GREATER_THAN', math_(nt, 'ABSOLUTE', _ns.outputs['Z']), 0.5)
    win = math_(nt, 'MULTIPLY', win, math_(nt, 'SUBTRACT', 1.0, roof))
    cx = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'FLOOR', math_(nt, 'DIVIDE', u, bay)), cx.inputs['X'])
    nt.links.new(math_(nt, 'FLOOR', math_(nt, 'DIVIDE', sx.outputs['Z'], floor)), cx.inputs['Y']); cx.inputs['Z'].default_value = seed
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '3D'; nt.links.new(cx.outputs['Vector'], wn.inputs['Vector'])
    litm = math_(nt, 'MULTIPLY', win, math_(nt, 'GREATER_THAN', wn.outputs['Value'], 1.0 - lit))
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 5
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    stone = mixc(nt, nz.outputs['Fac'], tuple(c * 0.86 for c in base), tuple(min(1, c * 1.08) for c in base))
    gl = mixc(nt, wn.outputs['Value'], glass, tuple(c * 1.6 for c in glass))
    nt.links.new(mixc(nt, roof, mixc(nt, win, stone, gl), (0.3, 0.3, 0.31)), b.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); nt.links.new(win, rr.inputs['Value']); rr.inputs['To Min'].default_value = 0.85; rr.inputs['To Max'].default_value = 0.06
    nt.links.new(rr.outputs['Result'], b.inputs['Roughness']); nt.links.new(math_(nt, 'MULTIPLY', win, 0.6), b.inputs['Metallic'])
    b.inputs['Emission Color'].default_value = (1.0, 0.78, 0.5, 1); nt.links.new(math_(nt, 'MULTIPLY', litm, 1.2), b.inputs['Emission Strength'])
    bm_ = nt.nodes.new('ShaderNodeBump'); bm_.inputs['Strength'].default_value = 0.6; bm_.inputs['Distance'].default_value = 0.08
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, win), bm_.inputs['Height']); nt.links.new(bm_.outputs['Normal'], b.inputs['Normal'])
    return m
def concrete(name, base=(0.6, 0.585, 0.56), joint=1.5, groove=0.012):
    m = noisy(mat(name, base, 0.9), 3.0, 0.22, 0.08, coord='Object'); nt = m.node_tree; b = N(m)['Principled BSDF']; sx = pos_xyz(nt)
    gx = math_(nt, 'LESS_THAN', math_(nt, 'FRACT', math_(nt, 'DIVIDE', sx.outputs['X'], joint)), groove / joint)
    gy = math_(nt, 'LESS_THAN', math_(nt, 'FRACT', math_(nt, 'DIVIDE', sx.outputs['Y'], joint)), groove / joint)
    gr = math_(nt, 'MAXIMUM', gx, gy)
    fine = nt.nodes.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 900.0; fine.inputs['Detail'].default_value = 3
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], fine.inputs['Vector'])
    spots = nt.nodes.new('ShaderNodeTexNoise'); spots.inputs['Scale'].default_value = 7.0; spots.inputs['Detail'].default_value = 2
    nt.links.new(tc.outputs['Object'], spots.inputs['Vector'])
    old = b.inputs['Base Color'].links[0].from_socket
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 260.0; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    speck = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', vo.outputs['Distance'], 0.62), 0.35)
    dark = math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', spots.outputs['Fac'], 0.68), 0.25), speck)
    c1 = mixc(nt, dark, old, tuple(c * 0.55 for c in base))
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', gr, 0.7), c1, (0.2, 0.19, 0.18)), b.inputs['Base Color'])
    h = math_(nt, 'ADD', math_(nt, 'MULTIPLY', fine.outputs['Fac'], 0.4), math_(nt, 'MULTIPLY', gr, -1.0))
    bm_ = nt.nodes.new('ShaderNodeBump'); bm_.inputs['Strength'].default_value = 0.5; bm_.inputs['Distance'].default_value = 0.004
    nt.links.new(h, bm_.inputs['Height']); nt.links.new(bm_.outputs['Normal'], b.inputs['Normal']); return m

def boxes(name, items, m, parent=None):
    """many axis-aligned boxes in one object (fast): items = [(size, centre), ...]"""
    vs, fs = [], []
    for (sx_, sy_, sz_), (cx_, cy_, cz_) in items:
        o_ = len(vs); hx_, hy_, hz_ = sx_ / 2, sy_ / 2, sz_ / 2
        vs += [(cx_ + a_ * hx_, cy_ + b_ * hy_, cz_ + c_ * hz_) for a_ in (-1, 1) for b_ in (-1, 1) for c_ in (-1, 1)]
        fs += [(o_ + i, o_ + j, o_ + k, o_ + l) for i, j, k, l in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))]
    return mesh(name, vs, fs, m, parent, smooth_=False)
# ================================================================ the tower: the front (-y) a flat cliff of stone piers, setbacks on the other sides
FRONT = -25.0                          # front face of the piers
TOPZ = 381.35                          # the roof: 1,250 ft
TOPS = TOPZ + 0.003                    # the roof surface sits 3 mm over the tier box (no shared faces: they shadow each other black)
def stone(name, base, bw=1.2, bh=0.6, groove=0.012):
    """cut stone: blocks with thin dark joints on walls facing x or y"""
    m = noisy(mat(name, base, 0.8), 6.0, 0.16, 0.08); nt = m.node_tree; b = N(m)['Principled BSDF']; sx = pos_xyz(nt)
    u = math_(nt, 'ADD', sx.outputs['X'], sx.outputs['Y']); row = math_(nt, 'FLOOR', math_(nt, 'DIVIDE', sx.outputs['Z'], bh))
    gz = math_(nt, 'LESS_THAN', math_(nt, 'FRACT', math_(nt, 'DIVIDE', sx.outputs['Z'], bh)), groove / bh)
    gu = math_(nt, 'LESS_THAN', math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'ADD', u, math_(nt, 'MULTIPLY', row, bw * 0.5)), bw)), groove / bw)
    gr = math_(nt, 'MAXIMUM', gz, gu); old = b.inputs['Base Color'].links[0].from_socket
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', gr, 0.6), old, (0.25, 0.23, 0.2)), b.inputs['Base Color'])
    bm_ = nt.nodes.new('ShaderNodeBump'); bm_.inputs['Strength'].default_value = 0.5; bm_.inputs['Distance'].default_value = 0.004
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, gr), bm_.inputs['Height']); nt.links.new(bm_.outputs['Normal'], b.inputs['Normal']); return m
STONE_M = stone('limestone', (0.66, 0.62, 0.54))
TOWER_F = facade('tower_face', (0.72, 0.68, 0.6), seed=1.0)
TIERS = [(60.0, 35.0, 0.0, 25.0), (45.0, 30.0, 25.0, 85.0), (27.0, 20.0, 85.0, 330.0), (18.0, 8.0, 330.0, TOPZ)]   # (half x, back y, z0, z1)
TOWER = []
for i, (hx, yb, z0, z1) in enumerate(TIERS):
    y0 = FRONT + 0.45
    TOWER.append(box(f'tier_{i}', (2 * hx, yb - y0, z1 - z0), (0, (y0 + yb) / 2, (z0 + z1) / 2), TOWER_F))
    xs = [-hx + 1.5 + 3.0 * k for k in range(int((2 * hx - 2.5) // 3.0) + 1)]
    TOWER.append(boxes(f'piers_{i}', [((0.7, 0.5, z1 - z0), (x, FRONT + 0.25, (z0 + z1) / 2)) for x in xs], STONE_M))
    for zc in ([z1 - 0.6] if i < 3 else []) + [z0 + 0.6]:     # stone bands
        TOWER.append(box(f'band_{i}_{zc:.0f}', (2 * hx + 0.4, 0.9, 1.2), (0, FRONT + 0.3, zc), STONE_M, bv=0.05))
    for side in (1, -1):                                       # corner piers, wider
        TOWER.append(box(f'corner_{i}_{side}', (1.6, 1.4, z1 - z0), (side * (hx - 0.3), FRONT + 0.6, (z0 + z1) / 2), STONE_M))
ROOF = box('roof', (36.0, 32.5, 0.1), (0, FRONT + 0.5 + 16.25, TOPS - 0.05), concrete('roof_conc', (0.5, 0.49, 0.47), 1.2)); TOWER.append(ROOF)
TOWER.append(box('roof_cap', (36.6, 0.5, 0.35), (0, FRONT + 0.25, TOPS - 0.175), STONE_M))      # the stone cap of the front edge      # the stone cap of the front edge
MAST = lathe('mast', [(5.5, 0), (5.5, 12), (4.0, 12), (4.0, 28), (2.6, 28), (2.6, 40), (1.4, 40), (0.9, 55), (0.35, 62), (0.05, 64)], 32,
             noisy(mat('mast_steel', (0.7, 0.71, 0.72), 0.45, metal=0.7), 4.0), loc=(0, FRONT + 18.0, TOPZ)); TOWER.append(MAST)
for k in range(6):                                             # roof vents and boxes
    TOWER.append(box(f'roofbox_{k}', (2.0 + h1(k) * 3, 1.5 + h1(k + 9) * 2, 1.0 + h1(k + 3) * 1.6), (-12 + k * 4.6, FRONT + 6 + h1(k + 5) * 8, TOPZ + 0.6),
                     mat(f'rb_{k}', (0.55, 0.56, 0.58), 0.6, metal=0.3), bv=0.05))

# ================================================================ the street in front, the city around
GROUND = box('ground', (6000, 6000, 0.2), (0, 0, -0.1), noisy(mat('asphalt', (0.08, 0.078, 0.075), 0.9), 0.8, 0.25, 0.05, coord='Object'))
ASPH = noisy(mat('road', (0.075, 0.074, 0.072), 0.88), 40.0, 0.3, 0.06)
SIDEW = concrete('sidewalk', (0.47, 0.46, 0.44))
SW_Z = 0.15
STREET = [box('walk_front', (900, FRONT - (-31.0), SW_Z), (0, (FRONT - 31.0) / 2, SW_Z / 2), SIDEW),
          box('curb', (900, 0.3, SW_Z + 0.01), (0, -31.15, SW_Z / 2), noisy(mat('granite', (0.5, 0.5, 0.5), 0.6), 30.0, 0.2)),
          box('avenue', (900, 16.0, 0.02), (0, -39.3, 0.01), ASPH),
          box('walk_far', (900, 6.0, SW_Z), (0, -50.3, SW_Z / 2), SIDEW)]
YEL = mat('yellow_paint', (0.85, 0.62, 0.08), 0.55); WHT = mat('white_paint', (0.85, 0.85, 0.82), 0.55)
for dy in (-0.12, 0.12): STREET.append(box(f'yline_{dy}', (900, 0.1, 0.004), (0, -39.3 + dy, 0.022), YEL))
STREET.append(boxes('dashes', [((3.0, 0.12, 0.004), (k * 7.5 + (3 if r else 0), -43.4 if r else -35.2, 0.022)) for k in range(-60, 60) for r in (0, 1)], WHT))
# a lamp post, a hydrant, a trash can near where things land
POLE_M = mat('pole_green', (0.05, 0.12, 0.08), 0.45, metal=0.6, coat=0.3)
LAMP = [prim('cylinder', 'lamp_pole', POLE_M, loc=(5.5, -30.4, 4.6), radius=0.09, depth=9.0, vertices=24),
        prim('cylinder', 'lamp_base', POLE_M, loc=(5.5, -30.4, 0.6), radius=0.2, depth=0.9, vertices=24),
        box('lamp_arm', (0.1, 2.4, 0.1), (5.5, -31.5, 9.0), POLE_M, bv=0.02),
        box('lamp_head', (0.45, 0.9, 0.18), (5.5, -32.6, 8.92), POLE_M, bv=0.05)]
HYD_M = mat('hydrant_red', (0.6, 0.06, 0.04), 0.4, coat=0.5)
HYD = [lathe('hydrant', [(0.0, 0), (0.17, 0), (0.17, 0.06), (0.13, 0.08), (0.13, 0.55), (0.15, 0.58), (0.15, 0.62), (0.1, 0.7), (0.05, 0.76), (0.0, 0.77)], 32, HYD_M, loc=(-4.2, -30.4, SW_Z)),
       prim('cylinder', 'hyd_nozzle', HYD_M, loc=(-4.2, -30.58, SW_Z + 0.42), rot=(R(90), 0, 0), radius=0.05, depth=0.16, vertices=16)]
PARK = [box('lawn', (300, 300, 0.1), (0, -215, 0.05), noisy(mat('lawn', (0.12, 0.26, 0.07), 0.9, sheen=0.4), 0.15, 0.35, 0.05, coord='Object')),
        box('park_path_a', (300, 5, 0.12), (0, -215, 0.06), concrete('path_a', (0.62, 0.6, 0.55), 2.0)),
        box('park_path_b', (5, 300, 0.12), (0, -215, 0.06), concrete('path_b', (0.62, 0.6, 0.55), 2.0))]
for k in range(70):                                                # park trees: a trunk and a round crown
    tx_, ty_ = random.Random(k).uniform(-140, 140), random.Random(k + 99).uniform(-350, -70)
    if abs(tx_) < 6 or abs(ty_ + 215) < 6: continue
    hh = random.Random(k + 7).uniform(6, 11)
    PARK.append(prim('cylinder', f'trunk_{k}', mat('bark', (0.12, 0.08, 0.05), 0.9), loc=(tx_, ty_, hh * 0.3), radius=0.25, depth=hh * 0.6, vertices=8))
    PARK.append(prim('ico_sphere', f'crown_{k}', mat(f'leaf_{k % 3}', (0.08 + 0.03 * (k % 3), 0.2 + 0.04 * (k % 3), 0.05), 0.85, sheen=0.5), loc=(tx_, ty_, hh * 0.75), subdivisions=2, radius=hh * 0.38))
CAN = lathe('trash_can', [(0.0, 0), (0.26, 0), (0.3, 0.9), (0.31, 0.92), (0.0, 0.92)], 32, mat('can_wire', (0.08, 0.09, 0.08), 0.5, metal=0.6), loc=(8.2, -30.2, SW_Z))
def car(name, x, y, col, rot=0.0):
    body_m = mat(name + '_paint', col, 0.25, coat=1.0); glass_m = mat(name + '_glass', (0.02, 0.025, 0.03), 0.05, coat=1.0)
    root = empty(name, loc=(x, y, 0)); root.rotation_euler = (0, 0, rot)
    box(name + '_body', (4.7, 1.85, 0.75), (0, 0, 0.68), body_m, bv=0.18, parent=root)
    box(name + '_cab', (2.5, 1.65, 0.6), (-0.2, 0, 1.25), glass_m, bv=0.15, parent=root)
    for sx_ in (1.45, -1.45):
        for sy_ in (0.9, -0.9):
            prim('cylinder', f'{name}_w{sx_}{sy_}', mat(name + '_tire', (0.03, 0.03, 0.03), 0.7), parent=root, loc=(sx_, sy_, 0.34), rot=(R(90), 0, 0), radius=0.34, depth=0.24, vertices=24)
    return root
CARS = [car('taxi_a', -16.0, -33.0, (0.95, 0.72, 0.05)), car('taxi_b', 14.0, -33.1, (0.95, 0.72, 0.05)), car('car_c', 32.0, -37.2, (0.6, 0.62, 0.66)),
        car('taxi_d', -38.0, -41.5, (0.95, 0.72, 0.05), R(180)), car('car_e', 6.0, -45.2, (0.08, 0.1, 0.16), R(180)), car('taxi_f', -70.0, -37.2, (0.95, 0.72, 0.05))]
# the city: blocks of buildings on a grid, kept off the tower's block and the avenue in front
CITY_M = [facade('bldg_a', (0.55, 0.36, 0.28), seed=2.0), facade('bldg_b', (0.68, 0.64, 0.58), seed=3.0), facade('bldg_c', (0.42, 0.44, 0.47), seed=4.0, lit=0.08),
          facade('bldg_d', (0.62, 0.55, 0.45), seed=5.0), facade('glass_tower', (0.25, 0.33, 0.42), glass=(0.06, 0.1, 0.16), seed=6.0, sill=0.08, mull=0.06)]
CITY = []; rng = random.Random(7); _CB = {i: [] for i in range(5)}
for i in range(-12, 13):
    for j in range(-12, 13):
        cx_, cy_ = i * 110.0, j * 85.0 - 98.0
        if abs(cx_) < 180 and -430 < cy_ < 80: continue
        for k in range(rng.choice((1, 2, 2, 3))):
            w = rng.uniform(22, 48); d = rng.uniform(20, 36); far = math.hypot(cx_, cy_)
            h = rng.choice((rng.uniform(15, 45), rng.uniform(30, 90), rng.uniform(60, 160) if far < 900 else rng.uniform(20, 60)))
            if rng.random() < 0.06 and far < 1200: h = rng.uniform(180, 300)
            if far < 520: h = min(h, 110.0)
            px = cx_ + (k - 1) * 30 + rng.uniform(-6, 6); py = cy_ + rng.uniform(-14, 14)
            _CB[4 if h > 170 else rng.randrange(4)].append(((w, d, h), (px, py, h / 2)))
            if h > 40 and rng.random() < 0.5: _CB[rng.randrange(4)].append(((w * 0.6, d * 0.6, h * 0.18), (px, py, h + h * 0.09)))
CITY = [boxes(f'city_{i}', its, CITY_M[i]) for i, its in _CB.items() if its]

# ================================================================ the penny (19.05 mm across, 1.52 mm thick, a raised rim, a bust and words in relief)
COPPER = noisy(mat('copper', (0.93, 0.5, 0.33), 0.3, metal=1.0), 900.0, 0.25, 0.12, coord='Object')
COPPER_D = noisy(mat('copper_relief', (0.88, 0.46, 0.3), 0.36, metal=1.0), 1400.0, 0.3, 0.1, coord='Object')
GHOST_M = noisy(mat('ghost', (0.93, 0.5, 0.33), 0.3, metal=1.0, emit=(0.15, 0.4, 1.0), estr=0.25), 900.0, 0.25, 0.12, coord='Object')
PR, PT = 0.009525, 0.00076
def make_penny(name, m_body, m_rel):
    root = empty(name); root.rotation_mode = 'XYZ'
    prof = [(0.0, PT - 0.00014), (PR - 0.0009, PT - 0.00014), (PR - 0.0006, PT), (PR - 0.0001, PT), (PR, PT - 0.0001), (PR, -PT + 0.0001),
            (PR - 0.0001, -PT), (PR - 0.0006, -PT), (PR - 0.0009, -PT + 0.00014), (0.0, -PT + 0.00014)]
    body = lathe(name + '_disc', prof, 96, m_body, parent=root)
    bust = prim('uv_sphere', name + '_bust', m_rel, parent=root, loc=(-0.0006, -0.0002, PT - 0.00016), scale=(0.0041, 0.0052, 0.00017), segments=32, ring_count=16)
    shoulder = prim('uv_sphere', name + '_shoulder', m_rel, parent=root, loc=(0.0004, -0.0047, PT - 0.00016), scale=(0.0045, 0.0018, 0.00013), segments=24, ring_count=12)
    shield = box(name + '_shield', (0.0072, 0.0078, 0.00016), (0, -0.0005, -PT + 0.0001), m_rel, bv=0.0025, parent=root)
    parts_ = [body, bust, shoulder, shield]
    for txt, loc, sz, rz, under in (('IN GOD WE TRUST', (0, 0.0066, PT - 0.00012), 0.0012, 0, False), ('LIBERTY', (-0.0066, -0.0012, PT - 0.00012), 0.0011, R(90), False),
                                    ('2024', (0.0062, -0.0034, PT - 0.00012), 0.0012, 0, False), ('ONE CENT', (0, -0.0068, -PT + 0.00012), 0.0012, 0, True),
                                    ('UNITED STATES OF AMERICA', (0, 0.0068, -PT + 0.00012), 0.0008, 0, True)):
        bpy.ops.object.text_add(location=(0, 0, 0)); tx = bpy.context.active_object; tx.name = f'{name}_{txt[:6]}'
        tx.data.body = txt; tx.data.size = sz; tx.data.align_x = 'CENTER'; tx.data.align_y = 'CENTER'; tx.data.extrude = 0.00008; tx.data.materials.append(m_rel)
        tx.parent = root; tx.location = loc; tx.rotation_euler = (R(180) if under else 0, 0, rz); parts_.append(tx)
    root['parts'] = [p.name for p in parts_]
    return root
PEN = make_penny('penny', COPPER, COPPER_D)
PEN_REST = make_penny('penny_rest', COPPER, COPPER_D)
GHOST = make_penny('ghost', GHOST_M, COPPER_D)
def pen_vis(root, on):
    root.hide_render = not on
    for n in root['parts']: bpy.data.objects[n].hide_render = not on
# a bright ring that follows the penny in the far shots (so a 19 mm coin can be found in a 1,250 ft frame)
RING = prim('torus', 'find_ring', emis('ring_glow', (1.0, 0.85, 0.2), 6.0), major_radius=1.0, minor_radius=0.06, major_segments=64, minor_segments=8)
RING.visible_shadow = False
# ================================================================ the bowling ball (8.5 in, 16 lb): swirled resin, three finger holes
BALL_R = 0.108
BALL_M = mat('ball_resin', (0.05, 0.08, 0.35), 0.12, coat=1.0)
_bn = BALL_M.node_tree; _sw = _bn.nodes.new('ShaderNodeTexNoise'); _sw.inputs['Scale'].default_value = 9.0; _sw.inputs['Distortion'].default_value = 6.0; _sw.inputs['Detail'].default_value = 4
_btc = _bn.nodes.new('ShaderNodeTexCoord'); _bn.links.new(_btc.outputs['Object'], _sw.inputs['Vector'])
_bn.links.new(mixc(_bn, math_(_bn, 'POWER', _sw.outputs['Fac'], 3.0), (0.03, 0.05, 0.3), (0.55, 0.15, 0.6)), N(BALL_M)['Principled BSDF'].inputs['Base Color'])
BALL = prim('uv_sphere', 'ball', BALL_M, radius=BALL_R, segments=96, ring_count=48); BALL.rotation_mode = 'XYZ'
for k, (ax, ay, rr) in enumerate(((0.0, 0.0, 0.012), (R(-14), R(-11), 0.011), (R(-14), R(11), 0.011))):
    cut = prim('cylinder', f'hole_{k}', None, radius=rr, depth=0.12, vertices=24); cut.rotation_euler = (ax + R(-30), ay, 0)
    cut.location = Vector((0, 0, BALL_R)).copy(); cut.location.rotate(Euler((ax + R(-30), ay, 0)))
    md = BALL.modifiers.new(f'h{k}', 'BOOLEAN'); md.object = cut; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = BALL; bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(cut)
for p_ in BALL.data.polygons: p_.use_smooth = True

# ================================================================ wind lines (thin glowing dashes that bend around the falling thing)
def wind_mat(name, rate=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs[0])
    ph = math_(nt, 'ADD', math_(nt, 'MULTIPLY', sx.outputs['Z'], objattr(nt, 'freq')), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), -rate))
    dash = math_(nt, 'GREATER_THAN', math_(nt, 'SINE', math_(nt, 'MULTIPLY', ph, 6.2832)), 0.35)
    a_ = math_(nt, 'MULTIPLY', dash, objattr(nt, 'alpha'))
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.85, 0.93, 1.0, 1); em.inputs['Strength'].default_value = 3.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(a_, mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
def wind_set(name, R_obj, n, span, bend, width, freq):
    root = empty(name); names = []; wm = wind_mat(name + '_m'); rng_ = random.Random(len(name))
    for k in range(n):
        ang = 2 * math.pi * k / n + rng_.uniform(-0.2, 0.2); rad = R_obj * rng_.uniform(0.6, 1.9)
        pts = []
        for s in np.linspace(-span, span, 40):
            push = bend * R_obj * math.exp(-(s / (R_obj * 1.6)) ** 2) * (R_obj / max(rad, 1e-6))
            rr = rad + push
            pts.append((rr * math.cos(ang), rr * math.sin(ang), s))
        tb = tube(f'{name}_{k}', pts, width, wm, parent=root, seg=6, caps=False); tb.visible_shadow = False
        tb['tt'] = 0.0; tb['freq'] = freq * rng_.uniform(0.8, 1.2); tb['alpha'] = 0.0; names.append(tb.name)
    root['parts'] = names; return root
WIND = wind_set('wind_p', 0.0105, 16, 0.07, 1.6, 0.00011, 55.0)        # around the penny
WINDB = wind_set('wind_b', BALL_R, 18, 0.7, 0.25, 0.0016, 6.0)            # around the ball: barely bent
WINDU = wind_set('wind_up', 1.2, 22, 14.0, 0.4, 0.012, 0.35)              # the updraft along the tower
def wind_on(root, on, tt=0.0, alpha=0.8):
    for n in root['parts']:
        o = bpy.data.objects[n]; o.hide_render = not on; o['tt'] = tt; o['alpha'] = alpha
    root.hide_render = not on

# ================================================================ the impact: a crater, cracks, flying chunks, dust
IMP = V3(-1.3, -27.9, SW_Z)
CRATER_M = noisy(mat('crater', (0.11, 0.105, 0.1), 0.95), 60.0, 0.5, 0.05)
CRATER = lathe('crater', [(0.0, 0.0008), (0.31, 0.0008)], 48, CRATER_M, loc=IMP)          # a shattered patch, flat on the slab
for v in CRATER.data.vertices:
    r_ = math.hypot(v.co.x, v.co.y)
    if r_ > 0.2: a_ = math.atan2(v.co.y, v.co.x); k_ = 0.75 + 0.35 * math.sin(5 * a_ + 1.0) * math.sin(3 * a_); v.co.x *= k_; v.co.y *= k_
_rng = random.Random(11); CRACKS = []
for k in range(14):
    a0 = 2 * math.pi * k / 14 + _rng.uniform(-0.2, 0.2); pts = []; p = Vector((0.25 * math.cos(a0), 0.25 * math.sin(a0), 0.0)); ang = a0
    L_ = _rng.uniform(0.6, 1.6)
    for s in range(24):
        pts.append(p.copy()); ang += _rng.uniform(-0.35, 0.35); p = p + Vector((math.cos(ang), math.sin(ang), 0)) * (L_ / 24)
    c = tube(f'crack_{k}', [(x_, y_, 0.0) for x_, y_, _ in pts], lambda u: 0.0035 * (1 - u) + 0.0008, mat(f'crack_m{k}', (0.03, 0.028, 0.026), 0.95), seg=6)
    c.location = IMP + V3(0, 0, 0.0002); c.scale = (1, 1, 0.12); CRACKS.append(c)
RUBBLE = []
for k in range(26):                                                 # broken bits left around the hole
    rb = prim('ico_sphere', f'rubble_{k}', SIDEW, subdivisions=1, radius=1.0)
    for v in rb.data.vertices: v.co *= _rng.uniform(0.6, 1.3)
    for p_ in rb.data.polygons: p_.use_smooth = False
    s_ = _rng.uniform(0.008, 0.03); a_ = _rng.uniform(0, 2 * math.pi); r_ = _rng.uniform(0.12, 0.32)
    rb.scale = (s_, s_ * _rng.uniform(0.7, 1.2), s_ * 0.6); rb.location = IMP + V3(r_ * math.cos(a_), r_ * math.sin(a_), s_ * 0.3)
    rb.rotation_euler = (_rng.uniform(0, 3), _rng.uniform(0, 3), _rng.uniform(0, 3)); RUBBLE.append(rb)
CHUNKS = []
for k in range(36):
    ch = prim('ico_sphere', f'chunk_{k}', SIDEW, subdivisions=1, radius=1.0)
    for v in ch.data.vertices: v.co *= _rng.uniform(0.6, 1.3)
    s_ = _rng.uniform(0.012, 0.05); ch.scale = (s_, s_ * _rng.uniform(0.6, 1.2), s_ * _rng.uniform(0.4, 0.9)); ch.rotation_mode = 'XYZ'
    for p_ in ch.data.polygons: p_.use_smooth = False
    a_ = _rng.uniform(0, 2 * math.pi); sp = _rng.uniform(1.5, 7.0); up = _rng.uniform(1.5, 6.5)
    ch['v'] = (sp * math.cos(a_), sp * math.sin(a_), up); ch['p0'] = (0.22 * math.cos(a_), 0.22 * math.sin(a_), 0.01); ch['spin'] = (_rng.uniform(-30, 30), _rng.uniform(-30, 30), _rng.uniform(-30, 30))
    CHUNKS.append(ch)
DUST_M = bpy.data.materials.new('dust'); DUST_M.use_nodes = True; _dn = DUST_M.node_tree; _dn.nodes.remove(_dn.nodes['Principled BSDF'])
_dv = _dn.nodes.new('ShaderNodeVolumePrincipled'); _dv.inputs['Color'].default_value = (0.85, 0.82, 0.77, 1)
_dz = _dn.nodes.new('ShaderNodeTexNoise'); _dz.inputs['Scale'].default_value = 3.0; _dz.inputs['Detail'].default_value = 3
_dtc = _dn.nodes.new('ShaderNodeTexCoord'); _dn.links.new(_dtc.outputs['Object'], _dz.inputs['Vector'])
_sph = _dn.nodes.new('ShaderNodeTexGradient'); _sph.gradient_type = 'SPHERICAL'; _dn.links.new(_dtc.outputs['Object'], _sph.inputs['Vector'])
_dn.links.new(math_(_dn, 'MULTIPLY', math_(_dn, 'MULTIPLY', _sph.outputs['Fac'], _dz.outputs['Fac']), objattr(_dn, 'dens')), _dv.inputs['Density'])
_dn.links.new(_dv.outputs['Volume'], _dn.nodes['Material Output'].inputs['Volume'])
DUST = []
for k in range(5):
    d_ = prim('ico_sphere', f'dust_{k}', DUST_M, subdivisions=2, radius=1.0); d_['dens'] = 0.0; d_.visible_shadow = False
    d_['dir'] = (math.cos(k * 1.3) * 0.5, math.sin(k * 1.3) * 0.5, 0.25 + 0.1 * k); DUST.append(d_)
IMPACT = [CRATER] + CRACKS + CHUNKS + DUST + RUBBLE

# ================================================================ light: a late-afternoon sun on the front, sky gradient
SUNL = bpy.data.lights.new('sun', 'SUN'); SUNL.energy = 3.6; SUNL.color = (1.0, 0.93, 0.82); SUNL.angle = R(0.8)
SUN_O = bpy.data.objects.new('sun', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_mode = 'QUATERNION'
SUN_O.rotation_quaternion = (-Vector((-0.4, -0.62, 0.95))).to_track_quat('-Z', 'Y')
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Strength'].default_value = 1.0
_tc = wnt.nodes.new('ShaderNodeTexCoord'); _sx = wnt.nodes.new('ShaderNodeSeparateXYZ'); wnt.links.new(_tc.outputs['Generated'], _sx.inputs['Vector'])
SKYR = wnt.nodes.new('ShaderNodeValToRGB'); _el = SKYR.color_ramp.elements
_el[0].position = 0.0; _el[0].color = (0.55, 0.58, 0.62, 1); _el[1].position = 0.75; _el[1].color = (0.12, 0.3, 0.72, 1)
_e2 = _el.new(0.5); _e2.color = (0.78, 0.84, 0.92, 1); _e3 = _el.new(0.56); _e3.color = (0.45, 0.62, 0.9, 1)
_mr = wnt.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = -1.0; _mr.inputs['From Max'].default_value = 1.0
wnt.links.new(_sx.outputs['Z'], _mr.inputs['Value']); wnt.links.new(_mr.outputs['Result'], SKYR.inputs['Fac']); wnt.links.new(SKYR.outputs['Color'], WBG.inputs['Color'])
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.004; CAM.data.clip_end = 8000
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5
def look(cp, ct, lens=35, fstop=8.0, focus=None, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    if up is None: q = d.to_track_quat('-Z', 'Y')
    else:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length

# ================================================================ motion
END = TOTAL
Y_EDGE = FRONT - 0.003                          # the penny's centre just past the edge: it tips
P0 = V3(0.0, Y_EDGE, TOPS + PT)
def penny_drop(tau):
    """the penny that slides off the roof edge and falls with drag. tau = seconds since it left the edge (negative: still sliding)"""
    if tau < 0:
        s = clamp(-tau / 0.8, 0, 1)
        p = V3(0.0, Y_EDGE + 0.33 * s ** 1.6, TOPS + PT)
        tip = R(14) * smooth(-0.12, 0.0, tau)
        return p, Euler((-tip, 0, 0.6 + 2.0 * tau))
    d = fall_d(tau, VT_P)
    p = V3(0.5 * math.sin(0.8 * tau) + 0.12 * math.sin(2.7 * tau + 1.0) - 0.12, Y_EDGE - 2.2 * (1 - math.exp(-tau / 1.5)), TOPS + PT - d)
    ramp = smooth(0.0, 0.7, tau)
    return p, Euler((-R(14) - 8.5 * tau * ramp, 0.5 * math.sin(1.9 * tau) * ramp, 0.6 + 1.2 * tau))
def cam0(t):
    """beat 0: from the roof edge, then riding down with the penny (also where the loop ends)"""
    pen, _ = penny_drop(t - 0.25)
    base = V3(0.13, FRONT + 0.2, TOPS + 0.13); follow = pen + V3(0.09, -0.12, 0.14)      # out over the edge first, then down with it
    k = smooth(0.2, 0.75, t)
    return base.lerp(follow, k), pen + V3(0.0, -0.02, -0.03)
# the coin settling on the sidewalk like a spun coin: the tilt dies away while the wobble speeds up
LAND = V3(0.35, -27.55, SW_Z)
_WT = [0.0]; _PHI = [0.0]; _ph = 0.0
for i in range(1, 6 * 600):
    tau = i / 600; tilt = 0.42 * math.exp(-tau / 0.85)
    if tilt > 0.006: _ph += 2.0 / math.sqrt(tilt) / 600
    _WT.append(tau); _PHI.append(_ph)
def wobble(tau):
    tau = max(tau, 0.0); tilt = 0.42 * math.exp(-tau / 0.85); phi = float(np.interp(tau, _WT, _PHI))
    if tilt <= 0.006: tilt = 0.0
    M_ = Matrix.Rotation(phi, 3, 'Z') @ Matrix.Rotation(tilt, 3, 'X') @ Matrix.Rotation(-phi * 0.15, 3, 'Z')
    return LAND + V3(0, 0, PR * math.sin(tilt) + PT * math.cos(tilt)), M_.to_euler('XYZ')
T_LAND = B[6] + 1.55
def penny_land(t):
    """beat 6-7: the last 17 m down, a hop on the concrete, then the wobble"""
    if t < T_LAND:
        k = (T_LAND - t) / 1.55
        p = LAND + V3(0.45 * math.sin(3.1 * t) * k, -0.5 * k * math.sin(1.7 * t + 0.4), PT + 11.2 * (T_LAND - t))
        return p, Euler((-8.5 * t, 0.5 * math.sin(1.9 * t), 1.2 * t))
    tb = t - T_LAND
    if tb < 0.2:
        h = 0.028 * abs(math.sin(math.pi * tb / 0.13)) if tb < 0.13 else 0.006 * abs(math.sin(math.pi * (tb - 0.13) / 0.07))
        p, e = wobble(0.0); return p + V3(0, 0, h), Euler((e.x + (0.2 - tb) * 6.0, e.y, e.z))
    return wobble(tb - 0.2)
# the bowling ball: rolls slowly off the edge (0.3 m/s), falls with drag (lands ~2.9 m out, ~151 mph, ~9.6 s)
BX = IMP.x; ROLL_V = 0.3; BY0 = FRONT + 0.45; T_EDGE = (BY0 - FRONT) / ROLL_V
def ball_at(tau):
    """tau = seconds since it started rolling"""
    if tau < T_EDGE:
        y = BY0 - ROLL_V * tau; return V3(BX, y, TOPS + BALL_R), Euler((-(BY0 - y) / BALL_R, 0, 0))
    tf = tau - T_EDGE
    return V3(BX, FRONT - ROLL_V * tf, TOPS + BALL_R - fall_d(tf, VT_B)), Euler((-(BY0 - FRONT + ROLL_V * tf) / BALL_R, 0, 0.3 * tf))
T_HIT = B[11] + 0.12
SLOW = 0.22
def impact(ti):
    """ti: real seconds after the hit (negative: before)"""
    on = ti >= 0
    for o in IMPACT: o.hide_render = not on
    if not on: return
    CRATER.scale = (1, 1, 1) if ti > 0.012 else (ti / 0.012 + 0.05,) * 3
    for c in CRACKS: k = clamp(ti / 0.035, 0.02, 1.0); c.scale = (k, k, 0.25)
    for ch in CHUNKS:
        v = Vector(ch['v']); p0 = Vector(ch['p0']); tl = (v.z + math.sqrt(v.z * v.z + 2 * G * 0.01)) / G
        tt_ = min(ti, tl); p = IMP + p0 + v * tt_ + V3(0, 0, -0.5 * G * tt_ * tt_)
        if ti > tl: p = p + V3(v.x, v.y, 0) * 0.15 * (1 - math.exp(-(ti - tl) * 6)); p.z = SW_Z + ch.scale.z * 0.5
        ch.location = p; sp = Vector(ch['spin']) * min(ti, tl + 0.05); ch.rotation_euler = (sp.x, sp.y, sp.z)
    for d_ in DUST:
        s_ = 0.08 + 0.9 * ti ** 0.5; dr = Vector(d_['dir'])
        d_.location = IMP + dr * (s_ * 0.9) + V3(0, 0, 0.05); d_.scale = (s_, s_, s_ * 0.7); d_['dens'] = 3.0 * math.exp(-ti / 0.9) * smooth(0.0, 0.02, ti)
def ring_at(p, cp, size):
    RING.hide_render = False; RING.location = p; RING.rotation_mode = 'QUATERNION'
    RING.rotation_quaternion = (Vector(cp) - Vector(p)).to_track_quat('Z', 'Y'); r_ = (Vector(cp) - Vector(p)).length * size; RING.scale = (r_, r_, r_)

def state(t):
    t = clamp(t, 0.0, END - 1e-4); b = beat_at(t)
    for root in (PEN, GHOST, PEN_REST): pen_vis(root, False)
    BALL.hide_render = True; RING.hide_render = True; impact(-1)
    for w in (WIND, WINDB, WINDU): wind_on(w, False)
    def put(root, pe):
        p, e = pe; pen_vis(root, True); root.location = p; root.rotation_euler = e
    if b in (0, 1):
        put(PEN, penny_drop(t - 0.25)); cp, ct = cam0(t)
        if b == 0: look(cp, ct, lens=lerp(40, 26, smooth(0.3, 1.4, t)), fstop=11.0)
        else:
            u = (t - B[1]) / DUR[1]; cp = V3(-70, -330, 1.7).lerp(V3(-62, -315, 1.7), u)
            look(cp, V3(0, FRONT, 165), lens=20, fstop=16.0); ring_at(PEN.location, cp, 0.04)
    elif b == 2:                                    # no air: the ghost penny drops like a stone
        tau = (t - B[2]) * 2.75; gp = V3(0.6, FRONT - 1.4, TOPS - 0.5 * G * tau * tau)
        put(GHOST, (gp, Euler((R(78), 0.0, 0.25 * tau)))); look(gp + V3(0.07, -0.17, 0.03), gp + V3(-0.005, 0, -0.006), lens=45, fstop=2.8)
    elif b == 3:                                    # slow motion: the air shoves on the flat face, it flips and flutters
        tau = 5.0 + (t - B[3]) * 0.3; p, e = penny_drop(tau); put(PEN, (p, e))
        ang = 0.5 + (t - B[3]) * 0.3; look(p + V3(0.085 * math.sin(ang), -0.085 * math.cos(ang), 0.022), p, lens=55, fstop=9.0)
        WIND.location = p; wind_on(WIND, True, (t - B[3]) * 4.0, 0.85)
    elif b == 4:                                    # riding down with it: speeds up, then stops speeding up
        tau = (t - B[4]) * 0.82; p, e = penny_drop(tau); put(PEN, (p, e))
        look(p + V3(0.07, -0.13, 0.045), p + V3(0, 0.02, -0.01), lens=35, fstop=5.6, focus=p)
        WIND.location = p; wind_on(WIND, True, (t - B[4]) * 6.0, 0.35)
    elif b == 5:                                    # wind along the tower tosses it back up
        u = (t - B[5]) / DUR[5]
        p = V3(-0.5 + 2.2 * u, FRONT - 1.6 - 2.4 * u, 230.0 - 1.5 * u + 5.0 * smooth(0.15, 0.9, u))
        put(PEN, (p, Euler((-10.0 * (t - B[5]), 0.6 * math.sin(2.3 * t), 1.5 * t))))
        cp = p + V3(0.08, -0.16, 0.01); look(cp, p + V3(0, 0.0, -0.018), lens=35, fstop=5.6, focus=p)      # close, coin above the captions
        WINDU.location = V3(0.6, FRONT - 2.4, 232.0); wind_on(WINDU, True, (t - B[5]) * 4.0, 0.55)
    elif b in (6, 7):                               # 35 seconds later it lands, a hop and a wobble
        put(PEN, penny_land(t))
        if b == 6:
            p = PEN.location.copy(); cp = p + V3(0.10, -0.24, 0.08); cp.z = max(cp.z, SW_Z + 0.07)
            look(cp, p + V3(0, 0.02, -0.03), lens=30, fstop=4.0, focus=p)
        else:
            u = (t - B[7]) / DUR[7]; cp = LAND + V3(0.075, -0.085, 0.032).lerp(V3(0.06, -0.07, 0.024), u)
            look(cp, LAND + V3(0, 0, 0.004), lens=50, fstop=2.8)
    else:                                           # the bowling ball
        put(PEN_REST, wobble(10.0)); BALL.hide_render = False
        if b == 8:
            BALL.location, BALL.rotation_euler = ball_at(t - B[8] + 0.05)
            look(V3(BX + 0.35, FRONT + 1.25, TOPS + 0.22), V3(BX - 0.1, FRONT - 1.2, TOPS - 0.9), lens=22, fstop=8.0, focus=BALL.location)
        elif b == 9:
            tau = (B[9] - B[8] + 0.05) + (t - B[9]) * 1.25; BALL.location, BALL.rotation_euler = ball_at(tau); p = BALL.location.copy()
            look(p + V3(0.55, -0.85, 0.3), p + V3(0, 0.2, -0.05), lens=28, fstop=8.0, focus=p)
            WINDB.location = p; wind_on(WINDB, True, (t - B[9]) * 8.0, 0.6)
        elif b == 10:
            BALL.location = IMP + V3(0, 0, BALL_R + 67.0 * (B[11] - t)); BALL.rotation_euler = (-3.0 * t, 0, 0.3 * t)
            cp = IMP + V3(-1.2, -1.5, 0.3); dd = (BALL.location - cp).length      # long lens locked on the ball: it stays big while it falls, then a crash zoom out
            look(cp, BALL.location, lens=clamp(6.6 * dd, 18.0, 1600.0), fstop=16.0, focus=BALL.location)
        else:
            ti = (t - T_HIT) * SLOW if b == 11 else (B[12] - T_HIT) * SLOW + (t - B[12])
            BALL.location = IMP + V3(0, 0, BALL_R + (67.0 * -ti if ti < 0 else -0.07 * min(1.0, ti / 0.01))); BALL.rotation_euler = (-3.0 * T_HIT - (ti < 0) * 3.0 * ti, 0, 0.3 * T_HIT)
            impact(ti)
            if b == 11:
                sh = shake(t, 0.012 * math.exp(-max(ti, 0) / 0.08) * (ti > 0), 2.0)
                look(IMP + V3(1.5, -1.25, 0.32) + sh, IMP + V3(0, 0.1, 0.2), lens=30, fstop=5.6, focus=IMP + V3(0, 0, 0.1))
            else:                                   # rise from the crater back up to the roof: the loop
                u = (t - B[12]) / DUR[12]; k = smooth(0.12, 0.93, u); c0, _ = cam0(0.0); pp, _ = penny_drop(t - END - 0.25); t0 = pp + V3(0.0, -0.02, -0.03)
                a_, b_, c_, d_ = IMP + V3(1.9, -3.2, 1.1), IMP + V3(4.0, -16.0, 30.0), c0 + V3(0.15, -0.5, 1.2), c0
                cp = a_ * (1 - k) ** 3 + b_ * 3 * k * (1 - k) ** 2 + c_ * 3 * k * k * (1 - k) + d_ * k ** 3
                tg = IMP.lerp(t0, smooth(0.1, 0.85, u)); look(cp, tg, lens=lerp(30, 40, k), fstop=lerp(8.0, 11.0, k))
                put(PEN, penny_drop(t - END - 0.25))
def shake(t, amt, seed=0.0): return Vector((wob(t, 23.0, seed), wob(t, 23.0, seed + 3.3), wob(t, 23.0, seed + 6.1))) * amt

bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
ANIM = [CAM, PEN, GHOST, BALL, RING, WIND, WINDB, WINDU] + CHUNKS
def frame(f):
    t = f / FPS; d = 0.25 / FPS
    for o in ANIM: o.animation_data_clear()
    if beat_at(max(0.0, t - d)) == beat_at(min(END - 1e-4, t + d)) == beat_at(t):
        anim = ANIM                                       # beat 10: the camera tracks the ball, so blurring both keeps the ball sharp
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            state(tt_)
            for o in anim:
                o.keyframe_insert('location', frame=kf)
                o.keyframe_insert('rotation_quaternion' if o.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=kf)
    S.frame_set(f); state(t)
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

