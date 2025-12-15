# Supabase Schema Design – antigravityCodeRed

**Goal:**  
Define a consistent Supabase schema for the **CodeRed brain** – tasks, agents, runs, CI, RAG, and learning – that can:

- Serve **this repo** (DPC / CodeRed) immediately.
- Scale to **multiple projects** under one brain.
- Later support **multi-tenant / white-label** without rewrites.

We design this as:

- A **base schema**: `codered`  
- Optional **per-project schemas**: `codered_<project_slug>`  
- A set of **core tables** for:
  - Projects & tasks
  - Agents & runs
  - CI/deploy events
  - RAG corpora
  - Learning/feedback
  - UX snippets (for your design corpus)

---

## 1. Naming & High-Level Principles

### 1.1 Schema Structure

- **Base schema:** `codered`
  - Holds global metadata and cross-project aggregates:
    - `projects`, `agents`, `corpora`, `lessons`, etc.

- **Per-project schemas (optional, Phase 2+):** `codered_<project_slug>`
  - Can hold project-specific application data if needed.
  - For MVP, we can start with **only `codered`** and add per-project schemas later.

### 1.2 General Design Rules

- All tables have:
  - `id` as `uuid` primary key (except small lookup/enums).
  - `created_at`, `updated_at` timestamps (`timestamptz`).
- All rows linked to a **project** include:
  - `project_id` → `codered.projects(id)`
- For future multi-tenant:
  - `projects` will link to `orgs` (Phase 3+).
- Soft deletes via `deleted_at` where we expect data to be retired but kept for audit.

---

## 2. Core Project & Task Tables

These power the Orchestrator, backlog, milestones, and execution history.

### 2.1 `codered.projects`

**Purpose:** Top-level container for a CodeRed-managed project (e.g., “antigravityCodeRed”, “Legal War Room”, “Twilio War Machine”).

**Columns (key ones):**

- `id` (uuid, PK)
- `slug` (text, unique) – machine name (e.g., `antigravity_codered`)
- `name` (text) – human-friendly name
- `description` (text)
- `status` (text) – e.g. `active`, `paused`, `archived`
- `owner_user_id` (uuid, nullable, Phase 3+ for multi-tenant)
- `created_at`, `updated_at`

### 2.2 `codered.milestones`

**Purpose:** Flexible milestone system with numeric + categorical barometer.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `name` (text)
- `description` (text)
- `status` (text) – e.g. `not_started`, `in_progress`, `ready_for_cynic`, `shipped`
- `progress_percent` (integer, 0–100)
- `target_date` (date, nullable)
- `actual_date` (date, nullable)
- `created_at`, `updated_at`

### 2.3 `codered.tasks`

**Purpose:** Canonical task/backlog unit. Orchestrator owns this.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `milestone_id` (uuid, FK → `codered.milestones`, nullable)
- `parent_task_id` (uuid, FK → `codered.tasks`, nullable) – for microtasks/subtasks
- `title` (text)
- `description` (text)
- `zone` (text) – `red`, `yellow`, `green`
- `impact_axes` (text[]) – subset of `['A','B','C','D','E']`  
  - A: easier to deploy  
  - B: more revenue  
  - C: saves money  
  - D: more organized  
  - E: legal wins / risk
- `size` (text) – `xs`, `s`, `m`, `l`, `xl`
- `status` (text) – `backlog`, `in_progress`, `blocked`, `ready_for_review`, `done`
- `assignee_agent_id` (uuid, FK → `codered.agents`, nullable)
- `assignee_human` (text, nullable)
- `priority` (integer, optional ordering)
- `due_date` (timestamptz, nullable)
- `created_at`, `updated_at`, `completed_at` (timestamptz, nullable)

### 2.4 `codered.task_runs`

**Purpose:** Execution history for a task – each “agent pass” or cycle recorded.

**Columns:**

- `id` (uuid, PK)
- `task_id` (uuid, FK → `codered.tasks`)
- `project_id` (uuid, FK → `codered.projects`)
- `agent_run_id` (uuid, FK → `codered.agent_runs`) – link to agent execution
- `phase` (text) – `architect`, `code`, `test`, `review`, `infra`, `safety`, `cynic`, `orchestrator`
- `status` (text) – `planned`, `running`, `succeeded`, `failed`, `skipped`
- `summary` (text)
- `created_at`, `updated_at`

---

## 3. Agents & Agent Runs

### 3.1 `codered.agents`

**Purpose:** Catalog of logical agents (Architect, Code, Cynic, ResearchAgent, etc.), aligned with YAML configs.

**Columns:**

