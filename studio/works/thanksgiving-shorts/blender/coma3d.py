# "Why you get so sleepy after Thanksgiving dinner" — the whole Short as one Blender scene, driven frame by frame from the narration timing.
#   python3 coma3d.py OUTDIR F0 F1 [--samples 24] [--scale 0.6667]  |  python3 coma3d.py OUTDIR --still 1,6,10
import sys, os, math, json, random, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Euler
import tg_lib as T
from tg_lib import ease, lerp, vlerp, shake

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('f0', type=int, nargs='?', default=0); ap.add_argument('f1', type=int, nargs='?', default=0)
ap.add_argument('--samples', type=int, default=24); ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--still', default='')
a = ap.parse_args()
TM = json.load(open(os.path.join(T.HERE, 'coma_times.json'))); B = TM['starts'] + [TM['total']]
FPS = 30
def beat(t):
    for i in range(len(B) - 1):
        if t < B[i + 1]: return i, t - B[i], B[i + 1] - B[i]
    return len(B) - 2, t - B[-2], B[-1] - B[-2]

S = T.reset(FPS)
W = bpy.data.worlds.new('room'); S.world = W
bg = W.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (*T.lin((0.12, 0.08, 0.06)), 1); bg.inputs['Strength'].default_value = 0.4
SETS = {}
def grab(name, fn):
    before = set(S.objects); r = fn(); SETS[name] = [o for o in S.objects if o not in before]; return r

