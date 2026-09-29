#!/usr/bin/env node
// Usage: node cli.mjs https://your-app.com [--json] [--md report.md] [--no-supabase]
// Scan YOUR OWN app for the security holes AI-built apps ship with.
import { writeFileSync } from 'node:fs';
import { scan } from './scan.mjs';
import { toText, toMarkdown } from './report.mjs';

const args = process.argv.slice(2);
const url = args.find((a) => !a.startsWith('--'));
if (!url) {
  console.log('Usage: node cli.mjs https://your-app.com [--json] [--md report.md] [--no-supabase]');
  console.log('\nScan your OWN app. VibeGuard only reads (GET) — it never changes your site or data.');
  process.exit(1);
}

const result = await scan(url, { checkSupabaseAccess: !args.includes('--no-supabase') });

if (args.includes('--json')) {
  console.log(JSON.stringify(result, null, 2));
} else {
  console.log(toText(result));
}
const mdFlag = args.indexOf('--md');
if (mdFlag !== -1 && args[mdFlag + 1]) {
  writeFileSync(args[mdFlag + 1], toMarkdown(result));
  console.log(`\nMarkdown report written to ${args[mdFlag + 1]}`);
}

// Exit non-zero if anything critical/high was found, so CI can gate on it.
process.exit(result.counts.critical + result.counts.high > 0 ? 2 : 0);
