
# ================================================================ timing, the turntable, the camera (one take: rests on each idea, flies between them)
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))
RPM = 2.4
def tt_angle(t): return R(-40) + 2 * math.pi * RPM / 60.0 * t
def tt_mat(t): return Matrix.Translation(TT_C) @ Matrix.Rotation(tt_angle(t), 4, 'Z')
# keys: (time, frame, position, target, lens, f-stop). frame 't' = riding on the turntable (inside the oven, close on the fork),
# 'w' = the world (outside, the oven on the counter). Every key is a rest: the camera eases in and out of it.
K = [
    (0.00, 't', (0.060, -0.110, 0.066), (0.002, -0.024, 0.024), 52, 110),     # frame one: the fork's tips already sparking
    (2.55, 't', (0.064, -0.113, 0.069), (0.002, -0.024, 0.024), 52, 110),
    (4.05, 'w', (-0.02, -0.95, 0.20), (-0.02, 0.0, 0.15), 40, 8),             # out through the door: the oven on the counter
    (5.45, 'w', (-0.01, -0.90, 0.19), (-0.02, 0.0, 0.15), 40, 8),
    (6.45, 'w', (-0.03, -0.56, 0.16), (-0.05, 0.0, 0.135), 35, 8),            # closer; the walls show their metal
    (8.20, 'w', (-0.035, -0.52, 0.155), (-0.05, 0.0, 0.135), 35, 8),
    (9.20, 'w', (-0.055, -0.40, 0.14), (-0.055, 0.0, 0.14), 32, 8),           # square on to the slice: the waves bouncing
    (12.45, 'w', (-0.055, -0.38, 0.137), (-0.055, 0.0, 0.14), 32, 8),
    (13.75, 't', (0.082, -0.118, 0.073), (0.002, -0.024, 0.024), 50, 110),    # in through the door to the fork's shape
    (14.75, 't', (0.079, -0.115, 0.070), (0.002, -0.024, 0.024), 50, 110),
    (17.30, 't', (0.057, -0.108, 0.063), (0.001, -0.024, 0.023), 55, 110),    # slowly closer while the charges slosh
    (19.85, 't', (0.047, -0.103, 0.060), (-0.001, -0.024, 0.023), 55, 110),    # right on the tips as they pile up
    (21.60, 't', (0.043, -0.100, 0.058), (-0.001, -0.024, 0.023), 55, 110),
    (24.35, 't', (0.039, -0.097, 0.056), (-0.001, -0.024, 0.023), 55, 110),   # hold close through the spark
    (25.55, 't', (0.070, -0.120, 0.090), (-0.010, 0.005, 0.030), 38, 64),     # back: lightning right next to the dinner
    (26.65, 't', (0.074, -0.122, 0.092), (-0.010, 0.005, 0.030), 38, 64),
    (27.85, 't', (0.004, -0.008, 0.112), (-0.080, 0.058, 0.068), 22, 64),     # the takeout box and its wire handle
    (31.00, 't', (0.008, -0.012, 0.108), (-0.080, 0.058, 0.068), 22, 64),
    (32.00, 't', (0.020, -0.060, 0.130), (0.025, 0.062, 0.026), 34, 64),     # the smooth spoon
    (34.05, 't', (0.016, -0.056, 0.126), (0.025, 0.062, 0.026), 34, 64),
    (35.25, 't', (0.070, -0.120, 0.100), (-0.012, 0.020, 0.026), 38, 64),     # fork and spoon together: it's the points
    (36.90, 't', (0.073, -0.122, 0.098), (-0.012, 0.020, 0.026), 38, 64),
    (38.60, 'w', (-0.10, -0.80, 0.22), (-0.05, 0.0, 0.14), 35, 8),            # out to the kitchen
    (39.60, 'w', (-0.09, -0.78, 0.215), (-0.05, 0.0, 0.14), 35, 8),
    (END, 't', (0.060, -0.110, 0.066), (0.002, -0.024, 0.024), 52, 110),      # back in to frame one (loop)
]
def key_world(k, t):
    _, fr, p, q, ln, fs = k
    if fr == 'w': return Vector(p), Vector(q)
    M = tt_mat(t); return M @ Vector(p), M @ Vector(q)
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    u = clamp((t - ts[i]) / (ts[i + 1] - ts[i]), 0, 1); s = u * u * (3 - 2 * u)            # zero speed at every key (rests)
    return vs[i] * (1 - s) + vs[i + 1] * s
