# ================================================================ the course: a turtle lays the track piece by piece (same geometry for physics and render)
MR = 0.05                      # marble radius (m); the whole world is "big marble" scale, which reads better on camera
NM = 8
COLS = [('RED', (1.0, 0.06, 0.04)), ('ORANGE', (1.0, 0.36, 0.0)), ('YELLOW', (1.0, 0.85, 0.05)), ('GREEN', (0.1, 1.0, 0.15)),
        ('CYAN', (0.0, 0.9, 1.0)), ('BLUE', (0.08, 0.2, 1.0)), ('PURPLE', (0.6, 0.1, 1.0)), ('PINK', (1.0, 0.15, 0.6))]
PHYS = []                       # passive collision objects
PIECES = []                     # course pieces in order, for progress (who's in front)
LIPS = []                       # (points, colour) lip lines for the LED rails
SAMPLES_ALL = []                # every channel sample point (for supports / overlap checks)
SECTION_SIGNS = []              # (pos, heading, text, colour)
KIN = []                        # kinematic movers: (obj, fn(t) -> (loc, rot))

def profile(w, rc, wh, n=8):
    """flat-bottom U: half flat width w, corner radius rc, wall top wh (above the bottom). (side, up) pairs left->right"""
    pts = [(-(w + rc), wh)]
    for k in range(n + 1):
        a_ = math.pi + (math.pi / 2) * k / n; pts.append((-w + rc * math.cos(a_), rc + rc * math.sin(a_)))
    for k in range(n + 1):
        a_ = 1.5 * math.pi + (math.pi / 2) * k / n; pts.append((w + rc * math.cos(a_), rc + rc * math.sin(a_)))
    pts.append((w + rc, wh)); return pts

class Turtle:
    def __init__(s, pos, hdg_deg):
        s.p = Vector(pos); s.h = R(hdg_deg); s.g = 0.0; s.b = 0.0; s.w, s.rc, s.wh = 0.4, 0.08, 0.25
    def run(s, L, grade=None, turn=0.0, w=None, rc=None, wh=None, wave=None, ds=0.035, bank=True, blend=0.6):
        """L horizontal length; grade = dz/dx reached smoothly over `blend` m; turn = total heading change (deg, + = left)"""
        g0 = s.g; g1 = s.g if grade is None else grade; n = max(2, int(L / ds)); out = []
        w0, rc0, wh0 = s.w, s.rc, s.wh; w1 = w0 if w is None else w; rc1 = rc0 if rc is None else rc; wh1 = wh0 if wh is None else wh
        kappa = R(turn) / L; b0 = s.b
        for i in range(n + 1):
            u = i / n; d = u * L; gg = lerp(g0, g1, smooth(0, min(blend, L), d))
            if i > 0:
                hm = s.h + kappa * ds_ * 0.5; s.p = s.p + Vector((math.cos(hm) * ds_, math.sin(hm) * ds_, gg * ds_)); s.h += kappa * ds_
            ds_ = L / n
            wz = 0.0; wslope = 0.0
            if wave:
                amp, lam = wave; env = smooth(0, 0.8, d) * smooth(L, L - 0.8, d)
                wz = amp * env * (math.sin(2 * math.pi * d / lam) ); wslope = amp * env * 2 * math.pi / lam * math.cos(2 * math.pi * d / lam)
            T = Vector((math.cos(s.h), math.sin(s.h), gg + wslope)).normalized()
            side = Vector((math.sin(s.h), -math.cos(s.h), 0.0)); up = side.cross(T).normalized(); side = T.cross(up).normalized()
            b1 = 0.0
            if bank and abs(kappa) > 1e-6: b1 = clamp(math.atan(1.4 ** 2 / (9.81 / abs(kappa))), 0, R(14)) * (1 if kappa > 0 else -1)
            b_ = lerp(b0, b1, smooth(0, min(1.2, L * 0.45), d))
            sd = side * math.cos(b_) + up * math.sin(b_); upb = up * math.cos(b_) - side * math.sin(b_)
            out.append(dict(p=s.p + Vector((0, 0, wz)), T=T, side=sd, up=upb, w=lerp(w0, w1, u), rc=lerp(rc0, rc1, u), wh=lerp(wh0, wh1, u), h=s.h))
        s.g = g1; s.b = b_; s.w, s.rc, s.wh = w1, rc1, wh1
        return out
    def jump(s, dx, dz, dturn=0.0):
        s.p = s.p + Vector((math.cos(s.h) * dx, math.sin(s.h) * dx, dz)); s.h += R(dturn)
    def at(s, pos, hdg_deg, grade=0.0):
        s.p = Vector(pos); s.h = R(hdg_deg); s.g = grade; s.b = 0.0

