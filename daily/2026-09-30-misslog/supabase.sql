-- Misslog tables. Run once in the Supabase SQL editor.
-- Only the server (service role) touches these. RLS is on with no policies, and the views are
-- revoked from anon/authenticated, so the public API key can't read anything.

create table if not exists ml_users (
  id uuid primary key default gen_random_uuid(),
  key text unique not null,
  handle text unique not null,
  public boolean not null default false,
  share_data boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists ml_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references ml_users(id) on delete cascade,
  type text not null check (type in ('miss', 'search')),
  model text not null,
  family text not null,
  client text not null default '',
  kind text,
  trying_to text,
  ask text,
  mistake text,
  fix text,
  topic text,
  searches int,
  tokens int not null default 0 check (tokens between 0 and 200000),
  dollars numeric(10,4) not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists ml_events_user on ml_events(user_id, created_at desc);
create index if not exists ml_events_family on ml_events(family);

alter table ml_users enable row level security;
alter table ml_events enable row level security;

-- Leaderboard per AI family (same math as lib/game.ts board()).
create or replace view ml_board as
select family,
  count(*) filter (where type = 'miss')::int as misses,
  count(*) filter (where type = 'miss' and fix is not null and fix <> '')::int as fixed,
  coalesce(sum(tokens) filter (where type = 'miss'), 0)::int as tokens,
  coalesce(sum(dollars) filter (where type = 'miss'), 0)::float as dollars,
  coalesce(sum(coalesce(searches, 1)) filter (where type = 'search'), 0)::int as searches,
  count(distinct user_id)::int as people
from ml_events group by family
order by (count(*) filter (where type = 'miss' and fix is not null and fix <> ''))::float / nullif(count(*) filter (where type = 'miss'), 0) desc nulls last,
  coalesce(sum(tokens) filter (where type = 'miss'), 0)::float / nullif(count(*) filter (where type = 'miss'), 0) asc nulls last;

-- Recent mistakes from people who made their profile public.
create or replace view ml_public_feed as
select e.*, u.handle from ml_events e join ml_users u on u.id = e.user_id
where u.public and e.type = 'miss' order by e.created_at desc;

revoke all on ml_users, ml_events, ml_board, ml_public_feed from anon, authenticated;
