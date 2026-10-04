// Lane Luck: pure game logic. No DOM, no clock, no unseeded randomness.
// Everything random comes from mulberry32(seed), so a seed fixes the ten rounds
// and their hidden snags for every player.

export const ROUNDS = 10;
export const LANES = 5;
export const PAYMENT_SECONDS = 25;
export const SNAG_CHANCE = 0.12;
export const SNAG_MIN = 40;
export const SNAG_MAX = 120;
export const EXPECTED_SNAG = SNAG_CHANCE * (SNAG_MIN + SNAG_MAX) / 2; // seconds per waiting shopper
export const GOOD_PICK_MARGIN = 0.05;
export const SPEED_MIN = 2.0;
export const SPEED_MAX = 4.5;
export const SPREAD = 0.3;
export const RANDOM_WINS_PER_TEN = 2; // 1 lane in 5, ten rounds
export const SNAG_KINDS = ['price check', 'coupons', 'card declined', 'forgot an item', 'chatty'];
export const VERDICTS = {
  gg: 'good pick, good result',
  gb: 'good pick, bad luck',
  bg: 'bad pick, got away with it',
  bb: 'bad pick, it cost you',
};

const SNAG_PHRASE = {
  'price check': 'a price check',
  'coupons': 'a coupon stack',
  'card declined': 'a declined card',
  'forgot an item': 'a forgotten item',
  'chatty': 'a chatty shopper',
};

