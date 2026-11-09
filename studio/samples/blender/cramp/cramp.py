# Charley horse (a calf cramp at night), built and rendered in Blender (Cycles): a man asleep with his toes pointed; his calf locks up;
# the real calf anatomy (Z-Anatomy atlas, CC BY-SA 4.0, from BodyParts3D) fitted inside him: gastrocnemius (two heads), soleus,
# plantaris and the Achilles tendon, the tibial nerve with its branches into the calf; a close-up inside the muscle (fibres, motor
# end plates, capillaries): normal signals squeeze and let go, then the end plates fire on their own up to 150 times a second and
# the fibres lock; pulling the toes back stretches the muscle and shuts it off.
#   python3 cramp.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]      (stride.json / redo.json beside it: see ../ele/ele.py)
# Needs man.blend (../foot/man_build.py) and anat.blend (anat_build.py + ../foot/anat_fit.py) beside it or in /root/vt/n42/cramp.
import sys, os, math, json, argparse
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join('/root/vt/n42/cramp', n)) if os.path.exists(p_))
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
# ================================================================ THE BEDROOM (z up, metres; queen bed along y, headboard at +y; he lies head to +y)
WOOD = mat('floor', (0.33, 0.2, 0.11), 0.42, coat=0.25)
def floor_mat():
    m = WOOD; nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 1.4; br.inputs['Row Height'].default_value = 0.16; br.offset = 0.37; br.squash_frequency = 1
    br.inputs['Color1'].default_value = (0.36, 0.22, 0.12, 1); br.inputs['Color2'].default_value = (0.27, 0.16, 0.085, 1); br.inputs['Mortar'].default_value = (0.08, 0.05, 0.03, 1)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 6.0; wv.inputs['Distortion'].default_value = 9.0; wv.inputs['Detail'].default_value = 4
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 12.0, 1.0); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.35
    nt.links.new(br.outputs['Color'], mx.inputs['A']); nt.links.new(wv.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    return m
floor_mat()
FLOOR = box('floor', (9, 9, 0.02), (0, 0, -0.01), WOOD)
def rug_mat(m, hx, hy, c_in, c_band):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    bx = math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', sx.outputs['X']), hx), math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', sx.outputs['Y']), hy))
    band = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', bx, 0.84), math_(nt, 'LESS_THAN', bx, 0.9))
    edge = math_(nt, 'GREATER_THAN', bx, 0.95)
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*c_in, 1); mx.inputs['B'].default_value = (*c_band, 1)
    nt.links.new(math_(nt, 'MAXIMUM', band, edge), mx.inputs['Factor'])
    old = next(l for l in nt.links if l.to_socket == b.inputs['Base Color']); nz_mix = old.from_node
    nt.links.new(mx.outputs['Result'], nz_mix.inputs['A']); return m
RUG_M = rug_mat(noisy(mat('rug', (0.42, 0.38, 0.34), 0.95, sheen=0.6), 900.0, 0.25, 0.05), 1.3, 1.0, (0.55, 0.5, 0.44), (0.18, 0.22, 0.3))
RUG = box('rug', (2.6, 2.0, 0.012), (0.0, -0.75, 0.006), RUG_M, bv=0.004)
WALL_M = noisy(mat('wall', (0.33, 0.37, 0.42), 0.9), 30.0, 0.04)                       # a muted blue-grey bedroom
TRIM_M = mat('trim', (0.82, 0.8, 0.76), 0.4)
WALLB = box('wall_back', (9, 0.1, 3.0), (0, 1.3, 1.5), WALL_M)
# side wall with a window opening (y -0.55..0.45, z 0.95..2.05): four pieces so the moonlight really comes through
WX = -1.85; WY0, WY1, WZ0, WZ1 = -0.55, 0.45, 0.95, 2.05
WALLS = [box('wall_s_lo', (0.1, 9, WZ0), (WX, 0, WZ0 / 2), WALL_M), box('wall_s_hi', (0.1, 9, 3.0 - WZ1), (WX, 0, (3.0 + WZ1) / 2), WALL_M),
         box('wall_s_a', (0.1, 4.5 + WY0, WZ1 - WZ0), (WX, (WY0 - 4.5) / 2, (WZ0 + WZ1) / 2), WALL_M),
         box('wall_s_b', (0.1, 4.5 - WY1, WZ1 - WZ0), (WX, (WY1 + 4.5) / 2, (WZ0 + WZ1) / 2), WALL_M)]
