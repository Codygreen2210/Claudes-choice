
# ================================================================ the sperm whale (about 15 m): a huge square head a third of its length, wrinkled
# dark skin, a thin under-slung lower jaw lined with teeth that drops open, and a throat wide enough to take a giant squid whole (shown in x-ray).
# Same local frame as the humpback: snout at x = 0 facing +x.
SW_L = 15.0
SW_TAB = [  # s,   ry,   top,   bottom   (the head: a tall square block a third of the body; the body behind it lower and narrower)
    (0.000, 0.95, 1.55, -1.20), (0.012, 1.10, 1.85, -1.38), (0.050, 1.20, 2.00, -1.48), (0.180, 1.25, 2.05, -1.52), (0.300, 1.28, 1.95, -1.55),
    (0.360, 1.26, 1.60, -1.52), (0.440, 1.24, 1.32, -1.45), (0.560, 1.10, 1.20, -1.30), (0.660, 0.88, 1.08, -1.06), (0.760, 0.60, 0.92, -0.84),
    (0.860, 0.35, 0.68, -0.58), (0.940, 0.20, 0.42, -0.37), (1.000, 0.08, 0.14, -0.14)]
SW_HINGE = 0.30
def build_sperm(name, mskin, mmouth, mteeth, mthroat):
    root = empty(name + '_root'); L = SW_L; NS, NA = 100, 56
    ss = [(0.5 * (1 - math.cos(math.pi * i / (NS - 1)))) ** 1.1 for i in range(NS)]
    vs = []; fs = []
    for s in ss:
        ry, zt, zb = (interp_tab(SW_TAB, s, k) for k in (1, 2, 3)); zc = (zt + zb) / 2
        ex = lerp(0.22, 0.85, smooth(0.28, 0.45, s))                    # boxy head, round body
        bump = 0.05 * math.sin(s * 70) * smooth(0.5, 0.7, s) * (1 - smooth(0.85, 0.95, s))   # the knuckles on the back
        for k in range(NA):
            th = 2 * math.pi * k / NA; c_, s_ = math.cos(th), math.sin(th)
            y_ = ry * (abs(c_) ** ex) * (1 if c_ >= 0 else -1)
            z_ = zc + (zt - zc + (bump if s_ > 0.9 else 0)) * (abs(s_) ** ex) * (1 if s_ >= 0 else -1) if s_ >= 0 else zc - (zc - zb) * (abs(s_) ** ex)
            vs.append((-s * L, y_, z_))
    for i in range(NS - 1):
        for k in range(NA): k2 = (k + 1) % NA; fs.append((i * NA + k, i * NA + k2, (i + 1) * NA + k2, (i + 1) * NA + k))
    vs.append((0.03, 0, 0.0)); tip = len(vs) - 1
    for k in range(NA): fs.append((tip, (k + 1) % NA, k))
    tl = len(vs); vs.append((-L - 0.02, 0, 0.0))
    for k in range(NA): fs.append(((NS - 1) * NA + k, (NS - 1) * NA + (k + 1) % NA, tl))
    body = mesh(name + '_body', vs, fs, mskin, root); subsurf(body, 1)
    # the dorsal hump
    s0 = 0.62; zt0 = interp_tab(SW_TAB, s0, 2)
    hump = tube(name + '_hump', [(-s0 * L + 0.6, 0, zt0 - 0.1), (-s0 * L, 0, zt0 + 0.25), (-s0 * L - 0.7, 0, zt0 - 0.05)], lambda u: 0.3 * math.sin(math.pi * min(max(u, 0.05), 0.95)), mskin, root, seg=12)
    # lower jaw: a narrow rod under the head, teeth along its top, on a hinge
    jpiv = empty(name + '_jawpiv', root, loc=(-SW_HINGE * L, 0, -1.30))
    n = 40; jv = []; jf = []
    for i in range(n):
        u = i / (n - 1); x_ = SW_HINGE * L - u * (SW_HINGE * L - 0.45); w = lerp(0.42, 0.20, u); h_ = lerp(0.36, 0.20, u)
        for (yy, zz) in ((-w, 0.0), (-w * 0.9, -h_ * 0.7), (0.0, -h_), (w * 0.9, -h_ * 0.7), (w, 0.0), (0.0, 0.06)):
            jv.append((x_, yy, zz))
    for i in range(n - 1):
        for k in range(6): k2 = (k + 1) % 6; jf.append((i * 6 + k, i * 6 + k2, (i + 1) * 6 + k2, (i + 1) * 6 + k))
    jf.append(tuple(range(6))[::-1]); jf.append(tuple((n - 1) * 6 + k for k in range(6)))
    jaw = mesh(name + '_jaw', jv, jf, mskin, jpiv); jaw.location = (0, 0, 0); subsurf(jaw, 1)
    teeth = []
    for side in (1, -1):
        for j in range(22):
            u = 0.06 + 0.88 * j / 21; x_ = SW_HINGE * L - u * (SW_HINGE * L - 0.45); w = lerp(0.42, 0.20, u) * 0.7
            tt = prim('cone', f'{name}_tooth{side}_{j}', mteeth, jpiv, loc=(x_, side * w, 0.11), radius1=0.045, radius2=0.004, depth=0.18, vertices=10)
            tt.rotation_euler = (side * R(-10), 0, 0); teeth.append(tt)
    # the upper mouth: a pale groove under the head where the jaw closes into
    gr = box(name + '_groove', (SW_HINGE * L - 0.5, 0.55, 0.06), (-(SW_HINGE * L) / 2 - 0.2, 0, -1.30), mmouth, bv=0.02, parent=root)
    # the throat ring (x-ray only): big enough for a person
    thr = prim('cylinder', name + '_throat', mthroat, root, loc=(-SW_HINGE * L - 0.5, 0, -0.6), radius=0.55, depth=0.08, vertices=40)
    thr.rotation_euler = (0, R(90), 0); thr.hide_render = True
    # flippers (small) and flukes
    fins = []
    for side in (1, -1):
        piv = empty(f'{name}_fpiv{side}', root, loc=(-0.36 * L, side * 1.2, -1.0))
        fo = tube(f'{name}_flip{side}', [(0, 0, 0), (-0.4, side * 0.6, -0.25), (-0.9, side * 1.0, -0.45)], lambda u: 0.32 * (1 - 0.75 * u), mskin, piv, seg=10)
        fo.scale = (1, 1, 0.35); fins.append(piv)
    fpiv = empty(name + '_flukepiv', root, loc=(-L + 0.1, 0, 0))
    fv = []; ff = []; n = 24
    for side in (1, -1):
        b0 = len(fv)
        for i in range(n):
            u = i / (n - 1); span = 2.2 * u; chord = lerp(1.1, 0.25, u ** 1.3); th = lerp(0.14, 0.03, u)
            for (cx, cz) in [(0.0, 0.0), (-0.3, th * 0.5), (-1.0, 0.0), (-0.3, -th * 0.5)]:
                fv.append((-0.5 * u ** 1.4 + cx * chord + 0.25, side * (0.05 + span), cz))
        for i in range(n - 1):
            for k in range(4):
                k2 = (k + 1) % 4; q_ = (b0 + i * 4 + k, b0 + i * 4 + k2, b0 + (i + 1) * 4 + k2, b0 + (i + 1) * 4 + k); ff.append(q_ if side > 0 else q_[::-1])
    flukes = mesh(name + '_flukes', fv, ff, mskin, fpiv); subsurf(flukes, 1)
    # eye
    eyes = [prim('uv_sphere', f'{name}_eye{s_}', mat('sw_eye', (0.01, 0.01, 0.01), 0.05, coat=1.0), root, loc=(-0.36 * L, s_ * 1.2, -0.95), radius=0.06, segments=12, ring_count=8) for s_ in (1, -1)]
    body.shape_key_add(name='Basis'); ku = body.shape_key_add(name='tail_up')
    for i, v in enumerate(body.data.vertices): ku.data[i].co = v.co + Vector((0, 0, tail_bend(-v.co.x / L)))
    return dict(root=root, body=body, jaw=jaw, jpiv=jpiv, teeth=teeth, throat=thr, fins=fins, fpiv=fpiv, flukes=flukes, L=L)