export function mulberry32(a) {
  a >>>= 0;
  return function () {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Turn whatever is in the URL into a 32-bit seed.
export function seedFrom(value) {
  const s = String(value == null ? '' : value).trim();
  if (/^\d{1,10}$/.test(s)) return Number(s) >>> 0;
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function speedLabel(speed) {
  if (speed < 2.8) return 'quick';
  if (speed < 3.7) return 'steady';
  return 'slow';
}

const int = (rng, lo, hi) => lo + Math.floor(rng() * (hi - lo + 1));
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

function makeShopper(rng, items) {
  // Always draw all three numbers so the stream stays aligned.
  const roll = rng();
  const kind = SNAG_KINDS[Math.floor(rng() * SNAG_KINDS.length)];
  const seconds = int(rng, SNAG_MIN, SNAG_MAX);
  return { items, snag: roll < SNAG_CHANCE ? { kind, seconds } : null };
}

function makeRound(rng, index) {
  const playerItems = int(rng, 5, 30);
  const hasExpress = rng() < 0.4;
  const expressAt = int(rng, 0, LANES - 1);
  const load = 170 + rng() * 160; // typical seconds of queue in a lane this round
  const lanes = [];
  for (let i = 0; i < LANES; i++) {
    const speed = Math.round((SPEED_MIN + rng() * (SPEED_MAX - SPEED_MIN)) * 10) / 10;
    const express = hasExpress && i === expressAt;
    const shoppers = [];
    if (express) {
      const n = int(rng, 3, 6);
      for (let k = 0; k < n; k++) shoppers.push(makeShopper(rng, int(rng, 2, 9)));
    } else {
      const n = int(rng, 1, 6);
      // Aim each lane at a similar wait on paper (busy lanes get the quick
      // cashiers, short lanes the slow ones), then let it drift by SPREAD.
      const wait = load * (1 - SPREAD + 2 * SPREAD * rng());
      const total = Math.max(2 * n, (wait - n * (PAYMENT_SECONDS + EXPECTED_SNAG)) / speed);
      const weights = [];
      let sum = 0;
      for (let k = 0; k < n; k++) { const w = 0.3 + rng(); weights.push(w); sum += w; }
      for (let k = 0; k < n; k++) {
        shoppers.push(makeShopper(rng, clamp(Math.round(total * weights[k] / sum), 2, 40)));
      }
    }
    lanes.push({ speed, label: speedLabel(speed), express, shoppers });
  }
  return { index, playerItems, payment: PAYMENT_SECONDS, lanes };
}

export function makeGame(seed) {
  const rng = mulberry32(seedFrom(seed));
  const rounds = [];
  for (let r = 0; r < ROUNDS; r++) rounds.push(makeRound(rng, r));
  return rounds;
}

// Time for the player to be done in a lane: on paper, with no snags, and for real.
export function laneTimes(round, laneIndex) {
  const lane = round.lanes[laneIndex];
  let noSnag = round.playerItems * lane.speed + round.payment;
  let snagSeconds = 0;
  for (const s of lane.shoppers) {
    noSnag += s.items * lane.speed + round.payment;
    if (s.snag) snagSeconds += s.snag.seconds;
  }
  return {
    noSnag,
    expected: noSnag + lane.shoppers.length * EXPECTED_SNAG,
    actual: noSnag + snagSeconds,
    snagSeconds,
  };
}

// Who is at the till when, for drawing the race. Last entry is the player (or ghost).
export function laneTimeline(round, laneIndex) {
  const lane = round.lanes[laneIndex];
  const out = [];
  let t = 0;
  const carts = lane.shoppers.concat([{ items: round.playerItems, snag: null, player: true }]);
  for (const s of carts) {
    const start = t;
    const scanEnd = start + s.items * lane.speed;
    const snagEnd = scanEnd + (s.snag ? s.snag.seconds : 0);
    const end = snagEnd + round.payment;
    out.push({ start, scanEnd, snagEnd, end, snag: s.snag, player: !!s.player });
    t = end;
  }
  return out;
}

export function fmtDuration(seconds) {
  const s = Math.round(seconds);
  if (s < 60) return s + (s === 1 ? ' second' : ' seconds');
  const m = Math.floor(s / 60);
  const rest = s % 60;
  return rest === 0 ? m + ' min' : m + ' min ' + String(rest).padStart(2, '0');
}

export function ordinal(n) {
  return ['0th', '1st', '2nd', '3rd', '4th', '5th'][n] || n + 'th';
}

export function scoreRound(round, laneIndex) {
  const times = round.lanes.map((_, i) => laneTimes(round, i));
  let bestExpectedLane = 0;
  let bestActualLane = 0;
  for (let i = 1; i < times.length; i++) {
    if (times[i].expected < times[bestExpectedLane].expected) bestExpectedLane = i;
    if (times[i].actual < times[bestActualLane].actual) bestActualLane = i;
  }
  const ranks = times.map((t, i) =>
    1 + times.filter((o, j) => o.actual < t.actual || (o.actual === t.actual && j < i)).length);
  const mine = times[laneIndex];
  const bestExpected = times[bestExpectedLane].expected;
  const pickedRank = ranks[laneIndex];
  const goodPick = mine.expected <= bestExpected * (1 + GOOD_PICK_MARGIN);
  const goodResult = pickedRank <= 2;
  const verdictKey = (goodPick ? 'g' : 'b') + (goodResult ? (goodPick ? 'g' : 'g') : 'b');
  const lost = Math.max(0, mine.actual - times[bestActualLane].actual);
  const lostToPick = Math.min(lost, Math.max(0, mine.expected - bestExpected));
  const lostToLuck = Math.max(0, lost - lostToPick);

  const result = {
    lane: laneIndex, times, ranks, pickedRank, bestExpectedLane, bestActualLane,
    goodPick, verdictKey, verdict: VERDICTS[verdictKey],
    lost, lostToPick, lostToLuck,
    paperGap: Math.max(0, mine.expected - bestExpected),
  };
  result.text = explain(round, result);
  return result;
}

function explain(round, r) {
  const mineNo = r.lane + 1;
  const bestNo = r.bestExpectedLane + 1;
  const place = ordinal(r.pickedRank);
  const smart = r.lane === r.bestExpectedLane ? 'the smart choice' : 'a smart choice';
  if (r.verdictKey === 'gg') {
    return `Good pick, good result: lane ${mineNo} was ${smart} and you finished ${place}.`;
  }
  if (r.verdictKey === 'gb') {
    const snags = round.lanes[r.lane].shoppers.map((s) => s.snag).filter(Boolean);
    if (snags.length) {
      const worst = snags.reduce((a, b) => (b.seconds > a.seconds ? b : a));
      const total = r.times[r.lane].snagSeconds;
      return `Good pick, bad luck: lane ${mineNo} was ${smart}, ${SNAG_PHRASE[worst.kind]} cost you ${fmtDuration(total)}. You finished ${place}.`;
    }
    return `Good pick, bad luck: lane ${mineNo} was ${smart}, other lanes just dodged their snags. You finished ${place}.`;
  }
  const gap = fmtDuration(r.paperGap);
  if (r.verdictKey === 'bg') {
    return `Bad pick, got away with it: lane ${bestNo} was shorter on paper by ${gap}, but you still finished ${place}.`;
  }
  return `Bad pick, it cost you: lane ${bestNo} was shorter on paper by ${gap}. You finished ${place}.`;
}

export function summarize(results) {
  const verdicts = { gg: 0, gb: 0, bg: 0, bb: 0 };
  let wins = 0, topTwo = 0, lost = 0, lostToLuck = 0, lostToPick = 0;
  for (const r of results) {
    verdicts[r.verdictKey]++;
    if (r.pickedRank === 1) wins++;
    if (r.pickedRank <= 2) topTwo++;
    lost += r.lost;
    lostToLuck += r.lostToLuck;
    lostToPick += r.lostToPick;
  }
  const luckShare = lost > 0 ? Math.round((100 * lostToLuck) / lost) : 0;
  const pickShare = lost > 0 ? 100 - luckShare : 0;
  const goodPicks = verdicts.gg + verdicts.gb;
  let title;
  if (wins >= 6 && goodPicks >= 7) title = 'Lane whisperer';
  else if (goodPicks >= 7 && verdicts.gb >= 3) title = 'Sharp eye, cold cashier';
  else if (lost > 0 && luckShare >= 60 && goodPicks >= 5) title = 'Unlucky, honestly';
  else if (goodPicks >= 7) title = 'Steady hand';
  else if (lost > 0 && pickShare >= 55) title = 'It was you';
  else title = 'Coin flipper';
  return {
    rounds: results.length, wins, topTwo, verdicts, goodPicks,
    lost, lostToLuck, lostToPick, luckShare, pickShare, title,
    randomWins: RANDOM_WINS_PER_TEN * results.length / ROUNDS,
  };
}