BASEB = [box('base_back', (9, 0.02, 0.1), (0, 1.24, 0.05), TRIM_M), box('base_side', (0.02, 9, 0.1), (WX + 0.06, 0, 0.05), TRIM_M)]
def glass_mat():
    m = bpy.data.materials.new('window_glass'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.02
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.5; mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fr.outputs['Fac'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(gl.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface']); return m
GLASS = box('window_glass', (0.01, WY1 - WY0, WZ1 - WZ0), (WX, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2), glass_mat())
WINF = [box('wf_top', (0.08, WY1 - WY0 + 0.1, 0.05), (WX + 0.02, (WY0 + WY1) / 2, WZ1 + 0.025), TRIM_M),
        box('wf_bot', (0.16, WY1 - WY0 + 0.14, 0.04), (WX + 0.06, (WY0 + WY1) / 2, WZ0 - 0.02), TRIM_M),
        box('wf_l', (0.08, 0.05, WZ1 - WZ0), (WX + 0.02, WY0 - 0.025, (WZ0 + WZ1) / 2), TRIM_M),
        box('wf_r', (0.08, 0.05, WZ1 - WZ0), (WX + 0.02, WY1 + 0.025, (WZ0 + WZ1) / 2), TRIM_M),
        box('wf_mid', (0.05, 0.03, WZ1 - WZ0), (WX + 0.01, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2), TRIM_M),           # mullions: the moonlight
        box('wf_mid2', (0.05, WY1 - WY0, 0.03), (WX + 0.01, (WY0 + WY1) / 2, WZ0 + (WZ1 - WZ0) * 0.55), TRIM_M)]  # falls on the bed in panes
def night_mat():
    m = bpy.data.materials.new('night_sky'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sx.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.01, 0.015, 0.035, 1); cr.color_ramp.elements[1].color = (0.05, 0.09, 0.2, 1)
    nt.links.new(sx.outputs['Z'], cr.inputs['Fac'])
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 90.0; nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
    star = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', vor.outputs['Distance'], 0.03), 3.0)
    em = nt.nodes.new('ShaderNodeEmission'); ad = nt.nodes.new('ShaderNodeMix'); ad.data_type = 'RGBA'; ad.blend_type = 'ADD'; ad.inputs['Factor'].default_value = 1.0
    nt.links.new(cr.outputs['Color'], ad.inputs['A']); cb = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(star, cb.inputs[i]) for i in range(3)]
    nt.links.new(cb.outputs['Color'], ad.inputs['B']); nt.links.new(ad.outputs['Result'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m
SKY = box('night', (0.02, 6.0, 4.0), (WX - 1.6, 0.0, 1.6), night_mat())
SKY.visible_shadow = False
CURT_M = noisy(mat('curtain', (0.2, 0.24, 0.32), 0.9, sheen=0.6), 200.0, 0.1)
def curtain(name, y0, w):
    vs, fs = [], []; nx, nz = 28, 18
    for j in range(nz + 1):
        for i in range(nx + 1):
            yy = y0 + i / nx * w; vs.append((WX + 0.1 + 0.03 * math.sin(i / nx * math.pi * 8), yy, 0.4 + j / nz * 2.2))
    for j in range(nz):
        for i in range(nx): fs.append((j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i))
    return mesh(name, vs, fs, CURT_M)
CURTS = [curtain('curtA', WY0 - 0.5, 0.42), curtain('curtB', WY1 + 0.08, 0.42)]
ROD = prim('cylinder', 'curtain_rod', mat('rod', (0.05, 0.05, 0.05), 0.3, metal=0.8), loc=(WX + 0.12, (WY0 + WY1) / 2, 2.62), rot=(R(90), 0, 0), vertices=12, radius=0.012, depth=2.0)
# ---- the bed: upholstered base and headboard, mattress, a quilted duvet that dents under him, pillows
BED_HW, BED_Y0, BED_Y1 = 0.76, -1.0, 1.0                 # mattress half width, foot end, head end
MAT_TOP, DUVET_TOP = 0.56, 0.60
UPH_M = noisy(mat('upholstery', (0.16, 0.19, 0.26), 0.88, sheen=0.9), 900.0, 0.18, 0.05)
N(UPH_M)['Principled BSDF'].inputs['Sheen Tint'].default_value = (0.6, 0.65, 0.8, 1)
LEGW_M = mat('bed_leg', (0.1, 0.06, 0.035), 0.35)
BED = [box('bed_base', (1.66, 2.12, 0.2), (0, -0.02, 0.21), UPH_M, bv=0.03, ss=1),
       box('headboard', (1.72, 0.1, 1.02), (0, 1.12, 0.83), UPH_M, bv=0.05, ss=2)]
for sx in (-1, 1):
    for sy in (-1, 1): BED.append(prim('cylinder', 'bed_leg', LEGW_M, loc=(sx * 0.76, -0.02 + sy * 0.98, 0.055), vertices=16, radius=0.03, depth=0.11))
BUTTON_M = mat('button', (0.12, 0.14, 0.2), 0.6, sheen=0.5)
for r_ in range(3):
    for c_ in range(7):
        xx = -0.72 + c_ * 0.24 + (0.12 if r_ % 2 else 0.0)
        if abs(xx) < 0.8: BED.append(prim('uv_sphere', 'tuft', BUTTON_M, loc=(xx, 1.066, 0.92 + r_ * 0.16), segments=12, ring_count=6, radius=0.011, scale=(1, 0.5, 1)))
MATT = box('mattress', (1.52, 2.0, 0.25), (0, 0.0, 0.435), noisy(mat('mattress', (0.85, 0.85, 0.83), 0.9), 400.0, 0.06), bv=0.05, ss=2)
BED.append(MATT)
# the duvet: one grid over the top that drapes down the sides and the foot end (rounded edge, folds in the skirt); quilted squares
DUV_M = noisy(mat('duvet', (0.42, 0.47, 0.55), 0.86, sheen=0.85), 1400.0, 0.08, 0.04)
N(DUV_M)['Principled BSDF'].inputs['Sheen Tint'].default_value = (0.85, 0.9, 1.0, 1)
import numpy as np
DX = 0.012
DXS = np.arange(-1.08, 1.08 + 1e-6, DX); DYS = np.arange(-1.32, 1.0 + 1e-6, DX); DNX, DNY = len(DXS), len(DYS)
def duvet_mesh():
    vs = []; top = []; r_ = 0.045
    for j, y in enumerate(DYS):
        for i, x in enumerate(DXS):
            dx = max(0.0, abs(x) - BED_HW); dy = max(0.0, BED_Y0 - y); d = math.hypot(dx, dy)
            q = (1 - abs(math.cos(math.pi * x / 0.38)) ** 10) * (1 - abs(math.cos(math.pi * (y + 0.1) / 0.38)) ** 10)     # quilt squares
            puff = 0.012 * q ** 0.35 - 0.006 + 0.004 * mnoise.noise(Vector((x * 2.1, y * 2.1, 0.3)))
            if d < 1e-9:
                vs.append((x, y, DUVET_TOP + puff)); top.append(True); continue
            ex = math.copysign(BED_HW, x) if dx > 0 else x; ey = BED_Y0 if dy > 0 else y
            nx_, ny_ = (math.copysign(dx, x) / d, -dy / d)
            if d <= r_ * math.pi / 2: th = d / r_; off = r_ * math.sin(th); z = DUVET_TOP + puff * (1 - th / 1.6) - r_ + r_ * math.cos(th)
            else:
                off = r_; z = DUVET_TOP - r_ - (d - r_ * math.pi / 2)
                k_ = min(1.0, (d - r_ * math.pi / 2) / 0.08); along = y if dx > 0 else x
                off += k_ * (0.012 * math.sin(along / 0.23 * 2 * math.pi + 0.7) + 0.006 * math.sin(along / 0.09 * 2 * math.pi))    # folds
            vs.append((ex + nx_ * off, ey + ny_ * off, z)); top.append(False)
    fs = [(j * DNX + i, j * DNX + i + 1, (j + 1) * DNX + i + 1, (j + 1) * DNX + i) for j in range(DNY - 1) for i in range(DNX - 1)]
    return vs, fs, np.array(top)
_dv, _df, DUV_TOP_MASK = duvet_mesh()
DUVET = mesh('duvet', _dv, _df, DUV_M)
_sol = DUVET.modifiers.new('thick', 'SOLIDIFY'); _sol.thickness = 0.008; _sol.offset = -1.0
subsurf(DUVET, 1)
DUV_REST = np.array(_dv, dtype=np.float64)
BED.append(DUVET)
# pillows: rounded super-ellipsoids sitting on the duvet; their tops dent under his head
PIL_M = noisy(mat('pillow', (0.66, 0.68, 0.72), 0.85, sheen=0.8), 1200.0, 0.06, 0.04)
def pillow(name, c, hx, hy, hz, rot_z=0.0, m=PIL_M, tilt=0.0):
    def S_(v, e): return math.copysign(abs(v) ** e, v)
    vs, fs = [], []; nu, nv = 64, 28
    for j in range(nv + 1):
        vv = -math.pi / 2 + math.pi * j / nv
        for i in range(nu):
            uu = 2 * math.pi * i / nu
            x = hx * S_(math.cos(vv), 0.55) * S_(math.cos(uu), 0.25); y = hy * S_(math.cos(vv), 0.55) * S_(math.sin(uu), 0.25); z = hz * S_(math.sin(vv), 0.7)
            x *= 1 - 0.06 * (1 - abs(S_(math.cos(uu), 0.25))) ; vs.append((x, y, z))
    for j in range(nv):
        for i in range(nu): fs.append((j * nu + i, j * nu + (i + 1) % nu, (j + 1) * nu + (i + 1) % nu, (j + 1) * nu + i))
    o = mesh(name, vs, fs, m); o.location = c; o.rotation_euler = (tilt, 0, rot_z); subsurf(o, 1); return o
PIL_H = 0.055
X_MID = -0.12; Y_HIP = 0.14                                   # his midline (x) and his hips (y) when he lies on his back
PILLOW = pillow('pillow_his', (X_MID - 0.02, 0.76, DUVET_TOP + PIL_H - 0.012), 0.34, 0.23, PIL_H, R(2))
PILLOW2 = pillow('pillow_2', (0.42, 0.78, DUVET_TOP + PIL_H - 0.012), 0.34, 0.23, PIL_H, R(-3))
EURO = pillow('pillow_euro', (0.18, 1.0, DUVET_TOP + 0.2), 0.36, 0.08, 0.22, R(0), noisy(mat('euro', (0.2, 0.26, 0.38), 0.9, sheen=0.8), 800.0, 0.12), tilt=R(-14))
PIL_REST = {o.name: np.array([v.co[:] for v in o.data.vertices]) for o in (PILLOW,)}
BED += [PILLOW, PILLOW2, EURO]
# ---- nightstand on his right (x-): lamp (on, low), clock reading 3:07, a glass of water, a phone face down, a book
NS_X, NS_Y = -1.12, 0.84
NS_M = noisy(mat('nightstand', (0.2, 0.12, 0.065), 0.4, coat=0.3), 25.0, 0.18)
NSTAND = [box('ns_body', (0.5, 0.42, 0.56), (NS_X, NS_Y, 0.28), NS_M, bv=0.01),
          box('ns_drawer_line', (0.46, 0.004, 0.006), (NS_X, NS_Y - 0.211, 0.38), mat('seam', (0.02, 0.012, 0.008), 0.6)),
          prim('uv_sphere', 'ns_knob', mat('knob', (0.6, 0.5, 0.3), 0.25, metal=0.9), loc=(NS_X, NS_Y - 0.215, 0.46), segments=16, ring_count=8, radius=0.014)]
NS_TOP = 0.56
LAMP_M = mat('lamp_ceramic', (0.75, 0.72, 0.66), 0.25, coat=0.6)
SHADE_M = mat('shade', (0.92, 0.86, 0.72), 0.8, trans=0.35, emit=(1.0, 0.7, 0.42), estr=1.2)
NSTAND += [lathe('lamp_base', [(0.0, 0.0), (0.07, 0.0), (0.085, 0.04), (0.09, 0.12), (0.06, 0.22), (0.025, 0.27), (0.012, 0.36), (0.0, 0.36)], 40, LAMP_M, loc=(NS_X + 0.1, NS_Y + 0.08, NS_TOP)),
           lathe('lamp_shade', [(0.17, 0.3), (0.11, 0.5)], 48, SHADE_M, loc=(NS_X + 0.1, NS_Y + 0.08, NS_TOP))]
CLK = box('clock', (0.15, 0.07, 0.075), (NS_X - 0.1, NS_Y - 0.08, NS_TOP + 0.0375), mat('clock_body', (0.02, 0.02, 0.022), 0.35), bv=0.01)
CLK.rotation_euler = (0, 0, R(-35))
_ct = bpy.data.curves.new('clock_digits', 'FONT'); _ct.body = '3:07'; _ct.size = 0.05; _ct.align_x = 'CENTER'; _ct.align_y = 'CENTER'; _ct.extrude = 0.0005
CLKT = bpy.data.objects.new('clock_digits', _ct); S.collection.objects.link(CLKT); CLKT.parent = CLK; CLKT.location = (0, -0.0362, 0.004); CLKT.rotation_euler = (R(90), 0, 0)
CLKT.data.materials.append(emis('digits', (1.0, 0.08, 0.04), 6.0))
GLASS_W = lathe('water_glass', [(0.0, 0.0), (0.034, 0.0), (0.037, 0.12), (0.035, 0.12), (0.032, 0.004), (0.0, 0.004)], 40, mat('glass', (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=1.5), loc=(NS_X + 0.16, NS_Y - 0.12, NS_TOP))
WATER = lathe('water', [(0.0, 0.004), (0.031, 0.004), (0.033, 0.07), (0.0, 0.07)], 40, mat('water', (0.85, 0.92, 1.0), 0.0, trans=1.0, ior=1.33), loc=(NS_X + 0.16, NS_Y - 0.12, NS_TOP))
PHONE = box('phone', (0.075, 0.155, 0.009), (NS_X - 0.12, NS_Y + 0.08, NS_TOP + 0.0045), mat('phone', (0.03, 0.03, 0.035), 0.3), bv=0.004); PHONE.rotation_euler = (0, 0, R(12))
BOOK = box('book', (0.15, 0.22, 0.03), (NS_X - 0.04, NS_Y + 0.1, NS_TOP + 0.015), noisy(mat('book', (0.45, 0.12, 0.08), 0.6), 300.0, 0.15), bv=0.003); BOOK.rotation_euler = (0, 0, R(-8))
NSTAND += [CLK, CLKT, GLASS_W, WATER, PHONE, BOOK]
# art over the bed, slippers on the rug
ART = [box('art_frame', (0.9, 0.03, 0.62), (0.0, 1.27, 1.78), mat('art_frame', (0.05, 0.04, 0.035), 0.4), bv=0.004)]
def art_mat():
    m = bpy.data.materials.new('art'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = 0.7
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 1.6; wv.inputs['Distortion'].default_value = 4.0
    nt.links.new(tc.outputs['Generated'], wv.inputs['Vector']); cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].color = (0.08, 0.14, 0.25, 1); cr.color_ramp.elements[1].color = (0.75, 0.55, 0.32, 1)
    nt.links.new(wv.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color']); return m
ART.append(box('art', (0.82, 0.005, 0.54), (0.0, 1.254, 1.78), art_mat()))
SLIP_M = noisy(mat('slipper', (0.3, 0.28, 0.26), 0.95, sheen=0.7), 900.0, 0.2)
SLIPS = [box('slipper%d' % k, (0.1, 0.27, 0.05), (-0.98 + 0.13 * k, -0.35 + 0.03 * k, 0.037), SLIP_M, bv=0.025, ss=1) for k in range(2)]
for k_, s_ in enumerate(SLIPS): s_.rotation_euler = (0, 0, R(-10 + 14 * k_))
# ---- light: moonlight through the window (cool key, the panes fall on the bed), the lamp low and warm, a soft fill
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
MOON = light_at('moon', 'AREA', (WX - 1.4, 0.25, 2.9), (-0.1, -0.35, 0.6), 380, (0.6, 0.72, 1.0), 0.35)
LAMP_L = light_at('lamp_light', 'POINT', (NS_X + 0.1, NS_Y + 0.08, NS_TOP + 0.4), (0, 0, 0), 45, (1.0, 0.68, 0.4), 0.08)
FILL = light_at('fill', 'AREA', (-0.6, -2.6, 2.3), (0, -0.2, 0.7), 90, (0.55, 0.65, 0.95), 2.5)
ROOM = [FLOOR, RUG, WALLB, GLASS, SKY, ROD] + WALLS + BASEB + WINF + CURTS + BED + NSTAND + ART + SLIPS
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.008, 0.012, 0.028, 1); WBG.inputs['Strength'].default_value = 1.0
XL = light_at('xray_key', 'AREA', (-0.9, -0.9, 1.6), (X_MID, -0.3, 0.6), 35, (0.85, 0.9, 1.0), 1.5); XL.hide_render = True
XL2 = light_at('xray_rim', 'AREA', (0.6, 0.3, 0.2), (X_MID, -0.3, 0.6), 25, (0.7, 0.8, 1.0), 1.2); XL2.hide_render = True
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.005

# ================================================================ THE MAN (MakeHuman, foot/man_build.py): t-shirt, sleep shorts, barefoot
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HAIR = bpy.data.objects['Human.short02']; HEADBITS = [o for o in bpy.data.objects if o.name.startswith('Human.') and o not in (BODY, SUIT, RIG)]
RB = RIG.data.bones; PB = RIG.pose.bones
KNEE_Z = RB['lowerleg01.R'].head_local.z
bm_ = bmesh.new(); bm_.from_mesh(SUIT.data)
kill = [f for f in bm_.faces if min(v.co.z for v in f.verts) < KNEE_Z + 0.11]          # sleep shorts: a bit shorter than his day shorts
bmesh.ops.delete(bm_, geom=kill, context='FACES'); bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context='VERTS')
_seen = set()
for f0_ in list(bm_.faces):
    if f0_ in _seen or not f0_.is_valid: continue
    isl, st_ = [], [f0_]; _seen.add(f0_)
    while st_:
        f_ = st_.pop(); isl.append(f_)
        for e_ in f_.edges:
            for g_ in e_.link_faces:
                if g_ not in _seen: _seen.add(g_); st_.append(g_)
    if len(isl) < 60: bmesh.ops.delete(bm_, geom=isl, context='FACES')
bm_.to_mesh(SUIT.data); bm_.free()
_dg = BODY.vertex_groups.get('Delete.male_casualsuit06')
if _dg: _dg.remove([v.index for v in BODY.data.vertices if v.co.z < KNEE_Z + 0.16])
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
retint(SHORTS_M, (0.34, 0.36, 0.42), 0.35, 0.95, 0.6)                # soft grey sleep shorts
retint(SHIRT_M, (0.62, 0.2, 0.16), 0.35, 0.9, 0.5)                   # the same brick-red tee as the foot Short (the channel's guy)
# x-ray look: glass skin; 'knot' (0..1) turns the back of his right calf hot red where the muscle locks; 'tt' time for its flicker
def xray_skin_mat():
    m = bpy.data.materials.new('xskin'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    # back of the right calf (rest space): x < -0.04, 0.14 < z < 0.46, y > -0.03 (his back is +y)
    calf = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', sx.outputs['X'], -0.04), math_(nt, 'GREATER_THAN', sx.outputs['Y'], -0.03))
    zz = math_(nt, 'SUBTRACT', sx.outputs['Z'], 0.33); zw = math_(nt, 'EXPONENT', math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', zz, zz), -90.0))
    calf = math_(nt, 'MULTIPLY', calf, zw)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 60.0
    nt.links.new(rp.outputs['Vector'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 6.0), nz.inputs['W'])
    hot = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', calf, objattr(nt, 'knot')), math_(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 0.8, 0.6))
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.0)
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.inputs['A'].default_value = (0.35, 0.62, 1.0, 1); base.inputs['B'].default_value = (1.0, 0.16, 0.08, 1)
    nt.links.new(math_(nt, 'MINIMUM', hot, 1.0), base.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(base.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 1.1, 0.03), math_(nt, 'MULTIPLY', hot, 0.9)), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 0.55, 0.05), math_(nt, 'MULTIPLY', hot, 0.25)), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
XSKIN = xray_skin_mat()
BODY['knot'] = 0.0; BODY['tt'] = 0.0
BODY_MATS = [sl.material for sl in BODY.material_slots]
PUFF = BODY.modifiers.new('xray_puff', 'DISPLACE'); PUFF.strength = 0.0; PUFF.mid_level = 0.0      # skin 4 mm fuller in x-ray (anatomy stays inside)
bpy.context.view_layer.objects.active = BODY
while BODY.modifiers.find('xray_puff') > BODY.modifiers.find('Armature') + 1: bpy.ops.object.modifier_move_up(modifier='xray_puff')
# the visible knot: a shape key bulging the back of his right calf over the gastrocnemius belly (rest space), up to ~9 mm
_bk = BODY.data.shape_keys.key_blocks
if 'knot' not in _bk:
    KNOT = BODY.shape_key_add(name='knot', from_mix=False); KNOT.value = 0.0
    for v in BODY.data.vertices:
        c = v.co
        if c.x < -0.03 and 0.14 < c.z < 0.5:
            w = math.exp(-((c.z - 0.34) / 0.075) ** 2) * math.exp(-((c.x + 0.155) / 0.06) ** 2) * max(0.0, v.normal.y) ** 1.2
            if w > 1e-3: KNOT.data[v.index].co = c + v.normal * 0.009 * w
KNOT = BODY.data.shape_keys.key_blocks['knot']

# ================================================================ HIS CALF ANATOMY (anat.blend: fitted in his rest space, weighted to his rig)
ANAT = []
with bpy.data.libraries.load(asset('anat.blend'), link=False) as (_s, _d): _d.objects = list(_s.objects)
for o in _d.objects:
    S.collection.objects.link(o); o.parent = RIG; o.matrix_world = Matrix.Identity(4)
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG; md.use_deform_preserve_volume = (o['kind'] != 'bone')
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
def muscle_mat(name, col):
    """red muscle with fibres; 'act' = lit up (working), 'dim' = faded back, 'spark' = cramp flicker (hot spots that jump about), 'tt' time"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.45; b.inputs['Coat Weight'].default_value = 0.3
    rp = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 140.0; wv.inputs['Distortion'].default_value = 3.0; nt.links.new(rp.outputs['Object'], wv.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*col, 1); mx.inputs['B'].default_value = tuple(c * 0.6 for c in col) + (1,)
    nt.links.new(math_(nt, 'MULTIPLY', wv.outputs['Fac'], 0.6), mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 70.0; nz.inputs['Detail'].default_value = 3
    nt.links.new(rp.outputs['Object'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 9.0), nz.inputs['W'])
    spk = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.5), 0.0), 1.4), math_(nt, 'MULTIPLY', objattr(nt, 'spark'), 30.0))
    b.inputs['Emission Color'].default_value = (1.0, 0.25, 0.12, 1)
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', objattr(nt, 'act'), 3.0), spk), b.inputs['Emission Strength'])
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', objattr(nt, 'dim'), 0.85)), b.inputs['Alpha'])
    return m
MUS_M = muscle_mat('muscle', (0.42, 0.12, 0.11)); MUS_KEY = muscle_mat('muscle_key', (0.72, 0.11, 0.08))
def tendon_mat(name):
    m = mat(name, (0.85, 0.82, 0.75), 0.3, coat=0.5); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (1.0, 0.9, 0.6, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'act'), 2.5), b.inputs['Emission Strength'])
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', objattr(nt, 'dim'), 0.85)), b.inputs['Alpha']); return m
TEND_M = tendon_mat('tendon')
def tree_mat(name, col, kind_):
    """nerve or artery: glows; pulses run down 'arc' (m from the hip). Object props: ph (pulse travel, m), glow, pulse (0..1), gap (m between
    pulses), spark (misfiring flicker), tt (time)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'; arc = arc.outputs['Fac']
    rel = math_(nt, 'SUBTRACT', objattr(nt, 'ph'), arc)
    saw = math_(nt, 'FRACT', math_(nt, 'DIVIDE', rel, objattr(nt, 'gap')))
    comet = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, saw), 10.0)
    front = math_(nt, 'GREATER_THAN', rel, 0.0)
    pul = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', comet, front), math_(nt, 'MULTIPLY', objattr(nt, 'pulse'), 9.0))
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '2D'; nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 2
    cmb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', arc, 60.0), cmb.inputs['X']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 14.0), cmb.inputs['Y'])
    nt.links.new(cmb.outputs['Vector'], nz.inputs['Vector'])
    spk = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.55), 0.0), 1.5), math_(nt, 'MULTIPLY', objattr(nt, 'spark'), 120.0))
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.4
    rim = math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.8, 0.6)
    strength = math_(nt, 'ADD', math_(nt, 'ADD', math_(nt, 'MULTIPLY', rim, objattr(nt, 'glow')), pul), spk)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(strength, em.inputs['Strength'])
    dk = nt.nodes.new('ShaderNodeBsdfDiffuse'); dk.inputs['Color'].default_value = (0.25, 0.24, 0.22, 1) if kind_ == 'nerve' else (0.2, 0.03, 0.03, 1)
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(em.outputs['Emission'], ad.inputs[0]); nt.links.new(dk.outputs['BSDF'], ad.inputs[1])
    nt.links.new(ad.outputs['Shader'], out.inputs['Surface']); return m
