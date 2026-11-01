# Turn the MakeHuman man (human.blend from mh_build.py) into a character for the web Shorts, in the same format as
# web/char/guy.json + guy.bin, so the loader (guy3d.js), the arm/hand solver and every scene keep working:
#   - his arms, hands, fingers and legs are re-posed to the old guy's rest pose (same bone directions, same palm frames),
#     and he is scaled so his hips sit at the same height (0.95 m);
#   - our 48-bone skeleton is placed on his joints, and his MakeHuman skin weights are folded onto our bones
#     (face bones onto the head, the lower face and tongue onto the jaw, his eyeballs onto two new eye bones);
#   - MakeHuman's expression units (blinks, brows, smile, frown, ...) become morph targets on the face, brows and lashes;
#   - every part keeps its UVs and textures (char/<name>/*.png|jpg); the json says which texture each part uses.
#   python3 mh_export.py human.blend ../../web/char mh
import sys, os, json, math, struct
import bpy, addon_utils, numpy as np
from mathutils import Vector, Matrix, Quaternion
addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
from bl_ext.user_default.mpfb.services.targetservice import TargetService
from bl_ext.user_default.mpfb.services.faceservice import FaceService

BLEND, OUTDIR, NAME = sys.argv[-3:]
HERE = os.path.dirname(os.path.abspath(__file__))
GUY = json.load(open(os.path.join(HERE, '../../web/char/guy.json')))
D = '/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data'
UNITS = '/root/.config/blender/5.2/extensions/user_default/mpfb/data/targets/expression/units/caucasian'

bpy.ops.wm.open_mainfile(filepath=BLEND)
S_ = bpy.context.scene
rig = bpy.data.objects['Human.rig']; body = bpy.data.objects['Human']
B2T = lambda v: Vector((-v[0], v[2], v[1]))        # Blender (z up, faces -y) -> three.js (y up, faces -z); a rotation, not a mirror
T2B = lambda v: Vector((-v[0], v[2], v[1]))
OB = {b['name']: b for b in GUY['bones']}
oh = lambda n: Vector(OB[n]['head']); ot = lambda n: Vector(OB[n]['tail'])

# ---------------------------------------------------------------- 1. expression units as shape keys (face, then brows/lashes)
UNIT_NAMES = ['eye-left-closure', 'eye-right-closure', 'eye-left-slit', 'eye-right-slit', 'eye-left-opened-up', 'eye-right-opened-up',
              'eyebrows-left-up', 'eyebrows-right-up', 'eyebrows-left-down', 'eyebrows-right-down', 'eyebrows-left-inner-up', 'eyebrows-right-inner-up',
              'mouth-corner-puller', 'mouth-depression', 'mouth-compression', 'mouth-pursing', 'mouth-protusion', 'mouth-upward-retraction',
              'mouth-retraction', 'nose-left-elevation', 'nose-right-elevation', 'mouth-open']
for u in UNIT_NAMES:
    TargetService.load_target(body, f'{UNITS}/{u}.target.gz', weight=0.0, name='u_' + u)
FaceService.interpolate_targets(body)

# ---------------------------------------------------------------- 2. re-pose arms, hands, fingers, legs to the old guy's rest pose
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='POSE')
def upd(): bpy.context.view_layer.update()
def J(n, end='head'): pb = rig.pose.bones[n]; return rig.matrix_world @ (pb.head if end == 'head' else pb.tail)
def rot_about(n, R, pivot):
    pb = rig.pose.bones[n]; Mw = rig.matrix_world @ pb.matrix; T = Matrix.Translation(pivot)
    pb.matrix = rig.matrix_world.inverted() @ (T @ R.to_matrix().to_4x4() @ T.inverted() @ Mw); upd()
def align(n, a, b, tdir):          # rotate bone n so the MH joint line a->b points along tdir (three.js direction)
    cur = (J(*b) - J(*a)).normalized(); rot_about(n, cur.rotation_difference(T2B(tdir).normalized()), J(n))
