# ================================================================ the story, frame by frame
DT = 1.0 / FPS
def speed(t):
    """sled speed (m/s) along +y.  t < 0 is the run-up into the loop (same crawl as frame one)"""
    if t < T_STUCK:
        crawl = 0.16 * (0.35 + 0.65 * max(0.0, math.sin(2 * math.pi * t / 1.7 + 0.6)) ** 2)
        return crawl * (1 - smooth(T_STUCK - 1.4, T_STUCK, t))
    if t < T_GO: return 0.0
    v = 0.55 * smooth(T_GO, T_GO + 1.6, t)
    v *= 1 - 0.75 * smooth(T_SOAK + 0.3, T_SOAK + 1.0, t) * (1 - smooth(T_RIGHT, T_RIGHT + 1.0, t))
    return v
_SY = [0.0]
for i in range(int(TOTAL * FPS) + 3): _SY.append(_SY[-1] + speed(i * DT) * DT)
def local_t(t): return t - END if t >= T_RESET else t
def sled_y(t):
    tl = local_t(t)
    if tl < 0: return 0.0 + tl * 0.11                        # the crawl before frame one (average speed of the opening)
    i = tl * FPS; i0 = int(i); k = i - i0; return lerp(_SY[min(i0, len(_SY) - 1)], _SY[min(i0 + 1, len(_SY) - 1)], k)
def rel(t, p): return Vector((p[0], sled_y(t) + p[1], p[2]))
def dist_walked(t): return sled_y(t)

def state(t):
    tl = local_t(t); st = {}
    st['tl'] = tl
    st['v'] = speed(tl) if tl >= 0 else 0.11
    st['dry'] = 1.0 - smooth(T_GO - 0.4, T_GO + 0.8, tl) if tl >= 0 else 1.0
    st['stuck'] = (smooth(T_STUCK - 1.0, T_STUCK, tl) * (1 - smooth(T_GO - 0.3, T_GO + 0.6, tl))) if tl >= 0 else 0.0
    st['berm'] = (0.45 + 0.55 * smooth(0, T_STUCK, tl)) * (1 - smooth(T_GO, T_GO + 1.3, tl)) if tl >= 0 else 0.45 + 0.08 * tl
    st['climb'] = smooth(T_CLIMB, T_UP, tl) if tl >= 0 else 0.0
    st['pour'] = smooth(T_POUR - 0.3, T_POUR + 0.4, tl) if tl >= 0 else 0.0
    st['soak'] = (smooth(T_SOAK, T_SOAK + 0.5, tl) * (1 - smooth(T_RIGHT - 0.2, T_RIGHT + 0.5, tl))) if tl >= 0 else 0.0
    st['letgo'] = smooth(T_LETGO - 0.2, T_LETGO + 0.6, tl) if tl >= 0 else 0.0
    st['bog'] = (smooth(T_SOAK + 0.4, T_SOAK + 1.2, tl) * (1 - smooth(T_RIGHT, T_RIGHT + 1.0, tl))) if tl >= 0 else 0.0
    return st

