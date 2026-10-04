import test from 'node:test';
import assert from 'node:assert/strict';
import {
  makeGame, scoreRound, summarize, laneTimes, laneTimeline, mulberry32,
  VERDICTS, ROUNDS, LANES, RANDOM_WINS_PER_TEN, SNAG_MIN, SNAG_MAX,
} from '../sim.js';

test('same seed gives identical games, different seeds differ', () => {
  assert.deepEqual(makeGame(12345), makeGame(12345));
  assert.deepEqual(makeGame('12345'), makeGame(12345));
  assert.notDeepEqual(makeGame(12345), makeGame(12346));
});

test('rounds have 5 lanes and valid numbers', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const game = makeGame(seed);
    assert.equal(game.length, ROUNDS);
    for (const round of game) {
      assert.equal(round.lanes.length, LANES);
      assert.ok(round.playerItems >= 5 && round.playerItems <= 30);
      assert.ok(round.lanes.filter((l) => l.express).length <= 1);
      for (const lane of round.lanes) {
        assert.ok(lane.speed >= 2.0 && lane.speed <= 4.5);
        assert.ok(['quick', 'steady', 'slow'].includes(lane.label));
        assert.ok(lane.shoppers.length >= 1 && lane.shoppers.length <= 6);
        for (const s of lane.shoppers) {
          assert.ok(Number.isInteger(s.items) && s.items >= 2 && s.items <= 40);
          if (lane.express) assert.ok(s.items <= 10);
          if (s.snag) assert.ok(s.snag.seconds >= SNAG_MIN && s.snag.seconds <= SNAG_MAX);
        }
      }
    }
  }
});

test('times are positive, actual >= no-snag, timeline agrees', () => {
  for (let seed = 1; seed <= 200; seed++) {
    for (const round of makeGame(seed)) {
      for (let i = 0; i < LANES; i++) {
        const t = laneTimes(round, i);
        assert.ok(t.expected > 0 && t.actual > 0 && t.noSnag > 0);
        assert.ok(t.actual >= t.noSnag);
        const tl = laneTimeline(round, i);
        assert.ok(Math.abs(tl[tl.length - 1].end - t.actual) < 1e-6);
      }
    }
  }
});

test('one verdict per round; luck and pick seconds add up and are never negative', () => {
  const keys = Object.keys(VERDICTS);
  for (let seed = 1; seed <= 300; seed++) {
    const game = makeGame(seed);
    const results = [];
    for (const round of game) {
      for (let lane = 0; lane < LANES; lane++) {
        const r = scoreRound(round, lane);
        assert.equal(keys.filter((k) => VERDICTS[k] === r.verdict).length, 1);
        assert.equal(r.verdict, VERDICTS[r.verdictKey]);
        assert.ok(r.pickedRank >= 1 && r.pickedRank <= 5);
        assert.deepEqual([...r.ranks].sort(), [1, 2, 3, 4, 5]);
        assert.ok(r.lostToLuck >= 0 && r.lostToPick >= 0 && r.lost >= 0);
        assert.ok(Math.abs(r.lostToLuck + r.lostToPick - r.lost) < 1e-6);
        assert.equal(typeof r.text, 'string');
        if (lane === seed % LANES) results.push(r);
      }
    }
    const s = summarize(results);
    const v = s.verdicts;
    assert.equal(v.gg + v.gb + v.bg + v.bb, ROUNDS);
    assert.ok(Math.abs(s.lostToLuck + s.lostToPick - s.lost) < 1e-6);
    assert.ok(s.luckShare >= 0 && s.luckShare <= 100);
    assert.ok(s.title.length > 0);
  }
});

test('balance: skill matters and luck is real', (t) => {
  const games = 2000;
  const pick = mulberry32(99);
  let skilled = 0;
  let random = 0;
  for (let seed = 1; seed <= games; seed++) {
    for (const round of makeGame(seed)) {
      const best = scoreRound(round, 0).bestExpectedLane;
      if (scoreRound(round, best).pickedRank === 1) skilled++;
      if (scoreRound(round, Math.floor(pick() * LANES)).pickedRank === 1) random++;
    }
  }
  const skilledAvg = skilled / games;
  const randomAvg = random / games;
  t.diagnostic(`best-expected picker: ${skilledAvg.toFixed(2)} wins of 10; random picker: ${randomAvg.toFixed(2)}`);
  assert.equal(RANDOM_WINS_PER_TEN, 2);
  assert.ok(skilledAvg > 4, `skilled ${skilledAvg}`);
  assert.ok(skilledAvg < 7.5, `skilled ${skilledAvg}`);
  assert.ok(randomAvg > 1.7 && randomAvg < 2.3, `random ${randomAvg}`);
});
