# ================================================================ the diver: the house MakeHuman man in a full 7 mm wetsuit and hood (no face shows: a
# twin-lens mask and regulator cover it), a BC vest with straps, pockets and an inflator hose, a steel tank with a first stage, an octopus and a
# pressure gauge, a weight belt, a dive knife on his calf, ribbed fins, and a mesh catch bag with lobsters in it. IK arms, a flutter kick.
GLOW_D = (1.0, 0.62, 0.22)
def wetsuit_mat():
    m = mat('neoprene', (0.016, 0.017, 0.02), 0.55, sheen=0.25); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    g = coord(nt, 'Generated'); sx = sepz(nt, g); ob = sepz(nt, coord(nt, 'Object'))
    # blue shoulder/chest panel, rubber knee pads, light stitch seams at the waist, the sides and round the arms
    panel = math_(nt, 'MULTIPLY', ramp_v(nt, sx.outputs['Z'], 0.80, 0.81), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, sx.outputs['Z'], 0.865, 0.875)))
    knee = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', ramp_v(nt, sx.outputs['Z'], 0.245, 0.255), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, sx.outputs['Z'], 0.315, 0.325))),
                 ramp_v(nt, math_(nt, 'MULTIPLY', ob.outputs['Y'], -1.0), 0.0, 0.03))
    seam = math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', ramp_v(nt, sx.outputs['Z'], 0.585, 0.587), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, sx.outputs['Z'], 0.589, 0.591))),
                 math_(nt, 'MULTIPLY', ramp_v(nt, math_(nt, 'ABSOLUTE', ob.outputs['X']), 0.150, 0.152), math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, math_(nt, 'ABSOLUTE', ob.outputs['X']), 0.154, 0.156))))
    col = mixc(nt, panel, (0.016, 0.017, 0.02), (0.02, 0.09, 0.22))
    col = mixc(nt, knee, col, (0.05, 0.05, 0.05)); col = mixc(nt, math_(nt, 'MULTIPLY', seam, 0.8), col, (0.22, 0.22, 0.24))
    nt.links.new(col, b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.004
    tx = nt.nodes.new('ShaderNodeTexNoise'); tx.inputs['Scale'].default_value = 900.0; nt.links.new(coord(nt, 'Object'), tx.inputs['Vector'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', tx.outputs['Fac'], 0.3), math_(nt, 'MULTIPLY', knee, math_(nt, 'MULTIPLY', ramp_v(nt, tnoise(nt, coord(nt, 'Object'), 260.0, 1.0), 0.4, 0.6), 1.0))), bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return xray_mix(m, GLOW_D)
NEO = wetsuit_mat()
NEO_PANEL = mat('neo_panel', (0.03, 0.10, 0.24), 0.5, sheen=0.2); xray_mix(NEO_PANEL, GLOW_D)
BCDM = mat('bcd', (0.025, 0.026, 0.03), 0.6, sheen=0.3); noisy(BCDM, 220.0, 0.3, 0.1); xray_mix(BCDM, GLOW_D)
WEBM = mat('webbing', (0.02, 0.02, 0.022), 0.8, sheen=0.4); noisy(WEBM, 400.0, 0.35, 0.1); xray_mix(WEBM, GLOW_D)
TANKM = mat('tank', (0.32, 0.34, 0.36), 0.35, metal=0.6, coat=0.5); noisy(TANKM, 30.0, 0.15, 0.1); xray_mix(TANKM, GLOW_D)
TANKBAND = mat('tankband', (0.85, 0.62, 0.05), 0.35, coat=0.5); xray_mix(TANKBAND, GLOW_D)
FINM = mat('fins', (0.02, 0.02, 0.025), 0.4, coat=0.3); xray_mix(FINM, GLOW_D)
FINB = mat('fin_blade', (0.04, 0.22, 0.58), 0.3, coat=0.5, trans=0.2); xray_mix(FINB, GLOW_D)
MASKG = mat('mask_glass', (0.01, 0.015, 0.02), 0.01, coat=1.0); xray_mix(MASKG, GLOW_D)
SKIRT = mat('mask_skirt', (0.02, 0.02, 0.025), 0.35, trans=0.3, coat=0.4); xray_mix(SKIRT, GLOW_D)
METAL = mat('metal', (0.75, 0.75, 0.78), 0.18, metal=1.0); xray_mix(METAL, GLOW_D)
OCTOM = mat('octo', (0.95, 0.78, 0.05), 0.35, coat=0.4); xray_mix(OCTOM, GLOW_D)
GAUGEF = mat('gauge_face', (0.92, 0.92, 0.88), 0.2, coat=1.0); xray_mix(GAUGEF, GLOW_D)
LEADM = mat('lead', (0.30, 0.31, 0.32), 0.55, metal=0.4); xray_mix(LEADM, GLOW_D)
BAGM = mat('bag', (0.95, 0.78, 0.1), 0.6); xray_mix(BAGM, GLOW_D)
LOBM = mat('lobster', (0.16, 0.10, 0.05), 0.35, coat=0.6); noisy(LOBM, 25.0, 0.4, 0.1); xray_mix(LOBM, GLOW_D)
KNIFEM = mat('knife', (0.75, 0.76, 0.78), 0.15, metal=1.0); xray_mix(KNIFEM, GLOW_D)
BONEM = emis('bones', (0.85, 0.95, 1.0), 4.0)
BRUISEM = emis_mix('bruise', (0.55, 0.12, 0.65), 1.8, 'alpha')

def bone_parent(o, rig, bone, world_pos, world_rot=None):
    """parent to a bone, keeping the rotation/scale the object already has, placed at world_pos (rest pose)"""
    bpy.context.view_layer.update()
    RS = o.matrix_world.to_3x3() if world_rot is None else world_rot
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = rig.matrix_world @ Matrix.Translation(Vector(world_pos)) @ RS.to_4x4()

def make_vest(name, body, rig, col):
    """the BC vest: the body's torso faces (chest, back, sides) pushed out ~2.5 cm, keeping his skin weights so it bends with him"""
    me_b = body.data; vg = {g.index: g.name for g in body.vertex_groups}
    def wmap(v): return {vg[g.group]: g.weight for g in v.groups if g.group in vg}
    keep = set()
    for v in me_b.vertices:
        w = wmap(v); z_ = v.co.z
        arm = sum(w.get(k, 0) for k in ('upperarm01.L', 'upperarm01.R', 'upperarm02.L', 'upperarm02.R', 'clavicle.L', 'clavicle.R'))
        if 0.98 < z_ < 1.40 and abs(v.co.x) < 0.24 and arm < 0.25 and not (v.co.y < -0.05 and abs(v.co.x) < 0.07 and z_ > 1.12): keep.add(v.index)
    ms = [i for i, m_ in enumerate(me_b.materials) if m_ and 'body' in m_.name] or [0]
    faces = [p_ for p_ in me_b.polygons if all(i in keep for i in p_.vertices)]
    used = sorted({i for p_ in faces for i in p_.vertices}); rid = {i: k for k, i in enumerate(used)}
    vs = [tuple(me_b.vertices[i].co + me_b.vertices[i].normal * 0.026) for i in used]
    fs = [tuple(rid[i] for i in p_.vertices) for p_ in faces]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = rig; o.matrix_parent_inverse = body.matrix_parent_inverse.copy(); o.matrix_basis = body.matrix_basis.copy()
    o.data.materials.append(BCDM); groups = {}
    for k, i in enumerate(used):
        for gn, w in wmap(me_b.vertices[i]).items():
            if w <= 0: continue
            if gn not in groups: groups[gn] = o.vertex_groups.new(name=gn)
            groups[gn].add([k], w, 'REPLACE')
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = rig; md.use_deform_preserve_volume = True
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.012; sol.offset = 1.0
    return o

class Diver:
    def __init__(self, name):
        with bpy.data.libraries.load(asset('man.blend'), link=False) as (_s, _d):
            _d.objects = [n for n in _s.objects if n.startswith('Human')]
        self.col = bpy.data.collections.new(name); S.collection.children.link(self.col)
        for o in _d.objects: self.col.objects.link(o)
        objs = list(_d.objects)
        self.rig = next(o for o in objs if o.type == 'ARMATURE'); self.PB = self.rig.pose.bones
        self.body = next(o for o in objs if o.name == 'Human')
        self.suit = next(o for o in objs if 'casualsuit' in o.name)
        for o in objs:
            if o.type == 'MESH' and o not in (self.body, self.suit): o.hide_render = o.hide_viewport = True     # hair, brows, lashes, eyes
        for ob in (self.body, self.suit):
            ob.data.materials.clear(); ob.data.materials.append(NEO)
            for md in ob.modifiers:
                if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
        for p_ in self.body.data.polygons: p_.material_index = 0
        sol = self.suit.modifiers.new('neo', 'SOLIDIFY'); sol.thickness = 0.004
        self.root = empty(name + '_root'); self.rig.parent = self.root; self.rig.location = (0, 0, 0); self.rig.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        self.gear = []
        g_ = self.gear
        def bp_(o, bone, pos=(0, 0, 0)): bone_parent(o, self.rig, bone, pos); g_.append(o); return o
        # mask: twin lenses in a hard frame, a soft skirt sealing round the face, a split strap with buckles
        for sx_ in (1, -1):
            fr = prim('cylinder', name + f'_lensframe{sx_}', FINM, radius=0.036, depth=0.022, vertices=24); fr.scale = (1.0, 1.0, 1.0); fr.rotation_euler = (R(90), 0, 0)
            fr.scale = (1.15, 0.95, 1.0); fr.rotation_euler = (R(90), 0, 0); bp_(fr, 'head', (sx_ * 0.036, -0.158, 1.533))
            ln = prim('cylinder', name + f'_lens{sx_}', MASKG, radius=0.031, depth=0.006, vertices=24); ln.scale = (1.15, 0.95, 1.0)
            ln.rotation_euler = (R(90), 0, 0); bp_(ln, 'head', (sx_ * 0.036, -0.170, 1.533))
        sk = prim('cube', name + '_skirt', SKIRT, size=1.0, scale=(0.155, 0.05, 0.078)); bevel(sk, 0.024, 4); bp_(sk, 'head', (0.0, -0.138, 1.524))
        nose = prim('cube', name + '_nosepocket', SKIRT, size=1.0, scale=(0.04, 0.04, 0.035)); bevel(nose, 0.012, 3); bp_(nose, 'head', (0.0, -0.162, 1.497))
        for k_, z_ in enumerate((1.545, 1.515)):
            st = tube(name + f'_strap{k_}', [(0.082 * math.cos(a_), -0.035 + 0.115 * math.sin(a_), z_ + 0.03 * math.sin(a_) * (k_ - 0.5)) for a_ in [math.pi * (1.0 + kk / 18) for kk in range(19)]][::-1] +
                      [], 0.007, WEBM, seg=6)
            bp_(st, 'head')
        for sx_ in (1, -1):
            bk = prim('cube', name + f'_buckle{sx_}', FINM, size=1.0, scale=(0.012, 0.03, 0.04)); bevel(bk, 0.004, 2); bp_(bk, 'head', (sx_ * 0.082, -0.12, 1.53))
        # regulator second stage: body, purge button, exhaust tee, mouthpiece; the hose over his right shoulder to the first stage
        rb = prim('cylinder', name + '_reg', FINM, radius=0.032, depth=0.045, vertices=20); rb.rotation_euler = (R(90), 0, 0); bp_(rb, 'head', (-0.012, -0.178, 1.455))
        pg = prim('cylinder', name + '_purge', mat('purge', (0.6, 0.6, 0.62), 0.3, metal=0.5), radius=0.024, depth=0.008, vertices=16); pg.rotation_euler = (R(90), 0, 0); bp_(pg, 'head', (-0.012, -0.203, 1.455))
        ex = prim('cube', name + '_exhaust', FINM, size=1.0, scale=(0.07, 0.025, 0.02)); bevel(ex, 0.008, 2); bp_(ex, 'head', (-0.012, -0.185, 1.425))
        bp_(tube(name + '_lp', [(-0.04, -0.175, 1.455), (-0.12, -0.15, 1.44), (-0.17, -0.04, 1.42), (-0.15, 0.10, 1.47), (-0.06, 0.22, 1.54), (0.0, 0.23, 1.57)], 0.0085, FINM, seg=8), 'neck01')
        # octopus (yellow backup) clipped at the chest on its own hose; inflator hose (corrugated) down the left shoulder
        oc_ = prim('cylinder', name + '_octo', OCTOM, radius=0.03, depth=0.042, vertices=18); oc_.rotation_euler = (R(80), 0, 0); bp_(oc_, 'spine02', (0.07, -0.16, 1.18))
        bp_(tube(name + '_octohose', [(0.07, -0.15, 1.19), (0.13, -0.11, 1.28), (0.15, 0.04, 1.36), (0.06, 0.19, 1.47), (0.02, 0.19, 1.50)], 0.008, OCTOM, seg=8), 'spine02')
        infl = [(0.12, -0.13, 1.08 + 0.02 * kk) for kk in range(1)]
        ip = [(0.13, -0.12, 1.06), (0.15, -0.11, 1.18), (0.15, -0.06, 1.33), (0.12, 0.05, 1.41)]
        bp_(tube(name + '_inflator', ip, lambda u: 0.014 * (1 + 0.18 * math.sin(u * 2 * math.pi * 22)), FINM, seg=10), 'spine02')
        bp_(prim('cube', name + '_inflhead', FINM, size=1.0, scale=(0.03, 0.03, 0.07)), 'spine02', (0.13, -0.125, 1.03))
        # pressure gauge console on its hose, hanging at the left hip
        bp_(tube(name + '_hp', [(0.05, 0.21, 1.54), (0.17, 0.12, 1.30), (0.20, 0.0, 1.05), (0.19, -0.06, 0.92)], 0.008, FINM, seg=8), 'spine03')
        gc = prim('cylinder', name + '_gauge', FINM, radius=0.038, depth=0.03, vertices=24); gc.rotation_euler = (R(90), 0, 0); bp_(gc, 'spine03', (0.19, -0.075, 0.90))
        gf = prim('cylinder', name + '_gaugeface', GAUGEF, radius=0.03, depth=0.004, vertices=24); gf.rotation_euler = (R(90), 0, 0); bp_(gf, 'spine03', (0.19, -0.092, 0.90))
        # BC vest: the torso's own shape pushed out, with a back plate, shoulder straps, a chest strap, a cummerbund, two pockets
        self.vest = make_vest(name + '_vest', self.body, self.rig, self.col); g_.append(self.vest)
        for sx_ in (1, -1):
            bp_(tube(name + f'_shstrap{sx_}', [(sx_ * 0.09, 0.10, 1.43), (sx_ * 0.13, -0.02, 1.44), (sx_ * 0.135, -0.135, 1.33), (sx_ * 0.12, -0.15, 1.15), (sx_ * 0.11, -0.14, 1.00)],
                       0.018, WEBM, seg=6), 'spine02')
            qr = prim('cube', name + f'_qr{sx_}', FINM, size=1.0, scale=(0.045, 0.02, 0.05)); bevel(qr, 0.006, 2); bp_(qr, 'spine02', (sx_ * 0.135, -0.155, 1.30))
            pk = prim('cube', name + f'_pocket{sx_}', BCDM, size=1.0, scale=(0.09, 0.05, 0.12)); bevel(pk, 0.02, 3); bp_(pk, 'spine03', (sx_ * 0.17, -0.10, 0.99))
            dr = prim('uv_sphere', name + f'_dring{sx_}', METAL, radius=0.012, segments=10, ring_count=6); dr.scale = (1, 0.4, 1); bp_(dr, 'spine02', (sx_ * 0.13, -0.16, 1.24))
        bp_(tube(name + '_chest', [(-0.13, -0.155, 1.27), (0.0, -0.17, 1.27), (0.13, -0.155, 1.27)], 0.01, WEBM, seg=6), 'spine02')
        bp_(tube(name + '_cummer', [(0.175 * math.cos(a_), -0.005 + 0.135 * math.sin(a_), 1.03) for a_ in [2 * math.pi * kk / 36 for kk in range(37)]], lambda u: 0.032, BCDM, seg=8, caps=False), 'spine03')
        # tank: a steel cylinder with a domed top, a yellow band, a valve, a first stage with ports, the cam band to the vest
        tk = lathe(name + '_tank', [(0.0, -0.36), (0.07, -0.355), (0.088, -0.33), (0.089, 0.24), (0.075, 0.31), (0.04, 0.345), (0.022, 0.36), (0.0, 0.36)], 32, TANKM)
        bp_(tk, 'spine02', (0.0, 0.225, 1.13))
        tb = prim('cylinder', name + '_tankband', TANKBAND, radius=0.0905, depth=0.05, vertices=32); bp_(tb, 'spine02', (0.0, 0.225, 1.33))
        vl = prim('cylinder', name + '_valve', METAL, radius=0.022, depth=0.07, vertices=16); bp_(vl, 'spine02', (0.0, 0.225, 1.52))
        kn = prim('cylinder', name + '_knob', FINM, radius=0.022, depth=0.016, vertices=16); bp_(kn, 'spine02', (0.0, 0.225, 1.565))
        fs_ = prim('cylinder', name + '_first', METAL, radius=0.026, depth=0.06, vertices=16); fs_.rotation_euler = (R(90), 0, 0); bp_(fs_, 'spine02', (0.0, 0.19, 1.515))
        for k_, a_ in enumerate((0.0, 1.5, 3.1, 4.6)):
            pt = prim('cylinder', name + f'_port{k_}', METAL, radius=0.008, depth=0.03, vertices=8)
            pt.rotation_euler = (0, R(90), a_); bp_(pt, 'spine02', (0.03 * math.cos(a_), 0.18, 1.515 + 0.03 * math.sin(a_)))
        for z_ in (0.98, 1.22):
            bp_(tube(name + f'_cam{z_}', [(0.093 * math.cos(a_), 0.225 + 0.093 * math.sin(a_), z_) for a_ in [2 * math.pi * kk / 24 for kk in range(25)]], 0.012, WEBM, seg=6, caps=False), 'spine02')
        # weight belt: webbing, lead blocks, a steel buckle
        bp_(tube(name + '_belt', [(0.168 * math.cos(a_), -0.005 + 0.128 * math.sin(a_), 0.955) for a_ in [2 * math.pi * kk / 40 for kk in range(41)]], 0.016, WEBM, seg=6, caps=False), 'spine04' if 'spine04' in self.rig.data.bones else 'spine03')
        for k_, a_ in enumerate((0.55, 1.0, 2.15, 2.6)):
            ld = prim('cube', name + f'_lead{k_}', LEADM, size=1.0, scale=(0.06, 0.035, 0.05)); bevel(ld, 0.008, 2)
            ld.rotation_euler = (0, 0, -a_ + math.pi / 2); bp_(ld, 'spine04' if 'spine04' in self.rig.data.bones else 'spine03', (0.17 * math.cos(-a_), -0.005 + 0.13 * math.sin(-a_), 0.955))
        bk = prim('cube', name + '_beltbuckle', METAL, size=1.0, scale=(0.06, 0.012, 0.045)); bevel(bk, 0.005, 2); bp_(bk, 'spine04' if 'spine04' in self.rig.data.bones else 'spine03', (0.0, -0.135, 0.955))
        # dive knife strapped to the inside of his right calf
        sh = prim('cube', name + '_sheath', FINM, size=1.0, scale=(0.035, 0.02, 0.17)); bevel(sh, 0.008, 2); bp_(sh, 'lowerleg01.R', (-0.10, -0.05, 0.36))
        hd_ = prim('cylinder', name + '_knifehandle', mat('knife_handle', (0.9, 0.35, 0.05), 0.4), radius=0.012, depth=0.09, vertices=10); bp_(hd_, 'lowerleg01.R', (-0.10, -0.05, 0.49))
        for z_ in (0.30, 0.42):
            bp_(tube(name + f'_kstrap{z_}', [(-0.165 + 0.065 * math.cos(a_), -0.03 + 0.06 * math.sin(a_), z_) for a_ in [2 * math.pi * kk / 20 for kk in range(21)]], 0.006, WEBM, seg=5, caps=False), 'lowerleg01.R')
        # fins: an open-heel foot pocket with a spring strap, a long blade with side rails, ribs and vents
        self.fins = {}
        for s_, x0 in (('L', 0.17), ('R', -0.17)):
            pk = prim('cube', name + '_footpocket' + s_, FINM, size=1.0, scale=(0.115, 0.25, 0.09)); bevel(pk, 0.032, 4); bp_(pk, 'foot.' + s_, (x0, -0.085, 0.05))
            bp_(tube(name + '_spring' + s_, [(x0 + 0.06, 0.02, 0.06), (x0 + 0.04, 0.085, 0.07), (x0, 0.10, 0.075), (x0 - 0.04, 0.085, 0.07), (x0 - 0.06, 0.02, 0.06)],
                     0.011, METAL, seg=8), 'foot.' + s_)
            n_ = 14; fv = []; ff = []
            for i in range(n_):
                u = i / (n_ - 1); w = lerp(0.10, 0.135, u) + 0.02 * math.sin(math.pi * u)
                for xx in (-1, -0.33, 0.33, 1): fv.append((x0 + xx * w, -0.19 - 0.56 * u, 0.03 - 0.025 * u - 0.012 * abs(xx) * u))
            for i in range(n_ - 1):
                for c_ in range(3): ff.append((i * 4 + c_, i * 4 + c_ + 1, (i + 1) * 4 + c_ + 1, (i + 1) * 4 + c_))
            bl = mesh(name + '_blade' + s_, fv, ff, FINB, smooth_=True); so = bl.modifiers.new('th', 'SOLIDIFY'); so.thickness = 0.01; subsurf(bl, 1)
            bp_(bl, 'foot.' + s_); self.fins[s_] = bl
            for xx in (-1, 1):
                bp_(tube(name + f'_rail{s_}{xx}', [(x0 + xx * 0.105, -0.15, 0.045), (x0 + xx * 0.125, -0.45, 0.02), (x0 + xx * 0.135, -0.74, 0.0)], lambda u: 0.014 * (1 - 0.5 * u), FINM, seg=8), 'foot.' + s_)
            for xx in (-0.45, 0.45):
                bp_(tube(name + f'_rib{s_}{xx}', [(x0 + xx * 0.1, -0.2, 0.038), (x0 + xx * 0.115, -0.55, 0.012)], 0.006, FINM, seg=6), 'foot.' + s_)
        # catch bag: a yellow mesh bag on a stainless frame handle, two lobsters inside
        bg = prim('uv_sphere', name + '_bag', BAGM, radius=0.15, segments=20, ring_count=12); bg.scale = (0.85, 0.85, 1.45)
        wf = bg.modifiers.new('net', 'WIREFRAME'); wf.thickness = 0.007; bp_(bg, 'wrist.L', (0.52, -0.26, 0.74)); self.bag = bg
        bp_(tube(name + '_baghandle', [(0.47, -0.26, 0.93), (0.52, -0.26, 0.97), (0.57, -0.26, 0.93)], 0.008, METAL, seg=6), 'wrist.L')
        for k_ in range(2):
            lc = Vector((0.52 + 0.04 * (k_ - 0.5), -0.26 + 0.03 * k_, 0.70 + 0.09 * k_))
            lb = prim('uv_sphere', name + f'_lobster{k_}', LOBM, radius=0.045, segments=14, ring_count=8); lb.scale = (0.55, 0.55, 1.6); bp_(lb, 'wrist.L', lc)
            for sx_ in (1, -1):
                cl = prim('uv_sphere', name + f'_claw{k_}{sx_}', LOBM, radius=0.028, segments=10, ring_count=6); cl.scale = (0.7, 0.5, 1.5)
                bp_(cl, 'wrist.L', lc + Vector((sx_ * 0.04, 0, 0.09)))
        # x-ray bones: glowing rods along the main bones (shown only in the x-ray beat), a skull, ribs
        self.bones = []
        for bn in ('upperarm01.L', 'upperarm02.L', 'lowerarm01.L', 'lowerarm02.L', 'upperarm01.R', 'upperarm02.R', 'lowerarm01.R', 'lowerarm02.R',
                   'upperleg01.L', 'upperleg02.L', 'lowerleg01.L', 'lowerleg02.L', 'upperleg01.R', 'upperleg02.R', 'lowerleg01.R', 'lowerleg02.R',
                   'spine01', 'spine02', 'spine03', 'spine04', 'spine05', 'neck01', 'neck02', 'clavicle.L', 'clavicle.R', 'pelvis.L', 'pelvis.R', 'foot.L', 'foot.R'):
            if bn not in self.rig.data.bones: continue
            b = self.rig.data.bones[bn]; L_ = (b.tail_local - b.head_local).length
            r_ = 0.022 if 'leg' in bn else (0.016 if 'arm' in bn else 0.02)
            ro = tube(name + '_xb_' + bn, [(0, 0, 0), (0, L_ * 0.5, 0), (0, L_, 0)], lambda u: r_ * (1.35 - 0.6 * math.sin(math.pi * u)), BONEM, seg=8)
            ro.parent = self.rig; ro.parent_type = 'BONE'; ro.parent_bone = bn; ro.matrix_parent_inverse.identity()
            ro.location = (0, -L_, 0)                                            # bone parenting puts the origin at the tail
            self.bones.append(ro)
        sk = prim('uv_sphere', name + '_xskull', BONEM, radius=0.085, segments=16, ring_count=10); sk.scale = (0.85, 1.0, 1.05)
        bone_parent(sk, self.rig, 'head', (0.0, -0.06, 1.57)); self.bones.append(sk)
        for j in range(6):
            z_ = 1.36 - 0.045 * j; rw = 0.12 + 0.012 * min(j, 3)
            rb = tube(name + f'_xrib{j}', [(rw * math.cos(a_), 0.02 + 0.09 * math.sin(a_), z_ - 0.03 * abs(math.cos(a_))) for a_ in [math.pi * (1 + k / 14) for k in range(15)]], 0.008, BONEM, seg=6)
            bone_parent(rb, self.rig, 'spine02', (0, 0, 0)); self.bones.append(rb)
        for o in self.bones: o.hide_render = True
        # bruises: soft purple patches that fade in over the x-ray
        self.bruises = []
        for j, (bn, off) in enumerate((('upperarm01.L', (0.04, 0, 0)), ('spine02', (0.08, -0.12, 0.0)), ('upperleg01.R', (-0.03, -0.08, 0)), ('spine04', (-0.1, -0.1, 0)),
                                      ('lowerleg01.L', (0.04, -0.05, 0)), ('upperarm02.R', (-0.04, -0.03, 0)), ('upperleg02.L', (0.06, -0.05, 0)))):
            if bn not in self.rig.data.bones: continue
            b = self.rig.data.bones[bn]; p = (b.head_local + b.tail_local) / 2 + Vector(off)
            bz = prim('uv_sphere', name + f'_bruise{j}', BRUISEM, radius=0.045 + 0.015 * (j % 3), segments=12, ring_count=8); bz.scale = (1.0, 1.0, 0.6)
            bone_parent(bz, self.rig, bn, p); bz['alpha'] = 0.0; bz.hide_render = True; self.bruises.append(bz)
        # IK arms
        self.tg = {k: empty(f'{name}_{k}') for k in ('hR', 'hL', 'pR', 'pL')}
        for s_ in ('R', 'L'):
            c = self.PB['wrist.' + s_].constraints.new('IK'); c.target = self.tg['h' + s_]; c.pole_target = self.tg['p' + s_]; c.chain_count = 5; c.pole_angle = R(-90); c.use_tail = True
        self.parts = [self.body, self.suit] + self.gear
    def world(self, p): return self.root.matrix_world @ Vector(p)
    def place(self, pos, fwd, up):
        """his head points along fwd (his body's up axis), his chest faces -up... we pass 'up' as where his back points"""
        Z = Vector(fwd).normalized(); Y = Vector(up).normalized(); Y = (Y - Z * Y.dot(Z)).normalized(); X = Y.cross(Z)
        self.root.matrix_world = Matrix.Translation(Vector(pos)) @ Matrix((X, Y, Z)).transposed().to_4x4()
    def kick(self, t, amp=1.0, f=1.6, bend=1.0):
        for s_, ph in (('L', 0.0), ('R', math.pi)):
            w = math.sin(2 * math.pi * f * t + ph)
            for nm, rot in (('upperleg01.' + s_, (R(-6 + 16 * amp * w), 0, 0)), ('lowerleg01.' + s_, (R((14 + 12 * amp * (1 + math.sin(2 * math.pi * f * t + ph - 0.9))) * bend), 0, 0)),
                            ('foot.' + s_, (R(48 + 10 * amp * w), 0, 0))):
                pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rot
    def legs(self, up=0.0, knee=0.0, foot=45.0, spread=0.0):
        for s_, sg in (('L', 1), ('R', -1)):
            for nm, rot in (('upperleg01.' + s_, (R(up), 0, R(sg * spread))), ('lowerleg01.' + s_, (R(knee), 0, 0)), ('foot.' + s_, (R(foot), 0, 0))):
                pb = self.PB[nm]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rot
    def spine(self, bend=0.0, head=0.0, twist=0.0):
        for n, k in (('spine03', 0.3), ('spine02', 0.3), ('spine01', 0.4)):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(bend * k), R(twist * k), 0)
        for n in ('neck01', 'head'):
            pb = self.PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(head * 0.5), 0, 0)
    def hands(self, hl, hr, pl=None, pr=None):
        self.tg['hL'].location = self.world(hl); self.tg['hR'].location = self.world(hr)
        self.tg['pL'].location = self.world(pl or (0.9, 0.4, 1.0)); self.tg['pR'].location = self.world(pr or (-0.9, 0.4, 1.0))
    def xray(self, v, bones=0.0, bruise=0.0):
        for o in self.parts: o['xr'] = v
        for o in self.bones: o.hide_render = bones < 0.05
        for o in self.bruises: o.hide_render = bruise < 0.05; o['alpha'] = bruise
    def show(self, on):
        for o in self.parts: o.hide_render = not on
        if not on:
            for o in self.bones + self.bruises: o.hide_render = True
DIVER = Diver('diver')
