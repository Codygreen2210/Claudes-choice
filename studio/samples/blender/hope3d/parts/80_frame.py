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
    key(0.0, (X0, 2.8, 1.4), (X0, 3.75, 1.24), 34),                        # the necklace rises in its case
    key(1.4, (X0, 2.9, 1.37), (X0, 3.75, 1.22), 34),
    key(2.2, (X0 + 0.05, 2.45, 1.55), (X0, 3.75, 1.15), 26),               # back: the lights flicker, the glass cracks, the plaque drops
    key(B[1] - 0.15, (X0 + 0.05, 2.47, 1.55), (X0, 3.75, 1.15), 26),
    key(B[1] + 0.7, (X1 + 0.15, 2.5, 1.6), (X1 + 0.15, 4.4, 1.5), 24),    # India to France: stone, banner, crown
    key(B[1] + 3.5, (X1 + 0.15, 2.55, 1.6), (X1 + 0.15, 4.4, 1.5), 24),
    key(B[1] + 4.15, (X1 - 0.08, 3.0, 1.48), (X1 - 0.06, 3.85, 1.1), 32),  # in on the wheel: the French Blue
    key(B[2] - 0.15, (X1 - 0.08, 3.03, 1.47), (X1 - 0.06, 3.85, 1.1), 32),
    key(B[2] + 0.7, (X2, 2.75, 1.75), (X2, 4.1, 1.15), 26),                # 1792: the crown jewels case
    key(B[2] + 3.2, (X2, 2.8, 1.73), (X2, 4.1, 1.15), 26),
    key(B[2] + 3.75, (X2 + 0.02, 3.05, 1.5), (X2 + 0.02, 3.8, 1.0), 34),  # in: the French Blue vanishes
    key(B[3] - 0.15, (X2 + 0.02, 3.07, 1.49), (X2 + 0.02, 3.8, 1.0), 34),
    key(B[3] + 0.75, (X3, 2.95, 1.6), (X3, 3.85, 1.12), 32),               # London: a smaller blue stone
    key(B[3] + 3.0, (X3, 3.0, 1.58), (X3, 3.85, 1.12), 32),
    key(B[3] + 3.6, (X3, 3.12, 1.5), (X3, 3.85, 1.14), 36),                # the scan outline fits round it
    key(B[4] - 0.15, (X3, 3.13, 1.5), (X3, 3.85, 1.14), 36),
    key(B[4] + 0.7, (X4 - 0.26, 3.12, 1.68), (X4 - 0.28, 3.95, 1.12), 30), # the catalog opens
    key(B[4] + 1.45, (X4 - 0.25, 3.14, 1.67), (X4 - 0.28, 3.95, 1.12), 30),
    key(B[4] + 1.95, (X4 + 0.1, 2.85, 1.72), (X4 + 0.2, 5.36, 1.8), 28),   # up to the nameplate: H-O-P-E
    key(B[5] - 0.15, (X4 + 0.1, 2.88, 1.72), (X4 + 0.2, 5.36, 1.8), 28),
    key(B[5] + 0.6, (X5 - 0.45, 3.0, 2.2), (X5 - 0.45, 5.36, 2.4), 26),    # the scare papers, MADE UP
    key(B[5] + 1.85, (X5 - 0.45, 3.05, 2.2), (X5 - 0.45, 5.36, 2.4), 26),
    key(B[5] + 2.6, (CX5 + 0.12, 2.8, 1.75), (CX5 + 0.12, 4.0, 1.15), 26), # the jeweler's counter: SOLD
    key(B[6] - 0.15, (CX5 + 0.12, 2.83, 1.74), (CX5 + 0.12, 4.0, 1.15), 26),
    key(B[6] + 0.6, (X6 - 0.12, 2.75, 1.68), (X6 - 0.12, 4.0, 1.05), 26),  # 1958: the plain package
    key(B[7] - 0.1, (X6 - 0.1, 2.78, 1.67), (X6 - 0.12, 4.0, 1.05), 26),
    key(B[7] + 0.45, (X6 + 0.08, 3.0, 1.45), (X6 + 0.08, 3.9, 0.9), 28),   # in: stamps, $2.44
    key(B[7] + 2.4, (X6 + 0.08, 3.02, 1.44), (X6 + 0.08, 3.9, 0.9), 28),
    key(B[7] + 3.1, (X6 + 0.28, 2.2, 1.85), (X6 + 0.28, 4.0, 1.3), 22),    # wide: the mailman shrugs off the curse
    key(B[7] + 4.5, (X6 + 0.3, 2.22, 1.85), (X6 + 0.3, 4.0, 1.3), 22),
    key(B[8] + 0.55, (X8 + 0.1, 2.65, 1.62), (X8 + 0.05, 3.75, 1.35), 26), # the last case: it bursts open, the necklace rises
    key(B[8] + 1.4, (X8 + 0.12, 2.8, 1.48), (X8 + 0.05, 3.75, 1.3), 26),   # ultraviolet: it glows red
    key(B[9] + 0.1, (X8 + 0.12, 2.86, 1.46), (X8 + 0.05, 3.75, 1.3), 26),
    key(TOTAL, (X8 + 0.05, 2.45, 1.65), (X8, 3.75, 1.3), 24),
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


