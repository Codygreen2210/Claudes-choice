# The iodine clock, built and rendered in Blender (Cycles): a beaker on a stir plate, a flask poured in, the wait, the snap to blue-black,
# and molecule close-ups (iodine made and erased, the starch coil, light soaked up). Real glass, real liquid, studio light.
#   python3 clock.py OUTDIR F0 F1 [--samples 64] [--scale 1.0]   -> OUTDIR/f_00000.png ...   (frames are 30 fps; times from times.json beside this file)
import sys, os, math, json, argparse
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=64); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
TM = json.load(open(os.path.join(HERE, 'times.json'))); B, DUR, TOTAL = TM['starts'], TM['durs'], TM['total']
FPS = 30
def beat_at(t):
    for i in range(len(B) - 1, -1, -1):
        if t >= B[i]: return i
    return 0
clamp = lambda x, lo, hi: max(lo, min(hi, x))
sm = lambda x: x * x * (3 - 2 * x)
def smooth(e0, e1, x): return sm(clamp((x - e0) / (e1 - e0), 0, 1))
lerp = lambda p, q, k: p + (q - p) * k
def h1(n): return (math.sin(n * 127.1 + 311.7) * 43758.5453) % 1.0

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('cycles', default_set=False)
S = bpy.context.scene; S.render.engine = 'CYCLES'; S.render.fps = FPS
S.render.resolution_x = int(1080 * a.scale); S.render.resolution_y = int(1920 * a.scale); S.render.resolution_percentage = 100
C = S.cycles; C.device = 'CPU'; C.samples = a.samples; C.use_denoising = os.environ.get('NODN') is None; C.denoiser = 'OPENIMAGEDENOISE'
C.max_bounces = 14; C.diffuse_bounces = 3; C.glossy_bounces = 6; C.transmission_bounces = 14; C.volume_bounces = 2; C.transparent_max_bounces = 10
C.caustics_reflective = False; C.caustics_refractive = False; C.blur_glossy = float(os.environ.get('BLURG', '0.0')); C.sample_clamp_indirect = 8.0; C.sample_clamp_direct = 0.0
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'
S.render.film_transparent = False

