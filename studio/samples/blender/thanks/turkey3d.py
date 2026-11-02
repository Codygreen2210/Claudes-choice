# "Why you should never fry a frozen turkey" — the whole Short as one Blender scene, driven frame by frame from the narration timing.
#   python3 turkey3d.py OUTDIR F0 F1 [--samples 40] [--scale 1.0]      -> OUTDIR/f_00000.png ...
#   python3 turkey3d.py OUTDIR --still 2.5,8.0 [--samples 16 --scale 0.4]
import sys, os, math, json, random, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Euler
import tg_lib as T
from tg_lib import ease, lerp, vlerp, shake

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int, nargs='?', default=0); ap.add_argument('f1', type=int, nargs='?', default=0)
ap.add_argument('--samples', type=int, default=40); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--still', default='')
a = ap.parse_args()
TM = json.load(open(os.path.join(T.HERE, 'turkey_times.json'))); B = TM['starts'] + [TM['total']]; TOT = TM['total']
FPS = 30
def beat(t):
    for i in range(len(B) - 1):
        if t < B[i + 1]: return i, t - B[i], B[i + 1] - B[i]
    return len(B) - 2, t - B[-2], B[-1] - B[-2]

S = T.reset(FPS)
W = bpy.data.worlds.new('dusk'); S.world = W
bg = W.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (*T.lin((0.16, 0.2, 0.32)), 1); bg.inputs['Strength'].default_value = 0.35

# ---------------- set A: the driveway at dusk
A = []                                                           # objects that belong to set A
def a_(o): A.append(o); return o
conc = T.mat('concrete', (0.55, 0.54, 0.52), 0.9); T.color_noise(conc, 3, (0.58, 0.57, 0.55), (0.42, 0.41, 0.4), 0.3, 0.75); T.bump(conc, 300, 0.25, 0.001, kind='voronoi')
a_(T.add('plane', 'ground', conc, (0, 0, 0), (8, 8, 1), smooth=False))
siding = T.mat('siding', (0.62, 0.6, 0.55), 0.8); T.bump(siding, 1, 0.0, 0.0)
house = a_(T.add('cube', 'house', siding, (0, 4.2, 2.0), (6, 0.2, 2.0), smooth=False))
for i, x in enumerate((-2.2, 1.6, 3.4)):                         # warm windows
    a_(T.add('plane', 'win%d' % i, T.emit_mat('winm%d' % i, (1.0, 0.72, 0.4), 1.2), (x, 3.99, 1.6), (0.35, 0.45, 1), (math.pi / 2, 0, 0), smooth=False))
gd = a_(T.add('plane', 'garage', T.mat('garage_m', (0.85, 0.85, 0.82), 0.6), (-0.4, 3.99, 1.1), (1.4, 1.1, 1), (math.pi / 2, 0, 0), smooth=False))
fence = T.mat('fence_m', (0.45, 0.33, 0.22), 0.85)
for i in range(30): a_(T.add('cube', 'post%d' % i, fence, (4.5, -3 + i * 0.25, 0.8), (0.04, 0.11, 0.8), smooth=False))
lamp = a_(T.light('AREA', 'porch', (-1.6, 2.6, 2.4), (0, 0, 0.6), 90, (1.0, 0.75, 0.48), 0.6))
key = a_(T.light('AREA', 'key', (-1.4, -1.2, 1.6), (0, 0, 0.6), 70, (1.0, 0.85, 0.7), 1.0))
rim = a_(T.light('AREA', 'rim', (1.2, 1.6, 1.4), (0, 0, 0.6), 60, (0.6, 0.72, 1.0), 0.8))

