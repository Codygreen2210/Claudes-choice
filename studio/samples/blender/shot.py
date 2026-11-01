# Render a shot exported by web/export_shot.mjs in Blender (Cycles): better skin, cloth and light than the web renderer.
#   python3 shot.py SHOT.glb OUTDIR F0 F1 [--scale 1.0] [--samples 48]     -> OUTDIR/f_00000.png ... (frames F0..F1-1 of the shot)
import sys, os, math, time, argparse
import bpy, addon_utils
from mathutils import Vector

ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--samples', type=int, default=48); ap.add_argument('--blend', default=''); ap.add_argument('--closeup', action='store_true'); ap.add_argument('--hide', default='')
a = ap.parse_args()

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('cycles', default_set=False)
S = bpy.context.scene; S.render.fps = 30
bpy.ops.import_scene.gltf(filepath=a.glb)
three = lambda x, y, z: Vector((x, -z, y))                  # three.js (y up) -> Blender (z up), as the glTF importer does

# ---- the guy: volume-preserving skinning (the web page uses dual-quaternion skinning too)
for o in S.objects:
    for m in o.modifiers:
        if m.type == 'ARMATURE': m.use_deform_preserve_volume = True
    if o.type == 'MESH': 
        for p in o.data.polygons: p.use_smooth = True

# ---- materials
def bsdf(m):
    if not m.use_nodes: m.use_nodes = True
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
def noise_bump(m, scale, strength, dist=0.002):
    nt = m.node_tree; b = bsdf(m)
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = dist
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
for m in bpy.data.materials:
    b = bsdf(m)
    if not b: continue
    n = m.name
    if n.startswith('skin') or n == 'face_baked':           # skin: light scatters under it (subsurface), soft sheen, fine pores
        b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.18); b.inputs['Subsurface Scale'].default_value = 0.012
        b.inputs['Roughness'].default_value = 0.48; b.inputs['Specular IOR Level'].default_value = 0.45
        noise_bump(m, 900, 0.08, 0.0006)
    elif n == 'shirt':
        b.inputs['Roughness'].default_value = 0.9; b.inputs['Sheen Weight'].default_value = 0.6; b.inputs['Sheen Roughness'].default_value = 0.5
        noise_bump(m, 1400, 0.12, 0.0008)
    elif n == 'jeans':
        b.inputs['Roughness'].default_value = 0.85; b.inputs['Sheen Weight'].default_value = 0.3; noise_bump(m, 1800, 0.18, 0.0008)
    elif n == 'hair' or n == 'hairCards':
        b.inputs['Roughness'].default_value = 0.5 if n == 'hairCards' else 0.85; b.inputs['Coat Weight'].default_value = 0.0; b.inputs['Specular IOR Level'].default_value = 0.3
        if not b.inputs['Base Color'].is_linked: b.inputs['Base Color'].default_value = (0.12, 0.062, 0.03, 1)
        if n == 'hairCards':                                # the cards: their texture only cuts the strands out; colour is a flat warm brown
            for l in list(m.node_tree.links):
                if l.to_socket == b.inputs['Base Color']: m.node_tree.links.remove(l)
            b.inputs['Base Color'].default_value = (0.26, 0.14, 0.065, 1)
    else:
        b.inputs['Roughness'].default_value = max(0.3, b.inputs['Roughness'].default_value)

# ---- light: the room's sun through the window, the lamp, a soft fill from the camera side; warm bounce from the world
for o in [o for o in S.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o)
def light(kind, name, pos, aim, energy, color, size=0.5):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size; L.shape = 'DISK'
    if kind == 'SUN': L.angle = math.radians(4)
    o = bpy.data.objects.new(name, L); S.collection.objects.link(o); o.location = pos
    o.rotation_euler = (aim - pos).to_track_quat('-Z', 'Y').to_euler(); return o
light('SUN', 'sun', three(1.6, 3.4, 2.4), three(0, 0, 0), 3.2, (1.0, 0.9, 0.78))
light('AREA', 'window', three(1.6, 1.65, -3.0), three(0.2, 1.2, 0.4), 220, (0.85, 0.92, 1.0), 1.4)
light('AREA', 'lamp', three(2.2, 1.9, -2.4), three(0.2, 1.2, 0.4), 60, (1.0, 0.78, 0.52), 0.35)
light('AREA', 'fill', three(1.4, 1.7, 2.6), three(0.2, 1.4, 0.4), 40, (1.0, 0.95, 0.9), 1.6)
W = bpy.data.worlds.new('room'); S.world = W; W.use_nodes = True
bg = W.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.78, 0.72, 0.64, 1); bg.inputs['Strength'].default_value = 0.3

# ---- camera, render
cam = S.objects.get('shot_camera') or next(o for o in S.objects if o.type == 'CAMERA'); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'
S.render.engine = 'CYCLES'; S.cycles.device = 'CPU'; S.cycles.samples = a.samples; S.cycles.use_adaptive_sampling = True
S.cycles.use_denoising = True; S.cycles.denoiser = 'OPENIMAGEDENOISE'; S.cycles.max_bounces = 6; S.cycles.transparent_max_bounces = 128   # the hair cards stack many cut-out layers; too few bounces turns them black
S.render.resolution_x, S.render.resolution_y = int(1080 * a.scale), int(1920 * a.scale); S.render.resolution_percentage = 100
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.4
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Punchy'
S.render.image_settings.file_format = 'PNG'; S.render.image_settings.color_mode = 'RGB'
act = bpy.data.actions[0] if bpy.data.actions else None
print('action range', act.frame_range[:] if act else None, flush=True)
if a.blend: bpy.ops.wm.save_as_mainfile(filepath=a.blend)
for o in S.objects:                                        # debug: hide objects whose material name is listed
    if a.hide and o.type == 'MESH' and o.data.materials and o.data.materials[0] and o.data.materials[0].name in a.hide.split(','): o.hide_render = True
if a.closeup:                                              # debug: a camera on his face (same frame) to judge skin, hair, eyes
    arm = next(o for o in S.objects if o.type == 'ARMATURE'); S.frame_set(a.f0)
    hb = arm.pose.bones.get('head'); hp = arm.matrix_world @ hb.head
    cd = bpy.data.cameras.new('close'); cd.lens = 70; co = bpy.data.objects.new('close', cd); S.collection.objects.link(co)
    tgt = hp + Vector((0, 0, 0.08)); fw = (cam.matrix_world.translation - tgt); fw.z = 0; fw.normalize()
    co.location = tgt + fw * 0.55 + Vector((0.12, 0, 0.03)); co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler(); S.camera = co
os.makedirs(a.out, exist_ok=True)
for f in range(a.f0, a.f1):
    S.frame_set(f); S.render.filepath = os.path.join(a.out, 'f_%05d.png' % f); t = time.time()
    bpy.ops.render.render(write_still=True); print('frame', f, '%.1f s' % (time.time() - t), flush=True)
