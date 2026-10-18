"""Sound for the elevator Short (no voice yet): effects per beat + music with cuts."""
import os, sys, subprocess, tempfile
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # repo root (needs studio/instruments + studio/sfx from studio/ponzi)
from studio.instruments import synth as S

SR = 44100
K = os.path.join(os.path.dirname(__file__), '..', '..', 'sfx', 'samples') + '/'
D = 52.0
N = int(D * SR)
fx = np.zeros((2, N)); mus = np.zeros((2, N))
C = dict(snap=0.0, rewind=3.0, cables=6.0, cutall=10.0, black=14.0, bomber=17.0, lobby=21.0,
         frayed=26.0, fall=29.0, pit=33.0, crash=38.0, medal=44.0, doors=48.0, end=52.0)


def ld(p):
    t = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ac', '1', '-ar', str(SR), t])
    x, _ = sf.read(t); os.unlink(t); return x


def k(cat, i=0):
    d = K + cat; fs = sorted(os.listdir(d)); return ld(os.path.join(d, fs[i % len(fs)]))


def put(buf, x, t, db, pan=0.0):
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
    a = int(t * SR); b = min(N, a + x.shape[1])
    if b > a:
        buf[:, a:b] += x[:, :b - a] * 10 ** (db / 20)


def snap():
    """Steel cable letting go: a sharp crack plus a twang that drops in pitch."""
    n = int(1.2 * SR); t = np.arange(n) / SR
    crack = S.hp(np.random.default_rng(1).standard_normal(n), 2500) * np.exp(-t / 0.02)
    f = 180 * np.exp(-t / 0.4) + 60
    tw = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.5) * 0.6
    tw += 0.3 * np.sin(2 * np.pi * np.cumsum(f * 2.7) / SR) * np.exp(-t / 0.25)
    return S.norm(crack * 1.2 + tw)


def hiss(dur):
    n = int(dur * SR)
    return S.norm(S.bp(np.random.default_rng(3).standard_normal(n), 2500, 9000)) * np.clip(np.arange(n) / (0.1 * SR), 0, 1) * np.clip((n - np.arange(n)) / (0.3 * SR), 0, 1)


def engine(dur):
    """Prop bomber drone, getting louder (and a touch higher) as it nears."""
    n = int(dur * SR); t = np.arange(n) / SR; p = t / dur
    f = 92 * (1 + 0.06 * p)
    x = S.saw(f, n) + 0.6 * S.saw(f * 1.5, n) + 0.5 * S.lp(np.random.default_rng(4).standard_normal(n), 400)
    am = 1 + 0.3 * np.sin(2 * np.pi * 16 * t)
    return S.norm(S.lp(x * am, 1400)) * (0.15 + 0.85 * p ** 2)


# 1. snap + drop
put(fx, snap(), C['snap'] + 0.7, -3)
put(fx, S.impact(), C['snap'] + 0.7, -6)
put(fx, S.whoosh(2.0, 200, 3000), C['snap'] + 0.9, -10)
put(fx, k('rooms/metal_hit', 0), C['snap'] + 0.72, -9, 0.3)
# 2. rewind
put(fx, S.whoosh(1.8, 4000, 300), C['rewind'] + 0.3, -7)
put(fx, S.pop_note(84), C['rewind'] + 0.05, -14)
# 3. six cables, pop each
for j in range(6):
    put(fx, S.pop_note(67 + j * 2), C['cables'] + 0.4 + j * 0.45, -11, -0.5 + j * 0.2)
put(fx, S.bell(91, 1.5), C['cables'] + 0.4 + 6 * 0.45, -16)
# 4. all cut, brakes bite
put(fx, snap(), C['cutall'] + 0.5, -4)
put(fx, k('rooms/metal_slam', 1), C['cutall'] + 1.05, -2)
put(fx, S.impact(), C['cutall'] + 1.05, -6)
for j in range(10):
    put(fx, k('rooms/keyclick', j), C['cutall'] + 1.05 + j * 0.05, -16, np.sin(j) * 0.7)   # sparks
put(fx, k('rooms/chain', 0), C['cutall'] + 1.1, -14)
# 5. black, wind
w = k('weather/wind', 0)
put(fx, np.tile(w, 3)[:int(7 * SR)] * np.clip(0.35 + np.arange(int(7 * SR)) / SR / 1.5, 0, 1), C['black'], -10)
# 6. bomber
put(fx, engine(2.05), C['bomber'], -6)
put(fx, k('war/explosion', 0), C['bomber'] + 2.0, -1)
put(fx, S.impact(2.0), C['bomber'] + 2.0, -3)
for j in range(4):
    put(fx, k('war/debris', j), C['bomber'] + 2.2 + j * 0.35, -12, (j - 1.5) * 0.4)
