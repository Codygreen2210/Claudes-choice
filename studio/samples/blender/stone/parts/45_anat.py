# ================================================================ HIS URINARY SYSTEM (anat.blend: fitted in his rest space). His trunk stays
# straight in every x-ray shot (he leans from the hips), so the organs ride on the rig as one rigid piece
ANAT = []
with bpy.data.libraries.load(asset('anat.blend'), link=False) as (_s, _d): _d.objects = list(_s.objects)
for o in _d.objects:
    S.collection.objects.link(o); o.parent = RIG; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, 0, 0)
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False; ANAT.append(o)
AN = {o.name: o for o in ANAT}
def kind(k): return [o for o in ANAT if o['kind'] == k]
def bone_mat():
    m = mat('bone', (0.86, 0.82, 0.72), 0.55, sheen=0.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.004, 0.003, 0.002)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (0.75, 0.85, 1.0, 1); nt.links.new(math_(nt, 'MULTIPLY', lw.outputs['Facing'], 1.2), b.inputs['Emission Strength'])
    noisy(m, 400.0, 0.12, 0.05); return m
BONE_M = bone_mat()

for o in kind('bone'): o.data.materials.clear(); o.data.materials.append(BONE_M)
def organ_mat(name, col, alpha, rim=(1.0, 0.6, 0.5), pain_col=(1.0, 0.12, 0.05)):
    """soft translucent organ: you see the funnel and the stone through the kidney; 'pain' (object prop) makes it throb red"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.35; b.inputs['Coat Weight'].default_value = 0.4
    b.inputs['Subsurface Weight'].default_value = 0.3; b.inputs['Subsurface Radius'].default_value = (0.01, 0.004, 0.003)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35; pn = objattr(nt, 'pain')
    ec = nt.nodes.new('ShaderNodeMix'); ec.data_type = 'RGBA'; ec.inputs['A'].default_value = (*rim, 1); ec.inputs['B'].default_value = (*pain_col, 1); nt.links.new(pn, ec.inputs['Factor'])
    nt.links.new(ec.outputs['Result'], b.inputs['Emission Color'])
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', lw.outputs['Facing'], 0.8), math_(nt, 'MULTIPLY', pn, 2.5)), b.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_(nt, 'MINIMUM', math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.6, alpha), 1.0), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(b.outputs['BSDF'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
def flow_mat(name, col, glow_col, kind_):
    """tubes: bright bands run along 'arc' (m). props: glow, flow (bands strength), speed, tt; ureters also 'fillto' (m: full of held-back pee above this)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = 0.35; b.inputs['Coat Weight'].default_value = 0.3
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'
    ph = math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', arc.outputs['Fac'], 45.0 if kind_ == 'ureter' else 30.0), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), objattr(nt, 'speed')))
    band = math_(nt, 'POWER', math_(nt, 'MULTIPLY_ADD', math_(nt, 'SINE', math_(nt, 'MULTIPLY', ph, 6.2832)), 0.5, 0.5), 3.0)
    st = math_(nt, 'ADD', objattr(nt, 'glow'), math_(nt, 'MULTIPLY', band, objattr(nt, 'flow')))
    if kind_ == 'ureter':
        full = math_(nt, 'LESS_THAN', arc.outputs['Fac'], objattr(nt, 'fillto')); st = math_(nt, 'ADD', st, math_(nt, 'MULTIPLY', full, 3.0))
    b.inputs['Emission Color'].default_value = (*glow_col, 1); nt.links.new(st, b.inputs['Emission Strength']); return m
KID_M = organ_mat('kidney', (0.42, 0.11, 0.08), 0.42); PELV_M = organ_mat('renal_pelvis', (0.95, 0.78, 0.5), 0.55, rim=(1.0, 0.85, 0.45), pain_col=(1.0, 0.8, 0.1))
BLAD_M = organ_mat('bladder', (0.9, 0.62, 0.5), 0.4, rim=(1.0, 0.8, 0.5))
URE_M = flow_mat('ureter', (0.95, 0.75, 0.55), (1.0, 0.8, 0.2), 'ureter'); ART_M = flow_mat('artery', (0.75, 0.08, 0.06), (1.0, 0.2, 0.1), 'artery'); VEIN_M = flow_mat('vein', (0.12, 0.2, 0.6), (0.3, 0.45, 1.0), 'vein')
for k_, m_ in (('kidney', KID_M), ('pelvis', PELV_M), ('bladder', BLAD_M), ('ureter', URE_M), ('artery', ART_M), ('vein', VEIN_M)):
    for o in kind(k_):
        o.data.materials.clear(); o.data.materials.append(m_); o['pain'] = 0.0; o['glow'] = 0.3; o['flow'] = 0.0; o['speed'] = 1.0; o['tt'] = 0.0; o['fillto'] = -1.0
