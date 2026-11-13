# Clay stop-motion demo (Blender, Cycles). A tabletop clay set: a lumpy grass slab with a hole and a grey collar, clay trees,
# flowers, fence posts, a painted paper sky with cotton clouds. A clay ball with googly eyes hops in, teeters on the rim,
# peeks down, dives in (clods fly), then pops back out spinning and lands dizzy. Poses on twos (12 a second, 120 poses);
# every pose re-boils the clay (fingerprints, lumps and smudges shift a hair) and the lights flicker a touch, like real stop motion.
#   python3 clay.py OUTDIR P0 P1 [--samples 192] [--scale 1.0] [--only p,p]      -> OUTDIR/f_00000.png (one per pose)
import sys, os, math, argparse, random
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=192); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default='')
a = ap.parse_args()
PPS = 12; POSES = 120
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
C.max_bounces = 8; C.diffuse_bounces = 4; C.glossy_bounces = 3; C.transmission_bounces = 2; C.volume_bounces = 0
C.use_adaptive_sampling = True; C.adaptive_threshold = 0.012; C.adaptive_min_samples = 32
C.caustics_reflective = False; C.caustics_refractive = False; C.sample_clamp_indirect = 8.0
S.render.use_motion_blur = False
if os.environ.get('CROP'):
    x0_, y0_, x1_, y1_ = map(float, os.environ['CROP'].split(',')); S.render.use_border = True; S.render.use_crop_to_border = True
    S.render.border_min_x, S.render.border_min_y, S.render.border_max_x, S.render.border_max_y = x0_, y0_, x1_, y1_
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'; S.view_settings.exposure = 0.0

