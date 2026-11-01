import bpy, math, sys
from mathutils import Vector
import addon_utils; addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
bpy.ops.wm.open_mainfile(filepath='/home/claude/mh/human.blend')
S = bpy.context.scene
rig = bpy.data.objects['Human.rig']
# relax the T/A pose a bit: arms down
pb = rig.pose.bones
import os
AX = os.environ.get('AX', 'Z'); ANG = float(os.environ.get('ANG', '50'))
for side, s in (('L', 1), ('R', -1)):
    b = pb[f'upperarm01.{side}']; b.rotation_mode = 'XYZ'; e = [0, 0, 0]; e['XYZ'.index(AX)] = math.radians(ANG) * s * float(os.environ.get('SGN', '1')); b.rotation_euler = e
    b = pb[f'lowerarm01.{side}']; b.rotation_mode = 'XYZ'; b.rotation_euler = (math.radians(float(os.environ.get('ELB', '0'))), 0, 0)
bpy.context.view_layer.update()
print([b.name for b in pb][:40])
def light(kind, name, pos, aim, energy, color, size=0.5):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size
    if kind == 'SUN': L.angle = math.radians(4)
    o = bpy.data.objects.new(name, L); S.collection.objects.link(o); o.location = pos
    o.rotation_euler = (Vector(aim) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
head = rig.matrix_world @ pb['head'].head
print('head at', head)
light('AREA', 'key', head + Vector((-1.2, -1.6, 0.6)), head, 120, (1, 0.93, 0.85), 1.2)
light('AREA', 'fill', head + Vector((1.4, -1.2, 0.0)), head, 35, (0.9, 0.95, 1.0), 1.5)
light('AREA', 'rim', head + Vector((0.6, 1.5, 0.8)), head, 160, (1, 0.95, 0.9), 0.8)
W = bpy.data.worlds.new('w'); S.world = W; W.use_nodes = True; W.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.68, 0.6, 1); W.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
bpy.ops.mesh.primitive_plane_add(size=20); 
cd = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cd); S.collection.objects.link(cam); S.camera = cam; cd.sensor_fit = 'VERTICAL'
S.render.engine = 'CYCLES'; S.cycles.device = 'CPU'; S.cycles.samples = int(os.environ.get('SAMP', '48')); S.cycles.use_denoising = True
S.render.resolution_x, S.render.resolution_y = 540, 960
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Punchy'
SHOTS = os.environ.get('SHOTS', 'face,body').split(',')
for name, off, tgt, lens in (('face', Vector((0.3, -0.7, 0.03)), head + Vector((0, 0, 0.02)), 70), ('body', Vector((0.35, -1.75, -0.2)), head - Vector((0, 0, 0.32)), 45)):
    if name not in SHOTS: continue
    cam.location = head + off; cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
    S.render.filepath = f'/tmp/claude-0/nl/bl/mh_{name}.png'; bpy.ops.render.render(write_still=True)
