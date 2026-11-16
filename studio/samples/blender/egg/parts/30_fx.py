
# ================================================================ the egg props: a peeled hard boiled egg on a plate in the oven, the fork,
# the kitchen floor with the engineers' hundred eggs, a microphone a foot from the test egg, a meat thermometer, the x-ray egg.
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))

# ---- the door swings on a hinge at its left edge (rotate the hinge about z; negative opens it toward us)
HINGE = empty('hinge', loc=(DOOR_X0, -MW_D / 2 - 0.004, 0)); DOOR.parent = HINGE; DOOR.location = (-DOOR_X0, 0, 0)

# ---- the plate (centered on the turntable) and the egg
CERAMIC = mat('ceramic', (0.05, 0.22, 0.30), 0.10, coat=1.0)                # deep teal: the white egg pops on it
PLATE = lathe('plate', [(0.0, 0.0205), (0.06, 0.0205), (0.068, 0.022), (0.088, 0.031), (0.095, 0.0325), (0.096, 0.031), (0.086, 0.0265), (0.066, 0.0225),
                        (0.058, 0.0215), (0.0, 0.0215)], 64, CERAMIC, TT)
EGG_L, EGG_R = 0.0285, 0.0215                                                # a large egg: 5.7 cm long, 4.3 cm wide
def egg_mesh(name, seg=48):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co; k = 1.0 - 0.12 * x                                    # the narrow end is +x
        v.co = Vector((x * EGG_L, y * EGG_R * k, z * EGG_R * k))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return me
