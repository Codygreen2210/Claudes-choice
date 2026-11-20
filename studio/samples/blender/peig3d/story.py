# The Lake Peigneur disaster (Louisiana, November 20, 1980), told as a cardboard cut-out play on a Broadway stage (style a).
# The set is a cut-away: the lake on a deck up top, the salt mine under it on the stage floor. One continuous shot from the back of
# the house; the curtains part on frame one and close on the last, so it loops.
#   python3 story.py OUTDIR F0 F1 [--samples 24] [--scale 0.75] [--only f,f]   (the farm calls it this way)
import sys, os, math, random, json
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.join(HERE, 'art')
OUT, F0, F1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
def opt(k, d): return type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
SAMP = opt('--samples', 24); SC = opt('--scale', 0.75); ONLY = opt('--only', '')
FPS = 30; STYLE = 'a'
TM = json.load(open(os.path.join(HERE, 'times.json'))); B = TM['starts']; TOTAL = TM['total']; NF = int(round(TOTAL * FPS))
todo = [int(x) for x in ONLY.split(',')] if ONLY else list(range(F0, min(F1, NF)))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
bpy.ops.wm.read_factory_settings(use_empty=True); S = bpy.context.scene; S.render.fps = FPS
P.set_scene_dir(HERE)
R = math.radians
def clamp(x, a, b): return max(a, min(b, x))
def smooth(a, b, x): t = clamp((x - a) / (b - a), 0.0, 1.0); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def back_out(a, b, x, k=1.6):
    t = clamp((x - a) / (b - a), 0.0, 1.0) - 1.0; return 1.0 + t * t * ((k + 1) * t + k)
# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree, m.node_tree.nodes['Principled BSDF']
def flat(name, col, rough=0.8, emit=None, es=0.0):
    m, nt, b = node_mat(name); b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = es
    return m
def tex_mat(name, pid, scale, tint=(1, 1, 1), rough=None, bump=0.6, box=True):
    d = P._dir(pid); m, nt, b = node_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3; nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    def t(pats, nc):
        f = P._one(d, *pats)
        if not f: return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f, check_existing=True); n.image.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
        n.projection = 'BOX' if box else 'FLAT'; n.projection_blend = 0.3; nt.links.new(mp.outputs[0], n.inputs['Vector']); return n
    c = t(['*_diff_*.*', '*_Color.*'], False)
    if c:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        nt.links.new(c.outputs['Color'], mx.inputs['A']); mx.inputs['B'].default_value = (*tint, 1); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    r = t(['*_rough_*.*', '*_Roughness.*'], True)
    if r and rough is None: nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    elif rough is not None: b.inputs['Roughness'].default_value = rough
    n_ = t(['*_nor_gl_*.*', '*_NormalGL.*'], True)
    if n_:
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump; nt.links.new(n_.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m
BOARD = tex_mat('board', 'acg:Cardboard004', 1.4, (1.0, 0.95, 0.88), bump=0.5)
EDGE = tex_mat('edge', 'acg:Cardboard004', 6.0, (0.85, 0.72, 0.55), bump=1.2)       # the cut edge: corrugation
WOOD = tex_mat('wood', 'ph:old_wooden_floor_01', 0.5, (0.9, 0.8, 0.7))
FLOOR = tex_mat('floor', 'ph:old_wooden_floor_01', 0.22, (0.75, 0.62, 0.5))
VELVET = tex_mat('velvet', 'ph:velour_velvet', 0.8, (0.55, 0.06, 0.06), bump=0.8)
BLACK = flat('black', (0.01, 0.01, 0.01), 0.9)
GOLD = flat('gold', (0.75, 0.55, 0.2), 0.35); GOLD.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.8
TAPE = flat('tape', (0.55, 0.42, 0.28), 0.45)

def art_mat(name, img):
    """the painted face: the art image, with a white cut border (style a) or worn paint showing raw board (style b)"""
    m, nt, b = node_mat('art_' + name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(img, check_existing=True); it.interpolation = 'Cubic'
    it.extension = 'CLIP'; nt.links.new(tc.outputs['UV'], it.inputs['Vector'])
    base = (0.92, 0.9, 0.86) if STYLE == 'a' else (0.62, 0.48, 0.34)                  # what shows where the paint is not
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(it.outputs['Alpha'], mx.inputs['Factor']); mx.inputs['A'].default_value = (*base, 1)
    nt.links.new(it.outputs['Color'], mx.inputs['B']); col = mx.outputs['Result']
    if STYLE == 'b':
        # board grain under the paint, and worn patches where the brown board shows through
        mpb = nt.nodes.new('ShaderNodeMapping'); mpb.inputs['Scale'].default_value = (14.0, 1.2, 70.0); nt.links.new(tc.outputs['Object'], mpb.inputs['Vector'])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 6.0; nt.links.new(mpb.outputs[0], nz.inputs['Vector'])
        cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.64; cr.color_ramp.elements[1].position = 0.70; nt.links.new(nz.outputs['Fac'], cr.inputs['Fac'])
        m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; nt.links.new(cr.outputs['Color'], m2.inputs['Factor']); nt.links.new(col, m2.inputs['A']); m2.inputs['B'].default_value = (0.50, 0.37, 0.24, 1)
        m3 = nt.nodes.new('ShaderNodeMix'); m3.data_type = 'RGBA'; m3.blend_type = 'MULTIPLY'; m3.inputs['Factor'].default_value = 0.35
        n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 60.0; nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
        nt.links.new(m2.outputs['Result'], m3.inputs['A']); nt.links.new(n2.outputs['Color'], m3.inputs['B']); col = m3.outputs['Result']
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; nt.links.new(n2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
        b.inputs['Roughness'].default_value = 0.85
    else:
        b.inputs['Roughness'].default_value = 0.55; b.inputs['Coat Weight'].default_value = 0.08
    nt.links.new(col, b.inputs['Base Color']); return m

# ---------------------------------------------------------------- a cut-out: contour of the art's alpha (grown for a border), extruded, UV'd to the art
CONT = json.load(open(os.path.join(ART, 'contours.json')))[STYLE]
def cutout(name, img_name, height, loc, yaw=0.0, thick=None, brace=True):
    path = os.path.join(ART, img_name + '.png'); C = CONT[img_name]; H, W = C['H'], C['W']; k = height / H
    bm = bmesh.new(); vs = [bm.verts.new(((x - W / 2) * k, 0.0, (H - y) * k)) for x, y in C['pts']]
    f = bm.faces.new(vs); bm.normal_update()
    if f.normal.y > 0: f.normal_flip()
    uv = bm.loops.layers.uv.new('UV')
    for lp in f.loops: lp[uv].uv = (lp.vert.co.x / (W * k) + 0.5, lp.vert.co.z / (H * k))
    bmesh.ops.triangulate(bm, faces=[f]); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    o.data.materials.append(art_mat(name, path)); o.data.materials.append(BOARD); o.data.materials.append(EDGE)
    sol = o.modifiers.new('board', 'SOLIDIFY'); sol.thickness = thick or (0.012 if STYLE == 'a' else 0.014); sol.offset = 1.0
    sol.use_rim = True; sol.material_offset = 1; sol.material_offset_rim = 2
    o.location = loc; o.rotation_euler = (0, 0, yaw); o['h'] = height
    if brace:
        bh = min(height * 0.55, 1.1); br = mesh_tri(name + '_brace', bh); br.parent = o; br.location = (0, 0.012, 0.0)
        blk = box(name + '_block', (0.14, 0.24, 0.1), (0, 0.012 + bh * 0.42, 0.05), WOOD if STYLE == 'a' else BOARD); blk.parent = o
        if STYLE == 'b':
            t = box(name + '_tape', (0.06, 0.003, 0.14), (0.0, 0.010, 0.12), TAPE); t.parent = o
    return o
def mesh_tri(name, h):
    vs = [(0, 0, 0), (0, 0, h), (0, h * 0.75, 0)]; me = bpy.data.meshes.new(name); me.from_pydata(vs, [], [(0, 1, 2)]); me.update()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.data.materials.append(BOARD if STYLE == 'b' else WOOD)
    s = o.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.02; s.offset = 0.0; return o
def box(name, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m); return o
def cyl(name, r, h, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=32); o = bpy.context.object; o.name = name; o.data.materials.append(m); return o


# ---------------------------------------------------------------- the stage floor, painted backdrop, the theatre round it
OW, OH = 10.0, 7.4                                          # the proscenium opening
box('stage', (13.0, 8.5, 1.0), (0, 3.75, -0.5), FLOOR)
box('apron', (13.0, 0.06, 1.0), (0, -0.52, -0.5), flat('apronblack', (0.03, 0.025, 0.02), 0.9))
bdm, nt, b = node_mat('backdrop'); it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(os.path.join(ART, 'backdrop.png')); nt.links.new(it.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.95
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 7.2, 3.6), rotation=(R(90), 0, 0)); BD = bpy.context.object; BD.scale = (12.5, 7.2, 1); BD.data.materials.append(bdm)
bpy.ops.object.transform_apply(scale=True); sd = BD.modifiers.new('sub', 'SUBSURF'); sd.subdivision_type = 'SIMPLE'; sd.levels = sd.render_levels = 5
tx = bpy.data.textures.new('rip', 'CLOUDS'); tx.noise_scale = 1.6; dp = BD.modifiers.new('rip', 'DISPLACE'); dp.texture = tx; dp.strength = 0.08; dp.direction = 'Z'
WALLD = flat('housewall', (0.035, 0.02, 0.02), 0.9)
box('house_floor', (40, 30, 0.2), (0, -16, -1.3), flat('carpet', (0.12, 0.02, 0.025), 0.95)); box('house_back', (40, 0.2, 20), (0, -31, 6), WALLD)
for x in (-16, 16): box(f'house_side{x}', (0.2, 40, 20), (x, -8, 6), WALLD)
box('house_top', (40, 40, 0.2), (0, -8, 13), WALLD)
box('pit_wall', (13.0, 0.25, 1.5), (0, -1.1, -0.55), WALLD)
cyl('pit_rail', 0.035, 13.0, (0, -1.1, 0.25), GOLD, (0, R(90), 0))
# the audience: a few rows of dark heads and shoulders in front
SIL = flat('sil', (0.012, 0.01, 0.01), 0.9)
for row, (yy, zz) in enumerate(((-9.6, 1.05), (-10.6, 1.45), (-11.6, 1.85))):
    for k in range(9):
        x = -4.0 + k * 1.0 + (0.5 if row % 2 else 0.0) + 0.1 * math.sin(k * 3.1 + row)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, yy, zz + 0.45), segments=16, ring_count=10); h_ = bpy.context.object; h_.scale = (1, 1, 1.15); h_.data.materials.append(SIL)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(x, yy, zz + 0.12), segments=16, ring_count=10); s_ = bpy.context.object; s_.scale = (1.0, 0.6, 0.55); s_.data.materials.append(SIL)

