# ================================================================ timing + the set: a backyard deck at dusk under a porch roof (the wrong place to fry),
# the house wall with a lit window, a lawn out to the fence; a second fryer far out on the grass (the right way)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
P.set_scene_dir(HERE)
SP_ = json.load(open(os.path.join(HERE, 'lines.json')))
def word_t(i, k, end=False):
    w = SP_[i].split(); wt = [len(x.strip('.,?!')) + 2.0 for x in w]; a_, b_ = TM['voice'][i]
    return a_ + (b_ - a_) * sum(wt[:k + (1 if end else 0)]) / sum(wt)
END = TOTAL
T_TOUCH = word_t(0, 10)          # skin meets the oil ("going into oil")
T_FLASH = word_t(1, 5)                # "flashes into steam"
T_XR0 = B[2] + 0.3                    # x-ray on (into the meat)
T_MELT = word_t(3, 8)                 # "as that ice melts"
T_DRIP = word_t(3, 10)                # "drips out"
T_SINK = word_t(4, 7)                 # "sinks straight to the bottom"
T_BOT = word_t(5, 4)                  # "right over the flame"
T_212 = word_t(5, 15)                 # "two hundred twelve": the drops start to boil
T_POP = word_t(6, 5) - 0.1            # "turns to steam": one drop blows into a bubble
T_1700 = word_t(6, 9)                 # "seventeen hundred times"
T_SURGE = word_t(7, 3)                # "blasts up through the oil"
T_XR1 = B[7] + 0.8                    # x-ray off: the pot goes solid again
T_OVER = word_t(7, 11)                # "over the edge"
T_POUR = B[8] + 0.2                   # oil pours down the side
T_HIT = word_t(8, 10)                 # "onto the burner"
T_CATCH = word_t(9, 3)                # "catches fire"
T_RACE = word_t(9, 7)                 # flames race up the oil
T_BALL = word_t(10, 4)                # "a fireball swallows the pot"
T_ROOF = word_t(10, 9)                # "climbs up the porch roof"
T_STATS = B[11]
T_SAFE = B[12] + 0.3                  # the camera turns out to the lawn fryer
T_RESET = B[13] + 0.6                 # (camera faces away from the deck) everything goes back to frame one
print('T', round(T_TOUCH, 2), round(T_POP, 2), round(T_OVER, 2), round(T_CATCH, 2), round(T_BALL, 2), round(T_RESET, 2), round(END, 2))

# ---------------------------------------------------------------- world: dusk sky
P.hdri('ph:qwantani_dusk_2', 0.6, 150)
DECK_Z = 0.45; WALL_Y = 3.2
# lawn: big ground with the leafy grass set, a wavy edge of grass clumps, a fence line
GRASS = P.material('ph:leafy_grass', scale=0.45, name='lawn')
lawn = prim('plane', 'lawn', GRASS, loc=(0, -8, 0), size=60.0)
try:
    b_ = GRASS.node_tree.nodes['Principled BSDF']; lk = next(l for l in GRASS.node_tree.links if l.to_socket == b_.inputs['Base Color'])
    mg = GRASS.node_tree.nodes.new('ShaderNodeMix'); mg.data_type = 'RGBA'; mg.blend_type = 'MULTIPLY'; mg.inputs['Factor'].default_value = 1.0
    GRASS.node_tree.links.new(lk.from_socket, mg.inputs['A']); mg.inputs['B'].default_value = (0.42, 0.75, 0.30, 1)
    hs = GRASS.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 1.35; GRASS.node_tree.links.new(mg.outputs['Result'], hs.inputs['Color'])
    GRASS.node_tree.links.new(hs.outputs['Color'], b_.inputs['Base Color'])
except Exception as e_: print('lawn tint skipped', e_)
fence_m = mat('fence', (0.42, 0.31, 0.20), 0.85); noisy(fence_m, 3.0, 0.25, 0.1)
for i in range(70):
    x_ = -17 + i * 0.5
    box(f'picket{i}', (0.09, 0.02, 1.5), (x_, -20.0, 0.75), fence_m)
for z_ in (0.35, 1.15): box(f'rail{z_}', (35, 0.04, 0.09), (0, -19.97, z_), fence_m)
for k in range(9):
    for s_ in (-1, 1):
        box(f'side{k}{s_}', (0.02, 2.0, 1.5), (s_ * 17, -20 + 2.0 * k + 1.0, 0.75), fence_m)
