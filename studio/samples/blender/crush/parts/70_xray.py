# ================================================================ X-RAY: see-through skin; the crushed legs ('crush' 0..1) glow a sick red-purple,
# yellow specks (potassium) build up in them, and when the weight comes off they run up the leg veins to the heart
def xray_skin_mat():
    m = bpy.data.materials.new('xskin'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    leg = nt.nodes.new('ShaderNodeMapRange'); leg.inputs['From Min'].default_value = 0.72; leg.inputs['From Max'].default_value = 0.6
    nt.links.new(sx.outputs['Z'], leg.inputs['Value'])                                    # 1 below mid-thigh, 0 above
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 28.0; nz.inputs['Detail'].default_value = 3
    nt.links.new(rp.outputs['Vector'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 1.5), nz.inputs['W'])
    hot = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', leg.outputs['Result'], objattr(nt, 'crush')), math_(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 1.2, 0.3))
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.0)
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.inputs['A'].default_value = (0.35, 0.62, 1.0, 1); base.inputs['B'].default_value = (0.85, 0.08, 0.35, 1)
    nt.links.new(math_(nt, 'MINIMUM', hot, 1.0), base.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(base.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 1.0, 0.02), math_(nt, 'MULTIPLY', hot, 0.9)), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 0.5, 0.04), math_(nt, 'MULTIPLY', hot, 0.3)), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
XSKIN = xray_skin_mat()
BODY['crush'] = 0.0; BODY['tt'] = 0.0
BODY_MATS = [sl.material for sl in BODY.material_slots]
def ghost_mat(name, col=(0.7, 0.8, 1.0), k=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 1.5), k), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 1.5), 0.6), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
GHOST_M = ghost_mat('ghost', (0.75, 0.85, 1.0), 0.8)
# vessels: the leg veins and the big vein up to the heart (his rest space, carried by the bones of the pinned pose)
def bone_for(c):
    side = 'L' if c.x > 0 else 'R'
    if c.z > 1.15: return 'spine01'
    if c.z > 0.95: return 'spine03'
    if c.z > 0.86: return 'root' if abs(c.x) < 0.06 else 'upperleg01.' + side
    if c.z > 0.5: return 'upperleg02.' + side
    if c.z > 0.12: return 'lowerleg02.' + side
    return 'foot.' + side
def smooth_pts(ctrl, n=40):
    out_ = []
    for i in range(n):
        u = i / (n - 1) * (len(ctrl) - 1); k = min(int(u), len(ctrl) - 2); f = u - k
        p0 = Vector(ctrl[max(k - 1, 0)]); p1 = Vector(ctrl[k]); p2 = Vector(ctrl[k + 1]); p3 = Vector(ctrl[min(k + 2, len(ctrl) - 1)])
        out_.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return out_
