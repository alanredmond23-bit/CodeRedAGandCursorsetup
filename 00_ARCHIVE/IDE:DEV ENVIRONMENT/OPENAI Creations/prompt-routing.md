# prompt-routing.md — antigravityCodeRed Prompt & Agent Routing

This document defines **how you talk to the system**:

- How humans should prompt Antigravity IDE, Cursor, VS Code, or any LLM attached to this repo.
- How tasks should be **routed to the right agent** (Architect, CodeWriter, Test, Review, Infra, Safety).
- How to handle **greenfield** vs **brownfield** work.
- How to separate **platform work (Modules 1–2)** from **SKU work (cashflow, legal, Twilio, closer)**.

If you are a human, this is your **prompt cookbook**.  
If you are an LLM, this is your **routing table and protocol.**

---

## 0. Mental Model

Think of `antigravityCodeRed` as a **control tower**:

- `agent.md` defines the **roles** (agents and their permissions).
- `orchestration.md` defines the **pipeline** (Plan → Code → Test → Review → Infra → Deploy).
- `architecture.md` defines the **map** (directories and zones).
- `prompt-routing.md` (this file) defines the **radio protocol** — who you call, what you say, and how work flows through agents without chaos.

We standardize prompts so that:

- Antigravity / Cursor / VS Code / web agents behave predictably.
- You can reuse the same patterns across projects.
- Every task is explicit: **goal, constraints, zones, and outputs.**

---

## 1. Global System Prompt for This Repo

When you open this repo in **Antigravity**, **Cursor**, or any LLM-powered IDE, you should first set a **global/system prompt** for the workspace.

### 1.1 Recommended Global Prompt

Paste this as the project-level / workspace-level instruction:

```text
You are operating inside the repository "antigravityCodeRed".

This repo is a PLATFORM SPINE, not a single app. It implements:
- Module 1: Orchestration Brain (agents, process, rules)
- Module 2: Infrastructure & Repo Skeleton (structure, CI/CD, Supabase wiring)
Future SKUs (cashflow, legal war room, Twilio machine, closer bot) will plug into this.

You MUST obey the repo docs:
- README.md
- docs/agent.md
- docs/orchestration.md
- docs/architecture.md
- docs/prompt-routing.md  (this file)

Before doing work:
1. Read the docs above and understand RED/YELLOW/GREEN zones and A/B/C/D/E merge criteria.
2. Never assume you can refactor the whole codebase. Work on small, scoped tasks.
3. Never push directly to main. Always use branches and PRs unless I explicitly override.

For every task:
- Classify which zones (RED/YELLOW/GREEN) are touched.
- Run the pipeline: Plan (ArchitectAgent) → Code (CodeWriterAgent) → Test (TestAgent) → Review (ReviewAgent) → Infra/Deploy (InfraAgent) → Safety check.
- Explain which of A/B/C/D/E (Deployment, Revenue, Cost, Organization, Legal) the work serves.

Do not ignore these docs. They are binding for how you behave in this repo.
```

This ensures **any tool** you use understands the architecture, zones, and orchestration rules.

---

## 2. Prompt Structure for Tasks (Human → System)

Every time you ask the system to do work, you should use a **structured task prompt**.

### 2.1 Standard Task Template

Use this pattern, adapted as needed:

```markdown
# Task
Short title of the task.

## Goal
What outcome do we want? (1–3 sentences)

## Context
- Relevant business/legal/tech context.
- Link to any existing files or modules (paths).
- Mention if this is greenfield or touching legacy/brownfield code.

## Zone Impact (guess)
- Likely paths: `src/...`
- Zones: [GREEN only] or [YELLOW + GREEN] or [RED + YELLOW]

## A/B/C/D/E
Which apply?
- A – Deployment (easier/safer/faster deploy)
- B – Revenue (more revenue)
- C – Cost (lower infra or human cost)
- D – Organization (cleaner, clearer, more maintainable)
- E – Legal (improves our legal/compliance posture)

## Constraints
- Languages/frameworks (TypeScript, Next.js, Supabase, etc.).
- No breaking changes to X if you know them.
- Time/risk constraints.

## Output
What you expect back (plan, code diff, tests, CI updates, etc.).
```

This gives the orchestrator everything it needs to route work through the agents correctly.

### 2.2 Micro-Task Template (Fast Mode)

For small or obvious tasks:

```text
TASK: <one line>
CONTEXT: <where in repo, high-level constraints>
ZONES: <GREEN | YELLOW | RED + YELLOW>
A/B/C/D/E: <letters>
OUTPUT: <plan | code | tests | mixed>
```

