#!/usr/bin/env python3
"""Kill Screen: the score.

A chiptune-leaning bed for a 49-second vertical facts reel, built to sit UNDER a narrator.
The arrangement deliberately leaves the 300 Hz - 3 kHz band thin, because that is where
the voice lives; the music carries its interest in the sub, the bass and above 3 kHz.

    python3 score.py            ->  score.wav  (and beats.json for the picture)

Run `python3 ../../studio/senses/listen.py score.wav --out notes/` afterwards.
That is the house rule, and it is what caught the mud in the first pass.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'studio', 'instruments'))

import synth as S          # noqa: E402
import theory as T         # noqa: E402

BPM = 140
BEAT = 60.0 / BPM          # 0.42857 s
BAR = 4 * BEAT             # 1.71429 s
BARS = 29                  # 49.7 s, enough for a 46.1 s read plus a tail
DUR = BARS * BAR

PROG = ['Am', 'F', 'C', 'G']          # i - VI - III - VII in A minor
N = S.smp(DUR)


def at(buf, t, x, gain=1.0):
    """Add x into buf at time t, clipped to the buffer."""
    a = S.smp(t)
    if a >= buf.shape[-1]:
        return
    b = min(buf.shape[-1], a + x.shape[-1])
    buf[..., a:b] += x[..., :b - a] * gain


def bar_chord(bar):
    return PROG[bar % len(PROG)]


# --------------------------------------------------------------------------- parts
def arp():
    """Chiptune arpeggio: 16ths through the chord, two octaves, bitcrushed.

    Kept above 1 kHz so it rides over the voice instead of fighting it.
    """
    out = np.zeros(N)
    step = BEAT / 4
    for bar in range(BARS):
        sym = bar_chord(bar)
        notes = T.chord(sym, octave=5)
        # a 16-step pattern that climbs, falls, then syncopates
        order = [0, 1, 2, 1, 0, 2, 1, 2, 0, 1, 2, 1, 0, 2, 1, 2]
        for i in range(16):
            # thin out the intro and the outro so the shape has an arc
            if bar < 2 and i % 4 != 0:
                continue
            if bar >= BARS - 2 and i % 2 != 0:
                continue
            m = notes[order[i] % len(notes)] + (12 if i >= 8 else 0)
            t = bar * BAR + i * step
            n = S.smp(step * 1.6)
            y = S.square(S.mtof(m), n, 0.42) * S.adsr(n, 0.002, 0.05, 0.25, 0.04)
            at(out, t, y, 0.32)
    # bits=7/down=3 put a lot of aliasing junk in 2-6 kHz, which the ears read
    # as "harsh or tiring". Gentler crush, and a lid on top of it.
    out = S.bitcrush(out, bits=10, down=2)
    # 450, not 1100: the arp plays around A5 (880 Hz), so a 1.1 kHz high-pass
    # cut the fundamentals out of the part and left 13 dB of harmonics — the
    # ears' "buried part" case. 450 Hz still clears the voice's fundamental.
    out = S.hp(out, 450, 2)
    out = S.lp(out, 8000, 2)                  # the harshness the ears found
    return out


def bassline():
    """Bass plus a sine sub.

    The first pass read 'thin low end' at 16% below 250 Hz, so the sub layer
    is a separate sine an octave down rather than the synth's own sub knob.
    """
    out = np.zeros(N)
    sub = np.zeros(N)
    for bar in range(BARS):
        if bar < 1:
            continue
        root = T.bass_of(bar_chord(bar), octave=2)
        # eighth-note drive, with the 'and' of 3 pushed for momentum
        hits = [0, 0.5, 1, 1.5, 2, 2.75, 3, 3.5]
        for h in hits:
            if bar >= BARS - 2 and h not in (0, 2):
                continue
            t = bar * BAR + h * BEAT
            y = S.bass_note(root, BEAT * 0.48, bright=1500, sub=0.6)
            at(out, t, y, 0.55)
        # one sub note per bar, held, under the whole bar
        n = S.smp(BAR * 0.92)
        f = S.mtof(root - 12)
        s = S.sine(f, n) * S.adsr(n, 0.01, 0.1, 0.9, 0.12)
        at(sub, bar * BAR, s, 0.07)
    return S.lp(out, 2600, 2) + S.lp(sub, 140, 2)


def crash_hit(dur=2.2):
    """A crash, from noise. The soundfont kits need tinysoundfont, which this
    container can't install, so the whole kit is the from-scratch one."""
    n = S.smp(dur)
    t = S.tt(n)
    y = S.noise(n, 'white') * np.exp(-t / 0.55)
    y = S.hp(y, 3200, 2) + 0.35 * S.hp(S.noise(n, 'white') * np.exp(-t / 1.1), 6500, 2)
    return S.norm(y)


def tom_hit(pitch=120, dec=0.18):
    n = S.smp(0.4)
    t = S.tt(n)
    f = pitch * (1 + 0.5 * np.exp(-t / 0.05))
    y = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.exp(-t / dec)
    y += S.noise(n, 'white') * np.exp(-t / 0.01) * 0.15
    return S.norm(y)


