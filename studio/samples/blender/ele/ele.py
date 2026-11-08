# Elephant toothpaste, built and rendered in Blender (Cycles): a 500 mL graduated cylinder of peroxide, soap and food colour on a tray,
# the helper poured in, a striped foam snake that shoots out and piles on the tray, steam; molecule close-ups (peroxide falling apart,
# the iodide helper doing it over and over) and soap bubbles with real thin-film colour.
#   python3 ele.py OUTDIR F0 F1 [--samples 64] [--scale 1.0] [--only f,f] [--stride J --total N]
#   --stride J: this job is number F0 // (F1 - F0) of J; it renders frames job, job + J, job + 2J ... < N, named f_F0, f_F0+1 ... in order
#   (spreads heavy and light shots evenly over the farm's runners; the clips are put back in order afterwards)
import sys, os, math, json, argparse
import bpy, bmesh, addon_utils
from mathutils import Vector, Matrix, Euler, noise as mnoise

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int); ap.add_argument('f1', type=int)
ap.add_argument('--samples', type=int, default=64); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--only', default='')
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
TM = json.load(open(os.path.join(HERE, 'times.json'))); B, DUR, TOTAL = TM['starts'], TM['durs'], TM['total']
FPS = 30
STRIDE = json.load(open(os.path.join(HERE, 'stride.json'))) if os.path.exists(os.path.join(HERE, 'stride.json')) else None
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
C.max_bounces = 14; C.diffuse_bounces = 3; C.glossy_bounces = 6; C.transmission_bounces = 14; C.volume_bounces = 1; C.transparent_max_bounces = 16
C.caustics_reflective = False; C.caustics_refractive = False; C.sample_clamp_indirect = 8.0; C.sample_clamp_direct = 0.0
C.volume_step_rate = 2.0
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'
S.render.film_transparent = False

