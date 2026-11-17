# ================================================================ the man: house MakeHuman model (man.blend), live rig. IK hands on the hook's T-handle
# (palms down, fingers wrapped round the bar), then he lets go, flinches and backs away from the fire with his arms up.
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
MANCOL = bpy.data.collections.new('man'); S.collection.children.link(MANCOL)
for o in _dst.objects: MANCOL.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
PB = RIG.pose.bones
try:
    with bpy.data.libraries.load(asset('pilot.blend'), link=False) as (_s2, _d2):
        _d2.objects = ['Human.shoes05']
    SHOES = _d2.objects[0]; MANCOL.objects.link(SHOES); SHOES.parent = RIG; SHOES.matrix_parent_inverse.identity()
    for md in SHOES.modifiers:
        if md.type == 'ARMATURE': md.object = RIG
    _bvg2 = {g.index: g.name for g in BODY.vertex_groups}
    fg = BODY.vertex_groups.new(name='under_shoes')
    for v in BODY.data.vertices:
        w = sum(g.weight for g in v.groups if any(_bvg2.get(g.group, '').startswith(k) for k in ('foot', 'toe')))
        if w > 0.3 and v.co.z < 0.13: fg.add([v.index], 1.0, 'REPLACE')
    mk = BODY.modifiers.new('hide_feet', 'MASK'); mk.vertex_group = 'under_shoes'; mk.invert_vertex_group = True
    BODY.modifiers.move(len(BODY.modifiers) - 1, 0)
    print('shoes on')
except Exception as e_: print('shoes skipped', e_)
for o in MANCOL.objects:
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
MAN = empty('man_root', loc=(-0.98, 1.08, DECK_Z)); MAN.rotation_euler = (0, 0, math.pi / 2)        # faces +x (the pot)
RIG.parent = MAN; RIG.location = (0, 0, 0); RIG.rotation_euler = (0, 0, 0)
# shirt: dark red flannel tint on the top half, jeans stay; an apron = his shirt's front torso faces pushed out
SH_SRC = SUIT.data.materials[0]; SHIRT = SH_SRC.copy(); SHIRT.name = 'flannel'; SUIT.data.materials.append(SHIRT)
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
    # flannel check: a plaid of two wave bands
    try:
        co = coord(nt, 'Object'); sx = sepz(nt, co)
        bx = math_(nt, 'GREATER_THAN', math_(nt, 'SINE', math_(nt, 'MULTIPLY', sx.outputs['X'], 70.0)), 0.55)
        bz = math_(nt, 'GREATER_THAN', math_(nt, 'SINE', math_(nt, 'MULTIPLY', sx.outputs['Z'], 70.0)), 0.55)
        pl = math_(nt, 'MAXIMUM', bx, bz)
        mm = nt.nodes.new('ShaderNodeMix'); mm.data_type = 'RGBA'; nt.links.new(pl, mm.inputs['Factor']); nt.links.new(mul.outputs['Result'], mm.inputs['A'])
        mm.inputs['B'].default_value = (0.06, 0.04, 0.04, 1); nt.links.new(mm.outputs['Result'], b.inputs['Base Color'])
    except Exception as e_: print('plaid skipped', e_)
    return m
retint(SHIRT, (0.55, 0.08, 0.06), 0.3)
_vgn = {g.index: g.name for g in SUIT.vertex_groups}
_ARM = {b_ + s_ for s_ in ('.L', '.R') for b_ in ('clavicle', 'shoulder01', 'upperarm01', 'upperarm02', 'lowerarm01', 'lowerarm02', 'wrist')}
def _armw(v): return sum(g.weight for g in v.groups if _vgn.get(g.group, '') in _ARM)
_af = [p_.index for p_ in SUIT.data.polygons if 0.62 < sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) < 1.36
       and sum(SUIT.data.vertices[i].co.y for i in p_.vertices) / len(p_.vertices) < -0.02 and max(_armw(SUIT.data.vertices[i]) for i in p_.vertices) < 0.2]
_bm = bmesh.new(); _bm.from_mesh(SUIT.data); _keep = set(_af)
bmesh.ops.delete(_bm, geom=[f for f in _bm.faces if f.index not in _keep], context='FACES'); _bm.normal_update()
for v in _bm.verts: v.co += v.normal * 0.016
_am = bpy.data.meshes.new('apron'); _bm.to_mesh(_am); _bm.free()
APRON = bpy.data.objects.new('apron', _am); MANCOL.objects.link(APRON); APRON.parent = SUIT.parent; APRON.matrix_parent_inverse = SUIT.matrix_parent_inverse.copy()
APRON.matrix_world = SUIT.matrix_world.copy()
for g in SUIT.vertex_groups: APRON.vertex_groups.new(name=g.name)
_md = APRON.modifiers.new('arm', 'ARMATURE'); _md.object = RIG
_sol = APRON.modifiers.new('thick', 'SOLIDIFY'); _sol.thickness = 0.006; _sol.offset = 1.0
AP_M = mat('apronm', (0.16, 0.17, 0.19), 0.85, sheen=0.3); noisy(AP_M, 160.0, 0.15, 0.05); APRON.data.materials.append(AP_M)
# work gloves: paint the hands by bone weights (a glove material on the body's hand faces)
GLOVE = mat('glove', (0.62, 0.48, 0.30), 0.8, sheen=0.4); noisy(GLOVE, 90.0, 0.2, 0.1)
BODY.data.materials.append(GLOVE); _gi = len(BODY.data.materials) - 1
_bvg = {g.index: g.name for g in BODY.vertex_groups}
def _handw(v): return sum(g.weight for g in v.groups if any(_bvg.get(g.group, '').startswith(k) for k in ('wrist', 'finger', 'metacarpal')))
for p_ in BODY.data.polygons:
    if min(_handw(BODY.data.vertices[i]) for i in p_.vertices) > 0.5: p_.material_index = _gi

