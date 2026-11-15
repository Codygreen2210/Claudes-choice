# Quality test, people: the MakeHuman man close up the way Zack D frames faces. Studio HDRI + warm key, skin with real
# subsurface scattering, short hair as a shell over the scalp, shallow depth of field.   python3 face.py OUT.png [--samples 64] [--scale 0.5]
import sys, os, math, argparse
import bpy, bmesh
from mathutils import Vector, Euler
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--samples', type=int, default=64); ap.add_argument('--scale', type=float, default=0.5)
ap.add_argument('--blend', default='/root/vt/n45/boat/man.blend'); a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(*p):
    for root in (os.path.join(HERE, 'assets'), '/root/vt/assets'):
        q = os.path.join(root, *p)
        if os.path.exists(q): return q
bpy.ops.wm.open_mainfile(filepath=a.blend)
S = bpy.context.scene; S.render.engine = 'CYCLES'
S.render.resolution_x = int(1080 * a.scale); S.render.resolution_y = int(1920 * a.scale); S.render.resolution_percentage = 100
C = S.cycles; C.device = 'CPU'; C.samples = a.samples; C.use_denoising = True; C.denoiser = 'OPENIMAGEDENOISE'; C.use_adaptive_sampling = True
try: S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
for o in list(S.objects):
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
W = bpy.data.worlds.new('w'); S.world = W; W.use_nodes = True; nt = W.node_tree; bg = nt.nodes['Background']
env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(asset('kloofendal_48d_partly_cloudy_puresky', 'kloofendal_48d_partly_cloudy_puresky_2k.hdr'))
mp = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp.inputs['Rotation'].default_value = (0, 0, math.radians(200))
nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], env.inputs['Vector']); nt.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.55
H = bpy.data.objects['Human']
# skin: rebuild the body material as a Principled BSDF with the MakeHuman diffuse map and proper subsurface
AK = next((d for d in (os.path.join(HERE, 'assets', 'aksel'), '/root/vt/mh/packs/keep/r2/skins/mindfront_aksel_skin') if os.path.isdir(d)), None)
def akimg(n, nc=False):
    im = bpy.data.images.load(os.path.join(AK, n)); im.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'; return im
JA = next((d for d in (os.path.join(HERE, 'assets', 'jartur'), '/root/vt/mh/packs/keep/r2/skins/jartur69_middleage_slavic_male_with_genitals_and_beard') if os.path.isdir(d)), None)
sk = bpy.data.images.load(os.path.join(JA, 'Jartur_mid_old_Slavic_Male_with_Genitals_and_Beard_lsdif_lighter_2k.jpg')) if JA else bpy.data.images.get('young_lightskinned_male_diffuse.png')   # CC0 middle-age male, stubble painted in
for mn in ('Human.body', 'Human.ears', 'Human.lips'):
    m = bpy.data.materials.get(mn)
    if not m: continue
    t = m.node_tree; [t.nodes.remove(n) for n in list(t.nodes) if n.bl_idname != 'ShaderNodeOutputMaterial']
    b = t.nodes.new('ShaderNodeBsdfPrincipled'); t.links.new(b.outputs[0], t.nodes['Material Output'].inputs['Surface'])
    if sk:
        im = t.nodes.new('ShaderNodeTexImage'); im.image = sk; hs = t.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 1.15; hs.inputs['Value'].default_value = 0.95
        t.links.new(im.outputs['Color'], hs.inputs['Color']); t.links.new(hs.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.42 if mn != 'Human.lips' else 0.3
    b.inputs['Subsurface Weight'].default_value = 0.35; b.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.2); b.inputs['Subsurface Scale'].default_value = 0.012
    b.inputs['Specular IOR Level'].default_value = 0.45
    oc = t.nodes.new('ShaderNodeTexCoord')
    vo = t.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 2600; t.links.new(oc.outputs['Object'], vo.inputs['Vector'])
    nz = t.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 700; nz.inputs['Detail'].default_value = 6; t.links.new(oc.outputs['Object'], nz.inputs['Vector'])
    pr = t.nodes.new('ShaderNodeMath'); pr.operation = 'MULTIPLY_ADD'; pr.inputs[1].default_value = 0.6; t.links.new(vo.outputs['Distance'], pr.inputs[0]); t.links.new(nz.outputs['Fac'], pr.inputs[2])
    bm_ = t.nodes.new('ShaderNodeBump'); bm_.inputs['Strength'].default_value = 0.35; bm_.inputs['Distance'].default_value = 0.0004
    if AK:                                                             # the skin's own normal map under the pores, its spec map drives shine
        nmi = t.nodes.new('ShaderNodeTexImage'); nmi.image = akimg('Aksel_Skin_NRM_2k.jpg', True); nmn = t.nodes.new('ShaderNodeNormalMap'); nmn.inputs['Strength'].default_value = 0.45
        t.links.new(nmi.outputs['Color'], nmn.inputs['Color']); t.links.new(nmn.outputs['Normal'], bm_.inputs['Normal'])
    t.links.new(pr.outputs[0], bm_.inputs['Height']); t.links.new(bm_.outputs['Normal'], b.inputs['Normal'])
    rv = t.nodes.new('ShaderNodeMapRange'); rv.inputs['To Min'].default_value = 0.34; rv.inputs['To Max'].default_value = 0.58; t.links.new(nz.outputs['Fac'], rv.inputs['Value'])
    if mn != 'Human.lips': t.links.new(rv.outputs['Result'], b.inputs['Roughness'])
