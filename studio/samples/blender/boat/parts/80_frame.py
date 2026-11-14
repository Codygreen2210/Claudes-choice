
# ================================================================ motion: the tanker, the riverboat, the people, and ONE continuous camera move
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
# ---- the tanker: swings from 22 to 52 degrees while it closes on the riverboat's river side, hits at T_HIT, crushes in, then drifts back
C_HIT = Vector((-4.0, 1.8, 0.0)); V_TK = 3.2; PEN = 4.5; T_BACK = 12.6
def tk_psi_pre(t): return R(lerp(22.0, 52.0, ease_io(clamp(t, -2, T_HIT) / T_HIT)))
_tk_tab = {}
def _tk_pre(t):
    """stem position before the hit: integrate back from the contact point"""
    key = round(t * 120)
    if key in _tk_tab: return _tk_tab[key]
    n = max(1, int((T_HIT - t) * 120)); dt = (T_HIT - t) / n; p = C_HIT.copy(); s_ = T_HIT
    for _ in range(n):
        s_ -= dt; a_ = tk_psi_pre(s_); p -= Vector((math.cos(a_), math.sin(a_), 0)) * V_TK * dt
    _tk_tab[key] = p; return p
def tk_pose(t):
    hit_dir = Vector((math.cos(R(52)), math.sin(R(52)), 0))
    if t < T_HIT: return _tk_pre(t), tk_psi_pre(t)
    p = C_HIT + hit_dir * PEN * ease_out((t - T_HIT) / 0.5)
    k = ease_io((t - T_BACK) / 7.0); p = p - hit_dir * 30.0 * k + Vector((-25.0, 0, 0)) * k
    return p, R(52) - R(7) * k
def tk_matrix(t):
    p, a_ = tk_pose(t); return Matrix.Translation(p) @ Matrix.Rotation(a_, 4, 'Z')
# ---- the riverboat: shoved and rocked by the hit, settles, lists toward the river, rolls onto her side and sinks to a sliver
def rb_theta(t):
    th = 0.0
    if t > T_HIT: th += R(3.5) * math.exp(-(t - T_HIT) / 1.3) * math.sin(2 * math.pi * 0.9 * (t - T_HIT))
    th += R(3) * ease_io((t - 14.6) / 1.4) + R(9) * ease_io((t - 16.0) / 3.5) + R(8) * ease_io((t - 19.5) / 2.9)
    th += R(64) * ease_io((t - (T_ROLL - 0.15)) / 2.3) - R(2) * ease_io((t - (T_ROLL + 2.1)) / 0.8)
    return th
def rb_off(t):
    o = Vector((0, 0, 0))
    if t > T_HIT: o.y += 0.18 * ease_out((t - T_HIT) / 0.35) - 0.12 * ease_io((t - T_HIT - 0.35) / 1.0); o.x += 0.3 * ease_out((t - T_HIT) / 0.5)
    o.z -= 0.4 * ease_io((t - T_HIT - 1) / 4) + 0.8 * ease_io((t - 14) / 8) + 5.0 * ease_io((t - T_ROLL) / 3.2)
    o.z += 0.08 * math.sin(2 * math.pi * 0.23 * t)
    return o
def rb_matrix(t):
    return Matrix.Translation(RB_PIV + rb_off(t)) @ Matrix.Rotation(rb_theta(t), 4, 'X') @ Matrix.Translation(-RB_PIV)

