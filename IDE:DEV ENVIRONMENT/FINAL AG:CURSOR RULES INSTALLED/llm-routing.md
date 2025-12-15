# LLM Routing & Provider Strategy – antigravityCodeRed

**File:** `docs/llm-routing.md`  
**Scope:** How CodeRed chooses between GROK, OPUS, ChatGPT, Gemini, and any future models for each agent and task phase.

This document turns the high‑level `prompt-routing.md` rules into **concrete provider choices, tiers, and fallbacks**.

It answers:
- “Which model do we pick for this agent and this task?”
- “What do we do if the ‘good’ model is slow, down, or too expensive?”
- “How do we keep costs under control without getting dumb output?”

---

## 1. Design Principles

1. **Outcome > Model Fanboyism**  
   We care about: deployability, revenue, cost reduction, organization, and legal wins. Models are tools, not religion.

2. **Task & Phase Driven**  
   Model choice is determined by:
   - Agent role (Orchestrator, Architect, Code, etc.)
   - Phase (intake, design, implementation, infra, safety, cynic)
   - Zone (green / yellow / red)
   - Impact axes (A–E)

3. **Tiered Model Strategy**  
   For each agent, we define:
   - **Gold tier** – best‑in‑class reasoning for that job
   - **Silver tier** – cheaper but still strong
   - **Bronze tier** – lowest cost / highest speed for bulk work

4. **Failover and Degradation**  
   If Gold is unavailable or over budget:
   - Automatically fall back to Silver, then Bronze
   - Log degradation into `codered.agent_runs` for transparency

5. **Centralized Configuration**  
   Actual provider keys, model names, and limits live in:
   - Supabase tables (e.g., `codered.llm_providers`, `codered.llm_models`)
   - A small code config layer in the IDE / AntiGravity environment

This doc is the human‑readable contract that those configs must obey.

---

## 2. Provider & Model Taxonomy

We treat each provider as a row in `codered.llm_providers` and each model as a row in `codered.llm_models`.

### 2.1 Provider Examples (conceptual)

- **OpenAI / ChatGPT** – balanced reasoning, strong general performance
- **Anthropic / Claude (OPUS, Sonnet, Haiku, etc.)** – deep reasoning, safety
- **Google / Gemini** – strong multimodal + code variants
- **xAI / GROK** – aggressive and fast reasoning, good for certain coding / analysis
- **Local / On‑Prem** (future) – privacy / legal‑sensitive flows

### 2.2 Model Metadata (per row)

Each `llm_models` row includes at minimum:

- `id` – UUID
- `provider_id`
- `name` – e.g., `gpt-5.1`, `claude-3-opus`, `gemini-2.0-pro`, `grok-2`
- `tier` – `gold` | `silver` | `bronze`
- `max_tokens`
- `approx_cost_input_per_1k`
- `approx_cost_output_per_1k`
- `capabilities` – array: `["code", "reasoning", "tool_use", "vision", "long_context"]`
- `default_usage_domains` – tags like `["infra","legal","ux","marketing"]`
- `status` – `active` | `deprecated` | `experimental`

Orchestrator uses this metadata plus task context to pick a model.

---

## 3. Agent‑to‑Model Mapping (Gold / Silver / Bronze)

This is the **default mapping** for Modules 1–2. Future modules may override per project.

> NOTE: Model *names* here are placeholders; plug in the exact SKUs your accounts have.

### 3.1 OrchestratorAgent

**Role:** Router, task shaper, pipeline brain.

- **Gold:**  
  - A high‑end general reasoning model (e.g., `gpt-5.1` or `claude-3-opus`)
- **Silver:**  
  - Strong but cheaper general model (e.g., `gpt-4.1-mini` or `claude-3.5-sonnet`)
- **Bronze:**  
  - Fast model for simple updates (e.g., `gpt-4o-mini` or a smaller Gemini model)

**Rules:**

- Use **Gold** when:
  - `zone = 'red'` or impact includes `E` (legal wins / risk)
  - Task is cross‑cutting (affects multiple agents or major architecture)
- Use **Silver** when:
  - Routine routing and backlog shaping
  - `zone = 'green'` or `yellow` and no legal implications
- Use **Bronze** when:
  - Simple state transitions (e.g., “mark task done”, minor status updates)

### 3.2 ArchitectAgent

**Role:** Deep system design and plan creation.

