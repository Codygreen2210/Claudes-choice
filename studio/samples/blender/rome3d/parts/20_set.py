# ================================================================ timing + the set: a paved square in Rome in the rain, the Pantheon (rotunda, stepped dome,
# portico), a mixing trough with quicklime, a test bench with two concrete blocks, town blocks and hills far off
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_CRACK = 0.05                        # the crack shoots across the wall (frame one)
T_DIVE1 = B[2] + 0.15                 # into the crack ("full of little white lumps")
T_IN1 = T_DIVE1 + 0.75                # inside: the cut face of the concrete
T_OUT1 = B[4] - 0.25                  # into a white lump ...
T_PIT = T_OUT1 + 0.35                 # ... and out of the quicklime heap in the trough
T_POUR = word_t(4, 4)                 # "quicklime": he tips the bucket
T_STEAM = T_POUR + 0.35
T_DIVE2 = B[5] + 0.05                 # "watch the crack": back to the wall, into the crack
T_IN2 = T_DIVE2 + 0.8
T_WATER = B[6] - 0.1                  # rainwater fills the crack
T_CRYS = B[7]                         # crystals grow across it
T_SEAL = B[8] - 0.35                  # sealed
T_OUT2 = B[8] + 0.05                  # out through the crack of the left test block
T_BENCH = T_OUT2 + 0.7
T_HEAL0 = B[8] + 1.6; T_HEAL1 = word_t(8, 18)   # left block's crack whitens; "the water stopped"
T_REV = B[10] + 0.1                   # rise to the Pantheon
T_RESET = B[11] + 1.0                 # (camera far up) the square goes back to frame one
T_BACK = B[12] + 0.2
print('T', round(T_POUR, 2), round(T_HEAL1, 2), round(T_REV, 2), round(END, 2))
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

def ground_mesh(name, size, n, height_fn, m):
    vs = []; fs = []
    for j in range(n + 1):
        for i in range(n + 1):
            x_ = -size / 2 + size * i / n; y_ = -size / 2 + size * j / n; vs.append((x_, y_, height_fn(x_, y_)))
    for j in range(n):
        for i in range(n): a_ = j * (n + 1) + i; fs.append((a_, a_ + 1, a_ + n + 2, a_ + n + 1))
    return mesh(name, vs, fs, m)

# ---------------------------------------------------------------- sky: soft grey rain light
P.hdri('ph:kloofendal_overcast', 1.0, 40)
try:   # the camera sees a plain grey rain sky (the photo's lake and hills are not Rome); the photo still lights everything
    wnt = S.world.node_tree; bg_ = next(n for n in wnt.nodes if n.type == 'BACKGROUND'); lp_ = wnt.nodes.new('ShaderNodeLightPath')
    gv = wnt.nodes.new('ShaderNodeTexCoord'); sz = sepz(wnt, gv.outputs['Generated'])
    hor = math_(wnt, 'POWER', math_(wnt, 'MAXIMUM', sz.outputs['Z'], 0.0), 0.5)
    sky = ramp(wnt, hor, [(0.0, (0.62, 0.64, 0.66)), (0.35, (0.50, 0.53, 0.57)), (1.0, (0.36, 0.39, 0.44))])
    skyb = wnt.nodes.new('ShaderNodeBackground'); wnt.links.new(sky, skyb.inputs['Color']); skyb.inputs['Strength'].default_value = 1.0
    mxs = wnt.nodes.new('ShaderNodeMixShader'); wnt.links.new(lp_.outputs['Is Camera Ray'], mxs.inputs['Fac'])
    wout = next(n for n in wnt.nodes if n.type == 'OUTPUT_WORLD'); wnt.links.new(bg_.outputs[0], mxs.inputs[1]); wnt.links.new(skyb.outputs[0], mxs.inputs[2])
    wnt.links.new(mxs.outputs[0], wout.inputs['Surface'])
