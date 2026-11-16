
# ================================================================ the grape props: a cut grape on a white plate, two whole grapes, two water
# balls, the plasma, sparks, the microwaves coming in and getting trapped, the hot spot, the atoms, the rack's eleven other microwaves.
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))

# ---- the turntable: 5 turns a minute while it runs, stopped from the beep, set going again off camera for the loop
RPM = 5.0
W_TT = 2 * math.pi * RPM / 60.0; A0_TT = R(-20)
def tt_angle(t):
    if t < T_STOP: return A0_TT + W_TT * t
    if t < T_RESET: return A0_TT + W_TT * T_STOP
    return A0_TT + W_TT * (t - END)
def tt_mat(t): return Matrix.Translation(TT_C) @ Matrix.Rotation(tt_angle(t), 4, 'Z')
TH_S = tt_angle(T_STOP)

# ---- a white plate centered on the turntable (red grapes pop on it); its top is local z = 0.0215
PLATE_M = mat('plate', (0.035, 0.05, 0.075), 0.12, coat=1.0)                 # dark slate blue: red grapes, clear water and the glow all pop on it
PLATE = lathe('plate', [(0.0, 0.0205), (0.06, 0.0205), (0.068, 0.022), (0.088, 0.031), (0.095, 0.0325), (0.096, 0.031), (0.086, 0.0265), (0.066, 0.0225),
                        (0.058, 0.0215), (0.0, 0.0215)], 64, PLATE_M, TT)
PZ = 0.0215
# ---- red grape skin: deep red-purple, a little see-through at the edges, glossy, with the dusty bloom
GA, GB, GC = 0.0115, 0.0092, 0.0090                                           # a grape: 2.3 cm long, 1.8 cm wide
def grape_mat(name='grape'):
    m = mat(name, (0.11, 0.008, 0.032), 0.24, coat=0.8); b = N(m)['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (1.0, 0.25, 0.35); b.inputs['Subsurface Scale'].default_value = 0.002
    noisy(m, 320.0, 0.22, 0.14); return m
GRAPE_M = grape_mat()
def ell_mesh(name, a_, b_, c_, half=False, seg=40):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        if half: z = max(z, 0.0)
        v.co = Vector((x * a_, y * b_, z * c_))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return me
# the cut grape: two halves cut face down, a little apart, still joined at one end by a strip of skin
CG_LOCAL = Vector((0.010, 0.004, PZ))
CG = empty('cutgrape', TT, loc=CG_LOCAL); CG.rotation_euler = (0, 0, R(15))
HALF_ME = ell_mesh('grape_half', GA, GB, GC, half=True); HALF_ME.materials.append(GRAPE_M)
HY = GB + 0.0022
HALVES = [obj('half0', HALF_ME, None, loc=(0, -HY, 0), parent=CG), obj('half1', HALF_ME, None, loc=(0, HY, 0), parent=CG)]
BX = -GA + 0.0016
BRIDGE_PTS = [(BX, -0.0040, 0.0010), (BX - 0.0004, -0.0020, 0.0030), (BX - 0.0006, 0.0, 0.0036), (BX - 0.0004, 0.0020, 0.0030), (BX, 0.0040, 0.0010)]
BRIDGE = tube('bridge', BRIDGE_PTS, 0.0011, GRAPE_M, CG, seg=12)
JUNC_L = Vector((BX - 0.0006, 0.0, 0.0036))                                     # where the spark starts (cut grape's local frame)
def junc_world(t): return tt_mat(t) @ (CG_LOCAL + Matrix.Rotation(R(15), 3, 'Z') @ JUNC_L)
CUT_PARTS = HALVES + [BRIDGE]

# ---- after the swap: two whole grapes touching, and two water balls touching, side by side across the front of the plate
def to_local(wx, wy):
    v = Matrix.Rotation(-TH_S, 3, 'Z') @ Vector((wx - TT_C.x, wy - TT_C.y, 0)); return v
WHOLE_C = Vector((TT_C.x - 0.034, TT_C.y - 0.024, TT_C.z + PZ + GB))
BEAD_R = 0.0095
BEAD_C = Vector((TT_C.x + 0.030, TT_C.y - 0.024, TT_C.z + PZ + BEAD_R))
GRAPE_ME = ell_mesh('grape_whole', GB, GA, GB); GRAPE_ME.materials.append(GRAPE_M)          # long axis front to back
WHOLE = []
for sx_ in (-1, 1):
    lp = to_local(WHOLE_C.x + sx_ * GB * 0.995, WHOLE_C.y); o = obj(f'whole{sx_}', GRAPE_ME, None, loc=(lp.x, lp.y, PZ + GB), parent=TT)
    o.rotation_euler = (0, 0, -TH_S); WHOLE.append(o)
WATER_M = mat('water_ball', (0.80, 0.93, 1.0), 0.02, trans=1.0, ior=1.33, coat=0.3)
BEADS = []
for sx_ in (-1, 1):
    lp = to_local(BEAD_C.x + sx_ * BEAD_R * 0.995, BEAD_C.y)
    BEADS.append(prim('uv_sphere', f'bead{sx_}', WATER_M, TT, loc=(lp.x, lp.y, PZ + BEAD_R), scale=(BEAD_R,) * 3, segments=48, ring_count=24))
CONTACT_W = WHOLE_C.copy(); CONTACT_B = BEAD_C.copy()
BEAD_W = [BEAD_C + Vector((-BEAD_R, 0, 0)), BEAD_C + Vector((BEAD_R, 0, 0))]

# ================================================================ glows, smoke
def soft_glow(name, col, strength, attr=None, power=2.5):
    # emission that fades to clear toward its silhouette, so a sphere reads as a soft halo, not a disc
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power)
    if attr: fac = math_(nt, 'MULTIPLY', fac, objattr(nt, attr))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', fac, strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(e_.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