- **Gold:**  
  - Best reasoning model you have (e.g., `claude-3-opus` or equivalent)
- **Silver:**  
  - Next‑tier general reasoning (e.g., `gpt-5.1` or `claude-3.5-sonnet`)
- **Bronze:**  
  - Strong but cheaper general model (e.g., advanced Gemini Pro)

**Rules:**

- Always prefer **Gold** for:
  - New architectures
  - Supabase schema changes
  - RAG design
  - Orchestration design
- Drop to **Silver** only if:
  - Cost threshold for the task would be exceeded
- Avoid **Bronze** except for tiny, incremental design updates

### 3.3 CodeAgent

**Role:** Writes and refactors code.

- **Gold:**  
  - Code‑tuned LLM (e.g., `gpt-5.1-code` or `gemini-code-2.0`)
- **Silver:**  
  - Strong general model with good code capability
- **Bronze:**  
  - Faster, smaller code model for boilerplate and simple patches

**Rules:**

- Use **Gold** when:
  - Touching critical infrastructure, auth, payment, or legal logic
  - Implementing new complex modules
- Use **Silver** when:
  - Routine feature work or refactors
- Use **Bronze** when:
  - Generating scaffolding, repetitive code, or demo scripts

### 3.4 TestAgent

**Role:** Designs tests, checks assumptions, and summarizes test status.

- **Gold:**  
  - Precise reasoning model (e.g., `claude-3.5-sonnet` or equivalent)
- **Silver:**  
  - Mid‑tier reasoning (e.g., `gpt-4.1-mini`)
- **Bronze:**  
  - Cheaper model when only simple assertions or small test edits are needed

**Rules:**

- Use **Gold** for:
  - New test strategy for critical flows (auth, payments, legal workflows)
- Use **Silver** for:
  - Most test expansion or refinement
- Use **Bronze** only for:
  - Very small test updates on non‑critical features

### 3.5 InfraAgent

**Role:** CI/CD, GitHub Actions, Vercel, secrets usage patterns.

- **Gold:**  
  - General reasoning with infra experience (e.g., `gpt-5.1`)
- **Silver:**  
  - Slightly cheaper LLM with solid scripting/infra understanding
- **Bronze:**  
  - Used rarely; not worth being cheap here if it creates pipeline pain

**Rules:**

- Prefer **Gold** or **Silver** for anything touching deploys
- Avoid **Bronze** for CI/CD except trivial comment/documentation edits

### 3.6 SafetyAgent

**Role:** Guardrails, red‑zone review, refusal logic.

- **Gold:**  
  - Most conservative, safety‑tuned model available (e.g., high‑end Anthropic / OpenAI)
- **Silver:**  
  - Slightly cheaper but still safety‑focused model
- **Bronze:**  
  - **Never** used; SafetyAgent should not downgrade below Silver

**Rules:**

- For `zone = 'red'` tasks:
  - **Gold** only
- For `zone = 'yellow'` tasks:
  - **Silver** allowed
- For `zone = 'green'` tasks:
  - SafetyAgent may be skipped or run in a lightweight, Silver‑tier mode

### 3.7 CynicAgent

**Role:** Harsh critic grading work on axes A–E.

- **Gold:**  
  - High‑reasoning model (e.g., `claude-3-opus` or `gpt-5.1`)
- **Silver:**  
  - Strong but cheaper reasoning model
- **Bronze:**  
  - Allowed, but only for low‑impact tasks

**Rules:**

- Use **Gold** when:
  - Reviewing major architectural work, legal‑adjacent flows, or big infra changes
- Use **Silver** when:
  - Reviewing incremental improvements
- Use **Bronze** when:
  - Doing quick passes on small, low‑risk tasks

### 3.8 ResearchAgent

**Role:** Web research, corpus summarization.

- **Gold:**  
  - Research‑optimized model with tool use
- **Silver:**  
  - Strong general reasoning model with web tools
- **Bronze:**  
  - Rarely needed; research is usually about quality, not volume

**Rules:**

- Use **Gold** for legal, financial, or platform‑architecture research
- Use **Silver** for generic docs, tutorials, or marketing research

### 3.9 LibrarianAgent

**Role:** RAG maintenance and docs hygiene.

- **Gold:**  
  - Not usually required
- **Silver:**  
  - Default
