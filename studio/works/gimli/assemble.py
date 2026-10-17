"""assemble.py: cut the Gimli Glider sample from Runway clips, the fuel insert and the ElevenLabs narration.
Cuts land in the narration's pauses; sound leads picture into each new scene (J-cuts).
  python3 assemble.py  ->  gimli_sample.mp4 (+ mix.wav for the ears)
"""
import os, subprocess, sys, json
import numpy as np, soundfile as sf, librosa
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'sfx')); import foley as F
SR = 48000; FPS = 30; END = 50.5
have = lambda f: os.path.exists(f) and os.path.getsize(f) > 10000
cockpit = 'cockpit.mp4' if have('cockpit.mp4') else None
glide = 'glide.mp4' if have('glide.mp4') else None

# (source, t0 in film, t1 in film, speed, source start)
EDL = [('cruise.mp4', 0.0, 5.45, 0.92, 0.0)]
if cockpit: EDL += [(cockpit, 5.45, 8.35, 1.0, 0.3)]
else: EDL += [('engine.mp4', 5.45, 8.35, 1.0, 0.0)]
EDL += [('engine.mp4', 8.35, 12.75, 0.75, 1.6 if not cockpit else 0.0)]
EDL += [(cockpit, 12.75, 16.6, 1.0, 4.1)] if cockpit else [('cruise.mp4', 12.75, 16.6, 0.8, 1.0)]
EDL += [('fuel.mp4', 16.6, 28.6, 1.0, 0.0)]                # holds on the last frame once the insert ends
if glide: EDL += [(glide, 28.6, 41.2, 0.4, 0.0)]
else: EDL += [('cruise.mp4', 28.6, 41.2, 0.4, 0.0)]
EDL += [('race.mp4', 41.2, END, 0.55, 0.0)]


def ff(*a): subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


