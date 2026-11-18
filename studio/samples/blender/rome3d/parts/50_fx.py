# ================================================================ effects: rain round the camera, the bucket's pour, steam off the slaking lime, the drips
# under the test blocks, and the inside-the-concrete set (cut face with aggregate and white lime lumps, the crack, water, crystals)
WORKER = Man('worker', (0.62, 0.42, 0.30))
# ---- rain: thin streaks in a box that follows the camera
RAIN_N = 2600; RAIN_BOX = (7.0, 7.0, 6.0); RAIN_V = 7.5
RAINM = mat('rain', (0.85, 0.9, 0.95), 0.15, alpha=0.32)
try: RAINM.surface_render_method = 'BLENDED'
except Exception: pass
_rr = random.Random(9)
RAIN_SEED = [(_rr.random(), _rr.random(), _rr.random(), 0.16 + 0.12 * _rr.random()) for _ in range(RAIN_N)]
_rv = []; _rf = []
for i in range(RAIN_N):
    b0 = len(_rv); _rv += [(0, 0, 0)] * 4; _rf.append((b0, b0 + 1, b0 + 2, b0 + 3))
RAIN = mesh('rain', _rv, _rf, RAINM, smooth_=False)
def set_rain(t, cam, on=1.0):
    co = []; cx, cy, cz = cam
    nshow = int(RAIN_N * on)
    for i, (a_, b_, c_, L_) in enumerate(RAIN_SEED):
        if i >= nshow: co.extend((cx, cy, cz - 50) * 4); continue
        x_ = cx + (a_ - 0.5) * RAIN_BOX[0]; y_ = cy + (b_ - 0.5) * RAIN_BOX[1]
        z_ = cz + (((c_ * RAIN_BOX[2] - RAIN_V * t) % RAIN_BOX[2]) - RAIN_BOX[2] / 2)
        if z_ < 0.0: z_ += RAIN_BOX[2]
        dx, dy = x_ - cx, y_ - cy; d_ = math.hypot(dx, dy) + 1e-6; px, py = -dy / d_ * 0.0012, dx / d_ * 0.0012
        tx, ty = 0.04 * L_, 0.02 * L_
        co.extend((x_ - px, y_ - py, z_, x_ + px, y_ + py, z_, x_ + px + tx, y_ + py + ty, z_ + L_, x_ - px + tx, y_ - py + ty, z_ + L_))
    RAIN.data.vertices.foreach_set('co', co); RAIN.data.update()
# ---- a stream of water (bucket pour, funnels)
class Stream:
    def __init__(self, name, n=20, seg=10):
        self.n = n; self.seg = seg; self.o = tube(name, [(0, 0, -i * 0.05) for i in range(n)], 0.02, WATERM, seg=seg, caps=True)
    def set(self, p0, v0, r0, t, zfloor, wob_amt=1.0):
        g = Vector((0, 0, -9.8)); pts = []
        tz = (v0.z + math.sqrt(max(v0.z ** 2 - 2 * g.z * (p0.z - zfloor), 0))) / -g.z
        for i in range(self.n):
            tau = tz * i / (self.n - 1); p = p0 + v0 * tau + 0.5 * g * tau * tau
            p += Vector((wob(t - tau, 9, i * 0.1), wob(t - tau, 9, 3 + i * 0.1), 0)) * 0.004 * wob_amt * (i / self.n); pts.append(p)
        co = []; T0 = (pts[1] - pts[0]).normalized(); up = Vector((1, 0, 0)) if abs(T0.x) < 0.9 else Vector((0, 1, 0)); Nn = T0.cross(up).normalized()
        for i, p in enumerate(pts):
            T = (pts[min(i + 1, self.n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
            rr = r0 * (1.0 - 0.4 * i / (self.n - 1)) * (1 + 0.12 * wob(t * 3 - i * 0.2, 7, i))
            for k in range(self.seg): co.extend(p + (Nn * math.cos(2 * math.pi * k / self.seg) + Bn * math.sin(2 * math.pi * k / self.seg)) * rr)
        self.o.data.vertices.foreach_set('co', co); self.o.data.update(); return pts[-1]
POUR = Stream('pour', 24, 12)
FSTREAM = [Stream(f'fstream{k}', 10, 8) for k in range(2)]
DRIPS = [[prim('uv_sphere', f'drip{k}_{j}', WATERM, radius=0.005, segments=10, ring_count=6) for j in range(4)] for k in range(2)]
for row in DRIPS:
    for d_ in row: d_.scale = (1, 1, 1.4)
WETTOP = [prim('cylinder', f'wettop{k}', WATERM, loc=TBLOCK[k]['top'] + Vector((0, 0, 0.002)), radius=TB_R * 0.9, depth=0.003, vertices=32) for k in range(2)]
BOWLW = [prim('cylinder', f'bowlwater{k}', WATERM, loc=TBLOCK[k]['bowl'] + Vector((0, 0, 0.012)), radius=0.075, depth=0.002, vertices=32) for k in range(2)]
# a bright wet trickle down each block's crack (it shrinks away on the healed one)
TTRICKLE = []
for k in range(2):
    rb = Ribbon(f'trickle{k}', 30, WATERM); TTRICKLE.append(rb)
# ---- steam off the slaking lime: soft volume puffs that rise, swell and thin out
STEAMM = bpy.data.materials.new('steam'); STEAMM.use_nodes = True; nt = STEAMM.node_tree; out_ = nt.nodes['Material Output']
for n in list(nt.nodes):
    if n.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n)
pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1)
gd = nt.nodes.new('ShaderNodeTexCoord')
# density: falls off from the puff's centre, broken up by noise, scaled by the object's 'dens'
vl = nt.nodes.new('ShaderNodeVectorMath'); vl.operation = 'LENGTH'; nt.links.new(gd.outputs['Object'], vl.inputs[0])
fall = math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, vl.outputs['Value']), 0.0)
nz = tnoise(nt, gd.outputs['Object'], 2.5, 4.0)
dn = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', fall, math_(nt, 'ADD', nz, -0.15)), objattr(nt, 'dens'))
nt.links.new(dn, pv.inputs['Density']); nt.links.new(pv.outputs[0], out_.inputs['Volume'])
STEAM = []
for k in range(26):
    o = prim('ico_sphere', f'steam{k}', STEAMM, subdivisions=2, radius=1.0); o['dens'] = 0.0; STEAM.append(o)

