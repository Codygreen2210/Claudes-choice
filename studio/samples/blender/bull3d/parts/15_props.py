# ================================================================ props: the bronze bull, game pieces, little helpers
def bronze_mat(name, base=(0.33, 0.18, 0.075), patina=(0.07, 0.17, 0.13), amt=0.5):
    """old bronze: warm metal, darker in the hollows of a big noise, with spots of green patina (rougher, not metal)"""
    m = mat(name, base, 0.3, 1.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    v = coord(nt, 'Object'); big = tnoise(nt, v, 3.5, 6.0); fine = tnoise(nt, v, 30.0, 4.0)
    pat = ramp_v(nt, math_(nt, 'ADD', math_(nt, 'MULTIPLY', big, 0.8), math_(nt, 'MULTIPLY', fine, 0.2)), 0.56, 0.72)
    pat = math_(nt, 'MULTIPLY', pat, amt)
    col = mixc(nt, math_(nt, 'MULTIPLY', fine, 0.5), base, tuple(c * 0.55 for c in base))
    nt.links.new(mixc(nt, pat, col, patina), b.inputs['Base Color'])
    nt.links.new(math_(nt, 'SUBTRACT', 1.0, pat), b.inputs['Metallic'])
    nt.links.new(math_(nt, 'ADD', 0.36, math_(nt, 'MULTIPLY', pat, 1.2)), b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.004
    nt.links.new(fine, bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


BULL_NPZ = np.load(asset('bull.npz'))
def bull_mesh(name='bullme'):
    """the bull's body: a smooth sculpt made by assets/bull_sdf.py (body along +x, head at +x, feet on z = 0, horns, ears, tail included)"""
    v, f = BULL_NPZ['v'], BULL_NPZ['f']
    me = bpy.data.meshes.new(name); me.vertices.add(len(v)); me.vertices.foreach_set('co', v.ravel())
    me.loops.add(f.size); me.loops.foreach_set('vertex_index', f.ravel()); me.polygons.add(len(f))
    me.polygons.foreach_set('loop_start', np.arange(0, f.size, 3, dtype=np.int32)); me.polygons.foreach_set('loop_total', np.full(len(f), 3, np.int32))
    me.update(); me.validate(); me.polygons.foreach_set('use_smooth', np.ones(len(f), bool)); return me


BULL_ME = None
def bull(name, m, loc=(0, 0, 0), s=1.0, parent=None, door=True):
    """a bronze bull with dark eyes and a hinged door in its -y flank (opens outward, toward -y). Returns (root, door hinge, door hole)"""
    global BULL_ME
    if BULL_ME is None: BULL_ME = bull_mesh()
    rt = empty(name, parent, loc=loc); rt.scale = (s, s, s)
    body = obj(name + '_b', BULL_ME, None, (0, 0, 0), rt); body.data = BULL_ME
    if not BULL_ME.materials: BULL_ME.materials.append(m)
    body.material_slots[0].link = 'OBJECT'; body.material_slots[0].material = m
    for k, p_ in enumerate(BULL_NPZ['eyes']): prim('uv_sphere', f'{name}_ey{k}', M_EYE, rt, loc=tuple(p_), segments=12, ring_count=8, radius=0.016)
    for k, p_ in enumerate(BULL_NPZ['nose']): prim('uv_sphere', f'{name}_ns{k}', M_BLACK, rt, loc=tuple(p_), segments=10, ring_count=6, radius=1.0, scale=(0.008, 0.012, 0.012))
    hinge = hole = None
    if door:
        # the door: a riveted bronze hatch on the flat flank plate (y = -0.211), hinged on its back (-x) edge
        DX0, DX1, DZ0, DZ1, DY = -0.19, 0.07, 0.52, 0.74, -0.211
        hole = box(name + '_hole', (DX1 - DX0 - 0.016, 0.02, DZ1 - DZ0 - 0.016), ((DX0 + DX1) / 2, DY + 0.008, (DZ0 + DZ1) / 2), M_HOLE, parent=rt)
        for (a_, b_) in (((DX0, DZ0), (DX1, DZ0)), ((DX1, DZ0), (DX1, DZ1)), ((DX1, DZ1), (DX0, DZ1)), ((DX0, DZ1), (DX0, DZ0))):
            tube(f'{name}_df{a_[0]}{a_[1]}{b_[1]}', [(a_[0], DY, a_[1]), (b_[0], DY, b_[1])], 0.008, m, rt, seg=8)
        hinge = empty(name + '_dh', rt, loc=(DX0 + 0.004, DY - 0.008, 0))
        box(name + '_dp', (DX1 - DX0 - 0.014, 0.012, DZ1 - DZ0 - 0.014), ((DX1 - DX0) / 2, 0, (DZ0 + DZ1) / 2), m, bv=0.004, parent=hinge)
        for k in range(4):
            for zz in (DZ0 + 0.028, DZ1 - 0.028):
                prim('uv_sphere', f'{name}_rv{k}{zz}', m, hinge, loc=(0.03 + (DX1 - DX0 - 0.06) * k / 3, -0.007, zz), segments=8, ring_count=5, radius=0.008)
        tube(name + '_dk', [(DX1 - DX0 - 0.045, -0.006, (DZ0 + DZ1) / 2 - 0.025), (DX1 - DX0 - 0.045, -0.03, (DZ0 + DZ1) / 2), (DX1 - DX0 - 0.045, -0.006, (DZ0 + DZ1) / 2 + 0.025)], 0.006, m, hinge, seg=8)
        hole.hide_render = True
    return rt, hinge, hole


def piece(name, kind, m, loc, s=1.0, parent=None):
    """a game piece about 0.12 tall (pawn) or 0.16 (king), base on z = 0"""
    rt = empty(name, parent or HALL, loc=loc); rt.scale = (s, s, s)
    if kind == 'pawn':
        lathe(name + '_l', [(0.0, 0.0), (0.034, 0.0), (0.034, 0.01), (0.026, 0.018), (0.014, 0.05), (0.011, 0.075), (0.022, 0.082), (0.012, 0.088), (0.0, 0.088)], 24, m, rt)
        prim('uv_sphere', name + '_h', m, rt, loc=(0, 0, 0.105), segments=16, ring_count=10, radius=0.022)
    else:
        lathe(name + '_l', [(0.0, 0.0), (0.04, 0.0), (0.04, 0.012), (0.03, 0.022), (0.016, 0.08), (0.014, 0.11), (0.028, 0.118), (0.02, 0.126), (0.024, 0.14), (0.0, 0.14)], 24, m, rt)
        for k in range(5):
            a = 2 * math.pi * k / 5; prim('cone', f'{name}_pt{k}', m, rt, loc=(0.018 * math.cos(a), 0.018 * math.sin(a), 0.152), vertices=8, radius1=0.008, radius2=0.001, depth=0.026)
    return rt


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


def flames(name, parent, n, spread, seed, z0=0.0):
    """little fire: cones that grow and flicker (see fire_step)"""
    gf_ = random.Random(seed); out = []
    for k in range(n):
        fx, fy = gf_.uniform(-spread[0], spread[0]), gf_.uniform(-spread[1], spread[1])
        o = prim('cone', f'{name}{k}', M_FLAME if k % 3 else M_FLAME2, parent, loc=(fx, fy, z0), vertices=10, radius1=1.0, radius2=0.0, depth=1.0)
        out.append((o, gf_.uniform(0.025, 0.045), gf_.uniform(0.09, 0.2), gf_.uniform(0, 6), gf_.uniform(0, 0.4), z0))
    return out


def fire_step(fl, t, t0, scale=1.0):
    fi = smooth(t0 - 0.05, t0 + 0.45, t)
    for o, r_, h_, ph, dl, z0 in fl:
        f_ = 0.75 + 0.25 * math.sin(t * 23 + ph) + 0.15 * wob(t, 9, ph)
        k_ = fi * smooth(t0 + dl * 0.5, t0 + dl * 0.5 + 0.3, t) * scale
        o.scale = (max(1e-4, r_ * k_), max(1e-4, r_ * k_), max(1e-4, h_ * k_ * f_)); o.location.z = z0 + 0.5 * h_ * k_ * f_
    return fi
