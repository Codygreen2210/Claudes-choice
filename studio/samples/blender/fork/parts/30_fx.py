
# ================================================================ on the turntable: a plate of leftover pasta, the fork and a spoon, a takeout box
# All built to real size. Everything on the turntable is parented to TT so it turns with it (3 turns a minute).
CERAMIC = mat('ceramic', (0.05, 0.22, 0.30), 0.10, coat=1.0)                # a deep teal plate: the silver fork pops on it
PLATE_C = Vector((0.03, 0.0, 0.0))
PLATE = lathe('plate', [(0.0, 0.0205), (0.06, 0.0205), (0.068, 0.022), (0.088, 0.031), (0.095, 0.0325), (0.096, 0.031), (0.086, 0.0265), (0.066, 0.0225),
                        (0.058, 0.0215), (0.0, 0.0215)], 64, CERAMIC, TT)
PLATE.location = PLATE_C
for p_ in PLATE.data.polygons: p_.use_smooth = True
# leftover mac and cheese: ~170 little curved macaroni on a low mound; 'heat' makes it glow warm (the food soaking up the waves)
def food_mat():
    m = mat('mac', (0.95, 0.68, 0.20), 0.32, coat=0.6); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    v = tnoise(nt, coord(nt, 'Object'), 60.0, 3.0); nt.links.new(mixc(nt, v, (0.78, 0.30, 0.02), (0.96, 0.52, 0.05)), b.inputs['Base Color'])
    b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (1.0, 0.6, 0.2); b.inputs['Subsurface Scale'].default_value = 0.002
    nt.links.new(objattr(nt, 'heat_col'), b.inputs['Emission Color']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'heat'), 2.5), b.inputs['Emission Strength']); return m
FOOD_M = food_mat()
FOOD = prim('uv_sphere', 'food', FOOD_M, TT, loc=(PLATE_C.x + 0.005, PLATE_C.y + 0.035, 0.0215), scale=(0.034, 0.028, 0.011), segments=32, ring_count=16)
for v in FOOD.data.vertices:
    if v.co.z < 0: v.co.z *= 0.05
FOOD['heat'] = 0.0; FOOD['heat_col'] = (1.0, 0.45, 0.12, 1.0)
for p_ in FOOD.data.polygons: p_.use_smooth = True
_mb = bmesh.new(); _rr = random.Random(9)
for i_ in range(170):
    a_ = _rr.uniform(0, 2 * math.pi); r_ = 0.034 * math.sqrt(_rr.random()); x_ = r_ * math.cos(a_); y_ = r_ * math.sin(a_) * 0.82
    zt = 0.011 * max(0.0, 1 - (x_ / 0.034) ** 2 - (y_ / 0.028) ** 2) ** 0.5 + _rr.uniform(0.0, 0.004)
    ring = bmesh.ops.create_circle(_mb, cap_ends=False, segments=8, radius=0.0019)['verts']; pts = []
    for k in range(6):                                                           # a bent tube: 6 rings round a 100-degree arc
        th = math.radians(-50 + 20 * k); c_ = Vector((0.006 * math.sin(th), 0.006 * (1 - math.cos(th)), 0)); pts.append((c_, th))
    rings = []
    for c_, th in pts:
        vs = [_mb.verts.new(c_ + Matrix.Rotation(th, 3, 'Z') @ Vector((0, v.co.x, v.co.y))) for v in ring]; rings.append(vs)
    bmesh.ops.delete(_mb, geom=ring, context='VERTS')
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(8): _mb.faces.new((r0[k], r0[(k + 1) % 8], r1[(k + 1) % 8], r1[k]))
    M = Matrix.Translation((PLATE_C.x + 0.005 + x_, PLATE_C.y + 0.035 + y_, 0.0215 + zt)) @ Euler((_rr.uniform(-0.6, 0.6), _rr.uniform(-0.6, 0.6), _rr.uniform(0, 6.3))).to_matrix().to_4x4()
    bmesh.ops.transform(_mb, matrix=M, verts=[v for r in rings for v in r])