# ---- people standing on the capsized hull's dock side (world, after the roll)
ONTOP = [figure(f'o{i}', 800 + i, loc=(-24 + 7.5 * i, 12.4, 2.1), yaw=math.pi / 2 + h1(i + 3), vest=True) for i in range(7)]
# ---- the camera: one key list, every key in a frame ('w' world, 'b' boat, 'tk' tanker, 'k0' = frame one's pose kept beside the tanker)
K = [
    (0.0, 'w', (-11.0, -22.0, 2.0), (-22.0, -5.0, 4.0), 16),
    (1.4, 'w', (-3.0, -20.0, 4.0), (-15, -2, 4.5), 18),
    (2.9, 'w', (40.0, -10.0, 18.0), (10, 15, 4), 24),
    (4.2, 'w', (20.0, 36.0, 12.0), (6, 20, 3), 24),
    (5.6, 'w', (-10.0, -70.0, 120.0), (-25, -15, 0), 20),
    (7.0, 'w', (28.0, -38.0, 20.0), (-3, 2, 3), 22),
    (T_HIT, 'w', (16.0, -14.0, 6.0), (-3, 3, 3), 24),
    (9.1, 'w', (8.0, -4.0, 4.0), (0, 4, 3), 24),
    (10.0, 'b', (4.2, 2.2, 3.2), (2, 9, 3), 22),
    (10.8, 'b', (3.0, 7.2, 3.1), (-4, 5.5, 2.6), 20),
    (12.2, 'b', (2.0, 10.0, 3.0), (-8, 7.5, 2.4), 22),
    (13.6, 'b', (1.5, 10.5, 2.7), (-3, 5.6, 2.0), 22),
    (15.2, 'b', (0.0, 12.0, 2.9), (-3, 6.0, 1.8), 20),
    (16.6, 'b', (-1.0, 14.5, 3.1), (-1, 19, 3.2), 20),
    (17.6, 'b', (-1.0, 17.5, 3.4), (-1, 26, 4), 22),
    (18.6, 'b', (-1.0, 23.5, 7.5), (-6, 14, 7.5), 22),
    (20.3, 'w', (20.0, 52.0, 14.0), (-4, 14, 5), 24),
    (21.6, 'w', (48.0, 40.0, 30.0), (-4, 4, 2), 18),
    (22.8, 'w', (40.0, -40.0, 16.0), (-2, 4, 3), 22),
    (24.4, 'w', (18.0, -30.0, 5.0), (5, -10, 0.5), 24),
    (25.7, 'w', (24.0, -38.0, 6.0), (12, -20, 0.5), 26),
    (27.3, 'w', (-30.0, -120.0, 70.0), (0, 0, 0), 22),
    (29.0, 'w', (120.0, -150.0, 60.0), (-100, 30, 10), 22),
    (31.0, 'w', (110.0, -30.0, 40.0), (-120, 60, 15), 22),
    (32.6, 'w', (58.0, 64.0, 12.0), (30, 36, 3), 24),
    (33.6, 'w', (44.0, 62.0, 18.0), (28, 36, 3), 24),
    (34.6, 'w', (-40.0, -60.0, 45.0), (-100, -110, 20), 24),
    (35.4, 'tk', (-118.0, -22.0, 26.0), (-143.5, 0, 21), 28),
    (36.5, 'tk', (-128.0, -15.0, 22.5), (-143.5, 0, 20.9), 32),
    (37.8, 'w', (-60.0, -80.0, 20.0), (-40, -20, 3), 22),
    (END, 'k0', (-11.0, -22.0, 2.0), (-22.0, -5.0, 4.0), 16),
]
_M0 = None
def key_world(k, t):
    global _M0
    tk_, fr, p, q, ln = k; p = Vector(p); q = Vector(q)
    if fr == 'b': M = rb_matrix(t)
    elif fr == 'tk': M = tk_matrix(t)
    elif fr == 'k0':
        if _M0 is None: _M0 = tk_matrix(0.0).inverted()
        M = tk_matrix(t) @ _M0
    else: return p, q, ln
    return M @ p, M @ q, ln
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    t0, t1 = ts[i], ts[i + 1]; u = clamp((t - t0) / (t1 - t0), 0, 1)
    def tan(j):
        a_, b_ = max(0, j - 1), min(n - 1, j + 1)
        return (vs[b_] - vs[a_]) / (ts[b_] - ts[a_]) * (t1 - t0)
    m0, m1 = tan(i), tan(i + 1); u2, u3 = u * u, u * u * u
    return vs[i] * (2 * u3 - 3 * u2 + 1) + m0 * (u3 - 2 * u2 + u) + vs[i + 1] * (-2 * u3 + 3 * u2) + m1 * (u3 - u2)
def cam_at(t):
    ts = [k[0] for k in K]; W = [key_world(k, t) for k in K]
    p = herm(ts, [w[0] for w in W], t); q = herm(ts, [w[1] for w in W], t); ln = herm(ts, [Vector((w[2], 0, 0)) for w in W], t).x
    # inside the boat (keys 'b'), the camera leans with her (60 %)
    wb = sum(math.exp(-((t - k[0]) / 0.9) ** 2) for k in K if k[1] == 'b'); wb = clamp(wb, 0, 1)
    up = Vector((0, 0, 1)); th = rb_theta(t) * 0.6 * wb
    up = Vector((0, -math.sin(th), math.cos(th)))
    sh = Vector((0, 0, 0))
    if t > T_HIT: sh += shake(t, 0.45 * math.exp(-(t - T_HIT) / 0.6), 1.0, 11.0)
    if T_SHAKE - 0.2 < t < T_SHAKE + 1.2: sh += shake(t, 0.05, 2.0, 9.0)
    sh += shake(t, 0.06, 5.0, 0.8)                                       # a drone's slow drift
    return p + sh, q + sh * 0.5, ln, up

