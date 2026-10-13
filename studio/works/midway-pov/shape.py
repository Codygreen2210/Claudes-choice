# shape.py: story-driven level moves on final.wav (quiet rooms and maps, loud dives and hits).
import json, re, numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d
TM = json.load(open('timing.json')); SC = TM['scenes']
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()
def q(i, p):
    p = norm(p).split(); W = [norm(w['w']) for w in SC[i]['words']]
    return next(SC[i]['words'][k]['s'] for k in range(len(W)) if W[k:k + len(p)] == p)
V = [0.0] + [s['start'] - 0.45 for s in SC[1:]] + [TM['total']]
x, sr = sf.read('final.wav'); n = len(x); t = np.arange(n) / sr; g = np.zeros(n)
moves = [(V[1], V[3], -3.0), (q(3, 'three american carriers'), V[4], -2.0), (q(4, 'at seven'), q(4, 'your second wave'), -2.0),
         (q(5, 'to drop your'), q(5, 'yours too') + 1, 1.0), (V[6], V[7], -2.5), (V[7], V[8], -2.0),
         (q(8, 'you roll over'), q(8, 'you pull out'), 1.5), (q(9, 'you fire at'), q(9, 'the yorktown stops'), 1.0),
         (q(9, 'the yorktown stops'), q(9, 'but that afternoon'), -2.5), (V[10], TM['total'], -2.5)]
for a, b, db in moves: g[(t >= a) & (t < b)] = db
g = uniform_filter1d(g, int(1.0 * sr)); x = x * (10 ** (g / 20))[:, None]
sf.write('final_shaped.wav', x.astype(np.float32), sr, subtype='PCM_16')
