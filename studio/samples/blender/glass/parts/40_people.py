
# ================================================================ people: the house MakeHuman man (man.blend) with the CC0 middle-age skin, sneakers on
# his feet (parented to the foot bones), posed on his rig and baked per pose (see the boat Short). Kids are the same man scaled.
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
# skin: the CC0 middle-age male skin with stubble (MakeHuman community skins02), as approved on the face test
_skd = next((d for d in (os.path.join(HERE, 'assets', 'jartur'), '/root/vt/mh/packs/keep/r2/skins/jartur69_middleage_slavic_male_with_genitals_and_beard') if os.path.isdir(d)), None)
if _skd:
    _ski = bpy.data.images.load(os.path.join(_skd, 'Jartur_mid_old_Slavic_Male_with_Genitals_and_Beard_lsdif_lighter_2k.jpg'))
    for mn in ('Human.body', 'Human.ears', 'Human.lips'):
        m = bpy.data.materials.get(mn)
        if not m: continue
        t = m.node_tree; [t.nodes.remove(n) for n in list(t.nodes) if n.bl_idname != 'ShaderNodeOutputMaterial']
        b = t.nodes.new('ShaderNodeBsdfPrincipled'); t.links.new(b.outputs[0], t.nodes['Material Output'].inputs['Surface'])
        im = t.nodes.new('ShaderNodeTexImage'); im.image = _ski; t.links.new(im.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.45; b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2); b.inputs['Subsurface Scale'].default_value = 0.012
# hair: MakeHuman's own short02, darkened (owner: "put the old hair back on")
_hm = bpy.data.materials.get('Human.short02')
if _hm:
    t = _hm.node_tree; hb_ = next(n for n in t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    src_ = hb_.inputs['Base Color'].links[0].from_socket if hb_.inputs['Base Color'].links else None
    mx_ = t.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs['Factor'].default_value = 1.0
    if src_: t.links.new(src_, mx_.inputs[6])
    mx_.inputs[7].default_value = (0.16, 0.10, 0.07, 1); t.links.new(mx_.outputs[2], hb_.inputs['Base Color']); hb_.inputs['Roughness'].default_value = 0.6
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
# sneakers on his feet: built round each foot's own vertices (rest pose), parented to the foot bone so they walk with him
def _foot_box(side):
    vg = BODY.vertex_groups.get('foot' + side); pts = []
    for v in BODY.data.vertices:
        if vg and any(g.group == vg.index and g.weight > 0.4 for g in v.groups): pts.append(BODY.matrix_world @ v.co)
    for nm in [g.name for g in BODY.vertex_groups if g.name.startswith('toe') and g.name.endswith(side)]:
        gi_ = BODY.vertex_groups[nm].index; pts += [BODY.matrix_world @ v.co for v in BODY.data.vertices if any(g.group == gi_ and g.weight > 0.4 for g in v.groups)]
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0.0)), (max(xs) - min(xs), max(ys) - min(ys), max(zs))
FEET_SHOES = []
for side in ('.L', '.R'):
    c_, (wx_, ly_, hz_) = _foot_box(side)
    sh = sneaker('shoe' + side, UPPER_MS[0], loc=(c_.x, c_.y + 0.005, -0.004), s=1.0); sh.scale = ((wx_ + 0.03) / 0.105, (ly_ + 0.03) / 0.285, max(1.0, (hz_ + 0.02) / 0.1))
    bpy.context.view_layer.update(); mw = sh.matrix_world.copy(); sh.parent = RIG; sh.parent_type = 'BONE'; sh.parent_bone = 'foot' + side; sh.matrix_world = mw
    FEET_SHOES.append(sh)