# ---------------------------------------------------------------- the gilded proscenium: a U frame with an arched top, trims, marquee bulbs, the title plaque
GILT = flat('gilt', (0.83, 0.6, 0.24), 0.32); g = GILT.node_tree.nodes['Principled BSDF']; g.inputs['Metallic'].default_value = 1.0
gnt = GILT.node_tree; gtc = gnt.nodes.new('ShaderNodeTexCoord'); gn = gnt.nodes.new('ShaderNodeTexNoise'); gn.inputs['Scale'].default_value = 3.0; gn.inputs['Detail'].default_value = 10.0
gnt.links.new(gtc.outputs['Object'], gn.inputs['Vector']); gb = gnt.nodes.new('ShaderNodeBump'); gb.inputs['Strength'].default_value = 0.45; gnt.links.new(gn.outputs['Fac'], gb.inputs['Height']); gnt.links.new(gb.outputs['Normal'], g.inputs['Normal'])
FRAME_RED = flat('framered', (0.32, 0.03, 0.03), 0.55)
def arch_path(half, h, rise, n):
    """bottom-left up, over a shallow arch, down to bottom-right; n points evenly spaced"""
    pts = [(-half, 0.0), (-half, h)] + [(-half + 2 * half * i / 24, h + rise * math.sin(math.pi * i / 24)) for i in range(1, 24)] + [(half, h), (half, 0.0)]
    L = [0.0]
    for i in range(1, len(pts)): L.append(L[-1] + math.dist(pts[i], pts[i - 1]))
    out = []
    for j in range(n):
        s_ = L[-1] * j / (n - 1); i = max(k for k in range(len(L)) if L[k] <= s_ + 1e-9); i = min(i, len(pts) - 2); u = (s_ - L[i]) / max(L[i + 1] - L[i], 1e-9)
        out.append((lerp(pts[i][0], pts[i + 1][0], u), lerp(pts[i][1], pts[i + 1][1], u)))
    return out