def cam_at(t):
    ts = [k[0] for k in K]; pq = [key_world(k, t) for k in K]
    p = herm(ts, [a_ for a_, _ in pq], t); q = herm(ts, [b_ for _, b_ in pq], t)
    ln = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[5], 0, 0)) for k in K], t).x
    inside = p.y > -0.19
    sh = shake(t, 0.0006 if inside else 0.002, 5.0, 0.6)
    for ts_, amp in BIG_FLASH:
        if ts_ < t < ts_ + 0.35: sh += shake(t, amp * (1 - (t - ts_) / 0.35), 2.0, 16.0)
    return p + sh, q + sh * 0.5, ln, fs

# ---- the spark schedule: (time, kind, a, b) kind 'tt' = between tine tips a and b, 'wire' = at the carton's wire end a
SPARKS = [(0.05, 'tt', 1, 2), (0.80, 'tt', 0, 1), (1.62, 'tt', 2, 3), (2.40, 'tt', 1, 2),
          (T_EXPLODE - 0.15, 'tt', 0, 1), (T_EXPLODE, 'tt', 1, 3), (T_EXPLODE + 0.2, 'tt', 2, 3),
          (T_SPARK, 'tt', 1, 2), (T_SPARK + 0.32, 'tt', 0, 1), (T_BOLT - 0.1, 'tt', 2, 3), (T_BOLT + 0.35, 'tt', 0, 2), (T_BOLT + 0.8, 'tt', 1, 3),
          (T_BOLT + 1.25, 'tt', 0, 1), (T_BOLT + 1.7, 'tt', 2, 3)]
SPARKS += [(T_PAPER + 0.45 + 0.33 * i_, 'wire', 1, 0) for i_ in range(int((T_FIRE - T_PAPER) / 0.33))]
SPARKS += [(31.6, 'tt', 1, 2), (32.9, 'tt', 0, 1), (T_POINTS - 0.1, 'tt', 0, 1), (T_POINTS + 0.1, 'tt', 2, 3), (T_POINTS + 0.35, 'tt', 1, 2),
           (38.1, 'tt', 1, 2), (39.3, 'tt', 0, 1), (40.25, 'tt', 2, 3)]
SPARK_LEN = 0.12
BIG_FLASH = [(T_EXPLODE, 0.004), (T_SPARK, 0.0018)]

