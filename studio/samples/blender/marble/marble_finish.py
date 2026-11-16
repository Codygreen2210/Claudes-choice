"""Race graphics over the Blender render, then the sound:  live standings (rows slide when places change, time gap to
the leader), the race clock, a course bar with every marble on it, the title at the start, NEW LEADER pops, the photo
finish, the winner, the final results and the call to action.
    python3 marble_finish.py cam.npz SHOT.mp4 MIX.wav OUT.mp4 [--frames a,b,c --still DIR]"""
import sys, os, subprocess, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from race import Race, NAMES, COLS, FPS
ap = argparse.ArgumentParser(); ap.add_argument('cam'); ap.add_argument('shot'); ap.add_argument('mix'); ap.add_argument('out')
ap.add_argument('--frames', default=''); ap.add_argument('--still', default='')
a = ap.parse_args()
R = Race(a.cam); W, H = 1920, 1080; NF = R.N
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, 'assets', n), s)
FB = lambda s: F('Outfit-Bold.ttf', s); FR = lambda s: F('Outfit-Regular.ttf', s); FT = lambda s: F('Tektur-Medium.ttf', s)
cl = lambda x, lo, hi: max(lo, min(hi, x))
def sm(e0, e1, x):
    u = cl((x - e0) / (e1 - e0), 0, 1); return u * u * (3 - 2 * u)
def fmt(t): return f'{int(t // 60)}:{t % 60:04.1f}'

# time gaps: when did the leader reach the spot this marble is at now?
LP = np.maximum.accumulate(R.prog.max(axis=1)); TT = np.arange(NF) / FPS
def gap(f, i):
    p = R.prog[f, i]; k = int(np.searchsorted(LP, p)); return max(0.0, TT[f] - TT[min(k, NF - 1)])
FIN_T = (R.fin) / FPS; T_WIN, T_LAST = R.t_win, R.t_last; ORDER = R.order_final; WIN = ORDER[0]
MARGIN = FIN_T[ORDER[1]] - FIN_T[ORDER[0]]
SECT = [('ZIGZAG', 'zigzag'), ('JUMP', 'drop1'), ('VORTEX', 'vortex1'), ('HALF-PIPE', 'halfpipe'), ('CORKSCREW', 'corkscrew'), ('PLINKO', 'plinko'),
        ('LANES', 'lanes'), ('BIG JUMP', 'drop2'), ('TOWER', 'helix'), ('MEGA VORTEX', 'vortex2'), ('ROLLERS', 'rollers'), ('FINAL JUMP', 'drop3')]
TOTAL = float(np.load(a.cam)['prog'].max()) if False else None
import json
# course length + where each section starts on it (from the progress the pieces were given in the sim)
d_ = np.load(a.cam, allow_pickle=True); pn = list(d_['names'])
PROG_END = float(R.prog[-1].max())
# section starts: the progress where the first marble entered that piece
SEC_AT = []
for lab, nm in SECT:
    k = pn.index(nm); fs = np.where((R.piece == k).any(axis=1))[0]
    SEC_AT.append((lab, float(R.prog[fs[0]].max()) if len(fs) else 0.0))
FIN_P = float(R.prog[R.fin[WIN], WIN])

# sprites: a glowing dot per colour
def glow_dot(col, r=11, g=22):
    s = 2 * (r + g); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((s / 2 - r - 6, s / 2 - r - 6, s / 2 + r + 6, s / 2 + r + 6), fill=col + (170,)); im = im.filter(ImageFilter.GaussianBlur(g / 2.2))
    d = ImageDraw.Draw(im); d.ellipse((s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r), fill=col + (255,))
    hi = tuple(min(255, c + 120) for c in col); d.ellipse((s / 2 - r * 0.45, s / 2 - r * 0.6, s / 2 + r * 0.1, s / 2 - r * 0.05), fill=hi + (230,))
    return im
DOT = [glow_dot(c) for c in COLS]; DOTS = [glow_dot(c, 8, 14) for c in COLS]
def paste_c(base, im, x, y): base.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
def text_glow(base, xy, txt, font, col, anchor='mm', glow=10, stroke=0, alpha=1.0):
    if alpha <= 0.01: return
    lay = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text(xy, txt, font=font, fill=col + (int(200 * alpha),), anchor=anchor, stroke_width=stroke + 4, stroke_fill=col + (int(200 * alpha),))
    lay = lay.filter(ImageFilter.GaussianBlur(glow)); d = ImageDraw.Draw(lay)
    d.text(xy, txt, font=font, fill=(255, 255, 255, int(255 * alpha)), anchor=anchor, stroke_width=stroke, stroke_fill=col + (int(255 * alpha),))
    base.alpha_composite(lay)
def panel(d, box, r=18, fill=(6, 9, 18, 170), outline=(90, 140, 255, 120)):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=2)

