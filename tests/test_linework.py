"""linework.py on drawings with known answers: tiled vs hand-varied marks, clean vs rough lines, focus."""
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'studio' / 'senses'))
import linework as lw  # noqa: E402


def canvas(n=480):
    return np.full((n, n), 0.95)


def stamp(img, cx, cy, r, w=1.6):
    """a U-shaped scale mark"""
    y, x = np.ogrid[:img.shape[0], :img.shape[1]]
    d = np.hypot(x - cx, y - cy)
    ring = (np.abs(d - r) < w) & (x >= cx)
    img[ring] = 0.2


def scales(jitter, seed=1):
    img, R = canvas(), np.random.default_rng(seed)
    for gy in range(20, 460, 18):
        for gx in range(20, 460, 18):
            j = jitter * R.normal(size=3)
            stamp(img, gx + 4 * j[0], gy + 4 * j[1], 7 * (1 + 0.2 * j[2]))
    return img


class Linework(unittest.TestCase):
    def test_exact_tiling_repeats_more_than_varied_marks(self):
        tiled = lw.measure(scales(0))['repetition']
        varied = lw.measure(scales(1))['repetition']
        self.assertGreater(tiled, varied * 1.5, (tiled, varied))

    def test_a_big_curve_is_not_repetition(self):
        """the overall shape must not count as a repeating mark (the bug that hid the serpent's real score)"""
        a = scales(1)
        b = a.copy()
        y, x = np.ogrid[:480, :480]
        b[np.abs(np.hypot(x - 240, y - 240) - 180) < 12] = 0.1        # add one huge ring across the picture
        ra, rb = lw.measure(a)['repetition'], lw.measure(b)['repetition']
        self.assertLess(abs(ra - rb) / ra, 0.35, (ra, rb))

    def test_rough_lines_score_rougher(self):
        clean = canvas()
        clean[200:212, 40:440] = 0.15
        R = np.random.default_rng(3)
        rough = clean.copy()
        edge = (ndi.binary_dilation(clean < 0.5, iterations=2) ^ ndi.binary_erosion(clean < 0.5, iterations=2))
        rough[edge & (R.random(clean.shape) < 0.5)] = 0.95
        rough[edge & (R.random(clean.shape) < 0.3)] = 0.15
        self.assertGreater(lw.measure(rough)['roughness'], lw.measure(clean)['roughness'] + 0.1)

    def test_detail_piled_in_one_spot_is_more_focused(self):
        even, focused = scales(1), canvas()
        focused[:] = 0.95
        sub = scales(1)[:160, :160]
        focused[40:200, 40:200] = sub
        focused[300:302, 40:440] = 0.2                                # something elsewhere, so the box is the same
        self.assertGreater(lw.measure(focused)['focus_gini'], lw.measure(even)['focus_gini'] + 0.2)


if __name__ == '__main__':
    unittest.main()
