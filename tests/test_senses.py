"""Tests for the studio's senses, built from material where every answer is known in advance:
a synthesized song with exact beat times, chords and loudness, and a video with cuts at exact moments,
a soundtrack hit on every cut, and a deliberately dangerous flashing section."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'studio' / 'senses'))
import listen  # noqa: E402
import look  # noqa: E402

SR = 44100
BPM = 120
T0 = 0.25                              # first beat
BEAT = 60 / BPM
PROG = ['C', 'G', 'Am', 'F', 'C', 'G', 'Am', 'F']
CHORD_NOTES = {'C': (48, [60, 64, 67]), 'G': (43, [59, 62, 67]), 'Am': (45, [57, 60, 64]), 'F': (41, [57, 60, 65])}


def tone(midi, n, harmonics=5):
    t = np.arange(n) / SR
    f = 440 * 2 ** ((midi - 69) / 12)
    y = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.2 for k in range(1, harmonics + 1))
    return y


def make_song(path, target_lufs=-20.0):
    dur = T0 + len(PROG) * 4 * BEAT + 1.0
    n = int(dur * SR)
    y = np.zeros(n)
    rng = np.random.default_rng(3)
    for bar, c in enumerate(PROG):
        root, triad = CHORD_NOTES[c]
        a = int((T0 + bar * 4 * BEAT) * SR)
        m = int(4 * BEAT * SR)
        env = np.minimum(1, np.arange(m) / (0.01 * SR)) * np.minimum(1, (m - np.arange(m)) / (0.02 * SR))
        seg = sum(tone(p, m) for p in triad) * 0.12 + tone(root, m, 3) * 0.2
        y[a:a + m] += seg * env
    for k in range(len(PROG) * 4):
        a = int((T0 + k * BEAT) * SR)
        m = int(0.15 * SR)
        t = np.arange(m) / SR
        kick = np.sin(2 * np.pi * np.cumsum(50 + 120 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.08)
        click = rng.standard_normal(m) * np.exp(-t / 0.004) * 0.3
        y[a:a + m] += (kick + click) * 0.9
    import pyloudnorm as pyln
    st = np.stack([y, y]).T
    meter = pyln.Meter(SR)
    st = pyln.normalize.loudness(st, meter.integrated_loudness(st), target_lufs)
    sf.write(path, st, SR)
    return [T0 + k * BEAT for k in range(len(PROG) * 4)]


class Listen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.path = os.path.join(cls.dir, 'known.wav')
        cls.true_beats = make_song(cls.path)
        cls.r = listen.analyse(cls.path)

    def test_tempo(self):
        self.assertAlmostEqual(self.r['tempo_bpm'], 120, delta=1.0)

    def test_beats_land_on_time(self):
        det = np.array(self.r['beats'])
        errs = [np.min(np.abs(det - b)) for b in self.true_beats]
        on_time = np.mean(np.array(errs) < 0.030)
        self.assertGreaterEqual(on_time, 0.9, f'beat errors (ms): {np.round(np.array(errs) * 1000)}')
        self.assertLess(abs(np.median([det[np.argmin(np.abs(det - b))] - b for b in self.true_beats])), 0.015, 'systematic timing offset')

    def test_chords_by_bar(self):
        bars = listen.chords_by_bar(self.r)
        firsts = [b.split()[0] for b in bars]
        # detected bars may start one beat off the true downbeat; compare the chord sounding mid-bar
        runs = self.r['chords']
        def at(t):
            c = 'N'
            for tt, name in runs:
                if tt <= t: c = name
            return c
        mids = [at(T0 + (i * 4 + 2) * BEAT) for i in range(len(PROG))]
        self.assertGreaterEqual(sum(a == b for a, b in zip(mids, PROG)), 7, f'heard {mids}, played {PROG}')

    def test_key(self):
        self.assertIn(self.r['key'], ('C major', 'A minor'))

    def test_loudness(self):
        self.assertAlmostEqual(self.r['loudness']['integrated_lufs'], -20.0, delta=0.3)


def make_video(path, fps=30):
    """Colour cards with cuts at known frames, a flashing section, and a click on every cut."""
    import cv2
    W, H = 180, 320
    cuts = [30, 75, 120]                      # 1.0 s, 2.5 s, 4.0 s
    colours = [(40, 40, 200), (60, 180, 60), (200, 120, 30), (180, 60, 180)]
    n = 7 * fps
    tmp = path + '.silent.mp4'
    vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*'mp4v'), fps, (W, H))
    for i in range(n):
        shot = sum(i >= c for c in cuts)
        fr = np.full((H, W, 3), colours[shot], np.uint8)
        cv2.circle(fr, (int(20 + (i * 3) % (W - 40)), H // 2), 14, (255, 255, 255), -1)   # a moving dot
        if 5 * fps <= i < 6 * fps:            # 5 to 6 s: full-frame black/white every 2 frames (7.5 flashes/s)
            fr[:] = 255 if (i // 2) % 2 else 0
        vw.write(fr)
    vw.release()
    a = np.zeros(int(7 * SR))
    for c in cuts:
        k = int(c / fps * SR)
        t = np.arange(int(0.1 * SR)) / SR
        a[k:k + len(t)] += np.sin(2 * np.pi * 80 * t) * np.exp(-t / 0.03) + np.random.default_rng(c).standard_normal(len(t)) * np.exp(-t / 0.003) * 0.4
    wav = path + '.wav'
    sf.write(wav, np.stack([a, a]).T * 0.5, SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-i', wav, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', path], check=True)
    return [c / fps for c in cuts]


class Look(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.path = os.path.join(cls.dir, 'known.mp4')
        cls.true_cuts = make_video(cls.path)
        cls.r = look.analyse(cls.path)

    def test_finds_the_cuts(self):
        found = [c / self.r['fps'] for c in self.r['cuts']]
        for t in self.true_cuts:
            self.assertTrue(any(abs(f - t) <= 1.5 / self.r['fps'] for f in found), f'missed cut at {t}s; found {found}')

    def test_flags_dangerous_flashing(self):
        self.assertGreater(self.r['flash_worst'], 3)
        self.assertAlmostEqual(self.r['flash_at'], 5.0, delta=1.0)
        self.assertIn('FLASHING', look.words(self.r))

    def test_cuts_sync_with_sound(self):
        s = self.r['sync']
        self.assertIsNotNone(s)
        # only the three real cuts carry a click; flash transitions may also register as cuts, so check the real ones
        self.assertLess(abs(s['median_offset_ms']), 40, s)


if __name__ == '__main__':
    unittest.main()


class Melody(unittest.TestCase):
    """Held-out check for melody hearing: instruments and a key it was never tuned on."""
    def test_hears_melodies_it_was_not_tuned_on(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from studio.instruments import synth as S, theory as T
        import random
        total = right = 0
        for inst_name, inst, seed in (('pluck', lambda m, d: S.pluck(m, d + 0.2), 5), ('bell', lambda m, d: S.bell(m, d + 0.6), 6),
                                      ('karplus', lambda m, d: S.karplus(m, d + 0.5), 7)):
            rnd = random.Random(seed)
            sc = T.scale('D', 'dorian', 4, 2)
            t, ev = 0.3, []
            while t < 9:
                d = rnd.choice([0.25, 0.5, 0.5, 0.75])
                ev.append((t, rnd.choice(sc[:12]), d)); t += d
            b = S.Bus(11)
            for tt_, m, d in ev:
                b.add(tt_, inst(m, d), 0.4)
            b.add(0.0, S.soft_pad(T.chord('Dm9', 3), 10, a=0.5, bright=1500), 0.25)
            path = os.path.join(tempfile.mkdtemp(), f'{inst_name}.wav')
            S.write(path, S.master(b.out(), lufs=-18))
            heard = listen.analyse(path)['melody']
            for tt_, m, d in ev:
                c = [hm for a, bb, hm in heard if abs(a - tt_) < 0.06]
                right += bool(c and c[0] == m); total += 1
        self.assertGreaterEqual(right / total, 0.75, f'{right}/{total}')
        print(f'\n  held-out melody accuracy: {right}/{total} = {right / total:.0%}')
