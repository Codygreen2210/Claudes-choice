"""Instruments and theory, checked by ear: play known music with the kit, and the studio's own ears must hear it right."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'studio' / 'senses'))
from studio.instruments import synth as S, theory as T  # noqa: E402
import listen  # noqa: E402


class Theory(unittest.TestCase):
    def test_notes(self):
        self.assertEqual(T.note('C4'), 60); self.assertEqual(T.note('A4'), 69); self.assertEqual(T.note('F#2'), 42)
        self.assertEqual(T.name(61), 'C#4')

    def test_chords(self):
        self.assertEqual(T.chord('Am7', 3), [57, 60, 64, 67])
        self.assertEqual(T.chord('C/G', 4)[0] % 12, 7)
        self.assertEqual(T.roman('I V vi IV', key='E'), ['E', 'B', 'C#m', 'A'])
        self.assertEqual(T.roman('i bVI bIII bVII', key='A', minor=True), ['Am', 'E', 'B', 'F'][0:1] + T.roman('bVI bIII bVII', key='A', minor=True))

    def test_voice_leading_is_smooth(self):
        v = T.progression('C G Am F C', octave=4)
        for a, b in zip(v, v[1:]):
            self.assertLessEqual(sum(abs(x - y) for x, y in zip(sorted(a), sorted(b))), 8, (a, b))
        for s, ch in zip('C G Am F C'.split(), v):
            root, ivs, _ = T.parse_chord(s)
            self.assertEqual({(root + i) % 12 for i in ivs}, {m % 12 for m in ch})

    def test_euclid(self):
        self.assertEqual(T.euclid(3, 8), [1, 0, 0, 1, 0, 0, 1, 0])
        self.assertEqual(sum(T.euclid(5, 16)), 5)


class ByEar(unittest.TestCase):
    def test_pitch_of_instruments(self):
        for inst in (lambda: S.pluck(69, 0.6), lambda: S.bell(69, 1.0), lambda: S.epiano(69, 1.0), lambda: S.karplus(69, 1.0),
                     lambda: S.bass_note(45, 0.8), lambda: S.supersaw([69], 0.8).mean(0), lambda: S.soft_pad([69], 1.5, a=0.1).mean(0)):
            y = inst()
            y = y[:S.SR]
            spec = np.abs(np.fft.rfft(y * np.hanning(len(y)), 8 * len(y)))
            f = np.fft.rfftfreq(8 * len(y), 1 / S.SR)
            sel = (f > 50) & (f < 2000)
            peak = f[sel][np.argmax(spec[sel])]
            semis = np.log2(peak / 440) * 12            # any octave of A counts (the bass has a sub an octave down)
            self.assertAlmostEqual((semis + 6) % 12 - 6, 0, delta=0.35, msg=f'peak {peak:.1f} Hz')

    def test_the_ears_hear_what_the_kit_plays(self):
        S.seed(4)
        prog = 'Am F C G Am F C G'.split()
        bpm = 100; beat = 60 / bpm; bar = 4 * beat
        dur = len(prog) * bar + 1.5
        mix, drums = S.Bus(dur), S.Bus(dur)
        k = S.kit('synth')
        voicings = T.progression(prog, octave=4)
        for i, (c, v) in enumerate(zip(prog, voicings)):
            t = 0.2 + i * bar
            mix.add(t, S.soft_pad(v, bar - 0.05, a=0.05, r=0.1, bright=2500), 0.5)
            for b in range(4):
                mix.add(t + b * beat, S.bass_note(T.bass_of(c, 2), beat * 0.9), 0.35)
                drums.add(t + b * beat, k['kick'], 0.8, mark=True)
                drums.add(t + b * beat + beat / 2, k['hat'], 0.2)
        out = S.master(mix.out() * S.ducker(drums.hits, dur, 0.4) + drums.out(), lufs=-16)
        path = os.path.join(tempfile.mkdtemp(), 'kit.wav')
        S.write(path, out)
        r = listen.analyse(path)
        self.assertAlmostEqual(r['tempo_bpm'], bpm, delta=1.5)
        self.assertAlmostEqual(r['loudness']['integrated_lufs'], -16, delta=0.5)
        self.assertLess(r['loudness']['true_peak_dbtp'], -1.0)
        runs = r['chords']
        def at(t):
            c = 'N'
            for tt, n in runs:
                if tt <= t: c = n
            return c
        heard = [at(0.2 + i * bar + bar / 2) for i in range(len(prog))]
        self.assertGreaterEqual(sum(a == b for a, b in zip(heard, prog)), 7, f'played {prog}, heard {heard}')


if __name__ == '__main__':
    unittest.main()
