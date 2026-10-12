"""moods: scene-by-scene music that changes with the story instead of one bed all the way through.

Each scene gets a mood (what the music is doing) and an energy (how hard). A mood sets its own tempo, mode,
chord progression and band; energy turns layers on and up. Scenes join with a hit, a swell or a cut.

    from studio.instruments.moods import Score
    sc = Score(dur, key='E')
    sc.scene(0.0, 34.0, 'mystery', 0.3)
    sc.scene(34.0, 61.0, 'tension', 0.6, enter='swell')
    sc.scene(61.0, 95.0, 'action', 0.9, enter='hit')
    sc.write('music.wav')                     # mixed and mastered at -20 LUFS, ready for mix.py

Moods: wonder, calm, mystery, dread, tension, action, march, grief, triumph, jaunty. See MOODS below.
Check the result with `python3 studio/senses/pacing.py music.wav moods.json` (each scene should sound like its mood,
and neighbours with different moods should sound different), then listen.py as always.
"""
from __future__ import annotations

import gc, json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from studio.instruments import synth as S
from studio.instruments import theory as T

# General MIDI programs in the GeneralUser soundfont
PIANO, CELESTA, MUSICBOX, STRINGS, SLOWSTR, TREM, PIZZ, HARP, TIMP, CHOIR = 0, 8, 10, 48, 49, 44, 45, 46, 47, 52
CELLO, BASS, TRUMPET, TROMBONE, HORN, BRASS, OBOE, CLARINET, FLUTE, PICCOLO = 42, 43, 56, 57, 60, 61, 68, 71, 73, 72

MOODS = {
    #            tempo  mode              progression (roman, one chord a bar)   what it's for
    'wonder':   (76,  'major',           'I V vi IV',            'discovery, scale, a first look at a place'),
    'calm':     (70,  'major',           'I IV I V',             'setting a scene, ordinary life before things go wrong'),
    'mystery':  (80,  'minor',           'i VI i VII',           'questions, a puzzle, something hidden'),
    'dread':    (60,  'minor',           'i i bII i',            'something bad is coming; night, waiting, a predator'),
    'tension':  (96,  'minor',           'i i VI v',             'pressure building: a plan, a countdown, a chase starting'),
    'action':   (132, 'minor',           'i VI III VII',         'the fight, the run, the crash itself'),
    'march':    (112, 'minor',           'i iv v i',             'armies moving, a column, a parade'),
    'grief':    (58,  'minor',           'i iv VI v',            'loss, aftermath, the cost'),
    'triumph':  (100, 'major',           'I IV V I',             'the win, the rescue, the last-minute save'),
    'jaunty':   (116, 'major',           'I vi ii V',            'money rolling in, a con, good times that will not last'),
}


