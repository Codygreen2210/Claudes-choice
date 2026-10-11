#!/usr/bin/env python3
"""score.py: the music and sound for The Battle of New Orleans, written against the narration's own timing.

Reads timing.json (from film_voice.py), writes music.wav and fx.wav.
D minor at 60 beats a minute. Fog scenes sit on a low drone and wind; the British come on to a field drum
and a fife; the guns are the loudest thing in the film; it turns to D major for the patchwork army at the end.
"""
import json, re, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from studio.instruments import synth as S

TM = json.load(open('timing.json')); SC = TM['scenes']; DUR = TM['total']
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()
NW = [[norm(w['w']) for w in s['words']] for s in SC]
def q(i, phrase):
    p = norm(phrase).split()
    for k in range(len(NW[i]) - len(p) + 1):
        if NW[i][k:k + len(p)] == p: return SC[i]['words'][k]['s']
    raise SystemExit(f'cue not found: scene {i} "{phrase}"')
V = [0.0] + [s['start'] - 0.45 for s in SC[1:]] + [DUR]          # when each scene's picture starts

S.seed(1815)
rng = np.random.default_rng(1815)
mus = S.Bus(DUR, tail=6); low = S.Bus(DUR, tail=6); fx = S.Bus(DUR, tail=4)
_cache = {}
def inst(prog, m, dur, vel):
    k = (prog, m, round(dur, 2), vel)
    if k not in _cache: _cache[k] = S.sfhit(int(m), program=prog, bank=0, channel=0, vel=int(vel), dur=dur + 0.6)
    return _cache[k]
PIANO, STR, TREM, CELLO, BASS, PIZZ, HARP, TIMP, BELL, KAL = 0, 48, 44, 42, 43, 45, 46, 47, 14, 108
def kal(t, m, vel=80, g=1.0, pan=0.1): mus.add(t, inst(KAL, m, 1.2, vel), g * 1.6, pan)
def piano(t, m, dur=2.5, vel=70, g=1.0, pan=0.0): mus.add(t, inst(PIANO, m, dur, vel), g * 2.2, pan)
def strings(t, notes, dur, vel=60, g=1.0, prog=STR, swell=1.2):
    for j, m in enumerate(notes):
        y = inst(prog, m, dur, vel).copy(); n = y.shape[1]; e = np.minimum(1, np.arange(n) / (swell * S.SR)) ** 1.5
        (low if m < 50 else mus).add(t, y * e, g * 1.5, (-0.3, 0.2, -0.1, 0.3)[j % 4])
def cello(t, m, dur, vel=70, g=1.0): low.add(t, inst(CELLO, m, dur, vel), g * 0.9, 0.15)
def pizz(t, m, vel=80, g=1.0): low.add(t, inst(PIZZ, m, 0.6, vel), g * 0.8, -0.1)
def harp(t, m, vel=70, g=1.0): mus.add(t, inst(HARP, m, 2.0, vel), g * 1.4, 0.25)

Em, C, Am, B, G, D, E = (52, 59, 64, 67), (48, 55, 60, 64), (45, 52, 57, 60), (47, 54, 59, 63), (43, 50, 55, 59), (50, 57, 62, 66), (52, 59, 64, 68)
PENT = [64, 67, 69, 71, 74, 76]
grid = lambda t: float(np.ceil(t))                                # next whole second
def bars(t0, t1): return np.arange(grid(t0), t1 - 0.5, 4.0)
def arp(t, ch, vel=58, g=1.0, step=1.0, shape=(0, 1, 2, 3)):
    for k, i in enumerate(shape): piano(t + k * step, ch[i] + 12, 3.0, vel + (4 if k == 0 else -4 * (k % 2)) + rng.integers(-3, 4), g, -0.15 + 0.1 * k)

# ---------------------------------------------------------------- sounds
def tick(t, hi=True, g=1.0):
    n = S.smp(0.09); x = np.arange(n) / S.SR
    y = S.bp(S.noise(n), 1800, 5200) * np.exp(-x / 0.006) * 0.8 + np.sin(2 * np.pi * (1250 if hi else 930) * x) * np.exp(-x / 0.018) * 0.6
    fx.add(t, y, 0.05 * g, -0.2)
def clack(t, g=1.0, f=420):
    n = S.smp(0.16); x = np.arange(n) / S.SR
    fx.add(t, S.bp(S.noise(n), 900, 4200) * np.exp(-x / 0.012) + np.sin(2 * np.pi * f * x) * np.exp(-x / 0.03) * 0.7, 0.10 * g, 0.3)
def thud(t, g=1.0, f=70):
    n = S.smp(0.5); x = np.arange(n) / S.SR
    fx.add(t, np.sin(2 * np.pi * f * (1 + 0.8 * np.exp(-x / 0.02)) * x) * np.exp(-x / 0.12) + S.lp(S.noise(n), 900) * np.exp(-x / 0.03) * 0.5, 0.22 * g, 0.0)