def flow_mat(name, col, dash=40.0):
    """a vessel: a dim tube with bright pulses running along it ('ph' moves them, 'glow' = brightness); UV x = metres along it"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    uv = nt.nodes.new('ShaderNodeUVMap'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv.outputs['UV'], sx.inputs['Vector'])
    sn = math_(nt, 'SINE', math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', sx.outputs['X'], dash), objattr(nt, 'ph')))
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.2; mr.inputs['From Max'].default_value = 1.0; mr.inputs['To Min'].default_value = 0.35; mr.inputs['To Max'].default_value = 3.0
    nt.links.new(sn, mr.inputs['Value'])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); nt.links.new(math_(nt, 'MULTIPLY', mr.outputs['Result'], objattr(nt, 'glow')), em.inputs['Strength'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
VEIN_M = flow_mat('vein', (0.25, 0.35, 1.0), 30.0)
def vtube(name, pts, r, m):
    o = tube(name, pts, r, m, None, seg=10)
    me = o.data; uvl = me.uv_layers.new(name='UVMap'); seg = 10; arc = [0.0]
    for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; ring = min(vi // seg, len(pts) - 1); uvl.data[li].uv = (arc[ring], (vi % seg) / seg)
    o['ph'] = 0.0; o['glow'] = 1.0; o.visible_shadow = False; return o, arc
pinned(0.0)
def wpath(rest_pts): return [deform(p_, bone_for(Vector(p_))) for p_ in rest_pts]
VEINS = {}
for s_, sg in (('L', 1), ('R', -1)):
    rp_ = smooth_pts([(sg * 0.2, 0.01, 0.1), (sg * 0.185, 0.02, 0.3), (sg * 0.17, 0.02, 0.47), (sg * 0.15, -0.01, 0.62), (sg * 0.12, -0.01, 0.82), (sg * 0.07, 0.02, 0.9), (0.012, 0.03, 0.94)], 46)
    VEINS[s_] = vtube('legvein' + s_, wpath(rp_), 0.0085, VEIN_M)
_cava_rest = smooth_pts([(0.012, 0.03, 0.94), (0.025, 0.025, 1.1), (0.03, -0.01, 1.22), (0.03, -0.04, 1.26)], 30)
CAVA = vtube('vena_cava', wpath(_cava_rest), 0.012, VEIN_M)
def organ_mat(name, c0, c1, prop):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (*c1, 1); mx.inputs['B'].default_value = (*c0, 1); nt.links.new(objattr(nt, prop), mx.inputs['Factor'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    st = nt.nodes.new('ShaderNodeMapRange'); st.inputs['To Min'].default_value = 3.0; st.inputs['To Max'].default_value = 0.9; nt.links.new(lw.outputs['Facing'], st.inputs['Value'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mx.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'MULTIPLY', st.outputs['Result'], math_(nt, 'MULTIPLY_ADD', objattr(nt, 'flash'), 0.35, 1.0)), em.inputs['Strength'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface']); return m
HEART_M = organ_mat('heart', (1.0, 0.18, 0.05), (0.85, 0.05, 0.05), 'kk')
HEART_C = deform(V3(0.025, -0.06, 1.25), 'spine01')
HEART = prim('uv_sphere', 'heart', HEART_M, None, loc=(0, 0, 0), segments=48, ring_count=24, radius=1.0)
for v in HEART.data.vertices:                                     # bend a ball into a heart: two lobes on top, a point at the bottom
    x, y, z = v.co; zz = z
    w = 1.0 - 0.55 * max(0.0, -zz) ** 1.3; dip = 0.28 * math.exp(-(x / 0.28) ** 2) * max(0.0, zz) ** 2
    v.co = Vector((x * 0.055 * w * (1 + 0.15 * max(0.0, zz)), y * 0.04 * w, (z - dip) * 0.06 - 0.012 * max(0.0, -zz) ** 2))
tx_ = bpy.data.textures.new('heart_n', 'CLOUDS'); tx_.noise_scale = 0.03; d_ = HEART.modifiers.new('bump', 'DISPLACE'); d_.texture = tx_; d_.strength = 0.006; d_.texture_coords = 'LOCAL'
HEART.location = HEART_C; HEART.rotation_euler = (R(20) - R(88), R(-25), R(15)); HEART['kk'] = 0.0; HEART['flash'] = 0.0; HEART.visible_shadow = False
# potassium specks: one mesh of tiny bright balls, moved every frame
NK = 260; _kr = np.random.default_rng(9)
_legv = np.where((_RP[:, 2] > 0.08) & (_RP[:, 2] < 0.6))[0]
def leg_spots():
    W_, RP_ = body_eval(); idx = _kr.choice(_legv, NK, replace=False)
    out = []
    for i in idx:
        s_ = 'L' if RP_[i, 0] > 0 else 'R'; bn = 'lowerleg02.' + s_ if RP_[i, 2] < 0.45 else 'upperleg02.' + s_
        a_ = np.array(wpos(bn)); b_ = np.array(wpos(bn, True)); p_ = W_[i]; ab = b_ - a_; k = np.clip(np.dot(p_ - a_, ab) / np.dot(ab, ab), 0, 1); c_ = a_ + ab * k
        out.append((c_ + (p_ - c_) * _kr.uniform(0.25, 0.7), s_, float(RP_[i, 2])))
    return out
KSPOTS = leg_spots()
K_P0 = np.array([k_[0] for k_ in KSPOTS]); K_SIDE = [k_[1] for k_ in KSPOTS]; K_Z = np.array([k_[2] for k_ in KSPOTS])
K_ORDER = _kr.permutation(NK) / NK                                  # when each speck shows up (0..1 of the build-up)
_ico = bpy.data.meshes.new('kico'); _bm = bmesh.new(); bmesh.ops.create_icosphere(_bm, subdivisions=1, radius=1.0); _bm.to_mesh(_ico); _bm.free()
ICO_V = np.array([v.co[:] for v in _ico.vertices]); ICO_F = [tuple(p_.vertices) for p_ in _ico.polygons]; NI = len(ICO_V)
K_M = emis('potassium', (1.0, 0.85, 0.15), 14.0)
KMESH = mesh('potassium', [tuple(v) for v in np.tile(ICO_V * 0.005, (NK, 1))], [tuple(i + k * NI for i in f) for k in range(NK) for f in ICO_F], K_M, smooth_=True)
KMESH.visible_shadow = False
_VPTS = {s_: [deform(p_, bone_for(Vector(p_))) for p_ in smooth_pts([(sg * 0.2, 0.01, 0.1), (sg * 0.185, 0.02, 0.3), (sg * 0.17, 0.02, 0.47), (sg * 0.15, -0.01, 0.62), (sg * 0.12, -0.01, 0.82), (sg * 0.07, 0.02, 0.9), (0.012, 0.03, 0.94)], 46)]
         + wpath(_cava_rest)[1:] + [HEART_C] for s_, sg in (('L', 1), ('R', -1))}
_VARC = {}
for s_, P_ in _VPTS.items():
    a_ = [0.0]
    for i in range(1, len(P_)): a_.append(a_[-1] + (P_[i] - P_[i - 1]).length)
    _VARC[s_] = np.array(a_)
def along(side, d):
    P_, A_ = _VPTS[side], _VARC[side]; d = clamp(d, 0, A_[-1]); i = int(np.searchsorted(A_, d)); i = clamp(i, 1, len(P_) - 1)
    f = (d - A_[i - 1]) / max(A_[i] - A_[i - 1], 1e-6); return np.array(P_[i - 1].lerp(P_[i], f))
def k_entry(i):
    """where speck i joins its leg vein: the vein point at the speck's own height in the leg (arc from the foot)"""
    return clamp((K_Z[i] - 0.1) / 0.84, 0.0, 1.0) * float(_VARC[K_SIDE[i]][45])
