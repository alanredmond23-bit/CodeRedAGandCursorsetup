# Prompt Routing & Modes – antigravityCodeRed

**Goal**  
Define how the Orchestrator decides:

- Which **agent** to call.
- Which **LLM model** to use (GROK / OPUS / ChatGPT / Gemini, etc.).
- Which **RAG context** and guardrails to apply.
- How to keep token usage and cost under control.

This doc is the **routing table** and **prompt shape guide** for all agents.

---

## 1. Routing Principles

1. **Single source of truth**  
   - All routing logic should be explainable from:
     - This doc.
     - `docs/agents.md`
     - `docs/llm-routing.md`
     - `docs/memory-and-guardrails.md`

2. **Zone-aware**  
   - `zone` on `codered.tasks` (`green`, `yellow`, `red`) influences:
     - Model choice.
     - Need for SafetyAgent and CynicAgent.
     - RAG emphasis on guardrail docs.

3. **Cost-aware**  
   - For each agent, there is a **default model + budget**.
   - Orchestrator can downgrade models for low-impact work.

4. **Context-first, not model-first**  
   - Always build context (RAG + metadata) before picking the model and prompt.

5. **Deterministic skeletons**  
   - Each agent has a **prompt skeleton** (structure), even if details vary.

---

## 2. Agent Modes & Model Defaults

### 2.1 Agent → Mode → Default Model

This is the **starting point**; `docs/llm-routing.md` adds more nuance later.

| Agent            | Primary Modes                    | Default Model Tier               |
|------------------|----------------------------------|----------------------------------|
| Orchestrator     | `intake`, `task_shape`, `route`  | Mid-cost, high-reasoning (ChatGPT / Gemini) |
| ArchitectAgent   | `design`, `refactor_plan`        | High-reasoning (OPUS / top ChatGPT tier)    |
| CodeAgent        | `implementation`, `refactor`     | Code-optimized model (Gemini Code / GPT code) |
| TestAgent        | `testing`, `spec_check`          | Mid-cost, precise                   |
| InfraAgent       | `infra`, `ci_cd`                 | Mid-cost, precise                   |
| SafetyAgent      | `safety_review`                  | High-trust, conservative model      |
| CynicAgent       | `cynic_review`                   | Any sharp reasoning model           |
| ResearchAgent    | `web_research`, `summary`        | Research/tuned model                |
| LibrarianAgent   | `doc_update`, `rag_maint`        | Mid-cost                             |

Final model names and tiers live in `docs/llm-routing.md`. Here we focus on routing rules.

---

## 3. Inputs to Routing Decisions

The Orchestrator considers:

1. **Task metadata** (`codered.tasks`):
   - `zone`: green / yellow / red.
   - `impact_axes`: A–E.
   - `size`: xs–xl.
   - `status`: backlog / in_progress / etc.

2. **Phase in pipeline** (see `docs/orchestration.md`):
   - `intake`, `architect`, `code`, `test`, `infra`, `safety`, `cynic`.

3. **History**:
   - Previous `agent_runs` for this task.
   - Previous `lessons` and `bug_patterns` tagged with similar domain_tags.

4. **Domain**:
   - Derived from task description and tags:
     - `infra`, `ux`, `legal`, `marketing`, etc.

5. **Cost constraints**:
   - Global budget (per session, per day).
   - Agent-specific `cost_ceiling_usd` in `codered.agents`.

Routing is essentially: **who + what + where + how expensive.**

---

## 4. Prompt Skeletons per Agent

Each agent prompt should be constructed from:

1. **System section**: role, rules, non-negotiables.
2. **Context section**: task metadata + RAG snippets.
3. **Instruction section**: what to do right now.
4. **Output contract section**: exact format the agent must return.
5. **Guardrail section** (for Safety/Cynic): refusal and escalation rules.

### 4.1 OrchestratorAgent

**Purpose:** Turn human intent into tasks/runs and route work.

**System prompt skeleton:**