# fryer stand, burner, propane tank
steel = T.mat('steel', (0.75, 0.75, 0.75), 0.28, 1.0, aniso=0.5); T.bump(steel, 400, 0.05, 0.0003)
black = T.mat('stand', (0.08, 0.08, 0.08), 0.55, 0.6)
for k in range(3):
    ang = k * 2 * math.pi / 3 + 0.4
    leg = a_(T.add('cylinder', 'leg%d' % k, black, (0.22 * math.cos(ang), 0.22 * math.sin(ang), 0.14), (0.012, 0.012, 0.15), (0.28 * math.sin(ang), -0.28 * math.cos(ang), 0), vertices=12))
ring = a_(T.add('torus', 'ring', black, (0, 0, 0.27), (1, 1, 1), major_radius=0.2, minor_radius=0.012))
burn = a_(T.add('cylinder', 'burner', T.mat('cast', (0.15, 0.13, 0.12), 0.7, 0.8), (0, 0, 0.2), (0.07, 0.07, 0.02), vertices=32))
flames = []
fm = T.emit_mat('blueflame', (0.35, 0.55, 1.0), 25)
for k in range(16):
    ang = k * 2 * math.pi / 16
    f = a_(T.add('cone', 'fl%d' % k, fm, (0.06 * math.cos(ang), 0.06 * math.sin(ang), 0.235), (0.008, 0.008, 0.02), vertices=8)); flames.append(f)
flame_lt = a_(T.light('POINT', 'flame_lt', (0, 0, 0.24), (0, 0, 0), 12, (0.45, 0.6, 1.0), 0.05))
tankm = T.mat('tank', (0.92, 0.92, 0.9), 0.35, coat=0.4)
tank = a_(T.add('cylinder', 'tank', tankm, (0.65, 0.35, 0.22), (0.15, 0.15, 0.22), vertices=48))
a_(T.add('uv_sphere', 'tanktop', tankm, (0.65, 0.35, 0.44), (0.15, 0.15, 0.06), segments=48, ring_count=16))
hose = a_(T.add('torus', 'hose', T.mat('hose_m', (0.05, 0.05, 0.05), 0.6), (0.35, 0.2, 0.05), (1, 0.6, 1), (0, 0, 0.5), major_radius=0.25, minor_radius=0.008))

# the pot
POT_B, POT_H, POT_R = 0.3, 0.45, 0.17
pot = a_(T.lathe('pot', [(0.0, POT_B), (POT_R, POT_B), (POT_R + 0.004, POT_B + 0.01), (POT_R + 0.004, POT_B + POT_H), (POT_R + 0.012, POT_B + POT_H + 0.008),
                         (POT_R + 0.006, POT_B + POT_H + 0.01), (POT_R - 0.002, POT_B + POT_H), (POT_R - 0.002, POT_B + 0.012), (0.0, POT_B + 0.006)], 96, steel))
for s in (-1, 1):
    a_(T.add('torus', 'handle%d' % s, steel, (s * (POT_R + 0.03), 0, POT_B + POT_H - 0.05), (1, 1, 1), (math.pi / 2, 0, 0), major_radius=0.03, minor_radius=0.006))