# ---------------- set 1: the dinner table with the hero plate, gravy, clock (origin)
def set_table():
    tb = T.table_set(); T.room_back()
    T.light('AREA', 'tb_key', (-1.0, -0.8, 1.3), (0, -0.2, 0), 160, (1.0, 0.85, 0.7), 0.6)
    T.light('AREA', 'tb_rim', (0.8, 1.5, 1.2), (0, 0, 0), 60, (1.0, 0.7, 0.45), 1.0)
    T.light('AREA', 'plate_fill', (0.5, -1.0, 0.6), (0, -0.38, 0.03), 25, (1.0, 0.9, 0.8), 0.5)
    hero = Vector((0, -0.38, 0.0))
    # food heaped on the hero plate
    mash = T.mash('hero_mash', hero + Vector((-0.02, 0.01, 0.01)), 0.055, 0.05)
    white = T.mat('white_meat', (0.93, 0.86, 0.74), 0.5, sss=0.25, sss_r=(1, 0.8, 0.6), sss_s=0.01); T.bump(white, 120, 0.2, 0.0006)
    rm = T.roast_mat()
    for k in range(4):
        sl = T.add('cube', 'slice%d' % k, white, hero + Vector((0.055 + k * 0.012, -0.03 + k * 0.006, 0.014 + k * 0.004)), (0.045, 0.03, 0.005), (0.25 - k * 0.05, 0.15, 0.6 + k * 0.1))
        bv = sl.modifiers.new('bv', 'BEVEL'); bv.width = 0.004; bv.segments = 3
        sl.data.materials.append(rm); sl.data.polygons[4].material_index = 1        # one face roasted skin
    stuff = T.mat('stuffing', (0.6, 0.42, 0.22), 0.6); T.color_noise(stuff, 40, (0.7, 0.5, 0.26), (0.38, 0.22, 0.1), 0.35, 0.7); T.bump(stuff, 200, 0.3, 0.001)
    random.seed(4)
    for k in range(26):
        c = T.add('cube', 'stf%d' % k, stuff, hero + Vector((random.uniform(-0.085, -0.03), random.uniform(-0.06, -0.01), 0.012 + random.uniform(0, 0.025))),
                  (0.008, 0.007, 0.007), (random.random() * 3, random.random() * 3, random.random() * 3), smooth=False)
        c.modifiers.new('bv', 'BEVEL').width = 0.002
    bean = T.mat('bean', (0.28, 0.5, 0.15), 0.35, sss=0.2, coat=0.3)
    for k in range(10):
        T.add('cylinder', 'bean%d' % k, bean, hero + Vector((0.01 + random.uniform(-0.02, 0.03), 0.055 + random.uniform(-0.01, 0.015), 0.016 + k * 0.002)),
              (0.0035, 0.0035, 0.03), (math.pi / 2, 0, random.uniform(-0.6, 0.6)), vertices=12)
    cm = T.mat('cran2', (0.5, 0.03, 0.06), 0.15, sss=0.6, sss_r=(1, 0.1, 0.1), sss_s=0.02, coat=0.5)
    T.add('uv_sphere', 'crandollop', cm, hero + Vector((0.06, 0.05, 0.016)), (0.02, 0.02, 0.012))
    T.roll('hero_roll', hero + Vector((-0.07, 0.065, 0.028)))
    # gravy: boat above the plate, stream, pool on the mash
    gb = tb['gravyboat']; gb.location = hero + Vector((-0.13, 0.02, 0.2)); gb.scale = (1.2, 0.85, 0.85)
    gm = T.gravy_mat()
    stream = T.add('cylinder', 'stream', gm, (0, 0, 0), (1, 1, 1), vertices=16)
    pool = T.add('uv_sphere', 'pool', gm, hero + Vector((-0.02, 0.01, 0.06)), (0.01, 0.01, 0.004), segments=48, ring_count=24)
    dp = pool.modifiers.new('dp', 'DISPLACE'); tx = bpy.data.textures.new('gv', 'CLOUDS'); tx.noise_scale = 0.4; dp.texture = tx; dp.strength = 0.0015
    # wall clock
    clk = T.add('cylinder', 'clock', T.mat('clockface', (0.95, 0.93, 0.86), 0.4), (-0.7, 2.17, 1.35), (0.18, 0.18, 0.015), (math.pi / 2, 0, 0), vertices=64)
    T.add('torus', 'clockrim', T.mat('clockrim_m', (0.2, 0.12, 0.06), 0.4, 0.3), (-0.7, 2.16, 1.35), (1, 1, 1), (math.pi / 2, 0, 0), major_radius=0.18, minor_radius=0.015)
    hm = T.mat('hand', (0.05, 0.05, 0.05), 0.4)
    hh = T.add('cube', 'hourhand', hm, (-0.7, 2.15, 1.35), (0.006, 0.002, 0.06), smooth=False)
    mh = T.add('cube', 'minhand', hm, (-0.7, 2.148, 1.35), (0.004, 0.002, 0.09), smooth=False)
    for k in range(12):
        ang = k * math.pi / 6
        T.add('cube', 'tick%d' % k, hm, (-0.7 + 0.15 * math.sin(ang), 2.152, 1.35 + 0.15 * math.cos(ang)), (0.004, 0.002, 0.012), (0, ang, 0), smooth=False)
    return dict(tb=tb, gb=gb, stream=stream, pool=pool, hero=hero, hh=hh, mh=mh)
TB = grab('table', set_table)