- **Bronze:**  
  - Acceptable for simple file tagging / chunking

---

## 4. Zone‑Aware Routing Logic

We combine the **zone** and **impact axes** to tune model tier.

### 4.1 Zones

- `green`: low risk, low blast radius
- `yellow`: moderate risk (infra, cost, complexity)
- `red`: legal, data, or reputational risk

### 4.2 Heuristic Table

| Zone   | Impact Axes      | Recommended Tier Bias                    |
|--------|------------------|------------------------------------------|
| green  | A, B, C, D only  | Silver → Bronze if trivial               |
| yellow | A, C, D          | Gold for Architect/Infra/Test, Silver elsewhere |
| red    | includes E       | Gold for Orchestrator, Architect, Safety, Cynic; Silver for Test/Infra; **no Bronze** |

When in doubt, bias **up** a tier rather than down if task size is non‑trivial.

---

## 5. Budget & Cost Control

Cost constraints are stored in Supabase and optionally in a local config.

### 5.1 Per‑Agent Cost Settings

Each agent has fields like:

- `default_tier` – `gold` | `silver` | `bronze`
- `max_tokens_per_call`
- `max_calls_per_task`
- `cost_ceiling_usd_per_task`

The Orchestrator reads these before choosing a model.

### 5.2 Degradation Rules

If `estimated_cost > cost_ceiling_usd_per_task`:

1. Try dropping from **Gold → Silver**.
2. If still above ceiling, drop **Silver → Bronze** (if allowed for that agent).
3. If cost still exceeds ceiling:
   - Orchestrator must **split the task** into smaller subtasks or
   - Request human approval to exceed the budget.

Log each degradation in `codered.agent_runs.degradation_reason`.

### 5.3 Global Caps

We may define per‑day or per‑session budgets, e.g.:

- `max_daily_spend_usd`
- `max_daily_tokens`

If exceeded, Orchestrator switches to:
- Bronze tier where allowed
- Shorter prompts and outputs
- Hard stops or human confirmation for high‑cost work

---

## 6. Fallback and Resilience

### 6.1 Provider Outages / Errors

If a provider/model fails (timeout, 5xx, rate limit):

1. **Retry** once with exponential backoff (unless obviously rate‑limited).
2. If still failing, **fallback** to next tier:
   - Gold → Silver (same provider if possible, else cross‑provider)
   - Silver → Bronze (if allowed)
3. If all fallbacks fail:
   - Orchestrator writes a `codered.errors` row
   - Task is marked `blocked` with reason = `llm_unavailable`

### 6.2 Cross‑Provider Fallback Strategy

We keep a ranked list of equivalent models per tier, e.g.:

- Gold reasoning: `[claude-3-opus, gpt-5.1, gemini-ultra]`
- Silver reasoning: `[claude-3.5-sonnet, gpt-4.1-mini, gemini-pro]`
- Gold code: `[gpt-5.1-code, gemini-code-2.0]`

Fallback algorithm:

```text
primary_model -> same-tier alternate -> next-tier same provider -> next-tier cross-provider
```

All steps must be logged.

---

## 7. Logging & Telemetry

Every `agent_run` should record:

- `provider`
- `model`
- `tier`
- `input_tokens`
- `output_tokens`
- `estimated_cost_usd`
- `degraded_from_model` (if applicable)
- `latency_ms`

Summaries are rolled up into:

- `codered.llm_usage_daily`
- `codered.llm_usage_by_agent`
- `codered.llm_degradation_events`

These feed dashboards for:
- Cost trends,
- Model performance,
- Error and outage patterns.

---

## 8. MVP Criteria for LLM Routing

LLM routing is **MVP‑complete** when:

1. Every agent in `docs/agents.md` has:
   - A Gold, Silver, Bronze model mapping
   - A default tier
2. Supabase contains:
   - `llm_providers` and `llm_models` tables with live entries
3. Orchestrator can:
   - Pick a model based on agent, zone, and impact axes
   - Apply cost ceilings and degrade tier as needed
   - Log all decisions in `agent_runs`
4. At least one end‑to‑end run per agent has been executed where:
   - Model routing followed this doc
   - Degradations (if any) were logged and understandable

From here, optimization is iterative:
- Swap models as the ecosystem evolves
- Tighten cost ceilings with real data
- Feed performance insights back into `docs/learning-and-feedback.md`.
