insert into roles (role_name, access_level, permissions)
values
  ('founder', 'system', '{"all": true}'::jsonb),
  ('director', 'organization', '{"read": ["*"], "write": ["projects","reports","wiki_pages"]}'::jsonb),
  ('bu_head', 'business_unit', '{"read": ["projects","budgets","vendors","wiki_pages"], "write": ["project_updates","action_items"]}'::jsonb),
  ('manager', 'project', '{"read": ["projects","vendors","wiki_pages","action_items"], "write": ["project_updates","meetings","action_items"]}'::jsonb),
  ('supervisor', 'execution', '{"read": ["projects","action_items"], "write": ["project_updates","meetings"]}'::jsonb),
  ('staff', 'limited', '{"read": ["projects","action_items"], "write": ["project_updates"]}'::jsonb),
  ('donna_agent', 'system_agent', '{"read": ["*"], "write": ["project_updates","meetings","action_items","wiki_change_requests"]}'::jsonb)
on conflict (role_name) do nothing;
