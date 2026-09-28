#!/usr/bin/env python3
"""look: turn a video into something I can take in at a glance, a contact sheet, a timeline, and words.

    python3 studio/senses/look.py video.mp4 [--out dir] [--frames 24] [--at 1.5,3,4.2] [--name label]

Writes <out>/<name>.look.png:
  - a contact sheet of frames (every cut is included, plus evenly spaced frames), each stamped with its time
  - timeline strips under it: motion, brightness, cuts, the colour palette of each shot, and (if the video
    has sound) the audio hits, so I can see whether cuts land on the music
and <name>.look.txt with the numbers in words, plus warnings: flashing that could trigger seizures
(WCAG 2.3.1, more than 3 big flashes in any second), black frames, frozen stretches, cuts that miss the beat.
--at extracts full-size frames at exact times for a close look (<name>.at-<t>.png).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def font(size):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def read_all(path, small_w=96):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f'look: cannot open {path}')
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    small_h = max(1, int(round(small_w * H / W)))
    smalls, hists = [], []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        s = cv2.resize(fr, (small_w, small_h), interpolation=cv2.INTER_AREA)
        smalls.append(s)
        hsv = cv2.cvtColor(s, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1, 2], None, [12, 4, 4], [0, 180, 0, 256, 0, 256]).flatten()
        hists.append(h / (h.sum() + 1e-9))
    cap.release()
    return fps, (W, H), np.array(smalls), np.array(hists)


def grab(path, t):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read()
    cap.release()
    return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB) if ok else None


def rel_lum(small_bgr):
    x = small_bgr[..., ::-1].astype(np.float64) / 255
    lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    return lin @ np.array([0.2126, 0.7152, 0.0722])


def analyse(path):
    fps, (W, H), smalls, hists = read_all(path)
    n = len(smalls)
    dur = n / fps
    lum = np.array([rel_lum(s) for s in smalls])                     # (n, h, w) linear relative luminance: for flash safety
    # perceptual lightness (gamma-encoded luma, 0..1) for motion, brightness and black frames: linear light
    # hides almost all change in dark scenes, which is not how eyes see it
    luma = np.array([(s[..., 2] * 0.2126 + s[..., 1] * 0.7152 + s[..., 0] * 0.0722) / 255.0 for s in smalls])
    mean_lum = luma.mean((1, 2))
    motion = np.concatenate([[0], np.abs(np.diff(luma, axis=0)).mean((1, 2))])
    histd = np.concatenate([[0], 0.5 * np.abs(np.diff(hists, axis=0)).sum(1)])   # 0..1

    # cuts: a histogram jump well above the local norm
    cuts = []
    med = np.array([np.median(histd[max(0, i - 15):i + 16]) for i in range(n)])
    for i in range(1, n):
        if histd[i] > max(0.35, 4 * med[i] + 0.12) and (not cuts or i - cuts[-1] > fps * 0.25):
            cuts.append(i)

    # WCAG 2.3.1 general flash: a pair of opposing changes of >= 10% relative luminance where the darker
    # state is below 0.8, over >= 25% of the frame. Count flashes (pairs) per 1 s window.
    area = []
    trans = []
    prev_dir = np.zeros(lum.shape[1:])
    for i in range(1, n):
        d = lum[i] - lum[i - 1]
        darker = np.minimum(lum[i], lum[i - 1])
        big = (np.abs(d) >= 0.1) & (darker < 0.8)
        frac = big.mean()
        area.append(frac)
        if frac >= 0.25:
            sgn = np.sign(np.sum(d[big]))
            trans.append((i, sgn))
    flashes = []
    for k in range(1, len(trans)):
        if trans[k][1] != trans[k - 1][1]:
            flashes.append(trans[k][0])
    worst = 0
    worst_at = 0.0
    fl = np.array(flashes)
    for i in range(n):
        c = int(np.sum((fl >= i) & (fl < i + fps))) // 1 if len(fl) else 0
        c = c // 1
        pairs = c // 2 + c % 2  # each flash is a pair of transitions; count opposing transitions / 2 rounded up
        if pairs > worst:
            worst, worst_at = pairs, i / fps

    black = [i for i in range(n) if mean_lum[i] < 0.03 and luma[i].max() < 0.08]
    # frozen stretches: essentially no change for > 1.5 s
    frozen, run = [], 0
    for i in range(n):
        if motion[i] < 0.0005:
            run += 1
        else:
            if run > fps * 1.5:
                frozen.append(((i - run) / fps, i / fps))
            run = 0
    if run > fps * 1.5:
        frozen.append(((n - run) / fps, n / fps))

    # palette per shot
    bounds = [0] + cuts + [n]
    palettes = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        px = np.concatenate([s.reshape(-1, 3) for s in smalls[a:b:max(1, (b - a) // 6)]]).astype(np.float32)
        k = min(5, len(px))
        _, labels, centers = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
        counts = np.bincount(labels.flatten(), minlength=k)
        order = np.argsort(-counts)
        palettes.append((a / fps, b / fps, [(tuple(int(c) for c in centers[j][::-1]), float(counts[j] / counts.sum())) for j in order]))

    # audio hits, if there's a soundtrack
    audio = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-vn', '-ac', '2', '-ar', '44100', tmp], capture_output=True)
        if r.returncode == 0 and os.path.getsize(tmp) > 1000:
            import listen
            x, sr = listen.load(tmp)
            y = listen.to_analysis_rate(x, sr)
            onset, ot = listen.onset_curve(y)
            bpm, beats, conf = listen.tempo_and_beats(onset)
            audio = {'onset': onset, 'ot': ot, 'beats': ot[beats] if len(beats) else np.array([]), 'bpm': bpm, 'conf': conf}
        os.unlink(tmp)
    except Exception as e:  # audio is a bonus; never fail the look on it
        audio = None

    sync = None
    if audio is not None and cuts:
        from scipy.signal import find_peaks
        pk, _ = find_peaks(audio['onset'], height=0.3, distance=4)
        hit_t = audio['ot'][pk]
        offs = []
        for c in cuts:
            t = c / fps
            if len(hit_t):
                j = int(np.argmin(np.abs(hit_t - t)))
                offs.append(t - hit_t[j])
        offs = np.array(offs)
        near = np.abs(offs) <= 0.2          # a cut more than 200 ms from any hit isn't "late", it's cut to nothing
        sync = {'median_offset_ms': float(np.median(offs[near]) * 1000) if near.any() else float('nan'),
                'on_hit': int(np.sum(np.abs(offs) <= 1.5 / fps)), 'total': len(offs), 'near': int(near.sum()),
                'off': [(cuts[i] / fps, float(offs[i] * 1000)) for i in range(len(offs)) if near[i] and abs(offs[i]) > 2.5 / fps],
                'unrelated': [cuts[i] / fps for i in range(len(offs)) if not near[i]]}

    return dict(path=path, fps=fps, size=(W, H), n=n, dur=dur, mean_lum=mean_lum, motion=motion, histd=histd, cuts=cuts,
                flash_worst=worst, flash_at=worst_at, black=black, frozen=frozen, palettes=palettes, audio=audio, sync=sync)


def words(r):
    W, H = r['size']
    fps, dur = r['fps'], r['dur']
    cuts = r['cuts']
    lines = [f"{os.path.basename(r['path'])}: {W}x{H} {'vertical' if H > W else 'horizontal' if W > H else 'square'}, {fps:.0f} fps, {dur:.1f} s, {r['n']} frames"]
    shots = np.diff([0] + [c / fps for c in cuts] + [dur])
    lines.append(f"{len(cuts)} cuts, {len(shots)} shots, average shot {np.mean(shots):.2f} s (shortest {np.min(shots):.2f}, longest {np.max(shots):.2f})")
    m = r['motion']
    busy = np.percentile(m, 75)
    lines.append(f"motion: median {np.median(m) * 100:.2f}, 75th pct {busy * 100:.2f} (per-frame change, % of full scale); "
                 f"{'very busy' if busy > 0.03 else 'lively' if busy > 0.01 else 'calm' if busy > 0.002 else 'mostly still'}")
    L = r['mean_lum']
    lines.append(f"brightness: mean {L.mean():.2f}, range {L.min():.2f}–{L.max():.2f} (perceptual lightness 0–1; typical video sits around 0.3–0.5)"
                 + ("  (very dark: hard to see on a phone outdoors)" if L.mean() < 0.12 else ""))
    if r['audio'] is not None:
        a = r['audio']
        lines.append(f"soundtrack: {a['bpm']:.1f} BPM (confidence {a['conf']:.2f})")
    if r['sync'] is not None:
        s = r['sync']
        lines.append(f"cuts vs audio hits: {s['on_hit']}/{s['total']} cuts land within 1.5 frames of a hit; median offset {s['median_offset_ms']:+.0f} ms over the {s['near']} cuts near a hit (+ means picture late)")
        if s['unrelated']:
            lines.append(f"  {len(s['unrelated'])} cut(s) with no hit within 200 ms: " + ', '.join(f'{t:.2f}s' for t in s['unrelated'][:10]))
    lines.append('')
    lines.append('shots:')
    for a, b, pal in r['palettes']:
        cols = ' '.join('#%02x%02x%02x %2.0f%%' % (c[0], c[1], c[2], p * 100) for c, p in pal[:4])
        lines.append(f"  {a:6.2f}–{b:6.2f}s  {cols}")
    warn = []
    if r['flash_worst'] > 3:
        warn.append(f"FLASHING: {r['flash_worst']} large flashes within one second near {r['flash_at']:.1f}s, over the WCAG 2.3.1 limit of 3 (seizure risk)")
    elif r['flash_worst'] == 3:
        warn.append(f"flashing at the limit: 3 large flashes in one second near {r['flash_at']:.1f}s")
    if r['black']:
        warn.append(f"{len(r['black'])} black frame(s), first at {r['black'][0] / fps:.2f}s")
    for a, b in r['frozen']:
        warn.append(f"no movement {a:.1f}–{b:.1f}s ({b - a:.1f}s): a hold, or a freeze?")
    if r['sync'] and r['sync']['off']:
        offs = ', '.join(f'{t:.2f}s ({ms:+.0f} ms)' for t, ms in r['sync']['off'][:8])
        warn.append(f"cuts off the beat by more than 2.5 frames: {offs}")
    if warn:
        lines.append('')
        lines.append('look out for:')
        lines += ['  - ' + w for w in warn]
    return '\n'.join(lines)


def picture(r, out_png, frames=24, title=''):
    path, fps, n, dur = r['path'], r['fps'], r['n'], r['dur']
    W, H = r['size']
    # which frames: every cut (a frame just after it), then fill evenly
    pick = set(min(n - 1, c + 1) for c in r['cuts'])
    k = max(frames - len(pick), 4)
    for t in np.linspace(0, n - 1, k):
        pick.add(int(t))
    pick = sorted(pick)
    if len(pick) > frames * 2:
        pick = pick[:: max(1, len(pick) // (frames * 2))]
    cols = 8 if H > W else 6
    tw = 200 if H > W else 300
    th = int(tw * H / W)
    rows = (len(pick) + cols - 1) // cols
    pad, lab = 6, 22
    sheet_h = rows * (th + lab + pad) + pad
    strip_h = 5 * 46 + 20
    total_w = cols * (tw + pad) + pad
    img = Image.new('RGB', (total_w, 40 + sheet_h + strip_h), (18, 18, 18))
    d = ImageDraw.Draw(img)
    f13, f16 = font(13), font(16)
    d.text((pad, 10), title, font=f16, fill=(240, 240, 240))
    cutset = set(min(n - 1, c + 1) for c in r['cuts'])
    cap = cv2.VideoCapture(path)
    for i, fi in enumerate(pick):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, fr = cap.read()
        if not ok:
            continue
        im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((tw, th), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad)
        y = 40 + pad + (i // cols) * (th + lab + pad)
        img.paste(im, (x, y + lab))
        is_cut = fi in cutset
        d.text((x + 2, y + 3), f'{fi / fps:6.2f}s' + ('  CUT' if is_cut else ''), font=f13, fill=(255, 200, 0) if is_cut else (200, 200, 200))
    cap.release()

    # timeline strips
    y0 = 40 + sheet_h + 10
    x0, x1 = pad + 90, total_w - pad
    def tx(t): return x0 + (x1 - x0) * t / dur
    def strip(label, yy, series=None, color=(120, 200, 255), norm=None, fill=False):
        d.rectangle([x0, yy, x1, yy + 38], outline=(70, 70, 70))
        d.text((pad, yy + 12), label, font=f13, fill=(200, 200, 200))
        if series is not None:
            s = np.asarray(series, float)
            mx = norm or (s.max() + 1e-9)
            pts = [(tx(i / len(s) * dur), yy + 38 - 36 * min(1, v / mx)) for i, v in enumerate(s)]
            if fill:
                d.polygon([(x0, yy + 38)] + pts + [(x1, yy + 38)], fill=tuple(int(c * 0.6) for c in color))
            d.line(pts, fill=color, width=1)
    strip('motion', y0, r['motion'], (120, 200, 255), fill=True)
    strip('brightness', y0 + 46, r['mean_lum'], (255, 220, 120), norm=0.6, fill=True)
    strip('cuts', y0 + 92)
    for c in r['cuts']:
        d.line([(tx(c / fps), y0 + 92), (tx(c / fps), y0 + 130)], fill=(255, 200, 0), width=2)
    strip('palette', y0 + 138)
    for a, b, pal in r['palettes']:
        yy = y0 + 139
        for c, p in pal:
            h = max(1, int(37 * p))
            d.rectangle([tx(a), yy, max(tx(a) + 1, tx(b) - 1), yy + h], fill=c)
            yy += h
    if r['audio'] is not None:
        a = r['audio']
        strip('audio hits', y0 + 184, a['onset'], (160, 255, 160))
        for bt in a['beats']:
            d.line([(tx(bt), y0 + 184), (tx(bt), y0 + 190)], fill=(255, 90, 90), width=1)
        for c in r['cuts']:
            d.line([(tx(c / fps), y0 + 184), (tx(c / fps), y0 + 222)], fill=(255, 200, 0), width=1)
    for s in range(0, int(dur) + 1, 1 if dur <= 40 else 5):
        d.line([(tx(s), y0 + 228), (tx(s), y0 + 232)], fill=(150, 150, 150))
        d.text((tx(s) - 6, y0 + 233), str(s), font=f13, fill=(150, 150, 150))
    img.save(out_png)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('--out', default='.')
    ap.add_argument('--frames', type=int, default=24)
    ap.add_argument('--at', default='')
    ap.add_argument('--name')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    name = a.name or os.path.splitext(os.path.basename(a.file))[0]
    base = os.path.join(a.out, name)
    r = analyse(a.file)
    text = words(r)
    open(base + '.look.txt', 'w').write(text + '\n')
    W, H = r['size']
    picture(r, base + '.look.png', a.frames, f"{name}   {W}x{H}   {r['dur']:.1f}s   {len(r['cuts'])} cuts")
    for t in [float(v) for v in a.at.split(',') if v.strip()]:
        fr = grab(a.file, t)
        if fr is not None:
            Image.fromarray(fr).save(f'{base}.at-{t:.2f}.png')
    print(text)
    print(f'\nwrote {base}.look.txt and {base}.look.png')


if __name__ == '__main__':
    main()
