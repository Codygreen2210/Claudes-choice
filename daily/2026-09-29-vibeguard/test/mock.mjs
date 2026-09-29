// A tiny fake `fetch` so the scanner can be tested with no network.
// You give it a router function (url, opts) -> { status, body, headers }.
export function makeFetch(router) {
  return async function mockFetch(url, opts = {}) {
    const r = router(url, opts) || { status: 404, body: '' };
    const headers = new Headers(r.headers || {});
    const body = typeof r.body === 'string' ? r.body : JSON.stringify(r.body ?? {});
    return {
      ok: r.status >= 200 && r.status < 300,
      status: r.status,
      headers,
      async text() { return body; },
      async json() { return typeof r.body === 'string' ? JSON.parse(body) : (r.body ?? {}); },
    };
  };
}

// Build a JWT-shaped string whose payload carries the given role.
export function fakeJwt(role) {
  const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
  const header = b64({ alg: 'HS256', typ: 'JWT' });
  const payload = b64({ role, iss: 'supabase', ref: 'abcdefghijklmnop' });
  const sig = 'x'.repeat(24);
  return `${header}.${payload}.${sig}`;
}
