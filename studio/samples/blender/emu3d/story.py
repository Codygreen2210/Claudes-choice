# The Great Emu War, told as a cardboard cut-out play on a Broadway stage (style a: clean painted flats with a white cut border).
# One continuous shot from the back of the house; the curtains part on frame one and close on the last, so it loops.
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
bpy.ops.object.text_add(location=(0, -0.9, OH + 1.38)); TX = bpy.context.object; TX.data.body = 'THE GREAT EMU WAR'; TX.data.align_x = 'CENTER'; TX.data.size = 0.5
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


# ---------------------------------------------------------------- the play: scenery and players (cut-outs)
OL, OR_ = -7.6, 7.6                                          # off stage left / right (behind the arch)
O = {}
O['wheat_back'] = cutout('wheat_back', 'wheat', 0.75, (1.0, 5.6, 0.0))
O['gum'] = cutout('gum', 'gumtree', 4.2, (3.4, 6.1, 0.0))
O['fence'] = cutout('fence', 'fence', 0.95, (-2.4, 4.6, 0.0))
O['sun'] = cutout('sun', 'sun', 1.3, (-1.6, 5.4, 4.6), brace=False); O['sun'].visible_shadow = False
SUNROD = cyl('sunrod', 0.012, 4.0, (-1.6, 5.42, 7.4), BLACK)
WHEAT_MID = [cutout(f'wheat_mid{k}', 'wheat', 0.6, (x, 3.0 + 0.05 * k, 0.0), brace=False) for k, x in enumerate((-0.9, 1.6, 4.1))]
O['wheat_front'] = cutout('wheat_front', 'wheat', 0.42, (0.6, 0.75, 0.0))
O['wheat_front2'] = cutout('wheat_front2', 'wheat', 0.38, (-3.0, 0.8, 0.0))
# the army
ARMY = {
    'major':   (cutout('major', 'major', 1.82, (0, 0, 0)), Vector((-3.4, 1.35, 0.0)), 0.0),
    'sold1':   (cutout('sold1', 'soldier', 1.78, (0, 0, 0)), Vector((-2.75, 2.45, 0.0)), 0.25),
    'lewis1':  (cutout('lewis1', 'lewis', 0.75, (0, 0, 0)), Vector((-2.15, 2.25, 0.0)), 0.35),
    'sold2':   (cutout('sold2', 'soldier', 1.78, (0, 0, 0)), Vector((-1.85, 3.45, 0.0)), 0.5),
    'lewis2':  (cutout('lewis2', 'lewis', 0.75, (0, 0, 0)), Vector((-1.25, 3.3, 0.0)), 0.6),
    'crate1':  (cutout('crate1', 'crate', 0.5, (0, 0, 0)), Vector((-4.1, 2.7, 0.0)), 0.7),
    'crate2':  (cutout('crate2', 'crate', 0.5, (0, 0, 0)), Vector((-3.7, 3.3, 0.0)), 0.8),
}
MUZZLE = Vector((0.73, -0.02, 0.405))
FLASH = [cutout(f'flash{k}', 'flash', 0.42, (0, 0, 0), brace=False) for k in range(2)]
SMOKE = cutout('smoke', 'smoke', 0.8, (0, 0, 0), brace=False); SPRING = cutout('spring', 'spring', 0.35, (0, 0, 0), brace=False)
DUST = [cutout(f'dust{k}', 'dust', 0.45, (0, 0, 0), brace=False) for k in range(8)]
# the truck with a gunner and a gun on the tray
TRUCK = cutout('truck', 'truck', 1.9, (OL - 3, 4.1, 0.0))
TGUN = cutout('tgun', 'lewis', 0.7, (0, 0, 0), brace=False); TGUN.parent = TRUCK; TGUN.location = (-0.7, 0.05, 0.62)
TSOLD = cutout('tsold', 'soldier', 1.6, (0, 0, 0), brace=False); TSOLD.parent = TRUCK; TSOLD.location = (-1.25, 0.1, 0.62)
# the dam and the bush for the ambush
POND = cutout('pond', 'pond', 0.55, (OR_ + 4, 3.9, 0.0), brace=False)
BUSH = cutout('bush', 'bush', 1.2, (OL - 2, 1.45, 0.0))
# the farmer and his bag of bounty money
FARMER = cutout('farmer', 'farmer', 1.76, (OR_ + 2, 2.0, 0.0)); BAG = cutout('bag', 'moneybag', 0.42, (0, 0, 0), brace=False)
BAG.parent = FARMER; BAG.location = (0.45, -0.03, 0.62)
# the emus: a dozen, each a body on a brace with a neck piece that bobs
class Emu:
    def __init__(self, k):
        self.k = k; self.body = cutout(f'emu{k}', 'emu_body', 1.15, (OR_ + 2, 2.0, 0.0))
        self.neck = cutout(f'emuneck{k}', 'emu_neck', 0.92, (0, 0, 0), brace=False); self.neck.parent = self.body; self.neck.location = (-0.30, -0.012, 0.72)
        self.segs = []                                    # (t0, t1, (x0, y0), (x1, y1), hop)
        self.drink = []                                   # (t0, t1) head down
    def go(self, t0, t1, p0, p1, hop=0.12): self.segs.append((t0, t1, p0, p1, hop)); return self
