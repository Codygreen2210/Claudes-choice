// The editor's local server. Only listens on this computer (127.0.0.1).
// Capture happens once per format; after that, captions, styles, timing and music are
// previewed live in the browser, and Export renders the MP4 with the same engine as the CLI.
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, existsSync, mkdtempSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, normalize, resolve, extname, basename } from 'node:path';
import { randomUUID } from 'node:crypto';
import { capture, FORMATS } from './capture.mjs';
import { render, studioHtml } from './render.mjs';
import { makeMusic, GENRES } from './music.mjs';
import { CAPTION_STYLES, FONTS, fontCss } from './styles.mjs';
import { checkScript } from './script.mjs';

const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.wav': 'audio/wav', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.json': 'application/json' };

export function startStudio({ port = 4567, scriptPath, outDir = process.cwd(), chromium, licensed = false }) {
  const caps = new Map(); // id -> {dir, cap, fmt}
  const tlSource = readFileSync(join(ROOT, 'lib/timeline.mjs'), 'utf8').replace(/^export /gm, '');
  const send = (res, code, body, type = 'application/json') => { res.writeHead(code, { 'content-type': type, 'cache-control': 'no-store' }); res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body)); };
  const file = (res, base, rel) => {
    const p = resolve(base, normalize(rel).replace(/^([/\\])+/, ''));
    if (!p.startsWith(resolve(base)) || !existsSync(p) || !statSync(p).isFile()) return send(res, 404, { error: 'not found' });
    send(res, 200, readFileSync(p), TYPES[extname(p)] || 'application/octet-stream');
  };
  const body = (req) => new Promise((ok, bad) => { let d = ''; req.on('data', (c) => { d += c; if (d.length > 2e6) req.destroy(); }); req.on('end', () => { try { ok(JSON.parse(d || '{}')); } catch (e) { bad(e); } }); });
  let busy = false;

  const server = createServer(async (req, res) => {
    const u = new URL(req.url, 'http://x');
    try {
      if (u.pathname === '/') return file(res, join(ROOT, 'editor'), 'index.html');
      if (u.pathname.startsWith('/editor/')) return file(res, join(ROOT, 'editor'), u.pathname.slice(8));
      if (u.pathname === '/lib/timeline.mjs') return file(res, join(ROOT, 'lib'), 'timeline.mjs');
      if (u.pathname.startsWith('/fonts/') && process.env.LAUNCHREEL_FONTS) return file(res, process.env.LAUNCHREEL_FONTS, u.pathname.slice(7));
      if (u.pathname.startsWith('/cap/')) { const [, , id, name] = u.pathname.split('/'); const c = caps.get(id); return c ? file(res, c.dir, name) : send(res, 404, {}); }
      if (u.pathname.startsWith('/out/')) return file(res, outDir, basename(u.pathname));
      if (u.pathname === '/api/setup') {
        let script = null;
        if (scriptPath && existsSync(scriptPath)) try { script = JSON.parse(readFileSync(scriptPath, 'utf8')); } catch {}
        return send(res, 200, { script, licensed, formats: Object.keys(FORMATS), views: Object.fromEntries(Object.entries(FORMATS).map(([k, v]) => [k, v.view])),
          styles: Object.fromEntries(Object.entries(CAPTION_STYLES).map(([k, v]) => [k, { label: v.label, font: v.font, weight: v.weight }])),
          genres: Object.fromEntries(Object.entries(GENRES).map(([k, v]) => [k, { label: v.label, blurb: v.blurb, bpm: v.bpm }])), fonts: Object.keys(FONTS), fontHead: fontCss(Object.keys(FONTS), { base: '/fonts/' }) });
      }
      if (u.pathname === '/api/capture' && req.method === 'POST') {
        const { script, format = 'landscape' } = await body(req);
        const errs = checkScript(script);
        if (errs.length) return send(res, 400, { error: errs.join('\n') });
        if (busy) return send(res, 409, { error: 'Still working on the last request.' });
        busy = true;
        try {
          const dir = mkdtempSync(join(tmpdir(), 'reel-studio-'));
          const cap = await capture(script, { dir, format, chromium });
          const id = randomUUID().slice(0, 8);
          caps.set(id, { dir, cap, fmt: format });
          return send(res, 200, { id, format, meta: cap.meta, events: cap.events, states: Object.fromEntries(Object.entries(cap.states).map(([k, v]) => [k, { height: v.height }])) });
        } finally { busy = false; }
      }
      if (u.pathname === '/api/studio' && req.method === 'POST') {
        const { id, script } = await body(req);
        const c = caps.get(id);
        if (!c) return send(res, 404, { error: 'Capture again: that session ended.' });
        const cap = { ...c.cap, events: script._events || c.cap.events };
        return send(res, 200, studioHtml({ fmt: c.fmt, meta: cap.meta, script: { ...script, _licensed: licensed }, states: c.cap.states, tlSource, imgBase: `/cap/${id}/`, fontBase: '/fonts/' }), TYPES['.html']);
      }
      if (u.pathname === '/api/music') {
        const q = Object.fromEntries(u.searchParams);
        const parts = Object.fromEntries(['drums', 'bass', 'chords', 'lead'].map((p) => [p, q[p] !== '0']));
        return send(res, 200, makeMusic({ seconds: Math.min(180, Number(q.seconds) || 20), genre: q.genre, key: q.key, seed: Number(q.seed) || 1, bpm: Number(q.bpm) || undefined, volume: Number(q.volume) || 0.5, parts }), TYPES['.wav']);
      }
      if (u.pathname === '/api/save' && req.method === 'POST') {
        const { script } = await body(req);
        const target = scriptPath || join(outDir, 'demo.json');
        const clean = JSON.parse(JSON.stringify(script, (k, v) => (k.startsWith('_') ? undefined : v)));
        writeFileSync(target, JSON.stringify(clean, null, 2) + '\n');
        return send(res, 200, { saved: target });
      }
      if (u.pathname === '/api/export' && req.method === 'POST') {
        const { id, script } = await body(req);
        const c = caps.get(id);
        if (!c) return send(res, 404, { error: 'Capture again: that session ended.' });
        if (busy) return send(res, 409, { error: 'Still working on the last request.' });
        busy = true;
        try {
          const name = `${(script.title || 'launchreel').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'launchreel'}-${c.fmt}.mp4`;
          const out = join(outDir, name);
          const cap = { ...c.cap, events: script._events || c.cap.events };
          const r = await render({ script: { ...script, _licensed: licensed }, cap, fmt: c.fmt, dir: c.dir, out, chromium });
          return send(res, 200, { file: name, url: '/out/' + name, duration: r.duration, path: out });
        } finally { busy = false; }
      }
      send(res, 404, { error: 'not found' });
    } catch (e) { send(res, 500, { error: e.message }); }
  });
  return new Promise((ok) => server.listen(port, '127.0.0.1', () => ok(server)));
}
