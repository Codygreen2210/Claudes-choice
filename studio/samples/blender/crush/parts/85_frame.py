# ================================================================ MODES and the story
MAN = [BODY, SUIT, HAIR] + HEADBITS
HEAD_W = deform(V3(0, -0.02, 1.62), 'head')
# bricks round his head and shoulder that the rescuers pull away (B2): stacked on the floor pile, never on him
DIG = []; _dg = random.Random(33)
for k in range(9):
    for _ in range(40):
        x = HEAD_W.x + _dg.uniform(-0.55, 0.55); y = HEAD_W.y + _dg.uniform(-0.2, 0.55)
        if not on_body(x, y, 0.13): break
    o = box('dig%d' % k, (0.2, 0.095, 0.06), V3(x, y, 0.03 + 0.065 * (k % 3)), LOOSE_BRICK_M, 0.006, rot=(0, 0, R(_dg.uniform(0, 180)))); o['p0'] = o.location.copy(); o['s'] = 0.15 + 0.22 * k; DIG.append(o)
INBEAMS = []
for i in range(3):
    o = prim('cone', 'inbeam%d' % i, BEAMS_M, radius1=0.9, radius2=0.03, depth=7.0, vertices=24); o.visible_shadow = False; o['on'] = 0.0; o.rotation_mode = 'QUATERNION'; o.hide_render = True
    INBEAMS.append(o)
STORESET = list(dict.fromkeys(STORE + CEIL_TILES + FALLERS + [GRIT] + PINNED_SET + [REBAR] + IV + DIG))
EMIS_STR = {m_: m_.node_tree.nodes['Emission'].inputs['Strength'] for m_ in (TUBE_GLOW, FRIDGE_GLOW, STORE[7].data.materials[0], BAR_R, BAR_W, DRONE_RED, DRONE_GRN)}
def glow(m_, v): EMIS_STR[m_].default_value = v
STREET_GLASS = STORE[7].data.materials[0]
def show(objs, on):
    for o in objs: o.hide_render = not on
def mode(which):
    """store | fall | pinned | xray | dusk | night"""
    inside = which in ('store', 'fall', 'pinned', 'xray')
    show(OUTSET, not inside); show(STORESET, inside and which != 'xray'); show(MAN, which != 'dusk' and which != 'night'); show(DUST, False)
    show(XRAY, False); show(IV, False); show(INBEAMS, False)
    if inside:
        before = which in ('store', 'fall')
        show(FALLERS + [GRIT], before); show(CEIL_TILES, True); show(PINNED_SET + DIG, which == 'pinned'); REBAR.hide_render = which != 'pinned'
        for o in DROP_TILES: o.hide_render = not before
        glow(TUBE_GLOW, 4.5 if before else 0.0); glow(FRIDGE_GLOW, 4.0 if before else 0.25); glow(STREET_GLASS, 1.4 if before else 0.35)
        for o in STORE_L: o.data.energy = (90 if o.name == 'store_fill' else 40) if before else (18 if o.name == 'store_fill' else 6)
        GAP_L.data.energy = 0.0 if before else 260.0
        for o in TORCH_L: o.data.energy = 0.0
        WBG.inputs['Color'].default_value = (0, 0, 0, 1); SUN_O.hide_render = True
    xray(which == 'xray')
    if which in ('pinned', 'xray'):
        fall(6.0); BEAM.matrix_world = BEAM0; BEAM.hide_render = False; ABOVE.hide_render = True
        for o in DIG: o.location = Vector(o['p0']); o.rotation_euler.x = 0.0
    if which == 'xray':
        show(XRAY, True); BEAM.hide_render = False; WBG.inputs['Color'].default_value = (0.0, 0.0, 0.004, 1)
    if which == 'dusk':
        WBG.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1); SKYBG.inputs['Strength'].default_value = 0.35; SUN_O.hide_render = False
        for o in STREETL: o.data.energy = 0.0
        show(OUT_GEAR, False); c_intact()
    elif which == 'night':
        WBG.inputs['Color'].default_value = (0.012, 0.016, 0.03, 1); WBG.inputs['Strength'].default_value = 1.0; SUN_O.hide_render = True
        for o in STREETL: o.data.energy = 900.0
        show(OUT_GEAR, True); c_rest()
        for o in TOWER_L: o.data.energy = 3500.0
    else: WBG.inputs['Strength'].default_value = 1.0
    if which != 'dusk': SKYBG.inputs['Strength'].default_value = 0.0
