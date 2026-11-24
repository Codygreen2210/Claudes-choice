
# ================================================================ props: iron, bronze, horn; the three helmet kinds
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

def bronze_mat(name, patina=0.45, seed=0.0):
    """old bronze: warm metal, green-blue patina in the low spots, dark grime"""
    m = mat(name, (0.55, 0.36, 0.16), 0.32, 1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed * 2.3, seed * 1.1, seed * 0.4); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 9.0, 8.0, 0.3); fine = tnoise(nt, mp.outputs['Vector'], 45.0, 4.0)
    pf = ramp_v(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', big, 0.8), math_(nt, 'MULTIPLY', fine, 0.2)), 0.62 - patina * 0.3, 0.70 - patina * 0.2)
    metal_c = mixc(nt, fine, (0.62, 0.40, 0.17), (0.40, 0.25, 0.10))
    pat_c = mixc(nt, tnoise(nt, mp.outputs['Vector'], 20.0, 5.0), (0.16, 0.34, 0.27), (0.07, 0.17, 0.12))
    nt.links.new(mixc(nt, pf, metal_c, pat_c), b.inputs['Base Color'])
    mt = nt.nodes.new('ShaderNodeMapRange'); mt.inputs['To Min'].default_value = 1.0; mt.inputs['To Max'].default_value = 0.0; nt.links.new(pf, mt.inputs['Value']); nt.links.new(mt.outputs['Result'], b.inputs['Metallic'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.28; mr.inputs['To Max'].default_value = 0.85; nt.links.new(pf, mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.003
    nt.links.new(math_(nt, 'ADD', tnoise(nt, mp.outputs['Vector'], 120.0, 3.0), math_(nt, 'MULTIPLY', pf, 0.5)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def horn_mat(name, base=(0.55, 0.45, 0.30), tip=(0.08, 0.05, 0.03)):
    """cow horn: cream at the root, dark at the tip (Generated z of the tube runs root -> tip), fine growth rings"""
    m = mat(name, base, 0.35, coat=0.4); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    g = sepz(nt, coord(nt, 'Generated'))
    zz = math_(nt, 'ADD', math_(nt, 'MULTIPLY', g.outputs['Z'], objattr(nt, 'tz')), math_(nt, 'MULTIPLY', g.outputs['X'], objattr(nt, 'tx')))
    zz = math_(nt, 'ADD', zz, objattr(nt, 'toff'))
    rings = tnoise(nt, coord(nt, 'Object'), 60.0, 2.0)
    c_ = ramp(nt, zz, [(0.0, base), (0.55, tuple(c * 0.85 for c in base)), (0.85, (0.35, 0.25, 0.15)), (1.0, tip)])
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', rings, 0.25), c_, tuple(c * 0.7 for c in base)), b.inputs['Base Color'])
    return m


def steel_mat(name, seed=0.0):
    m = iron_mat(name, 0.06, base=(0.32, 0.31, 0.30), rust_col=(0.12, 0.06, 0.03), seed=seed)
    return m


def horn_tube(name, side, parent, m, length=1.0, up=1.0):
    """a curved horn out of the side of a helmet: out, up, then forward; side = -1 / +1 (x direction); root at origin"""
    pts = []
    for i in range(16):
        u = i / 15
        pts.append(Vector((side * (0.03 + 0.13 * u - 0.02 * u * u) * length, -0.06 * u * u * length, (0.02 * u + 0.17 * u * u * up) * length)))
    o = tube(name, pts, lambda u: (0.040 - 0.036 * u ** 0.7) * length, m, parent, seg=16)
    o['tz'] = 0.75; o['tx'] = 0.25 if side > 0 else -0.25; o['toff'] = 0.25 if side < 0 else 0.0; o['tipdir'] = 1.0
    return o


DOME = [(0.0, 0.205), (0.05, 0.200), (0.09, 0.185), (0.12, 0.155), (0.14, 0.11), (0.150, 0.055), (0.152, 0.0)]


def horned_helmet(name, parent, m_metal, m_trim, m_horn, wings=False):
    """the opera / myth helmet: polished dome, brass brow band and cross straps, rivets, nose guard, two horns (or wings). base at origin, faces -y"""
    root = empty(name, parent)
    lathe(name + '_dome', DOME, 40, m_metal, root)
    lathe(name + '_brow', [(0.150, -0.005), (0.160, -0.005), (0.162, 0.04), (0.152, 0.04)], 40, m_trim, root)
    for k in range(2):
        a_ = math.pi / 2 * k
        arc = []
        for i in range(21):
            th = -math.pi / 2 + math.pi * i / 20; rr = dome_r(abs(th))                 # follow the dome surface at polar angle th
            arc.append(Vector((math.cos(a_) * rr[0] * math.copysign(1, th), math.sin(a_) * rr[0] * math.copysign(1, th), rr[1])))
        tube(f'{name}_strap{k}', arc, 0.009, m_trim, root, seg=8)
    for i in range(16):
        an = 2 * math.pi * i / 16; prim('uv_sphere', f'{name}_rv{i}', m_trim, root, loc=(0.163 * math.cos(an), 0.163 * math.sin(an), 0.018), segments=8, ring_count=5, radius=0.007)
    box(name + '_nose', (0.03, 0.012, 0.11), (0, -0.158, -0.035), m_trim, bv=0.004, parent=root)
    if wings:
        for s_ in (-1, 1):
            wr = empty(f'{name}_wing{s_}', root, loc=(s_ * 0.13, 0.0, 0.10)); wr.rotation_euler = (0, s_ * R(-25), 0)
            for f_ in range(7):
                L_ = 0.10 + 0.03 * f_; an = R(30 + 9 * f_)
                vs = [(0, 0, 0), (s_ * L_ * math.cos(an) * 0.4, 0.015, L_ * math.sin(an) * 0.4 + 0.01), (s_ * L_ * math.cos(an), 0.03 + 0.012 * f_, L_ * math.sin(an))]
                fe = mesh(f'{name}_feather{s_}{f_}', vs, [(0, 1, 2)], m_trim if f_ % 2 else m_metal, wr, smooth_=False); fe.modifiers.new('sd', 'SOLIDIFY').thickness = 0.004
    else:
        for s_ in (-1, 1):
            hr = empty(f'{name}_hroot{s_}', root, loc=(s_ * 0.118, 0.0, 0.105))
            horn_tube(f'{name}_horn{s_}', s_, hr, m_horn)
            lathe(f'{name}_hcol{s_}', [(0.036, -0.012), (0.040, 0.0), (0.040, 0.02), (0.034, 0.03)], 20, m_trim, hr).rotation_euler = (0, s_ * R(70), 0)
    return root


def dome_r(th):
    """point on the DOME profile at polar angle th (0 = top, pi/2 = rim): returns (radius, z)"""
    best = None
    for (r0, z0), (r1, z1) in zip(DOME, DOME[1:]):
        for j in range(9):
            u = j / 8; r_ = lerp(r0, r1, u); z_ = lerp(z0, z1, u); a_ = math.atan2(r_, max(z_, 1e-5) * 1.0)
            if best is None or abs(a_ - th) < best[0]: best = (abs(a_ - th), r_ + 0.006, z_ + 0.004)
    return best[1], best[2]


# ---- the Gjermundbu helmet (Norway, 950-975): rounded iron cap of four plates, brow band, two crossing bands, a small spike, the spectacle guard.
#      nine pieces, so it can lift out of the grave and come together
GJ = [(0.0, 0.235), (0.05, 0.230), (0.09, 0.212), (0.12, 0.182), (0.142, 0.135), (0.155, 0.075), (0.160, 0.02), (0.160, 0.0)]
GJ_EY = 1.16


def gjermundbu(tag, m_iron, m_dark):
    root = empty('gj_' + tag); P = {}
    for k in range(4):
        a0 = 45 + 90 * k
        P[f'plate{k}'] = arc_shell(f'{tag}_plate{k}', GJ, a0 + 1.5, a0 + 90 - 1.5, 14, 1.0, GJ_EY, m_iron, 0.006, root)
    P['brow'] = lathe(f'{tag}_brow', [(0.158, -0.004), (0.170, -0.004), (0.171, 0.036), (0.159, 0.036)], 48, m_dark, root); P['brow'].scale = (1, GJ_EY, 1)
    for k, a_ in enumerate((0.0, math.pi / 2)):
        arc = []
        for i in range(25):
            th = -math.pi / 2 + math.pi * i / 24; rr = gj_r(abs(th)); sx = math.copysign(1, th)
            arc.append(Vector((math.cos(a_) * rr[0] * sx, math.sin(a_) * rr[0] * sx * GJ_EY, rr[1])))
        P[f'band{k}'] = tube(f'{tag}_band{k}', arc, 0.012, m_dark, root, seg=6)
        P[f'band{k}'].scale = (1, 1, 1)
        for i in range(2, 24, 3): prim('uv_sphere', f'{tag}_rv{k}_{i}', m_dark, P[f'band{k}'], loc=arc[i] * 1.03, segments=8, ring_count=5, radius=0.006)
    P['spike'] = prim('cone', f'{tag}_spike', m_dark, root, loc=(0, 0, 0.255), vertices=12, radius1=0.022, radius2=0.004, depth=0.045)
    # the spectacle guard: two eye rings, a brow bar, a nose bar, hanging below the brow band at the front
    sg = empty(f'{tag}_spect', root, loc=(0, -0.172 * GJ_EY + 0.005, -0.005)); P['spect'] = sg
    for s_ in (-1, 1):
        ring = [Vector((s_ * 0.042 + 0.034 * math.cos(2 * math.pi * i / 20), -0.004 * math.cos(2 * math.pi * i / 20) ** 2, -0.045 + 0.030 * math.sin(2 * math.pi * i / 20))) for i in range(21)]
        tube(f'{tag}_eye{s_}', ring, 0.0075, m_dark, sg, seg=6, caps=False)
    tube(f'{tag}_nosebar', [(0, -0.004, 0.0), (0, -0.012, -0.065), (0, -0.016, -0.10)], lambda u: 0.009 - 0.003 * u, m_dark, sg, seg=6)
    tube(f'{tag}_browbar', [(-0.09, 0.012, -0.012), (0, -0.003, -0.012), (0.09, 0.012, -0.012)], 0.007, m_dark, sg, seg=6)
    return root, P


def gj_r(th):
    best = None
    for (r0, z0), (r1, z1) in zip(GJ, GJ[1:]):
        for j in range(9):
            u = j / 8; r_ = lerp(r0, r1, u); z_ = lerp(z0, z1, u); a_ = math.atan2(r_, max(z_, 1e-5))
            if best is None or abs(a_ - th) < best[0]: best = (abs(a_ - th), r_ + 0.008, z_ + 0.006)
    return best[1], best[2]


# ---- the Veksø helmets (Denmark, about 900 BC): bronze cap with a crest ridge, two long S-curved horns, a beaked face with big round eyes
VK = [(0.0, 0.175), (0.06, 0.170), (0.10, 0.150), (0.13, 0.112), (0.146, 0.06), (0.150, 0.0)]


def vekso(tag, m_br, m_br2):
    root = empty('vk_' + tag)
    lathe(f'{tag}_cap', VK, 40, m_br, root)
    lathe(f'{tag}_rim', [(0.148, -0.006), (0.160, -0.006), (0.160, 0.012), (0.148, 0.012)], 40, m_br2, root)
    # crest ridge, front to back
    cr = []
    for i in range(21):
        th = -math.pi / 2 * 0.92 + math.pi * 0.92 * i / 20; r_ = 0.175 + 0.02 * math.cos(th) ** 2
        cr.append(Vector((0, math.sin(th) * r_ * 0.86, math.cos(th) * r_ * 0.98)))
    tube(f'{tag}_crest', cr, lambda u: 0.010 + 0.010 * math.sin(math.pi * u), m_br2, root, seg=8)
    # the face: a beak (nose) and two big eyes as raised rings with bosses
    face = empty(f'{tag}_face', root, loc=(0, -0.148, 0.07)); face.rotation_euler = (R(-15), 0, 0)
    tube(f'{tag}_beak', [(0, 0.0, 0.03), (0, -0.015, -0.01), (0, -0.006, -0.05)], lambda u: 0.012 - 0.008 * u, m_br2, face, seg=8)
    for s_ in (-1, 1):
        ring = [Vector((s_ * 0.042 + 0.024 * math.cos(2 * math.pi * i / 20), -0.002, 0.008 + 0.024 * math.sin(2 * math.pi * i / 20))) for i in range(21)]
        tube(f'{tag}_eyer{s_}', ring, 0.005, m_br2, face, seg=6, caps=False)
        prim('uv_sphere', f'{tag}_eyeb{s_}', m_br2, face, loc=(s_ * 0.042, -0.006, 0.008), segments=12, ring_count=8, radius=0.012)
    # the horns: out of the sides, up, then out and forward in a long S (the lyre shape), with little knob tips
    for s_ in (-1, 1):
        pts = []
        for i in range(24):
            u = i / 23
            x = s_ * (0.13 + 0.10 * u + 0.12 * math.sin(math.pi * u * 0.9) * 0.6)
            y = -0.10 * math.sin(math.pi * u) * 0.5 - 0.06 * u
            z = 0.06 + 0.46 * u - 0.06 * math.sin(math.pi * u * 1.6) * u
            pts.append(Vector((x, y, z)))
        tube(f'{tag}_horn{s_}', pts, lambda u: 0.038 - 0.022 * u, m_br, root, seg=14)
        prim('uv_sphere', f'{tag}_knob{s_}', m_br2, root, loc=pts[-1] + Vector((0, 0, 0.01)), segments=12, ring_count=8, radius=0.022)
        for j in (4, 9, 14): tube(f'{tag}_hring{s_}{j}', [pts[j] + Vector((0.032 * math.cos(2 * math.pi * i / 12), 0.018 * math.sin(2 * math.pi * i / 12), 0)) for i in range(13)], 0.004, m_br2, root, seg=5, caps=False)
    return root
