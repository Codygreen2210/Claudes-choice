
# ================================================================ the iron maiden (built in parts so it can fly apart and come back together)
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
    return prof[-1][0] if z > prof[-1][1] else prof[0][0]


MAIDEN_PROF = [(0.40, 0.10), (0.445, 0.16), (0.455, 0.30), (0.44, 0.52), (0.41, 0.80), (0.375, 1.08), (0.362, 1.26), (0.385, 1.40), (0.39, 1.48)]
MAIDEN_TOP = [(0.39, 1.48), (0.375, 1.53), (0.31, 1.58), (0.21, 1.615), (0.13, 1.63)]
EX, EY = 1.0, 0.80
DOOR_A = 60.0                                     # each door spans 60 degrees of the front


def build_maiden(tag, m_iron, m_dark=None, base_m=None, spikes=True, head=True, face_rust=0.4):
    """returns dict: root (feet at origin, facing -y), parts {name: obj} parented to root, doors (L, R) with hinge origins"""
    root = empty('maiden_' + tag); P = {}
    m_dark = m_dark or m_iron
    # the back shell (240 degrees behind the doors) and the doors (front 120 degrees, split down the middle)
    back = arc_shell(f'{tag}_back', MAIDEN_PROF, -90 + DOOR_A, 270 - DOOR_A, 40, EX, EY, m_iron, 0.03, root); P['back'] = back
    doors = []
    for side, (a0, a1, ah) in (('L', (270 - DOOR_A, 270.0, 270 - DOOR_A)), ('R', (-90.0, -90 + DOOR_A, -90 + DOOR_A))):
        rh = 0.455; hp = Vector((rh * EX * math.cos(math.radians(ah)), rh * EY * math.sin(math.radians(ah)), 0.0))
        dpiv = empty(f'{tag}_door{side}', root, loc=hp); P['door' + side] = dpiv
        d = arc_shell(f'{tag}_doorpanel{side}', [(r_ + 0.004, z_) for r_, z_ in MAIDEN_PROF], a0, a1, 14, EX, EY, m_iron, 0.03, dpiv, origin=hp)
        d.location = (0, 0, 0)
        # iron bands and rivets on the door face
        for zb in (0.22, 0.62, 1.02, 1.38):
            rb = prof_r(MAIDEN_PROF, zb) + 0.012
            pts = [Vector((rb * EX * math.cos(math.radians(a0 + (a1 - a0) * k / 10)), rb * EY * math.sin(math.radians(a0 + (a1 - a0) * k / 10)), zb)) - hp for k in range(11)]
            tube(f'{tag}_band{side}{zb}', pts, 0.016, m_dark, dpiv, seg=8)
            for k in range(1, 10, 2):
                an = math.radians(a0 + (a1 - a0) * k / 10); pr = Vector(((rb + 0.012) * EX * math.cos(an), (rb + 0.012) * EY * math.sin(an), zb)) - hp
                prim('uv_sphere', f'{tag}_rv{side}{zb}{k}', m_dark, dpiv, loc=pr, segments=10, ring_count=6, radius=0.013)
        # the spikes on the inside: rows pointing in toward the body
        if spikes:
            for zi, zs in enumerate((0.32, 0.55, 0.78, 1.0, 1.22)):
                n_ = 3 if zi % 2 == 0 else 2
                for k in range(n_):
                    an = math.radians(a0 + (a1 - a0) * (k + 0.5 + (0 if zi % 2 == 0 else 0.5)) / (n_ + (0 if zi % 2 == 0 else 1)))
                    rr = prof_r(MAIDEN_PROF, zs) - 0.03; pin = Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), zs))
                    inward = -Vector((math.cos(an) / EX, math.sin(an) / EY, 0)).normalized()
                    sp = prim('cone', f'{tag}_sp{side}{zi}{k}', m_dark, dpiv, loc=pin - hp + inward * 0.075, vertices=10, radius1=0.016, radius2=0.0015, depth=0.15)
                    sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = inward.to_track_quat('Z', 'Y')
        # the hinge knuckles on the outer edge
        for zk in (0.2, 0.55, 0.9, 1.25):
            rk = prof_r(MAIDEN_PROF, zk) + 0.012; pk = Vector((rk * EX * math.cos(math.radians(ah)), rk * EY * math.sin(math.radians(ah)), zk)) - hp
            prim('cylinder', f'{tag}_hk{side}{zk}', m_dark, dpiv, loc=pk, vertices=14, radius=0.024, depth=0.12)
        # a ring handle near the meeting edge, and the hasp
        an = math.radians(a1 - 10 if side == 'L' else a0 + 10); rr = prof_r(MAIDEN_PROF, 0.95) + 0.03
        hp2 = Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), 0.95)) - hp
        prim('uv_sphere', f'{tag}_boss{side}', m_dark, dpiv, loc=hp2, segments=14, ring_count=8, radius=0.022, scale=(1, 0.6, 1))
        rg = tube(f'{tag}_ring{side}', [hp2 + Vector((0.035 * math.sin(2 * math.pi * k / 16), -0.008, -0.04 + 0.035 * math.cos(2 * math.pi * k / 16))) for k in range(17)], 0.006, m_dark, dpiv, seg=6, caps=False)
        if side == 'R':
            an = math.radians(-90 + 3); rr = prof_r(MAIDEN_PROF, 0.72) + 0.02
            box(f'{tag}_hasp', (0.05, 0.012, 0.14), Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), 0.72)) - hp, m_dark, bv=0.004, parent=dpiv)
        doors.append(dpiv)
    # back-shell bands, rivets and spikes
    for zb in (0.22, 0.62, 1.02, 1.38):
        rb = prof_r(MAIDEN_PROF, zb) + 0.01; a0, a1 = -90 + DOOR_A, 270 - DOOR_A
        pts = [(rb * EX * math.cos(math.radians(a0 + (a1 - a0) * k / 30)), rb * EY * math.sin(math.radians(a0 + (a1 - a0) * k / 30)), zb) for k in range(31)]
        tube(f'{tag}_bandB{zb}', pts, 0.016, m_dark, back, seg=8)
        for k in range(1, 30, 3):
            an = math.radians(a0 + (a1 - a0) * k / 30)
            prim('uv_sphere', f'{tag}_rvB{zb}{k}', m_dark, back, loc=((rb + 0.012) * EX * math.cos(an), (rb + 0.012) * EY * math.sin(an), zb), segments=10, ring_count=6, radius=0.013)
    if spikes:
        for zi, zs in enumerate((0.45, 0.85, 1.2)):
            for k in range(3):
                an = math.radians(90 + (k - 1) * 28); rr = prof_r(MAIDEN_PROF, zs) - 0.035
                pin = Vector((rr * EX * math.cos(an), rr * EY * math.sin(an), zs)); inward = -Vector((math.cos(an) / EX, math.sin(an) / EY, 0)).normalized()
                sp = prim('cone', f'{tag}_spB{zi}{k}', m_dark, back, loc=pin + inward * 0.075, vertices=10, radius1=0.016, radius2=0.0015, depth=0.15)
                sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = inward.to_track_quat('Z', 'Y')
    # shoulders and the cowl
    top = lathe(f'{tag}_top', MAIDEN_TOP, 48, m_iron, root); top.scale = (EX, EY, 1); P['top'] = top
    sd = top.modifiers.new('sd', 'SOLIDIFY'); sd.thickness = 0.02
    # base: a heavy iron foot ring and a plank floor inside
    ft = lathe(f'{tag}_foot', [(0.0, 0.0), (0.47, 0.0), (0.48, 0.02), (0.475, 0.10), (0.44, 0.11), (0.0, 0.11)], 48, m_dark, root); ft.scale = (EX, EY, 1); P['foot'] = ft
    bevel(ft, 0.006, 2)
    if head:
        hd = empty(f'{tag}_head', root, loc=(0, 0, 1.60)); P['head'] = hd
        lathe(f'{tag}_neck', [(0.0, 0.0), (0.11, 0.0), (0.10, 0.06), (0.095, 0.08), (0.0, 0.08)], 32, m_iron, hd)
        build_face(tag, hd, m_iron, m_dark)
    P['root'] = root; P['doors'] = doors
    if base_m:
        pl = box(f'{tag}_plinth', (1.15, 0.95, 0.10), (0, 0, -0.05), base_m, bv=0.01, parent=root); P['plinth'] = pl
    return P


