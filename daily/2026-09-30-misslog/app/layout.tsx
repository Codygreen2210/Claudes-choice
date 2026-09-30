import './globals.css';
import type { ReactNode } from 'react';
export const metadata = { title: 'Misslog', description: 'A mistake journal for your AI. One link, works in Claude, ChatGPT, Cursor and Gemini.' };
export default function Root({ children }: { children: ReactNode }) {
  return (
    <html lang="en"><body>
      <nav><a className="brand" href="/">MISSLOG</a><a href="/leaderboard">Leaderboard</a></nav>
      {children}
    </body></html>
  );
}