def hauler(m_, t, st):
    sy = sled_y(t); k = m_.row; s_ = m_.side
    let = st['letgo'] if k >= 2 else 0.0
    # where he stands: on his rope's length ahead of the sled; after letting go he stops, steps out to the side and watches
    tl = st['tl']; ty = T_LETGO - 0.2
    if let > 0 and tl >= ty:
        y_ = sled_y(ty) + m_.off.y + 0.25 * smooth(ty, ty + 0.8, tl); x_ = m_.off.x + s_ * 0.75 * smooth(ty + 0.2, ty + 1.4, tl)
    else: y_ = sy + m_.off.y; x_ = m_.off.x
    m_.root.location = (x_, y_, 0.0)
    strain = st['stuck']; dry = st['dry']
    lean = (26 + 14 * strain + 3 * wob(t, 1.3, m_.seed)) * (1 - let) + 2 * let
    body = (9 + 7 * strain) * (1 - let)
    m_.root.rotation_euler = (R(body), 0, math.pi + s_ * R(8) * (1 - let) - s_ * R(35) * smooth(T_LETGO + 0.6, T_LETGO + 1.6, tl) * (k >= 2))
    walked = (dist_walked(t) if not (let > 0 and tl >= ty) else dist_walked(ty) + 0.25 * smooth(ty, ty + 0.8, tl))
    ph = walked * 2 * math.pi / 1.25 + m_.seed
    amp = 24 * clamp(st['v'] / 0.25, 0.25, 1.0) * (1 - strain) * (1 - 0.8 * smooth(ty + 1.0, ty + 1.6, tl) * (k >= 2))
    legs = walk_legs(ph, amp, 1.0, strain)
    m_.pose(spine=lean, neck=-lean * 0.45, head=-lean * 0.35 + 4 * strain, head_yaw=-s_ * 30 * smooth(T_LETGO + 0.8, T_LETGO + 1.8, tl) * (k >= 2), legs=legs)
    bpy.context.view_layer.update()
    inner = 'L' if s_ > 0 else 'R'; outer = 'R' if s_ > 0 else 'L'
    sh = m_.bone('shoulder01.' + inner); fw = m_.fwd(); rt = m_.right(); up = Vector((0, 0, 1)); inw = -rt if s_ > 0 else rt
    sh_top = sh + up * 0.07 - fw * 0.01 + inw * 0.01
    h1_ = sh + fw * 0.13 - up * 0.05 + inw * 0.01; h2_ = sh + fw * 0.19 - up * 0.24 + inw * 0.03
    rest_ = {'R': m_.world((-0.28, -0.05, 0.85)), 'L': m_.world((0.28, -0.05, 0.85))}
    for s2, hp in ((inner, h1_), (outer, h2_)):
        m_.tg['h' + s2].location = hp.lerp(rest_[s2], let)
        m_.tg['p' + s2].location = m_.world((0.7 if s2 == 'L' else -0.7, 0.35, 0.9))
        m_.orient(s2, rt if s2 == 'L' else -rt, -fw, 1.0 - let)
        m_.fingers(s2, 1.0 - 0.85 * let)
    bpy.context.view_layer.update()
    tie = rel(t, TIE[s_]) + Vector((0, 0, 0.02 * k))
    if let < 0.5:
        p1 = m_.palm(inner); p2 = m_.palm(outer)
        pts = sag(tie, sh_top - fw * 0.06, 0.02 + 0.06 * (1 - strain) * (1 - dry * 0.5), 12)
        pts += [sh_top + fw * 0.06, p1, p2, p2 + (p2 - p1).normalized() * 0.08 - up * 0.22]
    else:     # dropped: the rope lies on the sand, dragged along by the sled
        far = tie + Vector((s_ * 0.5, 2.6 + 0.4 * k, 0)); far.z = 0.02
        pts = [tie, tie + Vector((s_ * 0.06, 0.25, -0.3)), tie.lerp(far, 0.4) + Vector((0, 0, -tie.z + 0.02)), far]
    m_.rope.set(pts)

def waterman(t, st):
    m_ = WATERMAN; tl = st['tl']; c = st['climb']; up = Vector((0, 0, 1))
    beside = rel(t, (-1.05, 0.25, 0.0)); deck = rel(t, (0.12, 0.70, DECK_TOP + 0.005))
    hop = math.sin(math.pi * c) * 0.18
    m_.root.location = beside.lerp(deck, sm(c)) + up * hop - Vector((0, 0, 0.03 * st['bog']))
    m_.root.rotation_euler = (0, 0, math.pi - R(25) * (1 - c))
    pour = st['pour']; soak = st['soak']
    lift = math.sin(math.pi * clamp((tl - T_CLIMB) / (T_UP - T_CLIMB), 0, 1)) if tl >= 0 else 0.0
    legs = {'upperleg01.R': (R(-55 * lift), 0, 0), 'lowerleg01.R': (R(80 * lift), 0, 0), 'upperleg01.L': (R(-8 * lift), 0, 0)}
    m_.pose(spine=6 + 14 * pour + 8 * soak, neck=-4 - 4 * pour, head=4 + 10 * pour, legs=legs)
    bpy.context.view_layer.update()
    fw = m_.fwd()
    # the jar: held at the belly, then out in front and tipped forward
    tilt = R(78) * pour + R(34) * soak + R(4) * wob(t, 1.1, 3) * pour
    jc = m_.world((0, -0.36 - 0.12 * pour, 1.16 - 0.08 * pour - 0.04 * soak))
    JAR.location = jc; JAR.rotation_euler = (-tilt, 0, 0)
    bpy.context.view_layer.update()
    Mj = JAR.matrix_world
    for s_, sx in (('R', 1), ('L', -1)):
        lug = Mj @ Vector((sx * 0.205, 0, 0.03)); ctr = Mj @ Vector((0, 0, 0.03))
        m_.tg['h' + s_].location = lug + (lug - ctr).normalized() * 0.035
        m_.tg['p' + s_].location = m_.world((0.7 if s_ == 'L' else -0.7, 0.35, 0.9))
        m_.orient(s_, -(Mj.to_3x3() @ Vector((0, 0, 1))), ctr - lug, 1.0)
        m_.fingers(s_, 0.85)
    bpy.context.view_layer.update()
    return Mj

