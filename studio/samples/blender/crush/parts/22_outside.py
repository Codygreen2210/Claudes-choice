# ================================================================ OUTSIDE (a block of Flatbush, built far from the store: origin at X0).
# The building line is y = 0, the street in front (-y). N = the next building (x -8..0, stands), C = the three-story building that
# falls (x 0..7), LOT = the dug-out lot next to it (x 7..19, a 4 m pit). C falls sideways into the pit; its side wall goes with it and
# leaves N's rooms open. No signs, no logos.
X0 = V3(200, 0, 0)
OUT = []
ASPHALT_M = noisy(mat('asphalt', (0.07, 0.07, 0.075), 0.75), 8.0, 0.35, 0.1)
WALK_M = noisy(mat('sidewalk', (0.45, 0.44, 0.42), 0.8), 4.0, 0.2)
DIRT_M = noisy(mat('dirt', (0.3, 0.22, 0.15), 0.95), 3.0, 0.35, 0.05)
TAN_BRICK_M = brick_mat('tan_brick', (0.55, 0.42, 0.3), (0.62, 0.6, 0.55))
RED_BRICK_M = brick_mat('red_brick', (0.36, 0.1, 0.06), (0.42, 0.4, 0.36), dirt=0.25)
FAR_BRICK_M = brick_mat('far_brick', (0.38, 0.26, 0.2), (0.5, 0.48, 0.45))
GLASS_M = mat('glass', (0.05, 0.06, 0.07), 0.05, metal=0.0, coat=1.0)
WINDOW_LIT = emis('window_lit', (1.0, 0.72, 0.4), 3.0)
TRIM_M = mat('trim_out', (0.15, 0.14, 0.13), 0.5)
OUT.append(box('street', (220, 30, 0.1), X0 + V3(0, -15, -0.05), ASPHALT_M))
OUT.append(box('sidewalk', (220, 3.0, 0.15), X0 + V3(0, -1.5, 0.075), WALK_M))
OUT.append(box('far_walk', (220, 3.0, 0.15), X0 + V3(0, -15.5, 0.075), WALK_M))
LINE_M = emis('lane_line', (0.75, 0.6, 0.2), 0.25)
for k in range(-12, 13): OUT.append(box('dash%d' % k, (2.4, 0.12, 0.01), X0 + V3(k * 5.0, -9.0, 0.005), LINE_M))
def windows(name, x0, x1, y_face, z0, floors, fh, face_dir, m_wall_frame=TRIM_M, lit_p=0.35, seed=0):
    rr = random.Random(seed); out = []; n = max(1, int((x1 - x0) / 1.8))
    for f in range(floors):
        for i in range(n):
            x = x0 + (i + 0.5) * (x1 - x0) / n; z = z0 + f * fh + fh * 0.55
            out.append(box(f'{name}_w{f}_{i}', (0.95, 0.06, 1.5), V3(x, y_face + 0.03 * face_dir, z), WINDOW_LIT if rr.random() < lit_p else GLASS_M))
            out.append(box(f'{name}_s{f}_{i}', (1.1, 0.16, 0.08), V3(x, y_face + 0.06 * face_dir, z - 0.78), m_wall_frame))
    return out
# across the street: a row of buildings to look past
for i in range(10):
    x = -40 + i * 9.5; h = random.Random(i).choice((10, 13, 16))
    OUT.append(box('far%d' % i, (9.3, 12, h), X0 + V3(x, -23, h / 2), FAR_BRICK_M))
    OUT += windows('far%d' % i, X0.x + x - 4.4, X0.x + x + 4.4, -17.0, 3.5, int((h - 3.5) / 3.2), 3.2, -1, lit_p=0.45, seed=i)
