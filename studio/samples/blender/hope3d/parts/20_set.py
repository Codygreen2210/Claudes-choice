
# ================================================================ set: a museum hall (x -4..36), the Hope's story in exhibits along the back wall
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
M_WAINS = noisy(mat('wains', (0.06, 0.07, 0.12), 0.45, coat=0.3), 20.0, 0.15)
M_CEIL = noisy(mat('ceil', (0.30, 0.29, 0.27), 0.9), 2.0, 0.1)
M_BRASS = mat('brass', (0.78, 0.55, 0.22), 0.28, 1.0)
M_WOOD = noisy(mat('wood', (0.26, 0.14, 0.065), 0.55, coat=0.15), 14.0, 0.3)
M_WOODDK = noisy(mat('wooddk', (0.08, 0.045, 0.025), 0.5, coat=0.12), 14.0, 0.3)
M_PAPER = noisy(mat('paper', (0.80, 0.74, 0.60), 0.8), 8.0, 0.08)
M_NEWS = noisy(mat('news', (0.78, 0.76, 0.70), 0.85), 10.0, 0.1)
M_INK = mat('ink', (0.01, 0.01, 0.012), 0.3); M_GREY = mat('greyink', (0.22, 0.22, 0.22), 0.6)
M_GOLD = mat('gold', (0.85, 0.62, 0.25), 0.25, 1.0); M_PLAT = mat('plat', (0.80, 0.80, 0.82), 0.15, 1.0)
M_PLAQ = mat('plaq', (0.06, 0.05, 0.045), 0.5); M_GILT = mat('gilt', (0.9, 0.7, 0.32), 0.3, 1.0)
M_BLACK = mat('blackm', (0.02, 0.02, 0.02), 0.6)
M_GLASS = mat('glass', (0.92, 0.96, 1.0), 0.02, trans=1.0, ior=1.45)
M_RED = mat('red', (0.55, 0.04, 0.04), 0.6); M_WHITE = mat('white', (0.85, 0.84, 0.80), 0.6)
M_STAMP = mat('stamp', (0.75, 0.04, 0.03), 0.6)
M_DUMMY = noisy(mat('dummy', (0.42, 0.40, 0.37), 0.7, sheen=0.3), 6.0, 0.15)
M_NAVYV = cloth_mat('navyv', (0.012, 0.016, 0.05), 0.8, 0.8, 140.0, 2.0)
M_REDV = cloth_mat('redv', (0.30, 0.015, 0.025), 0.8, 0.8, 120.0, 4.0)
M_ROYAL = cloth_mat('royal', (0.02, 0.05, 0.28), 0.8, 0.5, 120.0, 5.0)
M_CORK = noisy(mat('cork', (0.40, 0.27, 0.15), 0.9), 60.0, 0.35)
M_KRAFT = noisy(mat('kraft', (0.45, 0.30, 0.16), 0.85), 18.0, 0.2)
M_STRING = mat('string', (0.75, 0.68, 0.52), 0.8)
M_UNIF = cloth_mat('unif', (0.10, 0.14, 0.24), 0.85, 0.4, 150.0, 6.0)
M_LEATHER = noisy(mat('leather', (0.16, 0.08, 0.035), 0.45, coat=0.2), 40.0, 0.2)
M_STEEL = mat('steel', (0.6, 0.61, 0.63), 0.25, 1.0)
M_YELLOW = mat('yellow', (0.85, 0.62, 0.03), 0.5)
M_HOPE = gem_mat('hope', (0.05, 0.16, 0.85), (0.08, 0.22, 1.0), glow_col=(1.0, 0.1, 0.02))
M_WHITE_D = gem_mat('whited', (0.95, 0.97, 1.0), (0.9, 0.92, 1.0))
M_ROUGH = mat('roughst', (0.10, 0.14, 0.55), 0.45, trans=0.7, ior=2.42); M_ROUGH.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (0.1, 0.12, 0.6, 1)
M_ROUGH.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.4
M_SPINEL = gem_mat('spinel', (0.8, 0.04, 0.06)); M_EMER = gem_mat('emer', (0.04, 0.6, 0.15))
M_GHOST = emis('ghost', (0.2, 0.9, 1.0), 6.0)
M_CHECK = emis('check', (0.15, 1.0, 0.25), 5.0)
M_SPARK = emis('spark', (1.0, 0.7, 0.3), 30.0)
M_UVTUBE = emis('uvtube', (0.45, 0.15, 1.0), 12.0)

HOPE_ME = gem_mesh('hope_me', CUSHION, 0.0425, 0.036, n=16)
SMALL_ME = gem_mesh('small_me', ROUND, 0.0075, 0.0075, n=8)
FB_ME = gem_mesh('fb_me', SHIELD, 0.088, 0.08, n=18)
GHOST_ME = gem_mesh('ghost_me', SHIELD, 0.088, 0.08, n=18)
HOPEB_ME = gem_mesh('hopeb_me', CUSHION, 0.068, 0.058, n=16)

# ---------------------------------------------------------------- the museum hall
HALL = empty('hall')
box('hfloor', (40.8, 13.0, 0.2), (16.0, -0.9, -0.1), M_WOODF, parent=HALL)
box('hback', (40.8, 0.3, 6.0), (16.0, 5.55, 3.0), M_PLASTER, parent=HALL)
box('hwains', (40.8, 0.06, 1.0), (16.0, 5.38, 0.5), M_WAINS, bv=0.01, parent=HALL)
box('hrail', (40.8, 0.08, 0.05), (16.0, 5.36, 1.02), M_GILT, parent=HALL)
box('hfront', (40.8, 0.3, 6.0), (16.0, -7.55, 3.0), M_PLASTER, parent=HALL)
box('hleft', (0.3, 13.0, 6.0), (-4.35, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hright', (0.3, 13.0, 6.0), (36.35, -0.9, 3.0), M_PLASTER, parent=HALL)
box('hceil', (40.8, 13.4, 0.3), (16.0, -0.9, 6.15), M_CEIL, parent=HALL)
for xb in range(-3, 37, 3): box(f'beam{xb}', (0.3, 13.0, 0.35), (xb + 0.5, -0.9, 5.83), M_WOOD, bv=0.01, parent=HALL)
RAIL = box('rail', (40.0, 0.08, 0.06), (16.0, 0.4, 5.55), M_BLACK, parent=HALL)
MUSEUM_LIGHTS = []                                  # (light, base energy)
SPOTS = {}
def track_spot(key_, x, target, e=900, size=0.12, ang=46):
    p = Vector((x, 0.4, 5.45)); can = prim('cylinder', f'can{key_}', M_BLACK, HALL, loc=p, vertices=16, radius=0.07, depth=0.22)
    can.rotation_mode = 'QUATERNION'; can.rotation_quaternion = (Vector(target) - p).to_track_quat('-Z', 'Y')
    lt = light_at(f'spot{key_}', 'SPOT', p, target, e, (1.0, 0.92, 0.80), size); lt.data.spot_size = R(ang); lt.data.spot_blend = 0.6
    MUSEUM_LIGHTS.append((lt, e)); SPOTS[key_] = (lt, e); return lt
for k, xa in enumerate((1.5, 8.5, 15.5, 22.5, 29.5, 35.0)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 330, (1.0, 0.93, 0.84), 3.0), 330))
G = random.Random(7)


