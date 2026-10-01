# Spendlog (SCRAPPED, Oct 1 2026)

A spending book inside Claude (MCP connector with OAuth): "$42 groceries" logs it, budgets by category, month totals, CSV export. Built and tested (7 test groups, full HTTP sign-in flow), then **scrapped by Cody**: free budget apps are everywhere, so it fails the "real gap" test even though the Claude connector directory lacked one.

Kept for parts: `lib/money.ts` (exact cents math, CSV formula guard) and the OAuth/MCP plumbing adapted from Misslog.
