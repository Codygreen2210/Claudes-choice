// The one link people add to their AI. It speaks MCP (Model Context Protocol) over plain HTTP,
// which Claude, ChatGPT (developer mode), Cursor, Gemini CLI and others can all connect to.
// The key in the link says whose journal it is; no sign-in, no install.
import type { Store } from './store.ts';
import type { User } from './types.ts';
import { scrub } from './scrub.ts';
import { KINDS, isKind, cleanModel, modelFamily, estimateTokens, estimateDollars, fmtTokens, fmtDollars } from './cost.ts';
import { profileStats } from './game.ts';

export const SERVER = { name: 'misslog', version: '1.0.0' };
const VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05'];

export const INSTRUCTIONS = `This is the user's mistake journal (Misslog). Use it so you stop repeating mistakes.
1. At the start of a task, call my_misses and keep those checks in mind.
2. The moment the user corrects you, pushes back ("that's wrong", "too much", "no"), or you catch your own error, call log_miss:
   what you were trying to do, a short summary of what they asked, the mistake, the fix if you know it, and your best estimate of tokens spent on the wrong path. Pass your own model name.
3. When you find the fix later, call add_fix with the mistake's id.
4. After a research session (web searches, lookups), call log_search with the topic and how many searches it took.
Never put passwords, keys, emails, or private details in these fields; summarize instead. Log honestly; the point is to get better, not to look good.`;

const kindList = Object.keys(KINDS);
export const TOOLS = [
  {
    name: 'my_misses',
    description: "Read the user's recent mistakes and their fixes. Call this at the start of a task so you don't repeat them.",
    inputSchema: { type: 'object', properties: { limit: { type: 'number', description: 'How many (default 15, max 50)' } } },
    annotations: { readOnlyHint: true },
  },
  {
    name: 'log_miss',
    description: 'Log a mistake you made, right when the user corrects you or you catch it yourself.',
    inputSchema: {
      type: 'object',
      required: ['model', 'kind', 'trying_to', 'ask', 'mistake'],
      properties: {
        model: { type: 'string', description: 'Your model name, e.g. claude-sonnet-5-5, gpt-5, gemini-2.5-pro, grok-4' },
        kind: { type: 'string', enum: kindList, description: kindList.map((k) => `${k}: ${KINDS[k as keyof typeof KINDS].label}`).join('; ') },
        trying_to: { type: 'string', description: 'What you were trying to do' },
        ask: { type: 'string', description: "Short summary of what the user asked (no private details)" },
        mistake: { type: 'string', description: 'What went wrong' },
        fix: { type: 'string', description: 'What fixed it, and the check that stops it next time (if known)' },
        tokens_wasted: { type: 'number', description: 'Your estimate of tokens spent on the wrong path' },
      },
    },
  },
  {
    name: 'add_fix',
    description: 'Add the fix to a mistake logged earlier.',
    inputSchema: { type: 'object', required: ['id', 'fix'], properties: { id: { type: 'string' }, fix: { type: 'string' } } },
  },
  {
    name: 'log_search',
    description: 'Log a research session: the topic and how many searches or lookups it took.',
    inputSchema: {
      type: 'object', required: ['model', 'topic'],
      properties: { model: { type: 'string' }, topic: { type: 'string' }, searches: { type: 'number', description: 'Number of searches/lookups' } },
    },
  },
  {
    name: 'my_stats',
    description: "The user's totals: mistakes, fixes, estimated tokens and dollars burned, level, streak, badges.",
    inputSchema: { type: 'object', properties: {} },
    annotations: { readOnlyHint: true },
  },
];

type Rpc = { jsonrpc: '2.0'; id?: string | number | null; method: string; params?: any };
const ok = (id: any, result: any) => ({ jsonrpc: '2.0', id, result });
const err = (id: any, code: number, message: string) => ({ jsonrpc: '2.0', id, error: { code, message } });
const text = (t: string, isError = false) => ({ content: [{ type: 'text', text: t }], ...(isError ? { isError: true } : {}) });

