"""thumbcheck.py: score a History_Unfoldz thumbnail out of 100. Pass = 80 or higher.

The rules come from how high-CTR animated history thumbnails are built (OverSimplified, Kings and
Generals, Simple History, Armchair Historian) and the 2026 CTR studies in docs/youtube-growth-2026.md:
a big emotional character, off-center, a simple dark ground, 1-4 heavy words that add to the title,
one hot accent color, readable at phone size, and nothing under YouTube's timestamp.

Every check is measured on the real pixels (at 1280x720 and at a 320x180 phone preview). compose.py
writes the layer masks (character, text) next to each thumbnail so the checks know what is what.

  python3 thumbcheck.py thumb.jpg --title "The 5 Minutes That Won the Pacific War | The Battle of Midway"
  -> prints each check, its points, the total, PASS/FAIL, and what to fix.
"""
import argparse, json, os, re
import numpy as np
from PIL import Image, ImageFilter

STOP = {'the', 'a', 'an', 'of', 'that', 'and', 'to', 'in', 'on', 'at', 'for', 'is', 'it', 'his', 'her', 'their', 'how', 'why'}


def lum(a):  # relative luminance 0-1 from sRGB uint8
    a = a / 255.0
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def contrast(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def ramp(v, bad, good):  # 0 at bad, 1 at good, linear between
    if good == bad: return 1.0
    return float(min(1, max(0, (v - bad) / (good - bad))))


def load_mask(path, size):
    if not path or not os.path.exists(path): return None
    return np.array(Image.open(path).convert('L').resize(size)) > 127


def check(img_path, title='', meta=None):
    meta = meta or {}
    im = Image.open(img_path).convert('RGB').resize((1280, 720))
    a = np.array(im).astype(np.float64)
    small = np.array(im.resize((320, 180), Image.LANCZOS)).astype(np.float64)
    L, Ls = lum(a), lum(small)
    base = img_path.rsplit('.', 1)[0]
    char = load_mask(meta.get('char_mask') or base + '.char.png', (1280, 720))
    text = load_mask(meta.get('text_mask') or base + '.text.png', (1280, 720))
    words = meta.get('words', [])
    R = []  # (name, got, max, note)

    # 1. A character, big (top channels: one face filling 25-45% of the frame)
    if char is None or char.sum() == 0:
        R.append(('Character, big', 0, 20, 'no character: add a painted close-up (biggest single CTR factor)'))
    else:
        share = char.mean(); ys = np.where(char.any(1))[0]; hgt = (ys.max() - ys.min()) / 720
        pts = 20 * min(ramp(share, 0.08, 0.22), ramp(hgt, 0.45, 0.85)) * (1 if share <= 0.55 else ramp(0.75 - share, 0, 0.2))
        R.append(('Character, big', pts, 20, f'{share:.0%} of frame, {hgt:.0%} tall (want 22-55%, 85%+ tall)'))
        # 2. Off-center
        cx = np.where(char.any(0))[0].mean() / 1280
        R.append(('Character off-center', 5 * ramp(abs(cx - 0.5), 0.05, 0.18), 5, f'center at {cx:.0%} across (want outside 32-68%)'))

    # 3. Words: 1-4, adding to the title instead of repeating it
    n = len(' '.join(words).split())
    R.append(('1-4 words', 8 if 1 <= n <= 4 else (4 if n == 5 else 0), 8, f'{n} words'))
    tw = {w for w in re.findall(r"[a-z0-9']+", title.lower()) if w not in STOP}
    ww = {w for w in re.findall(r"[a-z0-9']+", ' '.join(words).lower()) if w not in STOP}
    rep = len(tw & ww)
    R.append(('Adds to the title', 7 * (1 - min(1, rep / max(1, len(ww)))) if ww else 0, 7, f'repeats {sorted(tw & ww) or "nothing"}'))

    # 4. Readable at phone size: letter height and contrast against what's behind
    if text is not None and text.sum():
        ts = np.array(Image.fromarray(text.astype(np.uint8) * 255).resize((320, 180))) > 127
        rows = np.where(ts.any(1))[0]; runs = np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)
        smallest = min(len(r) for r in runs)
        ring = np.array(Image.fromarray(text.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(41))) > 127
        around = ring & ~text & ~(np.array(Image.fromarray(text.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(13))) > 127)
        fill = meta.get('text_lum')  # fill colour luminance from compose; else brightest text pixels
        tl = fill if fill is not None else float(np.percentile(L[text], 90))
        bl = float(np.median(L[around])) if around.any() else float(L.mean())
        cr = contrast(tl, bl)
        R.append(('Letters big at 320 px', 7 * ramp(smallest, 9, 18), 7, f'smallest line {smallest}px tall at 320 wide (want 18+)'))
        R.append(('Text contrast', 8 * ramp(cr, 3, 7), 8, f'{cr:.1f}:1 against what is behind it (want 7+)'))
        br = np.zeros_like(text); br[int(720 * 0.80):, int(1280 * 0.80):] = True
        R.append(('Clear of timestamp', 5 if not (text & br).any() else 0, 5, 'bottom-right corner is covered by YouTube'))
    else:
        R += [('Letters big at 320 px', 0, 7, 'no text mask'), ('Text contrast', 0, 8, 'no text mask'), ('Clear of timestamp', 5, 5, 'no text')]

    # 5. Overall punch at phone size (RMS contrast)
    rms = float(Ls.std())
    R.append(('Punchy contrast', 10 * ramp(rms, 0.12, 0.24), 10, f'RMS {rms:.2f} at 320 px (want 0.24+)'))

    # 6. Color: saturated, with a hot accent (red/orange/yellow) somewhere
    hsv = np.array(im.convert('HSV')).astype(np.float64) / 255
    sat = float(hsv[..., 1][hsv[..., 2] > 0.15].mean())
    hot = float((((hsv[..., 0] < 0.13) | (hsv[..., 0] > 0.95)) & (hsv[..., 1] > 0.55) & (hsv[..., 2] > 0.5)).mean())
    R.append(('Color pop', 4 * ramp(sat, 0.2, 0.42) + 4 * ramp(hot, 0.01, 0.05), 8, f'saturation {sat:.2f} (want .42+), hot accent {hot:.1%} (want 5%+)'))

    # 7. Stands out in the feed (YouTube light #ffffff and dark #0f0f0f), measured on the outer edge
    edge = np.concatenate([Ls[:8].ravel(), Ls[-8:].ravel(), Ls[:, :8].ravel(), Ls[:, -8:].ravel()])
    em = float(np.mean(edge)); d = min(abs(contrast(em, 1.0)), contrast(em, lum(np.array([15, 15, 15.0]))))
    R.append(('Stands out in feed', 10 * ramp(d, 1.3, 2.5) if d else 0, 10, f'edge vs light/dark feed {d:.1f}:1 (want 2.5+ against both)'))

    # 8. Simple background: few busy edges outside the character and text
    g = np.array(im.convert('L').resize((320, 180)).filter(ImageFilter.FIND_EDGES)) > 40
    keep = np.ones_like(g)
    for m in (char, text):
        if m is not None: keep &= ~(np.array(Image.fromarray(m.astype(np.uint8) * 255).resize((320, 180)).filter(ImageFilter.MaxFilter(5))) > 127)
    busy = float(g[keep].mean()) if keep.any() else 0
    R.append(('Simple background', 10 * ramp(0.16 - busy, 0, 0.1), 10, f'{busy:.1%} busy edges (want under 6%)'))

    # 9. One key word in the accent color
    R.append(('Red key word', 2 if meta.get('red_word') else 0, 2, ''))

    total = sum(r[1] for r in R)
    return total, R


def report(path, title, meta):
    total, R = check(path, title, meta)
    out = [f'{os.path.basename(path)}: {total:.0f}/100  {"PASS" if total >= 80 else "FAIL"}']
    for name, got, mx, note in R:
        flag = '  ' if got >= mx * 0.8 else '->'
        out.append(f' {flag} {name:24s} {got:5.1f}/{mx:<3d} {note}')
    return total, '\n'.join(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('images', nargs='+'); ap.add_argument('--title', default='')
    a = ap.parse_args()
    for p in a.images:
        mp = p.rsplit('.', 1)[0] + '.meta.json'
        meta = json.load(open(mp)) if os.path.exists(mp) else {}
        print(report(p, a.title or meta.get('title', ''), meta)[1])
