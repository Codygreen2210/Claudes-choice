# ================================================================ the fryer: burner stand + blue jets, propane tank and hose, aluminium stockpot, oil,
# the turkey (frozen: frost on the skin; x-ray: ghost skin with an ice core), poultry rack and lift hook
STEEL = mat('steel', (0.30, 0.30, 0.32), 0.38, 1.0); noisy(STEEL, 30.0, 0.15, 0.12)
CAST = mat('castiron', (0.05, 0.05, 0.055), 0.6, 0.7); noisy(CAST, 50.0, 0.3, 0.15)
HOSE = mat('hose', (0.03, 0.03, 0.035), 0.55)
BRASS = bpy.data.materials.get('brass') or mat('brass', (0.85, 0.62, 0.3), 0.25, 1.0)

# pot: brushed aluminium; object prop xr (0..1) turns it into a see-through ghost with lit edges
def pot_mat(name):
    m = mat(name, (0.93, 0.93, 0.95), 0.40, 0.88); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    try: b.inputs['Anisotropic'].default_value = 0.6
    except Exception: pass
    nz = tnoise(nt, coord(nt, 'Object'), 900.0, 1.0)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.36; mr.inputs['To Max'].default_value = 0.44
    nt.links.new(nz, mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    out = nt.nodes['Material Output']; tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.55, 0.8, 1.0, 1); fr = nt.nodes.new('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.08
    rim = math_(nt, 'POWER', fr.outputs['Facing'], 3.0); em_s = nt.nodes.new('ShaderNodeMath'); em_s.operation = 'MULTIPLY'
    nt.links.new(rim, em_s.inputs[0]); em_s.inputs[1].default_value = 1.2; nt.links.new(em_s.outputs[0], em.inputs['Strength'])
    ghost = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr.outputs[0], ghost.inputs[0]); nt.links.new(em.outputs[0], ghost.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac'])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(ghost.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def oil_mat(name, hot=0.0):
    m = mat(name, (0.95, 0.62, 0.12), 0.06, 0.0, trans=1.0, ior=1.47); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (1.0, 0.55, 0.12, 1); b.inputs['Emission Strength'].default_value = 0.08 + hot
    try: b.inputs['Transmission Weight'].default_value = 0.92
    except Exception: pass
    return m

def skin_mat(name, frost=True):
    """raw turkey skin with goose bumps; object props frost (white crystals) and xr (ghost) and cook (browning)"""
    m = mat(name, (0.93, 0.77, 0.68), 0.42); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.35; b.inputs['Subsurface Radius'].default_value = (0.9, 0.35, 0.25)
    try: b.inputs['Subsurface Scale'].default_value = 0.02
    except Exception: pass
    co = coord(nt, 'Object'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 140.0; nt.links.new(co, vo.inputs['Vector'])
    goose = math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY', vo.outputs['Distance'], 2.6), 1.0)), 4.0)
    blot = tnoise(nt, co, 9.0, 4.0)
    base = mixc(nt, blot, (0.92, 0.64, 0.50), (0.80, 0.48, 0.40))
    cook = objattr(nt, 'cook'); base = mixc(nt, cook, base, (0.62, 0.36, 0.13))
    fz = objattr(nt, 'frost'); vf = nt.nodes.new('ShaderNodeTexVoronoi'); vf.inputs['Scale'].default_value = 260.0; nt.links.new(co, vf.inputs['Vector'])
    crys = math_(nt, 'MULTIPLY', fz, math_(nt, 'MULTIPLY', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', tnoise(nt, co, 22.0, 6.0), 0.5), 0.0), 2.4))
    col = mixc(nt, math_(nt, 'MINIMUM', crys, 1.0), base, (0.93, 0.96, 1.0))
    nt.links.new(col, b.inputs['Base Color'])
    nt.links.new(math_(nt, 'ADD', 0.40, math_(nt, 'MULTIPLY', fz, -0.15)), b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.0006
    nt.links.new(math_(nt, 'ADD', goose, math_(nt, 'MULTIPLY', fz, math_(nt, 'MULTIPLY', vf.outputs['Distance'], 1.5))), bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    try: b.inputs['Coat Weight'].default_value = 0.0
    except Exception: pass
    # x-ray ghost: faint pink rim + see-through
    out = nt.nodes['Material Output']; tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (1.0, 0.55, 0.45, 1); lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.25
    es = math_(nt, 'ADD', 0.15, math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 1.4), 5.0)); nt.links.new(es, em.inputs['Strength'])
    gh = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr.outputs[0], gh.inputs[0]); nt.links.new(em.outputs[0], gh.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac'])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(gh.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def blob_union(name, parts, voxel=0.0055, m=None):
    """join ellipsoids/capsules and voxel-remesh them into one smooth skin"""
    objs = []
    for kind, a_, b_, r_ in parts:
        if kind == 'e':
            o = prim('uv_sphere', name + '_p', None, loc=a_, scale=b_, segments=24, ring_count=14, radius=1.0); objs.append(o)
        else:
            pts = [Vector(a_).lerp(Vector(b_), u) for u in np.linspace(0, 1, 8)]
            o = tube(name + '_c', [tuple(p) for p in pts], (lambda u, r0=r_[0], r1=r_[1]: lerp(r0, r1, u)), None, seg=14); objs.append(o)
            for p_, rr in ((a_, r_[0]), (b_, r_[1])): objs.append(prim('uv_sphere', name + '_cap', None, loc=p_, scale=(rr, rr, rr), segments=14, ring_count=8, radius=1.0))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); o = bpy.context.active_object; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    rm = o.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel
    sm_ = o.modifiers.new('sm', 'SMOOTH'); sm_.factor = 0.8; sm_.iterations = 6
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); old = o.data
    o.modifiers.clear(); o.data = me; bpy.data.meshes.remove(old)
    for p in o.data.polygons: p.use_smooth = True
    if m: o.data.materials.append(m)
    return o

def build_turkey(name, m_skin):
    """upright on the rack, neck end down, drumsticks up; origin at the bottom; breast faces -y"""
    parts = [('e', (0, 0.01, 0.17), (0.125, 0.108, 0.16), None), ('e', (0, -0.04, 0.16), (0.112, 0.09, 0.135), None),
             ('e', (0, 0.02, 0.045), (0.068, 0.062, 0.055), None), ('e', (0, 0.05, 0.27), (0.09, 0.06, 0.06), None)]
    for s in (-1, 1):
        parts += [('e', (s * 0.098, 0.0, 0.25), (0.058, 0.07, 0.08), None),
                  ('c', (s * 0.095, -0.03, 0.29), (s * 0.035, -0.115, 0.335), (0.04, 0.02)),
                  ('e', (s * 0.03, -0.12, 0.338), (0.019, 0.019, 0.017), None),
                  ('e', (s * 0.112, 0.03, 0.105), (0.034, 0.055, 0.075), None)]
    o = blob_union(name, parts, m=m_skin)
    o['frost'] = 1.0; o['xr'] = 0.0; o['cook'] = 0.0
    # knuckle ends of the drumsticks (bone tips), a little darker
    knk = mat('knuckle', (0.92, 0.86, 0.80), 0.4)
    for s in (-1, 1): prim('uv_sphere', f'{name}_knk{s}', knk, parent=o, loc=(s * 0.026, -0.128, 0.342), scale=(0.014, 0.014, 0.012), segments=12, ring_count=8)
    tube(f'{name}_twine', [(-0.04, -0.112, 0.33), (0, -0.13, 0.334), (0.04, -0.112, 0.33)], 0.0025, mat('twine', (0.85, 0.80, 0.68), 0.8), o, seg=6)
    return o

ICE_M = mat('ice', (0.6, 0.85, 1.0), 0.05, trans=0.85, ior=1.31, emit=(0.3, 0.6, 1.0), estr=0.45)
WATER_M = mat('waterdrop', (0.45, 0.75, 1.0), 0.04, trans=0.6, ior=1.33, emit=(0.25, 0.55, 1.0), estr=1.2)
STEAMB_M = mat('steambubble', (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=0.72, emit=(0.8, 0.9, 1.0), estr=0.05)

def build_fryer(name, at, safe=False):
    F = {'at': Vector(at)}; X, Y, Z = at
    root = empty(name, loc=at); F['root'] = root
    # stand: a ring on three splayed legs, a cross brace, the burner head with its jet ring
    RING_Z = 0.32
    tube(f'{name}_ring', [(0.2 * math.cos(2 * math.pi * k / 40), 0.2 * math.sin(2 * math.pi * k / 40), RING_Z) for k in range(41)], 0.011, STEEL, root, seg=8, caps=False)
    for k in range(3):
        a_ = 2 * math.pi * k / 3 + 0.5
        tube(f'{name}_leg{k}', [(0.2 * math.cos(a_), 0.2 * math.sin(a_), RING_Z), (0.29 * math.cos(a_), 0.29 * math.sin(a_), 0.0)], 0.012, STEEL, root, seg=8)
        prim('cylinder', f'{name}_foot{k}', HOSE, root, loc=(0.29 * math.cos(a_), 0.29 * math.sin(a_), 0.008), scale=(0.022, 0.022, 0.008), vertices=12)
        tube(f'{name}_brace{k}', [(0.24 * math.cos(a_), 0.24 * math.sin(a_), 0.17), (0.04 * math.cos(a_), 0.04 * math.sin(a_), 0.17)], 0.008, STEEL, root, seg=6)
    for k in range(3):
        a_ = 2 * math.pi * k / 3 + 0.5 + math.pi / 3
        box(f'{name}_tab{k}', (0.05, 0.02, 0.02), (0.185 * math.cos(a_), 0.185 * math.sin(a_), RING_Z + 0.012), STEEL, rot=(0, 0, a_), parent=root)
    lathe(f'{name}_burner', [(0.0, 0.13), (0.075, 0.13), (0.08, 0.155), (0.072, 0.17), (0.04, 0.172), (0.0, 0.172)], 32, CAST, root)
    tube(f'{name}_venturi', [(0.0, 0.0, 0.15), (0.0, -0.12, 0.15), (0.0, -0.24, 0.165)], 0.016, CAST, root, seg=10)
    lathe(f'{name}_valve', [(0.0, 0.0), (0.02, 0.0), (0.02, 0.04), (0.0, 0.04)], 12, BRASS, root, loc=(0, -0.27, 0.145))
    # blue jets: little cones around the burner head (flicker set per frame)
    jet_m = bpy.data.materials.get('jet')
    if jet_m is None:
        jet_m = emis_mix('jet', (0.06, 0.22, 1.0), 2.0, 'ja'); ntj = jet_m.node_tree; mxj = next(n for n in ntj.nodes if n.type == 'MIX_SHADER')
        zj = sepz(ntj, coord(ntj, 'Generated')).outputs['Z']; fadej = math_(ntj, 'MULTIPLY', math_(ntj, 'POWER', math_(ntj, 'SUBTRACT', 1.0, zj), 1.5), 0.75)
        for l in list(ntj.links):
            if l.to_socket == mxj.inputs['Fac']: ntj.links.remove(l)
        ntj.links.new(fadej, mxj.inputs['Fac'])
        ej = next(n for n in ntj.nodes if n.type == 'EMISSION'); ntj.links.new(mixc(ntj, zj, (0.35, 0.55, 1.0), (0.02, 0.08, 0.9)), ej.inputs['Color'])
    JETS = []
    for k in range(18):
        a_ = 2 * math.pi * k / 18
        j = prim('cone', f'{name}_jet{k}', jet_m, root, loc=(0.062 * math.cos(a_), 0.062 * math.sin(a_), 0.2), vertices=8, radius1=1.0, depth=2.0); j.scale = (0.008, 0.008, 0.03)
        j.rotation_euler = (0.5 * math.sin(a_) * -1 * 0, 0, 0); j['ja'] = 1.0; JETS.append(j)
    F['jets'] = JETS
    blue_l = light_at(f'{name}_burnlight', 'POINT', (X, Y, Z + 0.22), (X, Y, Z + 1), 18, (0.35, 0.5, 1.0), 0.05); F['burnlight'] = blue_l
    # the pot
    POT_Z = RING_Z + 0.012; PH = 0.42; PR = 0.17; F['pot_z'] = Z + POT_Z; F['pr'] = PR; F['ph'] = PH
    pm = pot_mat(f'{name}_potm')
    prof = [(0.0, 0.0), (PR - 0.012, 0.0), (PR, 0.01), (PR, PH - 0.006), (PR + 0.006, PH), (PR + 0.003, PH + 0.006), (PR - 0.004, PH + 0.004), (PR - 0.004, 0.006), (0.0, 0.006)]
    pot = lathe(f'{name}_pot', prof, 96, pm, root, loc=(0, 0, POT_Z)); pot['xr'] = 0.0; F['pot'] = pot
    for s in (-1, 1):
        tube(f'{name}_handle{s}', [(s * PR, -0.045, POT_Z + PH - 0.07), (s * (PR + 0.045), -0.04, POT_Z + PH - 0.065), (s * (PR + 0.05), 0, POT_Z + PH - 0.06),
                                   (s * (PR + 0.045), 0.04, POT_Z + PH - 0.065), (s * PR, 0.045, POT_Z + PH - 0.07)], 0.007, pm, pot, seg=8)
    # thermometer clipped to the rim: dial + probe
    if not safe:
        tube(f'{name}_probe', [(0.12, -0.11, POT_Z + PH + 0.05), (0.11, -0.1, POT_Z + 0.15)], 0.003, STEEL, pot, seg=6)
        dial = lathe(f'{name}_dial', [(0.0, 0.0), (0.028, 0.0), (0.03, 0.01), (0.0, 0.012)], 24, STEEL, pot, loc=(0.12, -0.11, POT_Z + PH + 0.05))
        dial.rotation_euler = (R(75), 0, R(-48));
        face_m = mat('dialface', (0.95, 0.95, 0.92), 0.4)
        df = prim('cylinder', f'{name}_dialface', face_m, dial, loc=(0, 0, 0.0115), scale=(0.025, 0.025, 0.001), vertices=24)
        box(f'{name}_needle', (0.002, 0.02, 0.001), (0.0, 0.006, 0.0135), mat('needle', (0.8, 0.05, 0.03), 0.4), parent=dial)
    # oil: the top surface (ripples by bump + bubbles), and the body (seen in x-ray)
    OIL_M = oil_mat(f'{name}_oilm')
    nt = OIL_M.node_tree; b = nt.nodes['Principled BSDF']; wv = nt.nodes.new('ShaderNodeTexNoise'); wv.inputs['Scale'].default_value = 40.0
    nt.links.new(coord(nt, 'Object'), wv.inputs['Vector']); w4 = nt.nodes.new('ShaderNodeValue'); wv.noise_dimensions = '4D'
    nt.links.new(objattr(nt, 'ph'), wv.inputs['W']); bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Distance'].default_value = 0.002
    nt.links.new(objattr(nt, 'boil'), bp.inputs['Strength']); nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    top = prim('circle', f'{name}_oiltop', OIL_M, root, loc=(0, 0, POT_Z + 0.2), radius=PR - 0.005, vertices=64, fill_type='NGON')
    top['ph'] = 0.0; top['boil'] = 0.05; F['oiltop'] = top
    OB_M = bpy.data.materials.get('oilbody_m')
    if OB_M is None:
        OB_M = bpy.data.materials.new('oilbody_m'); OB_M.use_nodes = True; nt2 = OB_M.node_tree; nt2.nodes.remove(nt2.nodes['Principled BSDF'])
        tr2 = nt2.nodes.new('ShaderNodeBsdfTransparent'); tr2.inputs['Color'].default_value = (0.97, 0.66, 0.24, 1)
        em2 = nt2.nodes.new('ShaderNodeEmission'); em2.inputs['Color'].default_value = (1.0, 0.55, 0.12, 1); em2.inputs['Strength'].default_value = 0.06
        gl2 = nt2.nodes.new('ShaderNodeBsdfGlossy'); gl2.inputs['Roughness'].default_value = 0.05; lw2 = nt2.nodes.new('ShaderNodeLayerWeight'); lw2.inputs['Blend'].default_value = 0.15
        mx2 = nt2.nodes.new('ShaderNodeMixShader'); nt2.links.new(lw2.outputs['Fresnel'], mx2.inputs['Fac']); nt2.links.new(tr2.outputs[0], mx2.inputs[1]); nt2.links.new(gl2.outputs[0], mx2.inputs[2])
        ad2 = nt2.nodes.new('ShaderNodeAddShader'); nt2.links.new(mx2.outputs[0], ad2.inputs[0]); nt2.links.new(em2.outputs[0], ad2.inputs[1])
        nt2.links.new(ad2.outputs[0], nt2.nodes['Material Output'].inputs['Surface'])
    body = prim('cylinder', f'{name}_oilbody', OB_M, root, loc=(0, 0, POT_Z + 0.1), vertices=64); body.scale = (PR - 0.006, PR - 0.006, 0.1)
    body.hide_render = True; F['oilbody'] = body
    # the turkey on its rack
    sk = skin_mat(f'{name}_skin')
    tk = build_turkey(f'{name}_turkey', sk); tk.parent = root; F['turkey'] = tk
    if safe: tk['frost'] = 0.0; tk['cook'] = 0.85
    rack = empty(f'{name}_rack', root); tk.parent = rack; tk.location = (0, 0, 0.012); F['rack'] = rack
    lathe(f'{name}_rackplate', [(0.0, 0.0), (0.095, 0.0), (0.1, 0.012), (0.095, 0.014), (0.0, 0.006)], 32, STEEL, rack)
    for k in range(6):
        a_ = 2 * math.pi * k / 6; tube(f'{name}_rackwire{k}', [(0.09 * math.cos(a_), 0.09 * math.sin(a_), 0.01), (0.03 * math.cos(a_), 0.03 * math.sin(a_), 0.10)], 0.0035, STEEL, rack, seg=6)
    tube(f'{name}_rackrod', [(0, 0, 0.0), (0, 0, 0.50)], 0.006, STEEL, rack, seg=8)
    tube(f'{name}_rackloop', [(0.022 * math.cos(2 * math.pi * k / 20), 0, 0.522 + 0.022 * math.sin(2 * math.pi * k / 20)) for k in range(21)], 0.004, STEEL, rack, seg=6, caps=False)
    # ice core (inside the breast) + the melt water that runs out of the bottom
    if not safe:
        ice = prim('ico_sphere', f'{name}_ice', ICE_M, tk, loc=(0, -0.01, 0.16), subdivisions=2); ice.scale = (0.085, 0.07, 0.11)
        for p_ in ice.data.polygons: p_.use_smooth = False
        dp = ice.modifiers.new('d', 'DISPLACE'); tx_ = bpy.data.textures.new('icetx', 'VORONOI'); tx_.noise_scale = 0.05; dp.texture = tx_; dp.strength = 0.012
        ice.hide_render = True; F['ice'] = ice
        # rack hook: a J-hook in the loop, long rod up to a T-handle (held at frame one, then left leaning on the rim)
        hk = empty(f'{name}_hook', rack, loc=(0, 0, 0.522)); F['hook'] = hk
        tube(f'{name}_hookj', [(0.0, 0.0, -0.02), (0.012, 0, -0.03), (0.02, 0, -0.012), (0.012, 0, 0.012), (-0.04, 0, 0.05), (-0.2, 0, 0.09), (-0.44, 0, 0.11)], 0.0055, STEEL, hk, seg=8)
        tube(f'{name}_hookT', [(-0.44, -0.12, 0.11), (-0.44, 0.12, 0.11)], 0.012, mat('grip', (0.08, 0.08, 0.09), 0.6), hk, seg=10)
    else:
        tk['frost'] = 0.0
    # hose from the valve to the tank regulator
    return F

FRY = build_fryer('fryer', (0.0, 1.05, DECK_Z))
SAFE = build_fryer('safe', (3.6, -8.6, 0.0), safe=True)
try:
    TANK = P.place('ph:propane_tank', loc=(0.62, 1.42, DECK_Z), rot_deg=30, height=0.55, name='tank')
    TANK2 = P.place('ph:propane_tank', loc=(4.2, -8.25, 0.0), rot_deg=-20, height=0.55, name='tank2')
except Exception as e_: print('tank skipped', e_)
def hose(nm, p0, p1, sag=0.08):
    p0 = Vector(p0); p1 = Vector(p1); pts = []
    for u in np.linspace(0, 1, 24):
        q = p0.lerp(p1, u); q.z -= sag * 4 * u * (1 - u) + 0.0; pts.append(tuple(q))
    tube(nm, pts, 0.008, HOSE, seg=8)
for F_, tk_ in ((FRY, (0.62, 1.42, DECK_Z)), (SAFE, (4.2, -8.25, 0.0))):
    a0 = F_['at'] + Vector((0, -0.27, 0.165)); top_ = Vector(tk_) + Vector((0, 0, 0.6))
    hose(F_['root'].name + '_hose', a0, top_, sag=0.35)
    lathe(F_['root'].name + '_reg', [(0.0, 0.0), (0.025, 0.0), (0.03, 0.03), (0.0, 0.035)], 16, BRASS, loc=tuple(top_))
