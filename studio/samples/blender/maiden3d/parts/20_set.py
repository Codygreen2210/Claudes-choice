
# ================================================================ set: a museum hall (x -4..24) with four exhibits, a window out to a Baghdad courtyard (x 24..48)
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
M_SAND = brick_mat('sandg', (0.42, 0.33, 0.22), (0.37, 0.29, 0.19), (0.30, 0.23, 0.15), 0.7, plane='xy', bump=0.3, row=0.6, w=0.6, mortar_w=0.015, seed=4.0)
M_SANDW = brick_mat('sandw', (0.66, 0.54, 0.38), (0.60, 0.48, 0.33), (0.50, 0.40, 0.28), 1.2, plane='yz', bump=0.4, row=0.3, w=0.6, mortar_w=0.012, seed=6.0)
M_SANDWX = brick_mat('sandwx', (0.66, 0.54, 0.38), (0.60, 0.48, 0.33), (0.50, 0.40, 0.28), 1.2, plane='xz', bump=0.4, row=0.3, w=0.6, mortar_w=0.012, seed=7.0)
M_PALM = noisy(mat('palm', (0.30, 0.22, 0.13), 0.9), 18.0, 0.35); M_FROND = noisy(mat('frond', (0.10, 0.22, 0.06), 0.6, sheen=0.2), 12.0, 0.3)
M_LEAF = [noisy(mat(f'leaf{i}', c, 0.75), 20.0, 0.3) for i, c in enumerate(((0.42, 0.28, 0.09), (0.30, 0.18, 0.06), (0.50, 0.38, 0.12), (0.22, 0.14, 0.05)))]
for m_ in M_LEAF: m_.node_tree.nodes['Principled BSDF'].inputs['Subsurface Weight'].default_value = 0.0

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
for xs, tg in ((-1.4, (0, 2.0, 1.2)), (1.4, (0, 2.0, 1.2)), (6.4, (7.0, 3.0, 0.9)), (8.6, (7.8, 5.2, 2.8)), (12.4, (13.0, 2.8, 1.0)), (14.0, (13.4, 2.8, 1.2)),
               (18.4, (19.0, 2.8, 1.0)), (20.0, (19.0, 2.6, 1.3))):
    track_spot(xs, tg)
for k, xa in enumerate((2.0, 9.0, 16.0, 22.0)):
    MUSEUM_LIGHTS.append((light_at(f'amb{k}', 'AREA', (xa, -2.5, 5.7), (xa, -2.5, 0), 350, (1.0, 0.93, 0.84), 3.0), 350))

# ---------------------------------------------------------------- exhibit 1: the dungeon diorama (x = 0)
DUN = empty('dungeon')
box('dstage', (4.8, 3.9, 0.3), (0, 1.85, 0.15), M_FLAG, bv=0.02, parent=DUN)
box('dback', (4.8, 0.4, 3.9), (0, 3.95, 0.3 + 1.95), M_STONE, parent=DUN)
for s_ in (-1, 1): box(f'dside{s_}', (0.4, 3.9, 3.9), (s_ * 2.4, 1.85, 0.3 + 1.95), M_STONEY, parent=DUN)
box('dlintel', (5.2, 0.5, 0.5), (0, 0.0, 4.15), M_STONE, bv=0.02, parent=DUN)
for s_ in (-1, 1):                                          # stone pillars at the front corners (the diorama's frame)
    box(f'dpil{s_}', (0.5, 0.5, 4.4), (s_ * 2.4, 0.0, 2.2), M_STONEY, bv=0.02, parent=DUN)
