"""mix.py: voice over the score (story cut). The music dips about 6 dB while the voice is speaking and comes back in the gaps.
    python3 video/mix.py  ->  video/final.wav
"""
import os, numpy as np, scipy.signal as sg, soundfile as sf, pyloudnorm as pyln
HERE = os.path.dirname(os.path.abspath(__file__))
music, SR = sf.read(os.path.join(HERE, 'score.wav')); voice, sr2 = sf.read(os.path.join(HERE, 'voice.wav'))
assert SR == sr2
n = min(len(music), len(voice)); music = music[:n]; voice = voice[:n]
meter = pyln.Meter(SR)
# voice to -18 LUFS (measured over the speech only), music was made at about -16
spoken = np.abs(voice) > 1e-4
v_l = meter.integrated_loudness(voice[np.convolve(spoken, np.ones(4800), 'same') > 0])
voice = voice * 10 ** ((-18 - v_l) / 20)
env = np.sqrt(sg.sosfilt(sg.butter(1, 6, 'low', fs=SR, output='sos'), voice ** 2) + 1e-12)
talk = np.clip(env / 0.02, 0, 1)
# hold the dip through short gaps between words: slow release
rel = np.zeros(n); a_up = np.exp(-1 / (0.05 * SR)); a_dn = np.exp(-1 / (0.3 * SR)); g = 0.0
for i in range(n):
    x = talk[i]; g = a_up * g + (1 - a_up) * x if x > g else a_dn * g + (1 - a_dn) * x; rel[i] = g
duck = 10 ** (-6 * rel / 20)
mix = music * duck[:, None] + voice[:, None] * 0.98
mix *= 10 ** ((-15.5 - meter.integrated_loudness(mix)) / 20)
tp = lambda x: np.max(np.abs(sg.resample_poly(x, 4, 1, axis=0)))
ceil = 10 ** (-1.5 / 20)
if tp(mix) > ceil:
    over = np.abs(mix) > ceil * 0.8                      # soft-knee the few peaks rather than turn everything down
    mix = np.where(over, np.sign(mix) * (ceil * 0.8 + np.tanh((np.abs(mix) - ceil * 0.8) / (ceil * 0.2)) * ceil * 0.17), mix)
    if tp(mix) > ceil: mix *= ceil / tp(mix)
sf.write(os.path.join(HERE, 'final.wav'), mix, SR, subtype='PCM_24')
print('final.wav', round(meter.integrated_loudness(mix), 1), 'LUFS, true peak', round(20 * np.log10(tp(mix)), 2), 'dBTP')
