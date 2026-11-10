# ================================================================ INSIDE THE KIDNEY (a set of its own far from the room, at MO): the hollow
# where pee collects. Waste floats in it: calcium (white) and oxalate (blue-green) specks. Less water -> the same specks in half the
# room. They join into sharp two-ended crystals; the crystals stack into a stone.
MO = V3(40.0, 0.0, 1.0)
def cave_mat():
    m = mat('kidney_wall', (0.55, 0.13, 0.1), 0.3, coat=0.6); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    b.inputs['Subsurface Weight'].default_value = 0.4; b.inputs['Subsurface Radius'].default_value = (0.2, 0.06, 0.04)
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 5.0; nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14.0; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector']); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.05
    nt.links.new(math_(nt, 'ADD', vo.outputs['Distance'], math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.4)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.62, 0.16, 0.12, 1); mx.inputs['B'].default_value = (0.3, 0.05, 0.05, 1)
    nt.links.new(vo.outputs['Distance'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color']); return m
CAVE = prim('ico_sphere', 'kidney_cave', cave_mat(), loc=MO, subdivisions=5, radius=1.0, scale=(0.85, 1.3, 1.1))
bpy.context.view_layer.objects.active = CAVE; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
_cr = random.Random(21)
for v in CAVE.data.vertices:
    n = mnoise.noise(v.co * 2.2) * 0.14 + mnoise.noise(v.co * 5.0) * 0.05; v.co *= 1.0 + n
class Specks:
    """many small balls in one mesh, moved by numpy each frame"""
    def __init__(self, name, n, r, m, seed):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); base = np.array([v.co[:] for v in bm.verts]); faces = [[v.index for v in f.verts] for f in bm.faces]; bm.free()
        self.base = base; self.n = n; self.nv = len(base); rr = np.random.default_rng(seed)
        d = rr.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1)[:, None]; self.p0 = d * (rr.random(n)[:, None] ** 0.45) * np.array([0.42, 0.34, 0.5])
        self.r = r * rr.uniform(0.7, 1.3, n); self.seed = rr.random(n) * 100
        vs = (self.p0[:, None, :] + base[None] * self.r[:, None, None]).reshape(-1, 3); fs = [[i * self.nv + k for k in f] for i in range(n) for f in faces]
        me = bpy.data.meshes.new(name); me.from_pydata(vs.tolist(), [], fs); me.update()
        for p in me.polygons: p.use_smooth = True
        self.o = obj(name, me, m, loc=MO); self.o.visible_shadow = False
    def set(self, P, Sc):
        vs = (P[:, None, :] + self.base[None] * (self.r * Sc)[:, None, None]).reshape(-1); self.o.data.vertices.foreach_set('co', vs.astype(np.float32)); self.o.data.update()
