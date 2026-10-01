import './globals.css';
import type { ReactNode } from 'react';
export const metadata = { title: 'Spendlog', description: 'A spending book that lives inside Claude. Say what you spent; it keeps your budget. No bank login.', icons: { icon: '/favicon.png', apple: '/apple-touch-icon.png' } };
export default function Root({ children }: { children: ReactNode }) {
  return (
    <html lang="en"><body>
      <nav><a className="brand" href="/">SPENDLOG</a><a href="/docs">How to use</a></nav>
      {children}
    </body></html>
  );
}
