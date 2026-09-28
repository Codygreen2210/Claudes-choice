#!/usr/bin/env python3
"""explore: make many versions of an idea at once, see them side by side, keep the surprising ones, breed them.

My habit is to take the first reasonable idea and polish it. This fights that: an idea becomes a set of
knobs (a "space"), and each generation is a spread of different settings (genomes) rendered into one sheet
I can take in at a glance. Then I pick, and the next generation mutates and crosses the picks.

Visual (any page built on kit.js that reads K.genome()):
    python3 studio/explore/explore.py page.html --space space.json --n 16 --t 1.5,4 --size 360x640 --out runs/a
    python3 studio/explore/explore.py page.html --space space.json --from runs/a --pick 3,11 --n 16 --out runs/b

Sound (a Python function that turns a genome into audio):
    from studio.explore import explore
    explore.sound(make, space, n=12, out='runs/s1')      # make(genome, seconds) -> stereo array

A space is JSON: {"hue": [0, 360], "speed": [0.5, 3], "shape": ["circle", "square", "line"], "seed": "int"}
  [lo, hi] numbers -> continuous, a list of strings -> choice, "int" -> random integer seed.
Outputs: sheet.png (every variant, numbered), genomes.json (to breed from), and for sound a reel.wav
(every variant back to back, 0.5 s apart) plus each variant's listen picture.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def font(size):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


# ----------------------------------------------------------------------------- genomes
def sample(space: dict, rnd: random.Random) -> dict:
    g = {}
    for k, v in space.items():
        if v == 'int':
            g[k] = rnd.randrange(1, 10 ** 6)
        elif isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v) and len(v) == 2:
            lo, hi = v
            g[k] = rnd.randint(lo, hi) if isinstance(lo, int) and isinstance(hi, int) and not isinstance(lo, bool) and k.endswith('_n') else lo + (hi - lo) * rnd.random()
        elif isinstance(v, list):
            g[k] = rnd.choice(v)
        else:
            g[k] = v
    return g


def spread(space: dict, n: int, seed: int = 1) -> list[dict]:
    """n genomes that cover the space: Latin-hypercube for the numbers, so no two variants are near-twins."""
    rnd = random.Random(seed)
    out = [sample(space, rnd) for _ in range(n)]
    for k, v in space.items():
        if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            lo, hi = v
            slots = list(range(n)); rnd.shuffle(slots)
            for g, s in zip(out, slots):
                x = lo + (hi - lo) * (s + rnd.random()) / n
                g[k] = int(round(x)) if k.endswith('_n') else x
        elif isinstance(v, list) and v:
            opts = (v * (n // len(v) + 1))[:n]; rnd.shuffle(opts)
            for g, o in zip(out, opts):
                g[k] = o
    return out


def mutate(g: dict, space: dict, rnd: random.Random, amount: float = 0.25) -> dict:
    c = dict(g)
    for k, v in space.items():
        if v == 'int':
            if rnd.random() < amount:
                c[k] = rnd.randrange(1, 10 ** 6)
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            lo, hi = v
            x = c.get(k, (lo + hi) / 2) + rnd.gauss(0, amount * (hi - lo))
            x = min(hi, max(lo, x))
            c[k] = int(round(x)) if k.endswith('_n') else x
        elif isinstance(v, list) and rnd.random() < amount * 0.8:
            c[k] = rnd.choice(v)
    return c


def cross(a: dict, b: dict, rnd: random.Random) -> dict:
    return {k: (a[k] if rnd.random() < 0.5 else b[k]) for k in a}


def breed(parents: list[dict], space: dict, n: int, seed: int = 2, amount: float = 0.2) -> list[dict]:
    """Next generation: the parents themselves, then mutants and crosses of them."""
    rnd = random.Random(seed)
    out = [dict(p) for p in parents][:n]
    while len(out) < n:
        if len(parents) > 1 and rnd.random() < 0.4:
            a, b = rnd.sample(parents, 2)
            out.append(mutate(cross(a, b, rnd), space, rnd, amount * 0.5))
        else:
            out.append(mutate(rnd.choice(parents), space, rnd, amount))
    return out


# ----------------------------------------------------------------------------- sheets
def sheet(images: list[Image.Image], labels: list[str], out: str, cols: int | None = None, title: str = '', cell_w: int = 220):
    n = len(images)
    cols = cols or min(8, max(3, int(np.ceil(np.sqrt(n * 1.6)))))
    w0, h0 = images[0].size
    cw = cell_w; ch = int(cw * h0 / w0)
    lab, pad = 34, 8
    rows = (n + cols - 1) // cols
    W = pad + cols * (cw + pad)
    H = 44 + rows * (ch + lab + pad) + pad
    img = Image.new('RGB', (W, H), (16, 16, 16))
    d = ImageDraw.Draw(img)
    d.text((pad, 12), title, font=font(17), fill=(235, 235, 235))
    f13, f22 = font(12), font(22)
    for i, (im, l) in enumerate(zip(images, labels)):
        x = pad + (i % cols) * (cw + pad); y = 44 + (i // cols) * (ch + lab + pad)
        img.paste(im.convert('RGB').resize((cw, ch), Image.LANCZOS), (x, y + lab))
        d.text((x + 2, y), str(i), font=f22, fill=(255, 200, 0))
        d.text((x + 34, y + 2), l[:60], font=f13, fill=(190, 190, 190))
        if len(l) > 60:
            d.text((x + 34, y + 16), l[60:120], font=f13, fill=(150, 150, 150))
    img.save(out)
    return out


def label(g: dict) -> str:
    parts = []
    for k, v in g.items():
        if k == 'seed':
            continue
        parts.append(f'{k}={v:.2f}' if isinstance(v, float) else f'{k}={v}')
    return ' '.join(parts)


# ----------------------------------------------------------------------------- visual
def visual(page: str, space: dict, genomes: list[dict], times: list[float], size: tuple[int, int], out: str, title: str = ''):
    """Render each genome of a kit.js page at the given times; one sheet cell per genome (times side by side)."""
    os.makedirs(out, exist_ok=True)
    script = f"""
