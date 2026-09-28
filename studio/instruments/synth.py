"""synth: the sound kit. Oscillators, envelopes, filters, instruments, drums, effects and a mastering chain,
all plain numpy so every sound is made from scratch and can be shaped exactly.

Everything is stereo arrays shaped (2, n) or mono (n,), at SR = 44100. Times are in seconds, pitches in MIDI.

    from studio.instruments import synth as S
    mix = S.Bus(8.0)
    mix.add(0.0, S.pluck(64), g=0.3, pan=-0.2)
    S.write('out.wav', S.master(mix.out()))

Pulled out of the Hektiq promo scores, where I rebuilt most of this from scratch each time.
"""
from __future__ import annotations

import numpy as np
import soundfile as sf
from scipy import signal as sg
from scipy.signal import fftconvolve
from scipy.ndimage import maximum_filter1d

SR = 44100
rng = np.random.default_rng(11)
SOUNDFONT = '/home/claude/mrbumpy409/generaluser-gs/GeneralUser-GS.sf2'


def seed(n: int):
    global rng
    rng = np.random.default_rng(n)


# ----------------------------------------------------------------------------- basics
def smp(t): return int(round(t * SR))
def tt(n): return np.arange(n) / SR
def mtof(m): return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)
def db(x): return 10 ** (x / 20)
def lp(x, f, o=2): return sg.sosfilt(sg.butter(o, min(f, SR * .45), 'low', fs=SR, output='sos'), x, axis=-1)
def hp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'high', fs=SR, output='sos'), x, axis=-1)
def bp(x, lo, hi, o=2): return sg.sosfilt(sg.butter(o, [lo, min(hi, SR * .45)], 'bandpass', fs=SR, output='sos'), x, axis=-1)
def norm(x): m = np.max(np.abs(x)); return x / m if m > 0 else x


def stereo(y, pan=0.0):
    """Mono to stereo with equal-power pan (-1 left .. +1 right)."""
    if y.ndim == 2:
        return y
    a = (pan + 1) * np.pi / 4
    return np.stack([y * np.cos(a), y * np.sin(a)]) * 1.4142


def autopan(y, a=-0.7, b=0.7):
    ang = (np.linspace(a, b, len(y)) + 1) * np.pi / 4
    return np.stack([y * np.cos(ang), y * np.sin(ang)]) * 1.4142


class Bus:
    """A stereo track you drop sounds onto at times."""
    def __init__(self, dur: float, tail: float = 3.0):
        self.n = smp(dur)
        self.x = np.zeros((2, self.n + smp(tail)))
        self.hits: list[float] = []

    def add(self, t, y, g=1.0, pan=0.0, mark=False):
        i = smp(t)
        y = stereo(np.asarray(y, float), pan)
        if i < 0:
            y = y[:, -i:]; i = 0
        k = min(y.shape[1], self.x.shape[1] - i)
        if k > 0:
            self.x[:, i:i + k] += y[:, :k] * g
        if mark:
            self.hits.append(t)
        return self

    def out(self, with_tail=False):
        return self.x if with_tail else self.x[:, :self.n]


# ----------------------------------------------------------------------------- oscillators
def saw(freq, n, ph0=None):
    """Band-limited sawtooth (PolyBLEP). freq may be a scalar or a per-sample array."""
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    dt = f / SR
    ph = ((rng.random() if ph0 is None else ph0) + np.cumsum(dt) - dt) % 1.0
    y = 2 * ph - 1
    m = ph < dt; x = ph[m] / dt[m]; y[m] -= x + x - x * x - 1
    m = ph > 1 - dt; x = (ph[m] - 1) / dt[m]; y[m] -= x * x + x + x + 1
    return y


def square(freq, n, width=0.5):
    ph = rng.random()
    return saw(freq, n, ph) - saw(freq, n, (ph + width) % 1.0)


def sine(freq, n, ph0=0.0):
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    return np.sin(2 * np.pi * (ph0 + np.cumsum(f) / SR))


def tri(freq, n):
    """Triangle (soft, few harmonics; naive shape is fine since its harmonics fall off fast)."""
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    ph = (rng.random() + np.cumsum(f) / SR) % 1.0
    return lp(4 * np.abs(ph - 0.5) - 1, SR * 0.4)


def noise(n, color='white'):
    x = rng.standard_normal(n)
    if color == 'pink':
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]; a = [1, -2.494956002, 2.017265875, -0.522189400]
        x = sg.lfilter(b, a, x) * 8
    elif color == 'brown':
        x = np.cumsum(x); x = hp(x, 20) / 60
    return x


