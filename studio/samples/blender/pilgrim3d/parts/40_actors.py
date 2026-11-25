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
GL1 = glint('gl1', Vector((0, 0, -50))); GL2 = glint('gl2', Vector((0, 0, -50))); GL3 = glint('gl3', Vector((0, 0, -50)))
# ---- the Santa ending: a copy of the Pilgrim hat's buckle peels off and slams onto Santa's belt, two more onto his boots,
#      then Santa's hat pops off and the Pilgrim hat hops over onto his head (the opening drop again); leaves fall
bpy.context.view_layer.update()
TS_FLY, TS_BELT = B[7] + 0.75, B[7] + 1.75                     # "same trick ... Santa Claus"
TS_BOOT = [B[7] + 2.55, B[7] + 2.75]; BOOT_FL = 0.6             # "...buckles too"
TH_POP = B[8] + 0.05; TH_LAND = B[8] + 0.65                     # "Happy Thanksgiving"
HB3_W = HB3.matrix_world.translation.copy()
SBOOTS = [bpy.data.objects[f'sbootbk{k}'] for k in range(2)]
# each flier: (object, launch, land, start in the parent's frame, rest location, start scale)
SFLY = [(SBK, TS_FLY, TS_BELT, F_SANTA.matrix_world.inverted() @ HB3_W, SBK.location.copy(), 0.072 / 0.15)]
for k, o in enumerate(SBOOTS):
    SFLY.append((o, TS_BOOT[k], TS_BOOT[k] + BOOT_FL, o.parent.matrix_world.inverted() @ HB3_W, o.location.copy(), 0.072 / 0.05))
SHAT = [bpy.data.objects[n] for n in ('shat', 'shatfur', 'shatpom')]; SHAT_REST = [o.matrix_basis.copy() for o in SHAT]; SHAT_PIV = Vector((0, 0, 1.95))
H3_P0 = HAT3.location.copy(); H3_P1 = Vector((0.8, 0.0, 1.78))      # PH -> Santa's head, in PH's frame (same y, same floor)
assert (PH.matrix_world.translation + H3_P1 - (F_SANTA.matrix_world.translation + Vector((0, 0, 1.78)))).length < 1e-4
BELT_W = F_SANTA.matrix_world @ Vector((0, -0.19, 1.0425)); HATON_W = F_SANTA.matrix_world @ Vector((0, -0.118, 1.78 + 0.032))
BOOT_W = [o.parent.matrix_world @ (o.location) for o in SBOOTS]
GLS = [(GL1, TS_BELT, BELT_W, 1.0), (GL2, TS_BOOT[0] + BOOT_FL, BOOT_W[0], 0.6), (GL3, TS_BOOT[1] + BOOT_FL, BOOT_W[1], 0.6),
       (GL1, TH_LAND + 0.05, HATON_W, 0.8), (GL2, B[8] + 1.4, BELT_W, 1.0), (GL3, B[8] + 2.1, HATON_W, 0.8)]
