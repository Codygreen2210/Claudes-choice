"""Sound for the style samples. All DSP is ours: foley edits, crater echo built from the pit size,
binaural placement, doppler, procedural lava/rock, an original score, mastering.
   python3 audio.py <level 1|2|3> <out.wav>"""
import sys, os, math
import numpy as np
import soundfile as sf
import scipy.signal as sg
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.environ.get('STUDIO_ROOT', os.path.expanduser('~/vt/kit'))
sys.path.insert(0, KIT)
from studio.instruments import synth as S

SR = S.SR
DUR = 5.0
N = int(DUR * SR)
SAMP = os.path.join(KIT, 'studio/sfx/samples')
rng = np.random.default_rng(5)
G = 9.81
T_AIR, V_AIR = 1.30, np.array([0.9, -1.2])
CRACK = 0.76


def tt(n): return np.arange(n) / SR


_LOADED = {}


def load(rel, i=0):
    if (rel, i) in _LOADED:
        return _LOADED[(rel, i)].copy()
    import glob, os
    fs = sorted(glob.glob(f'{SAMP}/{rel}/*'))
    src = fs[i % len(fs)]
    cache = f'{HERE}/cache/{rel.replace("/", "_")}_{i % len(fs)}_{int(os.path.getmtime(src))}.npy'
    if os.path.exists(cache):
        x = np.load(cache)
    else:
        x, sr = sf.read(src, always_2d=True)
        x = x.mean(1)
        if sr != SR:
            x = sg.resample_poly(x, SR, sr)
        os.makedirs(os.path.dirname(cache), exist_ok=True); np.save(cache, x)
    _LOADED[(rel, i)] = x / (np.max(np.abs(x)) + 1e-9)
    return _LOADED[(rel, i)].copy()


def pitch(x, ratio):
    """Resample (tape-style speed change): ratio<1 = lower and slower."""
    n = int(len(x) / ratio)
    return np.interp(np.arange(n) * ratio, np.arange(len(x)), x)


def voice():
    v, sr = sf.read(os.path.join(HERE, 'voice.wav'))
    if v.ndim > 1:
        v = v.mean(1)
    v = v[:N]
    return np.pad(v, (0, N - len(v)))


def env_follow(x, att=0.01, rel=0.25):
    a, r = math.exp(-1 / (att * SR)), math.exp(-1 / (rel * SR))
    e = np.abs(x)
    # fast block approximation
    out = np.zeros_like(e); y = 0.0
    blk = 64
    for i in range(0, len(e), blk):
        m = e[i:i + blk].max()
        c = a ** blk if m > y else r ** blk
        y = c * y + (1 - c) * m
        out[i:i + blk] = y
    return out


def duck_curve(v, depth_db=-7):
    e = env_follow(v)
    e = e / (e.max() + 1e-9)
    k = np.clip(e * 3, 0, 1)
    return 10 ** (depth_db * k / 20)


def speed(t):
    tau = np.maximum(np.asarray(t) - T_AIR, 0)
    return np.where(np.asarray(t) > T_AIR, np.hypot(V_AIR[0], -V_AIR[1] + G * tau), 0.0)


def put(bus, t, y, g=1.0):
    i = int(round(t * SR))
    y = np.atleast_2d(y)
    if y.shape[0] == 1:
        y = np.vstack([y, y])
    if i < 0:
        y = y[:, -i:]; i = 0
    k = min(y.shape[1], bus.shape[1] - i)
    if k > 0:
        bus[:, i:i + k] += y[:, :k] * g


def pan(y, p):
    a = (p + 1) * np.pi / 4
    return np.vstack([y * math.cos(a), y * math.sin(a)]) * 1.4142


# ------------------------------------------------------------------ the crater's own echo
def crater_ir(dur=3.2, r_pit=32.0, depth=80.0, seed=3):
    """Impulse response from the pit geometry: slap-back off the far wall (~2x diameter / c),
    side-wall reflections, then a dark diffuse tail.  Stereo: left/right walls differ."""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    irs = []
    c = 343.0
    for ch in range(2):
        ir = np.zeros(n)
        ir[0] = 1.0
        far = 2 * (2 * r_pit) / c                    # across the pit and back
        for k, (d, g) in enumerate([(far, 0.42), (far * 2, 0.16), (far * 3, 0.06)]):
            j = int((d + r.uniform(-0.01, 0.01)) * SR)
            if j < n:
                burst = r.standard_normal(int(0.012 * SR)) * np.hanning(int(0.012 * SR))
                ir[j:j + len(burst)] += burst * g * (0.9 if ch else 1.0)
        for _ in range(40):                        # side walls and ledges
            d = r.uniform(0.02, far * 0.9)
            j = int(d * SR)
            ir[j] += r.uniform(-1, 1) * 0.25 * math.exp(-d / 0.4)
        tail = r.standard_normal(n) * np.exp(-tt(n) / 0.55) * np.clip((tt(n) - 0.05) / 0.2, 0, 1) * 0.35
        tail = S.lp(tail, 2600)
        ir = S.lp(ir, 5200) + tail
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return irs


