
# ================================================================ the set: river, wharf, port building, city, the Crescent City Connection
# World axes: the river runs along x (current toward -x), the wharf face is the line y = 20 (land is y > 20), water is z = 0.
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_HIT = word_t(3, 2) + 0.05                     # "smashes"
T_SHAKE = word_t(4, 4)                          # "shake"
T_POUR = word_t(5, 5)                           # "pouring"
T_LEAN = word_t(6, 4)                           # "starts to lean"
T_ROLL = word_t(9, 2)                           # "rolls over"
T_JUMP = word_t(10, 1)                          # "jump"
T_POLICE = word_t(8, 7)                         # "police"

# ---- sky: a clear November noon over the river, sun high in the south-west
_wn = W_.node_tree; WBG.inputs['Strength'].default_value = 1.0
_sky = ramp(_wn, sepz(_wn, coord(_wn, 'Generated')).outputs['Z'], [(0.0, (0.55, 0.62, 0.70)), (0.5, (0.62, 0.72, 0.85)), (0.53, (0.42, 0.58, 0.82)), (1.0, (0.16, 0.33, 0.66))])
_wn.links.new(_sky, WBG.inputs['Color'])
SUN = light_at('sun', 'SUN', (0, 0, 100), (60, 90, 0), 4.2, (1.0, 0.95, 0.86), 0.02)
SUN.data.angle = R(1.2)

# ---- the river: brown-green Mississippi water with moving chop (noise in 4D: w = time), deeper colour far out
def river_mat():
    m = bpy.data.materials.new('river'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.13, 0.11, 0.06, 1); b.inputs['Roughness'].default_value = 0.06; b.inputs['Specular IOR Level'].default_value = 0.6
    co = coord(nt, 'Object'); w_ = objattr(nt, 'tw')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.62
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 2.2, 1.0); nt.links.new(co, mp.inputs['Vector']); nt.links.new(mp.outputs[0], nz.inputs['Vector'])
    nt.links.new(w_, nz.inputs['W'])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.35; bm.inputs['Distance'].default_value = 0.25
    nt.links.new(nz.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])
    # muddy colour streaks
    nz2 = tnoise(nt, co, 0.02, 3.0); c_ = mixc(nt, nz2, (0.16, 0.13, 0.07), (0.09, 0.09, 0.05)); nt.links.new(c_, b.inputs['Base Color'])
    return m
RIVER_M = river_mat()
RIVER = prim('plane', 'river', RIVER_M, loc=(0, -300, 0), size=1, scale=(3000, 700, 1)); RIVER['tw'] = 0.0
for p in RIVER.data.polygons: p.use_smooth = False
FAR_SHORE = box('farshore', (3000, 300, 6), (0, -800, 2), mat('levee', (0.20, 0.27, 0.12), 0.9))
for i in range(60):                                                     # tree line on the west bank
    x_ = -1400 + i * 48 + h1(i) * 20
    prim('ico_sphere', f'ftree{i}', mat(f'ft{i}', (0.10 + 0.05 * h1(i + 3), 0.20 + 0.06 * h1(i + 4), 0.08), 0.9), loc=(x_, -680 - 30 * h1(i + 9), 12), scale=(18, 14, 12), subdivisions=2)

# ---- the wharf: concrete deck on piles at y 20..80, black rubber fenders on its face, yellow edge line, bollards
CONC = noisy(mat('concrete', (0.36, 0.35, 0.32), 0.85), 2.0, 0.18)
WHARF = box('wharf', (420, 70, 3.6), (0, 55, 1.6), CONC)
box('wharf_face', (420, 0.6, 5.0), (0, 20.3, 0.9), noisy(mat('wharf_face', (0.30, 0.29, 0.26), 0.9), 1.5, 0.3))
BLACK_RUB = mat('rubber', (0.025, 0.025, 0.025), 0.75)
for i in range(30):
    box(f'fender{i}', (1.6, 1.4, 3.2), (-200 + i * 14, 19.6, 1.4), BLACK_RUB, bv=0.3)
YEL = mat('yellow', (0.85, 0.65, 0.05), 0.6)
box('edge_line', (420, 0.35, 0.02), (0, 21.0, 3.41), YEL)
for i in range(22):
    lathe(f'bollard{i}', [(0.0, 0), (0.32, 0), (0.32, 0.55), (0.45, 0.65), (0.0, 0.7)], 16, mat(f'bol{i}', (0.06, 0.06, 0.07), 0.5, 0.6), loc=(-180 + i * 17, 21.8, 3.4))
