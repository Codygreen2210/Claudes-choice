#!/usr/bin/env python3
"""Lane Luck promo track: an original 21-second shop-floor shuffle, built only from the studio's
own synth voices (no samples, no soundfont, no borrowed tune).

    python3 daily/2026-10-04-lane-luck/ads/make-track.py            # writes ads/track.wav
    python3 studio/senses/listen.py daily/2026-10-04-lane-luck/ads/track.wav --out notes/

120 BPM swung eighths in C: C6 | A7 | Dm7 | G7 turnaround. Beats fall every 0.5 s, so the clip's
cuts (tap 2.5 s, verdict 9.5 s, card 12.5 s, end card 17.5 s) all sit on a beat. Last chord lands
at 20.0 s and rings out to 21.0 s.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..')))
from studio.instruments import synth as S   # noqa: E402
from studio.instruments import theory as T  # noqa: E402

S.seed(1004)
BPM = 120.0
BEAT = 60.0 / BPM
DUR = 21.0
SWING = 2 / 3            # where the off-beat eighth sits inside the beat
# Master tone. Shelves are capped at 6 dB by the owner's rule.
TONE = [('lowshelf', 180, -2.0, 0.7), ('peak', 450, -3.0, 0.9), ('highshelf', 4000, 4.0, 0.7)]


def at(beat):
    """Beat number (swung: x.5 means the late off-beat) to seconds."""
    whole = np.floor(beat)
    frac = beat - whole
    if abs(frac - 0.5) < 1e-6:
        frac = SWING
    return float((whole + frac) * BEAT)


CHORDS = ['C6', 'A7', 'Dm7', 'G7', 'C6', 'A7', 'Dm7', 'G7', 'C6']   # one per bar, bars 0..8
bass = S.Bus(DUR); keys = S.Bus(DUR); tune = S.Bus(DUR); drums = S.Bus(DUR); fx = S.Bus(DUR)
K = S.kit('synth')
K['kick'] = S.kick(pitch=62, punch=120, dec=0.13, click=0.5)     # tuned up so a phone speaker can carry it


def shaker(dec=0.03, g=1.0):
    n = S.smp(0.12)
    return S.hp(S.noise(n), 5500) * np.exp(-S.tt(n) / dec) * g


def snap():
    """Finger-snap-ish click: two short band-passed noise bursts."""
    n = S.smp(0.12); t = S.tt(n)
    x = S.bp(S.noise(n), 1500, 4200) * (np.exp(-t / 0.012) + 0.5 * np.exp(-np.maximum(t - 0.011, 0) / 0.02) * (t > 0.011))
    return S.norm(x)


# ---- drums: kick on 1 and 3, brushy snare on 2 and 4, swung shaker eighths ----
for bar in range(10):
    b0 = bar * 4
    full = bar >= 1
    lift = b0 >= 24                                      # from bar 6 the band fills out (the card lands at beat 25)
    stop = bar == 9
    for q in range(4):
        if stop and q >= 2:
            break
        if q in (0, 2) and full:
            drums.add(at(b0 + q), K['kick'], 0.5, mark=True)
        else:
            if lift:
                drums.add(at(b0 + q), K['snare'], 0.30, pan=0.05)
            drums.add(at(b0 + q), snap(), 0.40 if full else 0.22, pan=-0.25)
        drums.add(at(b0 + q), shaker(0.022), 0.30 if full else 0.10, pan=0.3)
        drums.add(at(b0 + q + 0.5), shaker(0.035), 0.48 if full else 0.15, pan=0.3)
    if lift and not stop:
        drums.add(at(b0 + 1.5), K['ohat'], 0.12, pan=-0.3)
        drums.add(at(b0 + 3.5), K['ohat'], 0.14, pan=-0.3)

# ---- bass: bouncy two-feel, root then fifth, with a swung push into the next bar ----
for bar, sym in enumerate(CHORDS):
    b0 = bar * 4
    root = T.bass_of(sym, 2)
    if root < 36:
        root += 12
    fifth = root + 7 if root + 7 <= 50 else root - 5
    nxt = T.bass_of(CHORDS[bar + 1], 2) if bar + 1 < len(CHORDS) else T.note('F2')
    if nxt < 36:
        nxt += 12
    lead_in = nxt - 1 if nxt > root else nxt + 1          # chromatic step into the next root
    lvl = 1.0 if bar >= 1 else 0.45                      # bar 0 is a quiet count-in under the first caption
    bass.add(at(b0), S.bass_note(root, 0.30, bright=1900, sub=0.12), 0.9 * lvl)
    bass.add(at(b0 + 1.5), S.bass_note(root, 0.12, bright=1600, sub=0.12), 0.55 * lvl)
    bass.add(at(b0 + 2), S.bass_note(fifth, 0.30, bright=1900, sub=0.12), 0.85 * lvl)
    if bar >= 1:
        bass.add(at(b0 + 3), S.bass_note(root + 12 if root + 12 <= 52 else root, 0.2, bright=1500), 0.6)
        bass.add(at(b0 + 3.5), S.bass_note(lead_in, 0.14, bright=1400), 0.7)
# bar 9: F, F#dim, then G and a stop; walk G A B up to the last C
for beat, m, ln in [(36, 'F2', 0.4), (37, 'F#2', 0.4), (38, 'G2', 0.3), (38.5, 'G2', 0.14), (39, 'A2', 0.2), (39.5, 'B2', 0.14)]:
    bass.add(at(beat), S.bass_note(T.note(m), ln, bright=1600), 0.85)
bass.add(at(40), S.bass_note(T.note('C2'), 0.9, bright=1300), 0.9)
bass.add(at(40), S.bass_note(T.note('C3'), 0.9, bright=1600), 0.5)

# ---- keys: short electric-piano stabs on 2 and 4 (the shuffle's back-beat) ----
voic = T.progression(CHORDS, octave=4, voices=4)
for bar, notes in enumerate(voic):
    b0 = bar * 4
    hits = [3] if bar == 0 else ([1, 3] if bar < 6 else [1, 2.5, 3])
    for h in hits:
        for j, m in enumerate(notes):
            keys.add(at(b0 + h), S.epiano(m, 0.32 if h != 2.5 else 0.2, vel=0.75), (0.16 if h != 2.5 else 0.10) * (0.5 if bar == 0 else 1),
                     pan=-0.35 + 0.2 * j)
for beat, sym in [(36, 'F6'), (37, 'F#dim7'), (38, 'G7')]:
    for j, m in enumerate(T.chord(sym, 4)):
        keys.add(at(beat), S.epiano(m, 0.45, vel=0.8), 0.12, pan=-0.35 + 0.2 * j)
for j, m in enumerate(T.chord('C6', 4) + [T.note('D5'), T.note('G5')]):
    keys.add(at(40) + 0.012 * j, S.epiano(m, 1.6, vel=0.85), 0.13, pan=-0.4 + 0.16 * j)

# ---- tune: plucked line with a bell on top of the long notes. (beat, note, beats long) ----
MELODY = [
    (3.5, 'G4', .5),
    (4, 'E5', .5), (4.5, 'C#5', .5), (5, 'E5', 1), (6, 'G5', 1), (7, 'E5', .5), (7.5, 'A4', .5),
    (8, 'F5', .5), (8.5, 'D5', .5), (9, 'F5', 1), (10, 'A5', 1.5), (11.5, 'F5', .5),
    (12, 'G5', .5), (12.5, 'F5', .5), (13, 'D5', .5), (13.5, 'B4', .5), (14, 'G4', 1), (15, 'A4', .5), (15.5, 'B4', .5),
    (16, 'C5', .5), (16.5, 'E5', .5), (17, 'G5', 1), (18, 'A5', .5), (18.5, 'G5', .5), (19, 'E5', 1),
    (20, 'C#5', .5), (20.5, 'E5', .5), (21, 'G5', 1), (22, 'Bb5', .5), (22.5, 'A5', .5), (23, 'G5', .5), (23.5, 'E5', .5),
    (24, 'F5', 1), (25, 'A5', .5), (25.5, 'C6', .5), (26, 'D6', 1), (27, 'C6', .5), (27.5, 'A5', .5),
    (28, 'B5', .5), (28.5, 'A5', .5), (29, 'G5', .5), (29.5, 'F5', .5), (30, 'D5', .5), (30.5, 'F5', .5), (31, 'D5', .5), (31.5, 'B4', .5),
    (32, 'C5', 1.5), (33.5, 'E5', .5), (34, 'G5', .5), (34.5, 'A5', .5), (35, 'C6', 1),
    (36, 'A5', .5), (36.5, 'F5', .5), (37, 'A5', .5), (37.5, 'Eb5', .5), (38, 'D5', .5),
    (40, 'C6', 2),
]
for beat, nm, ln in MELODY:
    m = T.note(nm)
    secs = ln * BEAT
    y = S.pluck(m, dur=max(0.16, secs * 0.9), bright=9000, dark=3600, fdec=0.06, adec=0.16 + 0.12 * ln, sq=0.35)
    tune.add(at(beat), y, 0.36, pan=0.12)
    tune.add(at(beat), S.pop_note(m, 0.2), 0.09, pan=0.12)          # the bounce on the front of each note
    if beat >= 24:                                       # the lift: same line an octave up on a glassy bell
        tune.add(at(beat), S.bell(m + 12, dur=max(0.25, secs), ratio=2.0, idx=0.9, dec=0.16), 0.06, pan=0.3)
    if ln >= 1:
        tune.add(at(beat), S.bell(m + 12, dur=0.9, ratio=3.0, idx=1.2, dec=0.28), 0.10, pan=-0.2)

# ---- little cues for the picture ----
fx.add(2.5, S.pop_note(T.note('G5'), 0.25), 0.4)                    # the tap
fx.add(2.5 + 0.09, S.pop_note(T.note('C6'), 0.25), 0.3)
fx.add(12.5, S.bell(T.note('E6'), dur=1.2, ratio=3.5, idx=1.6, dec=0.4), 0.14, pan=0.2)   # the card
fx.add(17.5, S.bell(T.note('G6'), dur=1.2, ratio=3.5, idx=1.6, dec=0.4), 0.12, pan=-0.2)  # the end card
fx.add(at(40), S.bell(T.note('C6'), dur=1.4, ratio=3.5, idx=1.8, dec=0.5), 0.16)
fx.add(at(40), S.bell(T.note('G6'), dur=1.4, ratio=3.5, idx=1.4, dec=0.5), 0.09, pan=0.3)
drums.add(at(40), K['kick'], 0.6)
drums.add(at(40), snap(), 0.3, pan=-0.25)

# ---- mix ----
room = S.plate(dur=1.0, decay=0.22, lo=400, hi=6500)
mel = tune.out() + fx.out()
k = S.eq(S.hp(keys.out(), 260), [('peak', 420, -3.0, 1.0)])
b = S.stereo(bass.out().mean(0))                                    # bass dead centre for phone speakers
mix = (b * 0.50 + k * 1.0 + mel * 1.0 + drums.out() * 1.0
       + S.reverb(mel, room, 0.10) + S.reverb(k, room, 0.07))
# Arrangement level: quiet count-in, light groove under the race, full band from the card on.
ride_t = [0.0, 1.9, 2.0, 12.3, 12.5, DUR]
ride_db = [-8.0, -8.0, -4.8, -4.8, 0.0, 0.0]
mix = mix * S.db(np.interp(S.tt(mix.shape[1]), ride_t, ride_db))
mix = S.glue(mix, thr=-14, ratio=1.8, rel=0.15)
out = S.master(mix, lufs=-14.0, tone=TONE, fade=0.5, ceiling=0.80)
path = os.path.join(HERE, 'track.wav')
S.write(path, out)
print(f'wrote {path}  {out.shape[1] / S.SR:.2f} s')
