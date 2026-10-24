"""Finishing pass for the quicksand Short: raw RGBA frames on stdin -> grade -> captions, hook word, labels,
subscribe tap -> one encode.
    node web/render2.mjs quick.html FRAMES | python3 qs_finish.py out.mp4 times.json lines.json
Captions: up to 3 words at a time, timed inside each line's voice span by word length (same as the house Shorts)."""
import sys, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from finish import grade

W, H, FPS = 1080, 1920, 30
FONT = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
dst, times_p, lines_p = sys.argv[1], sys.argv[2], sys.argv[3]
START = int(sys.argv[sys.argv.index('--start') + 1]) if '--start' in sys.argv else 0     # first frame number (chunked renders)
TM = json.load(open(times_p)); LN = json.load(open(lines_p))
B, DUR, VOICE, TOTAL = TM['starts'], TM['durs'], TM['voice'], TM['total']

# ---- caption chunks: (t0, t1, text)
CHUNKS = []
for (v0, v1), ln in zip(VOICE, LN):
    words = ln['text'].split()
    wts = np.array([len(w.strip('.,?!:')) + 2.0 for w in words]); cum = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
    i = 0
    while i < len(words):
        n = 3 if len(' '.join(words[i:i + 3])) <= 18 else 2
        if len(words[i]) > 11: n = 1
        j = min(len(words), i + n)
        CHUNKS.append((v0 + (v1 - v0) * cum[i] - 0.04, v0 + (v1 - v0) * cum[j], ' '.join(words[i:j]).upper()))
        i = j
for k in range(len(CHUNKS) - 1):                       # each chunk stays up until the next one (no blank flicker)
    a = CHUNKS[k]; CHUNKS[k] = (a[0], max(a[1], CHUNKS[k + 1][0]) if CHUNKS[k + 1][0] - a[1] < 0.35 else a[1], a[2])


def font(sz): return ImageFont.truetype(FONT, sz)


def text_layer(items):
    """items: [(text, y, size, fill, stroke)] -> list of (y0, y1, premultiplied rgb, inverse alpha) bands."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for txt, y, size, fill, stroke in items:
        f = font(size)
        while d.textlength(txt, font=f) > W - 110 and size > 50:
            size -= 6; f = font(size)
        tw = d.textlength(txt, font=f)
        d.text(((W - tw) / 2, y - size * 0.62), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(18, 12, 10, 255))
    return lay


def bands(lay):
    a = np.asarray(lay).astype(np.float32)
    rows = np.where(a[..., 3].max(1) > 0)[0]
    out = []
    if len(rows):
        cuts = np.where(np.diff(rows) > 1)[0]
        st = np.concatenate([[rows[0]], rows[cuts + 1]]); en = np.concatenate([rows[cuts], [rows[-1]]]) + 1
        for y0, y1 in zip(st, en):
            al = a[y0:y1, :, 3:4] / 255.0
            out.append((y0, y1, a[y0:y1, :, :3] * al, 1 - al))
    return out


YEL = (255, 222, 60, 255)
RED = (255, 70, 60, 255)
HOOK = 'QUICKSAND'
LABELS = [  # (beat, from-fraction, to-fraction, text)
    (4, 0.18, 1.0, 'SAND: 2X HEAVIER THAN YOU'),
    (5, 0.5, 1.0, '= LIFTING A CAR'),
    (6, 0.25, 1.0, 'THE TIDE IS COMING'),
    (7, 0.2, 1.0, 'WIGGLE. SLOWLY.'),
    (8, 0.15, 1.0, 'LEAN BACK + FLOAT'),
]
if '--cfg' in sys.argv:                 # another Short: {"hook": "...", "labels": [[beat, f0, f1, text, "red"?], ...]}
    _cfg = json.load(open(sys.argv[sys.argv.index('--cfg') + 1]))
    HOOK = _cfg.get('hook', HOOK); LABELS = [tuple(l) for l in _cfg.get('labels', [])]
_C = {}


def overlay(fr, t):
    items = []
    if t < B[1] or t > TOTAL - 0.45:                                   # hook word, full size from frame one (and into the loop)
        items.append((HOOK, 165, 165, YEL, 14))
    for b, f0, f1, txt, *col in LABELS:
        if B[b] + DUR[b] * f0 <= t < B[b] + DUR[b] * f1:
            items.append((txt, 150, 88 if len(txt) > 14 else 124, RED if col and col[0] == 'red' else YEL, 12))
    cap = next((c for c in CHUNKS if c[0] <= t < c[1]), None)
    if cap:
        items.append((cap[2], 960 + 390, 92, (255, 255, 255, 255), 12))
    key = tuple(items)
    if key not in _C:
        _C.clear() if len(_C) > 64 else None
        _C[key] = bands(text_layer(items))
    out = np.array(fr, copy=True)
    for y0, y1, pre, inv in _C[key]:
        out[y0:y1] = (out[y0:y1] * inv + pre + 0.5).astype(np.uint8)
    # subscribe button with a finger tap, 2.8 s before the loop
    ts = TOTAL - 2.8
    if ts <= t < ts + 1.3:
        u = (t - ts) / 1.3
        pop = min(1, u / 0.12) * (1 - max(0, (u - 0.85) / 0.15))
        press = 1 - 0.08 * np.exp(-((u - 0.45) / 0.06) ** 2)
        im = Image.fromarray(out); d = ImageDraw.Draw(im)
        bw, bh = 430 * pop * press, 112 * pop * press; cx, cy = W / 2, 1640
        if bw > 4:
            col = (200, 20, 20) if abs(u - 0.45) > 0.08 else (150, 150, 150)
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=bh / 2, fill=col)
            f = font(max(8, int(58 * pop * press))); txt = 'SUBSCRIBE' if abs(u - 0.45) > 0.08 or u < 0.45 else 'SUBSCRIBED'
            tw = d.textlength(txt, font=f); d.text((cx - tw / 2, cy - 36 * pop * press), txt, font=f, fill=(255, 255, 255))
            # the finger: comes in from lower right, taps at u=0.45
            fx = cx + 120 + 160 * max(0, 0.45 - u) / 0.45 * (u < 0.45) + 40 * max(0, u - 0.6)
            fy = cy + 40 + 200 * max(0, 0.45 - u) / 0.45 * (u < 0.45) + 60 * max(0, u - 0.6)
            if pop > 0.5:
                d.rounded_rectangle([fx - 26, fy - 10, fx + 26, fy + 120], radius=26, fill=(250, 214, 186), outline=(60, 40, 30), width=5)
                d.ellipse([fx - 20, fy - 8, fx + 20, fy + 16], fill=(255, 236, 222))
        out = np.asarray(im)
    return out


if __name__ == '__main__':
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', dst], stdin=subprocess.PIPE)
    src = sys.stdin.buffer; n = W * H * 4; i = 0
    while True:
        b = src.read(n)
        if len(b) < n:
            break
        fr = np.frombuffer(b, np.uint8).reshape(H, W, 4)[::-1, :, :3]
        enc.stdin.write(overlay(grade(fr), (START + i) / FPS).tobytes()); i += 1
    enc.stdin.close(); enc.wait()
    print('finished', i, 'frames', file=sys.stderr)
