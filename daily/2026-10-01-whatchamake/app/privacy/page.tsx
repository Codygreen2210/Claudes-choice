const CONTACT = process.env.WM_CONTACT || '';
export const metadata = { title: 'Your info · Whatcha Make' };
export default function Privacy() {
  return (
    <main className="wrap" style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: 36 }}>Your info, straight</h1>
      <p className="note">Last updated October 1, 2026.</p>
      <h2>What you give</h2>
      <ul>
        <li>Your job, the area you work in, your hourly pay, your regular and overtime hours a week, and (if you want) years in the trade.</li>
        <li>Your Google sign-in. It's only used to make sure each answer comes from one real person; a new answer replaces your old one.</li>
      </ul>
      <h2>What's never shown or shared</h2>
      <p>Your name, email and Google account are never shown to anyone, never attached to your pay, and never sold or shared.</p>
      <h2>How your pay numbers are used</h2>
      <ul>
        <li>They're pooled with everyone else's to show “from people like you” pay. A group's numbers only appear once at least 5 people in that job and area have shared, so no one can pick out one person.</li>
        <li><b>The pooled, anonymous pay data may be shared or sold</b> to people who study pay, like employers, researchers and job sites. It's only ever groups of 5 or more, never one person's answer, and never with names or emails.</li>
      </ul>
      <h2>Deleting</h2>
      <p>You can delete your answer any time{CONTACT ? <> by emailing <a href={CONTACT.includes('@') ? `mailto:${CONTACT}` : CONTACT}>{CONTACT}</a></> : ' by contacting us'}. Deleted answers are removed from future counts and reports.</p>
      <h2>Where it's kept</h2>
      <p>Data is stored with Supabase and the site runs on Vercel. Sign-in is through Google. Connections use HTTPS, and the answers table can only be read by the site's server.</p>
      <h2>Age</h2>
      <p>For people 18 and older.</p>
      <h2>Where the comparison numbers come from</h2>
      <p>Pay ranges: U.S. Bureau of Labor Statistics, Occupational Employment and Wage Statistics, May 2024. Price levels: U.S. Bureau of Economic Analysis, Regional Price Parities, 2024. Both are public. Results are comparisons, not financial or legal advice.</p>
    </main>
  );
}
