# ================================================================ the story, frame by frame
def local_t(t): return t - END if t >= T_RESET else t
CP_I = 35
CRACK_PT = wall_pt(*WC_PATH[CP_I], 0.0)
TB_PT = TBLOCK[0]['pts'][15]
MCRACK = lambda z_: MICRO + Vector((cr_x(z_)[0], 0.0, z_))

def worker(t, tl):
    m_ = WORKER; up = Vector((0, 0, 1))
    m_.root.location = TR_C + Vector((0.0, -0.80, 0.0)); m_.root.rotation_euler = (0, 0, math.pi)
    pour = smooth(T_POUR - 0.5, T_POUR + 0.4, tl) * (1 - smooth(T_POUR + 2.6, T_POUR + 3.4, tl)) if tl >= 0 else 0.0
    look_ = (1 - smooth(4.5, 6.0, tl)) * smooth(0.25, 0.9, tl) if tl >= 0 else 0.0   # he turns to look at the crack
    sway = wob(t, 0.7, 2) * 2.0
    m_.pose(spine=4 + 14 * pour, neck=-3 - 4 * pour, head=4 + 10 * pour + 6 * look_, head_yaw=-55 * look_ + sway, twist=-12 * look_)
    bpy.context.view_layer.update()
    fw = m_.fwd(); rt = m_.right()
    tilt = R(105) * pour + R(4) * wob(t, 1.1, 3) * pour
    c = m_.world((0.0, -0.36 - 0.22 * pour, 0.78 + 0.28 * pour))
    yaw = Matrix.Rotation(math.pi, 4, 'Z'); tip = Matrix.Rotation(-tilt, 4, rt)
    BUCKET_ROOT.matrix_world = Matrix.Translation(c - (tip.to_3x3() @ Vector((0, 0, BK_H * 0.5)))) @ tip @ yaw
    bpy.context.view_layer.update()
    Mb = BUCKET_ROOT.matrix_world
    for s_, sx in (('R', -1), ('L', 1)):
        rim = Mb @ Vector((sx * BK_R * 1.02, 0, BK_H * 0.80)); ctr = Mb @ Vector((0, 0, BK_H * 0.80))
        m_.tg['h' + s_].location = rim + (rim - ctr).normalized() * 0.02
        m_.tg['p' + s_].location = m_.world((0.7 if s_ == 'L' else -0.7, 0.35, 0.9))
        m_.orient(s_, -(Mb.to_3x3() @ Vector((0, 0, 1))).normalized(), (ctr - rim), 1.0)
        m_.fingers(s_, 0.85)
    bpy.context.view_layer.update()
    return pour, Mb

