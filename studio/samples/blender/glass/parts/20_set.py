
# ================================================================ the set: the Ledge on the 103rd floor, the tower, Chicago 412 m below
# World: the tower face is the plane y = 0 (inside the building is y > 0); the Ledge box sticks out toward -y. Ground z = 0.
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
Z0 = 412.4                                   # top of the Ledge floor: 1,353 ft
BW, BD, BH = 3.05, 1.31, 3.05                # box: 10 ft wide, sticks out 4.3 ft, 10 ft tall
T_CRACK0 = 0.0                               # frame one: a crack shoots across under his shoes
T_LAYERS = word_t(2, 4)                      # "three layers"
T_HEAT = word_t(3, 1)                        # "heated"
T_BLAST = word_t(3, 4)                       # "blasted with cold air"
T_COAT = word_t(4, 5)                        # "coating"
T_SHOES = word_t(4, 9)                       # "millions of shoes"
T_HIT = word_t(5, 4) + 0.05                  # "hits it too hard"
T_SPLINTER = word_t(6, 5)                    # "splintered"
T_FEET = word_t(6, 12)                       # "under people's feet"
T_NEVER = word_t(7, 11)                      # "never broke"
T_TONS = word_t(8, 7)                        # "five tons"
T_CARS = word_t(9, 3)                        # "parking two and a half cars"
T_AIR = word_t(9, 13)                        # "1,300 feet in the air"

# ---- sky: Poly Haven partly-cloudy sky HDRI (light + reflections) and a warm afternoon sun from the south-west
_wn = W_.node_tree; _env = _wn.nodes.new('ShaderNodeTexEnvironment')
_env.image = bpy.data.images.load(asset('kloofendal_48d_partly_cloudy_puresky/kloofendal_48d_partly_cloudy_puresky_2k.hdr'))
_mp = _wn.nodes.new('ShaderNodeMapping'); _mp.inputs['Rotation'].default_value = (0, 0, R(-70))
_wn.links.new(coord(_wn, 'Generated'), _mp.inputs['Vector']); _wn.links.new(_mp.outputs[0], _env.inputs['Vector'])
_wn.links.new(_env.outputs['Color'], WBG.inputs['Color']); WBG.inputs['Strength'].default_value = 1.0
SUN = light_at('sun', 'SUN', (0, 0, 1000), (0, 0, 0), 3.6, (1.0, 0.93, 0.82), 0.02); SUN.rotation_mode = 'XYZ'; SUN.rotation_euler = (R(52), 0, R(-32))
SUN.data.angle = R(1.0)
HAZE = (0.58, 0.66, 0.78)
def haze(m, far=2600.0, amt=0.85):
    """aerial perspective: things far from the camera fade toward the sky colour (cheap, no volume)"""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; cd = nt.nodes.new('ShaderNodeCameraData')
    k = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'EXPONENT', math_(nt, 'DIVIDE', cd.outputs['View Distance'], -far))), amt)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*HAZE, 1); em.inputs['Strength'].default_value = 1.0
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(k, mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ---- the tower: Willis Tower's nine bundled tubes in black glass and dark aluminium (we stand on the west face of a 108-floor tube)
def curtain_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    _geo = nt.nodes.new('ShaderNodeNewGeometry'); p = sepz(nt, _geo.outputs['Position'])                     # world position: pieces line up
    u = math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'ADD', p.outputs['X'], p.outputs['Y']), 1.524))       # 5-ft mullions
    v = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['Z'], 3.93))                                       # a floor every 3.93 m
    mull = math_(nt, 'MAXIMUM', math_(nt, 'GREATER_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.465),
                    math_(nt, 'LESS_THAN', v, 0.22))                                                         # mullion or spandrel band
    nt.links.new(mixc(nt, mull, (0.020, 0.018, 0.016), (0.035, 0.032, 0.030)), b.inputs['Base Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', mull, 0.5), 0.04), b.inputs['Roughness'])
    nt.links.new(math_(nt, 'SUBTRACT', 0.85, math_(nt, 'MULTIPLY', mull, 0.6)), b.inputs['Metallic'])
    b.inputs['Coat Weight'].default_value = 0.3; return m