def conv(x, irs, wet):
    x = np.atleast_2d(x)
    if x.shape[0] == 1:
        x = np.vstack([x, x])
    return np.stack([fftconvolve(x[ch], irs[ch])[:x.shape[1]] for ch in range(2)]) * wet


# ------------------------------------------------------------------ sound pieces
def lava_bed(n, dist=1.0, seed=1):
    """Low roar + distant blorps.  dist: 1 far .. 0 close (array or scalar)."""
    r = np.random.default_rng(seed)
    b = np.cumsum(r.standard_normal(n)); b = S.hp(b, 18); b = S.lp(b, 140); b /= np.abs(b).max() + 1e-9
    am = S.lp(r.standard_normal(n), 2); am = 0.7 + 0.3 * am / (np.abs(am).max() + 1e-9)
    out = b * am
    blorps = np.zeros(n)
    t = 0.0
    while t < n / SR:
        L = int(r.uniform(0.12, 0.3) * SR); x = tt(L)
        f0 = r.uniform(45, 90)
        y = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.4 * x / x[-1])) / SR) * np.exp(-x / 0.07) * np.clip(x / 0.01, 0, 1)
        i = int(t * SR)
        k = min(L, n - i)
        blorps[i:i + k] += y[:k] * r.uniform(0.3, 1)
        t += r.uniform(0.12, 0.45)
    return out * 0.8 + S.lp(blorps, 500) * 0.5


def crack_hit(seed=2):
    r = np.random.default_rng(seed)
    n = int(0.5 * SR); x = tt(n)
    snap = S.bp(r.standard_normal(n), 900, 7000) * np.exp(-x / 0.012)
    body = np.sin(2 * np.pi * 70 * x * (1 + 0.6 * np.exp(-x / 0.02))) * np.exp(-x / 0.09)
    grit = S.bp(r.standard_normal(n), 300, 3000) * np.exp(-x / 0.12) * (r.random(n) > 0.92)
    return S.norm(snap * 1.0 + body * 0.8 + grit * 0.6)


def fall_wind(n, t0=0.0, seed=4, stereo_=True):
    """Rushing air that follows his real speed; turbulence + cloth flutter.  Returns (2,n)."""
    r = np.random.default_rng(seed)
    t = t0 + tt(n)
    v = speed(t); k = np.clip(v / 36, 0, 1)
    outs = []
    for ch in range(2):
        w = r.standard_normal(n)
        lo = S.lp(w, 400) * 1.0
        hi = S.bp(w, 700, 5000) * 0.35
        turb = S.lp(r.standard_normal(n), 6); turb = 0.6 + 0.4 * turb / (np.abs(turb).max() + 1e-9)
        flut_rate = 18 + 6 * k
        ph = np.cumsum(flut_rate) / SR
        flut = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * ph + ch))) * S.bp(r.standard_normal(n), 150, 900)
        y = (lo * (0.3 + k) + hi * k ** 1.5 + flut * 0.5 * k) * turb * k ** 1.2
        outs.append(y)
    return np.vstack(outs) / (np.abs(np.vstack(outs)).max() + 1e-9)


def voice_chain(v, pro=False):
    if not pro:
        return v
    v = S.hp(v, 85, 2)
    v = S.eq(v, [('peak', 280, -2.5, 1.0), ('peak', 3400, 2.5, 0.9), ('highshelf', 10000, 1.5, 0.7)]) if hasattr(S, 'eq') else v
    # de-ess: duck 5-9 kHz band when it spikes
    band = S.bp(v, 5000, 9000)
    e = env_follow(band, 0.002, 0.05); thr = np.percentile(e, 92)
    g = np.where(e > thr, thr / (e + 1e-9), 1.0) ** 0.6
    v = v - band * (1 - g)
    # 3:1 compressor
    e = env_follow(v, 0.005, 0.12) + 1e-9
    thr = np.percentile(e[e > 1e-4], 60)
    g = np.where(e > thr, (thr / e) ** (1 - 1 / 3), 1.0)
    v = v * g
    return np.tanh(v * 1.6 / (np.abs(v).max() + 1e-9)) / 1.6 * np.abs(v).max()


