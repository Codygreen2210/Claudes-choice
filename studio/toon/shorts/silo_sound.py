"""Sound for the silo Short: dense effects, scored music with a direction per section, narration on top.
Mixed as a circle so the end flows into the start.

    STUDIO_ROOT=<repo with studio/instruments + studio/sfx> python3 silo_sound.py times.json narration.wav out.wav

Music map (beat index -> cue):
  0-1  hook / looks solid : light plucked motif in A minor, ticking hats      (curious, a little cheeky)
  2-3  the drain / funnel : motif drops an octave, low drone + slow pulse     (something is wrong)
  4-6  sinking            : pulse doubles, strings rise, heartbeat speeds up  (panic) -> HARD CUT to silence on "gone"
  7-8  the facts          : sparse dark piano over a sub drone               (heavy, quiet)
  9-10 the crust twist    : suspense riser, everything drops out, hit on the cave-in
  11-13 the rescue        : major lift, plucks + soft drums                   (relief)
  14  loop line           : back to the hook motif, same tempo and key, so it rolls into frame one
"""
import os, sys, json, subprocess, tempfile
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('STUDIO_ROOT', os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, ROOT)
from studio.instruments import synth as S

SR = 44100
K = os.path.join(ROOT, 'studio', 'sfx', 'samples')
TM = json.load(open(sys.argv[1]))
B, DUR, D = TM['starts'], TM['durs'], TM['total']
VO = TM['voice']
N = int(round(D * SR))
PAD = 5 * SR
fx = np.zeros((2, N + PAD)); mus = np.zeros((2, N + PAD))
BPM = 96; BEAT = 60 / BPM


def ld(p):
    t = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ac', '1', '-ar', str(SR), t])
    x, _ = sf.read(t); os.unlink(t); return x


_cache = {}
def k(cat, i=0):
    d = os.path.join(K, cat); fs = sorted(os.listdir(d)); p = os.path.join(d, fs[i % len(fs)])
    if p not in _cache:
        _cache[p] = ld(p)
    return _cache[p]


def put(buf, x, t, db, pan=0.0):
    x = np.asarray(x, float)
    if x.ndim == 1:
        x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
    a = int(t * SR) % N; b = min(N + PAD, a + x.shape[1])
    buf[:, a:b] += x[:, :b - a] * 10 ** (db / 20)


def env_(n, a=0.02, r=0.1):
    t = np.arange(n) / SR
    return np.clip(t / a, 0, 1) * np.clip((n / SR - t) / r, 0, 1)


def pour(dur, lo=800, hi=3000, seed=1):
    n = int(dur * SR); r = np.random.default_rng(seed)
    x = S.bp(r.standard_normal(n), lo, hi)
    crackle = S.hp((r.random(n) < 0.006) * r.standard_normal(n) * 6, 1500)
    return S.norm(x + crackle) * env_(n, 0.2, 0.3)


def rumble(dur, f=45, seed=2):
    n = int(dur * SR); t = np.arange(n) / SR
    x = S.lp(np.random.default_rng(seed).standard_normal(n), 120) * 3 + np.sin(2 * np.pi * f * t) * 0.6
    return S.norm(x) * env_(n, 0.4, 0.6)


def grind(dur, seed=4):
    """Cut-off saw: a whining bandpassed buzz that wobbles as it bites."""
    n = int(dur * SR); t = np.arange(n) / SR
    f = 2400 + 300 * np.sin(2 * np.pi * 7 * t)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + S.bp(np.random.default_rng(seed).standard_normal(n), 2000, 7000)
    return S.norm(tone) * env_(n, 0.05, 0.2)


def swish(t, db=-15, up=True):
    put(fx, S.whoosh(0.45, 300 if up else 3000, 3000 if up else 300), t - 0.2, db)


def tick():
    return S.pop_note(98, 0.035)


def heartbeat(t0, t1, bpm0, bpm1, db):
    t = t0
    while t < t1:
        p = (t - t0) / max(t1 - t0, 1e-6)
        bpm = bpm0 + (bpm1 - bpm0) * p
        hb = S.impact(0.35)
        put(fx, hb, t, db); put(fx, hb * 0.6, t + 0.2, db - 3)
        t += 60 / bpm


# ------------------------------------------------------------------ effects
room = S.lp(np.random.default_rng(3).standard_normal(N + PAD), 250); room /= np.max(np.abs(room))
fx += np.stack([room, np.roll(room, 997)]) * 10 ** (-32 / 20)            # silo air, constant (seamless)

