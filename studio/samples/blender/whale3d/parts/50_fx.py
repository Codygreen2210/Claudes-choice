
# ================================================================ effects: a school of sand lance the whale is feeding on, the diver's bubbles, the
# splash when the whale breaks the surface, a measuring bar across the open mouth, the throat ring, and the old-story "man in the belly" vignette.
# ---- the school: slim silver fish in one mesh, moved every frame
FISHM = mat('fish', (0.72, 0.76, 0.80), 0.18, metal=0.85, coat=0.6)
FISH_N = 360; _rf = random.Random(21); FISH = []
_fv = []; _ff = []
for i in range(FISH_N):
    b0 = len(_fv); _fv += [(0, 0, 0)] * 6
    _ff += [(b0, b0 + 1, b0 + 2), (b0, b0 + 2, b0 + 3), (b0, b0 + 3, b0 + 4), (b0, b0 + 4, b0 + 1), (b0 + 2, b0 + 5, b0 + 3), (b0 + 4, b0 + 5, b0 + 1)]
    FISH.append((_rf.random(), _rf.random(), _rf.random(), _rf.uniform(0.12, 0.2)))
SCHOOL = mesh('school', _fv, _ff, FISHM, smooth_=False)
def set_school(t, center, radius, swirl=0.6, scatter_from=None, scatter=0.0, gulp=None, gulp_k=0.0, on=1.0):
    co = []; nshow = int(FISH_N * on)
    for i, (a_, b_, c_, L_) in enumerate(FISH):
        if i >= nshow: co.extend((0, 0, -500) * 6); continue
        ang = 2 * math.pi * a_ + swirl * t * (0.8 + 0.4 * b_); rr = radius * (0.35 + 0.65 * b_ ** 0.5)
        p = Vector(center) + Vector((rr * math.cos(ang), rr * math.sin(ang) * 0.8, (c_ - 0.5) * radius * 0.7 + 0.3 * math.sin(t * 1.3 + i)))
        d = Vector((-math.sin(ang), math.cos(ang) * 0.8, 0.05 * math.cos(t + i))).normalized()
        if scatter_from is not None and scatter > 0:
            away = (p - Vector(scatter_from)); dist = away.length + 1e-3; push = scatter * 6.0 / (1 + 0.15 * dist)
            p = p + away.normalized() * push; d = (d + away.normalized() * scatter * 2).normalized()
        if gulp is not None and gulp_k > 0 and h1(i * 3.1) < 0.55:
            p = p.lerp(Vector(gulp) + Vector(((h1(i) - 0.5) * 1.5, (h1(i + 7) - 0.5) * 1.5, (h1(i + 9) - 0.5))), gulp_k);
        s_ = d.cross(Vector((0, 0, 1))).normalized(); u_ = s_.cross(d)
        nose = p + d * L_ * 0.5; tail = p - d * L_ * 0.5
        co.extend((*nose, *(p + s_ * L_ * 0.08), *(p + u_ * L_ * 0.12), *(p - s_ * L_ * 0.08), *(p - u_ * L_ * 0.1), *(tail + u_ * L_ * 0.06 * math.sin(t * 20 + i))))
    SCHOOL.data.vertices.foreach_set('co', co); SCHOOL.data.update()
# ---- bubbles: from the regulator, wobbling up, growing
BUBM = mat('bubble', (0.9, 0.95, 1.0), 0.0, trans=1.0, ior=1.0 / 1.33, coat=0.0)
BUBS = [prim('uv_sphere', f'bub{j}', BUBM, radius=1.0, segments=12, ring_count=8) for j in range(40)]
def set_bubbles(t, src, on=True, rate=1.0, ceiling=SEA_Z - 0.1, spread=1.0):
    for j, o in enumerate(BUBS):
        per = 2.6; ph = ((t * rate + j * per / len(BUBS)) % per) / per
        burst = int((t * rate + j * per / len(BUBS)) / per)
        p = Vector(src) + Vector((0.25 * wob(t, 2.0, j) * ph * spread, 0.25 * wob(t, 2.2, j + 5) * ph * spread, 4.5 * ph))
        r_ = (0.012 + 0.03 * h1(j + burst * 13)) * (1 + 1.5 * ph)
        o.location = p; o.scale = (r_ * 1.2, r_ * 1.2, r_ * 0.8)
        o.hide_render = (not on) or p.z > ceiling or h1(j * 7 + burst) > 0.85
