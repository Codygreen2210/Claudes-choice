
# ================================================================ you: the MakeHuman man seen from his own eyes (head hidden, camera at the eyes)
with bpy.data.libraries.load(asset('man.blend'), link=False) as (_src, _dst):
    _dst.objects = [n for n in _src.objects if n.startswith('Human')]
for o in _dst.objects: S.collection.objects.link(o)
RIG = bpy.data.objects['Human.rig']; BODY = bpy.data.objects['Human']; SUIT = bpy.data.objects['Human.male_casualsuit06']
HEADBITS = [o for o in bpy.data.objects if o.name.startswith('Human.') and o not in (BODY, SUIT, RIG)]
for o in HEADBITS: o.hide_render = True                                 # hair, brows, lashes, eyes: never seen from inside the head
RB = RIG.data.bones; PB = RIG.pose.bones
for o in (BODY, SUIT):
    for md in o.modifiers:
        if md.type == 'ARMATURE': md.use_deform_preserve_volume = True
    for p_ in o.data.polygons: p_.use_smooth = True
sol = SUIT.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0035; sol.offset = 1.0
BODY.add_rest_position_attribute = True
# hide the head and neck (every vertex mostly weighted to neck01 or anything above it)
def _desc(bn):
    out = {bn}
    for c_ in RB[bn].children: out |= _desc(c_.name)
    return out