_mm = bpy.data.meshes.new('macaroni'); _mb.to_mesh(_mm); _mb.free(); MAC = obj('macaroni', _mm, FOOD_M, parent=TT)
for p_ in _mm.polygons: p_.use_smooth = True
MAC['heat'] = 0.0; MAC['heat_col'] = (1.0, 0.45, 0.12, 1.0)
# ---- the fork: stainless, 19 cm, four pointed tines; local x runs from the handle end (0) to the tine tips (0.19)
FORK_M = mat('stainless', (0.80, 0.80, 0.82), 0.16, 1.0, coat=0.2)
def flat_shape(name, outline, th, m, parent, loc=(0, 0, 0)):
    bm = bmesh.new(); vs = [bm.verts.new((x, y, 0.0)) for x, y in outline]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, th), verts=[e for e in ex['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj(name, me, m, loc=loc, parent=parent); md = o.modifiers.new('bv', 'BEVEL'); md.width = th * 0.45; md.segments = 3; md.limit_method = 'ANGLE'
    o.modifiers.new('wn', 'WEIGHTED_NORMAL')
    for p_ in me.polygons: p_.use_smooth = True
    return o
FORK = empty('fork', TT, loc=(0.173, -0.045, 0.0369)); FORK.rotation_euler = (0, R(4.9), R(172))        # handle resting on the rim, tines lying on the flat of the plate
_h = [(0.0, 0.0105), (0.012, 0.0118), (0.05, 0.0095), (0.098, 0.0042), (0.118, 0.0036), (0.135, 0.0062), (0.148, 0.0118), (0.152, 0.0122)]
FORK_BODY = flat_shape('fork_body', [(x, y) for x, y in _h] + [(x, -y) for x, y in reversed(_h)], 0.0024, FORK_M, FORK)
TINE_TIPS = []
for k_ in range(4):
    yc = -0.0092 + 0.00613 * k_; w = 0.0021
    o = flat_shape(f'tine{k_}', [(0.150, yc - w), (0.182, yc - w * 0.9), (0.190, yc), (0.182, yc + w * 0.9), (0.150, yc + w)], 0.0022, FORK_M, FORK)
    TINE_TIPS.append(Vector((0.1895, yc, 0.0011)))
# ---- the spoon: smooth, no points (an oval bowl and a round-ended handle), lying beside the fork
SPOON = empty('spoon', TT, loc=(0.13, 0.055, 0.0345)); SPOON.rotation_euler = (0, R(2.0), R(176))
_sh = [(0.0, 0.006), (0.01, 0.0095), (0.06, 0.0085), (0.105, 0.0035), (0.12, 0.004)]
flat_shape('spoon_handle', [(x, y) for x, y in _sh] + [(x, -y) for x, y in reversed(_sh)], 0.0022, FORK_M, SPOON)
SB = prim('uv_sphere', 'spoon_bowl', FORK_M, SPOON, loc=(0.145, 0, 0.004), scale=(0.028, 0.019, 0.0065), segments=40, ring_count=20)
for v in SB.data.vertices:
    if v.co.z > 0.25: v.co.z = 0.25 - (v.co.z - 0.25) * 0.35                     # dished in on top: a real spoon bowl, smooth all round
# ---- the takeout box: white folded paperboard, wider at the top, with a thin wire handle stapled through its sides
PAPER_M = mat('paper', (0.92, 0.91, 0.87), 0.85)
_pn = PAPER_M.node_tree; _pz = sepz(_pn, coord(_pn, 'Object')).outputs['Z']
_band = math_(_pn, 'MULTIPLY', math_(_pn, 'GREATER_THAN', _pz, 0.028), math_(_pn, 'LESS_THAN', _pz, 0.046))
_pn.links.new(mixc(_pn, _band, (0.92, 0.91, 0.87), (0.72, 0.06, 0.05)), _pn.nodes['Principled BSDF'].inputs['Base Color'])
CARTON = empty('carton', TT, loc=(-0.098, 0.055, 0.02)); CARTON.rotation_euler = (0, 0, R(25))
_bm = bmesh.new()
bot = [(-0.026, -0.022), (0.026, -0.022), (0.026, 0.022), (-0.026, 0.022)]; top = [(-0.036, -0.03), (0.036, -0.03), (0.036, 0.03), (-0.036, 0.03)]
vb = [_bm.verts.new((x, y, 0.0)) for x, y in bot]; vt = [_bm.verts.new((x, y, 0.075)) for x, y in top]
_bm.faces.new(vb[::-1])
for i_ in range(4): _bm.faces.new((vb[i_], vb[(i_ + 1) % 4], vt[(i_ + 1) % 4], vt[i_]))
for sy in (-1, 1):                                                               # the folded top flaps (closed into a peak)
    a_ = _bm.verts.new((-0.036, sy * 0.03, 0.075)); b_ = _bm.verts.new((0.036, sy * 0.03, 0.075)); c_ = _bm.verts.new((0.036, sy * 0.004, 0.098)); d_ = _bm.verts.new((-0.036, sy * 0.004, 0.098))
    _bm.faces.new((a_, b_, c_, d_))
_me = bpy.data.meshes.new('carton'); _bm.to_mesh(_me); _bm.free(); CART = obj('carton_body', _me, PAPER_M, parent=CARTON)
sol = CART.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.0012
WIRE_M = mat('wire', (0.7, 0.7, 0.72), 0.25, 1.0)
WIRE_ENDS = [Vector((-0.0335, 0.0, 0.065)), Vector((0.0335, 0.0, 0.065))]
tube('carton_wire', [Vector((-0.0345, 0.0, 0.065)), Vector((-0.03, 0.0, 0.11)), Vector((0.0, 0.0, 0.135)), Vector((0.03, 0.0, 0.11)), Vector((0.0345, 0.0, 0.065))], 0.0009, WIRE_M, CARTON, seg=8)
# ---- the flame on the box (crossed sheets with a moving noise mask) and its light
def flame_mat():
    m = bpy.data.materials.new('flame'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    p = sepz(nt, coord(nt, 'Generated')); u = math_(nt, 'SUBTRACT', p.outputs['X'], 0.5); v = p.outputs['Y']          # the plane stands up: Y runs base to tip
    vec = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'MULTIPLY', p.outputs['X'], 3.0), vec.inputs['X'])
    nt.links.new(math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', v, 2.0), math_(nt, 'MULTIPLY', objattr(nt, 'ft'), 3.5)), vec.inputs['Y']); nt.links.new(objattr(nt, 'ft'), vec.inputs['Z'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4.0; nt.links.new(vec.outputs[0], nz.inputs['Vector'])
    width = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, v), 0.42)
    edge = math_(nt, 'SUBTRACT', width, math_(nt, 'ADD', math_(nt, 'ABSOLUTE', u), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.5), 0.5)))
    shape = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', edge, 0.07), 0.0), 1.0)          # soft edges, not a cut-out
    k = math_(nt, 'MULTIPLY', shape, objattr(nt, 'fa'))
    col = ramp(nt, v, [(0.0, (1.0, 0.75, 0.25)), (0.35, (1.0, 0.38, 0.04)), (1.0, (0.7, 0.06, 0.01))])
    e_ = nt.nodes.new('ShaderNodeEmission'); nt.links.new(col, e_.inputs['Color']); e_.inputs['Strength'].default_value = 4.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', k, 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