# ---- inside the concrete (about 100x): a cut face full of aggregate and white lime lumps, split by the crack
MICRO = Vector((0.0, -3000.0, 0.0))
CONCM = pbr('acg:Concrete048', 0.35, 'concface', 'Object', tint=(0.30, 0.26, 0.21), boxp=True)
noisy(CONCM, 1.2, 0.18, 0.1); noisy(CONCM, 26.0, 0.35, 0.1)
SLAB_W, SLAB_D = 26.0, 4.0
CR_N = 60
CR_PATH = [(x_, z_) for z_, x_ in jag((14.0, 0.0), (-14.0, 0.0), CR_N, 0.45, 5)]       # top to bottom, wandering in x
# force it through the big lime lump at the middle
CR_PATH = [(x_ * (0.25 + 0.75 * min(1.0, abs(z_) / 3.0)), z_) for x_, z_ in CR_PATH]
CR_W = [0.20 + 0.10 * h1(i + 3) for i in range(CR_N)]
def cr_x(z_):
    for i in range(CR_N - 1):
        (x0, z0), (x1, z1) = CR_PATH[i], CR_PATH[i + 1]
        if z1 <= z_ <= z0: k = (z0 - z_) / max(z0 - z1, 1e-6); return lerp(x0, x1, k), lerp(CR_W[i], CR_W[i + 1], k)
    return CR_PATH[-1][0], CR_W[-1]
def prism(name, z_hi, z_lo, y0, y1, wscale, m, n=CR_N):
    """the crack's shape between two heights, as a closed solid from y0 to y1 (a cutter, the water, the calcite fill)"""
    vs = []; fs = []
    zs = [lerp(z_hi, z_lo, i / (n - 1)) for i in range(n)]
    for z_ in zs:
        x_, w_ = cr_x(z_); w_ *= wscale
        for yy in (y0, y1): vs += [(MICRO.x + x_ - w_ / 2, MICRO.y + yy, MICRO.z + z_), (MICRO.x + x_ + w_ / 2, MICRO.y + yy, MICRO.z + z_)]
    for i in range(n - 1):
        a_ = i * 4; b_ = (i + 1) * 4
        fs += [(a_, a_ + 1, b_ + 1, b_), (a_ + 2, b_ + 2, b_ + 3, a_ + 3), (a_, b_, b_ + 2, a_ + 2), (a_ + 1, a_ + 3, b_ + 3, b_ + 1)]
    fs += [(0, 2, 3, 1), ((n - 1) * 4, (n - 1) * 4 + 1, (n - 1) * 4 + 3, (n - 1) * 4 + 2)]
    return mesh(name, vs, fs, m, smooth_=False)
