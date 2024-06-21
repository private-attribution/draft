alter table queries alter created_at type timestamptz using created_at at time zone 'utc';
alter table queries alter started_at type timestamptz using started_at at time zone 'utc';
alter table queries alter ended_at type timestamptz using ended_at at time zone 'utc';

alter table helper_parties alter created_at type timestamptz using created_at at time zone 'utc';
alter table helper_parties alter modified_at type timestamptz using modified_at at time zone 'utc';

alter table helper_party_networks alter created_at type timestamptz using created_at at time zone 'utc';
alter table helper_party_networks alter modified_at type timestamptz using modified_at at time zone 'utc';

alter table helper_party_network_members alter created_at type timestamptz using created_at at time zone 'utc';

alter table helper_party_query_status_updates alter started_at type timestamptz using started_at at time zone 'utc';

alter table helper_party_api_keys alter created_at type timestamptz using created_at at time zone 'utc';
alter table helper_party_api_keys alter expires_at type timestamptz using expires_at at time zone 'utc';
alter table helper_party_api_keys alter modified_at type timestamptz using modified_at at time zone 'utc';
