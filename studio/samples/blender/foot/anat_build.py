# Real anatomy for the foot-asleep Short: cuts the right leg out of the Z-Anatomy atlas (CC BY-SA 4.0, Gauthier Kervyn & Marcin
# Zielinski, models derived from BodyParts3D, DBCLS) into a small .blend: bones, the front/side shin muscles, the leg's nerves and
# arteries. Nerves and arteries come as curves in the atlas; they are turned into tubes of their real thickness, and every vertex gets
#   'arc'  = distance (m) along the nerve/artery tree from the hip (so signal pulses and blood can run down the whole tree in one go)
# Each object keeps o['kind'] (bone / muscle / tendon / nerve / artery) and o['src'] (atlas name).
#   python3 anat_build.py /root/anat/Z-Anatomy/Startup.blend OUT.blend
import bpy, sys, math
from mathutils import Vector, geometry, kdtree
src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
OB = bpy.data.objects
FOOT_BONES = ['Talus', 'Calcaneus', 'Navicular bone', 'Cuboid bone', 'Medial cuneiform bone', 'Intermediate cuneiform bone', 'Lateral cuneiform bone'] + \
    [f'{n} metatarsal bone' for n in ('First', 'Second', 'Third', 'Fourth', 'Fifth')] + \
    [f'{p} phalanx of {n} finger of foot' for n in ('first', 'second', 'third', 'fourth', 'fifth') for p in ('Proximal', 'Middle', 'Distal')]
BONES = ['Femur', 'Patella', 'Tibia', 'Fibula', 'Hip bone'] + FOOT_BONES
MUSCLES = ['Tibialis anterior muscle', 'Extensor digitorum longus', 'Extensor hallucis longus', 'Fibularis longus muscle', 'Fibularis brevis muscle',
           'Fibularis tertius muscle', 'Lateral head of gastrocnemius', 'Medial head of gastrocnemius', 'Soleus muscle', 'Long head of biceps femoris',
           'Short head of biceps femoris', 'Vastus lateralis muscle', 'Tibialis posterior muscle']
TENDONS = ['Tendon of extensor digitorum longus', 'Calcaneal tendon', 'Tendon sheath of tibialis anterior']
# nerves / arteries: (atlas name, tube radius m)  -- real sizes: sciatic ~1 cm wide, tibial ~5 mm, common fibular ~4 mm; femoral artery ~8 mm
NERVES = [('Sciatic nerve', 0.0048), ('Tibial nerve', 0.0028), ('Common fibular nerve', 0.0022), ('Deep fibular nerve', 0.0012), ('Superficial fibular nerve', 0.0012),
          ('Muscular branches of deep fibular nerve', 0.0007), ('Dorsal digital branches of deep fibular nerve', 0.0006),
          ('Dorsal digital branches of superficial fibular nerve', 0.0006), ('Medial dorsal cutaneous nerve of foot', 0.0007),
          ('Intermediate dorsal cutaneous nerve of foot', 0.0007), ('Sural nerve', 0.0011), ('Medial sural cutaneous nerve', 0.0008),
          ('Sural communicating branch of common fibular nerve', 0.0007), ('Medial plantar nerve', 0.0012), ('Lateral plantar nerve', 0.0011),
          ('Saphenous nerve', 0.0009), ('Lateral sural cutaneous nerve', 0.0008)]
ARTERIES = [('Femoral artery', 0.0040), ('Deep femoral artery', 0.0028), ('Popliteal artery', 0.0032), ('Anterior tibial artery', 0.0017),
            ('Posterior tibial artery', 0.0017), ('Fibular artery', 0.0012), ('Dorsalis pedis artery', 0.0014), ('Arcuate artery', 0.0008), ('Lateral tarsal artery', 0.0007), ('Anterior tibial recurrent artery', 0.0007), ('Dorsal metatarsal arteries', 0.0006),
            ('Dorsal digital arteries of foot', 0.0005), ('Deep plantar artery', 0.0008), ('Medial plantar artery', 0.0008), ('Lateral plantar artery', 0.0010),
            ('Superior lateral genicular artery', 0.0008), ('Inferior lateral genicular artery', 0.0008), ('Superior medial genicular artery', 0.0008),
            ('Inferior medial genicular artery', 0.0008), ('Middle genicular artery', 0.0006)]
dg = bpy.context.evaluated_depsgraph_get()
made = []
def new_obj(name, me, kind, srcname):
    o = bpy.data.objects.new(name, me); o['kind'] = kind; o['src'] = srcname; made.append(o); return o
