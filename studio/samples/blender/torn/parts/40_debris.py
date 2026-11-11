# ================================================================ DEBRIS: one mesh of many pieces (boards, shingles, rocks, glass), each moved
# and turned by numpy every frame. swirl(centre, ...) puts them on a spinning, rising cloud around a point (the funnel or the man)
class Swarm:
    KINDS = {'board': ((1.6, 0.14, 0.035), 0), 'shingle': ((0.33, 0.25, 0.01), 1), 'rock': ((0.08, 0.07, 0.06), 2), 'glass': ((0.22, 0.16, 0.006), 3), 'dust': ((0.05, 0.05, 0.05), 2)}
    def __init__(self, name, mix, seed, mats):
        rr = np.random.default_rng(seed); parts = []
        for k, n in mix:
            for _ in range(n): parts.append(k)
        self.n = len(parts); V, F, MI = [], [], []; self.local = []
        for i, k in enumerate(parts):
            (sx, sy, sz), mi = self.KINDS[k]; s = rr.uniform(0.6, 1.3)
            if k in ('rock', 'dust'):
                bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); pts = np.array([v.co[:] for v in bm.verts]) * np.array([sx, sy, sz]) * s * rr.uniform(0.7, 1.3, (1, 3))
                fs = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
            elif k == 'glass':
                pts = np.array([[0, 0, 0], [sx, rr.uniform(-0.3, 0.3) * sy, 0], [rr.uniform(0.2, 0.8) * sx, sy, 0], [0, 0, sz], [sx, 0, sz], [0.5 * sx, sy, sz]]) * s; pts -= pts.mean(0)
                fs = [[0, 1, 2], [3, 5, 4], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]]
            else:
                x, y, z = sx * s / 2, sy * s / 2, sz / 2; pts = np.array([[a, b, c] for a in (-x, x) for b in (-y, y) for c in (-z, z)])
                fs = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
            b0 = sum(len(p) for p in self.local); self.local.append(pts); F += [[b0 + j for j in f] for f in fs]; MI += [mi] * len(fs)
        self.counts = [len(p) for p in self.local]; self.L = np.concatenate(self.local)
        self.owner = np.repeat(np.arange(self.n), self.counts)
        me = bpy.data.meshes.new(name); me.from_pydata(self.L.tolist(), [], F); me.update()
        for m_ in mats: me.materials.append(m_)
        me.polygons.foreach_set('material_index', MI); me.update()
        self.o = obj(name, me); self.o.visible_shadow = True
        self.rad = rr.uniform(0.3, 1.0, self.n); self.ph = rr.uniform(0, 2 * math.pi, self.n); self.hz = rr.uniform(0, 1, self.n)
        self.spin = rr.normal(size=(self.n, 3)) * 3.0; self.sp = rr.uniform(0.7, 1.3, self.n)
    def set(self, P, ang):
        """P: (n,3) centres; ang: (n,3) euler angles"""
        cx, cy, cz = np.cos(ang).T; sx, sy, sz = np.sin(ang).T
        Rm = np.empty((self.n, 3, 3))
        Rm[:, 0, 0] = cy * cz; Rm[:, 0, 1] = sx * sy * cz - cx * sz; Rm[:, 0, 2] = cx * sy * cz + sx * sz
        Rm[:, 1, 0] = cy * sz; Rm[:, 1, 1] = sx * sy * sz + cx * cz; Rm[:, 1, 2] = cx * sy * sz - sx * cz
        Rm[:, 2, 0] = -sy; Rm[:, 2, 1] = sx * cy; Rm[:, 2, 2] = cx * cy
        W = np.einsum('vij,vj->vi', Rm[self.owner], self.L) + P[self.owner]
        self.o.data.vertices.foreach_set('co', W.reshape(-1).astype(np.float32)); self.o.data.update()
    def swirl(self, c, t, r0, r1, h, w, slow=1.0, inward=0.0, lift=0.0):
        """a spinning cloud around c: radius r0..r1, height 0..h, turning w rad/s (inner faster); slow = time scale (slow motion)"""
        r = r0 + (r1 - r0) * self.rad; r = r * (1 - inward * 0.5)
        a = self.ph + t * slow * w * self.sp * (r1 / np.maximum(r, 0.1)) ** 0.5
        z = (self.hz * h + t * slow * lift * self.sp) % max(h, 1e-3)
        P = np.stack([c.x + r * np.cos(a), c.y + r * np.sin(a), c.z + z], 1); self.set(P, self.spin * t * slow); return P