GAPM = mat('gapwall', (0.11, 0.095, 0.08), 0.95); noisy(GAPM, 3.0, 0.3, 0.1)
GAP_D = 2.6
def build_slab():
    """the cut face as two halves with the crack between them: front quads, crack walls (dark), the crack's floor, back and sides"""
    zs = [lerp(13.0, -13.0, i / 80) for i in range(81)]; H = SLAB_W / 2; y0 = MICRO.y; y1 = MICRO.y + SLAB_D
    vs = []; fs = []; mi = []
    def v(x_, y_, z_): vs.append((MICRO.x + x_, y_, MICRO.z + z_)); return len(vs) - 1
    for side in (-1, 1):
        for i in range(80):
            za, zb = zs[i], zs[i + 1]; xa, wa = cr_x(za); xb, wb = cr_x(zb)
            ea, eb = xa + side * wa / 2, xb + side * wb / 2; oa = side * H
            # front: from the crack edge out to the slab edge
            q = [v(ea, y0, za), v(oa, y0, za), v(oa, y0, zb), v(eb, y0, zb)]
            fs.append(tuple(q) if side > 0 else tuple(reversed(q))); mi.append(0)
            # crack wall going in GAP_D
            q = [v(ea, y0, za), v(eb, y0, zb), v(eb, y0 + GAP_D, zb), v(ea, y0 + GAP_D, za)]
            fs.append(tuple(q) if side > 0 else tuple(reversed(q))); mi.append(1)
    for i in range(80):      # the floor of the crack
        za, zb = zs[i], zs[i + 1]; xa, wa = cr_x(za); xb, wb = cr_x(zb)
        q = [v(xa - wa / 2, y0 + GAP_D, za), v(xb - wb / 2, y0 + GAP_D, zb), v(xb + wb / 2, y0 + GAP_D, zb), v(xa + wa / 2, y0 + GAP_D, za)]
        fs.append(tuple(q)); mi.append(1)
    q = [v(-H, y1, -H), v(H, y1, -H), v(H, y1, H), v(-H, y1, H)]; fs.append(tuple(q)); mi.append(0)   # back
    me = bpy.data.meshes.new('slab'); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new('slab', me); S.collection.objects.link(o); o.data.materials.append(CONCM); o.data.materials.append(GAPM)
    for p_, m_ in zip(me.polygons, mi): p_.material_index = m_
    me.validate(); me.update(); return o
GAPM = mat('gapwall', (0.09, 0.08, 0.07), 0.95); noisy(GAPM, 3.0, 0.3, 0.1)
SLAB = build_slab()
def cut(o):
    """tear a lump in two along the crack: push each vertex to its side, drop the faces that straddle it"""
    bpy.context.view_layer.update(); bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world.copy(); Mi = M.inverted(); side = {}
    for v in bm.verts:
        w = M @ v.co; x_, w_ = cr_x(w.z - MICRO.z); sd = 1 if (w.x - MICRO.x) > x_ else -1; side[v.index] = sd
    kill = [f for f in bm.faces if len({side[v.index] for v in f.verts}) > 1]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    for v in bm.verts:
        w = M @ v.co; x_, w_ = cr_x(w.z - MICRO.z); dx = (w.x - MICRO.x) - x_
        if abs(dx) < w_ / 2: w.x = MICRO.x + x_ + (w_ / 2 if dx > 0 else -w_ / 2); v.co = Mi @ w
    bm.to_mesh(o.data); bm.free()
# aggregate (volcanic tuff and brick bits) and lime lumps sitting in the face; anything the crack crosses is cut too
LIMEC = mat('limeclast', (0.93, 0.92, 0.88), 0.85); noisy(LIMEC, 6.0, 0.08, 0.05)
AGGM = [mat('tuff', (0.42, 0.33, 0.25), 0.8), mat('brickbit', (0.55, 0.24, 0.14), 0.75), mat('lava', (0.18, 0.17, 0.17), 0.7), mat('tuff2', (0.55, 0.47, 0.36), 0.85)]
for m_ in AGGM: noisy(m_, 5.0, 0.2, 0.1)
rr = random.Random(17); PLACED = []
def lump(name, m, c, rx, rz, seed, sub=3):
    o = prim('ico_sphere', name, m, loc=(MICRO.x + c[0], MICRO.y + 0.02, MICRO.z + c[1]), scale=(rx, 0.22 * min(rx, rz) + 0.05, rz), subdivisions=sub)
    o.rotation_euler.y = rr.uniform(0, 6.28)
    for v in o.data.vertices: v.co *= 1.0 + 0.22 * mnoise.noise(v.co * 2.2 + Vector((seed, 0, 0))) + 0.06 * mnoise.noise(v.co * 9.0 + Vector((0, seed, 0)))
    x_, w_ = cr_x(c[1])
    if abs(c[0] - x_) < max(rx, rz) * 1.3 + w_: cut(o)
    return o
