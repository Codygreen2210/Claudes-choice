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
    key(0.0, (0.12, 1.15, 2.2), (0.12, 2.55, 2.25), 30),                  # the buckled hat drops onto the Pilgrim's head
    key(0.9, (0.14, 1.2, 2.18), (0.12, 2.55, 2.22), 30),
    key(3.0, (0.75, -0.2, 1.85), (0.0, 2.3, 1.45), 26),                    # back a little: the harvest table, the two Pilgrims in black
    key(B[1] - 0.05, (0.7, -0.25, 1.85), (0.0, 2.3, 1.45), 26),
    key(B[1] + 1.7, (1.4, -6.4, 2.45), (0.4, 1.6, 1.85), 24),             # pull way back: a diorama in a museum
    key(B[2] - 0.05, (1.5, -6.5, 2.47), (0.45, 1.6, 1.85), 24),
    key(B[2] + 1.2, (EX, 3.05, 2.75), (EX, 5.3, 2.72), 30),               # the inventory page writes itself
    key(B[3] - 0.05, (EX, 3.1, 2.73), (EX, 5.3, 2.72), 30),
    key(B[3] + 1.2, (EX, 0.4, 2.05), (EX, 4.2, 1.6), 22),                 # back: the page and four stands; the clothes fly in
    key(B[4] - 0.45, (EX, 0.5, 2.0), (EX, 4.2, 1.6), 22),
    key(B[4] + 0.3, (BX + 0.05, 2.1, 1.45), (BX + 0.05, 3.5, 1.15), 24),  # the buckles pop off
    key(B[5] - 0.05, (BX + 0.05, 2.15, 1.43), (BX + 0.05, 3.5, 1.15), 24),
    key(B[5] + 0.7, (DX + 0.16, 1.95, 1.6), (DX + 0.16, 3.7, 1.1), 24),                 # the dye jars, coins stack by the black
    key(B[5] + 1.9, (DX + 0.16, 1.97, 1.62), (DX + 0.16, 3.7, 1.12), 24),
    key(B[5] + 3.0, (DX, 2.6, 2.55), (DX, 5.3, 2.8), 28),                 # up to the portrait in Sunday black
    key(B[6] - 0.05, (DX + 0.02, 2.65, 2.55), (DX, 5.3, 2.8), 28),
    key(B[6] + 0.9, (AX - 0.05, 1.6, 1.45), (AX, 2.95, 1.33), 25),        # the 1800s artist paints the buckles on
    key(B[7] - 0.05, (AX - 0.03, 1.65, 1.43), (AX, 2.95, 1.33), 25),
    key(B[7] + 0.9, (SX - 0.35, 1.45, 1.75), (SX - 0.1, 3.6, 1.45), 23),  # the same buckle on Santa
    key(B[8] - 0.05, (SX - 0.32, 1.5, 1.73), (SX - 0.1, 3.6, 1.45), 23),
    key(TOTAL, (SX - 0.25, 2.1, 1.55), (SX - 0.15, 3.6, 1.4), 26),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- the hat drops onto the Pilgrim, bounces, settles
    T_HIT = 0.32
    if t < T_HIT:
        u = (t + 0.25) / (T_HIT + 0.25); HAT1.location = HAT1_P + Vector((0, 0, 1.0 * (1 - u * u))); HAT1.rotation_euler = (R(8) * (1 - u), R(-6) * (1 - u), R(50) * (1 - u))
        HAT1.scale = (1, 1, 1)
    else:
        d = t - T_HIT; b_ = 0.035 * abs(math.sin(d * 13)) * math.exp(-d * 7)
        HAT1.location = HAT1_P + Vector((0, 0, b_)); w_ = R(3) * math.sin(d * 17) * math.exp(-d * 6); HAT1.rotation_euler = (w_, -w_ * 0.6, 0)
        sq = 0.12 * math.exp(-d * 18) * math.cos(d * 30); HAT1.scale = (1 + sq * 0.5, 1 + sq * 0.5, 1 - sq)
    # ---- leaves drift down through the diorama (fade out once the room is lit)
    lf_on = t < B[1] + 0.9
    for o, x0, y0, ph, sp, rot in LEAVES:
        if not lf_on: o.location = (0, 0, -50); continue
        z = 4.2 - ((t * sp + ph) % 3.85)
        o.location = (x0 + 0.15 * math.sin(t * 2.1 + rot), y0 + 0.08 * math.cos(t * 1.7 + rot), z)
        o.rotation_euler = (math.sin(t * 3 + rot) * 0.9, math.cos(t * 2.4 + rot) * 0.7, t * 1.5 + rot)
    # ---- the museum lights come up as the diorama is revealed
    ml = smooth(B[1] + 0.1, B[1] + 0.9, t)
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * ml; lt.hide_render = ml < 0.002
    # ---- the page: scribbled lines during B2, then the four items as they're named; the quill follows the writing
    qp = Vector((0.35, -0.08, -0.62)); qa = 0.0
    for k, (o, x0, L_) in enumerate(SCRIB):
        s = clamp((t - (B[2] + 0.25 + 0.5 * k)) / 0.45, 0, 1)
        o.scale = (max(s, 0.0001), 1, 1); o.location.x = x0 * (1 - s); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((x0 + L_ * s, -0.08, 0.32 - 0.075 * k)); qa = 1.0
    for k, o in enumerate(ITEMT):
        s = clamp((t - (ITEM_T[k] - 0.2)) / 0.4, 0, 1); o.scale = (max(s, 0.0001), 1, 1); o.hide_render = s <= 0
        if 0 < s < 1: qp = Vector((-0.48 + 0.42 * s, -0.08, -0.17 - 0.115 * k)); qa = 1.0
    QUILL.location = qp + Vector((0, 0, 0.008 * math.sin(t * 60) * qa)); QUILL.rotation_euler = (0, R(-10) + 0.15 * math.sin(t * 25) * qa, 0)
    # ---- the clothes fly off the page onto their stands, growing as they come, a turn and a flutter
    for nm, (off, t0, ctr) in FLY.items():
        o = CL[nm]; u = smooth(t0, t0 + 0.6, t)
        if u <= 0: o.scale = (0.0001,) * 3; o.hide_render = True; continue
        o.hide_render = False; s = 0.15 + 0.85 * u
        lift = 0.25 * math.sin(math.pi * u)
        pos = off * (1 - u) + Vector((0, 0, lift)); rz = R(200) * (1 - u) ** 1.5; tilt = R(25) * math.sin(math.pi * u)
        m_ = Matrix.Translation(ctr + pos) @ Euler((tilt, 0, rz)).to_matrix().to_4x4() @ Matrix.Diagonal((s, s, s, 1)) @ Matrix.Translation(-ctr)
        o.matrix_basis = m_
        if 0.999 > u > 0.9: pass
        settle = 0.03 * math.sin((t - t0 - 0.6) * 20) * math.exp(-(t - t0 - 0.6) * 9) if t > t0 + 0.6 else 0.0
        if settle: o.matrix_basis = Matrix.Translation(ctr) @ Euler((0, 0, settle)).to_matrix().to_4x4() @ Matrix.Translation(-ctr)
    # ---- the buckles pop off the hat and the shoes, spin, and land on the floor
    for k, b_ in enumerate(BUCKLES):
        l0, r0 = BUCK_REST[k]; tau = t - BUCK_T[k]
        if tau <= 0: b_.location = l0; b_.rotation_euler = r0; continue
        p_ = l0 + BUCK_V[k] * tau + Vector((0, 0, -4.9 * tau * tau))
        if p_.z <= BUCK_FLOOR[k]:
            tl = (BUCK_V[k].z + math.sqrt(BUCK_V[k].z ** 2 + 2 * 9.8 * (l0.z - BUCK_FLOOR[k]))) / 9.8
            p_ = l0 + BUCK_V[k] * tl + Vector((0, 0, -4.9 * tl * tl)); p_.z = BUCK_FLOOR[k]
            b_.location = p_; b_.rotation_euler = (R(90), 0, R(30) * k); continue
        b_.location = p_; b_.rotation_euler = (r0.x + tau * 14, r0.y + tau * 6, r0.z + tau * 9)
    # ---- the coins stack up beside the black dye
    for k, o in enumerate(COINS):
        u = clamp((t - (B[5] + 0.5 + 0.11 * k)) / 0.18, 0, 1); s = u * u * (3 - 2 * u) + 0.25 * math.sin(math.pi * u)
        o.scale = (max(s, 0.0001), max(s, 0.0001), max(s, 0.0001)); o.hide_render = u <= 0
    # ---- the artist paints: each stroke grows from its middle; the brush goes where the paint goes
    bp = Vector((0.3, -0.05, -0.2)); act = 0.0
    for k, o in enumerate(PAINT):
        t0 = B[6] + 0.3 + 0.3 * k; s = clamp((t - t0) / 0.28, 0, 1); c_ = PAINT_C[k]
        o.scale = (max(s, 0.0001), 1, max(s, 0.0001)); o.location = Vector((c_.x * (1 - s), 0, c_.z * (1 - s))); o.hide_render = s <= 0
        if t0 - 0.12 <= t <= t0 + 0.3: bp = Vector((c_.x, -0.05, c_.z)); act = 1.0
    BRUSH.location = bp + Vector((0.01 * math.sin(t * 40) * act, 0, 0.008 * math.cos(t * 33) * act))
    # ---- Santa: the tree twinkles, the two buckles glint
    for k, o in enumerate(TLIGHTS): o.scale = (0.7 + 0.3 * math.sin(t * 5 + k * 1.7),) * 3
    for g_, t0 in ((GL1, B[7] + 1.4), (GL2, B[7] + 2.4), (GL1, B[8] + 0.6), (GL2, B[8] + 1.2)):
        u = clamp((t - t0) / 0.35, 0, 1)
        if 0 < u < 1: s = math.sin(math.pi * u); g_.scale = (s, s, s); g_.rotation_euler = (0, u * 1.2, 0); g_.hide_render = False
    if all(not (0 < (t - t0) < 0.35) for t0 in (B[7] + 1.4, B[8] + 0.6)): GL1.hide_render = True
    if all(not (0 < (t - t0) < 0.35) for t0 in (B[7] + 2.4, B[8] + 1.2)): GL2.hide_render = True
    # ---- camera, with a little life in it (a nod when the hat lands)
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3) + (shake(t, 0.02, 4.0, 13.0) * math.exp(-max(0, t - 0.32) * 6.0) if t > 0.32 else Vector())
    look(cp, ct, lens, 5.6)
    bpy.context.view_layer.update()
