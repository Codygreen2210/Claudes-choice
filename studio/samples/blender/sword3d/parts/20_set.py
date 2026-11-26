
# ================================================================ set: a museum hall (x -4..24), sword exhibits along the back wall
def brick_mat(name, c1, c2, mortar, scale=1.0, rough=0.85, plane='xz', bump=0.6, row=0.5, w=0.5, mortar_w=0.02, seed=0.0, wob_=0.0):
    """bricks / stone blocks / planks on a wall or floor: object coords in metres; plane picks the two axes the pattern runs in"""
    m = mat(name, c1, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    if plane == 'xz': mp.inputs['Rotation'].default_value = (math.pi / 2, 0, 0)
    elif plane == 'yz': mp.inputs['Rotation'].default_value = (math.pi / 2, 0, math.pi / 2)
    mp.inputs['Location'].default_value = (seed, seed * 0.7, 0)
    br = nt.nodes.new('ShaderNodeTexBrick')
    if wob_:
        nzv = nt.nodes.new('ShaderNodeTexNoise'); nzv.inputs['Scale'].default_value = 2.5; nt.links.new(mp.outputs['Vector'], nzv.inputs['Vector'])
        sub = nt.nodes.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; nt.links.new(nzv.outputs['Color'], sub.inputs[0]); sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        sc_ = nt.nodes.new('ShaderNodeVectorMath'); sc_.operation = 'SCALE'; nt.links.new(sub.outputs[0], sc_.inputs[0]); sc_.inputs['Scale'].default_value = wob_
        ad = nt.nodes.new('ShaderNodeVectorMath'); ad.operation = 'ADD'; nt.links.new(mp.outputs['Vector'], ad.inputs[0]); nt.links.new(sc_.outputs[0], ad.inputs[1])
        nt.links.new(ad.outputs[0], br.inputs['Vector'])
    else: nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
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
M_IRON = iron_mat('iron', 0.32); M_IRDK = iron_mat('irondk', 0.22, base=(0.035, 0.035, 0.04), seed=2.0)
M_IRON2 = iron_mat('iron2', 0.42, seed=5.0); M_IRON4 = iron_mat('iron4', 0.62, seed=9.0, rust_col=(0.10, 0.045, 0.02))
M_STONE = brick_mat('stone', (0.11, 0.10, 0.09), (0.065, 0.06, 0.055), (0.03, 0.028, 0.026), 1.4, plane='xz', bump=1.6, row=0.36, w=0.55, mortar_w=0.05, wob_=0.12)
M_STONEY = brick_mat('stoney', (0.11, 0.10, 0.09), (0.065, 0.06, 0.055), (0.03, 0.028, 0.026), 1.4, plane='yz', bump=1.6, row=0.36, w=0.55, mortar_w=0.05, seed=3.0, wob_=0.12)
M_FLAG = brick_mat('flag', (0.13, 0.12, 0.11), (0.09, 0.085, 0.08), (0.035, 0.032, 0.03), 0.9, plane='xy', bump=0.7, row=0.55, w=0.7, mortar_w=0.03, seed=1.0)
M_WOODF = brick_mat('woodfloor', (0.30, 0.17, 0.08), (0.24, 0.13, 0.06), (0.12, 0.06, 0.03), 1.0, rough=0.35, plane='xy', bump=0.25, row=0.16, w=1.8, mortar_w=0.006, seed=2.0)
M_WOODF.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.35
M_PLASTER = noisy(mat('plaster', (0.52, 0.48, 0.42), 0.8), 3.0, 0.12)
M_WAINS = noisy(mat('wains', (0.12, 0.07, 0.04), 0.45, coat=0.3), 20.0, 0.15)
M_CEIL = noisy(mat('ceil', (0.30, 0.29, 0.27), 0.9), 2.0, 0.1)
M_BRASS = mat('brass', (0.78, 0.55, 0.22), 0.28, 1.0)
M_VELVET = mat('velvet', (0.32, 0.015, 0.03), 0.75, sheen=0.8)
M_WOOD = noisy(mat('wood', (0.26, 0.14, 0.065), 0.55, coat=0.15), 14.0, 0.3)
M_WOODRAW = noisy(mat('woodraw', (0.40, 0.29, 0.17), 0.85), 10.0, 0.3)
M_PAPER = noisy(mat('paper', (0.78, 0.70, 0.55), 0.8), 8.0, 0.08)
M_INK = mat('ink', (0.01, 0.01, 0.012), 0.3)
M_GOLD = mat('gold', (0.85, 0.62, 0.25), 0.25, 1.0); M_SILV = mat('silver', (0.72, 0.72, 0.74), 0.3, 1.0)
M_WAX = mat('wax', (0.85, 0.80, 0.68), 0.5, trans=0.2, sheen=0.3)
M_FLAME = emis_mix('flame', (1.0, 0.55, 0.18), 22.0)
M_STRAW = noisy(mat('straw', (0.55, 0.42, 0.18), 0.8), 30.0, 0.3)
M_PLAQ = mat('plaq', (0.06, 0.05, 0.045), 0.5); M_GILT = mat('gilt', (0.9, 0.7, 0.32), 0.3, 1.0)
M_BLACK = mat('blackm', (0.02, 0.02, 0.02), 0.6)
M_GLASS = mat('glass', (0.9, 0.95, 1.0), 0.02, trans=1.0, ior=1.45)
M_POSTER = mat('poster', (0.80, 0.70, 0.50), 0.8)
M_RED = mat('red', (0.55, 0.04, 0.04), 0.6); M_WHITE = mat('white', (0.85, 0.84, 0.80), 0.6); M_BLUE = mat('blue', (0.05, 0.10, 0.35), 0.6)

# ---------------------------------------------------------------- the museum hall
HALL = empty('hall')
box('hfloor', (28.4, 13.0, 0.2), (10.0, -0.9, -0.1), M_WOODF, parent=HALL)
box('hback', (28.4, 0.3, 6.0), (10.0, 5.55, 3.0), M_PLASTER, parent=HALL)
box('hwains', (28.4, 0.06, 1.0), (10.0, 5.38, 0.5), M_WAINS, bv=0.01, parent=HALL)
box('hfront', (28.4, 0.3, 6.0), (10.0, -7.55, 3.0), M_PLASTER, parent=HALL)
box('hleft', (0.3, 13.0, 6.0), (-4.35, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hceil', (28.4, 13.4, 0.3), (10.0, -0.9, 6.15), M_CEIL, parent=HALL)
for xb in range(-3, 24, 3): box(f'beam{xb}', (0.3, 13.0, 0.35), (xb + 0.5, -0.9, 5.83), M_WOOD, bv=0.01, parent=HALL)
# the end wall at x = 24 with a tall arched window (an opening the camera flies through)
WX = 24.0; WY0, WY1, WZ0, WZ1 = -1.3, 1.3, 1.0, 4.2
box('hend_l', (0.4, 7.4 - 1.3 + 0.0, 6.0), (WX, -7.4 + (7.4 - 1.3) / 2 - 0.3, 3.0), M_PLASTER, parent=HALL)
box('hend_r', (0.4, 5.7 - 1.3, 6.0), (WX, 1.3 + (5.7 - 1.3) / 2, 3.0), M_PLASTER, parent=HALL)
box('hend_b', (0.4, 2.6, 1.0), (WX, 0.0, 0.5), M_PLASTER, parent=HALL)
box('hend_t', (0.4, 2.6, 6.0 - WZ1), (WX, 0.0, WZ1 + (6.0 - WZ1) / 2), M_PLASTER, parent=HALL)
for s_ in (-1, 1): box(f'wjamb{s_}', (0.5, 0.12, WZ1 - WZ0 + 0.1), (WX, s_ * 1.36, (WZ0 + WZ1) / 2), M_WOOD, bv=0.01, parent=HALL)
box('wsill', (0.7, 2.9, 0.1), (WX, 0, WZ0 - 0.05), M_WOOD, bv=0.01, parent=HALL); box('whead', (0.5, 2.9, 0.12), (WX, 0, WZ1 + 0.05), M_WOOD, bv=0.01, parent=HALL)
for s_ in (-1, 1):                                          # the casements, swung open outward
    cp_ = empty(f'case{s_}', HALL, loc=(WX + 0.2, s_ * 1.3, WZ0)); cp_.rotation_euler = (0, 0, s_ * R(70))
    box(f'casef{s_}', (0.05, 1.3, WZ1 - WZ0), (0, -s_ * 0.65, (WZ1 - WZ0) / 2), M_WOOD, parent=cp_)
    for k in range(1, 4): box(f'casem{s_}{k}', (0.06, 1.3, 0.04), (0, -s_ * 0.65, (WZ1 - WZ0) * k / 4), M_WOOD, parent=cp_)
    box(f'caseg{s_}', (0.01, 1.2, WZ1 - WZ0 - 0.1), (0, -s_ * 0.65, (WZ1 - WZ0) / 2), M_GLASS, parent=cp_)
# museum track lights (fixtures) along a rail, one per exhibit
RAIL = box('rail', (26.0, 0.08, 0.06), (10.0, 0.4, 5.55), M_BLACK, parent=HALL)
MUSEUM_LIGHTS = []
def track_spot(x, target, e=900, size=0.12):
    p = Vector((x, 0.4, 5.45)); can = prim('cylinder', f'can{x}', M_BLACK, HALL, loc=p, vertices=16, radius=0.07, depth=0.22)
    can.rotation_mode = 'QUATERNION'; can.rotation_quaternion = (Vector(target) - p).to_track_quat('-Z', 'Y')
    lt = light_at(f'spot{x}', 'SPOT', p, target, e, (1.0, 0.92, 0.80), size); lt.data.spot_size = R(48); lt.data.spot_blend = 0.6
    MUSEUM_LIGHTS.append((lt, e)); return lt
for xs, tg in ((0.0, (0.0, 3.6, 0.9)), (1.6, (1.6, 3.6, 0.9)), (4.0, (4.0, 3.6, 1.1)), (7.4, (8.0, 5.3, 2.6)), (8.6, (8.6, 4.4, 1.2)),
               (12.0, (12.0, 4.3, 1.6)), (13.6, (13.6, 3.5, 1.0)), (16.5, (16.5, 3.9, 1.5)), (20.3, (20.3, 5.3, 2.4))):
    track_spot(xs, tg)
for k, xa in enumerate((2.0, 9.0, 16.0, 22.0)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 350, (1.0, 0.93, 0.84), 3.0), 350))
G = random.Random(7)


def placard(name, loc, rz, body, size=0.07):
    P_ = empty(name, HALL, loc=loc); P_.rotation_euler = (0, 0, R(rz))
    for xs_ in (-0.12, 0.12): box(f'{name}leg{xs_}', (0.03, 0.03, 0.9), (xs_, 0, 0.45), M_BRASS, parent=P_)
    pb = box(f'{name}board', (0.6, 0.03, 0.4), (0, -0.02, 0.98), M_PLAQ, bv=0.005, parent=P_); pb.rotation_euler = (R(-35), 0, 0)
    text3d(f'{name}txt', body, size, (0, -0.045, 1.0), (R(55), 0, 0), M_GILT, P_, extrude=0.002); return P_


def wall_banner(name, x, body, w=2.4):
    box(name, (w, 0.02, 0.5), (x, 5.38, 3.6), M_RED, parent=HALL)
    text3d(name + 'txt', body, 0.3, (x, 5.36, 3.6), (R(90), 0, 0), M_GILT, HALL, extrude=0.008)


PLAT_Z = 0.15
M_PLAT = noisy(mat('platm', (0.20, 0.12, 0.07), 0.6, coat=0.1), 10.0, 0.2)


# ---------------------------------------------------------------- sword-room materials
M_BLADE = steel_mat('blade', seed=1.0); M_BLADE2 = steel_mat('blade2', (0.58, 0.59, 0.61), 0.24, seed=4.0)
M_BLADEM = steel_mat('bladem', (0.55, 0.56, 0.60), 0.16, seed=7.0, dark=0.15)
M_HILTI = mat('hilti', (0.10, 0.10, 0.11), 0.35, 1.0)
M_GEM = mat('gem', (0.55, 0.02, 0.05), 0.05, trans=0.6, coat=1.0)
M_VELV = cloth_mat('velv', (0.30, 0.02, 0.03), 0.8, 0.8, 120.0, 2.0)
M_ENAM = noisy(mat('enam', (0.03, 0.10, 0.06), 0.3, coat=0.6), 6.0, 0.15)
M_ENAMR = noisy(mat('enamr', (0.28, 0.03, 0.03), 0.3, coat=0.6), 6.0, 0.15)
M_IRONB = mat('ironb', (0.03, 0.03, 0.032), 0.45, 0.6)
M_DIAL = noisy(mat('dial', (0.86, 0.84, 0.76), 0.35, coat=0.4), 5.0, 0.06)
M_NEEDLE = mat('needle', (0.65, 0.03, 0.02), 0.35, coat=0.5)
M_GLASSD = mat('glassd', (0.9, 0.95, 1.0), 0.02, trans=1.0)
M_TAPE = mat('tape', (0.85, 0.65, 0.05), 0.45)
M_STAMP = mat('stamp', (0.75, 0.04, 0.03), 0.6)
M_BOOK = cloth_mat('book', (0.03, 0.06, 0.20), 0.6, 0.2, 260.0, 9.0)
M_PANEL = cloth_mat('panel', (0.20, 0.015, 0.02), 0.85, 0.8, 200.0, 3.0)
for xp, w_, d_ in ((0.8, 3.6, 1.8), (4.0, 1.4, 1.4), (12.8, 3.8, 2.2), (16.5, 2.4, 1.6), (20.3, 1.6, 1.4)):
    box(f'plat{xp}', (w_, d_, PLAT_Z), (xp, 3.9 if xp != 20.3 else 4.45, PLAT_Z / 2), M_PLAT, bv=0.01, parent=HALL)
wall_banner('ban1', 0.8, 'SWORDS', 2.6)


def sword_on(sw, x, y, top):
    """rest a lying sword (guard at x) on a surface at height top: the lowest point just touches"""
    sw.location = (x, y, 0.0); sw.rotation_euler = (0, 0, 0); z0 = low_z(sw); sw.location = (x, y, top - z0 + 0.001); return sw.location.copy()


# ================================================================ exhibit 1: two dial scales (x = 0 and 1.6) - the myth sword, a real sword, a two-hander
S1X, S2X, SY = 0.0, 1.6, 3.6
SC1, ND1, TOP1 = dial_scale('sc1', HALL, (S1X, SY, PLAT_Z)); TOP1 += PLAT_Z
SC2, ND2, TOP2 = dial_scale('sc2', HALL, (S2X, SY, PLAT_Z), m_body=M_ENAMR); TOP2 += PLAT_Z
MYTH = sword('myth', None, 1.25, 0.14, 0.035, 0.5, 0.3, 0.075, M_BLADEM, M_GILT, M_LEATHER, kind='myth')
MYTH_P = sword_on(MYTH, S1X - 0.4, SY + 0.14, TOP1); MYTH_RZ = R(-20)          # lies a little across the pan so the gold hilt shows
ARM = sword('arm', None, 0.76, 0.026, 0.0035, 0.2, 0.1, 0.03, M_BLADE, M_HILTI, M_LEATHER)
ARM_P = sword_on(ARM, S1X - 0.2, SY, TOP1)
TWO = sword('two', None, 1.05, 0.027, 0.004, 0.36, 0.27, 0.035, M_BLADE2, M_HILTI, M_LEATHER)
TWO_P = sword_on(TWO, S2X - 0.25, SY, TOP2)
placard('plaq1', (S1X - 0.95, 2.75, 0), 12, 'WHAT DID A\nSWORD WEIGH?')

# ================================================================ exhibit 2: the balance - a sword teeters on a knife edge at its balance point (x = 4.0)
BALX, BALY = 4.0, 3.6
lathe('baltab', [(0.0, 0.0), (0.25, 0.0), (0.25, 0.03), (0.04, 0.06), (0.035, 0.8), (0.3, 0.8), (0.3, 0.85), (0.0, 0.85)], 32, M_WOOD, HALL, loc=(BALX, BALY, PLAT_Z))
prim('cylinder', 'baltop', M_VELV, HALL, loc=(BALX, BALY, PLAT_Z + 0.855), vertices=32, radius=0.29, depth=0.012)
tube('balpost', [(BALX, BALY, PLAT_Z + 0.86), (BALX, BALY, PLAT_Z + 1.08)], 0.012, M_BRASS, HALL, seg=12)
box('balknife', (0.022, 0.06, 0.022), (BALX, BALY, PLAT_Z + 1.08), M_BRASS, rot=(0, R(45), 0), parent=HALL)
PEG = Vector((BALX, BALY, PLAT_Z + 1.08 + 0.0156))
BSW = sword('bsw', None, 0.76, 0.026, 0.0035, 0.2, 0.1, 0.03, M_BLADE, M_HILTI, M_LEATHER)
BAL_PIV = Vector((0.12, 0.0, -0.0035 * (1 - 0.55 * 0.12 / 0.76)))        # the balance point on the blade's underside, in the sword's frame
placard('plaq2', (BALX + 0.75, 2.85, 0), -12, 'BALANCED\nNEAR THE HILT')

# ================================================================ exhibit 3: the old book on the wall (1746) and a new book on a stand (x = 8.0)
BKX = 8.0
PAGE = empty('page', HALL, loc=(BKX, 5.33, 2.65))
box('pgframe', (1.32, 0.04, 1.52), (0, 0.01, 0), M_GILT, bv=0.01, parent=PAGE)
box('pgpaper', (1.2, 0.02, 1.4), (0, -0.015, 0), noisy(mat('pgp', (0.62, 0.52, 0.34), 0.85), 6.0, 0.18), parent=PAGE)
text3d('pghead', 'THE USE OF THE', 0.07, (0, -0.03, 0.56), (R(90), 0, 0), M_INK, PAGE, extrude=0.001)
text3d('pghead1', 'BROAD SWORD', 0.1, (0, -0.03, 0.45), (R(90), 0, 0), M_INK, PAGE, extrude=0.001)
YEAR = text3d('pgyear', '1746', 0.09, (0, -0.03, 0.31), (R(90), 0, 0), M_STAMP, PAGE, extrude=0.001)
SCRIB = []
for k in range(4):
    z_ = 0.17 - 0.08 * k; L_ = 0.8 + 0.15 * G.random(); pts = []
    for i in range(60):
        u = i / 59; pts.append(Vector((-0.5 + L_ * u, -0.031, z_ + 0.012 * math.sin(u * 70 + k) + 0.006 * math.sin(u * 180 + k * 2))))
    o = tube(f'scr{k}', pts, 0.0035, M_INK, PAGE, seg=4); SCRIB.append((o, -0.5, L_))
QUOTE = [text3d('pgq0', '"The Sword was', 0.085, (-0.5, -0.031, -0.2), (R(90), 0, 0), M_INK, PAGE, extrude=0.001, align='LEFT'),
         text3d('pgq1', '... heavy"', 0.11, (-0.5, -0.031, -0.36), (R(90), 0, 0), M_INK, PAGE, extrude=0.001, align='LEFT')]
QUOTE_W = [0.75, 0.62]
QUILL = empty('quill', PAGE, loc=(0, -0.08, 0))
tube('qshaft', [(0, 0, 0), (0.05, -0.04, 0.3)], lambda u: 0.004 + 0.002 * u, M_LINEN, QUILL, seg=6)
vs = []; fs = []
for i in range(12):
    u = i / 11; c_ = Vector((0.05, -0.04, 0.3)) * (0.25 + 0.75 * u); w_ = 0.035 * math.sin(math.pi * u) ** 0.7
    vs += [tuple(c_ + Vector((-w_, 0.0, 0.0))), tuple(c_ + Vector((w_ * 0.6, 0.0, 0.0)))]
for i in range(11): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
mesh('qvane', vs, fs, noisy(mat('feather', (0.85, 0.84, 0.80), 0.8, sheen=0.6), 40.0, 0.2), QUILL, smooth_=False)
# the new book: a red hardcover on a wooden stand, a red stamp slams onto it
box('bkped', (0.42, 0.42, 0.95), (BKX + 0.6, 4.45, PLAT_Z + 0.475), M_WOOD, bv=0.01, parent=HALL)
BOOK = empty('book', HALL, loc=(BKX + 0.6, 4.45, PLAT_Z + 0.95)); BOOK.rotation_euler = (R(-12), 0, R(-8))
box('bkstand', (0.3, 0.05, 0.03), (0, -0.06, 0.015), M_WOOD, parent=BOOK)
box('bkcov', (0.27, 0.035, 0.36), (0, 0, 0.19), M_BOOK, bv=0.006, parent=BOOK)
box('bkpages', (0.255, 0.03, 0.345), (0.006, 0.002, 0.19), M_PAPER, parent=BOOK)
text3d('bkt', 'KNIGHTS', 0.05, (0, -0.019, 0.31), (R(90), 0, 0), M_GILT, BOOK, extrude=0.001)
text3d('bkt2', 'and their\nweapons', 0.028, (0, -0.019, 0.24), (R(90), 0, 0), M_GILT, BOOK, extrude=0.001)
STAMP = empty('stamp', BOOK, loc=(0, -0.022, 0.12)); STAMP.rotation_euler = (0, R(-10), 0)
text3d('stmp', 'UP TO\n30 LB!', 0.05, (0, -0.004, 0), (R(90), 0, 0), M_STAMP, STAMP, extrude=0.002)
box('stmpb', (0.2, 0.002, 0.13), (0, 0.0, 0.0), M_STAMP, parent=STAMP).hide_render = True

# ================================================================ exhibit 4: the real giant - a 7-foot bearing sword on its stand, a tape measure, a long scale (x = 12.0)
GX, GY = 12.0, 4.4
box('gstand', (0.4, 0.34, 0.16), (GX, GY, PLAT_Z + 0.08), M_WOOD, bv=0.01, parent=HALL)
GIANT = sword('giant', None, 1.59, 0.038, 0.005, 0.55, 0.42, 0.05, M_BLADE2, M_GILT, M_LEATHER, kind='bearing')
M_UP = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0))).to_4x4()     # blade up, flats facing the camera (-y)
GIANT.location = (0, 0, 0); GIANT.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
_gx = [ (GIANT.matrix_world.inverted() @ o.matrix_world @ v.co).x for o in GIANT.children_recursive if o.type == 'MESH' for v in o.data.vertices ]
G_XMIN, G_XMAX = min(_gx), max(_gx)                              # pommel end and point, in the sword's frame
G_UP = Matrix.Translation((GX, GY, PLAT_Z + 0.16 - G_XMIN + 0.002)) @ M_UP
GIANT.matrix_basis = G_UP
TAPE = empty('tape', HALL, loc=(GX + 0.25, GY - 0.05, 0))
G_H = G_XMAX - G_XMIN                                             # its length: 2.16 m, seven feet
box('tapeb', (0.035, 0.004, G_H), (0, 0, G_H / 2), M_TAPE, parent=TAPE)
for k in range(1, 8):
    z_ = 0.3048 * k; box(f'tapet{k}', (0.02, 0.006, 0.006), (-0.008, -0.002, z_), M_INK, parent=TAPE)
    text3d(f'tapen{k}', str(k), 0.025, (0.006, -0.004, z_ - 0.02), (R(90), 0, 0), M_INK, TAPE, extrude=0.0005)