# ---------------------------------------------------------------- materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior; b.inputs['Coat Weight'].default_value = coat; b.inputs['Alpha'].default_value = alpha
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    return m
def noisy(m, scale=40.0, amt=0.15, rough_amt=0.1):     # a little colour and roughness wobble so surfaces don't look like plastic
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    base = b.inputs['Base Color'].default_value[:]; mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs['A'].default_value = base; mx.inputs['B'].default_value = tuple(c * (1 - amt) for c in base[:3]) + (1,)
    nt.links.new(nz.outputs['Fac'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    r0 = b.inputs['Roughness'].default_value; mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = r0 - rough_amt; mr.inputs['To Max'].default_value = r0 + rough_amt
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness']); return m
def thin_glass(name):
    """lab glassware as thin glass: a sharp Fresnel reflection over a see-through layer that darkens and greens at grazing angles (the walls'
    edges). Real refracting glass hugging a refracting liquid made a hall of mirrors between the two surfaces and the liquid came out speckled grey."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.5
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.22
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.0; gl.inputs['Color'].default_value = (0.75, 0.75, 0.75, 1)
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.985, 0.995, 0.99, 1); ramp.color_ramp.elements[1].color = (0.42, 0.52, 0.48, 1)
    nt.links.new(lw.outputs['Facing'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], tr.inputs['Color'])
    # reflect only on the side facing the ray: on a back face the Fresnel node flips the IOR, hits total internal reflection and the
    # inside of the wall turned into a mirror (the black liquid came out bright grey)
    geo = nt.nodes.new('ShaderNodeNewGeometry'); fm = nt.nodes.new('ShaderNodeMath'); fm.operation = 'SUBTRACT'; fm.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs['Backfacing'], fm.inputs[1]); fx = nt.nodes.new('ShaderNodeMath'); fx.operation = 'MULTIPLY'
    nt.links.new(fr.outputs['Fac'], fx.inputs[0]); nt.links.new(fm.outputs['Value'], fx.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fx.outputs['Value'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(gl.outputs['BSDF'], mx.inputs[2])
    # only camera rays see the reflection; every other ray passes straight through. Bounced rays meeting the glass from odd sides made a
    # glowing cone inside the black liquid.
    lp = nt.nodes.new('ShaderNodeLightPath'); tr2 = nt.nodes.new('ShaderNodeBsdfTransparent'); tr2.inputs['Color'].default_value = (0.985, 0.995, 0.99, 1)
    mc = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(lp.outputs['Is Camera Ray'], mc.inputs['Fac']); nt.links.new(tr2.outputs['BSDF'], mc.inputs[1]); nt.links.new(mx.outputs['Shader'], mc.inputs[2])
    nt.links.new(mc.outputs['Shader'], out.inputs['Surface']); return m
GLASS = thin_glass('glass')
def liquid_mat(name):
    m = mat(name, (1, 1, 1), 0.0, trans=1.0, ior=1.333); nt = m.node_tree; va = nt.nodes.new('ShaderNodeVolumeAbsorption')
    va.inputs['Color'].default_value = (0.06, 0.08, 0.32, 1); va.inputs['Density'].default_value = 0.0
    nt.links.new(va.outputs['Volume'], nt.nodes['Material Output'].inputs['Volume']); return m, va
def shadow_pass(m):
    """shadow rays go straight through (the volume still darkens them): things inside or behind liquid get direct light instead of
    only caustic light, which in Cycles comes out as speckle"""
    nt = m.node_tree; out = nt.nodes['Material Output']; link = next(l for l in nt.links if l.to_socket == out.inputs['Surface']); src = link.from_socket
    lp = nt.nodes.new('ShaderNodeLightPath'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.remove(link); nt.links.new(lp.outputs['Is Shadow Ray'], mx.inputs['Fac']); nt.links.new(src, mx.inputs[1]); nt.links.new(tr.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
LIQB, VAB = liquid_mat('liquidB'); LIQA, _ = liquid_mat('liquidA'); LIQ2, VA2 = liquid_mat('liquid2')
for _m in (LIQB, LIQA, LIQ2, GLASS): shadow_pass(_m)
def set_dark(m, va, d):            # the starch-iodine blue-black: absorption in the volume plus a tinted surface (so it reads even in thin spots)
    va.inputs['Density'].default_value = d; k = min(1.0, d / 140.0); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (lerp(1, 0.006, k), lerp(1, 0.008, k), lerp(1, 0.03, k), 1); b.inputs['Roughness'].default_value = 0.0
BENCH = noisy(mat('bench', (0.035, 0.037, 0.04), 0.32, coat=0.4), 6.0, 0.25, 0.08)
WALL = noisy(mat('wall', (0.06, 0.065, 0.075), 0.8), 3.0, 0.1, 0.05)
WHITEP = noisy(mat('plate_white', (0.86, 0.86, 0.84), 0.35, coat=0.2), 30.0, 0.04, 0.05)
CERAMIC = mat('ceramic', (0.1, 0.105, 0.11), 0.3, metal=0.6)    # a dark aluminium top plate: a white one mirrors into the black liquid and greys it out
BLACKP = mat('black_plastic', (0.02, 0.02, 0.022), 0.35)
PTFE = mat('ptfe', (0.95, 0.95, 0.93), 0.45)
PRINT = mat('print', (0.95, 0.95, 0.95), 0.4)
AMBER = mat('amber', (0.55, 0.25, 0.05), 0.05, trans=1.0, ior=1.5)

# ---------------------------------------------------------------- geometry helpers
def obj(name, me, m=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.location = loc
    if m: o.data.materials.append(m)
    return o
def lathe(name, prof, seg=128, m=None, closed=False):
    """prof: [(r, z)...] around z. closed=True joins the last point back to the first (a solid wall section)."""
    vs, fs = [], []; n = len(prof)
    for i in range(seg):
        a_ = 2 * math.pi * i / seg; c_, s_ = math.cos(a_), math.sin(a_)
        for r, z in prof: vs.append((r * c_, r * s_, z))
    for i in range(seg):
        i2 = (i + 1) % seg
        for k in range(n - 1 + (1 if closed else 0)):
            k2 = (k + 1) % n; fs.append((i * n + k, i2 * n + k, i2 * n + k2, i * n + k2))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    for p in me.polygons: p.use_smooth = True
    return obj(name, me, m)
def box(name, sx, sy, sz, loc, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if bevel: md = o.modifiers.new('bv', 'BEVEL'); md.width = bevel; md.segments = 4
    o.data.materials.append(m); [setattr(p, 'use_smooth', True) for p in o.data.polygons]; return o
def sphere(name, r, loc, m, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2); o = bpy.context.active_object; o.name = name
    o.data.materials.append(m); [setattr(p, 'use_smooth', True) for p in o.data.polygons]; return o
def cyl(name, r, d, loc, m, rot=(0, 0, 0), seg=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=seg); o = bpy.context.active_object; o.name = name
    o.data.materials.append(m); [setattr(p, 'use_smooth', True) for p in o.data.polygons]; return o

# ================================================================ THE LAB (around the origin; bench top at z = 0)
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 0)); bench = bpy.context.active_object; bench.data.materials.append(BENCH)
# a curved backdrop wall, far behind and out of focus
wall = lathe('wall', [(1.6, -0.02), (1.6, 1.6)], 96, WALL); wall.scale = (1, 1, 1)
# stir plate (white body, ceramic top, two black knobs) with the beaker on it
SP = box('stirplate', 0.18, 0.2, 0.055, (0, 0, 0.0275), WHITEP, 0.008)
box('sp_top', 0.165, 0.165, 0.006, (0, 0.012, 0.058), CERAMIC, 0.003)
for x in (-0.04, 0.04): cyl('knob', 0.011, 0.012, (x, -0.1, 0.028), BLACKP, rot=(math.pi / 2, 0, 0))
BASEZ = 0.061                                      # beaker sits here
BEAK = Vector((0, 0.012, BASEZ))
# 600 mL beaker: 2 mm wall, thick base, rolled rim
R_OUT, HB = 0.045, 0.125
BEAKER = lathe('beaker', [(0.0, 0.0), (R_OUT - 0.004, 0.0), (R_OUT, 0.004), (R_OUT, HB - 0.002), (R_OUT + 0.0025, HB), (R_OUT - 0.0005, HB + 0.0015),
                          (R_OUT - 0.002, HB), (R_OUT - 0.002, 0.0055), (R_OUT - 0.006, 0.0035), (0.0, 0.0035)], 160, GLASS, closed=True)
BEAKER.location = (0, 0.012, BASEZ)
# printed graduation marks (white enamel) on the front
for i, zz in enumerate([0.03, 0.045, 0.06, 0.075, 0.09, 0.105]):
    L = 0.012 if i % 2 == 0 else 0.007
    mk = box('mark', L, 0.0006, 0.0011, (0.0, 0, 0), PRINT); ang = math.radians(-100)
    mk.location = (math.cos(ang) * (R_OUT + 0.0003) + 0.0, 0.012 + math.sin(ang) * (R_OUT + 0.0003), BASEZ + zz); mk.rotation_euler = (0, 0, ang + math.pi / 2)
# the liquid in the beaker: rebuilt every frame (level, vortex)
R_IN = R_OUT - 0.0021          # the liquid sits just inside the (thin-shaded) glass wall
LIQ = obj('liquidB', bpy.data.meshes.new('liquidB'), LIQB, (0, 0.012, BASEZ))
def build_liquid(o, level, depth, phase, ripple=0.0006):
    """solid of revolution: flat bottom at 0.004, wall up to level, top surface dipping into a vortex of depth 'depth' at the centre."""
    me = o.data; bm = bmesh.new(); NR, NA = 28, 96
    verts = {}
    def top(r, ang):
        z = level - depth * (1 - (r / R_IN) ** 2) ** 2.2 + ripple * math.sin(ang * 3 + phase * 2 + r * 300) * (r / R_IN) + 0.0012 * (r / R_IN) ** 12   # meniscus at the wall
        return z
    rows = []
    for j in range(NR + 1):
        r = R_IN * (j / NR) ** 0.8; row = []
        for i in range(NA):
            ang = 2 * math.pi * i / NA; row.append(bm.verts.new((r * math.cos(ang), r * math.sin(ang), top(r, ang))))
        rows.append(row)
    bot = [bm.verts.new((R_IN * math.cos(2 * math.pi * i / NA), R_IN * math.sin(2 * math.pi * i / NA), 0.0062)) for i in range(NA)]   # above the glass base: no glass surface may sit inside the liquid (it broke the volume's absorption)
    cb = bm.verts.new((0, 0, 0.0062))
    for j in range(NR):
        for i in range(NA):
            i2 = (i + 1) % NA; bm.faces.new((rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]))
    for i in range(NA):
        i2 = (i + 1) % NA; bm.faces.new((rows[NR][i], rows[NR][i2], bot[i2], bot[i])); bm.faces.new((bot[i2], cb, bot[i]) if True else ())
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.smooth = True
    bm.to_mesh(me); bm.free(); me.update()
# the stir bar (white PTFE capsule) spinning on the bottom
bpy.ops.mesh.primitive_cylinder_add(radius=0.0042, depth=0.026, location=(0, 0.012, BASEZ + 0.0108), rotation=(0, math.pi / 2, 0), vertices=24)
BAR = bpy.context.active_object; BAR.data.materials.append(PTFE); [setattr(p, 'use_smooth', True) for p in BAR.data.polygons]
md = BAR.modifiers.new('bv', 'BEVEL'); md.width = 0.0035; md.segments = 6; BAR.rotation_mode = 'ZYX'
# a 250 mL separatory funnel on a ring stand, holding liquid A; its tap opens and it drains into the beaker (no hands in shot)
FUN_OUT = [(0.0042, 0.0), (0.0045, 0.07), (0.006, 0.078), (0.038, 0.15), (0.045, 0.18), (0.04, 0.205), (0.013, 0.235), (0.013, 0.26), (0.0155, 0.262), (0.0155, 0.266), (0.0105, 0.264)]
FUN_IN = [(0.0105, 0.234), (0.0375, 0.204), (0.0425, 0.18), (0.0355, 0.152), (0.004, 0.08), (0.0022, 0.072), (0.0022, 0.0015)]
FUNNEL = lathe('funnel', FUN_OUT + FUN_IN, 128, GLASS, closed=True)
TIP = BEAK + Vector((0.0, 0.016, HB + 0.012))
FUNNEL.location = TIP
cyl('stopper', 0.012, 0.022, TIP + Vector((0, 0, 0.27)), PTFE)
TAP = cyl('tap', 0.0065, 0.03, TIP + Vector((0, 0, 0.055)), PTFE, rot=(0, math.pi / 2, 0)); TAP.rotation_mode = 'XYZ'
TAPH = box('taph', 0.026, 0.004, 0.009, TIP + Vector((0.022, 0, 0.055)), PTFE, 0.0015)
FLIQ = lathe('funliq', [(0.0, 0.0815), (0.0032, 0.0815), (0.0347, 0.152), (0.0417, 0.18), (0.0367, 0.2035), (0.0097, 0.2335), (0.0, 0.2335)], 96, LIQA, closed=True); FLIQ.location = TIP   # 0.8 mm inside the glass
CUT = box('cutter', 1, 1, 1, (0, 0, 0), BLACKP); CUT.hide_render = True; CUT.display_type = 'WIRE'
bo = FLIQ.modifiers.new('cut', 'BOOLEAN'); bo.operation = 'INTERSECT'; bo.object = CUT; bo.solver = 'EXACT'
STEEL = mat('steel', (0.62, 0.63, 0.65), 0.28, metal=1.0); CAST = noisy(mat('cast', (0.08, 0.085, 0.09), 0.55, metal=0.3), 60, 0.2, 0.1)
box('standbase', 0.16, 0.24, 0.014, (-0.17, 0.09, 0.007), CAST, 0.003)
cyl('rod', 0.0065, 0.62, (-0.17, 0.14, 0.31), STEEL)
ring_z = TIP.z + 0.165
bpy.ops.mesh.primitive_torus_add(major_radius=0.047, minor_radius=0.0035, location=(TIP.x, TIP.y, ring_z)); RINGO = bpy.context.active_object; RINGO.data.materials.append(STEEL)
cyl('arm', 0.004, 0.13, (-0.105, (0.14 + TIP.y) / 2, ring_z), STEEL, rot=(0, math.pi / 2, math.atan2(TIP.y - 0.14, TIP.x + 0.17) )) 
box('clamp', 0.022, 0.022, 0.03, (-0.17, 0.14, ring_z), CAST, 0.002)
# the pour stream (a tube along a curve), and a second beaker for the last beat
cd = bpy.data.curves.new('stream', 'CURVE'); cd.dimensions = '3D'; cd.bevel_depth = 0.0024; cd.bevel_resolution = 6; sp = cd.splines.new('BEZIER'); sp.bezier_points.add(1)
STREAM = obj('stream', cd, LIQA)
BEAKER2 = BEAKER.copy(); BEAKER2.data = BEAKER.data; S.collection.objects.link(BEAKER2)
LIQ2O = obj('liquid2', bpy.data.meshes.new('liquid2'), LIQ2, (0, 0, 0))
SP2 = [o for o in S.objects if o.name.startswith(('stirplate', 'sp_top', 'knob'))]
# background props, out of focus: amber reagent bottles, a wash bottle, a second flask
for i, (x, y) in enumerate([(-0.32, 0.38), (-0.25, 0.42), (0.3, 0.4)]):
    bt = lathe('bottle', [(0, 0), (0.035, 0), (0.037, 0.004), (0.037, 0.14), (0.022, 0.17), (0.014, 0.18), (0.014, 0.2), (0, 0.2)], 64, AMBER); bt.location = (x, y, 0)
    cap = cyl('cap', 0.016, 0.022, (x, y, 0.211), BLACKP)
wb = lathe('washbottle', [(0, 0), (0.04, 0), (0.042, 0.005), (0.042, 0.15), (0.02, 0.18), (0, 0.18)], 64, mat('wash', (0.9, 0.92, 0.95), 0.3, trans=0.6, ior=1.45)); wb.location = (0.42, 0.25, 0)

# ---------------------------------------------------------------- lights (big soft key above-left, two tall strips behind for glass edges, a bounce card)
def area(name, loc, rot, size, sizey, power, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = sizey; ld.energy = power; ld.color = color
    o = bpy.data.objects.new(name, ld); S.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    o.visible_transmission = False; o.visible_glossy = False     # small bright lights found at random through glass and liquid are fireflies;
    return o                                                     # what the glass reflects are the big soft cards below
def card(name, loc, rot, sx, sy, strength):
    """a large dim emissive card: what the glass and liquid reflect (softboxes). Not seen by the camera, adds no light of its own."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); e_ = nt.nodes.new('ShaderNodeEmission')
    e_.inputs['Strength'].default_value = strength; nt.links.new(e_.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); o.data.materials.append(m)
    o.visible_camera = False; o.visible_diffuse = False; o.visible_shadow = False; o.visible_volume_scatter = False; return o
KEY = area('key', (-0.5, -0.35, 0.9), (math.radians(38), 0, math.radians(-40)), 0.9, 0.6, 45)
area('stripL', (-0.35, 0.45, 0.3), (math.radians(-70), 0, math.radians(30)), 0.12, 0.9, 30)
area('stripR', (0.38, 0.45, 0.3), (math.radians(-70), 0, math.radians(-35)), 0.12, 0.9, 30)
area('fill', (0.6, -0.5, 0.35), (math.radians(65), 0, math.radians(50)), 0.8, 0.8, 5, (1.0, 0.96, 0.9))
card('cardKey', (-0.5, -0.35, 0.9), (math.radians(38), 0, math.radians(-40)), 0.9, 0.6, 6.0)
card('cardL', (-0.42, 0.5, 0.32), (math.radians(-70), 0, math.radians(30)), 0.35, 0.9, 4.0)
card('cardR', (0.45, 0.5, 0.32), (math.radians(-70), 0, math.radians(-35)), 0.35, 0.9, 4.0)
card('cardFront', (0.0, -0.9, 0.35), (math.radians(80), 0, 0), 1.2, 0.5, 0.6)
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; W_.node_tree.nodes['Background'].inputs['Color'].default_value = (0.012, 0.013, 0.016, 1)

# ================================================================ THE MOLECULE SET (far away at x = 60; units are ~1 per angstrom-ish, scaled up)
MX = Vector((60, 0, 1.5))
def mmat(name, col, rough=0.28, emit=0.0):
    m = mat(name, col, rough, coat=0.7);
    if emit: b = m.node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    return m
M_I = mmat('iod', (0.33, 0.08, 0.55)); M_IG = mmat('iodide', (0.45, 0.2, 0.75), 0.25, 0.6); M_S = mmat('sul', (0.95, 0.78, 0.12)); M_O = mmat('oxy', (0.85, 0.08, 0.06)); M_H = mmat('hyd', (0.92, 0.92, 0.92)); M_C = mmat('carb', (0.18, 0.18, 0.2))
BOND = mmat('bond', (0.75, 0.75, 0.78), 0.35)
# backdrop: a dark blue glow, floating specks
bpy.ops.mesh.primitive_uv_sphere_add(radius=40, location=MX, segments=48, ring_count=24); BG = bpy.context.active_object
bgm = bpy.data.materials.new('bg'); bgm.use_nodes = True; nt = bgm.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); em = nt.nodes.new('ShaderNodeEmission')
gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.03, 0.03, 0.03)
ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.004, 0.008, 0.02, 1); ramp.color_ramp.elements[1].color = (0.02, 0.05, 0.12, 1)
nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector']); nt.links.new(gr.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
em.inputs['Strength'].default_value = 1.0; nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); BG.data.materials.append(bgm); BG.data.polygons.foreach_set('use_smooth', [True] * len(BG.data.polygons))
SPECK = mmat('speck', (0.5, 0.7, 1.0), 0.5, 0.8)
for i in range(70): sphere('speck', 0.03 + 0.03 * h1(i), MX + Vector(((h1(i * 3) - 0.5) * 18, (h1(i * 5) - 0.5) * 18 + 4, (h1(i * 7) - 0.5) * 14)), SPECK, 12)
area('mkey', tuple(MX + Vector((-6, -6, 8))), (math.radians(45), 0, math.radians(-45)), 6, 6, 9000, (0.9, 0.95, 1.0))
area('mrim', tuple(MX + Vector((6, 8, 3))), (math.radians(-100), 0, math.radians(-150)), 4, 4, 5000, (0.6, 0.75, 1.0))
def bond_between(name, p, q, r=0.07):
    d = q - p; o = cyl(name, r, d.length, (p + q) / 2, BOND, seg=16); o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return o
