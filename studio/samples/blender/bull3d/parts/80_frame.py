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
    key(0.0, (X0 + 1.0, 1.75, 1.2), (X0 + 0.15, Y0, 0.95), 28),            # the bull turns on its turntable (we glide round it)
    key(1.7, (X0 + 0.15, 0.95, 1.42), (X0, Y0, 0.92), 28),
    key(B[1] - 0.15, (X0 + 0.12, 1.0, 1.42), (X0, Y0, 0.92), 28),
    key(B[1] + 0.7, (X1 - 0.08, 2.25, 1.55), (X1 - 0.08, 5.3, 1.5), 24),   # Sicily: the year, the ruler's bust, the pin
    key(B[2] - 0.15, (X1 - 0.06, 2.28, 1.55), (X1 - 0.08, 5.3, 1.5), 24),
    key(B[2] + 0.7, (X2, 2.3, 1.62), (X2, 4.6, 1.38), 24),                 # the workshop: the plans, the model drops in
    key(T_DOOR - 0.55, (X2, 2.34, 1.61), (X2, 4.6, 1.38), 24),
    key(T_DOOR - 0.05, (X2 - 0.06, 2.85, 1.25), (X2 - 0.06, 4.0, 1.1), 28),  # in on the door
    key(T_FIRE - 0.45, (X2 - 0.06, 2.88, 1.25), (X2 - 0.06, 4.0, 1.1), 28),
    key(T_FIRE + 0.1, (X2 + 0.05, 2.6, 1.18), (X2 + 0.05, 4.0, 0.85), 26),  # back: the fire underneath
    key(B[4] + 0.15, (X2 + 0.06, 2.63, 1.18), (X2 + 0.05, 4.0, 0.85), 26),
    key(B[4] + 0.75, (X2 + 0.85, 2.9, 1.22), (X2 + 0.45, 4.0, 1.12), 28),   # the head: pipes, sound rings
    key(B[5] - 0.15, (X2 + 0.87, 2.93, 1.22), (X2 + 0.45, 4.0, 1.12), 28),
    key(B[5] + 0.7, (X3 + 0.1, 3.1, 1.44), (X3 + 0.1, 4.13, 0.85), 28),   # the game board
    key(T_ROSE - 0.3, (X3 + 0.11, 3.13, 1.43), (X3 + 0.1, 4.13, 0.85), 28),
    key(T_ROSE + 0.4, (X3 + 0.11, 3.2, 1.39), (X3 + 0.1, 4.13, 0.85), 29),  # a touch closer as the people rise
    key(B[7] - 0.15, (X3 + 0.12, 3.22, 1.38), (X3 + 0.1, 4.13, 0.85), 29),
    key(B[7] + 0.7, (X4 - 0.15, 2.3, 1.6), (X4 - 0.15, 5.0, 1.48), 25),    # the record: ?, the book, 500 years, MADE UP?
    key(B[9] - 0.15, (X4 - 0.13, 2.35, 1.59), (X4 - 0.15, 5.0, 1.48), 25),
    key(B[9] + 0.7, (X5, 2.78, 2.02), (X5, 3.98, 0.84), 23),                # the map: REAL, to Carthage and home
    key(B[11] - 0.15, (X5 + 0.02, 2.81, 2.0), (X5, 3.98, 0.84), 23),
    key(B[11] + 0.65, (X6, 2.5, 1.65), (X6, 5.0, 1.6), 24),                # the Roman writer
    key(B[12] - 0.15, (X6 + 0.02, 2.53, 1.65), (X6, 5.0, 1.6), 24),
    key(B[12] + 0.65, (X7, 2.55, 1.35), (X7, 4.0, 0.55), 24),              # the river statue
    key(B[13] - 0.15, (X7 + 0.02, 2.58, 1.34), (X7, 4.0, 0.55), 24),
    key(B[13] + 0.7, (X8, 2.3, 1.5), (X8, 4.0, 1.15), 24),                 # lost
    key(TOTAL, (X8, 2.6, 1.45), (X8, 4.0, 1.15), 24),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)
FAR = Vector((0, 0, -60))


