# ================================================================ HIS POSES (built from the hip, a body turn, and hands/feet in his own frame)
def body_eval():
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); rp = rp.reshape(-1, 3); oe.to_mesh_clear()
    M_ = np.array(BODY.matrix_world); return co @ M_[:3, :3].T + M_[:3, 3], rp
FOOT = {}
for s_ in ('R', 'L'):
    e_ = empty('tgt_foot' + s_); e_.rotation_mode = 'QUATERNION'
    c_ = PB['foot.' + s_].constraints.new('COPY_ROTATION'); c_.target = e_; c_.owner_space = c_.target_space = 'WORLD'
    FOOT[s_] = (e_, RB['foot.' + s_].matrix_local.to_3x3(), c_)
def feet_flat(on=True, phi=0.0):
    for s_ in 'RL':
        e_, M0_, c_ = FOOT[s_]; c_.influence = 1.0 if on else 0.0; e_.rotation_quaternion = (Matrix.Rotation(R(phi), 3, 'X') @ M0_).to_quaternion()
def rigM(hip, rot):
    Rm = Euler(tuple(R(x) for x in rot)).to_matrix(); return Matrix.Translation(Vector(hip) - Rm @ HIP0) @ Rm.to_4x4()
def body(hip, rot, ankR, ankL, handR, handL, space='rig', neck=0.0, head=0.0, jaw=0.0, lids=0.0, curl=(0.3, 0.3), pk=(1.0, 1.0),
         palm=None, spine=0.0, kneel_pole=False, head_yaw=0.0):
    M = rigM(hip, rot); M3 = M.to_3x3()
    aR = M @ Vector(ankR) if space == 'rig' else Vector(ankR); aL = M @ Vector(ankL) if space == 'rig' else Vector(ankL)
    kp = V3(0, -2.0, 0.4) if not kneel_pole else V3(0, -2.0, -0.6)
    set_pose(hip, rot, spine, neck, head, head_yaw, 0.0, ankR=aR, poleR=M @ (V3(-0.15, 0, 0.5) + kp), ankL=aL, poleL=M @ (V3(0.15, 0, 0.5) + kp),
             curlR=curl[0], curlL=curl[1], lids=lids, jaw=jaw, poleArmR=M @ V3(-0.8, 0.6 * pk[0], 1.0), poleArmL=M @ V3(0.8, 0.6 * pk[1], 1.0))
    for s_, hp_ in (('R', handR), ('L', handL)):
        if palm and s_ in palm:
            c_, fd, pd = palm[s_]; place_hand(s_, M @ Vector(c_), M3 @ Vector(fd), M3 @ Vector(pd), 1.0)
        else: TGT['hand' + s_].location = M @ Vector(hp_); HAND[s_][2].influence = 0.0
    bpy.context.view_layer.update(); return M
STAND_HIP = 0.93
def stand(t, look_up=0.0, brace=0.0, yaw=0.0):
    """in the aisle at M0, facing -y (+yaw turns him); look_up tips his head back to the ceiling; brace: knees bend, arms over his head"""
    x, y = M0.x, M0.y
    hip = V3(x, y, STAND_HIP - 0.1 * brace); rot = (4 * brace + 1.5 * wob(t, 3, 1) * brace, 0, yaw)
    Rz = Matrix.Rotation(R(yaw), 3, 'Z'); aR = V3(x, y, 0) + Rz @ V3(-0.14, 0.02, 0.09); aL = V3(x, y, 0) + Rz @ V3(0.14, 0.02, 0.09)
    hR = V3(-0.27, 0.02, 0.86).lerp(V3(-0.14, -0.2, 1.86), brace); hL = V3(0.27, 0.02, 0.86).lerp(V3(0.14, -0.18, 1.84), brace)
    for s_ in 'RL': FOOT[s_][2].influence = 1.0; FOOT[s_][0].rotation_quaternion = (Rz @ FOOT[s_][1]).to_quaternion()
    body(hip, rot, aR, aL, hR, hL, space='world', neck=-14 * look_up + 6 * brace, head=-18 * look_up, jaw=0.25 * look_up + 0.25 * brace,
         lids=0.45 * brace, curl=(0.25 + 0.45 * brace,) * 2, pk=(1 - 1.6 * brace, 1 - 1.6 * brace))
    ground(0.0)
PIN_HIP = V3(M0.x, M0.y, 0.12)
def pinned(t, wince=0.0, look=0.0, armL=None):
    """on his back on the store floor, head toward +y; right arm out on the floor by his shoulder (the IV goes in there), left hand
    on his chest; legs straight under the rubble. Small moves only (the mound and the beam are built round this pose)"""
    feet_flat(False); hip = PIN_HIP.copy(); rot = (-88, 0, 0)
    aR, aL = V3(-0.13, 0.04, 0.1), V3(0.15, 0.02, 0.1)
    hR = V3(-0.62, 0.06, 1.22); hL = armL if armL is not None else V3(0.45, 0.06, 0.95)
    body(hip, rot, aR, aL, hR, hL, neck=lerp(-6, 8, look) + 3 * wob(t, 0.6, 2), head=lerp(0, 14, look), head_yaw=8 * wob(t, 0.4, 5),
         lids=lerp(0.35, 0.85, wince), jaw=lerp(0.1, 0.45, wince), curl=(0.35, 0.55), pk=(0.4, 0.4))
