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
sk = bpy.data.images.get('young_lightskinned_male_diffuse.png')
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
    nz = t.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900; nz.inputs['Detail'].default_value = 4
    bm_ = t.nodes.new('ShaderNodeBump'); bm_.inputs['Strength'].default_value = 0.08; bm_.inputs['Distance'].default_value = 0.0005
    t.links.new(nz.outputs['Fac'], bm_.inputs['Height']); t.links.new(bm_.outputs['Normal'], b.inputs['Normal'])
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
# hair: the model already wears MakeHuman's "short02" hair; darken it to a natural dark brown and soften its shine
hmat = bpy.data.materials.get('Human.short02')
if hmat:
    t = hmat.node_tree; hb = next(n for n in t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    src = hb.inputs['Base Color'].links[0].from_socket if hb.inputs['Base Color'].links else None
    mx = t.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    if src: t.links.new(src, mx.inputs[6])
    mx.inputs[7].default_value = (0.16, 0.10, 0.07, 1); t.links.new(mx.outputs[2], hb.inputs['Base Color'])
    hb.inputs['Roughness'].default_value = 0.6; hb.inputs['Specular IOR Level'].default_value = 0.3
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
