
# ================================================================ the story: one shot per line (times from times.json)
END = TOTAL
LIGHTS = {'yard': [SUN_O, NIGHT_O, PORCH], 'space': [SPACE_FILL, PLUTO_KEY], 'sea': [SEA_KEY, VENT_L, VENT_FILL, MIC_L, MIC_KICK]}
GROUPS = {'space': SPACE, 'yard': YARD, 'sea': SEA, 'vent': VENT, 'micro': MICRO_ALL}
def mode(which):
    """show one stage, hide the rest (and their lights)"""
    on = {'space': ('space',), 'yard': ('yard',), 'sea': ('sea',), 'vent': ('vent',), 'micro': ('micro',)}[which]
    for g, objs in GROUPS.items(): show(objs, g in on)
    for g, ls in LIGHTS.items():
        for o in ls: o.hide_render = not ((g == 'yard' and which == 'yard') or (g == 'space' and which == 'space') or (g == 'sea' and which in ('sea', 'vent', 'micro')))
    if which != 'yard': SKY_DAYK.outputs[0].default_value = 0.0
    if TRAIL is not None: TRAIL.hide_render = True
    stopwatch_set(False); breath_set(0, []); xtal_set(0, False); birds_set(0, False); fpv(hide=True)
def punch(lt, lens):
    """the house punch cut: lands a little zoomed in and settles in 0.2 s"""
    return lens * (1.0 + 0.07 * (1.0 - smooth(0.0, 0.2, lt)))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x, 0, 1); return x ** 3
def yaw_pitch(yaw, pitch, base=None):
    """a look target from the eye: yaw right of north, pitch up (degrees)"""
    e_ = EYE if base is None else base; return e_ + Vector((math.sin(R(yaw)) * math.cos(R(pitch)), math.cos(R(yaw)) * math.cos(R(pitch)), math.sin(R(pitch))))
def handheld(t, amt=1.0):
    return Vector((wob(t, 0.35, 1.0) * 0.6, 0.0, wob(t, 0.3, 2.0) * 0.45)) * amt, wob(t, 0.25, 5.0) * 0.6 * amt   # (yaw, pitch) wobble in degrees, roll
def fpv_look(t, yaw, pitch, lens, fstop=8.0, focus_d=4.0, amt=1.0, roll=0.0):
    w_, rl = handheld(t, amt); yy, pp = yaw + w_.x, pitch + w_.z
    look(EYE, yaw_pitch(yy, pp), lens=lens, fstop=fstop, roll=R(rl + roll))
    CAM.data.dof.focus_distance = focus_d

# ---- shot 0 (and the loop tail): the Sun, close, shuddering, then gone
def cam0(c):
    """frame one's camera, a slow push; c = seconds from frame one"""
    return SUN_C + Vector((0.6 * math.sin(0.35 * c), -46.0 + 7.0 * c, -1.0)), SUN_C + Vector((0.0, 0.0, -1.6)) + Vector((0.0, 0.0, 0.25 * c))
def shot_sun(t, c):
    mode('space'); r_ = sun_story(c); bloom(0.45, 0.9); S.view_settings.exposure = 0.0
    EARTH.hide_render = True; CLOUDS.hide_render = True; ATM.hide_render = True; PLUTO.hide_render = True; show(DASHES, False)
    cp, ct = cam0(c)
    if c < 0:                                                          # the loop tail: pulled back out of the Sun's face onto frame one's camera
        k = ease_out((c + 0.45) / 0.45); cp0, ct0 = cam0(0.0)
        cp = (SUN_C + Vector((0.0, -15.5, -0.6))).lerp(cp, k); ct = (SUN_C + Vector((0, 0, -0.3))).lerp(ct, k)
    sh = shake(c, 0.6, 3.0) * math.exp(-2.5 * max(c - 1.4, 0)) * smooth(1.32, 1.42, c) if c > 1.3 else Vector()
    look(cp + sh, ct + sh, lens=30.0, fstop=16.0)

