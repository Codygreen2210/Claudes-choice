// Plays all ten rounds in a real browser at phone and desktop sizes.
// Usage: node tools/play-check.mjs http://localhost:8765
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { makeGame, scoreRound, summarize } from '../sim.js';

const base = (process.argv[2] || 'http://localhost:8765').replace(/\/$/, '');
const screens = fileURLToPath(new URL('../screens/', import.meta.url));
mkdirSync(screens, { recursive: true });

const SEED = 12345;
const picks = [0, 1, 2, 3, 4, 2, 0, 4, 1, 3];
const expected = summarize(makeGame(SEED).map((round, i) => scoreRound(round, picks[i])));

const browser = await chromium.launch().catch(() => chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }));
const errors = [];

async function open(name, viewport, query, opts = {}) {
  const ctx = await browser.newContext({ viewport, ...opts });
  await ctx.grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => {});
  const page = await ctx.newPage();
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`${name}: ${m.text()}`); });
  page.on('pageerror', (e) => errors.push(`${name}: ${e.message}`));
  await page.goto(`${base}/index.html${query}`);
  await page.waitForSelector('.lane');
  return { ctx, page };
}

const noSideScroll = (page) => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

async function play(name, viewport, opts, useKeys) {
  const { ctx, page } = await open(name, viewport, `?s=${SEED}`, opts);
  assert.equal(await page.locator('.lane').count(), 5);
  assert.equal(await page.locator('#banner').isVisible(), false);
  assert.match(await page.locator('#prompt').innerText(), /Your cart: \d+ items/);
  if (viewport.width < 400) assert.ok(await noSideScroll(page), 'no horizontal scroll on round 1');
  await page.screenshot({ path: `${screens}${name}-round1.png` });
  for (let r = 0; r < 10; r++) {
    assert.equal(await page.locator('#round').innerText(), `${r + 1} / 10`);
    if (useKeys) await page.keyboard.press(String(picks[r] + 1));
    else await page.locator(`.lane[data-lane="${picks[r]}"]`).click();
    if (r === 0 && !opts.reducedMotion) {
      await page.waitForTimeout(2500);
      await page.screenshot({ path: `${screens}${name}-race.png` });
    }
    await page.locator('#next').waitFor({ state: 'visible', timeout: 15000 });
    assert.equal(await page.locator('.foot b').count(), 5, 'all five lanes have a finish place');
    assert.ok((await page.locator('#verdict').innerText()).length > 20);
    if (viewport.width < 400) assert.ok(await noSideScroll(page), `no horizontal scroll after round ${r + 1}`);
    if (r === 0) await page.screenshot({ path: `${screens}${name}-verdict.png`, fullPage: true });
    if (useKeys) await page.keyboard.press('Enter'); else await page.locator('#next').click();
  }
  await page.locator('#result').waitFor({ state: 'visible' });
  const distinct = await page.evaluate(() => {
    const c = document.getElementById('card');
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    const seen = new Set();
    for (let i = 0; i < d.length; i += 4 * 97) seen.add((d[i] << 16) | (d[i + 1] << 8) | d[i + 2]);
    return seen.size;
  });
  assert.ok(distinct > 4, `card canvas is drawn (${distinct} colours)`);
  const text = await page.locator('#challenge').getAttribute('data-share-text');
  assert.ok(text.includes(`${expected.topTwo}/10`), 'share text has the score');
  assert.ok(text.includes(`s=${SEED}&vs=${expected.topTwo}`), 'share text has the seed');
  assert.ok(text.includes(`${expected.pickShare}%`), 'share text has the pick share');
  assert.equal(await page.locator('#score').innerText(), `Top two ${expected.topTwo} · Wins ${expected.wins}`);
  if (viewport.width < 400) assert.ok(await noSideScroll(page), 'no horizontal scroll on card');
  await page.screenshot({ path: `${screens}${name}-card.png`, fullPage: true });
  await page.locator('#card').screenshot({ path: `${screens}${name}-card-only.png` });
  if (useKeys) {
    await page.evaluate(() => { navigator.share = undefined; });
    await page.locator('#challenge').click();
    await page.waitForFunction(() => document.getElementById('status').textContent.length > 0);
    assert.equal(await page.locator('#status').innerText(), 'Copied');
    await page.locator('#again').click();
    assert.equal(await page.locator('#round').innerText(), '1 / 10');
    assert.ok(!page.url().includes(`s=${SEED}`), 'new seed in URL');
  }
  await ctx.close();
}

await play('phone', { width: 390, height: 844 }, { hasTouch: true, isMobile: true, deviceScaleFactor: 2 }, false);
await play('desktop', { width: 1280, height: 800 }, { reducedMotion: 'reduce' }, true);

{
  const { ctx, page } = await open('vs', { width: 390, height: 844 }, `?s=${SEED}&vs=7`);
  assert.equal(await page.locator('#banner').isVisible(), true);
  assert.equal(await page.locator('#banner').innerText(), 'A friend got 7 / 10 on these same ten rounds. Beat it.');
  await page.screenshot({ path: `${screens}phone-vs-banner.png` });
  await ctx.close();
}
{
  const { ctx, page } = await open('noseed', { width: 360, height: 740 }, '');
  assert.match(page.url(), /\?s=\d+$/);
  assert.ok(await noSideScroll(page), 'no horizontal scroll at 360');
  await page.screenshot({ path: `${screens}phone-360.png` });
  await ctx.close();
}

await browser.close();
assert.deepEqual(errors, [], 'no console errors');
console.log(`play-check OK: phone + desktop, 10 rounds each, score ${expected.topTwo}/10, ${expected.wins} wins, 0 console errors`);
