# ================================================================ timing + the set: open desert at midday, the Great Pyramid half built far down the
# road, a limestone wall along the left of the road that carries the tomb painting (the payoff)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_PYR = B[1] + 0.1                    # rise to the pyramid
T_PILE = B[2]                         # "dry sand piles up": the camera is down at the runner
T_STUCK = word_t(2, 15)               # "gets stuck": the sled stops dead
T_CLIMB = word_t(3, 3)                # "climbs onto the front of the sled"
T_UP = T_CLIMB + 0.9                  # standing on the sled
T_POUR = word_t(4, 1)                 # "pours": water starts
T_DIVE = B[5] + 0.15                  # into the wet sand
T_IN = T_DIVE + 0.9                   # among the grains
T_OUT = B[6] - 0.05                   # back up out of the sand
T_GO = T_POUR + 1.2                   # the sled breaks loose on the wet sand
T_HALF = word_t(7, 17)                # "cut the pull in half"
T_LETGO = word_t(8, 4)                # "half as many men": the back two rows let go
T_SOAK = B[9] + 0.1                   # too much water: he dumps it
T_RIGHT = word_t(9, 10)               # "just right": back to a steady pour
T_WALL = B[10] + 0.2                  # the camera turns to the wall
T_RESET = B[10] + 2.6                 # (camera on the wall) the road goes back to frame one
T_BACK = B[12] + 0.2                  # the camera comes back to the start
print('T', round(T_STUCK, 2), round(T_CLIMB, 2), round(T_POUR, 2), round(T_GO, 2), round(T_LETGO, 2), round(T_SOAK, 2), round(T_WALL, 2), round(END, 2))

# ---------------------------------------------------------------- materials from photo sets, mapped by object coordinates (the meshes here have no UVs)
def pbr(pid, scale=1.0, name=None, coord_='Object', tint=None, rough_add=0.0, bump=1.0, boxp=False):
    d = P._dir(pid); m = bpy.data.materials.new(name or pid.split(':', 1)[-1]); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale); nt.links.new(coord(nt, coord_), mp.inputs['Vector'])
    def tex(pats, nc):
        f = P._one(d, *pats)
        if not f: return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f, check_existing=True); n.image.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
        n.projection = 'BOX' if boxp else 'FLAT'; n.projection_blend = 0.25; nt.links.new(mp.outputs[0], n.inputs['Vector']); return n
    c = tex(['*_diff_*.*', '*_Color.*', '*_col_*.*', '*diffuse*.*'], False)
    col = c.outputs['Color'] if c else None
    if col is not None and tint is not None:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        nt.links.new(col, mx.inputs['A']); mx.inputs['B'].default_value = (*tint, 1); col = mx.outputs['Result']
    if col is not None: nt.links.new(col, b.inputs['Base Color'])
    r = tex(['*_rough_*.*', '*_Roughness.*'], True)
    if r:
        if rough_add: nt.links.new(math_(nt, 'ADD', r.outputs['Color'], rough_add), b.inputs['Roughness'])
        else: nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    nmi = tex(['*_nor_gl_*.*', '*_NormalGL.*'], True)
    if nmi:
        nn = nt.nodes.new('ShaderNodeNormalMap'); nn.inputs['Strength'].default_value = bump; nt.links.new(nmi.outputs['Color'], nn.inputs['Color']); nt.links.new(nn.outputs['Normal'], b.inputs['Normal'])
    return m
