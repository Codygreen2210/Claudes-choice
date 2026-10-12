#!/usr/bin/env python3
"""score.py: music and sound for Tulip Mania, written against the narration's own timing.

Music: scene by scene with studio/instruments/moods.py, in G (the money years bright, the crash and the cost in minor).
Sound: the studio library (studio/sfx/foley.py) on cue words: the auction room, coins, paper, ships, a bell for the plague.
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

sc = Score(DUR, key='G', seed=1637)
tStop = q(0, 'what nobody') - 0.3; tPlague = q(5, 'that winter a plague') - 0.4; tPaper = q(5, 'it was no longer') - 0.4; tSub = q(12, 'subscribe') - 0.4
sc.scene(0, tStop, 'tension', 0.45, enter='soft'); sc.scene(tStop, V[1], 'dread', 0.3, enter='cut')
PLAN = [(1, 'jaunty', 0.5, 'swell'), (2, 'wonder', 0.4, 'swell'), (3, 'mystery', 0.45, 'soft'), (4, 'jaunty', 0.6, 'cut')]
for i, mood, e, ent in PLAN: sc.scene(V[i], V[i + 1], mood, e, enter=ent)
sc.scene(V[5], tPlague, 'jaunty', 0.8, enter='cut'); sc.scene(tPlague, tPaper, 'dread', 0.35, enter='cut'); sc.scene(tPaper, V[6], 'jaunty', 0.7, enter='cut')
PLAN = [(6, 'jaunty', 0.95, 'hit'), (7, 'tension', 0.75, 'cut'), (8, 'grief', 0.35, 'swell'), (9, 'mystery', 0.4, 'soft'), (10, 'calm', 0.45, 'swell'), (11, 'tension', 0.6, 'cut')]
for i, mood, e, ent in PLAN: sc.scene(V[i], V[i + 1], mood, e, enter=ent)
sc.scene(V[12], tSub, 'wonder', 0.35, enter='swell'); sc.scene(tSub, DUR, 'wonder', 0.45, enter='swell')
plan = sc.write('music.wav', 'moods.json')

fx = F.Track(DUR, seed=1637)
# 1. Alkmaar: the room, the bidding, the hammer; then the empty room
fx.bed('murmur', 0.2, tStop, db=-10)
tBid = q(0, 'the bidding starts'); tHam = q(0, 'when the hammer')
fx.seq('coins', tBid + 1, tHam, db=-14, n=5)
fx.hit('gavel', tHam + 0.35, db=-3)
fx.hit('creak', tStop + 1.0, db=-12)
# 2. the richest place: water, ships, the exchange
fx.bed('hull', V[1], q(1, 'and for the first time'), db=-8)
fx.bed('murmur', q(1, 'amsterdam had'), q(1, 'and for the first time') + 0.5, db=-14)
fx.seq('walk', q(1, 'and for the first time'), V[2] - 1, db=-14, surface='stone')
# 3. tulips: wind on the mountain; night thieves over the wall
fx.bed('wind', V[2], q(2, 'and the ottoman'), db=-10)
tNight = q(2, 'so people climbed'); fx.bed('crickets', tNight - 0.4, q(2, 'within a few years'), db=-10)
fx.hit('creak', tNight + 0.8, db=-12); fx.hit('thud', tNight + 2.4, db=-14)
# 4. broken tulips: quiet; a soft boom on the price, a knock on the "no"
fx.hit('boom', q(3, 'in 1623') + 1.2, db=-12)
fx.hit('door_slam', q(3, 'the owner said no') + 0.6, db=-12)
# 5. the wind trade: the tavern, the paper, the wind
tTav = q(4, 'the deals were made'); fx.bed('murmur', tTav - 0.3, q(4, 'the dutch had a name'), db=-12)
fx.hit('page', q(4, 'they were trading promises') + 0.2, db=-8)
for k in range(3): fx.hit('clink', tTav + 1.0 + k * 0.8, db=-14)
fx.bed('wind', q(4, 'the dutch had a name') - 0.3, V[5] + 0.5, db=-6)
# 6. prices going up, the plague bell, paper passing
fx.seq('coins', V[5] + 0.5, tPlague - 0.5, db=-14, n=6)
for k in range(3): fx.hit('toll', tPlague + 0.6 + k * 2.6, db=-10)
for k in range(6): fx.hit('page', tPaper + 1 + k * 1.6, db=-14)
# 7. the pamphlet: a thump on each good
for ph in ['two loads of wheat', 'four of rye', 'four fat oxen', 'eight fat pigs', 'twelve fat sheep', 'two barrels of wine', 'four barrels of beer', 'two of butter', '1000 pounds of cheese', 'a bed', 'a suit of clothes', 'and a silver']:
    fx.hit('thud', q(6, ph), db=-14)
fx.hit('clink', q(6, 'and a silver') + 0.5, db=-8)
fx.hit('boom', q(6, 'all of that'), db=-10)
# 8. the crash: the room goes quiet
fx.bed('murmur', V[7], q(7, 'and nobody bid') - 0.2, db=-10, fout=0.3)
fx.hit('creak', q(7, 'and nobody bid') + 1.2, db=-10)
fx.seq('walk', q(7, 'the news went'), q(7, 'the news went') + 3, db=-16, surface='stone')
fx.bed('murmur', q(7, 'the alkmaar auction') - 0.2, V[8], db=-12)
# 9. who pays: the court, the torn paper, spring
fx.hit('gavel', q(8, 'sellers took buyers') + 0.4, db=-6)
fx.hit('scratch', q(8, 'in haarlem') + 3, db=-10)
fx.hit('page', q(8, 'the paper was torn'), db=-4)
fx.bed('wind', q(8, 'and the tulips bloomed') - 0.3, V[9], db=-14)
# 10. the legend: pages, a book
for k in range(4): fx.hit('page', q(9, 'preachers wrote') + 0.6 + k * 0.9, db=-12)
fx.hit('book', q(9, 'two hundred years later'), db=-6)
# 11. the records: a quiet archive with a clock
fx.seq('clock', V[10], q(10, 'the traders were'), db=-14)
fx.hit('book', V[10] + 1.5, db=-10)
fx.bed('hull', q(10, 'the dutch economy') - 0.3, q(10, 'the bubble was real'), db=-12)
# 12. the shape: a boom where the next buyer does not come
fx.hit('boom', q(11, 'and then one ordinary'), db=-8)
fx.bed('murmur', q(11, 'and then one ordinary') - 0.3, V[12], db=-18)
# 13. the flower
fx.bed('wind', V[12], q(12, 'the question in that tavern'), db=-14)
fx.bed('murmur', q(12, 'the question in that tavern') - 0.3, tSub, db=-14)
fx.hit('gavel', q(12, 'it was who will buy') + 2.2, db=-8)
S.write('fx.wav', fx.out())
print('music', len(plan), 'scenes; sounds used:', fx.used)
