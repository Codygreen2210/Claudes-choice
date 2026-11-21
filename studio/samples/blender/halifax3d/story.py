# The Halifax Explosion (Halifax, Nova Scotia, December 6, 1917), told as a cardboard cut-out play on a Broadway stage (style a).
# The set is the Richmond end of town: the dispatcher's station, the track, Pier 6, the harbour with the ships, Dartmouth painted behind.
# One continuous shot; the curtains part on frame one, and it ends on a marquee SUBSCRIBE sign that drops in and lights up bulb by bulb.
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
box('stage', (19.0, 8.5, 1.0), (0, 3.75, -0.5), FLOOR)
box('apron', (13.0, 0.06, 1.0), (0, -0.52, -0.5), flat('apronblack', (0.03, 0.025, 0.02), 0.9))
bdm, nt, b = node_mat('backdrop'); it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(os.path.join(ART, 'backdrop.png')); nt.links.new(it.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.95
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 7.2, 3.6), rotation=(R(90), 0, 0)); BD = bpy.context.object; BD.scale = (16.0, 7.2, 1); BD.data.materials.append(bdm)
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
bpy.ops.object.text_add(location=(0, -0.9, OH + 1.38)); TX = bpy.context.object; TX.data.body = 'HALIFAX 1917'; TX.data.align_x = 'CENTER'; TX.data.size = 0.5
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


# ================================================================ the Halifax set
META = json.load(open(os.path.join(ART, 'meta.json')))
def cut(name, img, h, loc, brace=False): return cutout(name, img, h, loc, brace=brace)
def apos(o, img, key, idx=None):
    """world-ish local offset (x, z) of a point stored in meta.json for art img, on cut-out o (origin = bottom centre)"""
    C = CONT[img]; k = o['h'] / C['H']; u, v = META[img][key] if idx is None else META[img][key][idx]
    return (u - 0.5) * C['W'] * k, v * C['H'] * k
def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None); S.collection.objects.link(e); e.location = loc
    if parent: e.parent = parent
    return e
def emat(name, col, es):
    m = flat(name, col, 0.4, col, es); return m
def set_es(m, v): m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = v
def art_emit(o, col, v):
    b_ = o.data.materials[0].node_tree.nodes['Principled BSDF']; b_.inputs['Emission Color'].default_value = (*col, 1); b_.inputs['Emission Strength'].default_value = v
def wobble(t, k, a=1.0): return a * math.sin(t * 2.1 + k * 1.7)

# ---------------------------------------------------------------- tracks: the back track (No. 10 from Saint John) and the front track (the relief train)
TRK_B, TRK_F = 0.72, 0.22
RAIL = flat('rail', (0.32, 0.32, 0.34), 0.35); RAIL.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.8
TIE = flat('tie', (0.28, 0.2, 0.14), 0.9)
for ty in (TRK_B, TRK_F):
    for dy in (-0.09, 0.09): box(f'rail{ty}{dy}', (20.0, 0.03, 0.04), (0, ty + dy, 0.05), RAIL)
    for k in range(70): box(f'tie{ty}_{k}', (0.09, 0.3, 0.03), (-9.8 + k * 0.29, ty, 0.015), TIE)

# ---------------------------------------------------------------- the station (seen from the front: its front wall is off, like a doll's house)
SIDEM = tex_mat('sidewall', 'acg:Cardboard004', 1.4, (0.77, 0.67, 0.5), bump=0.5)
ROOFM = tex_mat('roofm', 'acg:Cardboard004', 1.4, (0.45, 0.25, 0.2), bump=0.5)
SX, SY = -3.6, 2.3
WALL = cut('st_wall', 'st_wall', 1.9, (SX, SY, 0))
SIDES = []
for k, sx in enumerate((-1.34, 1.34)):
    p = empty(f'sidepiv{k}', (SX + sx, 1.82, 0)); o = box(f'side{k}', (0.06, 0.95, 1.9), (0, 0, 0.95), SIDEM); o.parent = p; SIDES.append(p)
RPIV = empty('roofpiv', (SX, 1.82, 1.93)); RF = box('roofslab', (2.9, 1.1, 0.06), (0, 0, 0), ROOFM); RF.parent = RPIV
FASC = cut('st_roof', 'st_roof', 0.6, (0, -0.55, -0.33)); FASC.parent = RPIV
DESK = cut('desk', 'desk', 0.95, (-3.35, 1.75, 0))
kx, kz = apos(DESK, 'desk', 'key'); KEYP = empty('keypiv', (-3.35 + kx - 0.1, 1.73, kz + 0.012))
KEYA = cut('keyarm', 'keyarm', 0.055, (0.105, 0, -0.012)); KEYA.parent = KEYP
COLE = cut('coleman', 'coleman', 1.55, (-3.06, 1.95, 0), brace=True); COLE_GO = cut('coleman_go', 'coleman_go', 1.55, (-3.06, 1.95, 0), brace=True)
cx_, cz_ = apos(WALL, 'st_wall', 'clock'); CLX, CLZ = SX + cx_, cz_
CLOCK = cut('clock', 'clock', 0.36, (CLX, SY - 0.03, CLZ - 0.18))
HM = cut('hand_m', 'hand_m', 0.14, (CLX, SY - 0.045, CLZ)); HH = cut('hand_h', 'hand_h', 0.095, (CLX, SY - 0.05, CLZ))
ax_, az_ = apos(WALL, 'st_wall', 'cal')
CAL6 = cut('cal6', 'cal6', 0.3, (SX + ax_, SY - 0.03, az_ - 0.15)); CALP = empty('calpiv', (SX + ax_, SY - 0.04, az_ + 0.15)); CAL5 = cut('cal5', 'cal5', 0.3, (0, 0, -0.3)); CAL5.parent = CALP

# ---------------------------------------------------------------- the town: houses (faces at the windows), townsfolk, the pier, poles, the signal
HOUSES = []
for k, (img, h, x, y) in enumerate((('house_a', 2.1, -5.6, 3.0), ('house_c', 2.2, -1.95, 3.3), ('house_b', 1.95, 2.55, 3.05), ('house_a', 2.2, 4.75, 3.35))):
    HOUSES.append((cut(f'house{k}', img, h, (x, y, 0)), img))
FACES = []
for k, (hi, wk, img) in enumerate(((0, 'w0', 'face_a'), (1, 'w0', 'face_b'), (1, 'w1', 'face_c'), (2, 'w0', 'face_b'), (2, 'w1', 'face_a'), (3, 'w1', 'face_c'), (0, 'w1', 'face_b'))):
    ho, himg = HOUSES[hi]; fx, fz = apos(ho, himg, wk)
    f_ = cut(f'face{k}', img, 0.36, (ho.location.x + fx, ho.location.y - 0.025, fz - 0.24)); f_['home'] = list(f_.location); FACES.append(f_)
