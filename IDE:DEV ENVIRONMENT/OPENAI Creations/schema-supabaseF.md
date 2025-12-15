# Supabase Schema – antigravityCodeRed (Modules 1–2)

**File:** `docs/schema-supabase.md`  
**Scope:** Canonical schema for the CodeRed brain in Supabase, for Modules 1–2 only.

This document is the **single source of truth** for:

- Schema name and table names
- Columns, types, and keys
- Core relationships
- Indexes and constraints
- How this schema supports:
  - Tasks & orchestration
  - Agent runs & LLM usage
  - Tokens & cost
  - Learning & feedback
  - RAG v1 for Modules 1–2

SQL migrations must **not** contradict this file. If they do, this file should be updated first and then migrations generated from it.

---

## 1. Schema Overview

All core objects for Modules 1–2 live under the schema:

```sql
schema: codered
```

### 1.1 High-Level Entity Map

```text
projects
  └── tasks
        ├── task_runs
        ├── agent_runs
        ├── ci_events
        ├── deployments
        ├── errors
        └── long_runs / long_run_checkpoints (for long horizon)

agents
  └── agent_runs
        └── llm_usage_* aggregates

learning objects
  ├── lessons
  ├── bug_patterns
  └── decisions

RAG
  ├── doc_manifest
  └── doc_chunks

LLM routing & cost
  ├── llm_providers
  ├── llm_models
  ├── llm_usage_daily
  ├── llm_usage_by_agent
  └── llm_degradation_events

Overrides & safety
  └── user_overrides
```

---

## 2. Projects & Tasks

### 2.1 `codered.projects`

Represents a logical project that CodeRed helps manage (e.g. `antigravityCodeRed`).

**Columns (core):**

- `id` – `uuid` (PK, default `gen_random_uuid()`)
- `slug` – `text` (unique, e.g. `antigravity-codered`)
- `name` – `text`
- `description` – `text`
- `status` – `text` (`active` | `paused` | `archived`)
- `max_daily_spend_usd` – `numeric(10,2)` (nullable)
- `max_daily_tokens` – `bigint` (nullable)
- `created_at` – `timestamptz` (default `now()`)
- `updated_at` – `timestamptz` (default `now()`)

**Indexes:**

- `projects_slug_key` (unique)

---

### 2.2 `codered.tasks`

Each row is a **unit of work** the brain is handling.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid` (FK → `codered.projects.id`)
- `milestone_id` – `uuid` (nullable; future milestones table)
- `title` – `text`
- `description` – `text`
- `zone` – `text` (`green` | `yellow` | `red`)
- `impact_axes` – `text[]` (subset of `{'A','B','C','D','E'}`)
- `size` – `text` (`xs` | `s` | `m` | `l` | `xl`)
- `status` – `text` (`backlog` | `in_progress` | `blocked` | `needs_validation` | `done`)
- `task_token_budget` – `bigint` (nullable)
- `task_cost_ceiling_usd` – `numeric(10,2)` (nullable)
- `domain_tags` – `text[]` (e.g., `{'infra','ide','legal-adjacent'}`)
- `created_by` – `uuid` (nullable; future `users` table or external ID)
- `created_at` – `timestamptz` (default `now()`)
- `updated_at` – `timestamptz` (default `now()`)

**Indexes:**

- `tasks_project_id_idx`
- `tasks_status_idx`
- `tasks_zone_idx`
- `tasks_domain_tags_gin` – GIN on `domain_tags`
- `tasks_impact_axes_gin` – GIN on `impact_axes`

---

### 2.3 `codered.task_runs`

A **task run** is one pass through a major phase (orchestrator, architect, code, test, infra, safety, cynic, etc.) for a task.

**Columns:**

- `id` – `uuid` (PK)
- `task_id` – `uuid` (FK → `codered.tasks.id`)
- `project_id` – `uuid` (FK → `codered.projects.id`)
- `phase` – `text`  
  (`orchestrator` | `architect` | `code` | `test` | `infra` | `safety` | `cynic` | `research` | `librarian` | future phases)
- `status` – `text` (`queued` | `in_progress` | `succeeded` | `failed` | `blocked`)
- `agent_run_id` – `uuid` (nullable FK → `codered.agent_runs.id`)
- `summary` – `text` (short narrative of what happened in this phase)
- `created_at` – `timestamptz` (default `now()`)
- `completed_at` – `timestamptz` (nullable)

**Indexes:**

- `task_runs_task_id_idx`
- `task_runs_phase_idx`
- `task_runs_status_idx`

---

## 3. Agents & Runs

### 3.1 `codered.agents`

Defines each logical agent (Orchestrator, ArchitectAgent, CodeAgent, etc.).

**Columns:**

- `id` – `uuid` (PK)
- `slug` – `text` (unique, e.g. `orchestrator`, `architect`, `code`, `test`, `infra`, `safety`, `cynic`, `research`, `librarian`)
- `name` – `text`
- `description` – `text`
- `default_tier` – `text` (`gold` | `silver` | `bronze`)
- `max_tokens_per_call` – `bigint`
- `max_calls_per_task` – `integer`
- `cost_ceiling_usd_per_task` – `numeric(10,2)`
- `allowed_models` – `text[]` (optional; cross-check with `llm_models.name`)
- `allowed_tools` – `text[]` (MCP/tools)
- `is_active` – `boolean` (default `true`)
- `created_at` – `timestamptz` (default `now()`)
- `updated_at` – `timestamptz` (default `now()`)

**Indexes:**

- `agents_slug_key` (unique)

---

### 3.2 `codered.agent_runs`

Each LLM call or agent cycle is logged here.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid` (FK → `codered.projects.id`)
- `task_id` – `uuid` (nullable FK → `codered.tasks.id`)
- `agent_id` – `uuid` (FK → `codered.agents.id`)
- `mode` – `text` (e.g. `intake`, `design`, `implementation`, `testing`, `infra`, `safety_review`, `cynic_review`, `web_research`, `doc_update`)
- `provider` – `text` (e.g. `openai`, `anthropic`, `google`, `xai`, `local`)
- `model` – `text` (e.g. `gpt-5.1`, `claude-3-opus`)
- `tier` – `text` (`gold` | `silver` | `bronze`)
- `input_tokens` – `bigint`
- `output_tokens` – `bigint`
- `estimated_cost_usd` – `numeric(12,6)`
- `latency_ms` – `integer`
- `status` – `text` (`succeeded` | `failed`)
- `error_message` – `text` (nullable)
- `degraded_from_model` – `text` (nullable)
- `input_summary` – `text` (short description of the prompt)
- `output_summary` – `text` (short description of the response)
- `full_input` – `text` (optional, truncated or redacted)
- `full_output` – `text` (optional, truncated or redacted)
- `created_at` – `timestamptz` (default `now()`)

