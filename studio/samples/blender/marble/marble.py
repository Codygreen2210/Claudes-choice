# Glowing marble race: 8 marbles down one big detailed track (jumps, zigzags, vortex funnels, a glass corkscrew, a plinko board,
# a tower helix, rollers). Real Bullet physics, baked once (--sim) into sim.npz; the render reads it. ONE continuous camera move.
#   python3 marble.py OUTDIR F0 F1 [--samples 32] [--scale 1.0] [--only f,f]   |   python3 marble.py X 0 0 --sim SECONDS
import sys, os, math, json, argparse, random
import numpy as np
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, Quaternion, noise as mnoise
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
ap.add_argument('--blend', default=''); ap.add_argument('--sim', type=float, default=0.0); ap.add_argument('--simfrom', type=int, default=0); ap.add_argument('--seed', type=int, default=7)
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(n): return next(p_ for p_ in (os.path.join(HERE, n), os.path.join(HERE, 'assets', n), os.path.join('/root/vt/n45/boat', n), os.path.join('/root/vt/assets', n)) if os.path.exists(p_))
FPS = 30
STRIDE = json.load(open(os.path.join(HERE, 'stride.json'))) if os.path.exists(os.path.join(HERE, 'stride.json')) else None
REDO = json.load(open(os.path.join(HERE, 'redo.json'))) if os.path.exists(os.path.join(HERE, 'redo.json')) else None
clamp = lambda x, lo, hi: max(lo, min(hi, x))
sm = lambda x: x * x * (3 - 2 * x)
def smooth(e0, e1, x): return sm(clamp((x - e0) / (e1 - e0), 0, 1))
lerp = lambda p, q, k: p + (q - p) * k
def h1(n): return (math.sin(n * 127.1 + 311.7) * 43758.5453) % 1.0
def wob(t, f, seed=0.0): return mnoise.noise(Vector((t * f, seed, seed * 1.7)))
R = math.radians
V3 = lambda *p: Vector(p)

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('cycles', default_set=False)
S = bpy.context.scene; S.render.engine = 'CYCLES'; S.render.fps = FPS
S.render.resolution_x = int(1920 * a.scale); S.render.resolution_y = int(1080 * a.scale); S.render.resolution_percentage = 100
C = S.cycles; C.device = 'CPU'; C.samples = a.samples; C.use_denoising = os.environ.get('NODN') is None; C.denoiser = 'OPENIMAGEDENOISE'
C.max_bounces = 8; C.diffuse_bounces = 2; C.glossy_bounces = 2; C.transmission_bounces = 7; C.volume_bounces = 0; C.transparent_max_bounces = 24
C.use_adaptive_sampling = True; C.adaptive_threshold = 0.05; C.adaptive_min_samples = 8
C.caustics_reflective = False; C.caustics_refractive = False; C.sample_clamp_indirect = 6.0
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'; S.view_settings.exposure = 0.0

