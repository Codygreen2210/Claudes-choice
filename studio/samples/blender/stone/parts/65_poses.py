
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
    FOOT[s_] = (e_, RB['foot.' + s_].matrix_local.to_3x3())
def hand_out(sides=('R',), passes=6, keep=0.0015):
    """a hand that sank into his shirt/shorts is pushed back out along the cloth's normal"""
    T_ = suit_bvh()
    for _ in range(passes):
        W, RP = body_eval(); moved = False
        for s_ in sides:
            sg = -1.0 if s_ == 'R' else 1.0; hm = np.where(RP[:, 0] * sg > 0.44)[0]; pen, nrm = 0.0, Vector()
            for i in hm[::2]:
                p = Vector(W[i]); loc, nor, _, d = T_.find_nearest(p, 0.05)
                if loc is not None and (p - loc).dot(nor) < 0 and d > pen: pen, nrm = d, nor
            if pen > 0.0005: TGT['hand' + s_].location += nrm * (pen + keep); moved = True; HO_LOG.append((s_, round(pen, 4)))
        if not moved: return
        bpy.context.view_layer.update()
def hand_on_top(passes=5):
    """his left hand rests on the countertop: lowest point of the hand (fingertips, heel of the palm) just touching it"""
    for _ in range(passes):
        W, RP = body_eval(); m_ = (RP[:, 0] > 0.36) & (W[:, 0] > CX0 - 0.002)
        if not m_.any(): return
        d = clamp(CTOP + 0.001 - float(W[m_, 2].min()), -0.02, 0.02)
        if abs(d) < 0.0004: return
        TGT['handL'].location.z += d; bpy.context.view_layer.update()
# ================================================================ THE POSES. S: standing at the counter. A: the pain hits (bends, grabs his
# right side). B: on his knees (toes tucked under), left hand holding the counter, right hand pressed to his side.
TOE_SIGN = 1.0
BALL_Y = -0.13                                                        # where the balls of his feet stay planted (world y)
FLANK = V3(-0.142, -0.035, 1.065)                                     # rig space: his right side over the kidney
def P_S():
    return dict(hip=V3(0, 0, 0.858), rot=V3(0, 0, 0), neck=5.0, head=0.0, phi=0.0, pole=V3(0.19, -1.5, 0.5), lids=0.0, jaw=0.0, toe=0.0,
                hR=('rig', V3(-0.25, 0.0, 0.78), V3(0, -0.2, -1), V3(1, 0, 0), 0.0), paR=V3(-0.5, 0.9, 1.0), curlR=0.35,
                hL=('world', V3(CX0 + 0.04, -0.1, CTOP + 0.004), V3(0.12, -1, 0), V3(0, 0, -1), 1.0), paL=V3(0.5, 0.9, 1.1), curlL=-0.2, kneel=0.0)
def P_A():
    return dict(hip=V3(0, 0.02, 0.8), rot=V3(14, 0, -3), neck=22.0, head=12.0, phi=0.0, pole=V3(0.19, -1.5, 0.5), lids=1.0, jaw=0.5, toe=0.0,
                hR=('rig', FLANK, V3(0.1, -0.75, -0.65), V3(1, 0, 0), 1.0), paR=V3(-0.7, 0.7, 1.2), curlR=0.3,
                hL=('world', V3(CX0 + 0.04, -0.16, CTOP + 0.004), V3(0.12, -1, 0), V3(0, 0, -1), 1.0), paL=V3(0.5, 0.9, 1.1), curlL=-0.2, kneel=0.0)
def P_B():
    return dict(hip=V3(0, -0.6, 0.47), rot=V3(20, 0, -5), neck=32.0, head=14.0, phi=88.0, pole=V3(0.19, -2.2, 0.1), lids=1.0, jaw=0.6, toe=-80.0,
                hR=('rig', FLANK, V3(0.1, -0.75, -0.65), V3(1, 0, 0), 1.0), paR=V3(-0.7, 0.7, 1.2), curlR=0.35,
                hL=('world', V3(CX0 + 0.04, -0.74, CTOP + 0.004), V3(0.12, -1, 0), V3(0, 0, -1), 1.0), paL=V3(0.55, 0.6, 1.1), curlL=-0.2, kneel=1.0)
