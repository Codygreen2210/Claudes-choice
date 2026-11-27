# ================================================================ props: cut gems, necklace, cloth, dress forms
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
    return o


def cloth_mat(name, c, rough=0.85, sheen=0.5, weave=180.0, seed=0.0):
    """wool / velvet / linen: base colour with a fine weave bump and a little colour drift"""
    m = mat(name, c, rough, sheen=sheen); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (seed, seed * 0.7, seed * 0.3); nt.links.new(coord(nt, 'Object'), mp.inputs['Vector'])
    big = tnoise(nt, mp.outputs['Vector'], 6.0, 4.0)
    nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', big, 0.5), c, tuple(x * 0.7 for x in c)), b.inputs['Base Color'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = weave; wv.inputs['Distortion'].default_value = 2.0; nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(math_(nt, 'ADD', wv.outputs['Fac'], tnoise(nt, mp.outputs['Vector'], 90.0, 3.0)), bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def gem_mat(name, col, emit_col=None, glow_col=(1.0, 0.28, 0.05)):
    """a cut gem: clear, high-IOR, tinted; a faint emission of its own colour so it reads in a dim case; object property 'glow'
    (0..1) mixes in a red-orange emission (the Hope's phosphorescence)"""
    m = mat(name, col, 0.0, trans=1.0, ior=2.42); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = 0.8
    ec = emit_col or tuple(c * 0.9 for c in col)
    g = objattr(nt, 'glow'); c_ = mixc(nt, math_(nt, 'POWER', g, 0.4), ec, glow_col)
    nt.links.new(c_, b.inputs['Emission Color'])
    nt.links.new(math_(nt, 'ADD', 0.35, math_(nt, 'MULTIPLY', g, 7.0)), b.inputs['Emission Strength'])
    return m


def gem_mesh(name, rfn, rx, ry, n=16, table=0.56, crown=0.17, pav=0.44, girdle=0.015):
    """a faceted stone, table up (+z), girdle at z = 0. rfn(theta) shapes the outline (1 = round); sizes in metres (rx, ry = half width).
    Rings are offset half a step from each other and split into triangles so the flat shading reads as facets."""
    D = 2 * max(rx, ry); vs = []; rings = []
    def ring(rr, z, off):
        idx = []
        for k in range(n):
            th = 2 * math.pi * (k + off) / n; r_ = rfn(th) * rr
            idx.append(len(vs)); vs.append((rx * r_ * math.cos(th), ry * r_ * math.sin(th), z))
        return idx
    culet = len(vs); vs.append((0, 0, -pav * D))
    rings.append(ring(0.52, -pav * D * 0.5, 0.5))
    rings.append(ring(1.0, -girdle * D, 0.0)); rings.append(ring(1.0, girdle * D, 0.0))
    rings.append(ring(0.8, crown * D * 0.55, 0.5)); rings.append(ring(table, crown * D, 0.0))
    fs = [(culet, rings[0][(k + 1) % n], rings[0][k]) for k in range(n)]
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(n):
            k2 = (k + 1) % n; fs.append((a_[k], a_[k2], b_[k])); fs.append((a_[k2], b_[k2], b_[k]))
    fs.append(tuple(rings[-1]))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.validate(); me.update()
    for p_ in me.polygons: p_.use_smooth = False
    return me


ROUND = lambda th: 1.0
def CUSHION(th, p=3.2):
    c, s = abs(math.cos(th)), abs(math.sin(th)); return 1.0 / (c ** p + s ** p) ** (1.0 / p) * 0.93
def SHIELD(th): return 1.0 + 0.13 * math.cos(3 * (th + math.pi / 2))     # a rounded triangle, point down (-y in the mesh)


def gem_obj(name, me, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), glow=0.0):
    o = obj(name, me, None, loc, parent); o.data = me
    if not me.materials: me.materials.append(m)
    o.rotation_euler = rot; o['glow'] = glow; return o


def rough_stone(name, m, r, parent=None, loc=(0, 0, 0), seed=3):
    """an uncut crystal: a lumpy octahedron-ish blob, flat shaded"""
    gr = random.Random(seed); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    for v in bm.verts:
        d = v.co.normalized(); oct_ = 1.0 / (abs(d.x) + abs(d.y) + abs(d.z)) * 1.35
        v.co = d * r * (0.55 * oct_ + 0.45) * gr.uniform(0.85, 1.12); v.co.z *= 0.8
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = False
    o = obj(name, me, m, loc, parent); o['glow'] = 0.0; return o


