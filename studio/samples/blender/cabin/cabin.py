# What happens when a plane loses cabin pressure, built and rendered in Blender (Cycles): a man in a window seat at 35,000 ft when the
# window next to him blows out; the cabin (seat rows, overhead bins, ceiling, window holes cut through a curved shell) fills with fog,
# loose things stream to the hole; an x-ray of his lungs as the oxygen in his blood falls (Z-Anatomy lungs, CC BY-SA 4.0, BodyParts3D);
# the masks drop; the plane dives (outside: a shape-built jet over a cloud deck); the 2024 Alaska Airlines door plug (16,000 ft, the
# seats beside it empty, a shirt and phones out the hole, a phone found by a road still working).
#   python3 cabin.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]      (stride.json / redo.json beside it: see ../ele/ele.py)
# Needs man.blend (../foot/man_build.py) and lungs.blend (lung_build.py) beside it or in /root/vt/n42/cabin.
import sys, os, math, json, argparse, random
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n42/cabin', n), os.path.join('/root/vt/n42/cramp', n)) if os.path.exists(p_))
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
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
# ================================================================ THE CABIN (nose toward -y, his window on +x; floor z=0)
# shell: a circle R=1.9 about z=0.85 swept along y, cut by the floor; windows are real holes (boolean) so the sky shows through
RC, ZC = 1.9, 0.85; Y0C, Y1C = -6.4, 6.4
PITCH = 0.81; NROW = 15; ROW_Y = [-5.6 + PITCH * i for i in range(NROW)]; MYROW = 7; MY = ROW_Y[MYROW]      # his row
WIN_Z = 1.02; WIN_W, WIN_H, WIN_R = 0.27, 0.37, 0.11
def fix_normals(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free(); o.data.update(); return o
def wall_x(z): return math.sqrt(max(0.0, RC * RC - (z - ZC) ** 2))
def prism(name, prof, y0, y1, m, parent=None, smooth_=False):
    """profile [(x, z)...] (closed, counter-clockwise seen from -y) swept from y0 to y1"""
    n = len(prof); vs = [(x, y0, z) for x, z in prof] + [(x, y1, z) for x, z in prof]
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=smooth_)
def rrect(w, h, r, seg=6):
    """rounded rectangle outline (u, v), centred"""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(seg + 1): a = R(a0 + 90 * k / seg); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts
def ring_x(name, outer, inner, x0, x1, m, yc=0.0, zc=0.0, parent=None):
    """a flat ring (outer and inner outlines with the same point count) in the y-z plane, thickness along x"""
    n = len(outer); P = [(x0, outer), (x0, inner), (x1, inner), (x1, outer)]; vs = []
    for x, pts in P: vs += [(x, yc + u, zc + v) for u, v in pts]
    fs = []
    for a_ in range(4):
        b_ = (a_ + 1) % 4
        for i in range(n): j = (i + 1) % n; fs.append((a_ * n + i, a_ * n + j, b_ * n + j, b_ * n + i))
    return mesh(name, vs, fs, m, parent, smooth_=False)
def slab_x(name, pts_yz, x0, x1, m, yc=0.0, zc=0.0, parent=None):
    """a flat outline in the y-z plane, given thickness along x"""
    n = len(pts_yz); vs = [(x0, yc + u, zc + v) for u, v in pts_yz] + [(x1, yc + u, zc + v) for u, v in pts_yz]
    fs = [tuple(range(n)), tuple(range(n, 2 * n))[::-1]] + [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=False)
# ---- materials
WALL_M = noisy(mat('cabin_wall', (0.66, 0.65, 0.62), 0.45, coat=0.15), 60.0, 0.05, 0.05)
TRIM_M = mat('trim', (0.72, 0.72, 0.7), 0.35)
CARPET_M = noisy(mat('carpet', (0.13, 0.15, 0.22), 0.95, sheen=0.4), 300.0, 0.25, 0.05)
SEAT_M = noisy(mat('seat_fabric', (0.07, 0.11, 0.26), 0.9, sheen=0.6), 180.0, 0.2, 0.05)
HEADC_M = mat('headrest_cover', (0.82, 0.83, 0.85), 0.7, sheen=0.3)
PLAST_M = mat('seat_plastic', (0.35, 0.36, 0.38), 0.4)
METAL_M = mat('seat_metal', (0.6, 0.62, 0.65), 0.3, metal=1.0)
GLASS_M = mat('window_glass', (0.9, 0.95, 1.0), 0.02, trans=1.0, ior=1.49)
LAMP_M = emis('cove_light', (1.0, 0.9, 0.75), 3.0)
READ_M = emis('reading_light', (1.0, 0.95, 0.85), 2.0)
SIGN_M = emis('sign', (0.95, 0.95, 0.95), 1.5)
DARK_M = mat('dark_gap', (0.02, 0.02, 0.025), 0.6)
CABIN = []
# ---- shell (inside faces), solid 6 cm, windows cut through
_ang = [R(-26.6 + (233.2) * k / 64) for k in range(65)]
_prof = [(RC * math.cos(a), ZC + RC * math.sin(a)) for a in _ang]
_ys = [Y0C + (Y1C - Y0C) * k / 64 for k in range(65)]
vs = [(x, y, z) for y in _ys for (x, z) in _prof]; np_ = len(_prof); fs = []
for j in range(len(_ys) - 1):
    for i in range(np_ - 1): a_ = j * np_ + i; fs.append((a_, a_ + np_, a_ + np_ + 1, a_ + 1))
SHELL = mesh('shell', vs, fs, WALL_M); sol_ = SHELL.modifiers.new('thick', 'SOLIDIFY'); sol_.thickness = 0.06; sol_.offset = -1.0
_wv, _wf = [], []
for side in (1, -1):
    for y in ROW_Y:
        pts = rrect(WIN_W, WIN_H, WIN_R); n = len(pts); b0 = len(_wv)
        _wv += [(side * 1.55, y - 0.06 + u, WIN_Z + v) for u, v in pts] + [(side * 2.3, y - 0.06 + u, WIN_Z + v) for u, v in pts]
        _wf += [tuple(b0 + i for i in range(n)), tuple(b0 + n + i for i in range(n))[::-1]] + [(b0 + i, b0 + n + i, b0 + n + (i + 1) % n, b0 + (i + 1) % n) for i in range(n)]
WCUT = fix_normals(mesh('window_cutters', _wv, _wf, None, smooth_=False)); WCUT.hide_render = True; WCUT.hide_viewport = True
bo = SHELL.modifiers.new('windows', 'BOOLEAN'); bo.object = WCUT; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
# the door plug hole (the 2024 story): a door-sized cut on the -x side at row 11, only on in those beats
PLUG_ROW = 11; PLUG_Y = ROW_Y[PLUG_ROW] - 0.1; PLUG_W, PLUG_H, PLUG_Z = 0.66, 1.25, 0.95
_pc = rrect(PLUG_W, PLUG_H, 0.16)
PCUT = fix_normals(slab_x('plug_cutter', _pc, -2.3, -1.4, None, PLUG_Y, PLUG_Z)); PCUT.hide_render = True; PCUT.hide_viewport = True
PLUG_BO = SHELL.modifiers.new('plug', 'BOOLEAN'); PLUG_BO.object = PCUT; PLUG_BO.operation = 'DIFFERENCE'; PLUG_BO.solver = 'EXACT'
PLUG_BO.show_render = PLUG_BO.show_viewport = False
CABIN.append(SHELL)
# window glass in every hole (his one is its own object: it goes)
PANES = []
for side in (1, -1):
    for i, y in enumerate(ROW_Y):
        wx = wall_x(WIN_Z) + 0.015
        p_ = slab_x(f'pane_{side}_{i}', rrect(WIN_W - 0.01, WIN_H - 0.01, WIN_R - 0.005), side * (wx - 0.005), side * (wx + 0.005), GLASS_M, y - 0.06, WIN_Z)
        PANES.append(p_); CABIN.append(p_)
MYPANE = PANES[MYROW]
# his window's inner trim + pane: the piece that blows out (pivot = its middle)
_wx0 = wall_x(WIN_Z)
BLOW = empty("blowout", loc=(_wx0 - 0.04, MY - 0.06, WIN_Z))
RING_O = [(u * 1.3, v * 1.22) for u, v in rrect(WIN_W, WIN_H, WIN_R)]; RING_I = [(u * 1.0, v * 1.0) for u, v in rrect(WIN_W, WIN_H, WIN_R)]
BLOWP = ring_x('blow_trim', RING_O, RING_I, -0.015, 0.015, TRIM_M, 0, 0, parent=BLOW)
BLOWG = slab_x("blow_pane", rrect(WIN_W - 0.02, WIN_H - 0.02, WIN_R - 0.01), -0.009, 0.009, GLASS_M, 0, 0, parent=BLOW); BLOWG.rotation_mode = "XYZ"
CABIN += [BLOWP, BLOWG]
# window surrounds (raised trim ring around every hole, not his: his ring is BLOWP)
for side in (1, -1):
    for i, y in enumerate(ROW_Y):
        if side == 1 and i == MYROW: continue
        x_ = side * (_wx0 - 0.04); o_ = ring_x(f'trim_{side}_{i}', RING_O, RING_I, x_ - 0.015, x_ + 0.015, TRIM_M, y - 0.06, WIN_Z)
        CABIN.append(o_)
