# ================================================================ animation and the one continuous camera move
def key(t, p, q, lens): return (t, Vector(p), Vector(q), lens)
def interp(keys, t):
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0.0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0.0
    else:
        i = max(j for j in range(len(keys)) if keys[j][0] <= t); k0, k1 = keys[i], keys[i + 1]; u = sm((t - k0[0]) / (k1[0] - k0[0]))
    c0, c1 = k0[1], k1[1]; a0, a1 = k0[2], k1[2]
    d0 = (a0 - c0).normalized(); d1 = (a1 - c1).normalized(); cp = c0.lerp(c1, u); dr = d0.slerp(d1, u) if d0.dot(d1) > -0.99 else d1
    fl = lerp((a0 - c0).length, (a1 - c1).length, u)
    return cp, cp + dr * fl, lerp(k0[3], k1[3], u)
CK = [
    key(0.0, (0.0, 2.45, 2.1), (0.0, 3.6, 1.12), 24),                     # the myth sword slams onto the scale (looking down on the pan)
    key(0.9, (0.0, 2.5, 2.05), (0.0, 3.6, 1.08), 24),
    key(2.3, (0.0, 2.85, 0.98), (0.0, 3.6, 0.72), 28),                    # in on the dial: forty pounds
    key(B[1] - 0.1, (0.0, 2.88, 0.97), (0.0, 3.6, 0.72), 28),
    key(B[1] + 0.75, (0.15, 2.0, 2.1), (0.1, 3.6, 0.95), 24),             # back: it's yanked away
    key(B[2] + 0.4, (0.12, 2.05, 2.05), (0.1, 3.6, 0.95), 24),            # a real sword lands: three pounds
    key(B[2] + 1.85, (0.15, 2.1, 2.0), (0.1, 3.6, 0.95), 24),
    key(B[2] + 2.4, (1.6, 2.1, 2.0), (1.6, 3.6, 0.95), 24),               # the two-hander on the red scale
    key(B[3] - 0.1, (1.62, 2.15, 1.98), (1.6, 3.6, 0.95), 24),
    key(B[3] + 0.55, (4.0, 2.55, 1.85), (4.0, 3.6, 1.1), 24),             # the balance, from above
    key(B[4] - 0.1, (4.02, 2.6, 1.83), (4.0, 3.6, 1.1), 24),
    key(B[4] + 0.75, (8.0, 3.35, 2.55), (8.0, 5.3, 2.6), 28),             # the 1746 page writes itself
    key(B[4] + 3.3, (8.02, 3.4, 2.53), (8.0, 5.3, 2.6), 28),
    key(B[4] + 4.0, (8.5, 3.0, 1.85), (8.58, 4.6, 1.4), 26),              # down: the new book gets its stamp
    key(B[5] - 0.1, (8.52, 3.05, 1.83), (8.58, 4.6, 1.4), 26),
    key(B[5] + 0.7, (12.0, 2.65, 0.85), (12.0, 4.4, 0.95), 22),           # low on the giant's hilt
    key(B[5] + 2.3, (12.1, 1.95, 1.5), (12.05, 4.4, 1.5), 20),            # up its length: seven feet
    key(B[5] + 2.95, (12.12, 1.93, 1.5), (12.05, 4.4, 1.5), 20),
    key(B[5] + 3.5, (13.3, 1.3, 2.25), (13.3, 3.6, 1.0), 20),             # it tips onto the long scale: almost fifteen
    key(B[6] - 0.1, (13.32, 1.33, 2.23), (13.3, 3.6, 1.0), 20),
    key(B[6] + 0.95, (16.5, 1.55, 1.75), (16.5, 3.8, 1.65), 22),          # it flies to the parade guard
    key(B[7] - 0.1, (16.52, 1.6, 1.73), (16.5, 3.8, 1.65), 22),
    key(B[7] + 0.7, (20.3, 2.3, 2.1), (20.3, 5.3, 2.25), 22),             # the museum wall
    key(B[7] + 2.6, (20.3, 2.4, 2.05), (20.3, 5.3, 2.2), 22),
    key(B[7] + 3.2, (20.3, 3.2, 1.6), (20.3, 5.3, 1.45), 24),             # in on the plaque: struck out, flipped
    key(B[8] - 0.05, (20.3, 3.15, 1.62), (20.3, 5.3, 1.45), 24),
    key(B[8] + 0.5, (20.2, 2.45, 2.15), (20.15, 4.5, 1.1), 22),           # back and up: the myth sword breaks the last scale
    key(TOTAL, (20.2, 2.35, 2.18), (20.15, 4.5, 1.1), 22),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)
