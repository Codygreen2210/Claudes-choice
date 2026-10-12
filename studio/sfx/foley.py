"""foley: the studio's sound effects library. Every sound is built from scratch (noise, oscillators, filters) so there
is nothing to license, and every call comes out a little different so repeats don't sound like a loop.

    from studio.sfx import foley as F
    fx = F.Track(dur)                                  # a stereo bus that knows the library
    fx.hit('cannon', 12.3, db=-3, pan=-0.4)            # one-shot at a time
    fx.bed('blizzard', 0.0, 40.0, db=-6)               # a continuous bed over a span (fades in and out)
    fx.seq('volley', 20.0, 24.0, db=-8, per_s=6)       # a pattern of hits over a span
    y = fx.out()

Levels: every one-shot comes out peaking at -6 dBFS and every bed sitting at about -26 dBFS RMS, so `db` is
always relative to a sensible default and sounds can be swapped without re-balancing the film.

Adding a sound: write a function below, decorate it with @hit, @bed or @seq, then run
    python3 studio/sfx/audition.py <name>
and look at its sheet and listen notes before it goes into a film. The catalog (studio/sfx/CATALOG.md) is
rewritten by audition.py, so the list of what exists is always current.
"""
from __future__ import annotations

import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from studio.instruments import synth as S

SR = S.SR
REG: dict[str, dict] = {}
_rng = np.random.default_rng(1925)


def _register(kind):
    def deco(cat, desc, demo=None):
        def wrap(fn):
            REG[fn.__name__] = {'fn': fn, 'kind': kind, 'cat': cat, 'desc': desc, 'demo': demo or {}}
            return fn
        return wrap
    return deco
hit, bed, seq = _register('hit'), _register('bed'), _register('seq')


def x_(n): return np.arange(n) / SR
def env_ad(n, a, d): x = x_(n); return np.clip(x / max(a, 1e-4), 0, 1) * np.exp(-np.maximum(0, x - a) / d)
def edge(n, fin=1.5, fout=1.5): x = x_(n); T = n / SR; return np.clip(x / fin, 0, 1) * np.clip((T - x) / fout, 0, 1)
def j(r, v=0.08): return 1 + _rng.uniform(-v, v) * r                   # jitter a parameter by up to v
def ns(n, lo=None, hi=None, color='white'):
    y = S.noise(n, color)
    if lo and hi: return S.bp(y, lo, hi)
    if hi: return S.lp(y, hi)
    if lo: return S.hp(y, lo)
    return y
def chirp(f0, f1, n, curve=1.0): x = x_(n); T = max(n / SR, 1e-6); f = f0 + (f1 - f0) * (x / T) ** curve; return np.sin(2 * np.pi * np.cumsum(f) / SR)
def thump(f, n, dec, bend=0.8, bt=0.02): x = x_(n); return np.sin(2 * np.pi * f * x * (1 + bend * np.exp(-x / bt))) * np.exp(-x / dec)


# ================================================================ war
@hit('war', 'a cannon: hard crack, a deep body and a long rolling tail')
def cannon(r=1.0):
    n = S.smp(3.4); x = x_(n)
    y = ns(n) * np.exp(-x / 0.012) * 1.2 + thump(46 * j(r), n, 0.45, 1.0, 0.03) * 1.4 + ns(n, hi=380) * np.exp(-x / 0.9) * 1.3
    y += ns(n, 120, 900) * np.exp(-x / 1.6) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * 1.3 * x))   # the roll off the land
    return S.lp(y, 4200)

@hit('war', 'a musket or rifle shot at middle distance')
def musket(r=1.0):
    n = S.smp(1.4); x = x_(n)
    y = ns(n) * np.exp(-x / 0.02) + ns(n, hi=600) * np.exp(-x / 0.22) * 0.6 + thump(72 * j(r), n, 0.09, 1.0)
    y += ns(n, 300, 1800) * np.exp(-np.maximum(0, x - 0.08) / 0.4) * (x > 0.08) * 0.12           # the slap back off the trees
    return S.lp(y, 5200 * j(r, 0.15))

@hit('war', 'a big explosion: blast, low thud, falling debris')
def explosion(r=1.0):
    n = S.smp(4.0); x = x_(n)
    y = ns(n) * np.exp(-x / 0.05) * 1.3 + thump(38, n, 0.7, 1.2, 0.05) * 1.6 + ns(n, hi=300) * np.exp(-x / 1.4) * 1.2
    for t in np.sort(_rng.uniform(0.3, 2.6, 26)):                                                 # debris
        i = int(t * SR); m = S.smp(0.05); k = min(m, n - i)
        y[i:i + k] += ns(m, 900, 5000)[:k] * np.exp(-x_(m)[:k] / 0.01) * _rng.uniform(0.05, 0.2) * np.exp(-t / 1.5)
    return S.lp(y, 3800)

