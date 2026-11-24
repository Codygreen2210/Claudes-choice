# ================================================================ moving bits: sea spray, rain, the Gjermundbu pieces' flight paths, the helmet knocked off
GA = random.Random(21)
M_SPRAY = mat('spray', (0.70, 0.76, 0.80), 0.3, emit=(0.45, 0.52, 0.6), estr=0.15, alpha=0.75); M_SPRAY.blend_method = 'BLEND'
M_PUFF = mat('puff', (0.75, 0.80, 0.83), 0.9); nt_ = M_PUFF.node_tree; M_PUFF.blend_method = 'BLEND'
lw_ = nt_.nodes.new('ShaderNodeLayerWeight'); lw_.inputs['Blend'].default_value = 0.5
soft_ = math_(nt_, 'POWER', math_(nt_, 'SUBTRACT', 1.0, lw_.outputs['Facing']), 2.5)
nt_.links.new(math_(nt_, 'MULTIPLY', objattr(nt_, 'a'), soft_), nt_.nodes['Principled BSDF'].inputs['Alpha'])
SPRAY = []                                                         # (obj, p0, v, t0, kind)
for k in range(700):
    u = GA.uniform(0.22, 0.52); p0 = hull_pt(u, 1.0, 1, 0.05) + Vector((0, GA.uniform(0.0, 0.25), GA.uniform(-0.05, 0.25)))
    v = Vector((GA.gauss(0.2, 0.5), -GA.uniform(1.0, 3.4), GA.uniform(1.2, 3.4))); t0 = GA.uniform(-0.12, 0.55)
    o = prim('ico_sphere', f'spr{k}', M_SPRAY, None, loc=(0, 0, -50), subdivisions=1, radius=GA.uniform(0.0025, 0.007)); o.rotation_mode = 'QUATERNION'; SPRAY.append((o, p0, v, t0, 0))
for k in range(40):
    u = GA.uniform(0.22, 0.52); p0 = hull_pt(u, 1.0, 1, 0.05) + Vector((0, GA.uniform(0.0, 0.2), GA.uniform(0.0, 0.3)))
    v = Vector((GA.gauss(0.2, 0.3), -GA.uniform(0.6, 1.8), GA.uniform(0.8, 2.2))); t0 = GA.uniform(0.0, 0.5)
    o = prim('ico_sphere', f'puff{k}', M_PUFF, None, loc=(0, 0, -50), subdivisions=2, radius=GA.uniform(0.06, 0.14)); o['a'] = 0.0; SPRAY.append((o, p0, v, t0, 1))
M_RAIN = emis_mix('rain', (0.7, 0.78, 0.9), 0.22, 'a')
RAIN = []
for k in range(240):
    o = box(f'rain{k}', (0.0022, 0.0022, 0.13), (0, 0, -50), M_RAIN); o['a'] = 0.0; o.rotation_euler = (R(8), R(-6), 0)
    RAIN.append((o, Vector((GA.uniform(-2.3, 2.3), GA.uniform(-0.1, 3.9), 0)), GA.uniform(0, 4.0), GA.uniform(6.5, 8.5)))
# the Gjermundbu helmet: assembled on the stand; each piece starts in the grave (offset from its place, turned) and flies home in turn
GJR, GJP = gjermundbu('a', M_RUST, iron_mat('rustdk', 0.6, base=(0.04, 0.035, 0.03), seed=6.0, rust_col=(0.09, 0.04, 0.02)))
GJR.location = GJ_TOP
GJ_REST = {nm: (o.location.copy(), o.rotation_euler.copy()) for nm, o in GJP.items()}
GJ_ORDER = ['brow', 'plate0', 'plate1', 'plate2', 'plate3', 'band0', 'band1', 'spike', 'spect']
GJ_FROM = {}
for k, nm in enumerate(GJ_ORDER):
    gp = Vector((GX - 0.75 + 1.5 * GA.random(), 2.35 + 0.4 * GA.random(), PLAT_Z + 0.05)) - GJ_TOP          # a spot in the grave
    eu = Vector((GA.uniform(-2.2, 2.2), GA.uniform(-1.4, 1.4), GA.uniform(-3, 3)))
    GJ_FROM[nm] = (gp, eu, 0.15 + 0.3 * k, 0.75)
# the test helmet knocked off the head: it tumbles once and a bit round HAXIS and lands at rest on its rim and one horn
TI = B[4] + 0.55; HV = Vector((-1.0, -0.5, 1.4)); HAXIS = Vector((0.12, 1.0, 0.08)).normalized()
HELM2.location = (0, 0, 0); HELM2.rotation_quaternion = (1, 0, 0, 0); bpy.context.view_layer.update()
H2V_HORN, H2V_BODY = [], []
for o in HELM2.children_recursive:
    if o.type != 'MESH': continue
    mw_ = o.matrix_world
    (H2V_HORN if '_horn' in o.name else H2V_BODY).extend(mw_ @ v.co for v in o.data.vertices)
H2V_ALL = H2V_HORN + H2V_BODY
def h2_minz(q, vs): return min((q @ v).z for v in vs)
best_ = None
for a_ in range(70, 135):
    q_ = Quaternion(HAXIS, R(a_)); zh, zb = h2_minz(q_, H2V_HORN), h2_minz(q_, H2V_BODY)
    sc_ = abs(zh - zb)
    if best_ is None or sc_ < best_[0]: best_ = (sc_, a_, min(zh, zb))
H2_A = R(best_[1]); H2_Z = PLAT_Z - best_[2] + 0.002                 # final roll angle and root height at rest
QF = Quaternion(HAXIS, H2_A)
_a, _b, _c = -4.9, HV.z, HELM2_P0.z - H2_Z
T_LAND = (-_b - math.sqrt(_b * _b - 4 * _a * _c)) / (2 * _a)
HW = (H2_A + 2 * math.pi) / T_LAND
HELM2.location = HELM2_P0
print('helm2 rest angle', best_[1], 'gap', round(best_[0], 4), 'land after', round(T_LAND, 3), 'land x', round(HELM2_P0.x + HV.x * T_LAND, 2))
def helm2_pose(t):
    tau = t - TI
    if tau <= 0: return HELM2_P0.copy(), Quaternion()
    if tau < T_LAND:
        p_ = HELM2_P0 + HV * tau + Vector((0, 0, -4.9 * tau * tau)); q_ = Quaternion(HAXIS, HW * tau)
        p_.z = max(p_.z, PLAT_Z + 0.002 - h2_minz(q_, H2V_ALL)); return p_, q_          # never through the platform
    d_ = tau - T_LAND; xy_ = HELM2_P0 + HV * T_LAND + Vector((HV.x, HV.y, 0)) * 0.12 * (1 - math.exp(-d_ * 8))
    bounce = 0.05 * abs(math.sin(d_ * 18)) * math.exp(-d_ * 9); wob_ = 0.12 * math.sin(d_ * 22) * math.exp(-d_ * 7)
    q_ = Quaternion(HAXIS, H2_A + wob_)
    return Vector((xy_.x, xy_.y, PLAT_Z + 0.002 - h2_minz(q_, H2V_ALL) + bounce)), q_
