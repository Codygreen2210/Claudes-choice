# ================================================================ effects: the sand pile in front of the runners, the wet strip the water leaves,
# the puddle when he dumps too much, the water stream and its splashes, and the grain-scale set (water bridges between grains)
# ---- the pile of dry sand the runners shove ahead of them: one mound per runner, joined by a low ridge
BERM_M = SAND
def mound(name, w, l, n=14):
    vs = []; fs = []
    for j in range(n + 1):
        for i in range(n + 1):
            u = -1 + 2 * i / n; v = -1 + 2 * j / n; r_ = min(1.0, math.hypot(u, v)); hgt = (1 - r_ * r_) ** 1.4 * (1.0 + 0.25 * mnoise.noise(Vector((u * 2.3, v * 2.3, 0.7))))
            vs.append((u * w / 2, v * l / 2 + 0.25 * l * (1 - r_) * (v > 0), max(hgt, 0.0)))
    for j in range(n):
        for i in range(n): a_ = j * (n + 1) + i; fs.append((a_, a_ + 1, a_ + n + 2, a_ + n + 1))
    return mesh(name, vs, fs, BERM_M)
BERMS = []
for s_ in (-1, 1):
    o = mound(f'berm{s_}', 0.42, 0.46); o.parent = SLED; o.location = (s_ * RUN_X, 0.83, -0.004); BERMS.append(o)
RIDGE = mound('ridge', 1.15, 0.30); RIDGE.parent = SLED; RIDGE.location = (0, 0.86, -0.004)
# grains rolling off the pile while they strain (little clumps that tumble down its sides)
GRAINS = []
for k in range(26):
    g = prim('ico_sphere', f'grain{k}', SAND, scale=(1, 1, 0.8), radius=0.012 + 0.012 * h1(k), subdivisions=1); g.parent = SLED; GRAINS.append(g)

