"""Make the studio voice (Kokoro, local, free) sit like the beer-flood narrator."""
import numpy as np, soundfile as sf, librosa, pyloudnorm as pyln
from scipy import signal as sg
from kokoro_onnx import Kokoro
SR = 24000
TEXT = "This plane ran out of fuel at forty-one thousand feet. Both engines went quiet. And it all came down to one math mistake."
k = Kokoro('kokoro-v1.0.onnx', 'voices-v1.0.bin')

def ltas(y):
    f, p = sg.welch(y, SR, nperseg=2048)
    return f, 10 * np.log10(p + 1e-14)

def norm(y, lufs=-16):
    m = pyln.Meter(SR); return pyln.normalize.loudness(y, m.integrated_loudness(y), lufs)

ref, _ = librosa.load('beer_ref.wav', sr=SR)
# before: the studio voice as it was (Midway films: am_michael, speed 1.0)
before, _ = k.create(TEXT, voice='am_michael', speed=1.0, lang='en-us')
# after 1. voice: blend tuned to the beer narrator's pitch (~132 Hz) and range; 2. pace: beer talks 4.7 syl/s
style = k.get_voice_style('am_fenrir') * 0.65 + k.get_voice_style('am_puck') * 0.35
import re
parts = []
for sent in re.split(r'(?<=[.!?])\s+', TEXT):
    a, _ = k.create(sent, voice=style, speed=1.42, lang='en-us')
    nz = np.where(np.abs(a) > 0.01)[0]
    parts += [a[max(0, nz[0] - 240):nz[-1] + 480], np.zeros(int(0.24 * SR))]   # beer narrator's median pause
y = np.concatenate(parts[:-1])
# no pitch shift: the phase vocoder smeared the voice into an echo; the blend already sits near 132 Hz
# 3. tone: match the long-term spectrum to the beer voice (smoothed, capped at +-8 dB)
f, Lr = ltas(ref); _, Ly = ltas(y)
diff = np.clip(sg.savgol_filter(Lr - Ly - np.mean((Lr - Ly)[(f > 300) & (f < 3000)]), 101, 2), -5, 5)   # broad strokes only, no ringing
diff[f < 70] = -12
fir = sg.minimum_phase(sg.firwin2(513, f / (SR / 2), 10 ** (diff / 20)), method='homomorphic')   # min-phase: no pre-echo
y = sg.lfilter(fir, [1.0], y)
# 4. hold energy to the end of each phrase like the beer read (slow leveler), then light compression
env = np.sqrt(sg.lfilter([1 - 0.9995], [1, -0.9995], y ** 2)) + 1e-4
g = np.clip((np.median(env[env > 0.01]) / env) ** 0.5, 0.6, 2.0)
y = y * sg.lfilter([0.002], [1, -0.998], g)
th = 10 ** (-18 / 20); a = np.abs(y); c = np.where(a > th, (th + (a - th) / 3) / (a + 1e-9), 1.0)
y = y * sg.lfilter([0.02], [1, -0.98], c)
# final tone: ffmpeg equalizer=f=450:t=o:w=1.3:g=-5,equalizer=f=150:t=o:w=1:g=2,loudnorm=I=-16:TP=-2
for name, s in (('before_studio_voice', before), ('after_matched_voice', y), ('beer_narrator', ref)):
    s = norm(s); s = s / max(1, np.max(np.abs(s)) / 0.89)
    sf.write(name + '.wav', s, SR)
print('ok')
