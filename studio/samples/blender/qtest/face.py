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
R = random.Random(7); tot = sum(a for *_, a in scalp_all); NSTR = 190000; roots = []
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
# ---- the haircut (owner, 2026-11-14: "the same hair style and cut as Tom Holland"): a textured crop. Sides and back tapered
# short (a few mm, lying down and back, shortest at the neck and around the ears); the top left long (4-6 cm, longest at the
# front), lifted off the scalp and pushed up and a little to the side at the front, with loose waves and curls that move in
# locks (clumps share a wave). The hairline comes from the smooth hair field; nothing crosses it.
_hm = He.to_mesh(); _hv = [H.matrix_world @ v.co for v in _hm.vertices]; HB = BVHTree.FromPolygons(_hv, [tuple(pl.vertices) for pl in _hm.polygons]); He.to_mesh_clear()
TOPZ0, TOPZ1 = ztop - 0.085, ztop - 0.050; NP = 9
def smooth(a, b, x): u = min(1.0, max(0.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
YC = (min(r_[0].y for r_ in roots) + max(r_[0].y for r_ in roots)) / 2   # middle of the scalp front-to-back (hc leans forward: it averages in the face)
CROWN = Vector((hc.x, YC + 0.03, ztop))                             # the crown: top centre, a little toward the back of the head
def groom(p0, seedv, ph):
    # hair grows out from the crown like real hair: forward toward the forehead, down the sides, down the back. The longer front
    # hair, on reaching the hairline, turns up and back over itself (pushed up and to one side) instead of lying on the forehead.
    top = smooth(TOPZ0, TOPZ1, p0.z)
    front = smooth(YC - 0.02, YC - 0.08, p0.y)
    neck = smooth(hc.z - 0.02, hc.z - 0.10, p0.z)
    top = max(top, smooth(YC - 0.04, YC - 0.08, p0.y) * smooth(ztop - 0.13, ztop - 0.10, p0.z))   # the whole front hairline belongs to the top
    R_ = random.Random(seedv)
    L = ((0.030 - 0.020 * neck) * (1 - top) + (0.058 + 0.014 * front) * top) * R_.uniform(0.8, 1.15)        # sides ~3 cm, top ~6-7 cm
    away = p0 - CROWN; away.z = 0.0
    if away.length < 1e-4: away = Vector((0, -1, 0))
    away.normalize(); swirl = Vector((-away.y, away.x, 0)) * 0.25                         # a slight clockwise swirl round the crown
    comb = (away + swirl + Vector((0.25, 0, 0)) * top).normalized()                      # everything drifts a little to his left
    _l0, _n0, _f0, _ = HB.find_nearest(p0); edge_in = smooth(0.5, 0.85, mask_at(_l0, _f0)) if _f0 is not None else 1.0
    lift = ((0.006 + 0.006 * front) * top + 0.003 * (1 - top) * (1 - neck)) * (0.45 + 0.55 * edge_in)
    jitter = Vector((R_.gauss(0, 0.08), R_.gauss(0, 0.08), 0)); pts = []; q = p0.copy(); flip = None
    for k in range(NP):
        s_ = k / (NP - 1)
        if flip is not None:                                            # past the hairline: rise up and curl back over the top
            up, back = flip; d = (up * max(0.15, 0.7 - 0.25 * (k - flip_k)) + back * (0.3 + 0.3 * (k - flip_k))).normalized()   # up, then rolling back over
            pts.append(pts[-1] + d * (L / (NP - 1))); continue
        loc, nrm, fi, _ = HB.find_nearest(q)
        if loc is None: loc, nrm = q, Vector((0, 0, 1))
        if k > 0 and (fi is None or mask_at(loc, fi) < 0.5):
            if front > 0.5 and top > 0.5:                               # front hair: flip up at the hairline (a quiff), never down the forehead
                flip = (Vector((0, -0.15, 1)).normalized(), Vector((0.2, 1, 0.3)).normalized()); flip_k = k
                pts.append(pts[-1] + flip[0] * (L / (NP - 1))); continue
            pts += [pts[-1]] * (NP - len(pts)); break
        t = (comb + jitter) - nrm * (comb + jitter).dot(nrm)
        if t.length < 1e-6: t = comb
        t.normalize()
        m_ = mask_at(loc, fi) if fi is not None else 1.0
        quiff = 0.014 * front * top * smooth(0.95, 0.55, m_) * min(1.0, s_ * 3)          # front hair rises as it nears the hairline: volume above the forehead
        h = lift * math.sin(min(1.0, s_ * 2.2) * math.pi / 2) + quiff + 0.0004
        pts.append(loc + nrm * h)
        q = loc + t * (L / (NP - 1))
    return pts, top
# ---- guides -> children -> Blender's own grooming nodes. ~600 evenly spread guide hairs carry the cut's shape; every other
# strand copies the shape of its nearest guides (so neighbours run together like real hair), then Blender's hair node assets
# (Clump, Curl, Noise, Set Profile from procedural_hair_node_assets.blend) gather locks, add the waves and taper the ends.
from mathutils.kdtree import KDTree as _KD
_sp = _KD(len(roots))
for i_, r_ in enumerate(roots): _sp.insert(r_[0], i_)
_sp.balance(); _taken = set(); gi = []
for i_ in range(len(roots)):
    if i_ in _taken: continue
    gi.append(i_); _taken.update(j for _, j, _ in _sp.find_range(roots[i_][0], 0.006))
GK = _KD(len(gi))
for j_, i_ in enumerate(gi): GK.insert(roots[i_][0], j_)
GK.balance(); guides = [groom(roots[i_][0], i_, 0.0)[0] for i_ in gi]
print('guides', len(gi))
cv = bpy.data.hair_curves.new('hair'); cv.add_curves([NP] * len(roots)); pos = []
for i_, (p0, n, ln) in enumerate(roots):
    near = GK.find_n(p0, 3); ws = [1.0 / (d * d + 1e-6) for _, _, d in near]; tw = sum(ws)
    for k in range(NP):
        off = sum(((guides[j][k] - guides[j][0]) * w for (_, j, _), w in zip(near, ws)), Vector()) / tw
        pt = p0 + off
        if k > 0:                                                       # keep every point outside the head
            loc, nrm, fi, _ = HB.find_nearest(pt)
            if loc is not None and (pt - loc).dot(nrm) < 0.0005: pt = loc + nrm * 0.0005
        pos.append(pt)
cv.points.foreach_set('position', [c for v in pos for c in v])
rad = cv.attributes.get('radius') or cv.attributes.new('radius', 'FLOAT', 'POINT')
rad.data.foreach_set('value', [0.00006] * len(pos))
HO = bpy.data.objects.new('hair', cv); S.collection.objects.link(HO)
_ap = os.path.join(bpy.utils.system_resource('DATAFILES'), 'assets', 'nodes', 'procedural_hair_node_assets.blend')
with bpy.data.libraries.load(_ap) as (src, dst): dst.node_groups = ['Clump Hair Curves', 'Curl Hair Curves', 'Hair Curves Noise', 'Set Hair Curve Profile']
gt = bpy.data.node_groups.new('groom', 'GeometryNodeTree'); gt.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
gt.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
gin = gt.nodes.new('NodeGroupInput'); gout = gt.nodes.new('NodeGroupOutput'); prev = gin.outputs[0]
def step(name, **vals):
    global prev
    nd = gt.nodes.new('GeometryNodeGroup'); nd.node_tree = bpy.data.node_groups[name]
    for k_, v_ in vals.items(): nd.inputs[k_].default_value = v_
    gt.links.new(prev, nd.inputs['Geometry']); prev = nd.outputs[0]
step('Clump Hair Curves', Factor=0.6, Shape=0.7, **{'Tip Spread': 0.0006, 'Distance Threshold': 0.012, 'Guide Distance': 0.009})
step('Curl Hair Curves', Factor=0.7, Radius=0.004, Frequency=0.45, **{'Curl Start': 0.15, 'Random Offset': 1.0, 'Guide Distance': 0.009})
step('Hair Curves Noise', Factor=0.15, Distance=0.0008, Scale=150.0)
step('Set Hair Curve Profile', Radius=0.00007, Shape=-0.4, **{'Replace Radius': True})
gt.links.new(prev, gout.inputs[0])
gm = HO.modifiers.new('groom', 'NODES'); gm.node_group = gt

hm_ = bpy.data.materials.new('strands'); hm_.use_nodes = True; tt = hm_.node_tree; [tt.nodes.remove(x) for x in list(tt.nodes) if x.bl_idname != 'ShaderNodeOutputMaterial']
hb = tt.nodes.new('ShaderNodeBsdfHairPrincipled'); hb.parametrization = 'MELANIN'
hb.inputs['Melanin'].default_value = 0.72; hb.inputs['Melanin Redness'].default_value = 0.6; hb.inputs['Roughness'].default_value = 0.36   # warm chestnut brown; hb.inputs['Radial Roughness'].default_value = 0.35
hb.inputs['Random Roughness'].default_value = 0.2; tt.links.new(hb.outputs[0], tt.nodes['Material Output'].inputs['Surface'])
cv.materials.append(hm_)
# undercoat: the haircut mesh pulled onto the scalp, flat dark brown, no strands of texture
uc = bpy.data.materials.new('undercoat'); uc.use_nodes = True; ub = uc.node_tree.nodes['Principled BSDF']; _at = uc.node_tree.nodes.new('ShaderNodeAttribute'); _at.attribute_name = 'fade'; _mr = uc.node_tree.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = 0.48; _mr.inputs['From Max'].default_value = 0.52; uc.node_tree.links.new(_at.outputs['Fac'], _mr.inputs['Value']); uc.node_tree.links.new(_mr.outputs['Result'], ub.inputs['Alpha']); ub.inputs['Base Color'].default_value = (0.03, 0.018, 0.01, 1); ub.inputs['Roughness'].default_value = 0.9
HM.hide_render = True
# undercoat: the haircut mesh shrunk smoothly onto the scalp, hair-coloured, so no scalp can show between strands
HM.hide_render = True; ub.inputs['Base Color'].default_value = (0.045, 0.022, 0.011, 1)
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
# owner, 2026-11-14: "just put the old hair back on from our previous character": MakeHuman's own short02 hair (darkened, as
# in the first face test) is the default; HAIR=strands brings back the groomed strand hair for later work.
if os.environ.get('HAIR', 'mesh') == 'mesh':
    HO.hide_render = True; UO.hide_render = True; HM.hide_render = False
    hmat = bpy.data.materials.get('Human.short02')
    if hmat:
        t = hmat.node_tree; hb_ = next(n for n in t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
        src = hb_.inputs['Base Color'].links[0].from_socket if hb_.inputs['Base Color'].links else None
        mx = t.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        if src: t.links.new(src, mx.inputs[6])
        mx.inputs[7].default_value = (0.16, 0.10, 0.07, 1); t.links.new(mx.outputs[2], hb_.inputs['Base Color'])
        hb_.inputs['Roughness'].default_value = 0.6; hb_.inputs['Specular IOR Level'].default_value = 0.3
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