EGG_ME = egg_mesh('egg')
def egg_white_mat(name='egg_white'):
    m = mat(name, (0.93, 0.92, 0.86), 0.22, coat=0.5); b = N(m)['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.45; b.inputs['Subsurface Radius'].default_value = (1.0, 0.85, 0.6); b.inputs['Subsurface Scale'].default_value = 0.004
    return m
EGG_M = egg_white_mat(); EGG_ME.materials.append(EGG_M)            # shared mesh: one material on the mesh, objects add none
YOLK_M = noisy(mat('yolk', (0.95, 0.60, 0.07), 0.8), 600.0, 0.18, 0.1)
EGG_LOCAL = Vector((0.02, 0.0, 0.0215 + EGG_R))                            # on the plate, a little off center so it travels as the plate turns
EGG1 = obj('egg1', EGG_ME, None, loc=EGG_LOCAL, parent=TT); EGG1.rotation_euler = (0, 0, R(70))

# ---- the fork: 19 cm stainless; FORKP sits at the tine tips and its local +x points the way the fork is going
FORK_M = mat('stainless', (0.80, 0.80, 0.82), 0.16, 1.0, coat=0.2)
def flat_shape(name, outline, th, m, parent, loc=(0, 0, 0)):
    bm = bmesh.new(); vs = [bm.verts.new((x, y, 0.0)) for x, y in outline]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, th), verts=[e for e in ex['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = obj(name, me, m, loc=loc, parent=parent); md = o.modifiers.new('bv', 'BEVEL'); md.width = th * 0.45; md.segments = 3; md.limit_method = 'ANGLE'
    o.modifiers.new('wn', 'WEIGHTED_NORMAL')
    for p_ in me.polygons: p_.use_smooth = True
    return o
FORKP = empty('forkp'); FORKP.rotation_mode = 'QUATERNION'
_fi = empty('fork_in', FORKP, loc=(-0.19, 0, -0.0011))
_h = [(0.0, 0.0105), (0.012, 0.0118), (0.05, 0.0095), (0.098, 0.0042), (0.118, 0.0036), (0.135, 0.0062), (0.148, 0.0118), (0.152, 0.0122)]
FORK_PARTS = [flat_shape('fork_body', [(x, y) for x, y in _h] + [(x, -y) for x, y in reversed(_h)], 0.0024, FORK_M, _fi)]
for k_ in range(4):
    yc = -0.0092 + 0.00613 * k_; w = 0.0021
    FORK_PARTS.append(flat_shape(f'tine{k_}', [(0.150, yc - w), (0.182, yc - w * 0.9), (0.190, yc), (0.182, yc + w * 0.9), (0.150, yc + w)], 0.0022, FORK_M, _fi))

def obj_coords(m, rot=(0, 0, 0)):
    nt = m.node_tree; tc = next(n for n in nt.nodes if n.type == 'TEX_COORD'); mp = next(n for n in nt.nodes if n.type == 'MAPPING')
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); mp.inputs['Rotation'].default_value = rot; return m
for o_ in bpy.data.objects:
    if o_.name == 'cabinet': obj_coords(o_.data.materials[0], (R(90), 0, 0))
    if o_.name == 'counter': obj_coords(o_.data.materials[0])
# ---- the kitchen floor (the cabinet stands on it) and a light for it
FLOOR_Z = -0.90
box('floor', (4.0, 4.0, 0.02), (0, -0.9, FLOOR_Z - 0.01), obj_coords(P.material('ph:oak_veneer_01', scale=1.5)))
box('toekick', (1.6, 0.02, 0.09), (0, -0.215, FLOOR_Z + 0.045), mat('toe', (0.05, 0.05, 0.05), 0.6))
FKEY = light_at('floor_key', 'AREA', (-0.55, -1.95, -0.25), (0.0, -1.0, -0.9), 16, (1.0, 0.95, 0.88), 0.9)
FFILL = light_at('floor_fill', 'AREA', (0.9, -1.4, -0.45), (0.0, -1.0, -0.9), 5, (0.85, 0.9, 1.0), 0.6)

# ---- the engineers' eggs: almost a hundred, in rows on the floor; the test egg A with the microphone a foot away; egg B for the x-ray
FLOOR_EGG_Z = FLOOR_Z + EGG_R
GRID = []; _rr = random.Random(11)
for j_ in range(10):
    for i_ in range(10):
        if (i_, j_) in ((0, 0), (9, 0)): continue                                       # 98 of them: "almost a hundred"
        p = Vector((-0.34 + 0.0755 * i_ + _rr.uniform(-0.01, 0.01), -0.42 - 0.072 * j_ + _rr.uniform(-0.008, 0.008), FLOOR_EGG_Z))
        o = obj(f'gegg{len(GRID)}', EGG_ME, None, loc=p); o.rotation_euler = (0, 0, _rr.uniform(0, math.pi)); GRID.append(o)
A_C = Vector((0.05, -1.24, FLOOR_EGG_Z)); B_C = Vector((-0.17, -1.21, FLOOR_EGG_Z))
EGGA = obj('egga', EGG_ME, None, loc=A_C); EGGA.rotation_euler = (0, 0, R(100))
# egg B: its white turns to glass for the x-ray ('xr'), the yolk shows through, the trapped drops glow inside it
EGGX_M = xray_mat('egg_x', (0.93, 0.92, 0.86), 0.22)
EGGB = obj('eggb', egg_mesh('eggb'), EGGX_M, loc=B_C); EGGB.rotation_euler = (0, 0, R(-8)); EGGB['xr'] = 0.0
def yolk_x_mat():
    m = mat('yolk_x', (0.95, 0.60, 0.07), 0.7); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (1.0, 0.42, 0.08, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'heat'), 2.5), b.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', objattr(nt, 'xr'), 0.6)), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