EMUS = [Emu(k) for k in range(12)]
CAP = cutout('cap', 'cap', 0.16, (0, 0, 0), brace=False)
TANK = cutout('tankemu', 'emu_body', 1.15, (OR_ + 3, 1.75, 0.0), brace=False)
TANKNECK = cutout('tankneck', 'emu_neck', 0.92, (0, 0, 0), brace=False); TANKNECK.parent = TANK; TANKNECK.location = (-0.30, -0.012, 0.72)
TREADS = cutout('treads', 'treads', 0.36, (0, 0, 0), brace=False); TREADS.parent = TANK; TREADS.location = (0.0, -0.03, -0.08)

# ---- the emus' moves, beat by beat
rr = random.Random(12)
SPOTS = [(0.6, 1.7), (1.5, 2.3), (2.4, 1.6), (3.2, 2.6), (4.2, 1.9), (1.0, 3.6), (2.2, 3.9), (3.7, 4.1)]
for k in range(8):                                                       # 1: they hop in over the wheat
    t0 = 0.25 + 0.42 * k; EMUS[k].go(t0, t0 + 1.7, (OR_, SPOTS[k][1]), SPOTS[k])
for k, dx in ((1, -0.9), (3, -1.1), (5, -0.8), (6, -1.0)):           # 2: tramping through the wheat
    t0 = B[1] + 0.3 + 0.5 * (k % 3); x, y = SPOTS[k]; EMUS[k].go(t0, t0 + 1.4, (x, y), (x + dx, y - 0.3), 0.08)
def last(e, t):
    p = e.segs[-1][3] if e.segs else (OR_, 2.0)
    return p
FIRE1 = B[3] + 0.6
for k in range(8):                                                       # 4: the first shots: they split into small groups and run
    p = last(EMUS[k], FIRE1); dst = [(OR_, 1.4), (OR_, 4.6), (OR_ - 1.0, 6.5)][k % 3]; t0 = FIRE1 + 0.35 + 0.07 * k
    EMUS[k].go(t0, t0 + 1.25, p, dst, 0.22)
POND_SPOTS = [(0.2, 2.9), (0.9, 2.6), (1.7, 2.7), (2.5, 2.6), (3.2, 2.9), (0.5, 4.6), (1.3, 4.8), (2.1, 4.9), (2.9, 4.7), (3.6, 4.5), (4.2, 3.3), (-0.4, 3.6)]
for k in range(12):                                                      # 5: a thousand emus walk up to the dam
    t0 = B[4] + 0.4 + 0.22 * k; EMUS[k].go(t0, t0 + 1.9, (OR_, POND_SPOTS[k][1]), POND_SPOTS[k], 0.1); EMUS[k].drink.append((t0 + 2.0, B[5] + 1.0))
