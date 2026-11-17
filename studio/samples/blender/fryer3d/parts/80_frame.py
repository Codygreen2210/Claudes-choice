# ================================================================ per frame: the story state, then the one continuous camera
RACK0 = 0.80; RACK_BOT = FRY['pot_z'] - DECK_Z + 0.002          # rack-plate heights (fryer local)
OILL0 = 0.532                                                  # oil top (fryer local) before the turkey
def story(t):
    """state numbers at story time t (t < 0 = just before frame one: the loop's run-in)"""
    st = {}
    st['rack'] = RACK0 - (RACK0 - OILL0 + 0.012) / T_TOUCH * t if t < T_TOUCH else lerp(OILL0 - 0.012, RACK_BOT, smooth(T_TOUCH, B[2] + 0.6, t))
    st['oil'] = OILL0 + 0.07 * smooth(T_TOUCH, B[2] + 0.6, t) + (0.752 - 0.6 - 0.07) * smooth(T_SURGE, T_OVER, t) * (1 - smooth(T_BALL + 2.0, T_BALL + 5, t)) * 1.0
    st['frost'] = 1.0 - smooth(T_TOUCH, T_TOUCH + 1.3, t)
    st['boil'] = 0.15 + 0.85 * math.exp(-max(0.0, t - T_TOUCH) * 0.9) * (t > T_TOUCH) + 0.25 * (t > T_TOUCH) + 0.6 * smooth(T_SURGE - 0.3, T_SURGE + 0.4, t)
    st['xr'] = smooth(T_XR0 - 0.3, T_XR0 + 0.4, t) * (1 - smooth(T_XR1 - 0.4, T_XR1 + 0.3, t))
    st['ice'] = 1.0 - 0.6 * smooth(T_MELT - 0.5, T_SINK + 1.5, t)
    st['foam'] = smooth(T_SURGE + 0.2, T_OVER, t) * (1 - smooth(T_BALL + 1.5, T_BALL + 3.5, t))
    st['sheet'] = smooth(T_OVER - 0.2, T_HIT + 0.2, t)
    st['catch'] = smooth(T_CATCH - 0.15, T_CATCH + 0.4, t)
    st['race'] = smooth(T_CATCH + 0.1, T_RACE + 1.0, t)
    st['ball'] = smooth(T_BALL - 0.3, T_BALL + 0.9, t)
    st['roof'] = smooth(T_ROOF - 0.4, T_ROOF + 3.5, t) + 0.25 * smooth(T_ROOF + 3.5, END, t)
    st['let_go'] = smooth(T_SURGE - 0.15, T_SURGE + 0.25, t)
    st['back'] = 0.55 * smooth(T_SURGE - 0.1, T_SURGE + 0.7, t) + 0.9 * smooth(T_BALL - 0.2, T_BALL + 1.2, t)
    return st

def place_drop(d, t, st):
    o = d['o']; r0 = d['r']
    if t < d['t0'] or t > T_SURGE + 1.2 or st['xr'] < 0.02 and t < T_SURGE - 0.5: o.hide_render = True; return
    o.hide_render = False
    c = Vector((FX + d['rr'] * math.cos(d['ang']), FY + d['rr'] * math.sin(d['ang']), 0))
    top = DECK_Z + st['rack'] + 0.09 + 0.16 * h1(d['wob'] * 7); age = t - d['t0']
    z = top - 0.05 * age - 0.06 * age * age; z = max(z, FLOOR_Z + r0 * 0.8)
    c0 = Vector((FX + 0.112 * math.cos(d['ang']), FY + 0.112 * math.sin(d['ang']), 0)); c = c0.lerp(c, min(1.0, age * 1.5))
    shiv = smooth(T_212 - 0.3, T_212 + 0.4, t) * 0.0015
    p = Vector((c.x + shiv * math.sin(t * 61 + d['wob']), c.y + shiv * math.cos(t * 53 + d['wob']), z))
    r = r0 * (1 + 0.15 * shiv * 400 * abs(math.sin(t * 40 + d['wob'])))
    if d is HERO and t > T_POP:
        g = smooth(T_POP, T_POP + 1.0, t); r = lerp(r0, r0 * 12.0, g)                       # 12x wider = ~1,700x the space
        lift = 0.55 * max(0.0, t - (T_1700 + 0.7)) ** 1.6; p.z = FLOOR_Z + r * 0.92 + lift
        if p.z > DECK_Z + st['oil'] - r * 0.5: o.hide_render = True; return
        if o.material_slots[0].material != STEAMB_M: o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = STEAMB_M
    elif t > T_SURGE - 0.1 and d is not HERO:
        g = smooth(T_SURGE - 0.1, T_SURGE + 0.4, t); r = lerp(r0, r0 * 7.0, g); p.z = FLOOR_Z + r + 1.1 * max(0.0, t - T_SURGE - 0.1) ** 1.3
        if o.material_slots[0].material != STEAMB_M: o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = STEAMB_M
        if p.z > DECK_Z + st['oil']: o.hide_render = True; return
    else:
        if o.material_slots[0].link == 'OBJECT': o.material_slots[0].material = WATER_M
    v_ = Vector((p.x - FX, p.y - FY, 0)); lim = PR_ - 0.008 - r
    if v_.length > lim: v_ = v_.normalized() * max(lim, 0.0); p = Vector((FX + v_.x, FY + v_.y, p.z))
    o.location = p; o.scale = (r, r, r * (0.92 if z <= FLOOR_Z + r0 else 1.08))

