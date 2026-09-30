import Join from '../components/Join.tsx';
import { getStore } from '../lib/store.ts';
import { fmtTokens } from '../lib/cost.ts';
export const dynamic = 'force-dynamic';

export default async function Home() {
  const rows = await (await getStore()).board();
  const total = rows.reduce((a, r) => a + r.misses, 0), tokens = rows.reduce((a, r) => a + r.tokens, 0);
  return (
    <main className="wrap">
      <h1>Your AI keeps making the same mistakes.<br />Make it write them down.</h1>
      <p className="lead">One link turns any AI into one that keeps a journal: what it was trying to do, what you asked, what went wrong, and the fix. It reads the journal before it starts, so it quits repeating itself.</p>
      <Join />
      <h2>How it works</h2>
      <ol>
        <li>Get your link and paste it into Claude, ChatGPT, Cursor or Gemini as a connector.</li>
        <li>When you tell your AI "that's wrong," it logs the mistake, and later the fix.</li>
        <li>Before each task it reads its past mistakes. You see the tab: tokens and dollars burned, per AI.</li>
      </ol>
      <h2>So far</h2>
      <p>{total} mistakes logged across {rows.length} AI families, about {fmtTokens(tokens)} tokens burned. <a href="/leaderboard">See the leaderboard</a>.</p>
      <p className="note">Private by default. Fields are scrubbed of emails, keys and numbers before they're saved, and your prompts themselves are never stored, only the AI's short summary.</p>
    </main>
  );
}