CURTAIN = curtain_mat('curtain')
TUBE = 22.86; _tx = [-TUBE * 1.5, -TUBE * 0.5, TUBE * 0.5]; _ty = [TUBE * 0.5, TUBE * 1.5, TUBE * 2.5]
_th = [[442, 442, 368], [368, 368, 270], [270, 200, 200]]                  # floors 108 / 90 / 66 / 50 as metres
for i_ in range(3):
    for j_ in range(3):
        h_ = _th[j_][i_] if not (i_ == 1 and j_ == 0) else 442
        box(f'tube{i_}{j_}', (TUBE, TUBE, h_), (_tx[i_] + TUBE * 0.5, _ty[j_], h_ / 2), CURTAIN)
# our face (y = 0) gets a hole for the Ledge opening: the tube in front is split around it
TOWER = [o for o in bpy.data.objects if o.name.startswith('tube')]
_front = bpy.data.objects['tube10']; _front.hide_render = True                       # replace the front middle tube with pieces round the box
_fx0, _fx1 = _tx[1], _tx[1] + TUBE
for nm_, (x0, x1, z0, z1) in {'tf_l': (_fx0, -BW / 2, 0, 442), 'tf_r': (BW / 2, _fx1, 0, 442), 'tf_lo': (-BW / 2, BW / 2, 0, Z0 - 0.04), 'tf_hi': (-BW / 2, BW / 2, Z0 + BH, 442)}.items():
    box(nm_, (x1 - x0, TUBE, z1 - z0), ((x0 + x1) / 2, TUBE / 2, (z0 + z1) / 2), CURTAIN)
# ---- the Skydeck room behind the box: floor, ceiling, back wall, warm lights (mostly seen through the glass)
DECK_FLOOR = box('deck_floor', (BW + 0.6, 6.0, 0.1), (0, 3.0, Z0 - 0.05), noisy(mat('deckfloor', (0.10, 0.10, 0.11), 0.35), 30, 0.25))
box('deck_ceil', (BW + 0.6, 6.0, 0.1), (0, 3.0, Z0 + BH + 0.05), mat('deckceil', (0.35, 0.35, 0.36), 0.8))
box('deck_back', (BW + 0.6, 0.1, BH), (0, 6.0, Z0 + BH / 2), mat('deckback', (0.12, 0.12, 0.13), 0.6))
for sx_ in (-1, 1): box(f'deck_side{sx_}', (0.1, 6.0, BH), (sx_ * (BW / 2 + 0.3), 3.0, Z0 + BH / 2), mat(f'deckside{sx_}', (0.16, 0.16, 0.17), 0.6))
IN_LT = light_at('in_lt', 'AREA', (0, 2.5, Z0 + BH - 0.05), (0, 2.5, Z0), 400, (1.0, 0.86, 0.68), 2.0); IN_LT.visible_camera = False; IN_LT.visible_glossy = False

# ---- the Ledge: three 1/2-inch tempered glass layers laminated with clear interlayers, a thin clear coating on top;
# glass walls on three sides and a glass roof, thin dark metal edge trim. Low-iron glass, green only when seen edge-on.
def glass_mat(name, ior=1.52, absorb=0.6, tint=(0.80, 0.95, 0.90)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1, 1, 1, 1); b.inputs['Roughness'].default_value = 0.0; b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = ior
    b.inputs['Base Color'].default_value = (*[0.985 + 0.015 * c for c in tint], 1)    # a faint low-iron tint (a volume tint cost 5x the render time)
    # heat glow (tempering): object property 'heat' 0..1 adds an orange-hot emission
    em_c = nt.nodes.new('ShaderNodeBlackbody'); em_c.inputs['Temperature'].default_value = 1150
    nt.links.new(em_c.outputs[0], b.inputs['Emission Color']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'heat'), 0.45), b.inputs['Emission Strength'])
    return m