TAPE_Z0 = PLAT_Z + 0.16 - 0.002                                   # the tape runs from the pommel's foot
box('tapebox', (0.09, 0.07, 0.07), (GX + 0.25, GY - 0.05, PLAT_Z + 0.035), M_TAPE, bv=0.01, parent=HALL)
TAG = empty('tag7', HALL, loc=(GX + 0.5, GY - 0.06, TAPE_Z0 + G_H))
box('tagb', (0.4, 0.01, 0.16), (0, 0, 0), M_STAMP, bv=0.01, parent=TAG)
text3d('tagt', '7 FT', 0.11, (0, -0.007, 0), (R(90), 0, 0), M_WHITE, TAG, extrude=0.001)
GLX, GLY = 13.6, 3.45
SC3, ND3, TOP3 = dial_scale('sc3', HALL, (GLX, GLY, PLAT_Z), pan='long', pan_w=2.5, maxv=20); TOP3 += PLAT_Z
GIANT.matrix_basis = Matrix.Identity(4); G_FLAT = sword_on(GIANT, GLX - 0.62, GLY, TOP3); G_FLATM = GIANT.matrix_basis.copy()
GIANT.matrix_basis = G_UP
placard('plaq4', (GX + 0.75, 2.75, 0), -12, 'BEARING SWORD\n1500s')  # right side: the camera's path from the book runs through the left side

