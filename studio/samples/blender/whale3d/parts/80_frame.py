
# ================================================================ the story, frame by frame
# beats: 0 the lunge | 1 it really happened (x-ray, he's inside) | 2 the old story (man in the belly) | 3 mouth opens ~10 ft (ghost jaw + bar)
# 4 throat the size of a fist (ring) | 5 30-40 s in the dark | 6 rises, shakes, spits him out | 7 bruised, no broken bones (x-ray)
# 8 the sperm whale gulps a giant squid whole | 9 it swims past; subscribe
TE = 2.5                                   # the gulp
T_SPIT = B[6] + 1.95
T_SURF = B[6] + 0.95                       # the snout breaks the surface
DIV_IN = Vector((-3.2, 0.0, -1.16))       # his feet inside the closed mouth (whale-local), curled on his back, head toward the snout (cavity measured: x -1.8..-3.8, z -0.45..-1.75)
HIP = float(os.environ.get('HIP', '-70')); KNEE = float(os.environ.get('KNEE', '95'))
DIR0 = Vector((math.cos(R(12)), 0, math.sin(R(12))))
def diver_free(t): return Vector((0.35 * t, 0.0, -11.2))
CATCH_LOCAL = Vector((-2.6, 0.0, -1.1))     # where his feet are in the open mouth at the gulp: low and deep, so the upper jaw passes over his fins
def rotm(yaw, pitch, roll): return Euler((roll, -pitch, yaw), 'XYZ').to_matrix()
S_TE = diver_free(TE) - rotm(0, R(12), 0) @ CATCH_LOCAL
def hb_pose(t):
    """the humpback's pose at t: loc, yaw, pitch, roll, open, engulf, tail, fin"""
    v = 2.6
    if t < TE: s_ = v * (t - TE)
    else: tau = t - TE; s_ = v * 1.4 * (1 - math.exp(-tau / 1.4)) + 0.45 * tau
    loc = S_TE + DIR0 * s_; pitch = R(12); yaw = 0.0; roll = 0.0
    dt_ = max(0.0, TE - t); loc = loc + Vector((0, 0, 0.105 * v * dt_ * dt_ / (dt_ + 0.6)))   # flatter run-in, so the open jaw clears the sand
    open_ = 0.95 * (1 - smooth(TE - 0.35, TE + 0.45, t)); engulf = smooth(TE - 0.5, TE + 0.4, t) * (1 - 0.2 * smooth(TE + 2.0, TE + 5.0, t))
    tail = 0.55 * math.sin(2 * math.pi * 0.42 * t) * (1 if t < TE + 1 else 0.6)
    fin = 0.6 + 0.4 * math.sin(2 * math.pi * 0.3 * t)
    if t > B[6] - 0.2:                                                   # pitch up, power to the surface, shake, spit, sink back
        u = smooth(B[6] - 0.2, B[6] + 1.2, t)
        pitch = lerp(R(12), R(62), u) - R(20) * smooth(T_SPIT + 0.2, T_SPIT + 1.5, t)
        rise = 9.0 * smooth(B[6], T_SURF + 0.5, t) - 2.6 * smooth(T_SPIT + 0.3, T_SPIT + 2.5, t)
        loc = loc + Vector((1.2 * u, 0, rise))
        roll = R(24) * math.sin(2 * math.pi * 1.6 * (t - T_SURF)) * smooth(T_SURF + 0.2, T_SURF + 0.5, t) * (1 - smooth(T_SPIT + 0.2, T_SPIT + 0.6, t))
        open_ = 0.45 * smooth(T_SPIT - 0.45, T_SPIT - 0.15, t) * (1 - smooth(T_SPIT + 0.5, T_SPIT + 1.2, t))
        engulf = engulf * (1 - smooth(T_SPIT - 0.1, T_SPIT + 0.4, t))
        tail = 0.9 * math.sin(2 * math.pi * 0.9 * t) * (1 - smooth(T_SURF, T_SURF + 0.5, t))
    return loc, yaw, pitch, roll, open_, engulf, tail, fin
def hb_matrix(t):
    loc, yaw, pitch, roll = hb_pose(t)[:4]; return Matrix.Translation(loc) @ rotm(yaw, pitch, roll).to_4x4()

