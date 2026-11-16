# ================================================================ materials: dark glossy track so the glowing marbles light it up
def track_mat(name, col, rough=0.28):
    m = mat(name, col, rough, 0.0, coat=0.6); noisy(m, 9.0, 0.10, 0.06); return m
M = dict(track=track_mat('track', (0.035, 0.038, 0.045)), track2=track_mat('track2', (0.02, 0.05, 0.09)),
         track3=track_mat('track3', (0.06, 0.03, 0.08)), funnel=track_mat('funnel', (0.05, 0.05, 0.06), 0.18),
         glass=mat('glass', (0.92, 0.97, 1.0), 0.03, trans=1.0, ior=1.45), board=track_mat('board', (0.03, 0.06, 0.05)),
         peg=mat('peg', (0.75, 0.75, 0.78), 0.22, 1.0), wall=mat('wallm', (0.1, 0.1, 0.12), 0.3, 0.6), finish=track_mat('finish', (0.04, 0.04, 0.05)))
LED = {k: emis('led_' + k, c, 6.0) for k, c in (('white', (0.9, 0.92, 1.0)), ('cyan', (0.0, 0.75, 1.0)), ('orange', (1.0, 0.35, 0.02)),
       ('purple', (0.55, 0.1, 1.0)), ('green', (0.1, 1.0, 0.3)), ('blue', (0.1, 0.25, 1.0)), ('pink', (1.0, 0.1, 0.5)), ('yellow', (1.0, 0.8, 0.05)))}

def marble_mats(i):
    nm, col = COLS[i]
    # glass shell
    sh = bpy.data.materials.new(f'shell_{nm}'); sh.use_nodes = True; nt = sh.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*[0.6 + 0.4 * c for c in col], 1); b.inputs['Roughness'].default_value = 0.02
    b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.5
    b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = 0.6
    # glowing core with a swirl, so you can see it spin
    co = bpy.data.materials.new(f'core_{nm}'); co.use_nodes = True; nt = co.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 1.6; wv.inputs['Distortion'].default_value = 3.0; wv.inputs['Detail'].default_value = 2.0
    nt.links.new(coord(nt, 'Object'), wv.inputs['Vector'])
    hot = tuple(min(1.0, c * 0.5 + 0.55) for c in col)
    cc = ramp(nt, wv.outputs['Fac'], [(0.0, col), (0.45, col), (0.6, hot), (0.75, col), (1.0, tuple(c * 0.4 for c in col))])
    nt.links.new(cc, e_.inputs['Color']); e_.inputs['Strength'].default_value = 9.0
    nt.links.new(e_.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return sh, co

MARB = []
for i_ in range(NM):
    sh_, co_ = marble_mats(i_)
    mo = prim('uv_sphere', f'marble_{i_}', sh_, segments=40, ring_count=20, radius=MR)
    core = prim('uv_sphere', f'core_{i_}', co_, parent=mo, segments=24, ring_count=12, radius=MR * 0.62)
    lt = bpy.data.lights.new(f'mlight_{i_}', 'POINT'); lt.energy = 5.0; lt.color = COLS[i_][1]; lt.shadow_soft_size = MR * 0.6
    lo = bpy.data.objects.new(f'mlight_{i_}', lt); S.collection.objects.link(lo); lo.parent = mo
    try: lt.use_shadow = True
    except Exception: pass
    mo.rotation_mode = 'QUATERNION'; MARB.append(mo)
