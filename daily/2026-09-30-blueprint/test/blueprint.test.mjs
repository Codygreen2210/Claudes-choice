import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { execFileSync } from 'node:child_process';
import { analyze } from '../analyze.mjs';
import { ownersManual, aiContext, envExample } from '../render.mjs';

// Build a small, realistic AI-made Next.js + Supabase + Stripe app on disk.
function makeApp() {
  const root = mkdtempSync(join(tmpdir(), 'bp-'));
  const put = (p, s) => { mkdirSync(dirname(join(root, p)), { recursive: true }); writeFileSync(join(root, p), s); };
  put('package.json', JSON.stringify({ name: 'recipe-box', scripts: { dev: 'next dev', build: 'next build' },
    dependencies: { next: '15.0.0', react: '19.0.0', '@supabase/supabase-js': '2.0.0', stripe: '16.0.0', resend: '4.0.0' } }));
  put('app/page.tsx', 'export default function Home(){return null}');
  put('app/(marketing)/pricing/page.tsx', 'export default function P(){return null}');
  put('app/recipes/[id]/page.tsx', `import { sb } from '@/lib/sb'; const r = await sb.from('recipes').select('*');`);
  put('app/dashboard/page.tsx', `const { data } = await sb.from("profiles").select(); await sb.storage.from('photos').upload(f); await sb.rpc('like_recipe');`);
  put('app/api/checkout/route.ts', `const stripe = new Stripe(process.env.STRIPE_SECRET_KEY); await fetch('https://api.resend.com/emails');`);
  put('app/api/webhook/route.ts', `const s = process.env.STRIPE_WEBHOOK_SECRET; sb.from('recipes').update(x)`);
  put('lib/sb.ts', `createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY)`);
  put('lib/bad.ts', `const k = process.env.NEXT_PUBLIC_OPENAI_SECRET;`);
  put('node_modules/junk/index.js', `process.env.SHOULD_NOT_APPEAR; sb.from('nope')`);
  put('.github/workflows/nightly.yml', 'on: schedule');
  return root;
}

test('finds framework, services, pages and API routes', () => {
  const a = analyze(makeApp());
  assert.equal(a.framework, 'Next.js');
  assert.deepEqual(a.services, ['Resend (email)', 'Stripe (payments)', 'Supabase (database + logins)']);
  assert.deepEqual(a.pages, ['/', '/dashboard', '/pricing', '/recipes/[id]'], 'route groups like (marketing) are dropped');
  assert.deepEqual(a.apis, ['/api/checkout', '/api/webhook']);
  assert.deepEqual(a.deploy, ['Vercel']);
  assert.deepEqual(a.workflows, ['nightly.yml']);
});

test('finds tables, buckets and functions, and skips node_modules', () => {
  const a = analyze(makeApp());
  assert.deepEqual(a.tables.map((t) => t.table), ['profiles', 'recipes']);
  assert.equal(a.tables.find((t) => t.table === 'recipes').files.length, 2);
  assert.deepEqual(a.buckets, ['photos'], 'storage.from is a bucket, not a table');
  assert.deepEqual(a.rpcs, ['like_recipe']);
  assert.ok(!a.env.some((e) => e.name === 'SHOULD_NOT_APPEAR'));
  assert.deepEqual(a.hosts, ['api.resend.com']);
});

test('sorts settings into secret and public, and warns about a secret made public', () => {
  const a = analyze(makeApp());
  const pub = a.env.filter((e) => e.public).map((e) => e.name);
  assert.deepEqual(pub, ['NEXT_PUBLIC_OPENAI_SECRET', 'NEXT_PUBLIC_SUPABASE_ANON_KEY', 'NEXT_PUBLIC_SUPABASE_URL']);
  assert.equal(a.warnings.length, 1);
  assert.match(a.warnings[0], /NEXT_PUBLIC_OPENAI_SECRET/);
});

test('owner\'s manual, AI context and .env.example read right', () => {
  const a = analyze(makeApp());
  const m = ownersManual(a);
  assert.match(m, /## Fix these first/);
  assert.match(m, /Database tables \(2\)/);
  assert.match(m, /`npm run build` — next build/);
  const c = aiContext(a);
  assert.ok(c.split('\n').length < 20, 'AI context stays short');
  assert.match(c, /DB tables: profiles, recipes/);
  const env = envExample(a);
  assert.match(env, /# Server-only \(secret\)\nSTRIPE_SECRET_KEY=\nSTRIPE_WEBHOOK_SECRET=/);
  assert.ok(!/=\S/.test(env), 'no values are ever written');
});

test('CLI --write saves the files and never overwrites an existing .env.example', () => {
  const root = makeApp();
  writeFileSync(join(root, '.env.example'), 'MINE=keep\n');
  execFileSync(process.execPath, [new URL('../blueprint.mjs', import.meta.url).pathname, root, '--write']);
  assert.ok(existsSync(join(root, 'BLUEPRINT.md')));
  assert.ok(existsSync(join(root, 'AI-CONTEXT.md')));
  assert.equal(readFileSync(join(root, '.env.example'), 'utf8'), 'MINE=keep\n');
});
