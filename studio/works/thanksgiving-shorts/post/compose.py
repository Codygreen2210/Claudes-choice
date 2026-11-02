# Finish a Short: upscale the farm render to 1080x1920, burn in captions + live readouts, add the mix.
#   python3 compose.py turkey|coma RENDER.mp4 MIX.wav OUT.mp4
import sys, json, subprocess, re, numpy as np
from PIL import Image, ImageDraw, ImageFont
name, src, mix, out = sys.argv[1:5]
W, H, FPS = 1080, 1920, 30
TM = json.load(open('/home/claude/work/b3d/%s_times.json' % name)); B = TM['starts']; TOT = TM['total']
lines = json.load(open('/home/claude/work/%s.json' % name))
lines = [l if isinstance(l, str) else l['text'] for l in lines]
F = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
def font(px): return ImageFont.truetype(F, px)
KEY = {'350', 'degrees.', 'ice', 'steam', '212', '1,700', 'fireball.', 'four', 'fire', 'never', 'frozen', 'turkey.', 'turkey', 'oil',
       'gravy', 'tryptophan,', 'tryptophan', 'chicken', 'pork', 'brain.', 'food.', 'drinks', 'sleep,', 'couch.', 'sleepy', 'hour'}

# caption groups: words spread over each line's voiced span by length
groups = []
for (t0, t1), text in zip(TM['voice'], lines):
    words = text.split(); w8 = np.array([len(w) + 2 for w in words], float); cs = np.concatenate([[0], np.cumsum(w8)]) / w8.sum()
    i = 0
    while i < len(words):
        j = min(len(words), i + 3)
        if j < len(words) and words[j - 1].endswith((',', '.')) is False and len(words) - j == 1: j += 1
        groups.append((t0 + (t1 - t0) * cs[i], t0 + (t1 - t0) * cs[j], words[i:j])); i = j

def caption(d, t):
    for g0, g1, ws in groups:
        if g0 <= t < g1 + 0.05:
            pop = min(1, (t - g0) / 0.08); fs = int(84 * (0.85 + 0.15 * pop)); f = font(fs)
            toks = [w.upper() for w in ws]
            widths = [d.textlength(w + ' ', font=f) for w in toks]; x = (W - sum(widths) + d.textlength(' ', font=f)) / 2; y = int(H * 0.69)
            for w, wd, raw in zip(toks, widths, ws):
                col = (255, 214, 0) if raw.lower().strip('.,') in {k.strip('.,') for k in KEY} else (255, 255, 255)
                d.text((x, y), w, font=f, fill=col, stroke_width=9, stroke_fill=(0, 0, 0)); x += wd
            return

def pill(d, x, y, text, fs=52, col=(255, 255, 255), bg=(0, 0, 0, 170), a=1.0):
    f = font(fs); w = d.textlength(text, font=f); pad = 22
    d.rounded_rectangle((x - w / 2 - pad, y - pad * 0.6, x + w / 2 + pad, y + fs + pad * 0.7), radius=28, fill=(bg[0], bg[1], bg[2], int(bg[3] * a)))
    d.text((x - w / 2, y - fs * 0.08), text, font=f, fill=(*col, int(255 * a)))

def beat(t):
    for i in range(len(B)):
        if i == len(B) - 1 or t < B[i + 1]: return i, t - B[i]

def overlay(t):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    i, u = beat(t)
    fade = lambda u0, u1=None: min(1, max(0, (u - u0) / 0.2))
    if name == 'turkey':
        if i in (0, 1, 2) or (i == 3 and u < 3.0):
            temp = 350
            pill(d, W / 2, 150, 'OIL  %d°F' % temp, 60, (255, 170, 60), a=1.0)
        if i == 2: pill(d, W / 2, 260, 'WATER SINKS', 48, (140, 200, 255), a=fade(0.3))
        if i == 3:
            if u >= 0.5: pill(d, W / 2, 150, 'WATER BOILS AT 212°F', 54, (140, 200, 255), a=fade(0.5))
            if u >= 3.4:
                k = min(1, (u - 3.4) / 3.0); n = int(1 + 1699 * k ** 2)
                pill(d, W / 2, 270, 'STEAM SIZE  x%s' % format(n, ','), 66, (255, 255, 255), a=fade(3.4))
        if i == 6:
            k = min(1, max(0, (u - 0.6) / 2.2)); v = 1 + 2.88 * k
            pill(d, W / 2, 150, 'HOME COOKING FIRES', 48, (255, 255, 255), a=fade(0.3))
            pill(d, W / 2, 255, 'THANKSGIVING: %.1fx A NORMAL DAY' % v, 50, (255, 120, 60), a=fade(0.6))
    else:
        if i == 1: pill(d, W / 2, 150, '1 HOUR LATER', 60, (255, 214, 0), a=fade(0.8))
        if i == 2 and u > 2.0: pill(d, W / 2, 150, 'TRYPTOPHAN', 64, (255, 190, 60), a=fade(2.0))
        if i == 3:
            for x, lab in ((0.27, 'TURKEY'), (0.5, 'CHICKEN'), (0.73, 'PORK')):
                pill(d, W * x, int(H * 0.36), lab, 38, (255, 255, 255), a=fade(0.2))
            pill(d, W / 2, 150, 'TRYPTOPHAN', 56, (255, 190, 60), a=fade(0.1))
        if i == 4:
            pill(d, W / 2, 150, 'GOLD = TRYPTOPHAN', 52, (255, 190, 60), a=fade(0.3))
            if u > 2.5: pill(d, W / 2, 260, 'NEXT STOP: BRAIN', 46, (150, 210, 255), a=fade(2.5))
        if i == 5: pill(d, W / 2, 150, 'STOMACH', 60, (255, 160, 150), a=fade(0.3))
    caption(d, t)
    return im

n = int(round(TOT * FPS))
dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', src, '-vf', 'scale=%d:%d:flags=lanczos,unsharp=5:5:0.6' % (W, H), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-', '-i', mix,
                        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
f = 0; last = None
while f < n:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = Image.frombytes('RGB', (W, H), buf); last = buf
    ov = overlay(f / FPS); fr = Image.alpha_composite(fr.convert('RGBA'), ov).convert('RGB')
    enc.stdin.write(fr.tobytes()); f += 1
dec.kill()
while f < n and last is not None:                       # hold the last frame if the render came back short
    enc.stdin.write(fr.tobytes()); f += 1
enc.stdin.close(); enc.wait(); print('frames', f)