put(fx, k('weather/fire', 0)[:int(2 * SR)], C['bomber'] + 2.1, -15)
# 7. lobby: steps, low heartbeat
for j in range(10):
    put(fx, k('people/step_stone', j), C['lobby'] + 0.3 + j * 0.45, -15, (-0.3 if j % 2 else 0.3))
for j in range(4):
    hb = S.impact(0.5) * 0.7
    put(fx, hb, C['lobby'] + 1.0 + j * 1.0, -12); put(fx, hb * 0.6, C['lobby'] + 1.22 + j * 1.0, -14)
# 8. frayed cables
put(fx, k('rooms/creak', 0), C['frayed'] + 0.3, -10)
put(fx, snap() * 0.5, C['frayed'] + 1.4, -10)
# 9. fall: long riser + floor ticks
put(fx, S.riser(4.0, 200, 6000), C['fall'], -8)
for j in range(40):
    tj = C['fall'] + 4.0 * (j / 40) ** (1 / 1.6)
    put(fx, S.pop_note(96, 0.05), tj, -24, (j % 2) * 0.6 - 0.3)
# 10. coil + air
put(fx, k('rooms/chain', 1), C['pit'] + 0.3, -9)
put(fx, k('rooms/chain', 0), C['pit'] + 1.4, -11)
put(fx, hiss(3.5), C['pit'] + 1.2, -14)
# 11. crash, dust, survived
put(fx, k('rooms/metal_slam', 0), C['crash'] + 0.02, 0)
put(fx, S.impact(2.0), C['crash'], -2)
for j in range(5):
    put(fx, k('war/debris', j + 3), C['crash'] + 0.1 + j * 0.2, -10, (j - 2) * 0.3)
put(fx, k('rooms/slam', 3), C['crash'] + 2.2, -6)                                 # SURVIVED stamp
# 12. medal
put(fx, k('rooms/coins', 2), C['medal'] + 0.1, -8)
for j, m in enumerate((79, 84, 88, 91)):
    put(fx, S.bell(m, 1.5), C['medal'] + 0.4 + j * 0.12, -14)
# 13. doors, ding, pre-lap snap into the loop
put(fx, S.whoosh(1.2, 300, 1200), C['doors'] + 0.3, -16)
put(fx, k('rooms/door_close', 0), C['doors'] + 2.45, -9)
put(fx, S.bell(88, 1.6) + 0.6 * S.bell(84, 1.6), C['doors'] + 2.6, -8)
put(fx, snap()[:int(0.25 * SR)], C['end'] - 0.15, -8)

# music: tense pad, calm stem on the rewind/explainer, hard cut at "all of that failed", low pad after
def pad(notes, t0, t1, db, bright=1500):
    p = S.soft_pad(notes, t1 - t0, a=0.5, r=0.3, bright=bright)
    put(mus, p[:, :int((t1 - t0) * SR)], t0, db)

pad([45, 52, 57, 60], 0.0, 0.68, -16)                   # tense, cut on the snap
pad([45, 52, 60, 63], 0.95, 3.0, -17)
pad([57, 64, 67, 72], 3.4, 13.95, -18, 2400)           # calm: good news
pad([38, 45, 50], 15.0, 19.9, -17, 900)                # low, foggy
pad([38, 45, 50, 53], 21.0, 37.9, -18, 1200)
pad([50, 57, 62, 66], 40.3, 52.0, -18, 2600)           # hopeful after SURVIVED
# pulse under the fall
for j in range(16):
    put(mus, S.kick(), C['fall'] + j * 0.25, -14)

mix = S.hp(fx, 60) + S.hp(mus, 70) * 0.9
low = S.lp(mix, 200)
mix = mix - 0.45 * low                      # tame the sub build-up from the impacts
mix = np.tanh(mix / np.max(np.abs(mix)) * 2.2) / np.tanh(2.2)   # gentle saturation keeps hits loud but controlled
mix = mix * 10 ** (-1.5 / 20)
sf.write('/root/vt/e/mix_raw.wav', mix.T, SR)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i','/root/vt/e/mix_raw.wav','-af','equalizer=f=450:t=o:w=1.2:g=-4,equalizer=f=1100:t=o:w=1:g=-2,highshelf=f=5000:g=2.5,loudnorm=I=-14:TP=-2:LRA=11','-ar','44100','/root/vt/e/mix.wav'])
print('ok')
