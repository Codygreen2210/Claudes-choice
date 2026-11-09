# Frame-to-frame turn of each foot (deg); flags any jump over LIMIT (camera cuts and the beat-9 shake are expected):  python3 spinchk.py F0 F1 [LIMIT]
import sys, os, runpy, math, json
f0, f1 = int(sys.argv[1]), int(sys.argv[2]); LIM = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
sys.argv = ['foot.py', '/tmp/x', '0', '1', '--scale', '0.2', '--samples', '4']
g = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "foot.py"), run_name="lib")
PB, RIG = g['PB'], g['RIG']; prev = {}; worst = {}
for f in range(f0, f1):
    g['frame'](f)
    for s in 'RL':
        q = (RIG.matrix_world @ PB['foot.' + s].matrix).to_quaternion()
        if s in prev:
            d = math.degrees(prev[s].rotation_difference(q).angle); d = min(d, 360 - d)
            worst[s] = max(worst.get(s, (0, 0)), (d, f))
            if d > LIM: print(f, s, 'turned %.0f deg' % d, flush=True)
        prev[s] = q
print('worst', {k: (round(v[0], 1), v[1]) for k, v in worst.items()})
