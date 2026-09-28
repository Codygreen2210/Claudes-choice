#!/usr/bin/env python3
"""motion: watch an animation the way an animator reads it: paths, spacing, speed, timing. Not single frames.

    python3 studio/senses/motion.py page.html [--from 0 --to 6] [--fps 60] [--size 1080x1080] [--out dir] [--name label]

The page is a studio __seek(t) page. It tells me what to follow in one of two ways:
  - DOM elements marked with data-track="name" (their centre, size, rotation and opacity are read each frame), or
  - window.__track(t) returning {name: {x, y, s?, r?, o?, body?}} (for canvas pages).
  Points that are parts of one figure can share a body name (data-body="..." in the DOM); when the whole figure
  is carried along (a slide, a walk), its parts moving together isn't reported as lockstep.
Optionally window.__accents = [times]: beats and hits where a sharp start or stop is intended (music-driven styles).

What it reports for each tracked thing, per move (a stretch where it's actually moving):
  ease      how it starts and stops. Starting at full speed = a jolt; stopping dead = a wall (fine for an impact,
            robotic otherwise).
  linear    constant speed through the whole move reads mechanical.
  arc       whether the path curves. Living things move in arcs; UI slides are allowed to be straight.
  overshoot whether it passes its target and settles back (follow-through): springy and alive, or sloppy if huge.
  overlap   across things: moves that start on the same frame with the same length are "lockstep", which reads
            stiff. Offsetting starts by a few frames (overlapping action) usually fixes it.
Writes <name>.motion.png: an onion-skin strobe of the frames, each path with its spacing dots (animators'
spacing chart: dots bunch up where it slows), speed curves, and a timing chart. Plus <name>.motion.txt.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

TRACK_JS = r"""
const { createRequire } = require('node:module');
const req = createRequire(__filename);
let pw; for (const p of ['playwright', '/home/claude/.npm-global/lib/node_modules/playwright']) { try { pw = req(p); break } catch (e) {} }
const url = require('node:url'); const path = require('node:path'); const fs = require('node:fs');
(async () => {
  const A = JSON.parse(process.argv[2]);
  const b = await pw.chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: A.w, height: A.h } });
  p.on('pageerror', e => console.error('page error:', e.message));
  await p.goto(url.pathToFileURL(path.resolve(A.page)).href + (A.hash || ''));
  await p.evaluate(async () => { if (window.__init) await window.__init(); if (document.fonts) await document.fonts.ready });
  const frames = [];
  const n = Math.round((A.to - A.from) * A.fps);
  for (let i = 0; i <= n; i++) {
    const t = A.from + i / A.fps;
    await p.evaluate(t => window.__seek(t), t);
    const st = await p.evaluate(t => {
      const out = {};
      if (window.__track) Object.assign(out, window.__track(t));
      for (const el of document.querySelectorAll('[data-track]')) {
        const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
        let rot = 0; const m = cs.transform;
        if (m && m !== 'none') { const v = m.match(/matrix\(([^)]+)\)/); if (v) { const [a, bb] = v[1].split(',').map(Number); rot = Math.atan2(bb, a) * 180 / Math.PI } }
        let o = 1; for (let e = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity || 1);
        out[el.dataset.track] = { x: r.left + r.width / 2, y: r.top + r.height / 2, s: Math.sqrt(Math.max(r.width * r.height, 0)), r: rot, o, vis: cs.visibility !== 'hidden' && cs.display !== 'none', body: el.dataset.body || null };
      }
      return out;
    }, t);
    frames.push({ t, st });
    if (A.strobe && i % A.strobeEvery === 0) await p.screenshot({ path: path.join(A.dir, `s${String(i).padStart(4, '0')}.png`) });
  }
  const accents = await p.evaluate(() => (window.__accents || []));
  fs.writeFileSync(path.join(A.dir, 'track.json'), JSON.stringify({ frames, accents }));
  await b.close();
})().catch(e => { console.error(e); process.exit(1) });
"""


def font(size):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def capture(page, t0, t1, fps, size, workdir, strobe_n=12, hash_=''):
    os.makedirs(workdir, exist_ok=True)
    js = os.path.join(workdir, '_track.cjs')
    open(js, 'w').write(TRACK_JS)
    n = int(round((t1 - t0) * fps))
    args = dict(page=str(page), w=size[0], h=size[1], fps=fps, dir=workdir, strobe=True, strobeEvery=max(1, n // strobe_n), hash=hash_, **{'from': t0, 'to': t1})
    subprocess.run(['node', js, json.dumps(args)], check=True)
    data = json.load(open(os.path.join(workdir, 'track.json')))
    return data['frames'], data.get('accents', [])


def series(frames):
    names = sorted({k for f in frames for k in f['st']})
    t = np.array([f['t'] for f in frames])
    S = {}
    for nm in names:
        rows = [f['st'].get(nm) for f in frames]
        get = lambda key, d=np.nan: np.array([r.get(key, d) if r else np.nan for r in rows], float)
        vis = np.array([bool(r and r.get('vis', True) and r.get('o', 1) > 0.02) for r in rows])
        S[nm] = dict(x=get('x'), y=get('y'), s=get('s'), r=get('r', 0), o=get('o', 1), vis=vis)
    return t, S


def holds(act, eps=1e-6):
    """How many frames each drawing is held (1 = on ones, 2 = on twos...), from the gaps between changes."""
    changed = np.nonzero(act > eps)[0]
    if len(changed) < 6:
        return 1
    gaps = np.diff(changed)
    gaps = gaps[gaps <= 4]
    if len(gaps) < 5:
        return 1
    return int(np.bincount(gaps).argmax())


def moves(t, d, fps, size_ref):
    """Split a thing's motion into moves: stretches where it travels faster than a small threshold."""
    x, y = d['x'], d['y']
    ok = d['vis'] & ~np.isnan(x)
    # frame-to-frame speed (motion from frame i-1 to i), not a centred average: averaging would smooth a
    # jolt into something that looks eased, which is exactly what this is meant to catch
    dt = np.diff(t, prepend=t[0] - (t[1] - t[0]))
    xs, ys = np.where(ok, x, np.nan), np.where(ok, y, np.nan)
    sp = np.nan_to_num(np.hypot(np.diff(xs, prepend=xs[0]), np.diff(ys, prepend=ys[0])) / dt)
    # scale change and rotation count as motion too (a pop-in, a spin)
    ss = np.nan_to_num(np.abs(np.diff(np.nan_to_num(d['s']), prepend=np.nan_to_num(d['s'][0])) / dt))
    rr = np.nan_to_num(np.abs(np.diff(np.nan_to_num(d['r']), prepend=np.nan_to_num(d['r'][0])) / dt)) * size_ref / 360
    act = sp + 0.7 * ss + 0.5 * rr
    # Held drawings: hand animation is often "on twos" (a new drawing every 2 frames) or threes, so every other
    # frame shows no change at all. Measured frame to frame that looks like stop-start-stop; read it the way an
    # animator does, as one move sampled at the drawing rate.
    hold = holds(act)
    if hold > 1:
        act = np.convolve(act, np.ones(hold) / hold, mode='same')
    thr = max(size_ref * 0.02, 0.06 * np.max(act)) if np.max(act) > 0 else 1
    moving = act > thr
    segs, i, n = [], 0, len(t)
    while i < n:
        if moving[i]:
            j = i
            while j < n and moving[j]:
                j += 1
            if j - i >= 3:
                segs.append((max(0, i - 1), min(n - 1, j)))
            i = j
        else:
            i += 1
    # The threshold is set by the fastest thing in the clip, so a gentle move is only "found" partway up to
    # speed. Extend each move back (and forward) to where this thing was actually at rest (a local minimum of
    # its own speed), or a slow, well-eased move gets judged from its middle and looks like a jolt.
    ext = []
    for a, b in segs:
        pk = act[a:b + 1].max()
        while a > 0 and act[a - 1] < act[a] and act[a] > 0.04 * pk:
            a -= 1
        while b < n - 1 and act[b + 1] < act[b] and act[b] > 0.04 * pk:
            b += 1
        ext.append((a, b))
    segs = ext
    # a turnaround (settling back after an overshoot) briefly drops to zero speed; that's still one move
    fps = 1 / (t[1] - t[0])
    merged = []
    for a, b in segs:
        if merged and a - merged[-1][1] <= int(0.15 * fps):
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return sp, act, merged