except Exception as e_: print('sky swap skipped', e_)
SUNL = bpy.data.objects.new('sunl', bpy.data.lights.new('sunl', 'SUN')); S.collection.objects.link(SUNL)
SUNL.data.energy = 0.6; SUNL.data.color = (0.9, 0.93, 1.0); SUNL.data.angle = R(20); SUNL.rotation_euler = (R(50), 0, R(210))
try:
    S.world.mist_settings.start = 30; S.world.mist_settings.depth = 400
except Exception: pass

# ---------------------------------------------------------------- the square: wet stone paving, dark and shiny in the rain
PAVE = pbr('acg:PavingStones054', 0.32, 'pave', tint=(0.78, 0.74, 0.68), rough_add=-0.35, bump=0.8); haze(PAVE, 700.0, (0.62, 0.64, 0.66))
GROUND = ground_mesh('ground', 1400, 120, lambda x_, y_: smooth(160, 600, math.hypot(x_, y_ - 40)) * 22 * (0.5 + 0.5 * mnoise.noise(Vector((x_ / 300, y_ / 300, 0.4)))), PAVE)

# ---------------------------------------------------------------- the Pantheon: brick-faced concrete rotunda, stepped dome with the oculus, granite portico
PC = Vector((0, 40.0, 0)); RO = 28.0; DH = 22.0
BRICK = pbr('ph:brick_wall_005', 0.42, 'brick', 'Object', tint=(1.0, 0.86, 0.74), rough_add=-0.15, boxp=True); haze(BRICK, 900.0, (0.62, 0.64, 0.66))
CONC = pbr('acg:Concrete048', 0.25, 'dome', 'Object', tint=(0.92, 0.9, 0.86), boxp=True); haze(CONC, 900.0, (0.62, 0.64, 0.66))
TRAV = pbr('acg:Travertine009', 0.6, 'trav', 'Object', tint=(1.0, 0.97, 0.9), boxp=True); haze(TRAV, 900.0, (0.62, 0.64, 0.66))
def ring_wall(name, r_out, r_in, z0, z1, m, seg=180):
    vs = []; fs = []
    for k in range(seg):
        a_ = 2 * math.pi * k / seg
        for r_, z_ in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)): vs.append((PC.x + r_ * math.cos(a_), PC.y + r_ * math.sin(a_), z_))
    for k in range(seg):
        k2 = (k + 1) % seg
        for j in range(4): j2 = (j + 1) % 4; fs.append((k * 4 + j, k2 * 4 + j, k2 * 4 + j2, k * 4 + j2))
    return mesh(name, vs, fs, m, smooth_=True)
DRUM = ring_wall('drum', RO, RO - 6.0, 0.0, DH, BRICK)
for k, (z_, h_) in enumerate(((7.4, 0.5), (14.6, 0.6), (DH - 0.6, 0.8))):        # cornices
    ring_wall(f'cornice{k}', RO + 0.35, RO - 1.0, z_, z_ + h_, TRAV)
# dome: the outer shell steps up in rings, then a smooth cap round the open oculus
prof = []
for k in range(7): r_ = RO - 1.2 - 1.7 * k; prof += [(r_, DH + 1.15 * k), (r_, DH + 1.15 * (k + 1))]
for k in range(1, 13):
    u = k / 12; a_ = R(32 + 52 * u); prof.append((4.6 + (RO - 13.2 - 4.6) * (1 - u) ** 1.3, DH + 8.05 + 7.0 * math.sin(R(90 * u))))
