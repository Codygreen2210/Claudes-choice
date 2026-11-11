# ================================================================ OUTSIDE: the jet (nose -y), the cloud deck far below, and the roadside
PX = V3(400.0, 0.0, 0.0)                                                 # the jet's middle (same height as the cabin; the deck is under both)
CLOUD_Z = -420.0
JET = empty('jet', loc=PX); JET.rotation_mode = 'XYZ'
PAINT_M = mat('paint', (0.9, 0.91, 0.93), 0.25, coat=0.6)
BELLY_M = mat('belly', (0.62, 0.64, 0.68), 0.35, coat=0.3)
TAIL_M = mat('tail_paint', (0.05, 0.14, 0.32), 0.3, coat=0.6)
WINGM = mat('wing', (0.7, 0.72, 0.75), 0.35, metal=0.3)
NAC_M = mat('nacelle', (0.78, 0.79, 0.82), 0.3, metal=0.4, coat=0.4)
WINX_M = mat('ext_window', (0.03, 0.04, 0.06), 0.08, coat=1.0)
JETP = []
_fp = [(0.05, -19.0), (0.3, -18.6), (0.8, -17.2), (1.35, -15.2), (1.75, -13.0), (1.95, -10.5), (1.97, -6), (1.97, 6), (1.97, 13.0), (1.88, 15.2),
       (1.62, 16.8), (1.25, 17.9), (0.75, 18.7), (0.25, 19.15), (0.02, 19.3)]
FUS = lathe('fuselage', _fp, 64, PAINT_M, parent=JET); FUS.rotation_euler = (R(90), 0, 0); JETP.append(FUS)
for side in (1, -1):
    for k in range(30):
        y = -12.5 + k * 0.83
        if abs(y - 2.5) < 0.6: continue
        JETP.append(box(f'xwin_{side}_{k}', (0.05, 0.24, 0.34), (side * 1.99, y, 0.42), WINX_M, bv=0.015, parent=JET))
    for k in range(3):
        JETP.append(box(f'cockpit_{side}_{k}', (0.06, 0.55, 0.42), (side * (1.45 - 0.22 * k), -16.6 - 0.55 * k, 0.75 + 0.05 * k), WINX_M, bv=0.05,
                        rot=(0, side * R(-25 - 12 * k), side * R(18 + 10 * k)), parent=JET))
def wing(name, root, tip, m, parent):
    """root/tip: (x, y_le, y_te, z, thick)"""
    vs = []
    for x, yl, yt, z, th in (root, tip):
        c = yt - yl; vs += [(x, yl, z), (x, yl + 0.3 * c, z + th / 2), (x, yt, z), (x, yl + 0.3 * c, z - th / 2)]
    fs = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 3, 2, 1), (4, 5, 6, 7)]
    o = mesh(name, vs, fs, m, parent, smooth_=False); md = o.modifiers.new('ws', 'SUBSURF'); md.levels = md.render_levels = 1; return o
for side in (1, -1):
    JETP.append(wing(f'wing_{side}', (side * 1.5, -3.2, 4.2, -1.0, 0.55), (side * 17.5, 6.6, 8.1, 0.45, 0.14), WINGM, JET))
    JETP.append(wing(f'stab_{side}', (side * 0.6, 14.2, 17.6, 0.5, 0.3), (side * 6.6, 17.6, 18.6, 1.0, 0.08), WINGM, JET))
    nac = lathe(f'nacelle_{side}', [(0.82, -2.2), (1.02, -1.9), (1.05, -0.5), (0.95, 1.2), (0.55, 2.0), (0.3, 2.3)], 48, NAC_M, parent=JET)
    nac.rotation_euler = (R(90), 0, 0); nac.location = (side * 5.6, -4.6, -2.0); JETP.append(nac)
    fan = prim('cylinder', f'fan_{side}', mat(f'fan_{side}', (0.08, 0.08, 0.09), 0.3, metal=0.8), parent=JET, loc=(side * 5.6, -2.55, -2.0), rot=(R(90), 0, 0), radius=0.8, depth=0.05, vertices=32)
    JETP.append(fan)
    JETP.append(box(f'pylon_{side}', (0.25, 3.4, 0.8), (side * 5.6, -3.2, -1.35), WINGM, bv=0.08, parent=JET))