parts = []
for i, (src, t0, t1, sp, ss) in enumerate(EDL):
    o = f'part{i}.mp4'; dur = t1 - t0
    vf = (f"setpts=(PTS-STARTPTS)/{sp},minterpolate=fps={FPS}:mi_mode=blend," if sp < 0.99 else f"fps={FPS},") + \
         "scale=1920:1080:flags=lanczos,tpad=stop_mode=clone:stop_duration=20,eq=contrast=1.04:saturation=1.05"
    ff('-ss', f'{ss}', '-i', src, '-vf', vf, '-t', f'{dur:.3f}', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', o)
    parts.append(o)
open('list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
ff('-f', 'concat', '-safe', '0', '-i', 'list.txt', '-vf', f"fade=t=out:st={END - 1.6}:d=1.6,noise=alls=6:allf=t", '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', 'pic.mp4')

# ---- sound
n = int((END + 1) * SR); t = np.arange(n) / SR
v, vsr = librosa.load('narration.mp3', sr=SR, mono=True); vo = np.zeros(n); vo[:len(v)] = v[:n]
fx = F.Track(END + 1, tail=1.0, seed=7)
fx.bed('jet_cruise', 0.0, 9.5, db=-4, fin=0.3, fout=1.0)
fx.hit('caution_chime', 5.45, db=-12); fx.hit('caution_chime', 7.05, db=-11)
fx.hit('jet_spooldown', 8.2, db=-3, dur=7.0)
fx.bed('wind', 13.5, 29.0, db=-12, fin=2.0, fout=2.0)
fx.bed('wind', 27.6, 41.6, db=-8, fin=1.0, fout=1.2)          # J-cut: the glide's wind arrives a second early
fx.bed('murmur', 40.4, END, db=-12, fin=0.8, fout=1.5)        # J-cut into the race crowd
fx.bed('crickets', 40.4, END, db=-16, fin=1.0, fout=1.5)
f = np.asarray(fx.out()); f = f.T if f.shape[0] == 2 else f
if F.SR != SR: f = librosa.resample(f.T, orig_sr=F.SR, target_sr=SR).T
f = np.pad(f, ((0, max(0, n - len(f))), (0, 0)))[:n]

# score: low strings-like pad in D minor, a pulse that stops dead when the engines quit, swells for the reveal
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
mus = np.zeros((n, 2))
def pad(t0, t1, notes, g):
    a, b = int(t0 * SR), min(n, int(t1 * SR)); u = t[a:b] - t0; L = t1 - t0
    env = np.minimum(u / 1.8, 1) * np.minimum((L - u) / 1.5, 1).clip(0, 1)
    for m in notes:
        fr = hz(m); y = sum(np.sin(2 * np.pi * fr * k * u + k) / k ** 1.6 for k in (1, 2, 3)) * (1 + 0.004 * np.sin(2 * np.pi * 5 * u))
        mus[a:b, 0] += y * env * g; mus[a:b, 1] += np.roll(y, 40) * env * g
pad(0.0, 9.0, [50, 57, 62, 65], 0.016)            # Dm
pad(12.4, 21.5, [46, 53, 58, 62], 0.014)          # Bb
pad(21.0, 29.0, [45, 52, 57, 61], 0.016)          # A (tension)
pad(28.6, 41.5, [50, 57, 62, 69], 0.018)          # Dm, open, the glide
pad(41.0, END, [43, 50, 58, 62, 67], 0.02)        # Gm add 9: the race-day turn
for k in range(int(8.2 / 0.75)):                   # heartbeat pulse until the engines quit
    a = int(k * 0.75 * SR); b = min(n, a + int(0.25 * SR)); u = t[a:b] - k * 0.75
    mus[a:b] += (np.sin(2 * np.pi * 55 * u) * np.exp(-u / 0.08) * 0.10)[:, None]
mus[int(39.4 * SR):int(41.4 * SR)] *= np.linspace(1, 0.15, int(2.0 * SR))[:, None]   # drop out before "what nobody knows"

from scipy.ndimage import uniform_filter1d
# level hierarchy (voice is king): voice RMS while talking = 0 dB, effects -14 dB, music -24 dB, ducked further under speech
def rms(x): return np.sqrt(np.mean(x ** 2) + 1e-12)
talking = vo[np.abs(vo) > 0.01]; vo = vo * (0.1 / rms(talking))
f = f.mean(1, keepdims=True).repeat(2, 1) * 0.85 + f * 0.15          # fold the fake stereo spread back to near-mono
f = f * (0.1 * 10 ** (-14 / 20) / rms(f[np.abs(f).max(1) > 1e-4]))
mus = mus * (0.1 * 10 ** (-24 / 20) / rms(mus[np.abs(mus).max(1) > 1e-5]))
env = np.sqrt(uniform_filter1d(vo ** 2, int(0.05 * SR)) + 1e-12); talk = uniform_filter1d((env > 0.02).astype(float), int(0.3 * SR))
duck = 10 ** (-7 * np.clip(talk * 1.5, 0, 1) / 20)
duck_fx = 10 ** (-14 * np.clip(talk * 1.5, 0, 1) / 20)                 # effects step well back while he talks
f = np.clip(f, -0.06, 0.06)                                              # tame the hits' peaks
mix = np.stack([vo, vo], 1) + mus * duck[:, None] * 2.0 + f * duck_fx[:, None]
mix *= np.clip((END + 0.3 - t) / 1.6, 0, 1)[:, None]
mix *= 0.88 / np.abs(mix).max()
sf.write('mix.wav', mix, SR)
ff('-i', 'mix.wav', '-af', 'equalizer=f=300:width_type=o:width=1.4:g=-3,equalizer=f=3200:width_type=o:width=1.2:g=2,loudnorm=I=-15:TP=-1.5:LRA=11', '-ar', '48000', 'mix_eq.wav')
ff('-i', 'pic.mp4', '-i', 'mix_eq.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', 'gimli_sample.mp4')
json.dump([e[1] for e in EDL[1:]], open('cuts.json', 'w'))
print('wrote gimli_sample.mp4; cockpit:', bool(cockpit), 'glide:', bool(glide))