def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    TT.rotation_euler = (0, 0, tt_angle(t))
    for o in [x for x in bpy.data.objects if x.name == 'tt_ring']: o.rotation_euler = (0, 0, tt_angle(t))
    BULB.data.energy = 6.0
    # x-ray: the door clears whenever the camera flies through it or looks in; the enamel walls show bare metal for "made of metal"
    door = max(win(t, 2.65, 3.95, 0.12), win(t, T_METAL - 1.4, 13.55, 0.35), win(t, 37.35, 38.45, 0.12), ease_io((t - 39.65) / 0.12))
    for o in DOOR.children: o['xr'] = door
    walls = win(t, T_METAL - 1.0, T_SHAPE - 0.2, 0.5)
    for o in CAV: o['xr'] = walls
    # waves out of the waveguide, bouncing; the food soaks them up and warms
    WAVES['wv'] = win(t, T_BOUNCE - 0.5, T_SHAPE - 0.6, 0.4); WAVES['wt'] = max(0.0, t - (T_BOUNCE - 0.6)); WAVES.hide_render = WAVES['wv'] < 0.01
    FOOD['heat'] = MAC['heat'] = 0.55 * win(t, T_FOOD - 0.5, T_SHAPE + 0.8, 0.6)
    # charges in the fork: slosh with the waves, then crowd into the tips, then gone with the spark
    on = T_SHOVE - 0.4 < t < T_SPARK + 0.25
    pile = ease_io((t - (T_PILE - 0.4)) / 1.4)
    for o, x0, yy, k_, ph in CHARGES:
        o.hide_render = not on
        if not on: continue
        tip = TINE_TIPS[k_]
        xs = clamp(x0 + 0.018 * math.sin(2 * math.pi * 1.1 * t + ph), 0.006, 0.186)
        w = 0.0092 if xs < 0.098 else (0.0040 if xs < 0.135 else 0.0105)
        ys = (yy * w * 0.7) if xs < 0.15 else (tip.y + yy * 0.0008)
        xp = tip.x - 0.003 - 0.016 * ((ph * 7.3) % 1.0) ** 1.6; yp = tip.y + yy * 0.8 * min(0.0019, 0.0003 + (tip.x - xp) * 0.22)
        o.location = (xs + (xp - xs) * pile, ys + (yp - ys) * pile, 0.0026)
        s_ = 1.0; o.scale = (s_, s_, s_)
    g = 0.0 if t > T_SPARK - 0.02 else 0.35 * ease_io((t - T_PILE) / 1.2) + 0.65 * ease_io((t - T_AIR) / (T_SPARK - T_AIR))
    g += 0.6 * win(t, T_POINTS - 0.5, T_POINTS + 0.7, 0.2)
    for o in TIP_GLOW: o['g'] = g; o.hide_render = g < 0.01
    # the arcs live for a few frames each; a light flashes with them
    clear_arcs(); fl = 0.0; fpos = None
    Mf = FORK.matrix_world.copy(); Mc = CARTON.matrix_world.copy()
    for i_, (ts_, kind, a_, b_) in enumerate(SPARKS):
        if ts_ <= t < ts_ + SPARK_LEN:
            u = (t - ts_) / SPARK_LEN; seed = i_ * 31 + int(t * 120)
            if kind == 'tt':
                p0 = Mf @ TINE_TIPS[a_]; p1 = Mf @ TINE_TIPS[b_]
                rr_ = random.Random(i_ * 7 + int(t * 60)); fly = Mf @ (TINE_TIPS[a_] + Vector((0.006 + 0.004 * rr_.random(), rr_.uniform(-0.004, 0.004), 0.004 + 0.004 * rr_.random())))
                arc(p0, fly, seed + 5, 0.0006, 1)
            else: p0 = Mc @ WIRE_ENDS[a_]; p1 = Mc @ (WIRE_ENDS[a_] + Vector((0.004 if a_ else -0.004, -0.008, -0.016)))
            arc(p0, p1, seed, 0.00045 * (1.4 if ts_ in [x for x, _ in BIG_FLASH] else 1.0)); fl = max(fl, 1 - u); fpos = (p0 + p1) / 2
    ARC_LT.data.energy = 0.35 * fl
    if fpos is not None: ARC_LT.location = fpos
    # the paper catches: a small flame grows on the box corner, then dies down to a lick
    fa = ease_out((t - (T_FIRE - 0.35)) / 0.7) * (1 - 0.65 * ease_io((t - 31.0) / 2.0))
    for f in FLAMES: f['fa'] = fa; f['ft'] = t; f.hide_render = fa < 0.01
    FIRE_LT.data.energy = 0.35 * fa * (0.8 + 0.2 * math.sin(t * 37) * math.sin(t * 13))

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, fs = cam_at(tt_); look(cp, ct, ln, fs); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
    cp, ct, ln, fs = cam_at(t)
    if not (t > d and t < END - d): look(cp, ct, ln, fs)
