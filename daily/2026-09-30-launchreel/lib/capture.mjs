// Walks through your app in a real browser, following the script, and saves a full-page
// snapshot of every state the viewer should see, plus where each click landed.
import { createHash } from 'node:crypto';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

export const FORMATS = {
  landscape: { stage: [1920, 1080], view: [1120, 700], frame: 'browser' },
  square: { stage: [1080, 1080], view: [1120, 760], frame: 'browser' },
  vertical: { stage: [1080, 1920], view: [390, 844], frame: 'phone', mobile: true },
};

export async function capture(script, { dir, format = 'landscape', chromium, log = () => {} }) {
  const f = FORMATS[format];
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: f.view[0], height: f.view[1] }, deviceScaleFactor: 2,
    isMobile: !!f.mobile, hasTouch: !!f.mobile, colorScheme: script.theme === 'dark' ? 'dark' : 'light',
    reducedMotion: 'reduce',
  });
  const page = await ctx.newPage();
  const states = {};
  const byHash = new Map();
  let n = 0;
  const snap = async () => {
    await page.evaluate(() => document.fonts && document.fonts.ready).catch(() => {});
    await page.waitForTimeout(120);
    const png = await page.screenshot({ fullPage: true, animations: 'disabled', caret: 'hide' });
    const h = createHash('sha1').update(png).digest('hex');
    const scrollY = await page.evaluate(() => Math.round(window.scrollY));
    if (byHash.has(h)) return { id: byHash.get(h), scrollY };
    const id = 's' + n++;
    const file = join(dir, id + '.png');
    writeFileSync(file, png);
    const height = await page.evaluate(() => Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight || 0, innerHeight));
    states[id] = { file, height: Math.min(height, 16000) };
    byHash.set(h, id);
    return { id, scrollY };
  };
  const find = async (target, i) => {
    const loc = /^(text=|role=|css=|xpath=|#|\.|\[)|[>:]/.test(target) ? page.locator(target) : page.getByText(target, { exact: false });
    const el = loc.first();
    try { await el.waitFor({ state: 'visible', timeout: 6000 }); }
    catch { throw new Error(`Step ${i + 1}: couldn't find "${target}" on the page. Check the text or selector.`); }
    await el.scrollIntoViewIfNeeded().catch(() => {});
    return el;
  };
  const boxOf = async (el) => {
    const b = await el.boundingBox();
    const sy = await page.evaluate(() => window.scrollY);
    return b ? { x: b.x, y: b.y + sy, w: b.width, h: b.height } : { x: 0, y: sy, w: 10, h: 10 };
  };
  const settle = async () => {
    await page.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => {});
    await page.waitForTimeout(250);
    // Wait until the screen stops changing (smooth scrolls, inner scroll boxes, animations): two quick
    // snapshots 150ms apart must match. Gives up after 2.5s so a looping animation can't stall it.
    const t0 = Date.now();
    let prev = await page.screenshot({ type: 'jpeg', quality: 30 }).catch(() => null);
    while (prev && Date.now() - t0 < 2500) {
      await page.waitForTimeout(150);
      const next = await page.screenshot({ type: 'jpeg', quality: 30 }).catch(() => null);
      if (!next || next.equals(prev)) break;
      prev = next;
    }
  };

  const events = [];
  try {
    await page.goto(script.url, { waitUntil: 'networkidle', timeout: 30000 }).catch(async (e) => {
      if (/ERR_|NS_ERROR/.test(e.message)) throw new Error(`Couldn't open ${script.url}. Is the app running?`);
    });
    await page.evaluate(() => { const s = document.createElement('style'); s.textContent = '*{scroll-behavior:auto!important}::-webkit-scrollbar{display:none}'; document.head.appendChild(s); });
    await settle();
    const meta = await page.evaluate(() => ({
      title: document.title,
      theme: document.querySelector('meta[name="theme-color"]')?.content || null,
      // The app's own accent: the most used background colour on buttons and links.
      accent: (() => {
        const count = {};
        for (const el of document.querySelectorAll('button, a, [role=button], input[type=submit]')) {
          const c = getComputedStyle(el).backgroundColor;
          const m = c.match(/\d+/g); if (!m) continue;
          const [r, g, b, a = 1] = m.map(Number);
          if (a === 0 || (Math.max(r, g, b) - Math.min(r, g, b) < 24)) continue; // skip clear and grey
          count[c] = (count[c] || 0) + 1;
        }
        return Object.entries(count).sort((x, y) => y[1] - x[1])[0]?.[0] || null;
      })(),
    }));
    let cur = await snap();
    events.push({ kind: 'start', state: cur.id, scrollY: cur.scrollY, caption: script.steps[0]?.caption });
    for (let i = 0; i < script.steps.length; i++) {
      const s = script.steps[i];
      const cap = i === 0 ? undefined : s.caption;
      log(`step ${i + 1}/${script.steps.length}`);
      if (s.click || s.hover) {
        const el = await find(s.click || s.hover, i);
        const before = await snap();
        const box = await boxOf(el);
        if (s.click) await el.click({ timeout: 5000 }); else await el.hover();
        await settle();
        const after = await snap();
        events.push({ kind: s.click ? 'click' : 'hover', state: before.id, box, after: after.id, beforeScrollY: before.scrollY, afterScrollY: after.scrollY, caption: cap, hold: s.hold });
      } else if (s.type) {
        const [target, text] = s.type;
        const el = await find(target, i);
        const before = await snap();
        const box = await boxOf(el);
        await el.click();
        const chunks = Math.min(8, text.length);
        const frames = [];
        for (let k = 1; k <= chunks; k++) {
          const upto = Math.round((text.length * k) / chunks);
          await el.fill(text.slice(0, upto));
          frames.push((await snap()).id);
        }
        events.push({ kind: 'type', state: before.id, box, frames, caption: cap, hold: s.hold });
      } else if (s.scroll != null) {
        events.push({ kind: 'scroll', by: Number(s.scroll), caption: cap, hold: s.hold });
      } else if (s.zoom) {
        const el = await find(s.zoom, i);
        const st = await snap();
        events.push({ kind: 'zoom', state: st.id, box: await boxOf(el), caption: cap, hold: s.hold, max: s.max });
      } else if (s.wait != null || s.caption != null) {
        events.push({ kind: 'wait', ms: s.wait ?? 1200, caption: cap });
      }
    }
    return { events, states, meta: { ...meta, host: new URL(page.url()).host || script.url } };
  } finally {
    await browser.close();
  }
}