def wall_sign(name, x, z, body, w=1.6, h=0.42, size=0.2, m_bg=None, m_txt=None):
    P_ = empty(name, HALL, loc=(x, 5.37, z))
    box(name + 'b', (w, 0.02, h), (0, 0, 0), m_bg or M_PLAQ, bv=0.006, parent=P_)
    box(name + 'f', (w + 0.05, 0.016, h + 0.05), (0, 0.006, 0), M_GILT, bv=0.006, parent=P_)
    text3d(name + 't', body, size, (0, -0.012, 0), (R(90), 0, 0), m_txt or M_GILT, P_, extrude=0.003); return P_


PLAT_Z = 0.12
M_PLAT = noisy(mat('platm', (0.10, 0.06, 0.04), 0.5, coat=0.2), 10.0, 0.2)
def platform(x, w, d=1.5, y=4.15):
    box(f'plat{x}', (w, d, PLAT_Z), (x, y, PLAT_Z / 2), M_PLAT, bv=0.01, parent=HALL)


def glass_case(name, x, y, w=0.62, d=0.56, z0=1.0, h=0.66):
    """a pedestal and a glass case on it: four panes, a lid and brass corner posts. Returns (root, front pane z range)"""
    rt = empty(name, HALL, loc=(x, y, 0))
    box(f'{name}_ped', (w + 0.08, d + 0.08, z0), (0, 0, z0 / 2), M_WOODDK, bv=0.012, parent=rt)
    box(f'{name}_pedt', (w + 0.12, d + 0.12, 0.03), (0, 0, z0 - 0.015), M_GILT, bv=0.006, parent=rt)
    box(f'{name}_slot', (0.54, 0.24, 0.004), (0, 0.02, z0 + 0.002), M_NAVYV, parent=rt)
    t_ = 0.008
    box(f'{name}_gf', (w, t_, h), (0, -d / 2, z0 + h / 2), M_GLASS, parent=rt)
    box(f'{name}_gb', (w, t_, h), (0, d / 2, z0 + h / 2), M_GLASS, parent=rt)
    for s_ in (-1, 1): box(f'{name}_gs{s_}', (t_, d, h), (s_ * w / 2, 0, z0 + h / 2), M_GLASS, parent=rt)
    box(f'{name}_gt', (w, d, t_), (0, 0, z0 + h), M_GLASS, parent=rt)
    for sx in (-1, 1):
        for sy in (-1, 1): box(f'{name}_post{sx}{sy}', (0.014, 0.014, h), (sx * w / 2, sy * d / 2, z0 + h / 2), M_BRASS, parent=rt)
    for sy in (-1, 1): box(f'{name}_tr{sy}', (w, 0.014, 0.014), (0, sy * d / 2, z0 + h), M_BRASS, parent=rt)
    for sx in (-1, 1): box(f'{name}_tr{sx}x', (0.014, d, 0.014), (sx * w / 2, 0, z0 + h), M_BRASS, parent=rt)
    return rt


def display_board(name, parent, loc, tilt=R(-18), w=0.5, h=0.56):
    """an angled navy velvet board with the necklace on it; the root's local x-z plane is the board face (facing -y)"""
    bd = empty(name, parent, loc=loc); bd.rotation_euler = (tilt, 0, 0)
    box(f'{name}_v', (w, 0.03, h), (0, 0.015, 0.03), M_NAVYV, bv=0.01, parent=bd)
    tube(f'{name}_leg', [(0, 0.05, -0.25), (0, 0.16, -0.32)], 0.012, M_BRASS, bd, seg=8)
    return bd


# ================================================================ exhibit 0: the Hope Diamond in its case (x = 0) - it rises, the lights flicker, the glass cracks
X0, Y0 = 0.0, 3.75
CASE0 = glass_case('case0', X0, Y0)
BD0 = display_board('bd0', HALL, (X0, Y0 + 0.02, 1.31))
NK0, HOPE0 = necklace('nk0', BD0, M_HOPE, M_WHITE_D, M_PLAT, HOPE_ME, SMALL_ME)
BD0_REST = BD0.location.copy()
PLQ0 = empty('plq0', HALL, loc=(X0 - 0.13, Y0 - 0.327, 0.78))           # the pedestal plaque hangs from its left screw
box('plq0b', (0.3, 0.012, 0.09), (0.13, 0, 0), M_GILT, bv=0.004, parent=PLQ0)
text3d('plq0t', 'HOPE DIAMOND', 0.032, (0.13, -0.008, 0), (R(90), 0, 0), M_INK, PLQ0, extrude=0.001)
prim('uv_sphere', 'plq0s', M_BRASS, HALL, loc=(X0 - 0.13, Y0 - 0.335, 0.78), segments=8, ring_count=6, radius=0.007)
CRACK = []                                     # a zig-zag crack across the front pane, drawn in segments
cp_ = Vector((X0 + 0.22, Y0 - 0.285, 1.52)); gr_ = random.Random(5)
for k in range(9):
    nxt = cp_ + Vector((-0.055 + gr_.uniform(-0.02, 0.02), 0, -0.035 + gr_.uniform(-0.03, 0.03)))
    CRACK.append(tube(f'crk{k}', [cp_, nxt], 0.0018, M_WHITE, HALL, seg=5, caps=True)); cp_ = nxt
    if k == 3: br_ = cp_.copy()
CRACK.append(tube('crkb', [br_, br_ + Vector((0.03, 0, -0.07))], 0.0016, M_WHITE, HALL, seg=5))
for o in CRACK: o.hide_render = True
track_spot('e0', X0, (X0, Y0, 1.2), 1000, ang=40)
wall_sign('sg0', X0, 2.75, 'THE HOPE DIAMOND', 2.2, 0.42, 0.17)

# ================================================================ exhibit 1: from India to King Louis XIV - a rough stone is cut into the French Blue (x = 3.4)
X1 = 3.4
platform(X1, 2.0)
lathe('col1', [(0.0, PLAT_Z), (0.2, PLAT_Z), (0.2, PLAT_Z + 0.05), (0.09, PLAT_Z + 0.09), (0.08, 0.92), (0.2, 0.95), (0.2, 1.0), (0.0, 1.0)], 32, M_WOODDK, HALL, loc=(X1 - 0.2, 3.85, 0))
CUSH1 = box('cush1', (0.36, 0.36, 0.07), (X1 - 0.2, 3.85, 1.035), M_REDV, bv=0.03, parent=HALL); subsurf(CUSH1, 2)
CUSH1_TOP = 1.06
for sx in (-1, 1):
    for sy in (-1, 1): prim('uv_sphere', f'tass{sx}{sy}', M_GOLD, HALL, loc=(X1 - 0.2 + sx * 0.18, 3.85 + sy * 0.18, 1.035), segments=8, ring_count=6, radius=0.014)
