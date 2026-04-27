-- Provaliant Brain OS - Indexes

create index if not exists idx_projects_status on projects(status);
create index if not exists idx_projects_bu on projects(business_unit_id);
create index if not exists idx_projects_client on projects(client_id);
create index if not exists idx_projects_last_updated on projects(last_updated desc);

create index if not exists idx_documents_type on documents(document_type);
create index if not exists idx_documents_project on documents(project_id);
create index if not exists idx_documents_client on documents(client_id);
create index if not exists idx_documents_confidentiality on documents(confidentiality);
create index if not exists idx_documents_imported_at on documents(imported_at desc);

create index if not exists idx_ratecards_vendor on ratecards(vendor_id);
create index if not exists idx_ratecards_category on ratecards(item_category);
create index if not exists idx_ratecards_approval on ratecards(approval_status);

create index if not exists idx_budget_items_budget on budget_items(budget_id);
create index if not exists idx_budgets_project on budgets(project_id);
create index if not exists idx_budgets_status on budgets(budget_status);

create index if not exists idx_action_items_owner on action_items(owner_id);
create index if not exists idx_action_items_status on action_items(status);
create index if not exists idx_action_items_due_date on action_items(due_date);

create index if not exists idx_meetings_project on meetings(project_id);
create index if not exists idx_meetings_date on meetings(meeting_date desc);
create index if not exists idx_decisions_project on decisions(project_id);

create index if not exists idx_wiki_category on wiki_pages(category);
create index if not exists idx_wiki_approval on wiki_pages(approval_status);
create index if not exists idx_wiki_slug on wiki_pages(slug);

create index if not exists idx_query_logs_user on query_logs(user_id);
create index if not exists idx_query_logs_created_at on query_logs(created_at desc);
create index if not exists idx_audit_logs_table_record on audit_logs(table_name, record_id);
create index if not exists idx_audit_logs_created_at on audit_logs(created_at desc);

create index if not exists idx_gbrain_from on gbrain_relationships(from_entity_id);
create index if not exists idx_gbrain_to on gbrain_relationships(to_entity_id);
create index if not exists idx_gbrain_relation_type on gbrain_relationships(relation_type);

create index if not exists idx_chunks_embedding
on chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create index if not exists idx_wiki_embedding
on wiki_pages using ivfflat (embedding vector_cosine_ops) with (lists = 100);
