#!/usr/bin/env python3
"""Heron: the sound. A bayou at dusk: crickets, frogs, lapping water; the strike's splash, the fish, the heron's croak
as it lifts off, and a soft whoosh on every downstroke of its wings, drifting left and away.
Wingbeat times come from the same formula the picture uses, so the sound lands on the frames."""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from studio.instruments import synth as S  # noqa: E402

S.seed(5)
DUR = 13.0
rng = np.random.default_rng(12)
air, life, fx = S.Bus(DUR), S.Bus(DUR), S.Bus(DUR)


def prog(t, a, b, ease='l'):
    p = np.clip((t - a) / (b - a), 0, 1)
    if ease == 'io':
        return np.where(p < .5, 4 * p ** 3, 1 - (-2 * p + 2) ** 3 / 2)
    if ease == 'sine':
        return -(np.cos(np.pi * p) - 1) / 2
    return p


# ---------------------------------------------------------------- the bayou
n = S.smp(DUR)
tt = np.arange(n) / S.SR
water = S.lp(S.noise(n, 'pink'), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * tt) ** 2)
air.add(0, S.autopan(water * 0.5, -0.3, 0.3), 0.18)
lap = S.bp(S.noise(n), 300, 1400) * (np.sin(2 * np.pi * 0.61 * tt + 1) > 0.93) * 0.8
air.add(0, S.lp(lap, 1200), 0.05, 0.2)
# crickets: chirps of 3 to 5 pulses near 4.4-4.9 kHz, a loose chorus of individuals
for c in range(9):
    f0 = 4300 + 600 * rng.random(); pan = rng.uniform(-0.9, 0.9); rate = 0.9 + 0.8 * rng.random(); t = rng.random()
    while t < DUR:
        k = rng.integers(3, 6)
        for i in range(k):
            m = S.smp(0.018); tq = np.arange(m) / S.SR
            life.add(t + i * 0.034, np.sin(2 * np.pi * f0 * tq) * np.sin(np.pi * tq / tq[-1]) ** 2, 0.022, pan)
        t += 1 / rate + 0.2 * rng.random()
# frogs: a couple of low croaks now and then
for t0, f, pan in ((1.2, 190, -0.6), (4.1, 160, 0.7), (5.9, 205, -0.4), (9.8, 175, 0.5), (11.6, 190, -0.7)):
    for k in range(3):
        m = S.smp(0.09); tq = np.arange(m) / S.SR
        pulses = (np.sin(2 * np.pi * 38 * tq) > 0.2).astype(float)
        cro = S.bp(S.saw(f, m) * pulses, 250, 1200) * np.sin(np.pi * tq / tq[-1])
        life.add(t0 + k * 0.13, cro, 0.10, pan)
# a far fish rise at 1.9 s (the ripple the heron is watching)
m = S.smp(0.25); tq = np.arange(m) / S.SR
fx.add(1.9, S.bp(S.noise(m), 600, 3500) * np.exp(-tq / 0.05), 0.06, -0.1)

# ---------------------------------------------------------------- the strike (3.36 s)
m = S.smp(0.6); tq = np.arange(m) / S.SR
splash = S.bp(S.noise(m), 500, 6000) * np.exp(-tq / 0.09) + S.lp(S.noise(m), 400) * np.exp(-tq / 0.05) * 0.6
fx.add(3.34, splash, 0.34, 0.25)
for i in range(14):                                     # droplets falling back
    t = 3.42 + 0.35 * rng.random(); f = 1400 + 2200 * rng.random()
    mm = S.smp(0.03); q = np.arange(mm) / S.SR
    fx.add(t, np.sin(2 * np.pi * f * q * (1 + 2 * q)) * np.exp(-q / 0.008), 0.05, 0.1 + 0.3 * rng.random())
fx.add(3.2, S.whoosh(0.18, 600, 2500), 0.05, 0.2)       # the air of the thrust
# the fish, flapping in the beak (3.4 to 4.8 s)
t = 3.45
while t < 4.8:
    mm = S.smp(0.02); q = np.arange(mm) / S.SR
    fx.add(t, S.bp(S.noise(mm), 1500, 5000) * np.exp(-q / 0.004), 0.05, 0.2)
    t += 0.06 + 0.05 * rng.random()
# the swallow (4.6 s): a soft low gulp
mm = S.smp(0.2); q = np.arange(mm) / S.SR
fx.add(4.62, np.sin(2 * np.pi * (140 - 200 * q) * q) * np.sin(np.pi * q / q[-1]), 0.08, 0.2)

# ---------------------------------------------------------------- takeoff and flight
m = S.smp(0.5); tq = np.arange(m) / S.SR
fx.add(6.68, S.bp(S.noise(m), 250, 3000) * np.exp(-tq / 0.12), 0.22, 0.25)     # feet leaving the water
# the croak: herons give a harsh "frahnk" when they lift off
m = S.smp(0.42); tq = np.arange(m) / S.SR
f = 330 - 60 * tq / tq[-1]
voice = S.saw(f, m) + 0.5 * S.square(f * 1.01, m)
voice = S.bp(voice, 500, 2600) + 0.6 * S.bp(voice, 900, 1300)
voice *= np.sin(np.pi * tq / tq[-1]) ** 0.6 * (1 + 0.5 * (np.sin(2 * np.pi * 42 * tq) > 0))
fx.add(6.95, S.saturate(voice, 2.0), 0.12, 0.2)

# wingbeats: a downstroke whoosh each time the arm passes the top going down (the same formula as the picture)
t = np.arange(6.7, 12.6, 1 / 600)
ft = t - 6.7
hz = 2.4 * (1 - 0.3 * prog(t, 8, 11, 'io'))
amp = 1 - 0.55 * prog(t, 10.6, 12.2, 'io')
phase = 2 * np.pi * np.cumsum(hz) / 600                     # accumulated phase, same as flapPhase() in the page
flap = np.sin(phase) * amp
tops = [t[i] for i in range(1, len(t) - 1) if flap[i] > flap[i - 1] and flap[i] >= flap[i + 1] and flap[i] > 0.2]
q_arc = prog(np.array(tops), 6.7, 12.4, 'sine')
for tk, q in zip(tops, q_arc):
    dist = 1 - 0.75 * q                                          # further away as it climbs
    pan = 0.25 - 1.1 * q                                         # it flies off to the left
    w = S.whoosh(0.32, 180, 900, 0.8) * 0.8
    hi = S.whoosh(0.22, 700, 2500, 1.2) * 0.25
    w[:len(hi)] += hi
    fx.add(tk + 0.02, S.lp(w, 4000 - 2500 * q), 0.22 * dist, pan)

# ---------------------------------------------------------------- mix
IR = S.hall(3.5, 1.0, 0.03, 250, 6000)
mix = air.out() + life.out() + fx.out()
mix = mix + S.reverb(fx.out() * 0.4 + life.out() * 0.3, IR, 0.5)
fade = np.minimum(1, tt / 1.0) * np.clip((DUR - tt) / 1.2, 0, 1)
mix = mix * fade
master = S.master(mix, lufs=-20.0, fade=0)

if __name__ == '__main__':
    S.write(str(HERE / 'sound.wav'), master)
    print(f'{len(tops)} wingbeats; wrote sound.wav')