KIDR, KIDL, PELR, PELL, BLAD, URER, UREL = (AN[n] for n in ('Kidney.r', 'Kidney.l', 'Renal pelvis.r', 'Renal pelvis.l', 'Urinary bladder', 'Ureter.r', 'Ureter.l'))
def centre(o): return sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
KC, PC, BC = centre(KIDR), centre(PELR), centre(BLAD)                # rig (rest) space
for o in (KIDR, PELR):                                                # so they can swell about their own middle
    c_ = centre(o)
    for v in o.data.vertices: v.co -= c_
    o.location = c_; o['home'] = list(c_)
_uv = np.array([v.co[:] for v in URER.data.vertices]).reshape(-1, 10, 3).mean(1)
URE_CL = [Vector(p) for p in _uv]                                     # the right ureter's centre line, kidney end first
URE_ARC = [0.0]
for i in range(1, len(URE_CL)): URE_ARC.append(URE_ARC[-1] + (URE_CL[i] - URE_CL[i - 1]).length)
URE_LEN = URE_ARC[-1]
def ure_pt(s):
    """point at arc length s (m) down the right ureter (rig space); s < 0 = still up in the kidney's funnel"""
    if s <= 0: return URE_CL[0].lerp(PC + V3(0.006, 0, 0.012), clamp(-s / 0.03, 0, 1))
    s = min(s, URE_LEN - 1e-5); i = int(np.searchsorted(URE_ARC, s)) - 1; i = clamp(i, 0, len(URE_CL) - 2)
    return URE_CL[i].lerp(URE_CL[i + 1], (s - URE_ARC[i]) / max(URE_ARC[i + 1] - URE_ARC[i], 1e-9))
# ---- the stone: a clump of sharp crystals (calcium oxalate: little two-ended pyramids), yellow-brown
def crystal_mesh(name, n, seed, spread=1.0, size=1.0):
    rr = random.Random(seed); vs, fs = [], []
    for i in range(n):
        d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized(); c = Vector((d.x * 1.0, d.y * 0.8, d.z * 0.75)) * spread * rr.uniform(0.25, 1.0)
        s = size * rr.uniform(0.35, 0.75); ax = (d + Vector((rr.gauss(0, 0.5), rr.gauss(0, 0.5), rr.gauss(0, 0.5)))).normalized()
        u = ax.orthogonal().normalized(); w = ax.cross(u); b0 = len(vs)
        vs += [c + ax * s * 1.25, c - ax * s * 0.9] + [c + (u * math.cos(a_) + w * math.sin(a_)) * s * 0.62 for a_ in (0.4, 1.97, 3.54, 5.11)]
        for k in range(4): k2 = (k + 1) % 4; fs += [(b0, b0 + 2 + k, b0 + 2 + k2), (b0 + 1, b0 + 2 + k2, b0 + 2 + k)]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in vs], [], fs); me.update(); return me
def stone_mat(name='stone'):
    m = mat(name, (0.5, 0.33, 0.12), 0.5, coat=0.2); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    noisy(m, 300.0, 0.45, 0.2); b.inputs['Subsurface Weight'].default_value = 0.15; b.inputs['Subsurface Radius'].default_value = (0.3, 0.2, 0.1)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.3
    b.inputs['Emission Color'].default_value = (1.0, 0.75, 0.3, 1); nt.links.new(math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.6, objattr(nt, 'glow')), b.inputs['Emission Strength']); return m
STONE_M = stone_mat()
STONE = obj('stone', crystal_mesh('stone', 70, 5, 0.0042, 0.0032), STONE_M, parent=RIG); STONE['glow'] = 4.0; STONE.visible_shadow = False
for p_ in STONE.data.polygons: p_.use_smooth = False
SMALL = obj('stone_small', crystal_mesh('stone_small', 30, 9, 0.0011, 0.0009), STONE_M, parent=RIG); SMALL['glow'] = 1.5; SMALL.visible_shadow = False
HALO = prim('uv_sphere', 'stone_halo', emis('halo', (1.0, 0.8, 0.3), 25.0), parent=RIG, segments=12, ring_count=6, radius=0.0024)
XRAY_OBJS = ANAT + [STONE, SMALL, HALO]