g0_ = random.Random(5)
# a barred window high on the back wall, moonlight
box('dwin', (0.7, 0.1, 0.5), (0.0, 3.76, 3.1), M_BLACK, parent=DUN)
for k in range(4): tube(f'dbar{k}', [(-0.25 + k * 0.166, 3.72, 2.85), (-0.25 + k * 0.166, 3.72, 3.35)], 0.014, M_IRDK, DUN, seg=8)
MOON = light_at('moon', 'AREA', (0.0, 3.6, 3.1), (0.0, 1.0, 0.6), 90, (0.55, 0.68, 1.0), 0.6)
# chains and shackles on the back wall
def chain(name, top, n, parent, m, link=0.055):
    for k in range(n):
        p = Vector(top) + Vector((0, 0, -k * link * 1.55))
        bmt = bpy.data.meshes.new(f'{name}{k}'); bm = bmesh.new(); seg_ = 12; ring = 6; R0, r0 = link * 0.55, link * 0.16
        for i in range(seg_):
            u = 2 * math.pi * i / seg_
            for j in range(ring):
                v = 2 * math.pi * j / ring; c_ = Vector((math.cos(u) * (R0 + r0 * math.cos(v)) * 0.6, r0 * math.sin(v), math.sin(u) * (R0 + r0 * math.cos(v))))
                bm.verts.new(c_)
        bm.verts.ensure_lookup_table()
        for i in range(seg_):
            for j in range(ring): bm.faces.new([bm.verts[i * ring + j], bm.verts[((i + 1) % seg_) * ring + j], bm.verts[((i + 1) % seg_) * ring + (j + 1) % ring], bm.verts[i * ring + (j + 1) % ring]])
        bm.to_mesh(bmt); bm.free()
        for pp in bmt.polygons: pp.use_smooth = True
        o = obj(f'{name}{k}', bmt, m, p, parent); o.rotation_euler = (0, 0, (math.pi / 2) * (k % 2))
for s_ in (-1, 1):
    prim('cylinder', f'ring{s_}', M_IRDK, DUN, loc=(s_ * 1.3, 3.72, 2.9), rot=(R(90), 0, 0), vertices=16, radius=0.045, depth=0.05)
    chain(f'chain{s_}', (s_ * 1.3, 3.70, 2.83), 14, DUN, M_IRDK)
    tube(f'shack{s_}', [(s_ * 1.3 + 0.06 * math.cos(2 * math.pi * k / 14), 3.70, 1.62 + 0.06 * math.sin(2 * math.pi * k / 14)) for k in range(15)], 0.013, M_IRDK, DUN, seg=8, caps=False)
# torches in iron brackets on the side walls
TORCH = []
for s_ in (-1, 1):
    bx = s_ * 2.16; by = 1.05; bz = 2.25
    tube(f'tbrk{s_}', [(s_ * 2.2, by, bz - 0.25), (bx - s_ * 0.05, by, bz - 0.2), (bx - s_ * 0.12, by, bz - 0.05)], 0.018, M_IRDK, DUN, seg=8)
    st = tube(f'tstick{s_}', [(bx - s_ * 0.16, by, bz - 0.32), (bx - s_ * 0.10, by, bz + 0.12)], lambda u: 0.022 + 0.012 * u, M_WOOD, DUN, seg=10)
    lathe(f'tcup{s_}', [(0.03, 0.0), (0.06, 0.05), (0.075, 0.13), (0.07, 0.135)], 16, M_IRDK, DUN, loc=(bx - s_ * 0.10, by, bz + 0.02))
    fl = lathe(f'tflame{s_}', [(0.0, 0.0), (0.055, 0.04), (0.06, 0.10), (0.04, 0.2), (0.015, 0.3), (0.0, 0.34)], 16, M_FLAME, DUN, loc=(bx - s_ * 0.10, by, bz + 0.12))
    lt = light_at(f'tlight{s_}', 'POINT', (bx - s_ * 0.22, by, bz + 0.3), (0, by, 0), 70, (1.0, 0.55, 0.22), 0.08)
    TORCH.append((fl, lt))