prof.append((4.6, DH + 15.2)); prof.append((4.25, DH + 15.0)); prof.append((4.25, DH + 13.0))
DOME = lathe('dome', [(r_, z_) for r_, z_ in prof], 120, CONC, loc=PC)
CAP = lathe('domecap', [(RO - 0.1, DH), (RO - 1.2, DH), (RO - 1.2, DH + 0.1)], 120, TRAV, loc=PC)
DARK = mat('inside', (0.02, 0.02, 0.02), 0.9)
prim('cylinder', 'oculus_dark', DARK, loc=PC + Vector((0, 0, DH + 12.4)), radius=4.3, depth=0.2, vertices=48)
# portico on the west side (-x): a block, 8 columns across the front and 2 more rows, a gabled roof
PX0 = PC.x - RO + 1.0
box('porch_block', (10.0, 34.0, DH - 3.0), (PX0 - 3.0, PC.y, (DH - 3.0) / 2), BRICK, bv=0.05)
GRAN = mat('granite', (0.42, 0.38, 0.36), 0.45, coat=0.2); noisy(GRAN, 30.0, 0.25, 0.1)
for row, xx in enumerate((PX0 - 22.0, PX0 - 17.0, PX0 - 12.0)):
    for k in range(8):
        if row > 0 and k not in (0, 1, 2, 5, 6, 7): continue
        y_ = PC.y - 15.4 + 4.4 * k
        prim('cylinder', f'col{row}_{k}', GRAN, loc=(xx, y_, 0.6 + 5.9), radius=0.75, depth=11.8, vertices=32)
        box(f'cap{row}_{k}', (1.9, 1.9, 0.7), (xx, y_, 12.75), TRAV, bv=0.05); box(f'base{row}_{k}', (1.8, 1.8, 0.6), (xx, y_, 0.3), TRAV, bv=0.05)
box('entab', (17.0, 34.0, 2.4), (PX0 - 13.5, PC.y, 14.3), TRAV, bv=0.05)
mesh('pediment', [(PX0 - 22.6, PC.y - 17.2, 15.5), (PX0 - 22.6, PC.y + 17.2, 15.5), (PX0 - 22.6, PC.y, 21.3), (PX0 - 5.0, PC.y - 17.2, 15.5), (PX0 - 5.0, PC.y + 17.2, 15.5), (PX0 - 5.0, PC.y, 21.3)],
     [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (0, 2, 5, 3), (1, 4, 5, 2)], TRAV, smooth_=False)
mesh('roof', [(PX0 - 23.2, PC.y - 17.8, 15.4), (PX0 - 23.2, PC.y + 17.8, 15.4), (PX0 - 23.2, PC.y, 21.7), (PX0 - 4.0, PC.y - 17.8, 15.4), (PX0 - 4.0, PC.y + 17.8, 15.4), (PX0 - 4.0, PC.y, 21.7)],
     [(0, 2, 5, 3), (1, 4, 5, 2)], mat('rooflead', (0.34, 0.33, 0.32), 0.55, metal=0.4), smooth_=False)
box('steps', (6.0, 36.0, 0.6), (PX0 - 25.0, PC.y, 0.3), TRAV, bv=0.04)
# the town round the square: plain blocks with tiled roofs, and hills
STUC = mat('stucco', (0.68, 0.55, 0.42), 0.85); noisy(STUC, 3.0, 0.2, 0.1); haze(STUC, 600.0, (0.62, 0.64, 0.66))
TILE = mat('tiles', (0.52, 0.24, 0.14), 0.7); noisy(TILE, 6.0, 0.2, 0.1); haze(TILE, 600.0, (0.62, 0.64, 0.66))
rng_ = random.Random(3)
for k in range(46):
    a_ = rng_.uniform(0, 2 * math.pi); r_ = rng_.uniform(62, 200); cx, cy = PC.x + r_ * math.cos(a_), PC.y + r_ * math.sin(a_)
    if cx < PC.x - 40 and abs(cy - PC.y) < 40: continue                     # keep the front of the portico open
    w_, d_, h_ = rng_.uniform(10, 26), rng_.uniform(10, 26), rng_.uniform(8, 18)
    b_ = box(f'house{k}', (w_, d_, h_), (cx, cy, h_ / 2), STUC); b_.rotation_euler.z = a_
    r2 = mesh(f'hroof{k}', [(-w_ / 2 - 0.5, -d_ / 2 - 0.5, h_), (w_ / 2 + 0.5, -d_ / 2 - 0.5, h_), (w_ / 2 + 0.5, d_ / 2 + 0.5, h_), (-w_ / 2 - 0.5, d_ / 2 + 0.5, h_), (0, -d_ / 2 - 0.5, h_ + 3), (0, d_ / 2 + 0.5, h_ + 3)],
              [(0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4)], TILE, smooth_=False, loc=(cx, cy, 0)); r2.rotation_euler.z = a_

