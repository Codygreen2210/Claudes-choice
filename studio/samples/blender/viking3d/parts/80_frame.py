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
    key(0.0, (-0.08, 0.98, 1.66), (-0.42, 2.75, 1.42), 24),             # on deck, the helmet in front: the wave smashes over the far rail
    key(0.8, (-0.02, 0.92, 1.68), (-0.40, 2.75, 1.45), 24),
    key(2.7, (1.05, -0.85, 2.05), (-0.55, 1.75, 1.75), 24),              # out to the side: the whole bow, the dragon, the storm
    key(B[1] - 0.05, (0.95, -0.95, 2.05), (-0.55, 1.75, 1.75), 24),
    key(B[1] + 1.7, (1.5, -6.4, 2.45), (0.4, 1.6, 1.85), 24),            # pull way back: a diorama in a museum
    key(B[2] - 0.05, (1.6, -6.5, 2.47), (0.45, 1.6, 1.85), 24),
    key(B[2] + 1.3, (8.6, -1.25, 2.15), (7.3, 2.6, 0.75), 26),           # the grave mound, cut open; the shovel digs
    key(B[3] - 0.05, (8.5, -1.15, 2.1), (7.3, 2.6, 0.78), 26),
    key(B[3] + 0.9, (7.95, 0.40, 1.55), (7.5, 2.25, 1.02), 28),          # the nine pieces fly up onto the stand
    key(B[4] - 0.55, (7.88, 0.50, 1.50), (7.5, 2.2, 1.06), 28),
    key(B[4] + 0.25, (11.1, 0.3, 1.65), (11.1, 2.65, 1.38), 24),         # the sword hooks the horn, the helmet flies off
    key(B[5] - 0.05, (11.0, 0.4, 1.6), (10.9, 2.6, 1.3), 24),
    key(B[5] + 1.0, (16.3, -2.6, 2.35), (16.3, 2.0, 2.4), 24),           # the opera stage: the curtains open
    key(B[6] - 0.05, (16.3, -2.4, 2.32), (16.3, 2.0, 2.4), 24),
    key(B[6] + 0.9, (18.83, -0.08, 1.42), (19.27, 0.98, 1.28), 28),       # Doepler's sketch on the easel
    key(B[6] + 1.45, (18.8, -0.05, 1.43), (19.27, 0.98, 1.28), 28),
    key(B[6] + 2.25, (16.3, -0.6, 2.1), (16.3, 2.8, 2.25), 28),          # the costumes in the spotlights
    key(B[7] - 0.05, (16.33, -0.5, 2.08), (16.3, 2.8, 2.25), 28),
    key(B[7] + 0.45, (19.2, -1.0, 2.0), (20.6, 4.2, 1.85), 25),           # (wide of the stage corner)
    key(B[7] + 0.95, (21.4, 1.3, 1.9), (21.4, 5.1, 1.75), 26),            # the shelf fills with horned helmets
    key(B[8] - 0.05, (21.4, 1.45, 1.88), (21.4, 5.1, 1.75), 26),
    key(B[8] + 0.7, (22.3, 0.2, 2.6), (26.0, 0.0, 2.4), 22),             # turn to the window ...
    key(B[8] + 1.5, (24.6, 0.0, 2.3), (31.5, 0.0, -0.4), 22),            # ... and out over the bog
    key(B[8] + 2.6, (30.1, -1.6, 0.5), (32.4, 0.0, -0.85), 26),         # the peat cut: the slab lifts, two bronze helmets
    key(B[9] - 0.05, (30.5, -1.35, 0.32), (32.4, 0.0, -0.85), 28),
    key(TOTAL, (31.1, -0.95, -0.02), (32.4, 0.0, -0.85), 32),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])
def camera(t): return interp(CK, t)

def flash(t):
    f_ = 0.0
    for t0, d_, a_ in ((0.42, 0.05, 0.8), (0.55, 0.06, 0.5), (2.85, 0.08, 1.0), (3.02, 0.05, 0.6)):
        if t0 <= t < t0 + d_: f_ = max(f_, a_ * (1 - (t - t0) / d_) ** 0.5)
    return f_

SHIP_C = Vector((0.2, SHIP_Y, 0.6))
def ship_pose(t):
    hit = 4.0 * math.exp(-max(0.0, t - 0.05) * 2.2) * math.sin(max(0.0, t - 0.05) * 5.0) if t > 0.05 else 0.0
    eu = Euler((R(2.2 * math.sin(1.25 * t + 0.3) + hit), R(1.3 * math.sin(0.85 * t + 1.0)), 0)); m3 = eu.to_matrix()
    return SHIP_C + Vector((0, 0, 0.03 * math.sin(1.1 * t))) - m3 @ SHIP_C, eu

