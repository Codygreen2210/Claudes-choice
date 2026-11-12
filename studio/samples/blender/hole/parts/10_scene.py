
# ================================================================ numbers (checked: Live Science / Klotz 2015, NASA, Gizmodo 2013)
G = 9.81
TRIP_MIN = 38.0                        # one way, real (layered) Earth, no air
VMAX_MPH = 17895                       # "speeds over 8 km/s (17,895 mph)"
HR = 1.5                               # shaft radius, m
BALL_R = 0.35

# ================================================================ helpers
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
def mixc(nt, fac, a_, b_):
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    if isinstance(fac, (int, float)): mx.inputs['Factor'].default_value = fac
    else: nt.links.new(fac, mx.inputs['Factor'])
    for k, v in (('A', a_), ('B', b_)):
        if isinstance(v, tuple): mx.inputs[k].default_value = v if len(v) == 4 else (*v, 1)
        else: nt.links.new(v, mx.inputs[k])
    return mx.outputs['Result']
def ramp(nt, fac, stops, interp='LINEAR'):
    r_ = nt.nodes.new('ShaderNodeValToRGB'); el = r_.color_ramp.elements; r_.color_ramp.interpolation = interp
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1); el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p_, c_ in stops[1:-1]: e_ = el.new(p_); e_.color = (*c_, 1)
    nt.links.new(fac, r_.inputs['Fac']); return r_.outputs['Color']
def coord(nt, kind='Object'):
    tc = nt.nodes.new('ShaderNodeTexCoord'); return tc.outputs[kind]
def sepz(nt, vec):
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(vec, sx.inputs[0]); return sx
def tnoise(nt, vec, scale, detail=6.0, dist=0.0):
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nz.inputs['Distortion'].default_value = dist; nt.links.new(vec, nz.inputs['Vector']); return nz.outputs['Fac']
def ring_mesh(name, zs, r, rr, m, parent=None, seg=40, segr=8, loc=(0, 0, 0)):
    """many thin rings (tori) inside a shaft, one mesh"""
    vs, fs = [], []
    for z0 in zs:
        b0 = len(vs)
        for i in range(seg):
            a_ = 2 * math.pi * i / seg
            for j in range(segr):
                c_ = 2 * math.pi * j / segr; R_ = r + rr * math.cos(c_)
                vs.append((R_ * math.cos(a_), R_ * math.sin(a_), z0 + rr * math.sin(c_)))
        for i in range(seg):
            for j in range(segr):
                i2, j2 = (i + 1) % seg, (j + 1) % segr
                fs.append((b0 + i * segr + j, b0 + i2 * segr + j, b0 + i2 * segr + j2, b0 + i * segr + j2))
    return mesh(name, vs, fs, m, parent, loc=loc)

