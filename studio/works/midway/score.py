#!/usr/bin/env python3
"""score.py: the music and sound for Midway, written against the narration's own timing.

Reads timing.json (from film_voice.py), writes music.wav and fx.wav.
E minor at 60 beats a minute. Sea and engines underneath; a field drum and low strings for the fleets; morse for the
codebreakers; the dive is the loudest thing in the film; it ends in E major over a lone engine.
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

S.seed(1942)
rng = np.random.default_rng(1942)
mus = S.Bus(DUR, tail=6); low = S.Bus(DUR, tail=6); fx = S.Bus(DUR, tail=4)
_cache = {}
def inst(prog, m, dur, vel):
    k = (prog, m, round(dur, 2), vel)
    if dur > 5: return S.sfhit(int(m), program=prog, bank=0, channel=0, vel=int(vel), dur=dur + 0.6)      # long notes are one-offs: keeping them ran the machine out of memory
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


Em, C, Am, B, G, D, E, A = (52, 59, 64, 67), (48, 55, 60, 64), (45, 52, 57, 60), (47, 54, 59, 63), (43, 50, 55, 59), (50, 57, 62, 66), (52, 59, 64, 68), (45, 52, 57, 61)
HORN, TRB = 60, 57
def horn(t, m, dur=2.0, vel=64, g=1.0): mus.add(t, inst(HORN, m, dur, vel), g * 1.1, -0.2)
def waves(t0, t1, g=1.0):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR
    w = S.bp(S.noise(n), 120, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * x + 1)) ** 2 + 0.35 * S.bp(S.noise(n), 900, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * x + 2.2)) ** 6
    fx.add(t0, S.autopan(w * np.clip(x / 2, 0, 1) * np.clip((t1 - t0 - x) / 2, 0, 1), -0.4, 0.4), 0.03 * g)
def engines(t0, t1, g=1.0, f0=92, rise=0.0, pan=(-0.5, 0.5)):
    n = S.smp(t1 - t0); x = np.arange(n) / S.SR; f = f0 * (1 + rise * x / max(1e-6, t1 - t0)) * (1 + 0.006 * np.sin(2 * np.pi * 0.7 * x))
    y = S.saw(f, n) * 0.6 + S.saw(f * 1.5, n) * 0.3 + 0.3 * S.bp(S.noise(n), 200, 1200)
    y = S.hp(S.lp(y * (0.8 + 0.2 * np.sin(2 * np.pi * f0 / 7 * x)), 1800), 120)
    fx.add(t0, S.autopan(y * np.clip(x / 1.2, 0, 1) * np.clip((t1 - t0 - x) / 1.2, 0, 1), *pan), 0.035 * g)
def dive(t, dur=2.3, g=1.0, pan=0.3):
    n = S.smp(dur); x = np.arange(n) / S.SR; f = 180 * (1 + 2.2 * (x / dur) ** 2)
    y = S.lp(S.saw(f, n) * 0.6 + S.saw(f * 2.01, n) * 0.3, 2600) * np.clip(x / 0.3, 0, 1) * np.clip((dur - x) / 0.15, 0, 1) * (0.3 + 0.7 * x / dur)
    fx.add(t, y, 0.05 * g, pan)
def boom(t, g=1.0, pan=0.0):
    n = S.smp(2.8); x = np.arange(n) / S.SR
    y = np.sin(2 * np.pi * 50 * x * (1 + 0.9 * np.exp(-x / 0.03))) * np.exp(-x / 0.4) + S.noise(n) * np.exp(-x / 0.06) * 0.8 + S.lp(S.noise(n), 500) * np.exp(-x / 0.8) * 0.8
    fx.add(t, S.lp(y, 3600), 0.30 * g, pan)
def pop(t, g=1.0):
    n = S.smp(0.5); x = np.arange(n) / S.SR
    fx.add(t, S.lp(S.noise(n), 1800) * np.exp(-x / 0.05) + np.sin(2 * np.pi * 90 * x) * np.exp(-x / 0.08) * 0.6, 0.07 * g, rng.uniform(-0.6, 0.6))
def flakf(t0, t1, per_s=1.6, g=1.0):
    for t in np.sort(rng.uniform(t0, t1, max(1, int((t1 - t0) * per_s)))): pop(t, g * rng.uniform(0.5, 1))
def splashf(t, g=1.0):
    n = S.smp(1.2); x = np.arange(n) / S.SR
    fx.add(t, S.bp(S.noise(n), 600, 4500) * np.clip(x / 0.05, 0, 1) * np.exp(-x / 0.35), 0.05 * g, rng.uniform(-0.5, 0.5))
def morse(t0, t1, g=1.0, f=720, wpm=0.085):
    t = t0
    while t < t1 - 0.2:
        d = wpm * (1 if rng.random() < 0.6 else 3); n = S.smp(d); x = np.arange(n) / S.SR
        fx.add(t, np.sin(2 * np.pi * f * x) * np.clip(x / 0.004, 0, 1) * np.clip((d - x) / 0.004, 0, 1), 0.022 * g, 0.3); t += d + wpm * (1 if rng.random() < 0.75 else 3)
def snare(t, g=1.0):
    n = S.smp(0.22); x = np.arange(n) / S.SR
    fx.add(t, S.bp(S.noise(n), 900, 6000) * np.exp(-x / 0.05) + np.sin(2 * np.pi * 190 * x) * np.exp(-x / 0.04) * 0.6, 0.05 * g, -0.15)
def march(t0, t1, g0=0.5, g1=0.5, step=0.5):
    for k, t in enumerate(np.arange(grid(t0), t1, step)):
        g = g0 + (g1 - g0) * (t - t0) / max(1e-6, t1 - t0); snare(t, g)
        if k % 4 == 3: snare(t + step * 0.5, g * 0.6); snare(t + step * 0.75, g * 0.6)
def keys(t0, t1, n, g=1.0):
    for t in np.linspace(t0, t1, n): tick(t + rng.uniform(0, 0.03), rng.random() < 0.5, g)
def lay(t0, t1, chords, fn):
    for k, t in enumerate(bars(t0, t1)): fn(k, t, chords[k % len(chords)])
def bed(k, t, ch, vel=54, g=0.8): cello(t, ch[0] - 12, 3.8, vel + 6, g + 0.1); strings(t, ch, 4.3, vel, g, swell=1.0)
def walk(t0, t1, chords, g=1.0, top=True):
    for k, t in enumerate(np.arange(grid(t0), t1 - 0.3, 0.5)):
        ch = chords[int(k // 8) % len(chords)]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 68, 0.8 * g)
        if top and k % 2 == 0: piano(t, ch[(k // 2) % 4] + 12, 2, 54, 0.65 * g)

# ================================================================ 1. twenty past ten
q0 = lambda p: q(0, p)
waves(0.2, V[1] + 1, 1.2); drone(0.5, q0('for three hours'), (28, 40), 44, 0.8)
motif(SC[0]['start'] - 1.5, [64, 71, 67], 1.2, 66, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g))
horn(q0('around him are four'), 52, 3.5, 60, 0.9); horn(q0('the same four'), 55, 3.0, 58, 0.8)
qF = q0('for three hours'); engines(qF - 0.5, q0('he is winning') + 1, 1.0, 110); flakf(qF, q0('he is winning'), 1.8, 0.9)
for k in range(9): splashf(qF + 0.9 + k * 0.75, 0.9)
lay(qF, q0('he is winning'), (Em, C), lambda k, t, ch: strings(t, ch, 4.3, 54, 0.8, prog=TREM, swell=0.8)); march(qF, q0('he is winning'), 0.25, 0.4)
heart(q0('he is winning'), q0('three of those four'), 1.0, 0.7, 0.5, 0.9)
qO = q0('three of those four'); low.add(qO - 0.05, inst(TIMP, 40, 3, 100), 1.5); strings(qO, Em, V[1] - qO + 1.2, 76, 1.0, swell=0.6); motif(qO + 0.5, [76, 71, 67, 64], 0.5, 76, 1.0, fn=lambda t, m, v, g: piano(t, m, 4, v, g))

# ================================================================ 2. the plan
q1 = lambda p: q(1, p)
qAd, qNm, qHe = q1('but the admiral who'), q1('his name was yamamoto'), q1('he would attack')
walk(V[1] + 0.6, qAd - 0.6, (Em, G, C, D)); march(V[1] + 1, qAd - 0.6, 0.14, 0.22, 1.0)
waves(qAd - 0.5, qNm, 1.0); crackle(qAd, qNm - 0.3, 1.5); lay(qAd - 0.3, qNm - 0.3, (Am, Em, B), lambda k, t, ch: bed(k, t, ch, 52, 0.8)); boom(qAd + 0.6, 0.35, -0.4); boom(qAd + 2.2, 0.3, 0.3)
piano(q1('and as long as') + 0.4, 40, 5, 66, 0.9)
walk(qNm, V[2] - 0.5, (Em, C, Am, B)); horn(qNm + 0.4, 52, 3, 62, 0.9)
swish(qHe + 1.0, 1.3, 0.6); clink(qHe + 0.7, 96, 1.5); swish(q1('the americans would have'), 1.2, 0.6); low.add(q1('and when they did') + 0.5, inst(TIMP, 40, 3, 92), 1.2); swish(q1('and when they did') + 0.4, 1.3, 0.5)

# ================================================================ 3. the basement
q2 = lambda p: q(2, p)
qRd, qAF, qTr, qWi, qSh = q2('they could read'), q2('a f'), q2('so they set a trap'), q2('within a day'), q2('a f is short')
drone(V[2] + 0.2, qRd, (28, 40), 42, 0.7); morse(V[2] + 0.8, qRd - 0.3, 0.8); keys(V[2] + 1, qRd, 40, 0.5)
for k, m in enumerate((64, 62, 59, 62, 64, 67)): piano(q2('in a basement') + k * 1.2, m, 4, 54, 0.8)
keys(qRd, qAF - 0.3, 60, 0.7); morse(qRd, qAF - 0.4, 1.0, 880)
for k, t in enumerate(np.arange(grid(qRd), qAF - 0.4, 0.5)): pizz(t, (40, 47, 45, 47)[k % 4], 66, 0.7)
low.add(qAF - 0.05, inst(TIMP, 40, 3, 96), 1.3); strings(qAF, (40, 47, 52, 58), qTr - qAF, 56, 0.9, prog=TREM, swell=0.6); piano(q2('washington was not'), 39, 5, 66, 0.9)
waves(qTr - 0.5, qWi, 1.0); walk(qTr, qWi - 0.5, (G, D, Em, C)); morse(q2('midway was told') + 0.6, qWi - 0.4, 1.3, 620)
drone(qWi - 0.3, V[3], (28, 40, 47), 46, 0.8); morse(qWi + 0.3, qSh - 0.3, 1.0, 880)
for k in range(5): clink(qSh - 0.2 + k * 0.36, 96 + k * 2, 1.3)
low.add(qSh + 1.8, inst(TIMP, 40, 3, 98), 1.4); strings(qSh + 1.8, (40, 47, 52, 56, 59), V[3] - qSh - 1.4, 70, 1.0, swell=0.4)

# ================================================================ 4. three days
q3 = lambda p: q(3, p)
qTw, qYd, q3d, qSl, qTh = q3('he had two carriers'), q3('the repair yard'), q3('three days'), q3('she sailed'), q3('three american carriers')
waves(V[3], qYd, 1.0); lay(V[3] + 0.5, qTw - 0.4, (Em, C, G), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 60, 0.9), horn(t + 0.5, ch[1], 3, 58, 0.8)))
walk(qTw, qYd - 0.5, (Am, Em, B, Em), 0.9, False); creak(q3('a third the yorktown') + 0.4, 1.4, 1.0); cello(q3('a third the yorktown'), 28, qYd - q3('a third the yorktown'), 62, 0.9)
crackle(qYd, qTh - 0.3, 3.0)
for t in np.arange(qYd + 0.3, qTh - 0.5, 0.75): clack(t + rng.uniform(0, 0.1), 0.9, rng.choice([600, 800, 1100]))
for k, t in enumerate(np.arange(grid(qYd), qTh - 0.5, 0.5)):
    ch = (Em, G, D, C)[int(k // 8) % 4]; lvl = min(1.0, 0.5 + k / 30); pizz(t, ch[0] - 12 + (0, 7)[k % 2], 72, 0.9 * lvl); piano(t + 0.25, ch[(k * 3) % 4] + 12, 2, 56, 0.7 * lvl)
    if k % 8 == 0: strings(t, ch, 4.3, 48 + int(20 * lvl), 0.7 * lvl, swell=0.8)
thud(q3('she needed months') + 0.2, 0.9, 80); low.add(q3d, inst(TIMP, 40, 3, 96), 1.3); clink(q3d + 0.05, 96, 1.6)
whistle(qSl + 0.3, 1.6, 0.8)
waves(qTh - 0.5, V[4] + 1, 0.8); walk(qTh, V[4] - 0.4, (Em, C)); swish(qTh + 0.6, 1.2, 0.8); low.add(q3('the men setting') + 0.5, inst(TIMP, 40, 3, 90), 1.2); horn(q3('the men setting'), 52, 4, 62, 0.9)

# ================================================================ 5. the first order
q4 = lambda p: q(4, p)
q108, qHt, qNd, qSc, qOf, qLd = q4('he sent 108'), q4('they hit it hard'), q4('there is need'), q4('nagumo had a second'), q4('take off the torpedoes'), q4('load bombs')
waves(V[4], q108, 1.0); engines(V[4] + 1, qHt + 0.5, 1.1, 96, 0.2); march(V[4] + 0.5, qHt - 0.3, 0.3, 0.5)
lay(V[4] + 0.5, qHt - 0.3, (Em, C, D, Em), lambda k, t, ch: (bed(k, t, ch, 54 + 4 * k, 0.85), horn(t, ch[2], 3.5, 60, 0.8)))
for k in range(8): boom(qHt + 0.6 + k * 0.5, 0.75, rng.uniform(-0.5, 0.5))
crackle(qHt + 1, qSc, 1.6); engines(qHt, qSc - 0.3, 0.7, 120); strings(qHt, (40, 46, 52, 55), qSc - qHt, 56, 0.9, prog=TREM, swell=0.6)
morse(qNd - 0.3, qNd + 1.5, 1.3, 880)
walk(qSc, V[5] - 0.4, (Em, Am, B, Em), 0.9)
for t0 in (qOf, qLd):
    for k in range(4): clack(t0 + 0.2 + k * 0.3, 1.0, 380 + 70 * k); thud(t0 + 0.35 + k * 0.3, 0.5, 110)
for t in np.arange(qSc + 0.5, V[5] - 0.5, 1.1): creak(t, 0.5, 0.6)

# ================================================================ 6. the second order
q5 = lambda p: q(5, p)
qTn, qOn, qRv, qNo, qNw, qCd, qWt = q5('ten ships'), q5('one of them looks'), q5('nagumo reversed'), q5('there was no time'), q5('and now his first wave'), q5('he could launch'), q5('he decided to wait')
engines(V[5], qRv - 0.3, 0.8, 104, 0.0, (-0.6, 0.2)); waves(V[5], qRv, 0.6); drone(V[5] + 0.2, qRv, (28, 40), 44, 0.7)
morse(qTn - 0.2, qTn + 1.5, 1.3, 880); morse(qOn - 0.2, qOn + 1.6, 1.3, 880); low.add(qOn + 1.4, inst(TIMP, 40, 3, 94), 1.3); piano(qOn + 1.4, 28, 5, 76, 1.0)
for k, t in enumerate(np.arange(grid(qRv), qNw - 0.5, 0.5)):
    ch = (Em, Am, B, Em)[int(k // 8) % 4]; lvl = min(1.0, 0.6 + k / 40); pizz(t, ch[0] - 12 + (0, 7)[k % 2], 72, 0.9 * lvl); pizz(t + 0.25, ch[1] - 12, 60, 0.5 * lvl)
    if k % 8 == 0: strings(t, ch, 4.3, 50 + int(16 * lvl), 0.8 * lvl, prog=TREM, swell=0.6)
for t0 in (q5('take off the bombs'), q5('put the torpedoes back')):
    for k in range(4): clack(t0 + 0.2 + k * 0.3, 1.0, 380 + 70 * k); thud(t0 + 0.35 + k * 0.3, 0.5, 110)
for k in range(10): thud(q5('bombs were stacked') + k * 0.16, 0.45, 150 + 10 * k)
fx.add(q5('fuel hoses'), S.whoosh(1.4, 900, 4200, 0.9), 0.04, 0.2)
engines(qNw - 0.4, qCd, 1.2, 118, -0.1); waves(qNw, V[6], 0.8); lay(qNw, qCd - 0.3, (Am, B), lambda k, t, ch: bed(k, t, ch, 56, 0.85))
heart(qCd, qWt, 1.0, 0.7, 0.5, 0.9); strings(qCd, (40, 46, 52), qWt - qCd, 48, 0.8, prog=TREM, swell=2)
low.add(qWt + 0.2, inst(TIMP, 40, 4, 102), 1.5); cello(qWt + 0.2, 28, V[6] - qWt, 68, 1.0)

# ================================================================ 7. the torpedo planes
q6 = lambda p: q(6, p)
qTp, q8, qAl, qOf6, qTwo, q41, q34, qNt = q6('the torpedo bombers found'), q6('torpedo squadron eight'), q6('all fifteen'), q6('of thirty men'), q6('two more squadrons'), q6('forty one torpedo'), q6('thirty four did not'), q6('not one torpedo')
waves(V[6], q8, 1.0); engines(V[6], q8 - 0.3, 1.2, 108); flakf(V[6] + 0.8, q8 - 0.5, 2.2, 1.0); march(V[6] + 0.5, qTp, 0.3, 0.45)
for k in range(12): splashf(V[6] + 1.6 + k * 1.0, 0.9)
lay(V[6] + 0.4, qTp - 0.3, (Em, C, Am, B), lambda k, t, ch: strings(t, ch, 4.3, 56, 0.85, prog=TREM, swell=0.8))
volleyt = np.sort(rng.uniform(qTp, q8 - 0.5, int((q8 - qTp) * 7)))
for t in volleyt: shot(t, 0.14 * rng.uniform(0.5, 1), rng.uniform(-0.7, 0.0))
heart(qTp, q8 - 0.4, 0.8, 0.5, 0.5, 0.9); lay(qTp, q8 - 0.3, (Em, B), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 66, 1.0), strings(t, ch, 4.3, 58, 0.9, prog=TREM, swell=0.6)))
drone(q8 - 0.3, qOf6, (28, 40), 44, 0.7)
for i in range(15): piano(qAl - 0.3 + i * 0.1, 76 - i, 2.5, 58, 0.7); tick(qAl - 0.3 + i * 0.1, False, 1.0)
piano(qAl + 1.4, 28, 6, 76, 1.1); piano(qAl + 1.4, 40, 6, 66, 0.9)
waves(qOf6 - 0.4, qTwo, 1.6)
for k, m in enumerate((64, 62, 59, 57, 59, 52)): cello(qOf6 + 0.3 + k * 1.5, m - 12, 1.6, 60, 0.95)
piano(q6('a young pilot') + 0.5, 64, 4, 56, 0.8); piano(q6('a young pilot') + 1.5, 59, 4, 52, 0.8)
lay(qTwo - 0.3, V[7] - 0.3, (Am, Em, B), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 60, 0.9), piano(t + 1, ch[2], 4, 50, 0.7), piano(t + 2.5, ch[3], 4, 48, 0.7)))
for i in range(34): tick(q34 - 0.2 + i * 0.04, False, 0.8)
low.add(qNt + 0.1, inst(TIMP, 40, 4, 98), 1.4); piano(qNt + 0.1, 28, 6, 80, 1.2)

# ================================================================ 8. McClusky
q7 = lambda p: q(7, p)
qHi, qNo7, qFu, qWn, qSw, qFo = q7('and high above'), q7('there was nothing'), q7('his planes were running'), q7('he went on'), q7('and then he saw'), q7('mcclusky followed')
waves(V[7], qHi, 1.0); engines(V[7], qHi, 0.8, 130); walk(V[7] + 0.5, qHi - 0.5, (Em, G, Am, B), 0.9)
engines(qHi - 0.5, V[8] + 1, 1.3, 86, 0.0, (-0.3, 0.3))
lay(qHi, qNo7 - 0.3, (Em, C, G, D), lambda k, t, ch: (strings(t, ch, 4.3, 52, 0.8, swell=1.2), horn(t + 1, ch[2], 2.5, 58, 0.8)))
drone(qNo7, qSw, (28, 40), 46, 0.8); piano(qNo7 + 0.6, 64, 5, 56, 0.8); piano(qNo7 + 1.8, 62, 5, 52, 0.8)
heart(qFu, qSw, 1.0, 0.8, 0.45, 0.7)
for k, t in enumerate(np.arange(qFu + 0.4, qWn, 0.9)): tick(t, True, 1.2); tick(t + 0.45, False, 0.9)
piano(qWn + 0.3, 40, 5, 70, 1.0); piano(qWn + 0.3, 52, 5, 62, 0.9)
for k, m in enumerate((64, 67, 71, 76)): harp(qSw + 0.3 + k * 0.3, m, 66, 0.9)
lay(qSw, V[8] - 0.3, (C, D, Em, B), lambda k, t, ch: (bed(k, t, ch, 54 + 5 * k, 0.85), horn(t, ch[2], 3.5, 60 + 3 * k, 0.9)))
march(q7('it had stayed behind'), V[8], 0.2, 0.5); low.add(qFo + 0.3, inst(TIMP, 40, 3, 100), 1.4)

# ================================================================ 9. five minutes
q8_ = lambda p: q(8, p)
qKg, qAk, qTh8, qSm, qPt, qBy, qTk = q8_('the carrier kaga') - 0.4, q8_('the flagship akagi') - 0.4, q8_('it went through') - 0.2, q8_('and at that same moment') - 0.4, q8_('they put three bombs'), q8_('by 1026') - 0.4, q8_('it had taken')
low.add(SC[8]['start'] - 0.1, inst(TIMP, 40, 3, 104), 1.5); march(V[8] + 0.3, qBy, 0.5, 0.65); engines(V[8], qBy, 1.2, 100)
for i in range(6): dive(SC[8]['start'] + 0.6 + i * 0.28, 2.2, 0.8, 0.4)
lay(V[8] + 0.3, qBy - 0.2, (Em, C, Am, B), lambda k, t, ch: (strings(t, ch, 4.3, 64, 1.0, prog=TREM, swell=0.5), cello(t, ch[0] - 12, 3.8, 70, 1.0), horn(t, ch[1], 3.5, 66, 0.9)))
for i in range(6): dive(qKg + 0.2 + i * 0.55, 2.0, 1.0, 0.5)
for k, h in enumerate((2.0, 2.55, 3.1, 3.65)): boom(qKg + h, 1.25, -0.3 + k * 0.15)
crackle(qKg + 2, qBy, 2.5)
dive(qAk + 0.3, 1.6, 0.8, 0.0); fx.add(qAk + 0.7, S.whoosh(max(0.5, qTh8 - qAk - 0.5), 2400, 500, 0.9), 0.06, 0.0)
boom(qTh8 + 0.2, 1.5, 0.0)
for i in range(6): boom(qTh8 + 0.6 + i * 0.33, 0.8, rng.uniform(-0.6, 0.6))
for i in range(5): dive(qPt - 1.9 + i * 0.55, 2.0, 1.0, -0.5)
for k in range(3): boom(qPt + 0.2 + k * 0.55, 1.25, 0.3 - k * 0.15)
waves(qBy - 0.3, V[9], 1.0); crackle(qBy, V[9], 3.0); drone(qBy, V[9], (28, 40, 47), 52, 0.9)
for k, m in enumerate((64, 62, 59, 57, 55, 52)): cello(qBy + 0.4 + k * 1.2, m - 12, 1.3, 68, 1.0)
low.add(qTk + 0.6, inst(TIMP, 40, 4, 100), 1.4); piano(qTk + 0.6, 28, 6, 80, 1.2); piano(qTk + 0.6, 40, 6, 70, 1.0)

# ================================================================ 10. the last carrier
q9 = lambda p: q(9, p)
qSt, qHY, qCr, qAg, qSp, qAf, q5c, q4h, qYm, qTn9 = q9('she struck back'), q9('and hit the yorktown'), q9('the crew patched'), q9('they hit her again'), q9('this time she stopped'), q9('but that afternoon'), q9('at five oclock') - 0.3, q9('four hits'), q9('yamamoto was hundreds'), q9('he turned the fleet')
waves(V[9], qYm, 1.0); engines(qSt, qHY + 2, 1.0, 112, 0.1); march(qSt, qHY, 0.3, 0.5)
lay(V[9] + 0.4, qHY - 0.4, (Em, B), lambda k, t, ch: bed(k, t, ch, 56, 0.85))
for k in range(3): boom(qHY + 0.3 + k * 0.5, 1.0, 0.2 * k - 0.2)
crackle(qHY + 0.5, qCr + 1.5, 1.6)
for t in np.arange(qCr + 0.2, q9('they thought they were'), 0.4): clack(t + rng.uniform(0, 0.08), 0.8, rng.choice([500, 700, 900]))
walk(qCr, qAg - 0.3, (G, D, Em, C)); engines(qAg, qAg + 2.6, 1.0, 104)
for k in range(2): splashf(qAg + 1.3 + k * 0.6, 1.4); boom(qAg + 1.3 + k * 0.6, 1.0, -0.2 + 0.4 * k)
cello(qSp - 0.3, 28, qAf - qSp, 66, 1.0); creak(qSp + 0.3, 1.8, 1.2)
lay(qAf - 0.3, q5c, (Am, B), lambda k, t, ch: (bed(k, t, ch, 56, 0.85), horn(t, ch[1], 3.5, 60, 0.8)))
engines(q5c, q4h + 2, 1.2, 100); march(q5c, q4h, 0.4, 0.6)
for i in range(6): dive(q5c + 0.5 + i * 0.5, 2.0, 1.0, 0.5)
for k, h in enumerate((2.3, 2.8, 3.3, 3.8)): boom(q5c + h, 1.25, -0.3 + k * 0.15)
strings(q5c, (40, 47, 52, 55), q4h - q5c + 1.5, 62, 1.0, prog=TREM, swell=0.6); crackle(q5c + 2.3, qYm, 2.4)
waves(qYm - 0.4, V[10] + 1, 1.2); drone(qYm - 0.3, V[10], (28, 40), 46, 0.8)
for k, m in enumerate((59, 57, 55, 52, 47, 40)): cello(qYm + 0.6 + k * 1.3, m - 12, 1.4, 62, 1.0)
horn(qTn9, 52, 4, 56, 0.8)

# ================================================================ 11. the count
q10 = lambda p: q(10, p)
qUS, qJp, qWd = q10('the united states lost'), q10('in japan the newspapers'), q10('the wounded were')
lay(V[10] + 0.6, qJp - 0.5, (Em, C, Am, B), lambda k, t, ch: (pizz(t, ch[0] - 12, 66, 0.7), pizz(t + 2, ch[1] - 12, 58, 0.5), piano(t, ch[1], 4, 52, 0.75), piano(t + 1, ch[2], 4, 48, 0.7), piano(t + 2, ch[3], 4, 50, 0.7), piano(t + 3, ch[2], 4, 46, 0.7)))
for k in range(4): thud(SC[10]['start'] + 0.6 + k * 0.25, 0.7, 80)
thud(q10('a heavy cruiser'), 0.6, 100); keys(q10('about 250 planes'), q10('about 250 planes') + 0.6, 12, 0.7); low.add(q10('more than 3000'), inst(TIMP, 40, 3, 90), 1.2)
thud(qUS + 0.5, 0.7, 80); thud(q10('one destroyer'), 0.5, 110); keys(q10('about 150 planes'), q10('about 150 planes') + 0.5, 8, 0.7); piano(q10('307 men'), 40, 5, 66, 0.9)
thud(qJp + 0.5, 0.9, 150); swish(qJp, 1.2, 0.5); walk(qJp, qWd - 0.3, (G, D), 0.8); cello(qWd, 28, V[11] - qWd, 62, 0.9); piano(qWd + 0.6, 40, 5, 60, 0.9)

# ================================================================ 12. small things
q11 = lambda p: q(11, p)
qAn_, qOne, qKp, qNm_, qSub, qAn, qBat, qCol = q11('and it turned on'), q11('and one pilot'), q11('and kept looking'), q11('admiral nimitz said'), q11('subscribe'), q11('animal facts'), q11('historys greatest'), q11('worlds craziest')
waves(V[11], qAn_, 1.0); lay(V[11] + 0.5, qAn_ - 0.4, (Em, C, G, D), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 58, 0.9), arp(t, ch, 52, 0.85)))
for p, m in (('a code half', 76), ('a ship fixed', 79), ('men in old planes', 83)): harp(q11(p), m, 70, 1.0); pizz(q11(p), m - 36, 70, 0.8)
morse(q11('a code half') + 0.3, q11('a code half') + 1.3, 0.8, 880); clack(q11('a ship fixed') + 0.5, 0.8, 700); clack(q11('a ship fixed') + 0.8, 0.7, 900)
lay(qAn_, qOne - 0.4, (Am, Em, C), lambda k, t, ch: (cello(t, ch[0] - 12, 3.8, 56, 0.9), piano(t, ch[1], 4, 54, 0.8), piano(t + 1.5, ch[2], 4, 50, 0.75), piano(t + 3, ch[3], 4, 50, 0.75)))
engines(qOne - 0.3, qSub + 0.5, 1.2, 88, 0.0, (-0.2, 0.2))
strings(qKp - 0.2, (28, 40, 47, 52, 56, 59, 64), qSub - qKp + 0.4, 66, 1.0, swell=1.8)                 # E major
for k, m in enumerate((64, 68, 71, 76, 80, 83)): harp(qKp + 0.4 + k * 0.22, m, 68, 0.9)
motif(qNm_ + 0.8, [76, 71, 68, 64], 0.9, 62, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g)); horn(qNm_ + 0.4, 52, 5, 58, 0.8)
e0 = qSub
low.add(e0, inst(TIMP, 40, 3, 92), 1.2); strings(e0, (40, 47, 52, 56, 59, 64), DUR - e0 - 0.5, 70, 1.0, swell=0.8)
for k, (t, m) in enumerate(zip(np.arange(e0 + 0.5, DUR - 5.5, 1.0), [64, 71, 69, 68, 64, 71, 73, 71, 68, 69, 71, 76] * 3)): harp(t, m + 12, 70, 0.9); piano(t, m, 3.5, 52, 0.6)
march(e0 + 0.5, DUR - 6, 0.16, 0.16, 1.0)
for at, m in ((qAn, 76), (qBat, 80), (qCol, 83)): harp(at, m, 76, 1.0); harp(at + 0.12, m + 7, 70, 0.8)
tend = DUR - 5.2
for k, m in enumerate((40, 52, 59, 64, 68, 71, 76)): piano(tend + k * 0.16, m, 6, 68, 1.0)
low.add(tend, inst(TIMP, 40, 4, 80), 1.0)

# ---------------------------------------------------------------- mix
# an eight-minute film is too long to hold every bus and its copies at once: finish one bed, free it, then the other
import gc
_cache.clear()
DN = S.smp(DUR); tt_ = np.arange(DN) / S.SR; fade = np.clip(tt_ / 0.5, 0, 1) * np.clip((DUR - tt_) / 3.0, 0, 1)
f = fx.out(True).astype(np.float32); del fx; gc.collect()
lo_ = low.out(True)[:, :mus.x.shape[1]]
m = mus.out(True) * 1.1 + lo_ * 0.85
wet = S.reverb(mus.out(True) * 0.6 + lo_ * 0.25, S.hall(4.0, 1.3, 0.03, 220, 6500), 0.5)
del mus, low, lo_; gc.collect()
m = (m + wet)[:, :DN]; del wet; gc.collect()
m = S.eq(m, [('lowshelf', 110, -5.0, 0.7), ('peak', 280, -5.5, 0.9), ('peak', 520, -3.0, 1.0), ('peak', 1500, 2.0, 0.8), ('peak', 3000, 5.0, 0.8), ('highshelf', 4500, 10.0, 0.7)])
S.write('music.wav', S.master(m * fade, lufs=-20.0, fade=0, ceiling=0.8)); del m; gc.collect()
f = f.astype(np.float64); f = (f + S.reverb(f * 0.5, S.plate(1.8, 0.5), 0.45))[:, :DN]
f = S.eq(S.hp(f, 75), [('lowshelf', 140, -5.0, 0.7), ('peak', 2500, 3.0, 0.8), ('highshelf', 5000, 3.0, 0.7)])
S.write('fx.wav', S.limiter(f * fade * 2.2, 0.7))
print('music.wav, fx.wav', round(DUR, 2), 's')
