# ================================================================ effects
POT_Z0 = FRY['pot_z']; PR_ = FRY['pr']; PH_ = FRY['ph']; FX, FY = FRY['at'].x, FRY['at'].y
FLOOR_Z = POT_Z0 + 0.006; RIM_Z = POT_Z0 + PH_
OIL0 = POT_Z0 + 0.20                              # oil level before the turkey goes in

# ---- volume puffs (steam white, smoke dark): density from a noise ball; object props dens + ph
def puff_mat(name, col, dark=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (*col, 1)
    co = coord(nt, 'Object'); ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(co, ln.inputs[0])
    fall = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, ln.outputs['Value']), 0.0)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 5.0
    nt.links.new(co, nz.inputs['Vector']); nt.links.new(objattr(nt, 'ph'), nz.inputs['W'])
    d_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', fall, 0.8), math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.32), 0.0)), objattr(nt, 'dens'))
    nt.links.new(math_(nt, 'MULTIPLY', d_, 60.0 if not dark else 40.0), pv.inputs['Density'])
    if dark: pv.inputs['Anisotropy'].default_value = 0.1
    else: pv.inputs['Anisotropy'].default_value = 0.35
    nt.links.new(pv.outputs[0], out.inputs['Volume']); return m
STEAM_M = puff_mat('steam', (0.92, 0.93, 0.95)); SMOKE_M = puff_mat('smoke', (0.05, 0.045, 0.045), True)
class Puffs:
    def __init__(s, name, m, n, seed):
        s.o = []; s.n = n; s.r = random.Random(seed)
        for k in range(n):
            o = prim('ico_sphere', f'{name}{k}', m, scale=(1, 1, 1), subdivisions=2, radius=1.0); o.hide_render = True; o['dens'] = 0.0; o['ph'] = h1(k + seed) * 10; s.o.append(o)
        s.p = [(s.r.random(), s.r.random(), s.r.random(), s.r.random()) for _ in range(n)]
    def update(s, t, src, t0, t1, life, rise, size, spread, dens=1.0, drift=(0, 0, 0)):
        """emit from src(k, u) between t0 and t1, each puff lives `life` s, rises `rise` m/s, grows to `size`"""
        for k, o in enumerate(s.o):
            u0, u1, u2, u3 = s.p[k]; te = t0 + (t1 - t0) * (k + u0 * 0.7) / s.n; age = t - te
            if t1 <= t0 or age < 0 or age > life: o.hide_render = True; continue
            a_ = age / life; o.hide_render = False
            base = Vector(src(k, u1)); o.location = base + Vector(((u2 - 0.5) * spread * a_, (u3 - 0.5) * spread * a_, rise * age)) + Vector(drift) * age
            sc = size * (0.25 + 0.75 * math.sqrt(a_)) * (0.7 + 0.6 * u1); o.scale = (sc, sc, sc * 1.15)
            o['dens'] = dens * smooth(0, 0.15, a_) * (1 - smooth(0.45, 1.0, a_)); o['ph'] = u0 * 10 + age * 0.6

