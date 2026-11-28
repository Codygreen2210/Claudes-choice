
# ================================================================ set: a museum hall (x -4..30.8), the bull's story in exhibits along the back wall
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
M_WAINS = noisy(mat('wains', (0.13, 0.05, 0.035), 0.6, coat=0.06), 20.0, 0.15)
M_CEIL = noisy(mat('ceil', (0.30, 0.29, 0.27), 0.9), 2.0, 0.1)
M_BRASS = mat('brass', (0.78, 0.55, 0.22), 0.28, 1.0)
M_WOOD = noisy(mat('wood', (0.26, 0.14, 0.065), 0.55, coat=0.15), 14.0, 0.3)
M_WOODDK = noisy(mat('wooddk', (0.08, 0.045, 0.025), 0.5, coat=0.12), 14.0, 0.3)
M_PAPER = noisy(mat('paper', (0.80, 0.74, 0.60), 0.8), 8.0, 0.08)
M_PARCH = noisy(mat('parch', (0.72, 0.6, 0.4), 0.85), 6.0, 0.18)
M_INK = mat('ink', (0.01, 0.01, 0.012), 0.3); M_GREY = mat('greyink', (0.22, 0.22, 0.22), 0.6)
M_GOLD = mat('gold', (0.85, 0.62, 0.25), 0.25, 1.0)
M_PLAQ = mat('plaq', (0.06, 0.05, 0.045), 0.5); M_GILT = mat('gilt', (0.9, 0.7, 0.32), 0.3, 1.0)
M_BLACK = mat('blackm', (0.02, 0.02, 0.02), 0.6); M_IRON = noisy(mat('iron', (0.06, 0.06, 0.065), 0.55, 0.8), 30.0, 0.3)
M_RED = mat('red', (0.55, 0.04, 0.04), 0.6); M_WHITE = mat('white', (0.85, 0.84, 0.80), 0.6)
M_STAMP = mat('stamp', (0.75, 0.04, 0.03), 0.6)
M_GREENINK = mat('greenink', (0.02, 0.32, 0.07), 0.5)
M_REDV = noisy(mat('redv', (0.42, 0.02, 0.03), 0.8, sheen=0.5), 40.0, 0.2)
M_STEEL = mat('steel', (0.6, 0.61, 0.63), 0.25, 1.0); M_LEATHER = noisy(mat('leather', (0.16, 0.08, 0.035), 0.45, coat=0.2), 40.0, 0.2)
M_BRONZE = bronze_mat('bronze'); M_EYE = mat('eye', (0.01, 0.01, 0.01), 0.05, coat=1.0); M_HOLE = emis('hole', (0, 0, 0), 0.0)
M_MARBLE = noisy(mat('marble', (0.82, 0.8, 0.76), 0.3, coat=0.2), 5.0, 0.08)
M_STONE = noisy(mat('stone', (0.2, 0.18, 0.16), 0.85), 9.0, 0.3)
M_SEA = noisy(mat('sea', (0.08, 0.22, 0.38), 0.5), 4.0, 0.15); M_LAND = noisy(mat('land', (0.68, 0.56, 0.36), 0.8), 7.0, 0.15)
M_BLUEP = noisy(mat('bluep', (0.03, 0.12, 0.32), 0.7), 5.0, 0.12); M_CHALK = mat('chalk', (0.85, 0.9, 0.95), 0.6)
M_SQ1 = mat('sq1', (0.75, 0.68, 0.52), 0.4); M_SQ2 = mat('sq2', (0.16, 0.09, 0.05), 0.4)
M_PAWNW = mat('pawnw', (0.82, 0.78, 0.68), 0.35, coat=0.3); M_PAWNB = noisy(mat('pawnb', (0.35, 0.2, 0.09), 0.4, coat=0.3), 20.0, 0.3)
M_FLAME = emis('flame', (1.0, 0.42, 0.06), 9.0); M_FLAME2 = emis('flame2', (1.0, 0.8, 0.25), 12.0)
M_STEAM = mat('steam', (0.85, 0.85, 0.85), 0.95, alpha=0.14); M_STEAM.blend_method = 'BLEND'
M_RING = emis_mix('ringm', (1.0, 0.75, 0.35), 6.0, 'fade')
M_WATER = mat('water', (0.06, 0.25, 0.32), 0.04, trans=0.15, ior=1.33, coat=0.6)
_wnt = M_WATER.node_tree; _wb = _wnt.nodes['Principled BSDF']; WATER_MAP = _wnt.nodes.new('ShaderNodeMapping'); _wnt.links.new(coord(_wnt, 'Object'), WATER_MAP.inputs['Vector'])
_wbp = _wnt.nodes.new('ShaderNodeBump'); _wbp.inputs['Strength'].default_value = 0.3; _wbp.inputs['Distance'].default_value = 0.01
_wnt.links.new(tnoise(_wnt, WATER_MAP.outputs['Vector'], 7.0, 3.0, 1.5), _wbp.inputs['Height']); _wnt.links.new(_wbp.outputs['Normal'], _wb.inputs['Normal'])
M_RIPPLE = mat('ripple', (0.8, 0.9, 0.95), 0.1, alpha=0.5); M_RIPPLE.blend_method = 'BLEND'

