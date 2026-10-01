import './globals.css';
import type { ReactNode } from 'react';
export const metadata = { title: 'Whatcha Make · Are you paid fair for your trade?', description: 'See where your pay lands against your trade in your area, and what it is worth after the cost of living.', icons: { icon: '/favicon.png', apple: '/apple-touch-icon.png' } };
export default function Root({ children }: { children: ReactNode }) {
  return <html lang="en"><body><nav><a className="brand" href="/">WHATCHA MAKE</a><a href="/privacy">Your info</a></nav>{children}</body></html>;
}