def group(name):
    g = bpy.data.objects.new(name, None); S.collection.objects.link(g); return g
def parent(o, g): o.parent = g; return o
# I2 molecules (a pair) and their split halves (iodide), the 'eraser' (bisulfite: S, 3 O, H) and what it becomes (sulfate: S, 4 O)
def make_i2(k):
    g = group(f'I2_{k}'); a_ = parent(sphere('I', 0.42, (0, 0, 0), M_I, 40), g); b_ = parent(sphere('I', 0.42, (0, 0, 0), M_I, 40), g); bd = parent(bond_between('bI', Vector((-0.5, 0, 0)), Vector((0.5, 0, 0)), 0.1), g)
    a_.location = (-0.5, 0, 0); b_.location = (0.5, 0, 0); g['parts'] = [a_.name, b_.name, bd.name]; return g
def make_eraser(k):
    g = group(f'ER_{k}'); parent(sphere('S', 0.36, (0, 0, 0), M_S, 32), g)
    for j, v in enumerate([Vector((0.6, 0, 0.25)), Vector((-0.3, 0.52, 0.25)), Vector((-0.3, -0.52, 0.25))]):
        parent(sphere('O', 0.3, v, M_O, 28), g); parent(bond_between('b', Vector((0, 0, 0)), v, 0.08), g)
    parent(sphere('H', 0.2, (0.95, 0, 0.55), M_H, 20), g); parent(bond_between('b', Vector((0.6, 0, 0.25)), Vector((0.95, 0, 0.55)), 0.06), g); return g