def _mix(a_, b_, k):
    if isinstance(a_, tuple): return (a_[0],) + tuple(_mix(x, y, k) for x, y in zip(a_[1:], b_[1:]))
    return a_ + (b_ - a_) * k
def blend(PA, PB_, k): return {n: _mix(PA[n], PB_[n], k) for n in PA}
def ankle_for(phi, sg):
    """ankle over the planted ball of the foot: phi = how far the foot has tipped up onto its toes (deg)"""
    c_, s_ = math.cos(R(phi)), math.sin(R(phi)); return V3(sg * 0.135, BALL_Y + 0.13 * c_ - 0.06 * s_, 0.012 + 0.055 * c_ + 0.133 * s_)
def apply(P, shudder=0.0, t=0.0, lift=0.0):
    rot = P['rot'] + V3(wob(t, 3.0, 1.0), wob(t, 3.0, 2.0), wob(t, 3.0, 3.0)) * shudder
    set_pose(P['hip'], tuple(rot), 0.0, P['neck'], P['head'], 0.0, 0.0,
             ankR=ankle_for(P['phi'], -1), poleR=V3(-P['pole'].x, P['hip'].y + P['pole'].y, P['pole'].z), ankL=ankle_for(P['phi'], 1), poleL=V3(P['pole'].x, P['hip'].y + P['pole'].y, P['pole'].z),
             curlR=P['curlR'], curlL=P['curlL'], lids=P['lids'], jaw=P['jaw'])
    for s_ in 'RL': FOOT[s_][0].rotation_quaternion = (Matrix.Rotation(R(P['phi']), 3, 'X') @ FOOT[s_][1]).to_quaternion()
    for f_ in range(1, 6):
        for s_ in 'RL':
            if f'toe{f_}-1.{s_}' in PB: rot_ = TOE_SIGN * min(P['phi'], 82.0); PB[f'toe{f_}-1.{s_}'].rotation_mode = 'XYZ'; PB[f'toe{f_}-1.{s_}'].rotation_euler = (R(rot_), 0, 0)
            for seg in (2, 3):
                if f'toe{f_}-{seg}.{s_}' in PB: PB[f'toe{f_}-{seg}.{s_}'].rotation_mode = 'XYZ'; PB[f'toe{f_}-{seg}.{s_}'].rotation_euler = (0, 0, 0)
    M = RIG.matrix_world.copy(); M3 = M.to_3x3()
    for s_, key, pk in (('R', 'hR', 'paR'), ('L', 'hL', 'paL')):
        sp, c, fd, pd, w = P[key]
        if sp == 'rig': c, fd, pd = M @ c, M3 @ fd, M3 @ pd
        if s_ == 'R' and lift: c = c + (M3 @ V3(-1, 0.2, 0)) * lift
        place_hand(s_, c, fd, pd, w); TGT['poleArm' + s_].location = M @ P[pk]
    bpy.context.view_layer.update()
    ground(P['kneel']); hand_out(('R',)); hand_on_top()
PS, PA_, PB2 = P_S(), P_A(), P_B()
K0 = 0.07                                                              # frame one: already going down
def man_pose(nb, u, t):
    """which pose at this moment"""
    if nb == 11:
        k = smooth(0.12, 0.8, u); P = blend(PS, PA_, k); lift = 0.04 * math.sin(math.pi * k)
        if u > 0.8: P = blend(PA_, PB2, K0 * smooth(0.8, 1.0, u))
        apply(P, 0.6 * k, t, lift); return
    if nb == 0:
        v = clamp(u / 0.4, 0, 1); k = K0 + (1 - K0) * v ** 1.7; bounce = math.exp(-max(u - 0.4, 0) * 9) * math.sin(max(u - 0.4, 0) * 30) * 0.02 if u > 0.4 else 0.0
        P = blend(PA_, PB2, min(k, 1.0)); P['hip'] = P['hip'] + V3(0, 0, 0.0); P['rot'] = P['rot'] + V3(120 * bounce + 6 * smooth(0.4, 0.9, u), 0, 0)
        apply(P, 0.8 + 0.6 * smooth(0.4, 0.6, u), t); return
    apply(PB2 | {'rot': PB2['rot'] + V3(6, 0, 0)}, 1.0, t)
