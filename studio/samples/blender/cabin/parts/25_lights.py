# ---- light: the sun (outside and through the windows), cabin ceiling lights, a soft fill; the sky is a gradient on the view direction
SUNL = bpy.data.lights.new('sun', 'SUN'); SUNL.energy = 4.0; SUNL.color = (1.0, 0.96, 0.9); SUNL.angle = R(1.5)
SUN_O = bpy.data.objects.new('sun', SUNL); S.collection.objects.link(SUN_O); SUN_O.rotation_mode = 'QUATERNION'
def sun_from(d, energy=4.0, col=(1.0, 0.96, 0.9)):
    """d: direction TO the sun"""
    SUN_O.rotation_quaternion = (-Vector(d)).to_track_quat('-Z', 'Y'); SUNL.energy = energy; SUNL.color = col
sun_from((0.75, -0.25, 0.45))
CAB_L = []
for side in (1, -1):
    for k in range(5):
        CAB_L.append(light_at(f'ceil_{side}_{k}', 'AREA', (side * 0.55, -5.0 + 2.5 * k, 2.12), (side * 0.9, -5.0 + 2.5 * k, 0.0), 40, (1.0, 0.92, 0.8), 0.6))
FILLC = light_at('cabin_fill', 'AREA', (0.0, -3.0, 1.6), (1.3, 0.0, 1.0), 25, (0.85, 0.9, 1.0), 1.5); CAB_L.append(FILLC)
KEYC = light_at('cabin_key', 'AREA', (0.2, MY - 1.2, 1.5), (MYSEAT_X, MY, 1.1), 18, (1.0, 0.95, 0.9), 0.5); CAB_L.append(KEYC)
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; wnt = W_.node_tree
WBG = wnt.nodes['Background']; WBG.inputs['Strength'].default_value = 1.0
_tc = wnt.nodes.new('ShaderNodeTexCoord'); _sx = wnt.nodes.new('ShaderNodeSeparateXYZ'); wnt.links.new(_tc.outputs['Generated'], _sx.inputs['Vector'])
SKYR = wnt.nodes.new('ShaderNodeValToRGB'); wnt.links.new(_sx.outputs['Z'], SKYR.inputs['Fac'])
_el = SKYR.color_ramp.elements; _el[0].position = 0.0; _el[0].color = (0.75, 0.8, 0.88, 1); _el[1].position = 0.6; _el[1].color = (0.08, 0.22, 0.6, 1)
_e2 = _el.new(0.5); _e2.color = (0.72, 0.82, 0.95, 1); _e3 = _el.new(0.53); _e3.color = (0.42, 0.6, 0.9, 1)
# world Generated z runs -1..1 -> map to 0..1
_mr = wnt.nodes.new('ShaderNodeMapRange'); _mr.inputs['From Min'].default_value = -1.0; _mr.inputs['From Max'].default_value = 1.0
wnt.links.new(_sx.outputs['Z'], _mr.inputs['Value']); wnt.links.new(_mr.outputs['Result'], SKYR.inputs['Fac'])
WMIX = wnt.nodes.new('ShaderNodeMix'); WMIX.data_type = 'RGBA'; WMIX.inputs['Factor'].default_value = 0.0; WMIX.inputs['B'].default_value = (0.004, 0.012, 0.035, 1)
wnt.links.new(SKYR.outputs['Color'], WMIX.inputs['A']); wnt.links.new(WMIX.outputs['Result'], WBG.inputs['Color'])
def world(kind):
    """'sky' or 'xray' (dark blue)"""
    WMIX.inputs['Factor'].default_value = 1.0 if kind == 'xray' else 0.0
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.02; CAM.data.clip_end = 30000
XL = light_at('xray_key', 'AREA', (MYSEAT_X - 1.0, MY - 1.4, 1.6), (MYSEAT_X, MY, 1.2), 40, (0.85, 0.9, 1.0), 1.5); XL.hide_render = True
XL2 = light_at('xray_rim', 'AREA', (MYSEAT_X + 0.6, MY + 0.8, 1.4), (MYSEAT_X, MY, 1.2), 30, (0.7, 0.8, 1.0), 1.2); XL2.hide_render = True