SWSKIN = mat('sw_skin', (0.075, 0.068, 0.064), 0.45, coat=0.2); nt = SWSKIN.node_tree; b_ = nt.nodes['Principled BSDF']; co = coord(nt, 'Object')
wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 3.0; wv.inputs['Distortion'].default_value = 7.0
wv.inputs['Detail'].default_value = 4.0; nt.links.new(co, wv.inputs['Vector'])
bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.45; bp.inputs['Distance'].default_value = 0.04
nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b_.inputs['Normal'])
nt.links.new(mixc(nt, math_(nt, 'MULTIPLY', ramp_v(nt, tnoise(nt, co, 1.2, 6.0), 0.4, 0.7), 0.5), (0.075, 0.068, 0.064), (0.16, 0.15, 0.14)), b_.inputs['Base Color'])
xray_mix(SWSKIN, (0.45, 0.8, 1.0))
SWMOUTH = mat('sw_mouth', (0.78, 0.74, 0.70), 0.5); xray_mix(SWMOUTH)
SWTEETH = mat('sw_teeth', (0.92, 0.9, 0.84), 0.3, coat=0.5); xray_mix(SWTEETH)
THROATM = emis_mix('throat_glow', (1.0, 0.85, 0.3), 6.0, 'alpha')
SW = build_sperm('sw', SWSKIN, SWMOUTH, SWTEETH, THROATM)