# ---- what everything does at time t
def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    p_, a_ = tk_pose(t); TK.location = p_; TK.rotation_euler = (0, 0, a_ + R(0.6) * math.sin(0.4 * t))
    M = rb_matrix(t); RB.matrix_world = Matrix.Translation(RB_PIV) @ (Matrix.Translation(-RB_PIV) @ M @ Matrix.Translation(RB_PIV))
    tw = t * 0.18
    for o in (RIVER, BOW_FOAM, HIT_FOAM, ROLL_FOAM, CG_WAKE, PD_WAKE, *BOW_WAVE): o['tw'] = tw
    for o in POUR: o['tw'] = t * 1.6
    BOW_FOAM['a'] = 1.0 if t < T_HIT else lerp(1.0, 0.25, ease_io((t - T_HIT) / 2.0))
    for o in BOW_WAVE: o['a'] = 1.0 if t < T_HIT else lerp(1.0, 0.0, ease_io((t - T_HIT) / 1.5)); o.hide_render = o['a'] < 0.02
    HIT_FOAM['a'] = ease_out((t - T_HIT) / 0.3) * (1 - ease_io((t - T_HIT - 2.5) / 3.0)) if t > T_HIT else 0.0
    ROLL_FOAM['a'] = ease_out((t - T_ROLL - 0.6) / 0.6) * (1 - 0.6 * ease_io((t - T_ROLL - 3.5) / 4.0)) if t > T_ROLL + 0.6 else 0.0
    broken = t > T_HIT + 0.06
    for o in BREAK: o.hide_render = broken
    for o in HOLE: o.hide_render = not broken
    HIT_SPLASH.at((-4.5, 2.0, 0.8), t - T_HIT)
    ROLL_SPLASH.at((-4.0, -4.0, 0.3), t - T_ROLL - 1.0)
    GLASS_BITS.at(M @ Vector((-6.0, 4.8, 2.9)), t - T_HIT)
    pa = ease_io((t - (T_BACK + 0.9)) / 0.8) * (1 - ease_io((t - T_ROLL) / 0.6))
    for o in POUR: o['a'] = pa; o.hide_render = pa < 0.01
    FLOOD.hide_render = not (T_BACK + 1.0 < t < T_ROLL + 1.0); FLOOD.location.z = 1.52 + 0.9 * ease_io((t - T_BACK - 1.0) / 7.0)
    # tables slide toward the river side as she lists
    for g, cx, cy in TABLES:
        sl = clamp(rb_theta(t) - R(4), 0, R(30)) * 9.0
        ymin = 7.9 if -13 < cx < 4 else 6.2                                # stop short of the river-side wall (and the bow)
        g.location = (cx + 0.3 * h1(cx + cy) * sl, max(ymin, cy - sl * (0.6 + 0.4 * h1(cx * 3 + cy))), 1.5); g.rotation_euler = (0, 0, 0.25 * sl * (h1(cx + 2 * cy) - 0.5))
    # people
    for i, p in enumerate(GUESTS):
        show_fig(p, t < 17.0); pose(p, 'brace' if t > T_HIT else 'stand', t)
    for i, p in enumerate(WALKERS):
        y_ = 23.4 + 1.8 * i + 0.9 * min(t, T_HIT); p['root'].location = (6 + 1.0 * (i % 2), y_, 3.4)
        face(p, math.pi / 2 if t < T_HIT + 0.3 else -math.pi / 2 + 0.3 * (h1(i) - 0.5))
        pose(p, 'walk' if t < T_HIT else 'brace', t)
    show_fig(CREW, t < 18.0)
    if t < T_SHAKE: CREW['root'].location = (-6.5, RB_CY + 1.0, 1.5); face(CREW, 0.2); pose(CREW, 'stand', t)
    elif t < T_POUR: face(CREW, 0.2 - 1.6 * ease_io((t - T_SHAKE) / 0.6)); pose(CREW, 'stand', t)
    else:
        k = ease_io((t - T_POUR) / 3.0); CREW['root'].location = (-6.5 - 3 * k, RB_CY + 1.0 + 5.0 * k, 1.5); face(CREW, math.atan2(5.0, -3.0)); pose(CREW, 'run' if k < 1 else 'stand', t)
    for p in DINERS: show_fig(p, False)
    for i, p in enumerate(HIGH):
        on = 17.0 < t < T_ROLL + 0.9; show_fig(p, on)
        if on: pose(p, 'climb' if t < 19.3 else 'brace', t)
    for i, p in enumerate(POLICE):
        k = clamp((t - (T_POLICE - 1.2)) / 4.5, 0, 1)
        p['root'].location = (lerp(70 + 6 * i, 6 + 4 * i, k), 24 + 2 * (i % 2), 3.4); face(p, math.pi if k < 1 else -math.pi / 2)
        pose(p, 'run' if 0 < k < 1 else 'stand', t)
    for i, p in enumerate(SWIM):
        on = t > T_ROLL + 0.9; show_fig(p, on)
        if on:
            k = ease_out((t - T_ROLL - 0.9) / 1.5)
            p['root'].location = (-12 + 3.4 * i + 2 * h1(i), -6 - 9 * h1(i + 30) - 3 * k, -1.25 + 0.08 * math.sin(2 * math.pi * 0.6 * t + i)); pose(p, 'tread', t)
    for i, p in enumerate(ONTOP):
        on = t > T_ROLL + 2.3; show_fig(p, on)
        if on:                                                           # standing on the dock-side hull plating, now facing the sky
            q = M @ Vector((-24 + 7.5 * i, RB_CY + 8.0, -0.35 + 0.5 * h1(i))); p['root'].location = q; pose(p, 'wave' if i % 3 == 0 else 'stand', t)
    # rescue boats come in from the river; two rescuers jump from the police boat; ambulances flash on the wharf
    ka = ease_out((t - (T_ROLL - 0.6)) / 3.0)
    CG_BOAT.location = (lerp(-20, -2, ka), lerp(-140, -24, ka), 0.0 + 0.1 * math.sin(2.1 * t)); CG_BOAT.rotation_euler = (0.03 * math.sin(1.7 * t), 0, math.atan2(116, 18) if ka < 0.98 else R(40))
    PD_BOAT.location = (lerp(70, 14, ka), lerp(-130, -26, ka), 0.0 + 0.1 * math.sin(1.9 * t + 1)); PD_BOAT.rotation_euler = (0.03 * math.sin(1.5 * t), 0, math.atan2(104, -56) if ka < 0.98 else R(120))
    CG_WAKE['a'] = 1 - ka * 0.8; PD_WAKE['a'] = 1 - ka * 0.8
    for b_, lt in ((CG_BOAT, CG_LT), (PD_BOAT, PD_LT)): flash(lt, t > T_ROLL - 0.6, t, 2.5)
    for i, p in enumerate(RESC):
        on = i < 2 and t > T_JUMP - 0.6; show_fig(p, on)
        if on:
            u = (t - T_JUMP) / 0.9; base = PD_BOAT.matrix_world @ Vector((-2.6 + 1.2 * i, 1.3, 0.95))
            if u < 0: p['root'].location = base; pose(p, 'stand', t)
            else:
                uu = min(u, 1.0); p['root'].location = base + Vector((0.6 * uu, 4.0 * uu, 2.2 * uu - 4.4 * uu * uu * 1.0 - (1.2 if u > 1 else 0)))
                pose(p, 'jump' if u < 1 else 'tread', t)
            face(p, math.pi / 2)
    for k_, js in enumerate(JUMP_SPLASH): js.at(PD_BOAT.location + Vector((-0.6 + 1.6 * k_, 5.8, -0.2)), t - T_JUMP - 0.9)
    for g, l1, l2 in AMBS:
        flash(l1, t > 22.0, t, 2.0, 0.0); flash(l2, t > 22.0, t, 2.0, math.pi); show_fig({'root': g}, t > 21.0)
    # camera
    cp, ct, ln, up = cam_at(t); look(cp, ct, ln, 8.0 if not (9.8 < t < 18.0) else 4.0, up=up)
    bpy.context.view_layer.update()

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear(); CAM.data.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, up = cam_at(tt_); look(cp, ct, ln, up=up); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
if os.environ.get('TOPCAM'):                                             # debug: a top-down plan view of the whole layout
    _frame0 = frame
    def frame(f):
        _frame0(f); CAM.animation_data_clear(); CAM.data.type = 'ORTHO'; CAM.data.ortho_scale = float(os.environ['TOPCAM'])
        CAM.location = (-30, -20, 600); CAM.rotation_mode = 'XYZ'; CAM.rotation_euler = (0, 0, 0); CAM.data.dof.use_dof = False
if os.environ.get('CHKCAM'):                                             # debug: a fixed close-up camera for clipping checks
    _frame1 = frame; _cks = [[float(v) for v in c.split(',')] for c in os.environ['CHKCAM'].split(';')]
    def frame(f):
        _frame1(f); CAM.animation_data_clear(); c = _cks[int(os.environ.get('CHKI', '0'))]
        look(Vector(c[:3]), Vector(c[3:6]), c[6], 11.0)
