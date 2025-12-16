# Tokens, Cost & Long-Horizon Runs – antigravityCodeRed

**File:** `docs/tokens-and-costs.md`  
**Scope:** How CodeRed budgets tokens and dollars, monitors usage, and safely runs long-horizon jobs (1–24h).

This file is the **financial governor** of the brain.  
It answers:

- “How much are we allowed to spend on this task / day / project?”  
- “How do we estimate cost before we run?”  
- “How do long, multi-hour AntiGravity runs stay under control?”

---

## 1. Core Principles

1. **Everything is metered.**  
   Every agent call logs tokens, cost, and latency in Supabase.

2. **Budget before brilliance.**  
   For any non-trivial task, the Orchestrator should estimate cost *before* starting a deep chain of calls.

3. **Tiered budgets.**  
   Budgets differ by:
   - Zone (`green`, `yellow`, `red`)
   - Task size (`xs`, `s`, `m`, `l`, `xl`)
   - Impact axes (A–E)

4. **Fail safe, not fail open.**  
   When budgets are hit, work pauses or degrades; it does **not** silently keep spending.

5. **Long-horizon runs are planned, not accidents.**  
   3, 5, 9, 12, 24-hour runs have explicit scopes and checkpoints.

---

## 2. Data Model for Tokens & Cost

We extend the `codered` schema with (names are indicative):

- `codered.agent_runs`
  - `provider`
  - `model`
  - `tier`
  - `input_tokens`
  - `output_tokens`
  - `estimated_cost_usd`
  - `latency_ms`
  - `degraded_from_model`
- `codered.llm_usage_daily`
  - `date`
  - `agent_id`
  - `total_input_tokens`
  - `total_output_tokens`
  - `total_cost_usd`
- `codered.llm_usage_by_agent`
  - `agent_id`
  - `window_start`
  - `window_end`
  - `total_cost_usd`
- `codered.llm_degradation_events`
  - `agent_run_id`
  - `from_model`
  - `to_model`
  - `reason`

Budget settings live in:

- `codered.agents`
  - `default_tier`
  - `max_tokens_per_call`
  - `max_calls_per_task`
  - `cost_ceiling_usd_per_task`
- `codered.projects`
  - `max_daily_spend_usd`
  - `max_daily_tokens`
- Optional config file in the repo for AntiGravity (mirrors Supabase but is not the source of truth).

---

## 3. Task-Level Budgeting

### 3.1 Budget Dimensions

For each task, the Orchestrator derives a **budget profile** from:

- `zone`:
  - `green` – safer, cheaper
  - `yellow` – infra/complexity
  - `red` – legal / high risk
- `size`:
  - `xs`, `s`, `m`, `l`, `xl`
- `impact_axes` (A–E):
  - A – Deployability
  - B – Revenue
  - C – Cost reduction
  - D – Organization
  - E – Legal wins / risk

### 3.2 Example Heuristic Table (Per Task)

All numbers are conceptual; real values are set in Supabase.

| Zone   | Size | Base Token Budget | Base Cost Ceiling (USD) |
|--------|------|-------------------|--------------------------|
| green  | xs   | 5k–10k            | $0.10–$0.25              |
| green  | s    | 15k–30k           | $0.50–$1.00              |
| yellow | m    | 40k–75k           | $1.50–$3.00              |
| yellow | l    | 100k–200k         | $4.00–$8.00              |
| red    | m    | 75k–125k          | $3.00–$6.00              |
| red    | l    | 150k–300k         | $6.00–$12.00             |
| red    | xl   | 250k–500k         | $10.00–$25.00            |

Impact axis `E` (legal wins) can bump budget upward within its band.  
Axes `B` (revenue) and `C` (cost reduction) may also justify higher spend.

### 3.3 Orchestrator Responsibilities

When a task enters the pipeline, Orchestrator must:

1. Read project + agent budgets from Supabase.
2. Estimate rough token usage based on:
   - Number of phases required (Architect, Code, Test, Infra, Safety, Cynic).
   - Typical token use per phase (from historical `llm_usage_by_agent`).
3. Assign:
   - `task_token_budget`
   - `task_cost_ceiling_usd`

These are logged on the task and visible in dashboards.

If a single agent run would exceed budget, Orchestrator must:

- Split the task into smaller subtasks, or
- Ask for explicit human override to increase budget.

---

## 4. Agent-Level Budgets

Each agent has built-in ceilings.

### 4.1 Agent Budget Fields

For each agent (e.g., ArchitectAgent, CodeAgent):

- `max_tokens_per_call`
- `max_calls_per_task`
- `cost_ceiling_usd_per_task`
- `default_tier` (Gold / Silver / Bronze; see `llm-routing.md`)

### 4.2 Enforcement

Before an agent call, Orchestrator checks:

1. **Per-call limit** – If the proposed prompt + max_tokens_for_output > `max_tokens_per_call`, then:
   - Compress context,
   - Chunk the work, or
   - Refuse and ask for scope reduction.