export async function handleRpc(msg: Rpc, user: User, store: Store, client = ''): Promise<any | null> {
  const id = msg.id ?? null;
  const isNote = msg.id === undefined;
  try {
    switch (msg.method) {
      case 'initialize': {
        const want = msg.params?.protocolVersion;
        return ok(id, {
          protocolVersion: VERSIONS.includes(want) ? want : VERSIONS[0],
          capabilities: { tools: { listChanged: false } },
          serverInfo: SERVER,
          instructions: INSTRUCTIONS,
        });
      }
      case 'ping': return ok(id, {});
      case 'tools/list': return ok(id, { tools: TOOLS });
      case 'tools/call': return ok(id, await callTool(msg.params?.name, msg.params?.arguments || {}, user, store, client));
      case 'resources/list': return ok(id, { resources: [] });
      case 'prompts/list': return ok(id, { prompts: [] });
      default:
        if (isNote || msg.method?.startsWith('notifications/')) return null;
        return err(id, -32601, `Unknown method ${msg.method}`);
    }
  } catch (e: any) {
    return isNote ? null : err(id, -32603, e?.message || 'Server error');
  }
}

export async function callTool(name: string, a: any, user: User, store: Store, client = '') {
  if (name === 'my_misses') {
    const limit = Math.max(1, Math.min(50, Number(a.limit) || 15));
    const misses = (await store.events(user.id, 300)).filter((e) => e.type === 'miss').slice(0, limit);
    if (!misses.length) return text('No mistakes logged yet. When the user corrects you, call log_miss.');
    return text('Recent mistakes to avoid (newest first):\n' + misses.map((e) =>
      `- [${e.id}] ${KINDS[e.kind as keyof typeof KINDS]?.label || e.kind} (${e.family}): ${e.mistake}` + (e.fix ? ` FIX: ${e.fix}` : ' (no fix logged yet)')).join('\n'));
  }
  if (name === 'log_miss') {
    for (const f of ['model', 'trying_to', 'ask', 'mistake']) if (!String(a[f] ?? '').trim()) return text(`Missing "${f}".`, true);
    const kind = isKind(a.kind) ? a.kind : 'other';
    const model = cleanModel(a.model);
    const tokens = estimateTokens(kind, a.tokens_wasted);
    const ev = await store.addEvent({
      user_id: user.id, type: 'miss', model, family: modelFamily(model), client: scrub(client, 40), kind,
      trying_to: scrub(a.trying_to), ask: scrub(a.ask), mistake: scrub(a.mistake, 400), fix: a.fix ? scrub(a.fix, 400) : undefined,
      tokens, dollars: estimateDollars(model, tokens),
    });
    return text(`Logged [${ev.id}]. Estimated cost: ${fmtTokens(tokens)} tokens (~${fmtDollars(ev.dollars)}).` + (ev.fix ? ' Fix recorded.' : ' Call add_fix when you find the fix.'));
  }
  if (name === 'add_fix') {
    if (!String(a.fix ?? '').trim() || !a.id) return text('Need "id" and "fix".', true);
    const done = await store.setFix(user.id, String(a.id), scrub(a.fix, 400));
    return text(done ? 'Fix saved.' : 'No mistake with that id in this journal.', !done);
  }
  if (name === 'log_search') {
    if (!String(a.topic ?? '').trim()) return text('Missing "topic".', true);
    const model = cleanModel(a.model);
    await store.addEvent({
      user_id: user.id, type: 'search', model, family: modelFamily(model), client: scrub(client, 40),
      topic: scrub(a.topic, 120), searches: Math.max(1, Math.min(200, Math.round(Number(a.searches) || 1))), tokens: 0, dollars: 0,
    });
    return text('Research session logged.');
  }
  if (name === 'my_stats') {
    const s = profileStats(await store.events(user.id, 5000));
    return text([
      `Level ${s.level.level} (${s.xp} XP), streak ${s.streak} day(s).`,
      `${s.misses} mistakes, ${s.fixed} with fixes, ${s.searches} searches logged.`,
      `Estimated burn: ${fmtTokens(s.tokens)} tokens (~${fmtDollars(s.dollars)}).`,
      s.badges.length ? 'Badges: ' + s.badges.map((b) => b.name).join(', ') : 'No badges yet.',
    ].join('\n'));
  }
  return text(`Unknown tool ${name}`, true);
}
