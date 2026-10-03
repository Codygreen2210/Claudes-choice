// Packs the app into one self-contained page (demo/our-crossword.html) for a
// phone preview: styles and code inline, PDF library from a public CDN.
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
const body = /<body>([\s\S]*?)<script src="vendor/.exec(html)[1];
const js = ['globalThis.OC_DEMO = true;', strip(await read('construct.js')), strip(await read('layout.js')), strip(await read('config.js')), strip(await read('app.js'))].join('\n');
if (/^\s*(import|export)\s/m.test(js)) throw new Error('an import or export survived the pack');

await mkdir(join(root, 'demo'), { recursive: true });
await writeFile(join(root, 'demo/our-crossword.html'), `${title}\n${fonts}\n${style}\n${body.trim()}\n<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>\n<script type="module">\n${js}\n</script>\n`);
console.log('demo/our-crossword.html written');