@hit('war', 'a bomb or shell hitting water: whump and spray')
def splash(r=1.0):
    n = S.smp(2.0); x = x_(n)
    return thump(60, n, 0.15, 0.6) * 0.8 + ns(n, 500, 5000) * np.clip(x / 0.04, 0, 1) * np.exp(-x / 0.45) + ns(n, 2000, 8000) * np.exp(-np.maximum(0, x - 0.4) / 0.5) * (x > 0.4) * 0.15

@hit('war', 'a falling bomb or dive: rising scream, propeller rasp underneath')
def dive(r=1.0, dur=2.4):
    n = S.smp(dur); x = x_(n); f = 170 * (1 + 2.3 * (x / dur) ** 2)
    y = S.saw(f, n) * 0.6 + S.saw(f * 2.01, n) * 0.3 + 0.2 * ns(n, 800, 3000)
    return S.lp(y, 2800) * np.clip(x / 0.3, 0, 1) * np.clip((dur - x) / 0.12, 0, 1) * (0.3 + 0.7 * x / dur)

@hit('war', 'an anti-aircraft burst high up: short pop with a puff')
def flak(r=1.0):
    n = S.smp(0.7); x = x_(n)
    return ns(n, hi=1800) * np.exp(-x / 0.05) + thump(90, n, 0.08, 0.5) * 0.6

@hit('war', 'a field snare stroke')
def snare(r=1.0):
    n = S.smp(0.25); x = x_(n)
    return ns(n, 900, 6000) * np.exp(-x / 0.05) + np.sin(2 * np.pi * 190 * j(r, 0.03) * x) * np.exp(-x / 0.04) * 0.6

@hit('war', 'a sword or bayonet clash')
def clash(r=1.0):
    n = S.smp(1.0); x = x_(n); y = np.zeros(n)
    for f, a in ((2310, 1), (3470, 0.7), (5120, 0.5), (1580, 0.6)): y += np.sin(2 * np.pi * f * j(r, 0.04) * x) * np.exp(-x / (0.18 * a + 0.05)) * a
    return y * 0.5 + ns(n, 3000, 9000) * np.exp(-x / 0.01)

@seq('war', 'a ragged musket volley along a line', demo={'per_s': 7})
def volley(t0, t1, per_s=6.0, r=1.0):
    return [('musket', t, _rng.uniform(0.45, 1.0), _rng.uniform(-0.7, 0.4)) for t in np.sort(_rng.uniform(t0, t1, max(1, int((t1 - t0) * per_s))))]

@seq('war', 'a snare march with a roll every other bar')
def march(t0, t1, step=0.5, r=1.0):
    out = []
    for k, t in enumerate(np.arange(t0, t1, step)):
        out.append(('snare', t, 1.0, -0.15))
        if k % 4 == 3: out += [('snare', t + step * 0.5, 0.6, -0.15), ('snare', t + step * 0.75, 0.6, -0.15)]
        if k % 8 == 6: out += [('snare', t + step * 0.25 + i * 0.06, 0.4, -0.15) for i in range(4)]
    return out

@seq('war', 'distant artillery: booms spread out, far and dull')
def barrage(t0, t1, per_s=0.8, r=1.0):
    return [('cannon', t, _rng.uniform(0.25, 0.6), _rng.uniform(-0.8, 0.8)) for t in np.sort(_rng.uniform(t0, t1, max(1, int((t1 - t0) * per_s))))]


# ================================================================ machines
@bed('machines', 'piston aircraft engines droning overhead')
def engines(dur, f0=92, rise=0.0, r=1.0):
    n = S.smp(dur); x = x_(n); f = f0 * (1 + rise * x / dur) * (1 + 0.006 * np.sin(2 * np.pi * 0.7 * x))
    y = S.saw(f, n) * 0.6 + S.saw(f * 1.5, n) * 0.3 + 0.3 * ns(n, 200, 1200)
    return S.autopan(S.hp(S.lp(y * (0.8 + 0.2 * np.sin(2 * np.pi * f0 / 7 * x)), 1800), 120), -0.5, 0.5)

