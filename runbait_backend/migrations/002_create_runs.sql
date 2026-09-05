-- RunBait runs table
-- Run this in your Supabase SQL Editor

create table if not exists runs (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references users(id) on delete cascade,
  repo            text not null,
  pr_number       int not null,
  status          text not null default 'pending',
  is_demo         boolean default false,
  start_command   text,
  install_command text,
  results         jsonb default '{}'::jsonb,
  error           text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

-- Auto-update updated_at on row changes
create or replace trigger runs_updated_at
  before update on runs
  for each row execute procedure update_updated_at_column();

-- Indexes
create index if not exists idx_runs_user_id on runs(user_id);
