
# ================================================================ the coating and its cracks, the tempering (heat + air), shoes, the ball, the cars
# Coating cracks are a shader on the thin top layer (object space): two spiderwebs (radial lines + broken rings) and a fine
# craze of "thousands of pieces"; each grows by an object property so the frame code can drive them: w0 (the opening crack by
# his shoes), w1 (the hit), cz (the 2019 splinter spreading over the whole floor from the hit).
COAT = LAYERS[0][0]
def coat_mat():
    m = bpy.data.materials.new('coating'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1, 1, 1, 1); b.inputs['Roughness'].default_value = 0.03; b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.5
    p = sepz(nt, coord(nt, 'Object')); X, Y = p.outputs['X'], p.outputs['Y']
    def web(cx, cy, prop, seed, n_rad=17.0):
        dx = math_(nt, 'SUBTRACT', X, cx); dy = math_(nt, 'SUBTRACT', Y, cy)
        r = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dy, dy)))
        ang = math_(nt, 'ARCTAN2', dy, dx)
        wig = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', tnoise(nt, coord(nt, 'Object'), 9.0 + seed, 3.0), 0.5), 0.5)
        f = math_(nt, 'FRACT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'ADD', ang, wig), n_rad / (2 * math.pi)), seed * 0.37))
        dl = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 0.5, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', f, 0.5))), 2 * math.pi / n_rad), r)
        rad = math_(nt, 'LESS_THAN', dl, 0.0011)
        g = math_(nt, 'FRACT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'LOGARITHM', math_(nt, 'ADD', r, 0.012), 2.718), 4.0), math_(nt, 'MULTIPLY', wig, 0.6)))
        dr = math_(nt, 'MULTIPLY', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', 0.5, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', g, 0.5))), 4.0), r)
        brk = math_(nt, 'GREATER_THAN', tnoise(nt, coord(nt, 'Object'), 23.0 + seed, 2.0), 0.47)
        ring = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', dr, 0.0009), brk)
        inside = math_(nt, 'LESS_THAN', r, objattr(nt, prop))
        return math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', rad, ring), inside), r
    w0, _ = web(0.25, -0.02, 'w0', 1.0)                                   # under his feet
    w1, r1 = web(-0.55, 0.15, 'w1', 2.0, 21.0)
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 55.0; nt.links.new(coord(nt, 'Object'), vo.inputs['Vector'])
    cz = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', vo.outputs['Distance'], 0.022), math_(nt, 'LESS_THAN', r1, objattr(nt, 'cz')))
    scm = nt.nodes.new('ShaderNodeMapping'); scm.inputs['Scale'].default_value = (60.0, 2.0, 1.0); scm.inputs['Rotation'].default_value = (0, 0, 0.3)
    nt.links.new(coord(nt, 'Object'), scm.inputs['Vector'])
    scn = nt.nodes.new('ShaderNodeTexNoise'); scn.inputs['Scale'].default_value = 3.0; scn.inputs['Detail'].default_value = 1.0; nt.links.new(scm.outputs[0], scn.inputs['Vector'])
    scuff = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', scn.outputs['Fac'], 0.72), math_(nt, 'MULTIPLY', objattr(nt, 'sc'), 0.35))
    mask = math_(nt, 'MAXIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MAXIMUM', w0, w1), cz), scuff)
    cr = nt.nodes.new('ShaderNodeBsdfPrincipled'); cr.inputs['Base Color'].default_value = (0.95, 0.97, 0.98, 1); cr.inputs['Roughness'].default_value = 0.25
    cr.inputs['Transmission Weight'].default_value = 0.35; cr.inputs['Coat Weight'].default_value = 0.0
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(mask, mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(cr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
COAT.data.materials.clear(); COAT.data.materials.append(coat_mat())
for k_ in ('w0', 'w1', 'cz', 'sc'): COAT[k_] = 0.0
# the coating slides on during "on top sits a thin clear coating" (it is there from frame one too; it lifts away for the layer shot)

# ---- tempering: hot glow (glass 'heat' property) and blasts of cold air (blue streaks above and below the slab)
def air_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    p = sepz(nt, coord(nt, 'Object'))
    st = nt.nodes.new('ShaderNodeTexNoise'); st.inputs['Scale'].default_value = 6.0; st.inputs['Detail'].default_value = 3.0
    cv = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', p.outputs['X'], 0.4), math_(nt, 'MULTIPLY', objattr(nt, 'tw'), -3.0)), cv.inputs['X'])
    nt.links.new(math_(nt, 'MULTIPLY', p.outputs['Y'], 9.0), cv.inputs['Y']); nt.links.new(p.outputs['Z'], cv.inputs['Z']); nt.links.new(cv.outputs[0], st.inputs['Vector'])
    k = math_(nt, 'MULTIPLY', math_(nt, 'POWER', st.outputs['Fac'], 3.0), objattr(nt, 'a'))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (0.55, 0.80, 1.0, 1); e_.inputs['Strength'].default_value = 6.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', k, 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
AIR = []
for k_, zz in enumerate((Z0 + 0.03, SLAB_BOT - 0.03)):
    o = box(f'air{k_}', (BW, BD, 0.02), (0, -BD / 2, zz), air_mat(f'air{k_}')); o['a'] = 0.0; o['tw'] = 0.0; AIR.append(o)

# ---- sneakers (the shoes walking over the coating, and his feet)
SOLE_M = mat('sole', (0.92, 0.91, 0.88), 0.6); LACE_M = mat('lace', (0.95, 0.95, 0.95), 0.7)
UPPER_MS = [noisy(mat(f'upper{i}', c, 0.65, sheen=0.3), 300, 0.12) for i, c in enumerate([(0.08, 0.08, 0.09), (0.55, 0.06, 0.05), (0.85, 0.85, 0.85), (0.12, 0.20, 0.42), (0.40, 0.33, 0.25)])]
def sneaker(name, um, parent=None, loc=(0, 0, 0), yaw=0.0, s=1.0):
    root = empty(name, parent, loc); root.rotation_euler = (0, 0, yaw); root.scale = (s, s, s)
    sole = box(name + '_sole', (0.098, 0.280, 0.022), (0, 0, 0.011), SOLE_M, bv=0.008, parent=root)
    up = prim('uv_sphere', name + '_up', um, root, loc=(0, 0.012, 0.022), scale=(0.050, 0.136, 0.080), segments=28, ring_count=14)   # the upper wraps the foot
    bpy.context.view_layer.update()
    for v in up.data.vertices:
        if v.co.z < 0: v.co.z *= 0.15
        if v.co.y > 0.05: v.co.z *= 1.25                                           # higher at the heel collar
    tube(name + '_lace', [(0.0, -0.01, 0.092), (0.0, -0.07, 0.074)], 0.011, LACE_M, root, seg=6)
    return root
STEPS = []                                                       # shoes landing on the coating one after another (beat 4)
for i in range(8):
    sh = sneaker(f'step{i}', UPPER_MS[i % len(UPPER_MS)], loc=(-1.1 + 0.32 * i, -0.45 - 0.35 * (i % 2), Z0), yaw=R(-8 + 16 * h1(i)))
    STEPS.append(sh)

# ---- the ball that hits the coating too hard (a bowling ball: the classic drop test)
BALL_M = mat('ball', (0.05, 0.08, 0.30), 0.12, coat=1.0)
_bn = BALL_M.node_tree; _bb = _bn.nodes['Principled BSDF']
_bn.links.new(mixc(_bn, tnoise(_bn, coord(_bn, 'Object'), 6.0, 8.0, 4.0), (0.03, 0.04, 0.20), (0.25, 0.05, 0.45)), _bb.inputs['Base Color'])
BALL = prim('uv_sphere', 'ball', BALL_M, loc=(-0.55, -BD / 2 + 0.05 + 0.15, Z0 + 3), radius=0.109, segments=48, ring_count=24)
for k_, (hx, hz) in enumerate(((0.0, 0.07), (-0.022, 0.03), (0.022, 0.03))):
    prim('uv_sphere', f'hole{k_}', mat(f'hole{k_}', (0.01, 0.01, 0.01), 0.6), BALL, loc=(hx, -0.105, hz), scale=(0.011, 0.006, 0.011), segments=12, ring_count=8)

# ---- the payoff: the floor stretches into a long glass shelf and two and a half cars are parked on it
SHELF = box('shelf', (8.0, 14.0, 0.04), (0, -7.0, Z0 - 0.02), GLASS_M); SHELF.hide_render = True
PAINTS = [mat('paint0', (0.55, 0.04, 0.04), 0.25, 0.4, coat=1.0), mat('paint1', (0.85, 0.85, 0.87), 0.25, 0.4, coat=1.0), mat('paint2', (0.06, 0.16, 0.42), 0.25, 0.4, coat=1.0)]
TIRE_M = mat('tire', (0.02, 0.02, 0.02), 0.85); RIM_M = mat('rim', (0.7, 0.7, 0.72), 0.25, 1.0); WIN_M = mat('carwin', (0.02, 0.03, 0.04), 0.05, coat=1.0)
LAMP_M = mat('lamp', (1.0, 0.95, 0.85), 0.1, emit=(1.0, 0.95, 0.85), estr=1.0); TAIL_M = mat('tail', (0.6, 0.02, 0.02), 0.2)
def car(name, paint, half=False):
    root = empty(name)
    L_ = 4.6; ln = L_ / 2 if half else L_; y0 = -L_ / 2; y1 = y0 + ln
    box(name + '_body', (1.80, ln, 0.62), (0, (y0 + y1) / 2, 0.62), paint, bv=0.10, parent=root)
    cab_y1 = min(y1, 1.0) if not half else min(y1, 0.0)
    if cab_y1 > -1.3: box(name + '_cab', (1.62, cab_y1 + 1.3, 0.55), (0, (cab_y1 - 1.3) / 2, 1.18), WIN_M, bv=0.12, parent=root)
    for wy in (-1.45, 1.45):
        if half and wy > 0: continue
        for wx in (-0.86, 0.86):
            prim('uv_sphere', f'{name}_t{wx}{wy}', TIRE_M, root, loc=(wx, wy, 0.33), scale=(0.11, 0.33, 0.33), segments=24, ring_count=12)
            prim('uv_sphere', f'{name}_r{wx}{wy}', RIM_M, root, loc=(wx * 1.05, wy, 0.33), scale=(0.04, 0.2, 0.2), segments=16, ring_count=8)
    for lx in (-0.62, 0.62):
        box(f'{name}_hl{lx}', (0.32, 0.04, 0.12), (lx, y0 + 0.01, 0.72), LAMP_M, parent=root)
        if not half: box(f'{name}_tl{lx}', (0.32, 0.04, 0.12), (lx, y1 - 0.01, 0.74), TAIL_M, parent=root)
    if half: box(name + '_cut', (1.78, 0.02, 0.6), (0, y1, 0.62), mat(name + '_cutm', (0.25, 0.25, 0.27), 0.6, 0.6), parent=root)
    return root
# the cars: Poly Haven's CC0 "covered_car" (a real car under a fitted cover), two whole and one cut in half (bisected, capped dark)
def covered_car(name, half=False):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=asset('covered_car/covered_car_1k.gltf'))
    new_ = [o for o in bpy.data.objects if o not in before]; root = empty(name)
    for o in new_:
        if o.type != 'MESH': o.hide_render = True; continue
        mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
        if half:
            bm_ = bmesh.new(); bm_.from_mesh(o.data)
            bmesh.ops.bisect_plane(bm_, geom=bm_.verts[:] + bm_.edges[:] + bm_.faces[:], plane_co=(0, 0.0, 0), plane_no=(0, 1, 0), clear_outer=True)
            bm_.to_mesh(o.data); bm_.free()
            if not o.data.vertices: o.hide_render = True
    if half: box(name + '_cap', (1.74, 0.02, 1.2), (0.05, -0.01, 0.75), mat(name + '_capm', (0.05, 0.05, 0.055), 0.8), parent=root)
    return root
CARS = [covered_car('car0'), covered_car('car1'), covered_car('car2', half=True)]
CAR_REST = [(-2.1, -6.0), (2.1, -6.6), (0.0, -11.2)]
def show_tree(o, on):
    st_ = [o]
    while st_:
        x = st_.pop(); x.hide_render = not on; st_.extend(x.children)