# the shirt: plain colour (the stock texture carries a logo)
sm = bpy.data.materials.get('Human.male_casualsuit06')
if sm:
    sb = next(n for n in sm.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    for l in list(sb.inputs['Base Color'].links): sm.node_tree.links.remove(l)
    sb.inputs['Base Color'].default_value = (0.05, 0.12, 0.30, 1); sb.inputs['Roughness'].default_value = 0.8
# where is the head
dg = bpy.context.evaluated_depsgraph_get(); He = H.evaluated_get(dg); me = He.to_mesh()
vs = [H.matrix_world @ v.co for v in me.vertices]; ztop = max(v.z for v in vs)
head = [v for v in vs if v.z > ztop - 0.25]; hc = sum(head, Vector()) / len(head)
yfront = min(v.y for v in head)                                        # MakeHuman faces -Y
He.to_mesh_clear()
# hair: real strands (Blender hair curves), grown from the scalp out to the shape of MakeHuman's "short02" haircut, which is
# then shrunk onto the scalp as a dark undercoat so no skin shows through. Principled Hair BSDF (melanin), ~45k strands.
import random
from mathutils.bvhtree import BVHTree
HM = bpy.data.objects['Human.short02']; hme = HM.evaluated_get(dg).to_mesh(); hmw = HM.matrix_world
hv = [hmw @ v.co for v in hme.vertices]; hp = [tuple(p.vertices) for p in hme.polygons]
shell = BVHTree.FromPolygons(hv, hp); HM.evaluated_get(dg).to_mesh_clear()
me2 = He.to_mesh(); bvw = [H.matrix_world @ v.co for v in me2.vertices]
scalp = []; scalp_idx = set()
for pl in me2.polygons:
    c = sum((bvw[i] for i in pl.vertices), Vector()) / len(pl.vertices)
    if c.z < ztop - 0.17: continue
    loc, nrm, idx, d = shell.find_nearest(c)
    if loc is None or d > 0.03: continue
    n = (H.matrix_world.to_3x3() @ pl.normal).normalized()
    hit = shell.ray_cast(c + n * 0.0005, n, 0.035)
    if hit[0] is not None: ln = (hit[0] - c).length
    else:                                                               # the haircut dips into the head here: still scalp, short hair
        hit = shell.ray_cast(c + n * 0.0005, -n, 0.012)
        if hit[0] is None: continue
        ln = 0.0
    scalp.append(([bvw[i] for i in pl.vertices], n, max(ln, 0.007), pl.area)); scalp_idx.add(pl.index)
He.to_mesh_clear()
# ---- a smooth hairline: scalp membership per polygon is blocky (1 cm faces), so it's spread to the vertices and smoothed into a
# soft field; the hairline is where the field crosses 0.5, read between vertices, so it runs as a clean curve, not stair steps.
_mm = He.to_mesh(); NV = len(_mm.vertices); HMASK = [0.0] * NV
for pl in _mm.polygons:
    if pl.index in scalp_idx:
        for vi in pl.vertices: HMASK[vi] = 1.0
_nb = [[] for _ in range(NV)]
for e in _mm.edges: a__, b__ = e.vertices; _nb[a__].append(b__); _nb[b__].append(a__)
_head = [i for i in range(NV) if (H.matrix_world @ _mm.vertices[i].co).z > ztop - 0.26]
for _ in range(5):
    nm_ = HMASK[:]
    for i in _head:
        if _nb[i]: nm_[i] = 0.5 * HMASK[i] + 0.5 * sum(HMASK[j] for j in _nb[i]) / len(_nb[i])
    HMASK = nm_
POLYV = [tuple(pl.vertices) for pl in _mm.polygons]; VW = [H.matrix_world @ v.co for v in _mm.vertices]
RING = set(pl.index for pl in _mm.polygons if any(HMASK[vi] > 0.05 for vi in pl.vertices))
He.to_mesh_clear()
HB0 = BVHTree.FromPolygons(VW, POLYV)
def mask_at(pt, fi):
    vs = POLYV[fi]; ws = [1.0 / ((VW[vi] - pt).length + 1e-4) for vi in vs]; return sum(HMASK[vi] * w for vi, w in zip(vs, ws)) / sum(ws)

from mathutils.kdtree import KDTree
from mathutils import noise as mnoise
_eb = _bm_tmp = None
import bmesh as _bm0
_t = _bm0.new(); _me = He.to_mesh(); _t.from_mesh(_me); He.to_mesh_clear(); _t.faces.ensure_lookup_table()
_bverts = set()
for f in _t.faces:
    if f.index not in scalp_idx: continue
    for e in f.edges:
        if sum(1 for g in e.link_faces if g.index in scalp_idx) == 1: _bverts.update(tuple(H.matrix_world @ v.co) for v in e.verts)
_t.free(); EDGE = KDTree(len(_bverts))
for i_, v_ in enumerate(_bverts): EDGE.insert(v_, i_)
EDGE.balance()
_ring = []
for fi_ in RING:
    if fi_ in scalp_idx: continue
    vs_ = [VW[vi] for vi in POLYV[fi_]]; cc_ = sum(vs_, Vector()) / len(vs_); nn_ = (vs_[1] - vs_[0]).cross(vs_[-1] - vs_[0]).normalized()
    _ring.append((vs_, nn_, 0.007, ((vs_[1] - vs_[0]).cross(vs_[-1] - vs_[0])).length))
scalp_all = scalp + _ring
R = random.Random(7); tot = sum(a for *_, a in scalp_all); NSTR = 240000; roots = []
for verts, n, ln, ar in scalp_all:
    k = ar / tot * NSTR; k = int(k) + (1 if R.random() < k - int(k) else 0)
    for _ in range(k):
        a_, b_ = R.random(), R.random()
        if len(verts) == 4: p0 = (verts[0] * (1 - a_) + verts[1] * a_) * (1 - b_) + (verts[3] * (1 - a_) + verts[2] * a_) * b_   # whole quad
        else:
            if a_ + b_ > 1: a_, b_ = 1 - a_, 1 - b_
            p0 = verts[0] + (verts[1] - verts[0]) * a_ + (verts[-1] - verts[0]) * b_
        _l, _n, _fi, _ = HB0.find_nearest(p0)
        if _fi is not None and mask_at(_l, _fi) > 0.5: roots.append((p0, n, ln))   # only inside the smooth hairline, full density to it
# ---- the haircut: a short men's side-part. Sides and back clipped short (a few mm, lying down and back, shorter toward the
# neck); the top left longer (3-4 cm), lifted a little at the front and combed across from a part on his left; strands
# gathered into clumps so it reads as styled locks, not loose fuzz. Each strand walks over the head surface at a set height.
_hm = He.to_mesh(); _hv = [H.matrix_world @ v.co for v in _hm.vertices]; HB = BVHTree.FromPolygons(_hv, [tuple(pl.vertices) for pl in _hm.polygons]); He.to_mesh_clear()
PART_X = hc.x + 0.032; TOPZ0, TOPZ1 = ztop - 0.075, ztop - 0.045
def smooth(a, b, x): u = min(1.0, max(0.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
def groom(p0, seedv):
    top = smooth(TOPZ0, TOPZ1, p0.z) * (1 - smooth(hc.y + 0.06, hc.y + 0.10, p0.y))        # crown/back of the top blends into the short back
    front = smooth(hc.y - 0.02, hc.y - 0.07, p0.y)                                       # toward the forehead
    neck = smooth(hc.z - 0.02, hc.z - 0.10, p0.z)
    L = (0.005 - 0.0025 * neck) * (1 - top) + (0.034 + 0.008 * front) * top
    if p0.x < PART_X: comb_top = Vector((-0.8, 0.55 + 0.3 * front, 0.0))                # across and back from the part, off the forehead
    else: comb_top = Vector((0.9, 0.3, -0.35))                                           # the short side of the part falls down
    comb_side = Vector((0.0, 0.35, -1.0))
    comb = (comb_top.normalized() * top + comb_side.normalized() * (1 - top)).normalized()
    _l0, _n0, _f0, _ = HB.find_nearest(p0); edge_in = smooth(0.5, 0.85, mask_at(_l0, _f0)) if _f0 is not None else 1.0
    lift = ((0.004 + 0.005 * front) * top + 0.0008 * (1 - top)) * (0.25 + 0.75 * edge_in)   # volume on top, flat sides, low right at the hairline
    pts = []; q = p0.copy(); R_ = random.Random(seedv); L *= R_.uniform(0.75, 1.2)
    jitter = Vector((R_.gauss(0, 0.22), R_.gauss(0, 0.22), R_.gauss(0, 0.08)))
    for k in range(6):
        s_ = k / 5; loc, nrm, fi, _ = HB.find_nearest(q)
        if loc is None: loc, nrm = q, Vector((0, 0, 1))
        if k > 0 and (fi is None or mask_at(loc, fi) < 0.5):                 # walked past the hairline: end the strand at the last point
            pts += [pts[-1]] * (6 - len(pts)); break
        h = lift * math.sin(min(1.0, s_ * 2.2) * math.pi / 2) * (1 - 0.35 * s_ * s_) + 0.0004
        pts.append(loc + nrm * h)
        t = (comb + jitter) - nrm * (comb + jitter).dot(nrm)                                  # walk along the surface
        if t.length < 1e-6: t = comb
        q = loc + t.normalized() * (L / 5)
    return pts, top
# clumps: ~1/60 of the roots are guides; every top strand bends toward its guide's shape (stronger toward the tip); short side hair stays loose
from mathutils.kdtree import KDTree as _KD
gi = list(range(0, len(roots), 60)); GK = _KD(len(gi))
for j_, i_ in enumerate(gi): GK.insert(roots[i_][0], j_)
GK.balance(); guides = [groom(roots[i_][0], i_)[0] for i_ in gi]
cv = bpy.data.hair_curves.new('hair'); cv.add_curves([6] * len(roots)); pos = []
for i_, (p0, n, ln) in enumerate(roots):
    own, tp = groom(p0, i_); g = guides[GK.find(p0)[1]]; off = p0 - g[0]
    for k in range(6):
        c_ = 0.6 * tp * (k / 5) ** 1.2; pos.append(own[k] * (1 - c_) + (g[k] + off * (1 - k / 5)) * c_)
cv.points.foreach_set('position', [c for v in pos for c in v])
rad = cv.attributes.get('radius') or cv.attributes.new('radius', 'FLOAT', 'POINT')
rad.data.foreach_set('value', [(0.00006, 0.00006, 0.00005, 0.00004, 0.000025, 0.00001)[k % 6] for k in range(len(pos))])
HO = bpy.data.objects.new('hair', cv); S.collection.objects.link(HO)
hm_ = bpy.data.materials.new('strands'); hm_.use_nodes = True; tt = hm_.node_tree; [tt.nodes.remove(x) for x in list(tt.nodes) if x.bl_idname != 'ShaderNodeOutputMaterial']
hb = tt.nodes.new('ShaderNodeBsdfHairPrincipled'); hb.parametrization = 'MELANIN'
hb.inputs['Melanin'].default_value = 0.93; hb.inputs['Melanin Redness'].default_value = 0.3; hb.inputs['Roughness'].default_value = 0.42; hb.inputs['Radial Roughness'].default_value = 0.35
hb.inputs['Random Roughness'].default_value = 0.2; tt.links.new(hb.outputs[0], tt.nodes['Material Output'].inputs['Surface'])
cv.materials.append(hm_)
# undercoat: the haircut mesh pulled onto the scalp, flat dark brown, no strands of texture
uc = bpy.data.materials.new('undercoat'); uc.use_nodes = True; ub = uc.node_tree.nodes['Principled BSDF']; _at = uc.node_tree.nodes.new('ShaderNodeAttribute'); _at.attribute_name = 'fade'; _mr = uc.node_tree.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = 0.48; _mr.inputs['From Max'].default_value = 0.52; uc.node_tree.links.new(_at.outputs['Fac'], _mr.inputs['Value']); uc.node_tree.links.new(_mr.outputs['Result'], ub.inputs['Alpha']); ub.inputs['Base Color'].default_value = (0.03, 0.018, 0.01, 1); ub.inputs['Roughness'].default_value = 0.9
HM.hide_render = True
# undercoat: the haircut mesh shrunk smoothly onto the scalp, hair-coloured, so no scalp can show between strands
HM.hide_render = True; ub.inputs['Base Color'].default_value = (0.018, 0.011, 0.007, 1)
import bmesh as _bm
me3 = He.to_mesh(); ubm = _bm.new(); ubm.from_mesh(me3); He.to_mesh_clear(); ubm.faces.ensure_lookup_table(); ubm.verts.ensure_lookup_table()
fa = ubm.verts.layers.float.new('fade')
for v in ubm.verts: v[fa] = HMASK[v.index]                             # the smooth hair field (kept through the deletes below)
_bm.ops.delete(ubm, geom=[f for f in ubm.faces if f.index not in RING], context='FACES')
_bm.ops.delete(ubm, geom=[v for v in ubm.verts if not v.link_faces], context='VERTS')
ubm.normal_update()
for v in ubm.verts: v.co += v.normal * 0.0006                          # one connected skin-tight cap (shared corners: no blocks, no gaps)
um = bpy.data.meshes.new('undercoat'); ubm.to_mesh(um); ubm.free(); UO = bpy.data.objects.new('undercoat', um); S.collection.objects.link(UO)
UO.matrix_world = H.matrix_world; um.materials.append(uc)
for p_ in um.polygons: p_.use_smooth = True
print('hair strands', len(roots))
# lights: warm key from camera-left, cool rim from behind-right
def light(name, kind, loc, energy, color, size=0.5):
    L = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); S.collection.objects.link(L); L.location = loc; L.data.energy = energy; L.data.color = color
    if kind == 'AREA': L.data.size = size
    L.rotation_euler = (hc - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return L
light('key', 'AREA', hc + Vector((-0.9, -1.0, 0.5)), 120, (1.0, 0.88, 0.75), 0.8)
light('rim', 'AREA', hc + Vector((0.8, 0.9, 0.4)), 90, (0.75, 0.85, 1.0), 0.5)
# camera: 3/4 close-up, 85 mm, f/2
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.lens = 85; CAM.data.dof.use_dof = True; CAM.data.dof.aperture_fstop = 2.0
eye = Vector((hc.x, yfront + 0.03, hc.z + 0.01)); CAM.location = eye + Vector((-0.42, -1.05, 0.02))
CAM.rotation_euler = (eye + Vector((0, 0, -0.06)) - CAM.location).to_track_quat('-Z', 'Y').to_euler(); CAM.data.dof.focus_distance = (eye - CAM.location).length
S.render.filepath = a.out; bpy.ops.render.render(write_still=True); print('wrote', a.out)