def adsr(n, a=0.005, d=0.1, s=0.8, r=0.05, hold=None):
    t = tt(n); hold = n / SR - r if hold is None else hold
    e = np.where(t < a, t / max(a, 1e-5), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip((t - hold) / max(r, 1e-4), 0, 1)
    return e * (1 - rel)


def lp_sweep(x, fc, q=0.707, blk=64):
    """Lowpass whose cutoff follows the array fc (Hz, per sample)."""
    out = np.zeros_like(x); zi = np.zeros(2)
    fc = np.broadcast_to(np.asarray(fc, float), (len(x),)) if np.ndim(fc) == 0 else np.pad(fc, (0, max(0, len(x) - len(fc))), 'edge')
    for b in range(0, len(x), blk):
        f = min(float(fc[b]), SR * .45)
        w0 = 2 * np.pi * f / SR; al = np.sin(w0) / (2 * q); cw = np.cos(w0)
        bb = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2]) / (1 + al)
        aa = np.array([1, -2 * cw / (1 + al), (1 - al) / (1 + al)])
        out[b:b + blk], zi = sg.lfilter(bb, aa, x[b:b + blk], zi=zi)
    return out


def bp_sweep(x, fc, q=1.2, blk=128):
    out = np.zeros_like(x); zi = np.zeros(2)
    for b0 in range(0, len(x), blk):
        f = float(fc[min(b0, len(fc) - 1)]); w0 = 2 * np.pi * min(f, SR * .45) / SR; al = np.sin(w0) / (2 * q)
        bb = np.array([al, 0, -al]) / (1 + al); aa = np.array([1, -2 * np.cos(w0) / (1 + al), (1 - al) / (1 + al)])
        out[b0:b0 + blk], zi = sg.lfilter(bb, aa, x[b0:b0 + blk], zi=zi)
    return out


# ----------------------------------------------------------------------------- instruments
def supersaw(notes, dur, cutoff=5000, voices=7, spread=0.22, a=0.01, d=0.3, s=0.85, r=0.12, cut_arr=None, low_cut=140):
    """Detuned saw stack, spread across the stereo field. Big pads and chord stabs."""
    n = smp(dur + r); L = np.zeros(n); R = np.zeros(n)
    notes = [notes] if np.ndim(notes) == 0 else notes
    for m in notes:
        for v in range(voices):
            k = v / max(voices - 1, 1) - 0.5
            y = saw(mtof(m + spread * 2 * k), n)
            pan = 0.5 + 0.9 * k if v % 2 else 0.5 - 0.9 * k
            L += y * np.sqrt(1 - pan); R += y * np.sqrt(pan)
    env = adsr(n, a, d, s, r, dur)
    st = np.stack([L, R]) / (voices * len(notes)) ** 0.5
    st = np.stack([lp_sweep(st[c], cut_arr) for c in range(2)]) if cut_arr is not None else lp(st, cutoff, 2)
    return hp(st * env, low_cut)


def pluck(m, dur=0.22, bright=6500, dark=900, fdec=0.07, adec=0.22, sq=0.5):
    """Synth pluck: bright attack that darkens fast. Arps."""
    n = smp(dur + 0.05)
    x = saw(mtof(m), n) + sq * square(mtof(m) * 1.003, n)
    e = np.exp(-tt(n) / fdec)
    y = lp(x, dark) * (1 - e) + lp(x, bright) * e
    return y * np.exp(-tt(n) / adec) * np.clip(tt(n) / 0.002, 0, 1) * np.clip((n / SR - tt(n)) / 0.03, 0, 1)


def karplus(m, dur=1.5, bright=0.5, damp=0.996):
    """Plucked string (Karplus-Strong). Guitar/harp-like."""
    n = smp(dur); f = float(mtof(m)); p = max(2, int(round(SR / f)))
    buf = lp(rng.uniform(-1, 1, p * 4), 1000 + 9000 * bright)[:p]
    y = np.zeros(n); y[:p] = buf
    for i in range(p, n):
        y[i] = damp * 0.5 * (y[i - p] + y[i - p + 1])
    return y * np.clip((n / SR - tt(n)) / 0.05, 0, 1)


def bell(m, dur=1.2, ratio=3.5, idx=2.2, dec=0.5):
    """FM bell/glass."""
    n = smp(dur); t = tt(n); f = float(mtof(m))
    mod = np.sin(2 * np.pi * f * ratio * t) * idx * np.exp(-t / 0.12)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t / dec) * np.clip(t / 0.002, 0, 1)


