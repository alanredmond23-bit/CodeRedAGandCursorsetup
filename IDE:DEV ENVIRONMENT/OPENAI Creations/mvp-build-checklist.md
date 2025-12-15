# Phase 1 – MVP Build Checklist

**File:** `docs/mvp-build-checklist.md`  
**Purpose:** A single execution checklist for your first 60-minute (+30-minute tweak) MVP session.

Mark items as you complete them. When this file is fully checked, Phase 1 is done.

---

## 1. Environment & Secrets

- [ ] Create `.env.example` at repo root.
  - [ ] Include placeholders for:
    - [ ] `OPENAI_API_KEY`
    - [ ] `SUPABASE_URL`
    - [ ] `SUPABASE_ANON_KEY`
    - [ ] `AG_ENV` (e.g. `dev`)

- [ ] Create `.env.local` (gitignored) with real values on your machine.

---

## 2. Core Agent YAMLs (MVP Fields Only)

Agents to define in `/agents/`:

- `orchestrator_codered.yaml`
- `cynic_evaluator_v1.yaml`
- `legal_research_v1.yaml`
- `twilio_campaign_v1.yaml`

For each of the 4 agents, fill these MVP fields:

- [ ] `agent_id`
- [ ] `name`
- [ ] `domain`
- [ ] `tier`
- [ ] `role` (short paragraph)
- [ ] `goals` (2–3 bullets)
- [ ] `non_goals` (2–3 bullets)

Models:

- [ ] `models.primary`
- [ ] `models.backups` (at least one)
- [ ] `models.temperature`
- [ ] `models.max_tokens`

Tools (simple):

- [ ] 2–3 tools defined per agent with fields:
  - [ ] `name`
  - [ ] `mode` (`read` or `read/write`)

Limits:

- [ ] `limits.max_runtime_minutes`
- [ ] `limits.max_recursion_depth`
- [ ] `limits.max_child_agents`
- [ ] `limits.max_estimated_cost_usd`

Memory:

- [ ] `memory_profile.persistence` set to `run`
- [ ] `memory_profile.supabase_schema` set to `codered`

Guardrails & Cynic hooks:

- [ ] `guardrails.hallucination_policy: strict`
- [ ] `guardrails.can_touch_production: false` or `approval_required`
- [ ] `cynic_hooks.enabled: true`
- [ ] `cynic_hooks.scoring_profile` set appropriately (`default`, `code`, `infra`)

---

## 3. Cynic ¼ – Minimal Evaluation

- [ ] Ensure `cynic_evaluator_v1.yaml`:
  - [ ] Uses profiles: `default`, `code`, `infra` (per `docs/cynic-eval.md`).
  - [ ] Has `domain: qa` and `tier: core`.
- [ ] Implement logic (in orchestrator or tooling) to:
  - [ ] Call `cynic_evaluator_v1` manually on selected artefacts.
- [ ] Confirm `cynic_evaluator_v1` writes to `codered.evals_cynic` with:
  - [ ] `subject_type`
  - [ ] `subject_label`
  - [ ] `scoring_profile`
  - [ ] `total_score`
  - [ ] `grade`
  - [ ] `strengths` (array)
  - [ ] `weaknesses` (array)
  - [ ] `recommendations` (array)

---

## 4. Token ¼ – Per-Run Cost Tracking

- [ ] Update/create `codered.agent_runs` table with fields for:
  - [ ] `id` (PK)
  - [ ] `created_at`
  - [ ] `agent_id`
  - [ ] `status`
  - [ ] `tokens_in`
  - [ ] `tokens_out`
  - [ ] `cost_usd_estimate`
  - [ ] `model_name`
  - [ ] `duration_ms`

- [ ] Implement a simple **pricing map** in code/config for your primary model(s).  
- [ ] On each agent run, compute and store `cost_usd_estimate`.

---

## 5. Supabase – MVP Spine

- [ ] Create migration `supabase/migrations/0001_codered_core.sql` that defines:
  - [ ] `codered.agent_runs`
  - [ ] `codered.tool_calls` (minimal fields; token tracking can come later)
  - [ ] `codered.evals_cynic` (as per `docs/cynic-eval.md` MVP requirements)

- [ ] Run migration locally and confirm tables exist.

---

## 6. System Rules (`rules.md`)

- [ ] Create `rules.md` at repo root or under `docs/`.

Content to include:

- [ ] Orchestrator rules:
  - [ ] Break work into microtasks, route to agents, call Cynic, log to Supabase.
  - [ ] Never bypass limits in agent YAMLs.
- [ ] Agent rules:
  - [ ] Stay inside domain.
  - [ ] Use only configured tools, in allowed modes.
  - [ ] Respect runtime/recursion/cost limits.
- [ ] MVP boundaries:
  - [ ] Cynic is advisory only. No auto-deploy or auto-tuning.  
  - [ ] Only the core set of MCPs/extensions is used for now.

---

## 7. Sanity Pass

- [ ] Open each of the 4 agent YAMLs and read them end-to-end:
  - [ ] Does their role/goal match what you actually want them to do?  
  - [ ] Are cost and time limits sane?  
  - [ ] Are tools restricted enough to be safe?

- [ ] Run a test agent call and confirm:
  - [ ] Entry is created in `agent_runs`.  
  - [ ] Token and cost fields are populated.  
  - [ ] You can manually call Cynic on that output.

Once all boxes above are checked, **Phase 1 (MVP) is complete.**
