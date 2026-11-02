# Thanksgiving Shorts: shared Blender helpers (materials, meshes, props, the decorated table).
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler

S = None
def reset(fps=30):
    global S
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import addon_utils; addon_utils.enable('cycles', default_set=False)
    S = bpy.context.scene; S.render.fps = fps
    return S

def link(o):
    S.collection.objects.link(o); return o

# ---------------- materials (colours are given as sRGB, like a colour picker, and turned linear here)
def lin(c): return tuple(x ** 2.2 for x in c[:3])
def mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(color), 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    for k, v in kw.items():
        key = {'ior': 'IOR', 'trans': 'Transmission Weight', 'sss': 'Subsurface Weight', 'sss_r': 'Subsurface Radius', 'sss_s': 'Subsurface Scale',
               'coat': 'Coat Weight', 'coat_r': 'Coat Roughness', 'sheen': 'Sheen Weight', 'spec': 'Specular IOR Level', 'alpha': 'Alpha',
               'emit': 'Emission Color', 'emit_s': 'Emission Strength', 'aniso': 'Anisotropic'}[k]
        b.inputs[key].default_value = (*lin(v), 1) if key == 'Emission Color' else v
    return m

def nodes(m):
    return m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes['Principled BSDF']

def noise(m, scale, detail=6, coord='Object', w=None, dims='3D'):
    N, L, _ = nodes(m)
    tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.noise_dimensions = dims
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    L.new(tc.outputs[coord], nz.inputs['Vector']); return nz

def color_noise(m, scale, c1, c2, lo=0.35, hi=0.65, detail=6, to='Base Color'):
    N, L, b = nodes(m)
    nz = noise(m, scale, detail)
    r = N.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = lo; r.color_ramp.elements[1].position = hi
    r.color_ramp.elements[0].color = (*lin(c1), 1); r.color_ramp.elements[1].color = (*lin(c2), 1)
    L.new(nz.outputs['Fac'], r.inputs['Fac']); L.new(r.outputs['Color'], b.inputs[to]); return nz, r

def bump(m, scale, strength, dist=0.002, detail=8, kind='noise'):
    N, L, b = nodes(m)
    if kind == 'voronoi':
        tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexVoronoi'); nz.inputs['Scale'].default_value = scale
        L.new(tc.outputs['Object'], nz.inputs['Vector']); out = nz.outputs['Distance']
    else:
        nz = noise(m, scale, detail); out = nz.outputs['Fac']
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = dist
    L.new(out, bp.inputs['Height'])
    if b.inputs['Normal'].is_linked:                       # chain onto an existing bump
        prev = b.inputs['Normal'].links[0].from_socket; L.new(prev, bp.inputs['Normal'])
    L.new(bp.outputs['Normal'], b.inputs['Normal']); return nz

def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type == 'BSDF_PRINCIPLED': N.remove(n)
    e = N.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*lin(color), 1); e.inputs['Strength'].default_value = strength
    L.new(e.outputs[0], N['Material Output'].inputs['Surface']); return m