def copy_mesh(o):
    oe = o.evaluated_get(dg); m = oe.to_mesh(); M = oe.matrix_world
    me = bpy.data.meshes.new('a_' + o.name)
    me.from_pydata([M @ v.co for v in m.vertices], [], [tuple(p.vertices) for p in m.polygons]); oe.to_mesh_clear()
    for p in me.polygons: p.use_smooth = True
    return me
for nm in BONES + MUSCLES + TENDONS:
    o = OB.get(nm + '.r')
    if not o or o.type != 'MESH': print('missing', nm); continue
    kind = 'bone' if nm in BONES else 'muscle' if nm in MUSCLES else 'tendon'
    new_obj(nm, copy_mesh(o), kind, o.name)
# ---- curves: polylines (world), arc length along the whole tree
def polylines(o):
    M = o.matrix_world; res = []
    for sp in o.data.splines:
        pts = []
        if sp.type == 'BEZIER':
            bp = sp.bezier_points; n = len(bp)
            segs = list(zip(range(n - 1), range(1, n))) + ([(n - 1, 0)] if sp.use_cyclic_u else [])
            for i, j in segs:
                seg = geometry.interpolate_bezier(bp[i].co, bp[i].handle_right, bp[j].handle_left, bp[j].co, 24)
                pts += [M @ p for p in (seg if not pts else seg[1:])]
        else:
            pts = [M @ Vector(p.co[:3]) for p in sp.points]
        if len(pts) > 1: res.append(pts)
    return res
TREE = {}           # name -> list of (pts, s0) with pts oriented proximal -> distal
def orient_and_offset(name, o):
    pls = polylines(o)
    par = o.parent if o.parent and o.parent.name.rstrip('.r').rstrip('.') else None
    pname = o.parent.name[:-2] if (o.parent and o.parent.name.endswith('.r')) else None
    out_ = []
    for pts in pls:
        s0 = 0.0
        if pname in TREE:                       # start at the end nearest the parent; offset = parent's arc at that point
            best = None
            for ppts, ps0 in TREE[pname]:
                acc = ps0
                for k in range(len(ppts)):
                    if k: acc += (ppts[k] - ppts[k - 1]).length
                    for end in (0, -1):
                        d = (ppts[k] - pts[end]).length
                        if best is None or d < best[0]: best = (d, end, acc)
            if best[1] == -1: pts = pts[::-1]
            s0 = best[2]
        elif pts[0].z < pts[-1].z: pts = pts[::-1]          # roots run from the hip down
        out_.append((pts, s0))
    TREE[name] = out_
def tube_from_curve(name, r, kind):
    o = OB.get(name + '.r')
    if not o or o.type != 'CURVE': print('missing', name); return
    orient_and_offset(name, o)
    c = o.data; c.bevel_mode = 'ROUND'; c.bevel_depth = r; c.bevel_resolution = 3; c.resolution_u = 10; c.use_fill_caps = True; c.taper_object = None
    c.bevel_object = None; c.extrude = 0.0
    bpy.context.view_layer.update(); d2 = bpy.context.evaluated_depsgraph_get()
    me = copy_mesh(o)
    # arc per vertex: nearest sample on this curve's polylines
    samp = []
    for pts, s0 in TREE[name]:
        acc = s0
        for k in range(len(pts)):
            if k: acc += (pts[k] - pts[k - 1]).length
            samp.append((pts[k], acc))
    kd = kdtree.KDTree(len(samp))
    for i, (p, s) in enumerate(samp): kd.insert(p, i)
    kd.balance()
    at = me.attributes.new('arc', 'FLOAT', 'POINT')
    for v in me.vertices: at.data[v.index].value = samp[kd.find(v.co)[1]][1]
    nob = new_obj(name, me, kind, o.name); nob['arc_max'] = max(s for _, s in samp)
# parents before children: order by depth in the atlas hierarchy
def depth(o):
    d = 0
    while o.parent: d += 1; o = o.parent
    return d
for lst, kind in ((NERVES, 'nerve'), (ARTERIES, 'artery')):
    for nm, r in sorted(lst, key=lambda x: depth(OB[x[0] + '.r']) if (x[0] + '.r') in OB else 0):
        tube_from_curve(nm, r, kind)
for o in made: print(o['kind'], o.name, len(o.data.vertices), round(o.get('arc_max', 0), 3))
bpy.data.libraries.write(out, set(made), fake_user=True)
print('wrote', out, len(made))
