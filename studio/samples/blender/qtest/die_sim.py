# Real physics for the die (Blender rigid bodies / Bullet). Small objects simulate badly at true size, so the toss runs at
# 10x scale with 10x gravity (same timing), then everything is scaled back. The die is thrown across the table with spin,
# bounces, tumbles and settles on its own. Writes die_path.json: 120 samples a second of position + rotation, plus every
# moment it hits the table (time, impact speed in m/s) so the sound lands on the real hits.
#   python3 die_sim.py OUT.json [--seed N] [--try K]     (--try runs K seeds and keeps the best-looking toss)
import sys, os, math, json, argparse, random
import bpy, bmesh
from mathutils import Vector, Quaternion, Euler
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--try', dest='tries', type=int, default=1)
a = ap.parse_args()
K = 10.0; SZ = 0.016 * K; HZ = 120; DUR = 5.0
def run(seed):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    S = bpy.context.scene; S.render.fps = HZ; S.frame_start = 0; S.frame_end = int(DUR * HZ)
    bpy.ops.rigidbody.world_add(); W = S.rigidbody_world; W.substeps_per_frame = 20; W.solver_iterations = 40
    W.point_cache.frame_start = 0; W.point_cache.frame_end = S.frame_end; S.gravity = (0, 0, -9.81 * K)
    bpy.ops.mesh.primitive_plane_add(size=40 * K * 0.1); T = bpy.context.object
    bpy.ops.rigidbody.object_add(); T.rigid_body.type = 'PASSIVE'; T.rigid_body.friction = 0.6; T.rigid_body.restitution = 0.5
    T.rigid_body.collision_margin = 0.001 * K
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=SZ); bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=SZ * 0.12, segments=3, affect='EDGES')
    me = bpy.data.meshes.new('d'); bm.to_mesh(me); bm.free(); D = bpy.data.objects.new('d', me); S.collection.objects.link(D)
    bpy.context.view_layer.objects.active = D; D.select_set(True); bpy.ops.rigidbody.object_add()
    rb = D.rigid_body; rb.type = 'ACTIVE'; rb.collision_shape = 'CONVEX_HULL'; rb.mass = 0.004 * K ** 3; rb.friction = 0.6; rb.restitution = 0.55
    rb.collision_margin = 0.0004 * K; rb.linear_damping = 0.01; rb.angular_damping = 0.04
    # the throw: released 4 cm up, moving toward the camera and a little across, spinning, at a random tilt
    R = random.Random(seed)
    p0 = Vector((0.05 * K + R.uniform(-0.01, 0.01) * K, 0.16 * K, 0.06 * K)); v0 = Vector((R.uniform(-0.3, -0.15), R.uniform(-1.0, -0.8), R.uniform(0.0, 0.3))) * K
    w0 = Vector((R.uniform(-45, -25), R.uniform(-20, 20), R.uniform(-10, 10)))
    q0 = Euler((R.uniform(0, 6.3), R.uniform(0, 6.3), R.uniform(0, 6.3))).to_quaternion()
    # Bullet takes the starting velocity from a kinematic (animated) lead-in, then the die is let go at frame 0
    D.rotation_mode = 'QUATERNION'; lead = 3
    for i in range(-lead, 1):
        t = i / HZ; D.location = p0 + v0 * t; dq = Quaternion(w0.normalized(), w0.length * t) if w0.length else Quaternion()
        D.rotation_quaternion = dq @ q0; D.keyframe_insert('location', frame=i); D.keyframe_insert('rotation_quaternion', frame=i)
        rb.kinematic = i < 0; rb.keyframe_insert('kinematic', frame=i)
    W.point_cache.frame_start = -lead; S.frame_start = -lead
    path = []
    for f in range(-lead, S.frame_end + 1):
        S.frame_set(f)
        if f < 0: continue
        m = D.matrix_world; loc, rot, _ = m.decompose(); path.append((f / HZ, [c / K for c in loc], list(rot)))
    # hits: lowest point reaches the table while moving down (impact speed sets loudness)
    bb = [Vector((sx, sy, sz)) * SZ / 2 for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]; hits = []; ph = None; down = [False] * 8
    for t, l, r in path:
        q = Quaternion(r); hs = [(q @ c).z / K + l[2] for c in bb]
        if ph is not None:
            vs = [(h - p_) * HZ for h, p_ in zip(hs, ph)]; new = [i for i in range(8) if hs[i] < 0.0025 and not down[i] and vs[i] < -0.02]
            if new: sp = max(-vs[i] for i in new); hits.append((round(t, 4), round(sp, 3)))
        down = [h < 0.0025 for h in hs]; ph = hs
    merged = []
    for t, sp in hits:
        if merged and t - merged[-1][0] < 0.03: merged[-1] = (merged[-1][0], max(merged[-1][1], sp))
        else: merged.append((t, sp))
    hits = merged
    # where it ends up and when it stops
    last = path[-1]; rest_t = next((t for t, l, r in reversed(path) if Vector(l) - Vector(last[1]) != Vector() and (Vector(l) - Vector(last[1])).length > 0.0003), 0.0)
    up = max(range(6), key=lambda i: (Quaternion(last[2]) @ [Vector((0, 0, 1)), Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0))][i]).z)
    flat = abs((Quaternion(last[2]) @ Vector((0, 0, 1))).z) > 0.99 or abs((Quaternion(last[2]) @ Vector((1, 0, 0))).z) > 0.99 or abs((Quaternion(last[2]) @ Vector((0, 1, 0))).z) > 0.99
    travel = (Vector(last[1]) - Vector(p0 / K)).length
    return {'seed': seed, 'hz': HZ, 'path': path, 'hits': hits, 'rest_t': round(rest_t, 3), 'flat': flat, 'travel': round(travel, 3), 'end': last[1]}
best = None
for s in range(a.seed, a.seed + a.tries):
    r = run(s); n = len(r['hits'])
    score = (r['flat'], min(n, 7), -r['travel'])
    print('seed', s, 'hits', n, [h[0] for h in r['hits']], 'rest', r['rest_t'], 'flat', r['flat'], 'travel', r['travel'], 'end', [round(c, 3) for c in r['end']], flush=True)
    if best is None or score > best[0]: best = (score, r)
json.dump(best[1], open(a.out, 'w')); print('kept seed', best[1]['seed'], 'hits', best[1]['hits'])