def glow_line(name, col, strength, attr='g'):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, attr), strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', objattr(nt, attr), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
def smoke_mat(name, col=(0.16, 0.16, 0.17), dens=0.75):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 1.0
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), 2.6), math_(nt, 'MULTIPLY', objattr(nt, 'g'), dens))
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fac, mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
SMOKE_M = smoke_mat('smoke', (0.24, 0.24, 0.25), 0.7)
def decal(name, m, loc, sx, sy, rot=(0, 0, 0)):
    o = prim('plane', name, m, loc=loc, size=2.0, rot=rot); o.scale = (sx, sy, 1.0); return o
def burn_mat(name, axes='XY'):
    # a scorch mark, radius 1 in object space: black hole ('hr'), a glowing ember rim ('e'), brown char fading out; 'g' fades it all
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    p = sepz(nt, coord(nt, 'Object')); u_ = p.outputs[axes[0]]; v_ = p.outputs[axes[1]]
    nz = tnoise(nt, coord(nt, 'Object'), 6.0, 4.0)
    r = math_(nt, 'ADD', math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', u_, u_), math_(nt, 'MULTIPLY', v_, v_))), math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz, 0.5), 0.35))
    hr = objattr(nt, 'hr'); inhole = math_(nt, 'LESS_THAN', r, hr)
    rim = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', r, math_(nt, 'ADD', hr, 0.08))), 0.22)), 0.0)
    b.inputs['Roughness'].default_value = 0.9
    nt.links.new(mixc(nt, inhole, ramp(nt, r, [(0.0, (0.0, 0.0, 0.0)), (0.55, (0.02, 0.012, 0.008)), (1.0, (0.12, 0.07, 0.03))]), (0.0, 0.0, 0.0)), b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value = (1.0, 0.38, 0.06, 1)
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', rim, 2.0), objattr(nt, 'e')), 40.0), b.inputs['Emission Strength'])
    alpha = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'POWER', math_(nt, 'MINIMUM', r, 1.0), 3.0)), objattr(nt, 'g'))
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', alpha, 0.0), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ================================================================ plasma: a hot yellow core, a violet halo and flickering tongues that rise to the roof
def plasma_glow(name, col, strength, power, opac):
    # glow that also covers what's behind it (a mix, not an add), so its color holds up against the white oven walls
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    fac = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), power), objattr(nt, 'g'))
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', fac, opac), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
PL_CORE = plasma_glow('pl_core', (1.0, 0.58, 0.14), 7.5, 1.1, 2.0)
PL_HALO = plasma_glow('pl_halo', (0.55, 0.12, 1.0), 2.2, 1.6, 0.9)
PL_TONG = plasma_glow('pl_tongue', (1.0, 0.38, 0.06), 4.5, 1.2, 1.4)
PLASMAS = []
class Plasma:
    def __init__(s, name, origin, t0, t1, top, size, seed, drift=None, rise=0.45):
        s.origin, s.t0, s.t1, s.top, s.size, s.seed, s.drift, s.rise = origin, t0, t1, top, size, seed, drift, rise
        s.core = prim('uv_sphere', name + '_core', PL_CORE, segments=24, ring_count=12); s.halo = prim('uv_sphere', name + '_halo', PL_HALO, segments=24, ring_count=12)
        s.tongues = [prim('uv_sphere', f'{name}_t{i}', PL_TONG, segments=16, ring_count=8) for i in range(5)]
        s.objs = [s.core, s.halo] + s.tongues
        for o in s.objs: o.hide_render = True; o['g'] = 0.0
        PLASMAS.append(s)
    def g(s, t):
        if not (s.t0 <= t < s.t1 + 0.12): return 0.0
        return ease_out((t - s.t0) / 0.08) * (1 - ease_io((t - s.t1) / 0.12)) * (0.8 + 0.2 * wob(t, 17, s.seed))
    def center(s, t):
        o = s.origin(s.t0) if callable(s.origin) else s.origin
        k = ease_out((t - s.t0) / s.rise); c = Vector((o.x, o.y, o.z + (s.top - o.z) * k))
        if s.drift is not None: c = c.lerp(s.drift, ease_io((t - s.t0 - s.rise) / 1.2))
        return c + Vector((wob(t, 2.2, s.seed), wob(t, 2.2, s.seed + 9), 0)) * 0.004 * k
    def update(s, t):
        g_ = s.g(t)
        for o in s.objs: o.hide_render = g_ <= 0.0
        if g_ <= 0.0: return
        c = s.center(t); r = s.size * (0.35 + 0.65 * ease_out((t - s.t0) / 0.15)) * (1 + 0.14 * wob(t, 7, s.seed + 3))
        s.core.location = c; s.core.scale = (r * 0.55, r * 0.55, r * 0.62); s.core['g'] = g_
        s.halo.location = c; s.halo.scale = (r * 1.25, r * 1.25, r * 1.4); s.halo['g'] = g_ * (0.85 + 0.15 * wob(t, 23, s.seed + 5))
        for i, o in enumerate(s.tongues):
            a_ = 2 * math.pi * i / 5 + t * 5.0 + s.seed; ph = wob(t, 11, s.seed + 20 + i)
            o.location = c + Vector((math.cos(a_) * r * 0.5, math.sin(a_) * r * 0.5, r * (0.3 + 0.5 * ph)))
            sc = r * (0.32 + 0.12 * ph); o.scale = (sc, sc, sc * 1.8); o['g'] = g_ * (0.6 + 0.4 * wob(t, 19, s.seed + 40 + i))
    def light(s, t): return s.g(t) * s.size / 0.018