def clink(t, m=96, g=1.0, pan=0.0): fx.add(t, S.bell(m, 0.5, ratio=3.7, idx=1.4, dec=0.14), 0.035 * g, pan)
def swish(t, g=1.0, dur=0.25): fx.add(t, S.whoosh(dur, 900, 3800, 0.9), 0.05 * g, 0.1)
def scratch(t0, dur, g=1.0):
    n = S.smp(dur); x = np.arange(n) / S.SR
    am = 0.5 + 0.5 * np.sin(2 * np.pi * (9 + 3 * np.sin(x * 5)) * x)
    fx.add(t0, S.bp(S.noise(n), 2200, 6500) * am * np.clip(x / 0.03, 0, 1) * np.clip((dur - x) / 0.05, 0, 1), 0.035 * g, 0.2)
def murmur(t0, t1, g0, g1):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    y = S.bp(S.noise(n), 220, 1100) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.31 * x + 1) * np.sin(2 * np.pi * 0.83 * x)) + S.bp(S.noise(n), 90, 300) * 0.5
    env = np.linspace(g0, g1, n) * np.clip(x / 1.5, 0, 1) * np.clip((t1 - t0 - x) / 1.5, 0, 1)
    fx.add(t0, S.autopan(y * env, -0.4, 0.4), 0.11)
def creak(t0, dur, g=1.0):
    n = S.smp(dur); x = np.arange(n) / S.SR; f = 170 + 120 * x / dur + 12 * np.sin(2 * np.pi * 7 * x)
    y = S.bp(S.saw(f, n) * (np.sin(2 * np.pi * 23 * x) > -0.3), 300, 1800)
    fx.add(t0, y * np.sin(np.pi * x / dur) ** 0.7, 0.03 * g, 0.2)


def crickets(t0, t1, g=1.0):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    y = np.zeros(n)
    for f, rate, ph in ((4300, 3.1, 0.0), (4750, 2.3, 1.7), (5200, 3.7, 0.6)):
        y += np.sin(2 * np.pi * f * x) * (np.sin(2 * np.pi * 38 * x) > 0.2) * np.clip(np.sin(2 * np.pi * rate / 4 * x + ph), 0, 1) ** 3
    env = np.clip(x / 2, 0, 1) * np.clip((t1 - t0 - x) / 2, 0, 1)
    fx.add(t0, S.autopan(y * env, -0.6, 0.6), 0.013 * g)
    w = S.bp(S.noise(n), 90, 420) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * x)) * env      # wind; the first pass was all rumble
    fx.add(t0, w, 0.022 * g, 0.0)
def growl(t, dur=1.4, g=1.0, pan=0.0):
    n = S.smp(dur); x = np.arange(n) / S.SR
    f = 58 - 12 * x / dur + 3 * np.sin(2 * np.pi * 5 * x)
    y = S.saw(f, n) * (0.55 + 0.45 * np.sin(2 * np.pi * 24 * x)) + 0.4 * S.bp(S.noise(n), 150, 700)
    y = S.bp(y, 70, 900) + 0.5 * S.bp(y, 300, 620)
    fx.add(t, S.saturate(y * np.sin(np.pi * x / dur) ** 0.7, 1.6), 0.10 * g, pan)
def shot(t, g=1.0, pan=0.0):
    n = S.smp(1.2); x = np.arange(n) / S.SR
    y = S.noise(n) * np.exp(-x / 0.035) + S.lp(S.noise(n), 500) * np.exp(-x / 0.25) * 0.5 + np.sin(2 * np.pi * 70 * x * (1 + np.exp(-x / 0.02))) * np.exp(-x / 0.1)
    fx.add(t, S.lp(y, 5200), 0.20 * g, pan)
def drum(t, g=1.0, m=41): low.add(t, inst(TIMP, m, 1.0, 62), 0.7 * g)
def heart(t0, t1, gap0=1.0, gap1=1.0, g0=0.5, g1=0.5):
    t = t0
    while t < t1:
        p = (t - t0) / max(1e-6, t1 - t0); g = g0 + (g1 - g0) * p
        drum(t, g, 40); drum(t + 0.22, g * 0.7, 40); t += gap0 + (gap1 - gap0) * p
def chuff(t0, t1, rate0=2.0, rate1=2.0, g=1.0):
    t = t0
    while t < t1:
        p = (t - t0) / max(1e-6, t1 - t0); n = S.smp(0.16); x = np.arange(n) / S.SR
        fx.add(t, S.bp(S.noise(n), 300, 2600) * np.exp(-x / 0.05), 0.09 * g * np.sin(np.pi * min(1, max(0.05, p))) ** 0.5, -0.3 + 0.6 * p); t += 1 / (rate0 + (rate1 - rate0) * p)
def whistle(t, dur=1.2, g=1.0):
    n = S.smp(dur); x = np.arange(n) / S.SR; v = 1 + 0.004 * np.sin(2 * np.pi * 6 * x)
    y = (np.sin(2 * np.pi * 740 * v * x) + 0.8 * np.sin(2 * np.pi * 932 * v * x) + 0.3 * S.bp(S.noise(n), 700, 2500)) * np.clip(x / 0.08, 0, 1) * np.clip((dur - x) / 0.25, 0, 1)
    fx.add(t, y, 0.03 * g, -0.2)
