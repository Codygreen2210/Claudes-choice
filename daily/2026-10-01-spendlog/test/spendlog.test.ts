import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { toCents, money, cleanCategory, cleanDay, summarize, toCsv, today } from '../lib/money.ts';
import { FileStore } from '../lib/store.ts';
import { handleRpc, TOOLS } from '../lib/mcp.ts';
import { checkAuthorize, approve, tokenGrant, fromBearer, metadata } from '../lib/oauth.ts';

test('money parsing is exact', () => {
  assert.equal(toCents('42.18'), 4218);
  assert.equal(toCents('$1,250'), 125000);
  assert.equal(toCents(19.9), 1990);
  assert.equal(toCents('0.1'), 10);
  for (const bad of ['', '-5', '0', 'abc', '1.234', '99999999999']) assert.equal(toCents(bad), null, bad);
  assert.equal(money(125000), '$1,250.00');
  assert.equal(money(-550), '-$5.50');
  // 0.1 + 0.2 style drift can't happen in cents
  assert.equal([toCents('0.10')!, toCents('0.20')!].reduce((a, b) => a + b), 30);
});

test('categories and dates are cleaned', () => {
  assert.equal(cleanCategory('  Eating OUT!! '), 'eating out');
  assert.equal(cleanCategory(''), 'other');
  assert.equal(cleanDay('2026-09-28', new Date('2026-10-01T12:00:00Z')), '2026-09-28');
  assert.equal(cleanDay('yesterday', new Date('2026-10-01T12:00:00Z')), '2026-10-01');
  assert.equal(cleanDay('1999-01-01', new Date('2026-10-01T12:00:00Z')), '2026-10-01', 'far-off dates fall back to today');
});

test('month summary against budgets', () => {
  const e = (cents: number, category: string, kind: any = 'expense', day = '2026-10-03') => ({ id: Math.random() + '', user_id: 'u', kind, cents, category, note: '', day, created_at: '' });
  const s = summarize([e(4218, 'groceries'), e(30000, 'groceries'), e(125000, 'paycheck', 'income'), e(900, 'gas', 'expense', '2026-09-30')],
    [{ user_id: 'u', category: 'groceries', cents: 30000 }, { user_id: 'u', category: 'eating out', cents: 15000 }], '2026-10');
  assert.equal(s.spent, 34218); assert.equal(s.income, 125000); assert.equal(s.net, 90782); assert.equal(s.count, 3);
  assert.deepEqual(s.over, ['groceries']);
  assert.equal(s.categories.find((c) => c.category === 'eating out')!.left, 15000, 'budgeted with no spending still shows');
  assert.ok(!s.categories.some((c) => c.category === 'gas'), 'other months are left out');
});