# ================================================================ materials
def rock_wall(name, glow=True):
    """tunnel rock in bands along z; with 'depth' (0 rock .. 0.5 mantle .. 1 core) it turns dark red with glowing cracks, then white-hot"""
    m = mat(name, (0.3, 0.27, 0.24), 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']; oc = coord(nt)
    sz = sepz(nt, oc); band = tnoise(nt, oc, 0.9, 4, 3.0)
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 0.35; wv.inputs['Distortion'].default_value = 6.0
    wv.inputs['Detail'].default_value = 4; nt.links.new(oc, wv.inputs['Vector'])
    rockc = ramp(nt, wv.outputs['Fac'], [(0.0, (0.16, 0.13, 0.11)), (0.45, (0.36, 0.31, 0.26)), (0.7, (0.25, 0.2, 0.16)), (1.0, (0.45, 0.4, 0.34))])
    rockc = mixc(nt, math_(nt, 'MULTIPLY', band, 0.5), rockc, (0.12, 0.1, 0.09))
    if not glow: nt.links.new(rockc, b.inputs['Base Color']); return m
    d = objattr(nt, 'depth')
    mant = math_(nt, 'MULTIPLY_ADD', d, 3.0, -0.6); mant = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', mant, 0.0), 1.0)      # 0.2..0.53
    core = math_(nt, 'MULTIPLY_ADD', d, 3.3, -2.3); core = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', core, 0.0), 1.0)      # 0.7..1.0
    mantc = mixc(nt, wv.outputs['Fac'], (0.09, 0.025, 0.015), (0.2, 0.05, 0.02))
    base = mixc(nt, mant, rockc, mantc); base = mixc(nt, core, base, (0.12, 0.04, 0.015)); nt.links.new(base, b.inputs['Base Color'])
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 1.6; nt.links.new(oc, vo.inputs['Vector'])
    crack = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo.outputs['Distance'], 14.0)), 0.0), 2.0)
    flick = tnoise(nt, oc, 0.6, 3)
    ecol = mixc(nt, core, (1.0, 0.32, 0.05), mixc(nt, flick, (1.0, 0.22, 0.02), (1.0, 0.5, 0.08)))
    nt.links.new(ecol, b.inputs['Emission Color'])
    estr = math_(nt, 'ADD', math_(nt, 'MULTIPLY', crack, math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', mant, math_(nt, 'SUBTRACT', 1.0, core)), 2.2)), math_(nt, 'MULTIPLY', core, math_(nt, 'MULTIPLY_ADD', math_(nt, 'POWER', flick, 3.0), 0.9, 0.04)))
    estr = math_(nt, 'ADD', estr, math_(nt, 'MULTIPLY', mant, 0.12))
    nt.links.new(estr, b.inputs['Emission Strength']); return m
def lamp_ring_mat(name):
    """the light rings in the shaft: fade out once the walls glow on their own"""
    m = emis(name, (1.0, 0.9, 0.75), 9.0); nt = m.node_tree; e_ = nt.nodes['Emission']
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY_ADD', objattr(nt, 'depth'), -3.0, 1.0), 0.0), 9.0), e_.inputs['Strength'])
    return m
CONC = noisy(mat('concrete', (0.36, 0.355, 0.34), 0.9), 3.0, 0.25, 0.08)
STEEL = mat('steel', (0.45, 0.45, 0.47), 0.55, 1.0)
YEL = mat('yellow', (0.9, 0.62, 0.04), 0.5)
BALL_M = mat('ball', (0.85, 0.12, 0.03), 0.22, coat=0.6)
_bn = BALL_M.node_tree; _bz = sepz(_bn, coord(_bn))
_st = math_(_bn, 'LESS_THAN', math_(_bn, 'ABSOLUTE', _bz.outputs['Z']), 0.05)
_bn.links.new(mixc(_bn, _st, (0.85, 0.12, 0.03), (0.92, 0.92, 0.9)), _bn.nodes['Principled BSDF'].inputs['Base Color'])

def collar(name, at, parent=None):
    """concrete collar round the hole, a steel lip, a yellow safety band, four short bollards"""
    pr = [(HR, -2.0), (HR, 0.3), (HR + 0.04, 0.36), (HR + 0.5, 0.36), (HR + 0.62, 0.3), (HR + 0.75, 0.0), (HR + 0.8, -0.1)]
    out = [lathe(name, pr, 64, CONC, parent, loc=at)]
    out.append(lathe(name + '_lip', [(HR - 0.02, 0.3), (HR - 0.02, 0.38), (HR + 0.06, 0.38), (HR + 0.06, 0.36)], 64, STEEL, parent, loc=at))
    out.append(lathe(name + '_band', [(HR + 0.18, 0.361), (HR + 0.36, 0.361)], 64, YEL, parent, loc=at))
    for k in range(4):
        a_ = math.pi / 4 + k * math.pi / 2; p = Vector(at) + Vector((math.cos(a_), math.sin(a_), 0)) * (HR + 1.4)
        out.append(prim('cylinder', f'{name}_post{k}', YEL, loc=p + Vector((0, 0, 0.45)), radius=0.09, depth=0.9, vertices=16))
    return out
def shaft(name, at, depth, ring_every, ring_mat, wall_mat):
    s_ = lathe(name, [(0, -depth), (HR, -depth), (HR, -2.0)], 48, wall_mat, loc=at)
    rg = ring_mesh(name + '_rings', [-3.0 - ring_every * k for k in range(int((depth - 4) / ring_every))], HR - 0.03, 0.035, ring_mat, loc=at)
    s_['depth'] = 0.0; rg['depth'] = 0.0; return s_, rg

# ================================================================ set 1: the farm field, day (at the origin)
DS = Vector((0, 0, 0))
GRASS = noisy(mat('grass', (0.15, 0.27, 0.07), 0.92, sheen=0.4), 0.08, 0.35, 0.05)
_gn = GRASS.node_tree; _gb = _gn.nodes['Principled BSDF']; _bm = _gn.nodes.new('ShaderNodeBump'); _bm.inputs['Strength'].default_value = 0.35
_gn.links.new(tnoise(_gn, coord(_gn), 30.0, 8), _bm.inputs['Height']); _gn.links.new(_bm.outputs['Normal'], _gb.inputs['Normal'])
GROUND = lathe('ground', [(HR + 0.78, -0.08), (6, 0.0), (60, 0.0), (400, 0.0), (4000, -20.0)], 96, GRASS, loc=DS)
DIRT = noisy(mat('dirt', (0.3, 0.22, 0.14), 0.95), 4.0, 0.3, 0.05)
APRON = lathe('apron', [(HR + 0.79, -0.06), (HR + 2.6, 0.005)], 64, DIRT, loc=DS)
COL_D = collar('collar_d', DS)
SHAFT_D, RINGS_D = shaft('shaft_d', DS, 420.0, 7.0, lamp_ring_mat('ringlamp_d'), rock_wall('rock_d', glow=False))
random.seed(5)
for k in range(46):                                                # trees on the field edge: a trunk and a few round crowns
    a_ = random.uniform(0, 2 * math.pi); d_ = random.uniform(28, 160) if k < 30 else random.uniform(160, 420)
    tx_, ty_ = math.cos(a_) * d_, math.sin(a_) * d_; hh = random.uniform(7, 14)
    prim('cylinder', f'trunk_{k}', mat('bark', (0.12, 0.08, 0.05), 0.9), loc=(tx_, ty_, hh * 0.3), radius=0.25, depth=hh * 0.6, vertices=8)
    for j in range(3):
        prim('ico_sphere', f'crown_{k}_{j}', mat(f'leaf_{(k + j) % 3}', (0.07 + 0.03 * ((k + j) % 3), 0.19 + 0.04 * ((k + j) % 3), 0.05), 0.85, sheen=0.5),
             loc=(tx_ + random.uniform(-1.5, 1.5), ty_ + random.uniform(-1.5, 1.5), hh * random.uniform(0.62, 0.85)), subdivisions=2, radius=hh * random.uniform(0.25, 0.36))
FENCE = mat('fence', (0.42, 0.36, 0.28), 0.9)
for k in range(40):                                                # a wire fence line across the back of the field
    x_ = -60 + k * 3.2; prim('cylinder', f'fpost_{k}', FENCE, loc=(x_, 22, 0.6), radius=0.06, depth=1.2, vertices=6)
for z_ in (0.55, 0.95): tube(f'fwire_{z_}', [(-60, 22, z_), (65, 22, z_)], 0.008, STEEL, seg=4)
for k in range(6):                                                 # hay bales
    a_ = 1.2 + k * 0.5; prim('cylinder', f'bale_{k}', noisy(mat('hay', (0.62, 0.5, 0.26), 0.95), 6.0, 0.3), loc=(math.cos(a_) * (14 + k), math.sin(a_) * (14 + k), 0.6),
                             rot=(R(90), 0, a_), radius=0.6, depth=1.2, vertices=24)

# ================================================================ set 2: inside the tunnel (far below the field, closed tube)
TS = Vector((3000, 0, -5000))
TUBE_LEN = 900.0; RING_P = 9.0
TWALL = rock_wall('rock_t')
TUBE = lathe('tube', [(0, -TUBE_LEN / 2), (HR, -TUBE_LEN / 2), (HR, TUBE_LEN / 2), (0, TUBE_LEN / 2)], 64, TWALL, loc=TS)
TRINGS = ring_mesh('tube_rings', [-TUBE_LEN / 2 + 4 + RING_P * k for k in range(int((TUBE_LEN - 8) / RING_P))], HR - 0.03, 0.035, lamp_ring_mat('ringlamp_t'), loc=TS)
TUBE['depth'] = 0.0; TRINGS['depth'] = 0.0
SPARK_M = bpy.data.materials.new('spark'); SPARK_M.use_nodes = True; _pn = SPARK_M.node_tree; _pn.nodes.remove(_pn.nodes['Principled BSDF'])
_pe = _pn.nodes.new('ShaderNodeEmission'); _pd = objattr(_pn, 'depth')
_pn.links.new(mixc(_pn, math_(_pn, 'MINIMUM', math_(_pn, 'MULTIPLY', _pd, 3.0), 1.0), (0.85, 0.8, 0.7), (1.0, 0.45, 0.08)), _pe.inputs['Color'])
_pn.links.new(math_(_pn, 'MULTIPLY_ADD', _pd, 10.0, 1.5), _pe.inputs['Strength']); _pn.links.new(_pe.outputs[0], _pn.nodes['Material Output'].inputs['Surface'])
SPARK_W = 34.0; random.seed(21); SPARKS = []
for k in range(60):                                                # dust in the rock, embers lower down: streaks that show the speed
    a_ = random.uniform(0, 2 * math.pi); r_ = random.uniform(0.45, 1.35); o = prim('ico_sphere', f'spark_{k}', SPARK_M, subdivisions=1, radius=random.uniform(0.008, 0.02))
    o['ph'] = (math.cos(a_) * r_, math.sin(a_) * r_, random.uniform(0, SPARK_W), random.uniform(0.8, 1.25)); o['depth'] = 0.0; o.visible_shadow = False; SPARKS.append(o)
def sparks_set(soff, depth, bases=None):
    for i, o in enumerate(SPARKS):
        x_, y_, z0, sp = o['ph']; zz = z0 + soff * sp; bz = bases[i] if bases else math.floor(zz / SPARK_W) * SPARK_W
        o.location = TS + Vector((x_, y_, zz - bz - SPARK_W * 0.55)); o['depth'] = depth
def spark_bases(soff): return [math.floor((o['ph'][2] + soff * o['ph'][3]) / SPARK_W) * SPARK_W for o in SPARKS]
def tube_set(off, depth):
    for o in (TUBE, TRINGS): o.location = TS + Vector((0, 0, off)); o['depth'] = depth

# ================================================================ set 3: the cutaway Earth in space
CS = Vector((0, 40000, 0)); RE = 10.0
STARS = bpy.data.materials.new('stars'); STARS.use_nodes = True; _sn = STARS.node_tree; _sn.nodes.remove(_sn.nodes['Principled BSDF'])
def star_shader(nt, base, dens_scale=180.0, thresh=0.985, power=40.0):
    e_ = nt.nodes.new('ShaderNodeEmission'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = dens_scale
    nt.links.new(coord(nt, 'Generated'), vo.inputs['Vector']); vo2 = nt.nodes.new('ShaderNodeTexVoronoi'); vo2.inputs['Scale'].default_value = dens_scale * 0.37
    nt.links.new(coord(nt, 'Generated'), vo2.inputs['Vector'])
    s1 = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo.outputs['Distance'], 9.0)), 0.0), power)
    s2 = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo2.outputs['Distance'], 7.0)), 0.0), power * 0.6)
    st = math_(nt, 'ADD', math_(nt, 'MULTIPLY', s1, 2.5), math_(nt, 'MULTIPLY', s2, 6.0))
    col = base if not isinstance(base, tuple) else None
    c_ = mixc(nt, math_(nt, 'MINIMUM', st, 1.0), base, (1.0, 0.97, 0.92))
    nt.links.new(c_, e_.inputs['Color']); e_.inputs['Strength'].default_value = 1.0
    nt.links.new(e_.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])