MAN = cut('man', 'man', 1.5, (-0.7, 1.55, 0), brace=True); WOMAN = cut('woman', 'woman', 1.45, (0.05, 2.0, 0), brace=True); MAN2 = cut('man2', 'man2', 1.5, (2.0, 1.75, 0), brace=True)
FOLK = [(MAN, -1.9, -0.7, 1.55), (WOMAN, -1.0, 0.05, 2.0), (MAN2, 3.6, 2.0, 1.75)]
SAILOR = cut('sailor', 'sailor', 1.5, (0.6, 1.45, 0), brace=True); SAILOR_P = cut('sailor_pt', 'sailor_pt', 1.5, (-2.05, 1.45, 0), brace=True)
PIER = empty('pier', (0.8, 3.05, 0))
o = box('pierdeck', (1.0, 1.75, 0.08), (0, 0, 0.27), WOOD); o.parent = PIER
for k, (dx, dy) in enumerate(((-0.42, -0.7), (0.42, -0.7), (-0.42, 0.0), (0.42, 0.0), (-0.42, 0.75), (0.42, 0.75))):
    c_ = cyl(f'piling{k}', 0.05, 0.5, (dx, dy, 0.12), WOOD); c_.parent = PIER
P6 = cut('pier6', 'pier6', 1.0, (0.15, 2.2, 0), brace=True)
POLES = [cut(f'pole{k}', 'pole', 2.6, (x, 1.05, 0)) for k, x in enumerate((-1.9, 3.4, 6.0))]
WIRE = cyl('wire', 0.008, 9.0, (2.6, 1.03, 2.41), BLACK, (0, R(90), 0)); WIRE0 = cyl('wire0', 0.008, 0.85, (-2.1, 1.25, 2.15), BLACK, (R(30), R(60), 0))
SIGX = 1.6
SIGP = cut('sigpost', 'sigpost', 2.3, (SIGX, 0.92, 0)); SIGPV = empty('sigpiv', (SIGX + 0.05, 0.9, 2.07)); SIGA = cut('sigarm', 'sigarm', 0.11, (0.31, 0, -0.055)); SIGA.parent = SIGPV
LAMPM = emat('lamp', (0.2, 1.0, 0.3), 6.0); bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(SIGX, 0.88, 2.07), segments=16, ring_count=8); bpy.context.object.data.materials.append(LAMPM)
ROCK = cut('rocksign', 'rocksign', 1.7, (3.35, 1.45, 0))

# ---------------------------------------------------------------- the harbour: waves, the two ships, the cargo door, the lifeboat
ROWS = []
for k, y in enumerate((3.6, 4.45, 5.35, 6.25)):
    w_ = cut(f'wave{k}', 'waves' if k % 2 else 'waves2', 0.32, (0.3 * k, y, 0)); w_.scale.x = 3.5; ROWS.append(w_)
BIGW = []
for k, y in enumerate((3.95, 4.7)):
    w_ = cut(f'bigwave{k}', 'bigwave', 0.9, (0.4 * k, y, -0.9)); w_.scale.x = 3.5; BIGW.append(w_)
MB = cut('montblanc', 'montblanc', 1.5, (-6.5, 4.9, 0))
hx, hz = apos(MB, 'montblanc', 'hold')
CARGO = cut('cargo', 'cargo', 0.273, (hx, -0.008, hz)); CARGO.parent = MB
HPIV = empty('hullpiv', (hx, -0.016, hz), MB); HPAN = cut('hullpanel', 'hullpanel', 0.273, (0, 0, 0)); HPAN.parent = HPIV
IMO = cut('imo', 'imo', 1.35, (6.5, 5.3, 0))
FIREMB = []
fx, fz = apos(MB, 'montblanc', 'fire'); f2x, f2z = apos(MB, 'montblanc', 'fire2')
for k, (img, dx, x0, z0, h) in enumerate((('flame_a', -0.2, fx, fz, 0.6), ('flame_b', 0.15, fx, fz, 0.75), ('flame_c', 0.0, f2x, f2z, 0.55), ('flame_a', 0.3, f2x, f2z, 0.45))):
    f_ = cut(f'fmb{k}', img, h, (x0 + dx, -0.04 - 0.005 * k, z0 - 0.08)); f_.parent = MB; FIREMB.append(f_)
LB = cut('lifeboat', 'lifeboat', 0.55, (0, 4.6, 0)); OARS = cut('oars', 'oars', 0.17, (0, -0.02, 0.12)); OARS.parent = LB
BUB_BLOW = cut('bub_blow', 'bub_blow', 0.75, (0, 0, 0)); BUB_RUN = cut('bub_run', 'bub_run', 0.6, (-2.0, 1.35, 1.7)); BUB_HUH = cut('bub_huh', 'bub_huh', 0.55, (0, 0, 0))
PIERFIRE = [cut(f'fpier{k}', img, h, (0.55 + 0.4 * k, 3.75, 0.28)) for k, (img, h) in enumerate((('flame_b', 0.55), ('flame_c', 0.45)))]

# ---------------------------------------------------------------- smoke and steam pools; the blast (fireball, ring, cloud, pieces, glass), the rubble
SMOKE = [cut(f'smoke{k}', 'smoke' if k % 2 else 'smoke2', 0.7, (0, 0, -5)) for k in range(8)]
STACK = [cut(f'stack{k}', 'smoke2', 0.28, (0, 0, -5)) for k in range(8)]
STEAM = [cut(f'steam{k}', 'steam', 0.4, (0, 0, -5)) for k in range(10)]
for o in SMOKE + STACK + STEAM: o.visible_shadow = False
BX, BY, BZ = 1.25, 4.05, 0.8                                 # where Mont-Blanc lies at the pier when it goes
FBM = emat('fireball', (1.0, 0.85, 0.55), 30.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(BX, BY, BZ), segments=32, ring_count=16); FIREBALL = bpy.context.object; FIREBALL.data.materials.append(FBM); FIREBALL.visible_shadow = False
L_ = bpy.data.lights.new('flash', 'POINT'); L_.energy = 0; L_.color = (1.0, 0.88, 0.7); L_.shadow_soft_size = 2.0
FLASH = bpy.data.objects.new('flash', L_); S.collection.objects.link(FLASH); FLASH.location = (BX, 2.2, 2.5)
RINGM = emat('ring', (1.0, 0.95, 0.85), 4.0)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05, location=(BX, BY, 0.12)); RING = bpy.context.object; RING.data.materials.append(RINGM); RING.visible_shadow = False
CLOUD = cut('cloud', 'cloud', 7.0, (BX, BY + 0.4, 0)); CLOUD.visible_shadow = False
PIECES = []
for k, (img, h, vx, vz, spin) in enumerate((('chunk', 0.6, -3.0, 6.5, 9), ('chunk', 0.45, 3.5, 7.5, -11), ('funnel', 0.6, 0.6, 9.0, 7), ('plank', 0.16, -4.5, 5.0, 14),
                                             ('plank', 0.14, 4.0, 4.0, -15), ('crate', 0.35, -1.5, 8.0, 10), ('crate', 0.3, 2.2, 6.0, -8), ('plank', 0.15, -0.8, 5.5, 18),
                                             ('anchor', 0.7, -2.2, 12.0, 6))):
    o = cut(f'piece{k}', img, h, (0, 0, -5)); o['v'] = (vx, vz, spin); PIECES.append(o)
SHARDS = [cut(f'shard{k}', 'shard', 0.14, (0, 0, -5)) for k in range(16)]
RUBBLE = [cut(f'rubble{k}', 'rubble', 0.55, (x, y, -0.6)) for k, (x, y) in enumerate(((-5.6, 3.0), (-1.95, 3.3), (2.55, 3.05), (4.75, 3.35), (-4.1, 2.2), (-2.9, 2.35), (0.8, 2.9)))]
for o in RUBBLE: o.scale.x = 1.4
FIRER = [cut(f'frub{k}', ('flame_a', 'flame_b', 'flame_c')[k % 3], 0.4 + 0.08 * (k % 2), (x, y - 0.1, 0.1)) for k, (x, y) in enumerate(((-5.3, 3.0), (-1.4, 3.3), (2.9, 3.05), (4.4, 3.35), (-4.4, 2.2)))]