# ---- the splash: white water thrown up as the head breaks the surface, falling back, and a foam patch
SPRAYM = mat('spray', (0.95, 0.97, 1.0), 0.1, trans=0.6, ior=1.33)
FOAMM = mat('foam', (0.92, 0.94, 0.95), 0.6); _nt = FOAMM.node_tree; _out = _nt.nodes['Material Output']; _src = _out.inputs['Surface'].links[0].from_socket
_tr = _nt.nodes.new('ShaderNodeBsdfTransparent'); _mx = _nt.nodes.new('ShaderNodeMixShader')
_g = coord(_nt, 'Generated'); _rad = _nt.nodes.new('ShaderNodeVectorMath'); _rad.operation = 'DISTANCE'; _nt.links.new(_g, _rad.inputs[0]); _rad.inputs[1].default_value = (0.5, 0.5, 0.5)
_mask = math_(_nt, 'MULTIPLY', ramp_v(_nt, tnoise(_nt, coord(_nt, 'Object'), 2.5, 8.0, 1.5), 0.45, 0.6), math_(_nt, 'SUBTRACT', 1.0, ramp_v(_nt, _rad.outputs['Value'], 0.25, 0.5)))
_nt.links.new(_mask, _mx.inputs['Fac']); _nt.links.new(_tr.outputs[0], _mx.inputs[1]); _nt.links.new(_src, _mx.inputs[2]); _nt.links.new(_mx.outputs[0], _out.inputs['Surface'])
SPRAY = [prim('ico_sphere', f'spray{j}', SPRAYM, radius=1.0, subdivisions=1) for j in range(160)]
SPRAY_SEED = [(random.Random(j).uniform(0, 2 * math.pi), random.Random(j + 99).uniform(2.0, 8.0), random.Random(j + 7).uniform(1.0, 4.5), random.Random(j + 3).uniform(0.015, 0.06)) for j in range(160)]
FOAM = prim('cylinder', 'foam', FOAMM, radius=1.0, depth=0.05, vertices=48)
def set_splash(t, t0, center, on=True):
    age = t - t0
    for j, o in enumerate(SPRAY):
        ang, up, out, r_ = SPRAY_SEED[j]; a_ = age - 0.25 * h1(j)
        if (not on) or a_ < 0 or a_ > 2.4: o.hide_render = True; continue
        p = Vector(center) + Vector((math.cos(ang) * out * a_, math.sin(ang) * out * a_, up * a_ - 4.9 * a_ * a_))
        o.hide_render = p.z < SEA_Z - 0.3; o.location = p; o.scale = (r_, r_, r_ * 1.4)
    FOAM.hide_render = (not on) or age < 0.1
    if not FOAM.hide_render:
        r_ = 2.5 + 5.0 * smooth(0.0, 2.5, age); FOAM.location = Vector(center) + Vector((0, 0, SEA_Z + 0.06 - center[2])); FOAM.scale = (r_, r_ * 0.8, 1)