# trees behind the fence (dark masses against the dusk)
tree_m = mat('treeleaf', (0.03, 0.06, 0.03), 0.9); bark_m = mat('bark', (0.06, 0.045, 0.035), 0.9)
for k in range(9):
    x_ = -15 + k * 3.7 + 1.2 * h1(k); y_ = -22.5 - 2.0 * h1(k + 4)
    tube(f'trunk{k}', [(x_, y_, 0), (x_, y_, 2.5)], 0.18, bark_m, seg=8)
    for j in range(4):
        b_ = prim('ico_sphere', f'crown{k}_{j}', tree_m, loc=(x_ + (h1(k * 7 + j) - 0.5) * 2, y_ + (h1(k * 3 + j) - 0.5), 3.2 + 1.4 * h1(k + j)),
                  scale=(1.9 + h1(j), 1.7, 1.6 + h1(k)), subdivisions=3)
        dp = b_.modifiers.new('d', 'DISPLACE'); tx = bpy.data.textures.new(f'tc{k}{j}', 'CLOUDS'); tx.noise_scale = 0.6; dp.texture = tx; dp.strength = 0.6

# ---------------------------------------------------------------- the house: plank siding, a window with warm light, a back door
SIDING = P.material('ph:weathered_plank_siding', scale=1.2, name='siding')
try:
    b_ = SIDING.node_tree.nodes['Principled BSDF']; lk = next(l for l in SIDING.node_tree.links if l.to_socket == b_.inputs['Base Color'])
    hs = SIDING.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.35; hs.inputs['Value'].default_value = 1.35
    SIDING.node_tree.links.new(lk.from_socket, hs.inputs['Color']); SIDING.node_tree.links.new(hs.outputs['Color'], b_.inputs['Base Color'])
except Exception as e_: print('siding tint skipped', e_)
house = box('house_wall', (12.0, 0.25, 5.4), (0.0, WALL_Y + 0.125, 2.7), SIDING)
trim_m = mat('trim', (0.85, 0.84, 0.80), 0.45)
WIN_GLOW = emis('window_glow', (1.0, 0.72, 0.42), 3.5)
for wx in (-2.4, 2.6):
    box(f'win{wx}', (1.2, 0.05, 1.3), (wx, WALL_Y - 0.01, 1.95), WIN_GLOW)
    for dz in (-0.68, 0.68): box(f'winsill{wx}{dz}', (1.42, 0.12, 0.08), (wx, WALL_Y - 0.04, 1.95 + dz), trim_m)
    for dx in (-0.66, 0.66): box(f'winjamb{wx}{dx}', (0.08, 0.1, 1.42), (wx + dx, WALL_Y - 0.03, 1.95), trim_m)
    box(f'winmull{wx}', (0.04, 0.06, 1.3), (wx, WALL_Y - 0.03, 1.95), trim_m); box(f'winbar{wx}', (1.2, 0.06, 0.04), (wx, WALL_Y - 0.03, 1.95), trim_m)