# ---- shots 1, 2 and 10: the sunny yard from your eyes
T_BO = B[2] + 0.1457 * DUR[2]                                       # lights out, on the word (the label lands with it)
T_MOON = B[2] + 0.62 * DUR[2]                                       # "Moon goes dark"
SW_T0, SW_T1 = 2.347, 5.444                                         # the burned-in 8:20 countdown
WATCH_CURL, WATCH_THUMB, WATCH_SLIDE, WATCH_LIFT = 0.7, 0.55, -0.003, 0.019             # fingers wrap the watch's top edge (tuned with handchk.py)
def watch_hand(t, lift=0.0, drop=0.0):
    """left hand open, palm up and toward you, the stopwatch lying in it; drop 0..1 lowers it out of the shot"""
    fd = cam_dir(0.12, 1.0, 0.35); pd = cam_dir(0.05, 0.3, -1.0)       # palm turned to you, fingers up: the dial faces the camera
    c_ = cam_pt(-0.03 + 0.004 * wob(t, 0.8, 9.0), -0.06 + lift - 0.3 * ease_in(drop), 0.27 + 0.003 * wob(t, 0.7, 4.0))
    place_hand('L', c_, fd, pd); fingers('L', WATCH_CURL, thumb=WATCH_THUMB); return c_, fd, pd
def watch_on(c_, fd, pd, secs):
    bpy.context.view_layer.update()
    pp, d_, n_ = palm_point('L')
    up = pd.normalized(); y_ = (fd - up * fd.dot(up)).normalized(); x_ = y_.cross(up)
    q = Matrix((x_, y_, up)).transposed().to_quaternion()
    stopwatch_set(True, c_ + up * WATCH_LIFT - y_ * WATCH_SLIDE, q, secs)
def shade_hand(k):
    """right hand raised at arm's length toward the Sun, back of the hand to you, fingers spread: the light glows between them (k 0..1)"""
    kk = sm(clamp(k, 0, 1))
    lo = cam_pt(0.22, -0.5, 0.3); hi = cam_pt(-0.05, -0.035, 0.44)
    c_ = lo.lerp(hi, kk); fd = cam_dir(0.3, 0.6, 0.8).lerp(cam_dir(0.06, 1.0, 0.08), kk).normalized(); pd = cam_dir(-0.5, 0.0, 0.6).lerp(cam_dir(-0.05, 0.0, 1.0), kk).normalized()
    place_hand('R', c_, fd, pd, w_rot=1.0); fingers('R', lerp(0.35, 0.06, kk), spread=lerp(0.0, 9.0, kk), thumb=0.0)
def shot_day(t, b):
    lt = t - B[b]
    mode('yard'); dress(False); birds_set(t, True); show(CLOUDS_D, True)
    POND['ice'] = 0.0; LAKE['ice'] = 0.0; POND['front'] = 0.0; LAKE['front'] = 0.0; therm_set(72)
    MOON.hide_render = True; bloom(0.42, 1.1); S.view_settings.exposure = 0.0
    if b == 1 or (b == 2 and t < T_BO):
        yard_mode(1.0, 0.0, t); for_w(0.0)
        fpv_look(t, 9.0, -7.0, punch(lt, 24.0) if b == 1 else 24.0, 8.0, 0.33)
        fpv(); arm_down('R'); c_, fd, pd = watch_hand(t)
        k = clamp((t - SW_T0) / (SW_T1 - SW_T0), 0, 1); watch_on(c_, fd, pd, 480.0 * k)
    elif b == 2:                                                        # lights out: night in one frame, windows and the porch lamp come on, look up at the Moon
        yard_mode(0.0, 0.0, t); dt = t - T_BO; for_w(dt)
        NIGHTL.energy = 0.3 + 0.9 * (1 - smooth(T_MOON, T_MOON + 0.25, t))   # moonlight still on for a moment: a cool rim on your hand
        PORCH.data.energy = 110.0 * smooth(0.3, 0.38, dt); birds_set(t, False); show(CLOUDS_D, False)
        MOON.hide_render = False; MOON['lit'] = 0.35 * (1 - smooth(T_MOON, T_MOON + 0.25, t))
        k = smooth(T_BO + 0.25, T_BO + 0.85, t)
        fpv_look(t, lerp(9.0, -18.0, k), lerp(-7.0, 13.0, k), 24.0, 8.0, lerp(0.33, 8.0, k))
        fpv(); arm_down('R'); c_, fd, pd = watch_hand(t, drop=smooth(T_BO + 0.15, T_BO + 0.7, t))
        if k < 0.6: watch_on(c_, fd, pd, 0.0)
        S.view_settings.exposure = 0.35
    else:                                                               # shot 10: the sunshine is back; shade your eyes, look at the Sun, then dive into it
        yard_mode(1.0, 0.0, t); for_w(0.0)
        k = smooth(B[10] + 0.1, B[10] + 0.95, t); zk = smooth(END - 1.0, END - 0.45, t)
        fpv_look(t, lerp(9.0, 15.0, k), lerp(-7.0, 9.0, k), punch(lt, 24.0) * (1.0 + 5.0 * ease_in(zk)), 8.0, 0.3 + 3.0 * k, amt=1.0 - zk)
        fpv(); arm_down('L'); shade_hand(smooth(B[10] + 0.05, B[10] + 0.85, t) * (1 - smooth(END - 1.55, END - 1.05, t)))
        S.view_settings.exposure = 2.5 * ease_in(zk); bloom(0.3 + 1.2 * zk, 1.2 - 0.6 * zk)