for i in range(1, len(B)):                                            # a swish on every cut
    swish(B[i], -17, up=i % 2 == 0)

# 0 hook: hatch creak echo, boots on grain, a pop when the hook text lands
put(fx, k('rooms/creak', 2), B[0] + 0.0, -14, -0.4)
put(fx, S.pop_note(84, 0.2), B[0] + 0.12, -12)
for j in range(3):
    put(fx, k('people/step_dirt', j), B[0] + 0.5 + j * 0.45, -12, (j % 2 - 0.5) * 0.5)
# 1 looks solid: jumps land with a crunch
for j in range(4):
    put(fx, k('people/step_grass', j), B[1] + 0.25 + j * 0.57, -9, (j % 2 - 0.5) * 0.4)
put(fx, S.pop_note(79, 0.2), B[1] + 0.1, -16)
# 2 the drain: auger starts (clank + motor), kernels stream
put(fx, k('rooms/metal_slam', 1), B[2] + 0.15, -10)
put(fx, rumble(DUR[2] + DUR[3] + DUR[4] + DUR[5] + DUR[6] * 0.7, 55, 6), B[2] + 0.2, -15)
for j in range(int(DUR[2] / 0.22)):
    put(fx, k('rooms/metal_hit', j), B[2] + 0.4 + j * 0.22, -27, 0.4)
put(fx, pour(DUR[2] + DUR[3], 1500, 6000, 2), B[2] + 0.3, -15)
# 3 funnel: the pile groans and starts to slide
put(fx, k('rooms/creak', 0), B[3] + 0.2, -11)
put(fx, S.whoosh(DUR[3], 150, 900), B[3], -13)
put(fx, pour(DUR[3] + DUR[4] + DUR[5], 600, 2500, 3), B[3] + 0.3, -11)
put(fx, S.pop_note(76, 0.2), B[3] + DUR[3] * 0.5, -15)              # FUNNEL text
# 4 knees: ticking timer, sharp sink, a gasp-like breath (filtered noise burst)
for j in range(8):
    put(fx, tick(), B[4] + j * DUR[4] / 8, -15, 0.2)
put(fx, k('people/step_wet', 0), B[4] + 0.2, -8)
put(fx, S.bp(np.random.default_rng(8).standard_normal(int(0.35 * SR)), 800, 4000) * env_(int(0.35 * SR), 0.05, 0.25), B[4] + 0.5, -14)
# 5 stuck: struggling, wet suck, pulling arrows
for j in range(6):
    put(fx, k('people/step_wet', j), B[5] + 0.1 + j * DUR[5] / 6, -10, (j % 2 - 0.5) * 0.6)
heartbeat(B[4], B[6] + DUR[6] * 0.7, 90, 160, -11)
# 6 gone: riser, the grain closes with a deep thud, then near silence
put(fx, S.riser(DUR[6] * 0.7, 150, 2500), B[6], -12)
gone = B[6] + DUR[6] * 0.72
put(fx, S.impact(2.2), gone, -5)
put(fx, k('war/debris', 1), gone + 0.05, -16)
for j in range(14):
    put(fx, tick(), B[6] + j * DUR[6] * 0.7 / 14, -18)
# 7 chest: muffled world (underwater-ish low tone), squeeze creaks, slow heavy heartbeat
put(fx, S.lp(np.random.default_rng(9).standard_normal(int(DUR[7] * SR)), 350) * 0.6 * env_(int(DUR[7] * SR), 0.5, 0.5), B[7], -14)
heartbeat(B[7] + 0.2, B[7] + DUR[7], 70, 60, -10)
for j in range(3):
    put(fx, k('rooms/wood_squeak', j), B[7] + 0.6 + j * 1.2, -18)
put(fx, k('rooms/slam', 5), B[7] + DUR[7] * 0.55, -12)              # CAN'T BREATHE stamp
# 8 force: rope strain, pulley squeak, gauge ratchets up, slam on +600
put(fx, k('rooms/chain', 0), B[8] + 0.2, -11)
put(fx, k('rooms/creak', 1), B[8] + 0.5, -12)
for j in range(12):
    put(fx, k('rooms/keyclick', j), B[8] + 0.3 + j * DUR[8] * 0.5 / 12, -17)
put(fx, k('rooms/slam', 2), B[8] + DUR[8] * 0.62, -8)
put(fx, S.bell(64, 1.2), B[8] + DUR[8] * 0.62, -17)
# 9 crust: hollow knock, dust trickle, reveal sting
for j in range(3):
    put(fx, k('rooms/knock', j), B[9] + 0.3 + j * 0.35, -12)