door_m = mat('door', (0.35, 0.10, 0.08), 0.5, coat=0.4)
box('door', (0.95, 0.06, 2.1), (0.3, WALL_Y - 0.02, DECK_Z + 1.05), door_m, bv=0.01)
box('door_glass', (0.55, 0.07, 0.6), (0.3, WALL_Y - 0.025, DECK_Z + 1.55), WIN_GLOW)
for dx in (-0.52, 0.52): box(f'doorjamb{dx}', (0.09, 0.1, 2.2), (0.3 + dx, WALL_Y - 0.03, DECK_Z + 1.1), trim_m)
box('doorhead', (1.14, 0.1, 0.1), (0.3, WALL_Y - 0.03, DECK_Z + 2.2), trim_m)
box('doorknob', (0.05, 0.08, 0.05), (0.66, WALL_Y - 0.08, DECK_Z + 1.0), mat('brass', (0.85, 0.62, 0.3), 0.25, 1.0))
lamp = box('porch_lamp', (0.14, 0.12, 0.22), (1.05, WALL_Y - 0.08, DECK_Z + 1.9), emis('lamp_glow', (1.0, 0.75, 0.45), 6.0), bv=0.01)
light_at('porch_lamp_l', 'POINT', (1.05, WALL_Y - 0.3, DECK_Z + 1.85), (1.05, 0, 0), 25, (1.0, 0.72, 0.45), 0.08)
for wx in (-2.4, 2.6): light_at(f'winlight{wx}', 'AREA', (wx, WALL_Y - 0.15, 1.95), (wx, -3, 1.3), 30, (1.0, 0.72, 0.45), 1.1)
# ---------------------------------------------------------------- the deck: boards, joists, rails, steps down to the lawn
DECKM = P.material('ph:wood_floor_deck', scale=1.0, name='deckwood')
DX0, DX1, DY0 = -4.2, 3.6, -0.6
deck = box('deck', (DX1 - DX0, WALL_Y - DY0, 0.06), ((DX0 + DX1) / 2, (WALL_Y + DY0) / 2, DECK_Z - 0.03), DECKM)
rail_m = mat('railwood', (0.40, 0.27, 0.16), 0.75); noisy(rail_m, 6.0, 0.25, 0.1)
box('deck_fascia', (DX1 - DX0, 0.04, DECK_Z), ((DX0 + DX1) / 2, DY0 - 0.02, DECK_Z / 2), rail_m)
box('deck_fascia_l', (0.04, WALL_Y - DY0, DECK_Z), (DX0 - 0.02, (WALL_Y + DY0) / 2, DECK_Z / 2), rail_m)
# rails: along the front (gap for the steps at x 1.7..2.9) and the left side
def rail_run(p0, p1, nm):
    p0 = Vector(p0); p1 = Vector(p1); L_ = (p1 - p0).length; d_ = (p1 - p0).normalized(); n_ = int(L_ / 0.12)
    for k in range(n_ + 1):
        q = p0 + d_ * (k * L_ / max(n_, 1)); box(f'{nm}bal{k}', (0.04, 0.04, 0.82), (q.x, q.y, DECK_Z + 0.43), rail_m)
    mid = (p0 + p1) / 2; ang = math.atan2(d_.y, d_.x)
    box(f'{nm}top', (L_ + 0.1, 0.14, 0.05), (mid.x, mid.y, DECK_Z + 0.88), rail_m, rot=(0, 0, ang))
    box(f'{nm}bot', (L_, 0.08, 0.05), (mid.x, mid.y, DECK_Z + 0.06), rail_m, rot=(0, 0, ang))
    for q in (p0, p1): box(f'{nm}post{q.x:.1f}', (0.1, 0.1, 1.0), (q.x, q.y, DECK_Z + 0.5), rail_m)
rail_run((DX0, DY0, 0), (1.6, DY0, 0), 'rf'); rail_run((3.0, DY0, 0), (DX1, DY0, 0), 'rf2'); rail_run((DX0, DY0, 0), (DX0, WALL_Y - 0.1, 0), 'rl')
for k in range(3):
    box(f'step{k}', (1.4, 0.32, 0.05), (2.3, DY0 - 0.18 - 0.3 * k, DECK_Z - 0.15 * (k + 1)), DECKM)
# ---------------------------------------------------------------- the porch roof over the deck: posts, beam, rafters, a shingled top, a gutter
ROOF_Z0, ROOF_Z1 = 2.75, 2.45             # at the wall, at the front beam
POSTS_X = (-3.9, -1.2, 1.55, 3.3)
for px in POSTS_X: box(f'rpost{px}', (0.13, 0.13, ROOF_Z1 - DECK_Z), (px, DY0 + 0.15, (ROOF_Z1 + DECK_Z) / 2), rail_m)
box('beam', (DX1 - DX0 + 0.3, 0.16, 0.22), ((DX0 + DX1) / 2, DY0 + 0.15, ROOF_Z1 + 0.04), rail_m)
pitch = math.atan2(ROOF_Z0 - ROOF_Z1, WALL_Y - DY0)
RAFTERS = []
for k in range(15):
    x_ = DX0 + 0.05 + k * (DX1 - DX0 - 0.1) / 14
    RAFTERS.append(box(f'rafter{k}', (0.05, (WALL_Y - DY0) / math.cos(pitch) + 0.3, 0.14), (x_, (WALL_Y + DY0) / 2 - 0.15, (ROOF_Z0 + ROOF_Z1) / 2 + 0.16),
                       rail_m, rot=(pitch, 0, 0)))
