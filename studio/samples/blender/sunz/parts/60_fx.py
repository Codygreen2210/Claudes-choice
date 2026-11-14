
# ================================================================ props and effects
# ---- the stopwatch that lies in your open left hand: chrome case, crown and loop, white dial, ticks, a red sweep hand
SW_R = 0.028; SW_T = 0.013
CHROME = mat('chrome', (0.8, 0.78, 0.74), 0.22, 1.0)
DIAL_M = mat('dial', (0.95, 0.94, 0.9), 0.45, emit=(1.0, 0.98, 0.94), estr=0.25)
INK = mat('sw_ink', (0.03, 0.03, 0.03), 0.5)
HAND_RED = mat('sw_red', (0.85, 0.05, 0.03), 0.3, emit=(0.6, 0.0, 0.0), estr=0.3)
SWATCH = empty('stopwatch'); SWATCH.rotation_mode = 'QUATERNION'
SW = [lathe('sw_case', [(0, -SW_T / 2), (SW_R * 0.9, -SW_T / 2), (SW_R, -SW_T * 0.25), (SW_R, SW_T * 0.3), (SW_R * 0.93, SW_T / 2), (SW_R * 0.88, SW_T / 2)], 48, CHROME, SWATCH)]
SW.append(lathe('sw_dial', [(0, SW_T / 2 - 0.0005), (SW_R * 0.88, SW_T / 2 - 0.0005)], 48, DIAL_M, SWATCH))
for k in range(60):                                                 # minute/second ticks (longer every 5)
    a_ = 2 * math.pi * k / 60; L_ = 0.0045 if k % 5 == 0 else 0.0022; r_ = SW_R * 0.82 - L_ / 2
    o = box(f'sw_tick{k}', (0.0007 if k % 5 else 0.0011, L_, 0.0004), (r_ * math.sin(a_), r_ * math.cos(a_), SW_T / 2), INK, rot=(0, 0, -a_), parent=SWATCH); SW.append(o)
SW_SUB = lathe('sw_sub', [(0.0058, SW_T / 2 + 0.0001), (0.0066, SW_T / 2 + 0.0001), (0.0066, SW_T / 2 + 0.0003)], 32, INK, SWATCH); SW_SUB.location = (0, -0.010, 0); SW.append(SW_SUB)
SW_HAND = empty('sw_hand_pivot', SWATCH); SW_HAND.rotation_mode = 'XYZ'
SW.append(box('sw_hand', (0.0009, SW_R * 0.95, 0.0005), (0, SW_R * 0.33, SW_T / 2 + 0.0008), HAND_RED, parent=SW_HAND))
SW.append(prim('cylinder', 'sw_hub', HAND_RED, parent=SWATCH, loc=(0, 0, SW_T / 2 + 0.0009), radius=0.0018, depth=0.0012, vertices=16))
SW.append(prim('cylinder', 'sw_stem', CHROME, parent=SWATCH, loc=(0, SW_R + 0.003, 0), rot=(R(90), 0, 0), radius=0.003, depth=0.007, vertices=16))
SW.append(prim('cylinder', 'sw_crown', CHROME, parent=SWATCH, loc=(0, SW_R + 0.0075, 0), rot=(R(90), 0, 0), radius=0.0045, depth=0.004, vertices=24))
SW.append(prim('torus', 'sw_loop', CHROME, parent=SWATCH, loc=(0, SW_R + 0.0145, 0), rot=(0, R(90), 0), major_radius=0.0065, minor_radius=0.0012, major_segments=24, minor_segments=8))
SW_ALL = [SWATCH, SW_HAND] + SW
def stopwatch_set(on, pos=None, quat=None, secs=0.0):
    for o in SW: o.hide_render = not on
    if not on: return
    SWATCH.location = pos; SWATCH.rotation_quaternion = quat; SW_HAND.rotation_euler = (0, 0, -2 * math.pi * (secs % 60.0) / 60.0)

# ---- breath: soft white puffs that leave from just under the lens, roll forward and fade
BREATH_M = bpy.data.materials.new('breath'); BREATH_M.use_nodes = True; _bn = BREATH_M.node_tree; _bb = _bn.nodes['Principled BSDF']; BREATH_M.blend_method = 'BLEND'
_bg = _bn.nodes.new('ShaderNodeTexGradient'); _bg.gradient_type = 'SPHERICAL'; _bn.links.new(coord(_bn, 'Object'), _bg.inputs['Vector'])
_bz = _bn.nodes.new('ShaderNodeTexNoise'); _bz.noise_dimensions = '4D'; _bz.inputs['Scale'].default_value = 3.0; _bz.inputs['Detail'].default_value = 5
_bn.links.new(coord(_bn, 'Object'), _bz.inputs['Vector']); _bn.links.new(objattr(_bn, 'w'), _bz.inputs['W'])
_ba = math_(_bn, 'MULTIPLY', math_(_bn, 'MULTIPLY', math_(_bn, 'POWER', _bg.outputs['Fac'], 1.5), math_(_bn, 'MAXIMUM', math_(_bn, 'SUBTRACT', math_(_bn, 'MULTIPLY', _bz.outputs['Fac'], 2.2), 0.7), 0.0)), objattr(_bn, 'a'))
_bn.links.new(math_(_bn, 'MINIMUM', math_(_bn, 'MULTIPLY', _ba, 0.6), 0.5), _bb.inputs['Alpha']); _bb.inputs['Base Color'].default_value = (0.9, 0.93, 0.98, 1); _bb.inputs['Roughness'].default_value = 1.0
_bb.inputs['Emission Color'].default_value = (0.8, 0.88, 1.0, 1); _bb.inputs['Emission Strength'].default_value = 0.35
BREATH = []
for k in range(4):
    o = prim('plane', f'breath{k}', BREATH_M, size=2.0); o['a'] = 0.0; o['w'] = 3.0 * k; o.visible_shadow = False; o.rotation_mode = 'QUATERNION'; BREATH.append(o)
