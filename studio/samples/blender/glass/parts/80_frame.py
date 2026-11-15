
# ================================================================ timing and the camera (one take: rests on each idea, moves between them)
def clamp(x, a_, b_): return max(a_, min(b_, x))
def ease_out(x): x = clamp(x, 0, 1); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x, 0, 1); return x * x * (3 - 2 * x)
def win(t, a_, b_, f=0.25): return ease_io((t - a_) / f) * (1 - ease_io((t - b_) / f))
V = TM['voice']; Zf = Z0
# keys: (time, position, target, lens, f-stop)
K = [
    (0.00, (1.05, -1.25, Zf + 1.05), (0.20, -0.62, Zf + 0.02), 24, 8),        # frame one: low in the box, the crack shooting out from his feet
    (1.90, (1.10, -1.25, Zf + 1.20), (0.15, -0.60, Zf + 0.20), 24, 8),        # rest, a slow rise
    (3.70, (9.0, -5.0, Zf + 1.8), (0.00, -1.0, Zf - 3.5), 24, 8),        # outside: him in the glass box on the tower, Chicago far below
    (5.70, (9.5, -5.4, Zf + 1.5), (0.00, -1.0, Zf - 3.9), 24, 8),        # rest
    (6.70, (-0.75, -1.10, Zf + 1.60), (-0.45, -2.40, 0.0), 24, 5),            # in the box beside him, straight down through the cracking floor
    (8.80, (-0.72, -1.05, Zf + 1.25), (-0.45, -2.40, 0.0), 24, 5),            # rest, pushing down
    (9.90, (1.80, -1.62, Zf + 0.10), (1.40, -1.22, Zf - 0.04), 50, 11),       # the slab's edge: the layers
    (13.30, (1.82, -1.64, Zf + 0.10), (1.40, -1.22, Zf - 0.04), 50, 11),      # rest (layers part and press back)
    (18.40, (1.86, -1.68, Zf + 0.11), (1.40, -1.22, Zf - 0.04), 50, 11),    # rest through the heat and the air
    (19.70, (1.40, -1.22, Zf + 0.20), (0.00, -0.55, Zf), 28, 8),              # up to the top surface: the coating, the shoes
    (23.30, (1.30, -1.18, Zf + 0.24), (-0.10, -0.55, Zf), 28, 8),             # rest
    (24.30, (0.55, -1.20, Zf + 0.36), (-0.55, -0.46, Zf), 30, 8),             # the ball comes down
    (26.30, (0.45, -1.15, Zf + 0.30), (-0.55, -0.46, Zf), 30, 8),             # rest on the web
    (27.40, (-1.80, -0.80, Zf + 0.07), (-1.30, -0.48, Zf - 0.02), 45, 11),  # at the edge: only the top layer cracked
    (28.90, (-1.82, -0.82, Zf + 0.07), (-1.30, -0.48, Zf - 0.02), 45, 11),  # rest
    (29.65, (-1.20, 0.90, Zf + 2.35), (0.00, -0.70, Zf + 0.40), 24, 8),        # up over everyone's heads (never through a person)
    (30.40, (0.10, 2.60, Zf + 1.55), (0.00, -0.70, Zf + 0.55), 24, 8),        # inside the Skydeck behind the group (backs to us)
    (34.40, (0.05, 2.30, Zf + 1.45), (0.00, -0.70, Zf + 0.40), 24, 8),        # rest while it splinters
    (35.60, (0.35, -0.95, Zf - 1.30), (0.20, -0.55, Zf + 0.20), 22, 8),       # under the box, looking up through the floor
    (38.40, (0.30, -0.90, Zf - 1.20), (0.15, -0.55, Zf + 0.20), 22, 8),       # rest: cracked top, glass whole
    (39.40, (0.90, 0.80, Zf + 1.25), (0.00, -0.70, Zf), 28, 8),               # the empty cracked floor
    (41.80, (0.80, 0.70, Zf + 1.20), (0.00, -0.70, Zf), 28, 8),               # rest
    (43.20, (6.50, -15.0, Zf + 4.0), (0.00, -6.50, Zf + 0.5), 30, 8),         # the shelf and the cars
    (44.90, (9.00, -20.0, Zf + 3.0), (0.00, -7.00, Zf + 0.5), 30, 8),         # rest
    (46.60, (150.0, -450.0, 200.0), (0.00, -6.00, 215.0), 30, 8),      # way out: the shelf on the tower, the street far below
    (47.60, (156.0, -462.0, 196.0), (0.00, -6.00, 215.0), 30, 8),      # rest
    (END, (1.05, -1.25, Zf + 1.05), (0.20, -0.62, Zf + 0.02), 24, 8),         # back to frame one (loop)
]
def herm(ts, vs, t):
    n = len(ts); i = max(0, min(n - 2, next((j for j in range(n - 1) if ts[j + 1] >= t), n - 2)))
    t0, t1 = ts[i], ts[i + 1]; u = clamp((t - t0) / (t1 - t0), 0, 1)
    def tan(j):
        if j in REST: return vs[j] * 0                                     # zero speed at a rest key: it eases in and out, no overshoot
        a_, b_ = max(0, j - 1), min(n - 1, j + 1)
        return (vs[b_] - vs[a_]) / (ts[b_] - ts[a_]) * (t1 - t0)
    m0, m1 = tan(i), tan(i + 1); u2, u3 = u * u, u * u * u
    return vs[i] * (2 * u3 - 3 * u2 + 1) + m0 * (u3 - 2 * u2 + u) + vs[i + 1] * (-2 * u3 + 3 * u2) + m1 * (u3 - u2)