BRAZ = lathe('brazier', [(0.0, 0.55), (0.24, 0.55), (0.30, 0.68), (0.32, 0.70), (0.0, 0.70)], 24, M_IRDK, DUN, loc=(-1.25, 0.75, 0.3))
for k in range(3): tube(f'brleg{k}', [(-1.25 + 0.22 * math.cos(2.1 * k), 0.75 + 0.22 * math.sin(2.1 * k), 0.85), (-1.25 + 0.3 * math.cos(2.1 * k), 0.75 + 0.3 * math.sin(2.1 * k), 0.3)], 0.018, M_IRDK, DUN, seg=8)
M_COAL = mat('coal', (0.03, 0.02, 0.02), 0.9, emit=(1.0, 0.28, 0.05), estr=4.0)
for k in range(22): prim('ico_sphere', f'coal{k}', M_COAL, DUN, loc=(-1.25 + g0_.uniform(-0.2, 0.2), 0.75 + g0_.uniform(-0.2, 0.2), 1.0 + g0_.uniform(0, 0.05)), subdivisions=1, radius=g0_.uniform(0.035, 0.06))
BRAZF = lathe('brflame', [(0.0, 0.0), (0.16, 0.05), (0.14, 0.18), (0.06, 0.36), (0.0, 0.45)], 16, M_FLAME, DUN, loc=(-1.25, 0.75, 1.02))
BRAZL = light_at('brlight', 'POINT', (-1.15, 0.7, 1.55), (0, 2, 1), 120, (1.0, 0.5, 0.2), 0.15)
FILL = light_at('dfill', 'AREA', (0.0, -1.5, 2.8), (0.0, 2.0, 1.2), 45, (0.6, 0.65, 0.8), 2.0)
# straw on the stage floor, a bucket, a stool
g_ = random.Random(3)
for k in range(140):
    a_ = g_.uniform(0, 2 * math.pi); r_ = g_.uniform(0.5, 1.9); p = Vector((math.cos(a_) * r_ * 1.0, 2.0 + math.sin(a_) * r_ * 0.8, 0.305))
    if abs(p.x) > 2.1 or p.y > 3.65 or p.y < 0.2: continue
    d_ = Vector((math.cos(g_.uniform(0, 6.3)), math.sin(g_.uniform(0, 6.3)), 0.04)).normalized() * g_.uniform(0.12, 0.3)
    tube(f'straw{k}', [p, p + d_ * 0.5 + Vector((0, 0, 0.012)), p + d_], 0.0035, M_STRAW, DUN, seg=4, caps=False)
lathe('bucket', [(0.0, 0.0), (0.15, 0.0), (0.19, 0.34), (0.20, 0.35), (0.0, 0.35)], 24, M_WOODRAW, DUN, loc=(1.55, 3.1, 0.3))
for zb_ in (0.06, 0.28): tube(f'bkband{zb_}', [(1.55 + (0.158 + zb_ * 0.11) * math.cos(2 * math.pi * k / 24), 3.1 + (0.158 + zb_ * 0.11) * math.sin(2 * math.pi * k / 24), 0.3 + zb_) for k in range(25)], 0.008, M_IRDK, DUN, seg=6)
box('stool', (0.42, 0.42, 0.06), (-1.5, 2.9, 0.75), M_WOODRAW, bv=0.01, parent=DUN)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): box(f'stleg{sx_}{sy_}', (0.05, 0.05, 0.45), (-1.5 + sx_ * 0.16, 2.9 + sy_ * 0.16, 0.5), M_WOODRAW, parent=DUN)
# the museum front: brass posts, velvet rope, a placard
for k, xp in enumerate((-2.0, 0.0, 2.0)):
    lathe(f'post{k}', [(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.04, 0.06), (0.025, 0.08), (0.025, 0.88), (0.045, 0.92), (0.05, 0.96), (0.0, 1.0)], 24, M_BRASS, HALL, loc=(xp, -0.55, 0))
for k in range(2):
    x0, x1 = -2.0 + 2 * k, 2.0 * k
    tube(f'rope{k}', [(lerp(x0, x1, u), -0.55, 0.9 - 0.22 * math.sin(math.pi * u)) for u in [i / 16 for i in range(17)]], 0.022, M_VELVET, HALL, seg=10)
PLQ1 = empty('plaq1', HALL, loc=(1.15, -1.0, 0)); PLQ1.rotation_euler = (0, 0, R(-12))
for xs_ in (-0.12, 0.12): box(f'plqleg{xs_}', (0.03, 0.03, 0.9), (xs_, 0, 0.45), M_BRASS, parent=PLQ1)
pb = box('plqboard', (0.6, 0.03, 0.4), (0, -0.02, 0.98), M_PLAQ, bv=0.005, parent=PLQ1); pb.rotation_euler = (R(-35), 0, 0)
t_ = text3d('plqtxt', 'IRON MAIDEN\n"MEDIEVAL"?', 0.07, (0, -0.045, 1.0), (R(55), 0, 0), M_GILT, PLQ1, extrude=0.002)

