# RAG v1 – Modules 1–2 (IDE, Orchestration, Infra) – antigravityCodeRed

**File:** `docs/rag-v1-modules-1-2.md`  
**Scope:** Exactly what goes into RAG v1 for Modules 1–2, how it is chunked, tagged, and retrieved.

This is the **retrieval contract** for the brain when working on:

- IDE & AntiGravity setup (Modules 1–2)
- Orchestration, routing, guardrails, tokens
- CI/CD, Supabase schema, learning system

If a document is not listed here (or not in `codered.doc_manifest` with `module = 'modules-1-2'`), agents **should not assume** it is available in RAG.

---

## 1. RAG v1 Goals

1. **High signal, low noise.**  
   Only include docs that directly support Modules 1–2 behavior.

2. **Deterministic coverage.**  
   Agents know which docs are in play and can rely on them.

3. **Tight tagging.**  
   Chunks are tagged by domain, agent relevance, and section to support domain-specific retrieval.

4. **Stable foundation.**  
   Legal, Twilio, lead-faucet, and other future modules will have **separate** RAG profiles.

---

## 2. Docs Included in v1

RAG v1 for Modules 1–2 ingests the following repo files:

### 2.1 Root & Setup

1. `README.md`  
   - Purpose: Overview of antigravityCodeRed, modules, and philosophy.

2. `docs/architecture.md`  
   - Purpose: High-level architecture for the brain, modules, flows.

3. `FIRST5HOURS/SETUP.md`  
   - Purpose: Step-by-step for first-5-hours environment setup in AntiGravity, GitHub, Supabase, etc.

### 2.2 Orchestration & Agents

4. `docs/agents.md`  
   - Purpose: Agent catalog, roles, responsibilities.

5. `docs/orchestration.md`  
   - Purpose: Pipeline phases, task/task_run/agent_run lifecycle.

6. `docs/prompt-routing.md`  
   - Purpose: How Orchestrator builds prompts and routes requests.

7. `docs/llm-routing.md`  
   - Purpose: Gold/Silver/Bronze model tiering, per-agent defaults, fallbacks.

### 2.3 Safety, Memory, Tokens

8. `docs/memory-and-guardrails.md`  
   - Purpose: Memory strategy, guardrails, hallucination control, red-zones.

9. `docs/tokens-and-costs.md`  
   - Purpose: Budgets, tokens, cost ceilings, long-horizon runs.

10. `docs/learning-and-feedback.md`  
    - Purpose: Lessons, bug patterns, decisions, and feedback loop.

### 2.4 Data & Infra

11. `docs/schema-supabase.md`  
    - Purpose: Canonical schema for `codered` in Supabase.

12. `docs/infra-ci-cd.md` (once created)  
    - Purpose: CI/CD standards, GitHub Actions + Vercel rules.

13. `docs/playbooks/ci-vercel-supabase.md` (once created)  
    - Purpose: Concrete “when X breaks in CI/Vercel/Supabase, do Y” playbooks.

### 2.5 Optional / Extended (v1.1+)

14. `docs/mcp-and-extensions.md` (future)  
15. `docs/agents-yaml-templates.md` (future)  
16. `docs/cynic-eval.md` (future)

These may be added when they exist, but v1 can ship with 1–13.

---

## 3. Chunking Strategy

### 3.1 Chunk Size & Overlap

We use **semantic chunks** with guardrails, not dumb fixed-size token windows.

**Defaults:**

- Target size: ~500–800 tokens per chunk
- Overlap: 50–100 tokens
- Chunking boundaries:
  - Headings (`#`, `##`, `###`)
  - Bullet blocks
  - Code fences

For long docs (like `schema-supabase.md`), each major heading (e.g., table definition) should be kept intact in a chunk if possible.

### 3.2 Chunk Metadata

Each chunk written to `codered.doc_chunks` must have:

- `project_id`
- `doc_id`
- `chunk_index`
- `content`
- `tokens`
- `embedding`
- `section` – derived from nearest heading (e.g. `2.2 codered.tasks`)
- `tags` – see below

Embedding uses the project’s standard embedding model (e.g. 3072-dim vector).

---

## 4. Tagging Strategy

Tagging is what makes retrieval smart instead of noisy.

### 4.1 Core Tag Categories

Each chunk gets tags from these categories:

1. **Module**  
   - `modules-1-2` (constant for this profile)

2. **Domain**  
   One or more of:
   - `ide`
   - `orchestration`
   - `agents`
   - `routing`
   - `guardrails`
   - `tokens`
   - `learning`
   - `schema`
   - `infra`
   - `playbook`

3. **Agent-Relevant Tags**  
   Which agents should primarily care about this chunk:
   - `orchestrator`
   - `architect`
   - `code`
   - `test`
   - `infra`
   - `safety`
   - `cynic`
   - `research`
   - `librarian`

4. **Phase/Usage**  
   - `intake`
   - `design`
   - `implementation`
   - `testing`
   - `ci_cd`
   - `safety_review`
   - `cynic_review`
   - `learning`
   - `tokens_and_costs`

### 4.2 Examples

- A section in `orchestration.md` describing the full pipeline:
  - Tags: `['modules-1-2','orchestration','orchestrator','architect','code','test','infra','intake','design','implementation']`

