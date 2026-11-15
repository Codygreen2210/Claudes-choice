"""The real-recording sound library (pulled by .github/workflows/sfx.yml, unpacked under /root/vt/sfx/*/lib/).
    from sfxlib import Lib, whooshes_from_camera
    L = Lib(); hits = L.find('wood impact', avoid='gore blood'); x = L.load(hits[0])        # stereo float32 at 48 kHz
    L.show('dice')                                                                            # print matches
Search is by words in the original pack/file names (e.g. 'WOODImpt_Wood Hit Table ...'), best matches first.
Licence: Sonniss #GameAudioGDC bundles, royalty-free, commercial use, no attribution (sonniss.com/gdc-bundle-license)."""
import os, json, glob, re, hashlib
import numpy as np
SR = 48000
ROOTS = [os.environ.get('SFX_ROOT', '/root/vt/sfx')]

class Lib:
    def __init__(self, roots=None):
        self.items = []
        for r in roots or ROOTS:
            for ip in sorted(glob.glob(os.path.join(r, '*', 'lib', 'index.json'))):
                d = os.path.dirname(ip)
                for e in json.load(open(ip)):
                    e = dict(e); e['path'] = os.path.join(d, e['file']); e['key'] = re.sub(r'[^a-z0-9]+', ' ', e['src'].lower())
                    if os.path.exists(e['path']): self.items.append(e)
    def find(self, words, avoid='', minlen=0.0, maxlen=99.0, n=40):
        ws = [w for w in words.lower().split() if w]; av = [w for w in avoid.lower().split() if w]
        out = []
        for e in self.items:
            if not (minlen <= e['len'] <= maxlen): continue
            k = ' ' + e['key'] + ' '
            if any(a in k for a in av): continue
            sc = sum(2.0 if f' {w} ' in k else (1.0 if w in k else 0.0) for w in ws)
            if sc >= len(ws) * 0.99: out.append((sc, e))                  # every word must show up at least once
        out.sort(key=lambda z: (-z[0], z[1]['len'])); return [e for _, e in out[:n]]
    def pick(self, words, seed=0, **kw):
        c = self.find(words, **kw)
        if not c: raise LookupError(f'no sound for "{words}"')
        h = int(hashlib.md5(f'{words}|{seed}'.encode()).hexdigest(), 16); return c[h % len(c)]
    def load(self, e, dur=None, fade=0.03):
        import soundfile as sf
        x, sr = sf.read(e['path'], always_2d=True, dtype='float32')
        if x.shape[1] == 1: x = np.repeat(x, 2, 1)
        if dur is not None and len(x) > int(dur * SR):
            x = x[:int(dur * SR)].copy(); f = int(fade * SR); x[-f:] *= np.linspace(1, 0, f)[:, None]
        return x
    def show(self, words, **kw):
        for e in self.find(words, **kw): print(f"{e['file']:28s} {e['len']:5.2f}s  {e['src'][:110]}")

def whooshes_from_camera(pos, fps, thresh=None):
    """Camera positions (N,3) a frame -> [(start_s, dur_s, strength 0..1)] one whoosh per fast move (speed peak)."""
    p = np.asarray(pos, float); v = np.r_[0, np.linalg.norm(np.diff(p, axis=0), axis=1)] * fps
    v = np.convolve(v, np.ones(5) / 5, mode='same'); thr = thresh if thresh is not None else max(np.percentile(v, 60) * 1.8, 1e-6)
    out = []; i = 0
    while i < len(v):
        if v[i] > thr:
            j = i
            while j < len(v) and v[j] > thr * 0.6: j += 1
            pk = float(v[i:j].max()); out.append((i / fps, max(0.25, (j - i) / fps), min(1.0, pk / (thr * 4)))); i = j
        else: i += 1
    return out

class Bus:
    """A simple stereo mix bus: put(x, t, db, pan) then render(lufs)."""
    def __init__(self, dur): self.y = np.zeros((int(dur * SR) + SR, 2), np.float32)
    def put(self, x, t, db=0.0, pan=0.0, rate=1.0):
        if rate != 1.0:
            n = int(len(x) / rate); idx = np.linspace(0, len(x) - 1, n); x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1)
        g = 10 ** (db / 20); l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
        a = int(t * SR)
        if a < 0: x = x[-a:]; a = 0
        b = min(len(self.y), a + len(x)); self.y[a:b, 0] += x[:b - a, 0] * g * l; self.y[a:b, 1] += x[:b - a, 1] * g * r
    def render(self, dur, lufs=-14.0, peak_db=-1.0):
        import pyloudnorm as pl
        y = self.y[:int(dur * SR)].astype(np.float64); m = pl.Meter(SR); lu = m.integrated_loudness(y)
        if np.isfinite(lu): y = y * 10 ** ((lufs - lu) / 20)
        pk = np.abs(y).max(); lim = 10 ** (peak_db / 20)
        if pk > lim:                                                       # soft-limit only the samples above 70% of the ceiling
            k = 0.7 * lim; a_ = np.abs(y); over = a_ > k
            y[over] = np.sign(y[over]) * (k + (lim - k) * np.tanh((a_[over] - k) / (lim - k)))
        try:                                                               # true-peak guard: 4x oversampled peak must stay under the ceiling
            from scipy.signal import resample_poly
            tp = np.abs(resample_poly(y, 4, 1, axis=0)).max()
            if tp > lim: y = y * (lim / tp)
        except Exception: pass
        return y.astype(np.float32)
