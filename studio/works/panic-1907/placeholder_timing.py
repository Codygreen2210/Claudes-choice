#!/usr/bin/env python3
"""Make a stand-in timing.js from the script alone, so the picture can be built before the voice exists.
Real timing comes from assemble.py once the takes are in."""
import json, re
s = json.load(open('script.json'))['scenes']
t = 2.0; out = []
for sc in s:
    words = sc.split(); ws = []; start = t
    for w in words:
        d = 0.16 + 0.055 * len(re.sub(r'\W', '', w))
        ws.append({'w': w, 's': round(t, 3), 'e': round(t + d, 3)}); t += d
        if re.search(r'[.?!]["”]?$', w): t += 0.55
        elif w.endswith('…'): t += 0.5
        elif w.endswith(','): t += 0.22
    out.append({'start': round(start, 3), 'end': round(t - 0.55, 3), 'words': ws}); t += 0.9
json.dump({'scenes': out, 'total': round(t + 4.5, 2), 'placeholder': True}, open('timing.json', 'w'))
open('timing.js', 'w').write('window.TIMING = ' + json.dumps({'scenes': out, 'total': round(t + 4.5, 2)}))
print(round(t + 4.5, 1), [round(o['end'] - o['start'], 1) for o in out], sum(len(x.split()) for x in s))