def drop(t, t_land, rest, h=1.0, fall=0.4):
    """a prop dropped onto a surface: falls h, lands at t_land, two little bounces; None before it appears"""
    if t < t_land - fall: return None, 0.0
    if t < t_land: u = (t - (t_land - fall)) / fall; return rest + Vector((0, 0, h * (1 - u * u))), 1.0 - u
    d = t - t_land; return rest + Vector((0, 0, 0.02 * abs(math.sin(d * 14)) * math.exp(-d * 7))), 0.0


def pop(t, t0, dur=0.25, over=0.3):
    u = clamp((t - t0) / dur, 0, 1); return max(1e-4, u + over * math.sin(math.pi * u)) if u > 0 else 1e-4


def slam(t, t0):
    """stamp scale: 2.4x down to 1 in 0.12 s, a squash wobble after; 1e-4 before"""
    u = clamp((t - t0) / 0.12, 0, 1)
    if u <= 0: return (1e-4,) * 3
    d = t - t0 - 0.12; sq = 0.1 * math.exp(-d * 16) * math.cos(d * 40) if d > 0 else 0.0
    s = 2.4 - 1.4 * u * u; return (s * (1 + sq), s, s * (1 - sq))


def spring(d, amp, k=6.0, w=14.0): return amp * (1 - math.exp(-k * d) * math.cos(w * d)) if d > 0 else 0.0


def door_angle(t, opens, shuts, full=R(-105)):
    """door swing: list of (t, target) open/shut moves; an opening eases with a little overshoot, a shut slams with a bounce"""
    a = 0.0
    for t0, tgt, kind in sorted([(x, full, 'o') for x in opens] + [(x, 0.0, 's') for x in shuts]):
        d = t - t0
        if d <= 0: break
        if kind == 'o': u = clamp(d / 0.35, 0, 1); a = a + (tgt - a) * (sm(u) + 0.12 * math.sin(math.pi * u))
        else:
            u = clamp(d / 0.14, 0, 1); a = a * (1 - u * u)
            if u >= 1: a = R(-7) * math.exp(-(d - 0.14) * 12) * abs(math.sin((d - 0.14) * 30))
    return a


def puff_at(o, p, s):
    o.location = p; o.scale = (s * 1.25, s, s)


NOSE = [Vector(tuple(p_)) for p_ in BULL_NPZ['nose']]
BK_CLOSED = True