_HEADB = _desc('neck01'); _vgn = {g.index: g.name for g in BODY.vertex_groups}
_hw = np.zeros(len(BODY.data.vertices))
for v in BODY.data.vertices: _hw[v.index] = sum(g.weight for g in v.groups if _vgn[g.group] in _HEADB)
_keep = BODY.vertex_groups.new(name='fpv_keep'); _keep.add([i for i in range(len(_hw)) if _hw[i] < 0.35], 1.0, 'REPLACE')
_mk = BODY.modifiers.new('fpv_head', 'MASK'); _mk.vertex_group = 'fpv_keep'
subsurf(BODY, 1); subsurf(SUIT, 1)
def retint(m, col, keep=0.55, rough=0.85, sheen=0.35):
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); lk = next((l for l in nt.links if l.to_socket == b.inputs['Base Color']), None)
    src = lk.from_socket if lk else None
    bw = nt.nodes.new('ShaderNodeRGBToBW'); mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - keep; mr.inputs['To Max'].default_value = 1.0 + keep * 0.3
    if src: nt.links.new(src, bw.inputs['Color']); nt.links.new(bw.outputs['Val'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mul.inputs['A'])
    mul.inputs['B'].default_value = (*col, 1); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Tint'].default_value = (*col, 1)
    return m
SHORTS_M = SUIT.data.materials[0]; SHIRT_M = SHORTS_M.copy(); SHIRT_M.name = 'shirt'; SUIT.data.materials.append(SHIRT_M)
for p_ in SUIT.data.polygons:
    if sum(SUIT.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices) > 0.93: p_.material_index = 1
retint(SHORTS_M, (0.2, 0.25, 0.36), 0.35, 0.95, 0.6)
retint(SHIRT_M, (0.62, 0.2, 0.16), 0.35, 0.9, 0.5)                   # the channel's guy: brick-red tee

# ---- the cold-weather look: a quilted puffer sleeve shell (his own arm faces, pushed out, bending with him) and knit gloves painted on his hands
_ARMB = {b_ for s_ in ('L', 'R') for b_ in ('clavicle.' + s_, 'shoulder01.' + s_, 'upperarm01.' + s_, 'upperarm02.' + s_, 'lowerarm01.' + s_, 'lowerarm02.' + s_)}
_HANDB = set()
for s_ in ('L', 'R'): _HANDB |= _desc('wrist.' + s_)
def _wsum(v, names): return sum(g.weight for g in v.groups if _vgn.get(g.group, '') in names)
_aw = np.array([_wsum(v, _ARMB) for v in BODY.data.vertices]); _hd = np.array([_wsum(v, _HANDB) for v in BODY.data.vertices])
_wz = np.array([v.co.z for v in BODY.data.vertices])
_jf = [p_.index for p_ in BODY.data.polygons if np.mean(_aw[list(p_.vertices)]) > 0.5 and np.mean(_hd[list(p_.vertices)]) < 0.15 and np.mean(_wz[list(p_.vertices)]) < 1.36]
def _copy_faces(src, faces, name):
    bm = bmesh.new(); bm.from_mesh(src.data); keep = set(faces)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    for g in src.vertex_groups: o.vertex_groups.new(name=g.name)
    # vertex weights survive bmesh (deform layer); make sure the groups exist with the same names (done above)
    o.parent = src.parent; o.matrix_world = src.matrix_world.copy()
    md = o.modifiers.new('arm', 'ARMATURE'); md.object = RIG; md.use_deform_preserve_volume = True
    for p_ in me.polygons: p_.use_smooth = True
    return o
JACKET = _copy_faces(BODY, _jf, 'jacket')
_dsp = JACKET.modifiers.new('puff', 'DISPLACE'); _dsp.strength = 0.024; _dsp.mid_level = 0.0; _dsp.direction = 'NORMAL'
_sl = JACKET.modifiers.new('thick', 'SOLIDIFY'); _sl.thickness = 0.006; _sl.offset = -1.0
subsurf(JACKET, 1)
JACKET.add_rest_position_attribute = True
JACKET_M = mat('puffer', (0.03, 0.06, 0.14), 0.5, sheen=0.1, coat=0.2); _jn = JACKET_M.node_tree; _jb = _jn.nodes['Principled BSDF']
_ra = _jn.nodes.new('ShaderNodeAttribute'); _ra.attribute_name = 'rest_position'
_rx = sepz(_jn, _ra.outputs['Vector']); _cmb = _jn.nodes.new('ShaderNodeCombineXYZ')
_jn.links.new(math_(_jn, 'ABSOLUTE', _rx.outputs['X']), _cmb.inputs[0]); _jn.links.new(_rx.outputs['Y'], _cmb.inputs[1]); _jn.links.new(_rx.outputs['Z'], _cmb.inputs[2])
_vd = _jn.nodes.new('ShaderNodeVectorMath'); _vd.operation = 'DISTANCE'; _jn.links.new(_cmb.outputs[0], _vd.inputs[0]); _vd.inputs[1].default_value = (0.18, -0.017, 1.296)
_qs = math_(_jn, 'SINE', math_(_jn, 'MULTIPLY', _vd.outputs['Value'], 2 * math.pi / 0.075))          # quilting: a seam every 7.5 cm down the arm
_puff = math_(_jn, 'POWER', math_(_jn, 'ABSOLUTE', _qs), 0.35)
_jbm = _jn.nodes.new('ShaderNodeBump'); _jbm.inputs['Strength'].default_value = 0.6; _jbm.inputs['Distance'].default_value = 0.01
_jn.links.new(_puff, _jbm.inputs['Height']); _jn.links.new(_jbm.outputs['Normal'], _jb.inputs['Normal'])
_jcol = mixc(_jn, _puff, (0.008, 0.015, 0.04), (0.03, 0.06, 0.14)); _jn.links.new(_jcol, _jb.inputs['Base Color'])
JACKET.data.materials.append(JACKET_M)
GLOVE_M = mat('glove', (0.42, 0.08, 0.06), 0.9, sheen=0.8)                # red knit gloves
_gn = GLOVE_M.node_tree; _gb = _gn.nodes['Principled BSDF']
_gw = _gn.nodes.new('ShaderNodeTexWave'); _gw.inputs['Scale'].default_value = 140.0; _gw.inputs['Distortion'].default_value = 2.0
_gra = _gn.nodes.new('ShaderNodeAttribute'); _gra.attribute_name = 'rest_position'; _gn.links.new(_gra.outputs['Vector'], _gw.inputs['Vector'])
_gbm = _gn.nodes.new('ShaderNodeBump'); _gbm.inputs['Strength'].default_value = 0.5; _gbm.inputs['Distance'].default_value = 0.002
_gn.links.new(_gw.outputs['Fac'], _gbm.inputs['Height']); _gn.links.new(_gbm.outputs['Normal'], _gb.inputs['Normal'])
_gn.links.new(mixc(_gn, _gw.outputs['Fac'], (0.3, 0.05, 0.04), (0.5, 0.1, 0.07)), _gb.inputs['Base Color'])
BODY.data.materials.append(GLOVE_M); _GLOVE_I = len(BODY.data.materials) - 1
_mi0 = np.zeros(len(BODY.data.polygons), np.int32); BODY.data.polygons.foreach_get('material_index', _mi0)
_glove_f = np.array([np.mean(_hd[list(p_.vertices)]) > 0.5 for p_ in BODY.data.polygons])
_mi1 = np.where(_glove_f, _GLOVE_I, _mi0).astype(np.int32)
COLD = [False]
def dress(cold):
    """cold: puffer sleeves on, gloves on; warm: tee and bare hands"""
    if COLD[0] != cold or cold is None: BODY.data.polygons.foreach_set('material_index', _mi1 if cold else _mi0); BODY.data.update()
    COLD[0] = cold; JACKET.hide_render = (not cold) or BODY.hide_render
dress(None); dress(False)
FROST_SLEEVE = None                                                  # filled in by the frost part (the sleeve and gloves frost over)

# ---- rig controls (from crush/60_pose.py): IK to the wrists, wrist turned by a Copy Rotation, fingers by curl
def ik(bone, target, pole, chain, pole_angle=R(-90)):
    c = PB[bone].constraints.new('IK'); c.target = target; c.pole_target = pole; c.chain_count = chain; c.pole_angle = pole_angle; c.use_tail = True; return c
TGT = {k: empty('tgt_' + k) for k in ('ankR', 'ankL', 'poleR', 'poleL', 'handR', 'handL', 'poleArmR', 'poleArmL')}
for s_ in ('R', 'L'):
    ik('lowerleg02.' + s_, TGT['ank' + s_], TGT['pole' + s_], 4)
    for bn in ('lowerleg02.', 'upperleg02.'):
        pb = PB[bn + s_]; pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = True
    ik('lowerarm02.' + s_, TGT['hand' + s_], TGT['poleArm' + s_], 4)
RIG.rotation_mode = 'XYZ'
def _hand_frame(side):
    b = RB; d = (b['finger3-1.' + side].head_local - b['wrist.' + side].head_local).normalized()
    n = b['finger3-1.' + side].matrix_local.to_3x3().col[2]; n = (n - d * n.dot(d)).normalized()
    return Matrix((d.cross(n), d, n)).transposed()
HAND = {}
for s_ in ('R', 'L'):
    Hr = _hand_frame(s_); Wr = RB['wrist.' + s_].matrix_local.to_3x3()
    e_ = empty('tgt_rot' + s_); e_.rotation_mode = 'QUATERNION'
    c_ = PB['wrist.' + s_].constraints.new('COPY_ROTATION'); c_.target = e_; c_.owner_space = c_.target_space = 'WORLD'; c_.influence = 0.0
    HAND[s_] = (Hr.transposed() @ Wr, e_, c_)
def hand_quat(s_, fdir, pdir):
    O, e_, c_ = HAND[s_]; d = Vector(fdir).normalized(); n = Vector(pdir); n = (n - d * n.dot(d)).normalized(); a_ = d.cross(n)
    return (Matrix((a_, d, n)).transposed() @ O).to_quaternion()
def rot(bn, x=0.0, y=0.0, z=0.0):
    pb = PB[bn]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R(x), R(y), R(z))
