# Sound for the 10 s Emu War stage-play style test: a theatre full of people, the curtains, the cut-outs sliding and knocking into place,
# a drum roll into the guns, the emus flapping round and running, a laugh at the end.   python3 sound.py OUT.wav
import sys, os
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'senses'))
from sfxlib import Lib
from scipy.signal import resample_poly
SR = 48000; T = 10.0; N = int(SR * T); mix = np.zeros((N, 2)); L = Lib(); g = np.random.default_rng(5)
def load(words, seed=0):
    c = L.find(words)
    if not c: print('no sound:', words); return None
    x = L.load(c[seed % min(len(c), 6)]); x = x if x.ndim == 2 else np.stack([x, x], 1)
    return x
def put(words, t, db, seed=0, dur=None, pan=0.0, fade=0.03, off=0.0):
    x = load(words, seed)
    if x is None: return
    a0 = int(off * SR); x = x[a0:] if a0 < len(x) - 2400 else x
    if dur: x = x[:int(dur * SR)]
    n = len(x); f = min(int(fade * SR), n // 2)
    env = np.ones(n); env[:f] = np.linspace(0, 1, f); env[n - f:] = np.linspace(1, 0, f)
    x = x * env[:, None] * 10 ** (db / 20); x[:, 0] *= np.sqrt(0.5 - pan / 2) * 1.414; x[:, 1] *= np.sqrt(0.5 + pan / 2) * 1.414
    i = int(t * SR); j = min(N, i + n)
    if j > i: mix[i:j] += x[:j - i]
# the room: an audience and a pit orchestra under everything
put('audience', 0.0, -26, dur=T, fade=0.2); put('orchestra', 0.0, -22, seed=1, dur=T, fade=0.4)
put('applause', 0.0, -12, dur=2.8, fade=0.6); put('crowd cheer', 0.2, -20, seed=2, dur=2.0, fade=0.4)
# curtains swish open
put('curtain', 0.0, -14, dur=2.6, fade=0.1); put('fabric', 0.6, -18, seed=1, dur=1.8, fade=0.2, pan=0.4)
# the sun drops on its rod and knocks to a stop
put('whoosh airy', 0.45, -16, seed=3, dur=1.2); put('wood knock', 1.68, -14, seed=2); put('pop', 1.72, -20, seed=1)
# cut-outs slide in on their tracks and knock into place
for t0, t1, pan, sd in ((1.1, 2.2, -0.6, 0), (2.2, 3.3, -0.4, 1), (2.45, 3.55, -0.3, 2), (2.75, 3.85, -0.15, 3)):
    put('wood slide', t0, -17, seed=sd, dur=t1 - t0, pan=pan); put('wood knock', t1, -15, seed=sd + 4, pan=pan); put('cardboard', t1 + 0.05, -19, seed=sd, dur=0.4, pan=pan)
# the emus bob and squawk
put('squawk', 3.1, -16, seed=0, pan=0.4); put('squawk', 4.4, -18, seed=1, pan=0.6)
# drum roll into the guns
put('drum roll', 3.9, -15, seed=0, dur=1.55, fade=0.1); put('cymbal', 5.4, -14, seed=1, dur=1.6)
put('machine gun', 5.4, -11, seed=0, dur=1.2, fade=0.05, pan=-0.4)
for k in range(5): put('pop', 5.5 + 0.2 * k, -18, seed=k, pan=0.3)                # dust puffs
# the emus flip round (cards flapping) and run off with boings
for k in range(4): put('paper', 5.55 + 0.08 * k, -17, seed=k, dur=0.35, pan=0.3 + 0.1 * k)
put('footsteps', 5.95, -15, seed=3, dur=1.8, pan=0.6); put('boing', 6.0, -15, seed=0, pan=0.5); put('boing', 6.35, -17, seed=1, pan=0.8)
put('squawk', 6.1, -14, seed=2, pan=0.7); put('whoosh airy', 7.7, -15, seed=8, dur=0.9)
# the last emu pecks at the major, who leans back; the audience laughs
put('squawk', 8.2, -12, seed=3, pan=0.2); put('wood knock', 8.35, -16, seed=7); put('cardboard', 8.45, -15, seed=5, dur=0.5)
put('crowd cheer', 8.6, -14, seed=6, dur=1.4, fade=0.3); put('applause', 9.0, -16, seed=3, dur=1.0, fade=0.4)
# level to -14 LUFS, keep peaks under -1 dBTP
import pyloudnorm as pyln
m = pyln.Meter(SR); lu = m.integrated_loudness(mix); mix *= 10 ** ((-14.0 - lu) / 20)
up = resample_poly(mix, 4, 1, axis=0); pk = np.abs(up).max(); lim = 10 ** (-2.0 / 20)
if pk > lim:
    env = np.maximum(np.abs(mix).max(1) / lim, 1.0); from scipy.ndimage import maximum_filter1d, uniform_filter1d
    env = uniform_filter1d(maximum_filter1d(env, 480), 480); mix /= env[:, None]
mix[-int(0.15 * SR):] *= np.linspace(1, 0, int(0.15 * SR))[:, None]
sf.write(sys.argv[1], mix, SR); print('wrote', sys.argv[1], round(m.integrated_loudness(mix), 1), 'LUFS')