**Indexes:**

- `agent_runs_project_id_idx`
- `agent_runs_task_id_idx`
- `agent_runs_agent_id_idx`
- `agent_runs_model_idx`
- `agent_runs_created_at_idx`

---

## 4. CI/CD, Deployments & Errors

### 4.1 `codered.ci_events`

Tracks CI pipeline runs (GitHub Actions, etc.).

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `task_id` – `uuid` (nullable)
- `provider` – `text` (e.g. `github_actions`)
- `workflow_name` – `text`
- `run_id` – `text` (workflow run identifier from provider)
- `status` – `text` (`queued` | `in_progress` | `succeeded` | `failed` | `cancelled`)
- `started_at` – `timestamptz`
- `completed_at` – `timestamptz` (nullable)
- `commit_sha` – `text`
- `branch` – `text`
- `url` – `text` (link to CI run)
- `logs_url` – `text` (optional)

**Indexes:**

- `ci_events_project_id_idx`
- `ci_events_task_id_idx`
- `ci_events_run_id_idx`
- `ci_events_status_idx`

---

### 4.2 `codered.deployments`

Tracks deploys (Vercel, etc.).

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `task_id` – `uuid` (nullable)
- `provider` – `text` (e.g. `vercel`)
- `environment` – `text` (`preview`, `staging`, `production`)
- `status` – `text` (`queued` | `in_progress` | `succeeded` | `failed`)
- `url` – `text` (deployed URL)
- `deployment_id` – `text` (provider deployment ID)
- `commit_sha` – `text`
- `branch` – `text`
- `trigger_source` – `text` (`manual`, `ci`, `webhook`)
- `started_at` – `timestamptz`
- `completed_at` – `timestamptz` (nullable)

**Indexes:**

- `deployments_project_id_idx`
- `deployments_task_id_idx`
- `deployments_status_idx`
- `deployments_environment_idx`

---

### 4.3 `codered.errors`

Central error log for CI, deploys, agent runs, etc.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `task_id` – `uuid` (nullable)
- `ci_event_id` – `uuid` (nullable FK → `codered.ci_events.id`)
- `deployment_id` – `uuid` (nullable FK → `codered.deployments.id`)
- `agent_run_id` – `uuid` (nullable FK → `codered.agent_runs.id`)
- `source` – `text` (`ci`, `deploy`, `agent`, `infra`, `unknown`)
- `code` – `text` (provider/system error code)
- `message` – `text`
- `details` – `jsonb` (structured payload if available)
- `severity` – `text` (`low`, `medium`, `high`, `critical`)
- `created_at` – `timestamptz` (default `now()`)

