# ================================================================ the crack in the wall (a dark slit that shoots across the brick face), the two test
# blocks on the bench (each split by a crack, water fed from a clay funnel, dripping out the bottom into a bowl), the worker's bucket
class Ribbon:
    """a flat strip of fixed vertex count; set() takes centre points, widths and a normal and rebuilds it"""
    def __init__(self, name, n, m, parent=None):
        self.n = n; vs = [(i * 0.01, 0, 0) for i in range(n)] + [(i * 0.01, 0, 0.001) for i in range(n)]
        fs = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        self.o = mesh(name, vs, fs, m, parent, smooth_=False)
    def set(self, pts, ws, nrm):
        n = self.n; co_l = []; co_r = []
        for i in range(n):
            a_ = pts[max(i - 1, 0)]; b_ = pts[min(i + 1, n - 1)]; tg = (b_ - a_); tg = tg.normalized() if tg.length > 1e-9 else Vector((1, 0, 0))
            side = nrm.cross(tg).normalized() * ws[i] * 0.5
            co_l.extend(pts[i] - side); co_r.extend(pts[i] + side)
        self.o.data.vertices.foreach_set('co', co_l + co_r); self.o.data.update()
def jag(p0, p1, n, amp, seed, branch_amp=0.0):
    """a jagged crack path from p0 to p1 (2D tuples), n points"""
    rr = random.Random(seed); pts = []; off = 0.0
    for i in range(n):
        u = i / (n - 1); off = off * 0.55 + rr.uniform(-1, 1) * amp
        x_ = lerp(p0[0], p1[0], u); y_ = lerp(p0[1], p1[1], u) + off * math.sin(math.pi * u) ** 0.3
        pts.append((x_, y_))
    return pts
CRACKM = mat('crackdark', (0.012, 0.010, 0.009), 0.9)
# the wall crack: main run plus two short branches
WC_N = 70
WC_PATH = jag((-1.55, 1.70), (1.45, 0.98), WC_N, 0.055, 11)
WC_W = [0.004 + 0.012 * math.sin(math.pi * i / (WC_N - 1)) ** 0.6 * (0.7 + 0.6 * h1(i)) for i in range(WC_N)]
WCRACK = Ribbon('wallcrack', WC_N, CRACKM)
WC_BR = [(jag(WC_PATH[18], (WC_PATH[18][0] + 0.25, WC_PATH[18][1] + 0.38), 16, 0.03, 21), 0.30, 0.45),
         (jag(WC_PATH[44], (WC_PATH[44][0] + 0.12, WC_PATH[44][1] - 0.42), 16, 0.03, 23), 0.62, 0.78)]
WBR = [Ribbon(f'wallbranch{k}', 16, CRACKM) for k in range(len(WC_BR))]
def crack_pts(path, g, n):
    """the first fraction g of the path, resampled to n points (the rest bunched at the tip)"""
    m_ = len(path) - 1; out = []
    for i in range(n):
        s_ = g * m_ * i / (n - 1); j = min(int(s_), m_ - 1); k = s_ - j
        out.append((lerp(path[j][0], path[j + 1][0], k), lerp(path[j][1], path[j + 1][1], k)))
    return out
def set_wall_crack(g, wid=1.0):
    pts = [wall_pt(u_, v_, 0.004) for u_, v_ in crack_pts(WC_PATH, max(g, 0.002), WC_N)]
    ws = [WC_W[i] * wid * min(1.0, (1 - i / (WC_N - 1)) * 8 + 0.15) if g < 0.999 else WC_W[i] * wid for i in range(WC_N)]
    WCRACK.set(pts, ws, WALL_N); WCRACK.o.hide_render = g < 0.003
    for k, (bp, g0, g1) in enumerate(WC_BR):
        gb = clamp((g - g0) / (g1 - g0), 0, 1)
        WBR[k].set([wall_pt(u_, v_, 0.004) for u_, v_ in crack_pts(bp, max(gb, 0.002), 16)], [0.007 * wid * (1 - i / 16) for i in range(16)], WALL_N)
        WBR[k].o.hide_render = gb < 0.01
# chips knocked off where it split: a few dark flecks and a small spall
SPALL = []
for k in range(14):
    u_, v_ = WC_PATH[4 + k * 4]
    o = prim('ico_sphere', f'chip{k}', BRICK, scale=(1, 0.6, 1), radius=0.008 + 0.006 * h1(k), subdivisions=1); SPALL.append((o, k))