NERVE_M = tree_mat('nerve', (1.0, 0.82, 0.25), 'nerve'); NERVE_HERO = tree_mat('nerve_hero', (1.0, 0.62, 0.08), 'nerve'); ART_M = tree_mat('artery', (1.0, 0.1, 0.06), 'artery')
PROPS = (('act', 0.0), ('dim', 0.0), ('ph', 0.0), ('glow', 1.0), ('pulse', 0.0), ('gap', 0.16), ('spark', 0.0), ('tt', 0.0))
for o in ANAT:
    k = o['kind']; o.data.materials.clear()
    o.data.materials.append({'bone': BONE_M, 'muscle': MUS_M, 'tendon': TEND_M, 'nerve': NERVE_M, 'artery': ART_M}[k])
    for p_, v in PROPS: o[p_] = v
CALF = [AN[n] for n in ('Medial head of gastrocnemius', 'Lateral head of gastrocnemius', 'Soleus muscle', 'Plantaris muscle')]
for o in CALF: o.data.materials[0] = MUS_KEY
ACH = AN['Calcaneal tendon']
NERVES = kind('nerve'); ARTS = kind('artery'); BONES = kind('bone'); MUSCLES = kind('muscle'); TENDONS = kind('tendon')
TIB = AN['Tibial nerve']
HERO_N = [AN[n] for n in ('Sciatic nerve', 'Tibial nerve', 'Medial plantar nerve', 'Lateral plantar nerve') if n in AN]
for o in HERO_N: o.data.materials[0] = NERVE_HERO
# compositor: a soft glow around bright things (nerve signals, sparks)
try:
    ct_ = S.compositing_node_group if hasattr(S, 'compositing_node_group') else None
    if ct_ is None and hasattr(S, 'compositing_node_group'):
        ct_ = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); S.compositing_node_group = ct_
    rl_ = ct_.nodes.get('Render Layers') or ct_.nodes.new('CompositorNodeRLayers')
    gl_ = ct_.nodes.new('CompositorNodeGlare')
    for ty_ in ('Bloom', 'Fog Glow'):
        try: gl_.inputs['Type'].default_value = ty_; break
        except Exception: pass
    for k_, v_ in (('Threshold', 1.5), ('Strength', 0.35), ('Size', 0.55), ('Quality', 'High')):
        try: gl_.inputs[k_].default_value = v_
        except Exception: pass
    out_ = next((n for n in ct_.nodes if n.bl_idname in ('CompositorNodeComposite', 'NodeGroupOutput')), None)
    if out_ is None:
        out_ = ct_.nodes.new('NodeGroupOutput'); ct_.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ct_.links.new(rl_.outputs['Image'], gl_.inputs['Image']); ct_.links.new(gl_.outputs['Image'], out_.inputs[0])
    print('compositor glow on')
except Exception as e_: print('compositor glow skipped', e_)

# ---- the tibial nerve's branches into the calf (the atlas has the trunk only). Real layout: just below the back of the knee the
# tibial nerve sends a branch into each head of the gastrocnemius (entering its deep surface, upper part), into plantaris, popliteus
# and soleus; inside, each splits into fine twigs that run down the muscle. Built in rest space, riding the muscle they enter.
def centreline(o, step=250):
    arc = o.data.attributes['arc'].data; bins = {}
    for i, v in enumerate(o.data.vertices): bins.setdefault(round(arc[i].value * step), []).append(v.co)
    return sorted((k / step, sum(vs, Vector()) / len(vs)) for k, vs in bins.items())
TIB_C = centreline(TIB)
def copy_weights(dst, src):
    """dst vertices take the bone weights of the nearest src vertex (so a twig rides inside its muscle)"""
    kd = kdtree.KDTree(len(src.data.vertices))
    for i, v in enumerate(src.data.vertices): kd.insert(v.co, i)
    kd.balance()
    for g in src.vertex_groups:
        if g.name not in dst.vertex_groups: dst.vertex_groups.new(name=g.name)
    for v in dst.data.vertices:
        j = kd.find(v.co)[1]
        for g in src.data.vertices[j].groups: dst.vertex_groups[src.vertex_groups[g.group].name].add([v.index], g.weight, 'REPLACE')
def bez(p0, p1, p2, p3, n):
    return [p0 * (1 - t) ** 3 + p1 * 3 * (1 - t) ** 2 * t + p2 * 3 * (1 - t) * t * t + p3 * t ** 3 for t in (i / (n - 1) for i in range(n))]
