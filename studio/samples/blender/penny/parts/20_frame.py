
# ================================================================ motion
END = TOTAL
Y_EDGE = FRONT - 0.003                          # the penny's centre just past the edge: it tips
P0 = V3(0.0, Y_EDGE, TOPS + PT)
def penny_drop(tau):
    """the penny that slides off the roof edge and falls with drag. tau = seconds since it left the edge (negative: still sliding)"""
    if tau < 0:
        s = clamp(-tau / 0.8, 0, 1)
        p = V3(0.0, Y_EDGE + 0.33 * s ** 1.6, TOPS + PT)
        tip = R(14) * smooth(-0.12, 0.0, tau)
        return p, Euler((-tip, 0, 0.6 + 2.0 * tau))
    d = fall_d(tau, VT_P)
    p = V3(0.5 * math.sin(0.8 * tau) + 0.12 * math.sin(2.7 * tau + 1.0) - 0.12, Y_EDGE - 2.2 * (1 - math.exp(-tau / 1.5)), TOPS + PT - d)
    ramp = smooth(0.0, 0.7, tau)
    return p, Euler((-R(14) - 8.5 * tau * ramp, 0.5 * math.sin(1.9 * tau) * ramp, 0.6 + 1.2 * tau))
def cam0(t):
    """beat 0: from the roof edge, then riding down with the penny (also where the loop ends)"""
    pen, _ = penny_drop(t - 0.25)
    base = V3(0.13, FRONT + 0.2, TOPS + 0.13); follow = pen + V3(0.09, -0.12, 0.14)      # out over the edge first, then down with it
    k = smooth(0.2, 0.75, t)
    return base.lerp(follow, k), pen + V3(0.0, -0.02, -0.03)
# the coin settling on the sidewalk like a spun coin: the tilt dies away while the wobble speeds up
LAND = V3(0.35, -27.55, SW_Z)
_WT = [0.0]; _PHI = [0.0]; _ph = 0.0
for i in range(1, 6 * 600):
    tau = i / 600; tilt = 0.42 * math.exp(-tau / 0.85)
    if tilt > 0.006: _ph += 2.0 / math.sqrt(tilt) / 600
    _WT.append(tau); _PHI.append(_ph)
def wobble(tau):
    tau = max(tau, 0.0); tilt = 0.42 * math.exp(-tau / 0.85); phi = float(np.interp(tau, _WT, _PHI))
    if tilt <= 0.006: tilt = 0.0
    M_ = Matrix.Rotation(phi, 3, 'Z') @ Matrix.Rotation(tilt, 3, 'X') @ Matrix.Rotation(-phi * 0.15, 3, 'Z')
    return LAND + V3(0, 0, PR * math.sin(tilt) + PT * math.cos(tilt)), M_.to_euler('XYZ')
T_LAND = B[6] + 1.55
def penny_land(t):
    """beat 6-7: the last 17 m down, a hop on the concrete, then the wobble"""
    if t < T_LAND:
        k = (T_LAND - t) / 1.55
        p = LAND + V3(0.45 * math.sin(3.1 * t) * k, -0.5 * k * math.sin(1.7 * t + 0.4), PT + 11.2 * (T_LAND - t))
        return p, Euler((-8.5 * t, 0.5 * math.sin(1.9 * t), 1.2 * t))
    tb = t - T_LAND
    if tb < 0.2:
        h = 0.028 * abs(math.sin(math.pi * tb / 0.13)) if tb < 0.13 else 0.006 * abs(math.sin(math.pi * (tb - 0.13) / 0.07))
        p, e = wobble(0.0); return p + V3(0, 0, h), Euler((e.x + (0.2 - tb) * 6.0, e.y, e.z))
    return wobble(tb - 0.2)
# the bowling ball: rolls slowly off the edge (0.3 m/s), falls with drag (lands ~2.9 m out, ~151 mph, ~9.6 s)
BX = IMP.x; ROLL_V = 0.3; BY0 = FRONT + 0.45; T_EDGE = (BY0 - FRONT) / ROLL_V
def ball_at(tau):
    """tau = seconds since it started rolling"""
    if tau < T_EDGE:
        y = BY0 - ROLL_V * tau; return V3(BX, y, TOPS + BALL_R), Euler((-(BY0 - y) / BALL_R, 0, 0))
    tf = tau - T_EDGE
    return V3(BX, FRONT - ROLL_V * tf, TOPS + BALL_R - fall_d(tf, VT_B)), Euler((-(BY0 - FRONT + ROLL_V * tf) / BALL_R, 0, 0.3 * tf))