ROUGH = rough_stone('rough', M_ROUGH, 0.095, HALL, loc=(X1 - 0.2, 3.85, CUSH1_TOP + 0.04))
FB1 = gem_obj('fb1', FB_ME, M_HOPE, HALL, loc=(X1 - 0.2, 3.85, CUSH1_TOP + 0.023), rot=(R(-12), 0, 0))
FB1_REST = rest_on(FB1, CUSH1_TOP - 0.004)
ROUGH_REST = rest_on(ROUGH, CUSH1_TOP - 0.006)
# the cutting wheel beside the cushion
WHEEL_C = Vector((X1 + 0.13, 3.85, 1.15))
lathe('whst', [(0.0, PLAT_Z), (0.12, PLAT_Z), (0.12, PLAT_Z + 0.04), (0.03, PLAT_Z + 0.06), (0.025, 1.03), (0.0, 1.03)], 20, M_WOODDK, HALL, loc=(X1 + 0.13, 3.95, 0))
box('whfork', (0.03, 0.03, 0.14), (X1 + 0.13, 3.95, 1.08), M_STEEL, parent=HALL)
tube('whaxle', [(X1 + 0.13, 3.84, 1.15), (X1 + 0.13, 3.96, 1.15)], 0.008, M_STEEL, HALL, seg=8)
WHEEL = empty('wheel', HALL, loc=WHEEL_C)
wl_ = lathe('whd', [(0.0, -0.012), (0.085, -0.012), (0.09, -0.006), (0.09, 0.006), (0.085, 0.012), (0.0, 0.012)], 40, M_STEEL, WHEEL); wl_.rotation_euler = (R(90), 0, 0)
for k in range(6): box(f'whsp{k}', (0.15, 0.004, 0.01), (0, -0.016, 0), M_BRASS, rot=(0, R(30 * k), 0), parent=WHEEL)
prim('cylinder', 'whhub', M_BRASS, WHEEL, loc=(0, -0.018, 0), rot=(R(90), 0, 0), vertices=16, radius=0.022, depth=0.02)
SPARKS = []
gs_ = random.Random(11)
for k in range(28):
    o = prim('uv_sphere', f'spk{k}', M_SPARK, HALL, loc=(0, 0, -50), segments=6, ring_count=4, radius=0.005)
    SPARKS.append((o, gs_.uniform(-1.6, -0.3), gs_.uniform(-0.6, 0.3), gs_.uniform(0.4, 1.6), gs_.uniform(0, 0.55)))
# King Louis XIV: a royal banner unrolls on the wall and a crown lands on a small stand
BAN1 = empty('ban1', HALL, loc=(X1 + 0.2, 5.36, 2.6))
box('ban1c', (1.4, 0.015, 1.05), (0, 0, -0.53), M_ROYAL, parent=BAN1)
box('ban1g', (1.46, 0.012, 1.11), (0, 0.004, -0.53), M_GILT, parent=BAN1)
text3d('ban1t', 'KING\nLOUIS XIV', 0.19, (0, -0.012, -0.5), (R(90), 0, 0), M_GILT, BAN1, extrude=0.004)
prim('cylinder', 'ban1rod', M_GOLD, HALL, loc=(X1 + 0.2, 5.35, 2.61), rot=(0, R(90), 0), vertices=12, radius=0.018, depth=1.65)
box('crst', (0.22, 0.22, 0.62), (X1 + 0.58, 4.25, PLAT_Z + 0.31), M_WOODDK, bv=0.01, parent=HALL)
box('crstv', (0.2, 0.2, 0.03), (X1 + 0.58, 4.25, PLAT_Z + 0.635), M_REDV, bv=0.01, parent=HALL)
def crown(name, r=0.1, h=0.07):
    c_ = empty(name)
    lathe(f'{name}_band', [(r * 0.92, 0.0), (r, 0.0), (r, h), (r * 0.92, h)], 40, M_GOLD, c_)
    for k in range(5):
        a = 2 * math.pi * k / 5; prim('cone', f'{name}_pt{k}', M_GOLD, c_, loc=(r * 0.97 * math.cos(a), r * 0.97 * math.sin(a), h + 0.035), vertices=10, radius1=0.022, radius2=0.004, depth=0.07)
        prim('uv_sphere', f'{name}_pb{k}', M_GOLD, c_, loc=(r * 0.97 * math.cos(a), r * 0.97 * math.sin(a), h + 0.075), segments=8, ring_count=5, radius=0.01)
        prim('ico_sphere', f'{name}_gm{k}', M_SPINEL if k % 2 else M_HOPE, c_, loc=(r * 1.0 * math.cos(a + 0.63), r * 1.0 * math.sin(a + 0.63), h * 0.5), subdivisions=1, radius=0.012)
    prim('uv_sphere', f'{name}_cap', M_REDV, c_, loc=(0, 0, h * 0.6), segments=16, ring_count=8, radius=r * 0.88, scale=(1, 1, 0.75))
    return c_
CROWN1 = crown('crown1'); CROWN1_REST = Vector((X1 + 0.58, 4.25, PLAT_Z + 0.65))
track_spot('e1', X1, (X1, 3.95, 1.0), 950, ang=50)

# ================================================================ exhibit 2: 1792 - the French crown jewels case is emptied by thieves (x = 6.8)
X2 = 6.8
platform(X2, 1.9)
box('tab2', (1.0, 0.6, 0.86), (X2, 3.95, PLAT_Z + 0.43), M_WOODDK, bv=0.012, parent=HALL)
box('tab2v', (0.94, 0.54, 0.02), (X2, 3.95, PLAT_Z + 0.87), M_REDV, parent=HALL)
TOP2 = PLAT_Z + 0.88
LID2 = empty('lid2', HALL, loc=(X2, 3.95 + 0.3, TOP2 + 0.16))                # hinged at the back edge
box('lid2g', (0.98, 0.6, 0.008), (0, -0.3, 0), M_GLASS, parent=LID2)
for sy in (0.0, -0.6): box(f'lid2f{sy}', (1.0, 0.02, 0.02), (0, sy, 0), M_GILT, parent=LID2)
for sx in (-0.5, 0.5): box(f'lid2s{sx}', (0.02, 0.6, 0.02), (sx, -0.3, 0), M_GILT, parent=LID2)
for sx in (-0.5, 0.5):
    for sy in (-0.3, 0.3): box(f'tab2w{sx}{sy}', (0.012, 0.012, 0.16), (X2 + sx, 3.95 + sy, TOP2 + 0.08), M_GILT, parent=HALL)
