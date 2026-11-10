def bone_mat():
    m = mat('bone', (0.86, 0.82, 0.72), 0.55, sheen=0.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (0.75, 0.85, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY', lw.outputs['Facing'], 1.2), b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
BONE_M = bone_mat()