# ---- poses: bone rotations (radians). Front is -Y; legs swing forward with -X, arms forward with +X, L arm out with +Z, R arm out with -Z
POSE_BONES = ['upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'upperarm01.L', 'upperarm01.R', 'lowerarm01.L', 'lowerarm01.R', 'spine01', 'spine03', 'neck01', 'foot.L', 'foot.R']
def set_pose(d):
    for n in POSE_BONES:
        b = PB[n]; b.rotation_mode = 'XYZ'; b.rotation_euler = d.get(n, (0, 0, 0))
def p_stand(ph=0.0):
    return {'upperarm01.L': (0.05 * math.sin(ph), 0, -0.62), 'upperarm01.R': (0.05 * math.sin(ph + 1), 0, 0.62), 'lowerarm01.L': (0.25, 0, 0), 'lowerarm01.R': (0.25, 0, 0)}   # arms down at his sides
def p_gait(ph, leg, knee, arm, elbow, lean):
    s_ = math.sin(ph)
    return {'upperleg01.L': (-leg * s_, 0, 0), 'upperleg01.R': (leg * s_, 0, 0),
            'lowerleg01.L': (knee * max(0.0, math.sin(ph - 1.2)) + 0.1, 0, 0), 'lowerleg01.R': (knee * max(0.0, math.sin(ph + math.pi - 1.2)) + 0.1, 0, 0),
            'upperarm01.L': (-arm * s_, 0, -0.6), 'upperarm01.R': (arm * s_, 0, 0.6), 'lowerarm01.L': (elbow, 0, 0), 'lowerarm01.R': (elbow, 0, 0),
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
         'brace': (2, p_brace), 'look': (1, lambda ph=0.0: dict(p_stand(), **{'neck01': (0.55, 0, 0), 'spine03': (0.2, 0, 0)})), 'climb': (4, p_climb), 'tread': (4, p_tread), 'jump': (1, p_jump), 'wave': (4, p_wave)}
PARTS = [BODY, SUIT, HAIR, EYES, LASH, BROW]
def _shoe_parts(): return [c for s_ in FEET_SHOES for c in s_.children_recursive if c.type == 'MESH']
def bake(name, vest):
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new(); mats = []
    for o in PARTS + _shoe_parts():
        ev = o.evaluated_get(dg); me = ev.to_mesh(); nf0 = len(bm.faces); nv0 = len(bm.verts)
        bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
        bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts[nv0:])
        for f in bm.faces[nf0:]: f.material_index += len(mats); f.smooth = True
        mats += list(o.data.materials); ev.to_mesh_clear()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in mats: me.materials.append(m_)
    return me
BAKED = {}
NEED = {False: ('stand', 'walk', 'brace', 'look')}
for vest_, modes in NEED.items():
    for md_ in modes:
        n_, fn = POSES[md_]
        for k in range(n_):
            set_pose(fn(2 * math.pi * k / n_)); bpy.context.view_layer.update(); BAKED[(vest_, md_, k)] = bake(f'man_{md_}{k}{"v" if vest_ else ""}', vest_)
set_pose({}); bpy.context.view_layer.update()
SLOT_SKIN = 0; SLOT_SHORTS = len(BODY.data.materials); SLOT_SHIRT = SLOT_SHORTS + 1
SLOT_UPPER = sum(len(o.data.materials) for o in PARTS) + 1    # each sneaker: sole, upper, lace (left shoe's upper slot)
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


def show_fig(p, on):
    stack = [p['root']]
    while stack:
        o = stack.pop(); o.hide_render = not on; stack.extend(o.children)
# ---- the cast: him (on the Ledge from frame one), and the 2019 group (a mum and two kids, plus him) for the splinter
HIM = figure('him', 3, loc=(0.25, -0.62, Z0), yaw=-math.pi / 2)
GROUP = [figure('mum', 21, loc=(-0.75, -0.55, Z0), yaw=-math.pi / 2 + 0.3), figure('kid1', 22, loc=(-0.2, -0.85, Z0), yaw=-math.pi / 2 - 0.2, scale=0.68),
         figure('kid2', 23, loc=(0.75, -0.95, Z0), yaw=-math.pi / 2 + 0.1, scale=0.6)]
for p in GROUP: show_fig(p, False)

CROWD = [figure(f'c{i}', 40 + i, loc=(-1.1 + 0.42 * i, 1.5, Z0), yaw=-math.pi / 2) for i in range(6)]
for p in CROWD: show_fig(p, False)
for c in _shoe_parts(): c.hide_render = True
