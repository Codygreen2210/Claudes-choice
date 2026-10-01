'use client';
// Browser side of sign-in. With Supabase set up: Google sign-in. Without it (local testing): a dev sign-in.
import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL, anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
let sb: SupabaseClient | null = null;
export const supabase = () => (url && anon ? (sb ??= createClient(url, anon)) : null);
export const devMode = () => !(url && anon);

export const pack = (o: object) => btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
export const unpack = (s: string) => { try { return JSON.parse(decodeURIComponent(escape(atob(s.replace(/-/g, '+').replace(/_/g, '/'))))); } catch { return null; } };

export async function signIn(answers: object) {
  const next = `${location.origin}/results?a=${pack(answers)}`;
  const s = supabase();
  if (!s) { location.href = next + '&dev=1'; return; }
  await s.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: next } });
}

export async function token(): Promise<string | null> {
  const s = supabase();
  if (!s) return new URLSearchParams(location.search).get('dev') ? 'dev:local' : null;
  const { data } = await s.auth.getSession();
  return data.session?.access_token ?? null;
}
