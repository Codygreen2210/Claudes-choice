// Reads a PDF the way a test needs to: page boxes, link boxes and where each
// link goes, and the text (the page streams are compressed, so inflate them).
import { inflateSync } from 'node:zlib';

export function readPdf(buf) {
  const raw = Buffer.from(buf).toString('latin1');
  const kids = [...(/\/Kids \[([^\]]*)\]/.exec(raw)?.[1] ?? '').matchAll(/(\d+) 0 R/g)].map((m) => Number(m[1]));
  const pageOf = new Map(kids.map((id, i) => [id, i + 1]));
  const pages = [];
  for (const m of raw.matchAll(/(\d+) 0 obj\n<<\/Type \/Page\n([\s\S]*?)endobj/g)) {
    const body = m[2];
    const box = /\/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]/.exec(body);
    const links = [...body.matchAll(/\/Subtype \/Link \/Rect \[([\d.\- ]+)\][^>]*?\/Dest \[(\d+) 0 R/g)].map((l) => {
      const [x1, y1, x2, y2] = l[1].trim().split(/\s+/).map(Number);
      return { x1, y1, x2, y2, page: pageOf.get(Number(l[2])) };
    });
    pages.push({ number: pageOf.get(Number(m[1])), w: Number(box[1]), h: Number(box[2]), links });
  }
  pages.sort((a, b) => a.number - b.number);
  // jsPDF always writes a bare \n around stream data. Allowing \r here once dropped the last byte of a stream that happened to end in 0x0D.
  let text = '';
  for (const m of raw.matchAll(/stream\n([\s\S]*?)\nendstream/g)) {
    try { text += inflateSync(Buffer.from(m[1], 'latin1')).toString('latin1') + '\n'; } catch { /* not a compressed stream */ }
  }
  return {
    raw,
    pages,
    pageCount: [...raw.matchAll(/\/Type\s*\/Page(?![\w])/g)].length,
    linkCount: [...raw.matchAll(/\/Subtype\s*\/Link/g)].length,
    text,
    count: (s) => text.split(`(${s})`).length - 1,
  };
}
