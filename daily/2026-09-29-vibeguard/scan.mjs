// VibeGuard core — a self-audit for the security holes AI-built ("vibe-coded")
// apps ship with. You point it at YOUR OWN app's URL. It only does what a normal
// visitor's browser already does: GET the page, read the public JavaScript it
// loads, read response headers, and — if the app itself hands the browser a
// Supabase anon key — ask Supabase which tables that key can read. It never
// writes, never deletes, never downloads your rows (row counts only), and never
// guesses passwords or hidden URLs. Read-only, on your own site.

import { scanText, findSupabaseUrl, findSupabaseAnonKey } from './patterns.mjs';

const UA = 'VibeGuard/0.1 self-audit (+https://github.com/Codygreen2210/Claudes-choice)';

async function get(url, opts = {}) {
  const res = await fetch(url, { redirect: 'follow', headers: { 'user-agent': UA, ...(opts.headers || {}) }, ...opts });
  return res;
}

// Collect the page HTML plus every same-origin script it loads. Cross-origin
// scripts (a CDN, an analytics vendor) are skipped: not yours to audit, and the
// leak we care about is what your own build shipped.
async function collectSources(pageUrl, fetchImpl = get) {
  const origin = new URL(pageUrl).origin;
  const sources = [];
  const res = await fetchImpl(pageUrl);
  const html = await res.text();
  const headers = res.headers;
  const status = res.status;
  sources.push({ source: pageUrl, text: html, kind: 'html' });

  const scriptUrls = [...html.matchAll(/<script[^>]+src=["']([^"']+)["']/gi)]
    .map((m) => new URL(m[1], pageUrl).href)
    .filter((u) => new URL(u).origin === origin);

  const unique = [...new Set(scriptUrls)].slice(0, 25); // sane cap
  for (const u of unique) {
    try {
      const r = await fetchImpl(u);
      if (r.ok) sources.push({ source: u, text: await r.text(), kind: 'js', url: u });
    } catch { /* a script that won't load isn't a secret leak; skip */ }
  }
  return { sources, headers, status, html };
}

// Ask a Supabase project, using the app's OWN public anon key, which tables that
// key can read. PostgREST exposes an OpenAPI doc at the REST root listing the
// tables reachable with the given key. For each, we do a count-only HEAD-style
// GET (limit=0) so we learn "readable + how many rows" without pulling any row.
async function checkSupabase(supabaseUrl, anonKey, fetchImpl = get) {
  const out = { url: supabaseUrl, readableTables: [], checked: false, error: null };
  try {
    const rootRes = await fetchImpl(`${supabaseUrl}/rest/v1/`, { headers: { apikey: anonKey, authorization: `Bearer ${anonKey}` } });
    if (!rootRes.ok) { out.error = `REST root returned HTTP ${rootRes.status}`; return out; }
    const spec = await rootRes.json();
    const tables = Object.keys(spec.definitions || spec.components?.schemas || {});
    out.checked = true;
    for (const table of tables.slice(0, 40)) {
      try {
        const r = await fetchImpl(`${supabaseUrl}/rest/v1/${encodeURIComponent(table)}?select=*&limit=0`, {
          headers: { apikey: anonKey, authorization: `Bearer ${anonKey}`, prefer: 'count=exact', range: '0-0' },
        });
        // 200/206 means the anon key can read this table (RLS is open).
        if (r.status === 200 || r.status === 206) {
          const cr = r.headers.get('content-range'); // e.g. "*/1234"
          const count = cr && cr.includes('/') ? cr.split('/').pop() : '?';
          out.readableTables.push({ table, rows: count });
        }
      } catch { /* one table failing is fine */ }
    }
  } catch (e) {
    out.error = e.message;
  }
  return out;
}

const SECURITY_HEADERS = [
  ['content-security-policy', 'high', 'No Content-Security-Policy. This header is the main defense against a stranger injecting scripts into your page (XSS). Vibe-coded apps almost never set it.'],
  ['strict-transport-security', 'medium', 'No HSTS header. It forces browsers to always use HTTPS so a network attacker cannot downgrade the connection.'],
  ['x-frame-options', 'low', 'No X-Frame-Options (or frame-ancestors). Without it, another site can load yours in a hidden frame and trick users into clicking (clickjacking).'],
  ['x-content-type-options', 'low', 'No X-Content-Type-Options: nosniff. It stops the browser from guessing file types, which can turn an upload into a script.'],
];