REST = set(range(len(K)))                                           # every key eases in and out: the camera arrives and rests
def cam_at(t):
    ts = [k[0] for k in K]; P = [Vector(k[1]) for k in K]; Q = [Vector(k[2]) for k in K]
    p = herm(ts, P, t); q = herm(ts, Q, t); ln = herm(ts, [Vector((k[3], 0, 0)) for k in K], t).x; fs = herm(ts, [Vector((k[4], 0, 0)) for k in K], t).x
    sh = shake(t, 0.004, 5.0, 0.6) * (1.0 if p.z > Zf - 2 else 25.0)              # a hand-held breath (bigger when far out)
    if T_HIT < t < T_HIT + 0.5: sh += shake(t, 0.012 * (1 - (t - T_HIT) / 0.5), 2.0, 14.0)
    if T_SPLINTER < t < T_SPLINTER + 0.6: sh += shake(t, 0.02 * (1 - (t - T_SPLINTER) / 0.6), 3.0, 12.0)
    look_down = 6.2 < t < 9.3
    return p + sh, q + sh * 0.5, ln, fs, (Vector((0, 1, 0)) if look_down else None)

# ---- what everything does at time t
def state(t):
    t = clamp(t, 0.0, END - 1e-4)
    city_at(t)
    # the edge trims would sit between the camera and the slab in the cross-section shots: out of the way then
    for o in TRIMS + WALLS: o.hide_render = (9.3 < t < 19.2) or (26.8 < t < 29.6)
    # cracks: the opening crack at his feet (frame one), cleared once we leave him; the hit's web; the 2019 splinter
    COAT['w0'] = 0.0 if t > 9.0 else 0.18 + 0.55 * ease_out(t / 1.4) + 0.3 * ease_io((t - 6.6) / 1.6)   # already running at frame one
    COAT['w1'] = 0.0 if t < T_HIT else 0.06 + 0.42 * ease_out((t - T_HIT) / 0.25)
    COAT['cz'] = 0.0 if t < T_SPLINTER else 2.6 * ease_out((t - T_SPLINTER) / 1.3)
    if t > 46.8: COAT['w1'] = COAT['cz'] = 0.0                                  # far away: the floor is whole again for the loop
    # the layers: the coating lifts away, the three glass layers part (exploded) and press back; the coating returns on "coating"
    layered = 9.3 < t < 20.4 or 26.8 < t < 29.6                         # separate layers only in the close-ups
    SLAB.hide_render = layered
    for o, _ in LAYERS[1:]: o.hide_render = not layered
    part = win(t, T_LAYERS - 0.6, 12.6, 0.7)
    coat_off = win(t, 9.4, T_COAT, 0.6)
    for k_, (o, z_) in enumerate(LAYERS):
        o.location.z = z_ - 0.028 * part * k_ + (0.06 * coat_off if k_ == 0 else 0.0)
        o.location.x = (1.8 * coat_off if k_ == 0 else 0.0)
        if k_ == 0: o.hide_render = coat_off > 0.97
    # tempering: glow then the cold blast
    heat = ease_io((t - (T_HEAT - 0.2)) / 1.0) * (1 - ease_io((t - (T_BLAST + 0.3)) / 1.4))
    for o, _ in LAYERS[1:]: o['heat'] = heat
    SLAB['heat'] = heat
    for o in AIR: o['a'] = win(t, T_BLAST - 0.1, T_BLAST + 2.3, 0.3); o['tw'] = t; o.hide_render = o['a'] < 0.01
    # "millions of shoes": a time-lapse crowd hurrying in and out over the floor, scuffs flashing on the coating and fading
    cr_on = T_COAT + 0.3 < t < 23.7
    for i_, p in enumerate(CROWD):
        show_fig(p, cr_on)
        if not cr_on: continue
        ph = ((t - T_COAT) * 0.9 + i_ * 0.37) % 1.0; y_ = 1.4 - 2.4 * math.sin(ph * math.pi)        # out to the glass and back in
        p['root'].location = (-1.1 + 0.42 * i_, y_, Z0); face(p, -math.pi / 2 if ph < 0.5 else math.pi / 2); pose(p, 'walk', t * 2.5)
    COAT['sc'] = win(t, T_SHOES - 0.3, 23.5, 0.4) * (0.6 + 0.4 * math.sin(t * 9))
    for i_, sh in enumerate(STEPS):
        show_tree(sh, False); continue
        tl = T_SHOES - 0.4 + 0.16 * i_; u = t - tl
        on = -0.35 < u < 0.75; show_tree(sh, on)
        sh.location.z = Zf + 0.002 + (0.18 * ease_io(-u / 0.35) if u < 0 else 0.0) + (0.22 * ease_io((u - 0.45) / 0.3) if u > 0.45 else 0.0)
    # the ball: dropped from 1.2 m, hits at T_HIT, one small hop, rolls off toward the room
    td = math.sqrt(2 * 1.2 / 9.81); show_tree(BALL, T_HIT - td - 0.05 < t < 26.8)
    if t < T_HIT: bz = 1.2 - 0.5 * 9.81 * max(0.0, t - (T_HIT - td)) ** 2
    else: u = t - T_HIT; bz = max(0.0, 0.9 * u - 0.5 * 9.81 * u * u)
    BALL.location = (-0.55 + 0.12 * max(0.0, t - T_HIT - 0.2), -0.455 + 0.08 * max(0.0, t - T_HIT - 0.2), Zf + 0.109 + bz)
    BALL.rotation_euler = (0.0, 1.1 * max(0.0, t - T_HIT - 0.2), 0.0)
    # people: him from frame one until we go to the layers, back for the loop; the 2019 group for the splinter
    show_fig(HIM, t < 9.2 or t > 47.0); pose(HIM, 'look', t)
    grp_on = 29.6 < t < 39.2
    for i_, p in enumerate(GROUP + [HIM]):
        if p is HIM and not grp_on: continue
        if p is not HIM: show_fig(p, grp_on)
        if not grp_on: continue
        base = p['root']['home'] if 'home' in p['root'] else None
        if base is None: p['root']['home'] = tuple(p['root'].location); base = p['root']['home']
        back = ease_io((t - (T_NEVER - 1.8 + 0.25 * i_)) / 2.2)
        arrive = ease_io((t - 29.6 - 0.15 * i_) / 1.3)                     # they walk out from the Skydeck (behind the camera) onto the glass
        p['root'].location = (base[0], base[1] + 1.9 * (1 - arrive) + 2.4 * back, base[2])
        if arrive < 1.0: face(p, -math.pi / 2); pose(p, 'walk', t)
        elif t < T_SPLINTER + 0.15: face(p, -math.pi / 2); pose(p, 'look', t)
        elif back <= 0.0: pose(p, 'brace', t)
        elif back < 1.0: face(p, math.pi / 2); pose(p, 'walk', t)
        else: pose(p, 'stand', t)
    if grp_on: show_fig(HIM, True); HIM['root'].location = (0.25, HIM['root'].location.y, Zf)
    else: HIM['root'].location = (0.25, -0.62, Zf); face(HIM, -math.pi / 2)
    # the payoff: the floor stretches into a long shelf, two and a half cars drop onto it
    sh_on = T_CARS - 0.9 < t < 47.4; SHELF.hide_render = not sh_on
    SHELF.scale.y = max(0.02, ease_out((t - (T_CARS - 0.9)) / 0.7)); SHELF.location.y = -0.1 - 7.0 * SHELF.scale.y
    for i_, (c, (cx, cy)) in enumerate(zip(CARS, CAR_REST)):
        tl = T_CARS + 0.35 * i_; on = tl - 0.45 < t < 47.4; show_tree(c, on)
        u = t - tl; z = 2.4 * ease_io(-u / 0.45) if u < 0 else 0.03 * math.exp(-u * 6) * math.sin(u * 30)
        c.location = (cx, cy, Zf + z); c.rotation_euler = (0, 0, R(4 - 8 * h1(i_)))
    # Skydeck light only while it matters (it can glow through the glass at night shots; it is day, keep it gentle)
    IN_LT.data.energy = 400

def frame(f):
    t = f / FPS; d = 0.25 / FPS
    CAM.animation_data_clear(); CAM.data.animation_data_clear()
    if t > d and t < END - d:
        for kf, tt_ in ((f - 0.25, t - d), (f + 0.25, t + d)):
            cp, ct, ln, fs, up = cam_at(tt_); look(cp, ct, ln, fs, up=up); CAM.keyframe_insert('location', frame=kf); CAM.keyframe_insert('rotation_quaternion', frame=kf)
    S.frame_set(f); state(t)
    cp, ct, ln, fs, up = cam_at(t)
    if not (t > d and t < END - d): look(cp, ct, ln, fs, up=up)
if os.environ.get('CHKCAM'):                                             # debug: a fixed camera for checks  "x,y,z,tx,ty,tz,lens"
    _frame1 = frame; _cks = [[float(v) for v in c.split(',')] for c in os.environ['CHKCAM'].split(';')]
    def frame(f):
        _frame1(f); CAM.animation_data_clear(); c = _cks[int(os.environ.get('CHKI', '0'))]
        look(Vector(c[:3]), Vector(c[3:6]), c[6], 8.0)
