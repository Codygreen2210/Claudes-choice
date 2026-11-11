# ================================================================ LOOSE THINGS pulled to a hole, the masks, a shirt
PAPER_M = noisy(mat('paper', (0.92, 0.9, 0.86), 0.7), 30.0, 0.08)
NAPKIN_M = mat('napkin', (0.95, 0.95, 0.95), 0.85, sheen=0.3)
CUP_M = mat('cup', (0.96, 0.96, 0.96), 0.4)
BAG_M = mat('snack_bag', (0.8, 0.15, 0.1), 0.3, metal=0.4)
MAG_M = noisy(mat('magazine', (0.2, 0.45, 0.7), 0.35, coat=0.4), 20.0, 0.3)
def card(name, w, h, m):
    o = box(name, (w, h, 0.002), (0, 0, 0), m); o.rotation_mode = 'XYZ'; return o
def cup(name):
    o = lathe(name, [(0.0, 0.0), (0.028, 0.0), (0.032, 0.002), (0.04, 0.095), (0.042, 0.1), (0.038, 0.1), (0.03, 0.006), (0.0, 0.006)], 24, CUP_M)
    o.rotation_mode = 'XYZ'; return o
class Flyers:
    """things pulled toward a hole: each starts at P0, waits 'delay', speeds up toward the hole (with a little weave), goes through and
    away (out = direction outside). Pure function of time, so frames can render in any order."""
    def __init__(self, items, seed):
        rr = np.random.default_rng(seed); self.items = []
        for o, P0, delay, *air in items:
            self.items.append(dict(o=o, P0=Vector(P0), d=delay, air=bool(air), acc=rr.uniform(9, 18), spin=Vector(rr.normal(size=3) * 9.0), ph=rr.uniform(0, 6.3), wv=rr.uniform(0.05, 0.2),
                                   rot0=Vector(o.rotation_euler) if o.rotation_mode == 'XYZ' else Vector()))
        self.objs = [it['o'] for it in self.items]
    def at(self, t, H, out, slow=1.0, on=True):
        for it in self.items:
            o = it['o']; o.hide_render = not on
            if not on: continue
            if it['air'] and t <= it['d']: o.hide_render = True
            tau = max(0.0, (t - it['d'])) * slow; P0 = it['P0']; D = Vector(H) - P0; L = max(D.length, 1e-3)
            dist = 0.5 * it['acc'] * tau * tau
            if dist < L:
                s = dist / L; side = D.cross(V3(0, 0, 1)); side = side.normalized() if side.length > 1e-4 else V3(1, 0, 0)
                p = P0 + D * s + side * math.sin(s * 7 + it['ph']) * it['wv'] * s * (1 - s) * 4 + V3(0, 0, 0.25 * s * (1 - s))
            else:
                v = math.sqrt(2 * it['acc'] * L); tt_ = (dist - L) / max(v, 1e-3); p = Vector(H) + Vector(out).normalized() * (v * tt_ + 4.0 * tt_ * tt_)
            o.location = p; o.rotation_euler = tuple(it['rot0'] + it['spin'] * tau * (0.2 if tau < 0.05 else 1.0))
rng_ = np.random.default_rng(7)
# ---- the blowout: things in the rows around his are pulled to his window
H_WIN = V3(wall_x(WIN_Z) + 0.05, MY - 0.06, WIN_Z)
_its = []
for i in range(34):
    kind_ = ['paper', 'napkin', 'cup', 'paper', 'napkin', 'bag', 'mag'][i % 7]
    row = MYROW + int(rng_.integers(-3, 3)); sx = rng_.choice([0.52, 0.98, 1.44, -0.52, -0.98, 1.44]); y = ROW_Y[row] + rng_.uniform(-0.45, 0.1)
    z = rng_.choice([0.47, 0.78, 0.02, 0.66])
    if kind_ == 'paper': o = card(f'fly_paper_{i}', 0.21, 0.28, PAPER_M)
    elif kind_ == 'napkin': o = card(f'fly_napkin_{i}', 0.16, 0.16, NAPKIN_M)
    elif kind_ == 'cup': o = cup(f'fly_cup_{i}')
    elif kind_ == 'bag': o = box(f'fly_bag_{i}', (0.1, 0.14, 0.02), (0, 0, 0), BAG_M, bv=0.008); o.rotation_mode = 'XYZ'
    else: o = card(f'fly_mag_{i}', 0.2, 0.27, MAG_M)
    o.rotation_euler = tuple(rng_.uniform(-0.3, 0.3, 3)); _its.append((o, (sx, y, z), rng_.uniform(-0.25, 0.9)))