oilm = T.mat('oil', (0.98, 0.72, 0.25), 0.04, trans=0.85, ior=1.47)
N, L, ob = T.nodes(oilm)
absn = oilm.node_tree.nodes.new('ShaderNodeVolumeAbsorption'); absn.inputs['Color'].default_value = (*T.lin((0.95, 0.6, 0.18)), 1); absn.inputs['Density'].default_value = 45
L.new(absn.outputs[0], oilm.node_tree.nodes['Material Output'].inputs['Volume'])
OIL0 = POT_B + 0.3
oil = a_(T.add('cylinder', 'oil', oilm, (0, 0, (POT_B + 0.006 + OIL0) / 2), (POT_R - 0.004, POT_R - 0.004, (OIL0 - POT_B - 0.006) / 2), vertices=96))
surf = a_(T.add('circle', 'oilsurf', oilm, (0, 0, OIL0), (POT_R - 0.004, POT_R - 0.004, 1), vertices=96, fill_type='TRIFAN'))
sub = surf.modifiers.new('sub', 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = sub.render_levels = 4
tex = bpy.data.textures.new('ripple', 'CLOUDS'); tex.noise_scale = 0.03
dsp = surf.modifiers.new('dsp', 'DISPLACE'); dsp.texture = tex; dsp.strength = 0.004; dsp.texture_coords = 'OBJECT'
rip = bpy.data.objects.new('ripple_e', None); T.link(rip); dsp.texture_coords_object = rip
skirt = a_(T.lathe('skirt', [(POT_R + 0.0065, 0.0), (POT_R + 0.0085, 0.5), (POT_R + 0.0065, 1.0)], 96, oilm))   # oil running down the outside (scaled in z)
skirt.location.z = POT_B + POT_H

# the frozen turkey on its hook
frz = T.frozen_mat()
tk = a_(T.turkey_mesh('turkey', 'raw')); tk.data.materials.append(frz); tk.scale = (0.75, 0.75, 0.75)
tk.rotation_euler = (0, math.radians(90), 0)
hookm = steel
rod = a_(T.add('cylinder', 'rod', hookm, (0, 0, 0), (0.006, 0.006, 1.0), vertices=12))
hook = a_(T.add('torus', 'hook', hookm, (0, 0, 0), (1, 1, 1), (math.pi / 2, 0, 0), major_radius=0.028, minor_radius=0.005))
icem = T.mat('ice', (0.88, 0.94, 1.0), 0.12, trans=0.92, ior=1.31); T.bump(icem, 60, 0.4, 0.002)
ice = []
random.seed(7)
for i in range(7):
    c = a_(T.add('cube', 'ice%d' % i, icem, (0, 0, 0), (1, 1, 1), smooth=False))
    bv = c.modifiers.new('bv', 'BEVEL'); bv.width = 0.15; bv.segments = 2
    ice.append((c, Vector((random.uniform(-0.018, 0.018), random.uniform(-0.016, 0.016), random.uniform(-0.012, 0.01))), random.uniform(0.008, 0.014), random.uniform(0, 3)))

# bubbles, splash drops, water drops
bubm = T.mat('bub', (1.0, 0.9, 0.6), 0.02, trans=1.0, ior=1.3)
foam = T.mat('foam', (0.98, 0.88, 0.62), 0.35, sss=0.4, sss_s=0.01)
bubbles = [a_(T.add('uv_sphere', 'b%d' % i, bubm if i % 3 else foam, (0, 0, -5), (0.01, 0.01, 0.01), segments=16, ring_count=8)) for i in range(140)]
drops = [a_(T.add('uv_sphere', 'd%d' % i, oilm, (0, 0, -5), (0.006, 0.006, 0.006), segments=12, ring_count=6)) for i in range(48)]
waterm = T.mat('water', (0.75, 0.88, 1.0), 0.0, trans=1.0, ior=1.33)
wdrops = [a_(T.add('uv_sphere', 'w%d' % i, waterm, (0, 0, -5), (0.009, 0.009, 0.011), segments=24, ring_count=12)) for i in range(7)]
steam_m, steam_nz, _ = T.volume_mat('steam', (1, 1, 1), 40, 6)
steams = [a_(T.add('uv_sphere', 's%d' % i, steam_m, (0, 0, -5), (0.01, 0.01, 0.01), segments=24, ring_count=12)) for i in range(7)]
plume_m, plume_nz, _ = T.volume_mat('plume', (1, 1, 1), 6, 3)
plume = a_(T.add('uv_sphere', 'plume', plume_m, (0, 0, -5), (0.2, 0.2, 0.4), segments=24, ring_count=12))
fire_m, fire_nz, fire_v = T.volume_mat('fire', fire=True, density=3, scale=3.2, edge=0.15)
fire = a_(T.add('uv_sphere', 'fire', fire_m, (0, 0, -5), (0.1, 0.1, 0.1), segments=32, ring_count=16))
fire_lt = a_(T.light('POINT', 'fire_lt', (0, -0.2, 0.9), (0, 0, 0), 0, (1.0, 0.55, 0.2), 0.5))

# cutaway: half pot, half oil (back half, y > 0) shown in beats 2-3; the turkey is cut with a boolean (it is a closed mesh)
POTPROF = [(0.0, POT_B), (POT_R, POT_B), (POT_R + 0.004, POT_B + 0.01), (POT_R + 0.004, POT_B + POT_H), (POT_R + 0.012, POT_B + POT_H + 0.008),
           (POT_R + 0.006, POT_B + POT_H + 0.01), (POT_R - 0.002, POT_B + POT_H), (POT_R - 0.002, POT_B + 0.012), (0.0, POT_B + 0.006)]
pot_h = a_(T.lathe('pot_half', POTPROF, 48, steel, arc=(0, math.pi)))
rr_ = POT_R - 0.004
oil_h = a_(T.lathe('oil_half', [(0.0, POT_B + 0.006), (rr_, POT_B + 0.006), (rr_, 1.0), (0.0, 1.0)], 48, oilm, arc=(0, math.pi)))
import bmesh
def close_cut(o):                                  # cap the open cut faces of the half oil so it reads as a solid block
    bm = bmesh.new(); bm.from_mesh(o.data)
    edges = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=edges, sides=0); bm.to_mesh(o.data); bm.free()
