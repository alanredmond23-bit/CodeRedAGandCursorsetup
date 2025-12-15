# Orchestration Pipeline – antigravityCodeRed

**Goal**  
Define exactly how work flows through the CodeRed brain from a human intention to shipped, tested code and docs, using the Supabase schema and agents defined in Modules 1 and 2.

This document is the **operational contract** for:

- The Orchestrator agent.
- The supporting agents (Architect, Code, Test, Infra, Safety, Cynic, etc.).
- How they create and update:
  - `codered.tasks`
  - `codered.task_runs`
  - `codered.agent_runs`
  - `codered.ci_events`
  - `codered.deployments`
  - `codered.errors`
  - `codered.lessons` / `codered.bug_patterns` / `codered.decisions`

If this pipeline is followed, the system stays organized, auditable, and repeatable.

---

## 1. Actors in the Pipeline

### 1.1 Human Roles

- **Operator (You)**  
  - Opens tasks, sets priorities, and approves final work.
  - Can override agents (logged in `codered.user_overrides`).

- **Human Dev / Infra** (optional)  
  - Can pair with agents, commit code, tweak infra, and update docs.

### 1.2 Core Agents

These are logical agents (mapped to rows in `codered.agents` and YAML configs):

- **OrchestratorAgent**  
  - Owns the pipeline from “new task” to “ready for human review / deploy”.
  - Decides which agent runs next, in which mode, and with which constraints.
  - Updates `codered.tasks`, `codered.task_runs`, and `codered.agent_runs`.

- **ArchitectAgent**  
  - Defines or updates solution architecture and file-level plans.
  - Creates design docs, diagrams, and implementation notes.
  - Reads RAG v1 (architecture, schema, infra, etc.) before proposing changes.

- **CodeAgent**  
  - Writes or edits application code.
  - Follows the plans from ArchitectAgent and Orchestrator.
  - Ensures changes are localized, testable, and reversible.

- **TestAgent**  
  - Writes/updates tests and performs static/check-style reviews.
  - Verifies assumptions about inputs, outputs, and edge cases.

- **InfraAgent**  
  - Handles GitHub Actions, Vercel config, environment variables, and secrets usage (but not secret values themselves).
  - Ensures pipelines reflect current architecture and agent expectations.

- **SafetyAgent**  
  - Enforces guardrails (legal, privacy, RED zones, etc.).
  - Can veto a change or mark a task as requiring human approval.

- **CynicAgent**  
  - Acts as the harsh reviewer (Steve Jobs’ “this is shit, fix it” mode).
  - Scores work against your 5 axes:
    - A: Easier to deploy
    - B: More revenue
    - C: Saves money
    - D: More organized
    - E: Legal wins / risk reduction
  - Logs feedback into `lessons` and sometimes `bug_patterns`.

- **ResearchAgent**  
  - Does web or corpus research, summarizes findings, and prepares references.

- **LibrarianAgent**  
  - Keeps docs, RAG, and learning tables up to date after significant changes.

---

## 2. High-Level Orchestration Flow

The pipeline is broken into **four macro phases**:

1. **Intake & Shaping** – turning an idea into a structured `task`.
2. **Design & Plan** – defining architecture and concrete changes.
3. **Execution & Testing** – writing code, tests, and infra changes.
4. **Review, Safety, and Learning** – critical review, guardrails, and feedback.

### 2.1 ASCII Overview

```text
[Human Intent]
     |
     v
[Orchestrator] --(create)--> codered.tasks
     |
     v
[ArchitectAgent] -- design --> docs + task_runs + agent_runs
     |
     v
[CodeAgent] -- code changes --> repo + task_runs + agent_runs
     |
     v
[TestAgent] -- tests/checks --> task_runs + agent_runs
     |
     v
[InfraAgent] -- CI/CD config --> repo + ci_events + deployments
     |
     v
[SafetyAgent] -- guardrails --> approve / block / escalate
     |
     v
[CynicAgent] -- critique --> lessons + bug_patterns
     |
     v
[Human Operator] -- final say --> deploy/merge or re-open
```

Every arrow represents at least one **`codered.agent_runs`** row linked to a **`codered.task_runs`** row, so we can trace the entire lifecycle.

