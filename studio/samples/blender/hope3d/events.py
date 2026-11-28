"""Event times for the Hope Diamond Short, pinned to the words of the narration (word times estimated the way the captions are:
spread across each line's voice span by word length). Writes events.json, read by the scene (parts/40_actors.py) and the sound (body_sound.py).
    python3 events.py"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
TM = json.load(open(os.path.join(HERE, 'times.json'))); LN = json.load(open(os.path.join(HERE, 'lines.json')))
B, VOICE, TOTAL = TM['starts'], TM['voice'], TM['total']


def at(i, word, n=1, frac=0.0):
    """start time of the n-th word in line i that starts with `word` (case-insensitive); frac moves into the word"""
    ws = LN[i].split(); wt = [len(w.strip('.,?!:;')) + 2.0 for w in ws]; tot = sum(wt); v0, v1 = VOICE[i]; c = 0.0; seen = 0
    for w, x in zip(ws, wt):
        if re.sub(r'[^a-z]', '', w.lower()).startswith(word.lower()):
            seen += 1
            if seen == n: return round(v0 + (v1 - v0) * (c + frac * x) / tot, 3)
        c += x
    raise KeyError((i, word, n))


E = {}
E['RISE0'], E['RISE1'] = -0.35, 0.5
E['FLICK0'] = at(0, 'bad'); E['FLICK1'] = E['FLICK0'] + 0.8; E['CRACK'] = at(0, 'luck'); E['PLQ'] = at(0, 'anyone')
E['ROUGH'] = at(1, 'bought'); E['BAN'] = at(1, 'king'); E['CROWN'] = at(1, 'louis', frac=0.5); E['WHEEL'] = at(1, 'had'); E['CUT'] = at(1, 'blue')
E['YEAR2'] = at(2, 'seventeen'); E['LID'] = at(2, 'thieves'); s_ = at(2, 'stole'); E['STAMP2'] = s_ + 0.1
E['YANK'] = [s_ - 0.05, s_ + 0.2, s_ + 0.45, max(s_ + 0.7, at(2, 'crown'))]; E['VANISH'] = at(2, 'vanished')
E['YEAR3K'] = at(3, 'months'); E['KCROWN'] = at(3, 'head'); E['QCROWN'] = at(3, 'so')
E['HOPE3'] = at(4, 'blue'); E['SCAN0'] = at(4, 'scientists'); E['FIT'] = at(4, 'cut'); E['CHECK'] = at(4, 'stolen')
E['BOOK0'] = at(5, 'belonged'); E['BOOK1'] = E['BOOK0'] + 0.55; E['LET'] = at(5, 'hope'); E['SUB4'] = max(at(5, 'which'), E['LET'] + 0.55)
E['SOLD'] = at(6, 'sold'); E['COIN'] = at(6, 'mclean'); E['SCARY'] = at(6, 'scary')
E['GLOOM'] = at(7, 'bad'); E['SON'] = at(7, 'car'); E['APART'] = at(7, 'apart'); E['PAPER7'] = at(7, 'sold')
E['NEWS'] = [at(8, 'curse') - 0.2, at(8, 'curse') + 0.05]; E['STAMP8'] = at(8, 'made'); E['WOLF'] = at(8, 'story'); E['WOLF2'] = at(8, 'wolves'); E['LIVED'] = at(8, 'lived')
E['PKG'] = at(9, 'twist'); E['YEAR6'] = at(9, 'nineteen'); E['LABEL'] = at(9, 'smithsonian'); E['FRAG'] = at(9, 'regular')
E['STAMPS'] = [at(10, 'postage') + 0.12 * k for k in range(6)]; E['TAG6'] = at(10, 'two')
E['CRUTCH'] = at(11, 'crushed', frac=0.3); E['WIFE'] = at(11, 'died'); E['FIRE'] = at(11, 'fire')
E['SHAKE0'] = at(11, 'still'); E['SHAKE1'] = at(11, 'believe', frac=0.8); E['CURSE6'] = at(11, 'believe', frac=0.9)
E['FLY0'] = at(11, 'curse') - 0.05; E['FLY1'] = B[12] + 0.35; E['BURST'] = B[12] + 0.55; E['RISE8'] = B[12] + 1.1
E['DIM0'], E['DIM1'] = B[12] + 1.2, B[12] + 1.5; E['UV'] = B[12] + 1.55; E['GLOW1'] = B[12] + 2.25; E['COAL'] = at(12, 'hot')
E['UVOFF'] = B[13] + 0.2; E['LUP'] = B[13] + 0.6
for k, v in E.items(): E[k] = [round(x, 3) for x in v] if isinstance(v, list) else round(v, 3)
json.dump(E, open(os.path.join(HERE, 'events.json'), 'w'), indent=1)
if __name__ == '__main__':
    for k, v in E.items(): print(f'{k:8s} {v}')
