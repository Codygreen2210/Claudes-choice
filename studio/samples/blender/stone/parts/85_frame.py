# ================================================================ MODES and the story
MAN = [BODY, SUIT, HAIR] + HEADBITS
def room_mode(man=True):
    for o in ROOM: o.hide_render = False
    for o in MAN: o.hide_render = not man
    for i, sl in enumerate(BODY.material_slots): sl.material = BODY_MATS[i]
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = True
    PUFF.strength = 0.0
    for o in XRAY_OBJS + MACRO_A + MACRO_B: o.hide_render = True
    for lt in ROOM_L: lt.hide_render = False
    XL.hide_render = XL2.hide_render = True
    WBG.inputs['Color'].default_value = (0.01, 0.012, 0.02, 1)
def xray_mode():
    for o in ROOM + MACRO_A + MACRO_B: o.hide_render = True
    BODY.hide_render = False
    for o in [SUIT, HAIR] + HEADBITS: o.hide_render = True
    for i, sl in enumerate(BODY.material_slots): sl.material = XSKIN
    for md in BODY.modifiers:
        if md.type == 'MASK' and md.name.startswith('Delete'): md.show_render = False
    PUFF.strength = 0.004
    for o in XRAY_OBJS: o.hide_render = False
    for lt in ROOM_L: lt.hide_render = True
    XL.hide_render = XL2.hide_render = False
    WBG.inputs['Color'].default_value = (0.004, 0.012, 0.035, 1)
def macro_mode(which):
    for o in ROOM + MAN + XRAY_OBJS + MACRO_A + MACRO_B + ROOM_L + [XL, XL2]: o.hide_render = True
    for o in (MACRO_A if which == 'a' else MACRO_B): o.hide_render = False
    WBG.inputs['Color'].default_value = (0.05, 0.02, 0.004, 1) if which == 'a' else (0.012, 0.004, 0.005, 1)
def organs(t, art=0.0, pee=0.0, glow=0.3, pain=0.0, swell=0.0, fillto=-1.0, bones=1.0):
    for o in kind('artery') + kind('vein'): o['tt'] = t; o['flow'] = art; o['speed'] = 1.6; o['glow'] = 0.15 + 0.2 * art
    for o in kind('ureter'): o['tt'] = t; o['flow'] = pee * 2.0; o['speed'] = 1.2; o['glow'] = 0.25 + 0.3 * pee; o['fillto'] = -1.0
    URER['fillto'] = fillto
    for o in kind('kidney') + kind('pelvis') + kind('bladder'): o['pain'] = 0.0
    KIDR['pain'] = pain; PELR['pain'] = min(1.0, swell * 1.2)
    KIDR.scale = (1 + 0.05 * swell,) * 3; PELR.scale = (1 + 0.3 * swell, 1 + 0.3 * swell, 1 + 0.12 * swell)
    BODY['pain'] = pain; BODY['tt'] = t
def stone_at(s, t, small_s=None):
    p = ure_pt(s); STONE.location = p; STONE.rotation_euler = (t * 0.7 + s * 60, s * 90, t * 0.4); HALO.location = p; STONE.hide_render = HALO.hide_render = False
    SMALL.hide_render = small_s is None
    if small_s is not None: SMALL.location = ure_pt(small_s); SMALL.rotation_euler = (small_s * 80, t, 0)
def rw(p): return RIG.matrix_world @ Vector(p)
MANB = (0, 1, 2, 6, 8, 11); KSTEP = 6
def push_at(ff):
    """the right hand's push-out at frame ff, worked out fresh (None if he is not on screen then)"""
    tt = ff / FPS; nb_ = beat_at(tt)
    if nb_ not in MANB or ff < 0 or ff >= int(TOTAL * FPS): return None
    PUSH['use'] = None; man_pose(nb_, (tt - B[nb_]) / DUR[nb_], tt); return PUSH['last'].copy()
