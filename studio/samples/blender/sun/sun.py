# "What if the Sun blinked out?" - clay stop-motion Short (Blender, Cycles), built from clay/clay.py.
# Three little sets on one stage: A the tabletop world (grass slab, paper sky, clay Sun and Moon, lake, pond, the Ball),
# B a black-felt space table (chalk orbit, pushpin, string, clay Earth, Pluto, pinhead stars), C a cutaway ocean tank
# (ice lid, swirling clay water, sea floor, glowing vent, microbes). One shot per script line, timed by times.json beside
# this file ({"starts", "durs", "total"[, "voice"]}); every cut lands 2 poses before its line. Poses on twos (12 a second,
# ceil(total*12) poses); each pose re-boils the clay and flickers the lights. Pose 0 is the Sun already shrinking, and the
# last poses run the same shrink up to it, so the Short loops.
#   python3 sun.py OUTDIR P0 P1 [--samples 96] [--scale 1.0] [--only p,p]      -> OUTDIR/f_00000.png (one per pose)
#   env: CROP=x0,y0,x1,y1 (border render), NODN=1 (no denoiser), LAYOUT=1 (print where things land on screen, no render)
import sys, os, math, json, argparse, random
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=96); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
TM = json.load(open(os.path.join(HERE, 'times.json'))); ST, DU, TOTAL = TM['starts'], TM['durs'], TM['total']
NL = len(ST)
VO = TM.get('voice') or [[s + 0.1, s + d - 0.1] for s, d in zip(ST, DU)]
PPS = 12; POSES = math.ceil(TOTAL * PPS - 1e-6)
CUT = [0.0] + [max(0.0, ST[k] - 2.0 / PPS) for k in range(1, NL)]          # each shot starts 2 poses before its line
# sync points with the burned-in overlays: the 8:20 countdown hits 0:00 as line 3's voice starts (ding), the blackout lands
# on "lights out" a beat later; the thermometer steps with the 59/47/35/23°F readout, 0.4 / 0.9 / 1.4 s into line 5
UD = VO[2][0] - CUT[2]; UL = UD + 0.22
THDROPS = [ST[4] + 0.40, ST[4] + 0.90, ST[4] + 1.40]
def shot_of(t):
    k = max(i for i in range(NL) if CUT[i] <= t + 1e-9)
    return k, t - CUT[k], (CUT[k + 1] if k + 1 < NL else TOTAL) - CUT[k]
clamp = lambda x, lo, hi: max(lo, min(hi, x))
sm = lambda x: x * x * (3 - 2 * x)
def smooth(e0, e1, x): return sm(clamp((x - e0) / (e1 - e0), 0, 1))
lerp = lambda p, q, k: p + (q - p) * k
V3 = lambda *p: Vector(p)
R = math.radians
rng = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('cycles', default_set=False)
S = bpy.context.scene; S.render.engine = 'CYCLES'; S.render.fps = 24
S.render.resolution_x = int(1080 * a.scale); S.render.resolution_y = int(1920 * a.scale); S.render.resolution_percentage = 100
C = S.cycles; C.device = 'CPU'; C.samples = a.samples; C.use_denoising = os.environ.get('NODN') is None; C.denoiser = 'OPENIMAGEDENOISE'
C.max_bounces = 6; C.diffuse_bounces = 3; C.glossy_bounces = 2; C.transmission_bounces = 2; C.volume_bounces = 0; C.transparent_max_bounces = 4
C.use_adaptive_sampling = True; C.adaptive_threshold = 0.02; C.adaptive_min_samples = 24
C.caustics_reflective = False; C.caustics_refractive = False; C.sample_clamp_indirect = 6.0
S.render.use_motion_blur = False
if os.environ.get('CROP'):
    x0_, y0_, x1_, y1_ = map(float, os.environ['CROP'].split(',')); S.render.use_border = True; S.render.use_crop_to_border = True
    S.render.border_min_x, S.render.border_min_y, S.render.border_max_x, S.render.border_max_y = x0_, y0_, x1_, y1_
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'; S.view_settings.exposure = 0.0

# ---------------------------------------------------------------- object bookkeeping: every object belongs to a set (A/B/C) and maybe a prop
CUR = ['A']; PROP = [None]
def link(o):
    S.collection.objects.link(o); o['set'] = CUR[0]
    if PROP[0]: o['prop'] = PROP[0]
    return o
FREF = link(bpy.data.objects.new('frostref', None))          # frost sweeps across the tabletop in this object's x

