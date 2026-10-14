#!/usr/bin/env python3
"""score.py: music and sound for Midway, through their eyes, cut to the narration's timing.
Music: moods.py scene by scene in E minor, no brass. Sound: the studio library (modelled piston planes, the sea, the dock)."""
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

sc = Score(DUR, key='E', seed=1942)
P = [(V[0], q(0, 'then you see it') - 0.3, 'dread', 0.35, 'soft'), (q(0, 'then you see it') - 0.3, q(0, 'to understand how') - 0.3, 'tension', 0.45, 'cut'),
     (q(0, 'to understand how') - 0.3, V[2], 'mystery', 0.35, 'soft'),            # the plan
     (V[2], V[3], 'mystery', 0.45, 'soft'),                                         # the codebreakers
     (V[3], q(3, 'three american carriers') - 0.3, 'tension', 0.5, 'soft'), (q(3, 'three american carriers') - 0.3, V[4], 'dread', 0.4, 'soft'),
     (V[4], q(4, 'then a scout') - 0.3, 'tension', 0.4, 'soft'), (q(4, 'then a scout') - 0.3, V[5], 'tension', 0.65, 'cut'),
     (V[5], q(5, 'every plane in') - 0.3, 'tension', 0.85, 'cut'), (q(5, 'every plane in') - 0.3, V[6], 'dread', 0.3, 'cut'),
     (V[6], V[7], 'dread', 0.45, 'soft'), (V[7], V[8], 'tension', 0.55, 'swell'),
     (V[8], q(8, 'you pull out'), 'tension', 0.95, 'cut'), (q(8, 'you pull out'), V[9], 'dread', 0.55, 'cut'),
     (V[9], q(9, 'the yorktown stops') - 0.3, 'tension', 0.8, 'cut'), (q(9, 'the yorktown stops') - 0.3, q(9, 'but that afternoon') - 0.3, 'grief', 0.3, 'swell'),
     (q(9, 'but that afternoon') - 0.3, V[10], 'tension', 0.7, 'cut'),
     (V[10], q(10, 'the war went on') - 0.3, 'grief', 0.35, 'swell'), (q(10, 'the war went on') - 0.3, q(10, 'subscribe') - 0.3, 'wonder', 0.4, 'swell'), (q(10, 'subscribe') - 0.3, DUR, 'wonder', 0.35, 'swell')]
for a, b, m, e, en in P: sc.scene(a, b, m, e, enter=en)
plan = sc.write('music.wav', 'moods.json')