# ------------------------------------------------------------------ level 1: foley + crater echo + ducking
def level1():
    v = voice()
    fx = np.zeros((2, N)); amb = np.zeros((2, N)); mus = np.zeros((2, N))
    # bed: lava far below, wind across the rim (recorded)
    lb = lava_bed(N)
    near = np.clip((tt(N) - 1.3) / 3.7, 0, 1)
    amb += np.vstack([lb, np.roll(lb, 900)]) * (0.25 + 0.55 * near)
    wnd = load('weather/wind', 0); wnd = np.tile(wnd, 3)
    amb += np.vstack([wnd[20000:20000 + N], wnd[90000:90000 + N]]) * 0.18 * (1 - 0.6 * near)
    # foot scuff as he leans, then the crack and the rock giving way (recorded + built)
    put(fx, 0.58, pan(pitch(load('people/step_stone', 1), 0.9), -0.1), 0.35)
    put(fx, CRACK, pan(crack_hit(), 0.15), 0.6)
    put(fx, CRACK + 0.01, pan(load('war/debris', 2), 0.2), 0.35)
    for j, (dt, g) in enumerate([(0.18, 0.4), (0.42, 0.28), (0.75, 0.18), (1.2, 0.1)]):
        y = S.lp(load('war/debris', 4 + j), 6000 - 1100 * j)       # falling away: darker, quieter
        put(fx, CRACK + dt, pan(y, 0.25 + 0.1 * j), g)
    # arm flings and the tip-over: cloth whooshes
    for t0, d, f0, f1, g in [(0.84, 0.28, 400, 2200, 0.35), (1.0, 0.3, 2400, 500, 0.3), (1.28, 0.45, 300, 1800, 0.4)]:
        put(fx, t0, pan(S.whoosh(d, f0, f1), 0.1), g)
    # the fall: wind at his real speed
    wl = fall_wind(N - int(1.25 * SR), 1.25)
    put(fx, 1.25, wl, 0.55)
    put(fx, 1.80, pan(S.whoosh(0.22, 3000, 400), 0), 0.45)          # cut
    # music: low pad, sub hit on the slip, riser into the fall
    pad = S.soft_pad([40, 47, 52, 55], DUR, a=0.6, r=0.6, bright=900)
    put(mus, 0, S.stereo(pad, 0), 0.22)
    put(mus, CRACK, S.impact(1.6), 0.3)
    put(mus, 1.9, S.stereo(S.riser(3.1, 200, 5000), 0), 0.28)
    # space: everything outside the voice sits in the crater echo
    irs = crater_ir()
    sfx = fx + amb
    sfx = sfx + conv(sfx, irs, 0.45)
    dk = duck_curve(v, -9)
    LAST[:] = [(sfx + mus) * dk, np.vstack([v, v])]
    mix = (sfx + mus) * dk + np.vstack([v, v]) * 1.0
    return mix


# ------------------------------------------------------------------ binaural engine (ours)
HEAD_A, C_AIR = 0.0875, 343.0


def _onepole_shelf(alpha, beta):
    """Brown-Duda head-shadow filter, bilinear: H(s) = (alpha*s/w + 1)/(s/w + 1)."""
    b = np.array([alpha * beta + 1, 1 - alpha * beta]) / (beta + 1)
    a = np.array([1.0, (1 - beta) / (beta + 1)])
    return b, a


