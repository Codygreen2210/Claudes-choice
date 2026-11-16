# ================================================================ the camera (one take: rests on each idea, flies between them) and the story's state
BR_W = junc_world(T_STOP)                                    # the strip of skin once the plate stops
MID = (CONTACT_W + CONTACT_B) / 2
P0, Q0 = (-0.040, -0.120, 0.105), (-0.055, -0.005, 0.062)
def off(p, d): return tuple(Vector(p) + Vector(d))
# keys: (time, position, target, lens, f-stop), all in the world. Every key is a rest: the camera eases in and out of it.
K = [
    (0.00, P0, Q0, 38, 32),                                                          # frame one: the cut grape turning in the running oven
    (2.75, (-0.043, -0.118, 0.103), Q0, 38, 32),
    (3.70, (-0.046, -0.176, 0.085), (-0.055, 0.020, 0.135), 28, 32),                  # back and up as the plasma shoots to the roof
    (4.50, (-0.047, -0.178, 0.084), (-0.055, 0.020, 0.145), 28, 32),
    (7.20, (-0.050, -0.180, 0.085), (-0.055, 0.020, 0.146), 28, 32),
    (8.30, off(BR_W, (0.014, -0.074, 0.040)), tuple(BR_W), 36, 32),                   # in on the strip of skin: the antenna idea
    (10.75, off(BR_W, (0.012, -0.071, 0.039)), tuple(BR_W), 36, 32),
    (11.20, (-0.050, -0.170, 0.120), (-0.050, 0.000, 0.100), 30, 32),                 # out through the door glass
    (11.80, (0.000, -0.800, 0.220), (0.000, 0.000, 0.200), 30, 16),
    (12.80, (0.000, -2.750, 0.330), (0.000, 0.000, 0.350), 26, 16),                   # the whole rack: twelve microwaves
    (15.00, (0.012, -2.700, 0.338), (0.000, 0.000, 0.350), 26, 16),
    (15.55, (-0.040, -0.420, 0.120), (WHOLE_C.x, 0.000, 0.080), 32, 16),              # back in to the two whole grapes
    (16.05, off(WHOLE_C, (0.010, -0.075, 0.032)), off(WHOLE_C, (0, 0, 0.004)), 36, 32),
    (17.20, off(WHOLE_C, (0.012, -0.073, 0.031)), off(WHOLE_C, (0, 0, 0.004)), 36, 32),
    (17.75, off(BEAD_C, (0.002, -0.075, 0.030)), off(BEAD_C, (0, 0, 0.003)), 36, 32),  # across to the water balls
    (19.05, off(BEAD_C, (0.003, -0.074, 0.030)), off(BEAD_C, (0, 0, 0.003)), 36, 32),
    (19.70, off(BEAD_C, (0.016, -0.090, 0.022)), off(BEAD_C, (0.014, 0, 0.004)), 32, 32),  # the waves come in from the right
    (22.70, off(BEAD_C, (0.017, -0.088, 0.021)), off(BEAD_C, (0.014, 0, 0.004)), 32, 32),
    (23.40, off(CONTACT_B, (0.001, -0.042, 0.010)), tuple(CONTACT_B), 45, 45),        # right in on the spot where they touch
    (26.30, off(CONTACT_B, (0.001, -0.039, 0.009)), tuple(CONTACT_B), 45, 45),
    (27.40, off(BEAD_C, (-0.004, -0.150, 0.040)), off(BEAD_C, (-0.004, 0, 0.080)), 28, 32),   # follow the plasma up
    (28.40, off(MID, (0.000, -0.148, 0.048)), off(MID, (0, 0, 0.095)), 22, 32),        # both pairs going: it was the water
    (29.90, off(MID, (0.002, -0.146, 0.048)), off(MID, (0, 0, 0.098)), 22, 32),
    (30.80, off(MID, (0.000, -0.145, 0.062)), (HOLE_C.x, HOLE_C.y, CZ1 - 0.012), 22, 32),   # up at the roof: a hole melts through
    (32.50, off(MID, (0.002, -0.143, 0.063)), (HOLE_C.x, HOLE_C.y, CZ1 - 0.012), 22, 32),
    (33.30, (-0.030, -0.950, 0.230), (-0.040, 0.000, 0.170), 30, 16),                 # out front for the share line: smoke out of the roof
    (33.85, (-0.028, -0.940, 0.228), (-0.040, 0.000, 0.170), 30, 16),
    (END, P0, Q0, 38, 32),                                                           # and back in to frame one
]
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    u = clamp((t - ts[i]) / (ts[i + 1] - ts[i]), 0, 1); s = u * u * (3 - 2 * u)
    return vs[i] * (1 - s) + vs[i + 1] * s