# ---- sparks: short bright streaks thrown off a point (drag + gravity), pooled per spot
SPARK_M = glow_line('spark', (1.0, 0.72, 0.35), 14.0)
SPARKS = []
class Sparks:
    def __init__(s, name, origin, t0, t1, n, seed, spd=(0.15, 0.55), up=0.6, life=(0.12, 0.30), size=1.0, grav=9.8):
        rr = random.Random(seed); s.origin = origin; s.items = []; s.grav = grav
        for i in range(n):
            o = prim('uv_sphere', f'{name}_{i}', SPARK_M, segments=8, ring_count=4); o.hide_render = True; o.rotation_mode = 'QUATERNION'; o['g'] = 1.0
            d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized() + Vector((0, 0, up))
            s.items.append((o, rr.uniform(t0, t1), rr.uniform(*life), d.normalized() * rr.uniform(*spd), rr.uniform(0.00025, 0.0005) * size))
        SPARKS.append(s)
    def update(s, t):
        for o, tb, lf, v, r in s.items:
            dt = t - tb; on = 0 <= dt < lf; o.hide_render = not on
            if not on: continue
            k = 6.0; h = (1 - math.exp(-k * dt)) / k; c = s.origin(tb) if callable(s.origin) else s.origin
            p = c + Vector((v.x * h, v.y * h, (v.z + s.grav / k) * h - s.grav * dt / k))
            vel = Vector((v.x, v.y, v.z + s.grav / k)) * math.exp(-k * dt) - Vector((0, 0, s.grav / k))
            o.location = p; ln = max(r * 1.5, vel.length / FPS * 0.6)
            o.scale = (r, r, ln); o.rotation_quaternion = vel.normalized().to_track_quat('Z', 'Y') if vel.length > 1e-6 else Quaternion()
            o['g'] = 1.0 - (dt / lf) ** 2