# ---- flame cards: emission over clear, a licking tongue shape from noise; object props amt (0..1), ph, seed
def flame_card_mat(name, strength=7.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    uv = coord(nt, 'Generated'); sx = sepz(nt, uv); x_ = sx.outputs['X']; y_ = sx.outputs['Y']
    cx = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', x_, 0.5))
    width = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, y_), 0.5)                 # narrows to the top
    body = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', cx, math_(nt, 'MAXIMUM', width, 0.02))), 0.0)
    cm = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', x_, 3.0), cm.inputs['X'])
    nt.links.new(math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', y_, 2.2), math_(nt, 'MULTIPLY', objattr(nt, 'ph'), 2.6)), cm.inputs['Y']); nt.links.new(objattr(nt, 'seed'), cm.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.4; nz.inputs['Detail'].default_value = 6.0; nz.inputs['Distortion'].default_value = 0.6
    nt.links.new(cm.outputs[0], nz.inputs['Vector'])
    hmask = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', objattr(nt, 'amt'), y_), 0.0)
    f_ = math_(nt, 'MULTIPLY', math_(nt, 'ADD', math_(nt, 'MULTIPLY', body, 0.55), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.4), 1.6)), math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', hmask, 6.0), 1.0))
    a_ = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', f_, 0.46), 3.2), 0.0), 1.0)
    col = ramp(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', a_, 0.7), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, y_), 0.3)),
               [(0.0, (0.55, 0.05, 0.0)), (0.35, (1.0, 0.28, 0.02)), (0.7, (1.0, 0.62, 0.12)), (1.0, (1.0, 0.92, 0.6))])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(col, em.inputs['Color']); nt.links.new(math_(nt, 'MULTIPLY', a_, strength), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(a_, mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    try: m.cycles.emission_sampling = 'NONE'
    except Exception: pass
    return m
FLAME_M = flame_card_mat('flame', 2.4)
def card(name, base, h, w, yaw, parent=None):
    o = prim('plane', name, FLAME_M, parent, size=1.0)
    for v in o.data.vertices: v.co = Vector(((v.co.x) * w, 0.0, (v.co.y + 0.5) * h))
    o.location = base; o.rotation_euler = (0, 0, yaw); o['amt'] = 0.0; o['ph'] = 0.0; o['seed'] = random.random() * 20; o.hide_render = True
    return o

# ---- the fire volume (fireball): emission + smoke from a stretched noise ball; object props fire, ph
def fire_vol_mat(name, es=220.0, thr=0.44, dens=55.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (0.03, 0.025, 0.02, 1)
    co = coord(nt, 'Object'); sx = sepz(nt, co)
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(co, ln.inputs[0])
    fall = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, ln.outputs['Value']), 0.0), 1.6)
    rise = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sx.outputs['X'], rise.inputs['X']); nt.links.new(sx.outputs['Y'], rise.inputs['Y'])
    nt.links.new(math_(nt, 'SUBTRACT', sx.outputs['Z'], math_(nt, 'MULTIPLY', objattr(nt, 'ph'), 1.4)), rise.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.4; nz.inputs['Detail'].default_value = 8.0; nz.inputs['Distortion'].default_value = 1.0
    nt.links.new(rise.outputs[0], nz.inputs['Vector'])
    d_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', fall, math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], thr), 0.0)), objattr(nt, 'fire'))
    nt.links.new(math_(nt, 'MULTIPLY', d_, dens), pv.inputs['Density'])
    hot = math_(nt, 'MULTIPLY', math_(nt, 'POWER', fall, 0.5), math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], thr - 0.02), 0.0))
    hot = math_(nt, 'MULTIPLY', hot, math_(nt, 'SUBTRACT', 1.15, math_(nt, 'MULTIPLY', math_(nt, 'ADD', sx.outputs['Z'], 1.0), 0.45)))
    col = ramp(nt, math_(nt, 'MULTIPLY', hot, 5.0), [(0.0, (0.35, 0.06, 0.0)), (0.3, (1.0, 0.30, 0.02)), (0.6, (1.0, 0.52, 0.06)), (0.85, (1.0, 0.70, 0.18)), (1.0, (1.0, 0.86, 0.45))])
    nt.links.new(col, pv.inputs['Emission Color']); nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', hot, objattr(nt, 'fire')), es), pv.inputs['Emission Strength'])
    nt.links.new(pv.outputs[0], out.inputs['Volume']); return m
FIREVOL_M = fire_vol_mat('firevol', 330.0, 0.5, 40.0)
def fire_sleeve_mat(name):
    """fire hugging the pot: a ring-shaped density round its side, cut off above the flame front (object prop front, local z)"""
    m = fire_vol_mat(name); nt = m.node_tree; pv = next(n for n in nt.nodes if n.type == 'PRINCIPLED_VOLUME')
    co = coord(nt, 'Object'); sx = sepz(nt, co); rr = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', sx.outputs['X'], sx.outputs['X']), math_(nt, 'MULTIPLY', sx.outputs['Y'], sx.outputs['Y'])))
    ring = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', rr, 0.62)), 3.2)), 0.0)
    hm = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', objattr(nt, 'front'), sx.outputs['Z']), 3.0), 0.0), 1.0)
    lk = next(l for l in nt.links if l.to_socket == pv.inputs['Density']); src = lk.from_socket; nt.links.remove(lk)
    nt.links.new(math_(nt, 'MULTIPLY', src, math_(nt, 'MULTIPLY', ring, hm)), pv.inputs['Density'])
    lk = next(l for l in nt.links if l.to_socket == pv.inputs['Emission Strength']); src = lk.from_socket; nt.links.remove(lk)
    nt.links.new(math_(nt, 'MULTIPLY', src, math_(nt, 'MULTIPLY', ring, hm)), pv.inputs['Emission Strength'])
    return m