# ---------------------------------------------------------------- clay material
MAPS = []          # (mapping node, how much it boils)
FROSTN = []        # map-range nodes of the frost sweep (From Min / From Max = the frost front)
ICEN = {}          # name -> map-range node of a radial ice skin (From Min / From Max = threshold)
PBS = {}           # name -> principled node (for emission changes)
ICECOL = (0.80, 0.87, 0.95); WICE = (0.52, 0.74, 0.92)
def clay(name, col, rough=0.5, ss=0.12, prints=1.0, smudge=1.0, bump=0.45, boil=1.0, sheen=0.25, frost=False, ice=None, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; Nn = nt.nodes; Lk = nt.links.new
    b = Nn['Principled BSDF']; PBS[name] = b
    b.inputs['Roughness'].default_value = rough; b.inputs['Subsurface Weight'].default_value = ss
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.55, 0.35); b.inputs['Subsurface Scale'].default_value = 0.0007
    b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.6
    b.inputs['Specular IOR Level'].default_value = 0.42
    if emit: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    tc = Nn.new('ShaderNodeTexCoord'); mp = Nn.new('ShaderNodeMapping'); Lk(tc.outputs['Object'], mp.inputs['Vector']); MAPS.append((mp, boil))
    v = mp.outputs['Vector']
    nz = Nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 45; nz.inputs['Detail'].default_value = 4; Lk(v, nz.inputs['Vector'])
    cr = Nn.new('ShaderNodeValToRGB'); Lk(nz.outputs['Fac'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = (*[c * 0.88 for c in col], 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (*[min(1, c * 1.08) for c in col], 1)
    colout = cr.outputs['Color']
    mask = None
    if frost:                    # white clay pressed over everything left of the frost front (x in the frostref's space)
        tf = Nn.new('ShaderNodeTexCoord'); tf.object = FREF; sx = Nn.new('ShaderNodeSeparateXYZ'); Lk(tf.outputs['Object'], sx.inputs['Vector'])
        fn = Nn.new('ShaderNodeTexNoise'); fn.inputs['Scale'].default_value = 28; fn.inputs['Detail'].default_value = 3; Lk(tf.outputs['Object'], fn.inputs['Vector'])
        ma = Nn.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = 0.07
        Lk(fn.outputs['Fac'], ma.inputs[0]); Lk(sx.outputs['X'], ma.inputs[2])
        mr = Nn.new('ShaderNodeMapRange'); mr.clamp = True; mr.inputs['From Min'].default_value = -5; mr.inputs['From Max'].default_value = -5.02
        Lk(ma.outputs['Value'], mr.inputs['Value']); FROSTN.append(mr); mask = mr.outputs['Result']
    if ice is not None:          # an ice skin that grows in from the shore: r (0 centre .. 1 shore) above the threshold freezes
        rx, ry = ice
        mi = Nn.new('ShaderNodeMapping'); mi.inputs['Scale'].default_value = (1 / rx, 1 / ry, 0); Lk(tc.outputs['Object'], mi.inputs['Vector'])
        ln = Nn.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; Lk(mi.outputs['Vector'], ln.inputs[0])
        fn = Nn.new('ShaderNodeTexNoise'); fn.inputs['Scale'].default_value = 3; fn.inputs['Detail'].default_value = 3; Lk(mi.outputs['Vector'], fn.inputs['Vector'])
        ma = Nn.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = 0.35
        Lk(fn.outputs['Fac'], ma.inputs[0]); Lk(ln.outputs['Value'], ma.inputs[2])
        mr = Nn.new('ShaderNodeMapRange'); mr.clamp = True; mr.inputs['From Min'].default_value = 9; mr.inputs['From Max'].default_value = 9.04
        Lk(ma.outputs['Value'], mr.inputs['Value']); ICEN[name] = mr; mask = mr.outputs['Result']
    if mask is not None:
        fz = Nn.new('ShaderNodeMix'); fz.data_type = 'RGBA'; Lk(mask, fz.inputs['Factor']); Lk(colout, fz.inputs['A'])
        fz.inputs['B'].default_value = (*(WICE if ice else ICECOL), 1); colout = fz.outputs['Result']
        rf = Nn.new('ShaderNodeMapRange'); Lk(mask, rf.inputs['Value']); rf.inputs['To Min'].default_value = rough; rf.inputs['To Max'].default_value = 0.12 if ice else 0.33
        Lk(rf.outputs['Result'], b.inputs['Roughness'])
    Lk(colout, b.inputs['Base Color'])
    # fingerprints: one whorl per Voronoi cell, only in some cells, fading at the edge of the press
    vo = Nn.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 55; vo.inputs['Randomness'].default_value = 0.9; Lk(v, vo.inputs['Vector'])
    sub = Nn.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; Lk(v, sub.inputs[0]); Lk(vo.outputs['Position'], sub.inputs[1])
    wv = Nn.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'; wv.inputs['Scale'].default_value = 250; wv.inputs['Distortion'].default_value = 3.0
    wv.inputs['Detail'].default_value = 2; wv.inputs['Detail Scale'].default_value = 1.5; Lk(sub.outputs['Vector'], wv.inputs['Vector'])
    pm = Nn.new('ShaderNodeMapRange'); pm.inputs['From Min'].default_value = 0.7; pm.inputs['From Max'].default_value = 0.3
    Lk(vo.outputs['Distance'], pm.inputs['Value'])
    sel = Nn.new('ShaderNodeSeparateColor'); Lk(vo.outputs['Color'], sel.inputs['Color'])
    gt = Nn.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.3; Lk(sel.outputs['Red'], gt.inputs[0])
    p1 = Nn.new('ShaderNodeMath'); p1.operation = 'MULTIPLY'; Lk(pm.outputs['Result'], p1.inputs[0]); Lk(gt.outputs['Value'], p1.inputs[1])
    p2 = Nn.new('ShaderNodeMath'); p2.operation = 'MULTIPLY'; Lk(p1.outputs['Value'], p2.inputs[0]); Lk(wv.outputs['Fac'], p2.inputs[1])
    p3 = Nn.new('ShaderNodeMath'); p3.operation = 'MULTIPLY'; p3.inputs[1].default_value = 0.6 * prints; Lk(p2.outputs['Value'], p3.inputs[0])
    vd = Nn.new('ShaderNodeTexVoronoi'); vd.feature = 'SMOOTH_F1'; vd.inputs['Scale'].default_value = 110; Lk(v, vd.inputs['Vector'])
    d1 = Nn.new('ShaderNodeMath'); d1.operation = 'MULTIPLY'; d1.inputs[1].default_value = 1.6 * smudge; Lk(vd.outputs['Distance'], d1.inputs[0])
    gr = Nn.new('ShaderNodeTexNoise'); gr.inputs['Scale'].default_value = 1400; gr.inputs['Detail'].default_value = 3; Lk(v, gr.inputs['Vector'])
    g1 = Nn.new('ShaderNodeMath'); g1.operation = 'MULTIPLY'; g1.inputs[1].default_value = 0.035; Lk(gr.outputs['Fac'], g1.inputs[0])
    s1 = Nn.new('ShaderNodeMath'); s1.operation = 'ADD'; Lk(p3.outputs['Value'], s1.inputs[0]); Lk(d1.outputs['Value'], s1.inputs[1])
    s2 = Nn.new('ShaderNodeMath'); s2.operation = 'ADD'; Lk(s1.outputs['Value'], s2.inputs[0]); Lk(g1.outputs['Value'], s2.inputs[1])
    bp = Nn.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.003
    Lk(s2.outputs['Value'], bp.inputs['Height']); Lk(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def plain(name, col, rough=0.5, sheen=0.0, coat=0.0, emit=0.0, ecol=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; PBS[name] = b
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Coat Weight'].default_value = coat
    if emit: b.inputs['Emission Color'].default_value = (*(ecol or col), 1); b.inputs['Emission Strength'].default_value = emit
    return m

def grad_mat(name, stops, zmin, zmax, bump=0.15, night=None):
    """painted paper / painted backdrop: colour by object z. night: a second set of stops mixed in by PBS[name+'_n'] factor."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; Nn = nt.nodes; Lk = nt.links.new; b = Nn['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.92; PBS[name] = b
    tc = Nn.new('ShaderNodeTexCoord'); sz = Nn.new('ShaderNodeSeparateXYZ'); Lk(tc.outputs['Object'], sz.inputs['Vector'])
    mr = Nn.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = zmin; mr.inputs['From Max'].default_value = zmax; Lk(sz.outputs['Z'], mr.inputs['Value'])
    def ramp(st):
        cr = Nn.new('ShaderNodeValToRGB'); Lk(mr.outputs['Result'], cr.inputs['Fac'])
        cr.color_ramp.elements[0].position, cr.color_ramp.elements[0].color = st[0][0], (*st[0][1], 1)
        cr.color_ramp.elements[1].position, cr.color_ramp.elements[1].color = st[-1][0], (*st[-1][1], 1)
        for pos, c in st[1:-1]:
            e = cr.color_ramp.elements.new(pos); e.color = (*c, 1)
        return cr.outputs['Color']
    col = ramp(stops)
    if night:
        mx = Nn.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = 0.0
        Lk(col, mx.inputs['A']); Lk(ramp(night), mx.inputs['B']); col = mx.outputs['Result']; PBS[name + '_n'] = mx
    wv = Nn.new('ShaderNodeTexWave'); wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 9; wv.inputs['Distortion'].default_value = 6; wv.inputs['Detail'].default_value = 4
    Lk(tc.outputs['Object'], wv.inputs['Vector'])
    mx2 = Nn.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; mx2.blend_type = 'MULTIPLY'; mx2.inputs['Factor'].default_value = 0.05
    Lk(col, mx2.inputs['A']); Lk(wv.outputs['Color'], mx2.inputs['B']); Lk(mx2.outputs['Result'], b.inputs['Base Color'])
    nz = Nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 300; Lk(tc.outputs['Object'], nz.inputs['Vector'])
    bp = Nn.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; Lk(nz.outputs['Fac'], bp.inputs['Height']); Lk(bp.outputs['Normal'], b.inputs['Normal'])
    return m
def wood_mat():
    m = bpy.data.materials.new('wood'); m.use_nodes = True; nt = m.node_tree; Nn = nt.nodes; Lk = nt.links.new; b = Nn['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.45; b.inputs['Coat Weight'].default_value = 0.2
    tc = Nn.new('ShaderNodeTexCoord'); mp = Nn.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 12, 1); Lk(tc.outputs['Object'], mp.inputs['Vector'])
    wv = Nn.new('ShaderNodeTexWave'); wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 6; wv.inputs['Distortion'].default_value = 7; wv.inputs['Detail'].default_value = 5
    Lk(mp.outputs['Vector'], wv.inputs['Vector'])
    cr = Nn.new('ShaderNodeValToRGB'); Lk(wv.outputs['Fac'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].color = (0.20, 0.10, 0.045, 1); cr.color_ramp.elements[1].color = (0.42, 0.24, 0.11, 1)
    Lk(cr.outputs['Color'], b.inputs['Base Color'])
    return m
def felt_mat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; Nn = nt.nodes; Lk = nt.links.new; b = Nn['Principled BSDF']
    b.inputs['Roughness'].default_value = 1.0; b.inputs['Sheen Weight'].default_value = 1.0; b.inputs['Sheen Roughness'].default_value = 0.35
    b.inputs['Sheen Tint'].default_value = (0.35, 0.35, 0.45, 1); b.inputs['Specular IOR Level'].default_value = 0.2
    tc = Nn.new('ShaderNodeTexCoord'); nz = Nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900; nz.inputs['Detail'].default_value = 6
    Lk(tc.outputs['Object'], nz.inputs['Vector'])
    cr = Nn.new('ShaderNodeValToRGB'); Lk(nz.outputs['Fac'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].color = (*[c * 0.7 for c in col], 1); cr.color_ramp.elements[1].color = (*[c * 1.4 for c in col], 1)
    Lk(cr.outputs['Color'], b.inputs['Base Color'])
    bp = Nn.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.002
    Lk(nz.outputs['Fac'], bp.inputs['Height']); Lk(bp.outputs['Normal'], b.inputs['Normal'])
    return m

M_GRASS = clay('grass', (0.13, 0.36, 0.07), rough=0.55, prints=0.6, frost=True)
M_DIRT = clay('dirt', (0.22, 0.12, 0.06), rough=0.6, prints=0.4)
M_YEL = clay('yellow', (0.85, 0.62, 0.05), rough=0.45)
M_BALL = clay('ball', (0.85, 0.20, 0.04), rough=0.42, prints=0.9, smudge=1.0, bump=0.42, boil=4.0)     # lighter prints on the face (owner note)
M_WHITE = clay('white', (0.86, 0.85, 0.80), rough=0.4, prints=0.6, boil=3.0)
M_EYE = clay('eye', (0.92, 0.92, 0.90), rough=0.3, prints=0.3, smudge=0.4, bump=0.2, boil=3.0, emit=0.0001)
M_PUP = plain('pupil', (0.01, 0.01, 0.012), rough=0.15, coat=0.6)
M_MOUTH = clay('mouth', (0.06, 0.02, 0.015), rough=0.4, prints=0.2, boil=3.0)
M_TONGUE = clay('tongue', (0.85, 0.30, 0.38), rough=0.3, prints=0.2, boil=3.0)
M_TRUNK = clay('trunk', (0.24, 0.12, 0.05), rough=0.6, frost=True)
M_LEAF = clay('leaf', (0.07, 0.25, 0.05), rough=0.55, frost=True)
M_LEAF2 = clay('leaf2', (0.12, 0.33, 0.06), rough=0.55, frost=True)
M_TUFT = clay('tuft', (0.16, 0.42, 0.08), rough=0.55, prints=0.2, frost=True)
M_PINK = clay('pink', (0.85, 0.35, 0.50), rough=0.45, frost=True)
M_PETAL = clay('petal', (0.88, 0.86, 0.80), rough=0.45)
M_SUN = clay('sun', (0.95, 0.68, 0.10), rough=0.45, emit=0.35)
M_MOON = clay('moon', (0.78, 0.77, 0.66), rough=0.5, prints=0.5, emit=0.0001)
M_CRATER = clay('crater', (0.55, 0.54, 0.47), rough=0.55, prints=0.3)
M_ROCK = clay('rock', (0.30, 0.29, 0.28), rough=0.6, frost=True)
M_COTTON = plain('cotton', (0.92, 0.92, 0.93), rough=0.95, sheen=1.0)
M_STAR = plain('star', (1.0, 0.95, 0.8), rough=0.4, emit=8.0)
M_LAKE = clay('lake', (0.06, 0.26, 0.55), rough=0.22, prints=0.3, smudge=0.6, ice=(0.075, 0.046))
M_POND = clay('pond', (0.06, 0.28, 0.58), rough=0.22, prints=0.3, smudge=0.6, ice=(0.031, 0.022))
M_RED = clay('red', (0.75, 0.06, 0.04), rough=0.42)
M_FACE = clay('face', (0.90, 0.88, 0.82), rough=0.4, prints=0.4)
M_BLACK = clay('black', (0.03, 0.03, 0.035), rough=0.4, prints=0.2)
M_TAN = clay('tan', (0.72, 0.45, 0.20), rough=0.55)
M_SCOOP = clay('scoop', (0.92, 0.55, 0.62), rough=0.4)
M_TEAL = clay('teal', (0.08, 0.45, 0.58), rough=0.45, boil=3.0)
M_PAGE = clay('page', (0.90, 0.89, 0.84), rough=0.5, prints=0.4)
M_GREY = clay('grey', (0.42, 0.42, 0.40), rough=0.5)
M_DUCK = clay('duck', (0.95, 0.72, 0.08), rough=0.45, boil=2.0)
M_BEAK = clay('beak', (0.95, 0.38, 0.05), rough=0.45, boil=2.0)

# ---------------------------------------------------------------- helpers (as clay.py)
def mesh_obj(name, bm, mat=None, smooth_=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth_:
        for p in me.polygons: p.use_smooth = True
    o = link(bpy.data.objects.new(name, me))
    if mat: o.data.materials.append(mat)
    return o
def lumpy(bm, amp, freq, seed):
    for v in bm.verts:
        n = v.normal.copy() if v.normal.length > 0 else Vector((0, 0, 1))
        v.co += n * amp * mnoise.noise(v.co * freq + Vector((seed, seed * 1.3, seed * 0.7)))
BOILS = []          # (empty, amount)
def boil_mod(o, strength, size=0.012, amt=1.0, levels=2):
    sd = o.modifiers.new('sub', 'SUBSURF'); sd.levels = levels; sd.render_levels = levels
    tx = bpy.data.textures.new(o.name + '_bt', 'CLOUDS'); tx.noise_scale = size; tx.noise_depth = 2
    e = link(bpy.data.objects.new(o.name + '_be', None)); e.parent = o
    d = o.modifiers.new('boil', 'DISPLACE'); d.texture = tx; d.texture_coords = 'OBJECT'; d.texture_coords_object = e
    d.strength = strength; d.mid_level = 0.5
    BOILS.append((e, amt)); return o
def blob(name, r, mat, loc, scale=(1, 1, 1), amp=0.08, seed=None, seg=24, boil=0.0004, levels=1, parent=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    bm.normal_update(); lumpy(bm, r * amp, 3.0 / r, rng.random() * 100 if seed is None else seed)
    o = mesh_obj(name, bm, mat); o.location = loc; o.scale = scale
    if parent: o.parent = parent
    if boil: boil_mod(o, boil, size=max(0.004, r * 0.6), levels=levels)
    return o
def cone(name, r0, r1, h, mat, loc, rot=(0, 0, 0), seg=12, amp=0.0, parent=None):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=h)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, h / 2))
    if amp: bm.normal_update(); lumpy(bm, amp, 2.0 / max(r0, 0.002), rng.random() * 100)
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = rot
    if parent: o.parent = parent
    return o
def torus(name, R_, r_, mat, loc, rot=(0, 0, 0), su=96, sv=24, amp=0.0, flat=1.0, parent=None):
    bm = bmesh.new(); rows = []
    for i in range(su):
        u = 2 * math.pi * i / su; row = []
        for j in range(sv):
            w = 2 * math.pi * j / sv
            row.append(bm.verts.new(((R_ + r_ * math.cos(w)) * math.cos(u), (R_ + r_ * math.cos(w)) * math.sin(u), r_ * math.sin(w) * flat)))
        rows.append(row)
    for i in range(su):
        for j in range(sv):
            bm.faces.new((rows[i][j], rows[(i + 1) % su][j], rows[(i + 1) % su][(j + 1) % sv], rows[i][(j + 1) % sv]))
    bm.normal_update()
    if amp: lumpy(bm, amp, 2.5 / r_, rng.random() * 100)
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = rot
    if parent: o.parent = parent
    return o
def slabbox(name, sx, sy, sz, mat, loc, amp=0.0, rot=(0, 0, 0), parent=None, levels=2):
    """a rounded clay block (a cube smoothed by subsurf), sx/sy/sz are half sizes"""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
    for v in bm.verts: v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    bm.normal_update()
    if amp: lumpy(bm, amp, 1.5 / max(min(sx, sy, sz), 0.002), rng.random() * 100)
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = rot
    sd = o.modifiers.new('sub', 'SUBSURF'); sd.levels = levels; sd.render_levels = levels
    if parent: o.parent = parent
    return o
def empty(name, loc=(0, 0, 0), parent=None):
    e = link(bpy.data.objects.new(name, None)); e.location = loc
    if parent: e.parent = parent
    return e
def tube_curve(name, pts, r, mat, parent=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, q in enumerate(pts): sp.points[i].co = (*q, 1)
    o = link(bpy.data.objects.new(name, cu)); o.data.materials.append(mat)
    if parent: o.parent = parent
    return o
def set_curve(o, pts):
    sp = o.data.splines[0]
    for i, q in enumerate(pts): sp.points[i].co = (*q, 1)

# ================================================================ SET A: the tabletop world
CUR[0] = 'A'
RX, RY, CY = 0.25, 0.19, 0.035
LAKE = (V3(0.03, 0.085, 0), 0.075, 0.046); POND = (V3(-0.095, -0.025, 0), 0.031, 0.022)
def water_r(x, y, w): c, rx, ry = w; return math.hypot((x - c.x) / rx, (y - c.y) / ry)
def build_slab():
    bm = bmesh.new(); NA, NR = 176, 64; rings = []
    for k in range(1, NR + 1):
        s = (k / NR) ** 1.15; ring = []
        for i in range(NA):
            t = 2 * math.pi * i / NA; x, y = RX * s * math.cos(t), CY + RY * s * math.sin(t)
            z = 0.0016 * mnoise.noise(V3(x * 22, y * 22, 3.1)) + 0.0006 * mnoise.noise(V3(x * 80, y * 80, 7.7))
            for w in (LAKE, POND):
                rr = water_r(x, y, w); z += -0.007 * smooth(1.12, 0.8, rr) + 0.0016 * math.exp(-((rr - 1.17) / 0.12) ** 2)
            e = smooth(0.93, 1.0, s); z -= 0.006 * e * e
            ring.append((x, y, z))
        rings.append(ring)
    for k in range(1, 6):
        f = k / 5; z = -0.006 - (0.03 - 0.006) * f; bul = 1.0 + 0.015 * math.sin(math.pi * f)
        rings.append([(RX * bul * math.cos(2 * math.pi * i / NA), CY + RY * bul * math.sin(2 * math.pi * i / NA), z) for i in range(NA)])
    vv = [[bm.verts.new(p) for p in r] for r in rings]
    c = bm.verts.new((0, CY, 0.0))
    for i in range(NA): bm.faces.new((c, vv[0][i], vv[0][(i + 1) % NA]))
    for k in range(len(vv) - 1):
        for i in range(NA):
            f = bm.faces.new((vv[k][i], vv[k][(i + 1) % NA], vv[k + 1][(i + 1) % NA], vv[k + 1][i])); f.material_index = 1 if k >= NR - 1 else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj('slab', bm)
    for m_ in (M_GRASS, M_DIRT): o.data.materials.append(m_)
    zs = [p.normal.z for p in o.data.polygons if p.material_index == 0]
    if sum(zs) < 0: o.data.flip_normals()
    boil_mod(o, 0.0005, size=0.01, amt=0.25, levels=1)
    return o
slab = build_slab()
table = link(bpy.data.objects.new('table', bpy.data.meshes.new('table')))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.5); bm.to_mesh(table.data); bm.free()
table.location = (0, 0.4, -0.03); table.data.materials.append(wood_mat())
def water(name, w, mat):
    c, rx, ry = w; bm = bmesh.new(); NA = 64; rings = []
    for k in range(1, 9):
        s = k / 8 * 1.04; rings.append([bm.verts.new((rx * s * math.cos(2 * math.pi * i / NA), ry * s * math.sin(2 * math.pi * i / NA), 0)) for i in range(NA)])
    cc = bm.verts.new((0, 0, 0))
    for i in range(NA): bm.faces.new((cc, rings[0][i], rings[0][(i + 1) % NA]))
    for k in range(len(rings) - 1):
        for i in range(NA): bm.faces.new((rings[k][i], rings[k][(i + 1) % NA], rings[k + 1][(i + 1) % NA], rings[k + 1][i]))
    for v in bm.verts: v.co.z = 0.0004 * mnoise.noise(v.co * 90)
    o = mesh_obj(name, bm, mat); o.location = c + V3(0, 0, -0.0026); boil_mod(o, 0.0002, size=0.01, amt=0.3, levels=1); return o
lake = water('lake', LAKE, M_LAKE); pond = water('pond', POND, M_POND)

# ball home spots (kept clear of tufts and trees)
BR = 0.018; GND = BR + 0.0008
HOME = V3(0.0, -0.075, GND); LAKESIDE = V3(-0.055, 0.005, GND)
KEEP = [(HOME, 0.04), (V3(0.05, -0.065, 0), 0.025), (V3(-0.04, -0.07, 0), 0.02), (V3(-0.06, -0.06, 0), 0.028), (LAKESIDE, 0.03)]
def clear_spot(x, y, d=0.0):
    if water_r(x, y, LAKE) < 1.3 or water_r(x, y, POND) < 1.5: return False
    return all((V3(x, y, 0) - c).length > r + d for c, r in KEEP)
# trees
for i, (x, y, h, s) in enumerate([(-0.17, 0.125, 0.06, 1.05), (0.185, 0.13, 0.075, 1.2), (0.215, 0.02, 0.04, 0.8), (-0.205, 0.03, 0.035, 0.75)]):
    tr = cone(f'trunk{i}', 0.0065 * s, 0.0042 * s, h, M_TRUNK, (x, y, -0.002), rot=(R(rng.uniform(-5, 5)), R(rng.uniform(-5, 5)), 0), amp=0.0006)
    boil_mod(tr, 0.0003, size=0.006)
    for j in range(4):
        rr = 0.024 * s * rng.uniform(0.75, 1.0)
        blob(f'leaf{i}{j}', rr, M_LEAF if j % 2 else M_LEAF2, (x + rng.uniform(-0.014, 0.014) * s, y + rng.uniform(-0.01, 0.01) * s, h + rng.uniform(0.0, 0.026) * s),
             scale=(1, 1, 0.85), amp=0.12, boil=0.0006, levels=1)
# flowers
for i, (x, y) in enumerate([(-0.085, 0.05), (0.13, 0.03), (0.12, -0.06), (-0.14, -0.085), (0.0, 0.16), (-0.1, 0.13), (0.09, -0.11)]):
    if not clear_spot(x, y): continue
    cone(f'stem{i}', 0.0011, 0.0008, 0.016, M_TUFT, (x, y, -0.001), rot=(R(rng.uniform(-10, 10)), R(rng.uniform(-10, 10)), 0))
    top = V3(x, y, 0.015); pm = M_PINK if i % 2 else M_PETAL
    for k in range(5):
        an = 2 * math.pi * k / 5
        blob(f'pet{i}{k}', 0.0026, pm, top + V3(0.0028 * math.cos(an), 0.0028 * math.sin(an), 0), scale=(1, 1, 0.45), seg=12, boil=0)
    blob(f'fc{i}', 0.0019, M_YEL, top + V3(0, 0, 0.0008), seg=12, boil=0)
for i in range(12):
    x, y = rng.uniform(-0.2, 0.2), rng.uniform(-0.13, 0.18)
    if (x / RX) ** 2 + ((y - CY) / RY) ** 2 > 0.8 or not clear_spot(x, y, 0.01): continue
    blob(f'peb{i}', rng.uniform(0.003, 0.0055), M_ROCK, (x, y, 0.001), scale=(1, 0.85, 0.6), seg=16, boil=0)
n = 0
while n < 85:
    x, y = rng.uniform(-0.23, 0.23), rng.uniform(-0.15, 0.21)
    if (x / RX) ** 2 + ((y - CY) / RY) ** 2 > 0.84 or not clear_spot(x, y, 0.008): continue
    for k in range(3):
        cone(f'tuft{n}_{k}', 0.0013, 0.0001, rng.uniform(0.004, 0.0075), M_TUFT, (x + rng.uniform(-0.0025, 0.0025), y + rng.uniform(-0.0025, 0.0025), -0.0005),
             rot=(R(rng.uniform(-25, 25)), R(rng.uniform(-25, 25)), 0), seg=6)
    n += 1

# paper sky (day and night paint), cotton clouds, clay Sun and Moon, pinhead stars
SKYR, SKYC = 0.72, V3(0, -0.25, 0)
M_SKY = grad_mat('sky', [(0.0, (0.62, 0.74, 0.80)), (1.0, (0.12, 0.32, 0.70))], 0.0, 0.3,
                 night=[(0.0, (0.018, 0.022, 0.05)), (1.0, (0.004, 0.006, 0.02))])
bm = bmesh.new(); cols = []
for i in range(49):
    an = R(18 + 144 * i / 48); cols.append([bm.verts.new((SKYR * math.cos(an), SKYC.y + SKYR * math.sin(an), -0.03 + 0.75 * j / 12)) for j in range(13)])
for i in range(48):
    for j in range(12): bm.faces.new((cols[i][j], cols[i + 1][j], cols[i + 1][j + 1], cols[i][j + 1]))
sky = mesh_obj('sky', bm, M_SKY)
def on_sky(x, z, inset=0.012):
    y = SKYC.y + math.sqrt(max(0.0, SKYR ** 2 - x * x)) - inset; return V3(x, y, z)
for c_, (x, z, s) in enumerate([(-0.17, 0.16, 0.8), (0.17, 0.12, 0.75), (-0.02, 0.40, 0.6)]):
    for k in range(6):
        p = on_sky(x + rng.uniform(-0.05, 0.05) * s, z + rng.uniform(-0.012, 0.015) * s, 0.05)
        blob(f'cloud{c_}{k}', 0.03 * s * rng.uniform(0.6, 1.0), M_COTTON, p, scale=(1.3, 0.5, 0.75), amp=0.25, seg=20, boil=0)
SUNP = on_sky(0.035, 0.24, 0.03)
PROP[0] = 'sun'
sunrig = empty('sunrig', SUNP)
blob('sunbody', 0.04, M_SUN, (0, 0, 0), scale=(1, 0.35, 1), boil=0, parent=sunrig)
for k in range(10):
    an = 2 * math.pi * k / 10
    o = cone(f'ray{k}', 0.0068, 0.0017, 0.025, M_SUN, (0.045 * math.cos(an), 0, 0.045 * math.sin(an)), seg=8, parent=sunrig)
    o.rotation_euler = Euler((0, 0, 0)); o.rotation_euler.rotate_axis('Y', math.pi / 2 - an)
PROP[0] = 'puff'
PUFF = []
for k in range(8):
    an = 2 * math.pi * k / 8 + rng.uniform(-0.3, 0.3)
    o = blob(f'puff{k}', 0.014 * rng.uniform(0.7, 1.1), M_COTTON, SUNP + V3(0, -0.01, 0), scale=(1, 0.6, 1), amp=0.25, seg=16, boil=0)
    PUFF.append((o, V3(math.cos(an), 0, math.sin(an))))
PROP[0] = None
MOONP = on_sky(-0.15, 0.30, 0.025)
moon = blob('moon', 0.026, M_MOON, MOONP, scale=(1, 0.3, 1), boil=0)
for k, (dx, dz, rr) in enumerate([(-0.008, 0.007, 0.0055), (0.009, -0.004, 0.0045), (-0.002, -0.011, 0.0035)]):
    blob(f'crater{k}', rr, M_CRATER, MOONP + V3(dx, -0.0085, dz), scale=(1, 0.3, 1), seg=12, boil=0)
PROP[0] = 'stars'
for k in range(70):
    x = rng.uniform(-0.5, 0.5); z = rng.uniform(0.12, 0.70)
    if (V3(x, 0, z) - V3(MOONP.x, 0, MOONP.z)).length < 0.04: continue
    blob(f'star{k}', rng.uniform(0.0012, 0.0024), M_STAR, on_sky(x, z, 0.004), seg=8, amp=0, boil=0)
PROP[0] = None

# ---- props
# stopwatch (faces the camera, -y)
PROP[0] = 'watch'
WATCHP = V3(0.045, -0.07, 0.0)
watch = empty('watch', WATCHP)
wbody = empty('wbody', (0, 0, 0.0185), watch)
o = cone('wcase', 0.0155, 0.0155, 0.0075, M_RED, (0, 0.0037, 0), rot=(R(90), 0, 0), seg=32, parent=wbody); boil_mod(o, 0.0002, size=0.005, levels=2)
o = cone('wface', 0.0128, 0.0128, 0.0012, M_FACE, (0, -0.0035, 0), rot=(R(90), 0, 0), seg=32, parent=wbody); boil_mod(o, 0.0001, size=0.005, levels=2)
torus('wrim', 0.0138, 0.0014, M_RED, (0, -0.0042, 0), rot=(R(90), 0, 0), sv=10, su=48, parent=wbody)
for k in range(12):
    an = 2 * math.pi * k / 12
    blob(f'wtick{k}', 0.0009 if k % 3 else 0.0013, M_BLACK, (0.0105 * math.sin(an), -0.0049, 0.0105 * math.cos(an)), scale=(1, 0.5, 1), seg=8, boil=0, parent=wbody)
hpiv = empty('hpiv', (0, -0.0052, 0), wbody)
o = cone('hand', 0.0011, 0.0004, 0.0095, M_BLACK, (0, 0, 0), seg=8, parent=hpiv)
blob('hub', 0.0015, M_BLACK, (0, 0, 0), scale=(1, 0.6, 1), seg=10, boil=0, parent=hpiv)
cone('crown', 0.0022, 0.0022, 0.004, M_GREY, (0, 0, 0.0152), seg=12, parent=wbody)
crownb = blob('crownb', 0.0032, M_GREY, (0, 0, 0.0198), scale=(1, 1, 0.55), seg=12, boil=0, parent=wbody)
for k, sx in enumerate((-1, 1)):
    blob(f'wfoot{k}', 0.0045, M_RED, (0.008 * sx, 0.002, -0.0155), scale=(1, 1.2, 0.6), seg=12, boil=0, parent=wbody)
DINGS = []
for k, an in enumerate((-50, 0, 50)):
    d = V3(math.sin(R(an)), 0, math.cos(R(an)))
    o = cone(f'ding{k}', 0.0011, 0.0011, 0.0065, M_YEL, d * 0.026 + V3(0, -0.003, 0), seg=8, parent=wbody)
    o.rotation_euler = (0, R(an), 0); DINGS.append(o)
# ice-cream cone stuck point-down in the grass, left of the Ball
PROP[0] = 'icecream'
ICEP = V3(-0.034, -0.088, -0.004)
cone('cone', 0.0006, 0.0085, 0.024, M_TAN, ICEP + V3(0, 0, -0.004), seg=16, amp=0.0003)
scoop = blob('scoop', 0.0098, M_SCOOP, ICEP + V3(0, 0, 0.022), scale=(1, 1, 0.9), boil=0.0002)
blob('drip', 0.0035, M_SCOOP, ICEP + V3(0.004, -0.007, 0.016), scale=(0.8, 0.8, 1.3), seg=12, boil=0)
blob('cherry', 0.0036, M_RED, ICEP + V3(0.001, 0, 0.0325), seg=14, boil=0)
# thermometer, right of the Ball
PROP[0] = 'thermo'
THP = V3(0.052, -0.066, 0)
slabbox('thboard', 0.0105, 0.0032, 0.045, M_FACE, THP + V3(0, 0.003, 0.043), amp=0.0004)
cone('thtube', 0.0042, 0.0042, 0.072, M_WHITE, THP + V3(0, -0.0012, 0.012), seg=16)
blob('thbulb', 0.0068, M_RED, THP + V3(0, -0.002, 0.0085), seg=20, boil=0.0002)
THCOL0 = THP + V3(0, -0.0042, 0.012)
thcol = cone('thcol', 0.0024, 0.0024, 1.0, M_RED, THCOL0, seg=12)
thbead = blob('thbead', 0.0026, M_RED, THCOL0, seg=12, boil=0)
for k in range(9):
    cone(f'thtick{k}', 0.0007, 0.0007, 0.0042, M_BLACK, THP + V3(0.0052, -0.0025, 0.02 + 0.0065 * k), rot=(0, R(90), 0), seg=6)
# desk calendar (an A-frame), left of the Ball: pages hinged at the top flip over to the back; tally sticks count the days
PROP[0] = 'calendar'
CALP = V3(-0.062, -0.058, 0)
cal = empty('cal', CALP); cal.rotation_euler = (0, 0, R(18))
CT = R(16); CH_ = 0.034
slabbox('calback', 0.0145, 0.0012, CH_ / 2, M_RED, (0, math.sin(CT) * CH_ / 2 + 0.001, math.cos(CT) * CH_ / 2), rot=(CT, 0, 0), parent=cal)
calhinge = empty('calhinge', (0, -0.0003 - 0.0096, CH_ * math.cos(CT) + 0.0004), cal)
for k, sx in enumerate((-0.007, 0.007)): torus(f'calring{k}', 0.0022, 0.0006, M_GREY, (sx, 0.001, 0.001), rot=(0, R(90), 0), su=24, sv=8, parent=calhinge)
PAGES = []
for k in range(4):            # front page first: blank, then I, II, III
    pv = empty(f'pagepiv{k}', (0, 0.0032 * k, 0), calhinge)
    pg = slabbox(f'page{k}', 0.0135, 0.0005, CH_ / 2 - 0.001, M_PAGE, (0, 0, -CH_ / 2), parent=pv, levels=1)
    pg.rotation_euler = (-CT, 0, 0); pg.location = (0, -math.sin(CT) * CH_ / 2, -math.cos(CT) * CH_ / 2)
    slabbox(f'pagetop{k}', 0.0135, 0.0007, 0.0028, M_RED, (0, -0.0008, CH_ / 2 - 0.004), parent=pg, levels=1)
    for j in range(3 - k if False else k):
        o = cone(f'tally{k}{j}', 0.0011, 0.0011, 0.016, M_BLACK, ((j - (k - 1) / 2) * 0.0055, -0.0011, -0.011), seg=8, parent=pg)
        o.rotation_euler = (0, R(rng.uniform(-6, 6)), 0)
    PAGES.append(pv)
# scarf (teal, white stripes) parented to the Ball later
PROP[0] = 'duck'
def duck(name, loc, parent=None):
    rig = empty(name, loc, parent)
    blob(name + 'body', 0.012, M_DUCK, (0, 0, 0.0075), scale=(1.35, 0.95, 0.62), boil=0.0002, parent=rig)
    hd = blob(name + 'head', 0.0072, M_DUCK, (-0.0145, 0, 0.0105), boil=0.0002, parent=rig)
    o = cone(name + 'beak', 0.0032, 0.0008, 0.0068, M_BEAK, (-0.0205, 0, 0.0095), seg=10, parent=rig); o.rotation_euler = (0, R(-95), 0); o.scale = (1, 0.8, 1)
    for s in (-1, 1):
        blob(name + f'wing{s}', 0.0062, M_DUCK, (0.0005, 0.0115 * s, 0.0065), scale=(1.5, 0.9, 0.35), seg=12, boil=0, parent=rig)
        blob(name + f'deye{s}', 0.0013, M_PUP, (-0.0175, 0.0042 * s, 0.0142), seg=8, boil=0, parent=rig)
        blob(name + f'deyw{s}', 0.0021, M_EYE, (-0.0165, 0.0036 * s, 0.0138), seg=10, boil=0, parent=rig)
    blob(name + 'tail', 0.004, M_DUCK, (0.016, 0, 0.0115), scale=(1, 0.8, 0.6), seg=10, boil=0, parent=rig)
    return rig
duckA = duck('duckA', LAKE[0] + V3(-0.06, 0.0, -0.002))
PROP[0] = None

# ---- the Ball
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=BR); bm.normal_update(); lumpy(bm, 0.0005, 160, 3.3)
ball = mesh_obj('ball', bm, M_BALL); boil_mod(ball, 0.00045, size=0.008, amt=3.0, levels=2)
headband = torus('headband', BR * 0.985, 0.0021, M_WHITE, (0, 0, 0), rot=(R(-62), 0, 0), sv=12, amp=0.0003, flat=0.55, parent=ball)
boil_mod(headband, 0.0002, size=0.004, amt=3.0)
EYES = []
for side in (-1, 1):
    a_, e_ = R(23) * side, R(17)
    c = Vector((math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_))) * BR * 0.9
    em = empty(f'eye{side}', c, ball)
    w = blob(f'white{side}', 0.0062, M_EYE, (0, 0, 0), amp=0.03, seg=32, boil=0.00012); w.parent = em
    p = blob(f'pupil{side}', 0.0031, M_PUP, (0, 0, 0), amp=0.0, seg=24, boil=0); p.parent = em; p.scale = (1, 1, 0.4)
    p.rotation_mode = 'QUATERNION'
    EYES.append((em, p, c.normalized(), side))
def face_dir(az, el): return Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
cu = bpy.data.curves.new('mouth', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0009; cu.bevel_resolution = 4
sp_ = cu.splines.new('NURBS'); sp_.points.add(6); sp_.use_endpoint_u = True; sp_.order_u = 4
for k in range(7):
    u = (k / 6) * 2 - 1
    sp_.points[k].co = (*(face_dir(R(17) * u, R(-24) + R(11) * u * u) * BR), 1)
mouth = link(bpy.data.objects.new('mouth', cu)); mouth.data.materials.append(M_MOUTH); mouth.parent = ball
MD = face_dir(0, R(-22))
omouth = torus('omouth', 0.0034, 0.0011, M_MOUTH, MD * BR * 0.99, sv=10, su=32, parent=ball)
omouth.rotation_euler = Vector((0, 0, 1)).rotation_difference(MD).to_euler(); omouth.scale = (0.8, 1.0, 1)
ohole = blob('ohole', 0.0029, M_PUP, MD * BR * 0.93, scale=(0.8, 1, 0.35), seg=12, boil=0, parent=ball)
ohole.rotation_euler = omouth.rotation_euler
tongue = blob('tongue', 0.0045, M_TONGUE, (0, 0, 0), scale=(0.75, 1, 0.4), seg=16, boil=0.0001, parent=ball)
PROP[0] = 'scarf'
scarf = empty('scarf', (0, 0, -0.33 * BR), ball)
torus('scarfring', BR * 0.96, 0.0032, M_TEAL, (0, 0, 0), sv=12, su=64, amp=0.0003, flat=0.75, parent=scarf)
for k, dz in enumerate((-0.0016, 0.0016)):
    torus(f'scarfstripe{k}', BR * 0.96 + 0.0017, 0.0009, M_WHITE, (0, 0, dz), sv=8, su=64, flat=0.8, parent=scarf)
for k, (az, ln) in enumerate([(R(-38), 0.0105), (R(-24), 0.0085)]):
    o = blob(f'scarftail{k}', 0.0042, M_TEAL, (math.sin(az) * BR * 1.02, -math.cos(az) * BR * 1.02, -0.007 - 0.002 * k), scale=(0.75, 0.45, ln / 0.0042 * 0.55), seg=14, boil=0, parent=scarf)
    o.rotation_euler = (R(8), R(-12 + 20 * k), az)
PROP[0] = None
BALLPARTS = [o for o in S.objects if o.parent == ball or (o.parent and o.parent.parent == ball) or o == ball]

# ================================================================ SET B: black-felt space table
CUR[0] = 'B'
OB = V3(3.0, 0, 0)
M_FELT = felt_mat('felt', (0.012, 0.012, 0.018))
M_CHALK = clay('chalk', (0.78, 0.78, 0.74), rough=0.95, prints=0.0, smudge=0.4, bump=0.8, ss=0.0, sheen=0.0)
M_EARTH = clay('earth', (0.06, 0.24, 0.72), rough=0.42, prints=0.8)
M_LAND = clay('land', (0.16, 0.50, 0.12), rough=0.5, prints=0.6)
M_SNOW = clay('snow', (0.88, 0.91, 0.95), rough=0.4, prints=0.6)
M_SNOW2 = clay('snow2', (0.42, 0.62, 0.85), rough=0.35, prints=0.6)
M_PLUTO = clay('pluto', (0.70, 0.55, 0.42), rough=0.5, prints=0.8)
M_HEART = clay('heart', (0.93, 0.86, 0.74), rough=0.5, prints=0.4)
M_WIRE = plain('wire', (0.5, 0.5, 0.52), rough=0.3)
M_STRING = clay('string', (0.88, 0.80, 0.62), rough=0.8, prints=0.0, bump=0.3)
floorB = link(bpy.data.objects.new('feltfloor', bpy.data.meshes.new('feltfloor')))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0); bm.to_mesh(floorB.data); bm.free()
floorB.location = OB + V3(0, 0.4, 0); floorB.scale = (0.7, 1.0, 1); floorB.data.materials.append(M_FELT)
for k in range(110):                   # pinhead stars pushed into the felt (floor) and the felt wall
    if k < 55: p = OB + V3(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.0006)
    else: p = OB + V3(rng.uniform(-0.35, 0.35), 1.18, rng.uniform(0.0, 0.5))
    blob(f'fstar{k}', rng.uniform(0.0011, 0.0022), M_STAR, p, seg=8, amp=0, boil=0)
wallB = link(bpy.data.objects.new('feltwall', bpy.data.meshes.new('feltwall')))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5); bm.to_mesh(wallB.data); bm.free()
wallB.location = OB + V3(0, 1.19, 0.25); wallB.rotation_euler = (R(90), 0, 0); wallB.scale = (1.6, 1.2, 1); wallB.data.materials.append(M_FELT)
# top-down orbit table (shot 4)
PIN = OB + V3(0, 0.0, 0)
RO = 0.085
cone('pinshaft', 0.0012, 0.0012, 0.006, M_WIRE, PIN, seg=8)
blob('pinhead', 0.0055, M_GREY, PIN + V3(0, 0, 0.007), scale=(1, 1, 0.75), seg=16, boil=0.0001)
for k in range(30):                    # dashed chalk orbit
    an = 2 * math.pi * (k + 0.25) / 30
    o = slabbox(f'orbit{k}', 0.0052, 0.0009, 0.0003, M_CHALK, PIN + V3(RO * math.cos(an), RO * math.sin(an), 0.0004), rot=(0, 0, an + math.pi / 2), levels=1)
for k in range(14):                    # a small dashed ring where the Sun used to sit
    an = 2 * math.pi * k / 14
    slabbox(f'sunring{k}', 0.0034, 0.0008, 0.0003, M_CHALK, PIN + V3(0.024 * math.cos(an), 0.024 * math.sin(an), 0.0004), rot=(0, 0, an + math.pi / 2), levels=1)
streak = slabbox('streak', 0.5, 0.0024, 0.00035, M_CHALK, PIN, amp=0.0, levels=1)
def earth(name, r, frozen=False, face=V3(0, -1, 0)):
    rig = empty(name, (0, 0, 0))
    body = blob(name + 'b', r, M_SNOW2 if frozen else M_EARTH, (0, 0, 0), amp=0.05, seg=40, boil=0.0003, levels=2, parent=rig)
    lr = random.Random(5)
    for k in range(7):
        d = Vector((lr.uniform(-1, 1), lr.uniform(-1, 1), lr.uniform(-0.6, 0.6))).normalized()
        if d.dot(face) > 0.55: d = (d - face * 0.9).normalized()
        o = blob(name + f'land{k}', r * lr.uniform(0.32, 0.5), M_SNOW if frozen else M_LAND, d * r * 0.93, scale=(1, 1, 0.38), seg=16, boil=0, parent=rig)
        o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
    for s in (-1, 1):
        o = blob(name + f'cap{s}', r * 0.45, M_SNOW, V3(0, 0, s * r * 0.9), scale=(1, 1, 0.3), seg=16, boil=0, parent=rig)
    eyes = []
    side = face.cross(V3(0, 0, 1)) if abs(face.z) < 0.9 else V3(1, 0, 0)
    up = side.cross(face).normalized() if abs(face.z) < 0.9 else V3(0, 1, 0)
    for s in (-1, 1):
        c = (face * 0.93 + side.normalized() * 0.36 * s + up * 0.3).normalized() * r * 0.97
        em = empty(name + f'em{s}', c, rig)
        w = blob(name + f'ew{s}', r * 0.26, M_EYE, (0, 0, 0), amp=0.03, seg=20, boil=0.0001, parent=em)
        p = blob(name + f'ep{s}', r * 0.13, M_PUP, (0, 0, 0), amp=0, seg=16, boil=0, parent=em); p.scale = (1, 1, 0.4); p.rotation_mode = 'QUATERNION'
        eyes.append((em, p, c.normalized()))
    return rig, eyes
EARTH4, E4EYES = earth('earth4', 0.026, False, V3(0, 0, 1))
str_pin = tube_curve('strpin', [PIN + V3(0, 0, 0.006)] * 12, 0.0007, M_STRING)
str_earth = tube_curve('strearth', [PIN + V3(0, 0, 0.006)] * 12, 0.0007, M_STRING)
# side view (shot 10): frozen Earth on a wire drifts past little Pluto on a wire
OB2 = OB + V3(0, 0.75, 0)
EARTH10, E10EYES = earth('earth10', 0.03, True, V3(0, -1, 0)); EARTH10.scale = (1.2, 1.2, 1.2)
icicles = []
for k in range(6):
    an = R(-60 + 24 * k)
    icicles.append(cone(f'icicle{k}', 0.0026, 0.0003, 0.008 + 0.004 * (k % 2), M_SNOW2, (0.028 * math.sin(an), 0.004 * math.cos(an * 2), -0.024), rot=(R(180), 0, 0), seg=8, parent=EARTH10))
rodE = cone('rodE', 0.0011, 0.0011, 1.0, M_WIRE, (0, 0, 0), seg=8)
PLUTO = empty('pluto', (0, 0, 0)); PLUTO.scale = (1.4, 1.4, 1.4)
blob('plutob', 0.012, M_PLUTO, (0, 0, 0), amp=0.07, seg=32, boil=0.0002, parent=PLUTO)
for k, (dx, dz, rr) in enumerate([(-0.0028, -0.002, 0.0048), (0.0028, -0.002, 0.0048), (0, -0.0062, 0.0032)]):
    blob(f'heart{k}', rr, M_HEART, (dx, -0.0098, dz), scale=(1, 0.35, 1), seg=12, boil=0, parent=PLUTO)
PEYES = []
for s in (-1, 1):
    c = V3(0.0042 * s, -0.0098, 0.0058)
    em = empty(f'pem{s}', c, PLUTO)
    blob(f'pew{s}', 0.0029, M_EYE, (0, 0, 0), amp=0.03, seg=16, boil=0, parent=em)
    p = blob(f'pep{s}', 0.0015, M_PUP, (0, 0, 0), amp=0, seg=12, boil=0, parent=em); p.scale = (1, 1, 0.4); p.rotation_mode = 'QUATERNION'
    PEYES.append((em, p, c.normalized()))
rodP = cone('rodP', 0.0008, 0.0008, 1.0, M_WIRE, (0, 0, 0), seg=8)

# ================================================================ SET C: cutaway ocean tank
CUR[0] = 'C'
OC = V3(-3.0, 0, 0)
LIDZ = 0.34
M_OCEAN = grad_mat('ocean', [(0.0, (0.004, 0.012, 0.04)), (0.45, (0.02, 0.09, 0.22)), (0.93, (0.06, 0.27, 0.48)), (0.94, (0.004, 0.005, 0.012)), (1.0, (0.002, 0.003, 0.008))],
                   0.0, 0.40, bump=0.25)
M_WAVE1 = clay('wave1', (0.10, 0.42, 0.72), rough=0.35, prints=0.6, boil=2.0)
M_WAVE2 = clay('wave2', (0.04, 0.22, 0.52), rough=0.35, prints=0.6, boil=2.0)
M_ICE = clay('icelid', (0.82, 0.89, 0.96), rough=0.35, prints=0.8)
M_FLOOR = clay('seafloor', (0.14, 0.11, 0.09), rough=0.6, prints=0.5)
M_VROCK = clay('ventrock', (0.10, 0.08, 0.07), rough=0.55, prints=0.5)
M_GLOW = clay('glow', (1.0, 0.22, 0.015), rough=0.4, prints=0.3, emit=1.3)
M_BUB = plain('bubble', (0.75, 0.88, 1.0), rough=0.08, coat=1.0)
M_HOTBUB = plain('hotbubble', (1.0, 0.3, 0.03), rough=0.2, emit=0.7)
M_MIC = [clay('mic0', (0.35, 0.80, 0.25), rough=0.35, boil=3.0), clay('mic1', (0.65, 0.35, 0.85), rough=0.35, boil=3.0),
         clay('mic2', (0.95, 0.45, 0.60), rough=0.35, boil=3.0)]
bm = bmesh.new(); vs = [[bm.verts.new((-0.6 + 1.2 * i / 8, 0, -0.3 + 1.1 * j / 40)) for j in range(41)] for i in range(9)]
for i in range(8):
    for j in range(40): bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
back = mesh_obj('oceanback', bm, M_OCEAN, smooth_=False); back.location = OC + V3(0, 0.12, 0)
lid = slabbox('lid', 0.36, 0.11, 0.019, M_ICE, OC + V3(0, 0.0, LIDZ + 0.019), amp=0.003)
boil_mod(lid, 0.0004, size=0.01, amt=0.3, levels=1)
for k in range(9):
    blob(f'snowlump{k}', rng.uniform(0.006, 0.012), M_SNOW, OC + V3(rng.uniform(-0.2, 0.2), rng.uniform(-0.08, 0.06), LIDZ + 0.037), scale=(1.6, 1, 0.45), seg=16, boil=0)
duckC = duck('duckC', OC + V3(0.03, -0.04, LIDZ + 0.037))
duckC.rotation_euler = (0, 0, R(20))
for k in range(30):
    blob(f'cstar{k}', rng.uniform(0.0012, 0.002), M_STAR, OC + V3(rng.uniform(-0.3, 0.3), 0.115, rng.uniform(LIDZ + 0.05, 0.62)), seg=8, amp=0, boil=0)
floorC = slabbox('seafloor', 0.4, 0.2, 0.02, M_FLOOR, OC + V3(0, -0.06, 0.0), amp=0.006)
boil_mod(floorC, 0.0004, size=0.01, amt=0.3, levels=1)
for k in range(14):
    x = rng.uniform(-0.2, 0.2)
    if abs(x - 0.0) < 0.05: continue
    blob(f'srock{k}', rng.uniform(0.006, 0.014), M_VROCK, OC + V3(x, rng.uniform(-0.06, 0.08), 0.02), scale=(1.3, 1, 0.7), seg=16, boil=0)
for k in range(26):                    # foreground pebbles on the sea floor
    x, y = rng.uniform(-0.12, 0.09), rng.uniform(-0.17, -0.03)
    blob(f'fpeb{k}', rng.uniform(0.0025, 0.0065), M_VROCK if k % 3 else M_FLOOR, OC + V3(x, y, 0.019), scale=(1.3, 1, 0.55), seg=12, boil=0)
VENT = OC + V3(0.0, 0.035, 0.018)
v_ = cone('vent', 0.03, 0.012, 0.07, M_VROCK, VENT, seg=20, amp=0.004); boil_mod(v_, 0.0005, size=0.008, levels=1)
for k in range(5):
    an = rng.uniform(0, 2 * math.pi)
    blob(f'ventlump{k}', rng.uniform(0.008, 0.012), M_VROCK, VENT + V3(0.022 * math.cos(an), 0.02 * math.sin(an), rng.uniform(0.005, 0.03)), seg=16, boil=0)
blob('ventglow', 0.0115, M_GLOW, VENT + V3(0, 0, 0.066), scale=(1, 1, 0.55), seg=20, boil=0.0002)
NIB = OC + V3(-0.042, -0.012, 0.024)        # the rock a microbe nibbles: three lumps, the front one gets eaten
NIBS = [blob(f'nib{k}', rr, M_VROCK, NIB + d, scale=(1, 1, 0.8), seg=16, boil=0) for k, (rr, d) in
        enumerate([(0.011, V3(0, 0.004, 0)), (0.0075, V3(0.009, -0.004, 0.003)), (0.0055, V3(0.0105, -0.007, 0.009))])]
CRUMBS = [blob(f'crumb{k}', 0.0013, M_VROCK, NIB, seg=8, boil=0) for k in range(4)]
WAVES = []
for k in range(7):
    z = 0.075 + 0.036 * k; y = 0.06 - 0.012 * (k % 3)
    pts = [OC + V3(-0.36 + 0.72 * i / 39, y, z) for i in range(40)]
    WAVES.append((tube_curve(f'wave{k}', pts, 0.0045 + 0.001 * (k % 2), M_WAVE1 if k % 2 else M_WAVE2), z, y, k))
SWIRLS = []
for k, (x, z, s) in enumerate([(-0.07, 0.25, 1.0), (0.08, 0.17, 0.8), (-0.11, 0.11, 0.7), (0.12, 0.29, 0.9)]):
    pts = [OC + V3(x, 0.035, z)] * 30
    SWIRLS.append((tube_curve(f'swirl{k}', pts, 0.0028, M_WAVE1), V3(x, 0.03, z), s, k))
BUBS = []
for k in range(16):
    BUBS.append((blob(f'bub{k}', rng.uniform(0.002, 0.0045), M_BUB, OC, seg=12, amp=0.02, boil=0), rng.uniform(-0.22, 0.22), rng.uniform(-0.02, 0.05), rng.uniform(0, 1), rng.uniform(0.04, 0.07)))
HOT = []
for k in range(10):
    HOT.append((blob(f'hot{k}', rng.uniform(0.0025, 0.005), M_HOTBUB, OC, seg=12, amp=0.05, boil=0), rng.uniform(0, 1), rng.uniform(-1, 1)))
MICS = []
for k in range(7):
    rig = empty(f'mic{k}')
    L_ = rng.uniform(1.4, 2.0)
    blob(f'micb{k}', 0.0045, M_MIC[k % 3], (0, 0, 0), scale=(L_, 1, 0.9), amp=0.12, seg=20, boil=0.0002, parent=rig)
    for s in (-1, 1):
        blob(f'micw{k}{s}', 0.0017, M_EYE, (-0.0045 * L_ * 0.6, -0.0034, 0.0016 * s + 0.001), seg=10, boil=0, parent=rig)
        blob(f'micp{k}{s}', 0.0009, M_PUP, (-0.0045 * L_ * 0.6 - 0.0003, -0.0047, 0.0016 * s + 0.001), seg=8, boil=0, parent=rig)
    MICS.append((rig, rng.uniform(0, 2 * math.pi), rng.uniform(0.022, 0.05), rng.uniform(0.008, 0.036), rng.uniform(0.7, 1.4)))
CUR[0] = 'A'

# ================================================================ camera and lights
cd = bpy.data.cameras.new('cam'); cd.clip_start = 0.004; cd.clip_end = 20; cd.lens = 42; cd.sensor_width = 36; cd.dof.use_dof = True; cd.dof.aperture_fstop = 4.5
cam = link(bpy.data.objects.new('cam', cd)); cam['set'] = '*'; S.camera = cam
def aim(o, at, roll=0.0):
    o.rotation_euler = (at - o.location).to_track_quat('-Z', 'Y').to_euler()
    if roll: o.rotation_euler.rotate_axis('Z', roll)
LIGHTS = {}
def area(name, st, loc, at, size, energy, col=(1, 1, 1), kind='AREA'):
    CUR[0] = st
    ld = bpy.data.lights.new(name, kind); energy *= 0.06
    if kind == 'AREA': ld.size = size
    else: ld.shadow_soft_size = size
    ld.energy = energy; ld.color = col
    o = link(bpy.data.objects.new(name, ld)); o.location = loc; aim(o, at); LIGHTS[name] = (ld, energy, o); CUR[0] = 'A'; return o
# A: day
area('key', 'A', V3(-0.38, -0.32, 0.46), V3(0, 0.0, 0.02), 0.32, 55, (1.0, 0.9, 0.78))
area('fill', 'A', V3(0.48, -0.36, 0.16), V3(0, 0.0, 0.03), 0.45, 14, (0.78, 0.86, 1.0))
area('rim', 'A', V3(0.16, 0.30, 0.34), V3(0, -0.05, 0.03), 0.18, 22, (1.0, 0.85, 0.65))
area('skywash', 'A', V3(0.0, -0.1, 0.55), V3(0, 0.40, 0.2), 0.6, 18, (1.0, 0.97, 0.92))
area('warm', 'A', V3(0.25, 0.1, 0.4), V3(0, -0.07, 0.02), 0.2, 30, (1.0, 0.72, 0.4))        # the warm "sunbeam" in the last shot
# A: night (cold, low, from behind-left like moonlight, plus a faint front fill so faces read)
area('nkey', 'A', V3(-0.35, 0.25, 0.35), V3(0, -0.05, 0.02), 0.35, 30, (0.55, 0.7, 1.0))
area('nfill', 'A', V3(0.3, -0.45, 0.2), V3(0, -0.05, 0.03), 0.6, 12, (0.6, 0.75, 1.0))
area('nsky', 'A', V3(0.0, -0.1, 0.55), V3(0, 0.40, 0.2), 0.6, 4, (0.6, 0.7, 1.0))
# B: a studio light over the felt
area('bkey', 'B', OB + V3(-0.25, -0.3, 0.55), OB + V3(0, 0.1, 0), 0.35, 45, (1.0, 0.95, 0.9))
area('bfill', 'B', OB + V3(0.4, -0.2, 0.3), OB + V3(0, 0.2, 0), 0.5, 10, (0.75, 0.85, 1.0))
area('bkey2', 'B', OB2 + V3(-0.3, -0.35, 0.35), OB2 + V3(0, 0, 0.12), 0.3, 40, (0.9, 0.95, 1.0))
area('brim2', 'B', OB2 + V3(0.25, 0.25, 0.3), OB2 + V3(0, 0, 0.12), 0.2, 30, (0.7, 0.8, 1.0))
# C: cold light from the front-top, the warm vent glow on the floor
area('ckey', 'C', OC + V3(-0.2, -0.45, 0.45), OC + V3(0, 0.05, 0.2), 0.5, 45, (0.75, 0.88, 1.0))
area('cfill', 'C', OC + V3(0.35, -0.4, 0.15), OC + V3(0, 0.05, 0.1), 0.5, 12, (0.6, 0.75, 1.0))
area('ctop', 'C', OC + V3(0.0, -0.2, 0.7), OC + V3(0, 0.0, LIDZ), 0.5, 30, (0.85, 0.92, 1.0))
area('cvent', 'C', VENT + V3(0, -0.025, 0.085), VENT, 0.01, 0.9, (1.0, 0.45, 0.12), kind='POINT')
W = bpy.data.worlds.new('room'); S.world = W; W.use_nodes = True
WBG = W.node_tree.nodes['Background']

# ================================================================ the animation
SET_OF = ['A', 'A', 'A', 'B', 'A', 'A', 'A', 'C', 'C', 'B', 'A']
SHOT_PROPS = {0: {'sun', 'puff'}, 1: {'watch', 'icecream'}, 2: {'watch', 'stars'}, 4: {'thermo', 'stars'}, 5: {'calendar', 'stars', 'scarf'},
              6: {'stars', 'scarf', 'duck'}, 10: {'sun', 'puff'}}
MODE = ['day', 'day', 'dark', 'space', 'night', 'night', 'night', 'sea', 'sea', 'space', 'day']
# per shot: (cam loc, look-at, lens, f-stop); a slow motion-control push toward the target over the shot
CAMS = {
    0: (V3(0.0, -0.245, 0.028), V3(0.0, 0.10, 0.0305), 28, 5.6),
    1: (V3(0.008, -0.318, 0.034), V3(0.008, -0.07, 0.03), 40, 5.6),
    2: (V3(0.01, -0.33, 0.05), V3(0.01, 0.10, 0.05), 26, 6.3),
    3: (OB + V3(0.0, -0.11, 0.62), OB + V3(0.0, -0.06, 0.0), 42, 8.0),
    4: (V3(0.026, -0.28, 0.035), V3(0.026, -0.07, 0.035), 38, 5.6),
    5: (V3(-0.03, -0.30, 0.08), V3(-0.03, -0.04, 0.03), 34, 6.3),
    6: (V3(-0.06, -0.25, 0.20), V3(-0.025, 0.03, 0.0), 30, 7.1),
    7: (OC + V3(0.0, -0.55, 0.34), OC + V3(0.0, 0.0, 0.30), 42, 8.0),
    8: (OC + V3(-0.015, -0.22, 0.08), OC + V3(-0.015, 0.03, 0.042), 42, 5.6),
    9: (OB2 + V3(0.025, -0.42, 0.13), OB2 + V3(0.025, 0.0, 0.115), 40, 8.0),
    10: (V3(0.0, -0.245, 0.028), V3(0.0, 0.10, 0.0305), 28, 5.6),
}
def hop(u, p0, p1, h): return p0.lerp(p1, u) + V3(0, 0, 4 * h * u * (1 - u))

def sun_state(n):
    """the vanish, in poses: n = 0 is pose 0 (already squashing); n < 0 is the wobble that leads into it (end of the last shot)"""
    if n <= -10: return (1, 1, 1), 0.0
    if n < 0:
        w = (n + 10) / 10; s = 1 - 0.1 * w * w; q = 0.075 * w * (1 if n % 2 else -1)
        return (s * (1 + q), 1, s * (1 - q)), 0.0
    keys = [(0.86, 0.16), (0.72, -0.18), (0.56, 0.22), (0.36, -0.12), (0.17, 0.0)]
    if n < len(keys):
        s, q = keys[n]; return (s * (1 + q), 1, s * (1 - q)), (0.0 if n < 4 else 0.45)
    pf = [1.0, 1.25, 1.35, 1.3, 1.1, 0.8, 0.45, 0.0]
    return (0, 0, 0), (pf[n - 5] if n - 5 < len(pf) else 0.0)

def ball_state(k, u, D, n):
    st = dict(loc=HOME.copy(), sz=1.0, yaw=0.0, tilt=0.0, pitch=0.0, look='cam', blink=0.0, squint=0.0, vis=True, dizzy=0.0,
              mouth='smile', tongue=0.0, shiver=0.0, scarf=0.0, pivot=None)
    f = u / D
    if k == 0:                         # Sun vanishes; Ball looks up (eyes first, then the whole body whips back)
        sunp = SUNP.copy()
        if n >= 2: st['look'] = ('pt', sunp)
        if n == 5: st['sz'] = 0.84; st['mouth'] = 'o'
        elif n == 6: st['sz'] = 1.16; st['pitch'] = R(-16); st['mouth'] = 'o'
        elif n >= 7:
            st['sz'] = 1.0 + 0.04 * math.exp(-(n - 7) * 0.6) * (1 if n % 2 else -1); st['pitch'] = R(-13); st['mouth'] = 'o'
            st['tilt'] = R(4) * math.sin(n * 0.5)
        if n >= 7 and f > 0.78: st['look'] = 'cam'; st['pitch'] = R(-5); st['blink'] = 1.0 if 0.80 < f < 0.85 else 0.0
        st['pivot'] = HOME - V3(0, 0, BR)
    elif k == 1:                       # licking the ice cream, clueless, eyes squeezed happy
        ph = (u * 1.6) % 1.0
        st['yaw'] = R(-42) + R(4) * math.sin(u * 3.0); st['tilt'] = R(-10) - R(6) * math.sin(ph * math.pi)
        st['pivot'] = HOME - V3(0, 0, BR); st['squint'] = 0.9; st['look'] = ('pt', scoop.location)
        st['tongue'] = max(0.0, math.sin(ph * math.pi)) ** 0.6; st['mouth'] = 'smile'
        st['sz'] = 1.0 + 0.04 * math.sin(ph * 2 * math.pi)
        if f > 0.82: st['yaw'] = lerp(st['yaw'], R(-10), smooth(0.82, 0.95, f)); st['look'] = 'cam'; st['squint'] = 0.5; st['tongue'] *= 1 - smooth(0.82, 0.9, f)
    elif k == 2:                       # ding! then darkness: eyes glow, blink, look up at the Moon
        st['look'] = ('pt', WATCHP + V3(0, 0, 0.03)) if u < UL + 0.2 else 'cam'
        if UD <= u < UD + 0.2: st['sz'] = 1.12; st['mouth'] = 'o'
        elif u >= UD + 0.2: st['mouth'] = 'o'
        if UL + 0.45 < u < UL + 0.62 or UL + 0.8 < u < UL + 0.9: st['blink'] = 1.0
        if f > 0.56: st['look'] = ('pt', MOONP); st['pitch'] = R(-8)
    elif k == 4:                       # thermometer: eyes follow the bead down; shiver grows
        st['look'] = ('pt', THERMO_TOP[0]); st['shiver'] = 0.25 + 0.75 * f; st['mouth'] = 'o' if f > 0.3 else 'smile'
        if u < 0.25: st['look'] = 'cam'; st['mouth'] = 'smile'
        st['yaw'] = R(18); st['pitch'] = R(-4)
    elif k == 5:                       # frost: shiver, then the scarf goes on
        st['shiver'] = 1.0 - 0.6 * smooth(0.75, 0.9, f); st['mouth'] = 'o'
        st['look'] = ('pt', CALP + V3(0, 0, 0.03)) if f < 0.6 else 'cam'
        st['scarf'] = smooth(0.62, 0.8, f)
        if 0.62 < f < 0.8: st['sz'] = 0.9; st['squint'] = 0.7
        if f >= 0.8: st['mouth'] = 'smile'; st['squint'] = 0.3
        st['yaw'] = R(-20) if f < 0.6 else 0.0
    elif k == 6:                       # watching the pond and the duck from the lakeside, in its scarf
        st['loc'] = LAKESIDE.copy(); st['scarf'] = 1.0; st['shiver'] = 0.35
        if f < 0.4: st['look'] = ('pt', POND[0])
        else: st['look'] = ('pt', DUCK_NOW[0])
        st['yaw'] = R(-50) if f < 0.4 else R(35); st['mouth'] = 'o' if 0.15 < f < 0.4 else 'smile'
    elif k == 10:                      # the Sun is back: a sigh, lean into the warmth, then back to frame one
        tail = POSES - n_abs[0]        # poses left
        if u < 0.25: st['sz'] = 0.85 if u < 0.12 else 1.1; st['mouth'] = 'o'; st['look'] = ('pt', SUNP)
        elif tail > 10:
            q = smooth(0.25, 0.6, u)
            st['pitch'] = R(-14) * q; st['squint'] = 0.95 * q; st['blink'] = 0.75 * q; st['sz'] = 1.0 - 0.07 * q + 0.02 * math.sin(u * 2.2)
            st['tilt'] = R(5) * q * math.sin(u * 1.4); st['pivot'] = HOME - V3(0, 0, BR)
        if 10 >= tail > 4:              # open eyes, settle back into the frame-one pose
            st['blink'] = 1.0 if tail in (9, 8) else 0.0
    return st

THERMO_TOP = [THCOL0]; DUCK_NOW = [duckA.location.copy()]; n_abs = [0]
def therm_top(k, u, D):
    if k != 4: return 0.062
    t = CUT[4] + u; i = sum(t >= d for d in THDROPS)          # 59, 47, 35, 23 °F
    lv = [0.064, 0.051, 0.038, 0.025][i]
    if 0 < i and t - THDROPS[i - 1] < 1.5 / PPS: lv -= 0.004   # overshoot one pose, then settle
    return lv

def pose(p):
    t = p / PPS; k, u, D = shot_of(t); f = u / D; n_abs[0] = p
    r = random.Random(p * 7919 + 11)
    for mp, amt in MAPS: mp.inputs['Location'].default_value = (r.gauss(0, 0.00012 * amt), r.gauss(0, 0.00012 * amt), r.gauss(0, 0.00012 * amt))
    for e, amt in BOILS: e.location = (r.gauss(0, 0.0007 * amt), r.gauss(0, 0.0007 * amt), r.gauss(0, 0.0007 * amt))
    SET = SET_OF[k]; props = SHOT_PROPS.get(k, set()); mode = MODE[k]
    # ---- what is on stage
    for o in S.objects:
        if o.type not in ('MESH', 'CURVE', 'LIGHT'): continue
        st_ = o.get('set', 'A'); pr = o.get('prop')
        o.hide_render = not (st_ == SET and (pr is None or pr in props))
    # ---- the sun clock: n = poses since the vanish (shot 1) or until it (end of the last shot)
    n = None
    if k == 0: n = p
    elif k == 10:
        n = p - POSES if POSES - p <= 10 else None
    dark = (k == 2 and u >= UL)
    # ---- lights
    lv = {nm: 0.0 for nm in LIGHTS}
    if mode == 'day':
        for nm in ('key', 'fill', 'rim', 'skywash'): lv[nm] = 1.0
        if k == 10: lv['warm'] = smooth(0.2, 0.6, u) * (1 - smooth(TOTAL - 1.2, TOTAL - 0.9, t))
    elif mode == 'dark':
        if not dark:
            for nm in ('key', 'fill', 'rim', 'skywash'): lv[nm] = 1.0
        else:
            lv['nkey'] = 0.35; lv['nfill'] = 0.3; lv['nsky'] = 0.3
    elif mode == 'night':
        lv['nkey'] = 1.0; lv['nfill'] = 1.0; lv['nsky'] = 1.0
    elif mode == 'space':
        if k == 3: lv['bkey'] = 1.0; lv['bfill'] = 1.0
        else: lv['bkey2'] = 1.0; lv['brim2'] = 1.0
    elif mode == 'sea':
        lv['ckey'] = 1.0 if k == 7 else 0.5; lv['cfill'] = 1.0 if k == 7 else 0.6; lv['ctop'] = 1.0 if k == 7 else 0.25; lv['cvent'] = 1.0 if k == 8 else 0.3
    for nm, (ld, en, o) in LIGHTS.items():
        ld.energy = en * lv[nm] * (1 + r.gauss(0, 0.007)); o.hide_render = lv[nm] <= 0
    if mode == 'day' or (mode == 'dark' and not dark):
        WBG.inputs['Color'].default_value = (0.35, 0.33, 0.31, 1); WBG.inputs['Strength'].default_value = 0.25
    elif mode == 'dark': WBG.inputs['Color'].default_value = (0.02, 0.03, 0.07, 1); WBG.inputs['Strength'].default_value = 0.08
    elif mode == 'night': WBG.inputs['Color'].default_value = (0.05, 0.07, 0.15, 1); WBG.inputs['Strength'].default_value = 0.3
    elif mode == 'space': WBG.inputs['Color'].default_value = (0.02, 0.02, 0.03, 1); WBG.inputs['Strength'].default_value = 0.2
    else: WBG.inputs['Color'].default_value = (0.02, 0.05, 0.1, 1); WBG.inputs['Strength'].default_value = 0.3
    nightpaint = 1.0 if (mode == 'night' or dark) else 0.0
    PBS['sky_n'].inputs['Factor'].default_value = nightpaint
    for o in S.objects:
        if o.get('prop') == 'stars' and o.get('set') == 'A': o.hide_render = not (SET == 'A' and (mode == 'night' or dark))
    PBS['eye'].inputs['Emission Strength'].default_value = 0.35 if dark else 0.0
    PBS['eye'].inputs['Emission Color'].default_value = (0.9, 0.95, 1.0, 1)
    # Moon: pale by day, glowing in the blackout, then flicks off like a lamp; grey ever after
    moon_on = 0.0
    if k == 2 and dark:
        g = f - 0.6
        moon_on = 1.0 if g < 0 else (0.0 if g > 0.12 else [1, 0, 0.6, 0][min(3, int(g / 0.03))])
    PBS['moon'].inputs['Emission Strength'].default_value = 1.6 * moon_on
    PBS['moon'].inputs['Emission Color'].default_value = (1.0, 0.97, 0.85, 1)
    PBS['moon'].inputs['Base Color'].default_value = (0.78, 0.77, 0.66, 1)
    # sun glow (none after the vanish)
    PBS['sun'].inputs['Emission Strength'].default_value = 0.35
    # ---- frost and ice
    front = -5.0
    if k == 5:
        waves = [-0.06, 0.0, 0.06, 0.12, 0.2, 0.5]
        front = waves[min(len(waves) - 1, int((u - 0.05) / max(0.25, (D - 0.3) / 5.0)))] if u >= 0.05 else -0.12
    elif k in (6,): front = 5.0
    for mr in FROSTN: mr.inputs['From Min'].default_value = front; mr.inputs['From Max'].default_value = front - 0.015
    pond_th, lake_th = 9.0, 9.0
    if k == 5: pond_th = 0.95 - 0.5 * f; lake_th = 1.0 - 0.2 * f
    if k == 6:
        pond_th = 0.8 if u < 0.25 else (0.2 if u < 0.42 else -0.6)
        lake_th = 0.8 - 1.4 * smooth(0.3, 0.62, f)
        lake_th = round(lake_th * 6) / 6
    ICEN['pond'].inputs['From Min'].default_value = pond_th; ICEN['pond'].inputs['From Max'].default_value = pond_th + 0.04
    ICEN['lake'].inputs['From Min'].default_value = lake_th; ICEN['lake'].inputs['From Max'].default_value = lake_th + 0.04
    if k == 6: M_LAKE.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.22
    # ---- Sun and puff (shots 1 and 11)
    if SET == 'A':
        ss, pf = (1, 1, 1), 0.0
        if k == 0: ss, pf = sun_state(n)
        elif k == 10:
            m_ = int(round(u * PPS))
            if n is not None: ss, pf = sun_state(n)
            elif m_ < 5:
                ss = [(0.3, 1, 0.3), (1.18, 1, 0.88), (0.92, 1, 1.08), (1.04, 1, 0.97), (1, 1, 1)][m_]; pf = [1.2, 0.9, 0.5, 0.15, 0.0][m_]
        elif k in (1, 2, 4, 5, 6): ss = (0, 0, 0)
        sunrig.scale = tuple(c * 1.3 for c in ss); sunrig.location = SUNP + V3(r.gauss(0, 0.0004), 0, r.gauss(0, 0.0004))
        for o in S.objects:
            if o.get('prop') == 'sun': o.hide_render = o.hide_render or ss[0] < 0.01
        for o, d in PUFF:
            o.hide_render = o.hide_render or pf <= 0.01
            o.location = SUNP + V3(0, -0.012, 0) + d * (0.02 + 0.04 * pf); o.scale = (pf * 1.0, pf * 0.6, pf * 1.0)
    # ---- props
    # stopwatch
    if 'watch' in props:
        if k == 1: ang = -(u * 2 * math.pi * 1.35) - R(40)
        else: ang = (-R(300) - R(60) * u / UD) if u < UD else -R(360)
        hpiv.rotation_euler = (0, -ang, 0)
        hopz = 0.0; sq = 1.0
        if k == 2:
            if UD <= u < UD + 0.08: sq = 0.85
            elif UD + 0.08 <= u < UD + 0.34: hopz = 0.012 * math.sin((u - UD - 0.08) / 0.26 * math.pi); sq = 1.1
        watch.location = WATCHP + V3(0, 0, hopz); watch.scale = (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq)
        watch.rotation_euler = (0, R(3) * math.sin(u * 40) if k == 2 and UD < u < UD + 0.42 else 0, R(-18))
        crownb.location = (0, 0, 0.0198 - (0.0015 if k == 2 and UD <= u < UD + 0.22 else 0))
        for i, o in enumerate(DINGS): o.hide_render = not (k == 2 and UD <= u < UD + 0.34); o.scale = (1, 1, 1.0 + 0.6 * smooth(UD, UD + 0.22, u))
    # thermometer
    if 'thermo' in props:
        top = therm_top(k, u, D) + r.gauss(0, 0.0003)
        thcol.scale = (1, 1, max(0.001, top - 0.012)); thbead.location = THCOL0 + V3(0, 0, top - 0.012)
        THERMO_TOP[0] = thbead.location.copy()
    # calendar: three flips, each over 3 poses
    if 'calendar' in props:
        flips = [0.18, 0.34, 0.5]
        for i, pv in enumerate(PAGES):
            if i < 3:
                g = smooth(0, 0.25, u / D * D - flips[i] * D) if False else clamp((f - flips[i]) / (0.25 / D), 0, 1)
                g = round(g * 3) / 3
                pv.rotation_euler = (-(math.pi * 2 - 2 * CT) * g, 0, 0); pv.location.y = 0.0032 * i - 0.0015 * math.sin(g * math.pi)
                for c_ in pv.children_recursive: c_.hide_render = c_.hide_render or g >= 0.99
            else: pv.rotation_euler = (0, 0, 0)
    # duck slides on its belly across the lake once it has frozen
    if 'duck' in props:
        g = smooth(0.5, 1.0, f); g = round(g * D * PPS) / max(1, D * PPS) if False else g
        duckA.location = LAKE[0] + V3(-0.058 + 0.11 * g, -0.008 + 0.012 * math.sin(g * 3), -0.0018)
        duckA.rotation_euler = (0, 0, R(180) + R(200) * g)
        for o in duckA.children_recursive: o.hide_render = o.hide_render or f < 0.45
        DUCK_NOW[0] = duckA.location.copy()
    # ---- the Ball (tabletop sets only)
    for o in BALLPARTS: o.hide_render = o.hide_render or SET != 'A'
    if SET == 'A':
        st = ball_state(k, u, D, n if n is not None else 99)
        sz = st['sz']; sxy = 1 / math.sqrt(sz)
        sh = st['shiver'] * 0.0011
        loc = st['loc'] + V3(r.gauss(0, 0.00012) + (sh * (1 if p % 2 else -1)), r.gauss(0, 0.00012), 0)
        if st['pivot'] is not None:
            loc = st['pivot'] + Euler((st['pitch'], st['tilt'], 0)).to_matrix() @ (st['loc'] - st['pivot'])
        sq_off = V3(0, 0, -BR * (1 - sz))
        ball.location = loc + sq_off
        ball.rotation_euler = Euler((st['pitch'] + r.gauss(0, R(0.5)), st['tilt'] + r.gauss(0, R(0.5)), st['yaw'] + sh * 30 * (1 if p % 2 else -1)), 'XYZ')
        ball.scale = (sxy, sxy, sz)
        bl = st['blink']; sq = st['squint']; rw = ball.rotation_euler.to_matrix()
        for em, pup, nrm, side in EYES:
            em.scale = (1, 1, max(0.08, 1 - 0.92 * bl - 0.45 * sq))
            eyep = ball.location + rw @ (nrm * BR)
            if st['look'] == 'cam': wl = (cam_loc_for(k, u, D) - eyep).normalized()
            elif isinstance(st['look'], tuple): wl = (st['look'][1] - eyep).normalized()
            else: wl = st['look']
            d = rw.inverted() @ wl
            tg = d - nrm * nrm.dot(d)
            if tg.length > 0.85: tg = tg.normalized() * 0.85
            dirv = (nrm + 1.1 * tg).normalized()
            pup.location = dirv * 0.0055; pup.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
        smile = st['mouth'] == 'smile'
        mouth.hide_render = mouth.hide_render or not smile
        omouth.hide_render = omouth.hide_render or smile; ohole.hide_render = ohole.hide_render or smile
        tg_ = st['tongue']
        tongue.hide_render = tongue.hide_render or tg_ < 0.05
        tongue.location = MD * (BR * 0.98 + 0.0035 * tg_) + V3(0, 0, -0.0012); tongue.scale = (0.75 * max(tg_, 0.05), 1.0 * max(tg_, 0.05), 0.4 * max(tg_, 0.05))
        tongue.rotation_euler = Vector((0, -1, 0)).rotation_difference(MD).to_euler()
        sc = st['scarf']
        for o in scarf.children_recursive: o.hide_render = o.hide_render or sc <= 0.0
        q = round(sc * 3) / 3
        scarf.location = (0, 0, lerp(1.05 * BR, -0.33 * BR, q)); s_ = lerp(0.62, 1.0, q); scarf.scale = (s_, s_, 1)
    if k != 3:
        for o in (streak, str_pin, str_earth): o.hide_render = True
    # ---- Earth on the felt (shot 4): circling, the string snaps on pose 2, then a dead-straight run off to the right
    if k == 3:
        m_ = round(u * PPS); TS = 3
        an0 = R(-90)
        if m_ < TS:
            an = an0 - R(14) * (TS - m_); pos = PIN + V3(RO * math.cos(an), RO * math.sin(an), 0.026)
            vel = V3(-math.sin(an), math.cos(an), 0)
        else:
            tt = (m_ - TS) / PPS; dist = 0.075 * tt + 0.004 * tt * tt
            pos = PIN + V3(RO * math.cos(an0) + dist, RO * math.sin(an0), 0.026)
        EARTH4.location = pos + V3(r.gauss(0, 0.0002), r.gauss(0, 0.0002), 0)
        EARTH4.rotation_euler = (0, 0, R(6) * math.sin(m_ * 1.3))
        stretch = 1.0 if m_ < TS else 1.0 + 0.12 * math.exp(-(m_ - TS) * 0.35)
        EARTH4.scale = (stretch, 1 / stretch, 1)
        for em, pup, nrm in E4EYES:
            look = V3(-0.3, -0.6, 1) if m_ < TS else V3(0.6, -0.4, 1)
            d = look.normalized(); tg = d - nrm * nrm.dot(d); dirv = (nrm + 0.9 * tg).normalized()
            pup.location = dirv * 0.026 * 0.235; pup.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
        pa = PIN + V3(0, 0, 0.0065)
        if m_ < TS:
            set_curve(str_pin, [pa.lerp(pos, i / 11) + V3(0, 0, -0.004 * math.sin(math.pi * i / 11)) for i in range(12)])
            str_earth.hide_render = True
        else:
            g = min(1.0, (m_ - TS) / 6); snap = PIN + V3(RO * math.cos(an0), RO * math.sin(an0), 0.0065) * 0.5
            L1 = lerp(0.5, 0.18, g)
            mid = pa.lerp(V3(PIN.x, PIN.y - RO, 0.0065), L1)
            set_curve(str_pin, [pa.lerp(mid, i / 11) + V3(0.006 * g * math.sin(i * 1.3 + m_), 0, 0) for i in range(12)])
            tail_dir = V3(-1, 0.25, 0).normalized(); Lt = lerp(0.04, 0.016, g)
            set_curve(str_earth, [pos + V3(0, 0, -0.02) + tail_dir * Lt * i / 11 + V3(0, 0.004 * g * math.sin(i * 1.5 + m_), 0) for i in range(12)])
        x0 = PIN.x + RO * math.cos(an0); x1 = EARTH4.location.x - 0.022
        if m_ >= TS and x1 > x0 + 0.002:
            streak.location = V3((x0 + x1) / 2, PIN.y + RO * math.sin(an0), 0.0005); streak.scale = ((x1 - x0) / 1.0, 1, 1)
        else: streak.hide_render = True
    # ---- shot 10: frozen Earth drifts right, Pluto shivers and scoots away
    if k == 9:
        g = f
        epos = OB2 + V3(-0.075 + 0.052 * smooth(0, 0.40, g), 0.0, 0.115 + 0.003 * math.sin(u * 3))     # in frame by f=0.40 (before 'colder than Pluto'), then holds
        EARTH10.location = epos + V3(0.0008 * (1 if p % 2 else -1), 0, 0); EARTH10.rotation_euler = (0, R(-8) * min(g, 0.4) / 0.4, R(10) * min(g, 0.4) / 0.4)
        rodE.location = V3(epos.x, epos.y + 0.01, 0); rodE.scale = (1, 1, epos.z - 0.03)
        away = smooth(0.35, 0.8, f); away = round(away * 6) / 6
        ppos = OB2 + V3(0.065 + 0.075 * away, 0.05 * away, 0.11)
        PLUTO.location = ppos + V3(0.0006 * (1 if (p // 1) % 2 else -1) * (0.5 + away), 0, 0)
        PLUTO.rotation_euler = (0, R(-12) * away, R(-25) * away)
        rodP.location = V3(ppos.x, ppos.y + 0.008, 0); rodP.scale = (1, 1, ppos.z - 0.016)
        for em, pup, nrm in E10EYES:
            look = (PLUTO.location - EARTH10.location).normalized() * 0.6 + V3(0, -1, 0)
            d = EARTH10.rotation_euler.to_matrix().inverted() @ look.normalized(); tg = d - nrm * nrm.dot(d); dirv = (nrm + 0.9 * tg).normalized()
            pup.location = dirv * 0.03 * 0.235; pup.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
        for em, pup, nrm in PEYES:
            look = (EARTH10.location - PLUTO.location).normalized()
            d = PLUTO.rotation_euler.to_matrix().inverted() @ look; tg = d - nrm * nrm.dot(d)
            if tg.length > 0.85: tg = tg.normalized() * 0.85
            dirv = (nrm + 1.0 * tg).normalized()
            pup.location = dirv * 0.0025; pup.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
            em.scale = (1, 1, 1.15 if away > 0 else 1.0)
    # ---- the ocean (shots 8, 9): ribbons slosh, swirls turn, bubbles rise, the vent puffs, microbes wiggle
    if SET == 'C':
        tt = t
        for o, z, y, j in WAVES:
            pts = []
            for i in range(40):
                x = -0.36 + 0.72 * i / 39
                pts.append(OC + V3(x, y, z + 0.011 * math.sin(x * 28 + tt * (2.2 + 0.3 * j) + j) + 0.005 * math.sin(x * 61 - tt * 3.1 + j * 2)))
            set_curve(o, pts)
        for o, c, s, j in SWIRLS:
            pts = []
            for i in range(30):
                an = i * 0.42 + tt * 2.4 * (1 if j % 2 else -1); rr = s * 0.0018 * i ** 0.85
                pts.append(OC + c + V3(rr * math.cos(an), -0.003 * (i / 30), rr * math.sin(an)))
            set_curve(o, pts)
        for o, x, y, ph, sp in BUBS:
            zz = ((ph + tt * sp / 0.3) % 1.0)
            o.location = OC + V3(x + 0.006 * math.sin(tt * 4 + ph * 9), y, 0.04 + zz * (LIDZ - 0.05))
            o.hide_render = o.hide_render or zz > 0.97
        puff = 0.0
        if k == 8: puff = 1.0 if u < 0.6 else 0.5
        for o, ph, sw in HOT:
            zz = (ph + tt * 0.55) % 1.0
            if k == 8 and u < 0.6: zz = (ph * 0.5 + u * 0.9) % 1.0
            o.location = VENT + V3(0.012 * sw * zz + 0.004 * math.sin(tt * 6 + ph * 7), 0.0 - 0.006 * zz, 0.075 + zz * 0.09)
            s_ = (0.6 + 0.8 * zz) * (1 - smooth(0.75, 1.0, zz)); o.scale = (s_, s_, s_)
            o.hide_render = o.hide_render or s_ < 0.05
        PBS['glow'].inputs['Emission Strength'].default_value = 1.3 * (1.0 + 0.25 * math.sin(tt * 9))
        for j, (rig, ph, rad, hz, spd) in enumerate(MICS):
            if j == 0:                 # the nibbler: shuffles up to the rock, chomps, backs off happy
                g = smooth(0.15, 0.4, f); chomp = 0.4 < f < 0.65
                pos = NIB + V3(0.028 - 0.012 * g + (0.002 if chomp and p % 2 else 0), -0.012, 0.004)
                rig.location = pos; rig.rotation_euler = (0, 0, R(0))
                sq = 1.18 if chomp and p % 2 else 0.92 if chomp else 1.0
                rig.scale = (sq, 1 / sq, 1)
            else:
                an = ph + tt * spd * (1 if j % 2 else -1)
                pos = VENT + V3(rad * math.cos(an), -0.022 + 0.008 * math.sin(an), 0.03 + hz + 0.006 * math.sin(tt * 3 + j))
                rig.location = pos
                head = -math.sin(an) * (1 if j % 2 else -1)
                rig.rotation_euler = (0, R(15) * math.sin(tt * 7 + j), 0)
                w = 1 + 0.15 * math.sin(tt * 14 + j * 2); rig.scale = (w * (1 if head < 0 else -1), 1 / w, 1)
        eaten = k == 8 and f > 0.52
        NIBS[2].hide_render = NIBS[2].hide_render or eaten
        for i, o in enumerate(CRUMBS):
            g = (f - 0.52) / 0.3 if k == 8 else -1
            o.hide_render = o.hide_render or not (0 <= g <= 1)
            o.location = NIB + V3(0.0105, -0.007, 0.009) + V3(0.004 * (i - 1.5), -0.004, 0.006 * math.sin(g * math.pi) - 0.01 * g * g)
    # ---- camera
    cam.location = cam_loc_for(k, u, D); aim(cam, cam_tgt_for(k, u, D))
    cd.lens = CAMS[k][2]; cd.dof.aperture_fstop = CAMS[k][3]
    cd.dof.focus_distance = (focus_for(k, u, D) - cam.location).length

def cam_loc_for(k, u, D):
    L, T, lens, fs = CAMS[k]; f = clamp(u / D, 0, 1)
    if k == 7:                         # dropping through the lid into the water, in stop-motion steps
        g = smooth(0.0, 0.75, f); return L + V3(0, 0.08 * g, -0.23 * g)
    if k == 3: return L + V3(0, 0, -0.04 * f)
    if k == 10: return L.copy()
    return T + (L - T) * lerp(1.0, 0.93, sm(f))
def cam_tgt_for(k, u, D):
    L, T, lens, fs = CAMS[k]; f = clamp(u / D, 0, 1)
    if k == 7: g = smooth(0.0, 0.75, f); return T + V3(0, 0, -0.17 * g)
    return T
def focus_for(k, u, D):
    if SET_OF[k] == 'A':
        if k == 2 and u < 0.5: return WATCHP + V3(0, 0, 0.02)
        return ball.location
    if k == 3: return EARTH4.location
    if k == 9: return EARTH10.location
    if k == 7: return cam_tgt_for(k, u, D) + V3(0, 0.03, 0)
    return VENT + V3(0, -0.02, 0.05)

# ---------------------------------------------------------------- render
if __name__ == '__main__':
    if a.blend: bpy.ops.wm.save_as_mainfile(filepath=a.blend)
    todo = [int(x) for x in a.only.split(',')] if a.only else list(range(a.f0, min(a.f1, POSES)))
    if os.environ.get('LAYOUT'):
        if not a.only:
            todo = []
            for k in range(NL):
                p0 = math.ceil(CUT[k] * PPS - 1e-6); p1 = (math.ceil(CUT[k + 1] * PPS - 1e-6) if k + 1 < NL else POSES) - 1
                todo += [p0, (p0 + p1) // 2, p1]
        from bpy_extras.object_utils import world_to_camera_view as w2c
        for p in todo:
            pose(p); bpy.context.view_layer.update(); k = shot_of(p / PPS)[0]
            def px(o): v = w2c(S, cam, o.matrix_world.translation if hasattr(o, 'matrix_world') else o); return f'({v.x * 1080:.0f},{(1 - v.y) * 1920:.0f})'
            ks = {0: [ball, sunrig, moon], 1: [ball, scoop, watch], 2: [ball, watch, moon], 3: [EARTH4], 4: [ball, thbead], 5: [ball, cal],
                  6: [ball, pond, lake, duckA], 7: [lid], 8: [MICS[0][0]], 9: [EARTH10, PLUTO], 10: [ball, sunrig]}[k]
            print('pose', p, 'shot', k + 1, ' '.join(f'{o.name}{px(o)}' for o in ks), flush=True)
        sys.exit(0)
    os.makedirs(a.out, exist_ok=True)
    for p in todo:
        pose(p); S.render.filepath = os.path.join(a.out, f'f_{p:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', p, flush=True)
