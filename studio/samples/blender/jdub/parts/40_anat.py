# ================================================================ HIS LEFT LEG'S BONES (anat_l.blend: the Z-Anatomy left leg, fitted in his rest space)
ANAT = []
with bpy.data.libraries.load(asset('anat_l.blend'), link=False) as (_s, _d): _d.objects = list(_s.objects)
for o in _d.objects:
    if o['kind'] != 'bone': continue
    S.collection.objects.link(o); o.parent = RIG; o.matrix_world = Matrix.Identity(4)
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False; o.add_rest_position_attribute = True; ANAT.append(o)
AN = {o.name: o for o in ANAT}
TIB, FIB, TAL = AN['Tibia.L'], AN['Fibula.L'], AN['Talus.L']
FOOTB = [o for o in ANAT if o not in (TIB, FIB) and o.name not in ('Femur.L', 'Patella.L', 'Hip bone.L')]
def bone_mat(name):
    """bone: warm ivory with a cool x-ray rim; 'hi' lights it yellow (named on screen), 'crack' (fibula) burns red around the break"""
    m = mat(name, (0.86, 0.82, 0.72), 0.5); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    band = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'DIVIDE', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', sx.outputs['Z'], FIB_CUT)), 0.03)), 0.0), 2.0)
    crack = math_(nt, 'MULTIPLY', band, objattr(nt, 'crack'))
    hi = objattr(nt, 'hi')
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'; col.inputs['A'].default_value = (0.7, 0.85, 1.0, 1); col.inputs['B'].default_value = (1.0, 0.8, 0.2, 1)
    nt.links.new(math_(nt, 'MINIMUM', hi, 1.0), col.inputs['Factor'])
    col2 = nt.nodes.new('ShaderNodeMix'); col2.data_type = 'RGBA'; nt.links.new(col.outputs['Result'], col2.inputs['A']); col2.inputs['B'].default_value = (1.0, 0.12, 0.05, 1)
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', crack, 3.0), 1.0), col2.inputs['Factor'])
    nt.links.new(col2.outputs['Result'], b.inputs['Emission Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'ADD', math_(nt, 'MULTIPLY', lw.outputs['Facing'], 0.9), math_(nt, 'MULTIPLY', hi, 1.6)), math_(nt, 'MULTIPLY', crack, 8.0)),
                 b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
FIB_CUT = 0.17                                                   # the break: low on the fibula, a hand above the ankle (rest z, m)
for o in ANAT:
    o.data.materials.clear(); o.data.materials.append(bone_mat('bone_' + o.name)); o['hi'] = 0.0; o['crack'] = 0.0
# ---- the break and the dislocation as shape keys in his rest space (the armature carries them into any pose)
def _keys(o):
    if o.data.shape_keys is None: o.shape_key_add(name='Basis')
    return o.shape_key_add(name='k', from_mix=False)
_fx = sum(v.co.x for v in FIB.data.vertices) / len(FIB.data.vertices)
_low = [v for v in FIB.data.vertices if v.co.z < FIB_CUT]; _cx = sum(v.co.x for v in _low) / len(_low); _cy = sum(v.co.y for v in _low) / len(_low)
KB = _keys(FIB)
for v in FIB.data.vertices:
    p = v.co.copy()
    if p.z < FIB_CUT:                                             # the low piece: tips out about the break and slides out with the ankle
        q = p - V3(_cx, _cy, FIB_CUT); q = Matrix.Rotation(R(-14), 3, 'Y') @ q; KB.data[v.index].co = V3(_cx, _cy, FIB_CUT) + q + V3(0.016, -0.004, -0.006)
    else:
        k = clamp((p.z - FIB_CUT) / 0.03, 0, 1); KB.data[v.index].co = p + V3(-0.004 * (1 - k), 0.0, 0.0)
FIB_KEY = FIB.data.shape_keys.key_blocks['k']
DISL = []
for o in [TAL] + FOOTB:                                           # the talus and the whole foot shift out of the ankle socket
    kb = _keys(o)
    for v in o.data.vertices:
        p = v.co; kb.data[v.index].co = p + V3(0.026, 0.006, -0.008) + (Matrix.Rotation(R(-10), 3, 'Y') @ (p - V3(0.19, -0.03, 0.06)) - (p - V3(0.19, -0.03, 0.06)))
    DISL.append(o.data.shape_keys.key_blocks['k'])
def injury(brk, disl):
    FIB_KEY.value = brk
    for k in DISL: k.value = disl
# ---- x-ray: every material on him gets a mix to a see-through blue glow; 'xr' (on the object) runs it 0..1
def xray_wrap(m):
    if m is None or m.get('xw'): return
    m['xw'] = 1; nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'); lk = next((l for l in nt.links if l.to_socket == out.inputs['Surface']), None)
    if lk is None: return
    src = lk.from_socket
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.4
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.2)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.35, 0.62, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY_ADD', fz, 1.4, 0.02), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gm = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY_ADD', fz, 0.55, 0.03), 1.0), gm.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], gm.inputs[1]); nt.links.new(em.outputs['Emission'], gm.inputs[2])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac']); nt.links.new(src, mx.inputs[1]); nt.links.new(gm.outputs['Shader'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
MAN = [BODY, SUIT, HAIR] + HEADBITS
for o in MAN:
    o['xr'] = 0.0
    for sl in o.material_slots: xray_wrap(sl.material)
def xray(k):
    for o in MAN: o['xr'] = k
    for o in ANAT: o.hide_render = k < 0.02
