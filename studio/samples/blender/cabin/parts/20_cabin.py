# ================================================================ THE CABIN (nose toward -y, his window on +x; floor z=0)
# shell: a circle R=1.9 about z=0.85 swept along y, cut by the floor; windows are real holes (boolean) so the sky shows through
RC, ZC = 1.9, 0.85; Y0C, Y1C = -6.4, 6.4
PITCH = 0.81; NROW = 15; ROW_Y = [-5.6 + PITCH * i for i in range(NROW)]; MYROW = 7; MY = ROW_Y[MYROW]      # his row
WIN_Z = 1.02; WIN_W, WIN_H, WIN_R = 0.27, 0.37, 0.11
def fix_normals(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free(); o.data.update(); return o
def wall_x(z): return math.sqrt(max(0.0, RC * RC - (z - ZC) ** 2))
def prism(name, prof, y0, y1, m, parent=None, smooth_=False):
    """profile [(x, z)...] (closed, counter-clockwise seen from -y) swept from y0 to y1"""
    n = len(prof); vs = [(x, y0, z) for x, z in prof] + [(x, y1, z) for x, z in prof]
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=smooth_)
def rrect(w, h, r, seg=6):
    """rounded rectangle outline (u, v), centred"""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(seg + 1): a = R(a0 + 90 * k / seg); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts
def ring_x(name, outer, inner, x0, x1, m, yc=0.0, zc=0.0, parent=None):
    """a flat ring (outer and inner outlines with the same point count) in the y-z plane, thickness along x"""
    n = len(outer); P = [(x0, outer), (x0, inner), (x1, inner), (x1, outer)]; vs = []
    for x, pts in P: vs += [(x, yc + u, zc + v) for u, v in pts]
    fs = []
    for a_ in range(4):
        b_ = (a_ + 1) % 4
        for i in range(n): j = (i + 1) % n; fs.append((a_ * n + i, a_ * n + j, b_ * n + j, b_ * n + i))
    return mesh(name, vs, fs, m, parent, smooth_=False)
def slab_x(name, pts_yz, x0, x1, m, yc=0.0, zc=0.0, parent=None):
    """a flat outline in the y-z plane, given thickness along x"""
    n = len(pts_yz); vs = [(x0, yc + u, zc + v) for u, v in pts_yz] + [(x1, yc + u, zc + v) for u, v in pts_yz]
    fs = [tuple(range(n)), tuple(range(n, 2 * n))[::-1]] + [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)]
    return mesh(name, vs, fs, m, parent, smooth_=False)
# ---- materials
WALL_M = noisy(mat('cabin_wall', (0.66, 0.65, 0.62), 0.45, coat=0.15), 60.0, 0.05, 0.05)
TRIM_M = mat('trim', (0.72, 0.72, 0.7), 0.35)
CARPET_M = noisy(mat('carpet', (0.13, 0.15, 0.22), 0.95, sheen=0.4), 300.0, 0.25, 0.05)
SEAT_M = noisy(mat('seat_fabric', (0.07, 0.11, 0.26), 0.9, sheen=0.6), 180.0, 0.2, 0.05)
HEADC_M = mat('headrest_cover', (0.82, 0.83, 0.85), 0.7, sheen=0.3)
PLAST_M = mat('seat_plastic', (0.35, 0.36, 0.38), 0.4)
METAL_M = mat('seat_metal', (0.6, 0.62, 0.65), 0.3, metal=1.0)
GLASS_M = mat('window_glass', (0.9, 0.95, 1.0), 0.02, trans=1.0, ior=1.49)
LAMP_M = emis('cove_light', (1.0, 0.9, 0.75), 3.0)
READ_M = emis('reading_light', (1.0, 0.95, 0.85), 2.0)
SIGN_M = emis('sign', (0.95, 0.95, 0.95), 1.5)
DARK_M = mat('dark_gap', (0.02, 0.02, 0.025), 0.6)
CABIN = []
# ---- shell (inside faces), solid 6 cm, windows cut through
_ang = [R(-26.6 + (233.2) * k / 64) for k in range(65)]
_prof = [(RC * math.cos(a), ZC + RC * math.sin(a)) for a in _ang]
_ys = [Y0C + (Y1C - Y0C) * k / 64 for k in range(65)]
vs = [(x, y, z) for y in _ys for (x, z) in _prof]; np_ = len(_prof); fs = []
for j in range(len(_ys) - 1):
    for i in range(np_ - 1): a_ = j * np_ + i; fs.append((a_, a_ + np_, a_ + np_ + 1, a_ + 1))