# ---------------------------------------------------------------- clay material
MAPS = []          # (mapping node, how much it boils)
def clay(name, col, rough=0.5, ss=0.12, prints=1.0, smudge=1.0, bump=0.45, boil=1.0, darken_z=None, sheen=0.25):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; Nn = nt.nodes; Lk = nt.links.new
    b = Nn['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Subsurface Weight'].default_value = ss
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.55, 0.35); b.inputs['Subsurface Scale'].default_value = 0.0007
    b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.6
    b.inputs['Specular IOR Level'].default_value = 0.42
    tc = Nn.new('ShaderNodeTexCoord'); mp = Nn.new('ShaderNodeMapping'); Lk(tc.outputs['Object'], mp.inputs['Vector']); MAPS.append((mp, boil))
    v = mp.outputs['Vector']
    # colour: hand-mixed clay is never one flat tone
    nz = Nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 45; nz.inputs['Detail'].default_value = 4; Lk(v, nz.inputs['Vector'])
    cr = Nn.new('ShaderNodeValToRGB'); Lk(nz.outputs['Fac'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].position = 0.3; cr.color_ramp.elements[0].color = (*[c * 0.88 for c in col], 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (*[min(1, c * 1.08) for c in col], 1)
    colout = cr.outputs['Color']
    if darken_z is not None:      # the inside of the hole goes dark the deeper it gets
        sz = Nn.new('ShaderNodeSeparateXYZ'); Lk(tc.outputs['Object'], sz.inputs['Vector'])
        mr = Nn.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = darken_z; mr.inputs['From Max'].default_value = 0.0
        mr.inputs['To Min'].default_value = 0.03; mr.inputs['To Max'].default_value = 1.0; Lk(sz.outputs['Z'], mr.inputs['Value'])
        mu = Nn.new('ShaderNodeMix'); mu.data_type = 'RGBA'; mu.blend_type = 'MULTIPLY'; mu.inputs['Factor'].default_value = 1.0
        Lk(colout, mu.inputs['A']); Lk(mr.outputs['Result'], mu.inputs['B']); colout = mu.outputs['Result']
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
    # smudges and thumb dents: soft broad Voronoi bowls
    vd = Nn.new('ShaderNodeTexVoronoi'); vd.feature = 'SMOOTH_F1'; vd.inputs['Scale'].default_value = 110; Lk(v, vd.inputs['Vector'])
    d1 = Nn.new('ShaderNodeMath'); d1.operation = 'MULTIPLY'; d1.inputs[1].default_value = 1.6 * smudge; Lk(vd.outputs['Distance'], d1.inputs[0])
    # fine grain
    gr = Nn.new('ShaderNodeTexNoise'); gr.inputs['Scale'].default_value = 1400; gr.inputs['Detail'].default_value = 3; Lk(v, gr.inputs['Vector'])
    g1 = Nn.new('ShaderNodeMath'); g1.operation = 'MULTIPLY'; g1.inputs[1].default_value = 0.035; Lk(gr.outputs['Fac'], g1.inputs[0])
    s1 = Nn.new('ShaderNodeMath'); s1.operation = 'ADD'; Lk(p3.outputs['Value'], s1.inputs[0]); Lk(d1.outputs['Value'], s1.inputs[1])
    s2 = Nn.new('ShaderNodeMath'); s2.operation = 'ADD'; Lk(s1.outputs['Value'], s2.inputs[0]); Lk(g1.outputs['Value'], s2.inputs[1])
    bp = Nn.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.003
    Lk(s2.outputs['Value'], bp.inputs['Height']); Lk(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def plain(name, col, rough=0.5, sheen=0.0, coat=0.0, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Coat Weight'].default_value = coat
    if emit: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    return m

M_GRASS = clay('grass', (0.13, 0.36, 0.07), rough=0.55, prints=0.6)
M_DIRT = clay('dirt', (0.22, 0.12, 0.06), rough=0.6, prints=0.4)
M_HOLE = clay('hole', (0.20, 0.11, 0.055), rough=0.65, prints=0.3, darken_z=-0.032)
M_GREY = clay('collar', (0.42, 0.42, 0.40), rough=0.5)
M_YEL = clay('yellow', (0.85, 0.62, 0.05), rough=0.45)
M_BALL = clay('ball', (0.85, 0.20, 0.04), rough=0.42, prints=1.6, smudge=1.4, bump=0.7, boil=4.0)
M_WHITE = clay('white', (0.86, 0.85, 0.80), rough=0.4, prints=0.6, boil=3.0)
M_EYE = clay('eye', (0.92, 0.92, 0.90), rough=0.3, prints=0.3, smudge=0.4, bump=0.2, boil=3.0)
M_PUP = plain('pupil', (0.01, 0.01, 0.012), rough=0.15, coat=0.6)
M_MOUTH = clay('mouth', (0.06, 0.02, 0.015), rough=0.4, prints=0.2, boil=3.0)
M_TRUNK = clay('trunk', (0.24, 0.12, 0.05), rough=0.6)
M_LEAF = clay('leaf', (0.07, 0.25, 0.05), rough=0.55)
M_LEAF2 = clay('leaf2', (0.12, 0.33, 0.06), rough=0.55)
M_TUFT = clay('tuft', (0.16, 0.42, 0.08), rough=0.55, prints=0.2)
M_PINK = clay('pink', (0.85, 0.35, 0.50), rough=0.45)
M_PETAL = clay('petal', (0.88, 0.86, 0.80), rough=0.45)
M_SUN = clay('sun', (0.95, 0.68, 0.10), rough=0.45)
M_ROCK = clay('rock', (0.30, 0.29, 0.28), rough=0.6)
M_COTTON = plain('cotton', (0.92, 0.92, 0.93), rough=0.95, sheen=1.0)

def sky_mat():
    m = bpy.data.materials.new('sky'); m.use_nodes = True; nt = m.node_tree; Nn = nt.nodes; Lk = nt.links.new; b = Nn['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.9
    tc = Nn.new('ShaderNodeTexCoord'); sz = Nn.new('ShaderNodeSeparateXYZ'); Lk(tc.outputs['Object'], sz.inputs['Vector'])
    mr = Nn.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.25; Lk(sz.outputs['Z'], mr.inputs['Value'])
    cr = Nn.new('ShaderNodeValToRGB'); Lk(mr.outputs['Result'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].color = (0.62, 0.74, 0.80, 1); cr.color_ramp.elements[1].color = (0.12, 0.32, 0.70, 1)
    wv = Nn.new('ShaderNodeTexWave'); wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 9; wv.inputs['Distortion'].default_value = 6; wv.inputs['Detail'].default_value = 4
    Lk(tc.outputs['Object'], wv.inputs['Vector'])
    mx = Nn.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.05
    Lk(cr.outputs['Color'], mx.inputs['A']); Lk(wv.outputs['Color'], mx.inputs['B']); Lk(mx.outputs['Result'], b.inputs['Base Color'])
    nz = Nn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 300; Lk(tc.outputs['Object'], nz.inputs['Vector'])
    bp = Nn.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.15; Lk(nz.outputs['Fac'], bp.inputs['Height']); Lk(bp.outputs['Normal'], b.inputs['Normal'])
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

# ---------------------------------------------------------------- helpers
def link(o): S.collection.objects.link(o); return o
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
def blob(name, r, mat, loc, scale=(1, 1, 1), amp=0.08, seed=None, seg=24, boil=0.0004, levels=1):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    bm.normal_update(); lumpy(bm, r * amp, 3.0 / r, rng.random() * 100 if seed is None else seed)
    o = mesh_obj(name, bm, mat); o.location = loc; o.scale = scale
    if boil: boil_mod(o, boil, size=max(0.004, r * 0.6), levels=levels)
    return o
def cone(name, r0, r1, h, mat, loc, rot=(0, 0, 0), seg=12, amp=0.0):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=h)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, h / 2))
    if amp: bm.normal_update(); lumpy(bm, amp, 2.0 / max(r0, 0.002), rng.random() * 100)
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = rot; return o
def torus(name, R_, r_, mat, loc, rot=(0, 0, 0), su=96, sv=24, amp=0.0, flat=1.0):
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
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = rot; return o

# ---------------------------------------------------------------- the set
H = V3(0.035, 0.03, 0.0)                      # hole centre
RIN = 0.0265; RX, RY = 0.21, 0.16; TOP_DEPTH = 0.03; TUBE = 0.05; NA = 192
def build_slab():
    bm = bmesh.new(); rings = []                # each ring: list of NA (x,y,z)
    for k in range(7):                          # tube, from bottom up
        z = -TUBE + TUBE * k / 6; rr = RIN * (0.92 + 0.08 * k / 6)
        rings.append(('hole', [(H.x + rr * math.cos(2 * math.pi * i / NA), H.y + rr * math.sin(2 * math.pi * i / NA), z) for i in range(NA)]))
    NR = 56
    for k in range(NR + 1):                     # top surface, dense near the hole
        s = (k / NR) ** 1.6; ring = []
        for i in range(NA):
            t = 2 * math.pi * i / NA; ci, si = math.cos(t), math.sin(t)
            p_in = Vector((H.x + RIN * ci, H.y + RIN * si)); p_out = Vector((RX * ci, RY * si))
            p = p_in.lerp(p_out, s)
            z = 0.0016 * mnoise.noise(V3(p.x * 22, p.y * 22, 3.1)) + 0.0006 * mnoise.noise(V3(p.x * 80, p.y * 80, 7.7))
            z += 0.0022 * math.exp(-((s * 0.9) / 0.06) ** 2)            # a soft lip where the hole was dug
            e = smooth(0.93, 1.0, s); z -= 0.006 * e * e
            ring.append((p.x, p.y, z))
        rings.append(('grass' if k < NR - 1 else 'edge', ring))
    for k in range(1, 6):                       # slab side, bulging a little
        f = k / 5; z = -0.006 - (TOP_DEPTH - 0.006) * f; bul = 1.0 + 0.015 * math.sin(math.pi * f)
        rings.append(('side', [(RX * bul * math.cos(2 * math.pi * i / NA), RY * bul * math.sin(2 * math.pi * i / NA), z) for i in range(NA)]))
    vv = [[bm.verts.new(p) for p in r] for _, r in rings]
    mats = {'hole': 0, 'grass': 1, 'edge': 1, 'side': 2}
    for k in range(len(vv) - 1):
        kind = rings[k + 1][0] if rings[k][0] != 'hole' or rings[k + 1][0] == 'hole' else 'hole'
        mi = mats[rings[k][0]] if rings[k][0] in ('hole',) else (2 if rings[k + 1][0] == 'side' else 1)
        for i in range(NA):
            f = bm.faces.new((vv[k][i], vv[k][(i + 1) % NA], vv[k + 1][(i + 1) % NA], vv[k + 1][i])); f.material_index = mi
    c = bm.verts.new((H.x, H.y, -TUBE));
    for i in range(NA):
        f = bm.faces.new((c, vv[0][(i + 1) % NA], vv[0][i])); f.material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj('slab', bm);
    for m_ in (M_HOLE, M_GRASS, M_DIRT): o.data.materials.append(m_)
    # normals should point up on the grass
    zs = [p.normal.z for p in o.data.polygons if p.material_index == 1]
    if sum(zs) < 0: o.data.flip_normals()
    boil_mod(o, 0.0005, size=0.01, amt=0.25, levels=1)
    return o
slab = build_slab()
table = link(bpy.data.objects.new('table', bpy.data.meshes.new('table')))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.5); bm.to_mesh(table.data); bm.free()
table.location = (0, 0.4, -TOP_DEPTH); table.data.materials.append(wood_mat())

collar = torus('collar', 0.0335, 0.0068, M_GREY, H + V3(0, 0, 0.0055), amp=0.0012, flat=0.85); boil_mod(collar, 0.0003, size=0.006)
band = torus('stripe', 0.0335, 0.0026, M_YEL, H + V3(0, 0, 0.0108), sv=12, amp=0.0004, flat=0.5); boil_mod(band, 0.0002, size=0.005)

# posts and a string (like the hole video's yellow posts)
for i, (x, y) in enumerate([(-0.005, 0.085), (0.04, 0.095), (0.085, 0.08)]):
    p = cone(f'post{i}', 0.0038, 0.0034, 0.024, M_YEL, (x, y, -0.001), rot=(R(rng.uniform(-4, 4)), R(rng.uniform(-4, 4)), 0), amp=0.0004)
    boil_mod(p, 0.0002, size=0.004)
    blob(f'postcap{i}', 0.0038, M_YEL, (x, y, 0.023), scale=(1, 1, 0.7), boil=0.0001)
# trees
for i, (x, y, h, s) in enumerate([(-0.105, 0.10, 0.055, 1.0), (0.12, 0.115, 0.07, 1.15), (0.165, 0.035, 0.04, 0.8), (-0.165, 0.04, 0.035, 0.75)]):
    tr = cone(f'trunk{i}', 0.0065 * s, 0.0042 * s, h, M_TRUNK, (x, y, -0.002), rot=(R(rng.uniform(-5, 5)), R(rng.uniform(-5, 5)), 0), amp=0.0006)
    boil_mod(tr, 0.0003, size=0.006)
    for j in range(4):
        rr = 0.024 * s * rng.uniform(0.75, 1.0)
        blob(f'leaf{i}{j}', rr, M_LEAF if j % 2 else M_LEAF2, (x + rng.uniform(-0.014, 0.014) * s, y + rng.uniform(-0.01, 0.01) * s, h + rng.uniform(0.0, 0.026) * s),
             scale=(1, 1, 0.85), amp=0.12, boil=0.0006, levels=1)
# flowers
for i, (x, y) in enumerate([(-0.07, 0.06), (0.095, 0.035), (0.11, -0.045), (-0.125, -0.02), (0.07, 0.10), (-0.03, 0.115)]):
    st = cone(f'stem{i}', 0.0011, 0.0008, 0.016, M_TUFT, (x, y, -0.001), rot=(R(rng.uniform(-10, 10)), R(rng.uniform(-10, 10)), 0))
    top = st.matrix_world @ V3(0, 0, 0.016) if False else V3(x, y, 0.015)
    pm = M_PINK if i % 2 else M_PETAL
    for k in range(5):
        an = 2 * math.pi * k / 5
        blob(f'pet{i}{k}', 0.0026, pm, top + V3(0.0028 * math.cos(an), 0.0028 * math.sin(an), 0), scale=(1, 1, 0.45), seg=12, boil=0)
    blob(f'fc{i}', 0.0019, M_YEL, top + V3(0, 0, 0.0008), seg=12, boil=0)
# pebbles
for i in range(9):
    an = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.055, 0.15)
    x, y = 0.0 + rr * math.cos(an) * 1.2, 0.02 + rr * math.sin(an) * 0.8
    if abs(y - 0.015) < 0.03 and x < 0.03: continue
    blob(f'peb{i}', rng.uniform(0.003, 0.0055), M_ROCK, (x, y, 0.001), scale=(1, 0.85, 0.6), seg=16, boil=0)
# grass tufts, kept off the ball's path and the hole
path = [V3(-0.13 + 0.013 * i, -0.004 + 0.003 * i, 0) for i in range(12)] + [V3(0.03, -0.035, 0)]
n = 0
while n < 70:
    x, y = rng.uniform(-0.19, 0.19), rng.uniform(-0.14, 0.13)
    if (x / RX) ** 2 + (y / RY) ** 2 > 0.82: continue
    if (V3(x, y, 0) - H).length < 0.055: continue
    if min((V3(x, y, 0) - q).length for q in path) < 0.03: continue
    for k in range(3):
        cone(f'tuft{n}_{k}', 0.0013, 0.0001, rng.uniform(0.004, 0.0075), M_TUFT, (x + rng.uniform(-0.0025, 0.0025), y + rng.uniform(-0.0025, 0.0025), -0.0005),
             rot=(R(rng.uniform(-25, 25)), R(rng.uniform(-25, 25)), 0), seg=6)
    n += 1

# backdrop: painted paper sky, cotton clouds, a clay sun
bm = bmesh.new(); cols = []
for i in range(41):
    an = R(25 + 130 * i / 40); cols.append([bm.verts.new((0.62 * math.cos(an), -0.2 + 0.62 * math.sin(an), -TOP_DEPTH + 0.6 * j / 10)) for j in range(11)])
for i in range(40):
    for j in range(10): bm.faces.new((cols[i][j], cols[i + 1][j], cols[i + 1][j + 1], cols[i][j + 1]))
sky = mesh_obj('sky', bm, sky_mat())
for c_, (x, z, s) in enumerate([(-0.13, 0.15, 0.8), (0.05, 0.21, 0.7), (0.19, 0.13, 0.75)]):
    for k in range(6):
        blob(f'cloud{c_}{k}', 0.03 * s * rng.uniform(0.6, 1.0), M_COTTON, (x + rng.uniform(-0.05, 0.05) * s, 0.38, z + rng.uniform(-0.012, 0.015) * s),
             scale=(1.3, 0.5, 0.75), amp=0.25, seg=20, boil=0)
sun = blob('sun', 0.035, M_SUN, (0.11, 0.39, 0.2), scale=(1, 0.35, 1), boil=0)
for k in range(10):
    an = 2 * math.pi * k / 10
    cone(f'ray{k}', 0.006, 0.0015, 0.022, M_SUN, (0.11 + 0.04 * math.cos(an), 0.39, 0.2 + 0.04 * math.sin(an)), rot=(0, R(90) - an, 0), seg=8)
    bpy.data.objects[f'ray{k}'].rotation_euler = Euler((0, 0, 0)); bpy.data.objects[f'ray{k}'].rotation_euler.rotate_axis('Y', math.pi / 2 - an)

# clods that fly when the ball dives in
CLODS = []
for i in range(9):
    o = blob(f'clod{i}', rng.uniform(0.0025, 0.0042), M_GRASS if i % 3 else M_DIRT, (0, 0, -1), scale=(1, 0.9, 0.7), seg=12, boil=0)
    an = rng.uniform(0, 2 * math.pi); sp = rng.uniform(0.06, 0.11)
    CLODS.append((o, Vector((sp * math.cos(an), sp * math.sin(an) * 0.8, rng.uniform(0.32, 0.42))), rng.uniform(-8, 8)))

# ---------------------------------------------------------------- the ball character
BR = 0.018
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=BR); bm.normal_update(); lumpy(bm, 0.0005, 160, 3.3)
ball = mesh_obj('ball', bm, M_BALL); boil_mod(ball, 0.00045, size=0.008, amt=3.0, levels=2)
headband = torus('headband', BR * 0.985, 0.0021, M_WHITE, (0, 0, 0), rot=(R(-62), 0, 0), sv=12, amp=0.0003, flat=0.55)
headband.parent = ball; boil_mod(headband, 0.0002, size=0.004, amt=3.0)
EYES = []
for side in (-1, 1):
    a_, e_ = R(23) * side, R(17)
    c = Vector((math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_))) * BR * 0.9
    em = link(bpy.data.objects.new(f'eye{side}', None)); em.parent = ball; em.location = c
    w = blob(f'white{side}', 0.0062, M_EYE, (0, 0, 0), amp=0.03, seg=32, boil=0.00012); w.parent = em
    p = blob(f'pupil{side}', 0.0031, M_PUP, (0, 0, 0), amp=0.0, seg=24, boil=0); p.parent = em; p.scale = (1, 1, 0.4)
    p.rotation_mode = 'QUATERNION'
    EYES.append((em, p, c.normalized(), side))