GLASS_M = glass_mat('glass'); INTER_M = glass_mat('interlayer', 1.48, 0.2, (0.95, 0.97, 0.92))
_ib = INTER_M.node_tree.nodes['Principled BSDF']; _ib.inputs['Roughness'].default_value = 0.25; _ib.inputs['Transmission Weight'].default_value = 0.85   # the interlayer reads as a thin pale line edge-on
WALL_M = glass_mat('wallglass', 1.52, 0.6)
TRIM_M = mat('trim', (0.06, 0.06, 0.065), 0.35, 0.8)
TG, TI, TC = 0.0127, 0.0015, 0.0015            # glass, interlayer, coating thickness (m)
LAYERS = []                                    # (object, rest z) top to bottom: coating, glass, inter, glass, inter, glass
_z = Z0
for k_, (nm_, th_, m_) in enumerate((('coat', TC, None), ('g1', TG, GLASS_M), ('i1', TI, INTER_M), ('g2', TG, GLASS_M), ('i2', TI, INTER_M), ('g3', TG, GLASS_M))):
    if nm_ == 'coat': m_ = None
    o = box('layer_' + nm_, (BW - 0.004, BD + 0.10, th_), (0, -BD / 2 + 0.05, _z - th_ / 2), m_ if m_ else mat('tmp', (1, 1, 1), 0.1)); o['heat'] = 0.0
    LAYERS.append([o, _z - th_ / 2]); _z -= th_ + 0.0003                   # hairline gaps: touching glass faces render black in Cycles
SLAB_BOT = _z
# the floor as one piece of glass for every shot except the layer close-ups: laminated layers are index-matched (no internal
# reflections), but separate boxes with air between them reflect at every face and the floor turned into a mirror
SLAB = box('slab', (BW - 0.004, BD + 0.10, LAYERS[1][1] + TG / 2 - SLAB_BOT), (0, -BD / 2 + 0.05, (LAYERS[1][1] + TG / 2 + SLAB_BOT) / 2), GLASS_M); SLAB['heat'] = 0.0
for sx_ in (-1, 1): tube(f'trim_b{sx_}', [(sx_ * BW / 2, 0.05, SLAB_BOT - 0.012), (sx_ * BW / 2, -BD, SLAB_BOT - 0.012)], 0.012, TRIM_M, seg=8)
tube('trim_bf', [(-BW / 2, -BD, SLAB_BOT - 0.012), (BW / 2, -BD, SLAB_BOT - 0.012)], 0.012, TRIM_M, seg=8)
WALLS = [box('wall_f', (BW, 0.038, BH), (0, -BD - 0.019, Z0 + BH / 2), WALL_M), box('roof', (BW, BD, 0.038), (0, -BD / 2, Z0 + BH + 0.019), WALL_M)]
for sx_ in (-1, 1): WALLS.append(box(f'wall_s{sx_}', (0.038, BD, BH), (sx_ * (BW / 2 + 0.019), -BD / 2, Z0 + BH / 2), WALL_M))
for o in WALLS: o['heat'] = 0.0
for sx_ in (-1, 1):
    for zz_ in (Z0 + BH + 0.04, Z0 + 0.005):
        tube(f'trim_{sx_}_{zz_:.0f}', [(sx_ * (BW / 2 + 0.04), 0.0, zz_), (sx_ * (BW / 2 + 0.04), -BD - 0.04, zz_)], 0.015, TRIM_M, seg=8)
    tube(f'trim_v{sx_}', [(sx_ * (BW / 2 + 0.04), -BD - 0.04, Z0), (sx_ * (BW / 2 + 0.04), -BD - 0.04, Z0 + BH + 0.04)], 0.015, TRIM_M, seg=8)
tube('trim_ft', [(-BW / 2 - 0.04, -BD - 0.04, Z0 + BH + 0.04), (BW / 2 + 0.04, -BD - 0.04, Z0 + BH + 0.04)], 0.015, TRIM_M, seg=8)

# ---- Chicago below: a street grid, blocks of buildings (one big mesh, window shader), the river, cars on the streets
def window_city(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    p = sepz(nt, coord(nt, 'Object'))
    u = math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'ADD', p.outputs['X'], p.outputs['Y']), 3.0))
    v = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['Z'], 3.8))
    win = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.33), math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', v, 0.55)), 0.3))
    var = tnoise(nt, coord(nt, 'Object'), 0.004, 2.0)
    wall = mixc(nt, var, (0.62, 0.58, 0.52), (0.30, 0.31, 0.34))
    nt.links.new(mixc(nt, win, wall, (0.10, 0.14, 0.18)), b.inputs['Base Color'])
    nt.links.new(mixc(nt, win, (0.8, 0.8, 0.8), (0.12, 0.12, 0.12)), b.inputs['Roughness'])
    return haze(m)