star_shader(_sn, (0.002, 0.003, 0.008))
SKYBALL = prim('uv_sphere', 'starsphere', STARS, loc=CS, segments=48, ring_count=24, radius=600)
SKYBALL.visible_shadow = True
SUN_C = light_at('sun_c', 'AREA', CS + Vector((90, -60, 55)), CS, 3.0e5, (1.0, 0.95, 0.88), 25)
FILL_C = light_at('fill_c', 'AREA', CS + Vector((-40, -70, -10)), CS, 1.2e4, (0.5, 0.6, 1.0), 30)
# the surface: oceans and land, a quarter wedge cut out (x > 0, y < 0)
def earth_shell(name, r, m, lon0=0.0, lon1=270.0, nlon=180, nlat=90):
    vs, fs = [], []
    for i in range(nlat + 1):
        th = math.pi * i / nlat
        for j in range(nlon + 1):
            ph = R(lon0 + (lon1 - lon0) * j / nlon); vs.append((r * math.sin(th) * math.cos(ph), r * math.sin(th) * math.sin(ph), r * math.cos(th)))
    for i in range(nlat):
        for j in range(nlon): a0 = i * (nlon + 1) + j; fs.append((a0, a0 + 1, a0 + nlon + 2, a0 + nlon + 1))
    return mesh(name, vs, fs, m, loc=CS)