NI, NE = 7, 7
I2 = [make_i2(k) for k in range(NI)]; ER = [make_eraser(k) for k in range(NE)]
IONS = [sphere('ion', 0.44, (0, 0, 0), M_IG, 32) for _ in range(2 * NI)]
# starch: an amylose coil, 6 glucose rings per turn; iodine (a chain of purple atoms) slides inside along its axis
STARCH = group('starch'); RING = []
NG, RH, PITCH = 30, 1.25, 1.55
for k in range(NG):
    th = 2 * math.pi * k / 6.0; c_ = Vector((RH * math.cos(th), RH * math.sin(th), PITCH * k / 6.0))
    rg = group('glc'); rg.parent = STARCH; rg.location = c_; rg.rotation_euler = (0.4, 0, th + math.pi / 2)
    pts = [Vector((0.42 * math.cos(2 * math.pi * j / 6), 0.42 * math.sin(2 * math.pi * j / 6), 0)) for j in range(6)]
    for j, p in enumerate(pts):
        parent(sphere('a', 0.16, p, M_O if j == 0 else M_C, 20), rg); parent(bond_between('rb', p, pts[(j + 1) % 6], 0.05), rg)
    parent(sphere('oh', 0.12, pts[2] * 1.7, M_O, 16), rg); RING.append(rg)