ceil_m = mat('beadboard', (0.78, 0.76, 0.70), 0.6); noisy(ceil_m, 60.0, 0.06, 0.05)
ROOF_UNDER = box('roof_under', (DX1 - DX0 + 0.3, (WALL_Y - DY0) / math.cos(pitch) + 0.3, 0.02), ((DX0 + DX1) / 2, (WALL_Y + DY0) / 2 - 0.15, (ROOF_Z0 + ROOF_Z1) / 2 + 0.24),
                 ceil_m, rot=(pitch, 0, 0))
SHING = P.material('ph:grey_roof_01', scale=0.8, name='shingles')
ROOF_TOP = box('roof_top', (DX1 - DX0 + 0.4, (WALL_Y - DY0) / math.cos(pitch) + 0.45, 0.05), ((DX0 + DX1) / 2, (WALL_Y + DY0) / 2 - 0.2, (ROOF_Z0 + ROOF_Z1) / 2 + 0.28),
               SHING, rot=(pitch, 0, 0))
gut_m = mat('gutter', (0.88, 0.88, 0.86), 0.35, 0.3)
box('gutter', (DX1 - DX0 + 0.4, 0.12, 0.1), ((DX0 + DX1) / 2, DY0 - 0.32, ROOF_Z1 + 0.22), gut_m)
box('downspout', (0.07, 0.07, ROOF_Z1 + 0.2), (DX1 + 0.15, DY0 - 0.32, (ROOF_Z1 + 0.2) / 2), gut_m)
# string lights along the beam (warm bulbs, a catenary)
BULB = emis('bulb', (1.0, 0.78, 0.45), 9.0)
wire_pts = []
for k in range(41):
    u = k / 40; x_ = lerp(DX0 + 0.1, DX1 - 0.1, u); sag = 0.22 * (1 - (2 * ((u * 4) % 1) - 1) ** 2)
    wire_pts.append((x_, DY0 + 0.05, ROOF_Z1 - 0.1 - sag))
tube('lightwire', wire_pts, 0.004, mat('wire', (0.02, 0.02, 0.02), 0.5), seg=5)
for k in range(2, 40, 3):
    q = wire_pts[k]; prim('uv_sphere', f'bulb{k}', BULB, loc=(q[0], q[1], q[2] - 0.05), scale=(0.025, 0.025, 0.035), segments=10, ring_count=6)
# ---------------------------------------------------------------- props on the deck and the lawn
try:
    P.place('ph:wooden_picnic_table', loc=(-2.7, 1.6, DECK_Z), rot_deg=5, height=0.76)
    P.place('ph:metal_trash_can', loc=(-3.7, 2.8, DECK_Z), rot_deg=20, height=0.75)
    P.place('ph:potted_plant_02', loc=(3.15, 2.85, DECK_Z), rot_deg=40, height=0.9)
    P.place('ph:potted_plant_02', loc=(-3.75, DY0 + 0.35, DECK_Z), rot_deg=-60, height=0.75)
    P.place('ph:garden_hose_wall_mounted_01', loc=(-1.6, WALL_Y - 0.05, 0.9), rot_deg=180, height=0.5)
    P.place('ph:garden_gloves_01', loc=(-2.5, 1.55, DECK_Z + 0.77), rot_deg=30, height=0.04)
    P.place('ph:Lantern_01', loc=(-2.95, 1.7, DECK_Z + 0.77), rot_deg=0, height=0.32)
except Exception as e_: print('prop skipped', e_)
for k in range(60):                                   # grass clumps near the deck edge and out by the safe fryer
    x_ = -6 + 14 * h1(k + 3); y_ = -1.0 - 12 * h1(k + 41)
    try: P.place('ph:grass_medium_01', loc=(x_, y_, 0), rot_deg=360 * h1(k + 9), height=0.18 + 0.12 * h1(k + 2))
    except Exception: break
# light: a low warm key (last of the sun), a cool fill, a rim from behind the house
light_at('sun_key', 'SUN', (5, -6, 4), (0, 0, 0), 1.6, (1.0, 0.62, 0.38))
light_at('cool_fill', 'AREA', (-5, -6, 4), (0, 1, 1), 280, (0.55, 0.65, 1.0), 6)
light_at('pot_key', 'AREA', (0.9, 0.0, 1.75), (0.0, 1.05, 1.0), 70, (1.0, 0.9, 0.8), 1.2)