def fx(t, st):
    tl = st['tl']
    # the wall crack
    g = smooth(T_CRACK, T_CRACK + 0.55, tl) if tl >= 0 else 0.0
    set_wall_crack(g, 0.8 + 0.2 * smooth(0.5, 3.5, tl) if tl >= 0 else 0.8)
    for o, k in SPALL:
        u_, v_ = WC_PATH[4 + k * 4]; on = g > (4 + k * 4) / WC_N
        o.hide_render = not on
        if on:
            age = max(tl - T_CRACK - (4 + k * 4) / WC_N * 0.55, 0.0); fall = min(age, 0.6)
            p = wall_pt(u_ + 0.01 * h1(k), v_ - 0.01, 0.01) + Vector((0, -0.25 * fall, -4.9 * fall * fall))
            p.z = max(p.z, 0.008); o.location = p; o.rotation_euler = (age * 9, age * 5, 0)
    # the pour, the steam
    pour, Mb = st['pour'], st['Mb']
    lip = Mb @ Vector((0, -BK_R * 0.98, BK_H * 0.95)); lipd = (Mb.to_3x3() @ Vector((0, -0.4, 1.0))).normalized()
    BK_WATER.hide_render = pour > 0.75
    on = pour > 0.45 and tl >= 0
    POUR.o.hide_render = not on
    if on: POUR.set(lip, lipd * 0.6, 0.014 + 0.02 * pour, t, TR_C.z + 0.18)
    st_on = smooth(T_STEAM, T_STEAM + 0.6, tl) * (1 - smooth(T_DIVE2 + 1.0, T_DIVE2 + 2.0, tl)) if tl >= 0 else 0.0
    for k, o in enumerate(STEAM):
        per = 2.4; ph = ((t + h1(k) * per) % per) / per
        base = TR_C + Vector((-0.45 + 0.9 * h1(k + 3), -0.25 + 0.5 * h1(k + 5), 0.22))
        o.location = base + Vector((0.18 * wob(t, 0.4, k), 0.12 * wob(t, 0.5, k + 9), 1.7 * ph ** 0.8))
        r_ = 0.10 + 0.55 * ph; o.scale = (r_, r_, r_ * 0.85)
        o['dens'] = 16.0 * st_on * (1 - ph) ** 1.5 * smooth(0.0, 0.12, ph)
        o.hide_render = o['dens'] < 0.02
    # the test blocks: water from the funnels; the left one heals and stops dripping, the right keeps running
    bench_on = (tl >= T_OUT2 - 1.0 and tl < T_RESET) if tl >= 0 else False
    heal = smooth(T_HEAL0, T_HEAL1, tl)
    for k, tb in enumerate(TBLOCK):
        f0 = tb['funnel']; s_on = bench_on
        FSTREAM[k].o.hide_render = not s_on
        if s_on: FSTREAM[k].set(f0, Vector((0, 0, -0.1)), 0.004, t, tb['top'].z + 0.002)
        h = heal if k == 0 else 0.0
        cm = tb['cm'].node_tree.nodes['Principled BSDF']
        c0 = Vector((0.015, 0.013, 0.012)); c1 = Vector((0.80, 0.78, 0.72)); cc = c0.lerp(c1, h)
        cm.inputs['Base Color'].default_value = (*cc, 1); cm.inputs['Roughness'].default_value = 0.9 - 0.4 * h
        WETTOP[k].hide_render = not s_on; WETTOP[k].scale = (1.0 + 0.08 * h, 1.0 + 0.08 * h, 1.0)
        tr = TTRICKLE[k]; tr.set([p + Vector((0, -0.0025, 0)) for p in tb['pts']], [0.0055 * (1 - h)] * 30, Vector((0, -1, 0))); tr.o.hide_render = (not s_on) or h > 0.97
        rate = (1 - h)
        for j, d_ in enumerate(DRIPS[k]):
            per = 0.42; u = ((t + j * per / 4 + 0.13 * k) % per) / per
            src = tb['bottom']; fall = (src.z - tb['bowl'].z - 0.01)
            d_.location = src + Vector((0, 0, -fall * u * u))
            d_.hide_render = (not s_on) or (h1(j + int(t / per) * 7 + k) > rate) or u > 0.97
        BOWLW[k].hide_render = not bench_on
    # inside the concrete: water runs in, turns milky with lime, crystals grow and seal it
    zw = lerp(14.5, -14.5, smooth(T_WATER, T_WATER + 1.4, t))
    set_crack_water(zw if T_WATER <= t else 14.45)
    CWATER.hide_render = t < T_WATER
    milk = smooth(T_WATER + 0.9, B[7] - 0.2, t)
    wb = CWATERM.node_tree.nodes['Principled BSDF']; wb.inputs['Base Color'].default_value = (*Vector((0.35, 0.62, 0.95)).lerp(Vector((0.86, 0.88, 0.88)), milk), 1)
    wb.inputs['Transmission Weight'].default_value = 0.35 - 0.3 * milk; wb.inputs['Roughness'].default_value = 0.05 + 0.25 * milk
    wb.inputs['Emission Color'].default_value = (*Vector((0.2, 0.45, 0.9)).lerp(Vector((0.7, 0.72, 0.72)), milk), 1)
    span = T_SEAL - T_CRYS
    for o in CRYS:
        s0 = T_CRYS + span * (0.55 * (14.0 - o['z']) / 28.0 + 0.3 * o['t0']); k = smooth(s0, s0 + span * 0.45, t)
        o.hide_render = k < 0.02; sz = o['sz'] * k; o.scale = (sz, sz * 0.8, sz * 1.2)
    CFILL.hide_render = t < T_SEAL - 0.2

