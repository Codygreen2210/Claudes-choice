# ================================================================ the stone and its sled: a 2.5-ton limestone block (1.0 x 1.2 x 0.85 m, about a cubic
# metre) lashed onto a wooden sled with two runners curling up at the front, a plank deck ahead of the stone for the water man
WOOD = pbr('ph:rough_wood', 1.6, 'wood', 'Object', tint=(0.95, 0.80, 0.62), boxp=True)
STONEM = pbr('ph:rock_surface', 0.9, 'stone', 'Object', tint=(1.22, 1.12, 0.94), boxp=True, bump=0.7)
ROPEM = pbr('acg:Rope001', 9.0, 'rope', 'Object', tint=(1.0, 0.86, 0.62), boxp=True)
SLED = empty('sled')
RUN_X = 0.40; RUN_W = 0.12; RUN_H = 0.15; DECK_TOP = 0.28
def sweep_rect(name, path, w, h, x0, m, parent):
    """a beam of w (x) by h (normal to the path), swept along a (y, z) path; the path is the beam's bottom edge"""
    vs = []; fs = []; n = len(path)
    for i, (y_, z_) in enumerate(path):
        a_ = path[max(i - 1, 0)]; b_ = path[min(i + 1, n - 1)]; ty, tz = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(ty, tz); ny, nz = -tz / L_, ty / L_
        for dx, k in ((-w / 2, 0), (w / 2, 0), (w / 2, 1), (-w / 2, 1)): vs.append((x0 + dx, y_ + ny * h * k, z_ + nz * h * k))
    for i in range(n - 1):
        for k in range(4): k2 = (k + 1) % 4; fs.append((i * 4 + k, i * 4 + k2, (i + 1) * 4 + k2, (i + 1) * 4 + k))
    fs.append((0, 3, 2, 1)); fs.append(tuple((n - 1) * 4 + k for k in range(4)))
    return mesh(name, vs, fs, m, parent, smooth_=False)
RUN_PATH = [(-1.25, 0.0), (0.6, 0.0)] + [(0.6 + 0.42 * math.sin(R(90 * k / 8)), 0.40 * (1 - math.cos(R(90 * k / 8)))) for k in range(1, 9)]
RUNNERS = [sweep_rect(f'runner{s_}', RUN_PATH, RUN_W, RUN_H, s_ * RUN_X, WOOD, SLED) for s_ in (-1, 1)]
for o in RUNNERS: bevel(o, 0.012, 2)
for k, y_ in enumerate((-1.05, -0.62, -0.18, 0.26)):
    box(f'cross{k}', (RUN_X * 2 + 0.28, 0.13, 0.12), (0, y_, RUN_H + 0.06), WOOD, bv=0.01, parent=SLED)
for k in range(5):
    box(f'plank{k}', (RUN_X * 2 + 0.22, 0.105, 0.045), (0, 0.42 + k * 0.112, DECK_TOP - 0.02), WOOD, bv=0.008, parent=SLED)
box('frontbar', (RUN_X * 2 + 0.34, 0.11, 0.11), (0, 0.98, 0.30), WOOD, bv=0.012, parent=SLED)   # the ropes tie on here
for s_ in (-1, 1): box(f'peg{s_}', (0.05, 0.05, 0.22), (s_ * (RUN_X + 0.06), 0.98, 0.36), WOOD, bv=0.01, parent=SLED)
BLK_C = Vector((0, -0.42, DECK_TOP + 0.425)); BLK_S = (1.0, 1.2, 0.85)
BLOCK = box('block', BLK_S, BLK_C, STONEM, bv=0.035, parent=SLED)
# chisel marks: a little bump noise on the stone
try:
    nt = STONEM.node_tree; b_ = nt.nodes['Principled BSDF']; bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35
    nt.links.new(tnoise(nt, coord(nt, 'Object'), 9.0, 4.0), bp.inputs['Height'])
    nn = next((l.from_node for l in nt.links if l.to_socket == b_.inputs['Normal']), None)
    if nn: nt.links.new(nn.outputs['Normal'], bp.inputs['Normal'])
    nt.links.new(bp.outputs['Normal'], b_.inputs['Normal'])
