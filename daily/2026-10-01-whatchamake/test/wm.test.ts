import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { percentile, compare, cleanInput, occupations, areas, usMedian, occTitle, areaInfo } from '../lib/wages.ts';
import { FileStore } from '../lib/store.ts';

const BR = '12940', ELEC = '47-2111';

test('data loaded: real government numbers', () => {
  assert.ok(occupations().length > 200 && areas().length > 380);
  assert.equal(occTitle(ELEC), 'Electricians');
  assert.equal(areaInfo(BR)!.name, 'Baton Rouge, LA');
  assert.equal(areaInfo(BR)!.rpp, 90.8);
  assert.equal(occupations()[0].id, ELEC, 'common trades first');
});

test('percentile math', () => {
  const row: any = [20, 25, 30, 35, 40, 100];
  assert.equal(percentile(30, row), 50);
  assert.equal(percentile(25, row), 25);
  assert.equal(percentile(32.5, row), 63);
  assert.equal(percentile(40, row), 90);
  assert.ok(percentile(50, row) > 90 && percentile(50, row) <= 99);
  assert.ok(percentile(10, row) >= 1 && percentile(10, row) < 10);
  assert.equal(percentile(30, [null, null, 30, null, null, null] as any), 50, 'missing points are skipped');
});

test('comparison for a Baton Rouge electrician at $28.50', () => {
  const r = compare({ occ: ELEC, area: BR, hourly: 28.5, hours: 40, otHours: 10 });
  assert.equal(r.local!.median, 30.97);
  assert.equal(r.vsMedian, -2.47);
  assert.ok(r.percentile! > 10 && r.percentile! < 25, 'below the 25th percentile ($28.70)');
  assert.equal(r.buysLike, 31.39, '28.50 / 0.908');
  assert.equal(r.yearly, Math.round((28.5 * 40 + 28.5 * 1.5 * 10) * 52));
  assert.ok(usMedian(ELEC)! > 25 && usMedian(ELEC)! < 45);
});

test('bad input is refused with plain words', () => {
  const ok = { occ: ELEC, area: BR, hourly: '$28.50', hours: 40, otHours: 0 };
  assert.ok(cleanInput(ok).ok);
  for (const [k, v] of [['occ', 'nope'], ['area', '1'], ['hourly', '2'], ['hourly', 'abc'], ['hours', 0], ['otHours', 99], ['years', 70]] as const)
    assert.equal(cleanInput({ ...ok, [k]: v }).ok, false, `${k}=${v}`);
});

test('community numbers stay hidden under 5 people; one answer per person', async () => {
  const s = new FileStore(mkdtempSync(join(tmpdir(), 'wm-')));
  const i = (h: number) => ({ occ: ELEC, area: BR, hourly: h, hours: 40, otHours: 0 });
  for (const [u, h] of [['a', 25], ['b', 30], ['c', 32], ['d', 40]] as const) await s.save(u, i(h));
  assert.deepEqual(await s.community(ELEC, BR), { count: 4, median: null });
  await s.save('a', i(26)); // same person again replaces, doesn't add
  assert.equal((await s.community(ELEC, BR)).count, 4);
  await s.save('e', i(35));
  assert.deepEqual(await s.community(ELEC, BR), { count: 5, median: 32 });
  await s.remove('e');
  assert.equal((await s.community(ELEC, BR)).median, null);
});