def night_fx(t):
    """flashing truck lights, blinking drone, flashlight beams sweeping the pile"""
    fl = 1.0 if (t * 2.6) % 1.0 < 0.5 else 0.0
    glow(BAR_R, 40 * fl); glow(BAR_W, 40 * (1 - fl)); TRUCK_L[0].data.energy = 1500 * fl; TRUCK_L[1].data.energy = 1200 * (1 - fl)
    bl = 1.0 if (t * 1.3) % 1.0 < 0.15 else 0.0; glow(DRONE_RED, 30 * bl); glow(DRONE_GRN, 30 * bl)
    srcs = [V3(8.0, 1.0, 0.8), V3(11.0, 0.2, 0.9), V3(16.5, 1.2, 0.6), V3(7.6, 9.0, -1.5), V3(14.0, 13.5, -1.0)]
    for i, o in enumerate(TBEAMS):
        a_ = t * (0.5 + 0.13 * i) + i * 1.7
        dst = V3(11.0 + 3.5 * math.sin(a_), 7.0 + 4.0 * math.cos(a_ * 0.8), -2.5 + 0.8 * math.sin(a_ * 1.3))
        torch(o, X0 + srcs[i], X0 + dst, 0.9)
def drone_at(p, t):
    DRONE[0].location = p + V3(0.05 * wob(t, 0.7, 1), 0.05 * wob(t, 0.7, 2), 0.06 * wob(t, 0.9, 3)); DRONE[0].rotation_euler = (R(3 * wob(t, 1, 4)), R(3 * wob(t, 1, 5)), R(20))
    DRONE_SPOT.data.energy = 120.0
    for o in DRONE:
        if o.name.startswith('drone_rot'): o.rotation_euler = (0, 0, t * 120.0)
def store_lights_flicker(t, k):
    """the power failing as the ceiling comes down (k 0..1)"""
    fl = 1.0 - k * (0.5 + 0.5 * (1 if math.sin(t * 47.0) * math.sin(t * 13.0) > 0.1 else 0))
    glow(TUBE_GLOW, 4.5 * max(fl, 0.05))