def judge(t, d, sp, act, a, b, size_ref):
    seg = act[a:b + 1]
    peak = seg.max() + 1e-9
    dur = t[b] - t[a]
    k = max(1, int(round(len(seg) * 0.12)))
    start_frac = seg[:k].mean() / peak if seg[0] < peak else 1.0
    end_frac = seg[-k:].mean() / peak
    first = seg[1:3].max() / peak if len(seg) > 2 else 1        # speed in the first moving frames (seg[0] is the rest frame)
    last = seg[-2] / peak if len(seg) > 1 else 1
    mid = seg[int(len(seg) * 0.2):max(int(len(seg) * 0.8), int(len(seg) * 0.2) + 1)]
    flat = float(np.std(mid) / (np.mean(mid) + 1e-9)) if len(mid) > 2 else 1.0
    xs, ys = d['x'][a:b + 1], d['y'][a:b + 1]
    chord = np.hypot(xs[-1] - xs[0], ys[-1] - ys[0])
    travel = float(np.nansum(np.hypot(np.diff(xs), np.diff(ys))))
    if chord > size_ref * 0.03:
        ux, uy = (xs[-1] - xs[0]) / chord, (ys[-1] - ys[0]) / chord
        dev = np.abs((xs - xs[0]) * uy - (ys - ys[0]) * ux)
        arc = float(np.nanmax(dev) / chord)
        proj = (xs - xs[0]) * ux + (ys - ys[0]) * uy
        overshoot = float(max(0.0, (np.nanmax(proj) - chord)) / chord)
    else:
        arc, overshoot = 0.0, 0.0
    ds = np.nan_to_num(np.abs(np.diff(d['s'][a:b + 1]))).sum() / (np.nanmean(d['s'][a:b + 1]) + 1e-9)
    return dict(dx=float(np.nan_to_num(xs[-1] - xs[0])), dy=float(np.nan_to_num(ys[-1] - ys[0])), start=float(t[a]), end=float(t[b]), dur=float(dur), jolt=float(first), wall=float(last), start_frac=float(start_frac),
                end_frac=float(end_frac), linear=flat < 0.12, flatness=flat, arc=arc, overshoot=overshoot, travel=travel, chord=float(chord),
                scale_change=float(ds))


