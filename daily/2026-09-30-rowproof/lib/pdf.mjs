// A small PDF reader, no dependencies. It finds every piece of text on each page with
// its position and width, which is all a statement converter needs. Works in Node and
// in the browser; the caller passes an async `inflate` for compressed streams.
import { stdWidth } from './std-widths.mjs';

class Name { constructor(n) { this.n = n; } }
class PStr { constructor(b) { this.b = b; } }
class Ref { constructor(n, g) { this.n = n; this.g = g; } }
class Op { constructor(o) { this.o = o; } }
const EOF = Symbol('eof');
const isWS = (c) => c === ' ' || c === '\n' || c === '\r' || c === '\t' || c === '\f' || c === '\0';
const DEL = '()<>[]{}/%';
const isDict = (v) => v != null && v.constructor === Object;
const nm = (v) => (v instanceof Name ? v.n : undefined);

export function latin1(bytes) {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return s;
}

class Lexer {
  constructor(s, i = 0) { this.s = s; this.i = i; }
  skip() {
    const s = this.s;
    while (this.i < s.length) {
      const c = s[this.i];
      if (isWS(c)) { this.i++; continue; }
      if (c === '%') { while (this.i < s.length && s[this.i] !== '\n' && s[this.i] !== '\r') this.i++; continue; }
      return;
    }
  }
  next() {
    this.skip();
    const s = this.s;
    if (this.i >= s.length) return EOF;
    const c = s[this.i];
    if (c === '/') {
      let j = ++this.i;
      while (j < s.length && !isWS(s[j]) && !DEL.includes(s[j])) j++;
      const n = s.slice(this.i, j).replace(/#([0-9a-fA-F]{2})/g, (_, h) => String.fromCharCode(parseInt(h, 16)));
      this.i = j;
      return new Name(n);
    }
    if (c === '(') return new PStr(this.literal());
    if (c === '<') {
      if (s[this.i + 1] === '<') { this.i += 2; return this.dict(); }
      let j = s.indexOf('>', this.i);
      if (j < 0) j = s.length;
      let h = s.slice(this.i + 1, j).replace(/[^0-9a-fA-F]/g, '');
      if (h.length % 2) h += '0';
      this.i = j + 1;
      let b = '';
      for (let k = 0; k < h.length; k += 2) b += String.fromCharCode(parseInt(h.substr(k, 2), 16));
      return new PStr(b);
    }
    if (c === '[') {
      this.i++;
      const a = [];
      for (;;) {
        this.skip();
        if (this.i >= s.length) return a;
        if (s[this.i] === ']') { this.i++; return a; }
        const v = this.next();
        if (v === EOF) return a;
        a.push(v);
      }
    }
    if (DEL.includes(c)) { this.i++; return this.next(); } // stray delimiter: skip it
    let j = this.i;
    while (j < s.length && !isWS(s[j]) && !DEL.includes(s[j])) j++;
    const t = s.slice(this.i, j);
    this.i = j;
    if (/^[+-]?(\d+\.?\d*|\.\d+)$/.test(t)) {
      if (/^\d+$/.test(t)) {
        const m = /^\s+(\d+)\s+R(?![A-Za-z0-9])/.exec(s.slice(this.i, this.i + 24));
        if (m) { this.i += m[0].length; return new Ref(+t, +m[1]); }
      }
      return parseFloat(t);
    }
    if (t === 'true') return true;
    if (t === 'false') return false;
    if (t === 'null') return null;
    return new Op(t);
  }
  dict() {
    const d = {};
    const s = this.s;
    for (;;) {
      this.skip();
      if (this.i >= s.length) return d;
      if (s[this.i] === '>' && s[this.i + 1] === '>') { this.i += 2; return d; }
      const k = this.next();
      if (k === EOF) return d;
      if (!(k instanceof Name)) continue;
      d[k.n] = this.next();
    }
  }
  literal() {
    const s = this.s;
    const esc = { n: '\n', r: '\r', t: '\t', b: '\b', f: '\f', '(': '(', ')': ')', '\\': '\\' };
    let i = this.i + 1, depth = 1, out = '';
    while (i < s.length) {
      const c = s[i++];
      if (c === '\\') {
        const e = s[i++];
        if (esc[e] !== undefined) out += esc[e];
        else if (e >= '0' && e <= '7') {
          let o = e;
          while (o.length < 3 && s[i] >= '0' && s[i] <= '7') o += s[i++];
          out += String.fromCharCode(parseInt(o, 8) & 255);
        } else if (e === '\r') { if (s[i] === '\n') i++; }
        else if (e !== '\n') out += e;
      } else if (c === '(') { depth++; out += c; }
      else if (c === ')') { if (--depth === 0) break; out += c; }
      else out += c;
    }
    this.i = i;
    return out;
  }
}

function a85(s) {
  s = s.replace(/\s/g, '').replace(/^<~/, '').replace(/~>.*$/, '');
  let out = '';
  for (let i = 0; i < s.length;) {
    if (s[i] === 'z') { out += '\0\0\0\0'; i++; continue; }
    let chunk = s.slice(i, i + 5); i += 5;
    const pad = 5 - chunk.length;
    chunk += 'uuuu'.slice(0, pad);
    let n = 0;
    for (const ch of chunk) n = n * 85 + (ch.charCodeAt(0) - 33);
    const b = [(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255];
    out += String.fromCharCode(...b.slice(0, 4 - pad));
  }
  return out;
}

const mul = (a, b) => [
  a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
  a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
  a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5],
];

const WIN = { 0x80: '€', 0x82: '‚', 0x84: '„', 0x85: '…', 0x91: '‘', 0x92: '’', 0x93: '“', 0x94: '”', 0x95: '•', 0x96: '–', 0x97: '—', 0x99: '™', 0xa0: ' ' };
const GLYPH = { space: ' ', period: '.', comma: ',', hyphen: '-', minus: '-', endash: '–', emdash: '—', dollar: '$', parenleft: '(', parenright: ')', slash: '/', colon: ':', semicolon: ';', ampersand: '&', quoteright: '’', quotesingle: "'", quotedbl: '"', numbersign: '#', percent: '%', asterisk: '*', plus: '+', at: '@', underscore: '_', zero: '0', one: '1', two: '2', three: '3', four: '4', five: '5', six: '6', seven: '7', eight: '8', nine: '9' };
const glyphChar = (g) => GLYPH[g] ?? (/^uni([0-9A-Fa-f]{4})/.test(g) ? String.fromCharCode(parseInt(g.slice(3, 7), 16)) : g.length === 1 ? g : '');

function parseCMap(t) {
  const map = new Map();
  const lens = new Set();
  const u16 = (h) => { let o = ''; for (let i = 0; i + 4 <= h.length; i += 4) o += String.fromCharCode(parseInt(h.substr(i, 4), 16)); return o; };
  for (const b of t.matchAll(/begincodespacerange([\s\S]*?)endcodespacerange/g))
    for (const m of b[1].matchAll(/<([0-9a-fA-F]+)>/g)) lens.add(m[1].length / 2);
  for (const b of t.matchAll(/beginbfchar([\s\S]*?)endbfchar/g))
    for (const m of b[1].matchAll(/<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]*)>/g)) map.set(parseInt(m[1], 16), u16(m[2]));
  for (const b of t.matchAll(/beginbfrange([\s\S]*?)endbfrange/g))
    for (const m of b[1].matchAll(/<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*(?:<([0-9a-fA-F]+)>|\[([^\]]*)\])/g)) {
      const lo = parseInt(m[1], 16), hi = Math.min(parseInt(m[2], 16), lo + 65535);
      if (m[3] !== undefined) {
        const head = m[3].slice(0, -4), last = parseInt(m[3].slice(-4), 16);
        for (let c = lo; c <= hi; c++) map.set(c, u16(head + (last + c - lo).toString(16).padStart(4, '0')));
      } else {
        const list = [...m[4].matchAll(/<([0-9a-fA-F]*)>/g)].map((x) => u16(x[1]));
        list.forEach((v, k) => map.set(lo + k, v));
      }
    }
  return { map, len: lens.size === 1 ? [...lens][0] : null };
}