except Exception as e_: print('stone bump skipped', e_)
# lashings: two rope bands round the stone and the cross beams
def band(name, y_, parent):
    hx, hz = BLK_S[0] / 2 + 0.015, BLK_S[2] / 2 + 0.015; z0 = BLK_C.z; pts = []
    for k in range(41):
        a_ = 2 * math.pi * k / 40; c_, s_ = math.cos(a_), math.sin(a_)
        r_ = 1.0 / max(abs(c_) / hx, abs(s_) / (hz + 0.12 * (s_ < 0))) ; pts.append((r_ * c_ * 0.995, y_, z0 + r_ * s_))
    return tube(name, pts, 0.016, ROPEM, parent, seg=8, caps=False)
for k, y_ in enumerate((-0.82, -0.02)): band(f'lash{k}', y_, SLED)
# a rope tube we can move every frame (same vertex count, new points)
class Rope:
    def __init__(self, name, n=24, r=0.017, seg=8):
        self.n, self.seg, self.r = n, seg, r
        self.o = tube(name, [(0, i * 0.1, 0) for i in range(n)], r, ROPEM, seg=seg, caps=True)
    def set(self, pts):
        pts = [Vector(p) for p in pts]; n, seg = self.n, self.seg
        # resample the polyline to n evenly spaced points
        L_ = [0.0]
        for i in range(1, len(pts)): L_.append(L_[-1] + (pts[i] - pts[i - 1]).length)
        tot = L_[-1] or 1.0; rs = []; j = 0
        for i in range(n):
            s_ = tot * i / (n - 1)
            while j < len(pts) - 2 and L_[j + 1] < s_: j += 1
            k = (s_ - L_[j]) / max(L_[j + 1] - L_[j], 1e-6); rs.append(pts[j].lerp(pts[j + 1], min(max(k, 0), 1)))
        T0 = (rs[1] - rs[0]).normalized(); up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized(); co = []
        for i in range(n):
            T = (rs[min(i + 1, n - 1)] - rs[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
            for k in range(seg): co.extend(rs[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * self.r)
        self.o.data.vertices.foreach_set('co', co); self.o.data.update()
def sag(a_, b_, droop, n=10):
    a_, b_ = Vector(a_), Vector(b_); return [a_.lerp(b_, i / (n - 1)) - Vector((0, 0, droop * 4 * (i / (n - 1)) * (1 - i / (n - 1)))) for i in range(n)]
# the water jar: a round clay jar with a short neck and two lug handles
CLAY = mat('clay', (0.42, 0.17, 0.08), 0.8); noisy(CLAY, 30.0, 0.2, 0.1)
try:   # two dark painted bands round the jar's shoulder
    nt = CLAY.node_tree; b_ = nt.nodes['Principled BSDF']; zz = sepz(nt, coord(nt, 'Object')).outputs['Z']
    bd = math_(nt, 'MAXIMUM', math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', zz, 0.075)), 0.012), math_(nt, 'LESS_THAN', math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', zz, 0.105)), 0.007))
    lk = next(l for l in nt.links if l.to_socket == b_.inputs['Base Color']); nt.links.new(mixc(nt, bd, lk.from_socket, (0.05, 0.03, 0.02)), b_.inputs['Base Color'])
except Exception as e_: print('jar bands skipped', e_)
JAR = lathe('jar', [(0.0, -0.19), (0.09, -0.185), (0.16, -0.12), (0.18, -0.02), (0.165, 0.07), (0.11, 0.14), (0.065, 0.17), (0.06, 0.21), (0.075, 0.225), (0.06, 0.23), (0.05, 0.20), (0.04, 0.0)], 32, CLAY)
for s_ in (-1, 1):
    tube(f'jarlug{s_}', [(s_ * 0.15, 0, 0.08), (s_ * 0.2, 0, 0.06), (s_ * 0.2, 0, 0.0), (s_ * 0.17, 0, -0.03)], 0.016, CLAY, JAR, seg=8)
JAR_MOUTH = Vector((0, 0, 0.23))              # in the jar's own space
WATERM = mat('water', (0.8, 0.9, 1.0), 0.03, trans=1.0, ior=1.33)