@bed('machines', 'a steam train under way: chuffs on a beat, rail clatter')
def train(dur, rate=2.2, r=1.0):
    n = S.smp(dur); x = x_(n); y = ns(n, 60, 400) * 0.25
    for t in np.arange(0, dur, 1 / rate):
        i = int(t * SR); m = S.smp(0.18); k = min(m, n - i)
        y[i:i + k] += ns(m, 300, 2600)[:k] * np.exp(-x_(m)[:k] / 0.05) * (1 if int(t * rate) % 2 == 0 else 0.6)
    for t in np.arange(0.3, dur, 1.1):                                                            # rail joints
        for d in (0, 0.13):
            i = int((t + d) * SR); m = S.smp(0.06); k = min(m, n - i)
            if k > 0: y[i:i + k] += thump(130, m, 0.02, 0.3)[:k] * 0.3
    return y

@hit('machines', 'a steam whistle, two tones')
def whistle(r=1.0, dur=1.4):
    n = S.smp(dur); x = x_(n); v = 1 + 0.004 * np.sin(2 * np.pi * 6 * x)
    return (np.sin(2 * np.pi * 740 * v * x) + 0.8 * np.sin(2 * np.pi * 932 * v * x) + 0.3 * ns(n, 700, 2500)) * np.clip(x / 0.08, 0, 1) * np.clip((dur - x) / 0.25, 0, 1)

@hit('machines', "a ship's steam horn, low and long")
def ship_horn(r=1.0, dur=2.6):
    n = S.smp(dur); x = x_(n); f = 98 * (1 + 0.003 * np.sin(2 * np.pi * 4 * x))
    y = S.saw(f, n) * 0.7 + S.saw(f * 1.26, n) * 0.5 + 0.2 * ns(n, 200, 1500)
    return S.lp(y, 1400) * np.clip(x / 0.15, 0, 1) * np.clip((dur - x) / 0.6, 0, 1)

@hit('machines', 'a telegraph key click')
def telegraph(r=1.0):
    n = S.smp(0.08); x = x_(n)
    return ns(n, 1500, 6000) * np.exp(-x / 0.004) + np.sin(2 * np.pi * 1900 * x) * np.exp(-x / 0.01) * 0.4

@seq('machines', 'morse code tones on a wireless set')
def morse(t0, t1, wpm=0.085, r=1.0):
    out, t = [], t0
    while t < t1 - 0.2:
        d = wpm * (1 if _rng.random() < 0.6 else 3); out.append(('beep', t, 1.0, 0.3, {'dur': d})); t += d + wpm * (1 if _rng.random() < 0.75 else 3)
    return out

@hit('machines', 'a pure tone blip, for morse')
def beep(r=1.0, dur=0.1, f=720):
    n = S.smp(dur); x = x_(n); return np.sin(2 * np.pi * f * x) * np.clip(x / 0.004, 0, 1) * np.clip((dur - x) / 0.004, 0, 1)

@hit('machines', 'one typewriter key strike')
def typekey(r=1.0):
    n = S.smp(0.09); x = x_(n)
    return ns(n, 1800, 5200) * np.exp(-x / 0.006) * 0.8 + np.sin(2 * np.pi * _rng.choice([930, 1250, 1100]) * x) * np.exp(-x / 0.018) * 0.6

@seq('machines', 'typing: uneven keys with a carriage bell at the end')
def typing(t0, t1, per_s=7.0, r=1.0):
    ts = np.sort(_rng.uniform(t0, t1 - 0.4, max(1, int((t1 - t0) * per_s))))
    return [('typekey', t, _rng.uniform(0.6, 1.0), _rng.uniform(-0.3, 0.3)) for t in ts] + [('clink', t1 - 0.3, 0.7, 0.4)]

@hit('machines', 'a clock tick (alternate tick and tock with hi=False)')
def tick(r=1.0, hi=True):
    n = S.smp(0.09); x = x_(n)
    return ns(n, 1800, 5200) * np.exp(-x / 0.006) * 0.8 + np.sin(2 * np.pi * (1250 if hi else 930) * x) * np.exp(-x / 0.018) * 0.6

@seq('machines', 'a clock ticking once a second')
def clock(t0, t1, step=1.0, r=1.0):
    return [('tick', t, 1.0, -0.2, {'hi': k % 2 == 0}) for k, t in enumerate(np.arange(t0, t1, step))]


# ================================================================ money and rooms
@hit('rooms', 'a small metal ring: coin, spur, bell on a sled')
def clink(r=1.0, m=96):
    return S.bell(m + _rng.integers(-1, 2), 0.5, ratio=3.7, idx=1.4, dec=0.14)