# ---------------------------------------------------------------- the museum hall
HX0, HX1 = -4.0, 30.8; HW = HX1 - HX0; HC = (HX0 + HX1) / 2
HALL = empty('hall')
box('hfloor', (HW, 13.0, 0.2), (HC, -0.9, -0.1), M_WOODF, parent=HALL)
box('hback', (HW, 0.3, 6.0), (HC, 5.55, 3.0), M_PLASTER, parent=HALL)
box('hwains', (HW, 0.06, 1.0), (HC, 5.38, 0.5), M_WAINS, bv=0.01, parent=HALL)
box('hrail', (HW, 0.08, 0.05), (HC, 5.36, 1.02), M_GILT, parent=HALL)
box('hfront', (HW, 0.3, 6.0), (HC, -7.55, 3.0), M_PLASTER, parent=HALL)
box('hleft', (0.3, 13.0, 6.0), (HX0 - 0.15, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hright', (0.3, 13.0, 6.0), (HX1 + 0.15, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hceil', (HW, 13.4, 0.3), (HC, -0.9, 6.15), M_CEIL, parent=HALL)
for xb in range(-3, 31, 3): box(f'beam{xb}', (0.3, 13.0, 0.35), (xb + 0.5, -0.9, 5.83), M_WOOD, bv=0.01, parent=HALL)
RAIL = box('rail', (HW - 0.8, 0.08, 0.06), (HC, 0.4, 5.55), M_BLACK, parent=HALL)
MUSEUM_LIGHTS = []                                  # (light, base energy)
SPOTS = {}
def track_spot(key_, x, target, e=900, size=0.12, ang=46):
    p = Vector((x, 0.4, 5.45)); can = prim('cylinder', f'can{key_}', M_BLACK, HALL, loc=p, vertices=16, radius=0.07, depth=0.22)
    can.rotation_mode = 'QUATERNION'; can.rotation_quaternion = (Vector(target) - p).to_track_quat('-Z', 'Y')
    lt = light_at(f'spot{key_}', 'SPOT', p, target, e, (1.0, 0.92, 0.80), size); lt.data.spot_size = R(ang); lt.data.spot_blend = 0.6
    MUSEUM_LIGHTS.append((lt, e)); SPOTS[key_] = (lt, e); return lt
for k, xa in enumerate((-1.0, 5.4, 11.8, 18.2, 24.6, 29.8)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 330, (1.0, 0.93, 0.84), 3.0), 330))


def wall_sign(name, x, z, body, w=1.6, h=0.42, size=0.2, m_bg=None, m_txt=None, y=5.37):
    P_ = empty(name, HALL, loc=(x, y, z))
    box(name + 'b', (w, 0.02, h), (0, 0, 0), m_bg or M_PLAQ, bv=0.006, parent=P_)
    box(name + 'f', (w + 0.05, 0.016, h + 0.05), (0, 0.006, 0), M_GILT, bv=0.006, parent=P_)
    text3d(name + 't', body, size, (0, -0.012, 0), (R(90), 0, 0), m_txt or M_GILT, P_, extrude=0.003); return P_


def tent_card(name, loc, body, size, m_txt, w=0.24, h=0.12, rz=0.0, m_card=None):
    """a little folded card standing on a table, text on its front (-y) face; pivot at its base"""
    c_ = empty(name, HALL, loc=loc); c_.rotation_euler = (0, 0, rz)
    for s_ in (-1, 1): box(f'{name}{s_}', (w, 0.004, h), (0, s_ * h * 0.2, h * 0.48), m_card or M_PAPER, rot=(R(-12 * s_), 0, 0), parent=c_)
    text3d(name + 't', body, size, (0, -h * 0.2 - 0.009, h * 0.47), (R(78), 0, 0), m_txt, c_, extrude=0.001); return c_


PLAT_Z = 0.12
M_PLATM = noisy(mat('platm', (0.10, 0.06, 0.04), 0.5, coat=0.2), 10.0, 0.2)
def platform(x, w, d=1.5, y=4.15):
    box(f'plat{x}', (w, d, PLAT_Z), (x, y, PLAT_Z / 2), M_PLATM, bv=0.01, parent=HALL)


def puffs(name, n, m=None):
    return [prim('uv_sphere', f'{name}{k}', m or M_STEAM, HALL, loc=(0, 0, -50), segments=14, ring_count=8, radius=1.0) for k in range(n)]