close_cut(oil_h)
OIL_H_TOP = 1.0
cut = bpy.data.objects.new('cutter', bpy.data.meshes.new('cutter')); T.link(cut)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(cut.data); bm.free()
cut.location = (0, -0.5, 0.6); cut.scale = (1.2, 1.0, 1.4); cut.hide_render = True; cut.display_type = 'WIRE'
tkcut = tk.modifiers.new('cut', 'BOOLEAN'); tkcut.operation = 'DIFFERENCE'; tkcut.object = cut; tkcut.solver = 'EXACT'
cuts = [tkcut]
inner = T.mat('inner', (0.6, 0.6, 0.62), 0.35, 1.0)

# ---------------- set B: the Thanksgiving table (built away from the driveway)
before = set(S.objects)
tb = T.table_set(); T.room_back()
BSET = [o for o in S.objects if o not in before]
OFF = Vector((30, 0, 0))
for o in BSET:
    if o.parent is None: o.location += OFF
tb_key = T.light('AREA', 'tb_key', OFF + Vector((-1.0, -0.6, 1.3)), OFF, 180, (1.0, 0.85, 0.7), 0.6); BSET.append(tb_key)
tb_rim = T.light('AREA', 'tb_rim', OFF + Vector((0.8, 1.5, 1.2)), OFF, 60, (1.0, 0.7, 0.45), 1.0); BSET.append(tb_rim)

cam = T.camera(30, 2.4)
T.render_setup(a.samples, a.scale)
S.cycles.volume_step_rate = 3.0

def setvis(objs, on):
    for o in objs: o.hide_render = not on

# ---------------- per-frame state
def turkey_z(t):
    """B0: falls from 1.15 into the oil (rests at 0.6). B7: hangs at 1.6 and starts lowering, reaching 1.15 at the loop with the same speed as B0's start."""
    i, u, d = beat(t)
    if i == 7:
        k = u / d
        return lerp(1.45, 1.15, k ** 2)
    if i == 0:
        if u < 1.9: return lerp(1.15, 0.6, ease(u / 1.9) * 0.15 + (u / 1.9) ** 2 * 0.85)
        return 0.6 - 0.025 * math.exp(-(u - 1.9) * 3) * math.sin((u - 1.9) * 9)
    return 0.6

def boil_level(t):
    i, u, d = beat(t)
    if i == 0: return 0.15 if u < 1.85 else 1.0
    if i in (1, 2): return 0.85
    if i == 3: return 0.9 + 0.1 * u / d
    if i == 4: return 1.4
    if i == 5: return 1.4
    return 0.12