JAM = B[5] + 0.85
for k in range(12):                                                      # 6: the gun jams and they scatter
    t0 = JAM + 0.35 + 0.05 * k; EMUS[k].go(t0, t0 + 1.1, POND_SPOTS[k], (OR_, POND_SPOTS[k][1] + rr.uniform(-1, 1)), 0.25)
for k in range(5):                                                       # 7: the truck chase: they run ahead and pull away
    t0 = B[6] + 0.35 + 0.3 * k; y = 1.5 + 0.45 * k; EMUS[k].go(t0, t0 + 3.6, (OL, y), (OR_, y), 0.28)
for k in range(6):                                                       # 10: they come back, dodge the guns, then line up for the bow
    t0 = B[9] + 0.2 + 0.25 * k; p = (0.8 + 0.7 * k, 1.8 + 0.5 * (k % 3)); EMUS[k + 1].go(t0, t0 + 1.4, (OR_, p[1]), p, 0.12)
    td = B[9] + 1.9 + 0.1 * k; q = (p[0] + rr.choice((-0.7, 0.7)), p[1] + rr.uniform(-0.3, 0.3)); EMUS[k + 1].go(td, td + 0.35, p, q, 0.35)
LINE = [(-2.6 + 0.85 * i, 1.95 + 0.12 * (i % 2)) for i in range(7)]
for i in range(7):
    e = EMUS[i + 1] if i < 6 else EMUS[7]
    if i == 6: e.go(B[10] - 0.6, B[10] + 0.4, (OR_, 2.0), LINE[i], 0.12)
    else: e.go(B[10] - 0.15 + 0.05 * i, B[10] + 0.6 + 0.05 * i, last(e, 0), LINE[i], 0.12)
BOW = B[10] + 0.75
def emu_state(e, t):
    """position, hop height and which way it faces (1 = left as drawn, -1 = turned round)"""
    if not e.segs or t < e.segs[0][0]: return None
    cur = None
    for s_ in e.segs:
        if t >= s_[0]: cur = s_
    t0, t1, p0, p1, hop = cur; u = clamp((t - t0) / (t1 - t0), 0, 1)
    x = lerp(p0[0], p1[0], u); y = lerp(p0[1], p1[1], u); z = abs(math.sin(math.pi * u * max(2, round((t1 - t0) * 3.2)))) * hop * (0 < u < 1)
    face = 1.0 if p1[0] <= p0[0] else -1.0
    prev = 1.0
    for s_ in e.segs:
        if s_ is cur: break
        prev = 1.0 if s_[3][0] <= s_[2][0] else -1.0
    fl = smooth(t0, t0 + 0.25, t); f = lerp(prev, face, fl) if prev != face else face
    if u >= 1 and (abs(p1[0]) >= OR_ - 0.01): return None                  # gone off stage
    return x, y, z, f, 0 < u < 1

# ---------------------------------------------------------------- per-frame
def hide(o, v):
    """hide a cut-out with everything hung on it (brace, block, neck, cap ...)"""
    o.hide_render = v
    for c in o.children: hide(c, v)
def slide(o, home, t_in, t_out, t, dx_in=-6.5, dx_out=-7.0, hop=0.07, rock=6.0):
    """on a track: slide in at t_in, out at t_out (None = stays); hops and rocks while moving, settles with a wobble"""
    u = smooth(t_in, t_in + 1.0, t); w = smooth(t_out, t_out + 1.0, t) if t_out is not None else 0.0
    off = dx_in * (1 - u) + dx_out * w; moving = (0 < u < 1) or (0 < w < 1)
    hide(o, (u <= 0) or (w >= 1))
    o.location = home + Vector((off, 0, abs(math.sin(t * 11.0)) * hop if moving else 0.0))
    land = max(0.0, t - (t_in + 1.0)); wob_ = math.exp(-land * 4.5) * math.sin(land * 18) * (land > 0) * (w <= 0)
    o.rotation_euler.y = R(rock) * (math.sin(t * 11.0) if moving else 0.0) + R(5) * wob_