def for_w(dt):
    for o in WINDOWS: o['lit'] = 1.0 if dt > o['on_t'] else 0.0

# ---- shot 3: Earth on its orbit, the Sun gone; it breaks off along a straight line
ORB_C = SP; ORB_R2 = 30.0; E_R3 = 2.4; W3 = 0.45; T_BRK = B[3] + 0.3498 * DUR[3]
def earth3(t):
    if t < T_BRK: a_ = W3 * (t - T_BRK); return ORB_C + Vector((ORB_R2 * math.cos(a_), ORB_R2 * math.sin(a_), 0.0))
    return ORB_C + Vector((ORB_R2, ORB_R2 * W3 * (t - T_BRK), 0.0))
def shot_orbit(t):
    mode('space'); lt = t - B[3]; sun_story(9.0); show(PROMS, False); SUN.hide_render = True; CORONA.hide_render = True; EMBER.hide_render = True; SHOCK.hide_render = True
    PLUTO.hide_render = True; bloom(0.3, 1.0); S.view_settings.exposure = 0.3
    e_ = earth3(t); EARTH.location = e_; EARTH.scale = (E_R3,) * 3; EARTH['frost'] = 0.0; EARTH['city'] = 1.0; EARTH.rotation_euler = (R(-20), R(15), 0.4 * t)
    for k, o in enumerate(DASHES):
        a_ = 2 * math.pi * k / 90; o.location = ORB_C; o.scale = (ORB_R2 / ORB_R, ORB_R2 / ORB_R, 1.0); o['a'] = 0.55
    pts = []                                                         # the trail: the last bit of orbit, then the straight run
    for i in range(40):
        tt = t - 1.6 + 1.6 * i / 39; p_ = earth3(tt); pts.append(p_ - Vector((0, 0, 0.02)))
    tr = trail_set(pts); tr['a'] = 1.0
    SPACE_FILL.location = e_ + Vector((-25, -18, 22)); SPACE_FILL.rotation_quaternion = (e_ - SPACE_FILL.location).to_track_quat('-Z', 'Y'); SPACE_FILL.data.energy = 30000
    yc = (e_ - ORB_C).y + 4.0
    cp = ORB_C + Vector((ORB_R2 - 9.0, yc - 26.0, 36.0)); ct = ORB_C + Vector((ORB_R2 - 6.0, yc + 2.0, 0.0))
    look(cp, ct, lens=punch(lt, 26.0), fstop=16.0, up=(0, 1, 0.6))

# ---- shot 4: night, the thermometer on the post drops in steps; your breath fogs
TEMPS = [(B[4], 59), (10.395, 59), (10.475, 47), (10.893, 47), (10.973, 35), (11.391, 35), (11.471, 23), (99, 23)]
def temp_at(t):
    for (t0, f0), (t1, f1) in zip(TEMPS, TEMPS[1:]):
        if t0 <= t < t1: return lerp(f0, f1, sm((t - t0) / (t1 - t0)))
    return 23
def shot_therm(t):
    lt = t - B[4]; mode('yard'); yard_mode(0.0, 0.08 * smooth(B[4] + 1.2, B[5], t), t); for_w(9.0)
    MOON.hide_render = True; POND['ice'] = 0.0; LAKE['ice'] = 0.0; therm_set(temp_at(t)); bloom(0.3, 1.2); S.view_settings.exposure = 0.45
    w_, rl = handheld(t, 0.6)
    tg = TPOST + Vector((0.01, 0.0, 0.02)); cp = EYE + Vector((0.0, 0.05, -0.05))
    d_ = (tg - cp).normalized(); side = d_.cross(Vector((0, 0, 1))).normalized()
    look(cp, tg + side * (w_.x * 0.02) + Vector((0, 0, w_.z * 0.02)), lens=punch(lt, lerp(38.0, 44.0, sm(lt / DUR[4]))), fstop=5.6, roll=R(rl))
    CAM.data.dof.focus_distance = (tg - cp).length
    breath_set(t, [B[4] + 0.12, B[4] + 1.2], 1.0)

