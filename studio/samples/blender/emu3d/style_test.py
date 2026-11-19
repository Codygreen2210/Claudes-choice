# Style tests for the cardboard cut-out stage play: the art from art.py cut out along its alpha edge, given thickness, propped on
# braces on a wooden stage with a painted backdrop, velvet curtains and footlights.
#   python3 style_test.py OUTDIR STYLE(a|b) SHOT(wide|close) [--scale 0.75] [--samples 32]
#   a = clean painted stage flats with a white cut border;  b = rough hand-cut cardboard, paint worn so the board shows through
import sys, os, math, random
import bpy, bmesh
import numpy as np, cv2
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.join(HERE, 'art')
OUT, STYLE, SHOT = sys.argv[1], sys.argv[2], sys.argv[3]
SC = float(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 0.75
SAMP = int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 32
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'props')); import props_bpy as P
bpy.ops.wm.read_factory_settings(use_empty=True); S = bpy.context.scene
P.set_scene_dir(HERE)
R = math.radians; rr = random.Random(3)

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
def cutout(name, img_name, height, loc, yaw=0.0, thick=None, brace=True, flip=False):
    path = os.path.join(ART, img_name + '.png'); im = cv2.imread(path, cv2.IMREAD_UNCHANGED); H, W = im.shape[:2]
    a = (im[:, :, 3] > 100).astype(np.uint8) * 255
    grow = int(0.012 * H) if STYLE == 'a' else int(0.011 * H)
    a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1)))
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    cs, _ = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 0.0018 * H if STYLE == 'a' else 0.004 * H, True)[:, 0, :].astype(float)
    k = height / H
    if STYLE == 'b':                                     # a wobbly hand-cut line
        r2 = random.Random(hash(name) & 0xffff)
        c = np.array([(x + r2.uniform(-1, 1) * 0.004 * H, y + r2.uniform(-1, 1) * 0.004 * H) for x, y in c])
    bm = bmesh.new(); vs = [bm.verts.new(((x - W / 2) * k, 0.0, (H - y) * k)) for x, y in c]
    f = bm.faces.new(vs); bm.normal_update()
    if f.normal.y > 0: f.normal_flip()                   # face toward -y (the audience)
    uv = bm.loops.layers.uv.new('UV')
    for lp in f.loops: lp[uv].uv = (lp.vert.co.x / (W * k) + 0.5, lp.vert.co.z / (H * k))
    bmesh.ops.triangulate(bm, faces=[f]); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    o.data.materials.append(art_mat(name, path)); o.data.materials.append(BOARD); o.data.materials.append(EDGE)
    sol = o.modifiers.new('board', 'SOLIDIFY'); sol.thickness = thick or (0.012 if STYLE == 'a' else 0.014); sol.offset = 1.0
    sol.use_rim = True; sol.material_offset = 1; sol.material_offset_rim = 2
    o.location = loc; o.rotation_euler = (0, 0, yaw); o.scale.x = -1 if flip else 1
    if brace:   # a triangle brace behind, and a sandbag/block at its foot
        bh = min(height * 0.55, 1.1); br = mesh_tri(name + '_brace', bh)
        br.parent = o; br.location = (0, 0.012, 0.0)
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

