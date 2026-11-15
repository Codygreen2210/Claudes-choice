
# ================================================================ the set: a kitchen counter and a modern microwave built to real size
# World: the counter top is z = 0, the microwave's front face is the plane y = -0.20 (we look at it from -y), x is left/right.
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_START = word_t(0, 9)                         # "pressing start"
T_EXPLODE = word_t(1, 7)                       # "explode"
T_METAL = word_t(2, 10)                        # "made of metal"
T_BOUNCE = word_t(3, 2)                        # "bounce the waves"
T_FOOD = word_t(3, 15)                         # "water in your food"
T_SHAPE = word_t(4, 7)                         # "its shape"
T_SHOVE = word_t(5, 2)                         # "shove tiny charges"
T_PILE = word_t(5, 13)                         # "pile up at the sharp tips"
T_AIR = word_t(6, 6)                           # "the air around the tips breaks down"
T_SPARK = word_t(6, 19)                        # "as a spark"
T_BOLT = word_t(7, 3)                          # "tiny bolt of lightning"
T_PAPER = word_t(8, 4)                         # "paper nearby"
T_FIRE = word_t(8, 14)                         # "start a fire"
T_SPOON = word_t(9, 3)                         # "smooth spoon"
T_BARELY = word_t(9, 11)                       # "barely sparks"
T_POINTS = word_t(10, 9)                       # "it's the points"
CAM.data.clip_start = 0.002

# ---- the kitchen: a real interior (Poly Haven HDRI) for light, reflections and the view behind; a marble counter, a tiled wall
P.hdri('ph:cayley_interior', 0.9, 205)
COUNTER = box('counter', (1.6, 0.65, 0.04), (0, 0.02, -0.02), P.material('acg:Marble016', scale=1.4), bv=0.004)
box('counter_edge', (1.6, 0.03, 0.04), (0, -0.315, -0.02), mat('edge', (0.86, 0.86, 0.85), 0.2, coat=0.6))
box('cabinet', (1.6, 0.6, 0.86), (0, 0.04, -0.47), P.material('ph:kitchen_wood', scale=1.2))
WALL = box('backsplash', (1.6, 0.02, 0.6), (0, 0.36, 0.3), mat('tile', (0.92, 0.92, 0.90), 0.15, coat=0.4))
_wn = WALL.data.materials[0].node_tree; _wb = _wn.nodes['Principled BSDF']; _p = sepz(_wn, coord(_wn, 'Object'))
_gx = math_(_wn, 'LESS_THAN', math_(_wn, 'ABSOLUTE', math_(_wn, 'SUBTRACT', math_(_wn, 'FRACT', math_(_wn, 'DIVIDE', _p.outputs['X'], 0.15)), 0.5)), 0.485)
_gz = math_(_wn, 'LESS_THAN', math_(_wn, 'ABSOLUTE', math_(_wn, 'SUBTRACT', math_(_wn, 'FRACT', math_(_wn, 'DIVIDE', _p.outputs['Z'], 0.075)), 0.5)), 0.47)
_wn.links.new(mixc(_wn, math_(_wn, 'MULTIPLY', _gx, _gz), (0.55, 0.55, 0.53), (0.92, 0.92, 0.90)), _wb.inputs['Base Color'])
KEY = light_at('key', 'AREA', (-0.9, -0.9, 1.1), (0, 0, 0.15), 60, (1.0, 0.94, 0.86), 1.0)
RIM = light_at('rim', 'AREA', (0.8, 0.5, 0.9), (0, 0, 0.15), 25, (0.85, 0.9, 1.0), 0.6)