def army(t):
    # in for the first trip, out after six days, back for another month, out for good; the major also comes back alone for his quote
    for nm, (o, home, st) in ARMY.items():
        if t < B[8]: slide(o, home, B[2] + 0.15 + st, B[7] + 0.1 + st * 0.6, t)
        elif nm == 'major':
            if t < B[9] + 0.2: slide(o, Vector((-0.45, 1.6, 0.0)), B[8] + 0.05, B[9] - 0.25, t)
            else: slide(o, home, B[9] + 0.25, B[9] + 3.0, t)
        else: slide(o, home, B[9] + 0.25 + st * 0.5, B[9] + 3.0 + st * 0.4, t)
def firing(t):
    shots = [(FIRE1, FIRE1 + 0.9, 0), (FIRE1 + 0.15, FIRE1 + 0.9, 1), (B[5] + 0.25, JAM, 0), (B[9] + 1.6, B[9] + 2.4, 0), (B[9] + 1.7, B[9] + 2.4, 1)]
    for k, fl in enumerate(FLASH):
        on = any(a <= t < b and g == k for a, b, g in shots) and int(t * 14 + k) % 2 == 0
        g_ = ARMY['lewis1' if k == 0 else 'lewis2'][0]; hide(fl, not on or g_.hide_render)
        if on:
            fl.location = g_.location + MUZZLE + Vector((0.12, -0.03, -0.2)); fl.rotation_euler.y = (int(t * 14) % 3) * 0.6
            g_.location.x += 0.02 * math.sin(t * 90); g_.rotation_euler.y = R(1.5) * math.sin(t * 70)
    # the jam: a cough of smoke and a spring that boings out
    g1 = ARMY['lewis1'][0]; u = clamp((t - JAM) / 1.4, 0, 1)
    hide(SMOKE, not (0 < u < 1)); SMOKE.location = g1.location + Vector((0.1, -0.05, 0.35 + 0.5 * u)); SMOKE.scale = (0.4 + 0.9 * u,) * 3
    v = clamp((t - JAM) / 1.0, 0, 1); hide(SPRING, not (0 < v < 1))
    SPRING.location = g1.location + Vector((0.6 * v, -0.08, 0.4 + 2.2 * v - 2.6 * v * v)); SPRING.rotation_euler.y = 9 * v
    # dust where they break and run
    for k, d_ in enumerate(DUST):
        for t0, base in ((FIRE1 + 0.35, SPOTS), (JAM + 0.35, POND_SPOTS)):
            uu = (t - t0 - 0.1 * k) / 0.7
            if 0 < uu < 1:
                x, y = base[k % len(base)]; d_.location = (x + 0.2, y - 0.2, 0.0); d_.scale = (0.4 + uu, 1, 0.4 + uu); break
        else: uu = -1
        hide(d_, not (0 < uu < 1))
