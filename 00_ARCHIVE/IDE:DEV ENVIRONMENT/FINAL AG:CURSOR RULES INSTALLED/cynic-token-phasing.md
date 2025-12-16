# Cynic & Token Phasing – 1/4 to 4/4

**File:** `docs/cynic-token-phasing.md`  
**Purpose:** Precisely define how Cynic and token/cost tracking ramp from MVP to Worldclass in four slices each. This lets you ship something useful in one hour and layer sophistication in later passes.

This file is a focused add-on to:
- `docs/cynic-eval.md`
- `docs/phases-mvp-to-worldclass.md`

---

## 1. Cynic Phasing (¼ → 4/4)

### 1.1 Cynic ¼ – MVP

Scope:

- One agent: `cynic_evaluator_v1`
- Domain: `qa`
- Profiles enabled:
  - `default`
  - `code`
  - `infra`
- Triggering:
  - Manual only (orchestrator/you explicitly call Cynic).
- Data written to `codered.evals_cynic`:
  - `subject_type`
  - `subject_label`
  - `scoring_profile`
  - `total_score`
  - `grade`
  - `dims` (minimal: correctness, clarity, alignment)
  - `strengths` (≤ 3 items)
  - `weaknesses` (≤ 3 items)
  - `recommendations` (≤ 3 items)

Goal: Get a **real critic** into the loop on day one without any automation risk.

---

### 1.2 Cynic ½ – Phase 2

Adds:

- Profiles enabled:
  - `legal`
  - `twilio`
  - `ux`
  - `cashflow`
  - `orchestration`
  - `research`

- Auto-triggers:
  - New legal drafts saved into configured paths.  
  - New Twilio campaign configurations written.  
  - CI/infra changes (e.g. PRs on workflows).

Still **no YAML tuning**, but:

- Correct lens for each artefact.  
- Automatic scoring on key events, not just manual calls.

---

### 1.3 Cynic ¾ – Phase 3

Adds:

- `performance_targets` concept (tracked externally or in simple config):
  - `min_score` per agent (e.g. 88 for legal drafts).

- Orchestrator logic:
  - If last N evaluations for a given agent/artefact type fall **below target**, Orchestrator:
    - Requests another iteration.  
    - Or escalates to you for review.

Effect: Cynic grades now **drive behavior**, not just reporting.

Still **no direct YAML edits** – this is advisory pressure + orchestration rules.

---

### 1.4 Cynic 4/4 – Phase 4 & Worldclass (CYNIC_SUPREME)

Adds:

- YAML tuning capabilities (see `docs/cynic-eval.md` + `docs/agents-yaml-templates.md`):
  - `auto_tune: false | suggest_only | allow_safe_changes`
  - `performance_targets` stored per agent in YAML.

- Cynic + orchestrator together:
  - Observe scores, costs, and outcomes per agent.  
  - Generate **YAML patch proposals**, such as:
    - Adjust `max_estimated_cost_usd`.  
    - Change `reasoning_mode`.  
    - Adjust tools (add/remove) with justification.
  - Store proposals in Supabase (e.g. `yaml_patch_proposals` table).

- Optional (Worldclass):
  - Auto-apply “safe” proposals (small numeric changes) with:
    - Audit logs
    - Versioning
    - Rollback

Effect: The system becomes **self-critical and self-tuning**, but always within guardrails you define.

---

## 2. Token & Cost Phasing (¼ → 4/4)

### 2.1 Token ¼ – MVP

Scope:

- Extend `codered.agent_runs` with fields:
  - `tokens_in`
  - `tokens_out`
  - `cost_usd_estimate`
  - `model_name`
  - `duration_ms`

- Maintain a **static pricing map** in code/config for primary model(s).  
- Each agent run:
  - Captures tokens in/out via LLM response metadata.  
  - Calculates `cost_usd_estimate` using pricing map.

Effect: You immediately see **cost per run** and can sum up daily spend.

---

### 2.2 Token ½ – Phase 2

Scope:

- Extend `codered.tool_calls` with:
  - `tokens_in`
  - `tokens_out`
  - `cost_usd_estimate`
  - `tool_name`
  - `success` / `status`

Effect:

- Cost visibility by **tool**, not just by agent.  
- You can answer:
  - “How much does browser-based research cost?”  
  - “How expensive are Supabase-heavy vs Twilio-heavy workloads?”

---

### 2.3 Token ¾ – Phase 3

Scope:

- Add budgets to agent YAMLs:
  - `limits.max_estimated_cost_usd` (per run, optionally per day in config).

- Orchestrator logic:
  - Before launching a large or long-horizon run, estimate cost based on:
    - Recent tokens/cost per similar run.  
    - Configured YAML limits.
  - Decide:
    - “Run as planned.”  
    - “Downscope / split task.”  
    - “Ask Alan for approval.”

Effect: Cost control moves from **after-the-fact reporting** → **pre-flight gating**.

---

### 2.4 Token 4/4 – Phase 4 & Worldclass

Scope:

- Build dashboards from Supabase for:
  - Spend by agent, domain, project, time window.  
  - Cost vs Cynic score (quality) per agent.  
  - Trendlines for cost and quality.

- Integrate with Oracle models (if enabled):
  - Use cost + quality + outcome data to:
    - Predict ROI for certain campaigns/strategies.  
    - Decide where to allocate attention and LLM budget.

Effect:

- Cost becomes a **strategic signal**, not just an operational metric.  
- You can say:
  - “LegalAgents X and Y are expensive but consistently A+; worth it.”  
  - “This Twilio agent burns tokens without conversions; rework or retire it.”

---

## 3. MVP Requirements Recap (Cynic & Token Only)

To be crystal clear: for **MVP**, you must hit:

**Cynic ¼:**
- `cynic_evaluator_v1` defined and callable.  
- `default`, `code`, `infra` profiles available.  
- Writes minimal eval rows into `evals_cynic`.

**Token ¼:**
- `agent_runs` has token and cost fields.  
- Each agent run logs `tokens_in`, `tokens_out`, `cost_usd_estimate`, `model_name`, `duration_ms`.  
- Static pricing config exists for your primary model(s).

Everything beyond that can be safely layered as you execute Phases 2–5.