# ---- wet sand, painted straight into the road's own sand (a strip behind the pour, the fresh spot, the soaked patch), driven by
# numbers on the road object: wy0..wy1 strip, (sy, sr) spot, (ky, kr) soak
ROADM = pbr('ph:dense_sand', 0.45, 'road', tint=(1.05, 0.93, 0.78), bump=0.8)
def _road_wet(m):
    nt = m.node_tree; b_ = nt.nodes['Principled BSDF']
    lk = next(l for l in nt.links if l.to_socket == b_.inputs['Base Color']); base = lk.from_socket
    rk = next(l for l in nt.links if l.to_socket == b_.inputs['Roughness']); rough = rk.from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry'); ps = sepz(nt, geo.outputs['Position']); X, Y = ps.outputs['X'], ps.outputs['Y']
    nz = tnoise(nt, geo.outputs['Position'], 2.2, 3.0); nz2 = math_(nt, 'SUBTRACT', nz, 0.5)
    def band(v, lo, hi, soft):           # 1 inside [lo, hi] with soft edges
        a1 = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', v, lo), soft), 0.0), 1.0)
        a2 = math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', hi, v), soft), 0.0), 1.0)
        return math_(nt, 'MULTIPLY', a1, a2)
    ax = math_(nt, 'ADD', math_(nt, 'ABSOLUTE', X), math_(nt, 'MULTIPLY', nz2, 0.16))
    strip = math_(nt, 'MULTIPLY', band(ax, -1.0, 0.60, 0.07), band(math_(nt, 'ADD', Y, math_(nt, 'MULTIPLY', nz2, 0.12)), objattr(nt, 'wy0'), objattr(nt, 'wy1'), 0.08))
    def disc(cy, rr, sy_):
        dx = math_(nt, 'MULTIPLY', X, 0.8); dy = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', Y, cy), sy_)
        d_ = math_(nt, 'ADD', math_(nt, 'SQRT', math_(nt, 'ADD', math_(nt, 'MULTIPLY', dx, dx), math_(nt, 'MULTIPLY', dy, dy))), math_(nt, 'MULTIPLY', nz2, 0.14))
        return math_(nt, 'MINIMUM', math_(nt, 'MAXIMUM', math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', rr, d_), 0.06), 0.0), 1.0)
    spot = disc(objattr(nt, 'sy'), objattr(nt, 'sr'), 1.15); soak = disc(objattr(nt, 'ky'), objattr(nt, 'kr'), 0.85)
    wet = math_(nt, 'MAXIMUM', strip, spot); m['wetnode'] = wet.node.name; m['stripnode'] = strip.node.name; m['spotnode'] = spot.node.name
    # darken by scaling the colour (a plain multiply: base * (1 - 0.78 wet) * (1 - 0.6 soak)), a touch warmer in the wet
    def mr(v, o1):
        n_ = nt.nodes.new('ShaderNodeMapRange'); n_.inputs['From Min'].default_value = 0.0; n_.inputs['From Max'].default_value = 1.0
        n_.inputs['To Min'].default_value = 1.0; n_.inputs['To Max'].default_value = o1; nt.links.new(v, n_.inputs['Value']); return n_.outputs['Result']
    k_ = math_(nt, 'MULTIPLY', mr(wet, 0.30), mr(soak, 0.55))
    vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'SCALE'; nt.links.new(base, vm.inputs[0]); nt.links.new(k_, vm.inputs['Scale'])
    c2 = vm.outputs['Vector']
    nt.links.new(c2, b_.inputs['Base Color'])
    r1 = math_(nt, 'ADD', math_(nt, 'MULTIPLY', rough, math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MAXIMUM', wet, soak))), math_(nt, 'ADD', math_(nt, 'MULTIPLY', wet, 0.92), math_(nt, 'MULTIPLY', soak, 0.0)))
    try: nt.links.new(math_(nt, 'MULTIPLY', mr(math_(nt, 'MAXIMUM', wet, soak), 0.3), 0.5), b_.inputs['Specular IOR Level'])
    except Exception as e_: print('spec skipped', e_)
    nt.links.new(r1, b_.inputs['Roughness'])
    return m
_road_wet(ROADM)
NEAR.data.materials[0] = ROADM
for k_, v_ in (('wy0', 0.0), ('wy1', -1.0), ('sy', 0.0), ('sr', -1.0), ('ky', 0.0), ('kr', -1.0)): NEAR[k_] = v_
POOLM = mat('pool', (0.07, 0.05, 0.03), 0.06, coat=0.6)
POOL = lathe('pool', [(0.0, 0.010), (0.6, 0.010), (0.85, 0.008), (0.95, 0.004), (1.0, 0.0)], 40, POOLM)
# ---- the stream from the jar and the splash where it lands
class Stream:
    def __init__(self, n=22):
        self.n = n; self.seg = 10; self.o = tube('stream', [(0, 0, -i * 0.05) for i in range(n)], 0.02, WATERM, seg=10, caps=True)
    def set(self, p0, v0, r0, t, wob_amt=1.0):
        g = Vector((0, 0, -9.8)); pts = []; tau = 0.0
        tz = (v0.z + math.sqrt(max(v0.z ** 2 - 2 * g.z * (p0.z - 0.0), 0))) / -g.z
        for i in range(self.n):
            tau = tz * i / (self.n - 1); p = p0 + v0 * tau + 0.5 * g * tau * tau
            p += Vector((wob(t - tau, 9, i * 0.1), wob(t - tau, 9, 3 + i * 0.1), 0)) * 0.006 * wob_amt * (i / self.n)
            pts.append(p)
        co = []; T0 = (pts[1] - pts[0]).normalized(); up = Vector((1, 0, 0)); Nn = T0.cross(up).normalized()
        for i, p in enumerate(pts):
            T = (pts[min(i + 1, self.n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
            rr = r0 * (1.0 - 0.45 * i / (self.n - 1)) * (1 + 0.15 * wob(t * 3 - i * 0.2, 7, i))
            for k in range(self.seg): co.extend(p + (Nn * math.cos(2 * math.pi * k / self.seg) + Bn * math.sin(2 * math.pi * k / self.seg)) * rr)
        self.o.data.vertices.foreach_set('co', co); self.o.data.update(); return pts[-1]
STREAM = Stream()
DROPS = [prim('uv_sphere', f'drop{k}', WATERM, radius=0.007 + 0.006 * h1(k + 40), segments=10, ring_count=6) for k in range(18)]
for d_ in DROPS: d_.scale = (1, 1, 1.25)
SPLASH = lathe('splash', [(0.0, 0.0), (0.03, 0.003), (0.05, 0.012), (0.06, 0.022), (0.064, 0.02), (0.056, 0.008), (0.04, 0.002)], 28, WATERM)

# ---- grain scale: a bed of sand grains (rounded, chipped quartz) floating high above the desert, with water bridges that grow
# between touching grains; the camera dives into the wet sand and comes out here, then flies back up
MICRO = Vector((40, -60, 400)); GR = 0.06          # 1 grain ~ 0.12 m across here (real grains are ~0.25 mm)
QUARTZ = mat('quartz', (0.36, 0.20, 0.08), 0.28, coat=0.4); noisy(QUARTZ, 18.0, 0.45, 0.15)
QUARTZ2 = mat('quartz2', (0.22, 0.12, 0.05), 0.32, coat=0.3); noisy(QUARTZ2, 22.0, 0.45, 0.15)
QUARTZ3 = mat('quartz3', (0.46, 0.34, 0.20), 0.3, coat=0.3); noisy(QUARTZ3, 20.0, 0.4, 0.15)
BRIDGEM = mat('bridge', (0.15, 0.45, 1.0), 0.03, trans=0.25, ior=1.33, coat=0.9, emit=(0.15, 0.50, 1.0), estr=2.2)
rng = random.Random(5); GRS = []
bed = prim('plane', 'microbed', mat('microbedm', (0.12, 0.08, 0.05), 0.9), loc=MICRO + Vector((0, 0, -GR * 1.2)), size=40.0)
for k in range(4000):
    for _ in range(30):
        p = MICRO + Vector((rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6), 0)); r_ = GR * rng.uniform(0.7, 1.3)
        p.z += rng.uniform(-1.0, 1.4) * GR
        if all((p - q).length > (r_ + rq) * 0.93 for q, rq in GRS[-400:]): break
    else: continue
    GRS.append((p, r_))
    if len(GRS) >= 1500: break
for k, (p, r_) in enumerate(GRS):
    o = prim('ico_sphere', f'g{k}', (QUARTZ, QUARTZ2, QUARTZ3)[k % 3], loc=p, scale=(r_ * rng.uniform(0.85, 1.2), r_ * rng.uniform(0.8, 1.1), r_ * rng.uniform(0.7, 1.0)), subdivisions=3)
    o.rotation_euler = (rng.uniform(0, 6), rng.uniform(0, 6), rng.uniform(0, 6))
    for v in o.data.vertices: v.co *= 1.0 + 0.10 * mnoise.noise(v.co * (2.2 / r_) + Vector((k, 0, 0)))
    for pp in o.data.polygons: pp.use_smooth = True
# water bridges: a pinched neck between every close pair near the middle of the bed
BRIDGES = []
def neck(name, a_, ra, b_, rb):
    ax = (b_ - a_); L_ = ax.length; d_ = ax / L_; seg = 18; rings = 9; vs = []; fs = []
    up = Vector((0, 0, 1)) if abs(d_.z) < 0.9 else Vector((1, 0, 0)); n1 = d_.cross(up).normalized(); n2 = d_.cross(n1)
    s0 = ra * 0.55; s1 = L_ - rb * 0.55
    for i in range(rings):
        u = i / (rings - 1); s_ = lerp(s0, s1, u); rr = min(ra, rb) * (0.62 - 0.22 * math.sin(math.pi * u))
        for k in range(seg): a2 = 2 * math.pi * k / seg; vs.append(a_ + d_ * s_ + (n1 * math.cos(a2) + n2 * math.sin(a2)) * rr)
    for i in range(rings - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    o = mesh(name, [tuple(v - a_) for v in vs], fs, BRIDGEM, loc=a_); return o
for i, (p, r_) in enumerate(GRS):
    if (p - MICRO).length > 0.9: continue
    for j in range(i + 1, len(GRS)):
        q, rq = GRS[j]
        if (p - q).length < (r_ + rq) * 1.15 and len(BRIDGES) < 420:
            o = neck(f'br{i}_{j}', p, r_, q, rq); o['d'] = (p - MICRO).length; BRIDGES.append(o)
print('grains', len(GRS), 'bridges', len(BRIDGES))