def oil_level(t):
    i, u, d = beat(t)
    if i == 3: return OIL0 + 0.06 * ease((u - 3.5) / (d - 3.5))
    if i == 4: return lerp(OIL0 + 0.06, POT_B + POT_H + 0.012, ease(u / 2.2))
    if i == 5: return POT_B + POT_H + 0.012
    return OIL0

def overflow(t):
    i, u, d = beat(t)
    if i == 4: return ease((u - 2.0) / 2.8)
    if i == 5: return 1.0
    return 0.0

def place_bubbles(t, lvl, z_surf, cutaway):
    random.seed(11)
    n = len(bubbles); act = int(n * min(1, lvl / 1.4))
    for i, b in enumerate(bubbles):
        ang = random.uniform(0, 6.283); rr = (POT_R - 0.015) * math.sqrt(random.random()); life = random.uniform(0.35, 0.9); ph = random.random()
        sz = random.uniform(0.004, 0.012) * (1.3 if lvl > 1.2 else 1)
        if i >= act: b.location = (0, 0, -5); continue
        k = ((t * (1 + lvl)) / life + ph) % 1.0
        x, y = rr * math.cos(ang), rr * math.sin(ang)
        if cutaway and i % 2 == 0 and y > -0.01:                  # rising bubbles seen through the cut
            z = lerp(POT_B + 0.03, z_surf, k); s = sz * (0.4 + 0.6 * k)
            b.location = (x, max(y, 0.005), z); b.scale = (s, s, s); continue
        s = sz * math.sin(math.pi * k) ** 0.5
        b.location = (x, y, z_surf + s * 0.2); b.scale = (s, s, s * 0.7)

def place_drops(t):
    i, u, d = beat(t)
    random.seed(5)
    for j, dr in enumerate(drops):
        vx, vy, vz = random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(1.4, 2.6)
        t0 = 1.85 + random.uniform(0, 0.5); s = random.uniform(0.004, 0.009)
        if i == 0 and u > t0:
            tt = (u - t0) * 0.55                                 # slow motion
            z = OIL0 + vz * tt - 4.9 * tt * tt
            if z > 0.02:
                dr.location = (0.05 * vx + vx * tt * 0.4, 0.05 * vy + vy * tt * 0.4, z); dr.scale = (s, s, s * 1.4); continue
        if i == 4 and u > 1.2:                                    # spitting oil while it boils over
            tt = ((u - 1.2) * 0.6 + random.random() * 0.4) % 0.45
            z = oil_level(t) + vz * 0.5 * tt - 4.9 * tt * tt
            if z > oil_level(t):
                ang = random.uniform(0, 6.28); dr.location = (0.12 * math.cos(ang), 0.12 * math.sin(ang), z); dr.scale = (s, s, s); continue
        dr.location = (0, 0, -5)

def place_water(t, tz):
    i, u, d = beat(t)
    random.seed(9)
    for j, w in enumerate(wdrops):
        x = random.uniform(-0.05, 0.05); y = random.uniform(0.005, 0.03); t0 = 0.4 + j * 0.38
        top = tz - 0.165 + 0.01; bot = POT_B + 0.02
        if i == 2 and u > t0:
            k = min(1, (u - t0) / 1.4); z = lerp(top, bot, k * k)
            w.location = (x, y, z); s = 1.0; w.scale = (0.009 * s, 0.009 * s, 0.012 * s); continue
        if i == 3 and u < 0.6 + j * 0.25:
            w.location = (x, y, bot); continue
        w.location = (0, 0, -5)