# ---------------------------------------------------------------- exhibit 2: the writer's desk, 1793 (x = 7); the timeline above it
DESK = empty('desk')
box('rug', (3.0, 2.2, 0.01), (7.0, 3.0, 0.005), noisy(mat('rug', (0.30, 0.07, 0.05), 0.95), 6.0, 0.3), parent=DESK)
box('desktop', (1.5, 0.8, 0.05), (7.0, 3.1, 0.78), M_WOOD, bv=0.01, parent=DESK)
box('deskapron', (1.4, 0.7, 0.12), (7.0, 3.1, 0.69), M_WOOD, bv=0.005, parent=DESK)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): tube(f'dleg{sx_}{sy_}', [(7.0 + sx_ * 0.68, 3.1 + sy_ * 0.33, 0.63), (7.0 + sx_ * 0.66, 3.1 + sy_ * 0.31, 0.3), (7.0 + sx_ * 0.67, 3.1 + sy_ * 0.32, 0.0)], lambda u: 0.03 - 0.012 * u, M_WOOD, DESK, seg=10)
box('chairseat', (0.5, 0.5, 0.05), (7.1, 3.85, 0.47), M_WOOD, bv=0.01, parent=DESK); box('chairback', (0.5, 0.05, 0.6), (7.1, 4.1, 0.8), M_WOOD, bv=0.01, parent=DESK)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): box(f'chleg{sx_}{sy_}', (0.04, 0.04, 0.47), (7.1 + sx_ * 0.21, 3.85 + sy_ * 0.21, 0.23), M_WOOD, parent=DESK)
# the open book (two curved pages) and the line of writing that grows
BOOK = empty('book', DESK, loc=(6.95, 3.02, 0.805)); BOOK.rotation_euler = (0, 0, R(6))
for s_ in (-1, 1):
    vs = []; fs = []; nu, nv = 10, 2
    for i in range(nu + 1):
        u = i / nu; x_ = s_ * (0.01 + 0.2 * u); z_ = 0.03 * math.sin(math.pi * (0.15 + 0.7 * u)) - 0.012 * u
        for j in range(nv + 1): vs.append((x_, -0.14 + 0.28 * j / nv, z_))
    for i in range(nu):
        for j in range(nv): a_ = i * (nv + 1) + j; fs.append((a_, a_ + nv + 1, a_ + nv + 2, a_ + 1) if s_ > 0 else (a_, a_ + 1, a_ + nv + 2, a_ + nv + 1))
    pg = mesh(f'page{s_}', vs, fs, M_PAPER, BOOK); sd = pg.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.012
box('bookcover', (0.46, 0.31, 0.01), (0, 0, -0.012), noisy(mat('leather', (0.25, 0.08, 0.04), 0.6), 30, 0.3), parent=BOOK)
INKLINES = []
for k in range(7):                                         # lines of writing on the right page; they grow as the quill moves
    o = box(f'ink{k}', (0.16, 0.004, 0.0015), (0.03 + 0.08, 0.10 - k * 0.032, 0.036), M_INK, parent=BOOK); INKLINES.append(o)
QUILL = empty('quill', DESK)
tube('qshaft', [(0, 0, 0), (0.01, 0.0, 0.06), (0.03, 0.005, 0.30)], lambda u: 0.0035 * (1 - 0.5 * u), M_WHITE, QUILL, seg=6)
vs = []; fs = []
for i in range(13):
    u = i / 12; z_ = 0.08 + 0.24 * u; w_ = 0.028 * math.sin(math.pi * min(1, u * 1.15)) + 0.002
    vs += [(0.008 + 0.02 * u - w_, 0.002, z_), (0.008 + 0.02 * u + w_ * 0.6, 0.002, z_)]
