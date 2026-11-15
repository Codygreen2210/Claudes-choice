# Quality test (owner, 2026-11-14): how close can we get to Zack D Films' look? A die tumbles across a varnished wooden table
# and settles; one camera, close and low, slow drift then a rest. Real-scale die (16 mm), CC0 Poly Haven wood and studio HDRI,
# a warm window sun for crisp shadows, shallow depth of field, AgX colour.
#   python3 qtest.py OUTDIR F0 F1 [--samples 96] [--scale 1.0] [--only f,f]       assets in ./assets (see farm.sh)
import sys, os, math, argparse
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, Quaternion
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=96); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def asset(*p):
    for root in (os.path.join(HERE, 'assets'), '/root/vt/assets'):
        q = os.path.join(root, *p)
        if os.path.exists(q): return q
    raise FileNotFoundError(os.path.join(*p))
FPS = 30; DUR = 5.0; N = int(DUR * FPS)
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene; S.render.engine = 'CYCLES'; S.render.fps = FPS
S.render.resolution_x = int(1080 * a.scale); S.render.resolution_y = int(1920 * a.scale); S.render.resolution_percentage = 100
C = S.cycles; C.device = 'CPU'; C.samples = a.samples; C.use_denoising = True; C.denoiser = 'OPENIMAGEDENOISE'
C.use_adaptive_sampling = True; C.adaptive_threshold = 0.015; C.max_bounces = 8; C.caustics_reflective = False; C.caustics_refractive = False
try: S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
S.view_settings.exposure = 0.0
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5

