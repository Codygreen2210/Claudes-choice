
# ================================================================ the yard (at the origin): you stand on a back porch looking north (+y)
# over a lawn with a pond, trees, two neighbours' houses and a lake. Day (low golden sun), night (stars, porch lamp, lit windows),
# frost (one shared amount freezes every surface), the pond and the lake skin over with ice.
DECK_Z = 0.6; RAIL_Y = 1.2; RAIL_Z = DECK_Z + 1.0
EYE = Vector((0.0, -0.3, DECK_Z + 1.53))
SUN_DIR = Vector((math.sin(R(16)) * math.cos(R(15)), math.cos(R(16)) * math.cos(R(15)), math.sin(R(15)))).normalized()
MOON_DIR = Vector((math.sin(R(-24)) * math.cos(R(24)), math.cos(R(-24)) * math.cos(R(24)), math.sin(R(24)))).normalized()

# ---- frost: one node group shared by every outdoor material; FROST_AMT drives all of it
FG = bpy.data.node_groups.new('frost', 'ShaderNodeTree')
FG.interface.new_socket('Color', in_out='INPUT', socket_type='NodeSocketColor'); FG.interface.new_socket('Rough', in_out='INPUT', socket_type='NodeSocketFloat')
FG.interface.new_socket('Color', in_out='OUTPUT', socket_type='NodeSocketColor'); FG.interface.new_socket('Rough', in_out='OUTPUT', socket_type='NodeSocketFloat')
FG.interface.new_socket('Mask', in_out='OUTPUT', socket_type='NodeSocketFloat')
_gi = FG.nodes.new('NodeGroupInput'); _go = FG.nodes.new('NodeGroupOutput'); FROST_AMT = FG.nodes.new('ShaderNodeValue'); FROST_AMT.outputs[0].default_value = 0.0
_fz = tnoise(FG, coord(FG, 'Object'), 3.0, 6, 0.5)
_fz2 = FG.nodes.new('ShaderNodeTexVoronoi'); _fz2.inputs['Scale'].default_value = 40.0; FG.links.new(coord(FG, 'Object'), _fz2.inputs['Vector'])
_fm = math_(FG, 'MINIMUM', math_(FG, 'MAXIMUM', math_(FG, 'MULTIPLY', math_(FG, 'SUBTRACT', math_(FG, 'MULTIPLY', FROST_AMT.outputs[0], 1.7), math_(FG, 'ADD', _fz, 0.3)), 7.0), 0.0), 1.0)
_fc = mixc(FG, math_(FG, 'MULTIPLY', _fz2.outputs['Distance'], 1.4), (0.92, 0.95, 1.0), (0.7, 0.78, 0.88))
FG.links.new(mixc(FG, _fm, _gi.outputs['Color'], _fc), _go.inputs['Color'])
FG.links.new(math_(FG, 'ADD', math_(FG, 'MULTIPLY', _gi.outputs['Rough'], math_(FG, 'SUBTRACT', 1.0, _fm)), math_(FG, 'MULTIPLY', _fm, 0.42)), _go.inputs['Rough'])
FG.links.new(_fm, _go.inputs['Mask'])
def frostify(m):
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); g = nt.nodes.new('ShaderNodeGroup'); g.node_tree = FG
    for k in ('Base Color', 'Roughness'):
        lk = next((l for l in nt.links if l.to_socket == b.inputs[k]), None); gin = g.inputs['Color' if k == 'Base Color' else 'Rough']
        if lk: nt.links.new(lk.from_socket, gin); nt.links.remove(lk)
        else: gin.default_value = b.inputs[k].default_value
        nt.links.new(g.outputs['Color' if k == 'Base Color' else 'Rough'], b.inputs[k])
    return m

