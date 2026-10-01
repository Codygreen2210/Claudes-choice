// The site's public address, e.g. https://misslog-sand.vercel.app. Set MISSLOG_ORIGIN to pin it.
export function originOf(req: Request | { headers: Headers }): string {
  if (process.env.MISSLOG_ORIGIN) return process.env.MISSLOG_ORIGIN.replace(/\/$/, '');
  const h = req.headers;
  const host = h.get('x-forwarded-host') || h.get('host') || 'localhost:3000';
  const proto = h.get('x-forwarded-proto') || (host.startsWith('localhost') || host.startsWith('127.') ? 'http' : 'https');
  return `${proto.split(',')[0]}://${host.split(',')[0]}`;
}