def crackle(t0, t1, g=1.0):
    for t in np.sort(rng.uniform(t0, t1, int((t1 - t0) * 5))): n = S.smp(0.03); x = np.arange(n) / S.SR; fx.add(t, S.hp(S.noise(n), 2500) * np.exp(-x / 0.004), 0.03 * g * rng.uniform(0.3, 1), rng.uniform(-0.3, 0.5))
def drone(t0, t1, notes=(28, 40), vel=42, g=0.6): strings(t0, [m + 12 if m < 36 else m for m in notes], t1 - t0, vel, g * 0.8, swell=3)   # an octave up: E1 made the bed bottom-heavy
def motif(t, notes, step=1.0, vel=74, g=1.0, fn=None):
    for k, m in enumerate(notes): (fn or kal)(t + k * step, m, vel - 3 * (k % 2), g)


Dm, Bb, Gm, A, F, C, D, G = (50, 57, 62, 65), (46, 53, 58, 62), (43, 50, 55, 58), (45, 52, 57, 61), (41, 48, 53, 57), (48, 55, 60, 64), (50, 57, 62, 66), (43, 50, 55, 59)
FLUTE, PICC, PIPE = 73, 72, 109
def fife(t, m, dur=0.5, vel=70, g=1.0): mus.add(t, inst(PICC, m, dur, vel), g * 1.5, -0.25)
def snare(t, g=1.0):
    n = S.smp(0.22); x = np.arange(n) / S.SR
    fx.add(t, S.bp(S.noise(n), 900, 6000) * np.exp(-x / 0.05) + np.sin(2 * np.pi * 190 * x) * np.exp(-x / 0.04) * 0.6, 0.05 * g, -0.15)
def march(t0, t1, g0=0.5, g1=0.5, step=0.5):
    for k, t in enumerate(np.arange(grid(t0), t1, step)):
        g = g0 + (g1 - g0) * (t - t0) / max(1e-6, t1 - t0); snare(t, g)
        if k % 4 == 3: snare(t + step * 0.5, g * 0.6); snare(t + step * 0.75, g * 0.6)
        if k % 8 == 6:
            for j in range(4): snare(t + step * 0.25 + j * 0.06, g * 0.4)
def wind(t0, t1, g=1.0):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    w = S.bp(S.noise(n), 140, 700) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.06 * x + 1) * np.sin(2 * np.pi * 0.11 * x)) * np.clip(x / 2, 0, 1) * np.clip((t1 - t0 - x) / 2, 0, 1)
    fx.add(t0, S.autopan(w, -0.4, 0.4), 0.03 * g)
def boom(t, g=1.0, pan=0.0):
    n = S.smp(2.6); x = np.arange(n) / S.SR
    y = np.sin(2 * np.pi * 52 * x * (1 + 0.9 * np.exp(-x / 0.03))) * np.exp(-x / 0.35) + S.noise(n) * np.exp(-x / 0.05) * 0.8 + S.lp(S.noise(n), 420) * np.exp(-x / 0.7) * 0.7
    fx.add(t, S.lp(y, 3800), 0.30 * g, pan)
def hooves(t0, t1, rate=3.2, g=1.0):
    for t in np.arange(t0, t1, 1 / rate):
        for d, f in ((0, 120), (0.09, 150), (0.16, 105)): thud(t + d, 0.22 * g, f)
def volley(t0, t1, per_s=5, g=0.4):
    for t in np.sort(rng.uniform(t0, t1, int((t1 - t0) * per_s))): shot(t, g * rng.uniform(0.5, 1.0), rng.uniform(-0.6, 0.2))

# ================================================================ 1. fog
qJ, qS, qM, qF, qA, qW, qO = q(0, 'its just before'), q(0, 'somewhere out'), q(0, 'many of them'), q(0, 'in front of them'), q(0, 'and an army'), q(0, 'and the war'), q(0, 'is already over')
wind(0.2, V[1] + 1, 1.0); drone(0.5, qF, (26, 38), 42, 0.7)
motif(SC[0]['start'] - 1.5, [62, 69, 65], 1.2, 66, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g)); piano(qJ + 1.0, 57, 4, 58, 0.8); piano(qJ + 4.0, 50, 4, 56, 0.8)
march(qS + 0.5, qF - 0.6, 0.12, 0.32)
for k, m in enumerate((74, 77, 76, 74, 72, 74)): fife(qM + 0.3 + k * 0.5, m, 0.5, 52, 0.45)
drone(qF, V[1] + 0.5, (26, 38, 45), 48, 0.8); cello(qF + 0.5, 38, qW - qF, 58, 0.8)
low.add(qO - 0.05, inst(TIMP, 38, 3, 98), 1.4); strings(qO, Dm, V[1] - qO + 1.2, 74, 0.9, swell=0.6)
motif(qO + 0.5, [74, 69, 65, 62], 0.5, 76, 1.0, fn=lambda t, m, v, g: piano(t, m, 4, v, g))