def place_steam(t):
    i, u, d = beat(t)
    random.seed(9)
    for j, st in enumerate(steams):
        x = random.uniform(-0.05, 0.05); y = random.uniform(0.005, 0.03); t0 = 0.6 + j * 0.25
        if i == 3 and u > t0:
            g = ease((u - t0) / 2.6); r = lerp(0.006, 0.07 + 0.012 * j % 3, g)
            z = POT_B + 0.02 + r * 0.9 + 0.08 * max(0, u - t0 - 2.0) * 0.4
            st.location = (x * (1 + g), y + r * 0.3, min(z, oil_level(t) - r * 0.4)); st.scale = (r, r, r * 1.1); continue
        st.location = (0, 0, -5)
    steam_nz.inputs['W'].default_value = t * 0.8

def cam_at(t):
    i, u, d = beat(t)
    k = u / d
    if i in (0, 7):
        p0, t0 = Vector((0.75, -0.9, 1.3)), Vector((0, 0, 0.8))
        if i == 7: return p0 + shake(t, 0.0015), t0, 32, Vector((0, 0, 0.8))
        p = vlerp(p0, (0.5, -0.62, 1.02), ease((u - 0.3) / 3.5)); tgt = vlerp(t0, (0, 0, 0.7), ease(u / 2.0))
        sh = shake(t, 0.008 * math.exp(-max(0, u - 1.9) * 2) if u > 1.85 else 0.0015)
        return p + sh, tgt, 32, tgt
    if i == 1:
        tz = turkey_z(t)
        p = vlerp((0.13, -0.24, tz + 0.5), (0.07, -0.13, tz + 0.36), ease(k)); tgt = Vector((0, 0, tz + 0.13))
        return p + shake(t, 0.001), tgt, 45, tgt
    if i == 2:
        p = vlerp((0.0, -1.25, 0.66), (0.0, -1.05, 0.6), ease(k)); tgt = Vector((0, 0, 0.5))
        return p + shake(t, 0.001), tgt, 38, Vector((0, 0.0, 0.45))
    if i == 3:
        g = ease((u - 3.4) / 4.5)
        p = vlerp((0.0, -0.72, 0.46), (0.0, -1.1, 0.6), g); tgt = vlerp((0, 0, 0.4), (0, 0, 0.5), g)
        return p + shake(t, 0.001), tgt, 38, Vector((0, 0.0, tgt.z))
    if i == 4:
        p = vlerp((0.7, -0.85, 1.05), (0.85, -1.05, 0.85), ease(k)); tgt = vlerp((0, 0, 0.74), (0, 0, 0.6), ease(k))
        return p + shake(t, 0.002 + 0.004 * k), tgt, 32, tgt
    if i == 5:
        p = vlerp((0.9, -1.1, 0.9), (1.9, -2.5, 1.3), ease(u / 3.5)); tgt = vlerp((0, 0, 0.7), (0, 0, 1.1), ease(u / 3.5))
        return p + shake(t, 0.02 * math.exp(-u * 1.2) + 0.004), tgt, 30, tgt
    p = OFF + vlerp((-0.6, -1.15, 0.78), (0.4, -1.05, 0.7), ease(k)); tgt = OFF + vlerp((-0.25, 0.02, 0.04), (0.15, 0.02, 0.04), ease(k))
    return p, tgt, 30, OFF + Vector((0, 0, 0.08))

focus = bpy.data.objects.new('focus', None); T.link(focus); cam.data.dof.focus_object = focus