K_ENTRY = np.array([k_entry(i) for i in range(NK)])
def specks(t, amt, run=-1.0, size=0.006):
    """amt 0..1: how many specks have built up; run >= 0: seconds since the weight came off (they race to the heart)"""
    P = np.zeros((NK, 3)); sc = np.zeros(NK)
    for i in range(NK):
        on = amt > K_ORDER[i]; sc[i] = size * (0.7 + 0.6 * ((i * 37) % 10) / 10) if on else 0.0
        j = np.array([wob(t, 1.3, i * 0.37), wob(t, 1.3, i * 0.37 + 9), wob(t, 1.3, i * 0.37 + 17)]) * 0.006
        if run < 0: P[i] = K_P0[i] + j; continue
        d0 = run - 0.25 * K_ORDER[i]                              # they leave in a rush, a few at a time
        if d0 <= 0: P[i] = K_P0[i] + j; continue
        u0 = min(d0 / 0.25, 1.0); ve = along(K_SIDE[i], K_ENTRY[i])
        if u0 < 1.0: P[i] = K_P0[i] + (ve - K_P0[i]) * sm(u0) + j; continue
        d = K_ENTRY[i] + (d0 - 0.25) * 1.9; A_end = float(_VARC[K_SIDE[i]][-1])
        if d >= A_end: P[i] = np.array(HEART_C) + np.array([wob(t, 2, i), wob(t, 2, i + 5), wob(t, 2, i + 11)]) * 0.04; sc[i] *= max(0.0, 1.0 - (d - A_end) * 3.0); continue
        P[i] = along(K_SIDE[i], d) + j * 0.5
    V_ = np.repeat(P, NI, 0) + np.tile(ICO_V, (NK, 1)) * np.repeat(sc, NI)[:, None]
    KMESH.data.vertices.foreach_set('co', V_.ravel().astype(np.float32)); KMESH.data.update()