def epiano(m, dur=1.4, vel=0.8):
    """FM electric piano (tine-ish)."""
    n = smp(dur); t = tt(n); f = float(mtof(m))
    mod = np.sin(2 * np.pi * f * t) * (1.2 + 2.5 * vel) * np.exp(-t / 0.25)
    tine = np.sin(2 * np.pi * f * 14 * t) * 0.08 * vel * np.exp(-t / 0.02)
    y = np.sin(2 * np.pi * f * t + mod) + tine
    return y * np.exp(-t / (0.9 - 0.004 * (m - 60))) * np.clip(t / 0.002, 0, 1) * np.clip((n / SR - t) / 0.08, 0, 1)


def pop_note(m, dur=0.25):
    """Bubbly UI pop with a pitch blip."""
    n = smp(dur); t = tt(n); f = float(mtof(m))
    fr = f * (1 + 0.5 * np.exp(-t / 0.006))
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(fr * 2) / SR) * np.exp(-t / 0.03)
    return y * np.exp(-t / 0.09) * np.clip(t / 0.001, 0, 1)


def soft_pad(notes, dur, a=1.2, r=1.5, bright=1800, drift=0.08):
    """Slow, warm pad: filtered saws with slow detune drift and a breathing filter."""
    n = smp(dur + r); t = tt(n)
    L = np.zeros(n); R = np.zeros(n)
    notes = [notes] if np.ndim(notes) == 0 else notes
    for j, m in enumerate(notes):
        for side, sgn in ((L, -1), (R, 1)):
            wob = drift * np.sin(2 * np.pi * (0.07 + 0.013 * j) * t + rng.random() * 6) * sgn
            side += saw(mtof(m + wob), n) + 0.5 * saw(mtof(m + 12.03 + wob), n)
    breath = bright * (1 + 0.35 * np.sin(2 * np.pi * 0.11 * t))
    st = np.stack([lp_sweep(L, breath), lp_sweep(R, breath)]) / (2 * len(notes)) ** 0.5
    env = np.minimum(1, t / a) * np.clip((dur + r - t) / r, 0, 1)
    return hp(st * env, 90)


def bass_note(m, dur, bright=1700, sub=0.3, glide_from=None):
    """Punchy synth bass with a sine sub. Returns mono."""
    n = smp(dur + 0.03)
    f = mtof(m) if glide_from is None else mtof(m + (glide_from - m) * np.exp(-tt(n) / 0.03))
    x = saw(f, n) * 0.8 + 0.3 * square(f * (0.5 if m > 40 else 1), n)
    e = np.exp(-tt(n) / 0.06)
    y = lp(x, 380) * (1 - e) + lp(x, bright) * e
    s = sine(mtof(m if m < 40 else m - 12), n) * sub
    return hp((y + s) * adsr(n, 0.003, 0.15, 0.75, 0.03, dur), 32)


def lead(events, dur, glide=0.012, vib=0.13, bright=6500, octave=0):
    """Monophonic lead that glides between notes. events: [(time, midi, length)]."""
    n = smp(dur) + SR
    target = np.zeros(n); gate = np.zeros(n); age = np.zeros(n)
    for t, m, d in events:
        a, b = smp(t), smp(t + d * 0.9)
        target[a:b] = m + 12 * octave; gate[a:b] = 1; age[a:b] = tt(b - a)
    idx = np.nonzero(target)[0]
    if not len(idx):
        return np.zeros(smp(dur))
    fill = np.interp(np.arange(n), idx, target[idx])
    a = np.exp(-1 / (glide * SR)); pitch = sg.lfilter([1 - a], [1, -a], fill, zi=[fill[0] * a])[0]
    v = vib * np.clip((age - 0.18) / 0.2, 0, 1) * np.sin(2 * np.pi * 5.6 * tt(n))
    f = mtof(pitch + v)
    x = saw(f * 2 ** (7 / 1200), n) + saw(f * 2 ** (-7 / 1200), n) + 0.55 * square(f, n)
    k1, k2 = np.exp(-1 / (0.006 * SR)), np.exp(-1 / (0.05 * SR))
    env = np.minimum(sg.lfilter([1 - k1], [1, -k1], gate), sg.lfilter([1 - k2], [1, -k2], gate) * 4)
    return hp(lp(x, bright, 2) * env, 250)[:smp(dur)]


# ----------------------------------------------------------------------------- drums
_sf = None