Even this stripped-down form is better than “fix this file.”

---

## 3. Agent Routing Patterns

You rarely need to name agents explicitly, but it can help, especially in Antigravity. This section defines **how to instruct the system to call the right agent behaviors.**

### 3.1 “Architect First” Pattern

When you’re starting anything non-trivial, you want a **plan before code**.

**Prompt example:**

```text
[MODE: ARCHITECT]

Use docs/agent.md, docs/orchestration.md, and docs/architecture.md.

Task: I want to add a basic "Cashflow Stage 1" SKU scaffold: services, API, and minimal UI stub.

Please:
1. Classify zone impact (paths and RED/YELLOW/GREEN).
2. Draft a small, concrete plan that fits in 6–10 steps max.
3. Map each step to: files to read, files to edit/create, agent(s) involved.
4. Explain how this satisfies A/B/C/D/E.

Output as markdown under headings: Goal, Zones, Plan, A–E, Tests, Infra.
```

This tells the system: **behave like ArchitectAgent**, not as a freeform coder.

### 3.2 “Implementation” Pattern (CodeWriterAgent)

Once you approve the plan:

```text
[MODE: CODE]

Use the last approved plan from ArchitectAgent.

Implement only STEPS 1–3 in that plan, nothing else.
- Respect zones from docs/architecture.md (do not edit RED areas).
- Add or update tests for any new behavior.
- Make changes as diffs/patches or complete file contents as needed.

Output:
1. Summary of what you changed.
2. For each file: path + before/after summary.
3. Full code blocks for any new or heavily modified files.
```

The key is to enforce **scope**: reference the plan and limit which steps to implement.

### 3.3 “Testing” Pattern (TestAgent)

```text
[MODE: TEST]

Given the recent code changes (summarize or link paths):
1. List all behaviors that must be covered by tests.
2. Add or update tests in the appropriate test directories.
3. Run through the test strategy and tell me which commands to run locally (npm scripts).

Output:
- Test plan
- Specific test files to create or modify (paths)
- Full test code for new tests
- "Test Summary" section at the end
```

### 3.4 “Review” Pattern (ReviewAgent)

```text
[MODE: REVIEW]

Act as ReviewAgent per docs/agent.md.

Given these diffs (or file paths and new code):
1. Check zone compliance (no unapproved RED ZONE edits).
2. Check A/B/C/D/E justification.
3. Check that tests exist and are adequate.
4. Identify any obvious issues (style, clarity, coupling).

Output:
- "Verdict: APPROVE" or "Verdict: CHANGES NEEDED"
- If changes needed, list them in bullet points.
- If approved, summarize why this is safe and valuable.
```

### 3.5 “Infra” Pattern (InfraAgent)

```text
[MODE: INFRA]

Task: Update CI/CD and migrations as needed for the last changes.

Steps:
1. Identify if DB schema changes are required.
2. If yes, specify migration files to create (path + content at high level).
3. Check whether .github/workflows needs to be updated.
4. Ensure env vars and secrets are still correct.

Output:
- Infra plan
- Proposed migration script outlines or code
- Any workflow yaml changes
```

### 3.6 “Safety” Pattern (SafetyAgent)

```text
[MODE: SAFETY]

Given the following planned or completed changes:
- <summary or diff>

Check for:
1. RED ZONE edits (legal/cash-critical, see architecture.md).
2. Large deletions, structural rewrites, or interface changes.
3. Any effects on legal evidence, financial reporting, or compliance.

If anything looks risky:
- Say "BLOCK" and explain why.
- Recommend that a human review and approve before merging or deploying.
```

You can use these modes explicitly or implicitly by describing the behavior you want (“Act as ArchitectAgent…”).

---

## 4. Routing by Scenario

This section gives you **ready-made patterns** for common real-world scenarios.

### 4.1 Scenario: New SKU Scaffold (Cashflow Stage 1)

Goal: use Antigravity to scaffold the first version of the Cashflow app inside this platform.

**Step 1 – Architect**

```text
[MODE: ARCHITECT]

Task: Scaffold "Cashflow Stage 1" SKU inside antigravityCodeRed.

Goal:
- Create src/services/cashflow/ with a basic domain model and stub functions.
- Add an API endpoint under src/api/v1/cashflow/.
- Add a minimal UI stub (dashboard card / page) referencing cashflow data.
- No DB persistence yet; in-memory or mocked.

Zones: GREEN only (no touches to any RED code; see architecture.md).

A/B/C/D/E:
- B (Revenue): lays foundation for cashflow product.
- D (Organization): keeps SKU isolated in its own module.

Output: Concrete plan + file paths, tests to add, infra notes.
```