# ---- materials
WOOD = frostify(noisy(mat('deck_wood', (0.36, 0.22, 0.13), 0.7), 2.0, 0.3, 0.1))
_wn = WOOD.node_tree; _ww = _wn.nodes.new('ShaderNodeTexWave'); _ww.wave_type = 'BANDS'; _ww.bands_direction = 'Y'; _ww.inputs['Scale'].default_value = 3.0
_ww.inputs['Distortion'].default_value = 8.0; _ww.inputs['Detail'].default_value = 3; _wn.links.new(coord(_wn), _ww.inputs['Vector'])
_wbm = _wn.nodes.new('ShaderNodeBump'); _wbm.inputs['Strength'].default_value = 0.25; _wn.links.new(_ww.outputs['Fac'], _wbm.inputs['Height'])
_wn.links.new(_wbm.outputs['Normal'], _wn.nodes['Principled BSDF'].inputs['Normal'])
RAILW = frostify(mat('rail_white', (0.78, 0.76, 0.72), 0.45))
GRASS = noisy(mat('grass', (0.09, 0.2, 0.035), 0.92), 0.15, 0.4, 0.05)
_gn2 = GRASS.node_tree; _gb2 = _gn2.nodes['Principled BSDF']; _gbm2 = _gn2.nodes.new('ShaderNodeBump'); _gbm2.inputs['Strength'].default_value = 0.5
_gn2.links.new(tnoise(_gn2, coord(_gn2), 60.0, 8), _gbm2.inputs['Height']); _gn2.links.new(_gbm2.outputs['Normal'], _gb2.inputs['Normal'])
frostify(GRASS)
ROCK = frostify(noisy(mat('rock', (0.33, 0.31, 0.29), 0.85), 6.0, 0.4))
BARK = frostify(mat('bark', (0.12, 0.08, 0.05), 0.9))
LEAF = [frostify(noisy(mat(f'leaf{k}', c_, 0.8, sheen=0.4), 3.0, 0.35)) for k, c_ in enumerate(((0.07, 0.19, 0.04), (0.11, 0.24, 0.05), (0.16, 0.22, 0.04)))]
PINE = frostify(noisy(mat('pine', (0.03, 0.1, 0.04), 0.85), 5.0, 0.3))
SIDING = [frostify(noisy(mat(f'siding{k}', c_, 0.7), 1.5, 0.15)) for k, c_ in enumerate(((0.62, 0.6, 0.52), (0.45, 0.52, 0.58)))]
ROOF = frostify(noisy(mat('roof', (0.12, 0.11, 0.11), 0.8), 4.0, 0.3))
HILL = frostify(noisy(mat('hill', (0.06, 0.12, 0.05), 0.95), 0.05, 0.4))
WIN_M = bpy.data.materials.new('window'); WIN_M.use_nodes = True; _wi = WIN_M.node_tree; _wib = _wi.nodes['Principled BSDF']
_wib.inputs['Base Color'].default_value = (0.05, 0.06, 0.07, 1); _wib.inputs['Roughness'].default_value = 0.08
_wib.inputs['Emission Color'].default_value = (1.0, 0.72, 0.4, 1); _wi.links.new(math_(_wi, 'MULTIPLY', objattr(_wi, 'lit'), 2.6), _wib.inputs['Emission Strength'])

# ---- the porch: plank deck, white railing with balusters and posts (one post carries the thermometer)
YARD = []
for k in range(26):                                                # planks running out toward the yard
    x_ = -3.0 + k * 0.235; YARD.append(box(f'plank{k}', (0.22, 4.0, 0.04), (x_, -0.8, DECK_Z - 0.02), WOOD, bv=0.006))
YARD.append(box('deck_frame', (6.4, 0.2, 0.6), (0, RAIL_Y + 0.1, DECK_Z / 2), WOOD))
POSTS_X = [-3.0, -1.55, -0.32, 1.25, 3.0]
for i, x_ in enumerate(POSTS_X):
    YARD.append(box(f'post{i}', (0.09, 0.09, 1.12), (x_, RAIL_Y, DECK_Z + 0.56), RAILW, bv=0.008))
    YARD.append(box(f'cap{i}', (0.12, 0.12, 0.03), (x_, RAIL_Y, DECK_Z + 1.135), RAILW, bv=0.006))
YARD.append(box('toprail', (6.1, 0.1, 0.045), (0, RAIL_Y, RAIL_Z), RAILW, bv=0.008))
YARD.append(box('botrail', (6.1, 0.06, 0.04), (0, RAIL_Y, DECK_Z + 0.1), RAILW, bv=0.005))
for k in range(48):
    x_ = -2.94 + k * 0.125
    if min(abs(x_ - p_) for p_ in POSTS_X) < 0.07: continue
    YARD.append(box(f'bal{k}', (0.035, 0.035, 0.88), (x_, RAIL_Y, DECK_Z + 0.56), RAILW))
