# ================================================================ moving bits: falling leaves, the garments' flights, the buckles' flights, the glints
GA = random.Random(23)
LEAVES = []
for k in range(55):
    lf = leaf_mesh(f'fl{k}', M_LEAVES[k % 5], None, GA.uniform(0.028, 0.045)); lf.rotation_mode = 'XYZ'
    LEAVES.append((lf, GA.uniform(-2.2, 2.2), GA.uniform(0.2, 3.5), GA.uniform(0, 3.9), GA.uniform(0.28, 0.45), GA.uniform(0, 6.3)))
ITEM_T = [B[3] + 1.55, B[3] + 2.4, B[3] + 3.05, B[3] + 3.65]          # violet coat, green pants, blue suit, red cap (as they're said)
ORDER = ['coat', 'pants', 'suit', 'cap']; FORMS = {'coat': F_COAT, 'pants': F_PANT, 'suit': F_SUIT, 'cap': F_CAP}
FLY = {}
for k, nm in enumerate(ORDER):
    z_ = -0.17 - 0.115 * k
    src = Vector((EX - 0.15, 5.25, 2.75 + z_)); ctr = Vector((0, 0, 1.1 if nm != 'cap' else 1.38))
    FLY[nm] = (src - FORMS[nm].location - ctr, ITEM_T[k], ctr)
BUCK_T = [B[4] + 0.18, B[4] + 0.36, B[4] + 0.5]
BUCK_V = [Vector((-0.35, -0.7, 2.0)), Vector((-0.25, -0.6, 1.8)), Vector((0.3, -0.6, 1.9))]
BUCK_REST = [(b.location.copy(), b.rotation_euler.copy()) for b in BUCKLES]
BUCK_FLOOR = [-(1.23 + 0.032) + PLAT_Z * 0.0 + 0.006, -0.068 + 0.006, -0.068 + 0.006]   # local z of the floor under each buckle
M_GLINT = emis('glintm', (1.0, 0.95, 0.8), 25.0)
def glint(name, loc):
    vs = [(0, 0, 0)]; fs = []
    for i in range(8):
        a = math.pi / 4 * i; r_ = 0.07 if i % 2 == 0 else 0.012; vs.append((r_ * math.cos(a), 0, r_ * math.sin(a)))
    for i in range(8): fs.append((0, 1 + i, 1 + (i + 1) % 8))
    o = mesh(name, vs, fs, M_GLINT, None, smooth_=False, loc=loc); o.scale = (0.0,) * 3; return o
GL1 = glint('gl1', Vector((SX + 0.25 + 0.05, 3.8 - 0.21, PLAT_Z + 1.07)))
GL2 = glint('gl2', Vector((SX - 0.55 + 0.02, 3.8 - 0.13, PLAT_Z + 1.28 + 0.045)))
