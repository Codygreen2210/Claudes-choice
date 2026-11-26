# ================================================================ props: swords, dial scales, cloth
def iron_mat(name, rust=0.3, base=(0.05, 0.05, 0.055), rust_col=(0.085, 0.036, 0.017), seed=0.0, paint=None):
    """dark forged iron with rust blooms and pitting; paint (rgb) = old paint left in the low spots"""
    m = mat(name, base, 0.42, 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    co = coord(nt, 'Object'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed * 3.1, seed * 1.7, seed * 0.9); nt.links.new(co, mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 7.0, 10.0, 0.4); fine = tnoise(nt, mp.outputs['Vector'], 38.0, 4.0)
    f_ = math_(nt, 'ADD', math_(nt, 'MULTIPLY', big, 0.8), math_(nt, 'MULTIPLY', fine, 0.2))
    rf = ramp_v(nt, f_, 0.62 - rust * 0.25, 0.70 - rust * 0.18)                     # 0 = bare iron, 1 = rust
    rc = mixc(nt, tnoise(nt, mp.outputs['Vector'], 14.0, 6.0), rust_col, tuple(c * 0.55 for c in rust_col))
    ic = mixc(nt, fine, base, tuple(c * 1.6 for c in base))
    if paint: ic = mixc(nt, ramp_v(nt, big, 0.30, 0.42), paint, ic)
    nt.links.new(mixc(nt, rf, ic, rc), b.inputs['Base Color'])
    mt = nt.nodes.new('ShaderNodeMapRange'); mt.inputs['To Min'].default_value = 0.85; mt.inputs['To Max'].default_value = 0.05; nt.links.new(rf, mt.inputs['Value']); nt.links.new(mt.outputs['Result'], b.inputs['Metallic'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.38; mr.inputs['To Max'].default_value = 0.92; nt.links.new(rf, mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.004
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', tnoise(nt, mp.outputs['Vector'], 90.0, 3.0), 0.6), math_(nt, 'MULTIPLY', rf, 0.6)), bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal']); return m


def arc_shell(name, prof, a0, a1, seg, ex, ey, m, thick=0.025, parent=None, origin=(0, 0, 0)):
    """open surface of revolution between angles a0..a1 (degrees, from +x toward +y), stretched ex/ey; solidified inward"""
    o_ = Vector(origin); vs = []; fs = []
    for r_, z_ in prof:
        for k in range(seg + 1):
            an = math.radians(a0 + (a1 - a0) * k / seg); vs.append(Vector((r_ * ex * math.cos(an), r_ * ey * math.sin(an), z_)) - o_)
    w = seg + 1
    for i in range(len(prof) - 1):
        for k in range(seg): fs.append((i * w + k, (i + 1) * w + k, (i + 1) * w + k + 1, i * w + k + 1))
    o = mesh(name, vs, fs, m, parent, loc=o_)
    sd = o.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = thick; sd.offset = -1.0; sd.use_even_offset = True
    bv = o.modifiers.new('bv', 'BEVEL'); bv.width = 0.004; bv.segments = 2; bv.limit_method = 'ANGLE'
    return o


def prof_r(prof, z):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1: return lerp(r0, r1, (z - z0) / max(1e-6, z1 - z0))

def cloth_mat(name, c, rough=0.85, sheen=0.5, weave=180.0, seed=0.0):
    """wool / linen: base colour with a fine weave bump and a little colour drift"""
    m = mat(name, c, rough, sheen=sheen); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed, seed * 0.7, seed * 0.3); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 6.0, 4.0)
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', big, 0.5), c, tuple(x * 0.7 for x in c)), b.inputs['Base Color'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = weave; wv.inputs['Distortion'].default_value = 2.0; nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(math_(nt, 'ADD', wv.outputs['Fac'], tnoise(nt, mp.outputs['Vector'], 90.0, 3.0)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