# shown places: a new order only shows once it has held for 9 frames (so rows don't flicker while the pack is tied)
SHOWN = np.zeros_like(R.rank); cur = R.rank[0].copy(); cand = cur.copy(); hold = 0
for f_ in range(NF):
    tr = R.rank[f_]
    if (tr == cur).all() or R.fin.min() <= f_ and False: hold = 0
    elif (tr == cand).all():
        hold += 1
        if hold >= 9 or (R.fin <= f_).any() and (tr != cur).any() and f_ in set(R.fin.tolist()): cur = tr.copy(); hold = 0
    else: cand = tr.copy(); hold = 1
    if (R.fin == f_).any(): cur = tr.copy(); hold = 0
    SHOWN[f_] = cur
rowy = {i: float(SHOWN[0, i]) for i in range(8)}
def overlay(f, state):
    t = f / FPS; im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    results = t > T_LAST + 0.8
    # ---- standings (top left)
    if not results:
        x0, y0, rh = 34, 34, 46; panel(d, (x0, y0, x0 + 330, y0 + 56 + 8 * rh + 10))
        d.text((x0 + 18, y0 + 16), 'LIVE STANDINGS', font=FB(22), fill=(150, 190, 255, 255))
        for i in range(8):
            target = float(SHOWN[f, i]); state[i] += (target - state[i]) * 0.3
            y = y0 + 56 + state[i] * rh; r_ = int(round(state[i]))
            if r_ == 0 and abs(state[i] - target) < 0.3: d.rounded_rectangle((x0 + 8, y + 2, x0 + 322, y + rh - 4), 10, fill=COLS[i] + (55,))
            d.text((x0 + 24, y + rh / 2), str(int(target) + 1), font=FT(24), fill=(255, 255, 255, 235), anchor='mm')
            paste_c(im, DOT[i], x0 + 66, y + rh / 2)
            d.text((x0 + 92, y + rh / 2), NAMES[i], font=FB(25), fill=(255, 255, 255, 255), anchor='lm')
            if R.fin[i] <= f: s_ = fmt(FIN_T[i]) if i == WIN else f'+{FIN_T[i] - FIN_T[WIN]:.2f}'; c_ = (255, 215, 80, 255) if i == WIN else (200, 210, 230, 255)
            elif target == 0: s_ = 'LEADER'; c_ = (255, 215, 80, 255)
            else: s_ = f'+{gap(f, i):.1f}s'; c_ = (190, 200, 220, 255)
            d.text((x0 + 312, y + rh / 2), s_, font=FT(21), fill=c_, anchor='rm')
    # ---- race clock (top centre)
    tc = min(t, T_WIN) if t >= T_WIN else t
    if not results:
        panel(d, (W / 2 - 130, 30, W / 2 + 130, 112)); d.text((W / 2, 52), 'GLOWING MARBLE RACE', font=FB(19), fill=(150, 190, 255, 255), anchor='mm')
        d.text((W / 2, 86), fmt(tc), font=FT(40), fill=(255, 255, 255, 255) if t < T_WIN else (255, 215, 80, 255), anchor='mm')
    # ---- course bar (bottom): sections, finish flag, every marble
    if not results:
        bx0, bx1, by = 210, 1710, 1018
        d.rounded_rectangle((bx0 - 20, by - 44, bx1 + 60, by + 30), 16, fill=(6, 9, 18, 150))
        d.line((bx0, by, bx1, by), fill=(90, 140, 255, 200), width=4)
        X = lambda p: bx0 + (bx1 - bx0) * cl(p / FIN_P, 0, 1)
        for lab, p in SEC_AT:
            x = X(p); d.line((x, by - 9, x, by + 9), fill=(150, 190, 255, 200), width=2)
            if lab not in ('HALF-PIPE', 'LANES', 'ROLLERS'): d.text((x, by + 18), lab, font=FR(15), fill=(170, 195, 240, 230), anchor='mm')
        for k in range(6):
            for j in range(2):
                d.rectangle((bx1 + 8 + k * 6, by - 14 + j * 6 + (k % 2) * 6, bx1 + 14 + k * 6, by - 8 + j * 6 + (k % 2) * 6), fill=(255, 255, 255, 230))
        d.text((bx1 + 26, by + 18), 'FINISH', font=FB(14), fill=(255, 255, 255, 240), anchor='mm')
        for i in sorted(range(8), key=lambda i: -R.rank[f, i]):
            paste_c(im, DOTS[i], X(R.prog[f, i]), by - 22 + (R.rank[f, i] % 2) * 0)
    # ---- title at the start
    if t < 4.6:
        al = sm(0.0, 0.25, t) * (1 - sm(3.6, 4.6, t)); yy = 330
        text_glow(im, (W / 2, yy), 'GLOWING MARBLE RACE', FB(92), (90, 160, 255), glow=14, alpha=al)
        text_glow(im, (W / 2, yy + 92), '8 MARBLES  ·  1 WINNER  ·  PICK YOUR COLOR!', FB(40), (255, 120, 220), glow=8, alpha=al)
    # ---- NEW LEADER
    for fl, i in R.lead_changes:
        tl = fl / FPS
        if tl < 5 or not (tl <= t < tl + 2.0) or t > T_WIN - 0.3: continue
        al = sm(tl, tl + 0.15, t) * (1 - sm(tl + 1.6, tl + 2.0, t)); sl = (1 - sm(tl, tl + 0.25, t)) * 40
        text_glow(im, (W / 2, 168 - sl), f'NEW LEADER: {NAMES[i]}!', FB(54), COLS[i], glow=10, alpha=al)
    # ---- the finish
    if T_WIN - 0.2 <= t < T_LAST + 0.8:
        if MARGIN < 0.5 and t < T_WIN + 1.4:
            al = sm(T_WIN - 0.2, T_WIN, t) * (1 - sm(T_WIN + 1.1, T_WIN + 1.4, t)); sc = 1 + 0.15 * (1 - sm(T_WIN - 0.2, T_WIN + 0.2, t))
            text_glow(im, (W / 2, 330), 'PHOTO FINISH!', FB(int(120 * sc)), (255, 255, 255), glow=16, alpha=al)
        if t >= T_WIN + 1.2:
            al = sm(T_WIN + 1.2, T_WIN + 1.5, t) * (1 - sm(T_LAST + 0.4, T_LAST + 0.8, t))
            text_glow(im, (W / 2, 300), f'{NAMES[WIN]} WINS!', FB(140), COLS[WIN], glow=18, alpha=al)
            text_glow(im, (W / 2, 400), f'by just {MARGIN:.2f} seconds over {NAMES[ORDER[1]]}', FB(44), (255, 255, 255), glow=6, alpha=al)
    # ---- results + call to action
    if results:
        al = sm(T_LAST + 0.8, T_LAST + 1.3, t); lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        bx = (W / 2 - 360, 120, W / 2 + 360, 120 + 110 + 8 * 70); panel(dl, bx, 26, fill=(6, 9, 18, 200), outline=(255, 215, 80, 160))
        dl.text((W / 2, 170), 'FINAL RESULTS', font=FB(52), fill=(255, 215, 80, 255), anchor='mm')
        for r_, i in enumerate(ORDER):
            y = 250 + r_ * 70; ra = sm(T_LAST + 1.0 + r_ * 0.12, T_LAST + 1.3 + r_ * 0.12, t)
            if ra <= 0: continue
            medal = [(255, 215, 80), (210, 220, 235), (215, 140, 70)][r_] if r_ < 3 else (160, 175, 200)
            dl.text((W / 2 - 290, y), f'{r_ + 1}', font=FT(44), fill=medal + (int(255 * ra),), anchor='mm')
            paste_c(lay, DOT[i], W / 2 - 220, y)
            dl.text((W / 2 - 180, y), NAMES[i], font=FB(44), fill=(255, 255, 255, int(255 * ra)), anchor='lm')
            dl.text((W / 2 + 300, y), fmt(FIN_T[i]) if r_ == 0 else f'+{FIN_T[i] - FIN_T[WIN]:.2f}s', font=FT(36), fill=(220, 228, 245, int(255 * ra)), anchor='rm')
        if al < 1: lay.putalpha(lay.getchannel('A').point(lambda v: int(v * al)))
        im.alpha_composite(lay)
        ca = sm(T_LAST + 2.2, T_LAST + 2.7, t)
        text_glow(im, (W / 2, 1000), 'Did your color win? Tell us in the comments  ·  Subscribe for more races', FB(40), (255, 120, 220), glow=8, alpha=ca)
    return im

def frames_in():
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', a.shot, '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
state = dict(rowy)
if a.frames:
    want = [int(x) for x in a.frames.split(',')]; os.makedirs(a.still, exist_ok=True)
    for f, fr in enumerate(frames_in()):
        ov = overlay(f, state)
        if f in want:
            base = Image.fromarray(fr).convert('RGBA'); base.alpha_composite(ov); base.convert('RGB').save(os.path.join(a.still, f'o_{f:05d}.png'))
        if f >= max(want): break
    sys.exit(0)
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-', '-i', a.mix,
                        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
                        '-shortest', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
n = 0
for f, fr in enumerate(frames_in()):
    base = Image.fromarray(fr).convert('RGBA'); base.alpha_composite(overlay(f, state)); enc.stdin.write(base.convert('RGB').tobytes()); n += 1
    if f % 600 == 0: print('frame', f, flush=True)
enc.stdin.close(); enc.wait(); print('wrote', a.out, n, 'frames')