def pose_smooth(f):
    """the push-out is found every KSTEP frames and blended between them, so the hand glides instead of jumping frame to frame"""
    k0 = (f // KSTEP) * KSTEP; ps = [push_at(k0 - KSTEP), push_at(k0), push_at(k0 + KSTEP), push_at(k0 + 2 * KSTEP)]
    have = [p for p in ps if p is not None]
    if not have: PUSH['use'] = None
    else:
        ps = [p if p is not None else have[0] for p in ps]; w = (f - k0) / KSTEP
        a_, b_, c_, d_ = ps                                           # Catmull-Rom through the four
        PUSH['use'] = 0.5 * ((2 * b_) + (-a_ + c_) * w + (2 * a_ - 5 * b_ + 4 * c_ - d_) * w * w + (-a_ + 3 * b_ - 3 * c_ + d_) * w ** 3)
    t = f / FPS; nb = beat_at(t); man_pose(nb, (t - B[nb]) / DUR[nb], t); PUSH['use'] = None
CAM0 = (V3(-1.75, -2.35, 0.95), V3(0.05, -0.2, 0.92), 30.0)            # frame one and the loop's last frame
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    xr = nb in (1, 2, 6, 8)
    PUFF.strength = 0.004 if xr else 0.0
    S.view_settings.exposure = 0.0
    if nb in (0, 1, 2, 6, 8, 11): pose_smooth(f)
    WATER.scale = (1, 1, 0.02); STREAM.hide_render = True
    if nb == 0:                                             # he drops to his knees at the counter, hand to his side
        room_mode()
        cp, ct, ln = CAM0; k = smooth(0.0, 0.75, u)
        look(cp.lerp(V3(-1.25, -2.3, 0.5), k) + shake(t, 0.004 + 0.02 * math.exp(-abs(u - 0.4) * 14)), ct.lerp(V3(0.02, -0.55, 0.62), k), lerp(ln, 36, k), 5.6, focus=rw((0, 0, 1.1)))
    elif nb in (1, 2, 6, 8):
        xray_mode(); STONE.hide_render = HALO.hide_render = SMALL.hide_render = True
        tor = rw((0.0, -0.05, 1.04)); kid = rw(KC)
        if nb == 1:                                         # into him: the right kidney, deep under the ribs at his back
            organs(t, glow=0.3); KIDR['pain'] = 0.35 + 0.25 * math.sin(t * 5); k = smooth(0.0, 1.0, u)
            look(rw((-0.55, -1.6, 1.25)).lerp(rw((-0.32, -0.75, 1.16)), k), tor.lerp(kid, k), lerp(40, 55, k), 8.0, focus=kid)
        elif nb == 2:                                       # blood in (red), cleaned; the waste goes down both ureters to the bladder (yellow)
            organs(t, art=smooth(0.0, 0.3, u) * 1.4, pee=smooth(0.3, 0.6, u), glow=0.3); BLAD['pain'] = 0.0
            mid = rw((0.0, -0.05, 0.98)); k = smooth(0.2, 1.0, u)
            look(rw((-0.3, -0.95, 1.2)).lerp(rw((-0.12, -1.25, 1.02)), k), rw(KC + V3(0.04, 0, -0.01)).lerp(mid, k), lerp(50, 46, k), 9.0, focus=mid)
        elif nb == 6:                                       # the stone breaks loose from the funnel and drops into the ureter
            s = lerp(-0.03, 0.05, smooth(0.15, 0.85, u) ** 1.4); organs(t, pee=0.4, glow=0.25, pain=smooth(0.6, 1.0, u) * 0.8); stone_at(s, t)
            p = rw(ure_pt(s)); k = smooth(0, 1, u)
            look(rw(KC + V3(-0.16, -0.5, 0.06)).lerp(rw(KC + V3(-0.1, -0.42, -0.02)), k), rw(KC + V3(0.01, 0, -0.03)).lerp(p, 0.5), 70, 9.0, focus=p)
        else:                                               # pee backs up above the stone, the funnel swells, the pain comes in waves
            sw = smooth(0.0, 0.6, u); wave = 0.5 + 0.5 * math.sin(lt * 2 * math.pi * 1.25 - 1.2)
            organs(t, pee=0.2, glow=0.25, pain=0.25 + 0.75 * wave, swell=sw * (0.85 + 0.15 * wave), fillto=0.05 * sw + 0.001); stone_at(0.05, t * 0.2)
            UREL['flow'] = 1.6
            k = smooth(0, 1, u); look(rw((-0.42, -1.05, 1.22)).lerp(rw((-0.5, -1.3, 1.16)), k) + shake(t, 0.004 * wave), rw(KC + V3(0.03, 0, -0.07)), 55, 9.0, focus=kid)
    elif nb in (3, 4, 5):
        macro_mode('a')
        pack = smooth(0.1, 0.9, u) if nb == 3 else 1.0; join = smooth(0.0, 0.9, u) if nb == 4 else (1.0 if nb == 5 else 0.0); stack = smooth(0.0, 0.92, u) if nb == 5 else 0.0
        macro_a(pack, join, stack, t)
        WBG.inputs['Color'].default_value = tuple(Vector((0.09, 0.06, 0.012)).lerp(Vector((0.07, 0.025, 0.002)), pack)) + (1,)
        a_ = 0.5 + t * 0.12; rad = lerp(0.66, 0.58, pack) if nb == 3 else (lerp(0.58, 0.62, u) if nb == 4 else lerp(0.62, 0.5, smooth(0, 1, u)))
        look(MO + V3(math.sin(a_) * rad, -math.cos(a_) * rad, 0.1 + 0.05 * math.sin(t * 0.5)), MO, 42, 6.0 if nb == 3 else 8.0)
    elif nb in (7, 9):
        macro_mode('b'); USMALL.o.hide_render = True; USTONE.o.hide_render = False
        if nb == 7:                                         # it scrapes down the lining and jams where the tube is tight
            v = smooth(0.0, 0.62, u); zs = lerp(1.0, 0.05, 1 - (1 - v) ** 2.2); jam = smooth(0.62, 0.7, u); back = smooth(0.66, 1.0, u)
            ureter_set(t, zs, RS_BIG, narrow=1.0, back=0.75 * back, wave=0.0, z0=1.0, scrape=1.0, pee_to=zs + RS_BIG * 0.3 if back > 0 else None)
            USTONE.o.location = UO + V3(0, 0.005, zs) + shake(t, 0.004 * (1 - jam)); USTONE.o.rotation_euler = (zs * 2.2, zs * 1.1, 0.3)
            look(UO + V3(0.1, -1.55, 0.25).lerp(V3(0.06, -1.25, 0.12), smooth(0, 1, u)) + shake(t, 0.01 * math.exp(-abs(u - 0.64) * 16)), UO + V3(0, 0, clamp(zs * 0.75, 0.08, 0.6)), 50, 9.0)
        elif u < 0.48:                                      # a small stone: the squeeze waves carry it down and out
            v = u / 0.48; zs = lerp(1.0, -1.0, v); USTONE.o.hide_render = True; USMALL.o.hide_render = False
            ureter_set(t, zs, RS_SMALL, narrow=0.0, back=0.0, wave=0.7)
            USMALL.o.location = UO + V3(0.01, 0.01, zs); USMALL.o.rotation_euler = (t * 3, t * 2, 0)
            look(UO + V3(0.05, -1.5, 0.1 + zs * 0.55), UO + V3(0, 0, zs * 0.55), 50, 9.0)
        else:                                               # a big one: stuck. the waves hit it and it does not move
            ureter_set(t, 0.05, RS_BIG, narrow=1.0, back=0.9, wave=1.0, z0=1.4, scrape=1.0, pee_to=0.05 + RS_BIG * 0.3)
            USTONE.o.location = UO + V3(0, 0.005, 0.05) + shake(t, 0.002); USTONE.o.rotation_euler = (0.11, 0.055, 0.3)
            look(UO + V3(0.06, -1.3, 0.14) + shake(t, 0.003), UO + V3(0, 0, 0.1), 50, 9.0)
    elif nb == 10:                                          # water: the glass under the tap fills
        room_mode(man=False); lv = smooth(0.0, 0.95, u); S.view_settings.exposure = -1.3
        WATER.scale = (1, 1, 0.012 + 0.1 * lv); STREAM.hide_render = False; top = GL.z + 0.0085 + 0.012 + 0.1 * lv
        STREAM.location = (GL.x, GL.y, top - 0.002); STREAM.scale = (1 + 0.15 * math.sin(t * 40), 1 + 0.15 * math.cos(t * 33), (SK.z + 0.24) - top + 0.002)
        look(GL + V3(-0.42, -0.36, 0.22).lerp(V3(-0.34, -0.3, 0.2), smooth(0, 1, u)), GL + V3(0, 0, 0.09), 50, 4.0)
    else:                                                   # back at the counter: the pain starts, his hand goes to his side (= frame one)
        room_mode()
        cp, ct, ln = CAM0; k = smooth(0.0, 0.9, u)
        look(V3(-1.5, -2.5, 1.2).lerp(cp, k) + shake(t, 0.004), V3(0.08, -0.15, 1.0).lerp(ct, k), lerp(34, ln, k), 5.6, focus=rw((0, 0, 1.1)))