def nerve_tube(name, pts, r0, r1, arc0, parent_mus, m=None):
    o = tube(name, pts, lambda k: lerp(r0, r1, k), m or NERVE_HERO, seg=8); o.parent = RIG
    acc = [arc0]
    for i in range(1, len(pts)): acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
    at = o.data.attributes.new('arc', 'FLOAT', 'POINT')
    for i_, v in enumerate(o.data.vertices): at.data[i_].value = acc[min(i_ // 8, len(acc) - 1)]
    copy_weights(o, parent_mus); md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG; md.use_deform_preserve_volume = True
    o.visible_shadow = False; o['kind'] = 'nerve'
    for p_, v in PROPS: o[p_] = v
    return o, acc[-1]
import random
from mathutils import kdtree
BRANCHES = []
_rng = random.Random(7)
for mus_name, n_tw in (('Medial head of gastrocnemius', 6), ('Lateral head of gastrocnemius', 5), ('Soleus muscle', 6), ('Plantaris muscle', 2), ('Popliteus muscle', 2)):
    M_ = AN[mus_name]; P = [v.co.copy() for v in M_.data.vertices]
    z0, z1 = min(p.z for p in P), max(p.z for p in P); H = z1 - z0
    cen = sum(P, Vector()) / len(P)
    upper = [p for p in P if p.z > z1 - 0.38 * H]
    # entry: the muscle point (upper part) closest to the nerve trunk
    best = min(((min((p - c).length for _, c in TIB_C), p) for p in upper[::7]), key=lambda x: x[0])[1]
    a_o, c_o = min(TIB_C, key=lambda ac: (ac[1] - best).length)
    entry = best + (cen - best).normalized() * 0.004
    pts = bez(c_o, c_o + (entry - c_o) * 0.3 + Vector((0, 0, -0.01)), entry + (c_o - entry) * 0.3, entry, 14)
    br, a_e = nerve_tube('br_' + mus_name, pts, 0.0013, 0.0010, a_o, M_); BRANCHES.append(br)
    # twigs inside: run down through the belly, fanning out, ending in the muscle's middle and lower parts
    belly = [p for p in P if z0 + 0.15 * H < p.z < z1 - 0.3 * H]
    for k in range(n_tw):
        tgt = belly[_rng.randrange(len(belly))]; tgt = tgt + (cen - tgt) * 0.35
        mid = entry.lerp(tgt, 0.5) + (cen - entry.lerp(tgt, 0.5)) * 0.3 + Vector((_rng.uniform(-1, 1), _rng.uniform(-1, 1), 0)) * 0.006
        tw = bez(entry, entry.lerp(mid, 0.6), mid.lerp(tgt, 0.5), tgt, 18)
        o, a_t = nerve_tube('tw_%s_%d' % (mus_name[:6], k), tw, 0.0008, 0.00035, a_e, M_); BRANCHES.append(o)
        for kk in range(2):                                            # and finer twigs off each one
            s_ = 0.4 + 0.25 * kk; p0 = tw[int(s_ * 17)]; end = p0 + (tgt - entry).normalized() * 0.04 + Vector((_rng.uniform(-1, 1), _rng.uniform(-1, 1), _rng.uniform(-0.5, 0.2))) * 0.02
            end = end + (cen - end) * 0.25
            o2, _ = nerve_tube('tw2_%s_%d_%d' % (mus_name[:6], k, kk), bez(p0, p0.lerp(end, 0.4), p0.lerp(end, 0.7), end, 10), 0.00045, 0.00022,
                               a_e + (a_t - a_e) * s_, M_); BRANCHES.append(o2)
print('tibial branches', len(BRANCHES))
NERVES += BRANCHES; HERO_N += BRANCHES
# ---- the cramp itself: the calf muscles bunch into a knot (shape key 'knot': the belly swells out around its own long axis)
def pca_axis(P):
    c = sum(P, Vector()) / len(P); A_ = np.array([p - c for p in P]); w, v = np.linalg.eigh(A_.T @ A_); return c, Vector(v[:, -1]).normalized()
for o in CALF:
    P = [v.co.copy() for v in o.data.vertices]; c, ax = pca_axis(P)
    s = [(p - c).dot(ax) for p in P]; L_ = max(s) - min(s); sb = min(s) + 0.55 * L_ if ax.z > 0 else max(s) - 0.55 * L_
    o.shape_key_add(name='basis'); kk = o.shape_key_add(name='knot'); kk.value = 0.0
    for i, p in enumerate(P):
        rad = (p - c) - ax * s[i]; w = math.exp(-((s[i] - sb) / (0.24 * L_)) ** 2)
        kk.data[i].co = p + rad * 0.28 * w - ax * (s[i] - sb) * 0.06 * w
for o in ANAT + BRANCHES: o.hide_render = True

# ================================================================ INSIDE THE MUSCLE (a set of its own far from the room, at MO)
# A bundle of muscle fibres (striped: sarcomeres), their nuclei, capillaries with red blood cells, and one motor nerve fibre:
# myelin sheath with gaps (nodes) where the signal jumps, splitting into terminal branches that end in motor end plates on the
# fibres. A signal reaching an end plate flashes it, a wave runs both ways along the fibre, the fibre shortens (squeezes) and
# lets go. In the cramp the end plates fire on their own, up to 150 times a second: the fibres never let go.
# Scale: 1 scene metre here ~ 0.6 mm (a fibre 0.1 wide ~ 60 micrometres).
MO = V3(40.0, 0.0, 1.0)
FIB_R, FIB_L, SARC = 0.05, 2.6, 0.0068
def fibre_mat():
    m = bpy.data.materials.new('fibre'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.38; b.inputs['Coat Weight'].default_value = 0.4; b.inputs['Coat Roughness'].default_value = 0.15
    b.inputs['Subsurface Weight'].default_value = 0.25; b.inputs['Subsurface Radius'].default_value = (0.02, 0.006, 0.004)
    u = nt.nodes.new('ShaderNodeAttribute'); u.attribute_type = 'GEOMETRY'; u.attribute_name = 'u'; u = u.outputs['Fac']
    nuc = nt.nodes.new('ShaderNodeAttribute'); nuc.attribute_type = 'GEOMETRY'; nuc.attribute_name = 'nuc'; nuc = nuc.outputs['Fac']
    ph = math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'MULTIPLY', u, FIB_L), SARC))                       # position inside one sarcomere
    aband = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', ph, 0.28), math_(nt, 'LESS_THAN', ph, 0.72))   # dark A band in the middle
    zline = math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', ph, 0.0)), 0.035)            # thin Z line at the ends
    c0 = nt.nodes.new('ShaderNodeMix'); c0.data_type = 'RGBA'; c0.inputs['A'].default_value = (0.78, 0.3, 0.28, 1); c0.inputs['B'].default_value = (0.38, 0.06, 0.07, 1)
    nt.links.new(aband, c0.inputs['Factor'])
    c1 = nt.nodes.new('ShaderNodeMix'); c1.data_type = 'RGBA'; c1.inputs['B'].default_value = (0.25, 0.04, 0.05, 1); nt.links.new(c0.outputs['Result'], c1.inputs['A'])
    nt.links.new(zline, c1.inputs['Factor'])
    c2 = nt.nodes.new('ShaderNodeMix'); c2.data_type = 'RGBA'; c2.inputs['B'].default_value = (0.32, 0.12, 0.42, 1); nt.links.new(c1.outputs['Result'], c2.inputs['A'])
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', nuc, 1.4), 1.0), c2.inputs['Factor']); nt.links.new(c2.outputs['Result'], b.inputs['Base Color'])
    # the electrical wave: a bright ring at |u - ep| = wv (u units), fading with 'flash'; 'rip' adds repeating ripples (the cramp); 'mis' -> red
    d = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, objattr(nt, 'ep')))
    ring = math_(nt, 'EXPONENT', math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', d, objattr(nt, 'wv')), 0.012), 2.0), -1.0))
    ring = math_(nt, 'MULTIPLY', ring, objattr(nt, 'flash'))
    rip = math_(nt, 'POWER', math_(nt, 'FRACT', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', d, 22.0), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 9.0))), 6.0)
    rip = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', rip, objattr(nt, 'rip')), math_(nt, 'EXPONENT', math_(nt, 'MULTIPLY', d, -3.0)))
    glow = math_(nt, 'ADD', math_(nt, 'MULTIPLY', ring, 9.0), math_(nt, 'MULTIPLY', rip, 4.0))
    ec = nt.nodes.new('ShaderNodeMix'); ec.data_type = 'RGBA'; ec.inputs['A'].default_value = (1.0, 0.75, 0.35, 1); ec.inputs['B'].default_value = (1.0, 0.18, 0.06, 1)
    nt.links.new(objattr(nt, 'mis'), ec.inputs['Factor']); nt.links.new(ec.outputs['Result'], b.inputs['Emission Color'])
    nt.links.new(glow, b.inputs['Emission Strength']); return m
FIBRE_M = fibre_mat()
def fibre(name, c, r, seed):
    """a fibre along x: rings of 28, 'u' 0..1 along, nuclei as long low bumps ('nuc'), a gentle wander; shape key 'short' squeezes it"""
    rng = random.Random(seed); n_l, n_a = 220, 28
    nucs = [(rng.uniform(0.04, 0.96), rng.uniform(0, 2 * math.pi)) for _ in range(9)]
    ph1, ph2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
    vs, us, ns, sk = [], [], [], []
    for i in range(n_l):
        u = i / (n_l - 1); x = (u - 0.5) * FIB_L
        wy = 0.006 * math.sin(u * 5.0 + ph1); wz = 0.006 * math.sin(u * 4.1 + ph2)
        for k in range(n_a):
            a_ = 2 * math.pi * k / n_a; bump = 0.0
            for (nu, na) in nucs:
                da = (a_ - na + math.pi) % (2 * math.pi) - math.pi
                bump = max(bump, math.exp(-((u - nu) * FIB_L / 0.022) ** 2 - (da / 0.35) ** 2))
            rr = r * (1 + 0.012 * math.sin(a_ * 3 + u * 40) + 0.1 * bump)
            p = (x, c[0] + wy + rr * math.cos(a_), c[1] + wz + rr * math.sin(a_)); vs.append(p); us.append(u); ns.append(bump)
            # squeezed: 18% shorter about its middle, 10% fatter
            sk.append((x * 0.82, c[0] + wy + rr * 1.1 * math.cos(a_), c[1] + wz + rr * 1.1 * math.sin(a_)))
    fs = [(i * n_a + k, i * n_a + (k + 1) % n_a, (i + 1) * n_a + (k + 1) % n_a, (i + 1) * n_a + k) for i in range(n_l - 1) for k in range(n_a)]
    fs.append(tuple(range(n_a))[::-1]); fs.append(tuple((n_l - 1) * n_a + k for k in range(n_a)))
    o = mesh(name, vs, fs, FIBRE_M); o.location = MO
    au = o.data.attributes.new('u', 'FLOAT', 'POINT'); an = o.data.attributes.new('nuc', 'FLOAT', 'POINT')
    au.data.foreach_set('value', us); an.data.foreach_set('value', ns)
    o.shape_key_add(name='basis'); k_ = o.shape_key_add(name='short')
    for i, p in enumerate(sk): k_.data[i].co = p
    for p_, v in (('ep', 0.5), ('wv', 0.0), ('flash', 0.0), ('rip', 0.0), ('mis', 0.0), ('tt', 0.0)): o[p_] = v
    return o
# hex-packed bundle (37 fibres) in the y-z plane, plus a few fibres of the next bundle behind
FIBRES = []
_rng = random.Random(11); _sp = 0.108
_hex = [(0, 0)] + [(r_ * math.cos(math.pi / 3 * s_) + k_ * math.cos(math.pi / 3 * (s_ + 2)), r_ * math.sin(math.pi / 3 * s_) + k_ * math.sin(math.pi / 3 * (s_ + 2)))
                   for r_ in (1, 2, 3) for s_ in range(6) for k_ in range(r_)]
for i_, (hy, hz) in enumerate(_hex):
    FIBRES.append(fibre('fibre%d' % i_, (hy * _sp + _rng.uniform(-0.006, 0.006), hz * _sp + _rng.uniform(-0.006, 0.006)), FIB_R * _rng.uniform(0.9, 1.08), i_))
for i_ in range(7):                                                     # the next bundle, behind (soft in the depth of field)
    a_ = i_ / 7 * 2 * math.pi
    FIBRES.append(fibre('fibreB%d' % i_, (0.95 + 0.12 * math.cos(a_), -0.75 + 0.12 * math.sin(a_)), FIB_R, 100 + i_))
# motor unit: the fibres one motor nerve fibre reaches (outer ones facing the camera side +z / -y)
UNIT = [i for i, (hy, hz) in enumerate(_hex) if hz > 0.5 or hy < -1.5][:14]
# end plates: a small branched cluster of bulbs on the top of each unit fibre
EP_M = bpy.data.materials.new('endplate'); EP_M.use_nodes = True
_bp = N(EP_M)['Principled BSDF']; _bp.inputs['Base Color'].default_value = (0.95, 0.78, 0.4, 1); _bp.inputs['Roughness'].default_value = 0.3
_bp.inputs['Emission Color'].default_value = (1.0, 0.7, 0.3, 1)
nt_ = EP_M.node_tree; nt_.links.new(math_(nt_, 'MULTIPLY', objattr(nt_, 'flash'), 14.0), _bp.inputs['Emission Strength'])
_mc = nt_.nodes.new('ShaderNodeMix'); _mc.data_type = 'RGBA'; _mc.inputs['A'].default_value = (1.0, 0.75, 0.35, 1); _mc.inputs['B'].default_value = (1.0, 0.15, 0.05, 1)
nt_.links.new(objattr(nt_, 'mis'), _mc.inputs['Factor']); nt_.links.new(_mc.outputs['Result'], _bp.inputs['Emission Color'])
EPS = {}
for i_ in UNIT:
    fo = FIBRES[i_]; hy, hz = _hex[i_]; cy, cz = hy * _sp, hz * _sp
    ep = _rng.uniform(0.42, 0.6); fo['ep'] = ep
    up_ = Vector((0, cy, cz + 0.6)).normalized() if (hy, hz) != (0, 0) else Vector((0, 0, 1))
    bm = bmesh.new()
    for k in range(9):
        aa = k / 9 * 2 * math.pi; rr = 0.012 + 0.006 * math.sin(k * 2.3)
        off = Vector(((math.cos(aa) * rr * 1.8), math.sin(aa) * rr * 0.7, 0))
        m4 = Matrix.Translation(off) @ Matrix.Diagonal((1.6, 1.0, 0.55, 1.0))
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.0065 + 0.002 * (k % 3), matrix=m4)
    me_ = bpy.data.meshes.new('ep%d' % i_); bm.to_mesh(me_); bm.free()
    for p_ in me_.polygons: p_.use_smooth = True
    eo = obj('ep%d' % i_, me_, EP_M); eo['flash'] = 0.0; eo['mis'] = 0.0
    z_ax = up_; x_ax = Vector((1, 0, 0)); y_ax = z_ax.cross(x_ax)
    EPS[i_] = (eo, Vector((0, cy, cz)) + up_ * (FIB_R * 1.02), Matrix((x_ax, y_ax, z_ax)).transposed())
# the motor nerve fibre: myelinated stem (segments of myelin, gaps = nodes of Ranvier) coming in from above, then bare terminal branches
AX_M = bpy.data.materials.new('axon'); AX_M.use_nodes = True; nt_ = AX_M.node_tree; _ba = nt_.nodes['Principled BSDF']
_arc = nt_.nodes.new('ShaderNodeAttribute'); _arc.attribute_type = 'GEOMETRY'; _arc.attribute_name = 'arc'; _arc = _arc.outputs['Fac']
_my = nt_.nodes.new('ShaderNodeAttribute'); _my.attribute_type = 'GEOMETRY'; _my.attribute_name = 'myelin'; _my = _my.outputs['Fac']
_node = math_(nt_, 'MULTIPLY', math_(nt_, 'LESS_THAN', math_(nt_, 'FRACT', math_(nt_, 'DIVIDE', _arc, 0.16)), 0.08), _my)
_col = nt_.nodes.new('ShaderNodeMix'); _col.data_type = 'RGBA'; _col.inputs['A'].default_value = (0.93, 0.88, 0.74, 1); _col.inputs['B'].default_value = (0.95, 0.62, 0.2, 1)
nt_.links.new(math_(nt_, 'MAXIMUM', math_(nt_, 'SUBTRACT', 1.0, _my), _node), _col.inputs['Factor']); nt_.links.new(_col.outputs['Result'], _ba.inputs['Base Color'])
_ba.inputs['Roughness'].default_value = 0.22; _ba.inputs['Coat Weight'].default_value = 0.6
_rel = math_(nt_, 'SUBTRACT', objattr(nt_, 'ph'), _arc)
_pk = math_(nt_, 'MULTIPLY', math_(nt_, 'EXPONENT', math_(nt_, 'MULTIPLY', math_(nt_, 'ABSOLUTE', _rel), -28.0)), objattr(nt_, 'pulse'))
# on the myelinated stem the signal shows only at the nodes (it jumps node to node); on bare branches it glides
_vis = math_(nt_, 'MAXIMUM', math_(nt_, 'SUBTRACT', 1.0, _my), _node)
_ba.inputs['Emission Color'].default_value = (1.0, 0.75, 0.3, 1)
nt_.links.new(math_(nt_, 'ADD', math_(nt_, 'MULTIPLY', math_(nt_, 'MULTIPLY', _pk, _vis), 30.0), math_(nt_, 'MULTIPLY', objattr(nt_, 'glow'), 0.15)), _ba.inputs['Emission Strength'])
AXONS = []
def axon_tube(name, pts, r0, r1, arc0, myelin):
    o = tube(name, [p - MO for p in pts], lambda k: lerp(r0, r1, k), AX_M, seg=14); o.location = MO
    acc = [arc0]
    for i in range(1, len(pts)): acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
    at = o.data.attributes.new('arc', 'FLOAT', 'POINT'); am = o.data.attributes.new('myelin', 'FLOAT', 'POINT')
    for i_, v in enumerate(o.data.vertices): at.data[i_].value = acc[min(i_ // 14, len(acc) - 1)]; am.data[i_].value = myelin
    o['ph'] = 0.0; o['pulse'] = 0.0; o['glow'] = 1.0; AXONS.append(o); return o, acc[-1]
_top = MO + V3(-0.25, 0.05, 0.62); _src = MO + V3(-1.6, 0.35, 1.6)
_stem, ARC_SPLIT = axon_tube('axon', bez(_src, _src + V3(0.6, -0.1, -0.2), _top + V3(-0.3, 0.0, 0.25), _top, 40), 0.016, 0.014, 0.0, 1.0)
EP_ARC = {}
for i_ in UNIT:
    eo, loc, M3 = EPS[i_]; fo = FIBRES[i_]; ep_w = MO + V3((fo['ep'] - 0.5) * FIB_L, 0, 0) + loc
    mid = _top.lerp(ep_w, 0.5) + V3(0, 0, 0.12)
    pts = bez(_top, _top + (mid - _top) * 0.6, ep_w + V3(0, 0, 0.1) + (mid - ep_w) * 0.2, ep_w + M3.col[2] * 0.004, 26)
    o, a_end = axon_tube('axon_br%d' % i_, pts, 0.0055, 0.0032, ARC_SPLIT, 0.0); EP_ARC[i_] = a_end
# capillaries between the fibres, with red blood cells sliding through
CAP_M = mat('capillary', (0.8, 0.25, 0.25), 0.15, trans=0.6, ior=1.35, alpha=1.0)
RBC_M = mat('rbc', (0.65, 0.04, 0.04), 0.35, coat=0.3)
CAPS = []; RBCS = []
_rbc_me = None
for k in range(6):
    a_ = k / 6 * 2 * math.pi + 0.3; rr = 3.5 * _sp * 0.5 + 0.02
    cy, cz = rr * math.cos(a_) * 0.62, rr * math.sin(a_) * 0.62
    pts = [MO + V3((i / 59 - 0.5) * FIB_L, cy + 0.01 * math.sin(i * 0.3 + k), cz + 0.01 * math.cos(i * 0.25 + k)) for i in range(60)]
    c = tube('cap%d' % k, [p - MO for p in pts], 0.0075, CAP_M, seg=12); c.location = MO; CAPS.append((c, pts))
    for j in range(14):
        if _rbc_me is None:
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
            for v in bm.verts:
                rxy = math.hypot(v.co.x, v.co.y); v.co.z = 0.32 * v.co.z * (0.35 + 0.65 * rxy * rxy)       # biconcave disc
            _rbc_me = bpy.data.meshes.new('rbc'); bm.to_mesh(_rbc_me); bm.free()
            for p_ in _rbc_me.polygons: p_.use_smooth = True
        ro = obj('rbc%d_%d' % (k, j), _rbc_me, RBC_M); ro.scale = (0.0055, 0.0055, 0.0055); RBCS.append((ro, k, j / 14.0 + random.Random(k * 31 + j).uniform(0, 0.05)))
# light for the close-up: warm key from above, cool rim behind, a red-dark world (set in macro mode)
MKEY = light_at('macro_key', 'AREA', MO + V3(-0.8, -1.2, 1.6), MO, 160, (1.0, 0.86, 0.75), 1.2)
MRIM = light_at('macro_rim', 'AREA', MO + V3(0.9, 1.4, 0.6), MO, 220, (0.55, 0.7, 1.0), 1.0)
MFILL = light_at('macro_fill', 'AREA', MO + V3(0.0, -1.5, -0.8), MO, 45, (1.0, 0.5, 0.45), 2.0)
MACRO = FIBRES + [e[0] for e in EPS.values()] + AXONS + [c for c, _ in CAPS] + [r for r, _, _ in RBCS] + [MKEY, MRIM, MFILL]
for o in MACRO: o.hide_render = True
def macro_place(t, act):
    """fibres squeeze by act[i] (0..1); end plates ride their fibre; blood cells slide along the capillaries"""
    for i_, fo in enumerate(FIBRES):
        a_ = act.get(i_, 0.0); fo.data.shape_keys.key_blocks['short'].value = a_
    for i_, (eo, loc, M3) in EPS.items():
        fo = FIBRES[i_]; a_ = act.get(i_, 0.0); x = (fo['ep'] - 0.5) * FIB_L * (1 - 0.18 * a_)
        eo.matrix_world = Matrix.Translation(MO + V3(x, 0, 0) + loc * (1 + 0.1 * a_)) @ M3.to_4x4()
    for ro, k, ph0 in RBCS:
        _, pts = CAPS[k]; s_ = (ph0 + t * 0.09) % 1.0; f_ = s_ * (len(pts) - 1); i0 = int(f_); i1 = min(i0 + 1, len(pts) - 1)
        p = pts[i0].lerp(pts[i1], f_ - i0); d = (pts[i1] - pts[i0]).normalized()
        q = d.to_track_quat('Z', 'Y') @ Quaternion((1, 0, 0), 0.6 * math.sin(t * 3 + ph0 * 20))
        ro.location = p; ro.rotation_mode = 'QUATERNION'; ro.rotation_quaternion = q

# ================================================================ POSING: legs and arms by IK, hands turned by Copy Rotation; his weight dents the bed
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
# ---- his weight in the bed: heightfield of his underside (world), the duvet top and his pillow sink to it (smooth falloff)
def world_pts(objs):
    dg = bpy.context.evaluated_depsgraph_get(); out = []
    for o in objs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices); co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); oe.to_mesh_clear()
        M_ = np.array(o.matrix_world); out.append(co.reshape(-1, 3) @ M_[:3, :3].T + M_[:3, 3])
    return np.concatenate(out)
def _shift_min(H):
    p = np.pad(H, 1, constant_values=np.inf); return np.min([p[1 + a:1 + a + H.shape[0], 1 + b:1 + b + H.shape[1]] for a in (-1, 0, 1) for b in (-1, 0, 1)], axis=0)
def _shift_max(D):
    p = np.pad(D, 1, constant_values=0.0); return np.max([p[1 + a:1 + a + D.shape[0], 1 + b:1 + b + D.shape[1]] for a in (-1, 0, 1) for b in (-1, 0, 1)], axis=0)
def _blur(D, s):
    r = int(3 * s); k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * s * s)); k /= k.sum()
    p = np.pad(D, ((0, 0), (r, r)), mode='edge'); D = sum(k[i] * p[:, i:i + D.shape[1]] for i in range(2 * r + 1))
    p = np.pad(D, ((r, r), (0, 0)), mode='edge'); return sum(k[i] * p[i:i + D.shape[0], :] for i in range(2 * r + 1))