# ---- shot 5: day 3, everything frosts over (and your sleeve); ice crystals glitter in the porch light
def check_hand(t):
    c_ = cam_pt(0.02 + 0.003 * wob(t, 0.7, 2.0), -0.045, 0.46); place_hand('L', c_, cam_dir(1.0, 0.25, 0.55), cam_dir(0.0, -1.0, 0.3)); fingers('L', 0.28, thumb=0.2)
def shot_frost(t):
    lt = t - B[5]; u = lt / DUR[5]; mode('yard'); dress(True)
    fr = lerp(0.12, 1.0, smooth(0.05, 0.85, u)); yard_mode(0.0, fr, t); for_w(9.0); MOON.hide_render = True
    POND['ice'] = 0.0; LAKE['ice'] = 0.0; therm_set(23); bloom(0.3, 1.2); S.view_settings.exposure = 0.45
    fpv_look(t, lerp(-4.0, 2.0, sm(u)), -11.0, punch(lt, 24.0), 8.0, 0.33)
    fpv(); arm_down('R'); check_hand(t)
    xtal_set(t, True); breath_set(t, [B[5] + 0.3, B[5] + 1.5], 1.0)

# ---- shot 6: the pond freezes in a blink, then the lake starts to; dive into the lake ice
P_FREEZE = (B[6] + 0.05, B[6] + 1.0)
def shot_ponds(t):
    lt = t - B[6]; u = lt / DUR[6]; mode('yard'); yard_mode(0.0, 1.0, t); for_w(9.0); MOON.hide_render = True; therm_set(5)
    pk = smooth(*P_FREEZE, t); POND['ice'] = 1.25 * pk; POND['front'] = 3.0 * (1 - smooth(0.9, 1.0, pk))
    lk = smooth(B[6] + 1.05, B[6] + 1.95, t); LAKE['ice'] = 0.04 + 0.32 * lk; LAKE['front'] = 3.0
    bloom(0.35, 1.0); S.view_settings.exposure = 0.55
    k = smooth(B[6] + 0.95, B[6] + 1.5, t); dv = smooth(END * 0 + B[7] - 0.38, B[7], t)
    pond_t = Vector((PC.x, PC.y, ground_z(PC.x, PC.y))); lake_t = Vector((2.0, 80.0, LAKE_Z))
    tg = pond_t.lerp(lake_t, sm(k)); cp = EYE + Vector((0, 0.15, 0)); w_, rl = handheld(t, 1.0 - dv)
    d_ = (tg - cp); cp = cp + d_ * (0.92 * ease_in(dv))
    look(cp, tg + Vector((w_.x * 0.06, 0, w_.z * 0.06)), lens=punch(lt, lerp(36.0, 30.0, k)) * (1 + 1.5 * ease_in(dv)), fstop=8.0, roll=R(rl))
    CAM.data.dof.focus_distance = (tg - cp).length

# ---- shot 7: the ocean under the ice, cut open: the lid of ice, the water still moving
def shot_sea(t):
    lt = t - B[7]; u = lt / DUR[7]; mode('sea'); sea_set(t); bloom(0.35, 1.0); S.view_settings.exposure = 0.0
    SEA_KEY.data.energy = 4000
    k = ease_out(lt / 0.75); dv = smooth(B[8] - 0.36, B[8], t)
    top = SS + Vector((0.4, -1.2, ICE_T + 5.5)); side = SS + Vector((3.0, -13.0, -0.8)).lerp(Vector((2.6, -12.0, -2.4)), sm(u))
    cp = top.lerp(side, k); ct = (SS + Vector((0, 0, ICE_T))).lerp(SS + Vector((0, 0, -3.0)), k)
    bot = SS + Vector((0.3, 0, -BH + 0.4)); cp = cp.lerp(bot + Vector((0, -2.0, 0.6)), ease_in(dv)); ct = ct.lerp(bot, sm(dv))
    look(cp, ct, lens=lerp(22.0, 32.0, k) * (1 + 0.8 * ease_in(dv)), fstop=11.0)

