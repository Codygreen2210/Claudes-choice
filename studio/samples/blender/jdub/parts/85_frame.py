# ================================================================ HIM: the landing as story time s (seconds of the real play)
BASE = V3(0.45, 1.25, 0.0)                     # where he comes down; he faces the hoop (+y)
def Wd(x, y, z): return BASE + V3(-x, -y, z)    # his own frame (he faces -y, left = +x) -> the court
KEYS = [  # s, pose (his frame: left = +x, forward = -y)
    (0.00, dict(hip=(0.0, 0.02, 1.45), lean=-6, side=0, spine=6, head=-8, ankL=(0.11, -0.04, 0.66), poleL=(0.15, -1.0, 0.95), ankR=(-0.12, 0.17, 0.92), poleR=(-0.15, -1.0, 1.3),
                handL=(0.17, -0.2, 2.25), handR=(-0.13, -0.24, 2.3), ev=0.0, plant=0.0)),
    (0.45, dict(hip=(0.03, 0.0, 0.93), lean=6, side=-4, spine=12, head=0, ankL=(0.13, -0.03, 0.075), poleL=(0.2, -1.0, 0.6), ankR=(-0.14, 0.2, 0.42), poleR=(-0.2, -1.0, 0.8),
                handL=(0.47, -0.12, 1.55), handR=(-0.44, -0.16, 1.6), ev=0.0, plant=1.0)),
    (0.72, dict(hip=(0.22, 0.03, 0.55), lean=12, side=-22, spine=16, head=6, ankL=(0.13, -0.03, 0.075), poleL=(-0.6, -1.0, 0.45), ankR=(-0.2, 0.12, 0.2), poleR=(-0.3, -1.0, 0.6),
                handL=(0.62, -0.25, 0.95), handR=(-0.5, -0.3, 1.05), ev=1.0, plant=1.0)),
    (1.10, dict(hip=(0.32, 0.10, 0.2), lean=-18, side=-8, spine=8, head=10, ankL=(0.26, -0.55, 0.085), poleL=(0.45, -1.0, 0.75), ankR=(-0.1, -0.32, 0.085), poleR=(-0.3, -1.0, 1.0),
                handL=(0.68, 0.3, 0.06), handR=(-0.02, 0.3, 0.06), ev=1.0, plant=0.0)),
    (1.80, dict(hip=(0.32, 0.12, 0.12), lean=-24, side=-4, spine=6, head=16, ankL=(0.32, -0.66, 0.085), poleL=(0.4, -1.0, 1.0), ankR=(0.0, -0.38, 0.085), poleR=(-0.25, -1.0, 1.25),
                handL=(0.68, 0.38, 0.0), handR=(-0.03, 0.38, 0.0), ev=1.0, plant=0.0)),
]
S_END = KEYS[-1][0]
def pose_at(s):
    s = clamp(s, 0.0, S_END)
    for i in range(len(KEYS) - 1):
        if s <= KEYS[i + 1][0]: break
    s0, P0 = KEYS[i]; s1, P1 = KEYS[i + 1]; k = sm((s - s0) / (s1 - s0))
    out = {}
    for key in P0:
        a_, b_ = P0[key], P1[key]
        out[key] = tuple(lerp(x, y, k) for x, y in zip(a_, b_)) if isinstance(a_, tuple) else lerp(a_, b_, k)
    return out
EV_ROLL, EV_TURN = 38.0, 30.0                   # the foot rolled out and turned out ('his left foot bent out to the side')
def hand_floor(side, p, w):
    O, e_, c_ = HAND[side]
    if w <= 0.01: c_.influence = 0.0; TGT['hand' + side].location = p; return
    place_hand(side, p + V3(0, 0, PALM_T + 0.004), V3(0, 1, 0) if side == 'L' else V3(0, 1, 0), V3(0, 0, -1), w)
    TGT['hand' + side].location = TGT['hand' + side].location.lerp(p, 1 - w)
# ---- nothing through the floor: after posing, lift each foot / hand target (or the whole body) by however far its skin dips under z=0
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'SUBSURF' or md.name.startswith('Delete'): md.show_viewport = False
_vgB = {g.index: g.name for g in BODY.vertex_groups}
def _idx(pref):
    return np.array([v.index for v in BODY.data.vertices if sum(g.weight for g in v.groups if _vgB[g.group].startswith(pref)) > 0.5], dtype=np.int64)