# up and down the block (beyond N and the lot)
for i, (x0, x1, h) in enumerate(((-30, -17, 12), (-17, -8, 10), (19, 28, 13), (28, 40, 10))):
    OUT.append(box('row%d' % i, (x1 - x0, 15, h), X0 + V3((x0 + x1) / 2, 7.5, h / 2), TAN_BRICK_M if i % 2 else FAR_BRICK_M))
    OUT += windows('row%d' % i, X0.x + x0 + 0.5, X0.x + x1 - 0.5, -0.0, 3.4, int((h - 3.4) / 3.2), 3.2, -1, lit_p=0.4, seed=10 + i)
# N: four floors; front, back and far side are walls; the side toward C (x = 0) is open inside behind C's wall
NH, NF = 13.0, 3.2
OUT.append(box('N_front', (8.0, 0.3, NH), X0 + V3(-4.0, 0.15, NH / 2), TAN_BRICK_M))
OUT.append(box('N_back', (8.0, 0.3, NH), X0 + V3(-4.0, 14.85, NH / 2), TAN_BRICK_M))
OUT.append(box('N_far', (0.3, 15, NH), X0 + V3(-7.85, 7.5, NH / 2), TAN_BRICK_M))
OUT.append(box('N_roof', (8.2, 15.2, 0.3), X0 + V3(-4.0, 7.5, NH), mat('roof_tar', (0.08, 0.08, 0.08), 0.8)))
OUT += windows('N', X0.x - 7.5, X0.x - 0.5, -0.0, 3.4, 3, NF, -1, lit_p=0.5, seed=3)
OUT.append(box('N_shop', (7.0, 0.05, 2.4), X0 + V3(-4.0, -0.03, 1.3), WINDOW_LIT))
ROOM = []                                                              # what shows when the wall is gone
PAINT = [noisy(mat('paint%d' % i, c, 0.85), 5.0, 0.08) for i, c in enumerate(((0.75, 0.68, 0.55), (0.55, 0.65, 0.72), (0.78, 0.6, 0.6), (0.6, 0.7, 0.55)))]
for f in range(4):
    z = f * NF
    ROOM.append(box('N_floor%d' % f, (8.0, 15, 0.25), X0 + V3(-4.0, 7.5, z + 0.125), noisy(mat('slab%d' % f, (0.5, 0.48, 0.45), 0.9), 6.0, 0.2)))
    for r, (y0, y1) in enumerate(((0.3, 5.5), (5.5, 10.0), (10.0, 14.7))):
        ROOM.append(box(f'N_rw{f}_{r}', (0.12, y1 - y0, NF - 0.25), X0 + V3(-3.2, (y0 + y1) / 2, z + 0.25 + (NF - 0.25) / 2), PAINT[(f + r) % 4]))
        ROOM.append(box(f'N_div{f}_{r}', (3.2, 0.12, NF - 0.25), X0 + V3(-1.6, y1, z + 0.25 + (NF - 0.25) / 2), PAINT[(f + r + 1) % 4]))
# the bedroom on the second floor (a bed, a lamp), a closet full of clothes next to it, like the photos described
BZ = NF + 0.25
ROOM.append(box('bed', (1.9, 1.5, 0.45), X0 + V3(-2.1, 3.0, BZ + 0.225), noisy(mat('bedding', (0.85, 0.85, 0.9), 0.9), 8.0, 0.15), 0.06, ss=1))
ROOM.append(box('headboard', (0.1, 1.6, 0.9), X0 + V3(-3.1, 3.0, BZ + 0.45), noisy(mat('headb', (0.35, 0.22, 0.15), 0.6), 10.0, 0.2)))
ROOM.append(box('pillow', (0.45, 0.6, 0.15), X0 + V3(-2.8, 3.0, BZ + 0.52), mat('pillow', (0.95, 0.95, 0.95), 0.9), 0.05, ss=1))
ROOM.append(box('lamp', (0.25, 0.25, 0.3), X0 + V3(-2.9, 4.2, BZ + 0.75), emis('lamp', (1.0, 0.8, 0.5), 5.0)))
CL_Y = 6.2
ROOM.append(box('closet_rod', (0.03, 2.4, 0.03), X0 + V3(-1.5, CL_Y + 1.2, BZ + 1.85), STEEL_M))
_cr = random.Random(7); CLOTH_C = [(0.15, 0.2, 0.45), (0.7, 0.1, 0.1), (0.1, 0.1, 0.1), (0.85, 0.85, 0.8), (0.3, 0.5, 0.3), (0.55, 0.45, 0.35), (0.9, 0.6, 0.2)]
CLOTH_M = [noisy(mat('cloth%d' % i, c, 0.95, sheen=0.5), 30.0, 0.2) for i, c in enumerate(CLOTH_C)]
y = CL_Y + 0.1
while y < CL_Y + 2.3:
    w = _cr.uniform(0.05, 0.11); h = _cr.uniform(0.7, 1.15)
    ROOM.append(box('cloth%.2f' % y, (0.5, w, h), X0 + V3(-1.5, y, BZ + 1.85 - h / 2), _cr.choice(CLOTH_M), 0.015)); y += w + 0.01