// Open a PDF. Returns { pages: [{ width, height, items: [{x, y, x2, str, size}] }], warnings }.
export async function extractText(bytes, { inflate, maxPages = 500 } = {}) {
  if (!inflate) throw new Error('extractText needs an inflate function');
  const s = latin1(bytes);
  if (!s.startsWith('%PDF') && s.indexOf('%PDF') > 1024) throw new Error("This file isn't a PDF.");
  const objs = new Map();
  const warnings = [];

  // 1. Find every "N G obj" in the file. Later copies win, which matches how PDFs are updated.
  const re = /(\d+)\s+(\d+)\s+obj\b/g;
  let m;
  while ((m = re.exec(s))) {
    const L = new Lexer(s, re.lastIndex);
    const v = L.next();
    L.skip();
    let stream = null;
    if (isDict(v) && s.startsWith('stream', L.i)) {
      let a = L.i + 6;
      if (s[a] === '\r') a++;
      if (s[a] === '\n') a++;
      const len = typeof v.Length === 'number' ? v.Length : -1;
      let b;
      if (len >= 0 && /^\s*endstream/.test(s.slice(a + len, a + len + 40))) b = a + len;
      else {
        b = s.indexOf('endstream', a);
        if (b < 0) b = s.length;
        if (s[b - 1] === '\n') b--;
        if (s[b - 1] === '\r') b--;
      }
      stream = { a, b };
      re.lastIndex = b;
    } else re.lastIndex = Math.max(L.i, re.lastIndex);
    objs.set(+m[1], { v, stream });
  }
  const R = (v) => { for (let k = 0; v instanceof Ref && k < 32; k++) v = objs.get(v.n)?.v ?? null; return v; };
  const rec = (v) => (v instanceof Ref ? objs.get(v.n) : null);
  // Stream lengths given as references can only be checked once everything is found.
  for (const o of objs.values()) {
    if (o.stream && o.v.Length instanceof Ref) {
      const len = R(o.v.Length);
      if (typeof len === 'number' && /^\s*endstream/.test(s.slice(o.stream.a + len, o.stream.a + len + 40))) o.stream.b = o.stream.a + len;
    }
  }
  if (/\/Encrypt\s*(\d+\s+\d+\s+R|<<)/.test(s)) throw new Error('This PDF is password-protected or encrypted. Open it, print it to a new PDF, and try that one.');

  async function data(o) {
    if (o.data !== undefined) return o.data;
    let d = s.slice(o.stream.a, o.stream.b);
    let f = R(o.v.Filter);
    f = f == null ? [] : Array.isArray(f) ? f.map(R) : [f];
    for (const x of f) {
      const n = nm(x);
      if (n === 'FlateDecode' || n === 'Fl') {
        const u8 = new Uint8Array(d.length);
        for (let i = 0; i < d.length; i++) u8[i] = d.charCodeAt(i);
        d = latin1(await inflate(u8));
      } else if (n === 'ASCIIHexDecode' || n === 'AHx') d = new Lexer('<' + d.replace(/>.*$/s, '') + '>').next().b;
      else if (n === 'ASCII85Decode' || n === 'A85') d = a85(d);
      else throw new Error(`unsupported compression (${n})`);
    }
    return (o.data = d);
  }

  // 2. Objects packed inside object streams (most modern PDFs).
  for (const o of [...objs.values()]) {
    if (!o.stream || nm(o.v.Type) !== 'ObjStm') continue;
    let d;
    try { d = await data(o); } catch { continue; }
    const first = R(o.v.First), n = R(o.v.N);
    const head = d.slice(0, first).trim().split(/\s+/).map(Number);
    for (let k = 0; k < n; k++) {
      const L = new Lexer(d, first + head[2 * k + 1]);
      objs.set(head[2 * k], { v: L.next(), stream: null });
    }
  }

  // 3. Walk the page tree from the document root.
  const roots = [...s.matchAll(/\/Root\s+(\d+)\s+(\d+)\s+R/g)];
  let catalog = roots.length ? R(new Ref(+roots.at(-1)[1], 0)) : null;
  if (!isDict(catalog)) catalog = [...objs.values()].map((o) => o.v).find((v) => isDict(v) && nm(v.Type) === 'Catalog');
  const pageDicts = [];
  const seen = new Set();
  (function walk(node, inherited) {
    node = R(node);
    if (!isDict(node) || seen.has(node) || pageDicts.length >= maxPages) return;
    seen.add(node);
    const inh = { Resources: node.Resources ?? inherited.Resources, MediaBox: node.MediaBox ?? inherited.MediaBox };
    if (nm(node.Type) === 'Page' || (!node.Kids && node.Contents)) pageDicts.push({ node, ...inh });
    else for (const k of R(node.Kids) || []) walk(k, inh);
  })(catalog && catalog.Pages, {});
  if (!pageDicts.length) throw new Error("Couldn't find any pages in this PDF.");

  const fontCache = new Map();
  async function loadFont(ref) {
    const key = ref instanceof Ref ? ref.n : ref;
    if (fontCache.has(key)) return fontCache.get(key);
    const fd = R(ref) || {};
    const sub = nm(R(fd.Subtype));
    const f = { type0: sub === 'Type0', codeLen: sub === 'Type0' ? 2 : 1, first: R(fd.FirstChar) ?? 0, widths: null, dw: 1000, cid: null, cmap: null, diff: null, base: nm(R(fd.BaseFont)) };
    if (f.type0) {
      const df = R((R(fd.DescendantFonts) || [])[0]) || {};
      f.dw = R(df.DW) ?? 1000;
      const W = R(df.W);
      if (Array.isArray(W)) {
        f.cid = new Map();
        for (let i = 0; i < W.length;) {
          const c = R(W[i]), nx = R(W[i + 1]);
          if (Array.isArray(nx)) { nx.forEach((w, k) => f.cid.set(c + k, R(w))); i += 2; }
          else { const w = R(W[i + 2]); for (let k = c; k <= nx && k - c < 65536; k++) f.cid.set(k, w); i += 3; }
        }
      }
    } else {
      const W = R(fd.Widths);
      if (Array.isArray(W)) f.widths = W.map(R);
      const enc = R(fd.Encoding);
      const D = isDict(enc) ? R(enc.Differences) : null;
      if (Array.isArray(D)) {
        f.diff = {};
        let c = 0;
        for (const x of D) { const y = R(x); if (typeof y === 'number') c = y; else if (y instanceof Name) f.diff[c++] = glyphChar(y.n); }
      }
    }
    const tu = rec(fd.ToUnicode);
    if (tu && tu.stream) {
      try { f.cmap = parseCMap(await data(tu)); if (f.cmap.len) f.codeLen = f.cmap.len; } catch { /* fall back to encoding */ }
    }
    if (f.type0 && !f.cmap) warnings.push(`A font (${f.base || 'unnamed'}) has no text map, so some text may be missing.`);
    fontCache.set(key, f);
    return f;
  }

  function decode(f, b) {
    const out = [];
    for (let i = 0; i + f.codeLen <= b.length;) {
      let code = 0;
      for (let k = 0; k < f.codeLen; k++) code = code * 256 + b.charCodeAt(i + k);
      i += f.codeLen;
      let ch = f.cmap?.map.get(code);
      if (ch === undefined) ch = f.type0 ? '' : f.diff?.[code] ?? WIN[code] ?? (code >= 32 ? String.fromCharCode(code) : '');
      let w;
      if (f.type0) w = f.cid?.get(code) ?? f.dw;
      else w = f.widths?.[code - f.first] ?? (code >= 32 && code < 127 ? stdWidth(f.base, code) : 500);
      out.push({ ch, w, space: f.codeLen === 1 && code === 32 });
    }
    return out;
  }

  const pages = [];
  for (const pd of pageDicts) {
    const items = [];
    const mb = (R(pd.MediaBox) || [0, 0, 612, 792]).map(R);
    const contents = R(pd.node.Contents);
    const parts = Array.isArray(contents) ? contents : contents ? [pd.node.Contents] : [];
    let content = '';
    for (const p of parts) {
      const o = rec(p);
      if (o && o.stream) { try { content += (await data(o)) + '\n'; } catch (e) { warnings.push(`Page ${pages.length + 1}: ${e.message}`); } }
    }
    await run(content, R(pd.Resources) || {}, [1, 0, 0, 1, 0, 0], items, 0);
    pages.push({ width: mb[2] - mb[0], height: mb[3] - mb[1], items });
  }

  async function run(content, res, ctm0, items, depth) {
    if (depth > 8) return;
    const L = new Lexer(content);
    const stack = [];
    const gstack = [];
    let g = { ctm: ctm0, font: null, fs: 0, tc: 0, tw: 0, th: 1, tl: 0, rise: 0 };
    let tm = [1, 0, 0, 1, 0, 0], tlm = [1, 0, 0, 1, 0, 0];
    const fonts = R(res.Font) || {};
    const xobjs = R(res.XObject) || {};
    const nl = () => { tlm = mul([1, 0, 0, 1, 0, -g.tl], tlm); tm = tlm.slice(); };
    const show = (ps) => {
      if (!(ps instanceof PStr) || !g.font) return;
      const glyphs = decode(g.font, ps.b);
      const trm = mul([g.fs * g.th, 0, 0, g.fs, 0, g.rise], mul(tm, g.ctm));
      let adv = 0, str = '';
      for (const gl of glyphs) { str += gl.ch; adv += ((gl.w / 1000) * g.fs + g.tc + (gl.space ? g.tw : 0)) * g.th; }
      tm = mul([1, 0, 0, 1, adv, 0], tm);
      const end = mul([1, 0, 0, 1, 0, g.rise], mul(tm, g.ctm));
      const size = Math.hypot(trm[2], trm[3]);
      if (Math.abs(trm[1]) > 0.01 * size || trm[0] <= 0) return; // skip rotated or mirrored text (watermarks)
      if (str.trim()) items.push({ x: trm[4], y: trm[5], x2: end[4], str, size });
    };
    for (;;) {
      const t = L.next();
      if (t === EOF) break;
      if (!(t instanceof Op)) { stack.push(t); continue; }
      const a = stack;
      const n = (k) => (typeof a[a.length - k] === 'number' ? a[a.length - k] : 0);
      switch (t.o) {
        case 'q': gstack.push({ ...g }); break;
        case 'Q': if (gstack.length) g = gstack.pop(); break;
        case 'cm': g.ctm = mul([n(6), n(5), n(4), n(3), n(2), n(1)], g.ctm); break;
        case 'BT': tm = [1, 0, 0, 1, 0, 0]; tlm = tm.slice(); break;
        case 'Tf': g.font = await loadFont(fonts[nm(a[a.length - 2])] ?? null); g.fs = n(1); break;
        case 'Tc': g.tc = n(1); break;
        case 'Tw': g.tw = n(1); break;
        case 'Tz': g.th = n(1) / 100; break;
        case 'TL': g.tl = n(1); break;
        case 'Ts': g.rise = n(1); break;
        case 'Td': tlm = mul([1, 0, 0, 1, n(2), n(1)], tlm); tm = tlm.slice(); break;
        case 'TD': g.tl = -n(1); tlm = mul([1, 0, 0, 1, n(2), n(1)], tlm); tm = tlm.slice(); break;
        case 'Tm': tlm = [n(6), n(5), n(4), n(3), n(2), n(1)]; tm = tlm.slice(); break;
        case 'T*': nl(); break;
        case 'Tj': show(a[a.length - 1]); break;
        case "'": nl(); show(a[a.length - 1]); break;
        case '"': g.tw = n(3); g.tc = n(2); nl(); show(a[a.length - 1]); break;
        case 'TJ':
          for (const el of Array.isArray(a[a.length - 1]) ? a[a.length - 1] : []) {
            if (typeof el === 'number') tm = mul([1, 0, 0, 1, (-el / 1000) * g.fs * g.th, 0], tm);
            else show(el);
          }
          break;
        case 'Do': {
          const o = rec(xobjs[nm(a[a.length - 1])]);
          if (o && o.stream && nm(R(o.v.Subtype)) === 'Form') {
            const mtx = (R(o.v.Matrix) || [1, 0, 0, 1, 0, 0]).map(R);
            try { await run(await data(o), R(o.v.Resources) || res, mul(mtx, g.ctm), items, depth + 1); } catch { /* skip a broken form */ }
          }
          break;
        }
        case 'BI': {
          const at = content.indexOf('ID', L.i);
          const endRe = /\sEI(?=\s|$)/g;
          endRe.lastIndex = at + 3;
          const e = at < 0 ? null : endRe.exec(content);
          L.i = e ? e.index + 3 : content.length;
          break;
        }
      }
      stack.length = 0;
    }
  }

  // Drop exact double-drawn text (fake bold) so it isn't read twice.
  for (const p of pages) {
    const keep = [];
    for (const it of p.items) if (!keep.some((k) => k.str === it.str && Math.abs(k.x - it.x) < 1.5 && Math.abs(k.y - it.y) < 1.5)) keep.push(it);
    p.items = keep;
  }
  return { pages, warnings };
}

// Inflate for Node, using the built-in zlib.
export async function nodeInflate(u8) {
  const zlib = await import('node:zlib');
  try { return zlib.inflateSync(u8); } catch { return zlib.inflateSync(u8, { finishFlush: zlib.constants.Z_SYNC_FLUSH }); }
}