def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- lights: a flicker on "cruelest"; the writer's spot comes up; the last spot stutters on "lost"
    fl = 1.0
    if T_FLICK0 < t < T_FLICK1: fl = (1.0, 0.12, 0.9, 0.3, 0.08, 1.0, 0.2, 0.7)[int((t - T_FLICK0) * 11) % 8]
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * fl
    lt6, e6 = SPOTS['e6']; lt6.data.energy = e6 * (0.25 + 0.75 * smooth(T_WRITER - 0.1, T_WRITER + 0.3, t))
    lt8, e8 = SPOTS['e8']; FIRELT2.data.energy = 0.0
    if T_LOST < t < T_LOST + 0.5: lt8.data.energy = e8 * (1.0, 0.3, 0.8, 0.15, 1.0, 0.5)[int((t - T_LOST) * 12) % 6]
    # ---- exhibit 0: the turntable turns; steam from the nose (a big snort on "brazen"); LEGEND swings on its screw
    TT0.rotation_euler = (0, 0, R(-48) + R(24) * t)
    bpy.context.view_layer.update()
    for k, o in enumerate(STEAM0):
        if t > B[2]: o.location = FAR; continue
        nk = NOSE[k % 2]; d = (t + 0.27 * k) % 1.35; big = 1.0 + 1.6 * smooth(T_STEAM0 - 0.05, T_STEAM0 + 0.1, t) * (1 - smooth(T_STEAM0 + 0.6, T_STEAM0 + 1.4, t))
        p = wpos(BULL0, nk + Vector((0.03 + 0.22 * d * big, 0.03 * (k % 2 * 2 - 1) * d, -0.04 * d + 0.12 * d * d)))
        puff_at(o, p, (0.02 + 0.045 * d) * (1 - d / 1.35) ** 0.5 * big * 1.22)
    PLQ0.rotation_euler = (0, spring(t - T_PLQ, R(-22)), 0)
    # ---- exhibit 1: 570 BC; the ruler's bust rises; the pin drops onto Akragas
    YEAR1.scale = (pop(t, T_YEAR1, 0.25, 0.25),) * 3
    u = smooth(T_BUST - 0.25, T_BUST + 0.2, t); BUSTUP.location = BUSTUP_REST + Vector((0, 0, -0.7 * (1 - u) + 0.02 * math.sin(math.pi * u)))
    BUSTUP.scale = (max(1e-4, min(1.0, u * 3)),) * 3
    d = t - T_PIN
    if d < -0.3: PIN1.location = PIN1_REST + Vector((0, -0.8, 0.4)); PIN1.scale = (1e-4,) * 3
    else:
        PIN1.scale = (1, 1, 1); u = clamp((d + 0.3) / 0.3, 0, 1); PIN1.location = PIN1_REST + Vector((0, -0.8 * (1 - u * u), 0.4 * (1 - u)))
        if d > 0: PIN1.location = PIN1_REST + Vector((0, 0.006 * math.exp(-d * 9) * math.sin(d * 40), 0))
    # ---- exhibit 2: the plans unroll; the model bull drops on its stand; the door creaks, swings open; slams; padlock; fire; pipes, rings
    u = smooth(T_SCROLL, T_SCROLL + 0.55, t); SCRL2.scale = (1, 1, max(1e-4, u))
    p_, w_ = drop(t, T_MODEL, MODEL2_REST, 0.8, 0.36)
    MODEL2.location = p_ if p_ is not None else FAR; MODEL2.rotation_euler = (R(4) * w_, R(-3) * w_, R(12) * w_)
    a_ = door_angle(t, [T_DOOR], [T_SHUT])
    if T_HOLLOW < t < T_SHUT: a_ = min(a_, R(-12) * smooth(T_HOLLOW, T_HOLLOW + 0.4, t) * (1 + 0.15 * math.sin((t - T_HOLLOW) * 18) * math.exp(-(t - T_HOLLOW) * 4)))
    DH2.rotation_euler = (0, 0, a_); HOLE2.hide_render = abs(a_) < R(1.5)
    LOCK2.scale = (pop(t, T_LOCK, 0.18, 0.4),) * 3
    fi = fire_step(FIRE2, t, T_FIRE); FIRELT2.data.energy = 22.0 * fi * (0.7 + 0.3 * math.sin(t * 19) * wob(t, 6, 2.0))
    for k, pp in enumerate(PIPES2): pp.scale = (pop(t, T_PIPES + 0.08 * k, 0.22, 0.35),) * 3
    bpy.context.view_layer.update()
    for k, o in enumerate(RINGS2):
        d = t - T_RINGS - 0.22 * k
        if d < 0 or d > 1.1 or t > B[5] + 0.3: o.location = FAR; continue
        nk = NOSE[k % 2]; o.location = wpos(MODEL2, nk + Vector((0.12 + 0.55 * d, 0.0, 0.0)))
        r_ = (0.025 + 0.09 * d) * MODEL_S * 1.6; o.scale = (r_, r_, r_ * 0.5); o['fade'] = 1.0 - d / 1.1
        o.rotation_euler = (0, R(90), 0)
    for k, o in enumerate(STEAM2):
        if t < T_FIRE + 0.3 or t > B[5] + 0.3: o.location = FAR; continue
        nk = NOSE[k % 2]; d = (t - T_FIRE + 0.33 * k) % 1.6
        puff_at(o, wpos(MODEL2, nk + Vector((0.08 + 0.3 * d, 0, 0.1 * d * d))), (0.012 + 0.035 * d) * (1 - d / 1.6) ** 0.5)
    # ---- exhibit 3: the king shakes; the inventor pawn is pushed into the little bull; the people rise up; the king goes in
    sh = 0.0
    if T_DISG < t < T_DISG + 0.7: d = t - T_DISG; sh = R(12) * math.sin(d * 30) * math.sin(math.pi * d / 0.7)
    d6 = t - T_KINGIN
    if d6 < -0.2: KING3.location = KING3_REST; KING3.rotation_euler = (0, sh, 0); KING3.scale = (1.15,) * 3
    elif d6 < 0.3:
        u = sm(clamp((d6 + 0.2) / 0.5, 0, 1)); KING3.location = KING3_REST.lerp(DOOR3_FRONT, u) + Vector((0, 0, 0.06 * math.sin(math.pi * u))); KING3.scale = (1.15,) * 3
    else:
        u = clamp((d6 - 0.3) / 0.25, 0, 1); KING3.location = DOOR3_FRONT.lerp(DOOR3_MID - Vector((0, 0, 0.03)), sm(u)); KING3.scale = (max(1e-4, 1.15 * (1 - u)),) * 3
    d5 = t - T_INV
    if d5 < 0: INV3.location = INV3_REST; INV3.scale = (1, 1, 1)
    elif d5 < 0.32: u = sm(d5 / 0.32); INV3.location = INV3_REST.lerp(DOOR3_FRONT, u) + Vector((0, 0, 0.05 * math.sin(math.pi * u))); INV3.scale = (1, 1, 1)
    else:
        u = clamp((t - T_TEST) / 0.25, 0, 1); INV3.location = DOOR3_FRONT.lerp(DOOR3_MID - Vector((0, 0, 0.03)), sm(u)); INV3.scale = (max(1e-4, 1 - u),) * 3
    a3 = door_angle(t, [T_INV - 0.15, T_KINGIN - 0.2], [T_TEST + 0.3, T_SHUT6 + 0.12])
    DH3.rotation_euler = (0, 0, a3); HOLE3.hide_render = abs(a3) < R(1.5)
    for k, (o, p0) in enumerate(CROWD3):
        s = pop(t, T_ROSE + 0.05 * k, 0.22, 0.35); o.scale = (s * 0.92,) * 3
        push = smooth(T_KINGIN - 0.3, T_KINGIN + 0.3, t) * 0.05
        o.location = p0 + (KING3_REST - p0).normalized() * push + Vector((0, 0, 0.03 * max(0, math.sin(math.pi * clamp((t - T_ROSE - 0.05 * k) / 0.3, 0, 1)))))
    # ---- exhibit 4: ? pops; the book opens; the 500-year line grows; MADE UP?
    QM4.scale = (pop(t, T_QMARK, 0.25, 0.3),) * 3; QM4.rotation_euler = (0, 0, R(8) * math.sin(t * 2.2))
    e = smooth(T_BOOK, T_BOOK + 0.55, t)
    for pv, s_ in PG4:
        if s_ > 0: pv.rotation_euler = (0, -R(178) * (1 - e), 0); pv.location.z = 0.012 + 0.026 * (1 - e)
    TLBAR.scale = (max(1e-4, smooth(T_TL0, T_TL1 + 0.2, t)), 1, 1)
    TLTXT.scale = (pop(t, T_TL1 + 0.15, 0.25, 0.3),) * 3
    STAMP4.scale = slam(t, T_MADEUP)
    # ---- exhibit 5: REAL; CARTHAGE and 406 BC; the token rides to Carthage; 146 BC, the helmet drops; it rides home
    REAL5.scale = slam(t, T_REAL)
    CARLBL5.scale = (pop(t, T_CARTH, 0.22, 0.3),) * 3; CARD5A.scale = (pop(t, T_CARTH + 0.1, 0.22, 0.3),) * 3
    CARD5B.scale = (pop(t, T_YEAR10, 0.22, 0.3),) * 3
    u1 = sm(clamp((t - T_CARRY) / 1.1, 0, 1)); u2 = sm(clamp((t - T_BACK) / 1.0, 0, 1))
    if t < T_BACK: u = u1; mv = 0 < t - T_CARRY < 1.1
    else: u = 1 - u2; mv = 0 < t - T_BACK < 1.0
    p_ = arc5(u); hop = 0.012 * abs(math.sin(t * 22)) if mv else 0.0
    du = 0.02; dv = arc5(min(1, u + du)) - arc5(max(0, u - du))
    if t >= T_BACK: dv = -dv
    rz = math.atan2(dv.y, dv.x) if dv.length > 1e-6 else math.atan2(-0.22, -0.42)
    if t < T_CARRY: rz = math.atan2(-0.22, -0.42)
    TOK5.location = p_ + Vector((0, 0, hop)); TOK5.rotation_euler = (0, 0, rz)
    p_, w_ = drop(t, T_HELM, HELM5_REST, 0.7, 0.32)
    HELM5.location = p_ if p_ is not None else FAR; HELM5.rotation_euler = (R(25) * w_, R(-15) * w_, R(-20) + R(60) * w_)
    # ---- exhibit 6: the scroll unrolls
    u = smooth(T_REMIND - 0.1, T_REMIND + 0.5, t); SCRL6.scale = (1, 1, max(1e-4, u)); ROLL6.location.z = 2.2 - 0.8 * u
    # ---- exhibit 7: the statue drops onto its rock with a splash; the water starts to run, ripples spread
    p_, w_ = drop(t, T_STATUE, STAT7_REST, 0.9, 0.36)
    STAT7.location = p_ if p_ is not None else FAR; STAT7.rotation_euler = (0, 0, R(-18) + R(10) * w_)
    WATER_MAP.inputs['Location'].default_value = (0.04 * t + 0.9 * max(0.0, t - T_RIVER) * smooth(T_RIVER, T_RIVER + 0.5, t), 0.02 * t, 0.15 * t)
    for k, o in enumerate(RIPS7):
        t0 = (T_STATUE if k < 2 else T_RIVER + 0.25 * (k - 2)); d = t - t0 - 0.12 * (k % 2)
        if d < 0 or d > 1.4: o.location = FAR; continue
        c_ = Vector((X7 + (0.0 if k < 2 else -0.45 + 0.3 * (k - 2)), Y7 + (0.0 if k < 2 else 0.12 * ((k % 2) * 2 - 1)), 0.292))
        o.location = c_; r_ = 0.12 + 0.35 * d; o.scale = (r_, r_ * 0.85, 1)
    for k, o in enumerate(SPL7):
        d = t - T_STATUE
        if not 0 < d < 0.7: o.location = FAR; continue
        a_ = 2 * math.pi * k / len(SPL7); v = Vector((math.cos(a_) * 0.6, math.sin(a_) * 0.35, 1.4))
        p = Vector((X7, Y7, 0.31)) + Vector((v.x * d, v.y * d, v.z * d - 4.9 * d * d))
        if p.z < 0.28: o.location = FAR; continue
        puff_at(o, p, 0.018 * (1 - d / 0.7) + 0.004)
    # ---- exhibit 8: a ghost of the bull shows on the empty plinth and fades; the ? pops
    g = smooth(T_LOST - 0.05, T_LOST + 0.25, t) * (1 - smooth(T_LOST + 0.9, T_LOST + 1.5, t))
    if g < 0.01: GHOST8.location = FAR
    else: GHOST8.location = (X8 - 0.03, Y8, 0.942); GHOST8.rotation_euler = (0, 0, R(-20))
    bpy.data.materials['ghost8'].node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.3 * g
    QM8.scale = (pop(t, T_QM13, 0.25, 0.35),) * 3; QM8.rotation_euler = (0, 0, R(10) * math.sin(t * 2.0))
    # ---- camera, with a nod on each thud
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.005, 1.0, 1.3)
    for tn, a_ in ((T_MODEL, 0.008), (T_SHUT, 0.01), (T_TEST + 0.3, 0.006), (T_SHUT6 + 0.12, 0.008), (T_MADEUP, 0.008), (T_REAL, 0.008), (T_HELM, 0.008), (T_STATUE, 0.01)):
        if t > tn: cp = cp + shake(t, a_, 4.0, 13.0) * math.exp(-(t - tn) * 6.0)
    look(cp, ct, lens, 8.0)
    bpy.context.view_layer.update()