def binaural(x, P, fps=30, blk=512, air=True):
    """Place mono x on a moving path. P: (F,3) positions in camera space (x right, y up, -z ahead), metres.
    Distance delay per ear gives real doppler; ITD (Woodworth), head shadow (Brown-Duda), pinna elevation notch,
    air absorption and 1/r loss.  Returns (2, len(x))."""
    n = len(x)
    P = np.asarray(P, float)
    tf = np.arange(len(P)) / fps
    ts = np.arange(n) / SR
    px, py, pz = (np.interp(ts, tf, P[:, k]) for k in range(3))
    r = np.sqrt(px ** 2 + py ** 2 + pz ** 2) + 1e-3
    ux, uy = px / r, py / r
    lat = np.arcsin(np.clip(ux, -1, 1))
    el = np.arcsin(np.clip(uy, -1, 1))
    itd = HEAD_A / C_AIR * (lat + np.sin(lat))
    idx = np.arange(n, dtype=float)
    yL = np.interp(idx - (r / C_AIR + itd / 2) * SR, idx, x, left=0, right=0)
    yR = np.interp(idx - (r / C_AIR - itd / 2) * SR, idx, x, left=0, right=0)
    g = (1.0 / np.maximum(r, 1.0)) ** 0.7     # softened inverse-distance (film convention)
    out = np.zeros((2, n))
    w0 = C_AIR / HEAD_A
    beta = SR / w0          # K/(2*w0) with K=2*SR
    zs = {k: None for k in ('L', 'R', 'nL', 'nR', 'aL', 'aR')}
    starts = np.arange(0, n, blk)
    cnt = np.diff(np.append(starts, n))
    MUX = np.add.reduceat(ux, starts) / cnt; MEL = np.add.reduceat(el, starts) / cnt
    MPZ = np.add.reduceat(pz, starts) / cnt; MR = np.add.reduceat(r, starts) / cnt
    for bi, i0 in enumerate(starts):
        i1 = min(n, i0 + blk)
        m = slice(i0, i1)
        for ch, y, earx in ((0, yL, -1.0), (1, yR, 1.0)):
            key = 'LR'[ch]
            cth = np.clip(MUX[bi] * earx, -1, 1)
            th = np.degrees(np.arccos(cth))
            alpha = 1.05 + 0.95 * np.cos(np.radians(th * 180 / 150))
            b, a = _onepole_shelf(alpha, beta)
            # pinna: a notch that rises with elevation (above = higher notch), stronger in front
            e = MEL[bi]
            fn = float(np.clip(7500 + 5000 * e / (np.pi / 2), 4500, 12500))
            front = 1.0 if (-MPZ[bi]) > 0 else 0.5
            bb, aa = S.biquad('peak', fn, -9 * front, 2.2)
            b, a = np.convolve(b, bb), np.convolve(a, aa)       # cascade -> one filter call per block
            if air:   # air absorption: farther = darker
                fc = float(np.clip(21000 / (1 + MR[bi] / 30), 1800, 20000))
                k = math.exp(-2 * math.pi * fc / SR)
                b, a = np.convolve(b, [1 - k]), np.convolve(a, [1, -k])
            zi = zs[key] if zs[key] is not None else np.zeros(len(a) - 1)
            seg, zs[key] = sg.lfilter(b, a, y[m], zi=zi)
            out[ch, m] = seg * g[m]
    return out


def track(path=None):
    path = path or os.path.join(HERE, 'track2.json')
    import json
    return json.load(open(path))


def path_of(TR, key, add=(0, 0, 0)):
    return np.array([np.array(r[key]) + np.array(add) for r in TR])


def place(bus, t0, y, TR, key, gain=1.0, add=(0, 0, 0), fps=30):
    """Drop mono y at time t0 on the path of TR[key] (only the path slice it plays over)."""
    P = path_of(TR, key, add)
    f0 = int(t0 * fps)
    Pseg = P[f0:] if f0 < len(P) else P[-1:]
    put(bus, t0, binaural(y, Pseg, fps), gain)