def haze(m, dist=900.0, col=(0.78, 0.74, 0.66)):
    """far things fade into the bright desert air"""
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); out = nt.nodes['Material Output']
    cd = nt.nodes.new('ShaderNodeCameraData'); f = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'EXPONENT', math_(nt, 'DIVIDE', cd.outputs['View Distance'], -dist)))
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = 1.0
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(f, mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface']); return m

# ---------------------------------------------------------------- sky + sun
ENV = P.hdri('ph:goegap', 0.65, 205)
# the camera sees a clean desert sky instead of the photo (its hills are not Egypt); the photo still lights everything
try:
    wnt = S.world.node_tree; bg_ = next(n for n in wnt.nodes if n.type == 'BACKGROUND'); lp_ = wnt.nodes.new('ShaderNodeLightPath')
    gv = wnt.nodes.new('ShaderNodeTexCoord'); sz = sepz(wnt, gv.outputs['Generated'])
    hor = math_(wnt, 'POWER', math_(wnt, 'MAXIMUM', sz.outputs['Z'], 0.0), 0.45)
    sky = ramp(wnt, hor, [(0.0, (0.92, 0.86, 0.74)), (0.12, (0.62, 0.74, 0.86)), (0.55, (0.24, 0.45, 0.78)), (1.0, (0.12, 0.30, 0.66))])
    skyb = wnt.nodes.new('ShaderNodeBackground'); wnt.links.new(sky, skyb.inputs['Color']); skyb.inputs['Strength'].default_value = 1.0
    mxs = wnt.nodes.new('ShaderNodeMixShader'); wnt.links.new(lp_.outputs['Is Camera Ray'], mxs.inputs['Fac'])
    wout = next(n for n in wnt.nodes if n.type == 'OUTPUT_WORLD'); wnt.links.new(bg_.outputs[0], mxs.inputs[1]); wnt.links.new(skyb.outputs[0], mxs.inputs[2])
    wnt.links.new(mxs.outputs[0], wout.inputs['Surface'])
except Exception as e_: print('sky swap skipped', e_)
SUN = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(SUN)
SUN.data.energy = 3.4; SUN.data.color = (1.0, 0.94, 0.84); SUN.data.angle = R(1.2); SUN.rotation_euler = (R(38), R(0), R(81))

# ---------------------------------------------------------------- ground: hard-packed desert sand, with low dunes far off
SAND = pbr('ph:dense_sand', 0.45, 'sand', tint=(1.05, 0.93, 0.78), bump=0.8); haze(SAND, 1100.0)
def ground_mesh(name, size, n, height_fn, m):
    vs = []; fs = []
    for j in range(n + 1):
        for i in range(n + 1):
            x_ = -size / 2 + size * i / n; y_ = -size / 2 + size * j / n; vs.append((x_, y_, height_fn(x_, y_)))
    for j in range(n):
        for i in range(n): a_ = j * (n + 1) + i; fs.append((a_, a_ + 1, a_ + n + 2, a_ + n + 1))
    return mesh(name, vs, fs, m)
def dunes(x_, y_):
    r_ = math.hypot(x_, y_ - 20); k = smooth(60, 220, r_)
    return k * (6.0 * mnoise.noise(Vector((x_ / 140, y_ / 140, 0.3))) + 2.0 * mnoise.noise(Vector((x_ / 45, y_ / 45, 1.7))) + 4.0)
GROUND = ground_mesh('ground', 1800, 160, dunes, SAND)
NEAR = ground_mesh('near', 40, 2, lambda x_, y_: 0.0, SAND); NEAR.location = (0, 8, 0.002)        # the road itself: dead flat

# ---------------------------------------------------------------- the Great Pyramid, half built, far down the road; a long ramp up its face
LIME = pbr('ph:large_sandstone_blocks', 0.06, 'pyr', tint=(1.3, 1.1, 0.82), boxp=True); haze(LIME, 1400.0)
PYC = Vector((70, 430, 0)); PB_ = 230.0; PH_FULL = 146.0; PH_NOW = 92.0
hb = PB_ / 2; ht = hb * (1 - PH_NOW / PH_FULL)
pv = [(-hb, -hb, 0), (hb, -hb, 0), (hb, hb, 0), (-hb, hb, 0), (-ht, -ht, PH_NOW), (ht, -ht, PH_NOW), (ht, ht, PH_NOW), (-ht, ht, PH_NOW)]
PYR = mesh('pyramid', pv, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], LIME, smooth_=False, loc=PYC)
# stepped courses on the faces (a few big ledges read as stone layers from this far)
for k in range(1, 9):
    z_ = PH_NOW * k / 9; hk = hb * (1 - z_ / PH_FULL) + 0.6
    box(f'course{k}', (hk * 2, hk * 2, 0.9), (PYC.x, PYC.y, z_), LIME)