# ---------------------------------------------------------------- materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, trans=0.0, ior=1.45, coat=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior; b.inputs['Coat Weight'].default_value = coat; b.inputs['Alpha'].default_value = alpha
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    return m
def noisy(m, scale=40.0, amt=0.15, rough_amt=0.1):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    base = b.inputs['Base Color'].default_value[:]; mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs['A'].default_value = base; mx.inputs['B'].default_value = tuple(c * (1 - amt) for c in base[:3]) + (1,)
    nt.links.new(nz.outputs['Fac'], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    r0 = b.inputs['Roughness'].default_value; mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = r0 - rough_amt; mr.inputs['To Max'].default_value = r0 + rough_amt
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness']); return m
def thin_glass(name):
    """lab glass as thin glass (same as the iodine clock): Fresnel reflection, for camera rays only, over a see-through layer that greens at the edges"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.5
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.22
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.0; gl.inputs['Color'].default_value = (0.75, 0.75, 0.75, 1)
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.985, 0.995, 0.99, 1); ramp.color_ramp.elements[1].color = (0.42, 0.52, 0.48, 1)
    nt.links.new(lw.outputs['Facing'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], tr.inputs['Color'])
    geo = nt.nodes.new('ShaderNodeNewGeometry'); fm = nt.nodes.new('ShaderNodeMath'); fm.operation = 'SUBTRACT'; fm.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs['Backfacing'], fm.inputs[1]); fx = nt.nodes.new('ShaderNodeMath'); fx.operation = 'MULTIPLY'
    nt.links.new(fr.outputs['Fac'], fx.inputs[0]); nt.links.new(fm.outputs['Value'], fx.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fx.outputs['Value'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(gl.outputs['BSDF'], mx.inputs[2])
    lp = nt.nodes.new('ShaderNodeLightPath'); tr2 = nt.nodes.new('ShaderNodeBsdfTransparent'); tr2.inputs['Color'].default_value = (0.985, 0.995, 0.99, 1)
    mc = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(lp.outputs['Is Camera Ray'], mc.inputs['Fac']); nt.links.new(tr2.outputs['BSDF'], mc.inputs[1]); nt.links.new(mx.outputs['Shader'], mc.inputs[2])
    nt.links.new(mc.outputs['Shader'], out.inputs['Surface']); return m
GLASS = thin_glass('glass')
def liquid_mat(name, tint=(0.97, 0.98, 1.0)):
    m = mat(name, tint, 0.0, trans=1.0, ior=1.333); return m
def shadow_pass(m):
    """shadow rays go straight through, so things in or behind liquid get direct light instead of caustic speckle"""
    nt = m.node_tree; out = nt.nodes['Material Output']; link = next(l for l in nt.links if l.to_socket == out.inputs['Surface']); src = link.from_socket
    lp = nt.nodes.new('ShaderNodeLightPath'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.remove(link); nt.links.new(lp.outputs['Is Shadow Ray'], mx.inputs['Fac']); nt.links.new(src, mx.inputs[1]); nt.links.new(tr.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface']); return m
LIQ_M = shadow_pass(liquid_mat('peroxide', (0.98, 0.96, 0.9)))
KI_M = shadow_pass(liquid_mat('helper'))
SOAP_M = shadow_pass(mat('soap', (0.25, 0.85, 0.3), 0.02, trans=0.9, ior=1.4))
shadow_pass(GLASS)
BENCH = noisy(mat('bench', (0.035, 0.037, 0.04), 0.32, coat=0.4), 6.0, 0.25, 0.08)
WALL = noisy(mat('wall', (0.06, 0.065, 0.075), 0.8), 3.0, 0.1, 0.05)
TRAY_M = noisy(mat('tray', (0.05, 0.052, 0.056), 0.4), 25.0, 0.12, 0.08)
BLACKP = mat('black_plastic', (0.02, 0.02, 0.022), 0.35)
WHITEP = noisy(mat('hdpe', (0.82, 0.82, 0.8), 0.45), 40.0, 0.04, 0.05)
PRINT = mat('print', (0.95, 0.95, 0.95), 0.4)
INK = mat('ink', (0.02, 0.02, 0.025), 0.5)
LABEL = mat('label', (0.9, 0.9, 0.88), 0.6)
AMBER = mat('amber', (0.55, 0.25, 0.05), 0.05, trans=1.0, ior=1.5)
NITRILE = mat('nitrile', (0.06, 0.25, 0.75), 0.42); _b = NITRILE.node_tree.nodes['Principled BSDF']; _b.inputs['Sheen Weight'].default_value = 0.3
VISOR = mat('visor', (0.85, 0.92, 0.98), 0.03, trans=1.0, ior=1.5); _b = VISOR.node_tree.nodes['Principled BSDF']; _b.inputs['Thin Wall'].default_value = True
RUBBER = mat('rubber', (0.05, 0.05, 0.055), 0.6)
DYES = [(0.85, 0.03, 0.05), (0.02, 0.22, 0.85), (0.98, 0.72, 0.02), (0.05, 0.62, 0.15)]
DYE_M = [shadow_pass(mat(f'dye{k}', c, 0.05, trans=0.85, ior=1.33)) for k, c in enumerate(DYES)]

def foam_mat():
    """foam: soap film full of tiny bubbles. Light goes in and scatters (subsurface), a wet sheen on top, bubble cells as bump.
    Colour comes from the mesh ('fcol', the dye stripes); 'fc' is a coordinate that travels with the foam so the bubbles flow."""
    m = bpy.data.materials.new('foam'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'fcol'; nt.links.new(at.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Subsurface Weight'].default_value = 1.0; b.inputs['Subsurface Radius'].default_value = (1.0, 0.85, 0.7); b.inputs['Subsurface Scale'].default_value = 0.004
    b.inputs['Roughness'].default_value = 0.4; b.inputs['Coat Weight'].default_value = 0.2; b.inputs['Coat Roughness'].default_value = 0.08
    fc = nt.nodes.new('ShaderNodeAttribute'); fc.attribute_name = 'fc'
    v1 = nt.nodes.new('ShaderNodeTexVoronoi'); v1.feature = 'DISTANCE_TO_EDGE'; v1.inputs['Scale'].default_value = 260.0; v1.inputs['Randomness'].default_value = 1.0
    v2 = nt.nodes.new('ShaderNodeTexVoronoi'); v2.feature = 'DISTANCE_TO_EDGE'; v2.inputs['Scale'].default_value = 900.0
    nt.links.new(fc.outputs['Vector'], v1.inputs['Vector']); nt.links.new(fc.outputs['Vector'], v2.inputs['Vector'])
    c1 = nt.nodes.new('ShaderNodeMapRange'); c1.inputs['From Max'].default_value = 0.18; nt.links.new(v1.outputs['Distance'], c1.inputs['Value'])
    c2 = nt.nodes.new('ShaderNodeMapRange'); c2.inputs['From Max'].default_value = 0.2; nt.links.new(v2.outputs['Distance'], c2.inputs['Value'])
    sq = nt.nodes.new('ShaderNodeMath'); sq.operation = 'SQRT'; nt.links.new(c1.outputs['Result'], sq.inputs[0])       # rounded domes, sharp seams
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.35
    nt.links.new(c2.outputs['Result'], ad.inputs[0]); nt.links.new(sq.outputs['Value'], ad.inputs[2])
    bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.8; bu.inputs['Distance'].default_value = 0.0012
    nt.links.new(ad.outputs['Value'], bu.inputs['Height']); nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
    # the seams between bubbles hold a little more liquid: a touch darker and glossier
    sr = nt.nodes.new('ShaderNodeMapRange'); sr.inputs['To Min'].default_value = 0.12; sr.inputs['To Max'].default_value = 0.38; nt.links.new(sq.outputs['Value'], sr.inputs['Value'])
    nt.links.new(sr.outputs['Result'], b.inputs['Roughness'])
    return m
FOAM_M = foam_mat()

# ---------------------------------------------------------------- geometry helpers
def obj(name, me, m=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o); o.location = loc
    if m: o.data.materials.append(m)
    return o
def lathe(name, prof, seg=128, m=None, closed=False):
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
def text(name, s, loc, size, m, rot=(math.pi / 2, 0, 0), align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = s; cu.size = size; cu.align_x = align; cu.align_y = 'CENTER'; cu.extrude = 0.00015
    o = obj(name, cu, m, loc); o.rotation_euler = rot; return o

# ================================================================ THE LAB (bench top at z = 0)
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 0)); bench = bpy.context.active_object; bench.data.materials.append(BENCH)
wall = lathe('wall', [(1.6, -0.02), (1.6, 1.6)], 96, WALL)
# a big plastic catch tray
TX, TY, TW, TD, TH = 0.06, 0.04, 0.64, 0.5, 0.026
TZ = 0.004                                      # the tray floor
tr_out = box('tray', TW, TD, TH, (TX, TY, TH / 2), TRAY_M, 0.006)
tr_in = box('trayhole', TW - 0.016, TD - 0.016, TH, (TX, TY, TH / 2 + TZ), TRAY_M, 0.004)
bo = tr_out.modifiers.new('hole', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = tr_in; bo.solver = 'EXACT'; tr_in.hide_render = True; tr_in.hide_viewport = True
# the 500 mL graduated cylinder (round glass foot)
CX, CY = 0.0, 0.04
RO, R_IN, HC = 0.0275, 0.0255, 0.341
CYL_PROF = [(0.0, 0.0), (0.046, 0.0), (0.0485, 0.002), (0.0485, 0.007), (0.044, 0.011), (RO + 0.002, 0.014), (RO, 0.02), (RO, HC - 0.006),
            (RO + 0.002, HC - 0.002), (RO + 0.002, HC), (R_IN + 0.0003, HC), (R_IN, HC - 0.003), (R_IN, 0.018), (0.0, 0.018)]
CYLO = lathe('cylinder', CYL_PROF, 160, GLASS, closed=True); CYLO.location = (CX, CY, TZ)
ZB = TZ + 0.018                                  # inside bottom
ZM = TZ + HC                                     # mouth
ZL = ZB + 0.0122                                 # 25 mL of liquid
# a pour spout: a small lip bent out on the +x side
# graduations on the front (every 10 mL, longer every 50, numbers every 100)
ML = 0.000508 / 1.0                              # metres of height per mL
for k in range(5, 51):
    zz = ZB + k * 10 * ML * 0.5 + 0.0                 # (500 mL over 25.4 cm)
    zz = ZB + k * 10 * 0.000508
    if zz > ZM - 0.01: break
    L = 0.014 if k % 5 == 0 else 0.007; ang = math.radians(-90 - 22)
    mk = box('mark', L, 0.0005, 0.0008, (0, 0, 0), PRINT)
    mk.location = (CX + math.cos(ang) * (RO + 0.0002), CY + math.sin(ang) * (RO + 0.0002), zz); mk.rotation_euler = (0, 0, ang + math.pi / 2)
    if k % 10 == 0:
        ang2 = ang + math.radians(17)
        tx = text('num', str(k * 10), (CX + math.cos(ang2) * (RO + 0.0004), CY + math.sin(ang2) * (RO + 0.0004), zz + 0.0045), 0.0055, PRINT, (math.pi / 2, 0, ang2 + math.pi / 2))
text('mltxt', 'mL', (CX + math.cos(math.radians(-100)) * (RO + 0.0004), CY + math.sin(math.radians(-100)) * (RO + 0.0004), ZM - 0.03), 0.006, PRINT, (math.pi / 2, 0, math.radians(-100) + math.pi / 2))
# the liquid: flat bottom, a little meniscus up the wall
RL = R_IN - 0.0005
LIQO = lathe('liquid', [(0.0, ZB + 0.0006), (RL, ZB + 0.0006), (RL, ZL + 0.0012), (RL - 0.002, ZL + 0.0002), (0.0, ZL)], 96, LIQ_M, closed=True); LIQO.location = (CX, CY, 0)
# food colour streaks running down the inside of the glass (they become the stripes in the foam)
DYE_ANG = [math.radians(a_) for a_ in (-138, -104, -70, -36)]
STREAKS = []
for k, ang in enumerate(DYE_ANG):
    me = bpy.data.meshes.new(f'streak{k}'); o = obj(f'streak{k}', me, DYE_M[k]); STREAKS.append((o, ang))
def build_streak(o, ang, z_top, z_bot, w=0.0035, seed=0):
    """a thin dye ribbon on the inside wall, narrow at the top, a fatter drip-bead at its bottom end"""
    me = o.data; me.clear_geometry(); vs, fs = [], []; NZ, NA = 24, 6
    if z_top - z_bot < 0.002: o.hide_render = True; return
    r = R_IN - 0.00035
    for j in range(NZ + 1):
        z = lerp(z_top, z_bot, j / NZ); wj = w * (0.35 + 0.65 * (j / NZ) ** 0.6) * (1 + 0.25 * math.sin(z * 900 + seed))
        if j == NZ: wj *= 1.4
        for i in range(NA + 1):
            aa = ang + (i / NA - 0.5) * wj / r; vs.append((CX + r * math.cos(aa), CY + r * math.sin(aa), z))
    for j in range(NZ):
        for i in range(NA): fs.append((j * (NA + 1) + i, j * (NA + 1) + i + 1, (j + 1) * (NA + 1) + i + 1, (j + 1) * (NA + 1) + i))
    me.from_pydata(vs, [], fs); me.update(); [setattr(p, 'use_smooth', True) for p in me.polygons]; o.hide_render = False

# props: peroxide bottle (white HDPE, plain label), dish soap, a small dropper bottle, the helper beaker
def bottle(name, x, y, prof, m, cap_r, cap_h, cap_m=BLACKP):
    o = lathe(name, prof, 64, m); o.location = (x, y, 0); top = prof[-1][1]
    cyl(name + 'cap', cap_r, cap_h, (x, y, top + cap_h / 2), cap_m); return o
PER = bottle('peroxide', -0.2, 0.2, [(0, 0), (0.042, 0), (0.044, 0.004), (0.044, 0.16), (0.03, 0.19), (0.015, 0.2), (0.015, 0.215), (0, 0.215)], WHITEP, 0.018, 0.024)
lb = lathe('perlabel', [(0.0445, 0.04), (0.0445, 0.13)], 64, LABEL); lb.location = (-0.2, 0.2, 0)
text('pertxt', 'H2O2 30%', (-0.2 + 0.0453 * math.cos(math.radians(-70)), 0.2 + 0.0453 * math.sin(math.radians(-70)), 0.1), 0.014, INK, (math.pi / 2, 0, math.radians(-70) + math.pi / 2))
text('pertxt2', 'HYDROGEN PEROXIDE', (-0.2 + 0.0453 * math.cos(math.radians(-70)), 0.2 + 0.0453 * math.sin(math.radians(-70)), 0.075), 0.006, INK, (math.pi / 2, 0, math.radians(-70) + math.pi / 2))
SOAPB = bottle('soapb', -0.29, 0.3, [(0, 0), (0.03, 0), (0.033, 0.005), (0.035, 0.12), (0.028, 0.17), (0.012, 0.19), (0, 0.19)], mat('soapbottle', (0.3, 0.85, 0.35), 0.1, trans=0.8, ior=1.45), 0.013, 0.02, WHITEP)
bottle('dropper', 0.33, 0.33, [(0, 0), (0.022, 0), (0.023, 0.003), (0.023, 0.07), (0.012, 0.085), (0.008, 0.09), (0, 0.09)], AMBER, 0.009, 0.03, BLACKP)
wb = lathe('washbottle', [(0, 0), (0.04, 0), (0.042, 0.005), (0.042, 0.15), (0.02, 0.18), (0, 0.18)], 64, mat('wash', (0.9, 0.92, 0.95), 0.3, trans=0.6, ior=1.45)); wb.location = (0.42, 0.25, 0)
# the 50 mL beaker of helper (potassium iodide solution); pivots on its lip at the cylinder mouth
KB_R, KB_H = 0.021, 0.05
KBEAK = lathe('kbeaker', [(0.0, 0.0), (KB_R - 0.002, 0.0), (KB_R, 0.002), (KB_R, KB_H - 0.001), (KB_R + 0.0018, KB_H), (KB_R - 0.0008, KB_H + 0.001),
                          (KB_R - 0.0012, KB_H), (KB_R - 0.0012, 0.003), (0.0, 0.003)], 96, GLASS, closed=True)
KLIQ = lathe('kliq', [(0.0, 0.0035), (KB_R - 0.0016, 0.0035), (KB_R - 0.0016, 0.016), (0.0, 0.016)], 64, KI_M, closed=True)
KPIV = bpy.data.objects.new('kpivot', None); S.collection.objects.link(KPIV)
for o in (KBEAK, KLIQ): o.parent = KPIV; o.location = (-(KB_R + 0.0018), 0, -KB_H)     # pivot = the lip on its +x side
KHOME = Vector((0.12, -0.06, TZ))
for k, c in enumerate(DYES):                     # four little food colour bottles
    x = 0.17 + 0.045 * k; y = 0.24 + 0.012 * (k % 2)
    bottle(f'dyeb{k}', x, y, [(0, 0), (0.016, 0), (0.017, 0.003), (0.017, 0.055), (0.009, 0.068), (0.004, 0.08), (0, 0.08)], WHITEP, 0.0065, 0.016, mat(f'dcap{k}', c, 0.35))
# goggles and gloves, front left on the bench (for the safety beat)
def goggles(loc, rz):
    g = bpy.data.objects.new('goggles', None); S.collection.objects.link(g)
    me = bpy.data.meshes.new('visor'); vs, fs = [], []; NA, NZ = 40, 6; R = 0.082
    for j in range(NZ + 1):
        for i in range(NA + 1):
            aa = math.radians(-70 + 140 * i / NA); z = (j / NZ - 0.5) * 0.05 * (1 - 0.25 * abs(math.sin(aa)))
            vs.append((R * math.sin(aa), -R * math.cos(aa) + R, z))
    for j in range(NZ):
        for i in range(NA): fs.append((j * (NA + 1) + i, j * (NA + 1) + i + 1, (j + 1) * (NA + 1) + i + 1, (j + 1) * (NA + 1) + i))
    me.from_pydata(vs, [], fs); me.update(); [setattr(p, 'use_smooth', True) for p in me.polygons]
    v = obj('visor', me, VISOR); v.parent = g; md = v.modifiers.new('th', 'SOLIDIFY'); md.thickness = 0.0018
    # soft rubber frame around the visor and the strap
    for zz in (-0.025, 0.025):
        cd = bpy.data.curves.new('gframe', 'CURVE'); cd.dimensions = '3D'; cd.bevel_depth = 0.0035; cd.bevel_resolution = 4; sp = cd.splines.new('POLY'); sp.points.add(NA)
        for i in range(NA + 1):
            aa = math.radians(-72 + 144 * i / NA); sp.points[i].co = (R * 1.02 * math.sin(aa), -R * 1.02 * math.cos(aa) + R, zz * (1 - 0.25 * abs(math.sin(aa))), 1)
        f_ = obj('gframe', cd, RUBBER); f_.parent = g
    cd = bpy.data.curves.new('strap', 'CURVE'); cd.dimensions = '3D'; cd.extrude = 0.009; sp = cd.splines.new('POLY'); sp.points.add(30)
    for i in range(31):
        aa = math.radians(72 + 216 * i / 30); sp.points[i].co = (0.085 * math.sin(aa), -0.07 * math.cos(aa) + R + 0.01, -0.022, 1)
    st = obj('strap', cd, RUBBER); st.parent = g
    g.location = loc; g.rotation_euler = (0, 0, rz); return g
GOG = goggles(Vector((-0.16, -0.3, 0.027)), math.radians(18))
def glove(loc, rz, flip=1):
    """a nitrile glove lying flat: a skin-modifier skeleton (cuff, palm, five fingers) smoothed by subdivision, squashed flat"""
    V = [(-0.125, 0, 0), (-0.06, 0, 0), (0.0, 0, 0), (0.035, 0, 0)]; R = [0.033, 0.03, 0.04, 0.036]; E = [(0, 1), (1, 2), (2, 3)]
    for (bx, by), (tx, ty), r in [((0.045, 0.026), (0.112, 0.033), 0.0095), ((0.048, 0.009), (0.124, 0.011), 0.0098),
                                  ((0.046, -0.009), (0.117, -0.013), 0.0095), ((0.04, -0.025), (0.094, -0.034), 0.0082)]:
        b0 = len(V); V += [(bx, by * flip, 0), ((bx + tx) / 2, (by + ty) / 2 * flip, 0), (tx, ty * flip, 0)]; R += [r * 1.15, r, r * 0.92]; E += [(3, b0), (b0, b0 + 1), (b0 + 1, b0 + 2)]
    b0 = len(V); V += [(-0.005, 0.034 * flip, 0), (0.03, 0.062 * flip, 0), (0.055, 0.074 * flip, 0)]; R += [0.016, 0.0115, 0.0105]; E += [(2, b0), (b0, b0 + 1), (b0 + 1, b0 + 2)]
    me = bpy.data.meshes.new('glove'); me.from_pydata(V, E, []); o = obj('glove', me, NITRILE, loc)
    sk = o.modifiers.new('skin', 'SKIN')
    for k, r in enumerate(R): me.skin_vertices[0].data[k].radius = (r, r)
    me.skin_vertices[0].data[0].use_root = True
    sd = o.modifiers.new('sub', 'SUBSURF'); sd.levels = 2; sd.render_levels = 3
    o.scale = (1, 1, 0.42); o.location.z = 0.013; o.rotation_euler = (0, 0, rz)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_smooth()
    return o
GL1 = glove(Vector((-0.02, -0.29, 0.0)), math.radians(160)); GL2 = glove(Vector((0.05, -0.33, 0.0)), math.radians(135), -1)
SAFETY = [GOG] + list(GOG.children) + [GL1, GL2]

# the pour streams (soap, helper) as tubes along curves
def stream_obj(name, m, r):
    cd = bpy.data.curves.new(name, 'CURVE'); cd.dimensions = '3D'; cd.bevel_depth = r; cd.bevel_resolution = 6; cd.use_fill_caps = True
    sp = cd.splines.new('BEZIER'); sp.bezier_points.add(2); return obj(name, cd, m)
SOAPS = stream_obj('soapstream', SOAP_M, 0.0028); KST = stream_obj('kstream', KI_M, 0.0024)
def stream_set(o, pts, r, wob=0.0):
    o.hide_render = False; o.data.bevel_depth = r; bp = o.data.splines[0].bezier_points
    for i, p in enumerate(pts):
        p = Vector(p); bp[i].co = p
        q = Vector(pts[i + 1]) if i + 1 < len(pts) else p + (p - Vector(pts[i - 1])); d = (q - p) * 0.3
        bp[i].handle_right = p + d + Vector((0.0008 * math.sin(wob + i), 0, 0)); bp[i].handle_left = p - d

# ---------------------------------------------------------------- the foam snake: a tube along a path, rebuilt every frame
FOAM = obj('foam', bpy.data.meshes.new('foam'), FOAM_M)
def catmull(pts, n_per=24):
    out = []; P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n_per):
            t = k / n_per; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1]); return out
R_FOAM_OUT = 0.043
FLOOR_C = TZ + R_FOAM_OUT * 0.72                 # centre height of a flattened rope lying on the tray
def foam_path(t):
    """the foam's centre line: straight up the cylinder, out of the mouth, an arc over to the +x side (it sways), then along the tray
    around the cylinder, then a second layer on top. Returns a dense list of points and the arc length where it lands."""
    sw = Vector((0.006 * math.sin(2 * math.pi * 0.9 * t), 0.005 * math.sin(2 * math.pi * 0.7 * t + 1.0), 0.004 * math.sin(2 * math.pi * 1.1 * t)))
    c = Vector((CX, CY, 0))
    arc = [Vector((CX, CY, ZM)), Vector((CX, CY, ZM + 0.035)), c + Vector((0.016, -0.008, ZM + 0.085)) + sw, c + Vector((0.062, -0.02, ZM + 0.108)) + sw * 1.4,
           c + Vector((0.112, -0.04, ZM + 0.065)) + sw, c + Vector((0.15, -0.058, TZ + 0.17)) + sw * 0.6, c + Vector((0.175, -0.075, FLOOR_C + 0.02)), c + Vector((0.18, -0.1, FLOOR_C))]
    f1, f2 = FLOOR_C, FLOOR_C + R_FOAM_OUT * 1.25
    tray = [c + Vector((0.17, -0.135, f1)), c + Vector((0.12, -0.16, f1)), c + Vector((0.04, -0.165, f1)), c + Vector((-0.05, -0.155, f1)), c + Vector((-0.12, -0.115, f1)),
            c + Vector((-0.16, -0.05, f1)), c + Vector((-0.165, 0.03, f1)), c + Vector((-0.13, 0.1, f1)), c + Vector((-0.06, 0.145, f1)),
            c + Vector((0.03, 0.155, f1)), c + Vector((0.11, 0.135, f1)), c + Vector((0.16, 0.075, f1)), c + Vector((0.175, -0.01, f1 + 0.006)),
            c + Vector((0.14, -0.08, f2)), c + Vector((0.08, -0.115, f2)), c + Vector((0.0, -0.12, f2)), c + Vector((-0.07, -0.1, f2)), c + Vector((-0.11, -0.04, f2)), c + Vector((-0.115, 0.03, f2))]
    straight = [Vector((CX, CY, ZL + 0.002 + (ZM - ZL - 0.002) * k / 40)) for k in range(40)]
    a_ = catmull(arc, 20); land_i = len(straight) + len(a_) - 1
    pts = straight + a_ + catmull([arc[-1]] + tray, 20)[1:]
    for p in pts[len(straight):]: p.z = max(p.z, FLOOR_C if p.z < ZM else p.z)
    s = [0.0]
    for i in range(1, len(pts)): s.append(s[-1] + (pts[i] - pts[i - 1]).length)
    return pts, s, s[land_i], s[len(straight) - 1]
def resample(pts, s, ds):
    out, j = [], 0; L = s[-1]; n = int(L / ds) + 1
    for k in range(n + 1):
        q = min(L, k * ds)
        while j < len(s) - 2 and s[j + 1] < q: j += 1
        f_ = (q - s[j]) / max(1e-9, s[j + 1] - s[j]); out.append(pts[j].lerp(pts[j + 1], f_))
    return out
def stripe_col(th, m):
    """the dye stripes: four coloured bands where the drips ran down the wall, warm off-white between (a little iodine yellow)"""
    base = Vector((0.93, 0.87, 0.7)); col = base.copy(); wob = 0.12 * mnoise.noise(Vector((math.cos(th) * 2, math.sin(th) * 2, m * 14)))
    tw = 0.45 * mnoise.noise(Vector((0.7, 0.2, m * 3.0)))                       # the stripes wander around the rope
    for k, ang in enumerate(DYE_ANG):
        d = abs((th - ang - tw + math.pi) % (2 * math.pi) - math.pi)
        w = 0.24 + 0.16 * mnoise.noise(Vector((k * 3.1, m * 7, 0.5)))
        f_ = 1 - smooth(w - 0.1, w + 0.05, d + wob)
        streak = 0.75 + 0.25 * mnoise.noise(Vector((th * 3, k, m * 30)))         # darker and lighter streaks inside each band
        col = col.lerp(Vector(DYES[k]) * streak + Vector((0.03, 0.03, 0.03)), f_ * 0.95)
    return col
def build_foam(t, L, s0=None, NA=48, ds=0.0022):
    """the tube from the liquid up to arc length L (the head). Material coordinate m = s - L travels with the foam."""
    me = FOAM.data; me.clear_geometry()
    if L < 0.004: FOAM.hide_render = True; return
    FOAM.hide_render = False
    pts, s, s_land, s_mouth = foam_path(t)
    L = min(L, s[-1] - 0.01); P = resample(pts, s, ds); n = min(len(P) - 1, int(L / ds) + 1)
    P = P[:n + 1]; P[-1] = P[-1]
    # rotation-minimising frames along the path
    T = [(P[min(i + 1, n)] - P[max(i - 1, 0)]).normalized() for i in range(n + 1)]
    N_ = [Vector((1, 0, 0))]
    for i in range(1, n + 1):
        v = N_[-1] - T[i] * N_[-1].dot(T[i]); N_.append(v.normalized() if v.length > 1e-6 else N_[-1])
    vs, cols, fcs = [], [], []
    for i in range(n + 1):
        si = i * ds; m = si - L; c = P[i]; t_ = T[i]; nn = N_[i]; bb = t_.cross(nn)
        inside = si < s_mouth
        out_k = smooth(s_mouth, s_mouth + 0.035, si); tray_k = smooth(s_land - 0.03, s_land + 0.04, si)
        R0 = lerp(R_IN - 0.0007, R_FOAM_OUT, out_k) * lerp(1.0, 1.06, tray_k)
        cap = L - si                                           # the round head
        if cap < R0: R0 = R0 * math.sqrt(max(0.0, 1 - ((R0 - cap) / R0) ** 2)) + 0.0004
        if si < 0.006: R0 *= math.sqrt(max(0.05, si / 0.006))  # closed at the bottom, under the liquid
        lump = 0.2 * out_k
        R0 *= 1 + 0.22 * out_k * mnoise.noise(Vector((0.3, 1.7, m * 9.0)))         # bulges along its length
        sz, sh = lerp(1.0, 0.72, tray_k), lerp(1.0, 1.25, tray_k)
        for j in range(NA):
            th = 2 * math.pi * j / NA - math.pi; d0 = nn * math.cos(th) + bb * math.sin(th)
            q = Vector((math.cos(th) * 1.1, math.sin(th) * 1.1, m * 11))
            r = R0 * (1 + lump * (mnoise.noise(q) + 0.5 * mnoise.noise(q * 2.7 + Vector((5, 1, 2))) + 0.25 * mnoise.noise(q * 7 + Vector((1, 7, 3))) + 0.1 * mnoise.noise(q * 19)))
            d = d0 * r
            if tray_k > 0:                                     # sag: flatter and wider lying on the tray
                dz = d.z; dh = Vector((d.x, d.y, 0)); d = dh * sh + Vector((0, 0, dz * sz))
            p = c + d
            if tray_k > 0.5: p.z = max(p.z, TZ + 0.0004)
            vs.append(p); cols.append(stripe_col(th, m)); fcs.append((math.cos(th) * R0, math.sin(th) * R0, m))
    fs = []
    for i in range(n):
        for j in range(NA):
            j2 = (j + 1) % NA; fs.append((i * NA + j, i * NA + j2, (i + 1) * NA + j2, (i + 1) * NA + j))
    bot = len(vs); vs.append(P[0] - T[0] * 0.0005); cols.append(stripe_col(0, -L)); fcs.append((0, 0, -L))
    tip = len(vs); vs.append(P[n] + T[n] * 0.0003); cols.append(stripe_col(0, 0)); fcs.append((0, 0, 0))
    for j in range(NA):
        j2 = (j + 1) % NA; fs.append((bot, j2, j)); fs.append((tip, n * NA + j, n * NA + j2))
    me.from_pydata([tuple(v) for v in vs], [], fs); me.update()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    for nm_ in ('fcol', 'fc'):
        if nm_ in me.attributes: me.attributes.remove(me.attributes[nm_])
    ca = me.color_attributes.new('fcol', 'FLOAT_COLOR', 'POINT'); flat = []
    for c_ in cols: flat += [c_.x, c_.y, c_.z, 1.0]
    ca.data.foreach_set('color', flat)
    fa = me.attributes.new('fc', 'FLOAT_VECTOR', 'POINT'); fa.data.foreach_set('vector', [x for v in fcs for x in v])

# ---------------------------------------------------------------- steam: a volume over the pile, rising wisps
bpy.ops.mesh.primitive_cube_add(size=1, location=(CX + 0.03, CY - 0.01, TZ + 0.2)); STEAM = bpy.context.active_object; STEAM.name = 'steam'; STEAM.scale = (0.36, 0.3, 0.3)
sm_ = bpy.data.materials.new('steam'); sm_.use_nodes = True; nt = sm_.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (0.95, 0.96, 1.0, 1); pv.inputs['Anisotropy'].default_value = 0.45
tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
STEAM_MAP = mp
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 3.2; nz.inputs['Detail'].default_value = 5; nz.inputs['Roughness'].default_value = 0.55
nz.inputs['Distortion'].default_value = 0.6; nt.links.new(mp.outputs['Vector'], nz.inputs['Vector']); STEAM_W = nz.inputs['W']
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.72; nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
fall = nt.nodes.new('ShaderNodeMapRange'); fall.inputs['From Min'].default_value = -0.5; fall.inputs['From Max'].default_value = 0.5; fall.inputs['To Min'].default_value = 1.0; fall.inputs['To Max'].default_value = 0.0
nt.links.new(sep.outputs['Z'], fall.inputs['Value'])
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(mr.outputs['Result'], mul.inputs[0]); nt.links.new(fall.outputs['Result'], mul.inputs[1])
den = nt.nodes.new('ShaderNodeMath'); den.operation = 'MULTIPLY'; den.inputs[1].default_value = 0.0; nt.links.new(mul.outputs['Value'], den.inputs[0]); STEAM_DEN = den.inputs[1]
nt.links.new(den.outputs['Value'], pv.inputs['Density']); nt.links.new(pv.outputs['Volume'], nt.nodes['Material Output'].inputs['Volume'])
STEAM.data.materials.append(sm_); STEAM.visible_shadow = False

# ---------------------------------------------------------------- lights (as the clock: big soft key, two strips behind for glass edges, cards for reflections)
def area(name, loc, rot, size, sizey, power, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA'); ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = sizey; ld.energy = power; ld.color = color
    o = bpy.data.objects.new(name, ld); S.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    o.visible_transmission = False; o.visible_glossy = False; o.visible_camera = False; return o
def card(name, loc, rot, sx, sy, strength, soft=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); e_ = nt.nodes.new('ShaderNodeEmission')
    e_.inputs['Strength'].default_value = strength; nt.links.new(e_.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); o.data.materials.append(m)
    if soft:                                   # a soft round glow instead of a hard-edged rectangle
        tc = nt.nodes.new('ShaderNodeTexCoord'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'QUADRATIC_SPHERE'
        mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-1, -1, 0); mp.inputs['Scale'].default_value = (2, 2, 1)
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector']); nt.links.new(gr.outputs['Fac'], e_.inputs['Color'])
    o.visible_camera = False; o.visible_diffuse = False; o.visible_shadow = False; o.visible_volume_scatter = False; return o
area('key', (-0.55, -0.4, 1.0), (math.radians(38), 0, math.radians(-40)), 1.0, 0.7, 60)
area('stripL', (-0.4, 0.5, 0.4), (math.radians(-70), 0, math.radians(30)), 0.14, 1.0, 40)
area('stripR', (0.45, 0.5, 0.4), (math.radians(-70), 0, math.radians(-35)), 0.14, 1.0, 40)
area('fill', (0.7, -0.6, 0.4), (math.radians(65), 0, math.radians(50)), 0.9, 0.9, 7, (1.0, 0.96, 0.9))
area('back', (0.1, 0.65, 0.25), (math.radians(-85), 0, 0), 0.6, 0.3, 25, (0.95, 0.97, 1.0))        # behind: makes the steam glow
card('cardKey', (-0.55, -0.4, 1.0), (math.radians(38), 0, math.radians(-40)), 1.0, 0.7, 6.0)
card('cardL', (-0.47, 0.55, 0.42), (math.radians(-70), 0, math.radians(30)), 0.4, 1.0, 4.0)
card('cardR', (0.52, 0.55, 0.42), (math.radians(-70), 0, math.radians(-35)), 0.4, 1.0, 4.0)
card('cardFront', (0.0, -1.0, 0.4), (math.radians(80), 0, 0), 1.4, 0.6, 0.6)
W_ = bpy.data.worlds.new('world'); S.world = W_; W_.use_nodes = True; W_.node_tree.nodes['Background'].inputs['Color'].default_value = (0.012, 0.013, 0.016, 1)

# ================================================================ THE MOLECULE SET (far away at x = 60)
MX = Vector((60, 0, 1.5))
def mmat(name, col, rough=0.28, emit=0.0):
    m = mat(name, col, rough, coat=0.7)
    if emit: b = m.node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    return m
M_O = mmat('oxy', (0.85, 0.08, 0.06)); M_H = mmat('hyd', (0.92, 0.92, 0.92)); M_IG = mmat('iodide', (0.45, 0.2, 0.75), 0.25, 0.9)
BOND = mmat('bond', (0.75, 0.75, 0.78), 0.35)
def bg_sphere(center, c0, c1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=40, location=center, segments=48, ring_count=24); o = bpy.context.active_object
    m = bpy.data.materials.new('bg'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); em = nt.nodes.new('ShaderNodeEmission')
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'; tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.03, 0.03, 0.03)
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (*c0, 1); ramp.color_ramp.elements[1].color = (*c1, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], gr.inputs['Vector']); nt.links.new(gr.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    em.inputs['Strength'].default_value = 1.0; nt.links.new(em.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); o.data.materials.append(m)
    o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons)); return o
BG = bg_sphere(MX, (0.004, 0.008, 0.02), (0.02, 0.05, 0.12))
SPECK = mmat('speck', (0.5, 0.7, 1.0), 0.5, 0.8)
SPECKS = [sphere('speck', 0.03 + 0.03 * h1(i), MX + Vector(((h1(i * 3) - 0.5) * 18, (h1(i * 5) - 0.5) * 18 + 4, (h1(i * 7) - 0.5) * 14)), SPECK, 12) for i in range(70)]
MLIGHTS = [area('mkey', tuple(MX + Vector((-6, -6, 8))), (math.radians(45), 0, math.radians(-45)), 6, 6, 9000, (0.9, 0.95, 1.0)),
           area('mrim', tuple(MX + Vector((6, 8, 3))), (math.radians(-100), 0, math.radians(-150)), 4, 4, 5000, (0.6, 0.75, 1.0))]
# atom and bond pools: each frame places what it needs
O_POOL = [sphere('O', 0.33, MX, M_O, 32) for _ in range(64)]
H_POOL = [sphere('H', 0.2, MX, M_H, 20) for _ in range(64)]
I_POOL = [sphere('I', 0.62, MX, M_IG, 40) for _ in range(4)]
B_POOL = [cyl('bond', 1.0, 1.0, MX, BOND, seg=16) for _ in range(140)]
class Atoms:
    def __init__(self): self.o = 0; self.h = 0; self.i = 0; self.b = 0
    def put(self, kind, p):
        if kind == 'O': ob = O_POOL[self.o]; self.o += 1
        elif kind == 'H': ob = H_POOL[self.h]; self.h += 1
        else: ob = I_POOL[self.i]; self.i += 1
        ob.hide_render = False; ob.location = p; return p
    def bond(self, p, q, r=0.075, off=Vector()):
        if (q - p).length < 1e-4: return
        ob = B_POOL[self.b]; self.b += 1; d = q - p; ob.hide_render = False
        ob.location = (p + q) / 2 + off; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = d.to_track_quat('Z', 'Y'); ob.scale = (r, r, d.length)
def pool_hide():
    for ob in O_POOL + H_POOL + I_POOL + B_POOL: ob.hide_render = True
# molecule shapes (local offsets)
def rot(v, e): return Euler(e).to_matrix() @ v
def peroxide(A, c, e, sc=1.0):
    """H-O-O-H, twisted; returns the four atom positions"""
    o1 = c + rot(Vector((-0.62, 0, 0)), e) * sc; o2 = c + rot(Vector((0.62, 0, 0)), e) * sc
    h1_ = o1 + rot(Vector((-0.32, 0.55, 0.42)), e) * sc; h2 = o2 + rot(Vector((0.32, 0.55, -0.42)), e) * sc
    return [o1, o2, h1_, h2]
def draw_peroxide(A, P, k=1.0):
    o1, o2, h1_, h2 = P; A.put('O', o1); A.put('O', o2); A.put('H', h1_); A.put('H', h2)
    if k > 0.02: A.bond(o1, o1.lerp(o2, k * 0.5)); A.bond(o2, o2.lerp(o1, k * 0.5))
    A.bond(o1, h1_, 0.06); A.bond(o2, h2, 0.06)
def water_from(o, e):
    return [o, o + rot(Vector((-0.58, 0.45, 0.25)), e), o + rot(Vector((0.58, 0.45, 0.25)), e)]
def draw_water(A, W):
    o, ha, hb = W; A.put('O', o); A.put('H', ha); A.put('H', hb); A.bond(o, ha, 0.06); A.bond(o, hb, 0.06)
def draw_o2(A, p, q):
    A.put('O', p); A.put('O', q); n = (q - p).cross(Vector((0, 1, 0.3))).normalized() * 0.09
    A.bond(p, q, 0.055, n); A.bond(p, q, 0.055, -n)

# ================================================================ THE BUBBLE SET (x = 120): soap bubbles with thin-film colour
BX = Vector((120, 0, 1.5))
def bubble_mat():
    """a soap film: almost all see-through, a mirror that gets stronger toward the edges, and the mirror tinted by swirling
    thin-film rainbow colours (the film's thickness drifts, so the colours slide around)"""
    m = bpy.data.materials.new('bubble'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'
    nz.inputs['Scale'].default_value = 1.4; nz.inputs['Detail'].default_value = 3; nz.inputs['Distortion'].default_value = 1.6; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    th = nt.nodes.new('ShaderNodeMath'); th.operation = 'MULTIPLY_ADD'; th.inputs[1].default_value = 1.7
    nt.links.new(nz.outputs['Fac'], th.inputs[0]); nt.links.new(lw.outputs['Facing'], th.inputs[2])
    fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'; nt.links.new(th.outputs['Value'], fr.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'B_SPLINE'
    stops = [(0.0, (0.9, 0.25, 0.9)), (0.18, (1.0, 0.8, 0.25)), (0.36, (0.3, 1.0, 0.45)), (0.54, (0.2, 0.75, 1.0)), (0.72, (0.45, 0.3, 1.0)), (1.0, (0.9, 0.25, 0.9))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1); cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, c in stops[1:-1]: e = cr.elements.new(pos); e.color = (*c, 1)
    nt.links.new(fr.outputs['Value'], ramp.inputs['Fac'])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.0; nt.links.new(ramp.outputs['Color'], gl.inputs['Color'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (0.97, 0.97, 0.97, 1)
    w = nt.nodes.new('ShaderNodeMapRange'); w.inputs['To Min'].default_value = 0.1; w.inputs['To Max'].default_value = 0.85; nt.links.new(lw.outputs['Fresnel'], w.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(w.outputs['Result'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(gl.outputs['BSDF'], mx.inputs[2])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    es = nt.nodes.new('ShaderNodeMath'); es.operation = 'MULTIPLY'; es.inputs[1].default_value = 0.22; nt.links.new(lw.outputs['Fresnel'], es.inputs[0]); nt.links.new(es.outputs['Value'], em.inputs['Strength'])
    ad = nt.nodes.new('ShaderNodeAddShader'); nt.links.new(mx.outputs['Shader'], ad.inputs[0]); nt.links.new(em.outputs['Emission'], ad.inputs[1])
    nt.links.new(ad.outputs['Shader'], out.inputs['Surface']); return m, nz.inputs['W']
BUB, BUB_W = bubble_mat()
BGB = bg_sphere(BX, (0.003, 0.004, 0.012), (0.015, 0.025, 0.06))
# soft boxes the bubbles mirror (only seen in reflections)
BCARDS = [card('bc1', tuple(BX + Vector((-6, -5, 7))), (math.radians(50), 0, math.radians(-50)), 12, 9, 16.0, True),
          card('bc2', tuple(BX + Vector((8, 2, 2))), (math.radians(-90), 0, math.radians(-100)), 7, 14, 10.0, True),
          card('bc3', tuple(BX + Vector((0, -9, -6))), (math.radians(130), 0, 0), 16, 7, 5.0, True),
          card('bc4', tuple(BX + Vector((0, -22, 3))), (math.radians(90), 0, 0), 22, 16, 8.0, True),
          card('bc5', tuple(BX + Vector((-9, 1, -1))), (math.radians(90), 0, math.radians(80)), 7, 14, 7.0, True)]
for c_ in BCARDS: c_.visible_transmission = True
BLIGHTS = [area('bkey', tuple(BX + Vector((-5, -5, 6))), (math.radians(45), 0, math.radians(-45)), 5, 5, 5000)]
BUBS = []
for i in range(46):                         # a loose wet foam: round bubbles of mixed sizes packed together
    r = 0.35 + 0.85 * h1(i * 11) ** 1.6
    p = BX + Vector(((h1(i * 3) - 0.5) * 5.0, (h1(i * 5)) * 3.0, (h1(i * 7) - 0.5) * 8.0))
    BUBS.append([sphere('bub', 1.0, p, BUB, 48), p, r])
for _ in range(60):                         # push overlapping ones apart a little (they may still touch, like real foam)
    for i in range(len(BUBS)):
        for j in range(i + 1, len(BUBS)):
            d = BUBS[j][1] - BUBS[i][1]; need = (BUBS[i][2] + BUBS[j][2]) * 0.92
            if d.length < need: push = d.normalized() * (need - d.length) * 0.5; BUBS[i][1] -= push; BUBS[j][1] += push
for bo_, p, r in BUBS: bo_.location = p; bo_.scale = (r, r, r)
O2_FLY = [(sphere('Ob', 0.12, BX, M_O, 16), sphere('Ob', 0.12, BX, M_O, 16)) for _ in range(16)]

CAM = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(CAM); S.camera = CAM
CAM.data.sensor_width = 36; CAM.data.dof.use_dof = True; CAM.data.clip_start = 0.005
def look(cp, ct, lens=85, fstop=4.0, focus=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'; CAM.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop; CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus else d.length

# ================================================================ the story, frame by frame
LAB = [o for o in S.objects if o.location.x < 30 and o.name not in ('cam',) and not (o.parent and o.parent.location.x >= 30)]
MOL = [BG] + SPECKS + MLIGHTS
BUBSET = [BGB] + [b_[0] for b_ in BUBS] + BCARDS + BLIGHTS
def visible(objs, on):
    for o in objs: o.hide_render = not on
def foam_len(t):
    """how far the foam has come (arc length of its head), story time: starts at the end of beat 4, bursts out in beat 8, piles in 9-11"""
    pts, s, s_land, s_mouth = foam_path(t)
    if t < B[4] + 0.72 * DUR[4]: return 0.0
    if t < B[5]: return 0.004 + 0.04 * smooth(B[4] + 0.72 * DUR[4], B[5], t)
    if t < B[8]: return 0.044
    if t < B[9]:
        u = (t - B[8]) / DUR[8]; return lerp(0.044, s_land + 0.12, u ** 1.15)
    return s_land + 0.12 + 0.17 * (t - B[9])
def lab_state(t, foam=0.0, streaks=1.0, ki_tilt=0.0, ki_on=False, soap=None, steam=0.0, liquid=True, ki_liq=True):
    LIQO.hide_render = not liquid
    for k, (o, ang) in enumerate(STREAKS):
        top = ZM - 0.004; bot = lerp(top, ZL + 0.001, clamp(streaks * (1.0 + 0.25 * k) - 0.25 * k, 0, 1))
        build_streak(o, ang, top, bot, seed=k * 3.0)
        if foam > 0.0: o.hide_render = True if foam > 0.25 else o.hide_render
    build_foam(t, foam)
    KPIV.hide_render = not ki_on; [setattr(o, 'hide_render', not ki_on) for o in (KBEAK, KLIQ)]
    KLIQ.hide_render = not (ki_on and ki_liq)
    if ki_on:
        KPIV.location = Vector((CX - 0.004, CY, ZM + 0.012)); KPIV.rotation_euler = (0, math.radians(ki_tilt), 0)
    STEAM.hide_render = steam <= 0.0; STEAM_DEN.default_value = 5.0 * steam; STEAM_W.default_value = t * 0.35
    STEAM_MAP.inputs['Location'].default_value = (0, 0, -t * 0.22)
    if soap is None: SOAPS.hide_render = True
def frame(f):
    t = f / FPS; nb = beat_at(t); lt = t - B[nb]; du = DUR[nb]; u = lt / du
    lab = nb in (0, 1, 2, 4, 8, 9, 10, 11); mol = nb in (3, 5, 6); bub = nb == 7
    visible(LAB, lab); visible(MOL, mol); visible(BUBSET, bub); pool_hide(); KST.hide_render = True; SOAPS.hide_render = True
    for p_ in O2_FLY: p_[0].hide_render = p_[1].hide_render = True
    tr_in.hide_render = True
    visible(SAFETY, nb == 10)
    if lab and nb not in (8, 9, 10, 11, 0): STEAM.hide_render = True
    c0 = Vector((CX, CY, 0))
    if nb == 0:      # hook: the foam already blasting out of the cylinder and over (sped-up; motion from frame one)
        pts, s, s_land, s_mouth = foam_path(t)
        lab_state(t, foam=lerp(s_mouth + 0.17, s_land + 0.2, u ** 0.8), steam=0.3 * smooth(0.4, 1.0, u), liquid=False)
        look(c0 + Vector((0.36, -0.58, 0.16 + 0.02 * u)), c0 + Vector((0.06, 0.0, 0.3 - 0.03 * u)), 32 + 4 * u, 4.0)
    elif nb == 1:    # the setup, wide: tray, cylinder with its stripes of colour, the bottles, the little beaker of helper
        lab_state(t, foam=0.0, streaks=1.0, ki_on=True, ki_tilt=0.0)
        KPIV.location = KHOME + Vector((KB_R + 0.0018, 0, KB_H)); KPIV.rotation_euler = (0, 0, 0)
        a_ = math.radians(-12 + 14 * u); look(c0 + Vector((0.62 * math.sin(a_), -0.62 * math.cos(a_), 0.28)), c0 + Vector((0.0, 0.06, 0.15)), 34, 5.6)
    elif nb == 2:    # peroxide in the cylinder; a squirt of dish soap falls in; the colour drips run down the wall
        k = smooth(0.1, 0.95, u)
        lab_state(t, foam=0.0, streaks=k)
        if 0.05 < u < 0.55:
            top = Vector((CX + 0.004, CY - 0.002, ZM + 0.09)); land = Vector((CX + 0.003, CY, ZL + 0.001))
            head = top.lerp(land, smooth(0.05, 0.2, u)); tail = top.lerp(land, smooth(0.42, 0.55, u))
            stream_set(SOAPS, [tail, tail.lerp(head, 0.5) + Vector((0.001 * math.sin(t * 20), 0, 0)), head], 0.0026, t * 13)
        look(c0 + Vector((0.07, -0.5, 0.19 + 0.02 * u)), c0 + Vector((0.0, 0.0, 0.17)), 42, 5.0, c0 + Vector((0, -RO, 0.17)))
    elif nb == 4:    # the helper is poured in; at the end it starts to fizz and foam
        tilt = 112 * smooth(0.05, 0.4, u); pour = 0.18 < u < 0.82
        lab_state(t, foam=foam_len(t), streaks=1.0, ki_on=True, ki_tilt=tilt, ki_liq=u < 0.45)
        if pour:
            lip = Vector((CX - 0.004, CY, ZM + 0.012)); land = Vector((CX - 0.006, CY, ZL + 0.001))
            head = lip.lerp(land, smooth(0.18, 0.32, u)); tail = lip.lerp(land, smooth(0.66, 0.82, u))
            stream_set(KST, [tail, tail.lerp(head, 0.5) + Vector((0.0006 * math.sin(t * 25), 0, 0)), head], 0.0021 * (1 - 0.4 * smooth(0.5, 0.8, u)), t * 17)
        look(c0 + Vector((0.05, -0.56, 0.21)), c0 + Vector((0.0, 0.0, 0.2)), 40, 5.0, c0 + Vector((0, -RO, 0.2)))
    elif nb == 8:    # the eruption: up the cylinder, out the top, over and down onto the tray
        lab_state(t, foam=foam_len(t), steam=0.15 * u, liquid=u < 0.3)
        look(c0 + Vector((0.12, -0.66, 0.24 + 0.03 * u)), c0 + Vector((0.07, 0.0, 0.27)), 34, 5.0)
    elif nb == 9:    # it's hot: steam curls off the foam (back-lit)
        lab_state(t, foam=foam_len(t), steam=1.0, liquid=False)
        look(c0 + Vector((0.34 - 0.03 * u, -0.36, 0.12)), c0 + Vector((0.14, -0.06, 0.09)), 55, 2.8, c0 + Vector((0.18, -0.09, 0.05)))
    elif nb == 10:   # gloves and goggles up front, the foam pile behind
        lab_state(t, foam=foam_len(t), steam=0.8, liquid=False)
        look(c0 + Vector((-0.02 + 0.03 * u, -0.62, 0.14)), c0 + Vector((-0.08, -0.3, 0.05)), 48, 2.8, GOG.location)
    elif nb == 11:   # wide: the whole pile; slow pull back
        lab_state(t, foam=foam_len(t), steam=0.6, liquid=False)
        look(c0 + Vector((0.3, -0.72 - 0.08 * u, 0.36 + 0.03 * u)), c0 + Vector((0.05, -0.02, 0.17)), 32, 5.6)
    elif mol:
        mol_beat(nb, t, u)
    elif bub:
        bubble_beat(t, u)

# ---------------------------------------------------------------- molecule beats
def mol_beat(nb, t, u):
    A = Atoms()
    if nb == 3:      # peroxide drifts and tumbles; very slowly, two of them fall apart into water and oxygen
        for k in range(8):
            c = MX + Vector(((h1(k) - 0.5) * 4.2, (h1(k + 20) - 0.5) * 2.0, (k - 3.5) * 1.15))
            if k in (3, 4): continue
            draw_peroxide(A, peroxide(A, c + Vector((0.15 * math.sin(t + k), 0, 0.1 * math.sin(t * 0.7 + k))), (t * 0.35 + k, k * 0.7, t * 0.25 + k)))
        ca = MX + Vector((-0.9, 0, -0.1)); cb = MX + Vector((0.9, 0, 0.45))
        Pa = peroxide(A, ca, (0.3, 0.2, 0.4)); Pb = peroxide(A, cb, (2.0, 0.6, -0.3))
        k = smooth(0.45, 0.8, u)           # the slow split
        if k <= 0.0:
            draw_peroxide(A, Pa); draw_peroxide(A, Pb)
        else:
            drift = Vector((0, 0, 1.6)) * smooth(0.75, 1.0, u)
            o_a, o_b = Pa[1].lerp(MX + Vector((-0.55, 0, 0.3)), k) + drift, Pb[0].lerp(MX + Vector((0.55, 0, 0.3)), k) + drift
            Wa = water_from(Pa[0].lerp(MX + Vector((-1.6, 0, -0.6)), k), (0, 0, 0.4)); Wb = water_from(Pb[1].lerp(MX + Vector((1.6, 0, -0.5)), k), (0, 0.5, -0.4))
            for W in (Wa, Wb): draw_water(A, W)
            if k < 0.6:
                A.put('O', o_a); A.put('O', o_b); A.bond(Pa[0].lerp(Wa[0], k), o_a, 0.075 * (1 - k)); A.bond(Pb[1].lerp(Wb[0], k), o_b, 0.075 * (1 - k))
            else: draw_o2(A, o_a, o_b)
        look(MX + Vector((0.6, -13.5 + 1.2 * u, 0.6)), MX + Vector((0, 0, 0.0)), 40, 2.0)
    else:
        # the iodide helper: grabs one O off a peroxide (water left over), then hands it to the next peroxide's O (oxygen gas, more water)
        cycles = [(MX + Vector((0, 0, 0)), B[5], DUR[5], 1)] if nb == 5 else [
            (MX + Vector((-1.6, 0, 2.6)), B[6] - 0.2, 0.62, 4), (MX + Vector((1.5, 0.4, 0.1)), B[6] - 0.45, 0.58, 4), (MX + Vector((-1.2, -0.2, -2.6)), B[6] - 0.1, 0.66, 4)]
        for ci, (home, t0, per, nmax) in enumerate(cycles):
            run_helper(A, ci, home, t0, per, nmax, t, slow=(nb == 5))
        if nb == 5: look(MX + Vector((0.3, -12.5, 0.6)), MX + Vector((0.3, 0, 0.2)), 46, 2.4)
        else: look(MX + Vector((0.2, -16.5 - 3 * u, 0.2)), MX + Vector((0, 0, 0)), 40, 2.2)
def run_helper(A, ci, home, t0, per, nmax, t, slow):
    """one iodide doing its two-step cycle (one slow cycle for beat 5, quick repeats for beat 6). Peroxides come in, water and O2 leave."""
    if slow:
        u = clamp((t - t0) / per, 0, 1)
        P1 = peroxide(A, home + Vector((-1.3, 0, 0.9)), (0.4 + 0.2 * u, 0.0, 0.6))
        P2 = peroxide(A, home + Vector((1.3, 0, -0.9)), (1.8, 0.4 + 0.2 * u, -0.5))
        P3 = peroxide(A, home + Vector((-0.6, 0.3, -3.2 + 0.3 * u)), (0.9 + u, 1.2, 0.2))
        start = home + Vector((-3.4, -0.6, 2.8))
        off1 = (P1[0] - P1[1]).normalized(); grab1 = P1[0] + off1 * 0.95
        on_i = lambda ip: ip - off1 * 0.95                      # where the grabbed O rides on the iodide
        grab2 = P2[0] + Vector((-0.7, 0, 1.2))
        if u < 0.22: ip = start.lerp(grab1, sm(u / 0.22))
        elif u < 0.36: ip = grab1
        elif u < 0.55: ip = grab1.lerp(grab2, sm((u - 0.36) / 0.19))
        elif u < 0.68: ip = grab2
        else: ip = grab2.lerp(P3[0] + Vector((-0.9, 0, 0.6)), sm((u - 0.68) / 0.32))
        A.put('I', ip)
        k1 = smooth(0.22, 0.36, u); k2 = smooth(0.55, 0.68, u); fly = smooth(0.68, 1.0, u)
        if k1 <= 0: draw_peroxide(A, P1)
        else:                                                    # step one: O1 to the iodide, both H end up on O2 -> water drifts off
            gone = smooth(0.36, 1.0, u); wo = P1[1] + Vector((-0.6, 0, -1.6)) * gone
            W = water_from(wo, (0.2, 0.1, -0.3 + gone)); hA = P1[2].lerp(W[1], k1); hB = P1[3].lerp(W[2], k1)
            A.put('O', wo); A.put('H', hA); A.put('H', hB); A.bond(wo, hA, 0.06); A.bond(wo, hB, 0.06)
            if k2 <= 0:
                o1 = P1[0].lerp(on_i(grab1), k1) if u < 0.36 else on_i(ip)
                A.put('O', o1); A.bond(ip, o1, 0.09 * k1)
                if k1 < 1: A.bond(o1, wo, 0.075 * (1 - k1))
        if k2 <= 0: draw_peroxide(A, P2)
        else:                                                    # step two: that O and P2's first O join (oxygen gas, flies up); P2's other O keeps both H
            mid = (on_i(grab2) + P2[0]) / 2; up = Vector((0.4, 0, 3.8)) * fly
            oa_ = on_i(grab2).lerp(mid + Vector((-0.55, 0, 0)), k2) + up; ob_ = P2[0].lerp(mid + Vector((0.55, 0, 0)), k2) + up
            if k2 < 0.5: A.put('O', oa_); A.put('O', ob_); A.bond(oa_, ob_, 0.06 * k2 * 2); A.bond(ip, oa_, 0.09 * (1 - 2 * k2))
            else: draw_o2(A, oa_, ob_)
            wo = P2[1] + Vector((0.8, 0, -1.4)) * fly; W = water_from(wo, (0.3, 0.6, 0.4 - fly))
            hA = P2[2].lerp(W[1], k2); hB = P2[3].lerp(W[2], k2)
            A.put('O', wo); A.put('H', hA); A.put('H', hB); A.bond(wo, hA, 0.06); A.bond(wo, hB, 0.06)
        draw_peroxide(A, P3)
        return
    ip = home                                                    # the fast loop: same moves, quick, new peroxides every time
    for c in range(nmax):
        tc = t0 + c * per; u = (t - tc) / per
        if u < -0.6 or u > 1.6: continue
        e = (h1(ci * 10 + c) * 6, h1(ci * 10 + c + 3) * 6, h1(ci * 10 + c + 5) * 6); e2 = (e[1], e[2], e[0])
        dirn = Vector((math.cos(c * 2.1 + ci), 0.3 * math.sin(c + ci), math.sin(c * 2.1 + ci))).normalized()
        p1c = home + dirn * 1.6; p2c = home - dirn * 1.6
        if u < 0:
            draw_peroxide(A, peroxide(A, p1c + dirn * (-u) * 3, e)); draw_peroxide(A, peroxide(A, p2c - dirn * (-u) * 3, e2)); continue
        if u < 1: ip = home.lerp(p1c, 0.55 * math.sin(math.pi * clamp(u / 0.5, 0, 1))) if u < 0.5 else home.lerp(p2c, 0.55 * math.sin(math.pi * clamp((u - 0.5) / 0.5, 0, 1)))
        P1 = peroxide(A, p1c, e); P2 = peroxide(A, p2c, e2)
        k1 = smooth(0.12, 0.3, u); k2 = smooth(0.62, 0.8, u); fly = smooth(0.8, 1.6, u)
        if k1 <= 0: draw_peroxide(A, P1)
        else:
            wo = P1[1] + dirn * 2.0 * smooth(0.3, 1.6, u); draw_water(A, water_from(wo, e))
            if k2 <= 0: o1 = P1[0].lerp(ip + dirn * 0.9, k1); A.put('O', o1); A.bond(ip, o1, 0.09 * k1)
        if k2 <= 0: draw_peroxide(A, P2)
        else:
            q = P2[0] + Vector((0, 0, 0.4)) * k2 + Vector((0, 0, 4.5)) * fly - dirn * 0.6 * fly; d = dirn * 0.55
            draw_o2(A, q + d, q - d)
            wo = P2[1] - dirn * 1.8 * fly; draw_water(A, water_from(wo, e2))
    A.put('I', ip)

# ---------------------------------------------------------------- bubble beat
def bubble_beat(t, u):
    BUB_W.default_value = t * 0.6
    for i, (bo_, p, r) in enumerate(BUBS):
        tb = 0.05 + 0.6 * h1(i * 13); g = smooth(tb, tb + 0.22, u)           # each bubble blows up as oxygen arrives
        rr = r * (0.15 + 0.85 * g) * (1 + 0.015 * math.sin(t * 6 + i)); bo_.scale = (rr, rr, rr); bo_.hide_render = g <= 0.0
        bo_.location = p + Vector((0, 0, 0.25 * u))
    for k, (oa, ob) in enumerate(O2_FLY):                                     # oxygen pairs fly in and vanish into bubbles
        i = (k * 3) % len(BUBS); bo_, p, r = BUBS[i]; tb = 0.05 + 0.6 * h1(i * 13)
        fu = clamp((u - (tb - 0.18)) / 0.2, 0, 1)
        if 0 < fu < 1:
            src = p + Vector(((h1(k) - 0.5) * 6, -4.0, -4.0 - 2 * h1(k + 1))); c = src.lerp(p, sm(fu))
            d = Euler((t * 3 + k, k, t * 2)).to_matrix() @ Vector((0.13, 0, 0))
            oa.location = c - d; ob.location = c + d; oa.hide_render = ob.hide_render = False
    look(BX + Vector((0.4, -13.5 + 1.8 * u, 0.3)), BX + Vector((0, 1.5, 0.2)), 44, 2.4, BX + Vector((0, 0.3, 0)))

# ================================================================ render
os.makedirs(a.out, exist_ok=True)
if a.only: todo = [int(x) for x in a.only.split(',')]; names = todo
elif STRIDE:
    J, N = STRIDE['jobs'], int(round(TOTAL * FPS)); job = a.f0 // STRIDE['ch']
    todo = list(range(job, N, J)); names = [a.f0 + i for i in range(len(todo))]
else: todo = list(range(a.f0, a.f1)); names = todo
for f, nm in zip(todo, names):
    frame(f); S.render.filepath = os.path.join(a.out, f'f_{nm:05d}.png'); bpy.ops.render.render(write_still=True); print('frame', f, '->', nm, flush=True)