# ---------------- set 2: three plates and three glass tubes (x = 30)
O2 = Vector((30, 0, 0))
def set_compare():
    wood = bpy.data.materials['wood']
    T.add('cube', 'cmp_table', wood, O2 + Vector((0, 0, -0.025)), (1.0, 0.6, 0.025), smooth=False)
    T.light('AREA', 'cmp_key', O2 + Vector((-0.6, -0.9, 1.2)), O2, 160, (1.0, 0.88, 0.75), 0.8)
    T.light('AREA', 'cmp_rim', O2 + Vector((0.3, 1.2, 1.0)), O2, 70, (1.0, 0.75, 0.5), 1.0)
    wall = T.add('plane', 'cmp_wall', bpy.data.materials['wall_m'], O2 + Vector((0, 1.2, 0.8)), (2, 1, 1), (math.pi / 2, 0, 0), smooth=False)
    rm = T.roast_mat(); white = bpy.data.materials['white_meat']
    pork = T.mat('pork', (0.78, 0.55, 0.38), 0.4, coat=0.3, sss=0.2); T.color_noise(pork, 25, (0.8, 0.58, 0.4), (0.45, 0.25, 0.12), 0.4, 0.8); T.bump(pork, 50, 0.2, 0.002)
    chick = T.mat('chicken', (0.85, 0.62, 0.32), 0.35, coat=0.4, sss=0.2); T.color_noise(chick, 20, (0.88, 0.66, 0.32), (0.6, 0.35, 0.12), 0.35, 0.8); T.bump(chick, 60, 0.25, 0.002)
    tubes = []
    glass = T.mat('tubeglass', (0.9, 0.95, 1.0), 0.05, alpha=0.18, coat=1.0, coat_r=0.02)
    liq = T.mat('glowliq', (1.0, 0.72, 0.2), 0.1, emit=(1.0, 0.6, 0.15), emit_s=4.0)
    for k, x in enumerate((-0.22, 0.0, 0.22)):
        p = O2 + Vector((x, 0, 0))
        T.plate('cmp_plate%d' % k, p, 0.12)
        if k == 0:
            for j in range(3):
                sl = T.add('cube', 'cmp_ts%d' % j, white, p + Vector((j * 0.02 - 0.02, 0, 0.016 + j * 0.005)), (0.05, 0.035, 0.005), (0.2, 0.1, 0.4 + j * 0.15))
                sl.modifiers.new('bv', 'BEVEL').width = 0.004
        elif k == 1:
            o = T.add('uv_sphere', 'cmp_chicken', chick, p + Vector((0, 0, 0.022)), (0.075, 0.045, 0.026), segments=48, ring_count=24)
        else:
            o = T.add('cylinder', 'cmp_pork', pork, p + Vector((0, 0, 0.022)), (0.08, 0.055, 0.012), vertices=48)
            T.add('cylinder', 'cmp_bone', T.mat('bone', (0.95, 0.9, 0.8), 0.5), p + Vector((-0.06, 0.0, 0.035)), (0.012, 0.012, 0.006), vertices=24)
        tb_ = T.lathe('tube%d' % k, [(0.0, 0.0), (0.035, 0.0), (0.035, 0.32), (0.032, 0.32), (0.032, 0.004), (0.0, 0.004)], 48, glass); tb_.location = p + Vector((0, 0.17, 0.0))
        lq = T.add('cylinder', 'liq%d' % k, liq, p + Vector((0, 0.17, 0.01)), (0.03, 0.03, 0.001), vertices=32)
        tubes.append(lq)
    return dict(tubes=tubes)
CMP = grab('compare', set_compare)

# ---------------- set 3: inside a blood vessel (x = 60)
O3 = Vector((60, 0, 0))
def set_vessel():
    vm = T.mat('vessel', (0.75, 0.15, 0.12), 0.45, sss=0.6, sss_r=(1, 0.2, 0.15), sss_s=0.05); T.bump(vm, 8, 0.4, 0.01)
    tube = T.lathe('vessel_wall', [(0.5, -1.0), (0.5, 12.0)], 64, vm); tube.location = O3; tube.rotation_euler = (math.radians(-90), 0, 0)
    for p in tube.data.polygons: p.flip()
    rbc = T.mat('rbc', (0.8, 0.08, 0.06), 0.35, sss=0.7, sss_r=(1, 0.2, 0.15), sss_s=0.02)
    amino = [T.mat('am%d' % k, c, 0.3, emit=c, emit_s=1.2) for k, c in enumerate([(0.4, 0.7, 1.0), (0.5, 1.0, 0.6), (0.9, 0.5, 1.0)])]
    gold = T.mat('trp', (1.0, 0.75, 0.2), 0.3, emit=(1.0, 0.7, 0.15), emit_s=6.0)
    parts = []
    random.seed(21)
    for k in range(70):
        kind = 'rbc' if k < 22 else ('trp' if k < 26 else 'am')
        if kind == 'rbc':
            o = T.add('torus', 'p%d' % k, rbc, (0, 0, 0), (1, 1, 0.55), major_radius=0.05, minor_radius=0.03)
        else:
            m = gold if kind == 'trp' else random.choice(amino); r = 0.028 if kind == 'trp' else random.uniform(0.018, 0.03)
            o = T.add('ico_sphere', 'p%d' % k, m, (0, 0, 0), (r, r, r), subdivisions=3)
        parts.append((o, kind, random.uniform(-0.38, 0.38), random.uniform(-0.38, 0.38), random.uniform(0, 11), random.uniform(0.15, 0.6), random.random() * 6))
    gate = T.add('torus', 'gate', T.mat('gate_m', (0.6, 0.85, 1.0), 0.3, emit=(0.5, 0.8, 1.0), emit_s=5.0), O3 + Vector((0, 9.0, 0)), (1, 1, 1), (math.pi / 2, 0, 0), major_radius=0.3, minor_radius=0.02)
    T.light('POINT', 'v_lt1', O3 + Vector((0, 2.0, 0.2)), O3, 40, (1.0, 0.8, 0.7), 0.3)
    T.light('POINT', 'v_lt2', O3 + Vector((0, 6.0, -0.2)), O3, 40, (1.0, 0.8, 0.7), 0.3)
    T.light('POINT', 'v_gate', O3 + Vector((0, 8.8, 0)), O3, 60, (0.5, 0.8, 1.0), 0.3)
    return dict(parts=parts)
