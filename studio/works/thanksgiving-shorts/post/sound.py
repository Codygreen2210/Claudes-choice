# Sound for the two Thanksgiving Shorts: effects + a quiet score under the narration, built from scratch with the studio synth.
#   python3 sound.py turkey|coma TIMES.json NARRATION.wav OUT.wav
import sys, json, numpy as np, soundfile as sf
from scipy import signal as sg
sys.path.insert(0, '/home/claude/work/snd')
from studio.instruments import synth as S
from studio.instruments import theory as Th

name, tj, narr, out = sys.argv[1:5]
TM = json.load(open(tj)); B = TM['starts']; TOT = TM['total']
S.seed(7); rng = np.random.default_rng(3)
SR = S.SR; N = S.smp(TOT)
fx = S.Bus(TOT, 0.0); mus = S.Bus(TOT, 0.0)

def seg(a, b): return S.smp(a), S.smp(b)
def crackle(dur, rate=60, bright=5000, seed=0):
    """frying sizzle: dense random clicks through a bright band plus hiss"""
    r = np.random.default_rng(seed); n = S.smp(dur); x = np.zeros(n)
    k = r.poisson(rate * dur); idx = r.integers(0, n, k); x[idx] = r.uniform(-1, 1, k) * r.uniform(0.2, 1, k)
    x = S.bp(x, 1500, bright) + 0.06 * S.hp(S.noise(n), 3000)
    return S.norm(x)
def bubbles(dur, rate=8, lo=300, hi=900, seed=1):
    r = np.random.default_rng(seed); n = S.smp(dur); x = np.zeros(n)
    for _ in range(int(rate * dur)):
        i = r.integers(0, max(1, n - S.smp(0.08))); m = S.smp(r.uniform(0.03, 0.07)); t = S.tt(m)
        f = r.uniform(lo, hi) * (1 + 1.5 * t / t[-1])
        x[i:i + m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.02) * r.uniform(0.3, 1)
    return S.norm(x)
def env(n, pts):
    """piecewise-linear gain from [(t, g), ...] in seconds"""
    tt = np.arange(n) / SR; ts, gs = zip(*pts); return np.interp(tt, ts, gs)

if name == 'turkey':
    # sizzle bed following how hard the oil is boiling
    bed = crackle(TOT, 90, 6000, 1) * 0.5 + crackle(TOT, 30, 3000, 2) * 0.5
    g = env(len(bed), [(0, 0.15), (1.8, 0.15), (1.9, 1.0), (B[2], 0.8), (B[2] + 0.01, 0.3), (B[4], 0.45), (B[4] + 0.01, 1.0), (B[5], 1.2), (B[6], 0.6), (B[6] + 0.01, 0.0), (B[7], 0.0), (B[7] + 0.01, 0.15), (TOT, 0.15)])
    fx.add(0, bed * g, g=S.db(-17))
    # the drop: whoosh as it falls, splash + hard sizzle burst on entry (beat 0) and a sub hit
    fx.add(0.0, S.whoosh(1.9, 300, 1800), g=S.db(-15))
    fx.add(1.85, crackle(1.6, 900, 8000, 4) * np.exp(-S.tt(S.smp(1.6)) / 0.5), g=S.db(-9))
    fx.add(1.85, S.impact(1.0), g=S.db(-12))
    # cutaway beats: muffled bubbles, then steam bursts (beat 3) as each drop flashes over
    fx.add(B[2], S.lp(bubbles(B[4] - B[2], 10, 200, 600, 5), 1400), g=S.db(-16))
    for j in range(7):
        t0 = B[3] + 0.6 + j * 0.25
        hiss = S.hp(S.noise(S.smp(1.4)), 2500) * np.exp(-S.tt(S.smp(1.4)) / 0.35) * np.clip(S.tt(S.smp(1.4)) / 0.02, 0, 1)
        fx.add(t0, S.lp(S.impact(0.4), 400) * 0.6, g=S.db(-14)); fx.add(t0, hiss * 0.5, g=S.db(-14))
    fx.add(B[3] + 3.0, S.riser(B[4] - B[3] - 3.0, 200, 2500), g=S.db(-22))
    # boil-over: gurgle and a rising roar
    fx.add(B[4], bubbles(B[5] - B[4], 25, 150, 500, 6), g=S.db(-15))
    fx.add(B[4] + 1.0, S.riser(B[5] - B[4] - 1.0, 150, 4000), g=S.db(-18))
    # the fireball: impact, whoosh, and a long low roar
    fx.add(B[5], S.impact(2.4), g=S.db(-6))
    fx.add(B[5], S.whoosh(1.6, 120, 2500, 0.8), g=S.db(-9))
    n = S.smp(B[6] - B[5] + 0.8); roar = S.lp(S.noise(n, 'brown'), 500) + 0.3 * S.bp(S.noise(n), 300, 1800)
    roar = S.norm(roar) * np.minimum(1, S.tt(n) / 0.15) * np.exp(-S.tt(n) / 2.6)
    fx.add(B[5], roar, g=S.db(-9))
    # table: soft room tone and candle-quiet
    fx.add(B[6], S.lp(S.noise(S.smp(B[7] - B[6]), 'pink'), 600) * 0.3, g=S.db(-30))
    # score: low, uneasy minor pad, fading out under the fire stat; a short swell into the loop
    prog = ['Am', 'F', 'Dm', 'E']
    t = 0.0; i = 0
    while t < TOT:
        mus.add(t, S.soft_pad(Th.chord(prog[i % 4], 3), 4.6, a=0.8, r=1.2, bright=1100), g=1.0); t += 4.6; i += 1
    mg = env(mus.n, [(0, 0.8), (B[5] - 0.3, 1.0), (B[5], 0.25), (B[6], 0.6), (TOT, 0.8)])
    music = mus.out()[:, :N] * mg[:N]; music_db = -27
