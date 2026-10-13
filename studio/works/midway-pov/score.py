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
# one dark key, no brass: the search, the irony on the bridge, the run into the guns, the dive, the cost
sc.scene(V[0], tSee, 'dread', 0.35, enter='soft')
sc.scene(tSee, V[1], 'tension', 0.45, enter='cut')
sc.scene(V[1], V[2], 'dread', 0.45, enter='soft')
sc.scene(V[2], q(2, 'every plane in') - 0.3, 'tension', 0.85, enter='cut')
sc.scene(q(2, 'every plane in') - 0.3, V[3], 'dread', 0.3, enter='cut')
sc.scene(V[3], tRoll, 'tension', 0.5, enter='soft')
sc.scene(tRoll, tBack, 'tension', 0.95, enter='cut')
sc.scene(tBack, DUR, 'dread', 0.55, enter='cut')
plan = sc.write('music.wav', 'moods.json')

fx = F.Track(DUR, seed=1942)
# 0: the cockpit at altitude: engine drone, thin wind
fx.bed('cockpit', 0, V[1] + 0.3, db=-1, fin=0.05)
fx.bed('formation', q(0, 'about thirty') - 0.5, q(0, 'the enemy fleet'), db=-6, fin=1.0)
fx.bed('wind', 0, V[1], db=-20, fin=0.05)
fx.hit('riser', q(0, 'a japanese destroyer') - 1.0, db=-14)
fx.hit('boom', q(0, 'you follow it'), db=-10)
# 1: the bridge: sea, far flak, far engines
fx.bed('waves', V[1], V[2] + 1.2, db=-14)
fx.bed('wind', V[1], V[2], db=-18)
fx.bed('drone_far', q(1, 'all morning'), q(1, 'nobody is watching'), db=-8)
for k in range(3): fx.hit('flyby', q(1, 'all morning') + 0.5 + k * 2.6, db=-12 - k * 2, pan=0.3 - k * 0.3)
fx.bed('drone_far', q(1, 'the sky') + 0.3, V[2], db=-12, fin=1.0)
for k in range(6): fx.hit('flak', q(1, 'all morning') + k * 1.3, db=-18, pan=-0.5 + k * 0.2)
for k in range(4): fx.hit('explosion', q(1, 'your fighters have') + 0.6 + k * 1.1, db=-24, pan=0.4 - k * 0.25)
# 2: Gay: engines low over the water, flak right into the windscreen, then the sea alone
tDown = q(2, 'every plane in') - 0.2
fx.bed('cockpit', V[2] - 1.2, tDown + 1.2, db=0, fin=1.4, rpm=2200, cyl=14)
fx.hit('flyby', q(2, 'right into') - 1.5, db=-4, pan=-0.4)
for k in range(10): fx.hit('flak', q(2, 'to drop your') + k * 0.55, db=-11, pan=-0.6 + (k % 5) * 0.3)
fx.hit('explosion', tDown + 0.9, db=-6)
fx.bed('waves', tDown + 1.0, V[3] + 0.3, db=-10)
fx.bed('drone_far', q(2, 'you look up'), V[3] + 0.5, db=-10, fin=0.8)
# 3: the dive: engines, the scream, the bomb, the pull out, the carriers burning behind
fx.bed('cockpit', V[3], tRoll + 1.0, db=-1)
fx.hit('dive_run', tRoll + 0.3, db=0, dur=tRel + 0.7 - tRoll - 0.3)
fx.hit('flyby', tBack - 1.0, db=-6, pan=0.3)
for k in range(5): fx.hit('flak', q(3, 'it grows in') + 0.5 + k * 0.7, db=-14, pan=-0.4 + k * 0.2)
fx.hit('explosion', tRel + 1.1, db=-2)
fx.hit('explosion', tRel + 2.2, db=-8, pan=0.4)
fx.bed('cockpit', tBack - 0.4, tGot, db=-2, rpm=2300)
fx.bed('fire', tBack + 1.0, tGot + 1.0, db=-14)
fx.hit('explosion', tFive + 0.4, db=-10, pan=-0.5)
fx.hit('explosion', tFive + 2.4, db=-12, pan=0.5)
fx.bed('waves', tGot - 0.5, DUR, db=-14)
fx.hit('boom', q(3, 'and it was coming'), db=-6)
S.write('fx.wav', fx.out())
print('music', len(plan), 'scenes; sounds used:', fx.used)
