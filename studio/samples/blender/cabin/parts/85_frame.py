# ================================================================ FOG (a volume filling the cabin, thick for a few seconds after the blowout)
FOG_M = bpy.data.materials.new('fog'); FOG_M.use_nodes = True; _nt = FOG_M.node_tree; _nt.nodes.remove(_nt.nodes['Principled BSDF'])
_pv = _nt.nodes.new('ShaderNodeVolumePrincipled'); _pv.inputs['Color'].default_value = (0.92, 0.95, 1.0, 1)
_fz = _nt.nodes.new('ShaderNodeTexNoise'); _fz.inputs['Scale'].default_value = 1.6; _fz.inputs['Detail'].default_value = 3; _fz.noise_dimensions = '4D'
_ftc = _nt.nodes.new('ShaderNodeTexCoord'); _nt.links.new(_ftc.outputs['Object'], _fz.inputs['Vector']); _nt.links.new(objattr(_nt, 'tt'), _fz.inputs['W'])
_den = math_(_nt, 'MULTIPLY', objattr(_nt, 'dens'), math_(_nt, 'POWER', _fz.outputs['Fac'], 2.5))
_nt.links.new(math_(_nt, 'MULTIPLY', _den, 1.6), _pv.inputs['Density']); _nt.links.new(_pv.outputs['Volume'], _nt.nodes['Material Output'].inputs['Volume'])
FOG = box('fog', (3.6, Y1C - Y0C - 0.2, 2.3), (0, 0, 1.15), FOG_M); FOG.visible_shadow = False; FOG['dens'] = 0.0; FOG['tt'] = 0.0
C.volume_bounces = 0; S.cycles.volume_step_rate = 4.0
CABIN.append(FOG)
# ================================================================ MODES
MAN = [BODY, SUIT, HAIR] + HEADBITS
FLYW, FLYP = FLY_W.objs, FLY_P.objs + FLY_S.objs
def mode(which):
    """cabin / xray / out (the jet over the clouds) / road (the phone)"""
    for o in CABIN + JETP + ROADSIDE + [CLOUDS] + XRAY_OBJS: o.hide_render = True
    for lt in CAB_L + [XL, XL2]: lt.hide_render = True
    SUN_O.hide_render = False; world('sky'); PLUG_BO.show_render = False; HOLE.hide_render = True
    for i, sl in enumerate(BODY.material_slots): sl.material = BODY_MATS[i]
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = True
    PUFF.strength = 0.0
    for o in MAN: o.hide_render = which not in ('cabin', 'xray')
    if which == 'cabin':
        for o in CABIN + [CLOUDS]: o.hide_render = False
        for lt in CAB_L: lt.hide_render = False
        FOG.hide_render = FOG['dens'] <= 0.001
    elif which == 'xray':
        for o in [SUIT, HAIR] + HEADBITS: o.hide_render = True
        for i, sl in enumerate(BODY.material_slots): sl.material = XSKIN
        for md in BODY.modifiers:
            if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = False
        PUFF.strength = 0.004
        for o in XRAY_OBJS: o.hide_render = False
        XL.hide_render = XL2.hide_render = False; SUN_O.hide_render = True; world('xray')
    elif which == 'out':
        for o in JETP + [CLOUDS]: o.hide_render = False
        HOLE.hide_render = True
    elif which == 'road':
        for o in ROADSIDE: o.hide_render = False
# ================================================================ HIS HEAD: points on his face follow the head bone
def head_pt(p_rest):
    """a point given in his rest (armature) space near the head -> world, as the head bone moves it"""
    pb = PB['head']; return RIG.matrix_world @ (pb.matrix @ RB['head'].matrix_local.inverted() @ Vector(p_rest))
MOUTH_R = V3(0.0, -0.165, 1.475); FACE_R = V3(0.0, -0.14, 1.53)
def head_dir(d_rest):
    pb = PB['head']; return (RIG.matrix_world.to_3x3() @ (pb.matrix.to_3x3() @ RB['head'].matrix_local.to_3x3().inverted() @ Vector(d_rest))).normalized()