cu = bpy.data.curves.new('mouth', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0009; cu.bevel_resolution = 4
sp_ = cu.splines.new('NURBS'); sp_.points.add(6); sp_.use_endpoint_u = True; sp_.order_u = 4
for k in range(7):
    u = (k / 6) * 2 - 1; an = R(17) * u; el = R(-24) + R(11) * u * u
    q = Vector((math.sin(an) * math.cos(el), -math.cos(an) * math.cos(el), math.sin(el))) * BR * 1.0
    sp_.points[k].co = (*q, 1)
mouth = link(bpy.data.objects.new('mouth', cu)); mouth.data.materials.append(M_MOUTH); mouth.parent = ball

# ---------------------------------------------------------------- camera and lights
cd = bpy.data.cameras.new('cam'); cd.lens = 42; cd.sensor_width = 36; cd.dof.use_dof = True; cd.dof.aperture_fstop = 4.5
cam = link(bpy.data.objects.new('cam', cd)); S.camera = cam
CAM0, TGT0 = V3(-0.004, -0.36, 0.115), V3(-0.006, 0.03, 0.04)
def aim(o, at):
    o.rotation_euler = (at - o.location).to_track_quat('-Z', 'Y').to_euler()
LIGHTS = []
def area(name, loc, at, size, energy, col=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); energy *= 0.06; ld.size = size; ld.energy = energy; ld.color = col
    o = link(bpy.data.objects.new(name, ld)); o.location = loc; aim(o, at); LIGHTS.append((ld, energy)); return o
area('key', V3(-0.38, -0.32, 0.46), V3(0, 0.02, 0.02), 0.32, 55, (1.0, 0.9, 0.78))
area('fill', V3(0.48, -0.36, 0.16), V3(0, 0.02, 0.03), 0.45, 14, (0.78, 0.86, 1.0))
area('rim', V3(0.16, 0.30, 0.34), V3(0, 0.0, 0.03), 0.18, 22, (1.0, 0.85, 0.65))
area('skywash', V3(0.0, -0.1, 0.55), V3(0, 0.38, 0.18), 0.6, 18, (1.0, 0.97, 0.92))
W = bpy.data.worlds.new('room'); S.world = W; W.use_nodes = True
W.node_tree.nodes['Background'].inputs['Color'].default_value = (0.35, 0.33, 0.31, 1); W.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.25

# ---------------------------------------------------------------- the animation (t in seconds; poses at 12 a second)
TOPZ = 0.0125 + BR                               # resting on the collar
GND = BR + 0.001
def hop(u, p0, p1, h): return p0.lerp(p1, u) + V3(0, 0, 4 * h * u * (1 - u))
def ball_state(t):
    """-> loc, sz (squash/stretch along z), yaw, tilt (about y), look (world dir or 'cam'), blink, squint, visible, dizzy"""
    st = dict(sz=1.0, yaw=R(35), tilt=0.0, look=None, blink=0.0, squint=0.0, vis=True, dizzy=0.0, pivot=None)
    A0, A1 = V3(-0.105, -0.004, GND), V3(-0.07, 0.004, GND)
    B1, C1, D1 = V3(-0.04, 0.014, GND), V3(-0.013, 0.024, GND), V3(0.0015, 0.03, TOPZ)
    hops = [(-0.35, 0.45, A0, A1, 0.06), (0.58, 1.2, A1, B1, 0.04), (1.33, 1.85, B1, C1, 0.028), (1.98, 2.5, C1, D1, 0.022)]
    lands = [(0.45, 0.58, A1, 0.72), (1.2, 1.33, B1, 0.78), (1.85, 1.98, C1, 0.82), (2.5, 2.66, D1, 0.86)]
    for t0, t1, p0, p1, h in hops:
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0); st['loc'] = hop(u, p0, p1, h)
            vz = 4 * h * (1 - 2 * u); st['sz'] = 1 + 0.22 * clamp(abs(vz) / (4 * h), 0, 1) * (1 if abs(u - 0.5) > 0.12 else 0.3)
            st['tilt'] = R(10) * (1 - 2 * u); return st
    for t0, t1, p, sq in lands:
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0); st['sz'] = lerp(sq, 1.05, sm(u)); st['loc'] = p.copy(); return st
    if t < 4.3:                                   # teeter on the rim, peek down, look at us, blink
        u = t - 2.66
        st['tilt'] = R(15) * math.sin(u * 7.5) * math.exp(-u * 1.6)
        st['pivot'] = D1 - V3(0, 0, BR)
        st['loc'] = D1.copy(); st['yaw'] = lerp(R(35), R(55), smooth(2.66, 3.0, t))
        st['yaw'] = lerp(st['yaw'], R(0), smooth(3.6, 3.9, t))
        if 3.0 <= t < 3.6: st['look'] = (H + V3(0, 0, -0.03) - D1).normalized(); st['tilt'] += R(8) * smooth(3.0, 3.25, t)
        else: st['look'] = 'cam'
        st['blink'] = 1.0 if 4.0 <= t < 4.17 else 0.0
        return st
    if t < 4.75:                                  # wind up
        u = smooth(4.3, 4.62, t); st['yaw'] = R(0); st['sz'] = lerp(1.0, 0.68, u); st['squint'] = u
        st['loc'] = D1.copy(); st['tilt'] = R(-9) * u; st['look'] = 'cam'; st['pivot'] = D1 - V3(0, 0, BR); return st
    if t < 5.45:                                  # leap and dive
        u = (t - 4.75) / 0.7; P0, P1 = D1, V3(H.x, H.y, -0.06)
        x = lerp(P0.x, P1.x, smooth(0, 0.75, u)); z = lerp(P0.z, P1.z, u) + 4 * 0.09 * u * (1 - u)
        st['loc'] = V3(x, H.y, z); st['yaw'] = R(0)
        st['sz'] = 1.32 if u < 0.25 else (0.95 if u < 0.5 else 1.38); st['tilt'] = R(25) * smooth(0.3, 0.7, u)
        st['look'] = (V3(1, 0, -1)).normalized(); st['vis'] = z > -0.055; return st
    if t < 7.1: st['vis'] = False; st['loc'] = V3(H.x, H.y, -0.08); return st
    if t < 8.1:                                   # pops back out, spinning
        u = (t - 7.1) / 1.0; P0, P1 = V3(H.x, H.y, -0.05), V3(0.03, -0.035, GND)
        z = lerp(P0.z, P1.z, u) + 4 * 0.15 * u * (1 - u); v = smooth(0.16, 1.0, u)
        st['loc'] = V3(lerp(P0.x, P1.x, v), lerp(P0.y, P1.y, v), z); st['yaw'] = R(720) * (1 - sm(u))
        vz = -2 * (P1.z - P0.z) + 0.6 * (1 - 2 * u); st['sz'] = 1 + 0.35 * clamp(abs(1 - 2 * u) * 1.3 - 0.15, 0, 1)
        st['look'] = 'cam'; st['squint'] = 0.0; st['blink'] = 0.0; st['dizzy'] = 0.6 * smooth(0.4, 0.9, u)
        return st
    LZ = V3(0.03, -0.035, GND)
    if t < 8.32:
        u = (t - 8.1) / 0.22; st['loc'] = LZ.copy(); st['yaw'] = 0; st['sz'] = lerp(0.6, 1.12, sm(u)); st['look'] = 'cam'; st['dizzy'] = 1.0; return st
    if t < 9.35:                                  # dizzy
        u = t - 8.32; st['loc'] = LZ.copy(); st['yaw'] = R(8) * math.sin(u * 5.0)
        st['tilt'] = R(13) * math.sin(u * 6.2) * (1 - 0.5 * u); st['pivot'] = LZ - V3(0, 0, BR)
        st['sz'] = 1 + 0.03 * math.sin(u * 12); st['look'] = 'cam'; st['dizzy'] = 1.0 - smooth(0.75, 1.0, u); return st
    if t < 9.47:
        st['loc'] = LZ.copy(); st['yaw'] = 0; st['sz'] = 0.8; st['look'] = 'cam'; st['squint'] = 0.6; return st
    if t < 9.85:                                  # a happy little hop
        u = (t - 9.47) / 0.38; st['loc'] = hop(u, LZ, LZ, 0.02); st['yaw'] = 0; st['sz'] = 1.15 if abs(u - 0.5) > 0.2 else 1.0
        st['look'] = 'cam'; return st
    u = smooth(9.85, 10.0, t); st['loc'] = LZ.copy(); st['yaw'] = 0; st['sz'] = lerp(0.8, 1.0, u); st['look'] = 'cam'; return st

