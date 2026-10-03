// A real run in a real browser, against the local server.
// Usage: node test/e2e.mjs   (needs Playwright; starts and stops its own server)
import { spawn } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { makeKey } from '../lib/license.mjs';

const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright').catch(() => import('/opt/npm-tools/node_modules/playwright/index.mjs'));
const PORT = 4173;
const SECRET = ['e2e', 'secret', 'for', 'local', 'run'].join('-');
const SHOTS = process.env.SHOTS || '/tmp/prosal-shots';
await mkdir(SHOTS, { recursive: true });

const server = spawn(process.execPath, ['tools/dev-server.mjs', String(PORT)], { env: { ...process.env, PL_SECRET: SECRET }, stdio: ['ignore', 'pipe', 'inherit'] });
await new Promise((ok) => server.stdout.once('data', ok));
const browser = await chromium.launch();
const url = `http://localhost:${PORT}/`;
let n = 0;
const done = [];
const step = async (name, fn) => { await fn(); done.push(name); console.log(`ok ${++n} - ${name}`); };

try {
  const errors = [];
  const open = async (viewport, opts = {}) => {
    const ctx = await browser.newContext({ viewport, permissions: ['clipboard-read', 'clipboard-write'], ...opts });
    const page = await ctx.newPage();
    page.on('console', (m) => { if (m.type() === 'error' && !/fonts\.g|ERR_|Failed to load resource/.test(m.text())) errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(String(e)));
    return page;
  };
  const noSideScroll = async (page, what) => {
    const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(over <= 0, `${what}: page scrolls sideways by ${over}px`);
  };
  const type = async (page, sel, v) => { await page.fill(sel, v); await page.dispatchEvent(sel, 'change'); };

  const desk = await open({ width: 1280, height: 900 });
  const phone = await open({ width: 400, height: 860 });

  await step('opens on the example at desktop and phone width with no sideways scroll', async () => {
    for (const [page, name] of [[desk, 'desktop'], [phone, 'phone']]) {
      await page.goto(url);
      await page.waitForSelector('#sheet');
      await noSideScroll(page, name);
      await page.screenshot({ path: `${SHOTS}/01-example-${name}.png`, fullPage: true });
    }
    assert.match(await desk.textContent('.banner'), /Example numbers/);
  });

  await step('the example statement matches the numbers worked by hand', async () => {
    // Sep: 50,200 x 22% + 10,130 x 18% + 7,240 x 8% + 2,480 x 5% = 13,570.60 earned, 11,000 base
    assert.equal(await desk.textContent('#sheet .line.sub .amt'), '$13,570.60');
    assert.equal(await desk.textContent('#bonus'), '$2,570.60');
    // Mar: 12,663.40 earned - 11,000 base - 1,794.80 carried in from Feb = 131.40 short
    await desk.click('tr.pick:has-text("Mar 2026")');
    assert.match(await desk.textContent('#sheet'), /Less shortfall carried in\s*-\$1,794\.80/);
    assert.match(await desk.textContent('#sheet'), /came to \$131\.40 less than base pay plus the shortfall carried in/);
    await desk.screenshot({ path: `${SHOTS}/01b-march-desktop.png`, fullPage: true });
    assert.equal(await desk.evaluate(() => localStorage.getItem('prosal-ledger-v1')), null, 'looking at the example saves nothing');
  });

  await step('switching to the quarterly doctor shows a quarter', async () => {
    await desk.click('.chip:has-text("Dr. Jordan Example")');
    assert.match(await desk.textContent('#sheet'), /Jul 2026 to Sep 2026/);
    await desk.screenshot({ path: `${SHOTS}/02-quarterly.png`, fullPage: true });
  });

  await step('starting fresh: Owner Exchange numbers give a $2,060 shortfall, then a $940 bonus', async () => {
    await phone.click('[data-act="start"]');
    await type(phone, '#t-practice', 'Bayou Road Vet');
    await type(phone, '#t-name', 'Dr. Dana Okafor');
    await type(phone, '#t-base', '96000');
    await phone.fill('#t-start', '2026-01'); await phone.dispatchEvent('#t-start', 'change');
    for (const c of ['services', 'lab', 'pharmacy', 'preventives', 'other']) await type(phone, `#t-rate-${c}`, '22');
    assert.equal(await phone.inputValue('#t-base'), '96,000.00');
    await phone.click('[data-act="add-month"]');
    await type(phone, '#m-2026-01-services', '27000');
    assert.equal(await phone.textContent('#bonus'), '$0.00');
    assert.match(await phone.textContent('#sheet'), /came to \$2,060\.00 less than base pay/);
    await phone.screenshot({ path: `${SHOTS}/03-shortfall-phone.png`, fullPage: true });
    await phone.click('[data-act="add-month"]');
    await type(phone, '#m-2026-02-services', '$50,000');
    assert.equal(await phone.textContent('#bonus'), '$940.00');
    assert.match(await phone.textContent('#sheet'), /Less shortfall carried in\s*-\$2,060\.00/);
    await noSideScroll(phone, 'phone after entry');
    await phone.screenshot({ path: `${SHOTS}/04-bonus-phone.png`, fullPage: true });
  });

  await step('a typo is marked and does not change the statement', async () => {
    await phone.fill('#m-2026-02-services', '50,0x0');
    assert.ok(await phone.evaluate(() => document.querySelector('#m-2026-02-services').classList.contains('bad')));
    assert.equal(await phone.textContent('#bonus'), '$940.00');
    await type(phone, '#m-2026-02-services', '50000');
  });

  await step('numbers survive a reload', async () => {
    await phone.reload();
    await phone.waitForSelector('#sheet');
    assert.equal(await phone.textContent('#bonus'), '$940.00');
    assert.match(await phone.textContent('#sheet'), /Dr\. Dana Okafor/);
    assert.match(await phone.textContent('.pill'), /Free plan/);
  });

  await step('free plan: a second doctor, printing and payroll lines ask for the license', async () => {
    await phone.click('[data-act="add-doc"]');
    assert.equal(await phone.locator('.chip:not(.add)').count(), 1);
    assert.match(await phone.textContent('#toast'), /practice license/);
    await phone.click('[data-act="csv"]');
    assert.equal(await phone.evaluate(() => navigator.clipboard.readText()), '');
  });

  await step('a wrong key is refused with a reason', async () => {
    await phone.fill('#key', 'PL1.abc.def');
    await phone.click('[data-act="key"]');
    await phone.waitForSelector('#plans span[style]');
    assert.match(await phone.textContent('#plans'), /not one of ours/);
  });

  await step('a real key unlocks the practice license and sticks after reload', async () => {
    const key = makeKey({ name: 'Bayou Road Vet', exp: Date.now() + 30 * 86400000, id: 'e2e' }, SECRET);
    await phone.fill('#key', key);
    await phone.click('[data-act="key"]');
    await phone.waitForSelector('.pill.on');
    assert.match(await phone.textContent('.pill.on'), /Licensed to Bayou Road Vet/);
    await phone.reload();
    await phone.waitForSelector('.pill.on');
    await phone.click('[data-act="add-doc"]');
    assert.equal(await phone.locator('.chip:not(.add)').count(), 2);
    await phone.click('[data-act="del-doc"]'); await phone.click('[data-act="del-doc"]');
    assert.equal(await phone.locator('.chip:not(.add)').count(), 1);
    await phone.screenshot({ path: `${SHOTS}/05-licensed-phone.png`, fullPage: true });
  });

  await step('payroll lines copy out in a form a sheet can take', async () => {
    await phone.click('[data-act="csv"]');
    const csv = await phone.evaluate(() => navigator.clipboard.readText());
    const rows = csv.split('\n');
    assert.equal(rows[1], 'Dr. Dana Okafor,Jan 2026,27000.00,5940.00,8000.00,0.00,0.00,0.00,2060.00');
    assert.equal(rows[2], 'Dr. Dana Okafor,Feb 2026,50000.00,11000.00,8000.00,2060.00,940.00,0.00,0.00');
  });

  await step("the doctor's check link opens the same statement on another device, and saves nothing", async () => {
    await phone.click('[data-act="link"]');
    const link = await phone.evaluate(() => navigator.clipboard.readText());
    assert.match(link, /#check=/);
    const doc = await open({ width: 400, height: 860 });
    await doc.goto(link);
    await doc.waitForSelector('#sheet');
    assert.match(await doc.textContent('.banner'), /Bayou Road Vet sent you this statement/);
    assert.equal(await doc.textContent('#bonus'), '$940.00');
    assert.equal(await doc.locator('[data-act="print"]').count(), 0);
    await type(doc, '#m-2026-02-services', '60000');
    assert.equal(await doc.textContent('#bonus'), '$3,140.00');
    assert.equal(await doc.evaluate(() => localStorage.getItem('prosal-ledger-v1')), null);
    await noSideScroll(doc, 'check link');
    await doc.screenshot({ path: `${SHOTS}/06-check-link-phone.png`, fullPage: true });
  });

  await step('the printed page is the statement and ledger, without the buttons', async () => {
    await desk.emulateMedia({ media: 'print' });
    assert.equal(await desk.locator('.noprint:visible').count(), 0);
    assert.ok(await desk.locator('#sheet').isVisible());
    await desk.screenshot({ path: `${SHOTS}/07-print.png`, fullPage: true });
    await desk.emulateMedia({ media: 'screen' });
  });

  await step('dark theme reads', async () => {
    const dark = await open({ width: 400, height: 860 }, { colorScheme: 'dark' });
    await dark.goto(url);
    await dark.waitForSelector('#sheet');
    await dark.screenshot({ path: `${SHOTS}/08-dark-phone.png`, fullPage: true });
  });

  await step('the packed one-file demo runs on its own with paid features on', async () => {
    const inner = await readFile('demo/prosal-ledger.html', 'utf8');
    await writeFile(`${SHOTS}/demo-wrapped.html`, `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>${inner}</body></html>`);
    const demo = await open({ width: 400, height: 860 });
    await demo.goto(`file://${SHOTS}/demo-wrapped.html`);
    await demo.waitForSelector('#sheet');
    assert.match(await demo.textContent('.pill.on'), /Demo/);
    assert.equal(await demo.locator('[data-act="print"]').count(), 0);
    await demo.click('[data-act="add-doc"]');
    assert.equal(await demo.locator('.chip:not(.add)').count(), 3);
    await noSideScroll(demo, 'demo');
  });

  assert.deepEqual(errors, [], 'no errors in the browser console');
  console.log(`\n${done.length} browser checks passed. Screenshots in ${SHOTS}`);
} finally {
  await browser.close();
  server.kill();
}