@hit('rooms', 'a cash register: key clack, then the bell')
def ching(r=1.0):
    n = S.smp(0.8); y = np.zeros(n); y[:S.smp(0.16)] += clack()[:S.smp(0.16)] * 0.5
    for d, m, g in ((0.07, 100, 1.0), (0.15, 103, 0.8)): b = S.bell(m, 0.5, ratio=3.7, idx=1.4, dec=0.14); i = S.smp(d); y[i:i + len(b)] += b[:n - i] * g
    return y

@seq('rooms', 'coins spilling or being counted')
def coins(t0, t1, n=12, r=1.0):
    return [('clink', t, _rng.uniform(0.5, 1.0), _rng.uniform(-0.5, 0.5), {'m': int(_rng.choice([93, 96, 98, 100, 103]))}) for t in np.sort(_rng.uniform(t0, t1, n))]

@hit('rooms', 'a wooden knock or latch: dry, short')
def clack(r=1.0, f=420):
    n = S.smp(0.16); x = x_(n); return ns(n, 900, 4200) * np.exp(-x / 0.012) + np.sin(2 * np.pi * f * j(r) * x) * np.exp(-x / 0.03) * 0.7

@hit('rooms', 'a dull thud: a body, a sack, a heavy book on a table')
def thud(r=1.0, f=70):
    n = S.smp(0.5); x = x_(n); return thump(f * j(r), n, 0.12) + ns(n, hi=900) * np.exp(-x / 0.03) * 0.5

@hit('rooms', "a judge's gavel: two hard knocks")
def gavel(r=1.0):
    n = S.smp(0.8); y = np.zeros(n)
    for d in (0.0, 0.32): i = S.smp(d); k = clack(f=260) * 1.2 + np.pad(thud(f=110), (0, 0))[:S.smp(0.16)] * 0.4; y[i:i + len(k)] += k[:n - i]
    return y

@hit('rooms', 'a heavy door slamming shut in a stone room')
def door_slam(r=1.0):
    n = S.smp(1.8); x = x_(n)
    y = thump(64, n, 0.14, 0.6) * 1.2 + ns(n, 200, 2500) * np.exp(-x / 0.03) + ns(n, 300, 3000) * np.exp(-x / 0.6) * 0.08
    return y + S.reverb(y, S.hall(1.4, 0.6, 0.02, 200, 4000), 0.35)

@hit('rooms', 'a jail cell door: iron clank and rattle')
def cell_door(r=1.0):
    n = S.smp(1.6); x = x_(n); y = np.zeros(n)
    for f, a, d in ((410, 1, 0.25), (655, 0.8, 0.2), (1130, 0.6, 0.12), (1720, 0.4, 0.08)): y += np.sin(2 * np.pi * f * j(r, 0.03) * x) * np.exp(-x / d) * a
    y += ns(n, 800, 5000) * np.exp(-x / 0.02) + thump(80, n, 0.1, 0.5) * 0.8
    for t in (0.18, 0.27, 0.33): i = S.smp(t); m = S.smp(0.05); y[i:i + m] += ns(m, 1500, 6000) * np.exp(-x_(m) / 0.008) * 0.3
    return y + S.reverb(y, S.hall(1.2, 0.5, 0.02, 250, 5000), 0.3)

@hit('rooms', 'a page turn or newspaper snap')
def page(r=1.0):
    n = S.smp(0.45); x = x_(n); am = np.clip(np.sin(np.pi * x / 0.45), 0, 1) ** 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * x))
    return ns(n, 1500, 9000) * am * 0.6 + ns(n, 2000, 7000) * np.exp(-np.maximum(0, x - 0.3) / 0.01) * (x > 0.3) * 0.8

@hit('rooms', 'a pen scratching a line')
def scratch(r=1.0, dur=0.9):
    n = S.smp(dur); x = x_(n); am = 0.5 + 0.5 * np.sin(2 * np.pi * (9 + 3 * np.sin(x * 5)) * x)
    return ns(n, 2200, 6500) * am * np.clip(x / 0.03, 0, 1) * np.clip((dur - x) / 0.05, 0, 1)

@hit('rooms', 'a wooden creak: floorboard, mast, rope under load')
def creak(r=1.0, dur=1.2):
    n = S.smp(dur); x = x_(n); f = 170 + 120 * x / dur + 12 * np.sin(2 * np.pi * 7 * x)
    return S.bp(S.saw(f, n) * (np.sin(2 * np.pi * 23 * x) > -0.3), 300, 1800) * np.sin(np.pi * x / dur) ** 0.7

