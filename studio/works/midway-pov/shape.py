# shape.py: story-driven level moves on final.wav (the quiet bridge, the loud dive), so the sample is not one flat level.
import json, re, numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d
TM = json.load(open('timing.json')); SC = TM['scenes']
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()
def q(i, p):
    p = norm(p).split(); W = [norm(w['w']) for w in SC[i]['words']]
    return next(SC[i]['words'][k]['s'] for k in range(len(W)) if W[k:k + len(p)] == p)
x, sr = sf.read('final.wav'); n = len(x); t = np.arange(n) / sr; g = np.zeros(n)
moves = [(SC[1]['start'] - 0.45, SC[2]['start'] - 0.45, -3.5), (SC[0]['start'], q(0, 'then you see it'), -1.5),
         (q(2, 'every plane in') + 1.5, SC[3]['start'] - 0.45, -3.0), (q(3, 'you roll over'), q(3, 'you pull out'), 1.5), (q(3, 'but one of them'), TM['total'], -2.0)]
for a, b, db in moves: g[(t >= a) & (t < b)] = db
g = uniform_filter1d(g, int(1.0 * sr)); x = x * (10 ** (g / 20))[:, None]
sf.write('final_shaped.wav', x.astype(np.float32), sr, subtype='PCM_16')