test('CSV is safe to open in Excel', () => {
  const csv = toCsv([{ id: '1', user_id: 'u', kind: 'expense', cents: 500, category: 'other', note: '=HYPERLINK("x")', day: '2026-10-01', created_at: '' }]);
  assert.match(csv, /'=HYPERLINK/);
  assert.match(csv, /2026-10-01,expense,-5\.00,other,/);
});

test('every tool: titled, hinted, and describes without instructing', () => {
  for (const t of TOOLS as any[]) {
    assert.ok(t.title && t.annotations.title, t.name);
    assert.equal(typeof t.annotations.readOnlyHint, 'boolean'); assert.equal(typeof t.annotations.destructiveHint, 'boolean');
    const all = [t.description, ...Object.values(t.inputSchema.properties || {}).map((p: any) => p.description)].join(' ');
    assert.doesNotMatch(all, /\b(call this|you should|you must|always|never call|ignore|before you)\b/i, t.name);
  }
  assert.equal((TOOLS as any[]).find((t) => t.name === 'delete_entry').annotations.destructiveHint, true);
});

test('all five tools, the way Claude calls them', async () => {
  const store = new FileStore(mkdtempSync(join(tmpdir(), 'sl-')));
  const u = await store.createUser(), other = await store.createUser();
  const call = async (name: string, args: any, who = u) => (await handleRpc({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }, { user: who }, store)).result;
  assert.match((await call('month_summary', {})).content[0].text, /Nothing logged/);
  assert.match((await call('set_budget', { category: 'Groceries', amount: '$400' })).content[0].text, /groceries \$400\.00 a month/);
  const r1 = await call('log_spending', { amount: '42.18', category: 'groceries', note: 'Walmart, call me 225-555-0142' });
  assert.match(r1.content[0].text, /\$42\.18 groceries \(Walmart, call me \[phone\]\)/);
  assert.match(r1.content[0].text, /\$42\.18 of \$400\.00 \(\$357\.82 left\)/);
  await call('log_spending', { amount: '1,250', category: 'paycheck', kind: 'income' });
  await call('log_spending', { amount: '380', category: 'groceries' });
  const sum = (await call('month_summary', {})).content[0].text;
  assert.match(sum, /spent \$422\.18, income \$1,250\.00, left over \$827\.82/);
  assert.match(sum, /Over budget: groceries/);
  assert.equal((await call('log_spending', { amount: '-5', category: 'x' })).isError, true);
  const list = (await call('recent_entries', { limit: 5 })).content[0].text;
  const id = /\[([^\]]+)\] \S+ -\$380\.00/.exec(list)![1];
  assert.equal((await call('delete_entry', { id }, other)).isError, true, "can't delete someone else's entry");
  assert.match((await call('delete_entry', { id })).content[0].text, /Deleted \$380\.00 groceries/);
  assert.match((await call('month_summary', {})).content[0].text, /spent \$42\.18/);
  assert.match((await call('set_budget', { category: 'groceries', amount: '0' })).content[0].text, /removed/);
  assert.match((await call('month_summary', {}, other)).content[0].text, /Nothing logged/, 'books are separate');
  assert.equal((await store.entries(u.id))[0].day, today());
});

test("Claude's sign-in: CIMD + PKCE + tokens + tools + reuse a book", async () => {
  const store = new FileStore(mkdtempSync(join(tmpdir(), 'sl2-')));
  const CIMD = 'https://claude.ai/oauth/mcp-oauth-client-metadata', CB = 'https://claude.ai/api/mcp/auth_callback';
  const fakeFetch = (async (url: string) => url === CIMD ? new Response(JSON.stringify({ client_id: CIMD, client_name: 'Claude', redirect_uris: [CB] })) : new Response('', { status: 404 })) as typeof fetch;
  const v = 'v'.repeat(50), ch = createHash('sha256').update(v).digest('base64url');
  const chk = await checkAuthorize(store, { response_type: 'code', client_id: CIMD, redirect_uri: CB, code_challenge: ch, code_challenge_method: 'S256', state: 's' }, fakeFetch);
  assert.ok(chk.ok); if (!chk.ok) return;
  const first = await approve(store, chk.req, {});
  const again = await approve(store, chk.req, { dashKey: first.user.key });
  assert.equal(again.user.id, first.user.id, 'same book reused');
  const code = new URL(again.redirect).searchParams.get('code')!;
  const t = (await tokenGrant(store, { grant_type: 'authorization_code', code, client_id: CIMD, redirect_uri: CB, code_verifier: v })).body as any;
  assert.match(t.access_token, /^slat_/);
  const ctx = await fromBearer(store, 'Bearer ' + t.access_token);
  assert.equal(ctx!.user.id, first.user.id);
  const m = metadata('https://x.example');
  assert.equal(m.resource.resource_name, 'Spendlog'); assert.equal(m.server.client_id_metadata_document_supported, true);
  await store.deleteUser(first.user.id);
  assert.equal(await fromBearer(store, 'Bearer ' + t.access_token), null, 'deleted book = no access');
});