put(fx, pour(1.5, 3000, 9000, 11) * 0.4, B[9] + 1.0, -18)
put(fx, S.bell(57, 2.0) + 0.6 * S.bell(63, 2.0), B[9] + 1.0, -16)  # the pocket reveal
# 10 cave-in: steps, crack, collapse whoosh, impact, grain avalanche
for j in range(3):
    put(fx, k('people/step_dirt', j + 3), B[10] + 0.2 + j * 0.4, -11)
cave = B[10] + DUR[10] * 0.4
put(fx, k('rooms/wood_crack', 1), cave - 0.05, -5)
put(fx, k('rooms/wood_crack', 2), cave + 0.12, -8)
put(fx, S.whoosh(0.7, 2000, 150), cave, -9)
put(fx, S.impact(1.6), cave + 0.35, -5)
put(fx, pour(1.8, 400, 3000, 12), cave + 0.2, -6)
# 11 tube: chain lowering, metal tube clang, grain pushed back
put(fx, k('rooms/chain', 1), B[11] + 0.1, -10)
put(fx, k('rooms/metal_slam', 0), B[11] + DUR[11] * 0.6, -6)
put(fx, k('rooms/metal_hit', 3), B[11] + DUR[11] * 0.62, -10, 0.5)
put(fx, S.pop_note(83, 0.2), B[11] + DUR[11] * 0.62, -14)
# 12 scoop: bucket scrapes and pours on a rhythm, rope creak
for j in range(int(DUR[12] * 1.6)):
    tj = B[12] + j / 1.6
    put(fx, k('people/step_dirt', j), tj + 0.05, -10)
    put(fx, pour(0.35, 1500, 6000, 20 + j), tj + 0.35, -15)
# 13 cut and drain: grinder screams, sparks, grain gushes out
for j in range(3):
    put(fx, grind(0.6, 30 + j), B[13] + 0.2 + j * DUR[13] * 0.17, -13, (j - 1) * 0.6)
    put(fx, k('rooms/keyclick', j + 3), B[13] + 0.3 + j * DUR[13] * 0.17, -16)
put(fx, pour(DUR[13] * 0.6, 500, 4000, 40), B[13] + DUR[13] * 0.45, -7)
put(fx, rumble(DUR[13] * 0.6, 40, 41), B[13] + DUR[13] * 0.45, -14)
put(fx, S.pop_note(81, 0.2), B[13] + 0.1, -15)

# ------------------------------------------------------------------ music
AMIN = [57, 60, 64, 69]                     # motif notes (A minor)
def motif(t0, t1, octave=0, db=-18, dens=1):
    seq = [69, 64, 67, 64, 72, 64, 67, 64]
    t, i = t0, 0
    while t < t1:
        put(mus, S.pluck(seq[i % 8] + 12 * octave, 0.3), t, db, 0.25 * np.sin(i))
        t += BEAT / 2 * dens; i += 1

def hats(t0, t1, db=-26, step=0.5):
    t = t0
    while t < t1:
        put(mus, S.hat(), t, db, 0.4); t += BEAT * step

def drums(t0, t1, db=-18):
    t, i = t0, 0
    while t < t1:
        put(mus, S.kick(), t, db) if i % 4 in (0, 2) else None
        if i % 4 in (1, 3):
            put(mus, S.snare(), t, db - 4)
        put(mus, S.hat(), t + BEAT / 2, db - 8, 0.3)
        t += BEAT; i += 1

def pad(notes, t0, t1, db, bright=1400, a=0.35, r=0.6):
    put(mus, S.soft_pad(notes, t1 - t0 + r, a=a, r=r, bright=bright), t0, db)

gone_end = B[6] + DUR[6]
# hook + looks solid: curious plucks and ticking hats, and the same cue wraps around the loop point
motif(B[0], B[2]); hats(B[0], B[2])
pad([45, 52, 57, 60], B[0], B[2], -23, 1600)
motif(B[14], D + 0.01); hats(B[14], D); pad([45, 52, 57, 60], B[14], D, -23, 1600)
# drain + funnel: motif an octave down, slow pulse, low drone
motif(B[2], B[4], octave=-1, db=-19, dens=2)
pad([33, 40, 45], B[2], B[4], -19, 600)
for j in range(int((B[4] - B[2]) / BEAT)):
    put(mus, S.kick(pitch=44, punch=80), B[2] + j * BEAT, -22)