WOODD_M = noisy(mat('debris_wood', (0.4, 0.3, 0.2), 0.8), 20, 0.4); SHING_M = noisy(mat('shingle', (0.15, 0.14, 0.14), 0.9), 40, 0.3)
ROCK_M = noisy(mat('rock', (0.28, 0.25, 0.22), 0.9), 60, 0.4); GLASS_M = mat('glassd', (0.85, 0.95, 1.0), 0.02, trans=1.0, ior=1.5)
DEB_MATS = [WOODD_M, SHING_M, ROCK_M, GLASS_M]
NEAR = Swarm('debris_near', [('board', 14), ('shingle', 40), ('rock', 70), ('glass', 30)], 1, DEB_MATS)        # around him, close up
FAR = Swarm('debris_far', [('board', 60), ('shingle', 160), ('dust', 900)], 2, DEB_MATS)                       # around the funnel
DUSTC = prim('cylinder', 'dust_cloud', None, loc=TC0, vertices=64, radius=60, depth=40)
DUSTC.data.materials.append(FUN_M); DUSTC['tt'] = 0.0; DUSTC['dens'] = 0.8; DUSTC.visible_shadow = False
for v in DUSTC.data.vertices: v.co.z += 20; v.co *= Vector((1, 1, 1)) * (1 + 0.15 * mnoise.noise(v.co * 0.05))
# ---- INFLOW: glowing air streams that spiral in along the ground and climb the core ('arc' bands run along them)
def stream_mat():
    m = bpy.data.materials.new('stream'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    arc = nt.nodes.new('ShaderNodeAttribute'); arc.attribute_type = 'GEOMETRY'; arc.attribute_name = 'arc'
    ph = math_(nt, 'SUBTRACT', math_(nt, 'MULTIPLY', arc.outputs['Fac'], 0.025), math_(nt, 'MULTIPLY', objattr(nt, 'tt'), objattr(nt, 'speed')))
    band = math_(nt, 'POWER', math_(nt, 'MULTIPLY_ADD', math_(nt, 'SINE', math_(nt, 'MULTIPLY', ph, 6.2832)), 0.5, 0.5), 4.0)
    show = math_(nt, 'LESS_THAN', arc.outputs['Fac'], objattr(nt, 'reach'))
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.45, 0.85, 1.0, 1)
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY_ADD', band, 14.0, 1.5), show), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(math_(nt, 'MULTIPLY', show, math_(nt, 'MULTIPLY_ADD', band, 0.6, 0.35)), mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(em.outputs['Emission'], mx.inputs[2]); nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
STR_M = stream_mat()
def stream_lines(n=14):
    vs, fs, av = [], [], []; SEG = 6
    for j in range(n):
        a0 = 2 * math.pi * j / n; pts = []
        for k in range(260):
            s = k / 259
            if s < 0.6: u = s / 0.6; r = 260 * (1 - u) ** 1.6 + 26; a = a0 + 9.0 * u ** 1.8; z = 2 + 6 * u
            else: u = (s - 0.6) / 0.4; r = 26 * (1 - 0.35 * u); a = a0 + 9.0 + 14 * u; z = 8 + 520 * u ** 1.2
            pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
        arc = [0.0]
        for i in range(1, len(pts)): arc.append(arc[-1] + (pts[i] - pts[i - 1]).length)
        base = len(vs); up = Vector((0, 0, 1))
        for i, p in enumerate(pts):
            d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized(); x = d.cross(up)
            x = x.normalized() if x.length > 1e-4 else Vector((1, 0, 0)); y = d.cross(x); rw = 0.9 + 1.5 * (i / len(pts))
            for q in range(SEG): aa = 2 * math.pi * q / SEG; vs.append(tuple(p + (x * math.cos(aa) + y * math.sin(aa)) * rw)); av.append(arc[i])
        for i in range(len(pts) - 1):
            for q in range(SEG): a_ = base + i * SEG + q; b_ = base + i * SEG + (q + 1) % SEG; fs.append((a_, b_, b_ + SEG, a_ + SEG))
    me = bpy.data.meshes.new('streams'); me.from_pydata(vs, [], fs); me.update(); at = me.attributes.new('arc', 'FLOAT', 'POINT'); at.data.foreach_set('value', av)
    o = obj('streams', me, STR_M, loc=TC0); o['tt'] = 0.0; o['speed'] = 1.2; o['reach'] = 0.0; o.visible_shadow = False; return o
STREAMS = stream_lines()
# ---- the SHELTER: a small interior closet (no windows), one bare bulb that swings, towels on a shelf, a door ajar
CL = V3(300.0, 0.0, 0.0)
CLOSET = [box('cl_floor', (1.6, 1.6, 0.05), CL + V3(0, 0, -0.025), noisy(mat('cl_floor', (0.35, 0.27, 0.2), 0.6), 20, 0.3))]
CW_M = noisy(mat('cl_wall', (0.62, 0.6, 0.55), 0.85), 4, 0.08)
for nm, sz, lc in (('cl_wl', (0.05, 1.6, 2.4), V3(-0.8, 0, 1.2)), ('cl_wr', (0.05, 1.6, 2.4), V3(0.8, 0, 1.2)), ('cl_wb', (1.6, 0.05, 2.4), V3(0, 0.8, 1.2)), ('cl_ceil', (1.6, 1.6, 0.05), V3(0, 0, 2.42))):
    CLOSET.append(box(nm, sz, CL + lc, CW_M))
CLOSET.append(box('cl_shelf', (1.5, 0.4, 0.03), CL + V3(0, 0.6, 1.75), WOOD_M))
for i in range(4): CLOSET.append(box('towel%d' % i, (0.32, 0.36, 0.12), CL + V3(-0.55 + i * 0.36, 0.6, 1.83), mat('towel%d' % i, [(0.7, 0.3, 0.25), (0.25, 0.4, 0.6), (0.85, 0.82, 0.7), (0.4, 0.55, 0.35)][i], 0.95, sheen=0.6)))
BULB = empty('bulb_pivot', loc=CL + V3(0, 0, 2.4))
prim('cylinder', 'bulb_cord', mat('cord', (0.05, 0.05, 0.05), 0.5), BULB, loc=(0, 0, -0.15), vertices=8, radius=0.004, depth=0.3)
prim('uv_sphere', 'bulb_glass', emis('bulb_e', (1.0, 0.78, 0.5), 40.0), BULB, loc=(0, 0, -0.33), segments=16, ring_count=8, radius=0.04)
BLT = bpy.data.lights.new('bulb_light', 'POINT'); BLT.energy = 260; BLT.color = (1.0, 0.78, 0.5); BLT.shadow_soft_size = 0.04
BLO = bpy.data.objects.new('bulb_light', BLT); S.collection.objects.link(BLO); BLO.parent = BULB; BLO.location = (0, 0, -0.33)
CLOSET += [BULB, BLO] + [o for o in bpy.data.objects if o.parent == BULB]
