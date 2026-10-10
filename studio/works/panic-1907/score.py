#!/usr/bin/env python3
"""score.py: the music and sound for the Panic of 1907 film, written against the narration's own timing.

Reads timing.json (made by assemble.py from the voice takes), writes music.wav and fx.wav.
D minor at 60 beats a minute, so the bar line and the mantel clock keep the same second.
The film turns to D major twice: when the door is unlocked, and when the Federal Reserve Act passes.
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

S.seed(1907)
rng = np.random.default_rng(1907)
mus = S.Bus(DUR, tail=6); low = S.Bus(DUR, tail=6); fx = S.Bus(DUR, tail=4)
_cache = {}
def inst(prog, m, dur, vel):
    k = (prog, m, round(dur, 2), vel)
    if k not in _cache: _cache[k] = S.sfhit(int(m), program=prog, bank=0, channel=0, vel=int(vel), dur=dur + 0.6)
    return _cache[k]
PIANO, STR, TREM, CELLO, BASS, PIZZ, HARP, TIMP, BELL = 0, 48, 44, 42, 43, 45, 46, 47, 14
def piano(t, m, dur=2.5, vel=70, g=1.0, pan=0.0): mus.add(t, inst(PIANO, m, dur, vel), g * 2.2, pan)
def strings(t, notes, dur, vel=60, g=1.0, prog=STR, swell=1.2):
    for j, m in enumerate(notes):
        y = inst(prog, m, dur, vel).copy(); n = y.shape[1]; e = np.minimum(1, np.arange(n) / (swell * S.SR)) ** 1.5
        (low if m < 50 else mus).add(t, y * e, g * 1.5, (-0.3, 0.2, -0.1, 0.3)[j % 4])
def cello(t, m, dur, vel=70, g=1.0): low.add(t, inst(CELLO, m, dur, vel), g * 0.9, 0.15)
def pizz(t, m, vel=80, g=1.0): low.add(t, inst(PIZZ, m, 0.6, vel), g * 0.8, -0.1)
def harp(t, m, vel=70, g=1.0): mus.add(t, inst(HARP, m, 2.0, vel), g * 1.4, 0.25)

Dm, Bb, Gm, A, F, C = (50, 57, 62, 65), (46, 53, 58, 62), (43, 50, 55, 58), (45, 52, 57, 61), (41, 48, 53, 57), (48, 55, 60, 64)
D, G, A7 = (50, 57, 62, 66), (43, 50, 55, 59), (45, 52, 55, 61)
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

# ================================================================ 1. the locked door
qLib, qLocked, qKey, qNob = q(0, 'in a private library'), q(0, 'locked'), q(0, 'has the key'), q(0, 'and nobodys')
title = qNob + 0.9
for k, t in enumerate(np.arange(0.5, title, 1.0)): tick(t, k % 2 == 0, 1.0 if t < qLib else 0.55)
strings(0.5, (38, 45), title - 0.5, 40, 0.5, swell=3)
for t, m in zip(np.arange(2.0, title - 3, 4.0), [69, 65, 64, 62, 69, 65, 67, 64]): piano(t, m, 3.5, 52, 0.8); piano(t + 2, m - 12 if m > 64 else m - 7, 3.0, 42, 0.6)
for d in (-0.05, 0.28, 0.62): clack(qLocked + d + 0.1, 1.0)
clink(qKey + 0.3, 98, 1.6, 0.2); clink(qKey + 0.42, 103, 1.0, 0.25)
low.add(title - 0.05, inst(TIMP, 38, 3, 100), 1.6); strings(title, Dm, 7, 78, 1.0, swell=0.6); strings(title, (38, 45), 7, 75, 0.9, swell=0.5)
for k, m in enumerate((74, 69, 65, 62)): piano(title + 0.9 + k, m, 4, 72 - 4 * k, 1.0)

# ================================================================ 2. no central bank
prog2 = [Dm, Bb, F, C]
for k, t in enumerate(bars(V[1] + 1.5, V[2])):
    ch = prog2[k % 4]; arp(t, ch, 54, 0.85); pizz(t, ch[0] - 12, 70, 0.8); pizz(t + 2, ch[1] - 12, 60, 0.6)
thud(q(1, 'no central bank') + 0.36, 1.0, 85)
for k in range(8): clink(q(1, 'if a bank ran') + 0.3 + k * (q(1, 'nobody to call') - q(1, 'if a bank ran') - 0.3) / 8, 100 - k, 0.7, -0.3)
for k in range(25): clink(q(1, 'about a quarter') - 0.5 + 1.8 * (1 - (1 - k / 25) ** 3) * 1.0, 96 + (k % 5), 0.45, -0.4)
for k in range(5): clink(q(1, 'about a nickel') - 0.1 + k * 0.1, 98 + k, 0.7, 0.4)

# ================================================================ 3. the copper corner
qMon, q52, qTue, q60, q30, qWed, q10, qDead, qWhich = q(2, 'on monday'), q(2, 'to 52'), q(2, 'on tuesday'), q(2, 'almost 60'), q(2, 'closed at 30'), q(2, 'by wednesday'), q(2, 'it was 10'), q(2, 'the scheme was dead'), q(2, 'which banks')
prog3 = [Dm, Gm, Dm, A]
for k, t in enumerate(bars(V[2] + 1.0, q30 - 1)):
    ch = prog3[k % 4]; up = min(1, k / 4)
    arp(t, ch, 56 + int(10 * up), 0.85)
    for e in range(8): pizz(t + e * 0.5, ch[0] - 12 + (0, 0, 7, 0, 12, 0, 7, 0)[e], 62 + int(18 * up), 0.55 + 0.3 * up)
for a, b, rate in [(qMon - 0.2, q52 + 0.5, 9), (qTue, q60 + 0.4, 11), (q30 - 0.15, q30 + 0.55, 26), (qWed, q10 + 0.5, 14)]:
    for t in np.arange(a, b, 1 / rate): tick(t + rng.uniform(0, 0.02), rng.random() < 0.5, 0.45)
for k, m in enumerate((81, 77, 74, 69, 65, 62, 57, 53, 50)): piano(q30 - 0.1 + k * 0.085, m, 2, 80 - 2 * k, 0.9)
thud(q30 + 0.75, 0.8, 60); cello(q30 + 0.7, 38, 4, 80, 1.0)
piano(qDead + 0.1, 38, 5, 78, 1.2); piano(qDead + 0.1, 26, 5, 70, 1.0)
strings(qDead + 1.6, (57, 61, 64), V[3] - qDead - 1.6, 44, 0.8, prog=TREM, swell=2); strings(qDead + 1.6, (33, 45), V[3] - qDead - 1.4, 50, 0.6, swell=2)
for k in range(4): pizz(qWhich + 0.6 + k * 0.22, 57 + (0, 3, 7, 10)[k], 72, 0.8)

# ================================================================ 4. the run
qCrowd, q3h, q8, qShut, qFear, qLines, qNext2 = q(3, 'the crowd came'), q(3, 'in under three hours'), q(3, 'about 8 million'), q(3, 'it shut its doors') + 0.35, q(3, 'now the fear'), q(3, 'so the lines moved'), q(3, 'and the next')
prog4 = [Dm, Dm, Bb, Gm, A, A, Dm, Gm]
b4 = bars(V[3] + 0.6, qShut - 0.5)
for k, t in enumerate(b4):
    ch = prog4[k % 8]; up = min(1, (k + 1) / max(1, len(b4)))
    strings(t, ch, 4.3, 44 + int(26 * up), 0.55 + 0.4 * up, prog=TREM, swell=0.8)
    for e in range(8): cello(t + e * 0.5, ch[0] - 12 + (0, 0, 3, 0, 7, 0, 3, 0)[e], 0.42, 58 + int(30 * up), 0.5 + 0.4 * up)
    if k % 2 == 0: piano(t, ch[2] + 12, 3, 60 + int(14 * up), 0.8); piano(t + 1.5, ch[3] + 12, 3, 56 + int(14 * up), 0.7)
murmur(qCrowd - 0.5, V[4], 0.35, 1.0)
for t in np.arange(q3h, q8 + 0.9, 0.11): clink(t, 100 + int(rng.integers(0, 5)), 0.3, 0.5)
thud(qShut + 0.25, 2.0, 55); clack(qShut + 0.25, 1.6, 300); low.add(qShut + 0.25, inst(TIMP, 38, 3, 110), 1.6)
strings(qFear - 0.5, (38, 45, 53, 57), qLines - qFear + 0.5, 56, 0.9, swell=2)
for k, t in enumerate(np.arange(grid(qLines - 0.5), V[4] - 0.4, 0.5)):
    pizz(t, (38, 45, 41, 45, 43, 50, 45, 52)[k % 8], 64 + min(24, 2 * k), 0.8)
    if k % 8 == 0: strings(t, (Gm, A)[(k // 8) % 2], 4.2, 58, 0.7, prog=TREM, swell=0.6)

# ================================================================ 5. one private citizen
qJP, qMen, qSound, qThis, qNext, qCalled, q25, qTen, q236, qStay = q(4, 'j p morgan'), q(4, 'he had his men'), q(4, 'when they told him'), q(4, 'this is the place'), q(4, 'the next day'), q(4, 'morgan called in'), q(4, 'he needed 25'), q(4, 'in ten minutes'), q(4, 'twentythree point six'), q(4, 'the exchange stayed')
# his theme: slow, heavy, in the low strings
low.add(qJP - 0.1, inst(TIMP, 38, 3, 90), 1.2)
for k, t in enumerate(bars(V[4] + 0.8, qMen - 0.3)):
    ch = (Dm, Bb, Gm, A)[k % 4]
    cello(t, ch[0] - 12, 3.8, 82, 1.2); cello(t + 2, ch[1] - 12, 1.9, 72, 0.9)
    piano(t, ch[0] - 12, 4, 70, 1.0); piano(t, ch[0], 4, 64, 0.8); piano(t + 2, ch[2], 3, 54, 0.7); piano(t + 3, ch[3], 3, 50, 0.7)
# the night audit: the clock again, and pages
for k, t in enumerate(np.arange(grid(qMen), qSound - 0.2, 1.0)): tick(t, k % 2 == 0, 0.6)
strings(qMen, (38, 45, 53), qSound - qMen, 42, 0.6, swell=2.5)
for k, t in enumerate(bars(qMen + 0.5, qSound - 1)): piano(t, (69, 65, 67, 64)[k % 4], 3.5, 50, 0.8); piano(t + 2, (62, 58, 60, 57)[k % 4], 3, 44, 0.6)
for t in np.arange(qMen + 0.9, qSound - 0.3, 1.33 / 3): swish(t, 0.5, 0.2)
# the line: almost nothing under it
strings(qSound, (45, 57), qNext - qSound, 40, 0.5, swell=1.5)
piano(q(4, 'this is the place') + 2.8, 50, 5, 66, 1.0); piano(q(4, 'this is the place') + 2.8, 38, 5, 62, 0.9)
# the Exchange, then ten minutes
b5 = np.arange(grid(qNext), q236 + 0.2, 0.5)
for k, t in enumerate(b5):
    up = k / len(b5); bar = int((t - b5[0]) // 4); ch = (Dm, Gm, Bb, A, Dm, F, Gm, A)[bar % 8]
    pizz(t, ch[0] - 12 + (0, 7, 0, 12)[k % 4], 60 + int(34 * up), 0.6 + 0.4 * up)
    if k % 8 == 0: strings(t, ch, 4.3, 46 + int(34 * up), 0.5 + 0.5 * up, prog=TREM, swell=0.7)
    if t > qCalled and k % 2 == 0: cello(t, ch[0] - 12, 0.45, 60 + int(30 * up), 0.5 + 0.4 * up)
for k, t in enumerate(np.arange(qTen, q236 + 0.3, 0.5)): tick(t, k % 2 == 0, 0.9)
for k in range(14): clink(qTen + 0.9 + (k + 0.6) * (q236 + 0.3 - qTen - 0.9) / 14, 88 + k, 0.9, -0.3 + 0.04 * k)
swish(q(4, 'close early') - 0.1, 0.8)
# it holds: F major, the first bright chord in the film
strings(qStay - 0.1, (41, 48, 53, 57, 60), V[5] - qStay + 0.4, 74, 1.0, swell=0.4)
for k, m in enumerate((65, 69, 72, 77, 81)): piano(qStay + 0.1 + k * 0.22, m, 4, 74, 1.0)
low.add(qStay - 0.1, inst(TIMP, 41, 3, 90), 1.0)

# ================================================================ 6. back to the library
qBack, q25b, qHeld, qAbout, qSign, qRest, qUnl, qWorst = q(5, 'and that brings us back'), q(5, 'another 25 million'), q(5, 'they held out'), q(5, 'at about a quarter'), q(5, 'their leader signed'), q(5, 'then the rest'), q(5, 'morgan unlocked'), q(5, 'and the worst')
murmur(V[5], qBack + 0.5, 0.7, 0.3)
for k, t in enumerate(np.arange(grid(V[5] + 0.3), qBack, 0.5)): pizz(t, (38, 45, 41, 45)[k % 4], 62, 0.7)
strings(V[5] + 0.4, Gm, qBack - V[5], 48, 0.6, prog=TREM, swell=1)
for k, t in enumerate(np.arange(grid(qBack), qSign - 0.6, 1.0)): tick(t, k % 2 == 0, 0.6)
for t in np.arange(qHeld + 0.3, qAbout + 0.8, 0.125): tick(t, True, 0.22)                 # the hands spinning
strings(qBack, (38, 45), qSign - qBack, 44, 0.7, swell=2.5)
for t, m in zip(np.arange(grid(qBack + 1), qHeld, 4.0), [69, 65, 64, 62]): piano(t, m, 3.5, 54, 0.9); piano(t + 2, m - 12 if m > 64 else m - 7, 3, 44, 0.6)
low.add(q25b, inst(TIMP, 38, 3, 84), 1.0)
for k, t in enumerate(np.arange(grid(qHeld), qSign - 1, 2.0)): piano(t, (50, 53, 50, 52, 50, 55)[k % 6], 3, 50, 0.8); cello(t, 38, 1.9, 56, 0.7)
scratch(qSign - 0.1, 1.0, 1.2)
for k in range(4): scratch(qRest + k * 0.35, 0.5, 0.9)
strings(qSign + 0.3, Bb, qUnl - qSign, 54, 0.8, swell=1.2); piano(qSign + 0.4, 58, 4, 58, 0.9); piano(qRest + 0.2, 65, 4, 58, 0.9)
clack(qUnl + 0.1, 0.8, 900); thud(qUnl + 0.42, 0.9, 110); clack(qUnl + 0.42, 1.3, 520); creak(qUnl + 0.8, 1.3, 1.0)
# the door opens: D major
t0 = qUnl + 0.9
strings(t0, (38, 45, 50, 57, 62, 66), V[6] - t0 + 0.5, 70, 1.0, swell=1.6)
for k, m in enumerate((62, 66, 69, 74, 78, 81, 86)): harp(t0 + 0.3 + k * 0.2, m, 70, 0.9)
for k, t in enumerate(np.arange(qWorst + 0.2, V[6] - 0.5, 1.0)): piano(t, (74, 78, 81, 78, 74, 69)[k % 6], 3, 60, 0.9)

# ================================================================ 7. the turning point
qWhole, qWhat, qNot, qDied, qSame, qXmas, qCong, qCentral, qKeyb, qWhether, qSub, qAn, qBat, qCol = q(6, 'the whole financial'), q(6, 'so what happens'), q(6, 'when hes not there'), q(6, 'morgan died'), q(6, 'that same year'), q(6, 'two days before'), q(6, 'congress passed'), q(6, 'a central bank'), q(6, 'to hold the key'), q(6, 'whether its worked'), q(6, 'subscribe'), q(6, 'animal facts'), q(6, 'historys greatest'), q(6, 'worlds craziest')
for k, t in enumerate(bars(V[6] + 0.8, qWhat - 0.5)):
    ch = (Dm, Bb, Gm, A)[k % 4]; arp(t, ch, 54, 0.9); cello(t, ch[0] - 12, 3.8, 62, 0.9)
strings(qWhat, A7, qDied - qWhat - 0.6, 50, 0.8, prog=TREM, swell=1.2); cello(qWhat, 33, qDied - qWhat - 0.8, 66, 0.9)
piano(qNot + 0.2, 76, 4, 60, 0.9); piano(qNot + 0.7, 73, 4, 54, 0.8)
# 1913
mus.add(qDied + 0.2, inst(BELL, 62, 5, 78), 1.2, 0.0); piano(qDied + 0.2, 38, 6, 70, 1.1); piano(qDied + 0.2, 50, 6, 62, 0.9)
strings(qDied + 0.3, (38, 45, 53, 57), qSame - qDied + 0.5, 46, 0.8, swell=2)
piano(qDied + 2.4, 65, 4, 52, 0.9); piano(qDied + 3.4, 62, 4, 48, 0.8)
swish(qXmas - 0.15, 1.0, 0.35)
strings(qSame + 0.4, Bb, qCong - qSame, 56, 0.9, swell=1.5); piano(qSame + 0.5, 58, 4, 56, 0.9); piano(qXmas + 0.3, 62, 4, 56, 0.9)
strings(qCong, C, max(1.5, qCentral - qCong - 0.3), 62, 0.9, swell=0.8); piano(qCong + 0.1, 60, 4, 62, 0.9); piano(qCong + 0.6, 64, 4, 60, 0.9); piano(qCong + 1.1, 67, 4, 60, 0.9)
thud(qCong + 1.35, 0.8, 90)
# the building goes up: D major, and it stays
progD = [D, G, D, A, D, G, A, D]
bD = bars(qCentral - 0.5, qSub - 0.5)
for k, t in enumerate(bD):
    ch = progD[k % 8]; strings(t, ch, 4.3, 64, 0.9, swell=0.9); strings(t, (ch[0] - 12,), 4.3, 64, 0.8, swell=0.9)
    arp(t, ch, 62, 1.0, 0.5, (0, 1, 2, 3)); arp(t + 2, ch, 58, 0.9, 0.5, (1, 2, 3, 2))
clink(qKeyb + 0.2, 98, 1.6); clink(qKeyb + 0.34, 105, 1.0)
for k in range(3): pizz(qWhether + 1.2 + k * 0.3, (62, 66, 64)[k], 70, 0.8)
# the end card: the opening motif, turned major
e0 = qSub + 0.2
low.add(e0, inst(TIMP, 38, 3, 92), 1.2); strings(e0, (38, 45, 50, 57, 62, 66), DUR - e0 - 0.5, 72, 1.0, swell=0.8)
for k, (t, m) in enumerate(zip(np.arange(e0 + 0.5, DUR - 5, 1.0), [69, 66, 64, 62, 69, 66, 67, 64, 69, 74, 73, 74] * 3)): piano(t, m + 12, 3.5, 64, 0.95); piano(t, m, 3.5, 54, 0.6)
for at, m in ((qAn, 74), (qBat, 78), (qCol, 81)): harp(at, m, 76, 1.0); harp(at + 0.12, m + 7, 70, 0.8)
tend = DUR - 4.6
for k, m in enumerate((50, 57, 62, 66, 69, 74, 78)): piano(tend + k * 0.16, m, 6, 70, 1.0)
low.add(tend, inst(TIMP, 38, 4, 80), 1.0)

# ---------------------------------------------------------------- mix
IR = S.hall(4.0, 1.3, 0.03, 220, 6500)
m = mus.out(True) + low.out(True)[:, :mus.x.shape[1]]
m = m + S.reverb(mus.out(True) * 0.6 + low.out(True)[:, :mus.x.shape[1]] * 0.25, IR, 0.5)
m = m[:, :S.smp(DUR)]
m = S.eq(m, [('peak', 280, -4.0, 0.9), ('peak', 520, -2.0, 1.0), ('peak', 3000, 2.0, 0.8), ('highshelf', 5500, 4.5, 0.7)])   # the ears called the first mix muddy and dark
f = fx.out(True); f = f + S.reverb(f * 0.5, S.plate(1.6, 0.4), 0.4); f = f[:, :S.smp(DUR)]
tt_ = np.arange(m.shape[1]) / S.SR
fade = np.clip(tt_ / 0.5, 0, 1) * np.clip((DUR - tt_) / 2.5, 0, 1)
S.write('music.wav', S.master(m * fade, lufs=-20.0, fade=0, ceiling=0.8))
S.write('fx.wav', S.limiter(f * fade * 2.0, 0.7))                                  # the first pass clipped on the door slam
print('music.wav, fx.wav', round(DUR, 2), 's')
