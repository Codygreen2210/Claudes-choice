"""Sound for the glowing marble race, driven by the physics (race.py): every marble's roll (louder as it speeds up and
nears the camera, a hollow ring in the glass corkscrew, a whirr in the funnels), a glass clack for every marble-on-marble hit,
knocks off the walls, pings on the plinko pegs, whooshes and landings on the jumps, one short cheer at the photo finish, under a racing beat (kit.hype_score).
    STUDIO_ROOT=/root/vt/kit python3 marble_sound.py cam.npz WORKDIR      -> WORKDIR/mix.wav, mix.fx.wav"""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'toon', 'shorts')); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'senses'))
from race import Race, NAMES, FPS
from kit import Mix
from sfxlib import Lib
from scipy.signal import resample_poly
import soundfile as sf, pyloudnorm as pyln, subprocess

R = Race(sys.argv[1]); W = sys.argv[2]; os.makedirs(W, exist_ok=True)
D = R.T; tj = os.path.join(W, 'times.json'); json.dump({'starts': [0.0], 'durs': [D], 'total': D}, open(tj, 'w'))
M = Mix(tj); S = M.S; SR = M.SR; N = M.N
M.PAD = 0; M.fx = np.zeros((2, N + SR * 8)); M.mus = np.zeros((2, N + SR * 8))
def put(buf, x, t, db, pan=0.0):
    if t >= D or t < -1: return
    x = np.asarray(x, float)
    if x.ndim == 1: x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
    a = int(t * SR)
    if a < 0: x = x[:, -a:]; a = 0
    b = min(buf.shape[1], a + x.shape[1]); buf[:, a:b] += x[:, :b - a] * 10 ** (db / 20)
fx = lambda x, t, db, pan=0.0: put(M.fx, x, t, db, pan)
mu = lambda x, t, db, pan=0.0: put(M.mus, x, t, db, pan)
LB = Lib(); rng = np.random.default_rng(5)
def rec(words, seed=0, dur=None, off=0.0, pick=None):
    c = LB.find(words)
    if pick: c = [e for e in c if pick.lower() in e['src'].lower()] or c
    if not c: raise LookupError(words)
    x = LB.load(c[seed % len(c)]); a0 = int(off * 48000); x = x[a0:] if a0 < len(x) - 4800 else x
    if dur: n = min(len(x), int(dur * 48000)); x = x[:n] * np.r_[np.ones(max(0, n - 1440)), np.linspace(1, 0, min(n, 1440))][:, None]
    return resample_poly(x, 147, 160, axis=0).T
def sample(words, t, db, seed=0, dur=None, pan=0.0, off=0.0, pick=None):
    try: fx(rec(words, seed, dur, off, pick), t, db, pan)
    except LookupError as e: print('no sound', e)
tt = lambda n: np.arange(n) / SR
pc = lambda f: R.pnames[int(f)] if 0 <= f < len(R.pnames) else ''