def band(name, inner, outer, y0, depth, m):
    n = len(inner); vs = []; fs = []
    for (xi, zi), (xo, zo) in zip(inner, outer): vs += [(xi, y0, zi), (xo, y0, zo), (xo, y0 + depth, zo), (xi, y0 + depth, zi)]
    for i in range(n - 1):
        a_ = i * 4; b_ = a_ + 4
        fs += [(a_, a_ + 1, b_ + 1, b_), (a_ + 1, a_ + 2, b_ + 2, b_ + 1), (a_ + 3, a_, b_, b_ + 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update(); o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.data.materials.append(m); return o
NP = 120
IN = arch_path(OW / 2, OH, 0.9, NP); MID = arch_path(OW / 2 + 0.55, OH + 0.55, 0.95, NP); OUT_ = arch_path(OW / 2 + 1.7, OH + 1.7, 1.0, NP)
band('pros_gold', IN, MID, -0.75, 0.6, GILT); band('pros_red', MID, OUT_, -0.62, 0.5, FRAME_RED)
def tube_path(name, path, y, r, m):
    cv = bpy.data.curves.new(name, 'CURVE'); cv.dimensions = '3D'; sp = cv.splines.new('POLY'); sp.points.add(len(path) - 1)
    for p_, (x, z) in zip(sp.points, path): p_.co = (x, y, z, 1)
    cv.bevel_depth = r; cv.bevel_resolution = 3; o = bpy.data.objects.new(name, cv); S.collection.objects.link(o); o.data.materials.append(m); return o
tube_path('trim_in', IN, -0.78, 0.09, GILT); tube_path('trim_mid', MID, -0.78, 0.07, GILT); tube_path('trim_out', OUT_, -0.66, 0.1, GILT)
BULB_A = flat('bulb_a', (1, 0.9, 0.7), 0.3, (1.0, 0.78, 0.45), 8.0); BULB_B = flat('bulb_b', (1, 0.9, 0.7), 0.3, (1.0, 0.78, 0.45), 8.0)
BULBS = arch_path(OW / 2 + 0.28, OH + 0.28, 0.92, 44)
for k, (x, z) in enumerate(BULBS):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.075, location=(x, -0.83, z), segments=12, ring_count=8); o = bpy.context.object; o.data.materials.append(BULB_A if k % 2 else BULB_B)
box('plaque', (5.2, 0.12, 0.95), (0, -0.82, OH + 1.55), FRAME_RED)
tube_path('plaque_trim', [(-2.6, OH + 1.08), (-2.6, OH + 2.02), (2.6, OH + 2.02), (2.6, OH + 1.08), (-2.6, OH + 1.08)], -0.89, 0.05, GILT)
bpy.ops.object.text_add(location=(0, -0.9, OH + 1.38)); TX = bpy.context.object; TX.data.body = 'LAKE PEIGNEUR'; TX.data.align_x = 'CENTER'; TX.data.size = 0.5
TX.data.extrude = 0.02; TX.rotation_euler = (R(90), 0, 0); TX.data.materials.append(GILT)

# ---------------------------------------------------------------- the red velvet: a swagged valance and two traveler curtains that part
def drape_mat():
    m = tex_mat('velvet', 'ph:velour_velvet', 0.8, (0.62, 0.05, 0.05), bump=0.8)
    b_ = m.node_tree.nodes['Principled BSDF']; b_.inputs['Sheen Weight'].default_value = 0.6; b_.inputs['Sheen Tint'].default_value = (1.0, 0.45, 0.4, 1); return m
VEL = drape_mat()
FRINGE = GILT
NC = 140; NR = 8
class Drape:
    def __init__(self, name, side):
        self.side = side; vs = []; fs = []
        for j in range(NR + 1):
            for i in range(NC + 1): vs.append((0, 0, 0))
        for j in range(NR):
            for i in range(NC): a_ = j * (NC + 1) + i; fs.append((a_, a_ + 1, a_ + NC + 2, a_ + NC + 1))
        me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
        for p_ in me.polygons: p_.use_smooth = True
        self.o = bpy.data.objects.new(name, me); S.collection.objects.link(self.o); self.o.data.materials.append(VEL)
        s_ = self.o.modifiers.new('t', 'SOLIDIFY'); s_.thickness = 0.03
        cv = bpy.data.curves.new(name + '_fr', 'CURVE'); cv.dimensions = '3D'; sp = cv.splines.new('POLY'); sp.points.add(NC); cv.bevel_depth = 0.06; cv.bevel_resolution = 2
        self.fr = bpy.data.objects.new(name + '_fr', cv); S.collection.objects.link(self.fr); self.fr.data.materials.append(FRINGE); self.sp = sp
    def set(self, o_, t):
        """o_: 0 closed (inner edge at centre) .. 1 open (bunched at the side)"""
        outer = self.side * (OW / 2 + 0.4); inner = self.side * lerp(0.02, OW / 2 - 0.55, o_); w = abs(outer - inner)
        amp = 0.07 + 0.30 * (1 - w / (OW / 2 + 0.38)); pleats = 16
        co = []; frp = []
        for j in range(NR + 1):
            z = (OH + 1.2) * j / NR; flare = 1.0 + 0.10 * (1 - j / NR)         # a little fuller at the floor
            for i in range(NC + 1):
                u = i / NC; x = lerp(inner, outer, u)
                sway = 0.10 * math.sin(2.2 * t + u * 3) * (1 - j / NR) * smooth(0, 0.5, w) * (1 - smooth(2.4, 3.6, t))
                y = -0.35 + amp * flare * math.sin(u * pleats * 2 * math.pi) + sway * (1 - u)
                co += [x + self.side * 0.0, y, z]
                if j == 0: frp.append((x, y - 0.02, 0.06))
        self.o.data.vertices.foreach_set('co', co); self.o.data.update()
        for p_, (x, y, z) in zip(self.sp.points, frp): p_.co = (x, y, z, 1)
DRAPES = [Drape('drape_l', -1), Drape('drape_r', 1)]
# valance: three swags hanging under the arch, with fringe
vs = []; fs = []; n = 90
for j in range(2):
    for i in range(n + 1):
        u = i / n; x = (u - 0.5) * (OW + 0.6); sw = abs(math.sin(u * math.pi * 3)); top = OH + 1.0
        z = top if j else top - 0.55 - 0.75 * sw; y = -0.55 + 0.10 * math.sin(u * math.pi * 26) * (0.4 + sw)
        vs.append((x, y, z))
for i in range(n): fs.append((i, i + 1, n + 2 + i, n + 1 + i))
me = bpy.data.meshes.new('valance'); me.from_pydata(vs, [], fs); me.update(); VAL = bpy.data.objects.new('valance', me); S.collection.objects.link(VAL)
for p_ in me.polygons: p_.use_smooth = True
VAL.data.materials.append(VEL); s_ = VAL.modifiers.new('t', 'SOLIDIFY'); s_.thickness = 0.03
tube_path('valance_fr', [(v[0], v[2] - 0.03) for v in vs[:n + 1]], -0.58, 0.05, FRINGE).location.y = 0.0
# side legs (tied-back drapes framing the opening)
for sx in (-1, 1):
    vs = []; fs = []; n = 30
    for j in range(2):
        for i in range(n + 1):
            u = i / n; z = (OH + 1.0) * j; x = sx * (OW / 2 + 0.1 - 0.9 * u * (1.0 if j else 0.55)); y = -0.6 + 0.12 * math.sin(u * math.pi * 9)
            vs.append((x, y, z))
    for i in range(n): fs.append((i, i + 1, n + 2 + i, n + 1 + i))
    me = bpy.data.meshes.new('leg'); me.from_pydata(vs, [], fs); me.update(); o = bpy.data.objects.new('leg', me); S.collection.objects.link(o)
    for p_ in me.polygons: p_.use_smooth = True
    o.data.materials.append(VEL); s_ = o.modifiers.new('t', 'SOLIDIFY'); s_.thickness = 0.03
    tube_path(f'tie{sx}', [(sx * (OW / 2 - 0.1), 2.4), (sx * (OW / 2 - 0.9), 2.5)], -0.7, 0.06, GILT)
# footlights
for k in range(13):
    x = -5.4 + k * 0.9; box(f'hood{k}', (0.34, 0.16, 0.12), (x, -0.32, 0.06), BLACK)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.06, location=(x, -0.26, 0.08), rotation=(R(90), 0, 0)); bpy.context.object.data.materials.append(BULB_A)