# ---- floor, ceiling, bins, lights
FLOOR = box('floor', (3.4, Y1C - Y0C, 0.06), (0, 0, -0.03), CARPET_M); CABIN.append(FLOOR)
AISLE = box('aisle_strip', (0.5, Y1C - Y0C, 0.004), (0, 0, 0.002), noisy(mat('aisle_carpet', (0.2, 0.17, 0.2), 0.95, sheen=0.3), 300.0, 0.2)); CABIN.append(AISLE)
CEIL = prism('ceiling', [(-0.95, 2.18), (0.95, 2.18), (0.85, 2.3), (-0.85, 2.3)], Y0C, Y1C, WALL_M); CABIN.append(CEIL)
for side in (1, -1):
    pr = [(0.95, 1.62), (1.66, 1.62), (wall_x(2.12) - 0.02, 2.12), (0.95, 2.12)]
    if side < 0: pr = [(-x, z) for x, z in pr][::-1]
    b_ = prism(f'bins_{side}', pr, Y0C + 0.1, Y1C - 0.1, WALL_M); bevel(b_, 0.025, 3); CABIN.append(b_)
    lip = prism(f'bin_lip_{side}', [(side * 0.93, 1.6), (side * 0.97, 1.6), (side * 0.97, 2.14), (side * 0.93, 2.14)][::side], Y0C + 0.1, Y1C - 0.1, TRIM_M); CABIN.append(lip)
    for k in range(9):                                                   # bin door seams
        y = Y0C + 0.1 + k * 1.58
        CABIN.append(box(f'bin_seam_{side}_{k}', (0.012, 0.012, 0.5), (side * 0.925, y, 1.87), DARK_M))
    cove = box(f'cove_{side}', (0.03, Y1C - Y0C - 0.4, 0.03), (side * 0.9, 0, 2.165), LAMP_M); CABIN.append(cove)
    psu = box(f'psu_{side}', (0.68, Y1C - Y0C - 0.2, 0.03), (side * 1.3, 0, 1.605), TRIM_M); CABIN.append(psu)
    for i, y in enumerate(ROW_Y):
        for dx in (-0.18, 0.0, 0.18):
            CABIN.append(prim('cylinder', f'read_{side}_{i}_{dx}', READ_M, loc=(side * (1.3 + dx), y - 0.55, 1.588), radius=0.018, depth=0.004, vertices=16))
LOW = []                                                                 # side-wall air vents / lower panel line
for side in (1, -1):
    LOW.append(box(f'dado_{side}', (0.02, Y1C - Y0C, 0.02), (side * (wall_x(0.45) - 0.03), 0, 0.45), TRIM_M))
CABIN += LOW
# ---- seats: one triple unit (mesh shared by every row), facing -y; row origin = middle of the cushions
def triple(name):
    parts = []
    for k, sx in enumerate((-0.46, 0.0, 0.46)):
        parts.append(box('cu', (0.43, 0.47, 0.11), (sx, -0.02, 0.405), SEAT_M, bv=0.035))
        bk = box('bk', (0.43, 0.1, 0.72), (sx, 0.27, 0.82), SEAT_M, bv=0.04, rot=(R(-11), 0, 0)); parts.append(bk)
        parts.append(box('hc', (0.38, 0.115, 0.2), (sx, 0.335, 1.08), HEADC_M, bv=0.03, rot=(R(-11), 0, 0)))
        parts.append(box('sh', (0.43, 0.03, 0.62), (sx, 0.335, 0.8), PLAST_M, bv=0.01, rot=(R(-11), 0, 0)))     # plastic back shell
        parts.append(box('tray', (0.36, 0.02, 0.26), (sx, 0.355, 0.86), PLAST_M, bv=0.008, rot=(R(-11), 0, 0)))
        parts.append(box('pk', (0.32, 0.03, 0.2), (sx, 0.31, 0.56), SEAT_M, bv=0.01, rot=(R(-11), 0, 0)))
    for ax in (-0.69, -0.23, 0.23, 0.69):
        parts.append(box('ar', (0.05, 0.42, 0.05), (ax, -0.02, 0.63), PLAST_M, bv=0.015))
        parts.append(box('as', (0.03, 0.08, 0.2), (ax, 0.12, 0.53), PLAST_M))
    for lx in (-0.55, 0.55):
        parts.append(box('lg', (0.04, 0.04, 0.34), (lx, -0.12, 0.17), METAL_M)); parts.append(box('lg2', (0.04, 0.04, 0.34), (lx, 0.2, 0.17), METAL_M))
        parts.append(box('ft', (0.04, 0.5, 0.03), (lx, 0.04, 0.015), METAL_M))
    parts.append(box('bar', (1.3, 0.04, 0.04), (0, 0.04, 0.33), METAL_M))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        for md in o.modifiers: pass
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    for o in parts:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); o = bpy.context.active_object; o.name = name
    return o
SEAT_T = triple('seats_tpl'); SEAT_T.hide_render = True; SEAT_T.hide_viewport = True
SEATS = {}
for side in (1, -1):
    for i, y in enumerate(ROW_Y):
        o_ = bpy.data.objects.new(f'seats_{side}_{i}', SEAT_T.data); S.collection.objects.link(o_); o_.location = (side * 0.98, y, 0); SEATS[(side, i)] = o_; CABIN.append(o_)
MYSEAT_X = 0.98 + 0.46                                                   # his window seat (A)
# end walls (dark-ish bulkheads with a lit sign)
for yy, sg in ((Y0C, 1), (Y1C, -1)):
    CABIN.append(box(f'bulk_{yy}', (3.8, 0.05, 2.8), (0, yy, 1.2), WALL_M))
CABIN.append(box('exit_sign', (0.4, 0.02, 0.12), (0, Y0C + 0.04, 2.05), emis('exit', (0.1, 1.0, 0.3), 3.0)))
# ================================================================ OUTSIDE: the jet (nose -y), the cloud deck far below, and the roadside
PX = V3(400.0, 0.0, 0.0)                                                 # the jet's middle (same height as the cabin; the deck is under both)
CLOUD_Z = -420.0
JET = empty('jet', loc=PX); JET.rotation_mode = 'XYZ'
PAINT_M = mat('paint', (0.9, 0.91, 0.93), 0.25, coat=0.6)
BELLY_M = mat('belly', (0.62, 0.64, 0.68), 0.35, coat=0.3)
TAIL_M = mat('tail_paint', (0.05, 0.14, 0.32), 0.3, coat=0.6)
WINGM = mat('wing', (0.7, 0.72, 0.75), 0.35, metal=0.3)
NAC_M = mat('nacelle', (0.78, 0.79, 0.82), 0.3, metal=0.4, coat=0.4)
WINX_M = mat('ext_window', (0.03, 0.04, 0.06), 0.08, coat=1.0)
JETP = []
_fp = [(0.05, -19.0), (0.3, -18.6), (0.8, -17.2), (1.35, -15.2), (1.75, -13.0), (1.95, -10.5), (1.97, -6), (1.97, 6), (1.97, 13.0), (1.88, 15.2),
       (1.62, 16.8), (1.25, 17.9), (0.75, 18.7), (0.25, 19.15), (0.02, 19.3)]
FUS = lathe('fuselage', _fp, 64, PAINT_M, parent=JET); FUS.rotation_euler = (R(90), 0, 0); JETP.append(FUS)
for side in (1, -1):
    for k in range(30):
        y = -12.5 + k * 0.83
        if abs(y - 2.5) < 0.6: continue
        JETP.append(box(f'xwin_{side}_{k}', (0.05, 0.24, 0.34), (side * 1.99, y, 0.42), WINX_M, bv=0.015, parent=JET))
    for k in range(3):
        JETP.append(box(f'cockpit_{side}_{k}', (0.06, 0.55, 0.42), (side * (1.45 - 0.22 * k), -16.6 - 0.55 * k, 0.75 + 0.05 * k), WINX_M, bv=0.05,
                        rot=(0, side * R(-25 - 12 * k), side * R(18 + 10 * k)), parent=JET))
def wing(name, root, tip, m, parent):
    """root/tip: (x, y_le, y_te, z, thick)"""
    vs = []
    for x, yl, yt, z, th in (root, tip):
        c = yt - yl; vs += [(x, yl, z), (x, yl + 0.3 * c, z + th / 2), (x, yt, z), (x, yl + 0.3 * c, z - th / 2)]
    fs = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 3, 2, 1), (4, 5, 6, 7)]
    o = mesh(name, vs, fs, m, parent, smooth_=False); md = o.modifiers.new('ws', 'SUBSURF'); md.levels = md.render_levels = 1; return o
for side in (1, -1):
    JETP.append(wing(f'wing_{side}', (side * 1.5, -3.2, 4.2, -1.0, 0.55), (side * 17.5, 6.6, 8.1, 0.45, 0.14), WINGM, JET))
    JETP.append(wing(f'stab_{side}', (side * 0.6, 14.2, 17.6, 0.5, 0.3), (side * 6.6, 17.6, 18.6, 1.0, 0.08), WINGM, JET))
    nac = lathe(f'nacelle_{side}', [(0.82, -2.2), (1.02, -1.9), (1.05, -0.5), (0.95, 1.2), (0.55, 2.0), (0.3, 2.3)], 48, NAC_M, parent=JET)
    nac.rotation_euler = (R(90), 0, 0); nac.location = (side * 5.6, -4.6, -2.0); JETP.append(nac)
    fan = prim('cylinder', f'fan_{side}', mat(f'fan_{side}', (0.08, 0.08, 0.09), 0.3, metal=0.8), parent=JET, loc=(side * 5.6, -2.55, -2.0), rot=(R(90), 0, 0), radius=0.8, depth=0.05, vertices=32)
    JETP.append(fan)
    JETP.append(box(f'pylon_{side}', (0.25, 3.4, 0.8), (side * 5.6, -3.2, -1.35), WINGM, bv=0.08, parent=JET))
