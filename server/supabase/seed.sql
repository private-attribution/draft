--
-- Data for Name: users; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

INSERT INTO auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, invited_at, confirmation_token, confirmation_sent_at, recovery_token, recovery_sent_at, email_change_token_new, email_change, email_change_sent_at, last_sign_in_at, raw_app_meta_data, raw_user_meta_data, is_super_admin, created_at, updated_at, phone, phone_confirmed_at, phone_change, phone_change_token, phone_change_sent_at, email_change_token_current, email_change_confirm_status, banned_until, reauthentication_token, reauthentication_sent_at, is_sso_user, deleted_at, is_anonymous) VALUES ('00000000-0000-0000-0000-000000000000', '547cc447-046e-4eb9-9f1a-3ccf2ff61f4d', 'authenticated', 'authenticated', 'demo@draft.test', '$2a$10$wsNGVOHGOr1cIlo61ZmZB.u3jccbX.YPSN0P8g/dPDxfOtFFjAwvy', '2024-06-05 19:04:10.138363+00', NULL, '', NULL, '', NULL, '', '', NULL, '2024-06-05 19:09:51.248495+00', '{"provider": "email", "providers": ["email"]}', '{}', NULL, '2024-06-05 19:04:10.134596+00', '2024-06-05 19:09:51.251084+00', NULL, NULL, '', '', NULL, '', 0, NULL, '', NULL, false, NULL, false);


--
-- Data for Name: identities; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

INSERT INTO auth.identities (provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at, id) VALUES ('547cc447-046e-4eb9-9f1a-3ccf2ff61f4d', '547cc447-046e-4eb9-9f1a-3ccf2ff61f4d', '{"sub": "547cc447-046e-4eb9-9f1a-3ccf2ff61f4d", "email": "demo@draft.test", "email_verified": false, "phone_verified": false}', 'email', '2024-06-05 19:04:10.136163+00', '2024-06-05 19:04:10.136185+00', '2024-06-05 19:04:10.136185+00', '9db62519-e822-42ec-b2ed-6c7e18f2915a');
