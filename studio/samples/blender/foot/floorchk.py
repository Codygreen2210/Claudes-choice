# Feet vs the floor, every frame (room and x-ray beats):  python3 floorchk.py F0 F1 STEP
# Prints how far floor_fix lifted each foot (= how deep it would have gone in) and the lowest skin point left after the fix.
import sys, os, runpy, json
f0, f1, st = (int(x) for x in sys.argv[1:4])
sys.argv = ['foot.py', '/tmp/x', '0', '1', '--scale', '0.2', '--samples', '4']
g = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'foot.py'), run_name='lib')
bpy, np, BODY = g['bpy'], g['np'], g['BODY']
from bpy_extras.object_utils import world_to_camera_view
S = bpy.context.scene; CAM = g['CAM']
out = {}
for f in range(f0, f1, st):
    g['frame'](f); lift = dict(g['FLOOR_LOG'])
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh(); n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co)
    rp = np.empty(n * 3, np.float32); me.attributes['rest_position'].data.foreach_get('vector', rp); oe.to_mesh_clear()
    co = co.reshape(-1, 3); rp = rp.reshape(-1, 3)
    M_ = np.array(BODY.matrix_world); w = co @ M_[:3, :3].T + M_[:3, 3]
    gap = float((w[:, 2] - g['floor_top'](w[:, 0], w[:, 1])).min())
    sole = w[rp[:, 2] < 0.035]                                    # are the soles on screen at all (for the re-render list)
    Mi = np.array(CAM.matrix_world.inverted()); lc = sole @ Mi[:3, :3].T + Mi[:3, 3]; z = -lc[:, 2]
    fv = CAM.data.view_frame(scene=S); d = -fv[0].z                 # same maths as world_to_camera_view, for all points at once
    x0, x1, y0, y1 = fv[2].x * z / d, fv[1].x * z / d, fv[1].y * z / d, fv[0].y * z / d
    xs = (lc[:, 0] - x0) / (x1 - x0); ys = (lc[:, 1] - y0) / (y1 - y0)
    vis = int(((xs >= 0) & (xs <= 1) & (ys >= 0) & (ys <= 1) & (z > 0)).sum())
    out[f] = dict(lift=lift, gap=gap, plant=sorted(g['PLANT']), sole_vis=vis)
    print(f, 'lift', {k: round(v * 1000, 1) for k, v in lift.items()}, 'mm  lowest skin', round(gap * 1000, 1), 'mm  plant', sorted(g['PLANT']), 'soles on screen', vis, flush=True)
json.dump(out, open(f'/root/vt/n41/foot/floor_{f0}_{f1}.json', 'w'))
