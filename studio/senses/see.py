#!/usr/bin/env python3
"""see: look at a picture the way painters and designers do, not pixel by pixel.

    python3 studio/senses/see.py image.png [--out dir] [--name label]

The checks artists actually use:
  squint      blur and reduce to 3 values (dark / mid / light). A strong picture reads as a few clear shapes.
  thumbnail   shrink to 64 px wide. If it doesn't read there, it won't read in a feed.
  eye path    where attention lands first (a saliency model: spectral residual + colour and lightness contrast),
              how concentrated it is (one clear focal point vs. everything shouting), and where that sits
              against the thirds.
  balance     where the visual weight's centre is, left/right and top/bottom.
  colour      the palette in a perceptual space (OKLab), drawn on a hue wheel; the harmony it forms
              (monochrome, analogous, complementary, triadic...), warm/cool split, how much is calm vs. loud.
  detail      how busy it is (edge density) and how much quiet space it leaves.

Writes <name>.see.png (original | squint | eye map | thumbnail | colour wheel) and <name>.see.txt.
Numbers, then plain notes. Taste stays mine; this makes sure I'm looking at the right things.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


# ----------------------------------------------------------------------------- colour science
def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_oklab(rgb):
    """rgb in 0..1, shape (..., 3) -> OKLab (L 0..1, a, b)."""
    l = srgb_to_linear(rgb)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    lms = np.cbrt(l @ M1.T)
    return lms @ M2.T


def lch(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    return L, np.hypot(a, b), (np.degrees(np.arctan2(b, a)) + 360) % 360


def font(size):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


# ----------------------------------------------------------------------------- the looks
def kmeans(x, k, iters=25, seed=0):
    rng = np.random.default_rng(seed)
    c = x[rng.choice(len(x), k, replace=False)]
    for _ in range(iters):
        d = ((x[:, None, :] - c[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            if np.any(lab == j):
                c[j] = x[lab == j].mean(0)
    return c, lab


def gaussian(img2d, sigma):
    im = Image.fromarray((np.clip(img2d, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(sigma))).astype(float) / 255


def saliency(L, lab):
    """Where the eye goes: spectral residual (what's unexpected in the image's own structure) plus
    lightness and colour contrast against the surroundings, with a mild pull toward the centre."""
    h, w = L.shape
    small = np.asarray(Image.fromarray((L * 255).astype(np.uint8)).resize((64, max(8, int(64 * h / w))), Image.BILINEAR)).astype(float) / 255
    F = np.fft.fft2(small)
    logA = np.log(np.abs(F) + 1e-9)
    ph = np.angle(F)
    k = np.ones((3, 3)) / 9
    from scipy.signal import convolve2d
    resid = logA - convolve2d(logA, k, mode='same', boundary='wrap')
    sr = np.abs(np.fft.ifft2(np.exp(resid + 1j * ph))) ** 2
    sr = np.asarray(Image.fromarray((sr / (sr.max() + 1e-12) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(float) / 255
    sr = gaussian(sr, max(2, w / 60))
    # local contrast: difference from a heavily blurred version (lightness and colour)
    Lb = gaussian(L, w / 12)
    ab = np.hypot(lab[..., 1], lab[..., 2])
    ca = gaussian(np.clip(lab[..., 1] + 0.5, 0, 1), w / 12) - 0.5
    cb = gaussian(np.clip(lab[..., 2] + 0.5, 0, 1), w / 12) - 0.5
    cc = np.hypot(lab[..., 1] - ca, lab[..., 2] - cb)
    lc = np.abs(L - Lb)
    con = gaussian(np.clip(lc * 2.2 + cc * 3 + ab * 0.8, 0, 1), max(2, w / 80))
    yy, xx = np.mgrid[0:h, 0:w]
    centre = np.exp(-(((xx - w / 2) / (w * 0.6)) ** 2 + ((yy - h / 2) / (h * 0.6)) ** 2))
    # people read: dense clusters of fine, high-contrast strokes (lettering) pull the eye harder than raw contrast
    gx = np.abs(np.diff(L, axis=1, append=L[:, -1:])); gy = np.abs(np.diff(L, axis=0, append=L[-1:, :]))
    fine = (np.hypot(gx, gy) > 0.12).astype(float)
    dens = gaussian(fine, max(2, w / 70))
    wide = gaussian(fine, w / 8)
    texty = np.clip(dens - 1.3 * wide, 0, None)           # dense locally, but not everywhere (noise is dense everywhere)
    texty = texty / (texty.max() + 1e-9) if texty.max() > 0.02 else texty * 0
    s = (0.35 * sr / (sr.max() + 1e-9) + 0.40 * con / (con.max() + 1e-9) + 0.35 * texty) * (0.75 + 0.25 * centre)
    return s / (s.max() + 1e-9)


def peaks(s, n=3, min_dist=0.15):
    h, w = s.shape
    s = s.copy()
    out = []
    for _ in range(n):
        i = np.argmax(s)
        y, x = divmod(i, w)
        if s[y, x] < 0.25:
            break
        out.append((x / w, y / h, float(s[y, x])))
        yy, xx = np.mgrid[0:h, 0:w]
        s[((xx - x) / w) ** 2 + ((yy - y) / h) ** 2 < min_dist ** 2] = 0
    return out


def harmony(hues, chromas, shares):
    """Name the colour scheme from the chromatic palette entries (hue clusters, weighted by share)."""
    chrom = [(h, c, s) for h, c, s in zip(hues, chromas, shares) if c > 0.035 and s > 0.02]
    if not chrom:
        return 'achromatic (greys)', []
    hs = sorted(h for h, _, _ in chrom)
    clusters = [[hs[0]]]
    for h in hs[1:]:
        if h - clusters[-1][-1] <= 35:
            clusters[-1].append(h)
        else:
            clusters.append([h])
    if len(clusters) > 1 and (hs[0] + 360) - clusters[-1][-1] <= 35:
        clusters[0] = clusters[-1] + clusters[0]; clusters.pop()
    centres = [(np.degrees(np.angle(np.mean(np.exp(1j * np.radians(c))))) + 360) % 360 for c in clusters]
    span = max(hs) - min(hs) if len(clusters) == 1 else None
    def gap(a, b): d = abs(a - b) % 360; return min(d, 360 - d)
    if len(clusters) == 1:
        return ('monochromatic' if (span or 0) < 15 else 'analogous'), centres
    if len(clusters) == 2:
        g = gap(*centres)
        if g > 150: return 'complementary', centres
        if g < 75: return 'analogous', centres
        return 'two-colour (split)', centres
    if len(clusters) == 3:
        gs = sorted([gap(centres[0], centres[1]), gap(centres[1], centres[2]), gap(centres[0], centres[2])])
        if all(90 <= g <= 150 for g in gs): return 'triadic', centres
        if gs[-1] > 150: return 'split-complementary', centres
        return 'three hues', centres
    return f'{len(clusters)} hues (varied)', centres


def analyse(path):
    im = Image.open(path).convert('RGB')
    W0, H0 = im.size
    s = 640 / max(W0, H0)
    im = im.resize((max(1, int(W0 * s)), max(1, int(H0 * s))), Image.LANCZOS)
    rgb = np.asarray(im).astype(float) / 255
    lab = to_oklab(rgb)
    L = lab[..., 0]
    h, w = L.shape

    # squint: blur, then 3 values
    Ls = gaussian(L, max(3, w / 45))
    q = np.percentile(Ls, [2, 98])
    cents, labels = kmeans(Ls.reshape(-1, 1), 3, seed=1)
    order = np.argsort(cents[:, 0])
    rank = np.empty(3, int); rank[order] = np.arange(3)
    vmap = rank[labels].reshape(h, w)
    vshare = [float(np.mean(vmap == k)) for k in range(3)]
    vcent = sorted(float(c[0]) for c in cents)
    value_range = float(q[1] - q[0])
    value_sep = min(vcent[1] - vcent[0], vcent[2] - vcent[1])

    # thumbnail
    tw = 64
    th = max(1, int(tw * h / w))
    thumb = im.resize((tw, th), Image.LANCZOS)
    tL = to_oklab(np.asarray(thumb).astype(float) / 255)[..., 0]
    thumb_contrast = float(np.std(tL))

    # eye
    sal = saliency(L, lab)
    flat = np.sort(sal.ravel())[::-1]
    focus = float(flat[:max(1, len(flat) // 10)].sum() / (flat.sum() + 1e-9))   # share of attention in the top 10% of area
    pts = peaks(sal)
    thirds = [(a, b) for a in (1 / 3, 2 / 3) for b in (1 / 3, 2 / 3)]
    def near_third(p): return min(np.hypot(p[0] - a, p[1] - b) for a, b in thirds)
    # balance
    yy, xx = np.mgrid[0:h, 0:w]
    wgt = sal ** 1.5
    cx, cy = float((wgt * xx).sum() / wgt.sum() / w), float((wgt * yy).sum() / wgt.sum() / h)

    # colour
    px = lab.reshape(-1, 3)
    sub = px[np.random.default_rng(0).choice(len(px), min(20000, len(px)), replace=False)]
    pc, pl = kmeans(sub.copy(), 6, seed=2)
    share = np.bincount(pl, minlength=6) / len(pl)
    Lp, Cp, Hp = lch(pc)
    idx = np.argsort(-share)
    palette = [(pc[i], float(share[i]), float(Lp[i]), float(Cp[i]), float(Hp[i])) for i in idx]
    scheme, centres = harmony(Hp[idx], Cp[idx], share[idx])
    Lall, Call, Hall = lch(lab)
    chromatic = Call > 0.04
    warm = np.mean(((Hall < 100) | (Hall > 330)) & chromatic)
    cool = np.mean((Hall > 150) & (Hall < 300) & chromatic)
    loud = float(np.mean(Call > 0.15))
    # detail
    gx = np.abs(np.diff(L, axis=1, append=L[:, -1:]))
    gy = np.abs(np.diff(L, axis=0, append=L[-1:, :]))
    edges = (np.hypot(gx, gy) > 0.06)
    edge_density = float(edges.mean())
    quiet = float(np.mean((gaussian(edges.astype(float), w / 40) < 0.02) & (sal < 0.25)))

    return dict(path=path, size=(W0, H0), img=im, L=L, vmap=vmap, vshare=vshare, vcent=vcent, value_range=value_range,
                value_sep=value_sep, thumb=thumb, thumb_contrast=thumb_contrast, sal=sal, focus=focus, points=pts,
                near_third=[near_third(p) for p in pts], balance=(cx, cy), palette=palette, scheme=scheme, hue_centres=centres,
                warm=float(warm), cool=float(cool), loud=loud, edge_density=edge_density, quiet=quiet, mean_L=float(L.mean()))


def words(r):
    W, H = r['size']
    out = [f"{os.path.basename(r['path'])}: {W}x{H}"]
    names = ['dark', 'mid', 'light']
    out.append(f"values (squinting): {', '.join(f'{n} {s * 100:.0f}%' for n, s in zip(names, r['vshare']))}; "
               f"lightness spread {r['value_range']:.2f}, gap between value groups {r['value_sep']:.2f}; mean lightness {r['mean_L']:.2f}")
    out.append(f"thumbnail (64 px) contrast {r['thumb_contrast']:.3f}")
    fp = ', '.join(f"({x:.2f}, {y:.2f})" for x, y, _ in r['points'])
    out.append(f"eye: {r['focus'] * 100:.0f}% of attention falls in the top 10% of the area; focal points at {fp or 'none'} (x, y as fractions)")
    cx, cy = r['balance']
    out.append(f"balance: visual weight centred at ({cx:.2f}, {cy:.2f}); {'left' if cx < 0.45 else 'right' if cx > 0.55 else 'centred'}-weighted, "
               f"{'top' if cy < 0.45 else 'bottom' if cy > 0.55 else 'middle'}")
    out.append(f"colour: {r['scheme']}; warm {r['warm'] * 100:.0f}% / cool {r['cool'] * 100:.0f}% of the area; {r['loud'] * 100:.0f}% strongly saturated")
    out.append('  palette: ' + '  '.join(f"L{L:.2f} C{C:.2f} h{h:3.0f}° {s * 100:.0f}%" for _, s, L, C, h in r['palette']))
    out.append(f"detail: edges on {r['edge_density'] * 100:.1f}% of pixels; quiet space {r['quiet'] * 100:.0f}%")

    notes = []
    if r['value_sep'] < 0.08 or r['value_range'] < 0.25:
        notes.append('values are too close together: squinting, it goes to one grey soup. Push darks darker or lights lighter.')
    if max(r['vshare']) < 0.45:
        notes.append('no dominant value: dark, mid and light share the picture evenly, which tends to read as busy. Let one value family own ~50–70%.')
    if r['thumb_contrast'] < 0.06:
        notes.append("at thumbnail size there's almost no contrast; it won't read in a feed.")
    if r['focus'] < 0.25:
        notes.append('no clear focal point: attention is spread thin. Make one area clearly the loudest (contrast, colour, detail).')
    elif len(r['points']) >= 2 and r['points'][1][2] > 0.9 * r['points'][0][2]:
        notes.append('two areas compete for first look at nearly equal strength.')
    if r['points'] and r['near_third'][0] > 0.2 and abs(r['points'][0][0] - 0.5) < 0.08 and abs(r['points'][0][1] - 0.5) < 0.08:
        notes.append('the focal point is dead centre: stable and formal. Fine on purpose; static if not.')
    cx, cy = r['balance']
    if abs(cx - 0.5) > 0.15:
        notes.append(f"heavy on the {'left' if cx < 0.5 else 'right'}; counterweight the other side or lean into it on purpose.")
    if r['loud'] > 0.5:
        notes.append('most of the picture is strongly saturated: no rest for the eye, and the accent colour has nothing to stand out from.')
    if r['edge_density'] > 0.18 and r['quiet'] < 0.15:
        notes.append('busy: lots of edges and little quiet space.')
    if r['mean_L'] < 0.25:
        notes.append(f"dark overall (mean lightness {r['mean_L']:.2f}); check it on a phone in daylight.")
    if notes:
        out.append('')
        out.append('notes:')
        out += ['  - ' + n for n in notes]
    return '\n'.join(out)


def oklab_to_srgb(lab):
    M2i = np.linalg.inv(np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]]))
    M1i = np.linalg.inv(np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]]))
    l = (np.asarray(lab) @ M2i.T) ** 3 @ M1i.T
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)


def picture(r, out_png, title=''):
    im = r['img']
    w, h = im.size
    P = 300
    sc = P / max(w, h)
    cw, ch = int(w * sc), int(h * sc)
    pad, top = 10, 60
    W = pad + 5 * (cw + pad) if w >= h else pad + 5 * (cw + pad)
    Himg = top + ch + 36 + pad
    img = Image.new('RGB', (W, Himg), (18, 18, 18))
    d = ImageDraw.Draw(img)
    f14, f16 = font(13), font(16)
    d.text((pad, 10), title, font=f16, fill=(235, 235, 235))

    def put(i, pic, label):
        x = pad + i * (cw + pad)
        img.paste(pic.resize((cw, ch), Image.LANCZOS), (x, top))
        d.text((x, top - 20), label, font=f14, fill=(200, 200, 200))
        return x

    put(0, im, 'original')
    vals = np.array([[25, 25, 25], [128, 128, 128], [235, 235, 235]], np.uint8)[r['vmap']]
    put(1, Image.fromarray(vals), 'squint')
    hm = r['sal']
    heat = np.stack([np.clip(hm * 2, 0, 1), np.clip(hm * 1.6 - 0.3, 0, 1), np.clip(1 - hm * 3, 0, 1) * 0.35], -1)
    base = np.asarray(im.convert('L').convert('RGB')).astype(float) / 255 * 0.35
    x2 = put(2, Image.fromarray(((base + heat * 0.8).clip(0, 1) * 255).astype(np.uint8)), 'eye map')
    for a in (1 / 3, 2 / 3):
        d.line([(x2 + a * cw, top), (x2 + a * cw, top + ch)], fill=(90, 90, 90))
        d.line([(x2, top + a * ch), (x2 + cw, top + a * ch)], fill=(90, 90, 90))
    for k, (px_, py_, s) in enumerate(r['points']):
        X, Y = x2 + px_ * cw, top + py_ * ch
        rr = 14 - 3 * k
        d.ellipse([X - rr, Y - rr, X + rr, Y + rr], outline=(255, 255, 255), width=2)
        d.text((X + rr + 2, Y - 8), str(k + 1), font=f14, fill=(255, 255, 255))
    bx, by = r['balance']
    X, Y = x2 + bx * cw, top + by * ch
    d.line([(X - 8, Y), (X + 8, Y)], fill=(0, 255, 255), width=2); d.line([(X, Y - 8), (X, Y + 8)], fill=(0, 255, 255), width=2)
    put(3, r['thumb'].resize((cw, ch), Image.NEAREST), 'thumbnail (64 px)')
    # colour wheel
    x4 = pad + 4 * (cw + pad)
    R = min(cw, ch) / 2 - 12
    cx0, cy0 = x4 + cw / 2, top + ch / 2
    for a in range(0, 360, 3):
        rgb = oklab_to_srgb([0.72, 0.12 * np.cos(np.radians(a)), 0.12 * np.sin(np.radians(a))])
        d.pieslice([cx0 - R, cy0 - R, cx0 + R, cy0 + R], a, a + 3, fill=tuple(int(v * 255) for v in rgb))
    d.ellipse([cx0 - R * 0.82, cy0 - R * 0.82, cx0 + R * 0.82, cy0 + R * 0.82], fill=(30, 30, 30))
    for c, s, L, C, hdeg in r['palette']:
        rad = min(1, C / 0.3) * R * 0.8
        X, Y = cx0 + rad * np.cos(np.radians(hdeg)), cy0 + rad * np.sin(np.radians(hdeg))
        rr = 4 + 22 * np.sqrt(s)
        col = tuple(int(v * 255) for v in oklab_to_srgb(c))
        d.ellipse([X - rr, Y - rr, X + rr, Y + rr], fill=col, outline=(240, 240, 240))
    d.text((x4, top - 20), 'hue wheel', font=f14, fill=(200, 200, 200))
    # palette bar
    x = pad
    for c, s, *_ in r['palette']:
        wbar = int(s * (W - 2 * pad))
        d.rectangle([x, top + ch + 10, x + wbar, top + ch + 28], fill=tuple(int(v * 255) for v in oklab_to_srgb(c)))
        x += wbar
    img.save(out_png)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('--out', default='.')
    ap.add_argument('--name')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    name = a.name or os.path.splitext(os.path.basename(a.file))[0]
    base = os.path.join(a.out, name)
    r = analyse(a.file)
    text = words(r)
    open(base + '.see.txt', 'w').write(text + '\n')
    picture(r, base + '.see.png', f"{name}   {r['scheme']}   focus {r['focus'] * 100:.0f}%")
    print(text)
    print(f'\nwrote {base}.see.txt and {base}.see.png')


if __name__ == '__main__':
    main()