**Step 2 – CodeWriter**

```text
[MODE: CODE]

Use the last approved Cashflow Stage 1 plan.

Implement only:
- Service stubs in src/services/cashflow/
- API endpoint in src/api/v1/cashflow/
- Minimal UI entry point (page/component) under src/ui/

Constraints:
- Zone: GREEN directories only.
- Provide full code for any new files.
- Write TS types where useful but keep it simple.

Output: Summary + code.
```

**Step 3 – Test & Review**: use the TEST and REVIEW patterns above.

### 4.2 Scenario: Legal War Room / FBI Superseding Indictment

Goal: you’re building a **high-risk, legal-critical** module.

**Step 1 – Architect with Legal Sensitivity**

```text
[MODE: ARCHITECT]

Task: Create initial "Legal War Room" module for FBI superseding indictment analysis.

Context:
- This will eventually hold evidence tables, actor maps, timelines, and legal reasoning helpers.
- High legal sensitivity; any bugs or data loss are unacceptable.

Zones:
- Place new code in GREEN: src/services/legal/ and supporting libs.
- Treat all future "legal war room" code as candidate RED once live.

A/B/C/D/E:
- D (Organization): organizes legal reasoning and data.
- E (Legal): must improve legal clarity, not harm it.

Constraints:
- NO destruction of any existing legal-related code or data.
- Design with explicit auditability and traceability.

Output:
1. Directory layout and file plan for src/services/legal/.
2. List of future tables/entities (actors, cases, motions, exhibits).
3. Safety considerations that must be baked in from day 1.
```

**Step 2 – CodeWriter**: strictly follow the plan, stay in GREEN zone, minimal logic, heavy comments about legal criticality.

**Step 3 – SafetyAgent mandatory** before any deploy.

### 4.3 Scenario: Attaching to Existing Repo at 80% Completion

Goal: Antigravity joins mid-project; you don’t want it nuking your work.

**Prompt pattern:**

```text
You are attaching to a brownfield repo that is ~80% complete.

1. Read README.md and all docs in docs/ (especially architecture.md).
2. Using architecture.md, classify existing directories into RED/YELLOW/GREEN. If needed, propose updates to architecture.md only (no code changes yet).
3. Do NOT refactor anything. Your first tasks are:
   - Add documentation where missing.
   - Add tests for existing critical paths.
   - Add non-invasive logging/instrumentation if needed.

Output:
- Updated architecture mapping (in markdown) that I can paste into docs/architecture.md.
- A short list of safe "first tasks" for Architect/CodeWriter/Test that do NOT change behavior.
```

From there, you move task-by-task with the structured templates.

---

## 5. Prompt Libraries & Patterns to Borrow From

We are effectively building our own small **prompt library** structured around:

- Modes (ARCHITECT, CODE, TEST, REVIEW, INFRA, SAFETY)
- Zones (RED/YELLOW/GREEN)
- A/B/C/D/E motivations

When designing new prompts, follow these patterns:

### 5.1 “Four Pillars” Pattern

Every good prompt should make clear:

1. **Goal** – What we want.  
2. **Constraints** – What we must avoid.  
3. **Context** – Where this lives in the repo.  
4. **Output Format** – Exact shape of the response.

Example:

```text
GOAL: Add metric X to the Twilio dashboard.
CONSTRAINTS: No changes to RED ZONE paths; keep DB schema unchanged.
CONTEXT: Dashboard lives in src/ui/... and pulls data from src/services/marketing/...
OUTPUT: 
- Short plan
- Code changes (with file paths)
- New tests
```

### 5.2 “Zone Guardrails” Pattern

Always remind the system of zones, especially for risky work:

```text
Zones:
- You may work in GREEN and YELLOW only.
- You must NOT touch any RED ZONE paths listed in docs/architecture.md unless I explicitly list them in this task.

If you think you need a RED ZONE change, stop and propose a separate plan.
```

### 5.3 “Diff-First” Pattern (for IDE-integrated tools)

When working from real diffs (Cursor / AG change sets):

```text
Task: Review and refine the following diffs.

Context:
- Repo: antigravityCodeRed
- Zones: Use docs/architecture.md to identify zone for each file.

Steps:
1. For each diff, identify zone and risk.
2. Suggest minimal improvements or request changes as ReviewAgent.
3. Do not expand scope beyond these diffs.

Output:
- Per-file review comments.
- Overall verdict (approve / changes needed).
```

