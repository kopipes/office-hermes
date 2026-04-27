-- Provaliant Brain OS - Base Schema

create extension if not exists pgcrypto;
create extension if not exists vector;

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Identity and Access
create table if not exists roles (
  id uuid primary key default gen_random_uuid(),
  role_name text not null unique,
  access_level text not null,
  permissions jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists business_units (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  corporate_group text,
  director_id uuid,
  bu_head_id uuid,
  description text,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  email text unique,
  phone text,
  telegram_id text,
  whatsapp_id text,
  role_id uuid references roles(id),
  business_unit_id uuid references business_units(id),
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- director_id and bu_head_id are intentionally kept as UUID references
-- without hard FK constraints to keep schema bootstrap idempotent.

create table if not exists role_permissions (
  id uuid primary key default gen_random_uuid(),
  role_id uuid not null references roles(id) on delete cascade,
  table_name text not null,
  action text not null,
  classification_max text not null default 'internal',
  allow boolean not null default true,
  created_at timestamptz not null default now(),
  unique(role_id, table_name, action)
);

-- Knowledge sources
create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  source_type text not null,
  source_name text,
  channel_name text,
  group_name text,
  sender_name text,
  sender_identifier text,
  raw_reference text,
  imported_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists entities (
  id uuid primary key default gen_random_uuid(),
  entity_type text not null,
  name text not null,
  display_name text not null,
  aliases text[] not null default '{}',
  description text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(entity_type, name)
);

create table if not exists clients (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references entities(id) on delete cascade,
  client_type text,
  industry text,
  tier text,
  account_owner_id uuid references users(id),
  relationship_status text,
  last_contact_date date,
  next_followup_date date,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(entity_id)
);

create table if not exists vendors (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid not null references entities(id) on delete cascade,
  vendor_category text,
  service_area text,
  contact_person text,
  phone text,
  email text,
  reliability_score numeric,
  quality_score numeric,
  speed_score numeric,
  payment_terms text,
  blacklist_flag boolean not null default false,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(entity_id)
);

create table if not exists contacts (
  id uuid primary key default gen_random_uuid(),
  entity_id uuid references entities(id),
  client_id uuid references clients(id) on delete set null,
  full_name text not null,
  position text,
  company text,
  phone text,
  email text,
  whatsapp text,
  telegram text,
  relationship_owner_id uuid references users(id),
  notes text,
  confidentiality text not null default 'internal',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  project_code text unique,
  project_name text not null,
  client_id uuid references clients(id),
  business_unit_id uuid references business_units(id),
  project_owner_id uuid references users(id),
  project_manager_id uuid references users(id),
  pm_provaliant_id text,
  status text not null default 'active',
  start_date date,
  end_date date,
  budget_total numeric,
  actual_cost numeric,
  revenue numeric,
  gross_margin numeric,
  gross_margin_percent numeric,
  risk_level text,
  gdrive_folder_url text,
  latest_summary text,
  last_updated timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references sources(id) on delete set null,
  document_type text not null,
  title text,
  original_filename text,
  source_path text,
  gdrive_url text,
  project_id uuid references projects(id) on delete set null,
  client_id uuid references clients(id) on delete set null,
  business_unit_id uuid references business_units(id) on delete set null,
  owner_id uuid references users(id) on delete set null,
  confidentiality text not null default 'internal',
  status text not null default 'active',
  effective_date date,
  checksum text unique,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  imported_at timestamptz not null default now()
);

create table if not exists chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references documents(id) on delete cascade,
  chunk_index int not null,
  content text not null,
  content_hash text,
  embedding vector(1536),
  page_number int,
  section_title text,
  created_at timestamptz not null default now(),
  unique(document_id, chunk_index)
);

create table if not exists drive_links (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id) on delete cascade,
  client_id uuid references clients(id) on delete set null,
  document_id uuid references documents(id) on delete set null,
  drive_url text not null,
  title text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists project_updates (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  update_date timestamptz not null,
  update_type text,
  status text,
  summary text,
  blockers text,
  next_steps text,
  submitted_by uuid references users(id),
  source_id uuid references sources(id),
  confidence numeric,
  created_at timestamptz not null default now()
);

create table if not exists ratecards (
  id uuid primary key default gen_random_uuid(),
  vendor_id uuid not null references vendors(id) on delete cascade,
  item_name text not null,
  item_category text,
  unit text,
  internal_price numeric,
  external_price numeric,
  minimum_order numeric,
  lead_time_days int,
  valid_from date,
  valid_until date,
  source_document_id uuid references documents(id),
  approval_status text not null default 'pending_review',
  created_by uuid references users(id),
  approved_by uuid references users(id),
  approved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists budgets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  budget_version text not null,
  budget_status text not null default 'draft',
  total_internal numeric,
  total_external numeric,
  total_profit numeric,
  profit_percent numeric,
  source_document_id uuid references documents(id),
  created_by uuid references users(id),
  approved_by uuid references users(id),
  approved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(project_id, budget_version)
);

create table if not exists budget_items (
  id uuid primary key default gen_random_uuid(),
  budget_id uuid not null references budgets(id) on delete cascade,
  item_category text,
  item_name text not null,
  qty numeric,
  unit text,
  unit_cost numeric,
  internal_total numeric,
  external_total numeric,
  profit numeric,
  profit_percent numeric,
  vendor_id uuid references vendors(id),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists meetings (
  id uuid primary key default gen_random_uuid(),
  meeting_title text,
  meeting_date timestamptz,
  client_id uuid references clients(id),
  project_id uuid references projects(id),
  business_unit_id uuid references business_units(id),
  attendees text[] not null default '{}',
  source_document_id uuid references documents(id),
  summary text,
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists decisions (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid references meetings(id) on delete cascade,
  project_id uuid references projects(id) on delete set null,
  decision_text text not null,
  decision_owner_id uuid references users(id),
  decision_date date,
  impact text,
  confidence numeric,
  source_document_id uuid references documents(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists action_items (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid references meetings(id) on delete cascade,
  project_id uuid references projects(id) on delete set null,
  owner_id uuid references users(id),
  task_text text not null,
  due_date date,
  status text not null default 'open',
  priority text,
  source_id uuid references sources(id),
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists wiki_pages (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  title text not null,
  category text,
  content text,
  summary text,
  owner_id uuid references users(id),
  approval_status text not null default 'draft',
  source_document_ids uuid[] not null default '{}',
  related_entity_ids uuid[] not null default '{}',
  freshness_rule text,
  last_reviewed_at timestamptz,
  embedding vector(1536),
  version int not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists wiki_change_requests (
  id uuid primary key default gen_random_uuid(),
  wiki_page_id uuid references wiki_pages(id) on delete cascade,
  proposed_content text,
  change_reason text,
  proposed_by uuid references users(id),
  approval_status text not null default 'pending_review',
  reviewed_by uuid references users(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists wiki_page_entities (
  id uuid primary key default gen_random_uuid(),
  wiki_page_id uuid not null references wiki_pages(id) on delete cascade,
  entity_id uuid not null references entities(id) on delete cascade,
  relation_type text,
  created_at timestamptz not null default now(),
  unique(wiki_page_id, entity_id)
);

create table if not exists citations (
  id uuid primary key default gen_random_uuid(),
  source_type text not null,
  source_id uuid,
  chunk_id uuid references chunks(id) on delete set null,
  wiki_page_id uuid references wiki_pages(id) on delete set null,
  note text,
  created_at timestamptz not null default now()
);

create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  report_type text not null,
  title text,
  period_start date,
  period_end date,
  business_unit_id uuid references business_units(id),
  generated_by uuid references users(id),
  content text,
  source_refs jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists query_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id),
  query_text text,
  query_type text,
  tools_used text[] not null default '{}',
  rows_returned int,
  chunks_returned int,
  response_summary text,
  created_at timestamptz not null default now()
);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id),
  action_type text not null,
  table_name text not null,
  record_id uuid,
  previous_value jsonb,
  new_value jsonb,
  created_at timestamptz not null default now()
);

create table if not exists ingestion_jobs (
  id uuid primary key default gen_random_uuid(),
  source_type text not null,
  source_ref text,
  status text not null default 'queued',
  started_at timestamptz,
  finished_at timestamptz,
  error_message text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists gbrain_relationships (
  id uuid primary key default gen_random_uuid(),
  from_entity_id uuid not null references entities(id) on delete cascade,
  to_entity_id uuid not null references entities(id) on delete cascade,
  relation_type text not null,
  weight numeric,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(from_entity_id, to_entity_id, relation_type)
);

-- update triggers (idempotent)
drop trigger if exists trg_business_units_updated_at on business_units;
create trigger trg_business_units_updated_at before update on business_units for each row execute function set_updated_at();

drop trigger if exists trg_users_updated_at on users;
create trigger trg_users_updated_at before update on users for each row execute function set_updated_at();

drop trigger if exists trg_entities_updated_at on entities;
create trigger trg_entities_updated_at before update on entities for each row execute function set_updated_at();

drop trigger if exists trg_clients_updated_at on clients;
create trigger trg_clients_updated_at before update on clients for each row execute function set_updated_at();

drop trigger if exists trg_vendors_updated_at on vendors;
create trigger trg_vendors_updated_at before update on vendors for each row execute function set_updated_at();

drop trigger if exists trg_contacts_updated_at on contacts;
create trigger trg_contacts_updated_at before update on contacts for each row execute function set_updated_at();

drop trigger if exists trg_projects_updated_at on projects;
create trigger trg_projects_updated_at before update on projects for each row execute function set_updated_at();

drop trigger if exists trg_drive_links_updated_at on drive_links;
create trigger trg_drive_links_updated_at before update on drive_links for each row execute function set_updated_at();

drop trigger if exists trg_ratecards_updated_at on ratecards;
create trigger trg_ratecards_updated_at before update on ratecards for each row execute function set_updated_at();

drop trigger if exists trg_budgets_updated_at on budgets;
create trigger trg_budgets_updated_at before update on budgets for each row execute function set_updated_at();

drop trigger if exists trg_budget_items_updated_at on budget_items;
create trigger trg_budget_items_updated_at before update on budget_items for each row execute function set_updated_at();

drop trigger if exists trg_meetings_updated_at on meetings;
create trigger trg_meetings_updated_at before update on meetings for each row execute function set_updated_at();

drop trigger if exists trg_decisions_updated_at on decisions;
create trigger trg_decisions_updated_at before update on decisions for each row execute function set_updated_at();

drop trigger if exists trg_action_items_updated_at on action_items;
create trigger trg_action_items_updated_at before update on action_items for each row execute function set_updated_at();

drop trigger if exists trg_wiki_pages_updated_at on wiki_pages;
create trigger trg_wiki_pages_updated_at before update on wiki_pages for each row execute function set_updated_at();

drop trigger if exists trg_wiki_change_requests_updated_at on wiki_change_requests;
create trigger trg_wiki_change_requests_updated_at before update on wiki_change_requests for each row execute function set_updated_at();

drop trigger if exists trg_reports_updated_at on reports;
create trigger trg_reports_updated_at before update on reports for each row execute function set_updated_at();

drop trigger if exists trg_ingestion_jobs_updated_at on ingestion_jobs;
create trigger trg_ingestion_jobs_updated_at before update on ingestion_jobs for each row execute function set_updated_at();

drop trigger if exists trg_gbrain_relationships_updated_at on gbrain_relationships;
create trigger trg_gbrain_relationships_updated_at before update on gbrain_relationships for each row execute function set_updated_at();