def level2():
    TR = track()
    v = voice_chain(voice(), pro=True)
    fx = np.zeros((2, N)); amb = np.zeros((2, N)); mus = np.zeros((2, N))
    near = np.clip((tt(N) - 1.3) / 3.7, 0, 1)
    # the lake: a huge low source where it really is, with bubbles scattered across it
    lb = lava_bed(N, seed=1)
    amb += binaural(lb * 2.2, path_of(TR, 'lava')) * 1.0
    r = np.random.default_rng(9)
    tb = 0.0
    while tb < DUR:
        L = int(r.uniform(0.15, 0.35) * SR); x = tt(L); f0 = r.uniform(40, 80)
        y = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.8 * x / x[-1])) / SR) * np.exp(-x / 0.08) * np.clip(x / 0.01, 0, 1)
        y = S.lp(y + 0.3 * S.bp(r.standard_normal(L), 200, 1200) * np.exp(-x / 0.03), 1600)
        off = (r.uniform(-25, 25), r.uniform(-3, 3), r.uniform(-25, 25))
        place(amb, tb, y * 2.0, TR, 'lava', 1.0, off)
        tb += r.uniform(0.08, 0.3)
    # wind across the rim, from the left
    wnd = load('weather/wind', 0); wnd = np.tile(wnd, 3)[30000:30000 + N]
    amb += binaural(wnd * 0.5, path_of(TR, 'rimL') * 0.1) * (1 - near) * 0.6
    # foley on him and on the rock: real paths, real doppler as the rock drops away
    place(fx, 0.58, pitch(load('people/step_stone', 1), 0.9) * 0.6, TR, 'hip', 1.0, (0, -0.9, 0))
    place(fx, CRACK, crack_hit() * 1.2, TR, 'chunk')
    place(fx, CRACK + 0.01, load('war/debris', 2) * 0.8, TR, 'chunk')
    for j, dt in enumerate([0.18, 0.42, 0.75, 1.2, 1.7]):
        place(fx, CRACK + dt, load('war/debris', 4 + j) * 0.6, TR, 'chunk')
    for t0, d, f0, f1 in [(0.84, 0.28, 400, 2200), (1.0, 0.3, 2400, 500), (1.28, 0.45, 300, 1800)]:
        place(fx, t0, S.whoosh(d, f0, f1) * 0.9, TR, 'hip')
    # falling: air tearing past both ears + his clothes flapping where he is
    k0 = int(1.25 * SR)
    wl = fall_wind(N - k0, 1.25)
    put(fx, 1.25, wl, 0.2)
    flap = fall_wind(N - k0, 1.25, seed=8)[0]
    place(fx, 1.25, S.bp(flap, 200, 2500) * 1.2, TR, 'hip')
    # the wall rushing past: ledges come up from below, pass the camera, and are gone (doppler)
    tl = 1.6
    while tl < DUR - 0.1:
        f = int(tl * 30); row = TR[min(f, len(TR) - 1)]
        vsp = max(row['speed'], 1.0)
        w = np.array(row['wall']); up = np.array(row['wup'])
        dur = 0.5
        nfr = int(dur * 30) + 1
        Pp = np.array([w + up * (-vsp * (u - dur / 2)) for u in np.linspace(0, dur, nfr)])
        L = int(dur * SR)
        y = S.bp(r.standard_normal(L), 250, 3000) * np.hanning(L)
        put(fx, tl, binaural(y * 0.5 * min(vsp / 20, 1.5), Pp), 1.0)
        tl += r.uniform(0.12, 0.35) * (12 / (vsp + 6)) * 2
    put(fx, 1.80, pan(S.whoosh(0.22, 3000, 400), 0), 0.35)
    put(fx, 3.85, pan(S.whoosh(0.25, 2500, 300), 0), 0.35)
    # music: wide pad, sub on the slip, riser
    pad = S.soft_pad([40, 47, 52, 55], DUR, a=0.6, r=0.6, bright=900)
    pad = S.stereo(pad); padw = np.vstack([pad[0], np.roll(pad[1], 441)])
    put(mus, 0, padw, 0.2)
    put(mus, CRACK, S.impact(1.6), 0.15)
    put(mus, 1.9, S.stereo(S.riser(3.1, 200, 5000), 0), 0.2)
    irs = crater_ir()
    sfx = fx + amb
    sfx = sfx + conv(sfx.mean(0), irs, 0.35)
    dk = duck_curve(v, -9)
    LAST[:] = [(sfx + mus) * dk, np.vstack([v, v])]
    return (sfx + mus) * dk + np.vstack([v, v]) * 1.0


# ------------------------------------------------------------------ level 3: score + procedural design + slow-mo + master
def ACT(t):
    t = np.asarray(t, float)
    a = np.where(t < 0.62, t, 0.62 + 0.4 * (t - 0.62))
    u = t - 1.22
    a = np.where(t >= 1.22, 0.86 + 0.4 * u + 0.6 * u * u / 0.56, a)
    a = np.where(t >= 1.5, 1.056 + (t - 1.5), a)
    return a


def RATE(t):
    t = np.asarray(t, float)
    r = np.where((t >= 0.62) & (t < 1.22), 0.4, 1.0)
    return np.where((t >= 1.22) & (t < 1.5), 0.4 + 0.6 * (t - 1.22) / 0.28, r)


def real_of(a):
    ts = np.linspace(0, DUR, 5001)
    return float(np.interp(a, ACT(ts), ts))


