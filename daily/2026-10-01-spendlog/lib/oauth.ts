// Sign-in for AI apps (OAuth 2.1 with PKCE), built to Claude's connector rules:
// https://claude.com/docs/connectors/building/authentication
//  - Claude identifies itself with a Client ID Metadata Document (an https client_id) or registers
//    itself (DCR). We support both; public clients only (no client secret).
//  - Hosted Claude apps return to https://claude.ai/api/mcp/auth_callback; Claude Code uses a
//    loopback redirect on any port (localhost or 127.0.0.1), matched without the port.
//  - Access tokens last an hour; refresh tokens rotate on every use.
// Codes and tokens are stored only as SHA-256 hashes.
import { createHash, randomBytes } from 'node:crypto';
import type { Store } from './store.ts';
import type { User } from './types.ts';

export const ACCESS_TTL = 3600;
export const REFRESH_TTL = 60 * 24 * 3600;
const CODE_TTL = 300;
export const SCOPES = ['spending'];

const b64url = (b: Buffer) => b.toString('base64url');
export const hash = (s: string) => b64url(createHash('sha256').update(s).digest());
export const token = (prefix: string) => prefix + b64url(randomBytes(32));

export function pkceOk(verifier: string, challenge: string) {
  return typeof verifier === 'string' && verifier.length >= 43 && verifier.length <= 128 && hash(verifier) === challenge;
}

// Loopback redirects (Claude Code) match without the port; everything else matches exactly.
export function redirectMatches(registered: string[], given: string) {
  let g: URL;
  try { g = new URL(given); } catch { return false; }
  return registered.some((r) => {
    if (r === given) return true;
    try {
      const u = new URL(r);
      const loop = (h: string) => h === 'localhost' || h === '127.0.0.1' || h === '[::1]';
      return u.protocol === 'http:' && g.protocol === 'http:' && loop(u.hostname) && loop(g.hostname) && u.pathname === g.pathname;
    } catch { return false; }
  });
}

export type Client = { client_id: string; client_name: string; redirect_uris: string[]; kind: 'cimd' | 'dcr' };

// Fetch a Client ID Metadata Document (the client_id is an https URL that serves the client's details).
async function fetchCimd(clientId: string, fetcher: typeof fetch): Promise<Client | null> {
  let u: URL;
  try { u = new URL(clientId); } catch { return null; }
  if (u.protocol !== 'https:' || u.pathname === '/') return null;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 4000);
  try {
    const r = await fetcher(clientId, { signal: ctrl.signal, headers: { accept: 'application/json' } });
    if (!r.ok) return null;
    const j: any = await r.json();
    if (j.client_id !== clientId || !Array.isArray(j.redirect_uris)) return null;
    return { client_id: clientId, client_name: String(j.client_name || u.hostname).slice(0, 80), redirect_uris: j.redirect_uris.map(String), kind: 'cimd' };
  } catch { return null; } finally { clearTimeout(t); }
}

export async function getClient(store: Store, clientId: string, fetcher: typeof fetch = fetch): Promise<Client | null> {
  if (!clientId) return null;
  if (clientId.startsWith('https://')) {
    const cached = await store.kvGet<Client>('cimd', hash(clientId));
    if (cached) return cached;
    const c = await fetchCimd(clientId, fetcher);
    if (c) await store.kvPut('cimd', hash(clientId), c, 3600);
    return c;
  }
  return store.kvGet<Client>('client', clientId);
}

export async function registerClient(store: Store, body: any): Promise<Client | { error: string }> {
  const uris = Array.isArray(body?.redirect_uris) ? body.redirect_uris.map(String).slice(0, 10) : [];
  if (!uris.length) return { error: 'redirect_uris is required' };
  for (const u of uris) {
    try { const x = new URL(u); if (!(x.protocol === 'https:' || (x.protocol === 'http:' && /^(localhost|127\.0\.0\.1|\[::1\])$/.test(x.hostname)))) return { error: 'redirect_uris must be https or loopback' }; }
    catch { return { error: 'bad redirect_uri' }; }
  }
  const c: Client = { client_id: token('slc_'), client_name: String(body?.client_name || 'AI app').slice(0, 80), redirect_uris: uris, kind: 'dcr' };
  await store.kvPut('client', c.client_id, c, 365 * 24 * 3600);
  return c;
}

