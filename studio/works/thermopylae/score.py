#!/usr/bin/env python3
"""score.py: music and sound for Thermopylae, written against the narration's own timing.

Music: scored scene by scene with studio/instruments/moods.py (each scene a mood and an energy), in D minor.
Sound: everything from the studio library (studio/sfx/foley.py), placed on cue words.
Writes music.wav, moods.json (the plan pacing.py checks) and fx.wav.
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
V = [0.0] + [s['start'] - 0.45 for s in SC[1:]] + [DUR]          # when each scene's picture starts

# ---------------------------------------------------------------- music, scene by scene
sc = Score(DUR, key='D', seed=480)
PLAN = [  # scene, mood, energy, enter
    (0, 'mystery', 0.35, 'soft'), (1, 'march', 0.55, 'hit'), (2, 'calm', 0.4, 'swell'), (3, 'wonder', 0.45, 'swell'),
    (4, 'dread', 0.35, 'soft'), (5, 'action', 0.85, 'hit'), (6, 'tension', 0.6, 'cut'), (7, 'dread', 0.6, 'soft'),
    (8, 'grief', 0.35, 'swell'), (9, 'action', 1.0, 'hit'), (10, 'tension', 0.8, 'cut')]
for i, mood, e, ent in PLAN: sc.scene(V[i], V[i + 1], mood, e, enter=ent)
# after: grief, then the turn at Salamis, then grief again for the cost
tSal = q(11, 'a few weeks later') - 0.4; t20 = q(11, 'herodotus says 20000') - 0.4
sc.scene(V[11], tSal, 'grief', 0.4, enter='swell'); sc.scene(tSal, t20, 'triumph', 0.65, enter='hit'); sc.scene(t20, V[12], 'grief', 0.3, enter='cut')
tSub = q(12, 'subscribe') - 0.4
sc.scene(V[12], tSub, 'grief', 0.35, enter='swell'); sc.scene(tSub, DUR, 'wonder', 0.4, enter='swell')
plan = sc.write('music.wav', 'moods.json')

# ---------------------------------------------------------------- sound
fx = F.Track(DUR, seed=480)
# 1. the scout
fx.bed('wind', 0, V[1], db=-8)
fx.bed('waves', 0, V[1], db=-12)
fx.seq('hooves', 0.4, q(0, 'instead') - 0.5, db=-6)
fx.seq('hooves', q(0, 'he counts them'), q(0, 'he counts them') + 1.6, db=-8)
fx.hit('boom', q(0, 'three days'), db=-6)
# 2. the empire
fx.hit('war_horn', V[1] + 0.3, db=-6, pan=-0.3)
tCross = q(1, 'to cross from asia'); tStorm = q(1, 'when a storm'); tWhip = q(1, 'whipped')
fx.bed('waves', tCross - 0.4, tStorm, db=-10)
fx.seq('column', tCross + 1, tStorm, db=-12)
fx.bed('storm', tStorm - 0.3, tWhip + 0.8, db=-6)
fx.hit('thunder', tStorm + 0.5, db=-6)
for k in range(8): fx.hit('whip', tWhip + 0.1 + k * 0.42, db=-8 - k * 0.6, pan=0.4)
fx.hit('boom', q(1, 'historians today'), db=-9)
# 3. the Greeks
fx.seq('column', q(2, 'so one of its'), q(2, 'his name was'), db=-14)
fx.hit('boom', q(2, 'he picked'), db=-9)
fx.seq('column', q(2, 'on the way north'), V[3], db=-10)
# 4. the hot gates
fx.bed('wind', V[3], V[4], db=-10); fx.bed('waves', V[3], V[4], db=-12)
fx.seq('melee', q(3, 'in a space'), V[4], db=-14, per_s=2.5)
# 5. the wait: four nights of camp fires, then the arrows
fx.bed('fire', V[4], q(4, 'a story told'), db=-14); fx.bed('crickets', V[4], q(4, 'a story told'), db=-16)
tSun = q(4, 'block out the sun')
fx.seq('arrow_storm', tSun - 1.0, tSun + 5.5, db=-8, per_s=16, hits=0.0)
fx.bed('wind', V[5] - 5, V[5] + 4, db=-10)
# 6. day one
fx.hit('war_horn', V[5] + 0.6, db=-4, pan=-0.6)
fx.seq('melee', q(5, 'the greeks met'), q(5, 'herodotus says that') - 0.5, db=-5, per_s=6)
fx.bed('panic', q(5, 'the greeks met'), q(5, 'herodotus says that') - 0.3, db=-16)
fx.hit('war_horn', q(5, 'the immortals') - 0.4, db=-5, pan=-0.7)
for k, dt in enumerate((2.0, 3.6, 5.2)): fx.hit('thud', q(5, 'herodotus says that') + dt + 0.05, db=-8)
# 7. day two
fx.seq('melee', V[6] + 0.5, q(6, 'by sundown'), db=-9, per_s=4)
fx.bed('wind', q(6, 'by sundown'), V[7], db=-10)
# 8. the goat path
fx.bed('crickets', V[7], V[8], db=-13); fx.bed('wind', V[7], V[8], db=-14)
fx.seq('coins', q(7, 'he was hoping') + 0.6, q(7, 'he was hoping') + 1.6, db=-10, n=5)
tFeet = q(7, 'thousands of feet')
fx.seq('walk', q(7, 'just before dawn') - 0.5, V[8] - 0.5, db=-10, surface='dirt')
fx.seq('arrow_storm', q(7, 'they let a few') + 0.5, q(7, 'they let a few') + 2.5, db=-10, per_s=4, hits=0.4)
# 9. the choice
fx.bed('wind', V[8], V[9], db=-12)
fx.seq('walk', q(8, 'leonidas sent them'), q(8, 'leonidas sent them') + 4, db=-12, surface='dirt')
# 10. the last morning
fx.hit('war_horn', V[9] + 0.3, db=-4, pan=-0.6)
fx.seq('melee', V[9] + 1.0, V[10] - 0.5, db=-3, per_s=8)
fx.bed('panic', V[9] + 1.0, V[10], db=-12)
for k in range(10): fx.hit('whip', q(9, 'behind the persian lines') + 0.8 + k * 0.5, db=-10, pan=-0.5)
for k in range(6): fx.hit('splash', q(9, 'men were shoved') + k * 0.55 + 0.6, db=-8 - k, pan=0.2)
fx.hit('boom', q(9, 'and then leonidas fell') + 0.5, db=-3)
# 11. the hill
fx.hit('war_horn', q(10, 'then they heard it') + 0.6, db=-5, pan=0.7)
fx.seq('melee', V[10] + 0.5, q(10, 'the persians did not'), db=-6, per_s=5)
tShot = q(10, 'they stood back')
fx.seq('arrow_storm', tShot, V[11] - 0.4, db=-4, per_s=26, hits=0.45)
# 12. after
fx.bed('fire', q(11, 'the road south'), q(11, 'but the athenians'), db=-6)
fx.bed('waves', q(11, 'but the athenians') - 0.3, q(11, 'xerxes went home'), db=-9)
for k in range(4): fx.hit('thud', tSal + 2.4 + k * 0.5, db=-6); fx.hit('splash', tSal + 3.8 + k * 0.5, db=-9)
fx.hit('boom', t20 + 0.6, db=-6)
fx.hit('toll', q(11, 'in greek today') + 0.4, db=-10)
# 13. the stone
fx.bed('wind', V[12], tSub, db=-12)
tF = q(12, 'they found it')
for k in range(9): fx.hit('arrow_hit', tF - 0.3 + k * 0.33, db=-14 - k * 0.5, pan=np.sin(k) * 0.6)
fx.hit('boom', tSub, db=-12)
S.write('fx.wav', fx.out())
print('music', len(plan), 'scenes;', 'sounds used:', fx.used)