def warp_bed(x):
    """Read an action-time bed at a(t): slow motion drops the pitch, like tape."""
    ts = tt(N)
    return np.interp(ACT(ts) * SR, np.arange(len(x)), x, right=0)


def rock_crumble(dur=1.6, density=90, seed=3):
    """Modal synthesis: hundreds of little rocks, each a few damped resonances."""
    r = np.random.default_rng(seed)
    n = int(dur * SR); out = np.zeros(n)
    t = 0.0
    while t < dur:
        k = int(t * SR)
        L = int(0.06 * SR); x = tt(L)
        g = np.zeros(L)
        size = r.uniform(0.3, 1.0) * math.exp(-t * 1.5)
        for _ in range(3):
            f = r.uniform(700, 4800) / (0.5 + size)
            g += np.sin(2 * np.pi * f * x + r.uniform(0, 6)) * np.exp(-x / r.uniform(0.006, 0.03))
        g *= size * r.uniform(0.3, 1)
        m = min(L, n - k)
        out[k:k + m] += g[:m]
        t += r.exponential(1 / (density * math.exp(-t * 1.2) + 4))
    thunk = np.zeros(n); L = int(0.4 * SR); x = tt(L)
    thunk[:L] = np.sin(2 * np.pi * 55 * x * (1 + 0.8 * np.exp(-x / 0.03))) * np.exp(-x / 0.12)
    snap = S.bp(r.standard_normal(n), 1500, 9000) * np.exp(-tt(n) / 0.01)
    return S.norm(out * 0.7 + thunk * 0.9 + snap * 0.6)


def gasp(seed=2):
    """A sharp inhale: breath noise through three mouth/throat resonances."""
    r = np.random.default_rng(seed)
    L = int(0.42 * SR); x = tt(L)
    nz = r.standard_normal(L)
    y = S.bp(nz, 700, 1000) * 1.0 + S.bp(nz, 1100, 1500) * 0.8 + S.bp(nz, 2300, 3000) * 0.5 + S.bp(nz, 4000, 7000) * 0.25
    env = np.clip(x / 0.05, 0, 1) ** 2 * np.exp(-np.maximum(x - 0.12, 0) / 0.09)
    return S.norm(y * env)


def lava_blorp(r):
    L = int(r.uniform(0.18, 0.4) * SR); x = tt(L); f0 = r.uniform(35, 75)
    body = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2.2 * (x / x[-1]) ** 1.5)) / SR) * np.exp(-x / 0.1) * np.clip(x / 0.015, 0, 1)
    pop = S.bp(r.standard_normal(L), 300, 2500) * np.exp(-np.maximum(x - x[-1] * 0.7, 0) / 0.012) * (x > x[-1] * 0.7)
    return S.lp(body + pop * 0.5, 2400)


def crust_ticks(n, rate=30, seed=6):
    r = np.random.default_rng(seed)
    out = np.zeros(n); t = 0
    while t < n / SR:
        k = int(t * SR); L = int(0.004 * SR)
        if k + L < n:
            out[k:k + L] += r.standard_normal(L) * np.hanning(L) * r.uniform(0.2, 1)
        t += r.exponential(1 / rate)
    return S.bp(out, 1800, 7000)


def note_len(t0, t1):
    return max(int((t1 - t0) * SR), 1)


