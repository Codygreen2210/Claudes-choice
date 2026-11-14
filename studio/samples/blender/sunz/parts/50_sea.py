
# ================================================================ the ocean under the ice: a cut-open block on a dark stage (house x-ray look),
# then down to a hot vent on the sea floor with tube worms, and a close look at the microbes living off its chemicals
SS = Vector((0, -200000, 0))
BW, BD, BH = 7.0, 3.0, 9.0                                          # the block: width, depth, height of the water
ICE_T = 1.1
# ice lid: white-blue, cracked, a little see-through at the cut
ICE_M = mat('ice_lid', (0.75, 0.85, 0.95), 0.25, trans=0.35, ior=1.31); _in = ICE_M.node_tree; _ib = _in.nodes['Principled BSDF']
_ivo = _in.nodes.new('ShaderNodeTexVoronoi'); _ivo.feature = 'DISTANCE_TO_EDGE'; _ivo.inputs['Scale'].default_value = 0.8; _ivo.inputs['Randomness'].default_value = 1.0; _in.links.new(coord(_in), _ivo.inputs['Vector'])
_icr = math_(_in, 'MULTIPLY', math_(_in, 'LESS_THAN', _ivo.outputs['Distance'], 0.02), math_(_in, 'GREATER_THAN', tnoise(_in, coord(_in), 1.2, 3), 0.45))
_in.links.new(mixc(_in, _icr, mixc(_in, tnoise(_in, coord(_in), 3.0, 6), (0.55, 0.72, 0.88), (0.85, 0.92, 0.98)), (1.0, 1.0, 1.0)), _ib.inputs['Base Color'])
_ib.inputs['Emission Color'].default_value = (0.5, 0.75, 1.0, 1); _in.links.new(math_(_in, 'MULTIPLY', _icr, 0.8), _ib.inputs['Emission Strength'])
SEA = []
ICE_LID = box('ice_lid', (BW, BD, ICE_T), SS + Vector((0, 0, ICE_T / 2)), ICE_M, bv=0.03); SEA.append(ICE_LID)
SNOW_M = mat('snow', (0.9, 0.92, 0.96), 0.6); SEA.append(box('snow_top', (BW, BD, 0.08), SS + Vector((0, 0, ICE_T + 0.04)), SNOW_M, bv=0.03))
# water: a see-through glowing blue block, brighter at the top, deep blue at the bottom; currents swirl inside
WATER_M = bpy.data.materials.new('sea_water'); WATER_M.use_nodes = True; _wn2 = WATER_M.node_tree; _wb2 = _wn2.nodes['Principled BSDF']; WATER_M.blend_method = 'BLEND'
_wz = sepz(_wn2, coord(_wn2, 'Generated'))
_wcol = ramp(_wn2, _wz.outputs['Z'], [(0.0, (0.0, 0.02, 0.08)), (0.6, (0.02, 0.15, 0.38)), (1.0, (0.08, 0.35, 0.6))])
_wsw = _wn2.nodes.new('ShaderNodeTexNoise'); _wsw.noise_dimensions = '4D'; _wsw.inputs['Scale'].default_value = 0.6; _wsw.inputs['Distortion'].default_value = 3.0
_wn2.links.new(coord(_wn2, 'Object'), _wsw.inputs['Vector']); _wn2.links.new(objattr(_wn2, 'w'), _wsw.inputs['W'])
_wn2.links.new(_wcol, _wb2.inputs['Base Color']); _wn2.links.new(_wcol, _wb2.inputs['Emission Color'])
_wn2.links.new(math_(_wn2, 'MULTIPLY_ADD', _wsw.outputs['Fac'], 1.4, 0.15), _wb2.inputs['Emission Strength'])
_wb2.inputs['Alpha'].default_value = 0.88; _wb2.inputs['Roughness'].default_value = 0.35; _wb2.inputs['Specular IOR Level'].default_value = 0.15
WATER = box('sea_water', (BW, BD, BH), SS + Vector((0, 0, -BH / 2)), WATER_M); WATER['w'] = 0.0; SEA.append(WATER)
# the sea floor slab and its rocky top
FLOOR_M = noisy(mat('seafloor', (0.12, 0.1, 0.09), 0.9), 2.0, 0.4)
SEA.append(box('floor_slab', (BW, BD, 0.9), SS + Vector((0, 0, -BH - 0.45)), FLOOR_M, bv=0.03))
CURR_M = emis_mix('current', (0.5, 0.85, 1.0), 3.0, 'a')
CURRENTS = []
random.seed(77)
for k in range(28):                                                 # streaks riding slow loops: the water is still moving
    o = prim('uv_sphere', f'cur{k}', CURR_M, segments=10, ring_count=6, radius=0.05, scale=(1.0, 1.0, 1.0)); o['a'] = 0.0
    o['ph'] = (random.uniform(-2.6, 2.6), random.uniform(-1.0, 1.0), random.uniform(-BH + 1.2, -1.0), random.uniform(0.6, 1.6), random.uniform(0, 6.28), random.uniform(0.25, 0.6))
    o.visible_shadow = False; o.rotation_mode = 'QUATERNION'; CURRENTS.append(o)