# ---------------------------------------------------------------- lights: front-of-house keys, top wash, a backdrop wash, two followspot beams through the haze
P.hdri('ph:theater_01', 0.10, 0)
def spot(name, loc, aim, power, col, size=R(28), blend=0.4, rad=0.9):
    L = bpy.data.lights.new(name, 'SPOT'); L.energy = power; L.color = col; L.spot_size = size; L.spot_blend = blend; L.shadow_soft_size = rad
    o = bpy.data.objects.new(name, L); S.collection.objects.link(o); o.location = loc
    d = Vector(aim) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); return o
spot('key_l', (-6.0, -9.0, 8.0), (-1.0, 2.5, 1.0), 22000, (1.0, 0.86, 0.68))
spot('key_r', (6.0, -9.0, 8.5), (2.5, 2.5, 1.0), 16000, (1.0, 0.9, 0.76))
spot('top', (0.0, 3.0, 9.0), (0.0, 3.5, 0.0), 3000, (0.75, 0.82, 1.0), R(70), 0.6, 1.0)
spot('drop', (0.0, 1.0, 9.5), (0.0, 7.1, 3.5), 9000, (1.0, 0.95, 0.85), R(100), 0.9, 2.0)
spot('house', (0.0, -6.0, 11.5), (0.0, -0.8, 5.0), 9000, (1.0, 0.8, 0.6), R(60), 0.7, 1.5)                 # lights the arch and curtains
L = bpy.data.lights.new('foot', 'AREA'); L.shape = 'RECTANGLE'; L.size = 11.0; L.size_y = 0.2; L.energy = 600; L.color = (1.0, 0.75, 0.45)
fo = bpy.data.objects.new('foot', L); S.collection.objects.link(fo); fo.location = (0, -0.2, 0.2); fo.rotation_euler = (R(-70), 0, 0)
BEAM = bpy.data.materials.new('beam'); BEAM.use_nodes = True; bn = BEAM.node_tree; out_ = bn.nodes['Material Output']
for n_ in list(bn.nodes):
    if n_.type == 'BSDF_PRINCIPLED': bn.nodes.remove(n_)
lw = bn.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
em = bn.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.93, 0.78, 1); em.inputs['Strength'].default_value = 0.35
tr = bn.nodes.new('ShaderNodeBsdfTransparent'); mx = bn.nodes.new('ShaderNodeMixShader')
inv = bn.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; bn.links.new(lw.outputs['Facing'], inv.inputs[1])
pw = bn.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; bn.links.new(inv.outputs[0], pw.inputs[0]); pw.inputs[1].default_value = 2.0
bn.links.new(pw.outputs[0], mx.inputs['Fac']); bn.links.new(tr.outputs[0], mx.inputs[1]); bn.links.new(em.outputs[0], mx.inputs[2]); bn.links.new(mx.outputs[0], out_.inputs['Surface'])
def beam(name, src, dst, r1):
    d = Vector(dst) - Vector(src); L_ = d.length
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=r1, radius2=0.08, depth=L_, location=(Vector(src) + Vector(dst)) / 2); o = bpy.context.object; o.name = name
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); o.data.materials.append(BEAM)
    for p_ in o.data.polygons: p_.use_smooth = True
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; return o
BEAMS = []                                                         # (cone beams read as grey haze in tests; light only)
FS = [spot('follow_l', (-7.5, -12.0, 10.5), (-0.2, 1.6, 0.9), 14000, (1.0, 0.95, 0.85), R(7), 0.3, 0.2),
      spot('follow_r', (7.5, -12.0, 10.5), (1.25, 1.75, 0.9), 14000, (1.0, 0.95, 0.85), R(7), 0.3, 0.2)]



# ---------------------------------------------------------------- the set: a slab between the lake (on top) and the salt mine (under it)
TOP, BOT = 3.3, 2.6                                           # slab top (lake bed / land) and bottom (the mine's ceiling)
MUD = tex_mat('mud', 'acg:Cardboard004', 1.4, (0.55, 0.42, 0.3), bump=0.5)
GRASS = tex_mat('grass', 'acg:Cardboard004', 1.4, (0.45, 0.62, 0.36), bump=0.5)
SALTM = tex_mat('saltceil', 'acg:Cardboard004', 1.4, (0.86, 0.84, 0.8), bump=0.5)
def slab(name, x0, x1, top_m, art):
    o = box(name, (x1 - x0, 6.65, TOP - BOT), ((x0 + x1) / 2, 3.875, (TOP + BOT) / 2), top_m)
    o.data.materials.append(SALTM)
    for p_ in o.data.polygons:
        if p_.normal.z < -0.5: p_.material_index = 1          # the mine's ceiling is salt
    f = cutout(name + '_face', art, TOP - BOT, ((x0 + x1) / 2, 0.545, BOT), brace=False); return o, f
SL = slab('slab_l', -6.6, -4.6, GRASS, 'strata_l'); SM = slab('slab_m', -3.4, -1.0, GRASS, 'strata_m'); SR_ = slab('slab_r', 2.8, 6.6, MUD, 'strata_r')
HINGE = bpy.data.objects.new('hinge', None); S.collection.objects.link(HINGE); HINGE.location = (-1.0, 0.0, TOP)
TD, TDF = slab('slab_d', -1.0, 2.8, MUD, 'strata_d')
for o in (TD, TDF): o.parent = HINGE; o.location -= HINGE.location
# the mine: salt pillars, work lights on the ceiling
for k, (x, y) in enumerate(((-5.4, 4.9), (-1.9, 5.3), (2.1, 4.8), (5.3, 5.2))): cutout(f'pillar{k}', 'pillar', BOT, (x, y, 0.0), brace=False)
for k, x in enumerate((-3.0, 0.0, 3.2)):
    L_ = bpy.data.lights.new(f'mine{k}', 'POINT'); L_.energy = 260; L_.color = (1.0, 0.86, 0.62); L_.shadow_soft_size = 0.3
    o = bpy.data.objects.new(f'mine{k}', L_); S.collection.objects.link(o); o.location = (x, 2.2, BOT - 0.25)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(x, 2.2, BOT - 0.12), segments=12, ring_count=8); bpy.context.object.data.materials.append(BULB_A)
    cyl(f'cord{k}', 0.01, 0.12, (x, 2.2, BOT - 0.04), BLACK)
