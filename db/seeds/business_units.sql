insert into business_units (name, corporate_group, description, status)
values
  ('Premium', 'Provaliant Group', 'Premium and flagship business operations', 'active'),
  ('Sports', 'Provaliant Group', 'Sports activation and partnerships', 'active'),
  ('Retail', 'Provaliant Group', 'Retail execution and mall projects', 'active'),
  ('Starlight', 'Provaliant Group', 'Creative and entertainment unit', 'active'),
  ('Futurevast', 'Provaliant Group', 'Growth and strategic initiatives', 'active'),
  ('Event', 'Provaliant Group', 'Event production and operations', 'active'),
  ('Studios', 'Provaliant Group', 'Studio and design production', 'active'),
  ('Finance', 'Provaliant Group', 'Finance and control tower', 'active'),
  ('Operations', 'Provaliant Group', 'Procurement and operational excellence', 'active'),
  ('Commerce', 'Provaliant Group', 'Sales and pipeline management', 'active'),
  ('Creative', 'Provaliant Group', 'Creative strategy and design', 'active')
on conflict (name) do nothing;
