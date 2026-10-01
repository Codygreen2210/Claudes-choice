-- Whatcha Make: answers table. Run once in the Supabase SQL editor.
-- Prefixed wm_ so it can share the Misslog project on the free plan.
-- Sign-in uses Supabase Auth (auth.users). Only the server (service role) reads/writes answers.
create table if not exists wm_answers (
  user_id uuid primary key references auth.users(id) on delete cascade,
  occ text not null,
  area text not null,
  hourly numeric(7,2) not null check (hourly between 5 and 250),
  hours int not null check (hours between 1 and 80),
  ot_hours int not null default 0 check (ot_hours between 0 and 60),
  years int check (years between 0 and 60),
  updated_at timestamptz not null default now()
);
create index if not exists wm_answers_group on wm_answers(occ, area);
alter table wm_answers enable row level security;
revoke all on wm_answers from anon, authenticated;
