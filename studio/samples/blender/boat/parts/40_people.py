
# ================================================================ people: the house MakeHuman man (man.blend), posed on his rig and BAKED into
# shared meshes (one per pose and phase), so a crowd costs one mesh per pose. Clothes recoloured per person (object-level materials).
# A life vest is a shell of his own shirt pushed out (it deforms with him, so nothing pokes through).
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
MANCOL = bpy.data.collections.new('man_src'); S.collection.children.link(MANCOL)
for o in _dst.objects: MANCOL.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HAIR = bpy.data.objects['Human.short02']; EYES = bpy.data.objects['Human.high-poly']
LASH = bpy.data.objects['Human.eyelashes01']; BROW = bpy.data.objects['Human.eyebrow001']
PB = RIG.pose.bones
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
for o in MANCOL.objects: o.hide_render = True; o.hide_viewport = False
SHORTS_SRC = SUIT.data.materials[0]; SHIRT_SRC = SHORTS_SRC.copy(); SHIRT_SRC.name = 'shirt_src'; SUIT.data.materials.append(SHIRT_SRC)
for p_ in SUIT.data.polygons:
    if sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) > 0.93: p_.material_index = 1
def retint(m, col, keep=0.35, rough=0.9, sheen=0.4):
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    src = lk.from_socket if lk else None
    bw = nt.nodes.new('ShaderNodeRGBToBW'); mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - keep; mr.inputs['To Max'].default_value = 1.0 + keep * 0.3
    if src: nt.links.new(src, bw.inputs['Color']); nt.links.new(bw.outputs['Val'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mul.inputs['A'])
    else: mul.inputs['A'].default_value = (1, 1, 1, 1)
    mul.inputs['B'].default_value = (*col, 1); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Tint'].default_value = (*col, 1)
    return m
# the vest: his shirt's torso faces (not the sleeves), pushed out along their normals, bright orange with a reflective band
_vgn = {g.index: g.name for g in SUIT.vertex_groups}
_ARM = {b_ + s_ for s_ in ('.L', '.R') for b_ in ('clavicle', 'shoulder01', 'upperarm01', 'upperarm02', 'lowerarm01', 'lowerarm02', 'wrist')}
def _armw(v): return sum(g.weight for g in v.groups if _vgn.get(g.group, '') in _ARM)
_vf = [p_.index for p_ in SUIT.data.polygons if 1.0 < sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) < 1.42
       and max(_armw(SUIT.data.vertices[i]) for i in p_.vertices) < 0.25]
_bm = bmesh.new(); _bm.from_mesh(SUIT.data); _keep = set(_vf)
bmesh.ops.delete(_bm, geom=[f for f in _bm.faces if f.index not in _keep], context='FACES')
_bm.normal_update()
for v in _bm.verts: v.co += v.normal * 0.028
_vm = bpy.data.meshes.new('vest'); _bm.to_mesh(_vm); _bm.free()
VEST = bpy.data.objects.new('vest', _vm); MANCOL.objects.link(VEST); VEST.parent = SUIT.parent; VEST.matrix_world = SUIT.matrix_world.copy()
for g in SUIT.vertex_groups: VEST.vertex_groups.new(name=g.name)
_md = VEST.modifiers.new('arm', 'ARMATURE'); _md.object = RIG
_sol = VEST.modifiers.new('thick', 'SOLIDIFY'); _sol.thickness = 0.03; _sol.offset = 1.0
VEST_M = mat('lifevest', (1.0, 0.28, 0.02), 0.55)
_vn = VEST_M.node_tree; _vb = _vn.nodes['Principled BSDF']; _vz = sepz(_vn, coord(_vn, 'Object')).outputs['Z']
_band = math_(_vn, 'MULTIPLY', math_(_vn, 'GREATER_THAN', _vz, 1.18), math_(_vn, 'LESS_THAN', _vz, 1.23))
_vn.links.new(mixc(_vn, _band, (1.0, 0.28, 0.02), (0.92, 0.92, 0.90)), _vb.inputs['Base Color'])
VEST.data.materials.append(VEST_M); VEST.hide_render = True