SLEEVE = prim('cylinder', 'fire_sleeve', fire_sleeve_mat('firesleeve'), loc=(0, 0, 0), vertices=48, radius=1.0, depth=2.0)
SLEEVE.location = (0.0, 1.05, DECK_Z + 0.55); SLEEVE.scale = (0.34, 0.34, 0.55); SLEEVE['fire'] = 0.0; SLEEVE['ph'] = 0.0; SLEEVE['front'] = -1.0; SLEEVE.hide_render = True
FIREBALLS = []
for k in range(4):
    o = prim('ico_sphere', f'fireball{k}', FIREVOL_M, subdivisions=3, radius=1.0); o.hide_render = True; o['fire'] = 0.0; o['ph'] = 0.0; FIREBALLS.append(o)

# ---- steam: the flash at the skin, wisps off hot oil; smoke from the roof
STEAM_FLASH = Puffs('stflash', STEAM_M, 18, 3)
STEAM_SURGE = Puffs('stsurge', STEAM_M, 14, 5)
SMOKE = Puffs('smoke', SMOKE_M, 16, 7)
# ---- melt water: drops that run out of the bottom of the bird and sink; the hero drop blows up into a bubble 12x wide (1,700x the space)
DROPS = []
dr = random.Random(11)
for k in range(16):
    o = prim('uv_sphere', f'drop{k}', WATER_M, segments=16, ring_count=10, radius=1.0); o.hide_render = True
    ang = -1.75 + dr.uniform(-1.3, 1.3); rr = dr.uniform(0.128, 0.148)
    DROPS.append(dict(o=o, ang=ang, rr=rr, t0=T_DRIP + 0.25 * k + dr.uniform(0, 0.2), r=dr.uniform(0.0045, 0.0075), wob=dr.uniform(0, 6.28)))
HERO = DROPS[2]; HERO['rr'] = 0.112; HERO['ang'] = -1.75; HERO['r'] = 0.0045
BUBBLES = []
for k in range(40):
    o = prim('uv_sphere', f'bub{k}', STEAMB_M, segments=16, ring_count=10, radius=1.0); o.hide_render = True
    BUBBLES.append(dict(o=o, ang=dr.uniform(0, 6.28), rr=dr.uniform(0.0, 0.15), t0=T_SURGE - 0.2 + dr.uniform(0, 1.6), r=dr.uniform(0.012, 0.035), v=dr.uniform(0.35, 0.7)))
# surface bubbles on the oil (fizz) round the turkey
FIZZ = []
OILB_M = mat('oilbub', (1.0, 0.75, 0.3), 0.05, trans=0.5, ior=1.4)
for k in range(70):
    o = prim('uv_sphere', f'fizz{k}', OILB_M, segments=10, ring_count=6, radius=1.0); o.hide_render = True
    FIZZ.append(dict(o=o, ang=dr.uniform(0, 6.28), rr=dr.uniform(0.08, 0.16), ph=dr.uniform(0, 1), sp=dr.uniform(1.5, 3.5), r=dr.uniform(0.003, 0.009)))
# ---- the boil-over: foam dome over the pot, a sheet of oil running down the outside, streams onto the burner
FOAM_M = mat('foam', (0.98, 0.82, 0.48), 0.25, trans=0.25, ior=1.4, emit=(1.0, 0.6, 0.2), estr=0.05)
nt = FOAM_M.node_tree; vb = nt.nodes.new('ShaderNodeTexVoronoi'); vb.inputs['Scale'].default_value = 90.0; vb.voronoi_dimensions = '4D'
nt.links.new(coord(nt, 'Object'), vb.inputs['Vector']); nt.links.new(objattr(nt, 'ph'), vb.inputs['W'])
bpn = nt.nodes.new('ShaderNodeBump'); bpn.inputs['Strength'].default_value = 0.8; nt.links.new(vb.outputs['Distance'], bpn.inputs['Height']); nt.links.new(bpn.outputs['Normal'], nt.nodes['Principled BSDF'].inputs['Normal'])
FOAM = prim('uv_sphere', 'foam', FOAM_M, segments=48, ring_count=24, radius=1.0)
for v in FOAM.data.vertices:
    if v.co.z < 0: v.co.z = 0.0
