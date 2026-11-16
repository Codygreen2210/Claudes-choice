# ================================================================ physics: Bullet, baked once into sim.npz (positions, rotations, progress)
SIM_PRE = 14                                    # sim frames before video frame 0 (the gate is already dropping on frame one)
def piece_len(pc):
    if pc['kind'] == 'chan': return float(np.sum(np.linalg.norm(np.diff(pc['pts'], axis=0), axis=1)))
    if pc['kind'] == 'funnel': return 2.0 * pc['Rf']
    return pc['Lb']
PLEN = [piece_len(pc) for pc in PIECES]; PSTART = np.concatenate([[0.0], np.cumsum(PLEN)])[:-1]
def piece_frac(pc, p):
    """fraction 0..1 through this piece, or None if the marble isn't in it"""
    if pc['kind'] == 'chan':
        d = np.linalg.norm(pc['pts'] - p, axis=1); i = int(np.argmin(d))
        if d[i] > pc['rad']: return None
        return i / (len(pc['pts']) - 1)
    if pc['kind'] == 'funnel':
        if not (pc['z1'] < p[2] < pc['z0']): return None
        r = math.hypot(p[0] - pc['c'][0], p[1] - pc['c'][1])
        if r > pc['Rf'] + 0.1: return None
        if p[2] < pc['c'][2] - 1.0: return 0.98
        return clamp((pc['Rf'] - r) / (pc['Rf'] - pc['rh']), 0, 0.97)
    q = p - pc['top']; u = float(np.dot(q, pc['D'])); v = float(np.dot(q, pc['Sd']))
    nrm = np.cross(pc['Sd'], pc['D']); n = abs(float(np.dot(q, nrm)))
    if -0.9 < u < pc['Lb'] + 0.4 and abs(v) < pc['hw'] and n < 0.5: return clamp(u / pc['Lb'], 0, 1)
    return None

def run_sim(seconds):
    bpy.ops.rigidbody.world_add(); rw = S.rigidbody_world
    rw.substeps_per_frame = 24; rw.solver_iterations = 30; rw.time_scale = 1.0
    nF = int(seconds * FPS) + SIM_PRE; rw.point_cache.frame_start = 1; rw.point_cache.frame_end = nF + 2
    S.frame_start = 1; S.frame_end = nF + 2
    rbc = bpy.data.collections.new('RigidBodyWorld'); rw.collection = rbc
    def add_rb(o, kind):
        rbc.objects.link(o) if o.name not in rbc.objects else None
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.rigidbody.object_add(type=kind); o.select_set(False); return o.rigid_body
    for o in PHYS:
        rb = add_rb(o, 'PASSIVE'); rb.collision_shape = 'MESH'; rb.mesh_source = 'BASE'; rb.friction = 0.35; rb.restitution = 0.35
        rb.collision_margin = 0.002
    # start gate: a bar across the ramp that drops away at sim frame 6
    st = LMK['start']; g0 = st[int(len(st) * 0.25)]
    gate = box('gate', (0.03, 1.1, 0.25), tuple(g0['p'] + g0['up'] * 0.12), M['wall']); gate.rotation_mode = 'QUATERNION'
    gate.rotation_quaternion = Matrix((g0['T'], g0['side'], g0['up'])).transposed().to_quaternion()
    rb = add_rb(gate, 'PASSIVE'); rb.kinematic = True; rb.collision_shape = 'BOX'
    gate.keyframe_insert('location', frame=6); gate.location = gate.location + g0['up'] * -0.35; gate.keyframe_insert('location', frame=10)
    GATE[0] = gate
    rng = random.Random(a.seed); order = list(range(NM)); rng.shuffle(order)
    s0 = st[int(len(st) * 0.12)]
    for slot, i in enumerate(order):
        mo = MARB[i]; mo.location = s0['p'] + s0['side'] * ((slot - 3.5) * 0.105) + s0['up'] * (MR + 0.004) + s0['T'] * rng.uniform(-0.02, 0.02)
        rb = add_rb(mo, 'ACTIVE'); rb.collision_shape = 'SPHERE'; rb.mass = 0.05; rb.friction = 0.4; rb.restitution = 0.45
        rb.linear_damping = 0.30 + rng.uniform(-0.01, 0.01); rb.angular_damping = 0.15; rb.use_deactivation = False; rb.collision_margin = 0.001
        rb.use_margin = True
    POS = np.zeros((nF, NM, 3), np.float32); QUA = np.zeros((nF, NM, 4), np.float32); PRG = np.zeros((nF, NM), np.float32)
    cur = [0] * NM; best = [0.0] * NM; done = [None] * NM; total = float(PSTART[-1] + PLEN[-1])
    import time; t0 = time.time()
    for f in range(nF):
        S.frame_set(f + 1)
        for i, mo in enumerate(MARB):
            mw = mo.matrix_world; p = np.array(mw.translation); POS[f, i] = p; QUA[f, i] = tuple(mw.to_quaternion())
            got = None
            for j in range(cur[i], min(cur[i] + 3, len(PIECES))):
                fr = piece_frac(PIECES[j], p)
                if fr is not None: got = (j, fr)
            if got: cur[i] = got[0]; best[i] = max(best[i], PSTART[got[0]] + got[1] * PLEN[got[0]])
            PRG[f, i] = best[i]
            if done[i] is None and PIECES[cur[i]]['name'] == 'finish' and np.linalg.norm(p - np.array(tuple(LMK['finish_line']['p']))) < 0.6 \
               and np.dot(p - np.array(tuple(LMK['finish_line']['p'])), np.array(tuple(LMK['finish_line']['T']))) > 0:
                done[i] = f
        if f % 150 == 0:
            lead = int(np.argmax(PRG[f])); print(f'sim {f}/{nF}  {time.time() - t0:.0f}s  lead {COLS[lead][0]} {PRG[f, lead]:.1f}/{total:.0f} m  '
                                               f'pieces {[PIECES[c]["name"] for c in cur]}', flush=True)
        if all(d is not None for d in done) and f > max(done) + 6 * FPS: POS, QUA, PRG = POS[:f + 1], QUA[:f + 1], PRG[:f + 1]; break
        if any(p_[2] < LMK['floor_z'] + 0.3 for p_ in POS[f]):
            lost = [COLS[i][0] for i in range(NM) if POS[f, i, 2] < LMK['floor_z'] + 0.3]; print('LOST', lost, 'frame', f, [PIECES[c]['name'] for c in cur]);
            POS, QUA, PRG = POS[:f + 1], QUA[:f + 1], PRG[:f + 1]; break
    fin = np.array([d if d is not None else -1 for d in done])
    np.savez_compressed(os.path.join(HERE, os.environ.get('SIMOUT', 'sim.npz')), pos=POS, quat=QUA, prog=PRG, fin=fin, pre=SIM_PRE, total=total)
    print('finish frames', {COLS[i][0]: (int(d) - SIM_PRE) / FPS if d is not None else None for i, d in enumerate(done)})
GATE = [None]
