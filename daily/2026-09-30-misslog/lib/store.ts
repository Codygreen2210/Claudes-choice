// Storage. Uses Supabase when SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set (production),
// otherwise a JSON file in .data/ (local runs and tests). Same interface either way.
import { randomBytes, randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import type { Ev, User } from './types.ts';
import { board, type BoardRow } from './game.ts';

export interface Store {
  createUser(): Promise<User>;
  userByKey(key: string): Promise<User | null>;
  userByHandle(handle: string): Promise<User | null>;
  updateUser(id: string, patch: Partial<Pick<User, 'public' | 'share_data'>>): Promise<void>;
  addEvent(e: Omit<Ev, 'id' | 'created_at'>): Promise<Ev>;
  setFix(userId: string, eventId: string, fix: string): Promise<boolean>;
  events(userId: string, limit?: number): Promise<Ev[]>;
  board(): Promise<BoardRow[]>;
  recentPublic(limit?: number): Promise<(Ev & { handle: string })[]>;
}

const ADJ = ['quiet', 'steady', 'rusty', 'bright', 'patient', 'stubborn', 'honest', 'swift', 'humble', 'lucky', 'bold', 'calm'];
const NOUN = ['heron', 'wrench', 'bayou', 'anvil', 'otter', 'lantern', 'gator', 'hammer', 'pelican', 'compass', 'ember', 'rivet'];
export function newHandle() {
  const b = randomBytes(3);
  return `${ADJ[b[0] % ADJ.length]}-${NOUN[b[1] % NOUN.length]}-${10 + (b[2] % 90)}`;
}
export const newKey = () => 'ml_' + randomBytes(18).toString('base64url');
const now = () => new Date().toISOString();

// ---------------------------------------------------------------- file store
type DB = { users: User[]; events: Ev[] };
export class FileStore implements Store {
  file: string;
  constructor(dir = process.env.MISSLOG_DATA || join(process.cwd(), '.data')) { mkdirSync(dir, { recursive: true }); this.file = join(dir, 'db.json'); }
  private read(): DB { return existsSync(this.file) ? JSON.parse(readFileSync(this.file, 'utf8')) : { users: [], events: [] }; }
  private write(db: DB) { writeFileSync(this.file, JSON.stringify(db)); }
  async createUser() {
    const db = this.read();
    let handle = newHandle();
    while (db.users.some((u) => u.handle === handle)) handle = newHandle();
    const u: User = { id: randomUUID(), key: newKey(), handle, public: false, share_data: false, created_at: now() };
    db.users.push(u); this.write(db); return u;
  }
  async userByKey(key: string) { return this.read().users.find((u) => u.key === key) || null; }
  async userByHandle(h: string) { return this.read().users.find((u) => u.handle === h) || null; }
  async updateUser(id: string, patch: Partial<User>) { const db = this.read(); const u = db.users.find((x) => x.id === id); if (u) Object.assign(u, patch); this.write(db); }
  async addEvent(e: Omit<Ev, 'id' | 'created_at'>) { const db = this.read(); const ev = { ...e, id: randomUUID(), created_at: now() } as Ev; db.events.push(ev); this.write(db); return ev; }
  async setFix(userId: string, id: string, fix: string) { const db = this.read(); const e = db.events.find((x) => x.id === id && x.user_id === userId && x.type === 'miss'); if (!e) return false; e.fix = fix; this.write(db); return true; }
  async events(userId: string, limit = 500) { return this.read().events.filter((e) => e.user_id === userId).sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, limit); }
  async board() { return board(this.read().events); }
  async recentPublic(limit = 12) {
    const db = this.read(); const pub = new Map(db.users.filter((u) => u.public).map((u) => [u.id, u.handle]));
    return db.events.filter((e) => e.type === 'miss' && pub.has(e.user_id)).sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, limit).map((e) => ({ ...e, handle: pub.get(e.user_id)! }));
  }
}

// ---------------------------------------------------------------- supabase store
export class SupabaseStore implements Store {
  sb: any;
  constructor(sb: any) { this.sb = sb; }
  private one = async (q: any) => { const { data, error } = await q; if (error) throw new Error(error.message); return data; };
  async createUser() {
    for (let i = 0; i < 5; i++) {
      const u = { key: newKey(), handle: newHandle(), public: false, share_data: false };
      const { data, error } = await this.sb.from('ml_users').insert(u).select().single();
      if (!error) return data as User;
      if (!/duplicate|unique/i.test(error.message)) throw new Error(error.message);
    }
    throw new Error('Could not make a handle, try again.');
  }
  async userByKey(key: string) { return (await this.one(this.sb.from('ml_users').select('*').eq('key', key).maybeSingle())) as User | null; }
  async userByHandle(h: string) { return (await this.one(this.sb.from('ml_users').select('*').eq('handle', h).maybeSingle())) as User | null; }
  async updateUser(id: string, patch: Partial<User>) { await this.one(this.sb.from('ml_users').update(patch).eq('id', id)); }
  async addEvent(e: Omit<Ev, 'id' | 'created_at'>) { return (await this.one(this.sb.from('ml_events').insert(e).select().single())) as Ev; }
  async setFix(userId: string, id: string, fix: string) {
    const d = await this.one(this.sb.from('ml_events').update({ fix }).eq('id', id).eq('user_id', userId).eq('type', 'miss').select('id'));
    return (d || []).length > 0;
  }
  async events(userId: string, limit = 500) { return (await this.one(this.sb.from('ml_events').select('*').eq('user_id', userId).order('created_at', { ascending: false }).limit(limit))) as Ev[]; }
  async board() { return (await this.one(this.sb.from('ml_board').select('*'))) as BoardRow[]; }
  async recentPublic(limit = 12) {
    const rows = await this.one(this.sb.from('ml_public_feed').select('*').limit(limit));
    return rows as (Ev & { handle: string })[];
  }
}

let cached: Store | null = null;
export async function getStore(): Promise<Store> {
  if (cached) return cached;
  const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (url && key) {
    const { createClient } = await import('@supabase/supabase-js');
    cached = new SupabaseStore(createClient(url, key, { auth: { persistSession: false } }));
  } else cached = new FileStore();
  return cached;
}