M_LINEN = cloth_mat('linen', (0.80, 0.78, 0.72), 0.8, 0.3, 240.0, 3.0)
M_REDC = cloth_mat('redcl', (0.50, 0.04, 0.03), 0.9, 0.6, 90.0, 7.0)
M_YELC = cloth_mat('yelcl', (0.75, 0.52, 0.08), 0.85, 0.5, 90.0, 8.0)
M_BERET = cloth_mat('beret', (0.02, 0.02, 0.022), 0.9, 0.6, 60.0, 1.0)
M_DUMMY = noisy(mat('dummy', (0.42, 0.40, 0.37), 0.7, sheen=0.3), 6.0, 0.15)
M_LEATHER = noisy(mat('leather', (0.06, 0.035, 0.02), 0.45, coat=0.2), 40.0, 0.2)


def steel_mat(name, base=(0.62, 0.63, 0.65), rough=0.2, seed=0.0, dark=0.0):
    """polished steel with long grind lines along the blade (x) and a few dull patches"""
    m = mat(name, base, rough, 1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2.0, 90.0, 90.0); mp.inputs['Location'].default_value = (seed, seed, 0)
    nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    grind = tnoise(nt, mp.outputs['Vector'], 1.0, 3.0); blot = tnoise(nt, coord(nt, 'Object'), 9.0, 4.0)
    nt.links.new(mixc(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', grind, 0.5), math_(nt, 'MULTIPLY', blot, 0.3 + dark)), base, tuple(c * 0.6 for c in base)), b.inputs['Base Color'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough * 0.6; mr.inputs['To Max'].default_value = rough * 1.9
    nt.links.new(math_(nt, 'ADD', math_(nt, 'MULTIPLY', grind, 0.6), math_(nt, 'MULTIPLY', blot, 0.4)), mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m


def blade_mesh(name, L, w0, t0, parent, m, point=0.12, taper=0.65, wavy=0.0, xoff=0.0):
    """a flat blade along +x from the guard (x = 0) to the point; diamond section (edges at +-y, ridge at +-z)"""
    n = 40; vs = []; fs = []
    for i in range(n + 1):
        u = i / n; w = w0 * (1 - taper * u)
        if u > 1 - point: w *= math.sqrt(max(0.0, (1 - u) / point))
        t = t0 * (1 - 0.55 * u) * (w / max(w0 * (1 - taper * u), 1e-6)) ** 0.5
        yw = wavy * w0 * math.sin(u * 60) if wavy else 0.0
        x = xoff + L * u; vs += [(x, -w + yw * 0.0, 0), (x, 0, t), (x, w, 0), (x, 0, -t)]
        vs[-4] = (x, -w - yw, 0); vs[-2] = (x, w + yw, 0)
    for i in range(n):
        for k in range(4): k2 = (k + 1) % 4; fs.append((4 * i + k, 4 * i + k2, 4 * (i + 1) + k2, 4 * (i + 1) + k))
    fs.append((3, 2, 1, 0))
    o = mesh(name, vs, fs, m, parent, smooth_=False)
    for p_ in o.data.polygons: p_.use_smooth = False
    return o


def sword(name, parent, L, w0, t0, guard, grip, pom, m_blade, m_hilt, m_grip, kind='arming', loc=(0, 0, 0)):
    """root at the middle of the crossguard; blade along +x, grip along -x; lies flat (guard along y)"""
    root = empty(name, parent, loc=loc)
    if kind == 'myth':                                   # the cartoon sword everyone pictures: huge, slab-thick, a gold hilt with a gem
        blade_mesh(f'{name}_bl', L, w0, t0, root, m_blade, point=0.18, taper=0.25)
        box(f'{name}_gd', (0.09, guard, 0.07), (-0.045, 0, 0), m_hilt, bv=0.02, parent=root)
        for s_ in (-1, 1): prim('uv_sphere', f'{name}_gb{s_}', m_hilt, root, loc=(-0.045, s_ * guard / 2, 0), segments=16, ring_count=8, radius=0.05)
        tube(f'{name}_gr', [(-0.09, 0, 0), (-0.09 - grip, 0, 0)], 0.035, m_grip, root, seg=16)
        for k in range(6): tube(f'{name}_wr{k}', [(-0.1 - grip * k / 6, 0, 0), (-0.1 - grip * (k + 0.5) / 6, 0, 0)], 0.039, m_hilt if k % 2 else m_grip, root, seg=16)
        prim('uv_sphere', f'{name}_pm', m_hilt, root, loc=(-0.09 - grip - pom * 0.8, 0, 0), segments=20, ring_count=10, radius=pom)
        prim('uv_sphere', f'{name}_gem', M_GEM, root, loc=(-0.045, 0, 0.055), segments=12, ring_count=6, radius=0.03, scale=(1, 1, 0.6))
        return root
    blade_mesh(f'{name}_bl', L, w0, t0, root, m_blade, point=0.10 if kind != 'bearing' else 0.06, taper=0.62 if kind != 'bearing' else 0.4,
               wavy=0.0)
    gz = 0.013 if kind == 'arming' else 0.016
    if kind == 'bearing':                                # a long ricasso with parrying lugs, side rings, a big flared guard
        for s_ in (-1, 1):
            tube(f'{name}_lug{s_}', [(0.24, s_ * w0 * 0.9, 0), (0.25, s_ * (w0 + 0.05), 0), (0.29, s_ * (w0 + 0.07), 0)], 0.009, m_hilt, root, seg=8)
            lathe(f'{name}_ring{s_}', [(0.045, -0.006), (0.058, -0.006), (0.058, 0.006), (0.045, 0.006)], 24, m_hilt, root, loc=(0.05, s_ * 0.06, 0)).rotation_euler = (R(90), 0, 0)
        pts = [(0.0, -guard / 2 - 0.0, 0)] + [(-0.02 * math.sin(math.pi * u), -guard / 2 + guard * u, 0) for u in (0.2, 0.5, 0.8)] + [(0.0, guard / 2, 0)]
        tube(f'{name}_gd', [(0.03, -guard / 2, 0), (-0.02, -guard / 4, 0), (-0.03, 0, 0), (-0.02, guard / 4, 0), (0.03, guard / 2, 0)], lambda u: 0.016 + 0.01 * abs(u - 0.5) * 2, m_hilt, root, seg=10)
        for s_ in (-1, 1): prim('uv_sphere', f'{name}_gk{s_}', m_hilt, root, loc=(0.035, s_ * guard / 2, 0), segments=12, ring_count=6, radius=0.03)
        box(f'{name}_blk', (0.06, 0.07, 0.04), (-0.02, 0, 0), m_hilt, bv=0.01, parent=root)
        tube(f'{name}_gr', [(-0.05, 0, 0), (-0.05 - grip, 0, 0)], lambda u: 0.02 + 0.006 * math.sin(math.pi * u), M_VELV, root, seg=14)
        for k in range(5): lathe(f'{name}_band{k}', [(0.022, -0.008), (0.028, -0.006), (0.028, 0.006), (0.022, 0.008)], 16, m_hilt, root, loc=(-0.05 - grip * (k + 0.5) / 5, 0, 0)).rotation_euler = (0, R(90), 0)
        prim('uv_sphere', f'{name}_pm', m_hilt, root, loc=(-0.05 - grip - pom * 0.9, 0, 0), segments=20, ring_count=10, radius=pom, scale=(1.35, 1, 1))
        return root
    box(f'{name}_gd', (0.022, guard, 2 * gz), (-0.011, 0, 0), m_hilt, bv=0.006, parent=root)
    for s_ in (-1, 1): prim('uv_sphere', f'{name}_gk{s_}', m_hilt, root, loc=(-0.011, s_ * guard / 2, 0), segments=10, ring_count=6, radius=gz * 1.15)
    tube(f'{name}_gr', [(-0.022, 0, 0), (-0.022 - grip, 0, 0)], lambda u: 0.0145 + 0.003 * math.sin(math.pi * u), m_grip, root, seg=14)
    p_ = lathe(f'{name}_pm', [(0.0, -0.011), (pom * 0.75, -0.011), (pom, -0.006), (pom, 0.006), (pom * 0.75, 0.011), (0.0, 0.011)], 28, m_hilt, root, loc=(-0.022 - grip - pom * 0.85, 0, 0))
    # a wheel pommel: the disc lies in the blade's plane (its faces point the same way as the blade's flats)
    return root


def low_z(root):
    """lowest point of a prop (all its meshes) in the root's own frame, as built (for resting it on a surface)"""
    bpy.context.view_layer.update(); inv = root.matrix_world.inverted(); z = 1e9
    for o in [root] + list(root.children_recursive):
        if o.type != 'MESH': continue
        mw = inv @ o.matrix_world
        dg = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = dg.to_mesh()
        for v in me.vertices: z = min(z, (mw @ v.co).z)
        dg.to_mesh_clear()
    return z


def dial_scale(name, parent, loc, pan='round', pan_w=0.62, maxv=50, H=0.95, m_body=None):
    """a big museum dial scale: iron foot and column, a white dial facing -y, a red needle, a brass pan on top.
    returns (root, needle pivot, pan top z). needle angle for v pounds: -135 + 270 v / maxv degrees from straight up"""
    root = empty(name, parent, loc=loc); mb = m_body or M_ENAM
    box(f'{name}_foot', (0.7, 0.5, 0.08), (0, 0, 0.04), M_IRONB, bv=0.015, parent=root)
    box(f'{name}_col', (0.5, 0.36, H - 0.1), (0, 0, 0.08 + (H - 0.1) / 2), mb, bv=0.02, parent=root)
    for z_ in (0.1, H - 0.04): box(f'{name}_trim{z_}', (0.53, 0.39, 0.03), (0, 0, z_), M_BRASS, bv=0.008, parent=root)
    DZ = H * 0.58; dy = -0.18
    d_ = lathe(f'{name}_bez', [(0.0, 0.0), (0.205, 0.0), (0.225, 0.012), (0.225, 0.035), (0.205, 0.04), (0.19, 0.03), (0.0, 0.03)], 48, M_BRASS, root, loc=(0, dy, DZ))
    d_.rotation_euler = (R(90), 0, 0)
    face = prim('cylinder', f'{name}_face', M_DIAL, root, loc=(0, dy - 0.031, DZ), rot=(R(90), 0, 0), vertices=48, radius=0.19, depth=0.004)
    st, nst = (2, 10) if maxv >= 40 else (1, 5)
    for k in range(maxv // st + 1):
        v = st * k; a = R(-135 + 270 * v / maxv); big = v % nst == 0; r_ = 0.165
        box(f'{name}_tk{k}', (0.004 if not big else 0.007, 0.002, 0.022 if not big else 0.04), (r_ * math.sin(a), dy - 0.035, DZ + r_ * math.cos(a)), M_INK, rot=(0, a, 0), parent=root)
        if big: text3d(f'{name}_n{v}', str(v), 0.034, (0.118 * math.sin(a), dy - 0.035, DZ + 0.118 * math.cos(a)), (R(90), 0, 0), M_INK, root, extrude=0.0005)
    text3d(f'{name}_lb', 'LB', 0.03, (0, dy - 0.035, DZ - 0.085), (R(90), 0, 0), M_RED, root, extrude=0.0005)
    piv = empty(f'{name}_piv', root, loc=(0, dy - 0.042, DZ))
    box(f'{name}_ndl', (0.007, 0.003, 0.17), (0, 0, 0.065), M_NEEDLE, parent=piv)
    tube(f'{name}_ndt', [(0, 0, -0.03), (0, 0, 0.0)], 0.006, M_NEEDLE, piv, seg=8)
    prim('cylinder', f'{name}_hub', M_BRASS, piv, loc=(0, -0.004, 0), rot=(R(90), 0, 0), vertices=20, radius=0.016, depth=0.008)
    box(f'{name}_glass', (0.39, 0.002, 0.39), (0, dy - 0.05, DZ), M_GLASSD, parent=root).hide_render = True
    top = H + 0.03
    if pan == 'round':
        lathe(f'{name}_pan', [(0.0, 0.0), (pan_w / 2 - 0.02, 0.0), (pan_w / 2, 0.015), (pan_w / 2 + 0.005, 0.04), (pan_w / 2 - 0.01, 0.04), (pan_w / 2 - 0.03, 0.012), (0.0, 0.012)], 48, M_BRASS, root, loc=(0, 0, top))
        prim('cylinder', f'{name}_stem', M_BRASS, root, loc=(0, 0, top - 0.01), vertices=16, radius=0.04, depth=0.04)
        return root, piv, top + 0.012
    box(f'{name}_pan', (pan_w, 0.34, 0.03), (0, 0, top + 0.015), M_BRASS, bv=0.01, parent=root)
    for s_ in (-1, 1): box(f'{name}_lip{s_}', (pan_w, 0.02, 0.03), (0, s_ * 0.16, top + 0.04), M_BRASS, bv=0.006, parent=root)
    prim('cylinder', f'{name}_stem', M_BRASS, root, loc=(0, 0, top - 0.01), vertices=16, radius=0.05, depth=0.04)
    return root, piv, top + 0.03


def needle_angle(v, maxv=50): return R(-135 + 270 * v / maxv)
def dress_form(name, parent, loc, head=True, legs=False, h=1.0):
    """a museum dress form on a pole: torso (shoulders at about 1.5 * h), neck, head; legs optional (for breeches)"""
    f_ = empty(name, parent, loc=loc)
    lathe(f'{name}_base', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.03), (0.03, 0.05), (0.025, 0.85 if not legs else 0.42), (0.0, 0.85 if not legs else 0.42)], 20, M_BLACK, f_)
    lathe(f'{name}_torso', [(0.0, 0.85), (0.13, 0.86), (0.155, 0.95), (0.135, 1.12), (0.16, 1.30), (0.19, 1.42), (0.12, 1.50), (0.05, 1.53), (0.0, 1.53)], 28, M_DUMMY, f_).scale = (1.0, 0.68, 1.0)
    if legs:
        for s_ in (-1, 1): lathe(f'{name}_leg{s_}', [(0.0, 0.42), (0.055, 0.42), (0.06, 0.6), (0.075, 0.8), (0.08, 0.88), (0.0, 0.88)], 16, M_DUMMY, f_, loc=(s_ * 0.075, 0, 0))
    if head:
        lathe(f'{name}_neck', [(0.0, 1.5), (0.045, 1.5), (0.04, 1.62), (0.0, 1.62)], 16, M_DUMMY, f_)
        prim('uv_sphere', f'{name}_head', M_DUMMY, f_, loc=(0, 0, 1.72), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
    return f_


def garment(name, prof, m, parent, sx=1.0, sy=0.72, seg=32, open_front=0.0):
    """a body garment as a lathe shell (radius, z) scaled to the form's oval; open_front cuts a slit at the front (-y) for a coat"""
    if open_front <= 0:
        o = lathe(name, prof, seg, m, parent); o.scale = (sx, sy, 1.0)
    else:
        o = arc_shell(name, [(r, z) for r, z in prof], 270 + open_front / 2 - 360, 270 - open_front / 2, seg, sx, sy, m, 0.008, parent)
    return o


def collar(name, parent, z, r0=0.06, r1=0.17, m=None):
    """a flat white falling-band collar: a disc ring dropping toward the front"""
    vs = []; fs = []; n = 32
    for i in range(n + 1):
        a = math.pi * (0.0 + 1.0 * i / n) + math.pi                      # front half (y < 0)
        for r_, dz in ((r0, 0.0), (r1, -0.05 - 0.04 * math.sin(a - math.pi))):
            vs.append((r_ * math.cos(a), r_ * math.sin(a) * 0.75, z + dz))
    for i in range(n): fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    o = mesh(name, vs, fs, m or M_LINEN, parent); o.modifiers.new('sd', 'SOLIDIFY').thickness = 0.006; return o
