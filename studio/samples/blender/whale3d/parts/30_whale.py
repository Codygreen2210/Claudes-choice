
# ================================================================ the humpback: lofted from real proportions (about 14 m long), a hinged lower jaw and
# pleated throat pouch that balloons when it gulps, baleen hanging from the upper jaw, long white flippers, knobby tubercles on the head, flukes.
# Local frame: the snout tip is at x = 0, the whale faces +x, the tail runs to -x; z is up. Shape keys open the jaw, swell the pouch, bend the tail.
def interp_tab(tab, s, col):
    """smooth (Catmull-Rom) through the table, so the body has no ribs at the stations"""
    n = len(tab)
    if s <= tab[0][0]: return tab[0][col]
    if s >= tab[-1][0]: return tab[-1][col]
    i = max(j for j in range(n - 1) if tab[j][0] <= s)
    x0, x1 = tab[i][0], tab[i + 1][0]; u = (s - x0) / (x1 - x0)
    p1, p2 = tab[i][col], tab[i + 1][col]
    p0 = tab[i - 1][col] if i > 0 else p1 - (p2 - p1); p3 = tab[i + 2][col] if i + 2 < n else p2 + (p2 - p1)
    h0 = (x1 - tab[i - 1][0]) if i > 0 else 2 * (x1 - x0); h1_ = (tab[i + 2][0] - x0) if i + 2 < n else 2 * (x1 - x0)
    m1 = (p2 - p0) / h0 * (x1 - x0); m2 = (p3 - p1) / h1_ * (x1 - x0)
    u2, u3 = u * u, u * u * u
    return (2 * u3 - 3 * u2 + 1) * p1 + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2 + (u3 - u2) * m2

def xray_mix(m, glow=(0.35, 0.75, 1.0), prop='xr'):
    """blend the surface toward a see-through glowing x-ray shell, driven by the object's property 'xr' (0..1)"""
    nt = m.node_tree; out_ = nt.nodes['Material Output']; src = out_.inputs['Surface'].links[0].from_socket
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*glow, 1)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    nt.links.new(math_(nt, 'MULTIPLY', math_(nt, 'POWER', lw.outputs['Facing'], 2.2), 2.4), em.inputs['Strength'])
    add = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(objattr(nt, prop), mx.inputs['Fac'])
    nt.links.new(src, mx.inputs[1]); nt.links.new(add.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out_.inputs['Surface'])
    return m