def fish(name, at, size, col):
    m = mat(name + '_m', col, 0.4, emit=col, estr=0.6)
    body = prim('uv_sphere', name, m, loc=at, segments=16, ring_count=10, radius=size, scale=(2.4, 0.55, 0.9))
    tail = mesh(name + '_tail', [(-size * 2.2, 0, 0), (-size * 3.3, 0, size * 0.8), (-size * 3.3, 0, -size * 0.8)], [(0, 1, 2)], m, parent=body)
    tail.location = (0, 0, 0); body.rotation_mode = 'XYZ'; return [body, tail]
FISH = []
for k in range(5):
    FISH.append(fish(f'fish{k}', SS + Vector((0, 0, -3 - k)), random.uniform(0.09, 0.15), (0.35, 0.6, 0.7)))
SEA += CURRENTS + [p_ for f_ in FISH for p_ in f_]
def sea_set(t, a_cur=1.0):
    WATER['w'] = 0.12 * t
    for o in CURRENTS:
        x0, y0, z0, r_, ph, sp = o['ph']; a_ = ph + sp * t * 2.0
        p_ = Vector((x0 + r_ * math.cos(a_), y0, z0 + 0.6 * r_ * math.sin(a_))); p_.x = clamp(p_.x, -BW / 2 + 0.2, BW / 2 - 0.2)
        o.location = SS + p_; tg = Vector((-math.sin(a_), 0, 0.6 * math.cos(a_))).normalized()
        o.rotation_quaternion = tg.to_track_quat('X', 'Z'); o.scale = (3.5, 0.6, 0.6); o['a'] = a_cur
    for k, (b_, tl) in enumerate(FISH):
        u_ = (0.08 * t * (1 + 0.3 * k) + h1(k + 1)) % 1.0; dirn = 1 if k % 2 == 0 else -1
        x_ = (-BW / 2 + 0.4 + (BW - 0.8) * u_) * dirn; b_.location = SS + Vector((x_, -0.3 + 0.5 * h1(k + 7), -1.6 - 1.4 * k + 0.15 * math.sin(t * 2 + k)))
        b_.rotation_euler = (0, 0.1 * math.sin(t * 3 + k), 0 if dirn > 0 else math.pi)

# ---- the vent (on the sea floor of its own stage, far below the block): a chimney with glowing cracks, black smoke, tube worms
VS = SS + Vector((0, 0, -400))
CHIM_M = mat('chimney', (0.08, 0.07, 0.065), 0.85); _cm = CHIM_M.node_tree; _cb = _cm.nodes['Principled BSDF']
_cvo = _cm.nodes.new('ShaderNodeTexVoronoi'); _cvo.feature = 'DISTANCE_TO_EDGE'; _cvo.inputs['Scale'].default_value = 2.2; _cm.links.new(coord(_cm), _cvo.inputs['Vector'])
_cz = sepz(_cm, coord(_cm, 'Object'))
_ccr = math_(_cm, 'MULTIPLY', math_(_cm, 'POWER', math_(_cm, 'MAXIMUM', math_(_cm, 'SUBTRACT', 1.0, math_(_cm, 'MULTIPLY', _cvo.outputs['Distance'], 12.0)), 0.0), 2.0),
             math_(_cm, 'MAXIMUM', math_(_cm, 'SUBTRACT', 1.0, math_(_cm, 'DIVIDE', _cz.outputs['Z'], 3.4)), 0.15))