def sperm_set(loc, yaw=0.0, pitch=0.0, roll=0.0, jaw=0.0, tail=0.0, xr=0.0, throat=0.0):
    r_ = SW['root']; r_.location = loc; r_.rotation_mode = 'XYZ'; r_.rotation_euler = (roll, -pitch, yaw)
    SW['jpiv'].rotation_euler = (0, R(62) * jaw, 0)
    SW['body'].data.shape_keys.key_blocks['tail_up'].slider_min = -1.0; SW['body'].data.shape_keys.key_blocks['tail_up'].value = tail
    tb = tail_bend(1.0) * tail; ang = math.atan(tail_slope(0.985) * tail)
    SW['fpiv'].location = (-SW_L + 0.1, 0, tb); SW['fpiv'].rotation_euler = (0, -ang * 1.4, 0)
    for o in SW['root'].children_recursive:
        if o.type == 'MESH': o['xr'] = xr
    SW['throat'].hide_render = throat < 0.03; SW['throat']['alpha'] = throat
def sperm_show(on):
    for o in [SW['root']] + list(SW['root'].children_recursive):
        if o.type == 'MESH': o.hide_render = not on or (o is SW['throat'] and o.hide_render)

# ================================================================ the giant squid (about 10 m with its feeding tentacles): a red mantle with fins,
# big eyes, eight arms and two long tentacles that curl
SQM = mat('squid', (0.55, 0.12, 0.08), 0.35, coat=0.6, sheen=0.3); noisy(SQM, 8.0, 0.35, 0.1); xray_mix(SQM, (1.0, 0.6, 0.4))
SQ = empty('squid_root')
SQ_MANTLE = lathe('squid_mantle', [(0.01, 2.4), (0.18, 2.3), (0.32, 2.0), (0.38, 1.4), (0.36, 0.6), (0.30, 0.15), (0.26, 0.0)], 24, SQM, SQ)
SQ_MANTLE.rotation_euler = (0, R(90), 0)                                  # mantle points +x
for s_ in (1, -1):
    fn = prim('uv_sphere', f'squid_fin{s_}', SQM, SQ, loc=(2.05, s_ * 0.28, 0), radius=0.35, segments=12, ring_count=8); fn.scale = (1.0, 0.9, 0.12)
SQ_HEAD = prim('uv_sphere', 'squid_head', SQM, SQ, loc=(-0.15, 0, 0), radius=0.3, segments=16, ring_count=10); SQ_HEAD.scale = (1.0, 1.05, 0.95)
for s_ in (1, -1):
    prim('uv_sphere', f'squid_eye{s_}', mat('squid_eye', (0.02, 0.02, 0.03), 0.05, coat=1.0), SQ, loc=(-0.15, s_ * 0.26, 0.05), radius=0.12, segments=14, ring_count=8)
SQ_ARMS = []
for j in range(10):
    a_ = 2 * math.pi * j / 10; ln = 6.0 if j in (2, 7) else 2.0
    SQ_ARMS.append((tube(f'squid_arm{j}', [(-0.3 - ln * k / 15, 0.15 * math.cos(a_), 0.15 * math.sin(a_)) for k in range(16)], lambda u: 0.07 * (1 - 0.85 * u) + 0.008, SQM, SQ, seg=8), a_, ln))
for o, a_, ln in SQ_ARMS: o['a'] = a_; o['ln'] = ln
def squid_set(loc, rot, t, curl=1.0, xr=0.0, scale=1.0):
    SQ.location = loc; SQ.rotation_mode = 'XYZ'; SQ.rotation_euler = rot; SQ.scale = (scale,) * 3
    for o, a_, ln in SQ_ARMS:
        co = []; n = 16
        for k in range(n):
            u = k / (n - 1); r0 = 0.15 + 0.25 * u * curl
            ang = a_ + 0.6 * curl * u * math.sin(t * 2.2 + a_ * 3)
            p = Vector((-0.3 - ln * u * (1 - 0.25 * curl * u), r0 * math.cos(ang), r0 * math.sin(ang)))
            p += Vector((0, 0.25 * u * u * math.sin(t * 3.1 + a_ * 2 + u * 4), 0.25 * u * u * math.cos(t * 2.7 + a_ * 2 + u * 4))) * curl
            co.append(p)
        rebuild_tube(o, co, lambda u: 0.07 * (1 - 0.85 * u) + 0.008, 8)
    for o in [SQ] + list(SQ.children_recursive):
        if o.type == 'MESH': o['xr'] = xr
def squid_show(on):
    for o in SQ.children_recursive:
        if o.type == 'MESH': o.hide_render = not on
def rebuild_tube(o, pts, r, seg):
    pts = [Vector(p) for p in pts]; n = len(pts); T0 = (pts[1] - pts[0]).normalized()
    up = Vector((0, 0, 1)) if abs(T0.z) < 0.9 else Vector((1, 0, 0)); Nn = T0.cross(up).normalized(); co = []
    for i in range(n):
        T = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized(); Nn = (Nn - T * Nn.dot(T)).normalized(); Bn = T.cross(Nn)
        rr = r(i / (n - 1))
        for k in range(seg): co.extend(pts[i] + (Nn * math.cos(2 * math.pi * k / seg) + Bn * math.sin(2 * math.pi * k / seg)) * rr)
    o.data.vertices.foreach_set('co', co); o.data.update()