def necklace(name, parent, m_hope, m_white, m_plat, hope_me, small_me, loc=(0, 0, 0)):
    """the Hope necklace laid on a display board: the board's face is the local x-z plane, facing -y.
    A loop of white diamonds, a pendant of sixteen white diamonds round the blue stone. Returns (root, hope object)."""
    root = empty(name, parent, loc=loc)
    n = 34
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n; x = 0.15 * math.sin(a); z = 0.1 + 0.19 * math.cos(a)
        gem_obj(f'{name}_l{k}', small_me, m_white, root, loc=(x, -0.006, z), rot=(R(90), 0, a))
        tube(f'{name}_lk{k}', [(x, -0.002, z), (0.15 * math.sin(a + math.pi / n), -0.002, 0.1 + 0.19 * math.cos(a + math.pi / n))], 0.0022, m_plat, root, seg=6)
    PZ = -0.165
    tube(f'{name}_bail', [(0, -0.004, -0.092), (0, -0.006, -0.11)], 0.006, m_plat, root, seg=8)
    rim = lathe(f'{name}_rim', [(0.043, -0.004), (0.05, -0.004), (0.05, 0.004), (0.043, 0.004)], 32, m_plat, root, loc=(0, -0.006, PZ)); rim.rotation_euler = (R(90), 0, 0)
    rim.scale = (1.0, 0.86, 1.0)
    for k in range(16):
        a = 2 * math.pi * k / 16; gem_obj(f'{name}_p{k}', small_me, m_white, root, loc=(0.064 * math.cos(a), -0.007, PZ + 0.056 * math.sin(a)), rot=(R(90), 0, a))
    hope = gem_obj(f'{name}_hope', hope_me, m_hope, root, loc=(0, -0.008, PZ), rot=(R(90), 0, 0))
    return root, hope


def dress_form(name, parent, loc, head=True, h=1.0, m=None):
    """a museum dress form on a pole: torso (shoulders at about 1.5), neck, head"""
    md = m or M_DUMMY; f_ = empty(name, parent, loc=loc)
    lathe(f'{name}_base', [(0.0, 0.0), (0.2, 0.0), (0.2, 0.03), (0.03, 0.05), (0.025, 0.85), (0.0, 0.85)], 20, M_BLACK, f_)
    lathe(f'{name}_torso', [(0.0, 0.85), (0.13, 0.86), (0.155, 0.95), (0.135, 1.12), (0.16, 1.30), (0.19, 1.42), (0.12, 1.50), (0.05, 1.53), (0.0, 1.53)], 28, md, f_).scale = (1.0, 0.68, 1.0)
    if head:
        lathe(f'{name}_neck', [(0.0, 1.5), (0.045, 1.5), (0.04, 1.62), (0.0, 1.62)], 16, md, f_)
        prim('uv_sphere', f'{name}_head', md, f_, loc=(0, 0, 1.72), segments=24, ring_count=12, radius=0.1, scale=(0.95, 1.05, 1.2))
    return f_


def low_z(root):
    """lowest point of a prop (all its meshes, modifiers applied) in the root's own frame, as built"""
    bpy.context.view_layer.update(); inv = root.matrix_world.inverted(); z = 1e9
    for o in [root] + list(root.children_recursive):
        if o.type != 'MESH': continue
        mw = inv @ o.matrix_world
        dg = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = dg.to_mesh()
        for v in me.vertices: z = min(z, (mw @ v.co).z)
        dg.to_mesh_clear()
    return z


def rest_on(o, top, gap=0.001):
    """move o (keeping x, y and its rotation) so its lowest world point sits on height top"""
    bpy.context.view_layer.update(); dg = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = dg.to_mesh()
    z = min((o.matrix_world @ v.co).z for v in me.vertices); dg.to_mesh_clear()
    for c in o.children_recursive:
        if c.type != 'MESH': continue
        dc = c.evaluated_get(bpy.context.evaluated_depsgraph_get()); mc = dc.to_mesh(); z = min(z, min((c.matrix_world @ v.co).z for v in mc.vertices)); dc.to_mesh_clear()
    o.location.z += top - z + gap; return o.location.copy()
