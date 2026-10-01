// Storage. Supabase in production (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY), a JSON file locally/tests.
import { randomBytes, randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import type { Budget, Entry, User } from './types.ts';

export interface Store {
  createUser(): Promise<User>;
  userByKey(key: string): Promise<User | null>;
  userById(id: string): Promise<User | null>;
  deleteUser(id: string): Promise<void>;
  addEntry(e: Omit<Entry, 'id' | 'created_at'>): Promise<Entry>;
  deleteEntry(userId: string, id: string): Promise<Entry | null>;
  entries(userId: string, opts?: { month?: string; limit?: number }): Promise<Entry[]>;
  budgets(userId: string): Promise<Budget[]>;
  setBudget(userId: string, category: string, cents: number): Promise<void>; // 0 removes it
  kvPut(kind: string, id: string, data: unknown, ttlSeconds: number): Promise<void>;
  kvGet<T = any>(kind: string, id: string): Promise<T | null>;
  kvDel(kind: string, id: string): Promise<void>;
}

const ADJ = ['steady', 'thrifty', 'honest', 'patient', 'careful', 'humble', 'lucky', 'calm', 'sturdy', 'bright'];
const NOUN = ['pelican', 'wrench', 'bayou', 'ledger', 'heron', 'anvil', 'lantern', 'cypress', 'piggy', 'rivet'];
export const newHandle = () => { const b = randomBytes(3); return `${ADJ[b[0] % ADJ.length]}-${NOUN[b[1] % NOUN.length]}-${10 + (b[2] % 90)}`; };
export const newKey = () => 'sl_' + randomBytes(18).toString('base64url');
const now = () => new Date().toISOString();
const sortEntries = (a: Entry, b: Entry) => b.day.localeCompare(a.day) || b.created_at.localeCompare(a.created_at);

type KV = { kind: string; id: string; data: unknown; expires: number };
type DB = { users: User[]; entries: Entry[]; budgets: Budget[]; kv: KV[] };

export class FileStore implements Store {
  file: string;
  constructor(dir = process.env.SPENDLOG_DATA || join(process.cwd(), '.data')) { mkdirSync(dir, { recursive: true }); this.file = join(dir, 'db.json'); }
  private read(): DB { const d = existsSync(this.file) ? JSON.parse(readFileSync(this.file, 'utf8')) : {}; return { users: [], entries: [], budgets: [], kv: [], ...d }; }
  private write(db: DB) { writeFileSync(this.file, JSON.stringify(db)); }
  async createUser() { const db = this.read(); const u = { id: randomUUID(), key: newKey(), handle: newHandle(), created_at: now() }; db.users.push(u); this.write(db); return u; }
  async userByKey(key: string) { return this.read().users.find((u) => u.key === key) || null; }
  async userById(id: string) { return this.read().users.find((u) => u.id === id) || null; }
  async deleteUser(id: string) { const db = this.read(); db.users = db.users.filter((u) => u.id !== id); db.entries = db.entries.filter((e) => e.user_id !== id); db.budgets = db.budgets.filter((b) => b.user_id !== id); this.write(db); }
  async addEntry(e: Omit<Entry, 'id' | 'created_at'>) { const db = this.read(); const x = { ...e, id: randomUUID(), created_at: now() }; db.entries.push(x); this.write(db); return x; }
  async deleteEntry(userId: string, id: string) { const db = this.read(); const x = db.entries.find((e) => e.id === id && e.user_id === userId) || null; if (x) { db.entries = db.entries.filter((e) => e !== x); this.write(db); } return x; }
  async entries(userId: string, o: { month?: string; limit?: number } = {}) { return this.read().entries.filter((e) => e.user_id === userId && (!o.month || e.day.startsWith(o.month))).sort(sortEntries).slice(0, o.limit ?? 5000); }
  async budgets(userId: string) { return this.read().budgets.filter((b) => b.user_id === userId); }
  async setBudget(userId: string, category: string, cents: number) { const db = this.read(); db.budgets = db.budgets.filter((b) => !(b.user_id === userId && b.category === category)); if (cents > 0) db.budgets.push({ user_id: userId, category, cents }); this.write(db); }
  async kvPut(kind: string, id: string, data: unknown, ttl: number) { const db = this.read(); const t = Date.now(); db.kv = db.kv.filter((r) => r.expires > t && !(r.kind === kind && r.id === id)); db.kv.push({ kind, id, data, expires: t + ttl * 1000 }); this.write(db); }
  async kvGet(kind: string, id: string) { const r = this.read().kv.find((x) => x.kind === kind && x.id === id); return r && r.expires > Date.now() ? (r.data as any) : null; }
  async kvDel(kind: string, id: string) { const db = this.read(); db.kv = db.kv.filter((r) => !(r.kind === kind && r.id === id)); this.write(db); }
}

export class SupabaseStore implements Store {
  sb: any;
  constructor(sb: any) { this.sb = sb; }
  private one = async (q: any) => { const { data, error } = await q; if (error) throw new Error(error.message); return data; };
  async createUser() {
    for (let i = 0; i < 5; i++) {
      const { data, error } = await this.sb.from('sl_users').insert({ key: newKey(), handle: newHandle() }).select().single();
      if (!error) return data as User;
      if (!/duplicate|unique/i.test(error.message)) throw new Error(error.message);
    }
    throw new Error('Could not make a name, try again.');
  }
  async userByKey(key: string) { return this.one(this.sb.from('sl_users').select('*').eq('key', key).maybeSingle()); }
  async userById(id: string) { return this.one(this.sb.from('sl_users').select('*').eq('id', id).maybeSingle()); }
  async deleteUser(id: string) { await this.one(this.sb.from('sl_users').delete().eq('id', id)); } // entries + budgets cascade
  async addEntry(e: Omit<Entry, 'id' | 'created_at'>) { return this.one(this.sb.from('sl_entries').insert(e).select().single()); }
  async deleteEntry(userId: string, id: string) { const d = await this.one(this.sb.from('sl_entries').delete().eq('id', id).eq('user_id', userId).select()); return (d && d[0]) || null; }
  async entries(userId: string, o: { month?: string; limit?: number } = {}) {
    let q = this.sb.from('sl_entries').select('*').eq('user_id', userId);
    if (o.month) q = q.like('day', o.month + '-%');
    return this.one(q.order('day', { ascending: false }).order('created_at', { ascending: false }).limit(o.limit ?? 5000));
  }
  async budgets(userId: string) { return this.one(this.sb.from('sl_budgets').select('*').eq('user_id', userId)); }
  async setBudget(userId: string, category: string, cents: number) {
    if (cents > 0) await this.one(this.sb.from('sl_budgets').upsert({ user_id: userId, category, cents }));
    else await this.one(this.sb.from('sl_budgets').delete().eq('user_id', userId).eq('category', category));
  }
  async kvPut(kind: string, id: string, data: unknown, ttl: number) { await this.one(this.sb.from('sl_oauth').upsert({ kind, id, data, expires_at: new Date(Date.now() + ttl * 1000).toISOString() })); }
  async kvGet(kind: string, id: string) { const r = await this.one(this.sb.from('sl_oauth').select('data, expires_at').eq('kind', kind).eq('id', id).maybeSingle()); return r && new Date(r.expires_at).getTime() > Date.now() ? r.data : null; }
  async kvDel(kind: string, id: string) { await this.one(this.sb.from('sl_oauth').delete().eq('kind', kind).eq('id', id)); }
}

let cached: Store | null = null;
export async function getStore(): Promise<Store> {
  if (cached) return cached;
  const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (url && key) { const { createClient } = await import('@supabase/supabase-js'); cached = new SupabaseStore(createClient(url, key, { auth: { persistSession: false } })); }
  else cached = new FileStore();
  return cached;
}