for S, s in (('L', 'L'), ('R', 'R')):
    align(f'clavicle.{s}', (f'clavicle.{s}',), (f'upperarm01.{s}',), oh('uarm' + S) - oh('clav' + S))
    align(f'upperarm01.{s}', (f'upperarm01.{s}',), (f'lowerarm01.{s}',), oh('farm' + S) - oh('uarm' + S))
    align(f'lowerarm01.{s}', (f'lowerarm01.{s}',), (f'wrist.{s}',), oh('hand' + S) - oh('farm' + S))
    hu = Vector(GUY['hands'][S]['u']); hn = Vector(GUY['hands'][S]['n'])
    align(f'wrist.{s}', (f'wrist.{s}',), (f'finger3-1.{s}',), hu)
    # palm roll: MakeHuman's palm normal from the knuckle line, turned about the finger direction onto ours
    u = B2T((J(f'finger3-1.{s}') - J(f'wrist.{s}')).normalized()); across = B2T(J(f'finger2-1.{s}') - J(f'finger5-1.{s}'))
    n_mh = u.cross(across).normalized() * (-1 if S == 'R' else 1)
    p = (n_mh - u * n_mh.dot(u)).normalized(); q = (hn - u * hn.dot(u)).normalized()
    ang = math.atan2(u.dot(p.cross(q)), p.dot(q)); rot_about(f'wrist.{s}', Quaternion(T2B(u), ang), J(f'wrist.{s}'))
    for f, mh in (('index', 2), ('middle', 3), ('ring', 4), ('pinky', 5), ('thumb', 1)):
        b1, b2, b3 = f'finger{mh}-1.{s}', f'finger{mh}-2.{s}', f'finger{mh}-3.{s}'
        align(b1, (b1,), (b2,), ot(f + '1' + S) - oh(f + '1' + S))
        align(b2, (b2,), (b3,), ot(f + '2' + S) - oh(f + '2' + S))
        align(b3, (b3,), (b3, 'tail'), ot(f + '2' + S) - oh(f + '2' + S))
    align(f'upperleg01.{s}', (f'upperleg01.{s}',), (f'lowerleg01.{s}',), oh('shin' + S) - oh('thigh' + S))
    align(f'lowerleg01.{s}', (f'lowerleg01.{s}',), (f'foot.{s}',), oh('foot' + S) - oh('shin' + S))
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- 3. scale: hips at 0.95 m like the old guy
hipY = (B2T(J('upperleg01.L')).y + B2T(J('upperleg01.R')).y) / 2
SC = 0.95 / hipY
P = lambda v: B2T(v) * SC                           # Blender world point -> three.js metres
print('scale', round(SC, 4), 'hip', round(hipY, 4))

# ---------------------------------------------------------------- 4. our skeleton on his joints
def jt(n, end='head'): return P(J(n, end))
mid = lambda a, b: (a + b) / 2
hipC = mid(jt('upperleg01.L'), jt('upperleg01.R')); hipC.x = 0
eyeC = {'R': jt('eye.R'), 'L': jt('eye.L')}
heads = {'hips': hipC, 'spine1': jt('spine03'), 'spine2': jt('spine02'), 'chest': jt('spine01'), 'neck': jt('neck01'), 'head': jt('head'), 'jaw': jt('jaw')}   # chest = upper chest, like the old guy
tails = {'hips': jt('spine03'), 'spine1': jt('spine02'), 'spine2': jt('spine01'), 'chest': jt('neck01'), 'neck': jt('head'), 'head': jt('head', 'tail'), 'jaw': jt('jaw', 'tail')}
for S in 'RL':
    s = S
    heads['brow' + S] = eyeC[S] + Vector((0, 0.022, -0.012)); tails['brow' + S] = heads['brow' + S] + Vector((0, 0, -0.02))
    heads['eye' + S] = eyeC[S]; tails['eye' + S] = eyeC[S] + Vector((0, 0, -0.02))
    heads['clav' + S] = jt(f'clavicle.{s}'); tails['clav' + S] = jt(f'upperarm01.{s}')
    for n in ('uarm', 'uarmTwist'): heads[n + S] = jt(f'upperarm01.{s}'); tails[n + S] = jt(f'lowerarm01.{s}')
    for n in ('farm', 'farmTwist'): heads[n + S] = jt(f'lowerarm01.{s}'); tails[n + S] = jt(f'wrist.{s}')
    heads['hand' + S] = jt(f'wrist.{s}'); tails['hand' + S] = jt(f'finger3-1.{s}')
    for f, mh in (('index', 2), ('middle', 3), ('ring', 4), ('pinky', 5), ('thumb', 1)):
        heads[f + '1' + S] = jt(f'finger{mh}-1.{s}'); tails[f + '1' + S] = jt(f'finger{mh}-2.{s}')
        heads[f + '2' + S] = jt(f'finger{mh}-2.{s}'); tails[f + '2' + S] = jt(f'finger{mh}-3.{s}', 'tail')
    heads['thigh' + S] = jt(f'upperleg01.{s}'); tails['thigh' + S] = jt(f'lowerleg01.{s}')
    heads['shin' + S] = jt(f'lowerleg01.{s}'); tails['shin' + S] = jt(f'foot.{s}')
    heads['foot' + S] = jt(f'foot.{s}'); tails['foot' + S] = mid(jt(f'toe2-1.{s}'), jt(f'toe3-1.{s}'))
