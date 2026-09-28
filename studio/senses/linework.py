#!/usr/bin/env python3
"""linework: read a drawing the way a drawing teacher does, and compare it with a reference.

    python3 studio/senses/linework.py drawing.png [--ref reference.png] [--crop x0,y0,x1,y1] [--ref-crop ...] [--out dir]

see.py judges a picture's composition. This judges its drawing: the things that make line work look alive
rather than mechanical.

  focus       Artists pile detail and contrast where they want you to look and let the rest go loose. This maps
              edge detail over a grid and measures how unevenly it is spread (a Gini coefficient: 0 = the same
              everywhere, 1 = all in one spot), how much of it sits in the busiest tenth of the picture, and where.
  line weight Real lines swell and thin. This finds the drawn lines, measures their width all along their length,
              and reports how much it varies (coefficient of variation, and the ratio of thick to thin).
  values      The range from the lightest light to the darkest dark, and how many of five value bands are used.
  grain       Graphite and paper leave texture in the tones. This measures fine texture inside shaded areas.
  repetition  Hand-drawn marks are never quite the same twice; machine-tiled ones are. This looks for strong
              periodic peaks in the detail's spectrum: high means a pattern repeating exactly.
  roughness   A hand line's edge wanders a little; a vector line's edge is perfectly smooth. This compares the
              edge length of the drawn lines with that of a smoothed copy.
  edges       Artists lose and find edges: some crisp, some soft. This measures how much edge sharpness varies.

With --ref it prints the same numbers for the reference and says which way to move. The reference is only
measured, never copied: nothing from it is traced or reused.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize

GRID = 12


def load(path, crop=None):
    im = Image.open(path).convert('RGB')
    if crop:
        im = im.crop(tuple(int(v) for v in crop.split(',')))
    a = np.asarray(im, float) / 255.0
    # perceptual lightness (sRGB is already roughly perceptual; weight channels like luma)
    return a @ np.array([0.2126, 0.7152, 0.0722])


def content_box(L, paper):
    ink = L < paper - 0.08
    ys, xs = np.nonzero(ink)
    if len(xs) < 50:
        return 0, 0, L.shape[1], L.shape[0]
    x0, x1 = np.percentile(xs, [0.5, 99.5]).astype(int)
    y0, y1 = np.percentile(ys, [0.5, 99.5]).astype(int)
    return x0, y0, x1 + 1, y1 + 1


def gini(v):
    v = np.sort(np.asarray(v, float).ravel())
    if v.sum() <= 0:
        return 0.0
    n = len(v)
    return float((2 * np.arange(1, n + 1) - n - 1) @ v / (n * v.sum()))


def repetition_score(edges, lo=6, hi=60):
    """How peaky the detail's spectrum is, only at the size of marks (periods lo..hi px). The overall shape
    of the picture lives at much longer periods and must not count: a big S-curve is not a repeating mark."""
    e = edges - edges.mean()
    P = np.abs(np.fft.rfft2(e)) ** 2
    fy = np.fft.fftfreq(e.shape[0])[:, None]
    fx = np.fft.rfftfreq(e.shape[1])[None, :]
    f = np.hypot(fx, fy)
    band = P[(f >= 1 / hi) & (f <= 1 / lo)]
    if band.size < 100:
        return 0.0
    return float(np.percentile(band, 99.9) / max(np.median(band), 1e-12))


def measure(L):
    paper = float(np.percentile(L, 90))
    x0, y0, x1, y1 = content_box(L, paper)
    C = L[y0:y1, x0:x1]
    H, W = C.shape
    # ---- focus: edge detail over a grid
    sm = ndi.gaussian_filter(C, 1.0)
    edges = np.hypot(ndi.sobel(sm, 0), ndi.sobel(sm, 1))
    gh, gw = GRID, max(2, round(GRID * W / max(H, 1)))
    cells = np.zeros((gh, gw))
    for i in range(gh):
        for j in range(gw):
            cells[i, j] = edges[i * H // gh:(i + 1) * H // gh, j * W // gw:(j + 1) * W // gw].mean()
    flat = np.sort(cells.ravel())[::-1]
    top = max(1, len(flat) // 10)
    hi, hj = np.unravel_index(np.argmax(ndi.uniform_filter(cells, 3)), cells.shape)
    # ---- line weight: dark strokes, their skeleton, and the width along it
    ink = C < paper - 0.08
    darkness = paper - C[ink]
    thr = paper - max(0.25, float(np.percentile(darkness, 60)) if darkness.size else 0.25)
    lines = ndi.binary_opening(C < thr, iterations=1)
    widths = np.array([])
    if lines.sum() > 100:
        dist = ndi.distance_transform_edt(lines)
        sk = skeletonize(lines)
        widths = 2 * dist[sk]
        widths = widths[widths >= 1.5]
    wcv = float(widths.std() / widths.mean()) if widths.size > 20 else 0.0
    wratio = float(np.percentile(widths, 90) / max(np.percentile(widths, 10), 1e-6)) if widths.size > 20 else 1.0
    # ---- values
    v = C[ink] if ink.sum() > 100 else C.ravel()
    p1, p50 = np.percentile(C, 1), np.percentile(v, 50)
    bands = np.histogram(C, bins=[0, 0.2, 0.4, 0.6, 0.8, 1.01])[0] / C.size
    # ---- grain: fine texture inside toned (not paper, not solid line) areas
    tone = (C < paper - 0.06) & (C > 0.25) & ~lines
    fine = C - ndi.gaussian_filter(C, 1.5)
    grain = float(np.abs(fine[tone]).mean()) if tone.sum() > 200 else 0.0
    # ---- repetition: how peaky the detail's spectrum is (exact tiling makes sharp peaks)
    # Scored tile by tile, only where marks are dense, and the typical tile reported. Scored over the whole picture,
    # a single long clean line on empty paper looks "peaky" and swamps the answer.
    T = 128
    tiles = [edges[y:y + T, x:x + T] for y in range(0, H - T + 1, T) for x in range(0, W - T + 1, T)]
    dens = np.array([t.mean() for t in tiles]) if tiles else np.array([0.0])
    dense = [t for t, d in zip(tiles, dens) if d >= np.percentile(dens, 60) and d > 0]
    repetition = float(np.median([repetition_score(t, 4, 40) for t in dense])) if dense else 0.0
    # ---- roughness: edge length of the lines vs a smoothed version of them
    def perim(mask):
        return float((mask ^ ndi.binary_erosion(mask)).sum())
    # measured on the raw marks: the cleaned-up line mask used for widths would erase the very roughness we want
    raw = C < thr
    smooth = ndi.gaussian_filter(raw.astype(float), 1.5) > 0.5
    roughness = perim(raw) / max(perim(smooth), 1.0)
    # ---- edge variety: sharpness at the borders of lines
    border = lines ^ ndi.binary_erosion(lines)
    g = edges[border]
    edge_cv = float(g.std() / g.mean()) if g.size > 50 else 0.0
    return {
        'repetition': repetition, 'roughness': roughness, 'edge_cv': edge_cv,
        'box': (x0, y0, x1, y1), 'cells': cells, 'edges': edges, 'lines': lines,
        'focus_gini': gini(cells), 'focus_top10': float(flat[:top].sum() / max(flat.sum(), 1e-9)),
        'focus_at': ((hj + 0.5) / gw, (hi + 0.5) / gh),
        'width_median': float(np.median(widths)) if widths.size else 0.0, 'width_cv': wcv, 'width_ratio': wratio,
        'darkest': float(p1), 'paper': paper, 'value_range': float(paper - p1), 'bands_used': int((bands > 0.03).sum()),
        'bands': bands, 'grain': grain, 'scale': max(H, W),
    }


def describe(m, label):
    fx, fy = m['focus_at']
    return (f"{label}\n"
            f"  focus: gini {m['focus_gini']:.2f}, busiest tenth holds {m['focus_top10'] * 100:.0f}% of the detail, centred at ({fx:.2f}, {fy:.2f})\n"
            f"  line weight: median {m['width_median'] / m['scale'] * 1000:.1f} per 1000 px, variation (cv) {m['width_cv']:.2f}, thick/thin ratio {m['width_ratio']:.1f}\n"
            f"  values: darkest {m['darkest']:.2f}, paper {m['paper']:.2f}, range {m['value_range']:.2f}, {m['bands_used']} of 5 value bands used\n"
            f"  grain: {m['grain'] * 1000:.1f}\n"
            f"  hand: repetition {m['repetition']:.0f}, line roughness {m['roughness']:.3f}, edge-sharpness variety {m['edge_cv']:.2f}")


def compare(a, r):
    notes = []
    def say(cond, text):
        if cond:
            notes.append(text)
    say(a['focus_gini'] < r['focus_gini'] - 0.05, f"detail is spread too evenly (gini {a['focus_gini']:.2f} vs {r['focus_gini']:.2f}): pile more detail and contrast at the focal point and let the edges go loose")
    say(a['focus_gini'] > r['focus_gini'] + 0.1, f"detail is more concentrated than the reference (gini {a['focus_gini']:.2f} vs {r['focus_gini']:.2f})")
    say(a['width_cv'] < r['width_cv'] - 0.08, f"line weight is too uniform (cv {a['width_cv']:.2f} vs {r['width_cv']:.2f}): swell lines in shadow and at overlaps, thin them where light hits")
    say(a['width_ratio'] < r['width_ratio'] * 0.75, f"thick-to-thin contrast is low ({a['width_ratio']:.1f} vs {r['width_ratio']:.1f})")
    say(a['value_range'] < r['value_range'] - 0.08, f"the darkest darks aren't dark enough (range {a['value_range']:.2f} vs {r['value_range']:.2f})")
    say(a['bands_used'] < r['bands_used'], f"uses {a['bands_used']} value bands to the reference's {r['bands_used']}: add more in-between tones")
    say(a['grain'] < r['grain'] * 0.6, f"tones are too smooth (grain {a['grain'] * 1000:.1f} vs {r['grain'] * 1000:.1f}): graphite should show texture")
    say(a['repetition'] > r['repetition'] * 1.5, f"marks repeat too exactly (repetition {a['repetition']:.0f} vs {r['repetition']:.0f}): vary each scale's size, angle and pressure")
    say(a['roughness'] < r['roughness'] - 0.02, f"line edges are too clean (roughness {a['roughness']:.3f} vs {r['roughness']:.3f}): let lines wobble and break")
    say(a['edge_cv'] < r['edge_cv'] - 0.08, f"edges are all equally sharp (variety {a['edge_cv']:.2f} vs {r['edge_cv']:.2f}): soften some, sharpen others")
    return notes or ['close to the reference on every measure']


def sheet(m, path):
    """the drawing's detail map beside its detected lines, for looking at, not just reading"""
    cells = m['cells'] / max(m['cells'].max(), 1e-9)
    H, W = m['edges'].shape
    heat = np.kron(cells, np.ones((H // cells.shape[0] + 1, W // cells.shape[1] + 1)))[:H, :W]
    left = np.stack([heat, heat * 0.4, 1 - heat], -1)
    right = np.repeat((~m['lines'])[..., None].astype(float), 3, -1)
    Image.fromarray((np.concatenate([left, right], 1) * 255).astype(np.uint8)).save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image'); ap.add_argument('--ref'); ap.add_argument('--crop'); ap.add_argument('--ref-crop')
    ap.add_argument('--out', default='.')
    a = ap.parse_args()
    m = measure(load(a.image, a.crop))
    text = [describe(m, os.path.basename(a.image))]
    if a.ref:
        r = measure(load(a.ref, a.ref_crop))
        text += [describe(r, os.path.basename(a.ref) + ' (reference)'), 'to move toward the reference:'] + [f'  - {n}' for n in compare(m, r)]
    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, os.path.splitext(os.path.basename(a.image))[0])
    sheet(m, base + '.linework.png')
    open(base + '.linework.txt', 'w').write('\n'.join(text) + '\n')
    print('\n'.join(text))


if __name__ == '__main__':
    main()
