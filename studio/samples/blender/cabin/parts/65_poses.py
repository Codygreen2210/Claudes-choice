
# ---- keeping him out of the floor and his hand out of his side (measured on the posed skin, every frame)
def body_eval():
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); rp = rp.reshape(-1, 3); oe.to_mesh_clear()
    M_ = np.array(BODY.matrix_world); return co @ M_[:3, :3].T + M_[:3, 3], rp
def suit_bvh():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles(); M = SUIT.matrix_world
    T_ = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles]); oe.to_mesh_clear(); return T_
def suit_minz():
    dg = bpy.context.evaluated_depsgraph_get(); oe = SUIT.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); oe.to_mesh_clear(); M_ = np.array(SUIT.matrix_world)
    return float((co @ M_[:3, :3].T + M_[:3, 3])[:, 2].min())
def ground(kneel=0.0, passes=4):
    """feet: each ankle goes up or down until that foot just touches the floor. knees: the hips rise if a knee is under the floor,
    and (kneeling) sink until the knees rest on it"""
    for _ in range(passes):
        W, RP = body_eval(); moved = 0.0
        for s_, sg in (('R', -1.0), ('L', 1.0)):
            mn = float(W[(RP[:, 2] < 0.1) & (RP[:, 0] * sg > 0), 2].min()); d = clamp(0.001 - mn, -0.03, 0.03)
            if abs(d) > 0.0004: TGT['ank' + s_].location.z += d; moved = max(moved, abs(d))
        m_ = (RP[:, 2] > 0.25) & (RP[:, 2] < 0.75); kn = min(float(W[m_, 2].min()) if m_.any() else 9.0, suit_minz())      # knees: skin below the shorts, and the shorts
        d = (0.001 - kn) if (kn < 0.001 or kneel > 0.97) else 0.0; d = clamp(d, -0.03, 0.03)
        if abs(d) > 0.0004: RIG.location.z += d; moved = max(moved, abs(d))
        if moved < 0.0005: break
        bpy.context.view_layer.update()
HO_LOG = []
# feet: turned in the world (flat on the floor, or tipped up onto the toes by 'phi'), whatever the shin does
FOOT = {}
for s_ in ('R', 'L'):
    e_ = empty('tgt_foot' + s_); e_.rotation_mode = 'QUATERNION'
    c_ = PB['foot.' + s_].constraints.new('COPY_ROTATION'); c_.target = e_; c_.owner_space = c_.target_space = 'WORLD'
    FOOT[s_] = (e_, RB['foot.' + s_].matrix_local.to_3x3(), c_)
def feet_flat(on=True, phi=0.0):
    for s_ in 'RL':
        e_, M0, c_ = FOOT[s_]; c_.influence = 1.0 if on else 0.0; e_.rotation_quaternion = (Matrix.Rotation(R(phi), 3, 'X') @ M0).to_quaternion()
# ================================================================ HIS POSES (all built from the hip, a body turn, and hands/feet in his own frame)
def rigM(hip, rot):
    Rm = Euler(tuple(R(x) for x in rot)).to_matrix(); return Matrix.Translation(Vector(hip) - Rm @ HIP0) @ Rm.to_4x4()
def body(hip, rot, ankR, ankL, handR, handL, space='rig', neck=0.0, head=0.0, jaw=0.0, lids=0.0, curl=(0.3, 0.3), pk=(1.0, 1.0),
         palm=None, spine=0.0, kneel_pole=False, head_yaw=0.0):
    """space: 'rig' = ankles/hands in his own (rest) frame, moving with him; 'world' for ankles (planted)"""
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
def flail(t, k=1.0, seed=0.0):
    """limbs thrown about by the wind (rig space)"""
    w = lambda f, s_: wob(t, f, seed + s_) * k
    return dict(ankR=V3(-0.2 + 0.12 * w(1.3, 1), 0.15 + 0.25 * w(1.1, 2), 0.12 + 0.18 * w(0.9, 3)), ankL=V3(0.26 + 0.12 * w(1.2, 4), -0.12 + 0.3 * w(1.0, 5), 0.2 + 0.2 * w(0.8, 6)),
                handR=V3(-0.68 + 0.12 * w(1.5, 7), 0.12 + 0.3 * w(1.2, 8), 1.45 + 0.2 * w(1.0, 9)), handL=V3(0.62 + 0.12 * w(1.4, 10), 0.25 + 0.3 * w(1.3, 11), 1.25 + 0.25 * w(0.9, 12)))
