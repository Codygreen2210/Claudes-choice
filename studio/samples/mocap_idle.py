# Make a standing "life" layer from a CMU motion-capture clip (BVH, from github.com/una-dinosauria/cmu-mocap; CMU's data is free to use):
# the small sways, weight shifts and head moves of a real person standing, with the big moves (turns, steps) filtered out.
#   python3 mocap_idle.py CLIP.bvh OUT.json [--hp 2.5] [--lp 0.3]
# OUT.json: fps 30, per channel a list (degrees / metres): hips_x, hips_z (shift), hips (x,y,z rot), back, chest, neck, head (x,y,z each).
import sys, json, argparse, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('bvh'); ap.add_argument('out'); ap.add_argument('--hp', type=float, default=2.5); ap.add_argument('--lp', type=float, default=0.3); a = ap.parse_args()
L = open(a.bvh).read().split('\n'); chans, names = [], []; i = 0
while not L[i].strip().startswith('MOTION'):
    t = L[i].split()
    if t and t[0] in ('ROOT', 'JOINT'): names.append(t[1])
    if t and t[0] == 'CHANNELS': chans.append((names[-1], t[2:]))
    i += 1
nf = int(L[i + 1].split()[1]); ft = float(L[i + 2].split()[2])
d = np.array([[float(x) for x in l.split()] for l in L[i + 3:i + 3 + nf]])[1:]          # frame 1 is the added T-pose
cols = {}; k = 0
for n, cs in chans:
    for c in cs: cols[(n, c)] = k; k += 1
src_fps = 1 / ft; n30 = int(len(d) / src_fps * 30)
idx = np.linspace(0, len(d) - 1, n30)
col = lambda n, c: np.interp(idx, np.arange(len(d)), d[:, cols[(n, c)]])
def smooth(x, w):
    w = max(1, int(w)) | 1; k = np.ones(w) / w; pad = np.pad(x, w, mode='reflect'); return np.convolve(pad, k, 'same')[w:-w]
def hp(x):                                                          # keep the motion between ~0.3 s and ~hp seconds: no drift, no twitch
    return smooth(x - smooth(x, a.hp * 30), a.lp * 30)
S = 0.95 / np.mean(col('Hips', 'Yposition'))                        # BVH units -> metres (his hip height)
rot = lambda n: [hp(col(n, c)) for c in ('Xrotation', 'Yrotation', 'Zrotation')]
add = lambda *rs: [sum(r[j] for r in rs) for j in range(3)]
out = {'fps': 30, 'n': n30, 'src': a.bvh.split('/')[-1],
       'hips_x': hp(col('Hips', 'Xposition')) * S, 'hips_z': hp(col('Hips', 'Zposition')) * S, 'hips': rot('Hips'),
       'back': add(rot('LowerBack'), rot('Spine')), 'chest': rot('Spine1'), 'neck': add(rot('Neck'), rot('Neck1')), 'head': rot('Head')}
def r(v): return [round(float(x), 3) for x in v]
for k_, v in list(out.items()):
    if isinstance(v, np.ndarray): out[k_] = r(v)
    elif isinstance(v, list): out[k_] = [r(x) for x in v]
json.dump(out, open(a.out, 'w'), separators=(',', ':'))
st = lambda v: np.round(np.std(v), 2)
print(a.out, n30, 'frames;', 'hips shift sd (cm)', st(out['hips_x']) * 100, st(out['hips_z']) * 100, '| back sd', [st(x) for x in out['back']], '| head sd', [st(x) for x in out['head']])
