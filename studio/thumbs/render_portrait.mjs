// node render_portrait.mjs out.png '{"skin":"#d9a07a",...}'  -> transparent PNG of the character
import { createRequire } from 'node:module'; import path from 'node:path'; import url from 'node:url'
const require = createRequire(import.meta.url)
let pw; for (const p of ['playwright', '/home/claude/.npm-global/lib/node_modules/playwright']) { try { pw = require(p); break } catch {} }
const [out, spec] = process.argv.slice(2)
const b = await pw.chromium.launch(); const pg = await b.newPage({ viewport: { width: 1400, height: 1400 } })
await pg.goto(url.pathToFileURL(path.resolve(path.dirname(url.fileURLToPath(import.meta.url)), 'portrait.html')).href + '#' + encodeURIComponent(spec))
await pg.waitForFunction('window.__done'); await pg.screenshot({ path: out, omitBackground: true }); await b.close()