**Indexes:**

- `errors_project_id_idx`
- `errors_task_id_idx`
- `errors_source_idx`
- `errors_severity_idx`
- GIN index on `details` (`errors_details_gin`)

---

## 5. Learning & Feedback

### 5.1 `codered.lessons`

See `learning-and-feedback.md` for semantics.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `title` – `text`
- `description` – `text`
- `source_type` – `text` (`ci_failure`, `cynic_review`, `safety_escalation`, `success_story`, etc.)
- `related_task_id` – `uuid` (nullable)
- `related_agent_id` – `uuid` (nullable)
- `tags` – `text[]`
- `recommendations` – `text`
- `status` – `text` (`draft` | `applied` | `deprecated`)
- `applied_count` – `integer` (default `0`)
- `last_applied_at` – `timestamptz` (nullable)
- `created_at` – `timestamptz` (default `now()`)
- `updated_at` – `timestamptz` (default `now()`)

**Indexes:**

- `lessons_project_id_idx`
- `lessons_tags_gin`
- `lessons_status_idx`

---

### 5.2 `codered.bug_patterns`

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `name` – `text`
- `pattern_signature` – `text`
- `examples` – `uuid[]` (references into `errors` or `ci_events` by convention)
- `impact` – `text` (`low`, `medium`, `high`, `critical`)
- `playbook` – `text`
- `tags` – `text[]`
- `status` – `text` (`draft` | `active` | `deprecated`)
- `created_at` – `timestamptz`
- `updated_at` – `timestamptz`

**Indexes:**

- `bug_patterns_project_id_idx`
- `bug_patterns_status_idx`
- `bug_patterns_tags_gin`

---

### 5.3 `codered.decisions`

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `title` – `text`
- `description` – `text`
- `context` – `text`
- `options_considered` – `text`
- `chosen_option` – `text`
- `rationale` – `text`
- `impact_axes` – `text[]`
- `owner` – `text` (human/agent identifier)
- `status` – `text` (`active` | `reversed` | `superseded`)
- `observed_outcome` – `text` (nullable)
- `outcome_rating` – `text` (`positive` | `neutral` | `negative` | null)
- `time_to_impact` – `text` (`short` | `medium` | `long` | null)
- `created_at` – `timestamptz`
- `updated_at` – `timestamptz`

**Indexes:**

- `decisions_project_id_idx`
- `decisions_status_idx`

---

## 6. LLM Routing & Cost

### 6.1 `codered.llm_providers`

**Columns:**

- `id` – `uuid` (PK)
- `name` – `text` (e.g. `openai`, `anthropic`, `google`, `xai`, `local`)
- `display_name` – `text`
- `base_url` – `text` (nullable)
- `status` – `text` (`active` | `deprecated`)
- `created_at` – `timestamptz`
- `updated_at` – `timestamptz`

---

### 6.2 `codered.llm_models`

**Columns:**

- `id` – `uuid` (PK)
- `provider_id` – `uuid` (FK → `codered.llm_providers.id`)
- `name` – `text` (SKU/model name)
- `tier` – `text` (`gold` | `silver` | `bronze`)
- `max_tokens` – `bigint`
- `approx_cost_input_per_1k` – `numeric(10,6)`
- `approx_cost_output_per_1k` – `numeric(10,6)`
- `capabilities` – `text[]` (`code`, `reasoning`, `tool_use`, `vision`, `long_context`, etc.)
- `default_usage_domains` – `text[]`
- `status` – `text` (`active` | `deprecated` | `experimental`)
- `created_at` – `timestamptz`
- `updated_at` – `timestamptz`

**Indexes:**

- `llm_models_name_idx`
- `llm_models_provider_id_idx`

---

### 6.3 `codered.llm_usage_daily`

Daily aggregate usage.

**Columns:**

- `id` – `uuid` (PK)
- `date` – `date`
- `project_id` – `uuid`
- `agent_id` – `uuid`
- `total_input_tokens` – `bigint`
- `total_output_tokens` – `bigint`
- `total_cost_usd` – `numeric(12,6)`

**Indexes:**

- `llm_usage_daily_date_idx`
- `llm_usage_daily_project_id_idx`
- `llm_usage_daily_agent_id_idx`

---

### 6.4 `codered.llm_usage_by_agent`

Aggregates per agent for arbitrary windows.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `agent_id` – `uuid`
- `window_start` – `timestamptz`
- `window_end` – `timestamptz`
- `total_input_tokens` – `bigint`
- `total_output_tokens` – `bigint`
- `total_cost_usd` – `numeric(12,6)`

**Indexes:**

- `llm_usage_by_agent_project_id_idx`
- `llm_usage_by_agent_agent_id_idx`