def vfin(name, root, tip, m, parent):
    """an upright surface: root/tip = (y_le, y_te, z, thick), thickness along x"""
    vs = []
    for yl, yt, z, th in (root, tip):
        c = yt - yl; vs += [(0, yl, z), (th / 2, yl + 0.3 * c, z), (0, yt, z), (-th / 2, yl + 0.3 * c, z)]
    fs = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 3, 2, 1), (4, 5, 6, 7)]
    o = mesh(name, vs, fs, m, parent, smooth_=False); md = o.modifiers.new('ws', 'SUBSURF'); md.levels = md.render_levels = 1; return o
fin = vfin('fin', (11.8, 18.2, 1.7, 0.4), (16.6, 18.7, 8.6, 0.12), TAIL_M, JET); JETP.append(fin)
# the door plug (the -x side, aft of the wing): a panel with a seam, a dark hole behind it once it goes
PLUGE_Y, PLUGE_Z = 6.3, 0.15
PLUGE = empty('plug_ext', parent=JET, loc=(-2.0, PLUGE_Y, PLUGE_Z)); PLUGE.rotation_mode = 'XYZ'
PLUGP = slab_x('plug_panel', rrect(0.7, 1.3, 0.16), -0.015, 0.015, PAINT_M, 0, 0, parent=PLUGE); JETP.append(PLUGP)
PLUGW = box('plug_win', (0.03, 0.24, 0.34), (-0.012, 0.0, 0.27), WINX_M, bv=0.015, parent=PLUGE); JETP.append(PLUGW)
SEAM = ring_x('plug_seam', [(u * 1.06, v * 1.04) for u, v in rrect(0.7, 1.3, 0.16)], rrect(0.7, 1.3, 0.16), -2.025, -1.99, DARK_M, PLUGE_Y, PLUGE_Z, parent=JET); JETP.append(SEAM)
HOLE_M = emis('hole_glow', (0.35, 0.28, 0.22), 0.35)
HOLE = slab_x('plug_hole', rrect(0.68, 1.28, 0.16), -2.016, -2.01, HOLE_M, PLUGE_Y, PLUGE_Z, parent=JET); HOLE.hide_render = True; JETP.append(HOLE)
# ---- the cloud deck: a big lumpy sheet, sunlit tops
CLOUD_M = mat('cloud', (0.95, 0.96, 1.0), 0.9, sheen=0.5)
_b = CLOUD_M.node_tree.nodes['Principled BSDF']; _b.inputs['Subsurface Weight'].default_value = 0.6; _b.inputs['Subsurface Radius'].default_value = (30.0, 30.0, 34.0)
noisy(CLOUD_M, 0.004, 0.18, 0.05, coord='Object')
bpy.ops.mesh.primitive_grid_add(x_subdivisions=300, y_subdivisions=300, size=24000, location=(0, 0, CLOUD_Z)); CLOUDS = bpy.context.active_object; CLOUDS.name = 'clouds'
CLOUDS.data.materials.append(CLOUD_M)
for p_ in CLOUDS.data.polygons: p_.use_smooth = True
_tx = bpy.data.textures.new('cloud_tex', 'CLOUDS'); _tx.noise_scale = 900.0; _tx.noise_depth = 4
_dm = CLOUDS.modifiers.new('puff', 'DISPLACE'); _dm.texture = _tx; _dm.strength = 160.0; _dm.mid_level = 0.55; _dm.texture_coords = 'GLOBAL'
_tx2 = bpy.data.textures.new('cloud_tex2', 'CLOUDS'); _tx2.noise_scale = 160.0; _tx2.noise_depth = 2
_dm2 = CLOUDS.modifiers.new('puff2', 'DISPLACE'); _dm2.texture = _tx2; _dm2.strength = 40.0; _dm2.mid_level = 0.5; _dm2.texture_coords = 'GLOBAL'
# ---- the roadside where a phone was found (far off, under the deck: the deck is hidden there)
GX = V3(-3000.0, 0.0, -1500.0)
GRASS_M = noisy(mat('grass', (0.13, 0.22, 0.06), 0.85, sheen=0.4), 60.0, 0.5, 0.1)
GROUND = box('roadside', (80, 80, 0.2), GX + V3(0, 0, -0.1), GRASS_M)
ROAD_M = noisy(mat('asphalt', (0.11, 0.105, 0.1), 0.92), 260.0, 0.45, 0.05)
ROAD = box('road', (6.5, 80, 0.06), GX + V3(1.6 + 3.25, 0, 0.0), ROAD_M)
LINE = box('road_line', (0.12, 80, 0.07), GX + V3(1.6 + 3.25, 0, 0.0), mat('yellow_line', (0.85, 0.65, 0.1), 0.6))
EDGE = box('road_edge', (0.1, 80, 0.07), GX + V3(1.75, 0, 0.0), mat('white_line', (0.8, 0.8, 0.78), 0.6))
GRAVEL = box('shoulder', (0.6, 80, 0.04), GX + V3(1.3, 0, 0.0), noisy(mat('gravel', (0.42, 0.39, 0.34), 0.95), 300.0, 0.6, 0.05))
# grass blades: hair on a patch around the phone
_gp = box('grass_patch', (5.0, 7.0, 0.02), GX + V3(-1.5, 0, 0.0), GRASS_M)
BLADE_M = GRASS_M
PHONE_M = mat('phone_body', (0.02, 0.02, 0.025), 0.15, coat=1.0)
SCREEN_M = bpy.data.materials.new('phone_screen'); SCREEN_M.use_nodes = True
_nt = SCREEN_M.node_tree; _nt.nodes.remove(_nt.nodes['Principled BSDF']); _e = _nt.nodes.new('ShaderNodeEmission'); _g = _nt.nodes.new('ShaderNodeTexGradient')
_tc = _nt.nodes.new('ShaderNodeTexCoord'); _cr = _nt.nodes.new('ShaderNodeValToRGB'); _nt.links.new(_tc.outputs['Generated'], _g.inputs['Vector'])
_cr.color_ramp.elements[0].color = (0.1, 0.25, 0.9, 1); _cr.color_ramp.elements[1].color = (0.7, 0.2, 0.75, 1)
_nt.links.new(_g.outputs['Fac'], _cr.inputs['Fac']); _nt.links.new(_cr.outputs['Color'], _e.inputs['Color']); _e.inputs['Strength'].default_value = 2.2
_nt.links.new(_e.outputs['Emission'], _nt.nodes['Material Output'].inputs['Surface'])
PHONE_AT = GX + V3(1.25, 0.0, 0.021)
PHONE = box('phone', (0.074, 0.155, 0.008), PHONE_AT + V3(0, 0, 0.004), PHONE_M, bv=0.008, rot=(0, 0, R(28)))
SCREEN = box('phone_screen', (0.066, 0.145, 0.001), (0, 0, 0.0043), SCREEN_M, bv=0.004, parent=PHONE)
bpy.ops.object.text_add(location=(0, 0.035, 0.0055)); CLOCKT = bpy.context.active_object; CLOCKT.name = 'phone_time'; CLOCKT.data.body = '7:12'
CLOCKT.data.size = 0.022; CLOCKT.data.align_x = 'CENTER'; CLOCKT.parent = PHONE; CLOCKT.data.materials.append(emis('phone_text', (1, 1, 1), 4.0))
ROADSIDE = [GROUND, ROAD, LINE, EDGE, GRAVEL, _gp, PHONE, SCREEN, CLOCKT]
# ---- light: the sun (outside and through the windows), cabin ceiling lights, a soft fill; the sky is a gradient on the view direction
SUNL = bpy.data.lights.new('sun', 'SUN'); SUNL.energy = 4.0; SUNL.color = (1.0, 0.96, 0.9); SUNL.angle = R(1.5)
SUN_O = bpy.data.objects.new('sun', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_mode = 'QUATERNION'
def sun_from(d, energy=4.0, col=(1.0, 0.96, 0.9)):
    """d: direction TO the sun"""
    SUN_O.rotation_quaternion = (-Vector(d)).to_track_quat('-Z', 'Y'); SUNL.energy = energy; SUNL.color = col
sun_from((0.75, -0.25, 0.45))
CAB_L = []
for side in (1, -1):
    for k in range(5):
        CAB_L.append(light_at(f'ceil_{side}_{k}', 'AREA', (side * 0.55, -5.0 + 2.5 * k, 2.12), (side * 0.9, -5.0 + 2.5 * k, 0.0), 40, (1.0, 0.92, 0.8), 0.6))
FILLC = light_at('cabin_fill', 'AREA', (0.0, -3.0, 1.6), (1.3, 0.0, 1.0), 25, (0.85, 0.9, 1.0), 1.5); CAB_L.append(FILLC)
KEYC = light_at('cabin_key', 'AREA', (0.2, MY - 1.2, 1.5), (MYSEAT_X, MY, 1.1), 18, (1.0, 0.95, 0.9), 0.5); CAB_L.append(KEYC)
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Strength'].default_value = 1.0
_tc = wnt.nodes.new('ShaderNodeTexCoord'); _sx = wnt.nodes.new('ShaderNodeSeparateXYZ'); wnt.links.new(_tc.outputs['Generated'], _sx.inputs['Vector'])
SKYR = wnt.nodes.new('ShaderNodeValToRGB'); wnt.links.new(_sx.outputs['Z'], SKYR.inputs['Fac'])
_el = SKYR.color_ramp.elements; _el[0].position = 0.0; _el[0].color = (0.75, 0.8, 0.88, 1); _el[1].position = 0.6; _el[1].color = (0.08, 0.22, 0.6, 1)
_e2 = _el.new(0.5); _e2.color = (0.72, 0.82, 0.95, 1); _e3 = _el.new(0.53); _e3.color = (0.42, 0.6, 0.9, 1)
# world Generated z runs -1..1 -> map to 0..1
_mr = wnt.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = -1.0; _mr.inputs['From Max'].default_value = 1.0
wnt.links.new(_sx.outputs['Z'], _mr.inputs['Value']); wnt.links.new(_mr.outputs['Result'], SKYR.inputs['Fac'])
WMIX = wnt.nodes.new('ShaderNodeMix'); WMIX.data_type = 'RGBA'; WMIX.inputs['Factor'].default_value = 0.0; WMIX.inputs['B'].default_value = (0.004, 0.012, 0.035, 1)
wnt.links.new(SKYR.outputs['Color'], WMIX.inputs['A']); wnt.links.new(WMIX.outputs['Result'], WBG.inputs['Color'])
def world(kind):
    """'sky' or 'xray' (dark blue)"""
    WMIX.inputs['Factor'].default_value = 1.0 if kind == 'xray' else 0.0
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.02; CAM.data.clip_end = 30000
XL = light_at('xray_key', 'AREA', (MYSEAT_X - 1.0, MY - 1.4, 1.6), (MYSEAT_X, MY, 1.2), 40, (0.85, 0.9, 1.0), 1.5); XL.hide_render = True
XL2 = light_at('xray_rim', 'AREA', (MYSEAT_X + 0.6, MY + 0.8, 1.4), (MYSEAT_X, MY, 1.2), 30, (0.7, 0.8, 1.0), 1.2); XL2.hide_render = True
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
retint(SHORTS_M, (0.2, 0.25, 0.36), 0.35, 0.95, 0.6)                 # navy pants
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
# ================================================================ HIS LUNGS (lungs.blend: Z-Anatomy lobes, trachea, diaphragm, ribs, spine, fitted in his
# rest space by lung_build.py). They ride the rig as one piece (his trunk stays straight in the x-ray shot; he leans from the hips)
ANAT = []
with bpy.data.libraries.load(asset('lungs.blend'), link=False) as (_s, _d): _d.objects = list(_s.objects)
for o in _d.objects:
    S.collection.objects.link(o); o.parent = RIG; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, 0, 0)
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False; ANAT.append(o)
def kind(k): return [o for o in ANAT if o['kind'] == k]
ANAT = [o for o in ANAT if not (o['kind'] == 'bone' and (o.name.startswith('Hip bone') or o.name.startswith('Sacrum') or o.name.startswith('Coccyx')))]
for o in list(_d.objects):
    if o not in ANAT: o.hide_render = True; o.hide_viewport = True