---

## 3. Phase 1 – Intake & Shaping

### 3.1 From Intent to Task

When you ask for something (new feature, fix, infra change), OrchestratorAgent must:

1. **Clarify the intent (lightly)**  
   - Optional clarifying questions if needed for scope/impact.
2. **Create or update a `codered.tasks` row**:
   - `project_id`: antigravityCodeRed project.
   - `milestone_id`: if tied to an existing milestone.
   - `title`: concise summary (max ~120 chars).
   - `description`: expanded, but not a novel.
   - `zone`: `green` by default; use `yellow` or `red` if:
     - `yellow` – involves infra, cost, or non-trivial complexity.
     - `red` – touches legal, critical data, or production risk.
   - `impact_axes`: set based on your 5 axes (A–E).
   - `size`: rough estimate (`s`, `m`, `l`, `xl`).
   - `status`: `backlog` → `in_progress` after acceptance.

3. **Log an agent run**  
   - Create a row in `codered.agent_runs` with:
     - `agent_id`: OrchestratorAgent.
     - `mode`: `intake` or `task_shape`.
     - `input_summary`: what you asked.
     - `output_summary`: summary of the created/updated task.
     - `status`: `succeeded` or `failed`.

4. **Create a first `task_run`**  
   - `phase`: `orchestrator`
   - `status`: `succeeded`
   - Links `task_id` and `agent_run_id`.

From here, the task is ready to move into design.

---

## 4. Phase 2 – Design & Plan (ArchitectAgent)

### 4.1 Design Responsibilities

ArchitectAgent must:

- Read the relevant docs via RAG v1:
  - `docs/architecture.md`
  - `docs/schema-supabase.md`
  - `docs/rag-v1-modules-1-2.md`
  - Any related design docs.
- Produce a **concrete plan**, including:
  - Files to touch or create.
  - DB changes (if any).
  - Agent flows (if this task impacts orchestration).
  - Inputs/outputs and edge cases.

### 4.2 Outputs

ArchitectAgent should generate:

- A **design note** (either added to `docs/` or inline in the task description) that includes:
  - Context & goal.
  - Proposed approach.
  - Risks / tradeoffs.
  - Edge cases.
- A `codered.agent_runs` entry:
  - `agent_id`: ArchitectAgent.
  - `mode`: `design`.
  - `output_summary`: short bullet summary.
- A `codered.task_runs` entry:
  - `phase`: `architect`.
  - `status`: `succeeded` (or `failed` if blocked).

If blocked, ArchitectAgent must set `codered.tasks.status = 'blocked'` with a clear reason and propose follow-ups.

---

## 5. Phase 3 – Execution & Testing

### 5.1 CodeAgent

CodeAgent executes the plan:

1. **RAG prep**  
   - Fetch relevant chunks for:
     - Architecture.
     - File conventions.
     - Any related design notes.

2. **Code changes**  
   - Modify code as defined by the plan.
   - Avoid large, sweeping changes across unrelated areas.
   - Adhere to repo style and patterns.

3. **Logging**  
   - `codered.agent_runs`:
     - `agent_id`: CodeAgent.
     - `mode`: `implementation`.
     - `full_input`/`full_output`: recording the prompt + diff summary.
   - `codered.task_runs`:
     - `phase`: `code`.
     - `status`: `succeeded` or `failed` (include summary).

4. **Task state**  
   - Typically keep `tasks.status = 'in_progress'` until tests + safety pass.

### 5.2 TestAgent

TestAgent ensures we don’t ship blind:

1. **Responsibilities**  
   - Write or update tests (unit/integration as appropriate).
   - Consider edge cases from Architect notes.
   - Run test commands (when possible via MCP/tools).

2. **Logging**  
   - `agent_runs`:
     - `agent_id`: TestAgent.
     - `mode`: `testing`.
     - `status`: `succeeded` / `failed`.
     - `error_message`: if tests fail.
   - `task_runs`:
     - `phase`: `test`.
     - `status`: `succeeded` / `failed`.

3. **Failure path**  
   - On failure, TestAgent:
     - Annotates the task with failure details.
     - May create or update `bug_patterns` if a recurring pattern is detected.

