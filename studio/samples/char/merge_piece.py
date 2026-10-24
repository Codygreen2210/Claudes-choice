"""Swap pieces from a partial build (ONLY=name python3 character.py DIR) into a full build, for fast iteration.
    python3 merge_piece.py FULL_DIR PARTIAL_DIR      (pieces in PARTIAL replace the same-named pieces in FULL)"""
import json, sys
full, part = sys.argv[1], sys.argv[2]
F = json.load(open(full + '/guy.json')); fb = bytearray(open(full + '/guy.bin', 'rb').read())
P = json.load(open(part + '/guy.json')); pb = open(part + '/guy.bin', 'rb').read()
fb += b'\0' * (-len(fb) % 16); base = len(fb); fb += pb
def shift(o):
    if isinstance(o, dict): return {k: (v + base if isinstance(v, int) and k not in ('nv', 'nf') else shift(v)) for k, v in o.items()}
    if isinstance(o, list): return [shift(x) for x in o]
    return o
for e in P['meshes']:
    e2 = {k: v for k, v in e.items()}
    e2 = {k: (v + base if isinstance(v, int) and k not in ('nv', 'nf') else shift(v) if k != 'name' else v) for k, v in e2.items()}
    F['meshes'] = [e2 if m['name'] == e['name'] else m for m in F['meshes']]
    print('merged', e['name'])
json.dump(F, open(full + '/guy.json', 'w')); open(full + '/guy.bin', 'wb').write(fb)