EARTH_M = mat('earth', (0.03, 0.1, 0.32), 0.35); _en = EARTH_M.node_tree; _eb = _en.nodes['Principled BSDF']
_land = tnoise(_en, coord(_en), 0.22, 7, 0.4)
_lm = math_(_en, 'GREATER_THAN', _land, 0.53)
_lc = ramp(_en, tnoise(_en, coord(_en), 0.9, 5), [(0.3, (0.1, 0.22, 0.05)), (0.55, (0.35, 0.3, 0.14)), (0.8, (0.2, 0.3, 0.08))])
_ez = sepz(_en, coord(_en)); _ice = math_(_en, 'GREATER_THAN', math_(_en, 'ABSOLUTE', _ez.outputs['Z']), RE * 0.9)
_c1 = mixc(_en, _lm, (0.02, 0.08, 0.3), _lc); _c1 = mixc(_en, _ice, _c1, (0.85, 0.88, 0.92))
_en.links.new(_c1, _eb.inputs['Base Color']); _en.links.new(math_(_en, 'MULTIPLY_ADD', _lm, 0.6, 0.25), _eb.inputs['Roughness'])
EARTH = earth_shell('earth', RE, EARTH_M)
CLOUD_M = mat('clouds', (1, 1, 1), 0.9, alpha=1.0); _cn = CLOUD_M.node_tree; CLOUD_M.blend_method = 'BLEND'
_cn.links.new(math_(_cn, 'MULTIPLY', math_(_cn, 'GREATER_THAN', tnoise(_cn, coord(_cn), 0.6, 6, 1.0), 0.6), 0.85), _cn.nodes['Principled BSDF'].inputs['Alpha'])
CLOUDS = earth_shell('clouds', RE * 1.012, CLOUD_M)
# the two cut faces, colored by depth: crust, mantle (red to orange), outer core (orange), inner core (yellow-white)
CUT_M = mat('cut', (0.5, 0.2, 0.1), 0.8); _un = CUT_M.node_tree; _ub = _un.nodes['Principled BSDF']
_len = nt_ = None
_vl = _un.nodes.new('ShaderNodeVectorMath'); _vl.operation = 'LENGTH'; _un.links.new(coord(_un), _vl.inputs[0])
_rr = math_(_un, 'DIVIDE', _vl.outputs['Value'], RE)
_rr = math_(_un, 'ADD', _rr, math_(_un, 'MULTIPLY', tnoise(_un, coord(_un), 1.6, 4), 0.012))
CUT_STOPS = [(0.0, (1.0, 0.95, 0.75)), (0.185, (1.0, 0.85, 0.45)), (0.195, (1.0, 0.55, 0.12)), (0.54, (0.95, 0.38, 0.06)),
             (0.552, (0.75, 0.16, 0.04)), (0.97, (0.38, 0.06, 0.03)), (0.982, (0.33, 0.24, 0.17)), (1.0, (0.3, 0.22, 0.15))]
