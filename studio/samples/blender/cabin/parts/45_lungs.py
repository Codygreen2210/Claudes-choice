# ================================================================ HIS LUNGS (lungs.blend: Z-Anatomy lobes, trachea, diaphragm, ribs, spine, fitted in his
# rest space by lung_build.py). They ride the rig as one piece (his trunk stays straight in the x-ray shot; he leans from the hips)
ANAT = []
with bpy.data.libraries.load(asset('lungs.blend'), link=False) as (_s, _d): _d.objects = list(_s.objects)
for o in _d.objects:
    S.collection.objects.link(o); o.parent = RIG; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, 0, 0)
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False; ANAT.append(o)
def kind(k): return [o for o in ANAT if o['kind'] == k]
ANAT = [o for o in ANAT if not (o['kind'] == 'bone' and (o.name.startswith('Hip bone') or o.name.startswith('Sacrum') or o.name.startswith('Coccyx')))]
for o in list(_d.objects):
    if o not in ANAT: o.hide_render = True; o.hide_viewport = True
def bone_mat():
    m = mat('bone', (0.86, 0.82, 0.72), 0.55, sheen=0.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (0.75, 0.85, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY', lw.outputs['Facing'], 1.2), b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
BONE_M = bone_mat()
for o in kind('bone'): o.data.materials.clear(); o.data.materials.append(BONE_M)
def lung_mat(name, good, bad, alpha):
    """soft see-through organ; object prop 'oxy' 1 = pink and full of oxygen, 0 = dull blue-grey (starved); 'tt' moves the sheen"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    b.inputs['Roughness'].default_value = 0.35; b.inputs['Coat Weight'].default_value = 0.4
    b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Radius'].default_value = (0.01, 0.004, 0.003)
    ox = objattr(nt, 'oxy')
    bc = nt.nodes.new('ShaderNodeMix'); bc.data_type = 'RGBA'; bc.inputs['A'].default_value = (*bad, 1); bc.inputs['B'].default_value = (*good, 1)
    nt.links.new(ox, bc.inputs['Factor']); nt.links.new(bc.outputs['Result'], b.inputs['Base Color'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60.0; nz.noise_dimensions = '4D'; nt.links.new(objattr(nt, 'tt'), nz.inputs['W'])
    rim = nt.nodes.new('ShaderNodeMix'); rim.data_type = 'RGBA'; rim.inputs['A'].default_value = (0.35, 0.45, 1.0, 1); rim.inputs['B'].default_value = (1.0, 0.45, 0.45, 1)
    nt.links.new(ox, rim.inputs['Factor']); nt.links.new(rim.outputs['Result'], b.inputs['Emission Color'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', lw.outputs['Facing'], 0.9), math_(nt, 'MULTIPLY', nz.outputs['Fac'], math_(nt, 'MULTIPLY', ox, 0.5))), b.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.6, alpha), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(b.outputs['BSDF'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
LUNG_M = lung_mat('lung', (0.95, 0.42, 0.45), (0.38, 0.36, 0.62), 0.38)
TRACH_M = lung_mat('trachea', (0.95, 0.8, 0.75), (0.7, 0.7, 0.85), 0.5)
DIAPH_M = lung_mat('diaphragm', (0.75, 0.2, 0.18), (0.4, 0.25, 0.4), 0.22)
for k_, m_ in (('lung', LUNG_M), ('trachea', TRACH_M), ('diaphragm', DIAPH_M)):
    for o in kind(k_): o.data.materials.clear(); o.data.materials.append(m_); o['oxy'] = 1.0; o['tt'] = 0.0
def centre(o): return sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
LUNGS = kind('lung'); LC = sum((centre(o) for o in LUNGS), Vector()) / len(LUNGS)
for o in LUNGS + kind('diaphragm'):                                      # breathe about the middle of the chest (shrunk 6% to sit inside him)
    c_ = LC
    for v in o.data.vertices: v.co = (v.co - c_) * 0.94
    o.location = c_; o['home'] = list(c_)
XRAY_OBJS = ANAT
def lungs(t, oxy=1.0, rate=0.25, depth=1.0):
    """breathing: rate = breaths a second; oxy 0..1 colour"""
    ph = 0.5 - 0.5 * math.cos(2 * math.pi * rate * t); k = 1.0 + 0.045 * depth * ph
    for o in LUNGS: o.scale = (k, 1.0 + 0.03 * depth * ph, 1.0 + 0.06 * depth * ph); o['oxy'] = oxy; o['tt'] = t
    for o in kind('diaphragm'): o.scale = (1.0, 1.0, 1.0); o.location = Vector(o['home']) - V3(0, 0, 0.02 * depth * ph); o['oxy'] = oxy; o['tt'] = t
    for o in kind('trachea'): o['oxy'] = oxy; o['tt'] = t
for o in XRAY_OBJS: o.hide_render = True