# ================================================================ exhibit 0: the Brazen Bull on its turntable (x = 0)
X0, Y0 = 0.0, 3.75
lathe('dais0', [(0.0, 0.0), (1.08, 0.0), (1.08, 0.12), (1.04, 0.15), (0.0, 0.15)], 64, M_STONE, HALL, loc=(X0, Y0, 0))
TT0 = empty('tt0', HALL, loc=(X0, Y0, 0.15))
lathe('tt0d', [(0.0, 0.0), (0.98, 0.0), (0.98, 0.035), (0.0, 0.035)], 64, M_WOODDK, TT0)
for k in range(16): box(f'tt0s{k}', (0.12, 0.02, 0.006), (0.92 * math.cos(2 * math.pi * k / 16), 0.92 * math.sin(2 * math.pi * k / 16), 0.037), M_GILT, rot=(0, 0, 2 * math.pi * k / 16), parent=TT0)
BULL0, DH0, _ = bull('bull0', M_BRONZE, (0.06, 0, 0.035), 1.22, TT0, door=True)
STEAM0 = puffs('st0_', 10)
wall_sign('sg0', X0, 2.9, 'THE BRAZEN BULL', 2.3, 0.42, 0.17)
PLQ0 = empty('plq0', HALL, loc=(X0 - 0.16, Y0 - 1.085, 0.11))
box('plq0b', (0.34, 0.012, 0.07), (0.16, 0, 0), M_GILT, bv=0.004, parent=PLQ0)
text3d('plq0t', 'LEGEND', 0.04, (0.16, -0.008, 0), (R(90), 0, 0), M_INK, PLQ0, extrude=0.001)
prim('uv_sphere', 'plq0s', M_BRASS, HALL, loc=(X0 - 0.16, Y0 - 1.093, 0.11), segments=8, ring_count=6, radius=0.007)
track_spot('e0', X0, (X0, Y0, 0.8), 1100, ang=44)

# ================================================================ exhibit 1: Sicily - a wall map with a pin; the ruler's bust; the year (x = 3.6)
X1 = 3.6
MAP1 = empty('map1', HALL, loc=(X1 + 0.38, 5.35, 1.66))
box('map1s', (1.2, 0.02, 0.86), (0, 0, 0), M_SEA, bv=0.005, parent=MAP1)
box('map1f', (1.26, 0.018, 0.92), (0, 0.008, 0), M_GILT, bv=0.006, parent=MAP1)
MAP1.scale = (1.25, 1.25, 1.25)
def flat_poly(name, pts, m, parent, y=-0.014, th=0.008):
    """a flat island shape on a wall map (local x-z plane), standing out toward -y"""
    vs = [(x_, y, z_) for x_, z_ in pts] + [(x_, y + th, z_) for x_, z_ in pts]; n = len(pts)
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=False)
SICILY = [(-0.42, 0.12), (-0.2, 0.17), (0.05, 0.16), (0.28, 0.19), (0.38, 0.2), (0.33, 0.07), (0.3, -0.06), (0.36, -0.2), (0.24, -0.26),
          (0.1, -0.18), (-0.06, -0.12), (-0.22, -0.06), (-0.36, -0.02), (-0.44, 0.06)]
flat_poly('sic1', SICILY, M_LAND, MAP1)
flat_poly('ita1', [(0.42, 0.43), (0.5, 0.3), (0.47, 0.24), (0.55, 0.22), (0.6, 0.3), (0.6, 0.43)], M_LAND, MAP1)
text3d('map1t', 'SICILY', 0.1, (-0.02, -0.026, 0.03), (R(90), 0, 0), M_INK, MAP1, extrude=0.001)
PIN1_REST = Vector((-0.06, -0.03, -0.1))           # Akragas, on the south coast
PIN1 = empty('pin1', MAP1)
tube('pin1n', [(0, 0, 0), (0, -0.05, 0)], 0.003, M_STEEL, PIN1, seg=6)
prim('uv_sphere', 'pin1h', M_STAMP, PIN1, loc=(0, -0.055, 0), segments=12, ring_count=8, radius=0.022)
YEAR1 = wall_sign('sg1', X1 + 0.38, 2.6, '570 BC', 0.9, 0.36, 0.17)
def marble_bust(name, x, y, h, label, crown=False, beard=False, s=1.25):
    """a marble bust on a column (top at h): shoulders, neck, a head with brow, nose, ears and a hair cap. Returns (root, the bust part)"""
    rt = empty(name, HALL, loc=(x, y, 0))
    lathe(name + 'c', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.06), (0.13, 0.1), (0.11, h - 0.08), (0.18, h - 0.04), (0.18, h), (0.0, h)], 32, M_MARBLE, rt)
    box(name + 'nb', (0.34, 0.012, 0.06), (0, -0.12, h - 0.25), M_GILT, bv=0.003, parent=rt)
    text3d(name + 'nt', label, 0.036, (0, -0.127, h - 0.25), (R(90), 0, 0), M_INK, rt, extrude=0.001)
    up = empty(name + 'u', rt, loc=(0, 0, h)); up.scale = (s, s, s)
    lathe(name + 't', [(0.0, 0.0), (0.07, 0.0), (0.07, 0.04), (0.2, 0.1), (0.23, 0.2), (0.16, 0.3), (0.06, 0.34), (0.0, 0.34)], 28, M_MARBLE, up).scale = (1.0, 0.6, 1.0)
    lathe(name + 'n', [(0.0, 0.3), (0.056, 0.3), (0.05, 0.43), (0.0, 0.43)], 16, M_MARBLE, up)
    def sph(n_, loc, r, sc): return prim('uv_sphere', name + n_, M_MARBLE, up, loc=loc, segments=24, ring_count=14, radius=r, scale=sc)
    sph('h', (0, 0, 0.52), 0.105, (0.88, 1.0, 1.12)); sph('jw', (0, -0.035, 0.455), 0.07, (0.95, 0.95, 0.7))
    sph('no', (0, -0.1, 0.515), 0.02, (0.75, 1.0, 1.5)); sph('br', (0, -0.07, 0.565), 0.075, (1.05, 0.5, 0.28))
    sph('hc', (0, 0.018, 0.57), 0.108, (0.93, 1.0, 0.78))
    for sx in (-1, 1): sph(f'ea{sx}', (0.094 * sx, 0.0, 0.52), 0.026, (0.4, 0.8, 1.2))
    if beard: sph('bd', (0, -0.055, 0.44), 0.065, (1.0, 0.75, 0.85))
    if crown:
        lathe(name + 'k', [(0.093, 0.0), (0.105, 0.0), (0.105, 0.04), (0.093, 0.04)], 32, M_GOLD, up, loc=(0, 0.01, 0.58))
        for k in range(6):
            a_ = 2 * math.pi * k / 6; prim('cone', f'{name}p{k}', M_GOLD, up, loc=(0.1 * math.cos(a_), 0.01 + 0.1 * math.sin(a_), 0.64), vertices=8, radius1=0.017, radius2=0.002, depth=0.05)
    return rt, up