class Score:
    def __init__(self, dur, key='E', seed=7, tail=6.0):
        self.dur, self.key = dur, key
        self.mus, self.low, self.perc = S.Bus(dur, tail), S.Bus(dur, tail), S.Bus(dur, tail)
        self.rng = np.random.default_rng(seed); S.seed(seed)
        self._cache = {}; self.plan = []

    # ---------------------------------------------------------------- notes
    def inst(self, prog, m, dur, vel):
        m, vel = int(np.clip(m, 21, 108)), int(np.clip(vel, 1, 127))
        k = (prog, m, round(dur, 2), vel)
        if dur > 5: return S.sfhit(m, program=prog, bank=0, channel=0, vel=vel, dur=dur + 0.6)
        if k not in self._cache: self._cache[k] = S.sfhit(m, program=prog, bank=0, channel=0, vel=vel, dur=dur + 0.6)
        return self._cache[k]

    def note(self, prog, m, t, dur, vel, g=1.0, pan=0.0, swell=0.0):
        y = self.inst(prog, m, dur, vel)
        if swell > 0: y = y * np.minimum(1, np.arange(y.shape[1]) / (swell * S.SR)) ** 1.5
        (self.low if m < 50 else self.mus).add(t, y, g, pan)

    def chords(self, mood, n_bars, key):
        bpm, mode, prog, _ = MOODS[mood]
        romans = prog.split()
        out = []
        for b in range(n_bars):
            r = romans[b % len(romans)]
            out.append(self._roman(r, key, mode))
        return out

    def _roman(self, r, key, mode):
        # minor-key romans (i, iv, v, VI, III, VII, bII) and major-key romans, built on the key's scale
        flat = r.startswith('b'); r0 = r.lstrip('b')
        deg = {'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'VI': 5, 'VII': 6}[r0.upper()]
        sc = T.SCALES['minor' if mode == 'minor' else 'major']
        root = T.PC[key] + sc[deg] - (1 if flat else 0)
        minor = r0.islower()
        if mode == 'minor' and r0 == 'v': minor = True
        triad = [0, 3, 7] if minor else [0, 4, 7]
        base = 40 + (root - 4) % 12                                   # around E2..D#3
        return [base + i for i in triad]

    def scale(self, mood, key):
        mode = MOODS[mood][1]; sc = T.SCALES['minor' if mode == 'minor' else 'major']
        return [T.PC[key] + s for s in sc]

    # ---------------------------------------------------------------- layers (each fills t0..t1 on the mood's own beat)
    def _grid(self, t0, t1, step):
        return np.arange(t0, t1 - 0.05, step)

    def pad(self, t0, t1, chords, bar, vel, prog=SLOWSTR, g=1.0, octave=12, swell=1.0):
        for k, t in enumerate(self._grid(t0, t1, bar)):
            ch = chords[k % len(chords)]; d = min(bar + 0.3, t1 - t + 0.4)
            for i, m in enumerate(ch + [ch[0] + 12]): self.note(prog, m + octave, t, d, vel, g * 0.9, (-0.3, 0.2, -0.1, 0.3)[i % 4], swell)

    def bass(self, t0, t1, chords, bar, vel, prog=CELLO, g=1.0, per_bar=1):
        step = bar / per_bar
        for k, t in enumerate(self._grid(t0, t1, step)):
            ch = chords[int(k // per_bar) % len(chords)]; self.note(prog, ch[0] - 12 + (0, 7)[k % 2 if per_bar > 1 else 0], t, min(step, t1 - t) + 0.2, vel, g * 1.1, 0.1)

    def drone(self, t0, t1, root, vel, g=0.8):
        self.note(SLOWSTR, root, t0, t1 - t0 + 0.5, vel, g, -0.1, swell=2.5); self.note(SLOWSTR, root + 7, t0, t1 - t0 + 0.5, vel - 6, g * 0.8, 0.2, swell=3.0)

    def tremolo(self, t0, t1, chords, bar, vel, g=0.8):
        for k, t in enumerate(self._grid(t0, t1, bar)):
            ch = chords[k % len(chords)]
            for i, m in enumerate(ch): self.note(TREM, m + 12, t, min(bar, t1 - t) + 0.2, vel, g * 0.8, (-0.4, 0.0, 0.4)[i % 3], swell=0.5)

    def ostinato(self, t0, t1, chords, beat, vel, prog=PIZZ, sub=2, pattern=(0, 0, 2, 0, 1, 0, 2, 1), g=1.0, octave=12):
        step = beat / sub; bar_steps = int(round(4 * sub))
        for k, t in enumerate(self._grid(t0, t1, step)):
            ch = chords[(k // bar_steps) % len(chords)]; m = ch[pattern[k % len(pattern)] % 3] + octave
            acc = 10 if k % sub == 0 else 0
            self.note(prog, m, t, step * 0.9, vel + acc + self.rng.integers(-3, 4), g, -0.15 + 0.3 * ((k // 2) % 2))

    def arp(self, t0, t1, chords, beat, vel, prog=HARP, sub=2, g=1.0, octave=24):
        step = beat / sub; bar_steps = int(round(4 * sub))
        for k, t in enumerate(self._grid(t0, t1, step)):
            ch = chords[(k // bar_steps) % len(chords)]; seq = ch + [ch[0] + 12, ch[2] + 12, ch[1] + 12]
            self.note(prog, seq[k % len(seq)] + octave, t, step * 3, vel - 4 * (k % 2), g, 0.25 - 0.1 * (k % 3))

    def stride(self, t0, t1, chords, beat, vel, g=1.0):
        for k, t in enumerate(self._grid(t0, t1, beat)):
            ch = chords[(k // 4) % len(chords)]
            if k % 2 == 0: self.note(PIANO, ch[0] - (12 if (k // 2) % 2 == 0 else 5), t, beat, vel, g * 1.4, -0.2)
            else:
                for m in ch: self.note(PIANO, m + 12, t, beat * 0.6, vel - 12, g * 0.9, 0.15)

    def melody(self, t0, t1, mood, key, beat, vel, prog, g=1.0, octave=72, rhythm=(2, 1, 1, 2, 2), rest=0.15):
        sc = self.scale(mood, key); deg = 0; t = t0
        k = 0
        while t < t1 - beat:
            d = rhythm[k % len(rhythm)] * beat; k += 1
            if self.rng.random() > rest:
                m = octave - 12 + (deg // 7) * 12 + sc[deg % 7]
                while m < octave - 12: m += 12
                self.note(prog, m, t, min(d * 1.1, t1 - t), vel + self.rng.integers(-4, 5), g, -0.05)
            step = self.rng.choice([-2, -1, -1, 1, 1, 2, 3, -3])
            deg = int(np.clip(deg + step, -3, 9)); t += d

    def timp(self, t0, t1, root, beat, vel, every=4, g=1.0, roll_end=False):
        for k, t in enumerate(self._grid(t0, t1, beat * every)): self.low.add(t, self.inst(TIMP, root, 1.2, vel), 1.2 * g)
        if roll_end:
            for i, t in enumerate(np.arange(t1 - beat * 2, t1, beat / 6)): self.low.add(t, self.inst(TIMP, root, 0.5, int(vel * (0.5 + 0.5 * i / 12))), 0.8 * g)

    def snare(self, t, g=1.0):
        n = S.smp(0.22); x = np.arange(n) / S.SR
        self.perc.add(t, S.bp(S.noise(n), 900, 6000) * np.exp(-x / 0.05) + np.sin(2 * np.pi * 190 * x) * np.exp(-x / 0.04) * 0.6, 0.06 * g, -0.15)

    def kick(self, t, g=1.0):
        self.perc.add(t, S.kick(48, 100, 0.25, 0.2, 1.2), 0.25 * g)

    def tick(self, t, hi=True, g=1.0):
        n = S.smp(0.09); x = np.arange(n) / S.SR
        self.perc.add(t, S.bp(S.noise(n), 1800, 5200) * np.exp(-x / 0.006) * 0.8 + np.sin(2 * np.pi * (1250 if hi else 930) * x) * np.exp(-x / 0.018) * 0.6, 0.05 * g, -0.2)

    # ---------------------------------------------------------------- moods
    def scene(self, t0, t1, mood, energy=0.5, key=None, enter='swell', end='ring'):
        """Write one scene's music. enter: 'swell' (strings fade up), 'hit' (timpani and brass on the downbeat),
        'cut' (straight in), 'soft' (a single held note first). energy 0..1 adds layers and weight."""
        key = key or self.key; bpm = MOODS[mood][0]; beat = 60.0 / bpm; bar = beat * 4
        nb = int(np.ceil((t1 - t0) / bar)) + 1; ch = self.chords(mood, nb, key); e = float(np.clip(energy, 0, 1))
        v = lambda lo, hi: int(lo + (hi - lo) * e)
        root = ch[0][0]
        self.plan.append({'t0': round(t0, 2), 't1': round(t1, 2), 'mood': mood, 'energy': e, 'bpm': bpm, 'key': key})
        if enter == 'hit':
            self.low.add(t0 - 0.03, self.inst(TIMP, root - 12 if root > 40 else root, 2.5, 110), 1.6)
            for m in ch[0]: self.note(BRASS, m + 12, t0, 1.6, 96, 0.9)
        elif enter == 'swell' and t0 > 1.5:
            self.mus.add(t0 - 1.5, S.riser(1.5, 400, 4000) * 0.5, 0.05)
        if mood == 'wonder':
            self.pad(t0, t1, ch, bar, v(46, 66)); self.arp(t0, t1, ch, beat, v(52, 72))
            if e > 0.4: self.melody(t0 + bar, t1, mood, key, beat, v(56, 76), CELESTA, 1.1, 84, (2, 2, 4), 0.25)
            if e > 0.7: self.bass(t0, t1, ch, bar, v(56, 70), CELLO)
        elif mood == 'calm':
            self.pad(t0, t1, ch, bar, v(40, 56), g=0.8); self.arp(t0, t1, ch, beat, v(46, 62), PIANO, sub=1, g=1.4, octave=12)
            if e > 0.5: self.melody(t0 + bar * 2, t1, mood, key, beat, v(50, 66), FLUTE, 0.9, 79, (2, 1, 1, 4), 0.3)
        elif mood == 'mystery':
            self.drone(t0, t1, root + 12, v(40, 54))
            for t in self._grid(t0 + beat, t1, beat * self.rng.choice([1.5, 2, 3])):
                if self.rng.random() < 0.6: self.note(MUSICBOX, self.scale(mood, key)[self.rng.integers(0, 7)] + 72, t, 2.0, v(50, 70), 1.1, self.rng.uniform(-0.4, 0.4))
            if e > 0.4: self.tremolo(t0, t1, ch, bar, v(34, 50), 0.6)
            if e > 0.6: self.bass(t0, t1, ch, bar, v(50, 64), PIZZ, per_bar=2)
        elif mood == 'dread':
            self.drone(t0, t1, root, v(46, 60), 1.0)
            for t in self._grid(t0 + bar, t1, bar * 2): self.low.add(t, self.inst(TIMP, root, 2.0, v(60, 90)), 1.0)
            for t in self._grid(t0 + bar * 1.5, t1, bar * 2):                             # a semitone rub, low
                self.note(SLOWSTR, root + 13, t, bar, v(34, 52), 0.7, 0.3, swell=1.5)
            if e > 0.5:
                for t in self._grid(t0, t1, beat): self.low.add(t, self.inst(TIMP, root, 0.6, v(40, 70)), 0.5); self.low.add(t + beat * 0.28, self.inst(TIMP, root, 0.6, v(30, 55)), 0.35)
        elif mood == 'tension':
            self.ostinato(t0, t1, ch, beat, v(58, 78), PIZZ, 2, (0, 0, 0, 0, 0, 0, 1, 0), 1.0, 0)
            self.tremolo(t0, t1, ch, bar, v(40, 64), 0.7 + 0.3 * e)
            if e > 0.45: self.timp(t0, t1, root, beat, v(60, 86), every=1, g=0.6)
            if e > 0.65:
                for k, t in enumerate(self._grid(t0, t1, beat)): self.tick(t, k % 2 == 0, 0.9)
            if e > 0.8: self.ostinato(t0, t1, ch, beat, v(56, 72), STRINGS, 4, (0, 1, 2, 1), 0.7, 12)
        elif mood == 'action':
            self.ostinato(t0, t1, ch, beat, v(70, 100), STRINGS, 4, (0, 0, 2, 0, 1, 0, 2, 1), 0.9, 12)
            self.bass(t0, t1, ch, bar, v(70, 96), BASS, per_bar=8)
            for k, t in enumerate(self._grid(t0, t1, beat)):
                if k % 4 in (0, 2): self.low.add(t, self.inst(TIMP, root, 0.8, v(80, 110)), 1.0); self.kick(t, 0.8 + 0.4 * e)
                if k % 4 in (1, 3) and e > 0.5: self.snare(t, 0.6 + 0.6 * e)
            for t in self._grid(t0, t1, bar):
                for m in self.chords(mood, 1, key)[0]: self.note(BRASS, m + 12, t, beat * 0.9, v(80, 110), 0.8)
            if e > 0.7: self.melody(t0 + bar, t1, mood, key, beat, v(80, 104), HORN, 1.1, 64, (1, 1, 2), 0.1)
        elif mood == 'march':
            for k, t in enumerate(self._grid(t0, t1, beat)):
                self.snare(t, 0.7 + 0.5 * e)
                if k % 4 == 3: self.snare(t + beat * 0.5, 0.5); self.snare(t + beat * 0.75, 0.5)
                if k % 2 == 0: self.kick(t, 0.7)
            self.bass(t0, t1, ch, bar, v(66, 92), TROMBONE, per_bar=4)
            if e > 0.4: self.melody(t0 + bar, t1, mood, key, beat, v(66, 90), PICCOLO, 1.0, 79, (1, 1, 2), 0.15)
            if e > 0.6: self.pad(t0, t1, ch, bar, v(50, 66), HORN, 0.8, 12, 0.3)
        elif mood == 'grief':
            self.pad(t0, t1, ch, bar, v(36, 50), SLOWSTR, 0.8, 12, 2.0)
            self.melody(t0 + beat, t1, mood, key, beat, v(58, 76), CELLO, 1.3, 52, (4, 2, 2, 8), 0.1)
            for t in self._grid(t0, t1, bar):
                for m in self.chords(mood, 1, key)[0]: self.note(PIANO, m + 24, t + 0.03 * self.rng.random(), bar, v(40, 54), 1.0, 0.1)
        elif mood == 'triumph':
            self.pad(t0, t1, ch, bar, v(60, 84), STRINGS, 1.0, 12, 0.6)
            self.bass(t0, t1, ch, bar, v(70, 96), CELLO, per_bar=4)
            self.melody(t0, t1, mood, key, beat, v(76, 104), HORN, 1.3, 67, (2, 1, 1, 4), 0.05)
            self.timp(t0, t1, root, beat, v(80, 110), every=4, g=1.0, roll_end=e > 0.6)
            if e > 0.6: self.arp(t0, t1, ch, beat, v(56, 76), HARP, 4, 0.8)
        elif mood == 'jaunty':
            self.stride(t0, t1, ch, beat, v(58, 78))
            self.bass(t0, t1, ch, bar, v(60, 80), PIZZ, per_bar=4)
            if e > 0.4: self.melody(t0 + bar, t1, mood, key, beat, v(60, 82), CLARINET, 1.0, 72, (1, 1, 1, 1, 2), 0.2)
        else:
            raise ValueError(f'unknown mood {mood!r}; choose from {", ".join(MOODS)}')
        return self

    # ---------------------------------------------------------------- out
    def mixdown(self, lufs=-20.0, fade_out=3.0):
        DN = S.smp(self.dur); tt = np.arange(DN) / S.SR
        fade = np.clip(tt / 0.5, 0, 1) * np.clip((self.dur - tt) / fade_out, 0, 1)
        lo = self.low.out(True); mu = self.mus.out(True); pe = self.perc.out(True)
        m = mu * 1.1 + lo * 0.85 + pe
        wet = S.reverb(mu * 0.6 + lo * 0.25 + pe * 0.2, S.hall(3.2, 1.2, 0.03, 220, 6500), 0.45)
        del lo, mu, pe; gc.collect()
        m = (m + wet)[:, :DN]; del wet; gc.collect()
        # the soundfont is dark and thick in the low mids; this is the curve the films settled on, a little brighter
        m = S.eq(m, [('lowshelf', 110, -5.0, 0.7), ('peak', 280, -5.5, 0.9), ('peak', 520, -4.0, 1.0), ('peak', 850, -2.5, 1.0), ('peak', 1500, 2.0, 0.8), ('peak', 3000, 5.0, 0.8), ('highshelf', 4500, 11.0, 0.7)])
        return S.master(m * fade, lufs=lufs, fade=0, ceiling=0.8)

    def write(self, path, plan_path=None, **kw):
        S.write(path, self.mixdown(**kw))
        if plan_path: json.dump(self.plan, open(plan_path, 'w'), indent=1)
        return self.plan
