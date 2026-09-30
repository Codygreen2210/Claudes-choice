# Blueprint

An owner's manual for your AI-built app, made from its code in under a second.

You built an app with Lovable, Bolt, Cursor or Claude. It works. But could you say what pages it has, which database tables hold your users' data, which settings are secret, or which outside services you'd get billed by? Most people can't, and neither can their AI builder, which re-reads the whole app every session to figure it out. That's slow and it burns through your usage.

Blueprint reads the code (no AI, nothing leaves your computer) and writes three files:

1. **`BLUEPRINT.md`** — the owner's manual in plain English: what it's built with, where it runs, every page, every server endpoint, every database table and storage bucket, every setting (split into secret and public), the outside services, the commands, and how the code is laid out. Problems go at the top, like a secret key someone marked as public.
2. **`AI-CONTEXT.md`** — a short app map to paste into `CLAUDE.md` or `.cursorrules`, so your AI builder starts every session already knowing the app instead of paying to rediscover it.
3. **`.env.example`** — every setting the app reads, names only, never values. It's what you need when you move hosts or hand the app to someone. Blueprint never overwrites one you already have.

Built Sept 30, 2026, as a daily build. It's a product: it runs on its own, with nobody's time per customer.

## Run it

Node 18+, no install.

```
node blueprint.mjs path/to/your-app            # print the manual
node blueprint.mjs path/to/your-app --write    # save the three files into the app
```

Tested on a real open-source Next.js + Supabase + Stripe app ([vercel/nextjs-subscription-payments](https://github.com/vercel/nextjs-subscription-payments)): 85 files in 0.08 seconds, with all 5 database tables, 10 settings, 4 pages and 3 server endpoints found.

## What it understands

- **Frameworks:** Next.js (app and pages routers, route groups), SvelteKit, Remix, Nuxt, Astro, Vite, Express, plain HTML with Vercel functions.
- **Data:** Supabase tables (`.from('x')`), storage buckets, database functions (`.rpc`).
- **Settings:** `process.env.X` and `import.meta.env.X`. Anything starting with `NEXT_PUBLIC_`, `VITE_` or `PUBLIC_` is flagged as visible to the browser.
- **Services:** Stripe, Supabase, OpenAI, Anthropic, Gemini, Resend, SendGrid, Clerk, Firebase, Prisma, Sentry, Twilio and more.
- **Hosting:** Vercel, Netlify, Railway, Docker. GitHub Actions jobs too.

## Files

- `analyze.mjs` — reads the code and builds the picture.
- `render.mjs` — writes the manual, the AI context and `.env.example`.
- `blueprint.mjs` — the command.
- `test/` — a fake AI-built app on disk, checked end to end.

```
node --test "test/*.test.mjs"
```

MIT license.
