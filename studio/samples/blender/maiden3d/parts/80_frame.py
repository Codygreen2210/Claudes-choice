
# ================================================================ animation and the one continuous camera move
T_SLAM = 0.45
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
    key(0.0, (0.95, 0.05, 1.15), (-0.05, 1.8, 1.15), 22),              # close on the doors as they swing shut
    key(T_SLAM + 0.15, (0.85, -0.05, 1.18), (-0.02, 1.8, 1.15), 22),
    key(2.6, (0.25, -0.35, 1.45), (0.0, 2.0, 1.25), 24),                 # ease back: the whole maiden, torches, chains
    key(B[1] - 0.05, (0.2, -0.55, 1.5), (0.0, 2.0, 1.25), 24),
    key(B[1] + 1.7, (0.9, -6.0, 2.1), (0.25, 1.5, 1.6), 24),             # pull way back: it's a museum diorama
    key(B[2] - 0.05, (1.0, -6.15, 2.12), (0.3, 1.5, 1.6), 24),
    key(B[2] + 1.35, (6.45, 1.55, 1.5), (6.92, 3.05, 0.82), 28),         # the writer's desk, 1793: quill, coins, the mould
    key(B[3] - 0.05, (6.5, 1.65, 1.48), (6.92, 3.05, 0.82), 28),
    key(B[3] + 1.0, (7.5, 0.3, 2.6), (7.5, 5.2, 2.85), 20),              # up to the timeline: 1515 .. 1793
    key(B[4] - 0.05, (7.5, 0.2, 2.6), (7.5, 5.2, 2.85), 20),
    key(B[4] + 1.0, (12.3, -0.9, 1.75), (13.25, 2.9, 1.2), 22),          # the workshop: the parts come together
    key(B[5] - 0.05, (12.45, -0.75, 1.72), (13.15, 2.9, 1.2), 22),
    key(B[5] + 1.0, (18.3, -1.2, 1.85), (19.0, 2.7, 1.55), 24),          # the crate for Chicago, 1893
    key(B[6] - 0.05, (18.4, -1.1, 1.82), (19.0, 2.7, 1.55), 24),
    key(B[6] + 0.85, (19.0, 1.25, 1.32), (19.0, 2.95, 1.05), 22),        # look inside: empty
    key(B[7] - 0.05, (19.0, 1.35, 1.3), (19.0, 2.95, 1.05), 22),
    key(B[7] + 0.7, (19.9, -0.3, 1.9), (24.0, 0.0, 2.3), 22),            # back out and turn to the window ...
    key(B[7] + 1.55, (24.1, 0.0, 2.45), (30.0, 0.0, 1.0), 22),           # ... and out into the sun
    key(B[7] + 2.6, (28.3, -3.0, 2.3), (32.2, 0.1, 0.45), 26),           # Baghdad: the leaf pile, the iron face
    key(B[8] - 0.05, (28.5, -2.9, 2.25), (32.2, 0.1, 0.45), 26),
    key(TOTAL, (31.0, -1.7, 2.1), (31.35, 0.0, 0.5), 28),
]
for a_, b_ in zip(CK, CK[1:]): assert b_[0] > a_[0], ('camera keys out of order', a_[0], b_[0])

def camera(t): return interp(CK, t)