_cc = ramp(_un, _rr, CUT_STOPS); _un.links.new(_cc, _ub.inputs['Base Color']); _un.links.new(_cc, _ub.inputs['Emission Color'])
_es = ramp(_un, _rr, [(0.0, (0.75, 0.75, 0.75)), (0.19, (0.5, 0.5, 0.5)), (0.54, (0.35, 0.35, 0.35)), (0.56, (0.14, 0.14, 0.14)), (0.97, (0.06, 0.06, 0.06)), (0.98, (0.0, 0.0, 0.0))])
_sxe = sepz(_un, _es); _core_boost = objattr(_un, 'boost')
_un.links.new(math_(_un, 'MULTIPLY', _sxe.outputs['X'], math_(_un, 'ADD', 1.0, _core_boost)), _ub.inputs['Emission Strength'])
def half_disk(name, plane, nr=60, na=120):
    vs, fs = [], []
    for i in range(nr + 1):
        r_ = RE * i / nr
        for j in range(na + 1):
            al = math.pi * j / na; h_, z_ = r_ * math.sin(al), r_ * math.cos(al)
            vs.append((h_, 0, z_) if plane == 'xz' else (0, -h_, z_))
    for i in range(nr):
        for j in range(na): a0 = i * (na + 1) + j; fs.append((a0, a0 + 1, a0 + na + 2, a0 + na + 1))
    o = mesh(name, vs, fs, CUT_M, loc=CS, smooth_=False); o['boost'] = 0.0; return o