# ---- the test blocks: two concrete cylinders on little wooden grates over bowls, a clay funnel above each
TCONC = pbr('acg:Concrete048', 2.2, 'tconc', 'Object', tint=(0.86, 0.84, 0.80), boxp=True)
CLAY = mat('clay', (0.48, 0.22, 0.12), 0.8); noisy(CLAY, 30.0, 0.2, 0.1)
TB_R = 0.075; TB_H = 0.30; TB_Z0 = 0.855 + 0.09
TBLOCK = []
for k, dx in enumerate((-0.33, 0.33)):
    c = BENCH_C + Vector((dx, 0.0, 0.0))
    blk = prim('cylinder', f'tblock{k}', TCONC, loc=(c.x, c.y, TB_Z0 + TB_H / 2), radius=TB_R, depth=TB_H, vertices=48); bevel(blk, 0.004, 2)
    for sy in (-0.045, 0.045): box(f'grate{k}{sy}', (0.22, 0.022, 0.03), (c.x, c.y + sy, TB_Z0 - 0.015), WOOD)
    for sx in (-0.09, 0.09): box(f'gleg{k}{sx}', (0.025, 0.12, 0.06), (c.x + sx, c.y, TB_Z0 - 0.06), WOOD)
    bowl = lathe(f'bowl{k}', [(0.0, 0.0), (0.07, 0.0), (0.095, 0.03), (0.10, 0.045), (0.092, 0.045), (0.085, 0.032), (0.06, 0.008), (0.0, 0.008)], 40, CLAY, loc=(c.x, c.y, 0.89))
    fun = lathe(f'funnel{k}', [(0.012, 0.0), (0.016, 0.0), (0.02, 0.06), (0.075, 0.13), (0.07, 0.135), (0.014, 0.065), (0.008, 0.0)], 36, CLAY, loc=(c.x, c.y, TB_Z0 + TB_H + 0.12))
    stand = tube(f'fstand{k}', [(c.x + 0.14, c.y + 0.06, 0.89), (c.x + 0.14, c.y + 0.06, TB_Z0 + TB_H + 0.24), (c.x + 0.07, c.y + 0.03, TB_Z0 + TB_H + 0.24)], 0.008, WOOD, seg=8)
    cm = mat(f'tcrack{k}', (0.015, 0.013, 0.012), 0.9)
    # crack down the front of the block (facing -y), from the top rim to the bottom
    path = jag((0.0, TB_H / 2), (0.01, -TB_H / 2), 30, 0.008, 40 + k)
    rb = Ribbon(f'tcrack{k}', 30, cm)
    pts = []
    for x_, z_ in path:
        a_ = -math.pi / 2 + x_ / TB_R; pts.append(Vector((c.x + (TB_R + 0.0015) * math.cos(a_), c.y + (TB_R + 0.0015) * math.sin(a_), TB_Z0 + TB_H / 2 + z_)))
    rb.set(pts, [0.0035 + 0.002 * h1(i + 7 * k) for i in range(30)], Vector((0, -1, 0)))
    TBLOCK.append({'c': c, 'blk': blk, 'crack': rb, 'cm': cm, 'pts': pts, 'top': Vector((c.x, c.y, TB_Z0 + TB_H)), 'bottom': Vector((c.x, c.y - 0.01, TB_Z0 - 0.005)),
                   'funnel': Vector((c.x, c.y, TB_Z0 + TB_H + 0.12)), 'bowl': Vector((c.x, c.y, 0.89))})

# ---- the worker's bucket
BUCKET = P.place('ph:wooden_bucket_01', loc=(0, 0, 0), height=0.32, name='bucket')
BUCKET_ROOT = empty('bucket_root'); BUCKET.parent = BUCKET_ROOT
BK_H = BUCKET['size'][2]; BK_R = max(BUCKET['size'][0], BUCKET['size'][1]) / 2
WATERM = mat('water', (0.8, 0.88, 0.95), 0.03, trans=1.0, ior=1.33)
BK_WATER = prim('cylinder', 'bucketwater', WATERM, parent=BUCKET_ROOT, loc=(0, 0, BK_H * 0.72), radius=BK_R * 0.86, depth=0.004, vertices=32)
print('bucket', round(BK_H, 3), round(BK_R, 3))