for i in range(4):                                                       # close to the camera (frame one): papers already on their way
    o = card(f'fly_near_{i}', 0.15 if i % 2 else 0.12, 0.2 if i % 2 else 0.12, PAPER_M if i % 2 else NAPKIN_M)
    o.rotation_euler = tuple(rng_.uniform(-1, 1, 3)); _its.append((o, (MYSEAT_X - 0.3 + rng_.uniform(-0.12, 0.12), MY - 0.42 + rng_.uniform(-0.12, 0.12), rng_.uniform(1.15, 1.4)), -0.2 + 0.03 * i, True))
FLY_W = Flyers(_its, 3)
# a few drifting in front of the camera in the first beat (fill the frame)
# ---- the door plug: two phones and a shirt pulled out of the -x side hole
H_PLUG = V3(-wall_x(PLUG_Z) - 0.1, PLUG_Y, PLUG_Z)
PHN = [box(f'fly_phone_{k}', (0.074, 0.155, 0.008), (0, 0, 0), PHONE_M, bv=0.008) for k in range(2)]
for p_ in PHN:
    p_.rotation_mode = 'XYZ'; sc_ = box(p_.name + '_scr', (0.066, 0.145, 0.001), (0, 0, 0.0043), SCREEN_M, bv=0.004, parent=p_)
_its2 = [(PHN[0], (-1.0, ROW_Y[PLUG_ROW + 1] - 0.2, 0.66), 0.25), (PHN[1], (-0.5, ROW_Y[PLUG_ROW] - 0.3, 0.47), 0.55)]
for i in range(10):
    o = card(f'fly2_paper_{i}', 0.16 if i % 2 else 0.21, 0.16 if i % 2 else 0.28, NAPKIN_M if i % 2 else PAPER_M)
    _its2.append((o, (rng_.uniform(-1.5, -0.3), ROW_Y[PLUG_ROW + int(rng_.integers(-2, 2))] + rng_.uniform(-0.4, 0.1), rng_.choice([0.47, 0.66, 0.05])), rng_.uniform(0.0, 1.4)))
FLY_P = Flyers(_its2, 5)
# the shirt: a T outline, waving (verts moved every frame)
SHIRT2_M = mat('teen_shirt', (0.15, 0.32, 0.18), 0.85, sheen=0.5)
_sh = [(-0.24, -0.35), (0.24, -0.35), (0.24, 0.12), (0.36, 0.05), (0.42, 0.18), (0.2, 0.33), (0.08, 0.3), (0.0, 0.26), (-0.08, 0.3), (-0.2, 0.33), (-0.42, 0.18), (-0.36, 0.05), (-0.24, 0.12)]
bm_ = bmesh.new(); vs_ = [bm_.verts.new((x, y, 0)) for x, y in _sh]; bm_.faces.new(vs_)
bmesh.ops.triangulate(bm_, faces=bm_.faces[:]); bmesh.ops.subdivide_edges(bm_, edges=bm_.edges[:], cuts=3, use_grid_fill=True)
SHME = bpy.data.meshes.new('shirt'); bm_.to_mesh(SHME); bm_.free(); SHIRT2 = obj('flying_shirt', SHME, SHIRT2_M); SHIRT2.rotation_mode = 'XYZ'
_sd = SHIRT2.modifiers.new('cloth_thick', 'SOLIDIFY'); _sd.thickness = 0.004
for p_ in SHME.polygons: p_.use_smooth = True
SH_BASE = np.array([v.co[:] for v in SHME.vertices])
def shirt_wave(t, amp=0.06):
    x, y = SH_BASE[:, 0], SH_BASE[:, 1]; z = amp * (np.sin(x * 9 + t * 22) + 0.6 * np.sin(y * 11 - t * 17)) * (0.4 + np.abs(x) * 2)
    SHME.vertices.foreach_set('co', np.stack([x, y, z], 1).reshape(-1).astype(np.float32)); SHME.update()
