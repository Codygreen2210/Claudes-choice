
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
WIND = wind_set('wind_p', 0.0105, 16, 0.07, 1.6, 0.00018, 55.0)        # around the penny
WINDB = wind_set('wind_b', BALL_R, 18, 0.7, 0.25, 0.0016, 6.0)            # around the ball: barely bent
WINDU = wind_set('wind_up', 1.2, 22, 14.0, 0.4, 0.012, 0.35)              # the updraft along the tower
def wind_on(root, on, tt=0.0, alpha=0.8):
    for n in root['parts']:
        o = bpy.data.objects[n]; o.hide_render = not on; o['tt'] = tt; o['alpha'] = alpha
    root.hide_render = not on

# ================================================================ the impact: a crater, cracks, flying chunks, dust
IMP = V3(-1.3, -27.9, SW_Z)
CRATER_M = noisy(mat('crater', (0.16, 0.15, 0.14), 0.95), 120.0, 0.4, 0.05)
CRATER = lathe('crater', [(0.0, -0.05), (0.08, -0.045), (0.16, -0.025), (0.24, -0.006), (0.3, 0.004), (0.34, 0.0)], 48, CRATER_M, loc=IMP + V3(0, 0, 0.0015))
_rng = random.Random(11); CRACKS = []
for k in range(14):
    a0 = 2 * math.pi * k / 14 + _rng.uniform(-0.2, 0.2); pts = []; p = Vector((0.25 * math.cos(a0), 0.25 * math.sin(a0), 0.0)); ang = a0
    L_ = _rng.uniform(0.6, 1.6)
    for s in range(24):
        pts.append(p.copy()); ang += _rng.uniform(-0.35, 0.35); p = p + Vector((math.cos(ang), math.sin(ang), 0)) * (L_ / 24)
    c = tube(f'crack_{k}', [(x_, y_, 0.0) for x_, y_, _ in pts], lambda u: 0.006 * (1 - u) + 0.0015, mat(f'crack_m{k}', (0.02, 0.02, 0.02), 0.95), seg=6)
    c.location = IMP + V3(0, 0, 0.0005); c.scale = (1, 1, 0.25); CRACKS.append(c)
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
IMPACT = [CRATER] + CRACKS + CHUNKS + DUST

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