def heightfield(P, x0, y0, nx, ny, d):
    H = np.full((ny, nx), np.inf); i = np.round((P[:, 0] - x0) / d).astype(int); j = np.round((P[:, 1] - y0) / d).astype(int)
    ok = (i >= 0) & (i < nx) & (j >= 0) & (j < ny); np.minimum.at(H, (j[ok], i[ok]), P[ok, 2])
    return _shift_min(_shift_min(H))
DENT_SRC = None
def dent_bed():
    P = world_pts([BODY, SUIT, HAIR])
    H = heightfield(P, DXS[0], DYS[0], DNX, DNY, DX); rest = DUV_REST[:, 2].reshape(DNY, DNX)
    Dh = np.clip(rest - (H - 0.0015), 0.0, 0.032); Dh[~np.isfinite(Dh)] = 0.0
    D = np.maximum(Dh, _blur(_shift_max(Dh), 2.4)) * DUV_TOP_MASK.reshape(DNY, DNX)
    co = DUV_REST.copy(); co[:, 2] -= D.ravel(); DUVET.data.vertices.foreach_set('co', co.astype(np.float32).ravel()); DUVET.data.update()
    # pillow: per vertex, the head/hair height above it (heightfield 1 cm), then a few smoothing passes over the pillow's grid
    o = PILLOW; rest_l = PIL_REST[o.name]; M_ = np.array(o.matrix_world); wv = rest_l @ M_[:3, :3].T + M_[:3, 3]
    x0, y0 = wv[:, 0].min() - 0.02, wv[:, 1].min() - 0.02; nx, ny = int((wv[:, 0].max() - x0) / 0.01) + 3, int((wv[:, 1].max() - y0) / 0.01) + 3
    Hp = heightfield(P, x0, y0, nx, ny, 0.01)
    ii = np.clip(np.round((wv[:, 0] - x0) / 0.01).astype(int), 0, nx - 1); jj = np.clip(np.round((wv[:, 1] - y0) / 0.01).astype(int), 0, ny - 1)
    top = rest_l[:, 2] > -0.2 * PIL_H
    dv = np.clip(wv[:, 2] - (Hp[jj, ii] - 0.0015), 0.0, 1.6 * PIL_H) * top; dv[~np.isfinite(dv)] = 0.0
    nu = 64; G = dv.reshape(-1, nu)
    for _ in range(5):
        G = np.maximum(G, 0.6 * (np.roll(G, 1, 1) + np.roll(G, -1, 1) + np.vstack([G[:1], G[:-1]]) + np.vstack([G[1:], G[-1:]])) / 4)
    co = rest_l.copy(); co[:, 2] -= G.ravel() * top; o.data.vertices.foreach_set('co', co.astype(np.float32).ravel()); o.data.update()