def deform(rest_pt, bone):
    """a point given in his rest space, carried along by one bone (world)"""
    pb = PB[bone]; return RIG.matrix_world @ (pb.matrix @ RB[bone].matrix_local.inverted()) @ Vector(rest_pt)
def ground(kneel=0.0, passes=4):
    for _ in range(passes):
        W, RP = body_eval(); moved = 0.0
        for s_, sg in (('R', -1.0), ('L', 1.0)):
            mn = float(W[(RP[:, 2] < 0.1) & (RP[:, 0] * sg > 0), 2].min()); d = clamp(0.001 - mn, -0.03, 0.03)
            if abs(d) > 0.0004: TGT['ank' + s_].location.z += d; moved = max(moved, abs(d))
        if moved < 0.0005: break
        bpy.context.view_layer.update()

# ================================================================ THE PILE ON HIM (built once, round the pinned pose, so nothing goes through him)
def skin_points():
    """posed skin of the body and the clothes (world, numpy)"""
    out = []
    for o in (BODY, SUIT):
        dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
        co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); oe.to_mesh_clear(); M_ = np.array(o.matrix_world)
        out.append(co @ M_[:3, :3].T + M_[:3, 3])
    return np.concatenate(out)
pinned(0.0); bpy.context.view_layer.update()
_W, _RP = body_eval(); BODY_MINZ = float(_W[:, 2].min()); RIG.location.z += 0.003 - BODY_MINZ; PIN_HIP.z += 0.003 - BODY_MINZ; bpy.context.view_layer.update()
SKIN = skin_points()
MOUND_Y1 = M0.y - 0.16                                       # the mound covers him from mid-thigh (this y) down past his feet
GX0, GX1, GY0, GY1, GH = M0.x - 0.95, M0.x + 0.95, M0.y - 1.45, MOUND_Y1, 0.02
nx_, ny_ = int(round((GX1 - GX0) / GH)) + 1, int(round((GY1 - GY0) / GH)) + 1
TOP = np.full((nx_, ny_), -1.0)
_ix = np.round((SKIN[:, 0] - GX0) / GH).astype(int); _iy = np.round((SKIN[:, 1] - GY0) / GH).astype(int)
_ok = (_ix >= 0) & (_ix < nx_) & (_iy >= 0) & (_iy < ny_)
np.maximum.at(TOP, (_ix[_ok], _iy[_ok]), SKIN[_ok, 2])
from scipy.ndimage import maximum_filter, gaussian_filter
COVER = maximum_filter(TOP, size=7); COVER = np.where(COVER > 0, COVER + 0.04, 0.0)
_xs = np.linspace(GX0, GX1, nx_)[:, None]; _ys = np.linspace(GY0, GY1, ny_)[None, :]
_rn = np.random.default_rng(3)
PROF = 0.36 * np.exp(-((_xs - M0.x) / 0.5) ** 2) * (0.8 + 0.2 * np.sin(_ys * 7.0)) * np.clip((GY1 - _ys) / 0.12, 0, 1) ** 0.5
PROF *= np.clip((_ys - GY0) / 0.35, 0, 1) ** 0.7
PROF += gaussian_filter(_rn.normal(0, 0.05, (nx_, ny_)), 1.2) * (PROF > 0.02)
H = np.maximum(gaussian_filter(np.maximum(COVER, PROF), 1.0), COVER)
H = np.maximum(H, 0.0)
def mound_h(x, y):
    i = int(round((x - GX0) / GH)); j = int(round((y - GY0) / GH))
    if 0 <= i < nx_ and 0 <= j < ny_: return float(H[i, j])
    return 0.0