box('tab2gf', (0.98, 0.006, 0.15), (X2, 3.95 - 0.3, TOP2 + 0.08), M_GLASS, parent=HALL)
for sx in (-1, 1): box(f'tab2gs{sx}', (0.006, 0.58, 0.15), (X2 + sx * 0.49, 3.95, TOP2 + 0.08), M_GLASS, parent=HALL)
box('tab2gb', (0.98, 0.006, 0.15), (X2, 3.95 + 0.3, TOP2 + 0.08), M_GLASS, parent=HALL)
CROWN2 = crown('crown2', 0.075, 0.05); CROWN2.location = (X2 - 0.27, 3.98, TOP2)
JEWELS2 = [CROWN2]
for k, (mm, dx) in enumerate(((M_SPINEL, -0.06), (M_EMER, 0.1), (M_WHITE_D, 0.27))):
    o = gem_obj(f'j2_{k}', gem_mesh(f'j2me{k}', ROUND if k != 0 else SHIELD, 0.042, 0.036, n=12), mm, HALL, loc=(X2 + dx, 3.9 + 0.04 * k, TOP2 + 0.012), rot=(0, 0, 0))
    JEWELS2.append(o)
# the French Blue in its gold setting (the Golden Fleece badge, simplified to a gold frame) at the front
FB2R = empty('fb2r', HALL, loc=(X2 + 0.02, 3.78, TOP2 + 0.013))
lathe('fb2set', [(0.092, -0.006), (0.106, -0.006), (0.106, 0.008), (0.092, 0.008)], 32, M_GOLD, FB2R).scale = (1.0, 0.92, 1.0)
gem_obj('fb2', FB_ME, M_HOPE, FB2R, loc=(0, 0, 0.0), rot=(0, 0, 0))
for k in range(4): prim('uv_sphere', f'fb2b{k}', M_GOLD, FB2R, loc=(0.112 * math.cos(math.pi / 2 * k + 0.78), 0.104 * math.sin(math.pi / 2 * k + 0.78), 0), segments=8, ring_count=5, radius=0.013)
POOF = []
gp_ = random.Random(19)
for k in range(22):
    o = gem_obj(f'poof{k}', SMALL_ME, M_WHITE_D, HALL, loc=(0, 0, -50)); POOF.append((o, Vector((gp_.uniform(-1, 1), gp_.uniform(-1, 1), gp_.uniform(-0.3, 1.2))).normalized() * gp_.uniform(0.25, 0.5), gp_.uniform(0, 6)))
SIGN2 = wall_sign('sg2', X2, 2.4, 'FRENCH CROWN\nJEWELS', 1.5, 0.62, 0.15)
YEAR2 = text3d('yr2', '1792', 0.3, (X2, 5.37, 1.7), (R(90), 0, 0), M_GILT, HALL, extrude=0.012)
STAMP2 = empty('stamp2', SIGN2, loc=(0.05, -0.03, 0.0)); STAMP2.rotation_euler = (0, R(-9), 0)
text3d('stamp2t', 'STOLEN', 0.17, (0, 0, 0), (R(90), 0, 0), M_STAMP, STAMP2, extrude=0.004)
track_spot('e2', X2, (X2, 3.95, 1.0), 950, ang=44)

# ================================================================ portraits: an oval gilt frame, a dark painted ground, a flat silhouette bust (local x-z plane, facing -y)
M_PORT = mat('portbg', (0.09, 0.08, 0.05), 0.7); M_SIL = mat('sil', (0.012, 0.01, 0.01), 0.6)
def portrait(name, x, z, kind, w=0.45, h=0.6, y=5.33):
    """returns the root (pivot at the top screw, so it can swing crooked)"""
    rt = empty(name, HALL, loc=(x, y, z + h / 2 + 0.01)); c_ = empty(name + 'c', rt, loc=(0, 0, -h / 2 - 0.01))
    fr = lathe(name + 'f', [(0.86, -0.018), (1.0, -0.018), (1.0, 0.018), (0.86, 0.018)], 40, M_GILT, c_); fr.rotation_euler = (R(90), 0, 0); fr.scale = (w / 2, h / 2, 1)
    bg = lathe(name + 'g', [(0.0, 0.0), (0.88, 0.0), (0.88, 0.004), (0.0, 0.004)], 40, M_PORT, c_, loc=(0, 0.002, 0)); bg.rotation_euler = (R(90), 0, 0); bg.scale = (w / 2, h / 2, 1)
    sc = w / 0.45
    def blob(n_, loc, r3): return prim('uv_sphere', f'{name}_{n_}', M_SIL, c_, loc=(loc[0] * sc, -0.006, loc[1] * sc), segments=24, ring_count=12, radius=1.0, scale=(r3[0] * sc, 0.004, r3[1] * sc))
    blob('sh', (0, -0.19), (0.16, 0.085)); blob('nk', (0, -0.08), (0.03, 0.06)); blob('hd', (0.0, 0.0), (0.062, 0.08))
    if kind == 'king':
        for s_ in (-1, 1): blob(f'wg{s_}', (0.05 * s_, -0.02), (0.045, 0.09))
    elif kind == 'queen':
        blob('hr', (0, 0.1), (0.07, 0.11)); blob('hr2', (0, 0.06), (0.08, 0.06))
    elif kind == 'lady':
        blob('hr', (0, 0.04), (0.075, 0.06)); gem_obj(f'{name}_gem', SMALL_ME, M_HOPE, c_, loc=(0, -0.01, -0.115 * sc), rot=(R(90), 0, 0)).scale = (2.2, 2.2, 2.2)
    return rt


def photo_frame(name, loc, kind, parent=None):
    """a standing photo frame (0.2 x 0.26), pivot at its front bottom edge; rotation x: -12 deg leans back on its stand, +90 lies face down"""
    rt = empty(name, parent or HALL, loc=loc); rt.rotation_euler = (R(-12), 0, 0)
    box(name + 'f', (0.2, 0.018, 0.26), (0, 0.009, 0.13), M_GILT, bv=0.004, parent=rt)
    box(name + 'p', (0.16, 0.004, 0.22), (0, -0.002, 0.13), M_PAPER, parent=rt)
    def fig(n_, dx, hair=False, small=False, par=None):
        k_ = 0.7 if small else 1.0; par = par or rt
        prim('uv_sphere', f'{name}{n_}h', M_SIL, par, loc=(dx, -0.006, 0.17 * k_ + 0.02), segments=16, ring_count=8, radius=1.0, scale=(0.022 * k_, 0.002, 0.027 * k_))
        prim('uv_sphere', f'{name}{n_}b', M_SIL, par, loc=(dx, -0.006, 0.075 * k_ + 0.03), segments=16, ring_count=8, radius=1.0, scale=(0.04 * k_, 0.002, 0.07 * k_))
        if hair: prim('uv_sphere', f'{name}{n_}r', M_SIL, par, loc=(dx, -0.006, 0.2 * k_ + 0.02), segments=16, ring_count=8, radius=1.0, scale=(0.025, 0.002, 0.02))
    halves = []
    if kind == 'child': fig('a', 0.0, small=True)
    elif kind == 'lady': fig('a', 0.0, hair=True)
    elif kind == 'couple':          # the photo is two halves that can slide apart
        for s_ in (-1, 1):
            hv = empty(f'{name}hv{s_}', rt, loc=(0, 0, 0)); box(f'{name}hp{s_}', (0.08, 0.004, 0.22), (s_ * 0.04, -0.004, 0.13), M_PAPER, parent=hv)
            fig(f'c{s_}', s_ * 0.042, hair=s_ > 0, par=hv); halves.append((hv, s_))
    tube(name + 'leg', [(0, 0.018, 0.16), (0, 0.075, 0.004)], 0.004, M_GILT, rt, seg=6)
    return rt, halves