def body_eval():
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp)
    oe.to_mesh_clear(); M_ = np.array(BODY.matrix_world); return co.reshape(-1, 3) @ M_[:3, :3].T + M_[:3, 3], rp.reshape(-1, 3)
SETTLE_LOG = {}
SUIT.add_rest_position_attribute = True
def suit_trunk_low():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp)
    oe.to_mesh_clear(); co = co.reshape(-1, 3); rp = rp.reshape(-1, 3); M_ = np.array(SUIT.matrix_world); w = co @ M_[:3, :3].T + M_[:3, 3]
    m_ = (np.abs(rp[:, 0]) < 0.16) & (rp[:, 2] < 1.42); return float(w[m_, 2].min())
def settle(sink_trunk=0.022, sink_leg=0.012, legs=('R', 'L'), passes=5):
    """his back (or seat) sinks sink_trunk into the duvet, his legs sink_leg: move the rig, then each ankle target"""
    for _ in range(passes):
        # his trunk is under the clothes (the body mesh is masked away there), so the shirt and shorts tell where his back or seat is
        # (the trunk only: not the sleeves, which lie lower than his back when his arms rest on the bed)
        dz = (DUVET_TOP - sink_trunk) - suit_trunk_low(); RIG.location.z += dz; bpy.context.view_layer.update()
        w, rp = body_eval(); worst = abs(dz)
        for s_ in legs:
            sg = -1.0 if s_ == 'R' else 1.0; m_ = (rp[:, 0] * sg > 0.02) & (rp[:, 2] < 0.6)
            d2 = (DUVET_TOP - sink_leg) - float(w[m_, 2].min()); TGT['ank' + s_].location.z += d2; worst = max(worst, abs(d2))
        bpy.context.view_layer.update()
        if worst < 0.0005: break
    SETTLE_LOG['worst'] = worst
NECK = {'v': 0.0}
def head_on_pillow(target_sink=0.03, passes=6):
    """lying: bend his neck until the back of his head rests in the pillow (target_sink below its top)"""
    top = PILLOW.location.z + PIL_H
    for _ in range(passes):
        w, rp = body_eval(); hm = rp[:, 2] > 1.52
        err = (top - target_sink) - float(w[hm, 2].min())
        if abs(err) < 0.001: break
        NECK['v'] = clamp(NECK['v'] + math.degrees(err / 0.13), -10, 60)
        for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)): rot(n, NECK['v'] * k)
        bpy.context.view_layer.update()
HC_LOG = []
def hand_contact(sides=('R', 'L'), passes=7, keep=0.002):
    """push a hand out of his right calf/shin/foot if it sank in (signed distance to the leg skin)"""
    for _ in range(passes):
        dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles()
        n = len(me.vertices); co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); rp = rp.reshape(-1, 3)
        tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('vertices', tri); tri = tri.reshape(-1, 3); oe.to_mesh_clear()
        M_ = np.array(BODY.matrix_world); w = co @ M_[:3, :3].T + M_[:3, 3]
        leg = (rp[:, 0] < -0.035) & (rp[:, 2] < 0.52) & (np.abs(rp[:, 0]) < 0.3)
        lt_ = tri[leg[tri].all(1)]
        T_ = BVHTree.FromPolygons([Vector(p) for p in w], lt_.tolist())
        moved = False
        for s_ in sides:
            sg = -1.0 if s_ == 'R' else 1.0; hm = np.where((rp[:, 0] * sg > 0.4) & (rp[:, 2] < 1.02))[0]
            pen, nrm = 0.0, Vector()
            for i in hm[::2]:
                p = Vector(w[i]); loc, nor, _, d = T_.find_nearest(p, 0.05)
                if loc is not None and (p - loc).dot(nor) < 0 and d > pen: pen, nrm = d, nor
            if pen > 0.0005: TGT['hand' + s_].location += nrm * (pen + keep); moved = True; HC_LOG.append((s_, round(pen, 4), tuple(round(x, 2) for x in nrm)))
        if not moved: return
        bpy.context.view_layer.update()
def calf_frame():
    """right calf in the world: K knee, A ankle, sd down the shin, post toward the calf's back, lat out to his right side, C the belly"""
    K = bone_world('lowerleg01.R'); A = bone_world('foot.R'); sd = (A - K).normalized()
    post = bone_dir('lowerleg01.R', (0, 1, 0)); post = (post - sd * post.dot(sd)).normalized()     # rest +y = the back of his leg
    lat = bone_dir('lowerleg01.R', (-1, 0, 0)); lat = (lat - sd * lat.dot(sd) - post * lat.dot(post)).normalized()   # rest -x = his right
    return K, A, sd, post, lat, K + sd * 0.14 + post * 0.012
def bone_dir(bn, v):
    M = RIG.matrix_world.to_3x3() @ PB[bn].matrix.to_3x3() @ RB[bn].matrix_local.to_3x3().inverted(); return (M @ Vector(v)).normalized()
def foot_frame():
    A = bone_world('foot.R'); T = (bone_world('toe2-1.R') + bone_world('toe3-1.R')) * 0.5; fd = (T - A).normalized()
    K = bone_world('lowerleg01.R'); up_ = (K - A); up_ = (up_ - fd * up_.dot(fd)).normalized(); return A, T, fd, up_

# ================================================================ THE POSES (world). Lying on his back on the duvet, head on his pillow; sitting up;
# right knee up to grab the calf; leg out straight, leaning in to pull his toes back; rubbing the sore calf.
def LIE_ANK(s_): return V3(X_MID + (-0.11 if s_ == 'R' else 0.12), Y_HIP - 0.81, 0.66)
NECK_LIE = 30.0                                            # solved once at start-up (head_on_pillow), used everywhere so frames don't depend on each other
def P_lying(t, point=1.0, cramp=0.0, lids=1.0):
    br = math.sin(t * 1.3)
    return dict(hip=V3(X_MID, Y_HIP, 0.7), rot=-90.0, spine=1.2 * br, neck=NECK_LIE, head=4.0, side=0.0,
                ankR=LIE_ANK('R'), poleR=V3(X_MID - 0.16, Y_HIP - 0.42, 1.6), footR=26 * point + 26 * cramp, toesR=0.12 + 0.88 * cramp,
                ankL=LIE_ANK('L'), poleL=V3(X_MID + 0.17, Y_HIP - 0.42, 1.6), footL=24 * point, toesL=0.12,
                hR='bedR', hL='bedL', curlR=0.04, curlL=0.04, lids=lids, jaw=0.06, sinkT=0.022, knot=cramp, paR=V3(-0.85, -0.05, 1.05), paL=V3(0.85, -0.05, 1.05))
def P_grab(t, rock=1.0, cramp=1.0):
    r_ = math.sin(t * 7.0) * rock
    return dict(hip=V3(X_MID, Y_HIP, 0.7), rot=6.0 + 2.5 * r_, spine=18.0 + 3 * r_, neck=26.0, head=12.0, side=-4.0,
                ankR=V3(X_MID - 0.15, Y_HIP - 0.46, 0.66), poleR=V3(X_MID - 0.2, Y_HIP - 0.42, 1.9), footR=34 + 16 * cramp, toesR=1.0 * cramp,
                ankL=LIE_ANK('L') + V3(0.04, 0.03, 0.0), poleL=V3(X_MID + 0.3, Y_HIP - 0.42, 1.6), footL=12.0, toesL=0.1,
                hR='calfR', hL='calfL', curlR=0.3, curlL=0.3, lids=0.9 * cramp, jaw=0.55 * cramp, sinkT=0.028, knot=cramp, paR=V3(-0.8, -0.25, 0.85), paL=V3(0.85, -0.3, 0.85))