BUST1, BUSTUP = marble_bust('bust1', X1 - 0.62, 4.6, 1.0, 'PHALARIS', crown=True, beard=True)
BUSTUP_REST = BUSTUP.location.copy()
track_spot('e1', X1, (X1, 4.9, 1.5), 950, ang=52)

# ================================================================ exhibit 2: the workshop - plans, the model bull on a stand over a fire pit (x = 7.2)
X2, Y2 = 7.2, 4.0
platform(X2, 2.2)
STAND_Z = PLAT_Z + 0.62
for sx in (-1, 1):
    for sy in (-1, 1): tube(f'st2l{sx}{sy}', [(X2 + 0.36 * sx, Y2 + 0.22 * sy, PLAT_Z), (X2 + 0.33 * sx, Y2 + 0.2 * sy, STAND_Z)], 0.016, M_IRON, HALL, seg=8)
for k in range(7): tube(f'st2g{k}', [(X2 - 0.34, Y2 - 0.2 + 0.4 * k / 6, STAND_Z), (X2 + 0.34, Y2 - 0.2 + 0.4 * k / 6, STAND_Z)], 0.009, M_IRON, HALL, seg=6)
for sy in (-1, 1): tube(f'st2r{sy}', [(X2 - 0.36, Y2 + 0.21 * sy, STAND_Z), (X2 + 0.36, Y2 + 0.21 * sy, STAND_Z)], 0.013, M_IRON, HALL, seg=8)
lathe('pit2', [(0.0, PLAT_Z), (0.3, PLAT_Z), (0.32, PLAT_Z + 0.08), (0.26, PLAT_Z + 0.09), (0.0, PLAT_Z + 0.05)], 32, noisy(mat('ash', (0.035, 0.03, 0.028), 0.9), 20.0, 0.4), HALL, loc=(X2, Y2, 0))
for k in range(5):
    a_ = R(36 * k + 10); prim('cylinder', f'log2{k}', M_WOODDK, HALL, loc=(X2 + 0.07 * math.cos(a_), Y2 + 0.07 * math.sin(a_), PLAT_Z + 0.1), rot=(0, R(90), a_), vertices=12, radius=0.028, depth=0.36)
MODEL_S = 0.62
MODEL2, DH2, HOLE2 = bull('bull2', M_BRONZE, (X2 - 0.04, Y2, -50), MODEL_S, HALL, door=True)
MODEL2_REST = Vector((X2 - 0.04, Y2, STAND_Z + 0.009))
FIRE2 = flames('fl2_', None, 12, (0.13, 0.1), 31, 0.0); FIRE2_ROOT = empty('fire2', HALL, loc=(X2, Y2, PLAT_Z + 0.12))
for o, *_ in FIRE2: o.parent = FIRE2_ROOT
FIRELT2 = light_at('firelt2', 'POINT', (X2, Y2 - 0.1, PLAT_Z + 0.35), (X2, Y2, 0), 0.0, (1.0, 0.5, 0.15), 0.1)
# the padlock that snaps onto the door (bull local coords: the door's front edge)
LOCK2 = empty('lock2', MODEL2, loc=(0.095, -0.245, 0.63))
box('lk2b', (0.05, 0.02, 0.045), (0, 0, -0.02), M_BRASS, bv=0.006, parent=LOCK2)
tube('lk2s', [(-0.016, 0, 0.0), (-0.016, 0, 0.03), (0.0, 0, 0.042), (0.016, 0, 0.03), (0.016, 0, 0.0)], 0.005, M_STEEL, LOCK2, seg=8)
# brass pipes in its nostrils, and the sound rings that come out of them
PIPES2 = []
for k, p_ in enumerate(BULL_NPZ['nose']):
    pp = empty(f'pipe2{k}', MODEL2, loc=tuple(p_)); pp.rotation_euler = (0, R(90), R(8) * (1 if k else -1))
    prim('cone', f'pipe2c{k}', M_BRASS, pp, loc=(0, 0, 0.045), vertices=16, radius1=0.012, radius2=0.03, depth=0.09)
    PIPES2.append(pp)