export async function scan(pageUrl, { fetchImpl = get, checkSupabaseAccess = true } = {}) {
  const started = Date.now();
  const findings = [];
  const notes = [];
  const { sources, headers, status } = await collectSources(pageUrl, fetchImpl);

  if (status >= 400) notes.push(`The page returned HTTP ${status}. Results may be incomplete.`);

  // 1. Secrets in the shipped HTML + JS.
  let secretsFound = 0;
  for (const s of sources) {
    for (const hit of scanText(s.text, shortSource(s.source, pageUrl))) {
      secretsFound++;
      findings.push({
        check: 'exposed-secret',
        severity: hit.severity,
        title: `${hit.label} exposed in ${hit.source}`,
        detail: hit.why,
        evidence: `Found: ${hit.sample}`,
        fix: `Remove the ${hit.label.toLowerCase()} from anything the browser downloads. Move that call to a server route or edge function, put the key in a server-only environment variable, and rotate the exposed key so the old one stops working.`,
      });
    }
  }

  // 2. Supabase anon key + open RLS.
  const allText = sources.map((s) => s.text).join('\n');
  const supabaseUrl = findSupabaseUrl(allText);
  const anonKey = findSupabaseAnonKey(allText);
  if (supabaseUrl && anonKey && checkSupabaseAccess) {
    const sb = await checkSupabase(supabaseUrl, anonKey, fetchImpl);
    if (sb.readableTables.length) {
      const list = sb.readableTables.map((t) => `${t.table} (${t.rows} rows)`).join(', ');
      findings.push({
        check: 'supabase-open',
        severity: 'critical',
        title: `Supabase: ${sb.readableTables.length} table(s) readable by anyone`,
        detail: 'Your app ships a Supabase anon key (normal), but these tables have no Row Level Security, so anyone with that key — which is everyone who visits — can read them. This is the most common way AI-built apps leak user data.',
        evidence: `Readable without logging in: ${list}`,
        fix: 'In Supabase, turn on Row Level Security for each of these tables and add a policy that only lets a user read their own rows (for example: auth.uid() = user_id). Any table that is truly meant to be public can stay open on purpose.',
      });
    } else if (sb.checked) {
      notes.push('Supabase anon key found, and no tables were readable without logging in. Good — Row Level Security looks on.');
    } else if (sb.error) {
      notes.push(`Supabase anon key found; could not complete the read check (${sb.error}).`);
    }
  } else if (supabaseUrl && anonKey) {
    notes.push('Supabase anon key found. Read check was skipped.');
  }

  // 3. Missing security headers.
  for (const [name, severity, why] of SECURITY_HEADERS) {
    const present = headers.get(name) || (name === 'x-frame-options' && /frame-ancestors/i.test(headers.get('content-security-policy') || ''));
    if (!present) {
      findings.push({
        check: 'missing-header',
        severity,
        title: `Missing security header: ${name}`,
        detail: why,
        evidence: `The response from ${new URL(pageUrl).host} did not include ${name}.`,
        fix: headerFix(name),
      });
    }
  }

  // 4. Source map served in production (leaks your original source).
  for (const s of sources.filter((x) => x.kind === 'js')) {
    const mapMatch = /\/\/[#@]\s*sourceMappingURL=([^\s]+)/.exec(s.text);
    if (mapMatch && !mapMatch[1].startsWith('data:')) {
      try {
        const mapUrl = new URL(mapMatch[1], s.url).href;
        const r = await fetchImpl(mapUrl);
        if (r.ok) {
          findings.push({
            check: 'source-map',
            severity: 'low',
            title: 'Source map is public',
            detail: 'Your original, un-minified source code can be downloaded by anyone through the .map file. It makes it easy to read your logic and spot other mistakes.',
            evidence: shortSource(mapUrl, pageUrl),
            fix: 'Turn off source maps in your production build (for Vite: build.sourcemap = false; for Next.js: productionBrowserSourceMaps = false), or stop the .map files from being served.',
          });
        }
      } catch { /* map not reachable; nothing to report */ }
    }
  }

  findings.sort((a, b) => SEV_ORDER[a.severity] - SEV_ORDER[b.severity]);
  return {
    url: pageUrl,
    scannedAt: new Date().toISOString(),
    ms: Date.now() - started,
    counts: countBy(findings),
    findings,
    notes,
    filesScanned: sources.length,
  };
}

const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

function countBy(findings) {
  const c = { critical: 0, high: 0, medium: 0, low: 0 };
  for (const f of findings) c[f.severity]++;
  return c;
}

function shortSource(url, pageUrl) {
  try {
    if (url === pageUrl) return 'the page HTML';
    const u = new URL(url);
    return u.pathname.split('/').pop() || u.host;
  } catch { return url; }
}

function headerFix(name) {
  const fixes = {
    'content-security-policy': "Add a Content-Security-Policy header. A safe starting point: default-src 'self'. Set it in your host's config (Vercel: headers in vercel.json; Netlify: _headers) and tighten it until the app still works.",
    'strict-transport-security': 'Add: Strict-Transport-Security: max-age=31536000; includeSubDomains. Most hosts (Vercel, Netlify) can set this in one line of config.',
    'x-frame-options': "Add X-Frame-Options: DENY, or a frame-ancestors 'none' rule in your Content-Security-Policy.",
    'x-content-type-options': 'Add: X-Content-Type-Options: nosniff.',
  };
  return fixes[name] || 'Add this header in your host configuration.';
}

// A single block the owner can paste into their AI builder to fix everything found.
export function buildFixPrompt(result) {
  if (!result.findings.length) return null;
  const lines = [
    'Please fix these security problems in my app. Do not change anything else.',
    '',
  ];
  result.findings.forEach((f, i) => {
    lines.push(`${i + 1}. ${f.title}`);
    lines.push(`   Fix: ${f.fix}`);
  });
  return lines.join('\n');
}
