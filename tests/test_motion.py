"""motion.py, checked against an animation whose faults are known in advance (tests/fixtures/motion.html)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'studio' / 'senses'))
import motion  # noqa: E402


class Motion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = motion.analyse(ROOT / 'tests' / 'fixtures' / 'motion.html', 0, 3, 60, (1080, 1080), tempfile.mkdtemp())
        cls.w = motion.words(cls.r)

    def m(self, name):
        return self.r['things'][name]['moves'][0]

    def test_robot_is_mechanical(self):
        m = self.m('robot')
        self.assertTrue(m['linear']); self.assertGreater(m['jolt'], 0.6); self.assertGreater(m['wall'], 0.6)
        self.assertIn('robot at 0.50s moves like a machine', self.w)

    def test_eased_is_clean_and_arcs(self):
        m = self.m('eased')
        self.assertLess(m['jolt'], 0.35); self.assertLess(m['wall'], 0.35); self.assertGreater(m['arc'], 0.2)
        self.assertNotIn('eased at', self.w)

    def test_spring_overshoots_as_one_move(self):
        self.assertEqual(len(self.r['things']['spring']['moves']), 1)
        self.assertGreater(self.m('spring')['overshoot'], 0.1)

    def test_gentle_move_next_to_fast_ones_reads_as_eased(self):
        m = self.m('slow')
        self.assertLess(m['jolt'], 0.35, m); self.assertLess(m['wall'], 0.35, m)

    def test_held_drawings_read_as_one_move(self):
        v = self.r['things']['twos']
        self.assertEqual(v['hold'], 2)
        self.assertEqual(len(v['moves']), 1)
        self.assertLess(v['moves'][0]['jolt'], 0.35)

    def test_lockstep(self):
        self.assertTrue(any({a, b} == {'robot', 'twin'} for a, b, _ in self.r['lockstep']))
        self.assertFalse(any('eased' in (a, b) and 'twos' not in (a, b) for a, b, _ in self.r['lockstep']))


if __name__ == '__main__':
    unittest.main()