SHELL = mesh('shell', vs, fs, WALL_M); sol_ = SHELL.modifiers.new('thick', 'SOLIDIFY'); sol_.thickness = 0.06; sol_.offset = -1.0
_wv, _wf = [], []
for side in (1, -1):
    for y in ROW_Y:
        pts = rrect(WIN_W, WIN_H, WIN_R); n = len(pts); b0 = len(_wv)
        _wv += [(side * 1.55, y - 0.06 + u, WIN_Z + v) for u, v in pts] + [(side * 2.3, y - 0.06 + u, WIN_Z + v) for u, v in pts]
        _wf += [tuple(b0 + i for i in range(n)), tuple(b0 + n + i for i in range(n))[::-1]] + [(b0 + i, b0 + n + i, b0 + n + (i + 1) % n, b0 + (i + 1) % n) for i in range(n)]
WCUT = fix_normals(mesh('window_cutters', _wv, _wf, None, smooth_=False)); WCUT.hide_render = True; WCUT.hide_viewport = True
bo = SHELL.modifiers.new('windows', 'BOOLEAN'); bo.object = WCUT; bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'
# the door plug hole (the 2024 story): a door-sized cut on the -x side at row 11, only on in those beats
PLUG_ROW = 11; PLUG_Y = ROW_Y[PLUG_ROW] - 0.1; PLUG_W, PLUG_H, PLUG_Z = 0.66, 1.25, 0.95
_pc = rrect(PLUG_W, PLUG_H, 0.16)
PCUT = fix_normals(slab_x('plug_cutter', _pc, -2.3, -1.4, None, PLUG_Y, PLUG_Z)); PCUT.hide_render = True; PCUT.hide_viewport = True
PLUG_BO = SHELL.modifiers.new('plug', 'BOOLEAN'); PLUG_BO.object = PCUT; PLUG_BO.operation = 'DIFFERENCE'; PLUG_BO.solver = 'EXACT'
PLUG_BO.show_render = PLUG_BO.show_viewport = False
CABIN.append(SHELL)
# window glass in every hole (his one is its own object: it goes)
PANES = []
for side in (1, -1):
    for i, y in enumerate(ROW_Y):
        wx = wall_x(WIN_Z) + 0.015
        p_ = slab_x(f'pane_{side}_{i}', rrect(WIN_W - 0.01, WIN_H - 0.01, WIN_R - 0.005), side * (wx - 0.005), side * (wx + 0.005), GLASS_M, y - 0.06, WIN_Z)
        PANES.append(p_); CABIN.append(p_)
MYPANE = PANES[MYROW]
# his window's inner trim + pane: the piece that blows out (pivot = its middle)
_wx0 = wall_x(WIN_Z)
BLOW = empty("blowout", loc=(_wx0 - 0.04, MY - 0.06, WIN_Z))
RING_O = [(u * 1.3, v * 1.22) for u, v in rrect(WIN_W, WIN_H, WIN_R)]; RING_I = [(u * 1.0, v * 1.0) for u, v in rrect(WIN_W, WIN_H, WIN_R)]
BLOWP = ring_x('blow_trim', RING_O, RING_I, -0.015, 0.015, TRIM_M, 0, 0, parent=BLOW)
BLOWG = slab_x("blow_pane", rrect(WIN_W - 0.02, WIN_H - 0.02, WIN_R - 0.01), -0.009, 0.009, GLASS_M, 0, 0, parent=BLOW); BLOWG.rotation_mode = "XYZ"
CABIN += [BLOWP, BLOWG]
# window surrounds (raised trim ring around every hole, not his: his ring is BLOWP)
for side in (1, -1):
    for i, y in enumerate(ROW_Y):
        if side == 1 and i == MYROW: continue
        x_ = side * (_wx0 - 0.04); o_ = ring_x(f'trim_{side}_{i}', RING_O, RING_I, x_ - 0.015, x_ + 0.015, TRIM_M, y - 0.06, WIN_Z)
        CABIN.append(o_)
