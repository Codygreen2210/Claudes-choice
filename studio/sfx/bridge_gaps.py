# bridge_gaps.py <film dir> <bed name> <db> m:ss.s-m:ss.s ... : lay a quiet library bed over silent gaps in fx.wav
import sys, os, numpy as np, soundfile as sf, shutil
sys.path.insert(0, '/home/claude/claudes-choice')
from studio.sfx import foley as F
d, name, db = sys.argv[1], sys.argv[2], float(sys.argv[3])
os.chdir(d)
fx, sr = sf.read('fx.wav'); dur = len(fx) / sr
if not os.path.exists('fx_before_bridge.wav'): shutil.copy('fx.wav', 'fx_before_bridge.wav')
tr = F.Track(dur, tail=0, seed=77)
ts = lambda s: int(s.split(':')[0]) * 60 + float(s.split(':')[1])
for g in sys.argv[4:]:
    a, b = [ts(x) for x in g.split('-')]
    tr.bed(name, max(0, a - 1.4), min(dur, b + 1.4), db=db, fin=0.7, fout=0.7)
add = tr.out().T if tr.out().ndim > 1 else tr.out()
add = tr.out(); add = add.T if add.shape[0] == 2 else add
n = min(len(fx), len(add)); out = fx.copy(); out[:n] += add[:n]
sf.write('fx.wav', out.astype(np.float32), sr, subtype='FLOAT')
print('bridged', len(sys.argv) - 4, 'gaps with', name, 'at', db, 'dB; used', tr.used)
