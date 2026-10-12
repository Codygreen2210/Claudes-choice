#!/usr/bin/env python3
"""Honey: the score.

Warm and slow, to match liquid. Electric piano and a low pad, a soft pulse, and
a bell that answers each phrase. It sits under a narrator, so 300 Hz - 3 kHz
stays thin and the interest lives above and below her.

Carried over from earlier builds, as facts rather than taste:
  - synth.reverb and synth.pingpong return ONLY wet, so both are sends.
  - synth.kick is ~48% sub; the kit is split into low and top buses.
  - a part's high-pass must sit below its own lowest note.
  - soft_pad returns stereo with its sides detuned against each other, which is
    what cancels on a phone speaker, so it gets narrowed.

    python3 score.py   ->  score.wav, beats.json
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'studio', 'instruments'))

import synth as S          # noqa: E402
import theory as T         # noqa: E402

BPM = 84
BEAT = 60.0 / BPM          # 0.714 s
BAR = 4 * BEAT             # 2.857 s
BARS = 23                  # 65.7 s, for a 62.8 s read plus a tail
DUR = BARS * BAR

# I - vi - IV - V in F, warm and unhurried
PROG = ['F', 'Dm', 'Bb', 'C']
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
def keys():
    """Electric piano, the body of the thing. Lowest note is around F3 (175 Hz),
    so there's no high-pass on it at all — it lives under the voice, not beside it."""
    out = np.zeros(N)
    for bar in range(BARS):
        notes = T.chord(bar_chord(bar), octave=4)
        for i, m in enumerate(notes):
            if bar < 1 and i > 1:
                continue
            t = bar * BAR + i * BEAT * 0.18
            at(out, t, S.epiano(m, dur=BAR * 0.9, vel=0.55), 0.42)
        # a little upper answer on the back half
        if 2 <= bar < BARS - 2:
            at(out, bar * BAR + 2.5 * BEAT,
               S.epiano(notes[-1] + 12, dur=BEAT * 1.6, vel=0.4), 0.3)
    return S.lp(out, 8000, 2)


def bells():
    """A bell per phrase, high and sparse — the sparkle above the voice."""
    out = np.zeros(N)
    for bar in range(2, BARS - 1, 2):
        notes = T.chord(bar_chord(bar), octave=6)
        at(out, bar * BAR, S.bell(notes[0], dur=2.4, ratio=3.1, idx=1.8, dec=0.7), 0.30)
        at(out, bar * BAR, S.bell(notes[0] + 12, dur=1.8, ratio=3.6, idx=1.5, dec=0.5), 0.16)
        if bar % 4 == 2:
            at(out, bar * BAR + 2 * BEAT,
               S.bell(notes[2], dur=1.8, ratio=3.4, idx=1.5, dec=0.5), 0.20)
    return S.hp(out, 1100, 2)


def warmth():
    """soft_pad is already stereo (its sides are detuned against each other)."""
    out = np.zeros((2, N))
    for bar in range(0, BARS - 1):
        notes = T.chord(bar_chord(bar), octave=3)
        at(out, bar * BAR, S.soft_pad(notes, BAR * 0.98, a=0.6, r=0.8, bright=1300), 0.048)
    return S.lp(out, 1900, 2)


def low():
    out = np.zeros(N)
    for bar in range(1, BARS - 1):
        root = T.bass_of(bar_chord(bar), octave=2)
        at(out, bar * BAR, S.bass_note(root, BEAT * 2.4, bright=900, sub=0.22), 0.42)
        at(out, bar * BAR + 2.5 * BEAT, S.bass_note(root, BEAT * 1.2, bright=900, sub=0.18), 0.28)
    return S.lp(out, 1600, 2)


def pulse():
    """Barely a drum kit: a soft heartbeat and a shaker-ish tick."""
    lowb = np.zeros(N)
    top = np.zeros(N)
    k = S.kit('synth')
    for bar in range(2, BARS - 2):
        b0 = bar * BAR
        at(lowb, b0, k['kick'], 0.55)
        at(lowb, b0 + 2 * BEAT, k['kick'], 0.34)
        for i in range(4):
            at(top, b0 + i * BEAT + BEAT / 2, k['hat'], 0.17)
    return lowb, top


def arc(n):
    pts_t = [0.0, 2 * BAR, 6 * BAR, 11 * BAR, 13 * BAR, 17 * BAR, 21 * BAR, 22 * BAR, BARS * BAR]
    pts_db = [-13.0, -7.0, -2.0, 0.0, -3.5, 0.5, 0.0, -4.0, -15.0]
    t = np.arange(n) / S.SR
    return 10 ** (np.interp(t, pts_t, pts_db) / 20.0)


# --------------------------------------------------------------------------- mix
def build():
    S.seed(808)

    kz = keys()
    bl = bells()
    pd = warmth()
    lo = low()
    p_low, p_top = pulse()

    K_dry = S.stereo(kz, 0.0)
    KZ = K_dry + 0.16 * S.pingpong(K_dry, d=BEAT, fb=0.12, taps=2, lo=600, hi=5000)
    B_dry = S.stereo(bl, 0.0)
    BL = B_dry + 0.34 * S.pingpong(B_dry, d=BEAT * 1.5, fb=0.20, taps=3, lo=1200, hi=9000)
    PD = 0.6 * pd + 0.4 * S.stereo(pd.mean(axis=0), 0.0)     # narrowed, see warmth()

    mix = (KZ * 0.95 + BL * 1.25 + PD * 0.6 + S.stereo(lo, 0.0) * 0.8
           + S.stereo(p_low, 0.0) * 0.26 + S.stereo(p_top, 0.0) * 0.95)
    mix = mix * arc(mix.shape[-1])

    mix = mix + S.reverb(mix, S.plate(2.6, 0.6, 0.025, 450, 6500), wet=0.16)   # send
    mix = S.glue(mix, thr=-18, ratio=1.8, rel=0.3)

    mix = S.eq(mix, [
        ('peak', 420, -4.0, 0.9),       # her body
        ('peak', 760, -2.5, 1.0),       # the low-mid crowding
        ('peak', 2200, -2.0, 1.0),      # her consonants
        ('highshelf', 8500, 4.0, 0.7),
    ])

    return S.master(mix, lufs=-18.0, fade=1.8, ceiling=0.72)


if __name__ == '__main__':
    S.write(os.path.join(HERE, 'score.wav'), build())
    with open(os.path.join(HERE, 'beats.json'), 'w') as f:
        json.dump({'bpm': BPM, 'beat': BEAT, 'bar': BAR, 'bars': BARS,
                   'duration': DUR, 'progression': PROG}, f, indent=2)
    print(f'score.wav  {DUR:.2f}s  {BPM} BPM  {BARS} bars')
