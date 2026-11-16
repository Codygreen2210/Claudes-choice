# ================================================================ the one continuous camera: chase the front of the pack, rest on each big feature
if not a.sim:
    SIM = np.load(os.path.join(HERE, 'sim.npz')); SPOS = SIM['pos']; SQUA = SIM['quat']; SPRG = SIM['prog']; PRE = int(SIM['pre'])
    NFR = SPOS.shape[0] - PRE
    TT = np.arange(NFR) / FPS
    def gsmooth(arr, sig_s):
        sig = sig_s * FPS; r = int(sig * 3) + 1; k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
        pad = np.concatenate([np.repeat(arr[:1], r, 0), arr, np.repeat(arr[-1:], r, 0)]); out = np.empty_like(arr)
        for c in range(arr.shape[1]): out[:, c] = np.convolve(pad[:, c], k, 'valid')
        return out
    # focus: the front of the race, weighted toward whoever is close to the lead
    P_ = SPOS[PRE:]; G_ = SPRG[PRE:]
    w_ = np.exp(-(G_.max(axis=1, keepdims=True) - G_) / 1.2); FOC = (P_ * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
    FIN = SIM['fin'] - PRE; T_WIN = FIN.min() / FPS; T_LAST = FIN.max() / FPS
    fl_ = np.array(tuple(LMK['finish_line']['p']))
    after = TT > T_WIN + 0.6; FOC[after] = fl_ + np.array([0, 0, 0.05])          # once the winner crosses, watch the line
    pile = P_[-1].mean(axis=0) + np.array([0, 0, 0.03])
    for i in range(NFR):
        u = smooth(T_LAST + 0.3, T_LAST + 2.5, TT[i])
        if u > 0: FOC[i] = FOC[i] * (1 - u) + pile * u
    FOC = gsmooth(FOC, 0.35)
    VEL = gsmooth(np.gradient(FOC, axis=0) * FPS, 0.9); HD = VEL.copy(); HD[:, 2] = 0
    HD /= np.maximum(np.linalg.norm(HD, axis=1, keepdims=True), 1e-4); HD = gsmooth(HD, 0.6); HD /= np.maximum(np.linalg.norm(HD, axis=1, keepdims=True), 1e-4)
    SDV = np.stack([HD[:, 1], -HD[:, 0], np.zeros(NFR)], 1)        # right-hand side of travel
    UPZ = np.array([0, 0, 1.0])
    def vec(v): return np.array(tuple(v), float)
    def lead_t(name):
        st = PSTART[[p['name'] for p in PIECES].index(name)]; return float(np.argmax(G_.max(axis=1) >= st)) / FPS
    def landmark_side(key, off_side, off_fwd, up, hdg_key=None):
        p = vec(LMK[key]); h = LMK.get(hdg_key or key + '_h', 0.0); fw = np.array([math.cos(h), math.sin(h), 0]); sd = np.array([math.sin(h), -math.cos(h), 0])
        return p + sd * off_side + fw * off_fwd + UPZ * up
    # modes: ('chase', back, up, side, lens) or ('fix', pos, lens) or ('fixlook', pos, look, lens)
    zz = LMK['zigzag']; zmid = np.mean([tuple(s_['p']) for s_ in zz], axis=0); zz_end = vec(zz[-1]['p'])
    tw = LMK['tower']; hx = LMK['helix']; hmid = np.array([tw[0], tw[1], (hx[0]['p'].z + hx[-1]['p'].z) / 2])
    pl_top, pl_bot, PL = LMK['plinko']; pl_mid = (vec(pl_top) + vec(pl_bot)) / 2
    cs = LMK['corkscrew']; cmid = np.mean([tuple(s_['p']) for s_ in cs], axis=0)
    v1 = vec(LMK['vortex1']); v2 = vec(LMK['vortex2'])
    t_zig = lead_t('zigzag'); t_d1 = lead_t('drop1'); t_v1 = lead_t('vortex1'); t_hp = lead_t('halfpipe'); t_cs = lead_t('corkscrew')
    t_pl = lead_t('plinko'); t_ln = lead_t('lanes'); t_d2 = lead_t('drop2'); t_hx = lead_t('helix'); t_tv2 = lead_t('to_vortex2'); t_v2 = lead_t('vortex2')
    t_ro = lead_t('rollers'); t_d3 = lead_t('drop3'); t_fi = lead_t('finish')
    hp_c = vec(LMK['halfpipe'][len(LMK['halfpipe']) // 2]['p'])
    def away(p, c, d, up):            # a point d further from c than p, raised
        v = p - c; v[2] = 0; v /= max(np.linalg.norm(v), 1e-4); return p + v * d + UPZ * up
    CAM_PLAN = [
        (0.0, ('fix', vec(LMK['bumps'][int(len(LMK['bumps']) * 0.75)]['p']) + vec(LMK['bumps'][0]['side']) * 0.95 + UPZ * 0.85, 34)),     # they roll down at us
        (3.2, ('chase', 1.1, 0.75, -0.3, 30)),
        (t_zig + 2.0, ('fix', zmid + np.array([-0.6, -2.6, 2.2]), 30)),                                  # the zigzag laid out below
        (t_zig + 13.0, ('chase', 1.1, 0.8, 0.3, 30)),
        (t_d1 - 2.0, ('fix', landmark_side('kick1', 2.3, 0.7, 0.55), 32)),                               # jump 1, side on
        (t_v1 - 0.2, ('fix', v1 + np.array([-1.9, -2.4, 2.5]), 28)),                                      # down into vortex 1
        (t_hp + 0.8, ('chase', 1.1, 0.9, 0.0, 30)),
        (t_cs - 0.4, ('fix', away(cmid, hp_c, 0.0, 0) + np.array([0, 0, 0.6]) + (np.array([2.3, -2.3, 0.0])), 30)),  # the glass corkscrew
        (t_pl - 0.5, ('fix', pl_mid + np.array(tuple(PL[6])) * 2.8 + np.array(tuple(PL[4])) * 0.5, 30)),  # plinko face-on
        (t_ln + 1.2, ('chase', 1.1, 0.85, 0.2, 30)),
        (t_d2 - 1.6, ('fix', landmark_side('kick2', -2.2, 1.0, 0.45), 32)),                               # the big jump
        (t_hx + 2.5, ('chase', 1.0, 0.55, 0.3, 30)),
        (t_hx + 12.0, ('fixlook', hmid + np.array([0.0, -8.5, 2.2]), hmid + np.array([0, 0, -0.4]), 34)),  # the tower, wide (watch them spiral)
        (t_tv2 - 0.3, ('chase', 1.1, 0.8, 0.0, 30)),
        (t_v2 + 0.2, ('fix', v2 + np.array([2.2, -2.2, 2.3]), 30)),                                       # mega vortex
        (t_ro + 0.8, ('chase', 1.1, 0.8, -0.2, 30)),
        (t_d3 - 1.0, ('fix', landmark_side('kick3', -2.2, 1.3, 0.35), 32)),                               # final jump through the ring
        (t_fi + 1.4, ('fix', vec(LMK['finish_line']['p']) + vec(LMK['finish_line']['side']) * -1.5 + vec(LMK['finish_line']['T']) * 0.7 + UPZ * 1.1, 32)),
    ]
    fe_ = LMK['finish'][-1]; pile_cam = pile - vec(fe_['T']) * 1.1 + vec(fe_['side']) * -0.9 + UPZ * 0.55
    CAM_PLAN.append((T_LAST + 0.6, ('fixlook', pile_cam, pile, 36)))
    BLEND = 1.3
    def cam_of(mode, i):
        k = mode[0]; f_ = FOC[i]
        if k == 'chase':
            _, back, up, side, lens = mode; return f_ - HD[i] * back + UPZ * up + SDV[i] * side, f_ + HD[i] * 0.6 + UPZ * 0.02, lens
        if k == 'fix': return mode[1], f_, mode[2]
        return mode[1], mode[2] + (f_ - mode[2]) * 0.35, mode[3]
    CPOS = np.zeros((NFR, 3)); CTGT = np.zeros((NFR, 3)); CLEN = np.zeros(NFR)
    for i in range(NFR):
        t = TT[i]; j = max(k for k in range(len(CAM_PLAN)) if CAM_PLAN[k][0] <= t)
        p1, q1, l1 = cam_of(CAM_PLAN[j][1], i)
        if j > 0 and t - CAM_PLAN[j][0] < BLEND:
            p0, q0, l0 = cam_of(CAM_PLAN[j - 1][1], i); u = sm((t - CAM_PLAN[j][0]) / BLEND)
            p1 = p0 + (p1 - p0) * u; q1 = q0 + (q1 - q0) * u; l1 = l0 + (l1 - l0) * u
        CPOS[i], CTGT[i], CLEN[i] = p1, q1, l1
    CPOS = gsmooth(CPOS, 0.25); CTGT = gsmooth(CTGT, 0.18)
    # keep a clear line from the marbles to the lens: lift the camera when the track, a sign or a funnel is in the way
    DG = bpy.context.evaluated_depsgraph_get(); SKIP = ('marble', 'core', 'posts', 'rim', 'led', 'mlight')
    def blocked(src, dst):
        d = Vector(tuple(dst - src)); L_ = d.length; d.normalize(); o = Vector(tuple(src)) + d * 0.12; L_ -= 0.12
        for _ in range(12):
            hit, loc, nrm, idx, ob, mw = S.ray_cast(DG, o, d, distance=L_)
            if not hit: return False
            if not ob.name.startswith(SKIP): return True
            step = (loc - o).length + 0.01; o = loc + d * 0.01; L_ -= step
            if L_ <= 0: return False
        return False
    LIFT = np.zeros(NFR)
    for i in range(0, NFR, 2):
        for r_ in np.arange(0, 2.61, 0.15):
            if not blocked(CTGT[i] * 0.3 + FOC[i] * 0.7, CPOS[i] + UPZ * r_): LIFT[i] = r_; break
        else: LIFT[i] = 2.6
        if i + 1 < NFR: LIFT[i + 1] = LIFT[i]
    hw_ = int(FPS * 0.6); LIFT = np.array([LIFT[max(0, i - hw_):i + hw_ + 1].max() for i in range(NFR)]); LIFT = gsmooth(LIFT[:, None], 0.35)[:, 0]
    LIFT_RAW = LIFT
    CPOS = CPOS + UPZ[None, :] * LIFT[:, None]
    print('maxed at', [round(i / FPS, 1) for i in range(0, NFR, 15) if LIFT[i] > 2.5]); print('camera lifted on', int((LIFT > 0.05).sum()), 'of', NFR, 'frames, max', round(float(LIFT.max()), 2))
    CLEN = gsmooth(CLEN[:, None], 0.3)[:, 0]
else:
    NFR = 0
