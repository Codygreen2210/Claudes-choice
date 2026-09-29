import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scan, buildFixPrompt } from '../scan.mjs';
import { scanText, decodeJwtRole, findSupabaseAnonKey } from '../patterns.mjs';
import { makeFetch, fakeJwt } from './mock.mjs';

const ANON = fakeJwt('anon');
const SERVICE = fakeJwt('service_role');
const SB = 'https://abcdefghijklmnop.supabase.co';

// ---- pattern-level unit tests ----
test('tells a Stripe secret key from a publishable one', () => {
  const hits = scanText('const k="sk_live_ABCDEFGHIJKLMNOP1234"; const pub="pk_live_SAFE1234567890abc";', 'x');
  assert.equal(hits.length, 1);
  assert.equal(hits[0].id, 'stripe_secret_key');
});

test('reads a JWT role without verifying it', () => {
  assert.equal(decodeJwtRole(ANON), 'anon');
  assert.equal(decodeJwtRole(SERVICE), 'service_role');
});

test('flags service_role JWT but not anon JWT as a secret', () => {
  assert.equal(scanText(`key="${SERVICE}"`, 'x').some((h) => h.id === 'supabase_service_role'), true);
  assert.equal(scanText(`key="${ANON}"`, 'x').some((h) => h.id === 'supabase_service_role'), false);
  assert.equal(findSupabaseAnonKey(`key="${ANON}"`), ANON);
});

// ---- full pipeline against a fake vulnerable app ----
function vulnerableRouter(url) {
  const u = url.toString();
  if (u === 'https://demo.test/') {
    return { status: 200, headers: {}, body:
      `<!doctype html><title>Demo</title>
       <script src="/app.js"></script>
       <script>const stripe="sk_live_ABCDEFGHIJKLMNOP1234";</script>` };
  }
  if (u === 'https://demo.test/app.js') {
    return { status: 200, body:
      `const SUPABASE_URL="${SB}";const SUPABASE_ANON="${ANON}";const ADMIN="${SERVICE}";
       //# sourceMappingURL=app.js.map` };
  }
  if (u === 'https://demo.test/app.js.map') return { status: 200, body: '{"version":3}' };
  if (u === `${SB}/rest/v1/`) return { status: 200, body: { definitions: { users: {}, posts: {} } } };
  if (u.startsWith(`${SB}/rest/v1/users`)) return { status: 200, headers: { 'content-range': '*/42' }, body: [] };
  if (u.startsWith(`${SB}/rest/v1/posts`)) return { status: 401, body: {} }; // RLS on for posts
  return { status: 404, body: '' };
}

test('finds the big leaks in a vibe-coded app', async () => {
  const result = await scan('https://demo.test/', { fetchImpl: makeFetch(vulnerableRouter) });
  const kinds = result.findings.map((f) => f.check);
  assert.ok(kinds.includes('exposed-secret'), 'catches exposed secret keys');
  assert.ok(kinds.includes('supabase-open'), 'catches open Supabase table');
  assert.ok(kinds.includes('missing-header'), 'catches missing security headers');
  assert.ok(kinds.includes('source-map'), 'catches public source map');

  // Stripe secret + service_role = at least two criticals; posts stayed private.
  assert.ok(result.counts.critical >= 2);
  const sb = result.findings.find((f) => f.check === 'supabase-open');
  assert.match(sb.evidence, /users \(42 rows\)/);
  assert.ok(!sb.evidence.includes('posts'), 'a locked-down table is not reported');

  // The paste-back fix prompt lists the fixes.
  const prompt = buildFixPrompt(result);
  assert.match(prompt, /Row Level Security/);
});

// ---- a clean app should come back (nearly) clean ----
function cleanRouter(url) {
  const u = url.toString();
  const secure = {
    'content-security-policy': "default-src 'self'",
    'strict-transport-security': 'max-age=31536000',
    'x-frame-options': 'DENY',
    'x-content-type-options': 'nosniff',
  };
  if (u === 'https://safe.test/') {
    return { status: 200, headers: secure, body:
      `<!doctype html><title>Safe</title><script src="/app.js"></script>` };
  }
  if (u === 'https://safe.test/app.js') {
    return { status: 200, body: `const pub="pk_live_SAFE1234567890abc";const SUPABASE_ANON="${ANON}";const SUPABASE_URL="${SB}";` };
  }
  if (u === `${SB}/rest/v1/`) return { status: 200, body: { definitions: { profiles: {} } } };
  if (u.startsWith(`${SB}/rest/v1/profiles`)) return { status: 401, body: {} }; // RLS on
  return { status: 404, body: '' };
}

test('a clean app reports no critical or high findings', async () => {
  const result = await scan('https://safe.test/', { fetchImpl: makeFetch(cleanRouter) });
  assert.equal(result.counts.critical, 0);
  assert.equal(result.counts.high, 0);
  assert.ok(result.notes.some((n) => /Row Level Security looks on/.test(n)));
});
