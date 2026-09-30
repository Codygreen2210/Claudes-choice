#!/usr/bin/env node
// Usage: node reel.mjs demo.json [--format landscape|vertical|square|all] [--out name]
// Walks through your running app, then renders a launch video with captions and original music.
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, dirname, basename } from 'node:path';
import { checkScript } from './lib/script.mjs';
import { capture } from './lib/capture.mjs';
import { render } from './lib/render.mjs';
import { checkLicense } from './lib/license.mjs';

const args = process.argv.slice(2);
if (args[0] === 'studio') {
  // node reel.mjs studio [demo.json] [--port 4567]: the editor, in your browser.
  const { startStudio } = await import('./lib/studio-server.mjs');
  const { checkLicense } = await import('./lib/license.mjs');
  let chromium;
  try { ({ chromium } = await import('playwright')); } catch { console.error('LaunchReel needs Playwright: run  npm install playwright  then  npx playwright install chromium'); process.exit(1); }
  const i = args.indexOf('--port');
  const port = i > 0 ? Number(args[i + 1]) : 4567;
  const scriptPath = args[1] && !args[1].startsWith('--') ? resolve(args[1]) : null;
  await startStudio({ port, scriptPath, chromium, licensed: !!checkLicense(process.env.LAUNCHREEL_KEY), licenseKey: process.env.LAUNCHREEL_KEY || null });
  console.log(`LaunchReel studio is open at http://localhost:${port}  (Ctrl+C to stop)`);
  await new Promise(() => {});
}
const file = args.find((a) => !a.startsWith('--'));
const opt = (k) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : undefined; };
if (!file) { console.error('Usage: node reel.mjs demo.json [--format landscape|vertical|square|all] [--out name]'); process.exit(1); }
let script;
try { script = JSON.parse(readFileSync(file, 'utf8')); } catch (e) { console.error(`Couldn't read ${file}: ${e.message}`); process.exit(1); }
if (script && script.voice?.file) script.voice.file = resolve(dirname(resolve(file)), script.voice.file);
const errs = checkScript(script);
if (errs.length) { console.error('Fix these in ' + file + ':\n- ' + errs.join('\n- ')); process.exit(1); }
let chromium;
try { ({ chromium } = await import('playwright')); } catch { console.error('LaunchReel needs Playwright: run  npm install playwright  then  npx playwright install chromium'); process.exit(1); }

const lic = checkLicense(process.env.LAUNCHREEL_KEY || opt('key'));
script._licensed = !!lic;
if (!lic) console.log('Free version: the end card says "Made with LaunchReel". A Pro key removes it (set LAUNCHREEL_KEY).');
const fmts = (opt('format') || script.format || 'landscape') === 'all' ? ['landscape', 'vertical', 'square'] : [opt('format') || script.format || 'landscape'];
const base = opt('out') || join(dirname(resolve(file)), basename(file).replace(/\.json$/i, ''));
for (const fmt of fmts) {
  const dir = mkdtempSync(join(tmpdir(), 'reel-'));
  const out = `${base}-${fmt}.mp4`;
  const t0 = Date.now();
  try {
    process.stdout.write(`${fmt}: walking through ${script.url} ... `);
    const cap = await capture(script, { dir, format: fmt, chromium });
    process.stdout.write(`${Object.keys(cap.states).length} screens. Rendering ... `);
    const r = await render({ script, cap, fmt, dir, out, chromium, log: (m) => { if (/^ears/.test(m)) console.log('\n  ' + m); } });
    console.log(`done: ${out} (${r.duration.toFixed(1)}s video, ${((Date.now() - t0) / 1000).toFixed(0)}s to make)`);
  } catch (e) { console.log(''); console.error(e.message); process.exitCode = 1; }
  finally { if (process.env.REEL_KEEP) console.log('kept work folder: ' + dir); else rmSync(dir, { recursive: true, force: true }); }
}