def drums():
    """Returns (low, top) on separate buses.

    synth.kick is 48% sub / 49% bass, so raising "the drums" to sharpen the
    beat also buries the track in low end. Splitting them means the transients
    that carry the pulse can come up without the kick coming with them.
    """
    low = np.zeros(N)
    top = np.zeros(N)
    k = S.kit('synth')
    k['crash'] = crash_hit()
    k['tom'] = tom_hit()
    for bar in range(BARS):
        if bar < 2 or bar >= BARS - 2:
            continue
        b0 = bar * BAR
        at(low, b0 + 0 * BEAT, k['kick'], 0.95)
        at(low, b0 + 2.5 * BEAT, k['kick'], 0.80)
        at(top, b0 + 1 * BEAT, k['snare'], 0.55)
        at(top, b0 + 3 * BEAT, k['snare'], 0.55)
        for i in range(8):
            t = b0 + i * BEAT / 2
            open_ = (i == 7)
            at(top, t, k['ohat'] if open_ else k['hat'], 0.22 if open_ else 0.15)
        # a fill before each 4-bar turnaround
        if bar % 4 == 3:
            for j, h in enumerate([3.25, 3.5, 3.75]):
                at(top, b0 + h * BEAT, k['tom'], 0.35 + 0.1 * j)
    # crash on the first downbeat of the groove and at the button
    at(top, 2 * BAR, k['crash'], 0.45)
    at(top, (BARS - 2) * BAR, k['crash'], 0.5)
    return low, top


def accents(marks):
    """A sub impact under each section change, plus one riser into the groove."""
    out = np.zeros(N)
    at(out, 2 * BAR - 0.9, S.riser(0.9, 400, 7000), 0.18)
    for t in marks:
        at(out, t, S.impact(1.2), 0.34)
    return out


def arc(n):
    """A loudness shape across the reel.

    The first pass measured a loudness range of 1.6 LU, which the ears called
    "very flat dynamics" — the intro was as loud as the middle. A bed under a
    narrator shouldn't swing like a song, but it does need an arc, so this is
    roughly 8 dB from the quietest point to the loudest.
    """
    pts_t = [0.0, 2 * BAR, 6 * BAR, 14 * BAR, 15.5 * BAR, 22 * BAR, 26 * BAR, 27 * BAR, BARS * BAR]
    pts_db = [-11.0, -7.0, -2.0, 0.0, -4.0, 0.5, 0.5, -3.0, -13.0]
    t = np.arange(n) / S.SR
    return 10 ** (np.interp(t, pts_t, pts_db) / 20.0)


# --------------------------------------------------------------------------- mix
def build():
    S.seed(2026)

    # section marks: every 4 bars, where the reel turns over to a new fact
    marks = [b * BAR for b in range(2, BARS - 2, 4)]

    a = arp()
    b = bassline()
    d_low, d_top = drums()
    x = accents(marks)

    # The arp gets a little width, but not much: the first pass came back with
    # stereo correlation 0.04 and a warning that it may cancel on a phone
    # speaker, which is where this will actually be watched. The ping-pong is
    # now a short slap at low feedback, and the chorus is mostly dry.
    # synth.pingpong returns ONLY its taps, and they alternate hard left / hard
    # right, so using its output as the signal is what pinned correlation at
    # 0.04 through two passes. It's a send: dry down the middle, a little wet.
    A_dry = S.stereo(a, 0.0)
    A_wet = S.pingpong(A_dry, d=BEAT / 2, fb=0.12, taps=2, lo=900, hi=6000)
    A = A_dry + 0.22 * A_wet
    A = S.chorus(A, rate=0.45, depth_ms=1.2, mix=0.10)
    B = S.stereo(b, 0.0)
    DL = S.stereo(d_low, 0.0)
    DT = S.stereo(d_top, 0.0)
    X = S.stereo(x, 0.0)

    # Transients up, low end restrained: the pulse comes from DT, not from DL.
    mix = A * 1.0 + B * 0.34 + DL * 0.30 + DT * 1.0 + X * 0.22
    mix = mix * arc(mix.shape[-1])

    # synth.reverb is a SEND: it returns only the wet convolution, and plate()
    # builds two independent random IRs, so `mix = reverb(mix, ...)` threw the
    # dry signal away and left a decorrelated, band-limited wash. That one line
    # was behind the stuck 0.05 correlation, the "thin low end" and the
    # low-mid crowding across three passes. Dry plus a little wet.
    mix = mix + S.reverb(mix, S.plate(1.8, 0.4, 0.015, 400, 6000), wet=0.10)
    mix = S.glue(mix, thr=-18, ratio=1.8, rel=0.25)

    # Carve the voice's band out of the music before it ever meets the voice.
    # 420 Hz is where the first pass read as mud; 2.1 kHz is where the consonants live.
    mix = S.eq(mix, [
        ('peak', 420, -3.0, 0.9),       # low-mid crowding: the voice lives here
        ('peak', 2100, -2.0, 1.0),      # make room for consonants
        ('peak', 3600, -1.5, 0.8),      # takes the edge off the crush aliasing
        ('highshelf', 9000, 1.5, 0.7),
    ])

    # -18 LUFS, not -14: this is a bed under a narrator, and the mix step
    # ducks it further. Ceiling leaves room for the voice on top.
    mix = S.master(mix, lufs=-18.0, fade=1.2, ceiling=0.72)
    return mix, marks


if __name__ == '__main__':
    mix, marks = build()
    out = os.path.join(HERE, 'score.wav')
    S.write(out, mix)

    grid = {
        'bpm': BPM,
        'beat': BEAT,
        'bar': BAR,
        'bars': BARS,
        'duration': DUR,
        'progression': PROG,
        'section_marks': marks,
    }
    with open(os.path.join(HERE, 'beats.json'), 'w') as f:
        json.dump(grid, f, indent=2)

    print(f'score.wav  {DUR:.2f}s  {BPM} BPM  {BARS} bars')
    print(f'beats.json  {len(marks)} section marks')