# ---- poses: bone rotations (radians). Front is -Y; legs swing forward with -X, arms forward with +X, L arm out with +Z, R arm out with -Z
POSE_BONES = ['upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'upperarm01.L', 'upperarm01.R', 'lowerarm01.L', 'lowerarm01.R', 'spine01', 'spine03', 'neck01', 'foot.L', 'foot.R']
def set_pose(d):
    for n in POSE_BONES:
        b = PB[n]; b.rotation_mode = 'XYZ'; b.rotation_euler = d.get(n, (0, 0, 0))
def p_stand(ph=0.0):
    return {'upperarm01.L': (0.05 * math.sin(ph), 0, -0.38), 'upperarm01.R': (0.05 * math.sin(ph + 1), 0, 0.38), 'lowerarm01.L': (0.15, 0, 0), 'lowerarm01.R': (0.15, 0, 0)}
def p_gait(ph, leg, knee, arm, elbow, lean):
    s_ = math.sin(ph)
    return {'upperleg01.L': (-leg * s_, 0, 0), 'upperleg01.R': (leg * s_, 0, 0),
            'lowerleg01.L': (knee * max(0.0, math.sin(ph - 1.2)) + 0.1, 0, 0), 'lowerleg01.R': (knee * max(0.0, math.sin(ph + math.pi - 1.2)) + 0.1, 0, 0),
            'upperarm01.L': (-arm * s_, 0, -0.42), 'upperarm01.R': (arm * s_, 0, 0.42), 'lowerarm01.L': (elbow, 0, 0), 'lowerarm01.R': (elbow, 0, 0),
            'spine01': (lean, 0, 0)}
def p_brace(ph=0.0):
    return {'upperarm01.L': (0.5, 0, 0.25 + 0.08 * math.sin(ph)), 'upperarm01.R': (0.5, 0, -0.25 - 0.08 * math.sin(ph)), 'lowerarm01.L': (0.9, 0, 0), 'lowerarm01.R': (0.9, 0, 0),
            'upperleg01.L': (-0.25, 0, 0.06), 'upperleg01.R': (-0.25, 0, -0.06), 'lowerleg01.L': (0.45, 0, 0), 'lowerleg01.R': (0.45, 0, 0), 'spine01': (0.15, 0, 0)}
def p_climb(ph):
    s_ = math.sin(ph)
    return {'upperarm01.L': (1.9 + 0.35 * s_, 0, -0.2), 'upperarm01.R': (1.9 - 0.35 * s_, 0, 0.2), 'lowerarm01.L': (0.6, 0, 0), 'lowerarm01.R': (0.6, 0, 0),
            'upperleg01.L': (-0.5 - 0.3 * s_, 0, 0), 'upperleg01.R': (-0.2 + 0.3 * s_, 0, 0), 'lowerleg01.L': (0.7, 0, 0), 'lowerleg01.R': (0.4, 0, 0), 'spine01': (0.3, 0, 0)}
def p_tread(ph):
    s_ = math.sin(ph); c_ = math.cos(ph)
    return {'upperarm01.L': (0.4 + 0.35 * s_, 0, 0.55 + 0.3 * c_), 'upperarm01.R': (0.4 - 0.35 * s_, 0, -0.55 - 0.3 * c_), 'lowerarm01.L': (0.5, 0, 0), 'lowerarm01.R': (0.5, 0, 0),
            'upperleg01.L': (-0.4 - 0.3 * s_, 0, 0.1), 'upperleg01.R': (-0.4 + 0.3 * s_, 0, -0.1), 'lowerleg01.L': (0.9 + 0.3 * c_, 0, 0), 'lowerleg01.R': (0.9 - 0.3 * c_, 0, 0)}
def p_jump(ph=0.0):
    return {'upperarm01.L': (2.7, 0, 0.1), 'upperarm01.R': (2.7, 0, -0.1), 'lowerarm01.L': (0.1, 0, 0), 'lowerarm01.R': (0.1, 0, 0),
            'upperleg01.L': (-0.9, 0, 0.05), 'upperleg01.R': (-0.6, 0, -0.05), 'lowerleg01.L': (1.3, 0, 0), 'lowerleg01.R': (1.0, 0, 0), 'spine01': (0.25, 0, 0)}
def p_wave(ph):
    d = p_stand(); d['upperarm01.R'] = (0.3, 0, -2.5); d['lowerarm01.R'] = (0.2, 0, -0.45 * math.sin(ph) - 0.2); return d
POSES = {'stand': (1, p_stand), 'walk': (6, lambda ph: p_gait(ph, 0.42, 0.7, 0.35, 0.3, 0.04)), 'run': (6, lambda ph: p_gait(ph, 0.85, 1.4, 0.8, 1.3, 0.22)),
         'brace': (2, p_brace), 'climb': (4, p_climb), 'tread': (4, p_tread), 'jump': (1, p_jump), 'wave': (4, p_wave)}
PARTS = [BODY, SUIT, HAIR, EYES, LASH, BROW]
def bake(name, vest):
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); mats = []
    for o in PARTS + ([VEST] if vest else []):
        ev = o.evaluated_get(dg); me = ev.to_mesh(); nf0 = len(bm.faces); nv0 = len(bm.verts)
        bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts[nv0:])
        for f in bm.faces[nf0:]: f.material_index += len(mats); f.smooth = True
        mats += list(o.data.materials); ev.to_mesh_clear()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in mats: me.materials.append(m_)
    return me