### 5.4 “One-File-at-a-Time” Pattern (Token-Aware)

When you want to avoid huge context blowouts, especially in web ChatGPT:

```text
We will work one file at a time to avoid blowing context.

Step 1: I will paste README.md. You will summarize only what matters for this task.
Step 2: I will paste docs/agent.md. You will extract only agent rules relevant to this task.
Step 3: I will paste <file>. You will apply the rules and modify only this file.

You must:
- Not hallucinate content from files you have not seen.
- Ask me for specific file paths when needed, not "the whole repo".
```

You can use this pattern for dangerous large repos.

---

## 6. IDE-Specific Usage (Antigravity, Cursor, VS Code)

### 6.1 Antigravity IDE

Antigravity is the **primary cockpit** for executing this repo’s vision.

**Recommended setup:**
- Project-level system prompt = Section 1.1 above.  
- Saved prompt snippets for modes: ARCHITECT, CODE, TEST, REVIEW, INFRA, SAFETY.  
- Separate workflows for:
  - “New SKU Scaffold” (e.g., cashflow, legal).  
  - “Attach to Existing Repo”.  
  - “Refactor with Zone Guardrails”.

Make sure Antigravity is aware that:

- It must never silently rewrite entire directories.  
- It must open PRs, not commit directly to main.

### 6.2 Cursor

For **Cursor** or similar IDE copilots:

- Store key prompts as “Custom Instructions” or snippets:  
  - `AG-ARCH` – Architect prompt.  
  - `AG-CODE` – CodeWriter prompt.  
  - `AG-TEST` – Test prompt.  
  - `AG-REVIEW` – Review prompt.

You can then type:

```text
AG-ARCH: Plan the following task in antigravityCodeRed with zones + A/B/C/D/E...
```

Cursor will expand it and you fill in the task details.

### 6.3 VS Code + Chat Plugins

If you use VS Code with an LLM plugin:

- Pin the global repo prompt.  
- Use task templates from Section 2 in comments inside issues or TODO files.  
- Select files or code blocks and invoke specific modes (“Review this change as ReviewAgent,” etc.).

---

## 7. When to Escalate to Human Judgment

The prompts in this file are powerful, but there are cases where the system should **not** be allowed to auto-merge or auto-deploy.

You should explicitly say so in prompts when any of these apply:

- Anything touching **legal war room**, FBI case structures, or evidentiary data.  
- Anything changing **financial reporting**, billing flows, or cashflow calculations.  
- Major structural refactors across multiple services.  
- Deleting or massively altering any path marked RED in `architecture.md`.

Pattern:

```text
This is a HIGH-RISK task.

You may PLAN and PROPOSE changes, but you may NOT:
- Merge PRs
- Run destructive migrations
- Delete RED ZONE code

Your job is to surface risks, propose options, and then stop for human review.
```

Let the AI be the architect and analyst; let the human be the one who swings the axe.

---

## 8. Quick-Start Cheat Sheet

When you’re tired and just want to get going, use this **minimal cheat sheet**:

```text
1) New feature / SKU:
   - ARCHITECT: "Plan this in antigravityCodeRed, respect zones, A/B/C/D/E."
   - CODE: "Implement steps 1–3 from the plan, GREEN/YELLOW only, with tests."
   - REVIEW: "Review diffs, zones, tests, and A/B/C/D/E. Verdict + comments."

2) Brownfield repo:
   - "First, map current directories to RED/YELLOW/GREEN; output table for architecture.md.
      No code changes yet."

3) Legal / FBI / superseding indictment:
   - "Treat as HIGH-RISK LEGAL. Only plan & scaffold in GREEN. No data loss, no destructive edits.
      SafetyAgent must block anything ambiguous; human approval required."

4) Cashflow:
   - "New code in src/services/cashflow/, src/api/v1/cashflow/, and optional UI stub.
      GREEN only until stable; then promote to YELLOW/RED as needed."

5) Twilio / marketing war machine:
   - "New code under src/services/marketing/ and associated APIs/UI.
      Respect compliance and logging; avoid touching legal or billing modules without explicit permission."
```

Tape this cheat sheet to your mental whiteboard. Everything else in this file is detail and nuance layered on top.

---

This file completes the **Orchestration Brain** quartet with:

- `agent.md` — who the agents are.
- `orchestration.md` — how work flows.
- `architecture.md` — where things live and how risky they are.
- `prompt-routing.md` — how you talk to the system so it does the right thing.

Use it ruthlessly. If a prompt doesn’t look like it fits these patterns, fix the prompt before you blame the model.