RINGS2 = []
for k in range(6):
    o = lathe(f'ring2{k}', [(0.8, -0.06), (1.0, -0.06), (1.0, 0.06), (0.8, 0.06)], 40, M_RING, HALL, loc=(0, 0, -50)); o.rotation_euler = (0, R(90), 0); o['fade'] = 0.0
    RINGS2.append(o)
STEAM2 = puffs('st2_', 8)
# the plans: a blueprint unrolls down the wall
SCRL2 = empty('scrl2', HALL, loc=(X2 + 0.05, 5.34, 2.55))
prim('cylinder', 'scrl2rod', M_WOODDK, HALL, loc=(X2 + 0.05, 5.33, 2.56), rot=(0, R(90), 0), vertices=12, radius=0.025, depth=1.2)
SHEET2 = empty('sheet2', SCRL2)
box('sh2b', (1.05, 0.006, 0.75), (0, 0, -0.375), M_BLUEP, parent=SHEET2)
def chalk_line(name, pts, par, r=0.0045):
    return tube(name, [(x_, -0.006, z_) for x_, z_ in pts], r, M_CHALK, par, seg=5)
_bo = [(-0.36, -0.3), (-0.36, -0.52), (-0.33, -0.66), (-0.3, -0.66), (-0.3, -0.5), (0.18, -0.5), (0.2, -0.66), (0.24, -0.66), (0.25, -0.48),
       (0.3, -0.38), (0.38, -0.36), (0.44, -0.42), (0.47, -0.37), (0.41, -0.28), (0.34, -0.2), (0.22, -0.16), (0.05, -0.18), (-0.25, -0.18), (-0.36, -0.3)]
chalk_line('sh2o', _bo, SHEET2)
for s_ in (-1, 1): chalk_line(f'sh2h{s_}', [(0.36, -0.22), (0.4 + 0.02 * s_, -0.14), (0.46 + 0.03 * s_, -0.1)], SHEET2, 0.004)
chalk_line('sh2d', [(-0.17, -0.27), (0.02, -0.27), (0.02, -0.42), (-0.17, -0.42), (-0.17, -0.27)], SHEET2, 0.004)
text3d('sh2t', 'BRONZE BULL', 0.05, (0.0, -0.007, -0.08), (R(90), 0, 0), M_CHALK, SHEET2, extrude=0.0006)
text3d('sh2d2', 'DOOR', 0.032, (-0.075, -0.007, -0.345), (R(90), 0, 0), M_CHALK, SHEET2, extrude=0.0006)
SCRL2.scale = (1, 1, 1e-4)
wall_sign('sg2', X2 - 0.95, 2.35, 'ATHENS\nWORKSHOP', 0.8, 0.42, 0.11)
track_spot('e2', X2, (X2, 4.2, 1.2), 1000, ang=50)

# ================================================================ exhibit 3: the game board - the king, the inventor pawn, the people, a little bronze bull (x = 10.6)
X3, Y3 = 10.6, 4.05
box('tab3', (0.9, 0.7, 0.76), (X3, Y3, 0.38), M_WOODDK, bv=0.012, parent=HALL)
box('tab3t', (0.96, 0.76, 0.03), (X3, Y3, 0.775), M_WOOD, bv=0.006, parent=HALL)
TOP3 = 0.79
SQ = 0.075
for i in range(8):
    for j in range(8): box(f'sq3_{i}{j}', (SQ, SQ, 0.008), (X3 + (i - 3.5) * SQ, Y3 + (j - 3.5) * SQ, TOP3 + 0.004), M_SQ1 if (i + j) % 2 else M_SQ2, parent=HALL)