---

### 6.5 `codered.llm_degradation_events`

Tracks when routing downgraded model tiers.

**Columns:**

- `id` – `uuid` (PK)
- `agent_run_id` – `uuid` (FK → `codered.agent_runs.id`)
- `from_model` – `text`
- `to_model` – `text`
- `reason` – `text`
- `created_at` – `timestamptz`

**Indexes:**

- `llm_degradation_events_agent_run_id_idx`

---

## 7. RAG v1 for Modules 1–2

### 7.1 `codered.doc_manifest`

Tracks documents ingested into RAG.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `path` – `text` (e.g. `README.md`, `docs/orchestration.md`)
- `module` – `text` (e.g. `modules-1-2`)
- `domain` – `text` (`ide`, `infra`, `tokens`, `guardrails`, `learning`, etc.)
- `tags` – `text[]`
- `hash` – `text` (e.g. SHA-256)
- `size_bytes` – `bigint`
- `version` – `integer` (monotonic per path)
- `is_active` – `boolean`
- `created_at` – `timestamptz`
- `updated_at` – `timestamptz`

**Indexes:**

- `doc_manifest_project_id_idx`
- `doc_manifest_path_idx`
- `doc_manifest_domain_idx`
- `doc_manifest_tags_gin`

---

### 7.2 `codered.doc_chunks`

Chunk-level index for RAG retrieval.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `doc_id` – `uuid` (FK → `codered.doc_manifest.id`)
- `chunk_index` – `integer`
- `content` – `text`
- `embedding` – `vector` (or `double precision[]` depending on Supabase extension)
- `tokens` – `integer`
- `section` – `text` (optional heading/subheading info)
- `tags` – `text[]`
- `created_at` – `timestamptz`

**Indexes:**

- `doc_chunks_doc_id_idx`
- `doc_chunks_project_id_idx`
- `doc_chunks_tags_gin`
- Vector index on `embedding` (e.g. `IVFFLAT`), e.g.:  
  `CREATE INDEX doc_chunks_embedding_idx ON codered.doc_chunks USING ivfflat (embedding vector_cosine_ops);`

---

## 8. Long-Horizon Runs & Overrides

### 8.1 `codered.long_runs`

Definition of multi-hour AntiGravity runs.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `name` – `text`
- `target_duration_hours` – `integer`
- `goal_description` – `text`
- `allowed_agents` – `uuid[]` (agent IDs)
- `max_total_cost_usd` – `numeric(12,6)`
- `max_total_tokens` – `bigint`
- `status` – `text` (`planned` | `running` | `completed` | `stopped`)
- `started_at` – `timestamptz` (nullable)
- `completed_at` – `timestamptz` (nullable)
- `created_at` – `timestamptz`
- `updated_at` – `timestamptz`

**Indexes:**

- `long_runs_project_id_idx`
- `long_runs_status_idx`

---

### 8.2 `codered.long_run_checkpoints`

Periodic checkpoints for long runs.

**Columns:**

- `id` – `uuid` (PK)
- `long_run_id` – `uuid` (FK → `codered.long_runs.id`)
- `checkpoint_index` – `integer`
- `summary` – `text`
- `tokens_used_total` – `bigint`
- `cost_usd_total` – `numeric(12,6)`
- `created_at` – `timestamptz`

**Indexes:**

- `long_run_checkpoints_long_run_id_idx`

---

### 8.3 `codered.user_overrides`

Tracks when you override Safety, Cynic, or other guardrails.

**Columns:**

- `id` – `uuid` (PK)
- `project_id` – `uuid`
- `task_id` – `uuid` (nullable)
- `agent_run_id` – `uuid` (nullable)
- `override_type` – `text` (`deploy_anyway`, `cynic_reject`, `ignore_safety`, `budget_increase`, etc.)
- `reason` – `text`
- `created_by` – `text` (identifier)
- `created_at` – `timestamptz`

**Indexes:**

- `user_overrides_project_id_idx`
- `user_overrides_task_id_idx`

---

## 9. MVP Criteria for Schema

The Supabase schema for Modules 1–2 is **MVP-complete** when:

1. All tables in this doc exist with at least the listed columns and keys.
2. Basic indexes (especially on `project_id`, `task_id`, `agent_id`, and vector embeddings) are present.
3. RLS (if applied) does **not** block the brain from reading/writing its own rows in a controlled dev environment.
4. One end-to-end run has been executed where:
   - Tasks, task_runs, agent_runs, ci_events/deployments, errors, lessons, and doc_chunks are all populated,
   - Dashboards can query the aggregate views (`llm_usage_*`).

Future modules (legal, Twilio, lead faucet, etc.) get **their own** tables/schemas and extend, not break, this foundation.