def analyse(page, t0, t1, fps=60, size=(1080, 1080), workdir=None, hash_=''):
    workdir = workdir or tempfile.mkdtemp()
    frames, accents = capture(page, t0, t1, fps, size, workdir, hash_=hash_)
    t, S = series(frames)
    size_ref = min(size)
    out = {}
    for nm, d in S.items():
        sp, act, segs = moves(t, d, fps, size_ref)
        raw = np.nan_to_num(np.hypot(np.diff(d['x'], prepend=d['x'][0]), np.diff(d['y'], prepend=d['y'][0])))
        out[nm] = dict(d=d, sp=sp, act=act, hold=holds(raw), moves=[judge(t, d, sp, act, a, b, size_ref) for a, b in segs])
    bodies = {}
    for f in frames:
        for k, v in f['st'].items():
            if isinstance(v, dict) and v.get('body'):
                bodies[k] = v['body']
    # overlap: moves that start within one frame of each other with near-identical length
    starts = [(nm, m) for nm, v in out.items() for m in v['moves']]
    lock = []
    for i in range(len(starts)):
        for j in range(i + 1, len(starts)):
            (n1, m1), (n2, m2) = starts[i], starts[j]
            if n1 != n2 and abs(m1['start'] - m2['start']) <= 1.01 / fps and abs(m1['dur'] - m2['dur']) <= 2.01 / fps:
                # parts of one body carried along together (the whole figure slides or walks) aren't lockstep:
                # their displacements are the same vector. Lockstep is separate motions that happen to coincide.
                # (Only for parts the page says belong to one body; two separate things moving identically ARE lockstep.)
                v1 = np.array([m1['dx'], m1['dy']]); v2 = np.array([m2['dx'], m2['dy']])
                n1v, n2v = np.linalg.norm(v1), np.linalg.norm(v2)
                same_body = bodies.get(n1) is not None and bodies.get(n1) == bodies.get(n2)
                cos = float(v1 @ v2 / (n1v * n2v)) if n1v > 0 and n2v > 0 else 0.0
                carried = same_body and cos > 0.85 and 0.75 < n1v / n2v < 1.33
                # Lockstep (animators call it twinning) is the SAME or MIRRORED action at the same instant.
                # Different parts doing different things on the same beat is choreography. Twitches don't count.
                real = min(n1v, n2v) > 0.02 * min(size)
                alike = abs(cos) > 0.7 and 0.5 < n1v / max(n2v, 1e-9) < 2.0
                if real and alike and not carried:
                    lock.append((n1, n2, m1['start']))
    # Accents: times the page says a sharp start or stop is meant (beats, hits, gags). In styles built on hits
    # (rubber hose, anything cut to music) a snap on the beat is the point; a snap off the beat is still a fault.
    acc = np.array(sorted(accents), float)
    for nm, v in out.items():
        tol = 1.5 * v['hold'] / fps
        for m in v['moves']:
            near = lambda x: bool(len(acc)) and float(np.min(np.abs(acc - x))) <= tol
            m['start_on_accent'] = near(m['start']) or near(m['start'] + 1 / fps)
            m['end_on_accent'] = near(m['end']) or near(m['end'] - 1 / fps)
    return dict(page=str(page), t=t, fps=fps, size=size, things=out, lockstep=lock, workdir=workdir, t0=t0, t1=t1, accents=len(acc))


