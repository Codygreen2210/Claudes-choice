// Answers, one per signed-in person (a new answer replaces their old one).
// Supabase in production; a JSON file locally and in tests.
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import type { Input, Community } from './wages.ts';
import { MIN_GROUP } from './wages.ts';

export type Answer = Input & { user_id: string; updated_at: string };

export interface Store {
  save(userId: string, i: Input): Promise<void>;
  community(occ: string, area: string): Promise<Community>;
  remove(userId: string): Promise<void>;
}

const median = (xs: number[]) => { const s = xs.slice().sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const group = (hourlies: number[]): Community => hourlies.length >= MIN_GROUP ? { count: hourlies.length, median: Math.round(median(hourlies) * 100) / 100 } : { count: hourlies.length, median: null };

export class FileStore implements Store {
  file: string;
  constructor(dir = process.env.WM_DATA || join(process.cwd(), '.data')) { mkdirSync(dir, { recursive: true }); this.file = join(dir, 'answers.json'); }
  private read(): Answer[] { return existsSync(this.file) ? JSON.parse(readFileSync(this.file, 'utf8')) : []; }
  async save(userId: string, i: Input) { const all = this.read().filter((a) => a.user_id !== userId); all.push({ ...i, user_id: userId, updated_at: new Date().toISOString() }); writeFileSync(this.file, JSON.stringify(all)); }
  async community(occ: string, area: string) { return group(this.read().filter((a) => a.occ === occ && a.area === area).map((a) => a.hourly)); }
  async remove(userId: string) { writeFileSync(this.file, JSON.stringify(this.read().filter((a) => a.user_id !== userId))); }
}

export class SupabaseStore implements Store {
  sb: any;
  constructor(sb: any) { this.sb = sb; }
  async save(userId: string, i: Input) {
    const { error } = await this.sb.from('wm_answers').upsert({ user_id: userId, occ: i.occ, area: i.area, hourly: i.hourly, hours: i.hours, ot_hours: i.otHours, years: i.years ?? null, updated_at: new Date().toISOString() });
    if (error) throw new Error(error.message);
  }
  async community(occ: string, area: string) {
    const { data, error } = await this.sb.from('wm_answers').select('hourly').eq('occ', occ).eq('area', area).limit(5000);
    if (error) throw new Error(error.message);
    return group((data || []).map((r: any) => Number(r.hourly)));
  }
  async remove(userId: string) { const { error } = await this.sb.from('wm_answers').delete().eq('user_id', userId); if (error) throw new Error(error.message); }
}

let cached: { store: Store; sb: any } | null = null;
export async function backend() {
  if (cached) return cached;
  const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (url && key) {
    const { createClient } = await import('@supabase/supabase-js');
    const sb = createClient(url, key, { auth: { persistSession: false } });
    cached = { store: new SupabaseStore(sb), sb };
  } else cached = { store: new FileStore(), sb: null };
  return cached;
}

// Who is calling: checks the Supabase sign-in token. Locally (no Supabase), "dev:<name>" tokens are accepted.
export async function userFrom(req: Request): Promise<string | null> {
  const t = /^Bearer\s+(\S+)$/i.exec(req.headers.get('authorization') || '')?.[1];
  if (!t) return null;
  const { sb } = await backend();
  if (!sb) return /^dev:[a-z0-9-]{1,40}$/.test(t) ? t : null;
  const { data, error } = await sb.auth.getUser(t);
  return error || !data?.user ? null : data.user.id;
}
