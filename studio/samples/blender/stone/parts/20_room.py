# ================================================================ THE KITCHEN at night (z up, metres). He stands at the origin facing -y; the
# counter runs along his left (+x); the wall behind it has a window; warm light over the counter, cool night through the window
CX0, CX1, CY0, CY1, CTOP = 0.43, 1.05, -2.2, 1.3, 0.9                 # counter block: front face at CX0, top at CTOP
def tile_mat():
    m = mat('floor', (0.5, 0.42, 0.34), 0.35); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.5; br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Brick Width'].default_value = 0.9; br.inputs['Row Height'].default_value = 0.14
    br.inputs['Color1'].default_value = (0.34, 0.22, 0.13, 1); br.inputs['Color2'].default_value = (0.42, 0.28, 0.17, 1); br.inputs['Mortar'].default_value = (0.1, 0.07, 0.05, 1)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 4.0; nz.inputs['Detail'].default_value = 8
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (30, 1.5, 1)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.6
    nt.links.new(br.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Coat Weight'].default_value = 0.3; return m
FLOOR = box('floor', (7, 7, 0.1), (0, 0, -0.05), tile_mat())
WALL_M = noisy(mat('wall', (0.3, 0.36, 0.36), 0.85), 3.0, 0.08)
CAB_M = noisy(mat('cabinet', (0.16, 0.24, 0.3), 0.45, coat=0.2), 60.0, 0.1); TOP_M = noisy(mat('countertop', (0.82, 0.8, 0.76), 0.18, coat=0.5), 25.0, 0.2)
STEEL_M = mat('steel', (0.75, 0.76, 0.78), 0.22, metal=1.0); DARK_M = mat('dark', (0.03, 0.03, 0.035), 0.5)
WX = 1.08                                                              # the wall behind the counter
WALLS = [box('wall_side', (0.1, 7, 3), (WX + 0.05, 0, 1.5), WALL_M), box('wall_back', (7, 0.1, 3), (0, 1.75, 1.5), WALL_M)]
KIT = [box('cab_base', (CX1 - CX0 - 0.04, CY1 - CY0, CTOP - 0.14), ((CX0 + CX1) / 2 + 0.02, (CY0 + CY1) / 2, 0.1 + (CTOP - 0.14) / 2), CAB_M, 0.004),
       box('cab_kick', (CX1 - CX0 - 0.12, CY1 - CY0, 0.1), ((CX0 + CX1) / 2 + 0.06, (CY0 + CY1) / 2, 0.05), DARK_M),
       box('countertop', (CX1 - CX0 + 0.03, CY1 - CY0, 0.04), ((CX0 + CX1) / 2 - 0.015, (CY0 + CY1) / 2, CTOP - 0.02), TOP_M, 0.006)]
for i in range(6):                                                    # door fronts with steel pulls
    y = CY0 + (i + 0.5) * (CY1 - CY0) / 6
    KIT.append(box('door%d' % i, (0.018, (CY1 - CY0) / 6 - 0.012, CTOP - 0.2), (CX0 + 0.012, y, 0.1 + (CTOP - 0.14) / 2), CAB_M, 0.006))
    KIT.append(box('pull%d' % i, (0.012, 0.012, 0.14), (CX0 - 0.004, y + (0.2 if i % 2 == 0 else -0.2), 0.68), STEEL_M, 0.004))
# the sink and tap (he was getting a glass of water), the glass under the tap
SK = V3(0.78, -1.15, CTOP)
KIT += [box('sink_rim', (0.42, 0.56, 0.006), SK + V3(0, 0, 0.003), STEEL_M, 0.002), box('sink_hole', (0.38, 0.52, 0.004), SK + V3(0, 0, 0.0065), mat('basin', (0.55, 0.56, 0.58), 0.3, metal=0.8))]
KIT.append(tube('tap', [SK + V3(0.19, 0, 0.0), SK + V3(0.19, 0, 0.2), SK + V3(0.17, 0, 0.26), SK + V3(0.12, 0, 0.29), SK + V3(0.06, 0, 0.29), SK + V3(0.02, 0, 0.27), SK + V3(0.01, 0, 0.24)], 0.011, STEEL_M, seg=14))
subsurf(KIT[-1], 2)
KIT.append(prim('cylinder', 'tap_base', STEEL_M, loc=SK + V3(0.19, 0, 0.012), vertices=24, radius=0.022, depth=0.024))
KIT.append(box('tap_lever', (0.012, 0.07, 0.01), SK + V3(0.19, 0.045, 0.06), STEEL_M, 0.003))
def clear_mat(name, col, alpha, emit=0.0):
    m = mat(name, col, 0.03, coat=0.5, emit=col, estr=emit); nt = m.node_tree; b = nt.nodes['Principled BSDF']; lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.4
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY_ADD', lw.outputs['Facing'], 0.5, alpha), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(b.outputs['BSDF'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface']); return m
def glass_mat(): return clear_mat('glass', (0.9, 0.95, 1.0), 0.1)
GL = SK + V3(0.01, 0, 0.0075)                                          # the glass stands in the sink under the spout
GLASS_O = lathe('glass', [(0.0, 0.004), (0.031, 0.004), (0.036, 0.13), (0.0345, 0.13), (0.0295, 0.008), (0.0, 0.008)], 40, glass_mat(), loc=GL)
WATER_M = clear_mat('water', (0.45, 0.75, 1.0), 0.35, 0.5)
WATER = prim('cylinder', 'water', WATER_M, loc=GL + V3(0, 0, 0.0085), vertices=40, radius=0.029, depth=1.0)   # scaled in z each frame (origin moved to its base)
for v in WATER.data.vertices: v.co.z += 0.5
STREAM = prim('cylinder', 'stream', WATER_M, loc=GL, vertices=16, radius=0.0045, depth=1.0)
for v in STREAM.data.vertices: v.co.z += 0.5
KIT += [GLASS_O, WATER, STREAM]
for o in (GLASS_O, WATER, STREAM): o.visible_shadow = False
GLAMP = None
# things on the counter and the wall: a kettle, a fruit bowl, a knife block, a wall clock (3:12), a window with night outside
KIT.append(lathe('kettle', [(0.0, 0.0), (0.085, 0.0), (0.09, 0.02), (0.08, 0.15), (0.05, 0.2), (0.02, 0.215), (0.0, 0.215)], 40, STEEL_M, loc=(0.82, 0.25, CTOP))); subsurf(KIT[-1], 1)
KIT.append(tube('kettle_handle', [(0.82, 0.18, CTOP + 0.2), (0.82, 0.14, CTOP + 0.24), (0.82, 0.14, CTOP + 0.1), (0.82, 0.17, CTOP + 0.05)], 0.008, DARK_M, seg=10)); subsurf(KIT[-1], 2)
KIT.append(lathe('bowl', [(0.0, 0.006), (0.07, 0.006), (0.13, 0.07), (0.125, 0.07), (0.068, 0.012), (0.0, 0.012)], 40, mat('bowl', (0.85, 0.82, 0.75), 0.3, coat=0.4), loc=(0.78, 0.85, CTOP)))
_fr = random.Random(4)
for i in range(5):
    KIT.append(prim('uv_sphere', 'fruit%d' % i, noisy(mat('fruit%d' % i, [(0.85, 0.35, 0.05), (0.75, 0.08, 0.06), (0.8, 0.6, 0.1)][i % 3], 0.4), 90, 0.2),
                    loc=(0.78 + 0.05 * math.cos(i * 1.3), 0.85 + 0.05 * math.sin(i * 1.3), CTOP + 0.05 + (0.035 if i == 4 else 0)), segments=24, ring_count=12, radius=0.036))
