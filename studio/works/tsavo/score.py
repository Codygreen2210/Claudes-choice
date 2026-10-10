#!/usr/bin/env python3
"""score.py: the music and sound for The Man-Eaters of Tsavo, written against the narration's own timing.

Reads timing.json (from film_voice.py), writes music.wav and fx.wav.
E minor at 60 beats a minute. Night scenes run on a low drone, crickets and a drum like a heartbeat;
the daylight scenes get a thumb-piano figure. It turns to major twice: the morning after the first
lion, and in front of the glass case in Chicago.
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

S.seed(1898)
rng = np.random.default_rng(1898)
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

# ================================================================ 1. the tent
qM, qL, qT, qA, qG, qF, qN = q(0, 'its the middle'), q(0, 'a lion puts'), q(0, 'and takes him'), q(0, 'he gets his arms'), q(0, 'let go'), q(0, 'he was the first'), q(0, 'he would not')
crickets(0.3, qT + 0.2, 1.0); drone(0.5, qT + 0.3)
motif(SC[0]['start'] - 1.5, [64, 71, 69], 1.2, 70, 0.9); kal(qM + 1.0, 67, 66, 0.8); kal(qM + 3.0, 64, 62, 0.8)
heart(qL - 1.0, qT, 1.0, 0.6, 0.35, 0.7)
growl(qT - 0.1, 1.6, 1.3, 0.2); low.add(qT + 0.05, inst(TIMP, 40, 3, 105), 1.6); strings(qT + 0.1, (40, 46, 52, 58), qG - qT, 70, 0.9, prog=TREM, swell=0.4)
growl(qA + 0.2, 1.2, 0.8, 0.2)
cello(qG + 0.9, 40, qF - qG, 60, 0.8)
crickets(qF, V[1] + 1, 0.7); drone(qF, V[1] + 0.5, (28, 40, 47), 46, 0.7)
ti = qN + 1.0
low.add(ti - 0.05, inst(TIMP, 40, 3, 96), 1.4); strings(ti, Em, V[1] - ti + 1.2, 74, 0.9, swell=0.6)
motif(ti + 0.4, [76, 71, 67, 64], 0.5, 78, 1.0)

# ================================================================ 2. the railway
b2 = bars(V[1] + 1.0, V[2] - 1.0)
for k, t in enumerate(b2):
    ch = (G, Em, C, D)[k % 4]
    pizz(t, ch[0] - 12, 72, 0.8); pizz(t + 2, ch[1] - 12, 62, 0.6)
    for e in range(8):
        if (e + k) % 3 != 2: kal(t + e * 0.5, ch[(e * 2 + k) % 4] + 12, 66 + 6 * (e % 2 == 0), 0.75)
    if k % 2 == 0: strings(t, ch, 8.3, 46, 0.5, swell=2)
qP = q(1, 'the man in charge'); piano(qP + 1.4, 52, 4, 62, 0.9); piano(qP + 1.4, 40, 4, 58, 0.8)

# ================================================================ 3. the devils
qCame, qFen, qJump, qCrawl, qFire, qTin, qNoth, qAfter, qDev, qBew = q(2, 'they came at night'), q(2, 'they built fences'), q(2, 'the lions jumped'), q(2, 'or crawled'), q(2, 'they kept fires'), q(2, 'they banged'), q(2, 'nothing worked'), q(2, 'after a while'), q(2, 'they said these'), q(2, 'beware brothers')
crickets(V[2], qAfter, 0.9); drone(V[2] + 0.3, qCame, (28, 40, 47), 50, 0.8)
low.add(SC[2]['start'], inst(TIMP, 40, 3, 90), 1.2); motif(SC[2]['start'] + 0.6, [52, 55, 59], 1.0, 70, 1.0, fn=lambda t, m, v, g: piano(t, m, 4, v, g))
heart(qCame, qNoth, 1.0, 0.75, 0.4, 0.75)
for k, t in enumerate(bars(qCame, qNoth)):
    up = min(1, k / 4); strings(t, (Em, C, Am, B)[k % 4], 4.3, 44 + int(26 * up), 0.5 + 0.4 * up, prog=TREM, swell=0.8)
growl(q(2, 'and pulled men') + 0.2, 1.2, 0.8, 0.1); swish(qJump - 0.1, 1.4, 0.5); thud(qJump + 0.85, 0.7, 60); growl(qCrawl + 0.3, 1.5, 0.7, -0.4)
crackle(qFire, qAfter, 1.0)
for t in np.arange(qTin + 0.1, qNoth - 0.1, 0.19): clack(t + rng.uniform(0, 0.03), 0.9, rng.choice([1500, 1900, 2300]))
low.add(qNoth, inst(TIMP, 40, 3, 108), 1.6); piano(qNoth, 28, 5, 84, 1.2); piano(qNoth, 40, 5, 76, 1.0)
crackle(qAfter, V[3], 1.4); drone(qAfter, V[3] + 0.3, (28, 34, 40), 56, 0.9)
strings(qDev, (52, 55, 58, 61), qBew - qDev + 0.4, 50, 0.7, prog=TREM, swell=2)
for k, m in enumerate((52, 51, 49, 46, 45)): cello(qDev + 0.4 + k * 1.3, m - 12, 1.25, 66, 0.9)
growl(qDev + 1.8, 2.2, 0.8, 0.0); low.add(qBew, inst(TIMP, 40, 3, 100), 1.4); strings(qBew, (40, 47, 52, 55, 59), V[3] - qBew + 0.6, 66, 0.9, swell=0.5)

# ================================================================ 4. the trap
qSo, qWork, qIn, qFell, qFace, qFroze, qFired, qHit, qBar, qOut = q(3, 'so he built'), q(3, 'it worked'), q(3, 'a lion walked in'), q(3, 'the door fell'), q(3, 'and the two soldiers'), q(3, 'froze'), q(3, 'when they finally'), q(3, 'but they did'), q(3, 'one bar blew'), q(3, 'and the lion walked')
crickets(V[3], qSo, 0.9); drone(V[3] + 0.3, qSo, (28, 40), 44, 0.7)
for t, m in zip(np.arange(grid(V[3] + 1.5), qSo - 1, 2.0), [64, 67, 64, 62, 64, 59]): kal(t, m, 62, 0.8)
growl(q(3, 'the lions struck') + 0.7, 1.2, 0.45, 0.6)
for k, t in enumerate(np.arange(grid(qSo), qWork - 0.5, 0.5)):
    ch = (Em, G, Am, B)[int(k // 8) % 4]
    if k % 4 != 3: kal(t, ch[(k * 3) % 4] + 12, 68, 0.8)
    if k % 4 == 0: pizz(t, ch[0] - 12, 70, 0.8)
crickets(qWork, V[4], 0.8); drone(qWork, qBar, (28, 40, 47), 50, 0.8)
heart(qWork + 0.5, qFell, 0.9, 0.55, 0.45, 0.8)
thud(qFell + 0.08, 1.8, 50); clack(qFell + 0.08, 1.6, 260); growl(qFell + 0.4, 1.8, 1.2, 0.2)
heart(qFace, qFired, 0.5, 0.5, 0.55, 0.55); growl(qFroze + 0.3, 1.6, 1.0, 0.2)
for k in range(21): shot(qFired + 0.25 + k * 0.2 + rng.uniform(0, 0.04), 0.45 + 0.15 * rng.random(), -0.3)
growl(qFired + 1.6, 1.8, 1.0, 0.2); growl(qHit - 0.3, 1.4, 0.8, 0.2)
clack(qBar + 0.05, 1.8, 1300); clink(qBar + 0.5, 84, 1.6, 0.4); thud(qBar + 0.95, 0.6, 90)
for k, m in enumerate((64, 59, 55, 52, 47, 40)): piano(qBar + 0.3 + k * 0.28, m, 4, 70 - 3 * k, 0.9)
cello(qOut, 28, V[4] - qOut + 0.3, 70, 1.0); strings(qOut, (40, 47, 52), V[4] - qOut + 0.3, 50, 0.7, swell=1)

# ================================================================ 5. the strike
qTools, qHund, qLying, qClimb, qLeft, qStop, qTwo = q(4, 'they put down'), q(4, 'hundreds of them'), q(4, 'by lying down'), q(4, 'then they climbed'), q(4, 'and left'), q(4, 'the railway stopped'), q(4, 'because of two')
for k, t in enumerate(np.arange(grid(V[4] + 0.6), qStop - 1.0, 0.5)):
    ch = (Em, Em, C, D)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 70, 0.8)
    if k % 2 == 0: kal(t, ch[(k // 2) % 4] + 12, 66, 0.7)
for k in range(6): thud(qTools + 0.1 + k * 0.09, 0.35, 140 + 20 * k)
chuff(qHund - 0.6, qLying + 1.0, 4.0, 1.2, 1.0); whistle(qHund + 0.1, 1.0, 1.0); whistle(qLying + 0.2, 0.5, 0.8)
chuff(qLeft - 0.2, qStop + 0.6, 1.2, 4.5, 1.0); whistle(qLeft, 1.3, 0.9)
drone(qStop, V[5] + 0.3, (28, 40), 46, 0.8); crickets(qStop + 0.5, V[5], 0.5)
low.add(qTwo, inst(TIMP, 40, 3, 98), 1.4); growl(qTwo + 0.5, 1.8, 0.7, 0.4)

# ================================================================ 6. the platform
qNinth, qSo6, qDusk, qCame6, qNot6, qTwo6, qRick, qMid, qShot, qMorn, q98, q8 = q(5, 'on the ninth'), q(5, 'so he built'), q(5, 'and at dusk'), q(5, 'the lion came'), q(5, 'it had noticed'), q(5, 'for about two hours'), q(5, 'four rickety'), q(5, 'near midnight'), q(5, 'and fired') + 0.45, q(5, 'in the morning'), q(5, 'nine feet'), q(5, 'it took eight')
for k, t in enumerate(bars(V[5] + 0.8, qDusk - 0.5)):
    ch = (Em, C, G, D)[k % 4]; cello(t, ch[0] - 12, 3.8, 66, 1.0); piano(t, ch[1], 4, 56, 0.8); piano(t + 1, ch[2], 4, 52, 0.7); piano(t + 2, ch[3], 4, 54, 0.7)
for k in range(5): thud(qSo6 + 0.9 + k * 0.42, 0.4, 170)
crickets(qDusk, qShot, 1.0); drone(qDusk, qShot - 0.2, (28, 40), 48, 0.8)
kal(qDusk + 1.0, 64, 64, 0.8); kal(qDusk + 2.2, 59, 60, 0.8)
growl(qCame6 + 0.6, 1.6, 0.6, 0.6)
heart(qNot6, qTwo6, 1.0, 1.0, 0.45, 0.5)
heart(qTwo6, qMid, 0.95, 0.5, 0.5, 0.95)
for k, t in enumerate(bars(qTwo6, qMid)): up = min(1, (k + 1) / 4); strings(t, (40, 46, 52, 55 + k), 4.3, 46 + int(34 * up), 0.5 + 0.5 * up, prog=TREM, swell=0.8)
growl(qTwo6 + 2.0, 1.8, 0.6, -0.5); growl(q(5, 'and closer') + 0.2, 1.8, 0.9, 0.3)
for k in range(5): clack(qRick + 0.2 + k * 0.5, 0.5, 240)
heart(qMid, qShot - 0.3, 0.45, 0.4, 0.95, 1.0)
shot(qShot, 2.2, 0.1); growl(qShot + 0.25, 1.4, 1.1, 0.4)
cello(qShot + 2.2, 28, max(1.0, qMorn - qShot - 2.4), 48, 0.7)
strings(qMorn - 0.2, (43, 50, 55, 59, 62), V[6] - qMorn + 0.6, 66, 1.0, swell=1.6)            # morning: G major
for k, m in enumerate((67, 71, 74, 79, 83)): harp(qMorn + 0.3 + k * 0.22, m, 66, 0.9)
motif(q98, [71, 74, 79, 74], 1.0, 70, 0.9); pizz(q8, 43, 74, 0.9); pizz(q8 + 1, 50, 66, 0.8)

# ================================================================ 7. the second lion
q20, q3r, q9, q6, q29, qWrote, qStill, qBack, qFeb = q(6, 'it took twenty'), q(6, 'three rifles'), q(6, 'and nine shots'), q(6, 'six of them'), q(6, 'on the twenty'), q(6, 'patterson wrote'), q(6, 'still trying'), q(6, 'the men came back'), q(6, 'the bridge was')
crickets(V[6], qBack - 0.5, 0.8); drone(V[6] + 0.3, qWrote + 0.5, (28, 40, 47), 46, 0.8)
low.add(SC[6]['start'], inst(TIMP, 40, 3, 84), 1.1)
for k in range(20): tick(q20 + 0.1 + k * (q3r - q20 - 0.3) / 20, k % 2 == 0, 0.8)
for k in range(3): clack(q3r + k * 0.18, 0.8, 380)
for k in range(9): shot(q9 + 0.1 + k * 0.07, 0.22, -0.2 + 0.05 * k)
for k in range(6): clink(q6 + k * 0.08, 86 + k, 0.9, 0.2)
shot(q29 + 1.0, 1.4, 0.2); thud(q29 + 1.7, 1.0, 55)
for k, m in enumerate((64, 62, 59, 57, 55, 52)): cello(qWrote + k * 1.1, m - 12, 1.2, 62, 0.9)
growl(qWrote + 1.4, 2.0, 0.7, 0.2); growl(qStill + 0.2, 2.4, 0.45, 0.2)
strings(qWrote, (40, 47, 52), qBack - qWrote, 48, 0.7, swell=1.5)
for k, t in enumerate(np.arange(grid(qBack), V[7] - 0.6, 0.5)):
    ch = (G, C, G, D)[int(k // 8) % 4]; pizz(t, ch[0] - 12 + (0, 7)[k % 2], 72, 0.8)
    if k % 2 == 0: kal(t, ch[(k // 2) % 4] + 12, 70, 0.8)
    if k % 8 == 0: strings(t, ch, 4.3, 56, 0.7, swell=0.8)
chuff(qFeb + 1.2, V[7] + 0.5, 3.0, 3.6, 0.9); whistle(qFeb + 1.5, 1.2, 0.9)

# ================================================================ 8. the count
q28, q135, qCent, q2009, qBones, qHair, qAns, q35, q11, q24b, qOnly, qNot8 = q(7, 'say 28'), q(7, 'said 135'), q(7, 'for a century'), q(7, 'then in 2009'), q(7, 'in its bones'), q(7, 'and in its hair'), q(7, 'their answer'), q(7, 'about 35'), q(7, 'one lion ate'), q(7, 'the other'), q(7, 'though that only'), q(7, 'not everyone')
for k, t in enumerate(bars(V[7] + 0.6, qAns - 0.5)):
    ch = (Am, C, G, Em)[k % 4]; pizz(t, ch[0] - 12, 66, 0.7); pizz(t + 2, ch[1] - 12, 58, 0.5)
    piano(t, ch[1], 4, 52, 0.75); piano(t + 1, ch[2], 4, 48, 0.7); piano(t + 2, ch[3], 4, 50, 0.7); piano(t + 3, ch[2], 4, 46, 0.7)
thud(q28, 0.7, 80); thud(q135, 0.9, 70); piano(q135, 33, 4, 70, 1.0)
for i in range(22): tick(qBones + 0.2 + i * 0.03, True, 0.5); tick(qHair + 0.2 + i * 0.03, False, 0.5)
strings(qAns, (45, 52, 57, 60), V[8] - qAns, 50, 0.7, swell=1.5)
low.add(q35, inst(TIMP, 45, 3, 80), 1.0)
for i in range(11): kal(q11 - 0.2 + i * 0.05, 76 - (i % 3), 60, 0.6)
for i in range(24): kal(q24b - 0.2 + i * 0.03, 69 - (i % 4), 54, 0.5)
piano(qNot8, 33, 6, 74, 1.1); piano(qNot8, 45, 6, 66, 0.9); cello(qNot8, 33, V[8] - qNot8, 60, 0.8)

# ================================================================ 9. why, brothers, Chicago
qPlague, qTooth, qRoot, qSleep, qOne, q2024, qDNA, qTwo9, qBro, qHow, qExist, qRugs, qSold, q5k, qChi, qDisp, qWalk, qSub, qAn, qBat, qCol = q(8, 'a cattle plague'), q(8, 'and one of the lions'), q(8, 'at the root'), q(8, 'a sleeping man'), q(8, 'one more thing'), q(8, 'in 2024'), q(8, 'and read the dna'), q(8, 'the two maneaters'), q(8, 'were brothers'), q(8, 'and how could'), q(8, 'because they still'), q(8, 'patterson kept'), q(8, 'then he sold'), q(8, 'for 5000'), q(8, 'theyre in chicago'), q(8, 'on display'), q(8, 'you can walk'), q(8, 'subscribe'), q(8, 'animal facts'), q(8, 'historys greatest'), q(8, 'worlds craziest')
for k, t in enumerate(bars(V[8] + 0.6, qSleep - 0.8)):
    ch = (Em, C, Am, B)[k % 4]; arp(t, ch, 52, 0.85); cello(t, ch[0] - 12, 3.8, 58, 0.8)
for i in range(7): thud(qPlague + 0.4 + i * 0.22, 0.25, 110)
piano(qRoot, 40, 5, 70, 1.0); clink(qRoot + 0.05, 100, 0.9)
crickets(qSleep - 0.4, qOne, 0.9); drone(qSleep - 0.3, qOne, (28, 40), 46, 0.8); low.add(qSleep + 0.2, inst(TIMP, 40, 3, 86), 1.2); growl(qSleep + 1.3, 1.6, 0.45, -0.5)
for k, t in enumerate(np.arange(grid(qOne), qTwo9 - 0.3, 0.5)):
    ch = (Em, G, C, D)[int(k // 8) % 4]
    if k % 4 != 3: kal(t, ch[(k * 3) % 4] + 12, 64, 0.75)
    if k % 4 == 0: pizz(t, ch[0] - 12, 66, 0.7)
strings(qTwo9, C, qHow - qTwo9 + 0.3, 58, 0.9, swell=1.2); low.add(qBro, inst(TIMP, 36, 3, 90), 1.2); piano(qBro, 60, 5, 70, 1.0); piano(qBro + 0.4, 64, 5, 66, 0.9); piano(qBro + 0.8, 67, 5, 66, 0.9)
crackle(qHow, qChi, 1.2)
for k, t in enumerate(bars(qHow, qChi - 0.5)): ch = (Am, Em, C, B)[k % 4]; cello(t, ch[0] - 12, 3.8, 60, 0.9); piano(t + 1, ch[2], 4, 50, 0.7); piano(t + 2.5, ch[3], 4, 48, 0.7)
clink(q5k, 96, 1.6); clink(q5k + 0.14, 103, 1.2); clink(q5k + 0.3, 108, 0.8)
t0 = qChi - 0.2                                                                              # the glass case: E major
strings(t0, (40, 47, 52, 56, 59, 64), qSub - t0 + 0.4, 68, 1.0, swell=1.8)
for k, m in enumerate((64, 68, 71, 76, 80, 83)): harp(qDisp + k * 0.22, m, 68, 0.9)
motif(qWalk, [76, 71, 68, 64], 0.8, 66, 0.9, fn=lambda t, m, v, g: piano(t, m, 4, v, g))
e0 = qSub
low.add(e0, inst(TIMP, 40, 3, 92), 1.2); strings(e0, (40, 47, 52, 56, 59, 64), DUR - e0 - 0.5, 70, 1.0, swell=0.8)
for k, (t, m) in enumerate(zip(np.arange(e0 + 0.5, DUR - 5.5, 1.0), [64, 71, 69, 68, 64, 71, 73, 71, 68, 69, 71, 76] * 3)): kal(t, m + 12, 72, 0.9); piano(t, m, 3.5, 52, 0.6)
for at, m in ((qAn, 76), (qBat, 80), (qCol, 83)): harp(at, m, 76, 1.0); harp(at + 0.12, m + 7, 70, 0.8)
tend = DUR - 5.2
for k, m in enumerate((40, 52, 59, 64, 68, 71, 76)): piano(tend + k * 0.16, m, 6, 68, 1.0)
low.add(tend, inst(TIMP, 40, 4, 80), 1.0)

# ---------------------------------------------------------------- mix
IR = S.hall(4.0, 1.3, 0.03, 220, 6500)
m = mus.out(True) + low.out(True)[:, :mus.x.shape[1]]
m = m + S.reverb(mus.out(True) * 0.6 + low.out(True)[:, :mus.x.shape[1]] * 0.25, IR, 0.5)
m = m[:, :S.smp(DUR)]
m = S.eq(m, [('lowshelf', 110, -4.0, 0.7), ('peak', 280, -4.0, 0.9), ('peak', 520, -2.0, 1.0), ('peak', 3000, 2.0, 0.8), ('highshelf', 5500, 4.5, 0.7)])
f = fx.out(True); f = f + S.reverb(f * 0.5, S.plate(1.8, 0.5), 0.45); f = f[:, :S.smp(DUR)]
tt_ = np.arange(m.shape[1]) / S.SR
fade = np.clip(tt_ / 0.5, 0, 1) * np.clip((DUR - tt_) / 3.0, 0, 1)
S.write('music.wav', S.master(m * fade, lufs=-20.0, fade=0, ceiling=0.8))
S.write('fx.wav', S.limiter(S.hp(f, 45) * fade * 2.0, 0.7))
print('music.wav, fx.wav', round(DUR, 2), 's')
