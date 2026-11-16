
# ================================================================ timing, the turntable, the camera (one take: rests on each idea, flies between them)
RPM = 5.0
W_TT = 2 * math.pi * RPM / 60.0; A0_TT = R(-40)
def tt_angle(t):
    if t < T_STOP: return A0_TT + W_TT * t
    if t < T_RESET: return A0_TT + W_TT * T_STOP
    return A0_TT + W_TT * (t - END)                     # set going again off camera, so the end runs straight into frame one
def tt_mat(t): return Matrix.Translation(TT_C) @ Matrix.Rotation(tt_angle(t), 4, 'Z')
E1 = tt_mat(T_STOP) @ EGG_LOCAL                       # where the oven egg sits once the plate stops
EM = TT_C + Vector((0, 0, EGG_LOCAL.z))              # the middle of its little circle
# keys: (time, position, target, lens, f-stop), all in the world. Every key is a rest: the camera eases in and out of it.
K = [
    (0.00, (-0.005, -0.135, 0.118), (-0.055, -0.005, 0.074), 30, 64),      # frame one: the egg turning in the running oven
    (2.90, (-0.012, -0.128, 0.112), (-0.055, -0.005, 0.074), 30, 64),
    (4.60, (-0.035, -0.360, 0.150), (-0.055, -0.005, 0.070), 38, 32),      # out through the opening door: it looks totally normal
    (5.30, (-0.034, -0.370, 0.152), (-0.055, -0.005, 0.070), 38, 32),
    (T_TOUCH - 0.25, (0.020, -0.160, 0.115), tuple(E1), 34, 64),            # in close as the fork touches it
    (T_BANG1 + 0.9, (0.024, -0.166, 0.118), tuple(E1), 34, 64),
    (9.60, (-0.010, -0.240, 0.140), (-0.055, 0.000, 0.070), 30, 32),       # egg all over the oven
    (11.00, (-0.050, -0.620, 0.200), (-0.050, 0.000, 0.120), 35, 16),
    (13.20, (0.000, -1.620, -0.500), (0.000, -0.780, -0.880), 28, 16),     # down to the floor: almost a hundred eggs
    (15.20, (0.004, -1.660, -0.520), (0.000, -0.780, -0.880), 28, 16),
    (16.60, (-0.140, -1.320, -0.830), (0.170, -1.240, -0.875), 30, 22),     # the test egg, the microphone a foot away, the thermometer
    (19.00, (-0.142, -1.322, -0.828), (0.170, -1.240, -0.875), 30, 22),
    (21.00, (-0.150, -1.335, -0.822), (0.170, -1.240, -0.875), 30, 22),     # hold through the bang
    (23.60, (-0.170, -1.370, -0.835), (-0.170, -1.210, -0.878), 38, 32),   # egg B: the x-ray
    (25.40, (-0.170, -1.366, -0.837), (-0.170, -1.210, -0.878), 38, 32),
    (27.40, (-0.170, -1.338, -0.846), (-0.171, -1.210, -0.878), 40, 45),   # into the yolk: the trapped drops
    (30.20, (-0.170, -1.334, -0.848), (-0.171, -1.210, -0.878), 40, 45),
    (31.00, (-0.166, -1.338, -0.838), (-0.170, -1.210, -0.872), 40, 45),   # the poke and the chain
    (T_BOIL - 0.05, (-0.166, -1.342, -0.838), (-0.170, -1.210, -0.872), 40, 45),
    (T_BOIL + 0.90, (-0.160, -1.380, -0.825), (-0.170, -1.210, -0.874), 36, 32),
    (38.60, (0.000, -1.700, -0.420), (0.000, -0.760, -0.890), 26, 16),     # high over the rows: egg roulette
    (42.30, (0.020, -1.720, -0.400), (0.000, -0.760, -0.890), 26, 16),
    (44.40, (-0.050, -0.800, 0.200), (-0.050, 0.000, 0.130), 35, 16),      # back up: the oven running again
    (45.00, (-0.048, -0.780, 0.198), (-0.050, 0.000, 0.130), 35, 16),
    (END, (-0.005, -0.135, 0.118), (-0.055, -0.005, 0.074), 30, 64),
]
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    u = clamp((t - ts[i]) / (ts[i + 1] - ts[i]), 0, 1); s = u * u * (3 - 2 * u)            # zero speed at every key (rests)
    return vs[i] * (1 - s) + vs[i + 1] * s
