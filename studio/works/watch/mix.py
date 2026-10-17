# mix.py: narration + ticks on the escapement's real beats + a quiet piano-and-pad score, ducked under the voice.
import json, sys, os, numpy as np, soundfile as sf, librosa
from scipy.ndimage import uniform_filter1d
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sfx'))
import foley as F
SR = 48000
TM = json.load(open('timing.json')); L = {l['name']: l for l in TM['lines']}; DUR = TM['total']
T = lambda n: L[n]['t0']
sm = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
prog = lambda t, a, b: sm((t - a) / (b - a))
# the same watch clock as the picture
SPEED = [('open', 1), ('spring', .35), ('rotor', .35), ('train', 1), ('escape', .07), ('tick', .07), ('balance', .12), ('beat', 1), ('hands', .16), ('end', 1)]
def speed(t):
    s = 1
    for i, (n, v) in enumerate(SPEED):
        t0 = T(n) - 0.6
        if t >= t0: s = v if i == 0 else SPEED[i - 1][1] + (v - SPEED[i - 1][1]) * prog(t, t0, t0 + 1.2)
    return s
dt = 1 / 2000; ts = np.arange(0, DUR + 1, dt); tau = np.cumsum([speed(t) * dt for t in ts])
beats = np.searchsorted(tau, np.arange(1, int(tau[-1] * 8)) / 8) * dt

# ticks: loud in the close-ups, a whisper elsewhere
def tick_level(t):
    close = prog(t, T('escape') - .5, T('escape') + .5) * (1 - prog(t, T('hands') + 1, T('hands') + 3))
    return -30 + 22 * close + 6 * prog(t, T('beat'), T('beat') + .5) * (1 - prog(t, T('hands') - .5, T('hands')))
fx = F.Track(DUR + 2, tail=1.0, seed=3)
for i, b in enumerate(beats):
    if b < 0.5 or b > DUR - 1: continue
    fx.hit('tick', float(b), db=tick_level(b), pan=0.1 if i % 2 else -0.1, hi=bool(i % 2))
fxw = np.asarray(fx.out()); fxw = fxw.T if fxw.shape[0] == 2 else fxw
if F.SR != SR: fxw = librosa.resample(fxw.T, orig_sr=F.SR, target_sr=SR).T
fxw = np.pad(fxw, ((0, max(0, int((DUR + 2) * SR) - len(fxw))), (0, 0)))

# score: D major, slow chords on a soft pad, a few high piano notes like a music box
n = int((DUR + 2) * SR); t = np.arange(n) / SR; mus = np.zeros((n, 2))
chords = [[62, 69, 73, 78], [59, 66, 71, 74], [55, 62, 66, 71], [57, 64, 69, 73]]   # Dmaj7, Bm7, Gmaj7, A
bar = 4.8
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
for k in range(int(DUR / bar) + 1):
    t0 = k * bar; ch = chords[k % 4]; i0 = int(t0 * SR); i1 = min(n, int((t0 + bar + 1.5) * SR)); tt = t[i0:i1] - t0
    env = np.minimum(tt / 1.6, 1) * np.exp(-np.maximum(0, tt - bar) / 0.6)
    for m in ch:
        f = hz(m); y = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt + .3) + 0.12 * np.sin(2 * np.pi * 3 * f * tt)) * env * 0.035
        mus[i0:i1, 0] += y * 1.05; mus[i0:i1, 1] += y * 0.95
    for j, m in enumerate([ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12]):    # music-box notes
        s0 = t0 + j * bar / 4 + 0.05; a = int(s0 * SR); b2 = min(n, a + int(2.2 * SR)); u = t[a:b2] - s0; f = hz(m)
        y = (np.sin(2 * np.pi * f * u) + 0.25 * np.sin(2 * np.pi * 4.01 * f * u)) * np.exp(-u / 0.7) * np.minimum(u / 0.004, 1) * 0.05
        mus[a:b2] += np.stack([y * (0.9 + .2 * (j % 2)), y * (1.1 - .2 * (j % 2))], 1)
mus *= np.clip(np.minimum(t / 1.5, (DUR + 0.5 - t) / 2.0), 0, 1)[:, None]
# shape: quiet under the mechanism close-ups so the ticks carry them, fuller at the start and the end
shape = 1 - 0.8 * prog(t, T('escape') - 1, T('escape') + 1) * (1 - prog(t, T('beat') + 2, T('hands'))) + 2.2 * prog(t, L['end']['t1'] - 1, L['end']['t1'] + .6) - 0.5 * prog(t, T('spring') - 1, T('spring')) * (1 - prog(t, T('rotor') + 2, T('train')))
shape *= 1 - 0.8 * prog(t, T('tick') - 1.4, T('tick') - 0.6) * (1 - prog(t, L['tick']['t1'] + .3, L['tick']['t1'] + 1.2))   # silence before the tick
mus *= shape[:, None]

# narration, resampled to 48 k, and the ducking it drives
v, vsr = sf.read('narration.wav')
import librosa
v = librosa.resample(v, orig_sr=vsr, target_sr=SR)
from scipy.signal import butter, sosfilt
v = sosfilt(butter(2, 110, 'hp', fs=SR, output='sos'), v)   # trim the voice's boom
vo = np.zeros(n); vo[:min(n, len(v))] = v[:n]
env = np.sqrt(uniform_filter1d(vo ** 2, int(0.05 * SR)) + 1e-12); talk = uniform_filter1d((env > 0.01).astype(float), int(0.4 * SR))
duck = 10 ** (-14 * np.clip(talk * 1.5, 0, 1) / 20)
vg = 10 ** (-4.5 * prog(t, T('escape') - .3, T('escape') + .3) * (1 - prog(t, T('beat') - .3, T('beat'))) / 20)   # closer and quieter in the slow close-ups
mix = np.stack([vo * vg, vo * vg], 1) * 1.0 + mus * duck[:, None] * 3.4 + fxw[:n] * 1.0
pk = np.abs(mix).max(); mix *= 0.85 / pk
sf.write('final.wav', mix[:int((DUR) * SR)], SR)
print('final.wav', round(DUR, 1), 's, ticks', len(beats))
