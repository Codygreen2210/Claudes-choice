
# ================================================================ numbers (Live Science with T. Cronin (MIT) and M. Summers (GMU))
LIGHT_MIN = 8 + 20 / 60                 # sunlight takes 8 min 20 s to get here (the gravity change too)
# Earth drops ~36 F a day at first, most places under freezing in 2-3 days, ponds in a week, lakes in months,
# the ocean stays liquid under the ice for years, vents keep chemical life going, Earth ends near -400 F (Pluto ~ -380 F)

# ================================================================ space (far from the yard): stars, the Sun, Earth, Pluto
SP = Vector((0, 200000, 0))
STARS = bpy.data.materials.new('stars'); STARS.use_nodes = True; _sn = STARS.node_tree; _sn.nodes.remove(_sn.nodes['Principled BSDF'])
star_shader(_sn, (0.0015, 0.002, 0.006), 420.0)
_sn.nodes['Emission'].inputs['Strength'].default_value = 1.0
SKYBALL = prim('uv_sphere', 'starsphere', STARS, loc=SP, segments=64, ring_count=32, radius=3000)
SKYBALL.visible_shadow = False; SKYBALL.visible_diffuse = False; SKYBALL.visible_glossy = False
NEB = bpy.data.materials.new('nebula'); NEB.use_nodes = True; _nb = NEB.node_tree; _nb.nodes.remove(_nb.nodes['Principled BSDF']); NEB.blend_method = 'BLEND'
_ne = _nb.nodes.new('ShaderNodeEmission'); _nf = tnoise(_nb, coord(_nb, 'Generated'), 3.0, 6, 1.5)
_nb.links.new(ramp(_nb, _nf, [(0.45, (0.0, 0.0, 0.0)), (0.62, (0.05, 0.02, 0.09)), (0.75, (0.02, 0.05, 0.12))]), _ne.inputs['Color'])
_ne.inputs['Strength'].default_value = 0.1; _nt_ = _nb.nodes.new('ShaderNodeBsdfTransparent'); _nad = _nb.nodes.new('ShaderNodeAddShader')
_nb.links.new(_ne.outputs[0], _nad.inputs[0]); _nb.links.new(_nt_.outputs[0], _nad.inputs[1]); _nb.links.new(_nad.outputs[0], _nb.nodes['Material Output'].inputs['Surface'])
NEBULA = prim('uv_sphere', 'nebula', NEB, loc=SP, segments=48, ring_count=24, radius=2900); NEBULA.visible_shadow = False; NEBULA.hide_render = True

