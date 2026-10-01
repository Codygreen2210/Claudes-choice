# Whatcha Make

"Are you paid fair for your trade?" Drop the link; people pick their job and area, enter hourly pay and hours, sign in with Google, and see:
- where they land against everyone in that job and metro (BLS OEWS May 2024 percentiles)
- what their pay is worth after local prices (BEA Regional Price Parities 2024) vs the U.S. middle for the job
- their yearly estimate with overtime
- "from people like you" pay once 5+ people share the same job and area

Every answer (one per signed-in person) builds a pay data set for hands-on jobs, the gap Glassdoor and job-posting data miss. Pooled, anonymous data (groups of 5+) may be sold; this is stated plainly on /privacy.

Data: `data/wages.json` built from BLS `MSA_M2024_dl.xlsx` (259 jobs in SOC groups 47/49/51/53 across 393 metros) and BEA RPP 2024 (386 metros).

## Run
```
npm install && npm run dev   # local: no Supabase, "sign in" is a dev pass-through
npm test                     # 5 test groups
```

## Put it online (Cody)
1. Supabase (Misslog project is fine; table is `wm_answers`): run `supabase.sql`.
2. Supabase → Authentication → Sign In / Providers → Google: turn on. It shows a Callback URL; paste that into a Google Cloud OAuth client (Web), and copy the client ID + secret back into Supabase. Basic email/profile sign-in needs no Google review.
3. Supabase → Authentication → URL Configuration: Site URL = your Vercel address; add `https://<your-site>/results` to Redirect URLs.
4. Vercel: import with root `daily/2026-10-01-whatchamake`; env vars `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (Project Settings → API), optional `WM_CONTACT`.