_cb.inputs['Emission Color'].default_value = (1.0, 0.38, 0.05, 1); _cm.links.new(math_(_cm, 'MULTIPLY', math_(_cm, 'MULTIPLY', _ccr, math_(_cm, 'GREATER_THAN', tnoise(_cm, coord(_cm), 0.9, 2), 0.5)), 5.0), _cb.inputs['Emission Strength'])
_cmn = _cm.nodes.new('ShaderNodeBump'); _cmn.inputs['Strength'].default_value = 0.6; _cm.links.new(tnoise(_cm, coord(_cm), 5.0, 8), _cmn.inputs['Height']); _cm.links.new(_cmn.outputs['Normal'], _cb.inputs['Normal'])
VENT = []
_prof = [(0.0, 0.0), (0.95, 0.0), (0.8, 0.5), (0.62, 1.2), (0.55, 2.0), (0.42, 2.8), (0.36, 3.3), (0.28, 3.5), (0.18, 3.5), (0.12, 3.2)]
CHIM = lathe('chimney', _prof, 40, CHIM_M, loc=VS); _cd = CHIM.modifiers.new('lumps', 'DISPLACE'); _ctx = bpy.data.textures.new('chim_tx', 'CLOUDS'); _ctx.noise_scale = 0.35
_cd.texture = _ctx; _cd.strength = 0.25; subsurf(CHIM, 1); VENT.append(CHIM)
for k, (dx, dy, sc_) in enumerate([(-1.6, 0.4, 0.55), (1.5, -0.2, 0.45), (0.8, 1.4, 0.35)]):
    o = lathe(f'chim_s{k}', [(r_ * sc_, z_ * sc_) for r_, z_ in _prof], 32, CHIM_M, loc=VS + Vector((dx, dy, 0))); _md = o.modifiers.new('lumps', 'DISPLACE'); _md.texture = _ctx; _md.strength = 0.15; VENT.append(o)
SEAFLOOR = lathe('vent_floor', [(0, -0.2), (6, -0.1), (40, 0.2), (200, 2.0)], 64, FLOOR_M, loc=VS); VENT.append(SEAFLOOR)
_sfb = FLOOR_M.node_tree; _sfbm = _sfb.nodes.new('ShaderNodeBump'); _sfbm.inputs['Strength'].default_value = 0.5
_sfb.links.new(tnoise(_sfb, coord(_sfb), 3.0, 8), _sfbm.inputs['Height']); _sfb.links.new(_sfbm.outputs['Normal'], _sfb.nodes['Principled BSDF'].inputs['Normal'])
# black smoke: soft cards that rise and grow, lit orange from below
SMOKE_M = bpy.data.materials.new('smoke'); SMOKE_M.use_nodes = True; _sm = SMOKE_M.node_tree; _smb = _sm.nodes['Principled BSDF']; SMOKE_M.blend_method = 'BLEND'
_smg = _sm.nodes.new('ShaderNodeTexGradient'); _smg.gradient_type = 'SPHERICAL'; _sm.links.new(coord(_sm, 'Object'), _smg.inputs['Vector'])
_smn = _sm.nodes.new('ShaderNodeTexNoise'); _smn.noise_dimensions = '4D'; _smn.inputs['Scale'].default_value = 2.5; _smn.inputs['Detail'].default_value = 6
_sm.links.new(coord(_sm, 'Object'), _smn.inputs['Vector']); _sm.links.new(objattr(_sm, 'w'), _smn.inputs['W'])
_sma = math_(_sm, 'MULTIPLY', math_(_sm, 'MULTIPLY', math_(_sm, 'POWER', _smg.outputs['Fac'], 1.2), math_(_sm, 'MAXIMUM', math_(_sm, 'SUBTRACT', math_(_sm, 'MULTIPLY', _smn.outputs['Fac'], 2.0), 0.6), 0.0)), objattr(_sm, 'a'))
_sm.links.new(math_(_sm, 'MINIMUM', _sma, 1.0), _smb.inputs['Alpha']); _smb.inputs['Base Color'].default_value = (0.18, 0.17, 0.17, 1); _smb.inputs['Roughness'].default_value = 1.0
_smb.inputs['Emission Color'].default_value = (1.0, 0.35, 0.08, 1); _sm.links.new(math_(_sm, 'MULTIPLY', objattr(_sm, 'glow'), 1.0), _smb.inputs['Emission Strength'])
SMOKE = []
for k in range(14):
    o = prim('plane', f'smoke{k}', SMOKE_M, size=2.0); o['a'] = 0.0; o['w'] = h1(k) * 10; o['glow'] = 0.0; o['ph'] = h1(k + 20); o.visible_shadow = False
    o.rotation_mode = 'QUATERNION'; SMOKE.append(o)
