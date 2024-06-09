--
-- Data for Name: helper_parties; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.helper_parties (uuid, display_name, created_at) VALUES ('de218b52-1ec7-4a4d-9bf9-f9070b2c3a93', 'Local test helper 1', '2024-06-05 20:37:32.472191');
INSERT INTO public.helper_parties (uuid, display_name, created_at) VALUES ('b8848f0f-65c4-499f-82b4-1e3a119ba31e', 'Local test helper 2', '2024-06-05 20:37:45.47656');
INSERT INTO public.helper_parties (uuid, display_name, created_at) VALUES ('91993b4a-4131-4b9f-a132-d4a5839e3c6c', 'Local test helper 3', '2024-06-05 20:37:53.375326');


--
-- Data for Name: helper_party_networks; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.helper_party_networks (uuid, display_name, size, created_at) VALUES ('a8c892ae-8cee-472f-95f0-e25b1fec9759', 'Local test network', 3, '2024-06-05 20:38:40.956239');

--
-- Data for Name: helper_party_network_members; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.helper_party_network_members (helper_party_uuid, helper_party_network_uuid, created_at) VALUES ('de218b52-1ec7-4a4d-9bf9-f9070b2c3a93', 'a8c892ae-8cee-472f-95f0-e25b1fec9759', '2024-06-05 20:39:01.362579');
INSERT INTO public.helper_party_network_members (helper_party_uuid, helper_party_network_uuid, created_at) VALUES ('b8848f0f-65c4-499f-82b4-1e3a119ba31e', 'a8c892ae-8cee-472f-95f0-e25b1fec9759', '2024-06-05 20:39:10.502079');
INSERT INTO public.helper_party_network_members (helper_party_uuid, helper_party_network_uuid, created_at) VALUES ('91993b4a-4131-4b9f-a132-d4a5839e3c6c', 'a8c892ae-8cee-472f-95f0-e25b1fec9759', '2024-06-05 20:39:24.703602');