ROOM.append(box('dresser', (0.5, 1.0, 0.9), X0 + V3(-2.9, 8.4, BZ + 0.45), noisy(mat('dresser', (0.45, 0.32, 0.2), 0.5), 10.0, 0.2), 0.02))
OUT += ROOM
# C: three floors, red brick, the store at street level. Built as loose chunks that fall; each chunk keeps its own start and end place.
SLAB_M = noisy(mat('slab_c', (0.24, 0.2, 0.17), 0.9), 7.0, 0.35, 0.05)
CW, CD, CF, CH = 7.0, 14.0, 3.3, 9.9
CHUNKS = []
def chunk(name, size, loc, m):
    o = box(name, size, X0 + loc, m, 0.03); o.rotation_mode = 'QUATERNION'; CHUNKS.append(o); bpy.context.view_layer.update(); return o
for f in range(3):
    z = f * CF + CF / 2
    for i in range(4):                                                 # front wall panels (store glass on the ground floor)
        x = (i + 0.5) * CW / 4
        if f == 0:
            o = chunk(f'C_front0_{i}', (CW / 4, 0.3, CF), V3(x, 0.15, z), RED_BRICK_M)
            g_ = box(f'C_glass{i}', (CW / 4 - 0.2, 0.04, 2.2), X0 + V3(x, -0.02, 1.3), WINDOW_LIT); g_.parent = o; g_.matrix_parent_inverse = o.matrix_world.inverted()
        else:
            o = chunk(f'C_front{f}_{i}', (CW / 4, 0.3, CF), V3(x, 0.15, z), RED_BRICK_M)
            w_ = box(f'C_win{f}_{i}', (0.95, 0.06, 1.5), X0 + V3(x, -0.03, z + 0.15), WINDOW_LIT if (f + i) % 3 == 0 else GLASS_M); w_.parent = o; w_.matrix_parent_inverse = o.matrix_world.inverted()
            s_ = box(f'C_sill{f}_{i}', (1.1, 0.14, 0.08), X0 + V3(x, -0.06, z - 0.62), TRIM_M); s_.parent = o; s_.matrix_parent_inverse = o.matrix_world.inverted()
    for j in range(8):                                                 # the side over the pit, and the shared wall with N
        y_ = (j + 0.5) * CD / 8
        chunk(f'C_side{f}_{j}', (0.3, CD / 8, CF), V3(CW - 0.15, y_, z), RED_BRICK_M)
        chunk(f'C_party{f}_{j}', (0.3, CD / 8, CF), V3(0.15, y_, z), RED_BRICK_M)
    for i in range(4): chunk(f'C_back{f}_{i}', (CW / 4, 0.3, CF), V3((i + 0.5) * CW / 4, CD - 0.15, z), RED_BRICK_M)
    for i in range(2):
        for j in range(3): chunk(f'C_slab{f}_{i}{j}', (CW / 2 - 0.4, CD / 3 - 0.3, 0.3), V3((i + 0.5) * CW / 2, (j + 0.5) * CD / 3, (f + 1) * CF - 0.15), SLAB_M)