def state(t):
    st = story(t)
    # turkey + rack + oil
    FRY['rack'].location = (0, 0, st['rack']); TK = FRY['turkey']; TK['frost'] = st['frost']; TK['xr'] = st['xr']
    FRY['pot']['xr'] = st['xr'] * 0.92
    FRY['oiltop'].location = (0, 0, st['oil']); FRY['oiltop']['boil'] = 0.04 + 0.5 * st['boil']; FRY['oiltop']['ph'] = t * 0.7
    body = FRY['oilbody']; body.hide_render = st['xr'] < 0.02; hb = (st['oil'] - (FRY['pot_z'] - DECK_Z + 0.006)); body.scale = (PR_ - 0.006, PR_ - 0.006, hb / 2)
    body.location = (0, 0, FRY['pot_z'] - DECK_Z + 0.006 + hb / 2)
    ice = FRY['ice']; ice.hide_render = st['xr'] < 0.05; s_ = st['ice']; ice.scale = (0.085 * s_, 0.07 * s_, 0.11 * s_)
    # the hook: held, then let go -> it tips onto the rim
    FRY['hook'].rotation_euler = (0, R(-22) * st['let_go'], 0)
    # fizz on the surface
    oz = DECK_Z + st['oil']; bo = st['boil']
    for k, b_ in enumerate(FIZZ):
        on = bo > 0.18 and (k / len(FIZZ)) < bo * 0.9 and t < T_BALL + 2.5
        if not on: b_['o'].hide_render = True; continue
        u = (t * b_['sp'] + b_['ph']) % 1.0; a_ = b_['ang'] + 0.3 * math.sin(t + k)
        b_['o'].hide_render = False; b_['o'].location = (FX + b_['rr'] * math.cos(a_), FY + b_['rr'] * math.sin(a_), oz + 0.002)
        r = b_['r'] * math.sin(math.pi * u) * (0.6 + 0.6 * bo); b_['o'].scale = (r, r, r * 0.6)
    # steam: the flash off the frozen skin, then the boil-over cloud
    STEAM_FLASH.update(t, lambda k, u: (FX + 0.14 * math.cos(k * 2.4), FY + 0.14 * math.sin(k * 2.4), oz + 0.02), T_TOUCH - 0.1, T_TOUCH + 1.6, 2.2, 0.35, 0.16, 0.25, 0.9)
    STEAM_SURGE.update(t, lambda k, u: (FX + 0.1 * math.cos(k * 1.7), FY + 0.1 * math.sin(k * 1.7), DECK_Z + 0.78), T_SURGE, T_CATCH, 2.0, 0.45, 0.24, 0.4, 1.0)
    for d in DROPS: place_drop(d, t, st)
    for b_ in BUBBLES:
        o = b_['o']; age = t - b_['t0']
        if age < 0 or t > T_BALL + 1 or t < T_SURGE - 0.4: o.hide_render = True; continue
        z = FLOOR_Z + b_['r'] + b_['v'] * age ** 1.2
        if z > oz - 0.01: o.hide_render = True; continue
        o.hide_render = False; r = b_['r'] * (1 + 1.5 * min(age, 1.0)); rr = min(b_['rr'], PR_ - 0.008 - r)
        o.location = (FX + rr * math.cos(b_['ang']), FY + rr * math.sin(b_['ang']), z); o.scale = (r, r, r * 1.1)
    # foam dome + the sheet down the outside + the pour onto the burner
    FOAM.hide_render = st['foam'] < 0.02
    if not FOAM.hide_render:
        f_ = st['foam']; FOAM.location = (FX, FY, max(oz - 0.01, RIM_Z - 0.012 * f_)); FOAM.scale = (PR_ + 0.012 + 0.028 * f_, PR_ + 0.012 + 0.028 * f_, 0.02 + 0.13 * f_)   # skirt always covers the lip; FOAM['ph'] = t * 1.5
    SHEET.hide_render = True
    for k, rv in enumerate(RIVS):
        prog = clamp(st['sheet'] * rv['sp'] * 1.15 - 0.1 * rv['w'], 0, 1)
        if prog < 0.02: rv['o'].hide_render = True; continue
        L_ = (PH_ - 0.035) * prog; n_ = max(3, int(24 * prog)); pts = []          # start under the lip, stop above the stand
        for i in range(n_):
            u = i / (n_ - 1); z = RIM_Z - 0.008 - L_ * u; a_ = rv['a'] + 0.05 * math.sin(z * 40 + rv['w'] * 6) + 0.02 * math.sin(z * 97)
            rr = PR_ + 0.002
            pts.append((FX + rr * math.cos(a_), FY + rr * math.sin(a_), z))
        set_tube(rv['o'], pts, lambda u, r0=rv['r']: r0 * min(1.0, 0.15 + u * 7) * (1.2 - 0.5 * u + 0.4 * max(0, u - 0.92) * 10), seg=8)
    for k, sm_ in enumerate(STREAMS):
        if sm_['o'] is None:
            sm_['o'] = tube(f'stream{k}', [(0, 0, 0), (0, 0, -0.5), (0, 0, -1.0)], lambda u: 0.0045 * (1 - 0.5 * u), SHEET_M, seg=8)
        o = sm_['o']; on = t > sm_['t0'] and t < T_BALL + 4.0
        o.hide_render = not on
        if on:
            ln = min(1.0, (t - sm_['t0']) * 2.2) * (FRY['pot_z'] - DECK_Z - 0.02); a_ = sm_['a']
            o.location = (FX + (PR_ + 0.004) * math.cos(a_), FY + (PR_ + 0.004) * math.sin(a_), FRY['pot_z']); o.scale = (1, 1, max(ln, 0.001))
    # burner jets flicker (and in the safe fryer)
    for F_ in (FRY, SAFE):
        for k, j in enumerate(F_['jets']):
            j['ja'] = 0.85 + 0.15 * math.sin(t * 37 + k * 2.1); j.scale = (0.008, 0.008, 0.03 * (0.85 + 0.25 * wob(t, 9, k)))
        F_['burnlight'].data.energy = 16 * (0.85 + 0.15 * wob(t, 7, 1))
    SAFE['oiltop']['boil'] = 0.25; SAFE['oiltop']['ph'] = t * 0.5; SAFE['rack'].location = (0, 0, RACK_BOT); SAFE['oiltop'].location = (0, 0, OILL0 + 0.07)
    # fire
    ca, ra, ba = st['catch'], st['race'], st['ball']
    front = 0.12 + 1.0 * ra                                            # height of the flame front up the pot side (m above the deck)
    for c_ in POT_CARDS + TOP_CARDS: c_.hide_render = True
    for c_, _d in ROOF_CARDS: c_.hide_render = True
    SLEEVE.hide_render = ca < 0.02; SLEEVE['fire'] = ca * (0.6 + 0.4 * ra) + 0.5 * ba; SLEEVE['ph'] = t * 1.1
    SLEEVE['front'] = -1.0 + 2.0 * min(1.0, (front + 0.25 * ba) / 0.96)
    for k, fb in enumerate(FIREBALLS):
        g = ba * (1.0 if k < 2 else st['roof']); fb.hide_render = g < 0.02; fb['fire'] = g; fb['ph'] = t * (0.9 + 0.2 * k)
        if k == 0: fb.location = (FX, FY, RIM_Z + 0.25 + 0.2 * ba); fb.scale = (0.4 + 0.3 * ba, 0.4 + 0.3 * ba, 0.5 + 0.45 * ba)
        elif k == 1: fb.location = (FX, FY - 0.05, RIM_Z + 0.75 + 0.45 * ba); fb.scale = (0.45 + 0.45 * ba, 0.45 + 0.45 * ba, 0.55 + 0.5 * ba)
        elif k == 2: fb.location = (FX, FY - 0.2, ROOF_Z1 + 0.05); fb.scale = (0.6 + 0.9 * st['roof'], 0.6 + 0.5 * st['roof'], 0.28)
        else: fb.location = (FX + 0.4, DY0 - 0.2, ROOF_Z1 + 0.6); fb.scale = (0.5 + 0.6 * st['roof'], 0.4, 0.5 + 0.4 * st['roof'])
    rf = st['roof']
    for o in [ROOF_UNDER] + RAFTERS: o['burnr'] = 1.8 * min(rf, 1.0) + 0.6 * max(rf - 1, 0) - 0.05; o['glow'] = min(1.0, rf * 1.5)
    for c_, dist in ROOF_CARDS:
        amt = smooth(dist - 0.2, dist + 0.3, 1.8 * rf); c_.hide_render = amt < 0.02; c_['amt'] = amt * (0.8 + 0.2 * wob(t, 3, dist)); c_['ph'] = t + c_['seed']
    SMOKE.update(t, lambda k, u: (FX - 1.2 + 2.4 * u, DY0 - 0.35, ROOF_Z1 + 0.3), T_ROOF, END + 3, 4.5, 0.55, 0.9, 0.8, 0.8, (0.08, -0.05, 0))
    flick = 0.75 + 0.25 * wob(t, 6, 2)
    FIRE_L[0].data.energy = (25 * ca + 90 * ra + 320 * ba) * flick; FIRE_L[0].location = (FX, FY - 0.25, DECK_Z + 0.4 + 0.5 * ra + 0.6 * ba)
    FIRE_L[1].data.energy = 450 * ba * flick; FIRE_L[1].location = (FX, FY - 0.3, RIM_Z + 0.9)
    FIRE_L[2].data.energy = 380 * min(rf, 1.0) * flick; FIRE_L[2].location = (FX, FY - 0.5, ROOF_Z1 - 0.2)
    # the man: hands on the T-handle while he lowers it; lets go, flinches back, backs away arms up
    lg = st['let_go']; bk = st['back']
    MAN.location = (-0.98 - bk, 1.08 + 0.15 * smooth(T_BALL, T_BALL + 1.2, t), DECK_Z)
    bpy.context.view_layer.update()
    hk = FRY['hook'].matrix_world
    want = {}
    for s_, dy in (('R', -0.06), ('L', 0.06)):
        bar = hk @ Vector((-0.44, dy, 0.11))
        tgt = grip(s_, bar, 1.0 - lg)
        want[s_] = bar + Vector((0, 0, 0.026))                          # knuckle line just over the bar
        up = man_world((0.3 if s_ == 'L' else -0.3, -0.42, 1.62))     # arms up in front of the face
        TG['h' + s_].location = tgt.lerp(up, lg)
        TG['p' + s_].location = man_world((0.75 if s_ == 'L' else -0.75, 0.25, 1.0))
        fingers(s_, 1.0 - 0.8 * lg)
    stepb = smooth(T_SURGE - 0.1, T_SURGE + 0.5, t) * (1 - smooth(T_SURGE + 0.5, T_SURGE + 1.0, t)) + smooth(T_BALL - 0.2, T_BALL + 0.4, t) * (1 - smooth(T_BALL + 0.4, T_BALL + 1.0, t))
    man_pose(spine=18 * (1 - lg) - 14 * lg, neck=15 * (1 - lg) - 10 * lg, head=12 * (1 - lg) - 6 * lg, head_yaw=-25 * smooth(T_BALL + 1, T_BALL + 2, t),
         legs={'upperleg01.R': (R(28 * stepb), 0, 0), 'lowerleg01.R': (R(35 * stepb), 0, 0), 'upperleg01.L': (R(-8 * stepb), 0, 0)})
    grip_fix(want, 1.0 - lg)