FLAME_M = flame_mat(); FLAMES = []
for k_ in range(3):
    f = prim('plane', f'flame{k_}', FLAME_M, CARTON, loc=(0.036, -0.012 + 0.012 * k_, 0.07), rot=(R(90), 0, R(90 + 55 * k_ - 55)), scale=(0.024, 0.045, 1), size=1)
    bpy.context.view_layer.update(); f.data.transform(Matrix.Translation((0, 0.0225, 0))); f['ft'] = 0.0; f['fa'] = 0.0; f.hide_render = True; FLAMES.append(f)   # base at the origin (scale already applied)
FIRE_LT = light_at('fire_lt', 'POINT', (0, 0, 0), (0, 0, 0), 0.0, (1.0, 0.55, 0.2), 0.006); FIRE_LT.parent = CARTON; FIRE_LT.location = (0.04, 0.0, 0.09)

# ================================================================ the physics shown: waves bouncing off the walls, charges sloshing, the spark
# ---- waves: a glass "slice" through the cavity shows the wave crests spreading out of the waveguide and bouncing off every wall.
# Each wall is a mirror, so the bounces are rings from mirror-image sources (reflected across the walls); a ring exists only where
# the front has had time to arrive, so the first ring travels out, then its reflections appear one by one. Strength: 'wv'.
def wave_mat():
    m = bpy.data.materials.new('waves'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    g = nt.nodes.new('ShaderNodeNewGeometry'); p = sepz(nt, g.outputs['Position']); X, Z = p.outputs['X'], p.outputs['Z']
    sx, sz = CX1, 0.19; t_ = objattr(nt, 'wt'); c_ = 0.09; lam = 0.03
    xs = [sx, 2 * CX0 - sx, 2 * CX1 - (2 * CX0 - sx)]; zs = [sz, 2 * CZ0 - sz, 2 * CZ1 - sz]
    tot = None
    for ix, x0 in enumerate(xs):
        for iz, z0 in enumerate(zs):
            dx = math_(nt, 'SUBTRACT', X, x0); dz = math_(nt, 'SUBTRACT', Z, z0)
            d = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dz, dz)))
            front = math_(nt, 'LESS_THAN', d, math_(nt, 'MULTIPLY', t_, c_))
            ph = math_(nt, 'FRACT', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', d, math_(nt, 'MULTIPLY', t_, c_)), lam))
            crest = math_(nt, 'POWER', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', ph, 2.0), 1.0)), 14.0)
            amp = 1.0 / (1 + 1.6 * (ix + iz))
            term = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', crest, front), amp)
            tot = term if tot is None else math_(nt, 'ADD', tot, term)
    k = math_(nt, 'MULTIPLY', math_(nt, 'MINIMUM', tot, 1.0), objattr(nt, 'wv'))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (0.25, 0.65, 1.0, 1); e_.inputs['Strength'].default_value = 5.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(k, mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
WAVES = box('waves', (CX1 - CX0 - 0.004, 0.0005, CZ1 - CZ0 - 0.004), ((CX0 + CX1) / 2, CY0 + 0.012, (CZ0 + CZ1) / 2), wave_mat())     # just inside the door; WAVES['wv'] = 0.0; WAVES['wt'] = 0.0
WAVES.visible_shadow = False; WAVES.visible_diffuse = False; WAVES.visible_glossy = False
# ---- charges: little glowing specks in the fork that slosh back and forth with the waves, then crowd into the tine tips
CHG_M = emis('charge', (1.0, 0.78, 0.25), 6.0)
CHARGES = []
_rr = random.Random(4)
for i_ in range(46):
    o = prim('uv_sphere', f'chg{i_}', CHG_M, FORK, loc=(0, 0, 0), scale=(0.0006, 0.0006, 0.0006), segments=8, ring_count=6)
    o.visible_shadow = False; x0 = _rr.uniform(0.01, 0.15); k_ = _rr.randrange(4)
    CHARGES.append((o, x0, _rr.uniform(-1, 1), k_, _rr.uniform(0, 6.28)))
def soft_glow(name, col, strength, attr=None, power=2.5):
    # emission that fades to clear toward its silhouette, so a sphere or tube reads as a soft halo, not a disc
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power)
    if attr: fac = math_(nt, 'MULTIPLY', fac, objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')          # additive: a see-through glow
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
GLOW_M = soft_glow('tipglow', (0.65, 0.45, 1.0), 4.0, 'g', 3.0)
HALO_M = soft_glow('arc_halo', (0.45, 0.6, 1.0), 8.0, None, 2.0)
TIP_GLOW = []
for k_, tp in enumerate(TINE_TIPS):
    o = prim('uv_sphere', f'tipglow{k_}', GLOW_M, FORK, loc=tp, scale=(0.0022, 0.0022, 0.0022), segments=16, ring_count=8); o['g'] = 0.0; o.visible_shadow = False; TIP_GLOW.append(o)
# ---- arcs: jagged white-blue lightning between tine tips (or a wire end and the paper), rebuilt every frame, with a flash light
ARC_M = emis('arc', (0.85, 0.9, 1.0), 22.0)
ARC_LT = light_at('arc_lt', 'POINT', (0, 0, 0), (0, 0, 0), 0.0, (0.75, 0.82, 1.0), 0.004)
ARC_OBJS = []
def clear_arcs():
    for o in ARC_OBJS: bpy.data.objects.remove(o, do_unlink=True)
    ARC_OBJS.clear()
def arc(p0, p1, seed, r=0.0007, branches=2):
    rr = random.Random(seed); pts = [p0]; n = 9; d = (p1 - p0); L_ = d.length; side = d.cross(Vector((0, 0, 1))).normalized() if abs(d.normalized().z) < 0.9 else Vector((1, 0, 0))
    up = side.cross(d).normalized()
    for i in range(1, n):
        u = i / n; j = math.sin(u * math.pi) * L_ * 0.28
        pts.append(p0 + d * u + side * rr.uniform(-j, j) * 0.7 + Vector((0, 0, 1)) * (math.sin(u * math.pi) * L_ * 0.45 + rr.uniform(-j, j) * 0.3))   # bows up off the plate
    pts.append(p1); o = tube(f'arc{len(ARC_OBJS)}', pts, r, ARC_M, seg=6); o.visible_shadow = False; ARC_OBJS.append(o)
    h = tube(f'arch{len(ARC_OBJS)}', pts, r * 3.5, HALO_M, seg=8); h.visible_shadow = False; h.visible_diffuse = False; h.visible_glossy = False; ARC_OBJS.append(h)
    for b in range(branches):
        i0 = rr.randrange(2, n - 2); q = pts[i0]; dd = (side * rr.uniform(-1, 1) + up * rr.uniform(-0.5, 1)).normalized() * L_ * rr.uniform(0.2, 0.4)
        bp = [q, q + dd * 0.5 + side * rr.uniform(-1, 1) * L_ * 0.05, q + dd]; ob = tube(f'arcb{len(ARC_OBJS)}', bp, r * 0.5, ARC_M, seg=5); ob.visible_shadow = False; ARC_OBJS.append(ob)
    return pts
