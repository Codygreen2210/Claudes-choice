# ================================================================ THE MAP (2006): his trailer, the path the tornado carried him (398 m = 1,307 ft,
# a glowing dashed arc that draws itself), where he landed
LAND = TR + V3(240.0, 318.0, 0.0)                                       # 398 m from the trailer
def path_mat():
    m = bpy.data.materials.new('path'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'
    dash = math_(nt, 'LESS_THAN', math_(nt, 'FRACT', math_(nt, 'MULTIPLY', arc.outputs['Fac'], 0.06)), 0.6)
    show = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', arc.outputs['Fac'], objattr(nt, 'reach')), dash)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.82, 0.25, 1); em.inputs['Strength'].default_value = 25.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(show, mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
def path_obj():
    pts = []
    for k in range(200):
        s = k / 199; p = TR.lerp(LAND, s) + V3(0, 0, 60 * math.sin(math.pi * s) + 1.0); p += V3(-25 * math.sin(math.pi * s), 15 * math.sin(2 * math.pi * s), 0); pts.append(p)
    vs, fs, av = [], [], []; SEG = 8; arc = [0.0]
    for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized(); x = d.cross(V3(0, 0, 1)).normalized(); y = d.cross(x)
        for q in range(SEG): aa = 2 * math.pi * q / SEG; vs.append(tuple(p + (x * math.cos(aa) + y * math.sin(aa)) * 2.2)); av.append(arc[i])
    for i in range(len(pts) - 1):
        for q in range(SEG): a_ = i * SEG + q; b_ = i * SEG + (q + 1) % SEG; fs.append((a_, b_, b_ + SEG, a_ + SEG))
    me = bpy.data.meshes.new('path'); me.from_pydata(vs, [], fs); me.update(); at = me.attributes.new('arc', 'FLOAT', 'POINT'); at.data.foreach_set('value', av)
    o = obj('path', me, path_mat()); o['reach'] = 0.0; o.visible_shadow = False; return o, pts, arc
PATH, PATH_PTS, PATH_ARC = path_obj()
PIN0 = prim('cylinder', 'pin_start', emis('pin0', (1.0, 0.3, 0.2), 30.0), loc=TR + V3(0, 0, 1), vertices=32, radius=7, depth=1.5)
PIN1 = prim('cylinder', 'pin_end', emis('pin1', (0.3, 1.0, 0.4), 30.0), loc=LAND + V3(0, 0, 1), vertices=32, radius=7, depth=1.5)
DOT = prim('uv_sphere', 'flying_dot', emis('dot', (1.0, 0.95, 0.8), 60.0), segments=16, ring_count=8, radius=4.5)
MAPSET = [PATH, PIN0, PIN1, DOT]
def path_at(s):
    s = clamp(s, 0, 1) * PATH_ARC[-1]; i = int(np.searchsorted(PATH_ARC, s)) - 1; i = clamp(i, 0, len(PATH_PTS) - 2)
    return PATH_PTS[i].lerp(PATH_PTS[i + 1], (s - PATH_ARC[i]) / max(PATH_ARC[i + 1] - PATH_ARC[i], 1e-9))