# ---- the microwave: 50 x 40 x 30 cm. Brushed steel case, black glass door with the dotted metal screen inside it,
# white enamel cavity (34 x 33 x 21 cm), a glass turntable, the mica cover of the waveguide on the right wall, a warm bulb.
MW_W, MW_D, MW_H = 0.50, 0.40, 0.30
CX0, CX1, CY0, CY1, CZ0, CZ1 = -0.225, 0.115, -0.185, 0.165, 0.035, 0.245     # the cavity box
STEEL = mat('steel', (0.62, 0.63, 0.64), 0.28, 1.0); noisy(STEEL, 900.0, 0.05, 0.08)
ENAMEL = mat('enamel', (0.86, 0.86, 0.84), 0.25, coat=0.3); ENAMEL_M = ENAMEL
CASE = []
def cbox(n, size, loc, m=STEEL, bv=0.0): o = box(n, size, loc, m, bv=bv); CASE.append(o); return o
cbox('mw_top', (MW_W, MW_D, 0.012), (0, -0.0, MW_H - 0.006), bv=0.004)
cbox('mw_bot', (MW_W, MW_D, 0.035), (0, -0.0, 0.0175))
cbox('mw_left', (0.012, MW_D, MW_H), (-MW_W / 2 + 0.006, 0, MW_H / 2), bv=0.003)
cbox('mw_right', (0.012, MW_D, MW_H), (MW_W / 2 - 0.006, 0, MW_H / 2), bv=0.003)
cbox('mw_back', (MW_W, 0.012, MW_H), (0, MW_D / 2 - 0.006, MW_H / 2))
for i_ in range(4): cbox(f'mw_foot{i_}', (0.03, 0.03, 0.008), ((-1) ** i_ * 0.2, (-1) ** (i_ // 2) * 0.16, -0.002), mat('foot', (0.02, 0.02, 0.02), 0.8))
# the cavity: five enamel walls (the x-ray beat turns them see-through by the 'xr' property)
def xray_mat(name, base, rough, metal=0.0):
    m = mat(name, base, rough, metal); nt = m.node_tree; b = nt.nodes['Principled BSDF']; out = nt.nodes['Material Output']
    gl = nt.nodes.new('ShaderNodeBsdfPrincipled'); gl.inputs['Base Color'].default_value = (0.75, 0.85, 1.0, 1); gl.inputs['Metallic'].default_value = 1.0; gl.inputs['Roughness'].default_value = 0.22
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    ghost = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(lw.outputs['Facing'], ghost.inputs['Fac']); nt.links.new(tr.outputs[0], ghost.inputs[1]); nt.links.new(gl.outputs[0], ghost.inputs[2])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, 'xr'), mx.inputs['Fac']); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(ghost.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface']); return m
CAV_M = xray_mat('cavity', (0.86, 0.86, 0.84), 0.25)
CAV = [box('cav_floor', (CX1 - CX0, CY1 - CY0, 0.004), ((CX0 + CX1) / 2, (CY0 + CY1) / 2, CZ0 - 0.002), CAV_M),
       box('cav_top', (CX1 - CX0, CY1 - CY0, 0.004), ((CX0 + CX1) / 2, (CY0 + CY1) / 2, CZ1 + 0.002), CAV_M),
       box('cav_left', (0.004, CY1 - CY0, CZ1 - CZ0), (CX0 - 0.002, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2), CAV_M),
       box('cav_right', (0.004, CY1 - CY0, CZ1 - CZ0), (CX1 + 0.002, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2), CAV_M),
       box('cav_back', (CX1 - CX0, 0.004, CZ1 - CZ0), ((CX0 + CX1) / 2, CY1 + 0.002, (CZ0 + CZ1) / 2), CAV_M)]
for o in CAV: o['xr'] = 0.0
WG = box('waveguide', (0.003, 0.07, 0.05), (CX1 - 0.0005, 0.02, 0.19), mat('mica', (0.72, 0.62, 0.45), 0.6))   # where the waves come in
# the control panel (right of the door): black glass, a green clock, the keypad
PANEL_M = mat('panel', (0.012, 0.012, 0.014), 0.12, coat=1.0)
box('panel', (MW_W / 2 - CX1 - 0.02, 0.006, MW_H - 0.05), ((CX1 + 0.02 + MW_W / 2) / 2 + 0.005, -MW_D / 2 - 0.003, MW_H / 2), PANEL_M)
CLOCK = box('clock', (0.07, 0.002, 0.018), (0.185, -MW_D / 2 - 0.0065, 0.245), emis('clock', (0.2, 1.0, 0.45), 4.0))
for r_ in range(4):
    for c_ in range(3):
        box(f'key{r_}{c_}', (0.016, 0.003, 0.010), (0.163 + 0.022 * c_, -MW_D / 2 - 0.007, 0.205 - 0.022 * r_), mat(f'kp{r_}{c_}', (0.25, 0.25, 0.26), 0.4))
START_BTN = box('start_btn', (0.06, 0.003, 0.016), (0.185, -MW_D / 2 - 0.007, 0.095), mat('startb', (0.25, 0.55, 0.30), 0.4))
# the door: frame + glass with the dotted screen (holes much smaller than the 12 cm waves, so they can't get out)
DOOR_X0, DOOR_X1 = -MW_W / 2 + 0.008, CX1 + 0.02
DOOR_M = mat('doorframe', (0.02, 0.02, 0.022), 0.15, coat=1.0)
def door_glass_mat():
    m = bpy.data.materials.new('doorglass'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1); b.inputs['Roughness'].default_value = 0.05; b.inputs['Coat Weight'].default_value = 1.0
    p = sepz(nt, coord(nt, 'Object'))
    u = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['X'], 0.004)); v = math_(nt, 'FRACT', math_(nt, 'DIVIDE', p.outputs['Z'], 0.004))
    hole = math_(nt, 'LESS_THAN', math_(nt, 'ADD', math_(nt, 'POWER', math_(nt, 'SUBTRACT', u, 0.5), 2.0), math_(nt, 'POWER', math_(nt, 'SUBTRACT', v, 0.5), 2.0)), 0.09)
    see = math_(nt, 'MAXIMUM', math_(nt, 'MULTIPLY', hole, 0.8), objattr(nt, 'xr'))        # see through the holes (and fully in x-ray)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(see, mx.inputs['Fac'])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
