create table
helper_party_api_keys (
uuid uuid default gen_random_uuid() primary key,
helper_party_uuid uuid references helper_parties not null,
hashed_api_key text not null,
created_at timestamp default current_timestamp not null,
expires_at timestamp default current_timestamp + interval '1 year' not null,
modified_at timestamp default null,
modified_reason text default null
);

alter table helper_party_api_keys enable row level security;

-- do not add any authenticated access to api_keys, require service_role and handle in application