def frame(t):
    i, u, d = beat(t)
    table = i == 6
    setvis(A, not table); setvis(BSET, table)
    cutaway = i in (2, 3)
    for md in cuts: md.show_render = cutaway
    if not table:
        for o in (pot, oil, surf): o.hide_render = cutaway
        for o in (pot_h, oil_h): o.hide_render = not cutaway
    tz = turkey_z(t)
    tk.location = (0, 0, tz); sway = 0.04 * math.sin(t * 1.7) * (1 if i == 7 else 0.15)
    tk.rotation_euler = (sway, math.radians(90), 0.3 * math.sin(t * 0.4) if i == 7 else 0.0)
    top = tz + 0.26 * 0.75
    hook.location = (0, 0, top + 0.03); rod.location = (0, 0, top + 0.06 + 1.0)
    for c, off, s, r in ice:
        ok = i in (0, 1, 7) or (i == 2 and u < 0.2)
        melt = 1.0 if i != 1 else 1.0 - 0.35 * ease(u / d)
        c.location = Vector((0, 0, tz + 0.13)) + off if ok else Vector((0, 0, -5))
        c.scale = (s * melt, s * melt * 0.9, s * melt * 1.1); c.rotation_euler = (r, r * 0.7, r * 1.3)
    lvl = oil_level(t)
    for v in oil_h.data.vertices:
        if v.co.z > POT_B + 0.1: v.co.z = lvl
    oil_h.data.update()
    surf.location.z = lvl; oil.location.z = (POT_B + 0.006 + lvl) / 2; oil.scale.z = (lvl - POT_B - 0.006) / 2
    rip.location = (t * 0.05, t * 0.03, t * 0.08 * (1 + boil_level(t)))
    dsp.strength = 0.002 + 0.005 * boil_level(t)
    ov = overflow(t); skirt.scale = (1, 1, max(0.001, ov * 0.8)); skirt.location.z = POT_B + POT_H + 0.008 - ov * 0.8 * 0.5 * 0; skirt.hide_render = ov <= 0 or table
    if ov > 0: skirt.location.z = POT_B + POT_H + 0.008 - ov * 0.8;
    place_bubbles(t, boil_level(t), lvl, cutaway)
    place_drops(t); place_water(t, tz); place_steam(t)
    # plume of steam over the pot while it boils over; the fireball
    for o in steams: o.hide_render = i != 3 or table
    plume.hide_render = i != 4; fire.hide_render = i != 5
    if i == 4:
        g = ease(u / d); plume.location = (0, 0, POT_B + POT_H + 0.25 + 0.2 * g); plume.scale = (0.18 + 0.15 * g, 0.18 + 0.15 * g, 0.3 + 0.3 * g)
    else: plume.location = (0, 0, -5)
    plume_nz.inputs['W'].default_value = t * 0.6
    if i == 5:
        g = ease(u / 1.4); r = lerp(0.12, 1.0, g) * (1 + 0.15 * u / d)
        fire.location = (0.05, -0.05, 0.25 + r * 0.75 + 0.15 * u); fire.scale = (r * 0.9, r * 0.9, r * 1.35)
        fire_nz.inputs['W'].default_value = t * 1.6; fire_lt.data.energy = 900 * g * (0.85 + 0.15 * math.sin(t * 23))
        fire_lt.location = (0, -0.3, 0.6 + r * 0.6)
    else:
        fire.location = (0, 0, -5); fire_lt.data.energy = 0
    for k, f in enumerate(flames): f.scale.z = 0.02 * (0.8 + 0.3 * math.sin(t * 31 + k * 1.7))
    flame_lt.data.energy = 10 + 2 * math.sin(t * 29)
    if table:
        for c, fl, lt in tb['candles']:
            fl.scale.z = 0.018 * (0.9 + 0.12 * math.sin(t * 13 + c.location.x * 40)); lt.data.energy = 1.6 * (0.85 + 0.15 * math.sin(t * 17 + c.location.x * 30))
    p, tgt, lens, foc = cam_at(t)
    cam.location = p; T.look(cam, tgt); cam.data.lens = lens; focus.location = foc
    cam.data.dof.aperture_fstop = 1.8 if i in (1,) else 2.6

os.makedirs(a.out, exist_ok=True)
if a.still:
    for t in [float(x) for x in a.still.split(',')]:
        frame(t); S.render.filepath = os.path.join(a.out, 'still_%05.2f.png' % t); bpy.ops.render.render(write_still=True)
else:
    for f in range(a.f0, a.f1):
        frame(f / FPS); S.render.filepath = os.path.join(a.out, 'f_%05d.png' % f); bpy.ops.render.render(write_still=True)
        print('frame', f, flush=True)
