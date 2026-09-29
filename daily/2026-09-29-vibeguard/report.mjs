// Turn a scan result into something a non-coder can read: a plain-English
// report, and the paste-back fix prompt.
import { buildFixPrompt } from './scan.mjs';

const MARK = { critical: '[CRITICAL]', high: '[HIGH]', medium: '[MEDIUM]', low: '[LOW]' };

export function toText(result) {
  const c = result.counts;
  const lines = [];
  lines.push(`VibeGuard report for ${result.url}`);
  lines.push(`${result.filesScanned} file(s) scanned in ${(result.ms / 1000).toFixed(1)}s`);
  lines.push('');
  if (!result.findings.length) {
    lines.push('No problems found in the checks VibeGuard runs. Nice.');
  } else {
    lines.push(`Found: ${c.critical} critical, ${c.high} high, ${c.medium} medium, ${c.low} low`);
    lines.push('');
    for (const f of result.findings) {
      lines.push(`${MARK[f.severity]} ${f.title}`);
      lines.push(`  What it means: ${f.detail}`);
      lines.push(`  Evidence: ${f.evidence}`);
      lines.push(`  How to fix: ${f.fix}`);
      lines.push('');
    }
  }
  for (const n of result.notes) lines.push(`Note: ${n}`);
  return lines.join('\n');
}

export function toMarkdown(result) {
  const c = result.counts;
  const lines = [`# VibeGuard report`, '', `**Site:** ${result.url}`, `**Scanned:** ${result.scannedAt}`, ''];
  if (!result.findings.length) {
    lines.push('No problems found in the checks VibeGuard runs.');
  } else {
    lines.push(`**Found:** ${c.critical} critical · ${c.high} high · ${c.medium} medium · ${c.low} low`, '');
    for (const f of result.findings) {
      lines.push(`### ${MARK[f.severity]} ${f.title}`);
      lines.push(`- **What it means:** ${f.detail}`);
      lines.push(`- **Evidence:** ${f.evidence}`);
      lines.push(`- **How to fix:** ${f.fix}`, '');
    }
    const prompt = buildFixPrompt(result);
    if (prompt) {
      lines.push('## Copy this to your AI builder to fix it', '', '```', prompt, '```');
    }
  }
  for (const n of result.notes) lines.push(`> ${n}`);
  return lines.join('\n');
}