T_HIT = B[11] + 0.12
SLOW = 0.22
def impact(ti):
    """ti: real seconds after the hit (negative: before)"""
    on = ti >= 0
    for o in IMPACT: o.hide_render = not on
    if not on: return
    CRATER.scale = (1, 1, 1) if ti > 0.012 else (ti / 0.012 + 0.05,) * 3
    for c in CRACKS: k = clamp(ti / 0.035, 0.02, 1.0); c.scale = (k, k, 0.25)
    for ch in CHUNKS:
        v = Vector(ch['v']); p0 = Vector(ch['p0']); tl = (v.z + math.sqrt(v.z * v.z + 2 * G * 0.01)) / G
        tt_ = min(ti, tl); p = IMP + p0 + v * tt_ + V3(0, 0, -0.5 * G * tt_ * tt_)
        if ti > tl: p = p + V3(v.x, v.y, 0) * 0.15 * (1 - math.exp(-(ti - tl) * 6)); p.z = SW_Z + ch.scale.z * 0.5
        ch.location = p; sp = Vector(ch['spin']) * min(ti, tl + 0.05); ch.rotation_euler = (sp.x, sp.y, sp.z)
    for d_ in DUST:
        s_ = 0.08 + 0.9 * ti ** 0.5; dr = Vector(d_['dir'])
        d_.location = IMP + dr * (s_ * 0.9) + V3(0, 0, 0.05); d_.scale = (s_, s_, s_ * 0.7); d_['dens'] = 3.0 * math.exp(-ti / 0.9) * smooth(0.0, 0.02, ti)
def ring_at(p, cp, size):
    RING.hide_render = False; RING.location = p; RING.rotation_mode = 'QUATERNION'
    RING.rotation_quaternion = (Vector(cp) - Vector(p)).to_track_quat('Z', 'Y'); r_ = (Vector(cp) - Vector(p)).length * size; RING.scale = (r_, r_, r_)

