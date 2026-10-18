"""Shared kit for the narrated toon Shorts.

Picture: run(BEATS, times.json, lines.json, out.mp4) renders beats timed to the narration.
  BEATS[i] is fn(lt, dur, T) -> Canvas. The LAST beat must be the opening beat run up to its own
  start (pass loop_fn=BEATS[0]); it is drawn as BEATS[0](T - total, ...) so the final frame is the
  frame just before frame one: seamless loop. Every Short opens mid-action (house rule).
Sound: Mix(times) gives put(), circular folding, voice ducking and a fixed-gain finish.
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import *          # noqa: F401,F403
import common

for _f in ('/usr/share/fonts/opentype/inter/Inter-Black.otf', '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'):
    if os.path.exists(_f):
        common.FONT = _f
        break

BLUE = ramp('#3d7fd8', '#2a559a', '#7fb4ff')
ORANGE = ramp('#ff8a2a', '#c4561a', '#ffbf7a')
YELLOW = ramp('#ffd23f', '#d09a10', '#fff08a')
GREEN = ramp('#3fbf6a', '#25804a', '#7fe8a0')
PINK = ramp('#ff8f9a', '#d0566a', '#ffc4cc')
DARK = ramp('#2b2f38', '#191c22', '#454b57')
STEEL = ramp('#a7b0ba', '#6d7782', '#dfe6ec')
WATER = ramp('#3fa9e0', '#2378b0', '#8fd6ff')


# ------------------------------------------------------------------ small drawing helpers
def pop(t, t0, dur=0.25):
    """0 before t0, then a scale that overshoots and settles at 1."""
    k = np.clip((t - t0) / dur, 0, 1)
    if k <= 0:
        return 0
    return 1 + 0.25 * np.sin(k * np.pi) * (1 - k) * 3 if k < 1 else 1



def arrows(cv, pairs, col=(255, 255, 255), w=12):
    c = flat(np.array(col, np.float32) / 255.0)
    for a, b in pairs:
        line(cv, [a, b], w, c, ow=3)
        d = np.array(b, float) - np.array(a, float); d /= (np.linalg.norm(d) + 1e-6); n = np.array([-d[1], d[0]])
        tip = np.array(b, float)
        line(cv, [tuple(tip - d * 36 + n * 24), tuple(tip), tuple(tip - d * 36 - n * 24)], w, c, ow=3)


def thermo(cv, x, y, val, lo=70, hi=130, h=700, label_=True, unit='°F'):
    """Big thermometer, val in degrees, fills red."""
    k = np.clip((val - lo) / (hi - lo), 0, 1)
    box(cv, x, y, 60, h / 2 + 30, ramp('#f4f1ea'), r=60)
    disc(cv, x, y + h / 2 + 30, 95, ramp('#f4f1ea'))
    disc(cv, x, y + h / 2 + 30, 72, ramp('#e2483d'))
    top = y + h / 2 - k * h
    if k > 0.01:
        box(cv, x, (top + y + h / 2 + 30) / 2, 32, (y + h / 2 + 30 - top) / 2, ramp('#e2483d'), r=30, ow=0)
    if label_:
        label(cv, f'{int(val)}{unit}', x, y - h / 2 - 110, 84, (255, 236, 80))


def meter(cv, x, y, w, k, col, title, a=1.0):
    """Horizontal bar meter with a title, k in 0..1."""
    box(cv, x, y, w / 2 + 10, 46, DARK, r=30, alpha=a)
    if k > 0.01:
        box(cv, x - w / 2 + w * k / 2, y, w * k / 2, 34, col, r=24, ow=0, alpha=a)
    label(cv, title, x, y - 90, 54, (255, 255, 255), a=a)


def heart_icon(cv, x, y, s, beat=0.0):
    sc = s * (1 + 0.12 * beat)
    cv.shape(heart(x, y, 200 * sc), (x - 130 * sc, y - 130 * sc, x + 130 * sc, y + 130 * sc), ramp('#e2483d'))


def brain(cv, x, y, s, hot=0.0):
    col = ramp('#f6a5b4', '#d0708a', '#ffd0da')
    blobs = [circle(x + dx * s, y + dy * s, r * s) for dx, dy, r in
             ((-110, -20, 110), (0, -60, 125), (110, -20, 110), (-60, 60, 100), (70, 60, 100))]
    cv.shape(smooth(40 * s, *blobs), (x - 230 * s, y - 190 * s, x + 230 * s, y + 170 * s), col,
             tint=('#ff3a2a', float(hot)) if hot > 0 else None)
    for k in range(5):
        pts = [(x + (-170 + k * 80 + 30 * np.sin(u * 6 + k)) * s, y + (-120 + u * 240) * s) for u in np.linspace(0, 1, 8)]
        line(cv, pts, 6 * s, flat(hexc('#c0607a')))


def rewind(cv, T, k):
    """Rewind look for k in 0..1 (1 = full): desaturate, sideways streaks, label."""
    if k <= 0:
        return
    g = cv.img.mean(2, keepdims=True)
    cv.img = np.ascontiguousarray(cv.img * (1 - 0.6 * k) + g * 0.6 * k, dtype=np.float32)
    speed_lines(cv, T, k, vertical=False)
    label(cv, 'REWIND', cv.cx, cv.cy + 820 / cv.zoom, 60 / cv.zoom, (255, 255, 255), a=k)


def caption(cv, txt, k):
    words = txt.split()
    shown = ' '.join(words[:max(1, int(np.ceil(np.clip(k, 0, 1) * len(words))))])
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(common.FONT, 60)
    lines_, cur = [], ''
    for w in shown.split():
        test = (cur + ' ' + w).strip()
        if d.textlength(test, font=f) > W - 160:
            lines_.append(cur); cur = w
        else:
            cur = test
    lines_.append(cur)
    y = H - 440 - 74 * (len(lines_) - 1)
    for ln in lines_:
        tw = d.textlength(ln, font=f)
        d.text(((W - tw) / 2, y), ln, font=f, fill=(255, 255, 255, 255), stroke_width=9, stroke_fill=(20, 14, 26, 255))
        y += 74
    cv.overlay(im)


# ------------------------------------------------------------------ render
def frame(T, TM, LINES, BEATS):
    total = TM['total']
    n = len(TM['starts'])
    for i, (t0, d) in enumerate(zip(TM['starts'], TM['durs'])):
        if t0 <= T < t0 + d or i == n - 1:
            lt = T - t0
            if i == n - 1:
                cv = BEATS[0](T - total, TM['durs'][0], T - total)     # the opening, on its own clock, just before frame one
            else:
                cv = BEATS[i](lt, d, T)
            v0, v1 = TM['voice'][i]
            caption(cv, LINES[i]['text'], (T - v0) / max(v1 - v0, 0.3) + 0.05)
            if 0 < i < n - 1 and lt < 0.08:
                cv.flash('#ffffff', 0.25 * (1 - lt / 0.08))
            return cv


def run(BEATS):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('times'); ap.add_argument('lines'); ap.add_argument('out')
    ap.add_argument('--still', type=float); ap.add_argument('--sheet', action='store_true')
    a = ap.parse_args()
    TM = json.load(open(a.times)); LINES = json.load(open(a.lines))
    assert len(BEATS) == len(LINES) - 1, f'{len(BEATS)} beats for {len(LINES)} lines (last line reuses beat 0)'
    if a.sheet:                                   # one still per beat, for checking
        ims = []
        for t0, d in zip(TM['starts'], TM['durs']):
            ims.append(Image.fromarray(frame(t0 + d * 0.75, TM, LINES, BEATS).to_uint8()).resize((216, 384)))
        cols = 8
        sh = Image.new('RGB', (216 * cols, 384 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sh.paste(im, ((i % cols) * 216, (i // cols) * 384))
        sh.save(a.out); return
    if a.still is not None:
        Image.fromarray(frame(a.still, TM, LINES, BEATS).to_uint8()).save(a.out); return
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    for i in range(int(round(TM['total'] * FPS))):
        ff.stdin.write(frame(i / FPS, TM, LINES, BEATS).to_uint8().tobytes())
    ff.stdin.close(); ff.wait()


# ------------------------------------------------------------------ sound
class Mix:
    """Circular mix: anything placed past the end folds back onto the start."""
    SR = 44100

    def __init__(self, times_path, studio_root=None):
        root = studio_root or os.environ.get('STUDIO_ROOT')
        sys.path.insert(0, root)
        from studio.instruments import synth as S
        self.S = S
        self.K = os.path.join(root, 'studio', 'sfx', 'samples')
        self.TM = json.load(open(times_path))
        self.B, self.DUR, self.D = self.TM['starts'], self.TM['durs'], self.TM['total']
        self.N = int(round(self.D * self.SR)); self.PAD = 6 * self.SR
        self.fx = np.zeros((2, self.N + self.PAD)); self.mus = np.zeros((2, self.N + self.PAD))
        self._c = {}

    def ld(self, p):
        t = tempfile.mktemp(suffix='.wav')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ac', '1', '-ar', str(self.SR), t])
        import soundfile as sf
        x, _ = sf.read(t); os.unlink(t); return x

    def k(self, cat, i=0):
        d = os.path.join(self.K, cat); fs = sorted(os.listdir(d)); p = os.path.join(d, fs[i % len(fs)])
        if p not in self._c:
            self._c[p] = self.ld(p)
        return self._c[p]

    def put(self, buf, x, t, db, pan=0.0):
        x = np.asarray(x, float)
        if x.ndim == 1:
            x = np.stack([x * np.sqrt(0.5 - pan / 2), x * np.sqrt(0.5 + pan / 2)]) * np.sqrt(2)
        a = int(t * self.SR) % self.N; b = min(self.N + self.PAD, a + x.shape[1])
        buf[:, a:b] += x[:, :b - a] * 10 ** (db / 20)

    def fx_(self, x, t, db, pan=0.0):
        self.put(self.fx, x, t, db, pan)

    def mu(self, x, t, db, pan=0.0):
        self.put(self.mus, x, t, db, pan)

    # sound makers
    def env(self, n, a=0.02, r=0.1):
        t = np.arange(n) / self.SR
        return np.clip(t / a, 0, 1) * np.clip((n / self.SR - t) / r, 0, 1)

    def noise(self, dur, lo, hi, seed=1, a=0.1, r=0.2):
        n = int(dur * self.SR)
        return self.S.norm(self.S.bp(np.random.default_rng(seed).standard_normal(n), lo, hi)) * self.env(n, a, r)

    def rumble(self, dur, f=45, seed=2):
        n = int(dur * self.SR); t = np.arange(n) / self.SR
        x = self.S.lp(np.random.default_rng(seed).standard_normal(n), 120) * 3 + np.sin(2 * np.pi * f * t) * 0.6
        return self.S.norm(x) * self.env(n, 0.4, 0.6)

    def tick(self):
        return self.S.pop_note(98, 0.035)

    def heartbeat(self, t0, t1, bpm0, bpm1, db):
        t = t0
        while t < t1:
            p = (t - t0) / max(t1 - t0, 1e-6)
            hb = self.S.impact(0.35)
            self.fx_(hb, t, db); self.fx_(hb * 0.6, t + 0.2, db - 3)
            t += 60 / (bpm0 + (bpm1 - bpm0) * p)

    def swishes(self, db=-17):
        for i in range(1, len(self.B) - 1):
            S = self.S
            self.fx_(S.whoosh(0.45, 300 if i % 2 else 3000, 3000 if i % 2 else 300), self.B[i] - 0.2, db)

    def drone(self, t0, t1, root=33, db=-18):
        S = self.S
        n = int((t1 - t0 + 0.8) * self.SR); t = np.arange(n) / self.SR
        f = S.mtof(root)
        x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.003 * t) + 0.25 * S.lp(np.random.default_rng(int(root)).standard_normal(n), 200)
        x *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.15 * t)
        self.mu(S.norm(x) * self.env(n, 0.8, 0.8), t0, db)

    def pad(self, notes, t0, t1, db, bright=1400, a=0.6, r=0.8):
        self.mu(self.S.soft_pad(notes, t1 - t0 + r, a=a, r=r, bright=bright), t0, db)

    def strings(self, notes, t0, t1, db, c0=300, c1=4000):
        S = self.S; n = t1 - t0
        ss = S.supersaw(notes, n + 0.3, cutoff=max(c0, c1), cut_arr=np.linspace(c0, c1, int((n + 0.3) * self.SR)))
        self.mu(ss[:, :int(n * self.SR)], t0, db)

    def clock(self, t0, t1, db=-24, step=0.625):
        t, i = t0, 0
        while t < t1:
            self.mu(self.S.pop_note(103 if i % 2 else 98, 0.03), t, db, 0.3 if i % 2 else -0.3); t += step; i += 1

    def shape(self, t0, t1, db, ramp=0.3):
        """Story-level loudness: lift or sink a whole section (quiet before a reveal, open up for the payoff)."""
        if not hasattr(self, '_shape'):
            self._shape = []
        self._shape.append((t0, t1, db, ramp))

    def finish(self, narration, out):
        """Fold tails, put the voice on top (bed 7 dB under while talking), shape, one fixed gain to -14 LUFS."""
        import soundfile as sf, pyloudnorm as pyln
        S, N, PAD, SR = self.S, self.N, self.PAD, self.SR
        fx, mus = self.fx, self.mus
        fx[:, :PAD] += fx[:, N:N + PAD]; mus[:, :PAD] += mus[:, N:N + PAD]
        fx, mus = fx[:, :N], mus[:, :N]
        v = self.ld(narration)[:N]
        vo = np.zeros((2, N)); vo[:, :len(v)] += v
        e = np.convolve(np.abs(vo[0]), np.ones(2205) / 2205, 'same')
        act = np.convolve(np.clip(e / (np.percentile(e, 95) + 1e-9) * 3, 0, 1), np.ones(4410) / 4410, 'same')
        bed = S.hp(fx, 45) * (1 - 0.5 * act) + S.hp(mus, 55) * (1 - 0.6 * act)
        rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-9
        talk = act > 0.5
        vo = vo / rms(vo[:, talk]); bed = bed / rms(bed[:, talk]) * 10 ** (-7 / 20)
        mix = bed + vo
        sh = np.zeros(N)
        for t0, t1, db, r in getattr(self, '_shape', []):
            a, b = int(t0 * SR), int(t1 * SR); w = np.zeros(N); w[a:b] = 1
            sh += db * np.convolve(w, np.ones(int(r * SR)) / int(r * SR), 'same')
        mix = mix * 10 ** (sh / 20)
        mix = np.tanh(mix / np.max(np.abs(mix)) * 0.9) / np.tanh(0.9)
        raw, eq = out + '.raw.wav', out + '.eq.wav'
        sf.write(raw, mix.T, SR)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', 'equalizer=f=450:t=o:w=1.2:g=-4,highshelf=f=5000:g=2', '-ar', str(SR), eq])
        y, _ = sf.read(eq)
        y = y * 10 ** ((-14 - pyln.Meter(SR).integrated_loudness(y)) / 20)
        lim = 10 ** (-2 / 20)
        if np.max(np.abs(y)) > lim:
            y = np.tanh(y / lim) * lim
        n = int(0.01 * SR); w = np.linspace(0, 1, n)[:, None]
        y[-n:] = y[-n:] * (1 - w) + y[:1] * w
        sf.write(out, y, SR)
        os.unlink(raw); os.unlink(eq)
