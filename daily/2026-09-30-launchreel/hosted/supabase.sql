-- Monthly AI usage per license key (the key is stored only as a hash).
create table if not exists launchreel_ai_usage (
  key_hash text not null,
  month text not null,
  count int not null default 0,
  primary key (key_hash, month)
);
alter table launchreel_ai_usage enable row level security; -- no public access at all; only the service role uses it

-- Adds one use if under the cap and returns the new count; returns null when the cap is reached.
create or replace function launchreel_use_ai(p_key text, p_month text, p_cap int)
returns int language plpgsql security definer set search_path = public as $$
declare n int;
begin
  insert into launchreel_ai_usage (key_hash, month, count) values (p_key, p_month, 1)
  on conflict (key_hash, month) do update set count = launchreel_ai_usage.count + 1
    where launchreel_ai_usage.count < p_cap
  returning count into n;
  return n;
end $$;
revoke all on function launchreel_use_ai(text, text, int) from public, anon, authenticated;
