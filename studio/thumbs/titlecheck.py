"""titlecheck.py: score a YouTube title out of 100, and the title + thumbnail together. Pass = 80+.

Title rules (from how top history channels title and the 2026 research in docs/youtube-growth-2026.md):
  short enough to show whole on a phone, the hook first, the searchable name of the event in it,
  something specific (a number, a name, money), real stakes, and honest (no bait, no shouting).
Combo rules: the thumbnail words add to the title instead of repeating it, the pair gives one new
fact or feeling the title doesn't, and both still pass on their own.

  python3 titlecheck.py "The Tiger That Killed 436 People | The Champawat Tiger" --search "champawat tiger"
  python3 titlecheck.py "<title>" --search "<event>" --thumb thumb.jpg     (adds the combo score)
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STAKES = {'killed', 'kill', 'won', 'win', 'lost', 'lose', 'cost', 'saved', 'save', 'crash', 'crashed', 'fell', 'fall', 'deadliest',
          'biggest', 'worst', 'first', 'last', 'only', 'never', 'every', 'nobody', 'everyone', 'million', 'billion', 'war', 'died',
          'dead', 'death', 'empire', 'collapse', 'stole', 'fooled', 'broke', 'ruined', 'hunted', 'trapped', 'doomed', 'promised'}
BAIT = ["you won't believe", 'shocking', 'they hid', 'secret they', 'gone wrong', 'must watch', 'insane', '!!', '???']
NUMWORDS = {'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'hundred', 'thousand', 'million', 'billion'}
STOP = {'the', 'a', 'an', 'of', 'that', 'and', 'to', 'in', 'on', 'at', 'for', 'is', 'it', 'his', 'her', 'their', 'how', 'why', 'who'}


def ramp(v, bad, good):
    return float(min(1, max(0, (v - bad) / (good - bad))))


def check_title(title, search):
    R = []
    n = len(title)
    R.append(('Fits on a phone', 20 * (1 if n <= 60 else ramp(80 - n, 0, 20)), 20, f'{n} characters (want 60 or fewer)'))
    s = search.lower().strip()
    R.append(('Searchable name', 20 if s and s in title.lower() else 0, 20, f'needs "{search}" in the title'))
    hook = re.split(r'\s[|:\-–]\s', title)[0]
    ok = hook.lower() != s and len(hook) <= 48 and (not s or title.lower().find(s) != 0)
    R.append(('Hook first', 15 if ok else (7 if len(hook) <= 60 else 0), 15, f'hook "{hook}" ({len(hook)} chars, want first and 48 or fewer)'))
    words = re.findall(r"[a-z0-9$,']+", title.lower())
    spec = any(re.search(r'\d', w) for w in words) or any(w in NUMWORDS for w in words) or '$' in title
    R.append(('Something specific', 15 if spec else 0, 15, 'a number, amount or count'))
    st = [w for w in words if w in STAKES]
    R.append(('Real stakes', 15 if st else 0, 15, f'stakes words: {st or "none"}'))
    caps = [w for w in re.findall(r"[A-Za-z]{4,}", title) if w.isupper()]
    bait = [b for b in BAIT if b in title.lower()]
    R.append(('Honest, no shouting', 15 if not caps and not bait else 0, 15, f'caps {caps or "none"}, bait {bait or "none"}'))
    return sum(r[1] for r in R), R


def check_combo(title, search, thumb):
    import thumbcheck
    meta = json.load(open(thumb.rsplit('.', 1)[0] + '.meta.json'))
    t_score, _ = check_title(title, search)
    th_score, _ = thumbcheck.check(thumb, title, meta)
    R = [('Title score', t_score * 0.3, 30, f'{t_score:.0f}/100'), ('Thumbnail score', th_score * 0.3, 30, f'{th_score:.0f}/100')]
    tw = {w for w in re.findall(r"[a-z0-9']+", title.lower()) if w not in STOP}
    ww = {w for w in re.findall(r"[a-z0-9']+", ' '.join(meta['words']).lower()) if w not in STOP}
    rep = tw & ww
    R.append(('Thumb adds, not repeats', 15 * (1 - min(1, len(rep) / max(1, len(ww)))), 15, f'repeats {sorted(rep) or "nothing"}'))
    new_num = any(re.search(r'\d', w) for w in ww - tw) or any(w in NUMWORDS for w in ww - tw)
    new_feel = bool((ww - tw) & (STAKES | {'zero', 'nowhere', 'hide', 'gone', 'miss', "don't", 'bulb', 'watching', 'alone', 'trapped'}))
    R.append(('Pair gives something new', 15 if (new_num or new_feel) else 0, 15, 'thumb brings a new number or feeling the title lacks'))
    total_words = len(title.split()) + len(' '.join(meta['words']).split())
    R.append(('Quick to take in', 10 * ramp(20 - total_words, 0, 6), 10, f'{total_words} words across both (want 14 or fewer)'))
    floor = t_score >= 80 and th_score >= 80
    total = sum(r[1] for r in R)
    return (total if floor else min(total, 79)), R, floor


def show(name, total, R, extra=''):
    print(f'{name}: {total:.0f}/100  {"PASS" if total >= 80 else "FAIL"}{extra}')
    for k, got, mx, note in R:
        print(f' {"  " if got >= mx * 0.8 else "->"} {k:26s} {got:5.1f}/{mx:<3d} {note}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('title'); ap.add_argument('--search', default=''); ap.add_argument('--thumb')
    a = ap.parse_args()
    t, R = check_title(a.title, a.search); show('Title', t, R)
    if a.thumb:
        c, R2, floor = check_combo(a.title, a.search, a.thumb)
        show('Title + thumbnail', c, R2, '' if floor else '  (capped: title and thumbnail must each pass on their own)')