_vs = [(GX0 + i * GH, GY0 + j * GH, float(H[i, j]) - 0.004) for i in range(nx_) for j in range(ny_)]
_fs = [(i * ny_ + j, (i + 1) * ny_ + j, (i + 1) * ny_ + j + 1, i * ny_ + j + 1) for i in range(nx_ - 1) for j in range(ny_ - 1)]
def rubble_mat():
    m = mat('rubble', (0.42, 0.36, 0.3), 0.95); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 22.0; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); el = cr.color_ramp.elements
    el[0].color = (0.32, 0.12, 0.08, 1); el[1].color = (0.62, 0.6, 0.55, 1); el.new(0.45).color = (0.25, 0.22, 0.2, 1); el.new(0.7).color = (0.48, 0.2, 0.12, 1)
    nt.links.new(vo.outputs['Color'], cr.inputs['Fac']) if False else nt.links.new(vo.outputs['Distance'], cr.inputs['Fac'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60.0; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.5
    nt.links.new(cr.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.9; bp.inputs['Distance'].default_value = 0.03
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
RUBBLE_M = rubble_mat()
MOUND = mesh('mound', _vs, _fs, RUBBLE_M)
MOUND_H0 = np.array(_vs)[:, 2].copy()
# bricks and chunks sitting on the mound (above it; the mound is above him), and strewn round him on the floor (not on him)
PILE = []
_pr = random.Random(21); _occ = np.zeros((int(4.0 / 0.05), int(6.0 / 0.05)), bool)
def on_body(x, y, r=0.16):
    d = np.hypot(SKIN[:, 0] - x, SKIN[:, 1] - y); return bool((d < r).any())
for k in range(70):
    x = M0.x + _pr.uniform(-0.75, 0.75); y = _pr.uniform(GY0 + 0.1, GY1 - 0.05)
    h0 = mound_h(x, y)
    if h0 < 0.04: continue
    hz = max(h0, mound_h(x + 0.1, y), mound_h(x - 0.1, y), mound_h(x, y + 0.05), mound_h(x, y - 0.05))
    o = box('pbrick%d' % k, (0.2, 0.095, 0.06), V3(x, y, hz + 0.028), LOOSE_BRICK_M, 0.006, rot=(R(_pr.uniform(-12, 12)), R(_pr.uniform(-12, 12)), R(_pr.uniform(0, 180))))
    PILE.append(o)
for k in range(140):
    x = M0.x + _pr.uniform(-1.3, 1.3); y = M0.y + _pr.uniform(-2.0, 1.9)
    if on_body(x, y, 0.22) or (GX0 < x < GX1 and GY0 < y < GY1 + 0.15): continue
    if _pr.random() < 0.65: o = box('fbr%d' % k, (0.2, 0.095, 0.06), V3(x, y, 0.03), LOOSE_BRICK_M, 0.006, rot=(0, 0, R(_pr.uniform(0, 180))))
    else:
        s3 = _pr.uniform(0.08, 0.22); o = prim('ico_sphere', 'fch%d' % k, PLASTER_M, loc=V3(x, y, s3 * 0.25), subdivisions=1, radius=s3, scale=(1, _pr.uniform(0.6, 1), 0.35))
    PILE.append(o)
# the broken ceiling tiles leaning on the pile, a cracked joist on the floor beyond his head
for k in range(8):
    x = M0.x + _pr.choice((-1, 1)) * _pr.uniform(0.6, 1.2); y = M0.y + _pr.uniform(-1.6, 1.6)
    if on_body(x, y, 0.5): continue
    PILE.append(box('ptile%d' % k, (0.58, 0.58, 0.025), V3(x, y, 0.18), CEIL_M, rot=(R(_pr.uniform(-35, 35)), R(_pr.uniform(-35, 35)), R(_pr.uniform(0, 90)))))
# THE BEAM: a heavy timber across his thighs, resting on the mound's top edge, the far end down on the floor
BEAM_Y = MOUND_Y1 - 0.12
_xB = M0.x + 1.75; _xL = M0.x - 0.6
_hs = [(x_, max(mound_h(x_, y_) for y_ in np.linspace(BEAM_Y - 0.11, BEAM_Y + 0.11, 12))) for x_ in np.linspace(_xL, _xB, 120)]
_slope = max(h_ / max(_xB - x_, 1e-3) for x_, h_ in _hs) + 0.004           # the beam's underside just touches the highest point of the pile
_zL = _slope * (_xB - _xL); _len = math.hypot(_xB - _xL, _zL); _ang = math.atan2(_zL, _xB - _xL)
BEAM = box('beam', (_len, 0.2, 0.24), V3(0, 0, 0), OLDWOOD_M, 0.01)
_mid = V3((_xL + _xB) / 2, BEAM_Y, _zL / 2); _nrm = V3(math.sin(_ang), 0, math.cos(_ang))
BEAM.rotation_euler = (0, _ang, 0); BEAM.location = _mid + _nrm * 0.12
BEAM0 = BEAM.matrix_world.copy()
STRAP_M = noisy(mat('rebar', (0.3, 0.16, 0.08), 0.7, metal=0.6), 50.0, 0.4)
REBAR = tube('rebar', [V3(M0.x - 0.95, M0.y + 0.6, 0.0), V3(M0.x - 0.85, M0.y + 0.55, 0.9), V3(M0.x - 0.7, M0.y + 0.45, 1.3), V3(M0.x - 0.5, M0.y + 0.4, 1.45)], 0.012, STRAP_M, seg=8)
PINNED_SET = [MOUND, BEAM] + PILE