def score():
    """Original cue in E minor.  Tension -> slow-motion suck-out -> braam -> driving ostinato -> riser."""
    mus = np.zeros((2, N))
    E1, E2, B1, G2, B2, E3 = 28, 40, 35, 43, 47, 52
    # 1) tension: low cluster pad + soft pulses
    pad = S.stereo(S.soft_pad([E2, B2, 55, 58], 0.9, a=0.35, r=0.5, bright=1200))
    put(mus, 0, pad, 0.25)
    for tp in (0.0, 0.31):
        put(mus, tp, S.kick(46, 90, 0.35, 0.1, 1.2), 0.35)
    # 2) suck-out at 0.62: everything drops away to one high harmonic and a slowed heartbeat
    hi = S.sine(S.mtof(83), int(0.9 * SR)) * np.clip(tt(int(0.9 * SR)) / 0.2, 0, 1) * np.exp(-tt(int(0.9 * SR)) / 0.7)
    put(mus, 0.62, pan(hi, 0), 0.05)
    put(mus, 0.6, S.impact(1.8), 0.35)
    for tb in (0.78, 1.12):
        put(mus, tb, S.kick(40, 110, 0.5, 0.05, 1.6), 0.55)
    # reverse swell into the snap back
    L = int(0.42 * SR)
    sw = S.bp(np.random.default_rng(1).standard_normal(L), 600, 9000) * (tt(L) / tt(L)[-1]) ** 3
    put(mus, 1.5 - 0.42, S.stereo(sw, 0), 0.4)
    # 3) the braam at 1.5: low supersaw stack, filter opening, driven
    d = 1.6
    br = S.supersaw([E1 + 12, E2 + 12, B2], d, cutoff=2400, voices=9, spread=0.3, a=0.02, d=0.6, s=0.7, r=0.5,
                    cut_arr=np.linspace(300, 2600, int(d * SR)) ** 1.0)
    br = np.tanh(br * 2.2)
    put(mus, 1.5, br, 0.42)
    put(mus, 1.5, S.impact(1.8), 0.45)
    put(mus, 1.5, S.kick(38, 127, 0.6, 0.3, 2.0), 0.6)
    # 4) ostinato 16ths (E minor), climbing every half bar, from 1.6 to the end
    bpm = 140; st = 60 / bpm / 4
    seq = [E3, E3 + 7, E3 + 12, E3 + 7, E3 + 3, E3 + 7, E3 + 10, E3 + 7]
    t = 1.6; i = 0
    while t < DUR:
        lift = 2 * int((t - 1.6) / (st * 16))
        m = seq[i % len(seq)] + lift
        y = S.pluck(m, dur=st * 1.6, bright=5200, dark=900)
        put(mus, t, pan(y, 0.35 if i % 2 else -0.35), 0.16 * (0.7 + 0.3 * (i % 4 == 0)))
        t += st; i += 1
    # low string bed under it
    bed = S.stereo(S.soft_pad([E2, B2, 55], DUR - 1.6, a=0.8, r=0.4, bright=900))
    put(mus, 1.6, bed, 0.18)
    # hits on the cuts, a riser to the end
    for tc in (1.95, 3.5):
        put(mus, tc, S.kick(42, 120, 0.4, 0.2, 1.6), 0.45)
        put(mus, tc, S.stereo(S.whoosh(0.3, 3000, 300), 0), 0.25)
    put(mus, 3.2, S.stereo(S.riser(1.8, 300, 9000), 0), 0.32)
    # widen: mid/side
    m_, s_ = (mus[0] + mus[1]) / 2, (mus[0] - mus[1]) / 2
    return np.vstack([m_ + s_ * 1.5, m_ - s_ * 1.5])


def multiband_glue(x):
    lo = S.lp(x, 180, 4); hi = S.hp(x, 4000, 4); mid = x - lo - hi
    out = 0
    for b, thr, ratio in ((lo, -20, 2.5), (mid, -18, 2.0), (hi, -24, 1.8)):
        e = np.maximum(env_follow(b.mean(0), 0.01, 0.15), 1e-6)
        edb = 20 * np.log10(e)
        g = np.where(edb > thr, 10 ** (-(edb - thr) * (1 - 1 / ratio) / 20), 1.0)
        out = out + b * g
    return out