CITY_M = window_city('city'); ROOF_M = haze(noisy(mat('roofs', (0.30, 0.30, 0.30), 0.85), 0.05, 0.4))
GROUND_M = haze(noisy(mat('ground', (0.16, 0.16, 0.17), 0.9), 0.02, 0.3)); RIVER_M = haze(mat('river', (0.05, 0.10, 0.09), 0.08))
LAKE_M = haze(mat('lake', (0.06, 0.16, 0.22), 0.06))
prim('plane', 'ground', GROUND_M, loc=(0, 0, 0), size=1, scale=(16000, 16000, 1))
box('river', (6000, 60, 0.3), (0, -150, 0.2), RIVER_M)                         # the south branch of the Chicago River, in front of the tower
box('lake', (16000, 7000, 0.3), (0, 6200, 0.2), LAKE_M)                        # Lake Michigan far behind the tower
_bm = bmesh.new(); _rr = random.Random(5); _cx = []
for gx in range(-30, 31):
    for gy in range(-30, 25):
        x0 = gx * 120.0; y0 = gy * 120.0
        if -130 < y0 < -110 or (-90 < x0 < 90 and -60 < y0 < 90): continue          # river and the tower's own block
        d = math.hypot(x0, y0)
        for k in range(_rr.randint(2, 4)):
            w_ = _rr.uniform(25, 50); dd = _rr.uniform(25, 50); hx = x0 + _rr.uniform(-35, 35); hy = y0 + _rr.uniform(-35, 35)
            hmax = 230 * math.exp(-d / 1400) + 18
            h_ = max(10.0, _rr.random() ** 2.2 * hmax)
            r_ = bmesh.ops.create_cube(_bm, size=1.0)
            for v in r_['verts']: v.co = Vector((hx + v.co.x * w_, hy + v.co.y * dd, (v.co.z + 0.5) * h_))
CITY_ME = bpy.data.meshes.new('city'); _bm.to_mesh(CITY_ME); _bm.free(); CITY = obj('city', CITY_ME, CITY_M)
CITY.data.materials.append(ROOF_M)
for p_ in CITY.data.polygons:
    if p_.normal.z > 0.9: p_.material_index = 1
ROAD_M = haze(mat('road', (0.07, 0.07, 0.075), 0.7)); LINE_M = haze(mat('lane', (0.75, 0.72, 0.6), 0.6))
for g in range(-30, 31):
    box(f'road_x{g}', (7400, 16, 0.05), (0, g * 120 + 60, 0.08), ROAD_M); box(f'road_y{g}', (16, 7400, 0.05), (g * 120 + 60, 0, 0.08), ROAD_M)
# cars: strips of little cars per lane, each strip slides along its road (wrapped), so the streets move from frame one
CAR_COLS = [(0.6, 0.6, 0.62), (0.08, 0.08, 0.09), (0.55, 0.06, 0.05), (0.9, 0.9, 0.9), (0.10, 0.18, 0.40), (0.35, 0.35, 0.37)]
CAR_MS = [haze(mat(f'carp{i}', c, 0.3, 0.6, coat=1.0)) for i, c in enumerate(CAR_COLS)]
LANES = []
for li, (axis, g, side) in enumerate([(ax, g, sd) for ax in 'xy' for g in range(-6, 6) for sd in (-1, 1)]):
    bm_ = bmesh.new(); rr_ = random.Random(li * 13 + 1); n_ = 0
    for k in range(60):
        if rr_.random() < 0.45: continue
        s_ = k * 25.0 - 750; L_ = rr_.uniform(4.2, 5.0)
        c_ = bmesh.ops.create_cube(bm_, size=1.0)
        for v in c_['verts']:
            if axis == 'x': v.co = Vector((s_ + v.co.x * L_, g * 120 + 60 + side * 3.0 + v.co.y * 1.8, 0.75 + v.co.z * 1.3))
            else: v.co = Vector((g * 120 + 60 + side * 3.0 + v.co.x * 1.8, s_ + v.co.y * L_, 0.75 + v.co.z * 1.3))
        n_ += 1
    me_ = bpy.data.meshes.new(f'lane{li}'); bm_.to_mesh(me_); bm_.free(); o = obj(f'lane{li}', me_, CAR_MS[li % len(CAR_MS)])
    LANES.append((o, axis, side * (11 + 3 * (li % 3))))
def city_at(t):
    for o, axis, v in LANES:
        d = (v * t) % 25.0
        o.location = (d, 0, 0) if axis == 'x' else (0, d, 0)

TRIMS = [o for o in bpy.data.objects if o.name.startswith('trim')]
