# ================================================================ moving bits: event times (each pinned to its word; see events.py / events.json), glints
EV = json.load(open(os.path.join(HERE, 'events.json')))
T_RISE0, T_RISE1 = EV['RISE0'], EV['RISE1']                   # the necklace rises in its case (frame 0 is mid-rise)
T_FLICK0, T_FLICK1, T_CRACK, T_PLQ = EV['FLICK0'], EV['FLICK1'], EV['CRACK'], EV['PLQ']   # "bad luck": flicker, crack, plaque drops
T_ROUGH, T_BAN, T_CROWN, T_WHEEL, T_CUT = EV['ROUGH'], EV['BAN'], EV['CROWN'], EV['WHEEL'], EV['CUT']
T_YEAR2, T_LID, T_STAMP2, T_YANK, T_VANISH = EV['YEAR2'], EV['LID'], EV['STAMP2'], EV['YANK'], EV['VANISH']
T_YEARK, T_KCROWN, T_QCROWN = EV['YEAR3K'], EV['KCROWN'], EV['QCROWN']        # "lost his head": the king's crown tumbles; "queen": hers
T_HOPE3, T_SCAN0, T_FIT, T_CHECK = EV['HOPE3'], EV['SCAN0'], EV['FIT'], EV['CHECK']
T_BOOK0, T_BOOK1, T_LET, T_SUB4 = EV['BOOK0'], EV['BOOK1'], EV['LET'], EV['SUB4']
T_SOLD, T_COIN, T_SCARY = EV['SOLD'], EV['COIN'], EV['SCARY']                  # Cartier: SOLD, coins; "scary stories": IT'S CURSED!
T_GLOOM, T_SON, T_APART, T_PAPER7 = EV['GLOOM'], EV['SON'], EV['APART'], EV['PAPER7']   # the McLeans: dim, photo falls, photo splits, SOLD
T_NEWS, T_STAMP5, T_WOLF, T_LIVED = EV['NEWS'], EV['STAMP8'], EV['WOLF'], EV['LIVED']   # scare papers, MADE UP, the wolves paper, LIVED TO 84
T_PKG, T_YEAR6, T_LABEL, T_FRAG = EV['PKG'], EV['YEAR6'], EV['LABEL'], EV['FRAG']
T_STAMPS, T_TAG6 = EV['STAMPS'], EV['TAG6']
T_CRUTCH, T_WIFE, T_FIRE = EV['CRUTCH'], EV['WIFE'], EV['FIRE']               # the mailman's bad year
T_SHAKE0, T_SHAKE1, T_CURSE6 = EV['SHAKE0'], EV['SHAKE1'], EV['CURSE6']
T_FLY0, T_FLY1, T_BURST, T_RISE8 = EV['FLY0'], EV['FLY1'], EV['BURST'], EV['RISE8']
T_DIM0, T_DIM1, T_UV, T_GLOW1, T_COAL = EV['DIM0'], EV['DIM1'], EV['UV'], EV['GLOW1'], EV['COAL']
T_UVOFF, T_LUP = EV['UVOFF'], EV['LUP']

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
