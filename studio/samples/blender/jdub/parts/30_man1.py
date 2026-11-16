with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HAIR = bpy.data.objects['Human.short02']; HEADBITS = [o for o in bpy.data.objects if o.name.startswith('Human.') and o not in (BODY, SUIT, RIG)]
RB = RIG.data.bones; PB = RIG.pose.bones
KNEE_Z = RB['lowerleg01.R'].head_local.z
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
    for p_ in o.data.polygons: p_.use_smooth = True
# ---- the kit: the casual suit cut down to a basketball tank and shorts (Thunder home whites, #8). Cut faces are deleted from the suit,
# so the skin under them shows; nothing new is laid on top, so nothing can clip.
_vgs = {g.index: g.name for g in SUIT.vertex_groups}
_bm = bmesh.new(); _bm.from_mesh(SUIT.data); _dl = _bm.verts.layers.deform.active
def _armw(v):
    d_ = v[_dl]; return sum(w for gi, w in d_.items() if _vgs[gi].startswith(('upperarm', 'lowerarm')))
_cut = []
for f_ in _bm.faces:
    zc = sum(v.co.z for v in f_.verts) / len(f_.verts)
    aw = sum(_armw(v) for v in f_.verts) / len(f_.verts)
    xc = abs(sum(v.co.x for v in f_.verts) / len(f_.verts))
    if zc < KNEE_Z + 0.13: _cut.append(f_)                        # shorts end a hand above the knee
    elif aw > 0.25 and zc > 1.0: _cut.append(f_)                   # sleeves off: a tank top
    elif zc > 1.34 and xc > 0.085: _cut.append(f_)                 # wide tank shoulders: open over the shoulder caps
bmesh.ops.delete(_bm, geom=_cut, context='FACES'); _bm.to_mesh(SUIT.data); _bm.free(); SUIT.data.update()
# the skin under the cut-away cloth: MakeHuman hides body faces under the suit ('Delete.male_casualsuit06' mask). Take the legs below the
# shorts and the arms back out of that group (with 3 cm of overlap under the cloth edges so no gap can open)
_dg_ = BODY.vertex_groups.get('Delete.male_casualsuit06'); _bvg = {g.index: g.name for g in BODY.vertex_groups}
if _dg_ is not None:
    _free = []
    for v in BODY.data.vertices:
        aw = sum(g.weight for g in v.groups if _bvg[g.group].startswith(('upperarm', 'lowerarm')))
        sw = sum(g.weight for g in v.groups if _bvg[g.group].startswith(('shoulder', 'clavicle')))
        if v.co.z < KNEE_Z + 0.10 or (aw > 0.05 and v.co.z > 1.0) or (v.co.z > 1.28 and abs(v.co.x) > 0.075) or sw > 0.35: _free.append(v.index)
    _dg_.remove(_free)