fx = F.Track(DUR, seed=1942)
# 0 cockpit
fx.bed('cockpit', 0, q(0, 'to understand how') + 1.5, db=-1, fin=0.05)
fx.bed('formation', q(0, 'about thirty') - 0.5, q(0, 'the enemy fleet'), db=-6, fin=1.0)
fx.bed('wind', 0, q(0, 'to understand how'), db=-20, fin=0.05)
fx.hit('riser', q(0, 'a japanese destroyer') - 1.0, db=-14); fx.hit('boom', q(0, 'you follow it'), db=-10)
# 1 map room, 2 basement
fx.seq('clock', V[1] + 0.5, V[2] + 1.5, db=-14)
fx.bed('rain', V[2] - 0.5, V[3], db=-26)
fx.hit('page', V[1] + 0.6, db=-10); fx.hit('page', q(1, 'so you draw'), db=-10); fx.hit('page', q(1, 'your own staff'), db=-8)
fx.seq('typing', q(2, 'your team has') - 0.2, q(2, 'two letters') - 0.3, db=-14)
fx.hit('boom', q(2, 'two letters'), db=-10); fx.seq('morse', q(2, 'midway is told'), q(2, 'a day later') - 0.5, db=-12)
fx.seq('morse', q(2, 'a day later'), q(2, 'is short') - 0.3, db=-12); fx.hit('boom', q(2, 'is short'), db=-8)
# 3 harbor, dock, sailing
fx.bed('hull', V[3], q(3, 'you are one of'), db=-10); fx.hit('ship_horn', q(3, 'you are one of') - 1.5, db=-12)
fx.seq('clock', q(3, 'ninety days'), q(3, 'when she sails'), db=-16)
fx.bed('fire_synth', q(3, 'you are one of'), q(3, 'when she sails'), db=-18)
fx.bed('waves', q(3, 'when she sails'), V[4] + 0.5, db=-12)
# 4 Nagumo's morning
fx.bed('waves', V[4], V[5], db=-16); fx.bed('drone_far', V[4] + 0.5, q(4, 'at seven'), db=-6)
for k in range(4): fx.hit('flyby', q(4, 'you send') - 1.0 + k * 1.4, db=-8 - k * 2, pan=-0.3 + k * 0.2)
fx.seq('morse', q(4, 'at seven') + 0.3, q(4, 'your second wave') - 0.5, db=-12)
fx.seq('morse', q(4, 'sends a message') + 0.2, q(4, 'you reverse') - 0.6, db=-12); fx.hit('boom', q(4, 'to be a carrier'), db=-8)
fx.bed('drone_far', q(4, 'and your planes'), V[5] + 1.0, db=-8)
# 5 Gay
tDown = q(5, 'every plane in') - 0.2
fx.bed('cockpit', V[5] + 1.0, tDown + 1.2, db=0, fin=1.4, rpm=2200, cyl=14)
fx.hit('swish', q(5, 'george gay') - 0.9, db=-6)
for k in range(10): fx.hit('flak', q(5, 'to drop its') + k * 0.55, db=-11, pan=-0.6 + (k % 5) * 0.3)
fx.hit('explosion', tDown + 0.9, db=-6)
fx.bed('waves', tDown + 1.0, V[6] + 0.3, db=-10)
for k in range(6): fx.hit('flak', q(5, 'two more squadrons') + k * 1.2, db=-20, pan=-0.5 + k * 0.2)
fx.bed('drone_far', q(5, 'two more squadrons'), V[6] + 0.5, db=-12)
# 6 follow the destroyer, Nagumo 10:20
fx.bed('cockpit', V[6], q(6, 'it is racing') + 0.5, db=-2); fx.hit('swish', q(6, 'it is racing') - 0.7, db=-6)
fx.bed('waves', q(6, 'it is racing'), V[7] + 1.0, db=-14); fx.bed('wind', q(6, 'it is racing'), V[7], db=-18)
fx.bed('drone_far', q(6, 'all morning'), q(6, 'nobody is watching'), db=-8)
for k in range(3): fx.hit('flyby', q(6, 'all morning') + 0.5 + k * 2.6, db=-12 - k * 2, pan=0.3 - k * 0.3)
fx.bed('drone_far', q(6, 'the sky') + 0.3, V[7] + 0.5, db=-12, fin=1.0)
# 7 Gay looks up
fx.bed('waves', V[7], V[8], db=-10); fx.bed('drone_far', q(7, 'he spots something'), V[8] + 0.5, db=-10, fin=0.8)
fx.hit('riser', q(7, 'making his run') - 0.5, db=-10); fx.hit('swish', V[8] - 0.7, db=-6)
# 8 the dive
tRoll = q(8, 'you roll over') - 0.3; tRel = q(8, 'release'); tBack = q(8, 'you pull out'); tFive = q(8, 'in about five'); tGot = q(8, 'but one of them') - 0.3
fx.bed('cockpit', V[8], tRoll + 1.0, db=-1)
fx.hit('dive_run', tRoll + 0.3, db=0, dur=tRel + 0.7 - tRoll - 0.3)
for k in range(5): fx.hit('flak', q(8, 'it grows in') + 0.5 + k * 0.7, db=-14, pan=-0.4 + k * 0.2)
fx.hit('explosion', tRel + 1.1, db=-2); fx.hit('explosion', tRel + 2.2, db=-8, pan=0.4)
fx.bed('cockpit', tBack - 0.4, tGot, db=-2, rpm=2300); fx.hit('flyby', tBack - 1.0, db=-6, pan=0.3)
fx.hit('dive_run', q(8, 'at the same moment') + 0.5, db=-12, dur=3.0); fx.hit('explosion', q(8, 'at the same moment') + 3.2, db=-10, pan=-0.5)
fx.bed('fire', tBack + 1.0, tGot + 1.0, db=-14)
fx.hit('explosion', tFive + 0.4, db=-10, pan=-0.5); fx.hit('explosion', tFive + 2.4, db=-12, pan=0.5)
fx.bed('waves', tGot - 0.5, V[9] + 0.5, db=-14); fx.hit('boom', q(8, 'and it is coming'), db=-6)
# 9 the Yorktown
fx.bed('waves', V[9], V[10], db=-14)
for k in range(4): fx.hit('dive_run', q(9, 'the carrier hiryus') + k * 1.8, db=-10, dur=2.5)
for k in range(14): fx.hit('flak', q(9, 'you fire at') + k * 0.35, db=-8, pan=0.3)
for d in (0.3, 0.9, 1.5): fx.hit('explosion', q(9, 'three bombs hit') + d, db=-2)
fx.bed('fire', q(9, 'three bombs hit') + 1, q(9, 'this time its'), db=-14)
for k in range(3): fx.hit('flyby', q(9, 'this time its') + k * 0.9, db=-8, pan=-0.5 + k * 0.5)
h1 = q(9, 'two of them') + 0.4; fx.hit('explosion', h1, db=0); fx.hit('explosion', h1 + 1.0, db=-1)
fx.hit('ship_horn', q(9, 'you are told'), db=-10)
fx.hit('dive_run', q(9, 'at five') - 0.5, db=-4, dur=q(9, 'four hits') - q(9, 'at five') + 0.8)
for d in (0, 0.3, 0.6, 0.9): fx.hit('explosion', q(9, 'four hits') + d, db=-3)
# 10 the cost
fx.bed('waves', q(10, 'the war went on'), DUR, db=-16)
fx.hit('boom', q(10, 'more than 3000'), db=-10); fx.hit('boom', q(10, '307 men'), db=-10)
fx.hit('page', q(10, 'in japan'), db=-10); fx.hit('page', q(10, 'admiral nimitz'), db=-10)
fx.bed('cockpit', q(10, 'and one pilot') - 0.3, q(10, 'admiral nimitz') - 0.3, db=-8)
S.write('fx.wav', fx.out())
print('music', len(plan), 'scenes; sounds used:', fx.used)