BIG_FLASH = [(T_BANG1, 0.004), (T_BANG2, 0.006), (T_BOIL, 0.003)]
def cam_at(t):
    ts = [k[0] for k in K]
    p = herm(ts, [Vector(k[1]) for k in K], t); q = herm(ts, [Vector(k[2]) for k in K], t)
    ln = herm(ts, [Vector((k[3], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x
    close = p.z > -0.2 and p.y > -0.3
    sh = shake(t, 0.0006 if close else 0.0015, 5.0, 0.6)
    for ts_, amp in BIG_FLASH:
        if ts_ < t < ts_ + 0.35: sh += shake(t, amp * (1 - (t - ts_) / 0.35), 2.0, 16.0)
    return p + sh, q + sh * 0.5, ln, fs
_tc = [t_ / 100 for t_ in range(4400, int(END * 100))]
T_IN = next((t_ for t_ in _tc if herm([k[0] for k in K], [Vector(k[1]) for k in K], t_).y > -MW_D / 2 - 0.02), END - 0.3)   # the end flight goes in through the door

# ---- the bursts: the oven egg, test egg A, x-ray egg B, and about one in three of the floor eggs (egg roulette)
def oven_floor(x, y):
    if y < CY0: return 0.0 if y < -MW_D / 2 - 0.01 else CZ0
    dxy = math.hypot(x - TT_C.x, y - TT_C.y)
    if dxy < 0.096: return TT_C.z + 0.0215
    if dxy < 0.135: return TT_C.z + 0.02
    return CZ0
BURST1 = Burst('b1', T_BANG1, E1, 70, 26, 3, spd=(0.3, 1.2), up=0.5, box_=((CX0, CX1), (CY0 - 0.05, CY1), CZ1), floor=oven_floor, size=0.9, steam=2, flash=1.0)
BURSTA = Burst('ba', T_BANG2, A_C, 70, 26, 7, spd=(0.6, 2.2), up=0.6, floor=FLOOR_Z, size=1.0, steam=0, flash=1.4)
BURSTB = Burst('bb', T_BOIL, B_C, 60, 26, 8, spd=(0.5, 1.8), up=0.6, floor=FLOOR_Z, size=1.0, steam=0, flash=1.2)
_rr = random.Random(33); ROUL = []
_pick = _rr.sample(range(len(GRID)), 33)
_tr0, _tr1 = T_ROUL - 0.15, B[13] + 0.6
for k_, gi in enumerate(_pick):
    t0 = _tr0 + (_tr1 - _tr0) * (k_ + _rr.uniform(-0.3, 0.3)) / len(_pick)
    ROUL.append((GRID[gi], Burst(f'r{k_}', t0, GRID[gi].location.copy(), 14, 5, 100 + k_, spd=(0.35, 1.1), up=0.8, floor=FLOOR_Z, size=0.8, steam=0, flash=0.35)))
ROUL_T = {id(o): b.t0 for o, b in ROUL}

# ---- the thermometer's path (tip position), eased between keys; hidden before and after
A_TOP = A_C + Vector((0, 0, EGG_R))
TK = [(T_MIC - 1.2, A_TOP + Vector((-0.03, 0.04, 0.26))), (T_STAB - 0.15, A_TOP + Vector((0, 0, 0.03))), (T_STAB, A_TOP + Vector((0, 0, -0.012))),
      (T_BANG2, A_TOP + Vector((0, 0, -0.012))), (T_BANG2 + 0.3, A_TOP + Vector((0, 0, 0.08))), (T_POKE - 0.5, POKE_B + Vector((0, 0, 0.04))),
      (T_POKE, POKE_B + Vector((0, 0, -0.008))), (T_BOIL, POKE_B + Vector((0, 0, -0.008))), (T_BOIL + 0.7, POKE_B + Vector((0.02, 0.03, 0.26)))]
THERM_KIDS = list(THERM.children)
def therm_at(t):
    ts = [k[0] for k in TK]; return herm(ts, [k[1] for k in TK], t)

def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    a_ = tt_angle(t); TT.rotation_euler = (0, 0, a_)
    for o in [x for x in bpy.data.objects if x.name == 'tt_ring']: o.rotation_euler = (0, 0, a_)
    BULB.data.energy = 6.0
    # the door: shut while it runs, swings open at "comes out", shut again (off camera) for the loop; see-through as the camera flies in at the end
    HINGE.rotation_euler = (0, 0, -R(108) * ease_io((t - (T_DOOR - 0.25)) / 0.5) if t < T_RESET else 0.0)
    door = ease_io((t - (T_IN - 0.4)) / 0.2)
    for o in DOOR.children: o['xr'] = door
    for o in CAV: o['xr'] = 0.0
    # the oven egg, then its burst; set back up for the loop
    EGG1.hide_render = T_BANG1 <= t < T_RESET
    BURST1.update(t if t < T_RESET else -1.0)
    # the fork comes in through the open door, touches, presses, and jumps back with the bang
    u = (E1 - (E1 + Vector((0.07, -0.30, 0.10)))).normalized(); p_far = E1 - u * 0.33; p_touch = E1 - u * 0.0235
    fv = T_DOOR + 0.3 < t < T_BANG1 + 0.7
    for o in FORK_PARTS: o.hide_render = not fv
    s_ = ease_io((t - (T_DOOR + 0.4)) / max(0.3, T_TOUCH - T_DOOR - 0.4))
    tip = p_far.lerp(p_touch, s_) + u * 0.004 * ease_io((t - T_TOUCH) / max(0.1, T_BANG1 - T_TOUCH))
    if t > T_BANG1: tip = tip - u * 0.12 * ease_out((t - T_BANG1) / 0.25) + Vector((0, 0, 0.03)) * ease_out((t - T_BANG1) / 0.25)
    FORKP.location = tip; FORKP.rotation_quaternion = u.to_track_quat('X', 'Z')
    # the floor: the test egg A, its bang and the shockwave past the microphone
    EGGA.hide_render = t >= T_BANG2
    BURSTA.update(t)
    dt = t - T_BANG2; on = 0 <= dt < 0.6
    SHOCK.hide_render = True; SHOCK_RING.hide_render = not on
    if on:
        r_ = 0.03 + 0.9 * dt; g_ = (1 - dt / 0.6) ** 1.5
        SHOCK.scale = (r_, r_, r_ * 0.75); SHOCK.location = A_C; SHOCK['g'] = 0.15 * g_
        SHOCK_RING.scale = (r_, r_, r_); SHOCK_RING.location = (A_C.x, A_C.y, FLOOR_Z + 0.002); SHOCK_RING['g'] = g_
    mic0 = A_C + Vector((0.30, 0.0, 0.045)); hit = dt - 0.29
    MIC.location = mic0 + (shake(t, 0.004 * math.exp(-hit / 0.18), 9.0, 30.0) if hit > 0 else Vector())
    # the thermometer
    tv = TK[0][0] < t < TK[-1][0]
    for o in THERM_KIDS: o.hide_render = not tv
    THERM.location = therm_at(t) if tv else Vector((0, 0, -5))
    # egg B: x-ray, drops, heat, the chain of steam flashes, then it boils apart
    xr = ease_io((t - T_XRAY) / 0.6); gone = t >= T_BOIL
    EGGB['xr'] = YOLKB['xr'] = xr; EGGB.hide_render = YOLKB.hide_render = gone
    chain = ease_io((t - T_CHAIN) / max(0.2, T_BOIL - T_CHAIN))
    jig = shake(t, 0.0012 * chain, 4.0, 28.0)
    EGGB.location = B_C + jig; YOLKB.location = B_C + Vector((-0.002, 0, 0)) + jig
    YOLKB['heat'] = 0.7 * ease_io((t - T_HOT) / 1.5) + 0.5 * chain
    for i, d in enumerate(DROPS):
        vis = xr > 0.3 and T_DROPS - 0.3 < t < T_BOIL; d.hide_render = not vis
        if not vis: continue
        sc = ease_out((t - (T_DROPS + 0.03 * i)) / 0.3); h = ease_io((t - (T_HOT + 0.02 * i)) / 1.2)
        ti = T_FLASH if i == DROP0 else T_CHAIN + (_dd[i] - _dmin) / max(1e-6, _dmax - _dmin) * 0.55
        f = max(0.0, 1 - (t - ti) / 0.3) if t >= ti else 0.0
        grow = 1 + 1.8 * ease_out((t - ti) / 0.15) if t >= ti else 1.0
        d.scale = (sc * grow,) * 3; d['h'] = h; d['f'] = f
        d.location = Vector(d['home']) + jig + Vector((wob(t, 9, i), wob(t, 9, i + 50), wob(t, 9, i + 90))) * 0.0005 * h
    BURSTB.update(t)
    # egg roulette: about one in three of the floor eggs goes off
    for o, b in ROUL: o.hide_render = t >= b.t0; b.update(t)
    # one flash light at whichever burst is brightest right now
    best = max(BURSTS, key=lambda b: b.light(t)); L_ = best.light(t)
    POP_LT.location = best.c + Vector((0, 0, 0.03)); POP_LT.data.energy = 6.0 * L_

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, fs = cam_at(tt_); look(cp, ct, ln, fs); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
    cp, ct, ln, fs = cam_at(t)
    if not (t > d and t < END - d): look(cp, ct, ln, fs)