def face_mesh(name, m, parent, loc, R=(0.118, 0.122, 0.158), seg=72, rings=56):
    """the head as one sculpted surface: a calm woman's face hammered from iron (brow, closed eyes, nose, lips, chin)"""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    def g(x, z, cx, cz, wx, wz): return math.exp(-((x - cx) / wx) ** 2 - ((z - cz) / wz) ** 2)
    for v in bm.verts:
        n = v.co.copy(); x, y, z = n.x * R[0], n.y * R[1], n.z * R[2]
        zz = z + 0.19 - 0.0                                                         # in the old face coordinates (head origin at the neck)
        x *= 1.0 - 0.22 * smooth(0.17, 0.07, zz) - 0.05 * smooth(0.12, 0.26, zz)    # narrower jaw and temples
        f = max(0.0, -n.y) ** 1.5                                                   # features only on the front
        d = 0.0
        for sx in (-1, 1):
            d += 0.016 * g(x, zz, sx * 0.040, 0.233, 0.024, 0.008)                  # brow ridge
            d -= 0.026 * g(x, zz, sx * 0.041, 0.210, 0.019, 0.013)                  # eye socket
            d += 0.016 * g(x, zz, sx * 0.041, 0.206, 0.015, 0.0062)                # closed lid
            d += 0.010 * g(x, zz, sx * 0.056, 0.176, 0.022, 0.018)                  # cheekbone
            d += 0.010 * g(x, zz, sx * 0.0135, 0.163, 0.006, 0.006)                 # nostril wing
        d += 0.042 * g(x, zz, 0.0, 0.172, 0.0105, 0.013) + 0.022 * g(x, zz, 0.0, 0.200, 0.0075, 0.024)   # nose tip, bridge
        d += 0.014 * g(x, zz, 0.0, 0.134, 0.022, 0.0058) + 0.015 * g(x, zz, 0.0, 0.119, 0.019, 0.0065)   # upper, lower lip
        d -= 0.008 * g(x, zz, 0.0, 0.1265, 0.025, 0.0024) - 0.006 * g(x, zz, 0.0, 0.147, 0.006, 0.008)   # the line of the mouth, the groove under the nose (-)
        d += 0.016 * g(x, zz, 0.0, 0.094, 0.021, 0.015)                             # chin
        v.co = Vector((x, y, z)) + n * d * f
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return obj(name, me, m, loc, parent)


def build_face(tag, hd, m_iron, m_dark):
    """the maiden's head under a hooded cowl"""
    face_mesh(f'{tag}_face', m_iron, hd, (0, 0.0, 0.19))
    a0, a1 = -90 + 50, 270 - 50
    cowl = arc_shell(f'{tag}_cowl', [(0.015, 0.372), (0.075, 0.362), (0.118, 0.335), (0.142, 0.29), (0.150, 0.23), (0.148, 0.16), (0.152, 0.10), (0.18, 0.05), (0.24, 0.015), (0.31, -0.005)],
                     a0, a1, 40, 1.0, 1.0, m_iron, 0.014, hd)
    subsurf(cowl, 1)
    tube(f'{tag}_collar', [(0.215 * math.cos(math.radians(k * 15)) * EX, 0.215 * math.sin(math.radians(k * 15)) * EY, -0.005) for k in range(25)], 0.016, m_dark, hd, seg=8)
