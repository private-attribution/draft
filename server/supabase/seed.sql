--
-- Data for Name: helper_parties; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.helper_parties (uuid, display_name) VALUES ('de218b52-1ec7-4a4d-9bf9-f9070b2c3a93', 'Local test helper 1');
INSERT INTO public.helper_parties (uuid, display_name) VALUES ('b8848f0f-65c4-499f-82b4-1e3a119ba31e', 'Local test helper 2');
INSERT INTO public.helper_parties (uuid, display_name) VALUES ('91993b4a-4131-4b9f-a132-d4a5839e3c6c', 'Local test helper 3');

--
-- Data for Name: helper_party_networks; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.helper_party_networks (uuid, display_name) VALUES ('a8c892ae-8cee-472f-95f0-e25b1fec9759', 'Local test network');

--
-- Data for Name: helper_party_network_members; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.helper_party_network_members (helper_party_uuid, helper_party_network_uuid) VALUES ('de218b52-1ec7-4a4d-9bf9-f9070b2c3a93', 'a8c892ae-8cee-472f-95f0-e25b1fec9759');
INSERT INTO public.helper_party_network_members (helper_party_uuid, helper_party_network_uuid) VALUES ('b8848f0f-65c4-499f-82b4-1e3a119ba31e', 'a8c892ae-8cee-472f-95f0-e25b1fec9759');
INSERT INTO public.helper_party_network_members (helper_party_uuid, helper_party_network_uuid) VALUES ('91993b4a-4131-4b9f-a132-d4a5839e3c6c', 'a8c892ae-8cee-472f-95f0-e25b1fec9759');

--
-- Data for Name: helper_party_api_keys; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.helper_party_api_keys (uuid, helper_party_uuid, hashed_api_key) VALUES ('13d80a42-4b40-4987-a338-b394674ab399', 'de218b52-1ec7-4a4d-9bf9-f9070b2c3a93', '243262243130244470514a2e527665766e57614a4f5835782f505a534f6a674f335866444737505178585851656e3866796e52467563516d66414547');
INSERT INTO public.helper_party_api_keys (uuid, helper_party_uuid, hashed_api_key) VALUES ('1d61b974-7ac8-4baa-b0b0-a83cd29c46e2', 'b8848f0f-65c4-499f-82b4-1e3a119ba31e', '243262243130247770623576564767534f61772f516441334a51734c2e7373494e3652714369355a554a414e2e7343796d4673394c475247584c5375');
INSERT INTO public.helper_party_api_keys (uuid, helper_party_uuid, hashed_api_key) VALUES ('31c229e3-8150-4f9b-91e6-ac413198f4ff', '91993b4a-4131-4b9f-a132-d4a5839e3c6c', '24326224313024724746664c3146614b4b6e68715169714e6b58573165485a37662f6d3857563271364a336845564139352e5746465677616b774d71');