OUT.append(box('C_cornice', (CW + 0.2, 0.5, 0.4), X0 + V3(CW / 2, 0.0, CH + 0.2), TRIM_M)); C_CORNICE = OUT[-1]; C_CORNICE.rotation_mode = 'QUATERNION'; CHUNKS.append(C_CORNICE)
OUT.append(box('awning', (CW - 0.4, 1.1, 0.12), X0 + V3(CW / 2, -0.55, 2.75), noisy(mat('awning', (0.12, 0.3, 0.18), 0.8), 6.0, 0.15)))
AWNING = OUT[-1]; AWNING.rotation_mode = 'QUATERNION'; CHUNKS.append(AWNING)
# the lot: a pit with dirt walls, a plywood fence on the street, a ramp
LX0, LX1, LY0, LY1, PD = 7.3, 18.6, 0.5, 14.3, 3.0
OUT.append(box('pit_floor', (LX1 - LX0, LY1 - LY0, 0.2), X0 + V3((LX0 + LX1) / 2, (LY0 + LY1) / 2, -PD - 0.1), DIRT_M))
OUT.append(box('pit_wN', (LX1 - LX0, 0.4, PD), X0 + V3((LX0 + LX1) / 2, LY1 + 0.2, -PD / 2), DIRT_M))
OUT.append(box('pit_wS', (LX1 - LX0, 0.4, PD), X0 + V3((LX0 + LX1) / 2, LY0 - 0.2, -PD / 2), DIRT_M))
OUT.append(box('pit_wE', (0.4, LY1 - LY0, PD), X0 + V3(LX1 + 0.2, (LY0 + LY1) / 2, -PD / 2), DIRT_M))
OUT.append(box('pit_wW', (0.4, LY1 - LY0, PD), X0 + V3(LX0 - 0.2, (LY0 + LY1) / 2, -PD / 2), DIRT_M))
OUT.append(box('lot_rim', (12, 15, 0.1), X0 + V3(13.0, 7.5, -0.05), DIRT_M)); OUT[-1].hide_render = True    # (the pit cuts the ground; only its rim shows)
for i, (x0, x1, y0, y1) in enumerate(((7.0, 19.0, 0.0, 0.5), (7.0, 19.0, 14.3, 15.0), (18.6, 19.0, 0.5, 14.3), (7.0, 7.3, 0.5, 14.3))):
    OUT.append(box('rim%d' % i, (x1 - x0, y1 - y0, 0.1), X0 + V3((x0 + x1) / 2, (y0 + y1) / 2, -0.05), DIRT_M))
PLY_M = noisy(mat('plywood', (0.6, 0.48, 0.3), 0.8), 4.0, 0.3)
for i in range(5): OUT.append(box('ply%d' % i, (2.4, 0.04, 2.4), X0 + V3(7.4 + 1.2 + i * 2.42, -0.15, 1.2), PLY_M))
for k in range(9):                                                     # shoring piles along the pit wall
    OUT.append(box('pile%d' % k, (0.25, 0.25, PD + 0.4), X0 + V3(LX0 + 0.1, LY0 + 0.6 + k * 1.6, -PD / 2 + 0.2), STEEL_M))
# where every chunk ends up: dropped one by one into a height map of the pit and the lot (so they stack, not overlap much)
_hm_res = 0.25; _hx0, _hy0 = -0.5, -0.5; _hnx, _hny = int(21 / _hm_res), int(16 / _hm_res)
HM = np.zeros((_hnx, _hny))
for i in range(_hnx):
    for j in range(_hny):
        x, y = _hx0 + i * _hm_res, _hy0 + j * _hm_res
        if LX0 < x < LX1 and LY0 < y < LY1: HM[i, j] = -PD
