-- Supabase Free プランの自動一時停止（無アクセス7日）対策。
-- keepalive.sh がこの1行テーブルを毎回 update して、読みだけでなく書き込みの活動も残す。
create table if not exists public.ops_keepalive (
  id smallint primary key default 1,
  pinged_at timestamptz not null default now(),
  constraint ops_keepalive_single_row check (id = 1)
);

alter table public.ops_keepalive enable row level security;

insert into public.ops_keepalive (id, pinged_at)
values (1, now())
on conflict (id) do nothing;
