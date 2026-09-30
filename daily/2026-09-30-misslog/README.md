# Misslog

A mistake journal for any AI. Someone clicks **Get my link**, pastes the link into Claude, ChatGPT, Cursor or Gemini as a connector, and from then on that AI:

- reads its past mistakes before a task (`my_misses`)
- logs a mistake the moment the user pushes back (`log_miss`): what it was trying to do, the ask, the mistake, the fix, and estimated tokens burned
- adds the fix later (`add_fix`) and logs research sessions (`log_search`)

**Game side:** XP, levels, streaks and badges per profile, plus a public leaderboard per AI family (mistakes, fix rate, tokens per mistake, total tokens, estimated cost, searches, people).

**Privacy:** there's no sign-up; the link is the key. Every field is scrubbed (emails, keys, tokens, phone and card numbers, home paths) and cut short before it's saved. Raw prompts are never stored. Profiles are private until the owner flips them public. Sharing anonymous totals for research reports is opt-in and off by default.

## Run it

```
npm install
npm run dev          # uses a local .data/db.json
npm test             # 5 test groups, including a full MCP session
```

## Put it online (Cody's steps)

1. Supabase: run `supabase.sql` in the SQL editor.
2. Vercel: import the repo with root `daily/2026-09-30-misslog` and set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
3. Done. The connector link is `https://<site>/api/mcp/<key>`.

## Files

- `lib/mcp.ts`: the MCP server (JSON-RPC over HTTP), tools and instructions
- `lib/scrub.ts`: strips private details
- `lib/cost.ts`: token and dollar estimates (prices dated, rough on purpose)
- `lib/game.ts`: XP, levels, streaks, badges, leaderboard math
- `lib/store.ts`: Supabase or local-file storage
- `app/`: home (join), `/me/<key>` dashboard, `/u/<handle>` public profile, `/leaderboard`

## Honest limits

- Mistakes are self-reported by the AI, so an AI that owns up more can look worse on the board.
- Tokens are the AI's own estimate or a default by kind. Dollar figures are ballparks.
- The rate limit is per server instance. Put Vercel's firewall in front if traffic grows.
