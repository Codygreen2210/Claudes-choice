# ================================================================ THE CEILING COMES DOWN (collapse clock cc: 0 = frame one; pieces with
# a negative release time are already falling at frame one, so the end of the last beat runs straight into it)
G_ = 9.81
# ceiling tiles (a grid; the middle ones drop), joists above them (the middle ones break and sag), bricks from the floor above
CEIL_TILES = []; _rc = random.Random(11)
for i in range(10):
    for j in range(7):
        x = -SX + 0.3 + i * 0.6; y = -SY + 0.6 + j * 1.2 - 0.0
        if j == 6: continue
        o = box('ctile%d_%d' % (i, j), (0.58, 1.18, 0.025), V3(x, y, SH - 0.0125), CEIL_M)
        CEIL_TILES.append(o)
STORE[1].hide_render = True                                         # the solid ceiling is replaced by the tile grid
VOID_M = mat('void', (0.03, 0.028, 0.025), 0.95)
STORE.append(box('above', (2 * SX, 2 * SY, 0.05), V3(0, 0, SH + 0.6), VOID_M)); ABOVE = STORE[-1]     # the dark underside of the floor above
JOISTS = [box('joist%d' % k, (0.06, 2 * SY, 0.26), V3(-SX + 0.2 + k * 0.4, 0, SH + 0.2), WOOD_M) for k in range(15)]
STORE += JOISTS
for o in JOISTS: o['x0'] = o.location.x
PIECES = []                                                          # (object, p0, v0, rot0, w, release, rest_z)
def add_piece(o, p0, s_, v0=(0, 0, 0), w=(0, 0, 0), rest=None):
    o.rotation_mode = 'XYZ'; PIECES.append(dict(o=o, p0=Vector(p0), v0=Vector(v0), r0=Vector(o.rotation_euler), w=Vector(w), s=s_, rest=rest)); return o
def far_from_him(x, y, r=0.55): return (Vector((x, y)) - M0.xy).length > r
# the tiles over the middle fall first, the one right over his head last (still above him when the beat cuts)
DROP_TILES = []
for o in CEIL_TILES:
    x, y = o.location.x, o.location.y
    if abs(x - M0.x) < 1.3 and abs(y - M0.y) < 2.6:
        over_him = abs(x - M0.x) < 0.31 and abs(y - M0.y) < 0.6
        s_ = 1.5 if over_him else _rc.uniform(-0.75, 1.1)
        near = (Vector((x, y)) - M0.xy).length < 1.05
        w = (0, 0, 0) if over_him else ((_rc.uniform(-0.4, 0.4), _rc.uniform(-0.4, 0.4), 0) if near else (_rc.uniform(-3, 3), _rc.uniform(-3, 3), _rc.uniform(-1, 1)))
        add_piece(o, o.location.copy(), s_, (0, 0, 0) if near else (_rc.uniform(-0.3, 0.3), _rc.uniform(-0.3, 0.3), 0), w, 0.02); DROP_TILES.append(o)
        if over_him: HEAD_TILE = o
# bricks and plaster chunks raining down from the gap (kept out of a circle round him; he isn't hit on screen)
BRICKS = []
for k in range(90):
    while True:
        x = _rc.uniform(-1.05, 1.25); y = M0.y + _rc.uniform(-2.4, 2.0)
        if far_from_him(x, y, 0.62): break
    if _rc.random() < 0.7:
        o = box('fbrick%d' % k, (0.2, 0.095, 0.06), V3(x, y, SH + 0.3), LOOSE_BRICK_M, 0.006); rz = 0.03
    else:
        s3 = _rc.uniform(0.12, 0.3); o = prim('ico_sphere', 'chunk%d' % k, PLASTER_M, loc=V3(x, y, SH + 0.3), subdivisions=1, radius=s3, scale=(1, _rc.uniform(0.5, 1), _rc.uniform(0.3, 0.6))); rz = s3 * 0.35
    o.rotation_euler = (_rc.uniform(0, 6), _rc.uniform(0, 6), _rc.uniform(0, 6))
    add_piece(o, V3(x, y, SH + _rc.uniform(0.1, 0.9)), _rc.uniform(-0.8, 1.6), (_rc.uniform(-0.4, 0.4), _rc.uniform(-0.4, 0.4), _rc.uniform(-1, 0)),
              (_rc.uniform(-8, 8), _rc.uniform(-8, 8), _rc.uniform(-4, 4)), rz); BRICKS.append(o)