def volume_mat(name, color=(1, 1, 1), density=1.0, scale=4.0, fire=False, edge=0.5):
    """Smoke/steam (white, scattering) or fire (emissive, blackbody). Density shaped by noise and a soft sphere falloff.
    Animate with the returned noise node's W input."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    for n in list(N):
        if n.type == 'BSDF_PRINCIPLED': N.remove(n)
    v = N.new('ShaderNodeVolumePrincipled'); L.new(v.outputs[0], N['Material Output'].inputs['Volume'])
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    nz.inputs['Roughness'].default_value = 0.6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    # radial falloff: 1 at centre, 0 at the object's unit sphere
    ln = N.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L.new(tc.outputs['Object'], ln.inputs[0])
    fall = N.new('ShaderNodeMapRange'); fall.inputs['From Min'].default_value = 1.0; fall.inputs['From Max'].default_value = edge
    L.new(ln.outputs['Value'], fall.inputs['Value'])
    mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; L.new(nz.outputs['Fac'], mul.inputs[0]); L.new(fall.outputs['Result'], mul.inputs[1])
    sh = N.new('ShaderNodeMapRange'); sh.inputs['From Min'].default_value = 0.3 if fire else 0.22; sh.inputs['From Max'].default_value = 0.55 if fire else 0.6
    sh.inputs['To Max'].default_value = density; L.new(mul.outputs[0], sh.inputs['Value'])
    L.new(sh.outputs['Result'], v.inputs['Density'])
    v.inputs['Color'].default_value = (*lin(color), 1)
    if fire:
        v.inputs['Color'].default_value = (0.05, 0.04, 0.035, 1)       # soot
        es = N.new('ShaderNodeMapRange'); es.inputs['From Min'].default_value = 0.28; es.inputs['From Max'].default_value = 0.62
        es.inputs['To Min'].default_value = 0.0; es.inputs['To Max'].default_value = 22.0
        L.new(mul.outputs[0], es.inputs['Value']); L.new(es.outputs['Result'], v.inputs['Emission Strength'])
        rp = N.new('ShaderNodeValToRGB'); cr = rp.color_ramp
        cr.elements[0].position = 0.3; cr.elements[0].color = (*lin((0.55, 0.06, 0.0)), 1)
        cr.elements[1].position = 0.62; cr.elements[1].color = (*lin((1.0, 0.8, 0.35)), 1)
        e2 = cr.elements.new(0.45); e2.color = (*lin((1.0, 0.38, 0.02)), 1)
        L.new(mul.outputs[0], rp.inputs['Fac']); L.new(rp.outputs['Color'], v.inputs['Emission Color'])
    return m, nz, v

# ---------------- meshes
def obj_from(me, name, m=None, smooth=True):
    o = bpy.data.objects.new(name, me); link(o)
    if m: me.materials.append(m)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return o

def lathe(name, prof, seg=64, m=None, cap_bottom=False, arc=None):
    """prof: list of (r, z) from bottom/inside up. Revolve around z (a full turn, or arc=(a0, a1) radians for a part)."""
    vs, fs = [], []
    n = len(prof)
    full = arc is None
    cols = seg if full else seg + 1
    for i in range(cols):
        a = 2 * math.pi * i / seg if full else arc[0] + (arc[1] - arc[0]) * i / seg
        for r, z in prof: vs.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(seg):
        j = (i + 1) % seg if full else i + 1
        for k in range(n - 1): fs.append((i * n + k, j * n + k, j * n + k + 1, i * n + k + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    return obj_from(me, name, m)

def add(kind, name, m=None, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), smooth=True, **kw):
    getattr(bpy.ops.mesh, 'primitive_' + kind + '_add')(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    if m: o.data.materials.append(m)
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
    return o

def subsurf(o, lv=2):
    md = o.modifiers.new('ss', 'SUBSURF'); md.levels = lv; md.render_levels = lv; return md

def solidify(o, t):
    md = o.modifiers.new('sol', 'SOLIDIFY'); md.thickness = t; md.offset = 0; return md

def deform(o, fn):
    """fn(x, y, z) -> (x, y, z) on object-space verts"""
    for v in o.data.vertices: v.co = Vector(fn(*v.co))
    o.data.update()

def look(o, target, up='Y'):
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat('-Z', up).to_euler()

def light(kind, name, pos, aim, energy, color, size=0.5):
    Ld = bpy.data.lights.new(name, kind); Ld.energy = energy; Ld.color = lin(color)
    if kind == 'AREA': Ld.size = size; Ld.shape = 'DISK'
    if kind in ('POINT', 'SPOT'): Ld.shadow_soft_size = size
    o = bpy.data.objects.new(name, Ld); link(o); o.location = pos
    look(o, aim); return o

# ---------------- the turkey (metaballs -> mesh)
import os
HERE = os.path.dirname(os.path.abspath(__file__))
def turkey_mesh(name, kind='roast'):
    import numpy as np
    d = np.load(os.path.join(HERE, 'turkey_%s.npz' % kind))
    me = bpy.data.meshes.new(name); me.from_pydata(d['v'].tolist(), [], d['f'].tolist()); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = obj_from(me, name)
    sm = o.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 3
    return o

def roast_mat():
    m = mat('roast', (0.5, 0.24, 0.07), 0.28, coat=0.55, coat_r=0.1, sss=0.06, sss_r=(0.7, 0.3, 0.1), sss_s=0.02)
    N, L, b = nodes(m)
    geo = N.new('ShaderNodeNewGeometry')
    nz = noise(m, 16, 10)
    mx = N.new('ShaderNodeMath'); mx.operation = 'ADD'
    pw = N.new('ShaderNodeMapRange'); pw.inputs['From Min'].default_value = 0.47; pw.inputs['From Max'].default_value = 0.56
    pw.inputs['To Min'].default_value = -0.25; pw.inputs['To Max'].default_value = 0.35
    L.new(geo.outputs['Pointiness'], pw.inputs['Value'])
    L.new(nz.outputs['Fac'], mx.inputs[0]); L.new(pw.outputs['Result'], mx.inputs[1])
    r = N.new('ShaderNodeValToRGB'); cr = r.color_ramp
    cr.elements[0].position = 0.38; cr.elements[0].color = (*lin((0.78, 0.5, 0.2)), 1)
    cr.elements[1].position = 0.78; cr.elements[1].color = (*lin((0.3, 0.13, 0.04)), 1)
    e = cr.elements.new(0.55); e.color = (*lin((0.62, 0.32, 0.1)), 1)
    L.new(mx.outputs[0], r.inputs['Fac']); L.new(r.outputs['Color'], b.inputs['Base Color'])
    bump(m, 35, 0.3, 0.004); bump(m, 260, 0.15, 0.0008, kind='voronoi')
    return m

def frozen_mat():
    m = mat('frozen', (0.88, 0.66, 0.6), 0.35, sss=0.3, sss_r=(0.9, 0.35, 0.25), sss_s=0.03)
    N, L, b = nodes(m)
    nz = noise(m, 14, 8)
    r = N.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = 0.42; r.color_ramp.elements[1].position = 0.62
    L.new(nz.outputs['Fac'], r.inputs['Fac'])
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs['A'].default_value = (*lin((0.9, 0.68, 0.62)), 1); mix.inputs['B'].default_value = (*lin((0.93, 0.95, 0.98)), 1)
    L.new(r.outputs['Color'], mix.inputs['Factor']); L.new(mix.outputs['Result'], b.inputs['Base Color'])
    rr = N.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.3; rr.inputs['To Max'].default_value = 0.85
    L.new(r.outputs['Color'], rr.inputs['Value']); L.new(rr.outputs['Result'], b.inputs['Roughness'])
    bump(m, 500, 0.45, 0.0008, kind='voronoi'); bump(m, 60, 0.2, 0.002)
    return m

# ---------------- decorations and food for the table
def pumpkin(name, loc, r=0.12, h=0.8, color=(0.85, 0.36, 0.05), lobes=10, rot=0.0):
    m = mat(name + '_m', color, 0.42, coat=0.2, coat_r=0.3, sss=0.05)
    color_noise(m, 6, color, tuple(c * 0.75 for c in color), 0.3, 0.7)
    bump(m, 80, 0.1, 0.001)
    o = add('uv_sphere', name, m, loc, segments=96, ring_count=48)
    def f(x, y, z):
        a = math.atan2(y, x); rad = math.hypot(x, y)
        k = 1 - 0.09 * (1 - abs(math.cos(lobes * a / 2))) ** 1.5        # grooves
        zz = z * h; zz -= 0.25 * (1 - rad) * (1 if z > 0 else -0.5) * 0.4  # dimple top
        return (x * k * r, y * k * r, (zz) * r)
    deform(o, f); o.rotation_euler.z = rot
    st = add('cylinder', name + '_stem', mat(name + '_st', (0.28, 0.22, 0.1), 0.8), (loc[0], loc[1], loc[2] + h * r * 0.95),
             (0.012 * r / 0.12, 0.012 * r / 0.12, 0.03 * r / 0.12), (0.25, 0.1, 0), vertices=7)
    bump(st.data.materials[0], 120, 0.5, 0.002)
    return o

def gourd(name, loc, s=0.05, color=(0.9, 0.75, 0.2), rot=0.0):
    m = mat(name + '_m', color, 0.35, coat=0.3)
    color_noise(m, 5, color, (0.25, 0.45, 0.12), 0.45, 0.7); bump(m, 30, 0.3, 0.003)
    o = add('uv_sphere', name, m, loc, segments=48, ring_count=24)
    deform(o, lambda x, y, z: (x * s * (1 - 0.35 * max(0, z)), y * s * (1 - 0.35 * max(0, z)), z * s * 1.6))
    o.rotation_euler = (1.35, 0, rot); return o

def leaf(name, loc, size=0.06, color=(0.8, 0.25, 0.05), rot=0.0):
    # maple leaf outline in polar form, curled a little
    pts = []
    for i in range(160):
        a = 2 * math.pi * i / 160
        r = 0.55 + 0.45 * abs(math.sin(2.5 * a)) ** 0.6 + 0.08 * math.sin(15 * a)
        r *= 0.55 if math.sin(a) < -0.85 else 1.0
        pts.append((r * math.cos(a), r * math.sin(a)))
    vs = [(0, 0, 0)] + [(x * size, y * size, 0.015 * size * (x * x + y * y) * 4) for x, y in pts]
    fs = [(0, i + 1, (i + 1) % 160 + 1) for i in range(160)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    m = mat(name + '_m', color, 0.55, sss=0.15, sss_r=(1, 0.4, 0.1), sss_s=0.002)
    color_noise(m, 4, color, (min(1, color[0] * 1.1), min(1, color[1] * 1.8 + 0.1), 0.05), 0.35, 0.8)
    bump(m, 90, 0.2, 0.0005)
    o = obj_from(me, name, m); o.location = loc; o.rotation_euler = (0.08, -0.05, rot); return o

def plate(name, loc, r=0.13, m=None):
    m = m or mat('china', (0.94, 0.93, 0.9), 0.12, coat=0.6, coat_r=0.05)
    p = [(0.0, 0.0), (r * 0.6, 0.0), (r * 0.62, 0.004), (r * 0.66, 0.006), (r * 0.9, 0.014), (r, 0.02), (r * 1.0, 0.024), (r * 0.9, 0.019), (r * 0.66, 0.011), (0.0, 0.011)]
    o = lathe(name, p, 96, m); o.location = loc; return o

def bowl(name, loc, r=0.08, h=0.06, m=None):
    m = m or mat('bowl_glaze', (0.55, 0.3, 0.15), 0.15, coat=0.8, coat_r=0.05)
    p = [(0, 0), (r * 0.5, 0), (r * 0.9, h * 0.5), (r, h), (r * 0.94, h), (r * 0.84, h * 0.52), (r * 0.45, h * 0.1), (0, h * 0.1)]
    o = lathe(name, p, 96, m); o.location = loc; return o

def mash(name, loc, r=0.07, h=0.06):
    m = mat('mash', (0.93, 0.88, 0.72), 0.55, sss=0.2, sss_r=(1, 0.9, 0.6), sss_s=0.01)
    bump(m, 18, 0.5, 0.006); bump(m, 120, 0.15, 0.001)
    o = add('uv_sphere', name, m, loc, segments=64, ring_count=32)
    random.seed(len(name))
    deform(o, lambda x, y, z: (x * r * (1 + 0.06 * math.sin(7 * y + 3 * z)), y * r * (1 + 0.06 * math.sin(6 * x)), max(z, -0.2) * h))
    pat = add('cube', name + '_butter', mat('butter', (1.0, 0.85, 0.35), 0.25, sss=0.3), (loc[0], loc[1], loc[2] + h * 0.98), (0.012, 0.012, 0.006), (0, 0, 0.5))
    return o

def gravy_mat():
    m = mat('gravy', (0.22, 0.1, 0.035), 0.08, sss=0.15, sss_r=(0.5, 0.2, 0.05), sss_s=0.01, coat=0.4, coat_r=0.03)
    return m

def candle(name, loc, h=0.2, r=0.025, color=(0.95, 0.88, 0.75)):
    wax = mat(name + '_wax', color, 0.45, sss=0.6, sss_r=(1, 0.7, 0.4), sss_s=0.02)
    c = add('cylinder', name, wax, (loc[0], loc[1], loc[2] + h / 2), (r, r, h / 2), vertices=48)
    holder = lathe(name + '_h', [(0, 0), (r * 2.2, 0), (r * 2.2, 0.008), (r * 1.4, 0.014), (r * 1.15, 0.03), (r * 1.15, 0.035), (0, 0.035)], 48,
                   mat(name + '_brass', (0.85, 0.62, 0.3), 0.25, 1.0))
    holder.location = loc
    fl = add('uv_sphere', name + '_flame', emit_mat(name + '_fm', (1.0, 0.62, 0.22), 18), (loc[0], loc[1], loc[2] + h + 0.022), (0.006, 0.006, 0.018), segments=24, ring_count=12)
    deform(fl, lambda x, y, z: (x * (1 - 0.6 * max(0, z)), y * (1 - 0.6 * max(0, z)), z))
    lt = light('POINT', name + '_lt', (loc[0], loc[1], loc[2] + h + 0.03), (loc[0], loc[1], 0), 1.6, (1.0, 0.6, 0.28), 0.01)
    return c, fl, lt

def corn(name, loc, rot=0.0):
    m = mat(name + '_m', (0.95, 0.72, 0.15), 0.35, sss=0.2, coat=0.3)
    color_noise(m, 3, (0.95, 0.72, 0.15), (0.75, 0.32, 0.08), 0.4, 0.8)
    bump(m, 260, 0.6, 0.002, kind='voronoi')
    o = add('uv_sphere', name, m, loc, (0.022, 0.022, 0.085), (math.pi / 2, 0, rot), segments=48, ring_count=24)
    return o

def roll(name, loc):
    m = mat('roll', (0.72, 0.42, 0.15), 0.4, coat=0.35, coat_r=0.2, sss=0.1)
    color_noise(m, 5, (0.78, 0.48, 0.17), (0.5, 0.25, 0.07), 0.3, 0.8); bump(m, 70, 0.15, 0.001)
    o = add('uv_sphere', name, m, loc, (0.04, 0.035, 0.028), segments=48, ring_count=24); return o

def cranberry(name, loc):
    d = bowl(name + '_dish', loc, 0.055, 0.035, mat('glass', (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=1.5))
    m = mat('cran', (0.45, 0.02, 0.04), 0.12, sss=0.6, sss_r=(1, 0.1, 0.1), sss_s=0.02, coat=0.5)
    bump(m, 40, 0.25, 0.002)
    c = add('cylinder', name, m, (loc[0], loc[1], loc[2] + 0.02), (0.045, 0.045, 0.016), vertices=48); return c

def wine(name, loc, fill=0.6):
    g = mat('glass', (0.95, 0.97, 1.0), 0.02, trans=1.0, ior=1.5)
    p = [(0, 0), (0.035, 0), (0.035, 0.003), (0.006, 0.006), (0.004, 0.09), (0.03, 0.11), (0.042, 0.15), (0.038, 0.2), (0.036, 0.2), (0.04, 0.15), (0.028, 0.112), (0.0, 0.096)]
    o = lathe(name, p, 64, g); o.location = loc
    return o

def table_set(seed=3):
    """A decorated Thanksgiving table centred on the origin, top at z=0. Returns dict of key objects."""
    random.seed(seed)
    wood = mat('wood', (0.3, 0.16, 0.07), 0.38, coat=0.3, coat_r=0.15)
    N, L, b = nodes(wood)
    tc = N.new('ShaderNodeTexCoord'); wv = N.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 3; wv.inputs['Distortion'].default_value = 8
    wv.inputs['Detail'].default_value = 6; L.new(tc.outputs['Object'], wv.inputs['Vector'])
    rr = N.new('ShaderNodeValToRGB'); rr.color_ramp.elements[0].color = (*lin((0.5, 0.3, 0.16)), 1); rr.color_ramp.elements[1].color = (*lin((0.3, 0.16, 0.08)), 1)
    L.new(wv.outputs['Fac'], rr.inputs['Fac']); L.new(rr.outputs['Color'], b.inputs['Base Color'])
    bump(wood, 30, 0.08, 0.001)
    top = add('cube', 'table', wood, (0, 0, -0.025), (1.1, 0.55, 0.025), smooth=False)
    bv = top.modifiers.new('bv', 'BEVEL'); bv.width = 0.008; bv.segments = 3
    burlap = mat('runner', (0.72, 0.58, 0.38), 0.95, sheen=0.5)
    bump(burlap, 600, 0.4, 0.0006, kind='voronoi')
    run = add('cube', 'runner', burlap, (0, 0, 0.0015), (1.15, 0.17, 0.0015), smooth=False)
    out = {}
    # centrepiece: roast turkey on a platter
    pl = plate('platter', (0, 0, 0.003), 0.24, mat('platter_m', (0.92, 0.9, 0.85), 0.1, coat=0.7, coat_r=0.04)); pl.scale = (1.25, 0.9, 1)
    tk = turkey_mesh('roast_turkey', 'roast'); tk.data.materials.append(roast_mat()); tk.location = (0, 0, 0.098); tk.rotation_euler.z = math.radians(200); tk.scale = (0.82, 0.82, 0.82); tk.location.z = 0.084
    out['turkey'] = tk; out['platter'] = pl
    for i, (x, y) in enumerate([(0.2, 0.11), (-0.2, -0.12), (0.19, -0.1)]):       # herb sprigs as small leaves
        leaf('herb%d' % i, (x, y, 0.016), 0.02, (0.2, 0.4, 0.12), random.random() * 6)
    # pumpkins, gourds, leaves along the runner
    out['pumpkins'] = [pumpkin('pk1', (-0.62, 0.02, 0.0), 0.11, 0.78), pumpkin('pk2', (-0.48, -0.07, 0.0), 0.065, 0.8, (0.93, 0.9, 0.82), 8),
                       pumpkin('pk3', (0.6, -0.02, 0.0), 0.09, 0.75, (0.8, 0.42, 0.1), 10, 1.0), pumpkin('pk4', (0.75, 0.07, 0.0), 0.055, 0.82, (0.95, 0.55, 0.12), 8)]
    gourd('gd1', (-0.4, 0.07, 0.03), 0.032, (0.95, 0.8, 0.25), 0.4); gourd('gd2', (0.47, 0.06, 0.03), 0.03, (0.4, 0.55, 0.2), 2.1)
    cols = [(0.85, 0.28, 0.04), (0.9, 0.55, 0.06), (0.65, 0.12, 0.05), (0.9, 0.7, 0.1)]
    for i in range(22):
        x = random.uniform(-1.0, 1.0); y = random.uniform(-0.16, 0.16)
        if abs(x) < 0.32: continue
        leaf('lf%d' % i, (x, y, 0.004 + i * 0.0003), random.uniform(0.035, 0.06), random.choice(cols), random.random() * 6.3)
    out['candles'] = [candle('cd1', (-0.33, -0.04, 0.003), 0.22), candle('cd2', (0.36, 0.03, 0.003), 0.17), candle('cd3', (0.9, -0.05, 0.003), 0.26, 0.022)]
    corn('corn1', (-0.82, -0.08, 0.022), 0.3); corn('corn2', (-0.8, 0.0, 0.022), -0.2)
    # place settings and sides
    for i, x in enumerate((-0.55, 0.0, 0.55)):
        for s in (-1, 1):
            plate('plate%d%d' % (i, s), (x, s * 0.38, 0.0))
            wine('wine%d%d' % (i, s), (x + 0.17, s * 0.3, 0.0))
    bowl('mashbowl', (-0.18, 0.26, 0.0)); out['mash'] = mash('mashed', (-0.18, 0.26, 0.015), 0.06, 0.045)
    cranberry('cranb', (0.2, -0.26, 0.0))
    for i, (x, y) in enumerate([(0.28, 0.24), (0.33, 0.27), (0.3, 0.2)]): roll('roll%d' % i, (x, y, 0.024))
    # gravy boat
    gb = lathe('gravyboat', [(0, 0), (0.04, 0), (0.04, 0.008), (0.05, 0.04), (0.052, 0.06), (0.047, 0.06), (0.045, 0.04), (0.035, 0.012), (0, 0.012)], 64,
               mat('gb_m', (0.93, 0.92, 0.88), 0.1, coat=0.7)); gb.location = (-0.32, -0.25, 0); gb.scale = (1.5, 1, 1)
    out['gravyboat'] = gb
    return out

def room_back(z0=0.0, warm=True):
    """Dark warm dining room behind the table: wall, window glow, out-of-focus string lights."""
    wall = add('plane', 'wall', mat('wall_m', (0.32, 0.22, 0.15), 0.85), (0, 2.2, 1.0), (4, 2, 1), (math.pi / 2, 0, 0), smooth=False)
    bump(wall.data.materials[0], 6, 0.05, 0.01)
    win = add('plane', 'window', emit_mat('win_m', (0.35, 0.45, 0.7), 0.6), (0.9, 2.19, 1.1), (0.6, 0.7, 1), (math.pi / 2, 0, 0), smooth=False)
    bl = emit_mat('bulb', (1.0, 0.7, 0.35), 25)
    for i in range(18):
        x = -2 + i * 0.24; add('uv_sphere', 'bulb%d' % i, bl, (x, 2.1, 1.65 + 0.08 * math.sin(i * 0.9)), (0.012, 0.012, 0.012), segments=12, ring_count=8)
    floor = add('plane', 'floor', mat('floor_m', (0.18, 0.1, 0.05), 0.5), (0, 0, -0.75), (5, 5, 1), smooth=False)
    return wall

def camera(lens=35, fstop=2.0):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.sensor_fit = 'VERTICAL'; c.sensor_height = 24
    c.dof.use_dof = True; c.dof.aperture_fstop = fstop
    o = bpy.data.objects.new('cam', c); link(o); S.camera = o; return o

def render_setup(samples, scale, bounces=6):
    S.render.engine = 'CYCLES'; S.cycles.device = 'CPU'; S.cycles.samples = samples; S.cycles.use_adaptive_sampling = True
    S.cycles.adaptive_threshold = 0.03
    S.cycles.use_denoising = True; S.cycles.denoiser = 'OPENIMAGEDENOISE'; S.cycles.max_bounces = bounces
    S.cycles.transmission_bounces = 8; S.cycles.volume_bounces = 1; S.cycles.volume_step_rate = 4.0
    S.render.resolution_x, S.render.resolution_y = int(1080 * scale), int(1920 * scale); S.render.resolution_percentage = 100
    S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Punchy'
    S.render.image_settings.file_format = 'PNG'; S.render.image_settings.color_mode = 'RGB'
    S.render.use_persistent_data = True

def ease(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def lerp(a, b, t): return a + (b - a) * t
def vlerp(a, b, t): return Vector(a).lerp(Vector(b), t)

def shake(t, amp, seed=0):
    return Vector((amp * (math.sin(t * 13.1 + seed) * 0.6 + math.sin(t * 29.7 + 2 * seed) * 0.4),
                   amp * (math.sin(t * 11.3 + 1 + seed) * 0.6 + math.sin(t * 23.9 + seed) * 0.4),
                   amp * 0.5 * math.sin(t * 17.7 + 3 + seed)))