BAKED = {}
NEED = {False: ('stand', 'walk', 'run', 'brace', 'tread', 'jump'), True: ('stand', 'brace', 'climb', 'tread', 'wave')}
for vest_, modes in NEED.items():
    for md_ in modes:
        n_, fn = POSES[md_]
        for k in range(n_):
            set_pose(fn(2 * math.pi * k / n_)); bpy.context.view_layer.update(); BAKED[(vest_, md_, k)] = bake(f'man_{md_}{k}{"v" if vest_ else ""}', vest_)
set_pose({}); bpy.context.view_layer.update()
SLOT_SKIN = 0; SLOT_SHORTS = len(BODY.data.materials); SLOT_SHIRT = SLOT_SHORTS + 1
SKINS = [(0.95, 0.80, 0.70), (0.70, 0.52, 0.40), (0.48, 0.33, 0.24), (0.98, 0.86, 0.76), (0.82, 0.64, 0.50)]
SHIRTS = [(0.15, 0.30, 0.60), (0.80, 0.80, 0.78), (0.62, 0.15, 0.13), (0.20, 0.45, 0.30), (0.85, 0.72, 0.38), (0.30, 0.30, 0.34), (0.55, 0.38, 0.62), (0.90, 0.55, 0.60)]
SHIRT_M = [retint(SHIRT_SRC.copy(), c) for c in SHIRTS]
SHORTS_M = [retint(SHORTS_SRC.copy(), c) for c in ((0.12, 0.13, 0.20), (0.42, 0.37, 0.28), (0.20, 0.20, 0.22), (0.30, 0.34, 0.45))]
POLICE_M = retint(SHIRT_SRC.copy(), (0.05, 0.07, 0.17), 0.3); POLICE_P = retint(SHORTS_SRC.copy(), (0.05, 0.07, 0.15), 0.3)
CREW_M = retint(SHIRT_SRC.copy(), (0.95, 0.95, 0.95), 0.25); CREW_P = retint(SHORTS_SRC.copy(), (0.08, 0.08, 0.10), 0.3)
BAG_M = [mat('bag0', (0.10, 0.10, 0.12), 0.5), mat('bag1', (0.45, 0.10, 0.10), 0.5), mat('bag2', (0.15, 0.25, 0.45), 0.5)]
PEOPLE = []
def figure(name, seed, kind='guest', parent=None, loc=(0, 0, 0), yaw=0.0, scale=1.0, vest=False, bag=False):
    """yaw = the direction he faces, measured from +x (like the old figures)"""
    r_ = random.Random(seed); me = BAKED[(vest, 'stand', 0)]
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.location = loc; o.rotation_mode = 'XYZ'; o.rotation_euler = (0, 0, yaw + math.pi / 2)
    if parent: o.parent = parent
    sc = scale * r_.uniform(0.95, 1.06); o.scale = (sc, sc, sc)
    for i_, m_ in ((SLOT_SHIRT, POLICE_M if kind == 'police' else CREW_M if kind == 'crew' else SHIRT_M[r_.randrange(len(SHIRT_M))]),
                   (SLOT_SHORTS, POLICE_P if kind == 'police' else CREW_P if kind == 'crew' else SHORTS_M[r_.randrange(len(SHORTS_M))])):
        o.material_slots[i_].link = 'OBJECT'; o.material_slots[i_].material = m_
    if bag:                                                              # a roller bag at his side, handle in his hand's reach
        b_ = box(name + '_bag', (0.36, 0.22, 0.52), (0.42, 0.10, 0.27), BAG_M[r_.randrange(3)], bv=0.04, parent=o)
        tube(name + '_bagh', [(0.42, 0.10, 0.53), (0.42, 0.10, 0.80)], 0.012, BAG_M[0], o, seg=6)
    p = dict(root=o, seed=seed, kind=kind, vest=vest); PEOPLE.append(p); return p
