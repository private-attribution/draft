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

INSERT INTO public.helper_party_api_keys (uuid, helper_party_uuid, hashed_api_key) VALUES ('13d80a42-4b40-4987-a338-b394674ab399', 'de218b52-1ec7-4a4d-9bf9-f9070b2c3a93', '$2b$10$p7/VcbCbxS5plmM0ECSHJOuG37D9ZhvW.E0x0j90vtcgcAxRn3tby');
INSERT INTO public.helper_party_api_keys (uuid, helper_party_uuid, hashed_api_key) VALUES ('1d61b974-7ac8-4baa-b0b0-a83cd29c46e2', 'b8848f0f-65c4-499f-82b4-1e3a119ba31e', '$2b$10$ZXftUXa6xjjSB9epo5gIyOSYsJc3pNm9GotKjuYyGHSoXf3OcSNSO');
INSERT INTO public.helper_party_api_keys (uuid, helper_party_uuid, hashed_api_key) VALUES ('31c229e3-8150-4f9b-91e6-ac413198f4ff', '91993b4a-4131-4b9f-a132-d4a5839e3c6c', '$2b$10$ouTo4otPRPZ/cCaQKgCqxeS449DqfrKxBe7F33ewuvHMX9dagSuCe');

--
-- Data for Name: queries; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.queries (uuid, display_id, type, status) VALUES ('0e067bd3-b93a-4a17-ab51-d5d042181c5f', '__test__query_for_testing', 'IPA', 'QUEUED');