# ---- the ghost jaw (beat 3): a glowing copy that swings open while the real one stays shut on him
GHOSTM = bpy.data.materials.new('ghost'); GHOSTM.use_nodes = True; nt = GHOSTM.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
lw_ = nt.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.4
em_ = nt.nodes.new('ShaderNodeEmission'); em_.inputs['Color'].default_value = (1.0, 0.85, 0.25, 1)
nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw_.outputs['Facing'], 1.4), math_(nt, 'MULTIPLY', objattr(nt, 'alpha'), 12.0)), math_(nt, 'MULTIPLY', objattr(nt, 'alpha'), 0.6)), em_.inputs['Strength'])
tr_ = nt.nodes.new('ShaderNodeBsdfTransparent'); ad_ = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr_.outputs[0], ad_.inputs[0]); nt.links.new(em_.outputs[0], ad_.inputs[1])
nt.links.new(ad_.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
GHOST = HB['jaw'].copy(); GHOST.data = HB['jaw'].data.copy(); GHOST.name = 'ghost_jaw'; S.collection.objects.link(GHOST)
GHOST.data.materials.clear(); GHOST.data.materials.append(GHOSTM); GHOST.parent = HB['root']
for c in list(GHOST.children): pass
GHOST.hide_render = True
def jaw_tip_open(a_):
    hx = -HINGE_S * HB_L; hz = hb_mouth(HINGE_S); x_, z_ = 0.12, -0.26; ang = R(58) * a_; dx, dz = x_ - hx, z_ - hz
    return Vector((hx + dx * math.cos(ang) + dz * math.sin(ang), 0.0, hz - dx * math.sin(ang) + dz * math.cos(ang)))

# ---- a dim light inside the mouth so his struggle reads in the dark (beat 5)
MOUTH_LT = light_at('mouth_light', 'POINT', (0, 0, 0), (0, 0, -1), 0.0, (0.55, 0.85, 0.75), 0.4)
# ---- deep water past the drop-off (beats 8-9): darker, bluer, a soft light from above on the sperm whale
DEEPV = bpy.data.materials.new('deep_vol'); DEEPV.use_nodes = True; nt = DEEPV.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
va2 = nt.nodes.new('ShaderNodeVolumeAbsorption'); va2.inputs['Color'].default_value = (0.12, 0.30, 0.55, 1); va2.inputs['Density'].default_value = 0.022
nt.links.new(va2.outputs[0], nt.nodes['Material Output'].inputs['Volume'])
DEEP_X = 48.0
DEEPBOX = box('deep', (500, 600, 260), (DEEP_X + 250 + 6, 0, -14 - 130), DEEPV)
CLIFFM = mat('cliff', (0.14, 0.13, 0.12), 0.9); noisy(CLIFFM, 1.5, 0.45, 0.1)
CLIFF = prim('plane', 'cliff', CLIFFM, loc=(DEEP_X, 0, FLOOR_Z - 60), rot=(0, R(90), 0), size=120)
cs_ = CLIFF.modifiers.new('sub', 'SUBSURF'); cs_.subdivision_type = 'SIMPLE'; cs_.levels = cs_.render_levels = 5
cd_ = CLIFF.modifiers.new('disp', 'DISPLACE'); cd_.texture = tx_; cd_.strength = 2.5
FLOOR.scale = (1.0, 1.0, 1.0); FLOOR.location = (DEEP_X - 200, 0, FLOOR_Z)
SW_LT = light_at('sw_light', 'SPOT', (DEEP_X + 34, -4, 0.0), (DEEP_X + 36, 0, -28), 0.0, (0.6, 0.8, 1.0), 2.0)
SW_LT.data.spot_size = R(70); SW_LT.data.spot_blend = 0.8
FILL_LT = light_at('deep_fill', 'AREA', (0, 0, -30), (1, 0, -30), 0.0, (0.75, 0.88, 1.0), 4.0)
try: FILL_LT.visible_camera = False
except Exception: pass
SW_HOME = Vector((DEEP_X + 40, 4.0, -26.0))
def sw_pose(t):
    t0 = B[8] - 0.3; u = t - t0
    loc = SW_HOME + Vector((-2.2 * u, -0.6 * u, 0.25 * u)); yaw = R(185) + R(4) * math.sin(u * 0.8)
    jaw = smooth(B[8] + 1.2, B[8] + 1.7, t) * (1 - smooth(B[8] + 2.6, B[8] + 3.2, t))
    return loc, yaw, R(-3), 0.0, jaw, 0.5 * math.sin(2 * math.pi * 0.35 * t)

# ---- camera keys: world (lunge, surface, deep) and whale-local (riding along while he's inside)
def key(t, p, q, lens): return (t, Vector(p), Vector(q), lens)
def interp(keys, t):
    if t <= keys[0][0]: k0 = k1 = keys[0]; u = 0.0
    elif t >= keys[-1][0]: k0 = k1 = keys[-1]; u = 0.0
    else:
        i = max(j for j in range(len(keys)) if keys[j][0] <= t); k0, k1 = keys[i], keys[i + 1]; u = sm((t - k0[0]) / (k1[0] - k0[0]))
    c0, c1 = k0[1], k1[1]; a0, a1 = k0[2], k1[2]
    d0 = (a0 - c0).normalized(); d1 = (a1 - c1).normalized(); cp = c0.lerp(c1, u); dr = d0.slerp(d1, u) if d0.dot(d1) > -0.99 else d1
    fl = lerp((a0 - c0).length, (a1 - c1).length, u)
    return cp, cp + dr * fl, lerp(k0[3], k1[3], u)
T_A = 4.6                                  # world -> whale-local
T_B = B[6] + 0.35                          # whale-local -> world (out of the mouth, up to the surface)
LK = [   # whale-local camera keys
    key(T_A, (-0.6, -4.8, 0.2), (-1.8, 0.0, -0.6), 26),                     # the shut mouth from the side (the screen dips to black)
    key(B[1] + 0.2, (-0.9, -5.6, 0.3), (-2.0, 0.0, -0.6), 26),
    key(B[1] + 1.6, (-2.4, -8.6, 0.9), (-3.0, 0.0, -0.45), 28),             # pull back: x-ray, he's in there
    key(B[2] - 0.2, (-2.9, -8.8, 1.0), (-3.6, 0.0, -0.45), 28),
    key(B[2] + 1.1, (-6.2, -6.4, 0.6), (-6.8, 0.0, -0.55), 30),             # along to the belly: the old story
    key(B[3] - 0.3, (-6.4, -6.2, 0.5), (-6.9, 0.0, -0.6), 30),
    key(B[3] + 0.8, (3.6, -6.4, 0.6), (-1.6, 0.0, -1.3), 24),               # front quarter: the mouth's ten-foot gape (ghost)
    key(B[4] - 0.2, (3.7, -6.2, 0.6), (-1.6, 0.0, -1.35), 24),
    key(B[4] + 0.9, (-2.7, -3.3, -0.55), (-3.2, 0.0, -0.9), 30),            # in close, from outside: him, and the fist-sized throat behind his fins
    key(B[5] - 0.25, (-2.9, -3.1, -0.55), (-3.35, 0.0, -0.9), 30),
    key(B[5] + 0.6, (-1.0, -3.4, -0.3), (-2.1, 0.0, -1.0), 26),             # in the dark with him (dim x-ray)
    key(B[6] - 0.3, (-1.3, -3.0, -0.35), (-2.1, 0.0, -1.0), 26),
    key(T_B, (1.6, -5.5, -0.8), (-2.5, 0.0, -0.4), 24),                     # back out as it powers up
]
def world_keys_lunge():
    D0 = diver_free(0.0)
    return [key(0.0, D0 + Vector((4.2, 2.3, -0.45)), D0 + Vector((-1.4, 0.0, -0.85)), 26),          # ahead of him, looking back: the mouth coming up behind
            key(TE - 0.6, diver_free(TE) + Vector((4.2, 2.8, 0.6)), diver_free(TE) + Vector((-1.0, -0.2, -0.3)), 24),
            key(TE + 0.5, diver_free(TE) + Vector((5.5, 6.0, 1.4)), diver_free(TE) + Vector((0.2, 0.0, -0.2)), 22)]
def surf_keys():
    sp = hb_matrix(T_SPIT) @ Vector((0.5, 0, -0.4)); land = DIVER_LAND
    return [key(T_SURF + 0.1, Vector((sp.x + 4.0, sp.y - 8.0, 0.9)), Vector((sp.x, sp.y, 2.2)), 22),      # at the waterline: up it comes
            key(T_SPIT + 0.4, Vector((sp.x + 4.2, sp.y - 8.4, 1.2)), Vector((sp.x + 1.2, sp.y - 1.2, 2.4)), 22),
            key(T_LAND + 0.15, Vector((sp.x + 4.6, sp.y - 8.6, 1.3)), DIVER_LAND + Vector((0, 0, 0.3)), 24),
            key(T_LAND + 1.35, land + Vector((0.8, -1.9, 2.6)), land + Vector((0.9, 0.1, 0.1)), 30),    # down to him floating on his back (after he lands: keys must stay in time order)
            key(B[8] - 0.4, land + Vector((0.9, -1.7, 2.4)), land + Vector((0.9, 0.1, 0.1)), 30)]
def deep_keys():
    land = DIVER_LAND
    return [key(B[8] - 0.4, land + Vector((0.9, -1.7, 2.4)), land + Vector((0.9, 0.1, 0.1)), 30),
            key(B[8] + 0.55, Vector((DEEP_X + 16, -6.0, -18.0)), Vector((DEEP_X + 36, 3.0, -25.0)), 24),   # dive: over the drop-off, into the deep
            key(B[8] + 1.5, Vector((DEEP_X + 27.5, -5.2, -24.2)), Vector((DEEP_X + 37, 3.0, -26.0)), 26),   # it comes at us, jaw dropping, the squid
            key(B[9] - 0.3, Vector((DEEP_X + 27.0, -6.2, -24.5)), Vector((DEEP_X + 33, 3.0, -26.0)), 26),   # x-ray: down the throat
            key(B[9] + 2.6, Vector((DEEP_X + 22, -8.5, -21.5)), Vector((DEEP_X + 28, 2.0, -25.0)), 26),
            key(TOTAL, Vector((DEEP_X + 20.5, -9.0, -19.5)), Vector((DEEP_X + 25, 1.0, -22.0)), 26)]
DIVER_LAND = None
SPIT_LOCAL = Vector((0.6, 0, -0.75))           # just past the lips, low: the slide out stays under the upper jaw
def diver_spit(t):
    p0 = hb_matrix(T_SPIT) @ SPIT_LOCAL; v0 = Vector((3.0, -2.6, 6.5)); tau = t - T_SPIT
    p = p0 + v0 * tau + Vector((0, 0, -4.9 * tau * tau))
    return p
_tl = (v0z := 6.5); _z0 = (hb_matrix(T_SPIT) @ SPIT_LOCAL).z
T_LAND = T_SPIT + (_tl + math.sqrt(_tl * _tl + 2 * 4.9 * max(_z0 - SEA_Z, 0))) / 9.8
DIVER_LAND = Vector((diver_spit(T_LAND).x + 0.6, diver_spit(T_LAND).y - 0.4, SEA_Z + 0.32))
print('T_LAND', round(T_LAND - T_SPIT, 3), flush=True)

def camera(t):
    if t < T_A:
        ks = world_keys_lunge(); M = hb_matrix(T_A)
        ks.append(key(T_A, M @ LK[0][1], M @ LK[0][2], LK[0][3])); return interp(ks, t)
    if t < T_B:
        cp, ct, lens = interp(LK, t); M = hb_matrix(t); return M @ cp, M @ ct, lens
    if t < B[8] - 0.4:
        M = hb_matrix(T_B); ks = [key(T_B, M @ LK[-1][1], M @ LK[-1][2], LK[-1][3])]
        # rise with the head to the surface (just under it), then break out above
        mh = hb_matrix(T_SURF - 0.1) @ Vector((-1.0, 0, 0))
        ks.append(key(T_SURF - 0.25, Vector((mh.x + 4.0, mh.y - 7.5, -0.9)), Vector((mh.x, mh.y, mh.z + 1.0)), 22))
        ks += surf_keys(); return interp(ks, t)
    return interp(deep_keys(), t)

def frame(f):
    t = f / FPS; S.frame_set(f)
    # ---------------- the humpback
    loc, yaw, pitch, roll, open_, engulf, tail, fin = hb_pose(t)
    xr = 0.82 * smooth(B[1] + 0.5, B[1] + 1.4, t) * (1 - smooth(B[6] - 0.25, B[6] + 0.25, t)) * (1 - 0.35 * smooth(B[3] - 0.2, B[3] + 0.3, t) * (1 - smooth(B[4] - 0.2, B[4] + 0.3, t)))
    dark = smooth(B[5] - 0.1, B[5] + 0.6, t) * (1 - smooth(B[6] - 0.3, B[6] + 0.2, t))
    SUN.data.energy = 3.2 * (1 - 0.82 * dark); WBG.inputs['Strength'].default_value = 0.3 * (1 - 0.8 * dark)
    humpback_set(loc, yaw, pitch, roll, open_, engulf, tail, fin, xr=xr)
    on_hb = t < B[8] + 0.6
    for o in [HB['root']] + list(HB['root'].children_recursive):
        if o.type == 'MESH' and o is not GHOST: o.hide_render = not on_hb
    bpy.context.view_layer.update()
    M = hb_matrix(t)
    # ghost jaw + measuring bar (beat 3)
    ga = smooth(B[3] + 0.05, B[3] + 0.5, t) * (1 - smooth(B[4] + 0.1, B[4] + 0.6, t))
    GHOST.hide_render = ga < 0.02; GHOST['alpha'] = ga
    GHOST.data.shape_keys.key_blocks['open'].value = smooth(B[3] + 0.2, B[3] + 1.2, t); GHOST.data.shape_keys.key_blocks['engulf'].value = 0.0
    set_measure(M @ Vector((0.15, 0.0, -0.12)), M @ jaw_tip_open(GHOST.data.shape_keys.key_blocks['open'].value), ga * smooth(B[3] + 0.9, B[3] + 1.3, t))
    # throat ring (beat 4): fist size, stretching to about 15 in
    ra = smooth(B[4] + 0.4, B[4] + 0.8, t) * (1 - smooth(B[5] - 0.2, B[5] + 0.2, t))
    RING.hide_render = RING_IN.hide_render = ra < 0.02; RING['alpha'] = ra
    rr_ = lerp(0.05, 0.19, smooth(B[4] + 1.6, B[4] + 2.6, t))
    if ra >= 0.02:
        rp = M @ Vector((-3.62, 0.0, -0.80)); q_ = (M.to_3x3() @ Vector((1, 0, 0))).to_track_quat('Z', 'Y')
        for o, k in ((RING, 1.0), (RING_IN, 0.86)):
            o.location = rp; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = q_; o.scale = (rr_ * k, rr_ * k, 1.0)
    # the old story (beat 2)
    ma = smooth(B[2] + 0.2, B[2] + 0.7, t) * (1 - smooth(B[3] - 0.25, B[3] + 0.15, t))
    set_myth(t, M @ Vector((-6.9, 0.0, -1.25)), ma, yaw + math.pi * 0.5)
    # ---------------- the diver
    D = DIVER; D.show(True)
    if t < TE - 0.1:
        p = diver_free(t); D.place(p, (1, 0, 0), (0, 0, 1)); D.kick(t, 1.0); D.spine(6, 22)
        D.hands((0.28, -0.42, 1.60), (-0.22, -0.40, 0.95))
    elif t < T_SPIT:
        # scooped: he slides back into the mouth from wherever he was swimming, rolls onto his back and curls up (fits the measured cavity)
        Mi = M.inverted(); R3 = Mi.to_3x3()
        u = smooth(TE - 0.45, TE + 0.55, t)
        ffw = (R3 @ Vector((1, 0, 0))).normalized(); fu = R3 @ Vector((0, 0, 1))
        pl = (Mi @ diver_free(t)).lerp(DIV_IN, u)
        pl = pl.lerp(SPIT_LOCAL, smooth(T_SPIT - 0.22, T_SPIT, t))          # slides out as the mouth opens at the surface
        fw = ffw.lerp(Vector((1, 0, 0.05)), u).normalized()
        up_ = Quaternion(fw, math.pi * u) @ fu
        squirm = smooth(B[5], B[5] + 0.4, t) * (1 - smooth(B[6] - 0.3, B[6], t))
        D.place(M @ pl, M.to_3x3() @ fw, M.to_3x3() @ up_)
        w_ = math.sin(2 * math.pi * 1.6 * t)
        D.legs(lerp(-6, HIP, u) + (1 - u) * 16 * w_ + 4 * squirm * math.sin(t * 5), lerp(20, KNEE, u) + 5 * squirm * math.cos(t * 4), lerp(48, 40, u), 6 * u)
        D.spine(lerp(6, 16, u) + 8 * squirm * math.sin(t * 5), lerp(22, 30, u))
        hl = Vector((0.28, -0.42, 1.60)).lerp(Vector((0.16, -0.30, 1.22)), u); hr = Vector((-0.22, -0.40, 0.95)).lerp(Vector((-0.16, -0.30, 1.22)), u)
        D.hands(tuple(hl + Vector((0, 0.08 * squirm * math.sin(t * 6), 0))), tuple(hr + Vector((0, 0.08 * squirm * math.cos(t * 6), 0))))
    elif t < T_LAND:
        p = diver_spit(t); tau = t - T_SPIT
        D.place(p, (math.cos(tau * 5), 0.4 * math.sin(tau * 3), math.sin(tau * 5)), (0.2, 1.0, 0.3 * math.sin(tau * 4)))
        D.legs(-20 + 30 * math.sin(tau * 9), 35, 40, 12); D.spine(-10, 10)
        D.hands((0.55, -0.1, 1.85), (-0.55, -0.1, 1.85))
    else:
        tau = t - T_LAND; bob = 0.06 * math.sin(t * 1.7)
        p = DIVER_LAND + Vector((0.05 * tau, 0.02 * tau, bob)) + Vector((0, 0, -0.6 * math.exp(-tau * 3)))
        D.place(p, (1, 0.15, 0.0), (0, 0, -1)); D.legs(6, 18, 40, 8); D.spine(-4, -8)
        D.hands((0.40, 0.05, 1.10), (-0.40, 0.05, 1.10))
    dx = smooth(B[7] + 0.4, B[7] + 1.0, t) * (1 - smooth(B[8] - 0.4, B[8] + 0.1, t))
    if t > B[1] and t < B[6]: D.xray(0.8 * smooth(B[1] + 0.5, B[1] + 1.4, t), 0.0, 0.0)
    else: D.xray(0.75 * dx, dx, dx)
    D.show(t < B[8] + 0.8)
    bpy.context.view_layer.update()
    # bubbles from the regulator (under water only)
    head = D.root.matrix_world @ Vector((0, -0.17, 1.46))
    set_bubbles(t, head, on=head.z < SEA_Z - 0.4 and not (TE + 0.1 < t < T_SPIT), rate=1.0)
    # ---------------- the sea, the school, the splash, the boat
    set_school(t, diver_free(0.0) + Vector((1.5, 1.0, 0.8)), 4.5, swirl=0.5, scatter_from=(M @ Vector((-1.5, 0, -0.5))) if t > 1.2 else None,
               scatter=smooth(1.4, TE, t), gulp=M @ Vector((-2.0, 0, -0.8)), gulp_k=smooth(TE - 0.6, TE, t) * (1 - smooth(TE + 0.2, TE + 0.3, t)), on=1.0 if t < B[3] else 0.0)
    SCHOOL.hide_render = t > B[3]
    set_splash(t, T_SURF + 0.05, hb_matrix(T_SURF + 0.3) @ Vector((0.0, 0, 0)), on=T_SURF < t < B[8])
    oc.time = 2.0 + t * 0.9
    GOBO_MAP.inputs['Location'].default_value = (t * 0.35, t * 0.18, 0.0); GOBO_W.default_value = t * 0.35
    BOAT.location = DIVER_LAND + Vector((13.0 - 1.5 * smooth(B[7], B[8], t), 11.0, SEA_Z - DIVER_LAND.z)); BOAT.rotation_euler = (R(2) * math.sin(t), R(1.5) * math.sin(t * 1.3), R(-30))
    FLOAT.location = DIVER_LAND + Vector((-3.0, 4.0, SEA_Z - DIVER_LAND.z + 0.05 * math.sin(t * 1.5)))
    for o, j in WEED:
        o.rotation_euler = (R(4) * math.sin(t * 0.8 + j), R(4) * math.cos(t * 0.7 + j), 0)
    # ---------------- the deep: the sperm whale and the giant squid
    deep_on = t > B[8] - 0.4
    sperm_show(deep_on); squid_show(deep_on)
    SW_LT.data.energy = 90000.0 * smooth(B[8] - 0.2, B[8] + 0.6, t); FILL_LT.data.energy = 9000.0 * smooth(B[8] + 0.2, B[8] + 0.8, t)
    if deep_on:
        sl, sy, sp_, sr, sj, stl = sw_pose(t)
        swx = smooth(B[8] + 2.6, B[8] + 3.1, t)
        sperm_set(sl, sy, sp_, sr, sj, stl, xr=0.8 * swx, throat=swx)
        bpy.context.view_layer.update()
        Ms = SW['root'].matrix_world
        SW_LT.location = Ms @ Vector((-3.0, -2.5, 7.5)); SW_LT.rotation_mode = 'QUATERNION'; SW_LT.rotation_quaternion = (Ms @ Vector((-4.0, 0, -1.0)) - SW_LT.location).to_track_quat('-Z', 'Y')   # after the update, so a chunk's first frame isn't lit from the old pose
        g = smooth(B[8] + 1.55, B[8] + 2.6, t)                             # the squid: in front of the jaw, then pulled in and down the throat
        sq0 = Ms @ Vector((3.6, 0.6, -1.2)); sq1 = Ms @ Vector((-SW_HINGE * SW_L - 1.5, 0, -0.6)); sq2 = Ms @ Vector((-SW_HINGE * SW_L - 5.5, 0, -0.4))
        sq = sq0.lerp(sq1, g).lerp(sq2, smooth(B[8] + 2.7, B[9] + 1.5, t))
        heading = (Ms.to_3x3() @ Vector((-1, 0, 0)))
        squid_set(sq, (0, 0, math.atan2(heading.y, heading.x) + math.pi), t, curl=1.0 - 0.7 * g, xr=0.0, scale=1.0)
    else:
        sperm_set(SW_HOME, xr=0.0)
    # ---------------- light inside the mouth (only while we're in there), camera
    MOUTH_LT.location = M @ Vector((-0.8, 0.2, -0.6)); MOUTH_LT.data.energy = 40.0 * smooth(B[5] - 0.2, B[5] + 0.3, t) * (1 - smooth(B[6] - 0.2, B[6] + 0.3, t))
    cp, ct, lens = camera(t)
    if t > B[8]: FILL_LT.location = cp + (cp - ct).normalized() * 1.5 + Vector((0, 0, 2.0)); FILL_LT.rotation_mode = 'QUATERNION'; FILL_LT.rotation_quaternion = (ct - FILL_LT.location).to_track_quat('-Z', 'Y')
    if os.environ.get('DBGPOS'): print('DBG t', round(t,2), 'whale', tuple(round(x,2) for x in HB['root'].matrix_world.translation), 'Mcalc', tuple(round(x,2) for x in M.translation), 'diver', tuple(round(x,2) for x in DIVER.root.matrix_world.translation), 'rig', tuple(round(x,2) for x in DIVER.rig.matrix_world.translation), flush=True)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = Vector(q_[0:3]), Vector(q_[3:6]), q_[6]
    sh = shake(t, 0.05 * smooth(TE - 0.3, TE, t) * (1 - smooth(TE + 0.4, TE + 1.0, t)) + 0.06 * smooth(T_SURF - 0.1, T_SURF, t) * (1 - smooth(T_SPIT + 0.5, T_SPIT + 1.2, t)), 3.0)
    look(cp + sh, ct + sh, lens, 11.0)
    S.view_settings.exposure = -0.9 * smooth(-0.3, 0.3, cp.z - SEA_Z) - 7.0 * smooth(TE + 1.6, TE + 2.1, t) * (1 - smooth(TE + 2.4, TE + 3.0, t))