# ---- the old idea: current runs through the skin like an antenna: blue dots along the halves' tops and over the strip, the skin glows blue
CUR_M = soft_glow('current', (0.05, 0.4, 1.0), 3.0, 'g', 0.8)
SKIN_GLOW_M = soft_glow('skinglow', (0.1, 0.4, 1.0), 0.7, 'g', 3.5)
SKIN_GLOW = [obj(f'skinglow{i}', HALF_ME, None, loc=h.location, parent=CG) for i, h in enumerate(HALVES)]
for o in SKIN_GLOW: o.data = HALF_ME.copy(); o.data.materials.clear(); o.data.materials.append(SKIN_GLOW_M); o.scale = (1.06, 1.06, 1.06); o['g'] = 0.0; o.hide_render = True
_path = [Vector((x_, -HY, GC * math.sqrt(max(0.0, 1 - (x_ / GA) ** 2)) + 0.0006)) for x_ in [GA * 0.85 - i * GA * 1.7 / 10 for i in range(11)]]
_path += [Vector(p_) + Vector((0, 0, 0.0012)) for p_ in BRIDGE_PTS]
_path += [Vector((x_, HY, GC * math.sqrt(max(0.0, 1 - (x_ / GA) ** 2)) + 0.0006)) for x_ in [-GA * 0.85 + i * GA * 1.7 / 10 for i in range(11)]]
_plen = [0.0]
for i in range(1, len(_path)): _plen.append(_plen[-1] + (_path[i] - _path[i - 1]).length)
def path_at(sv):
    sv = sv % _plen[-1]; i = next(j for j in range(1, len(_plen)) if _plen[j] >= sv); k = (sv - _plen[i - 1]) / max(1e-9, _plen[i] - _plen[i - 1])
    return _path[i - 1].lerp(_path[i], k)
CUR_DOTS = [prim('uv_sphere', f'cur{i}', CUR_M, CG, scale=(0.0007,) * 3, segments=12, ring_count=6) for i in range(18)]
for o in CUR_DOTS: o['g'] = 0.0; o.hide_render = True

# ---- the waves: wiggly beams from the waveguide (right wall) into each water ball, long in the air, squeezed tight inside the water
WAVE_M = glow_line('wave', (0.15, 0.75, 1.0), 3.0)
WAVES = []
for i_, bc in enumerate(BEAD_W):
    o = obj(f'wave{i_}', bpy.data.meshes.new(f'wave{i_}'), WAVE_M); o['g'] = 0.0; o.hide_render = True
    WAVES.append((o, Vector((CX1 - 0.003, bc.y + (0.012 if i_ else -0.010), 0.150 - 0.02 * i_)), bc))
