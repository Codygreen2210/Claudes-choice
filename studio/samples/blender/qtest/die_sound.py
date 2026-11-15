# Sound for the die test: only the die's own hits, each one on the exact moment the physics toss (die_path.json) has a corner
# land on the table, loudness from how hard it lands. Hits are short clean clacks cut from real recordings of a die and a
# chess piece on a table, chosen by measurement (sharp attack, no scrape tail). Quiet room tone under it. python3 die_sound.py OUT.wav
import sys, os, math, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'senses'))
from sfxlib import Lib, Bus, SR
L = Lib(); byf = {e['src'].split('/')[-1]: e for e in L.items}
P = json.load(open(os.path.join(HERE, 'die_path.json'))); SLOW = 0.5; DUR = 5.0
def cut(name, at, n=0.09):
    x = L.load(byf[name]); a = max(0, int((at - 0.003) * SR)); c = x[a:a + int(n * SR)].copy()
    env = np.exp(-np.arange(len(c)) / (0.022 * SR)); c *= env[:, None]                   # fast decay: a clack, never a scrape
    c[:int(0.001 * SR)] *= np.linspace(0, 1, int(0.001 * SR))[:, None]; return c / (np.abs(c).max() + 1e-9)
DICE = 'GAMEBoard_Dice, Contact, Die, Roll, On Table_UberDuo_Game.wav'; CHESS = 'GAMEBoard_Chess, Contact, King Takes_UberDuo_Game.wav'
WOOD = 'WOODImpt_Drops20_InMotionAudio_Wood.wav'
hard = [cut(DICE, 0.373), cut(WOOD, 0.021)]                        # big landings: the die clack plus the bright knock of the table
soft = [cut(DICE, 0.373, 0.05), cut(WOOD, 0.021, 0.05), cut(DICE, 0.181, 0.05)]
B = Bus(DUR)
room = L.load(L.pick('quiet room livingroom')); B.put(np.tile(room, (2, 1))[:int(DUR * SR)], 0.0, -40)
vmax = max(v for _, v in P['hits'])
for j, (ts, v) in enumerate(P['hits']):
    t = ts / SLOW; s = v / vmax; db = -6 + 22 * math.log10(max(s, 0.08))
    pan = 0.1 * math.sin(1.7 * j); rate = 1.0 + 0.04 * ((j * 5) % 3)
    if s > 0.45: B.put(hard[0], t, db, pan, rate); B.put(hard[1], t, db - 5, pan, rate)
    else: B.put(soft[j % len(soft)], t, db, pan, rate)
y = B.render(DUR, lufs=-16.0, peak_db=-1.5)
import soundfile as sf; sf.write(sys.argv[1], y, SR); print('wrote', sys.argv[1], 'hits at', [round(ts / SLOW, 3) for ts, _ in P['hits']])