# ---------------------------------------------------------------- the telegraph's dots and dashes running down the wire
DOTM = emat('dots', (1.0, 0.82, 0.25), 0.0)
DOTS = []
for k in range(14):
    if k % 3 == 1: o = box(f'dash{k}', (0.16, 0.02, 0.05), (0, 0, -5), DOTM)
    else: o = cyl(f'dot{k}', 0.035, 0.02, (0, 0, -5), DOTM, (R(90), 0, 0))
    o.visible_shadow = False; DOTS.append(o)

# ---------------------------------------------------------------- trains: No. 10 from Saint John (left), the Boston relief train with its plow (right)
def train_car(name, img, h, y):
    o = cut(name, img, h, (0, y, 0)); W_ = []
    for j, (u, v) in enumerate(META[img]['wheels'] + META[img].get('small', [])):
        C = CONT[img]; k = h / C['H']; r = 0.16 if j < 3 and 'loco' in img else 0.1
        pv = empty(f'{name}_wp{j}', ((u - 0.5) * C['W'] * k, -0.02, r), o); wl = cut(f'{name}_w{j}', 'wheel', 2 * r, (0, 0, -r)); wl.parent = pv; W_.append(pv)
    o['wheels'] = len(W_); return o, W_
NO10 = [train_car('no10_loco', 'loco_l', 1.15, TRK_B), train_car('no10_c1', 'coach', 1.05, TRK_B), train_car('no10_c2', 'coach', 1.05, TRK_B)]
RELIEF = [train_car('rel_loco', 'loco_r', 1.2, TRK_F), train_car('rel_b1', 'box_boston', 1.0, TRK_F), train_car('rel_b2', 'box_food', 1.0, TRK_F), train_car('rel_b3', 'box_med', 1.0, TRK_F)]
SPARKS = [cut(f'spark{k}', 'sparks', 0.28, (0, 0, -5)) for k in range(3)]
for o in SPARKS: o.visible_shadow = False; art_emit(o, (1.0, 0.75, 0.3), 3.0)

# ---------------------------------------------------------------- the blizzard, and the tree
FLAKES = [cut(f'flake{k}', 'flake', 0.07 + 0.03 * (k % 3), (0, 0, -5)) for k in range(80)]
for o in FLAKES: o.visible_shadow = False
DRIFTS = [cut(f'drift{k}', 'drift', 0.42, (x, y, -0.45)) for k, (x, y) in enumerate(((-4.6, -0.05), (-1.0, -0.02), (2.6, -0.05), (6.0, -0.02), (-3.2, 1.3), (1.6, 1.5), (4.6, 1.75)))]
TX_, TY_ = -0.6, 2.45
TREE = cut('xtree', 'xtree', 4.0, (TX_, TY_, -4.1))
TLM = [emat(f'tl{k}', c, 0.0) for k, c in enumerate(((1.0, 0.25, 0.2), (1.0, 0.8, 0.3), (0.4, 0.6, 1.0)))]
TLIGHTS = []
for k, (u, v) in enumerate(META['xtree']['lights']):
    C = CONT['xtree']; kk = 4.0 / C['H']
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=((u - 0.5) * C['W'] * kk, -0.05, v * C['H'] * kk), segments=12, ring_count=8)
    b_ = bpy.context.object; b_.parent = TREE; b_.data.materials.append(TLM[k % 3]); TLIGHTS.append(b_)
STAR = cut('star', 'star', 0.6, (0, -0.04, 3.82)); STAR.parent = TREE
tgx, tgz = apos(TREE, 'xtree', 'tag'); TAGP = empty('tagpiv', (tgx, -0.07, tgz), TREE); TAG = cut('tag', 'tag', 0.75, (0.43, 0, -0.375)); TAG.parent = TAGP
L_ = bpy.data.lights.new('starlight', 'POINT'); L_.energy = 0; L_.color = (1.0, 0.85, 0.5); STARL = bpy.data.objects.new('starlight', L_); S.collection.objects.link(STARL); STARL.parent = TREE; STARL.location = (0, -0.6, 3.6)

# ---------------------------------------------------------------- the marquee: a sign that drops from the flies, SUBSCRIBE spelled in light bulbs
FONT5 = {'S': ['.###.', '#...#', '#....', '.###.', '....#', '#...#', '.###.'], 'U': ['#...#'] * 6 + ['.###.'],
         'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'], 'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
         'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'], 'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
         'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####']}
def onmat(name, col, lo, hi):
    """emission = lo + (hi - lo) * the object's 'on' property, so each bulb can light on its own"""
    m, nt, b_ = node_mat(name); b_.inputs['Base Color'].default_value = (*col, 1); b_.inputs['Roughness'].default_value = 0.25
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'on'
    mp = nt.nodes.new('ShaderNodeMapRange'); mp.inputs['To Min'].default_value = lo; mp.inputs['To Max'].default_value = hi; nt.links.new(at.outputs['Fac'], mp.inputs['Value'])
    b_.inputs['Emission Color'].default_value = (*col, 1); nt.links.new(mp.outputs['Result'], b_.inputs['Emission Strength']); return m
def halomat(name, col, k):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; out_ = nt.nodes['Material Output']
    for n_ in list(nt.nodes):
        if n_.type == 'BSDF_PRINCIPLED': nt.nodes.remove(n_)
    tc = nt.nodes.new('ShaderNodeTexCoord'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; nt.links.new(tc.outputs['Object'], gr.inputs['Vector'])
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'on'
    p2 = nt.nodes.new('ShaderNodeMath'); p2.operation = 'POWER'; nt.links.new(gr.outputs['Fac'], p2.inputs[0]); p2.inputs[1].default_value = 2.2
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; nt.links.new(p2.outputs[0], mu.inputs[0]); nt.links.new(at.outputs['Fac'], mu.inputs[1])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = k
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1])
    mx_ = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(mu.outputs[0], mx_.inputs['Fac']); nt.links.new(tr.outputs[0], mx_.inputs[1]); nt.links.new(ad.outputs[0], mx_.inputs[2])
    nt.links.new(mx_.outputs[0], out_.inputs['Surface']); return m
MW, MH = 4.9, 1.3
MQ = empty('marquee', (0, 0.35, 14.0))
MRED = flat('mqred', (0.32, 0.03, 0.04), 0.5)
mb_ = box('mq_board', (MW, 0.12, MH), (0, 0.06, 0), MRED); mb_.parent = MQ
tube_path('mq_trim', [(-MW / 2, -MH / 2), (-MW / 2, MH / 2), (MW / 2, MH / 2), (MW / 2, -MH / 2), (-MW / 2, -MH / 2)], -0.02, 0.05, GILT).parent = MQ
ib_ = box('mq_inner', (MW - 0.5, 0.02, MH - 0.42), (0, -0.01, 0), flat('mqin', (0.05, 0.02, 0.02), 0.6)); ib_.parent = MQ
for sx in (-1, 1):
    c_ = cyl(f'mq_chain{sx}', 0.02, 9.0, (sx * (MW / 2 - 0.4), 0.06, MH / 2 + 4.5), GOLD); c_.parent = MQ