def cam_b0(u):
    return M0 + V3(0.55, -2.25, 0.55).lerp(V3(0.45, -1.9, 0.5), u), M0 + V3(0.0, 0.0, 2.05).lerp(V3(0.0, 0.1, 2.25), u), 17.0
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    S.view_settings.exposure = 0.0
    for o in DUST: o['dens'] = 0.0
    if nb in (0, 12):                                       # the store: before and as the ceiling comes down (B12 runs into B0)
        cc = t if nb == 0 else t - TOTAL
        mode('fall' if cc > -1.2 else 'store'); fall(cc); grit(cc, 1.0)
        if cc > -1.2: store_lights_flicker(t, smooth(-1.2, 0.8, cc))
        look_up = 1.0 if nb == 0 else smooth(-1.4, -0.5, cc); brace = smooth(0.15, 1.1, cc) if nb == 0 else 0.0
        yaw = 0.0 if nb == 0 else lerp(70, 0, smooth(-2.4, -1.5, cc))
        stand(t, look_up, brace, yaw)
        show(DUST, True); dust(t, 0.35 * smooth(-0.8, 1.2, cc), M0 + V3(0, 0.6, 1.4), CAM.location, 1.0)
        if nb == 0:
            cp, ct, ln = cam_b0(u); look(cp + shake(t, 0.035 * smooth(-0.5, 0.5, cc)), ct, ln, 5.6, focus=M0 + V3(0, 0, 1.6))
        else:
            k = smooth(0.0, 1.0, u); cp0, ct0, ln0 = cam_b0(0.0)
            cp = (M0 + V3(1.4, -3.4, 1.55)).lerp(cp0, sm(k)); ct = (M0 + V3(-0.4, 0.4, 1.2)).lerp(ct0, sm(smooth(0.35, 1.0, u)))
            look(cp + shake(t, 0.02 * smooth(-1.0, 0.0, cc)), ct, lerp(28, ln0, sm(k)), 5.6, focus=M0 + V3(0, 0, 1.5))
    elif nb in (1, 2, 4, 9):                                # pinned in the dark
        mode('pinned'); pinned(t, wince=0.6 if nb != 9 else 0.4, look=0.35 if nb == 1 else 0.1)
        hd = deform(V3(0, -0.02, 1.62), 'head'); legs = V3(M0.x, M0.y - 0.6, 0.25)
        show(DUST, True); dust(t, 0.25, M0 + V3(0, -0.2, 1.0), CAM.location, 0.8, rise=0.02)
        if nb == 1:                                         # high and to the side: him, the beam, the pile on his legs
            cp = M0 + V3(0.95, -1.75, 2.15).lerp(V3(0.85, -1.5, 1.95), u); look(cp + shake(t, 0.01), M0 + V3(-0.05, 0.3, 0.15), 19, 8.0, focus=M0 + V3(0, 0.1, 0.2))
            GAP_L.data.energy = 900 * (0.8 + 0.2 * wob(t, 2, 1)); S.view_settings.exposure = 0.5
        elif nb == 2:                                       # light breaks in from above; bricks round his head are pulled away
            for o in DIG:
                k = smooth(o['s'], o['s'] + 0.5, u * 2.4); o.location = Vector(o['p0']) + V3(-0.9 * k, -0.2 * k, 2.2 * k * k); o.rotation_euler.x = 1.5 * k
            GAP_L.data.energy = 400 + 2600 * smooth(0.0, 0.9, u); S.view_settings.exposure = 0.5
            for i, o in enumerate(TORCH_L):
                a_ = t * 1.3 + i * 2.1; o.location = M0 + V3(0.5 * math.sin(a_), 0.6 + 0.4 * math.cos(a_), 3.6)
                tg = hd + V3(0.3 * math.sin(a_ * 1.7), 0.3 * math.cos(a_), 0); on = smooth(0.1 + 0.15 * i, 0.4 + 0.15 * i, u)
                o.rotation_quaternion = (tg - o.location).to_track_quat('-Z', 'Y'); o.data.energy = 260 * on
                INBEAMS[i].hide_render = False; torch(INBEAMS[i], o.location, tg, 1.4 * on)
            look(hd + V3(0.62, 0.32, 0.12), hd + V3(-0.35, -0.25, 0.85), 16, 4.0, focus=hd)
        elif nb == 4:                                       # the warning: slow push from his face down to the beam on his legs
            k = sm(u); cp = (hd + V3(0.75, -0.2, 0.55)).lerp(V3(M0.x + 0.75, M0.y - 0.55, 0.75), k)
            look(cp, hd.lerp(V3(M0.x, BEAM_Y, 0.35), smooth(0.1, 0.8, u)), 24, 5.0, focus=hd.lerp(V3(M0.x, BEAM_Y, 0.3), k))
            GAP_L.data.energy = 600; S.view_settings.exposure = 0.3 - 0.4 * smooth(0.4, 1.0, u)
        else:                                               # the IV goes in before the lift; drops fall in the chamber, fluid runs down
            show(IV, True); IV_LINE['ph'] = t * 6.0; IV_LINE['glow'] = 0.9
            dk = (t * 2.2) % 1.0; IV_DROP.location = IV_BAG - V3(0, 0, 0.135 + 0.04 * dk * dk)
            for i, o in enumerate(TORCH_L[:1]): o.location = IV_BAG + V3(0.6, -0.6, 1.2); o.rotation_quaternion = (IV_BAG - o.location).to_track_quat('-Z', 'Y'); o.data.energy = 120
            GAP_L.data.energy = 600
            arm = Vector(wpos('lowerarm02.R')); look(arm + V3(0.95, -1.15, 0.75).lerp(V3(0.85, -1.0, 0.85), u), arm.lerp(IV_BAG, 0.5), 22, 5.6, focus=arm.lerp(IV_BAG, 0.3))
            if u > 0.8: BEAM.matrix_world = Matrix.Translation(V3(0, 0, 0.06 * smooth(0.8, 1.0, u))) @ BEAM0
            else: BEAM.matrix_world = BEAM0
    elif nb in (5, 6, 7, 8):                                # x-ray: crush syndrome
        mode('xray'); pinned(t, wince=0.5); BODY['tt'] = t
        for v_ in VEINS.values(): v_[0]['ph'] = t * 4.0; v_[0]['glow'] = 0.6
        CAVA[0]['ph'] = t * 4.0; CAVA[0]['glow'] = 0.6; HEART['kk'] = 0.0; HEART['flash'] = 0.0
        bt = (t * 1.2) % 1.0; hb = 0.06 * math.exp(-((bt - 0.1) / 0.06) ** 2)
        legc = V3(M0.x, M0.y - 0.45, 0.2)
        if nb == 5:
            BODY['crush'] = 0.25 + 0.75 * smooth(0.0, 0.9, u); specks(t, 0.45 * smooth(0.2, 1.0, u), size=0.011); BEAM.matrix_world = BEAM0
            look(legc + V3(1.15, -1.25, 0.95).lerp(V3(0.95, -1.05, 0.8), u), legc + V3(0, 0.1, 0.05), 22, 8.0, focus=legc)
        elif nb == 6:
            BODY['crush'] = 1.0; specks(t, 0.45 + 0.55 * smooth(0.0, 0.85, u), size=0.012); BEAM.matrix_world = BEAM0
            th = V3(M0.x, M0.y - 0.45, 0.14); look(th + V3(0.45, -0.75, 0.38).lerp(V3(0.38, -0.62, 0.32), u), th + V3(0, 0.1, 0), 26, 4.0, focus=th)
        elif nb == 7:                                       # the weight comes off: the beam lifts away, the specks race up to the heart
            BODY['crush'] = 1.0 - 0.5 * smooth(0.2, 1.0, u)
            lift = smooth(0.0, 0.35, u); BEAM.matrix_world = Matrix.Translation(V3(0.25 * lift, 0, 0.9 * lift)) @ BEAM0
            run = lt - 0.25; specks(t, 1.0, run if run > 0 else -1.0, 0.012)
            for v_ in list(VEINS.values()) + [CAVA]: v_[0]['glow'] = 0.6 + 1.6 * smooth(0.15, 0.4, u); v_[0]['ph'] = t * 14.0
            mid = V3(M0.x, M0.y + 0.1, 0.18); look(mid + V3(0.6, -1.0, 1.25).lerp(V3(0.65, -0.1, 1.3), sm(u)), mid + V3(0, 0.35 * u, 0), 24, 11.0, focus=mid)
            HEART['kk'] = smooth(0.6, 1.0, u)
        else:                                               # the heart can't keep a beat: it flutters and stutters
            BEAM.hide_render = True; specks(t, 1.0, 3.0 + lt, 0.012)
            seq = [0.0, 0.18, 0.31, 0.62, 0.7, 0.78, 1.05, 1.5, 1.58, 2.2, 2.32, 2.4, 2.9, 3.05]
            hb = sum(0.09 * math.exp(-((lt - s_) / 0.045) ** 2) for s_ in seq) if lt < 2.6 else 0.02 * math.sin(lt * 40) * (1 - smooth(2.6, 3.4, lt))
            HEART['kk'] = 1.0; HEART['flash'] = 3.0 * hb / 0.09
            look(HEART_C + V3(0.42, -0.32, 0.3).lerp(V3(0.3, -0.22, 0.22), u) + shake(t, 0.004), HEART_C, 30, 4.0, focus=HEART_C)
            S.view_settings.exposure = 0.0
        HEART.scale = Vector((1.0, 1.0, 1.0)) * (1.0 + 2.2 * hb)
    elif nb == 10:                                          # outside, late afternoon: C leans and falls into the dug-out lot next door
        mode('dusk'); c_collapse(smooth(0.05, 1.0, u))
        show(DUST, True); dust(t, 0.7 * smooth(0.35, 0.8, u), X0 + V3(11.0, 6.0, 2.0 + 3 * u), CAM.location, 4.0, rise=0.3)
        look(X0 + V3(4.0, -14.0, 1.6).lerp(V3(5.0, -13.2, 1.8), u) + shake(t, 0.06 * smooth(0.25, 0.6, u)), X0 + V3(6.0, 5.0, 4.6), 15, 16.0)
    elif nb == 11:                                          # night: lights on the pile, the open rooms next door, a drone over the pit
        mode('night'); night_fx(t); drone_at(X0 + V3(9.5, 3.0, float(HM.max()) + 4.0), t)
        cp = X0 + V3(13.0, -11.0, 9.5).lerp(V3(11.5, -10.5, 9.0), u)
        look(cp, X0 + V3(3.0, 6.0, 2.5), 18, 16.0)
    elif nb == 3:                                           # outside at night: the drone hangs in front of us, beams sweep the pile
        mode('night'); night_fx(t); dp = X0 + V3(10.0, 1.5, 7.5); drone_at(dp, t)
        look(X0 + V3(9.0, -3.5, 12.5).lerp(V3(9.3, -3.0, 12.0), u), X0 + V3(12.0, 7.0, -2.5), 20, 16.0)