def sweep(name, samples, m=None, cap_start=False, cap_end=False, tube_r=None, lanes=0, phys=True, pieces=True, led=None):
    """the channel surface (one-sided, normals inward). tube_r -> closed glass pipe instead of an open U."""
    vs, fs = [], []; ring = None
    for smp in samples:
        if tube_r: prof = [(tube_r * math.cos(2 * math.pi * k / 20), tube_r + tube_r * math.sin(2 * math.pi * k / 20)) for k in range(20)]
        else: prof = profile(smp['w'], smp['rc'], smp['wh'])
        ring = len(prof)
        for y_, z_ in prof: vs.append(smp['p'] + smp['side'] * y_ + smp['up'] * z_)
    n = len(samples)
    for i in range(n - 1):
        for k in range(ring if tube_r else ring - 1):
            k2 = (k + 1) % ring; fs.append((i * ring + k, i * ring + k2, (i + 1) * ring + k2, (i + 1) * ring + k))
    if cap_start: fs.append(tuple(range(ring)))
    if cap_end: fs.append(tuple((n - 1) * ring + k for k in range(ring))[::-1])
    o = mesh(name, [tuple(v) for v in vs], fs, m)
    if phys: PHYS.append(o)
    if pieces: PIECES.append(dict(kind='chan', name=name, pts=np.array([tuple(s_['p'] + s_['up'] * MR) for s_ in samples]),
                                  rad=max(s_['w'] + s_['rc'] for s_ in samples) + 0.25))
    SAMPLES_ALL.extend(tuple(s_['p']) for s_ in samples[::3])
    if not tube_r: LIPS.append(([s_['p'] + s_['side'] * -(s_['w'] + s_['rc']) + s_['up'] * s_['wh'] for s_ in samples],
                                [s_['p'] + s_['side'] * (s_['w'] + s_['rc']) + s_['up'] * s_['wh'] for s_ in samples], led))
    return o

def funnel(name, ctr, Rf, rh, depth, m, wall=0.30):
    """vortex: z falls like 1/r toward the hole; a rim wall keeps them in"""
    prof = [(Rf, ctr[2] + wall)]
    nn = 36
    for k in range(nn + 1):
        r_ = Rf * (rh / Rf) ** (k / nn); f_ = (1 / r_ - 1 / Rf) / (1 / rh - 1 / Rf); prof.append((r_, ctr[2] - depth * f_))
    prof.append((rh, ctr[2] - depth - 0.06))
    o = lathe(name, prof, 72, m, loc=(ctr[0], ctr[1], 0)); PHYS.append(o)
    PIECES.append(dict(kind='funnel', name=name, c=np.array(ctr), Rf=Rf, rh=rh, z0=ctr[2] + 0.4, z1=ctr[2] - depth - 0.5))
    SAMPLES_ALL.extend((ctr[0] + Rf * math.cos(a_), ctr[1] + Rf * math.sin(a_), ctr[2]) for a_ in np.linspace(0, 6.28, 24))
    return o

