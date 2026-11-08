"""Put a re-read narration onto an OLD timing, so a finished picture doesn't need re-rendering (a word fix, a new pronunciation).
Each line of the new read is cut at its voice span, stretched to the old span's length (pitch kept) and placed at the old start.
    python3 refit.py OLD_DIR NEW_DIR OUT.wav      (each dir has times.json + narration.wav)"""
import sys, json
import numpy as np, soundfile as sf, librosa

old_d, new_d, out = sys.argv[1:4]
to, tn = json.load(open(f'{old_d}/times.json')), json.load(open(f'{new_d}/times.json'))
yn, sr = sf.read(f'{new_d}/narration.wav', always_2d=True); yo, sr2 = sf.read(f'{old_d}/narration.wav', always_2d=True)
assert sr == sr2 and len(to['voice']) == len(tn['voice'])
res = np.zeros_like(yo)
for i, ((o0, o1), (n0, n1)) in enumerate(zip(to['voice'], tn['voice'])):
    pad = 0.04                                                    # keep the soft edges of each line
    seg = yn[max(0, int((n0 - pad) * sr)):int((n1 + pad) * sr)]
    want = int(((o1 - o0) + 2 * pad) * sr); rate = len(seg) / want
    st = np.stack([librosa.effects.time_stretch(np.ascontiguousarray(seg[:, c]), rate=rate) for c in range(seg.shape[1])], 1) if abs(len(seg) - want) > 0.06 * sr else seg     # tiny differences: no stretch (a phase vocoder smears the voice)
    if len(st) > want: st = st[:want] * np.r_[np.ones(want - int(0.02 * sr)), np.linspace(1, 0, int(0.02 * sr))][:, None]
    else: st = np.pad(st, ((0, want - len(st)), (0, 0)))
    a = max(0, int((o0 - pad) * sr)); b = min(len(res), a + len(st))
    res[a:b] += st[:b - a]
    print(f'line {i}: {n1 - n0:.2f}s -> {o1 - o0:.2f}s (x{1 / rate:.3f})')
sf.write(out, res, sr)