def pose(p, mode, t, phase=0.0):
    n_, _ = POSES[mode]; v_ = p['vest']
    if (v_, mode, 0) not in BAKED: mode = 'stand' if (v_, 'stand', 0) in BAKED else mode; n_ = POSES[mode][0]
    rate = {'walk': 1.8, 'run': 2.8, 'climb': 1.4, 'tread': 1.0, 'wave': 2.0, 'brace': 0.5}.get(mode, 0.0)
    k = int(((t * rate + phase + p['seed'] * 0.137) % 1.0) * n_) if n_ > 1 else 0
    p['root'].data = BAKED[(v_, mode, k)]
def place(p, loc, yaw=None):
    p['root'].location = loc
    if yaw is not None: p['root'].rotation_euler = (0, 0, yaw + math.pi / 2)
def face(p, yaw): p['root'].rotation_euler = (0, 0, yaw + math.pi / 2)

# ---- the cast
# passengers waiting to get off (main-deck walkway on the dock side, boat frame), and some already on the wharf with bags
GUESTS = [figure(f'g{i}', 100 + i, parent=RBL, loc=(2 + 1.2 * i + 0.4 * h1(i), RB_CY + 7.15 - 0.3 * h1(i + 50), 1.5), yaw=math.pi * (0.5 if i % 3 else 0.0) + 0.3 * (h1(i + 9) - 0.5)) for i in range(12)]
WALKERS = [figure(f'w{i}', 200 + i, loc=(6 + 1.0 * (i % 2), 23.4 + 1.8 * i, 3.4), yaw=math.pi / 2, bag=True) for i in range(5)]
CREW = figure('crew0', 7, 'crew', RBL, loc=(-6.5, RB_CY + 1.0, 1.5), yaw=0.2)
DINERS = []
# on the high side in life vests (deck 2 and 3 walkways, dock side), boat frame
HIGH = []
for i in range(24):
    lv = (1, 2)[i % 2]; z0 = LEVELS[lv][0]
    HIGH.append(figure(f'h{i}', 400 + i, parent=RBL, loc=(-30 + 2.4 * i + 0.5 * h1(i), RB_CY + 7.25, z0), yaw=math.pi / 2 + 0.3 * (h1(i + 2) - 0.5), vest=True))
POLICE = [figure(f'p{i}', 500 + i, 'police', loc=(60 + 6 * i, 28 + 2 * (i % 2), 3.4), yaw=math.pi) for i in range(5)]
SWIM = [figure(f's{i}', 600 + i, loc=(-12 + 3.4 * i, -6, -1.25), yaw=h1(i + 60) * 6.28, vest=True) for i in range(14)]
RESC = [figure(f'r{i}', 700 + i, 'police', loc=(0, 0, 0), yaw=-math.pi / 2) for i in range(2)]
def show_fig(p, on):
    stack = [p['root']]
    while stack:
        o = stack.pop(); o.hide_render = not on; stack.extend(o.children)
for p in SWIM + RESC: show_fig(p, False)
