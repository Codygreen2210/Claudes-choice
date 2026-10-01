import { CONTACT, contactLink } from '../../lib/site.ts';
export const metadata = { title: 'Spendlog privacy policy' };
export default function Privacy() {
  return (
    <main className="wrap" style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: 36 }}>Privacy policy</h1>
      <p className="note">Last updated October 1, 2026.</p>
      <h2>What Spendlog collects</h2>
      <ul>
        <li><b>Entries you or Claude add:</b> amount, expense or income, a category, a short note (like a store name), and a date.</li>
        <li><b>Budgets you set:</b> a category and a monthly amount.</li>
        <li><b>A random name</b> for your book (like “steady-pelican-42”). No email, no real name.</li>
        <li><b>Basic request data:</b> your IP address for rate limiting, kept in memory and not stored.</li>
      </ul>
      <h2>What it never collects</h2>
      <p>No bank logins, account numbers or card numbers, and your conversations with Claude aren't sent to Spendlog; only the entries Claude adds through its tools are. Notes are scrubbed of emails, phone numbers, card-like numbers and keys before they're saved.</p>
      <h2>How it's used</h2>
      <p>Only to show your book to you and to the Claude account you connect: totals, budgets and entries. It isn't sold, shared or used for ads.</p>
      <h2>Who stores it</h2>
      <p>Data is stored with Supabase (database) and served by Vercel (hosting), who process it on Spendlog's behalf.</p>
      <h2>Keeping and deleting</h2>
      <p>Entries are kept until you delete them. You can download everything as a spreadsheet, delete single entries (through Claude), or delete your whole book from its page (“Delete my book”). Sign-in tokens expire on their own: one hour, with refresh tokens after 60 days.</p>
      <h2>Age</h2>
      <p>Spendlog is for people 18 and older.</p>
      <h2>Security</h2>
      <p>Connections use HTTPS. Sign-in codes and tokens are stored only as one-way hashes. Database tables are locked so only the Spendlog server can read them.</p>
      <h2>Contact</h2>
      <p>{CONTACT ? <a href={contactLink()}>{CONTACT}</a> : 'Contact details are listed on the Spendlog home page.'}</p>
    </main>
  );
}