# ---------------------------------------------------------------- materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, estr=0.0, alpha=1.0, sheen=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior; b.inputs['Coat Weight'].default_value = coat; b.inputs['Alpha'].default_value = alpha
    b.inputs['Sheen Weight'].default_value = sheen
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    return m
def N(m): return m.node_tree.nodes
def L(m, a_, b_): m.node_tree.links.new(a_, b_)
def noisy(m, scale=40.0, amt=0.15, rough_amt=0.1, coord='Object'):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6; nt.links.new(tc.outputs[coord], nz.inputs['Vector'])
    base = b.inputs['Base Color'].default_value[:]; mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs['A'].default_value = base; mx.inputs['B'].default_value = tuple(c * (1 - amt) for c in base[:3]) + (1,)
    nt.links.new(nz.outputs['Fac'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    r0 = b.inputs['Roughness'].default_value; mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = max(0, r0 - rough_amt); mr.inputs['To Max'].default_value = r0 + rough_amt
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness']); return m
def emis(name, col, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = strength
    nt.links.new(e_.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m
def objattr(nt, name):
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = name; return at.outputs['Fac']
def math_(nt, op, a_, b_=None, c_=None):
    m_ = nt.nodes.new('ShaderNodeMath'); m_.operation = op
    for i, v in enumerate((a_, b_, c_)):
        if v is None: continue
        if isinstance(v, (int, float)): m_.inputs[i].default_value = v
        else: nt.links.new(v, m_.inputs[i])
    return m_.outputs['Value']

# ---------------------------------------------------------------- geometry helpers
def obj(name, me, m=None, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.location = loc
    if m: o.data.materials.append(m)
    if parent: o.parent = parent
    return o
def mesh(name, vs, fs, m=None, parent=None, smooth_=True, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.validate(); me.update()
    if smooth_:
        for p in me.polygons: p.use_smooth = True
    return obj(name, me, m, loc, parent)
def empty(name, parent=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); S.collection.objects.link(o); o.location = loc
    if parent: o.parent = parent
    return o
def prim(kind, name, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), **kw):
    getattr(bpy.ops.mesh, 'primitive_' + kind + '_add')(location=(0, 0, 0), **kw); o = bpy.context.active_object; o.name = name
    o.scale = scale; bpy.ops.object.transform_apply(scale=True)
    o.location = loc; o.rotation_euler = rot
    if m: o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    if parent: o.parent = parent
    return o
def bevel(o, w, seg=3):
    md = o.modifiers.new('bv', 'BEVEL'); md.width = w; md.segments = seg; md.limit_method = 'ANGLE'; return o
def subsurf(o, lv=2):
    md = o.modifiers.new('ss', 'SUBSURF'); md.levels = lv; md.render_levels = lv; return o
def box(name, size, loc, m, bv=0.0, rot=(0, 0, 0), parent=None, ss=0):
    o = prim('cube', name, m, parent, loc=loc, rot=rot, size=1, scale=size)
    if bv: bevel(o, bv, 4)
    if ss: subsurf(o, ss)
    return o
def tube(name, pts, r, m, parent=None, seg=16, caps=True):
    pts = [Vector(p) for p in pts]; n = len(pts); rings = []; T0 = (pts[1] - pts[0]).normalized()
    up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized(); Bn = T0.cross(Nn)
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        rr = r(i / (n - 1)) if callable(r) else r
        rings.append([pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
    vs = [p for ring in rings for p in ring]; fs = []
    for i in range(n - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    if caps: fs.append(tuple(range(seg))[::-1]); fs.append(tuple((n - 1) * seg + k for k in range(seg)))
    return mesh(name, vs, fs, m, parent)
def lathe(name, prof, seg=48, m=None, parent=None, loc=(0, 0, 0)):
    """profile (r, z) turned about local z"""
    vs = [(r_ * math.cos(2 * math.pi * k / seg), r_ * math.sin(2 * math.pi * k / seg), z_) for r_, z_ in prof for k in range(seg)]; fs = []
    for i in range(len(prof) - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    return mesh(name, vs, fs, m, parent, loc=loc)

# ---------------------------------------------------------------- compositor: a soft bloom round bright things (the Sun, the vent, glows)
GLARE = None
try:
    ct_ = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); S.compositing_node_group = ct_
    rl_ = ct_.nodes.new('CompositorNodeRLayers'); GLARE = ct_.nodes.new('CompositorNodeGlare'); GLARE.inputs['Type'].default_value = 'Bloom'
    for k_, v_ in (('Threshold', 1.2), ('Strength', 0.35), ('Size', 0.6)):
        try: GLARE.inputs[k_].default_value = v_
        except Exception: pass
    out_ = ct_.nodes.new('NodeGroupOutput'); ct_.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ct_.links.new(rl_.outputs['Image'], GLARE.inputs['Image']); ct_.links.new(GLARE.outputs['Image'], out_.inputs[0]); print('glow on')
except Exception as e_: print('glow skipped', e_)
def bloom(strength=0.35, thresh=1.2):
    if GLARE is None: return
    try: GLARE.inputs['Strength'].default_value = strength; GLARE.inputs['Threshold'].default_value = thresh
    except Exception: pass

# ---------------------------------------------------------------- fast primitives (bmesh, no bpy.ops): this scene has thousands of parts
def prim(kind, name, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), **kw):
    bm = bmesh.new()
    if kind == 'cube': bmesh.ops.create_cube(bm, size=kw.get('size', 2.0))
    elif kind == 'uv_sphere': bmesh.ops.create_uvsphere(bm, u_segments=kw.get('segments', 32), v_segments=kw.get('ring_count', 16), radius=kw.get('radius', 1.0))
    elif kind == 'ico_sphere': bmesh.ops.create_icosphere(bm, subdivisions=kw.get('subdivisions', 2), radius=kw.get('radius', 1.0))
    elif kind == 'plane':
        h = kw.get('size', 2.0) / 2; vs_ = [bm.verts.new((x_ * h, y_ * h, 0)) for x_, y_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; bm.faces.new(vs_)
    else: raise ValueError(kind)
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    smooth_ = kind in ('uv_sphere', 'ico_sphere')
    for p in me.polygons: p.use_smooth = smooth_
    o = obj(name, me, m, loc, parent); o.rotation_euler = rot; return o

# ================================================================ helpers
def light_at(name, kind, loc, target, energy, col, size=0.3):
    lt = bpy.data.lights.new(name, kind); lt.energy = energy; lt.color = col
    if kind == 'AREA': lt.size = size
    else: lt.shadow_soft_size = size
    o = bpy.data.objects.new(name, lt); S.collection.objects.link(o); o.location = loc
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y'); return o
def mixc(nt, fac, a_, b_):
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    if isinstance(fac, (int, float)): mx.inputs['Factor'].default_value = fac
    else: nt.links.new(fac, mx.inputs['Factor'])
    for k, v in (('A', a_), ('B', b_)):
        if isinstance(v, tuple): mx.inputs[k].default_value = v if len(v) == 4 else (*v, 1)
        else: nt.links.new(v, mx.inputs[k])
    return mx.outputs['Result']
def ramp(nt, fac, stops, interp='LINEAR'):
    r_ = nt.nodes.new('ShaderNodeValToRGB'); el = r_.color_ramp.elements; r_.color_ramp.interpolation = interp
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1); el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for p_, c_ in stops[1:-1]: e_ = el.new(p_); e_.color = (*c_, 1)
    nt.links.new(fac, r_.inputs['Fac']); return r_.outputs['Color']
def coord(nt, kind='Object'):
    tc = nt.nodes.new('ShaderNodeTexCoord'); return tc.outputs[kind]
def sepz(nt, vec):
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(vec, sx.inputs[0]); return sx
def tnoise(nt, vec, scale, detail=6.0, dist=0.0):
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nz.inputs['Distortion'].default_value = dist; nt.links.new(vec, nz.inputs['Vector']); return nz.outputs['Fac']
def star_shader(nt, base, dens_scale=180.0, thresh=0.985, power=40.0):
    e_ = nt.nodes.new('ShaderNodeEmission'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = dens_scale
    nt.links.new(coord(nt, 'Generated'), vo.inputs['Vector']); vo2 = nt.nodes.new('ShaderNodeTexVoronoi'); vo2.inputs['Scale'].default_value = dens_scale * 0.37
    nt.links.new(coord(nt, 'Generated'), vo2.inputs['Vector'])
    s1 = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo.outputs['Distance'], 9.0)), 0.0), power)
    s2 = math_(nt, 'POWER', math_(nt, 'MAXIMUM', math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', vo2.outputs['Distance'], 7.0)), 0.0), power * 0.6)
    st = math_(nt, 'ADD', math_(nt, 'MULTIPLY', s1, 2.5), math_(nt, 'MULTIPLY', s2, 6.0))
    col = base if not isinstance(base, tuple) else None
    c_ = mixc(nt, math_(nt, 'MINIMUM', st, 1.0), base, (1.0, 0.97, 0.92))
    nt.links.new(c_, e_.inputs['Color']); e_.inputs['Strength'].default_value = 1.0
    nt.links.new(e_.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface'])

def emis_mix(name, col, strength, alpha_attr=None):
    """emission over transparent; object property alpha_attr (0..1) fades it"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    if alpha_attr: nt.links.new(objattr(nt, alpha_attr), mx.inputs['Fac'])
    else: mx.inputs['Fac'].default_value = 1.0
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e_.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.03; CAM.data.clip_end = 1e6
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5
def look(cp, ct, lens=35, fstop=8.0, focus=None, up=None, roll=0.0):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    if up is None: q = d.to_track_quat('-Z', 'Y')
    else:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0, f=7.0): return Vector((wob(t, f, seed), wob(t, f, seed + 3.3), wob(t, f, seed + 6.1))) * amt
def show(objs, on):
    for o in objs: o.hide_render = not on
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; WBG = W_.node_tree.nodes['Background']
WBG.inputs['Color'].default_value = (0, 0, 0, 1); WBG.inputs['Strength'].default_value = 0.0
# ================================================================ the course: a turtle lays the track piece by piece (same geometry for physics and render)
MR = 0.05                      # marble radius (m); the whole world is "big marble" scale, which reads better on camera
NM = 8
COLS = [('RED', (1.0, 0.06, 0.04)), ('ORANGE', (1.0, 0.36, 0.0)), ('YELLOW', (1.0, 0.85, 0.05)), ('GREEN', (0.1, 1.0, 0.15)),
        ('CYAN', (0.0, 0.9, 1.0)), ('BLUE', (0.08, 0.2, 1.0)), ('PURPLE', (0.6, 0.1, 1.0)), ('PINK', (1.0, 0.15, 0.6))]
PHYS = []                       # passive collision objects
PIECES = []                     # course pieces in order, for progress (who's in front)
LIPS = []                       # (points, colour) lip lines for the LED rails
SAMPLES_ALL = []                # every channel sample point (for supports / overlap checks)
SECTION_SIGNS = []              # (pos, heading, text, colour)
KIN = []                        # kinematic movers: (obj, fn(t) -> (loc, rot))

def profile(w, rc, wh, n=8):
    """flat-bottom U: half flat width w, corner radius rc, wall top wh (above the bottom). (side, up) pairs left->right"""
    pts = [(-(w + rc), wh)]
    for k in range(n + 1):
        a_ = math.pi + (math.pi / 2) * k / n; pts.append((-w + rc * math.cos(a_), rc + rc * math.sin(a_)))
    for k in range(n + 1):
        a_ = 1.5 * math.pi + (math.pi / 2) * k / n; pts.append((w + rc * math.cos(a_), rc + rc * math.sin(a_)))
    pts.append((w + rc, wh)); return pts

class Turtle:
    def __init__(s, pos, hdg_deg):
        s.p = Vector(pos); s.h = R(hdg_deg); s.g = 0.0; s.b = 0.0; s.w, s.rc, s.wh = 0.4, 0.08, 0.25
    def run(s, L, grade=None, turn=0.0, w=None, rc=None, wh=None, wave=None, ds=0.035, bank=True, blend=0.6):
        """L horizontal length; grade = dz/dx reached smoothly over `blend` m; turn = total heading change (deg, + = left)"""
        g0 = s.g; g1 = s.g if grade is None else grade; n = max(2, int(L / ds)); out = []
        w0, rc0, wh0 = s.w, s.rc, s.wh; w1 = w0 if w is None else w; rc1 = rc0 if rc is None else rc; wh1 = wh0 if wh is None else wh
        kappa = R(turn) / L; b0 = s.b
        for i in range(n + 1):
            u = i / n; d = u * L; gg = lerp(g0, g1, smooth(0, min(blend, L), d))
            if i > 0:
                hm = s.h + kappa * ds_ * 0.5; s.p = s.p + Vector((math.cos(hm) * ds_, math.sin(hm) * ds_, gg * ds_)); s.h += kappa * ds_
            ds_ = L / n
            wz = 0.0; wslope = 0.0
            if wave:
                amp, lam = wave; env = smooth(0, 0.8, d) * smooth(L, L - 0.8, d)
                wz = amp * env * (math.sin(2 * math.pi * d / lam) ); wslope = amp * env * 2 * math.pi / lam * math.cos(2 * math.pi * d / lam)
            T = Vector((math.cos(s.h), math.sin(s.h), gg + wslope)).normalized()
            side = Vector((math.sin(s.h), -math.cos(s.h), 0.0)); up = side.cross(T).normalized(); side = T.cross(up).normalized()
            b1 = 0.0
            if bank and abs(kappa) > 1e-6: b1 = clamp(math.atan(1.4 ** 2 / (9.81 / abs(kappa))), 0, R(14)) * (1 if kappa > 0 else -1)
            b_ = lerp(b0, b1, smooth(0, min(1.2, L * 0.45), d))
            sd = side * math.cos(b_) + up * math.sin(b_); upb = up * math.cos(b_) - side * math.sin(b_)
            out.append(dict(p=s.p + Vector((0, 0, wz)), T=T, side=sd, up=upb, w=lerp(w0, w1, u), rc=lerp(rc0, rc1, u), wh=lerp(wh0, wh1, u), h=s.h))
        s.g = g1; s.b = b_; s.w, s.rc, s.wh = w1, rc1, wh1
        return out
    def jump(s, dx, dz, dturn=0.0):
        s.p = s.p + Vector((math.cos(s.h) * dx, math.sin(s.h) * dx, dz)); s.h += R(dturn)
    def at(s, pos, hdg_deg, grade=0.0):
        s.p = Vector(pos); s.h = R(hdg_deg); s.g = grade; s.b = 0.0

def sweep(name, samples, m=None, cap_start=False, cap_end=False, tube_r=None, lanes=0, phys=True, pieces=True, led=None):
    """the channel surface (one-sided, normals inward). tube_r -> closed glass pipe instead of an open U."""
    vs, fs = [], []; ring = None
    for smp in samples:
        if tube_r: prof = [(tube_r * math.cos(2 * math.pi * k / 20), tube_r + tube_r * math.sin(2 * math.pi * k / 20)) for k in range(20)]
        else: prof = profile(smp['w'], smp['rc'], smp['wh'])
        ring = len(prof)
        for y_, z_ in prof: vs.append(smp['p'] + smp['side'] * y_ + smp['up'] * z_)
    n = len(samples)
    for i in range(n - 1):
        for k in range(ring if tube_r else ring - 1):
            k2 = (k + 1) % ring; fs.append((i * ring + k, i * ring + k2, (i + 1) * ring + k2, (i + 1) * ring + k))
    if cap_start: fs.append(tuple(range(ring)))
    if cap_end: fs.append(tuple((n - 1) * ring + k for k in range(ring))[::-1])
    o = mesh(name, [tuple(v) for v in vs], fs, m)
    if phys: PHYS.append(o)
    if pieces: PIECES.append(dict(kind='chan', name=name, pts=np.array([tuple(s_['p'] + s_['up'] * MR) for s_ in samples]),
                                  rad=max(s_['w'] + s_['rc'] for s_ in samples) + 0.25))
    SAMPLES_ALL.extend(tuple(s_['p']) for s_ in samples[::3])
    if not tube_r: LIPS.append(([s_['p'] + s_['side'] * -(s_['w'] + s_['rc']) + s_['up'] * s_['wh'] for s_ in samples],
                                [s_['p'] + s_['side'] * (s_['w'] + s_['rc']) + s_['up'] * s_['wh'] for s_ in samples], led))
    return o

def funnel(name, ctr, Rf, rh, depth, m, wall=0.30):
    """vortex: z falls like 1/r toward the hole; a rim wall keeps them in"""
    prof = [(Rf, ctr[2] + wall)]
    nn = 36
    for k in range(nn + 1):
        r_ = Rf * (rh / Rf) ** (k / nn); f_ = (1 / r_ - 1 / Rf) / (1 / rh - 1 / Rf); prof.append((r_, ctr[2] - depth * f_))
    prof.append((rh, ctr[2] - depth - 0.06))
    o = lathe(name, prof, 72, m, loc=(ctr[0], ctr[1], 0)); PHYS.append(o)
    PIECES.append(dict(kind='funnel', name=name, c=np.array(ctr), Rf=Rf, rh=rh, z0=ctr[2] + 0.4, z1=ctr[2] - depth - 0.5))
    SAMPLES_ALL.extend((ctr[0] + Rf * math.cos(a_), ctr[1] + Rf * math.sin(a_), ctr[2]) for a_ in np.linspace(0, 6.28, 24))
    return o

def plinko(name, top, hdg, tilt, W, Lb, m_board, m_peg, m_wall):
    """tilted peg board; returns (bottom-centre point, heading). Pegs on a hex grid, walls funnel the bottom to a gap"""
    h = R(hdg); th = R(tilt)
    D = Vector((math.cos(h) * math.cos(th), math.sin(h) * math.cos(th), -math.sin(th)))
    Sd = Vector((math.sin(h), -math.cos(h), 0)); Nn = Sd.cross(D).normalized()
    if Nn.z < 0: Nn = -Nn
    P = lambda u, v, n=0.0: Vector(top) + D * u + Sd * v + Nn * n
    hw = W / 2
    o = mesh(name, [tuple(P(-0.3, -hw)), tuple(P(-0.3, hw)), tuple(P(Lb, hw)), tuple(P(Lb, -hw))], [(0, 1, 2, 3)], m_board); PHYS.append(o)
    walls = []
    def wall(u0, v0, u1, v1, hgt=0.16, nm='w'):
        vs_ = [P(u0, v0), P(u1, v1), P(u1, v1, hgt), P(u0, v0, hgt)]
        w_ = mesh(name + nm, [tuple(v) for v in vs_], [(0, 1, 2, 3)], m_wall); PHYS.append(w_); walls.append(w_); return w_
    wall(-0.3, -hw, Lb, -hw, nm='L'); wall(-0.3, hw, Lb, hw, nm='R'); wall(-0.3, -hw, -0.3, hw, nm='T')
    gap = 0.17
    wall(Lb - 0.75, -hw, Lb, -gap, nm='FL'); wall(Lb - 0.75, hw, Lb, gap, nm='FR')
    pegs = []; row = 0; u = 0.6
    while u < Lb - 0.85:
        off = 0.0 if row % 2 == 0 else 0.11; v = -hw + 0.19 + off
        while v < hw - 0.18:
            pegs.append((P(u, v), Nn)); v += 0.22
        u += 0.2; row += 1
    # pegs as ONE mesh of little cylinders (fast)
    vs_, fs_ = [], []
    for c_, n_ in pegs:
        a0 = len(vs_); seg = 12
        ax1 = Sd; ax2 = D
        for k in range(seg):
            a_ = 2 * math.pi * k / seg; rr = ax1 * math.cos(a_) * 0.022 + ax2 * math.sin(a_) * 0.022
            vs_.append(tuple(c_ + rr)); vs_.append(tuple(c_ + rr + n_ * 0.13))
        for k in range(seg):
            k2 = (k + 1) % seg; fs_.append((a0 + 2 * k, a0 + 2 * k2, a0 + 2 * k2 + 1, a0 + 2 * k + 1))
        fs_.append(tuple(a0 + 2 * k + 1 for k in range(seg)))
    po = mesh(name + '_pegs', vs_, fs_, m_peg, smooth_=False); PHYS.append(po)
    PIECES.append(dict(kind='board', name=name, top=np.array(top), D=np.array(D), Sd=np.array(Sd), Lb=Lb, hw=hw + 0.3))
    for uu in np.linspace(0, Lb, 12):
        for vv in (-hw, 0, hw): SAMPLES_ALL.append(tuple(P(uu, vv)))
    return P(Lb, 0), hdg, (o, po, walls, P, D, Sd, Nn)

def build_course(M):
    """M: materials dict. Lays the whole course; returns the turtle path landmarks used by camera and decor."""
    LM = {}
    t = Turtle((0, 0, 30.0), 0)
    # 1 start ramp with 8 lanes for the first metre, then a bumpy slope that narrows
    a1 = t.run(3.2, grade=-0.30, w=0.42, rc=0.08, wh=0.22, blend=0.01)
    sweep('start', a1, M['track'], cap_start=True, led='white'); LM['start'] = a1
    a2 = t.run(6.0, grade=-0.13, w=0.26, wave=(0.05, 1.1)); sweep('bumps', a2, M['track'], led='white'); LM['bumps'] = a2
    # 2 the zigzag: six legs with tight U-turns (marbles bank hard and bash the walls)
    zz = []
    for k in range(6):
        leg = t.run(3.4, grade=-0.10, w=0.24, wh=0.22); zz.append(leg)
        if k < 5:
            ut = t.run(1.65, grade=-0.05, turn=180 if k % 2 == 0 else -180, wh=0.30); zz.append(ut)
    zzs = [s_ for seg in zz for s_ in seg]; sweep('zigzag', zzs, M['track2'], led='cyan'); LM['zigzag'] = zzs
    # 3 the steep drop, a kicker, JUMP 1, into a wide catch tray
    d3 = t.run(3.0, grade=-0.42, w=0.16, wh=0.20, blend=0.5); k3 = t.run(0.7, grade=0.30, blend=0.5)
    sweep('drop1', d3 + k3, M['track'], led='orange'); LM['kick1'] = k3[-1]['p'].copy(); LM['kick1_h'] = t.h
    t.jump(1.0, -0.9); t.g = -0.10
    tr = t.run(3.4, grade=-0.08, w=0.40, wh=0.34, blend=0.1); tr2 = t.run(3.5, turn=-60, w=0.14, wh=0.24)
    sweep('land1', tr + tr2, M['track'], cap_start=True, led='orange'); LM['land1'] = tr[0]['p'].copy()
    # 4 into vortex funnel 1, tangent at its rim
    Rf = 1.25; fdrop = 0.22
    hh = t.h; ctr = t.p + Vector((math.cos(hh + math.pi / 2), math.sin(hh + math.pi / 2), 0)) * (Rf - 0.38)
    ctr.z = t.p.z - 0.10 - 0.30
    funnel('vortex1', tuple(ctr), Rf, 0.085, 1.0, M['funnel']); LM['vortex1'] = ctr.copy()
    # 5 catch under the hole, then the banked half-pipe S-bends
    t.at((ctr.x - 0.35 * math.cos(hh), ctr.y - 0.35 * math.sin(hh), ctr.z - 1.0 - 0.55), math.degrees(hh), grade=-0.10)
    t.w, t.rc, t.wh = 0.20, 0.10, 0.34
    c5 = t.run(1.6, grade=-0.12, w=0.0, rc=0.30, wh=0.36)
    s1 = t.run(5.0, turn=90, grade=-0.12); s2 = t.run(5.5, turn=-130); s3 = t.run(5.5, turn=130); s4 = t.run(3.5, turn=-80)
    sweep('halfpipe', c5 + s1 + s2 + s3 + s4, M['track3'], cap_start=True, led='purple'); LM['halfpipe'] = c5 + s1 + s2 + s3 + s4
    # 6 the glass corkscrew (single file: a clear pipe)
    t.w, t.rc = 0.0, 0.09
    gi = t.run(1.2, grade=-0.14, w=0.0, rc=0.095, wh=0.30)
    sweep('pipe_in', gi, M['track3'], led='purple')
    cs = t.run(2 * math.pi * 0.85 * 2, grade=-0.12, turn=720, bank=False)
    sweep('corkscrew', cs, M['glass'], tube_r=0.085); LM['corkscrew'] = cs
    # 7 chute out onto the plinko board
    co = t.run(1.6, grade=-0.25, w=0.0, rc=0.10, wh=0.22); sweep('pipe_out', co, M['track'], led='green')
    top = t.p + Vector((math.cos(t.h), math.sin(t.h), 0)) * -0.25 + Vector((0, 0, -0.24))
    bot, bh, PL = plinko('plinko', tuple(top), math.degrees(t.h), 24, 1.7, 3.6, M['board'], M['peg'], M['wall']); LM['plinko'] = (top, bot, PL)
    # 8 tray under the board's gap, then the three-lane split with speed bumps in the side lanes
    hh = R(bh)
    t.at(bot + Vector((math.cos(hh) * -0.05, math.sin(hh) * -0.05, -0.32)), bh, grade=-0.10); t.w, t.rc, t.wh = 0.40, 0.08, 0.36
    tr8 = t.run(1.5, grade=-0.10, w=0.38, wh=0.26)
    ln = t.run(8.0, grade=-0.10, turn=40, w=0.38)
    lo = t.run(2.0, w=0.16, wh=0.22)
    sweep('lanes', tr8 + ln + lo, M['track2'], cap_start=True, led='green'); LM['lanes'] = ln
    # dividers and bumps inside the lanes
    divs = []
    for sv in (-0.13, 0.13):
        pts_ = [s_['p'] + s_['side'] * sv + s_['up'] * 0.0 for s_ in ln[8:-8]]
        vs_, fs_ = [], []
        for i, (s_, p_) in enumerate(zip(ln[8:-8], pts_)):
            for dv in (-0.012, 0.012):
                vs_.append(tuple(p_ + s_['side'] * dv)); vs_.append(tuple(p_ + s_['side'] * dv + s_['up'] * 0.13))
        for i in range(len(pts_) - 1):
            b0 = 4 * i; b1 = 4 * (i + 1)
            fs_ += [(b0, b1, b1 + 1, b0 + 1), (b0 + 2, b0 + 3, b1 + 3, b1 + 2), (b0 + 1, b1 + 1, b1 + 3, b0 + 3)]
        fs_ += [(0, 1, 3, 2)]
        dv_ = mesh('divider', vs_, fs_, M['wall']); PHYS.append(dv_); divs.append(dv_)
    bumps = []
    for i in range(20, len(ln) - 20, 22):
        s_ = ln[i]
        for lv in (-0.26, 0.26):
            c_ = s_['p'] + s_['side'] * lv
            bp = tube('bump', [tuple(c_ + s_['side'] * -0.11), tuple(c_ + s_['side'] * 0.11)], 0.022, M['peg'], seg=12); PHYS.append(bp); bumps.append(bp)
    LM['divs'] = divs; LM['bumps_l'] = bumps
    # 9 JUMP 2: the big one, off a ramp and over a gap onto a wide tray
    d9 = t.run(3.6, grade=-0.45, w=0.14, wh=0.20, blend=0.5); k9 = t.run(0.8, grade=0.38, blend=0.5)
    sweep('drop2', d9 + k9, M['track'], led='orange'); LM['kick2'] = k9[-1]['p'].copy(); LM['kick2_h'] = t.h
    t.jump(1.0, -1.4); t.g = -0.08
    tr9 = t.run(4.0, grade=-0.06, w=0.45, wh=0.40, blend=0.1); tr9b = t.run(2.0, turn=30, w=0.10, rc=0.25, wh=0.36)
    sweep('land2', tr9 + tr9b, M['track'], cap_start=True, led='orange'); LM['land2'] = tr9[0]['p'].copy()
    # 10 helix round the glowing tower: two and a half laps, banked half-pipe
    Rh = 2.3; hx = t.run(2 * math.pi * Rh * 2.5, grade=-0.075, turn=900)
    sweep('helix', hx, M['track3'], led='blue'); LM['helix'] = hx
    hc = hx[0]['p'] + Vector((math.cos(hx[0]['h'] + math.pi / 2), math.sin(hx[0]['h'] + math.pi / 2), 0)) * Rh
    LM['tower'] = (hc.x, hc.y, hx[-1]['p'].z - 1.0, hx[0]['p'].z + 1.5)
    # 11 out to vortex 2, the giant funnel
    o11 = t.run(4.0, grade=-0.10, turn=-50, w=0.0, rc=0.14, wh=0.24); sweep('to_vortex2', o11, M['track'], led='pink')
    Rf2 = 1.9; hh = t.h; ctr2 = t.p + Vector((math.cos(hh - math.pi / 2), math.sin(hh - math.pi / 2), 0)) * (Rf2 - 0.42)
    ctr2.z = t.p.z - 0.10 - 0.30
    funnel('vortex2', tuple(ctr2), Rf2, 0.085, 1.3, M['funnel']); LM['vortex2'] = ctr2.copy()
    # 12 catch, then the roller waves (they get air off every crest)
    t.at((ctr2.x - 0.35 * math.cos(hh), ctr2.y - 0.35 * math.sin(hh), ctr2.z - 1.3 - 0.55), math.degrees(hh), grade=-0.10)
    t.w, t.rc, t.wh = 0.22, 0.10, 0.34
    c12 = t.run(2.0, grade=-0.12, w=0.20, wh=0.40, turn=-30)
    wv = t.run(10.0, grade=-0.08, wave=(0.11, 1.7), turn=20)
    sweep('rollers', c12 + wv, M['track2'], cap_start=True, led='yellow'); LM['rollers'] = wv
    # 13 JUMP 3 through the ring, then the finish straight
    d13 = t.run(3.4, grade=-0.40, w=0.14, wh=0.20, blend=0.5); k13 = t.run(0.8, grade=0.42, blend=0.5)
    sweep('drop3', d13 + k13, M['track'], led='orange'); LM['kick3'] = k13[-1]['p'].copy(); LM['kick3_h'] = t.h
    t.jump(1.0, -1.3); t.g = -0.05
    fz = t.run(4.0, grade=-0.04, w=0.50, wh=0.40, blend=0.1); LM['land3'] = fz[0]['p'].copy()
    fs = t.run(7.0, grade=-0.02, w=0.40, wh=0.30); fe = t.run(2.4, grade=0.20, w=0.40, blend=1.2)
    sweep('finish', fz + fs + fe, M['finish'], cap_start=True, cap_end=True, led='white'); LM['finish'] = fs
    LM['finish_line'] = fs[int(len(fs) * 0.25)]
    return LM
# ================================================================ materials: dark glossy track so the glowing marbles light it up
def track_mat(name, col, rough=0.28):
    m = mat(name, col, rough, 0.0, coat=0.6); noisy(m, 9.0, 0.10, 0.06); return m
M = dict(track=track_mat('track', (0.035, 0.038, 0.045)), track2=track_mat('track2', (0.02, 0.05, 0.09)),
         track3=track_mat('track3', (0.06, 0.03, 0.08)), funnel=track_mat('funnel', (0.05, 0.05, 0.06), 0.18),
         glass=mat('glass', (0.92, 0.97, 1.0), 0.03, trans=1.0, ior=1.45), board=track_mat('board', (0.03, 0.06, 0.05)),
         peg=mat('peg', (0.75, 0.75, 0.78), 0.22, 1.0), wall=mat('wallm', (0.1, 0.1, 0.12), 0.3, 0.6), finish=track_mat('finish', (0.04, 0.04, 0.05)))
LED = {k: emis('led_' + k, c, 6.0) for k, c in (('white', (0.9, 0.92, 1.0)), ('cyan', (0.0, 0.75, 1.0)), ('orange', (1.0, 0.35, 0.02)),
       ('purple', (0.55, 0.1, 1.0)), ('green', (0.1, 1.0, 0.3)), ('blue', (0.1, 0.25, 1.0)), ('pink', (1.0, 0.1, 0.5)), ('yellow', (1.0, 0.8, 0.05)))}

def marble_mats(i):
    nm, col = COLS[i]
    # glass shell
    sh = bpy.data.materials.new(f'shell_{nm}'); sh.use_nodes = True; nt = sh.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*[0.6 + 0.4 * c for c in col], 1); b.inputs['Roughness'].default_value = 0.02
    b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.5
    b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = 0.6
    # glowing core with a swirl, so you can see it spin
    co = bpy.data.materials.new(f'core_{nm}'); co.use_nodes = True; nt = co.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 1.6; wv.inputs['Distortion'].default_value = 3.0; wv.inputs['Detail'].default_value = 2.0
    nt.links.new(coord(nt, 'Object'), wv.inputs['Vector'])
    hot = tuple(min(1.0, c * 0.5 + 0.55) for c in col)
    cc = ramp(nt, wv.outputs['Fac'], [(0.0, col), (0.45, col), (0.6, hot), (0.75, col), (1.0, tuple(c * 0.4 for c in col))])
    nt.links.new(cc, e_.inputs['Color']); e_.inputs['Strength'].default_value = 9.0
    nt.links.new(e_.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return sh, co

MARB = []
for i_ in range(NM):
    sh_, co_ = marble_mats(i_)
    mo = prim('uv_sphere', f'marble_{i_}', sh_, segments=40, ring_count=20, radius=MR)
    core = prim('uv_sphere', f'core_{i_}', co_, parent=mo, segments=24, ring_count=12, radius=MR * 0.62)
    lt = bpy.data.lights.new(f'mlight_{i_}', 'POINT'); lt.energy = 5.0; lt.color = COLS[i_][1]; lt.shadow_soft_size = MR * 0.6
    lo = bpy.data.objects.new(f'mlight_{i_}', lt); S.collection.objects.link(lo); lo.parent = mo
    try: lt.use_shadow = True
    except Exception: pass
    mo.rotation_mode = 'QUATERNION'; MARB.append(mo)
# ================================================================ build the course
for mo in MARB: mo.visible_shadow = False          # the marble's own light shines out through its glass
LMK = build_course(M)
print('course built:', len(PHYS), 'collision parts,', len(PIECES), 'pieces')
LMK['floor_z'] = min(p_[2] for p_ in SAMPLES_ALL) - 1.2
# ================================================================ physics: Bullet, baked once into sim.npz (positions, rotations, progress)
SIM_PRE = 14                                    # sim frames before video frame 0 (the gate is already dropping on frame one)
def piece_len(pc):
    if pc['kind'] == 'chan': return float(np.sum(np.linalg.norm(np.diff(pc['pts'], axis=0), axis=1)))
    if pc['kind'] == 'funnel': return 2.0 * pc['Rf']
    return pc['Lb']
PLEN = [piece_len(pc) for pc in PIECES]; PSTART = np.concatenate([[0.0], np.cumsum(PLEN)])[:-1]
def piece_frac(pc, p):
    """fraction 0..1 through this piece, or None if the marble isn't in it"""
    if pc['kind'] == 'chan':
        d = np.linalg.norm(pc['pts'] - p, axis=1); i = int(np.argmin(d))
        if d[i] > pc['rad']: return None
        return i / (len(pc['pts']) - 1)
    if pc['kind'] == 'funnel':
        if not (pc['z1'] < p[2] < pc['z0']): return None
        r = math.hypot(p[0] - pc['c'][0], p[1] - pc['c'][1])
        if r > pc['Rf'] + 0.1: return None
        if p[2] < pc['c'][2] - 1.0: return 0.98
        return clamp((pc['Rf'] - r) / (pc['Rf'] - pc['rh']), 0, 0.97)
    q = p - pc['top']; u = float(np.dot(q, pc['D'])); v = float(np.dot(q, pc['Sd']))
    nrm = np.cross(pc['Sd'], pc['D']); n = abs(float(np.dot(q, nrm)))
    if -0.9 < u < pc['Lb'] + 0.4 and abs(v) < pc['hw'] and n < 0.5: return clamp(u / pc['Lb'], 0, 1)
    return None

def run_sim(seconds):
    bpy.ops.rigidbody.world_add(); rw = S.rigidbody_world
    rw.substeps_per_frame = 24; rw.solver_iterations = 30; rw.time_scale = 1.0
    nF = int(seconds * FPS) + SIM_PRE; rw.point_cache.frame_start = 1; rw.point_cache.frame_end = nF + 2
    S.frame_start = 1; S.frame_end = nF + 2
    rbc = bpy.data.collections.new('RigidBodyWorld'); rw.collection = rbc
    def add_rb(o, kind):
        rbc.objects.link(o) if o.name not in rbc.objects else None
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.rigidbody.object_add(type=kind); o.select_set(False); return o.rigid_body
    for o in PHYS:
        rb = add_rb(o, 'PASSIVE'); rb.collision_shape = 'MESH'; rb.mesh_source = 'BASE'; rb.friction = 0.35; rb.restitution = 0.35
        rb.collision_margin = 0.002
    # start gate: a bar across the ramp that drops away at sim frame 6
    st = LMK['start']; g0 = st[int(len(st) * 0.25)]
    gate = box('gate', (0.03, 1.1, 0.25), tuple(g0['p'] + g0['up'] * 0.12), M['wall']); gate.rotation_mode = 'QUATERNION'
    gate.rotation_quaternion = Matrix((g0['T'], g0['side'], g0['up'])).transposed().to_quaternion()
    rb = add_rb(gate, 'PASSIVE'); rb.kinematic = True; rb.collision_shape = 'BOX'
    gate.keyframe_insert('location', frame=6); gate.location = gate.location + g0['up'] * -0.35; gate.keyframe_insert('location', frame=10)
    GATE[0] = gate
    rng = random.Random(a.seed); order = list(range(NM)); rng.shuffle(order)
    s0 = st[int(len(st) * 0.12)]
    for slot, i in enumerate(order):
        mo = MARB[i]; mo.location = s0['p'] + s0['side'] * ((slot - 3.5) * 0.105) + s0['up'] * (MR + 0.004) + s0['T'] * rng.uniform(-0.02, 0.02)
        rb = add_rb(mo, 'ACTIVE'); rb.collision_shape = 'SPHERE'; rb.mass = 0.05; rb.friction = 0.4; rb.restitution = 0.45
        rb.linear_damping = 0.30 + rng.uniform(-0.01, 0.01); rb.angular_damping = 0.15; rb.use_deactivation = False; rb.collision_margin = 0.001
        rb.use_margin = True
    POS = np.zeros((nF, NM, 3), np.float32); QUA = np.zeros((nF, NM, 4), np.float32); PRG = np.zeros((nF, NM), np.float32)
    cur = [0] * NM; best = [0.0] * NM; done = [None] * NM; total = float(PSTART[-1] + PLEN[-1])
    import time; t0 = time.time()
    for f in range(nF):
        S.frame_set(f + 1)
        for i, mo in enumerate(MARB):
            mw = mo.matrix_world; p = np.array(mw.translation); POS[f, i] = p; QUA[f, i] = tuple(mw.to_quaternion())
            got = None
            for j in range(cur[i], min(cur[i] + 3, len(PIECES))):
                fr = piece_frac(PIECES[j], p)
                if fr is not None: got = (j, fr)
            if got: cur[i] = got[0]; best[i] = max(best[i], PSTART[got[0]] + got[1] * PLEN[got[0]])
            PRG[f, i] = best[i]
            if done[i] is None and PIECES[cur[i]]['name'] == 'finish' and np.linalg.norm(p - np.array(tuple(LMK['finish_line']['p']))) < 0.6 \
               and np.dot(p - np.array(tuple(LMK['finish_line']['p'])), np.array(tuple(LMK['finish_line']['T']))) > 0:
                done[i] = f
        if f % 150 == 0:
            lead = int(np.argmax(PRG[f])); print(f'sim {f}/{nF}  {time.time() - t0:.0f}s  lead {COLS[lead][0]} {PRG[f, lead]:.1f}/{total:.0f} m  '
                                               f'pieces {[PIECES[c]["name"] for c in cur]}', flush=True)
        if all(d is not None for d in done) and f > max(done) + 6 * FPS: POS, QUA, PRG = POS[:f + 1], QUA[:f + 1], PRG[:f + 1]; break
        if any(p_[2] < LMK['floor_z'] + 0.3 for p_ in POS[f]):
            lost = [COLS[i][0] for i in range(NM) if POS[f, i, 2] < LMK['floor_z'] + 0.3]; print('LOST', lost, 'frame', f, [PIECES[c]['name'] for c in cur]);
            POS, QUA, PRG = POS[:f + 1], QUA[:f + 1], PRG[:f + 1]; break
    fin = np.array([d if d is not None else -1 for d in done])
    np.savez_compressed(os.path.join(HERE, os.environ.get('SIMOUT', 'sim.npz')), pos=POS, quat=QUA, prog=PRG, fin=fin, pre=SIM_PRE, total=total)
    print('finish frames', {COLS[i][0]: (int(d) - SIM_PRE) / FPS if d is not None else None for i, d in enumerate(done)})
GATE = [None]
# ================================================================ decor (render only): LED rails, thickness, supports, floor, signs, tower, ring, arches
def no_light(m):
    try: m.cycles.emission_sampling = 'NONE'
    except Exception: pass
    return m
if not a.sim:
    for m_ in LED.values(): no_light(m_)
    for o in PHYS:
        if o.name.startswith(('start', 'bumps', 'zigzag', 'drop', 'land', 'halfpipe', 'pipe_', 'lanes', 'helix', 'to_vortex', 'rollers', 'finish', 'vortex')):
            sd = o.modifiers.new('thick', 'SOLIDIFY'); sd.thickness = 0.022; sd.offset = -1.0 if not o.name.startswith('vortex') else 1.0
            sd.use_even_offset = True
            bv = o.modifiers.new('bv', 'BEVEL'); bv.width = 0.006; bv.segments = 2; bv.limit_method = 'ANGLE'
    # LED rails along every lip (a thin glowing tube) + a chrome rim under it
    rim_m = mat('rim', (0.8, 0.8, 0.85), 0.18, 1.0)
    def rail(pts, m, r, nm):
        pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
        if len(pts) > 2: tube(nm, [tuple(p) for p in pts], r, m, seg=8)
    for k_, (lp, rp, led) in enumerate(LIPS):
        for side_, pts in (('L', lp), ('R', rp)):
            rail(pts, rim_m, 0.011, f'rim{k_}{side_}')
            rail([p + Vector((0, 0, 0.012)) for p in pts], LED[led or 'white'], 0.0055, f'led{k_}{side_}')
    # supports: a cradle bar under the track every ~1.5 m and a steel post down to the floor where nothing is underneath
    from mathutils import kdtree
    KD = kdtree.KDTree(len(SAMPLES_ALL))
    for i_, p_ in enumerate(SAMPLES_ALL): KD.insert(p_, i_)
    KD.balance()
    FLOOR = LMK['floor_z']
    steel = mat('steel', (0.55, 0.56, 0.6), 0.32, 1.0); noisy(steel, 30, 0.08, 0.08)
    yel = mat('yellow_paint', (0.9, 0.55, 0.02), 0.4, 0.0, coat=0.3)
    posts_v, posts_f = [], []
    def post(x, y, z0, z1, r=0.022, seg=8):
        b0 = len(posts_v)
        for k in range(seg):
            a_ = 2 * math.pi * k / seg; posts_v.append((x + r * math.cos(a_), y + r * math.sin(a_), z0)); posts_v.append((x + r * math.cos(a_), y + r * math.sin(a_), z1))
        for k in range(seg): k2 = (k + 1) % seg; posts_f.append((b0 + 2 * k, b0 + 2 * k2, b0 + 2 * k2 + 1, b0 + 2 * k + 1))
    def clear_below(p, r=0.5):
        for (co, idx, dist) in KD.find_range(p, 30.0):
            if co[2] < p[2] - 0.15 and math.hypot(co[0] - p[0], co[1] - p[1]) < r: return False
        return True
    for nm_, smp in [(k, v) for k, v in LMK.items() if k in ('start', 'bumps', 'zigzag', 'halfpipe', 'lanes', 'helix', 'rollers', 'finish')]:
        for j in range(0, len(smp), 40):
            s_ = smp[j]; bot = s_['p'] - Vector((0, 0, 0.03)); wd = s_['w'] + s_['rc'] + 0.03
            box('cradle', (0.05, 2 * wd, 0.03), tuple(bot), steel, rot=(0, 0, s_['h']))
            if j % 80 == 0:
                for sv in (-wd, wd):
                    q = bot + s_['side'] * sv
                    if clear_below(q): post(q.x, q.y, FLOOR, q.z)
    # floor: dark polished concrete with a faint grid, huge
    cx = sum(p_[0] for p_ in SAMPLES_ALL) / len(SAMPLES_ALL); cy = sum(p_[1] for p_ in SAMPLES_ALL) / len(SAMPLES_ALL)
    fm = bpy.data.materials.new('floor'); fm.use_nodes = True; nt = fm.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.22; b.inputs['Base Color'].default_value = (0.02, 0.022, 0.028, 1)
    tc_ = coord(nt, 'Object'); br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 0.5; br.inputs['Mortar Size'].default_value = 0.004
    br.inputs['Color1'].default_value = (0.022, 0.024, 0.03, 1); br.inputs['Color2'].default_value = (0.018, 0.02, 0.025, 1); br.inputs['Mortar'].default_value = (0.0, 0.25, 0.45, 1)
    nt.links.new(tc_, br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    em_ = math_(nt, 'MULTIPLY', br.outputs['Fac'], 0.35)
    b.inputs['Emission Color'].default_value = (0.0, 0.35, 0.7, 1); nt.links.new(em_, b.inputs['Emission Strength'])
    no_light(fm)
    flo = prim('plane', 'floor', fm, loc=(cx, cy, FLOOR), size=400.0)
    # far walls: a dark arena ring with rows of small lights (depth cue), well outside the course
    arena = bpy.data.materials.new('arena'); arena.use_nodes = True; nt = arena.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e_ = nt.nodes.new('ShaderNodeEmission'); sx_ = sepz(nt, coord(nt, 'Object'))
    hz = math_(nt, 'POWER', math_(nt, 'ABSOLUTE', math_(nt, 'SINE', math_(nt, 'MULTIPLY', sx_.outputs['Z'], 0.22))), 400.0)
    zf = math_(nt, 'MULTIPLY', hz, math_(nt, 'LESS_THAN', sx_.outputs['Z'], FLOOR + 30))
    cc_ = mixc(nt, zf, (0.004, 0.006, 0.012), (0.05, 0.11, 0.24)); nt.links.new(cc_, e_.inputs['Color']); e_.inputs['Strength'].default_value = 1.0
    nt.links.new(e_.outputs[0], nt.nodes['Material Output'].inputs['Surface']); no_light(arena)
    ar = lathe('arena', [(85, FLOOR), (85, FLOOR + 60)], 96, arena, loc=(cx, cy, 0))
    # lights: big soft overheads so the track reads, cool rim from the far side; the marbles do the rest
    WBG.inputs['Color'].default_value = (0.006, 0.008, 0.016, 1); WBG.inputs['Strength'].default_value = 1.0
    for k, (dx, dy) in enumerate(((-15, -6), (5, 3), (-30, 14), (-40, 22), (-25, 8))):
        light_at(f'over{k}', 'AREA', (cx + dx, cy + dy, 40), (cx + dx, cy + dy, 0), 9000, (0.75, 0.82, 1.0), size=14)
    # the tower in the helix: a tall frosted column with glowing blue bands
    tx, ty, tz0, tz1 = LMK['tower']
    tw = mat('tower', (0.05, 0.08, 0.15), 0.25, 0.3)
    lathe('tower', [(0.0, FLOOR), (1.15, FLOOR), (1.15, tz1 + 0.6), (0.9, tz1 + 1.0), (0.0, tz1 + 1.1)], 64, tw, loc=(tx, ty, 0))
    tb = no_light(emis('tower_led', (0.15, 0.45, 1.0), 5.0))
    zz_ = FLOOR + 0.8
    while zz_ < tz1 + 0.5:
        lathe('tband', [(1.16, zz_), (1.18, zz_ + 0.02), (1.18, zz_ + 0.08), (1.16, zz_ + 0.1)], 64, tb, loc=(tx, ty, 0)); zz_ += 0.7
    # LED rings round both funnel rims
    for key in ('vortex1', 'vortex2'):
        c_ = LMK[key]; Rf_ = 1.25 if key == 'vortex1' else 1.9
        lathe(key + '_ring', [(Rf_ + 0.005, c_.z + 0.30), (Rf_ + 0.02, c_.z + 0.31), (Rf_ + 0.02, c_.z + 0.33)], 96, LED['pink' if key == 'vortex2' else 'orange'], loc=(c_.x, c_.y, 0))
        lathe(key + '_skirt', [(Rf_ + 0.01, c_.z - 0.2), (Rf_ + 0.01, c_.z + 0.30)], 96, steel, loc=(c_.x, c_.y, 0))
        if clear_below(c_, 0.6): post(c_.x, c_.y, FLOOR, c_.z - (1.0 if key == 'vortex1' else 1.3), r=0.06, seg=12)
    # glowing hoop over the final jump, at the top of the marbles' flight
    try:
        sim_ = np.load(os.path.join(HERE, 'sim.npz')); P_ = sim_['pos']; k3 = np.array(tuple(LMK['kick3'])); h3 = LMK['kick3_h']
        fw3 = np.array([math.cos(h3), math.sin(h3), 0]); apex = []
        for i in range(NM):
            ah = (P_[:, i] - k3) @ fw3; ok = np.where((ah > 0.2) & (ah < 1.4) & (np.linalg.norm(P_[:, i, :2] - k3[:2], axis=1) < 1.6))[0]
            if len(ok): apex.append(P_[ok[np.argmax(P_[ok, i, 2])], i])
        ap_ = np.mean(apex, axis=0); LMK['hoop'] = Vector(tuple(ap_))
        hoop_m = no_light(emis('hoop', (1.0, 0.35, 0.02), 9.0))
        bm_ = bmesh.new(); bmesh.ops.create_circle(bm_, segments=64, radius=0.42)
        pts_ = [Vector(tuple(ap_)) + Vector((0, 0, 0)) + Vector((-math.sin(h3), math.cos(h3), 0)) * 0.42 * math.cos(2 * math.pi * k / 64) + Vector((0, 0, 0.42)) * math.sin(2 * math.pi * k / 64) for k in range(65)]
        bm_.free(); tube('hoop', [tuple(p) for p in pts_], 0.025, hoop_m, seg=10, caps=False)
    except Exception as e_: print('hoop skipped', e_)
    # arches: START and FINISH, with a checkered line on the finish
    def arch(s_, text, col, wd=0.75, hgt=0.75):
        q0 = s_['p'] + s_['side'] * -wd; q1 = s_['p'] + s_['side'] * wd
        for q in (q0, q1): box('arch_post', (0.06, 0.06, hgt), tuple(q + Vector((0, 0, hgt / 2 - 0.02))), steel)
        box('arch_bar', (0.08, 2 * wd + 0.06, 0.16), tuple(s_['p'] + Vector((0, 0, hgt))), steel, rot=(0, 0, s_['h']))
        tx_ = bpy.data.curves.new('t_' + text, 'FONT'); tx_.body = text; tx_.align_x = 'CENTER'; tx_.align_y = 'CENTER'; tx_.size = 0.13; tx_.extrude = 0.004
        to = bpy.data.objects.new('t_' + text, tx_); S.collection.objects.link(to); to.data.materials.append(no_light(emis('tm_' + text, col, 6.0)))
        to.location = s_['p'] + Vector((0, 0, hgt)) - s_['T'] * 0.045; to.rotation_euler = (math.pi / 2, 0, s_['h'] - math.pi / 2)
        to2 = to.copy(); S.collection.objects.link(to2); to2.location = s_['p'] + Vector((0, 0, hgt)) + s_['T'] * 0.045; to2.rotation_euler = (math.pi / 2, 0, s_['h'] + math.pi / 2)
    arch(LMK['start'][2], 'START', (0.2, 1.0, 0.3), wd=0.62)
    fl_ = LMK['finish_line']; arch(fl_, 'FINISH', (1.0, 1.0, 1.0), wd=0.62)
    ck = bpy.data.materials.new('checker'); ck.use_nodes = True; nt = ck.node_tree; b = nt.nodes['Principled BSDF']
    cb = nt.nodes.new('ShaderNodeTexChecker'); cb.inputs['Scale'].default_value = 1.0; cb.inputs['Color1'].default_value = (0.9, 0.9, 0.9, 1); cb.inputs['Color2'].default_value = (0.01, 0.01, 0.01, 1)
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (14, 14, 14); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector']); nt.links.new(mp.outputs[0], cb.inputs['Vector'])
    nt.links.new(cb.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.3
    stripe = prim('plane', 'finish_stripe', ck, loc=tuple(fl_['p'] + fl_['up'] * 0.004), scale=(0.14 / 2, (fl_['w'] + 0.05), 1), size=2.0)
    stripe.rotation_mode = 'QUATERNION'; stripe.rotation_quaternion = Matrix((fl_['T'], fl_['side'], fl_['up'])).transposed().to_quaternion()
    # section signs: glowing word panels beside each feature
    SIGNS = [('zigzag', 'ZIGZAG', 'cyan'), ('kick1', 'JUMP!', 'orange'), ('vortex1', 'VORTEX', 'orange'), ('halfpipe', 'HALF-PIPE', 'purple'),
             ('corkscrew', 'CORKSCREW', 'purple'), ('plinko', 'PLINKO', 'green'), ('lanes', 'PICK A LANE', 'green'), ('kick2', 'BIG JUMP', 'orange'),
             ('helix', 'THE TOWER', 'blue'), ('vortex2', 'MEGA VORTEX', 'pink'), ('rollers', 'ROLLERS', 'yellow'), ('kick3', 'FINAL JUMP', 'orange')]
    panel_m = mat('panel', (0.02, 0.02, 0.03), 0.35, 0.2)
    def sign_at(pos, hdg, text, led, size=0.22):
        tx_ = bpy.data.curves.new('s_' + text, 'FONT'); tx_.body = text; tx_.align_x = 'CENTER'; tx_.align_y = 'CENTER'; tx_.size = size; tx_.extrude = 0.006
        to = bpy.data.objects.new('s_' + text, tx_); S.collection.objects.link(to); to.data.materials.append(LED[led])
        to.location = pos; to.rotation_euler = (math.pi / 2, 0, hdg)
        tb_ = to.copy(); S.collection.objects.link(tb_); tb_.location = pos - Vector((math.sin(hdg), -math.cos(hdg), 0)) * 0.06; tb_.rotation_euler = (math.pi / 2, 0, hdg + math.pi)
        wdt = 0.14 * size * len(text) * 4.6
        box('panel', (wdt, 0.03, size * 1.7), tuple(pos - Vector((math.sin(hdg), -math.cos(hdg), 0)) * 0.03), panel_m, rot=(0, 0, hdg))
        post(pos.x - math.sin(hdg) * 0.06, pos.y + math.cos(hdg) * 0.06, FLOOR, pos.z - size * 0.85, r=0.03)
    for key, text, led in SIGNS:
        v_ = LMK[key]
        if isinstance(v_, list): s_ = v_[len(v_) // 6]; base = s_['p']; hh_ = s_['h']; sd_ = s_['side']
        elif isinstance(v_, tuple): base = Vector(v_[0]); hh_ = 0.0; sd_ = Vector((0, -1, 0))
        else: base = Vector(v_); hh_ = LMK.get(key + '_h', 0.0); sd_ = Vector((math.sin(hh_), -math.cos(hh_), 0))
        if key.startswith('vortex'): pos = base + Vector((0, 0, 1.0)); hh_ = 0.0
        elif key == 'helix': tx0, ty0, _, tz1_ = LMK['tower']; pos = Vector((tx0, ty0, tz1_ + 1.6)); hh_ = 0.0
        else: pos = base + sd_ * -1.0 + Vector((0, 0, 0.55))
        LMK['sign_' + key] = pos
        sign_at(pos, 0.0 if key.startswith(('vortex', 'helix')) else hh_ + math.pi, text, led)
    if posts_v: mesh('posts', posts_v, posts_f, steel, smooth_=True)
# ================================================================ the one continuous camera: chase the front of the pack, rest on each big feature
if not a.sim:
    SIM = np.load(os.path.join(HERE, 'sim.npz')); SPOS = SIM['pos']; SQUA = SIM['quat']; SPRG = SIM['prog']; PRE = int(SIM['pre'])
    NFR = SPOS.shape[0] - PRE
    TT = np.arange(NFR) / FPS
    def gsmooth(arr, sig_s):
        sig = sig_s * FPS; r = int(sig * 3) + 1; k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
        pad = np.concatenate([np.repeat(arr[:1], r, 0), arr, np.repeat(arr[-1:], r, 0)]); out = np.empty_like(arr)
        for c in range(arr.shape[1]): out[:, c] = np.convolve(pad[:, c], k, 'valid')
        return out
    # focus: the front of the race, weighted toward whoever is close to the lead
    P_ = SPOS[PRE:]; G_ = SPRG[PRE:]
    w_ = np.exp(-(G_.max(axis=1, keepdims=True) - G_) / 1.2); FOC = (P_ * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
    FIN = SIM['fin'] - PRE; T_WIN = FIN.min() / FPS; T_LAST = FIN.max() / FPS
    fl_ = np.array(tuple(LMK['finish_line']['p']))
    after = TT > T_WIN + 0.6; FOC[after] = fl_ + np.array([0, 0, 0.05])          # once the winner crosses, watch the line
    pile = P_[-1].mean(axis=0) + np.array([0, 0, 0.03])
    for i in range(NFR):
        u = smooth(T_LAST + 0.3, T_LAST + 2.5, TT[i])
        if u > 0: FOC[i] = FOC[i] * (1 - u) + pile * u
    FOC = gsmooth(FOC, 0.35)
    VEL = gsmooth(np.gradient(FOC, axis=0) * FPS, 0.9); HD = VEL.copy(); HD[:, 2] = 0
    HD /= np.maximum(np.linalg.norm(HD, axis=1, keepdims=True), 1e-4); HD = gsmooth(HD, 0.6); HD /= np.maximum(np.linalg.norm(HD, axis=1, keepdims=True), 1e-4)
    SDV = np.stack([HD[:, 1], -HD[:, 0], np.zeros(NFR)], 1)        # right-hand side of travel
    UPZ = np.array([0, 0, 1.0])
    def vec(v): return np.array(tuple(v), float)
    def lead_t(name):
        st = PSTART[[p['name'] for p in PIECES].index(name)]; return float(np.argmax(G_.max(axis=1) >= st)) / FPS
    def landmark_side(key, off_side, off_fwd, up, hdg_key=None):
        p = vec(LMK[key]); h = LMK.get(hdg_key or key + '_h', 0.0); fw = np.array([math.cos(h), math.sin(h), 0]); sd = np.array([math.sin(h), -math.cos(h), 0])
        return p + sd * off_side + fw * off_fwd + UPZ * up
    # modes: ('chase', back, up, side, lens) or ('fix', pos, lens) or ('fixlook', pos, look, lens)
    zz = LMK['zigzag']; zmid = np.mean([tuple(s_['p']) for s_ in zz], axis=0); zz_end = vec(zz[-1]['p'])
    tw = LMK['tower']; hx = LMK['helix']; hmid = np.array([tw[0], tw[1], (hx[0]['p'].z + hx[-1]['p'].z) / 2])
    pl_top, pl_bot, PL = LMK['plinko']; pl_mid = (vec(pl_top) + vec(pl_bot)) / 2
    cs = LMK['corkscrew']; cmid = np.mean([tuple(s_['p']) for s_ in cs], axis=0)
    v1 = vec(LMK['vortex1']); v2 = vec(LMK['vortex2'])
    t_zig = lead_t('zigzag'); t_d1 = lead_t('drop1'); t_v1 = lead_t('vortex1'); t_hp = lead_t('halfpipe'); t_cs = lead_t('corkscrew')
    t_pl = lead_t('plinko'); t_ln = lead_t('lanes'); t_d2 = lead_t('drop2'); t_hx = lead_t('helix'); t_tv2 = lead_t('to_vortex2'); t_v2 = lead_t('vortex2')
    t_ro = lead_t('rollers'); t_d3 = lead_t('drop3'); t_fi = lead_t('finish')
    hp_c = vec(LMK['halfpipe'][len(LMK['halfpipe']) // 2]['p'])
    def away(p, c, d, up):            # a point d further from c than p, raised
        v = p - c; v[2] = 0; v /= max(np.linalg.norm(v), 1e-4); return p + v * d + UPZ * up
    CAM_PLAN = [
        (0.0, ('fix', vec(LMK['bumps'][int(len(LMK['bumps']) * 0.75)]['p']) + vec(LMK['bumps'][0]['side']) * 0.95 + UPZ * 0.85, 34)),     # they roll down at us
        (3.2, ('chase', 1.1, 0.75, -0.3, 30)),
        (t_zig + 2.0, ('fix', zmid + np.array([-0.6, -2.6, 2.2]), 30)),                                  # the zigzag laid out below
        (t_zig + 13.0, ('chase', 1.1, 0.8, 0.3, 30)),
        (t_d1 - 2.0, ('fix', landmark_side('kick1', 2.3, 0.7, 0.55), 32)),                               # jump 1, side on
        (t_v1 - 0.2, ('fix', v1 + np.array([-1.9, -2.4, 2.5]), 28)),                                      # down into vortex 1
        (t_hp + 0.8, ('chase', 1.1, 0.9, 0.0, 30)),
        (t_cs - 0.4, ('fix', away(cmid, hp_c, 0.0, 0) + np.array([0, 0, 0.6]) + (np.array([2.3, -2.3, 0.0])), 30)),  # the glass corkscrew
        (t_pl - 0.5, ('fix', pl_mid + np.array(tuple(PL[6])) * 2.8 + np.array(tuple(PL[4])) * 0.5, 30)),  # plinko face-on
        (t_ln + 1.2, ('chase', 1.1, 0.85, 0.2, 30)),
        (t_d2 - 1.6, ('fix', landmark_side('kick2', -2.2, 1.0, 0.45), 32)),                               # the big jump
        (t_hx + 2.5, ('chase', 1.0, 0.55, 0.3, 30)),
        (t_hx + 12.0, ('fixlook', hmid + np.array([0.0, -8.5, 2.2]), hmid + np.array([0, 0, -0.4]), 34)),  # the tower, wide (watch them spiral)
        (t_tv2 - 0.3, ('chase', 1.1, 0.8, 0.0, 30)),
        (t_v2 + 0.2, ('fix', v2 + np.array([2.2, -2.2, 2.3]), 30)),                                       # mega vortex
        (t_ro + 0.8, ('chase', 1.1, 0.8, -0.2, 30)),
        (t_d3 - 1.0, ('fix', landmark_side('kick3', -2.2, 1.3, 0.35), 32)),                               # final jump through the ring
        (t_fi + 1.4, ('fix', vec(LMK['finish_line']['p']) + vec(LMK['finish_line']['side']) * -1.5 + vec(LMK['finish_line']['T']) * 0.7 + UPZ * 1.1, 32)),
    ]
    fe_ = LMK['finish'][-1]; pile_cam = pile - vec(fe_['T']) * 1.1 + vec(fe_['side']) * -0.9 + UPZ * 0.55
    CAM_PLAN.append((T_LAST + 0.6, ('fixlook', pile_cam, pile, 36)))
    BLEND = 1.3
    def cam_of(mode, i):
        k = mode[0]; f_ = FOC[i]
        if k == 'chase':
            _, back, up, side, lens = mode; return f_ - HD[i] * back + UPZ * up + SDV[i] * side, f_ + HD[i] * 0.6 + UPZ * 0.02, lens
        if k == 'fix': return mode[1], f_, mode[2]
        return mode[1], mode[2] + (f_ - mode[2]) * 0.35, mode[3]
    CPOS = np.zeros((NFR, 3)); CTGT = np.zeros((NFR, 3)); CLEN = np.zeros(NFR)
    for i in range(NFR):
        t = TT[i]; j = max(k for k in range(len(CAM_PLAN)) if CAM_PLAN[k][0] <= t)
        p1, q1, l1 = cam_of(CAM_PLAN[j][1], i)
        if j > 0 and t - CAM_PLAN[j][0] < BLEND:
            p0, q0, l0 = cam_of(CAM_PLAN[j - 1][1], i); u = sm((t - CAM_PLAN[j][0]) / BLEND)
            p1 = p0 + (p1 - p0) * u; q1 = q0 + (q1 - q0) * u; l1 = l0 + (l1 - l0) * u
        CPOS[i], CTGT[i], CLEN[i] = p1, q1, l1
    CPOS = gsmooth(CPOS, 0.25); CTGT = gsmooth(CTGT, 0.18)
    # keep a clear line from the marbles to the lens: lift the camera when the track, a sign or a funnel is in the way
    DG = bpy.context.evaluated_depsgraph_get(); SKIP = ('marble', 'core', 'posts', 'rim', 'led', 'mlight')
    def blocked(src, dst):
        d = Vector(tuple(dst - src)); L_ = d.length; d.normalize(); o = Vector(tuple(src)) + d * 0.12; L_ -= 0.12
        for _ in range(12):
            hit, loc, nrm, idx, ob, mw = S.ray_cast(DG, o, d, distance=L_)
            if not hit: return False
            if not ob.name.startswith(SKIP): return True
            step = (loc - o).length + 0.01; o = loc + d * 0.01; L_ -= step
            if L_ <= 0: return False
        return False
    LIFT = np.zeros(NFR)
    for i in range(0, NFR, 2):
        for r_ in np.arange(0, 2.61, 0.15):
            if not blocked(CTGT[i] * 0.3 + FOC[i] * 0.7, CPOS[i] + UPZ * r_): LIFT[i] = r_; break
        else: LIFT[i] = 2.6
        if i + 1 < NFR: LIFT[i + 1] = LIFT[i]
    hw_ = int(FPS * 0.6); LIFT = np.array([LIFT[max(0, i - hw_):i + hw_ + 1].max() for i in range(NFR)]); LIFT = gsmooth(LIFT[:, None], 0.35)[:, 0]
    LIFT_RAW = LIFT
    CPOS = CPOS + UPZ[None, :] * LIFT[:, None]
    print('maxed at', [round(i / FPS, 1) for i in range(0, NFR, 15) if LIFT[i] > 2.5]); print('camera lifted on', int((LIFT > 0.05).sum()), 'of', NFR, 'frames, max', round(float(LIFT.max()), 2))
    CLEN = gsmooth(CLEN[:, None], 0.3)[:, 0]
else:
    NFR = 0
# ================================================================ per frame
def frame(f):
    t = f / FPS
    # keys at the frame before, this one and the next so motion blur is right both ways
    for i, mo in enumerate(MARB):
        if mo.animation_data: mo.animation_data_clear()
        for k in (-1, 0, 1):
            g = clamp(f + k, -PRE, NFR - 1) + PRE
            mo.location = tuple(SPOS[g, i]); mo.rotation_quaternion = tuple(SQUA[g, i])
            mo.keyframe_insert('location', frame=k); mo.keyframe_insert('rotation_quaternion', frame=k)
    S.frame_set(0)
    cp = Vector(tuple(CPOS[f])) + shake(t, 0.006, 2.0, 1.3); ct = Vector(tuple(CTGT[f]))
    look(cp, ct, float(CLEN[f]), fstop=16.0)
# ================================================================ render / sim / preview
if __name__ == '__main__':
    if a.sim:
        run_sim(a.sim); sys.exit(0)
    if a.blend: bpy.ops.wm.save_as_mainfile(filepath=a.blend)
    os.makedirs(a.out, exist_ok=True)
    N_ = NFR
    if a.only: todo = [int(x) for x in a.only.split(',')]; names = todo
    elif REDO:
        job = a.f0 // REDO['ch']; todo = REDO['frames'][job::REDO['jobs']]; names = [a.f0 + i for i in range(len(todo))]
    elif STRIDE:
        J = STRIDE['jobs']; job = a.f0 // STRIDE['ch']; todo = list(range(job, N_, J)); names = [a.f0 + i for i in range(len(todo))]
    else: todo = list(range(a.f0, min(a.f1, N_))); names = todo
    for f, nm in zip(todo, names):
        frame(f); S.render.filepath = os.path.join(a.out, f'f_{nm:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', f, '->', nm, flush=True)