def words(r):
    lines = [f"{Path(r['page']).name}: {r['t0']:.2f}–{r['t1']:.2f}s at {r['fps']} fps, {len(r['things'])} tracked thing(s)" + (f", {r['accents']} accents from the page" if r.get('accents') else '')]
    notes = []
    for nm, v in r['things'].items():
        ms = v['moves']
        h = v.get('hold', 1)
        lines.append(f"  {nm}: {len(ms)} move(s)" + (f"  (drawn on {['ones', 'twos', 'threes', 'fours'][h - 1]}: a new drawing every {h} frames)" if h > 1 else ''))
        for m in ms:
            ease_in = 'eases in' if m['jolt'] < 0.35 else 'JOLTS to speed' if m['jolt'] > 0.6 else 'firm start'
            ease_out = 'eases out' if m['wall'] < 0.35 else 'STOPS DEAD' if m['wall'] > 0.6 else 'firm stop'
            shape = 'arcs' if m['arc'] > 0.06 else 'straight'
            extra = []
            if m['overshoot'] > 0.02: extra.append(f"overshoots {m['overshoot'] * 100:.0f}% then settles")
            if m['linear']: extra.append('constant speed')
            if m['scale_change'] > 0.3: extra.append('changes size')
            if m.get('start_on_accent') and m['jolt'] > 0.6: ease_in = 'snaps in on a beat'
            if m.get('end_on_accent') and m['wall'] > 0.6: ease_out = 'hits a beat'
            lines.append(f"    {m['start']:.2f}–{m['end']:.2f}s ({m['dur'] * 1000:.0f} ms): {ease_in}, {ease_out}, {shape}" + (', ' + ', '.join(extra) if extra else ''))
            on_s, on_e = m.get('start_on_accent'), m.get('end_on_accent')
            if on_s and on_e:
                continue
            if m['linear'] and m['jolt'] > 0.6 and m['wall'] > 0.6:
                notes.append(f"{nm} at {m['start']:.2f}s moves like a machine: full speed from the first frame, constant, then a dead stop. Ease it (slow in / slow out).")
            elif m['jolt'] > 0.6 and m['dur'] > 0.15 and not on_s:
                notes.append(f"{nm} at {m['start']:.2f}s jolts into motion; give it a few frames to get going (or anticipation: a small move the other way first).")
            elif m['wall'] > 0.6 and m['overshoot'] < 0.01 and m['dur'] > 0.15 and not on_e:
                notes.append(f"{nm} at {m['start']:.2f}s hits a wall at the end; unless it's an impact, ease out or let it overshoot and settle.")
            if m['overshoot'] > 0.3:
                notes.append(f"{nm} at {m['start']:.2f}s overshoots by {m['overshoot'] * 100:.0f}%: very rubbery. Intended?")
            if m['dur'] < 0.1 and m['chord'] > min(r['size']) * 0.3:
                notes.append(f"{nm} at {m['start']:.2f}s crosses {m['chord']:.0f} px in {m['dur'] * 1000:.0f} ms; the eye may lose it (consider a smear or a trail).")
    moving = [m for v in r['things'].values() for m in v['moves'] if m['chord'] > min(r['size']) * 0.1]
    if len(moving) >= 3 and all(m['arc'] < 0.03 for m in moving):
        notes.append('every long move is a dead-straight line. Fine for interface slides; for anything alive, curve the paths (arcs).')
    if r['lockstep']:
        pairs = sorted({(a, b) for a, b, _ in r['lockstep']})
        notes.append('lockstep: ' + '; '.join(f'{a} + {b}' for a, b in pairs[:6]) + ' do the same (or mirrored) move on the same frame for the same length: twinning. Offset them 2–6 frames (overlapping action) so it reads as one motion rippling through, not a block.')
    if notes:
        lines.append('')
        lines.append('notes:')
        lines += ['  - ' + n for n in dict.fromkeys(notes)]
    return '\n'.join(lines)


