"""Sound for the Gimli Glider Short (no voice yet). Beat times come straight from gimli.timeline().

    python3 studio/toon/shorts/gimli_sound.py out.wav   (needs studio/instruments + studio/sfx from studio/ponzi)
"""
import os, sys, subprocess, tempfile
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.environ.get('STUDIO_ROOT', os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, ROOT)
from studio.instruments import synth as S
import gimli

SR = 44100
K = os.path.join(ROOT, 'studio', 'sfx', 'samples')
TL, D = gimli.timeline()
B = [t0 for (t0, d, fn, l) in TL]
DUR = [d for (t0, d, fn, l) in TL]
N = int(D * SR)
fx = np.zeros((2, N)); mus = np.zeros((2, N))


def ld(p):
    t = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ac', '1', '-ar', str(SR), t])
    x, _ = sf.read(t); os.unlink(t); return x


def k(cat, i=0):
    d = os.path.join(K, cat); fs = sorted(os.listdir(d)); return ld(os.path.join(d, fs[i % len(fs)]))


def put(buf, x, t, db, pan=0.0):
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
    a = int(t * SR); b = min(N, a + x.shape[1])
    if b > a:
        buf[:, a:b] += x[:, :b - a] * 10 ** (db / 20)


def jet(dur, wind_down=None):
    """Jet cabin roar; optionally spooling down from wind_down seconds."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = S.lp(np.random.default_rng(2).standard_normal(n), 900) + 0.25 * S.bp(np.random.default_rng(3).standard_normal(n), 2500, 6000)
    whine = 0.08 * np.sin(2 * np.pi * np.cumsum(np.full(n, 1800.0)) / SR)
    g = np.ones(n)
    if wind_down is not None:
        p = np.clip((t - wind_down) / 1.2, 0, 1)
        g = 1 - p
        whine = 0.08 * np.sin(2 * np.pi * np.cumsum(1800 * (1 - 0.7 * p)) / SR) * (1 - p)
    return S.norm(x + whine) * g


def wind(dur):
    n = int(dur * SR)
    return S.norm(S.bp(np.random.default_rng(5).standard_normal(n), 300, 2200)) * (0.7 + 0.3 * np.sin(np.arange(n) / SR * 1.3))


def tick():
    return S.pop_note(100, 0.04)


# beat-by-beat
put(fx, jet(DUR[0] + 0.5, wind_down=0.8), B[0], -14)
put(fx, k('rooms/metal_hit', 1), B[0] + 0.8, -12)
put(fx, S.whoosh(1.2, 2000, 200), B[1], -12)
put(fx, wind(DUR[1]), B[1], -24)
put(fx, k('rooms/slam', 2), B[2] + 0.25, -8)                     # MATH MISTAKE stamp
put(fx, S.whoosh(0.6, 5000, 400), B[3], -10)                      # rewind
for j in range(4):
    put(fx, S.pop_note(52, 0.12), B[3] + 0.8 + j * 0.33, -16)      # dead-gauge buzz blinks
put(fx, k('rooms/metal_hit', 3), B[4] + 0.7, -14)                  # dipstick
put(fx, k('rooms/metal_hit', 4), B[4] + 2.0, -16)
put(fx, k('rooms/pen', 1), B[5] + 0.4, -10)
put(fx, k('rooms/pen', 3), B[5] + DUR[5] * 0.45, -10)
put(fx, k('rooms/slam', 4), B[5] + DUR[5] * 0.45 + 0.1, -9)        # red X
put(fx, k('water/splash', 2), B[6] + 0.2, -14)                     # fuel pouring
put(fx, S.bell(52, 1.4), B[6] + DUR[6] * 0.62, -10)                # LESS THAN HALF
put(fx, jet(DUR[7], wind_down=0.6), B[7], -15)
put(fx, wind(DUR[7] + DUR[8]), B[7] + 1.5, -18)
for j in range(5):
    put(fx, S.pop_note(88 - j, 0.08), B[8] + 0.3 + j * 0.2, -18, (j - 2) * 0.3)
put(fx, S.bell(84, 1.2) + 0.5 * S.bell(91, 1.2), B[9] + 1.0, -14)  # glider idea
put(fx, k('rooms/lock', 0), B[10] + 0.05, -10)                     # RAT drops
put(fx, S.lp(np.random.default_rng(8).standard_normal(int(DUR[10] * SR)), 1200) * 0.5, B[10] + 0.4, -18)
put(fx, wind(DUR[10] + DUR[11]), B[10], -22)
for j in range(10):
    put(fx, tick(), B[11] + j * DUR[11] * 0.08, -20)
put(fx, S.bell(79, 1.0), B[11] + DUR[11] * 0.85, -12)
# race day: engines zooming past, crowd
for j in range(4):
    put(fx, S.whoosh(1.0, 300, 3000), B[12] + 0.4 + j * 1.1, -12, (-0.8 if j % 2 else 0.8))
put(fx, S.riser(DUR[12] * 0.45, 200, 3000), B[12] + DUR[12] * 0.55, -14)
put(fx, wind(DUR[13]), B[13], -12)
put(fx, S.riser(DUR[13], 300, 5000), B[13], -14)
# landing: touch, gear fold, scrape, stop
put(fx, S.impact(1.2), B[14] + 0.1, -6)
put(fx, k('rooms/metal_slam', 0), B[14] + 0.5, -4)
sc = S.bp(np.random.default_rng(9).standard_normal(int((DUR[14] * 0.85 - 0.5) * SR)), 1500, 7000)
put(fx, sc * np.linspace(1, 0.2, sc.shape[0]), B[14] + 0.5, -12)
for j in range(6):
    put(fx, k('war/debris', j), B[14] + 0.6 + j * 0.5, -16, (j - 2.5) * 0.3)
put(fx, k('rooms/slam', 6), B[14] + DUR[14] * 0.86, -8)
put(fx, wind(2.0), B[14] + DUR[14] - 1.0, -16)                      # air settling after the stop
# slides and cheers
for j in range(4):
    put(fx, S.whoosh(0.5, 600, 2400), B[15] + 0.3 + j * 0.35, -16)
put(fx, k('rooms/slam', 7), B[15] + 0.3, -9)                      # NOBODY DIED stamp
put(fx, k('rooms/pen', 5), B[16] + 0.5, -12)
put(fx, jet(1.2)[:int(1.2 * SR)] * np.linspace(0, 1, int(1.2 * SR)), D - 1.2, -16)   # roar pre-laps into the loop

# music: tense pulse for the setup, drop out at the shutdown, hopeful after the glider idea, lift at the end
def pad(notes, t0, t1, db, bright=1600):
    p = S.soft_pad(notes, t1 - t0, a=0.4, r=0.3, bright=bright)
    put(mus, p[:, :int((t1 - t0) * SR)], t0, db)

pad([45, 52, 57, 60], 0.0, B[1] - 0.05, -18)
pad([40, 47, 52], B[1] + 0.6, B[3], -19, 900)
pad([45, 52, 55, 60], B[3] + 0.3, B[7] - 0.05, -19, 1300)
for j in range(int((B[7] - B[3]) / 0.5)):
    put(mus, S.kick(pitch=48, punch=90), B[3] + 0.3 + j * 0.5, -20)
pad([38, 45, 50], B[7] + 0.8, B[9] + 0.9, -19, 800)
pad([50, 57, 62, 66], B[9] + 1.0, B[14], -19, 2200)
for j in range(int((B[14] - B[12]) / 0.25)):
    put(mus, S.hat(), B[12] + j * 0.25, -24, 0.3)
pad([43, 50, 55, 59], B[15], D, -18, 2600)

mix = S.hp(fx, 50) + S.hp(mus, 60)
mix = mix - 0.4 * S.lp(mix, 200)
mix = np.tanh(mix / np.max(np.abs(mix)) * 2.0) / np.tanh(2.0) * 10 ** (-1.5 / 20)
out = sys.argv[1] if len(sys.argv) > 1 else 'gimli_mix.wav'
raw = out + '.raw.wav'
sf.write(raw, mix.T, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af',
                'equalizer=f=450:t=o:w=1.2:g=-5,equalizer=f=1000:t=o:w=1:g=-3,highshelf=f=5000:g=3,loudnorm=I=-14:TP=-2:LRA=11', '-ar', '44100', out])
os.unlink(raw)
print('ok', round(D, 2))