XRAY = [HEART, KMESH, CAVA[0]] + [v[0] for v in VEINS.values()]
for o in XRAY: o.hide_render = True
BEAM_MATS = [BEAM.material_slots[0].material]
def xray(on):
    for o in XRAY: o.hide_render = not on
    for o in (SUIT, HAIR) + tuple(HEADBITS): o.hide_render = on
    for i_, sl in enumerate(BODY.material_slots): sl.material = XSKIN if on else BODY_MATS[i_]
    BEAM.material_slots[0].material = GHOST_M if on else BEAM_MATS[0]
# IV: a bag hung on the bent rebar, a line down to the inside of his right forearm, taped; fluid runs down it ('ph')
def iv_build():
    pinned(0.0)
    a_ = Vector(wpos('lowerarm02.R')); b_ = Vector(wpos('wrist.R')); mid = a_.lerp(b_, 0.55)
    W_, RP_ = body_eval(); d = np.linalg.norm(W_ - np.array(mid), axis=1); near = W_[d < 0.05]; top = near[np.argmax(near[:, 2])]
    entry = Vector(top) + V3(0, 0, 0.004)
    bag_c = V3(M0.x - 0.48, M0.y + 0.4, 1.28)
    BAG_M = mat('ivbag', (0.85, 0.9, 0.95), 0.08, trans=0.9, ior=1.4)
    bag = box('iv_bag', (0.13, 0.04, 0.22), bag_c, BAG_M, 0.02, ss=2)
    FLUID_M = emis('iv_fluid', (0.75, 0.9, 1.0), 1.2)
    fluid = box('iv_fluid', (0.11, 0.025, 0.16), bag_c - V3(0, 0, 0.02), FLUID_M, 0.015)
    hook = tube('iv_hook', [bag_c + V3(0, 0, 0.11), bag_c + V3(0, 0, 0.17), V3(M0.x - 0.5, M0.y + 0.4, 1.45)], 0.003, STEEL_M, seg=6)
    chamber = box('iv_chamber', (0.022, 0.022, 0.06), bag_c - V3(0, 0, 0.16), BAG_M, 0.008, ss=1)
    p0 = bag_c - V3(0, 0, 0.19); p3 = entry; c1 = p0 + V3(0.02, -0.05, -0.45); c2 = entry + V3(0.0, 0.0, 0.18)
    pts = [p0 * (1 - u) ** 3 + c1 * 3 * u * (1 - u) ** 2 + c2 * 3 * u * u * (1 - u) + p3 * u ** 3 for u in np.linspace(0, 1, 50)]
    line_m = flow_mat('iv_flow', (0.7, 0.9, 1.0), 25.0)
    line, arc = vtube('iv_line', pts, 0.0028, line_m); line.visible_shadow = True
    tape = box('iv_tape', (0.045, 0.035, 0.003), entry + V3(0, 0, 0.002), mat('tape', (0.9, 0.9, 0.86), 0.7), 0.003)
    DROP = prim('uv_sphere', 'iv_drop', mat('drop', (0.8, 0.9, 1.0), 0.05, trans=1.0, ior=1.33), loc=bag_c - V3(0, 0, 0.14), segments=12, ring_count=8, radius=0.004)
    return [bag, fluid, hook, chamber, line, tape, DROP], line, DROP, bag_c
IV, IV_LINE, IV_DROP, IV_BAG = iv_build()
for o in IV: o.hide_render = True