# ================================================================ exhibit 5: the parade - two guards in red and yellow, one carries the giant sword (x = 16.5)
PX, PY = 16.5, 3.9
def guard(name, x):
    f_ = dress_form(name, HALL, (x, PY, PLAT_Z))
    prof = [(0.17, 0.62), (0.175, 0.85), (0.15, 1.0), (0.16, 1.18), (0.19, 1.34), (0.205, 1.42), (0.14, 1.5), (0.06, 1.545)]
    arc_shell(f'{name}_l', prof, 90, 270, 20, 1.0, 0.72, M_REDC, 0.008, f_); arc_shell(f'{name}_r', prof, -90, 90, 20, 1.0, 0.72, M_YELC, 0.008, f_)
    collar(f'{name}_col', f_, 1.535, 0.05, 0.13)
    lathe(f'{name}_beret', [(0.0, 0.03), (0.08, 0.03), (0.15, 0.015), (0.16, 0.0), (0.11, -0.01), (0.0, -0.005)], 28, M_BERET, f_, loc=(0.01, 0, 1.83)).rotation_euler = (R(-6), R(12), 0)
    prim('uv_sphere', f'{name}_feather', M_WHITE, f_, loc=(0.12, 0.02, 1.88), segments=10, ring_count=6, radius=0.05, scale=(1.6, 0.4, 0.6))
    hands = Vector((0.0, -0.21, 1.13))
    for s_ in (-1, 1):
        tube(f'{name}_sl{s_}', [(s_ * 0.19, 0, 1.43), (s_ * 0.2, -0.05, 1.27), (s_ * 0.12, -0.17, 1.15), (s_ * 0.035, -0.205, 1.13)], lambda u: 0.055 - 0.02 * u, M_REDC if s_ < 0 else M_YELC, f_, seg=12)
        prim('uv_sphere', f'{name}_hand{s_}', M_DUMMY, f_, loc=(s_ * 0.022, -0.212, 1.13 + s_ * 0.035), segments=12, ring_count=8, radius=0.032)
    return f_, hands
