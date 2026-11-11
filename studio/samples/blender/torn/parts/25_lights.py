SUNL = bpy.data.lights.new('storm_sun', 'SUN'); SUNL.energy = 1.6; SUNL.color = (0.75, 0.85, 0.8); SUNL.angle = R(25)
SUN_O = bpy.data.objects.new('storm_sun', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_euler = (R(50), R(-20), R(200))
RIMO = light_at('rim', 'AREA', (-14, 26, 9), (0, 0, 3), 4000, (0.8, 0.9, 1.0), 6.0)
FLASH = light_at('lightning', 'AREA', (60, 120, 300), (0, 0, 0), 0.0, (0.75, 0.82, 1.0), 40.0)
KEYF = light_at('front_key', 'AREA', (-2.0, -13.0, 4.0), (2.6, -4.6, 1.4), 900, (0.85, 0.92, 1.0), 4.0)
OUT_L = [SUN_O, RIMO, FLASH, KEYF]
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.04, 0.05, 0.045, 1); WBG.inputs['Strength'].default_value = 1.0
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.05; CAM.data.clip_end = 3000
S.view_settings.view_transform = 'AgX'