PAL = [(255, 196, 0), (0, 214, 255), (255, 84, 120), (130, 255, 120), (190, 140, 255), (255, 150, 60), (120, 200, 200), (240, 240, 240)]


def picture(r, out_png, title=''):
    W_, H_ = r['size']
    wd = r['workdir']
    shots = sorted(p for p in os.listdir(wd) if p.startswith('s') and p.endswith('.png'))
    # onion skin: lighten-blend all strobe frames, later ones stronger
    sc = 420 / max(W_, H_)
    cw, ch = int(W_ * sc), int(H_ * sc)
    onion = None
    for k, s in enumerate(shots):
        im = Image.open(os.path.join(wd, s)).convert('RGB').resize((cw, ch), Image.LANCZOS)
        a = 0.35 + 0.65 * (k + 1) / len(shots)
        im = Image.eval(im, lambda v, a=a: int(v * a))
        onion = im if onion is None else ImageChops.lighter(onion, im)
    pad, top = 12, 44
    Wimg = pad * 3 + cw * 2 + 520
    Himg = top + 20 + max(ch, 300 + 40 + 26 * max(1, len(r['things']))) + 24
    img = Image.new('RGB', (Wimg, Himg), (16, 16, 16))
    d = ImageDraw.Draw(img)
    f13, f16 = font(13), font(16)
    d.text((pad, 12), title, font=f16, fill=(235, 235, 235))
    if onion is not None:
        img.paste(onion, (pad, top + 20)); d.text((pad, top), 'onion skin (strobe of the whole span)', font=f13, fill=(190, 190, 190))
    # paths with spacing dots
    x0 = pad * 2 + cw
    d.rectangle([x0, top + 20, x0 + cw, top + 20 + ch], outline=(60, 60, 60))
    d.text((x0, top), 'paths + spacing (a dot per frame)', font=f13, fill=(190, 190, 190))
    for k, (nm, v) in enumerate(r['things'].items()):
        c = PAL[k % len(PAL)]
        dd = v['d']
        pts = [(x0 + xx * sc, top + 20 + yy * sc) for xx, yy, vis in zip(dd['x'], dd['y'], dd['vis']) if vis and not np.isnan(xx)]
        if len(pts) > 1:
            d.line(pts, fill=tuple(int(q * 0.5) for q in c), width=1)
        for (px_, py_) in pts[::max(1, r['fps'] // 30)]:
            d.ellipse([px_ - 2, py_ - 2, px_ + 2, py_ + 2], fill=c)
        if pts:
            d.text((pts[-1][0] + 6, pts[-1][1] - 6), nm, font=f13, fill=c)
    # speed curves
    x1 = pad * 3 + cw * 2
    gw, gh = 500, 300
    d.text((x1, top), 'speed over time (px/s); shaded = moves', font=f13, fill=(190, 190, 190))
    gy0 = top + 20
    d.rectangle([x1, gy0, x1 + gw, gy0 + gh], outline=(60, 60, 60))
    t = r['t']; T0, T1 = t[0], t[-1]
    mx = max((v['act'].max() for v in r['things'].values()), default=1) + 1e-9
    tx = lambda tt: x1 + (tt - T0) / (T1 - T0 + 1e-9) * gw
    for k, (nm, v) in enumerate(r['things'].items()):
        c = PAL[k % len(PAL)]
        pts = [(tx(tt), gy0 + gh - gh * a / mx) for tt, a in zip(t, v['act'])]
        d.line(pts, fill=c, width=2)
    # timing chart
    ty0 = gy0 + gh + 30
    d.text((x1, ty0 - 18), 'timing (each move as a bar)', font=f13, fill=(190, 190, 190))
    for k, (nm, v) in enumerate(r['things'].items()):
        c = PAL[k % len(PAL)]
        yy = ty0 + k * 26
        d.text((x1, yy + 4), nm[:12], font=f13, fill=c)
        for m in v['moves']:
            d.rectangle([tx(m['start']) + 90 * 0, yy, tx(m['end']), yy + 18], fill=tuple(int(q * 0.55) for q in c), outline=c)
    for s in np.arange(np.ceil(T0 * 2) / 2, T1 + 1e-9, 0.5):
        d.line([(tx(s), gy0 + gh), (tx(s), gy0 + gh + 5)], fill=(140, 140, 140))
        d.text((tx(s) - 8, gy0 + gh + 6), f'{s:g}', font=f13, fill=(140, 140, 140))
    for a, b, st in r['lockstep']:
        d.line([(tx(st), ty0 - 4), (tx(st), ty0 + 26 * len(r['things']))], fill=(255, 60, 60), width=1)
    img.save(out_png)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('page')
    ap.add_argument('--from', dest='t0', type=float, default=0.0)
    ap.add_argument('--to', dest='t1', type=float, default=None)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--size', default='1080x1080')
    ap.add_argument('--out', default='.')
    ap.add_argument('--name')
    ap.add_argument('--hash', default='', help='URL hash to pass (e.g. a genome for kit.js pages)')
    a = ap.parse_args()
    size = tuple(int(v) for v in a.size.split('x'))
    t1 = a.t1 if a.t1 is not None else 5.0
    os.makedirs(a.out, exist_ok=True)
    name = a.name or Path(a.page).stem
    r = analyse(a.page, a.t0, t1, a.fps, size, os.path.join(a.out, name + '_frames'), a.hash)
    text = words(r)
    base = os.path.join(a.out, name)
    open(base + '.motion.txt', 'w').write(text + '\n')
    picture(r, base + '.motion.png', f'{name}  {a.t0:g}–{t1:g}s')
    print(text)
    print(f'\nwrote {base}.motion.txt and {base}.motion.png')


if __name__ == '__main__':
    main()
