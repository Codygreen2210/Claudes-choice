import { extractText } from './pdf.mjs';
import { readStatement } from './statement.mjs';
export { toCSV, toXLSX, toOFX, checkLabel } from './export.mjs';

// PDF bytes in; transactions, a proof summary and plain warnings out.
export async function convert(bytes, { inflate }) {
  const { pages, warnings } = await extractText(bytes, { inflate });
  const r = readStatement(pages);
  // If any page couldn't be read, never call the result proven.
  if (warnings.some((w) => /^Page \d+:/.test(w)) && r.summary.verdict !== 'no-text') r.summary.verdict = 'check';
  return { ...r, warnings: [...warnings, ...r.warnings], pages: pages.length };
}