STAND_HIP = 0.93
def stand(x, y, yaw, t, brace=0.0, lift=0.0):
    """on his feet by the trailer, facing yaw (deg); brace: knees bend, arms come up over his face; lift: heels leave the ground"""
    hip = V3(x, y, STAND_HIP - 0.12 * brace + lift); rot = (6 * brace + 3 * wob(t, 2, 1) * brace, 0, yaw)
    Rz = Matrix.Rotation(R(yaw), 3, 'Z'); aR = V3(x, y, 0) + Rz @ V3(-0.14, 0.02, 0.09 + lift * 0.9); aL = V3(x, y, 0) + Rz @ V3(0.14, 0.02, 0.09 + lift * 0.9)
    hR = V3(-0.28, 0.02, 0.86).lerp(V3(-0.1, -0.32, 1.62), brace); hL = V3(0.28, 0.02, 0.86).lerp(V3(0.12, -0.33, 1.6), brace)
    Rq = Matrix.Rotation(R(yaw), 3, 'Z')
    for s_ in 'RL': FOOT[s_][2].influence = 1.0; FOOT[s_][0].rotation_quaternion = (Rq @ FOOT[s_][1]).to_quaternion()
    body(hip, rot, aR, aL, hR, hL, space='world', neck=8 * brace, jaw=0.3 * brace, lids=0.5 * brace, curl=(0.3 + 0.5 * brace,) * 2)
    if lift < 0.01: ground(0.0)
def airborne(hip, rot, t, k=1.0, seed=0.0, jaw=0.6):
    feet_flat(False)
    f = flail(t, k, seed); body(hip, rot, f['ankR'], f['ankL'], f['handR'], f['handL'], neck=15 * wob(t, 1, seed), head=10 * wob(t, 1.3, seed), jaw=jaw, lids=0.6, curl=(0.6, 0.6), pk=(-1, -1))
def lying(x, y, sit, t):
    """on his back in the grass, head toward +y; sit 0..1: pushes up on his hands to sitting"""
    feet_flat(False); a = lerp(-88, -35, sm(sit)); hip = V3(x, y, 0.12 + 0.02 * sit); rot = (a, 0, 180)
    M = rigM(hip, rot)
    aR, aL = V3(-0.16, 0.05, 0.1), V3(0.2, 0.0, 0.12)
    hR = V3(-0.4, 0.15, 0.95).lerp(V3(-0.3, 0.32, 0.85), sit); hL = V3(0.42, 0.1, 0.9).lerp(V3(0.3, 0.32, 0.85), sit)
    body(hip, rot, aR, aL, hR, hL, neck=lerp(-5, 15, sit), head=lerp(0, 10, sit), lids=lerp(1.0, 0.1, smooth(0.0, 0.5, sit)), jaw=0.2, curl=(0.5, 0.5), kneel_pole=False)
    W, RP = body_eval(); mn = float(W[:, 2].min()); RIG.location.z += 0.002 - mn; bpy.context.view_layer.update()
def crouch(t, shake_=0.0):
    """in the closet: down on his knees and folded forward, both hands locked over the back of his head"""
    feet_flat(False); hip = CL + V3(0.0, -0.05, 0.42); rot = (68 + 2 * wob(t, 6, 3) * shake_, 0, 0)
    M = rigM(hip, rot); Mi = M.inverted()
    aR = Mi @ (CL + V3(-0.13, 0.32, 0.07)); aL = Mi @ (CL + V3(0.13, 0.32, 0.07))
    body(hip, rot, aR, aL, V3(-0.06, 0.15, 1.6), V3(0.06, 0.15, 1.62), neck=30, head=12, lids=1.0, jaw=0.1, curl=(0.15, 0.15),
         palm={'R': (V3(-0.03, 0.09, 1.71), V3(1, 0.2, -0.2), V3(0, -0.3, -1)), 'L': (V3(0.03, 0.09, 1.71), V3(-1, 0.2, -0.2), V3(0, -0.3, -1))}, kneel_pole=True)
    ground(1.0)
SEAT_HIP = V3(MYSEAT_X, MY + 0.12, 0.55)
def seated(t, lean=-8.0, at=None, handR=None, handL=None, neck=0.0, head=0.0, head_yaw=0.0, lids=0.0, jaw=0.0, curl=(0.35, 0.35), side_lean=0.0, palm=None, bob=0.0):
    """in his window seat (A), facing the nose (-y); hands in his own (rig) frame, default on his thighs"""
    sx_, sy_ = at if at is not None else (MYSEAT_X, MY)
    hip = V3(sx_, sy_ + 0.19, SEAT_HIP.z + 0.004 * bob * math.sin(t * 9)); rot = (lean, side_lean, 0.0)
    aR = V3(sx_ - 0.13, sy_ - 0.36, 0.085); aL = V3(sx_ + 0.13, sy_ - 0.36, 0.085)
    for s_ in 'RL': FOOT[s_][2].influence = 1.0; FOOT[s_][0].rotation_quaternion = FOOT[s_][1].to_quaternion()
    hR = handR if handR is not None else V3(-0.17, -0.36, 0.98); hL = handL if handL is not None else V3(0.17, -0.36, 0.98)
    body(hip, rot, aR, aL, hR, hL, space='world', neck=neck, head=head, head_yaw=head_yaw, lids=lids, jaw=jaw, curl=curl, palm=palm, pk=(1.0, 1.0))
