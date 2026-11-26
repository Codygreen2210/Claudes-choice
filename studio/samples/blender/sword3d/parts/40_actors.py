# ================================================================ moving bits: event times (each on its word), needles, glints, confetti
T_HIT = 0.55                                   # "slams onto a scale"
T_YANK = B[1] + 0.3                            # "no knight ever..." - the myth sword is yanked away
T_ARM = B[2] + 0.75                            # "a real fighting sword" lands: 3 lb
T_TWO = B[2] + 2.55                            # "the big two-handed ones": 9.5 lb
T_BAL = B[3] + 0.6; T_SPIN = B[3] + 2.3       # drops onto the knife edge; "moved fast" - a quick spin
T_YEAR = B[4] + 0.6; T_QUOTE = B[4] + 2.1      # "seventeen hundreds"; "heavy and clumsy"
T_STAMP = B[4] + 4.95                          # "up to thirty pounds"
T_TAPE0, T_TAPE1 = B[5] + 2.05, B[5] + 2.85    # "seven feet long"
T_TIP0, T_TIPL = B[5] + 3.0, B[5] + 3.45       # the giant tips onto the long scale; "almost fifteen pounds"
T_CARRY0, T_CARRY1 = B[6] + 0.2, B[6] + 1.0    # "only carried in parades": it flies into the guard's hands
T_MARCH = B[6] + 1.0
T_CONF = B[6] + 1.45                           # "to show off": confetti
T_PSTAMP = B[6] + 2.5                          # "too big to use in battle"
T_HANG = [B[7] + 0.75 + 0.16 * k for k in range(4)] + [B[7] + 1.45]   # "hang these parade swords"
T_WAR = B[7] + 2.0; T_STRIKE = B[7] + 3.0; T_FLIP = B[7] + 3.25       # "made for war"; "keeps the myth alive"
T_END = B[8] + 0.05; T_ENDL = B[8] + 0.33; T_POP = B[8] + 0.95       # the myth sword drops on the last scale; the needle spins off


def needle_v(t, evs):
    """spring needle: each event (t0, target) pulls the reading from where it was to the target, with an overshoot and a settle"""
    tp = None; v0 = vt = 0.0
    for t0, tgt in evs:
        if t < t0: break
        val = vt + (v0 - vt) * math.exp(-3.4 * (t0 - tp)) * math.cos(9.0 * (t0 - tp)) if tp is not None else 0.0
        tp, v0, vt = t0, val, tgt
    if tp is None: return 0.0
    d = t - tp; return max(-1.2, vt + (v0 - vt) * math.exp(-3.4 * d) * math.cos(9.0 * d))


EV1 = [(T_HIT, 40.0), (T_YANK + 0.1, 0.0), (T_ARM, 3.0)]
EV2 = [(T_TWO, 9.5)]
EV3 = [(T_TIPL, 14.7), (T_CARRY0 + 0.1, 0.0)]

M_GLINT = emis('glintm', (1.0, 0.95, 0.8), 25.0)
def glint(name):
    vs = [(0, 0, 0)]; fs = []
    for i in range(8):
        a = math.pi / 4 * i; r_ = 0.07 if i % 2 == 0 else 0.012; vs.append((r_ * math.cos(a), 0, r_ * math.sin(a)))
    for i in range(8): fs.append((0, 1 + i, 1 + (i + 1) % 8))
    o = mesh(name, vs, fs, M_GLINT, None, smooth_=False, loc=(0, 0, -50)); o.scale = (0.0,) * 3; return o
GLS_O = [glint(f'gl{k}') for k in range(3)]
GEM_W = MYTH_P + Vector((-0.042, 0.015 - 0.06, 0.07))
GLS = [(0, T_HIT + 0.02, GEM_W, 1.1), (1, T_ARM + 0.05, ARM_P + Vector((0.3, -0.02, 0.01)), 0.8), (2, T_TWO + 0.05, TWO_P + Vector((0.45, -0.02, 0.01)), 0.8),
       (0, B[3] + 1.2, PEG + Vector((-0.12 - 0.022 - 0.1 - 0.025, -0.03, 0.0)), 0.8),
       (1, B[5] + 0.95, Vector((GX, GY - 0.04, TAPE_Z0 + 1.2)), 1.1), (2, B[5] + 1.3, Vector((GX, GY - 0.04, TAPE_Z0 + G_H - 0.05)), 1.0),
       (0, T_TIPL + 0.05, G_FLAT + Vector((0.6, -0.04, 0.01)), 1.0), (1, T_WAR, Vector((WDX, 5.2, 2.4)), 1.0), (2, T_WAR + 0.35, Vector((WDX + 0.32, 5.21, 1.3)), 0.8),
       (0, T_ENDL + 0.03, MYTH_P2 + Vector((-0.042, 0.015 - 0.06, 0.07)), 1.1)]

# confetti for the parade
GA = random.Random(23); M_CONF = [mat(f'conf{k}', c, 0.5) for k, c in enumerate(((0.7, 0.05, 0.04), (0.85, 0.62, 0.08), (0.9, 0.88, 0.8), (0.85, 0.65, 0.25)))]
CONF = []
for k in range(80):
    sz = GA.uniform(0.018, 0.03); o = mesh(f'cf{k}', [(-sz, 0, -sz * 0.6), (sz, 0, -sz * 0.6), (sz, 0, sz * 0.6), (-sz, 0, sz * 0.6)], [(0, 1, 2, 3)], M_CONF[k % 4], None, smooth_=False)
    o.modifiers.new('sd', 'SOLIDIFY').thickness = 0.001
    CONF.append((o, GA.uniform(-1.3, 1.3), GA.uniform(2.9, 3.6), GA.uniform(0.0, 0.35), GA.uniform(0.7, 1.2), GA.uniform(0, 6.3), GA.uniform(3.6, 4.1)))

ND4_REST = ND4.location.copy()
