// Secret patterns worth catching in a shipped client bundle.
// The important split: some keys are MEANT to be public (publishable / anon),
// and some are a real leak (secret / service_role). We flag only the leaks,
// and we say clearly when a "key" we found is the safe kind, so the report
// doesn't cry wolf.

export const SECRET_RULES = [
  {
    id: 'stripe_secret_key',
    label: 'Stripe secret key',
    severity: 'critical',
    // sk_live_ / sk_test_ / rk_live_ (restricted). Publishable keys are pk_ and are fine.
    re: /\b(sk|rk)_(live|test)_[0-9a-zA-Z]{16,}\b/g,
    why: 'A Stripe secret key can charge cards, issue refunds and read every customer on your account. It must live only on a server, never in code the browser downloads.',
  },
  {
    id: 'openai_key',
    label: 'OpenAI API key',
    severity: 'critical',
    re: /\bsk-(proj-)?[0-9A-Za-z_-]{20,}\b/g,
    why: 'Anyone who copies this key can run AI calls on your bill. Keys have been drained within hours of being exposed in a public bundle.',
  },
  {
    id: 'aws_access_key',
    label: 'AWS access key id',
    severity: 'critical',
    re: /\bAKIA[0-9A-Z]{16}\b/g,
    why: 'An AWS key can reach your servers, storage and databases. Paired with its secret it is full account access.',
  },
  {
    id: 'google_api_key',
    label: 'Google API key',
    severity: 'high',
    re: /\bAIza[0-9A-Za-z_-]{35}\b/g,
    why: 'A Google API key with no referrer restriction can be used by anyone and billed to you. Restrict it to your domain, or move it server-side.',
  },
  {
    id: 'private_key_block',
    label: 'Private key',
    severity: 'critical',
    re: /-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----/g,
    why: 'A private key in the browser bundle is a private key handed to the public. Rotate it now.',
  },
  {
    id: 'supabase_service_role',
    label: 'Supabase service_role key',
    severity: 'critical',
    // A JWT whose payload contains "service_role". We match the JWT then confirm below.
    re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g,
    confirm: (match) => decodeJwtRole(match) === 'service_role',
    why: 'The Supabase service_role key ignores every security rule (RLS) and can read and write all of your data. It must never reach the browser.',
  },
  {
    id: 'generic_secret_assignment',
    label: 'Hard-coded secret',
    severity: 'medium',
    // things like  apiSecret: "abcd1234efgh...."  / PASSWORD='...'
    re: /\b(secret|api[_-]?secret|client[_-]?secret|password|passwd|private[_-]?token)\b\s*[:=]\s*['"][^'"\s]{8,}['"]/gi,
    why: 'A value literally named a secret is sitting in code the browser can read. Confirm it is not real; if it is, move it to a server and rotate it.',
  },
];

// Keys that look scary but are meant to be public. We note them as "OK" so the
// report can reassure instead of alarm.
export const PUBLIC_KEY_RULES = [
  { id: 'stripe_publishable', label: 'Stripe publishable key', re: /\bpk_(live|test)_[0-9a-zA-Z]{16,}\b/g },
  { id: 'supabase_anon', label: 'Supabase anon key', re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, confirm: (m) => decodeJwtRole(m) === 'anon' },
];

// Decode the middle segment of a JWT and return its "role" claim, if any.
// No verification — we only read the public payload to tell anon from service_role.
export function decodeJwtRole(jwt) {
  try {
    const payload = jwt.split('.')[1];
    const json = Buffer.from(payload.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8');
    return JSON.parse(json).role ?? null;
  } catch {
    return null;
  }
}

// Find the Supabase project URL in text, e.g. https://abcdefgh.supabase.co
export function findSupabaseUrl(text) {
  const m = /https:\/\/[a-z0-9]{16,}\.supabase\.co/i.exec(text);
  return m ? m[0] : null;
}

// Pull the anon key (a JWT with role "anon") out of text, if present.
export function findSupabaseAnonKey(text) {
  const jwts = text.match(/\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g) || [];
  return jwts.find((j) => decodeJwtRole(j) === 'anon') || null;
}

// Run the secret rules over a blob of text. Returns hits with a redacted sample.
export function scanText(text, source) {
  const hits = [];
  for (const rule of SECRET_RULES) {
    rule.re.lastIndex = 0;
    let m;
    while ((m = rule.re.exec(text))) {
      const value = m[0];
      if (rule.confirm && !rule.confirm(value)) continue;
      // Don't double-report an anon key as a generic JWT etc.
      hits.push({
        id: rule.id, label: rule.label, severity: rule.severity, why: rule.why,
        source, sample: redact(value),
      });
    }
  }
  // De-dupe identical (id, sample, source).
  const seen = new Set();
  return hits.filter((h) => {
    const k = `${h.id}|${h.sample}|${h.source}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

export function redact(value) {
  if (value.length <= 10) return value[0] + '…';
  return `${value.slice(0, 6)}…${value.slice(-4)} (${value.length} chars)`;
}