for i in range(12): fs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
vane = mesh('qvane', vs, fs, noisy(mat('feather', (0.86, 0.84, 0.78), 0.7, sheen=0.6), 40, 0.15), QUILL); sd = vane.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.002
lathe('inkwell', [(0.0, 0.0), (0.045, 0.0), (0.05, 0.04), (0.03, 0.06), (0.018, 0.075), (0.02, 0.085), (0.0, 0.085)], 24, M_GLASS, DESK, loc=(7.35, 2.95, 0.805))
lathe('inkin', [(0.0, 0.0), (0.04, 0.0), (0.04, 0.035), (0.0, 0.035)], 16, M_INK, DESK, loc=(7.35, 2.95, 0.808))
lathe('candlehold', [(0.0, 0.0), (0.08, 0.0), (0.085, 0.01), (0.02, 0.02), (0.018, 0.05), (0.03, 0.055), (0.0, 0.06)], 24, M_BRASS, DESK, loc=(7.55, 3.3, 0.805))
lathe('candle', [(0.0, 0.0), (0.022, 0.0), (0.022, 0.20), (0.016, 0.215), (0.0, 0.215)], 16, M_WAX, DESK, loc=(7.55, 3.3, 0.86))
CFLAME = lathe('cflame', [(0.0, 0.0), (0.009, 0.01), (0.011, 0.025), (0.006, 0.045), (0.0, 0.06)], 12, M_FLAME, DESK, loc=(7.55, 3.3, 1.08))
CLIGHT = light_at('clight', 'POINT', (7.55, 3.3, 1.13), (7.0, 3.0, 0.8), 25, (1.0, 0.62, 0.3), 0.03)
# the forger's coins and a two-part coin mould
COINS = []
for k in range(9):
    c_ = prim('cylinder', f'coin{k}', M_SILV if k % 3 else M_GOLD, DESK, loc=(6.45 + (0.07 if k > 5 else 0), 3.0 + (0.06 if k > 5 else 0), 0.81 + 0.0065 * (k if k <= 5 else k - 6)), vertices=28, radius=0.022, depth=0.005)
    COINS.append(c_)
for k in range(4):
    a_ = 0.9 * k; prim('cylinder', f'coinf{k}', M_SILV, DESK, loc=(6.32 + 0.06 * math.cos(a_), 3.2 + 0.05 * math.sin(a_), 0.808), vertices=28, radius=0.022, depth=0.005)
box('mouldA', (0.09, 0.07, 0.04), (6.40, 2.82, 0.825), M_IRDK, bv=0.006, parent=DESK); box('mouldB', (0.09, 0.07, 0.04), (6.52, 2.80, 0.825), M_IRDK, bv=0.006, parent=DESK).rotation_euler = (0, 0, R(18))
prim('cylinder', 'mouldhole', M_BLACK, DESK, loc=(6.40, 2.82, 0.846), vertices=20, radius=0.022, depth=0.002)
PLQ2 = empty('plaq2', HALL, loc=(8.25, 1.75, 0)); PLQ2.rotation_euler = (0, 0, R(-10))
for xs_ in (-0.1, 0.1): box(f'plq2leg{xs_}', (0.03, 0.03, 0.85), (xs_, 0, 0.42), M_BRASS, parent=PLQ2)
pb = box('plq2board', (0.5, 0.03, 0.34), (0, -0.02, 0.92), M_PLAQ, bv=0.005, parent=PLQ2); pb.rotation_euler = (R(-35), 0, 0)
text3d('plq2txt', 'THE STORY\n1793', 0.075, (0, -0.045, 0.94), (R(55), 0, 0), M_GILT, PLQ2, extrude=0.002)
# the timeline rail on the wall: 1515 ...... 1793
TL = empty('timeline', HALL)
box('tlbar', (2.8, 0.04, 0.05), (7.5, 5.38, 2.8), M_BLACK, parent=TL)
TLFILL = box('tlfill', (1.0, 0.03, 0.08), (6.1 + 0.5, 5.36, 2.8), emis('tlglow', (1.0, 0.25, 0.12), 6.0), parent=TL)
for xp, yr in ((6.1, '1515'), (8.9, '1793')):
    box(f'tltick{yr}', (0.04, 0.04, 0.35), (xp, 5.38, 2.8), M_GILT, parent=TL)
    text3d(f'tltxt{yr}', yr, 0.42, (xp, 5.35, 3.3), (R(90), 0, 0), M_GILT, TL, extrude=0.01)
text3d('tltxt_q', 'NO RECORD', 0.3, (7.5, 5.35, 2.3), (R(90), 0, 0), emis('redtxt', (0.9, 0.12, 0.08), 2.5), TL, extrude=0.006)

