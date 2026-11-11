# ================================================================ OPEN PRAIRIE under a storm (z up, metres). The trailer sits at the origin,
# the tornado comes in from +y. Grass ground, a fence line, power poles, far tree line; a green-grey sky with a dark storm base overhead
def grass_mat():
    m = mat('grass', (0.2, 0.26, 0.1), 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.08; nz.inputs['Detail'].default_value = 8; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 6.0; nz2.inputs['Detail'].default_value = 4; nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.11, 0.13, 0.05, 1); cr.color_ramp.elements[1].color = (0.32, 0.33, 0.14, 1)
    nt.links.new(math_(nt, 'ADD', nz.outputs['Fac'], math_(nt, 'MULTIPLY', nz2.outputs['Fac'], 0.35)), cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5; nt.links.new(nz2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
GROUND = prim('plane', 'ground', grass_mat(), size=4000)
# grass tufts near the action (one mesh): thin bent blades that lean with the wind ('wind' prop drives a shader-free lean via shape key)
def tufts(name, n, area, seed, m):
    rr = random.Random(seed); vs, fs = [], []; lean = []
    for i in range(n):
        cx, cy = rr.uniform(area[0], area[1]), rr.uniform(area[2], area[3])
        for b_ in range(5):
            a_ = rr.uniform(0, 2 * math.pi); h = rr.uniform(0.18, 0.5); w = 0.012; x0, y0 = cx + 0.04 * math.cos(a_), cy + 0.04 * math.sin(a_)
            dx, dy = -math.sin(a_) * w, math.cos(a_) * w; k = len(vs)
            vs += [(x0 - dx, y0 - dy, 0), (x0 + dx, y0 + dy, 0), (x0 + 0.3 * h * math.cos(a_), y0 + 0.3 * h * math.sin(a_), h)]; fs.append((k, k + 1, k + 2))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); o = obj(name, me, m)
    sk0 = o.shape_key_add(name='basis'); sk = o.shape_key_add(name='wind')
    for i, v in enumerate(o.data.vertices):
        z = v.co.z
        if z > 0: sk.data[i].co = v.co + Vector((-0.25 * z, -0.6 * z, -0.35 * z))
    return o
TUFT_M = mat('tuft', (0.3, 0.32, 0.12), 0.8); TUFT_M.node_tree.nodes['Principled BSDF'].inputs['Subsurface Weight'].default_value = 0.2
TUFTS = tufts('tufts', 2600, (-14, 14, -16, 10), 3, TUFT_M)
# fence and power poles (wood), wires
WOOD_M = noisy(mat('wood', (0.3, 0.22, 0.14), 0.8), 30, 0.3); WIRE_M = mat('wire', (0.05, 0.05, 0.05), 0.4)
FENCE = []
for i in range(30):
    x = -30 + i * 3.0; FENCE.append(box('post%d' % i, (0.1, 0.1, 1.3), (x, -24.0 + 0.05 * math.sin(i), 0.65), WOOD_M, rot=(0, 0, R(3 * math.sin(i * 1.7)))))
for z in (0.5, 0.9, 1.2): FENCE.append(box('rail%.1f' % z, (90, 0.015, 0.015), (15, -24.0, z), WIRE_M))
POLES = []
for i in range(8):
    x = -60 + i * 35; POLES.append(box('pole%d' % i, (0.28, 0.28, 10), (x, 18, 5), WOOD_M)); POLES.append(box('arm%d' % i, (0.15, 2.2, 0.15), (x, 18, 9.3), WOOD_M))
for i in range(7):
    for dy in (-0.9, 0.9):
        x0, x1 = -60 + i * 35, -60 + (i + 1) * 35; pts = [Vector((x0 + (x1 - x0) * k / 12, 18 + dy, 9.4 - 1.2 * math.sin(math.pi * k / 12))) for k in range(13)]
        POLES.append(tube('wire%d%d' % (i, dy > 0), pts, 0.012, WIRE_M, seg=5))
# far tree line: lumpy dark shapes on the horizon
TREE_M = mat('trees', (0.05, 0.07, 0.04), 0.9); TREES = []
_tr = random.Random(8)
for i in range(70):
    a_ = _tr.uniform(-math.pi, math.pi); d = _tr.uniform(640, 820); x, y = d * math.cos(a_), d * math.sin(a_)
    TREES.append(prim('ico_sphere', 'tree%d' % i, TREE_M, loc=(x, y, _tr.uniform(5, 9)), subdivisions=2, radius=_tr.uniform(8, 16), scale=(1.4, 1.4, _tr.uniform(0.7, 1.1))))
# the trailer (mobile home): long box on skirting, siding lines, windows (warm light inside), a door with steps, a satellite dish
TR = V3(0.0, 0.0, 0.0); TRL, TRW, TRH = 14.0, 4.2, 2.6
SIDING = noisy(mat('siding', (0.78, 0.76, 0.68), 0.6), 3.0, 0.12)
_st = SIDING.node_tree; _wv = _st.nodes.new('ShaderNodeTexWave'); _wv.wave_type = 'BANDS'; _wv.bands_direction = 'Z'; _wv.inputs['Scale'].default_value = 8.0
_tc = _st.nodes.new('ShaderNodeTexCoord'); _st.links.new(_tc.outputs['Object'], _wv.inputs['Vector'])
_bp = _st.nodes.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.3; _st.links.new(_wv.outputs['Fac'], _bp.inputs['Height']); _st.links.new(_bp.outputs['Normal'], _st.nodes['Principled BSDF'].inputs['Normal'])
TRAILER = [box('trailer', (TRL, TRW, TRH), TR + V3(0, 0, 0.75 + TRH / 2), SIDING, 0.04),
           box('skirt', (TRL - 0.2, TRW - 0.2, 0.75), TR + V3(0, 0, 0.375), mat('skirt', (0.5, 0.48, 0.44), 0.7)),
           box('roof', (TRL + 0.2, TRW + 0.3, 0.12), TR + V3(0, 0, 0.75 + TRH + 0.05), mat('roof', (0.6, 0.6, 0.6), 0.4, metal=0.6), 0.02)]
WIN_GLOW = emis('trailer_window', (1.0, 0.75, 0.42), 6.0)
for i, x in enumerate((-5.0, -2.0, 2.5, 5.2)):
    TRAILER.append(box('twin%d' % i, (1.0, 0.03, 0.8), TR + V3(x, -TRW / 2 - 0.01, 2.2), WIN_GLOW))
    TRAILER.append(box('twinf%d' % i, (1.1, 0.04, 0.9), TR + V3(x, -TRW / 2 - 0.005, 2.2), mat('trim', (0.9, 0.9, 0.88), 0.5)))
TRAILER.append(box('door', (0.9, 0.04, 2.0), TR + V3(0.4, -TRW / 2 - 0.02, 1.75), mat('door', (0.55, 0.52, 0.48), 0.5)))
TRAILER.append(box('steps', (1.2, 0.9, 0.6), TR + V3(0.4, -TRW / 2 - 0.5, 0.3), WOOD_M))
# the sky: a dome with storm clouds (noise), green-grey, darker overhead; low cloud base
def sky_mat():
    m = bpy.data.materials.new('sky'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 0.02), nz.inputs['W'])
    up = math_(nt, 'MAXIMUM', sx.outputs['Z'], 0.0)
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.035, 0.05, 0.045, 1); cr.color_ramp.elements[1].color = (0.28, 0.34, 0.3, 1)
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[1].position = 0.75
    nt.links.new(math_(nt, 'SUBTRACT', nz.outputs['Fac'], math_(nt, 'MULTIPLY', up, 0.45)), cr.inputs['Fac'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cr.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
SKY = prim('uv_sphere', 'sky', sky_mat(), segments=64, ring_count=32, radius=900); SKY['tt'] = 0.0
for p_ in SKY.data.polygons: p_.use_smooth = True
SKY.visible_shadow = False
# ---- the TORNADO at TC (moves): a funnel shell that twists (bands in the shader run around it), a dusty debris cloud at its foot
TC0 = V3(10.0, 160.0, 0.0)
def funnel_mat():
    m = bpy.data.materials.new('funnel'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs['Vector'])
    ang = math_(nt, 'ARCTAN2', sx.outputs['Y'], sx.outputs['X'])
    twist = math_(nt, 'ADD', ang, math_(nt, 'ADD', math_(nt, 'MULTIPLY', sx.outputs['Z'], 0.02), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 3.0)))
    cxyz = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', twist, 1.6), cxyz.inputs['X']); nt.links.new(math_(nt, 'MULTIPLY', sx.outputs['Z'], 0.03), cxyz.inputs['Y'])
    nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 0.3), cxyz.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.65
    nt.links.new(cxyz.outputs['Vector'], nz.inputs['Vector'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    dens = math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 0.3), math_(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 1.1, 0.35))
    dens = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', dens, objattr(nt, 'dens')), 0.0), 1.0)
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.025, 0.028, 0.026, 1); cr.color_ramp.elements[1].color = (0.2, 0.19, 0.17, 1)
    nt.links.new(nz.outputs['Fac'], cr.inputs['Fac'])
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(cr.outputs['Color'], df.inputs['Color'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(cr.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 0.25
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(df.outputs['BSDF'], ad.inputs[0]); nt.links.new(em.outputs['Emission'], ad.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(dens, mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(ad.outputs['Shader'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
FUN_M = funnel_mat()
def funnel_mesh(name, prof, seg=96):
    vs, fs = [], []; n = len(prof)
    for z, r in prof:
        for k in range(seg): a_ = 2 * math.pi * k / seg; vs.append((r * math.cos(a_), r * math.sin(a_), z))
    for i in range(n - 1):
        for k in range(seg): a0 = i * seg + k; a1 = i * seg + (k + 1) % seg; fs.append((a0, a1, a1 + seg, a0 + seg))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    return me
_prof = [(z, 22 + 0.00012 * z * z + 6 * math.sin(z * 0.02)) for z in np.linspace(0, 560, 60)] + [(600, 300), (640, 600)]
FUNNEL = obj('funnel', funnel_mesh('funnel', _prof), FUN_M, loc=TC0); FUNNEL['tt'] = 0.0; FUNNEL['dens'] = 1.0; FUNNEL.visible_shadow = False
FUN2 = obj('funnel_outer', funnel_mesh('funnel_outer', [(z, r * 1.45 + 8) for z, r in _prof[:-2]]), FUN_M, loc=TC0); FUN2['tt'] = 0.0; FUN2['dens'] = 0.45; FUN2.visible_shadow = False
WALLCLOUD = prim('cylinder', 'wallcloud', mat('wallcloud', (0.06, 0.07, 0.065), 0.9), loc=TC0 + V3(0, 0, 560), vertices=96, radius=700, depth=60)
for v in WALLCLOUD.data.vertices: v.co.z += mnoise.noise(v.co * 0.008) * 25