def door_angle(t):
    if t < T_SLAM: u = t / T_SLAM; return 105.0 * (1 - u ** 2.2)
    d = t - T_SLAM; return 3.5 * math.exp(-d * 9.0) * abs(math.sin(d * 28.0))

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---- maiden 1: the slam
    a1 = door_angle(t)
    for d, s_ in zip(M1['doors'], (-1, 1)): d.rotation_euler = (0, 0, s_ * R(a1))
    for o, p0, v, s_ in DUST:
        tau = t - T_SLAM - 0.01
        if tau < 0 or tau > 2.4: o.location = (0, 0, -50); o['a'] = 0.0; continue
        dsp = (1 - math.exp(-tau * 3.0)) / 3.0
        o.location = p0 + v * dsp + Vector((0, 0, -0.06 * tau)); o['a'] = 0.3 * s_ * math.exp(-tau * 1.6) * min(1, tau * 30); o.scale = (0.6 + 0.8 * tau,) * 3
    # torches, embers, candle
    for k, (fl, lt) in enumerate(TORCH):
        w_ = wob(t, 6.0, k * 3.1); fl.scale = (1 + 0.12 * w_, 1 + 0.12 * wob(t, 7.0, k + 9), 1 + 0.22 * wob(t, 9.0, k + 4)); lt.data.energy = 260 * (1 + 0.25 * w_)
    for o, side, ph, sp, dx, dy in EMB:
        fl, _ = TORCH[side]; p0 = fl.matrix_world.translation; u = ((t * sp + ph) % 1.2)
        o.location = p0 + Vector((dx + 0.05 * math.sin(t * 3 + ph * 5), dy, 0.25 + u * 0.9)); o['a'] = max(0.0, 1 - u / 1.2) * (0.6 + 0.4 * math.sin(t * 20 + ph * 9))
    BRAZF.scale = (1 + 0.1 * wob(t, 6, 11), 1 + 0.1 * wob(t, 6, 12), 1 + 0.25 * wob(t, 9, 13)); BRAZL.data.energy = 120 * (1 + 0.25 * wob(t, 7, 11))
    CFLAME.scale = (1 + 0.1 * wob(t, 8, 2), 1 + 0.1 * wob(t, 8, 5), 1 + 0.18 * wob(t, 10, 7)); CLIGHT.data.energy = 25 * (1 + 0.2 * wob(t, 8, 2))
    # ---- the museum lights come up as the diorama is revealed
    ml = smooth(B[1] + 0.1, B[1] + 0.9, t)
    for lt, e in MUSEUM_LIGHTS: lt.data.energy = e * ml; lt.hide_render = ml < 0.002
    FILL.data.energy = 45 * (1 - 0.6 * ml); MOON.data.energy = 90 * (1 - 0.7 * ml)
    WBG.inputs['Strength'].default_value = 0.012 + 0.10 * smooth(B[6], B[7] + 1.0, t)
    # ---- the desk: the quill writes, a coin spins
    w0 = B[2] + 0.5; per = 0.62
    for k, o in enumerate(INKLINES):
        u = clamp((t - w0 - k * per) / per, 0, 1); o.scale = (max(u, 0.001), 1, 1); o.location.x = 0.03 + 0.08 * u; o.hide_render = u <= 0.0
    kq = int(clamp((t - w0) // per, 0, len(INKLINES) - 1)); uq = clamp((t - w0 - kq * per) / per, 0, 1)
    if t < w0: kq, uq = 0, 0.0
    tip = BOOK.matrix_world @ Vector((0.03 + 0.16 * uq, 0.10 - kq * 0.032, 0.04 + 0.004 * abs(math.sin(t * 22))))
    QUILL.location = tip; QUILL.rotation_euler = (R(-28), R(22) + 0.08 * math.sin(t * 22), R(-30))
    cn = COINS[-1]; sp_ = smooth(B[2] + 0.2, B[2] + 0.5, t) * (1 - smooth(B[3] + 1.0, B[3] + 2.0, t))
    cn.location = (6.62, 2.86, 0.81 + 0.02 * sp_); cn.rotation_euler = (R(80) * sp_ * (0.6 + 0.4 * math.cos(t * 3)), 0, t * 14 * sp_)
    # ---- the timeline: 1515 -> 1793 fills in
    u = smooth(B[3] + 0.4, B[3] + 2.3, t); TLFILL.scale = (max(2.8 * u, 0.001), 1, 1); TLFILL.location.x = 6.1 + 1.4 * u; TLFILL.hide_render = u <= 0.001
    # ---- the shop maiden comes together from old parts
    for nm, (off, eu, ts, du) in M2_FROM.items():
        o = M2[nm]; l0, r0 = M2_REST[nm]; u = smooth(B[4] + ts, B[4] + ts + du, t)
        lift = 0.45 * math.sin(math.pi * u) if du > 0.05 else 0.0
        o.location = l0 + off * (1 - u) + Vector((0, 0, lift)); o.rotation_euler = (r0.x + eu.x * (1 - u), r0.y + eu.y * (1 - u), r0.z + eu.z * (1 - u))
    for d, s_ in zip(M2['doors'], (-1, 1)):
        nm = 'door' + ('L' if s_ < 0 else 'R'); off, eu, ts, du = M2_FROM[nm]; u = smooth(B[4] + ts, B[4] + ts + du, t)
        sh = smooth(B[4] + 3.65 * S4, B[4] + 3.95 * S4, t)                       # last: both doors swing shut
        d.rotation_euler = (0, 0, M2_REST[nm][1].z + eu.z * (1 - u) + s_ * R(80) * (1 - sh))
    # ---- the crate: bunting sways; inside the copy a warm light during the look in
    for fo, k in FLAGS: fo.rotation_euler = (0.18 * math.sin(t * 2.2 + k * 0.7), 0, 0.08 * math.sin(t * 1.7 + k))
    M3IN.data.energy = 60.0 * smooth(B[6] - 0.3, B[6] + 0.6, t) * (1 - smooth(B[7] + 0.6, B[7] + 1.2, t))
    # ---- outside: wind in the leaves, the tape measure
    for o, p0, sp, ph in LOOSE:
        tau = max(0.0, t - B[7]); dx = sp * tau * 0.6 + 0.05 * math.sin(t * 3 + ph)
        o.location = p0 + Vector((dx, 0.25 * math.sin(tau * 1.3 + ph), 0.02 + 0.05 * abs(math.sin(tau * 4 + ph)))); o.rotation_euler = (0.3 * math.sin(tau * 5 + ph), 0.2 * math.cos(tau * 4 + ph), ph + tau * 2.0 * sp)
    for o, l0, r0, k in LEAVES[:60]:
        o.rotation_euler = (r0.x + 0.12 * math.sin(t * 3.0 + k), r0.y + 0.1 * math.cos(t * 2.6 + k * 1.3), r0.z)
    ut = smooth(B[7] + 3.0, B[7] + 4.2, t) * (1 - smooth(B[8] - 0.1, B[8] + 0.3, t)); L_ = 2.05
    x0 = M4['root'].location.x; TAPE.location = (x0 - L_ * ut / 2, -0.62, 0.012); TAPE.scale = (max(L_ * ut, 0.001), 1, 1); TAPE.hide_render = ut < 0.002
    for k, o in enumerate(TAPE_ENDS): o.location = (x0 - (L_ * ut if k else 0.0), -0.62, 0.04); o.hide_render = ut < 0.002
    # ---- camera, with a little life in it
    cp, ct, lens = camera(t)
    cp = cp + shake(t, 0.006, 1.0, 1.3) + (shake(t, 0.03, 4.0, 14.0) * math.exp(-max(0, t - T_SLAM) * 6.0) if t > T_SLAM else Vector())
    look(cp, ct, lens, 5.6 if t < B[7] + 1.0 else 8.0)
    bpy.context.view_layer.update()
