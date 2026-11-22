
# ================================================================ the set: Cape Cod Bay, about 14 m (45 ft) deep. Green-blue water as a volume under a
# rolling ocean surface, sun shafts through it (a shadow-only ripple screen just under the surface), a sandy bottom with ripples, rocks and weed,
# a bright sky above for the surface shots, and a lobster boat.
SEA_Z = 0.0; FLOOR_Z = -13.7
# ---- the sky (seen above water and through the surface from below)
sky = W_.node_tree.nodes.new('ShaderNodeTexSky')
try: sky.sky_type = 'MULTIPLE_SCATTERING'
except Exception: pass
for k_, v_ in (('sun_elevation', R(48)), ('sun_rotation', R(140)), ('altitude', 10.0), ('air_density', 1.0), ('dust_density', 2.0)):
    try: setattr(sky, k_, v_)
    except Exception: pass
W_.node_tree.links.new(sky.outputs['Color'], WBG.inputs['Color']); WBG.inputs['Strength'].default_value = 0.3
SUN = light_at('sun', 'SUN', (0, 0, 50), (math.cos(R(140)) * -0.9, math.sin(R(140)) * -0.9, 0), 3.2, (1.0, 0.96, 0.9), 0.02)
SUN.data.angle = R(1.2)
# ---- the ocean surface: an ocean-modifier grid, glass from both sides, but it lets the sun's shadow rays through
SURF = prim('plane', 'surface', None, loc=(0, 0, SEA_Z), size=1.0)
oc = SURF.modifiers.new('ocean', 'OCEAN'); oc.geometry_mode = 'GENERATE'; oc.repeat_x = 1; oc.repeat_y = 1; oc.size = 1.0
oc.spatial_size = 120; oc.resolution = 10; oc.wave_scale = 0.4; oc.choppiness = 0.9; oc.wind_velocity = 7.0; oc.random_seed = 3
SURFM = bpy.data.materials.new('sea_surface'); SURFM.use_nodes = True; nt = SURFM.node_tree; b_ = nt.nodes['Principled BSDF']
b_.inputs['Base Color'].default_value = (0.05, 0.25, 0.26, 1); b_.inputs['Roughness'].default_value = 0.04; b_.inputs['Transmission Weight'].default_value = 1.0
b_.inputs['IOR'].default_value = 1.333
lp = nt.nodes.new('ShaderNodeLightPath'); tr_ = nt.nodes.new('ShaderNodeBsdfTransparent'); mx_ = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Shadow Ray'], mx_.inputs['Fac']); nt.links.new(b_.outputs[0], mx_.inputs[1]); nt.links.new(tr_.outputs[0], mx_.inputs[2])
nt.links.new(mx_.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
SURF.data.materials.append(SURFM)
for p_ in SURF.data.polygons: p_.use_smooth = True
# a darker, bluer open sea out past the ocean tile
_fv = []; _ff = []
for k in range(64):
    a_ = 2 * math.pi * k / 64; _fv += [(59.0 * math.cos(a_), 59.0 * math.sin(a_), 0.0), (2500 * math.cos(a_), 2500 * math.sin(a_), 0.0)]
for k in range(64): k2 = (k + 1) % 64; _ff.append((2 * k, 2 * k2, 2 * k2 + 1, 2 * k + 1))
FARSEAM = mat('farsea', (0.02, 0.07, 0.09), 0.08, coat=0.6)
FARSEA = mesh('farsea', _fv, _ff, FARSEAM, smooth_=False, loc=(0, 0, SEA_Z - 0.05))
# ---- the water: green-blue, light scatters forward; deeper is darker
WATERV = bpy.data.materials.new('water_vol'); WATERV.use_nodes = True; nt = WATERV.node_tree; out_ = nt.nodes['Material Output']
nt.nodes.remove(nt.nodes['Principled BSDF'])
vs_ = nt.nodes.new('ShaderNodeVolumeScatter'); vs_.inputs['Color'].default_value = (0.40, 0.75, 0.70, 1); vs_.inputs['Density'].default_value = 0.034
try: vs_.inputs['Anisotropy'].default_value = 0.75
except Exception: pass
va_ = nt.nodes.new('ShaderNodeVolumeAbsorption'); va_.inputs['Color'].default_value = (0.22, 0.62, 0.58, 1); va_.inputs['Density'].default_value = 0.055
ad_ = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(vs_.outputs[0], ad_.inputs[0]); nt.links.new(va_.outputs[0], ad_.inputs[1])
nt.links.new(ad_.outputs[0], out_.inputs['Volume'])
VOL = box('water', (600, 600, 140), (0, 0, SEA_Z - 70.03), WATERV)
VOLM_DEEP = None
# ---- sun shafts: a ripple screen a little under the surface, seen only by shadow rays
GOBO = bpy.data.materials.new('gobo'); GOBO.use_nodes = True; nt = GOBO.node_tree; out_ = nt.nodes['Material Output']; nt.nodes.remove(nt.nodes['Principled BSDF'])
lp = nt.nodes.new('ShaderNodeLightPath'); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 1.1
vo.voronoi_dimensions = '4D'; GOBO_W = vo.inputs['W']
GOBO_MAP = nt.nodes.new('ShaderNodeMapping'); nt.links.new(coord(nt, 'Object'), GOBO_MAP.inputs['Vector'])
wn_ = nt.nodes.new('ShaderNodeTexNoise'); wn_.inputs['Scale'].default_value = 0.6; nt.links.new(GOBO_MAP.outputs['Vector'], wn_.inputs['Vector'])
vd_ = nt.nodes.new('ShaderNodeVectorMath'); vd_.operation = 'ADD'; nt.links.new(GOBO_MAP.outputs['Vector'], vd_.inputs[0]); nt.links.new(wn_.outputs['Color'], vd_.inputs[1])
nt.links.new(vd_.outputs[0], vo.inputs['Vector'])
mask_ = ramp_v(nt, vo.outputs['Distance'], 0.015, 0.09)
fac_ = math_(nt, 'MULTIPLY', lp.outputs['Is Shadow Ray'], math_(nt, 'MULTIPLY', mask_, 0.62))
tr_ = nt.nodes.new('ShaderNodeBsdfTransparent'); df_ = nt.nodes.new('ShaderNodeBsdfDiffuse'); df_.inputs['Color'].default_value = (0, 0, 0, 1)
mx_ = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fac_, mx_.inputs['Fac']); nt.links.new(tr_.outputs[0], mx_.inputs[1]); nt.links.new(df_.outputs[0], mx_.inputs[2])
nt.links.new(mx_.outputs[0], out_.inputs['Surface'])
SCREEN = prim('plane', 'gobo', GOBO, loc=(0, 0, SEA_Z - 0.6), size=300)
# ---- the bottom: sand with ripples and patches of darker silt, rocks, weed
SAND = mat('sand', (0.42, 0.38, 0.30), 0.95); nt = SAND.node_tree; b_ = nt.nodes['Principled BSDF']; co = coord(nt, 'Object')
wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 0.9; wv.inputs['Distortion'].default_value = 3.0; wv.inputs['Detail'].default_value = 3.0
nt.links.new(co, wv.inputs['Vector'])
bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5; bp.inputs['Distance'].default_value = 0.05
nt.links.new(math_(nt, 'ADD', wv.outputs['Fac'], math_(nt, 'MULTIPLY', tnoise(nt, co, 9.0, 8.0), 0.6)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b_.inputs['Normal'])
nt.links.new(mixc(nt, ramp_v(nt, tnoise(nt, co, 0.12, 4.0), 0.45, 0.62), (0.42, 0.38, 0.30), (0.22, 0.22, 0.18)), b_.inputs['Base Color'])
FLOOR = prim('plane', 'floor', SAND, loc=(0, 0, FLOOR_Z), size=400)
sub_ = FLOOR.modifiers.new('sub', 'SUBSURF'); sub_.subdivision_type = 'SIMPLE'; sub_.levels = sub_.render_levels = 6
tx_ = bpy.data.textures.new('dunes', 'CLOUDS'); tx_.noise_scale = 14.0
dp_ = FLOOR.modifiers.new('disp', 'DISPLACE'); dp_.texture = tx_; dp_.strength = 1.4; dp_.texture_coords = 'GLOBAL'
ROCKM = mat('rock', (0.20, 0.19, 0.17), 0.85); noisy(ROCKM, 3.0, 0.45, 0.1)
rr_ = random.Random(11); ROCKS = []
for j in range(70):
    x_, y_ = rr_.uniform(-60, 60), rr_.uniform(-40, 60); r0 = rr_.uniform(0.3, 1.6)
    o = prim('ico_sphere', f'rock{j}', ROCKM, loc=(x_, y_, FLOOR_Z + 0.2), radius=r0, subdivisions=3)
    o.scale = (rr_.uniform(0.8, 1.4), rr_.uniform(0.8, 1.3), rr_.uniform(0.4, 0.8)); o.rotation_euler = (0, 0, rr_.uniform(0, 6))
    dd = o.modifiers.new('d', 'DISPLACE'); dd.texture = tx_; dd.strength = 0.35 * r0; ROCKS.append(o)
WEEDM = mat('weed', (0.18, 0.22, 0.06), 0.6, trans=0.25, sheen=0.3)
WEED = []
for j in range(60):
    x_, y_ = rr_.uniform(-30, 30), rr_.uniform(-20, 40); h_ = rr_.uniform(0.8, 2.6)
    pts = [(x_ + 0.15 * math.sin(k * 0.9 + j), y_ + 0.1 * math.cos(k * 0.7 + j), FLOOR_Z + 0.4 + h_ * k / 9) for k in range(10)]
    o = tube(f'weed{j}', pts, lambda u: 0.035 * (1 - 0.7 * u) + 0.01, WEEDM, seg=6); o.scale = (1.0, 1.0, 1.0); WEED.append((o, j))
# ---- the lobster boat at the surface: a 35 ft Down East hull (high flared bow, low stern), wheelhouse forward with windows, a mast with
# radar and antennas, a hauler and davit on the starboard side, stacked traps, painted buoys, rails, an exhaust stack, hull numbers.
BOAT = empty('boat_root', loc=(14.0, 10.0, SEA_Z))
HULLM = mat('hull', (0.80, 0.81, 0.80), 0.25, coat=0.6); noisy(HULLM, 4.0, 0.06, 0.05)
BOTM = mat('bottom', (0.42, 0.07, 0.05), 0.6); BOOTM = mat('boot', (0.06, 0.12, 0.30), 0.35, coat=0.5)
DECKM = mat('deck', (0.58, 0.56, 0.50), 0.75); noisy(DECKM, 18.0, 0.18, 0.1)
TRIMM = mat('trim', (0.06, 0.12, 0.30), 0.35, coat=0.5); GLASSB = mat('bglass', (0.02, 0.03, 0.04), 0.03, coat=1.0)
STEEL = mat('steel', (0.7, 0.7, 0.72), 0.2, metal=1.0); RUBBER = mat('rubber', (0.03, 0.03, 0.03), 0.7)
L_B = 10.6
def hull_sec(u):
    """u 0 = transom .. 1 = stem: half-beam, sheer height, keel depth, flare"""
    b = 1.85 * (1 - (max(0.0, u - 0.45) / 0.55) ** 2.2) ** 0.75 * (1 - 0.08 * (1 - u) ** 3)
    h = 1.05 + 0.75 * u ** 2.4; k = 0.55 + 0.25 * math.sin(math.pi * min(u, 0.9) / 0.9) ** 0.5 - 0.3 * u ** 6
    return b, h, k
hv = []; hf = []; NH = 60; NSC = 14
for i in range(NH):
    u = i / (NH - 1); x_ = -L_B / 2 + L_B * u; b, h, k = hull_sec(u)
    ring = []
    for j in range(NSC):                                                   # keel -> chine -> flared topsides -> sheer, starboard side
        v = j / (NSC - 1)
        y_ = b * (math.sin(v * math.pi / 2) ** 0.55) * (0.9 + 0.1 * v) + 0.05 * v ** 3
        z_ = -k + (k + h) * (v ** 1.5)
        ring.append((x_, max(y_, 0.02), z_))
    hv += ring + [(x_, -y_, z_) for (x_, y_, z_) in ring[::-1]]
NR2 = 2 * NSC
for i in range(NH - 1):
    for j in range(NR2 - 1): hf.append((i * NR2 + j, i * NR2 + j + 1, (i + 1) * NR2 + j + 1, (i + 1) * NR2 + j))
hf.append(tuple(range(NR2))[::-1])                                          # the transom
HULL = mesh('hull', hv, hf, HULLM, BOAT); HULL.data.materials.append(BOTM); HULL.data.materials.append(BOOTM)
for p_ in HULL.data.polygons:
    zc = sum(HULL.data.vertices[v].co.z for v in p_.vertices) / len(p_.vertices)
    p_.material_index = 1 if zc < 0.05 else (2 if zc < 0.18 else 0)
HULL.modifiers.new('th', 'SOLIDIFY').thickness = 0.05; subsurf(HULL, 1)
# decks: the cockpit sole aft, the foredeck up at the sheer
deck_pts = []
for i in range(30):
    u = i / 29 * 0.62; b, h, k = hull_sec(u); deck_pts.append((-L_B / 2 + L_B * u, b * 0.96))
dv = [(x_, y_, 0.55) for x_, y_ in deck_pts] + [(x_, -y_, 0.55) for x_, y_ in deck_pts[::-1]]
mesh('cockpit_sole', dv, [tuple(range(len(dv)))], DECKM, BOAT, smooth_=False)
fd = []
for i in range(30):
    u = 0.62 + 0.37 * i / 29; b, h, k = hull_sec(u); fd.append((-L_B / 2 + L_B * u, b * 0.97, h - 0.03))
fv_ = [(x_, y_, z_) for x_, y_, z_ in fd] + [(x_, -y_, z_) for x_, y_, z_ in fd[::-1]]
mesh('foredeck', fv_, [tuple(range(len(fv_)))], DECKM, BOAT, smooth_=False)
# rub rail and cap rail along the sheer
for sy in (1, -1):
    rail = [(-L_B / 2 + L_B * u, sy * (hull_sec(u)[0] + 0.06), hull_sec(u)[1]) for u in [i / 40 for i in range(41)]]
    tube(f'caprail{sy}', rail, 0.045, TRIMM, BOAT, seg=8)
    tube(f'rubrail{sy}', [(x_, y_ + sy * 0.02, z_ - 0.35) for (x_, y_, z_) in rail], 0.035, RUBBER, BOAT, seg=8)
# wheelhouse with windows all round, a roof with an overhang, a mast, radar and antennas
HX = 1.2
house = box('house', (2.9, 2.9, 1.9), (HX, 0, 0.55 + 0.95), HULLM, bv=0.07, parent=BOAT)
box('roof', (3.6, 3.2, 0.12), (HX - 0.2, 0, 2.52), HULLM, bv=0.04, parent=BOAT)
for k_, (pos, size) in enumerate((((HX + 1.46, 0, 1.95), (0.04, 2.5, 0.7)), ((HX, 1.46, 1.95), (2.2, 0.04, 0.6)), ((HX, -1.46, 1.95), (2.2, 0.04, 0.6)))):
    box(f'win{k_}', size, pos, GLASSB, parent=BOAT)
for yy in (-0.85, 0.0, 0.85): box(f'mull{yy}', (0.06, 0.06, 0.72), (HX + 1.48, yy, 1.95), TRIMM, parent=BOAT)
box('stripe_house', (2.95, 2.95, 0.08), (HX, 0, 1.52), TRIMM, parent=BOAT)
tube('mast', [(HX - 0.6, 0, 2.55), (HX - 0.6, 0, 4.3)], 0.05, STEEL, BOAT, seg=10)
box('radar_arm', (1.6, 0.14, 0.12), (HX - 0.6, 0, 4.0), mat('radar', (0.9, 0.9, 0.88), 0.4), bv=0.03, parent=BOAT)
prim('cylinder', 'radar_base', mat('radarb', (0.9, 0.9, 0.88), 0.4), BOAT, loc=(HX - 0.6, 0, 3.85), radius=0.16, depth=0.22, vertices=18)
for yy in (0.9, -0.9): tube(f'whip{yy}', [(HX - 1.6, yy, 2.58), (HX - 1.7, yy, 5.2)], lambda u: 0.02 * (1 - 0.7 * u), mat('whip', (0.92, 0.92, 0.9), 0.4), BOAT, seg=6)
prim('uv_sphere', 'light', emis('masthead', (1.0, 1.0, 0.95), 2.0), BOAT, loc=(HX - 0.6, 0, 4.35), radius=0.06, segments=10, ring_count=6)
# exhaust stack, hauler on its davit, bait barrel
tube('exhaust', [(HX - 1.3, 1.25, 1.0), (HX - 1.3, 1.25, 3.0)], 0.09, STEEL, BOAT, seg=12)
tube('davit', [(HX - 1.7, 1.75, 1.1), (HX - 1.7, 1.75, 2.6), (HX - 1.7, 2.1, 2.8), (HX - 1.7, 2.35, 2.6)], 0.045, STEEL, BOAT, seg=10)
prim('cylinder', 'block', STEEL, BOAT, loc=(HX - 1.7, 2.35, 2.5), radius=0.11, depth=0.06, vertices=16, rot=(R(90), 0, 0))
prim('cylinder', 'hauler', mat('hauler', (0.75, 0.75, 0.78), 0.25, metal=1.0), BOAT, loc=(HX - 1.7, 1.55, 1.3), radius=0.2, depth=0.18, vertices=24, rot=(R(90), 0, 0))
prim('cylinder', 'barrel', mat('barrel', (0.15, 0.32, 0.6), 0.5), BOAT, loc=(-2.6, -1.0, 0.95), radius=0.28, depth=0.8, vertices=20)
# lobster traps: green vinyl-coated wire boxes, stacked
TRAPM = mat('trap', (0.08, 0.30, 0.10), 0.5)
_trap = prim('cube', 'trap_src', TRAPM, size=1.0, scale=(1.15, 0.58, 0.42)); _sb = _trap.modifiers.new('sub', 'SUBSURF'); _sb.subdivision_type = 'SIMPLE'; _sb.levels = _sb.render_levels = 3
_wf = _trap.modifiers.new('wire', 'WIREFRAME'); _wf.thickness = 0.012; _trap.parent = BOAT; _trap.location = (-1.4, -0.7, 0.78)
for k_, (x_, y_, z_) in enumerate(((-1.4, 0.7, 0.78), (-2.8, -0.7, 0.78), (-2.8, 0.7, 0.78), (-1.4, -0.7, 1.21), (-2.8, 0.7, 1.21), (-4.0, 0.0, 0.78))):
    t_ = _trap.copy(); S.collection.objects.link(t_); t_.parent = BOAT; t_.location = (x_, y_, z_); t_.rotation_euler = (0, 0, R(3 * k_ - 6))
# painted buoys hung on the house side and on the rail
BUOYM = [mat('buoy_a', (0.95, 0.45, 0.05), 0.5), mat('buoy_b', (0.95, 0.95, 0.9), 0.5), mat('buoy_c', (0.08, 0.35, 0.75), 0.5)]
for k_ in range(5):
    bz = lathe(f'buoy{k_}', [(0.0, 0.0), (0.09, 0.05), (0.13, 0.2), (0.13, 0.45), (0.08, 0.6), (0.02, 0.62)], 16, BUOYM[k_ % 3], BOAT, loc=(HX - 1.45, -1.47 - 0.01 * k_, 1.0 + 0.0))
    bz.location = (HX - 1.4 + 0.33 * k_, -1.5, 1.05); bz.data.materials.append(BUOYM[(k_ + 1) % 3])
    for p_ in bz.data.polygons:
        zc = sum(bz.data.vertices[v].co.z for v in p_.vertices) / len(p_.vertices); p_.material_index = 1 if 0.25 < zc < 0.4 else 0
    tube(f'buoyspindle{k_}', [(HX - 1.4 + 0.33 * k_, -1.5, 1.65), (HX - 1.4 + 0.33 * k_, -1.5, 0.95)], 0.012, mat('spindle', (0.6, 0.45, 0.25), 0.7), BOAT, seg=6)
# the dive flag on a float (red with a white stripe)
FLAGM = mat('diveflag', (0.75, 0.04, 0.03), 0.6); FLOAT = empty('float', loc=(-3.0, 6.0, SEA_Z))
prim('uv_sphere', 'floatball', mat('floatball', (0.9, 0.35, 0.05), 0.4), FLOAT, loc=(0, 0, 0.12), radius=0.28, segments=16, ring_count=10)
tube('flagpole', [(0, 0, 0.2), (0, 0, 1.4)], 0.015, mat('pole', (0.8, 0.8, 0.8), 0.4), FLOAT, seg=8)
fl_ = box('flag', (0.02, 0.6, 0.45), (0, 0.32, 1.15), FLAGM, parent=FLOAT)
box('flagstripe', (0.025, 0.7, 0.08), (0, 0.32, 1.15), mat('flagw', (0.9, 0.9, 0.9), 0.6), parent=FLOAT, rot=(R(-37), 0, 0))