CUTS = [half_disk('cut_xz', 'xz'), half_disk('cut_yz', 'yz')]
ATM_M = bpy.data.materials.new('atm'); ATM_M.use_nodes = True; _an = ATM_M.node_tree; _an.nodes.remove(_an.nodes['Principled BSDF']); ATM_M.blend_method = 'BLEND'
_ae = _an.nodes.new('ShaderNodeEmission'); _ae.inputs['Color'].default_value = (0.35, 0.6, 1.0, 1); _ae.inputs['Strength'].default_value = 2.5
_at = _an.nodes.new('ShaderNodeBsdfTransparent'); _am = _an.nodes.new('ShaderNodeMixShader'); _lw = _an.nodes.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.25
_pw = math_(_an, 'POWER', _lw.outputs['Facing'], 3.0); _an.links.new(_pw, _am.inputs['Fac'])
_an.links.new(_at.outputs[0], _am.inputs[1]); _an.links.new(_ae.outputs[0], _am.inputs[2]); _an.links.new(_am.outputs[0], _an.nodes['Material Output'].inputs['Surface'])
ATM = earth_shell('atmosphere', RE * 1.035, ATM_M, nlon=120, nlat=60); ATM.visible_shadow = False
# the tunnel along the cut edge (x = y = 0): dark outside the core, the core part can melt shut
TUN_M = mat('tunnel', (0.02, 0.02, 0.025), 0.4, emit=(0.4, 0.75, 1.0), estr=0.6)
TUN_OUT = [tube('tun_top', [CS + Vector((0, 0, RE * 1.01)), CS + Vector((0, 0, RE * 0.546))], 0.07, TUN_M, seg=16),
           tube('tun_bot', [CS + Vector((0, 0, -RE * 0.546)), CS + Vector((0, 0, -RE * 1.01))], 0.07, TUN_M, seg=16)]