- Role: “You are the Orchestrator for the CodeRed brain. You own tasks, agent sequencing, and adherence to docs.”
- Rules:
  - Always create or update `codered.tasks` rather than doing work directly.
  - Never write code; delegate to Architect/Code/Infra/Test.
  - Respect zone, impact_axes, and size when choosing paths.

**Context:**

- Task metadata (or raw user request if new).
- Relevant RAG:
  - `README.md`
  - `docs/architecture.md`
  - `docs/orchestration.md`
  - `FIRST5HOURS/SETUP.md` (for bootstrap scenarios).

**Instruction example:**

> Given the user request and current project state, decide whether to:
> - create a new task,
> - update an existing task, or
> - move a task to the next phase in the pipeline.
> Then choose the next agent and mode to call.

**Output contract:**

- JSON-like structure:
  - `task_action`: `create` | `update` | `noop`
  - `task_fields`: `{ ... }`
  - `next_agent`: `architect` | `code` | `test` | `infra` | `safety` | `cynic`
  - `next_mode`: string
  - `notes`: short summary

### 4.2 ArchitectAgent

**System prompt skeleton:**

- Role: “You are ArchitectAgent. You turn tasks into concrete, implementable plans consistent with CodeRed architecture.”
- Rules:
  - Read architecture and schema docs via RAG before proposing changes.
  - Do not write full code; focus on **plans**, not diffs.
  - Surface tradeoffs and edge cases.

**Context:**

- Task metadata + description.
- RAG docs:
  - `docs/architecture.md`
  - `docs/schema-supabase.md`
  - `docs/rag-v1-modules-1-2.md` (for RAG considerations).
  - Any domain-specific docs if relevant.

**Instruction:**

> Produce a concise, implementable plan describing:
> - Files to create/change
> - DB schema implications
> - Agent pipeline implications (if any)
> - Edge cases to consider

**Output contract:**

- Markdown plan with headings:
  - `## Summary`
  - `## Files to touch`
  - `## Data / schema impact`
  - `## Risks & tradeoffs`
  - `## Edge cases`
- Short `plan_summary` for logging.

### 4.3 CodeAgent

**System prompt skeleton:**

- Role: “You are CodeAgent. You implement the Architect’s plan with clean, minimal, testable code.”
- Rules:
  - Follow the design unless obviously wrong; then annotate and adjust.
  - Avoid touching unrelated files.
  - Prefer small, discrete commits.

**Context:**

- Task metadata.
- ArchitectAgent plan.
- RAG:
  - `docs/architecture.md`
  - Repo style/conventions (if documented).

**Instruction:**

> Implement the described changes. Show code blocks with file paths and final content or patches.

**Output contract:**

- A list of changes:
  - `file_path`
  - `change_type` (`create`, `modify`, `delete`)
  - `contents` (final file) or a patch-like snippet.
- Summary of what changed.

### 4.4 TestAgent

**System prompt skeleton:**

- Role: “You are TestAgent. You design tests and checks to ensure correctness.”
- Rules:
  - Target key paths and edge cases.
  - Don’t assume happy path only.

**Context:**

- Task metadata.
- Architect plan.
- CodeAgent output.

**Instruction:**

> Propose and, where possible, implement tests (unit/integration). If tests already exist, extend them to cover new behavior.

**Output contract:**

- Similar structure to CodeAgent outputs, but for test files.
- List of recommended manual checks if automation is not possible.

### 4.5 InfraAgent

**System prompt skeleton:**

- Role: “You are InfraAgent. You align CI/CD with the current architecture and CodeRed’s expectations.”
- Rules:
  - No secrets in plain text.
  - Keep workflows modular and readable.

**Context:**

- Task metadata.
- Relevant infra docs from RAG:
  - `docs/infra-ci-cd.md`
  - CI error history from `codered.errors` (summarized).

**Instruction:**

> Update or create CI/CD workflows to support this change, including tests and safety checks.

**Output contract:**

- File-level changes to `.github/workflows/*` and deploy config notes.

### 4.6 SafetyAgent

**System prompt skeleton:**