def slab_pose(t):
    u = smooth(B[8] + 2.5, B[8] + 3.7, t)
    p0 = Vector((CXc, 0, CUT_Z + 0.62)); p1 = Vector((CXc + 0.1, 2.15, BZ + 0.17))
    lift = 0.55 * math.sin(math.pi * min(1.0, u * 1.15))
    p_ = p0.lerp(p1, sm(clamp((u - 0.25) / 0.75, 0, 1))) + Vector((0, 0, lift))
    return p_, Euler((R(-20) * math.sin(math.pi * u) + R(6) * u, R(4) * u, R(5) * u))

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- the storm on the ship: sea, rocking, sail, spray, rain, lightning, lantern
    xy = SEA_XY; z_ = WATER_Z + sea_h(xy[:, 0], xy[:, 1], t)
    co_ = np.column_stack([xy, z_]).astype(np.float32).ravel(); SEA.data.vertices.foreach_set('co', co_); SEA.data.update()
    loc_, eu_ = ship_pose(t); SHIP.location = loc_; SHIP.rotation_euler = eu_
    sv = SAIL_V0.copy(); ni, nj = SAIL_N[0] + 1, SAIL_N[1] + 1
    ii = np.tile(np.arange(ni), nj) / (ni - 1); jj = np.repeat(np.arange(nj), ni) / (nj - 1)
    sv[:, 0] -= (0.28 + 0.04 * math.sin(t * 2.7)) * np.sin(np.pi * ii) * np.sin(np.pi * (0.15 + 0.85 * jj)) * (1 + 0.08 * np.sin(t * 5 + jj * 6))
    SAIL.data.vertices.foreach_set('co', sv.astype(np.float32).ravel()); SAIL.data.update()
    rattle = 0.012 * math.exp(-max(0.0, t - 0.08) * 6) * math.sin(t * 60) if t > 0.08 else 0.0
    HELM1.location = CHEST_P + Vector((0.0, rattle * 0.5, 0.42 + abs(rattle))); HELM1.rotation_euler = (rattle * 2, -rattle * 3, R(18))
    M_ = Matrix.Translation(loc_) @ eu_.to_matrix().to_4x4()
    for o, p0, v, t0, kind in SPRAY:
        tau = t - t0
        if tau < 0 or tau > 1.3 or t > B[1] + 0.5: o.location = (0, 0, -50); continue
        p_ = M_ @ p0 + v * tau + Vector((0, 0, -4.9 * tau * tau)) * (0.6 if kind else 1.0)
        if p_.z < DECK_Z + 0.02 and abs(p_.y - SHIP_Y) < 0.9: o.location = (0, 0, -50); continue
        if p_.z < WATER_Z: o.location = (0, 0, -50); continue
        o.location = p_
        if not kind:
            vel = v + Vector((0, 0, -9.8 * tau)); o.rotation_quaternion = vel.to_track_quat('Z', 'Y'); o.scale = (1, 1, 1 + vel.length * 1.6)
        if kind: o['a'] = 0.22 * math.exp(-tau * 2.5) * min(1.0, tau * 8); o.scale = (1 + 2.0 * tau,) * 3
    rf = 1 - smooth(B[1] + 0.1, B[1] + 0.8, t)
    for o, p0, ph, sp in RAIN:
        if rf <= 0.001: o.location = (0, 0, -50); continue
        z = 4.2 - ((t * sp + ph * 1.3) % 4.0); o.location = (p0.x + 0.35 * (4.2 - z) * 0.14, p0.y - 0.3 * (4.2 - z) * 0.1, z); o['a'] = rf
    fl = flash(t); BOLT.data.energy = 1800 * fl; CYC['flash'] = fl; CYT['flash'] = fl
    LLIGHT.data.energy = 30 * (1 + 0.25 * wob(t, 8, 3)); STORM_KEY.data.energy = 160 + 800 * fl
    # ---- the museum lights come up as the diorama is revealed
    ml = smooth(B[1] + 0.1, B[1] + 0.9, t)
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * ml; lt.hide_render = ml < 0.002
    STORM_FILL.data.energy = 25 * (1 - 0.5 * ml)
    # ---- the shovel digs three times, throwing clods
    for c_ in range(3):
        s0 = B[2] + 0.25 + 1.25 * c_
        for k in range(8):
            o = CLODS[c_ * 8 + k]; tr = s0 + 0.72 + 0.02 * k; tau = t - tr
            if tau < 0: o.location = (0, 0, -50); continue
            p0 = SHOVEL_P + Vector((-0.05, 0.0, 0.55)) + Vector((0.03 * (k % 3), 0.02 * (k % 2), 0)); v = CLOD_V[c_ * 8 + k]
            T_ = (v.z + math.sqrt(v.z * v.z + 2 * 9.8 * (p0.z - PLAT_Z - 0.03))) / 9.8; tt = min(tau, T_)
            o.location = p0 + v * tt + Vector((0, 0, -4.9 * tt * tt))
    sd = 0.0; tilt = R(12); lift = 0.0
    for c_ in range(3):
        s = (t - (B[2] + 0.25 + 1.25 * c_)) / 1.0
        if 0 <= s <= 1.0:
            sd = 0.14 * smooth(0.0, 0.25, s) * (1 - smooth(0.4, 0.6, s)); lift = 0.42 * smooth(0.4, 0.72, s) * (1 - smooth(0.8, 1.0, s))
            tilt = R(12) + R(38) * smooth(0.3, 0.5, s) * (1 - smooth(0.62, 0.78, s)) - R(30) * smooth(0.62, 0.74, s) * (1 - smooth(0.8, 1.0, s))
    SHOVEL.location = SHOVEL_P + Vector((0.12 * lift, 0, -sd + lift)); SHOVEL.rotation_euler = (0, tilt, 0)
    # ---- the nine pieces fly from the grave up onto the stand
    for nm, (off, eu, ts, du) in GJ_FROM.items():
        o = GJP[nm]; l0, r0 = GJ_REST[nm]; u = smooth(B[3] + ts, B[3] + ts + du, t)
        lift_ = 0.35 * math.sin(math.pi * u)
        o.location = l0 + off * (1 - u) + Vector((0, 0, lift_)); o.rotation_euler = (r0.x + eu.x * (1 - u), r0.y + eu.y * (1 - u), r0.z + eu.z * (1 - u))
    # ---- the sword swings down, hooks the horn, the helmet flies off and lands
    s = clamp((t - (TI - 0.4)) / 0.4, 0, 1); ft = clamp((t - TI) / 0.3, 0, 1)
    th = R(200) - R(160) * s * s - R(25) * (1 - (1 - ft) ** 2) + R(6) * math.sin(clamp(t - TI - 0.3, 0, 1) * 14) * math.exp(-max(0.0, t - TI - 0.3) * 5) * (ft >= 1)
    SWORD.rotation_euler = (0, th, 0)
    hp_, hq_ = helm2_pose(t); HELM2.location = hp_; HELM2.rotation_quaternion = hq_
    # ---- the opera: curtains draw apart, then the spotlights snap on
    uc = smooth(B[5] + 0.25, B[5] + 1.35, t)
    for c_ in CURT: c_.scale = (1 - 0.8 * uc, 1, 1)
    for k, (lt, cone_) in enumerate(OSPOTS):
        on = smooth(B[6] + 1.7 + 0.18 * k, B[6] + 1.78 + 0.18 * k, t); lt.data.energy = 900 * on; cone_['a'] = 0.12 * on; lt.hide_render = on < 0.001
        cone_.hide_render = on < 0.001
    # ---- the shelf fills, one helmet after another
    for k, h_ in enumerate(SHELF):
        u = clamp((t - (B[7] + 0.2 + 0.16 * k)) / 0.28, 0, 1); sc = 0.8 * (u * u * (3 - 2 * u) + 0.25 * math.sin(math.pi * u)) if u > 0 else 0.0
        h_.scale = (max(sc, 0.0001),) * 3; h_.hide_render = u <= 0.0
    # ---- outside: the slab of peat lifts, drips fall, the grass sways; the sky lights the room as we go out
    sp_, se_ = slab_pose(t); SLAB.location = sp_; SLAB.rotation_euler = se_
    for k, o in enumerate(DRIPS):
        tr = B[8] + 2.65 + 0.04 * k
        if t < tr or t > tr + 1.2: o.location = (0, 0, -50); continue
        ps_, pe_ = slab_pose(tr); p0 = Matrix.Translation(ps_) @ pe_.to_matrix().to_4x4() @ DRIP_P[k]; tau = t - tr
        p_ = p0 + Vector((0, 0, -4.9 * tau * tau))
        o.location = p_ if p_.z > CUT_Z + 0.02 else (0, 0, -50)
    for o, p0, ph in COTTON: o.location = p0 + Vector((0.02 * math.sin(t * 1.7 + ph), 0.015 * math.cos(t * 1.3 + ph), 0))
    for k, o in enumerate(MIST): o.location.y = 0.3 * math.sin(t * 0.2 + k)
    out = smooth(B[8] + 0.4, B[8] + 1.6, t)
    WBG.inputs['Strength'].default_value = 0.01 + 0.35 * out; BOGFILL.data.energy = 120 * out
    # ---- camera, with a little life in it (a jolt when the wave hits)
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3) + (shake(t, 0.035, 4.0, 13.0) * math.exp(-max(0, t - 0.08) * 5.0) if t > 0.08 else Vector())
    look(cp, ct, lens, 5.6 if t < B[8] + 1.5 else 8.0)
    bpy.context.view_layer.update()
