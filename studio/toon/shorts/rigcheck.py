#!/usr/bin/env python3
"""Rig check for a Short: runs every frame with drawing switched off, logs every arm the Short asks guy() for,
and reports what a body can't do.   python3 rigcheck.py <name> <work dir>   (work dir holds times.json, lines.json)

Flags (raw numbers from the Short, before rig safety fixes them):
  LIMIT   shoulder/elbow outside human range, elbow wound past a full turn
  BODY    upper arm through the head, hand past the far shoulder (through the body)
  SPIN    a joint moving faster than 25 deg per frame (750 deg/s): reads as flailing/popping, not motion
  FLIP    the arm switching in front of / behind the head more than twice in a second
Exit code 1 if anything other than SPIN-free, limit-clean output (so it can gate a build)."""
import importlib, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
if '--draw' not in sys.argv:          # poses only: run every beat on a tiny canvas (pixels don't matter here)
    os.environ['TOON_SIZE'] = '108x192'
import toon2d  # noqa: E402
import common, rigsafe  # noqa: E402

LOG = []          # (T, call index, sx, a1, a2, front)
STATE = {'T': 0.0, 'k': 0}
CUTS = []

_guy = common.guy


def guy_logged(cv, x, y, s=1.0, face='calm', arms=((12, 0), (12, 0)), *a, **kw):
    for sx, (a1, a2) in zip((-1, 1), arms):
        _, _, front = rigsafe.safe_arm(sx, a1, a2, kw.get('tilt_head', 0.0) * 30)
        LOG.append((STATE['T'], STATE['k'], sx, float(a1), float(a2), front))
    STATE['k'] += 1
    return _guy(cv, x, y, s, face, arms, *a, **kw)


def main():
    name, wd = sys.argv[1], sys.argv[2]
    fast = '--draw' not in sys.argv
    common.guy = guy_logged
    if fast:                                   # skip the pixels: only the poses matter here
        for m in ('shape', 'glow', 'overlay'):
            setattr(toon2d.Canvas, m, lambda self, *a, **k: None)
    sys.argv = [name]                          # the Short module must not parse our args
    import kit
    kit.guy = guy_logged
    mod = importlib.import_module(name)
    if hasattr(mod, 'guy'):
        mod.guy = guy_logged
    for m in list(sys.modules.values()):       # star-imports copied guy into other helper modules too
        if getattr(m, 'guy', None) is _guy:
            m.guy = guy_logged
    TM = json.load(open(os.path.join(wd, 'times.json'))); LINES = json.load(open(os.path.join(wd, 'lines.json')))
    CUTS.extend(TM['starts'] + [TM['total']])
    n = int(round(TM['total'] * kit.FPS))
    for i in range(n):
        STATE['T'] = i / kit.FPS; STATE['k'] = 0
        kit.frame(i / kit.FPS, TM, LINES, mod.BEATS)
    return report(name, n)


def report(name, n):
    import collections
    probs = collections.defaultdict(list)
    tracks = collections.defaultdict(list)
    for T, k, sx, a1, a2, front in LOG:
        for p in rigsafe.report_arm(sx, a1, a2):
            kind = 'BODY' if ('through' in p and 'folds' not in p) else 'LIMIT'
            what = re.sub(r'\s+', ' ', re.sub(r'-?\d+(\.\d+)?', '', p)).replace(' outside ..', ' outside its range').strip()
            probs[(kind, f'{"left" if sx < 0 else "right"} {what}')].append(T)
        tracks[(k, sx)].append((T, a1, a2, front))
    for (k, sx), tr in tracks.items():
        tr.sort()
        for (t0, a10, a20, f0), (t1, a11, a21, f1) in zip(tr, tr[1:]):
            if abs(t1 - t0 - 1 / 30) > 1e-3 or any(t0 < c <= t1 + 1e-6 for c in CUTS):
                continue                       # not consecutive frames, or a cut between them (new shot, new pose)
            d = max(abs(float(rigsafe.wrap180(a11 - a10))), abs(float(rigsafe.wrap180(a21 - a20))))
            if d > 25:
                probs[('SPIN', f'{"left" if sx < 0 else "right"} arm of figure {k}')].append(t1)
        flips = [tr[j + 1][0] for j in range(len(tr) - 1) if tr[j][3] != tr[j + 1][3]]
        for j in range(len(flips)):
            if j >= 2 and flips[j] - flips[j - 2] < 1.0:
                probs[('FLIP', f'{"left" if sx < 0 else "right"} arm of figure {k} in front/behind head')].append(flips[j])
    print(f'rig check: {name}  ({n} frames, {len(LOG)} arm poses)')
    if not probs:
        print('  clean: every arm inside human range, nothing through the body, no spins')
        return 0
    for (kind, what), ts in sorted(probs.items()):
        ts = sorted(set(round(t, 2) for t in ts))
        spans = []
        for t in ts:
            if spans and t - spans[-1][1] <= 0.07:
                spans[-1][1] = t
            else:
                spans.append([t, t])
        sp = ', '.join(f'{a:.1f}s' if a == b else f'{a:.1f}-{b:.1f}s' for a, b in spans[:6]) + (' ...' if len(spans) > 6 else '')
        print(f'  {kind:5s} {what}: {len(ts)} frames at {sp}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
