# ================================================================ per frame
def frame(f):
    t = f / FPS
    # keys at the frame before, this one and the next so motion blur is right both ways
    for i, mo in enumerate(MARB):
        if mo.animation_data: mo.animation_data_clear()
        for k in (-1, 0, 1):
            g = clamp(f + k, -PRE, NFR - 1) + PRE
            mo.location = tuple(SPOS[g, i]); mo.rotation_quaternion = tuple(SQUA[g, i])
            mo.keyframe_insert('location', frame=k); mo.keyframe_insert('rotation_quaternion', frame=k)
    S.frame_set(0)
    cp = Vector(tuple(CPOS[f])) + shake(t, 0.006, 2.0, 1.3); ct = Vector(tuple(CTGT[f]))
    look(cp, ct, float(CLEN[f]), fstop=16.0)