GD1, HANDS1 = guard('gd1', PX - 0.45)
GD2, HANDS2 = guard('gd2', PX + 0.45)
# the second guard's banner on a pole (a cloth that ripples)
POLE = tube('pole', [(0.0, -0.21, 0.03), (0.0, -0.21, 2.55)], 0.016, M_WOOD, GD2, seg=10)
prim('cone', 'poletip', M_GOLD, GD2, loc=(0.0, -0.21, 2.6), vertices=12, radius1=0.03, radius2=0.0, depth=0.1)
FLAG_W, FLAG_H, FLN, FLM = 0.7, 0.45, 14, 8
vs = [(0.016 + FLAG_W * i / FLN, -0.21, 2.5 - FLAG_H * j / FLM) for j in range(FLM + 1) for i in range(FLN + 1)]
fs = [(j * (FLN + 1) + i, j * (FLN + 1) + i + 1, (j + 1) * (FLN + 1) + i + 1, (j + 1) * (FLN + 1) + i) for j in range(FLM) for i in range(FLN)]
FLAG = mesh('flag', vs, fs, cloth_mat('flagc', (0.55, 0.40, 0.05), 0.8, 0.5, 100.0, 4.0), GD2); FLAG.modifiers.new('sd', 'SOLIDIFY').thickness = 0.004
FLAG_REST = [Vector(v) for v in vs]
PSIGN = placard('plaq5', (PX + 1.05, 2.8, 0), -12, 'CARRIED IN\nPARADES')
PSTAMP = empty('pstamp', PSIGN, loc=(0, -0.06, 0.98)); PSTAMP.rotation_euler = (R(55), 0, R(-8))
text3d('pstmp', 'NOT FOR\nBATTLE', 0.075, (0, 0, 0), (0, 0, 0), M_STAMP, PSTAMP, extrude=0.003)

