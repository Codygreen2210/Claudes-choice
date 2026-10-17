"""voicecheck.py: is the narrator on top? Compares the voice stem against the finished mix, second by second.
  python3 studio/senses/voicecheck.py narration.wav mix.wav
Fails if, while the narrator is talking, anything else comes within 10 dB of the voice (voice-to-rest ratio < 10 dB)
for more than 5% of the talking time. Catches the buried-narrator mix the Gimli sample shipped with on Oct 17 2026.
"""
import sys, numpy as np, soundfile as sf, librosa
vf, mf = sys.argv[1], sys.argv[2]
m, sr = sf.read(mf); m = m.mean(1) if m.ndim > 1 else m
v, _ = librosa.load(vf, sr=sr, mono=True); n = min(len(v), len(m)); v, m = v[:n], m[:n]
g = np.dot(m, v) / (np.dot(v, v) + 1e-12)                 # how loud the voice sits inside the mix
rest = m - g * v
hop = int(0.5 * sr); bad = talk = 0; worst = []
for i in range(0, n - hop, hop):
    vs, rs = g * v[i:i + hop], rest[i:i + hop]
    if np.sqrt(np.mean(vs ** 2)) < 0.01: continue
    talk += 1; r = 20 * np.log10(np.sqrt(np.mean(vs ** 2)) / (np.sqrt(np.mean(rs ** 2)) + 1e-9))
    if r < 10: bad += 1; worst.append((round(i / sr, 1), round(r, 1)))
share = bad / max(1, talk)
print(f'voice over the rest: {bad}/{talk} talking half-seconds under 10 dB ({share:.0%})  {"PASS" if share <= 0.05 else "FAIL"}')
if worst: print('  worst:', sorted(worst, key=lambda x: x[1])[:6])
sys.exit(0 if share <= 0.05 else 1)
