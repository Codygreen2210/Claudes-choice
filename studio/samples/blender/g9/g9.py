# What 9 G's does to a fighter pilot, built and rendered in Blender (Cycles): a generic single-seat fighter (no markings) in a 9 G turn
# over farmland and cloud, the pilot in full gear (helmet, dark visor, mask, gloves, G-suit), an x-ray of his blood draining to his legs,
# his view going gray, tunnel, black, the jet diving at the ground and pulling up by itself.
#   python3 g9.py OUTDIR F0 F1 [--samples 64] [--scale 1.0] [--only f,f]       (stride.json / redo.json beside it: see ele.py)
import sys, os, math, json, argparse
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=64); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')          # save the built scene here (look-dev)
ap.add_argument('--gmeter', default='')         # write the G readout keys (for finish.json) and stop
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

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('cycles', default_set=False)
S = bpy.context.scene; S.render.engine = 'CYCLES'; S.render.fps = FPS
S.render.resolution_x = int(1080 * a.scale); S.render.resolution_y = int(1920 * a.scale); S.render.resolution_percentage = 100
C = S.cycles; C.device = 'CPU'; C.samples = a.samples; C.use_denoising = os.environ.get('NODN') is None; C.denoiser = 'OPENIMAGEDENOISE'
C.max_bounces = int(os.environ.get('G9_BOUNCES', 6)); C.diffuse_bounces = 2; C.glossy_bounces = 2; C.transmission_bounces = 4; C.volume_bounces = 0; C.transparent_max_bounces = 12
C.use_adaptive_sampling = True; C.adaptive_threshold = float(os.environ.get('G9_ADAPT', 0.03)); C.adaptive_min_samples = 12
if os.environ.get('G9_OLD'): C.max_bounces = 10; C.diffuse_bounces = 3; C.glossy_bounces = 4; C.transmission_bounces = 8; C.transparent_max_bounces = 24; C.use_adaptive_sampling = False
C.caustics_reflective = False; C.caustics_refractive = False; C.sample_clamp_indirect = 6.0
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'; S.view_settings.exposure = -0.6

# ---------------------------------------------------------------- materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior; b.inputs['Coat Weight'].default_value = coat; b.inputs['Alpha'].default_value = alpha
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

def jet_paint():
    """air-superiority gray: slightly glossy paint, darker panel lines (thin brick mortar on the object's own coordinates), faint grime"""
    m = mat('paint', (0.21, 0.225, 0.24), 0.42, coat=0.15); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, 0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 0.55; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 1.6; br.inputs['Row Height'].default_value = 0.7; br.offset = 0.37
    br.inputs['Color1'].default_value = (1, 1, 1, 1); br.inputs['Color2'].default_value = (1, 1, 1, 1); br.inputs['Mortar'].default_value = (0, 0, 0, 1)
    nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.8; nz.inputs['Detail'].default_value = 8; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeMapRange'); gr.inputs['To Min'].default_value = 0.86; gr.inputs['To Max'].default_value = 1.06; nt.links.new(nz.outputs['Fac'], gr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 0.55
    mul.inputs['A'].default_value = (0.21, 0.225, 0.24, 1); nt.links.new(br.outputs['Color'], mul.inputs['B'])
    mul2 = nt.nodes.new('ShaderNodeMix'); mul2.data_type = 'RGBA'; mul2.blend_type = 'MULTIPLY'; mul2.inputs['Factor'].default_value = 1.0
    nt.links.new(mul.outputs['Result'], mul2.inputs['A']); nt.links.new(gr.outputs['Result'], mul2.inputs['B'])
    nt.links.new(mul2.outputs['Result'], b.inputs['Base Color'])
    bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.35; bu.inputs['Distance'].default_value = 0.002; bu.invert = True
    nt.links.new(br.outputs['Fac'], bu.inputs['Height']); nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.34; rr.inputs['To Max'].default_value = 0.55; nt.links.new(nz.outputs['Fac'], rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], b.inputs['Roughness']); return m
PAINT = jet_paint()
PAINT_D = noisy(mat('paint_dark', (0.07, 0.075, 0.08), 0.5), 6.0, 0.2)
RADOME = noisy(mat('radome', (0.16, 0.17, 0.18), 0.55), 3.0, 0.1)
NOZZLE = noisy(mat('nozzle', (0.12, 0.11, 0.1), 0.38, metal=0.9), 9.0, 0.35, 0.15)
NOZ_IN = mat('nozzle_in', (0.01, 0.01, 0.01), 0.9)
INTAKE = mat('intake', (0.006, 0.006, 0.007), 0.9)
COCK = noisy(mat('cockpit', (0.035, 0.038, 0.042), 0.62), 30.0, 0.2, 0.1)
COCK_L = noisy(mat('cockpit_lt', (0.075, 0.08, 0.085), 0.55), 30.0, 0.15)
BLACK = mat('black', (0.01, 0.01, 0.011), 0.45)
METAL = mat('metal', (0.6, 0.6, 0.62), 0.3, metal=1.0)
YELLOW = mat('yellow', (0.75, 0.55, 0.02), 0.45)
SEATC = noisy(mat('seat_cushion', (0.05, 0.06, 0.04), 0.85), 60.0, 0.25)
GLASS_HUD = mat('hud_glass', (0.9, 0.95, 0.92), 0.0, trans=1.0, ior=1.5); N(GLASS_HUD)['Principled BSDF'].inputs['Thin Wall'].default_value = True

