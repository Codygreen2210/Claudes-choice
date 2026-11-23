
# ================================================================ the four maidens
M1 = build_maiden('m1', M_IRON, M_IRDK); M1['root'].location = (0.0, 2.0, 0.3)                     # the dungeon one (the myth)
M2 = build_maiden('m2', M_IRON2, M_IRDK, base_m=M_WOODRAW); M2['root'].location = (13.0, 2.9, 0.25) # pieced together in the shop
M3 = build_maiden('m3', M_IRON, M_IRDK); M3['root'].location = (CX, CY - 0.05, 0.1)                 # the copy in the crate for Chicago
M4 = build_maiden('m4', M_IRON4, M_IRDK); M4['root'].location = (LP.x + 1.0, LP.y, 0.37)           # Baghdad: on its back under the leaves
M4['root'].rotation_mode = 'QUATERNION'
M4['root'].rotation_quaternion = Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0))).to_quaternion()     # up -> -x (head toward the window), front -> +z (face up)
for d, s_ in zip(M3['doors'], (-1, 1)): d.rotation_euler = (0, 0, s_ * R(108))
for d, s_ in zip(M4['doors'], (-1, 1)): d.rotation_euler = (0, 0, s_ * R(4))
M3IN = light_at('m3in', 'POINT', (CX, CY - 0.05, 1.3), (CX, CY, 0), 0.0, (1.0, 0.8, 0.55), 0.1)
# the shop maiden's parts: where each sits before it's put together (offset from its place, rotation, a little lift on the way)
M2_REST = {}
for nm in ('foot', 'back', 'top', 'head', 'doorL', 'doorR', 'plinth'):
    o = M2[nm]; M2_REST[nm] = (o.location.copy(), o.rotation_euler.copy())
S4 = min(1.0, (DUR[4] - 0.35) / 3.95)   # the assembly fits beat 4 (shorter one-take read): every start and length scaled
M2_FROM = {     # name: (offset, euler, start time from B4, duration)
    'plinth': (Vector((0, 0, 0)), Vector((0, 0, 0)), 0.0, 0.01),
    'foot': (Vector((-1.25, -0.55, -0.12)), Vector((0, 0, R(30))), 0.25, 0.7),
    'back': (Vector((1.55, 0.55, -0.18)), Vector((0, 0, R(-55))), 0.55, 0.9),
    'top': (Vector((1.95, 0.6, -0.72)), Vector((R(12), 0, R(40))), 1.25, 0.75),
    'head': (Vector((2.45, 0.6, -0.7)), Vector((0, R(-20), R(70))), 1.75, 0.75),
    'doorL': (Vector((-1.6, 0.9, -0.12)), Vector((0, 0, R(-75))), 2.3, 0.85),
    'doorR': (Vector((-1.15, -0.95, -0.12)), Vector((0, 0, R(60))), 2.75, 0.85),
}
M2_FROM = {k: (o, e, ts * S4, max(du * S4, 0.01)) for k, (o, e, ts, du) in M2_FROM.items()}
# dust that bursts out of the seam when the door slams
M_DUST = mat('dust', (0.55, 0.50, 0.44), 0.95); nt_ = M_DUST.node_tree; M_DUST.blend_method = 'BLEND'
nt_.links.new(objattr(nt_, 'a'), nt_.nodes['Principled BSDF'].inputs['Alpha'])
DUST = []
gd = random.Random(11)
for k in range(70):
    z0 = gd.uniform(0.35, 1.9); v = Vector((gd.uniform(-0.9, 0.9), gd.uniform(-1.4, -0.3), gd.uniform(-0.1, 0.5))); r0 = gd.uniform(0.008, 0.025)
    o = prim('ico_sphere', f'dust{k}', M_DUST, None, loc=(0, 0, -50), subdivisions=1, radius=r0); o['a'] = 0.0
    DUST.append((o, Vector((gd.uniform(-0.05, 0.05), 2.0 - 0.37, z0 + 0.3)), v, gd.uniform(0.6, 1.0)))
# sparks drifting up from the torches
EMB = []
M_EMB = emis_mix('ember', (1.0, 0.45, 0.12), 12.0, 'a')
for k in range(24):
    o = prim('ico_sphere', f'emb{k}', M_EMB, None, loc=(0, 0, -50), subdivisions=1, radius=0.006); o['a'] = 0.0
    EMB.append((o, k % 2, gd.uniform(0, 3.0), gd.uniform(0.25, 0.6), gd.uniform(-0.1, 0.1), gd.uniform(-0.1, 0.1)))
# a tape measure along the Baghdad maiden (7 feet)
TAPE = box('tape', (1.0, 0.035, 0.006), (0, 0, 0), emis('tapeglow', (1.0, 0.82, 0.1), 3.0)); TAPE.location = (-50, 0, 0)
TAPE_ENDS = []
for k in range(2): o = box(f'tapeend{k}', (0.012, 0.09, 0.07), (-50, 0, 0), emis(f'tapee{k}', (1.0, 0.82, 0.1), 3.0)); TAPE_ENDS.append(o)
# loose leaves skittering over the courtyard in the wind
LOOSE = []
for k in range(26):
    p = Vector((gd.uniform(26.5, 37.0), gd.uniform(-4.5, 4.5), 0.01))
    o = leaf(f'loose{k}', p, (0, 0, gd.uniform(0, 6.3)), gd.uniform(0.09, 0.14), M_LEAF[k % 4], None)
    LOOSE.append((o, p.copy(), gd.uniform(0.5, 1.4), gd.uniform(0, 6.3)))
# framed pictures along the hall
for k, (xf, wf, hf) in enumerate(((3.3, 1.0, 1.3), (10.6, 1.2, 0.9), (16.3, 0.9, 1.2), (22.3, 1.1, 1.4))):
    box(f'frame{k}', (wf + 0.14, 0.06, hf + 0.14), (xf, 5.36, 2.5), M_GILT, bv=0.02, parent=HALL)
    cv = box(f'canvas{k}', (wf, 0.02, hf), (xf, 5.32, 2.5), brick_mat(f'canvasm{k}', (0.18, 0.14, 0.09), (0.10, 0.12, 0.10), (0.15, 0.10, 0.06), 0.4 + 0.3 * k, rough=0.6, plane='xz', bump=0.05, row=0.4, w=1.3, mortar_w=0.2, seed=k * 1.3), parent=HALL)