# ---- the measuring bar across the open mouth (about 10 ft = 3 m), with arrow ends
MEASM = emis_mix('measure', (1.0, 0.85, 0.15), 6.0, 'alpha')
MEAS = empty('measure_root')
MEAS_BAR = tube('meas_bar', [(0, 0, -1.5), (0, 0, 1.5)], 0.035, MEASM, MEAS, seg=10)
MEAS_TIPS = [prim('cone', f'meas_tip{k}', MEASM, MEAS, loc=(0, 0, s_ * 1.42), rot=(R(0 if s_ > 0 else 180), 0, 0), radius1=0.12, radius2=0.0, depth=0.22, vertices=16) for k, s_ in enumerate((1, -1))]
def set_measure(p0, p1, a_):
    on = a_ > 0.02
    for o in [MEAS_BAR] + MEAS_TIPS: o.hide_render = not on; o['alpha'] = a_
    if not on: return
    c = (Vector(p0) + Vector(p1)) / 2; d = (Vector(p1) - Vector(p0)); MEAS.location = c
    MEAS.rotation_mode = 'QUATERNION'; MEAS.rotation_quaternion = d.to_track_quat('Z', 'Y'); s_ = d.length / 3.0; MEAS.scale = (1, 1, s_ * smooth(0, 1, a_))
# ---- the throat ring: about the size of a fist, stretching to about 15 in (38 cm)
RINGM = emis_mix('ring', (1.0, 0.85, 0.3), 8.0, 'alpha')
RING = prim('cylinder', 'throat_ring', RINGM, radius=1.0, depth=0.02, vertices=48)
RING_IN = prim('cylinder', 'throat_hole', emis('hole', (0.0, 0.0, 0.0), 0.0), radius=0.9, depth=0.03, vertices=48)
FIST = empty('fist_root')
# ---- the old-story vignette: a little man sitting by a fire in the whale's belly (x-ray)
MYTHM = emis_mix('myth', (1.0, 0.75, 0.35), 3.5, 'alpha')
MYTH = empty('myth_root')
MYTH_PARTS = [prim('uv_sphere', 'myth_head', MYTHM, MYTH, loc=(0, 0, 0.72), radius=0.13, segments=14, ring_count=8),
              tube('myth_torso', [(0, 0, 0.6), (0.02, 0, 0.32)], lambda u: 0.11, MYTHM, MYTH, seg=10),
              tube('myth_thighL', [(0.02, 0.08, 0.32), (0.32, 0.1, 0.3), (0.34, 0.1, 0.02)], 0.05, MYTHM, MYTH, seg=8),
              tube('myth_thighR', [(0.02, -0.08, 0.32), (0.32, -0.1, 0.3), (0.34, -0.1, 0.02)], 0.05, MYTHM, MYTH, seg=8),
              tube('myth_armL', [(0.0, 0.12, 0.56), (0.18, 0.18, 0.42), (0.36, 0.1, 0.42)], 0.04, MYTHM, MYTH, seg=8),
              tube('myth_armR', [(0.0, -0.12, 0.56), (0.18, -0.18, 0.42), (0.36, -0.1, 0.42)], 0.04, MYTHM, MYTH, seg=8)]
FIREM = emis_mix('fire', (1.0, 0.45, 0.08), 12.0, 'alpha')
MYTH_FIRE = [prim('cone', f'myth_flame{k}', FIREM, MYTH, loc=(0.75 + 0.06 * k, 0.05 * (k - 1), 0.12), radius1=0.09, radius2=0.0, depth=0.3, vertices=10) for k in range(3)]
STOMACHM = emis_mix('stomach', (0.9, 0.35, 0.3), 1.2, 'alpha')
STOMACH = prim('uv_sphere', 'stomach', STOMACHM, radius=1.0, segments=24, ring_count=14)
def set_myth(t, loc, a_, yaw):
    on = a_ > 0.02
    for o in MYTH_PARTS + MYTH_FIRE + [STOMACH]: o.hide_render = not on; o['alpha'] = a_ * (0.35 if o is STOMACH else 1.0)
    if not on: return
    MYTH.location = loc; MYTH.rotation_euler = (0, 0, yaw); STOMACH.location = Vector(loc) + Vector((0, 0, 0.55)); STOMACH.scale = (1.7, 1.25, 1.1)
    STOMACH.rotation_euler = (0, 0, yaw)
    for k, o in enumerate(MYTH_FIRE): o.scale = (1, 1, 0.8 + 0.4 * abs(wob(t, 9, k)))