# ---------------------------------------------------------------- the stage
SW, SD = 14.0, 8.0
box('stage', (SW, SD, 1.0), (0, SD / 2 - 0.5, -0.5), FLOOR)
box('apron_front', (SW, 0.06, 1.0), (0, -0.53, -0.5), flat('apronblack', (0.03, 0.025, 0.02), 0.9))
# painted backdrop on a batten
bdm, nt, b = node_mat('backdrop'); it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(os.path.join(ART, 'backdrop.png')); nt.links.new(it.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.95
if STYLE == 'b':
    m3 = nt.nodes.new('ShaderNodeMix'); m3.data_type = 'RGBA'; m3.blend_type = 'MULTIPLY'; m3.inputs['Factor'].default_value = 0.25
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 30.0; nt.links.new(it.outputs['Color'], m3.inputs['A']); nt.links.new(n2.outputs['Color'], m3.inputs['B']); nt.links.new(m3.outputs['Result'], b.inputs['Base Color'])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 7.2, 3.5), rotation=(R(90), 0, 0)); BD = bpy.context.object; BD.scale = (14.0, 7.0, 1); BD.data.materials.append(bdm)
# a gentle sag/ripple in the cloth
bpy.ops.object.transform_apply(scale=True); sd = BD.modifiers.new('sub', 'SUBSURF'); sd.subdivision_type = 'SIMPLE'; sd.levels = sd.render_levels = 5
tx = bpy.data.textures.new('rip', 'CLOUDS'); tx.noise_scale = 1.6; dp = BD.modifiers.new('rip', 'DISPLACE'); dp.texture = tx; dp.strength = 0.08; dp.direction = 'Z'
cyl('batten', 0.05, 14.4, (0, 7.2, 7.05), BLACK, (0, R(90), 0))
# proscenium arch and velvet curtains (pulled to the sides, with swags)
PM = flat('proscenium', (0.08, 0.06, 0.05), 0.6)
box('pros_l', (1.2, 0.5, 9.0), (-7.3, -0.3, 4.0), PM); box('pros_r', (1.2, 0.5, 9.0), (7.3, -0.3, 4.0), PM); box('pros_t', (15.8, 0.5, 1.4), (0, -0.3, 8.2), PM)
for x0 in (-6.2, 6.2):
    vs = []; fs = []; n = 40
    for j in range(2):
        z = 7.6 if j else 0.0
        for i in range(n + 1):
            u = i / n; x = x0 + (u - 0.5) * (2.2 if j else 1.5); y = -0.05 + 0.10 * math.sin(u * math.pi * 9)
            vs.append((x, y, z))
    for i in range(n): fs.append((i, i + 1, n + 2 + i, n + 1 + i))
    me = bpy.data.meshes.new('curtain'); me.from_pydata(vs, [], fs); me.update(); o = bpy.data.objects.new('curtain', me); S.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    o.data.materials.append(VELVET); s = o.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.04
vs = []; fs = []; n = 60
for j in range(2):
    for i in range(n + 1):
        u = i / n; x = (u - 0.5) * 13.2; z = 7.5 - (0.0 if j else 0.9 + 0.35 * abs(math.sin(u * math.pi * 3))); y = -0.1 + 0.08 * math.sin(u * math.pi * 14)
        vs.append((x, y, z))
for i in range(n): fs.append((i, i + 1, n + 2 + i, n + 1 + i))
me = bpy.data.meshes.new('valance'); me.from_pydata(vs, [], fs); me.update(); o = bpy.data.objects.new('valance', me); S.collection.objects.link(o)
for p in me.polygons: p.use_smooth = True
o.data.materials.append(VELVET); s = o.modifiers.new('t', 'SOLIDIFY'); s.thickness = 0.04
# footlights: a row of hooded bulbs along the front edge
BULB = flat('bulb', (1, 0.9, 0.7), 0.3, (1.0, 0.82, 0.55), 6.0)
for k in range(15):
    x = -6.3 + k * 0.9; box(f'hood{k}', (0.34, 0.16, 0.12), (x, -0.32, 0.06), BLACK); cyl(f'bulb{k}', 0.05, 0.06, (x, -0.26, 0.08), BULB, (R(90), 0, 0))

# ---------------------------------------------------------------- the scene on stage
O = {}
O['wheat_back'] = cutout('wheat_back', 'wheat', 0.75, (1.0, 5.6, 0.0), brace=True)
O['gum'] = cutout('gum', 'gumtree', 4.2, (3.6, 6.1, 0.0))
O['fence'] = cutout('fence', 'fence', 0.95, (-2.6, 4.6, 0.0))
O['sun'] = cutout('sun', 'sun', 1.3, (-1.6, 5.4, 4.6), brace=False)
cyl('sunrod', 0.012, 2.6, (-1.6, 5.42, 6.6), BLACK)
for o in [O['sun']] + list(O['sun'].children): o.visible_shadow = False
O['truck'] = cutout('truck', 'truck', 1.9, (-3.0, 4.0, 0.0))
O['lewis'] = cutout('lewis', 'lewis', 0.75, (-1.15, 2.3, 0.0))
O['soldier'] = cutout('soldier', 'soldier', 1.78, (-2.25, 2.55, 0.0))
O['major'] = cutout('major', 'major', 1.82, (-0.2, 1.6, 0.0))
EMUS = []
for k, (x, y, yaw, tilt) in enumerate(((1.25, 1.75, 0.0, 6), (2.9, 3.0, 0.05, -10), (3.9, 2.4, -0.04, 14), (5.0, 3.4, 0.03, -4), (2.4, 4.2, 0.0, 0))):
    body = cutout(f'emu{k}', 'emu_body', 1.15, (x, y, 0.0), yaw)
    neck = cutout(f'emuneck{k}', 'emu_neck', 0.92, (0, 0, 0), brace=False)
    neck.parent = body; neck.location = (-0.30, -0.012, 0.72); neck.rotation_euler = (0, R(tilt), 0)
    EMUS.append(body)
