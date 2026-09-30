// Prints a UK-style statement from HTML with Chrome, which embeds real fonts (the hard kind to read).
// One printed balance is wrong on purpose (row 9) to check that the mistake is caught.
// Run from a folder where playwright is installed: node make-chrome.mjs
import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';
const d = JSON.parse(readFileSync(new URL('./chrome-data.json', import.meta.url)));
const f = (x) => x.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const dmy = (s) => s.slice(8, 10) + '/' + s.slice(5, 7) + '/' + s.slice(0, 4);
const rows = d.rows.map((r, i) => `<tr><td>${dmy(r.date)}</td><td>${r.desc}</td><td class=n>${r.amt < 0 ? f(-r.amt) : ''}</td><td class=n>${r.amt > 0 ? f(r.amt) : ''}</td><td class=n>${f(i === 9 ? r.bal + 10 : r.bal)}</td></tr>`).join('');
const html = `<html><body style="font-family:Arial, sans-serif;font-size:11px;margin:40px">
<h2>Thames &amp; Tyne Building Society (fictional)</h2><p>Statement 03/02/2026 to 28/02/2026</p>
<table style="width:100%;border-collapse:collapse"><tr><th align=left>Date</th><th align=left>Description</th><th align=right>Paid out</th><th align=right>Paid in</th><th align=right>Balance</th></tr>
<tr><td></td><td>Balance brought forward</td><td></td><td></td><td class=n>${f(d.opening)}</td></tr>${rows}</table>
<style>.n{text-align:right} td{padding:3px 6px}</style></body></html>`;
const b = await chromium.launch(); const p = await b.newPage();
await p.setContent(html); await p.pdf({ path: new URL('./chrome.pdf', import.meta.url).pathname, format: 'A4' });
await b.close(); console.log('ok');