def fingers(s_, curl, spread=0.0, thumb=None):
    for f_ in range(1, 6):
        for seg in (1, 2, 3):
            nm = f'finger{f_}-{seg}.{s_}'
            if nm in PB:
                c__ = (thumb if thumb is not None else curl) if f_ == 1 else curl
                ang = (10, 15, 8)[seg - 1] if f_ == 1 else (40, 55, 30)[seg - 1]; rot(nm, ang * c__, 0, (f_ - 3) * spread * (1 if seg == 1 else 0))
def wpos(bn, tail=False):
    pb = PB[bn]; return RIG.matrix_world @ (pb.tail if tail else pb.head)
HIP0 = (RB['upperleg01.R'].head_local + RB['upperleg01.L'].head_local) * 0.5
EYE0 = (RB['eye.L'].head_local + RB['eye.R'].head_local) * 0.5
PALM_D = 0.068; PALM_T = 0.013
def place_hand(s_, contact, fdir, pdir, w_rot=1.0):
    """middle of his palm on 'contact', fingers along fdir, palm facing pdir"""
    d = Vector(fdir).normalized(); n = Vector(pdir); n = (n - d * n.dot(d)).normalized()
    TGT['hand' + s_].location = Vector(contact) - n * PALM_T - d * PALM_D
    O, e_, c_ = HAND[s_]; c_.influence = w_rot; e_.rotation_quaternion = hand_quat(s_, d, n)
