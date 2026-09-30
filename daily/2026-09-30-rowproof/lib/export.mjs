// CSV, Excel (.xlsx) and OFX output. The .xlsx is written by hand (a zip of XML files)
// so there's nothing to install.

const LABEL = { verified: 'Proven by running balance', 'totals-match': 'Proven by statement totals', 'balance-typo': 'Row OK; bank printed a wrong balance', mismatch: 'CHECK: does not add up', unchecked: 'Not checked (no balances printed)' };
export const checkLabel = (c) => LABEL[c] || c;

// Text starting with = + - @ could run as a formula in Excel, so it gets a leading apostrophe.
const csvCell = (v) => { let s = v == null ? '' : String(v); if (/^[=+\-@\t\r]/.test(s) && isNaN(Number(s))) s = "'" + s; return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
export function toCSV(rows) {
  const head = ['Date', 'Description', 'Amount', 'Money out', 'Money in', 'Balance', 'Page', 'Check'];
  const lines = [head.join(',')];
  for (const r of rows) {
    const a = r.amount;
    lines.push([r.date, r.description, a?.toFixed(2), a < 0 ? (-a).toFixed(2) : '', a > 0 ? a.toFixed(2) : '', r.balance?.toFixed(2), r.page, checkLabel(r.check)].map(csvCell).join(','));
  }
  return lines.join('\r\n') + '\r\n';
}

// OFX 1.02 (the plain-text kind QuickBooks Desktop, Xero and most money apps import).
export function toOFX(rows, { closing = null } = {}) {
  const d = (s) => s.replace(/-/g, '');
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').slice(0, 64);
  const dated = rows.filter((r) => /^\d{4}-/.test(r.date) && r.amount != null);
  const start = dated[0]?.date ?? '1970-01-01', end = dated.at(-1)?.date ?? start;
  const tx = dated.map((r, i) => `<STMTTRN><TRNTYPE>${r.amount < 0 ? 'DEBIT' : 'CREDIT'}<DTPOSTED>${d(r.date)}<TRNAMT>${r.amount.toFixed(2)}<FITID>${d(r.date)}${String(i + 1).padStart(4, '0')}<NAME>${esc(r.description)}</STMTTRN>`).join('\n');
  return `OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO</STATUS><DTSERVER>${d(end)}<LANGUAGE>ENG</SONRS></SIGNONMSGSRSV1>
<BANKMSGSRSV1><STMTTRNRS><TRNUID>1<STATUS><CODE>0<SEVERITY>INFO</STATUS><STMTRS><CURDEF>USD<BANKACCTFROM><BANKID>000000000<ACCTID>ROWPROOF<ACCTTYPE>CHECKING</BANKACCTFROM>
<BANKTRANLIST><DTSTART>${d(start)}<DTEND>${d(end)}
${tx}
</BANKTRANLIST>${closing != null ? `<LEDGERBAL><BALAMT>${closing.toFixed(2)}<DTASOF>${d(end)}</LEDGERBAL>` : ''}</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>\n`;
}

// ---- xlsx ----
const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(b) { let c = 0xffffffff; for (let i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }
function zip(files) { // files: [{name, data: Uint8Array}], stored (no compression)
  const enc = new TextEncoder();
  const parts = [], central = [];
  let off = 0;
  for (const f of files) {
    const name = enc.encode(f.name), crc = crc32(f.data), n = f.data.length;
    const h = new DataView(new ArrayBuffer(30));
    h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(8, 0, true);
    h.setUint16(10, 0, true); h.setUint16(12, 0x21, true); // 1980-01-01
    h.setUint32(14, crc, true); h.setUint32(18, n, true); h.setUint32(22, n, true); h.setUint16(26, name.length, true);
    parts.push(new Uint8Array(h.buffer), name, f.data);
    const c = new DataView(new ArrayBuffer(46));
    c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true);
    c.setUint16(12, 0, true); c.setUint16(14, 0x21, true);
    c.setUint32(16, crc, true); c.setUint32(20, n, true); c.setUint32(24, n, true); c.setUint16(28, name.length, true); c.setUint32(42, off, true);
    central.push(new Uint8Array(c.buffer), name);
    off += 30 + name.length + n;
  }
  const csize = central.reduce((s, p) => s + p.length, 0);
  const e = new DataView(new ArrayBuffer(22));
  e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true); e.setUint32(12, csize, true); e.setUint32(16, off, true);
  const all = [...parts, ...central, new Uint8Array(e.buffer)];
  const out = new Uint8Array(all.reduce((s, p) => s + p.length, 0));
  let p = 0; for (const a of all) { out.set(a, p); p += a.length; }
  return out;
}
const x = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '');
const serial = (iso) => { const [y, m, d] = iso.split('-').map(Number); return (Date.UTC(y, m - 1, d) - Date.UTC(1899, 11, 30)) / 86400000; };
const colL = (i) => String.fromCharCode(65 + i);

export function toXLSX(rows) {
  const head = ['Date', 'Description', 'Amount', 'Money out', 'Money in', 'Balance', 'Page', 'Check'];
  const cell = (ci, ri, v, style) => {
    const ref = colL(ci) + ri;
    if (v == null || v === '') return '';
    if (typeof v === 'number') return `<c r="${ref}"${style ? ` s="${style}"` : ''}><v>${v}</v></c>`;
    return `<c r="${ref}" t="inlineStr"${style ? ` s="${style}"` : ''}><is><t>${x(v)}</t></is></c>`;
  };
  const sheetRows = [`<row r="1">${head.map((h, i) => cell(i, 1, h, 3)).join('')}</row>`];
  rows.forEach((r, k) => {
    const ri = k + 2, a = r.amount;
    const date = /^\d{4}-\d{2}-\d{2}$/.test(r.date) ? serial(r.date) : r.date;
    const vals = [[date, typeof date === 'number' ? 1 : 0], [r.description], [a, 2], [a < 0 ? -a : null, 2], [a > 0 ? a : null, 2], [r.balance, 2], [r.page], [checkLabel(r.check), r.check === 'mismatch' ? 4 : 0]];
    sheetRows.push(`<row r="${ri}">${vals.map(([v, s], i) => cell(i, ri, v, s)).join('')}</row>`);
  });
  const sheet = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="1" width="12" customWidth="1"/><col min="2" max="2" width="44" customWidth="1"/><col min="3" max="6" width="13" customWidth="1"/><col min="7" max="7" width="6" customWidth="1"/><col min="8" max="8" width="34" customWidth="1"/></cols><sheetData>${sheetRows.join('')}</sheetData></worksheet>`;
  const styles = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0.00"/></numFmts><fonts count="3"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFB3261E"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="5"><xf/><xf numFmtId="14" applyNumberFormat="1"/><xf numFmtId="164" applyNumberFormat="1"/><xf fontId="1" applyFont="1"/><xf fontId="2" applyFont="1"/></cellXfs></styleSheet>`;
  const enc = new TextEncoder();
  const f = (name, s) => ({ name, data: enc.encode(s) });
  return zip([
    f('[Content_Types].xml', `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>`),
    f('_rels/.rels', `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`),
    f('xl/workbook.xml', `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Transactions" sheetId="1" r:id="rId1"/></sheets></workbook>`),
    f('xl/_rels/workbook.xml.rels', `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`),
    f('xl/worksheets/sheet1.xml', sheet),
    f('xl/styles.xml', styles),
  ]);
}