# ---------------------------------------------------------------- 1. rolling: a pool ball on polished marble, per marble
# A hard resin ball on stone is a smooth, deep rumble: rough-contact noise (brighter the faster it goes) ringing the stone
# slab's low modes, with a slow wobble at the spin rate. The glass corkscrew adds a hollow pipe ring; the real recorded
# metal-ball roll sits underneath for grit.
def lpn(fc, seed): return S.lp(np.random.default_rng(seed).standard_normal(N), fc)
DARK, MID, BRT = lpn(260, 1), lpn(900, 2), S.bp(np.random.default_rng(3).standard_normal(N), 900, 4200) * 0.5
fr_t = np.arange(R.N) / FPS; at = tt(N)
rollS = np.zeros((2, N)); rollG = np.zeros((2, N))
for i in range(8):
    g = np.zeros(R.N); pan = np.zeros(R.N); kind = np.zeros(R.N)
    for f in range(R.N):
        gg, pp = R.near(f, R.pos[f, i]); g[f] = max(gg, 0.22); pan[f] = pp
        nm = R.pnames[R.piece[f, i]] if R.piece[f, i] >= 0 else ''
        kind[f] = 1 if nm == 'corkscrew' else 0
    v = R.speed[:, i]
    amp = np.clip(v / 2.2, 0, 1.3) ** 1.15 * g * (~R.air[:, i])
    A = np.interp(at, fr_t, amp); P = np.interp(at, fr_t, pan); K = np.interp(at, fr_t, kind); V = np.interp(at, fr_t, np.clip(v / 3.0, 0, 1))
    sh = (i * 7919) % (N // 3)
    src = np.roll(DARK, sh) * 0.9 + np.roll(MID, sh) * (0.3 + 0.7 * V) + np.roll(BRT, sh) * (0.15 + V ** 2) * 1.1
    spin = np.cumsum(np.interp(at, fr_t, v) / (2 * np.pi * 0.05)) / SR
    src = src * (0.78 + 0.22 * np.sin(2 * np.pi * spin) + 0.06 * np.sin(4 * np.pi * spin + 1.3))
    lg = A * np.sqrt(0.5 - P / 2); rg = A * np.sqrt(0.5 + P / 2)
    rollS[0] += src * lg * (K < 0.5); rollS[1] += src * rg * (K < 0.5)
    rollG[0] += src * lg * (K >= 0.5); rollG[1] += src * rg * (K >= 0.5)
def resonate(x, modes):
    from scipy.signal import iirpeak, lfilter
    y = np.zeros_like(x)
    for f0, q, gn in modes:
        b, a = iirpeak(f0, q, fs=SR); y += lfilter(b, a, x, axis=-1) * gn
    return y
STONE = [(150, 10, 0.35), (233, 12, 0.5), (340, 14, 0.7), (490, 16, 0.75), (705, 18, 0.6), (1010, 20, 0.45), (1450, 22, 0.3), (2080, 24, 0.18)]
PIPE = [(640, 25, 0.8), (1290, 30, 0.6), (1930, 35, 0.45), (2580, 40, 0.3)]
roll = rollS * 0.6 + resonate(rollS, STONE) * 1.0 + rollG * 0.5 + resonate(rollG, PIPE) * 1.3
roll = S.hp(roll, 85); roll = roll / (np.max(np.abs(roll)) + 1e-9)
M.fx[:, :N] += roll * 10 ** (-11 / 20)
try:
    mb = rec('metallic ball rolling', 0, pick='Metallic ball rolling')
    lvl = np.sqrt(np.convolve((roll ** 2).sum(0), np.ones(4410) / 4410, 'same')); lvl /= lvl.max() + 1e-9
    reps = int(np.ceil(N / mb.shape[1])) + 1; lp_ = S.lp(np.tile(mb, (1, reps))[:, :N], 5000)
    M.fx[:, :N] += lp_ / (np.max(np.abs(lp_)) + 1e-9) * lvl * 10 ** (-23 / 20)
except LookupError as e: print('no roll loop', e)

# ---------------------------------------------------------------- 2. hits
def clack(s, seed):
    r = np.random.default_rng(seed); n = int(0.09 * SR); t = tt(n); x = np.zeros(n)
    for k, (f0, dec) in enumerate(((2300, 0.022), (3700, 0.016), (5600, 0.010), (1500, 0.03))):
        x += np.sin(2 * np.pi * f0 * r.uniform(0.9, 1.12) * t) * np.exp(-t / dec) * (1.0, 0.7, 0.45, 0.5)[k]
    x += r.standard_normal(n) * np.exp(-t / 0.002) * 0.6
    return x
def knock(s, seed):
    r = np.random.default_rng(seed); n = int(0.12 * SR); t = tt(n)
    x = np.sin(2 * np.pi * r.uniform(380, 620) * t) * np.exp(-t / 0.035) + np.sin(2 * np.pi * r.uniform(1100, 1500) * t) * np.exp(-t / 0.015) * 0.5
    return x + S.bp(r.standard_normal(n), 800, 5000) * np.exp(-t / 0.006) * 0.5
import glob as _g
MHITS = [sf.read(p)[0] for p in sorted(_g.glob(os.path.join(sys.argv[2], 'hits', 'metal_*.wav')))]
MHITS = [resample_poly(h if h.ndim == 1 else h.mean(1), 147, 160) for h in MHITS if len(h) > 0.1 * 48000]
def plate(seed, ring):
    r = np.random.default_rng(seed); n = int((0.25 + 0.5 * ring) * SR); t = tt(n); x = np.zeros(n); b = r.uniform(0.9, 1.15)
    for f0, dec, g_ in ((520, 0.30, 1.0), (1345, 0.22, 0.8), (2210, 0.16, 0.6), (3480, 0.11, 0.45), (5130, 0.07, 0.3), (7020, 0.05, 0.2)):
        x += np.sin(2 * np.pi * f0 * b * r.uniform(0.98, 1.02) * t + r.uniform(0, 6.28)) * np.exp(-t / (dec * (0.4 + ring))) * g_
    return x * 0.5
def clang(s, seed):
    r = np.random.default_rng(seed); h = MHITS[r.integers(len(MHITS))].copy() if MHITS else knock(s, seed)
    ring = float(np.clip(s / 1.5, 0.15, 1.0)); pl = plate(seed, ring); n = max(len(h), len(pl)); x = np.zeros(n)
    x[:len(h)] += h; x[:len(pl)] += pl * (0.35 + 0.4 * ring); return x
def ping(seed):
    r = np.random.default_rng(seed); n = int(0.35 * SR); t = tt(n); f0 = r.uniform(1700, 2300)
    return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.76 * t) * np.exp(-t / 0.05)) * np.exp(-t / 0.12)