@hit('rooms', 'a church or town bell toll')
def toll(r=1.0, m=50):
    a = S.bell(m, 6.0, ratio=2.76, idx=2.6, dec=2.2) * 0.7; b = S.bell(m + 12, 4.0, ratio=3.1, idx=1.5, dec=1.2) * 0.3
    a[:len(b)] += b; return a

@hit('rooms', 'a heartbeat: lub-dub')
def heartbeat(r=1.0):
    n = S.smp(0.6); x = x_(n)
    beat = lambda m, f: S.lp(thump(f, m, 0.09, 0.4) + 0.35 * np.sin(2 * np.pi * 2 * f * x_(m)) * np.exp(-x_(m) / 0.05), 300) + ns(m, 300, 1400) * np.exp(-x_(m) / 0.012) * 0.25   # the tap lets a phone speaker hear it
    y = beat(n, 52); i = S.smp(0.22); y[i:] += beat(n - i, 48) * 0.7; return y

@seq('rooms', 'a heartbeat that speeds up', demo={'gap0': 1.0, 'gap1': 0.55})
def heart(t0, t1, gap0=1.0, gap1=1.0, r=1.0):
    out, t = [], t0
    while t < t1: p = (t - t0) / max(1e-6, t1 - t0); out.append(('heartbeat', t, 0.7 + 0.3 * p, 0.0)); t += gap0 + (gap1 - gap0) * p
    return out


# ================================================================ crowds
def _voices(n, k=24, lo=180, hi=1100):
    x = x_(n); y = np.zeros(n)
    for _ in range(k):                                                                          # each voice: a formant band that comes and goes
        f = _rng.uniform(lo, hi); w = f * 0.35; on = (np.sin(2 * np.pi * _rng.uniform(0.15, 0.6) * x + _rng.uniform(0, 6)) > 0.2).astype(float)
        y += S.bp(S.noise(n), f - w / 2, f + w / 2) * S.lp(on, 6) * _rng.uniform(0.4, 1)
    return y

@bed('crowds', 'a crowd talking: a street, a room, a line of people')
def murmur(dur, r=1.0):
    n = S.smp(dur); return S.autopan(_voices(n) + ns(n, 90, 300) * 0.4, -0.4, 0.4)

@bed('crowds', 'a crowd cheering: rising roar with whistles')
def cheer(dur, r=1.0):
    n = S.smp(dur); x = x_(n); y = _voices(n, 40, 300, 2200) * 1.4 + ns(n, 400, 3000) * 0.6
    for t in _rng.uniform(0.3, max(0.4, dur - 1), int(dur * 1.2)): i = S.smp(t); m = S.smp(0.6); k = min(m, n - i); y[i:i + k] += chirp(2200, 2900, m, 0.5)[:k] * np.sin(np.pi * x_(m)[:k] / 0.6) * 0.12
    return S.autopan(y * (0.7 + 0.3 * np.clip(x / 1.5, 0, 1)), -0.6, 0.6)

@bed('crowds', 'panic: a crowd shouting, raised and ragged')
def panic(dur, r=1.0):
    n = S.smp(dur); x = x_(n); y = _voices(n, 36, 350, 1800) * (0.7 + 0.3 * np.abs(np.sin(2 * np.pi * 0.9 * x)))
    return S.autopan(S.saturate(y * 1.3, 1.4) + ns(n, 100, 400) * 0.3, -0.6, 0.6)


# ================================================================ nature
@bed('nature', 'open wind across flat ground')
def wind(dur, r=1.0):
    n = S.smp(dur); x = x_(n)
    w = ns(n, 140, 700) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.06 * x + 1) * np.sin(2 * np.pi * 0.11 * x))
    return S.autopan(w, -0.4, 0.4)

@bed('nature', 'a blizzard: gusting wind with a hiss of snow and a high whistle in the gusts')
def blizzard(dur, r=1.0):
    n = S.smp(dur); x = x_(n); gust = 0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * x + 1) * np.sin(2 * np.pi * 0.17 * x + 2)
    w = ns(n, 160, 900) * (0.4 + 0.6 * gust) + 0.35 * ns(n, 2500, 9000) * gust ** 2
    w += 0.06 * S.bp_sweep(S.noise(n), 900 + 700 * gust, 6) if hasattr(S, 'bp_sweep') else 0
    return S.autopan(w, -0.6, 0.6)