def breath_set(t, starts, amt=1.0):
    """puffs that start at the given times (seconds); each lives 1.3 s"""
    for k, o in enumerate(BREATH):
        o.hide_render = True
        if k >= len(starts): continue
        age = (t - starts[k]) / 1.3
        if not (0.0 <= age <= 1.0): continue
        o.hide_render = False; o['a'] = amt * smooth(0.0, 0.12, age) * (1 - smooth(0.45, 1.0, age)); o['w'] = 3.0 * k + 0.8 * age
        o.location = cam_pt(0.02 * math.sin(k * 2.1), -0.1 + 0.07 * age, 0.17 + 0.3 * age); s_ = 0.045 + 0.12 * age; o.scale = (s_, s_ * 0.7, s_)
        o.rotation_quaternion = CAM.rotation_quaternion @ Quaternion((0, 0, 1), 0.6 * k + 0.3 * age)

# ---- ice crystals glittering down through the porch light (day 3)
XTAL_M = mat('xtal', (0.9, 0.95, 1.0), 0.05, emit=(0.8, 0.9, 1.0), estr=1.5)
XTALS = []
random.seed(66)
for k in range(70):
    o = prim('ico_sphere', f'xtal{k}', XTAL_M, subdivisions=1, radius=random.uniform(0.0018, 0.0035)); o['ph'] = (random.uniform(-1.2, 1.2), random.uniform(0.4, 3.5), random.uniform(0, 1), random.uniform(0.25, 0.5))
    o.visible_shadow = False; XTALS.append(o)
def xtal_set(t, on):
    for o in XTALS:
        o.hide_render = not on
        if not on: continue
        x_, z_, p0, sp = o['ph']; y_ = 1.2 - 2.4 * ((p0 + sp * t * 0.35) % 1.0)
        o.location = cam_pt(x_ * z_ * 0.55 + 0.03 * math.sin(t * 2 + p0 * 9), y_ * z_ * 0.55, z_)

# ---- birds crossing the day sky (two flapping wings each)
BIRD_M = mat('bird', (0.03, 0.03, 0.035), 0.8)
BIRDS = []
for k in range(4):
    b_ = empty(f'bird{k}'); b_.rotation_mode = 'XYZ'; wings = []
    for sg in (-1, 1):
        w_ = mesh(f'bird{k}_w{sg}', [(0, -0.12, 0), (0, 0.12, 0), (sg * 0.55, 0.0, 0.0)], [(0, 1, 2)], BIRD_M, parent=b_); w_.rotation_mode = 'XYZ'; wings.append(w_)
    bod = prim('uv_sphere', f'bird{k}_b', BIRD_M, parent=b_, segments=8, ring_count=6, radius=0.09, scale=(0.6, 2.2, 0.6)); BIRDS.append((b_, wings, bod))
def birds_set(t, on):
    for k, (b_, wings, bod) in enumerate(BIRDS):
        for o in wings + [bod]: o.hide_render = not on
        if not on: continue
        u_ = t * 0.035 + 0.17 * k; b_.location = Vector((-60 + 120 * (u_ % 1.0) + 3 * k, 70 + 6 * k, 22 + 2.5 * k + 1.5 * math.sin(t * 0.8 + k)))
        b_.rotation_euler = (0, 0, R(-90)); b_.scale = (4, 4, 4); fl = 0.6 * math.sin(t * 9 + k * 1.3)
        wings[0].rotation_euler = (0, fl, 0); wings[1].rotation_euler = (0, -fl, 0)

# ---- soft clouds low in the day sky
CLOUD_M = bpy.data.materials.new('cloud_card'); CLOUD_M.use_nodes = True; _cc = CLOUD_M.node_tree; _ccb = _cc.nodes['Principled BSDF']; CLOUD_M.blend_method = 'BLEND'
_ccg = _cc.nodes.new('ShaderNodeTexGradient'); _ccg.gradient_type = 'SPHERICAL'; _cc.links.new(coord(_cc, 'Object'), _ccg.inputs['Vector'])
_ccn = tnoise(_cc, coord(_cc, 'Object'), 2.2, 7, 0.3)
_cc.links.new(math_(_cc, 'MINIMUM', math_(_cc, 'MULTIPLY', math_(_cc, 'POWER', _ccg.outputs['Fac'], 0.8), math_(_cc, 'MAXIMUM', math_(_cc, 'SUBTRACT', math_(_cc, 'MULTIPLY', _ccn, 2.6), 1.05), 0.0)), 1.0), _ccb.inputs['Alpha'])
_ccb.inputs['Base Color'].default_value = (1.0, 0.95, 0.9, 1); _ccb.inputs['Roughness'].default_value = 1.0
_ccb.inputs['Emission Color'].default_value = (1.0, 0.85, 0.7, 1); _ccb.inputs['Emission Strength'].default_value = 0.6
CLOUDS_D = []
random.seed(18)
for k in range(9):
    az = R(random.uniform(-40, 40)); el = R(random.uniform(6, 22)); d_ = random.uniform(1800, 2600)
    p_ = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))) * d_
    o = prim('plane', f'cloud{k}', CLOUD_M, loc=p_, size=2.0); s_ = random.uniform(160, 320); o.scale = (s_ * 2.2, s_, s_)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (-p_).to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), random.uniform(-0.15, 0.15)); o.visible_shadow = False; CLOUDS_D.append(o)
YARD += CLOUDS_D
frostify(JACKET_M); frostify(GLOVE_M)                               # the sleeve and gloves frost over with everything else
