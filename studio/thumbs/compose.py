"""compose.py: build a thumbnail from a film still + a painted character + 1-4 words, then score it.

  python3 compose.py spec.json      (a list of specs; each is built, checked, and reported)

spec: {"out": "midway_D.jpg", "title": "...", "still": "t330.png", "zoom": 1.9, "focus": [0.5, 0.48],
       "bg_side": "right",                     # where the scene's subject should sit
       "char": "pilot.png", "char_box": [x, y, height], "char_flip": false,
       "lines": [["DON'T", "cream"], ["MISS.", "red"]], "text_at": [x, y, "left"|"right"], "text_w": 0.42,
       "shade": "left"|"right"|null, "tint": [r,g,b], "tint_amt": 0.05}
Writes <out>, <out>.char.png and <out>.text.png (masks for thumbcheck), <out>.meta.json and a 320 px preview.
"""
import json, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_thumb import frame, grade, W, H, FONT, COLS
import thumbcheck


def darken_side(im, side, strength=235):
    if not side: return im
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for x in range(W):
        t = x / W if side == 'right' else 1 - x / W
        d.line([(x, 0), (x, H)], fill=int(strength * min(1, max(0, (t - 0.30) / 0.45)) ** 1.1))
    return Image.composite(Image.new('RGB', (W, H), (8, 8, 12)), im, m)


def vignette(im, amt=185):
    v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse((-W * .25, -H * .3, W * 1.25, H * 1.3), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(120)).point(lambda p: 255 - amt + p * amt // 255)
    return Image.composite(im, Image.new('RGB', (W, H), (8, 8, 12)), v)


def _lay(s, dm, d):
    tx, ty, align = s.get('text_at', [W - 50, H * 0.2, 'right'])
    box_w = W * s.get('text_w', 0.42)
    for txt, col in s['lines']:
        size = s.get('max_size', 220)
        while ImageFont.truetype(FONT, size).getlength(txt) > box_w and size > 50: size -= 4
        f = ImageFont.truetype(FONT, size); lw = f.getlength(txt)
        x = tx - lw if align == 'right' else tx
        sw = max(6, size // 20)
        if d is not None:
            d.text((x + 7, ty + 9), txt, font=f, fill=(0, 0, 0, 230))
            d.text((x, ty), txt, font=f, fill=COLS.get(col, col), stroke_width=sw, stroke_fill=(14, 10, 8))
        dm.text((x, ty), txt, font=f, fill=255)
        ty += int(size * 0.98)


def build(s):
    bg = frame(s['still'], s.get('zoom', 1.3), s.get('focus', [0.5, 0.5]), s.get('bg_side', 'right'))
    bg = grade(bg, s.get('tint'), s.get('tint_amt', 0))
    if s.get('blur'): bg = bg.filter(ImageFilter.GaussianBlur(s['blur']))  # depth: scene softer than the face
    bg = vignette(darken_side(bg, s.get('shade')))
    out = bg.convert('RGBA')
    char_mask = Image.new('L', (W, H), 0)
    if s.get('char'):
        ch = Image.open(s['char']).convert('RGBA'); bb = ch.getbbox(); ch = ch.crop(bb)
        if s.get('char_flip'): ch = ch.transpose(Image.FLIP_LEFT_RIGHT)
        x, y, h = s['char_box']; w = int(ch.width * h / ch.height); ch = ch.resize((w, h), Image.LANCZOS)
        # soft dark glow behind the character so it separates from the scene
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); glow.paste((6, 6, 10, 255), (x, y), ch.split()[3])
        glow.putalpha(glow.split()[3].filter(ImageFilter.GaussianBlur(28)).point(lambda p: p * 0.75))
        out.alpha_composite(glow); out.alpha_composite(ch, (x, y))
        char_mask.paste(255, (x, y), ch.split()[3].point(lambda p: 255 if p > 128 else 0))
    text_mask = Image.new('L', (W, H), 0)
    # first pass: lay the words out on the mask only, to put a soft dark halo behind them
    _lay(s, ImageDraw.Draw(text_mask), None)
    halo = text_mask.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(26)).point(lambda p: int(p * s.get('halo', 0.8)))
    out.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), 8)] * 3 + [halo]))
    text_mask = Image.new('L', (W, H), 0)
    d, dm = ImageDraw.Draw(out), ImageDraw.Draw(text_mask)
    _lay(s, dm, d)
    rgb = out.convert('RGB')
    base = s['out'].rsplit('.', 1)[0]
    rgb.save(s['out'], quality=92); rgb.resize((320, 180), Image.LANCZOS).save(base + '_320.png')
    char_mask.save(base + '.char.png'); text_mask.save(base + '.text.png')
    cream = np.array([[COLS['cream']]], dtype=np.float64)
    meta = {'title': s.get('title', ''), 'words': [t for t, _ in s['lines']], 'red_word': any(c == 'red' for _, c in s['lines']),
            'text_lum': float(thumbcheck.lum(cream)[0, 0])}
    json.dump(meta, open(base + '.meta.json', 'w'))
    return thumbcheck.report(s['out'], meta['title'], meta)


if __name__ == '__main__':
    for s in json.load(open(sys.argv[1])):
        print(build(s)[1]); print()