RAMP = mesh('ramp', [(-14, -hb - 150, 0), (14, -hb - 150, 0), (14, -hb + 30, PH_NOW * 0.9), (-14, -hb + 30, PH_NOW * 0.9), (-14, -hb + 30, 0), (14, -hb + 30, 0)],
            [(0, 1, 2, 3), (1, 5, 2), (0, 3, 4), (3, 2, 5, 4)], LIME, smooth_=False, loc=PYC + Vector((-30, 0, 0)))
# a second, finished pyramid off to the side (scale and age)
pv2 = [(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0), (0, 0, 76)]
mesh('pyr2', pv2, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4), (3, 2, 1, 0)], LIME, smooth_=False, loc=(-260, 640, 0))

# ---------------------------------------------------------------- the wall on the left of the road, and the tomb painting on it
WALLX = -5.6; WALL_Y0, WALL_Y1 = -6.0, 22.0; WALL_H = 3.4
WALLM = pbr('ph:plaster_stone_wall_01', 0.4, 'wallm', 'Object', tint=(1.08, 0.98, 0.82), boxp=True)
WALL = box('wall', (1.2, WALL_Y1 - WALL_Y0, WALL_H), (WALLX - 0.6, (WALL_Y0 + WALL_Y1) / 2, WALL_H / 2), WALLM, bv=0.04)
box('wallcap', (1.4, WALL_Y1 - WALL_Y0 + 0.2, 0.18), (WALLX - 0.6, (WALL_Y0 + WALL_Y1) / 2, WALL_H + 0.09), WALLM, bv=0.03)
PAINT_W, PAINT_H = 6.6, 6.6 * 1600 / 4096; PAINT_C = Vector((WALLX + 0.004, 11.0, 0.35 + PAINT_H / 2))
pm = bpy.data.materials.new('painting'); pm.use_nodes = True; nt = pm.node_tree; b = nt.nodes['Principled BSDF']
it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(os.path.join(HERE, 'painting.png')); it.interpolation = 'Cubic'
nt.links.new(coord(nt, 'UV'), it.inputs['Vector']); nt.links.new(it.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.88
wn = tnoise(nt, coord(nt, 'Object'), 26.0, 8.0); bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.18; nt.links.new(wn, bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
_pv = [(0, -PAINT_W / 2, -PAINT_H / 2), (0, PAINT_W / 2, -PAINT_H / 2), (0, PAINT_W / 2, PAINT_H / 2), (0, -PAINT_W / 2, PAINT_H / 2)]
PAINT = mesh('paintplane', _pv, [(0, 1, 2, 3)], pm, smooth_=False, loc=PAINT_C)
_uv = PAINT.data.uv_layers.new(name='UV')
for li, (u_, v_) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): _uv.data[li].uv = (u_, v_)
def paint_pt(u_, v_):
    """a point on the painting from its picture coords (0..1 left to right, 0..1 top to bottom), 3 cm out from the wall"""
    return PAINT_C + Vector((0.03, (u_ - 0.5) * PAINT_W, (0.5 - v_) * PAINT_H))
# a few loose stones and a basket by the wall, scattered rubble on the road edge
ROCKM = pbr('ph:rock_surface', 1.2, 'rockm', tint=(1.1, 0.98, 0.8), boxp=True)
for k in range(26):
    x_ = -3.2 - 2.0 * h1(k) if k % 2 else 2.6 + 3.0 * h1(k + 9); y_ = -4 + 26 * h1(k + 3)
    s_ = 0.08 + 0.25 * h1(k + 7) ** 2
    o = prim('ico_sphere', f'rub{k}', ROCKM, loc=(x_, y_, s_ * 0.3), scale=(s_ * (1 + h1(k)), s_, s_ * 0.6), subdivisions=2); o.rotation_euler = (0, 0, h1(k + 1) * 6)
