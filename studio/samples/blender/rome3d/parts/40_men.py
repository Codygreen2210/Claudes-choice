# ================================================================ the worker: the house MakeHuman man (man.blend) in a short-sleeved undyed wool
# tunic (a flared skirt to the knee plus a shell lifted off his own chest and upper arms, so it bends with him), a belt, bare legs, sandals-free.
_BVG_KEYS = ('foot', 'toe')
def _retint_skin(m, col):
    """the MakeHuman skin is a node group: push its colour mix-in toward a sun-browned tone"""
    g = next((n for n in m.node_tree.nodes if n.type == 'GROUP'), None)
    if g is None: return
    g.inputs['colorMixIn'].default_value = (*col, 1); g.inputs['colorMixInStrength'].default_value = 0.95
    g.inputs['Roughness'].default_value = 0.5
LINEN = mat('wool', (0.46, 0.38, 0.28), 0.97, sheen=0.5); noisy(LINEN, 160.0, 0.12, 0.05)
BELT = mat('belt', (0.16, 0.09, 0.05), 0.75, sheen=0.2)
def make_kilt(name, rig, col):
    # rings: (z, rx, ry) in the rig's rest space (he faces -y); pleats as small ripples round the hem
    rings = [(1.000, 0.150, 0.118), (0.960, 0.162, 0.128), (0.900, 0.188, 0.150), (0.840, 0.205, 0.165), (0.760, 0.222, 0.185), (0.680, 0.238, 0.205), (0.620, 0.248, 0.215)]
    seg = 48; vs = []; fs = []; cy = 0.012
    for i, (z_, rx, ry) in enumerate(rings):
        u = i / (len(rings) - 1)
        for k in range(seg):
            a_ = 2 * math.pi * k / seg; pl = 1.0 + 0.035 * u * math.sin(a_ * 14)
            vs.append((rx * pl * math.cos(a_), cy + ry * pl * math.sin(a_), z_ + (0.03 * u if math.sin(a_) < -0.3 else 0.0) * max(0, -math.sin(a_))))
    for i in range(len(rings) - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = rig; o.matrix_parent_inverse.identity(); o.data.materials.append(LINEN)
    gr = o.vertex_groups.new(name='root'); gl = o.vertex_groups.new(name='upperleg01.L'); gR = o.vertex_groups.new(name='upperleg01.R')
    for i, v in enumerate(me.vertices):
        u = clamp((1.0 - v.co.z) / 0.38, 0, 1); x_ = v.co.x; leg = 0.45 * u * u * min(1.0, abs(x_) / 0.12)
        gr.add([i], 1.0 - leg, 'REPLACE')
        (gl if x_ > 0 else gR).add([i], leg, 'REPLACE')
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.008; sol.offset = 1.0
    bt = tube(name + '_belt', [(0.152 * math.cos(2 * math.pi * k / 40), 0.012 + 0.120 * math.sin(2 * math.pi * k / 40), 0.985) for k in range(41)], 0.016, BELT, seg=8, caps=False)
    bt.parent = rig; bt.matrix_parent_inverse.identity(); col.objects.link(bt); S.collection.objects.unlink(bt)
    gb = bt.vertex_groups.new(name='root'); gb.add(list(range(len(bt.data.vertices))), 1.0, 'REPLACE'); mb = bt.modifiers.new('arm', 'ARMATURE'); mb.object = rig
    return o
def make_shell(name, body, rig, col):
    """the tunic's top: the body's own chest, back and upper-arm faces, pushed out 1.4 cm, with the body's skin weights copied"""
    me_b = body.data; vg = {g.index: g.name for g in body.vertex_groups}
    def wmap(v): return {vg[g.group]: g.weight for g in v.groups if g.group in vg}
    keep = set()
    for v in me_b.vertices:
        w = wmap(v); z_ = v.co.z
        arm = w.get('upperarm01.L', 0) + w.get('upperarm01.R', 0) + w.get('upperarm02.L', 0) + w.get('upperarm02.R', 0)
        low = w.get('lowerarm01.L', 0) + w.get('lowerarm01.R', 0) + w.get('lowerarm02.L', 0) + w.get('lowerarm02.R', 0) + w.get('wrist.L', 0) + w.get('wrist.R', 0)
        if w.get('body', 0) > 0.5 and 0.93 < z_ < 1.43 and low < 0.05 and (arm < 0.3 or z_ > 1.17) and abs(v.co.x) < 0.33: keep.add(v.index)
    ms = [i for i, m_ in enumerate(me_b.materials) if m_ and 'body' in m_.name]
    faces = [p_ for p_ in me_b.polygons if p_.material_index in ms and all(i in keep for i in p_.vertices)]
    used = sorted({i for p_ in faces for i in p_.vertices}); rid = {i: k for k, i in enumerate(used)}
    vs = [tuple(me_b.vertices[i].co + me_b.vertices[i].normal * 0.022) for i in used]
    fs = [tuple(rid[i] for i in p_.vertices) for p_ in faces]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = rig; o.matrix_parent_inverse = body.matrix_parent_inverse.copy(); o.matrix_basis = body.matrix_basis.copy()
    o.data.materials.append(LINEN); groups = {}
    for k, i in enumerate(used):
        for gn, w in wmap(me_b.vertices[i]).items():
            if w <= 0: continue
            if gn not in groups: groups[gn] = o.vertex_groups.new(name=gn)
            groups[gn].add([k], w, 'REPLACE')
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig; md.use_deform_preserve_volume = True
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.006; sol.offset = 1.0
    # hide the body under it for good (nothing can poke through)
    inner = [i for i in used if all(j in keep for j in [i])]
    hg = body.vertex_groups.new(name='under_tunic'); hg.add([i for i in used if 0.96 < me_b.vertices[i].co.z < 1.40 and abs(me_b.vertices[i].co.x) < 0.17], 1.0, 'REPLACE')
    mk = body.modifiers.new('hide_under_tunic', 'MASK'); mk.vertex_group = 'under_tunic'; mk.invert_vertex_group = True; body.modifiers.move(len(body.modifiers) - 1, 0)
    return o
HAIRM = mat('hairblack', (0.018, 0.014, 0.012), 0.55, sheen=0.3)
class Man:
    def __init__(self, name, skin=(0.55, 0.36, 0.24), loc=(0, 0, 0), yaw=math.pi):
        with bpy.data.libraries.load(asset('man.blend'), link=False) as (_s, _d):
            _d.objects = [n for n in _s.objects if n.startswith('Human')]
        self.col = bpy.data.collections.new(name); S.collection.children.link(self.col)
        for o in _d.objects: self.col.objects.link(o)
        objs = list(_d.objects)
        self.rig = next(o for o in objs if o.type == 'ARMATURE')
        self.body = next(o for o in objs if o.type == 'MESH' and any(m_.type == 'MASK' and m_.name.startswith('Delete') for m_ in o.modifiers))
        suit = next(o for o in objs if 'casualsuit' in o.name); hair = next((o for o in objs if 'short02' in o.name), None)
        self.PB = self.rig.pose.bones
        # body: show the chest (the trousers' delete mask off), hide the groin under the kilt for good, brown the skin
        for m_ in self.body.modifiers:
            if m_.type == 'MASK' and m_.name.startswith('Delete'): m_.show_render = m_.show_viewport = False
        gi = [i for i, m_ in enumerate(self.body.data.materials) if m_ and 'genital' in m_.name]
        hg = self.body.vertex_groups.new(name='hide_groin')
        hv = set()
        for p_ in self.body.data.polygons:
            if p_.material_index in gi: hv.update(p_.vertices)
        if hv: hg.add(list(hv), 1.0, 'REPLACE')
        mk = self.body.modifiers.new('hide_groin', 'MASK'); mk.vertex_group = 'hide_groin'; mk.invert_vertex_group = True; self.body.modifiers.move(len(self.body.modifiers) - 1, 0)
        for m_ in self.body.data.materials:
            if m_ and ('body' in m_.name or 'ears' in m_.name or 'lips' in m_.name or 'nipple' in m_.name): _retint_skin(m_, skin)
        # kilt (shendyt): a flared linen wrap from the waist to above the knee, skinned to the hips with a little pull from each thigh
        suit.hide_render = True; suit.hide_viewport = True
        self.kilt = make_kilt(name + '_kilt', self.rig, self.col)
        self.shell = make_shell(name + '_shell', self.body, self.rig, self.col)
        if hair:
            hair.data.materials.clear(); hair.data.materials.append(HAIRM)
        for o in self.col.objects:
            for md in o.modifiers:
                if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
        self.root = empty(name + '_root', loc=loc); self.root.rotation_euler = (0, 0, yaw)
        self.rig.parent = self.root; self.rig.location = (0, 0, 0); self.rig.rotation_euler = (0, 0, 0)
        # IK arms and hand rotation
        self.tg = {k: empty(f'{name}_{k}') for k in ('hR', 'hL', 'pR', 'pL', 'rotR', 'rotL')}
        self.ikc = {}
        for s_ in ('R', 'L'):
            c = self.PB['wrist.' + s_].constraints.new('IK'); c.target = self.tg['h' + s_]; c.pole_target = self.tg['p' + s_]; c.chain_count = 5; c.pole_angle = R(-90); c.use_tail = True
            self.ikc[s_] = c
        self.hand = {}
        for s_ in ('R', 'L'):
            b = self.rig.data.bones
            d_ = (b['finger3-1.' + s_].head_local - b['wrist.' + s_].head_local).normalized()
            n_ = b['finger3-1.' + s_].matrix_local.to_3x3().col[2]; n_ = (n_ - d_ * n_.dot(d_)).normalized(); a_ = d_.cross(n_)
            Hr = Matrix((a_, d_, n_)).transposed(); Wr = b['wrist.' + s_].matrix_local.to_3x3(); self.tg['rot' + s_].rotation_mode = 'QUATERNION'
            c = self.PB['wrist.' + s_].constraints.new('COPY_ROTATION'); c.target = self.tg['rot' + s_]; c.owner_space = c.target_space = 'WORLD'
            self.hand[s_] = (Hr.transposed() @ Wr, c)
    def world(self, p): return self.root.matrix_world @ Vector(p)
    def fwd(self): return (self.root.matrix_world.to_3x3().normalized() @ Vector((0, -1, 0))).normalized()
    def right(self): return (self.root.matrix_world.to_3x3().normalized() @ Vector((-1, 0, 0))).normalized()
    def orient(self, s_, d_, n_, w=1.0):
        """hand frame: d = where the straight fingers point, n = out of the palm (toward what it holds)"""
        O, con = self.hand[s_]; con.influence = w; d_ = Vector(d_).normalized(); n_ = (Vector(n_) - d_ * Vector(n_).dot(d_)).normalized(); a_ = d_.cross(n_)
        self.tg['rot' + s_].rotation_quaternion = (Matrix((a_, d_, n_)).transposed() @ O).to_quaternion()
    def fingers(self, s_, w, thumb=1.0):
        for f_ in range(1, 6):
            for g in (1, 2, 3):
                nm = f'finger{f_}-{g}.{s_}'
                if nm not in self.PB: continue
                held = (14, 20, 12)[g - 1] if f_ == 1 else (55, 75, 50)[g - 1]; loose = (6, 8, 5)[g - 1] if f_ == 1 else (12, 16, 10)[g - 1]
                pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(lerp(loose, held, w * (thumb if f_ == 1 else 1.0))), 0, 0)
    def pose(self, spine=0.0, neck=0.0, head=0.0, head_yaw=0.0, legs=None, twist=0.0):
        for n, k in (('spine03', 0.3), ('spine02', 0.3), ('spine01', 0.4)):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(spine * k), R(twist * k), 0)
        for n, k in (('neck01', 0.4), ('neck02', 0.3), ('neck03', 0.3)):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(neck * k), R(head_yaw * k * 0.5), 0)
        pb = self.PB['head']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(head), R(head_yaw * 0.5), 0)
        for nm in ('upperleg01.L', 'upperleg01.R', 'lowerleg01.L', 'lowerleg01.R', 'foot.L', 'foot.R'):
            pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (legs or {}).get(nm, (0, 0, 0))
    def bone(self, nm, tail=False):
        pb = self.PB[nm]; return self.rig.matrix_world @ (pb.tail if tail else pb.head)
    def knuckles(self, s_):
        ps = [self.bone(k + '.' + s_) for k in ('finger2-1', 'finger3-1', 'finger4-1', 'finger5-1') if k + '.' + s_ in self.PB]
        return sum(ps, Vector()) / len(ps)
    def palm(self, s_):
        return (self.bone('wrist.' + s_) + self.knuckles(s_)) / 2
def walk_legs(ph, amp, bend=1.0, plant=0.0):
    """a stride: ph is the leg phase (radians), amp the swing in degrees; plant > 0 braces both legs (straining, stuck)"""
    out = {}
    for s_, off in (('L', 0.0), ('R', math.pi)):
        sw = math.sin(ph + off); lift = max(0.0, math.cos(ph + off))
        up = -amp * sw - plant * (14 if s_ == 'L' else -10)
        knee = (8 + 40 * lift * bend) * (1 - 0.3 * plant) + plant * (18 if s_ == 'L' else 4)
        out['upperleg01.' + s_] = (R(up), 0, 0); out['lowerleg01.' + s_] = (R(knee), 0, 0); out['foot.' + s_] = (R(-0.4 * up - 0.3 * knee + 10 * lift), 0, 0)
    return out