# sinking: pulse doubles, rising strings (supersaw with opening filter) -> hard cut at "gone"
sw_n = gone - B[4]
cut = np.linspace(400, 5000, int((sw_n + 0.2) * SR)) ** 1.0
ss = S.supersaw([45, 52, 57, 60], sw_n + 0.2, cutoff=5000, cut_arr=cut)
put(mus, ss[:, :int(sw_n * SR)], B[4], -21)
for j in range(int(sw_n / (BEAT / 2))):
    put(mus, S.kick(pitch=46, punch=100), B[4] + j * BEAT / 2, -20)
# (silence from 'gone' for a beat — only the thud rings)
# facts: sparse dark piano over a sub drone
pad([33, 40], gone_end - 0.2, B[9], -22, 500, a=1.0)
for j, m in enumerate([57, 60, 55, 53, 57, 52, 53, 52]):
    put(mus, S.epiano(m, 1.8, 0.6), gone_end + 0.3 + j * 1.05, -17)
# crust twist: suspense riser, drop out, hit on the cave-in
put(mus, S.riser(cave - B[9], 120, 3000), B[9], -18)
pad([46, 53, 58], B[9], cave - 0.05, -21, 900)
put(mus, S.impact(1.8), cave + 0.35, -10)
# rescue: major lift, plucks + soft drums, bright pad
pad([45, 52, 57, 61, 64], B[11], B[14], -20, 2600)
for t0 in np.arange(B[11] + 0.2, B[14], BEAT / 2):
    put(mus, S.pluck([69, 73, 76, 73, 81, 76, 73, 76][int((t0 - B[11]) / (BEAT / 2)) % 8], 0.3), t0, -20, 0.3)
drums(B[12], B[14], -20)

# fold tails past the end back onto the start (circular mix)
fx[:, :PAD] += fx[:, N:N + PAD]; mus[:, :PAD] += mus[:, N:N + PAD]
fx, mus = fx[:, :N], mus[:, :N]

# narration on top; effects and music duck under the voice
v = ld(sys.argv[2])[:N]
vo = np.zeros((2, N)); vo[:, :len(v)] += v
envv = np.convolve(np.abs(vo[0]), np.ones(2205) / 2205, 'same')
act = np.convolve(np.clip(envv / (np.percentile(envv, 95) + 1e-9) * 3, 0, 1), np.ones(4410) / 4410, 'same')
duck = 1 - 0.5 * act
bed = S.hp(fx, 45) * duck + S.hp(mus, 55) * (1 - 0.6 * act)
# set levels by loudness, not peaks: the bed sits 7 dB under the voice while he talks, and comes up between lines
rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-9
talk = act > 0.5
vo = vo / rms(vo[:, talk])
bed = bed / rms(bed[:, talk]) * 10 ** (-7 / 20)
print('bed vs voice while talking: -7 dB; bed between lines vs voice: %.1f dB' % (20 * np.log10(rms(bed[:, ~talk]))))
bed = bed + vo

shape = np.zeros(N)
def seg(t0, t1, db, ramp=0.3):
    a, b = int(t0 * SR), int(t1 * SR); r = int(ramp * SR)
    w = np.zeros(N); w[a:b] = 1; shape[:] += db * np.convolve(w, np.ones(r) / r, 'same')
seg(gone + 0.4, gone_end, -6)
seg(B[7], B[9], -2)
seg(B[11], B[13] + DUR[13], 1.5)
bed = bed * 10 ** (shape / 20)
mix = np.tanh(bed / np.max(np.abs(bed)) * 0.9) / np.tanh(0.9) * 10 ** (-1.5 / 20)
out = sys.argv[3]; raw = out + '.raw.wav'; eq = out + '.eq.wav'
sf.write(raw, mix.T, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'equalizer=f=450:t=o:w=1.2:g=-4,highshelf=f=5000:g=2', '-ar', '44100', eq])
import pyloudnorm as pyln
y, _ = sf.read(eq)
y = y * 10 ** ((-14 - pyln.Meter(SR).integrated_loudness(y)) / 20)
lim = 10 ** (-2 / 20)
if np.max(np.abs(y)) > lim:
    y = np.tanh(y / lim) * lim
n = int(0.01 * SR); w = np.linspace(0, 1, n)[:, None]
y[-n:] = y[-n:] * (1 - w) + y[:1] * w
sf.write(out, y, SR)
os.unlink(raw); os.unlink(eq)
print('ok', round(D, 2))