TUNI_M = mat('tunnel_core', (0.02, 0.02, 0.025), 0.4, emit=(1.0, 0.55, 0.15), estr=0.0); _ti = TUNI_M.node_tree
_ti.links.new(math_(_ti, 'MULTIPLY_ADD', objattr(_ti, 'heat'), 14.0, 0.0), _ti.nodes['Principled BSDF'].inputs['Emission Strength'])
_ti.links.new(mixc(_ti, objattr(_ti, 'heat'), (0.4, 0.75, 1.0), (1.0, 0.55, 0.15)), _ti.nodes['Principled BSDF'].inputs['Emission Color'])
TUN_IN = tube('tun_core', [CS + Vector((0, 0, RE * 0.546)), CS + Vector((0, 0, -RE * 0.546))], 0.07, TUNI_M, seg=16); TUN_IN['heat'] = 0.0
DOT = prim('uv_sphere', 'dot', emis('dot_m', (1.0, 0.2, 0.04), 7.0), loc=CS, segments=24, ring_count=12, radius=0.34)
TRAIL_M = bpy.data.materials.new('trail'); TRAIL_M.use_nodes = True; _tn = TRAIL_M.node_tree; _tn.nodes.remove(_tn.nodes['Principled BSDF']); TRAIL_M.blend_method = 'BLEND'
_te = _tn.nodes.new('ShaderNodeEmission'); _te.inputs['Color'].default_value = (1.0, 0.5, 0.15, 1); _te.inputs['Strength'].default_value = 3.0
_tt = _tn.nodes.new('ShaderNodeBsdfTransparent'); _tm = _tn.nodes.new('ShaderNodeMixShader')
_tz = sepz(_tn, coord(_tn, 'Generated')); _tn.links.new(math_(_tn, 'POWER', math_(_tn, 'SUBTRACT', 1.0, _tz.outputs['Z']), 2.0), _tm.inputs['Fac'])
_tn.links.new(_tt.outputs[0], _tm.inputs[1]); _tn.links.new(_te.outputs[0], _tm.inputs[2]); _tn.links.new(_tm.outputs[0], _tn.nodes['Material Output'].inputs['Surface'])
TRAIL = prim('cylinder', 'trail', TRAIL_M, loc=CS, radius=0.2, depth=1.0, vertices=16); TRAIL.visible_shadow = False
MELT = prim('ico_sphere', 'melt_glow', emis('melt_m', (1.0, 0.7, 0.3), 0.0), loc=CS, subdivisions=3, radius=RE * 0.56); MELT.hide_render = True
def earth_dot(m_):
    """the ball in the cutaway: m_ minutes into the trip (0 top .. 38 bottom .. 76 top), uniform-Earth shape for the drawing"""
    z = RE * math.cos(math.pi * m_ / TRIP_MIN); v = math.sin(math.pi * m_ / TRIP_MIN)
    DOT.location = CS + Vector((0, 0, z)); L_ = 3.2 * abs(v); dirn = 1 if (m_ % (2 * TRIP_MIN)) < TRIP_MIN else -1
    TRAIL.scale = (1, 1, max(L_, 1e-3)); TRAIL.location = CS + Vector((0, 0, z + dirn * L_ / 2)); TRAIL.rotation_euler = (0 if dirn > 0 else math.pi, 0, 0)
    TRAIL.hide_render = L_ < 0.05