# ---- the lawn, sloping gently down to the lake; the pond is a dish cut into it
def ground_z(x, y):
    z = -0.025 * max(y - 2.0, 0.0) - 0.0004 * x * x
    if y > 24: z -= 0.07 * (y - 24) ** 1.3
    return z
_vs, _fs = [], []; _NX, _NY = 90, 90; _xs = np.linspace(-60, 60, _NX); _ys = [1.3 + 34.0 * (j / (_NY - 1)) ** 1.15 for j in range(_NY)]
PC = Vector((1.6, 8.5)); PRX, PRY = 2.8, 1.9
for j, y_ in enumerate(_ys):
    for i, x_ in enumerate(_xs):
        z_ = ground_z(x_, y_); d_ = math.hypot((x_ - PC.x) / (PRX + 0.6), (y_ - PC.y) / (PRY + 0.6))
        if d_ < 1.0: z_ -= 0.35 * (1 - d_ * d_)
        _vs.append((x_, y_, z_))
for j in range(_NY - 1):
    for i in range(_NX - 1): a0 = j * _NX + i; _fs.append((a0, a0 + 1, a0 + _NX + 1, a0 + _NX))
LAWN = mesh('lawn', _vs, _fs, GRASS); YARD.append(LAWN)
# ---- water: dark glassy water with moving ripples; property 'ice' grows an ice sheet in from the shore
def water_mat(name, mode):
    m = mat(name, (0.01, 0.025, 0.03), 0.04, ior=1.33); nt = m.node_tree; b = nt.nodes['Principled BSDF']; oc = coord(nt, 'Object')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 3.0 if mode == 'pond' else 0.6
    nz.inputs['Detail'].default_value = 4; nt.links.new(oc, nz.inputs['Vector']); nt.links.new(objattr(nt, 'w'), nz.inputs['W'])
    bm_ = nt.nodes.new('ShaderNodeBump'); bm_.inputs['Strength'].default_value = 0.12; nt.links.new(nz.outputs['Fac'], bm_.inputs['Height'])
    sx = sepz(nt, oc)
    if mode == 'pond':                                            # elliptical distance: 1 at the shore, 0 in the middle
        dd = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'POWER', math_(nt, 'DIVIDE', sx.outputs['X'], PRX), 2.0), math_(nt, 'POWER', math_(nt, 'DIVIDE', sx.outputs['Y'], PRY), 2.0)))
        edge = math_(nt, 'SUBTRACT', 1.0, dd)
    else:                                                         # the lake: from its near shore (local y 0) out
        edge = math_(nt, 'DIVIDE', sx.outputs['Y'], 400.0)
    jag = tnoise(nt, oc, 1.4 if mode == 'pond' else 0.08, 4)
    ice = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', objattr(nt, 'ice'), math_(nt, 'ADD', edge, math_(nt, 'MULTIPLY', jag, 0.18))), 40.0), 0.0), 1.0)
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 2.2 if mode == 'pond' else 0.25; nt.links.new(oc, vo.inputs['Vector'])
    crack = math_(nt, 'LESS_THAN', vo.outputs['Distance'], 0.025)
    icec = mixc(nt, tnoise(nt, oc, 4.0 if mode == 'pond' else 0.3, 5), (0.55, 0.68, 0.78), (0.8, 0.86, 0.92)); icec = mixc(nt, math_(nt, 'MULTIPLY', crack, 0.6), icec, (0.95, 0.97, 1.0))
    nt.links.new(mixc(nt, ice, (0.01, 0.025, 0.03), icec), b.inputs['Base Color'])
    nt.links.new(mixc(nt, ice, (0.04, 0.04, 0.04, 1), (0.25, 0.25, 0.25, 1)), b.inputs['Roughness'])
    nm = nt.nodes.new('ShaderNodeMix'); nm.data_type = 'VECTOR'
    nt.links.new(ice, nm.inputs['Factor']); nt.links.new(bm_.outputs['Normal'], nm.inputs[4]); nm.inputs[5].default_value = (0, 0, 1)
    nt.links.new(nm.outputs[1], b.inputs['Normal'])
    edgeglow = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', ice, math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', objattr(nt, 'ice'), math_(nt, 'ADD', edge, math_(nt, 'MULTIPLY', jag, 0.18)))), 12.0), 1.0))), objattr(nt, 'front'))
    b.inputs['Emission Color'].default_value = (0.7, 0.9, 1.0, 1); nt.links.new(edgeglow, b.inputs['Emission Strength'])         # the freezing edge glints
    return m
