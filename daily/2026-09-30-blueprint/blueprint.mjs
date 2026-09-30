#!/usr/bin/env node
// Usage: node blueprint.mjs path/to/your-app [--write]
// Prints the owner's manual. With --write, saves BLUEPRINT.md, AI-CONTEXT.md and
// .env.example into the app folder (it never overwrites an existing .env.example).
import { writeFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { analyze } from './analyze.mjs';
import { ownersManual, aiContext, envExample } from './render.mjs';

const args = process.argv.slice(2);
const dir = resolve(args.find((a) => !a.startsWith('--')) || '.');
if (!existsSync(dir)) { console.error(`Can't find ${dir}`); process.exit(1); }

const a = analyze(dir);
const manual = ownersManual(a);
console.log(manual);
console.log('\n---\n');
console.log(aiContext(a));

if (args.includes('--write')) {
  writeFileSync(join(dir, 'BLUEPRINT.md'), manual + '\n');
  writeFileSync(join(dir, 'AI-CONTEXT.md'), aiContext(a) + '\n');
  const envPath = join(dir, '.env.example');
  const wroteEnv = !existsSync(envPath);
  if (wroteEnv) writeFileSync(envPath, envExample(a));
  console.log(`\nSaved BLUEPRINT.md and AI-CONTEXT.md${wroteEnv ? ' and .env.example' : ' (kept your existing .env.example)'} in ${dir}`);
  console.log('Paste AI-CONTEXT.md into your CLAUDE.md (or .cursorrules) so your AI builder starts each session knowing the app.');
}
