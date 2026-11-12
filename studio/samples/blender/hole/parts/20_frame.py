
# ================================================================ motion
END = TOTAL
def lerpv(a_, b_, k): return Vector(a_).lerp(Vector(b_), k)
def shake(t, amt, seed=0.0): return Vector((wob(t, 19.0, seed), wob(t, 19.0, seed + 3.3), wob(t, 19.0, seed + 6.1))) * amt
# story clock (minutes into the trip) and speed, shown on screen and used for the cutaway dot
T_CEN = B[4]; T_OUT = B[6] + 0.6
def story_min(t):
    if t < B[2]: return 0.0
    if t < T_CEN: return 19.0 * (t - B[2]) / (T_CEN - B[2])
    if t < B[5]: return 19.0
    return min(TRIP_MIN, 19.0 + 19.0 * (t - B[5]) / (T_OUT - B[5]))
def mph(m_): return VMAX_MPH * math.sin(math.pi * min(m_, TRIP_MIN) / TRIP_MIN)

# ---- day hole: one parabola, apex ZA at t = -TA (frame one) and again at END - TA (the loop)
ZA = 2.4; TA = 0.42
def ball_day(t, at_end=False):
    tau = (t - END + TA) if at_end else (t + TA)
    z = ZA - 0.5 * G * tau * tau; BALL.location = DS + Vector((0, 0, z)); BALL.rotation_euler = (2.2 * tau, 0.6, 0.0); return BALL.location.copy(), -G * tau
CAM0 = DS + Vector((4.4, -6.6, 3.3)); TGT0 = DS + Vector((0, 0, 0.6)); LENS0 = 28.0
def cam_shaft_follow(zb, above=4.6):
    return DS + Vector((0.0, -0.45, zb + above))

# ---- night hole: the same throw, slowed down at the top (beat 7)
ZN = 3.0
def warp(t):
    if t < B[7]: return t
    if t < B[8]: return B[7] + 0.3 * (t - B[7])
    return B[7] + 0.3 * DUR[7] + (t - B[8])
T_AP = B[7] + 0.5 * DUR[7]
def ball_night(t):
    tau = warp(t) - warp(T_AP); z = ZN - 0.5 * G * tau * tau
    BALL.location = NS + Vector((0, 0, z)); BALL.rotation_euler = (2.2 * tau, 0.6, 0.0); return BALL.location.copy()

# ---- tunnel: the walls stream up past a still ball; visual speed follows the real speed curve
VVIS = 420.0                                                       # wall speed (m/s on screen) at the middle of the Earth
def wall_off(t):
    """integral of the on-screen wall speed: beats 2-4 (speeding up to the middle, then the center beat at top speed)"""
    m_ = story_min(t); T1 = T_CEN - B[2]
    if t < B[2]: return 0.0
    if t < T_CEN: return VVIS * T1 / 19.0 * TRIP_MIN / math.pi * (1 - math.cos(math.pi * m_ / TRIP_MIN))
    return VVIS * T1 / 19.0 * TRIP_MIN / math.pi + VVIS * (t - T_CEN)
def tunnel_depth(t):
    if t < B[3]: return 0.0
    if t < B[4]:
        u = (t - B[3]) / DUR[3]                                    # rock, then mantle, then core, on the words
        return 0.45 * smooth(0.25, 0.42, u) + 0.55 * smooth(0.55, 0.78, u)
    return 1.0

