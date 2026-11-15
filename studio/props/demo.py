# Prop studio demo: a desk and an arm chair on a concrete floor, lit by a studio HDRI.  python3 studio/props/demo.py OUT.png
import sys, os, math
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import props_bpy as P
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene; S.render.engine = 'CYCLES'; S.cycles.device = 'CPU'; S.cycles.samples = 32; S.cycles.use_denoising = True
S.render.resolution_x, S.render.resolution_y = 540, 960
S.view_settings.view_transform = 'AgX'
P.hdri('ph:poly_haven_studio', 1.0, 40)
bpy.ops.mesh.primitive_plane_add(size=8); floor = bpy.context.object; floor.data.materials.append(P.material('acg:Concrete048', scale=3.0))
desk = P.place('ph:metal_office_desk', loc=(0, 0.3, 0), rot_deg=0, height=0.75)
chair = P.place('ph:ArmChair_01', loc=(-0.9, -0.8, 0), rot_deg=-35, height=0.95)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.location = (2.2, -3.6, 1.6); cam.data.lens = 32; cam.rotation_euler = (Vector((-0.3, 0, 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
S.render.filepath = sys.argv[-1]; bpy.ops.render.render(write_still=True)
print('desk size', tuple(round(x, 2) for x in desk['size']), 'chair size', tuple(round(x, 2) for x in chair['size']))