def sfhit(note, kit=25, vel=115, dur=1.8, program=None, bank=128, channel=9):
    """One-shot from the GeneralUser GS soundfont. Drums: bank 128, kit 25 = TR-808, 26 = TR-909, 0 = standard.
    For a melodic instrument pass bank=0, program=<GM program>, channel=0."""
    import tinysoundfont
    global _sf
    if _sf is None:
        syn = tinysoundfont.Synth(samplerate=SR, gain=0)
        _sf = (syn, syn.sfload(SOUNDFONT))
    syn, sid = _sf
    syn.program_select(channel, sid, bank, kit if program is None else program, channel == 9)
    syn.noteon(channel, note, vel)
    hold = min(0.15, dur) if channel == 9 else dur * 0.8
    a = np.frombuffer(syn.generate(smp(hold)), dtype=np.float32).reshape(-1, 2)
    syn.noteoff(channel, note)
    b = np.frombuffer(syn.generate(smp(dur - hold)), dtype=np.float32).reshape(-1, 2)
    syn.generate(smp(0.5))
    return np.concatenate([a, b]).T.astype(float)


def kick(pitch=52, punch=115, dec=0.17, click=0.35, drive=1.6):
    n = smp(0.5); t = tt(n)
    f = pitch + punch * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec)
    c = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.004) * click
    return norm(np.tanh((body + c) * drive))


def snare(tone=190, snap=0.6, dec=0.14):
    n = smp(0.4); t = tt(n)
    body = np.sin(2 * np.pi * np.cumsum(tone + 60 * np.exp(-t / 0.01)) / SR) * np.exp(-t / 0.05)
    nz = bp(rng.standard_normal(n), 1800, 9000) * np.exp(-t / dec) * snap
    return norm(body * 0.6 + nz)


def hat(open_=False, bright=8000):
    n = smp(0.5 if open_ else 0.08); t = tt(n)
    x = sum(square(f, n) for f in (205.3, 304.4, 369.6, 522.7, 540, 800))
    return norm(hp(bp(x, bright * 0.8, 16000), 7000) * np.exp(-t / (0.18 if open_ else 0.018)))


def kit(which='808'):
    """A dict of drum one-shots. '808' / '909' use the soundfont; 'synth' is built from scratch."""
    if which in ('808', '909'):
        k = 25 if which == '808' else 26
        return {'kick': norm(sfhit(35, k, 120)), 'snare': norm(sfhit(38, k)), 'clap': norm(sfhit(39, k)),
                'hat': norm(sfhit(42, k)), 'ohat': norm(sfhit(46, k)), 'crash': norm(sfhit(49, k, 110, 3.0)),
                'tom': norm(sfhit(45, k)), 'rim': norm(sfhit(37, k)), 'shaker': norm(sfhit(70, k, 100)), 'tamb': norm(sfhit(54, k, 90))}
    return {'kick': kick(), 'snare': snare(), 'hat': hat(), 'ohat': hat(True)}


def impact(dur=1.6):
    n = smp(dur); t = tt(n)
    sub = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-t / 0.12)) / SR) * np.exp(-t / 0.5)
    return np.tanh(sub * 1.3)


def riser(dur, f0=300, f1=9000):
    n = smp(dur); p = tt(n) / dur
    out = bp_sweep(rng.standard_normal(n), f0 * (f1 / f0) ** p, 1.2)
    tone = saw(220 * 2 ** (2 * p), n) * 0.15
    return norm(out + lp(tone, 3000)) * p ** 1.8


def whoosh(dur, f0, f1, q=1.2):
    n = smp(dur); p = tt(n) / dur
    return norm(bp_sweep(rng.standard_normal(n), f0 * (f1 / f0) ** p, q) * np.sin(np.pi * p) ** 2)


# ----------------------------------------------------------------------------- effects
def ducker(hit_times, dur, depth=0.6, rel=0.13):
    """Sidechain gain curve: dips on each hit (kick) and recovers. Multiply a bus by it."""
    n = smp(dur); g = np.ones(n)
    for t in hit_times:
        i = smp(t); L = smp(0.42)
        q = tt(L); curve = 1 - depth * np.clip(q / 0.004, 0, 1) * np.exp(-np.maximum(q - 0.004, 0) / rel)
        j = min(n, i + L)
        if j > i:
            g[i:j] = np.minimum(g[i:j], curve[:j - i])
    return g


def plate(dur=2.4, decay=0.55, pre=0.02, lo=250, hi=7000):
    n = smp(dur); t = tt(n); irs = []
    for _ in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / decay)
        ir = lp(hp(ir, lo), hi); ir[:smp(pre)] = 0; irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return irs


def hall(dur=5.0, decay=1.6, pre=0.035, lo=180, hi=5000):
    return plate(dur, decay, pre, lo, hi)


def reverb(x, irs, wet=0.5):
    x = stereo(x)
    return np.stack([fftconvolve(x[c], irs[c])[:x.shape[1]] for c in range(2)]) * wet