PART_IDX = {'ankL': _idx(('foot.L', 'toe1-', 'toe2-', 'toe3-', 'toe4-', 'toe5-')), 'handL': _idx(('wrist.L', 'finger', 'metacarpal')),
            'handR': _idx(('wrist.R',)), 'ankR': _idx(('foot.R',))}
for k_ in ('ankL', 'ankR', 'handL', 'handR'):                       # toes / fingers split by side
    sd = k_[-1]; PART_IDX[k_] = np.array([i for i in _idx(('foot.' + sd, 'toe', 'wrist.' + sd, 'finger', 'metacarpal')) if
        any(_vgB[g.group].endswith('.' + sd) and g.weight > 0.3 for g in BODY.data.vertices[i].groups) and
        any(_vgB[g.group].startswith(('foot', 'toe')) if k_.startswith('ank') else _vgB[g.group].startswith(('wrist', 'finger', 'metacarpal')) for g in BODY.data.vertices[i].groups)], dtype=np.int64)
FLOOR_EPS = 0.005
def _zs(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); oe.to_mesh_clear(); co = co.reshape(-1, 3)
    M = np.array(oe.matrix_world); return co @ M[:3, :3].T + M[:3, 3]
_NB = None
def unfloor():
    global _NB
    if _NB is None:
        _NB = len(_zs(BODY))
        for k_ in PART_IDX: PART_IDX[k_] = PART_IDX[k_][PART_IDX[k_] < _NB]
    for _ in range(6):
        P = _zs(BODY); lift = False
        for k_, idx in PART_IDX.items():
            if len(idx) == 0: continue
            z = P[idx, 2].min()
            if z < FLOOR_EPS: TGT[k_].location.z += FLOOR_EPS - z; lift = True
        rest = min(P[:, 2].min(), _zs(SUIT)[:, 2].min())
        if not lift and rest < FLOOR_EPS:
            RIG.location.z += FLOOR_EPS - rest; lift = True
            for k_ in PART_IDX: TGT[k_].location.z += FLOOR_EPS - rest
        if not lift: break
        bpy.context.view_layer.update()
def pose(s, evk=1.0, wince=0.0):
    P = pose_at(s); ev = P['ev'] * evk
    hip = Wd(*P['hip'])
    set_pose(hip, rig_rot=(P['lean'], P['side'], 180.0), spine=P['spine'], neck=P['head'] * 0.5, head=P['head'] * 0.5,
             ankL=Wd(*P['ankL']), poleL=Wd(*P['poleL']), footL=(0, -EV_ROLL * ev, -EV_TURN * ev), toesL=0.0,
             ankR=Wd(*P['ankR']), poleR=Wd(*P['poleR']), footR=(0, 0, 0), curlR=0.35, curlL=0.35, jaw=0.25 * wince, lids=0.25 * wince,
             poleArmR=Wd(-0.9, 0.5, 1.2), poleArmL=Wd(0.9, 0.5, 1.2))
    seat = smooth(1.0, 1.6, s)
    hand_floor('L', Wd(*P['handL']), seat); hand_floor('R', Wd(*P['handR']), seat)
    bpy.context.view_layer.update(); unfloor()
# ---- the ball: knocked off his hand, falls and bounces away toward the corner (a function of s, so it rewinds too)
def ball_at(s):
    p0 = Wd(-0.05, -0.45, 2.45); v = V3(1.5, 0.5, 0.6); g = 9.8; r = 0.12   # off to his right, away from the lens
    t_ = s; z0 = p0.z; vz = v.z; x = p0.x; y = p0.y
    while True:                                                   # bounces lose 30% each time
        tf = (vz + math.sqrt(vz * vz + 2 * g * (z0 - r))) / g
        if t_ < tf or vz < 0.4 and tf < 0.02: break
        t_ -= tf; x += v.x * tf; y += v.y * tf; vz = -(vz - g * tf) * 0.7; z0 = r; v = V3(v.x * 0.85, v.y * 0.85, vz)
        if abs(vz) < 0.4: return V3(x + v.x * t_ * 0.5, y + v.y * t_ * 0.5, r)
    return V3(x + v.x * t_, y + v.y * t_, max(r, z0 + vz * t_ - 0.5 * g * t_ * t_))