POND_M = water_mat('pond_w', 'pond')
_pv, _pf = [], []; _pn = 64
for i in range(_pn):
    a_ = 2 * math.pi * i / _pn; _pv.append(((PRX + 0.25) * math.cos(a_), (PRY + 0.25) * math.sin(a_), 0))
_pv.append((0, 0, 0)); _pf = [(i, (i + 1) % _pn, _pn) for i in range(_pn)]
POND = mesh('pond', _pv, _pf, POND_M, loc=(PC.x, PC.y, ground_z(PC.x, PC.y) - 0.12)); POND['ice'] = 0.0; POND['w'] = 0.0; POND['front'] = 0.0
subsurf(POND, 3); YARD.append(POND)
random.seed(12)
for k in range(30):                                                # stones round the pond
    a_ = 2 * math.pi * k / 30 + random.uniform(-0.05, 0.05); rr = 1.0 + random.uniform(0.0, 0.1)
    x_, y_ = PC.x + (PRX + 0.15) * rr * math.cos(a_), PC.y + (PRY + 0.15) * rr * math.sin(a_)
    YARD.append(prim('ico_sphere', f'pstone{k}', ROCK, loc=(x_, y_, ground_z(x_, y_) - 0.06), subdivisions=2, radius=random.uniform(0.16, 0.3), scale=(1.2, 1, 0.55)))
for k in range(26):                                                # cattails on the far bank
    a_ = R(random.uniform(40, 140)); x_, y_ = PC.x + (PRX + 0.1) * math.cos(a_) * random.uniform(0.85, 1.0), PC.y + (PRY + 0.1) * math.sin(a_) * random.uniform(0.85, 1.0)
    h_ = random.uniform(0.7, 1.2); lean = (random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), h_)
    z0 = ground_z(x_, y_) - 0.15; YARD.append(tube(f'reed{k}', [(x_, y_, z0), (x_ + lean[0], y_ + lean[1], z0 + h_)], 0.007, LEAF[0], seg=5))
    YARD.append(prim('cylinder', f'cat{k}', BARK, loc=(x_ + lean[0] * 0.9, y_ + lean[1] * 0.9, z0 + h_ * 0.88), radius=0.018, depth=0.14, vertices=8))
# ---- the lake beyond the lawn, a far shore of hills and dark pines
LAKE_Y = 33.0; LAKE_Z = ground_z(0, LAKE_Y) + 0.15
LAKE_M = water_mat('lake_w', 'lake')
LAKE = mesh('lake', [(-500, 0, 0), (500, 0, 0), (500, 700, 0), (-500, 700, 0)], [(0, 1, 2, 3)], LAKE_M, loc=(0, LAKE_Y - 3.0, LAKE_Z)); LAKE['ice'] = 0.0; LAKE['w'] = 0.0; LAKE['front'] = 0.0
YARD.append(LAKE)
_hv, _hf = [], []; _HN = 160
for i in range(_HN):
    x_ = -900 + 1800 * i / (_HN - 1); h_ = 30 + 26 * mnoise.noise(Vector((x_ * 0.004, 0.3, 0))) + 12 * mnoise.noise(Vector((x_ * 0.015, 1.1, 0)))
    _hv += [(x_, 520 + 30 * mnoise.noise(Vector((x_ * 0.01, 2, 0))), LAKE_Z - 2), (x_, 600, LAKE_Z + h_)]