last = np.full(8, -9.0); n_h = 0
for f, kind, s, i, j in R.hits:
    t = f / FPS; g, pan = R.near(f, R.pos[f, i])
    if kind == 'mm':
        db = -16 + 20 * np.log10(min(s, 1.5) / 0.4 + 1e-3) * 0.6 + 20 * np.log10(g + 1e-4)
        fx(clack(s, f * 13 + i), t, min(db, -6), pan); n_h += 1
        if s > 0.5 and g > 0.35: sample('billiards strike hit ball', t - 0.01, db - 4, pick='strike hit ball')
        continue
    if s < 0.42: continue                                   # just rolling round a curve, not a hit
    if t - last[i] < 0.09: continue
    last[i] = t; nm = R.pnames[R.piece[f, i]]
    db = -24 + 20 * np.log10(min(s, 2.5) / 0.5) * 0.8 + 20 * np.log10(g + 1e-4)
    if db < -44: continue
    if nm == 'plinko': fx(ping(f * 7 + i) * 0.7 + np.pad(clang(s, f * 7 + i), (0, 0))[:int(0.35 * SR)] * 0.5, t, db + 3, pan)
    elif nm == 'corkscrew': fx(clack(s, f + i) * 0.6, t, db - 2, pan)
    elif s >= 0.6: fx(clang(s, f * 5 + i), t, db - 1, pan)
    else: fx(S.hp(clang(0.3, f * 5 + i)[:int(0.12 * SR)], 1500), t, db - 9, pan)
    n_h += 1
print('hits placed', n_h)

# ---------------------------------------------------------------- 3. jumps: whoosh off the lip, a crowd "ooh", landings
done_k = set()
for k, i, f0, f1 in R.jumps:
    g, pan = R.near(f0, R.pos[f0, i]); t0 = f0 / FPS; t1 = f1 / FPS
    fx(S.whoosh(0.45, 500, 2600), t0 - 0.05, -22 + 20 * np.log10(g + 1e-3) * 0.5, pan)
    g1, p1 = R.near(f1, R.pos[f1, i]); fx(clang(1.5, f1), t1, -13 + 20 * np.log10(g1 + 1e-3) * 0.6, p1)
    fx(clack(1.0, f1 + 3), t1 + 0.012, -20 + 20 * np.log10(g1 + 1e-3) * 0.6, p1)
    if k not in done_k:
        done_k.add(k)
        fx(S.impact(0.8), t1, -24)

# ---------------------------------------------------------------- 4. funnels: a spinning whirr that rises as they circle in
for nm in ('vortex1', 'vortex2'):
    pi = R.pnames.index(nm); inside = (R.piece == pi)
    fs = np.where(inside.any(axis=1))[0]
    if not len(fs): continue
    a, b = fs[0] / FPS, fs[-1] / FPS; n = int((b - a + 0.5) * SR); t = tt(n)
    cnt = np.interp(a + t, fr_t, inside.sum(axis=1)); gg = np.interp(a + t, fr_t, [R.near(f, R.pos[f].mean(0))[0] for f in range(R.N)])
    rate = 2.5 + 6.0 * (t / (b - a + 0.5)) ** 2
    x = S.bp(np.random.default_rng(9).standard_normal(n), 300, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(rate) / SR)) * np.sqrt(cnt / 8) * gg
    fx(x * M.env(n, 0.4, 0.4), a, -15)
    sample('coin spin', b - 3.0, -24, pick='Coin_Wood', dur=3.2, off=4.0)
    for f in fs[::1]:
        pass
    # each drop through the hole: a hollow thunk
    for i in range(8):
        w = np.where(inside[:, i])[0]
        if len(w): f = w[-1]; g, p = R.near(f, R.pos[f, i]); fx(S.lp(knock(1, f), 900) * 1.5, f / FPS + 0.15, -15 + 20 * np.log10(g + 1e-3) * 0.6, p)

