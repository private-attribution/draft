create type status as enum ('QUEUED', 'STARTING', 'COMPILING', 'WAITING_TO_START', 'IN_PROGRESS', 'COMPLETE', 'KILLED', 'NOT_FOUND', 'CRASHED', 'UNKNOWN');

create type query_type as enum ('IPA', 'DEMO_LOGGER');

create table
queries (
uuid uuid default gen_random_uuid() primary key,
display_id varchar(255) unique not null,
type query_type not null,
status status not null,
params jsonb not null default '{}'::jsonb,
created_at timestamp default current_timestamp not null,
started_at timestamp,
ended_at timestamp
);

create index idx_display_id on queries (display_id);

alter table queries enable row level security;

create policy "Queries are visible to authenticated users"
on queries for select
to authenticated
using ( true );

create policy "Queries are only created by authenticated users"
on queries for insert
to authenticated
with check ( true );

create policy "Queries are only updated by authenticated users"
on queries for update
to authenticated
using ( true )
with check ( true );

create or replace function generate_unique_display_id(p_display_id varchar) returns varchar as $$
declare
    new_display_id varchar;
    suffix varchar;
begin
    new_display_id := p_display_id;
    suffix := ''; -- initialize the suffix as an empty string

    -- check if the initial short name exists
    while exists (select 1 from queries where display_id = new_display_id) loop
        -- if exists, append one digit at a time
        suffix := case when suffix = '' then '-' else suffix end || floor(random() * 10)::text;
        new_display_id := p_display_id || suffix;
    end loop;

    return new_display_id;
end;
$$ language plpgsql;