# ================================================================ THE BLOWOUT (shared by the first beat and the end of the last: the loop)
CAM0_P = V3(MYSEAT_X - 0.62, MY - 0.78, 1.32); CAM0_T = V3(MYSEAT_X + 0.28, MY + 0.08, 1.1)
def blow_state(tb, t):
    """tb = time since the window went (s, may be < 0 = still shut)"""
    k = smooth(0.0, 0.35, tb)
    d = 0.0 if tb <= 0 else 3.0 * tb + 30.0 * tb * tb
    BLOWG.location = (d, -0.4 * d, 0.05 * d); BLOWG.rotation_euler = (3.0 * d, 1.2 * d, 0.0); BLOWG.hide_render = d > 3.0
    MYPANE.hide_render = tb > 0.0
    BLOWP.location = V3(0.004, 0, 0) * math.sin(tb * 70) * k
    FOG['dens'] = 0.55 * smooth(0.0, 0.5, tb) * (1 - 0.6 * smooth(2.0, 6.0, tb)); FOG['tt'] = t * 0.6 + 2.0 * tb
    FLY_W.at(tb, H_WIN, V3(1, 0.6, -0.1), on=True)
    # him: flinches away from the hole, then grabs the armrest, hair pushed
    seated(t, lean=lerp(-8, -2, k), handR=V3(-0.17, -0.36, 0.98).lerp(V3(-0.22, -0.2, 0.86), k), handL=V3(0.17, -0.36, 0.98).lerp(V3(0.05, -0.32, 1.52), k),
           neck=lerp(0, 8, k), head=lerp(0, 4, k), head_yaw=lerp(0, -28, k), lids=lerp(0.05, 0.0, k), jaw=lerp(0.0, 0.55, k), curl=(0.35 + 0.4 * k, 0.35 + 0.3 * k),
           side_lean=lerp(0, -6, k), bob=k)
    return k
def cam_blow(tb, t):
    k = smooth(0.0, 0.5, tb)
    look(CAM0_P + V3(0.06, 0.1, 0.0) * k + shake(t, 0.006 + 0.03 * k), CAM0_T + V3(0.05, 0, 0.05) * k, 20, 4.0, focus=H_WIN.lerp(head_pt(FACE_R), 0.4))