def plinko(name, top, hdg, tilt, W, Lb, m_board, m_peg, m_wall):
    """tilted peg board; returns (bottom-centre point, heading). Pegs on a hex grid, walls funnel the bottom to a gap"""
    h = R(hdg); th = R(tilt)
    D = Vector((math.cos(h) * math.cos(th), math.sin(h) * math.cos(th), -math.sin(th)))
    Sd = Vector((math.sin(h), -math.cos(h), 0)); Nn = Sd.cross(D).normalized()
    if Nn.z < 0: Nn = -Nn
    P = lambda u, v, n=0.0: Vector(top) + D * u + Sd * v + Nn * n
    hw = W / 2
    o = mesh(name, [tuple(P(-0.3, -hw)), tuple(P(-0.3, hw)), tuple(P(Lb, hw)), tuple(P(Lb, -hw))], [(0, 1, 2, 3)], m_board); PHYS.append(o)
    walls = []
    def wall(u0, v0, u1, v1, hgt=0.16, nm='w'):
        vs_ = [P(u0, v0), P(u1, v1), P(u1, v1, hgt), P(u0, v0, hgt)]
        w_ = mesh(name + nm, [tuple(v) for v in vs_], [(0, 1, 2, 3)], m_wall); PHYS.append(w_); walls.append(w_); return w_
    wall(-0.3, -hw, Lb, -hw, nm='L'); wall(-0.3, hw, Lb, hw, nm='R'); wall(-0.3, -hw, -0.3, hw, nm='T')
    gap = 0.17
    wall(Lb - 0.75, -hw, Lb, -gap, nm='FL'); wall(Lb - 0.75, hw, Lb, gap, nm='FR')
    pegs = []; row = 0; u = 0.6
    while u < Lb - 0.85:
        off = 0.0 if row % 2 == 0 else 0.11; v = -hw + 0.19 + off
        while v < hw - 0.18:
            pegs.append((P(u, v), Nn)); v += 0.22
        u += 0.2; row += 1
    # pegs as ONE mesh of little cylinders (fast)
    vs_, fs_ = [], []
    for c_, n_ in pegs:
        a0 = len(vs_); seg = 12
        ax1 = Sd; ax2 = D
        for k in range(seg):
            a_ = 2 * math.pi * k / seg; rr = ax1 * math.cos(a_) * 0.022 + ax2 * math.sin(a_) * 0.022
            vs_.append(tuple(c_ + rr)); vs_.append(tuple(c_ + rr + n_ * 0.13))
        for k in range(seg):
            k2 = (k + 1) % seg; fs_.append((a0 + 2 * k, a0 + 2 * k2, a0 + 2 * k2 + 1, a0 + 2 * k + 1))
        fs_.append(tuple(a0 + 2 * k + 1 for k in range(seg)))
    po = mesh(name + '_pegs', vs_, fs_, m_peg, smooth_=False); PHYS.append(po)
    PIECES.append(dict(kind='board', name=name, top=np.array(top), D=np.array(D), Sd=np.array(Sd), Lb=Lb, hw=hw + 0.3))
    for uu in np.linspace(0, Lb, 12):
        for vv in (-hw, 0, hw): SAMPLES_ALL.append(tuple(P(uu, vv)))
    return P(Lb, 0), hdg, (o, po, walls, P, D, Sd, Nn)

