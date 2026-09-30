// The editor's local server. Only listens on this computer (127.0.0.1).
// Capture happens once per format; after that, captions, styles, timing and music are
// previewed live in the browser, and Export renders the MP4 with the same engine as the CLI.
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, existsSync, mkdtempSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, normalize, resolve, extname, basename } from 'node:path';
import { randomUUID } from 'node:crypto';
import { capture, FORMATS } from './capture.mjs';
import { render, studioHtml, timelineFor, soundtrack } from './render.mjs';
import { toWav } from './mix.mjs';
import { inventory, promptToScript, anthropicCaller, proxyScript } from './ai.mjs';
import { copyFileSync } from 'node:fs';
import { makeMusic, GENRES } from './music.mjs';
import { CAPTION_STYLES, FONTS, fontCss } from './styles.mjs';
import { checkScript } from './script.mjs';

const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.wav': 'audio/wav', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.json': 'application/json' };

export function startStudio({ port = 4567, scriptPath, outDir = process.cwd(), chromium, licensed = false, licenseKey = null, aiCall = null }) {
  const caps = new Map(); // id -> {dir, cap, fmt}
  const voices = new Map(); // id -> wav path
  const voiceDir = mkdtempSync(join(tmpdir(), 'reel-voice-'));
  // The browser only knows a voice by id; swap in the real file before rendering.
  const withVoice = (script) => (script.voice?.id && voices.has(script.voice.id) ? { ...script, voice: { ...script.voice, file: voices.get(script.voice.id) } } : script.voice?.file ? script : { ...script, voice: null });
  const raw = (req, max = 40e6) => new Promise((ok, bad) => { const parts = []; let n = 0; req.on('data', (c) => { n += c.length; if (n > max) { bad(new Error('That file is too big (40 MB max).')); req.destroy(); } else parts.push(c); }); req.on('end', () => ok(Buffer.concat(parts))); });
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
        if (script?.voice?.file) { // load a saved voiceover so the editor can play it
          const f = resolve(scriptPath, '..', script.voice.file);
          if (existsSync(f)) { const id = randomUUID().slice(0, 8); const w = join(voiceDir, id + '.wav'); await toWav(f, w); voices.set(id, w); script.voice = { ...script.voice, id, url: '/voice/' + id + '.wav' }; delete script.voice.file; }
        }
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
      if (u.pathname === '/api/ai' && req.method === 'POST') {
        const { prompt, url, format = 'landscape' } = await body(req);
        try { new URL(url); } catch { return send(res, 400, { error: "Put in your app's address first." }); }
        const key = process.env.ANTHROPIC_API_KEY, hosted = process.env.LAUNCHREEL_AI_URL;
        if (!aiCall && !key && !(hosted && licenseKey)) return send(res, 400, { error: 'To write a video from a description, set ANTHROPIC_API_KEY (your own key: a few cents a video) before starting the studio, or use a Pro key with the hosted service.' });
        if (busy) return send(res, 409, { error: 'Still working on the last request.' });
        busy = true;
        try {
          const inv = await inventory(url, { chromium, mobile: format === 'vertical' });
          const r = aiCall || key ? await promptToScript({ prompt, url, inv, format, call: aiCall || anthropicCaller({ apiKey: key }) })
            : await proxyScript({ url: hosted, licenseKey, prompt, inv, format, pageUrl: url });
          return send(res, 200, { script: r.script, used: r.used, cap: r.cap });
        } catch (e) { return send(res, 422, { error: e.message }); }
        finally { busy = false; }
      }
      if (u.pathname === '/api/voice' && req.method === 'POST') {
        const data = await raw(req);
        if (data.length < 1000) return send(res, 400, { error: 'That recording is empty.' });
        const id = randomUUID().slice(0, 8);
        const src = join(voiceDir, id + '.upload'), wavPath = join(voiceDir, id + '.wav');
        writeFileSync(src, data);
        await toWav(src, wavPath);
        voices.set(id, wavPath);
        return send(res, 200, { id, seconds: +((statSync(wavPath).size - 44) / (44100 * 4)).toFixed(2), url: '/voice/' + id + '.wav' });
      }
      if (u.pathname.startsWith('/voice/')) return file(res, voiceDir, basename(u.pathname));
      if (u.pathname === '/api/audio' && req.method === 'POST') {
        const { id, script } = await body(req);
        const c = caps.get(id);
        if (!c) return send(res, 404, { error: 'Capture again: that session ended.' });
        const sc = withVoice(script);
        const tl = timelineFor({ script: sc, cap: { ...c.cap, events: script._events || c.cap.events }, fmt: c.fmt });
        const wavPath = await soundtrack({ script: sc, tl, dir: c.dir, name: 'preview.wav' });
        return send(res, 200, readFileSync(wavPath), TYPES['.wav']);
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
        if (clean.voice?.id && voices.has(clean.voice.id)) {
          const vf = join(resolve(target, '..'), 'voiceover.wav');
          copyFileSync(voices.get(clean.voice.id), vf);
          clean.voice = { file: 'voiceover.wav', at: clean.voice.at ?? 0, volume: clean.voice.volume ?? 1 };
        }
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
          const r = await render({ script: { ...withVoice(script), _licensed: licensed }, cap, fmt: c.fmt, dir: c.dir, out, chromium });
          return send(res, 200, { file: name, url: '/out/' + name, duration: r.duration, path: out });
        } finally { busy = false; }
      }
      send(res, 404, { error: 'not found' });
    } catch (e) { send(res, 500, { error: e.message }); }
  });
  return new Promise((ok) => server.listen(port, '127.0.0.1', () => ok(server)));
}
