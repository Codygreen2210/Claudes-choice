// Packs the app into one self-contained page (demo/prosal-ledger.html) for a
// phone preview: styles, pay math and screen code inline, paid features on.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const read = (f) => readFile(join(root, f), 'utf8');
const strip = (js) => js.replace(/^import[\s\S]*?from\s+'[^']+';\n/gm, '').replace(/^export /gm, '');

const html = await read('index.html');
const title = /<title>[\s\S]*?<\/title>/.exec(html)[0];
const fonts = /<link rel="stylesheet"[^>]+>/.exec(html)[0];
const style = /<style>[\s\S]*?<\/style>/.exec(html)[0];
const body = /<body>([\s\S]*?)<script type="module" src="app\.js"><\/script>/.exec(html)[1];
const js = ['globalThis.PL_DEMO = true;', strip(await read('engine.js')), strip(await read('config.js')), strip(await read('app.js'))].join('\n');
if (/^\s*(import|export)\s/m.test(js)) throw new Error('an import or export survived the pack');

await mkdir(join(root, 'demo'), { recursive: true });
await writeFile(join(root, 'demo/prosal-ledger.html'), `${title}\n${fonts}\n${style}\n${body.trim()}\n<script type="module">\n${js}\n</script>\n`);
console.log('demo/prosal-ledger.html written');
