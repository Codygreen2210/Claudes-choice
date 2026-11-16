# ================================================================ camera + world
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.012, 0.014, 0.02, 1); WBG.inputs['Strength'].default_value = 1.0
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.03; CAM.data.clip_end = 3000
# ================================================================ THE COURT (an NBA arena: hardwood, Thunder-blue paint, the hoop, stands)
# Court frame: the hoop is at y = +HOOP_Y and faces -y; he comes down just in front of it, facing the hoop (+y).
HOOP_Y = 2.2; RIM_Z = 3.05
COURT = []
def wood_mat():
    m = bpy.data.materials.new('wood'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.28; b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.08
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    # boards 5.7 cm wide running along y, staggered butt joints; each board its own shade
    bx = math_(nt, 'FLOOR', math_(nt, 'DIVIDE', sx.outputs['X'], 0.057))
    by = math_(nt, 'FLOOR', math_(nt, 'DIVIDE', math_(nt, 'ADD', sx.outputs['Y'], math_(nt, 'MULTIPLY', math_(nt, 'FRACT', math_(nt, 'MULTIPLY', bx, 0.618)), 2.4)), 2.4))
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '2D'; cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(bx, cb.inputs['X']); nt.links.new(by, cb.inputs['Y'])
    nt.links.new(cb.outputs['Vector'], wn.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.55, 0.33, 0.16, 1); ramp.color_ramp.elements[1].color = (0.78, 0.52, 0.28, 1)
    nt.links.new(wn.outputs['Value'], ramp.inputs['Fac'])
    grain = nt.nodes.new('ShaderNodeTexWave'); grain.bands_direction = 'Y'; grain.inputs['Scale'].default_value = 3.0; grain.inputs['Distortion'].default_value = 12.0; grain.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], grain.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; nt.links.new(ramp.outputs['Color'], mx.inputs['A'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.85; nt.links.new(grain.outputs['Fac'], mr.inputs['Value'])
    cc = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(mr.outputs['Result'], cc.inputs[i]) for i in range(3)]; nt.links.new(cc.outputs['Color'], mx.inputs['B']); mx.inputs['Factor'].default_value = 1.0
    # the paint: the blue lane (4.9 m wide, 5.8 m from the baseline), white lines 5 cm, the restricted-area arc
    X, Y = sx.outputs['X'], sx.outputs['Y']; ax = math_(nt, 'ABSOLUTE', X)
    base_y = HOOP_Y + 1.2
    def lt_(a_, b_): return math_(nt, 'LESS_THAN', a_, b_)
    def gt_(a_, b_): return math_(nt, 'GREATER_THAN', a_, b_)
    lane = math_(nt, 'MULTIPLY', lt_(ax, 2.45), math_(nt, 'MULTIPLY', lt_(Y, base_y), gt_(Y, base_y - 5.8)))
    edge = math_(nt, 'MULTIPLY', lane, math_(nt, 'MAXIMUM', gt_(ax, 2.40), lt_(Y, base_y - 5.75)))
    dx = X; dy = math_(nt, 'SUBTRACT', Y, HOOP_Y); dr = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dy, dy)))
    arc = math_(nt, 'MULTIPLY', lt_(math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', dr, 1.22)), 0.025), lt_(Y, HOOP_Y))
    base_l = lt_(math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', Y, base_y)), 0.025)
    white = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MAXIMUM', edge, arc), base_l), 1.0)
    pm = nt.nodes.new('ShaderNodeMix'); pm.data_type = 'RGBA'; nt.links.new(mx.outputs['Result'], pm.inputs['A']); pm.inputs['B'].default_value = (0.0, 0.1, 0.3, 1)
    nt.links.new(math_(nt, 'MULTIPLY', lane, 0.93), pm.inputs['Factor'])
    wm = nt.nodes.new('ShaderNodeMix'); wm.data_type = 'RGBA'; nt.links.new(pm.outputs['Result'], wm.inputs['A']); wm.inputs['B'].default_value = (0.9, 0.9, 0.88, 1)
    nt.links.new(white, wm.inputs['Factor']); nt.links.new(wm.outputs['Result'], b.inputs['Base Color']); return m
FLOOR = mesh('floor', [(-16, -14, 0), (16, -14, 0), (16, 5, 0), (-16, 5, 0)], [(0, 1, 2, 3)], wood_mat(), smooth_=False); COURT.append(FLOOR)
# beyond the baseline: dark blue apron, the stanchion, the padded base
APRON = mesh('apron', [(-16, HOOP_Y + 1.2, 0.001), (16, HOOP_Y + 1.2, 0.001), (16, 12, 0.001), (-16, 12, 0.001)], [(0, 1, 2, 3)], mat('apron', (0.01, 0.06, 0.16), 0.5), smooth_=False); COURT.append(APRON)
PAD_M = mat('pad', (0.0, 0.18, 0.42), 0.55, sheen=0.3); STEEL_M = mat('steel', (0.15, 0.15, 0.17), 0.35, 0.9)
COURT.append(box('stanch_base', (1.2, 2.2, 0.9), V3(0, HOOP_Y + 3.6, 0.45), PAD_M, 0.06))
COURT.append(box('stanch_post', (0.32, 0.32, 3.2), V3(0, HOOP_Y + 3.0, 2.0), PAD_M, 0.04))
COURT.append(box('stanch_arm', (0.24, 2.4, 0.3), V3(0, HOOP_Y + 1.9, 3.55), PAD_M, 0.04, rot=(R(-12), 0, 0)))
GLASS_M = mat('glass', (0.9, 0.95, 1.0), 0.03, trans=1.0, ior=1.5)
BB = box('backboard', (1.83, 0.025, 1.07), V3(0, HOOP_Y + 0.38, RIM_Z + 0.35), GLASS_M, 0.004); COURT.append(BB)
LINE_W = emis('bbline', (1.0, 1.0, 1.0), 1.2)
for (sz, lc) in (((1.83, 0.03, 0.05), V3(0, HOOP_Y + 0.37, RIM_Z + 0.86)), ((1.83, 0.03, 0.05), V3(0, HOOP_Y + 0.37, RIM_Z - 0.16)),
                 ((0.05, 0.03, 1.07), V3(-0.89, HOOP_Y + 0.37, RIM_Z + 0.35)), ((0.05, 0.03, 1.07), V3(0.89, HOOP_Y + 0.37, RIM_Z + 0.35)),
                 ((0.59, 0.03, 0.05), V3(0, HOOP_Y + 0.365, RIM_Z + 0.43)), ((0.59, 0.03, 0.05), V3(0, HOOP_Y + 0.365, RIM_Z + 0.0)),
                 ((0.05, 0.03, 0.45), V3(-0.29, HOOP_Y + 0.365, RIM_Z + 0.21)), ((0.05, 0.03, 0.45), V3(0.29, HOOP_Y + 0.365, RIM_Z + 0.21))):
    COURT.append(box('bbl', sz, lc, LINE_W))
RIM_M = mat('rim', (0.95, 0.28, 0.03), 0.35, 0.6)
bpy.ops.mesh.primitive_torus_add(major_radius=0.2286, minor_radius=0.0095, major_segments=48, minor_segments=10, location=(0, HOOP_Y, RIM_Z))
RIM = bpy.context.active_object; RIM.name = 'rim'; RIM.data.materials.append(RIM_M); COURT.append(RIM)
COURT.append(box('rim_mount', (0.12, 0.17, 0.08), V3(0, HOOP_Y + 0.29, RIM_Z - 0.03), RIM_M, 0.01))
NET_M = mat('net', (0.97, 0.97, 0.97), 0.8)
for k in range(12):                                                     # net cords: zig-zag down and in
    a0 = 2 * math.pi * k / 12; a1 = a0 + math.pi / 12
    pts = [V3(0.225 * math.cos(a0), HOOP_Y + 0.225 * math.sin(a0), RIM_Z - 0.01), V3(0.18 * math.cos(a1), HOOP_Y + 0.18 * math.sin(a1), RIM_Z - 0.2),
           V3(0.14 * math.cos(a0), HOOP_Y + 0.14 * math.sin(a0), RIM_Z - 0.4)]
    COURT.append(tube('net%d' % k, pts, 0.004, NET_M, seg=6))
    pts2 = [V3(0.225 * math.cos(a1 + math.pi / 12), HOOP_Y + 0.225 * math.sin(a1 + math.pi / 12), RIM_Z - 0.01), V3(0.18 * math.cos(a1), HOOP_Y + 0.18 * math.sin(a1), RIM_Z - 0.2),
            V3(0.14 * math.cos(a1 + math.pi / 12), HOOP_Y + 0.14 * math.sin(a1 + math.pi / 12), RIM_Z - 0.4)]
    COURT.append(tube('netb%d' % k, pts2, 0.004, NET_M, seg=6))
# the ball, knocked loose (bounces away in the first beat)
def ball_mat():
    m = noisy(mat('ball', (0.62, 0.17, 0.03), 0.7), 260.0, 0.22); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    X, Y, Z = sx.outputs['X'], sx.outputs['Y'], sx.outputs['Z']
    def ln(v): return math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', v), 0.004)
    curve = math_(nt, 'SUBTRACT', math_(nt, 'ABSOLUTE', X), math_(nt, 'MULTIPLY_ADD', math_(nt, 'MULTIPLY', Z, Z), 3.5, 0.045))   # the two curved seams
    seam = math_(nt, 'MINIMUM', math_(nt, 'ADD', math_(nt, 'ADD', ln(X), ln(Z)), ln(curve)), 1.0)
    src = next(l.from_socket for l in nt.links if l.to_socket == b.inputs['Base Color'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(src, mx.inputs['A']); mx.inputs['B'].default_value = (0.02, 0.015, 0.01, 1)
    nt.links.new(seam, mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color']); return m
BALL_M = ball_mat()
BALL = prim('uv_sphere', 'ball', BALL_M, radius=0.12, segments=32, ring_count=16); COURT.append(BALL)
BSEAM = emis('seam', (0.02, 0.02, 0.02), 0.0)
# the stands: tiers of seated fans (rounded bodies, heads with hair, some arms up), out of focus behind him.
# A few template meshes are shared by every fan (linked copies), so the crowd is big but quick to build.
FANS = []; _r = random.Random(8)
SHIRTS = [(0.0, 0.25, 0.6), (0.9, 0.3, 0.05), (0.85, 0.85, 0.85), (0.05, 0.05, 0.07), (0.6, 0.1, 0.1), (0.0, 0.35, 0.7), (0.0, 0.25, 0.6), (0.85, 0.85, 0.85)]
FAN_MS = [noisy(mat('fan%d' % i, c, 0.85, sheen=0.4), 30.0, 0.15) for i, c in enumerate(SHIRTS)]
SKINS = [mat('fs%d' % i, c, 0.5) for i, c in enumerate([(0.45, 0.3, 0.22), (0.25, 0.15, 0.1), (0.62, 0.45, 0.35), (0.14, 0.08, 0.05)])]
HAIR_M = mat('fhair', (0.02, 0.015, 0.012), 0.6)
SEAT_M = mat('seat', (0.02, 0.035, 0.08), 0.6)
def _tmpl(kind, m, **kw):
    o = prim(kind, '_t', m, **kw); me = o.data; bpy.data.objects.remove(o); return me
_torso = [_tmpl('uv_sphere', m, radius=1.0, segments=16, ring_count=10, scale=(0.21, 0.15, 0.3)) for m in FAN_MS]
_head = [_tmpl('uv_sphere', m, radius=0.105, segments=14, ring_count=8) for m in SKINS]
_hair = _tmpl('uv_sphere', HAIR_M, radius=0.112, segments=14, ring_count=8, scale=(1.0, 1.0, 0.75))
_arm = [_tmpl('cylinder', m, radius=0.05, depth=0.5, vertices=8) for m in FAN_MS]
def _put(me, loc, rot=(0, 0, 0)):
    o = bpy.data.objects.new('fan', me); S.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; o.visible_shadow = False; FANS.append(o); return o
FLASH_M = emis('flash', (1.0, 0.97, 0.9), 0.0)
_fn = FLASH_M.node_tree.nodes['Emission']; FLASH_M.node_tree.links.new(math_(FLASH_M.node_tree, 'MULTIPLY', objattr(FLASH_M.node_tree, 'fl'), 400.0), _fn.inputs['Strength'])
FLASHES = []
def stand(x0, x1, y0, dy, rows, rot_):
    face = 1.0 if dy < 0 else -1.0                                # fans face the court
    for r_ in range(rows):
        z = 0.5 + r_ * 0.45; yy = y0 + r_ * dy
        COURT.append(box('tier', (abs(x1 - x0), 0.9, 0.45), V3((x0 + x1) / 2, yy, z - 0.225), SEAT_M) if rot_ == 0 else
                     box('tier', (0.9, abs(x1 - x0), 0.45), V3(yy, (x0 + x1) / 2, z - 0.225), SEAT_M))
        x = x0
        while x < x1:
            if _r.random() < 0.9:
                P = (lambda a_, b_, c_: V3(a_, b_, c_)) if rot_ == 0 else (lambda a_, b_, c_: V3(b_, a_, c_))
                lean = _r.uniform(-0.12, 0.12); ti = _r.randrange(len(FAN_MS)); hz = z + 0.3 + _r.uniform(-0.03, 0.05)
                rz = 0.0 if rot_ == 0 else R(90)
                _put(_torso[ti], P(x, yy, hz), (lean * 0.5, 0, rz + lean))
                hp = P(x, yy, hz + 0.39); _put(_head[_r.randrange(4)], hp)
                if _r.random() < 0.7: _put(_hair, hp + V3(0, 0, 0.025))
                if _r.random() < 0.18:                           # arms up, cheering
                    for sd in (-1, 1):
                        _put(_arm[ti], P(x + sd * 0.2, yy, hz + 0.45), (0, sd * R(-15), rz) if rot_ == 0 else (sd * R(15), 0, rz))
                if _r.random() < 0.05:                           # a phone up: flashes now and then
                    fo = prim('uv_sphere', 'fl', FLASH_M, loc=P(x + 0.12, yy + face * 0.25, hz + 0.3), radius=0.02, segments=6, ring_count=4)
                    fo['fl'] = 0.0; fo.visible_shadow = False; FLASHES.append(fo)
            x += _r.uniform(0.48, 0.58)
stand(-10.0, 10.0, HOOP_Y + 6.5, 0.9, 12, 0)
stand(-14.0, 5.0, -9.5, -0.9, 12, 1)
stand(-14.0, 9.5, 11.0, 0.9, 12, 1)                              # the far side: fills the right of the wide shot
COURT += FANS
# ---- the upper bowl: a dark wall over the stands, a glowing LED ribbon (Thunder blue + orange, scrolling) along its foot,
# a far upper deck of tiny lit specks (crowd too far to model), and rows of hanging light rigs that bloom out of focus
WALL_M = mat('wall', (0.008, 0.01, 0.018), 0.7)
def ribbon_mat():
    m = emis('ribbon', (1, 1, 1), 1.0); nt = m.node_tree; e_ = nt.nodes['Emission']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    u_ = math_(nt, 'ADD', math_(nt, 'ADD', sx.outputs['X'], sx.outputs['Y']), objattr(nt, 'scroll'))
    band = math_(nt, 'GREATER_THAN', math_(nt, 'FRACT', math_(nt, 'DIVIDE', u_, 3.0)), 0.5)
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.0, 0.35, 1.0, 1); col.inputs['B'].default_value = (1.0, 0.35, 0.02, 1)
    nt.links.new(band, col.inputs['Factor']); nt.links.new(col.outputs['Result'], e_.inputs['Color']); e_.inputs['Strength'].default_value = 6.0; return m
RIB_M = ribbon_mat(); RIBBONS = []
def deck_mat():
    m = bpy.data.materials.new('deck'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.01, 0.012, 0.02, 1)
    tc = nt.nodes.new('ShaderNodeTexCoord'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 9.0
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.12; ramp.color_ramp.elements[1].color = (0, 0, 0, 1); el = ramp.color_ramp.elements.new(0.0); el.color = (0.9, 0.85, 0.75, 1)
    nt.links.new(vo.outputs['Distance'], ramp.inputs['Fac'])
    tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], tint.inputs['A']); nt.links.new(vo.outputs['Color'], tint.inputs['B'])
    nt.links.new(tint.outputs['Result'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 0.6; return m
DECK_M = deck_mat(); LAMP_M = emis('lamp', (1.0, 0.96, 0.88), 40.0)
def bowl(x0, x1, y0, rot_, out):
    """wall + ribbon + upper deck + light rigs above a stand; out = which way is away from the court (+1/-1)"""
    zt = 0.5 + 12 * 0.45; L_ = abs(x1 - x0); c = (x0 + x1) / 2; yb = y0 + out * 12 * 0.9
    P = (lambda a_, b_, c_: V3(a_, b_, c_)) if rot_ == 0 else (lambda a_, b_, c_: V3(b_, a_, c_))
    SZ = (lambda a_, b_, c_: (a_, b_, c_)) if rot_ == 0 else (lambda a_, b_, c_: (b_, a_, c_))
    COURT.append(box('wall', SZ(L_ + 6, 0.3, 4.0), P(c, yb + out * 0.6, zt + 1.6), WALL_M))
    rb = box('ribbon', SZ(L_ + 6, 0.05, 0.55), P(c, yb + out * 0.42, zt + 0.55), RIB_M); rb['scroll'] = 0.0; rb.visible_shadow = False; COURT.append(rb); RIBBONS.append(rb)
    dk = box('deck', SZ(L_ + 10, 0.2, 9.0), P(c, yb + out * 4.0, zt + 7.5), DECK_M, rot=(R(-out * 35), 0, 0) if rot_ == 0 else (0, R(out * 35), 0)); COURT.append(dk)
    for k in range(int(L_ // 2.2) + 3):                           # the hanging light rigs: a row of bright fixtures high up
        lp = box('lamp', (0.35, 0.35, 0.18), P(x0 - 3 + k * 2.2 + 1.1, yb - out * 1.5, zt + 4.8), LAMP_M); lp.visible_shadow = False; COURT.append(lp)
bowl(-10.0, 10.0, HOOP_Y + 6.5, 0, 1)
bowl(-14.0, 5.0, -9.5, 1, -1)
bowl(-14.0, 9.5, 11.0, 1, 1)
# the arena lights: big soft overheads (an NBA court is lit flat and bright) and a warm rim light from the stands side
LIGHTS = [light_at('over1', 'AREA', V3(-2.0, 0.0, 12.0), V3(0, 0.5, 0), 4200, (1.0, 0.97, 0.92), 8.0),
          light_at('over2', 'AREA', V3(3.0, -4.0, 12.0), V3(0, 0.5, 0), 3000, (1.0, 0.97, 0.92), 8.0),
          light_at('rimL', 'AREA', V3(-6.0, 6.0, 5.0), V3(0, 0.6, 1.0), 900, (1.0, 0.85, 0.7), 3.0),
          light_at('fill', 'AREA', V3(-5.0, -5.0, 2.5), V3(0, 0.6, 0.8), 170, (0.8, 0.88, 1.0), 4.0),
          light_at('back', 'AREA', V3(2.5, 6.5, 6.0), V3(0.45, 1.25, 0.9), 1400, (0.75, 0.85, 1.0), 2.0)]
for _o in LIGHTS: _o['e0'] = _o.data.energy