else:
    # gravy pour: thick, gloopy filtered noise (beat 7 start of pour, beat 0 pour)
    def pour(dur, seed):
        n = S.smp(dur); x = S.bp(S.noise(n, 'pink'), 150, 900) * (0.7 + 0.3 * np.sin(2 * np.pi * 3.1 * S.tt(n)))
        return S.norm(x + 0.5 * bubbles(dur, 6, 120, 300, seed))
    fx.add(0.0, pour(B[1] - 0.3, 1) * np.clip((B[1] - 0.3 - S.tt(S.smp(B[1] - 0.3))) / 0.6, 0, 1), g=S.db(-17))
    t_st = B[7] + (B[8] - B[7]) * 0.45 if len(B) > 8 else B[7] + 2.0
    t_st = B[7] + (TOT - B[7]) * 0.45
    fx.add(t_st, pour(TOT - t_st, 2), g=S.db(-17))
    # an hour goes by: clock ticks that speed up
    tk = S.hp(S.noise(S.smp(0.02)), 2500) * np.exp(-S.tt(S.smp(0.02)) / 0.004)
    t = B[1]; dt = 0.5
    while t < B[2]:
        fx.add(t, tk, g=S.db(-16)); t += dt; dt = max(0.12, dt * 0.93)
    # compare: three tubes fill (bubbly rise)
    for j in range(3): fx.add(B[3] + 0.3 + 0.15 * j, bubbles(1.6, 18, 400 + 200 * j, 900 + 200 * j, 10 + j), g=S.db(-22))
    # vessel: heartbeat and rushing flow
    n = S.smp(B[5] - B[4]); flow = S.lp(S.noise(n, 'pink'), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.1 * S.tt(n)) ** 2)
    fx.add(B[4], S.norm(flow), g=S.db(-22))
    t = B[4]
    while t < B[5]:
        fx.add(t, S.lp(S.impact(0.35), 120), g=S.db(-12)); fx.add(t + 0.28, S.lp(S.impact(0.3), 110), g=S.db(-16)); t += 0.9
    # stomach: low gurgles
    fx.add(B[5], S.lp(bubbles(B[6] - B[5], 5, 60, 160, 21), 400), g=S.db(-12))
    # couch: TV murmur fading out, then quiet
    n = S.smp(B[7] - B[6]); tv = S.bp(S.noise(n, 'pink'), 300, 2500) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 2.3 * S.tt(n))))
    fx.add(B[6], S.norm(tv) * np.clip(1 - (S.tt(n) - 1.5) / 3.0, 0, 1), g=S.db(-30))
    # score: warm, slow major pad (I - vi - IV - V), getting sleepier toward the couch
    prog = ['C', 'Am', 'F', 'G']
    t = 0.0; i = 0
    while t < TOT:
        mus.add(t, S.soft_pad(Th.chord(prog[i % 4], 4), 4.8, a=1.0, r=1.4, bright=1500), g=1.0); t += 4.8; i += 1
    for k, tt_ in enumerate(np.arange(0.3, TOT, 0.6 * 4)):
        mus.add(tt_, S.bell(Th.chord(prog[int(tt_ // 4.8) % 4], 5)[k % 3], 1.6), g=0.12)
    mg = env(mus.n, [(0, 0.9), (B[6], 0.9), (B[7] - 0.3, 0.45), (B[7], 0.9), (TOT, 0.9)])
    music = mus.out()[:, :N] * mg[:N]; music_db = -26

v, vsr = sf.read(narr)
if vsr != SR: v = sg.resample_poly(v, SR, vsr, axis=0)
v = v.T if v.ndim == 2 else np.stack([v, v])
L = max(N, v.shape[1])
def fit(x): y = np.zeros((2, L)); y[:, :min(L, x.shape[1])] = x[:, :L]; return y
fxo = fit(fx.out()); mo = fit(music); vo = fit(v)
# duck fx and music under the voice
ve = np.sqrt(sg.lfilter([0.002], [1, -0.998], (vo ** 2).mean(0))); duck = 1 - 0.45 * np.clip(ve / (ve.max() * 0.3), 0, 1)
mix = vo * 1.0 + fxo * duck * 1.0 + mo * S.db(music_db) / (np.abs(mo).max() + 1e-9) * duck
mix = S.limiter(mix, 0.85)
sf.write(out, mix.T, SR)
print('ok', round(L / SR, 2))