# ================================================================ exhibit K: 1793 - the king and the queen who owned it; their crowns tumble off (x = 10.2)
XK = 10.2
box('cnsk', (1.7, 0.34, 0.05), (XK, 5.18, 0.95), M_WOODDK, bv=0.01, parent=HALL)
box('cnska', (1.62, 0.04, 0.12), (XK, 5.03, 0.87), M_GILT, bv=0.005, parent=HALL)
for sx in (-0.78, 0.78): box(f'cnskl{sx}', (0.05, 0.05, 0.9), (XK + sx, 5.1, 0.47), M_WOODDK, bv=0.008, parent=HALL)
CNSK_TOP = 0.975
PORTK = portrait('portk', XK - 0.45, 1.93, 'king'); PORTQ = portrait('portq', XK + 0.45, 1.93, 'queen')
for nm_, xx_, tx_ in (('nmk', XK - 0.45, 'LOUIS XVI'), ('nmq', XK + 0.45, 'MARIE ANTOINETTE')):
    box(nm_ + 'b', (0.42, 0.012, 0.07), (xx_, 5.355, 1.53), M_GILT, bv=0.003, parent=HALL)
    text3d(nm_ + 't', tx_, 0.03 if len(tx_) < 12 else 0.024, (xx_, 5.347, 1.53), (R(90), 0, 0), M_INK, HALL, extrude=0.001)
CRWNS = []
for nm_, xx_ in (('kcrown', XK - 0.45), ('qcrown', XK + 0.45)):
    box(nm_ + 'sh', (0.22, 0.15, 0.02), (xx_, 5.28, 2.255), M_GILT, bv=0.004, parent=HALL)     # a little gilt shelf on the frame top
    c_ = crown(nm_, 0.085, 0.06); c_.location = (xx_, 5.26, 2.265); CRWNS.append((c_, Vector((xx_, 5.26, 2.265)), Vector((xx_ + (0.12 if xx_ < XK else -0.1), 5.1, CNSK_TOP + 0.085))))
YEARK = wall_sign('sgk', XK, 2.9, 'FRANCE\n1793', 1.0, 0.5, 0.14)
track_spot('ek', XK, (XK, 5.2, 1.6), 900, ang=46)

# ================================================================ exhibit 3: London, twenty years later - a smaller blue diamond; the scan outline of the French Blue fits round it (x = 13.6)
X3 = 13.6
platform(X3, 1.6)
lathe('col3', [(0.0, PLAT_Z), (0.18, PLAT_Z), (0.18, PLAT_Z + 0.05), (0.08, PLAT_Z + 0.09), (0.07, 0.96), (0.17, 0.99), (0.17, 1.03), (0.0, 1.03)], 32, M_WOODDK, HALL, loc=(X3, 3.85, 0))
box('tray3', (0.34, 0.34, 0.025), (X3, 3.85, 1.042), M_NAVYV, bv=0.008, parent=HALL)
TOP3 = 1.055
HOPE3 = gem_obj('hope3', HOPEB_ME, M_HOPE, HALL, loc=(X3, 3.85, TOP3 + 0.016), rot=(0, 0, 0))
HOPE3_REST = rest_on(HOPE3, TOP3 - 0.004)
GHOST = obj('ghost', GHOST_ME, M_GHOST, (X3, 3.85, TOP3 + 0.6), HALL)
wf_ = GHOST.modifiers.new('wf', 'WIREFRAME'); wf_.thickness = 0.0022; wf_.use_replace = True
GHOST.scale = (1e-4,) * 3
CHECK3 = empty('check3', HALL, loc=(X3 + 0.13, 3.7, 1.21))
tube('chk3a', [(-0.045, 0, 0.0), (-0.012, 0, -0.035), (0.055, 0, 0.05)], 0.008, M_CHECK, CHECK3, seg=8)
CHECK3.scale = (1e-4,) * 3
wall_sign('sg3', X3, 1.75, 'LONDON\n1812', 1.0, 0.5, 0.14)
track_spot('e3', X3, (X3, 3.85, 1.05), 950, ang=40)

# ================================================================ exhibit 4: the Hope family - a catalog opens, the HOPE nameplate letters drop in (x = 16.8)
X4 = 16.8
platform(X4, 1.8)
box('lect4', (0.56, 0.42, 1.0), (X4 - 0.28, 3.95, PLAT_Z + 0.5), M_WOODDK, bv=0.01, parent=HALL)
BK4 = empty('bk4', HALL, loc=(X4 - 0.28, 3.95, PLAT_Z + 1.02)); BK4.rotation_euler = (R(22), 0, 0); BK4.scale = (1.55, 1.55, 1.55)
box('bk4sp', (0.02, 0.24, 0.02), (0, 0, 0.0), M_NAVYV, parent=BK4)
PG4 = []
for s_ in (-1, 1):
    pv = empty(f'bk4pv{s_}', BK4, loc=(0, 0, 0.012))
    box(f'bk4c{s_}', (0.2, 0.26, 0.012), (s_ * 0.1, 0, 0), M_NAVYV, bv=0.003, parent=pv)
    box(f'bk4p{s_}', (0.19, 0.25, 0.01), (s_ * 0.1, 0, 0.011), M_PAPER, parent=pv)
    PG4.append((pv, s_))
text3d('bk4t', 'THE HOPE\nCOLLECTION\n1839', 0.022, (-0.1, 0.0, 0.0175), (0, 0, 0), M_INK, PG4[0][0], extrude=0.0005)
gem_obj('bk4gem', HOPE_ME, M_HOPE, PG4[1][0], loc=(0.1, 0.02, 0.035), rot=(0, 0, 0))
for k in range(3): box(f'bk4l{k}', (0.12, 0.006, 0.001), (0.1, -0.06 - 0.022 * k, 0.017), M_GREY, parent=PG4[1][0])
NAME4 = empty('name4', HALL, loc=(X4 + 0.25, 5.36, 1.95))
box('nm4b', (1.4, 0.02, 0.55), (0, 0, 0), M_PLAQ, bv=0.006, parent=NAME4)
box('nm4f', (1.46, 0.016, 0.61), (0, 0.006, 0), M_GILT, bv=0.006, parent=NAME4)
LET4 = [text3d(f'nm4l{k}', ch, 0.36, (-0.42 + 0.28 * k, -0.02, 0.03), (R(90), 0, 0), M_GILT, NAME4, extrude=0.02) for k, ch in enumerate('HOPE')]
LET4_REST = [o.location.copy() for o in LET4]
SUB4 = text3d('nm4s', 'HENRY PHILIP HOPE', 0.06, (0, -0.014, -0.2), (R(90), 0, 0), M_GILT, NAME4, extrude=0.002)
track_spot('e4', X4, (X4, 4.4, 1.5), 950, ang=50)