def palm_point(s_):
    """world middle of the palm and its frame (fingers d, palm normal n) from the posed bones"""
    w = wpos('wrist.' + s_); f3 = wpos('finger3-1.' + s_); d = (f3 - w).normalized()
    M_ = (RIG.matrix_world @ PB['finger3-1.' + s_].matrix).to_3x3(); n = M_.col[2]; n = (n - d * n.dot(d)).normalized()
    return w + d * PALM_D + n * PALM_T, d, n

# ---- first person: put him so his eyes sit at the camera, facing where the camera faces (heading only); hands in camera space
def cam_axes():
    M_ = CAM.rotation_quaternion.to_matrix(); return M_.col[0], M_.col[1], -M_.col[2]          # right, up, forward
def cam_pt(x, y, z):
    """camera space (x right, y up, z forward, metres) -> world"""
    r_, u_, f_ = cam_axes(); return CAM.location + r_ * x + u_ * y + f_ * z
def cam_dir(x, y, z):
    r_, u_, f_ = cam_axes(); return (r_ * x + u_ * y + f_ * z).normalized()
HANDS_DOWN = {'R': None, 'L': None}
def fpv(spine=0.0, eye_back=0.04, hide=False):
    """place the body under the camera. eye_back: the camera sits this far in front of the eyes (inside the hidden head)"""
    for o in (BODY, SUIT): o.hide_render = hide
    JACKET.hide_render = hide or not COLD[0]
    if hide: return
    r_, u_, f_ = cam_axes(); fh = Vector((f_.x, f_.y, 0)).normalized()
    th = math.atan2(fh.x, -fh.y); RIG.rotation_euler = (0, 0, th)
    RIG.location = Vector((0, 0, 0)); bpy.context.view_layer.update()
    for n, k in (('spine03', 0.3), ('spine02', 0.35), ('spine01', 0.35)): rot(n, spine * k)
    eye = RIG.matrix_world @ EYE0; RIG.location = CAM.location - fh * eye_back - (eye - RIG.location) + Vector((0, 0, 0))
    bpy.context.view_layer.update()
    hipw = RIG.matrix_world @ HIP0; rt = Vector((math.cos(th), math.sin(th), 0))
    for s_, sg in (('R', -1), ('L', 1)):                                # feet under the hips (never seen, keeps the legs calm)
        TGT['ank' + s_].location = hipw + rt * (0.11 * sg) - Vector((0, 0, 0.82)) - fh * 0.02
        TGT['pole' + s_].location = hipw + rt * (0.11 * sg) - Vector((0, 0, 0.4)) + fh * 0.6
    for s_, sg in (('R', -1), ('L', 1)): TGT['poleArm' + s_].location = hipw + rt * (0.7 * sg) - fh * 0.35 + Vector((0, 0, 0.1))
def arm_down(s_):
    """a relaxed arm hanging at his side, out of the shot"""
    O, e_, c_ = HAND[s_]; c_.influence = 0.0; sg = -1 if s_ == 'R' else 1
    th = RIG.rotation_euler.z; rt = Vector((math.cos(th), math.sin(th), 0)); fh = Vector((-math.sin(th), math.cos(th), 0)) * -1
    TGT['hand' + s_].location = (RIG.matrix_world @ HIP0) + rt * (0.24 * sg) + Vector((0, 0, -0.02)) + fh * 0.05
    fingers(s_, 0.3)