# the shaft: guide posts, the cage (floor + front grille, roof, cable), the headframe on top
for k, x in enumerate((-4.56, -3.44)): box(f'guide{k}', (0.07, 0.07, 5.6), (x, 1.32, 2.8), flat('guide', (0.3, 0.32, 0.35), 0.5))
HEAD = cutout('headframe', 'headframe', 2.4, (-4.0, 1.75, TOP), brace=False)
CAGE = cutout('cage', 'lift', 0.64, (-4.0, 1.25, 0.0), brace=False)
ROOF = cutout('cageroof', 'liftroof', 0.2, (0, 0, 0), brace=False); ROOF.parent = CAGE; ROOF.location = (0, 0.1, 1.8)
CABLE = cyl('cable', 0.012, 6.0, (0, 0, 0), BLACK); CABLE.parent = CAGE; CABLE.location = (0, 0.1, 4.95)
# land on top: live oaks, the sign
for k, (x, y, h) in enumerate(((-5.6, 5.4, 2.3), (-2.3, 5.9, 2.1), (-5.3, 3.4, 1.4))): cutout(f'oak{k}', 'oak', h, (x, y, TOP))
SIGN10 = cutout('sign10', 'sign10', 2.3, (-2.2, 3.3, TOP)); SIGN200 = cutout('sign200', 'sign200', 2.3, (-2.2, 3.3, TOP))
# the lake: rows of waves, the canal on the right, the rig with its crew, a second rig, barges, a tug, a bit of island
ROWS = [cutout(f'wave{k}', 'waves' if k % 2 else 'waves2', 0.32, (1.9 + 0.3 * k, y, TOP), brace=False) for k, y in enumerate((5.4, 4.0, 2.6, 1.15))]
CANAL = [cutout(f'canal{k}', 'canal', 0.3, (9.0, y, TOP), brace=False) for k, y in enumerate((3.4, 1.9))]
RIG = cutout('rig', 'rig', 2.6, (0.8, 3.05, TOP), brace=False)
PIPE_X = 0.8 + (425 / 1000 - 0.5) * 2.6 * 1000 / 1800
PIPE = cyl('pipe', 0.04, 1.0, (PIPE_X, 3.05, 0), flat('pipe', (0.35, 0.35, 0.38), 0.4))
BIT = bpy.ops.mesh.primitive_cone_add(radius1=0.09, radius2=0.0, depth=0.22, location=(0, 0, 0), rotation=(math.pi, 0, 0)); BIT = bpy.context.object; BIT.data.materials.append(flat('bit', (0.55, 0.5, 0.42), 0.35))
CREW = [cutout(f'crew{k}', 'roughneck', 0.62, (0, 0, 0), brace=False) for k in range(2)]
for k, c in enumerate(CREW): c.parent = RIG; c.location = (0.32 + 0.22 * k, -0.06, 0.55)
SKIFF = cutout('skiff', 'skiff', 0.24, (2.1, 1.75, TOP - 0.02), brace=False)
RIG2 = cutout('rig2', 'rig', 1.9, (3.9, 5.0, TOP), brace=False)
BARGES = [cutout(f'barge{k}', 'barge', 0.3, (x, y, TOP), brace=False) for k, (x, y) in enumerate(((2.4, 1.85), (3.6, 3.3), (-0.2, 4.6), (1.9, 4.5)))]
TUG = cutout('tug', 'tug', 0.5, (3.8, 2.1, TOP), brace=False)
ISLE = cutout('isle', 'island', 0.75, (-0.6, 2.3, TOP - 0.05), brace=False)
MATH = cutout('math', 'mathcard', 0.85, (2.05, 1.45, TOP))
WHIRL = bpy.data.objects.new('whirl_pivot', None); S.collection.objects.link(WHIRL); WHIRL.location = (0.8, 3.3, TOP + 0.03)
WD = 4.4; WDISC = cutout('whirl', 'whirl', WD, (0, 0, 0), brace=False); WDISC.parent = WHIRL; WDISC.rotation_euler = (R(-90), 0, 0); WDISC.location = (0, -WD / 2, 0)
# water in the mine: falling sheets (scrolling), flood water that rises, the refill over the crater, splash and dust
def fall_mat(o):
    nt = o.data.materials[0].node_tree; it = [n_ for n_ in nt.nodes if n_.type == 'TEX_IMAGE'][0]; it.extension = 'REPEAT'
    tc = [n_ for n_ in nt.nodes if n_.type == 'TEX_COORD'][0]; mp = nt.nodes.new('ShaderNodeMapping'); nt.links.new(tc.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], it.inputs['Vector'])
    b_ = nt.nodes['Principled BSDF']; b_.inputs['Emission Color'].default_value = (0.5, 0.75, 0.9, 1); b_.inputs['Emission Strength'].default_value = 0.15
    return mp
FALL1 = cutout('fall1', 'fallwater', BOT, (PIPE_X, 3.0, 0.0), brace=False); FM1 = fall_mat(FALL1)
FALL2 = cutout('fall2', 'fallwater', TOP + 0.05, (2.62, 2.2, 0.0), brace=False); FM2 = fall_mat(FALL2)
FLOOD = [cutout(f'flood{k}', 'tallwater', 3.6, (0.0, y, -3.6), brace=False) for k, y in enumerate((0.8, 4.3))]
REFILL = cutout('refill', 'tallwater', 3.6, (0.9, 0.62, -3.6), brace=False); REFILL.scale.x = 4.0 / 10.8
SPLASH = [cutout(f'splash{k}', 'splash', 0.45, (0, 0, 0), brace=False) for k in range(3)]
DUST = [cutout(f'dust{k}', 'dust', 0.45, (0, 0, 0), brace=False) for k in range(6)]
for o in SPLASH + DUST + [FALL1, FALL2]: o.visible_shadow = False          # no dark splash-shaped shadows on the falling water
# the miners: at work with picks, running, and (at the end, up top) cheering
MPOS = [(-2.3, 1.85), (-1.45, 2.45), (-0.55, 1.9), (1.7, 2.5)]
MINE_W = [cutout(f'minerw{k}', 'miner', 1.55, (x, y, 0.0)) for k, (x, y) in enumerate(MPOS)]
MINE_R = [cutout(f'minerr{k}', 'miner_run', 1.55, (x, y, 0.0)) for k, (x, y) in enumerate(MPOS)]
MINE_U = [cutout(f'mineru{k}', 'miner_up', 1.55, (0, 0, 0)) for k in range(4)]
INCAGE = [(-4.32, 1.62), (-4.1, 1.45), (-3.9, 1.62), (-3.68, 1.45)]
ONTOP = [(-3.05, 1.55), (-2.5, 2.05), (-1.95, 1.55), (-1.4, 2.05)]
for k, (x, y) in enumerate(INCAGE): pass