# ================================================================ exhibit 5: Pierre Cartier's counter sells it to the McLeans, with a scary story (x = 20.2)
X5 = 20.2
platform(X5 + 0.55, 1.6)
# the jeweler's counter: a glass-topped wooden counter; the necklace on its board; a SOLD tag, a little heap of gold coins
CX5 = X5 + 0.55
box('ctr5', (1.2, 0.55, 0.82), (CX5, 4.0, PLAT_Z + 0.41), M_WOODDK, bv=0.012, parent=HALL)
box('ctr5t', (1.24, 0.59, 0.03), (CX5, 4.0, PLAT_Z + 0.835), M_WOODDK, bv=0.006, parent=HALL)
TOP5 = PLAT_Z + 0.85
BD5 = display_board('bd5n', HALL, (CX5 - 0.15, 4.08, TOP5 + 0.33), tilt=R(-16))
NK5, HOPE5 = necklace('nk5', BD5, M_HOPE, M_WHITE_D, M_PLAT, HOPE_ME, SMALL_ME)
wall_sign('sg5', CX5 + 0.1, 2.75, 'CARTIER\n1910', 0.9, 0.5, 0.14)
TAG5 = empty('tag5', HALL, loc=(CX5 + 0.2, 3.95, TOP5 + 0.3))
tube('tag5s', [(0, 0, 0), (0.0, 0, -0.12)], 0.0015, M_STRING, TAG5, seg=5)
box('tag5b', (0.22, 0.004, 0.12), (0, 0, -0.18), M_PAPER, bv=0.004, parent=TAG5)
text3d('tag5t', 'SOLD', 0.065, (0, -0.004, -0.18), (R(90), 0, 0), M_STAMP, TAG5, extrude=0.001)
lathe('tag5post', [(0.0, TOP5), (0.03, TOP5), (0.03, TOP5 + 0.01), (0.006, TOP5 + 0.012), (0.006, TOP5 + 0.32), (0.0, TOP5 + 0.32)], 12, M_BRASS, HALL, loc=(CX5 + 0.2, 3.97, 0))
CARD5 = empty('card5', HALL, loc=(CX5 - 0.3, 3.8, TOP5)); CARD5_S = 1.6                 # "scary stories": a little tent card pops up
for s_ in (-1, 1): box(f'cd5{s_}', (0.2, 0.004, 0.11), (0, s_ * 0.022, 0.053), M_PAPER, rot=(R(-12 * s_), 0, 0), parent=CARD5)
text3d('cd5t', 'CURSED!', 0.034, (0, -0.031, 0.05), (R(78), 0, 0), M_STAMP, CARD5, extrude=0.001)
COINS = []
gc_ = random.Random(3)
for k in range(9):
    o = prim('cylinder', f'coin{k}', M_GOLD, HALL, loc=(0, 0, -50), vertices=20, radius=0.032, depth=0.006)
    COINS.append((o, Vector((CX5 + 0.43 + gc_.uniform(-0.07, 0.07), 3.86 + gc_.uniform(-0.035, 0.035), TOP5 + 0.0031 + 0.0062 * (k % 3))), gc_.uniform(-0.4, 0.4), 0.07 * k))
track_spot('e5b', CX5, (CX5, 4.0, 1.1), 900, ang=44)

# ================================================================ exhibit M: the McLeans - a portrait, a sideboard; photos fall, a photo splits, SOLD on the newspaper (x = 23.6)
XM = 23.6
platform(XM, 1.9)
box('sbm', (1.5, 0.45, 0.82), (XM, 4.35, PLAT_Z + 0.41), M_WOODDK, bv=0.012, parent=HALL)
box('sbmt', (1.56, 0.5, 0.035), (XM, 4.35, PLAT_Z + 0.837), M_WOOD, bv=0.008, parent=HALL)
for k in range(3): box(f'sbmd{k}', (0.44, 0.01, 0.6), (XM - 0.49 + 0.49 * k, 4.12, PLAT_Z + 0.42), M_WOOD, bv=0.006, parent=HALL)
TOPM = PLAT_Z + 0.855
PORTM = portrait('portm', XM, 1.85, 'lady', 0.52, 0.68)
box('nmmb', (0.5, 0.012, 0.07), (XM, 5.355, 1.67), M_GILT, bv=0.003, parent=HALL)
text3d('nmmt', 'EVALYN McLEAN', 0.028, (XM, 5.347, 1.67), (R(90), 0, 0), M_INK, HALL, extrude=0.001)
wall_sign('sgm', XM, 2.75, 'THE McLEANS\nWASHINGTON', 1.3, 0.5, 0.13)
PHM1, _ = photo_frame('phm1', (XM - 0.47, 4.26, TOPM), 'child')
PHM2, HALVES = photo_frame('phm2', (XM - 0.02, 4.3, TOPM), 'couple')
NEWSM = empty('newsm', HALL, loc=(XM + 0.46, 4.3, TOPM)); NEWSM.rotation_euler = (R(-28), 0, 0)
box('nwmst', (0.3, 0.02, 0.02), (0, -0.01, 0.01), M_BRASS, parent=NEWSM)
box('nwmp', (0.3, 0.005, 0.38), (0, 0.0, 0.2), M_NEWS, parent=NEWSM)
text3d('nwmh', 'THE POST', 0.045, (0, -0.004, 0.35), (R(90), 0, 0), M_INK, NEWSM, extrude=0.0008)
box('nwmr', (0.27, 0.003, 0.004), (0, -0.003, 0.32), M_INK, parent=NEWSM)
for j in range(8):
    for c in range(2): box(f'nwml{j}{c}', (0.12, 0.002, 0.01), (-0.07 + 0.14 * c, -0.003, 0.28 - 0.03 * j), M_GREY, parent=NEWSM)
STAMPM = empty('stampm', NEWSM, loc=(0.0, -0.012, 0.17)); STAMPM.rotation_euler = (0, R(-14), 0)
text3d('stampmt', 'SOLD', 0.1, (0, 0, 0), (R(90), 0, 0), M_STAMP, STAMPM, extrude=0.003)
track_spot('em', XM, (XM, 4.6, 1.3), 950, ang=50)