YOLKB = prim('uv_sphere', 'yolkb', yolk_x_mat(), loc=B_C + Vector((-0.002, 0, 0.0)), scale=(0.0118, 0.0118, 0.0118), segments=32, ring_count=16)
YOLKB['xr'] = 0.0; YOLKB['heat'] = 0.0
def drop_mat():
    m = bpy.data.materials.new('drop'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    c_ = mixc(nt, objattr(nt, 'h'), (0.45, 0.75, 1.0), (1.0, 0.5, 0.12)); c_ = mixc(nt, objattr(nt, 'f'), c_, (1.0, 0.95, 0.85))
    e_ = nt.nodes.new('ShaderNodeEmission'); nt.links.new(c_, e_.inputs['Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'ADD', 3.0, math_(nt, 'MULTIPLY', objattr(nt, 'h'), 5.0)), math_(nt, 'MULTIPLY', objattr(nt, 'f'), 30.0)), e_.inputs['Strength'])
    nt.links.new(e_.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
DROP_M = drop_mat(); DROPS = []
_rr = random.Random(5)
while len(DROPS) < 42:
    p = Vector((_rr.uniform(-1, 1), _rr.uniform(-1, 1), _rr.uniform(-1, 1)))
    if p.length > 1.0: continue
    d = prim('ico_sphere', f'drop{len(DROPS)}', DROP_M, loc=YOLKB.location + p * 0.0092, subdivisions=2, radius=_rr.uniform(0.0009, 0.0014))
    d['h'] = 0.0; d['f'] = 0.0; d['home'] = tuple(d.location); d.hide_render = True; DROPS.append(d)
POKE_B = B_C + Vector((0.004, 0.0, EGG_R))                                     # where the thermometer goes into egg B (the top)
_dd = [(Vector(x['home']) - POKE_B).length for x in DROPS]
DROP0 = min(range(len(DROPS)), key=lambda i: _dd[i]); _dmax = max(_dd); _dmin = min(_dd)

# ---- the microphone a foot from egg A, on a little stand, pointing at it
MIC_M = mat('mic', (0.03, 0.03, 0.035), 0.35, 0.6); GRILLE_M = mat('grille', (0.22, 0.22, 0.23), 0.45, 1.0)
MIC = empty('mic', loc=A_C + Vector((0.30, 0.0, 0.045))); MIC.rotation_euler = (0, R(-12), 0)
prim('uv_sphere', 'mic_grille', GRILLE_M, MIC, scale=(0.011, 0.011, 0.011), segments=24, ring_count=12)
tube('mic_body', [(0.008, 0, 0), (0.05, 0, 0), (0.095, 0, 0)], lambda u: 0.0095 - 0.003 * u, MIC_M, MIC)
MIC_STAND = []
_hub = A_C + Vector((0.35, 0.0, 0.025))
MIC_STAND.append(tube('mic_rod', [_hub + Vector((0, 0, 0.012)), _hub + Vector((0, 0, -0.01)), _hub + Vector((0, 0, -0.03))], 0.0025, MIC_M))
for k_ in range(3):
    a_ = R(90 + 120 * k_); MIC_STAND.append(tube(f'mic_leg{k_}', [_hub, _hub + Vector((math.cos(a_) * 0.03, math.sin(a_) * 0.03, -0.024)), _hub + Vector((math.cos(a_) * 0.05, math.sin(a_) * 0.05, -0.0455))], 0.0018, MIC_M))
tube('mic_cable', [A_C + Vector((0.395, 0, 0.04)), A_C + Vector((0.43, 0.02, 0.0)), A_C + Vector((0.47, 0.05, -0.0205)), A_C + Vector((0.7, 0.2, -0.0205))], 0.0022, MIC_M)

# ---- the meat thermometer: THERM sits at the probe tip, the probe runs up its local +z to a round dial
THERM = empty('therm'); THERM.rotation_euler = (R(-14), R(10), 0)
_tm = mat('probe', (0.82, 0.82, 0.84), 0.2, 1.0)
lathe('probe', [(0.0, 0.0), (0.0019, 0.009), (0.0019, 0.125), (0.0, 0.125)], 24, _tm, THERM)
lathe('dial_case', [(0.0, 0.124), (0.008, 0.124), (0.024, 0.128), (0.025, 0.134), (0.024, 0.140), (0.0, 0.140)], 48, _tm, THERM)
_dial = lathe('dial_face', [(0.0, 0.1405), (0.0215, 0.1405), (0.0215, 0.1406), (0.0, 0.1406)], 48, mat('dialface', (0.95, 0.95, 0.93), 0.4), THERM)
box('needle', (0.002, 0.016, 0.0008), (0.0, 0.006, 0.1412), mat('needle', (0.85, 0.05, 0.03), 0.4), parent=THERM)

# ================================================================ bursts: chunks of white and yolk that fly, hit walls and floor, and slide to a stop
def soft_glow(name, col, strength, attr=None, power=2.5):
    # emission that fades to clear toward its silhouette, so a sphere or tube reads as a soft halo, not a disc
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power)
    if attr: fac = math_(nt, 'MULTIPLY', fac, objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')          # additive: a see-through glow
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
CHUNK_ME = {False: [], True: []}
_rr = random.Random(21)
for yolk_ in (False, True):
    for k_ in range(8):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); fl = _rr.uniform(0.35, 0.7)
        for v in bm.verts: v.co = Vector((v.co.x * _rr.uniform(0.7, 1.3), v.co.y * _rr.uniform(0.7, 1.3), v.co.z * fl))
        me = bpy.data.meshes.new(f'chunk{int(yolk_)}{k_}'); bm.to_mesh(me); bm.free(); [setattr(p_, 'use_smooth', True) for p_ in me.polygons]; me.materials.append(YOLK_M if yolk_ else EGG_M); CHUNK_ME[yolk_].append(me)
STEAM_M = soft_glow('steam', (0.85, 0.87, 0.9), 0.15, 'g', 3.0)
POP_LT = light_at('pop_lt', 'POINT', (0, 0, 0), (0, 0, 0), 0.0, (1.0, 0.92, 0.8), 0.01)
BURSTS = []
class Burst:
    def __init__(s, name, t0, c, nW, nY, seed, spd=(0.5, 1.8), up=0.7, box_=None, floor=None, size=1.0, steam=4, flash=1.0):
        rr = random.Random(seed); s.t0, s.c, s.box, s.floor, s.flash = t0, Vector(c), box_, floor, flash; s.parts = []; s.steam = []
        for i in range(nW + nY):
            yolk = i >= nW; d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized()
            p0 = Vector((d.x * EGG_L, d.y * EGG_R, d.z * EGG_R)) * (0.35 if yolk else 0.8)
            v = (d + Vector((0, 0, up))).normalized() * rr.uniform(*spd) * (0.8 if yolk else 1.0)
            r = (rr.uniform(0.0018, 0.0042) if yolk else rr.uniform(0.0025, 0.0075)) * size
            o = obj(f'{name}_c{i}', CHUNK_ME[yolk][rr.randrange(8)], None); o.scale = (r, r, r); o.hide_render = True
            s.parts.append((o, p0, v, r, Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1))) * rr.uniform(8, 25)))
        for i in range(steam):
            o = prim('uv_sphere', f'{name}_st{i}', STEAM_M, scale=(1, 1, 1), segments=20, ring_count=10); o['g'] = 0.0; o.hide_render = True
            s.steam.append((o, Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(0.2, 1))).normalized() * rr.uniform(0.01, 0.04) * size, rr.uniform(0.014, 0.03) * size, rr.uniform(0.9, 1.6)))
        BURSTS.append(s)
    def floor_at(s, x, y): return s.floor(x, y) if callable(s.floor) else s.floor
    def update(s, t):
        on = t >= s.t0; dt = max(0.0, t - s.t0); k = 3.0; g = 9.8; h = (1 - math.exp(-k * dt)) / k
        for o, p0, v, r, spin in s.parts:
            o.hide_render = not on
            if not on: continue
            x = s.c.x + p0.x + v.x * h; y = s.c.y + p0.y + v.y * h; z = s.c.z + p0.z + (v.z + g / k) * h - g * dt / k
            if s.box:
                (x0, x1), (y0, y1), z1 = s.box
                x = clamp(x, x0 + r, x1 - r); y = min(y, y1 - r); z = min(z, z1 - r)
            fz = s.floor_at(x, y) + r * 0.55
            if z < fz: z = fz
            o.location = (x, y, z); o.rotation_euler = (spin.x * h, spin.y * h, spin.z * h)
        for o, dv, rad, life in s.steam:
            u = dt / life; o.hide_render = not on or u > 1.0
            if o.hide_render: continue
            sc = rad * (0.4 + 1.6 * ease_out(u * 1.5)); o.scale = (sc, sc, sc); o.location = s.c + dv * (1 + 6 * u) + Vector((0, 0, 0.05 * u))
            o['g'] = (1 - u) ** 1.5 * ease_out(dt / 0.05)
    def light(s, t): return s.flash * max(0.0, 1 - (t - s.t0) / 0.18) if t >= s.t0 else 0.0

# shockwave from egg A: a flat ring along the floor and a faint bubble, both swelling past the microphone
def edge_glow(name, col, strength, attr, power=3.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], power), objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
WAVE_M = edge_glow('shock', (0.75, 0.88, 1.0), 3.0, 'g', 2.5)
SHOCK = prim('uv_sphere', 'shock', WAVE_M, loc=A_C, segments=48, ring_count=24); SHOCK['g'] = 0.0; SHOCK.hide_render = True
SHOCK_RING = lathe('shock_ring', [(1.0 + 0.012 * math.cos(2 * math.pi * k / 12), 0.012 * math.sin(2 * math.pi * k / 12)) for k in range(13)], 96, soft_glow('ring', (0.8, 0.9, 1.0), 6.0, 'g', 1.0))
SHOCK_RING['g'] = 0.0; SHOCK_RING.hide_render = True
# the glass turntable would throw a black shadow over the whole oven floor (no caustics): let light through it
for o_ in bpy.data.objects:
    if o_.name == 'tt_plate': o_.visible_shadow = False