def P_stretch(t, pull=1.0):
    return dict(hip=V3(X_MID, Y_HIP, 0.7), rot=20.0 + 8 * pull, spine=30.0 + 10 * pull, neck=18.0, head=8.0, side=-6.0,
                ankR=V3(X_MID - 0.12, Y_HIP - 0.72, 0.66), poleR=V3(X_MID - 0.2, Y_HIP - 0.4, 1.7), footR=-16.0 * pull + 30 * (1 - pull), toesR=-0.35 * pull,
                ankL=LIE_ANK('L') + V3(0.06, 0.04, 0.0), poleL=V3(X_MID + 0.32, Y_HIP - 0.42, 1.6), footL=14.0, toesL=0.1,
                hR='toes', hL='kneeR', curlR=0.75, curlL=0.45, lids=0.3, jaw=0.15, sinkT=0.028, knot=1.0 - pull, paR=V3(-0.8, -0.1, 0.9), paL=V3(0.85, -0.3, 0.85))
def P_rub(t):
    return dict(hip=V3(X_MID, Y_HIP, 0.7), rot=4.0, spine=14.0, neck=22.0, head=8.0, side=-3.0,
                ankR=V3(X_MID - 0.15, Y_HIP - 0.48, 0.66), poleR=V3(X_MID - 0.2, Y_HIP - 0.42, 1.9), footR=12.0, toesR=0.15,
                ankL=LIE_ANK('L') + V3(0.04, 0.03, 0.0), poleL=V3(X_MID + 0.3, Y_HIP - 0.42, 1.6), footL=14.0, toesL=0.1,
                hR='rub', hL='kneeR', curlR=0.3, curlL=0.45, lids=0.1, jaw=0.0, sinkT=0.028, knot=0.0, rub=t, paR=V3(-0.8, -0.25, 0.85), paL=V3(0.85, -0.3, 0.85))
def hand_spec(s_, spec):
    """(contact, finger dir, palm dir) for a named hand placement, from where his body is right now"""
    if spec in ('bedR', 'bedL'):
        sg = -1.0 if spec == 'bedR' else 1.0
        return V3(X_MID + sg * 0.29, Y_HIP + 0.05, DUVET_TOP - 0.002), V3(0.12 * sg, -1.0, 0.0), V3(0, 0, -1)
    if spec in ('sitR', 'sitL'):
        sg = -1.0 if spec == 'sitR' else 1.0
        return V3(X_MID + sg * 0.3, Y_HIP - 0.06, DUVET_TOP - 0.006), V3(0.1 * sg, -1.0, 0.0), V3(0, 0, -1)
    K, A, sd, post, lat, C = calf_frame()
    # both palms flat on the sides of the calf belly, fingers down toward the heel, squeezing it between them
    if spec == 'calfR': return C + lat * 0.06 + post * 0.012 - sd * 0.01, (sd * 0.9 + post * 0.25).normalized(), -lat
    if spec == 'calfL': return C - lat * 0.058 + post * 0.012 + sd * 0.01, (sd * 0.9 + post * 0.25).normalized(), lat
    if spec == 'rub':
        k_ = math.sin(RUBT['t'] * 6.5); return C + lat * 0.06 + post * 0.012 + sd * (0.0 + 0.04 * k_), (sd * 0.9 + post * 0.25).normalized(), -lat
    if spec == 'kneeR':                                       # palm on top of his right knee, fingers down the shin
        H = bone_world('upperleg01.R'); ku = (K - (H + A) * 0.5); ku = (ku - sd * ku.dot(sd)).normalized()
        return K + ku * 0.052 + sd * 0.02, (sd * 0.9 + ku * 0.1).normalized(), -ku
    if spec == 'toes':
        A_, T_, fd, up_ = foot_frame(); return T_ + fd * 0.035 + up_ * 0.018, (fd - up_ * 0.35).normalized(), -up_
    raise KeyError(spec)
RUBT = {'t': 0.0}
def _lerp_any(a_, b_, k):
    if isinstance(a_, str) or isinstance(b_, str) or a_ is None or b_ is None: return a_ if k < 0.5 else b_
    return a_ + (b_ - a_) * k if not isinstance(a_, Vector) else a_.lerp(b_, k)
def RIG_WORLD_PT(hip, rot_x, p):
    """a point given in his rest space (like the rig's own), placed where it goes with his hips at 'hip' turned rot_x"""
    Rm = Euler((R(rot_x), 0, 0)).to_matrix(); return Vector(hip) + Rm @ (Vector(p) - HIP0)
def apply_pose(PA, PB_=None, k=0.0):
    """pose him (PA, or PA blended toward PB_ by k), let him sink into the bed, put his hands, dent the duvet and pillow"""
    P = PA if PB_ is None else {kk: _lerp_any(PA[kk], PB_[kk], k) for kk in PA if kk in PB_}
    RUBT['t'] = P.get('rub', 0.0) if isinstance(P.get('rub', 0.0), float) else 0.0
    set_pose(P['hip'], (P['rot'], 0, 0), spine=P['spine'], neck=P['neck'], head=P['head'], side_lean=P['side'],
             ankR=P['ankR'], poleR=P['poleR'], footR=(P['footR'], 0, 0), toesR=P['toesR'], ankL=P['ankL'], poleL=P['poleL'],
             footL=(P['footL'], 0, 0), toesL=P['toesL'], curlR=P['curlR'], curlL=P['curlL'], lids=P['lids'], jaw=P['jaw'],
             poleArmR=RIG_WORLD_PT(P['hip'], P['rot'], P['paR']), poleArmL=RIG_WORLD_PT(P['hip'], P['rot'], P['paL']))
    KNOT.value = clamp(P['knot'], 0, 1)
    for o in CALF: o.data.shape_keys.key_blocks['knot'].value = clamp(P['knot'], 0, 1)
    settle(P['sinkT'], 0.012)
    for s_, key in (('R', 'hR'), ('L', 'hL')):
        ca, fa, pa = hand_spec(s_, PA[key])
        if PB_ is not None and PB_[key] != PA[key]:
            cb, fb, pb_ = hand_spec(s_, PB_[key]); kk = sm(clamp(k, 0, 1))
            front = bone_dir('spine03', (0, -1, 0)); out_ = bone_dir('spine03', (1 if s_ == 'L' else -1, 0, 0))
            lift = (front * 0.16 + out_ * 0.06 + V3(0, 0, 0.08)) * math.sin(math.pi * kk)  # the hand travels out in front of him, not through him
            ca, fa, pa = ca.lerp(cb, kk) + lift, fa.lerp(fb, kk), pa.lerp(pb_, kk)
        place_hand(s_, ca, fa, pa)
    bpy.context.view_layer.update()
    for _ in range(3):                                         # an arm resting on the bed sinks at most 1.2 cm (lift the hand if it went deeper)
        w, rp = body_eval(); moved = False
        for s_ in ('R', 'L'):
            sg = -1.0 if s_ == 'R' else 1.0; m_ = (rp[:, 0] * sg > 0.25) & (np.abs(w[:, 0]) < BED_HW) & (w[:, 1] > BED_Y0) & (w[:, 1] < BED_Y1)
            if m_.any():
                d_ = (DUVET_TOP - 0.012) - float(w[m_, 2].min())
                if d_ > 0.001: TGT['hand' + s_].location.z += d_; moved = True
        if not moved: break
        bpy.context.view_layer.update()
    if any(P_.get(key, '') in ('calfR', 'calfL', 'rub', 'kneeR', 'toes') for P_ in (PA, PB_ or {}) for key in ('hR', 'hL')): hand_contact()
    dent_bed()

# ================================================================ X-RAY / MACRO MODES and the story's controls
def xray_mode(on):
    for o in ROOM: o.hide_render = on
    for o in (BODY,): o.hide_render = False
    for o in (SUIT, HAIR) + tuple(HEADBITS): o.hide_render = on
    for i, sl in enumerate(BODY.material_slots): sl.material = XSKIN if on else BODY_MATS[i]
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = not on
    PUFF.strength = 0.004 if on else 0.0
    for o in ANAT + BRANCHES: o.hide_render = not on
    for o in THIGH_MUS: o.hide_render = True
    for o in MACRO: o.hide_render = True
    WBG.inputs['Color'].default_value = (0.004, 0.012, 0.035, 1) if on else (0.008, 0.012, 0.028, 1)
    XL.hide_render = XL2.hide_render = not on
    for lt in (MOON, LAMP_L, FILL): lt.hide_render = on
def macro_mode():
    for o in ROOM + ANAT + BRANCHES + [BODY, SUIT, HAIR] + HEADBITS: o.hide_render = True
    for o in MACRO: o.hide_render = False
    for lt in (MOON, LAMP_L, FILL, XL, XL2): lt.hide_render = True
    WBG.inputs['Color'].default_value = (0.014, 0.003, 0.004, 1)
THIGH_MUS = [AN[n] for n in ('Vastus lateralis muscle', 'Long head of biceps femoris', 'Short head of biceps femoris') if n in AN]
OTHER_MUS = [o for o in MUSCLES if o not in CALF]
def anatomy(t, calf_act=0.0, calf_spark=0.0, ach=0.0, dim_other=0.75, calf_dim=0.45, bones=1.0):
    for o in CALF: o['act'] = calf_act; o['spark'] = calf_spark; o['tt'] = t; o['dim'] = calf_dim
    for o in OTHER_MUS: o['dim'] = dim_other; o['act'] = 0.0; o['spark'] = 0.0
    for o in TENDONS: o['dim'] = dim_other if o is not ACH else 0.15; o['act'] = ach if o is ACH else 0.0
def nerves(t, glow=1.0, other=0.3, pulse=0.0, speed=1.4, gap=0.16, spark=0.0):
    for o in NERVES:
        hero = o in HERO_N
        o['glow'] = glow if hero else other; o['pulse'] = pulse if hero else pulse * 0.2; o['ph'] = t * speed; o['gap'] = gap if o in BRANCHES else max(gap, 0.12)
        o['spark'] = spark if o in BRANCHES else 0.0; o['tt'] = t
def arteries(t, glow=0.35, pulse=0.15):
    for o in ARTS: o['glow'] = glow; o['pulse'] = pulse; o['ph'] = t * 0.9; o['gap'] = 0.16; o['tt'] = t
def h1(n): return (math.sin(n * 127.1 + 311.7) * 43758.5453) % 1.0
def twitch(dt): return 0.0 if dt < 0 else 1.7 * (1 - math.exp(-dt / 0.03)) * math.exp(-dt / 0.2)
MAX_SPD = 2.2                                             # signal speed in the close-up (scene m/s)
VOLLEYS = [0.25, 1.3, 2.35]
def fire_times(i_, t0, t1, rate):
    """this end plate's own (misfiring) shots between t0 and t1, rate(t) shots/s: deterministic per plate"""
    ts, t_ = [], t0 + 0.05 + 0.3 * h1(i_ * 7.1)
    while t_ < t1:
        ts.append(t_); t_ += (0.6 + 0.8 * h1(i_ * 13.3 + len(ts) * 1.7)) / max(rate(t_), 0.5)
    return ts