const {{ createRequire }} = require('node:module');
const req = createRequire(__filename);
let pw; for (const p of ['playwright', '/home/claude/.npm-global/lib/node_modules/playwright']) {{ try {{ pw = req(p); break }} catch (e) {{}} }}
const url = require('node:url'); const path = require('node:path');
(async () => {{
  const G = {json.dumps(genomes)}; const T = {json.dumps(times)};
  const b = await pw.chromium.launch({{ args: ['--allow-file-access-from-files'] }});
  const base = url.pathToFileURL(path.resolve({json.dumps(page)})).href;
  for (let i = 0; i < G.length; i++) {{
    const p = await b.newPage({{ viewport: {{ width: {size[0]}, height: {size[1]} }} }});
    p.on('pageerror', e => console.error('variant', i, e.message));
    await p.goto(base + '#' + encodeURIComponent(JSON.stringify(G[i])));
    await p.evaluate(async () => {{ if (window.__init) await window.__init(); if (document.fonts) await document.fonts.ready }});
    for (let k = 0; k < T.length; k++) {{
      await p.evaluate(t => window.__seek(t), T[k]);
      await p.screenshot({{ path: path.join({json.dumps(out)}, `v${{String(i).padStart(2,'0')}}_t${{k}}.png`) }});
    }}
    await p.close();
  }}
  await b.close();
}})().catch(e => {{ console.error(e); process.exit(1) }});
"""
    js = os.path.join(out, '_render.cjs')
    open(js, 'w').write(script)
    subprocess.run(['node', js], check=True)
    cells = []
    for i in range(len(genomes)):
        frames = [Image.open(os.path.join(out, f'v{i:02d}_t{k}.png')) for k in range(len(times))]
        w, h = frames[0].size
        cell = Image.new('RGB', (w * len(frames) + 6 * (len(frames) - 1), h), (16, 16, 16))
        for k, f in enumerate(frames):
            cell.paste(f, (k * (w + 6), 0))
        cells.append(cell)
    json.dump(genomes, open(os.path.join(out, 'genomes.json'), 'w'), indent=1)
    landscape = size[0] > size[1]
    cw = (420 if landscape else 220) if len(times) == 1 else min(1100, (330 if landscape else 150) * len(times))
    return sheet(cells, [label(g) for g in genomes], os.path.join(out, 'sheet.png'), title=title or f'{Path(page).name}  t={times}', cell_w=cw)


# ----------------------------------------------------------------------------- sound
def sound(make, space: dict, n: int = 12, out: str = 'explore-sound', seconds: float = 6.0, genomes: list[dict] | None = None, seed: int = 1, title: str = ''):
    """make(genome, seconds) -> stereo float array (2, n) at 44.1 kHz. Writes a reel, a sheet of listen pictures, genomes.json."""
    sys.path.insert(0, str(ROOT / 'studio' / 'senses'))
    sys.path.insert(0, str(ROOT))
    import listen
    from studio.instruments import synth as S
    os.makedirs(out, exist_ok=True)
    genomes = genomes or spread(space, n, seed)
    reel, thumbs, labels = [], [], []
    for i, g in enumerate(genomes):
        y = S.stereo(np.asarray(make(g, seconds), float))
        y = y / (np.max(np.abs(y)) + 1e-9) * 0.7
        wav = os.path.join(out, f'v{i:02d}.wav')
        S.write(wav, y)
        r = listen.analyse(wav)
        png = os.path.join(out, f'v{i:02d}.listen.png')
        listen.picture(r, png, f'#{i} ' + label(g))
        rp = os.path.join(out, f'v{i:02d}.roll.png')
        listen.roll(r, rp)
        thumbs.append(Image.open(rp))                                    # melody register, heard notes, chords
        labels.append(f"{r['tempo_bpm']:.0f}bpm {r['key']} | " + label(g))
        reel += [y, np.zeros((2, int(0.5 * S.SR)))]
    S.write(os.path.join(out, 'reel.wav'), np.concatenate(reel, axis=1))
    json.dump(genomes, open(os.path.join(out, 'genomes.json'), 'w'), indent=1)
    return sheet(thumbs, labels, os.path.join(out, 'sheet.png'), cols=3, title=title or f'{n} sound variations', cell_w=520)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('page')
    ap.add_argument('--space', required=True, help='JSON file or inline JSON')
    ap.add_argument('--n', type=int, default=16)
    ap.add_argument('--t', default='1.0', help='comma-separated times to show for each variant')
    ap.add_argument('--size', default='360x640')
    ap.add_argument('--out', required=True)
    ap.add_argument('--from', dest='frm', help='a previous run folder to breed from')
    ap.add_argument('--pick', default='', help='indices from the previous sheet to keep and breed')
    ap.add_argument('--amount', type=float, default=0.2, help='mutation strength 0..1')
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    space = json.loads(open(a.space).read() if os.path.exists(a.space) else a.space)
    if a.frm:
        prev = json.load(open(os.path.join(a.frm, 'genomes.json')))
        parents = [prev[int(i)] for i in a.pick.split(',') if i.strip()] or prev
        genomes = breed(parents, space, a.n, a.seed, a.amount)
    else:
        genomes = spread(space, a.n, a.seed)
    size = tuple(int(v) for v in a.size.split('x'))
    out = visual(a.page, space, genomes, [float(t) for t in a.t.split(',')], size, a.out)
    print(out)


if __name__ == '__main__':
    main()