FLY_S = Flyers([(SHIRT2, (-0.55, ROW_Y[PLUG_ROW] - 0.15, 1.15), 0.0)], 9); FLY_S.items[0]['acc'] = 6.0
# ---- masks: a door in the service panel over each row opens, three masks drop on tubes and swing
MASK_M = mat('mask', (1.0, 0.82, 0.05), 0.45, coat=0.3)
TUBEM = mat('mask_tube', (0.95, 0.95, 0.9), 0.2, trans=0.6)
BAGM = mat('mask_bag', (0.9, 0.95, 1.0), 0.15, trans=0.7, alpha=0.6)
MASKS = []                                                               # (row, side, seat_x, cup, tube curve, door)
def tube_curve(name):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(3); o = bpy.data.objects.new(name, cu); S.collection.objects.link(o); cu.materials.append(TUBEM); return o
MASK_ROWS = list(range(MYROW - 4, MYROW + 3))
DOORS = {}
for side in (1, -1):
    for r_ in MASK_ROWS:
        y = ROW_Y[r_]
        dpiv = empty(f'door_piv_{side}_{r_}', loc=(side * 1.12, y - 0.5, 1.588)); dpiv.rotation_mode = 'XYZ'
        door = box(f'mask_door_{side}_{r_}', (0.46, 0.2, 0.012), (side * 0.23, 0.0, -0.006), TRIM_M, bv=0.003, parent=dpiv); DOORS[(side, r_)] = (dpiv, door)
        CABIN.append(door)
        CABIN.append(box(f'mask_hole_{side}_{r_}', (0.44, 0.18, 0.004), (side * 1.35, y - 0.5, 1.586), DARK_M))
        for k, sx in enumerate((0.52, 0.98, 1.44)):
            c_ = lathe(f'mask_{side}_{r_}_{k}', [(0.0, 0.0), (0.022, 0.002), (0.036, 0.016), (0.044, 0.038), (0.046, 0.046), (0.043, 0.047), (0.04, 0.04), (0.032, 0.02), (0.0, 0.012)], 24, MASK_M)
            c_.rotation_mode = 'QUATERNION'; t_ = tube_curve(f'mask_tube_{side}_{r_}_{k}')
            MASKS.append(dict(row=r_, side=side, sx=side * sx, cup=c_, tube=t_, top=V3(side * (1.2 + 0.08 * (k - 1)), y - 0.5, 1.585), seed=k * 1.7 + r_ * 0.9 + side))
def masks(t, drop_t=None, slow=1.0, mine=None):
    """drop_t: when the doors pop (None = still shut); mine: (cup position, facing dir) for his mask once he holds / wears it"""
    for (side, r_), (dpiv, door) in DOORS.items():
        k = 0.0 if drop_t is None else smooth(0.0, 0.12, (t - drop_t) * slow)
        dpiv.rotation_euler = (0, side * R(-100) * k, 0)
    for m in MASKS:
        cup_, tub = m['cup'], m['tube']; on = drop_t is not None and t >= drop_t
        mine_ = m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01
        on = on and m['row'] != HIDE_ROW[0] and not (HIDE_ROW[0] is not None and m['row'] == MYROW and not mine_); cup_.hide_render = tub.hide_render = not on
        if not on: continue
        tau = (t - drop_t) * slow
        fall = min(1.0, 0.5 * 9.8 * tau * tau / 0.42)                    # falls 42 cm, then bounces on the tube and swings
        hang = m['top'] + V3((m['sx'] - m['top'].x) * 0.55, 0.12, -0.42 * fall)
        if fall >= 1.0:
            ts_ = tau - math.sqrt(2 * 0.42 / 9.8); d = math.exp(-1.6 * ts_)
            hang = hang + V3(0.05 * math.sin(4.5 * ts_ + m['seed']) * d, 0.06 * math.sin(3.7 * ts_ + m['seed'] * 2) * d, 0.05 * math.cos(9 * ts_) * d * abs(math.sin(9 * ts_)))
        face = V3(0, 0.55, -0.8)
        if mine is not None and m['row'] == MYROW and m['side'] == 1 and abs(m['sx'] - MYSEAT_X) < 0.01: hang, face = Vector(mine[0]), Vector(mine[1])
        cup_.location = hang; cup_.rotation_quaternion = (-face).to_track_quat('-Z', 'Y') if False else face.to_track_quat('Z', 'Y')
        top = m['top']; mid = top.lerp(hang, 0.5) + V3(0, 0.03, -0.05); pts = [top, top.lerp(mid, 0.6), mid.lerp(hang, 0.6), hang + face * 0.0]
        for i, p in enumerate(pts): tub.data.splines[0].points[i].co = (p.x, p.y, p.z, 1.0)
HIDE_ROW = [None]
MASK_OBJS = [m['cup'] for m in MASKS] + [m['tube'] for m in MASKS]