# ---- floor, ceiling, bins, lights
FLOOR = box('floor', (3.4, Y1C - Y0C, 0.06), (0, 0, -0.03), CARPET_M); CABIN.append(FLOOR)
AISLE = box('aisle_strip', (0.5, Y1C - Y0C, 0.004), (0, 0, 0.002), noisy(mat('aisle_carpet', (0.2, 0.17, 0.2), 0.95, sheen=0.3), 300.0, 0.2)); CABIN.append(AISLE)
CEIL = prism('ceiling', [(-0.95, 2.18), (0.95, 2.18), (0.85, 2.3), (-0.85, 2.3)], Y0C, Y1C, WALL_M); CABIN.append(CEIL)
for side in (1, -1):
    pr = [(0.95, 1.62), (1.66, 1.62), (wall_x(2.12) - 0.02, 2.12), (0.95, 2.12)]
    if side < 0: pr = [(-x, z) for x, z in pr][::-1]
    b_ = prism(f'bins_{side}', pr, Y0C + 0.1, Y1C - 0.1, WALL_M); bevel(b_, 0.025, 3); CABIN.append(b_)
    lip = prism(f'bin_lip_{side}', [(side * 0.93, 1.6), (side * 0.97, 1.6), (side * 0.97, 2.14), (side * 0.93, 2.14)][::side], Y0C + 0.1, Y1C - 0.1, TRIM_M); CABIN.append(lip)
    for k in range(9):                                                   # bin door seams
        y = Y0C + 0.1 + k * 1.58
        CABIN.append(box(f'bin_seam_{side}_{k}', (0.012, 0.012, 0.5), (side * 0.925, y, 1.87), DARK_M))
    cove = box(f'cove_{side}', (0.03, Y1C - Y0C - 0.4, 0.03), (side * 0.9, 0, 2.165), LAMP_M); CABIN.append(cove)
    psu = box(f'psu_{side}', (0.68, Y1C - Y0C - 0.2, 0.03), (side * 1.3, 0, 1.605), TRIM_M); CABIN.append(psu)
    for i, y in enumerate(ROW_Y):
        for dx in (-0.18, 0.0, 0.18):
            CABIN.append(prim('cylinder', f'read_{side}_{i}_{dx}', READ_M, loc=(side * (1.3 + dx), y - 0.55, 1.588), radius=0.018, depth=0.004, vertices=16))
LOW = []                                                                 # side-wall air vents / lower panel line
for side in (1, -1):
    LOW.append(box(f'dado_{side}', (0.02, Y1C - Y0C, 0.02), (side * (wall_x(0.45) - 0.03), 0, 0.45), TRIM_M))
CABIN += LOW
# ---- seats: one triple unit (mesh shared by every row), facing -y; row origin = middle of the cushions
def triple(name):
    parts = []
    for k, sx in enumerate((-0.46, 0.0, 0.46)):
        parts.append(box('cu', (0.43, 0.47, 0.11), (sx, -0.02, 0.405), SEAT_M, bv=0.035))
        bk = box('bk', (0.43, 0.1, 0.72), (sx, 0.27, 0.82), SEAT_M, bv=0.04, rot=(R(-11), 0, 0)); parts.append(bk)
        parts.append(box('hc', (0.38, 0.115, 0.2), (sx, 0.335, 1.08), HEADC_M, bv=0.03, rot=(R(-11), 0, 0)))
        parts.append(box('sh', (0.43, 0.03, 0.62), (sx, 0.335, 0.8), PLAST_M, bv=0.01, rot=(R(-11), 0, 0)))     # plastic back shell
        parts.append(box('tray', (0.36, 0.02, 0.26), (sx, 0.355, 0.86), PLAST_M, bv=0.008, rot=(R(-11), 0, 0)))
        parts.append(box('pk', (0.32, 0.03, 0.2), (sx, 0.31, 0.56), SEAT_M, bv=0.01, rot=(R(-11), 0, 0)))
    for ax in (-0.69, -0.23, 0.23, 0.69):
        parts.append(box('ar', (0.05, 0.42, 0.05), (ax, -0.02, 0.63), PLAST_M, bv=0.015))
        parts.append(box('as', (0.03, 0.08, 0.2), (ax, 0.12, 0.53), PLAST_M))
    for lx in (-0.55, 0.55):
        parts.append(box('lg', (0.04, 0.04, 0.34), (lx, -0.12, 0.17), METAL_M)); parts.append(box('lg2', (0.04, 0.04, 0.34), (lx, 0.2, 0.17), METAL_M))
        parts.append(box('ft', (0.04, 0.5, 0.03), (lx, 0.04, 0.015), METAL_M))
    parts.append(box('bar', (1.3, 0.04, 0.04), (0, 0.04, 0.33), METAL_M))
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        for md in o.modifiers: pass
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    for o in parts:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); o = bpy.context.active_object; o.name = name
    return o
SEAT_T = triple('seats_tpl'); SEAT_T.hide_render = True; SEAT_T.hide_viewport = True
SEATS = {}
for side in (1, -1):
    for i, y in enumerate(ROW_Y):
        o_ = bpy.data.objects.new(f'seats_{side}_{i}', SEAT_T.data); S.collection.objects.link(o_); o_.location = (side * 0.98, y, 0); SEATS[(side, i)] = o_; CABIN.append(o_)
MYSEAT_X = 0.98 + 0.46                                                   # his window seat (A)
# end walls (dark-ish bulkheads with a lit sign)
for yy, sg in ((Y0C, 1), (Y1C, -1)):
    CABIN.append(box(f'bulk_{yy}', (3.8, 0.05, 2.8), (0, yy, 1.2), WALL_M))
CABIN.append(box('exit_sign', (0.4, 0.02, 0.12), (0, Y0C + 0.04, 2.05), emis('exit', (0.1, 1.0, 0.3), 3.0)))
