PEND = light_at('pendant_light', 'SPOT', (0.72, -0.2, 2.02), (0.6, -0.3, 0.0), 170, (1.0, 0.74, 0.46), 0.06); PEND.data.spot_size = R(125); PEND.data.spot_blend = 0.5
MOON = light_at('moon', 'AREA', (WX - 0.1, WIN_Y, WIN_Z), (-0.6, -0.5, 0.6), 110, (0.55, 0.7, 1.0), 0.8)
FILL = light_at('fill', 'AREA', (-1.6, -2.4, 2.0), (0, -0.3, 0.8), 30, (0.6, 0.7, 1.0), 2.5)
RIMK = light_at('rim', 'AREA', (-0.8, 1.3, 1.9), (0, -0.3, 0.9), 45, (1.0, 0.8, 0.6), 1.0)
ROOM_L = [PEND, MOON, FILL, RIMK]
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Color'].default_value = (0.01, 0.012, 0.02, 1); WBG.inputs['Strength'].default_value = 1.0
XL = light_at('xray_key', 'AREA', (-0.9, -1.4, 1.5), (0, -0.5, 0.9), 40, (0.85, 0.9, 1.0), 1.5); XL.hide_render = True
XL2 = light_at('xray_rim', 'AREA', (0.8, 0.5, 1.2), (0, -0.5, 0.9), 30, (0.7, 0.8, 1.0), 1.2); XL2.hide_render = True
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.005
