create table
helper_party_query_status_updates (
uuid uuid default gen_random_uuid() primary key,
query_uuid uuid references queries not null,
helper_party_uuid uuid references helper_parties not null,
status status not null,
started_at timestamp default current_timestamp not null
);

alter table helper_party_query_status_updates enable row level security;

create policy "Helper Party Query Status Updates are visible to authenticated users"
on helper_party_query_status_updates for select
to authenticated
using ( true );

create policy "Helper Party Query Status Updates are only created by authenticated users"
on helper_party_query_status_updates for insert
to authenticated
with check ( true );

create policy "Helper Party Query Status Updates are only updated by authenticated users"
on helper_party_query_status_updates for update
to authenticated
using ( true )
with check ( true );
