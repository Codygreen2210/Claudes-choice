#!/usr/bin/env python3
"""Bayou Jig: the score. 1930s hot jazz at 188 BPM, swung: a trumpet fanfare for the title, a clarinet chorus over
stride piano, tuba and banjo, a hot trumpet chorus with a stop-time freeze, a slide whistle for the big jump, and the
"shave and a haircut, two bits" tag (a folk tag from 1899). Then it's pressed onto a worn 78: narrow band, mono,
wow and flutter, crackle. Writes jig.wav (the record), jig_clean.wav, and timeline.js (every beat and gag, so the
cartoon moves on the music)."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from studio.instruments import synth as S, theory as T  # noqa: E402

S.seed(1930)
BPM = 188
BEAT = 60 / BPM
BAR = 4 * BEAT
T0 = 0.35                         # the needle drops; first bar of the fanfare
INTRO_BARS = 2
DANCE = T0 + INTRO_BARS * BAR     # the dance starts on this downbeat
BARS = INTRO_BARS + 14
DUR = T0 + BARS * BAR + 1.6
rng = np.random.default_rng(7)

GM = {'piano': 0, 'tuba': 58, 'banjo': 105, 'clarinet': 71, 'trumpet': 56, 'mute': 59, 'trombone': 57}
_cache = {}


def inst(name, m, dur, vel=100):
    key = (name, m, round(dur, 3), vel)
    if key not in _cache:
        _cache[key] = S.sfhit(int(m), program=GM[name], bank=0, channel=0, dur=dur + 0.35, vel=int(vel))
    return _cache[key]


def drum(note, vel=100, dur=0.8):
    key = ('d', note, vel)
    if key not in _cache:
        _cache[key] = S.sfhit(note, kit=0, vel=vel, dur=dur)
    return _cache[key]


def at(bar, beat=0.0):
    """Time of a bar/beat, where bar 0 is the first bar of the fanfare."""
    return T0 + bar * BAR + beat * BEAT


buses = {k: S.Bus(DUR) for k in ('lead', 'piano', 'tuba', 'banjo', 'drums', 'fx')}
events = {'beats': [], 'downbeats': [], 'hits': [], 'gags': {}}

# ---------------------------------------------------------------- harmony
CHORDS = {2: 'F', 3: 'D7', 4: 'G7', 5: 'C7', 6: 'F', 7: ['F7', 'Bb'], 8: ['F', 'C7'], 9: 'F',
          10: 'Bb', 11: 'Bbm', 12: ['F', 'D7'], 13: ['G7', 'C7'], 14: 'F', 15: 'F'}


def chord_at(bar, beat):
    c = CHORDS.get(bar)
    if c is None:
        return 'C7'
    if isinstance(c, list):
        return c[0] if beat < 2 else c[1]
    return c


# ---------------------------------------------------------------- the tunes (bar-relative beats; .67 = a swung "and")
FANFARE = [(0, 60, .67), (.67, 64, .33), (1, 67, .67), (1.67, 70, .33), (2, 72, 2.0),
           (4, 72, .5), (4.67, 72, .33), (5, 76, .67), (6, 79, 1.8)]
A = [  # clarinet chorus, 8 bars from DANCE
    [(0, 72, .67), (.67, 69, .33), (1, 72, 1), (2, 74, .67), (2.67, 72, .33), (3, 69, 1)],
    [(0, 66, .67), (.67, 69, .33), (1, 72, 1), (2, 74, 1.5), (3.67, 72, .33)],
    [(0, 71, .67), (.67, 74, .33), (1, 77, 1), (2, 76, .67), (2.67, 74, .33), (3, 71, 1)],
    [(0, 72, 1), (1, 76, .67), (1.67, 79, .33), (2, 70, 2)],
    [(0, 69, .67), (.67, 72, .33), (1, 77, 1), (2, 77, .67), (2.67, 76, .33), (3, 77, 1)],
    [(0, 75, 1), (1, 74, 1), (2, 74, .67), (2.67, 72, .33), (3, 70, 1)],
    [(0, 69, 1), (1, 72, .67), (1.67, 69, .33)],                      # ...the jump (slide whistle) takes the rest
    [(0, 65, 1)],
]
B = [  # hot trumpet chorus
    [(0, 74, .67), (.67, 77, .33), (1, 82, 1), (2, 77, 1), (3, 74, 1)],
    [(0, 73, .67), (.67, 77, .33), (1, 80, 1), (2, 77, 1), (3, 73, 1)],
    [],                                                                   # stop time: the band hits, the gator freezes
    [(0, 71, .5), (.5, 74, .5), (1, 77, .5), (1.5, 79, .5), (2, 76, .5), (2.5, 79, .5), (3, 82, 1)],
]
TAG = [[(0, 77, 1), (1, 72, .67), (1.67, 72, .33), (2, 74, 1), (3, 72, 1)],   # shave and a hair-cut...
       [(1, 76, 1), (2, 77, 2)]]                                                # ...two bits!

for b, m, d in FANFARE:
    t = at(0, b)
    buses['lead'].add(t, inst('trumpet', m, d * BEAT, 112), 0.55)
buses['drums'].add(at(1, 2), S.hp(drum(49, 90, 2.5), 300), 0.3)             # cymbal swell under the held note
for k in range(10):
    buses['drums'].add(at(1, 2 + k * 0.2), drum(38, 40 + 7 * k, 0.3), 0.25)  # snare roll into the dance

for i, bar in enumerate(A):
    for b, m, d in bar:
        buses['lead'].add(at(2 + i, b), inst('clarinet', m, d * BEAT, 105), 0.8, -0.1)
for i, bar in enumerate(B):
    for b, m, d in bar:
        buses['lead'].add(at(10 + i, b), inst('trumpet', m, d * BEAT, 118), 0.62, 0.1)
for i, bar in enumerate(TAG):
    for b, m, d in bar:
        buses['lead'].add(at(14 + i, b), inst('trumpet', m, d * BEAT, 120), 0.6)
        buses['lead'].add(at(14 + i, b), inst('clarinet', m - 12, d * BEAT, 100), 0.5)
        buses['drums'].add(at(14 + i, b), drum(76, 110, 0.3), 0.35, 0.3)      # woodblock doubles the tag
        events['hits'].append(at(14 + i, b))

# ---------------------------------------------------------------- the rhythm section (bars 2..15)
STOP_BAR = 12
for bar in range(2, 16):
    for beat in range(4):
        t = at(bar, beat)
        events['beats'].append(t)
        if beat == 0:
            events['downbeats'].append(t)
        c = chord_at(bar, beat)
        root, ivs, _ = T.parse_chord(c)
        if bar == STOP_BAR:
            if beat in (0, 2):                                           # stop time: two band hits, silence around them
                hit = T.chord(c if beat == 0 else 'D7', 3)
                for m in hit:
                    buses['piano'].add(t, inst('piano', m, 0.25, 110), 0.5)
                buses['tuba'].add(t, inst('tuba', T.bass_of(c if beat == 0 else 'D7', 1), 0.25, 115), 0.6)
                buses['drums'].add(t, drum(49, 110, 1.2), 0.3)
                events['hits'].append(t)
            continue
        if bar >= 15 and beat > 2:
            continue
        # tuba: root on 1, fifth on 3 (oom-pah)
        if beat in (0, 2):
            m = T.bass_of(c, 1) + (7 if beat == 2 else 0)
            m = m - 12 if m > 47 else m
            buses['tuba'].add(t, inst('tuba', m, 0.4 * BEAT * 2, 110), 0.55)
            buses['piano'].add(t, inst('piano', m + 12, 0.3, 95), 0.4)          # stride left hand
        else:
            v = T.voice_lead([], c, 58, 72) if len(ivs) >= 3 else T.chord(c, 4)
            for m in v:
                buses['piano'].add(t, inst('piano', m, 0.22, 90), 0.33)          # stride right hand on 2 and 4
        # banjo: four strums a bar, chopped hard on 2 and 4
        strum = T.chord(c, 3)
        for k, m in enumerate(strum):
            buses['banjo'].add(t + k * 0.008, inst('banjo', m + 12, 0.18, 110 if beat % 2 else 80), 0.16 if beat % 2 else 0.1, 0.35)
        # drums: brushed snare on 2 and 4, woodblocks on the swung "and" of some beats
        if beat % 2:
            buses['drums'].add(t, drum(38, 70, 0.3), 0.22)
        if bar >= 10 and beat in (1, 3):
            buses['drums'].add(t + 0.67 * BEAT, drum(77, 90, 0.2), 0.16, -0.3)

# ---------------------------------------------------------------- gags
jump_up, jump_land = at(8, 2), at(9, 0)
events['gags'].update({'jump': jump_up, 'land': jump_land, 'stop': at(STOP_BAR, 0), 'stop2': at(STOP_BAR, 2),
                       'restart': at(STOP_BAR + 1, 0), 'tag': at(14, 0), 'twobits': at(15, 1), 'end': at(15, 2), 'dance': DANCE,
                       'title_out': DANCE - 0.25})
n = S.smp(2 * BEAT); tq = np.arange(n) / S.SR
whistle = S.sine(600 * (3.2 ** (tq / tq[-1]) ** 1.3) * (1 + 0.01 * np.sin(2 * np.pi * 6 * tq)), n) * np.sin(np.pi * np.minimum(tq / tq[-1] * 1.05, 1)) ** 0.3
buses['fx'].add(jump_up, whistle, 0.22)
n2 = S.smp(0.6); t2 = np.arange(n2) / S.SR
boing = S.sine(90 * (1 + 0.6 * np.exp(-t2 / 0.05)) * (1 + 0.25 * np.sin(2 * np.pi * 14 * t2) * np.exp(-t2 / 0.25)), n2) * np.exp(-t2 / 0.3)
buses['fx'].add(jump_land, boing, 0.5)
buses['drums'].add(jump_land, drum(35, 127, 0.8), 0.6)
buses['drums'].add(jump_land, drum(49, 110, 1.5), 0.3)
buses['drums'].add(at(15, 2), drum(49, 120, 2.0), 0.35)                          # the final cymbal
buses['drums'].add(at(15, 2), drum(35, 120, 0.8), 0.5)
for m in T.chord('F6', 3):
    buses['piano'].add(at(15, 2), inst('piano', m, 1.2, 115), 0.45)
buses['tuba'].add(at(15, 2), inst('tuba', 29, 1.0, 120), 0.6)

# ---------------------------------------------------------------- mix, then press it onto a worn 78
mix = sum(buses[k].out() for k in buses)
room = S.plate(1.2, 0.35, 0.01, 300, 5000)
mix = mix + S.reverb(mix * 0.4, room, 0.25)
clean = S.master(mix, lufs=-16, fade=0.8)


def seventy_eight(x):
    m = x.mean(0)                                                          # mono
    n = len(m); tt = np.arange(n) / S.SR
    # wow (slow, 0.55 Hz) and flutter (fast, 7 Hz): the record isn't quite round and the turntable isn't quite steady
    rate = 1 + 0.0035 * np.sin(2 * np.pi * 0.55 * tt) + 0.0007 * np.sin(2 * np.pi * 7.1 * tt)
    pos = np.cumsum(rate); pos = pos / pos[-1] * (n - 1)
    m = np.interp(pos, np.arange(n), m)
    m = S.bp(m, 220, 5200, 4)                                              # the narrow acoustic band of the era
    m = S.eq(m, [('peak', 1500, 3.0, 0.9), ('peak', 400, -2.0, 1.0)])     # a nasal, horn-like midrange
    m = np.tanh(m * 2.2) / np.tanh(2.2)                                    # a little cutting-lathe grit
    # surface: hiss, crackle, and a pop each revolution (78 rpm = 1.3 Hz)
    hiss = S.hp(S.noise(n, 'pink'), 1500) * 0.012
    crackle = np.zeros(n)
    for i in rng.choice(n, int(DUR * 28), replace=False):
        L = int(rng.integers(8, 60)); a = rng.uniform(0.02, 0.12) * rng.choice([-1, 1])
        crackle[i:i + L] += a * np.exp(-np.arange(min(L, n - i)) / 6)
    for k in range(int(DUR * 78 / 60)):
        i = int((0.37 + k * 60 / 78) * S.SR)
        if i < n - 200:
            crackle[i:i + 120] += 0.25 * np.exp(-np.arange(120) / 18) * np.sign(np.sin(np.arange(120) * 0.9))
    crackle = S.bp(crackle, 800, 7000)
    return m * 0.95 + hiss + crackle


if __name__ == '__main__':
    rec = seventy_eight(clean)
    rec = S.master(np.stack([rec, rec]), lufs=-16, fade=0.3)
    S.write(str(HERE / 'jig.wav'), rec)
    S.write(str(HERE / 'jig_clean.wav'), clean)
    events.update({'bpm': BPM, 'beat': BEAT, 'bar': BAR, 'dur': DUR, 't0': T0})
    (HERE / 'timeline.js').write_text('window.TL = ' + json.dumps(events) + ';\n')
    print(f'{DUR:.1f} s, {len(events["beats"])} beats, gags {events["gags"]}')
