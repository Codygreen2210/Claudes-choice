# x-ray look: glass skin; 'pain' (0..1) lights his right side red around the kidney; 'tt' = time for its flicker
def xray_skin_mat():
    m = bpy.data.materials.new('xskin'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
    rp = nt.nodes.new('ShaderNodeAttribute'); rp.attribute_type = 'GEOMETRY'; rp.attribute_name = 'rest_position'
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rp.outputs['Vector'], sx.inputs['Vector'])
    xx = math_(nt, 'ADD', sx.outputs['X'], 0.09); zz = math_(nt, 'SUBTRACT', sx.outputs['Z'], 1.07)
    side = math_(nt, 'EXPONENT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', xx, xx), -120.0), math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', zz, zz), -70.0)))
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 40.0
    nt.links.new(rp.outputs['Vector'], nz.inputs['Vector']); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'tt'), 5.0), nz.inputs['W'])
    hot = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', side, objattr(nt, 'pain')), math_(nt, 'MULTIPLY_ADD', nz.outputs['Fac'], 0.8, 0.6))
    fz = math_(nt, 'POWER', lw.outputs['Facing'], 2.0)
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.inputs['A'].default_value = (0.35, 0.62, 1.0, 1); base.inputs['B'].default_value = (1.0, 0.16, 0.08, 1)
    nt.links.new(math_(nt, 'MINIMUM', hot, 1.0), base.inputs['Factor'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(base.outputs['Result'], em.inputs['Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 1.0, 0.02), math_(nt, 'MULTIPLY', hot, 0.5)), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'ADD', math_(nt, 'MULTIPLY_ADD', fz, 0.5, 0.04), math_(nt, 'MULTIPLY', hot, 0.12)), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
XSKIN = xray_skin_mat()
BODY['pain'] = 0.0; BODY['tt'] = 0.0
BODY_MATS = [sl.material for sl in BODY.material_slots]
PUFF = BODY.modifiers.new('xray_puff', 'DISPLACE'); PUFF.strength = 0.0; PUFF.mid_level = 0.0      # skin 4 mm fuller in x-ray (anatomy stays inside)
bpy.context.view_layer.objects.active = BODY
while BODY.modifiers.find('xray_puff') > BODY.modifiers.find('Armature') + 1: bpy.ops.object.modifier_move_up(modifier='xray_puff')