# ---------------------------------------------------------------- exhibit 3: the workshop, where a maiden is pieced together (x = 13)
SHOP = empty('shop')
box('shopplat', (4.2, 3.0, 0.15), (13.4, 3.0, 0.075), M_WOODRAW, bv=0.01, parent=SHOP)
box('bench', (1.8, 0.7, 0.08), (15.0, 3.6, 0.85), M_WOODRAW, bv=0.01, parent=SHOP)
for sx_ in (-1, 1):
    for sy_ in (-1, 1): box(f'bleg{sx_}{sy_}', (0.08, 0.08, 0.7), (15.0 + sx_ * 0.8, 3.6 + sy_ * 0.28, 0.5), M_WOODRAW, parent=SHOP)
tube('hammerh', [(14.5, 3.5, 0.91), (14.62, 3.5, 0.91)], 0.025, M_IRDK, SHOP, seg=10); tube('hammerg', [(14.56, 3.5, 0.91), (14.6, 3.2, 0.905)], 0.012, M_WOOD, SHOP, seg=8)
tube('tongs1', [(15.3, 3.4, 0.9), (15.6, 3.6, 0.9), (15.75, 3.75, 0.9)], 0.008, M_IRDK, SHOP, seg=6); tube('tongs2', [(15.3, 3.45, 0.9), (15.6, 3.58, 0.9), (15.78, 3.7, 0.9)], 0.008, M_IRDK, SHOP, seg=6)
for k in range(3):                                          # old museum pieces on the bench: a helmet, a door panel, a box of nails
    pass
lathe('helmet', [(0.0, 0.2), (0.08, 0.19), (0.13, 0.14), (0.15, 0.05), (0.16, 0.0)], 24, M_IRON2, SHOP, loc=(15.5, 3.75, 0.89))
box('nailbox', (0.3, 0.2, 0.1), (14.8, 3.8, 0.94), M_WOODRAW, bv=0.005, parent=SHOP)
for k in range(12): tube(f'nail{k}', [(14.68 + 0.02 * k, 3.75 + 0.01 * (k % 3), 0.97), (14.68 + 0.02 * k + 0.01, 3.80, 1.04)], 0.004, M_IRDK, SHOP, seg=4)
box('banner3', (2.4, 0.02, 0.5), (13.2, 5.38, 3.6), M_RED, parent=SHOP)
text3d('ban3txt', 'NUREMBERG', 0.3, (13.2, 5.36, 3.6), (R(90), 0, 0), M_GILT, SHOP, extrude=0.008)

# ---------------------------------------------------------------- exhibit 4: the shipping crate, Chicago 1893 (x = 19)
CRATE = empty('crate')
CX, CY = 19.0, 2.8
for s_ in (-1, 1):                                          # side walls of slats
    for k in range(6): box(f'crs{s_}{k}', (0.05, 1.3, 0.36), (CX + s_ * 0.68, CY, 0.2 + k * 0.4), M_WOODRAW, bv=0.006, parent=CRATE)
for k in range(6): box(f'crb{k}', (1.4, 0.05, 0.36), (CX, CY + 0.65, 0.2 + k * 0.4), M_WOODRAW, bv=0.006, parent=CRATE)
box('crtop', (1.46, 1.36, 0.06), (CX + 1.05, CY - 0.1, 0.72), M_WOODRAW, bv=0.006, rot=(0, R(-62), 0), parent=CRATE); box('crbase', (1.46, 1.36, 0.1), (CX, CY, 0.05), M_WOODRAW, bv=0.006, parent=CRATE)
for s_ in (-1, 1):
    for xx in (-0.66, 0.66): box(f'crpost{s_}{xx}', (0.08, 0.08, 2.4), (CX + xx, CY + s_ * 0.64, 1.2), M_WOODRAW, bv=0.006, parent=CRATE)
lid = empty('crlid', CRATE, loc=(CX - 1.55, CY - 0.2, 0)); lid.rotation_euler = (R(-10), 0, R(-75))
for k in range(5): box(f'crl{k}', (1.4, 0.05, 0.4), (0, 0, 0.22 + k * 0.44), M_WOODRAW, bv=0.006, parent=lid)
box('crlx', (0.08, 0.06, 2.2), (0, -0.04, 1.1), M_WOODRAW, parent=lid).rotation_euler = (0, R(31), 0)
text3d('crtxt', 'CHICAGO', 0.2, (CX + 0.71, CY, 1.3), (R(90), 0, R(90)), M_BLACK, CRATE, extrude=0.002)
text3d('crtxt2', 'FRAGILE', 0.11, (CX + 0.71, CY, 0.95), (R(90), 0, R(90)), M_RED, CRATE, extrude=0.002)
for k in range(60):
    p = Vector((CX + g_.uniform(-0.6, 0.6), CY + g_.uniform(-0.55, 0.55), 0.11)); d_ = Vector((g_.uniform(-1, 1), g_.uniform(-1, 1), 0.05)).normalized() * g_.uniform(0.1, 0.25)
    tube(f'cstraw{k}', [p, p + d_ * 0.5 + Vector((0, 0, 0.015)), p + d_], 0.004, M_STRAW, CRATE, seg=4, caps=False)
