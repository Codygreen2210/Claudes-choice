# ================================================================ moving bits: event times (each on its word), glints
T_RISE0, T_RISE1 = -0.35, 0.5                  # the necklace rises in its case (frame 0 is mid-rise)
T_FLICK0, T_FLICK1 = 2.35, 3.15                # "bad luck": the lights flicker
T_CRACK = 2.6; T_PLQ = 2.95                    # the glass cracks; the plaque drops crooked
T_ROUGH = B[1] + 0.95                          # "bought it": the rough stone lands on the cushion
T_BAN = B[1] + 2.4; T_CROWN = B[1] + 2.75      # "King Louis": the banner unrolls, a crown lands
T_WHEEL = B[1] + 3.55; T_CUT = B[1] + 4.6      # "had it cut": the wheel spins up, sparks; "the French Blue": the stone becomes the cut gem
T_YEAR2 = B[2] + 0.2; T_LID = B[2] + 1.2       # "1792"; "thieves": the lid flips open
T_STAMP2 = B[2] + 1.65                         # "stole": STOLEN stamp
T_YANK = [B[2] + 1.55, B[2] + 1.8, B[2] + 2.05, B[2] + 2.4]   # the jewels are snatched up one by one (crown on "crown")
T_VANISH = B[2] + 3.9                          # "vanished": the French Blue is gone in a sparkle
T_HOPE3 = B[3] + 1.45                          # "blue diamond": the smaller stone pops up in London
T_SCAN0, T_FIT = B[3] + 3.2, B[3] + 4.35       # "scientists": the French Blue's outline comes down; "cut from": it fits round it
T_CHECK = B[3] + 4.85                          # "stolen one": a green check
T_BOOK0, T_BOOK1 = B[4] + 0.55, B[4] + 1.1     # "banker": the catalog opens
T_LET = B[4] + 1.95; T_SUB4 = B[4] + 2.5      # "Hope": H-O-P-E drop in
T_NEWS = [B[5] + 0.12, B[5] + 0.36, B[5] + 0.6]   # "the curse": the scare papers slap onto the board
T_STAMP5 = B[5] + 1.2                          # "made up"
T_SOLD = B[5] + 5.3; T_COIN = B[5] + 5.8       # "sell it": SOLD tag; "rich buyer": coins
T_PKG = B[6] + 0.4                             # "twist": the plain package thuds onto the table
T_YEAR6 = B[6] + 1.05; T_LABEL = B[6] + 3.3; T_FRAG = B[6] + 4.75
T_STAMPS = [B[7] + 0.15 + 0.12 * k for k in range(6)]          # "postage": stamps slap on
T_TAG6 = B[7] + 1.0                            # "two dollars and forty-four cents"
T_SHAKE0, T_SHAKE1 = B[7] + 3.7, B[7] + 4.35   # "didn't believe": the mailman shakes his head
T_CURSE6 = B[7] + 4.4                          # "curse": the CURSE sign falls flat
T_FLY0, T_FLY1 = B[7] + 4.55, B[8] + 0.2       # the package flies to the last case
T_BURST = B[8] + 0.4; T_RISE8 = B[8] + 0.95    # it bursts open; the necklace rises
T_DIM0, T_DIM1 = B[8] + 1.15, B[8] + 1.45      # "ultraviolet": the room goes dark
T_UV = B[8] + 1.5; T_GLOW1 = B[8] + 2.2; T_COAL = B[8] + 2.95
T_UVOFF = B[9] + 0.2; T_LUP = B[9] + 0.6       # "follow": the lamp goes off, the lights come back, the red glow lingers and fades

M_GLINT = emis('glintm', (1.0, 0.97, 0.9), 25.0)
def glint(name):
    vs = [(0, 0, 0)]; fs = []
    for i in range(8):
        a = math.pi / 4 * i; r_ = 0.07 if i % 2 == 0 else 0.012; vs.append((r_ * math.cos(a), 0, r_ * math.sin(a)))
    for i in range(8): fs.append((0, 1 + i, 1 + (i + 1) % 8))
    o = mesh(name, vs, fs, M_GLINT, None, smooth_=False, loc=(0, 0, -50)); o.scale = (0.0,) * 3; return o
GLS_O = [glint(f'gl{k}') for k in range(3)]
bpy.context.view_layer.update()
def wpos(o, off=(0, 0, 0)): return o.matrix_world @ Vector(off)
HOPE0_W = wpos(HOPE0) + Vector((0, -0.03, 0.01)); HOPE8_W = wpos(HOPE8) + Vector((0, -0.03, 0.01))
GLS = [(0, T_RISE1 + 0.05, HOPE0_W, 0.9), (1, 1.6, HOPE0_W + Vector((0.12, 0, 0.36)), 0.6),
       (2, T_CUT + 0.05, FB1_REST + Vector((0.0, -0.05, 0.03)), 1.0), (0, T_CROWN + 0.05, CROWN1_REST + Vector((0.05, -0.1, 0.12)), 0.7),
       (1, T_HOPE3 + 0.05, HOPE3_REST + Vector((0.01, -0.04, 0.03)), 0.8), (2, T_CHECK + 0.05, HOPE3_REST + Vector((-0.02, -0.04, 0.03)), 0.9),
       (0, T_SUB4 + 0.05, Vector((X4 + 0.32 + 0.45, 5.33, 2.4)), 0.8), (1, T_SOLD - 0.2, wpos(HOPE5) + Vector((0, -0.03, 0.01)), 0.8),
       (2, T_RISE8 + 0.05, HOPE8_W, 0.9), (0, T_LUP + 0.3, HOPE8_W + Vector((0.1, 0, 0.3)), 0.7), (1, TOTAL - 0.8, HOPE8_W, 0.9)]