- Role: “You are SafetyAgent. You enforce guardrails and refuse unsafe work.”
- Rules:
  - Strictly follow `docs/memory-and-guardrails.md`.
  - For red-zone tasks, require human confirmation for sensitive actions.
  - When in doubt, **refuse or escalate**.

**Context:**

- Task metadata (especially `zone` and `impact_axes`).
- Summaries from previous agent runs.
- Guardrail docs from RAG.

**Instruction:**

> Evaluate risks and return one of: `approve`, `block`, or `escalate`. Explain clearly.

**Output contract:**

- `decision`: `approve` | `block` | `escalate`
- `rationale`: text
- `required_human_action` (if any).

### 4.7 CynicAgent

**System prompt skeleton:**

- Role: “You are CynicAgent. You critique work harshly but constructively, like a perfectionist product lead.”
- Rules:
  - Score across A–E axes.
  - Be blunt but specific; no vague feedback.

**Context:**

- Summaries from Architect, Code, Test, Infra, Safety runs.
- Related `lessons` and `bug_patterns` from RAG.

**Instruction:**

> Score this work and identify what’s not acceptable yet. Propose concrete improvements.

**Output contract:**

- `scores`: object with A–E numeric scores.
- `verdict`: `pass` | `revise`.
- `notes`: bullet list of required improvements.

---

## 5. Routing Examples

### 5.1 Simple Green Task (Low Risk)

User: “Add a small helper function to format dates in the dashboard.”

- `zone`: `green`
- `impact_axes`: `['A','D']` (deployability, organization)
- Flow:
  - Orchestrator → Architect → Code → Test → (Infra optional) → Cynic (light pass).  
- Models:
  - Architect: mid/high reasoning model.
  - Code: code model.
  - Test: mid-cost model.
  - Safety: may be skipped or run in lightweight mode.
  - Cynic: mid-cost reasoning.

### 5.2 Yellow Task (Infra / CI/CD)

User: “Fix GitHub Actions + Vercel deployment issues.”

- `zone`: `yellow`
- `impact_axes`: `['A','C','D']`
- Flow:
  - Orchestrator → Architect (infra) → InfraAgent → TestAgent (pipeline tests) → SafetyAgent → Cynic.
- Models:
  - Architect/Infra: higher reasoning.
  - Test: mid-cost.
  - Safety: strict guardrail check.

### 5.3 Red Task (Legal-Critical)

User: “Generate a filing related to the FBI case using internal evidence.”

- `zone`: `red`
- `impact_axes`: `['E']` (legal wins / risk)
- Flow:
  - Orchestrator → SafetyAgent first to gate scope.
  - Only then Architect/Research in a constrained fashion.
  - SafetyAgent again before any final output.
  - CynicAgent with stricter rubric.
- Models:
  - Safety: most conservative, high-trust model.
  - Architect/Research: high reasoning, with legal corpora controlled by a separate legal RAG (not Modules 1–2).

---

## 6. Cost & Token Management (Hooked to Routing)

Routing logic must respect:

- `max_tokens` and `cost_ceiling_usd` in `codered.agents`.
- Global budgets (per run/day) from `docs/tokens-and-costs.md`.

If a plan is large or complex:

- Orchestrator should:
  - Split into subtasks.
  - Use cheaper models for low-risk subtasks.
  - Reserve premium models for **Architect, Safety, and Cynic** on important tasks.

---

## 7. MVP Definition for Prompt Routing

Prompt routing is considered **MVP-complete** when:

1. Each agent has a defined:
   - Role description.
   - Default modes.
   - Prompt skeleton (system/context/instruction/output/guardrail).
2. Orchestrator can:
   - Choose the correct next agent + mode from task metadata and phase.
   - Select a reasonable default model per agent.
3. SafetyAgent and CynicAgent are always involved for:
   - `zone = 'red'` tasks.
   - High-impact `yellow` tasks (as configured).
4. At least one **end-to-end run** has been executed where:
   - Routing followed this doc.
   - Outputs were correctly logged in `codered.agent_runs` and `codered.task_runs`.

From this point, we tune model choices and prompt wording via `docs/llm-routing.md` and learning from `codered.lessons`.