- A table definition in `schema-supabase.md` for `codered.doc_chunks`:
  - Tags: `['modules-1-2','schema','rag','librarian','infra']`

- A budget rule in `tokens-and-costs.md`:
  - Tags: `['modules-1-2','tokens','orchestrator','learning','long_run']`

---

## 5. Retrieval Rules (Who Sees What)

Different agents should query RAG differently.

### 5.1 OrchestratorAgent

**Goal:** Understand architecture, routing, budgets, and guardrails when shaping tasks.

**RAG Query Defaults:**

- Filter tags to domains:
  - `['orchestration','agents','routing','guardrails','tokens','learning']`
- Filter by agents:
  - `['orchestrator']` (required) OR general docs (no agent tag)
- Top-k: 10–15 chunks

### 5.2 ArchitectAgent

**Goal:** Design solutions that respect architecture, schema, and infra patterns.

**RAG Query Defaults:**

- Filter domains:
  - `['architecture','orchestration','schema','infra','playbook']` (depending on final domain labels)
- Agent tags:
  - `['architect']`
- Extra emphasis (higher weight) on:
  - `schema-supabase.md`
  - `infra-ci-cd.md`
  - `playbooks/ci-vercel-supabase.md`

Top-k: 15–25 chunks for complex tasks.

### 5.3 CodeAgent

**Goal:** Implement without breaking conventions.

**RAG Query Defaults:**

- Filter domains:
  - `['architecture','schema','orchestration']`
- Agent tags:
  - `['code']`
- Top-k: 5–10 chunks

CodeAgent mostly cares about:
- File conventions from `README.md`/`architecture.md`
- Relevant schema tables
- Any playbooks that affect implementation choices

### 5.4 TestAgent

**Goal:** Design tests and checks aligned with architecture & known bug patterns (from learning system).

**RAG Query Defaults:**

- Domains:
  - `['testing','learning','playbook','infra']` (once these exist)
- Agent tags:
  - `['test']`
- Top-k: 5–15 chunks

### 5.5 InfraAgent

**Goal:** CI/CD, Vercel, Supabase infra.

**RAG Query Defaults:**

- Domains:
  - `['infra','schema','playbook','tokens']`
- Agent tags:
  - `['infra']`
- Top-k: 10–20 chunks

InfraAgent focuses heavily on:

- `infra-ci-cd.md`
- `playbooks/ci-vercel-supabase.md`
- Relevant parts of:
  - `schema-supabase.md`
  - `tokens-and-costs.md`

### 5.6 SafetyAgent

**Goal:** Apply guardrails and red-zone rules.

**RAG Query Defaults:**

- Domains:
  - `['guardrails','tokens','learning']`
- Agent tags:
  - `['safety']`
- Top-k: 10–15 chunks

### 5.7 CynicAgent

**Goal:** Score work and critique.

**RAG Query Defaults:**

- Domains:
  - `['orchestration','learning','playbook']`
- Agent tags:
  - `['cynic']`
- Top-k: 10–20 chunks

CynicAgent should see:

- Prior `lessons` and `bug_patterns` once they are RAG-ingested.
- Definitions of A–E axes and scoring bands (from `cynic-eval.md` when added).

### 5.8 Research & Librarian Agents

- **ResearchAgent** will mostly hit external/web tools, but for Modules 1–2:
  - Domains: `['architecture','schema','infra']`
- **LibrarianAgent**:
  - Domains: `['learning','schema','rag']`
  - Uses RAG to understand existing structures when adding new `lessons` or `bug_patterns`.

---

## 6. Update & Re-indexing Rules

### 6.1 When to Re-index

Re-index RAG v1 for Modules 1–2 when:

- Any included doc (1–13) changes materially.
- New docs (14–16) in the list are created or significantly updated.
- Schema changes affect interpretation of existing docs.

**Process:**

1. Compute new hash for the file.
2. If hash changed:
   - Increment `version` in `doc_manifest`.
   - Mark older version as `is_active = false` (but keep for traceability).
   - Delete old `doc_chunks` for that `doc_id` or mark them inactive.
   - Re-chunk, re-embed, and insert new chunks with updated `version` and tags.

### 6.2 Who Triggers Re-index

- **LibrarianAgent** is primary.
- Orchestrator or InfraAgent can request a re-index when they detect changes to critical docs (e.g., schema/infra).

---

## 7. RAG MVP Criteria for Modules 1–2

RAG v1 is **MVP-complete** when:

1. `doc_manifest` and `doc_chunks` are populated for docs 1–11 (and 12–13 once created).
2. All chunks have:
   - module/domain/agent tags,
   - embeddings,
   - section labels.
3. Orchestrator, ArchitectAgent, CodeAgent, TestAgent, InfraAgent, SafetyAgent, CynicAgent, ResearchAgent, and LibrarianAgent:
   - Have RAG query templates that follow the retrieval rules above.
4. At least one task has been run where:
   - Agents clearly **used** RAG (referencing specific docs/sections),
   - Outputs improved versus running without RAG.

From here, we can expand:

- Legal RAG (separate profile).
- Product/marketing RAG (separate profile).
- Multi-project and white-label RAG strategies.
