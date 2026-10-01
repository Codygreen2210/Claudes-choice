-- Spendlog tables. Run once in the Supabase SQL editor.
-- Prefixed sl_ so they can share a project with Misslog (ml_) on the free plan.
-- RLS on with no policies + revoked: only the server's service role key can touch them.
create table if not exists sl_users (
  id uuid primary key default gen_random_uuid(),
  key text unique not null,
  handle text unique not null,
  created_at timestamptz not null default now()
);
create table if not exists sl_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references sl_users(id) on delete cascade,
  kind text not null check (kind in ('expense', 'income')),
  cents bigint not null check (cents > 0 and cents <= 1000000000),
  category text not null,
  note text not null default '',
  day text not null check (day ~ '^\d{4}-\d{2}-\d{2}$'),
  created_at timestamptz not null default now()
);
create index if not exists sl_entries_user_day on sl_entries(user_id, day desc);
create table if not exists sl_budgets (
  user_id uuid not null references sl_users(id) on delete cascade,
  category text not null,
  cents bigint not null check (cents > 0),
  primary key (user_id, category)
);
create table if not exists sl_oauth (
  kind text not null,
  id text not null,
  data jsonb not null,
  expires_at timestamptz not null,
  primary key (kind, id)
);
alter table sl_users enable row level security;
alter table sl_entries enable row level security;
alter table sl_budgets enable row level security;
alter table sl_oauth enable row level security;
revoke all on sl_users, sl_entries, sl_budgets, sl_oauth from anon, authenticated;