def state(t):
    t = clamp(t, 0.0, END - 1e-4); b = beat_at(t)
    BALL.hide_render = False; MELT.hide_render = True
    for c_ in CUTS: c_['boost'] = 0.0
    TUN_IN.scale = (1, 1, 1); TUN_IN['heat'] = 0.0
    for o in SPARKS: o.hide_render = b not in (2, 3, 4)
    if b == 0:                                                       # the drop: the ball falls into the hole, the camera dives in after it
        p, v = ball_day(t)
        k1 = smooth(0.2, 0.9, t); k2 = smooth(0.35, 1.4, t)
        f_ = cam_shaft_follow(p.z)
        cp = Vector((lerp(CAM0.x, f_.x, k1), lerp(CAM0.y, f_.y, k1), lerp(CAM0.z, f_.z, k2)))
        up = lerpv((0, 0, 1), (0, 1, 0), smooth(0.4, 1.0, t)).normalized()
        look(cp, lerpv(TGT0, p, k1), lens=lerp(LENS0, 30.0, k2), fstop=lerp(11.0, 5.6, k2), focus=p, up=up)
    elif b == 1:                                                     # the cutaway: the whole trip, 7,918 miles
        u = (t - B[1]) / DUR[1]; earth_dot(0.0); BALL.location = DS + Vector((0, 0, -2000))
        ang = R(-45 + 10 * u); d_ = lerp(37.0, 31.0, sm(u))
        cp = CS + Vector((math.cos(ang) * d_, math.sin(ang) * d_, d_ * 0.16))
        look(cp, CS + Vector((0, 0, -0.4)), lens=30, fstop=16.0, up=(0, 0, 1))
    elif b in (2, 3, 4):                                             # inside: the walls stream past
        d_ = tunnel_depth(t); off = wall_off(t); tube_set(off, d_)
        BALL.location = TS + shake(t, 0.03, 1.0); BALL.rotation_euler = (7.0 * t, 0.9 * t, 0.3)
        sh = shake(t, 0.025 + 0.035 * d_, 4.0)
        if b == 2:
            u = (t - B[2]) / DUR[2]
            look(TS + Vector((0.32, -0.7, lerp(3.6, 2.6, sm(u)))) + sh, TS, lens=22, fstop=5.6, focus=BALL.location, up=(0, 1, 0))
        elif b == 3:
            u = (t - B[3]) / DUR[3]; ang = R(-60 + 70 * u)
            cp = TS + Vector((math.cos(ang) * 1.05, math.sin(ang) * 1.05, lerp(1.6, 0.9, u))) + sh
            look(cp, TS + Vector((0, 0, -0.5)), lens=16, fstop=4.0, focus=BALL.location, up=(0, 0, 1))
        else:
            u = (t - B[4]) / DUR[4]; ang = R(10 + 25 * u)
            cp = TS + Vector((math.cos(ang) * 1.25, math.sin(ang) * 1.25, -1.6)) + sh          # from below: the ball coming at you, embers streaking past
            look(cp, TS + Vector((0, 0, 0.6)), lens=lerp(16, 19, u), fstop=4.0, focus=BALL.location, up=(0, 0, 1))
    elif b == 5:                                                     # the cutaway again: past the middle, slowing down
        u = (t - B[5]) / DUR[5]; earth_dot(story_min(t)); BALL.location = DS + Vector((0, 0, -2000))
        ang = R(-40 + 14 * u); d_ = lerp(30.0, 27.0, u)
        cp = CS + Vector((math.cos(ang) * d_, math.sin(ang) * d_, d_ * lerp(0.1, -0.12, u)))
        look(cp, CS + Vector((0, 0, lerp(-1.0, -3.5, u))), lens=30, fstop=16.0, up=(0, 0, 1))
    elif b == 6:                                                     # the far side, night: rising up the shaft, out into the stars
        p = ball_night(t)
        zc = min(p.z + 4.2, 1.1); k1 = smooth(B[7] - 0.75, B[7] + 0.25, t)
        f_ = NS + Vector((0.55, -0.85, zc)); end_ = NS + Vector((2.3, -3.3, 0.9))
        cp = lerpv(f_, end_, k1); up = lerpv((0, 1, 0), (0, 0, 1), k1).normalized()
        look(cp, p, lens=lerp(28, 30, k1), fstop=lerp(5.6, 8.0, k1), focus=p, up=up)
    elif b == 7:                                                     # it stops at the top (slow motion)
        p = ball_night(t); u = (t - B[7]) / DUR[7]
        cp = NS + Vector((lerp(2.3, 1.7, sm(u)), lerp(-3.3, -2.7, sm(u)), lerp(0.9, 2.2, sm(u))))
        look(cp, p, lens=lerp(30, 38, sm(u)), fstop=8.0, focus=p, up=(0, 0, 1))
    elif b == 8:                                                     # and falls all the way back
        p = ball_night(t); u = (t - B[8]) / DUR[8]; k = sm(u)
        cp = NS + Vector((lerp(1.7, 0.35, k), lerp(-2.7, -0.9, k), lerp(2.2, 5.0, k)))
        look(cp, p, lens=lerp(38, 30, k), fstop=8.0, focus=p, up=lerpv((0, 0, 1), (0, 1, 0), k).normalized())
    elif b == 9:                                                     # the core is as hot as the Sun: the middle of the hole melts shut
        u = (t - B[9]) / DUR[9]; BALL.location = DS + Vector((0, 0, -2000)); DOT.hide_render = True; TRAIL.hide_render = True
        mk = smooth(0.45, 0.85, u); TUN_IN.scale = (max(1 - mk, 0.02), max(1 - mk, 0.02), 1); TUN_IN['heat'] = smooth(0.1, 0.45, u) * (1 - 0.7 * mk)
        for c_ in CUTS: c_['boost'] = 0.3 * smooth(0.15, 0.6, u)
        ang = R(-40 - 8 * u); d_ = lerp(33.0, 26.0, sm(u))
        cp = CS + Vector((math.cos(ang) * d_, math.sin(ang) * d_, d_ * 0.12))
        look(cp, CS + Vector((0, 0, 0)), lens=lerp(30, 32, u), fstop=16.0, up=(0, 0, 1))
    else:                                                            # back home: up out of the first hole and into frame one (the loop)
        p, v = ball_day(t, at_end=True)
        k1 = smooth(END - 1.55, END - 0.12, t)
        f_ = cam_shaft_follow(p.z, 4.2); f_.z = min(f_.z, 1.0)
        cp = lerpv(f_, CAM0, k1); up = lerpv((0, 1, 0), (0, 0, 1), smooth(END - 1.55, END - 0.7, t)).normalized()
        look(cp, lerpv(p, TGT0, k1), lens=lerp(30.0, LENS0, k1), fstop=lerp(5.6, 11.0, k1), focus=p, up=up)
    if b not in (9,):
        DOT.hide_render = b not in (1, 5)
        if b not in (1, 5): TRAIL.hide_render = True

bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
ANIM = [CAM, BALL, DOT, TRAIL]
def frame(f):
    t = f / FPS; d = 0.25 / FPS
    for o in ANIM + [TUBE, TRINGS] + SPARKS: o.animation_data_clear()
    if beat_at(max(0.0, t - d)) == beat_at(min(END - 1e-4, t + d)) == beat_at(t):
        base = 0.0
        if beat_at(t) in (2, 3, 4): base = math.floor(wall_off(t) / RING_P) * RING_P; sb = spark_bases(0.15 * wall_off(t))   # wrap by whole steps, same for both keys
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            state(tt_)
            if beat_at(t) in (2, 3, 4): tube_set(wall_off(tt_) - base - 200.0, tunnel_depth(tt_)); sparks_set(0.15 * wall_off(tt_), tunnel_depth(tt_), sb)
            for o in ANIM + ([TUBE, TRINGS] + SPARKS if beat_at(t) in (2, 3, 4) else []):
                o.keyframe_insert('location', frame=kf)
                o.keyframe_insert('rotation_quaternion' if o.rotation_mode == 'QUATERNION' else 'rotation_euler', frame=kf)
                if o is TRAIL: o.keyframe_insert('scale', frame=kf)
    S.frame_set(f); state(t)
    if beat_at(t) in (2, 3, 4):
        base = math.floor(wall_off(t) / RING_P) * RING_P; tube_set(wall_off(t) - base - 200.0, tunnel_depth(t)); sparks_set(0.15 * wall_off(t), tunnel_depth(t))