# ================================================================ the story: one continuous shot
def shin_mid():
    return (wpos('lowerleg01.L') + wpos('foot.L')) * 0.5
def ankle_pt(): return wpos('foot.L') + V3(0, 0, 0.02)
CAM_WIDE = (V3(-2.05, -0.35, 1.5), V3(0.3, 1.35, 1.5), 26.0)
def cam_follow(tgt, off, lens): return (tgt + off, tgt, lens)
def cam_blend(A, Bc, k):
    k = sm(clamp(k, 0, 1)); return (A[0].lerp(Bc[0], k), A[1].lerp(Bc[1], k), lerp(A[2], Bc[2], k))
def story_s(t):
    nb = beat_at(t); lt = t - B[nb]; u = lt / DUR[nb]
    if nb == 0:
        if u < 0.15: return lerp(0.0, 0.36, u / 0.15)
        if u < 0.6: return lerp(0.36, 0.74, (u - 0.15) / 0.45)            # slow motion through the landing
        return lerp(0.74, S_END, sm((u - 0.6) / 0.4))
    if nb == 1: return S_END
    if nb == 2: return lerp(S_END, 0.45, sm(clamp(lt / 1.5, 0, 1)))       # x-ray replay: rewind to the moment his foot lands
    if nb == 3: return 0.45
    if nb == 4: return lerp(0.45, 0.62, sm(u))                           # super slow: the body keeps going, the ankle twists
    if nb in (5, 6): return 0.62 + 0.04 * (u if nb == 5 else 1.0)
    if nb == 7: return lerp(0.66, S_END, sm(clamp(lt / 1.8, 0, 1)))
    if nb in (8, 9, 10): return S_END
    return lerp(S_END, 0.0, sm(clamp(lt / max(DUR[11] - 0.25, 0.1), 0, 1)))   # the rewind into the loop