LBM = onmat('mqbulb', (1.0, 0.82, 0.5), 0.15, 14.0); HALO = halomat('mqhalo', (1.0, 0.75, 0.4), 2.2)
WORD = 'SUBSCRIBE'; PIT = (MW - 0.75) / (len(WORD) * 6 - 1)
MBULBS = []                                                     # (bulb, halo, letter index, order in the letter)
for li, ch in enumerate(WORD):
    order = 0
    for col_ in range(5):
        for row in range(7):
            if FONT5[ch][row][col_] != '#': continue
            x = -(len(WORD) * 6 - 1) * PIT / 2 + (li * 6 + col_) * PIT; z = (3 - row) * PIT * 1.05
            bpy.ops.mesh.primitive_uv_sphere_add(radius=PIT * 0.36, location=(x, -0.06, z), segments=12, ring_count=8); bb = bpy.context.object; bb.parent = MQ; bb.data.materials.append(LBM); bb['on'] = 0.0
            bpy.ops.mesh.primitive_circle_add(vertices=20, radius=PIT * 1.1, fill_type='NGON', location=(x, -0.1, z), rotation=(R(90), 0, 0)); hl = bpy.context.object; hl.parent = MQ; hl.data.materials.append(HALO); hl['on'] = 0.0
            hl.visible_shadow = False; hl.visible_diffuse = False; MBULBS.append((bb, hl, li, order)); order += 1
BORDER = []
per = []
for k in range(26): per.append((-MW / 2 + 0.14 + k * (MW - 0.28) / 25, MH / 2 - 0.12))
for k in range(1, 6): per.append((MW / 2 - 0.14, MH / 2 - 0.12 - k * (MH - 0.24) / 6))
for k in range(26): per.append((MW / 2 - 0.14 - k * (MW - 0.28) / 25, -MH / 2 + 0.12))
for k in range(1, 6): per.append((-MW / 2 + 0.14, -MH / 2 + 0.12 + k * (MH - 0.24) / 6))
for k, (x, z) in enumerate(per):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(x, -0.05, z), segments=12, ring_count=8); bb = bpy.context.object; bb.parent = MQ; bb.data.materials.append(LBM); bb['on'] = 0.0; BORDER.append(bb)
L_ = bpy.data.lights.new('mqglow', 'AREA'); L_.shape = 'RECTANGLE'; L_.size = MW; L_.size_y = MH; L_.energy = 0; L_.color = (1.0, 0.8, 0.55)
MQL = bpy.data.objects.new('mqglow', L_); S.collection.objects.link(MQL); MQL.parent = MQ; MQL.location = (0, -0.4, 0); MQL.rotation_euler = (R(-90), 0, 0)

# ---------------------------------------------------------------- timing (seconds; B = line starts)
BUMP = B[1] + 1.55; PANEL = B[1] + 3.15
FIRE = B[2] + 0.3; BOAT0 = B[2] + 0.85; BLOW = B[2] + 1.85
FOLK0 = B[2] + 1.6; HUH = B[3] + 0.25; DRIFT0, DRIFT1 = B[3] + 1.3, B[3] + 3.2; PFIRE = B[3] + 3.05
SAIL0, SAIL1 = B[4] - 0.25, B[4] + 0.9; CGO, CBACK, CHOME = B[4] + 1.3, B[4] + 3.4, B[5] + 0.45
TRAIN0 = B[4] + 1.2; TAP0, TAP1 = B[5] + 0.85, B[5] + 3.6; DOTS0 = B[5] + 1.3; DSPD = 4.0
SEMA = DOTS0 + (SIGX + 2.3) / DSPD; BRAKE = SEMA + 0.08; STOPT = BRAKE + 0.8
C904 = B[6] + 0.45; BLAST = B[6] + 1.75
ROCKT = B[8] + 0.5; DOTS1 = B[8] + 1.6
SNOW0, SNOW1 = B[9] + 0.25, B[10] + 0.5; REL0 = B[9] + 0.35; RSPD = 3.7
REBUILD = B[10] + 0.45; FOLK2 = B[10] + 1.9; TREE0, TREE1 = B[10] + 1.55, B[10] + 2.6; LIGHTS = B[10] + 3.7; TAGT = B[10] + 4.35
SIGN0, SIGN1 = B[11] + 0.3, B[11] + 1.25; LIT0 = B[11] + 2.62
BASE_E = {n_: bpy.data.objects[n_].data.energy for n_ in ('key_l', 'key_r', 'top', 'drop', 'house')}

def hide(o, v):
    o.hide_render = v
    for c in o.children: hide(c, v)
def puffs(pool, srcs, t, t0, t1, per, rise, grow, drift=-0.3, h0=1.0):
    """smoke/steam: each puff is born at one of the sources (callables giving (x, y, z)), rises, grows and goes"""
    for k, o in enumerate(pool):
        on = False
        if srcs and t0 <= t < t1:
            ph = ((t - t0) / per + k / len(pool)) % 1.0; tb = t - ph * per
            if tb >= t0:
                x, y, z = srcs[k % len(srcs)](tb); on = True
                o.location = (x + drift * ph * per + 0.05 * math.sin(k * 3.1), y - 0.02 * k, z + rise * ph); s_ = h0 * (0.4 + grow * ph); o.scale = (s_, 1, s_)
                o.rotation_euler.y = 0.3 * math.sin(k * 2.3 + ph * 2)
        hide(o, not on)
def clock_hm(t):
    """the wall clock: 8:42 at the start, 8:45 at the collision, about 9:00 when the sailor comes, 9:04 on the dot"""
    pts = [(0.0, 8 * 60 + 42), (BUMP, 8 * 60 + 45), (B[4], 8 * 60 + 58), (C904 - 0.1, 9 * 60 + 3), (C904, 9 * 60 + 4)]
    if t >= C904: return 9 * 60 + 4
    for (a, ma), (b, mb_) in zip(pts, pts[1:]):
        if a <= t <= b: return lerp(ma, mb_, (t - a) / max(b - a, 1e-6))
    return 9 * 60 + 4