O['wheat_front'] = cutout('wheat_front', 'wheat', 0.6, (0.6, 0.55, 0.0), brace=True)

# ---------------------------------------------------------------- lights: warm key spots from the front of house, a cool top wash, footlight glow
P.hdri('ph:theater_01', 0.12, 0)
def spot(name, loc, aim, power, col, size=R(28), blend=0.4, rad=0.9):
    L = bpy.data.lights.new(name, 'SPOT'); L.energy = power; L.color = col; L.spot_size = size; L.spot_blend = blend; L.shadow_soft_size = rad
    o = bpy.data.objects.new(name, L); S.collection.objects.link(o); o.location = loc
    d = Vector(aim) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); return o
spot('key_l', (-6.0, -9.0, 8.0), (-1.0, 2.5, 1.0), 22000, (1.0, 0.86, 0.68))
spot('key_r', (6.0, -9.0, 8.5), (2.5, 2.5, 1.0), 16000, (1.0, 0.9, 0.76))
spot('top', (0.0, 3.0, 9.0), (0.0, 3.5, 0.0), 3000, (0.75, 0.82, 1.0), R(70), 0.6, 1.0)
spot('drop', (0.0, 1.0, 9.5), (0.0, 7.1, 3.5), 9000, (1.0, 0.95, 0.85), R(100), 0.9, 2.0)
L = bpy.data.lights.new('foot', 'AREA'); L.shape = 'RECTANGLE'; L.size = 12.0; L.size_y = 0.2; L.energy = 600; L.color = (1.0, 0.75, 0.45)
fo = bpy.data.objects.new('foot', L); S.collection.objects.link(fo); fo.location = (0, -0.2, 0.2); fo.rotation_euler = (R(-70), 0, 0)
# a dark house in front of the stage so the camera never sees empty sky
box('house_floor', (40, 30, 0.2), (0, -16, -1.2), BLACK); box('house_back', (40, 0.2, 20), (0, -30, 6), BLACK)
for x in (-20, 20): box(f'house_side{x}', (0.2, 40, 20), (x, -8, 6), BLACK)
box('house_top', (40, 40, 0.2), (0, -8, 12), BLACK)

# ---------------------------------------------------------------- camera and render
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
if SHOT == 'wide': cp, ct, lens = (0.9, -2.9, 3.4), (0.9, 3.2, 1.25), 17
else:              cp, ct, lens = (1.7, -1.1, 1.45), (0.35, 2.0, 1.1), 24
cam.location = cp; cam.rotation_euler = (Vector(ct) - Vector(cp)).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (Vector(ct) - Vector(cp)).length * 0.95; cam.data.dof.aperture_fstop = 11
S.render.engine = 'CYCLES'; S.cycles.samples = SAMP; S.cycles.use_denoising = True
try: S.cycles.device = 'CPU'
except Exception: pass
S.render.resolution_x = int(1080 * SC); S.render.resolution_y = int(1920 * SC)
try: S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Punchy'
except Exception:
    try: S.view_settings.view_transform = 'Filmic'
    except Exception: pass
os.makedirs(OUT, exist_ok=True); S.render.filepath = os.path.join(OUT, f'style_{STYLE}_{SHOT}.png'); bpy.ops.render.render(write_still=True)
print('wrote', S.render.filepath)