def vfin(name, root, tip, m, parent):
    """an upright surface: root/tip = (y_le, y_te, z, thick), thickness along x"""
    vs = []
    for yl, yt, z, th in (root, tip):
        c = yt - yl; vs += [(0, yl, z), (th / 2, yl + 0.3 * c, z), (0, yt, z), (-th / 2, yl + 0.3 * c, z)]
    fs = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 3, 2, 1), (4, 5, 6, 7)]
    o = mesh(name, vs, fs, m, parent, smooth_=False); md = o.modifiers.new('ws', 'SUBSURF'); md.levels = md.render_levels = 1; return o
fin = vfin('fin', (11.8, 18.2, 1.7, 0.4), (16.6, 18.7, 8.6, 0.12), TAIL_M, JET); JETP.append(fin)
# the door plug (the -x side, aft of the wing): a panel with a seam, a dark hole behind it once it goes
PLUGE_Y, PLUGE_Z = 6.3, 0.15
PLUGE = empty('plug_ext', parent=JET, loc=(-2.0, PLUGE_Y, PLUGE_Z)); PLUGE.rotation_mode = 'XYZ'
PLUGP = slab_x('plug_panel', rrect(0.7, 1.3, 0.16), -0.015, 0.015, PAINT_M, 0, 0, parent=PLUGE); JETP.append(PLUGP)
PLUGW = box('plug_win', (0.03, 0.24, 0.34), (-0.012, 0.0, 0.27), WINX_M, bv=0.015, parent=PLUGE); JETP.append(PLUGW)
SEAM = ring_x('plug_seam', [(u * 1.06, v * 1.04) for u, v in rrect(0.7, 1.3, 0.16)], rrect(0.7, 1.3, 0.16), -2.025, -1.99, DARK_M, PLUGE_Y, PLUGE_Z, parent=JET); JETP.append(SEAM)
HOLE_M = emis('hole_glow', (0.35, 0.28, 0.22), 0.35)
HOLE = slab_x('plug_hole', rrect(0.68, 1.28, 0.16), -2.016, -2.01, HOLE_M, PLUGE_Y, PLUGE_Z, parent=JET); HOLE.hide_render = True; JETP.append(HOLE)
# ---- the cloud deck: a big lumpy sheet, sunlit tops
CLOUD_M = mat('cloud', (0.95, 0.96, 1.0), 0.9, sheen=0.5)
_b = CLOUD_M.node_tree.nodes['Principled BSDF']; _b.inputs['Subsurface Weight'].default_value = 0.6; _b.inputs['Subsurface Radius'].default_value = (30.0, 30.0, 34.0)
noisy(CLOUD_M, 0.004, 0.18, 0.05, coord='Object')
bpy.ops.mesh.primitive_grid_add(x_subdivisions=300, y_subdivisions=300, size=24000, location=(0, 0, CLOUD_Z)); CLOUDS = bpy.context.active_object; CLOUDS.name = 'clouds'
CLOUDS.data.materials.append(CLOUD_M)
for p_ in CLOUDS.data.polygons: p_.use_smooth = True
_tx = bpy.data.textures.new('cloud_tex', 'CLOUDS'); _tx.noise_scale = 900.0; _tx.noise_depth = 4
_dm = CLOUDS.modifiers.new('puff', 'DISPLACE'); _dm.texture = _tx; _dm.strength = 160.0; _dm.mid_level = 0.55; _dm.texture_coords = 'GLOBAL'
_tx2 = bpy.data.textures.new('cloud_tex2', 'CLOUDS'); _tx2.noise_scale = 160.0; _tx2.noise_depth = 2
_dm2 = CLOUDS.modifiers.new('puff2', 'DISPLACE'); _dm2.texture = _tx2; _dm2.strength = 40.0; _dm2.mid_level = 0.5; _dm2.texture_coords = 'GLOBAL'
# ---- the roadside where a phone was found (far off, under the deck: the deck is hidden there)
GX = V3(-3000.0, 0.0, -1500.0)
GRASS_M = noisy(mat('grass', (0.13, 0.22, 0.06), 0.85, sheen=0.4), 60.0, 0.5, 0.1)
GROUND = box('roadside', (80, 80, 0.2), GX + V3(0, 0, -0.1), GRASS_M)
ROAD_M = noisy(mat('asphalt', (0.11, 0.105, 0.1), 0.92), 260.0, 0.45, 0.05)
ROAD = box('road', (6.5, 80, 0.06), GX + V3(1.6 + 3.25, 0, 0.0), ROAD_M)
LINE = box('road_line', (0.12, 80, 0.07), GX + V3(1.6 + 3.25, 0, 0.0), mat('yellow_line', (0.85, 0.65, 0.1), 0.6))
EDGE = box('road_edge', (0.1, 80, 0.07), GX + V3(1.75, 0, 0.0), mat('white_line', (0.8, 0.8, 0.78), 0.6))
GRAVEL = box('shoulder', (0.6, 80, 0.04), GX + V3(1.3, 0, 0.0), noisy(mat('gravel', (0.42, 0.39, 0.34), 0.95), 300.0, 0.6, 0.05))
# grass blades: hair on a patch around the phone
_gp = box('grass_patch', (5.0, 7.0, 0.02), GX + V3(-1.5, 0, 0.0), GRASS_M)
BLADE_M = GRASS_M
PHONE_M = mat('phone_body', (0.02, 0.02, 0.025), 0.15, coat=1.0)
SCREEN_M = bpy.data.materials.new('phone_screen'); SCREEN_M.use_nodes = True
_nt = SCREEN_M.node_tree; _nt.nodes.remove(_nt.nodes['Principled BSDF']); _e = _nt.nodes.new('ShaderNodeEmission'); _g = _nt.nodes.new('ShaderNodeTexGradient')
_tc = _nt.nodes.new('ShaderNodeTexCoord'); _cr = _nt.nodes.new('ShaderNodeValToRGB'); _nt.links.new(_tc.outputs['Generated'], _g.inputs['Vector'])
_cr.color_ramp.elements[0].color = (0.1, 0.25, 0.9, 1); _cr.color_ramp.elements[1].color = (0.7, 0.2, 0.75, 1)
_nt.links.new(_g.outputs['Fac'], _cr.inputs['Fac']); _nt.links.new(_cr.outputs['Color'], _e.inputs['Color']); _e.inputs['Strength'].default_value = 2.2
_nt.links.new(_e.outputs['Emission'], _nt.nodes['Material Output'].inputs['Surface'])
PHONE_AT = GX + V3(1.25, 0.0, 0.021)
PHONE = box('phone', (0.074, 0.155, 0.008), PHONE_AT + V3(0, 0, 0.004), PHONE_M, bv=0.008, rot=(0, 0, R(28)))
SCREEN = box('phone_screen', (0.066, 0.145, 0.001), (0, 0, 0.0043), SCREEN_M, bv=0.004, parent=PHONE)
bpy.ops.object.text_add(location=(0, 0.035, 0.0055)); CLOCKT = bpy.context.active_object; CLOCKT.name = 'phone_time'; CLOCKT.data.body = '7:12'
CLOCKT.data.size = 0.022; CLOCKT.data.align_x = 'CENTER'; CLOCKT.parent = PHONE; CLOCKT.data.materials.append(emis('phone_text', (1, 1, 1), 4.0))
ROADSIDE = [GROUND, ROAD, LINE, EDGE, GRAVEL, _gp, PHONE, SCREEN, CLOCKT]