# ---------------------------------------------------------------- the crack spot: on the drum facing the camera's start, 1 to 1.7 m up
CRACK_A = -math.pi / 2                                       # the point of the drum nearest the square (y = PC.y - RO)
def wall_pt(u_, v_, out=0.0):
    """u along the wall (m, +x), v height (m); on the curved drum face"""
    a_ = CRACK_A + u_ / RO; r_ = RO + out; return Vector((PC.x + r_ * math.cos(a_), PC.y + r_ * math.sin(a_), v_))
WALL_N = Vector((0, -1, 0))

# ---------------------------------------------------------------- the mixing trough (right of the crack, out from the wall) and the test bench (left)
WOOD = pbr('ph:wood_planks', 1.2, 'wood', 'Object', tint=(0.85, 0.72, 0.58), boxp=True)
TR_C = Vector((2.3, PC.y - RO - 1.9, 0.0))
TROUGH = empty('trough', loc=TR_C)
for nm_, sz, lc in (('tb', (1.6, 0.9, 0.06), (0, 0, 0.12)), ('tf', (1.6, 0.06, 0.38), (0, -0.45, 0.3)), ('tk', (1.6, 0.06, 0.38), (0, 0.45, 0.3)),
                    ('tl', (0.06, 0.9, 0.38), (-0.8, 0, 0.3)), ('tr', (0.06, 0.9, 0.38), (0.8, 0, 0.3))):
    box(nm_, sz, lc, WOOD, bv=0.01, parent=TROUGH)
for sx in (-0.7, 0.7):
    for sy in (-0.38, 0.38): box(f'tleg{sx}{sy}', (0.08, 0.08, 0.12), (sx, sy, 0.06), WOOD, parent=TROUGH)
LIMEW = mat('quicklime', (0.86, 0.85, 0.80), 0.92); noisy(LIMEW, 14.0, 0.25, 0.05)
HEAP = prim('ico_sphere', 'heap', LIMEW, parent=TROUGH, loc=(0.1, 0.0, 0.16), scale=(0.62, 0.36, 0.2), subdivisions=4)
for v in HEAP.data.vertices: v.co *= 1.0 + 0.18 * mnoise.noise(v.co * 4.0) + 0.06 * mnoise.noise(v.co * 15.0)
for k in range(30):
    prim('ico_sphere', f'limelump{k}', LIMEW, parent=TROUGH, loc=(-0.6 + 1.25 * h1(k), -0.32 + 0.64 * h1(k + 5), 0.17 + 0.05 * h1(k + 9)), scale=(1, 0.9, 0.7), radius=0.025 + 0.03 * h1(k + 2), subdivisions=1)
LIMEWATER = mat('limewater', (0.72, 0.74, 0.70), 0.08, trans=0.3, ior=1.33)
POOLT = box('tpool', (1.48, 0.82, 0.02), (0, 0, 0.15), LIMEWATER, parent=TROUGH)
HOE = tube('hoe', [(0.0, 0.0, 0.0), (0.0, 0.0, 1.5)], 0.018, WOOD); box('hoeblade', (0.24, 0.02, 0.16), (0, 0, 0), mat('iron', (0.2, 0.19, 0.18), 0.5, metal=0.8), parent=HOE)
HOE.location = TR_C + Vector((-1.05, 0.3, 0.0)); HOE.rotation_euler = (R(-12), R(14), 0)
# test bench
BENCH_C = Vector((-2.5, PC.y - RO - 1.6, 0.0))
BENCH = empty('bench', loc=BENCH_C)
box('btop', (1.5, 0.7, 0.07), (0, 0, 0.82), WOOD, bv=0.01, parent=BENCH)
for sx in (-0.65, 0.65):
    for sy in (-0.28, 0.28): box(f'bleg{sx}{sy}', (0.07, 0.07, 0.8), (sx, sy, 0.4), WOOD, parent=BENCH)