def level3():
    TR = track(os.path.join(HERE, 'track3.json'))
    v = voice_chain(voice(), pro=True)
    fx = np.zeros((2, N)); amb = np.zeros((2, N))
    rate = RATE(tt(N))
    def ev(a_time, y, key, gain=1.0, add=(0, 0, 0)):
        """An event at action time: lands at its real time, pitched by the local slow-motion rate."""
        tr = real_of(a_time)
        rr = float(RATE(tr))
        place(fx, tr, pitch(y, rr) * gain, TR, key, 1.0, add)
    # lake bed (warped into slow motion), bubbles and crust ticks across the lake
    r = np.random.default_rng(13)
    lb = lava_bed(int((DUR + 0.5) * SR), seed=1)
    amb += binaural(warp_bed(lb) * 2.2, path_of(TR, 'lava'))
    ta = 0.0
    while ta < 4.6:
        off = (r.uniform(-25, 25), r.uniform(-3, 3), r.uniform(-25, 25))
        y = lava_blorp(r) * 2.2
        tr = real_of(ta)
        place(amb, tr, pitch(y, float(RATE(tr))), TR, 'lava', 1.0, off)
        ta += r.uniform(0.06, 0.25)
    ticks = crust_ticks(int((DUR + 0.5) * SR))
    amb += binaural(warp_bed(ticks) * 0.25, path_of(TR, 'lava'))
    wnd = load('weather/wind', 0); wnd = np.tile(wnd, 3)[30000:30000 + N + SR]
    amb += binaural(warp_bed(wnd) * 0.5, path_of(TR, 'rimL') * 0.1) * (1 - np.clip((tt(N) - 1.4) / 2, 0, 1)) * 0.6
    # the slip, in slow motion: stone scrape, the crack, the crumble running away from us, his gasp
    ev(0.58, pitch(load('people/step_stone', 1), 0.85) * 0.7, 'hip', 1.0, (0, -0.9, 0))
    ev(CRACK, crack_hit() * 0.55, 'chunk')
    ev(CRACK + 0.005, rock_crumble(1.8) * 0.4, 'chunk')
    ev(CRACK + 0.02, load('war/debris', 2) * 0.35, 'chunk')
    ev(0.8, gasp() * 0.55, 'hip', 1.0, (0, 0.65, 0))
    for t0, d, f0, f1 in [(0.84, 0.28, 400, 2200), (1.0, 0.3, 2400, 500), (1.28, 0.45, 300, 1800)]:
        ev(t0, S.whoosh(d, f0, f1) * 0.9, 'hip')
    # slow-motion transitions: a low suck-in and the snap back
    L = int(0.5 * SR)
    suck = S.lp(np.random.default_rng(4).standard_normal(L), 900) * np.linspace(1, 0, L) ** 2
    put(fx, 0.58, S.stereo(suck, 0), 0.25)
    put(fx, 1.3, S.stereo(S.whoosh(0.35, 300, 4000), 0), 0.3)
    # falling: air past the ears + his clothes + the wall streaming by
    k0 = 1.5
    wl = fall_wind(N - int(k0 * SR), 1.3 + 0.1)
    put(fx, k0, wl, 0.13)
    flap = fall_wind(N - int(k0 * SR), 1.4, seed=8)[0]
    place(fx, k0, S.bp(flap, 200, 2500) * 0.6, TR, 'hip')
    tl = 1.6
    while tl < DUR - 0.1:
        f = int(tl * 30); row = TR[min(f, len(TR) - 1)]
        vsp = max(row['speed'], 1.0)
        w = np.array(row['wall']); up = np.array(row['wup'])
        dur = 0.5; nfr = int(dur * 30) + 1
        Pp = np.array([w + up * (-vsp * (u - dur / 2)) for u in np.linspace(0, dur, nfr)])
        Ls = int(dur * SR)
        y = S.bp(r.standard_normal(Ls), 250, 3000) * np.hanning(Ls)
        put(fx, tl, binaural(y * 0.3 * min(vsp / 20, 1.5), Pp), 1.0)
        tl += r.uniform(0.12, 0.35) * (12 / (vsp + 6)) * 2
    # heartbeat under the fall, getting faster
    tb = 1.7
    while tb < DUR - 0.2:
        put(fx, tb, S.stereo(S.kick(44, 100, 0.25, 0.05, 1.3), 0), 0.1)
        put(fx, tb + 0.17, S.stereo(S.kick(41, 90, 0.25, 0.05, 1.3), 0), 0.07)
        tb += max(0.42, 0.75 - 0.08 * (tb - 1.7))
    mus = score() * 0.22
    irs = crater_ir()
    sfx = fx + amb
    sfx = sfx + conv(sfx.mean(0), irs, 0.35)
    dk = duck_curve(v, -11)
    bed = (sfx + mus) * dk
    LAST[:] = [bed, np.vstack([v, v])]
    mix = bed + np.vstack([v, v]) * 1.0
    return multiband_glue(mix)


LAST = []


def report():
    bed, vv = LAST
    for a, b in [(0.06, 0.7), (0.7, 1.3), (1.3, 2.5), (2.5, 3.5), (3.5, 4.3)]:
        i, j = int(a * SR), int(b * SR)
        print(f'{a:.1f}-{b:.1f} voice over bed {10 * np.log10((vv[:, i:j] ** 2).mean() / ((bed[:, i:j] ** 2).mean() + 1e-12)):5.1f} dB')


def main():
    lvl, out = int(sys.argv[1]), sys.argv[2]
    mix = {1: level1, 2: lambda: level2(), 3: lambda: level3()}[lvl]()
    if LAST:
        report()
    m = S.master(mix, lufs=-14.0, fade=0.25)
    S.write(out, m)
    print('wrote', out)


if __name__ == '__main__':
    main()
