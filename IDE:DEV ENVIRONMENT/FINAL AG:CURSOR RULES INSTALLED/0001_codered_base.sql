-- 0001_codered_base.sql
-- Base schema for antigravityCodeRed / CodeRed brain
-- This migration creates the core codered schema, tables, and indexes.

-- Extensions (Supabase/Postgres)
create extension if not exists "pgcrypto";
create extension if not exists "uuid-ossp";
create extension if not exists "vector";

-- Schema
create schema if not exists codered;

-- ============================================================
-- 1. Core Project & Org Tables
-- ============================================================

create table if not exists codered.orgs (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists codered.projects (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text,
  status text not null default 'active', -- active, paused, archived
  owner_user_id uuid, -- reserved for future multi-tenant
  org_id uuid references codered.orgs(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============================================================
-- 2. Milestones, Tasks, Task Runs
-- ============================================================

create table if not exists codered.milestones (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  name text not null,
  description text,
  status text not null default 'not_started', -- not_started, in_progress, ready_for_cynic, shipped
  progress_percent integer not null default 0 check (progress_percent between 0 and 100),
  target_date date,
  actual_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists codered.agents (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  slug text not null unique,
  description text,
  role text not null, -- architect, code, test, review, infra, safety, orchestrator, cynic, research, librarian
  allowed_zones text[] not null default '{}'::text[], -- ['red','yellow','green']
  default_model text,
  max_tokens integer,
  temperature numeric,
  cost_ceiling_usd numeric,
  long_horizon_allowed boolean not null default false,
  config_yaml_path text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists codered.tasks (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  milestone_id uuid references codered.milestones(id) on delete set null,
  parent_task_id uuid references codered.tasks(id) on delete set null,
  title text not null,
  description text,
  zone text not null default 'green', -- red, yellow, green
  impact_axes text[] not null default '{}'::text[], -- subset of ['A','B','C','D','E']
  size text not null default 'm', -- xs, s, m, l, xl
  status text not null default 'backlog', -- backlog, in_progress, blocked, ready_for_review, done
  assignee_agent_id uuid references codered.agents(id) on delete set null,
  assignee_human text,
  priority integer,
  due_date timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists codered.agent_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  agent_id uuid not null references codered.agents(id) on delete restrict,
  task_id uuid references codered.tasks(id) on delete set null,
  mode text not null, -- architect, code, test, review, infra, safety, cynic, orchestrator, research, etc.
  input_summary text,
  output_summary text,
  full_input text,
  full_output text,
  model text,
  tokens_prompt integer,
  tokens_completion integer,
  approx_cost_usd numeric,
  zones_touched text[] not null default '{}'::text[],
  tools_used text[] not null default '{}'::text[],
  rag_documents uuid[] not null default '{}'::uuid[], -- references codered.documents(id)
  status text not null default 'succeeded', -- succeeded, failed, aborted
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists codered.task_runs (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references codered.tasks(id) on delete cascade,
  project_id uuid not null references codered.projects(id) on delete cascade,
  agent_run_id uuid references codered.agent_runs(id) on delete set null,
  phase text not null, -- architect, code, test, review, infra, safety, cynic, orchestrator
  status text not null default 'planned', -- planned, running, succeeded, failed, skipped
  summary text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Indexes for core tables
create index if not exists idx_codered_tasks_project on codered.tasks(project_id);
create index if not exists idx_codered_tasks_milestone on codered.tasks(milestone_id);
create index if not exists idx_codered_task_runs_task on codered.task_runs(task_id);
create index if not exists idx_codered_agent_runs_project on codered.agent_runs(project_id);

-- ============================================================
-- 3. CI Events, Deployments, Errors
-- ============================================================

create table if not exists codered.ci_events (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  provider text not null, -- github-actions, etc.
  workflow_name text,
  run_id text, -- external id
  branch text,
  commit_sha text,
  status text not null, -- queued, running, succeeded, failed, canceled
  trigger text, -- push, pull_request, manual
  zones_touched text[] not null default '{}'::text[],
  start_time timestamptz,
  end_time timestamptz,
  duration_seconds integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_ci_events_project on codered.ci_events(project_id);

create table if not exists codered.deployments (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  provider text not null, -- vercel, other
  environment text not null, -- dev, staging, prod
  deployment_id text, -- external id
  ci_event_id uuid references codered.ci_events(id) on delete set null,
  status text not null default 'pending', -- pending, succeeded, failed, rolled_back
  url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_deployments_project on codered.deployments(project_id);

create table if not exists codered.errors (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  source text not null, -- ci, deployment, agent, runtime
  ci_event_id uuid references codered.ci_events(id) on delete set null,
  deployment_id uuid references codered.deployments(id) on delete set null,
  agent_run_id uuid references codered.agent_runs(id) on delete set null,
  error_code text,
  message text,
  details text,
  severity text not null default 'error', -- info, warning, error, critical
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_errors_project on codered.errors(project_id);

-- ============================================================
-- 4. RAG: Corpora, Documents, Chunks, Embeddings
-- ============================================================

create table if not exists codered.corpora (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references codered.projects(id) on delete cascade,
  name text not null,
  description text,
  domain_tags text[] not null default '{}'::text[],
  risk_level text not null default 'safe', -- safe, internal, legal_critical
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists codered.documents (
  id uuid primary key default gen_random_uuid(),
  corpus_id uuid not null references codered.corpora(id) on delete cascade,
  project_id uuid references codered.projects(id) on delete cascade,
  title text not null,
  source_path text,
  version text,
  domain_tags text[] not null default '{}'::text[],
  risk_level text not null default 'safe', -- safe, internal, legal_critical
  is_pinned boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_documents_corpus on codered.documents(corpus_id);
create index if not exists idx_codered_documents_project on codered.documents(project_id);

create table if not exists codered.chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references codered.documents(id) on delete cascade,
  project_id uuid references codered.projects(id) on delete cascade,
  chunk_index integer not null,
  content text not null,
  token_count integer,
  embedding_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_chunks_document on codered.chunks(document_id);

-- Embeddings using pgvector (change dimension if needed)
create table if not exists codered.embeddings (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references codered.projects(id) on delete cascade,
  document_id uuid not null references codered.documents(id) on delete cascade,
  chunk_id uuid not null references codered.chunks(id) on delete cascade,
  embedding vector(1536) not null,
  model text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Link chunks to embeddings (optional, not enforced by FK to avoid circular dependency)
alter table codered.chunks
  add constraint if not exists chunks_embedding_id_fk
  foreign key (embedding_id) references codered.embeddings(id) on delete set null;

create index if not exists idx_codered_embeddings_project_doc_chunk
  on codered.embeddings(project_id, document_id, chunk_id);

-- Vector index (requires ANALYZE tuning; can be adjusted later)
create index if not exists idx_codered_embeddings_vector
  on codered.embeddings using ivfflat (embedding vector_l2_ops)
  with (lists = 100);

-- ============================================================
-- 5. Learning & Feedback
-- ============================================================

create table if not exists codered.lessons (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  title text not null,
  description text,
  domain_tags text[] not null default '{}'::text[],
  source_type text not null, -- agent_run, ci_event, retro, manual
  source_id uuid,
  impact_axes text[] not null default '{}'::text[], -- subset of ['A','B','C','D','E']
  severity text not null default 'minor', -- minor, moderate, major, critical
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_lessons_project on codered.lessons(project_id);

create table if not exists codered.bug_patterns (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  name text not null,
  description text,
  pattern_signature text,
  root_cause text,
  recommended_fix text,
  related_lessons uuid[] not null default '{}'::uuid[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_bug_patterns_project on codered.bug_patterns(project_id);

create table if not exists codered.decisions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  title text not null,
  description text,
  domain text not null, -- legal, infra, ux, marketing, etc.
  decision_type text not null, -- architecture, policy, legal_strategy, product
  rationale text,
  options_considered text,
  chosen_option text,
  decision_maker text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_decisions_project on codered.decisions(project_id);

-- ============================================================
-- 6. UX Snippets
-- ============================================================

create table if not exists codered.ux_snippets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references codered.projects(id) on delete cascade,
  name text not null,
  description text,
  tech_stack text[] not null default '{}'::text[], -- e.g. ['nextjs','tailwind']
  code_sample text,
  preview_url text,
  tags text[] not null default '{}'::text[],
  quality_score numeric,
  approved_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_ux_snippets_project on codered.ux_snippets(project_id);

-- ============================================================
-- 7. User Overrides (Governance)
-- ============================================================

create table if not exists codered.user_overrides (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references codered.projects(id) on delete cascade,
  "user" text not null,
  override_type text not null, -- cynic_reject, deploy_anyway, agent_override, etc.
  target_type text not null, -- agent_run, ci_event, deployment, task
  target_id uuid,
  reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_codered_user_overrides_project on codered.user_overrides(project_id);

-- ============================================================
-- 8. Timestamps Maintenance (Optional)
-- ============================================================
-- You may later add triggers to auto-update updated_at on row changes.
-- For MVP, we rely on application-side updates where necessary.