BIG = lump('bigclast', LIMEC, (0.0, 0.0), 1.05, 1.25, 3.0, 4); BIG.scale.y = 0.45
PLACED.append(((0.0, 0.0), 1.3))
LIMES = [BIG]
for kind, count, rmin, rmax in (('agg', 70, 0.5, 1.9), ('lime', 46, 0.12, 0.55)):
    for k in range(count * 6):
        if (kind == 'agg' and len(PLACED) >= count + 1) or (kind == 'lime' and len(LIMES) >= count + 1): break
        c = (rr.uniform(-11, 11), rr.uniform(-11, 11)); r_ = rr.uniform(rmin, rmax)
        if any(math.hypot(c[0] - q[0], c[1] - q[1]) < r_ + qr + 0.12 for q, qr in PLACED): continue
        PLACED.append((c, r_))
        if kind == 'agg': lump(f'agg{k}', AGGM[k % 4], c, r_ * rr.uniform(0.7, 1.3), r_ * rr.uniform(0.6, 1.1), k * 1.7)
        else: LIMES.append(lump(f'lime{k}', LIMEC, c, r_ * rr.uniform(0.8, 1.2), r_ * rr.uniform(0.7, 1.1), k * 2.3 + 50))
SANDM = [mat('sandbit0', (0.30, 0.26, 0.21), 0.8), mat('sandbit1', (0.62, 0.57, 0.48), 0.8), mat('sandbit2', (0.16, 0.14, 0.13), 0.7)]
for k in range(420):
    c = (rr.uniform(-12, 12), rr.uniform(-12, 12)); r_ = rr.uniform(0.04, 0.13)
    if any(math.hypot(c[0] - q[0], c[1] - q[1]) < r_ + qr for q, qr in PLACED): continue
    x_, w_ = cr_x(c[1])
    if abs(c[0] - x_) < w_ + r_: continue
    o = prim('ico_sphere', f'aggs{k}', SANDM[k % 3], loc=(MICRO.x + c[0], MICRO.y + 0.01, MICRO.z + c[1]), scale=(r_, r_ * 0.5, r_ * rr.uniform(0.7, 1.2)), subdivisions=1)
# the water that runs down into the crack, and the calcite that grows out of it
CWATERM = mat('crackwater', (0.35, 0.62, 0.95), 0.05, trans=0.35, ior=1.33, coat=0.8, emit=(0.2, 0.45, 0.9), estr=0.35)
CWATER = prism('crackwater', 14.5, 14.0, 0.02, 2.4, 0.97, CWATERM)
def set_crack_water(z_lo, z_hi=14.5):
    tmp = prism('_tmpw', z_hi, max(z_lo, -14.5), 0.02, 2.4, 0.97, CWATERM)
    co = [0.0] * (len(tmp.data.vertices) * 3); tmp.data.vertices.foreach_get('co', co); CWATER.data.vertices.foreach_set('co', co); CWATER.data.update()
    bpy.data.objects.remove(tmp, do_unlink=True)
CALCM = mat('calcite', (0.97, 0.96, 0.92), 0.12, trans=0.15, ior=1.6, coat=0.6, emit=(1.0, 0.98, 0.92), estr=0.15)
CRYS = []
for i in range(520):
    z_ = rr.uniform(-12.5, 12.5); x_, w_ = cr_x(z_); side = 1 if i % 2 else -1; yy = rr.uniform(0.03, 0.45)
    o = box(f'xtal{i}', (1.0, 1.0, 1.0), (MICRO.x + x_ + side * w_ / 2, MICRO.y + yy, MICRO.z + z_), CALCM)
    o.rotation_euler = (rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), rr.uniform(0, 6.28)); o['sz'] = w_ * rr.uniform(0.55, 1.0); o['z'] = z_; o['side'] = side
    o['t0'] = rr.random(); o.scale = (1e-3,) * 3; o.hide_render = True; CRYS.append(o)
CFILL = prism('calcfill', 14.4, -14.4, 0.01, 2.0, 1.0, CALCM); CFILL.hide_render = True
# a dark room round the set so the open sky does not flatten it; only the two lamps light it
ROOM = box('microroom', (60.0, 60.0, 60.0), MICRO + Vector((0, -10.0, 0)), mat('roomdark', (0.012, 0.011, 0.010), 0.95))
for p_ in ROOM.data.polygons: p_.flip()
MICRO_OBJS = [SLAB, CWATER, CFILL, ROOM] + CRYS + [o for o in bpy.data.objects if o.name.startswith(('agg', 'lime', 'bigclast'))]
MLIGHT = light_at('microlight', 'AREA', MICRO + Vector((-9.0, -5.0, 13.0)), MICRO, 1300.0, (1.0, 0.96, 0.9), 5.0)
MLIGHT2 = light_at('microlight2', 'AREA', MICRO + Vector((10.0, -12.0, -4.0)), MICRO, 220.0, (0.8, 0.88, 1.0), 6.0)