def frame(f):
    t = f / FPS; S.frame_set(f)
    # curtains: part on frame one, close at the end back to the same gap (loops)
    o_ = lerp(0.06, 1.0, smooth(0.0, 2.6, t)) * (1 - smooth(B[11] + 0.9, TOTAL, t)) + 0.06 * smooth(B[11] + 0.9, TOTAL, t)
    for d_ in DRAPES: d_.set(o_, t)
    chase = int(t * 6) % 2
    BULB_A.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 9.0 if chase else 3.0
    BULB_B.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0 if chase else 9.0
    sz = lerp(10.5, 4.6, back_out(0.5, 1.7, t, 1.2)); sw = R(6) * math.exp(-max(t - 1.7, 0) * 2.5) * math.sin(max(t - 1.7, 0) * 9)
    O['sun'].location = Vector((-1.6, 5.4, sz)); O['sun'].rotation_euler.y = sw; SUNROD.location.z = sz + 3.3
    # the wheat they tramp flat
    for k, w_ in enumerate(WHEAT_MID):
        tf = B[1] + 0.9 + 0.75 * k; u = back_out(tf, tf + 0.45, t, 0.8); w_.rotation_euler.x = R(-78) * u
    army(t); firing(t)
    # the ambush: the dam slides in from the right, a bush from the left; both go before the truck
    slide(POND, Vector((1.8, 3.9, 0.0)), B[4] + 0.05, B[6] + 0.1, t, dx_in=8.0, dx_out=8.0, hop=0.0, rock=0.0)
    slide(BUSH, Vector((-1.6, 1.45, 0.0)), B[4] + 0.2, B[6] + 0.1, t, dx_in=-6.0, dx_out=-6.0, hop=0.04, rock=3.0)
    # the truck: rolls in bucking behind the emus, can't catch them, the gunner can't hold the gun; backs out
    tin = clamp((t - (B[6] + 0.7)) / 4.6, 0, 1); tout = smooth(B[7] + 0.1, B[7] + 1.3, t)
    hide(TRUCK, tin <= 0 or tout >= 1)
    TRUCK.location = (lerp(-7.0, 3.0, tin) - 10.0 * tout, 3.7, abs(math.sin(t * 7.0)) * 0.28 * (0 < tin < 1 or 0 < tout < 1))
    TRUCK.rotation_euler.y = R(7) * math.sin(t * 8.5) * (0 < tin < 1)
    TSOLD.location.z = 0.62 + abs(math.sin(t * 9 + 1)) * 0.38 * (0 < tin < 1); TSOLD.rotation_euler.y = R(16) * math.sin(t * 6.5) * (0 < tin < 1)
    TGUN.location.z = 0.62 + abs(math.sin(t * 10 + 2)) * 0.3 * (0 < tin < 1); TGUN.rotation_euler.y = R(22) * math.sin(t * 7.5) * (0 < tin < 1)
    # Meredith's quote: an emu on tank treads rolls up to the major
    ti = smooth(B[8] + 0.25, B[8] + 1.5, t); to = smooth(B[9] - 0.3, B[9] + 0.5, t)
    hide(TANK, ti <= 0 or to >= 1); TANK.location = (lerp(OR_ + 1.0, 1.25, ti) + 8.0 * to, 1.75, 0.0); TANK.rotation_euler.y = R(2) * math.sin(t * 20) * (0 < ti < 1)
    TANKNECK.rotation_euler.y = R(-6 + 4 * math.sin(t * 2.5))
    if B[8] + 1.3 < t < B[9] - 0.2:
        mj = ARMY['major'][0]; mj.rotation_euler.y = R(-10) * smooth(B[8] + 1.3, B[8] + 1.7, t) + R(2) * math.sin(t * 7)
    # the farmer and his bounty money
    slide(FARMER, Vector((4.3, 2.3, 0.0)), B[9] + 3.3, None, t, dx_in=5.0, hop=0.06, rock=5.0)
    BAG.rotation_euler.y = R(10) * math.sin(t * 4.0)
    # the emus
    for e in EMUS:
        s_ = emu_state(e, t)
        if s_ is None: hide(e.body, True); continue
        x, y, z, fc, mv = s_; hide(e.body, False); e.body.location = (x, y, z); e.body.scale.x = fc
        e.body.rotation_euler.y = R(-7) * fc * mv * (abs(x - (OR_ if fc < 0 else OL)) > 0.1)
        dn = max([smooth(a, a + 0.4, t) * (1 - smooth(b, b + 0.3, t)) for a, b in e.drink] + [0.0])
        e.neck.rotation_euler.y = R(9 * math.sin(t * (3.1 + 0.4 * e.k) + e.k * 1.7) * (1 - dn) - 55 * dn * (0.85 + 0.15 * math.sin(t * 6 + e.k)))
        bw = smooth(BOW, BOW + 0.3, t) * (1 - smooth(BOW + 0.7, BOW + 1.0, t)) if e.k in range(1, 8) else 0.0
        e.body.rotation_euler.x = R(22) * bw
    # the cap on the middle emu at the end
    ce = EMUS[4]; on = (t >= B[10] - 0.1) and not ce.body.hide_render
    hide(CAP, not on)
    if on:
        bpy.context.view_layer.update(); M = ce.neck.matrix_world; CAP.location = M @ Vector((-0.07, -0.02, 0.86)); CAP.rotation_euler = (ce.body.rotation_euler.x, ce.neck.rotation_euler.y + R(-8), 0); CAP.scale.x = ce.body.scale.x
    # followspots: up for the quote and the bow
    fu = smooth(B[8] + 0.6, B[8] + 1.2, t) * (1 - smooth(B[9], B[9] + 0.5, t)) + smooth(BOW - 0.6, BOW, t) * (1 - smooth(B[11] + 0.9, B[11] + 1.8, t))
    for l_ in FS: l_.data.energy = 14000 * fu
    FS[0].rotation_euler = (Vector((-0.45, 1.6, 0.9)) - FS[0].location).to_track_quat('-Z', 'Y').to_euler()
    FS[1].rotation_euler = (Vector((1.25 if t < B[10] else -0.0, 1.9, 0.9)) - FS[1].location).to_track_quat('-Z', 'Y').to_euler()
    # camera: from the back of the house in to the stage; rests on each beat; in close for the quote; back out to the start at the end
    MID = lambda x_, d=2.0, z=1.5, lz=1.25, lens_=16: ((x_, -0.5 * d, 0.6 + 0.25 * z), (x_ + 0.1, 3.0, 0.75 + 0.25 * lz), 18)
    K = [(0.0, (0.0, -13.8, 3.2), (0.0, 3.0, 3.3), 22), (3.4, (0.6, -5.6, 2.3), (0.8, 3.0, 2.0), 19),
         (B[1], *MID(1.9)), (B[2] - 0.3, *MID(1.7, 2.1)),                                  # the emus in the wheat
         (B[2] + 1.4, *MID(-2.0, 1.9)), (B[3] - 0.2, *MID(-1.8)),                          # the army arrives
         (B[3] + 0.5, *MID(0.2, 2.6, 1.6, 1.3)), (B[4] - 0.1, *MID(0.2, 2.6, 1.6, 1.3)),     # first shots, they split up
         (B[4] + 0.8, *MID(0.6, 2.4, 1.55, 1.2)), (B[5] - 0.2, *MID(0.5, 2.4, 1.55, 1.2)),   # the dam
         (B[5] + 0.6, (-1.6, -1.0, 1.35), (-2.0, 2.4, 0.9), 20), (B[6] - 0.1, (-1.5, -0.9, 1.35), (-1.9, 2.4, 0.9), 20),   # the jam
         (B[6] + 1.0, *MID(0.4, 3.2, 1.75, 1.3)), (B[8] - 0.1, *MID(0.3, 3.1, 1.75, 1.3)),   # the truck, the army leaves
         (B[8] + 1.0, (0.85, -1.15, 1.45), (0.35, 2.0, 1.1), 24), (B[9] - 0.2, (0.75, -1.0, 1.42), (0.35, 2.0, 1.1), 24),   # the quote
         (B[9] + 0.9, *MID(0.9, 2.6, 1.6, 1.3)), (B[10] - 0.3, *MID(1.3, 2.5, 1.6, 1.3)),    # another month, the bounty
         (B[10] + 0.6, *MID(-0.2, 3.3, 1.75, 1.4)), (B[11] + 0.8, *MID(-0.1, 4.0, 2.0, 1.6, 17)),   # the bow
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