J2_REST = [o.location.copy() for o in JEWELS2]; LID2_REST = LID2.location.copy(); FB2R_REST = FB2R.location.copy()
NEWS_REST = [(o.location.copy(), o.rotation_euler.copy()) for o, _, _ in NEWS]
PKG_TOP8 = Vector((X8, Y8, 1.0 + 0.66 + 0.006))
def wheel_angle(t):
    a = 0.0; n = 160; t0 = T_WHEEL
    if t <= t0: return 0.0
    dt = (t - t0) / n
    for i in range(n):
        tt = t0 + (i + 0.5) * dt; w = 32.0 * smooth(T_WHEEL, T_WHEEL + 0.45, tt) * (1 - smooth(T_CUT + 0.4, T_CUT + 1.3, tt)); a += w * dt
    return a


def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- lights: a flicker on "bad luck"; the crown-jewel spot dims after the theft; the room goes dark for the ultraviolet lamp
    fl = 1.0
    if T_FLICK0 < t < T_FLICK1: fl = (1.0, 0.12, 0.9, 0.3, 0.08, 1.0, 0.2, 0.7)[int((t - T_FLICK0) * 11) % 8]
    dim = 1.0 - 0.9 * smooth(T_DIM0, T_DIM1, t) * (1.0 - smooth(T_UVOFF, T_LUP, t))
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * fl * dim
    lt2, e2 = SPOTS['e2']; lt2.data.energy = e2 * fl * (1 - 0.7 * smooth(T_VANISH + 0.2, T_VANISH + 0.7, t)) * dim
    # ---- exhibit 0: the necklace rises; the glass cracks; the plaque drops crooked
    u = smooth(T_RISE0, T_RISE1, t); BD0.location = BD0_REST + Vector((0, 0, -0.65 * (1 - u) + 0.012 * math.sin(math.pi * u)))
    for k, o in enumerate(CRACK): o.hide_render = t < T_CRACK + 0.03 * k
    PLQ0.rotation_euler = (0, spring(t - T_PLQ, R(24)), 0)
    # ---- exhibit 1: the rough stone lands; banner and crown; the wheel spins, sparks fly; the stone becomes the French Blue
    p_, w_ = drop(t, T_ROUGH, ROUGH_REST, 0.9, 0.4)
    if p_ is None or t > T_CUT + 0.06: ROUGH.location = FAR
    else:
        jit = Vector((wob(t, 40, 1) * 0.003, 0, 0)) * smooth(T_WHEEL + 0.3, T_WHEEL + 0.5, t)
        ROUGH.location = p_ + jit; ROUGH.rotation_euler = (R(30) * w_, R(-20) * w_, R(40) * w_)
        s = 1.0 - smooth(T_CUT - 0.06, T_CUT + 0.06, t); ROUGH.scale = (max(s, 1e-4),) * 3
    s = pop(t, T_CUT, 0.22, 0.35); FB1.scale = (s, s, s); FB1.location = FB1_REST if t >= T_CUT else FAR
    BAN1.scale = (1.0, 1.0, pop(t, T_BAN, 0.35, 0.08))
    p_, w_ = drop(t, T_CROWN, CROWN1_REST, 0.9, 0.38)
    CROWN1.location = p_ if p_ is not None else FAR; CROWN1.rotation_euler = (R(8) * w_, R(-6) * w_, R(60) * w_)
    WHEEL.rotation_euler = (0, wheel_angle(t), 0)
    for o, vx, vy, vz, dl in SPARKS:
        on = T_WHEEL + 0.35 < t < T_CUT
        if not on: o.location = FAR; continue
        d = (t - T_WHEEL - 0.35 - dl) % 0.5
        o.location = Vector((X1 + 0.04, 3.83, 1.13)) + Vector((vx * d, vy * d * 0.3 - 0.05 * d, vz * d - 4.9 * d * d))
        o.scale = (1.0 - d / 0.5,) * 3
    # ---- exhibit 2: 1792 - the lid flips up, STOLEN, the jewels are snatched one by one; the French Blue vanishes in a sparkle
    YEAR2.scale = (pop(t, T_YEAR2),) * 3
    d = t - T_LID
    if d < 0: LID2.location = LID2_REST; LID2.rotation_euler = (0, 0, 0)
    elif d < 1.0: LID2.location = LID2_REST + Vector((0.1 * d, 0.3 * d, 0.5 * d + 6.0 * d * d)); LID2.rotation_euler = (-R(80) * min(1, d / 0.3), R(25) * d, 0)
    else: LID2.location = FAR
    STAMP2.scale = slam(t, T_STAMP2)
    for k, (o, r0) in enumerate(zip(JEWELS2, J2_REST)):
        ty = T_YANK[(k - 1) % 4]; d = t - ty
        if d < 0: o.location = r0; o.rotation_euler = (0, 0, 0); continue
        if d > 1.2: o.location = FAR; continue
        sx = (-1, 1, -1, 1)[k]; o.location = r0 + Vector((0.12 * sx * d, 0.25 * d, 0.6 * d + 7.0 * d * d)); o.rotation_euler = (R(200) * d, R(140) * d * sx, R(260) * d)
    s = 1.0 - smooth(T_VANISH, T_VANISH + 0.16, t); FB2R.scale = (max(s, 1e-4),) * 3
    FB2R.location = FB2R_REST + Vector((0, 0, 0.03 * smooth(T_VANISH - 0.15, T_VANISH, t)))
    for o, v, ph in POOF:
        d = t - T_VANISH
        if not 0 < d < 0.7: o.location = FAR; continue
        o.location = FB2R_REST + Vector((0, 0, 0.03)) + v * d * (1.0 - 0.5 * d); s = math.sin(math.pi * d / 0.7) * 0.9; o.scale = (s, s, s); o.rotation_euler = (ph + 9 * d, ph, 7 * d)
    # ---- exhibit 3: London - the smaller blue stone pops up; the French Blue's outline comes down and fits round it; a green check
    s = pop(t, T_HOPE3, 0.22, 0.35); HOPE3.scale = (s, s, s); HOPE3.location = HOPE3_REST + Vector((0, 0, 0.04 * math.sin(math.pi * clamp((t - T_HOPE3) / 0.3, 0, 1))))
    if t < T_SCAN0: GHOST.scale = (1e-4,) * 3
    else:
        u = smooth(T_SCAN0 + 0.15, T_FIT, t); s = pop(t, T_SCAN0, 0.2, 0.2) * (1 + 0.06 * math.sin(math.pi * clamp((t - T_CHECK) / 0.3, 0, 1)))
        GHOST.scale = (s, s, s); GHOST.location = HOPE3_REST + Vector((0, 0, 0.42 * (1 - u))); GHOST.rotation_euler = (0, 0, R(70) * (1 - u))
    CHECK3.scale = (pop(t, T_CHECK, 0.22, 0.4),) * 3
    # ---- exhibit 4: the catalog opens; H-O-P-E drop onto the nameplate
    e = smooth(T_BOOK0, T_BOOK1, t)
    for pv, s_ in PG4:
        if s_ > 0: pv.rotation_euler = (0, -R(178) * (1 - e), 0); pv.location.z = 0.012 + 0.026 * (1 - e)
    bpy.data.objects['bk4gem'].hide_render = e < 0.6
    for k, (o, r0) in enumerate(zip(LET4, LET4_REST)):
        d = t - (T_LET + 0.1 * k)
        if d < -0.15: o.location = r0 + Vector((0, -0.5, 0.6)); o.scale = (1e-4,) * 3; continue
        o.scale = (1, 1, 1)
        if d < 0: u = (d + 0.15) / 0.15; o.location = r0 + Vector((0, -0.25 * (1 - u), 0.5 * (1 - u * u)))
        else: o.location = r0 + Vector((0, 0, 0.02 * abs(math.sin(d * 18)) * math.exp(-d * 9)))
    SUB4.scale = (pop(t, T_SUB4),) * 3
    # ---- exhibit 5: the scare papers fly onto the board; MADE UP; at the counter a SOLD tag swings on and coins drop
    for k, (np_, (r0, e0)) in enumerate(zip([n[0] for n in NEWS], NEWS_REST)):
        d = t - T_NEWS[k]
        if d < -0.28: np_.location = FAR; continue
        if d < 0:
            u = sm((d + 0.28) / 0.28); np_.location = r0.lerp(r0 + Vector((-0.4 + 0.4 * k, -1.5, 0.6)), 1 - u)
            np_.rotation_euler = (e0.x + R(70) * (1 - u), e0.y + R(200) * (1 - u) * (1 if k % 2 else -1), e0.z)
        else:
            np_.location = r0; np_.rotation_euler = e0; sq = 0.05 * math.exp(-d * 14) * math.cos(d * 40); np_.scale = (1 + sq, 1, 1 - sq)
    STAMP5.scale = slam(t, T_STAMP5)
    s = pop(t, T_SOLD, 0.2, 0.3); TAG5.scale = (s, s, s); TAG5.rotation_euler = (R(18) * math.exp(-3 * max(0, t - T_SOLD)) * math.sin(9 * max(0, t - T_SOLD)), 0, 0)
    for o, rest, rz, dl in COINS:
        p_, w_ = drop(t, T_COIN + dl, rest, 0.5, 0.3)
        o.location = p_ if p_ is not None else FAR; o.rotation_euler = (R(160) * w_, R(90) * w_, rz)
    # ---- exhibit 6: the plain package thuds down; 1958; the address label, FRAGILE, the stamps, $2.44; the mailman shakes his head, CURSE falls
    PKG.scale = (1, 1, 1)
    if t < T_FLY0:
        p_, w_ = drop(t, T_PKG, PKG_REST, 0.9, 0.35)
        PKG.location = p_ if p_ is not None else FAR; PKG.rotation_euler = (R(12) * w_, R(-8) * w_, R(-25) * w_)
    elif t < T_FLY1:
        u = sm((t - T_FLY0) / (T_FLY1 - T_FLY0)); uh = u ** 1.6; PKG.location = PKG_REST.lerp(PKG_TOP8, uh) + Vector((0, 0, 1.5 * math.sin(math.pi * u)))
        PKG.rotation_euler = (R(25) * math.sin(math.pi * u), 0, R(360) * u)
    elif t < T_BURST:
        d = t - T_FLY1; PKG.location = PKG_TOP8 + Vector((0, 0, 0.02 * abs(math.sin(d * 14)) * math.exp(-d * 7))); PKG.rotation_euler = (0, 0, 0)
        sq = 0.08 * smooth(T_BURST - 0.15, T_BURST, t); PKG.scale = (1 + sq, 1 + sq, 1 - sq)
    else: PKG.location = FAR
    YEAR6.scale = (pop(t, T_YEAR6, 0.25, 0.25),) * 3
    LABEL6.scale = slam(t, T_LABEL); FRAG6.scale = slam(t, T_FRAG)
    for st, ts in zip(STAMPS6, T_STAMPS): st.scale = slam(t, ts)
    s = pop(t, T_TAG6, 0.22, 0.3); TAG6.scale = (s, s, s); TAG6.rotation_euler = (0, R(10) * math.exp(-3 * max(0, t - T_TAG6)) * math.sin(10 * max(0, t - T_TAG6)), 0)
    a_ = 0.0
    if T_SHAKE0 < t < T_SHAKE1 + 0.2: d = t - T_SHAKE0; a_ = R(16) * math.sin(2 * math.pi * 2.6 * d) * math.sin(math.pi * clamp(d / (T_SHAKE1 + 0.2 - T_SHAKE0), 0, 1))
    MM.rotation_euler = (0, 0, a_)
    d = t - T_CURSE6
    CS6.rotation_euler = (-R(88) * clamp(d / 0.22, 0, 1) ** 2 + (R(4) * math.exp(-d * 10) * abs(math.sin(d * 25)) if d > 0.22 else 0.0), 0, 0) if d > 0 else (0, 0, 0)
    # ---- exhibit 8: the package bursts; the necklace rises; ultraviolet - it glows red like a hot coal, and keeps glowing after the lamp goes off
    for o, v, w in SCRAPS:
        d = t - T_BURST
        if not 0 < d < 1.3: o.location = FAR; continue
        pz = PKG_TOP8.z + 0.06 + v.z * d - 4.9 * d * d
        if pz < 0.02: o.location = FAR; continue
        o.location = Vector((PKG_TOP8.x + v.x * d * 0.6, PKG_TOP8.y + v.y * d * 0.6, pz)); o.rotation_euler = tuple(w * d)
    u = smooth(T_BURST + 0.05, T_RISE8, t); BD8.location = BD8_REST + Vector((0, 0, -0.65 * (1 - u) + 0.012 * math.sin(math.pi * u)))
    uv = (T_UV < t < T_UVOFF) and not (T_UV + 0.06 < t < T_UV + 0.12)
    UVLIGHT.data.energy = 70.0 * uv; UVT.hide_render = not uv
    g = smooth(T_UV + 0.1, T_GLOW1, t) * (1 + 0.25 * math.sin(math.pi * clamp((t - T_COAL) / 0.5, 0, 1)))
    if t > T_UVOFF: g = math.exp(-(t - T_UVOFF) / 0.9)
    HOPE8['glow'] = g
    # ---- glints
    for g_ in GLS_O: g_.hide_render = True; g_.scale = (0.0,) * 3
    for gi, t0, pw, sz in GLS:
        u = clamp((t - t0) / 0.35, 0, 1)
        if 0 < u < 1: g_ = GLS_O[gi]; s = math.sin(math.pi * u) * sz; g_.scale = (s, s, s); g_.rotation_euler = (0, u * 1.2, 0); g_.location = pw; g_.hide_render = False
    # ---- camera, with a nod on each thud
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.005, 1.0, 1.3)
    for tn, a_ in ((T_CROWN, 0.006), (T_STAMP5, 0.01), (T_PKG, 0.012), (T_FLY1, 0.008), (T_BURST, 0.01)):
        if t > tn: cp = cp + shake(t, a_, 4.0, 13.0) * math.exp(-(t - tn) * 6.0)
    look(cp, ct, lens, 8.0)
    bpy.context.view_layer.update()
