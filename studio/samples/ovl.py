"""Shared caption + hook overlay for the style samples (same words, same timing as the real Short)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 5.0
FONT = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
LINE = "This man just slipped off a volcano, two hundred sixty feet above a lava lake."
V0, V1 = 0.06, 4.327


def _text(im, txt, y, size, fill, stroke=12, sc=1.0):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, int(size * sc))
    while d.textlength(txt, font=f) > W - 120 and size > 60:
        size -= 6; f = ImageFont.truetype(FONT, int(size * sc))
    tw = d.textlength(txt, font=f)
    d.text(((W - tw) / 2, y - size * sc * 0.6), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(20, 14, 26, 255))


_CACHE = {}


def _layer(hook, hook_col, cap):
    """Render the text layer once per distinct (hook, caption); keep only the rows that have ink."""
    key = (hook, hook_col, cap)
    if key not in _CACHE:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        _text(lay, hook, 165, 118, hook_col + (255,))
        if cap:
            _text(lay, cap, H - 620 + 62, 104, (255, 255, 255, 255))
        a = np.asarray(lay).astype(np.float32)
        rows = np.where(a[..., 3].max(1) > 0)[0]
        bands = []
        if len(rows):
            # split into contiguous bands (hook band, caption band)
            cuts = np.where(np.diff(rows) > 1)[0]
            starts = np.concatenate([[rows[0]], rows[cuts + 1]]); ends = np.concatenate([rows[cuts], [rows[-1]]]) + 1
            for y0, y1 in zip(starts, ends):
                al = a[y0:y1, :, 3:4] / 255.0
                bands.append((y0, y1, a[y0:y1, :, :3] * al, 1 - al))
        _CACHE[key] = bands
    return _CACHE[key]


def caption_at(t):
    words = LINE.split()
    k = float(np.clip((t - V0) / (V1 - V0) + 0.05, 0, 0.999))
    if t >= V1 + 0.6:
        return None
    i = int(k * len(words)); j0 = (i // 2) * 2
    return ' '.join(words[j0:j0 + 2])


def overlay(rgb, t, hook='260 FEET', hook_col=(255, 236, 80)):
    """rgb: HxWx3 uint8. Returns a new uint8 frame with hook + 2-word caption (cached text, blended only where it is)."""
    out = np.array(rgb, copy=True)
    for y0, y1, pre, inv in _layer(hook, hook_col, caption_at(t)):
        out[y0:y1] = (out[y0:y1] * inv + pre + 0.5).astype(np.uint8)
    return out