@bed('nature', 'sea swell: slow waves, foam on the crests')
def waves(dur, r=1.0):
    n = S.smp(dur); x = x_(n)
    w = ns(n, 120, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * x + 1)) ** 2 + 0.35 * ns(n, 900, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * x + 2.2)) ** 6
    return S.autopan(w, -0.4, 0.4)

@bed('nature', 'steady rain on a roof or field')
def rain(dur, r=1.0):
    n = S.smp(dur); y = ns(n, 1500, 9000, 'pink') * 0.5 + ns(n, 200, 900) * 0.2
    for t in _rng.uniform(0, dur, int(dur * 40)): i = S.smp(t); m = S.smp(0.01); k = min(m, n - i); y[i:i + k] += ns(m, 3000, 9000)[:k] * _rng.uniform(0.1, 0.4)
    return S.autopan(y, -0.5, 0.5)

@hit('nature', 'thunder: a crack and a long roll')
def thunder(r=1.0):
    n = S.smp(5.0); x = x_(n); roll = 0.6 + 0.4 * np.sin(2 * np.pi * 2.1 * x) * np.sin(2 * np.pi * 0.7 * x)
    return ns(n, hi=2500) * np.exp(-x / 0.05) * 0.8 + ns(n, hi=200) * roll * np.clip(x / 0.2, 0, 1) * np.exp(-x / 1.6) * 2.0

@bed('nature', 'a fire burning: low roar with pops')
def fire(dur, r=1.0):
    n = S.smp(dur); y = ns(n, hi=500, color='brown') * 3 + ns(n, 400, 2000) * 0.1
    for t in _rng.uniform(0, dur, int(dur * 6)): i = S.smp(t); m = S.smp(0.03); k = min(m, n - i); y[i:i + k] += ns(m, 2500, 9000)[:k] * np.exp(-x_(m)[:k] / 0.004) * _rng.uniform(0.3, 1)
    return S.autopan(y, -0.3, 0.3)

@bed('nature', 'night insects and a little wind')
def crickets(dur, r=1.0):
    n = S.smp(dur); x = x_(n); y = np.zeros(n)
    for f, rate, ph in ((4300, 3.1, 0.0), (4750, 2.3, 1.7), (5200, 3.7, 0.6)):
        y += np.sin(2 * np.pi * f * x) * (np.sin(2 * np.pi * 38 * x) > 0.2) * np.clip(np.sin(2 * np.pi * rate / 4 * x + ph), 0, 1) ** 3
    return S.autopan(y * 0.6 + ns(n, 90, 420) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * x)), -0.6, 0.6)

@hit('nature', 'ice cracking: a sharp report and a groan under it')
def ice_crack(r=1.0):
    n = S.smp(2.0); x = x_(n)
    y = ns(n) * np.exp(-x / 0.025) + thump(80, n, 0.25, 1.0, 0.05) + S.lp(S.noise(n), 600) * np.exp(-x / 0.4) * 0.8
    y += chirp(900, 300, n, 0.5) * np.exp(-x / 0.3) * 0.15                                       # the zing along the ice sheet
    return S.lp(y, 4200)


# ================================================================ animals
@hit('animals', 'a big cat growl')
def growl(r=1.0, dur=1.4):
    n = S.smp(dur); x = x_(n); f = 58 - 12 * x / dur + 3 * np.sin(2 * np.pi * 5 * x)
    y = S.saw(f, n) * (0.55 + 0.45 * np.sin(2 * np.pi * 24 * x)) + 0.4 * ns(n, 150, 700)
    return S.saturate((S.bp(y, 70, 900) + 0.5 * S.bp(y, 300, 620)) * np.sin(np.pi * x / dur) ** 0.7, 1.6)

@hit('animals', 'a lion roar: rising, open, then the grunts')
def roar(r=1.0):
    n = S.smp(3.2); x = x_(n); body = np.clip(x / 0.3, 0, 1) * np.exp(-np.maximum(0, x - 0.9) / 0.5)
    f = 95 + 40 * np.sin(np.pi * np.clip(x / 1.6, 0, 1)) + 4 * np.sin(2 * np.pi * 6 * x)
    y = S.saw(f, n) * (0.6 + 0.4 * np.sin(2 * np.pi * 31 * x)) + 0.5 * ns(n, 200, 1400)
    y = (S.bp(y, 120, 600) + 0.6 * S.bp(y, 650, 1100) + 0.3 * S.bp(y, 1600, 2400)) * body
    for t in (2.0, 2.45, 2.85):                                                                   # the grunts after
        i = S.smp(t); m = S.smp(0.25); g = growl(dur=0.25) * 0.5; y[i:i + m] += g[:min(m, n - i)]
    return S.saturate(y, 1.4)