VES = grab('vessel', set_vessel)

# ---------------- set 4: the stomach, x-ray style (x = 90)
O4 = Vector((90, 0, 0))
def set_stomach():
    sm = T.mat('stomach', (0.95, 0.55, 0.55), 0.35, trans=0.55, ior=1.35, sss=0.3, sss_r=(1, 0.3, 0.25), sss_s=0.05, coat=0.5, coat_r=0.1)
    T.bump(sm, 6, 0.35, 0.01)
    st = T.add('uv_sphere', 'stomach', sm, O4, (1, 1, 1), segments=64, ring_count=32)
    def f(x, y, z):            # bean / J shape
        bend = 0.35 * (z ** 2); return (x * 0.33 * (1 + 0.35 * z) + bend * 0.5 - 0.1, y * 0.24, z * 0.42)
    T.deform(st, f)
    T.add('cylinder', 'esoph', sm, O4 + Vector((0.02, 0, 0.55)), (0.05, 0.05, 0.2), (0, 0.25, 0), vertices=32)
    T.add('cylinder', 'duod', sm, O4 + Vector((0.32, 0, -0.25)), (0.045, 0.045, 0.15), (0, 1.2, 0), vertices=32)
    chunks = []
    cols = [(0.8, 0.6, 0.35), (0.95, 0.9, 0.75), (0.45, 0.25, 0.1), (0.3, 0.5, 0.15), (0.6, 0.05, 0.1)]
    random.seed(31)
    for k in range(40):
        m = T.mat('ch%d' % k, random.choice(cols), 0.5)
        r = random.uniform(0.025, 0.05)
        o = T.add('ico_sphere', 'chunk%d' % k, m, O4, (r, r * 0.8, r * 0.7), subdivisions=2)
        chunks.append((o, random.uniform(0, 6.28), random.uniform(0.05, 0.22), random.uniform(-0.25, 0.2), random.uniform(0.4, 1.2)))
    T.light('AREA', 'st_key', O4 + Vector((-1.0, -1.5, 1.0)), O4, 300, (1.0, 0.9, 0.85), 1.0)
    T.light('AREA', 'st_rim', O4 + Vector((1.2, 1.0, 0.5)), O4, 260, (0.5, 0.75, 1.0), 1.0)
    T.light('POINT', 'st_in', O4 + Vector((0, 0, 0)), O4, 30, (1.0, 0.6, 0.3), 0.2)
    streaks = []
    em = T.mat('energy', (1.0, 0.85, 0.3), 0.3, emit=(1.0, 0.75, 0.2), emit_s=12.0)
    for k in range(18):
        o = T.add('uv_sphere', 'en%d' % k, em, O4, (0.012, 0.012, 0.012), segments=12, ring_count=6)
        streaks.append((o, random.uniform(0, 6.28), random.uniform(-0.6, 0.6), random.random()))
    return dict(st=st, chunks=chunks, streaks=streaks)
STM = grab('stomach', set_stomach)