# ================================================================ set 4: the far side, night (a dome of stars blocks the sun)
NS = Vector((20000, 0, 0))
NIGHT = bpy.data.materials.new('night'); NIGHT.use_nodes = True; _nn = NIGHT.node_tree; _nn.nodes.remove(_nn.nodes['Principled BSDF'])
_nz = sepz(_nn, coord(_nn, 'Generated'))
_nsky = ramp(_nn, _nz.outputs['Z'], [(0.5, (0.05, 0.07, 0.14)), (0.56, (0.018, 0.028, 0.07)), (1.0, (0.004, 0.006, 0.022))])
star_shader(_nn, _nsky, 140.0)
DOME = prim('uv_sphere', 'dome', NIGHT, loc=NS, segments=64, ring_count=32, radius=700)
MOON = prim('uv_sphere', 'moon', emis('moon_m', (0.95, 0.95, 0.9), 4.0), loc=NS + Vector((-250, 480, 300)), segments=32, ring_count=16, radius=18)
MOON.visible_shadow = False
MOONL = light_at('moonlight', 'AREA', NS + Vector((-120, 230, 150)), NS, 2.2e5, (0.62, 0.72, 1.0), 40)
SAND = noisy(mat('sand', (0.38, 0.33, 0.25), 0.95), 0.5, 0.35, 0.05)
_sn2 = SAND.node_tree; _sb2 = _sn2.nodes['Principled BSDF']; _bm2 = _sn2.nodes.new('ShaderNodeBump'); _bm2.inputs['Strength'].default_value = 0.4
_sn2.links.new(tnoise(_sn2, coord(_sn2), 9.0, 6), _bm2.inputs['Height']); _sn2.links.new(_bm2.outputs['Normal'], _sb2.inputs['Normal'])
GROUND_N = lathe('ground_n', [(HR + 0.78, -0.08), (6, 0.0), (80, 0.3), (720, 4.0)], 96, SAND, loc=NS)
COL_N = collar('collar_n', NS)
SHAFT_N, RINGS_N = shaft('shaft_n', NS, 120.0, 7.0, lamp_ring_mat('ringlamp_n'), rock_wall('rock_n', glow=False))
random.seed(9)
SCRUB = mat('scrub', (0.06, 0.09, 0.04), 0.9)
for k in range(70):
    a_ = random.uniform(0, 2 * math.pi); d_ = random.uniform(9, 160)
    prim('ico_sphere', f'bush_{k}', SCRUB, loc=NS + Vector((math.cos(a_) * d_, math.sin(a_) * d_, 0.2 + 0.0004 * d_ * d_ / 8)), subdivisions=2,
         radius=random.uniform(0.4, 1.4), scale=(1, 1, random.uniform(0.45, 0.8)))
for k in range(9):                                                 # rocks
    a_ = random.uniform(0, 2 * math.pi); d_ = random.uniform(5, 30)
    r_ = prim('ico_sphere', f'rock_{k}', noisy(mat('rk', (0.25, 0.23, 0.21), 0.9), 3.0, 0.3), loc=NS + Vector((math.cos(a_) * d_, math.sin(a_) * d_, 0.1)),
              subdivisions=2, radius=random.uniform(0.3, 0.9), scale=(1, 0.8, 0.5))

# ================================================================ the ball (moves between sets)
BALL = prim('uv_sphere', 'ball', BALL_M, segments=48, ring_count=24, radius=BALL_R); BALL.rotation_mode = 'XYZ'

# ================================================================ light for the day field: a clear midday-ish sun, sky gradient
SUNL = bpy.data.lights.new('sun', 'SUN'); SUNL.energy = 3.4; SUNL.color = (1.0, 0.95, 0.86); SUNL.angle = R(0.8)
SUN_O = bpy.data.objects.new('sun', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_mode = 'QUATERNION'
SUN_O.rotation_quaternion = (-Vector((-0.35, -0.55, 0.9))).to_track_quat('-Z', 'Y')
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Strength'].default_value = 1.0
_tc = wnt.nodes.new('ShaderNodeTexCoord'); _sx = wnt.nodes.new('ShaderNodeSeparateXYZ'); wnt.links.new(_tc.outputs['Generated'], _sx.inputs['Vector'])
SKYR = wnt.nodes.new('ShaderNodeValToRGB'); _el = SKYR.color_ramp.elements
_el[0].position = 0.0; _el[0].color = (0.4, 0.42, 0.4, 1); _el[1].position = 0.8; _el[1].color = (0.1, 0.28, 0.75, 1)
_e2 = _el.new(0.5); _e2.color = (0.8, 0.86, 0.94, 1); _e3 = _el.new(0.57); _e3.color = (0.42, 0.6, 0.92, 1)
_mr = wnt.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = -1.0; _mr.inputs['From Max'].default_value = 1.0
wnt.links.new(_sx.outputs['Z'], _mr.inputs['Value']); wnt.links.new(_mr.outputs['Result'], SKYR.inputs['Fac']); wnt.links.new(SKYR.outputs['Color'], WBG.inputs['Color'])
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.02; CAM.data.clip_end = 9000
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5
def look(cp, ct, lens=35, fstop=8.0, focus=None, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    if up is None: q = d.to_track_quat('-Z', 'Y')
    else:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