def pingpong(x, d=0.375, fb=0.38, taps=5, lo=400, hi=5000):
    x = stereo(x)
    out = np.zeros_like(x); ds = smp(d); m = x.mean(0)
    for k in range(1, taps + 1):
        i = ds * k
        if i >= x.shape[1]:
            break
        out[(k + 1) % 2, i:] += m[:-i] * fb ** (k - 1)
    return lp(hp(out, lo), hi)


def chorus(x, rate=0.6, depth_ms=3.0, mix=0.5):
    x = stereo(x); n = x.shape[1]; t = tt(n); out = np.zeros_like(x)
    for c in range(2):
        d = (depth_ms / 1000 * SR) * (1 + np.sin(2 * np.pi * rate * t + c * np.pi / 2)) / 2 + smp(0.008)
        idx = np.arange(n) - d
        out[c] = np.interp(idx, np.arange(n), x[c], left=0)
    return x * (1 - mix) + out * mix


def saturate(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)


def bitcrush(x, bits=8, down=4):
    q = 2 ** (bits - 1)
    y = np.round(x * q) / q
    return np.repeat(y[..., ::down], down, axis=-1)[..., :x.shape[-1]]


def glue(x, thr=-16, ratio=2.0, rel=0.2):
    """Gentle bus compression."""
    x = stereo(x)
    k = np.exp(-1 / (0.02 * SR))
    e = np.sqrt(sg.lfilter([1 - k], [1, -k], (x ** 2).mean(0)))
    lvl = 20 * np.log10(e + 1e-9)
    gr = -np.maximum(0, lvl - thr) * (1 - 1 / ratio)
    a = np.exp(-1 / (rel * SR)); g = sg.lfilter([1 - a], [1, -a], gr)
    return x * 10 ** (np.minimum(g, 0) / 20)


def biquad(kind, f0, gain_db=0.0, q=0.7):
    A = 10 ** (gain_db / 40); w0 = 2 * np.pi * f0 / SR; al = np.sin(w0) / (2 * q); cw = np.cos(w0)
    if kind == 'peak':
        b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind == 'lowshelf':
        sa = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cw + sa), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sa)]
        a = [(A + 1) + (A - 1) * cw + sa, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sa]
    else:
        sa = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * cw + sa), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sa)]
        a = [(A + 1) - (A - 1) * cw + sa, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sa]
    return np.array(b) / a[0], np.array(a) / a[0]


def eq(x, bands):
    """bands: [('lowshelf'|'peak'|'highshelf', freq, gain_db, q), ...]"""
    for kind, f0, g, q in bands:
        b, a = biquad(kind, f0, g, q); x = sg.lfilter(b, a, x, axis=-1)
    return x


def limiter(x, ceiling=0.80, look=0.004, rel=0.06):
    """True-peak-aware (4x oversampled) look-ahead limiter."""
    x = stereo(x)
    up = np.stack([sg.resample_poly(x[c], 4, 1) for c in range(2)])
    peak = np.max(np.abs(up), axis=0)[:x.shape[1] * 4].reshape(-1, 4).max(axis=1)
    envl = maximum_filter1d(peak, size=smp(look) * 2 + 1)
    g = np.minimum(1.0, ceiling / np.maximum(envl, 1e-9))
    a = np.exp(-1.0 / (rel * SR)); gs = np.empty_like(g); cur = 1.0
    for i, v in enumerate(g.tolist()):
        cur = v if v < cur else cur * a + v * (1 - a); gs[i] = cur
    d = smp(look); gs = np.concatenate((gs[d:], np.full(d, gs[-1])))
    return x * gs


def master(m, lufs=-14.0, tone=None, fade=0.6, ceiling=0.80):
    """Loudness-targeted master: high-pass, optional EQ, soft saturation, limiter, fade-out."""
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    m = hp(stereo(m), 28, 2)
    if tone:
        m = eq(m, tone)
    m = lp(m, 16500, 4)
    g = 0.0
    for _ in range(4):
        y = limiter(np.tanh(m * 10 ** (g / 20) * 1.1) / 1.1, ceiling)
        g += lufs - meter.integrated_loudness(y.T)
    y = limiter(np.tanh(m * 10 ** (g / 20) * 1.1) / 1.1, ceiling)
    if fade:
        f = smp(fade); y[:, -f:] *= np.linspace(1, 0, f) ** 1.5
    return np.clip(y, -ceiling - 0.02, ceiling + 0.02)


def write(path, x, sr=SR):
    sf.write(path, stereo(x).T.astype(np.float32), sr, subtype='PCM_16')
    return path