export type AuthReq = { client_id: string; redirect_uri: string; code_challenge: string; state?: string; scope?: string; resource?: string };
export async function checkAuthorize(store: Store, q: Record<string, string | undefined>, fetcher: typeof fetch = fetch):
  Promise<{ ok: true; req: AuthReq; client: Client } | { ok: false; error: string; redirect?: string }> {
  const client = await getClient(store, q.client_id || '', fetcher);
  if (!client) return { ok: false, error: 'Unknown app. Try connecting again from your AI app.' };
  if (!q.redirect_uri || !redirectMatches(client.redirect_uris, q.redirect_uri)) return { ok: false, error: "That app's return address doesn't match what it registered." };
  const back = (error: string) => { const u = new URL(q.redirect_uri!); u.searchParams.set('error', error); if (q.state) u.searchParams.set('state', q.state); return u.toString(); };
  if (q.response_type !== 'code') return { ok: false, error: 'unsupported_response_type', redirect: back('unsupported_response_type') };
  if (!q.code_challenge || q.code_challenge_method !== 'S256') return { ok: false, error: 'PKCE (S256) is required', redirect: back('invalid_request') };
  return { ok: true, client, req: { client_id: client.client_id, redirect_uri: q.redirect_uri, code_challenge: q.code_challenge, state: q.state, scope: q.scope, resource: q.resource } };
}

// The person said yes: use their journal (if they gave its key) or start one, then issue a code.
export async function approve(store: Store, req: AuthReq, opts: { dashKey?: string }) {
  let user: User | null = opts.dashKey ? await store.userByKey(opts.dashKey) : null;
  if (!user) user = await store.createUser();
  const code = token('slcode_');
  await store.kvPut('code', hash(code), { ...req, user_id: user.id }, CODE_TTL);
  const u = new URL(req.redirect_uri);
  u.searchParams.set('code', code);
  if (req.state) u.searchParams.set('state', req.state);
  return { redirect: u.toString(), user };
}

async function issue(store: Store, grant: { user_id: string; client_id: string }) {
  const access = token('slat_'), refresh = token('slrt_');
  await store.kvPut('access', hash(access), grant, ACCESS_TTL);
  await store.kvPut('refresh', hash(refresh), grant, REFRESH_TTL);
  return { access_token: access, token_type: 'Bearer', expires_in: ACCESS_TTL, refresh_token: refresh, scope: SCOPES.join(' ') };
}

const fail = (error: string, description: string, status = 400) => ({ status, body: { error, error_description: description } });

export async function tokenGrant(store: Store, f: Record<string, string | undefined>) {
  if (f.grant_type === 'authorization_code') {
    if (!f.code) return fail('invalid_request', 'code is required');
    const rec = await store.kvGet<AuthReq & { user_id: string }>('code', hash(f.code));
    await store.kvDel('code', hash(f.code)); // one use only
    if (!rec) return fail('invalid_grant', 'code is invalid or expired');
    if (f.client_id && f.client_id !== rec.client_id) return fail('invalid_grant', 'client_id does not match');
    if (f.redirect_uri && f.redirect_uri !== rec.redirect_uri) return fail('invalid_grant', 'redirect_uri does not match');
    if (!pkceOk(f.code_verifier || '', rec.code_challenge)) return fail('invalid_grant', 'PKCE check failed');
    return { status: 200, body: await issue(store, { user_id: rec.user_id, client_id: rec.client_id }) };
  }
  if (f.grant_type === 'refresh_token') {
    if (!f.refresh_token) return fail('invalid_request', 'refresh_token is required');
    const rec = await store.kvGet<{ user_id: string; client_id: string }>('refresh', hash(f.refresh_token));
    if (!rec) return fail('invalid_grant', 'refresh token is invalid or expired');
    if (f.client_id && f.client_id !== rec.client_id) return fail('invalid_grant', 'client_id does not match');
    await store.kvDel('refresh', hash(f.refresh_token)); // rotate
    return { status: 200, body: await issue(store, rec) };
  }
  return fail('unsupported_grant_type', 'use authorization_code or refresh_token');
}

// Bearer token -> whose book.
export async function fromBearer(store: Store, header: string | null) {
  const m = /^Bearer\s+(\S+)$/i.exec(header || '');
  if (!m) return null;
  const rec = await store.kvGet<{ user_id: string }>('access', hash(m[1]));
  if (!rec) return null;
  const user = await store.userById(rec.user_id);
  return user ? { user } : null;
}

export function metadata(origin: string) {
  return {
    resource: {
      resource: `${origin}/api/mcp`,
      authorization_servers: [origin],
      scopes_supported: SCOPES,
      bearer_methods_supported: ['header'],
      resource_name: 'Spendlog',
      resource_documentation: `${origin}/docs`,
    },
    server: {
      issuer: origin,
      authorization_endpoint: `${origin}/oauth/authorize`,
      token_endpoint: `${origin}/api/oauth/token`,
      registration_endpoint: `${origin}/api/oauth/register`,
      response_types_supported: ['code'],
      grant_types_supported: ['authorization_code', 'refresh_token'],
      code_challenge_methods_supported: ['S256'],
      token_endpoint_auth_methods_supported: ['none'],
      client_id_metadata_document_supported: true,
      scopes_supported: SCOPES,
      service_documentation: `${origin}/docs`,
    },
  };
}