# ================================================================ 2. why New Orleans
qNot, qSum, qBurn, qNow, qWho, qEv, qSent, qArmy, qGen = q(1, 'it had not gone'), q(1, 'the summer before'), q(1, 'and burned'), q(1, 'now they wanted'), q(1, 'whoever held'), q(1, 'and everything that'), q(1, 'so they sent'), q(1, 'and an army'), q(1, 'and a general')
for k, t in enumerate(bars(V[1] + 0.8, qSum - 0.5)):
    ch = (Dm, Bb)[k % 2]; pizz(t, ch[0] - 12, 70, 0.8); pizz(t + 2, ch[1] - 12, 60, 0.6); piano(t + 1, ch[2], 4, 52, 0.7); piano(t + 3, ch[3], 4, 50, 0.7)
volley(SC[1]['start'] + 0.8, qSum - 0.4, 1.6, 0.16)
march(qSum, qBurn, 0.25, 0.4); crackle(qBurn, qNow + 0.3, 2.2); strings(qBurn, (38, 45, 50, 53, 56), qNow - qBurn + 0.3, 62, 0.9, prog=TREM, swell=0.6); low.add(qBurn, inst(TIMP, 38, 3, 96), 1.3)
for k, t in enumerate(bars(qNow, qSent - 0.6)):
    ch = (F, C, Dm, Bb)[k % 4]; cello(t, ch[0] - 12, 3.8, 60, 0.8)
    for e in range(4): harp(t + e, ch[(e + k) % 4] + 12, 64, 0.8)
clink(qNow + 0.4, 98, 1.4)
creak(qSent, 1.4, 1.0); creak(qArmy, 1.2, 0.8); strings(qSent, (38, 45, 50, 57), qGen - qSent + 0.5, 60, 0.9, swell=1.5); march(qSent + 0.5, qGen, 0.15, 0.35)
low.add(qGen + 0.3, inst(TIMP, 38, 3, 94), 1.2); hooves(qGen + 0.2, qGen + 2.2, 2.0, 0.6); cello(qGen + 0.4, 26, V[2] - qGen, 66, 0.9)

