// Builds the frames for a how-to ad: the real app is driven step by step,
// and each frame is the live printed page plus the part of the form in use,
// under a plain caption. Output: frames + an ffconcat list.
import { spawn } from 'node:child_process';
import { writeFile, mkdir } from 'node:fs/promises';
const { chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs');
const SP = process.env.SP, ROOT = '/home/claude/claudes-choice/daily/2026-10-03-our-crossword';
const OUT = `${SP}/ad/frames`;
await mkdir(OUT, { recursive: true });
const SECRET = 'ad-local-secret-xxxxxxx';

const server = spawn(process.execPath, ['tools/dev-server.mjs', '4190'], { cwd: ROOT, env: { ...process.env, OC_SECRET: SECRET }, stdio: ['ignore', 'pipe', 'inherit'] });
await new Promise((ok) => server.stdout.once('data', ok));
const browser = await chromium.launch();
const pg = await (await browser.newContext({ viewport: { width: 520, height: 1000 }, deviceScaleFactor: 2 })).newPage();
const comp = await (await browser.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();

let n = 0;
const list = [];
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const shell = (inner) => `<!doctype html><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1920px;background:#f3f2f7;color:#1e1a2c;font-family:"DejaVu Sans",sans-serif;overflow:hidden}
.cap{height:270px;padding:70px 70px 0;font-size:58px;line-height:1.16;font-weight:bold;letter-spacing:-.5px}
.cap small{display:block;font-size:30px;font-weight:normal;color:#5a3e9f;letter-spacing:3px;text-transform:uppercase;margin-bottom:14px}
.paper{height:930px;display:flex;align-items:center;justify-content:center}
.paper img,.paper .blank{max-height:900px;max-width:720px;box-shadow:0 18px 50px rgba(30,26,44,.22);background:#fff}
.paper .blank{width:696px;height:900px;display:flex;align-items:center;justify-content:center;color:#a39eb8;font-size:30px;text-align:center;padding:60px;line-height:1.4}
.form{height:600px;display:flex;align-items:flex-start;justify-content:center;padding-top:34px}
.form img{max-width:980px;max-height:540px;border-radius:14px;box-shadow:0 8px 26px rgba(30,26,44,.14)}
.brand{position:absolute;left:0;right:0;bottom:44px;text-align:center;font-family:"DejaVu Serif",serif;font-size:34px;color:#5a3e9f}
.big{height:1920px;display:flex;flex-direction:column;justify-content:center;padding:0 90px;gap:36px}
.big h1{font-family:"DejaVu Serif",serif;font-size:104px;line-height:1.08;margin:0}
.big h1 em{color:#5a3e9f}
.big p{font-size:46px;line-height:1.35;margin:0;color:#605b73}
.big .rule{width:200px;height:6px;background:#5a3e9f}
</style>${inner}`;

const emit = async (html, hold) => {
  const f = `${OUT}/${String(++n).padStart(4, '0')}.png`;
  await writeFile(`${SP}/ad/frame.html`, html);
  await comp.goto(`file://${SP}/ad/frame.html`);
  await comp.screenshot({ path: f });
  list.push({ f, hold });
};
const card = (h1, p, hold) => emit(shell(`<div class="big"><div class="rule"></div><h1>${h1}</h1><p>${p}</p></div>`), hold);

// One frame: caption on top, the live sheet, then the piece of the form being used.
const frame = async (step, caption, formSel, hold) => {
  await pg.evaluate(() => { const t = document.querySelector('#toast'); if (t) t.hidden = true; });
  const hasPaper = await pg.locator('#paper svg').count();
  if (hasPaper) await pg.locator('#paper').screenshot({ path: `${SP}/ad/paper.png` });
  let form = '';
  if (formSel) { await pg.locator(formSel).first().screenshot({ path: `${SP}/ad/form.png` }); form = `<img src="form.png?${n}">`; }
  await emit(shell(`<div class="cap"><small>${esc(step)}</small>${esc(caption)}</div>
    <div class="paper">${hasPaper ? `<img src="paper.png?${n}">` : '<div class="blank">Your puzzle shows up here as you type</div>'}</div>
    <div class="form">${form}</div><div class="brand">Our Crossword</div>`), hold);
};
// Type into a box a couple of letters at a time, with a frame for each burst.
const typeIn = async (sel, text, step, caption, formSel, per = 2, hold = 0.085) => {
  await pg.click(sel);
  for (let i = 0; i < text.length; i += per) {
    await pg.type(sel, text.slice(i, i + per));
    if (i + per >= text.length) await pg.waitForTimeout(220);
    await frame(step, caption, formSel, hold);
  }
};

try {
  const { makeKey } = await import(`${ROOT}/lib/license.mjs`);
  await pg.goto('http://localhost:4190/'); await pg.waitForSelector('#paper svg');
  await pg.evaluate((k) => localStorage.setItem('our-crossword-pass', k), makeKey({ exp: Date.now() + 20 * 86400000, id: 'ad' }, SECRET));
  await pg.reload(); await pg.waitForSelector('[data-act="download"]');

  await card('A crossword<br>about <em>the two<br>of you.</em>', 'For wedding tables, showers and anniversaries. Made in a few minutes.', 2.6);
  await frame('How it works', 'Open the link. A finished example is waiting.', '.banner', 2.0);

  await pg.click('[data-act="start"]');
  await frame('Step 1', 'Type your names.', 'label.f:has(#d-title)', 0.5);
  await typeIn('#d-title', 'Priya & Sam', 'Step 1', 'Type your names.', 'label.f:has(#d-title)', 1, 0.1);
  await pg.fill('#d-subtitle', 'October 10, 2026 · Sip & Solve'); await pg.fill('#d-footer', 'Thank you for celebrating with us');
  await frame('Step 1', 'Type your names.', 'label.f:has(#d-title)', 0.5);

  const cap2 = 'Add answers and clues. It builds as you type.';
  for (const [i, a, c] of [[0, 'Lisbon', 'Where we met'], [1, 'Mango', 'Our cat'], [2, 'Ramen', 'First-date dinner']]) {
    await typeIn(`#a-${i}`, a, 'Step 2', cap2, '#rows', 2, 0.085);
    await typeIn(`#c-${i}`, c, 'Step 2', cap2, '#rows', 3, 0.075);
    await frame('Step 2', cap2, '#rows', 0.55);
  }

  await pg.click('[data-act="paste"]');
  await pg.fill('#pastebox', ['Lisbon - Where we met', 'Mango - Our cat', 'Ramen - First-date dinner', 'Trivia night - How Tuesdays go', 'Volvo - The car that will not die', 'Glacier - Where Sam proposed', 'Pediatrics - What Priya practices', 'Cello - Sam plays it badly', 'Portland - Home', 'Samosas - Made by Priya\'s mom', 'Backpacking - Our kind of trip', 'Espresso - Sam before 9 am', 'Marigold - The wedding flower', 'Kyoto - Honeymoon', 'Scrabble - The game we fight over', 'Maid of honor - Anjali, to Priya'].join('\n'));
  await frame('Step 2', 'Or paste your whole list at once.', 'label.f:has(#pastebox)', 1.5);
  await pg.click('[data-act="use-paste"]'); await pg.waitForTimeout(300);
  await frame('Step 2', '16 answers, every one crossing another.', '#count', 2.0);

  for (const [t, name] of [['garden', 'Garden'], ['blush', 'Blush'], ['midnight', 'Midnight'], ['classic', 'Classic']]) {
    await pg.click(`[data-act="theme"][data-v="${t}"]`);
    await frame('Step 3', `Pick a look: ${name}.`, '.chips[aria-label="Look"]', 0.85);
  }
  for (const [z, text] of [['5x7', 'A 5 × 7 table card.'], ['24x36', 'A 24 × 36 welcome sign.'], ['letter', 'Or plain 8.5 × 11 at home.']]) {
    await pg.selectOption('#d-size', z);
    await frame('Step 3', `Pick a size. ${text}`, 'label.f:has(#d-size)', 1.0);
  }
  await pg.click('[data-act="shuffle"]');
  await frame('Step 3', 'Tap for a different layout.', '.sheet > .row', 0.8);
  await pg.click('[data-act="shuffle"]');
  await frame('Step 3', 'Tap for a different layout.', '.sheet > .row', 0.9);
  await pg.click('[data-act="tab"][data-v="key"]');
  await frame('Included', 'The answer key comes with it.', '.sheet > .row', 1.7);
  await pg.click('[data-act="tab"][data-v="puzzle"]');
  await frame('Step 4', 'Download the print file and print it.', '.pay', 2.0);
  await card('Our <em>Crossword</em>', 'Free to make and preview.<br>$9 once for the print files.', 3.2);
} finally { await browser.close(); server.kill(); }

const total = list.reduce((s, x) => s + x.hold, 0);
await writeFile(`${SP}/ad/list.txt`, list.map((x) => `file '${x.f}'\nduration ${x.hold.toFixed(3)}`).join('\n') + `\nfile '${list[list.length - 1].f}'\n`);
console.log(n, 'frames', total.toFixed(2), 'seconds');
