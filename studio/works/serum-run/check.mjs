// check.mjs: run every frame time coarsely, report cue words that were not found and any page error
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright')
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }), p = await b.newPage({ viewport: { width: 1920, height: 1080 } })
const errs = []; p.on('pageerror', e => errs.push(e.message))
await p.goto('file://' + process.cwd() + '/film.html'); await p.evaluate(async () => { await window.__init() })
const dur = await p.evaluate(() => window.__duration)
let slow = 0, t0 = Date.now()
for (let t = 0; t < dur; t += 0.5) { await p.evaluate(t => window.__seek(t), t); if (errs.length) { console.log('ERROR at', t, errs[0]); break } }
console.log('duration', dur, 'ms/frame', ((Date.now() - t0) / (dur * 2)).toFixed(0))
console.log('missing cues:', await p.evaluate(() => window.__missing))
await b.close()
