# ================================================================ MODES and the story
MAN = [BODY, SUIT, HAIR] + HEADBITS
OUTDOOR = [GROUND, TUFTS, SKY, WALLCLOUD, FUNNEL, FUN2, DUSTC, NEAR.o, FAR.o] + FENCE + POLES + TREES + TRAILER + OUT_L
def mode(which):
    for o in OUTDOOR + CLOSET + MAPSET + [STREAMS]: o.hide_render = True
    for o in MAN: o.hide_render = which == 'map'
    if which in ('out', 'map'):
        for o in OUTDOOR: o.hide_render = False
    if which == 'map':
        for o in MAPSET: o.hide_render = False
        NEAR.o.hide_render = True
    if which == 'closet':
        for o in CLOSET: o.hide_render = False
    WBG.inputs['Color'].default_value = (0.04, 0.05, 0.045, 1) if which != 'closet' else (0.0, 0.0, 0.0, 1)
def storm(t, tc, near_c=None, near_slow=1.0, far_slow=1.0, near_r=(1.2, 5.0), dens=1.0, wind=1.0):
    for o in (FUNNEL, FUN2, DUSTC): o.location = tc; o['tt'] = t
    FUNNEL['dens'] = dens; FUN2['dens'] = 0.45 * dens; DUSTC['dens'] = 0.8 * dens; SKY['tt'] = t; WALLCLOUD.location = tc + V3(0, 0, 560)
    FAR.swirl(tc + V3(0, 0, 1), t, 18, 70, 140, 0.55, far_slow, lift=6.0)
    if near_c is not None: NEAR.o.hide_render = False; NEAR.swirl(near_c - V3(0, 0, 2.5), t, near_r[0], near_r[1], 6.0, 1.6, near_slow, lift=1.2)
    else: NEAR.o.hide_render = True
    TUFTS.data.shape_keys.key_blocks['wind'].value = clamp(wind * (0.6 + 0.4 * wob(t, 3, 2)), 0, 1)
M0 = V3(2.6, -4.6, 0.0); YAW0 = 0.0
BRACE_T = dict(ankR=V3(-0.14, 0.02, 0.09), ankL=V3(0.14, 0.02, 0.09), handR=V3(-0.1, -0.32, 1.62), handL=V3(0.12, -0.33, 1.6))
def lift_off(v, t):
    """0..1: off his feet and tumbling up (B0); v<0 = still braced, rising onto his toes (end of B11, the loop)"""
    k = smooth(0.08, 0.45, v); up = 0.05 + 7.5 * smooth(0.0, 1.0, v) ** 1.5
    hip = M0 + V3(0.0, 4.0 * smooth(0.1, 1.0, v), STAND_HIP + up); rot = (6 + lerp(0, -75, smooth(0.1, 1.0, v)) + 20 * wob(t, 1.5, 4) * k, 25 * wob(t, 1.1, 5) * k, YAW0 + 120 * smooth(0.15, 1.0, v) ** 1.3)
    f = flail(t, 1.0, 2.0); tg = {n: BRACE_T[n].lerp(f[n], k) for n in f}
    feet_flat(False); body(hip, rot, tg['ankR'], tg['ankL'], tg['handR'], tg['handL'], neck=8 + 10 * k, jaw=0.3 + 0.4 * k, lids=0.5 + 0.2 * k, curl=(0.8 - 0.3 * k,) * 2, pk=(1 - 2 * k, 1 - 2 * k))
    return hip