VENT += SMOKE
# tube worms: white tubes with red plumes, swaying
WORM_T = mat('worm_tube', (0.85, 0.82, 0.75), 0.6); WORM_P = mat('worm_plume', (0.75, 0.04, 0.04), 0.4, sheen=0.6)
WORMS = []
random.seed(55)
_clumps = [(-1.15, -0.55), (1.2, -0.75), (-0.2, -1.05), (0.55, 0.9), (-1.0, 0.8)]
for k in range(44):
    cx_, cy_ = _clumps[k % len(_clumps)]; base = VS + Vector((cx_ + random.uniform(-0.28, 0.28), cy_ + random.uniform(-0.2, 0.2), 0.0)); h_ = random.uniform(0.45, 1.1)
    t_ = tube(f'worm{k}', [(0, 0, 0), (0, 0, h_ * 0.5), (0, 0, h_)], 0.05, WORM_T, seg=10); t_.location = base
    p_ = prim('uv_sphere', f'plume{k}', WORM_P, loc=(0, 0, h_ + 0.09), segments=14, ring_count=8, radius=0.1, scale=(1, 1, 1.5)); p_.parent = t_
    t_.rotation_mode = 'XYZ'; t_['ph'] = random.uniform(0, 6.3); WORMS.append(t_); VENT += [t_, p_]
VENT_L = light_at('vent_light', 'POINT', VS + Vector((0, -0.4, 2.2)), VS, 0.0, (1.0, 0.45, 0.12), 0.4)
VENT_FILL = light_at('vent_fill', 'AREA', VS + Vector((-4, -6, 6)), VS + Vector((0, 0, 1.5)), 0.0, (0.3, 0.5, 1.0), 4)
def vent_set(t):
    for k, o in enumerate(SMOKE):
        age = (o['ph'] + 0.35 * t) % 1.0; z_ = 3.2 + 6.0 * age; sc_ = 0.35 + 2.2 * age
        o.location = VS + Vector((0.25 * math.sin(k * 1.7 + t * 0.6) * age, -0.05 * k, z_)); o.scale = (sc_, sc_, sc_)
        o['a'] = smooth(0.0, 0.08, age) * (1 - smooth(0.7, 1.0, age)) * 0.85; o['w'] = h1(k) * 10 + 0.4 * t; o['glow'] = 1.5 * (1 - smooth(0.0, 0.5, age))
        o.rotation_quaternion = (CAM.location - o.location).to_track_quat('Z', 'Y')
    for o in WORMS: o.rotation_euler = (0.12 * math.sin(t * 1.3 + o['ph']), 0.12 * math.cos(t * 1.1 + o['ph']), 0)

# ---- the microbes up close (their own little stage): a rock face, rod-shaped microbes glowing green, chemical specks drifting in and eaten
MS = SS + Vector((0, 0, -900))
MROCK_M = noisy(mat('mrock', (0.1, 0.08, 0.07), 0.9), 3.0, 0.4); _mr = MROCK_M.node_tree; _mrb = _mr.nodes['Principled BSDF']
_mrm = _mr.nodes.new('ShaderNodeBump'); _mrm.inputs['Strength'].default_value = 0.35; _mr.links.new(tnoise(_mr, coord(_mr), 1.5, 10), _mrm.inputs['Height']); _mr.links.new(_mrm.outputs['Normal'], _mrb.inputs['Normal'])
_mrb.inputs['Emission Color'].default_value = (1.0, 0.4, 0.08, 1)
_mr.links.new(math_(_mr, 'MULTIPLY', math_(_mr, 'POWER', math_(_mr, 'MAXIMUM', math_(_mr, 'SUBTRACT', tnoise(_mr, coord(_mr), 0.8, 3), 0.55), 0.0), 1.5), 3.0), _mrb.inputs['Emission Strength'])
_mv, _mf = [], []; _MN = 60
for j in range(_MN):
    for i in range(_MN):
        x_ = -1.5 + 3.0 * i / (_MN - 1); y_ = -1.5 + 3.0 * j / (_MN - 1); _mv.append((x_, y_, 0.12 * mnoise.noise(Vector((x_ * 1.3, y_ * 1.3, 0.5))) + 0.05 * mnoise.noise(Vector((x_ * 4, y_ * 4, 2)))))