bones = [dict(b) for b in GUY['bones']] + [{'name': 'eyeR', 'parent': 'head'}, {'name': 'eyeL', 'parent': 'head'}]
for b in bones: b['head'] = [round(x, 5) for x in heads[b['name']]]; b['tail'] = [round(x, 5) for x in tails[b['name']]]
BI = {b['name']: i for i, b in enumerate(bones)}

# MakeHuman bone -> our bone (anything not listed climbs to its parent until it hits one that is)
MAPW = {'root': 'hips', 'pelvis': 'hips', 'spine05': 'hips', 'spine04': 'hips', 'spine03': 'spine1', 'spine02': 'spine2', 'spine01': 'chest', 'breast': 'chest',
        'neck01': 'neck', 'neck02': 'neck', 'neck03': 'neck', 'head': 'head', 'jaw': 'jaw', 'eye': 'eye',
        'clavicle': 'clav', 'shoulder01': 'clav', 'upperarm01': 'uarm', 'upperarm02': 'uarmTwist', 'lowerarm01': 'farm', 'lowerarm02': 'farmTwist',
        'wrist': 'hand', 'metacarpal1': 'hand', 'metacarpal2': 'hand', 'metacarpal3': 'hand', 'metacarpal4': 'hand',
        'finger1-1': 'thumb1', 'finger1-2': 'thumb2', 'finger1-3': 'thumb2', 'finger2-1': 'index1', 'finger2-2': 'index2', 'finger2-3': 'index2',
        'finger3-1': 'middle1', 'finger3-2': 'middle2', 'finger3-3': 'middle2', 'finger4-1': 'ring1', 'finger4-2': 'ring2', 'finger4-3': 'ring2',
        'finger5-1': 'pinky1', 'finger5-2': 'pinky2', 'finger5-3': 'pinky2', 'upperleg01': 'thigh', 'upperleg02': 'thigh', 'lowerleg01': 'shin', 'lowerleg02': 'shin', 'foot': 'foot'}
MID = ('hips', 'spine1', 'spine2', 'chest', 'neck', 'head', 'jaw')
def ours(mhname):
    b = rig.data.bones.get(mhname)
    while b is not None:
        base, _, side = b.name.partition('.')
        if base in MAPW: t = MAPW[base]; return t if t in MID else t + side
        b = b.parent
    return 'head'

