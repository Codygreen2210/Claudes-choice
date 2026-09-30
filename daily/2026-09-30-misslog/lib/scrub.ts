// Nothing private leaves the user's chat. Every text field is scrubbed before it's stored:
// emails, phone numbers, keys/tokens, secret-looking URLs, card-like numbers and file paths
// with a username in them become placeholders. Then it's cut to a short length.
const RULES: [RegExp, string][] = [
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g, '[private key]'],
  [/\b(?:sk|pk|rk|sb|ghp|gho|ghu|ghs|github_pat|xox[abpr]|AKIA|AIza|eyJ)[A-Za-z0-9_\-.]{12,}\b/g, '[key]'],
  [/\b(?:api[_-]?key|secret|token|password|passwd|pwd|bearer)\s*[:=]\s*["']?[^\s"',;]{4,}/gi, '[secret]'],
  [/https?:\/\/[^\s)]*(?:token|key|secret|sig|signature|auth|password)=[^\s)]*/gi, '[link with secret]'],
  [/postgres(?:ql)?:\/\/[^\s]+/gi, '[database url]'],
  [/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, '[email]'],
  [/\b(?:\d[ -]?){13,19}\b/g, '[number]'],
  [/(?:\+?1[ .-]?)?\(?\b\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b/g, '[phone]'],
  [/\b\d{3}-\d{2}-\d{4}\b/g, '[id number]'],
  [/(?:\/Users|\/home|C:\\Users)[\\/][^\\/\s]+/g, '[home]'],
  [/\b[A-Fa-f0-9]{32,}\b/g, '[hash]'],
];

export function scrub(input: unknown, max = 280): string {
  let s = String(input ?? '').replace(/\s+/g, ' ').trim();
  for (const [re, rep] of RULES) s = s.replace(re, rep);
  return s.length > max ? s.slice(0, max - 1).trimEnd() + '…' : s;
}