box('sq3f', (8 * SQ + 0.04, 8 * SQ + 0.04, 0.006), (X3, Y3, TOP3 + 0.003), M_GILT, parent=HALL)
TOP3 += 0.008
TOK3, DH3, HOLE3 = bull('bull3', M_BRONZE, (X3 + 0.17, Y3 + 0.12, TOP3), 0.24, HALL, door=True)
KING3 = piece('king3', 'king', M_GOLD, (X3 - 0.08, Y3 - 0.06, TOP3), 1.15)
INV3 = piece('inv3', 'pawn', M_PAWNB, (X3 - 0.22, Y3 - 0.12, TOP3), 1.0)
CROWD3 = []
for k in range(9):
    a_ = R(120 + 25 * k); p_ = Vector((X3 - 0.08 + 0.2 * math.cos(a_), Y3 - 0.06 + 0.17 * math.sin(a_), TOP3))
    if p_.y < Y3 - 0.29: p_.y = Y3 - 0.29
    CROWD3.append((piece(f'crowd3{k}', 'pawn', M_PAWNW, p_, 0.92), p_))
wall_sign('sg3', X3, 2.35, 'THE LEGEND', 1.1, 0.4, 0.14)
track_spot('e3', X3, (X3, Y3, 0.8), 950, ang=40)

# ================================================================ exhibit 4: the record - a lectern and an old book; a timeline on the wall (x = 14.0)
X4 = 14.0
platform(X4, 1.8)
box('lect4', (0.62, 0.46, 0.95), (X4 - 0.42, 4.0, PLAT_Z + 0.475), M_WOODDK, bv=0.01, parent=HALL)
BK4 = empty('bk4', HALL, loc=(X4 - 0.42, 4.0, PLAT_Z + 1.0)); BK4.rotation_euler = (R(32), 0, 0); BK4.scale = (1.75, 1.75, 1.75)
box('bk4sp', (0.02, 0.24, 0.02), (0, 0, 0.0), M_LEATHER, parent=BK4)
PG4 = []
for s_ in (-1, 1):
    pv = empty(f'bk4pv{s_}', BK4, loc=(0, 0, 0.012))
    box(f'bk4c{s_}', (0.2, 0.26, 0.012), (s_ * 0.1, 0, 0), M_WOODDK, bv=0.003, parent=pv)
    box(f'bk4p{s_}', (0.19, 0.25, 0.01), (s_ * 0.1, 0, 0.011), M_PARCH, parent=pv)
    PG4.append((pv, s_))
text3d('bk4t', 'THE BULL\nOF PHALARIS', 0.02, (-0.1, 0.03, 0.0175), (0, 0, 0), M_INK, PG4[0][0], extrude=0.0005)
for k in range(5): box(f'bk4la{k}', (0.13, 0.006, 0.001), (-0.1, -0.03 - 0.02 * k, 0.017), M_GREY, parent=PG4[0][0])
for k in range(8): box(f'bk4l{k}', (0.13, 0.006, 0.001), (0.1, 0.08 - 0.022 * k, 0.017), M_GREY, parent=PG4[1][0])
STAMP4 = empty('stamp4', BK4, loc=(0.03, 0.0, 0.03)); STAMP4.rotation_euler = (0, 0, R(12))
text3d('stamp4t', 'MADE UP?', 0.055, (0, 0, 0), (0, 0, 0), M_STAMP, STAMP4, extrude=0.002)
QM4 = empty('qm4', HALL, loc=(X4 - 0.42, 4.1, PLAT_Z + 1.62))
text3d('qm4t', '?', 0.45, (0, 0, 0), (R(90), 0, 0), M_STAMP, QM4, extrude=0.04)
TL4 = empty('tl4', HALL, loc=(X4 + 0.32, 5.36, 1.95)); TL4.scale = (0.9, 0.9, 0.9)
box('tl4b', (1.5, 0.02, 0.7), (0, 0, 0), M_PLAQ, bv=0.006, parent=TL4)
box('tl4f', (1.56, 0.016, 0.76), (0, 0.006, 0), M_GILT, bv=0.006, parent=TL4)
for sx, tx in ((-1, '570 BC\nTHE RULER'), (1, '60 BC\nSTORY WRITTEN')):
    box(f'tl4m{sx}', (0.025, 0.012, 0.16), (0.55 * sx, -0.014, -0.08), M_GILT, parent=TL4)
    text3d(f'tl4t{sx}', tx, 0.055, (0.55 * sx, -0.016, -0.24), (R(90), 0, 0), M_GILT, TL4, extrude=0.002)
TLBAR = empty('tlbar', TL4, loc=(-0.55, -0.016, -0.08))
box('tl4bar', (1.1, 0.012, 0.03), (0.55, 0, 0), M_STAMP, parent=TLBAR); TLBAR.scale = (1e-4, 1, 1)
TLTXT = text3d('tl4y', '500 YEARS', 0.09, (0, -0.016, 0.12), (R(90), 0, 0), M_GILT, TL4, extrude=0.003)
track_spot('e4', X4, (X4, 4.6, 1.5), 950, ang=52)