def build_course(M):
    """M: materials dict. Lays the whole course; returns the turtle path landmarks used by camera and decor."""
    LM = {}
    t = Turtle((0, 0, 30.0), 0)
    # 1 start ramp with 8 lanes for the first metre, then a bumpy slope that narrows
    a1 = t.run(3.2, grade=-0.30, w=0.42, rc=0.08, wh=0.22, blend=0.01)
    sweep('start', a1, M['track'], cap_start=True, led='white'); LM['start'] = a1
    a2 = t.run(6.0, grade=-0.13, w=0.26, wave=(0.05, 1.1)); sweep('bumps', a2, M['track'], led='white'); LM['bumps'] = a2
    # 2 the zigzag: six legs with tight U-turns (marbles bank hard and bash the walls)
    zz = []
    for k in range(6):
        leg = t.run(3.4, grade=-0.10, w=0.24, wh=0.22); zz.append(leg)
        if k < 5:
            ut = t.run(1.65, grade=-0.05, turn=180 if k % 2 == 0 else -180, wh=0.30); zz.append(ut)
    zzs = [s_ for seg in zz for s_ in seg]; sweep('zigzag', zzs, M['track2'], led='cyan'); LM['zigzag'] = zzs
    # 3 the steep drop, a kicker, JUMP 1, into a wide catch tray
    d3 = t.run(3.0, grade=-0.42, w=0.16, wh=0.20, blend=0.5); k3 = t.run(0.7, grade=0.30, blend=0.5)
    sweep('drop1', d3 + k3, M['track'], led='orange'); LM['kick1'] = k3[-1]['p'].copy(); LM['kick1_h'] = t.h
    t.jump(1.0, -0.9); t.g = -0.10
    tr = t.run(3.4, grade=-0.08, w=0.40, wh=0.34, blend=0.1); tr2 = t.run(3.5, turn=-60, w=0.14, wh=0.24)
    sweep('land1', tr + tr2, M['track'], cap_start=True, led='orange'); LM['land1'] = tr[0]['p'].copy()
    # 4 into vortex funnel 1, tangent at its rim
    Rf = 1.25; fdrop = 0.22
    hh = t.h; ctr = t.p + Vector((math.cos(hh + math.pi / 2), math.sin(hh + math.pi / 2), 0)) * (Rf - 0.38)
    ctr.z = t.p.z - 0.10 - 0.30
    funnel('vortex1', tuple(ctr), Rf, 0.085, 1.0, M['funnel']); LM['vortex1'] = ctr.copy()
    # 5 catch under the hole, then the banked half-pipe S-bends
    t.at((ctr.x - 0.35 * math.cos(hh), ctr.y - 0.35 * math.sin(hh), ctr.z - 1.0 - 0.55), math.degrees(hh), grade=-0.10)
    t.w, t.rc, t.wh = 0.20, 0.10, 0.34
    c5 = t.run(1.6, grade=-0.12, w=0.0, rc=0.30, wh=0.36)
    s1 = t.run(5.0, turn=90, grade=-0.12); s2 = t.run(5.5, turn=-130); s3 = t.run(5.5, turn=130); s4 = t.run(3.5, turn=-80)
    sweep('halfpipe', c5 + s1 + s2 + s3 + s4, M['track3'], cap_start=True, led='purple'); LM['halfpipe'] = c5 + s1 + s2 + s3 + s4
    # 6 the glass corkscrew (single file: a clear pipe)
    t.w, t.rc = 0.0, 0.09
    gi = t.run(1.2, grade=-0.14, w=0.0, rc=0.095, wh=0.30)
    sweep('pipe_in', gi, M['track3'], led='purple')
    cs = t.run(2 * math.pi * 0.85 * 2, grade=-0.12, turn=720, bank=False)
    sweep('corkscrew', cs, M['glass'], tube_r=0.085); LM['corkscrew'] = cs
    # 7 chute out onto the plinko board
    co = t.run(1.6, grade=-0.25, w=0.0, rc=0.10, wh=0.22); sweep('pipe_out', co, M['track'], led='green')
    top = t.p + Vector((math.cos(t.h), math.sin(t.h), 0)) * -0.25 + Vector((0, 0, -0.24))
    bot, bh, PL = plinko('plinko', tuple(top), math.degrees(t.h), 24, 1.7, 3.6, M['board'], M['peg'], M['wall']); LM['plinko'] = (top, bot, PL)
    # 8 tray under the board's gap, then the three-lane split with speed bumps in the side lanes
    hh = R(bh)
    t.at(bot + Vector((math.cos(hh) * -0.05, math.sin(hh) * -0.05, -0.32)), bh, grade=-0.10); t.w, t.rc, t.wh = 0.40, 0.08, 0.36
    tr8 = t.run(1.5, grade=-0.10, w=0.38, wh=0.26)
    ln = t.run(8.0, grade=-0.10, turn=40, w=0.38)
    lo = t.run(2.0, w=0.16, wh=0.22)
    sweep('lanes', tr8 + ln + lo, M['track2'], cap_start=True, led='green'); LM['lanes'] = ln
    # dividers and bumps inside the lanes
    divs = []
    for sv in (-0.13, 0.13):
        pts_ = [s_['p'] + s_['side'] * sv + s_['up'] * 0.0 for s_ in ln[8:-8]]
        vs_, fs_ = [], []
        for i, (s_, p_) in enumerate(zip(ln[8:-8], pts_)):
            for dv in (-0.012, 0.012):
                vs_.append(tuple(p_ + s_['side'] * dv)); vs_.append(tuple(p_ + s_['side'] * dv + s_['up'] * 0.13))
        for i in range(len(pts_) - 1):
            b0 = 4 * i; b1 = 4 * (i + 1)
            fs_ += [(b0, b1, b1 + 1, b0 + 1), (b0 + 2, b0 + 3, b1 + 3, b1 + 2), (b0 + 1, b1 + 1, b1 + 3, b0 + 3)]
        fs_ += [(0, 1, 3, 2)]
        dv_ = mesh('divider', vs_, fs_, M['wall']); PHYS.append(dv_); divs.append(dv_)
    bumps = []
    for i in range(20, len(ln) - 20, 22):
        s_ = ln[i]
        for lv in (-0.26, 0.26):
            c_ = s_['p'] + s_['side'] * lv
            bp = tube('bump', [tuple(c_ + s_['side'] * -0.11), tuple(c_ + s_['side'] * 0.11)], 0.022, M['peg'], seg=12); PHYS.append(bp); bumps.append(bp)
    LM['divs'] = divs; LM['bumps_l'] = bumps
    # 9 JUMP 2: the big one, off a ramp and over a gap onto a wide tray
    d9 = t.run(3.6, grade=-0.45, w=0.14, wh=0.20, blend=0.5); k9 = t.run(0.8, grade=0.38, blend=0.5)
    sweep('drop2', d9 + k9, M['track'], led='orange'); LM['kick2'] = k9[-1]['p'].copy(); LM['kick2_h'] = t.h
    t.jump(1.0, -1.4); t.g = -0.08
    tr9 = t.run(4.0, grade=-0.06, w=0.45, wh=0.40, blend=0.1); tr9b = t.run(2.0, turn=30, w=0.10, rc=0.25, wh=0.36)
    sweep('land2', tr9 + tr9b, M['track'], cap_start=True, led='orange'); LM['land2'] = tr9[0]['p'].copy()
    # 10 helix round the glowing tower: two and a half laps, banked half-pipe
    Rh = 2.3; hx = t.run(2 * math.pi * Rh * 2.5, grade=-0.075, turn=900)
    sweep('helix', hx, M['track3'], led='blue'); LM['helix'] = hx
    hc = hx[0]['p'] + Vector((math.cos(hx[0]['h'] + math.pi / 2), math.sin(hx[0]['h'] + math.pi / 2), 0)) * Rh
    LM['tower'] = (hc.x, hc.y, hx[-1]['p'].z - 1.0, hx[0]['p'].z + 1.5)
    # 11 out to vortex 2, the giant funnel
    o11 = t.run(4.0, grade=-0.10, turn=-50, w=0.0, rc=0.14, wh=0.24); sweep('to_vortex2', o11, M['track'], led='pink')
    Rf2 = 1.9; hh = t.h; ctr2 = t.p + Vector((math.cos(hh - math.pi / 2), math.sin(hh - math.pi / 2), 0)) * (Rf2 - 0.42)
    ctr2.z = t.p.z - 0.10 - 0.30
    funnel('vortex2', tuple(ctr2), Rf2, 0.085, 1.3, M['funnel']); LM['vortex2'] = ctr2.copy()
    # 12 catch, then the roller waves (they get air off every crest)
    t.at((ctr2.x - 0.35 * math.cos(hh), ctr2.y - 0.35 * math.sin(hh), ctr2.z - 1.3 - 0.55), math.degrees(hh), grade=-0.10)
    t.w, t.rc, t.wh = 0.22, 0.10, 0.34
    c12 = t.run(2.0, grade=-0.12, w=0.20, wh=0.40, turn=-30)
    wv = t.run(10.0, grade=-0.08, wave=(0.11, 1.7), turn=20)
    sweep('rollers', c12 + wv, M['track2'], cap_start=True, led='yellow'); LM['rollers'] = wv
    # 13 JUMP 3 through the ring, then the finish straight
    d13 = t.run(3.4, grade=-0.40, w=0.14, wh=0.20, blend=0.5); k13 = t.run(0.8, grade=0.42, blend=0.5)
    sweep('drop3', d13 + k13, M['track'], led='orange'); LM['kick3'] = k13[-1]['p'].copy(); LM['kick3_h'] = t.h
    t.jump(1.0, -1.3); t.g = -0.05
    fz = t.run(4.0, grade=-0.04, w=0.50, wh=0.40, blend=0.1); LM['land3'] = fz[0]['p'].copy()
    fs = t.run(7.0, grade=-0.02, w=0.40, wh=0.30); fe = t.run(2.4, grade=0.20, w=0.40, blend=1.2)
    sweep('finish', fz + fs + fe, M['finish'], cap_start=True, cap_end=True, led='white'); LM['finish'] = fs
    LM['finish_line'] = fs[int(len(fs) * 0.25)]
    return LM