def trk(t, pts):
    """piecewise smooth track over global time; flat before the first and after the last point"""
    if t <= pts[0][0]: return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1: return lerp(v0, v1, sm((t - t0) / max(t1 - t0, 1e-6)))
    return pts[-1][1]
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; u = lt / DUR[nb]
    s = story_s(t)
    evk = 1.0; brk = 0.0; disl = 0.0; xr = 0.0; crack = 0.0
    hi = {TIB: 0.0, FIB: 0.0, TAL: 0.0}
    if nb in (2, 3): evk = smooth(0.4, 1.4, 1.5 - lt) if nb == 2 else 0.0      # rewinding: the foot straightens as the play goes back
    if nb == 4: evk = smooth(0.15, 1.0, u)
    if nb >= 5: brk = 1.0 if nb > 5 else smooth(0.3, 0.42, lt)
    if nb >= 6: disl = smooth(0.45, 1.2, lt) if nb == 6 else 1.0
    if nb == 9: disl = 1.0 - smooth(0.2, 1.0, lt); brk = 1.0 - smooth(1.0, 2.0, lt); evk = 1.0 - smooth(0.2, 1.2, lt)
    if nb == 10: evk = 0.0
    if nb == 11: evk = 0.0
    if nb in (2, 3, 4, 5, 6, 7, 8, 9): xr = smooth(0.0, 0.9, lt) if nb == 2 else 1.0
    if nb == 10: xr = 1.0 - smooth(0.4, 1.6, lt)
    hi[TIB] = trk(t, [(B[2] + 1.6, 0), (B[2] + 2.0, 1), (B[2] + 3.4, 1), (B[2] + 3.8, 0.55), (B[4] + 0.2, 0.55), (B[4] + 0.8, 0.0)])
    hi[FIB] = trk(t, [(B[2] + 3.4, 0), (B[2] + 3.8, 1), (B[3] + 0.4, 0.55), (B[4] + 0.8, 0.45), (B[6] + 0.3, 0.45), (B[6] + 0.8, 0.0),
                      (B[9] + 1.6, 0.0), (B[9] + 2.1, 0.8), (B[10] + 0.3, 0.8), (B[10] + 1.2, 0.0)])
    hi[TAL] = trk(t, [(B[3] + 0.2, 0), (B[3] + 0.7, 1), (B[4] + 0.2, 1), (B[4] + 0.8, 0.0), (B[6] + 0.3, 0.0), (B[6] + 0.6, 1.0), (B[7] + 1.0, 1.0), (B[7] + 1.8, 0.5), (B[9] + 1.0, 0.5), (B[9] + 1.6, 0.0)])
    crack = trk(t, [(B[4] + 0.4 * DUR[4], 0.0), (B[4] + DUR[4], 0.35), (B[5] + 0.3, 0.35), (B[5] + 0.4, 1.0), (B[5] + 0.6, 1.0), (B[5] + 1.4, 0.4), (B[9] + 1.0, 0.4), (B[9] + 2.0, 0.0)])
    pose(s, evk, wince=1.0 if s > 0.7 and xr < 0.5 else 0.3)
    injury(brk, disl); xray(xr)
    for o, e0 in zip(LIGHTS, (4200, 3000, 900, 260)): o.data.energy = e0 * (1.0 - 0.85 * xr)
    WBG.inputs['Strength'].default_value = 1.0 - 0.8 * xr
    for o, v in hi.items(): o['hi'] = v
    FIB['crack'] = crack
    BALL.location = ball_at(s); BALL.rotation_euler = (s * 9.0, s * 4.0, 0)
    BALL.hide_render = 2 <= nb <= 9                                      # the x-ray close-ups: keep the loose ball out of the background
    # ---- the one camera move
    wide = CAM_WIDE; sm_ = shin_mid(); ank = ankle_pt()
    if nb == 0:
        cp, ct, ln = wide; c = (cp + V3(0.25 * u, 0.15 * u, -0.1 * u), ct.lerp(Wd(0.2, 0.0, 0.7), smooth(0.6, 1.0, u)), lerp(ln, 24, u))
        c = (c[0] + shake(t, 0.03 * smooth(0.3, 0.45, u) * (1 - smooth(0.5, 0.7, u))), c[1], c[2])
    elif nb == 1:
        A = (wide[0] + V3(0.25, 0.15, -0.1), Wd(0.2, 0.0, 0.7), 24.0); Bc = cam_follow(sm_, V3(-0.85, -0.55, 0.45), 32.0)
        c = cam_blend(A, Bc, smooth(0.15, 1.0, u))
    elif nb in (2, 3):
        Bc0 = cam_follow(sm_, V3(-0.85, -0.55, 0.45), 32.0); Bc1 = cam_follow(sm_ + V3(0, 0, -0.05), V3(-0.9, -0.3, 0.12), 35.0)
        c = cam_blend(Bc0, Bc1, smooth(0.0, 1.8, lt)) if nb == 2 else Bc1
    elif nb in (4, 5, 6):
        Bc1 = cam_follow(sm_ + V3(0, 0, -0.05), V3(-0.9, -0.3, 0.12), 35.0); Bc2 = cam_follow(ank + V3(0, 0, 0.06), V3(-0.62, -0.26, 0.1), 40.0)
        c = cam_blend(Bc1, Bc2, smooth(0.0, 1.6, lt)) if nb == 4 else Bc2
        if nb == 5: c = (c[0] + shake(t, 0.012 * smooth(0.3, 0.35, lt) * (1 - smooth(0.4, 1.0, lt)), 3), c[1], c[2])
    elif nb in (7, 8, 9):
        Bc2 = cam_follow(ank + V3(0, 0, 0.06), V3(-0.62, -0.26, 0.1), 40.0); Bc3 = cam_follow(sm_ + V3(0, 0.08, 0), V3(-0.95, -0.05, 0.5), 30.0)
        c = cam_blend(Bc2, Bc3, smooth(0.0, 2.0, lt)) if nb == 7 else Bc3
    elif nb == 10:
        Bc3 = cam_follow(sm_ + V3(0, 0.08, 0), V3(-0.95, -0.05, 0.5), 30.0); A = (V3(-2.2, -0.2, 1.1), Wd(0.25, -0.1, 0.45), 24.0)
        c = cam_blend(Bc3, A, smooth(0.8, DUR[10], lt))
    else:
        A = (V3(-2.2, -0.2, 1.1), Wd(0.25, -0.1, 0.45), 24.0)
        c = cam_blend(A, (wide[0], wide[1], wide[2]), smooth(0.0, DUR[11] - 0.25, lt))
    look(c[0], c[1], c[2], 5.6 if c[2] < 28 else 4.0, focus=c[1])