# ---------------------------------------------------------------- timing
PUNCH = B[3] + 1.0                       # the drill comes through the ceiling
TIP = B[3] + 2.6                         # the rig starts to lean
JUMP = B[4] + 0.5; ROLL = B[4] + 1.6     # the crew jumps to the skiff; the rig rolls over
POUR = B[5] + 0.15; RUN = B[5] + 0.9; BOARD = B[5] + 2.5; LIFT0, LIFT1 = B[5] + 2.9, B[6] + 1.0
SWIRL = B[6] + 0.3
SWALLOW = [(RIG2, B[6] + 3.0), (TUG, B[6] + 3.6), (BARGES[0], B[6] + 4.1), (BARGES[1], B[6] + 4.4), (BARGES[2], B[6] + 4.7), (BARGES[3], B[6] + 5.0), (ISLE, B[6] + 5.5)]
GONE = B[7] + 0.8; DROP = B[7] + 0.95
CANAL_IN = B[8] + 0.5; FALLS = B[8] + 1.5
REFILL0 = B[9] + 0.05; POP = [B[9] + 1.5, B[9] + 1.8, B[9] + 2.1, B[9] + 2.45]
CHEER = B[10] + 0.1; FLIP = B[10] + 2.75; BOWT = B[11] + 0.7
POPSPOT = [(0.2, 1.75), (1.4, 3.0), (2.5, 1.95), (3.4, 4.1)]

def hide(o, v):
    o.hide_render = v
    for c in o.children: hide(c, v)
def spiral(o, home, t0, t, dur=1.7):
    """caught by the whirlpool: round and round, in to the middle, and down"""
    u = clamp((t - t0) / dur, 0, 1)
    if u <= 0: return False
    cx, cy = WHIRL.location.x, WHIRL.location.y; dx, dy = home.x - cx, home.y - cy; r0 = math.hypot(dx, dy); a0 = math.atan2(dy, dx)
    r = r0 * (1 - u) ** 1.3; a = a0 + 9.0 * u ** 1.5
    o.location = (cx + r * math.cos(a), cy + r * math.sin(a) * 0.75, home.z - o['h'] * 1.05 * smooth(0.55, 1.0, u))
    o.rotation_euler.y = R(25) * math.sin(u * 20) * u
    return u >= 1