FAR = Matrix.Translation((0, 0, -60))


def drop(t, t_land, rest, h=1.3, fall=0.45):
    """a prop dropped onto a surface: falls h (accelerating), lands at t_land, two little bounces; None before it appears"""
    if t < t_land - fall: return None, 0.0
    if t < t_land: u = (t - (t_land - fall)) / fall; return rest + Vector((0, 0, h * (1 - u * u))), 1.0 - u
    d = t - t_land; return rest + Vector((0, 0, 0.03 * abs(math.sin(d * 14)) * math.exp(-d * 7))), 0.0


def blend_m(m0, m1, u, lift=0.0):
    l0, q0, _ = m0.decompose(); l1, q1, _ = m1.decompose()
    return Matrix.Translation(l0.lerp(l1, u) + Vector((0, 0, lift * math.sin(math.pi * u)))) @ q0.slerp(q1, u).to_matrix().to_4x4()


def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- the myth sword: drops and slams (frame one is already falling), is yanked away, comes back at the end for the last scale
    if t < T_YANK:
        p_, w_ = drop(t, T_HIT, MYTH_P, 0.6, T_HIT + 0.25)                 # at frame 0 it's already in view, falling
        MYTH.location = p_; MYTH.rotation_euler = (R(10) * w_, R(-8) * w_, MYTH_RZ + R(25) * w_)
        if t > T_HIT: d = t - T_HIT; MYTH.rotation_euler = (R(2.5) * math.sin(d * 16) * math.exp(-d * 6), 0, MYTH_RZ)
    elif t < T_YANK + 1.1:
        d = t - T_YANK; MYTH.location = MYTH_P + Vector((0.25 * d, 0.1 * d, 0.4 * d + 5.0 * d * d)); MYTH.rotation_euler = (R(30) * d, R(-20) * d, MYTH_RZ + R(200) * d * d)
    elif t < T_END: MYTH.location = (0, 0, -60)
    else:
        p_, w_ = drop(t, T_ENDL, MYTH_P2, 1.3, T_ENDL - T_END)
        MYTH.location = p_; MYTH.rotation_euler = (R(8) * w_, R(-6) * w_, MYTH_RZ - R(30) * w_)
        if t > T_ENDL: d = t - T_ENDL; MYTH.rotation_euler = (R(2.5) * math.sin(d * 16) * math.exp(-d * 6), 0, MYTH_RZ)
    # ---- the needles
    ND1.rotation_euler = (0, needle_angle(needle_v(t, EV1)), 0)
    ND2.rotation_euler = (0, needle_angle(needle_v(t, EV2)), 0)
    ND3.rotation_euler = (0, needle_angle(needle_v(t, EV3), 20), 0)
    ND4.location = ND4_REST; ND4.rotation_euler = (0, needle_angle(0), 0)
    if t > T_ENDL:
        d = t - T_ENDL; a_ = needle_angle(0) + R(300) * smooth(0, 0.25, d) + R(360) * 2.2 * smooth(0.2, T_POP - T_ENDL, d) ** 1.5
        if t < T_POP: ND4.rotation_euler = (0, a_, 0)
        else:
            e = t - T_POP; ND4.location = ND4_REST + Vector((0.5 * e, -1.3 * e, 2.2 * e - 4.9 * e * e)); ND4.rotation_euler = (R(500) * e, a_ + R(900) * e, 0)
            if ND4.location.z < -0.6: ND4.location = (0, 0, -60)
    # ---- the real sword and the two-hander drop onto their scales
    for sw, rest, tl in ((ARM, ARM_P, T_ARM), (TWO, TWO_P, T_TWO)):
        p_, w_ = drop(t, tl, rest, 1.3, 0.45)
        if p_ is None: sw.location = (0, 0, -60); continue
        sw.location = p_; sw.rotation_euler = (R(6) * w_, R(-4) * w_, R(-20) * w_)
    # ---- the balance: drops onto the knife edge, teeters, settles level; a quick spin for "moved fast"
    if t < T_BAL - 0.4: BSW.matrix_basis = FAR
    else:
        if t < T_BAL: u = (t - (T_BAL - 0.4)) / 0.4; off = Vector((0, 0, 0.9 * (1 - u * u))); th = R(10); ph = R(20) * (1 - u)
        else:
            d = t - T_BAL; off = Vector(); th = R(13) * math.exp(-2.0 * d) * math.cos(7.5 * d) + 0.0
            ph = R(360) * smooth(T_SPIN, T_SPIN + 0.55, t) ** 1.0
            if t > T_SPIN + 0.55: e = t - T_SPIN - 0.55; th += R(5) * math.exp(-4 * e) * math.sin(10 * e)
        BSW.matrix_basis = Matrix.Translation(PEG + off) @ Matrix.Rotation(ph, 4, 'Z') @ Matrix.Rotation(th, 4, 'Y') @ Matrix.Translation(-BAL_PIV)
    # ---- the 1746 page: the year pops in, lines scribble, the quote writes itself; the quill follows
    u = smooth(T_YEAR, T_YEAR + 0.25, t); s = u + 0.3 * math.sin(math.pi * u); YEAR.scale = (max(s, 1e-4),) * 3; YEAR.hide_render = u <= 0
    qp = Vector((0.4, -0.08, -0.62)); qa = 0.0
    for k, (o, x0, L_) in enumerate(SCRIB):
        s = clamp((t - (B[4] + 1.0 + 0.28 * k)) / 0.26, 0, 1)
        o.scale = (max(s, 0.0001), 1, 1); o.location.x = x0 * (1 - s); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((x0 + L_ * s, -0.08, 0.17 - 0.08 * k)); qa = 1.0
    for k, o in enumerate(QUOTE):
        s = clamp((t - (T_QUOTE + 0.45 * k)) / 0.4, 0, 1); o.scale = (max(s, 0.0001), 1, 1); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((-0.5 + QUOTE_W[k] * s, -0.08, -0.2 - 0.16 * k)); qa = 1.0
    QUILL.location = qp + Vector((0, 0, 0.008 * math.sin(t * 60) * qa)); QUILL.rotation_euler = (0, R(-10) + 0.15 * math.sin(t * 25) * qa, 0)
    # ---- the stamps slam on
    for st, t0, sg in ((STAMP, T_STAMP, 1.0), (PSTAMP, T_PSTAMP, 1.0)):
        u = clamp((t - t0) / 0.12, 0, 1)
        if u <= 0: st.scale = (1e-4,) * 3; continue
        d = t - t0 - 0.12; sq = 0.1 * math.exp(-d * 16) * math.cos(d * 40) if d > 0 else 0.0
        s = 2.4 - 1.4 * u * u; st.scale = (s * (1 + sq), s, s * (1 - sq))
    # ---- the giant: the tape measure runs up its length, the 7 FT tag pops; it tips onto the long scale, then flies to the guard
    TAPE.location.z = TAPE_Z0 - G_H * (1 - smooth(T_TAPE0, T_TAPE1, t))
    u = smooth(T_TAPE1, T_TAPE1 + 0.2, t); s = u + 0.35 * math.sin(math.pi * u); TAG.scale = (max(s, 1e-4),) * 3
    mb = max(0.0, t - T_MARCH) if t > T_MARCH else 0.0
    for gd, x0, ph in ((GD1, PX - 0.45, 0.0), (GD2, PX + 0.45, 0.5)):
        if t < T_MARCH: gd.location = (x0, PY, PLAT_Z); gd.rotation_euler = (0, 0, 0); continue
        st_ = (t - T_MARCH) * 2.2 + ph; amp = smooth(T_MARCH, T_MARCH + 0.3, t)
        gd.location = (x0 + 0.025 * math.sin(math.pi * st_) * amp, PY, PLAT_Z + 0.03 * abs(math.sin(math.pi * st_)) * amp); gd.rotation_euler = (0, R(3) * math.sin(math.pi * st_) * amp, 0)
    bpy.context.view_layer.update()
    G_HOLD = Matrix.Translation(GD1.matrix_world @ (HANDS1 + Vector((0, 0, 0.26)))) @ GD1.matrix_world.to_quaternion().to_matrix().to_4x4() @ M_UP
    if t < T_TIP0: GIANT.matrix_basis = G_UP
    elif t < T_TIPL: u = (t - T_TIP0) / (T_TIPL - T_TIP0); GIANT.matrix_basis = blend_m(G_UP, G_FLATM, u * u, 0.15)
    elif t < T_CARRY0: d = t - T_TIPL; GIANT.matrix_basis = Matrix.Translation((0, 0, 0.02 * abs(math.sin(d * 14)) * math.exp(-d * 7))) @ G_FLATM
    elif t < T_CARRY1: u = sm((t - T_CARRY0) / (T_CARRY1 - T_CARRY0)); GIANT.matrix_basis = blend_m(G_FLATM, G_HOLD, u, 0.6)
    else: GIANT.matrix_basis = G_HOLD
    # ---- the banner ripples once the parade starts; confetti falls for "show off"
    me = FLAG.data; amp = 0.3 + 0.7 * smooth(T_MARCH, T_MARCH + 0.5, t)
    for i, v in enumerate(FLAG_REST):
        x = v.x - 0.016; me.vertices[i].co = (v.x - 0.02 * (x / FLAG_W) * amp, v.y + 0.045 * math.sin(6.5 * x - 7.0 * t) * (x / FLAG_W) * amp, v.z - 0.02 * (x / FLAG_W) ** 2)
    me.update()
    for o, x0, y0, dl, sp, rot, z0 in CONF:
        d = t - T_CONF - dl; z = z0 - sp * d
        if d < 0 or z < PLAT_Z + 0.02: o.location = (0, 0, -60); continue
        o.location = (PX + x0 + 0.08 * math.sin(3.1 * d + rot), y0 + 0.05 * math.cos(2.3 * d + rot), z)
        o.rotation_euler = (rot + 6.0 * d, rot * 0.5 + 4.0 * d, rot + 2.0 * d)
    # ---- the wall: the swords drop onto their pins in turn; the plaque is struck out and flipped
    for k, (o, m_) in enumerate(WSW):
        d = t - T_HANG[k]
        if d < 0: o.matrix_basis = FAR @ m_; continue
        z = 0.3 * (1 - min(1.0, d / 0.2) ** 2) if d < 0.2 else 0.012 * abs(math.sin(25 * (d - 0.2))) * math.exp(-10 * (d - 0.2))
        o.matrix_basis = Matrix.Translation((0, 0, z)) @ m_
    u = smooth(T_STRIKE, T_STRIKE + 0.25, t); STRIKE.scale = (max(u, 1e-4), 1, 1); STRIKE.hide_render = u <= 0
    u = smooth(T_FLIP, T_FLIP + 0.35, t); PLQ.rotation_euler = (math.pi * u + R(12) * math.sin(math.pi * u), 0, 0)
    # ---- glints
    for g_ in GLS_O: g_.hide_render = True; g_.scale = (0.0,) * 3
    for gi, t0, pw, sz in GLS:
        u = clamp((t - t0) / 0.35, 0, 1)
        if 0 < u < 1: g_ = GLS_O[gi]; s = math.sin(math.pi * u) * sz; g_.scale = (s, s, s); g_.rotation_euler = (0, u * 1.2, 0); g_.location = pw; g_.hide_render = False
    # ---- camera, with a nod on each big landing
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3)
    for tn, a_ in ((T_HIT, 0.02), (T_TIPL, 0.012), (T_ENDL, 0.015), (T_POP, 0.008)):
        if t > tn: cp = cp + shake(t, a_, 4.0, 13.0) * math.exp(-(t - tn) * 6.0)
    look(cp, ct, lens, 5.6)
    bpy.context.view_layer.update()