# ================================================================ exhibit B: the scare board - CURSED GEM, DOOMED DIAMOND: MADE UP; KILLED BY WOLVES - LIVED TO 84 (x = 26.8)
XB = 26.8
BOARD5 = empty('board5', HALL, loc=(XB, 5.36, 2.15))
box('bd5', (2.2, 0.03, 1.2), (0, 0, 0), M_CORK, bv=0.01, parent=BOARD5)
box('bd5f', (2.26, 0.025, 1.26), (0, 0.006, 0), M_WOOD, bv=0.01, parent=BOARD5)
def paper(k, hd, dx, dz, rz, size=0.07):
    np_ = empty(f'news{k}', BOARD5, loc=(dx, -0.03 - 0.004 * k, dz)); np_.rotation_euler = (0, R(rz), 0)
    box(f'nw{k}', (0.46, 0.004, 0.6), (0, 0, 0), M_NEWS, parent=np_)
    text3d(f'nwh{k}', hd, size, (0, -0.004, 0.17), (R(90), 0, 0), M_INK, np_, extrude=0.0008)
    box(f'nwr{k}', (0.42, 0.003, 0.006), (0, -0.003, 0.27), M_INK, parent=np_)
    for j in range(7):
        for c in range(2): box(f'nwl{k}{j}{c}', (0.18, 0.002, 0.012), (-0.105 + 0.21 * c, -0.003, -0.02 - 0.035 * j), M_GREY, parent=np_)
    return (np_, np_.location.copy(), np_.rotation_euler.copy())
NEWS = [paper(0, 'CURSED\nGEM!', -0.78, 0.1, 6), paper(1, 'DOOMED\nDIAMOND', -0.28, -0.06, -5)]
WOLFP = paper(2, 'KILLED BY\nWOLVES!', 0.55, 0.08, 4, 0.062)
STAMP5 = empty('stamp5', BOARD5, loc=(-0.52, -0.06, 0.0)); STAMP5.rotation_euler = (0, R(-12), 0)
text3d('stamp5t', 'MADE UP', 0.2, (0, 0, 0), (R(90), 0, 0), M_STAMP, STAMP5, extrude=0.005)
M_GREENINK = mat('greenink', (0.02, 0.32, 0.07), 0.5)
LIVED = empty('lived', BOARD5, loc=(0.55, -0.075, -0.1)); LIVED.rotation_euler = (0, R(-6), 0)
box('lvb', (0.5, 0.004, 0.17), (0, 0, 0), M_WHITE, bv=0.004, parent=LIVED)
box('lvf', (0.52, 0.003, 0.19), (0, 0.003, 0), M_GREENINK, parent=LIVED)
text3d('lvt', 'LIVED TO 84', 0.06, (0, -0.004, 0.0), (R(90), 0, 0), M_GREENINK, LIVED, extrude=0.001)
track_spot('eb', XB, (XB, 5.3, 2.15), 850, ang=46)