# the gangway: a ramp from the wharf to the riverboat's main deck door (starboard side)
GANG_M = mat('gangway', (0.70, 0.71, 0.72), 0.35, 0.8)
GANG = box('gangway', (3.0, 6.0, 0.3), (8, 22.5, 3.2), GANG_M, rot=(R(-12), 0, 0))
for sx in (-1.4, 1.4):
    box(f'gang_rail{sx}', (0.08, 6.0, 0.08), (8 + sx, 22.5, 4.3), GANG_M, rot=(R(-12), 0, 0))
# the Port NOLA building and the warehouses behind the wharf
def windows_mat(name, wall, glass, rows=0.42, cols=0.33):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    co = coord(nt, 'Object'); sx = sepz(nt, co)
    u = math_(nt, 'FRACT', math_(nt, 'MULTIPLY', math_(nt, 'ADD', sx.outputs['X'], sx.outputs['Y']), cols))
    v = math_(nt, 'FRACT', math_(nt, 'MULTIPLY', sx.outputs['Z'], rows))
    win = math_(nt, 'MULTIPLY', math_(nt, 'GREATER_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.12), 0.0)
    win = math_(nt, 'MULTIPLY', math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', u, 0.5)), 0.36), math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', v, 0.5)), 0.3))
    nt.links.new(mixc(nt, win, wall, glass), b.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.8; rr.inputs['To Max'].default_value = 0.08; nt.links.new(win, rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], b.inputs['Roughness']); return m
PORT_BLDG = box('port_bldg', (70, 30, 24), (30, 110, 12), windows_mat('portb', (0.78, 0.76, 0.70), (0.12, 0.20, 0.28)))
box('port_roof', (72, 32, 1), (30, 110, 24.5), mat('roof', (0.35, 0.36, 0.38), 0.6))
for i, (x_, w_, h_) in enumerate([(-120, 90, 12), (-30, 60, 10), (110, 80, 14), (200, 70, 11), (-200, 60, 12)]):
    box(f'whse{i}', (w_, 40, h_), (x_, 70 + 20 * (i % 2), h_ / 2 + 3.4), mat(f'wh{i}', (0.55 + 0.1 * h1(i), 0.52, 0.48), 0.8))
# the city behind: towers of the CBD upriver past the bridge
for i in range(26):
    x_ = -560 + i * 34 + 15 * h1(i + 20); hgt = 40 + 160 * h1(i + 40) ** 1.6
    box(f'tower{i}', (24 + 10 * h1(i), 24, hgt), (x_, 380 + 120 * h1(i + 60), hgt / 2), windows_mat(f'tw{i}', (0.62 + 0.15 * h1(i + 7), 0.62, 0.64), (0.14, 0.22, 0.32)))
for i in range(40):
    x_ = -900 + i * 45; y_ = 160 + 160 * h1(i + 80)
    prim('ico_sphere', f'ctree{i}', mat(f'ct{i}', (0.12, 0.24 + 0.05 * h1(i), 0.09), 0.9), loc=(x_, y_, 10), scale=(12, 12, 10), subdivisions=2)

# ---- the Crescent City Connection: twin cantilever truss bridges across the river upstream (x ~ -330), grey steel
STEEL_G = mat('bridge_steel', (0.50, 0.53, 0.56), 0.45, 0.7)
def bridge(x0, name):
    ys = [-780 + 20 * i for i in range(int(1300 / 20) + 1)]
    def top(y): return 52 + 58 * math.exp(-((y + 330) / 150) ** 2) + 58 * math.exp(-((y - 60) / 150) ** 2) - 10 * math.exp(-((y + 135) / 80) ** 2)
    for sx in (-7, 7):
        tube(f'{name}_bot{sx}', [(x0 + sx, y, 46) for y in ys], 0.9, STEEL_G, seg=8)
        tube(f'{name}_top{sx}', [(x0 + sx, y, top(y)) for y in ys], 0.9, STEEL_G, seg=8)
        for i, y in enumerate(ys[:-1]):
            tube(f'{name}_v{sx}_{i}', [(x0 + sx, y, 46), (x0 + sx, y, top(y))], 0.45, STEEL_G, seg=6)
            y2 = ys[i + 1]; tube(f'{name}_d{sx}_{i}', [(x0 + sx, y, 46), (x0 + sx, y2, top(y2))] if i % 2 else [(x0 + sx, y, top(y)), (x0 + sx, y2, 46)], 0.4, STEEL_G, seg=6)
    box(f'{name}_deck', (15, 1300, 1.2), (x0, -130, 46.5), mat(f'{name}_dm', (0.30, 0.30, 0.32), 0.7))
    for yt in (-330, 60):
        for sx in (-7, 7):
            tube(f'{name}_pier{yt}{sx}', [(x0 + sx, yt, -2), (x0 + sx, yt, 46)], 2.2, CONC, seg=10)
bridge(-330, 'ccc_a'); bridge(-362, 'ccc_b')
