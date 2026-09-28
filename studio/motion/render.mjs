#!/usr/bin/env node
// render: turn an animated HTML page into video, frame-exact, at any size.
//
//   node studio/motion/render.mjs page.html --out film.mp4 [--size 1080x1920] [--fps 30] [--dur 12]
//        [--audio score.wav] [--workers 3] [--crf 16] [--from 0 --to 12] [--png]
// Frames are captured as high-quality JPEG (10x faster than PNG, invisible after H.264). --png for exact frames.
//   node studio/motion/render.mjs page.html --shots 0.5,2,4.25 --outdir stills/     (single frames)
//
// The page's contract (see kit.js):
//   window.__seek(t)      required. Draw the state at time t seconds. May be async.
//   window.__init()       optional. Awaited once after load (load fonts, measure text...).
//   window.__duration     optional. Used when --dur is not given.
// Time never runs on its own: every frame is set explicitly with __seek, so renders are exact and
// repeatable, and can be split across workers.

import { createRequire } from 'node:module'
import { spawn, execFileSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import url from 'node:url'

const require = createRequire(import.meta.url)
function playwright() {
  for (const p of [process.env.PLAYWRIGHT_PATH, 'playwright', '/home/claude/.npm-global/lib/node_modules/playwright'].filter(Boolean)) {
    try { return require(p) } catch {}
  }
  console.error('render: Playwright not found'); process.exit(2)
}

function args(argv) {
  const o = { page: null, out: 'out.mp4', size: [1080, 1920], fps: 30, dur: null, audio: null, workers: Math.max(1, Math.min(4, os.cpus().length - 1)), crf: 16, format: 'jpeg', shots: null, outdir: '.', from: 0, to: null, quiet: false }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i], v = () => argv[++i]
    if (a === '--out') o.out = v()
    else if (a === '--size') o.size = v().split('x').map(Number)
    else if (a === '--fps') o.fps = Number(v())
    else if (a === '--dur') o.dur = Number(v())
    else if (a === '--audio') o.audio = v()
    else if (a === '--workers') o.workers = Number(v())
    else if (a === '--crf') o.crf = Number(v())
    else if (a === '--png') o.format = 'png'
    else if (a === '--shots') o.shots = v().split(',').map(Number)
    else if (a === '--outdir') o.outdir = v()
    else if (a === '--from') o.from = Number(v())
    else if (a === '--to') o.to = Number(v())
    else if (a === '--quiet') o.quiet = true
    else o.page = a
  }
  if (!o.page) { console.error('usage: render.mjs page.html --out film.mp4 [--size WxH] [--fps 30] [--dur s] [--audio a.wav]'); process.exit(2) }
  return o
}

async function open(o) {
  const { chromium } = playwright()
  const browser = await chromium.launch({ args: ['--force-device-scale-factor=1', '--allow-file-access-from-files', '--disable-lcd-text', '--font-render-hinting=none', '--autoplay-policy=no-user-gesture-required'] })
  const page = await browser.newPage({ viewport: { width: o.size[0], height: o.size[1] }, deviceScaleFactor: 1 })
  page.on('pageerror', e => console.error('page exception:', e.message))
  page.on('console', m => { if (m.type() === 'error') console.error('page error:', m.text()) })
  const target = /^https?:/.test(o.page) ? o.page : url.pathToFileURL(path.resolve(o.page)).href
  await page.goto(target, { waitUntil: 'load' })
  await page.evaluate(async () => { if (window.__init) await window.__init(); if (document.fonts) await document.fonts.ready })
  const has = await page.evaluate(() => typeof window.__seek === 'function')
  if (!has) { console.error('render: the page has no window.__seek(t)'); process.exit(2) }
  const dur = o.dur ?? await page.evaluate(() => window.__duration || null)
  return { browser, page, dur }
}

const seek = (page, t) => page.evaluate(t => window.__seek(t), t)

async function renderRange(o, f0, f1, out) {
  const { browser, page } = await open(o)
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(o.fps), '-c:v', o.format === 'png' ? 'png' : 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', String(o.crf), '-pix_fmt', 'yuv420p', '-r', String(o.fps), out], { stdio: ['pipe', 'inherit', 'inherit'] })
  for (let f = f0; f < f1; f++) {
    await seek(page, f / o.fps)
    const buf = await page.screenshot(o.format === 'png' ? { type: 'png' } : { type: 'jpeg', quality: 95 })
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r))
    if (!o.quiet && (f - f0) % 90 === 0) process.stdout.write(`  ${path.basename(out)} frame ${f}/${f1}\n`)
  }
  ff.stdin.end()
  await new Promise(r => ff.on('close', r))
  await browser.close()
}

const o = args(process.argv.slice(2))

if (o.shots) {
  fs.mkdirSync(o.outdir, { recursive: true })
  const { browser, page } = await open(o)
  for (const t of o.shots) {
    await seek(page, t)
    const f = path.join(o.outdir, `t${t.toFixed(2).padStart(6, '0')}.png`)
    await page.screenshot({ path: f })
    console.log(f)
  }
  await browser.close()
  process.exit(0)
}

// work out the duration once
const probe = await open(o)
const dur = probe.dur
await probe.browser.close()
if (!dur) { console.error('render: no duration (pass --dur or set window.__duration)'); process.exit(2) }
const F0 = Math.round(o.from * o.fps), F1 = Math.round((o.to ?? dur) * o.fps)
const n = F1 - F0
const W = Math.max(1, Math.min(o.workers, Math.ceil(n / 30)))
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'render-'))
const t0 = Date.now()
const parts = []
for (let w = 0; w < W; w++) {
  const a = F0 + Math.floor(n * w / W), b = F0 + Math.floor(n * (w + 1) / W)
  parts.push({ a, b, file: path.join(tmp, `part${w}.mp4`) })
}
await Promise.all(parts.map(p => renderRange(o, p.a, p.b, p.file)))
const list = path.join(tmp, 'list.txt')
fs.writeFileSync(list, parts.map(p => `file '${p.file}'`).join('\n'))
const silent = path.join(tmp, 'silent.mp4')
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', silent])
fs.mkdirSync(path.dirname(path.resolve(o.out)), { recursive: true })
if (o.audio) {
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', silent, '-ss', String(o.from), '-i', o.audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', o.out])
} else {
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', silent, '-c', 'copy', '-movflags', '+faststart', o.out])
}
fs.rmSync(tmp, { recursive: true, force: true })
console.log(`${o.out}: ${n} frames, ${o.size.join('x')} @ ${o.fps} fps, ${W} worker(s), ${((Date.now() - t0) / 1000).toFixed(1)} s`)
