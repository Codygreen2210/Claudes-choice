# Idea journal

Every idea the studio's scouts looked at, and why it was liked or killed. Newest round first.

**The bar (set by Cody, Oct 3, 2026):** build only when an idea has at least a 3 in 6 chance of 100 paying customers within 30 days of launch, starting with no audience and no ad money. If nothing clears it, ideas are introduced here and not built.

Odds are the scout's own estimate of reaching 100 paying customers in 30 days. Founder numbers quoted from the web are self-reported unless noted.

---

## Oct 3, 2026: Rounds 11 to 15, five agents a round (4 inventors or repairers + 1 checker, Sonnet)

Cody's order: five agents, keep going until the checker says "stands". Brief: tech sector, free, money from data, fast self-growth. Stopped after round 15 because the session hit its cap of 200 web searches. **Nothing stood.** Briefs and search logs: `daily/2026-10-03-round11/` to `round15/`. From round 13 the mechanism was changed (my call): the page collects public data itself, BuiltWith style, instead of waiting for users to create it.

- R11 **Will It Run** (browser test of which AI models your device runs) | killed | inventivehq.com/tools/developer/llm-gpu-benchmark does it.
- R11 **Package worked/broke votes** | dropped by its inventor | Renovate Merge Confidence; no cold-start answer.
- R11-12 **Hours Guess** (guess how long real GitHub fixes took, share a calibration card) | weakened | no such game exists, but answer-key licence unclear and the data is a curiosity. Could live as a cheap quiz, not a data business.
- R11-12 **Swap Notes** (AI model migration brief plus "what broke" reports) | weakened | vendor guides and coding assistants cover the brief; the inventor's retirement counts did not check out; nobody pastes a stranger's link into company code review.
- R12 **Still Installs?** (Android sideload verification check) | weakened | rests on a Google API with a 1,000-a-day cap; audience is sideloaders in four non-English countries.
- R12 **AI Footprint Card** (badge for how much of a repo AI wrote) | exists | AI Maxing.
- R13 **StackDex** (which repos wire up which MCP servers) | partly exists, thin | GitHub code search limits make a census impossible.
- R13-15 **HF Tape** (Hugging Face download history per model with rivals) | weakened, close to dead | history is already a free dataset (cfahlgren1/hub-stats); stranger-made Spaces top out near 100 to 150 likes; no buyer.
- R13 **Hub Graveyard** (deleted or relicensed model tracker) | weakened | a feature of the same snapshot; paid Apify monitors exist.
- R13-14 **Breaking-Change Table** (league table of which public APIs break callers most, from vendors' own spec repos with oasdiff) | weakened | no public ranking exists and sources are real (Stripe, GitHub, Cloudflare, OpenAI, Twilio, Adyen, DigitalOcean, Plaid), but the past is rebuildable by anyone and repeat visits are weak. A good one-off study.
- R14 **Who Gets My Data** (which AI companies are on a tool's subprocessor list) | killed | conductatlas.com archives these free for 352+ platforms; Wayback holds the past.
- R14-15 **Router Pulse** (is my router model still getting updates) | weakened, leaning dead | no cross-brand tracker exists, but TP-Link's and Asus's terms ban bots and copying; spread untested.
- R15 platform angle (unfinished, search cap): Telegram's bot terms ban collecting data to build datasets; Reddit's developer platform needs app review and bars selling Reddit data; Discord is open but its crowd is gamers. "Settle It" (group tool comparison) returned unchecked.

## Oct 3, 2026: Round 10, free-with-data inside the tech sector (2 inventors + 1 checker, Sonnet)

Brief from Cody: same as round 9 but tech sector only. Inventors were told the round 9 lessons (must work for the first user; one record must be worth something; no installs; nothing sensitive). Result: **neither cleared the bar.** Search logs: `daily/2026-10-03-round10/log-*.jsonl`. No video made.

- **Run Autopsy** (paste an AI coding session log, see where the agent looped or wasted tokens, donate the cleaned log with a worked/didn't-work label) | weakened | the analysis half exists free (agentfdr, claude-replay, claude-code-transcripts, agentlore); Anthropic's terms bar using Claude output to train competing models, so logs full of it are hard to sell to rival labs; finding the log in a hidden folder is not one click; secret stripping cannot be trusted; two of the inventor's links did not say what was claimed. No paying buyer found. Checker odds: 100 users in 30 days 1 in 6.
- **AI Speedtest** (one click times your connection to ChatGPT, Claude, Gemini and others) | killed | myaispeed.com already does it in the browser for 18+ providers with share buttons and anonymous data collection; browsers cannot read connect or first-byte timings across sites, so it mostly measures distance to the nearest network edge, which is already mapped. No paying buyer found.

## Oct 3, 2026: Round 9, free users whose data makes the money (2 inventors + 1 checker, Sonnet)

Brief from Cody: free product, growth built in, money from the data. He ruled the checker does not kill for lacking a paying data buyer today. Result: **neither cleared the bar.** Search logs: `daily/2026-10-03-round9/log-*.jsonl`. No session video made (condition was an idea standing). Cost about 560k subagent units, including two runs cut short by the web search limit.

- **Neighbor Bill** (type your internet bill and ZIP, see what neighbors pay; add yours to see) | weakened | Consumer Reports already ran it once with 22,000 bills, using a trusted brand and an email list; first user in most of about 41,000 ZIPs gets an empty answer; fake entries with no sign-up; no buyer for paid-price data found (buyers exist for advertised prices only). Checker odds: 100 users in 30 days about 40%, 10,000 in six months about 5%.
- **Heard Wrong** (read a sentence aloud, see what three speech AIs typed, share the miss card) | weakened, close to killed | voice is biometric: nine BIPA class actions filed May 2026 over voice used for AI training; microphone prompt is a second click; 3,000 ten-second clips is under 10 hours, worth a few hundred euros at Defined.ai's roughly 160 euros an hour, and Common Voice gives hours away free. The share-card format itself is open. Checker odds: 35% and 4%.

## Oct 3, 2026: Round 8, first round run the ROUND.md way (three passes, 2 inventors + 1 checker each, Sonnet)

Brief from Cody: an idea top MIT graduates would start and get funded at multi-million or billion scale, that one person could build alone at home on a laptop. Result: **nothing stood.** Six ideas, six knocked down. Cost: about 925k subagent units for all three passes (earlier rounds: 2.75M to 5.3M each).

- **Obey Test** (link that tests whether an AI obeys hidden instructions) | weakened | free versions exist (Agent Arena, Prefactor); server logs cannot see "obeyed"; nobody pays for a chart.
- **Deduction report checker** (small food brands, KeHE/UNFI/Walmart) | killed | Glimpse (a16z) already serves small brands with a free trial; one report cannot prove a line wrong without PO and delivery papers; disputes go through portals.
- **Balance Check** (vendor statement matching with a reply link) | weakened | Dext does the matching for small business; reply link reads as phishing; needs two uploads.
- **Tested version sets for coding agents** | weakened | depscope MCP has the same tool; agents pay about $5k to $11k a month in total across x402 (TRM Labs); an MCP server is an install.
- **Contractor bid comparison** | killed by its own inventor | ReadMyBid, GreatBuildz BidCompare, EstimateHawk.
- **Env Forge** (fill Prime Intellect environment bounties) | killed | checker opened the bounty sheet: program closed, no claims accepted.

**Finding that held under the checker:** every verified 2024 to 2026 solo or two-person software win (Base44 to Wix for $80M, Cal AI, OpenClaw) had a track record, an audience, creator videos or open-source fame. No verified case of a no-audience first-timer was found.

## Oct 3, 2026: Round 7, make a Pro plan last like Max (5 teams, Sonnet)

Brief: cut usage per finished piece of work toward 5x, going past Anthropic's own tips, no repeats. **All savings below are estimates. Nobody has measured them on a real account, and Anthropic does not publish how plan limits weigh cached text or each model.**

| Method | What it is | Est. saving, whole account | Odds it holds | Build time |
|---|---|---|---|---|
| **Offload Ledger** | A script ranks which tool outputs cost most in your own logs (size x turns kept), then caps the top three: partial file reads, failures-only logs, diffs. | 1.3x to 1.8x | 4/6 for 1.3x | ~2 days |
| **Gearbox** | Plan on Opus in a small session, do the work on Sonnet at medium in a fresh one, never switch model mid-session (a switch re-reads everything), subagent only if it keeps 20k+ tokens out of a chat with 15+ turns left. | ~1.5x | 4/6 | ~2 days |
| **Lean Roster** | A small connector set per kind of job instead of everything on. Biggest in the chat app, where 10+ connectors may load 30k to 70k tokens every turn. | 1.2x in Claude Code, up to 2x to 3x in connector-heavy chat | 4/6 chat, 3/6 Code | ~1 day |
| **Ledger Reset** | Claude adds 3 lines to a notes file after each step, so a fresh chat can start any time for free. Reset after a break or when history gets long, by rule not feel. | 1.2x to 1.5x | 3/6 | ~1 day |
| **Read-Back Gate** | Before big work, a 60-word read-back: deliverable, done test, two assumptions, one thing it will not touch. If it still goes wrong, restart with the read-back, do not argue in the old chat. | 1.2x to 1.4x | 3/6 | ~1 day |

**All five teams' verdict:** stacked, about 2x to 3x. 5x is unlikely: the methods overlap (most cut the same re-read cost), and nobody found a measured share of usage that is pure waste.
**Open facts:** teams disagreed on how long cached text stays cheap on a plan (5 minutes vs 1 hour), and on model prices; neither was checked against Anthropic's pages.
**Liked:** Lean Roster (fits a many-connector phone user, free, testable today) and Offload Ledger (biggest single lever, measures before it cuts).
**Status:** introduced, not built, not measured. Waiting on Cody.

## Oct 3, 2026: Round 6, frontier startups for Claude only (5 teams, Sonnet)

Brief: round 4 rules, but each idea must make Claude specifically better, from the outside, with nothing repeated. **Nothing built or measured. Odds are the teams' own.**

| Idea | What it does | Demo number | Odds: demo in 2 wks / 100 users in 30 days / press / Anthropic builds it in 6 months |
|---|---|---|---|
| **Stencil** | After Claude does the same edit by hand 2 or 3 times, it writes a script, proves the script reproduces those edits exactly, then finishes the rest for zero tokens. | Tokens and time on a 60-file job, with and without | 4/6, 2/6, 2/6, 2/6 |
| **Bedrock** | Traces every line in Claude's memory back to words the person actually said; lines it cannot trace are set aside, not deleted. | Share of planted false memory lines caught | 5/6, 3/6 (free installs), 2/6, 2/6 |
| **Foreman** | An outside supervisor for long Claude Code runs: keeps a list of dead ends the agent cannot edit, puts it back after each compaction, blocks repeats. | Tokens wasted on repeated failures over 8 hours | 4/6, 2/6, 2/6, 3/6 |
| **Bylaw** | Turns written rules (like "never delete in a connected app") into hard blocks, tested first, with a count of how often each rule held. | Rule breaks per 100 tasks, with and without | 4/6, 2/6, 2/6, 2/6 |
| **Spec Pass** | Claude writes code that checks an image against a written spec and fixes failures; text and colours placed by code. | Pass rate on 100 exact-spec prompts vs raw image models | 4/6, 2/6, 2/6, 1/6 |

**Liked:** Stencil (clearest before/after number, goes at usage caps, the loudest complaint) and Bedrock (best odds, a failure Anthropic's own issue tracker documents).
**Liked less:** Foreman (most likely to be built by Anthropic), Spec Pass (dead if rival image models already pass; helps any model, not just Claude).
**Doubt on Bylaw:** the Bedrock team found rules-into-blocking-hooks already crowded (Claude Rule Enforcer, sentinel-ai); the Bylaw team said nobody does it. Needs a check before any build.
**Honest read:** these fix known weak spots. None would by itself put Claude far ahead of every other model; that takes changes inside the model, which an outside add-on cannot make.
**Status:** introduced, not built. Waiting on Cody.

## Oct 3, 2026: Round 5, breakthrough bets (5 researchers, Sonnet)

Brief: each agent acts as a top new researcher going after an unproven breakthrough that works on top of most AI models. No customer target. Every bet needs an experiment that could prove it wrong. **Nothing here has been run. These are conjectures, and the agents read mostly paper summaries, not full papers.**

| Bet | The claim | The proof experiment | Time and cost | Odds: can run / comes out right / as big as hoped |
|---|---|---|---|---|
| **Checker-Once Cascade** | An expensive model writes a checker once per kind of task; cheap models do the work; only rejected answers go back to the expensive model. | Cost per correct answer at least 8x lower, accuracy within 1 point, wrong answers let through 2% or less. | ~3 weeks, $500 to $2,000 | 5/6, 1.5/6, 2/6 |
| **Tiebreaker Court** | When models disagree, settle it with a written test that is actually run, not by vote or debate. | At least 3 points better than the best single model at equal cost on fresh coding problems. | ~3 weeks, $500 to $1,500 | 5/6, 2/6 (3/6 to beat voting), 1/6 |
| **Disguise Test** | Reword a question to strip its surface cues; if the answer changes, the model was guessing. | Predicts right vs wrong at 0.80 or better (1.0 is perfect, 0.5 is a coin flip) on six fields it was not tuned on. | 3 to 4 weeks, up to ~$1,500 | 5/6, 1/6, 2/6 |
| **Fork Test** | Have several models each write a simulator of the situation; where they disagree is where the model's picture of the world is wrong. | Flags bad plans at 0.80 or better and lifts plan success 15 points. | 3 to 4 weeks, $2,000 to $5,000 | 5/6, 2/6, 1/6 |
| **Ratchet** | A model's playbook only changes when the change wins a replay and holds up on a second model, so it learns from use without retraining and without drifting. | ~300 recurring tasks, 3 models: beat the ungated method by 10 points at task 100, and 60% of the gain carries to another model. | 3 to 4 weeks, $3,000 to $10,000 | 4/6, 2/6, 1/6 |

**Liked:** Checker-Once Cascade (cost is the thing every buyer already measures, and the test is cheap and clear) and Tiebreaker Court (cheapest test, best odds of a real result).
**Liked less:** Ratchet (biggest prize, most expensive test, longest odds), Fork Test (hard to pick fair tasks), Disguise Test (1 in 6 to come out right; rewording itself can change the question).
**Status:** introduced, not built, not tested. Waiting on Cody.

### Checker-Once Cascade: small pilot run Oct 3 (not the full proof)

36 tasks with exact answer keys (12 crew schedules, 12 invoices, 12 pick-a-set puzzles). Opus wrote one checker per kind from one example. Haiku answered everything; Opus answered everything as the baseline. Models were told not to run code.

| | Right out of 36 |
|---|---|
| Haiku alone | 29 |
| Opus alone | 34 |
| Cascade (Haiku, checker, Opus on rejects) | 34 |

- Wrong answers the checkers let through: 0 of 7.
- Haiku kept 24 of 36 tasks; 12 went up to Opus (11 of them invoices, where the checker turned away 5 correct answers because it would not accept anything it could not fully recompute).
- If Opus costs about 5x Haiku per task (assumed, not measured), that is roughly 2x cheaper overall, about 4x on the two kinds with a clean checker. The 8x target cannot be reached with these two models; it needs a much cheaper small model.
- Limits: tiny sample, one family of models, tasks I made up, cost not metered, and the invoice key rounds half-cents up, which the task wording did not say (may explain Opus's two misses).

## Oct 3, 2026: Round 4, frontier startups (5 teams, Sonnet)

Cody changed the rules for this round: each agent acts as a startup inventing new technology that makes today's AI models far better. The only rules kept: nothing repeated, and get to 100 customers as fast as possible. Aim for something the AI newsletters would lead with.

Odds are each team's own: a working demo in two weeks / 100 customers in 30 days of showing it (free users count) / real newsletter pickup. Nothing here has been built or measured.

| Idea | What it does | The demo | Closest existing things | Demo | 100 users | Press |
|---|---|---|---|---|---|---|
| **Stale Stamp** | Stops an AI coding agent from saying "done, tests pass" when it changed the code after the tests ran. It runs the checks itself, records exactly which files they read, and voids the result if any of those files change. | Replay real agent sessions and show what share of "done" claims were stale and how many it blocked. One developer measured 35% stale in 101 claims. | Tool receipts (record calls, not whether still true); ORP; the studio's own second-look and Misslog | 4 in 6 | 2 in 6 | 2 in 6 |
| **Gap** | Lists what an AI summary or rewrite left out of the original, each with a quote. Models are measurably bad at noticing what is missing (AbsenceBench, NeurIPS 2025). | 100 documents, 3 planted omissions each: how many does plain asking find, versus Gap. | A developer coverage metric; a French medical checker; contract clause tools | 4 in 6 | 2 in 6 | 2 in 6 |
| **Earshot** | Gives a text-only model ears for tone: a timeline of how each phrase was said (pace, pitch, pauses) next to the words, flagging when the words and the voice disagree. | A public scoreboard on VoxParadox, a test where words and tone conflict; today's best audio model scores 17.4%. | Hume (emotion score per clip); research cascades with no packaged tool | 4 in 6 | 2 in 6 | 2 in 6 |
| **Patchwork** | Finds the one broken part of an AI-made video (wrong hand, changed jacket), repairs only that region, and proves the rest of the frame was untouched. | 14 benchmark clips, before and after, with defects found, fixed and pixels changed outside the repair. | Checkers that only flag; region editors that need a person to draw the mask | 4 in 6 | 1 in 6 | 2 in 6 |
| **Receipts** | Sits between a coding agent and the model, replaces repeat file reads with short "unchanged" stubs, and replays your own past sessions to show the savings before you turn it on. | Ten real tasks with and without it: tokens, dollars, tests passing. | Several token-saving tools already; the gap is the replay proof | 4 in 6 | 2 in 6 | 1 in 6 |

Ideas the teams passed on: turning repeated agent runs into fixed scripts (academic work exists, small savings); shared model cache across teams (needs control of the model servers); cross-user mistake store (Misslog covers it); a "stop and ask" gate (research project, no buyer); a scene file for exact visual edits (Remotion and others do it); a character-lock layer for video (the big labs' race); a pause-and-stress score for speech (close research exists); a fast voice that holds the floor while a slow model thinks (OpenAI and NVIDIA do it); a freshness checker for outdated facts (search tools cover it); a reader-stumble map (not new enough).

---

## Oct 3, 2026: Round 3, each scout brings its one best idea (10 scouts, Sonnet)

Cody asked for another run and said he would decide on a build himself. Each scout had to bring back its single best idea even if it fell short, with odds at 30 and 90 days.

**Result: 0 of 10 met the bar. Best odds: 1 in 6 at 30 days, 1.5 in 6 at 90 days.**

| Scout's best idea | Who pays today | What kills it | 30 days | 90 days |
|---|---|---|---|---|
| **Prop Rule Check**: drop in a trade export, pick a prop firm, see pass or fail on its loss and consistency rules | Traders spend about $4,270 each on evaluations; journals cost $19.99 a month | TradesViz covers 37+ firms with a free tier; five free calculators; no proven way to reach traders | 1 in 6 | 1.5 in 6 |
| **Year-End Packet**: upload a giving spreadsheet, get a statement for every donor | One statements-only add-on sells at $497 a year; church software $29 to $119 a month | MosesTab does it free from a CSV with no signup (one donor at a time); no channel to volunteer treasurers; January only | 1 in 6 | 1.5 in 6 |
| **Client Question Sheet**: bookkeeper sends clients one link to explain unclear transactions | Uncat, $9 per client a month, 263 reviews | Uncat is the default and plugs into QuickBooks; free forms; bookkeepers are wary of new tools with client data | 1 in 6 | 1.5 in 6 |
| Hearing packet builder (exhibit stickers, page numbers, index) | $5 to $20 per packet | Twelve tools already, some free | 1 in 6 | 1.5 in 6 |
| Print-size pack sold through Fiverr | $5 to $20 gigs | New Fiverr sellers get 0 to 20 orders in month one; it is a service, not a product | 1 in 6 | 1.5 in 6 |
| Thesis format pre-check | $200 Fiverr formatters; $3 a page at one university | Four upload-and-format tools plus a $5 checker; one-time need; no channel | 1 in 6 | 1 in 6 |
| Vendor W-9 request link | getW9 from $19 a year | Eight tools, one free; the 2026 threshold change shrinks the need; holds tax ID numbers | under 1 in 6 | 1 in 6 |
| Course video check before Udemy review | No one, as far as found | Udemy publishes no pass/fail numbers; free audio tools | under 1 in 6 | 1 in 6 |
| Windows 10 renew-or-replace sheet | No one pays for the sheet | Free calculators and ChatGPT | 1 in 6 | 1 in 6 |
| Google Play external-link fee ledger (reporting began Oct 1, 2026) | No one yet; no tool exists | Tiny pool of developers; the real report needs API keys; Google keeps moving the date | under 1 in 6 | 1 in 6 |

Also killed this round (0 to 1 in 6): Exchange EWS usage decoder (a free one is live), privilege log builder, redaction checker, spreadsheet to legal billing format, table of authorities, journal figure checker, poster resizer, reference list cleaner, prop spend ledger, profit cards from statements, reference check link, change order approval link, contractor pay application generator, supplier quote compare, subtitle gigs, audiobook loudness fixer, podcast feed validator, flashing checker, musician loudness check, auction receipts, volunteer hour certificates, HOA dues notices, French e-invoice maker (nine free ones), Teamer shutdown exporter, Amazon peak fee recalculator, AI memory transfer.

Checked after the round: MosesTab's free giving-statement tool takes a CSV with no signup and adds the acknowledgement wording, so Year-End Packet's only gap is doing every donor in one go.

---

## Oct 3, 2026: Round 2, channel first (10 scouts, Sonnet)

Round 1 showed the products were fine and the channel was the problem, so this round started from the channel: what can a brand-new seller with no following really get from it in 30 days?

**Result: 0 of 10 passed.**

| Channel | Verdict | What a new seller really gets in month one | Odds |
|---|---|---|---|
| Etsy digital, new shop | Killed | Typical 0 to 10 sales; best found about 20. One shop: 126 views, 8 orders. New shops are slow to show in search. | 1 in 6 |
| Teachers Pay Teachers | Killed | $29 to join. Cases: 0 sales, 14 sales, $0. Best case 235 sales took 3 months. TpT demotes AI-made stores. | 1 in 6 |
| Gumroad Discover | Killed | Discover shows nothing until a product has sales. Two sellers with 25+ products each made $0. | 0 in 6 |
| Lemon Squeezy marketplace | Killed | Needs approval plus prior sales. | 0 in 6 |
| Whop | Killed | One unverified case of 87 members in 60 days, for a paid community. Buyers there want communities and signals. | 1 in 6 |
| TikTok and Reels, new account | Killed | Median about 350 views a video. 100 buyers needs roughly 3 to 25 million views. Winners rode one or two viral videos. | 1 in 6 |
| Pinterest, new account | Killed | About 900 visits a month at best; buyers arrive 4 to 12 weeks after the click. | 1 in 6 |
| YouTube how-to search | Killed for 30 days | Videos take 250 days to a year to rank. Good slow channel (Tiiny Host, Atlist). | 1 in 6 |
| Hand-written replies in communities | Killed | Cleanest case: 6 paying customers for 15 hours of work. The "60 customers in 45 days" case from round 1 is contradicted by the same founder reporting 4 in 90 days. | 1 in 6 |
| Launch platforms (Product Hunt, Show HN, others) | Killed | Typical unknown launch: 100 to 500 visits, 0 to 5 paying. Front page of HN: 500 visitors, no sales. | 1 in 6 |
| Template marketplaces | Killed | Notion, Figma, Canva closed or months of review. Framer is open: 1 to 21 sales in the cases found. | 0 to 1 in 6 |
| AI assistant add-on stores | Killed | Instant ones can't charge; ones that charge have a review step or almost no buyers. Best case: 1 customer in a week. | 0 in 6 |

Products considered inside those channels, all killed at 0 or 1 in 6: free web tool sold as an Etsy link, budget spreadsheet packs, Canva template links, bulk worksheets for TpT, $5 one-tap consumer tool for TikTok, sticker and template packs, resume template packs, Notion and Canva packs, wedding printables, pin-making tool, niche Framer templates, paid MCP servers, skill packs, pay-per-call agent tools, small paid developer tools launched on Product Hunt.

---

## Oct 3, 2026: Round 1, sector first (10 scouts, Sonnet)

Sectors per Cody's direction: people actively searching for a fix, plus tech and finance.

**Result: 0 of 10 passed.**

### Developers and AI builders
- Play Store 12-tester helper | killed | It's a service (needs real people on real phones); five sellers plus free swap groups | 1 in 6
- App store screenshot maker | killed | Eight or more paid tools plus Figma and Canva | under 1 in 6
- Fix for AI-built sites not showing in search | killed | Three sellers already, and it needs DNS setup, so not one click | 1 in 6
- CLAUDE.md / AGENTS.md generator, rules packs | killed | Free generators and free rule libraries | under 1 in 6
- Supabase keep-alive pinger | killed | Free fix is everywhere; would need the customer's keys | under 1 in 6
- App privacy label and policy generators | killed | Established sellers; edges into legal advice | 1 in 6

### Small-business money chores
- Bank statement PDF to Excel | killed for 30 days | **Proven money** ($12.5K to $38K a month for the leader) but it took years of Google ranking; the leader's own ads and 1,000 cold emails failed | 1 in 6
- Bank CSV to QuickBooks formats | killed | Nine free tools | 0 in 6
- Stripe payouts to QuickBooks entries | killed | Already sold from $5 with a free preview | 1 in 6
- Amazon or Etsy settlements to accounting | killed | A2X plus four cheaper rivals | 1 in 6
- Venmo, Cash App, PayPal statements to CSV | killed | Five free converters | 0 in 6
- Payroll report to journal entry | killed | Gusto does it natively | 1 in 6

### Personal money paperwork
- Crypto or brokerage export to tax-software format | killed | Free tools and the exchanges' own reports | 0 in 6
- 1099-DA check against own records | killed | Sold by CoinLedger and CPA firms; needs whole wallet history | 1 in 6
- Visa bank-balance evidence checker | killed | Existing analyzers hold the searches; no channel | 1 in 6
- Gig driver income merger | killed | Platforms give drivers a summary already | 1 in 6
- eBay/Etsy 1099-K vs sales reconciler | killed | Sellers complain, but no one is paying for a fix and no channel | 1 in 6

### Online sellers
- **Whatnot true-profit page, no login** | killed, best lead in the sector | Real pain in sellers' own words ("takes hours every week"), spreadsheets for it sell on Etsy at $5 to $47, but Aftershows already does it at $19 a month and there's no open channel to Whatnot sellers | 1 in 6
- Shipping label cropper | killed | Six free sites | 0 in 6
- Shopify product CSV fixer | killed | Six existing tools | 0 in 6
- Packing slips from an orders file | killed | Free generators; platforms print them | 0 in 6
- Reseller profit per item | killed | Free calculators; Seller Ledger from $10 a month | 1 in 6
- Replacement for Shopify's Stocky (shut down Aug 2026) | killed | Eight alternatives already listed | 1 in 6

### Freelancers and creators
- Media kit generator | killed | Nine free ones | under 1 in 6
- Podcast sponsor report | killed | BuzzyPod bundles it at $10 a month | 1 in 6
- Rate cards, retainer reports, handoff pages | killed | Free templates and free tiers | 1 in 6
- Note: this group pays for platforms, not single documents.

### Job seekers
- **Unemployment work-search log, all states** | killed | About 35 states require written records and one Texas tool charges for it, but every state posts a free form and a new site can't rank in 30 days | 1 in 6
- Federal resume formatter | killed | Six builders plus the government's free one | 1 in 6
- Resume-to-application-field kit, portfolio packager, clearance prep sheet | killed | Free tools or tiny markets | 1 in 6

### File and data conversion
- WhatsApp chat to court-ready PDF | killed | Eight sites already | 1 in 6
- Fuel tax mileage report | killed | Free calculators; close to tax filing | 1 in 6
- Google Takeout photo fixer | killed | Won't run in a browser tab at that size | 1 in 6
- Bank file formats (BAI2, MT940) to Excel | killed | Free converters | 1 in 6
- Court e-filing PDF fixer | killed | Needs a server; buyer already has Adobe | 1 in 6
- A 2025 clone of the bank statement converter has 17,000 visitors a month and $1 of revenue: traffic alone doesn't convert on a new domain.

### Marketers and SEO
- Negative keyword finder, AI-traffic report, redirect map builder, keyword clustering, llms.txt generator, ad copy bulk editor | all killed | Several free tools each, plus ChatGPT | 0 to 1 in 6

### Landlords and property
- Airbnb payout file to per-property profit | killed | Three small tools with free tiers | 1 in 6
- Lender-ready financial statement | killed | One seller at $79; rare buyer; needs a paid bank link | 1 in 6
- Inspection report to repair request | killed | Sold at $29 a report; needs a paid AI model | 1 in 6
- Rent ledgers, condition reports, utility splits | killed | Free from the big landlord apps | 0 to 1 in 6

### Proof hunt: who actually got 100 paying customers fast?
- SuperX (650 customers at launch) | evidence | Founder built 40K followers first | n/a
- SoloPush (60+ customers in 19 days) | evidence | Sold to makers through Reddit and X posts | n/a
- RankInPublic | evidence | Audience first; under $300 a month for a long stretch | n/a
- $9 invoice tool, zero audience | evidence of failure | $0 by day 4 | n/a
- Reply helper for Reddit help threads | liked as a lead only | Aims at a channel that has worked, but no proof anyone pays and ChatGPT does it | 1.5 in 6

---

## What both rounds say

1. **No idea and no channel cleared the bar.** 30 scouts across three rounds, about 150 ideas and 12 channels, best odds 1.5 in 6.
2. **The products are not the problem.** People pay for many of these jobs. What fails every time is getting in front of about 7,000 to 8,000 likely buyers in 30 days from a standing start.
3. **Every fast winner found had one of three things:** an audience built first, ad money, or months of search ranking.
4. **Self-reported wins need a second source.** The best-looking case in round 1 fell apart when the same founder's other write-up was read.

## Earlier today (before the bar was set)

- Planner Press (built) | 1 in 6 for 10 customers by its scout | Cody ruled planners out afterwards: too much free.
- Our Crossword (built) | four competitors including one free.
- ProSal Ledger (built) | almost no search demand; reached through groups and email.
- Cook-off voting page, pinewood derby manager, scan-to-pay sign, funeral program, treasure hunt maker | not built | weak evidence, free alternatives.
