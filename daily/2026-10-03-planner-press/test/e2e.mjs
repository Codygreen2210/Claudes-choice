// A real run in a real browser, against the local server.
// Usage: node test/e2e.mjs   (needs Playwright; starts and stops its own server)
import { spawn } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { makeKey } from '../lib/license.mjs';
import { makePlan } from '../plan.js';
import { readPdf } from './pdftext.mjs';

const { chromium } = await import('playwright').catch(() => import('/opt/npm-tools/node_modules/playwright/index.mjs'));
const PORT = 4175;
const SECRET = ['e2e', 'secret', 'for', 'local', 'run'].join('-');
const SHOTS = process.env.SHOTS || '/tmp/planner-press-shots';
const CREDIT = 'Made with Planner Press';
await mkdir(SHOTS, { recursive: true });

const server = spawn(process.execPath, ['tools/dev-server.mjs', String(PORT)], { env: { ...process.env, PP_SECRET: SECRET }, stdio: ['ignore', 'pipe', 'inherit'] });
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
  const svg = (page) => page.locator('#paper').innerHTML();
  const where = (page) => page.textContent('#where');
  const countText = (page) => page.textContent('#count');
  const keyPage = async (page, name) => { await page.click(`[data-act="key-page"][data-v="${name}"]`); };
  const shot = (page, name) => page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: true });
  const download = async (page, file) => {
    const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 60000 }), page.click('[data-act="download"]')]);
    await dl.saveAs(`${SHOTS}/${file}`);
    return { name: dl.suggestedFilename(), pdf: readPdf(await readFile(`${SHOTS}/${file}`)) };
  };

  const desk = await open({ width: 1280, height: 900 });
  const phone = await open({ width: 400, height: 860 });

  await step('opens on a finished 2027 planner at desktop and phone width, no sideways scroll, no sign-up', async () => {
    for (const [page, name] of [[desk, 'desktop'], [phone, 'phone']]) {
      await page.goto(url);
      await page.waitForSelector('#paper svg');
      assert.equal(await where(page), 'Year overview');
      assert.match(await countText(page), /page 1 of 441\. The whole planner is 441 pages with 7,6\d\d tap links/);
      assert.ok((await svg(page)).includes('>2027<'));
      assert.equal(await page.locator('input[type="email"], input[type="password"]').count(), 0);
      await noSideScroll(page, name);
      await shot(page, `01-year-${name}`);
    }
  });

  await step('on a phone the preview comes before the options', async () => {
    const sheetY = await phone.locator('#paper').evaluate((e) => e.getBoundingClientRect().top);
    const optY = await phone.locator('[data-act="year"][data-v="2028"]').evaluate((e) => e.getBoundingClientRect().top);
    assert.ok(sheetY < optY, `preview at ${sheetY}, options at ${optY}`);
  });

  await step('the page says everything stays in the browser and the free file has a credit line', async () => {
    const t = await desk.textContent('footer.fine');
    assert.match(t, /Everything happens in this browser/);
    assert.ok(t.includes(CREDIT));
    assert.ok((await svg(desk)).includes(CREDIT));
  });

  await step('a month page and a week page look right (screenshots)', async () => {
    for (const [page, name] of [[desk, 'desktop'], [phone, 'phone']]) {
      await keyPage(page, 'month');
      assert.equal(await where(page), 'Month page');
      assert.ok((await svg(page)).includes('>January<'));
      await noSideScroll(page, `${name} month`);
      await shot(page, `02-month-${name}`);
      await keyPage(page, 'week');
      assert.equal(await where(page), 'Week page');
      assert.ok((await svg(page)).includes('>Week 2<'));
      await noSideScroll(page, `${name} week`);
      await shot(page, `03-week-${name}`);
      await keyPage(page, 'day');
      assert.equal(await where(page), 'Day page');
      const day = await svg(page);
      assert.ok(day.includes('>Monday<') && day.includes('January 4, 2027'));
    }
  });

  await step('tapping a tab or a date inside the preview follows the link', async () => {
    await keyPage(desk, 'year');
    await desk.locator('.lnk[data-page="4"]').first().click(); // the March tab
    assert.equal(await where(desk), 'Month page');
    assert.ok((await svg(desk)).includes('>March<'));
    const plan = makePlan({ year: 2027, weekStart: 0 });
    const wk = plan.weekNumberOf('2027-03-10');
    await desk.locator(`.lnk[data-page="${plan.at.week[wk]}"]`).first().click(); // a day number in that week's row
    assert.equal(await where(desk), 'Week page');
    assert.ok((await svg(desk)).includes(`>Week ${wk}<`));
    await desk.locator(`.lnk[data-page="${plan.at.day['2027-03-10']}"]`).first().click(); // Wednesday's header
    assert.equal(await where(desk), 'Day page');
    assert.ok((await svg(desk)).includes('March 10, 2027'));
    await desk.click('[data-act="prev"]');
    assert.ok((await svg(desk)).includes('March 9, 2027'));
    await desk.click('[data-act="next"]'); await desk.click('[data-act="next"]');
    assert.ok((await svg(desk)).includes('March 11, 2027'));
  });

  await step('changing the year changes the planner (2028 is a leap year with 366 daily pages)', async () => {
    await desk.click('[data-act="year"][data-v="2028"]');
    assert.ok((await svg(desk)).includes('2028'));
    const want = makePlan({ year: 2028, weekStart: 0 }).count;
    assert.match(await countText(desk), new RegExp(`of ${want}\\.`));
    assert.equal(want - makePlan({ year: 2028, weekStart: 0, sections: { day: false } }).count, 366);
    await keyPage(desk, 'day');
    assert.ok((await svg(desk)).includes('January 4, 2028'));
    await desk.click('[data-act="year"][data-v="2027"]');
  });

  await step('week start: Monday puts MON first on the month page; Sunday puts SUN first', async () => {
    await desk.click('[data-act="weekstart"][data-v="1"]');
    await keyPage(desk, 'month');
    let s = await svg(desk);
    assert.ok(s.indexOf('>MON<') < s.indexOf('>TUE<') && s.indexOf('>SAT<') < s.indexOf('>SUN<'));
    await keyPage(desk, 'week');
    s = await svg(desk);
    assert.ok(s.indexOf('>MON<') < s.indexOf('>SUN<'));
    await desk.click('[data-act="weekstart"][data-v="0"]');
    await keyPage(desk, 'month');
    s = await svg(desk);
    assert.ok(s.indexOf('>SUN<') < s.indexOf('>MON<'));
  });

  await step('sections: turn off daily pages and the page count drops by 365; the last section cannot be turned off', async () => {
    await desk.uncheck('[data-sec="day"]');
    assert.match(await countText(desk), /of 76\./);
    assert.equal(await desk.locator('[data-act="key-page"][data-v="day"]').count(), 0);
    await desk.check('[data-sec="day"]');
    assert.match(await countText(desk), /of 441\./);
    for (const id of ['year', 'month', 'week', 'day']) await desk.uncheck(`[data-sec="${id}"]`);
    assert.match(await countText(desk), /of 10\./);
    await desk.click('[data-sec="notes"]'); // the app refuses; a plain click, since uncheck() insists the box changes
    assert.ok(await desk.isChecked('[data-sec="notes"]'));
    assert.match(await desk.textContent('#toast'), /at least one section/);
    for (const id of ['year', 'month', 'week', 'day']) await desk.check(`[data-sec="${id}"]`);
    assert.match(await countText(desk), /of 441\./);
  });

  await step('page shape and color change the picture', async () => {
    await desk.click('[data-act="orient"][data-v="portrait"]');
    assert.ok((await svg(desk)).includes('viewBox="0 0 595 842"'));
    await desk.click('[data-act="theme"][data-v="night"]');
    assert.ok((await svg(desk)).includes('#161d2e'));
    await keyPage(desk, 'week');
    await shot(desk, '04-week-portrait-night-desktop');
    for (const t of ['sage', 'rose', 'classic']) { await desk.click(`[data-act="theme"][data-v="${t}"]`); await desk.waitForSelector('#paper svg'); }
    await desk.click('[data-act="orient"][data-v="landscape"]');
    assert.ok((await svg(desk)).includes('viewBox="0 0 842 595"'));
  });

  await step('the free download: 441 landscape pages, a credit line on every page, every link planned', async () => {
    await keyPage(desk, 'year');
    const { name, pdf } = await download(desk, 'free.pdf');
    const plan = makePlan({ year: 2027, weekStart: 0 });
    assert.equal(name, 'planner-2027-sunday-landscape.pdf');
    assert.ok(pdf.raw.startsWith('%PDF-'));
    assert.equal(pdf.pageCount, 441);
    assert.deepEqual([...new Set(pdf.pages.map((p) => `${p.w}x${p.h}`))], ['842x595']);
    assert.equal(pdf.linkCount, plan.expected.length);
    assert.equal(pdf.count(CREDIT), 441);
    // the March tab on page 1 jumps to page 4 inside the file itself
    const tabs = pdf.pages[0].links;
    assert.equal(tabs.length, 14 + 12);
    assert.ok(tabs.some((l) => l.page === 4));
    for (const p of pdf.pages) for (const l of p.links) assert.ok(l.page >= 1 && l.page <= 441);
    const bytes = (await readFile(`${SHOTS}/free.pdf`)).length;
    console.log(`   free PDF: ${bytes} bytes`);
  });

  await step('the pay step says "Not on sale yet." and a wrong pass is refused', async () => {
    await desk.click('[data-act="want"]');
    assert.match(await desk.textContent('#paybox'), /\$9, once/);
    assert.match(await desk.textContent('#paybox'), /Not on sale yet\./);
    await desk.fill('#key', 'PP1.abc.def');
    await desk.click('[data-act="key"]');
    await desk.waitForSelector('#paybox span[style]');
    assert.match(await desk.textContent('#paybox'), /not one of ours/);
    await shot(desk, '05-pay-desktop');
  });

  await step('a real pass removes the credit line from the screen and from the downloaded PDF', async () => {
    await desk.click('[data-act="year"][data-v="2028"]');
    await desk.click('[data-act="weekstart"][data-v="1"]');
    await desk.click('[data-act="orient"][data-v="portrait"]');
    await desk.click('[data-act="theme"][data-v="rose"]');
    assert.ok((await svg(desk)).includes(CREDIT));
    await desk.click('[data-act="want"]');
    await desk.fill('#key', makeKey({ exp: Date.now() + 5 * 86400000, id: 'e2e' }, SECRET));
    await desk.click('[data-act="key"]');
    await desk.waitForFunction(() => !document.querySelector('#paper').innerHTML.includes('Made with Planner Press'));
    assert.match(await desk.textContent('#buy'), /No credit line on any page/);
    const { name, pdf } = await download(desk, 'paid.pdf');
    const plan = makePlan({ year: 2028, weekStart: 1, orientation: 'portrait' });
    assert.equal(name, 'planner-2028-monday-portrait.pdf');
    assert.equal(pdf.pageCount, plan.count);
    assert.deepEqual([...new Set(pdf.pages.map((p) => `${p.w}x${p.h}`))], ['595x842']);
    assert.equal(pdf.linkCount, plan.expected.length);
    assert.equal(pdf.count(CREDIT), 0);
    assert.ok(!pdf.text.includes('Planner Press'));
    assert.ok(pdf.text.includes('(February 29, 2028) Tj'));
  });

  await step('the pass and the choices survive a reload', async () => {
    await desk.reload();
    await desk.waitForSelector('#paper svg');
    await desk.waitForSelector('[data-act="download"]');
    await desk.waitForFunction(() => /No credit line/.test(document.querySelector('#buy').textContent));
    assert.ok((await svg(desk)).includes('viewBox="0 0 595 842"'));
    assert.ok(!(await svg(desk)).includes(CREDIT));
    assert.equal(await desk.getAttribute('[data-act="year"][data-v="2028"]', 'aria-pressed'), 'true');
  });

  await step('phone: options, month and week pages, portrait day page, nothing runs sideways', async () => {
    await phone.click('[data-act="orient"][data-v="portrait"]');
    await keyPage(phone, 'month'); await shot(phone, '06-month-portrait-phone');
    await keyPage(phone, 'day'); await shot(phone, '07-day-portrait-phone');
    await noSideScroll(phone, 'phone portrait');
    await phone.click('[data-act="want"]');
    await noSideScroll(phone, 'phone pay box');
    await shot(phone, '08-pay-phone');
  });

  await step('dark mode reads', async () => {
    const dark = await open({ width: 400, height: 860 }, { colorScheme: 'dark' });
    await dark.goto(url);
    await dark.waitForSelector('#paper svg');
    await noSideScroll(dark, 'dark phone');
    await shot(dark, '09-dark-phone');
    const bg = await dark.evaluate(() => getComputedStyle(document.body).backgroundColor);
    assert.notEqual(bg, 'rgb(243, 240, 232)');
  });

  await step('the packed one-file demo runs on its own: preview and flipping work, no download button, a note about the live site', async () => {
    const inner = await readFile('demo/planner-press.html', 'utf8');
    assert.ok(inner.startsWith('<title>Planner Press</title>'));
    assert.ok(!/<\/?(html|head|body)[\s>]/i.test(inner));
    assert.ok(inner.includes('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'));
    await writeFile(`${SHOTS}/demo-wrapped.html`, `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>${inner}</body></html>`);
    const demo = await open({ width: 400, height: 860 });
    const lib = await readFile('vendor/jspdf.umd.min.js');
    let hits = 0;
    await demo.route('https://cdnjs.cloudflare.com/**', (r) => { hits++; return r.fulfill({ body: lib, contentType: 'text/javascript' }); });
    await demo.goto(`file://${SHOTS}/demo-wrapped.html`);
    await demo.waitForSelector('#paper svg');
    assert.equal(hits, 1);
    assert.equal(await where(demo), 'Year overview');
    assert.equal(await demo.locator('[data-act="download"], [data-act="want"]').count(), 0);
    assert.match(await demo.textContent('#buy'), /download works on the live site/);
    await keyPage(demo, 'week');
    assert.ok((await svg(demo)).includes('>Week 2<'));
    await demo.click('[data-act="theme"][data-v="sage"]');
    assert.ok((await svg(demo)).includes('#f8f6ef'));
    await noSideScroll(demo, 'demo');
    await shot(demo, '10-demo-phone');
  });

  assert.deepEqual(errors, [], 'no errors in the browser console');
  console.log(`\n${n} browser checks passed. Screenshots in ${SHOTS}`);
} finally {
  await browser.close();
  server.kill();
}
