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
# the stands: tiers of fans (small boxes with shirt colors) beyond the baseline and along the side, softly lit; out of focus behind him
FANS = []; _r = random.Random(8)
SHIRTS = [(0.0, 0.25, 0.6), (0.9, 0.3, 0.05), (0.85, 0.85, 0.85), (0.05, 0.05, 0.07), (0.6, 0.1, 0.1), (0.0, 0.35, 0.7)]
FAN_MS = [mat('fan%d' % i, c, 0.8) for i, c in enumerate(SHIRTS)]; FACE_M = mat('fface', (0.45, 0.3, 0.22), 0.6)
SEAT_M = mat('seat', (0.03, 0.05, 0.1), 0.7)
def stand(x0, x1, y0, dy, rows, rot_):
    for r_ in range(rows):
        z = 0.5 + r_ * 0.42; yy = y0 + r_ * dy
        COURT.append(box('tier', (abs(x1 - x0), 0.85, 0.42), V3((x0 + x1) / 2, yy, z - 0.21), SEAT_M) if rot_ == 0 else
                     box('tier', (0.85, abs(x1 - x0), 0.42), V3(yy, (x0 + x1) / 2, z - 0.21), SEAT_M))
        x = x0
        while x < x1:
            if _r.random() < 0.85:
                m_ = FAN_MS[_r.randrange(len(FAN_MS))]; h = _r.uniform(0.62, 0.72)
                p0 = V3(x, yy, z + h / 2) if rot_ == 0 else V3(yy, x, z + h / 2)
                FANS.append(box('fan', (0.36, 0.26, h * 0.7), p0, m_)); FANS.append(prim('uv_sphere', 'fh', FACE_M, loc=p0 + V3(0, 0, h * 0.5), radius=0.1, segments=10, ring_count=6))
            x += _r.uniform(0.5, 0.62)
stand(-9.0, 9.0, HOOP_Y + 6.5, 0.85, 8, 0)
stand(-12.0, 4.0, -9.5, -0.85, 8, 1)
COURT += FANS
# the arena lights: big soft overheads (an NBA court is lit flat and bright) and a warm rim light from the stands side
LIGHTS = [light_at('over1', 'AREA', V3(-2.0, 0.0, 12.0), V3(0, 0.5, 0), 4200, (1.0, 0.97, 0.92), 8.0),
          light_at('over2', 'AREA', V3(3.0, -4.0, 12.0), V3(0, 0.5, 0), 3000, (1.0, 0.97, 0.92), 8.0),
          light_at('rimL', 'AREA', V3(-6.0, 6.0, 5.0), V3(0, 0.6, 1.0), 900, (1.0, 0.85, 0.7), 3.0),
          light_at('fill', 'AREA', V3(-5.0, -5.0, 2.5), V3(0, 0.6, 0.8), 260, (0.8, 0.88, 1.0), 4.0)]