_er = random.Random(17)
C_T0, C_T1, C_REL = {}, {}, {}
for o in sorted(CHUNKS, key=lambda o_: (o_.location.z, -o_.location.x)):
    C_T0[o.name] = (o.location.copy(), o.rotation_quaternion.copy())
    lx = o.location.x - X0.x; ly = o.location.y - X0.y; lz = o.location.z
    tx = _er.uniform(LX0 + 1.2, LX1 - 1.2) if _er.random() < 0.8 else _er.uniform(LX0 + 0.8, LX0 + 4.0); ty = clamp(ly + _er.uniform(-2.5, 2.5), LY0 + 1.0, LY1 - 1.0)
    if lz < 2.0 and lx < 3.0: tx = clamp(lx + _er.uniform(0.5, 3.5), 0.6, 9.0)          # the bottom of the street-side ends up in a heap on its own lot
    dims = o.dimensions; flat = sorted(dims)[::-1]
    i0 = int((tx - flat[0] / 2 - _hx0) / _hm_res); i1 = int((tx + flat[0] / 2 - _hx0) / _hm_res) + 1
    j0 = int((ty - flat[1] / 2 - _hy0) / _hm_res); j1 = int((ty + flat[1] / 2 - _hy0) / _hm_res) + 1
    i0, j0 = max(i0, 0), max(j0, 0); i1, j1 = min(i1, _hnx), min(j1, _hny)
    base = float(HM[i0:i1, j0:j1].mean()) if i1 > i0 and j1 > j0 else 0.0
    zt = base + flat[2] / 2
    if i1 > i0 and j1 > j0: HM[i0:i1, j0:j1] = np.maximum(HM[i0:i1, j0:j1] + flat[2] * 0.9, base + flat[2] * 0.6)
    # lay it down flat (its thinnest side up), with a tilt and a random turn
    d_ = o.dimensions; thin = int(np.argmin([d_.x, d_.y, d_.z]))
    q_flat = {0: Euler((0, R(90), 0)), 1: Euler((R(90), 0, 0)), 2: Euler((0, 0, 0))}[thin].to_quaternion()
    q = Euler((R(_er.uniform(-18, 18)), R(_er.uniform(-18, 18)), R(_er.uniform(0, 360)))).to_quaternion() @ q_flat
    C_T1[o.name] = (X0 + V3(tx, ty, zt), q); C_REL[o.name] = _er.uniform(0.0, 0.35) + 0.25 * clamp(1 - lz / CH, 0, 1) * 0 + 0.3 * clamp((7 - lx) / 7, 0, 1)
PIVOT = X0 + V3(CW, 0, 0)
def c_collapse(k):
    """k 0..1 over the collapse beat: lean toward the pit, then the chunks break off and fall in"""
    lean = R(14) * smooth(0.0, 0.4, k)
    Rl = Matrix.Rotation(-lean, 4, 'Y')
    for o in CHUNKS:
        p0, q0 = C_T0[o.name]; p1, q1 = C_T1[o.name]
        pl = PIVOT + (Rl @ (p0 - PIVOT).to_4d()).to_3d() if True else p0; ql = Rl.to_quaternion() @ q0
        s_ = 0.22 + 0.45 * C_REL[o.name]; f = clamp((k - s_) / 0.42, 0, 1); f2 = f * f
        p = pl.lerp(p1, f2); p.z += 1.2 * math.sin(math.pi * f) * (1 - f)
        o.location = p; o.rotation_quaternion = ql.slerp(q1, sm(f))
def c_rest():
    for o in CHUNKS: o.location, o.rotation_quaternion = C_T1[o.name]
def c_intact():
    for o in CHUNKS: o.location, o.rotation_quaternion = C_T0[o.name]
