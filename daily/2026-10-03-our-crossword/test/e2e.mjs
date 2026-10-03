// A real run in a real browser, against the local server.
// Usage: node test/e2e.mjs   (needs Playwright; starts and stops its own server)
import { spawn } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { makeKey } from '../lib/license.mjs';

const { chromium } = await import('playwright').catch(() => import('/opt/npm-tools/node_modules/playwright/index.mjs'));
const PORT = 4174;
const SECRET = ['e2e', 'secret', 'for', 'local', 'run'].join('-');
const SHOTS = process.env.SHOTS || '/tmp/our-crossword-shots';
await mkdir(SHOTS, { recursive: true });

const server = spawn(process.execPath, ['tools/dev-server.mjs', String(PORT)], { env: { ...process.env, OC_SECRET: SECRET }, stdio: ['ignore', 'pipe', 'inherit'] });
await new Promise((ok) => server.stdout.once('data', ok));
const browser = await chromium.launch();
const url = `http://localhost:${PORT}/`;
let n = 0;
const step = async (name, fn) => { await fn(); console.log(`ok ${++n} - ${name}`); };

try {
  const errors = [];
  const open = async (viewport, opts = {}) => {
    const ctx = await browser.newContext({ viewport, acceptDownloads: true, ...opts });
    const page = await ctx.newPage();
    page.on('console', (m) => { if (m.type() === 'error' && !/fonts\.g|ERR_|Failed to load resource/.test(m.text())) errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(String(e)));
    return page;
  };
  const noSideScroll = async (page, what) => {
    const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(over <= 0, `${what}: page scrolls sideways by ${over}px`);
  };
  const settle = (page) => page.waitForTimeout(260);
  const svg = (page) => page.locator('#paper').innerHTML();

  const desk = await open({ width: 1280, height: 900 });
  const phone = await open({ width: 400, height: 860 });

  await step('opens on a finished example at desktop and phone width, no sideways scroll', async () => {
    for (const [page, name] of [[desk, 'desktop'], [phone, 'phone']]) {
      await page.goto(url);
      await page.waitForSelector('#paper svg');
      assert.match(await page.textContent('#count'), /18 answers, every one crossing another\. Fits 8\.5 × 11 in\./);
      await noSideScroll(page, name);
      await page.screenshot({ path: `${SHOTS}/01-example-${name}.png`, fullPage: true });
    }
  });

  await step('on a phone the printed sheet comes before the form', async () => {
    const sheetY = await phone.locator('#paper').evaluate((e) => e.getBoundingClientRect().top);
    const formY = await phone.locator('#d-title').evaluate((e) => e.getBoundingClientRect().top);
    assert.ok(sheetY < formY);
  });

  await step('the free preview carries a watermark and shows no answers', async () => {
    const s = await svg(desk);
    assert.ok(s.includes('PREVIEW'));
    assert.ok(s.includes('Emma &amp; Jack'));
    assert.ok(!/>GOLDENRETRIEVER</.test(s) && !/font-weight="bold"[^>]*>G<\/text>/.test(s));
  });

  await step('typing a new title and clue redraws the sheet', async () => {
    await desk.fill('#d-title', 'Priya & Sam');
    await desk.fill('#c-4', 'The dog who runs the house');
    await settle(desk);
    const s = await svg(desk);
    assert.ok(s.includes('Priya &amp; Sam') && !s.includes('Emma &amp; Jack'));
    assert.ok(s.includes('The dog who runs the house'));
  });

  await step('the answer key tab shows the letters', async () => {
    await desk.click('[data-act="tab"][data-v="key"]');
    const s = await svg(desk);
    assert.ok(s.includes('ANSWER KEY'));
    assert.equal((s.match(/font-weight="bold"[^>]*>[A-Z]<\/text>/g) || []).length > 80, true);
    await desk.screenshot({ path: `${SHOTS}/02-answer-key.png`, fullPage: true });
    await desk.click('[data-act="tab"][data-v="puzzle"]');
  });

  await step('another layout, another look and another paper size each change the sheet', async () => {
    const before = await svg(desk);
    await desk.click('[data-act="shuffle"]');
    const shuffled = await svg(desk);
    assert.notEqual(shuffled, before);
    await desk.click('[data-act="theme"][data-v="midnight"]');
    assert.ok((await svg(desk)).includes('#16213a'));
    await desk.selectOption('#d-size', '5x7');
    assert.ok((await svg(desk)).includes('viewBox="0 0 360 504"'));
    await desk.screenshot({ path: `${SHOTS}/03-midnight-5x7.png`, fullPage: true });
    await desk.selectOption('#d-size', '24x36');
    assert.ok((await svg(desk)).includes('viewBox="0 0 1728 2592"'));
  });

  await step('starting fresh: two answers that share a letter make a puzzle; one that shares none is explained', async () => {
    await phone.click('[data-act="start"]');
    assert.match(await phone.textContent('#status'), /Add at least two answers/);
    await phone.fill('#d-title', 'Nana turns 80');
    await phone.fill('#a-0', 'Banana bread'); await phone.fill('#c-0', 'What she bakes every Sunday');
    await phone.fill('#a-1', 'Cabana'); await phone.fill('#c-1', 'Where we stayed in 1998');
    await phone.fill('#a-2', 'Xyz');
    await settle(phone);
    assert.match(await phone.textContent('#count'), /2 answers/);
    assert.match(await phone.textContent('[data-why="2"]'), /No letter in common/);
    assert.ok((await svg(phone)).includes('Nana turns 80'));
    await phone.fill('#a-3', 'A');
    await settle(phone);
    assert.match(await phone.textContent('[data-why="3"]'), /at least 2 letters/);
    await noSideScroll(phone, 'phone after typing');
    await phone.screenshot({ path: `${SHOTS}/04-own-phone.png`, fullPage: true });
  });

  await step('a pasted list becomes the puzzle', async () => {
    await phone.click('[data-act="paste"]');
    await phone.fill('#pastebox', 'Paris - Honeymoon city\nBiscuit: Our dog\nTacos - First-date dinner\nPancakes - Sunday tradition\nCoffee - Morning must');
    await phone.click('[data-act="use-paste"]');
    await settle(phone);
    assert.match(await phone.textContent('#count'), /5 answers/);
    assert.equal(await phone.inputValue('#c-1'), 'Our dog');
  });

  await step('everything survives a reload', async () => {
    await phone.reload();
    await phone.waitForSelector('#paper svg');
    assert.match(await phone.textContent('#count'), /5 answers/);
    assert.equal(await phone.inputValue('#d-title'), 'Nana turns 80');
  });

  await step('the file is behind the pay step; a wrong pass is refused', async () => {
    await phone.click('[data-act="want"]');
    assert.match(await phone.textContent('#paybox'), /\$9, once/);
    assert.equal(await phone.locator('[data-act="download"]').count(), 0);
    await phone.fill('#key', 'OC1.abc.def');
    await phone.click('[data-act="key"]');
    await phone.waitForSelector('#paybox span[style]');
    assert.match(await phone.textContent('#paybox'), /not one of ours/);
    await phone.screenshot({ path: `${SHOTS}/05-pay-phone.png`, fullPage: true });
  });

  await step('a real pass removes the watermark and downloads a two-page PDF at the chosen paper size', async () => {
    await phone.fill('#key', makeKey({ exp: Date.now() + 5 * 86400000, id: 'e2e' }, SECRET));
    await phone.click('[data-act="key"]');
    await phone.waitForSelector('[data-act="download"]');
    assert.ok(!(await svg(phone)).includes('PREVIEW'));
    await phone.selectOption('#d-size', '8x10');
    const [dl] = await Promise.all([phone.waitForEvent('download'), phone.click('[data-act="download"]')]);
    assert.equal(dl.suggestedFilename(), 'nana-turns-80-8x10.pdf');
    const path = `${SHOTS}/download.pdf`;
    await dl.saveAs(path);
    const raw = (await readFile(path)).toString('latin1');
    assert.ok(raw.startsWith('%PDF-'));
    const boxes = [...raw.matchAll(/\/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]/g)].map((m) => [Number(m[1]), Number(m[2])]);
    assert.deepEqual(boxes, [[576, 720], [576, 720]]);
    assert.ok(!raw.includes('PREVIEW'));
  });

  await step('the pass sticks after a reload', async () => {
    await phone.reload();
    await phone.waitForSelector('[data-act="download"]');
    await phone.screenshot({ path: `${SHOTS}/06-paid-phone.png`, fullPage: true });
  });

  await step('dark mode reads', async () => {
    const dark = await open({ width: 400, height: 860 }, { colorScheme: 'dark' });
    await dark.goto(url);
    await dark.waitForSelector('#paper svg');
    await dark.screenshot({ path: `${SHOTS}/07-dark-phone.png`, fullPage: true });
  });

  await step('the packed one-file demo runs on its own: no watermark, no download button', async () => {
    const inner = await readFile('demo/our-crossword.html', 'utf8');
    await writeFile(`${SHOTS}/demo-wrapped.html`, `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>${inner}</body></html>`);
    const demo = await open({ width: 400, height: 860 });
    const lib = await readFile('vendor/jspdf.umd.min.js');
    await demo.route('https://cdnjs.cloudflare.com/**', (r) => r.fulfill({ body: lib, contentType: 'text/javascript' }));
    await demo.goto(`file://${SHOTS}/demo-wrapped.html`);
    await demo.waitForSelector('#paper svg');
    assert.ok(!(await svg(demo)).includes('PREVIEW'));
    assert.equal(await demo.locator('[data-act="download"], [data-act="want"]').count(), 0);
    await noSideScroll(demo, 'demo');
  });

  assert.deepEqual(errors, [], 'no errors in the browser console');
  console.log(`\n${n} browser checks passed. Screenshots in ${SHOTS}`);
} finally {
  await browser.close();
  server.kill();
}