# poster and bunting
box('poster', (2.6, 0.02, 1.4), (19.0, 5.38, 3.4), M_POSTER, parent=CRATE)
box('posterband', (2.6, 0.025, 0.28), (19.0, 5.37, 3.95), M_RED, parent=CRATE)
text3d('posttxt1', "WORLD'S FAIR", 0.24, (19.0, 5.355, 3.95), (R(90), 0, 0), M_WHITE, CRATE, extrude=0.004)
text3d('posttxt2', 'CHICAGO 1893', 0.3, (19.0, 5.355, 3.45), (R(90), 0, 0), M_BLUE, CRATE, extrude=0.004)
text3d('posttxt3', 'SEE THE IRON MAIDEN', 0.13, (19.0, 5.355, 2.95), (R(90), 0, 0), M_RED, CRATE, extrude=0.004)
FLAGS = []
for row_, (z0, y0) in enumerate(((4.6, 1.0), (4.4, 3.4))):
    pts = [(16.6 + 4.8 * u, y0, z0 - 0.35 * math.sin(math.pi * u)) for u in [i / 20 for i in range(21)]]; tube(f'bstr{row_}', pts, 0.006, M_WHITE, CRATE, seg=6)
    for k in range(12):
        u = (k + 0.5) / 12; p = Vector((16.6 + 4.8 * u, y0, z0 - 0.35 * math.sin(math.pi * u)))
        f_ = mesh(f'flag{row_}{k}', [(-0.12, 0, 0), (0.12, 0, 0), (0, 0, -0.26)], [(0, 1, 2)], (M_RED, M_WHITE, M_BLUE)[k % 3], CRATE, smooth_=False, loc=p)
        sd = f_.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.004; FLAGS.append((f_, k + row_ * 7))

# ---------------------------------------------------------------- outside: a courtyard in Baghdad (x 24..48), sun and sky
YARD = empty('yard')
box('yground', (30.0, 34.0, 0.2), (39.0, 0.0, -0.11), M_SAND, parent=YARD)
box('ybldg', (1.0, 30.0, 9.0), (46.0, 0.0, 4.5), M_SANDW, parent=YARD)
for k in range(-5, 6):                                      # arches (dark recesses with pointed heads) along the building
    y_ = k * 2.4
    box(f'yarch{k}', (0.3, 1.4, 2.6), (45.45, y_, 1.3), mat(f'ydark{k}', (0.06, 0.05, 0.04), 0.9), parent=YARD)
    ar = mesh(f'yarchh{k}', [(45.42, y_ - 0.7, 2.6), (45.42, y_ + 0.7, 2.6), (45.42, y_, 3.3)], [(0, 1, 2)], bpy.data.materials[f'ydark{k}'], YARD, smooth_=False)
    box(f'ywin{k}', (0.3, 0.9, 1.0), (45.45, y_, 5.5), bpy.data.materials[f'ydark{k}'], parent=YARD)
