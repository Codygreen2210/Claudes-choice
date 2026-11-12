# ================================================================ camera + world
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1); WBG.inputs['Strength'].default_value = 1.0
SKYTEX = wnt.nodes.new('ShaderNodeTexSky'); SKYTEX.sun_elevation = R(5); SKYTEX.sun_rotation = R(245)
SKYBG = wnt.nodes.new('ShaderNodeBackground'); SKYBG.inputs['Strength'].default_value = 0.0; wnt.links.new(SKYTEX.outputs['Color'], SKYBG.inputs['Color'])
WADD = wnt.nodes.new('ShaderNodeAddShader'); wnt.links.new(WBG.outputs['Background'], WADD.inputs[0]); wnt.links.new(SKYBG.outputs['Background'], WADD.inputs[1])
wnt.links.new(WADD.outputs['Shader'], wnt.nodes['World Output'].inputs['Surface'])
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.03; CAM.data.clip_end = 3000

# ================================================================ THE STORE (z up, metres): a Brooklyn corner store, ground floor of the
# three-story building. Floor x -3..3, y -4..4, ceiling 3.1. He stands in the aisle at M0 facing the front (-y, the camera side).
SX, SY, SH = 3.0, 4.0, 3.1
M0 = V3(0.15, 0.4, 0.0)
def tile_mat(name, c0, c1, scale=2.5):
    m = mat(name, c0, 0.35); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    ck = nt.nodes.new('ShaderNodeTexChecker'); ck.inputs['Scale'].default_value = scale; ck.inputs['Color1'].default_value = (*c0, 1); ck.inputs['Color2'].default_value = (*c1, 1)
    nt.links.new(tc.outputs['Object'], ck.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14.0; nz.inputs['Detail'].default_value = 8; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.35
    nt.links.new(ck.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.25; mr.inputs['To Max'].default_value = 0.6; nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m
def brick_mat(name, base=(0.42, 0.16, 0.1), mortar=(0.55, 0.52, 0.46), scale=1.0, dirt=0.0):
    """running-bond brick from a brick texture in object space"""
    m = mat(name, base, 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    bk = nt.nodes.new('ShaderNodeTexBrick'); bk.inputs['Color1'].default_value = (*base, 1); bk.inputs['Color2'].default_value = tuple(c * 0.72 for c in base) + (1,)
    bk.inputs['Mortar'].default_value = (*mortar, 1); bk.inputs['Scale'].default_value = 1.0; bk.inputs['Mortar Size'].default_value = 0.012
    bk.inputs['Brick Width'].default_value = 0.2; bk.inputs['Row Height'].default_value = 0.068; bk.offset = 0.5
    nt.links.new(mp.outputs['Vector'], bk.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6; nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.4 + dirt
    nt.links.new(bk.outputs['Color'], mx.inputs['A']); nt.links.new(nz.outputs['Color'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.invert = True; nt.links.new(bk.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
FLOOR_M = tile_mat('floor_tile', (0.62, 0.6, 0.55), (0.2, 0.21, 0.22))
WALL_M = noisy(mat('wall', (0.72, 0.7, 0.62), 0.8), 6.0, 0.12)
CEIL_M = noisy(mat('ceiling_tile', (0.78, 0.77, 0.72), 0.9), 60.0, 0.15)
PLASTER_M = noisy(mat('plaster', (0.7, 0.68, 0.62), 0.95), 25.0, 0.25)
WOOD_M = noisy(mat('joist', (0.42, 0.3, 0.19), 0.75), 18.0, 0.35, 0.15)
OLDWOOD_M = noisy(mat('old_wood', (0.3, 0.22, 0.15), 0.85), 25.0, 0.4)
BRICK_M = brick_mat('brick', dirt=0.1)
LOOSE_BRICK_M = noisy(mat('loose_brick', (0.45, 0.17, 0.1), 0.9), 22.0, 0.35, 0.1)
STEEL_M = noisy(mat('steel', (0.25, 0.25, 0.26), 0.45, metal=0.8), 30.0, 0.3)
SHELF_M = noisy(mat('shelf', (0.85, 0.85, 0.83), 0.4, metal=0.3), 30.0, 0.08)
TUBE_GLOW = emis('fluor', (0.92, 0.97, 1.0), 4.5)
FRIDGE_GLOW = emis('fridge', (0.85, 0.93, 1.0), 4.0)
STORE = []
STORE.append(box('floor', (2 * SX, 2 * SY, 0.1), V3(0, 0, -0.05), FLOOR_M))
STORE.append(box('ceiling', (2 * SX, 2 * SY, 0.05), V3(0, 0, SH + 0.025), CEIL_M))
STORE.append(box('wall_back', (2 * SX, 0.2, SH), V3(0, SY + 0.1, SH / 2), WALL_M))
STORE.append(box('wall_L', (0.2, 2 * SY, SH), V3(-SX - 0.1, 0, SH / 2), BRICK_M))
STORE.append(box('wall_R', (0.2, 2 * SY, SH), V3(SX + 0.1, 0, SH / 2), WALL_M))
# the front: big window (night-blue street glow) and the door frame
STORE.append(box('front_low', (2 * SX, 0.2, 0.7), V3(0, -SY - 0.1, 0.35), WALL_M))
STORE.append(box('front_top', (2 * SX, 0.2, 0.5), V3(0, -SY - 0.1, SH - 0.25), WALL_M))
STORE.append(box('front_glass', (2 * SX, 0.02, SH - 1.2), V3(0, -SY - 0.15, 0.7 + (SH - 1.2) / 2), emis('street', (0.9, 0.75, 0.55), 1.4)))
# ceiling grid lights (fluorescent troffers)
TROFFERS = []
for i, y in enumerate((-2.6, -0.8, 1.0, 2.8)):
    for x in (-1.5, 1.5):
        TROFFERS.append(box('troffer%d%s' % (i, 'L' if x < 0 else 'R'), (0.6, 1.2, 0.03), V3(x, y, SH - 0.02), TUBE_GLOW))
STORE += TROFFERS
# shelves: two gondola runs along y (x = -1.6, +1.6) and a wall run; rows of colourful product boxes
_rs = random.Random(4); PRODUCT_M = [noisy(mat('prod%d' % i, c, 0.45), 40.0, 0.15) for i, c in enumerate(
    [(0.8, 0.12, 0.08), (0.95, 0.75, 0.1), (0.1, 0.35, 0.8), (0.15, 0.6, 0.25), (0.9, 0.45, 0.1), (0.85, 0.85, 0.82), (0.5, 0.15, 0.55)])]
def gondola(name, x0, y0, y1, face):
    out = [box(name + '_base', (0.5, y1 - y0, 0.12), V3(x0, (y0 + y1) / 2, 0.06), SHELF_M),
           box(name + '_back', (0.04, y1 - y0, 1.6), V3(x0 - 0.2 * face, (y0 + y1) / 2, 0.8), SHELF_M)]
    for k, z in enumerate((0.12, 0.55, 0.98, 1.4)):
        out.append(box(name + '_s%d' % k, (0.42, y1 - y0, 0.025), V3(x0, (y0 + y1) / 2, z), SHELF_M))
        y = y0 + 0.03
        while y < y1 - 0.12:
            w = _rs.uniform(0.08, 0.2); h = _rs.uniform(0.14, 0.32); d_ = _rs.uniform(0.12, 0.3)
            out.append(box(name + '_p%d_%.2f' % (k, y), (d_, w, h), V3(x0 + 0.04 * face, y + w / 2, z + 0.0125 + h / 2), _rs.choice(PRODUCT_M)))
            y += w + 0.012
    return out
STORE += gondola('gL', -1.55, -2.8, 2.6, 1) + gondola('gR', 1.75, -2.8, 2.6, -1)
# cold cases on the back wall (glowing glass doors) with bottles
for i in range(4):
    x = -2.2 + i * 1.3
    STORE.append(box('fridge%d' % i, (1.2, 0.05, 1.9), V3(x, SY - 0.6, 1.05), FRIDGE_GLOW))
    STORE.append(box('fridge_fr%d' % i, (1.25, 0.65, 0.12), V3(x, SY - 0.33, 2.05), STEEL_M))
    STORE.append(box('fridge_mull%d' % i, (0.05, 0.06, 1.95), V3(x + 0.6, SY - 0.64, 1.05), STEEL_M))
# counter by the front
STORE.append(box('counter', (1.8, 0.6, 1.0), V3(-1.8, -3.0, 0.5), noisy(mat('counter', (0.5, 0.42, 0.33), 0.5), 10.0, 0.2), 0.01))
STORE.append(box('register', (0.35, 0.3, 0.25), V3(-1.8, -3.0, 1.13), mat('reg', (0.08, 0.08, 0.09), 0.4)))
# interior light (sources are the troffers; a fill keeps faces readable)
STORE_L = [light_at('store_fill', 'AREA', V3(0.0, -2.6, 2.6), M0 + V3(0, 0, 1.2), 160, (1.0, 0.95, 0.88), 2.0),
           light_at('store_back', 'AREA', V3(0.0, SY - 0.8, 1.4), M0 + V3(0, 0, 1.2), 60, (0.85, 0.93, 1.0), 2.4)]
# after the collapse: the room is dark, one gap above lets a cold shaft of light in (rescue lights outside), a dust haze
GAP_L = light_at('gap_light', 'SPOT', V3(0.3, 0.6, 4.2), M0 + V3(0.0, -0.3, 0.0), 0.0, (0.82, 0.9, 1.0), 0.15)
GAP_L.data.spot_size = R(48); GAP_L.data.spot_blend = 0.6
TORCH_L = [light_at('torch%d' % i, 'SPOT', V3(0.0, 0.0, 4.0), M0, 0.0, (1.0, 0.93, 0.8), 0.04) for i in range(3)]
for o in TORCH_L: o.data.spot_size = R(16); o.data.spot_blend = 0.35
STORE += STORE_L + [GAP_L] + TORCH_L