@hit('animals', 'a sled dog or wolf howl')
def howl(r=1.0, dur=2.6):
    n = S.smp(dur); x = x_(n); f = 520 + 160 * np.sin(np.pi * np.clip(x / dur, 0, 1)) ** 0.8 - 120 * (x / dur) ** 3
    f = f * j(r, 0.1) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * x))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR) + 0.08 * ns(n, 400, 2000)
    return y * np.clip(x / 0.25, 0, 1) * np.clip((dur - x) / 0.6, 0, 1)

@hit('animals', 'a dog bark')
def bark(r=1.0):
    n = S.smp(0.35); x = x_(n); f = 420 * j(r, 0.15) * (1 + 0.6 * np.exp(-x / 0.04))
    y = S.saw(f, n) * 0.5 + ns(n, 400, 2500) * 0.6
    return (S.bp(y, 350, 1300) + 0.6 * S.bp(y, 1600, 3000)) * env_ad(n, 0.008, 0.08)

@seq('animals', 'a dog team running on packed snow: paws, harness bells', demo={'rate': 5.0})
def paws(t0, t1, rate=5.0, r=1.0):
    out = [('pawstep', t + _rng.uniform(0, 0.02), _rng.uniform(0.6, 1.0), _rng.uniform(-0.4, 0.4)) for t in np.arange(t0, t1, 1 / rate)]
    return out + [('clink', t, 0.5, 0.3, {'m': 101 + (0, 3, 0, 5)[k % 4]}) for k, t in enumerate(np.arange(t0, t1, 0.5))]

@hit('animals', 'one paw on packed snow')
def pawstep(r=1.0):
    n = S.smp(0.08); x = x_(n); return ns(n, 500, 2400) * np.exp(-x / 0.015)

@seq('animals', 'a horse at a canter: three-beat hooves on dirt', demo={'rate': 1.6})
def hooves(t0, t1, rate=1.6, r=1.0):
    return [('hoof', t + d, a, 0.0) for t in np.arange(t0, t1, 1 / rate) for d, a in ((0, 1.0), (0.09, 0.8), (0.17, 0.9))]

@hit('animals', 'one hoof on dirt')
def hoof(r=1.0):
    n = S.smp(0.2); x = x_(n); return thump(120 * j(r, 0.15), n, 0.04, 0.4) + ns(n, 200, 1500) * np.exp(-x / 0.02) * 0.5


# ================================================================ people
@hit('people', 'one footstep: surface = snow, wood, dirt or stone', demo={'surface': 'wood'})
def step(r=1.0, surface='dirt'):
    n = S.smp(0.3); x = x_(n)
    if surface == 'snow':  y = ns(n, 600, 5000) * np.clip(x / 0.02, 0, 1) * np.exp(-x / 0.08) * (0.6 + 0.4 * (np.sin(2 * np.pi * 140 * x) > 0))
    elif surface == 'wood': y = thump(150 * j(r), n, 0.05, 0.3) + ns(n, 300, 3000) * np.exp(-x / 0.015) * 0.6
    elif surface == 'stone': y = ns(n, 1200, 7000) * np.exp(-x / 0.01) + thump(200, n, 0.03, 0.2) * 0.5
    else: y = ns(n, 150, 1800) * np.exp(-x / 0.04) + thump(90, n, 0.04, 0.3) * 0.6
    return y

@seq('people', 'someone walking: surface = snow, wood, dirt or stone', demo={'surface': 'snow'})
def walk(t0, t1, pace=0.55, surface='dirt', r=1.0):
    return [('step', t + _rng.uniform(-0.02, 0.02), 0.7 + 0.3 * (k % 2), -0.1 + 0.2 * (k % 2), {'surface': surface}) for k, t in enumerate(np.arange(t0, t1, pace))]

@seq('people', 'a column of soldiers marching in step', demo={'pace': 0.5})
def column(t0, t1, pace=0.5, r=1.0):
    return [('step', t + _rng.uniform(-0.03, 0.03), _rng.uniform(0.3, 0.6), _rng.uniform(-0.7, 0.7), {'surface': 'dirt'}) for t in np.arange(t0, t1, pace) for _ in range(6)]

@hit('people', 'a punch or body blow')
def punch(r=1.0):
    n = S.smp(0.35); x = x_(n); return thump(85, n, 0.06, 0.8) + ns(n, 300, 2000) * np.exp(-x / 0.015) * 0.8


