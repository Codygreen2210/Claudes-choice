// Draws og.png (1200x630) from an HTML card. Run: node tools/make-og.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';

const out = fileURLToPath(new URL('../og.png', import.meta.url));
const heights = [[30, 22, 40, 26], [44, 30], [24, 36, 20, 28, 34], [38], [26, 42, 30]];
const lanes = heights.map((hs, i) => `<div class="lane${i === 3 ? ' mine' : ''}"><div class="till">${i + 1}</div>${
  hs.map((h) => `<div class="cart" style="height:${h}px"></div>`).join('')}${i === 3 ? '<div class="cart you" style="height:34px"></div>' : ''}</div>`).join('');

const html = `<!doctype html><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;width:1200px;height:630px;background:#faf3e7;color:#2a2320;
font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;display:flex;align-items:center;padding:0 70px;gap:60px}
.text{flex:1}.name{font-size:44px;font-weight:800;color:#b8430f;letter-spacing:-1px}
h1{font-size:84px;line-height:1.02;margin:14px 0 22px;letter-spacing:-3px;font-weight:800}
p{font-size:32px;margin:0;color:#6a5d55;font-weight:600}
.lanes{display:flex;gap:12px;height:470px}
.lane{width:78px;background:#e9dcc6;border:3px solid #d9cbb6;border-radius:14px;overflow:hidden;display:flex;flex-direction:column;align-items:center}
.lane.mine{border-color:#b8430f;background:#fffaf1}
.till{width:100%;background:#fffaf1;border-bottom:3px solid #d9cbb6;text-align:center;font-size:34px;font-weight:800;padding:8px 0;margin-bottom:14px}
.cart{width:52px;border:3px solid #2a2320;border-radius:4px 4px 10px 10px;background:#f2c879;margin-bottom:14px}
.cart.you{border-color:#b8430f;background:repeating-linear-gradient(135deg,#f2c879 0 6px,#fffaf1 6px 11px)}
</style><div class="text"><div class="name">Lane Luck</div><h1>Was it bad luck, or was it you?</h1>
<p>Pick a checkout lane. Ten rounds. Then see the split.</p></div><div class="lanes">${lanes}</div>`;

const exe = '/opt/pw-browsers/chromium';
const browser = await chromium.launch().catch(() => chromium.launch({ executablePath: exe }));
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
await page.setContent(html);
await page.screenshot({ path: out });
await browser.close();
console.log('wrote', out);