# ================================================================ 3. Jackson's army
qThin, qNo, qBuilt, q5, qNever = q(2, 'jackson was thin'), q(2, 'and he had no'), q(2, 'so he built'), q(2, 'about five thousand'), q(2, 'who had never')
cues = [q(2, c) for c in ('a few regular', 'sailors and marines', 'militia from', 'shopkeepers', 'two battalions', 'a company of choctaw', 'and the pirates')]
for k, m in enumerate((38, 41, 45, 43, 38)): cello(SC[2]['start'] + 0.3 + k * 1.6, m, 1.7, 62, 0.9)
piano(qNo + 0.6, 38, 4, 58, 0.8); wind(qNo - 0.5, qBuilt + 1, 0.8)
for k, t in enumerate(np.arange(grid(qBuilt), q5 - 0.4, 0.5)):
    ch = (Dm, F, Bb, C)[int(k // 8) % 4]; lvl = min(1.0, 0.45 + k / 50)
    pizz(t, ch[0] - 12 + (0, 7)[k % 2], 70, 0.8 * lvl)
    if k % 2 == 0: piano(t, ch[(k // 2) % 4] + 12, 2, 56, 0.7 * lvl)
    if k % 8 == 0: strings(t, ch, 4.3, 44 + int(20 * lvl), 0.6 * lvl, swell=0.8)
for k, t in enumerate(cues): thud(t + 0.5, 0.5, 90); snare(t + 0.55, 0.35); harp(t + 0.1, 74 + (0, 3, 5, 7, 8, 10, 12)[k], 66, 0.8)
low.add(q5 + 0.2, inst(TIMP, 38, 3, 98), 1.3); strings(q5 + 0.2, (38, 45, 50, 53, 57), V[3] - q5 + 0.4, 68, 1.0, swell=0.6); piano(qNever, 50, 5, 66, 0.9); piano(qNever + 0.5, 53, 5, 60, 0.8)

# ================================================================ 4. the wall
qCan, qLess, qNoW, qBeh, qEn, qTwo, qGunW, qSt, qWait = q(3, 'an old canal'), q(3, 'less than a mile'), q(3, 'and no way'), q(3, 'behind that ditch'), q(3, 'enslaved men'), q(3, 'for two weeks'), q(3, 'with cannon'), q(3, 'then they stood'), q(3, 'and waited')
for k, t in enumerate(bars(V[3] + 0.6, qBeh - 0.6)): ch = (Dm, Gm, Bb, A)[k % 4]; arp(t, ch, 52, 0.85); cello(t, ch[0] - 12, 3.8, 56, 0.8)
scratch(qCan, 1.3, 1.0); thud(qNoW + 0.9, 0.7, 80); thud(qNoW + 1.4, 0.7, 70)
for t in np.arange(qBeh + 0.2, qGunW - 0.4, 0.98): thud(t, 0.4, 130); swish(t + 0.35, 0.6, 0.2)
for k, t in enumerate(bars(qBeh, qGunW)): ch = (Dm, Bb, F, C)[k % 4]; strings(t, ch, 4.3, 46 + 6 * k, 0.6 + 0.08 * k, swell=1.0); cello(t, ch[0] - 12, 3.8, 60, 0.9)
for k in range(3): thud(qGunW + 0.1 + k * 0.3, 0.9, 60)
low.add(qGunW + 0.1, inst(TIMP, 38, 3, 90), 1.2)
drone(qSt, V[4] + 0.4, (26, 38, 45), 48, 0.8); wind(qSt - 0.5, V[4] + 1, 1.0); piano(qWait + 0.3, 38, 5, 62, 0.9); piano(qWait + 0.3, 50, 5, 56, 0.8)

# ================================================================ 5. the plan
qOne, qTake, qTurn, qMain, qFill, qLad, qNone, qBoat, qLate, qReg, qPast, qBy, qCall, qGo, qFire = q(4, 'one force would'), q(4, 'take the american'), q(4, 'and turn them'), q(4, 'then the main army'), q(4, 'fill the ditch'), q(4, 'throw ladders'), q(4, 'almost none'), q(4, 'the boats got stuck'), q(4, 'and the river force'), q(4, 'and the regiment'), q(4, 'marched right past'), q(4, 'by the time'), q(4, 'call it off'), q(4, 'or go anyway'), q(4, 'he fired')
for k, t in enumerate(np.arange(grid(V[4] + 0.6), qNone - 0.6, 0.5)):
    ch = (Dm, Dm, Gm, A)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 68, 0.8)
    if k % 2 == 0: piano(t, ch[(k // 2) % 4] + 12, 2, 54, 0.65)
march(V[4] + 1, qNone - 0.6, 0.14, 0.26, 1.0)
for t in (qOne + 0.4, qTurn + 0.1, qMain + 0.5): swish(t, 1.4, 0.6)
for k in range(3): clack(qLad + 0.2 + k * 0.15, 0.7, 500)
piano(qNone, 26, 5, 84, 1.2); piano(qNone, 38, 5, 76, 1.0); thud(qNone + 0.02, 1.2, 60)
for k in range(3): thud(qNone + 0.5 + k * 0.3, 0.5, 200)
drone(qBoat - 0.3, qBy, (26, 38), 46, 0.8); wind(qBoat - 0.5, V[5], 1.0)
for t in np.arange(qBoat + 0.4, qReg - 0.6, 2.85): creak(t, 1.0, 1.2); thud(t + 0.9, 0.6, 70)
cello(qLate, 38, 3.5, 60, 0.9); cello(qLate + 1.8, 37, 2.5, 58, 0.9)
march(qReg, qBy - 0.8, 0.34, 0.1); piano(qPast + 0.3, 62, 4, 62, 0.8); piano(qPast + 0.8, 61, 4, 58, 0.8); piano(qPast + 1.3, 57, 4, 56, 0.8)
heart(qBy, qFire, 1.0, 0.7, 0.4, 0.75); strings(qBy, (38, 44, 50), qFire - qBy, 46, 0.7, prog=TREM, swell=2)
fx.add(qFire + 0.5, S.whoosh(1.9, 500, 5200, 0.9), 0.07, -0.3); clink(qFire + 2.4, 92, 2.2); clink(qFire + 2.5, 99, 1.6); shot(qFire + 2.4, 0.35, -0.3)
low.add(qFire + 2.4, inst(TIMP, 38, 4, 104), 1.5); strings(qFire + 2.4, (38, 45, 50, 53), V[5] - qFire - 1.6, 70, 0.9, swell=0.4)

# ================================================================ 6. the assault
qDr, qFog, qOpen, qEv, qCn, qRif, qMus, qStop, qDit, qNoL, qStd, qDie = q(5, 'drums going'), q(5, 'and then the fog'), q(5, 'they were in the open'), q(5, 'in front of every'), q(5, 'the cannon opened') - 0.35, q(5, 'then the rifles') - 0.25, q(5, 'then the muskets') - 0.3, q(5, 'it did not stop') - 0.4, q(5, 'the men who reached') - 0.4, q(5, 'there were no ladders'), q(5, 'so they stood'), q(5, 'and they died')
march(V[5] + 0.3, qCn, 0.4, 0.55); wind(V[5], qFog + 2, 0.8)
tune = [74, 74, 77, 76, 74, 72, 74, 69, 74, 74, 77, 76, 79, 77, 76, 74]
for k, t in enumerate(np.arange(grid(V[5] + 1.0), qFog - 0.2, 0.5)): fife(t, tune[k % 16], 0.5, 62, 0.6)
for k, t in enumerate(bars(V[5] + 0.5, qFog)): pizz(t, 38, 70, 0.7); pizz(t + 2, 45, 62, 0.6)
strings(qFog + 0.4, (62, 69, 74, 77), qCn - qFog, 44, 0.7, prog=TREM, swell=2.5); cello(qOpen, 26, qCn - qOpen, 62, 0.9); heart(qEv, qCn, 0.6, 0.45, 0.6, 0.9)
for k in range(3): boom(qCn + 0.35 + k * 0.65, 1.0, (-0.5, 0.0, 0.5)[k]); boom(qRif + 1.2 + k * 0.5, 0.7, (-0.5, 0.0, 0.5)[k])
volley(qRif + 0.15, qMus + 0.3, 6, 0.3)
T = 2.4
for n in range(-1, 12):
    for k in range(3):
        t = qMus + T * (0.12 - k / 3 + n)
        if qMus + 0.25 < t < qStop + 0.2: shot(t, 0.75, -0.2)
strings(qMus, (38, 45, 50, 53), qStop - qMus + 0.3, 58, 0.8, prog=TREM, swell=0.8)
volley(qStop + 0.3, qDit + 0.2, 6, 0.3)
for n in range(3):
    for k in range(3):
        t = qStop + 0.5 + k * 0.8 + n * 2.6
        if t < qDit: boom(t, 0.7, (-0.5, 0.0, 0.5)[k])
for k, m in enumerate((50, 49, 46, 45)): cello(qStop + 0.6 + k * 1.3, m - 12, 1.3, 70, 1.0)
drone(qDit, V[6] + 0.3, (26, 38), 46, 0.8); wind(qDit, V[6] + 1, 0.8); heart(qDit + 0.5, qDie, 1.0, 1.0, 0.4, 0.5)
piano(qNoL + 0.2, 38, 5, 70, 1.0); piano(qNoL + 0.2, 26, 5, 64, 0.9)
for d in (0.25, 0.75, 1.35, 1.95): shot(qDie + d, 0.7, -0.3)
for k, m in enumerate((62, 57, 53, 50)): piano(qDie + 2.4 + k * 0.6, m, 5, 60 - 3 * k, 0.9)

# ================================================================ 7. the generals, the Highlanders
qHit, qHit2, qLive, qSec, qDown, qThird, qHigh, qHalt, qStood, qNob, qAll, qAlive = q(6, 'he was hit'), q(6, 'then hit again'), q(6, 'he did not live'), q(6, 'his second in command'), q(6, 'went down'), q(6, 'then his third'), q(6, 'one regiment of highlanders'), q(6, 'halted in the open'), q(6, 'so they stood'), q(6, 'because nobody'), q(6, 'all across the field'), q(6, 'just to stay')
hooves(V[6] + 0.2, qHit2, 3.0, 0.9); hooves(qHit2 + 0.6, qHit2 + 3.2, 3.4, 0.5)
strings(V[6] + 0.3, (38, 45, 50, 53), qHit - V[6], 60, 0.8, prog=TREM, swell=0.6); volley(V[6] + 0.3, qHit2, 2.5, 0.18)
shot(qHit - 0.05, 1.3, -0.4); shot(qHit2 - 0.05, 1.5, -0.4); thud(qHit2 + 0.7, 1.0, 60)
for k, m in enumerate((62, 60, 58, 57, 53, 50)): cello(qHit2 + 1.2 + k * 1.0, m - 12, 1.2, 64, 1.0)
strings(qLive, (38, 45, 50), qSec - qLive + 0.3, 48, 0.7, swell=1.5)
volley(qSec, qHigh - 0.5, 2.5, 0.16); shot(qDown - 0.1, 1.1, -0.4); thud(qDown + 0.45, 0.8, 70); shot(qThird + 0.45, 1.1, -0.4); thud(qThird + 1.0, 0.8, 70)
low.add(qDown + 0.4, inst(TIMP, 38, 3, 84), 1.1); low.add(qThird + 1.0, inst(TIMP, 36, 3, 88), 1.1)
march(qHigh, qHalt + 0.3, 0.42, 0.42)
mus.add(qHigh + 0.4, inst(PIPE, 50, qNob - qHigh, 44), 0.5, 0.2); mus.add(qHigh + 0.4, inst(PIPE, 57, qNob - qHigh, 40), 0.4, 0.2)
for k, m in enumerate((69, 74, 72, 69, 67, 69)): mus.add(qHigh + 1.2 + k * 0.9, inst(PIPE, m, 0.9, 54), 0.5, 0.2)
snare(qHalt + 0.5, 0.7)
for t in np.arange(qStood + 0.5, qAll - 0.5, 0.9): shot(t + rng.uniform(0, 0.08), 0.6, -0.5); shot(t + 0.2 + rng.uniform(0, 0.1), 0.35, -0.5)
cello(qStood, 26, qAll - qStood, 62, 0.9); piano(qNob + 0.3, 38, 5, 66, 0.9)
drone(qAll - 0.3, V[7] + 0.3, (26, 38, 45), 46, 0.8); wind(qAll - 0.5, V[7] + 1, 1.0); volley(qAll, qAlive, 1.0, 0.12)
for k, m in enumerate((65, 64, 62, 57)): piano(qAll + 1.0 + k * 1.2, m, 5, 56, 0.8)

# ================================================================ 8. the count
qHalf, qBrit, qKil, qAm, q71, q13, qKy, qCov, qThen, qUp, qLiv, qWalk = q(7, 'about half an hour'), q(7, 'the british lost'), q(7, 'killed wounded'), q(7, 'the americans lost'), q(7, '71'), q(7, '13 of them'), q(7, 'a kentucky soldier'), q(7, 'entirely covered'), q(7, 'and then some'), q(7, 'stood up'), q(7, 'living men'), q(7, 'and now walked')
for k in range(30): tick(qHalf - 0.3 + k * 1.9 / 30, k % 2 == 0, 0.9)
for k, t in enumerate(bars(V[7] + 0.6, qKy - 0.6)):
    ch = (Dm, Bb, Gm, A)[k % 4]; pizz(t, ch[0] - 12, 66, 0.7); piano(t, ch[1], 4, 52, 0.75); piano(t + 1, ch[2], 4, 48, 0.7); piano(t + 2, ch[3], 4, 50, 0.7); piano(t + 3, ch[2], 4, 46, 0.7)
for i in range(60): tick(qBrit + 0.3 + i * (qKil + 0.6 - qBrit - 0.3) / 60, i % 2 == 0, 0.55)
low.add(qKil + 0.6, inst(TIMP, 38, 3, 88), 1.1)
for i in range(7): tick(q71 - 0.2 + i * 0.1, True, 0.7)
piano(q13, 26, 6, 74, 1.1); piano(q13, 38, 6, 66, 0.9)
wind(qKy - 0.5, V[8] + 1, 1.0); drone(qKy, qThen, (26, 38, 45), 44, 0.7); cello(qCov, 38, qThen - qCov, 58, 0.8)
strings(qThen, (41, 48, 53, 57, 60), V[8] - qThen + 0.4, 56, 0.9, swell=1.6)
for k, m in enumerate((65, 69, 72, 77, 81)): harp(qUp - 0.1 + k * 0.3, m, 62, 0.9)
for k, m in enumerate((77, 76, 72, 69)): piano(qLiv + k * 1.0, m, 4, 54, 0.8)

# ================================================================ 9. the treaty
q15, qEve, qCity, qSign, qNews, qStill, qTr, qBut, qWord = q(8, '15 days earlier'), q(8, 'on christmas eve'), q(8, 'in a city'), q(8, 'had signed a peace'), q(8, 'the news was on'), q(8, 'still crossing'), q(8, 'the treaty still'), q(8, 'but its terms'), q(8, 'changed a word')
low.add(SC[8]['start'] + 0.2, inst(TIMP, 38, 3, 80), 1.0); cello(SC[8]['start'] + 0.2, 26, q15 - SC[8]['start'], 60, 0.9)
crackle(q15, qNews, 0.5)
for i in range(15): tick(q15 + 0.3 + i * (qEve - q15) / 15, i % 2 == 0, 0.9)
for k, t in enumerate(bars(q15, qNews - 0.4)): ch = (Dm, Bb, F, C)[k % 4]; harp(t, ch[0], 60, 0.8); harp(t + 1, ch[2], 56, 0.7); harp(t + 2, ch[3], 58, 0.7); harp(t + 3, ch[2] + 12, 54, 0.7); cello(t, ch[0] - 12, 3.8, 54, 0.7)
scratch(qSign - 0.9, 1.1, 1.3); thud(qSign + 0.55, 0.9, 110); clink(qSign + 0.6, 90, 1.0)
wind(qNews - 0.5, qTr + 0.5, 1.2)
for t in np.arange(qNews + 0.5, qTr - 1.0, 2.6): creak(t, 1.2, 1.0)
strings(qNews, (41, 48, 53, 57), qTr - qNews + 0.3, 56, 0.9, swell=1.6)
for k, m in enumerate((69, 72, 77, 76, 72, 69, 65)): piano(qNews + 0.8 + k * 1.0, m, 4, 54, 0.75)
crackle(qTr, V[9], 0.5)
for k, t in enumerate(bars(qTr, V[9] - 0.4)): ch = (Dm, Gm, A)[k % 3]; cello(t, ch[0] - 12, 3.8, 58, 0.8); harp(t, ch[1], 58, 0.8); harp(t + 1.5, ch[2], 54, 0.7); harp(t + 3, ch[3], 54, 0.7)
piano(qWord + 0.4, 38, 5, 66, 0.9)

# ================================================================ 10. what it changed
qNoth, qCo, qVic, qPe, qDec, qPat, qMan, qWH, qLast, qAft, qMat, qSub, qAn, qBat, qCol = q(9, 'on paper nothing'), q(9, 'but the country'), q(9, 'the news of the victory'), q(9, 'and the news of the peace'), q(9, 'and americans decided'), q(9, 'a patchwork army'), q(9, 'and the man behind'), q(9, 'all the way to'), q(9, 'the last great battle'), q(9, 'was fought after'), q(9, 'and it mattered'), q(9, 'subscribe'), q(9, 'animal facts'), q(9, 'historys greatest'), q(9, 'worlds craziest')
crackle(V[9], qCo, 0.5); piano(qNoth + 0.9, 38, 5, 64, 0.9); piano(qNoth + 0.9, 50, 5, 56, 0.8)
for k, t in enumerate(np.arange(grid(qCo), qPat - 0.6, 0.5)):
    ch = (F, C, Dm, Bb)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 70, 0.8)
    if k % 2 == 0: piano(t, ch[(k // 2) % 4] + 12, 2, 58, 0.7)
    if k % 8 == 0: strings(t, ch, 4.3, 52, 0.7, swell=0.8)
thud(qVic + 0.3, 0.8, 150); swish(qVic - 0.1, 1.2, 0.4); thud(qPe + 0.3, 0.8, 150); swish(qPe - 0.1, 1.2, 0.4)
murmur(qDec - 0.3, qPat, 0.5, 1.3)
for k, t in enumerate(np.arange(grid(qDec), qPat - 0.5, 0.5)): fife(t, (74, 77, 81, 77, 79, 77, 76, 74)[k % 8], 0.5, 66, 0.55)
t0 = qPat - 0.3                                                                               # the patchwork army: D major
strings(t0, (38, 45, 50, 54, 57, 62), qMan - t0 + 0.5, 70, 1.0, swell=1.4)
for k, m in enumerate((62, 66, 69, 74, 78, 81)): harp(t0 + 0.4 + k * 0.22, m, 68, 0.9)
low.add(t0 + 0.3, inst(TIMP, 38, 3, 90), 1.2)
for k, t in enumerate(bars(qMan, qLast - 0.5)): ch = (D, G, D, A)[k % 4]; cello(t, ch[0] - 12, 3.8, 62, 0.9); arp(t, ch, 56, 0.85)
hooves(qMan + 0.2, qLast - 0.8, 1.6, 0.4)
drone(qLast - 0.3, qSub, (26, 38, 45), 46, 0.8); wind(qLast - 0.5, qSub + 0.5, 1.0)
motif(qLast + 0.8, [62, 69, 65], 1.2, 62, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g))
strings(qMat - 0.2, (38, 45, 50, 54, 57), qSub - qMat + 0.5, 62, 0.9, swell=1.4)
for k, m in enumerate((62, 66, 69, 74)): piano(qMat + 0.3 + k * 0.5, m, 5, 60, 0.9)
e0 = qSub
low.add(e0, inst(TIMP, 38, 3, 92), 1.2); strings(e0, (38, 45, 50, 54, 57, 62), DUR - e0 - 0.5, 70, 1.0, swell=0.8)
for k, (t, m) in enumerate(zip(np.arange(e0 + 0.5, DUR - 5.5, 1.0), [62, 69, 67, 66, 62, 69, 71, 69, 66, 67, 69, 74] * 3)): harp(t, m + 12, 70, 0.9); piano(t, m, 3.5, 52, 0.6)
march(e0 + 0.5, DUR - 6, 0.16, 0.16, 1.0)
for at, m in ((qAn, 74), (qBat, 78), (qCol, 81)): harp(at, m, 76, 1.0); harp(at + 0.12, m + 7, 70, 0.8)
tend = DUR - 5.2
for k, m in enumerate((38, 50, 57, 62, 66, 69, 74)): piano(tend + k * 0.16, m, 6, 68, 1.0)
low.add(tend, inst(TIMP, 38, 4, 80), 1.0)

# ---------------------------------------------------------------- mix
IR = S.hall(4.0, 1.3, 0.03, 220, 6500)
m = mus.out(True) * 1.1 + low.out(True)[:, :mus.x.shape[1]] * 0.85
m = m + S.reverb(mus.out(True) * 0.6 + low.out(True)[:, :mus.x.shape[1]] * 0.25, IR, 0.5)
m = m[:, :S.smp(DUR)]
m = S.eq(m, [('lowshelf', 110, -5.0, 0.7), ('peak', 280, -5.5, 0.9), ('peak', 520, -3.0, 1.0), ('peak', 1500, 2.0, 0.8), ('peak', 3000, 5.0, 0.8), ('highshelf', 4500, 10.0, 0.7)])
f = fx.out(True); f = f + S.reverb(f * 0.5, S.plate(1.8, 0.5), 0.45); f = f[:, :S.smp(DUR)]
tt_ = np.arange(m.shape[1]) / S.SR
fade = np.clip(tt_ / 0.5, 0, 1) * np.clip((DUR - tt_) / 3.0, 0, 1)
S.write('music.wav', S.master(m * fade, lufs=-20.0, fade=0, ceiling=0.8))
f = S.eq(S.hp(f, 62), [('lowshelf', 120, -7.0, 0.7), ('peak', 2500, 2.5, 0.8)])
S.write('fx.wav', S.limiter(f * fade * 2.2, 0.7))
print('music.wav, fx.wav', round(DUR, 2), 's')