KIT.append(box('block', (0.1, 0.14, 0.2), (0.9, -0.35, CTOP + 0.1), noisy(mat('wood', (0.4, 0.25, 0.13), 0.5), 20, 0.3), 0.008, rot=(0, R(-12), 0)))
WIN_Y, WIN_Z = -1.15, 1.55
KIT.append(box('win_glow', (0.02, 0.9, 0.8), (WX - 0.005, WIN_Y, WIN_Z), emis('night', (0.06, 0.1, 0.22), 1.5)))
FRAME_M = mat('frame', (0.85, 0.85, 0.82), 0.5)
for dy, dz, sy, sz in ((0, 0.42, 0.98, 0.05), (0, -0.42, 0.98, 0.05), (0.47, 0, 0.05, 0.89), (-0.47, 0, 0.05, 0.89), (0, 0, 0.03, 0.8), (0, 0, 0.9, 0.03)):
    KIT.append(box('winf', (0.05, sy, sz), (WX - 0.02, WIN_Y + dy, WIN_Z + dz), FRAME_M, 0.004))
KIT.append(box('shelf', (0.2, 1.3, 0.03), (WX - 0.1, 0.55, 1.5), noisy(mat('shelfwood', (0.35, 0.22, 0.12), 0.5), 20, 0.3), 0.004))
for i in range(6):
    KIT.append(lathe('jar%d' % i, [(0.0, 0.0), (0.04, 0.0), (0.042, 0.1), (0.03, 0.12), (0.03, 0.135), (0.0, 0.135)], 24,
                     mat('jar%d' % i, [(0.7, 0.5, 0.2), (0.3, 0.45, 0.3), (0.75, 0.72, 0.65), (0.5, 0.2, 0.15)][i % 4], 0.25, coat=0.5), loc=(WX - 0.1, 0.05 + i * 0.2, 1.515)))
KIT.append(prim('cylinder', 'clock', mat('clock', (0.9, 0.9, 0.86), 0.4), loc=(0.3, 1.69, 1.95), rot=(R(90), 0, 0), vertices=48, radius=0.16, depth=0.03))
KIT.append(box('clock_h', (0.012, 0.004, 0.08), (0.3 - 0.008, 1.672, 1.985), DARK_M, rot=(0, R(-96 + 90), 0)))
KIT.append(box('clock_m', (0.008, 0.004, 0.12), (0.3 + 0.045, 1.672, 1.975), DARK_M, rot=(0, R(72), 0)))
# pendant lamp over the counter
KIT.append(lathe('pendant', [(0.0, 0.16), (0.03, 0.16), (0.16, 0.0), (0.155, 0.0), (0.028, 0.15), (0.0, 0.15)], 40, mat('pendant', (0.1, 0.12, 0.13), 0.4, metal=0.6), loc=(0.72, -0.2, 2.0)))
KIT.append(prim('cylinder', 'pendant_cord', DARK_M, loc=(0.72, -0.2, 2.58), vertices=8, radius=0.004, depth=0.85))
KIT.append(prim('uv_sphere', 'bulb', emis('bulb', (1.0, 0.72, 0.42), 30.0), loc=(0.72, -0.2, 2.06), segments=16, ring_count=8, radius=0.03))
ROOM = [FLOOR] + WALLS + KIT
SOLIDS = [KIT[0], KIT[2]]                                              # what he must not sink into (cabinet, countertop)
