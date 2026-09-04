-- RunBait users table
-- Run this once in your Supabase SQL Editor (https://supabase.com/dashboard → SQL Editor)

create table if not exists users (
  id              uuid primary key default gen_random_uuid(),
  github_id       bigint unique not null,
  email           text,
  name            text,
  avatar_url      text,
  github_login    text,
  -- The OAuth access token — used to call GitHub APIs on behalf of the user
  -- (repo access, GitHub Actions, etc.)
  github_access_token text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

-- Auto-update updated_at on row changes
create or replace function update_updated_at_column()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace trigger users_updated_at
  before update on users
  for each row execute procedure update_updated_at_column();

-- Index for fast lookups by github_id
create index if not exists idx_users_github_id on users(github_id);