# ---- world: the studio HDRI (soft light + reflections), turned so the bright softbox sits behind-left
W = bpy.data.worlds.new('w'); S.world = W; W.use_nodes = True; nt = W.node_tree; bg = nt.nodes['Background']
env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(asset('brown_photostudio_02', 'brown_photostudio_02_2k.hdr'))
mp = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp.inputs['Rotation'].default_value = (0, 0, math.radians(120))
nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], env.inputs['Vector']); nt.links.new(env.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 0.8

# ---- the table: Poly Haven oak veneer, warmed up and varnished (a clear coat gives the long window highlight)
def img(path, non_color=False):
    im = bpy.data.images.load(asset(*path)); im.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'; return im
def wood_mat():
    m = bpy.data.materials.new('table'); m.use_nodes = True; t = m.node_tree; b = t.nodes['Principled BSDF']
    tc_ = t.nodes.new('ShaderNodeTexCoord'); mp_ = t.nodes.new('ShaderNodeMapping'); mp_.inputs['Scale'].default_value = (2.2, 2.2, 2.2)
    mp_.inputs['Rotation'].default_value = (0, 0, math.radians(90)); t.links.new(tc_.outputs['UV'], mp_.inputs['Vector'])
    def tex(p, nc=False):
        n = t.nodes.new('ShaderNodeTexImage'); n.image = img(p, nc); t.links.new(mp_.outputs[0], n.inputs['Vector']); return n
    d = tex(('oak_veneer_01', 'oak_veneer_01_diff_2k.jpg'))
    warm = t.nodes.new('ShaderNodeMix'); warm.data_type = 'RGBA'; warm.blend_type = 'MULTIPLY'; warm.inputs['Factor'].default_value = 1.0
    t.links.new(d.outputs['Color'], warm.inputs[6]); warm.inputs[7].default_value = (1.0, 0.70, 0.45, 1)
    t.links.new(warm.outputs[2], b.inputs['Base Color'])
    r = tex(('oak_veneer_01', 'oak_veneer_01_rough_2k.jpg'), True); rr = t.nodes.new('ShaderNodeMapRange')
    rr.inputs['To Min'].default_value = 0.25; rr.inputs['To Max'].default_value = 0.55; t.links.new(r.outputs['Color'], rr.inputs['Value']); t.links.new(rr.outputs['Result'], b.inputs['Roughness'])
    nm = tex(('oak_veneer_01', 'oak_veneer_01_nor_gl_2k.jpg'), True); nn = t.nodes.new('ShaderNodeNormalMap'); nn.inputs['Strength'].default_value = 0.6
    t.links.new(nm.outputs['Color'], nn.inputs['Color']); t.links.new(nn.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Coat Weight'].default_value = 0.45; b.inputs['Coat Roughness'].default_value = 0.14
    return m
bpy.ops.mesh.primitive_plane_add(size=1.2, location=(0, 0, 0)); TABLE = bpy.context.object; TABLE.data.materials.append(wood_mat())
for p in TABLE.data.polygons: p.use_smooth = True

# ---- light: warm low sun through a window (crisp die shadows) plus the HDRI fill
SUN = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(SUN)
SUN.data.energy = 3.2; SUN.data.color = (1.0, 0.86, 0.68); SUN.data.angle = math.radians(2.5)
SUN.rotation_euler = Euler((math.radians(58), 0, math.radians(-35)), 'XYZ')

# ---- the die: 16 mm, rounded edges, drilled pips (boolean), white plastic with a little subsurface and a clear coat
SZ = 0.016
def die(name):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=SZ); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    bv = o.modifiers.new('bevel', 'BEVEL'); bv.width = SZ * 0.14; bv.segments = 6; bv.limit_method = 'NONE'
    pl = bpy.data.materials.new(name + '_pl'); pl.use_nodes = True; b = pl.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.92, 0.91, 0.88, 1); b.inputs['Roughness'].default_value = 0.32
    b.inputs['Subsurface Weight'].default_value = 0.25; b.inputs['Subsurface Radius'].default_value = (0.002, 0.0018, 0.0015); b.inputs['Subsurface Scale'].default_value = 1.0
    b.inputs['Coat Weight'].default_value = 0.5; b.inputs['Coat Roughness'].default_value = 0.08
    pip = bpy.data.materials.new(name + '_pip'); pip.use_nodes = True; bp = pip.node_tree.nodes['Principled BSDF']
    bp.inputs['Base Color'].default_value = (0.012, 0.012, 0.014, 1); bp.inputs['Roughness'].default_value = 0.35
    me.materials.append(pl); me.materials.append(pip)
    # pip layout per face (u, v in -1..1 of the face): 1 opposite 6, 2 opposite 5, 3 opposite 4
    L = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
         5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}
    faces = {6: (Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))), 1: (Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((0, 1, 0))),
             2: (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))), 5: (Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))),
             3: (Vector((0, 1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))), 4: (Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)))}
    bm = bmesh.new(); R = SZ * 0.085; off = SZ * 0.26
    for n_, (nv, uv, vv) in faces.items():
        for (u, v) in L[n_]:
            c = nv * (SZ / 2 + R * 0.45) + uv * (u * off) + vv * (v * off)
            res = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=R, matrix=Matrix.Translation(c))
    cm = bpy.data.meshes.new(name + '_cut'); bm.to_mesh(cm); bm.free(); cut = bpy.data.objects.new(name + '_cut', cm); S.collection.objects.link(cut)
    cm.materials.append(pip); cut.parent = o; cut.hide_render = True; cut.hide_viewport = True
    bo = o.modifiers.new('pips', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.solver = 'EXACT'; bo.object = cut
    try: bo.material_mode = 'TRANSFER'
    except Exception: pass
    o.modifiers.new('wn', 'WEIGHTED_NORMAL')
    for p in me.polygons: p.use_smooth = True
    return o
D1 = die('die'); D2 = die('die2')
D2.location = (-0.055, 0.075, SZ / 2); D2.rotation_euler = (0, 0, math.radians(28))     # a second die resting further back (out of focus)

# ---- the tumble: the die arrives already rolling (motion on frame one), hops twice, rolls edge over edge and settles on 6
def ease_out(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
T_SET = 2.6; ROLLS = 5                         # five quarter-turns while it travels, then rest
HEAD = math.radians(-24)                        # travel direction (toward the camera, a little across)
def die_at(t):
    k = ease_out(t / T_SET); ang = ROLLS * (math.pi / 2) * k            # roll angle about the axis across the path
    dist = ang * SZ / 2 * 1.12
    hop = 0.0
    for t0, h, d in ((0.0, 0.020, 0.42), (0.42, 0.007, 0.30)):          # two hops at the start
        if t0 <= t < t0 + d: u = (t - t0) / d; hop = h * 4 * u * (1 - u)
    ph = ang % (math.pi / 2); lift = SZ / 2 * (math.cos(ph) + math.sin(ph) - 1)  # centre rises as it goes over an edge
    d_ = Vector((math.sin(HEAD), -math.cos(HEAD), 0)); start = Vector((0.03, 0.05, 0))
    pos = start + d_ * dist; pos.z = SZ / 2 + lift + hop
    axis = Vector((math.cos(HEAD), math.sin(HEAD), 0))                  # roll axis, across the path
    # roll about an axis that lines up with the die's own face axes (yaw = travel heading) so every quarter turn lands flat
    q = Quaternion(axis, -ang) @ Quaternion((0, 0, 1), HEAD) @ Quaternion((1, 0, 0), math.radians(90))
    return pos, q
# ---- camera: low and close, 70 mm, f/2.2, slow drift with the die then a gentle push while it rests
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.lens = 70; CAM.data.sensor_width = 36; CAM.data.clip_start = 0.005
CAM.data.dof.use_dof = True; CAM.data.dof.aperture_fstop = 2.2
FOC = bpy.data.objects.new('focus', None); S.collection.objects.link(FOC); CAM.data.dof.focus_object = FOC
def cam_at(t):
    p, _ = die_at(t); u = ease_out((t - T_SET) / (DUR - T_SET))
    tgt = Vector((p.x, p.y, SZ * 0.45)); base = tgt + Vector((0.035, -0.20, 0.075)) * (1 - 0.18 * u)
    base += Vector((0.006 * math.sin(0.7 * t), 0, 0.002 * math.sin(0.9 * t)))
    return base, tgt
def frame(f):
    t = f / FPS
    p, q = die_at(t); D1.location = p; D1.rotation_mode = 'QUATERNION'; D1.rotation_quaternion = q
    D1.keyframe_insert('location', frame=f); D1.keyframe_insert('rotation_quaternion', frame=f)
    cp, ct = cam_at(t); CAM.location = cp; CAM.rotation_mode = 'QUATERNION'; CAM.rotation_quaternion = (ct - cp).to_track_quat('-Z', 'Y')
    CAM.keyframe_insert('location', frame=f); CAM.keyframe_insert('rotation_quaternion', frame=f); FOC.location = p; FOC.keyframe_insert('location', frame=f)
for f in range(-1, N + 2): frame(f)                 # key everything so motion blur sees the moves
if __name__ == '__main__':
    os.makedirs(a.out, exist_ok=True)
    todo = [int(x) for x in a.only.split(',')] if a.only else list(range(a.f0, min(a.f1, N)))
    for f in todo:
        S.frame_set(f); S.render.filepath = os.path.join(a.out, f'f_{f:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', f, flush=True)