# ================================================================ exhibit 5: the twist - a table map; the bull token rides to Carthage and home (x = 17.6)
X5, Y5 = 17.6, 4.0
box('tab5', (1.4, 0.9, 0.8), (X5, Y5, 0.4), M_WOODDK, bv=0.012, parent=HALL)
box('tab5t', (1.46, 0.96, 0.03), (X5, Y5, 0.815), M_WOOD, bv=0.006, parent=HALL)
TOP5 = 0.83
MAP5 = empty('map5', HALL, loc=(X5, Y5, TOP5))
box('map5s', (1.3, 0.8, 0.006), (0, 0, 0.003), M_SEA, parent=MAP5)
def flat_xy(name, pts, m, parent, z=0.006, th=0.006):
    vs = [(x_, y_, z) for x_, y_ in pts] + [(x_, y_, z + th) for x_, y_ in pts]; n = len(pts)
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=False)
flat_xy('sic5', [(p_[0] * 0.6 + 0.22, p_[1] * 0.6 + 0.2) for p_ in SICILY], M_LAND, MAP5)
flat_xy('ita5', [(0.5, 0.4), (0.5, 0.34), (0.53, 0.3), (0.6, 0.32), (0.64, 0.4)], M_LAND, MAP5)
flat_xy('afr5', [(-0.65, -0.4), (-0.65, -0.05), (-0.5, -0.02), (-0.36, -0.06), (-0.27, -0.1), (-0.22, -0.06), (-0.17, -0.13), (-0.18, -0.22),
                 (-0.08, -0.26), (0.05, -0.3), (0.2, -0.34), (0.4, -0.36), (0.65, -0.33), (0.65, -0.4)], M_LAND, MAP5)
AKR5 = Vector((0.18, 0.1, 0.012)); CAR5 = Vector((-0.24, -0.12, 0.012))
for nm_, p_, tx_ in (('ak5', AKR5, 'AKRAGAS'), ('ca5', CAR5, 'CARTHAGE')):
    prim('cylinder', nm_ + 'd', M_STAMP, MAP5, loc=tuple(p_ + Vector((0, 0, 0.002))), vertices=16, radius=0.016, depth=0.006)
CARLBL5 = text3d('ca5t', 'CARTHAGE', 0.045, (-0.26, -0.2, 0.017), (0, 0, 0), M_INK, MAP5, extrude=0.001)
text3d('ak5t', 'SICILY', 0.04, (0.24, 0.27, 0.016), (0, 0, 0), M_INK, MAP5, extrude=0.001)
def arc5(u, bend=0.16):
    p_ = AKR5.lerp(CAR5, u); d = (CAR5 - AKR5); nrm = Vector((-d.y, d.x, 0)).normalized()
    return p_ + nrm * bend * math.sin(math.pi * u)
DOTS5 = [prim('uv_sphere', f'dot5{k}', M_INK, MAP5, loc=tuple(arc5((k + 1) / 12) + Vector((0, 0, 0.0))), segments=8, ring_count=5, radius=0.006) for k in range(11)]
TOK5, _, _ = bull('bull5', M_BRONZE, (0, 0, 0), 0.17, MAP5, door=False)
REAL5 = empty('real5', HALL, loc=(X5 + 0.44, Y5 - 0.43, TOP5 + 0.005)); REAL5.rotation_euler = (R(-58), 0, R(4))
box('rl5b', (0.36, 0.006, 0.14), (0, 0, 0.07), M_WHITE, bv=0.004, parent=REAL5)
box('rl5f', (0.38, 0.004, 0.16), (0, 0.004, 0.07), M_GREENINK, parent=REAL5)
text3d('rl5t', 'REAL', 0.09, (0, -0.006, 0.07), (R(90), 0, 0), M_GREENINK, REAL5, extrude=0.002)
CARD5A = tent_card('cd5a', (X5 - 0.42, Y5 + 0.36, TOP5), '406 BC', 0.05, M_INK, 0.22, 0.11)
CARD5B = tent_card('cd5b', (X5 + 0.0, Y5 + 0.36, TOP5), '146 BC', 0.05, M_STAMP, 0.22, 0.11)
# a Roman helmet with a red crest, dropped by Carthage
HELM5 = empty('helm5', HALL)
lathe('hl5d', [(0.0, 0.12), (0.05, 0.118), (0.085, 0.1), (0.1, 0.06), (0.105, 0.0), (0.112, -0.005), (0.112, 0.0), (0.0, 0.0)], 32, M_STEEL, HELM5).scale = (1.0, 1.12, 1.0)
for sx in (-1, 1): box(f'hl5c{sx}', (0.012, 0.06, 0.08), (0.1 * sx, -0.03, -0.035), M_BRASS, rot=(0, R(-8 * sx), 0), parent=HELM5)
tube('hl5r', [(0, 0.11, 0.11), (0, 0.04, 0.17), (0, -0.05, 0.16), (0, -0.1, 0.11)], 0.022, M_REDV, HELM5, seg=10)
HELM5_REST = Vector((X5 - 0.36, Y5 - 0.27, TOP5 + 0.006 + 0.005)); HELM5.location = (0, 0, -60)
wall_sign('sg5', X5, 2.35, 'THE REAL BULL', 1.4, 0.4, 0.14)
track_spot('e5', X5, (X5, Y5, 0.85), 950, ang=44)