# ================================================================ transitions
@hit('transitions', 'an air swish for a cut or a thrown object')
def swish(r=1.0, dur=0.3):
    return S.whoosh(dur, 900, 3800, 0.9)

@hit('transitions', 'a deep boom to land a title or a turn in the story')
def boom(r=1.0):
    n = S.smp(2.8); x = x_(n)
    y = thump(50, n, 0.4, 0.9, 0.03) + ns(n) * np.exp(-x / 0.06) * 0.8 + ns(n, hi=500) * np.exp(-x / 0.8) * 0.8
    return S.lp(y, 3600)

@hit('transitions', 'a rising swell into a hit')
def riser(r=1.0, dur=2.0):
    return S.riser(dur, 300, 7000)


# ================================================================ phone speakers
# Most viewers listen on a phone, which plays almost nothing under 300 Hz. A boom that is all low end vanishes there.
# For the low sounds, add the harmonics of the low end (what a small speaker can play), so the ear still hears
# the weight. The audition flags anything with under 8% of its energy between 300 Hz and 5 kHz.
def audible(y, amt=0.5):
    low = S.lp(y, 260)
    h = S.bp(S.saturate(low / max(np.abs(low).max(), 1e-9) * 3.0, 3.0), 280, 2600)
    return y + h * amt * max(np.abs(y).max(), 1e-9) / max(np.abs(h).max(), 1e-9)

for _nm, _amt in (('cannon', 0.85), ('explosion', 1.0), ('thud', 1.1), ('door_slam', 0.5), ('toll', 0.55), ('heartbeat', 1.3),
                  ('fire', 0.7), ('hoof', 0.6), ('step', 0.5), ('punch', 0.6), ('boom', 0.45)):
    _f = REG[_nm]['fn']
    def _wrapped(*a, _f=_f, _amt=_amt, **k): return audible(np.asarray(_f(*a, **k), float), _amt)
    REG[_nm]['fn'] = _wrapped


# ================================================================ the track
class Track:
    """A stereo bus that places library sounds by name. Levels are relative: db=0 is the library's default."""
    HIT_PEAK, BED_RMS = 0.5, 0.05

    def __init__(self, dur, tail=4.0, seed=1):
        global _rng
        _rng = np.random.default_rng(seed); S.seed(seed)
        self.bus = S.Bus(dur, tail); self.dur = dur; self.used = {}

    @staticmethod
    def make(name, **kw):
        e = REG[name]; y = np.asarray(e['fn'](**kw), float)
        if e['kind'] == 'hit':
            m = np.max(np.abs(y)); y = y * (Track.HIT_PEAK / m) if m > 0 else y
        return y

    def hit(self, name, t, db=0.0, pan=0.0, **kw):
        self.used[name] = self.used.get(name, 0) + 1
        self.bus.add(t, self.make(name, **kw), S.db(db), pan); return self

    def bed(self, name, t0, t1, db=0.0, fin=1.5, fout=1.5, **kw):
        self.used[name] = self.used.get(name, 0) + 1
        y = np.asarray(REG[name]['fn'](t1 - t0, **kw), float)
        rms = np.sqrt(np.mean(y ** 2)); y = y * (self.BED_RMS / rms) if rms > 0 else y
        y = y * edge(y.shape[-1], fin, fout)
        self.bus.add(t0, y, S.db(db)); return self

    def seq(self, name, t0, t1, db=0.0, **kw):
        self.used[name] = self.used.get(name, 0) + 1
        for ev in REG[name]['fn'](t0, t1, **kw):
            nm, t, g, pan = ev[:4]; extra = ev[4] if len(ev) > 4 else {}
            self.bus.add(t, self.make(nm, **extra), S.db(db) * g, pan)
        return self

    def out(self, tail=False): return self.bus.out(tail)


def render(name, dur=None, **kw):
    """One sound on its own, for auditions: hits as they are, beds for `dur` seconds, sequences over `dur`."""
    e = REG[name]; kw = {**e['demo'], **kw}
    if e['kind'] == 'hit': return S.stereo(Track.make(name, **kw), 0.0)
    d = dur or (12.0 if e['kind'] == 'bed' else 6.0)
    t = Track(d + 0.5, 2.0)
    (t.bed(name, 0.0, d, **kw) if e['kind'] == 'bed' else t.seq(name, 0.2, d, **kw))
    return t.out(True)[:, :S.smp(d + 2.0)]