dpf = FOAM.modifiers.new('d', 'DISPLACE'); txf = bpy.data.textures.new('foamtx', 'CLOUDS'); txf.noise_scale = 0.25; dpf.texture = txf; dpf.strength = 0.18; dpf.texture_coords = 'OBJECT'
FOAM.hide_render = True; FOAM['ph'] = 0.0
SHEET_M = oil_mat('sheet', 0.0); SHEET_M.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.12
_nt = SHEET_M.node_tree; _gp0 = _nt.nodes.new('ShaderNodeNewGeometry').outputs['Position']
_vs = _nt.nodes.new('ShaderNodeVectorMath'); _vs.operation = 'SUBTRACT'; _nt.links.new(_gp0, _vs.inputs[0]); _vs.inputs[1].default_value = (0.0, 1.05, 0.0); _sx = sepz(_nt, _vs.outputs[0])
_ang = _nt.nodes.new('ShaderNodeMath'); _ang.operation = 'ARCTAN2'; _nt.links.new(_sx.outputs['Y'], _ang.inputs[0]); _nt.links.new(_sx.outputs['X'], _ang.inputs[1])
_cm = _nt.nodes.new('ShaderNodeCombineXYZ'); _nt.links.new(math_(_nt, 'MULTIPLY', _ang.outputs[0], 2.2), _cm.inputs['X']); _nt.links.new(math_(_nt, 'MULTIPLY', _sx.outputs['Z'], 0.35), _cm.inputs['Y'])
_st = tnoise(_nt, _cm.outputs[0], 2.5, 2.0); _al = math_(_nt, 'MINIMUM', math_(_nt, 'MAXIMUM', math_(_nt, 'MULTIPLY', math_(_nt, 'SUBTRACT', _st, 0.55), 9.0), 0.0), 1.0)
_tr = _nt.nodes.new('ShaderNodeBsdfTransparent'); _mx = _nt.nodes.new('ShaderNodeMixShader'); _nt.links.new(_al, _mx.inputs['Fac'])
_nt.links.new(_tr.outputs[0], _mx.inputs[1]); _nt.links.new(_nt.nodes['Principled BSDF'].outputs[0], _mx.inputs[2]); _nt.links.new(_mx.outputs[0], _nt.nodes['Material Output'].inputs['Surface'])
def sheet_mesh():
    segs, rows = 96, 24; vs = []; fs = []
    for i in range(rows + 1):
        for k in range(segs):
            a_ = 2 * math.pi * k / segs; vs.append((math.cos(a_), math.sin(a_), -i / rows))
    for i in range(rows):
        for k in range(segs): k2 = (k + 1) % segs; fs.append((i * segs + k, i * segs + k2, (i + 1) * segs + k2, (i + 1) * segs + k))
    return mesh('oilsheet', vs, fs, SHEET_M)
SHEET = sheet_mesh(); SHEET.hide_render = True
# rivulets: oil running down the outside of the pot in wiggly streams (rebuilt each frame to their current length)
RIV_M = oil_mat('rivulet', 0.05); RIV_M.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.08
RIVS = []
for k in range(11):
    a0 = -2.7 + 2.6 * (k / 10) + 0.15 * h1(k); RIVS.append(dict(a=a0, w=h1(k + 30), sp=0.75 + 0.45 * h1(k + 31), r=0.0035 + 0.004 * h1(k + 32), o=mesh(f'riv{k}', [(0, 0, 0)] * 3, [(0, 1, 2)], RIV_M)))