# ---- the Sun: boiling surface (4D noise, w = time), dark limb, corona, loops of glowing gas; it shudders, pinches and blinks out
SUN_C = SP + Vector((0, 0, 0)); SUN_R = 10.0
SUN_M = bpy.data.materials.new('sun_surf'); SUN_M.use_nodes = True; _su = SUN_M.node_tree; _su.nodes.remove(_su.nodes['Principled BSDF'])
_se = _su.nodes.new('ShaderNodeEmission')
def _n4(nt, scale, detail, w_attr, dist=0.0):
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    nz.inputs['Distortion'].default_value = dist; nt.links.new(coord(nt, 'Object'), nz.inputs['Vector']); nt.links.new(objattr(nt, w_attr), nz.inputs['W']); return nz.outputs['Fac']
_g1 = _n4(_su, 0.9, 8, 'w', 0.6)                                           # granulation
_vo = _su.nodes.new('ShaderNodeTexVoronoi'); _vo.voronoi_dimensions = '4D'; _vo.feature = 'DISTANCE_TO_EDGE'; _vo.inputs['Scale'].default_value = 3.2
_su.links.new(coord(_su, 'Object'), _vo.inputs['Vector']); _su.links.new(objattr(_su, 'w'), _vo.inputs['W'])
_cell = math_(_su, 'MINIMUM', math_(_su, 'MULTIPLY', _vo.outputs['Distance'], 5.0), 1.0)
_g = math_(_su, 'ADD', math_(_su, 'MULTIPLY', _g1, 0.72), math_(_su, 'MULTIPLY', _cell, 0.28))
_lw = _su.nodes.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.5
_limb = math_(_su, 'POWER', math_(_su, 'SUBTRACT', 1.0, _lw.outputs['Facing']), 0.55)                     # 1 at the middle, dark at the rim
_heat = objattr(_su, 'heat')                                                                                 # 1 normal .. 0 a dying red ember
_cA = ramp(_su, _g, [(0.2, (0.6, 0.08, 0.0)), (0.45, (1.0, 0.32, 0.02)), (0.65, (1.0, 0.6, 0.08)), (0.85, (1.0, 0.85, 0.3))])
_cB = ramp(_su, _g, [(0.25, (0.25, 0.02, 0.0)), (0.6, (0.7, 0.1, 0.01)), (0.9, (1.0, 0.35, 0.05))])
_col = mixc(_su, _heat, _cB, _cA)
_su.links.new(_col, _se.inputs['Color'])
_su.links.new(math_(_su, 'MULTIPLY', math_(_su, 'MULTIPLY', math_(_su, 'MULTIPLY_ADD', _limb, 0.8, 0.25), objattr(_su, 'bright')), 0.9), _se.inputs['Strength'])
_su.links.new(_se.outputs[0], _su.nodes['Material Output'].inputs['Surface'])
SUN = prim('uv_sphere', 'sun', SUN_M, loc=SUN_C, segments=96, ring_count=48, radius=SUN_R); SUN['w'] = 0.0; SUN['heat'] = 1.0; SUN['bright'] = 1.0
SUN.visible_shadow = False
def glow_shell(name, col, power, strength, attr='a'):
    """an additive fresnel glow shell (corona, shock ring, atmosphere)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.blend_method = 'BLEND'
    e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    if power > 0: f_ = math_(nt, 'POWER', lw.outputs['Facing'], power)                  # rim glow
    else: f_ = math_(nt, 'MULTIPLY', math_(nt, 'POWER', math_(nt, 'SUBTRACT', 1.0, lw.outputs['Facing']), -power), math_(nt, 'MULTIPLY', lw.outputs['Facing'], 4.0))   # a halo ring: 0 at the middle and the edge
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'MULTIPLY', f_, objattr(nt, attr)), strength), e_.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(e_.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m
HALO_M = bpy.data.materials.new('halo_m'); HALO_M.use_nodes = True; _hn = HALO_M.node_tree; _hn.nodes.remove(_hn.nodes['Principled BSDF']); HALO_M.blend_method = 'BLEND'
_hg = _hn.nodes.new('ShaderNodeTexGradient'); _hg.gradient_type = 'SPHERICAL'; _hn.links.new(coord(_hn, 'Object'), _hg.inputs['Vector'])
_hf = math_(_hn, 'POWER', _hg.outputs['Fac'], 2.6); _he = _hn.nodes.new('ShaderNodeEmission')
_hn.links.new(mixc(_hn, _hf, (1.0, 0.18, 0.01), (1.0, 0.55, 0.12)), _he.inputs['Color'])
_hn.links.new(math_(_hn, 'MULTIPLY', _hf, math_(_hn, 'MULTIPLY', objattr(_hn, 'a'), 2.2)), _he.inputs['Strength'])
_ht = _hn.nodes.new('ShaderNodeBsdfTransparent'); _ha = _hn.nodes.new('ShaderNodeAddShader')
_hn.links.new(_he.outputs[0], _ha.inputs[0]); _hn.links.new(_ht.outputs[0], _ha.inputs[1]); _hn.links.new(_ha.outputs[0], _hn.nodes['Material Output'].inputs['Surface'])
CORONA = prim('plane', 'corona', HALO_M, loc=SUN_C + Vector((0, 0.5, 0)), rot=(R(90), 0, 0), size=2.0)     # a soft glow card behind the Sun (unit radius, scaled)
CORONA.visible_shadow = False; CORONA_R = SUN_R * 2.6
CORONA['a'] = 1.0; CORONA.visible_shadow = False
SHOCK = prim('torus', 'shock', emis_mix('shock_m', (1.0, 0.8, 0.5), 9.0, 'a'), loc=SUN_C, rot=(R(90), 0, 0), major_radius=1.0, minor_radius=0.025, major_segments=128, minor_segments=12)
SHOCK['a'] = 0.0; SHOCK.visible_shadow = False
PROM_M = bpy.data.materials.new('prom'); PROM_M.use_nodes = True; _pm = PROM_M.node_tree; _pm.nodes.remove(_pm.nodes['Principled BSDF'])
_pe = _pm.nodes.new('ShaderNodeEmission'); _pe.inputs['Color'].default_value = (1.0, 0.22, 0.03, 1)
_pm.links.new(math_(_pm, 'MULTIPLY', math_(_pm, 'MULTIPLY_ADD', tnoise(_pm, coord(_pm, 'Object'), 2.0, 4), 1.4, 0.2), math_(_pm, 'MULTIPLY', objattr(_pm, 'a'), 0.9)), _pe.inputs['Strength'])
_pm.links.new(_pe.outputs[0], _pm.nodes['Material Output'].inputs['Surface'])
PROMS = []
random.seed(41)
for k in range(0):                                                 # loops of glowing gas standing off the limb (seen edge-on)
    a0 = 0.6 + k * 1.57 + random.uniform(-0.3, 0.3); span = random.uniform(0.45, 0.7); hgt = random.uniform(0.12, 0.2); pts = []
    for i in range(17):
        u = i / 16; a_ = a0 + span * (u - 0.5); h_ = SUN_R * (1.0 + hgt * math.sin(math.pi * u))
        pts.append((h_ * math.cos(a_), 0.0, h_ * math.sin(a_)))
    o = tube(f'prom_{k}', pts, lambda u: 0.35 + 0.3 * math.sin(math.pi * u), PROM_M, seg=10); o.parent = None
    o.location = SUN_C; o['a'] = 1.0; o['ph'] = random.uniform(0, 6.3); o.visible_shadow = False; PROMS.append(o)
EMBER = prim('uv_sphere', 'ember', emis_mix('ember_m', (1.0, 0.12, 0.02), 3.0, 'a'), loc=SUN_C, segments=32, ring_count=16, radius=1.0); EMBER['a'] = 0.0
SPACE_FILL = light_at('space_fill', 'AREA', SP + Vector((60, -40, 30)), SP, 0.0, (0.55, 0.65, 1.0), 40)

def sun_story(c):
    """c = seconds from frame one (it runs on past the end into the loop). Shudder from -0.6, pinch at 1.15-1.4, blink out at 1.4."""
    w = 0.9 * c; SUN['w'] = w                                       # the surface boils visibly
    for o in PROMS: o['a'] = 1.0
    if c < 1.15:
        k = smooth(-1.6, 1.15, c)                                  # already shuddering on frame one: pulses, flickers, reddens, shrinks
        pul = 1.0 + 0.06 * k * math.sin(2 * math.pi * 2.6 * c) + 0.025 * k * wob(c, 9.0, 2.0)
        r_ = (1.0 - 0.3 * k) * pul; SUN['heat'] = 1.0 - 0.75 * k; SUN['bright'] = (1.0 - 0.1 * k) * (1.0 + 0.18 * k * math.sin(2 * math.pi * 2.6 * c + 1.0))
        CORONA['a'] = 1.0 - 0.3 * k; SHOCK['a'] = 0.0; sh_r = 1.0
        for o in PROMS: o['a'] = 1.0 + 0.6 * k
    elif c < 1.4:                                                  # the pinch: falls in on itself, one hot flare
        k = smooth(1.15, 1.4, c); r_ = lerp(0.72, 0.04, k * k)
        SUN['heat'] = lerp(0.55, 0.9, k); SUN['bright'] = lerp(0.85, 2.6, k); CORONA['a'] = (1.0 - k) * 0.7; SHOCK['a'] = 0.0; sh_r = 1.0
        for o in PROMS: o['a'] = 1.6 * (1 - k)
    else:                                                          # gone; the last light leaves as an expanding shell
        r_ = 0.0; SUN['bright'] = 0.0; CORONA['a'] = 0.0
        k = c - 1.4; sh_r = SUN_R * (0.3 + 3.2 * k + 2.0 * k * k); SHOCK['a'] = 1.4 * math.exp(-1.6 * k) * smooth(0.0, 0.03, k)
        for o in PROMS: o['a'] = 0.0
    SUN.scale = (max(r_, 1e-4),) * 3; SUN.hide_render = r_ < 0.01
    CORONA.scale = (max(r_, 1e-4) * CORONA_R * (1 + 0.04 * wob(c, 2.0, 7.0)),) * 3; CORONA.hide_render = CORONA['a'] < 0.01
    for o in PROMS:
        o.scale = (max(r_, 1e-4),) * 3; o.hide_render = o['a'] < 0.01 or r_ < 0.05
        o.rotation_euler = (0, 0.03 * wob(c, 0.6, o['ph']), 0)
    SHOCK.scale = (sh_r,) * 3; SHOCK.hide_render = SHOCK['a'] < 0.005
    EMBER['a'] = (smooth(1.3, 1.42, c) * math.exp(-1.2 * max(c - 1.42, 0.0))) if c > 1.3 else 0.0; EMBER.scale = (lerp(0.9, 0.35, smooth(1.4, 2.6, c)),) * 3; EMBER.hide_render = EMBER['a'] < 0.01
    return r_

# ---- Earth: real coastlines (earth_col.jpg), clouds, a thin blue air shell, city lights at night, frost over everything later
EARTH_C = SP + Vector((0, 0, 0)); ER = 1.0
EIMG = bpy.data.images.load(asset('earth_col.jpg'))
EARTH_M = mat('earth_m', (0.1, 0.2, 0.4), 0.6); _em = EARTH_M.node_tree; _eb = _em.nodes['Principled BSDF']
_et = _em.nodes.new('ShaderNodeTexImage'); _et.image = EIMG; _et.interpolation = 'Cubic'
_euv = coord(_em, 'UV'); _em.links.new(_euv, _et.inputs['Vector'])
_ecol = mixc(_em, math_(_em, 'MULTIPLY', tnoise(_em, coord(_em, 'Object'), 6.0, 8), 0.25), _et.outputs['Color'], (0.06, 0.07, 0.05))
# frost: white-blue ice with faint cracks; a noisy front so it can creep
_fr = objattr(_em, 'frost'); _fn = tnoise(_em, coord(_em, 'Object'), 2.5, 6)
_fk = math_(_em, 'MINIMUM', math_(_em, 'MAXIMUM', math_(_em, 'MULTIPLY', math_(_em, 'SUBTRACT', math_(_em, 'MULTIPLY_ADD', _fr, 1.4, -0.2), _fn), 6.0), 0.0), 1.0)
_icec = ramp(_em, tnoise(_em, coord(_em, 'Object'), 9.0, 6), [(0.3, (0.55, 0.66, 0.78)), (0.55, (0.86, 0.9, 0.96)), (0.75, (0.95, 0.97, 1.0))])
_icec = mixc(_em, 0.42, _icec, _et.outputs['Color'])
_em.links.new(mixc(_em, _fk, _ecol, _icec), _eb.inputs['Base Color'])
_em.links.new(mixc(_em, _fk, (0.55, 0.55, 0.55, 1), (0.25, 0.25, 0.25, 1)), _eb.inputs['Roughness'])
# city lights on land (the night side), only where it isn't frozen
_city = math_(_em, 'MULTIPLY', math_(_em, 'GREATER_THAN', tnoise(_em, coord(_em, 'Object'), 70.0, 3), 0.64), math_(_em, 'GREATER_THAN', tnoise(_em, coord(_em, 'Object'), 3.0, 3), 0.48))
_sxc = sepz(_em, _et.outputs['Color']); _land2 = math_(_em, 'GREATER_THAN', math_(_em, 'SUBTRACT', _sxc.outputs['Y'], _sxc.outputs['Z']), 0.04)
_em.links.new(math_(_em, 'MULTIPLY', math_(_em, 'MULTIPLY', math_(_em, 'MULTIPLY', _city, _land2), objattr(_em, 'city')), math_(_em, 'SUBTRACT', 1.0, _fk)), _eb.inputs['Emission Strength'])
_eb.inputs['Emission Color'].default_value = (1.0, 0.7, 0.35, 1)
EARTH = prim('uv_sphere', 'earth', EARTH_M, loc=EARTH_C, segments=128, ring_count=64, radius=ER); EARTH['frost'] = 0.0; EARTH['city'] = 0.0
EARTH.rotation_mode = 'XYZ'
CLD_M = mat('cld_m', (1, 1, 1), 0.9); CLD_M.blend_method = 'BLEND'; _cn = CLD_M.node_tree
_cn.links.new(math_(_cn, 'MULTIPLY', math_(_cn, 'MINIMUM', math_(_cn, 'MAXIMUM', math_(_cn, 'MULTIPLY', math_(_cn, 'SUBTRACT', tnoise(_cn, coord(_cn, 'Object'), 2.2, 8, 0.8), 0.56), 5.0), 0.0), 1.0), objattr(_cn, 'a')), _cn.nodes['Principled BSDF'].inputs['Alpha'])
CLOUDS = prim('uv_sphere', 'clouds', CLD_M, loc=EARTH_C, segments=96, ring_count=48, radius=ER * 1.012); CLOUDS['a'] = 0.8; CLOUDS.parent = EARTH; CLOUDS.location = (0, 0, 0)
ATM = prim('uv_sphere', 'atm', glow_shell('atm_m', (0.3, 0.55, 1.0), 3.0, 2.0), loc=EARTH_C, segments=96, ring_count=48, radius=ER * 1.04); ATM['a'] = 1.0; ATM.parent = EARTH; ATM.location = (0, 0, 0)
ATM.visible_shadow = False
EARTH_PARTS = [EARTH, CLOUDS, ATM]

# ---- the orbit: a ghost circle (dashed) where Earth would have gone, and a glowing trail that goes dead straight
ORB_R = 22.0
DASH_M = emis_mix('dash_m', (0.6, 0.8, 1.0), 2.0, 'a')
_orb_pts = []
DASHES = []
for k in range(90):
    a0_ = 2 * math.pi * k / 90; a1_ = a0_ + 2 * math.pi / 90 * 0.55
    pts = [(ORB_R * math.cos(a0_ + (a1_ - a0_) * j / 3), ORB_R * math.sin(a0_ + (a1_ - a0_) * j / 3), 0) for j in range(4)]
    o = tube(f'dash_{k}', pts, 0.06, DASH_M, seg=6); o.location = SUN_C; o['a'] = 0.0; o.visible_shadow = False; DASHES.append(o)
TRAIL_M = emis_mix('trail_m', (0.45, 0.85, 1.0), 4.0, 'a')
TRAIL = None
def trail_set(pts):
    """rebuild the trail tube along pts (world), thin at the old end"""
    global TRAIL
    if TRAIL is not None:
        me_ = TRAIL.data; bpy.data.objects.remove(TRAIL); bpy.data.meshes.remove(me_)
    TRAIL = tube('trail', pts, lambda u: 0.03 + 0.17 * u, TRAIL_M, seg=10); TRAIL['a'] = 1.0; TRAIL.visible_shadow = False
    return TRAIL

# ---- Pluto: tan and rust with its big pale heart (texture made here), much smaller than Earth
def pluto_image(w=1024, h=512):
    u = (np.arange(w) + 0.5) / w; v = (np.arange(h) + 0.5) / h; U, Vv = np.meshgrid(u, v)
    lon = (U - 0.5) * 2 * np.pi; lat = (Vv - 0.5) * np.pi
    rng = np.random.default_rng(7); acc = np.zeros((h, w), np.float32)
    for o_, amp in ((4, 1.0), (8, 0.5), (16, 0.3), (32, 0.18), (64, 0.1)):
        ph = rng.random(4) * 6.28; acc += amp * np.sin(o_ * lon + ph[0] + 2 * np.sin(o_ * 0.7 * lat + ph[1])) * np.cos(o_ * lat * 0.9 + ph[2])
    acc = (acc - acc.min()) / (np.ptp(acc) + 1e-9)
    tan = np.array([0.62, 0.48, 0.34]); rust = np.array([0.33, 0.16, 0.08]); pale = np.array([0.82, 0.78, 0.7])
    c = tan[None, None] * (0.75 + 0.5 * acc[..., None])
    belt = np.clip(1 - np.abs(lat + 0.15) / 0.35, 0, 1) * (acc > 0.45)                 # the dark rusty belt near the equator
    c = c * (1 - belt[..., None] * 0.8) + rust * belt[..., None] * 0.8
    from PIL import Image as _I, ImageDraw as _D, ImageFilter as _F                # the heart, facing lon 0 (classic heart curve)
    hm = _I.new('L', (w, h), 0); tt = np.linspace(0, 2 * np.pi, 200); hx = 16 * np.sin(tt) ** 3; hy = 13 * np.cos(tt) - 5 * np.cos(2 * tt) - 2 * np.cos(3 * tt) - np.cos(4 * tt)
    lat0 = 0.12; sc_ = 0.027; plon = hx * sc_ / np.cos(lat0 + hy * sc_); plat = lat0 + hy * sc_
    _D.Draw(hm).polygon([((lo / (2 * np.pi) + 0.5) * w, (la_ / np.pi + 0.5) * h) for lo, la_ in zip(plon, plat)], fill=255)
    heart = np.asarray(hm.filter(_F.GaussianBlur(3))).astype(np.float32) / 255.0
    c = c * (1 - heart[..., None]) + pale * heart[..., None]
    c = c * (0.9 + 0.2 * acc[..., None])
    img = bpy.data.images.new('pluto_tex', w, h); img.colorspace_settings.name = 'sRGB'
    px = np.concatenate([np.clip(c, 0, 1) ** 2.2, np.ones((h, w, 1))], axis=2).astype(np.float32)   # image rows bottom-up
    img.pixels.foreach_set(px.ravel()); img.pack(); return img
PLUTO_M = mat('pluto_m', (0.6, 0.5, 0.4), 0.85); _pl = PLUTO_M.node_tree; _pt = _pl.nodes.new('ShaderNodeTexImage'); _pt.image = pluto_image()
_pl.links.new(coord(_pl, 'UV'), _pt.inputs['Vector']); _pl.links.new(_pt.outputs['Color'], _pl.nodes['Principled BSDF'].inputs['Base Color'])
_pb = _pl.nodes.new('ShaderNodeBump'); _pb.inputs['Strength'].default_value = 0.25; _pl.links.new(tnoise(_pl, coord(_pl, 'Object'), 18.0, 8), _pb.inputs['Height'])
_pl.links.new(_pb.outputs['Normal'], _pl.nodes['Principled BSDF'].inputs['Normal'])
PLUTO = prim('uv_sphere', 'pluto', PLUTO_M, loc=SP + Vector((0, 0, -60)), segments=96, ring_count=48, radius=0.42); PLUTO.rotation_mode = 'XYZ'
PLUTO_KEY = light_at('pluto_key', 'AREA', SP + Vector((-30, -25, 20)), SP, 0.0, (0.75, 0.82, 1.0), 12)
SPACE = [SKYBALL, SUN, CORONA, SHOCK, EMBER, PLUTO] + PROMS + EARTH_PARTS + DASHES