def frame(f):
    t = f / FPS; S.frame_set(f)
    o_ = lerp(0.06, 1.0, smooth(0.0, 2.6, t)) * (1 - smooth(B[11] + 0.9, TOTAL, t)) + 0.06 * smooth(B[11] + 0.9, TOTAL, t)
    for d_ in DRAPES: d_.set(o_, t)
    chase = int(t * 6) % 2
    BULB_A.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 9.0 if chase else 3.0
    BULB_B.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0 if chase else 9.0
    # ---- the lake: waves bob; they sink as the whirlpool takes the water, and come back when it refills
    drain = smooth(SWIRL, GONE, t) * (1 - smooth(REFILL0 + 0.5, REFILL0 + 1.3, t))
    for k, w_ in enumerate(ROWS):
        w_.location.z = TOP + 0.025 * math.sin(t * 2.2 + k * 1.3) - 0.36 * drain; hide(w_, drain > 0.97)
        w_.location.x = 1.9 + 0.3 * k + 0.06 * math.sin(t * 0.7 + k)
    for k, c_ in enumerate(CANAL):
        u = smooth(CANAL_IN + 0.2 * k, CANAL_IN + 1.4 + 0.2 * k, t); c_.location = (lerp(9.5, 6.3, u) + 0.05 * math.sin(t * 3 + k), c_.location.y, TOP + 0.02 * math.sin(t * 2.5 + k)); hide(c_, u <= 0)
    # ---- the rig: drilling, leaning, rolling over and sinking; its crew jumps into the skiff, which runs off
    lean = R(7) * smooth(TIP, TIP + 0.8, t) + R(1.2) * math.sin(t * 13) * (t > TIP); roll = R(88) * smooth(ROLL, ROLL + 1.1, t) ** 1.6
    RIG.rotation_euler.y = lean + roll + R(0.4) * math.sin(t * 31) * (t < PUNCH)
    RIG.location.z = TOP + 0.02 * math.sin(t * 2.0) - 0.75 * smooth(ROLL + 1.0, ROLL + 2.0, t); hide(RIG, t > ROLL + 2.0)
    for k, c in enumerate(CREW):
        tj = JUMP + 0.25 * k; u = clamp((t - tj) / 0.55, 0, 1)
        if u <= 0: c.parent = RIG; c.location = (0.32 + 0.22 * k, -0.06, 0.55); hide(c, RIG.hide_render); continue
        bpy.context.view_layer.update()
        c.parent = None; p0 = Vector((RIG.location.x + 0.32 + 0.22 * k, RIG.location.y - 0.06, TOP + 0.55)) if u < 1 else None
        p1 = SKIFF.location + Vector((-0.12 + 0.24 * k, -0.04, 0.1))
        if u < 1: c.location = p0.lerp(p1, u) + Vector((0, 0, 0.7 * math.sin(math.pi * u))); c.rotation_euler.y = R(-30) * math.sin(math.pi * u)
        else: c.location = p1; c.rotation_euler.y = 0
        hide(c, False)
    us = smooth(JUMP + 1.0, JUMP + 2.6, t); SKIFF.location = (2.1 + 7.0 * us ** 1.5, 1.75, TOP - 0.02 + abs(math.sin(t * 9)) * 0.04 * (0 < us < 1))
    SKIFF.rotation_euler.y = R(-6) * (0 < us < 1); hide(SKIFF, us >= 1)
    for k, c in enumerate(CREW):
        if t > JUMP + 0.25 * k + 0.55: c.location = SKIFF.location + Vector((-0.12 + 0.24 * k, -0.04, 0.1)); hide(c, us >= 1)
    # the pipe: down through the slab, its bit punches out of the mine's ceiling
    tip = lerp(TOP - 0.1, BOT - 0.75, back_out(PUNCH, PUNCH + 0.35, t, 1.0)); tip = min(tip, TOP - 0.1) if t < PUNCH else tip
    ptop = TOP + 0.6 if t < ROLL else TOP - 0.05; PIPE.scale.z = (ptop - tip); PIPE.location.z = (ptop + tip) / 2; BIT.location = (PIPE_X, 3.05, tip - 0.08)
    BIT.rotation_euler.z = t * 20; hide(PIPE, t > POUR + 0.6); hide(BIT, t > POUR + 0.6)
    # the math card pops up next to the rig and goes again
    um = back_out(B[2] + 0.9, B[2] + 1.3, t, 1.4) * (1 - smooth(B[3] + 0.2, B[3] + 0.6, t)); MATH.location.z = TOP - 1.0 + 1.0 * um
    MATH.rotation_euler.y = R(4) * math.sin(t * 5); hide(MATH, um <= 0.01)
    # ---- the whirlpool: grows and spins, everything goes round and down, then it is gone with the lake
    gw = smooth(SWIRL, SWIRL + 2.0, t) * (1 - smooth(GONE - 0.6, GONE, t)); WHIRL.scale = (max(gw, 1e-3),) * 3; WHIRL.rotation_euler.z = -1.6 * t - 2.0 * max(0, t - SWIRL) ** 1.3
    hide(WDISC, gw <= 0.01)
    for o, t0 in SWALLOW:
        home = o.get('home')
        if home is None: o['home'] = list(o.location); home = o['home']
        done = spiral(o, Vector(home), t0, t)
        if t < t0: o.location = Vector(home) + Vector((0.08 * math.sin(t * 0.8 + o['h'] * 7), 0, 0.02 * math.sin(t * 2.2 + o['h'] * 9))); o.rotation_euler.y = R(1.5) * math.sin(t * 1.7 + o['h'] * 5)
        hide(o, done and t < REFILL0)
    # barges pop back up like corks once it refills (the tug, rigs and the island stay down)
    for k, b_ in enumerate(BARGES):
        if t >= REFILL0:
            x, y = POPSPOT[k]; u = back_out(POP[k], POP[k] + 0.4, t, 2.6); hide(b_, t < POP[k])
            b_.location = (x, y, TOP - 0.35 + 0.5 * u + 0.025 * math.sin(t * 3 + k) * (t > POP[k] + 0.4)); b_.rotation_euler.y = R(10) * math.exp(-max(0, t - POP[k] - 0.4) * 3) * math.sin(t * 14)
    for o in (RIG2, TUG, ISLE): hide(o, o.hide_render or t >= REFILL0)
    # ---- the slab over the lake bed caves into the mine
    HINGE.rotation_euler.y = R(48) * clamp(back_out(DROP, DROP + 0.7, t, 0.9), 0, 1.05)
    # ---- water in the mine: pours from the hole, then the canal's waterfall; flood rises; the crater refills
    uf = smooth(POUR, POUR + 0.6, t) * (1 - smooth(GONE + 0.3, GONE + 0.9, t)); FALL1.scale = (max(uf, 1e-3), 1, 1); hide(FALL1, uf <= 0.01); FM1.inputs['Location'].default_value[1] = t * 1.6
    u2 = smooth(FALLS, FALLS + 0.8, t) * (1 - smooth(REFILL0 + 0.6, REFILL0 + 1.2, t)); FALL2.scale = (lerp(0.6, 1.0, u2), 1, max(u2, 1e-3)); FALL2.location.z = (TOP + 0.05) * (1 - u2)
    hide(FALL2, u2 <= 0.01); FM2.inputs['Location'].default_value[1] = t * 2.2
    lvl = (0.55 * smooth(POUR + 0.3, B[6] + 0.3, t) + 0.9 * smooth(B[6] + 0.3, GONE, t) + 0.75 * smooth(FALLS + 0.4, REFILL0, t))   # top of the flood
    for k, fl in enumerate(FLOOD): fl.location.z = -3.6 + lvl + 0.03 * math.sin(t * 2 + k); hide(fl, lvl < 0.02)
    ur = smooth(REFILL0, REFILL0 + 1.3, t); REFILL.location.z = -3.6 + lerp(2.2, 3.62, ur) + 0.02 * math.sin(t * 2.4); hide(REFILL, ur <= 0)
    for k, s_ in enumerate(SPLASH):
        on = (POUR + 0.4 < t < GONE + 0.6) if k == 0 else (FALLS + 0.6 < t < REFILL0 + 0.9)
        hide(s_, not on)
        if on:
            x = PIPE_X if k == 0 else 2.62 + (k - 1.5) * 0.35; s_.location = (x, 2.9 if k == 0 else 2.1, max(lvl, 0.0) - 0.08 + 0.04 * math.sin(t * 17 + k)); s_.scale = (1.0 + 0.2 * math.sin(t * 11 + k), 1, 0.8 + 0.3 * abs(math.sin(t * 9 + k)))
    for k, d_ in enumerate(DUST):
        for t0, x, z in ((PUNCH, PIPE_X, BOT - 0.35), (DROP + 0.45, -0.2 + 0.7 * (k % 3), TOP - 0.2)):
            uu = (t - t0 - 0.06 * k) / 0.8
            if 0 < uu < 1: d_.location = (x + 0.25 * (k - 2.5) * uu, 2.6 + 0.1 * k, z - 0.4 * uu * (t0 == PUNCH)); sc_ = 0.35 if t0 == PUNCH else 1.0; d_.scale = ((0.5 + 0.8 * uu) * sc_, 1, (0.5 + 0.8 * uu) * sc_); break
        else: uu = -1
        hide(d_, not (0 < uu < 1))
    # ---- the miners: at work; look up when the drill comes through; run for the cage; ride up; cheer on the bank; bow
    bpy.context.view_layer.update()
    cz = TOP * smooth(LIFT0, LIFT1, t); CAGE.location.z = cz
    for k in range(4):
        w_, r_, u_ = MINE_W[k], MINE_R[k], MINE_U[k]; x0, y0 = MPOS[k]
        hide(w_, t >= RUN); hide(r_, not (RUN <= t < CHEER)); hide(u_, t < CHEER)
        if t < RUN:
            w_.rotation_euler.y = R(7) * math.sin(t * 5 + k * 1.9) * (t < PUNCH) + R(-5) * (t >= PUNCH)
            w_.location.z = 0.12 * abs(math.sin((t - PUNCH) * 9)) * (PUNCH < t < PUNCH + 0.5)
            w_.scale.x = -1 if (t > PUNCH + 0.2 and k % 2) else 1
        elif t < CHEER:
            tb = RUN + 0.25 * k; ub = smooth(tb, BOARD, t); cx, cy = INCAGE[k]
            if t < LIFT1 + 0.2:
                r_.location = (lerp(x0, cx, ub), lerp(y0, cy, ub), abs(math.sin(t * 10 + k)) * 0.08 * (0 < ub < 1) + cz * (t >= BOARD))
                r_.scale.x = -1 if ub < 1 else 1; r_.rotation_euler.y = R(-8) * (0 < ub < 1)
            else:                                                                                   # off the cage onto the bank
                uo = smooth(LIFT1 + 0.2 + 0.2 * k, LIFT1 + 1.2 + 0.2 * k, t); ox, oy = ONTOP[k]
                r_.location = (lerp(cx, ox, uo), lerp(cy, oy, uo), TOP + abs(math.sin(t * 10 + k)) * 0.08 * (0 < uo < 1)); r_.scale.x = 1 if ox > cx else -1; r_.rotation_euler.y = 0
        else:
            ox, oy = ONTOP[k]; u_.location = (ox, oy, TOP + abs(math.sin(t * 7 + k * 0.8)) * 0.12 * (t < BOWT)); u_.rotation_euler.y = R(4) * math.sin(t * 6 + k)
            bw = smooth(BOWT + 0.08 * k, BOWT + 0.35 + 0.08 * k, t) * (1 - smooth(BOWT + 0.9, BOWT + 1.2, t)); u_.rotation_euler.x = R(24) * bw
    # the depth sign pops up on the bank and flips from 10 to 200
    us_ = back_out(CHEER + 0.4, CHEER + 0.8, t, 1.6); fl_ = clamp((t - FLIP) / 0.35, 0, 1)
    for sg_, on in ((SIGN10, fl_ < 0.5), (SIGN200, fl_ >= 0.5)):
        hide(sg_, us_ <= 0.01 or not on); sg_.location.z = TOP - 2.3 + 2.3 * us_; sg_.scale.x = max(abs(math.cos(math.pi * fl_)), 0.02) if 0 < fl_ < 1 else 1
    # followspots: on the miners for the cheer and the bow
    fu = smooth(CHEER, CHEER + 0.6, t) * (1 - smooth(B[11] + 1.2, B[11] + 2.2, t))
    for k, l_ in enumerate(FS):
        l_.data.energy = 9000 * fu; l_.rotation_euler = (Vector((-5.5 if k == 0 else -2.7, 1.8, TOP + 0.9)) - l_.location).to_track_quat('-Z', 'Y').to_euler()
    # ---- camera: one shot; rests on each beat (about half the time); lens 18 mm across a 36 mm tall sensor
    def SH(x, z, h, y=2.4, lens=28, up=0.3):
        dist = h / 2 * lens / 18.0; return ((x, y - dist, z + up), (x, y, z), lens)
    K = [(0.0, (0.0, -13.8, 3.2), (0.0, 3.0, 3.3), 22),
         (3.0, *SH(-1.0, 1.45, 4.0, 2.1)), (B[1] - 0.3, *SH(-0.85, 1.45, 4.0, 2.1)),          # the miners at work
         (B[1] + 1.2, *SH(1.0, 4.55, 3.4, 2.9)), (B[2] - 0.2, *SH(1.1, 4.5, 3.4, 2.9)),      # the rig on the lake
         (B[2] + 0.8, *SH(1.0, 3.0, 6.4, 2.6)), (PUNCH - 0.5, *SH(0.9, 3.0, 6.4, 2.6)),       # both at once: the drill is headed down
         (PUNCH + 0.2, *SH(0.05, 1.75, 3.5, 2.6)), (TIP - 0.6, *SH(0.1, 1.75, 3.5, 2.6)),      # through the ceiling
         (TIP + 0.4, *SH(1.2, 4.5, 3.6, 2.8)), (B[5] - 0.3, *SH(1.5, 4.4, 3.6, 2.8)),       # the rig tips, the crew jumps, it rolls and sinks
         (B[5] + 0.8, *SH(-0.5, 1.55, 4.2, 2.2)), (B[5] + 2.4, *SH(-0.9, 1.55, 4.2, 2.2)),  # the lake pours in, run for the cage
         (B[5] + 3.4, *SH(-3.6, 2.6, 5.4, 1.8)), (B[6] + 0.9, *SH(-3.6, 2.9, 5.4, 1.8)),     # the cage goes up
         (B[6] + 2.0, (1.0, -2.2, 7.3), (1.1, 3.5, 3.3), 30), (B[7] - 0.2, (1.1, -2.1, 7.2), (1.1, 3.5, 3.3), 30),   # the whirlpool from above
         (B[7] + 0.7, *SH(0.8, 3.0, 7.0, 2.4)), (B[8] + 0.7, *SH(0.9, 3.0, 7.0, 2.4)),       # the lake is gone; the bed caves in
         (B[8] + 1.6, *SH(2.4, 2.9, 5.6, 2.4)), (B[9] - 0.1, *SH(2.5, 2.9, 5.6, 2.4)),       # the canal runs backward: a waterfall
         (B[9] + 1.0, *SH(1.6, 3.95, 3.6, 2.8)), (B[10] - 0.3, *SH(1.7, 3.95, 3.6, 2.8)),   # it refills; the barges pop up
         (B[10] + 0.8, *SH(-2.25, 4.3, 4.0, 2.0)), (B[11] + 0.2, *SH(-2.2, 4.3, 4.0, 2.0)), # the miners on the bank, the depth sign
         (B[11] + 1.6, *SH(-2.0, 4.1, 5.0, 2.0)),
         (TOTAL, (0.0, -13.8, 3.2), (0.0, 3.0, 3.3), 22)]
    i = max(j for j in range(len(K)) if K[j][0] <= t); i = min(i, len(K) - 2); u = smooth(K[i][0], K[i + 1][0], t)
    cp = Vector(K[i][1]).lerp(Vector(K[i + 1][1]), u); ct = Vector(K[i][2]).lerp(Vector(K[i + 1][2]), u); lens = lerp(K[i][3], K[i + 1][3], u)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = Vector(q_[0:3]), Vector(q_[3:6]), q_[6]
    CAM.location = cp; CAM.rotation_euler = (ct - cp).to_track_quat('-Z', 'Y').to_euler(); CAM.data.lens = lens; CAM.data.dof.focus_distance = (ct - cp).length
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.dof.use_dof = True; CAM.data.dof.aperture_fstop = 11
S.render.engine = 'CYCLES'; S.cycles.samples = SAMP; S.cycles.use_denoising = True; S.cycles.device = 'CPU'
try: S.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
S.cycles.transparent_max_bounces = 16
S.render.resolution_x = int(1080 * SC); S.render.resolution_y = int(1920 * SC)
try: S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Punchy'
except Exception: pass
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in todo:
        frame(f); S.render.filepath = os.path.join(OUT, f'f_{f:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', f, flush=True)