def frame(f):
    t = f / FPS; S.frame_set(f)
    for d_ in DRAPES: d_.set(lerp(0.06, 1.0, smooth(0.0, 2.6, t)), t)
    chase = int(t * 6) % 2
    BULB_A.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 9.0 if chase else 3.0
    BULB_B.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0 if chase else 9.0
    blast = t >= BLAST + 0.05; flashu = clamp((t - BLAST) / 0.9, 0, 1)
    # ---- waves bob; the tsunami lifts and runs at the shore after the blast
    for k, w_ in enumerate(ROWS):
        w_.location.z = 0.025 * math.sin(t * 2.2 + k * 1.3) + 0.25 * math.sin(math.pi * clamp((t - BLAST - 0.1) / 2.2, 0, 1)); w_.location.x = 0.3 * k + 0.08 * math.sin(t * 0.7 + k)
    for k, w_ in enumerate(BIGW):
        u = clamp((t - BLAST - 0.15 - 0.15 * k) / 2.6, 0, 1); up = math.sin(math.pi * u) ** 0.7
        w_.location = (0.4 * k + 0.15 * math.sin(t * 3 + k), (3.95, 4.7)[k] - 1.3 * math.sin(math.pi * min(u * 1.2, 1)) * (1 - k * 0.3), -0.9 + 1.0 * up); hide(w_, u <= 0 or u >= 1)
    # ---- the ships: Mont-Blanc comes in from the left, Imo from the right; they bump; Imo backs off; Mont-Blanc burns and drifts to the pier
    ub = smooth(0.0, BUMP, t) ** 0.85; jolt = math.exp(-max(0, t - BUMP) * 4) * (t > BUMP)
    mbx = lerp(-6.8, -0.5, ub) - 0.15 * jolt * math.sin((t - BUMP) * 30) * (t > BUMP)
    ud = smooth(DRIFT0, DRIFT1, t); MB.location = (lerp(mbx, BX, ud), lerp(4.9, BY, ud), 0.02 * math.sin(t * 1.8))
    MB.rotation_euler.y = R(1.2) * math.sin(t * 1.3) + R(4) * jolt * math.sin((t - BUMP) * 22) + R(-2) * smooth(FIRE, FIRE + 1, t)
    hide(MB, blast)
    ui = smooth(0.0, BUMP, t) ** 0.85; ur = smooth(BUMP + 0.4, B[3] + 0.8, t)
    if not blast: IMO.location = (lerp(lerp(7.0, 2.05, ui), 4.3, ur) + 0.12 * jolt, 5.3, 0.02 * math.sin(t * 1.6 + 1)); IMO.rotation_euler.y = R(1.0) * math.sin(t * 1.4 + 2) + R(-3) * jolt * math.sin((t - BUMP) * 20)
    else:
        us = back_out(BLAST + 0.05, BLAST + 0.7, t, 1.0); IMO.location = (lerp(4.3, 5.2, us), lerp(5.3, 6.6, us), -0.25 * us); IMO.rotation_euler.y = R(-14) * us + R(3) * math.sin(t * 2) * (1 - smooth(BLAST + 1, BLAST + 3, t))
    HPIV.rotation_euler.x = R(100) * back_out(PANEL, PANEL + 0.45, t, 1.2)
    fu = smooth(FIRE, FIRE + 0.5, t)
    for k, f_ in enumerate(FIREMB):
        g_ = fu * (1.0 if k < 2 else smooth(FIRE + 1.0, FIRE + 2.0, t)) * (1 + 0.25 * smooth(DRIFT0, DRIFT1, t)); s_ = max(g_ * (0.85 + 0.15 * math.sin(t * 17 + k * 2.1)), 1e-3)
        f_.scale = (s_ * (0.9 + 0.1 * math.sin(t * 11 + k)), 1, s_); hide(f_, g_ <= 0.01 or blast)
    # the lifeboat: drops in by the stern and rows hard for the Dartmouth side; the shout above it
    ul = smooth(BOAT0 + 0.3, B[3] + 3.0, t); LB.location = (lerp(mbx - 1.3, -4.3, ul), lerp(4.6, 6.15, ul), 0.03 * abs(math.sin(t * 6)) - 0.25 * (1 - smooth(BOAT0, BOAT0 + 0.3, t)))
    OARS.rotation_euler.y = R(18) * math.sin(t * 7.5); hide(LB, t < BOAT0 or blast)
    ubb = back_out(BLOW, BLOW + 0.3, t, 2.0) * (1 - smooth(B[3] + 0.5, B[3] + 0.8, t)); BUB_BLOW.location = (LB.location.x + 0.35, LB.location.y - 0.1, 0.55); BUB_BLOW.scale = (max(ubb, 1e-3),) * 3; hide(BUB_BLOW, ubb <= 0.01)
    # ---- stack smoke while steaming; the fire's black smoke; steam from No. 10 and the plow's spray
    def mbstack(tb): x, z = apos(MB, 'montblanc', 'stack'); return (MB.location.x + x, MB.location.y - 0.05, z)
    def imstack(tb): x, z = apos(IMO, 'imo', 'stack'); return (IMO.location.x + x, IMO.location.y - 0.05, z)
    puffs(STACK, [mbstack, imstack], t, 0.0, BLAST, 1.4, 0.9, 1.3, -0.25)
    def mbfire(tb): return (MB.location.x + fx, MB.location.y - 0.1, fz + 0.3)
    def mbfire2(tb): return (MB.location.x + f2x, MB.location.y - 0.1, f2z + 0.3)
    def rub(k): return lambda tb: (RUBBLE[k].location.x, RUBBLE[k].location.y - 0.15, 0.3)
    if t < BLAST: puffs(SMOKE, [mbfire, mbfire2], t, FIRE + 0.3, BLAST, 2.2, 3.2, 1.8, -0.4)
    else: puffs(SMOKE, [rub(0), rub(1), rub(2), rub(3)], t, BLAST + 1.2, SNOW0 + 0.8, 3.0, 2.6, 1.6, 0.3)
    # ---- No. 10: rolls in slowly from the right, stops at the signal; sparks under the brakes
    def xf10(t_):
        if t_ < BRAKE: return 2.95 - (2.95 - 2.0) * (t_ - TRAIN0) / (BRAKE - TRAIN0)
        v = (2.95 - 2.0) / (BRAKE - TRAIN0); u_ = clamp((t_ - BRAKE) / (STOPT - BRAKE), 0, 1); return 2.0 - v * (STOPT - BRAKE) * (u_ - u_ * u_ / 2)
    xf = xf10(max(t, TRAIN0)) if t >= TRAIN0 else 2.95; rocking = 0.03 * math.sin(t * 9) * math.exp(-max(0, t - BLAST) * 1.5) * (t > BLAST)
    xs = xf
    for k, (o, W_) in enumerate(NO10):
        w = o['h'] * CONT[('loco_l', 'coach', 'coach')[k]]['W'] / CONT[('loco_l', 'coach', 'coach')[k]]['H']
        o.location = (xs + w / 2, TRK_B, 0.012 + 0.006 * abs(math.sin(t * 14 + k)) * (t < STOPT)); o.rotation_euler.y = rocking; xs += w + 0.06
        for pv in W_: pv.rotation_euler.y = (2.95 - xf) / 0.16
        hide(o, t < TRAIN0 - 0.5 or t > SNOW0 + 1.0)
    def no10stack(tb): x, z = apos(NO10[0][0], 'loco_l', 'stack'); return (NO10[0][0].location.x + x, TRK_B - 0.1, z)
    def plow(tb): o = RELIEF[0][0]; return (o.location.x + 1.0, TRK_F - 0.25, 0.25)
    def relstack(tb): o = RELIEF[0][0]; x, z = apos(o, 'loco_r', 'stack'); return (o.location.x + x, TRK_F - 0.1, z)
    if t < SNOW0: puffs(STEAM, [no10stack], t, TRAIN0, STOPT + 1.5, 1.2, 0.7, 0.9, 0.3, 0.6)
    else: puffs(STEAM, [plow, relstack, plow], t, REL0 + 0.6, B[10] + 1.6, 0.7, 0.6, 2.2, -0.6, 1.4)
    for k, sp_ in enumerate(SPARKS):
        on = BRAKE < t < STOPT; hide(sp_, not on)
        if on:
            o = NO10[0][0] if k < 2 else NO10[1][0]; sp_.location = (o.location.x - 0.5 + 0.6 * k, TRK_B - 0.12, 0.0); s_ = 0.7 + 0.5 * abs(math.sin(t * 23 + k * 2)); sp_.scale = (s_, 1, s_)
    # ---- the relief train out of Boston plows through the snow, left to right
    xr = -9.0 + RSPD * max(0.0, t - REL0); xs = xr
    for k, (o, W_) in enumerate(RELIEF):
        img = ('loco_r', 'box_boston', 'box_food', 'box_med')[k]; w = o['h'] * CONT[img]['W'] / CONT[img]['H']
        o.location = (xs - w / 2, TRK_F, 0.012 + 0.006 * abs(math.sin(t * 14 + k))); xs -= w + 0.06
        for pv in W_: pv.rotation_euler.y = -(xr + 9) / 0.16
        hide(o, not (REL0 <= t <= B[11] - 0.5))
    # ---- the station: the calendar's page goes over; the clock runs to 9:04; Coleman taps, goes to leave, comes back, taps out the warning
    CALP.rotation_euler.x = -R(178) * smooth(B[0] + 2.95, B[0] + 3.4, t)
    mins = clock_hm(t); HM.rotation_euler.y = R(mins % 60 * 6); HH.rotation_euler.y = R((mins / 60 % 12) * 30)
    tapping = (t < CGO) or (CHOME <= t < TAP1 + 0.3)
    fast = TAP0 <= t < TAP1
    tap = (0.5 + 0.5 * math.sin(t * (38 if fast else 14))) ** 3 if tapping else 0.0
    if fast and int(t * 7) % 4 == 3: tap *= 0.2                     # letter gaps
    KEYP.rotation_euler.y = R(7) * tap
    going = CGO <= t < CHOME
    hide(COLE, going or blast); hide(COLE_GO, not going or blast)
    if going:
        uo = smooth(CGO, CGO + 1.0, t); uback = smooth(CBACK, CHOME, t); COLE_GO.location = (lerp(lerp(-3.06, -4.35, uo), -3.06, uback), 1.95, 0.05 * abs(math.sin(t * 9)))
        COLE_GO.scale.x = -1 if t < CBACK else 1
    COLE.location = (-3.06, 1.95, 0.012 * tap)
    # the station comes down in the blast; the desk stays
    ucol = back_out(BLAST + 0.05, BLAST + 0.55, t, 0.7)
    WALL.rotation_euler.x = -R(84) * ucol; SIDES[0].rotation_euler.y = -R(80) * ucol; SIDES[1].rotation_euler.y = R(80) * ucol
    RPIV.location.z = 1.93 - 1.7 * ucol; RPIV.rotation_euler.y = R(8) * ucol
    for o in (WALL, CLOCK, HM, HH, CAL6, CALP, RPIV) + tuple(SIDES): hide(o, t > BLAST + 0.9)
    hide(CAL5, t > B[0] + 3.35)
    DESK.rotation_euler.y = R(-3) * ucol
    # ---- the townsfolk come out to look; '?' (they cannot hear the crew); faces at the windows
    for k, (o, x0, x1, y) in enumerate(FOLK):
        uf = smooth(FOLK0 + 0.25 * k, FOLK0 + 1.0 + 0.25 * k, t); back_ = smooth(FOLK2, FOLK2 + 0.6, t)
        if t < REBUILD: o.location = (lerp(x0, x1, uf), y, 0.06 * abs(math.sin(t * 9 + k)) * (0 < uf < 1)); o.scale.x = 1 if x1 > x0 else -1
        else: o.location = ((-2.1, 0.85, 1.9)[k], (1.8, 2.0, 1.7)[k], 0.08 * abs(math.sin(t * 6 + k)) * back_); o.scale.x = 1 if k != 2 else -1
        hide(o, uf <= 0 or (blast and t < FOLK2))
    uh = back_out(HUH, HUH + 0.3, t, 2.0) * (1 - smooth(HUH + 1.3, HUH + 1.6, t)); BUB_HUH.location = (MAN.location.x + 0.45, MAN.location.y - 0.05, 1.55); BUB_HUH.scale = (max(uh, 1e-3),) * 3; hide(BUB_HUH, uh <= 0.01)
    for k, f_ in enumerate(FACES):
        up = back_out(FOLK0 + 0.4 + 0.15 * k, FOLK0 + 0.8 + 0.15 * k, t, 1.6); h_ = f_['home']
        f_.location = (h_[0] + 0.02 * math.sin(t * 2 + k), h_[1], h_[2] - 0.3 * (1 - up)); hide(f_, up <= 0.01 or blast)
    # ---- the sailor runs up from the pier: 'RUN!'
    us_ = smooth(SAIL0, SAIL1, t); hide(SAILOR, not (SAIL0 <= t < SAIL1)); hide(SAILOR_P, not (SAIL1 <= t < B[4] + 2.6))
    SAILOR.location = (lerp(0.6, -2.05, us_), 1.45, 0.06 * abs(math.sin(t * 10))); SAILOR.scale.x = -1; SAILOR_P.scale.x = -1
    ur_ = back_out(SAIL1, SAIL1 + 0.25, t, 2.2) * (1 - smooth(B[4] + 2.2, B[4] + 2.5, t)); BUB_RUN.scale = (max(ur_, 1e-3),) * 3; hide(BUB_RUN, ur_ <= 0.01)
    # ---- the pier, its fire; the houses go down in the blast and come back up rebuilt
    hide(PIER, blast); hide(P6, blast)
    for k, f_ in enumerate(PIERFIRE):
        g_ = smooth(PFIRE, PFIRE + 0.4, t); s_ = max(g_ * (0.85 + 0.15 * math.sin(t * 15 + k)), 1e-3); f_.scale = (s_, 1, s_); hide(f_, g_ <= 0.01 or blast)
    uh_ = back_out(BLAST + 0.05, BLAST + 0.5, t, 0.6) * (1 - back_out(REBUILD + 0.0, REBUILD + 0.7, t, 1.4))
    for k, (o, img) in enumerate(HOUSES): o.rotation_euler.x = -R(86) * uh_ * (0.97 + 0.03 * k)
    for k, o in enumerate(POLES): o.rotation_euler.y = R(18 if k % 2 else -14) * back_out(BLAST + 0.1, BLAST + 0.6, t, 0.8) * (1 - smooth(REBUILD, REBUILD + 0.6, t))
    WIRE.rotation_euler.x = 0; hide(WIRE, blast and t < REBUILD); hide(WIRE0, blast and t < REBUILD)
    urb = smooth(BLAST + 0.3, BLAST + 0.8, t) * (1 - smooth(REBUILD - 0.1, REBUILD + 0.5, t))
    for k, o in enumerate(RUBBLE): o.location.z = -0.6 + 0.6 * urb; hide(o, urb <= 0.01)
    for k, o in enumerate(FIRER):
        g_ = smooth(BLAST + 0.6, BLAST + 1.2, t) * (1 - smooth(SNOW0 + 0.4, SNOW0 + 1.4, t)); s_ = max(g_ * (0.8 + 0.2 * math.sin(t * 13 + k * 2)), 1e-3); o.scale = (s_, 1, s_); hide(o, g_ <= 0.01)
    # ---- the blast: fireball and flash, the ring over the water, the cloud, pieces of the ship, the anchor, glass from the windows
    ufb = clamp((t - BLAST) / 0.22, 0, 1); dfb = 1 - smooth(BLAST + 0.25, BLAST + 0.9, t); fb = (1.6 * ufb ** 0.5 + 0.6 * smooth(BLAST, BLAST + 0.9, t)) * dfb
    FIREBALL.scale = (max(fb, 1e-3),) * 3; hide(FIREBALL, fb <= 0.01); set_es(FBM, 30 * dfb + 2)
    FLASH.data.energy = 6e5 * math.exp(-max(0, t - BLAST) * 8) * (t >= BLAST)
    ur = clamp((t - BLAST - 0.05) / 0.55, 0, 1); RING.scale = (max(9 * ur, 1e-3), max(9 * ur * 0.75, 1e-3), 1); set_es(RINGM, 6 * (1 - ur)); hide(RING, not (0 < ur < 1))
    uc = back_out(BLAST + 0.1, BLAST + 1.8, t, 0.6); sink = smooth(B[7] + 2.4, B[8] + 0.6, t)
    CLOUD.scale = (max(uc * (1 + 0.08 * max(0, t - BLAST - 1.8)), 1e-3),) * 3; CLOUD.location = (BX + 0.25 * max(0, t - BLAST), BY + 0.4, -7.2 * sink); hide(CLOUD, uc <= 0.01 or sink >= 0.99)
    for k, o in enumerate(PIECES):
        vx, vz, sp = o['v']; tt = t - BLAST - 0.04; on = 0 < tt < 2.6
        if on:
            z = BZ + vz * tt - 0.5 * 6.5 * tt * tt; o.location = (BX + vx * tt, BY - 0.3 - 0.6 * tt * (k % 3), z); o.rotation_euler.y = sp * tt; on = z > -0.6
        hide(o, not on)
    for k, o in enumerate(SHARDS):
        ho, himg = HOUSES[k % 4]; wk = f'w{k % 2}'; wx, wz = apos(ho, himg, wk); tt = t - BLAST - 0.06 - 0.02 * k; on = 0 < tt < 0.9
        if on: o.location = (ho.location.x + wx + (k % 5 - 2) * 0.5 * tt, ho.location.y - 0.1 - 5.5 * tt, wz + 1.6 * tt - 3.0 * tt * tt); o.rotation_euler = (3 * tt * (k % 3), 9 * tt, 2 * tt)
        hide(o, not on)
    # ---- the dots and dashes down the wire: to the signal (No. 10 stops), and on down the line
    set_es(DOTM, 9.0)
    for k, o in enumerate(DOTS):
        x = None
        for t0 in (DOTS0, DOTS1):
            tt = t - t0 - 0.13 * k
            if 0 < tt and (t0 == DOTS0 and t < BLAST or t0 == DOTS1 and t < SNOW0):
                x = (-2.3 if t0 == DOTS0 else SIGX) + DSPD * tt
        on = x is not None and x < 7.5; hide(o, not on)
        if on: o.location = (x, 1.0, 2.49 + 0.02 * math.sin(t * 30 + k))
    us_ = back_out(SEMA, SEMA + 0.3, t, 1.6); SIGPV.rotation_euler.y = -R(45) * (1 - us_)
    LAMPM.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = ((0.2, 1.0, 0.3, 1) if t < SEMA else (1.0, 0.12, 0.08, 1))
    uk = back_out(ROCKT, ROCKT + 0.4, t, 1.5); ROCK.location.z = -1.75 + 1.75 * uk; hide(ROCK, uk <= 0.01)
    # ---- the blizzard: flakes, drifts that pile up and melt away again
    us_ = smooth(SNOW0, SNOW0 + 0.6, t) * (1 - smooth(SNOW1, SNOW1 + 0.6, t))
    for k, o in enumerate(FLAKES):
        r_ = random.Random(k); ph = r_.random(); x0 = r_.uniform(-7.5, 6.0); y = r_.uniform(-1.6, 3.6); sp = r_.uniform(0.25, 0.4)
        u = (t * sp + ph) % 1.0; o.location = (x0 + 2.2 * u + 0.15 * math.sin(t * 2 + k), y, 6.0 * (1 - u) - 0.2); o.rotation_euler.y = t * (2 + k % 3)
        hide(o, us_ < r_.random() * 0.9 + 0.05)
    ud_ = smooth(SNOW0 + 0.3, SNOW0 + 2.0, t) * (1 - smooth(SNOW1 + 0.2, SNOW1 + 1.2, t))
    for k, o in enumerate(DRIFTS): o.location.z = -0.45 + 0.45 * ud_; hide(o, ud_ <= 0.01)
    # ---- the tree comes up through the stage: lights, the star, the tag to Boston
    ut = back_out(TREE0, TREE1, t, 1.0); TREE.location.z = -4.1 + 4.1 * ut; TREE.rotation_euler.y = R(2) * math.sin(t * 1.3) * ut; hide(TREE, ut <= 0.001)
    for k, m in enumerate(TLM): set_es(m, (6.0 if (int(t * 3) + k) % 3 else 1.5) * smooth(LIGHTS, LIGHTS + 0.25, t))
    for k, b_ in enumerate(TLIGHTS): hide(b_, t < LIGHTS - 0.02 * (k % 6) or ut <= 0.001)
    art_emit(STAR, (1.0, 0.8, 0.3), 2.5 * smooth(LIGHTS + 0.2, LIGHTS + 0.6, t)); STARL.data.energy = 300 * smooth(LIGHTS + 0.2, LIGHTS + 0.6, t)
    ug = back_out(TAGT, TAGT + 0.35, t, 1.8); TAG.scale = (max(ug, 1e-3),) * 3; TAGP.rotation_euler.y = R(14) * math.exp(-max(0, t - TAGT) * 1.8) * math.sin((t - TAGT) * 6); hide(TAG, ug <= 0.01)
    # ---- the marquee drops in on its chains, then the bulbs light up letter by letter, then the border chases
    ud = back_out(SIGN0, SIGN1, t, 0.9); sw = math.exp(-max(0, t - SIGN1) * 1.6) * (t > SIGN0)
    MQ.location = (0, 0.35, lerp(14.0, 5.45, ud)); MQ.rotation_euler = (R(5) * sw * math.sin((t - SIGN0) * 5.5), 0, R(2.5) * sw * math.sin((t - SIGN0) * 4.2)); hide(MQ, t < SIGN0 - 0.1)
    for bb, hl, li, oi in MBULBS:
        tl = LIT0 + 0.105 * li + 0.012 * oi; on = smooth(tl, tl + 0.05, t) * (0.92 + 0.08 * math.sin(t * 40 + li))
        bb['on'] = on; hl['on'] = on
    chase_on = smooth(LIT0 + 1.0, LIT0 + 1.2, t)
    for k, bb in enumerate(BORDER): bb['on'] = chase_on * (1.0 if (k + int(t * 10)) % 3 else 0.15) + 0.0
    nl = sum(1 for bb, hl, li, oi in MBULBS if bb['on'] > 0.5); MQL.data.energy = 25 * nl + 600 * chase_on
    # ---- the lights: dim and grey for the loss, back up for the train and the tree
    dim = smooth(B[7] - 0.2, B[7] + 0.7, t) * (1 - smooth(B[8] - 0.1, B[8] + 0.7, t)); snowc = smooth(SNOW0, SNOW0 + 0.8, t) * (1 - smooth(SNOW1, SNOW1 + 0.8, t))
    for n_, e_ in BASE_E.items(): bpy.data.objects[n_].data.energy = e_ * (1 - 0.68 * dim) * (1 + 0.15 * snowc)
    for n_ in ('key_l', 'key_r'): bpy.data.objects[n_].data.color = (lerp(1.0, 0.82, snowc), lerp(0.88, 0.9, snowc), lerp(0.7, 1.0, snowc))
    for k, l_ in enumerate(FS):
        aim = Vector((-3.0, 1.75, 0.8)) if k == 0 else Vector((TX_, TY_, 2.4)); en = (14000 * dim) if k == 0 else (9000 * smooth(LIGHTS, LIGHTS + 0.5, t) * (1 - smooth(SIGN0, SIGN1, t)))
        l_.data.energy = en; l_.rotation_euler = (aim - l_.location).to_track_quat('-Z', 'Y').to_euler()
    # ---- camera: one shot, a different angle for each beat; rests about half the time; shakes in the blast
    def SH(x, z, h, y=2.4, lens=28, up=0.3):
        dist = h / 2 * lens / 18.0; return ((x, y - dist, z + up), (x, y, z), lens)
    def TRK(t_):                                                         # alongside the relief train
        xc = -9.0 + RSPD * max(0.0, t_ - REL0) - 2.0; cx = clamp(xc, -3.4, 3.6); return ((cx, -1.0, 1.1), (cx + 0.2, TRK_F, 0.75), 22)
    TR0, TR1 = B[9] + 0.6, B[10] + 0.6
    K = [(0.0, (0.0, -13.8, 3.2), (0.0, 3.0, 3.3), 22),
         (2.5, *SH(-3.45, 1.15, 2.1, 1.9, 30)), (B[1] - 0.3, *SH(-3.55, 1.12, 2.0, 1.9, 30)),                          # Coleman at his key; the calendar
         (B[1] + 0.6, *SH(1.0, 1.0, 5.0, 5.0, 28, 0.9)), (BUMP + 0.6, *SH(0.95, 1.0, 4.8, 5.0, 28, 0.9)),               # the two ships, low over the water
         (PANEL - 0.35, *SH(-0.45, 0.55, 1.55, 4.9, 30, 0.1)), (B[2] + 0.1, *SH(-0.4, 0.58, 1.5, 4.9, 30, 0.1)),       # close on the hold: TNT
         (B[2] + 0.75, *SH(0.0, 0.85, 2.7, 4.9, 28, 0.15)),                                                             # the fire takes
         (B[2] + 1.6, (-1.3, 2.6, 4.6), (-2.3, 5.5, 0.45), 26), (B[3] + 0.05, (-1.6, 2.6, 4.6), (-2.8, 5.7, 0.4), 26), # high: the lifeboat rows away
         (B[3] + 0.75, (0.15, -0.4, 0.75), (0.45, 3.2, 1.1), 20), (B[4] - 0.25, (0.3, -0.4, 0.75), (0.6, 3.2, 1.1), 20),  # low from the track: '?', the drift to the pier
         (B[4] + 0.4, *SH(-2.85, 1.1, 3.2, 1.6, 26)), (B[4] + 1.75, *SH(-3.0, 1.1, 3.2, 1.6, 26)),                     # the sailor: RUN!
         (B[4] + 2.6, (2.7, -2.0, 1.35), (3.2, 0.8, 1.0), 30), (B[4] + 4.0, (2.6, -2.0, 1.35), (3.05, 0.8, 1.0), 30),                       # No. 10, due any minute
         (B[5] + 0.35, (-2.25, 0.55, 1.0), (-3.0, 1.9, 0.92), 30), (DOTS0 + 0.25, (-2.2, 0.55, 1.0), (-2.95, 1.9, 0.94), 30),   # over the key
         (DOTS0 + 1.0, *SH(2.0, 1.65, 3.7, 0.9, 26)), (STOPT + 0.25, *SH(2.1, 1.6, 3.6, 0.9, 26)),                     # down the wire: the signal, No. 10 stops
         (B[5] + 4.15, *SH(-3.35, 1.22, 1.7, 2.0, 30, 0.12)), (B[6] + 0.1, *SH(-3.4, 1.25, 1.6, 2.0, 30, 0.12)),        # 'Goodbye, boys.'
         (C904 - 0.1, *SH(CLX, CLZ, 0.85, SY - 0.05, 32, 0.0)), (BLAST - 0.3, *SH(CLX, CLZ, 0.8, SY - 0.05, 32, 0.0)),   # 9:04
         (BLAST + 0.02, (0.9, -2.0, 1.5), (1.0, 4.0, 2.3), 20), (BLAST + 1.3, (0.9, -2.2, 1.5), (1.0, 4.0, 2.8), 20),   # the blast, wide
         (B[7] - 0.1, (0.9, -2.3, 1.55), (1.0, 4.0, 3.0), 20),
         (B[7] + 1.0, *SH(-2.6, 1.0, 3.4, 1.75, 28, 0.25)), (B[8] - 0.2, *SH(-3.0, 0.78, 1.7, 1.75, 30, 0.1)),         # the key on the wreck, in the one light
         (B[8] + 0.7, *SH(2.55, 1.25, 4.4, 0.9, 26)), (B[9] + 0.1, *SH(2.65, 1.25, 4.4, 0.9, 26)),                        # No. 10 at Rockingham; down the line
         (TR0, *TRK(TR0)), (TR1, *TRK(TR1)),                                                                             # the relief train in the snow
         (B[10] + 1.2, (TX_, -1.5, 0.4), (TX_, TY_, 1.9), 26), (B[10] + 3.6, (TX_ + 0.1, -1.6, 0.45), (TX_, TY_, 2.0), 26),   # the tree, from low
         (TAGT + 0.2, *SH(TX_ + 0.85, 1.15, 1.5, TY_, 30, 0.1)), (B[11] + 0.1, *SH(TX_ + 0.85, 1.15, 1.45, TY_, 30, 0.1)),  # the tag
         (SIGN0 + 0.6, (0.0, -6.8, 3.3), (0.0, 2.0, 4.2), 28), (TOTAL, (0.0, -6.4, 3.4), (0.0, 2.0, 4.3), 28)]          # the marquee
    if TR0 <= t <= TR1: cp, ct, lens = TRK(t); cp, ct = Vector(cp), Vector(ct)
    else:
        i = max(j for j in range(len(K)) if K[j][0] <= t); i = min(i, len(K) - 2); u = smooth(K[i][0], K[i + 1][0], t)
        cp = Vector(K[i][1]).lerp(Vector(K[i + 1][1]), u); ct = Vector(K[i][2]).lerp(Vector(K[i + 1][2]), u); lens = lerp(K[i][3], K[i + 1][3], u)
    sh = math.exp(-max(0, t - BLAST) * 2.2) * (t >= BLAST)
    cp += Vector((0.12 * sh * math.sin(t * 47), 0, 0.1 * sh * math.sin(t * 39 + 1))); roll = R(3.5) * sh * math.sin(t * 23)
    if os.environ.get('DBGCAM'):
        q_ = [float(x) for x in os.environ['DBGCAM'].split(',')]; cp, ct, lens = Vector(q_[0:3]), Vector(q_[3:6]), q_[6]
    CAM.location = cp; CAM.rotation_euler = (ct - cp).to_track_quat('-Z', 'Y').to_euler(); CAM.rotation_euler.rotate_axis('Z', roll)
    CAM.data.lens = lens; CAM.data.dof.focus_distance = (ct - cp).length
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.dof.use_dof = True; CAM.data.dof.aperture_fstop = 11; CAM.data.clip_start = 0.05
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