def macro_state(nb, lt, du):
    """drive the close-up: fibres' squeeze, end plate flashes, waves, the nerve fibre's signal"""
    act = {}; u = lt / du
    for o in AXONS: o['glow'] = 1.0; o['pulse'] = 0.0
    for fo in FIBRES: fo['flash'] = 0.0; fo['wv'] = 0.0; fo['rip'] = 0.0; fo['mis'] = 0.0; fo['tt'] = lt
    for eo, _, _ in EPS.values(): eo['flash'] = 0.0; eo['mis'] = 0.0
    if nb == 4:                                                       # normal: three signals come down, squeeze, let go
        past = [v for v in VOLLEYS if v <= lt]
        if past:
            v = past[-1]
            for o in AXONS: o['ph'] = (lt - v) * MAX_SPD; o['pulse'] = 1.0
        for i_ in UNIT:
            a_ = 0.0; fo = FIBRES[i_]; eo = EPS[i_][0]
            for v in past:
                dt = lt - (v + EP_ARC[i_] / MAX_SPD); a_ += twitch(dt)
                if dt >= 0: fo['flash'] = max(fo['flash'], math.exp(-dt / 0.25)); fo['wv'] = dt * 0.9; eo['flash'] = max(eo['flash'], math.exp(-dt / 0.12))
            act[i_] = clamp(a_, 0, 1)
    elif nb == 5 or nb == 6 or nb == 7:                               # misfire: the plates fire on their own, faster and faster
        T_ = lt if nb == 5 else DUR[5] + (lt if nb == 6 else DUR[6] + lt)
        rate = lambda tt: 1.5 + 22.0 * (tt / DUR[5]) ** 2 if tt < DUR[5] else 150.0
        mis = smooth(0.0, 0.6, T_)
        for o in AXONS: o['glow'] = 0.35
        for i_ in UNIT:
            fo = FIBRES[i_]; eo = EPS[i_][0]; shots = fire_times(i_, 0.0, min(T_, DUR[5]), rate)
            a_ = sum(twitch(T_ - s) for s in shots)
            if shots:
                dt = T_ - shots[-1]; fo['flash'] = math.exp(-dt / 0.2); fo['wv'] = dt * 0.9; eo['flash'] = math.exp(-dt / 0.1)
            if T_ >= DUR[5] - 0.6:                                     # the last stretch: a blur of shots, fused squeeze, ripples
                kf = smooth(DUR[5] - 0.6, DUR[5] + 0.3, T_)
                a_ = lerp(a_, 1.0, kf) + 0.04 * kf * math.sin(T_ * 70 + i_ * 2.1)
                fo['rip'] = kf; eo['flash'] = max(eo['flash'], kf * (0.55 + 0.45 * h1(i_ + int(T_ * 30) * 0.37)))
            fo['mis'] = mis; eo['mis'] = mis; act[i_] = clamp(a_, 0, 1.05)
        for i_ in range(len(FIBRES)):                                 # the rest of the bundle catches it too
            if i_ not in act: act[i_] = clamp(smooth(1.0, DUR[5] + 0.5, T_) * (0.8 + 0.2 * math.sin(T_ * 63 + i_)), 0, 1)
    macro_place(lt, act)

# ================================================================ CAMERAS
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
CAM0 = (V3(-0.98, -1.32, 1.0), V3(X_MID - 0.06, Y_HIP - 0.42, 0.68), 26.0)    # frame one and the loop's last frame: his legs from the foot end
# the lying neck: solve it once (head resting in the pillow) so no frame depends on another
def _solve_neck():
    global NECK_LIE
    P = P_lying(0.0); NECK['v'] = NECK_LIE
    set_pose(P['hip'], (P['rot'], 0, 0), spine=0, neck=NECK_LIE, head=P['head'], ankR=P['ankR'], poleR=P['poleR'], ankL=P['ankL'], poleL=P['poleL'])
    settle(P['sinkT'], 0.012); NECK['v'] = NECK_LIE; head_on_pillow(); NECK_LIE = NECK['v']; print('lying neck %.1f deg' % NECK_LIE)
_solve_neck()

def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    xray_mode(False); BODY['tt'] = t; BODY['knot'] = 0.0
    anatomy(t); nerves(t); arteries(t)
    if nb == 0:                                             # 3 a.m.: the calf locks; he jolts up and grabs it
        cr = smooth(0.0, 0.35, lt); k = smooth(0.18, 0.95, lt)
        kk = k + 0.08 * math.sin(math.pi * clamp((lt - 0.6) / 0.5, 0, 1)) * (1 - k * 0.2)       # a little overshoot as he folds up
        apply_pose(P_lying(t, 1.0, cr, 1.0 - smooth(0.12, 0.3, lt)), P_grab(t, smooth(0.8, 1.2, lt), 1.0), clamp(kk, 0, 1.05))
        cp, ct, lens = CAM0; K, A, sd, post, lat, C = calf_frame()
        kc = smooth(0.0, 1.0, u)
        look(cp.lerp(V3(-0.95, -0.72, 1.12), kc) + shake(t, 0.004 + 0.01 * smooth(0.2, 0.5, lt) * (1 - smooth(0.6, 1.2, lt))),
             ct.lerp(C.lerp(bone_world('head'), 0.3), kc), lerp(lens, 30, kc), 4.0)
    elif nb == 1:                                           # earlier: asleep, toes pointed; then x-ray: the calf squeezed short
        apply_pose(P_lying(t, 1.0, 0.0, 1.0))
        if u < 0.5:
            look(ease(V3(X_MID - 0.3, -1.5, 0.76), V3(X_MID - 0.24, -1.36, 0.73), u * 2) + shake(t, 0.002), V3(X_MID - 0.06, -0.64, 0.66), 34, 3.2)
        else:
            xray_mode(True); anatomy(t, calf_act=0.35, calf_dim=0.4); nerves(t, glow=0.6)
            K, A, sd, post, lat, C = calf_frame(); k2 = (u - 0.5) * 2
            look(C + lat * lerp(0.5, 0.42, k2) + post * 0.12 + sd * 0.06, C + sd * 0.1, 30, 4.0, up=-sd)
    elif nb == 2:                                           # x-ray: the two calf muscles and the heel tendon they pull on
        apply_pose(P_lying(t, 1.0, 0.0, 1.0)); xray_mode(True)
        k_ach = smooth(0.52, 0.66, u)
        anatomy(t, calf_act=1.0 - 0.6 * k_ach, calf_dim=0.3, ach=k_ach); nerves(t, glow=0.5)
        K, A, sd, post, lat, C = calf_frame(); ph_ = lerp(0.35, 1.45, sm(u))
        dir_ = (lat * math.cos(ph_) + post * math.sin(ph_)).normalized()
        look(C + dir_ * lerp(0.46, 0.4, u) + sd * lerp(0.0, 0.17, k_ach), C + sd * lerp(0.02, 0.22, k_ach), 34, 4.5, up=-sd)
    elif nb == 3:                                           # the tibial nerve runs down into them; signals; dive into the muscle
        apply_pose(P_lying(t, 1.0, 0.0, 1.0)); xray_mode(True)
        anatomy(t, calf_act=0.25, calf_dim=0.55); nerves(t, glow=1.0, pulse=1.0, speed=1.1, gap=0.12)
        K, A, sd, post, lat, C = calf_frame(); G = eval_centroid(AN['Medial head of gastrocnemius'])
        cp = K + post * 0.3 + lat * 0.16 + sd * lerp(-0.02, 0.1, smooth(0.0, 0.7, u)); ct = K + sd * lerp(0.05, 0.14, smooth(0.0, 0.7, u)) + post * 0.03
        kd = smooth(0.72, 1.0, u) ** 1.6
        look(cp.lerp(G + post * 0.03, kd), ct.lerp(G, kd), lerp(30, 40, kd), 4.0, up=-sd)
    elif nb in (4, 5, 6):                                   # inside the muscle: fibres, end plates, the signal; misfire; 150 a second
        macro_mode(); macro_state(nb, lt, du)
        if nb == 4:
            kin = smooth(0.0, 0.45, lt)
            cp = (MO + V3(-0.95, -1.25, 0.95)).lerp(MO + V3(-0.62, -0.82, 0.6), kin) + V3(0.12, 0.0, 0.0) * u
            look(cp, MO + V3(-0.02, -0.1, 0.28), 50, 2.2, focus=MO + V3(-0.05, -0.12, 0.3))
        elif nb == 5:
            look(ease(MO + V3(0.72, -0.78, 0.6), MO + V3(0.52, -0.66, 0.5), u), MO + V3(0.02, -0.12, 0.26), 55, 2.2)
        else:
            look(MO + V3(0.32, -0.55, 0.44) + shake(t, 0.006), MO + V3(0.04, -0.08, 0.24) + shake(t + 3, 0.003), 60, 2.4)
    elif nb == 7:                                           # locked: pull back out; the whole calf knotted; he grips it
        if lt < 0.4:
            macro_mode(); macro_state(7, lt, du); kb = smooth(0.0, 0.4, lt)
            look((MO + V3(0.32, -0.55, 0.44)).lerp(MO + V3(1.3, -2.4, 1.5), kb ** 1.5), MO + V3(0.04, -0.08, 0.24), lerp(60, 30, kb), 2.4)
        else:
            apply_pose(P_grab(t, 1.0, 1.0)); K, A, sd, post, lat, C = calf_frame()
            if u < 0.56:
                xray_mode(True); BODY['knot'] = 1.0
                anatomy(t, calf_act=1.0, calf_spark=1.0, calf_dim=0.25); nerves(t, glow=1.0, pulse=1.0, speed=2.6, gap=0.04, spark=0.8)
                kx = smooth(0.4 / du, 0.56, u)
                look(C + lat * lerp(0.5, 0.36, kx) + post * 0.18 - sd * 0.02, C + sd * 0.07, 34, 4.0, up=-sd)
            else:
                k3 = (u - 0.56) / 0.44; ct = C.lerp(bone_world('head'), 0.32)
                look(ct + (lat * 0.85 + post * 0.05 + V3(0, -0.45, 0.3)).normalized() * lerp(1.0, 0.9, k3) + shake(t, 0.004), ct, 32, 3.4)
    elif nb == 8:                                           # straighten the leg, pull the toes back
        k = smooth(0.05, 0.75, u); apply_pose(P_grab(t, 0.0, 1.0 - k * 0.5), P_stretch(t, smooth(0.45, 0.9, u)), k)
        A_, T_, fd, up_ = foot_frame()
        ct = T_.lerp(bone_world('lowerleg01.R'), 0.4).lerp(bone_world('head'), 0.25)
        look(ct + (V3(-0.85, 0.05, 0.42)).normalized() * lerp(1.15, 1.0, u), ct, 30, 4.0)
    elif nb == 9:                                           # x-ray: the muscle pulled long, the misfiring stops, it lets go
        P = P_stretch(t, 1.0); P['knot'] = 1.0 - smooth(0.1, 0.65, u); apply_pose(P)
        xray_mode(True); calm = smooth(0.1, 0.7, u); BODY['knot'] = 1.0 - calm
        anatomy(t, calf_act=lerp(1.0, 0.15, calm), calf_spark=1.0 - calm, calf_dim=0.3)
        nerves(t, glow=lerp(1.0, 0.5, calm), pulse=1.0 - calm, speed=2.6, gap=lerp(0.04, 0.16, calm), spark=0.8 * (1 - calm))
        K, A, sd, post, lat, C = calf_frame(); dir_ = (lat * 0.65 + post * 0.76).normalized()
        look(C + dir_ * lerp(0.5, 0.44, u) + sd * 0.06, C + sd * 0.1, 32, 4.0, up=-sd)
    elif nb == 10:                                          # sore for hours; most adults get these
        apply_pose(P_rub(t)); K, A, sd, post, lat, C = calf_frame()
        look(ease(V3(-1.12, Y_HIP + 0.02, 1.2), V3(-1.02, Y_HIP - 0.12, 1.12), u), C.lerp(K, 0.3) + V3(0, 0, 0.08), 30, 3.6)
    else:                                                   # lies back down, toes pointing; the camera eases back to frame one
        k = smooth(0.0, 0.6, u)
        apply_pose(P_rub(t), P_lying(t, smooth(0.5, 1.0, u), 0.0, smooth(0.45, 0.9, u)), k)
        cp, ct, lens = CAM0
        look(ease(V3(-1.02, Y_HIP - 0.12, 1.12), cp, smooth(0.0, 0.95, u)), ease(V3(X_MID - 0.1, Y_HIP - 0.3, 0.85), ct, smooth(0.0, 0.95, u)),
             lerp(30, lens, smooth(0.0, 0.95, u)), 4.0)

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