# ---------------- set 5: the living room couch (x = 120)
O5 = Vector((120, 0, 0))
def set_couch():
    fab = T.mat('couch', (0.42, 0.36, 0.3), 0.85, sheen=0.6); T.bump(fab, 400, 0.25, 0.0005, kind='voronoi')
    def box(n, loc, sc, m=fab):
        o = T.add('cube', n, m, O5 + Vector(loc), sc, smooth=False); bv = o.modifiers.new('bv', 'BEVEL'); bv.width = 0.05; bv.segments = 4; return o
    box('seat', (0, 0, 0.3), (0.9, 0.42, 0.1)); box('back', (0, 0.36, 0.62), (0.9, 0.12, 0.28)); box('armL', (-0.95, 0.0, 0.45), (0.1, 0.45, 0.22)); box('armR', (0.95, 0.0, 0.45), (0.1, 0.45, 0.22))
    for k, x in enumerate((-0.44, 0.44)): box('cush%d' % k, (x, -0.02, 0.46), (0.42, 0.38, 0.07))
    T.add('cube', 'base', T.mat('couchleg', (0.2, 0.12, 0.06), 0.5), O5 + Vector((0, 0, 0.12)), (0.95, 0.42, 0.08), smooth=False)
    pil = T.mat('pillow', (0.85, 0.5, 0.2), 0.8, sheen=0.5)
    p = T.add('uv_sphere', 'pillow', pil, O5 + Vector((-0.7, 0.18, 0.62)), (0.2, 0.08, 0.17), (0.2, 0, 0.3))
    blanket = T.mat('blanket', (0.75, 0.2, 0.12), 0.9, sheen=0.7); T.bump(blanket, 180, 0.3, 0.001)
    bl = T.add('plane', 'blanket', blanket, O5 + Vector((0.35, -0.1, 0.56)), (0.5, 0.42, 1), (0.25, 0, 0.15))
    sub = bl.modifiers.new('ss', 'SUBSURF'); sub.levels = sub.render_levels = 3
    tex = bpy.data.textures.new('fold', 'CLOUDS'); tex.noise_scale = 0.25; dsp = bl.modifiers.new('d', 'DISPLACE'); dsp.texture = tex; dsp.strength = 0.08
    floor = T.add('plane', 'lr_floor', T.mat('rug', (0.5, 0.42, 0.32), 0.95), O5, (4, 4, 1), smooth=False)
    T.add('plane', 'lr_wall', T.mat('lr_wall_m', (0.45, 0.4, 0.35), 0.9), O5 + Vector((0, 0.55, 1.3)), (3, 1.3, 1), (math.pi / 2, 0, 0), smooth=False)
    side = T.add('cylinder', 'sidetable', T.mat('st_wood', (0.35, 0.2, 0.1), 0.4), O5 + Vector((1.35, -0.1, 0.28)), (0.22, 0.22, 0.28), vertices=48)
    T.wine('lr_wine', O5 + Vector((1.3, -0.15, 0.56)))
    tv = T.add('plane', 'tvglow', T.emit_mat('tv', (0.55, 0.7, 1.0), 6.0), O5 + Vector((0.2, -4.4, 0.9)), (0.7, 0.4, 1), (math.radians(90), 0, math.radians(180)), smooth=False)
    lamp = T.light('AREA', 'lr_lamp', O5 + Vector((-1.4, -0.3, 1.5)), O5 + Vector((0, 0, 0.4)), 120, (1.0, 0.75, 0.45), 0.5)
    tvl = T.light('AREA', 'lr_tv', O5 + Vector((0.2, -4.2, 0.9)), O5 + Vector((0, 0, 0.5)), 220, (0.55, 0.7, 1.0), 1.2)
    return dict(lamp=lamp, tvl=tvl, tv=tv)
LR = grab('couch', set_couch)

cam = T.camera(30, 2.4)
focus = bpy.data.objects.new('focus', None); T.link(focus); cam.data.dof.focus_object = focus
T.render_setup(a.samples, a.scale)

