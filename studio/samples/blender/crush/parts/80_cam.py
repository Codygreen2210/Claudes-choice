def look(cp, ct, lens=35, fstop=8.0, focus=None, roll=0.0, up=None):
    CAM.location = cp; d = Vector(ct) - Vector(cp); CAM.rotation_mode = 'QUATERNION'
    q = d.to_track_quat('-Z', 'Y')
    if up is not None:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x); q = Matrix((x, y, z)).transposed().to_quaternion()
    if roll: q = q @ Quaternion((0, 0, 1), roll)
    CAM.rotation_quaternion = q; CAM.data.lens = lens; CAM.data.dof.aperture_fstop = fstop
    CAM.data.dof.focus_distance = (Vector(focus) - Vector(cp)).length if focus is not None else d.length
def shake(t, amt, seed=0.0): return Vector((wob(t, 7.0, seed), wob(t, 7.0, seed + 3.3), wob(t, 7.0, seed + 6.1))) * amt
def eval_centroid(o, idx=None):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    vs = me.vertices if idx is None else [me.vertices[i] for i in idx]; c = sum((oe.matrix_world @ v.co for v in vs), Vector()) / len(vs); oe.to_mesh_clear(); return c
def ease(a_, b_, k): return a_.lerp(b_, sm(clamp(k, 0, 1)))
