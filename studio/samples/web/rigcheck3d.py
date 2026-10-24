"""Summarise the 3D rig check: python3 rigcheck3d.py rig.json"""
import json, sys
LIM = dict(phi=(-45, 180), e=(0, 180), tw=(-70, 90), elb=(0, 145), lphi=(-30, 180), le=(0, 120), ltw=(-40, 50), knee=(0, 150))
rows = json.load(open(sys.argv[1]))
lim, spin, pen_b, pen_a = {}, {}, [], []
prev = None
for r in rows:
    for s in ('N', 'F'):
        for k, (lo, hi) in LIM.items():
            v = r['raw'][s][k]
            if v < lo - 1 or v > hi + 1:
                lim.setdefault(f'{s} {k}', []).append(r['t'])
            if prev is not None:
                d = abs(r['P'][s][k] - prev['P'][s][k]) * 30
                if k in ('phi', 'lphi'):            # the plane of a hanging limb is meaningless: weight by elevation
                    e = r['P'][s]['e' if k == 'phi' else 'le']
                    import math; d *= math.sin(math.radians(min(e, 90)))
                if d > 1000:
                    spin.setdefault(f'{s} {k}', []).append(round(r['t'], 2))
    if max(r['penBefore'].values()) > 0.003: pen_b.append(r['t'])
    if max(r['pen'].values()) > 0.003: pen_a.append((round(r['t'], 2), {k: round(v, 3) for k, v in r['pen'].items() if v > 0.003}))
    prev = r
print(f'frames {len(rows)}')
print('joint asks outside human range (clamped by the rig):', {k: len(v) for k, v in lim.items()} or 'none')
print('limbs inside the body before push-out:', len(pen_b), 'frames;  after:', len(pen_a), 'frames', pen_a[:5])
print('joints faster than 1000 deg/s:', spin or 'none')