def pose(p):
    t = p / PPS; r = random.Random(p * 7919 + 11)
    # boil: every textured surface shifts a hair, more on the character the animator keeps touching
    for mp, amt in MAPS: mp.inputs['Location'].default_value = (r.gauss(0, 0.00012 * amt), r.gauss(0, 0.00012 * amt), r.gauss(0, 0.00012 * amt))
    for e, amt in BOILS: e.location = (r.gauss(0, 0.0007 * amt), r.gauss(0, 0.0007 * amt), r.gauss(0, 0.0007 * amt))
    for ld, en in LIGHTS: ld.energy = en * (1 + r.gauss(0, 0.007))
    st = ball_state(t)
    ball.hide_render = not st['vis']
    for o in [headband, mouth] + [c for em, *_ in EYES for c in em.children]: o.hide_render = not st['vis']
    sz = st['sz']; sxy = 1 / math.sqrt(sz)
    rot = Euler((0, st['tilt'], st['yaw']), 'XYZ').to_matrix()
    loc = st['loc'] + V3(r.gauss(0, 0.00012), r.gauss(0, 0.00012), 0)
    if st['pivot'] is not None:                   # rock about the contact point, not the middle
        loc = st['pivot'] + Euler((0, st['tilt'], 0)).to_matrix() @ (st['loc'] - st['pivot'])
    grounded = abs(st['loc'].z - GND) < 0.003 or abs(st['loc'].z - TOPZ) < 0.003
    sq_off = V3(0, 0, -BR * (1 - sz)) if grounded else V3(0, 0, 0)
    ball.location = loc + sq_off
    ball.rotation_euler = Euler((r.gauss(0, R(0.5)), st['tilt'] + r.gauss(0, R(0.5)), st['yaw']), 'XYZ')
    ball.scale = (sxy, sxy, sz)
    # eyes
    bl = st['blink']; sq = st['squint']
    rw = ball.rotation_euler.to_matrix()
    for em, pup, n, side in EYES:
        em.scale = (1, 1, max(0.08, 1 - 0.92 * bl - 0.45 * sq))
        if st['look'] == 'cam' or st['look'] is None:
            wl = (cam.location - (ball.location + rw @ (n * BR))).normalized()
        else: wl = st['look']
        d = rw.inverted() @ wl
        if st['dizzy'] > 0:
            ph = t * 11 * side; d = d + st['dizzy'] * 0.9 * (Vector((math.cos(ph), 0, math.sin(ph))))
        tg = d - n * n.dot(d)
        if tg.length > 0.85: tg = tg.normalized() * 0.85
        dirv = (n + 1.1 * tg).normalized()
        pup.location = dirv * 0.0055
        pup.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(dirv)
    # clods
    for o, v0, spin in CLODS:
        tt = t - 5.42
        if tt < 0: o.hide_render = True; continue
        o.hide_render = False; tl = 2 * v0.z / 0.95
        if tt < tl:
            o.location = H + V3(v0.x * tt, v0.y * tt, 0.004 + v0.z * tt - 0.5 * 0.95 * tt * tt); o.rotation_euler = (spin * tt, spin * tt * 0.7, 0)
        else:
            o.location = H + V3(v0.x * tl, v0.y * tl, 0.0028); o.rotation_euler = (spin * tl, spin * tl * 0.7, 0)
            if (o.location.xy - H.xy).length < RIN + 0.012: o.hide_render = True
    # the collar and stripe wobble when the ball goes in and when it rumbles out
    wob = 0.0
    if t >= 5.4: wob += 0.07 * math.exp(-(t - 5.4) * 4) * math.cos((t - 5.4) * 30)
    if 6.3 <= t < 6.5 or 6.8 <= t < 7.1: wob += r.uniform(-0.03, 0.03)
    if t >= 7.1: wob += 0.06 * math.exp(-(t - 7.1) * 4) * math.cos((t - 7.1) * 30)
    for o, z0 in ((collar, 0.0055), (band, 0.0108)):
        o.scale = (1 + wob, 1 + wob, 1 - wob); o.location = H + V3(r.gauss(0, 0.0001) if 6.3 <= t < 7.1 else 0, 0, z0)
    # camera: locked off, with a slow motion-control push in
    k = smooth(0.0, 10.0, t)
    cam.location = TGT0 + (CAM0 - TGT0) * lerp(1.0, 0.9, k) + V3(0.006 * k, 0, 0)
    aim(cam, TGT0 + V3(0.01 * k, 0, 0))
    focus = ball.location if st['vis'] else H
    cd.dof.focus_distance = (focus - cam.location).length

# ---------------------------------------------------------------- render
if __name__ == '__main__':
    if a.blend: bpy.ops.wm.save_as_mainfile(filepath=a.blend)
    os.makedirs(a.out, exist_ok=True)
    todo = [int(x) for x in a.only.split(',')] if a.only else list(range(a.f0, min(a.f1, POSES)))
    for p in todo:
        pose(p); S.render.filepath = os.path.join(a.out, f'f_{p:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', p, flush=True)