- `id` (uuid, PK)
- `name` (text, unique) – e.g., `ArchitectAgent`, `CynicAgent`
- `slug` (text, unique) – e.g., `architect`, `cynic`
- `description` (text)
- `role` (text) – `architect`, `code`, `test`, `review`, `infra`, `safety`, `orchestrator`, `cynic`, `research`, `librarian`
- `allowed_zones` (text[]) – subset of `['red','yellow','green']`
- `default_model` (text) – e.g. `gemini-code`, `gpt-5.1`, `claude-opus`
- `max_tokens` (integer)
- `temperature` (numeric)
- `cost_ceiling_usd` (numeric, nullable)
- `long_horizon_allowed` (boolean)
- `config_yaml_path` (text) – path in repo for YAML, for sync
- `created_at`, `updated_at`

### 3.2 `codered.agent_runs`

**Purpose:** Max-observability log of each LLM/agent call.

**Columns (key ones):**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `agent_id` (uuid, FK → `codered.agents`)
- `task_id` (uuid, FK → `codered.tasks`, nullable) – optional if freeform run
- `mode` (text) – `architect`, `code`, etc.
- `input_summary` (text)
- `output_summary` (text)
- `full_input` (text) – raw prompt (can be large; consider compression later)
- `full_output` (text) – raw model output
- `model` (text)
- `tokens_prompt` (integer)
- `tokens_completion` (integer)
- `approx_cost_usd` (numeric)
- `zones_touched` (text[]) – e.g., `['green']`, `['yellow','red']`
- `tools_used` (text[]) – e.g., `['supabase_client','github_api']`
- `rag_documents` (uuid[] of `codered.documents.id`) – docs consulted
- `status` (text) – `succeeded`, `failed`, `aborted`
- `error_message` (text, nullable)
- `created_at`, `updated_at`

---

## 4. CI, Deployments, Errors

### 4.1 `codered.ci_events`

**Purpose:** Track all CI runs (GitHub Actions, etc.), both pass/fail.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `provider` (text) – e.g., `github-actions`
- `workflow_name` (text)
- `run_id` (text) – external ID
- `branch` (text)
- `commit_sha` (text)
- `status` (text) – `queued`, `running`, `succeeded`, `failed`, `canceled`
- `trigger` (text) – `push`, `pull_request`, `manual`
- `zones_touched` (text[], nullable) – aggregated from task/agent labels
- `start_time` (timestamptz)
- `end_time` (timestamptz)
- `duration_seconds` (integer)
- `created_at`, `updated_at`

### 4.2 `codered.deployments`

**Purpose:** Record all deployments (Vercel, etc.), linked to CI and projects.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `provider` (text) – `vercel`, `other`
- `environment` (text) – `dev`, `staging`, `prod`
- `deployment_id` (text) – external ID
- `ci_event_id` (uuid, FK → `codered.ci_events`, nullable)
- `status` (text) – `pending`, `succeeded`, `failed`, `rolled_back`
- `url` (text, nullable)
- `created_at`, `updated_at`

### 4.3 `codered.errors`

**Purpose:** Unified error log for CI, deployments, runtime issues, agent-level errors.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `source` (text) – `ci`, `deployment`, `agent`, `runtime`
- `ci_event_id` (uuid, FK → `codered.ci_events`, nullable)
- `deployment_id` (uuid, FK → `codered.deployments`, nullable)
- `agent_run_id` (uuid, FK → `codered.agent_runs`, nullable)
- `error_code` (text)
- `message` (text)
- `details` (text)
- `severity` (text) – `info`, `warning`, `error`, `critical`
- `created_at`, `updated_at`

---

## 5. RAG: Corpora, Documents, Chunks, Embeddings

### 5.1 `codered.corpora`

**Purpose:** High-level group of documents (e.g., “Core CodeRed Docs”, “Legal War Room”, “Twilio Flows”).

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`, nullable) – null for global corpus
- `name` (text)
- `description` (text)
- `domain_tags` (text[]) – e.g., `['core','orchestration']`, `['legal']`, `['twilio']`
- `risk_level` (text) – `safe`, `internal`, `legal_critical`
- `created_at`, `updated_at`

### 5.2 `codered.documents`

**Purpose:** Single logical document (README, md, PDF, etc.).

**Columns:**

- `id` (uuid, PK)
- `corpus_id` (uuid, FK → `codered.corpora`)
- `project_id` (uuid, FK → `codered.projects`, nullable)
- `title` (text)
- `source_path` (text) – file path or external URL
- `version` (text) – e.g., `v1`, `2025-11-27`
- `domain_tags` (text[]) – `['orchestration','agents']`
- `risk_level` (text) – `safe`, `internal`, `legal_critical`
- `is_pinned` (boolean) – for core rules (Modules 1–2)
- `created_at`, `updated_at`

### 5.3 `codered.chunks`

**Purpose:** Chunked text of each document for RAG.

**Columns:**

- `id` (uuid, PK)
- `document_id` (uuid, FK → `codered.documents`)
- `project_id` (uuid, FK → `codered.projects`, nullable)
- `chunk_index` (integer)
- `content` (text)
- `token_count` (integer)
- `embedding_id` (uuid, FK → `codered.embeddings`, nullable)
- `created_at`, `updated_at`

### 5.4 `codered.embeddings`

**Purpose:** Vector representations for chunks.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`, nullable)
- `document_id` (uuid, FK → `codered.documents`)
- `chunk_id` (uuid, FK → `codered.chunks`)
- `embedding` (vector) – pgvector column
- `model` (text)
- `created_at`, `updated_at`