sol = SUIT.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0035; sol.offset = 1.0
subsurf(BODY, 1); subsurf(SUIT, 1)
BODY.add_rest_position_attribute = True; SUIT.add_rest_position_attribute = True
def kit_mat():
    """white mesh jersey + shorts; Thunder blue and orange trim at the hems, side panels; a blue #8 front and back (rest-space rings)"""
    m = bpy.data.materials.new('kit'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.62; b.inputs['Sheen Weight'].default_value = 0.4
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector']); X, Y, Z = sx.outputs['X'], sx.outputs['Y'], sx.outputs['Z']
    ax = math_(nt, 'ABSOLUTE', X)
    def band(v, lo, hi): return math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', v, lo), math_(nt, 'LESS_THAN', v, hi))
    hem = KNEE_Z + 0.13
    blue = math_(nt, 'MAXIMUM', band(Z, hem, hem + 0.035), band(ax, 0.19, 0.40))               # shorts hem + side panels
    orng = band(Z, hem + 0.035, hem + 0.05)
    # the number 8: two stacked rings, on the chest (y < 0) and the back (y > 0)
    def ring(cz, r):
        dx = X; dz = math_(nt, 'SUBTRACT', Z, cz)
        d = math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dz, dz)))
        return math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', d, r)), 0.012)
    eight = math_(nt, 'MAXIMUM', ring(1.205, 0.033), ring(1.135, 0.04))
    torso = band(Z, 1.06, 1.27)
    num = math_(nt, 'MULTIPLY', eight, torso)
    blue = math_(nt, 'MAXIMUM', blue, num)
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.86, 0.87, 0.88, 1); col.inputs['B'].default_value = (0.0, 0.19, 0.45, 1)
    nt.links.new(blue, col.inputs['Factor'])
    col2 = nt.nodes.new('ShaderNodeMix'); col2.data_type = 'RGBA'; nt.links.new(col.outputs['Result'], col2.inputs['A']); col2.inputs['B'].default_value = (0.85, 0.16, 0.05, 1)
    nt.links.new(orng, col2.inputs['Factor'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900.0; nt.links.new(rp.outputs['Vector'], nz.inputs['Vector'])
    mesh_ = nt.nodes.new('ShaderNodeMix'); mesh_.data_type = 'RGBA'; mesh_.blend_type = 'MULTIPLY'; nt.links.new(col2.outputs['Result'], mesh_.inputs['A'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.9; mr.inputs['To Max'].default_value = 1.03; nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    cc = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(mr.outputs['Result'], cc.inputs[i]) for i in range(3)]
    nt.links.new(cc.outputs['Color'], mesh_.inputs['B']); mesh_.inputs['Factor'].default_value = 1.0
    nt.links.new(mesh_.outputs['Result'], b.inputs['Base Color']); return m
KIT_M = kit_mat(); SUIT.data.materials.clear(); SUIT.data.materials.append(KIT_M)
# his skin a deep brown (multiply over the MakeHuman skin texture, keeping its detail)
def skin_tone(m, col):
    nt = m.node_tree; g_ = next((n for n in nt.nodes if n.type == 'GROUP'), None)
    if g_ is not None:
        nt = g_.node_tree
        if nt.get('toned'): return
        nt['toned'] = 1
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    if lk: nt.links.new(lk.from_socket, mul.inputs['A'])
    else: mul.inputs['A'].default_value = b.inputs['Base Color'].default_value[:]
    mul.inputs['B'].default_value = (*col, 1); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    if 'Subsurface Weight' in b.inputs: b.inputs['Subsurface Weight'].default_value = 0.08
def hair_dark(m):
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED' or n.type == 'BSDF_HAIR_PRINCIPLED':
            if 'Base Color' in n.inputs:
                lk = next((l for l in nt.links if l.to_socket == n.inputs['Base Color']), None)
                if lk: nt.links.remove(lk)
                n.inputs['Base Color'].default_value = (0.012, 0.009, 0.008, 1)
if 'Human.short02' in bpy.data.materials: hair_dark(bpy.data.materials['Human.short02'])
for nm in ('Human.body', 'Human.ears', 'Human.lips', 'Human.nipple'):
    if nm in bpy.data.materials: skin_tone(bpy.data.materials[nm], (0.3, 0.19, 0.13))
# sneakers painted onto his feet (every face mostly weighted to the foot and toe bones), so nothing can clip through them; white socks above
SHOE_M = noisy(mat('sneaker', (0.0, 0.2, 0.45), 0.5), 60.0, 0.12); SOLE_M = mat('sole', (0.92, 0.92, 0.9), 0.6); SOCK_M = noisy(mat('sock', (0.9, 0.9, 0.9), 0.9, sheen=0.5), 300.0, 0.08)
BODY.data.materials.append(SHOE_M); BODY.data.materials.append(SOLE_M); BODY.data.materials.append(SOCK_M); _shoe_i = len(BODY.data.materials) - 3
_vgn = {g.index: g.name for g in BODY.vertex_groups}
_footw = np.zeros(len(BODY.data.vertices))
for v in BODY.data.vertices:
    _footw[v.index] = sum(g.weight for g in v.groups if _vgn[g.group].startswith(('foot.', 'toe')))
for p_ in BODY.data.polygons:
    w_ = float(np.mean([_footw[i] for i in p_.vertices])); zc = sum(BODY.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices)
    if w_ > 0.45:
        p_.material_index = _shoe_i + 1 if zc < 0.018 else _shoe_i
    elif zc < 0.2 and zc > 0.0: p_.material_index = _shoe_i + 2
