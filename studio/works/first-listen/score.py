#!/usr/bin/env python3
"""First Listen: the score. Writes the audio (mix.wav) and the exact note data the picture is drawn from (score.js),
so what you see is precisely what you hear.

The theme came out of studio/explore: 9 generated motifs, then 9 bred from the two with the clearest shape.
This one (generation 2, #4) rises step by step to C#6 and settles back: one breath in and out.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))
from studio.instruments import synth as S, theory as T  # noqa: E402
import motif  # noqa: E402

S.seed(27)
BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT
T0 = 0.6                                   # a breath of silence before the first note
BARS = 24
DUR = T0 + BARS * BAR + 4.0
THEME = motif.melody({"contour": "arch", "leap": 0.8795960515091095, "density": 0.4951709790482493, "range_n": 9,
                      "rhythm": "syncopated", "seed": 362494})
THEME = [(t / BEAT, m, d / BEAT) for t, m, d in THEME]      # in beats

LOOP1 = ['Amaj9', 'E/G#', 'C#m7', 'F#m9']
LOOP2 = ['Dmaj7#11', 'E6', 'C#m7', 'Amaj9']
CHORDS = {0: None, 1: None, 2: 'Amaj9', 3: 'F#m9'}
for i, c in enumerate(LOOP1 + LOOP2):
    CHORDS[4 + i] = c
for i, c in enumerate(LOOP1 + LOOP2):
    CHORDS[12 + i] = c
CHORDS.update({20: 'Amaj9', 21: 'Dmaj7#11', 22: 'F#m9', 23: 'Amaj9'})

events = []            # everything the picture needs: {t, d, m, i(nstrument), v(elocity)}
kicks, snares = [], []
buses = {k: S.Bus(DUR) for k in ('keys', 'pad', 'bass', 'arp', 'bell', 'lead', 'drums', 'air')}


def bt(bar, beat=0.0):
    return T0 + bar * BAR + beat * BEAT


def note(bus, t, m, d, inst, v, sound, g, pan=0.0):
    buses[bus].add(t, sound, g, pan)
    events.append({'t': round(t, 4), 'd': round(d, 4), 'm': int(m), 'i': inst, 'v': round(v, 3)})


def theme(bar, inst='keys', octave=0, g=0.34, vel=0.7, transpose_last=None):
    for k, (b, m, d) in enumerate(THEME):
        m2 = m + 12 * octave
        if transpose_last is not None and k == len(THEME) - 1:
            m2 = transpose_last
        t = bt(bar, b); dur = d * BEAT
        if inst == 'keys':
            note('keys', t, m2, dur, 'keys', vel, S.epiano(m2, max(dur * 1.8, 1.0), vel), g, (m2 - 76) / 40)
        elif inst == 'string':
            note('keys', t, m2, dur, 'string', vel, S.karplus(m2, max(dur * 2, 1.2), 0.6), g * 0.9, -(m2 - 76) / 40)
        elif inst == 'lead':
            pass
    if inst == 'lead':
        ev = [(bt(bar, b), m + 12 * octave, d * BEAT) for b, m, d in THEME]
        buses['lead'].add(0, S.lead(ev, DUR, glide=0.03, vib=0.1, bright=4200), g)
        for t, m, d in ev:
            events.append({'t': round(t, 4), 'd': round(d, 4), 'm': int(m), 'i': 'lead', 'v': vel})


# ---------------------------------------------------------------- A: the theme alone (bars 0-3)
theme(0, 'keys', g=0.36, vel=0.62)
for bar in (2, 3):
    c = CHORDS[bar]
    v = T.progression([c], octave=3)[0]
    buses['pad'].add(bt(bar), S.soft_pad(v, BAR + 0.3, a=2.0 if bar == 2 else 0.6, r=1.4, bright=900 + 200 * (bar - 2)), 0.20 + 0.06 * (bar - 2))
    for m in v:
        events.append({'t': round(bt(bar), 4), 'd': round(BAR, 4), 'm': m, 'i': 'pad', 'v': 0.4})

# ---------------------------------------------------------------- B and C share the harmony (bars 4-19)
prev = None
for bar in range(4, 20):
    c = CHORDS[bar]
    v = T.voice_lead(prev or T.chord(c, 3), c, 52, 76) if prev else T.progression([c], octave=3)[0]
    prev = v
    full = bar >= 12
    buses['pad'].add(bt(bar), S.soft_pad(v, BAR + 0.1, a=0.5, r=0.9, bright=1400 if not full else 2400), 0.27 if not full else 0.24)
    for m in v:
        events.append({'t': round(bt(bar), 4), 'd': round(BAR, 4), 'm': m, 'i': 'pad', 'v': 0.5 if full else 0.4})
    root = T.bass_of(c, 1)
    if bar >= 8:
        # bass: root on 1, a push on the "and" of 2, octave on 3 (fuller in C)
        pattern = [(0, root, 1.4), (1.5, root, 0.4), (2, root + 12, 0.9), (3.5, root, 0.4)] if full else [(0, root, 1.8), (2.5, root, 1.2)]
        for b, m, d in pattern:
            t = bt(bar, b)
            note('bass', t, m, d * BEAT, 'bass', 0.8, S.bass_note(m, d * BEAT, 1100 if not full else 1900, sub=0.3), 0.32 if full else 0.24)
    if bar >= 6:
        # arp: euclidean plucks over the chord tones, rotating each bar
        steps = T.euclid(7 if full else 5, 16, rotate=bar % 5)
        tones = sorted(v + [v[0] + 12, v[1] + 12])
        for s, on in enumerate(steps):
            if not on:
                continue
            m = tones[(s * 3 + bar) % len(tones)] + 12
            t = bt(bar, s / 4)
            note('arp', t, m - (12 if full else 0), BEAT / 4, 'arp', 0.5, S.pluck(m - (12 if full else 0), 0.24, bright=3000 if not full else 4200, dark=600), 0.10 if full else 0.09,
                 0.5 * (1 if s % 2 else -1))

# the theme through B and C
theme(4, 'keys', g=0.34, vel=0.66)
theme(8, 'keys', octave=0, g=0.26, vel=0.6)
theme(8, 'string', octave=0, g=0.24, vel=0.6)
theme(12, 'lead', octave=0, g=0.20, vel=0.8)
theme(16, 'lead', octave=0, g=0.21, vel=0.85)
theme(16, 'string', octave=1, g=0.14, vel=0.55)

# bells answer the theme in C, in the gaps
ANSWER = [(1.0, 88), (1.5, 85), (2.5, 81), (5.0, 92), (5.5, 88), (9.0, 90), (9.5, 88), (10.5, 85), (13.0, 81), (14.0, 85)]
for base in (12, 16):
    for b, m in ANSWER:
        t = bt(base, b)
        note('bell', t, m, 0.8, 'bell', 0.5, S.bell(m, 1.6, 3.5, 1.4, 0.7), 0.07, 0.4)

# drums: a soft pulse arrives in B, a heartbeat in C
K = S.kit('808')
for bar in range(8, 20):
    full = bar >= 12
    for b in ((0, 2) if not full else (0, 1, 2, 3)):
        t = bt(bar, b); kicks.append(t)
        buses['drums'].add(t, S.hp(K['kick'], 38), 0.50 if full else 0.38)
    if full:
        for b in (1, 3):
            t = bt(bar, b); snares.append(t)
            buses['drums'].add(t, K['rim'] if bar < 16 else K['clap'], 0.16)
        for s in range(8):
            buses['drums'].add(bt(bar, s / 2 + 0.25), K['shaker'], 0.07 + 0.04 * (s % 2))
        for s in range(16):
            buses['drums'].add(bt(bar, s / 4), K['hat'], [0.09, 0.035, 0.06, 0.035][s % 4])
buses['air'].add(bt(11, 2), S.riser(2 * BEAT + 0.05, 300, 7000), 0.08)
for bar in range(12, 20):
    n = S.smp(BAR); tq = np.arange(n) / S.SR
    breath = S.bp(S.noise(n), 7000, 15000) * (0.4 + 0.6 * np.sin(np.pi * tq / BAR) ** 2)
    buses['air'].add(bt(bar), S.autopan(breath, -0.5, 0.5), 0.035)
buses['air'].add(bt(12), S.impact(2.0), 0.18)
buses['air'].add(bt(19, 2), S.whoosh(2 * BEAT, 6000, 300), 0.06)

# ---------------------------------------------------------------- D: back to the theme alone, and home (bars 20-23)
theme(20, 'keys', g=0.34, vel=0.58, transpose_last=69)
for bar in range(20, 24):
    c = CHORDS[bar]
    v = T.progression([c], octave=3)[0]
    fade = 1 - (bar - 20) * 0.18
    buses['pad'].add(bt(bar), S.soft_pad(v, BAR + (3.5 if bar == 23 else 0.2), a=0.8, r=3.0 if bar == 23 else 0.9, bright=1100), 0.24 * fade)
    for m in v:
        events.append({'t': round(bt(bar), 4), 'd': round(BAR + (3 if bar == 23 else 0), 4), 'm': m, 'i': 'pad', 'v': 0.35 * fade})
for k, m in enumerate([57, 64, 69, 73, 76, 81]):
    t = bt(23, 2) + k * 0.12
    note('bell', t, m, 2.5, 'bell', 0.4, S.bell(m, 3.0, 2.0, 0.8, 1.2), 0.05, (k - 2.5) / 4)

# ---------------------------------------------------------------- mix
dk = S.ducker(kicks, DUR, 0.35, 0.18)
keys = S.eq(S.hp(buses['keys'].out(), 140), [('peak', 350, -2.5, 1.0)])
pad = S.eq(S.hp(buses['pad'].out(), 220, 2), [('peak', 420, -4.0, 0.8), ('peak', 900, -1.5, 1.0)]) * S.ducker(kicks, DUR, 0.25, 0.25)
bass = buses['bass'].out() * S.ducker(kicks, DUR, 0.5, 0.12)
arp = buses['arp'].out() * dk
bell = buses['bell'].out()
lead = S.chorus(buses['lead'].out(), 0.4, 4.0, 0.35)
drums = buses['drums'].out()
air = buses['air'].out()
HALL = S.hall(5.5, 1.9, 0.04, 250, 9500)
PLATE = S.plate(2.6, 0.7)
arp = arp + S.pingpong(arp, 3 * BEAT / 4, 0.4) * 0.4
lead = lead + S.pingpong(lead, 3 * BEAT / 4, 0.3) * 0.25
send_hall = S.hp(keys * 0.55 + bell * 0.8 + pad * 0.10 + arp * 0.35 + lead * 0.4, 300)
send_plate = drums * 0.12 + arp * 0.2
music = keys + pad + bass + arp + bell + lead + drums + air + S.reverb(send_hall, HALL, 0.6) + S.reverb(send_plate, PLATE, 0.35)
# the loudness arc: the intro is a whisper, B leans in, C is full, D lets go (dB per bar, smoothed)
ARC = {0: -9, 2: -8, 4: -5, 8: -3, 12: 0, 16: 0.5, 19: 0, 20: -6, 23: -8}
bars_t = [bt(b) for b in sorted(ARC)]
arc_db = [ARC[b] for b in sorted(ARC)]
tt_ = np.arange(music.shape[1]) / S.SR
g = 10 ** (np.interp(tt_, bars_t, arc_db) / 20)
g = np.convolve(g, np.ones(S.smp(0.5)) / S.smp(0.5), mode='same')
music = music * g
music = S.glue(music / (np.max(np.abs(music)) + 1e-9) * 0.5, -16, 1.5)
master = S.master(music, lufs=-15.0, tone=[('lowshelf', 60, -2.0, 0.7), ('peak', 400, -2.0, 0.8), ('peak', 3200, 1.5, 0.8), ('highshelf', 7500, 5.0, 0.7)], fade=3.0)

if __name__ == '__main__':
    S.write(str(HERE / 'mix.wav'), master)
    events.sort(key=lambda e: e['t'])
    chords = [{'t': round(bt(b), 4), 'd': round(BAR, 4), 'name': c, 'root': T.parse_chord(c)[0]} for b, c in CHORDS.items() if c]
    sections = [{'t': bt(0), 'name': 'A'}, {'t': bt(4), 'name': 'B'}, {'t': bt(12), 'name': 'C'}, {'t': bt(20), 'name': 'D'}]
    data = {'bpm': BPM, 't0': T0, 'bar': BAR, 'dur': DUR, 'events': events, 'chords': chords, 'kicks': kicks, 'snares': snares, 'sections': sections}
    (HERE / 'score.js').write_text('window.SCORE = ' + json.dumps(data) + ';\n')
    print(f'{len(events)} notes, {len(kicks)} kicks, {DUR:.1f} s')