def state(t):
    tl = local_t(t); return {'tl': tl}

# ---- camera
def key(t, p, q, lens): return (t, Vector(p), Vector(q), lens)
CP_V = Vector(CRACK_PT)
K = [
    key(0.0, (0.60, 9.15, 1.55), (0.05, 12.0, 1.30), 24),
    key(B[1] - 0.2, (0.48, 9.45, 1.50), (0.05, 12.0, 1.30), 24),
    key(B[1] + 1.4, CP_V + Vector((0.25, -1.05, 0.12)), CP_V + Vector((0.0, 0, -0.02)), 30),      # in close: rain running into the crack
    key(T_DIVE1, CP_V + Vector((0.12, -0.70, 0.06)), CP_V, 30),
    key(T_DIVE1 + 0.6, CP_V + Vector((0.0, 0.05, 0.0)), CP_V + Vector((0, 1, 0)), 30),            # into the crack
]
LP = LIMES[3] if len(LIMES) > 3 else LIMES[-1]
LPV = LP.location.copy()
MK1 = [
    key(T_DIVE1 + 0.6, MCRACK(1.6) + Vector((0, -0.25, 0)), MCRACK(1.6) + Vector((0, 1.0, 0)), 26),
    key(T_IN1 + 0.9, MICRO + Vector((1.6, -9.5, 1.2)), MICRO + Vector((0.4, 0, 0.2)), 30),           # the cut face: lumps of lime everywhere
    key(B[3] + 0.4, MICRO + Vector((-0.6, -8.8, -0.4)), MICRO + Vector((-0.6, 0, -0.4)), 30),
    key(T_OUT1 - 0.6, LPV + Vector((0.3, -3.0, 0.3)), LPV, 30),
    key(T_OUT1, LPV + Vector((0.0, -0.25, 0.0)), LPV, 30),                                          # into a white lump
]
HEAPV = TR_C + Vector((0.1, 0.0, 0.25))
K2 = [
    key(T_OUT1, HEAPV + Vector((0.0, -0.06, 0.02)), HEAPV + Vector((0.0, 1.0, 0.0)), 30),           # out of the quicklime heap
    key(T_PIT + 0.9, TR_C + Vector((-1.25, -1.45, 1.55)), TR_C + Vector((0.0, -0.2, 0.55)), 28),     # the trough: he pours, it steams
    key(T_DIVE2 - 0.9, TR_C + Vector((-1.10, -1.30, 1.45)), TR_C + Vector((0.0, -0.1, 0.5)), 28),
    key(T_DIVE2 - 0.1, CP_V + Vector((0.18, -0.9, 0.1)), CP_V, 30),
    key(T_DIVE2 + 0.5, CP_V + Vector((0.0, 0.05, 0.0)), CP_V + Vector((0, 1, 0)), 30),               # into the crack again
]
MK2 = [
    key(T_DIVE2 + 0.5, MCRACK(1.4) + Vector((0, -0.2, 0)), MCRACK(1.4) + Vector((0, 1.0, 0)), 26),
    key(T_IN2 + 0.7, MICRO + Vector((0.9, -4.6, 0.7)), MICRO + Vector((0.0, 0, 0.0)), 30),           # the crack runs through a lime lump
    key(B[6] + 0.2, MICRO + Vector((0.7, -4.2, 0.6)), MICRO + Vector((0.0, 0, 0.1)), 30),
    key(B[7] - 0.2, MICRO + Vector((0.5, -3.0, 0.9)), MICRO + Vector((0.0, 0.6, 0.0)), 30),          # water in, milky
    key(T_SEAL - 0.1, MICRO + Vector((0.35, -2.2, 0.35)), MICRO + Vector((0.0, 0.8, 0.0)), 30),      # crystals close it up
    key(T_OUT2, MCRACK(-0.2) + Vector((0, -0.3, 0)), MCRACK(-0.2) + Vector((0, 1.0, 0)), 30),
]
TBV = Vector(TB_PT)
K3 = [
    key(T_OUT2, TBV + Vector((0.0, -0.03, 0.0)), TBV + Vector((0, 1, 0)), 30),                       # out of the left test block's crack
    key(T_BENCH + 0.8, BENCH_C + Vector((0.0, -1.85, 1.42)), BENCH_C + Vector((0.0, 0.0, 1.02)), 30),
    key(B[9] - 0.3, BENCH_C + Vector((0.0, -1.75, 1.38)), BENCH_C + Vector((0.0, 0.0, 1.02)), 30),
    key(B[9] + 0.7, BENCH_C + Vector((0.45, -0.85, 1.18)), BENCH_C + Vector((0.33, 0.0, 1.0)), 32),   # the right block keeps dripping
    key(T_REV, BENCH_C + Vector((0.43, -0.88, 1.18)), BENCH_C + Vector((0.33, 0.0, 1.0)), 32),
    key(B[11] - 0.3, PC + Vector((-58.0, -78.0, 34.0)), PC + Vector((-12.0, 0.0, 16.0)), 30),        # up and back: the Pantheon
    key(B[12] - 0.3, PC + Vector((-34.0, -46.0, 66.0)), PC + Vector((0.0, 0.0, 30.0)), 30),          # over the dome and its oculus
    key(END, K[0][1], K[0][2], K[0][3]),                                                             # back down to frame one
]
def interp(keys, t):
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0.0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0.0
    else:
        i = max(j for j in range(len(keys)) if keys[j][0] <= t); k0, k1 = keys[i], keys[i + 1]; u = sm((t - k0[0]) / (k1[0] - k0[0]))
    c0, c1 = k0[1], k1[1]; a0, a1 = k0[2], k1[2]
    d0 = (a0 - c0).normalized(); d1 = (a1 - c1).normalized(); cp = c0.lerp(c1, u); dr = d0.slerp(d1, u) if d0.dot(d1) > -0.99 else d1
    fl = lerp((a0 - c0).length, (a1 - c1).length, u)
    return cp, cp + dr * fl, lerp(k0[3], k1[3], u)
def camera(t):
    if t < T_DIVE1 + 0.6: return interp(K, t), False
    if t < T_OUT1: return interp(MK1, t), True
    if t < T_DIVE2 + 0.5: return interp(K2, t), False
    if t < T_OUT2: return interp(MK2, t), True
    return interp(K3, t), False

def frame(f):
    t = f / FPS; S.frame_set(f); st = state(t); tl = st['tl']
    st['pour'], st['Mb'] = worker(t, tl)
    fx(t, st)
    (cp, ct, lens), micro = camera(t)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = Vector(q_[0:3]), Vector(q_[3:6]), q_[6]; micro = (cp - MICRO).length < 60
    for o in MICRO_OBJS: o.hide_render = (not micro) or o.hide_render if o in CRYS or o in (CWATER, CFILL) else (not micro)
    rain_on = 0.0 if micro else (1.0 - smooth(T_REV, T_REV + 1.2, t) * (1 - smooth(END - 2.4, END - 0.6, t)))
    RAIN.hide_render = rain_on < 0.01
    if rain_on >= 0.01: set_rain(t, cp, rain_on)
    look(cp, ct, lens, 16.0)