for rv in RIVS: rv['o'].hide_render = True
def set_tube(o, pts, r, seg=8):
    pts = [Vector(p) for p in pts]; n = len(pts)
    if n < 2: o.hide_render = True; return
    rings = []; T0 = (pts[1] - pts[0]).normalized(); up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized()
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        rr = r(i / (n - 1)) if callable(r) else r
        rings.append([pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
    vs = [tuple(p) for ring in rings for p in ring]; fs = []
    for i in range(n - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    me = o.data; me.clear_geometry(); me.from_pydata(vs, [], fs); me.update()
    for p in me.polygons: p.use_smooth = True
    o.hide_render = False
SHEET_BASE = [Vector(v.co) for v in SHEET.data.vertices]
STREAMS = []
for k in range(7):
    a_ = -1.4 + 0.45 * k + 0.2 * h1(k); STREAMS.append(dict(a=a_, o=None, t0=T_POUR + 0.15 * k + 0.2 * h1(k + 5)))
# ---- fire: cards up the outside of the pot (racing up the oil), cards over the top, a ring on the roof, the fireball volumes, lights
POT_CARDS = []
for k in range(18):
    a_ = 2 * math.pi * k / 18; base = Vector((FX + (PR_ + 0.02) * math.cos(a_), FY + (PR_ + 0.02) * math.sin(a_), DECK_Z + 0.15))
    POT_CARDS.append(card(f'pcard{k}', base, 0.75, 0.24, a_ + math.pi / 2))
TOP_CARDS = []
for k in range(14):
    a_ = math.pi * k / 14; r_ = 0.06 * h1(k)
    TOP_CARDS.append(card(f'tcard{k}', Vector((FX + r_ * math.cos(a_ * 2), FY + r_ * math.sin(a_ * 2), RIM_Z - 0.05)), 1.6, 0.7, a_))
ROOF_CARDS = []
for k in range(24):
    x_ = FX - 1.6 + 3.2 * (k / 23) + 0.1 * h1(k); y_ = FY - 0.9 + 1.6 * h1(k + 3)
    zr = ROOF_Z1 + (ROOF_Z0 - ROOF_Z1) * (y_ - DY0) / (WALL_Y - DY0) + 0.2
    c_ = card(f'rcard{k}', Vector((x_, y_, zr - 0.32)), 0.55, 0.5, h1(k + 8) * 3.14); ROOF_CARDS.append((c_, math.hypot(x_ - FX, y_ - FY)))
FIRE_L = [light_at(f'fire_l{k}', 'POINT', (FX, FY, RIM_Z + 0.3 + 0.5 * k), (FX, FY, 0), 0.0, (1.0, 0.45, 0.12), 0.35) for k in range(3)]
# roof underside burn: char + embers growing out from above the pot
nt = ceil_m.node_tree; bb = nt.nodes['Principled BSDF']
lk = next((l for l in nt.links if l.to_socket == bb.inputs['Base Color']), None); src = lk.from_socket if lk else None
gpos = nt.nodes.new('ShaderNodeNewGeometry').outputs['Position']
dv = nt.nodes.new('ShaderNodeVectorMath'); dv.operation = 'DISTANCE'; nt.links.new(gpos, dv.inputs[0]); dv.inputs[1].default_value = (FX, FY, ROOF_Z1 + 0.3)
burnr = objattr(nt, 'burnr')
ch = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', math_(nt, 'ADD', burnr, math_(nt, 'MULTIPLY', tnoise(nt, gpos, 3.0), 0.5)), dv.outputs['Value']), 3.0), 0.0), 1.0)
basec = src if src else (0.78, 0.76, 0.70)
nt.links.new(mixc(nt, ch, basec, (0.02, 0.015, 0.012)), bb.inputs['Base Color'])
emb = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', ch, math_(nt, 'POWER', tnoise(nt, gpos, 40.0, 3.0), 4.0)), objattr(nt, 'glow'))
bb.inputs['Emission Color'].default_value = (1.0, 0.3, 0.04, 1); nt.links.new(math_(nt, 'MULTIPLY', emb, 60.0), bb.inputs['Emission Strength'])
ROOF_UNDER['burnr'] = 0.0; ROOF_UNDER['glow'] = 0.0
for rf in RAFTERS: rf.data.materials.clear(); rf.data.materials.append(ceil_m); rf['burnr'] = 0.0; rf['glow'] = 0.0
