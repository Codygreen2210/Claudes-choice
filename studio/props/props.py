#!/usr/bin/env python3
"""The prop studio: free CC0 props, backgrounds and surfaces for the Shorts, fetched on demand.

Sources (all CC0: free for anything, no credit needed):
  ph   Poly Haven   - scanned/modelled props (glTF), HDRI backgrounds (sky + light), photo texture sets
  acg  ambientCG    - photo PBR materials (concrete, asphalt, fabric, metal...) and some scanned models

  python3 studio/props/props.py catalog                    refresh the catalogs (runner job, ~1 min)
  python3 studio/props/props.py find "wooden chair"        search; --kind model|hdri|texture|material, -n 20
  python3 studio/props/props.py get ph:wooden_stool_02 acg:Asphalt012 ph:kloofendal_48d_partly_cloudy_puresky
                                                           download (runner job) into the cache; already-cached ids are skipped
  python3 studio/props/props.py show ph:wooden_stool_02    what's in the cache for it

Cache: /root/vt/assets/<id>/  (catalogs in /root/vt/assets/catalog_*.json). In Blender use studio/props/props_bpy.py.
A Short ships its own copies to the render farm: list the ids in its farm.sh (see props_bpy.farm_files)."""
import sys, os, json, re, subprocess, time, tempfile
CACHE = os.environ.get('PROPS_CACHE', '/root/vt/assets')
REPO_URL = 'https://github.com/Codygreen2210/Claudes-choice.git'
ROOT = subprocess.run(['git', '-C', os.path.dirname(os.path.abspath(__file__)), 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()

def catalogs():
    items = []
    for kind, f in (('hdri', 'catalog_ph_hdris.json'), ('texture', 'catalog_ph_textures.json'), ('model', 'catalog_ph_models.json'),
                    ('hdri', 'catalog_hdris.json'), ('texture', 'catalog_textures.json'), ('model', 'catalog_models.json')):
        p = os.path.join(CACHE, f)
        if not os.path.exists(p) or any(i['src'] == 'ph' and i['kind'] == kind for i in items): continue
        for k, v in json.load(open(p)).items():
            items.append({'id': 'ph:' + k, 'src': 'ph', 'kind': kind, 'name': v.get('name') or k, 'tags': v.get('tags') or [], 'cats': v.get('categories') or [], 'dims': v.get('dims')})
    p = os.path.join(CACHE, 'catalog_acg.json')
    if os.path.exists(p):
        for k, v in json.load(open(p)).items():
            dt = ' '.join(v.get('categories') or []).lower()
            kind = 'model' if '3dmodel' in dt or 'model' in dt else 'hdri' if 'hdri' in dt else 'material'
            items.append({'id': 'acg:' + k, 'src': 'acg', 'kind': kind, 'name': v.get('name') or k, 'tags': v.get('tags') or [], 'cats': v.get('categories') or []})
    return items

def find(q, kind=None, n=15):
    ws = [w for w in re.split(r'\W+', q.lower()) if w]; out = []
    for it in catalogs():
        if kind and it['kind'] != kind: continue
        name = it['name'].lower(); hay = ' '.join([it['id'].lower(), name] + [t.lower() for t in it['tags']] + [str(c).lower() for c in it['cats']])
        if not all(w in hay for w in ws): continue
        sc = sum(3 if w in name else 1 for w in ws) + (1 if os.path.isdir(os.path.join(CACHE, it['id'].split(':', 1)[1])) else 0)
        out.append((sc, it))
    out.sort(key=lambda z: -z[0]); return [it for _, it in out[:n]]

def run_job(lines, wait=True):
    """push assets/in-<id> with want.txt, wait for the runner, unpack into the cache"""
    jid = time.strftime('%Y%m%d-%H%M%S'); env = dict(os.environ)
    with tempfile.TemporaryDirectory() as td:
        w = os.path.join(td, 'want.txt'); open(w, 'w').write('\n'.join(lines) + '\n')
        env['GIT_INDEX_FILE'] = os.path.join(td, 'idx'); g = lambda *a: subprocess.run(['git', '-C', ROOT, *a], env=env, capture_output=True, text=True, check=True).stdout.strip()
        g('read-tree', 'HEAD'); h = g('hash-object', '-w', w); g('update-index', '--add', '--cacheinfo', f'100644,{h},assets/want.txt')
        tree = g('write-tree'); c = g('commit-tree', tree, '-p', 'HEAD', '-m', f'asset job {jid}')
        subprocess.run(['git', '-C', ROOT, 'push', '-q', REPO_URL, f'{c}:refs/heads/assets/in-{jid}'], capture_output=True)
    print('asset job', jid, flush=True)
    if not wait: return jid
    rid = None
    for _ in range(60):
        r = subprocess.run(['gh', 'run', 'list', '-R', 'Codygreen2210/Claudes-choice', '-L', '10', '--json', 'databaseId,displayTitle,status'], capture_output=True, text=True).stdout
        m = [x for x in json.loads(r or '[]') if x['displayTitle'] == f'asset job {jid}']
        if m:
            rid = m[0]['databaseId']
            if m[0]['status'] == 'completed': break
        time.sleep(10)
    if rid: subprocess.run(['gh', 'run', 'watch', str(rid), '-R', 'Codygreen2210/Claudes-choice'], capture_output=True)
    os.makedirs(CACHE, exist_ok=True)
    subprocess.run(f'cd {ROOT} && git fetch -q --depth 1 {REPO_URL} refs/heads/assets/out-{jid} && git archive FETCH_HEAD | tar -x -C {CACHE}', shell=True, check=True)
    log = open(os.path.join(CACHE, 'log.txt')).read(); print(log); return jid

def cached(pid): return os.path.isdir(os.path.join(CACHE, pid.split(':', 1)[1]))

def get(ids, res=None):
    lines = []
    for pid in ids:
        if cached(pid): print('cached', pid); continue
        src, aid = pid.split(':', 1) if ':' in pid else ('ph', pid)
        lines.append(f'{src} {aid}' + (f' {res if src == "ph" else res.upper()}' if res else ''))
    if lines: run_job(lines)

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'): print(__doc__); sys.exit(0)
    if a[0] == 'catalog': run_job(['catalog'])
    elif a[0] == 'find':
        kind = a[a.index('--kind') + 1] if '--kind' in a else None; n = int(a[a.index('-n') + 1]) if '-n' in a else 15
        q = ' '.join(x for i, x in enumerate(a[1:], 1) if x not in ('--kind', '-n') and a[i - 1] not in ('--kind', '-n'))
        for it in find(q, kind, n):
            print(f"{it['id']:48s} {it['kind']:8s} {'[cached] ' if cached(it['id']) else ''}{it['name']}  ({', '.join(map(str, it['cats']))[:40]})")
    elif a[0] == 'get':
        res = a[a.index('--res') + 1] if '--res' in a else None
        get([x for i, x in enumerate(a[1:], 1) if x != '--res' and a[i - 1] != '--res'], res)
    elif a[0] == 'show':
        for pid in a[1:]:
            d = os.path.join(CACHE, pid.split(':', 1)[1]); print(pid, '->', d)
            for r, _, fs in os.walk(d):
                for f in fs: print('   ', os.path.relpath(os.path.join(r, f), d))
