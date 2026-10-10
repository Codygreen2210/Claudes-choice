#!/usr/bin/env python3
"""mix.py: voice + music + sound into final.wav. The music ducks under the voice and comes up in the gaps.
Target: -14 LUFS integrated, true peak at or under -1 dBTP, voice sitting about 12 LU above the music under it."""
import sys, os, numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import maximum_filter1d, uniform_filter1d
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from studio.instruments import synth as S
v, sr = sf.read('narration.wav'); assert sr == S.SR
m, _ = sf.read('music.wav'); f, _ = sf.read('fx.wav')
n = min(len(v), len(m), len(f)); v = v[:n]; m = m[:n].T; f = f[:n].T
meter = pyln.Meter(sr)
# voice: gentle clean-up, then to -17 LUFS (speech-gated)
v = S.hp(v, 70, 2)
v = S.eq(v[None, :], [('peak', 220, -1.5, 1.0), ('peak', 3200, 1.5, 0.9), ('highshelf', 9000, 1.5, 0.7)])[0]
v = v * 10 ** ((-17 - meter.integrated_loudness(v)) / 20)
env = np.sqrt(uniform_filter1d(v * v, int(0.02 * sr)))
talking = maximum_filter1d((env > 0.012).astype(float), int(0.35 * sr))            # hold through short pauses
duck = uniform_filter1d(talking, int(0.45 * sr))                                     # slow in, slow out
gm = 10 ** ((-5.0 * duck) / 20)                                                      # 5 dB down under speech
gf = 10 ** ((-3.0 * duck) / 20)
mix = np.stack([v, v]) * 1.0 + m * gm * 0.62 + f * gf * 0.8
out = S.master(mix, lufs=-14.0, fade=0, ceiling=0.86)
sf.write('final.wav', out.T.astype(np.float32), sr, subtype='PCM_16')
vv = np.stack([v, v]); bed = m * gm * 0.62 + f * gf * 0.8
sel = duck > 0.9
print('voice', round(meter.integrated_loudness(v), 1), 'LUFS; bed under voice', round(meter.integrated_loudness(bed[:, sel].T), 1), 'LUFS; bed in gaps', round(meter.integrated_loudness(bed[:, duck < 0.1].T), 1), 'LUFS; final', round(meter.integrated_loudness(out.T), 1), 'LUFS; peak', round(float(np.max(np.abs(out))), 3))
