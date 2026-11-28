# ================================================================ moving bits: event times (each pinned to its word; see events.py / events.json)
EV = json.load(open(os.path.join(HERE, 'events.json')))
T_STEAM0, T_FLICK0, T_FLICK1, T_PLQ = EV['STEAM0'], EV['FLICK0'], EV['FLICK1'], EV['PLQ']
T_YEAR1, T_BUST, T_PIN = EV['YEAR1'], EV['BUST'], EV['PIN']
T_SCROLL, T_MODEL, T_HOLLOW, T_DOOR = EV['SCROLL'], EV['MODEL'], EV['HOLLOW'], EV['DOOR']
T_SHUT, T_LOCK, T_FIRE = EV['SHUT'], EV['LOCK'], EV['FIRE']
T_PIPES, T_RINGS, T_MOO = EV['PIPES'], EV['RINGS'], EV['MOO']
T_DISG, T_INV, T_TEST = EV['DISG'], EV['INV'], EV['TEST']
T_ROSE, T_KINGIN, T_SHUT6 = EV['ROSE'], EV['KINGIN'], EV['SHUT6']
T_QMARK, T_BOOK, T_TL0, T_TL1, T_MADEUP = EV['QMARK'], EV['BOOK'], EV['TL0'], EV['TL1'], EV['MADEUP']
T_REAL, T_CARRY, T_CARTH = EV['REAL'], EV['CARRY'], EV['CARTH']
T_YEAR10, T_HELM, T_BACK = EV['YEAR10'], EV['HELM'], EV['BACK']
T_WRITER, T_REMIND = EV['WRITER'], EV['REMIND']
T_STATUE, T_RIVER = EV['STATUE'], EV['RIVER']
T_LOST, T_QM13 = EV['LOST'], EV['QM13']
bpy.context.view_layer.update()
def wpos(o, off=(0, 0, 0)): return o.matrix_world @ Vector(off)
# the little board bull's door, in world space: the spot in front of it on the board, and the door's middle
DOOR3_FRONT = wpos(TOK3, (-0.06, -0.62, 0.0)); DOOR3_MID = wpos(TOK3, (-0.06, -0.2, 0.63))
INV3_REST = INV3.location.copy(); KING3_REST = KING3.location.copy()