# ---------------------------------------------------------------- 5. meshes: rest positions after the re-pose, masks, UV seams split, weights, morphs
dg = bpy.context.evaluated_depsgraph_get()
REF = {}
def mesh_data(o, morph_combo=None):
    mods = {m.name: m.show_viewport for m in o.modifiers}
    for m in o.modifiers:
        if m.type == 'MASK': m.show_viewport = False
        if m.type == 'ARMATURE': m.show_viewport = True      # MPFB's target interpolation leaves the body's armature switched off
    keys = o.data.shape_keys.key_blocks if o.data.shape_keys else []
    for k in keys:
        if k.name.startswith('u_'): k.value = 0.0          # expression units off; the body-shape (macro) keys stay as they are
    upd(); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.array([o.matrix_world @ v.co for v in me.vertices]); nrm = np.array([(o.matrix_world.to_3x3() @ v.normal).normalized() for v in me.vertices])
    keep = np.ones(len(o.data.vertices), bool)
    for m in o.modifiers:
        if m.type == 'MASK' and m.vertex_group in o.vertex_groups:      # every mask counts (MPFB's target interpolation leaves them switched off)
            gi = o.vertex_groups[m.vertex_group].index; ing = np.zeros(len(o.data.vertices), bool)
            for v in o.data.vertices:
                for g in v.groups:
                    if g.group == gi and g.weight > 0.5: ing[v.index] = True
            keep &= ~ing if m.invert_vertex_group else ing
    # morph deltas (in rest space; the face didn't move in the re-pose)
    basis = np.array([k.co for k in o.data.shape_keys.reference_key.data]) if keys else None
    deltas = {}
    if morph_combo and not keys and 'body' in REF:    # brows and lashes: carry the face's movement from the nearest skin points
        from mathutils.kdtree import KDTree
        bco, bdel = REF['body']
        if not hasattr(mesh_data, 'kd'):
            kd = KDTree(len(bco))
            for i, c in enumerate(bco): kd.insert(c, i)
            kd.balance(); mesh_data.kd = kd
        near = [mesh_data.kd.find_n(Vector(c), 4) for c in co]
        for name, dl in bdel.items():
            out = np.zeros((len(co), 3))
            for vi, hits in enumerate(near):
                ws = np.array([1 / (d + 1e-4) for _, _, d in hits]); out[vi] = (np.array([dl[i] for _, i, _ in hits]) * ws[:, None]).sum(0) / ws.sum()
            deltas[name] = out
    if keys and morph_combo:
        units = {k.name[2:]: np.array([d.co for d in k.data]) - basis for k in keys if k.name.startswith('u_')}
        for name, combo in morph_combo.items():
            dl = sum((units[u] * w for u, w in combo if u in units), np.zeros_like(basis))
            if np.abs(dl).max() > 1e-6: deltas[name] = dl
        if o == body:
            REF['body'] = (co, {k: v for k, v in deltas.items()})
    loops_uv = None
    if me.uv_layers: loops_uv = np.zeros((len(me.loops), 2)); me.uv_layers.active.data.foreach_get('uv', loops_uv.ravel())
    polys = [(list(p.vertices), list(p.loop_indices)) for p in me.polygons]
    groups = [[(o.vertex_groups[g.group].name, g.weight) for g in v.groups] for v in o.data.vertices]
    ev.to_mesh_clear()
    for m in o.modifiers: m.show_viewport = mods[m.name]
    return co, nrm, keep, polys, loops_uv, groups, deltas

def build(parts, face_filter=None):     # parts: list of (object, morph_combo) -> one mesh in our format
    P3, N3, UV, SI, SW, IDX, MOR = [], [], [], [], [], [], {}
    for o, combo in parts:
        co, nrm, keep, polys, luv, groups, deltas = mesh_data(o, combo)
        vmap = {}
        for verts, loops in polys:
            if not all(keep[v] for v in verts): continue
            if face_filter and not face_filter(o, verts, [luv[l] for l in loops] if luv is not None else None, co): continue
            ids = []
            for v, l in zip(verts, loops):
                key = (v, tuple(np.round(luv[l], 5))) if luv is not None else (v,)
                if key not in vmap:
                    vmap[key] = len(P3); P3.append(P(Vector(co[v]))); N3.append(B2T(Vector(nrm[v])).normalized())
                    UV.append((luv[l][0], luv[l][1]) if luv is not None else (0, 0))   # GL convention, like Blender: three's default flipY matches
                    w = {}
                    for gname, gw in groups[v]:
                        if rig.data.bones.get(gname) is None or gw <= 0: continue
                        t = ours(gname); w[t] = w.get(t, 0) + gw
                    top = sorted(w.items(), key=lambda x: -x[1])[:4]; tot = sum(x[1] for x in top) or 1
                    si = [BI[t] for t, _ in top] + [0] * (4 - len(top)); sw = [x / tot for _, x in top] + [0] * (4 - len(top))
                    SI.append(si); SW.append(sw)
                    for nm, dl in deltas.items(): MOR.setdefault(nm, {})[vmap[key]] = B2T(Vector(dl[v])) * SC
                ids.append(vmap[key])
            for k in range(1, len(ids) - 1): IDX.append((ids[0], ids[k], ids[k + 1]))
    n = len(P3)
    mor = {nm: np.array([d.get(i, Vector()) for i in range(n)], np.float32) for nm, d in MOR.items()}
    return {'pos': np.array(P3, np.float32), 'nrm': np.array(N3, np.float32), 'uv': np.array(UV, np.float32), 'si': np.array(SI, np.uint16),
            'sw': np.array(SW, np.float32), 'idx': np.array(IDX, np.uint32), 'morphs': mor}

