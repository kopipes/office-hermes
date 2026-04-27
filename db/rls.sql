-- Provaliant Brain OS - RLS bootstrap
-- Note: app should set `app.user_role` and `app.business_unit_id` session vars.

alter table projects enable row level security;
alter table budgets enable row level security;
alter table budget_items enable row level security;
alter table ratecards enable row level security;
alter table documents enable row level security;
alter table wiki_pages enable row level security;
alter table action_items enable row level security;

-- Founder/director full read.
drop policy if exists projects_read_privileged on projects;
create policy projects_read_privileged on projects
for select
using (coalesce(current_setting('app.user_role', true), '') in ('founder', 'director'));

drop policy if exists budgets_read_privileged on budgets;
create policy budgets_read_privileged on budgets
for select
using (coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'finance'));

drop policy if exists budget_items_read_privileged on budget_items;
create policy budget_items_read_privileged on budget_items
for select
using (coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'finance'));

drop policy if exists ratecards_read_manager on ratecards;
create policy ratecards_read_manager on ratecards
for select
using (coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'manager', 'operations', 'finance'));

drop policy if exists documents_read_internal on documents;
create policy documents_read_internal on documents
for select
using (
  confidentiality in ('public', 'internal')
  or coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'manager', 'finance', 'operations')
);

drop policy if exists wiki_pages_read_approved on wiki_pages;
create policy wiki_pages_read_approved on wiki_pages
for select
using (approval_status = 'approved' or coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'manager'));

drop policy if exists action_items_read_scope on action_items;
create policy action_items_read_scope on action_items
for select
using (
  owner_id::text = coalesce(current_setting('app.user_id', true), '')
  or coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'manager')
);

-- Write policy placeholders (restricted to privileged roles).
drop policy if exists projects_write_privileged on projects;
create policy projects_write_privileged on projects
for all
using (coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'manager'))
with check (coalesce(current_setting('app.user_role', true), '') in ('founder', 'director', 'manager'));