for k in range(NG - 1):   # links between rings
    p = Vector((RH * math.cos(2 * math.pi * k / 6), RH * math.sin(2 * math.pi * k / 6), PITCH * k / 6)); q = Vector((RH * math.cos(2 * math.pi * (k + 1) / 6), RH * math.sin(2 * math.pi * (k + 1) / 6), PITCH * (k + 1) / 6))
    parent(bond_between('gl', p, q, 0.05), STARCH)
M_IC = mmat('iodc', (0.33, 0.08, 0.55), emit=0.001)      # the iodine inside the coil: its own material so it can glow as it soaks up light
CHAIN = [sphere('Ic', 0.4, (0, 0, 0), M_IC, 32) for _ in range(9)]
# the coil stands up (the frame is tall) and leans a little to the right
COIL_TILT = math.radians(18); COIL_R = Euler((0, COIL_TILT, 0)).to_matrix()
def axis_pt(s): return MX + COIL_R @ Vector((0, 0, s))          # s = distance from the coil centre along its axis
def coil_show(): show(STARCH, MX - COIL_R @ Vector((0, 0, PITCH * (NG - 1) / 12.0)), (0, COIL_TILT, 0))
# light (rainbow) that gets soaked up inside the coil: each colour is a glowing wave (red long, violet short) with a soft glow around it
RAYC = [(1, 0.12, 0.08), (1, 0.45, 0.05), (1, 0.9, 0.12), (0.2, 1, 0.25), (0.15, 0.5, 1), (0.5, 0.2, 1)]
RAYL = [1.5, 1.32, 1.16, 1.0, 0.85, 0.72]          # wavelength (scene units)
NP_W = 120
def glow_mat(name, c_, strength, alpha, power):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    eh = nt.nodes.new('ShaderNodeEmission'); eh.inputs['Color'].default_value = (*c_, 1); eh.inputs['Strength'].default_value = strength
    if alpha >= 1: nt.links.new(eh.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m, eh
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(lw.outputs['Facing'], inv.inputs[1])
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = power; nt.links.new(inv.outputs[0], pw.inputs[0])
    sc = nt.nodes.new('ShaderNodeMath'); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = alpha; nt.links.new(pw.outputs[0], sc.inputs[0])
    mx_ = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(sc.outputs[0], mx_.inputs[0]); nt.links.new(tr.outputs[0], mx_.inputs[1]); nt.links.new(eh.outputs[0], mx_.inputs[2])
    nt.links.new(mx_.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m, eh
def wave_curve(name, bevel, m):
    cd = bpy.data.curves.new(name, 'CURVE'); cd.dimensions = '3D'; cd.bevel_depth = bevel; cd.bevel_resolution = 4; cd.use_fill_caps = True
    sp = cd.splines.new('POLY'); sp.points.add(NP_W - 1); cd.materials.append(m)
    o = bpy.data.objects.new(name, cd); S.collection.objects.link(o); o.location = MX; o.visible_shadow = False; return o
RAYS = []
for k, c_ in enumerate(RAYC):
    mc, e_ = glow_mat(f'ray{k}', c_, 3.2, 1.0, 1.0); mh, eh = glow_mat(f'rayh{k}', c_, 2.4, 0.42, 3.0)
    RAYS.append((wave_curve(f'ray{k}', 0.045, mc), wave_curve(f'rayh{k}', 0.2, mh), e_, eh))
def set_wave(o, ax, f_, b_, front, lam, amp=0.22):
    """the wave shape rides with the light's front; it stops (is soaked up) at the coil's axis"""
    for i, pt in enumerate(o.data.splines[0].points):
        x = f_ + (b_ - f_) * i / (NP_W - 1); taper = min(1.0, (x - f_) / 0.25 + 0.15, (b_ - x) / 0.6)
        pt.co = (ax.x - MX.x + x, ax.y - MX.y, ax.z - MX.z + amp * max(0.0, taper) * math.sin(2 * math.pi * (x - front) / lam), 1.0)

# ---------------------------------------------------------------- camera
CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True
def look(cp, ct, lens=85, fstop=4.0, focus=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'; CAM.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop; CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus else d.length

# ================================================================ the story, frame by frame
BEAK = Vector((0, 0.012, BASEZ))
T_POUR = B[2] + 0.5                     # the real pour (beat 2); the hook shows a sped-up run
T_SNAP = B[10] + 0.6                    # the moment it turns
def stream_on(p0, p1, on, wob):
    STREAM.hide_render = not on
    if not on: return
    sp = STREAM.data.splines[0]; a0, a1 = sp.bezier_points
    a0.co = p0; a0.handle_left = p0 + Vector((0, 0, 0.005)); a0.handle_right = p0 + Vector((0.0006 * math.sin(wob), 0, -0.01))
    a1.co = p1; a1.handle_left = p1 + Vector((0.0008 * math.sin(wob * 1.3), 0, 0.012)); a1.handle_right = p1 + Vector((0, 0, -0.005))
    STREAM.data.bevel_depth = 0.0019
def visible(objs, on):
    for o in objs: o.hide_render = not on
LAB = [o for o in S.objects if o.location.x < 30 and o.name not in ('cam',)]
MOL = [o for o in S.objects if o.location.x >= 30 or (o.parent and o.parent.location.x >= 30)]
def lab_state(t, level, vortex, dark, fun_level, tap_open):
    build_liquid(LIQ, level, vortex, t * 6.0); set_dark(LIQB, VAB, dark)
    BAR.location = BEAK + Vector((0, 0, 0.0108)); BAR.rotation_euler = (0, math.pi / 2, t * 2 * math.pi * 1.6)
    CUT.location = (0, 0, TIP.z + fun_level - 0.5); FLIQ.hide_render = fun_level < 0.081
    TAP.rotation_euler = (0, math.pi / 2, 0); TAPH.rotation_euler = (math.radians(90) * tap_open, 0, 0)
    stream_on(TIP + Vector((0, 0, -0.0005)), BEAK + Vector((0.0, 0.016, level - vortex * 0.55)), tap_open > 0.5 and fun_level > 0.081, t * 9)
def mol_reset():
    for g in I2 + ER: g.hide_render = True; [setattr(c, 'hide_render', True) for c in g.children]
    for o in IONS + CHAIN: o.hide_render = True
    STARCH.hide_render = True; [setattr(c, 'hide_render', True) for c in STARCH.children_recursive]
    for o, h_, _, _ in RAYS: o.hide_render = h_.hide_render = True
    M_IC.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
def show(g, p, rot=(0, 0, 0), sc=1.0):
    g.hide_render = False; [setattr(c, 'hide_render', False) for c in g.children_recursive]; g.location = p; g.rotation_euler = rot; g.scale = (sc, sc, sc)
ZORD = [3, 0, 5, 2, 6, 1, 4]      # pairs stack up and down the tall frame (not in birth order, so it doesn't fill like a ladder)
def race(t0, t, erasers_left):
    """iodine pairs appear one by one; while erasers are left, each pair gets grabbed and split into two iodide ions"""
    for k in range(NI):
        tb = t0 + 0.35 * k; age = t - tb
        side = 1 if k % 2 == 0 else -1
        home = MX + Vector((side * (0.5 + 1.0 * h1(k * 2)), (h1(k * 3) - 0.5) * 2.0, (ZORD[k] - 3) * 1.0 + (h1(k * 4) - 0.5) * 0.4))
        if age < 0: continue
        er = k < erasers_left
        if er and age > 0.9:                       # split: two ions drift apart
            for j in (0, 1):
                io = IONS[2 * k + j]; io.hide_render = False; s_ = (-1) ** j; d_ = age - 0.9
                io.location = home + Vector((s_ * (0.5 + 0.6 * d_), -0.25 * d_, 0.3 * s_ * d_))
        else: show(I2[k], home, (0.3 * age, 0.5 * k, 0.4 * age), sm(clamp(age / 0.25, 0, 1)))
        if er:                                     # the eraser flies in from its own side, grabs the pair, then drifts off
            e_ = ER[k]; tgt = home + Vector((0, -0.9, 0.5)); start = tgt + Vector((side * 3.0, -1.6, 1.0 if ZORD[k] < 3 else -1.0))
            show(e_, start.lerp(tgt, sm(clamp(age / 0.9, 0, 1))) + (Vector((side * 0.7, 0.9, 0.3)) * (age - 0.9) if age > 0.9 else Vector()), (age * 1.3, k, age))
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    lab = nb in (0, 1, 2, 4, 10, 11); visible(LAB, lab); visible([BG], not lab); mol_reset(); CUT.hide_render = True
    LIQ2O.hide_render = BEAKER2.hide_render = True    # AFTER visible(): the second beaker sat on top of the first (same mesh, same spot) and the doubled glass rendered as speckle
    if not lab:
        for o in S.objects:
            if o.name.startswith('speck') or o.name.startswith(('mkey', 'mrim')): o.hide_render = False
    if nb == 0:      # hook: a sped-up run: the pour is already going, then the snap
        dark = 140 * smooth(1.85, 2.15, lt); lab_state(t, 0.05 + 0.03 * smooth(0, 1.6, lt), 0.018, dark, 0.15 - 0.065 * smooth(0, 1.6, lt), 1.0 if lt < 1.6 else 0.0)
        look(BEAK + Vector((0.16, -0.36, 0.14)) + Vector((0, 0.04 * u, -0.01 * u)), BEAK + Vector((0, 0, 0.06)), 70, 3.2)
    elif nb == 1:    # the setup, wide: the plate, the beaker (clear), the flask beside it
        lab_state(t, 0.05, 0.016, 0, 0.2, 0.0)
        a_ = math.radians(-58 + 18 * u); look(BEAK + Vector((0.5 * math.sin(a_), -0.5 * math.cos(a_), 0.2)), BEAK + Vector((0.0, 0, 0.13)), 50, 5.6)
    elif nb == 2:    # the real pour starts (the clock starts)
        k = smooth(0.1, 0.3, u); lab_state(t, 0.05 + 0.03 * smooth(0.3, 1.0, u), 0.016, 0, 0.2 - 0.119 * smooth(0.3, 1.0, u), k)
        look(BEAK + Vector((-0.3, -0.34, 0.17)), BEAK + Vector((0, 0, 0.12)), 60, 4.0)
    elif nb in (3, 5, 6):    # molecules: iodine made, erased; the race; the eraser runs out
        if nb == 3: race(B[3], t, NE)
        elif nb == 5: race(B[5] - 1.2, t, NE)
        else: race(B[6] - 2.0, t, 3)
        look(MX + Vector((0.8, -14 + 1.5 * u, 2.3)), MX + Vector((0, 0, -0.75)), 36, 2.0)   # aim low so the pairs sit between the label and the captions
    elif nb == 4:    # back at the bench: stirring, clear, the timer running
        lab_state(t, 0.08, 0.02, 0, 0.0, 0.0)
        look(BEAK + Vector((0.08, -0.4, 0.12)) + Vector((0, 0.03 * u, 0)), BEAK + Vector((0, 0, 0.07)), 85, 3.5)
    elif nb == 7:    # free iodine drifts in to the starch coil (standing up, it fills the tall frame)
        coil_show()
        for k in range(5):
            s = (k - 2) * 1.4 + (h1(k + 9) - 0.5) * 0.5; ax = axis_pt(s); end = ax + Vector((2.4 + 0.4 * h1(k), (h1(k) - 0.5) * 1.5, 0))
            show(I2[k], end + Vector((2.6 + 0.6 * h1(k + 3), 0, 0.3 * (h1(k + 5) - 0.5))) * (1 - sm(u)), (u + k, k, 0.5 * u))
        a_ = math.radians(-6 + 10 * u)
        look(MX + Vector((15 * math.sin(a_), -15 * math.cos(a_), 1.5)), MX + Vector((0.8, 0, -0.9)), 35, 2.8)
    elif nb == 8:    # iodine slides into the coil like beads on a string; the camera rides down with the lead bead
        coil_show(); off = 9.0 * (1 - sm(clamp(u * 1.2, 0, 1)))
        for k, o in enumerate(CHAIN): o.hide_render = False; o.location = axis_pt(-3.28 + 0.82 * k + off)
        s_ = 2.4 - 2.6 * sm(u); a_ = math.radians(22 - 10 * u)
        look(axis_pt(s_) + Vector((8.6 * math.sin(a_), -8.6 * math.cos(a_), 1.4)), axis_pt(s_) + Vector((0, 0, -0.6)), 45, 2.4)
    elif nb == 9:    # light of every colour goes in and doesn't come out; the iodine glows as it soaks it up
        coil_show(); glow = 0.0
        for k, o in enumerate(CHAIN): o.hide_render = False; o.location = axis_pt(-3.28 + 0.82 * k)
        for k, (o, h_, e_, eh) in enumerate(RAYS):
            ax = axis_pt((k - 2.5) * 1.05); tk = 0.06 + 0.075 * k; ln = 4.2
            front = 5.8 - 20 * (u - tk); back = front + ln; f_ = max(front, 0.0); b_ = min(back, 12.0)
            on = u >= tk and b_ > f_ + 0.02
            for ob in (o, h_):
                ob.hide_render = not on
                if on: set_wave(ob, ax, f_, b_, front, RAYL[k])
            if on and front < 0.6: glow += min(1.0, (0.6 - front) / 0.6)
        M_IC.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.15 + 0.9 * min(2.0, glow)
        look(MX + Vector((2.6, -13, 0.8)), MX + Vector((1.4, 0, -0.9)), 40, 3.2)
    elif nb == 10:   # the snap, slowed down
        k = smooth(0.45, 0.85, u); lab_state(t, 0.08, 0.02, 140 * k, 0.0, 0.0)
        look(BEAK + Vector((-0.05, -0.38, 0.1)), BEAK + Vector((0, 0, 0.065)), 85, 3.5)
    elif nb == 11:   # two beakers: more eraser on the right, so it waits longer; it turns just before the loop
        lab_state(t, 0.08, 0.02, 140, 0.0, 0.0); BEAKER2.hide_render = False; LIQ2O.hide_render = False
        BEAKER2.location = BEAK + Vector((0.12, 0, 0)); LIQ2O.location = BEAKER2.location; build_liquid(LIQ2O, 0.08, 0.0, t * 6); set_dark(LIQ2, VA2, 140 * smooth(0.82, 0.92, u))
        look(BEAK + Vector((0.06, -0.48, 0.16)), BEAK + Vector((0.06, 0, 0.06)), 60, 5.0)
os.makedirs(a.out, exist_ok=True)
only = [int(x) for x in a.only.split(',')] if a.only else None
for f in (only or range(a.f0, a.f1)):
    frame(f); S.render.filepath = os.path.join(a.out, f'f_{f:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', f, flush=True)