BIG = [(T_SPARK, 0.0012), (T_WRECK, 0.010), (T_RIP, 0.0006), (T_MELT, 0.0010)]
def cam_raw(t):
    ts = [k[0] for k in K]; return herm(ts, [Vector(k[1]) for k in K], t)
def cam_at(t):
    ts = [k[0] for k in K]
    p = herm(ts, [Vector(k[1]) for k in K], t); q = herm(ts, [Vector(k[2]) for k in K], t)
    ln = herm(ts, [Vector((k[3], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x
    close = p.y > -0.3
    sh = shake(t, 0.00025 if close else 0.002, 5.0, 0.6)
    for ts_, amp in BIG:
        if ts_ < t < ts_ + 0.35: sh += shake(t, amp * (1 - (t - ts_) / 0.35), 2.0, 16.0)
    return p + sh, q + sh * 0.5, ln, fs
# the four times the camera goes through the door glass (it turns clear around each)
FRONT = -MW_D / 2 - 0.004
_tc = [i_ / 200 for i_ in range(int(END * 200))]
CROSS = [t_ for a_, b_ in zip(_tc, _tc[1:]) for t_ in (a_,) if (cam_raw(a_).y - FRONT) * (cam_raw(b_).y - FRONT) < 0]
print('door crossings', [round(x, 2) for x in CROSS])

# ---- plasma, sparks, the waves
P1 = Plasma('p1', junc_world, T_SPARK, T_STOP, CZ1 - 0.022, 0.018, 1.0, rise=0.5)
PW = Plasma('pw', CONTACT_W + Vector((0, -0.002, GB * 0.9)), T_WHOLE, T_WHOLE + 0.55, CONTACT_W.z + 0.02, 0.008, 2.0, rise=0.4)
PB = Plasma('pb', CONTACT_B + Vector((0, -0.002, BEAD_R * 0.9)), T_BEAD, T_BEAD + 0.55, CONTACT_B.z + 0.02, 0.008, 3.0, rise=0.4)
P2 = Plasma('p2', CONTACT_B + Vector((0, -0.002, 0.002)), T_RIP, T_RESET, CZ1 - 0.024, 0.017, 4.0, drift=Vector((HOLE_C.x + 0.012, HOLE_C.y, CZ1 - 0.024)), rise=0.6)
P3 = Plasma('p3', CONTACT_W + Vector((0, -0.002, GB * 0.9)), T_ALL, T_RESET, CZ1 - 0.026, 0.016, 5.0, drift=Vector((HOLE_C.x - 0.012, HOLE_C.y, CZ1 - 0.026)), rise=0.6)
S0 = Sparks('s0', junc_world, 1.7, T_SPARK + 0.1, 26, 1, spd=(0.08, 0.3), life=(0.06, 0.16), size=0.8)
S1 = Sparks('s1', junc_world, T_SPARK - 0.05, T_STOP - 0.2, 60, 2, spd=(0.15, 0.6))
SW = Sparks('sw', CONTACT_W + Vector((0, -0.003, GB * 0.8)), T_WHOLE - 0.25, T_WHOLE + 0.5, 30, 3)
SB = Sparks('sb', CONTACT_B + Vector((0, -0.003, BEAD_R * 0.8)), T_BEAD - 0.25, T_BEAD + 0.5, 30, 4)
S2 = Sparks('s2', CONTACT_B + Vector((0, -0.004, 0.001)), T_RIP - 0.05, T_RIP + 0.9, 50, 5, spd=(0.2, 0.7))
S3 = Sparks('s3', CONTACT_W + Vector((0, -0.003, GB * 0.8)), T_ALL - 0.1, T_ALL + 0.8, 35, 6)
SD = Sparks('sd', HOLE_C + Vector((0, 0, -0.002)), T_MELT, T_RESET, 40, 7, spd=(0.02, 0.12), up=-1.5, life=(0.25, 0.5), size=1.2)
SKIN_ON = (T_SKIN - 0.6, B[4] - 0.1)
T_IN1 = CROSS[1] if len(CROSS) > 1 else 15.4

def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    a_ = tt_angle(t); TT.rotation_euler = (0, 0, a_)
    for o in [x for x in bpy.data.objects if x.name == 'tt_ring']: o.rotation_euler = (0, 0, a_)
    BULB.data.energy = 6.0
    door = max([win(t, c_ - 0.28, c_ + 0.22, 0.12) for c_ in CROSS] + [0.0])
    for o in DOOR.children: o['xr'] = door
    for o in CAV: o['xr'] = 0.0
    reset = t >= T_RESET
    swapped = T_SWAP <= t < T_RESET
    for o in CUT_PARTS: o.hide_render = swapped
    for o in WHOLE + BEADS: o.hide_render = not swapped
    # the old idea: current racing through the skin (it moves back and forth, like in an antenna)
    sk = win(t, *SKIN_ON, 0.3)
    for o in SKIN_GLOW: o.hide_render = True; o['g'] = sk * (0.7 + 0.3 * wob(t, 12, 1.0))
    for i, o in enumerate(CUR_DOTS):
        o.hide_render = sk <= 0
        if sk > 0:
            sv = _plen[-1] * (0.5 + 0.48 * math.sin(2 * math.pi * 1.1 * t + i * 0.52)); o.location = path_at(sv); o['g'] = sk
    # plasma and sparks
    for p in PLASMAS: p.update(t)
    for s in SPARKS: s.update(t)
    best = max(PLASMAS, key=lambda p: p.light(t)); Lp = sum(p.light(t) for p in PLASMAS)
    PL_LT.location = best.center(t) if Lp > 0 else Vector((0, 0, -5)); PL_LT.data.energy = 0.3 * Lp
    # the waves in, the trapped rings, the hot spot, the atoms
    wg = ease_io((t - T_WAVE) / 0.2) * (1 - ease_io((t - (T_TRAP + 0.3)) / 0.5))
    for i, (o, S_, C_) in enumerate(WAVES):
        on = wg > 0 and t < T_TRAP + 0.85; o.hide_render = not on
        if on: o.hide_render = not set_tube(o, wave_points(S_, C_, 0.20 * (t - T_WAVE), 2 * math.pi * 2.5 * t), 0.00045); o['g'] = wg
    ring_g = ease_io((t - (T_SHRINK + 0.2)) / 0.8) * (1 - ease_io((t - T_RIP) / 0.25)) if t < T_RESET else 0.0
    cram = ease_io((t - (T_CRAM - 0.6)) / 1.0)
    for o, bc, i, j in RINGS:
        o.hide_render = ring_g <= 0
        if ring_g <= 0: continue
        toward = CONTACT_B - bc
        o.location = bc + toward * 0.55 * cram; sc = 1 - 0.55 * cram; o.scale = (sc, sc, sc)
        o.rotation_euler = (0, (1 if (i + j) % 2 else -1) * t * (3.0 + j), 0); o['g'] = ring_g * (1 + 1.5 * cram) * (0.85 + 0.15 * wob(t, 20, i * 3 + j))
    hot = cram * (1 - ease_io((t - (T_RIP + 0.2)) / 0.3)) if t < T_RESET else 0.0
    HOT.hide_render = hot <= 0
    if hot > 0:
        r_ = 0.0008 + 0.0022 * hot * (1 + 0.15 * wob(t, 25, 9.0)); HOT.scale = (r_, r_, r_); HOT['g'] = hot * (1 + 0.6 * ease_io((t - (T_RIP - 0.5)) / 0.5))
    av = T_CRAM - 0.3 < t < T_RIP + 0.6
    for k_, (nuc, els, home, dirv, ph) in enumerate(ATOMS):
        for o in [nuc] + els: o.hide_render = not av
        if not av: continue
        sc = ease_out((t - (T_CRAM - 0.3 + 0.06 * k_)) / 0.3); jig = Vector((wob(t, 8, k_), wob(t, 8, k_ + 30), wob(t, 8, k_ + 60))) * 0.0003 * (1 + 2 * cram)
        rip = t - T_RIP
        nuc.location = home + jig + (dirv * 0.012 * ease_out(rip / 0.5) if rip > 0 else Vector())
        ns = 0.0008 * sc * (1 - ease_io((rip - 0.3) / 0.3) if rip > 0 else 1); nuc.scale = (ns,) * 3
        for j_, e in enumerate(els):
            a2 = ph + j_ * math.pi + t * 2 * math.pi * 3.0; orb = Vector((math.cos(a2), 0.35 * math.sin(a2 * 0.5), math.sin(a2))) * 0.0021
            if j_: orb = Vector((orb.z, orb.y, -orb.x))
            p = home + jig + orb
            if rip > 0:
                fly = (orb.normalized() + dirv * 0.3).normalized(); p = p + fly * 0.05 * ease_out(rip / 0.45)
            e.location = p; es = 0.00035 * sc * (1 - ease_io((rip - 0.35) / 0.2) if rip > 0 else 1); e.scale = (es,) * 3
    # the rack: windows flash as each oven zaps grapes, then smoke and scorch as they get wrecked
    for c in COPIES + [dict(off=Vector(), glow=MAIN_GLOW, top=None, soot=None, puffs=MAIN_PUFFS, tz=T_ZAP - 0.55 + 0.11 * 5.5, tw=T_WRECK - 0.15 + 0.07 * 5.5, seed=99.0)]:
        zg = win(t, c['tz'], c['tz'] + 0.32, 0.06) * (0.75 + 0.25 * wob(t, 30, c['seed'])) if T_OUT < t < T_IN1 else 0.0
        c['glow'].hide_render = zg <= 0; c['glow']['g'] = zg
        dw = t - c['tw']; wr = dw > 0 and t < T_RESET
        if c['top'] is not None:
            c['top'].hide_render = not wr; c['top']['g'] = ease_out(dw / 0.25) if wr else 0.0; c['top']['e'] = max(0.0, 1 - dw / 1.2) if wr else 0.0
            c['soot'].hide_render = not wr; c['soot']['g'] = 0.85 * ease_out(dw / 0.3) if wr else 0.0
        top0 = c['off'] + Vector((-0.04, -0.02, MW_H))
        for j_, o in enumerate(c['puffs']):
            u = (dw - 0.06 * j_) / 1.9; on = 0 < u < 1 and T_OUT < t < T_IN1 + 0.3; o.hide_render = not on
            if not on: continue
            sc = 0.05 + 0.17 * ease_out(u); o.scale = (sc, sc, sc * 0.9)
            o.location = top0 + Vector((0.08 * wob(j_ * 0.7, 1, c['seed']), -0.03 + 0.04 * wob(j_ * 0.7, 1, c['seed'] + 4), 0.03 + 0.32 * ease_out(u) + 0.035 * j_))
            o['g'] = ease_out(u / 0.08) * (1 - u) ** 1.3
    WIDE.data.energy = 140.0 * win(t, T_OUT - 0.1, T_IN1 + 0.2, 0.4)
    # our oven's roof: glows, then melts open; smoke gathers under it
    hv = B[12] - 0.3 < t < T_RESET; HOLE.hide_render = not hv
    if hv:
        HOLE['g'] = ease_out((t - (B[12] - 0.3)) / 0.6); HOLE['e'] = 0.4 + 0.6 * ease_io((t - (B[12] - 0.3)) / 1.0) * (0.85 + 0.15 * wob(t, 18, 2.0))
        HOLE['hr'] = 0.55 * ease_out((t - T_MELT) / 0.6) if t > T_MELT else 0.0
    for j_, o in enumerate(OUT_SMOKE):
        u = (t - (T_MELT + 0.3 + 0.22 * j_)) / 1.8; u = u % 1.0 if u > 0 else u; on = t > T_MELT + 0.3 + 0.22 * j_ and t < T_RESET; o.hide_render = not on
        if not on: continue
        sc = 0.02 + 0.05 * ease_out(u); o.scale = (sc * 1.6, sc, sc * 0.8)
        o.location = Vector((HOLE_C.x + 0.06 * wob(j_ * 0.7, 1, 3.0), HOLE_C.y - 0.24 * ease_out(u), MW_H + 0.015 + 0.06 * ease_out(u) + 0.05 * max(0.0, u - 0.6)))
        o['g'] = 0.7 * ease_out(u / 0.15) * (1 - u) * (1 - ease_io((t - (T_RESET - 0.35)) / 0.35))
    for j_, o in enumerate(ROOF_SMOKE):
        u = (t - (T_MELT - 0.4 + 0.15 * j_)) / 2.2; on = 0 < u and t < T_RESET; o.hide_render = not on
        if not on: continue
        a2 = 2 * math.pi * j_ / 6; sc = 0.012 + 0.03 * ease_out(u); o.scale = (sc, sc, sc * 0.6)
        o.location = HOLE_C + Vector((math.cos(a2) * 0.03 * ease_out(u), math.sin(a2) * 0.025 * ease_out(u) - 0.01, -0.012 - 0.004 * j_ % 3))
        o['g'] = 0.35 * ease_out(u / 0.2) * clamp(1.4 - u * 0.5, 0, 1)

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, fs = cam_at(tt_); look(cp, ct, ln, fs); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
    cp, ct, ln, fs = cam_at(t)
    if not (t > d and t < END - d): look(cp, ct, ln, fs)