### 5.3 InfraAgent

InfraAgent bridges code to CI/CD:

1. **Responsibilities**  
   - Update GitHub Actions workflows.
   - Adjust Vercel project config (build commands, env var usage, etc.).
   - Ensure that CI/CD reflects CodeRed’s expectations (e.g., safety checks, formatting, tests).

2. **Logging**  
   - `agent_runs`:
     - `agent_id`: InfraAgent.
     - `mode`: `infra`.
   - `task_runs`:
     - `phase`: `infra`.
   - Potentially insert/update:
     - `codered.ci_events` for workflow configs.
     - `codered.deployments` after deployments are triggered.

---

## 6. Phase 4 – Review, Safety, and Learning

### 6.1 SafetyAgent

SafetyAgent sits near the end of the pipeline, especially for **yellow** and **red** zone tasks.

1. **Scope**  
   - Check against `docs/memory-and-guardrails.md`.
   - Look for:
     - Legal risk.
     - Data risk.
     - Misuse risk.
   - For red-zone tasks, SafetyAgent must be consulted before final approval.

2. **Outcomes**  
   - `approve` → task can proceed to CynicAgent and human review.
   - `block` → task marked `blocked`, rationale recorded.
   - `escalate` → SafetyAgent requires explicit human override, logged in `user_overrides`.

3. **Logging**  
   - `agent_runs`:
     - `agent_id`: SafetyAgent.
     - `mode`: `safety_review`.
   - `task_runs`:
     - `phase`: `safety`.

### 6.2 CynicAgent

CynicAgent acts as an aggressive reviewer across all axes:

1. **Inputs**  
   - Summaries from Architect, Code, Test, Infra, Safety runs.
   - RAG context from:
     - `docs/learning-and-feedback.md`
     - `codered.lessons`
     - `codered.bug_patterns`

2. **Scoring**  
   - Assigns scores on axes A–E (0–10 or 1–5, to be finalized in `cynic-eval.md`).
   - Writes a short, blunt critique.

3. **Outputs**  
   - `agent_runs`:
     - `agent_id`: CynicAgent.
     - `mode`: `cynic_review`.
     - `output_summary`: scores + short critique.
   - `lessons`:
     - New lesson rows for substantial insights.
   - `bug_patterns`:
     - If recurring mistakes are found.

4. **Gate**  
   - If scores are below thresholds (to be defined), CynicAgent can recommend:
     - “Re-open task” with specific fixes.
     - Or escalate for human decision.

### 6.3 Human Operator & Overrides

Final call is always yours:

- If you accept the work:
  - `codered.tasks.status = 'done'`.
  - Optionally, mark milestone progress.
- If you override Safety or Cynic:
  - A row is added to `codered.user_overrides` explaining:
    - Override type (`deploy_anyway`, `cynic_reject`, etc.).
    - Reason (short text).

---

## 7. Mapping Phases to Tables

### 7.1 Per Phase

Each major phase should at least create/update:

- **Intake & Shaping**
  - `tasks`, `agent_runs`, `task_runs`
- **Design & Plan**
  - `agent_runs`, `task_runs`
  - Optional design doc in RAG
- **Execution & Testing**
  - `agent_runs`, `task_runs`
  - `ci_events` (for test runs triggered by CI)
- **Review & Safety**
  - `agent_runs`, `task_runs`
  - `lessons`, `bug_patterns`
  - `user_overrides` (if needed)

### 7.2 Minimal Contract (MVP)

For a minimal “valid” CodeRed run on any task, we expect at least:

1. One Orchestrator `agent_run` + `task_run` (`phase = orchestrator`).
2. One Architect `agent_run` + `task_run` (`phase = architect`).
3. One Code `agent_run` + `task_run` (`phase = code`).
4. One Test `agent_run` + `task_run` (`phase = test`) – unless explicitly marked non-code task.
5. One Safety `agent_run` + `task_run` (`phase = safety`) for yellow/red tasks.
6. One Cynic `agent_run` + `task_run` (`phase = cynic`) before closing big tasks.

When these exist and `tasks.status = 'done'`, the run is auditable and compliant with Modules 1–2.
