
# ================================================================ water effects, rescue boats, ambulances
def foam_mat(name, attr='a', scale=3.0, thr=0.8, radial=True):
    """white foam with a noisy edge over transparent; object property attr (0..1) sets how much shows"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    b.inputs['Base Color'].default_value = (0.92, 0.90, 0.84, 1); b.inputs['Roughness'].default_value = 0.6
    co = coord(nt, 'Generated'); sx = sepz(nt, co)
    rad = math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'ADD', math_(nt, 'POWER', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', sx.outputs['X'], 0.5), 2.0), 2.0),
                                                                                    math_(nt, 'POWER', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', sx.outputs['Y'], 0.5), 2.0), 2.0)), 0.5), 1.0))
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    nt.links.new(coord(nt, 'Object'), nz.inputs['Vector']); nt.links.new(objattr(nt, 'tw'), nz.inputs['W'])
    al = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', math_(nt, 'ADD', math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.9), math_(nt, 'MULTIPLY', rad, 0.6 if radial else 0.0)), thr), objattr(nt, attr))
    nt.links.new(al, b.inputs['Alpha']); return m
FOAM_M = foam_mat('foam', scale=9.0, thr=0.95)
BOW_FOAM = prim('plane', 'bow_foam', FOAM_M, TK, loc=(-2, 0, 0.06), size=1, scale=(26, 36, 1)); BOW_FOAM['a'] = 1.0; BOW_FOAM['tw'] = 0.0
# the bow wave: a curling ridge of white water peeling off each side of the stem
WAVE_M = foam_mat('bowwave', scale=6.0, thr=0.22, radial=False); BOW_WAVE = []
for sy in (-1, 1):
    vs = []; fs = []
    for i in range(14):
        u = i / 13; x_ = -u * 34; yb = (12.4 * (math.sin(math.pi / 2 * min(u * 34, 28) / 28)) ** 0.75 + 0.3) * sy
        out = (0.6 + 4.0 * u) * sy; hgt = 1.6 * (1 - u) ** 1.3 + 0.1
        vs += [(x_, yb, hgt), (x_, yb + out * 0.5, hgt * 0.75), (x_, yb + out, 0.0)]
        if i: fs += [(3 * i - 3, 3 * i - 2, 3 * i + 1, 3 * i), (3 * i - 2, 3 * i - 1, 3 * i + 2, 3 * i + 1)]
    o = mesh(f'bow_wave{sy}', vs, fs, WAVE_M, TK); o['a'] = 1.0; o['tw'] = 0.0; BOW_WAVE.append(o)
HIT_FOAM = prim('plane', 'hit_foam', foam_mat('hitfoam', scale=1.5), loc=(-4, 2.0, 0.08), size=1, scale=(30, 22, 1)); HIT_FOAM['a'] = 0.0; HIT_FOAM['tw'] = 0.0
ROLL_FOAM = prim('plane', 'roll_foam', foam_mat('rollfoam', scale=1.2), loc=(-2, -2.0, 0.09), size=1, scale=(110, 40, 1)); ROLL_FOAM['a'] = 0.0; ROLL_FOAM['tw'] = 0.0
# splash: a burst of droplets (small spheres) thrown from a point, falling under gravity; shared drop meshes reused per burst
DROP_M = mat('drop', (0.88, 0.86, 0.80), 0.35)
class Burst:
    def __init__(s, name, n, seed, speed=9.0, up=1.0, size=0.18, spread=1.0, dirv=(0, 0, 1)):
        r_ = random.Random(seed); s.d = []; s.v = []
        for i in range(n):
            o = prim('ico_sphere', f'{name}{i}', DROP_M, loc=(0, 0, -50), size=1, scale=(size * (0.5 + r_.random()),) * 3, subdivisions=1); o.hide_render = True
            dv = Vector(dirv).normalized(); rv = Vector((r_.gauss(0, 1), r_.gauss(0, 1), r_.gauss(0, 1))) * spread
            v = (dv + rv).normalized() * speed * (0.5 + r_.random()); v.z = abs(v.z) * up + 2.0; s.d.append(o); s.v.append(v)
    def at(s, origin, t):
        for o, v in zip(s.d, s.v):
            if t < 0 or t > 2.2: o.hide_render = True; continue
            p = Vector(origin) + v * t + Vector((0, 0, -4.9 * t * t)); o.location = p; o.hide_render = p.z < -0.3
HIT_SPLASH = Burst('hs', 70, 1, 11.0, 1.4, 0.12, 0.9, (0.2, -1.0, 0.4))
ROLL_SPLASH = Burst('rs', 90, 2, 9.0, 1.2, 0.14, 1.2, (0, -1.0, 0.6))
JUMP_SPLASH = [Burst(f'js{k}', 18, 10 + k, 4.0, 1.5, 0.12, 0.7) for k in range(2)]
GLASS_BITS = Burst('gb', 40, 3, 6.0, 0.6, 0.06, 0.8, (0.1, 1.0, 0.2))
for o in GLASS_BITS.d: o.data.materials[0] = GLASS_IN
# the flood inside the dining room: a sheet of river pouring through the hole and a rising pool on the carpet (boat frame)
def pour_mat():
    m = bpy.data.materials.new('pour'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; m.blend_method = 'BLEND'
    b.inputs['Base Color'].default_value = (0.16, 0.13, 0.07, 1); b.inputs['Roughness'].default_value = 0.04; b.inputs['Transmission Weight'].default_value = 0.5; b.inputs['IOR'].default_value = 1.33
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 5.0; nz.inputs['Detail'].default_value = 6
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4.0, 0.6, 0.25); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector']); nt.links.new(mp.outputs[0], nz.inputs['Vector'])
    nt.links.new(objattr(nt, 'tw'), nz.inputs['W'])
    nt.links.new(mixc(nt, math_(nt, 'POWER', nz.outputs['Fac'], 3.0), (0.14, 0.11, 0.06), (0.62, 0.58, 0.48)), b.inputs['Base Color'])
    al = math_(nt, 'MULTIPLY', math_(nt, 'ADD', 0.55, math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.5)), objattr(nt, 'a'))
    nt.links.new(al, b.inputs['Alpha'])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.6; nt.links.new(nz.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    return m
POUR_M = pour_mat()
POUR = []
for k in range(3):                                                       # three falling sheets at the hole, curving in and down
    xk = HIT_X[0] + 2.0 + k * 3.6
    pts = [(xk, RB_CY - 6.6 + 1.6 * (u / 7) ** 0.7, 3.2 - 1.7 * (u / 7) ** 1.6) for u in range(8)]
    vs = []; fs = []
    for i, p_ in enumerate(pts):
        vs += [(p_[0] - 1.3, p_[1], p_[2]), (p_[0] + 1.3, p_[1], p_[2])]
        if i: fs.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    o = mesh(f'pour{k}', vs, fs, POUR_M, RBL); o['a'] = 0.0; o['tw'] = 0.0; POUR.append(o)
FLOOD = rbx('flood', (70, 12.6, 0.02), (-4, RB_CY, 1.52), mat('flood', (0.20, 0.16, 0.09), 0.04, trans=0.3, ior=1.33))
FLOOD.hide_render = True
# rescue boats: an orange Coast Guard response boat and a grey harbor police boat with blue lights; ambulances with flashing lights on the wharf
CG_ORANGE = mat('cg_orange', (0.95, 0.35, 0.05), 0.5); CG_GREY = mat('cg_grey', (0.55, 0.57, 0.60), 0.5)
def small_boat(name, hull_m, cab_m, light_col):
    g = empty(name); g.rotation_mode = 'XYZ'
    loft(name + '_h', [(-5, 1.6, -0.6, 0.9, 6), (0, 1.7, -0.7, 1.0, 6), (3, 1.4, -0.6, 1.1, 4), (5, 0.3, 0.0, 1.3, 2)], hull_m, g, seg=14)
    box(name + '_cab', (2.6, 2.2, 1.4), (-0.8, 0, 1.7), cab_m, bv=0.15, parent=g)
    box(name + '_win', (2.65, 2.25, 0.5), (-0.8, 0, 2.0), mat(name + 'w', (0.05, 0.07, 0.09), 0.05), parent=g)
    lt = box(name + '_lt', (0.5, 1.0, 0.18), (-0.8, 0, 2.5), emis(name + 'le', light_col, 0.0), parent=g)
    return g, lt
CG_BOAT, CG_LT = small_boat('cgboat', CG_ORANGE, mat('cgw', (0.92, 0.92, 0.92), 0.5), (1.0, 0.25, 0.1))
PD_BOAT, PD_LT = small_boat('pdboat', CG_GREY, CG_GREY, (0.1, 0.3, 1.0))
CG_WAKE = prim('plane', 'cg_wake', foam_mat('cgwake', scale=2.0), CG_BOAT, loc=(-7, 0, -0.85), size=1, scale=(12, 5, 1)); CG_WAKE['a'] = 1.0; CG_WAKE['tw'] = 0.0
PD_WAKE = prim('plane', 'pd_wake', foam_mat('pdwake', scale=2.0), PD_BOAT, loc=(-7, 0, -0.85), size=1, scale=(12, 5, 1)); PD_WAKE['a'] = 1.0; PD_WAKE['tw'] = 0.0
AMBS = []
for i in range(3):
    g = empty(f'amb{i}', loc=(22 + 9 * i, 34 + 1.5 * i, 3.4)); g.rotation_euler = (0, 0, 0.1 * i)
    box(f'amb{i}_body', (6.5, 2.4, 2.6), (0, 0, 1.6), mat(f'ambw{i}', (0.94, 0.94, 0.92), 0.4), bv=0.15, parent=g)
    box(f'amb{i}_stripe', (6.55, 2.45, 0.35), (0, 0, 1.4), mat(f'ambr{i}', (0.80, 0.08, 0.06), 0.4), parent=g)
    box(f'amb{i}_cab', (1.8, 2.3, 1.2), (3.6, 0, 1.0), mat(f'ambw{i}b', (0.94, 0.94, 0.92), 0.4), bv=0.15, parent=g)
    for w_ in (-2.2, 2.2):
        for sy in (-1.1, 1.1):
            tube(f'amb{i}_wh{w_}{sy}', [(w_, sy - 0.15, 0.4), (w_, sy + 0.15, 0.4)], 0.42, BLACK_RUB, g, seg=12)
    l1 = box(f'amb{i}_l1', (0.3, 0.6, 0.2), (2.9, -0.6, 3.0), emis(f'aml1{i}', (1.0, 0.1, 0.05), 0.0), parent=g)
    l2 = box(f'amb{i}_l2', (0.3, 0.6, 0.2), (2.9, 0.6, 3.0), emis(f'aml2{i}', (0.2, 0.3, 1.0), 0.0), parent=g)
    AMBS.append((g, l1, l2))
def flash(o, on, t, rate=3.0, ph=0.0, peak=40.0):
    nd = o.data.materials[0].node_tree.nodes['Emission']
    nd.inputs['Strength'].default_value = (peak if (math.sin(2 * math.pi * rate * t + ph) > 0.2) else 0.4) if on else 0.0
