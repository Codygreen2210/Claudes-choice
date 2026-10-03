// Local stand-in for the host: serves the app and runs the two /api files
// the way Vercel does. Usage: PL_SECRET=... node tools/dev-server.mjs [port]
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json' };
const api = { '/api/claim': () => import('../api/claim.js'), '/api/check': () => import('../api/check.js') };

createServer(async (req, res) => {
  const path = new URL(req.url, 'http://x').pathname;
  if (api[path]) {
    const shim = Object.assign(res, {
      status(c) { res.statusCode = c; return shim; },
      json(b) { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(b)); return shim; },
    });
    return (await api[path]()).default(req, shim);
  }
  const file = normalize(join(root, path === '/' ? 'index.html' : path));
  if (!file.startsWith(root)) { res.statusCode = 403; return res.end(); }
  try {
    res.setHeader('Content-Type', types[extname(file)] || 'application/octet-stream');
    res.end(await readFile(file));
  } catch { res.statusCode = 404; res.end('Not found'); }
}).listen(Number(process.argv[2]) || 4173, () => console.log('ProSal Ledger on http://localhost:' + (Number(process.argv[2]) || 4173)));