# ---------------- per-frame state
def gravy(t, flow, tilt):
    """flow 0..1: stream reaching the mash; pool grows with how long it has poured"""
    gb = TB['gb']; hero = TB['hero']
    gb.rotation_euler = (0, math.radians(-12 - 30 * tilt), 0)
    spout = hero + Vector((-0.06, 0.02, 0.215 - 0.03 * tilt)); top_mash = hero + Vector((-0.02, 0.01, 0.065))
    st = TB['stream']
    if flow <= 0: st.hide_render = True; return
    st.hide_render = False
    end = spout.lerp(top_mash, min(1, flow))
    mid = (spout + end) / 2; d = end - spout
    st.location = mid; st.scale = (0.0065, 0.0065, d.length / 2)
    st.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

def frame(t):
    i, u, d = beat(t)
    k = u / d
    vis = {0: 'table', 1: 'table', 2: 'table', 3: 'compare', 4: 'vessel', 5: 'stomach', 6: 'couch', 7: 'table'}[i]
    for nm, objs in SETS.items():
        for o in objs: o.hide_render = nm != vis
    hero = TB['hero']
    # gravy: beat 7 starts the pour, beat 0 continues it, after that it has pooled
    pool = TB['pool']
    if i == 7:
        tilt = ease(k * 1.4); flow = max(0, (k - 0.45) / 0.55)
        gravy(t, flow, tilt); g = 0.0
    elif i == 0:
        gravy(t, 1.0, 1.0); g = ease(u / d)
    else:
        TB['stream'].hide_render = True; TB['gb'].rotation_euler = (0, math.radians(-12), 0); g = 1.0
    pool.hide_render = (g <= 0.01) or vis != 'table'
    r = lerp(0.012, 0.05, g); pool.scale = (r, r * 0.95, 0.004 + 0.004 * g); pool.location = hero + Vector((-0.02, 0.01, 0.062 - 0.012 * g))
    # after dinner: candles burn down, the clock runs an hour
    burn = {1: ease(k), 2: 1.0, 3: 1.0}.get(i, 0.0)
    for c, fl, lt in TB['tb']['candles']:
        if not hasattr(c, '_h0'): pass
        h0 = c.get('h0') or c.scale.z; c['h0'] = h0
        c.scale.z = h0 * (1 - 0.45 * burn); c.location.z = c.scale.z
        fl.location.z = 2 * c.scale.z + 0.022 + 0.003; lt.location.z = fl.location.z + 0.01
        fl.scale.z = 0.018 * (0.9 + 0.12 * math.sin(t * 13 + c.location.x * 40)); lt.data.energy = 1.6 * (0.85 + 0.15 * math.sin(t * 17 + c.location.x * 30))
    hrs = 6.0 + (ease(k) if i == 1 else (1.0 if i in (2,) else 0.0))
    for hand, frac, ln in ((TB['hh'], hrs / 12, 0.06), (TB['mh'], hrs % 1.0, 0.09)):
        ang = 2 * math.pi * frac; c = Vector((-0.7, hand.location.y, 1.35))
        hand.rotation_euler = (0, ang, 0); hand.location = c + Vector((math.sin(ang) * ln * 0.75, 0, math.cos(ang) * ln * 0.75))
    # compare: liquid fills
    if i == 3:
        for j, (lq, lvl) in enumerate(zip(CMP['tubes'], (0.55, 0.52, 0.85))):
            h = 0.3 * lvl * ease((u - 0.3 - 0.15 * j) / 1.6); lq.scale.z = max(0.001, h / 2); lq.location.z = 0.006 + h / 2
    # vessel: particles stream past, crowding the gold ones
    if i == 4:
        for o, kind, x, y, s0, sp, ph in VES['parts']:
            yy = (s0 + u * sp * (0.35 if kind == 'trp' else 1.0)) % 11.0 - 1.0
            wob = 0.03 * math.sin(t * 2 + ph)
            o.location = O3 + Vector((x + wob, yy, y + wob)); o.rotation_euler = (ph + t * 0.6, ph * 0.5 + t * 0.4, 0)
    # stomach: swells and churns
    if i == 5:
        sw = 1.0 + 0.18 * ease(k); STM['st'].scale = (sw, sw, sw)
        for o, a0, rr, zz, sp in STM['chunks']:
            ang = a0 + t * sp
            o.location = O4 + Vector((-0.05 + rr * math.cos(ang) * sw, rr * 0.6 * math.sin(ang) * sw, zz * sw + 0.03 * math.sin(t * 2 + a0)))
            o.rotation_euler = (t * sp, a0, t)
        for o, a0, zz, ph in STM['streaks']:
            q = (ph + u * 0.45) % 1.0; ang = a0
            o.location = O4 + Vector((math.cos(ang) * lerp(1.4, 0.35, q), math.sin(ang) * lerp(1.4, 0.3, q) - 0.2, zz * (1 - q)))
            s = 0.012 * (1 - q * 0.5); o.scale = (s, s, s)
    # couch: the room goes dark
    if i == 6:
        dim = ease((u - 1.5) / 3.0)
        LR['lamp'].data.energy = 120 * (1 - 0.92 * dim); LR['tvl'].data.energy = 220 * (1 - 0.85 * dim) * (0.85 + 0.15 * math.sin(t * 9))
    p, tgt, lens, foc, fs = cam_at(t)
    cam.location = p; T.look(cam, tgt); cam.data.lens = lens; focus.location = foc; cam.data.dof.aperture_fstop = fs