U = lambda *names: [(n, 1.0) for n in names]
FACE = {'blinkR': U('eye-right-closure'), 'blinkL': U('eye-left-closure'), 'squintR': U('eye-right-slit'), 'squintL': U('eye-left-slit'),
        'wideR': U('eye-right-opened-up'), 'wideL': U('eye-left-opened-up'), 'browUpR': U('eyebrows-right-up'), 'browUpL': U('eyebrows-left-up'),
        'browDownR': U('eyebrows-right-down'), 'browDownL': U('eyebrows-left-down'), 'browInR': U('eyebrows-right-inner-up'), 'browInL': U('eyebrows-left-inner-up'),
        'smile': U('mouth-corner-puller'), 'frown': U('mouth-depression'), 'press': U('mouth-compression'), 'oh': U('mouth-pursing'),
        'puff': U('mouth-protusion'), 'grimace': U('mouth-upward-retraction'), 'retract': U('mouth-retraction'),
        'sneer': U('nose-left-elevation', 'nose-right-elevation'), 'open': U('mouth-open')}
obj = lambda suffix: bpy.data.objects['Human' + suffix]
texdir = os.path.join(OUTDIR, NAME); os.makedirs(texdir, exist_ok=True)
from PIL import Image
def tex(src, dst, size=2048, alpha=False, tint=None):
    im = Image.open(src).convert('RGBA' if alpha else 'RGB')
    if max(im.size) > size: im = im.resize((size, size), Image.LANCZOS)
    if tint:
        a = np.asarray(im).astype(np.float32); a[..., :3] *= np.array(tint)[None, None]; im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    p = os.path.join(texdir, dst); im.save(p, quality=90) if dst.endswith('.jpg') else im.save(p); return f'{NAME}/{dst}'
T = {'skin': tex(f'{D}/skins/textures/young_lightskinned_male_diffuse_tan.png', 'skin.jpg'),
     'cloth': tex(f'{D}/clothes/male_casualsuit06/male_casualsuit06_diffuse.png', 'cloth.jpg'),
     'clothN': tex(f'{D}/clothes/male_casualsuit06/male_casualsuit06_normal.png', 'cloth_n.jpg', 1024),
     'shoe': tex(f'{D}/clothes/shoes05/shoes05_diffuse.png', 'shoe.jpg', 1024),
     'hair': tex(f'{D}/hair/short02/short02_diffuse.png', 'hair.png', 1024, True, (0.42, 0.30, 0.22)),
     'hairN': tex(f'{D}/hair/short02/short02_normal.png', 'hair_n.jpg', 1024),
     'brow': tex(f'{D}/eyebrows/eyebrow001/eyebrow001.png', 'brow.png', 512, True, (0.55, 0.42, 0.32)),
     'lash': tex(f'{D}/eyelashes/eyelashes01/eyelashes01.png', 'lash.png', 512, True),
     'eye': tex(f'{D}/eyes/materials/brown_eye.png', 'eye.png', 1024, True),   # its alpha is the clear cornea over the iris
     'teeth': tex(f'{D}/teeth/materials/teeth.png', 'teeth.jpg', 512), 'tongue': tex(f'{D}/tongue/tongue01/tongue01_diffuse.png', 'tongue.jpg', 512)}