for i in range(_HN - 1): _hf.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
YARD.append(mesh('hills', _hv, _hf, HILL))
def pine(name, at, h):
    out = [prim('cylinder', name + '_t', BARK, loc=Vector(at) + Vector((0, 0, h * 0.15)), radius=h * 0.025, depth=h * 0.3, vertices=8)]
    for j in range(4):
        z_ = h * (0.2 + 0.2 * j); r_ = h * (0.26 - 0.05 * j)
        out.append(prim('cone', f'{name}_c{j}', PINE, loc=Vector(at) + Vector((0, 0, z_ + h * 0.15)), radius1=r_, radius2=0.0, depth=h * 0.36, vertices=12))
    return out
def leafy(name, at, h):
    out = [prim('cylinder', name + '_t', BARK, loc=Vector(at) + Vector((0, 0, h * 0.25)), radius=h * 0.035, depth=h * 0.5, vertices=8)]
    for j in range(5):
        p_ = Vector(at) + Vector((random.uniform(-0.18, 0.18) * h, random.uniform(-0.18, 0.18) * h, h * random.uniform(0.55, 0.85)))
        o = prim('ico_sphere', f'{name}_l{j}', random.choice(LEAF), loc=p_, subdivisions=3, radius=h * random.uniform(0.2, 0.28))
        d_ = o.modifiers.new('lumpy', 'DISPLACE'); tx = bpy.data.textures.new(f'{name}_tx{j}', 'CLOUDS'); tx.noise_scale = 0.35 * h / 6; d_.texture = tx; d_.strength = 0.35 * h / 6
        out.append(o)
    return out
random.seed(31)
for k, (x_, y_, h_) in enumerate([(-7.5, 7.0, 7.5), (-10.0, 13.0, 9.0), (-15.0, 18.5, 7.5), (8.5, 6.5, 7.0), (10.5, 13.5, 8.5), (16.0, 19.0, 7.0), (-4.5, 27, 8), (5.5, 29, 9)]):
    YARD += leafy(f'tree{k}', (x_, y_, ground_z(x_, y_)), h_)
for k in range(46):                                                # pines along the shore, on both sides of the open view
    x_ = random.choice([-1, 1]) * random.uniform(9, 70); y_ = random.uniform(24, 34)
    YARD += pine(f'pine{k}', (x_, y_, ground_z(x_, y_)), random.uniform(6, 12))
for k in range(140):                                               # far shore pines (dark shapes against the hills)
    x_ = random.uniform(-420, 420); y_ = random.uniform(505, 560)
    YARD += pine(f'fpine{k}', (x_, y_, LAKE_Z - 1), random.uniform(14, 26))
# ---- two neighbours' houses (windows light up after the blackout)
WINDOWS = []
def house(name, at, w, d, h, yaw, m):
    g = empty(name, loc=at); g.rotation_euler = (0, 0, yaw); out = [g]
    out.append(box(name + '_b', (w, d, h), (0, 0, h / 2), m, parent=g))
    rv = [(-w / 2 - 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, d / 2 + 0.3, h), (-w / 2 - 0.3, d / 2 + 0.3, h), (0, -d / 2 - 0.3, h + 2.2), (0, d / 2 + 0.3, h + 2.2)]
    out.append(mesh(name + '_r', rv, [(0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4)], ROOF, parent=g, smooth_=False))
    for row in range(2):
        for i in range(3):
            wo = box(f'{name}_w{row}{i}', (1.0, 0.06, 1.2), (-w / 2 + w * (i + 0.5) / 3, -d / 2 - 0.01, 1.3 + row * 2.4), WIN_M, parent=g); wo['lit'] = 0.0; WINDOWS.append(wo); out.append(wo)
    return out
YARD += house('house_l', Vector((-9.5, 21, ground_z(-9.5, 21))), 9, 7, 5.2, R(18), SIDING[0])
YARD += house('house_r', Vector((11.5, 25, ground_z(11.5, 25))), 8, 7, 4.8, R(-22), SIDING[1])
for k, o in enumerate(WINDOWS): o['on_t'] = 0.25 + 0.9 * h1(k + 3)            # each window comes on at its own moment after the blackout