# ---- camera: (time, position, target, lens); rests on each beat, one unbroken move
POT_C = Vector((FX, FY, 0)); ZR = RIM_Z
def potp(dx, dy, z): return (FX + dx, FY + dy, z)
K = [
    (0.0, potp(0.60, -0.78, ZR + 0.22), potp(-0.02, 0.0, ZR + 0.04), 32),
    (T_TOUCH + 0.3, potp(0.52, -0.64, ZR + 0.14), potp(-0.02, 0.0, ZR - 0.06), 34),
    (B[2] - 0.2, potp(0.48, -0.60, ZR + 0.10), potp(-0.02, 0.0, ZR - 0.10), 34),
    (B[2] + 1.2, potp(0.30, -0.62, ZR - 0.16), potp(0.0, 0.0, ZR - 0.22), 36),          # into the meat (x-ray): the ice core
    (B[3] - 0.4, potp(0.30, -0.60, ZR - 0.18), potp(0.0, 0.0, ZR - 0.24), 36),
    (B[3] + 1.0, potp(0.24, -0.62, ZR - 0.28), potp(0.0, -0.03, ZR - 0.30), 34),        # the melt water running out
    (B[4] - 0.3, potp(0.24, -0.62, ZR - 0.29), potp(0.0, -0.03, ZR - 0.31), 34),
    (B[4] + 1.0, potp(0.22, -0.60, ZR - 0.34), potp(0.0, -0.06, ZR - 0.38), 34),        # sinking to the floor
    (B[5] - 0.3, potp(0.22, -0.60, ZR - 0.35), potp(0.0, -0.06, ZR - 0.39), 34),
    (B[5] + 1.0, potp(0.24, -0.62, ZR - 0.50), potp(0.0, -0.06, ZR - 0.44), 34),        # under: the flame right below the floor
    (B[6] - 0.3, potp(0.24, -0.62, ZR - 0.50), potp(0.0, -0.06, ZR - 0.44), 34),
    (T_POP + 0.2, potp(0.10, -0.42, ZR - 0.37), potp(0.112 * math.cos(-1.75), 0.112 * math.sin(-1.75), ZR - 0.38), 40),     # the bubble
    (B[7] - 0.2, potp(0.12, -0.46, ZR - 0.34), potp(0.08, -0.08, ZR - 0.34), 40),
    (T_OVER - 0.2, potp(0.62, -0.78, ZR + 0.22), potp(0.0, 0.0, ZR - 0.02), 30),        # out: foaming over the top
    (B[8] + 0.2, potp(0.62, -0.78, ZR + 0.18), potp(0.0, 0.0, ZR - 0.08), 30),
    (T_HIT + 0.3, potp(0.55, -0.62, DECK_Z + 0.30), potp(0.0, 0.0, DECK_Z + 0.28), 30),  # down the side to the burner
    (T_CATCH + 0.2, potp(0.55, -0.62, DECK_Z + 0.30), potp(0.0, 0.0, DECK_Z + 0.30), 30),
    (T_RACE + 1.0, potp(0.85, -0.95, ZR + 0.15), potp(0.0, 0.0, ZR - 0.05), 28),        # up with the flames
    (T_BALL + 1.6, (1.7, -2.1, 2.25), (0.0, 1.15, 1.55), 26),                            # wide: the fireball and the roof, over the railing
    (B[11] + 0.4, (1.85, -2.4, 2.3), (0.0, 1.2, 1.6), 26),
    (B[12] - 0.3, (2.0, -2.7, 2.35), (0.0, 1.2, 1.65), 26),
    (T_SAFE + 1.6, (2.75, -6.55, 1.05), (3.6, -8.6, 0.62), 32),                          # out on the lawn: the right way
    (B[13] + 0.9, (2.8, -6.6, 1.02), (3.6, -8.6, 0.6), 32),
    (END - 0.75, (1.15, -1.35, 1.82), (0.0, 1.05, 1.25), 30),                           # over the railing on the way back in
    (END, None, None, 32),
]
K[-1] = (END, K[0][1], K[0][2], K[0][3])
KT = [k[0] for k in K]
def cam_at(t):
    i = max(j for j in range(len(K)) if KT[j] <= t) if t < END else len(K) - 2
    i = min(i, len(K) - 2); a_, b_ = K[i], K[i + 1]; u = sm(clamp((t - a_[0]) / max(b_[0] - a_[0], 1e-6), 0, 1))
    p = Vector(a_[1]).lerp(Vector(b_[1]), u); q = Vector(a_[2]).lerp(Vector(b_[2]), u); ln = lerp(a_[3], b_[3], u)
    return p, q, ln
def frame(f):
    t = f / FPS; tt = t if t < T_RESET else t - END
    state(tt)
    cp, ct, ln = cam_at(t)
    look(cp + shake(t, 0.004, 1.3, 1.1) * (1 + 2.5 * smooth(T_BALL - 0.2, T_BALL + 0.6, t) * (1 - smooth(T_BALL + 1.5, T_BALL + 3, t))), ct, ln, fstop=16.0)
    bloom(0.35 + 0.35 * smooth(T_CATCH, T_BALL, t) * (t < T_RESET), 1.1)
