import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { scrub } from '../lib/scrub.ts';
import { modelFamily, estimateTokens, estimateDollars, MAX_TOKENS } from '../lib/cost.ts';
import { level, streak, board, profileStats } from '../lib/game.ts';
import { FileStore } from '../lib/store.ts';
import { handleRpc, TOOLS } from '../lib/mcp.ts';
import type { Ev } from '../lib/types.ts';

test('scrub removes private stuff', () => {
  const s = scrub('email cody@example.com key sk-ant-api03-abcdefghijklmnopqrstuv password=hunter22 call 225-555-0142 card 4242 4242 4242 4242 at /home/cody/app https://x.com/a?token=abc postgres://u:p@db/x');
  for (const bad of ['cody@example.com', 'sk-ant', 'hunter22', '555-0142', '4242 4242', '/home/cody', 'token=abc', 'u:p@db']) assert.ok(!s.includes(bad), bad + ' leaked: ' + s);
  assert.ok(scrub('x'.repeat(1000)).length <= 280);
  assert.equal(scrub('fixed the RLS on the posts table'), 'fixed the RLS on the posts table');
});

test('model families', () => {
  assert.equal(modelFamily('claude-opus-5-5'), 'Claude');
  assert.equal(modelFamily('GPT-5'), 'ChatGPT');
  assert.equal(modelFamily('gemini-2.5-pro'), 'Gemini');
  assert.equal(modelFamily('grok-4'), 'Grok');
  assert.equal(modelFamily('something'), 'Other');
});

test('token and dollar estimates are capped and sane', () => {
  assert.equal(estimateTokens('guess'), 3000);
  assert.equal(estimateTokens('guess', 1e9), MAX_TOKENS);
  assert.equal(estimateTokens('guess', -5), 3000);
  assert.equal(estimateDollars('claude-opus-5-5', 1_000_000), 30);
  assert.ok(estimateDollars('gemini-2.5-flash', 10_000) < estimateDollars('gpt-5', 10_000));
});

const ev = (p: Partial<Ev>): Ev => ({ id: Math.random() + '', user_id: 'u1', type: 'miss', model: 'x', family: 'Claude', client: '', tokens: 1000, dollars: 0.01, created_at: new Date().toISOString(), ...p });

test('levels, streaks, board ranking', () => {
  assert.deepEqual(level(0), { level: 1, into: 0, need: 100 });
  assert.equal(level(250).level, 3);
  const d = (n: number) => new Date(Date.now() - n * 864e5).toISOString();
  assert.equal(streak([ev({ created_at: d(0) }), ev({ created_at: d(1) }), ev({ created_at: d(2) }), ev({ created_at: d(4) })]), 3);
  assert.equal(streak([ev({ created_at: d(1) }), ev({ created_at: d(2) })]), 2, 'not logging today yet keeps the streak');
  const rows = board([
    ev({ family: 'Claude', fix: 'y' }), ev({ family: 'Claude' }),
    ev({ family: 'ChatGPT', fix: 'y', user_id: 'u2' }),
    ev({ family: 'ChatGPT', type: 'search', searches: 5, tokens: 0, user_id: 'u3' }),
  ]);
  assert.equal(rows[0].family, 'ChatGPT');
  assert.equal(rows[0].people, 2);
  assert.equal(rows[0].searches, 5);
  const s = profileStats([ev({ fix: 'y', tokens: 60000 })]);
  assert.ok(s.badges.some((b) => b.id === 'bigone'));
});

test('a full MCP session, the way an AI app runs it', async () => {
  process.env.MISSLOG_DATA = mkdtempSync(join(tmpdir(), 'ml-'));
  const store = new FileStore(process.env.MISSLOG_DATA);
  const u = await store.createUser();
  assert.match(u.key, /^ml_/);
  const rpc = (method: string, params?: any, id: any = 1) => handleRpc({ jsonrpc: '2.0', id, method, params }, u, store, 'claude-ai');
  const init = await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'test', version: '1' } });
  assert.equal(init.result.protocolVersion, '2025-06-18');
  assert.ok(init.result.instructions.includes('log_miss'));
  assert.equal(await handleRpc({ jsonrpc: '2.0', method: 'notifications/initialized' } as any, u, store), null);
  const list = await rpc('tools/list');
  assert.deepEqual(list.result.tools.map((t: any) => t.name), TOOLS.map((t) => t.name));
  const empty = await rpc('tools/call', { name: 'my_misses', arguments: {} });
  assert.match(empty.result.content[0].text, /No mistakes/);
  const logged = await rpc('tools/call', { name: 'log_miss', arguments: { model: 'claude-opus-5-5', kind: 'unverified', trying_to: 'fix audio peaks', ask: 'finish LaunchReel', mistake: 'said fixed before re-checking; key sk-ant-api03-zzzzzzzzzzzzzzzzzzzz', tokens_wasted: 12000 } });
  const id = logged.result.content[0].text.match(/\[([^\]]+)\]/)[1];
  assert.match(logged.result.content[0].text, /12\.0K tokens/);
  const bad = await rpc('tools/call', { name: 'log_miss', arguments: { model: 'x' } });
  assert.equal(bad.result.isError, true);
  await rpc('tools/call', { name: 'add_fix', arguments: { id, fix: 'measure again before saying done' } });
  const other = await store.createUser();
  const stolen = await handleRpc({ jsonrpc: '2.0', id: 9, method: 'tools/call', params: { name: 'add_fix', arguments: { id, fix: 'x' } } }, other, store);
  assert.equal(stolen.result.isError, true, "one journal can't touch another's mistakes");
  await rpc('tools/call', { name: 'log_search', arguments: { model: 'gpt-5', topic: 'passport photo market', searches: 4 } });
  const back = await rpc('tools/call', { name: 'my_misses', arguments: {} });
  assert.match(back.result.content[0].text, /FIX: measure again/);
  assert.ok(!back.result.content[0].text.includes('sk-ant'), 'key scrubbed');
  const stats = await rpc('tools/call', { name: 'my_stats', arguments: {} });
  assert.match(stats.result.content[0].text, /1 mistakes, 1 with fixes, 4 searches/);
  const rows = await store.board();
  assert.deepEqual(rows.map((r) => r.family).sort(), ['ChatGPT', 'Claude']);
  const unknown = await rpc('nope/method');
  assert.equal(unknown.error.code, -32601);
});
