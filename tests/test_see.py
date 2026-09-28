"""see.py, checked against pictures whose answers are known in advance."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'studio' / 'senses'))
import see  # noqa: E402

D = tempfile.mkdtemp()


def save(img, name):
    p = os.path.join(D, name + '.png'); img.save(p); return see.analyse(p)


def canvas(bg=(14, 18, 40), size=(600, 400)):
    im = Image.new('RGB', size, bg); return im, ImageDraw.Draw(im)


class See(unittest.TestCase):
    def test_single_focal_point_on_a_third(self):
        im, d = canvas()
        d.ellipse([400 - 30, 133 - 30, 400 + 30, 133 + 30], fill=(255, 150, 40))
        r = save(im, 'dot')
        x, y, _ = r['points'][0]
        self.assertAlmostEqual(x, 0.667, delta=0.06); self.assertAlmostEqual(y, 0.333, delta=0.08)
        self.assertGreater(r['focus'], 0.35)
        self.assertNotIn('no clear focal point', see.words(r))

    def test_noise_has_no_focal_point_and_is_busy(self):
        rng = np.random.default_rng(1)
        r = save(Image.fromarray(rng.integers(0, 255, (400, 600, 3), dtype=np.uint8)), 'noise')
        w = see.words(r)
        self.assertIn('busy', w)
        self.assertLess(r['focus'], 0.3)

    def test_grey_soup(self):
        rng = np.random.default_rng(2)
        im, d = canvas((120, 120, 120))
        for _ in range(40):
            x, y = rng.integers(0, 600), rng.integers(0, 400); g = int(rng.integers(105, 140))
            d.rectangle([x, y, x + 80, y + 50], fill=(g, g, g))
        self.assertIn('values are too close', see.words(save(im, 'soup')))

    def test_complementary(self):
        im, d = canvas((30, 70, 200)); d.rectangle([300, 0, 600, 400], fill=(240, 130, 20))
        self.assertEqual(save(im, 'comp')['scheme'], 'complementary')

    def test_triadic(self):
        im, d = canvas((220, 40, 40)); d.rectangle([200, 0, 400, 400], fill=(40, 190, 60)); d.rectangle([400, 0, 600, 400], fill=(50, 60, 230))
        self.assertEqual(save(im, 'tri')['scheme'], 'triadic')

    def test_analogous(self):
        im, d = canvas((200, 50, 30)); d.rectangle([200, 0, 400, 400], fill=(230, 120, 30)); d.rectangle([400, 0, 600, 400], fill=(235, 190, 40))
        self.assertIn(save(im, 'ana')['scheme'], ('analogous',))

    def test_left_heavy(self):
        im, d = canvas()
        for k in range(4):
            d.ellipse([30 + k * 25, 60 + k * 80, 110 + k * 25, 140 + k * 80], fill=(250, 240, 220))
        r = save(im, 'left')
        self.assertLess(r['balance'][0], 0.4)
        self.assertIn('heavy on the left', see.words(r))


if __name__ == '__main__':
    unittest.main()