def cam_at(t):
    i, u, d = beat(t)
    k = u / d
    hero = TB['hero']
    if i in (0, 7):
        p0 = hero + Vector((0.3, -0.42, 0.3)); tg0 = hero + Vector((-0.04, 0.01, 0.11))
        if i == 7:
            q = ease(k); p = vlerp(hero + Vector((0.05, -0.55, 0.42)), p0, q); tg = vlerp(hero + Vector((0, 0.15, 0.1)), tg0, q)
            return p, tg, 45, tg0, 2.0
        p = vlerp(p0, hero + Vector((0.2, -0.3, 0.22)), ease(u / d)); return p + shake(t, 0.0008), tg0, 40, hero + Vector((-0.02, 0.01, 0.07)), 2.8
    if i == 1:
        p = vlerp((0.1, -0.95, 0.7), (-0.2, -1.3, 0.95), ease(k)); tg = vlerp((0, 0, 0.15), (-0.3, 0.6, 0.5), ease(k))
        return p, tg, 30, Vector((-0.3, 0.3, 0.2)), 3.5
    if i == 2:
        tk = TB['tb']['turkey'].location; ang = math.radians(-70 + 50 * ease(k))
        p = tk + Vector((0.85 * math.cos(ang), 0.85 * math.sin(ang), 0.45 - 0.05 * k)); return p, tk + Vector((0, 0, 0.04)), 34, tk, 2.8
    if i == 3:
        p = vlerp(O2 + Vector((0.0, -1.35, 0.75)), O2 + Vector((0.0, -1.2, 0.65)), ease(k)); tg = O2 + Vector((0, 0.08, 0.12))
        return p, tg, 26, O2 + Vector((0, 0.05, 0.1)), 5.6
    if i == 4:
        p = O3 + Vector((0.05 * math.sin(t * 0.7), u * 1.2 - 0.6, 0.04 * math.cos(t * 0.6))); return p, p + Vector((0.02, 1.0, 0.0)), 22, p + Vector((0, 1.0, 0)), 8.0
    if i == 5:
        p = vlerp(O4 + Vector((0.25, -2.4, 0.3)), O4 + Vector((0.12, -1.7, 0.15)), ease(k)); return p, O4 + Vector((0.0, 0, 0.02)), 40, O4, 5.6
    p = vlerp(O5 + Vector((1.1, -3.4, 1.2)), O5 + Vector((0.6, -2.6, 1.0)), ease(k)); return p, O5 + Vector((0.2, 0, 0.45)), 30, O5 + Vector((0, 0, 0.5)), 4.0

os.makedirs(a.out, exist_ok=True)
if a.still:
    for t in [float(x) for x in a.still.split(',')]:
        frame(t); S.render.filepath = os.path.join(a.out, 'still_%05.2f.png' % t); bpy.ops.render.render(write_still=True)
else:
    for f in range(a.f0, a.f1):
        frame(f / FPS); S.render.filepath = os.path.join(a.out, 'f_%05d.png' % f); bpy.ops.render.render(write_still=True)
        print('frame', f, flush=True)