2. **Per-task limit** – Sum of all `agent_runs` for that agent on the task must not exceed `cost_ceiling_usd_per_task`.
3. **Task-level budget** – Sum of all agent runs must not exceed `task_cost_ceiling_usd`.

If any limit would be violated:

- Orchestrator either:
  - Downshifts the model tier (see `llm-routing.md`), and/or
  - Splits work into subtasks, and/or
  - Pauses and requires human approval.

---

## 5. Global & Daily Budgets

At the project level:

- `max_daily_spend_usd`
- `max_daily_tokens`

Orchestrator periodically checks usage against these thresholds using `llm_usage_daily`.

### 5.1 Approaching Limits

If usage > 80% of daily budget:

- Orchestrator should:
  - Prefer Bronze or Silver models where safe.
  - Skip non-essential operations (e.g., some Cynic passes on green tasks).
  - Surface a dashboard warning: **“Token budget tight today. Be selective.”**

### 5.2 Exceeding Limits

If usage exceeds a hard cap:

- Orchestrator must:
  - Stop initiating new work that consumes tokens.
  - Allow only “cheap” summary/report calls to close out the day.
  - Notify the human operator that the cap has been hit.

---

## 6. Long-Horizon Runs (1–24 Hours)

AntiGravity is allowed to orchestrate **long-running sequences** (e.g., 3, 5, 9, 12, 24 hours) when explicitly requested.

These runs are **not** free-for-alls. They have structure.

### 6.1 Required Elements

A valid long-horizon run must have:

1. **Run definition** stored in Supabase, e.g. `codered.long_runs`:
   - `id`
   - `project_id`
   - `name`
   - `target_duration_hours` (1–24)
   - `goal_description`
   - `allowed_agents`
   - `max_total_cost_usd`
   - `max_total_tokens`
2. **Checkpoints** (e.g., every N minutes or agent cycles):
   - `codered.long_run_checkpoints`
   - Each checkpoint logs:
     - Progress summary
     - Tokens used so far
     - Cost so far
     - Remaining budget

3. **Stop conditions**, e.g.:
   - Hit cost or token limit,
   - Goal reached early,
   - Error threshold exceeded (too many failures).

### 6.2 Phases of a Long Run

Example structure for a 9-hour run:

1. **Phase 1 – Framing (0–45 min)**  
   - Orchestrator + Architect frame the work, create tasks, set budgets.

2. **Phase 2 – Broad Sweep (45–180 min)**  
   - ResearchAgent + CodeAgent draft initial solutions.
   - TestAgent begins scaffolding tests.

3. **Phase 3 – Refinement (180–480 min)**  
   - CodeAgent + TestAgent iterate on key modules.
   - InfraAgent configures CI/CD.

4. **Phase 4 – Review & Synthesis (480–540 min)**  
   - CynicAgent and SafetyAgent run thorough passes.
   - LibrarianAgent updates docs, lessons, and bug patterns.

5. **Phase 5 – Final Report (540–600 min)**  
   - Orchestrator generates a final summary and to-do list for you.

Each phase consumes a **slice of the total budget**, not the whole thing.

### 6.3 Human-Controlled “Brake”

Long runs must have:

- A configurable pause/stop switch – e.g., a flag you can flip to `paused` in Supabase.
- A “low-fuel” warning when budget hits 70–80% mid-run.

Orchestrator is responsible for checking this flag between phases or after every N agent runs.

---

## 7. Dashboards & Monitoring

Tokens and cost are useless if they’re invisible. We expect at least:

### 7.1 Core Views

- **Daily spend dashboard**
  - Tokens and cost by agent, by project, by zone.
- **Task cost breakdown**
  - Cost per task and per phase (Architect, Code, Test, Infra, Safety, Cynic).
- **Long-run summary**
  - For each long-horizon run:
    - Actual duration,
    - Cost,
    - Key outcomes,
    - ROI tags (“worth it?”).

### 7.2 Alerts

Use simple thresholds and webhooks/email for:

- Daily spend > X% of budget.
- Single task cost > Y USD.
- Long-run at risk of breaching budget.

Alerts should be informational and not spammy. Attach context and suggested actions (e.g., “switch to Bronze for green tasks until reset”).

---

## 8. MVP Criteria for Tokens & Cost Control

We consider this **MVP-complete** when:

1. `agent_runs` records:
   - Provider, model, tier, tokens, estimated cost, latency.
2. `llm_usage_daily` and `llm_usage_by_agent` aggregates run on a schedule.
3. `agents` and `projects` have:
   - Basic budgets (`max_tokens`, `max_daily_spend_usd`, etc.).
4. Orchestrator:
   - Checks budgets before calling agents.
   - Degrades tier or splits tasks when necessary.
   - Logs degradations in `llm_degradation_events`.
5. At least one **long-horizon run** has been executed with:
   - A defined budget,
   - Mid-run checkpoints,
   - A final summary and cost report.

From here, we tune limits with real data and link ROI tags (e.g., revenue saved/earned) to cost so you can see which runs are worth doing again.
