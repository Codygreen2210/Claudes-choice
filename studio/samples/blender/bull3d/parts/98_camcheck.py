# ================================================================ CAMCHECK=1: fly the camera through every frame and report any frame where it comes within 6 cm of a prop's box
if os.environ.get('CAMCHECK'):
    N_ = int(round(TOTAL * FPS)); skip = ('hfloor', 'hback', 'hfront', 'hleft', 'hright', 'hceil', 'hwains', 'hrail', 'rail')
    hits = {}
    for f in range(N_):
        frame(f); cp = CAM.matrix_world.translation
        for o in S.objects:
            if o.type not in ('MESH', 'FONT') or o.name in skip or o.name.startswith('beam') or o.hide_render: continue
            if o.matrix_world.translation.z < -20: continue
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))); hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
            if all(lo[i] - 0.06 < cp[i] < hi[i] + 0.06 for i in range(3)): hits.setdefault(o.name, []).append(f)
    for k_, v_ in hits.items(): print('CAMHIT', k_, v_[0], v_[-1], len(v_))
    print('CAMCHECK done', len(hits)); sys.exit(0)