# ================================================================ exhibit 6: the Roman writer - a marble bust; a scroll unrolls (x = 21.0)
X6 = 21.0
BUST6, _ = marble_bust('bust6', X6 - 0.35, 4.6, 1.0, 'CICERO')
SCRL6 = empty('scrl6', HALL, loc=(X6 + 0.42, 5.34, 2.2))
prim('cylinder', 'scrl6rod', M_WOODDK, HALL, loc=(X6 + 0.42, 5.32, 2.21), rot=(0, R(90), 0), vertices=12, radius=0.022, depth=0.78)
box('sc6b', (0.66, 0.006, 0.8), (0, 0, -0.4), M_PARCH, parent=SCRL6)
text3d('sc6t', 'A REMINDER\nOF HOW CRUEL\nTHEIR OLD\nRULERS WERE', 0.058, (0, -0.007, -0.38), (R(90), 0, 0), M_INK, SCRL6, extrude=0.0008)
ROLL6 = prim('cylinder', 'scrl6bot', M_WOODDK, HALL, loc=(X6 + 0.42, 5.31, 2.2), rot=(0, R(90), 0), vertices=12, radius=0.026, depth=0.74)
SCRL6.scale = (1, 1, 1e-4)
wall_sign('sg6', X6, 2.75, 'ROME', 0.8, 0.36, 0.15)
track_spot('e6', X6, (X6, 4.8, 1.5), 950, ang=48)

# ================================================================ exhibit 7: a river statue - a bronze bull on a rock in a stone pool of running water (x = 24.2)
X7, Y7 = 24.2, 4.0
for nm_, sz_, lc_ in (('pool7a', (1.5, 0.06, 0.34), (X7, Y7 - 0.37, 0.17)), ('pool7b', (1.5, 0.06, 0.34), (X7, Y7 + 0.37, 0.17)),
                      ('pool7c', (0.06, 0.8, 0.34), (X7 - 0.72, Y7, 0.17)), ('pool7d', (0.06, 0.8, 0.34), (X7 + 0.72, Y7, 0.17))):
    box(nm_, sz_, lc_, M_STONE, bv=0.012, parent=HALL)
WATER7 = box('water7', (1.38, 0.68, 0.02), (X7, Y7, 0.28), M_WATER, parent=HALL)
box('pool7in', (1.38, 0.68, 0.02), (X7, Y7, 0.08), mat('poolbt', (0.05, 0.08, 0.08), 0.8), parent=HALL)
lathe('rock7', [(0.0, 0.05), (0.26, 0.05), (0.27, 0.2), (0.22, 0.38), (0.0, 0.4)], 12, M_STONE, HALL, loc=(X7, Y7, 0)).scale = (1.3, 0.8, 1.0)
STAT7, _, _ = bull('bull7', M_BRONZE, (0, 0, -60), 0.55, HALL, door=False)
STAT7_REST = Vector((X7 - 0.02, Y7, 0.4))
RIPS7 = [lathe(f'rip7{k}', [(0.94, 0.0), (1.0, 0.0), (1.0, 0.003), (0.94, 0.003)], 40, M_RIPPLE, HALL, loc=(0, 0, -60)) for k in range(6)]
SPL7 = puffs('spl7_', 10, M_RIPPLE)
wall_sign('sg7', X7, 2.35, 'RIVER GOD?', 1.3, 0.4, 0.15)
track_spot('e7', X7, (X7, Y7, 0.4), 950, ang=44)

# ================================================================ exhibit 8: lost - an empty plinth (x = 27.6)
X8, Y8 = 27.6, 4.0
box('plin8', (0.8, 0.8, 0.9), (X8, Y8, 0.45), M_MARBLE, bv=0.015, parent=HALL)
box('plin8t', (0.86, 0.86, 0.04), (X8, Y8, 0.92), M_MARBLE, bv=0.01, parent=HALL)
box('dust8', (0.62, 0.3, 0.002), (X8, Y8, 0.941), mat('dust8m', (0.62, 0.6, 0.56), 0.95), parent=HALL)
box('plq8b', (0.42, 0.012, 0.1), (X8, Y8 - 0.407, 0.62), M_GILT, bv=0.003, parent=HALL)
text3d('plq8t', 'LOCATION\nUNKNOWN', 0.032, (X8, Y8 - 0.414, 0.62), (R(90), 0, 0), M_INK, HALL, extrude=0.001)
QM8 = empty('qm8', HALL, loc=(X8, Y8, 1.32))
text3d('qm8t', '?', 0.5, (0, 0, 0), (R(90), 0, 0), M_GILT, QM8, extrude=0.04)
GHOST8, _, _ = bull('bull8', mat('ghost8', (0.9, 0.85, 0.7), 0.5, alpha=0.18), (0, 0, -60), 0.5, HALL, door=False)
wall_sign('sg8', X8, 2.6, 'LOST', 1.0, 0.4, 0.2)
track_spot('e8', X8, (X8, Y8, 0.95), 1000, ang=36)
