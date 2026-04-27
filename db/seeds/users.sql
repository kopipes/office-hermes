-- Optional starter users (replace with real IDs and contact data)
insert into users (full_name, email, role_id, business_unit_id, status)
select
  'Donna System Agent',
  'donna@provaliant.internal',
  r.id,
  b.id,
  'active'
from roles r
cross join business_units b
where r.role_name = 'donna_agent'
  and b.name = 'Operations'
on conflict (email) do nothing;