# the troffer over him swings down on one wire and sparks (its glow flickers)
SWING = TROFFERS[3]; SWING['y0'] = SWING.location.y
FALLERS = [p['o'] for p in PIECES]
def fall(cc):
    """place every falling piece at collapse-clock time cc"""
    for p in PIECES:
        tau = cc - p['s']; o = p['o']
        if tau <= 0: o.location = p['p0']; o.rotation_euler = p['r0']; continue
        z = p['p0'].z + p['v0'].z * tau - 0.5 * G_ * tau * tau
        if z <= p['rest']:                                          # landed: solve the landing time, freeze there
            a_, b_, c_ = -0.5 * G_, p['v0'].z, p['p0'].z - p['rest']; tl = (-b_ - math.sqrt(b_ * b_ - 4 * a_ * c_)) / (2 * a_); tau = tl; z = p['rest']
        o.location = V3(p['p0'].x + p['v0'].x * tau, p['p0'].y + p['v0'].y * tau, z); o.rotation_euler = p['r0'] + p['w'] * tau
    for o in JOISTS:                                                  # middle joists crack and sag in a V
        k = max(0.0, 1 - abs(o['x0'] - M0.x) / 1.3)
        o.rotation_euler = (0, R(9) * k * (1 if o['x0'] > M0.x else -1) * smooth(-0.9, 0.4, cc), 0); o.location.z = SH + 0.2 - 0.32 * k * smooth(-0.9, 0.6, cc)
    a_ = smooth(-0.3, 0.6, cc); SWING.rotation_euler = (R(-55) * a_ + R(6) * math.sin(cc * 9) * a_, 0, 0); SWING.location.z = SH - 0.02 - 0.32 * a_
# grit: one mesh of small specks raining through the gap (moved every frame)
NGRIT = 500; _gr = np.random.default_rng(5)
GR_P0 = np.stack([_gr.uniform(-1.1, 1.3, NGRIT), M0.y + _gr.uniform(-2.6, 2.2, NGRIT), SH + _gr.uniform(0.0, 0.6, NGRIT)], 1)
GR_S = _gr.uniform(-1.0, 3.5, NGRIT); GR_R = _gr.uniform(0.004, 0.014, NGRIT); GR_V = _gr.uniform(0.2, 1.0, NGRIT)
_tet = np.array([(1, 1, 1), (-1, -1, 1), (-1, 1, -1), (1, -1, -1)], float) / 1.732
GRIT = mesh('grit', [tuple(v) for v in np.repeat(GR_P0, 4, 0) + np.tile(_tet, (NGRIT, 1)) * np.repeat(GR_R, 4)[:, None]],
            [(4 * i, 4 * i + 1, 4 * i + 2) for i in range(NGRIT)] + [(4 * i, 4 * i + 3, 4 * i + 1) for i in range(NGRIT)] + [(4 * i, 4 * i + 2, 4 * i + 3) for i in range(NGRIT)] + [(4 * i + 1, 4 * i + 3, 4 * i + 2) for i in range(NGRIT)],
            mat('grit', (0.55, 0.52, 0.47), 0.95), smooth_=False)
GRIT.visible_shadow = False
def grit(cc, rate=1.0):
    tau = np.clip(cc - GR_S, 0, None) * GR_V
    P = GR_P0.copy(); P[:, 2] = np.where(tau > 0, GR_P0[:, 2] - (0.5 * G_ * (tau % 0.95) ** 2) * rate, GR_P0[:, 2]); P[:, 2] = np.maximum(P[:, 2], 0.01)
    V_ = np.repeat(P, 4, 0) + np.tile(_tet, (NGRIT, 1)) * np.repeat(GR_R, 4)[:, None]; GRIT.data.vertices.foreach_set('co', V_.ravel().astype(np.float32)); GRIT.data.update()
# dust: soft see-through cards that billow (noise moves with 'tt'); kept in front of the far wall
def dust_mat(name, col=(0.62, 0.58, 0.52), dens=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 4
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 0.25), nz.inputs['W'])
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; nt.links.new(tc.outputs['Generated'], gr.inputs['Vector'])
    # generated coords run 0..1; centre the sphere
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-0.5, -0.5, -0.5); mp.inputs['Scale'].default_value = (2, 2, 2)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
    a_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', gr.outputs['Fac'], 1.5), math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', nz.outputs['Fac'], 0.38), 0.0)), objattr(nt, 'dens'))
    a_ = math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', a_, 4.0 * dens), 0.85)
    df = nt.nodes.new('ShaderNodeBsdfDiffuse'); df.inputs['Color'].default_value = (*col, 1)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = 0.08
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(df.outputs['BSDF'], ad.inputs[0]); nt.links.new(em.outputs['Emission'], ad.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(a_, mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(ad.outputs['Shader'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None; return m
DUST_M = dust_mat('dust')
DUST = []
for k in range(5):
    o = prim('plane', 'dust%d' % k, DUST_M, size=1.0); o.scale = (3.2, 3.2, 1); o['tt'] = 0.0; o['dens'] = 0.0; o.visible_shadow = False
    o['k'] = k; DUST.append(o)
def dust(cc_or_t, dens, center, cam_pos, spread=1.0, rise=0.0):
    """cards face the camera, spread round 'center'"""
    for o in DUST:
        k = o['k']; off = V3(math.sin(k * 2.1) * 0.9, math.cos(k * 1.7) * 0.9, 0.3 * (k - 2)) * spread + V3(0, 0, rise * (0.3 + 0.2 * k) * cc_or_t)
        o.location = Vector(center) + off; d_ = Vector(cam_pos) - o.location; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d_.to_track_quat('Z', 'Y')
        o['tt'] = cc_or_t + k * 3.1; o['dens'] = dens; o.scale = (3.2 * spread, 3.2 * spread, 1)
