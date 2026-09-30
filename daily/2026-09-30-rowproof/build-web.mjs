#!/usr/bin/env node
// Bundles lib/ into web/page.html so the page runs with no server and no build tools.
// node build-web.mjs            -> web/index.html (the full page, with file downloads)
// node build-web.mjs --artifact out.html  -> a copy for places that block downloads (copy-to-clipboard instead)
import { readFileSync, writeFileSync } from 'node:fs';
const here = (p) => new URL(p, import.meta.url);
const mods = ['std-widths', 'pdf', 'statement', 'export', 'rowproof'];
const bundle = mods.map((m) => `// ---- lib/${m}.mjs ----\n` + readFileSync(here(`lib/${m}.mjs`), 'utf8')
  .replace(/^import .*$/gm, '').replace(/^export \{[^}]*\} from .*$/gm, '')
  .replace(/^export (async function|function|const|class) /gm, '$1 ')).join('\n');
const b64 = (f) => readFileSync(here('web/samples/' + f)).toString('base64');
const samples = {
  bayou: { name: 'first-bayou-sample.pdf', data: b64('bayou.pdf') },
  misread: { name: 'first-bayou-one-wrong-amount.pdf', data: b64('bayou-misread.pdf') },
  uk: { name: 'thames-tyne-sample.pdf', data: b64('chrome.pdf') },
};
const art = process.argv.indexOf('--artifact');
const page = readFileSync(here('web/page.html'), 'utf8')
  // The engine gets its own scope so its names can't clash with the page's.
  .replace('/*BUNDLE*/', () => `const { convert, toCSV, toXLSX, toOFX, checkLabel } = (() => {\n${bundle}\nreturn { convert, toCSV, toXLSX, toOFX, checkLabel };\n})();`)
  .replace('/*ARTIFACT*/false', String(art >= 0))
  .replace('/*SAMPLES*/{}', () => JSON.stringify(samples));
if (art >= 0) writeFileSync(process.argv[art + 1], page);
else writeFileSync(here('web/index.html'), `<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n${page.replace(/(<\/style>)/, '$1\n</head><body>')}\n</body></html>\n`);
console.log('built', art >= 0 ? process.argv[art + 1] : 'web/index.html', Math.round(page.length / 1024) + 'KB');