# ---------------------------------------------------------------- 5. the race calls: start, lead changes, the finish
sample('air horn', 0.0, -18, pick='Air Horn', dur=1.2)
fx(S.impact(1.0), 0.0, -18); fx(S.whoosh(0.5, 300, 3000), 0.02, -20)
for f, i in R.lead_changes:
    t = f / FPS; fx(S.whoosh(0.25, 800, 3500), t - 0.12, -22); fx(S.bell(88, 0.6, dec=0.25), t, -21); fx(S.bell(95, 0.7, dec=0.3), t + 0.08, -22)
T_WIN = R.t_win; T_LAST = R.t_last
sample('crowd cheer', T_WIN - 0.1, -17, seed=0, dur=6.0, pick='Big Surge')
fx(S.impact(1.6), T_WIN, -12)
for k_, i in enumerate(R.order_final):
    f = R.fin[i]; fx(S.bell(84 + (k_ == 0) * 7, 0.8, dec=0.3), f / FPS, -18 if k_ else -12)
sample('air horn', T_WIN + 0.05, -16, pick='Air Horn', dur=1.5)

# ---------------------------------------------------------------- 6. camera moves: soft whoosh when the camera starts a new move
plan = json.load(open(os.path.join(W, 'plan.json'))) if os.path.exists(os.path.join(W, 'plan.json')) else []
for tp in plan[1:]: fx(S.whoosh(0.9, 250, 1800), tp - 0.2, -25)

# ---------------------------------------------------------------- 7. music: a racing beat, building into each jump, a stop at the line
k1 = min(f for k, i, f, _ in R.jumps if k == 0) / FPS; k2 = min(f for k, i, f, _ in R.jumps if k == 1) / FPS; k3 = min(f for k, i, f, _ in R.jumps if k == 2) / FPS
M.mus = M.mus; M.D = D
M.hype_score(bpm=128, key=57, db=-17, anchor=k3, plan=[
    (0.0, 52.0, 'full'), (52.0, 60.0, 'light'), (60.0, T_WIN - 0.05, 'full'),
    (T_WIN - 0.05, T_WIN + 1.6, 'stop'), (T_WIN + 1.6, D + 1, 'full')])
for kt in (k1, k2, k3): fx(S.riser(3.2), kt - 3.2, -17); fx(S.impact(1.2), kt + 0.35, -19)
mus = M.mus[:, :N]; fxb = M.fx[:, :N]
# fade the beat out over the last 2.5 s, the crowd carries the end
fo = np.clip((D - at) / 2.5, 0, 1); mus = mus * fo

# ---------------------------------------------------------------- mix: effects on top, the beat 6 dB under them, -14 LUFS, peaks under -1 dBTP
rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-9
fxb = S.hp(fxb, 40); mus = S.hp(mus, 45)
# level the effects: lift the quiet stretches (far camera, single file) so there's no dead air, then glue
fxb = fxb / np.max(np.abs(fxb)) * 0.5
w_ = int(1.5 * SR); ev = np.sqrt(np.convolve((fxb ** 2).mean(0), np.ones(w_) / w_, 'same')) + 1e-6
gain = np.clip(np.median(ev) / ev, 1.0, 3.0); gain = np.convolve(gain, np.ones(SR // 2) / (SR // 2), 'same'); fxb = fxb * gain
fxb = S.glue(fxb, thr=-24, ratio=2.5, rel=0.25)
mus = mus / rms(mus) * rms(fxb) * 10 ** (-4.5 / 20)
mix = fxb + mus
sf.write(os.path.join(W, 'mix.fx.wav'), (fxb / np.max(np.abs(mix))).T, SR)
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.1) / np.tanh(1.1)
raw = os.path.join(W, 'mix.raw.wav'); eq = os.path.join(W, 'mix.eq.wav'); sf.write(raw, mix.T, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'lowshelf=f=110:g=-3,equalizer=f=320:t=o:w=1.4:g=-3.5,equalizer=f=650:t=o:w=1.2:g=-2.5,highshelf=f=3500:g=1.5,equalizer=f=900:t=o:w=1.2:g=-1.0,equalizer=f=3800:t=o:w=1.4:g=-3', '-ar', str(SR), eq], check=True)
out = os.path.join(W, 'mix.wav')
st = subprocess.run(['ffmpeg', '-hide_banner', '-i', eq, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=14:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
js = json.loads(st[st.rindex('{'):st.rindex('}') + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=14:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
      f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', eq, '-af', af, '-ar', '48000', '-c:a', 'pcm_s16le', out + '.48.wav'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', out + '.48.wav', '-af', 'alimiter=limit=0.82:level=false:attack=2:release=60', '-ar', str(SR), out], check=True)
os.unlink(raw); os.unlink(eq); os.unlink(out + '.48.wav')
print('mix:', os.path.join(W, 'mix.wav'), round(D, 2), 's')