# ---- shot 8: the vent on the sea floor (tube worms, black smoke), then the microbes living off its chemicals
T_MIC = B[8] + 1.8
def shot_vent(t):
    lt = t - B[8]
    if t < T_MIC:
        mode('vent'); vent_set(t); VENT_L.data.energy = 300; VENT_FILL.data.energy = 600; bloom(0.4, 1.0); S.view_settings.exposure = 0.2
        k = ease_out(lt / 1.0)
        cp = (VS + Vector((0.6, -3.0, 8.5))).lerp(VS + Vector((1.5, -6.2, 1.7)), k) + Vector((0.4 * math.sin(lt * 0.5), 0, 0))
        ct = (VS + Vector((0, 0, 3.0))).lerp(VS + Vector((0, 0, 2.2)), k)
        look(cp, ct, lens=lerp(22.0, 26.0, k), fstop=8.0)
    else:
        mode('micro'); micro_set(t); MIC_L.data.energy = 60; MIC_KICK.data.energy = 25; bloom(0.35, 1.1); S.view_settings.exposure = 0.2
        u = (t - T_MIC) / (B[9] - T_MIC); p_, n_ = rock_pt(0.0, 0.0, 0.0)
        a_ = R(-8 + 16 * u); off = Vector((math.sin(a_) * 0.85, -math.cos(a_) * 0.85, 0.75)) * lerp(1.25, 1.0, sm(u))
        look(p_ + off, p_ + Vector((0, 0.05, 0.02)), lens=punch(t - T_MIC, 40.0), fstop=5.6, focus=p_)

# ---- shot 9: frozen Earth drifts in beside Pluto
C9 = SP + Vector((0.0, -520.0, 0.0))
def shot_pluto(t):
    lt = t - B[9]; u = lt / DUR[9]; mode('space'); sun_story(9.0); SUN.hide_render = True; CORONA.hide_render = True; EMBER.hide_render = True; SHOCK.hide_render = True
    show(DASHES, False); bloom(0.25, 1.1); S.view_settings.exposure = 0.0
    k = ease_out(lt / 2.6)
    EARTH.location = C9 + Vector((lerp(4.8, 0.75, k), 9.0, 0.95)); EARTH.scale = (1.6,) * 3; EARTH['frost'] = lerp(0.75, 1.0, smooth(0.0, 0.5, u)); EARTH['city'] = 0.0
    EARTH.rotation_euler = (R(-15), R(10), -0.6 + 0.12 * t)
    PLUTO.hide_render = False; PLUTO.location = C9 + Vector((-0.6, 4.5, -0.22)); PLUTO.rotation_euler = (R(8), 0, R(270) + 0.05 * lt)
    PLUTO_KEY.location = C9 + Vector((-7.0, 1.0, 5.0)); PLUTO_KEY.rotation_quaternion = ((C9 + Vector((0, 6, 0))) - PLUTO_KEY.location).to_track_quat('-Z', 'Y'); PLUTO_KEY.data.energy = 4500; PLUTO_KEY.data.size = 6
    SPACE_FILL.location = C9 + Vector((6, 3, -3)); SPACE_FILL.rotation_quaternion = ((C9 + Vector((0, 7, 0))) - SPACE_FILL.location).to_track_quat('-Z', 'Y'); SPACE_FILL.data.energy = 1500
    a_ = R(2.0 * math.sin(0.4 * lt))
    look(C9 + Vector((0.15 * u, 0.25 * u, 0.0)), C9 + Vector((0.12, 6.0, 0.18)), lens=punch(lt, 35.0), fstop=16.0, roll=a_)

def state(t):
    t = clamp(t, 0.0, END - 1e-4); b = beat_at(t)
    S.render.use_motion_blur = True
    if b == 0: shot_sun(t, t)
    elif b in (1, 2): shot_day(t, b)
    elif b == 3: shot_orbit(t)
    elif b == 4: shot_therm(t)
    elif b == 5: shot_frost(t)
    elif b == 6: shot_ponds(t)
    elif b == 7: shot_sea(t)
    elif b == 8: shot_vent(t)
    elif b == 9: shot_pluto(t)
    else:
        if t >= END - 0.45: shot_sun(t, t - END)
        else: shot_day(t, 10)
    bpy.context.view_layer.update()

def cut_at(t, d):
    """a camera cut sits between t - d and t + d: no blur keys across it"""
    cuts = list(B[1:]) + [T_MIC, END - 0.45]
    return any(t - d < c_ <= t + d for c_ in cuts)
def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear(); CAM.data.animation_data_clear()
    if not cut_at(t, d) and t > d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            state(tt_); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
            CAM.data.keyframe_insert('lens', frame=kf)
    S.frame_set(f); state(t)
    if CAM.animation_data:                                              # the lens and camera come from the keys; everything else is set for t
        pass
