#!/usr/bin/env python3
"""score.py: music and sound for the Midway POV sample, cut to the narration's timing.
Music: moods.py scene by scene in E minor. Sound: the studio library (engines, dive, flak, explosions, waves, wind).
The cockpit shots sit inside the engine drone; it drops out when we are in the water with Gay."""
import json, re, sys, os
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

tSee = q(0, 'then you see it') - 0.3; tRoll = q(3, 'you roll over') - 0.3; tRel = q(3, 'release'); tBack = q(3, 'you pull out'); tFive = q(3, 'in about five'); tGot = q(3, 'but one of them') - 0.3
sc = Score(DUR, key='E', seed=1942)
sc.scene(V[0], tSee, 'dread', 0.45, enter='soft')
sc.scene(tSee, V[1], 'tension', 0.55, enter='cut')
sc.scene(V[1], V[2], 'mystery', 0.4, enter='soft')
sc.scene(V[2], q(2, 'every plane in') - 0.3, 'action', 0.8, enter='hit')
sc.scene(q(2, 'every plane in') - 0.3, V[3], 'grief', 0.35, enter='cut')
sc.scene(V[3], tRoll, 'tension', 0.6, enter='swell')
sc.scene(tRoll, tBack, 'action', 0.95, enter='hit')
sc.scene(tBack, tGot, 'grief', 0.45, enter='swell')
sc.scene(tGot, DUR, 'dread', 0.5, enter='cut')
plan = sc.write('music.wav', 'moods.json')

fx = F.Track(DUR, seed=1942)
# 0: the cockpit at altitude: engine drone, thin wind
fx.bed('engines', 0, V[1] + 0.3, db=-9, fin=0.05)
fx.bed('wind', 0, V[1], db=-20, fin=0.05)
fx.hit('riser', q(0, 'a japanese destroyer') - 1.0, db=-14)
fx.hit('boom', q(0, 'you follow it'), db=-10)
# 1: the bridge: sea, far flak, far engines
fx.bed('waves', V[1], V[2], db=-14)
fx.bed('wind', V[1], V[2], db=-18)
for k in range(6): fx.hit('flak', q(1, 'all morning') + k * 1.3, db=-18, pan=-0.5 + k * 0.2)
for k in range(4): fx.hit('explosion', q(1, 'your fighters have') + 0.6 + k * 1.1, db=-24, pan=0.4 - k * 0.25)
# 2: Gay: engines low over the water, flak right into the windscreen, then the sea alone
tDown = q(2, 'every plane in') - 0.2
fx.bed('engines', V[2], tDown + 1.2, db=-8, fin=0.3)
for k in range(10): fx.hit('flak', q(2, 'to drop your') + k * 0.55, db=-11, pan=-0.6 + (k % 5) * 0.3)
fx.hit('explosion', tDown + 0.9, db=-6)
fx.bed('waves', tDown + 1.0, V[3] + 0.3, db=-10)
# 3: the dive: engines, the scream, the bomb, the pull out, the carriers burning behind
fx.bed('engines', V[3], tRoll + 0.5, db=-9)
fx.hit('dive', tRoll + 0.4, db=-4)
fx.hit('dive', q(3, 'it grows in') + 0.2, db=-6)
for k in range(5): fx.hit('flak', q(3, 'it grows in') + 0.5 + k * 0.7, db=-14, pan=-0.4 + k * 0.2)
fx.hit('explosion', tRel + 1.1, db=-2)
fx.hit('explosion', tRel + 2.2, db=-8, pan=0.4)
fx.bed('engines', tBack - 0.4, tGot, db=-10)
fx.bed('fire', tBack + 1.0, tGot + 1.0, db=-14)
fx.hit('explosion', tFive + 0.4, db=-10, pan=-0.5)
fx.hit('explosion', tFive + 2.4, db=-12, pan=0.5)
fx.bed('waves', tGot - 0.5, DUR, db=-14)
fx.hit('boom', q(3, 'and it was coming'), db=-6)
S.write('fx.wav', fx.out())
print('music', len(plan), 'scenes; sounds used:', fx.used)