# ---- IK
def ik(bone, target, pole, chain=4, pole_angle=0.0):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TG = {k: empty('tg_' + k) for k in ('hR', 'hL', 'pR', 'pL', 'rotR', 'rotL')}
IKR = ik('wrist.R', TG['hR'], TG['pR'], 5, R(-90)); IKL = ik('wrist.L', TG['hL'], TG['pL'], 5, R(-90))
def _hand_frame(side):
    b = RIG.data.bones
    d = (b['finger3-1.' + side].head_local - b['wrist.' + side].head_local).normalized()
    n = b['finger3-1.' + side].matrix_local.to_3x3().col[2]; n = (n - d * n.dot(d)).normalized()
    a = d.cross(n); th = b['finger1-1.' + side].head_local - b['finger3-1.' + side].head_local
    return Matrix((a, d, n)).transposed(), (1.0 if th.dot(a) > 0 else -1.0)
HAND = {}
for s_ in ('R', 'L'):
    Hr, ts = _hand_frame(s_); Wr = RIG.data.bones['wrist.' + s_].matrix_local.to_3x3(); TG['rot' + s_].rotation_mode = 'QUATERNION'
    c = PB['wrist.' + s_].constraints.new('COPY_ROTATION'); c.target = TG['rot' + s_]; c.owner_space = c.target_space = 'WORLD'
    HAND[s_] = (Hr.transposed() @ Wr, ts, c)
def grip(side, bar_pt, w):
    """palm on top of a horizontal bar, fingers curling over its far side; returns the wrist IK target (world)"""
    O, ts, con = HAND[side]; con.influence = w
    fwd = (MAN.matrix_world.to_3x3().normalized() @ Vector((0, -1, 0))).normalized()     # his front, in the world
    d = (fwd * 0.72 + Vector((0, 0, -0.69))).normalized()                                 # toward the fingers: forward and down over the bar
    n = (Vector((0, 0, -1)) * 0.72 - fwd * 0.69).normalized()                             # palm faces down (and a little back) onto the bar
    a = d.cross(n)
    TG['rot' + side].rotation_quaternion = (Matrix((a, d, n)).transposed() @ O).to_quaternion()
    return Vector(bar_pt) - n * 0.032 - d * 0.05
FING = {s_: [f'finger{f_}-{g}.{s_}' for f_ in range(1, 6) for g in (1, 2, 3)] for s_ in ('L', 'R')}
def fingers(side, w):
    for nm in FING[side]:
        if nm not in PB: continue
        f_ = int(nm[6]); seg = int(nm[8])
        held = (14, 20, 12)[seg - 1] if f_ == 1 else (40, 62, 38)[seg - 1]; loose = (6, 8, 5)[seg - 1] if f_ == 1 else (12, 16, 10)[seg - 1]
        pb = PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(lerp(loose, held, w)), 0, 0)
def man_pose(spine=0.0, neck=0.0, head=0.0, head_yaw=0.0, legs=None):
    for n, k in (('spine03', 0.3), ('spine02', 0.3), ('spine01', 0.4)):
        pb = PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(spine * k), 0, 0)
    for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)):
        pb = PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(neck * k), R(head_yaw * k * 0.5), 0)
    pb = PB['head']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(head), R(head_yaw * 0.5), 0)
    for nm in ('upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'foot.L', 'foot.R'):
        pb = PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (legs or {}).get(nm, (0, 0, 0))
def man_world(p): return MAN.matrix_world @ Vector(p)
KNK = ('finger2-1', 'finger3-1', 'finger4-1', 'finger5-1')
def knuckles(side):
    ps = [RIG.matrix_world @ PB[k + '.' + side].head for k in KNK if k + '.' + side in PB]
    return sum(ps, Vector()) / len(ps)
def grip_fix(want, w, iters=3):
    """closed loop: nudge each wrist target until the knuckle line sits where it should on the bar"""
    if w <= 0.01: return
    for _ in range(iters):
        bpy.context.view_layer.update()
        for s_, p in want.items():
            err = p - knuckles(s_); TG['h' + s_].location += err * w
    bpy.context.view_layer.update()
