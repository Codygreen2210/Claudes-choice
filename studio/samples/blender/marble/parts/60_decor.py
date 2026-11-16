# ================================================================ decor (render only): LED rails, thickness, supports, floor, signs, tower, ring, arches
def no_light(m):
    try: m.cycles.emission_sampling = 'NONE'
    except Exception: pass
    return m
if not a.sim:
    for m_ in LED.values(): no_light(m_)
    for o in PHYS:
        if o.name.startswith(('start', 'bumps', 'zigzag', 'drop', 'land', 'halfpipe', 'pipe_', 'lanes', 'helix', 'to_vortex', 'rollers', 'finish', 'vortex')):
            sd = o.modifiers.new('thick', 'SOLIDIFY'); sd.thickness = 0.022; sd.offset = -1.0 if not o.name.startswith('vortex') else 1.0
            sd.use_even_offset = True
            bv = o.modifiers.new('bv', 'BEVEL'); bv.width = 0.006; bv.segments = 2; bv.limit_method = 'ANGLE'
    # LED rails along every lip (a thin glowing tube) + a chrome rim under it
    rim_m = mat('rim', (0.8, 0.8, 0.85), 0.18, 1.0)
    def rail(pts, m, r, nm):
        pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
        if len(pts) > 2: tube(nm, [tuple(p) for p in pts], r, m, seg=8)
    for k_, (lp, rp, led) in enumerate(LIPS):
        for side_, pts in (('L', lp), ('R', rp)):
            rail(pts, rim_m, 0.011, f'rim{k_}{side_}')
            rail([p + Vector((0, 0, 0.012)) for p in pts], LED[led or 'white'], 0.0055, f'led{k_}{side_}')
    # supports: a cradle bar under the track every ~1.5 m and a steel post down to the floor where nothing is underneath
    from mathutils import kdtree
    KD = kdtree.KDTree(len(SAMPLES_ALL))
    for i_, p_ in enumerate(SAMPLES_ALL): KD.insert(p_, i_)
    KD.balance()
    FLOOR = LMK['floor_z']
    steel = mat('steel', (0.55, 0.56, 0.6), 0.32, 1.0); noisy(steel, 30, 0.08, 0.08)
    yel = mat('yellow_paint', (0.9, 0.55, 0.02), 0.4, 0.0, coat=0.3)
    posts_v, posts_f = [], []
    def post(x, y, z0, z1, r=0.022, seg=8):
        b0 = len(posts_v)
        for k in range(seg):
            a_ = 2 * math.pi * k / seg; posts_v.append((x + r * math.cos(a_), y + r * math.sin(a_), z0)); posts_v.append((x + r * math.cos(a_), y + r * math.sin(a_), z1))
        for k in range(seg): k2 = (k + 1) % seg; posts_f.append((b0 + 2 * k, b0 + 2 * k2, b0 + 2 * k2 + 1, b0 + 2 * k + 1))
    def clear_below(p, r=0.5):
        for (co, idx, dist) in KD.find_range(p, 30.0):
            if co[2] < p[2] - 0.15 and math.hypot(co[0] - p[0], co[1] - p[1]) < r: return False
        return True
    for nm_, smp in [(k, v) for k, v in LMK.items() if k in ('start', 'bumps', 'zigzag', 'halfpipe', 'lanes', 'helix', 'rollers', 'finish')]:
        for j in range(0, len(smp), 40):
            s_ = smp[j]; bot = s_['p'] - Vector((0, 0, 0.03)); wd = s_['w'] + s_['rc'] + 0.03
            box('cradle', (0.05, 2 * wd, 0.03), tuple(bot), steel, rot=(0, 0, s_['h']))
            if j % 80 == 0:
                for sv in (-wd, wd):
                    q = bot + s_['side'] * sv
                    if clear_below(q): post(q.x, q.y, FLOOR, q.z)
    # floor: dark polished concrete with a faint grid, huge
    cx = sum(p_[0] for p_ in SAMPLES_ALL) / len(SAMPLES_ALL); cy = sum(p_[1] for p_ in SAMPLES_ALL) / len(SAMPLES_ALL)
    fm = bpy.data.materials.new('floor'); fm.use_nodes = True; nt = fm.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.22; b.inputs['Base Color'].default_value = (0.02, 0.022, 0.028, 1)
    tc_ = coord(nt, 'Object'); br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 0.5; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Color1'].default_value = (0.022, 0.024, 0.03, 1); br.inputs['Color2'].default_value = (0.018, 0.02, 0.025, 1); br.inputs['Mortar'].default_value = (0.0, 0.25, 0.45, 1)
    nt.links.new(tc_, br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    em_ = math_(nt, 'MULTIPLY', br.outputs['Fac'], 0.35)
    b.inputs['Emission Color'].default_value = (0.0, 0.35, 0.7, 1); nt.links.new(em_, b.inputs['Emission Strength'])
    no_light(fm)
    flo = prim('plane', 'floor', fm, loc=(cx, cy, FLOOR), size=400.0)
    # far walls: a dark arena ring with rows of small lights (depth cue), well outside the course
    arena = bpy.data.materials.new('arena'); arena.use_nodes = True; nt = arena.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); sx_ = sepz(nt, coord(nt, 'Object'))
    hz = math_(nt, 'POWER', math_(nt, 'ABSOLUTE', math_(nt, 'SINE', math_(nt, 'MULTIPLY', sx_.outputs['Z'], 0.22))), 400.0)
    zf = math_(nt, 'MULTIPLY', hz, math_(nt, 'LESS_THAN', sx_.outputs['Z'], FLOOR + 30))
    cc_ = mixc(nt, zf, (0.004, 0.006, 0.012), (0.05, 0.11, 0.24)); nt.links.new(cc_, e_.inputs['Color']); e_.inputs['Strength'].default_value = 1.0
    nt.links.new(e_.outputs[0], nt.nodes['Material Output'].inputs['Surface']); no_light(arena)
    ar = lathe('arena', [(85, FLOOR), (85, FLOOR + 60)], 96, arena, loc=(cx, cy, 0))
    # lights: big soft overheads so the track reads, cool rim from the far side; the marbles do the rest
    WBG.inputs['Color'].default_value = (0.006, 0.008, 0.016, 1); WBG.inputs['Strength'].default_value = 1.0
    for k, (dx, dy) in enumerate(((-15, -6), (5, 3), (-30, 14), (-40, 22), (-25, 8))):
        light_at(f'over{k}', 'AREA', (cx + dx, cy + dy, 40), (cx + dx, cy + dy, 0), 9000, (0.75, 0.82, 1.0), size=14)
    # the tower in the helix: a tall frosted column with glowing blue bands
    tx, ty, tz0, tz1 = LMK['tower']
    tw = mat('tower', (0.05, 0.08, 0.15), 0.25, 0.3)
    lathe('tower', [(0.0, FLOOR), (1.15, FLOOR), (1.15, tz1 + 0.6), (0.9, tz1 + 1.0), (0.0, tz1 + 1.1)], 64, tw, loc=(tx, ty, 0))
    tb = no_light(emis('tower_led', (0.15, 0.45, 1.0), 5.0))
    zz_ = FLOOR + 0.8
    while zz_ < tz1 + 0.5:
        lathe('tband', [(1.16, zz_), (1.18, zz_ + 0.02), (1.18, zz_ + 0.08), (1.16, zz_ + 0.1)], 64, tb, loc=(tx, ty, 0)); zz_ += 0.7
    # LED rings round both funnel rims
    for key in ('vortex1', 'vortex2'):
        c_ = LMK[key]; Rf_ = 1.25 if key == 'vortex1' else 1.9
        lathe(key + '_ring', [(Rf_ + 0.005, c_.z + 0.30), (Rf_ + 0.02, c_.z + 0.31), (Rf_ + 0.02, c_.z + 0.33)], 96, LED['pink' if key == 'vortex2' else 'orange'], loc=(c_.x, c_.y, 0))
        lathe(key + '_skirt', [(Rf_ + 0.01, c_.z - 0.2), (Rf_ + 0.01, c_.z + 0.30)], 96, steel, loc=(c_.x, c_.y, 0))
        if clear_below(c_, 0.6): post(c_.x, c_.y, FLOOR, c_.z - (1.0 if key == 'vortex1' else 1.3), r=0.06, seg=12)
    # glowing hoop over the final jump, at the top of the marbles' flight
    try:
        sim_ = np.load(os.path.join(HERE, 'sim.npz')); P_ = sim_['pos']; k3 = np.array(tuple(LMK['kick3'])); h3 = LMK['kick3_h']
        fw3 = np.array([math.cos(h3), math.sin(h3), 0]); apex = []
        for i in range(NM):
            ah = (P_[:, i] - k3) @ fw3; ok = np.where((ah > 0.2) & (ah < 1.4) & (np.linalg.norm(P_[:, i, :2] - k3[:2], axis=1) < 1.6))[0]
            if len(ok): apex.append(P_[ok[np.argmax(P_[ok, i, 2])], i])
        ap_ = np.mean(apex, axis=0); LMK['hoop'] = Vector(tuple(ap_))
        hoop_m = no_light(emis('hoop', (1.0, 0.35, 0.02), 9.0))
        bm_ = bmesh.new(); bmesh.ops.create_circle(bm_, segments=64, radius=0.42)
        pts_ = [Vector(tuple(ap_)) + Vector((0, 0, 0)) + Vector((-math.sin(h3), math.cos(h3), 0)) * 0.42 * math.cos(2 * math.pi * k / 64) + Vector((0, 0, 0.42)) * math.sin(2 * math.pi * k / 64) for k in range(65)]
        bm_.free(); tube('hoop', [tuple(p) for p in pts_], 0.025, hoop_m, seg=10, caps=False)
    except Exception as e_: print('hoop skipped', e_)
    # arches: START and FINISH, with a checkered line on the finish
    def arch(s_, text, col, wd=0.75, hgt=0.75):
        q0 = s_['p'] + s_['side'] * -wd; q1 = s_['p'] + s_['side'] * wd
        for q in (q0, q1): box('arch_post', (0.06, 0.06, hgt), tuple(q + Vector((0, 0, hgt / 2 - 0.02))), steel)
        box('arch_bar', (0.08, 2 * wd + 0.06, 0.16), tuple(s_['p'] + Vector((0, 0, hgt))), steel, rot=(0, 0, s_['h']))
        tx_ = bpy.data.curves.new('t_' + text, 'FONT'); tx_.body = text; tx_.align_x = 'CENTER'; tx_.align_y = 'CENTER'; tx_.size = 0.13; tx_.extrude = 0.004
        to = bpy.data.objects.new('t_' + text, tx_); S.collection.objects.link(to); to.data.materials.append(no_light(emis('tm_' + text, col, 6.0)))
        to.location = s_['p'] + Vector((0, 0, hgt)) - s_['T'] * 0.045; to.rotation_euler = (math.pi / 2, 0, s_['h'] - math.pi / 2)
        to2 = to.copy(); S.collection.objects.link(to2); to2.location = s_['p'] + Vector((0, 0, hgt)) + s_['T'] * 0.045; to2.rotation_euler = (math.pi / 2, 0, s_['h'] + math.pi / 2)
    arch(LMK['start'][2], 'START', (0.2, 1.0, 0.3), wd=0.62)
    fl_ = LMK['finish_line']; arch(fl_, 'FINISH', (1.0, 1.0, 1.0), wd=0.62)
    ck = bpy.data.materials.new('checker'); ck.use_nodes = True; nt = ck.node_tree; b = nt.nodes['Principled BSDF']
    cb = nt.nodes.new('ShaderNodeTexChecker'); cb.inputs['Scale'].default_value = 1.0; cb.inputs['Color1'].default_value = (0.9, 0.9, 0.9, 1); cb.inputs['Color2'].default_value = (0.01, 0.01, 0.01, 1)
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (14, 14, 14); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector']); nt.links.new(mp.outputs[0], cb.inputs['Vector'])
    nt.links.new(cb.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.3
    stripe = prim('plane', 'finish_stripe', ck, loc=tuple(fl_['p'] + fl_['up'] * 0.004), scale=(0.14 / 2, (fl_['w'] + 0.05), 1), size=2.0)
    stripe.rotation_mode = 'QUATERNION'; stripe.rotation_quaternion = Matrix((fl_['T'], fl_['side'], fl_['up'])).transposed().to_quaternion()
    # section signs: glowing word panels beside each feature
    SIGNS = [('zigzag', 'ZIGZAG', 'cyan'), ('kick1', 'JUMP!', 'orange'), ('vortex1', 'VORTEX', 'orange'), ('halfpipe', 'HALF-PIPE', 'purple'),
             ('corkscrew', 'CORKSCREW', 'purple'), ('plinko', 'PLINKO', 'green'), ('lanes', 'PICK A LANE', 'green'), ('kick2', 'BIG JUMP', 'orange'),
             ('helix', 'THE TOWER', 'blue'), ('vortex2', 'MEGA VORTEX', 'pink'), ('rollers', 'ROLLERS', 'yellow'), ('kick3', 'FINAL JUMP', 'orange')]
    panel_m = mat('panel', (0.02, 0.02, 0.03), 0.35, 0.2)
    def sign_at(pos, hdg, text, led, size=0.22):
        tx_ = bpy.data.curves.new('s_' + text, 'FONT'); tx_.body = text; tx_.align_x = 'CENTER'; tx_.align_y = 'CENTER'; tx_.size = size; tx_.extrude = 0.006
        to = bpy.data.objects.new('s_' + text, tx_); S.collection.objects.link(to); to.data.materials.append(LED[led])
        to.location = pos; to.rotation_euler = (math.pi / 2, 0, hdg)
        tb_ = to.copy(); S.collection.objects.link(tb_); tb_.location = pos - Vector((math.sin(hdg), -math.cos(hdg), 0)) * 0.06; tb_.rotation_euler = (math.pi / 2, 0, hdg + math.pi)
        wdt = 0.14 * size * len(text) * 4.6
        box('panel', (wdt, 0.03, size * 1.7), tuple(pos - Vector((math.sin(hdg), -math.cos(hdg), 0)) * 0.03), panel_m, rot=(0, 0, hdg))
        post(pos.x - math.sin(hdg) * 0.06, pos.y + math.cos(hdg) * 0.06, FLOOR, pos.z - size * 0.85, r=0.03)
    for key, text, led in SIGNS:
        v_ = LMK[key]
        if isinstance(v_, list): s_ = v_[len(v_) // 6]; base = s_['p']; hh_ = s_['h']; sd_ = s_['side']
        elif isinstance(v_, tuple): base = Vector(v_[0]); hh_ = 0.0; sd_ = Vector((0, -1, 0))
        else: base = Vector(v_); hh_ = LMK.get(key + '_h', 0.0); sd_ = Vector((math.sin(hh_), -math.cos(hh_), 0))
        if key.startswith('vortex'): pos = base + Vector((0, 0, 1.0)); hh_ = 0.0
        elif key == 'helix': tx0, ty0, _, tz1_ = LMK['tower']; pos = Vector((tx0, ty0, tz1_ + 1.6)); hh_ = 0.0
        else: pos = base + sd_ * -1.0 + Vector((0, 0, 0.55))
        LMK['sign_' + key] = pos
        sign_at(pos, 0.0 if key.startswith(('vortex', 'helix')) else hh_ + math.pi, text, led)
    if posts_v: mesh('posts', posts_v, posts_f, steel, smooth_=True)