# ================================================================ exhibit 6: the museum wall - a fan of real swords and a parade sword hung as if for war (x = 20.3)
WDX = 20.3
box('wpanel', (2.0, 0.03, 2.4), (WDX, 5.37, 2.65), M_PANEL, bv=0.01, parent=HALL)
box('wpanelf', (2.1, 0.02, 2.5), (WDX, 5.385, 2.65), M_GILT, bv=0.01, parent=HALL)
def wall_mat(a, x, z):
    """a sword hung on the wall at angle a (from +x, in the wall plane), flats facing the room"""
    xa = Vector((math.cos(a), 0, math.sin(a))); za = Vector((0, -1, 0)); ya = za.cross(xa)
    m_ = Matrix((xa, ya, za)).transposed().to_4x4(); m_.translation = (x, 5.3, z); return m_
WSW = []                                                    # (object, rest matrix) - they drop onto their pins in turn
for k, (a_, x_, z_, kind) in enumerate(((R(60), WDX - 0.7, 1.75, 'arm'), (R(120), WDX + 0.7, 1.75, 'arm'), (R(75), WDX - 0.45, 2.1, 'two'), (R(105), WDX + 0.45, 2.1, 'two'))):
    o = sword(f'ws{k}', None, 0.76 if kind == 'arm' else 1.05, 0.026, 0.004, 0.2 if kind == 'arm' else 0.36, 0.1 if kind == 'arm' else 0.27, 0.032,
              M_BLADE if k % 2 else M_BLADE2, M_HILTI, M_LEATHER)
    WSW.append((o, wall_mat(a_, x_, z_)))