def canopy_glass():
    """thin canopy: a faint gold tint, real reflections of sky and sun for camera rays, light passes straight through for shadows/indirect"""
    m = bpy.data.materials.new('canopy'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.55
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (0.93, 0.9, 0.78, 1)
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.02; gl.inputs['Color'].default_value = (1.0, 0.86, 0.6, 1)
    mp = nt.nodes.new('ShaderNodeMath'); mp.operation = 'MULTIPLY_ADD'; mp.inputs[1].default_value = 0.55; mp.inputs[2].default_value = 0.03
    nt.links.new(fr.outputs['Fac'], mp.inputs[0])
    geo = nt.nodes.new('ShaderNodeNewGeometry'); bk = nt.nodes.new('ShaderNodeMapRange'); bk.inputs['To Min'].default_value = 1.0; bk.inputs['To Max'].default_value = 0.12
    nt.links.new(geo.outputs['Backfacing'], bk.inputs['Value']); mb = nt.nodes.new('ShaderNodeMath'); mb.operation = 'MULTIPLY'
    nt.links.new(mp.outputs['Value'], mb.inputs[0]); nt.links.new(bk.outputs['Result'], mb.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(mb.outputs['Value'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(gl.outputs['BSDF'], mx.inputs[2])
    lp = nt.nodes.new('ShaderNodeLightPath'); tr2 = nt.nodes.new('ShaderNodeBsdfTransparent'); tr2.inputs['Color'].default_value = (0.95, 0.93, 0.85, 1)
    mc = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(lp.outputs['Is Camera Ray'], mc.inputs['Fac']); nt.links.new(tr2.outputs['BSDF'], mc.inputs[1]); nt.links.new(mx.outputs['Shader'], mc.inputs[2])
    nt.links.new(mc.outputs['Shader'], out.inputs['Surface']); return m
CANOPY = canopy_glass()

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
def loft(name, sections, m, parent=None, cap0=True, cap1=True, skip=None):
    """sections: list of rings (lists of 3D points, same count). Rings are joined in order; skip(i, k) can leave a face out (an opening)."""
    vs = [p for ring in sections for p in ring]; n = len(sections[0]); fs = []
    for i in range(len(sections) - 1):
        for k in range(n):
            if skip and skip(i, k): continue
            k2 = (k + 1) % n; fs.append((i * n + k, i * n + k2, (i + 1) * n + k2, (i + 1) * n + k))
    if cap0: fs.append(tuple(range(n))[::-1])
    if cap1: fs.append(tuple((len(sections) - 1) * n + k for k in range(n)))
    return mesh(name, vs, fs, m, parent)
def interp(table, x):
    """piecewise-smooth (Catmull-Rom) through (x, value) pairs, clamped at the ends"""
    xs = [p[0] for p in table]
    if x <= xs[0]: return table[0][1]
    if x >= xs[-1]: return table[-1][1]
    i = max(k for k in range(len(xs) - 1) if xs[k] <= x); u = (x - xs[i]) / (xs[i + 1] - xs[i])
    p0 = table[max(i - 1, 0)][1]; p1 = table[i][1]; p2 = table[i + 1][1]; p3 = table[min(i + 2, len(table) - 1)][1]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
def tube(name, pts, r, m, parent=None, seg=16, uvlen=False, caps=True):
    """a swept tube along pts (rotation-minimising frames); r may be a function of the 0..1 position. uvlen: UV u = arc length (for flowing textures)."""
    pts = [Vector(p) for p in pts]; n = len(pts); rings = []; T0 = (pts[1] - pts[0]).normalized()
    up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized(); Bn = T0.cross(Nn)
    acc = [0.0]
    for i in range(1, n): acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        rr = r(i / (n - 1)) if callable(r) else r
        rings.append([pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
    vs = [p for ring in rings for p in ring]; fs = []
    for i in range(n - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    if caps: fs.append(tuple(range(seg))[::-1]); fs.append(tuple((n - 1) * seg + k for k in range(seg)))
    o = mesh(name, vs, fs, m, parent)
    if uvlen:
        uvl = o.data.uv_layers.new(name='UVMap')
        for poly in o.data.polygons:
            for li in poly.loop_indices:
                vi = o.data.loops[li].vertex_index; ring = vi // seg
                uvl.data[li].uv = (acc[min(ring, n - 1)], (vi % seg) / seg)
    return o

# ================================================================ THE JET (local: +X forward, +Y left, +Z up; metres; origin = pilot's seat reference)
JET = empty('jet')
def superring(x, w, ht, hb, cz, n=48, pw=2.4, shift=0.0):
    """one fuselage cross-section: a superellipse, taller on top (ht) than below (hb)"""
    ring = []
    for k in range(n):
        th = 2 * math.pi * k / n; c_, s_ = math.cos(th), math.sin(th)
        y = w * math.copysign(abs(c_) ** (2 / pw), c_); z = (ht if s_ > 0 else hb) * math.copysign(abs(s_) ** (2 / pw), s_)
        ring.append(Vector((x, y, cz + z + shift)))
    return ring
FX = [-7.9, -7.3, -6.0, -4.0, -2.0, 0.0, 1.5, 2.6, 3.6, 4.6, 5.6, 6.6, 7.5, 8.1]
FW = [0.56, 0.60, 0.70, 0.80, 0.83, 0.82, 0.74, 0.64, 0.58, 0.50, 0.40, 0.27, 0.12, 0.02]
FHT = [0.56, 0.62, 0.86, 0.95, 0.92, 0.80, 0.62, 0.48, 0.46, 0.42, 0.36, 0.25, 0.11, 0.02]
FHB = [0.56, 0.60, 0.66, 0.70, 0.70, 0.66, 0.62, 0.58, 0.52, 0.42, 0.32, 0.22, 0.10, 0.02]
FCZ = [0.0, 0.0, 0.0, 0.02, 0.04, 0.04, 0.02, -0.02, -0.04, -0.06, -0.08, -0.1, -0.12, -0.13]
fus_tab = lambda arr: list(zip(FX, arr))
NS = 140
xs = [lerp(FX[0], FX[-1], (i / (NS - 1)) ** 1.0) for i in range(NS)]
def in_cockpit(x, k, n=48):
    th = 2 * math.pi * k / n
    return 1.95 < x < 4.75 and math.sin(th) > 0.55
FUS_RINGS = [superring(x, max(interp(fus_tab(FW), x), 0.004), max(interp(fus_tab(FHT), x), 0.004), max(interp(fus_tab(FHB), x), 0.004), interp(fus_tab(FCZ), x)) for x in xs]
FUS = loft('fuselage', FUS_RINGS, PAINT, JET, cap0=True, cap1=False, skip=lambda i, k: in_cockpit(xs[i], k) or in_cockpit(xs[i + 1], k))
subsurf(FUS, 1)
# nose cone (radome) colour: the last 1.6 m as a separate darker shell slightly outside
RAD = loft('radome', [superring(x, max(interp(fus_tab(FW), x), 0.003) * 1.004, max(interp(fus_tab(FHT), x), 0.003) * 1.004, max(interp(fus_tab(FHB), x), 0.003) * 1.004, interp(fus_tab(FCZ), x))
                      for x in [lerp(6.55, 8.1, i / 39) for i in range(40)]], RADOME, JET, cap0=False, cap1=False)
# chin intake: a rounded duct under the cockpit/forward fuselage, its mouth at x = 3.0
def intake_ring(x, k_open):
    w = interp([(-1.5, 0.42), (0.0, 0.48), (1.5, 0.52), (3.0, 0.55)], x); h = interp([(-1.5, 0.30), (0.0, 0.36), (1.5, 0.42), (3.0, 0.46)], x)
    cz = interp([(-1.5, -0.62), (0.0, -0.74), (1.5, -0.84), (3.0, -0.86)], x)
    return superring(x, w, h * 0.55, h, cz, n=40, pw=3.0)
INT = loft('intake', [intake_ring(x, 0) for x in [lerp(-1.5, 3.0, i / 23) for i in range(24)]], PAINT, JET, cap0=False, cap1=False); subsurf(INT, 1)
INT_IN = loft('intake_in', [[p - Vector((0, 0, 0)) for p in superring(x, 0.48, 0.2, 0.38, -0.86, n=40, pw=3.0)] for x in (2.2, 2.99)], INTAKE, JET, cap0=True, cap1=False)
# lip of the intake mouth
LIP = tube('intake_lip', [p for p in superring(3.0, 0.535, 0.245, 0.445, -0.86, n=40, pw=3.0)] + [superring(3.0, 0.535, 0.245, 0.445, -0.86, n=40, pw=3.0)[0]], 0.022, PAINT, JET, seg=10, caps=False)

def airfoil_ring(chord, le_x, y, z, th, n=40, twist=0.0):
    """a thin symmetric airfoil (NACA 00xx shape) as a ring of points in the x-z plane at span y"""
    pts = []
    for k in range(n):
        u = k / (n - 1); xc = 0.5 * (1 - math.cos(math.pi * u))
        yt = 5 * th * (0.2969 * math.sqrt(xc) - 0.126 * xc - 0.3516 * xc ** 2 + 0.2843 * xc ** 3 - 0.1036 * xc ** 4)
        pts.append((xc, yt))
    ring = [Vector((le_x - xc * chord, y, z + yt * chord)) for xc, yt in pts] + [Vector((le_x - xc * chord, y, z - yt * chord)) for xc, yt in reversed(pts[1:-1])]
    return ring
def wing(side):
    s = 1 if side == 'L' else -1; rings = []
    for i in range(18):
        u = i / 17; y = lerp(0.72, 4.75, u)
        le = lerp(1.25, -2.55, u); te = lerp(-3.65, -3.55, u); ch = le - te
        rings.append([Vector((p.x, p.y * s, p.z)) for p in airfoil_ring(ch, le, y, lerp(0.05, 0.12, u), lerp(0.05, 0.035, u))])
    o = loft('wing' + side, rings, PAINT, JET, cap0=True, cap1=True); return o
WINGS = [wing('L'), wing('R')]
def lerx(side):
    """the strake that blends the wing root forward along the fuselage"""
    s = 1 if side == 'L' else -1; rings = []
    for i in range(14):
        u = i / 13; x = lerp(4.3, 1.0, u); half = lerp(0.0, 0.46, u ** 0.8)
        y0 = interp(fus_tab(FW), x) * 0.92; z = lerp(-0.02, 0.06, u)
        rings.append([Vector((x, (y0 + half * (1 - abs(c))) * s, z + 0.03 * c)) for c in [-1, -0.5, 0, 0.5, 1, 0.5, 0, -0.5]])
    vs, fs = [], []
    for i in range(14):
        x = lerp(4.3, 1.0, i / 13); half = lerp(0.0, 0.5, (i / 13) ** 0.75); y0 = interp(fus_tab(FW), x) * 0.9; z = lerp(-0.03, 0.06, i / 13)
        vs += [Vector((x, y0 * s, z + 0.035)), Vector((x, (y0 + half) * s, z)), Vector((x, y0 * s, z - 0.035))]
    for i in range(13):
        a0 = i * 3; b0 = (i + 1) * 3
        fs += [(a0, b0, b0 + 1, a0 + 1), (a0 + 1, b0 + 1, b0 + 2, a0 + 2)] if s > 0 else [(a0, a0 + 1, b0 + 1, b0), (a0 + 1, a0 + 2, b0 + 2, b0 + 1)]
    return mesh('lerx' + side, vs, fs, PAINT, JET)
LERX = [lerx('L'), lerx('R')]
def stab(side):
    s = 1 if side == 'L' else -1; rings = []
    for i in range(10):
        u = i / 9; y = lerp(0.6, 2.95, u); le = lerp(-4.55, -6.35, u); te = lerp(-7.25, -7.05, u)
        rings.append([Vector((p.x, p.y * s, p.z - 0.18 * u)) for p in airfoil_ring(le - te, le, y, 0.05, 0.045)])
    return loft('stab' + side, rings, PAINT, JET)
STABS = [stab('L'), stab('R')]
def fin():
    rings = []
    for i in range(12):
        u = i / 11; z = lerp(0.78, 3.3, u); le = lerp(-2.9, -5.85, u); te = lerp(-6.6, -7.05, u)
        ring = airfoil_ring(le - te, le, 0.0, 0.0, lerp(0.06, 0.04, u))
        rings.append([Vector((p.x, p.z, z)) for p in ring])
    return loft('fin', rings, PAINT, JET)
FIN = fin()
FINCAP = loft('fin_tip', [[Vector((p.x, p.z, 3.3 + dz)) for p in airfoil_ring(1.2, -5.85, 0, 0, 0.04)] for dz in (0.0, 0.012)], RADOME, JET)
# engine nozzle: a lathe of petals, dark metal; the hot dark hole inside
def lathe(name, prof, seg=64, m=None, parent=None, axis='x', loc=(0, 0, 0)):
    vs, fs = [], []; n = len(prof)
    for i in range(seg):
        a_ = 2 * math.pi * i / seg; c_, s_ = math.cos(a_), math.sin(a_)
        for r_, h_ in prof:
            vs.append((h_, r_ * c_, r_ * s_) if axis == 'x' else (r_ * c_, r_ * s_, h_))
    for i in range(seg):
        i2 = (i + 1) % seg
        for k in range(n - 1): fs.append((i * n + k, i * n + k + 1, i2 * n + k + 1, i2 * n + k))
    o = mesh(name, vs, fs, m, parent, loc=loc); return o
NOZ = lathe('nozzle', [(0.56, -7.75), (0.55, -8.0), (0.5, -8.6), (0.47, -8.75), (0.44, -8.75), (0.46, -8.4), (0.48, -8.0)], 64, NOZZLE, JET)
NOZH = lathe('nozzle_hole', [(0.46, -8.3), (0.3, -8.1), (0.0, -8.05)], 48, NOZ_IN, JET)
# wingtip rails (generic launch rails, empty)
RAILS = [prim('cube', 'rail' + s_, PAINT, JET, loc=(-2.85, sg * 4.82, 0.1), scale=(1.45, 0.05, 0.07)) for s_, sg in (('L', 1), ('R', -1))]
[bevel(r_, 0.015) for r_ in RAILS]
# canopy: a bubble from x = 2.0 to 5.0 over the open cockpit, a frame at the back
def canopy_ring(x, n=48, grow=0.0):
    w = interp([(1.85, 0.42), (2.4, 0.5), (3.4, 0.5), (4.3, 0.44), (5.0, 0.3), (5.45, 0.05)], x) + grow
    h = interp([(1.85, 0.42), (2.4, 0.62), (3.2, 0.66), (4.2, 0.55), (5.0, 0.3), (5.45, 0.04)], x) + grow
    base = interp(fus_tab(FCZ), x) + 0.28
    ring = []
    for k in range(n):
        th = math.pi * k / (n - 1); c_, s_ = math.cos(th), math.sin(th)
        ring.append(Vector((x, w * math.copysign(abs(c_) ** (2 / 2.3), c_), base + h * max(s_, 0.0) ** (2 / 2.3))))
    return ring
CXS = [lerp(1.85, 5.45, i / 59) for i in range(60)]
CAN = loft('canopy', [canopy_ring(x) for x in CXS], CANOPY, JET, cap0=False, cap1=False)
CAN.data.polygons.foreach_set('use_smooth', [True] * len(CAN.data.polygons))
# canopy frame (rear bow + sills)
CFRAME = [tube('canopy_bow', canopy_ring(2.05, 24, 0.012), 0.025, PAINT_D, JET, seg=8, caps=False),
          tube('sillL', [Vector((x, interp([(1.85, 0.42), (2.4, 0.5), (3.4, 0.5), (4.3, 0.44), (5.0, 0.3)], x) + 0.01, interp(fus_tab(FCZ), x) + 0.29)) for x in [lerp(1.9, 4.95, i / 20) for i in range(21)]], 0.022, PAINT_D, JET, seg=8),
          tube('sillR', [Vector((x, -interp([(1.85, 0.42), (2.4, 0.5), (3.4, 0.5), (4.3, 0.44), (5.0, 0.3)], x) - 0.01, interp(fus_tab(FCZ), x) + 0.29)) for x in [lerp(1.9, 4.95, i / 20) for i in range(21)]], 0.022, PAINT_D, JET, seg=8)]
# dorsal spine behind the canopy, blending into the fuselage top
SPINE = loft('spine', [superring(x, interp([(-3.0, 0.2), (0.0, 0.36), (1.4, 0.42), (1.95, 0.42)], x), interp([(-3.0, 0.02), (0.0, 0.2), (1.4, 0.36), (1.95, 0.4)], x), 0.01,
                                interp(fus_tab(FCZ), x) + interp(fus_tab(FHT), x) * 0.82, n=32, pw=2.2) for x in [lerp(-3.0, 1.95, i / 29) for i in range(30)]], PAINT, JET, cap0=False, cap1=True)

# ---------------------------------------------------------------- cockpit (inside the opening: x 1.95..4.75)
COCKPIT = empty('cockpit', JET)
def cbox(name, sx, sy, sz, loc, m, rot=(0, 0, 0), bv=0.01, parent=COCKPIT):
    o = prim('cube', name, m, parent, loc=loc, rot=rot, scale=(sx, sy, sz), size=1)
    if bv: bevel(o, bv)
    return o
TUB = [cbox('tub_floor', 2.9, 0.86, 0.04, (3.3, 0, -0.62), COCK), cbox('tub_wallL', 2.9, 0.04, 0.95, (3.3, 0.45, -0.15), COCK), cbox('tub_wallR', 2.9, 0.04, 0.95, (3.3, -0.45, -0.15), COCK),
       cbox('tub_back', 0.05, 0.9, 1.0, (1.97, 0, -0.1), COCK)]
# side consoles
CONS = [cbox('consoleL', 1.25, 0.16, 0.05, (2.75, 0.36, 0.06), COCK_L, rot=(R(-6), 0, 0)), cbox('consoleR', 1.25, 0.16, 0.05, (2.75, -0.36, 0.06), COCK_L, rot=(R(6), 0, 0))]
CONS += [cbox('consoleLb', 1.25, 0.16, 0.5, (2.75, 0.36, -0.2), COCK), cbox('consoleRb', 1.25, 0.16, 0.5, (2.75, -0.36, -0.2), COCK)]
# switches and knobs on the consoles
for side, sg in (('L', 1), ('R', -1)):
    for i in range(14):
        x = 2.22 + 0.08 * i + 0.03 * h1(i + (5 if sg < 0 else 0)); y = sg * (0.31 + 0.09 * h1(i * 3 + sg))
        if h1(i * 7 + sg) < 0.5: prim('cylinder', 'knob', BLACK, COCKPIT, loc=(x, y, 0.1), vertices=16, radius=0.011, depth=0.02)
        else: prim('cube', 'switch', METAL, COCKPIT, loc=(x, y, 0.1), rot=(R(20), 0, 0), size=1, scale=(0.006, 0.006, 0.03))
# instrument panel: a hood and a face with three screens
PANEL = cbox('panel', 0.08, 0.84, 0.42, (4.12, 0, 0.03), COCK, rot=(0, R(-14), 0))
GLARE = cbox('glareshield', 0.42, 0.78, 0.05, (4.03, 0, 0.27), BLACK, rot=(0, R(4), 0))
def screen_mat(name, seed):
    """a lit multi-function display: dark glass with a generic green/cyan picture (procedural rings and bars)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.005, 0.006, 0.006, 1); b.inputs['Roughness'].default_value = 0.12; b.inputs['Coat Weight'].default_value = 0.5
    tc = nt.nodes.new('ShaderNodeTexCoord'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-0.5 + 0.2 * h1(seed), -0.5, 0); nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 2.0 + 2 * h1(seed + 1); wv.inputs['Distortion'].default_value = 0
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].position = 0.9; rp.color_ramp.elements[1].position = 0.97
    nt.links.new(wv.outputs['Fac'], rp.inputs['Fac'])
    e_ = nt.nodes.new('ShaderNodeMix'); e_.data_type = 'RGBA'; e_.inputs['A'].default_value = (0.0, 0.0, 0.0, 1); e_.inputs['B'].default_value = (0.25, 1.0, 0.45, 1) if seed % 2 else (0.3, 0.85, 1.0, 1)
    nt.links.new(rp.outputs['Color'], e_.inputs['Factor']); nt.links.new(e_.outputs['Result'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.2
    return m
def screen(name, loc, w, h, seed):
    o = prim('plane', name, screen_mat(name + '_m', seed), COCKPIT, loc=loc, rot=(R(90), 0, R(90)), size=1, scale=(w, h, 1))
    o.rotation_euler = (R(90) + R(0), R(-14) * 0, R(90)); o.rotation_mode = 'XYZ'
    return o
SCREENS = [screen('mfdL', (4.075, 0.2, 0.02), 0.15, 0.15, 1), screen('mfdR', (4.075, -0.2, 0.02), 0.15, 0.15, 2), screen('mfdC', (4.075, 0.0, -0.08), 0.12, 0.1, 3)]
for s_ in SCREENS: s_.rotation_euler = Euler((R(90), R(14), R(90)), 'XYZ'); s_.location.x -= 0.004
# HUD: frame and the two glass combiners; the symbology is a per-frame picture on the front combiner
HUDF = []
def hud_mat():
    m = bpy.data.materials.new('hud'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    img = bpy.data.images.new('hud_img', 512, 512, alpha=True); tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Linear'
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['UV'], tex.inputs['Vector'])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.35, 1.0, 0.45, 1); em.inputs['Strength'].default_value = 6.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(tex.outputs['Alpha'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.0; gl.inputs['Color'].default_value = (0.25, 0.3, 0.28, 1)
    nt.links.new(mx.outputs['Shader'], ad.inputs[0]); nt.links.new(gl.outputs['BSDF'], ad.inputs[1])
    lp = nt.nodes.new('ShaderNodeLightPath'); tr2 = nt.nodes.new('ShaderNodeBsdfTransparent'); mc = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mc.inputs['Fac']); nt.links.new(tr2.outputs['BSDF'], mc.inputs[1]); nt.links.new(ad.outputs['Shader'], mc.inputs[2])
    nt.links.new(mc.outputs['Shader'], out.inputs['Surface']); return m, img
HUD_M, HUD_IMG = hud_mat()
HUDG = prim('plane', 'hud_glass', HUD_M, COCKPIT, loc=(3.98, 0, 0.5), size=1, scale=(0.24, 0.24, 1)); HUDG.rotation_euler = Euler((R(90), R(-8), R(90)), 'XYZ')
# side-stick (right console), throttle (left), rudder pedals
STICK = empty('stick', COCKPIT, (3.0, -0.37, 0.09))
STK = [prim('cylinder', 'stick_base', BLACK, STICK, loc=(0, 0, 0.02), vertices=24, radius=0.035, depth=0.04),
       prim('cylinder', 'stick_shaft', BLACK, STICK, loc=(0, 0, 0.08), vertices=20, radius=0.016, depth=0.1)]
SGRIP = prim('uv_sphere', 'stick_grip', BLACK, STICK, loc=(0.005, 0, 0.165), segments=24, ring_count=12, scale=(0.035, 0.028, 0.065)); subsurf(SGRIP, 1)
THR = empty('throttle', COCKPIT, (2.8, 0.37, 0.1))
TGRIP = prim('cube', 'throttle_grip', BLACK, THR, loc=(0, 0, 0.07), size=1, scale=(0.07, 0.04, 0.11)); bevel(TGRIP, 0.015)
PEDALS = [cbox('pedal' + s_, 0.03, 0.09, 0.16, (3.95, sg * 0.14, -0.43), METAL, rot=(0, R(-25), 0)) for s_, sg in (('L', 1), ('R', -1))]
# ejection seat: bucket, back, headrest, cushions, the pull handle between the knees
SEAT = empty('seat', COCKPIT, (2.35, 0, -0.42))
SEATP = [cbox('seat_pan', 0.48, 0.48, 0.08, (0.28, 0, 0.06), SEATC, parent=SEAT, bv=0.025),
         cbox('seat_back', 0.08, 0.5, 0.8, (0.02, 0, 0.47), SEATC, rot=(0, R(-26), 0), parent=SEAT, bv=0.03),
         cbox('seat_frame', 0.12, 0.6, 1.35, (-0.08, 0, 0.62), COCK_L, rot=(0, R(-26), 0), parent=SEAT, bv=0.02),
         cbox('headrest', 0.12, 0.34, 0.28, (-0.24, 0, 1.15), SEATC, rot=(0, R(-26), 0), parent=SEAT, bv=0.04),
         cbox('seat_sideL', 0.5, 0.06, 0.22, (0.25, 0.27, 0.12), COCK_L, parent=SEAT), cbox('seat_sideR', 0.5, 0.06, 0.22, (0.25, -0.27, 0.12), COCK_L, parent=SEAT)]
HANDLE = tube('eject_handle', [Vector((0.5, 0.06, 0.08)), Vector((0.56, 0.06, 0.14)), Vector((0.56, -0.06, 0.14)), Vector((0.5, -0.06, 0.08))], 0.012, YELLOW, SEAT, seg=10)

# ================================================================ SKY, SUN, GROUND, CLOUDS (world: z up, ground at z = 0)
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
SKY = wnt.nodes.new('ShaderNodeTexSky'); SKY.sky_type = 'MULTIPLE_SCATTERING'; SKY.sun_elevation = R(38); SKY.sun_rotation = R(140); SKY.altitude = 3000.0
SKY.sun_disc = True; SKY.sun_intensity = 1.0
WBG = wnt.nodes['Background']; WBG.inputs['Strength'].default_value = 0.22; wnt.links.new(SKY.outputs['Color'], WBG.inputs['Color'])
# the dark world for the x-ray beats (switched per frame)
XBG = wnt.nodes.new('ShaderNodeBackground'); XBG.inputs['Color'].default_value = (0.004, 0.008, 0.02, 1); XBG.inputs['Strength'].default_value = 1.0
WMIX = wnt.nodes.new('ShaderNodeMixShader'); wnt.links.new(WBG.outputs['Background'], WMIX.inputs[1]); wnt.links.new(XBG.outputs['Background'], WMIX.inputs[2])
wnt.links.new(WMIX.outputs['Shader'], wnt.nodes['World Output'].inputs['Surface'])
SUND = Vector((math.cos(R(38)) * math.sin(R(140)), -math.cos(R(38)) * math.cos(R(140)), math.sin(R(38))))   # matches the sky's sun (rotation measured from -y toward +x)
SUN = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(SUN)
SUN.data.energy = 3.0; SUN.data.angle = R(0.6); SUN.data.color = (1.0, 0.96, 0.9)
SUN.rotation_mode = 'QUATERNION'; SUN.rotation_quaternion = (-SUND).to_track_quat('-Z', 'Y')

def ground_mat():
    """farmland from above: rectangular fields (two brick patterns at different angles, mixed by region) in greens, browns and straw,
    hedgerows between them, crop rows inside, dark woods, all fading into blue haze with distance"""
    m = bpy.data.materials.new('ground'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = 0.92
    Ln = lambda a_, b_: nt.links.new(a_, b_)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    def bricks(rot, scale, seed):
        mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, R(rot)); mp.inputs['Location'].default_value = (seed * 137.0, seed * 59.0, 0)
        Ln(tc.outputs['Object'], mp.inputs['Vector'])
        br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = scale; br.inputs['Mortar Size'].default_value = 0.012; br.inputs['Mortar Smooth'].default_value = 0.3
        br.inputs['Brick Width'].default_value = 0.62; br.inputs['Row Height'].default_value = 0.3; br.offset = 0.31; br.squash = 1.6; br.squash_frequency = 3
        br.inputs['Color1'].default_value = (0, 0, 0, 1); br.inputs['Color2'].default_value = (1, 1, 1, 1); br.inputs['Bias'].default_value = 0.0
        Ln(mp.outputs['Vector'], br.inputs['Vector']); return br, mp
    b1, m1 = bricks(14, 0.0021, 1); b2, m2 = bricks(-31, 0.0016, 2)
    reg = nt.nodes.new('ShaderNodeTexNoise'); reg.inputs['Scale'].default_value = 0.00025; reg.inputs['Detail'].default_value = 2; Ln(tc.outputs['Object'], reg.inputs['Vector'])
    rg = nt.nodes.new('ShaderNodeMapRange'); rg.inputs['From Min'].default_value = 0.48; rg.inputs['From Max'].default_value = 0.52; Ln(reg.outputs['Fac'], rg.inputs['Value'])
    pick = nt.nodes.new('ShaderNodeMix'); pick.data_type = 'RGBA'; Ln(rg.outputs['Result'], pick.inputs['Factor']); Ln(b1.outputs['Color'], pick.inputs['A']); Ln(b2.outputs['Color'], pick.inputs['B'])
    mort = nt.nodes.new('ShaderNodeMix'); mort.data_type = 'FLOAT'; Ln(rg.outputs['Result'], mort.inputs['Factor']); Ln(b1.outputs['Fac'], mort.inputs[2]); Ln(b2.outputs['Fac'], mort.inputs[3])
    bw0 = nt.nodes.new('ShaderNodeRGBToBW'); Ln(pick.outputs['Result'], bw0.inputs['Color'])
    spread = nt.nodes.new('ShaderNodeMath'); spread.operation = 'MULTIPLY'; spread.inputs[1].default_value = 17.3; Ln(bw0.outputs['Val'], spread.inputs[0])
    bw = nt.nodes.new('ShaderNodeMath'); bw.operation = 'FRACT'; Ln(spread.outputs['Value'], bw.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
    cols = [(0.035, 0.06, 0.016), (0.11, 0.095, 0.045), (0.05, 0.085, 0.02), (0.17, 0.14, 0.07), (0.028, 0.045, 0.014), (0.13, 0.12, 0.055),
            (0.07, 0.1, 0.03), (0.085, 0.065, 0.035), (0.045, 0.075, 0.02), (0.15, 0.13, 0.08)]
    cr.elements[0].color = (*cols[0], 1); cr.elements[1].position = 1 / len(cols); cr.elements[1].color = (*cols[1], 1)
    for k in range(2, len(cols)): e_ = cr.elements.new(k / len(cols)); e_.color = (*cols[k], 1)
    Ln(bw.outputs['Value'], ramp.inputs['Fac'])
    # crop rows inside each field
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 0.12; wv.inputs['Distortion'].default_value = 0.5; Ln(m1.outputs['Vector'], wv.inputs['Vector'])
    wr = nt.nodes.new('ShaderNodeMapRange'); wr.inputs['To Min'].default_value = 0.85; wr.inputs['To Max'].default_value = 1.1; Ln(wv.outputs['Fac'], wr.inputs['Value'])
    rows = nt.nodes.new('ShaderNodeMix'); rows.data_type = 'RGBA'; rows.blend_type = 'MULTIPLY'; rows.inputs['Factor'].default_value = 1.0; Ln(ramp.outputs['Color'], rows.inputs['A']); Ln(wr.outputs['Result'], rows.inputs['B'])
    # fine mottling
    fn = nt.nodes.new('ShaderNodeTexNoise'); fn.inputs['Scale'].default_value = 0.05; fn.inputs['Detail'].default_value = 8; Ln(tc.outputs['Object'], fn.inputs['Vector'])
    fm = nt.nodes.new('ShaderNodeMapRange'); fm.inputs['To Min'].default_value = 0.78; fm.inputs['To Max'].default_value = 1.18; Ln(fn.outputs['Fac'], fm.inputs['Value'])
    mot = nt.nodes.new('ShaderNodeMix'); mot.data_type = 'RGBA'; mot.blend_type = 'MULTIPLY'; mot.inputs['Factor'].default_value = 1.0; Ln(rows.outputs['Result'], mot.inputs['A']); Ln(fm.outputs['Result'], mot.inputs['B'])
    # hedgerows (the brick mortar): dark green lines
    hd = nt.nodes.new('ShaderNodeMix'); hd.data_type = 'RGBA'; hd.inputs['B'].default_value = (0.015, 0.03, 0.01, 1)
    hm = nt.nodes.new('ShaderNodeMath'); hm.operation = 'SUBTRACT'; hm.inputs[0].default_value = 1.0; Ln(mort.outputs[0], hm.inputs[1])
    Ln(hm.outputs['Value'], hd.inputs['Factor']); Ln(mot.outputs['Result'], hd.inputs['A'])
    # woods: large blotches, dark and lumpy
    wn = nt.nodes.new('ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = 0.0011; wn.inputs['Detail'].default_value = 6; Ln(tc.outputs['Object'], wn.inputs['Vector'])
    wm = nt.nodes.new('ShaderNodeMapRange'); wm.inputs['From Min'].default_value = 0.57; wm.inputs['From Max'].default_value = 0.6; Ln(wn.outputs['Fac'], wm.inputs['Value'])
    tn = nt.nodes.new('ShaderNodeTexVoronoi'); tn.inputs['Scale'].default_value = 0.12; Ln(tc.outputs['Object'], tn.inputs['Vector'])
    tcol = nt.nodes.new('ShaderNodeMix'); tcol.data_type = 'RGBA'; tcol.inputs['A'].default_value = (0.008, 0.02, 0.006, 1); tcol.inputs['B'].default_value = (0.03, 0.055, 0.016, 1)
    Ln(tn.outputs['Distance'], tcol.inputs['Factor'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; Ln(wm.outputs['Result'], mix.inputs['Factor']); Ln(hd.outputs['Result'], mix.inputs['A']); Ln(tcol.outputs['Result'], mix.inputs['B'])
    Ln(mix.outputs['Result'], b.inputs['Base Color'])
    bh = nt.nodes.new('ShaderNodeMath'); bh.operation = 'MULTIPLY_ADD'; bh.inputs[2].default_value = 0.0; Ln(wm.outputs['Result'], bh.inputs[0]); Ln(tn.outputs['Distance'], bh.inputs[1])
    bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.8; bu.inputs['Distance'].default_value = 4.0
    Ln(bh.outputs['Value'], bu.inputs['Height']); Ln(bu.outputs['Normal'], b.inputs['Normal'])
    # haze by distance (camera rays)
    lp = nt.nodes.new('ShaderNodeLightPath'); hz = nt.nodes.new('ShaderNodeMath'); hz.operation = 'MULTIPLY'; hz.inputs[1].default_value = -1 / 9000.0
    Ln(lp.outputs['Ray Length'], hz.inputs[0]); ex = nt.nodes.new('ShaderNodeMath'); ex.operation = 'EXPONENT'; Ln(hz.outputs['Value'], ex.inputs[0])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; Ln(ex.outputs['Value'], inv.inputs[1])
    hzc = nt.nodes.new('ShaderNodeEmission'); hzc.inputs['Color'].default_value = (0.42, 0.55, 0.75, 1); hzc.inputs['Strength'].default_value = 0.7
    msh = nt.nodes.new('ShaderNodeMixShader'); Ln(inv.outputs['Value'], msh.inputs['Fac']); Ln(b.outputs['BSDF'], msh.inputs[1]); Ln(hzc.outputs['Emission'], msh.inputs[2])
    Ln(msh.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface'])
    return m, hz
GROUND_M, HAZE = ground_mat()
def ground():
    """60 km of gently rolling farmland (low hills from noise), finer near the middle"""
    n = 220; size = 60000.0; vs = []; fs = []
    for j in range(n):
        for i in range(n):
            u = (i / (n - 1) - 0.5); v = (j / (n - 1) - 0.5)
            x = size * u * abs(u) * 2; y = size * v * abs(v) * 2          # denser near the middle
            z = 120 * mnoise.fractal(Vector((x / 4000, y / 4000, 0.3)), 0.5, 2.0, 4) + 40 * mnoise.noise(Vector((x / 900, y / 900, 2.1)))
            vs.append((x, y, z))
    for j in range(n - 1):
        for i in range(n - 1): fs.append((j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i))
    return mesh('ground', vs, fs, GROUND_M)
GROUND = ground()
def ground_h(x, y):
    return 120 * mnoise.fractal(Vector((x / 4000, y / 4000, 0.3)), 0.5, 2.0, 4) + 40 * mnoise.noise(Vector((x / 900, y / 900, 2.1)))
def cloud_mat(seed):
    """a cumulus card: soft noise shape, lit from the sun side (a gradient across the card), thin transparent edges"""
    m = bpy.data.materials.new('cloud%d' % seed); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.6; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.62
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed * 3.7, seed * 1.3, 0); nt.links.new(tc.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'QUADRATIC_SPHERE'; mg = nt.nodes.new('ShaderNodeMapping'); mg.inputs['Location'].default_value = (-1, -1, 0); mg.inputs['Scale'].default_value = (2, 2, 1)
    nt.links.new(tc.outputs['UV'], mg.inputs['Vector']); nt.links.new(mg.outputs['Vector'], gr.inputs['Vector'])
    ml = nt.nodes.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'; nt.links.new(nz.outputs['Fac'], ml.inputs[0]); nt.links.new(gr.outputs['Fac'], ml.inputs[1])
    th = nt.nodes.new('ShaderNodeMapRange'); th.inputs['From Min'].default_value = 0.22; th.inputs['From Max'].default_value = 0.42; nt.links.new(ml.outputs['Value'], th.inputs['Value'])
    sh = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['UV'], sh.inputs['Vector'])
    lit = nt.nodes.new('ShaderNodeMix'); lit.data_type = 'RGBA'; lit.inputs['A'].default_value = (0.42, 0.47, 0.56, 1); lit.inputs['B'].default_value = (1.25, 1.22, 1.15, 1)
    lm = nt.nodes.new('ShaderNodeMath'); lm.operation = 'MULTIPLY_ADD'; lm.inputs[1].default_value = 0.8; lm.inputs[2].default_value = 0.0
    nt.links.new(sh.outputs['Y'], lm.inputs[0]); lsum = nt.nodes.new('ShaderNodeMath'); lsum.operation = 'ADD'; nt.links.new(lm.outputs['Value'], lsum.inputs[0]); nt.links.new(nz.outputs['Fac'], lsum.inputs[1])
    lc = nt.nodes.new('ShaderNodeMath'); lc.operation = 'SUBTRACT'; lc.inputs[1].default_value = 0.3; nt.links.new(lsum.outputs['Value'], lc.inputs[0])
    nt.links.new(lc.outputs['Value'], lit.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(lit.outputs['Result'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(th.outputs['Result'], mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    return m
CLOUD_MS = [cloud_mat(k) for k in range(6)]
CLOUDS = []
for k in range(70):          # a broken layer of cumulus tops at 1300-1900 m, spread over 12 km around the turn
    ang = h1(k * 3.1) * 2 * math.pi; rad = 900 + 6500 * h1(k * 5.3) ** 0.7
    c_ = Vector((rad * math.cos(ang), rad * math.sin(ang), 1300 + 600 * h1(k * 7.7)))
    sz = 500 + 900 * h1(k * 2.9)
    o = prim('plane', 'cloud', CLOUD_MS[k % 6], None, loc=c_, size=1, scale=(sz, sz * 0.55, 1)); CLOUDS.append(o)
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
# a few closer puffs at the jet's height for speed in the turn shots (placed on the turn circle each frame)
NEAR = [prim('plane', 'puff', CLOUD_MS[k % 6], None, size=1, scale=(160, 90, 1)) for k in range(8)]
for o in NEAR: o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False

# ---------------------------------------------------------------- vapor: sheets over the wings and trails off the wingtips in hard pulls
def vapor_mat(name, base_alpha=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    mp = nt.nodes.new('ShaderNodeMapping'); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'vap'
    fade = nt.nodes.new('ShaderNodeAttribute'); fade.attribute_name = 'fade'
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(nz.outputs['Fac'], m1.inputs[0]); nt.links.new(at.outputs['Fac'], m1.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs['Value'], m2.inputs[0]); nt.links.new(fade.outputs['Fac'], m2.inputs[1])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.25; mr.inputs['From Max'].default_value = 0.75; mr.inputs['To Max'].default_value = base_alpha
    nt.links.new(m2.outputs['Value'], mr.inputs['Value'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tl = nt.nodes.new('ShaderNodeBsdfTranslucent'); tl.inputs['Color'].default_value = (1, 1, 1, 1)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.85, 0.9, 1.0, 1); em.inputs['Strength'].default_value = 0.45
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tl.outputs['BSDF'], ad.inputs[0]); nt.links.new(em.outputs['Emission'], ad.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(mr.outputs['Result'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(ad.outputs['Shader'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m, mp
VAP_M, VAP_MAP = vapor_mat('vapor', 0.75)
TRAIL_M, TRAIL_MAP = vapor_mat('trail', 0.32)
def vapor_sheet(side):
    """a thin curved sheet just over the wing's upper surface, thickest near the leading edge, fading toward tip and trailing edge"""
    s = 1 if side == 'L' else -1; vs, fs, fade = [], [], []
    nu, nv = 16, 12
    for i in range(nu):
        u = i / (nu - 1); y = lerp(0.9, 4.6, u); le = lerp(1.0, -2.45, u) if y < 4.6 else -2.45; te = lerp(-3.6, -3.5, u)
        for j in range(nv):
            v = j / (nv - 1); x = lerp(le, te - 0.6, v)
            vs.append(Vector((x, y * s, 0.16 + 0.05 * u + 0.22 * math.sin(math.pi * min(v * 1.4, 1)) * (1 - 0.4 * u))))
            fade.append(math.sin(math.pi * u) ** 0.5 * (1 - v) ** 0.6)
    for i in range(nu - 1):
        for j in range(nv - 1): fs.append((i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1))
    o = mesh('vapor' + side, vs, fs, VAP_M, JET)
    at = o.data.attributes.new('fade', 'FLOAT', 'POINT'); at.data.foreach_set('value', fade); o['vap'] = 0.0
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.12; sol.offset = 0
    o.visible_shadow = False; return o
VAPS = [vapor_sheet('L'), vapor_sheet('R')]
def trail(side):
    """a long thin tube off the wingtip, streaming back (in the jet's frame), fading out behind"""
    s = 1 if side == 'L' else -1; pts = [Vector((-2.5 - 1.6 * k, (4.8 + 0.02 * k) * s, 0.1 + 0.015 * k)) for k in range(30)]
    o = tube('trail' + side, pts, lambda u: 0.025 + 0.22 * u, TRAIL_M, JET, seg=12, caps=False)
    fade = [max(0.0, 1 - (vi // 12) / 29) ** 1.5 for vi in range(len(o.data.vertices))]
    at = o.data.attributes.new('fade', 'FLOAT', 'POINT'); at.data.foreach_set('value', fade); o['vap'] = 0.0; o.visible_shadow = False
    return o
TRAILS = [trail('L'), trail('R')]

CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.02; CAM.data.clip_end = 80000

# ================================================================ THE PILOT (MakeHuman man from pilot.blend, see pilot_build.py) in full gear
PB_FILE = next(p_ for p_ in (os.path.join(HERE, 'pilot.blend'), '/root/vt/n38/g9/pilot.blend') if os.path.exists(p_))
with bpy.data.libraries.load(PB_FILE, link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n in ('Human', 'Human.rig', 'Human.male_worksuit01', 'Human.shoes05')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_worksuit01']; BOOTS = bpy.data.objects['Human.shoes05']
for o in (BODY, SUIT, BOOTS):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
    for p_ in o.data.polygons: p_.use_smooth = True
subsurf(BODY, 1); subsurf(SUIT, 1)
# seated in the seat, leaning back with it (rig space: he faces -Y, his left is +X)
RIG.parent = SEAT; RIG.rotation_mode = 'XYZ'; RIG.rotation_euler = (R(-20), 0, R(90))
bpy.context.view_layer.update()
_root = RIG.data.bones['root'].head_local
RIG.location = Vector((0.2, 0, 0.21)) - RIG.rotation_euler.to_matrix() @ Vector(_root)
bpy.context.view_layer.update()
# ---- materials: flight suit sage, dark boots, gloves on the hands
def retint(m, col, keep=0.55):
    """grey out the asset's own picture and multiply it by a colour (keeps its folds, seams and pockets)"""
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    src = lk.from_socket if lk else None
    bw = nt.nodes.new('ShaderNodeRGBToBW'); mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - keep; mr.inputs['To Max'].default_value = 1.0 + keep * 0.3
    if src: nt.links.new(src, bw.inputs['Color']); nt.links.new(bw.outputs['Val'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mul.inputs['A'])
    mul.inputs['B'].default_value = (*col, 1); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85; b.inputs['Sheen Weight'].default_value = 0.35; b.inputs['Sheen Tint'].default_value = (*col, 1)
    return m
retint(SUIT.data.materials[0], (0.16, 0.17, 0.115))
retint(BOOTS.data.materials[0], (0.025, 0.022, 0.02), 0.3)
GLOVE = noisy(mat('glove', (0.045, 0.045, 0.04), 0.62), 220.0, 0.25, 0.12); N(GLOVE)['Principled BSDF'].inputs['Sheen Weight'].default_value = 0.4
BODY.data.materials.append(GLOVE); _gi = len(BODY.data.materials) - 1
_vg = {g.index: g.name for g in BODY.vertex_groups}
_hand = set()
for v in BODY.data.vertices:
    w = sum(g.weight for g in v.groups if _vg[g.group].startswith(('wrist', 'finger', 'metacarpal', 'lowerarm02')))
    if w > 0.35: _hand.add(v.index)
SLEEVE = noisy(mat('sleeve', (0.16, 0.17, 0.115), 0.85), 260.0, 0.2, 0.05); N(SLEEVE)['Principled BSDF'].inputs['Sheen Weight'].default_value = 0.35
HOOD = noisy(mat('hood', (0.03, 0.032, 0.028), 0.85), 300.0, 0.2, 0.05)
BODY.data.materials.append(SLEEVE); _si = len(BODY.data.materials) - 1; BODY.data.materials.append(HOOD); _hi = len(BODY.data.materials) - 1
_arm, _headv = set(), set()
for v in BODY.data.vertices:
    names = {_vg[g.group]: g.weight for g in v.groups}
    if sum(w for n, w in names.items() if n.startswith(('lowerarm01', 'upperarm', 'shoulder'))) > 0.3: _arm.add(v.index)
    if sum(w for n, w in names.items() if not n.startswith(('spine', 'clavicle', 'shoulder', 'upperarm', 'lowerarm', 'wrist', 'finger', 'metacarpal', 'pelvis', 'upperleg', 'lowerleg', 'foot', 'toe', 'breast', 'root', 'body', 'Left', 'Right', 'Mid', 'helper', 'Joint'))) > 0.3: _headv.add(v.index)
for p_ in BODY.data.polygons:
    if sum(1 for vi in p_.vertices if vi in _hand) >= 3: p_.material_index = _gi
    elif sum(1 for vi in p_.vertices if vi in _arm) >= 3: p_.material_index = _si
    elif sum(1 for vi in p_.vertices if vi in _headv) >= 3: p_.material_index = _hi
# ---- gear helpers: build in rig rest space, ride a bone
def ride(o, bone):
    if o.type == 'MESH': o.data.transform(o.matrix_basis.copy())
    bm_ = RIG.data.bones[bone]; o.parent = RIG; o.parent_type = 'BONE'; o.parent_bone = bone
    o.matrix_parent_inverse = (bm_.matrix_local @ Matrix.Translation((0, bm_.length, 0))).inverted(); o.matrix_basis = Matrix.Identity(4); return o
HELM_M = noisy(mat('helmet', (0.075, 0.08, 0.07), 0.32, coat=0.5), 30.0, 0.12, 0.08)
VISOR_M = mat('visor', (0.012, 0.012, 0.014), 0.16, coat=1.0); N(VISOR_M)['Principled BSDF'].inputs['Coat Roughness'].default_value = 0.02
N(VISOR_M)['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.9
MASK_M = noisy(mat('mask', (0.075, 0.08, 0.07), 0.55), 150.0, 0.2)
RUB = noisy(mat('rubber', (0.012, 0.012, 0.013), 0.55), 90.0, 0.2)
GSUIT_M = noisy(mat('gsuit', (0.3, 0.26, 0.15), 0.8), 400.0, 0.18, 0.05); N(GSUIT_M)['Principled BSDF'].inputs['Sheen Weight'].default_value = 0.4
STRAP_M = noisy(mat('strap', (0.06, 0.065, 0.045), 0.8), 600.0, 0.25)
HC = Vector((0.0, -0.058, 1.555))           # helmet centre (rig rest space): middle of the head
def shell(name, rx, ry, rz, cz_off, m, open_fn=None, nu=64, nv=40, zmin=-0.75):
    """an egg-shaped shell around HC; open_fn(theta, phi) True leaves a face out (the face opening)"""
    vs, fs = [], []
    for j in range(nv):
        ph = lerp(zmin, 1.0, j / (nv - 1)) * math.pi / 2       # -..+90 deg (bottom..top)
        for i in range(nu):
            th = 2 * math.pi * i / nu                          # 0 = front (-Y)
            cy, sy = math.cos(ph), math.sin(ph)
            back = 1.0 + 0.12 * max(0.0, math.cos(th + math.pi)) # a little longer at the back
            vs.append(HC + Vector((rx * cy * math.sin(th), -ry * cy * math.cos(th) * (back if math.cos(th) < 0 else 1.0), rz * sy + cz_off)))
    for j in range(nv - 1):
        for i in range(nu):
            i2 = (i + 1) % nu; th = 2 * math.pi * (i + 0.5) / nu; ph = lerp(zmin, 1.0, (j + 0.5) / (nv - 1)) * math.pi / 2
            if open_fn and open_fn(th, ph): continue
            fs.append((j * nu + i, j * nu + i2, (j + 1) * nu + i2, (j + 1) * nu + i))
    return mesh(name, vs, fs, m)
def face_open(th, ph):
    d = math.degrees(math.atan2(math.sin(th), math.cos(th))); return abs(d) < 58 and -48 < math.degrees(ph) < 28
HELMET = shell('helmet', 0.128, 0.142, 0.15, 0.0, HELM_M, face_open, zmin=-0.62)
sol = HELMET.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.012; subsurf(HELMET, 1)
# visor: a dark curved sheet over the face opening, from the brow down past the nose; visor housing ridge on top
VISOR = shell('visor', 0.137, 0.152, 0.155, 0.0, VISOR_M, lambda th, ph: not (abs(math.degrees(math.atan2(math.sin(th), math.cos(th)))) < 70 and -34 < math.degrees(ph) < 32), zmin=-0.62)
VISOR.modifiers.new('sol', 'SOLIDIFY').thickness = 0.004; subsurf(VISOR, 1)
HOUSING = shell('visor_housing', 0.142, 0.158, 0.162, 0.0, HELM_M, lambda th, ph: not (abs(math.degrees(math.atan2(math.sin(th), math.cos(th)))) < 75 and 30 < math.degrees(ph) < 52), zmin=-0.62)
HOUSING.modifiers.new('sol', 'SOLIDIFY').thickness = 0.01; subsurf(HOUSING, 1)
# oxygen mask: a rounded cup over nose and mouth, with a valve and side straps
MASK = shell('mask', 0.062, 0.036, 0.07, 0.0, MASK_M, lambda th, ph: math.cos(th) < 0.1, nu=48, nv=24, zmin=-1.0)
for v in MASK.data.vertices:          # narrower toward the nose bridge, wider at the chin
    rel = v.co - HC; k = clamp((rel.z + 0.068) / 0.136, 0, 1); rel.x *= lerp(1.15, 0.5, k ** 1.4); rel.y *= lerp(1.0, 0.75, k); v.co = HC + rel + Vector((0, -0.118, -0.06))
MASK.modifiers.new('sol', 'SOLIDIFY').thickness = 0.008; subsurf(MASK, 1)
VALVE = prim('cylinder', 'valve', RUB, None, loc=HC + Vector((0, -0.15, -0.112)), rot=(R(35), 0, 0), vertices=24, radius=0.022, depth=0.04)
MSTRAPS = [tube('mask_strap' + s_, [HC + Vector((sg * 0.055, -0.15, -0.04)), HC + Vector((sg * 0.105, -0.11, -0.01)), HC + Vector((sg * 0.135, -0.05, 0.0))], 0.007, RUB, None, seg=8) for s_, sg in (('L', 1), ('R', -1))]
EARS = [prim('uv_sphere', 'earcup' + s_, HELM_M, None, loc=HC + Vector((sg * 0.128, -0.0, -0.035)), segments=24, ring_count=12, scale=(0.022, 0.05, 0.06)) for s_, sg in (('L', 1), ('R', -1))]
GEAR_HEAD = [HELMET, VISOR, HOUSING, MASK, VALVE] + MSTRAPS + EARS
for o in GEAR_HEAD: ride(o, 'head')
# ---- G-suit and harness: bands of the suit's own surface, lifted off it (so they bend with him exactly)
def suit_band(name, keep, m, lift, thick):
    me = SUIT.data.copy(); o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.parent = SUIT.parent; o.matrix_world = SUIT.matrix_world.copy()
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    dele = [f for f in bm.faces if not keep(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=dele, context='FACES'); bm.to_mesh(me); bm.free()
    for g in SUIT.vertex_groups: o.vertex_groups.new(name=g.name)
    o.data.materials.clear(); o.data.materials.append(m)
    am = o.modifiers.new('arm', 'ARMATURE'); am.object = RIG; am.use_deform_preserve_volume = True
    so = o.modifiers.new('sol', 'SOLIDIFY'); so.thickness = thick; so.offset = 1.0
    dp = o.modifiers.new('lift', 'DISPLACE'); dp.strength = lift; dp.mid_level = 0.0
    subsurf(o, 1); return o
def gsuit_keep(c):
    thigh = 0.52 < c.z < 0.86 and abs(c.x) > 0.035
    calf = 0.13 < c.z < 0.42
    belly = 0.93 < c.z < 1.1 and c.y < -0.02
    return thigh or calf or belly
GSUIT = suit_band('gsuit', gsuit_keep, GSUIT_M, 0.006, 0.01)
GS_TEX = bpy.data.textures.new('bladder', 'CLOUDS'); GS_TEX.noise_scale = 0.06
GSUIT.modifiers['lift'].texture = GS_TEX; GSUIT.modifiers['lift'].texture_coords = 'LOCAL'
def strap_keep(c):
    vert = any(abs(c.x - sx) < 0.022 for sx in (0.085, -0.085)) and 0.95 < c.z < 1.46
    chest = abs(c.z - 1.24) < 0.018 and c.y < 0.0
    waist = abs(c.z - 0.99) < 0.025
    legs = any(abs(c.x - sx) < 0.02 for sx in (0.12, -0.12)) and 0.78 < c.z < 0.95 and c.y < 0.05
    return vert or chest or waist or legs
HARNESS = suit_band('harness', strap_keep, STRAP_M, 0.012, 0.006)
BUCKLES = [prim('cube', 'buckle', METAL, None, loc=Vector((sx, -0.135, 1.24)), size=1, scale=(0.04, 0.012, 0.03)) for sx in (0.085, -0.085)]
for o in BUCKLES: ride(o, 'spine01')
# hose: from the mask valve down to a connector on his chest (rebuilt each frame from where those bones are)
HOSE_M = noisy(mat('hose', (0.045, 0.048, 0.04), 0.65), 80.0, 0.2)
HOSE = None
def hose_update():
    global HOSE
    hb = RIG.pose.bones['head']; cb = RIG.pose.bones['spine01']; mw = RIG.matrix_world
    def at(pb, v): b_ = RIG.data.bones[pb.name]; return mw @ (pb.matrix @ b_.matrix_local.inverted() @ Vector(v))
    p0 = at(hb, HC + Vector((0, -0.158, -0.13))); p3 = at(cb, Vector((0.07, -0.14, 1.2)))
    p1 = p0 + (mw.to_3x3() @ Vector((0.0, -0.07, -0.08))); p2 = p3 + (mw.to_3x3() @ Vector((0.02, -0.08, 0.1)))
    pts = [((1 - s) ** 3) * p0 + 3 * ((1 - s) ** 2) * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3 * p3 for s in [k / 15 for k in range(16)]]
    if HOSE: bpy.data.meshes.remove(HOSE.data)
    HOSE = tube('hose', pts, 0.016, HOSE_M, seg=12); return HOSE
PILOT = [BODY, SUIT, BOOTS, GSUIT, HARNESS] + GEAR_HEAD + BUCKLES
# ---- posing: legs and arms by IK to targets in the cockpit, spine/neck/head by hand
def ik(bone, target, pole, chain=4, pole_angle=0.0):
    c = RIG.pose.bones[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TGT = {k: empty('tgt_' + k, COCKPIT) for k in ('handR', 'handL', 'footR', 'footL', 'poleArmR', 'poleArmL', 'poleLegR', 'poleLegL')}
IK_HR = ik('wrist.R', TGT['handR'], TGT['poleArmR'], 5, R(-90)); IK_HL = ik('wrist.L', TGT['handL'], TGT['poleArmL'], 5, R(-90))
IK_FR = ik('foot.R', TGT['footR'], TGT['poleLegR'], 5, R(-90)); IK_FL = ik('foot.L', TGT['footL'], TGT['poleLegL'], 5, R(-90))
def set_pose(head_pitch=0.0, head_roll=0.0, head_yaw=0.0, neck=0.0, spine=0.0, strain=0.0, hand_r=None, hand_l=None, curl=0.9, t=0.0):
    """angles in degrees; strain = shoulders up and a tremble; hand_r/hand_l = cockpit-space points for the IK targets (None = on the grips)"""
    tr = strain * 0.6
    for n, ang in (('spine03', spine * 0.3), ('spine02', spine * 0.3), ('spine01', spine * 0.4)):
        pb = RIG.pose.bones[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(ang + tr * wob(t, 11, 1)), 0, 0)
    for n, k in (('neck01', 0.35), ('neck02', 0.35), ('neck03', 0.3)):
        pb = RIG.pose.bones[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(neck * k + tr * wob(t, 13, 2)), R(head_yaw * k * 0.5), R(head_roll * k * 0.5))
    pb = RIG.pose.bones['head']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(head_pitch + 1.5 * tr * wob(t, 15, 3)), R(head_yaw * 0.5), R(head_roll * 0.5))
    for s_ in ('L', 'R'):
        pb = RIG.pose.bones['clavicle.' + s_]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, R((6 if s_ == 'L' else -6) * strain))
    TGT['handR'].location = Vector(hand_r) if hand_r is not None else STICK.location + Vector((-0.02, 0.0, 0.16))
    TGT['handL'].location = Vector(hand_l) if hand_l is not None else THR.location + Vector((-0.03, 0.0, 0.1))
    TGT['poleArmR'].location = Vector((2.55, -0.75, 0.0)); TGT['poleArmL'].location = Vector((2.55, 0.75, 0.0))
    TGT['footR'].location = PEDALS[1].location + Vector((-0.06, 0.0, 0.0)); TGT['footL'].location = PEDALS[0].location + Vector((-0.06, 0.0, 0.0))
    TGT['poleLegR'].location = Vector((3.4, -0.25, 0.6)); TGT['poleLegL'].location = Vector((3.4, 0.25, 0.6))
    for s_ in ('L', 'R'):                        # fingers curled round the grips
        for f_ in range(1, 6):
            for seg in (1, 2, 3):
                nm = f'finger{f_}-{seg}.{s_}'
                if nm in RIG.pose.bones:
                    pb = RIG.pose.bones[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(curl * (35 if f_ > 1 else 15)), 0, 0)
    bpy.context.view_layer.update(); hose_update()
set_pose()

# ================================================================ X-RAY: his body see-through, blood vessels, heart and brain
def xray_body_mat():
    """glassy blue body; 'pool' (object property) turns the low parts (legs) red as blood pools there"""
    m = bpy.data.materials.new('xbody'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.42
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    low = nt.nodes.new('ShaderNodeMapRange'); low.inputs['From Min'].default_value = 0.95; low.inputs['From Max'].default_value = 0.55; nt.links.new(sx.outputs['Z'], low.inputs['Value'])
    pool = nt.nodes.new('ShaderNodeAttribute'); pool.attribute_type = 'OBJECT'; pool.attribute_name = 'pool'
    pm = nt.nodes.new('ShaderNodeMath'); pm.operation = 'MULTIPLY'; nt.links.new(low.outputs['Result'], pm.inputs[0]); nt.links.new(pool.outputs['Fac'], pm.inputs[1])
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.25, 0.55, 1.0, 1); col.inputs['B'].default_value = (1.0, 0.12, 0.08, 1)
    nt.links.new(pm.outputs['Value'], col.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(col.outputs['Result'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.6
    fz = nt.nodes.new('ShaderNodeMath'); fz.operation = 'POWER'; fz.inputs[1].default_value = 2.2; nt.links.new(lw.outputs['Facing'], fz.inputs[0])
    fa = nt.nodes.new('ShaderNodeMath'); fa.operation = 'MULTIPLY_ADD'; fa.inputs[1].default_value = 0.85; fa.inputs[2].default_value = 0.04
    nt.links.new(fz.outputs['Value'], fa.inputs[0]); fb = nt.nodes.new('ShaderNodeMath'); fb.operation = 'MULTIPLY_ADD'; fb.inputs[1].default_value = 0.35
    nt.links.new(pm.outputs['Value'], fb.inputs[0]); nt.links.new(fa.outputs['Value'], fb.inputs[2])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fb.outputs['Value'], mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
XBODY = xray_body_mat()
def flow_mat(name, col, dash=40.0):
    """a vessel: a dim tube with bright pulses running along it; 'ph' = how far the pulses have moved, 'glow' = brightness (object properties)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    uv = nt.nodes.new('ShaderNodeUVMap'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv.outputs['UV'], sx.inputs['Vector'])
    ph = nt.nodes.new('ShaderNodeAttribute'); ph.attribute_type = 'OBJECT'; ph.attribute_name = 'ph'
    gl = nt.nodes.new('ShaderNodeAttribute'); gl.attribute_type = 'OBJECT'; gl.attribute_name = 'glow'
    ma = nt.nodes.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = dash; nt.links.new(sx.outputs['X'], ma.inputs[0])
    sb = nt.nodes.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; nt.links.new(ma.outputs['Value'], sb.inputs[0]); nt.links.new(ph.outputs['Fac'], sb.inputs[1])
    sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'; nt.links.new(sb.outputs['Value'], sn.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.2; mr.inputs['From Max'].default_value = 1.0; mr.inputs['To Min'].default_value = 0.35; mr.inputs['To Max'].default_value = 3.0
    nt.links.new(sn.outputs['Value'], mr.inputs['Value'])
    mg = nt.nodes.new('ShaderNodeMath'); mg.operation = 'MULTIPLY'; nt.links.new(mr.outputs['Result'], mg.inputs[0]); nt.links.new(gl.outputs['Fac'], mg.inputs[1])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(mg.outputs['Value'], em.inputs['Strength'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
ART_M = flow_mat('artery', (1.0, 0.08, 0.05)); VEIN_M = flow_mat('vein', (0.25, 0.3, 1.0), 30.0)
def organ_mat(name, c0, c1, prop):
    """glows c0 when full of blood (prop = 1), c1 when starved (prop = 0)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = prop
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*c1, 1); mx.inputs['B'].default_value = (*c0, 1); nt.links.new(at.outputs['Fac'], mx.inputs['Factor'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    st = nt.nodes.new('ShaderNodeMapRange'); st.inputs['To Min'].default_value = 3.0; st.inputs['To Max'].default_value = 0.9; nt.links.new(lw.outputs['Facing'], st.inputs['Value'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mx.outputs['Result'], em.inputs['Color']); nt.links.new(st.outputs['Result'], em.inputs['Strength'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
BRAIN_M = organ_mat('brain', (1.0, 0.35, 0.4), (0.08, 0.12, 0.35), 'ox')
HEART_M = organ_mat('heart', (1.0, 0.1, 0.07), (0.6, 0.05, 0.04), 'ox')
def bumpy(o, scale, amt):
    tx = bpy.data.textures.new(o.name + '_n', 'CLOUDS'); tx.noise_scale = scale; d_ = o.modifiers.new('bump', 'DISPLACE'); d_.texture = tx; d_.strength = amt; d_.texture_coords = 'LOCAL'; return o
BRAIN = prim('uv_sphere', 'brain', BRAIN_M, None, loc=HC + Vector((0, 0.005, 0.03)), segments=64, ring_count=32, scale=(0.068, 0.088, 0.062)); bumpy(BRAIN, 0.012, 0.006); ride(BRAIN, 'head')
HEART = prim('uv_sphere', 'heart', HEART_M, None, loc=Vector((0.025, -0.06, 1.25)), segments=48, ring_count=24, scale=(0.05, 0.045, 0.065)); HEART.rotation_euler = (R(20), R(-25), R(15)); bumpy(HEART, 0.03, 0.006)
ride(HEART, 'spine01')
def bone_for(c):
    """which bone a vessel point in rest space rides"""
    side = 'L' if c.x > 0 else 'R'
    if c.z > 1.5: return 'head'
    if c.z > 1.42: return 'neck02'
    if c.z > 1.15: return 'spine01'
    if c.z > 0.95: return 'spine03'
    if c.z > 0.86: return 'root' if abs(c.x) < 0.06 else 'upperleg01.' + side
    if c.z > 0.5: return 'upperleg02.' + side
    if c.z > 0.12: return 'lowerleg02.' + side
    return 'foot.' + side
def vessel(name, pts, r, m):
    o = tube(name, [Vector(p_) for p_ in pts], r, m, None, seg=10, uvlen=True)
    groups = {}
    for v in o.data.vertices:
        bn = bone_for(v.co)
        if bn not in groups: groups[bn] = o.vertex_groups.new(name=bn)
        groups[bn].add([v.index], 1.0, 'REPLACE')
    o.parent = RIG; o.matrix_parent_inverse = RIG.matrix_world.inverted() @ RIG.matrix_world; o.matrix_world = RIG.matrix_world.copy()
    am = o.modifiers.new('arm', 'ARMATURE'); am.object = RIG
    sw = o.modifiers.new('swell', 'DISPLACE'); sw.strength = 0.0; sw.mid_level = 0.0
    o['ph'] = 0.0; o['glow'] = 1.0; return o
def smooth_pts(ctrl, n=40):
    out_ = []
    for i in range(n):
        u = i / (n - 1) * (len(ctrl) - 1); k = min(int(u), len(ctrl) - 2); f = u - k
        p0 = Vector(ctrl[max(k - 1, 0)]); p1 = Vector(ctrl[k]); p2 = Vector(ctrl[k + 1]); p3 = Vector(ctrl[min(k + 2, len(ctrl) - 1)])
        out_.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return out_
ART_UP = [vessel('carotid' + s_, smooth_pts([(0.02, -0.05, 1.3), (sg * 0.022, -0.045, 1.37), (sg * 0.03, -0.055, 1.44), (sg * 0.032, -0.05, 1.5), (sg * 0.025, -0.04, 1.56)], 30), 0.006, ART_M) for s_, sg in (('L', 1), ('R', -1))]
AORTA = vessel('aorta', smooth_pts([(0.02, -0.05, 1.29), (0.01, -0.04, 1.36), (0.0, 0.0, 1.37), (0.0, 0.035, 1.3), (0.0, 0.04, 1.15), (0.0, 0.035, 1.0), (0.0, 0.02, 0.93)], 40), 0.011, ART_M)
ART_LEG = [vessel('femoral' + s_, smooth_pts([(0.0, 0.02, 0.93), (sg * 0.06, 0.0, 0.9), (sg * 0.1, -0.03, 0.82), (sg * 0.13, -0.03, 0.62), (sg * 0.15, -0.0, 0.47), (sg * 0.16, 0.01, 0.3), (sg * 0.18, 0.0, 0.1)], 46), 0.0075, ART_M) for s_, sg in (('L', 1), ('R', -1))]
VEIN_LEG = [vessel('legvein' + s_, smooth_pts([(sg * 0.2, 0.01, 0.1), (sg * 0.185, 0.02, 0.3), (sg * 0.17, 0.02, 0.47), (sg * 0.15, -0.01, 0.62), (sg * 0.12, -0.01, 0.82), (sg * 0.07, 0.02, 0.9), (0.012, 0.03, 0.94)], 46), 0.0085, VEIN_M) for s_, sg in (('L', 1), ('R', -1))]
VCAVA = vessel('vena_cava', smooth_pts([(0.012, 0.03, 0.94), (0.025, 0.025, 1.1), (0.03, -0.01, 1.22), (0.03, -0.04, 1.26)], 30), 0.012, VEIN_M)
JUG = [vessel('jugular' + s_, smooth_pts([(sg * 0.035, -0.035, 1.55), (sg * 0.045, -0.045, 1.45), (sg * 0.04, -0.04, 1.37), (0.03, -0.045, 1.3)], 30), 0.0065, VEIN_M) for s_, sg in (('L', 1), ('R', -1))]
XRAY = [BRAIN, HEART] + ART_UP + [AORTA] + ART_LEG + VEIN_LEG + [VCAVA] + JUG
for o in XRAY: o.visible_shadow = False
GS_X = noisy(mat('gsuit_x', (0.35, 0.3, 0.12), 0.6, trans=0.0, alpha=0.35), 400.0, 0.1)
def xray_mode(on):
    """swap the pilot to see-through and show the inside; returns nothing"""
    BODY.material_slots[0].material  # (slots are swapped below)
    for o in XRAY: o.hide_render = not on
    for o in (SUIT, BOOTS, HARNESS) + tuple(GEAR_HEAD) + tuple(BUCKLES): o.hide_render = on
    if HOSE: HOSE.hide_render = on
    for i, sl in enumerate(BODY.material_slots): sl.material = XBODY if on else BODY_MATS[i]
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = not on
    GSUIT.material_slots[0].material = GS_X if on else GSUIT_M
BODY_MATS = [sl.material for sl in BODY.material_slots]
for o in XRAY: o.hide_render = True
BODY['pool'] = 0.0; BRAIN['ox'] = 1.0; HEART['ox'] = 1.0

# ================================================================ FLIGHT: where the jet is and how hard it's pulling, story time
V = 200.0                                   # m/s, about 450 mph
def g_turn(tau):
    """G in the turn: wings level at 1 G, yanked to 9 G (tau -1.2 .. 1.0), held at 9 with a little jitter"""
    g = 1.0 + 8.0 * smooth(-1.2, 1.0, tau)
    return g + (0.12 * wob(tau, 1.3, 4.0) if tau > 1.0 else 0.0)
def bank_turn(tau):
    return math.acos(1.0 / max(1.0, g_turn(tau) - 0.0)) * smooth(-1.6, 0.4, tau) + math.acos(1 / 9.0) * 0.0
def turn_state(tau):
    """position, (roll, pitch, yaw) and G for the level left turn; integrated from tau = -4 so it's the same every time"""
    x, y, psi = -1400.0, -500.0, R(20); dt = 1 / 120.0; tt = -4.0
    while tt < tau - 1e-9:
        h = min(dt, tau - tt); phi = bank_turn(tt + h / 2)
        psi += 9.81 * math.tan(phi) / V * h; x += V * math.cos(psi) * h; y += V * math.sin(psi) * h; tt += h
    g = g_turn(tau); phi = bank_turn(tau); aoa = R(1.5 + 1.2 * (g - 1))
    return Vector((x, y, 3000.0)), (-phi, -aoa, psi), g
def dive_state(td):
    """after he passes out (td = t - B[8]): the jet rolls past vertical and the nose falls toward the ground (exterior from ~1.2 s)"""
    p0 = Vector((2600.0, 900.0, 1150.0)); psi = R(200)
    roll = -R(110) - R(25) * smooth(0, 2.7, td); pitch = R(25 + 30 * smooth(0, 2.7, td))       # +pitch here = nose down
    d = Vector((math.cos(psi) * math.cos(pitch), math.sin(psi) * math.cos(pitch), -math.sin(pitch)))
    p = p0 + Vector((math.cos(psi), math.sin(psi), 0)) * V * td + Vector((0, 0, -1)) * (90 * td + 70 * td * td)
    return p, (roll, pitch, psi), 1.0 + 0.4 * (1 - smooth(0, 1.2, td))
def pull_state(tp):
    """Auto-GCAS (tp = t - B[9]): low over the ground, rolls wings level, then a 5 G pull up and away"""
    psi = R(200); ground_ = Vector((800.0, -600.0, 0.0)); gz = ground_h(ground_.x, ground_.y)
    roll = -R(135) * (1 - smooth(0.15, 1.05, tp))
    g = 1.0 + 4.0 * smooth(0.9, 1.25, tp) - 3.6 * smooth(4.6, 5.6, tp)
    pitch = R(42) - R(62) * smooth(1.0, 3.2, tp) - R(10) * smooth(3.2, 6.5, tp)           # +pitch = nose down; ends 30 deg nose up
    # altitude: descending, bottoming ~110 m above the ground around tp 2.4, then climbing
    alt = 110 + 220 * (1 - tp / 2.4) ** 2 if tp < 2.4 else 110 + 75 * (tp - 2.4) ** 2
    along = V * 1.12 * tp
    p = ground_ + Vector((math.cos(psi), math.sin(psi), 0)) * along + Vector((0, 0, gz + alt))
    return p, (roll, pitch, psi), g
def place_jet(state):
    p, (roll, pitch, yaw), g = state
    JET.location = p; JET.rotation_mode = 'QUATERNION'
    q = Quaternion((0, 0, 1), yaw) @ Quaternion((0, 1, 0), pitch) @ Quaternion((1, 0, 0), roll)
    JET.rotation_quaternion = q; bpy.context.view_layer.update(); return g
def jet_local(v): return JET.matrix_world @ Vector(v)

# ---------------------------------------------------------------- HUD: green symbology drawn per frame (G, speed, altitude, pitch ladder turned with the bank)
from PIL import Image as _Im, ImageDraw as _Dr, ImageFont as _Fn
import numpy as _np
_HF = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
def _font(sz):
    try: return _Fn.truetype(_HF, sz)
    except Exception: return _Fn.load_default()
def hud_draw(g, kts, alt_ft, roll, pitch, chev=0.0):
    W_, H_ = 512, 512; im = _Im.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = _Dr.Draw(im); col = (255, 255, 255, 255); f = _font(26); fs = _font(20)
    cx, cy = W_ / 2, H_ / 2 + 10
    # pitch ladder: lines every 10 deg, turned by the bank
    ca, sa = math.cos(-roll), math.sin(-roll)
    for k in range(-9, 10):
        ang = k * 10 - math.degrees(-pitch) * 0 ; off = (k * 10 + math.degrees(pitch)) * 6.0
        if abs(off) > 300: continue
        for sgn in (-1, 1):
            x0, x1 = sgn * 40, sgn * 120
            pts = [(cx + (x * ca - off * sa), cy + (x * sa + off * ca)) for x in (x0, x1)]
            d.line(pts, fill=col, width=3 if k else 4)
    # flight path marker
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=col, width=3); d.line([(cx - 30, cy), (cx - 12, cy)], fill=col, width=3); d.line([(cx + 12, cy), (cx + 30, cy)], fill=col, width=3); d.line([(cx, cy - 12), (cx, cy - 26)], fill=col, width=3)
    # G at the top left, speed box left, altitude box right
    d.text((40, 40), f'{g:3.1f}', font=f, fill=col); d.text((40, 70), 'G', font=fs, fill=col)
    d.rectangle([20, 230, 120, 270], outline=col, width=3); d.text((30, 236), f'{int(kts):4d}', font=f, fill=col)
    d.rectangle([380, 230, 500, 270], outline=col, width=3); d.text((388, 236), f'{int(alt_ft):5d}', font=f, fill=col)
    # heading tape
    for k in range(-3, 4): d.line([(cx + k * 40, 22), (cx + k * 40, 36)], fill=col, width=3)
    if chev > 0:                             # recovery chevrons closing in (the ground warning)
        gap = 120 * (1 - chev) + 20
        for sgn in (-1, 1):
            d.line([(cx + sgn * gap, cy + 80), (cx + sgn * (gap + 40), cy + 50)], fill=col, width=5); d.line([(cx + sgn * gap, cy + 80), (cx + sgn * (gap - 40) * 0 + sgn * (gap + 40), cy + 110)], fill=col, width=5)
    a_ = _np.asarray(im, dtype=_np.float32)[::-1] / 255.0
    HUD_IMG.pixels.foreach_set(a_.ravel()); HUD_IMG.update()

# ---------------------------------------------------------------- camera
def look(cp, ct, lens=35, fstop=8.0, focus=None, roll=0.0, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    q = d.to_track_quat('-Z', 'Y')
    if up is not None:                       # roll the camera so its 'up' follows a given vector (shots that ride with the jet)
        z = -d.normalized(); u = Vector(up); x = u.cross(z).normalized(); y = z.cross(x)
        q = Matrix((x, y, z)).transposed().to_quaternion()
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0): return Vector((wob(t, 9.0, seed), wob(t, 9.0, seed + 3.3), wob(t, 9.0, seed + 6.1))) * amt

# ================================================================ the story, frame by frame
EXT = [GROUND] + CLOUDS + NEAR
JETBITS = [o for o in S.objects if o.parent in (JET, COCKPIT, SEAT, STICK, THR) and o not in PILOT and o.type == 'MESH']
def visible(objs, on):
    for o in objs: o.hide_render = not on
def world_mode(xray):
    WMIX.inputs['Fac'].default_value = 1.0 if xray else 0.0; SUN.hide_render = xray
def near_puffs(t, state):
    """a few puffs scattered just outside the turn circle, facing the camera, so the speed reads"""
    p, (roll, pitch, yaw), g = state
    for k, o in enumerate(NEAR):
        ang = yaw + 0.6 + 0.9 * k + 0.2 * h1(k); rr = 520 + 260 * h1(k * 3)
        o.location = p + Vector((math.cos(ang), math.sin(ang), 0)) * rr + Vector((0, 0, -60 - 140 * h1(k * 5)))
        d = (CAM.location - o.location); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')
def vapor(amount, t):
    for o in VAPS + TRAILS: o['vap'] = amount
    VAP_MAP.inputs['Location'].default_value = (t * 9.0, 0, 0); TRAIL_MAP.inputs['Location'].default_value = (t * 14.0, t * 0.7, 0)
def hud_for(t, state, chev=0.0):
    p, (roll, pitch, yaw), g = state
    hud_draw(g, 450 + 20 * wob(t, 0.3), (p.z - ground_h(p.x, p.y)) * 3.281, roll, pitch, chev)
def gsuit_inflate(k):
    GSUIT.modifiers['lift'].strength = 0.006 + 0.04 * k; GSUIT.modifiers['sol'].thickness = 0.01 + 0.012 * k
def breath(t, times, w=0.22):
    """0..1 pulses at the given times (sharp in, quick out)"""
    return max((math.exp(-((t - tb) / w) ** 2) for tb in times), default=0.0)
def g_story(t):
    """the G he feels (HUD, readout, vapor): the yank to 9, held; it falls away when his hand comes off the stick; 5 in the auto pull-up"""
    nb = beat_at(t); lt = t - B[nb]
    if nb == 11: return g_turn(t - TOTAL)
    if nb <= 7: return g_turn(t)
    if nb == 8: return lerp(g_turn(B[8]), 1.25, smooth(0.3, 1.1, lt))
    if nb == 9: return pull_state(lt)[2]
    return pull_state(DUR[9] + lt)[2]
# ---------------------------------------------------------------- how he holds himself, story time
def pilot_pose(t):
    nb = beat_at(t); lt = t - B[nb]; u = lt / DUR[nb]
    G = 9.0
    if nb == 11: G = g_turn(t - TOTAL)
    elif nb == 0: G = g_turn(t)
    press = clamp((G - 1.5) / 7.5, 0, 1)                               # how hard 9 G pushes him down
    kw = dict(head_pitch=14 * press, neck=10 * press, spine=5 * press, strain=0.5 * press, t=t)
    if nb in (1, 2, 3, 4): kw.update(head_pitch=16, neck=12, spine=6, strain=0.6)
    if nb == 5:                                                        # the straining move: tensed, shoulders up, a sharp breath
        b_ = breath(lt, (0.45, 2.75)); kw.update(head_pitch=10 - 8 * b_, neck=8 - 6 * b_, spine=3 - 6 * b_, strain=1.0)
    if nb == 6: kw.update(head_pitch=16, neck=12, spine=6, strain=0.3)
    if nb == 7:                                                        # out cold: head drops forward and over, body slumps
        k = smooth(0.42, 0.75, u); kw.update(head_pitch=lerp(16, 48, k), neck=lerp(12, 30, k), head_roll=lerp(0, 22, k), spine=lerp(6, 16, k), strain=0.3 * (1 - k))
    if nb == 8:
        kw.update(head_pitch=48, neck=30, head_roll=22, spine=16, strain=0.0)
        k = smooth(0.12, 0.42, u)                                       # his hand slides off the stick and drops to his thigh
        grip = STICK.location + Vector((-0.02, 0.0, 0.16)); lap = Vector((2.92, -0.2, -0.06))
        kw.update(hand_r=grip.lerp(lap, k) + Vector((0, 0, 0.03 * math.sin(math.pi * k))), curl=lerp(0.9, 0.25, k))
    if nb == 9:
        kw.update(head_pitch=48, neck=30, head_roll=22 - 10 * smooth(0.3, 1.0, u), spine=16, hand_r=Vector((2.92, -0.2, -0.06)), curl=0.25)
    if nb == 10:                                                       # he comes to: jerks, lifts his head, looks around, grabs the stick
        k = smooth(0.0, 0.35, u); jerk = (0.7 * math.sin(lt * 31) * math.exp(-lt * 2.2)) * (1 - smooth(0.25, 0.4, u))
        kw.update(head_pitch=lerp(48, 6, k) + 8 * jerk, neck=lerp(30, 6, k), head_roll=lerp(12, 0, k) + 6 * jerk, head_yaw=-18 * math.sin(math.pi * smooth(0.18, 0.45, u)),
                  spine=lerp(16, 3, k), strain=0.0)
        kr = smooth(0.3, 0.45, u); kw.update(hand_r=Vector((2.92, -0.2, -0.06)).lerp(STICK.location + Vector((-0.02, 0.0, 0.16)), kr), curl=lerp(0.3, 0.9, kr))
    set_pose(**kw)
    if nb == 4: gsuit_inflate(smooth(0.05, 0.35, u))
    elif 5 <= nb <= 7: gsuit_inflate(1.0)
    elif nb == 8: gsuit_inflate(1.0 - smooth(0.3, 0.6, u))
    else: gsuit_inflate(0.15 * press)
# ---------------------------------------------------------------- shots
def jup(): return JET.matrix_world.to_3x3() @ Vector((0, 0, 1))
def head_world(v=(0, 0, 0)):
    pb = RIG.pose.bones['head']; b_ = RIG.data.bones['head']; return RIG.matrix_world @ (pb.matrix @ b_.matrix_local.inverted() @ (HC + Vector(v)))
def cockpit_shot(t, kind, u):
    sh = shake(t, 0.004 + 0.006 * (kind in ('press', 'strain')), 7.0)
    if kind == 'press':        # from the instrument panel, looking back at him, a little below
        look(jet_local(Vector((3.92, -0.12, 0.42)) + sh), head_world((0, 0, -0.08)), 26 + 4 * u, 2.4, up=jup())
    elif kind == 'neck':       # side, close: helmet and neck carrying the load
        look(jet_local(Vector((2.95, -0.38, 0.5)) + sh), head_world((0, 0.03, -0.12)), 24, 2.4, up=jup())
    elif kind == 'strain':
        look(jet_local(Vector((3.95, 0.1, 0.38)) + sh), head_world((0, 0, -0.2)), 22, 2.6, up=jup())
    elif kind == 'out':
        look(jet_local(Vector((3.92, -0.12, 0.4)) + sh), head_world((0, 0, -0.12)), 26, 2.4, up=jup())
    elif kind == 'hand':       # right side, close on the stick and his glove
        look(jet_local(Vector((3.32, -0.28, 0.42)) + sh), jet_local(STICK.location + Vector((-0.06, 0.02, 0.06))), 28, 2.4, up=jup())
    elif kind == 'wake':
        look(jet_local(Vector((3.92, 0.06, 0.42)) + sh), head_world((0, 0, -0.1)), 24, 2.4, up=jup())
    elif kind == 'shoulder':   # behind his right shoulder, through the HUD and canopy (the ground rushing up)
        look(jet_local(Vector((2.12, -0.44, 0.92)) + sh), jet_local(Vector((5.6, 0.18, 0.62))), 20, 6.0, up=jup(), focus=jet_local(Vector((2.6, 0, 0.6))))
def pov_shot(t):
    """his eyes: just in front of where his eyes are, looking along the jet through the HUD"""
    e = jet_local(Vector((3.32, 0.0, 0.56))); look(e + shake(t, 0.003, 9.0), jet_local(Vector((9.0, 0.0, 0.5))), 20, 16.0, up=jup(), focus=jet_local(Vector((4.0, 0, 0.47))))
def xray_shot(t, kind, u):
    sh = shake(t, 0.002, 5.0)
    if kind == 'body':         # the whole man from his right, the seat and jet gone: blood running down into his legs
        look(jet_local(Vector((3.25, -1.55, 0.3)) + sh), jet_local(Vector((2.95, 0.0, 0.08))), 32, 8.0, up=jup())
    elif kind == 'heart':      # heart, neck and head
        look(jet_local(Vector((2.95, -0.85, 0.62)) + sh), jet_local(Vector((2.62, 0.0, 0.42))), 34, 8.0, up=jup())
    elif kind == 'legs':
        look(jet_local(Vector((3.75, -1.1, 0.25)) + sh), jet_local(Vector((3.2, 0.0, -0.18))), 28, 8.0, up=jup())
def flow(t, up_rate, leg_rate, pool, ox, glow_up=1.0):
    """pulse positions along the vessels; up_rate < 0 = blood falling back down the neck"""
    for o in ART_UP: o['ph'] = up_rate * t * 6.0; o['glow'] = glow_up
    AORTA['ph'] = 6.0 * t; AORTA['glow'] = 1.0
    for o in ART_LEG: o['ph'] = leg_rate * t * 6.0; o['glow'] = 1.0 + 0.8 * pool
    for o in VEIN_LEG: o['ph'] = (1.0 - 0.8 * pool) * t * 4.0; o['glow'] = 1.0 + 1.2 * pool; o.modifiers['swell'].strength = 0.006 * pool
    VCAVA['ph'] = (1.0 - 0.7 * pool) * t * 4.0
    for o in JUG: o['ph'] = t * 4.0; o['glow'] = 0.4 + 0.6 * ox
    BODY['pool'] = pool; BRAIN['ox'] = ox; HEART['ox'] = 1.0
    hb = 1.0 + 0.09 * max(0.0, math.sin(t * 2 * math.pi * 2.6)) ** 4     # the heart pounding (about 155 a minute)
    HEART.scale = (hb, hb, hb)
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    world_mode(False); visible(EXT, True); visible(JETBITS, True); xray_mode(False)
    for o in GEAR_HEAD + [BODY]: o.hide_render = False
    # where the jet is
    if nb == 8 and lt > 1.15: st = dive_state(lt)
    elif nb == 8: st = turn_state(B[8])
    elif nb == 9: st = pull_state(lt)
    elif nb == 10: st = pull_state(DUR[9] + lt)
    elif nb == 11: st = turn_state(t - TOTAL)
    else: st = turn_state(t)
    place_jet(st); g = g_story(t); st = (st[0], st[1], g); pilot_pose(t)
    vapor(clamp((g - 3.5) / 4.0, 0, 1), t); hud_for(t, st, chev=smooth(0.0, 0.9, lt) if nb == 9 else 0.0)
    if nb in (0, 11) and not (nb == 0 and lt > 2.4):     # the yank: chase camera, one continuous shot across the loop seam
        tau = t if nb == 0 else t - TOTAL; k = smooth(-2.7, 2.4, tau)
        cp = jet_local(Vector((-16 + 3 * k, -7.5 + 2.0 * k, 4.0 + 0.5 * k)) + shake(t, 0.06 + 0.12 * smooth(-1, 1, tau)))
        look(cp, jet_local(Vector((1.0, 0, 0.0))), 28 + 4 * k, 9.0, up=(jup() * 0.55 + Vector((0, 0, 1)) * 0.45).normalized())
        near_puffs(t, st)
    elif nb == 0: cockpit_shot(t, 'press', (lt - 2.4) / (du - 2.4))
    elif nb == 1: cockpit_shot(t, 'neck', u)
    elif nb in (2, 3) or (nb == 4 and u > 0.45):          # x-ray
        world_mode(True); visible(EXT, False); visible(JETBITS, False); xray_mode(True)
        if nb == 2:
            pool = smooth(0.1, 0.9, u); flow(t, 1.0 - 1.6 * pool, 1.0 + pool, pool, 1.0 - 0.6 * pool); xray_shot(t, 'body', u)
        elif nb == 3:
            flow(t, -0.6 + 0.4 * math.sin(t * 5), 1.8, 1.0, 0.4 - 0.25 * u, glow_up=0.6); xray_shot(t, 'heart', u)
        else:
            k = smooth(0.5, 0.95, u); flow(t, -0.4 + 1.6 * k, 1.8 - 2.6 * k, 1.0 - 0.75 * k, 0.15 + 0.6 * k); xray_shot(t, 'legs', u)
    elif nb == 4:                                           # the real G-suit puffing up on his legs
        look(jet_local(Vector((3.62, -0.34, 0.12)) + shake(t, 0.004)), jet_local(Vector((2.85, 0.02, -0.16))), 22, 3.5, up=jup())
    elif nb == 5: cockpit_shot(t, 'strain', u)
    elif nb == 6 or (nb == 7 and u < 0.45):                # his view: gray, tunnel, black (done in finishing; here: the HUD view)
        for o in GEAR_HEAD + [BODY]: o.hide_render = True
        if HOSE: HOSE.hide_render = True
        pov_shot(t)
    elif nb == 7: cockpit_shot(t, 'out', u)
    elif nb == 8 and lt <= 1.15: cockpit_shot(t, 'hand', u)
    elif nb == 8:                                           # the dive: camera rides above and behind, ground filling the frame
        look(jet_local(Vector((-20, 6, 7)) + shake(t, 0.08)), jet_local(Vector((2, 0, 0))), 30, 9.0, up=Vector((0, 0, 1)))
    elif nb == 9 and lt < 1.05: cockpit_shot(t, 'shoulder', u)
    elif nb == 9:                                           # the pull-up, from low by the ground
        p = st[0]; bot = pull_state(2.4)[0]; side_ = Vector((math.cos(R(290)), math.sin(R(290)), 0))
        gp = bot + side_ * 22 + Vector((math.cos(R(200)), math.sin(R(200)), 0)) * 30; gp.z = max(ground_h(gp.x, gp.y) + 4, bot.z - 18)
        look(gp + shake(t, 0.15 + 0.3 * smooth(1.8, 2.5, lt)), p + Vector((0, 0, 1)), lerp(55, 20, smooth(1.1, 2.35, lt)), 11.0, up=Vector((0, 0, 1)))
    elif nb == 10 and lt <= 1.8: cockpit_shot(t, 'wake', u)
    elif nb == 10:                                          # climbing away
        look(jet_local(Vector((-24, -10, -3)) + shake(t, 0.05)), jet_local(Vector((1, 0, 0))), 34, 9.0, up=Vector((0, 0, 1)))

# ================================================================ render
if __name__ == '__main__':
    if a.gmeter:
        keys = [[round(f / FPS, 3), round(g_story(f / FPS), 2)] for f in range(0, int(round(TOTAL * FPS)) + 1, 3)]
        json.dump(keys, open(a.gmeter, 'w')); print('gmeter', len(keys)); sys.exit(0)
    if a.blend: bpy.ops.wm.save_as_mainfile(filepath=a.blend)
    os.makedirs(a.out, exist_ok=True)
    N_ = int(round(TOTAL * FPS))
    if a.only: todo = [int(x) for x in a.only.split(',')]; names = todo
    elif REDO:
        job = a.f0 // REDO['ch']; todo = REDO['frames'][job::REDO['jobs']]; names = [a.f0 + i for i in range(len(todo))]
    elif STRIDE:
        J = STRIDE['jobs']; job = a.f0 // STRIDE['ch']; todo = list(range(job, N_, J)); names = [a.f0 + i for i in range(len(todo))]
    else: todo = list(range(a.f0, a.f1)); names = todo
    for f, nm in zip(todo, names):
        frame(f); S.render.filepath = os.path.join(a.out, f'f_{nm:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', f, '->', nm, flush=True)