# rescue gear for the night: light towers, a fire truck with flashing lights, a drone, flashlight beams
RED_PAINT = noisy(mat('truck_red', (0.6, 0.03, 0.03), 0.35, coat=0.8), 10.0, 0.08)
TRUCK = [box('truck_body', (9.0, 2.5, 2.6), X0 + V3(26.0, -6.0, 1.7), RED_PAINT, 0.1),
         box('truck_cab', (2.4, 2.5, 2.9), X0 + V3(32.0, -6.0, 1.85), RED_PAINT, 0.15),
         box('truck_wind', (0.05, 2.2, 1.0), X0 + V3(33.2, -6.0, 2.5), GLASS_M),
         box('truck_ladder', (8.5, 1.0, 0.25), X0 + V3(25.5, -6.0, 3.15), mat('ladder', (0.75, 0.75, 0.78), 0.3, metal=0.8)),
         box('truck_stripe', (11.5, 2.52, 0.18), X0 + V3(27.0, -6.0, 1.2), mat('stripe', (0.9, 0.9, 0.85), 0.4))]
for i, x in enumerate((23.0, 25.0, 31.5)):
    for sy in (-1, 1): TRUCK.append(prim('cylinder', f'wheel{i}{sy}', mat('tire', (0.03, 0.03, 0.03), 0.8), loc=X0 + V3(x, -6.0 + 1.25 * sy, 0.5), rot=(R(90), 0, 0), radius=0.5, depth=0.35))
BAR_R = emis('bar_red', (1.0, 0.05, 0.03), 0.0); BAR_W = emis('bar_white', (1.0, 0.95, 0.9), 0.0)
TRUCK += [box('lightbar_r', (0.3, 1.0, 0.15), X0 + V3(32.6, -6.45, 3.4), BAR_R), box('lightbar_w', (0.3, 1.0, 0.15), X0 + V3(32.6, -5.55, 3.4), BAR_W)]
TRUCK_L = [light_at('truck_red_l', 'POINT', X0 + V3(32.6, -6.6, 3.8), X0, 0.0, (1.0, 0.08, 0.04), 0.3), light_at('truck_wht_l', 'POINT', X0 + V3(32.6, -5.4, 3.8), X0, 0.0, (1.0, 0.9, 0.8), 0.3)]
TOWER_M = mat('tower', (0.85, 0.75, 0.1), 0.5)
TOWERS, TOWER_L = [], []
for i, (x, y) in enumerate(((5.5, -2.5), (19.5, -2.0))):
    TOWERS.append(box('mast%d' % i, (0.15, 0.15, 7.5), X0 + V3(x, y, 3.75), STEEL_M))
    TOWERS.append(box('lamps%d' % i, (1.4, 0.3, 0.6), X0 + V3(x, y, 7.6), emis('lamps%d' % i, (1.0, 0.95, 0.85), 30.0), rot=(R(-35), 0, 0)))
    TOWER_L.append(light_at('tower_l%d' % i, 'SPOT', X0 + V3(x, y + 0.3, 7.4), X0 + V3(11.5 - 2 * i, 7.0, -2.5), 0.0, (1.0, 0.94, 0.85), 0.6))
    TOWER_L[-1].data.spot_size = R(70); TOWER_L[-1].data.spot_blend = 0.4
DRONE = [box('drone_body', (0.35, 0.35, 0.12), V3(0, 0, 0), mat('drone', (0.1, 0.1, 0.11), 0.4), 0.03)]
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        a_ = box(f'drone_arm{sx_}{sy_}', (0.36, 0.04, 0.03), V3(sx_ * 0.16, sy_ * 0.16, 0), DRONE[0].data.materials[0], rot=(0, 0, R(45 * sx_ * sy_))); a_.parent = DRONE[0]; DRONE.append(a_)
        r_ = prim('cylinder', f'drone_rot{sx_}{sy_}', mat('rotor', (0.2, 0.2, 0.22), 0.5, alpha=0.5), loc=V3(sx_ * 0.3, sy_ * 0.3, 0.05), radius=0.13, depth=0.005); r_.parent = DRONE[0]; DRONE.append(r_)