CA = Specks('calcium', 150, 0.011, mat('calcium', (0.95, 0.95, 0.92), 0.3, emit=(1.0, 0.98, 0.9), estr=0.6), 1)
OX = Specks('oxalate', 150, 0.008, mat('oxalate', (0.25, 0.85, 0.75), 0.3, emit=(0.2, 0.9, 0.75), estr=0.9), 2)
class Cluster:
    """sharp two-ended crystals in one mesh; each has a free spot (where it forms), a home in the stone, a size"""
    def __init__(self, name, n, seed, spread, size, m, loc):
        rr = random.Random(seed); V, H = [], []; fs = []
        for i in range(n):
            d = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 1))).normalized(); c = Vector((d.x, d.y * 0.8, d.z * 0.75)) * spread * (rr.uniform(0.0, 0.35) if i < 8 else rr.uniform(0.45, 1.0))
            s = size * rr.uniform(0.55, 1.0); ax = (d + Vector((rr.gauss(0, 0.5), rr.gauss(0, 0.5), rr.gauss(0, 0.5)))).normalized(); u = ax.orthogonal().normalized(); w = ax.cross(u)
            V.append([ax * s * 1.25, -ax * s * 0.9] + [(u * math.cos(a_) + w * math.sin(a_)) * s * 0.62 for a_ in (0.4, 1.97, 3.54, 5.11)]); H.append(c)
            b0 = i * 6
            for k in range(4): k2 = (k + 1) % 4; fs += [(b0, b0 + 2 + k, b0 + 2 + k2), (b0 + 1, b0 + 2 + k2, b0 + 2 + k)]
        self.V = np.array([[v[:] for v in c] for c in V]); self.H = np.array([h[:] for h in H]); self.n = n
        rg = np.random.default_rng(seed); d = rg.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1)[:, None]
        self.F = d * rg.uniform(0.16, 0.36, n)[:, None] * np.array([1.0, 0.8, 1.25]); self.spin = rg.uniform(-2, 2, (n, 3))
        me = bpy.data.meshes.new(name); me.from_pydata((self.H[:, None, :] + self.V).reshape(-1, 3).tolist(), [], fs); me.update()
        self.o = obj(name, me, m, loc=loc); self.o['glow'] = 0.3
    def set(self, attach, grow, t=0.0):
        """attach 0..1 per crystal (free spot -> home), grow 0..1 (size)"""
        a_ = attach[:, None]; P = self.F * (1 - a_) + self.H * a_
        ang = (1 - attach) * (t * 0.8 + 1.0); c_, s_ = np.cos(ang * self.spin[:, 0])[:, None, None], np.sin(ang * self.spin[:, 0])[:, None, None]
        V = self.V.copy(); x = V[:, :, 0:1] * c_ - V[:, :, 1:2] * s_; y = V[:, :, 0:1] * s_ + V[:, :, 1:2] * c_; V[:, :, 0:1] = x; V[:, :, 1:2] = y
        vs = (P[:, None, :] + V * grow[:, None, None]).reshape(-1); self.o.data.vertices.foreach_set('co', vs.astype(np.float32)); self.o.data.update()
def crystal_mat():
    m = stone_mat('crystal'); return m
NCR = 90
BIG = Cluster('macro_stone', NCR, 5, 0.105, 0.062, crystal_mat(), MO)
_ord = np.argsort(np.linalg.norm(BIG.H, axis=1)); BIG.rank = np.empty(NCR); BIG.rank[_ord] = np.arange(NCR) / (NCR - 1)        # inner ones attach first
# each speck's crystal (first 16 crystals form in beat 4): it flies to that crystal's free spot and is used up
FIRST = _ord[:16]
for sp_ in (CA, OX): sp_.to = BIG.F[FIRST[np.arange(sp_.n) % 16]]
MK = light_at('macroA_key', 'AREA', MO + V3(-0.5, -0.7, 0.6), MO, 11, (1.0, 0.9, 0.7), 0.6); MR = light_at('macroA_rim', 'AREA', MO + V3(0.6, 0.6, -0.2), MO, 12, (1.0, 0.75, 0.35), 0.8)
MF = light_at('macroA_fill', 'POINT', MO + V3(0, 0, 0), MO + V3(0, 0, 1), 2.5, (1.0, 0.8, 0.4), 0.3)
MACRO_A = [CAVE, CA.o, OX.o, BIG.o, MK, MR, MF]
def macro_a(pack, join, stack, t):
    """pack: specks crowd into less water; join: specks -> first crystals; stack: crystals -> the stone"""
    for sp_ in (CA, OX):
        drift = np.stack([np.sin(t * 0.7 + sp_.seed), np.cos(t * 0.6 + sp_.seed * 1.7), np.sin(t * 0.5 + sp_.seed * 2.3)], 1) * 0.02
        P = sp_.p0 * (1 - 0.5 * pack) + drift * (1 - 0.6 * pack)
        kj = np.clip((join * 1.6 - (sp_.seed % 1.0) * 0.6), 0, 1); kj = kj * kj * (3 - 2 * kj)
        P = P * (1 - kj[:, None]) + sp_.to * kj[:, None]; sp_.set(P, 1.0 - kj ** 3)
    first = np.zeros(NCR, bool); first[FIRST] = True
    grow = np.where(first, np.clip(join * 1.5 - 0.3 - BIG.rank * 1.5, 0, 1), np.clip((stack * 1.25 - BIG.rank) * 6.0, 0, 1))
    att = np.clip((stack * 1.25 - BIG.rank) * 5.0 - 0.15, 0, 1); att = att * att * (3 - 2 * att)
    BIG.set(att, grow * (0.75 + 0.25 * att), t); BIG.o['glow'] = 0.25 + 0.3 * stack
    MF.data.color = Vector((1.0, 0.86, 0.5)).lerp(Vector((1.0, 0.55, 0.12)), pack)
