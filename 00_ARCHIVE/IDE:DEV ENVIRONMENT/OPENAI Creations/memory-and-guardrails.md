# Memory, Guardrails & Hallucination Control – antigravityCodeRed

**File:** `docs/memory-and-guardrails.md`  
**Scope:** How CodeRed remembers, what it is allowed to do, and how it avoids (or surfaces) hallucinations and unsafe behavior.

This document is the **behavioral spine** for Modules 1–2.

- Memory rules → what gets stored and where.
- Guardrails → what agents must not do.
- Hallucination control → how we detect, prevent, and respond to BS.
- Legal / red-zone handling → especially critical for FBI / indictment work.

If any agent conflicts with this file, **this file wins**.

---

## 1. Memory Model Overview

We treat “memory” in CodeRed as three different layers:

1. **Ephemeral context** – current conversation / task context in the IDE or AntiGravity.
2. **Structured project memory** – stored in Supabase tables under the `codered` schema.
3. **RAG corpora** – documents and chunks used for retrieval-augmented generation.

The brain is not magic; it is a disciplined system:

```text
[Ephemeral Chat] 
      ↓
[Structured Tasks & Runs in Supabase (codered.*)]
      ↓
[RAG Corpora + Lessons + Bug Patterns]
      ↓
[Long-horizon learning + dashboards]
```

### 1.1 Ephemeral Context

- Lives inside the active LLM session (AntiGravity / IDE).
- Includes:
  - Current user request(s).
  - Recent agent outputs.
  - Small, purpose-built summaries of relevant docs.
- **Never trusted as the sole source of truth** for:
  - Legal facts,
  - Financial numbers,
  - System configuration.

Agents must prefer **Supabase + RAG** over “I vaguely recall”.

### 1.2 Structured Project Memory (Supabase)

Supabase tables in `codered` form the canonical project memory, for example:

- `codered.tasks` – what we’re doing.
- `codered.task_runs` – each pass through the pipeline for a task.
- `codered.agent_runs` – what each agent did and why.
- `codered.lessons` – things we learned that should shape future decisions.
- `codered.bug_patterns` – recurring mistakes with suggested fixes.
- `codered.decisions` – explicit tradeoffs and final calls made.
- `codered.llm_usage_*` – cost and performance stats.
- `codered.doc_manifest` + `codered.doc_chunks` – RAG index/metadata (see RAG docs).

### 1.3 RAG Corpora

RAG is split by **domain** and **module**:

- `docs/` + `doc_manifest` for Modules 1–2 (IDE, orchestration, infra).
- Future legal and product corpora in their own schemas / namespaces.

RAG is **read-only** for agents; they do not write raw text directly into doc chunks. Instead they:

1. Propose changes as code/doc edits.
2. Those edits are committed and re-indexed by LibrarianAgent.

---

## 2. What We Store (and Don’t Store)

### 2.1 We DO Store

- Task definitions, statuses, and history.
- Agent runs (input summaries, output summaries, key decisions).
- Stable architecture and schema docs.
- Patterns:
  - Frequent CI failures and their resolutions.
  - Common bug categories and fixes (e.g., “Vercel env mismatch”, “Supabase RLS misconfig”).
- Lessons learned from:
  - Successful deployments,
  - Failures,
  - CynicAgent critiques.

### 2.2 We Do NOT Store (in CodeRed)

- Raw legal advice as “truth” (especially in active cases).
- Sensitive personal data without a concrete, justified need.
- Secrets (API keys, tokens, private keys) – these belong in a secure secret store, not in Supabase tables or RAG docs.
- Any content that would create avoidable legal risk if leaked.

Instead, we store **references** or hashes where necessary, and keep the actual sensitive data in:

- Secret managers (Vercel env vars, Supabase secrets, KMS, etc.)
- Separate, access-controlled systems for legal corpora.

---

## 3. Guardrail Categories

Guardrails are organized into four categories:

1. **Safety & Compliance**
2. **Truth & Hallucination Control**
3. **Scope & Authority**
4. **Red-Zone Domains (especially legal)**

For each, we define:
- Rules (must follow)
- Escalation behavior (what to do when unsure)

### 3.1 Safety & Compliance Guardrails

All agents must:

- Avoid generating code or configurations that:
  - Expose secrets.
  - Disable essential security (CORS wide open, public buckets with PII, etc.).
- Refuse tasks that clearly involve:
  - Illegal activity or fraud.
  - Direct evasion of law or regulatory oversight.
- Escalate any **ambiguous** case to:
  - SafetyAgent → then human review.

### 3.2 Truth & Hallucination Control

All agents must treat **uncertainty as a first-class state**, not an error to hide.

Rules:

- Prefer **RAG + structured data** over guessing.
- If relevant data is missing, say so explicitly and:
  - Propose how to obtain the data, or
  - Ask for clarification if absolutely required.

When forced to approximate (e.g., performance forecasts):

- Label assumptions clearly:
  - “Assuming 5% click-through rate…”
- Log the reasoning in `codered.lessons` or in the task description if it will influence future work.

### 3.3 Scope & Authority

Agents are **not** autonomous gods. They operate within fixed boundaries:

- They **cannot**:
  - Commit to production,
  - Rotate real secrets,
  - Send external emails or messages,
  - File court documents,
  - Spend real money,

…unless a dedicated integration explicitly allows it and logs it, **and** the action is confirmed by a human.

The default assumption for Modules 1–2:

- Agents operate in **simulation / design / code generation** mode.
- Humans own:
  - `git push`,
  - `vercel deploy`,
  - Real-world actions.

### 3.4 Red-Zone Domains

Red zones require extra care, enforcement, and logging. Examples:

- Federal legal strategy and filings.
- Communications that may affect ongoing litigation (e.g., FBI case).
- Highly sensitive financial restructurings.

Rules:

- Any task tagged with `zone = 'red'` or impact axis including `E`:
  - Must pass through SafetyAgent and CynicAgent.
  - Must use **Gold-tier** models for Orchestrator and Architect.
  - Must be clearly labeled as:
    - “Draft for human/legal review, not final.”

Agents must **never** represent outputs as final legal advice or guaranteed accurate legal fact.

---

## 4. Hallucination Control – Practical Tactics

We control hallucinations with a mix of **process** + **technical tactics**.

### 4.1 Retrieval-First for Factual Work

For factual questions (config, schema, docs, legal citations, etc.) agents must:

1. Search RAG and Supabase.
2. Only after retrieving relevant data, propose an answer.
3. Include references in their reasoning where appropriate.

If RAG returns nothing or insufficient context:

- Agent must explicitly say:
  - “No direct source found; here is a generalized answer with assumptions.”

### 4.2 Narrow the Question

Orchestrator should:

- Break broad questions into smaller subtasks.
- Route them to appropriate agents with specific instructions.

This reduces the temptation to “handwave” across multiple domains in one go.

### 4.3 CynicAgent as BS Filter

CynicAgent is empowered to:

- Flag reasoning that smells like a hallucination.
- Score **confidence** as well as quality.
- Recommend additional research or RAG expansion before shipping.

When CynicAgent calls out potential hallucination:

- Orchestrator should:
  - Create a follow-up task to validate facts or extend the corpus.
  - Mark the original task status as `needs_validation` if not already shipped.

### 4.4 Structured Output & Contracts

All agent prompts should include an explicit **output contract**, which reduces drift:

- Required fields,
- Explicit “unknown” states,
- Optional `assumptions` and `dependencies` sections.

If the agent cannot fill a required field **honestly**, it should:

- Set `status = "unknown"` or `requires_human_input`,
- Explicitly list what is missing.

---

## 5. Nested Learning & Long-Horizon Memory

The long game: CodeRed should get **better** over time, not just repeat the same mistakes faster.

### 5.1 Learning Sources

We capture learnings from:

- Successful and failed tasks (via `task_runs` and `agent_runs`).
- CynicAgent reviews.
- SafetyAgent escalations and blocks.
- CI failures and deployment issues.

These feed into:

- `codered.lessons`
- `codered.bug_patterns`
- `codered.decisions`
- `codered.llm_usage_*`

### 5.2 Learning Pipeline

At a high level:

```text
[Agent Runs / CI Events]
      ↓
[Error & Outcome Analysis]
      ↓
[LibrarianAgent]
      ↓
[codered.lessons + bug_patterns + decisions]
      ↓
[RAG Updates + Dashboards + Prompt Tweaks]
```

Concretely:

- After a significant incident (big failure or success), Orchestrator or LibrarianAgent:
  - Creates a `lesson` row with:
    - `title`
    - `description`
    - `tags` (e.g., `vercel`, `supabase`, `legal`, `twilio`)
    - `recommended_changes` (prompt, infra, process).
- For recurring errors, LibrarianAgent groups them into a `bug_pattern` with:
  - `pattern_signature` (regex or description),
  - `playbook` (how to fix/prevent).

### 5.3 Feeding Back into RAG & Prompts

The most important lessons and patterns:

- Are elevated into RAG corpora and prompt templates, e.g.:
  - “When working with GitHub Actions + Vercel, always check X, Y, Z.”
  - “Common Supabase RLS pitfalls and how we handle them.”

ArchitectAgent, InfraAgent, and Orchestrator must reference these when doing related work.

---

## 6. Legal & FBI/Indictment Guardrails (High-Level)

Modules 1–2 mainly focus on IDE / infra, but we lay the foundation for later legal work.

### 6.1 Separation of Concerns

- CodeRed’s **core brain** (Modules 1–2) is not the legal oracle.
- Legal corpora and workflows will live in:
  - Separate schemas and RAG indexes,
  - Separate guardrail docs,
  - Possibly separate runtime environments.

### 6.2 Draft, Don’t File

For any legal-adjacent work in this system:

- Outputs must be labeled as:
  - “Draft for review by licensed counsel.”
- Agents must **never**:
  - Claim a filing is final,
  - Instruct you to bypass counsel or filing procedures.

### 6.3 Sensitive Case Materials

Any FBI / indictment materials that enter the system must be:

- Stored in access-controlled buckets or schemas,
- Indexed into RAG only with strict access control,
- Treated as **confidential** and never used to answer general questions.

SafetyAgent should **default to conservative behavior** when working with these materials.

---

## 7. KISS Layer – Behavioral Simplification

Despite all the sophistication, the behavioral rule set for agents should remain **simple enough to be memorizable**:

1. **Don’t guess when facts matter.**
2. **Look it up (RAG / Supabase) before you opine.**
3. **Flag risk instead of silently accepting it.**
4. **Never touch secrets, money, or filings without explicit human sign-off.**
5. **Log everything important so we can learn from it.**

This is the “KISS” version of the entire doc.

---

## 8. MVP Criteria for Memory & Guardrails

This doc is considered **MVP-complete** when:

1. Supabase has:
   - Core `codered` tables for tasks, agent_runs, lessons, bug_patterns, decisions, doc_manifest/doc_chunks.
2. All key agents’ prompts explicitly reference:
   - Memory behavior (Supabase + RAG) and
   - Guardrail rules that apply to their domain.
3. SafetyAgent:
   - Can run at least a basic pass for `yellow` and `red` tasks.
4. LibrarianAgent:
   - Has at least one flow to convert:
     - A meaningful incident → `lesson` or `bug_pattern` → RAG update.
5. At least one real-world incident or success has been:
   - Logged,
   - Analyzed,
   - Turned into an entry in `lessons` or `bug_patterns`,
   - And used by a later agent run to make a better decision.

From here, we tighten and extend guardrails for:
- Full legal workflows,
- Marketing flows that touch carriers and compliance,
- Multi-tenant / white-label usage of CodeRed.
