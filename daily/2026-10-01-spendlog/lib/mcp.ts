// Spendlog's tools, spoken over MCP. Descriptions say what each tool does and nothing else
// (Claude's directory forbids tool text that instructs the model).
import type { Store } from './store.ts';
import type { User } from './types.ts';
import { scrub } from './scrub.ts';
import { toCents, money, cleanCategory, cleanDay, cleanMonth, summarize, monthLabel } from './money.ts';

export const SERVER = { name: 'spendlog', version: '1.0.0' };
const VERSIONS = ['2025-06-18', '2025-03-26', '2024-11-05'];

export const INSTRUCTIONS = `Spendlog is the user's spending book. It records what they spend and earn, keeps monthly budgets by category, and reports totals. It tracks numbers only; it does not give financial advice.`;

const ro = { readOnlyHint: true, destructiveHint: false, openWorldHint: false };
export const TOOLS = [
  {
    name: 'log_spending',
    title: 'Log spending or income',
    description: 'Records one expense or income in the user\'s spending book: amount, category, an optional short note, and the date. Returns the new entry and the month\'s total for that category.',
    inputSchema: {
      type: 'object', required: ['amount', 'category'],
      properties: {
        amount: { type: 'string', description: 'Amount in dollars, e.g. "42.50"' },
        category: { type: 'string', description: 'Category, e.g. groceries, gas, rent, eating out, paycheck' },
        note: { type: 'string', description: 'Short note such as the store name (optional)' },
        date: { type: 'string', description: 'Date the money moved, YYYY-MM-DD (optional; defaults to today)' },
        kind: { type: 'string', enum: ['expense', 'income'], description: 'expense (default) or income' },
      },
    },
    annotations: { title: 'Log spending or income', readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false },
  },
  {
    name: 'month_summary',
    title: 'Month summary',
    description: 'Returns totals for a month: spending, income, what is left, and each category against its budget.',
    inputSchema: { type: 'object', properties: { month: { type: 'string', description: 'Month as YYYY-MM (optional; defaults to this month)' } } },
    annotations: { title: 'Month summary', ...ro },
  },
  {
    name: 'set_budget',
    title: 'Set a monthly budget',
    description: 'Sets the monthly budget for one category. An amount of 0 removes that budget.',
    inputSchema: {
      type: 'object', required: ['category', 'amount'],
      properties: { category: { type: 'string', description: 'Category, e.g. groceries' }, amount: { type: 'string', description: 'Monthly amount in dollars, or "0" to remove' } },
    },
    annotations: { title: 'Set a monthly budget', readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  },
  {
    name: 'recent_entries',
    title: 'Recent entries',
    description: 'Lists the most recent entries in the spending book with their ids, newest first.',
    inputSchema: { type: 'object', properties: { limit: { type: 'number', description: 'How many (default 10, max 50)' } } },
    annotations: { title: 'Recent entries', ...ro },
  },
  {
    name: 'delete_entry',
    title: 'Delete an entry',
    description: 'Deletes one entry from the spending book by its id.',
    inputSchema: { type: 'object', required: ['id'], properties: { id: { type: 'string', description: 'Entry id from Recent entries' } } },
    annotations: { title: 'Delete an entry', readOnlyHint: false, destructiveHint: true, idempotentHint: true, openWorldHint: false },
  },
];

type Rpc = { jsonrpc: '2.0'; id?: string | number | null; method: string; params?: any };
const ok = (id: any, result: any) => ({ jsonrpc: '2.0', id, result });
const err = (id: any, code: number, message: string) => ({ jsonrpc: '2.0', id, error: { code, message } });
const text = (t: string, isError = false) => ({ content: [{ type: 'text', text: t }], ...(isError ? { isError: true } : {}) });

export async function handleRpc(msg: Rpc, ctx: { user: User }, store: Store): Promise<any | null> {
  const id = msg.id ?? null;
  const isNote = msg.id === undefined;
  try {
    switch (msg.method) {
      case 'initialize': {
        const want = msg.params?.protocolVersion;
        return ok(id, { protocolVersion: VERSIONS.includes(want) ? want : VERSIONS[0], capabilities: { tools: { listChanged: false } }, serverInfo: SERVER, instructions: INSTRUCTIONS });
      }
      case 'ping': return ok(id, {});
      case 'tools/list': return ok(id, { tools: TOOLS });
      case 'tools/call': return ok(id, await callTool(msg.params?.name, msg.params?.arguments || {}, ctx.user, store));
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

export async function callTool(name: string, a: any, user: User, store: Store) {
  if (name === 'log_spending') {
    const cents = toCents(a.amount);
    if (cents === null) return text('Amount must be a positive dollar amount, like 42.50.', true);
    const kind = a.kind === 'income' ? 'income' : 'expense';
    const e = await store.addEntry({ user_id: user.id, kind, cents, category: cleanCategory(a.category), note: scrub(a.note ?? '', 60), day: cleanDay(a.date) });
    const month = e.day.slice(0, 7);
    const s = summarize(await store.entries(user.id, { month }), await store.budgets(user.id), month);
    const line = s.categories.find((c) => c.category === e.category);
    let tail = '';
    if (kind === 'expense' && line) tail = line.budget === null ? ` ${e.category} this month: ${money(line.spent)}.` : ` ${e.category} this month: ${money(line.spent)} of ${money(line.budget)} (${line.left! >= 0 ? money(line.left!) + ' left' : money(-line.left!) + ' over'}).`;
    return text(`Logged ${kind === 'income' ? 'income' : 'spending'} [${e.id}]: ${money(cents)} ${e.category}${e.note ? ' (' + e.note + ')' : ''} on ${e.day}.${tail}`);
  }
  if (name === 'month_summary') {
    const month = cleanMonth(a.month);
    const s = summarize(await store.entries(user.id, { month }), await store.budgets(user.id), month);
    if (!s.count && !s.categories.length) return text(`Nothing logged for ${monthLabel(month)} yet.`);
    const lines = s.categories.map((c) => `- ${c.category}: ${money(c.spent)}` + (c.budget === null ? '' : ` of ${money(c.budget)} (${c.left! >= 0 ? money(c.left!) + ' left' : money(-c.left!) + ' over'})`));
    return text([`${monthLabel(month)}: spent ${money(s.spent)}, income ${money(s.income)}, ${s.net >= 0 ? 'left over ' + money(s.net) : 'short ' + money(-s.net)}. ${s.count} entries.`, ...lines, s.over.length ? `Over budget: ${s.over.join(', ')}.` : ''].filter(Boolean).join('\n'));
  }
  if (name === 'set_budget') {
    const zero = String(a.amount ?? '').replace(/[$\s]/g, '') === '0';
    const cents = zero ? 0 : toCents(a.amount);
    if (cents === null) return text('Amount must be a dollar amount, like 400, or 0 to remove the budget.', true);
    const cat = cleanCategory(a.category);
    await store.setBudget(user.id, cat, cents);
    return text(cents ? `Budget set: ${cat} ${money(cents)} a month.` : `Budget removed for ${cat}.`);
  }
  if (name === 'recent_entries') {
    const limit = Math.max(1, Math.min(50, Number(a.limit) || 10));
    const list = await store.entries(user.id, { limit });
    if (!list.length) return text('No entries yet.');
    return text(list.map((e) => `- [${e.id}] ${e.day} ${e.kind === 'income' ? '+' : '-'}${money(e.cents)} ${e.category}${e.note ? ' (' + e.note + ')' : ''}`).join('\n'));
  }
  if (name === 'delete_entry') {
    if (!a.id) return text('Need the entry id.', true);
    const gone = await store.deleteEntry(user.id, String(a.id));
    return gone ? text(`Deleted ${money(gone.cents)} ${gone.category} on ${gone.day}.`) : text('No entry with that id in this book.', true);
  }
  return text(`Unknown tool ${name}`, true);
}