def cam_b0(v):
    return M0 + V3(1.3, -3.1, 0.45).lerp(V3(2.2, -5.0, 0.3), smooth(0, 1, v)), M0 + V3(-0.1, 0.4, 1.35).lerp(V3(0.0, 3.5, 5.5), smooth(0, 1, v)), lerp(22, 20, v)
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    S.view_settings.exposure = 0.0; FLASH.data.energy = 0.0
    if nb == 0:                                             # he is ripped off the ground: rising, tumbling, junk all around him
        mode('out'); hip = lift_off(u, t); storm(t, V3(4, 34, 0), near_c=hip, dens=1.0)
        cp, ct, ln = cam_b0(u); look(cp + shake(t, 0.05), ct.lerp(hip + V3(0, 0, 0.2), 0.6 + 0.35 * smooth(0.3, 1.0, u)), ln, 4.0, focus=hip)
    elif nb == 1:                                           # the inflow: air spiralling in along the ground, faster as it squeezes in
        mode('out'); STREAMS.hide_render = False; STREAMS['tt'] = t; STREAMS['reach'] = 120 + 700 * smooth(0.0, 1.0, u); storm(t, TC0, dens=0.9)
        a_ = lerp(-0.9, -0.55, u); cp = TC0 + V3(520 * math.sin(a_), -520 * math.cos(a_), 150); look(cp, TC0 + V3(0, 0, 70), 30, 16.0)
        FUNNEL['dens'] = 0.75
    elif nb == 2:                                           # up the middle: inside the funnel looking up, he goes up with it
        mode('out'); tc = V3(0, 0, 0) + M0
        hip = M0 + V3(0, 0, 14 + 22 * u); airborne(hip, (-40 + 90 * u, 20, 180 + 200 * u), t, 1.0, 3.0); storm(t, tc, near_c=hip, dens=1.0, near_r=(2, 9))
        look(hip + V3(1.2, -2.2, -6.0), hip + V3(0, 0, 1.5), 22, 8.0, focus=hip); S.view_settings.exposure = 0.4
    elif nb == 3:                                           # over 200 mph: the whole tornado, junk orbiting it
        mode('out'); storm(t, TC0, dens=1.0); look(TC0 + V3(-230, -300, 8).lerp(V3(-190, -250, 12), u) + shake(t, 0.4), TC0 + V3(0, 0, 110), 26, 16.0)
    elif nb in (4, 5, 6):                                   # slow motion up in it: him tumbling, boards / glass / rocks going past
        mode('out'); slow = 0.25; ts = B[4] + (t - B[4]) * slow
        hip = M0 + V3(0, 4, 10 + 2.0 * (t - B[4]) * slow); airborne(hip, (-80 + 40 * (t - B[4]) * slow, 15, 300 + 70 * (t - B[4]) * slow), ts, 1.0, 2.0)
        storm(ts, V3(4, 34, 0), near_c=hip, near_slow=1.0, dens=1.0, near_r=(0.9, 4.0))
        if nb == 4: a_ = 0.4 + 0.5 * u; look(hip + V3(3.8 * math.sin(a_), -3.8 * math.cos(a_), -0.8), hip + V3(0, 0, 0.1), 32, 5.6, focus=hip)
        elif nb == 5: a_ = 0.9 + 0.7 * u; look(hip + V3(2.6 * math.sin(a_), -2.6 * math.cos(a_), 0.3 - 0.6 * u), hip, 28, 4.0, focus=hip)
        else:                                               # a board comes straight at the camera and just misses
            NEAR_B = 0; ang = np.zeros((NEAR.n, 3)); P = NEAR.swirl(hip - V3(0, 0, 2.5), ts, 0.9, 4.0, 6.0, 1.6, 1.0, lift=1.2)
            cp = hip + V3(0.6, -3.6, 0.2); P[0] = np.array(hip + V3(2.5, 3.0, 0.4)).copy() * 0 + np.array((hip + V3(4.0, 6.0, 0.3)).lerp(cp + V3(0.35, -0.6, 0.15), smooth(0.05, 0.75, u)))
            angs = NEAR.spin * ts; angs[0] = (0.3, 0.2, R(60) + 3.0 * u); NEAR.set(P, angs)
            look(cp, hip + V3(0, 0, 0.1), 30, 4.0, focus=hip)
    elif nb == 7:                                           # 2006: pulled out through the trailer's door
        mode('out'); S.view_settings.exposure = -0.9; FLASH.data.energy = 2.5e6 * max(0.0, 1 - abs(u - 0.3) * 14) + 1.2e6 * max(0.0, 1 - abs(u - 0.38) * 20)
        for o in TRAILER: o.hide_render = False
        v = smooth(0.25, 1.0, u); door = V3(0.4, -TRW / 2 - 0.4, 0)
        hip = door + V3(0, -0.3 - 9 * v, 1.0 + 6 * v ** 1.4); airborne(hip, (-60 * v, 10, 200 + 160 * v), t, 0.4 + 0.6 * v, 5.0)
        storm(t, V3(0, 42, 0), near_c=hip if v > 0.05 else None, dens=1.0)
        look(door + V3(-4.0, -6.5, 1.2).lerp(V3(-4.5, -8.5, 1.6), u), (door + V3(0, -1, 1.6)).lerp(hip, 0.7), 24, 6.0, focus=hip)
    elif nb == 8:                                           # carried 1,307 ft: the map, the path draws itself, a light rides it
        mode('map'); v = smooth(0.05, 0.9, u); PATH['reach'] = PATH_ARC[-1] * v; DOT.location = path_at(v) + V3(0, 0, 3)
        storm(t, TR + V3(-40, -90, 0) + (LAND - TR) * (0.3 + 0.7 * v), dens=0.6); NEAR.o.hide_render = True
        for o in (FUNNEL, FUN2, DUSTC, FAR.o): o.hide_render = True
        WALLCLOUD.hide_render = SKY.hide_render = True; mid = TR.lerp(LAND, 0.5); look(mid + V3(-40, -300, 520), mid, 34, 64.0)
    elif nb == 9:                                           # he lands in a field and comes to
        mode('out'); FUNNEL.hide_render = FUN2.hide_render = DUSTC.hide_render = True; NEAR.o.hide_render = FAR.o.hide_render = True
        lying(LAND.x, LAND.y, smooth(0.35, 1.0, u), t); TUFTS.location = LAND - V3(0, 0, 0)
        hd = RIG.matrix_world @ V3(0, 0, 1.4); look(hd + V3(1.8, -1.3, 0.45).lerp(V3(1.5, -1.0, 0.65), u), hd.lerp(RIG.matrix_world @ HIP0, 0.4), 30, 4.0, focus=hd)
        SKY['tt'] = t
    elif nb == 10:                                          # the lowest room, no windows, hands over his head
        mode('closet'); S.view_settings.exposure = 0.8; crouch(t, 1.0); BULB.rotation_euler = (R(18) * math.sin(t * 3.1), R(10) * math.sin(t * 2.3 + 1), 0)
        hd = RIG.matrix_world @ V3(0, 0.05, 1.55); look(CL + V3(0.62, -0.72, 1.55) + shake(t, 0.012), hd.lerp(CL + V3(0, 0, 0.6), 0.4), 18, 4.0, focus=hd)
    else:                                                   # back outside: the wind picks up, then his heels come up (= frame one)
        mode('out'); wind = smooth(0.0, 0.8, u)
        tc = V3(4, 34, 0).lerp(V3(4, 34, 0), 1.0) + V3(-25 * (1 - u), 20 * (1 - u), 0)
        if u < 0.72: stand(M0.x, M0.y, YAW0, t, brace=smooth(0.2, 0.6, u)); hip = RIG.matrix_world @ HIP0
        else: hip = lift_off(lerp(-0.0, 0.0, u), t) if False else lift_off(0.0, t)
        storm(t, tc, near_c=hip if u > 0.5 else None, dens=1.0, wind=wind)
        cp0, ct0, ln0 = cam_b0(0.0); k = smooth(0.0, 0.9, u)
        look(cp0 + V3(-0.6, -1.5, 0.4) * (1 - k) + shake(t, 0.02 + 0.03 * k), (M0 + V3(-0.5, 1.5, 1.6)).lerp(ct0, k), lerp(26, ln0, k), 4.0, focus=hip)