def bone_mat():
    m = mat('bone', (0.86, 0.82, 0.72), 0.55, sheen=0.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (0.75, 0.85, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY', lw.outputs['Facing'], 1.2), b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
BONE_M = bone_mat()
for o in kind('bone'): o.data.materials.clear(); o.data.materials.append(BONE_M)
def lung_mat(name, good, bad, alpha):
    """soft see-through organ; object prop 'oxy' 1 = pink and full of oxygen, 0 = dull blue-grey (starved); 'tt' moves the sheen"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    b.inputs['Roughness'].default_value = 0.35; b.inputs['Coat Weight'].default_value = 0.4
    b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Radius'].default_value = (0.01, 0.004, 0.003)
    ox = objattr(nt, 'oxy')
    bc = nt.nodes.new('ShaderNodeMix'); bc.data_type = 'RGBA'; bc.inputs['A'].default_value = (*bad, 1); bc.inputs['B'].default_value = (*good, 1)
    nt.links.new(ox, bc.inputs['Factor']); nt.links.new(bc.outputs['Result'], b.inputs['Base Color'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60.0; nz.noise_dimensions = '4D'; nt.links.new(objattr(nt, 'tt'), nz.inputs['W'])
    rim = nt.nodes.new('ShaderNodeMix'); rim.data_type = 'RGBA'; rim.inputs['A'].default_value = (0.35, 0.45, 1.0, 1); rim.inputs['B'].default_value = (1.0, 0.45, 0.45, 1)
    nt.links.new(ox, rim.inputs['Factor']); nt.links.new(rim.outputs['Result'], b.inputs['Emission Color'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', lw.outputs['Facing'], 0.9), math_(nt, 'MULTIPLY', nz.outputs['Fac'], math_(nt, 'MULTIPLY', ox, 0.5))), b.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.6, alpha), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(b.outputs['BSDF'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
LUNG_M = lung_mat('lung', (0.95, 0.42, 0.45), (0.38, 0.36, 0.62), 0.38)
TRACH_M = lung_mat('trachea', (0.95, 0.8, 0.75), (0.7, 0.7, 0.85), 0.5)
DIAPH_M = lung_mat('diaphragm', (0.75, 0.2, 0.18), (0.4, 0.25, 0.4), 0.22)
for k_, m_ in (('lung', LUNG_M), ('trachea', TRACH_M), ('diaphragm', DIAPH_M)):
    for o in kind(k_): o.data.materials.clear(); o.data.materials.append(m_); o['oxy'] = 1.0; o['tt'] = 0.0
def centre(o): return sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
LUNGS = kind('lung'); LC = sum((centre(o) for o in LUNGS), Vector()) / len(LUNGS)
for o in LUNGS + kind('diaphragm'):                                      # breathe about the middle of the chest (shrunk 6% to sit inside him)
    c_ = LC
    for v in o.data.vertices: v.co = (v.co - c_) * 0.94
    o.location = c_; o['home'] = list(c_)
XRAY_OBJS = ANAT
def lungs(t, oxy=1.0, rate=0.25, depth=1.0):
    """breathing: rate = breaths a second; oxy 0..1 colour"""
    ph = 0.5 - 0.5 * math.cos(2 * math.pi * rate * t); k = 1.0 + 0.045 * depth * ph
    for o in LUNGS: o.scale = (k, 1.0 + 0.03 * depth * ph, 1.0 + 0.06 * depth * ph); o['oxy'] = oxy; o['tt'] = t
    for o in kind('diaphragm'): o.scale = (1.0, 1.0, 1.0); o.location = Vector(o['home']) - V3(0, 0, 0.02 * depth * ph); o['oxy'] = oxy; o['tt'] = t
    for o in kind('trachea'): o['oxy'] = oxy; o['tt'] = t
for o in XRAY_OBJS: o.hide_render = True
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
    FOOT[s_] = (e_, RB['foot.' + s_].matrix_local.to_3x3(), c_)
def feet_flat(on=True, phi=0.0):
    for s_ in 'RL':
        e_, M0, c_ = FOOT[s_]; c_.influence = 1.0 if on else 0.0; e_.rotation_quaternion = (Matrix.Rotation(R(phi), 3, 'X') @ M0).to_quaternion()
# ================================================================ HIS POSES (all built from the hip, a body turn, and hands/feet in his own frame)
def rigM(hip, rot):
    Rm = Euler(tuple(R(x) for x in rot)).to_matrix(); return Matrix.Translation(Vector(hip) - Rm @ HIP0) @ Rm.to_4x4()
def body(hip, rot, ankR, ankL, handR, handL, space='rig', neck=0.0, head=0.0, jaw=0.0, lids=0.0, curl=(0.3, 0.3), pk=(1.0, 1.0),
         palm=None, spine=0.0, kneel_pole=False, head_yaw=0.0):
    """space: 'rig' = ankles/hands in his own (rest) frame, moving with him; 'world' for ankles (planted)"""
    M = rigM(hip, rot); M3 = M.to_3x3()
    aR = M @ Vector(ankR) if space == 'rig' else Vector(ankR); aL = M @ Vector(ankL) if space == 'rig' else Vector(ankL)
    kp = V3(0, -2.0, 0.4) if not kneel_pole else V3(0, -2.0, -0.6)
    set_pose(hip, rot, spine, neck, head, head_yaw, 0.0, ankR=aR, poleR=M @ (V3(-0.15, 0, 0.5) + kp), ankL=aL, poleL=M @ (V3(0.15, 0, 0.5) + kp),
             curlR=curl[0], curlL=curl[1], lids=lids, jaw=jaw, poleArmR=M @ V3(-0.8, 0.6 * pk[0], 1.0), poleArmL=M @ V3(0.8, 0.6 * pk[1], 1.0))
    for s_, hp_ in (('R', handR), ('L', handL)):
        if palm and s_ in palm:
            c_, fd, pd = palm[s_]; place_hand(s_, M @ Vector(c_), M3 @ Vector(fd), M3 @ Vector(pd), 1.0)
        else: TGT['hand' + s_].location = M @ Vector(hp_); HAND[s_][2].influence = 0.0
    bpy.context.view_layer.update(); return M
def flail(t, k=1.0, seed=0.0):
    """limbs thrown about by the wind (rig space)"""
    w = lambda f, s_: wob(t, f, seed + s_) * k
    return dict(ankR=V3(-0.2 + 0.12 * w(1.3, 1), 0.15 + 0.25 * w(1.1, 2), 0.12 + 0.18 * w(0.9, 3)), ankL=V3(0.26 + 0.12 * w(1.2, 4), -0.12 + 0.3 * w(1.0, 5), 0.2 + 0.2 * w(0.8, 6)),
                handR=V3(-0.68 + 0.12 * w(1.5, 7), 0.12 + 0.3 * w(1.2, 8), 1.45 + 0.2 * w(1.0, 9)), handL=V3(0.62 + 0.12 * w(1.4, 10), 0.25 + 0.3 * w(1.3, 11), 1.25 + 0.25 * w(0.9, 12)))
STAND_HIP = 0.93
def stand(x, y, yaw, t, brace=0.0, lift=0.0):
    """on his feet by the trailer, facing yaw (deg); brace: knees bend, arms come up over his face; lift: heels leave the ground"""
    hip = V3(x, y, STAND_HIP - 0.12 * brace + lift); rot = (6 * brace + 3 * wob(t, 2, 1) * brace, 0, yaw)
    Rz = Matrix.Rotation(R(yaw), 3, 'Z'); aR = V3(x, y, 0) + Rz @ V3(-0.14, 0.02, 0.09 + lift * 0.9); aL = V3(x, y, 0) + Rz @ V3(0.14, 0.02, 0.09 + lift * 0.9)
    hR = V3(-0.28, 0.02, 0.86).lerp(V3(-0.1, -0.32, 1.62), brace); hL = V3(0.28, 0.02, 0.86).lerp(V3(0.12, -0.33, 1.6), brace)
    Rq = Matrix.Rotation(R(yaw), 3, 'Z')
    for s_ in 'RL': FOOT[s_][2].influence = 1.0; FOOT[s_][0].rotation_quaternion = (Rq @ FOOT[s_][1]).to_quaternion()
    body(hip, rot, aR, aL, hR, hL, space='world', neck=8 * brace, jaw=0.3 * brace, lids=0.5 * brace, curl=(0.3 + 0.5 * brace,) * 2)
    if lift < 0.01: ground(0.0)
def airborne(hip, rot, t, k=1.0, seed=0.0, jaw=0.6):
    feet_flat(False)
    f = flail(t, k, seed); body(hip, rot, f['ankR'], f['ankL'], f['handR'], f['handL'], neck=15 * wob(t, 1, seed), head=10 * wob(t, 1.3, seed), jaw=jaw, lids=0.6, curl=(0.6, 0.6), pk=(-1, -1))
def lying(x, y, sit, t):
    """on his back in the grass, head toward +y; sit 0..1: pushes up on his hands to sitting"""
    feet_flat(False); a = lerp(-88, -35, sm(sit)); hip = V3(x, y, 0.12 + 0.02 * sit); rot = (a, 0, 180)
    M = rigM(hip, rot)
    aR, aL = V3(-0.16, 0.05, 0.1), V3(0.2, 0.0, 0.12)
    hR = V3(-0.4, 0.15, 0.95).lerp(V3(-0.3, 0.32, 0.85), sit); hL = V3(0.42, 0.1, 0.9).lerp(V3(0.3, 0.32, 0.85), sit)
    body(hip, rot, aR, aL, hR, hL, neck=lerp(-5, 15, sit), head=lerp(0, 10, sit), lids=lerp(1.0, 0.1, smooth(0.0, 0.5, sit)), jaw=0.2, curl=(0.5, 0.5), kneel_pole=False)
    W, RP = body_eval(); mn = float(W[:, 2].min()); RIG.location.z += 0.002 - mn; bpy.context.view_layer.update()
def crouch(t, shake_=0.0):
    """in the closet: down on his knees and folded forward, both hands locked over the back of his head"""
    feet_flat(False); hip = CL + V3(0.0, -0.05, 0.42); rot = (68 + 2 * wob(t, 6, 3) * shake_, 0, 0)
    M = rigM(hip, rot); Mi = M.inverted()
    aR = Mi @ (CL + V3(-0.13, 0.32, 0.07)); aL = Mi @ (CL + V3(0.13, 0.32, 0.07))
    body(hip, rot, aR, aL, V3(-0.06, 0.15, 1.6), V3(0.06, 0.15, 1.62), neck=30, head=12, lids=1.0, jaw=0.1, curl=(0.15, 0.15),
         palm={'R': (V3(-0.03, 0.09, 1.71), V3(1, 0.2, -0.2), V3(0, -0.3, -1)), 'L': (V3(0.03, 0.09, 1.71), V3(-1, 0.2, -0.2), V3(0, -0.3, -1))}, kneel_pole=True)
    ground(1.0)
SEAT_HIP = V3(MYSEAT_X, MY + 0.12, 0.55)
def seated(t, lean=-8.0, at=None, handR=None, handL=None, neck=0.0, head=0.0, head_yaw=0.0, lids=0.0, jaw=0.0, curl=(0.35, 0.35), side_lean=0.0, palm=None, bob=0.0):
    """in his window seat (A), facing the nose (-y); hands in his own (rig) frame, default on his thighs"""
    sx_, sy_ = at if at is not None else (MYSEAT_X, MY)
    hip = V3(sx_, sy_ + 0.19, SEAT_HIP.z + 0.004 * bob * math.sin(t * 9)); rot = (lean, side_lean, 0.0)
    aR = V3(sx_ - 0.13, sy_ - 0.36, 0.085); aL = V3(sx_ + 0.13, sy_ - 0.36, 0.085)
    for s_ in 'RL': FOOT[s_][2].influence = 1.0; FOOT[s_][0].rotation_quaternion = FOOT[s_][1].to_quaternion()
    hR = handR if handR is not None else V3(-0.17, -0.36, 0.98); hL = handL if handL is not None else V3(0.17, -0.36, 0.98)
    body(hip, rot, aR, aL, hR, hL, space='world', neck=neck, head=head, head_yaw=head_yaw, lids=lids, jaw=jaw, curl=curl, palm=palm, pk=(1.0, 1.0))
# ================================================================ LOOSE THINGS pulled to a hole, the masks, a shirt
PAPER_M = noisy(mat('paper', (0.92, 0.9, 0.86), 0.7), 30.0, 0.08)
NAPKIN_M = mat('napkin', (0.95, 0.95, 0.95), 0.85, sheen=0.3)
CUP_M = mat('cup', (0.96, 0.96, 0.96), 0.4)
BAG_M = mat('snack_bag', (0.8, 0.15, 0.1), 0.3, metal=0.4)
MAG_M = noisy(mat('magazine', (0.2, 0.45, 0.7), 0.35, coat=0.4), 20.0, 0.3)
def card(name, w, h, m):
    o = box(name, (w, h, 0.002), (0, 0, 0), m); o.rotation_mode = 'XYZ'; return o
def cup(name):
    o = lathe(name, [(0.0, 0.0), (0.028, 0.0), (0.032, 0.002), (0.04, 0.095), (0.042, 0.1), (0.038, 0.1), (0.03, 0.006), (0.0, 0.006)], 24, CUP_M)
    o.rotation_mode = 'XYZ'; return o
class Flyers:
    """things pulled toward a hole: each starts at P0, waits 'delay', speeds up toward the hole (with a little weave), goes through and
    away (out = direction outside). Pure function of time, so frames can render in any order."""
    def __init__(self, items, seed):
        rr = np.random.default_rng(seed); self.items = []
        for o, P0, delay, *air in items:
            self.items.append(dict(o=o, P0=Vector(P0), d=delay, air=bool(air), acc=rr.uniform(9, 18), spin=Vector(rr.normal(size=3) * 9.0), ph=rr.uniform(0, 6.3), wv=rr.uniform(0.05, 0.2),
                                   rot0=Vector(o.rotation_euler) if o.rotation_mode == 'XYZ' else Vector()))
        self.objs = [it['o'] for it in self.items]
    def at(self, t, H, out, slow=1.0, on=True):
        for it in self.items:
            o = it['o']; o.hide_render = not on
            if not on: continue
            if it['air'] and t <= it['d']: o.hide_render = True
            tau = max(0.0, (t - it['d'])) * slow; P0 = it['P0']; D = Vector(H) - P0; L = max(D.length, 1e-3)
            dist = 0.5 * it['acc'] * tau * tau
            if dist < L:
                s = dist / L; side = D.cross(V3(0, 0, 1)); side = side.normalized() if side.length > 1e-4 else V3(1, 0, 0)
                p = P0 + D * s + side * math.sin(s * 7 + it['ph']) * it['wv'] * s * (1 - s) * 4 + V3(0, 0, 0.25 * s * (1 - s))
            else:
                v = math.sqrt(2 * it['acc'] * L); tt_ = (dist - L) / max(v, 1e-3); p = Vector(H) + Vector(out).normalized() * (v * tt_ + 4.0 * tt_ * tt_)
            o.location = p; o.rotation_euler = tuple(it['rot0'] + it['spin'] * tau * (0.2 if tau < 0.05 else 1.0))
rng_ = np.random.default_rng(7)
# ---- the blowout: things in the rows around his are pulled to his window
H_WIN = V3(wall_x(WIN_Z) + 0.05, MY - 0.06, WIN_Z)
_its = []
for i in range(34):
    kind_ = ['paper', 'napkin', 'cup', 'paper', 'napkin', 'bag', 'mag'][i % 7]
    row = MYROW + int(rng_.integers(-3, 3)); sx = rng_.choice([0.52, 0.98, 1.44, -0.52, -0.98, 1.44]); y = ROW_Y[row] + rng_.uniform(-0.45, 0.1)
    z = rng_.choice([0.47, 0.78, 0.02, 0.66])
    if kind_ == 'paper': o = card(f'fly_paper_{i}', 0.21, 0.28, PAPER_M)
    elif kind_ == 'napkin': o = card(f'fly_napkin_{i}', 0.16, 0.16, NAPKIN_M)
    elif kind_ == 'cup': o = cup(f'fly_cup_{i}')
    elif kind_ == 'bag': o = box(f'fly_bag_{i}', (0.1, 0.14, 0.02), (0, 0, 0), BAG_M, bv=0.008); o.rotation_mode = 'XYZ'
    else: o = card(f'fly_mag_{i}', 0.2, 0.27, MAG_M)
    o.rotation_euler = tuple(rng_.uniform(-0.3, 0.3, 3)); _its.append((o, (sx, y, z), rng_.uniform(-0.25, 0.9)))
for i in range(4):                                                       # close to the camera (frame one): papers already on their way
    o = card(f'fly_near_{i}', 0.15 if i % 2 else 0.12, 0.2 if i % 2 else 0.12, PAPER_M if i % 2 else NAPKIN_M)
    o.rotation_euler = tuple(rng_.uniform(-1, 1, 3)); _its.append((o, (MYSEAT_X - 0.3 + rng_.uniform(-0.12, 0.12), MY - 0.42 + rng_.uniform(-0.12, 0.12), rng_.uniform(1.15, 1.4)), -0.2 + 0.03 * i, True))
FLY_W = Flyers(_its, 3)
# a few drifting in front of the camera in the first beat (fill the frame)
# ---- the door plug: two phones and a shirt pulled out of the -x side hole
H_PLUG = V3(-wall_x(PLUG_Z) - 0.1, PLUG_Y, PLUG_Z)
PHN = [box(f'fly_phone_{k}', (0.074, 0.155, 0.008), (0, 0, 0), PHONE_M, bv=0.008) for k in range(2)]
for p_ in PHN:
    p_.rotation_mode = 'XYZ'; sc_ = box(p_.name + '_scr', (0.066, 0.145, 0.001), (0, 0, 0.0043), SCREEN_M, bv=0.004, parent=p_)
_its2 = [(PHN[0], (-1.0, ROW_Y[PLUG_ROW + 1] - 0.2, 0.66), 0.25), (PHN[1], (-0.5, ROW_Y[PLUG_ROW] - 0.3, 0.47), 0.55)]
for i in range(10):
    o = card(f'fly2_paper_{i}', 0.16 if i % 2 else 0.21, 0.16 if i % 2 else 0.28, NAPKIN_M if i % 2 else PAPER_M)
    _its2.append((o, (rng_.uniform(-1.5, -0.3), ROW_Y[PLUG_ROW + int(rng_.integers(-2, 2))] + rng_.uniform(-0.4, 0.1), rng_.choice([0.47, 0.66, 0.05])), rng_.uniform(0.0, 1.4)))
FLY_P = Flyers(_its2, 5)
# the shirt: a T outline, waving (verts moved every frame)
SHIRT2_M = mat('teen_shirt', (0.15, 0.32, 0.18), 0.85, sheen=0.5)
_sh = [(-0.24, -0.35), (0.24, -0.35), (0.24, 0.12), (0.36, 0.05), (0.42, 0.18), (0.2, 0.33), (0.08, 0.3), (0.0, 0.26), (-0.08, 0.3), (-0.2, 0.33), (-0.42, 0.18), (-0.36, 0.05), (-0.24, 0.12)]
bm_ = bmesh.new(); vs_ = [bm_.verts.new((x, y, 0)) for x, y in _sh]; bm_.faces.new(vs_)
bmesh.ops.triangulate(bm_, faces=bm_.faces[:]); bmesh.ops.subdivide_edges(bm_, edges=bm_.edges[:], cuts=3, use_grid_fill=True)
SHME = bpy.data.meshes.new('shirt'); bm_.to_mesh(SHME); bm_.free(); SHIRT2 = obj('flying_shirt', SHME, SHIRT2_M); SHIRT2.rotation_mode = 'XYZ'
_sd = SHIRT2.modifiers.new('cloth_thick', 'SOLIDIFY'); _sd.thickness = 0.004
for p_ in SHME.polygons: p_.use_smooth = True
SH_BASE = np.array([v.co[:] for v in SHME.vertices])
def shirt_wave(t, amp=0.06):
    x, y = SH_BASE[:, 0], SH_BASE[:, 1]; z = amp * (np.sin(x * 9 + t * 22) + 0.6 * np.sin(y * 11 - t * 17)) * (0.4 + np.abs(x) * 2)
    SHME.vertices.foreach_set('co', np.stack([x, y, z], 1).reshape(-1).astype(np.float32)); SHME.update()
FLY_S = Flyers([(SHIRT2, (-0.55, ROW_Y[PLUG_ROW] - 0.15, 1.15), 0.0)], 9); FLY_S.items[0]['acc'] = 6.0
# ---- masks: a door in the service panel over each row opens, three masks drop on tubes and swing
MASK_M = mat('mask', (1.0, 0.82, 0.05), 0.45, coat=0.3)
TUBEM = mat('mask_tube', (0.95, 0.95, 0.9), 0.2, trans=0.6)
BAGM = mat('mask_bag', (0.9, 0.95, 1.0), 0.15, trans=0.7, alpha=0.6)
MASKS = []                                                               # (row, side, seat_x, cup, tube curve, door)
def tube_curve(name):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(3); o = bpy.data.objects.new(name, cu); S.collection.objects.link(o); cu.materials.append(TUBEM); return o
MASK_ROWS = list(range(MYROW - 4, MYROW + 3))
DOORS = {}
for side in (1, -1):
    for r_ in MASK_ROWS:
        y = ROW_Y[r_]
        dpiv = empty(f'door_piv_{side}_{r_}', loc=(side * 1.12, y - 0.5, 1.588)); dpiv.rotation_mode = 'XYZ'
        door = box(f'mask_door_{side}_{r_}', (0.46, 0.2, 0.012), (side * 0.23, 0.0, -0.006), TRIM_M, bv=0.003, parent=dpiv); DOORS[(side, r_)] = (dpiv, door)
        CABIN.append(door)
        CABIN.append(box(f'mask_hole_{side}_{r_}', (0.44, 0.18, 0.004), (side * 1.35, y - 0.5, 1.586), DARK_M))
        for k, sx in enumerate((0.52, 0.98, 1.44)):
            c_ = lathe(f'mask_{side}_{r_}_{k}', [(0.0, 0.0), (0.022, 0.002), (0.036, 0.016), (0.044, 0.038), (0.046, 0.046), (0.043, 0.047), (0.04, 0.04), (0.032, 0.02), (0.0, 0.012)], 24, MASK_M)
            c_.rotation_mode = 'QUATERNION'; t_ = tube_curve(f'mask_tube_{side}_{r_}_{k}')
            MASKS.append(dict(row=r_, side=side, sx=side * sx, cup=c_, tube=t_, top=V3(side * (1.2 + 0.08 * (k - 1)), y - 0.5, 1.585), seed=k * 1.7 + r_ * 0.9 + side))
def masks(t, drop_t=None, slow=1.0, mine=None):
    """drop_t: when the doors pop (None = still shut); mine: (cup position, facing dir) for his mask once he holds / wears it"""
    for (side, r_), (dpiv, door) in DOORS.items():
        k = 0.0 if drop_t is None else smooth(0.0, 0.12, (t - drop_t) * slow)
        dpiv.rotation_euler = (0, side * R(-100) * k, 0)
    for m in MASKS:
        cup_, tub = m['cup'], m['tube']; on = drop_t is not None and t >= drop_t
        mine_ = m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01
        on = on and m['row'] != HIDE_ROW[0] and not (HIDE_ROW[0] is not None and m['row'] == MYROW and not mine_); cup_.hide_render = tub.hide_render = not on
        if not on: continue
        tau = (t - drop_t) * slow
        fall = min(1.0, 0.5 * 9.8 * tau * tau / 0.42)                    # falls 42 cm, then bounces on the tube and swings
        hang = m['top'] + V3((m['sx'] - m['top'].x) * 0.55, 0.12, -0.42 * fall)
        if fall >= 1.0:
            ts_ = tau - math.sqrt(2 * 0.42 / 9.8); d = math.exp(-1.6 * ts_)
            hang = hang + V3(0.05 * math.sin(4.5 * ts_ + m['seed']) * d, 0.06 * math.sin(3.7 * ts_ + m['seed'] * 2) * d, 0.05 * math.cos(9 * ts_) * d * abs(math.sin(9 * ts_)))
        face = V3(0, 0.55, -0.8)
        if mine is not None and m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01: hang, face = Vector(mine[0]), Vector(mine[1])
        cup_.location = hang; cup_.rotation_quaternion = (-face).to_track_quat('-Z', 'Y') if False else face.to_track_quat('Z', 'Y')
        top = m['top']; mid = top.lerp(hang, 0.5) + V3(0, 0.03, -0.05); pts = [top, top.lerp(mid, 0.6), mid.lerp(hang, 0.6), hang + face * 0.0]
        for i, p in enumerate(pts): tub.data.splines[0].points[i].co = (p.x, p.y, p.z, 1.0)
HIDE_ROW = [None]
MASK_OBJS = [m['cup'] for m in MASKS] + [m['tube'] for m in MASKS]
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
# ================================================================ FOG (a volume filling the cabin, thick for a few seconds after the blowout)
FOG_M = bpy.data.materials.new('fog'); FOG_M.use_nodes = True; _nt = FOG_M.node_tree; _nt.nodes.remove(_nt.nodes['Principled BSDF'])
_pv = _nt.nodes.new('ShaderNodeVolumePrincipled'); _pv.inputs['Color'].default_value = (0.92, 0.95, 1.0, 1)
_fz = _nt.nodes.new('ShaderNodeTexNoise'); _fz.inputs['Scale'].default_value = 1.6; _fz.inputs['Detail'].default_value = 3; _fz.noise_dimensions = '4D'
_ftc = _nt.nodes.new('ShaderNodeTexCoord'); _nt.links.new(_ftc.outputs['Object'], _fz.inputs['Vector']); _nt.links.new(objattr(_nt, 'tt'), _fz.inputs['W'])
_den = math_(_nt, 'MULTIPLY', objattr(_nt, 'dens'), math_(_nt, 'POWER', _fz.outputs['Fac'], 2.5))
_nt.links.new(math_(_nt, 'MULTIPLY', _den, 1.6), _pv.inputs['Density']); _nt.links.new(_pv.outputs['Volume'], _nt.nodes['Material Output'].inputs['Volume'])
FOG = box('fog', (3.6, Y1C - Y0C - 0.2, 2.3), (0, 0, 1.15), FOG_M); FOG.visible_shadow = False; FOG['dens'] = 0.0; FOG['tt'] = 0.0
C.volume_bounces = 0; S.cycles.volume_step_rate = 4.0
CABIN.append(FOG)
# ================================================================ MODES
MAN = [BODY, SUIT, HAIR] + HEADBITS
FLYW, FLYP = FLY_W.objs, FLY_P.objs + FLY_S.objs
def mode(which):
    """cabin / xray / out (the jet over the clouds) / road (the phone)"""
    for o in CABIN + JETP + ROADSIDE + [CLOUDS] + XRAY_OBJS: o.hide_render = True
    for lt in CAB_L + [XL, XL2]: lt.hide_render = True
    SUN_O.hide_render = False; world('sky'); PLUG_BO.show_render = False; HOLE.hide_render = True
    for i, sl in enumerate(BODY.material_slots): sl.material = BODY_MATS[i]
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = True
    PUFF.strength = 0.0
    for o in MAN: o.hide_render = which not in ('cabin', 'xray')
    if which == 'cabin':
        for o in CABIN + [CLOUDS]: o.hide_render = False
        for lt in CAB_L: lt.hide_render = False
        FOG.hide_render = FOG['dens'] <= 0.001
    elif which == 'xray':
        for o in [SUIT, HAIR] + HEADBITS: o.hide_render = True
        for i, sl in enumerate(BODY.material_slots): sl.material = XSKIN
        for md in BODY.modifiers:
            if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = False
        PUFF.strength = 0.004
        for o in XRAY_OBJS: o.hide_render = False
        XL.hide_render = XL2.hide_render = False; SUN_O.hide_render = True; world('xray')
    elif which == 'out':
        for o in JETP + [CLOUDS]: o.hide_render = False
        HOLE.hide_render = True
    elif which == 'road':
        for o in ROADSIDE: o.hide_render = False
# ================================================================ HIS HEAD: points on his face follow the head bone
def head_pt(p_rest):
    """a point given in his rest (armature) space near the head -> world, as the head bone moves it"""
    pb = PB['head']; return RIG.matrix_world @ (pb.matrix @ RB['head'].matrix_local.inverted() @ Vector(p_rest))
MOUTH_R = V3(0.0, -0.165, 1.475); FACE_R = V3(0.0, -0.14, 1.53)
def head_dir(d_rest):
    pb = PB['head']; return (RIG.matrix_world.to_3x3() @ (pb.matrix.to_3x3() @ RB['head'].matrix_local.to_3x3().inverted() @ Vector(d_rest))).normalized()
# ================================================================ THE BLOWOUT (shared by the first beat and the end of the last: the loop)
CAM0_P = V3(MYSEAT_X - 0.62, MY - 0.78, 1.32); CAM0_T = V3(MYSEAT_X + 0.28, MY + 0.08, 1.1)
def blow_state(tb, t):
    """tb = time since the window went (s, may be < 0 = still shut)"""
    k = smooth(0.0, 0.35, tb)
    d = 0.0 if tb <= 0 else 3.0 * tb + 30.0 * tb * tb
    BLOWG.location = (d, -0.4 * d, 0.05 * d); BLOWG.rotation_euler = (3.0 * d, 1.2 * d, 0.0); BLOWG.hide_render = d > 3.0
    MYPANE.hide_render = tb > 0.0
    BLOWP.location = V3(0.004, 0, 0) * math.sin(tb * 70) * k
    FOG['dens'] = 0.55 * smooth(0.0, 0.5, tb) * (1 - 0.6 * smooth(2.0, 6.0, tb)); FOG['tt'] = t * 0.6 + 2.0 * tb
    FLY_W.at(tb, H_WIN, V3(1, 0.6, -0.1), on=True)
    # him: flinches away from the hole, then grabs the armrest, hair pushed
    seated(t, lean=lerp(-8, -2, k), handR=V3(-0.17, -0.36, 0.98).lerp(V3(-0.22, -0.2, 0.86), k), handL=V3(0.17, -0.36, 0.98).lerp(V3(0.05, -0.32, 1.52), k),
           neck=lerp(0, 8, k), head=lerp(0, 4, k), head_yaw=lerp(0, -28, k), lids=lerp(0.05, 0.0, k), jaw=lerp(0.0, 0.55, k), curl=(0.35 + 0.4 * k, 0.35 + 0.3 * k),
           side_lean=lerp(0, -6, k), bob=k)
    return k
def cam_blow(tb, t):
    k = smooth(0.0, 0.5, tb)
    look(CAM0_P + V3(0.06, 0.1, 0.0) * k + shake(t, 0.006 + 0.03 * k), CAM0_T + V3(0.05, 0, 0.05) * k, 20, 4.0, focus=H_WIN.lerp(head_pt(FACE_R), 0.4))
TB0 = 0.04                                                               # frame one is this far into the blowout
SIT_AISLE = (-0.52, ROW_Y[PLUG_ROW])                                    # beats 9-10: he is the aisle seat of the door-plug row
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    S.view_settings.exposure = 0.0; FOG['dens'] = 0.0; HIDE_ROW[0] = None; masks(t, None); sun_from((0.75, -0.25, 0.45)); JET.location = PX; JET.rotation_euler = (0, 0, 0)
    PLUGE.location = (-2.0, PLUGE_Y, PLUGE_Z); PLUGE.rotation_euler = (0, 0, 0); FLY_P.at(-5, H_PLUG, V3(-1, 0.6, 0), on=False); FLY_W.at(-5, H_WIN, V3(1, 0, 0), on=False); FLY_S.at(-5, H_PLUG, V3(-1, 0.6, 0), on=False)
    BLOWG.location = (0, 0, 0); BLOWG.rotation_euler = (0, 0, 0); BLOWG.hide_render = False; MYPANE.hide_render = False
    if nb == 0:                                                          # the window goes (frame one already moving)
        tb = t + TB0; blow_state(tb, t); mode('cabin'); cam_blow(tb, t)
    elif nb == 1:                                                        # air rushes for the hole, the cabin fogs: down the aisle
        tb = t + TB0; blow_state(tb, t); mode('cabin')
        look(V3(0.12, MY - 3.4, 1.55).lerp(V3(0.2, MY - 2.7, 1.5), u) + shake(t, 0.015), V3(1.15, MY - 0.2, 1.0), 24, 5.6, focus=V3(1.2, MY, 1.0))
    elif nb == 2:                                                        # fifteen seconds: close on his face, fog drifting
        tb = t + TB0; blow_state(tb, t); mode('cabin')
        seated(t, lean=-4, handL=V3(0.2, -0.33, 1.05), handR=V3(-0.2, -0.33, 1.0), neck=5, head=2, head_yaw=-10 + 14 * sm(u), jaw=0.25, lids=0.1, side_lean=-3)
        fp = head_pt(FACE_R); look(fp + V3(-0.45, -0.62, -0.02).lerp(V3(-0.38, -0.5, 0.0), u) + shake(t, 0.004), fp + V3(0.02, 0, -0.03), 42, 2.8, focus=fp)
    elif nb == 3:                                                        # low oxygen feels good: x-ray, his lungs go from pink to blue, head lolls
        ts = B[3] + lt * 0.6; seated(ts, lean=-10, neck=lerp(4, 18, sm(u)), head=lerp(0, 8, u), head_yaw=lerp(4, 14, u) + 8 * wob(ts, 0.6, 2), lids=lerp(0.15, 0.55, u), jaw=0.12)
        mode('xray'); lungs(ts, oxy=lerp(1.0, 0.1, smooth(0.05, 0.9, u)), rate=0.35, depth=1.2)
        c_ = RIG.matrix_world @ V3(0, 0, 1.3); a_ = R(-35 + 30 * u)
        look(c_ + V3(1.05 * math.sin(a_), -1.05 * math.cos(a_), 0.12), c_ + V3(0, 0, 0.02), 38, 5.6, focus=c_)
        S.view_settings.exposure = 0.3
    elif nb == 4:                                                        # the masks drop; he grabs his and puts it on
        tb = t + TB0; blow_state(tb, t); mode('cabin'); FOG['dens'] *= 0.6
        dt_ = B[4] + 0.15; g = smooth(0.5, 0.75, u); w = smooth(0.75, 0.95, u)
        seated(t, lean=-4, neck=5, head_yaw=-6 * (1 - g), jaw=0.3 * (1 - w))
        mp = head_pt(MOUTH_R); fd = head_dir(V3(0, -1, 0))
        hang = None
        for m in MASKS:
            if m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01: m_my = m
        masks(t, dt_)
        hang = Vector(m_my['cup'].location)
        if g > 0:
            cpos = hang.lerp(mp + fd * 0.05, w); masks(t, dt_, mine=(cpos, V3(0, 1, 0.15).lerp(-fd, w)))
            Mi = rigM(SEAT_HIP, (-4, 0, 0)).inverted()
            hr = Vector(m_my['cup'].location) + V3(-0.04, -0.05, -0.03)
            seated(t, lean=-4, neck=5, head_yaw=-6 * (1 - g), jaw=0.3 * (1 - w), handR=V3(-0.17, -0.36, 0.98).lerp(Mi @ hr, g), curl=(0.35 + 0.4 * g, 0.35))
            if g > 0.98: place_hand('R', cpos + fd * 0.012, V3(0.2, 0, 1), -fd, 1.0); bpy.context.view_layer.update()
        look(V3(0.15, MY - 1.6, 1.5).lerp(V3(0.35, MY - 1.2, 1.4), u) + shake(t, 0.008), V3(1.25, MY - 0.15, 1.3), 24, 4.0, focus=V3(1.3, MY - 0.2, 1.3))
    elif nb == 5:                                                        # the pilots dive: the jet noses down toward the clouds
        mode('out'); dz = -80 * sm(u); JET.location = PX + V3(0, -40 * u, dz); JET.rotation_euler = (R(-11 * smooth(0, 0.3, u)), R(4), 0); bpy.context.view_layer.update()
        c_ = JET.location; look(c_ + V3(-30, -34, 9) + V3(3, 6, -3) * u, c_ + V3(0, -2, -1), 32, 22.0); sun_from((0.6, -0.5, 0.55))
    elif nb == 6:                                                        # the mask: at least twelve minutes, he breathes slow
        mode('cabin'); masks(t, B[4] + 0.15 - 20); HIDE_ROW[0] = MYROW - 1
        seated(t, lean=-6, neck=2, head=0, head_yaw=-4, lids=0.1)
        mp = head_pt(MOUTH_R); fd = head_dir(V3(0, -1, 0))
        for m in MASKS:
            if m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01: m_my = m
        cpos = mp + fd * (0.05 + 0.003 * math.sin(t * 2.5)); masks(t, B[4] + 0.15 - 20, mine=(cpos, -fd))
        Mi = rigM(SEAT_HIP, (-6, 0, 0)).inverted(); hr = Vector(m_my['cup'].location) + V3(-0.04, -0.05, -0.03)
        seated(t, lean=-6, neck=2, head_yaw=-4, lids=0.1, handR=Mi @ hr, curl=(0.75, 0.35)); place_hand('R', cpos + fd * 0.012, V3(0.2, 0, 1), -fd, 1.0); bpy.context.view_layer.update()
        fp = head_pt(FACE_R); look(fp + V3(-0.75, -0.95, 0.02).lerp(V3(-0.62, -0.8, 0.0), u), fp + V3(0.05, 0, -0.1), 38, 4.0, focus=fp)
    elif nb == 7:                                                        # 2024, Alaska Airlines: low sun, climbing out
        mode('out'); JET.location = PX + V3(0, -30 * u, 8 * u); JET.rotation_euler = (R(7), R(-3), 0); bpy.context.view_layer.update(); sun_from((-0.7, 0.4, 0.18), 3.5, (1.0, 0.72, 0.45))
        c_ = JET.location; look(c_ + V3(-40, -46, -5).lerp(V3(-35, -40, -4), u), c_ + V3(0, 2, 1), 30, 22.0)
    elif nb == 8:                                                        # the door plug blows out (slow motion)
        mode('out'); sun_from((-0.7, 0.4, 0.18), 3.5, (1.0, 0.72, 0.45)); JET.rotation_euler = (R(7), R(-3), 0); bpy.context.view_layer.update()
        ts = lt * 0.35; v = max(0.0, ts - 0.12); HOLE.hide_render = v <= 0
        PLUGE.location = V3(-2.0, PLUGE_Y, PLUGE_Z) + V3(-6 * v - 30 * v * v, 14 * v * v + 3 * v, 2 * v); PLUGE.rotation_euler = (R(40) * v * 3, R(-90) * v * 2, R(25) * v * 4)
        Mj = JET.matrix_world; pw = Mj @ V3(-1.975, PLUGE_Y, PLUGE_Z); cpl = Mj @ (V3(-12.0, PLUGE_Y + 3.2, 1.3).lerp(V3(-10.5, PLUGE_Y + 2.6, 1.1), u))
        look(cpl + shake(t, 0.03), Mj @ V3(-2.0, PLUGE_Y - 0.6, PLUGE_Z + 0.1), 40, 11.0, focus=pw)
    elif nb == 9:                                                        # the seats beside it were empty (he is on the aisle)
        mode('cabin'); PLUG_BO.show_render = True; PANES[len(ROW_Y) + PLUG_ROW].hide_render = True
        FOG['dens'] = 0.12; FOG['tt'] = t; FOG.hide_render = False
        seated(t, lean=-3, at=SIT_AISLE, head_yaw=30, neck=6, jaw=0.4, handL=V3(0.2, -0.3, 0.9), handR=V3(-0.25, -0.15, 0.9), side_lean=4, bob=1.0)
        FLY_P.at(lt + 0.6, H_PLUG, V3(-1, 0.7, 0));
        look(V3(0.35, ROW_Y[PLUG_ROW] - 1.9, 1.45).lerp(V3(0.3, ROW_Y[PLUG_ROW] - 1.6, 1.4), u) + shake(t, 0.01), V3(-1.2, ROW_Y[PLUG_ROW] - 0.1, 0.85), 24, 5.6)
    elif nb == 10:                                                       # a shirt and phones out the hole (slow motion)
        mode('cabin'); PLUG_BO.show_render = True; PANES[len(ROW_Y) + PLUG_ROW].hide_render = True
        FOG['dens'] = 0.1; FOG['tt'] = t; FOG.hide_render = False; ts = lt * 0.45
        seated(t, lean=-3, at=SIT_AISLE, head_yaw=40, neck=8, jaw=0.5, handL=V3(0.1, -0.35, 1.45), handR=V3(-0.25, -0.15, 0.9), side_lean=6, bob=1.0)
        FLY_P.at(ts + 1.0, H_PLUG, V3(-1, 0.7, 0)); FLY_S.at(ts + 0.1, H_PLUG, V3(-1, 0.8, 0.1)); shirt_wave(ts)
        look(V3(-0.2, ROW_Y[PLUG_ROW] - 1.2, 1.25) + shake(t, 0.006), H_PLUG + V3(0.3, 0.1, 0.1), 26, 5.6, focus=H_PLUG)
    elif nb in (11, 12):                                                 # a phone by the road, still working
        mode('road'); S.view_settings.exposure = 0.5; sun_from((0.4, -0.6, 0.5), 3.5, (1.0, 0.9, 0.75)); u2 = (t - B[11]) / (DUR[11] + DUR[12])
        look(PHONE_AT + V3(-0.5, -0.65, 0.6).lerp(V3(-0.22, -0.3, 0.32), sm(u2)), PHONE_AT + V3(0, 0, 0.0), 40, 4.0, focus=PHONE_AT)
    else:                                                                # back in his seat, calm; the camera settles where it starts; the window goes (= frame one)
        tb = t - TOTAL + TB0; blow_state(tb, t); mode('cabin')
        if tb < 0:
            k = smooth(0.0, 0.85, u)
            seated(t, lean=-8, head_yaw=lerp(-20, 0, smooth(0, 0.6, u)), neck=lerp(-2, 0, u), lids=0.05)
            look(CAM0_P + V3(-0.3, 0.35, 0.15) * (1 - k) + shake(t, 0.004), CAM0_T + V3(-0.2, 0.0, 0.2) * (1 - k), lerp(26, 20, k), 4.0,
                 focus=H_WIN.lerp(head_pt(FACE_R), 0.4))
        else: cam_blow(tb, t)
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

