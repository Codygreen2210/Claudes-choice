"""make_thumb.py: build a high-contrast YouTube thumbnail from a clean film still.

Rules (from the Oct 13 thumbnail research, see CLAUDE.md):
  - one subject, pushed off-center and zoomed big
  - punchier color and contrast than the film, dark vignette
  - 2-4 heavy words on the empty side, one key word in red, thick dark outline
  - check it at phone size (a 320 px preview is saved next to it)

Usage (from a spec JSON):
  python3 make_thumb.py spec.json
spec: {"out": "a.jpg", "still": "t312.png", "zoom": 1.5, "focus": [0.3, 0.45],
       "side": "right", "lines": [["DON'T", "cream"], ["MISS", "red"]],
       "tint": [255, 140, 60], "tint_amt": 0.12}
"""
import json, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1280, 720
FONT = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
COLS = {'cream': (246, 236, 214), 'red': (226, 52, 38), 'gold': (255, 196, 64)}


def frame(still, zoom, focus, side):
    im = Image.open(still).convert('RGB')
    # crop off the bottom caption band before zooming
    im = im.crop((0, 0, im.width, int(im.height * 0.90)))
    cw, ch = im.width / zoom, im.width / zoom * H / W
    ch = min(ch, im.height); cw = ch * W / H
    fx, fy = focus[0] * im.width, focus[1] * im.height
    # subject sits on the opposite third from the text
    tx = 0.68 if side == 'left' else 0.32
    x0 = min(max(fx - cw * tx, 0), im.width - cw)
    y0 = min(max(fy - ch * 0.5, 0), im.height - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)


def grade(im, tint, amt):
    im = ImageEnhance.Color(im).enhance(1.45)
    im = ImageEnhance.Contrast(im).enhance(1.3)
    if tint and amt:
        im = Image.blend(im, Image.new('RGB', im.size, tuple(tint)), amt)
    return im


def shade(im, side):
    # darken the text side so cream/red read at phone size, plus a soft vignette
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for x in range(W):
        t = x / W if side == 'right' else 1 - x / W
        d.line([(x, 0), (x, H)], fill=int(235 * min(1, max(0, (t - 0.30) / 0.45)) ** 1.1))
    v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse((-W * .25, -H * .3, W * 1.25, H * 1.3), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new('RGB', (W, H), (8, 8, 12))
    im = Image.composite(dark, im, m)
    return Image.composite(im, dark, v.point(lambda p: 70 + p * 185 // 255))


def words(im, lines, side):
    d = ImageDraw.Draw(im)
    box_w = W * 0.46
    sizes = []
    for s, _ in lines:
        size = 260
        while ImageFont.truetype(FONT, size).getlength(s) > box_w and size > 60: size -= 6
        sizes.append(size)
    total = sum(int(s * 0.95) for s in sizes)
    y = (H - total) / 2 - 10
    for (s, col), size in zip(lines, sizes):
        f = ImageFont.truetype(FONT, size)
        x = W - 50 - f.getlength(s) if side == 'right' else 50
        d.text((x + 8, y + 10), s, font=f, fill=(0, 0, 0))  # drop shadow
        d.text((x, y), s, font=f, fill=COLS.get(col, col), stroke_width=max(6, size // 22), stroke_fill=(14, 10, 8))
        y += int(size * 0.95)
    return im


def build(spec):
    im = frame(spec['still'], spec.get('zoom', 1.3), spec.get('focus', [0.5, 0.5]), spec.get('side', 'right'))
    im = grade(im, spec.get('tint'), spec.get('tint_amt', 0))
    im = shade(im, spec.get('side', 'right'))
    im = words(im, spec['lines'], spec.get('side', 'right'))
    im.save(spec['out'], quality=92)
    im.resize((320, 180), Image.LANCZOS).save(spec['out'].rsplit('.', 1)[0] + '_320.png')


if __name__ == '__main__':
    for s in json.load(open(sys.argv[1])):
        build(s)