DOOR = empty('door', loc=(0, -MW_D / 2 - 0.004, 0))
for nm_, sz, lc in (('door_l', (0.03, 0.012, MW_H - 0.02), (DOOR_X0 + 0.015, 0, MW_H / 2)), ('door_r', (0.03, 0.012, MW_H - 0.02), (DOOR_X1 - 0.015, 0, MW_H / 2)),
                    ('door_t', (DOOR_X1 - DOOR_X0, 0.012, 0.035), ((DOOR_X0 + DOOR_X1) / 2, 0, MW_H - 0.0275)), ('door_b', (DOOR_X1 - DOOR_X0, 0.012, 0.035), ((DOOR_X0 + DOOR_X1) / 2, 0, 0.0275))):
    o = box(nm_, sz, lc, DOOR_M, bv=0.002, parent=DOOR); o['xr'] = 0.0
DGLASS = box('door_glass', (DOOR_X1 - DOOR_X0 - 0.06, 0.004, MW_H - 0.09), ((DOOR_X0 + DOOR_X1) / 2, 0, MW_H / 2), door_glass_mat(), parent=DOOR); DGLASS['xr'] = 0.0
HANDLE = box('handle', (0.016, 0.03, 0.2), (DOOR_X1 - 0.03, -0.018, MW_H / 2), STEEL, bv=0.006, parent=DOOR)
# inside light (the bulb behind the top right) and the turntable
BULB = light_at('bulb', 'POINT', (CX1 - 0.03, CY0 + 0.06, CZ1 - 0.01), (0, 0, 0), 4.0, (1.0, 0.82, 0.55), 0.01)
TT_C = Vector(((CX0 + CX1) / 2, (CY0 + CY1) / 2 + 0.005, CZ0))
TT = empty('turntable', loc=TT_C)
TT_GLASS = mat('tt_glass', (0.72, 0.86, 0.82), 0.14, trans=0.92, ior=1.5)          # green-edged tray glass, a touch frosted so it reads as a surface
lathe('tt_plate', [(0.0, 0.012), (0.132, 0.012), (0.135, 0.016), (0.135, 0.02), (0.0, 0.02)], 64, TT_GLASS, TT)
lathe('tt_ring', [(0.07, 0.0), (0.075, 0.0), (0.075, 0.011), (0.07, 0.011)], 32, mat('ring', (0.08, 0.08, 0.08), 0.5), loc=TT_C)
