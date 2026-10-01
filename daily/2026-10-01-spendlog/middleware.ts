// Opening your dashboard link remembers this browser, so connecting from Claude later
// offers your existing book instead of making a second one.
import { NextResponse, type NextRequest } from 'next/server';
export function middleware(req: NextRequest) {
  const key = req.nextUrl.pathname.split('/')[2];
  const res = NextResponse.next();
  if (key && /^sl_[A-Za-z0-9_-]{10,}$/.test(key)) res.cookies.set('sl_dash', key, { path: '/', maxAge: 31536000, httpOnly: true, secure: req.nextUrl.protocol === 'https:', sameSite: 'lax' });
  return res;
}
export const config = { matcher: '/me/:key*' };