def state(t):
    t = clamp(t, 0.0, END - 1e-4); b = beat_at(t)
    for root in (PEN, GHOST, PEN_REST): pen_vis(root, False)
    BALL.hide_render = True; RING.hide_render = True; impact(-1)
    for w in (WIND, WINDB, WINDU): wind_on(w, False)
    def put(root, pe):
        p, e = pe; pen_vis(root, True); root.location = p; root.rotation_euler = e
    if b in (0, 1):
        put(PEN, penny_drop(t - 0.25)); cp, ct = cam0(t)
        if b == 0: look(cp, ct, lens=lerp(40, 26, smooth(0.3, 1.4, t)), fstop=11.0)
        else:
            u = (t - B[1]) / DUR[1]; cp = V3(-70, -330, 1.7).lerp(V3(-62, -315, 1.7), u)
            look(cp, V3(0, FRONT, 165), lens=20, fstop=16.0); ring_at(PEN.location, cp, 0.04)
    elif b == 2:                                    # no air: the ghost penny drops like a stone
        tau = (t - B[2]) * 2.75; gp = V3(0.6, FRONT - 1.4, TOPS - 0.5 * G * tau * tau)
        put(GHOST, (gp, Euler((R(78), 0.0, 0.25 * tau)))); look(gp + V3(0.07, -0.17, 0.03), gp + V3(-0.005, 0, -0.006), lens=45, fstop=2.8)
    elif b == 3:                                    # slow motion: the air shoves on the flat face, it flips and flutters
        tau = 5.0 + (t - B[3]) * 0.3; p, e = penny_drop(tau); put(PEN, (p, e))
        ang = 0.5 + (t - B[3]) * 0.3; look(p + V3(0.085 * math.sin(ang), -0.085 * math.cos(ang), 0.022), p, lens=55, fstop=9.0)
        WIND.location = p; wind_on(WIND, True, (t - B[3]) * 4.0, 0.85)
    elif b == 4:                                    # riding down with it: speeds up, then stops speeding up
        tau = (t - B[4]) * 0.82; p, e = penny_drop(tau); put(PEN, (p, e))
        look(p + V3(0.07, -0.13, 0.045), p + V3(0, 0.02, -0.01), lens=35, fstop=5.6, focus=p)
        WIND.location = p; wind_on(WIND, True, (t - B[4]) * 6.0, 0.35)
    elif b == 5:                                    # wind along the tower tosses it back up
        u = (t - B[5]) / DUR[5]
        p = V3(-0.5 + 2.2 * u, FRONT - 1.6 - 2.4 * u, 230.0 - 1.5 * u + 5.0 * smooth(0.15, 0.9, u))
        put(PEN, (p, Euler((-10.0 * (t - B[5]), 0.6 * math.sin(2.3 * t), 1.5 * t))))
        cp = p + V3(0.22, -0.42, 0.05); look(cp, p + V3(0, 0.15, 0.1), lens=32, fstop=5.6, focus=p); ring_at(p, cp, 0.03)
        WINDU.location = V3(0.6, FRONT - 2.4, 232.0); wind_on(WINDU, True, (t - B[5]) * 4.0, 0.55)
    elif b in (6, 7):                               # 35 seconds later it lands, a hop and a wobble
        put(PEN, penny_land(t))
        if b == 6:
            p = PEN.location.copy(); cp = p + V3(0.10, -0.24, 0.08); cp.z = max(cp.z, SW_Z + 0.07)
            look(cp, p + V3(0, 0.02, -0.03), lens=30, fstop=4.0, focus=p)
        else:
            u = (t - B[7]) / DUR[7]; cp = LAND + V3(0.075, -0.085, 0.032).lerp(V3(0.06, -0.07, 0.024), u)
            look(cp, LAND + V3(0, 0, 0.004), lens=50, fstop=2.8)
    else:                                           # the bowling ball
        put(PEN_REST, wobble(10.0)); BALL.hide_render = False
        if b == 8:
            BALL.location, BALL.rotation_euler = ball_at(t - B[8] + 0.05)
            look(V3(BX + 0.35, FRONT + 1.25, TOPS + 0.22), V3(BX - 0.1, FRONT - 1.2, TOPS - 0.9), lens=22, fstop=8.0, focus=BALL.location)
        elif b == 9:
            tau = (B[9] - B[8] + 0.05) + (t - B[9]) * 1.25; BALL.location, BALL.rotation_euler = ball_at(tau); p = BALL.location.copy()
            look(p + V3(0.55, -0.85, 0.3), p + V3(0, 0.2, -0.05), lens=28, fstop=8.0, focus=p)
            WINDB.location = p; wind_on(WINDB, True, (t - B[9]) * 8.0, 0.6)
        elif b == 10:
            BALL.location = IMP + V3(0, 0, BALL_R + 67.0 * (B[11] - t)); BALL.rotation_euler = (-3.0 * t, 0, 0.3 * t)
            cp = IMP + V3(-1.2, -1.5, 0.3); look(cp, IMP + V3(0.1, 0.25, 12.0), lens=18, fstop=8.0, focus=BALL.location); ring_at(BALL.location, cp, 0.03)
        else:
            ti = (t - T_HIT) * SLOW if b == 11 else (B[12] - T_HIT) * SLOW + (t - B[12])
            BALL.location = IMP + V3(0, 0, BALL_R + (67.0 * -ti if ti < 0 else -0.07 * min(1.0, ti / 0.01))); BALL.rotation_euler = (-3.0 * T_HIT - (ti < 0) * 3.0 * ti, 0, 0.3 * T_HIT)
            impact(ti)
            if b == 11:
                sh = shake(t, 0.012 * math.exp(-max(ti, 0) / 0.08) * (ti > 0), 2.0)
                look(IMP + V3(1.5, -1.25, 0.32) + sh, IMP + V3(0, 0.1, 0.2), lens=30, fstop=5.6, focus=IMP + V3(0, 0, 0.1))
            else:                                   # rise from the crater back up to the roof: the loop
                u = (t - B[12]) / DUR[12]; k = smooth(0.12, 0.93, u); c0, _ = cam0(0.0); pp, _ = penny_drop(t - END - 0.25); t0 = pp + V3(0.0, -0.02, -0.03)
                a_, b_, c_, d_ = IMP + V3(1.9, -3.2, 1.1), IMP + V3(4.0, -16.0, 30.0), c0 + V3(0.15, -0.5, 1.2), c0
                cp = a_ * (1 - k) ** 3 + b_ * 3 * k * (1 - k) ** 2 + c_ * 3 * k * k * (1 - k) + d_ * k ** 3
                tg = IMP.lerp(t0, smooth(0.1, 0.85, u)); look(cp, tg, lens=lerp(30, 40, k), fstop=lerp(8.0, 11.0, k))
                put(PEN, penny_drop(t - END - 0.25))
def shake(t, amt, seed=0.0): return Vector((wob(t, 23.0, seed), wob(t, 23.0, seed + 3.3), wob(t, 23.0, seed + 6.1))) * amt

bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
ANIM = [CAM, PEN, GHOST, BALL, RING, WIND, WINDB, WINDU] + CHUNKS
def frame(f):
    t = f / FPS; d = 0.25 / FPS
    for o in ANIM: o.animation_data_clear()
    if beat_at(max(0.0, t - d)) == beat_at(min(END - 1e-4, t + d)) == beat_at(t):
        anim = [o for o in ANIM if not (o is BALL and beat_at(t) == 10)]      # the far ball would blur away to nothing
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            state(tt_)
            for o in anim:
                o.keyframe_insert('location', frame=kf)
                o.keyframe_insert('rotation_quaternion' if o.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=kf)
    S.frame_set(f); state(t)