**Indexes:**

- Vector index on `embedding` for nearest-neighbor search.
- B-tree index on `(project_id, document_id, chunk_id)`.

---

## 6. Learning & Feedback

### 6.1 `codered.lessons`

**Purpose:** High-level “what we learned” items for nested learning.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `title` (text)
- `description` (text)
- `domain_tags` (text[]) – `['legal']`, `['ci']`, `['ux']`
- `source_type` (text) – `agent_run`, `ci_event`, `retro`, `manual`
- `source_id` (uuid, nullable) – links to `agent_runs` or `ci_events`
- `impact_axes` (text[]) – subset of `['A','B','C','D','E']`
- `severity` (text) – `minor`, `moderate`, `major`, `critical`
- `created_at`, `updated_at`

### 6.2 `codered.bug_patterns`

**Purpose:** Canonical bug / failure patterns and their fixes.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `name` (text)
- `description` (text)
- `pattern_signature` (text) – e.g., key stacktrace fragment, regex
- `root_cause` (text)
- `recommended_fix` (text)
- `related_lessons` (uuid[], nullable)
- `created_at`, `updated_at`

### 6.3 `codered.decisions`

**Purpose:** Log major design / legal / architectural decisions.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `title` (text)
- `description` (text)
- `domain` (text) – `legal`, `infra`, `ux`, `marketing`, etc.
- `decision_type` (text) – `architecture`, `policy`, `legal_strategy`, `product`
- `rationale` (text)
- `options_considered` (text)
- `chosen_option` (text)
- `decision_maker` (text)
- `created_at`, `updated_at`

---

## 7. UX Snippets Corpus

### 7.1 `codered.ux_snippets`

**Purpose:** Store your favorite UX code snippets/design fragments.

**Columns:**

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`, nullable)
- `name` (text)
- `description` (text)
- `tech_stack` (text[]) – e.g., `['nextjs','tailwind']`
- `code_sample` (text)
- `preview_url` (text, nullable)
- `tags` (text[]) – `['glassmorphism','dashboard','landing']`
- `quality_score` (numeric, nullable) – Cynic design score later
- `approved_by` (text, nullable) – you
- `created_at`, `updated_at`

---

## 8. Governance & Audit

These will be fleshed out later but can be stubbed now.

### 8.1 `codered.orgs` (Phase 3+)

**Purpose:** Future multi-tenant support.

- `id` (uuid, PK)
- `name` (text)
- `created_at`, `updated_at`

### 8.2 `codered.user_overrides`

**Purpose:** Log human overrides of agents/Cynic/Orchestrator.

- `id` (uuid, PK)
- `project_id` (uuid, FK → `codered.projects`)
- `user` (text)
- `override_type` (text) – `cynic_reject`, `deploy_anyway`, `agent_override`
- `target_type` (text) – `agent_run`, `ci_event`, `deployment`, `task`
- `target_id` (uuid, nullable)
- `reason` (text)
- `created_at`, `updated_at`

---

## 9. MVP Scope vs Later Phases

- **MVP must implement:**
  - `projects`, `milestones`, `tasks`, `task_runs`
  - `agents`, `agent_runs`
  - `ci_events`, `deployments`, `errors`
  - `corpora`, `documents`, `chunks`, `embeddings`
  - `lessons`, `bug_patterns`, `decisions`
- **Nice-to-have but can be stubbed:**
  - `ux_snippets`
  - `user_overrides`
  - `orgs`
- **Legal evidence schemas:**
  - Will live in a **separate Supabase project** for safety.
  - Aggregations for “global thinking” done via analytics views, not by mixing raw legal data in `codered`.

This design gives us a **single brain** with domain-like segmentation (projects, corpora, domains) while keeping the door open for multi-tenant and productization later.