DRONE_RED = emis('drone_red', (1.0, 0.1, 0.05), 0.0); DRONE_GRN = emis('drone_grn', (0.1, 1.0, 0.2), 0.0)
for i, (mx_, px_) in enumerate(((DRONE_RED, -0.3), (DRONE_GRN, 0.3))):
    b_ = prim('uv_sphere', 'drone_led%d' % i, mx_, loc=V3(px_, 0.3, -0.03), radius=0.03); b_.parent = DRONE[0]; DRONE.append(b_)
DRONE_SPOT = light_at('drone_spot', 'SPOT', V3(0, 0, -0.1), V3(0, 0, -5), 0.0, (0.9, 0.95, 1.0), 0.05); DRONE_SPOT.parent = DRONE[0]
DRONE_SPOT.location = V3(0, 0, -0.1); DRONE_SPOT.rotation_quaternion = Quaternion((1, 0, 0, 0)); DRONE_SPOT.data.spot_size = R(30); DRONE_SPOT.data.spot_blend = 0.5
def beam_mat(name):
    """a flashlight beam through dusty night air: a cone that fades along its length and at its edges"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sx.inputs['Vector'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    a_ = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', math_(nt, 'POWER', sx.outputs['Z'], 1.6), math_(nt, 'POWER', lw.outputs['Facing'], 3.0)), 0.7)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.95, 0.8, 1); nt.links.new(math_(nt, 'MULTIPLY', objattr(nt, 'on'), 3.0), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY', a_, objattr(nt, 'on')), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
BEAMS_M = beam_mat('torch_beam')
TBEAMS = []
for i in range(5):
    o = prim('cone', 'tbeam%d' % i, BEAMS_M, radius1=0.9, radius2=0.03, depth=7.0, vertices=24); o.visible_shadow = False; o['on'] = 0.0; o.rotation_mode = 'QUATERNION'
    TBEAMS.append(o)
def torch(o, src, dst, on):
    """cone apex at src pointing at dst (length = distance)"""
    d_ = Vector(dst) - Vector(src); L_ = d_.length; o.scale = (L_ / 7.0 * 0.6 + 0.4, L_ / 7.0 * 0.6 + 0.4, L_ / 7.0)
    o.rotation_quaternion = (-d_).to_track_quat('Z', 'Y'); o.location = Vector(src) + d_ * 0.5; o['on'] = on
STREETL = [light_at('streetlamp%d' % i, 'POINT', X0 + V3(x, -3.0, 7.5), X0, 0.0, (1.0, 0.6, 0.25), 0.3) for i, x in enumerate((-14, 3, 22))]
for i, x in enumerate((-14, 3, 22)):
    OUT.append(box('lpole%d' % i, (0.15, 0.15, 7.5), X0 + V3(x, -2.7, 3.75), STEEL_M)); OUT.append(box('lhead%d' % i, (0.6, 0.3, 0.18), X0 + V3(x, -3.0, 7.55), emis('lhead%d' % i, (1.0, 0.65, 0.3), 0.0)))
SUN_L = bpy.data.lights.new('dusk_sun', 'SUN'); SUN_L.energy = 2.5; SUN_L.color = (1.0, 0.7, 0.45); SUN_L.angle = R(3)
SUN_O = bpy.data.objects.new('dusk_sun', SUN_L); S.collection.objects.link(SUN_O); SUN_O.rotation_euler = (R(78), 0, R(-115))
SKY_M = bpy.data.materials.new('sky_out'); SKY_M.use_nodes = True
OUT_GEAR = TRUCK + TRUCK_L + TOWERS + TOWER_L + DRONE + [DRONE_SPOT] + TBEAMS
OUTSET = OUT + CHUNKS + OUT_GEAR + STREETL + [SUN_O]
OUTSET = list(dict.fromkeys(OUTSET))