# ---- sky: day gradient (bright toward the sun), the Sun's disk, a pale day Moon; night: stars on a dome round the yard
_wt = W_.node_tree; _wtc = _wt.nodes.new('ShaderNodeTexCoord'); _wsx = _wt.nodes.new('ShaderNodeSeparateXYZ'); _wt.links.new(_wtc.outputs['Generated'], _wsx.inputs['Vector'])
SKYR = _wt.nodes.new('ShaderNodeValToRGB'); _el = SKYR.color_ramp.elements
_el[0].position = 0.45; _el[0].color = (0.55, 0.5, 0.42, 1); _el[1].position = 0.8; _el[1].color = (0.05, 0.16, 0.55, 1)
_e2 = _el.new(0.505); _e2.color = (0.92, 0.72, 0.5, 1); _e3 = _el.new(0.56); _e3.color = (0.3, 0.48, 0.85, 1)
_wmr = _wt.nodes.new('ShaderNodeMapRange'); _wmr.inputs['From Min'].default_value = -1.0; _wmr.inputs['From Max'].default_value = 1.0
_wt.links.new(_wsx.outputs['Z'], _wmr.inputs['Value']); _wt.links.new(_wmr.outputs['Result'], SKYR.inputs['Fac'])
_wsun = _wt.nodes.new('ShaderNodeVectorMath'); _wsun.operation = 'DOT_PRODUCT'; _wt.links.new(_wtc.outputs['Generated'], _wsun.inputs[0]); _wsun.inputs[1].default_value = SUN_DIR
_wgl = math_(_wt, 'POWER', math_(_wt, 'MAXIMUM', _wsun.outputs['Value'], 0.0), 18.0)
SKY_DAYK = _wt.nodes.new('ShaderNodeValue'); SKY_DAYK.outputs[0].default_value = 1.0
_wday = mixc(_wt, math_(_wt, 'MULTIPLY', _wgl, 0.6), SKYR.outputs['Color'], (1.0, 0.8, 0.5))
_wnight = (0.008, 0.014, 0.035)
_wt.links.new(mixc(_wt, SKY_DAYK.outputs[0], _wnight, _wday), WBG.inputs['Color'])
WBG.inputs['Strength'].default_value = 1.0
SUN_DISK = prim('uv_sphere', 'sun_disk', emis('sun_disk_m', (1.0, 0.82, 0.55), 60.0), loc=SUN_DIR * 4000, segments=32, ring_count=16, radius=58)
SUN_DISK.visible_shadow = False; SUN_DISK.visible_diffuse = False; SUN_DISK.visible_glossy = True
SUN_GLOW = prim('plane', 'sun_glow', HALO_M, loc=SUN_DIR * 3990, size=2.0); SUN_GLOW.scale = (300, 300, 300); SUN_GLOW['a'] = 1.0; SUN_GLOW.visible_shadow = False
SUN_GLOW.rotation_mode = 'QUATERNION'; SUN_GLOW.rotation_quaternion = (-SUN_DIR).to_track_quat('Z', 'Y')
MOON_M = mat('moon_m', (0.6, 0.6, 0.58), 0.95); _mn = MOON_M.node_tree; _mb = _mn.nodes['Principled BSDF']
_mn.links.new(mixc(_mn, math_(_mn, 'GREATER_THAN', tnoise(_mn, coord(_mn), 2.5, 5), 0.55), (0.75, 0.75, 0.72), (0.45, 0.45, 0.45)), _mb.inputs['Emission Color'])
_mn.links.new(math_(_mn, 'MULTIPLY', objattr(_mn, 'lit'), 2.5), _mb.inputs['Emission Strength'])
MOON = prim('uv_sphere', 'moon', MOON_M, loc=MOON_DIR * 3000, segments=48, ring_count=24, radius=110); MOON['lit'] = 0.35; MOON.visible_shadow = False
YSTARS = bpy.data.materials.new('ystars'); YSTARS.use_nodes = True; _ys_ = YSTARS.node_tree; _ys_.nodes.remove(_ys_.nodes['Principled BSDF'])
star_shader(_ys_, (0.0, 0.0, 0.0), 300.0)
YDOME = prim('uv_sphere', 'ydome', YSTARS, loc=(0, 0, 0), segments=64, ring_count=32, radius=6000); YDOME.visible_shadow = False
YDOME.visible_diffuse = False; YDOME.visible_glossy = False
SUNL = bpy.data.lights.new('sunlight', 'SUN'); SUNL.energy = 3.6; SUNL.color = (1.0, 0.86, 0.66); SUNL.angle = R(0.6)
SUN_O = bpy.data.objects.new('sunlight', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_mode = 'QUATERNION'; SUN_O.rotation_quaternion = (-SUN_DIR).to_track_quat('-Z', 'Y')
NIGHTL = bpy.data.lights.new('nightfill', 'SUN'); NIGHTL.energy = 0.0; NIGHTL.color = (0.45, 0.6, 1.0); NIGHTL.angle = R(8)
NIGHT_O = bpy.data.objects.new('nightfill', NIGHTL); S.collection.objects.link(NIGHT_O); NIGHT_O.rotation_mode = 'QUATERNION'; NIGHT_O.rotation_quaternion = (-MOON_DIR).to_track_quat('-Z', 'Y')   # night light comes from the Moon's side
PORCH = light_at('porch', 'POINT', (0.9, -1.6, DECK_Z + 2.4), (0, 2, 1), 0.0, (1.0, 0.68, 0.38), 0.06)
YARD += [SUN_DISK, SUN_GLOW, MOON, YDOME]

# ---- the thermometer on the post left of you: white board, ticks, glass tube, red column (steps down with the °F readout)
TPOST = Vector((POSTS_X[2], RAIL_Y - 0.047, DECK_Z + 0.8))
THERM = []
_tb = box('th_board', (0.08, 0.012, 0.36), TPOST + Vector((0, -0.006, 0)), mat('th_white', (0.9, 0.9, 0.86), 0.35), bv=0.004); THERM.append(_tb)
for k in range(13):
    w_ = 0.026 if k % 2 == 0 else 0.016
    THERM.append(box(f'th_tick{k}', (w_, 0.002, 0.0028), TPOST + Vector((-0.02 + (0.026 - w_) / 2 * 0, -0.013, -0.12 + 0.02 * k)), mat('th_ink', (0.03, 0.03, 0.03), 0.6)))
GLASS = mat('glass', (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=1.45)
THERM.append(prim('cylinder', 'th_tube', GLASS, loc=TPOST + Vector((0.012, -0.018, 0.02)), radius=0.0065, depth=0.29, vertices=16))
RED = mat('th_red', (0.75, 0.02, 0.02), 0.25, emit=(0.6, 0.0, 0.0), estr=0.4)
THERM.append(prim('uv_sphere', 'th_bulb', RED, loc=TPOST + Vector((0.012, -0.018, -0.135)), radius=0.012, segments=16, ring_count=8))
TH_COL = prim('cylinder', 'th_col', RED, loc=TPOST + Vector((0.012, -0.018, -0.13)), radius=0.0035, depth=1.0, vertices=12); THERM.append(TH_COL)
THERM.append(box('th_screw', (0.01, 0.004, 0.01), TPOST + Vector((0, -0.013, 0.165)), STEEL if 'STEEL' in globals() else mat('steel', (0.5, 0.5, 0.52), 0.4, 1.0)))
def therm_set(f_):
    """column height for f_ degrees F: the scale runs -20 F (bottom tick) to 100 F (top tick)"""
    h_ = clamp((f_ + 20) / 120.0, 0.02, 1.0) * 0.24 + 0.01
    TH_COL.scale = (1, 1, h_); TH_COL.location = TPOST + Vector((0.012, -0.018, -0.13 + h_ / 2))
therm_set(70)
YARD += THERM
WATER_W = [POND, LAKE]

def yard_mode(day, frost=0.0, t=0.0):
    """day 1 = sunny; 0 = the blackout night. frost 0..1 everywhere."""
    SKY_DAYK.outputs[0].default_value = day; SUNL.energy = 3.6 * day
    SUN_DISK.hide_render = day < 0.5; SUN_GLOW.hide_render = day < 0.5
    NIGHTL.energy = 0.3 * (1 - day); PORCH.data.energy = 0.0 if day > 0.5 else 110.0
    YDOME.hide_render = day > 0.5; FROST_AMT.outputs[0].default_value = frost
    for o in CLOUDS_D if 'CLOUDS_D' in globals() else []: o.hide_render = day < 0.5
    for o in WATER_W: o['w'] = 0.25 * t
YARD_ALL = YARD + [o for o in []]
