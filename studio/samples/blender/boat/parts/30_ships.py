
# ================================================================ the ships
def loft(name, stations, m, parent=None, seg=24, cap_top=True):
    """stations: list of (x, half_breadth, keel_z, deck_z, boxiness n). Section: superellipse, deck edge to keel to deck edge."""
    vs = []; fs = []; K = seg + 1
    for (x_, b_, kz, dz, n_) in stations:
        for k in range(K):
            th = math.pi * k / seg; c_, s_ = math.cos(th), math.sin(th)
            y_ = b_ * math.copysign(abs(c_) ** (2 / n_), c_); z_ = dz - (dz - kz) * abs(s_) ** (2 / n_)
            vs.append((x_, y_, z_))
    for i in range(len(stations) - 1):
        for k in range(seg): fs.append((i * K + k, i * K + k + 1, (i + 1) * K + k + 1, (i + 1) * K + k))
    if cap_top:
        fs.append(tuple(i * K for i in range(len(stations))) + tuple(i * K + seg for i in range(len(stations)))[::-1])
    fs.append(tuple(range(K))[::-1]); fs.append(tuple((len(stations) - 1) * K + k for k in range(K)))
    return mesh(name, vs, fs, m, parent)

def hull_paint(name, top, boot, below, waterline=0.4, deck_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    z_ = sepz(nt, coord(nt, 'Object')).outputs['Z']
    c_ = mixc(nt, math_(nt, 'GREATER_THAN', z_, waterline), mixc(nt, math_(nt, 'GREATER_THAN', z_, waterline - 2.5), below, boot), top)
    nz = tnoise(nt, coord(nt, 'Object'), 0.6, 6.0)                       # streaks and wear
    c_ = mixc(nt, math_(nt, 'MULTIPLY', nz, 0.25), c_, (0.25, 0.18, 0.12)); nt.links.new(c_, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55; b.inputs['Metallic'].default_value = 0.3; return m

# ---- the Atlantic Asphalt: ~160 m asphalt tanker, black hull, red bottom, green deck, white house aft. Origin = stem at the waterline.
TK = empty('tanker')
_TL = 160.0
def tk_station(x_):
    """x_ from the stem (0) aft (negative)"""
    u = -x_
    if u < 28: b_ = 12.4 * (math.sin(math.pi / 2 * u / 28)) ** 0.75 + 0.25; n_ = 1.6 + 3.0 * u / 28
    elif u > _TL - 14: b_ = 12.4 - 3.0 * ((u - (_TL - 14)) / 14) ** 2; n_ = 4.6
    else: b_ = 12.4; n_ = 6.0
    deck = 6.5 + 3.0 * max(0, 1 - u / 22) ** 2 + 1.2 * max(0, (u - (_TL - 30)) / 30)
    keel = -8.0 + 6.5 * max(0, 1 - u / 9) ** 1.5
    return (x_ + (0.0 if u > 9 else 0.0), b_, keel, deck, n_)
stns = [tk_station(-u) for u in [0, 0.6, 1.5, 3, 5, 8, 12, 17, 23, 28, 40, 70, 100, 130, 146, 152, 156, 160]]
# rake: the stem leans forward at the top (the deck edge at the stem is ahead of the waterline point)
TK_HULL = loft('tk_hull', stns, hull_paint('tk_paint', (0.025, 0.025, 0.028), (0.42, 0.06, 0.05), (0.32, 0.07, 0.05)), TK, seg=28)
for v in TK_HULL.data.vertices:
    if v.co.x > -12: v.co.x += 0.16 * max(0.0, v.co.z) * max(0, 1 + v.co.x / 12)
GREEN_DECK = mat('tk_deck', (0.17, 0.30, 0.20), 0.75)
for (x0, x1) in ((-150, -26),):
    box('tk_deck', (x1 - x0, 24.2, 0.3), ((x0 + x1) / 2, 0, 6.55), GREEN_DECK, parent=TK)
WHITE_P = noisy(mat('white_paint', (0.82, 0.82, 0.80), 0.5), 3.0, 0.08)
# the house aft: five levels, bridge windows all round, wings
for lv in range(5):
    w_ = 21 - lv * 1.0; ln = 18 - lv * 1.2
    box(f'tk_house{lv}', (ln, w_, 2.9), (-146 + ln / 2 - 3, 0, 8.5 + lv * 2.9), WHITE_P, bv=0.1, parent=TK)
TK_GLASS = mat('tk_glass', (0.05, 0.08, 0.10), 0.05, 0.0)
box('tk_bridge_win', (13.3, 17.1, 1.3), (-142.4, 0, 20.9), TK_GLASS, parent=TK)
box('tk_wings', (4, 25.0, 0.4), (-139.0, 0, 20.0), WHITE_P, parent=TK)
FUN = box('tk_funnel', (6, 5, 9), (-144, 0, 26.0), mat('funnel', (0.06, 0.06, 0.07), 0.5), bv=0.6, parent=TK)
box('tk_funnel_band', (6.1, 5.1, 1.6), (-144, 0, 28.5), mat('fband', (0.60, 0.08, 0.05), 0.5), bv=0.6, parent=TK)
box('tk_mast', (0.6, 0.6, 8), (-138.5, 0, 25.5), WHITE_P, parent=TK)
# deck: pipes along the length, the manifold midships, a fore mast, asphalt heating trunk
PIPE_M = mat('pipe', (0.30, 0.34, 0.30), 0.5, 0.5)
def tk_deck_z(u): return 6.5 + 3.0 * max(0, 1 - u / 22) ** 2 + 1.2 * max(0, (u - (_TL - 30)) / 30)
for yy in (-4.4, -3.6, 3.6, 4.4):
    tube(f'tk_pipe{yy}', [(-128, yy, 6.85), (-26, yy, 6.85)], 0.28, PIPE_M, TK, seg=8)
    for k in range(9): box(f'tk_pipe_sup{yy}{k}', (0.3, 0.3, 0.35), (-125 + 12 * k, yy, 6.7), PIPE_M, parent=TK)
box('tk_trunk', (100, 6, 1.2), (-80, 0, 7.3), GREEN_DECK, bv=0.2, parent=TK)
for i in range(6):
    box(f'tk_hatch{i}', (2.2, 2.2, 0.7), (-40 - i * 16, 7.0, 6.85), GREEN_DECK, bv=0.2, parent=TK)
box('tk_manifold', (3, 20, 1.4), (-78, 0, 7.2), mat('manif', (0.75, 0.55, 0.08), 0.5), parent=TK)
tube('tk_foremast', [(-14, 0, tk_deck_z(14) - 0.2), (-14, 0, 19)], 0.35, mat('fmast', (0.85, 0.75, 0.10), 0.5), TK, seg=10)
for sy in (-1, 1):
    us = [24, 18, 12, 8, 5, 3, 1.6]
    tube(f'tk_frail{sy}', [(-u, sy * (tk_station(-u)[1] - 0.3), tk_deck_z(u) + 1.0) for u in us], 0.06, WHITE_P, TK, seg=6)
    for u in us: tube(f'tk_frailp{sy}{u}', [(-u, sy * (tk_station(-u)[1] - 0.3), tk_deck_z(u) - 0.1), (-u, sy * (tk_station(-u)[1] - 0.3), tk_deck_z(u) + 1.0)], 0.04, WHITE_P, TK, seg=6)
# white name on the bow (two thin bars stand in for the lettering at this size), white draft marks
TK.rotation_mode = 'XYZ'

# ---- the American Heritage: 90 m stern paddlewheeler, white decks with white rails, red wheel, twin black stacks.
# Parented to RB (pivot on the centre line at the waterline; a positive x-rotation lists her toward the river and rolls her over).
RB_PIV = Vector((0, 11.0, 0.0))
RB = empty('rb', loc=RB_PIV); RB.rotation_mode = 'XYZ'
RBL = empty('rb_local', RB, loc=-RB_PIV)                                 # children are placed in world-at-rest coordinates under this
def rbx(name, size, loc, m, bv=0.0, rot=(0, 0, 0)): return box(name, size, loc, m, bv, rot, RBL)
RB_WHITE = noisy(mat('rb_white', (0.86, 0.86, 0.84), 0.45), 4.0, 0.05)
RB_HULLM = hull_paint('rb_hullp', (0.88, 0.88, 0.86), (0.20, 0.20, 0.22), (0.12, 0.12, 0.13), waterline=0.0)
RB_CY = 11.0                                                             # centre line y
stR = []
for x_ in (-45, -44, -40, -20, 0, 20, 34, 39, 42, 44.5, 45.5):
    b_ = 8.0 if x_ < 30 else 8.0 * math.sqrt(max(0.02, 1 - ((x_ - 30) / 15.8) ** 2))
    stR.append((x_, b_, -2.0 + (0.8 if x_ > 40 else 0.0), 1.5, 8.0 if x_ < 30 else 3.0))
RB_HULL = loft('rb_hull', stR, RB_HULLM, RBL, seg=20)
for v in RB_HULL.data.vertices: v.co.y += RB_CY
DECK_M = mat('rb_deckm', (0.55, 0.50, 0.44), 0.7)
CARPET = noisy(mat('carpet', (0.20, 0.08, 0.07), 0.95), 18.0, 0.35)
GLASS_IN = mat('rb_glass', (0.55, 0.65, 0.70), 0.03, 0.0, trans=1.0, ior=1.2); GLASS_IN.surface_render_method = 'DITHERED'
CEIL = mat('ceiling', (0.90, 0.88, 0.82), 0.6)
GOLD = mat('gold', (0.85, 0.62, 0.22), 0.3, 1.0)
LEVELS = [(1.5, 4.3, -38, 38), (4.3, 7.1, -37, 36), (7.1, 9.9, -33, 30), (9.9, 12.7, -27, 27)]   # z0, z1, x0, x1 of each cabin
WALK = 1.6                                                               # walkway between the cabin wall and the rail
HIT_X = (-9.0, 6.0)                                                     # the stretch of the river-side wall the bow breaks
BREAK = []                                                               # parts hidden once the bow comes through
HOLE = []                                                                # torn plates shown after
def wall_run(name, x0, x1, y_, z0, z1, lvl, breakable=True):
    """a cabin wall along x at y_: lower band, posts and glass, upper band; split at the hit zone so it can break"""
    xs = [x0]
    for xb in HIT_X:
        if x0 < xb < x1: xs.append(xb)
    xs.append(x1); out = []
    for a_, b_ in zip(xs[:-1], xs[1:]):
        inhit = breakable and a_ >= HIT_X[0] - 1e-6 and b_ <= HIT_X[1] + 1e-6
        grp = []
        h_ = z1 - z0
        grp.append(rbx(f'{name}_lo{a_:.0f}', (b_ - a_, 0.18, h_ * 0.30), ((a_ + b_) / 2, y_, z0 + h_ * 0.15), RB_WHITE))
        grp.append(rbx(f'{name}_hi{a_:.0f}', (b_ - a_, 0.18, h_ * 0.22), ((a_ + b_) / 2, y_, z1 - h_ * 0.11), RB_WHITE))
        grp.append(rbx(f'{name}_gl{a_:.0f}', (b_ - a_, 0.04, h_ * 0.48), ((a_ + b_) / 2, y_, z0 + h_ * 0.54), GLASS_IN))
        n_ = max(1, int((b_ - a_) / 2.6))
        for k in range(n_ + 1):
            grp.append(rbx(f'{name}_post{a_:.0f}_{k}', (0.22, 0.24, h_ * 0.5), (a_ + (b_ - a_) * k / n_, y_, z0 + h_ * 0.54), RB_WHITE))
        if inhit: BREAK.extend(grp)
        out += grp
    return out
def rail_run(name, x0, x1, y_, z0, breakable=True, gap=None):
    xs = sorted([x0] + [xb for xb in HIT_X if x0 < xb < x1] + ([g_ for g_ in gap if x0 < g_ < x1] if gap else []) + [x1])
    for a_, b_ in zip(xs[:-1], xs[1:]):
        if gap and a_ >= gap[0] - 1e-6 and b_ <= gap[1] + 1e-6: continue    # the gate for the gangway
        inhit = breakable and a_ >= HIT_X[0] - 1e-6 and b_ <= HIT_X[1] + 1e-6
        g = [rbx(f'{name}_top{a_:.0f}', (b_ - a_, 0.12, 0.12), ((a_ + b_) / 2, y_, z0 + 1.05), RB_WHITE),
             rbx(f'{name}_mid{a_:.0f}', (b_ - a_, 0.05, 0.05), ((a_ + b_) / 2, y_, z0 + 0.55), RB_WHITE)]
        for k in range(int((b_ - a_) / 1.2) + 1):
            g.append(rbx(f'{name}_p{a_:.0f}_{k}', (0.07, 0.07, 1.05), (a_ + k * 1.2, y_, z0 + 0.52), RB_WHITE))
        if inhit: BREAK.extend(g)
for li, (z0, z1, x0, x1) in enumerate(LEVELS):
    yp, ys = RB_CY - 8.0 + WALK, RB_CY + 8.0 - WALK                       # river-side and dock-side cabin walls
    rbx(f'deck{li}', (x1 - x0 + 2 * WALK + 2, 16.0, 0.25), ((x0 + x1) / 2, RB_CY, z0 - 0.12), DECK_M if li else CARPET)
    wall_run(f'wp{li}', x0, x1, yp, z0, z1, li, breakable=li <= 2)
    wall_run(f'ws{li}', x0, x1, ys, z0, z1, li, breakable=False)
    rbx(f'wend_a{li}', (0.2, ys - yp, z1 - z0), (x0, RB_CY, (z0 + z1) / 2), RB_WHITE)
    rbx(f'wend_b{li}', (0.2, ys - yp, z1 - z0), (x1, RB_CY, (z0 + z1) / 2), RB_WHITE)
    rbx(f'ceil{li}', (x1 - x0, ys - yp, 0.1), ((x0 + x1) / 2, RB_CY, z1 - 0.06), CEIL)
    rail_run(f'rp{li}', x0 - WALK, x1 + WALK, RB_CY - 7.9, z0, breakable=li <= 2)
    rail_run(f'rs{li}', x0 - WALK, x1 + WALK, RB_CY + 7.9, z0, breakable=False, gap=(4.6, 7.4) if li == 1 else None)
    # the deck overhang above the walkway (the next deck), with a gold trim line
    rbx(f'trim_p{li}', (x1 - x0 + 2 * WALK, 0.12, 0.18), ((x0 + x1) / 2, RB_CY - 8.0, z1 - 0.02), GOLD)
    rbx(f'trim_s{li}', (x1 - x0 + 2 * WALK, 0.12, 0.18), ((x0 + x1) / 2, RB_CY + 8.0, z1 - 0.02), GOLD)
rbx('sundeck', (58, 16, 0.25), (0, RB_CY, 12.7), DECK_M)

rail_run('rtop_p', -29, 29, RB_CY - 7.9, 12.75, False); rail_run('rtop_s', -29, 29, RB_CY + 7.9, 12.75, False)
PH = rbx('pilothouse', (6, 8, 2.8), (19, RB_CY, 14.2), RB_WHITE, bv=0.1)
rbx('ph_glass', (6.1, 8.1, 0.9), (19, RB_CY, 14.6), mat('phg', (0.06, 0.09, 0.12), 0.05))
rbx('ph_roof', (7, 9, 0.3), (19, RB_CY, 15.75), mat('phroof', (0.40, 0.08, 0.07), 0.5))
STACK_M = mat('stack', (0.03, 0.03, 0.035), 0.45)
for sy in (-3.5, 3.5):
    s_ = tube(f'stack{sy}', [(25, RB_CY + sy, 12.8), (25, RB_CY + sy, 22.5)], 0.75, STACK_M, RBL, seg=16)
    lathe(f'crown{sy}', [(0.75, 0), (1.2, 0.6), (1.35, 1.0), (1.2, 1.15), (0.0, 1.15)], 20, GOLD, RBL, loc=(25, RB_CY + sy, 22.5))
# the stern paddlewheel: red buckets on two rims, inside a white housing frame
PW = empty('paddlewheel', RBL, loc=(-50.2, RB_CY, 2.4)); PW.rotation_mode = 'XYZ'
RED = mat('wheel_red', (0.62, 0.05, 0.04), 0.5)
for sy in (-5.5, 5.5):
    tube(f'pw_rim{sy}', [(4.4 * math.cos(2 * math.pi * k / 40), sy, 4.4 * math.sin(2 * math.pi * k / 40)) for k in range(41)], 0.12, RED, PW, seg=8, caps=False)
for k in range(16):
    a_ = 2 * math.pi * k / 16
    box(f'pw_bucket{k}', (0.12, 11.4, 1.0), (4.0 * math.cos(a_), 0, 4.0 * math.sin(a_)), RED, rot=(0, -a_ + math.pi / 2, 0), parent=PW)
    tube(f'pw_spoke{k}', [(0, -5.5, 0), (4.2 * math.cos(a_), -5.5, 4.2 * math.sin(a_))], 0.08, RED, PW, seg=6)
    tube(f'pw_spoke2{k}', [(0, 5.5, 0), (4.2 * math.cos(a_), 5.5, 4.2 * math.sin(a_))], 0.08, RED, PW, seg=6)
tube('pw_axle', [(0, -6, 0), (0, 6, 0)], 0.35, RED, PW, seg=10)
for sy in (-6.2, 6.2):
    rbx(f'pw_arm{sy}', (8.5, 0.5, 0.6), (-47.5, RB_CY + sy, 4.0), RB_WHITE)
# ---- the dining room on the main deck: white cloth tables, chairs, a buffet, ceiling lights; the bow comes through its river-side wall
TABLES = []
CLOTH = mat('cloth', (0.93, 0.93, 0.90), 0.8, sheen=0.4); CHAIR_M = mat('chair', (0.32, 0.18, 0.09), 0.6)
for i in range(7):
    for j in range(3):
        cx, cy = -30 + i * 9.0, RB_CY - 4.0 + j * 4.0
        if j == 0 and -12 < cx < 3: continue                              # the bow comes in here
        g = empty(f'table{i}_{j}', RBL, loc=(cx, cy, 1.5)); g.rotation_mode = 'XYZ'
        lathe(f'tcloth{i}_{j}', [(0.0, 0.78), (0.75, 0.78), (0.78, 0.74), (0.80, 0.25), (0.0, 0.25)], 24, CLOTH, g)
        tube(f'tleg{i}_{j}', [(0, 0, 0), (0, 0, 0.3)], 0.06, CHAIR_M, g, seg=8)
        for k in range(4):
            a_ = math.pi / 4 + k * math.pi / 2; c = empty(f'chair{i}_{j}_{k}', g, loc=(1.05 * math.cos(a_), 1.05 * math.sin(a_), 0)); c.rotation_euler = (0, 0, a_)
            box(f'cseat{i}{j}{k}', (0.45, 0.45, 0.06), (0, 0, 0.46), CHAIR_M, parent=c)
            box(f'cback{i}{j}{k}', (0.06, 0.45, 0.5), (0.22, 0, 0.72), CHAIR_M, parent=c)
            for lx, ly in ((-0.18, -0.18), (-0.18, 0.18), (0.18, -0.18), (0.18, 0.18)):
                box(f'cleg{i}{j}{k}{lx}{ly}', (0.04, 0.04, 0.46), (lx, ly, 0.23), CHAIR_M, parent=c)
        for k in range(3):                                               # glasses and plates on the table
            a_ = k * 2.1; lathe(f'glass{i}{j}{k}', [(0.0, 0.79), (0.035, 0.79), (0.04, 0.95), (0.0, 0.95)], 10, GLASS_IN, g, loc=(0.4 * math.cos(a_), 0.4 * math.sin(a_), 0))
        TABLES.append((g, cx, cy))
for i in range(6):
    rbx(f'ceil_light{i}', (3.0, 0.8, 0.06), (-27 + i * 10, RB_CY, 4.18), emis(f'cl{i}', (1.0, 0.92, 0.78), 6.0))
IN_LT = light_at('in_lt', 'AREA', (-6, RB_CY, 4.05), (-6, RB_CY, 0), 6500, (1.0, 0.9, 0.78), 1.0); IN_LT.parent = RBL
IN_LT.data.shape = 'RECTANGLE'; IN_LT.data.size = 64; IN_LT.data.size_y = 10
UP_LT = light_at('up_lt', 'AREA', (-6, RB_CY, 2.9), (-6, RB_CY, 9), 3500, (1.0, 0.93, 0.82), 1.0); UP_LT.parent = RBL
UP_LT.data.shape = 'RECTANGLE'; UP_LT.data.size = 64; UP_LT.data.size_y = 8
rbx('buffet', (10, 1.0, 1.0), (-8, RB_CY + 5.6, 2.0), mat('buffet', (0.35, 0.20, 0.10), 0.4))
rbx('bar_top', (10.2, 1.1, 0.06), (-8, RB_CY + 5.6, 2.53), mat('marble', (0.86, 0.84, 0.80), 0.15))
# the torn steel round the hole (shown after the hit): bent white plates pushed inward, ragged edges
for k in range(9):
    xk = HIT_X[0] + 0.6 + k * (HIT_X[1] - HIT_X[0] - 1.2) / 8; zk = 1.6 + 2.6 * h1(k + 3)
    HOLE.append(rbx(f'torn{k}', (0.35 + 0.4 * h1(k), 0.06, 0.4 + 0.5 * h1(k + 1)), (xk, RB_CY - 6.3 + 0.5 * h1(k + 7), zk), RB_WHITE,
                    rot=(R(-30 + 60 * h1(k + 2)), R(-40 + 80 * h1(k + 5)), R(-60 + 120 * h1(k + 9)))))
for o in HOLE: o.hide_render = True
HOLE.clear()
def ragged(name, x0, x1, z0, z1, y_, seed):
    r_ = random.Random(seed); pts = []
    for k in range(28):
        a_ = 2 * math.pi * k / 28; rx = (x1 - x0) / 2 * (0.75 + 0.25 * r_.random()); rz = (z1 - z0) / 2 * (0.75 + 0.25 * r_.random())
        pts.append(((x0 + x1) / 2 + rx * math.cos(a_), y_, (z0 + z1) / 2 + rz * math.sin(a_)))
    vs = [((x0 + x1) / 2, y_, (z0 + z1) / 2)] + pts; fs = [(0, 1 + k, 1 + (k + 1) % 28) for k in range(28)]
    return mesh(name, vs, fs, mat(name + 'm', (0.02, 0.018, 0.015), 0.9), RBL, smooth_=False)
HOLE.append(ragged('hull_hole', -12.5, 0.5, -1.4, 1.48, RB_CY - 8.0 - 0.03, 5))
for o in HOLE: o.hide_render = True
