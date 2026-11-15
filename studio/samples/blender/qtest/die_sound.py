# Sound for the die quality test, all real recordings from the Sonniss library, each contact placed on its exact frame:
# the die's hops and every face slap come from the same maths qtest.py animates with. python3 die_sound.py OUT.wav
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'senses'))
from sfxlib import Lib, Bus, SR
L = Lib(); DUR = 5.0; T_SET = 2.6; ROLLS = 5
# contact times: hop landings, then a face slap each time the roll angle passes a quarter turn (ease_out inverse)
ev = [(0.0, 1.0, 'hop'), (0.42, 0.9, 'hop'), (0.72, 0.6, 'hop')]
for k in range(1, ROLLS + 1):
    t = T_SET * (1 - (1 - k / ROLLS) ** (1 / 3)); ev.append((t, 0.75 - 0.1 * k, 'slap'))
# cut single clacks out of the real "die roll on table" recording (its loudest transients)
dice = L.load(L.pick('dice contact roll table')); env = np.abs(dice).max(1)
win = int(0.004 * SR); en = np.convolve(env, np.ones(win) / win, 'same'); pk = []
for i in np.argsort(-en):
    if all(abs(i - j) > int(0.09 * SR) for j in pk): pk.append(i)
    if len(pk) >= 6: break
clacks = []
for i in sorted(pk):
    a = max(0, i - int(0.004 * SR)); c = dice[a:a + int(0.16 * SR)].copy(); c[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))[:, None]; clacks.append(c / (np.abs(c).max() + 1e-9))
chess = L.load(L.pick('chess contact')); ce = np.abs(chess).max(1); ci = int(np.argmax(ce)); knock = chess[max(0, ci - 200):ci + int(0.25 * SR)]
knock = knock / (np.abs(knock).max() + 1e-9)
B = Bus(DUR)
room = L.load(L.pick('quiet room livingroom')); B.put(np.tile(room, (2, 1))[:int(DUR * SR)], 0.0, -26)              # the room under it all
from scipy.signal import butter, sosfilt
hp = butter(4, 180, 'highpass', fs=SR, output='sos')
roll = sosfilt(hp, L.load(L.pick('wood roll table', avoid='blood'), dur=T_SET), axis=0); B.put(roll, 0.15, -24, 0.1)                     # wood grain rumble while it rolls
B.put(L.load(L.pick('whoosh airy', maxlen=1.0)), 0.0, -24, -0.3)                                                      # it arrives through the air
for j, (t, s, kind) in enumerate(ev):
    x = clacks[j % len(clacks)]; db = -10 + 20 * math.log10(max(s, 0.05))
    B.put(x, t, db, 0.15 * math.sin(j), rate=1.0 + 0.05 * ((j * 7) % 5 - 2))
    if kind == 'hop': B.put(sosfilt(hp, knock, axis=0), t, db - 9, 0.0)                                                                     # a little wood body on the bigger hits
B.put(clacks[0], T_SET + 0.02, -24, 0.0, rate=1.12)                                                                   # the last tiny settle
B.put(L.load(L.pick('whoosh airy', seed=3, minlen=1.5, maxlen=3.5)), T_SET + 0.3, -26, 0.2)                            # the slow camera push while it rests
y = B.render(DUR, lufs=-14.0, peak_db=-1.5)
import soundfile as sf; sf.write(sys.argv[1], y, SR); print('wrote', sys.argv[1], [round(e[0], 2) for e in ev])
