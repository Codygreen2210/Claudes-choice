"""Event times for the Brazen Bull Short, pinned to the words of the narration (word times estimated the way the captions are:
spread across each line's voice span by word length). Writes events.json, read by the scene (parts/40_actors.py) and the sound (body_sound.py).
    python3 events.py"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
TM = json.load(open(os.path.join(HERE, 'times.json'))); LN = json.load(open(os.path.join(HERE, 'lines.json')))
B, VOICE, TOTAL = TM['starts'], TM['voice'], TM['total']


def at(i, word, n=1, frac=0.0):
    """start time of the n-th word in line i that starts with `word` (case-insensitive, letters only); frac moves into the word"""
    ws = LN[i].split(); wt = [len(w.strip('.,?!:;')) + 2.0 for w in ws]; tot = sum(wt); v0, v1 = VOICE[i]; c = 0.0; seen = 0
    for w, x in zip(ws, wt):
        if re.sub(r'[^a-z]', '', w.lower()).startswith(word.lower()):
            seen += 1
            if seen == n: return round(v0 + (v1 - v0) * (c + frac * x) / tot, 3)
        c += x
    raise KeyError((i, word, n))


E = {}
# 0: the big bull turns on its turntable; steam from the nose on "brazen"; the lights flicker on "cruelest"
E['STEAM0'] = at(0, 'brazen'); E['FLICK0'] = at(0, 'cruelest'); E['FLICK1'] = E['FLICK0'] + 0.7; E['PLQ'] = at(0, 'punishment')
# 1: Sicily - the year sign, the ruler's bust, the pin on the map
E['YEAR1'] = at(1, 'two'); E['BUST'] = at(1, 'phalaris'); E['PIN'] = at(1, 'sicily')
# 2-4: the workshop - plans unroll, the model bull drops on its stand, its side goes see-through, the door opens; locked, fire; sound rings
E['SCROLL'] = at(2, 'artist'); E['MODEL'] = at(2, 'bronze'); E['HOLLOW'] = at(2, 'hollow'); E['DOOR'] = at(2, 'door')
E['SHUT'] = at(3, 'locked'); E['LOCK'] = E['SHUT'] + 0.25; E['FIRE'] = at(3, 'fire')
E['PIPES'] = at(4, 'pipes'); E['RINGS'] = at(4, 'cries'); E['MOO'] = at(4, 'sound')
# 5-6: the game board - the king piece shakes; the inventor pawn is pushed into the little bull; the people rise up; the king goes in
E['DISG'] = at(5, 'disgusted'); E['INV'] = at(5, 'inventor'); E['TEST'] = at(5, 'test')
E['ROSE'] = at(6, 'rose'); E['KINGIN'] = at(6, 'inside'); E['SHUT6'] = at(6, 'bull')
# 7-8: the record - "?", the book opens, the 500-year line grows; MADE UP?
E['QMARK'] = at(7, 'sure'); E['BOOK'] = at(7, 'written'); E['TL0'] = at(7, 'five'); E['TL1'] = at(7, 'later')
E['MADEUP'] = at(8, 'made')
# 9-10: the map - REAL; the bull token rides to Carthage; the Roman helmet; it rides home
E['REAL'] = at(9, 'really'); E['CARRY'] = at(9, 'carried'); E['CARTH'] = at(9, 'carthage')
E['YEAR10'] = at(10, 'centuries'); E['HELM'] = at(10, 'roman'); E['BACK'] = at(10, 'sent')
# 11: the Roman writer - the bust's spot comes up, the scroll unrolls
E['WRITER'] = at(11, 'roman'); E['REMIND'] = at(11, 'reminder')
# 12: the river - the statue, the water starts to run
E['STATUE'] = max(at(12, 'historian'), B[12] + 0.8); E['RIVER'] = at(12, 'river')
# 13: lost - the empty plinth, the ? on "truth"
E['LOST'] = at(13, 'lost'); E['QM13'] = at(13, 'truth')
for k, v in E.items(): E[k] = [round(x, 3) for x in v] if isinstance(v, list) else round(v, 3)
json.dump(E, open(os.path.join(HERE, 'events.json'), 'w'), indent=1)
if __name__ == '__main__':
    for k, v in E.items(): print(f'{k:8s} {v}')