LAM_AIR, LAM_W = 0.030, 0.0055
def wave_points(S0, C, head, ph):
    d = C - S0; Lt = d.length + BEAD_R * 0.75; u_ = d.normalized(); n_ = u_.cross(Vector((0, 1, 0))); n_ = n_.normalized() if n_.length > 1e-6 else Vector((0, 0, 1))
    pts = []; phase = 0.0; s_ = 0.0; ds = 0.0004
    while s_ < min(head, Lt):
        p = S0 + u_ * s_; inside = (p - C).length < BEAD_R * 0.98
        lam = LAM_W if inside else LAM_AIR; amp = 0.0011 if inside else 0.0042
        taper = clamp(s_ / 0.01, 0, 1) * clamp((head - s_) / 0.004, 0, 1)
        pts.append(p + n_ * amp * taper * math.sin(phase - ph)); phase += 2 * math.pi * ds / lam; s_ += ds
    return pts
def set_tube(o, pts, r, seg=8):
    me = o.data; me.clear_geometry()
    if len(pts) < 3: return False
    n = len(pts); T0 = (pts[1] - pts[0]).normalized(); up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized()
    vs = []; fs = []
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        vs += [pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    for i in range(n - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    me.from_pydata([tuple(v) for v in vs], [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    return True
# trapped: a wavy glowing ring inside each ball (facing the camera), spinning; two per ball
RING_M = glow_line('ring', (0.15, 0.78, 1.0), 3.2)
def ring_mesh(name, R0, lobes, amp, r=0.00035, seg=6, n=160):
    pts = [Vector((R0 * (1 + amp * math.sin(lobes * 2 * math.pi * i / n)) * math.cos(2 * math.pi * i / n), 0, R0 * (1 + amp * math.sin(lobes * 2 * math.pi * i / n)) * math.sin(2 * math.pi * i / n))) for i in range(n)]
    pts.append(pts[0]); pts.append(pts[1])
    o = obj(name, bpy.data.meshes.new(name), RING_M); set_tube(o, pts, r, seg); return o
RINGS = []
for i_, bc in enumerate(BEAD_W):
    for j_, (R0, lob) in enumerate(((0.0060, 7), (0.0037, 5))):
        o = ring_mesh(f'ring{i_}{j_}', R0, lob, 0.12); o.rotation_mode = 'XYZ'; o['g'] = 0.0; o.hide_render = True; RINGS.append((o, bc, i_, j_))
# the hot spot where the balls touch, and five atoms in it that get ripped apart
HOT_M = soft_glow('hot', (0.75, 0.92, 1.0), 9.0, 'g', 1.0)
HOT = prim('uv_sphere', 'hotspot', HOT_M, loc=CONTACT_B, segments=20, ring_count=10); HOT['g'] = 0.0; HOT.hide_render = True
NUC_M = mat('nucleus', (0.95, 0.35, 0.12), 0.35, emit=(1.0, 0.45, 0.15), estr=2.0)
ELEC_M = soft_glow('electron', (0.2, 0.7, 1.0), 8.0, None, 0.8)
ATOMS = []; _rr = random.Random(7)
for k_ in range(5):
    a_ = 2 * math.pi * k_ / 5 + 0.4; home = CONTACT_B + Vector((math.cos(a_) * 0.0034, -0.0085, math.sin(a_) * 0.0034))
    nuc = prim('uv_sphere', f'nuc{k_}', NUC_M, loc=home, segments=16, ring_count=8)
    els = [prim('uv_sphere', f'el{k_}{j_}', ELEC_M, segments=10, ring_count=5) for j_ in range(2)]
    ATOMS.append((nuc, els, home, Vector((_rr.uniform(-1, 1), _rr.uniform(-1, 1), _rr.uniform(-1, 1))).normalized(), _rr.uniform(0, 6.28)))
    for o in [nuc] + els: o.hide_render = True

# ================================================================ the rack: eleven more microwaves (ours is the middle of the second shelf)
COPIES = []
_order = random.Random(4).sample(range(11), 11)
WIN_GLOW = soft_glow('winglow', (1.0, 0.5, 0.35), 5.0, 'g', 1.2)
_slots = [(c_, r_) for r_ in range(4) for c_ in range(3) if not (c_ == 1 and r_ == 1)]
for n_, (c_, r_) in enumerate(_slots):
    off = Vector((COL_X[c_], 0.0, SHELF_Z[r_])); root = empty(f'mw{n_}', loc=off); mp = {}
    for o in MW_OBJS:
        c = o.copy(); S.collection.objects.link(c); mp[o] = c
    for o, c in mp.items():
        c.parent = mp[o.parent] if o.parent in mp else root
    for k_ in ('xr',):
        for c in mp.values():
            if k_ in c: c[k_] = 0.0
    glow = prim('uv_sphere', f'mw{n_}_glow', WIN_GLOW, loc=off + Vector((TT_C.x, TT_C.y, 0.09)), scale=(0.035,) * 3, segments=16, ring_count=8); glow['g'] = 0.0; glow.hide_render = True
    top = decal(f'mw{n_}_scorch', burn_mat(f'scorch{n_}', 'XY'), off + Vector((-0.04, 0.0, MW_H + 0.0006)), 0.09, 0.09); top['g'] = 0.0; top['hr'] = 0.30; top['e'] = 0.0
    soot = decal(f'mw{n_}_soot', burn_mat(f'soot{n_}', 'XY'), off + Vector((-0.05, -MW_D / 2 - 0.0125, MW_H - 0.02)), 0.15, 0.05, (R(90), 0, 0))
    soot['g'] = 0.0; soot['hr'] = -1.0; soot['e'] = 0.0
    puffs = [prim('uv_sphere', f'mw{n_}_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(7)]
    for o in puffs: o['g'] = 0.0; o.hide_render = True
    tz = T_ZAP - 0.55 + 0.11 * _order[n_]; tw = T_WRECK - 0.15 + 0.07 * _order[n_]
    COPIES.append(dict(off=off, glow=glow, top=top, soot=soot, puffs=puffs, tz=tz, tw=tw, seed=n_ * 13.0))
MAIN_GLOW = prim('uv_sphere', 'main_glow', WIN_GLOW, loc=Vector((TT_C.x, TT_C.y, 0.09)), scale=(0.035,) * 3, segments=16, ring_count=8); MAIN_GLOW['g'] = 0.0; MAIN_GLOW.hide_render = True
MAIN_PUFFS = [prim('uv_sphere', f'main_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(7)]
for o in MAIN_PUFFS: o['g'] = 0.0; o.hide_render = True
WIDE = light_at('wide', 'AREA', (0.3, -2.2, 1.7), (0, 0, 0.35), 0.0, (1.0, 0.96, 0.9), 2.5)

# ---- our oven's roof melting through: a scorch that glows, opens to a black hole with an ember rim; smoke under the roof; drips
HOLE_C = Vector(((CONTACT_W.x + CONTACT_B.x) / 2, CONTACT_B.y + 0.01, CZ1 - 0.0004))
HOLE = decal('hole', burn_mat('hole', 'XY'), HOLE_C, 0.045, 0.045); HOLE['g'] = 0.0; HOLE['hr'] = 0.0; HOLE['e'] = 0.0
HOLE.hide_render = True
ROOF_SMOKE = [prim('uv_sphere', f'roof_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(6)]
for o in ROOF_SMOKE: o['g'] = 0.0; o.hide_render = True
OUT_SMOKE = [prim('uv_sphere', f'out_smoke{j_}', SMOKE_M, segments=16, ring_count=8) for j_ in range(8)]
for o in OUT_SMOKE: o['g'] = 0.0; o.hide_render = True
PL_LT = light_at('plasma_lt', 'POINT', (0, 0, 0.1), (0, 0, 0), 0.0, (1.0, 0.45, 0.25), 0.008)
for o_ in bpy.data.objects:
    if o_.name.startswith('tt_plate'): o_.visible_shadow = False