for j in range(_MN - 1):
    for i in range(_MN - 1): a0 = j * _MN + i; _mf.append((a0, a0 + 1, a0 + _MN + 1, a0 + _MN))
MROCK = mesh('mrock', _mv, _mf, MROCK_M, loc=MS); subsurf(MROCK, 1)
MICRO_M = mat('microbe', (0.1, 0.55, 0.3), 0.3, trans=0.15, emit=(0.25, 1.0, 0.5), estr=0.8); _mi = MICRO_M.node_tree; _mib = _mi.nodes['Principled BSDF']
_mlw = _mi.nodes.new('ShaderNodeLayerWeight'); _mlw.inputs['Blend'].default_value = 0.4
_mi.links.new(math_(_mi, 'ADD', math_(_mi, 'MULTIPLY', _mlw.outputs['Facing'], 2.5), math_(_mi, 'MULTIPLY', math_(_mi, 'GREATER_THAN', tnoise(_mi, coord(_mi, 'Object'), 9.0, 2), 0.62), 1.5)), _mib.inputs['Emission Strength'])
MICROBES = []
random.seed(91)
_mrM = MROCK.matrix_world
def rock_pt(x_, y_, lift=0.0):
    z_ = 0.12 * mnoise.noise(Vector((x_ * 1.3, y_ * 1.3, 0.5))) + 0.05 * mnoise.noise(Vector((x_ * 4, y_ * 4, 2)))
    return MS + Vector((x_, y_, z_ + lift)), Vector((0, 0, 1))
for k in range(80):
    x_, y_ = random.gauss(0, 0.35), random.gauss(0, 0.35); p_, n_ = rock_pt(x_, y_, 0.028)
    o = prim('uv_sphere', f'mic{k}', MICRO_M, loc=p_, segments=20, ring_count=14, radius=0.021, scale=(1, 1, random.uniform(2.0, 3.2)))
    o.rotation_mode = 'XYZ'; o['ph'] = random.uniform(0, 6.3); o['rot0'] = (R(random.uniform(60, 120)), 0, random.uniform(0, 6.3)); o['p0'] = p_; MICROBES.append(o)
CHEM_M = emis('chem', (1.0, 0.8, 0.15), 6.0)
CHEMS = []
for k in range(70):
    o = prim('ico_sphere', f'chem{k}', CHEM_M, subdivisions=1, radius=0.011); o['tgt'] = k % len(MICROBES); o['ph'] = h1(k + 40); o.visible_shadow = False; CHEMS.append(o)
MIC_L = light_at('mic_light', 'AREA', MS + Vector((0, -2.2, 1.6)), MS, 0.0, (0.5, 0.7, 1.0), 2.0)
MIC_KICK = light_at('mic_kick', 'POINT', MS + Vector((0.8, 0.6, -0.6)), MS, 0.0, (1.0, 0.45, 0.12), 0.3)
MICRO_ALL = [MROCK] + MICROBES + CHEMS
def micro_set(t):
    for o in MICROBES:
        ph = o['ph']; r0 = o['rot0']; o.rotation_euler = (r0[0] + 0.25 * math.sin(t * 3.1 + ph), r0[1] + 0.2 * math.sin(t * 2.3 + ph * 2), r0[2] + 0.3 * math.sin(t * 1.7 + ph))
        o.location = Vector(o['p0']) + Vector((0.01 * math.sin(t * 2 + ph), 0.01 * math.cos(t * 1.6 + ph), 0))
    for o in CHEMS:
        tg = MICROBES[o['tgt']]; age = (o['ph'] + 0.5 * t) % 1.0; src = Vector(tg['p0']) + Vector((0.3 * math.sin(o['ph'] * 20), -0.35, 0.45))
        o.location = src.lerp(tg.location, sm(age)); s_ = 1.0 - smooth(0.85, 1.0, age); o.scale = (max(s_, 0.01),) * 3; o.hide_render = s_ < 0.05
SEA_ALL = SEA + VENT + MICRO_ALL
SEA_KEY = light_at('sea_key', 'AREA', SS + Vector((-5, -10, 6)), SS + Vector((0, 0, -2)), 4000, (0.7, 0.85, 1.0), 6)