box('ybldg2', (16.0, 1.0, 7.0), (36.0, 10.5, 3.5), M_SANDWX, parent=YARD)
box('ycornice', (1.4, 30.0, 0.4), (45.8, 0.0, 9.1), M_SANDW, bv=0.02, parent=YARD)
box('ywall', (16.0, 0.6, 2.4), (33.0, -9.5, 1.2), M_SANDWX, parent=YARD)
def palm(name, base, h, lean, seed):
    gg = random.Random(seed); pts = [Vector(base) + Vector((lean[0] * u * u * h, lean[1] * u * u * h, u * h)) for u in [i / 12 for i in range(13)]]
    tube(name + 'tr', pts, lambda u: 0.22 - 0.09 * u, M_PALM, YARD, seg=14)
    for i in range(1, 12): tube(f'{name}ring{i}', [pts[i] + Vector((0.2 * math.cos(2 * math.pi * k / 14), 0.2 * math.sin(2 * math.pi * k / 14), 0)) * (1 - 0.4 * i / 12) for k in range(15)], 0.018, M_PALM, YARD, seg=5, caps=False)
    top = pts[-1]
    for k in range(13):
        a_ = 2 * math.pi * k / 13 + gg.uniform(-0.2, 0.2); dr = Vector((math.cos(a_), math.sin(a_), 0)); L_ = gg.uniform(2.2, 3.0)
        spine = [top + dr * (L_ * u) + Vector((0, 0, 0.6 * math.sin(math.pi * u * 0.8) - 1.1 * u * u)) for u in [i / 10 for i in range(11)]]
        vs = []; fs = []
        for i, sp in enumerate(spine):
            u = i / 10; w_ = 0.42 * math.sin(math.pi * min(1, 0.15 + u)) + 0.02; side = dr.cross(Vector((0, 0, 1)))
            vs += [sp + side * w_ + Vector((0, 0, -0.12 * w_)), sp, sp - side * w_ + Vector((0, 0, -0.12 * w_))]
        for i in range(10): fs += [(3 * i, 3 * i + 1, 3 * i + 4, 3 * i + 3), (3 * i + 1, 3 * i + 2, 3 * i + 5, 3 * i + 4)]
        fr = mesh(f'{name}fr{k}', vs, fs, M_FROND, YARD); sd = fr.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.01
palm('palm1', (38.0, 6.0, 0.0), 7.5, (0.08, -0.05), 1); palm('palm2', (41.5, -5.5, 0.0), 8.5, (-0.06, 0.07), 2); palm('palm3', (30.0, 7.5, 0.0), 6.5, (0.1, 0.0), 3)
SUN = light_at('sun', 'SUN', (40, -20, 30), (32, 0, 0), 3.2, (1.0, 0.92, 0.78), 0.02); SUN.data.angle = R(1.2)
SKY = W_.node_tree.nodes.new('ShaderNodeTexSky')
try:
    SKY.sky_type = 'MULTIPLE_SCATTERING'; SKY.sun_elevation = R(38); SKY.sun_rotation = R(120); SKY.altitude = 50; SKY.air_density = 1.4
    for k_, v_ in (('dust_density', 3.0), ('aerosol_density', 3.0)):
        try: setattr(SKY, k_, v_)
        except Exception: pass
except Exception as e_: print('sky', e_)
W_.node_tree.links.new(SKY.outputs['Color'], WBG.inputs['Color']); WBG.inputs['Strength'].default_value = 0.0
# the leaf pile it was hidden under, and loose leaves
LEAVES = []
def leaf(name, p, rot, sc, m, parent):
    vs = [(0, -0.5, 0), (0.18, -0.25, 0.02), (0.22, 0.05, 0.03), (0.12, 0.35, 0.02), (0, 0.5, 0), (-0.12, 0.35, 0.02), (-0.22, 0.05, 0.03), (-0.18, -0.25, 0.02), (0, 0, 0.04)]
    fs = [(8, i, (i + 1) % 8) for i in range(8)]
    o = mesh(name, [Vector(v) * sc for v in vs], fs, m, parent, loc=p); o.rotation_euler = rot; return o
LP = Vector((32.0, 0.0, 0.0))
for k in range(1500):
    a_ = g_.uniform(0, 2 * math.pi); r_ = abs(g_.gauss(0, 0.62)); p = LP + Vector((0.55 + math.cos(a_) * r_ * 1.6, math.sin(a_) * r_ * 1.0, 0))
    if p.x < LP.x - 0.55 and abs(p.y) < 0.45: continue                       # keep the face clear
    hgt = max(0.0, 0.9 * math.exp(-(r_ / 0.65) ** 2)) * g_.uniform(0.55, 1.0)
    o = leaf(f'pile{k}', p + Vector((0, 0, 0.01 + hgt)), (g_.uniform(-0.7, 0.7), g_.uniform(-0.7, 0.7), g_.uniform(0, 6.3)), g_.uniform(0.12, 0.2), M_LEAF[k % 4], YARD)
    LEAVES.append((o, o.location.copy(), o.rotation_euler.copy(), k))