# part, objects, texture spec, face filter
xs = lambda co, verts: np.mean([P(Vector(co[v])).x for v in verts])
PARTS = [
    ('skin_head', [(body, FACE)], {'map': T['skin'], 'kind': 'skin'}, None),
    ('shirt', [(obj('.male_casualsuit06'), None)], {'map': T['cloth'], 'normalMap': T['clothN'], 'kind': 'cloth', 'roughness': 0.85, 'sheen': 0.5}, lambda o, v, uv, co: np.mean([u[1] for u in uv]) > 0.57),
    ('jeans', [(obj('.male_casualsuit06'), None)], {'map': T['cloth'], 'normalMap': T['clothN'], 'kind': 'cloth', 'roughness': 0.9}, lambda o, v, uv, co: np.mean([u[1] for u in uv]) <= 0.57),
    ('shoeR', [(obj('.shoes05'), None)], {'map': T['shoe'], 'kind': 'cloth', 'roughness': 0.6}, lambda o, v, uv, co: xs(co, v) > 0),
    ('shoeL', [(obj('.shoes05'), None)], {'map': T['shoe'], 'kind': 'cloth', 'roughness': 0.6}, lambda o, v, uv, co: xs(co, v) <= 0),
    ('hair', [(obj('.short02'), None)], {'map': T['hair'], 'normalMap': T['hairN'], 'kind': 'hair', 'alphaTest': 0.45, 'roughness': 0.5}, None),
    ('brows', [(obj('.eyebrow001'), FACE)], {'map': T['brow'], 'kind': 'alpha', 'alphaTest': 0.25, 'roughness': 0.8}, None),
    ('lashes', [(obj('.eyelashes01'), FACE)], {'map': T['lash'], 'kind': 'alpha', 'alphaTest': 0.3, 'roughness': 0.8}, None),
    ('eyeR', [(obj('.high-poly'), None)], {'map': T['eye'], 'kind': 'eye', 'roughness': 0.08, 'alphaTest': 0.5}, lambda o, v, uv, co: xs(co, v) > 0),
    ('eyeL', [(obj('.high-poly'), None)], {'map': T['eye'], 'kind': 'eye', 'roughness': 0.08, 'alphaTest': 0.5}, lambda o, v, uv, co: xs(co, v) <= 0),
    ('teeth', [(obj('.teeth_base'), None)], {'map': T['teeth'], 'kind': 'plain', 'roughness': 0.35}, None),
    ('tongue', [(obj('.tongue01'), None)], {'map': T['tongue'], 'kind': 'plain', 'roughness': 0.45}, None)]
blob = bytearray(); meshes = []
def put(a): off = len(blob); blob.extend(a.tobytes()); blob.extend(b'\0' * ((-len(blob)) % 4)); return off
for name, objs, spec, flt in PARTS:
    m = build(objs, flt)
    nv, nf = len(m['pos']), len(m['idx'])
    if nv == 0: print('EMPTY', name); continue
    if name in ('eyeR', 'eyeL'): m['si'][:] = 0; m['si'][:, 0] = BI[name]; m['sw'][:] = 0; m['sw'][:, 0] = 1     # eyeballs ride their eye bones only
    ent = {'name': name, 'nv': nv, 'nf': nf, 'pos': put(m['pos']), 'idx': put(m['idx']), 'si': put(m['si']), 'sw': put(m['sw']), 'nrm': put(m['nrm']), 'uv': put(m['uv']),
           'ao': put(np.full(nv, 255, np.uint8)), 'mat': spec, 'morphs': []}
    for mn, arr in m['morphs'].items():
        if np.abs(arr).max() < 1e-5: continue
        ent['morphs'].append({'name': mn, 'p': put(arr), 'n': put(np.zeros_like(arr))})
    meshes.append(ent); print(name, nv, 'verts', nf, 'tris', len(ent['morphs']), 'morphs')

# ---------------------------------------------------------------- 6. the facts the scenes read
lips = [P(J('oris01')), P(J('oris05'))]
man = {k: GUY[k] for k in ('hands', 'nails') if k in GUY}
man.update({'bones': bones, 'meshes': meshes, 'eyes': {S: [round(x, 5) for x in eyeC[S]] for S in 'RL'}, 'eyeR': 0.0125,
            'mouthY': round(float(np.mean([p.y for p in lips])), 5), 'mouthZ': round(float(min(p.z for p in lips)), 5),
            'headC': [0.0, round(float(eyeC['R'].y), 5), round(float((eyeC['R'].z + heads['head'].z) / 2 + 0.03), 5)],
            'textured': True, 'ownFace': True, 'faceMorphs': list(FACE.keys())})
open(os.path.join(OUTDIR, NAME + '.bin'), 'wb').write(bytes(blob))
json.dump(man, open(os.path.join(OUTDIR, NAME + '.json'), 'w'), separators=(',', ':'))
print('wrote', NAME, len(blob) // 1024, 'KB', 'hips', [round(x, 3) for x in heads['hips']], 'eyes', man['eyes'], 'mouth', man['mouthY'], man['mouthZ'])
