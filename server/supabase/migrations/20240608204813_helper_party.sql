create table
helper_parties (
uuid uuid default gen_random_uuid() primary key,
display_name varchar(255) unique not null,
created_at timestamp default current_timestamp not null,
modified_at timestamp default current_timestamp not null
);

alter table helper_parties enable row level security;

create policy "Helper Parties are visible to authenticated users"
on helper_parties for select
to authenticated
using ( true );

create policy "Helper Parties are only created by authenticated users"
on helper_parties for insert
to authenticated
with check ( true );

create policy "Helper Parties are only updated by authenticated users"
on helper_parties for update
to authenticated
using ( true )
with check ( true );

create table
helper_party_networks (
uuid uuid default gen_random_uuid() primary key,
display_name varchar(255) unique not null,
created_at timestamp default current_timestamp not null,
modified_at timestamp default current_timestamp not null
);

alter table helper_party_networks enable row level security;

create policy "Helper Party Networks are visible to authenticated users"
on helper_party_networks for select
to authenticated
using ( true );

create policy "Helper Party Networks are only created by authenticated users"
on helper_party_networks for insert
to authenticated
with check ( true );

create policy "Helper Party Networks are only updated by authenticated users"
on helper_party_networks for update
to authenticated
using ( true )
with check ( true );

create table
helper_party_network_members (
helper_party_uuid uuid references helper_parties not null,
helper_party_network_uuid uuid references helper_party_networks not null,
created_at timestamp default current_timestamp not null,
primary key (helper_party_uuid, helper_party_network_uuid)
);

alter table helper_party_network_members enable row level security;

create policy "Helper Party Network Members are visible to authenticated users"
on helper_party_network_members for select
to authenticated
using ( true );

create policy "Helper Party Network Members are only created by authenticated users"
on helper_party_network_members for insert
to authenticated
with check ( true );

create policy "Helper Party Network Members are only updated by authenticated users"
on helper_party_network_members for update
to authenticated
using ( true )
with check ( true );