# ================================================================ INSIDE THE URETER (cut open lengthwise, at UO; pee runs down = -z): a thin
# muscle tube with a folded lining. The stone comes down, scrapes the lining, jams where the tube is narrow. Pee fills the tube
# above it; the wall squeezes in waves that run down into the stone.
UO = V3(60.0, 0.0, 1.0)
NS_, NT_ = 150, 40; S_AX = np.linspace(-1.25, 1.25, NS_); TH = np.linspace(R(-2), R(182), NT_)      # the far half of the tube (near half cut away)
def wall_mat():
    m = mat('ureter_wall', (0.86, 0.45, 0.42), 0.3, coat=0.5); nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    b.inputs['Subsurface Weight'].default_value = 0.35; b.inputs['Subsurface Radius'].default_value = (0.08, 0.03, 0.02)
    sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 5; mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (60, 60, 1.5)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    # scrape marks: thin red streaks along the tube, only between where the stone came in (z0) and where it is now (zs)
    below = math_(nt, 'LESS_THAN', sp.outputs['Z'], objattr(nt, 'z0')); above = math_(nt, 'GREATER_THAN', sp.outputs['Z'], objattr(nt, 'zs'))
    streak = math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', below, above), math_(nt, 'GREATER_THAN', nz.outputs['Fac'], 0.56))
    streak = math_(nt, 'MULTIPLY', streak, objattr(nt, 'scrape'))
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.86, 0.45, 0.42, 1); mx.inputs['B'].default_value = (0.75, 0.05, 0.04, 1)
    nt.links.new(streak, mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value = (1.0, 0.1, 0.05, 1); nt.links.new(math_(nt, 'MULTIPLY', streak, 1.2), b.inputs['Emission Strength'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.02; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal']); return m
def _grid_faces(ns, nt, off=0, flip=False):
    fs = []
    for i in range(ns - 1):
        for k in range(nt - 1):
            a0 = off + i * nt + k; q = (a0, a0 + 1, a0 + nt + 1, a0 + nt); fs.append(q[::-1] if flip else q)
    return fs
_N = NS_ * NT_
_fs = _grid_faces(NS_, NT_, 0, True) + _grid_faces(NS_, NT_, _N, False)
for i in range(NS_ - 1):                                              # the two cut faces (lining to outside)
    for k in (0, NT_ - 1):
        a0 = i * NT_ + k; q = (a0, a0 + NT_, a0 + NT_ + _N, a0 + _N); _fs.append(q if k == 0 else q[::-1])
_me = bpy.data.meshes.new('ureter_cut'); _me.from_pydata([(0, 0, 0)] * (2 * _N), [], _fs); _me.update()
for p in _me.polygons: p.use_smooth = True
UWALL = obj('ureter_cut', _me, wall_mat(), loc=UO); UWALL['z0'] = 9.0; UWALL['zs'] = 9.0; UWALL['scrape'] = 0.0
PEE_M = bpy.data.materials.new('pee'); PEE_M.use_nodes = True; _nt = PEE_M.node_tree; _b = _nt.nodes['Principled BSDF']
_b.inputs['Base Color'].default_value = (1.0, 0.78, 0.1, 1); _b.inputs['Roughness'].default_value = 0.05; _b.inputs['Emission Color'].default_value = (1.0, 0.7, 0.05, 1); _b.inputs['Emission Strength'].default_value = 0.9
_tr = _nt.nodes.new('ShaderNodeBsdfTransparent'); _mx = _nt.nodes.new('ShaderNodeMixShader'); _mx.inputs['Fac'].default_value = 0.5
_nt.links.new(_tr.outputs['BSDF'], _mx.inputs[1]); _nt.links.new(_b.outputs['BSDF'], _mx.inputs[2]); _nt.links.new(_mx.outputs['Shader'], _nt.nodes['Material Output'].inputs['Surface'])
NPT = 24; _me2 = bpy.data.meshes.new('pee'); _me2.from_pydata([(0, 0, 0)] * (NS_ * NPT), [], [(i * NPT + k, i * NPT + (k + 1) % NPT, (i + 1) * NPT + (k + 1) % NPT, (i + 1) * NPT + k) for i in range(NS_ - 1) for k in range(NPT)]); _me2.update()
for p in _me2.polygons: p.use_smooth = True
PEE = obj('pee', _me2, PEE_M, loc=UO); PEE.visible_shadow = False
USTONE = Cluster('ureter_stone', 80, 5, 0.085, 0.05, stone_mat('stone_u'), UO); USTONE.set(np.ones(80), np.ones(80)); USTONE.o['glow'] = 0.15
USMALL = Cluster('ureter_small', 40, 9, 0.034, 0.022, stone_mat('stone_s'), UO); USMALL.set(np.ones(40), np.ones(40)); USMALL.o['glow'] = 0.15
RS_BIG, RS_SMALL, R_LUM = 0.118, 0.045, 0.07
UK = light_at('macroB_key', 'AREA', UO + V3(-0.9, -1.3, 0.7), UO, 70, (1.0, 0.93, 0.85), 1.0); UR_ = light_at('macroB_rim', 'AREA', UO + V3(0.9, 0.5, -0.4), UO, 50, (1.0, 0.6, 0.4), 1.0)
UBACK = box('macroB_back', (6, 0.1, 6), UO + V3(0, 1.2, 0), mat('back', (0.03, 0.012, 0.014), 0.9))
MACRO_B = [UWALL, PEE, USTONE.o, USMALL.o, UK, UR_, UBACK]
def lumen(z, t, zs, rs, narrow, back, wave):
    """inner radius along the tube (z down = downstream). zs = stone centre, rs = its radius; narrow: tube tight below the stone;
    back: 0..1 tube swollen with held pee above it; wave: 0..1 strength of the squeeze waves running down"""
    r = np.full_like(z, R_LUM)
    r = r * (1 - 0.42 * narrow * (1 / (1 + np.exp((z - (zs - rs * 0.6)) * 30))))            # narrow part below the stone
    r = r * (1 + 0.5 * back * (1 / (1 + np.exp(-(z - (zs + rs * 0.5)) * 14))))              # swollen above it
    for j in range(3):                                                                      # squeeze rings travelling down
        zw = 1.4 - ((t * 0.75 + j / 3.0) % 1.0) * 2.8
        amp = wave * 0.45 * (1.0 if zw > zs + rs * 0.6 else 0.25)
        r = r * (1 - amp * np.exp(-((z - zw) / 0.11) ** 2))
    if rs > 0: r = np.maximum(r, np.sqrt(np.clip(rs * rs - (z - zs) ** 2, 0, None)) * 0.985)     # the wall wraps the stone
    return r
def ureter_set(t, zs, rs, narrow=1.0, back=0.0, wave=0.0, z0=9.0, scrape=0.0, pee_to=None):
    z = -S_AX; ri = lumen(z, t, zs, rs, narrow, back, wave)
    fold = 1 + 0.07 * np.cos(TH[None, :] * 6 + z[:, None] * 2.0) * np.clip(1.6 - ri[:, None] / R_LUM, 0.2, 1.0)
    RI = ri[:, None] * fold; RO = np.maximum(ri[:, None] + 0.038, 0.118 + 0.0 * RI)
    def ring(Rr): return np.stack([Rr * np.cos(TH)[None, :], Rr * np.sin(TH)[None, :], np.repeat(z[:, None], NT_, 1)], 2).reshape(-1, 3)
    vs = np.concatenate([ring(RI), ring(RO)]).reshape(-1).astype(np.float32); UWALL.data.vertices.foreach_set('co', vs); UWALL.data.update()
    UWALL['zs'] = float(zs); UWALL['z0'] = float(z0); UWALL['scrape'] = float(scrape)
    # the pee: fills the lumen from the top down to 'pee_to' (default: everywhere, a thin stream when nothing is stuck)
    a2 = np.linspace(0, 2 * math.pi, NPT, endpoint=False); top = 9.0 if pee_to is None else pee_to
    rp = np.where(z > top, ri * 0.93, ri * 0.0 + 0.002)
    vp = np.stack([rp[:, None] * np.cos(a2)[None, :], rp[:, None] * np.sin(a2)[None, :], np.repeat(z[:, None], NPT, 1)], 2).reshape(-1).astype(np.float32)
    PEE.data.vertices.foreach_set('co', vp); PEE.data.update()