def fx(t, st, Mj):
    sy = sled_y(t); tl = st['tl']
    SLED.location = (0, sy, -0.03 * st['bog'])
    b = st['berm']
    for o in BERMS: o.scale = (1.0, 1.0 + 0.3 * b, max(b, 0.0) * 0.13 + 1e-4); o.hide_render = b < 0.02
    RIDGE.scale = (1.0, 1.0, max(b, 0.0) * 0.07 + 1e-4); RIDGE.hide_render = b < 0.02
    # grains tumbling off the piles while it inches along or they strain
    act = st['dry'] * (0.4 + 0.6 * clamp(st['v'] / 0.12 + st['stuck'], 0, 1)) * (b > 0.05)
    for k, g in enumerate(GRAINS):
        per = 0.9 + 0.5 * h1(k); u = ((t + h1(k + 3) * per) % per) / per; s_ = -1 if k % 2 else 1; side = 1 if (k // 2) % 2 else -1
        p = Vector((s_ * RUN_X + side * (0.06 + 0.14 * u), 0.98 + 0.08 * u + 0.05 * h1(k + 9), b * 0.13 * (1 - u) ** 1.5 + 0.01))
        g.location = p; g.rotation_euler = (u * 9, u * 7, 0); g.hide_render = act < 0.3 or u > 0.95
    # wet sand (painted into the road): strip behind the pour, the fresh spot, the soak
    pour = st['pour']
    started = tl >= T_POUR - 0.3 and tl >= 0
    y_hit = sy + 1.50
    if started:
        y0 = sled_y(T_POUR) + 1.50; sp = smooth(T_POUR + 0.1, T_POUR + 1.0, tl)
        NEAR['wy0'] = y0 - 0.15; NEAR['wy1'] = y_hit + 0.35 if y_hit - y0 > 0.1 else y0 - 1.0
        NEAR['sy'] = y_hit + 0.02; NEAR['sr'] = 0.14 + 0.60 * sp
    else: NEAR['wy0'], NEAR['wy1'], NEAR['sr'] = 0.0, -1.0, -1.0
    if tl >= T_SOAK and tl >= 0:
        ys = sled_y(T_SOAK + 0.5) + 1.55; g_ = smooth(T_SOAK + 0.1, T_SOAK + 1.4, tl)
        NEAR['ky'] = ys; NEAR['kr'] = 0.05 + 0.62 * g_
        POOL.hide_render = g_ < 0.02; POOL.location = (0.0, ys, 0.002); POOL.scale = (0.42 * g_ + 0.01, 0.55 * g_ + 0.01, 1.0 + 0.6 * st['soak'])
    else: NEAR['kr'] = -1.0; POOL.hide_render = True
    # the stream
    flow = pour * (1.0 + 1.3 * st['soak'])
    on = flow > 0.05 and tl >= 0
    STREAM.o.hide_render = not on; SPLASH.hide_render = True
    if on:
        mouth = Mj @ JAR_MOUTH; lip = (Mj.to_3x3() @ Vector((0, 0, 1))).normalized()
        v0 = lip * (0.35 + 0.45 * st['soak']) + Vector((0, st['v'], 0))
        hit = STREAM.set(mouth + lip * 0.01, v0, 0.015 + 0.014 * flow, t, 1.0)
        SPLASH.location = (hit.x, hit.y, 0.0); SPLASH.scale = (0.9 + 0.8 * st['soak'],) * 2 + (0.8 + 0.5 * wob(t, 8, 1) * 0.3 + 0.6 * st['soak'],)
        for k, d_ in enumerate(DROPS):
            per = 0.35 + 0.25 * h1(k); u = ((t + h1(k + 1) * per) % per) / per; a_ = 2 * math.pi * h1(k + 7)
            sp_ = (0.35 + 0.5 * h1(k + 11)) * (1 + st['soak']); up_ = 1.2 + 0.8 * h1(k + 13)
            tt = u * per
            d_.location = hit + Vector((math.cos(a_) * sp_ * tt, math.sin(a_) * sp_ * tt, max(up_ * tt - 4.9 * tt * tt, 0.0) + 0.006))
            d_.hide_render = u > 0.92 or h1(k + 20) > 0.55 + 0.45 * flow
    else:
        for d_ in DROPS: d_.hide_render = True
    # grain-scale bridges grow from the middle out while he says it
    gb = smooth(T_IN - 0.3, B[5] + DUR[5] - 0.6, t)
    for o in BRIDGES:
        k = clamp(gb * 2.0 - o['d'] / 0.9, 0.0, 1.0); o.hide_render = k < 0.02 or not (T_DIVE < t < T_OUT + 0.6); o.scale = (k, k, k) if k > 0 else (1e-3,) * 3

# ---- camera: keys of (time, pos, target, lens). A 'rel' tuple rides along with the sled; a Vector is a fixed spot in the world.
PYR_AIM = PYC + Vector((0, 0, 42))
def P_(t, p): return rel(t, p) if isinstance(p, tuple) else Vector(p)
HOLD = lambda t0, t1, p, q, lens: [(t0, p, q, lens), (t1, p, q, lens)]
pp = lambda u_, v_: paint_pt(u_, v_)
K = [
    (0.0, (1.15, 7.3, 1.25), (0.05, 2.1, 0.95), 30),
    (T_PYR - 0.3, (0.95, 7.0, 1.20), (0.05, 2.2, 0.95), 30),
    (T_PYR + 0.55, (1.9, 4.6, 3.6), (0.0, 1.2, 0.6), 28),             # up and over the crew
    (T_PYR + 1.6, (-1.6, -3.4, 3.6), (0.4, 20.0, 0.4), 26),           # up behind the stone: the crew, the road, the pyramid
    (B[2] - 0.6, (-1.5, -3.1, 3.5), (0.4, 20.0, 0.5), 27),
    (B[2] + 0.9, (0.98, 1.95, 0.30), (0.38, 0.86, 0.06), 30),          # down at the runner: the pile building, stuck
    (B[3] - 0.25, (0.92, 1.88, 0.27), (0.38, 0.86, 0.05), 30),
    (B[3] + 0.9, (2.05, 2.35, 1.15), (0.25, 0.70, 0.95), 30),          # he climbs onto the front deck
    (B[4] - 0.2, (1.95, 2.25, 1.05), (0.20, 0.85, 0.80), 30),
    (B[4] + 0.6, (2.3, 2.65, 1.55), (0.10, 0.95, 0.85), 28),          # the pour hits the sand, the dark spot spreads
    (T_DIVE, (1.9, 2.30, 1.10), (0.05, 1.30, 0.25), 28),
    (T_DIVE + 0.75, (0.10, 1.50, 0.07), (0.05, 1.47, 0.0), 30),        # down into the wet sand
]
MK = [   # grain scale (world spots at the micro set)
    (T_DIVE + 0.75, MICRO + Vector((0.20, -0.25, 1.9)), MICRO + Vector((0.1, -0.05, 0.0)), 30),
    (T_IN + 0.6, MICRO + Vector((0.36, -0.66, 0.34)), MICRO + Vector((0.02, 0.02, 0.03)), 30),
    (T_OUT - 0.5, MICRO + Vector((0.28, -0.52, 0.28)), MICRO + Vector((0.0, 0.05, 0.03)), 30),
    (T_OUT, MICRO + Vector((0.30, -0.45, 1.6)), MICRO + Vector((0.0, 0.1, 0.0)), 30),
]
K2 = [
    (T_OUT, (0.66, 1.30, 0.55), (0.58, 1.26, 0.0), 28),                  # back up out of the wet sand beside the runner, looking straight down
    (T_OUT + 0.8, (1.9, 1.45, 0.90), (0.20, 1.10, 0.15), 28),            # rising out to the side: the runner slides onto the dark wet strip
    (B[6] + 1.6, (2.7, 1.2, 1.05), (0.0, 0.8, 0.45), 30),
    (B[7] - 0.3, (2.9, 1.5, 1.15), (0.0, 1.0, 0.50), 30),
    (B[7] + 1.0, (3.7, 3.2, 1.8), (0.0, 2.3, 0.70), 28),                # wide side: pull halved
    (B[8] - 0.2, (3.6, 3.6, 1.9), (0.0, 2.5, 0.70), 28),
    (B[8] + 0.6, (4.4, 10.2, 3.1), (0.0, 3.0, 0.60), 28),               # from the front: the back rows let go
    (B[9] - 0.2, (4.3, 10.0, 3.0), (0.0, 3.0, 0.60), 28),
    (B[9] + 0.8, (2.0, 2.7, 1.25), (0.10, 1.20, 0.40), 28),             # too much: the puddle
    (B[10] - 0.1, (1.9, 2.6, 1.20), (0.10, 1.25, 0.40), 28),
]
def wall_keys():
    return [
        (T_WALL + 1.5, pp(0.70, 0.45) + Vector((3.4, 0.0, 0.1)), pp(0.66, 0.47), 25),   # the wall: rows of men hauling
        (T_WALL + 3.0, pp(0.60, 0.45) + Vector((3.3, 0.0, 0.1)), pp(0.56, 0.47), 25),
        (B[11] - 0.3, pp(0.26, 0.40) + Vector((3.5, 0.0, 0.0)), pp(0.25, 0.42), 25),    # the giant statue
        (B[11] + 1.0, pp(0.37, 0.70) + Vector((1.15, 0.0, 0.0)), pp(0.365, 0.72), 30),   # the man on the front, pouring
        (B[12] - 0.1, pp(0.37, 0.71) + Vector((1.05, 0.0, 0.0)), pp(0.365, 0.73), 30),
    ]
def interp(keys, t, sy_t):
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0.0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0.0
    else:
        i = max(j for j in range(len(keys)) if keys[j][0] <= t); k0, k1 = keys[i], keys[i + 1]; u = sm((t - k0[0]) / (k1[0] - k0[0]))
    def ev(p):
        if isinstance(p, tuple) and len(p) == 2 and p[0] == 'aim': return Vector(p[1])
        return P_(t, p)
    c0, c1 = ev(k0[1]), ev(k1[1]); a0, a1 = ev(k0[2]), ev(k1[2])
    # aim at far things by direction (so a target 400 m away blends cleanly with one 1 m away)
    d0 = (a0 - c0).normalized(); d1 = (a1 - c1).normalized(); cp = c0.lerp(c1, u); dr = d0.slerp(d1, u) if d0.dot(d1) > -0.99 else d1
    fl = lerp((a0 - c0).length if (a0 - c0).length < 60 else 6.0, (a1 - c1).length if (a1 - c1).length < 60 else 6.0, u)
    return cp, cp + dr * fl, lerp(k0[3], k1[3], u)
def camera(t):
    if t < T_DIVE + 0.75: return interp(K, t, None)
    if t < T_OUT: return interp(MK, t, None)
    if t < T_WALL: return interp(K2, t, None)
    last = K2[-1]; wk = [(T_WALL, rel(t, last[1]), rel(t, last[2]), last[3])] + wall_keys()
    if t < B[12] - 0.1: return interp(wk, t, None)
    # back to frame one: swing round from the wall to the opening view (the road was reset while we looked at the wall)
    cp0, ct0, l0 = interp(wk, B[12] - 0.1, None); st_ = (END - 0.0)
    cp1, ct1, l1 = interp(K, 0.0, None) if False else (rel(t, K[0][1]), rel(t, K[0][2]), K[0][3])
    u = sm(clamp((t - (B[12] - 0.1)) / (END - (B[12] - 0.1)), 0, 1)); u = sm(u)
    mid = cp0.lerp(cp1, u) + Vector((0.6, 0, 0.8)) * math.sin(math.pi * u)
    d0 = (ct0 - cp0).normalized(); d1 = (ct1 - cp1).normalized()
    return mid, mid + d0.slerp(d1, u) * lerp((ct0 - cp0).length, (ct1 - cp1).length, u), lerp(l0, l1, u)

def frame(f):
    t = f / FPS; S.frame_set(f); st = state(t)
    for m_ in HAUL: hauler(m_, t, st)
    Mj = waterman(t, st)
    fx(t, st, Mj)
    cp, ct, lens = camera(t)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = rel(t, q_[0:3]), rel(t, q_[3:6]), q_[6]
    cp = cp + shake(t, 0.006 * st['stuck'] * (t < T_DIVE), 2.0, 6.0)
    look(cp, ct, lens, 16.0)
