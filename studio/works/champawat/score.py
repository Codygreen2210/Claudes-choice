#!/usr/bin/env python3
"""score.py: music and sound for The Champawat Tiger, written against the narration's own timing.

Music: scene by scene with studio/instruments/moods.py, in C minor.
Sound: the studio library (studio/sfx/foley.py): the village drum line, wind in the hills, the forest at night,
the rifle, the train, the tigress herself (low growls, used sparingly).
Writes music.wav, moods.json and fx.wav.
"""
import json, re, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from studio.instruments import synth as S
from studio.instruments.moods import Score
from studio.sfx import foley as F

TM = json.load(open('timing.json')); SC = TM['scenes']; DUR = TM['total']
norm = lambda s: re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()
NW = [[norm(w['w']) for w in s['words']] for s in SC]
def q(i, phrase):
    p = norm(phrase).split()
    for k in range(len(NW[i]) - len(p) + 1):
        if NW[i][k:k + len(p)] == p: return SC[i]['words'][k]['s']
    raise SystemExit(f'cue not found: scene {i} "{phrase}"')
V = [0.0] + [s['start'] - 0.45 for s in SC[1:]] + [DUR]

sc = Score(DUR, key='C', seed=1907)
tBy = q(1, 'but by 1907') - 0.4; tArmy = q(2, 'finally the government') - 0.4; tCam = q(11, 'he traded his rifle') - 0.4; tSub = q(12, 'subscribe') - 0.4
sc.scene(V[0], V[1], 'tension', 0.6, enter='soft')
sc.scene(V[1], tBy, 'calm', 0.4, enter='swell'); sc.scene(tBy, V[2], 'dread', 0.35, enter='cut')
sc.scene(V[2], tArmy, 'mystery', 0.4, enter='soft'); sc.scene(tArmy, V[3], 'march', 0.6, enter='hit')
PLAN = [(3, 'dread', 0.5, 'soft'), (4, 'mystery', 0.4, 'soft'), (5, 'calm', 0.45, 'swell'), (6, 'tension', 0.4, 'cut'),
        (7, 'dread', 0.65, 'soft'), (8, 'tension', 0.55, 'cut'), (9, 'action', 0.95, 'hit'), (10, 'grief', 0.4, 'swell')]
for i, mood, e, ent in PLAN: sc.scene(V[i], V[i + 1], mood, e, enter=ent)
sc.scene(V[11], tCam, 'calm', 0.45, enter='swell'); sc.scene(tCam, V[12], 'wonder', 0.45, enter='swell')
sc.scene(V[12], tSub, 'wonder', 0.35, enter='swell'); sc.scene(tSub, DUR, 'wonder', 0.45, enter='swell')
plan = sc.write('music.wav', 'moods.json')

fx = F.Track(DUR, seed=1907)
# 1. the beat on the ridge
fx.seq('drum_line', 0.3, V[1] - 0.5, db=-6, n=14)
fx.bed('panic', 0.5, V[1] - 0.5, db=-20)
fx.bed('wind', 0, V[1], db=-14)
fx.hit('growl', q(0, 'something that has been') + 1.4, db=-12, pan=-0.2)
fx.hit('boom', q(0, 'by the time this day') + 3.0, db=-8)
# 2. Kumaon: wind, cattle, then the night drums
fx.bed('wind', V[1], tBy, db=-10)
fx.hit('cow', q(1, 'life here depended') + 2.5, db=-14, pan=0.5)
fx.bed('crickets', q(1, 'and at night') - 0.3, V[2], db=-12)
fx.seq('drum_line', q(1, 'and at night') + 0.5, V[2] - 0.3, db=-12, n=4, bpm=96)
# 3. Nepal: hunters, then the army's line
fx.bed('wind', V[2], tArmy, db=-12)
fx.seq('column', tArmy + 0.5, q(2, 'most accounts say'), db=-10)
fx.bed('panic', q(2, 'hundreds of soldiers'), q(2, 'most accounts say'), db=-18)
fx.bed('rain', q(2, 'hundreds of soldiers') + 2, q(2, 'most accounts say'), db=-20)
# 4. how she hunted: daylight, grass, a growl in the brush
fx.bed('wind', V[3], V[4], db=-12)
fx.hit('growl', q(3, 'most tigers that hunt') + 3.4, db=-10)
fx.hit('boom', q(3, '200'), db=-10)
# 5. why: the teeth
fx.seq('hooves', q(4, 'a healthy tiger') + 0.5, q(4, 'a healthy tiger') + 4, db=-14)
fx.hit('thud', q(4, 'two of her big teeth') + 1.2, db=-10)
fx.hit('musket', q(4, 'most likely') + 0.6, db=-14, pan=0.4)
# 6. Corbett: the forest, the railway
fx.bed('wind', V[5], q(5, 'he had a job'), db=-12)
fx.bed('train', q(5, 'he had a job') - 0.2, q(5, 'when the government asked'), db=-8)
fx.hit('whistle', q(5, 'he had a job') + 0.6, db=-10)
fx.hit('page', q(5, 'the reward on her head'), db=-8)
# 7. the search: walking
fx.seq('walk', V[6] + 0.3, V[7] - 0.4, db=-12, surface='dirt')
fx.bed('wind', V[6], V[7], db=-14)
# 8. Phungar: the ravine, the earth falling, two shots
fx.seq('walk', q(7, 'corbett picked up'), q(7, 'he found what'), db=-10, surface='dirt')
fx.bed('crickets', q(7, 'it went down'), V[8], db=-16)
fx.hit('growl', q(7, 'a little earth') + 1.2, db=-8, pan=0.5)
tFire = q(7, 'he swung his rifle')
fx.hit('musket', tFire + 1.0, db=-2); fx.hit('musket', tFire + 1.5, db=-3)
fx.hit('roar', tFire + 1.7, db=-10, pan=0.6)
# 9. the plan
fx.bed('wind', V[8], V[9], db=-14)
fx.seq('walk', q(8, 'the tahsildar went'), q(8, '298 of them'), db=-14, surface='dirt')
# 10. the shot
fx.seq('drum_line', V[9] + 0.3, q(9, 'it was over'), db=-5, n=16)
fx.bed('panic', V[9] + 0.5, q(9, 'it was over'), db=-16)
fx.hit('growl', q(9, 'then she came out') + 0.4, db=-6, pan=-0.3)
fx.hit('musket', q(9, 'corbett fired') + 0.5, db=0); fx.hit('roar', q(9, 'corbett fired') + 0.9, db=-6)
fx.hit('musket', q(9, 'he fired again') + 0.5, db=0)
fx.hit('clack', q(9, 'then his rifle was empty') + 0.4, db=-4)
fx.hit('musket', q(9, 'she was 20 feet away') + 0.8, db=1)
fx.bed('wind', q(9, 'it was over') - 0.3, V[10] + 3, db=-12)
# 11. the count, the marker
fx.hit('boom', q(10, 'is 436'), db=-8)
fx.bed('wind', V[10], V[11], db=-14)
# 12. after: the train again, the camera
fx.bed('train', V[11], q(11, 'but over the next'), db=-12)
fx.bed('wind', q(11, 'but over the next'), V[12], db=-14)
fx.hit('clack', tCam + 1.2, db=-8)
# 13. today
fx.bed('wind', V[12], tSub, db=-14)
fx.hit('growl', V[12] + 2, db=-16)
S.write('fx.wav', fx.out())
print('music', len(plan), 'scenes; sounds used:', fx.used)
