#!/usr/bin/env python3
"""Painted Face: the score.

A bright, music-box-ish bed for a 75-second explainer. It sits under a narrator,
so the arrangement keeps 300 Hz - 3 kHz thin on purpose and carries its interest
in the sparkle above 3 kHz and in a soft low end.

Three things here are lessons from the Kill Screen build, not taste:
  - synth.reverb and synth.pingpong return ONLY their wet signal, so both are
    used as sends (dry + wet), never as `x = fx(x)`.
  - synth.kick is ~48% sub, so the kit is split into a low bus and a top bus and
    they get their own faders.
  - a part's high-pass must sit below its own lowest note, or the filter takes
    the fundamentals out and buries it.

    python3 score.py   ->  score.wav, beats.json

Then: python3 ../../studio/senses/listen.py score.wav --out notes/
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'studio', 'instruments'))

import synth as S          # noqa: E402
import theory as T         # noqa: E402

BPM = 112
BEAT = 60.0 / BPM          # 0.53571 s
BAR = 4 * BEAT             # 2.14286 s
BARS = 37                  # 79.3 s, enough for a 75.1 s read plus a tail
DUR = BARS * BAR

PROG = ['C', 'Am', 'F', 'G']          # I - vi - IV - V, bright and plain
N = S.smp(DUR)


def at(buf, t, x, gain=1.0):
    a = S.smp(t)
    if a >= buf.shape[-1]:
        return
    b = min(buf.shape[-1], a + x.shape[-1])
    buf[..., a:b] += x[..., :b - a] * gain


def bar_chord(bar):
    return PROG[bar % len(PROG)]


# --------------------------------------------------------------------------- parts
def music_box():
    """Plucked ostinato in the top octaves — the bright thing the ear follows.

    It plays from C6 up, so the high-pass that keeps it clear of the voice sits
    at 700 Hz, well under its own lowest note (C6 is 1047 Hz).
    """
    out = np.zeros(N)
    step = BEAT / 2
    for bar in range(BARS):
        notes = T.chord(bar_chord(bar), octave=6)
        order = [0, 2, 1, 2, 0, 1, 2, 1]
        for i in range(8):
            if bar < 2 and i % 4 != 0:
                continue
            if bar >= BARS - 3 and i % 4 != 0:
                continue
            m = notes[order[i] % len(notes)] - (12 if i in (2, 6) else 0)
            t = bar * BAR + i * step
            at(out, t, S.pluck(m, dur=step * 1.9, bright=8500, dark=1400), 0.40)
    return S.hp(out, 700, 2)


def sparkle():
    """A bell on the first beat of each bar, and a little flourish every fourth."""
    out = np.zeros(N)
    for bar in range(2, BARS - 2):
        notes = T.chord(bar_chord(bar), octave=6)
        at(out, bar * BAR, S.bell(notes[0] + 12, dur=1.6, ratio=3.2, idx=1.6, dec=0.45), 0.16)
        if bar % 4 == 3:
            for j, n in enumerate(notes):
                at(out, bar * BAR + (2 + j * 0.5) * BEAT,
                   S.bell(n + 12, dur=1.1, ratio=3.5, idx=1.3, dec=0.35), 0.10)
    return S.hp(out, 900, 2)


def pad():
    """soft_pad returns stereo already: its two sides are detuned against each
    other, so it needs a stereo buffer. The detune is also why it gets narrowed
    at the mix — opposed drift is exactly what cancels on a mono phone speaker."""
    out = np.zeros((2, N))
    for bar in range(1, BARS - 1):
        notes = T.chord(bar_chord(bar), octave=4)
        at(out, bar * BAR, S.soft_pad(notes, BAR * 0.98, a=0.35, r=0.5, bright=1500), 0.085)
    return S.lp(out, 2200, 2)


def bassline():
    out = np.zeros(N)
    for bar in range(BARS):
        if bar < 1 or bar >= BARS - 2:
            continue
        root = T.bass_of(bar_chord(bar), octave=2)
        for h in (0, 1.5, 2, 3.5):
            at(out, bar * BAR + h * BEAT,
               S.bass_note(root, BEAT * 0.75, bright=1200, sub=0.18), 0.5)
    return S.lp(out, 2000, 2)


def drums():
    """(low, top) on separate buses — the kick is almost all sub."""
    low = np.zeros(N)
    top = np.zeros(N)
    k = S.kit('synth')
    for bar in range(BARS):
        if bar < 2 or bar >= BARS - 3:
            continue
        b0 = bar * BAR
        at(low, b0 + 0 * BEAT, k['kick'], 0.80)
        at(low, b0 + 2 * BEAT, k['kick'], 0.55)
        at(top, b0 + 1 * BEAT, k['snare'], 0.22)
        at(top, b0 + 3 * BEAT, k['snare'], 0.22)
        for i in range(8):
            at(top, b0 + i * BEAT / 2, k['hat'], 0.11 if i % 2 else 0.16)
    return low, top


def arc(n):
    """A shape across the film, so it isn't flat from end to end."""
    pts_t = [0.0, 2 * BAR, 6 * BAR, 16 * BAR, 18 * BAR, 26 * BAR, 32 * BAR, 34 * BAR, BARS * BAR]
    pts_db = [-12.0, -7.0, -2.0, 0.0, -4.5, 0.0, 0.5, -4.0, -14.0]
    t = np.arange(n) / S.SR
    return 10 ** (np.interp(t, pts_t, pts_db) / 20.0)


# --------------------------------------------------------------------------- mix
def build():
    S.seed(1933)

    m = music_box()
    sp = sparkle()
    pd = pad()
    b = bassline()
    d_low, d_top = drums()

    M_dry = S.stereo(m, 0.0)
    M = M_dry + 0.20 * S.pingpong(M_dry, d=BEAT / 2, fb=0.14, taps=3, lo=800, hi=7000)
    SPr = S.stereo(sp, 0.0)
    SP = SPr + 0.30 * S.pingpong(SPr, d=BEAT * 0.75, fb=0.18, taps=3, lo=1200, hi=9000)

    PD = 0.65 * pd + 0.35 * S.stereo(pd.mean(axis=0), 0.0)   # narrowed, see pad()
    mix = (M * 1.0 + SP * 1.15 + PD * 0.7
           + S.stereo(b, 0.0) * 0.38 + S.stereo(d_low, 0.0) * 0.20
           + S.stereo(d_top, 0.0) * 0.85)
    mix = mix * arc(mix.shape[-1])

    # send, not insert
    mix = mix + S.reverb(mix, S.plate(2.2, 0.5, 0.02, 500, 7000), wet=0.14)
    mix = S.glue(mix, thr=-18, ratio=1.8, rel=0.25)

    mix = S.eq(mix, [
        ('peak', 400, -3.0, 0.9),       # the voice's body
        ('peak', 2000, -2.0, 1.0),      # her consonants
        ('highshelf', 8000, 3.0, 0.7),  # keep the music box bright
    ])

    mix = S.master(mix, lufs=-18.0, fade=1.5, ceiling=0.72)
    return mix


if __name__ == '__main__':
    mix = build()
    S.write(os.path.join(HERE, 'score.wav'), mix)
    with open(os.path.join(HERE, 'beats.json'), 'w') as f:
        json.dump({'bpm': BPM, 'beat': BEAT, 'bar': BAR, 'bars': BARS,
                   'duration': DUR, 'progression': PROG}, f, indent=2)
    print(f'score.wav  {DUR:.2f}s  {BPM} BPM  {BARS} bars')