TB0 = 0.04                                                               # frame one is this far into the blowout
SIT_AISLE = (-0.52, ROW_Y[PLUG_ROW])                                    # beats 9-10: he is the aisle seat of the door-plug row
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    S.view_settings.exposure = 0.0; FOG['dens'] = 0.0; HIDE_ROW[0] = None; masks(t, None); sun_from((0.75, -0.25, 0.45)); JET.location = PX; JET.rotation_euler = (0, 0, 0)
    PLUGE.location = (-2.0, PLUGE_Y, PLUGE_Z); PLUGE.rotation_euler = (0, 0, 0); FLY_P.at(-5, H_PLUG, V3(-1, 0.6, 0), on=False); FLY_W.at(-5, H_WIN, V3(1, 0, 0), on=False); FLY_S.at(-5, H_PLUG, V3(-1, 0.6, 0), on=False)
    BLOWG.location = (0, 0, 0); BLOWG.rotation_euler = (0, 0, 0); BLOWG.hide_render = False; MYPANE.hide_render = False
    if nb == 0:                                                          # the window goes (frame one already moving)
        tb = t + TB0; blow_state(tb, t); mode('cabin'); cam_blow(tb, t)
    elif nb == 1:                                                        # air rushes for the hole, the cabin fogs: down the aisle
        tb = t + TB0; blow_state(tb, t); mode('cabin')
        look(V3(0.12, MY - 3.4, 1.55).lerp(V3(0.2, MY - 2.7, 1.5), u) + shake(t, 0.015), V3(1.15, MY - 0.2, 1.0), 24, 5.6, focus=V3(1.2, MY, 1.0))
    elif nb == 2:                                                        # fifteen seconds: close on his face, fog drifting
        tb = t + TB0; blow_state(tb, t); mode('cabin')
        seated(t, lean=-4, handL=V3(0.2, -0.33, 1.05), handR=V3(-0.2, -0.33, 1.0), neck=5, head=2, head_yaw=-10 + 14 * sm(u), jaw=0.25, lids=0.1, side_lean=-3)
        fp = head_pt(FACE_R); look(fp + V3(-0.45, -0.62, -0.02).lerp(V3(-0.38, -0.5, 0.0), u) + shake(t, 0.004), fp + V3(0.02, 0, -0.03), 42, 2.8, focus=fp)
    elif nb == 3:                                                        # low oxygen feels good: x-ray, his lungs go from pink to blue, head lolls
        ts = B[3] + lt * 0.6; seated(ts, lean=-10, neck=lerp(4, 18, sm(u)), head=lerp(0, 8, u), head_yaw=lerp(4, 14, u) + 8 * wob(ts, 0.6, 2), lids=lerp(0.15, 0.55, u), jaw=0.12)
        mode('xray'); lungs(ts, oxy=lerp(1.0, 0.1, smooth(0.05, 0.9, u)), rate=0.35, depth=1.2)
        c_ = RIG.matrix_world @ V3(0, 0, 1.3); a_ = R(-35 + 30 * u)
        look(c_ + V3(1.05 * math.sin(a_), -1.05 * math.cos(a_), 0.12), c_ + V3(0, 0, 0.02), 38, 5.6, focus=c_)
        S.view_settings.exposure = 0.3
    elif nb == 4:                                                        # the masks drop; he grabs his and puts it on
        tb = t + TB0; blow_state(tb, t); mode('cabin'); FOG['dens'] *= 0.6
        dt_ = B[4] + 0.15; g = smooth(0.5, 0.75, u); w = smooth(0.75, 0.95, u)
        seated(t, lean=-4, neck=5, head_yaw=-6 * (1 - g), jaw=0.3 * (1 - w))
        mp = head_pt(MOUTH_R); fd = head_dir(V3(0, -1, 0))
        hang = None
        for m in MASKS:
            if m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01: m_my = m
        masks(t, dt_)
        hang = Vector(m_my['cup'].location)
        if g > 0:
            cpos = hang.lerp(mp + fd * 0.05, w); masks(t, dt_, mine=(cpos, V3(0, 1, 0.15).lerp(-fd, w)))
            Mi = rigM(SEAT_HIP, (-4, 0, 0)).inverted()
            hr = Vector(m_my['cup'].location) + V3(-0.04, -0.05, -0.03)
            seated(t, lean=-4, neck=5, head_yaw=-6 * (1 - g), jaw=0.3 * (1 - w), handR=V3(-0.17, -0.36, 0.98).lerp(Mi @ hr, g), curl=(0.35 + 0.4 * g, 0.35))
            if g > 0.98: place_hand('R', cpos + fd * 0.012, V3(0.2, 0, 1), -fd, 1.0); bpy.context.view_layer.update()
        look(V3(0.15, MY - 1.6, 1.5).lerp(V3(0.35, MY - 1.2, 1.4), u) + shake(t, 0.008), V3(1.25, MY - 0.15, 1.3), 24, 4.0, focus=V3(1.3, MY - 0.2, 1.3))
    elif nb == 5:                                                        # the pilots dive: the jet noses down toward the clouds
        mode('out'); dz = -80 * sm(u); JET.location = PX + V3(0, -40 * u, dz); JET.rotation_euler = (R(-11 * smooth(0, 0.3, u)), R(4), 0); bpy.context.view_layer.update()
        c_ = JET.location; look(c_ + V3(-30, -34, 9) + V3(3, 6, -3) * u, c_ + V3(0, -2, -1), 32, 22.0); sun_from((0.6, -0.5, 0.55))
    elif nb == 6:                                                        # the mask: at least twelve minutes, he breathes slow
        mode('cabin'); masks(t, B[4] + 0.15 - 20); HIDE_ROW[0] = MYROW - 1
        seated(t, lean=-6, neck=2, head=0, head_yaw=-4, lids=0.1)
        mp = head_pt(MOUTH_R); fd = head_dir(V3(0, -1, 0))
        for m in MASKS:
            if m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01: m_my = m
        cpos = mp + fd * (0.05 + 0.003 * math.sin(t * 2.5)); masks(t, B[4] + 0.15 - 20, mine=(cpos, -fd))
        Mi = rigM(SEAT_HIP, (-6, 0, 0)).inverted(); hr = Vector(m_my['cup'].location) + V3(-0.04, -0.05, -0.03)
        seated(t, lean=-6, neck=2, head_yaw=-4, lids=0.1, handR=Mi @ hr, curl=(0.75, 0.35)); place_hand('R', cpos + fd * 0.012, V3(0.2, 0, 1), -fd, 1.0); bpy.context.view_layer.update()
        fp = head_pt(FACE_R); look(fp + V3(-0.75, -0.95, 0.02).lerp(V3(-0.62, -0.8, 0.0), u), fp + V3(0.05, 0, -0.1), 38, 4.0, focus=fp)
    elif nb == 7:                                                        # 2024, Alaska Airlines: low sun, climbing out
        mode('out'); JET.location = PX + V3(0, -30 * u, 8 * u); JET.rotation_euler = (R(7), R(-3), 0); bpy.context.view_layer.update(); sun_from((-0.7, 0.4, 0.18), 3.5, (1.0, 0.72, 0.45))
        c_ = JET.location; look(c_ + V3(-40, -46, -5).lerp(V3(-35, -40, -4), u), c_ + V3(0, 2, 1), 30, 22.0)
    elif nb == 8:                                                        # the door plug blows out (slow motion)
        mode('out'); sun_from((-0.7, 0.4, 0.18), 3.5, (1.0, 0.72, 0.45)); JET.rotation_euler = (R(7), R(-3), 0); bpy.context.view_layer.update()
        ts = lt * 0.35; v = max(0.0, ts - 0.12); HOLE.hide_render = v <= 0
        PLUGE.location = V3(-2.0, PLUGE_Y, PLUGE_Z) + V3(-6 * v - 30 * v * v, 14 * v * v + 3 * v, 2 * v); PLUGE.rotation_euler = (R(40) * v * 3, R(-90) * v * 2, R(25) * v * 4)
        Mj = JET.matrix_world; pw = Mj @ V3(-1.975, PLUGE_Y, PLUGE_Z); cpl = Mj @ (V3(-12.0, PLUGE_Y + 3.2, 1.3).lerp(V3(-10.5, PLUGE_Y + 2.6, 1.1), u))
        look(cpl + shake(t, 0.03), Mj @ V3(-2.0, PLUGE_Y - 0.6, PLUGE_Z + 0.1), 40, 11.0, focus=pw)
    elif nb == 9:                                                        # the seats beside it were empty (he is on the aisle)
        mode('cabin'); PLUG_BO.show_render = True; PANES[len(ROW_Y) + PLUG_ROW].hide_render = True
        FOG['dens'] = 0.12; FOG['tt'] = t; FOG.hide_render = False
        seated(t, lean=-3, at=SIT_AISLE, head_yaw=30, neck=6, jaw=0.4, handL=V3(0.2, -0.3, 0.9), handR=V3(-0.25, -0.15, 0.9), side_lean=4, bob=1.0)
        FLY_P.at(lt + 0.6, H_PLUG, V3(-1, 0.7, 0));
        look(V3(0.35, ROW_Y[PLUG_ROW] - 1.9, 1.45).lerp(V3(0.3, ROW_Y[PLUG_ROW] - 1.6, 1.4), u) + shake(t, 0.01), V3(-1.2, ROW_Y[PLUG_ROW] - 0.1, 0.85), 24, 5.6)
    elif nb == 10:                                                       # a shirt and phones out the hole (slow motion)
        mode('cabin'); PLUG_BO.show_render = True; PANES[len(ROW_Y) + PLUG_ROW].hide_render = True
        FOG['dens'] = 0.1; FOG['tt'] = t; FOG.hide_render = False; ts = lt * 0.45
        seated(t, lean=-3, at=SIT_AISLE, head_yaw=40, neck=8, jaw=0.5, handL=V3(0.1, -0.35, 1.45), handR=V3(-0.25, -0.15, 0.9), side_lean=6, bob=1.0)
        FLY_P.at(ts + 1.0, H_PLUG, V3(-1, 0.7, 0)); FLY_S.at(ts + 0.1, H_PLUG, V3(-1, 0.8, 0.1)); shirt_wave(ts)
        look(V3(-0.2, ROW_Y[PLUG_ROW] - 1.2, 1.25) + shake(t, 0.006), H_PLUG + V3(0.3, 0.1, 0.1), 26, 5.6, focus=H_PLUG)
    elif nb in (11, 12):                                                 # a phone by the road, still working
        mode('road'); S.view_settings.exposure = 0.5; sun_from((0.4, -0.6, 0.5), 3.5, (1.0, 0.9, 0.75)); u2 = (t - B[11]) / (DUR[11] + DUR[12])
        look(PHONE_AT + V3(-0.5, -0.65, 0.6).lerp(V3(-0.22, -0.3, 0.32), sm(u2)), PHONE_AT + V3(0, 0, 0.0), 40, 4.0, focus=PHONE_AT)
    else:                                                                # back in his seat, calm; the camera settles where it starts; the window goes (= frame one)
        tb = t - TOTAL + TB0; blow_state(tb, t); mode('cabin')
        if tb < 0:
            k = smooth(0.0, 0.85, u)
            seated(t, lean=-8, head_yaw=lerp(-20, 0, smooth(0, 0.6, u)), neck=lerp(-2, 0, u), lids=0.05)
            look(CAM0_P + V3(-0.3, 0.35, 0.15) * (1 - k) + shake(t, 0.004), CAM0_T + V3(-0.2, 0.0, 0.2) * (1 - k), lerp(26, 20, k), 4.0,
                 focus=H_WIN.lerp(head_pt(FACE_R), 0.4))
        else: cam_blow(tb, t)