WG = sword('wgiant', None, 1.59, 0.038, 0.005, 0.55, 0.42, 0.05, M_BLADE2, M_GILT, M_LEATHER, kind='bearing')
WSW.append((WG, wall_mat(R(90), WDX, 1.55)))
for o, m_ in WSW:
    o.matrix_basis = m_
    for d_ in (0.25, 0.6): prim('cylinder', f'{o.name}_pin{d_}', M_BRASS, HALL, loc=m_ @ Vector((d_ if o.name != 'wgiant' else d_ * 1.6, 0, 0.0)) + Vector((0, 0.03, 0)), rot=(R(90), 0, 0), vertices=10, radius=0.008, depth=0.06)
PLQ = empty('plq', HALL, loc=(WDX, 5.24, 1.3))
box('plqb', (0.8, 0.02, 0.2), (0, 0, 0), M_PLAQ, bv=0.005, parent=PLQ)
box('plqf', (0.84, 0.024, 0.24), (0, 0.004, 0), M_GILT, bv=0.005, parent=PLQ)
text3d('plqt', 'SWORD OF WAR', 0.075, (0, -0.012, 0), (R(90), 0, 0), M_GILT, PLQ, extrude=0.002)
text3d('plqt2', 'PARADE SWORD', 0.075, (0, 0.016, 0), (R(-90), 0, 0), M_STAMP, PLQ, extrude=0.002)
STRIKE = box('strike', (0.68, 0.004, 0.02), (0, -0.016, 0), M_STAMP, parent=PLQ)
SC4, ND4, TOP4 = dial_scale('sc4', HALL, (WDX + 0.0, 4.5, PLAT_Z)); TOP4 += PLAT_Z
MYTH_P2 = Vector((WDX - 0.4, 4.5 + 0.14, MYTH_P.z - TOP1 + TOP4))