# ================================================================ exhibit 6: 1958 - a plain brown package, stamps, the mailman (x = 30.2)
X6 = 30.2
platform(X6 + 0.6, 2.6)
box('tab6', (1.1, 0.6, 0.72), (X6, 3.95, PLAT_Z + 0.36), M_WOOD, bv=0.012, parent=HALL)
TOP6 = PLAT_Z + 0.72
PKG = empty('pkg', HALL)
PW, PD, PH = 0.46, 0.32, 0.15
box('pkgb', (PW, PD, PH), (0, 0, PH / 2), M_KRAFT, bv=0.006, parent=PKG)
for sx_, sy_ in ((PW + 0.006, 0.008), (0.008, PD + 0.006)): box(f'pkgs{sx_}', (sx_, sy_, PH + 0.006), (0, 0, PH / 2), M_STRING, parent=PKG)
LABEL6 = empty('label6', PKG, loc=(-0.09, 0.0, PH + 0.0035))
box('lab6b', (0.2, 0.13, 0.002), (0, 0, 0), M_PAPER, parent=LABEL6)
text3d('lab6t', 'SMITHSONIAN\nWASHINGTON DC', 0.016, (0, 0, 0.0016), (0, 0, 0), M_INK, LABEL6, extrude=0.0003)
FRAG6 = empty('frag6', PKG, loc=(0.0, -PD / 2 - 0.0035, PH / 2)); FRAG6.rotation_euler = (R(90), 0, 0)
box('frg6b', (0.22, 0.065, 0.002), (0, 0, 0), M_STAMP, parent=FRAG6)
text3d('frg6t', 'FRAGILE', 0.04, (0, 0, 0.0016), (0, 0, 0), M_WHITE, FRAG6, extrude=0.0004)
STAMPS6 = []
for k in range(6):
    st = empty(f'pst{k}', PKG, loc=(0.075 + 0.05 * (k % 3), 0.07 - 0.065 * (k // 3), PH + 0.0035))
    box(f'pstb{k}', (0.042, 0.052, 0.002), (0, 0, 0), M_WHITE, parent=st); box(f'psti{k}', (0.032, 0.042, 0.002), (0, 0, 0.0006), M_STAMP, parent=st)
    STAMPS6.append(st)
PKG_REST = Vector((X6 - 0.05, 3.88, TOP6))
YEAR6 = wall_sign('sg6', X6, 2.2, '1958', 1.1, 0.5, 0.3)
TAG6 = empty('tag6', HALL, loc=(X6 + 0.3, 3.82, TOP6))
box('tag6b', (0.2, 0.012, 0.11), (0, 0, 0.11), M_PAPER, bv=0.004, parent=TAG6)
text3d('tag6t', '$2.44', 0.05, (0, -0.007, 0.115), (R(90), 0, 0), M_INK, TAG6, extrude=0.001)
box('tag6s', (0.012, 0.012, 0.06), (0, 0.0, 0.03), M_BRASS, parent=TAG6)
# the CURSE warning sign on the table, flicked flat when the mailman shrugs it off
CS6 = empty('cs6', HALL, loc=(X6 - 0.43, 3.86, TOP6)); CS6.scale = (1.45, 1.45, 1.45)
box('cs6p', (0.012, 0.012, 0.1), (0, 0, 0.05), M_BRASS, parent=CS6)
tri_ = mesh('cs6t', [(-0.09, 0, 0.1), (0.09, 0, 0.1), (0, 0, 0.255)], [(0, 1, 2)], M_YELLOW, CS6, smooth_=False); tri_.modifiers.new('sd', 'SOLIDIFY').thickness = 0.008
text3d('cs6x', 'CURSE!', 0.024, (0, -0.007, 0.142), (R(90), 0, 0), M_INK, CS6, extrude=0.0008)
# the mailman: a dress form in a postal uniform, cap and satchel
MM = dress_form('mm', HALL, (X6 + 0.95, 4.05, PLAT_Z), m=M_DUMMY)
lathe('mm_coat', [(0.165, 0.7), (0.17, 0.85), (0.15, 1.0), (0.16, 1.18), (0.19, 1.34), (0.205, 1.42), (0.14, 1.5), (0.06, 1.545)], 28, M_UNIF, MM).scale = (1.0, 0.72, 1.0)
lathe('mm_cap', [(0.0, 0.07), (0.1, 0.07), (0.105, 0.02), (0.1, 0.0), (0.0, 0.0)], 24, M_UNIF, MM, loc=(0, 0.01, 1.8))
box('mm_brim', (0.14, 0.09, 0.008), (0, -0.1, 1.805), M_BLACK, parent=MM)
box('mm_badge', (0.04, 0.005, 0.03), (0, -0.098, 1.84), M_GILT, parent=MM)
tube('mm_strap', [(0.17, -0.02, 1.43), (0.05, -0.13, 1.22), (-0.15, -0.14, 0.98)], 0.012, M_LEATHER, MM, seg=8)
box('mm_bag', (0.26, 0.09, 0.22), (-0.17, -0.12, 0.88), M_LEATHER, bv=0.015, parent=MM)
box('mm_flap', (0.27, 0.095, 0.1), (-0.17, -0.125, 0.95), M_LEATHER, bv=0.012, parent=MM)
track_spot('e6', X6 + 0.2, (X6 + 0.2, 4.0, 1.1), 950, ang=52)
# the mailman's bad year: a crutch lands against him; on a side table a photo falls and a little model house catches fire
SIDE6 = empty('side6', HALL, loc=(X6 + 1.58, 4.0, 0))
box('sd6', (0.52, 0.4, 0.72), (0, 0, PLAT_Z + 0.36), M_WOOD, bv=0.01, parent=SIDE6)
TOPS6 = PLAT_Z + 0.72
HOUSE6 = empty('house6', SIDE6, loc=(-0.1, 0.02, TOPS6))
box('hs6w', (0.2, 0.16, 0.13), (0, 0, 0.065), M_WHITE, bv=0.003, parent=HOUSE6)
rf_ = mesh('hs6r', [(-0.115, -0.09, 0.13), (0.115, -0.09, 0.13), (0.115, 0.09, 0.13), (-0.115, 0.09, 0.13), (-0.115, 0, 0.21), (0.115, 0, 0.21)],
           [(0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5)], M_RED, HOUSE6, smooth_=False); rf_.modifiers.new('sd', 'SOLIDIFY').thickness = 0.008
box('hs6d', (0.04, 0.004, 0.07), (0.04, -0.081, 0.035), M_WOODDK, parent=HOUSE6)
for dx in (-0.055, 0.04): box(f'hs6x{dx}', (0.035, 0.004, 0.03), (dx, -0.081, 0.095 if dx > 0 else 0.07), mat('win', (0.95, 0.75, 0.3), 0.3, emit=(1.0, 0.6, 0.2), estr=0.0), parent=HOUSE6)
M_FLAME = emis('flame', (1.0, 0.42, 0.06), 22.0); M_FLAME2 = emis('flame2', (1.0, 0.8, 0.25), 30.0)
FLAMES = []
gf_ = random.Random(23)
for k in range(9):
    fx, fy, fz = gf_.uniform(-0.09, 0.09), gf_.uniform(-0.06, 0.06), (0.17 if k < 6 else 0.13)
    o = prim('cone', f'flm{k}', M_FLAME if k % 3 else M_FLAME2, HOUSE6, loc=(fx, fy, fz), vertices=10, radius1=1.0, radius2=0.0, depth=1.0)
    FLAMES.append((o, gf_.uniform(0.018, 0.032), gf_.uniform(0.07, 0.15), gf_.uniform(0, 6), gf_.uniform(0, 0.4)))
FIRELT = light_at('firelt', 'POINT', (X6 + 1.48, 3.9, TOPS6 + 0.3), (X6 + 1.48, 3.9, 0), 0.0, (1.0, 0.5, 0.15), 0.08)
M_SMOKE = mat('smoke', (0.06, 0.06, 0.06), 0.95, alpha=0.3)
SMOKE = [prim('uv_sphere', f'smk{k}', M_SMOKE, HALL, loc=(0, 0, -50), segments=16, ring_count=10, radius=1.0) for k in range(12)]
PH6, _ = photo_frame('ph6', (X6 + 1.72, 3.98, TOPS6), 'lady')
CRUTCH = empty('crutch', HALL); CRUTCH_REST = Vector((X6 + 1.25, 3.93, PLAT_Z)); CRUTCH_ROT = (0, R(-10), 0)
for s_ in (-1, 1): tube(f'cr{s_}', [(0.0, 0, 0.26), (0.05 * s_, 0, 0.6), (0.05 * s_, 0, 1.14)], 0.011, M_WOOD, CRUTCH, seg=8)
tube('crb', [(0, 0, 0.02), (0, 0, 0.27)], 0.013, M_WOOD, CRUTCH, seg=8); tube('crt', [(0, 0, 0.0), (0, 0, 0.03)], 0.016, M_BLACK, CRUTCH, seg=8)
box('crp', (0.15, 0.04, 0.035), (0, 0, 1.16), M_BLACK, bv=0.012, parent=CRUTCH); box('crg', (0.1, 0.025, 0.025), (0, 0, 0.78), M_BLACK, bv=0.008, parent=CRUTCH)
CRUTCH.location = FAR_ = Vector((0, 0, -60))
track_spot('e6b', X6 + 1.4, (X6 + 1.4, 4.0, 1.0), 700, ang=40)

# ================================================================ exhibit 8: today, the Smithsonian - the package bursts open, the necklace rises; ultraviolet light, it glows red (x = 33.8)
X8, Y8 = 33.8, 3.75
CASE8 = glass_case('case8', X8, Y8)
BD8 = display_board('bd8', HALL, (X8, Y8 + 0.02, 1.31))
NK8, HOPE8 = necklace('nk8', BD8, M_HOPE, M_WHITE_D, M_PLAT, HOPE_ME, SMALL_ME)
BD8_REST = BD8.location.copy()
wall_sign('sg8', X8, 2.75, 'SMITHSONIAN', 2.0, 0.42, 0.18, m_bg=mat('navyp', (0.02, 0.03, 0.08), 0.5))
SCRAPS = []
gsc_ = random.Random(29)
for k in range(10):
    o = box(f'scrap{k}', (gsc_.uniform(0.07, 0.13), gsc_.uniform(0.05, 0.1), 0.004), (0, 0, -50), M_KRAFT, parent=HALL)
    SCRAPS.append((o, Vector((gsc_.uniform(-1.0, 1.0), gsc_.uniform(-0.9, 0.2), gsc_.uniform(1.0, 2.2))), Vector((gsc_.uniform(-9, 9), gsc_.uniform(-9, 9), gsc_.uniform(-5, 5)))))
UVL = empty('uvl', HALL, loc=(X8 + 0.5, Y8 - 0.2, 0))
lathe('uvst', [(0.0, 0.0), (0.12, 0.0), (0.12, 0.03), (0.02, 0.05), (0.016, 1.45), (0.0, 1.45)], 16, M_BLACK, UVL)
UVH = empty('uvh', UVL, loc=(0, 0, 1.5)); UVH.rotation_euler = (0, R(-35), 0)
box('uvhb', (0.08, 0.3, 0.06), (0, 0, 0), M_BLACK, bv=0.01, parent=UVH)
UVT = prim('cylinder', 'uvtube', M_UVTUBE, UVH, loc=(-0.035, 0, 0), rot=(R(90), 0, 0), vertices=10, radius=0.012, depth=0.26)
UVLIGHT = light_at('uvlight', 'AREA', (X8 + 0.44, Y8 - 0.22, 1.5), (X8, Y8, 1.25), 0.0, (0.45, 0.12, 1.0), 0.3)
track_spot('e8', X8, (X8, Y8, 1.2), 1000, ang=40)
