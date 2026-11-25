# ================================================================ props
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


M_FELT = cloth_mat('felt', (0.018, 0.017, 0.017), 0.9, 0.6, 60.0, 1.0)
M_BLACKCL = cloth_mat('blackcloth', (0.022, 0.021, 0.022), 0.75, 0.5, 200.0, 2.0)
M_LINEN = cloth_mat('linen', (0.80, 0.78, 0.72), 0.8, 0.3, 240.0, 3.0)
M_VIOLET = cloth_mat('violet', (0.22, 0.07, 0.28), 0.8, 0.6, 180.0, 4.0)
M_GREENC = cloth_mat('greencl', (0.10, 0.20, 0.06), 0.85, 0.5, 180.0, 5.0)
M_BLUEC = cloth_mat('bluecl', (0.04, 0.09, 0.30), 0.8, 0.5, 180.0, 6.0)
M_REDC = cloth_mat('redcl', (0.50, 0.04, 0.03), 0.9, 0.6, 90.0, 7.0)
M_SANTA = cloth_mat('santa', (0.55, 0.015, 0.02), 0.8, 0.7, 150.0, 8.0)
M_FUR = mat('fur', (0.88, 0.87, 0.84), 0.95, sheen=1.0); nt_ = M_FUR.node_tree
bp_ = nt_.nodes.new('ShaderNodeBump'); bp_.inputs['Strength'].default_value = 0.6; nt_.links.new(tnoise(nt_, coord(nt_, 'Object'), 160.0, 6.0), bp_.inputs['Height']); nt_.links.new(bp_.outputs['Normal'], nt_.nodes['Principled BSDF'].inputs['Normal'])
M_LEATHER = noisy(mat('leather', (0.025, 0.022, 0.02), 0.4, coat=0.3), 40.0, 0.2)
M_BUCKLE = mat('buckle', (0.95, 0.75, 0.32), 0.15, 1.0)
M_DUMMY = noisy(mat('dummy', (0.42, 0.40, 0.37), 0.7, sheen=0.3), 6.0, 0.15)


def buckle(name, parent, w=0.11, h=0.085, bar=0.012, depth=0.012, loc=(0, 0, 0), rot=(0, 0, 0)):
    """a square gold buckle in the x-z plane (faces -y): four bars, a centre pin"""
    b_ = empty(name, parent, loc=loc); b_.rotation_euler = rot
    for k, (sz, lc) in enumerate((((w, depth, bar), (0, 0, h / 2 - bar / 2)), ((w, depth, bar), (0, 0, -h / 2 + bar / 2)),
                                  ((bar, depth, h), (-w / 2 + bar / 2, 0, 0)), ((bar, depth, h), (w / 2 - bar / 2, 0, 0)))):
        box(f'{name}_b{k}', sz, lc, M_BUCKLE, bv=bar * 0.3, parent=b_)
    box(f'{name}_pin', (bar * 0.5, depth * 0.8, h - bar), (0, -depth * 0.2, 0), M_BUCKLE, parent=b_)
    return b_


def capotain(name, parent, m=None, with_buckle=True):
    """the tall 'Pilgrim' hat: a tapered crown, flat-ish brim, black band, (the myth's) gold buckle. base at origin"""
    root = empty(name, parent)
    lathe(f'{name}_brim', [(0.0, 0.0), (0.21, -0.004), (0.235, 0.004), (0.232, 0.014), (0.20, 0.012), (0.0, 0.012)], 48, m or M_FELT, root)
    lathe(f'{name}_crown', [(0.0, 0.0), (0.112, 0.0), (0.108, 0.06), (0.100, 0.16), (0.094, 0.22), (0.090, 0.235), (0.07, 0.245), (0.0, 0.248)], 40, m or M_FELT, root)
    lathe(f'{name}_band', [(0.112, 0.008), (0.117, 0.008), (0.114, 0.055), (0.109, 0.055)], 40, M_LEATHER, root)
    bk = buckle(f'{name}_bk', root, 0.072, 0.056, 0.009, 0.008, loc=(0, -0.118, 0.032)) if with_buckle else None
    return root, bk


def shoe(name, parent, with_buckle=True):
    root = empty(name, parent)
    prim('uv_sphere', f'{name}_toe', M_LEATHER, root, loc=(0, -0.07, 0.035), segments=20, ring_count=10, radius=1.0, scale=(0.045, 0.09, 0.035))
    prim('uv_sphere', f'{name}_heel', M_LEATHER, root, loc=(0, 0.06, 0.04), segments=20, ring_count=10, radius=1.0, scale=(0.042, 0.06, 0.045))
    box(f'{name}_sole', (0.095, 0.26, 0.015), (0, 0, 0.007), M_LEATHER, bv=0.005, parent=root)
    bk = buckle(f'{name}_bk', root, 0.05, 0.04, 0.007, 0.006, loc=(0, -0.05, 0.068), rot=(R(-35), 0, 0)) if with_buckle else None
    return root, bk


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