def whale_skin(name, dark, light, belly_z, pleats=False, rough=0.38):
    """dark back, a mottled white belly below belly_z (object space), wet coat; pleats: long grooves down the throat"""
    m = mat(name, dark, rough, coat=0.25); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    co = coord(nt, 'Object'); sx = sepz(nt, co)
    nz = tnoise(nt, co, 0.9, 8.0, 0.4); nz2 = tnoise(nt, co, 6.0, 4.0)
    edge = math_(nt, 'ADD', sx.outputs['Z'], math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', nz, 0.5), 0.7))
    wfac = math_(nt, 'SUBTRACT', 1.0, ramp_v(nt, edge, belly_z - 0.08, belly_z + 0.08))
    blot = ramp_v(nt, nz2, 0.62, 0.70)                                  # dark blotches on the white
    wfac = math_(nt, 'MULTIPLY', wfac, math_(nt, 'SUBTRACT', 1.0, math_(nt, 'MULTIPLY', blot, 0.85)))
    mott = mixc(nt, math_(nt, 'MULTIPLY', ramp_v(nt, tnoise(nt, co, 3.0, 6.0), 0.45, 0.75), 0.35), dark, tuple(c * 1.9 for c in dark))
    col = mixc(nt, wfac, mott, light)
    # scars: thin pale rake marks (orca teeth, rope) in patches
    sc = nt.nodes.new('ShaderNodeTexWave'); sc.wave_type = 'BANDS'; sc.bands_direction = 'Z'; sc.inputs['Scale'].default_value = 6.0
    sc.inputs['Distortion'].default_value = 2.0; sc.inputs['Detail'].default_value = 1.0; nt.links.new(co, sc.inputs['Vector'])
    scar = math_(nt, 'MULTIPLY', ramp_v(nt, sc.outputs['Fac'], 0.975, 0.995), ramp_v(nt, tnoise(nt, co, 0.35, 2.0), 0.69, 0.72))
    col = mixc(nt, math_(nt, 'MULTIPLY', scar, 0.7), col, (0.55, 0.56, 0.58))
    nt.links.new(col, b.inputs['Base Color'])
    if pleats:
        wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 1.35
        wv.inputs['Distortion'].default_value = 0.25; wv.inputs['Detail'].default_value = 2.0; nt.links.new(co, wv.inputs['Vector'])
        gro = ramp_v(nt, wv.outputs['Fac'], 0.0, 0.18)                 # thin grooves
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.55; bp.inputs['Distance'].default_value = 0.03
        nt.links.new(math_(nt, 'MULTIPLY', gro, wfac), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
        nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1.0, gro), math_(nt, 'MULTIPLY', wfac, 0.55)), col, tuple(c * 0.45 for c in light)), b.inputs['Base Color'])
    else:
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; bp.inputs['Distance'].default_value = 0.02
        nt.links.new(tnoise(nt, co, 14.0, 6.0), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(math_(nt, 'ADD', rough, math_(nt, 'MULTIPLY', nz2, 0.12)), b.inputs['Roughness'])
    return xray_mix(m)

# ---- proportions (s = 0 snout tip .. 1 fluke notch): half-width, top, belly, mouth line
HB_L = 14.0
HB_TAB = [  # s,   ry,   top,   belly,  mouth
    (0.000, 0.30, 0.02, -0.10, -0.10), (0.020, 0.54, 0.13, -0.16, -0.16), (0.060, 0.76, 0.30, -0.24, -0.24), (0.120, 0.96, 0.50, -0.32, -0.32),
    (0.190, 1.16, 0.72, -0.40, -0.40), (0.250, 1.38, 0.95, -0.95, -0.46), (0.300, 1.56, 1.12, -1.40, -0.48), (0.360, 1.68, 1.24, -1.66, -0.48),
    (0.450, 1.72, 1.28, -1.68, -0.48), (0.550, 1.58, 1.24, -1.50, -0.48), (0.650, 1.22, 1.10, -1.16, -0.48), (0.750, 0.76, 0.92, -0.86, -0.48),
    (0.850, 0.38, 0.70, -0.62, -0.48), (0.930, 0.20, 0.44, -0.42, -0.48), (1.000, 0.08, 0.12, -0.12, -0.48)]
JAW_TAB = [  # s,   ry,   bottom  (the lower jaw and pleated pouch; it runs a little past the snout and tucks into the belly by s 0.58)
    (-0.012, 0.36, -0.20), (0.030, 0.68, -0.48), (0.090, 0.96, -0.82), (0.160, 1.22, -1.10), (0.240, 1.44, -1.40), (0.320, 1.62, -1.64),
    (0.420, 1.72, -1.715), (0.500, 1.62, -1.62), (0.580, 1.32, -1.22)]
HINGE_S = 0.255
def hb_mouth(s): return interp_tab(HB_TAB, s, 4)
def hb_upper_section(s, nseg):
    ry, zt, zb, zm = (interp_tab(HB_TAB, s, k) for k in (1, 2, 3, 4))
    flat = 1.0 - smooth(0.22, 0.33, s)                                   # the head's underside is the palate (flat at the mouth line)
    bot = lerp(zb, zm, flat); zc = (zt + bot) / 2 if flat < 0.5 else lerp(zm, 0.0, smooth(0.25, 0.4, s))
    pts = []
    for k in range(nseg):
        th = 2 * math.pi * k / nseg; c_, s_ = math.cos(th), math.sin(th)
        y_ = ry * (abs(c_) ** 0.82) * (1 if c_ >= 0 else -1)
        if s_ >= 0: z_ = zc + (zt - zc) * (s_ ** 0.9)
        else:
            sb = (-s_) ** (0.9 if flat < 0.5 else 0.25)
            z_ = zc - (zc - bot) * sb
        if s_ < 0 and flat > 0.5: y_ *= 1.0 - 0.04 * (-s_)
        pts.append((y_, z_))
    return pts


# ---- small surface details built right into a mesh's vertex list (so shape keys carry them): domes and barnacles
def add_dome(vs, fs, c, n, r, h, seg=10, rings=4):
    """a knob (tubercle) of radius r rising h out of the surface at c along normal n; returns its face indices"""
    c = Vector(c); n = Vector(n).normalized(); a_ = n.orthogonal().normalized(); b_ = n.cross(a_)
    f0 = len(fs); b0 = len(vs)
    for i in range(rings):
        u = i / rings; rr = r * math.cos(u * math.pi / 2); zz = h * math.sin(u * math.pi / 2) - h * 0.45
        for k in range(seg):
            th = 2 * math.pi * k / seg; vs.append(tuple(c + (a_ * math.cos(th) + b_ * math.sin(th)) * rr + n * zz))
    vs.append(tuple(c + n * (h * 0.55))); top = len(vs) - 1
    for i in range(rings - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((b0 + i * seg + k, b0 + i * seg + k2, b0 + (i + 1) * seg + k2, b0 + (i + 1) * seg + k))
    for k in range(seg): fs.append((b0 + (rings - 1) * seg + k, b0 + (rings - 1) * seg + (k + 1) % seg, top))
    return list(range(f0, len(fs)))
def add_barnacle(vs, fs, c, n, r, h, seg=9):
    """an acorn barnacle: a ridged cone with a dark slot in its top"""
    c = Vector(c); n = Vector(n).normalized(); a_ = n.orthogonal().normalized(); b_ = n.cross(a_)
    f0 = len(fs); b0 = len(vs)
    prof = [(r, -h * 0.4), (r * 0.98, 0.0), (r * 0.62, h * 0.85), (r * 0.42, h), (r * 0.30, h * 0.72)]
    for (rr, zz) in prof:
        for k in range(seg):
            th = 2 * math.pi * k / seg; rk = rr * (1 + 0.12 * math.cos(th * 3 + r * 40))
            vs.append(tuple(c + (a_ * math.cos(th) + b_ * math.sin(th)) * rk + n * zz))
    vs.append(tuple(c + n * h * 0.45)); bot = len(vs) - 1
    for i in range(len(prof) - 1):
        for k in range(seg): k2 = (k + 1) % seg; fs.append((b0 + i * seg + k, b0 + i * seg + k2, b0 + (i + 1) * seg + k2, b0 + (i + 1) * seg + k))
    L_ = len(prof) - 1
    for k in range(seg): fs.append((b0 + L_ * seg + k, b0 + L_ * seg + (k + 1) % seg, bot))
    return list(range(f0, len(fs)))

def build_humpback(name, mbody, mjaw, mmouth, mbaleen, mfin, mbarn, mfringe):
    root = empty(name + '_root')
    L = HB_L; NS, NA = 170, 84
    rr = random.Random(4)
    # ---------------- upper body (skull, back, tail stock), with knobs on the rostrum, a splash guard, blowholes
    ss = [(0.5 * (1 - math.cos(math.pi * i / (NS - 1)))) ** 1.15 for i in range(NS)]
    vs = []; fs = []
    for s in ss:
        for (y_, z_) in hb_upper_section(s, NA): vs.append((-s * L, y_, z_))
    for i in range(NS - 1):
        for k in range(NA): k2 = (k + 1) % NA; fs.append((i * NA + k, i * NA + k2, (i + 1) * NA + k2, (i + 1) * NA + k))
    vs.append((0.02, 0, -0.04)); tip = len(vs) - 1
    for k in range(NA): fs.append((tip, (k + 1) % NA, k))
    tl = len(vs); vs.append((-L - 0.02, 0, 0.0))
    for k in range(NA): fs.append(((NS - 1) * NA + k, (NS - 1) * NA + (k + 1) % NA, tl))
    nbase = len(fs); barn_faces = []
    def top_pt(s, frac):
        ry, zt, zm = interp_tab(HB_TAB, s, 1), interp_tab(HB_TAB, s, 2), interp_tab(HB_TAB, s, 4)
        y_ = ry * frac; zc = zm if s < 0.25 else 0.0
        z_ = zc + (zt - zc) * max(0.0, 1 - abs(frac) ** 2.2) ** 0.5
        return Vector((-s * L, y_, z_)), Vector((0, y_ / max(ry, 1e-3) * 0.8, 1.0)).normalized()
    # tubercles: a row down the middle of the rostrum and scattered rows either side
    for j in range(64):
        s = 0.012 + 0.215 * (j / 63) if j < 18 else 0.012 + 0.21 * rr.random()
        frac = 0.0 if j < 18 else rr.choice((-1, 1)) * rr.uniform(0.25, 0.9)
        p, n = top_pt(s, frac); r_ = 0.045 + 0.03 * rr.random()
        add_dome(vs, fs, p, n, r_, r_ * 0.9)
    # splash guard ridge in front of the blowholes
    for j in range(9):
        p, n = top_pt(0.198, (j - 4) / 14.0); add_dome(vs, fs, p + Vector((0.02 * abs(j - 4), 0, 0)), n, 0.09, 0.06, seg=8, rings=3)
    body = mesh(name + '_body', vs, fs, mbody, root); subsurf(body, 2)
    # ---------------- lower jaw + pleated pouch: real grooves cut into the hull, knobs and barnacles on the chin, floor ridges
    NJ, NB, NF = 120, 176, 30
    js = [lerp(JAW_TAB[0][0], JAW_TAB[-1][0], (i / (NJ - 1)) ** 1.1) for i in range(NJ)]
    jv = []; jf = []; mi = []
    NP = 44
    for s in js:
        ry = interp_tab(JAW_TAB, s, 1); zb = interp_tab(JAW_TAB, s, 2); zm = hb_mouth(max(s, 0.0)) - 0.02 * (1 - smooth(0.0, 0.05, s))
        fade = smooth(0.02, 0.07, s) * (1 - smooth(0.46, 0.56, s))
        ring = []
        for k in range(NB + 1):
            th = math.pi * k / NB; c_, s_ = math.cos(th), math.sin(th)
            y_ = ry * (abs(c_) ** 0.75) * (1 if c_ >= 0 else -1); z_ = zm - (zm - zb) * (s_ ** 0.8)
            vent = smooth(0.25, 0.55, s_)                                  # grooves only on the underside
            g = (0.5 + 0.5 * math.cos(2 * math.pi * NP * th / math.pi)) ** 8
            zc = (zm + zb) / 2; rad = Vector((0, y_, z_ - zc)); rl = rad.length or 1.0
            d = 0.038 * g * vent * fade
            ring.append((y_ - y_ / rl * d, z_ - (z_ - zc) / rl * d))
        dip = 0.28 * smooth(0.0, 0.12, s) * (1 - smooth(0.38, 0.55, s))
        for k in range(1, NF):
            u = k / NF; y_ = -ry * 0.74 * math.cos(math.pi * u)
            ridge = 0.015 * math.sin(u * math.pi * 9) * smooth(0.04, 0.12, s)        # the floor of the mouth: soft ridges
            ring.append((y_, zm - 0.04 - 0.05 * (1 - smooth(0.0, 0.05, s)) - dip * math.sin(math.pi * u) ** 1.5 + ridge))
        for (y_, z_) in ring: jv.append((-s * L, y_, z_))
    NR = NB + 1 + NF - 1
    for i in range(NJ - 1):
        for k in range(NR):
            k2 = (k + 1) % NR; jf.append((i * NR + k, i * NR + k2, (i + 1) * NR + k2, (i + 1) * NR + k)); mi.append(1 if (NB < k < NR - 1 and js[i] > 0.045) else 0)
    jf.append(tuple(range(NR))[::-1]); mi.append(0); jf.append(tuple((NJ - 1) * NR + k for k in range(NR))); mi.append(0)
    def jaw_pt(s, th):
        ry = interp_tab(JAW_TAB, s, 1); zb = interp_tab(JAW_TAB, s, 2); zm = hb_mouth(max(s, 0.0))
        c_, s_ = math.cos(th), math.sin(th); y_ = ry * (abs(c_) ** 0.75) * (1 if c_ >= 0 else -1); z_ = zm - (zm - zb) * (s_ ** 0.8)
        zc = (zm + zb) / 2; return Vector((-s * L, y_, z_)), Vector((0, y_, z_ - zc)).normalized()
    for j in range(40):                                                    # knobs along the lower lip and on the chin
        s = 0.0 + 0.07 * rr.random(); th = rr.choice((rr.uniform(0.08, 0.5), rr.uniform(2.64, 3.06)))
        p, n = jaw_pt(s, th); r_ = 0.04 + 0.025 * rr.random(); f_ = add_dome(jv, jf, p, n, r_, r_ * 0.9); mi += [0] * len(f_)
    for j in range(130):                                                   # barnacle clusters on the chin
        cl = j // 13; cs_ = 0.002 + 0.035 * h1(cl * 3.1); ct_ = 1.57 + 0.9 * (h1(cl * 7.7) - 0.5) * 2.0
        s = max(-0.01, cs_ + 0.012 * (rr.random() - 0.5)); th = clamp(ct_ + 0.12 * (rr.random() - 0.5), 0.1, math.pi - 0.1)
        p, n = jaw_pt(s, th); r_ = 0.018 + 0.026 * rr.random(); f_ = add_barnacle(jv, jf, p, n, r_, r_ * 1.1); mi += [2] * len(f_)
    jaw = mesh(name + '_jaw', jv, jf, mjaw, root); jaw.data.materials.append(mmouth); jaw.data.materials.append(mbarn)
    for p_, m_ in zip(jaw.data.polygons, mi): p_.material_index = m_
    subsurf(jaw, 1)
    hx = -HINGE_S * L; hz = hb_mouth(HINGE_S)
    jaw.shape_key_add(name='Basis'); ko = jaw.shape_key_add(name='open'); ke = jaw.shape_key_add(name='engulf')
    ang = R(58)
    for i, v in enumerate(jaw.data.vertices):
        x_, y_, z_ = v.co; s = -x_ / L
        w = 1.0 - smooth(0.24, 0.50, s); a_ = ang * w; dx, dz = x_ - hx, z_ - hz
        ko.data[i].co = Vector((hx + dx * math.cos(a_) + dz * math.sin(a_), y_ * (1 + 0.05 * w), hz - dx * math.sin(a_) + dz * math.cos(a_)))
        bal = smooth(0.06, 0.14, s) * (1 - smooth(0.42, 0.58, s))
        low = clamp((hb_mouth(max(s, 0)) - z_) / 1.2, 0, 1)
        edge = min(1.0, abs(y_) / max(interp_tab(JAW_TAB, s, 1), 1e-3)) ** 4
        ke.data[i].co = Vector((x_, y_ * (1 + 0.32 * bal * low), z_ - bal * (0.95 * (1 - edge) + 0.6 * low ** 1.2)))
    # ---------------- baleen: ~300 plates a side, each curved, dark on the outside and fading to a cream fringe of bristles inside
    bv = []; bf = []; fv = []; ff = []
    NBAL = 300
    for side in (1, -1):
        for j in range(NBAL):
            s = 0.012 + 0.245 * j / (NBAL - 1); x_ = -s * L; ry = interp_tab(HB_TAB, s, 1) * 0.80; zm = hb_mouth(s)
            ln = 0.16 + 0.60 * math.sin(math.pi * min(1.0, (s - 0.01) / 0.25)) ** 0.7; wd = 0.10 + 0.12 * smooth(0.0, 0.2, s)
            ryj = interp_tab(JAW_TAB, s, 1); zbj = interp_tab(JAW_TAB, s, 2); cth = min(1.0, (ry / max(ryj, 1e-3)) ** (1 / 0.75))
            room = (zm - zbj) * (math.sqrt(max(0.0, 1 - cth * cth)) ** 0.8) - 0.06        # stay inside the shut lower jaw
            ln = max(0.05, min(ln, room))
            p0 = len(bv); bend = 0.03 * math.sin(j * 0.7)
            for (u, v) in ((0, 0), (1, 0), (1, 0.5), (0.95, 1), (0, 1)):
                bv.append((x_ + bend * v, side * (ry - wd * u * (1 - 0.45 * v)), zm + 0.02 - ln * v * (1 - 0.18 * u)))
            q = [p0, p0 + 1, p0 + 2, p0 + 3, p0 + 4]; bf.append(tuple(q) if side > 0 else tuple(q[::-1]))
            # the fringe: fine bristles hanging off the inner edge
            for b in range(4):
                v0 = 0.15 + 0.2 * b; yb = side * (ry - wd * (1 - 0.45 * v0)); zb_ = zm + 0.02 - ln * v0 * 0.82
                q0 = len(fv); fv += [(x_, yb, zb_), (x_ + 0.012, yb, zb_), (x_ + 0.012, yb - side * 0.10, zb_ - 0.10), (x_, yb - side * 0.10, zb_ - 0.10)]
                ff.append((q0, q0 + 1, q0 + 2, q0 + 3))
    baleen = mesh(name + '_baleen', bv, bf, mbaleen, root, smooth_=False)
    sol = baleen.modifiers.new('th', 'SOLIDIFY'); sol.thickness = 0.006
    fringe = mesh(name + '_fringe', fv, ff, mfringe, root, smooth_=False)
    # ---------------- eyes with lids, blowholes
    eyes = []
    EYEM = mat('whale_eye', (0.035, 0.018, 0.01), 0.05, coat=1.0)
    for side in (1, -1):
        s = 0.262; y_ = side * interp_tab(HB_TAB, s, 1) * 0.93; z_ = hb_mouth(s) + 0.2
        e = prim('uv_sphere', f'{name}_eye{side}', EYEM, root, loc=(-s * L, y_, z_), radius=0.07, segments=20, ring_count=12)
        for k_, (dz, sc) in enumerate(((0.045, (1.25, 0.55, 0.55)), (-0.045, (1.2, 0.5, 0.45)))):
            lid = prim('uv_sphere', f'{name}_lid{side}{k_}', mbody, root, loc=(-s * L, y_ - side * 0.025, z_ + dz), radius=0.12, segments=18, ring_count=10); lid.scale = sc
            eyes.append(lid)
        eyes.append(e)
    for side in (1, -1):
        s = 0.212; z_ = interp_tab(HB_TAB, s, 2)
        bh = prim('uv_sphere', f'{name}_blow{side}', mat('blowhole', (0.005, 0.005, 0.006), 0.4), root, loc=(-s * L, side * 0.09, z_ + 0.004), radius=0.13, segments=16, ring_count=8)
        bh.scale = (1.0, 0.22, 0.10); bh.rotation_euler = (0, 0, side * R(14)); eyes.append(bh)
    # ---------------- dorsal fin: a small hooked fin on a hump
    s0 = 0.64; zt0 = interp_tab(HB_TAB, s0, 2); dvs = []; dfs = []
    for i in range(12):
        u = i / 11; x0 = -s0 * L + 0.7 - 1.5 * u; h_ = 0.48 * math.sin(math.pi * u ** 0.8) ** 1.4; th_ = 0.13 * (1 - u * 0.6)
        for (yy, zz) in ((-th_, -0.1), (0, h_), (th_, -0.1), (0, -0.3)): dvs.append((x0 - 0.18 * (zz / 0.5) ** 2 * (zz > 0), yy, zt0 + zz))
    for i in range(11):
        for k in range(4): k2 = (k + 1) % 4; dfs.append((i * 4 + k, i * 4 + k2, (i + 1) * 4 + k2, (i + 1) * 4 + k))
    dfs.append((0, 1, 2, 3)[::-1]); dfs.append(tuple(44 + k for k in range(4)))
    dorsal = mesh(name + '_dorsal', dvs, dfs, mbody, root); subsurf(dorsal, 2)
    # ---------------- flippers: a third of the body long, a hydrofoil section, a row of knobs on the leading edge, barnacles near the tip
    fins = {}
    for side in (1, -1):
        piv = empty(f'{name}_finpiv{side}', root, loc=(-0.29 * L, side * 1.36, -1.0))
        n = 64; fv_ = []; ff_ = []; sec = 12
        for i in range(n):
            u = i / (n - 1); span = 4.6 * u
            knob = sum(math.exp(-((u - kk / 11.0) / 0.018) ** 2) for kk in range(2, 11)) * 0.07 * smooth(0.1, 0.25, u)
            chord = lerp(1.30, 0.30, u ** 1.1); th = lerp(0.17, 0.04, u)
            for k in range(sec):
                a_ = 2 * math.pi * k / sec; cx = -0.5 * (1 - math.cos(a_)); cz = th * 0.5 * math.sin(a_) * (1 - 0.6 * (-cx)) * 1.6
                lead = knob if k in (0, 1, sec - 1) else 0.0
                fv_.append((cx * chord + 0.25 * chord + lead, side * span, cz))
        for i in range(n - 1):
            for k in range(sec):
                k2 = (k + 1) % sec; q = (i * sec + k, i * sec + k2, (i + 1) * sec + k2, (i + 1) * sec + k); ff_.append(q if side > 0 else q[::-1])
        cap = tuple((n - 1) * sec + k for k in range(sec)); ff_.append(cap if side > 0 else cap[::-1])
        fmi = [0] * len(ff_)
        for j in range(26):
            u = rr.uniform(0.55, 0.98); chord = lerp(1.30, 0.30, u ** 1.1)
            p = Vector((0.25 * chord + 0.01, side * 4.6 * u, rr.uniform(-0.02, 0.02))); n_ = Vector((1, 0, rr.uniform(-0.6, 0.6))).normalized()
            r_ = 0.014 + 0.018 * rr.random(); f_ = add_barnacle(fv_, ff_, p, n_, r_, r_ * 1.1); fmi += [1] * len(f_)
        fo = mesh(f'{name}_fin{side}', fv_, ff_, mfin, piv); fo.data.materials.append(mbarn)
        for p_, m_ in zip(fo.data.polygons, fmi): p_.material_index = m_
        subsurf(fo, 1)
        fo.rotation_euler = (R(-16) * side, R(22), R(-52) * side)
        fins[side] = piv
    # ---------------- flukes: swept wings, a deep notch, a ragged trailing edge
    fpiv = empty(name + '_flukepiv', root, loc=(-L + 0.15, 0, 0.0))
    n = 56; fv_ = []; ff_ = []; sec = 10
    for side in (1, -1):
        b0 = len(fv_)
        for i in range(n):
            u = i / (n - 1); span = 2.3 * u; sweep = -0.6 * u ** 1.5; chord = lerp(1.05, 0.28, u ** 1.2)
            ser = (0.045 * abs(math.sin(u * 2 * math.pi * 11)) + 0.02 * h1(i * 1.7)) * smooth(0.04, 0.12, u); th = lerp(0.15, 0.03, u)
            notch = 0.22 * (1 - smooth(0.0, 0.08, u))
            for k in range(sec):
                a_ = 2 * math.pi * k / sec; cx = -0.5 * (1 - math.cos(a_)); cz = th * 0.5 * math.sin(a_) * 1.5
                fv_.append((sweep + cx * chord + 0.25 - (ser + notch) * (-cx) ** 3, side * (0.04 + span), cz))
        for i in range(n - 1):
            for k in range(sec):
                k2 = (k + 1) % sec; q = (b0 + i * sec + k, b0 + i * sec + k2, b0 + (i + 1) * sec + k2, b0 + (i + 1) * sec + k); ff_.append(q if side > 0 else q[::-1])
        cap = tuple(b0 + (n - 1) * sec + k for k in range(sec)); ff_.append(cap if side > 0 else cap[::-1])
    for k in range(sec):
        k2 = (k + 1) % sec; ff_.append((k2, k, n * sec + k, n * sec + k2))
    flukes = mesh(name + '_flukes', fv_, ff_, mfin, fpiv); subsurf(flukes, 1)
    # body shape keys: the tail bends up / down (the flukes follow)
    body.shape_key_add(name='Basis'); ku = body.shape_key_add(name='tail_up')
    for i, v in enumerate(body.data.vertices):
        s = -v.co.x / L; ku.data[i].co = v.co + Vector((0, 0, tail_bend(s)))
    return dict(root=root, body=body, jaw=jaw, baleen=baleen, fringe=fringe, fins=fins, fpiv=fpiv, flukes=flukes, eyes=eyes, dorsal=dorsal, L=L)

def tail_bend(s): return 1.1 * smooth(0.42, 1.0, s) ** 1.8          # how far the body lifts at s for tail_up = 1 (m)
def tail_slope(s, ds=0.01): return (tail_bend(min(s + ds, 1)) - tail_bend(s - ds)) / (2 * ds * HB_L)

HB_DARK = (0.030, 0.034, 0.040); HB_WHITE = (0.80, 0.82, 0.84)
HBM = whale_skin('hb_skin', HB_DARK, HB_WHITE, -1.05)
HBJ = whale_skin('hb_jaw', HB_DARK, HB_WHITE, -0.85, pleats=True)
HBMOUTH = mat('hb_mouth', (0.30, 0.17, 0.17), 0.6, coat=0.3); noisy(HBMOUTH, 6.0, 0.35, 0.1); xray_mix(HBMOUTH)
HBBAL = mat('hb_baleen', (0.035, 0.03, 0.028), 0.75); nt = HBBAL.node_tree
nt.links.new(mixc(nt, ramp_v(nt, sepz(nt, coord(nt, 'Generated')).outputs['Z'], 0.0, 1.0), (0.30, 0.26, 0.20), (0.025, 0.022, 0.02)), nt.nodes['Principled BSDF'].inputs['Base Color'])
xray_mix(HBBAL)
HBFRINGE = mat('hb_fringe', (0.62, 0.55, 0.42), 0.9, trans=0.3, sheen=0.6); xray_mix(HBFRINGE)
HBBARN = mat('hb_barnacle', (0.72, 0.70, 0.64), 0.85); noisy(HBBARN, 60.0, 0.45, 0.1); xray_mix(HBBARN)
HBFIN = whale_skin('hb_fin', (0.06, 0.065, 0.07), (0.86, 0.87, 0.88), 0.03)
HB = build_humpback('hb', HBM, HBJ, HBMOUTH, HBBAL, HBFIN, HBBARN, HBFRINGE)

def humpback_set(loc, yaw=0.0, pitch=0.0, roll=0.0, open_=0.0, engulf=0.0, tail=0.0, fin=0.0, xr=0.0, scale=1.0):
    r_ = HB['root']; r_.location = loc; r_.rotation_mode = 'XYZ'; r_.rotation_euler = (roll, -pitch, yaw); r_.scale = (scale,) * 3
    HB['jaw'].data.shape_keys.key_blocks['open'].value = open_
    HB['jaw'].data.shape_keys.key_blocks['engulf'].value = engulf
    HB['body'].data.shape_keys.key_blocks['tail_up'].slider_min = -1.0
    HB['body'].data.shape_keys.key_blocks['tail_up'].value = tail
    tb = tail_bend(1.0) * tail; ang = math.atan(tail_slope(0.985) * tail)
    HB['fpiv'].location = (-HB_L + 0.15, 0, tb); HB['fpiv'].rotation_euler = (0, -ang * 1.4, 0)
    for side, piv in HB['fins'].items(): piv.rotation_euler = (side * R(14) * fin, R(6) * fin, side * R(8) * fin)
    for o in [c for c in HB['root'].children_recursive if c.type == 'MESH']:
        o['xr'] = xr
    for o in [HB['baleen'], HB['fringe']]: o.hide_render = xr > 0.2 or open_ < 0.04
    for o in HB['eyes']: o.hide_render = xr > 0.2
