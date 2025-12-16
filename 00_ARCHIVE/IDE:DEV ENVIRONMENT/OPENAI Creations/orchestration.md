# orchestration.md — antigravityCodeRed Orchestration Brain

This document defines **how work flows** inside `antigravityCodeRed` when Antigravity IDE and LLM agents are operating on the repo.

Where `agent.md` defines **who** the agents are and **what** they are allowed to do, this file defines:

- The **lifecycle of a task** (from idea → merged code → deployed system)
- The **default pipelines** (Plan → Code → Test → Review → Infra → Deploy)
- How we handle **greenfield** vs **brownfield** repos
- How we treat **errors, failures, and rollback**
- The **interaction contract** with Antigravity IDE

This is **Module 1: Orchestration Brain (Process)**.

If you are an LLM/agent reading this file:  
Do not skip sections. You are expected to follow this orchestration unless a human overrides you explicitly for a specific task.

---

## 0. Core Orchestration Principles

1. **Everything is a Task**  
   No work happens “freehand.” Every change is anchored to a **task**: an issue, card, ticket, or explicit written prompt.

2. **Task → Plan → Code → Test → Review → Infra → Deploy**  
   The default pipeline applies to almost everything.  
   Skipping stages requires explicit justification and must be surfaced to the human.

3. **Zones First**  
   Every step respects RED / YELLOW / GREEN zones from `architecture.md`.  
   Any attempt to mutate RED ZONE code must be **explicitly scoped** and flagged.

4. **A/B/C/D/E Check at Every Gate**  
   For each task and each PR, the agents must be able to answer:  
   “Which of A (deployment), B (revenue), C (cost), D (organization), E (legal) does this serve?”

5. **PRs, Not Cowboy Commits**  
   - Agents work on **feature branches**, not `main`.  
   - Changes are merged via PR after review + CI, not by direct pushes to `main` (unless a human explicitly says otherwise).

6. **Human is the Final Arbiter**  
   - The human can override any orchestration rule, but you must highlight consequences.  
   - When in doubt on legal, cash, or safety questions, defer.

---

## 1. Task Lifecycle Overview

We define a **Task** as the atomic unit of work. That can be:

- “Implement endpoint X”
- “Wire Supabase table Y”
- “Add metric Z to Twilio dashboard”
- “Add new legal actor table for FBI case”
- “Refactor orchestration to handle new agent”

The lifecycle:

1. **Intake** — task is created and scoped.
2. **Classification** — zone & risk classification (RED/YELLOW/GREEN impact, legal/financial sensitivity).
3. **Planning** — ArchitectAgent designs a small, precise plan.
4. **Implementation** — CodeWriterAgent implements code in correct directories.
5. **Testing** — TestAgent adds/updates and runs tests.
6. **Review** — ReviewAgent checks diffs, zones, and A–E criteria.
7. **Infra & Deploy** — InfraAgent updates workflows/migrations if needed; CI/CD runs.
8. **Post-Deploy** — Optional: monitoring, notes, and next-steps.

Each step has a concrete, expected output and must not be silently skipped.

---

## 2. Intake & Classification

### 2.1 Task Intake

A task may originate from:

- The human (via issue, note, or spoken instruction).  
- A system alert (failing CI, error logs).  
- A SKU module (cashflow, legal, Twilio) requesting a platform change.

At intake, we capture:

- **Title** – concise description.  
- **Description** – details, background, and success criteria.  
- **Type** – feature / bug / refactor / infra / doc.  
- **Risk** – low / medium / high (high if legal/financial-sensitive).  
- **Target zones** – suspected directories / modules impacted.

### 2.2 Zone & Risk Classification

Before any code change is planned, the orchestrator must:

1. Map the task to directories using `docs/architecture.md`.  
2. Determine which zones it touches:
   - RED? YELLOW? GREEN?
3. Mark the risk level:
   - RED zone always at least medium, often high.  
   - Legal / cash changes are high by default.

**Agent behavior:**  
- If the task clearly impacts RED ZONE or legal-critical logic, the orchestrator must:  
  - Explicitly flag it as **HIGH RISK**.  
  - Require a more detailed plan and review.  
  - Potentially require human sign-off before code is written.

---

## 3. Planning Stage (ArchitectAgent)

### 3.1 Responsibilities

**ArchitectAgent** takes the task and produces a **Plan** that includes:

- Objective and constraints.  
- Files and directories to read.  
- Proposed changes (new modules, updated functions, schema changes).  
- Mapping to zones (which files are RED/YELLOW/GREEN).  
- How the change satisfies A/B/C/D/E.  
- Testing strategy (unit, integration, smoke).  
- Infra implications (migrations, CI changes, env vars).

### 3.2 Plan Output Format (Recommended)

ArchitectAgent should emit something like:

```markdown
## Plan

### 1. Goal
Short description of the outcome and why it matters.

### 2. Scope
- Touch `src/services/...` (YELLOW)
- Add new module `src/services/new-...` (GREEN)
- Avoid `src/legacy/...` (RED)

### 3. Steps
1. Read existing code in ...
2. Add new service function in ...
3. Wire new API route in ...
4. Add tests for ...

### 4. A/B/C/D/E Justification
- B (Revenue): ...
- D (Organization): ...

### 5. Tests
- Add unit test: `...`
- Add integration test: `...`

### 6. Infra Considerations
- No schema changes needed. OR
- Add migration: `...`

### 7. Risks / Notes
- Avoid touching RED modules ...
```

This plan should be committed as a comment in the issue/PR description or saved in `docs/plans/` if persistent planning docs are used.

### 3.3 Rules for Planning

- Keep plans small. If the plan looks like “rewrite half the repo”, split the task.  
- Prefer additive changes in GREEN zone over destructive changes in RED.  
- Always specify which zone each step will operate in.

---

## 4. Implementation Stage (CodeWriterAgent)

### 4.1 Responsibilities

**CodeWriterAgent** implements the plan:

- Writes code in appropriate directories/zones.  
- Creates new files for services, endpoints, UI, or orchestrator logic.  
- Maintains consistency with established patterns.  

### 4.2 Implementation Rules

1. **Follow the Plan**  
   - Do not silently expand the scope beyond the ArchitectAgent’s plan.  
   - If you realize the plan is incomplete, request an updated plan rather than improvising large changes.

2. **Respect Zones**  
   - GREEN zone: OK for new work and refactors.  
   - YELLOW zone: OK for changes, but keep refactors scoped and test-backed.  
   - RED zone: Only surgical edits as explicitly allowed by the plan.

3. **Tests Are Not Optional**  
   - For every non-trivial code change, create or update tests.  
   - If you truly cannot add tests (e.g., framework limitations), document why and let ReviewAgent decide.

4. **No Silent Deletions**  
   - Avoid deleting large blocks of code, especially in RED or YELLOW zones, without a clear reason in the plan and the PR description.

---

## 5. Testing Stage (TestAgent)

### 5.1 Responsibilities

**TestAgent** ensures changes are covered and safe:

- Adds or updates tests.  
- Runs the test suite.  
- Reports the status and coverage (if known).

### 5.2 Testing Rules

1. For each planned change, map at least one test that would fail if the change is incorrect.  
2. Prefer fast unit tests where possible; add integration tests for cross-module flows.  
3. Do not downgrade or delete tests for convenience. If tests are flaky, mark them and request follow-up work rather than silently disabling everything.

### 5.3 Reporting

TestAgent must provide a summary, e.g.:

```markdown
## Test Summary

- Added tests:
  - `src/services/__tests__/cashflow.spec.ts`
- Updated tests:
  - `src/api/__tests__/payments.spec.ts`

- Commands run:
  - `npm test`
  - `npm run lint`

- Result:
  - ✅ All tests passing
```

If tests fail, TestAgent should:

- Provide a short explanation.  
- Suggest a next step (fix or further debugging).  
- Not proceed to Review stage as “green” until tests pass or a human explicitly overrides.

---

## 6. Review Stage (ReviewAgent)

### 6.1 Responsibilities

**ReviewAgent** acts as the senior engineer on code review:

- Reviews diffs for correctness, clarity, and zone compliance.  
- Verifies A/B/C/D/E justification.  
- Checks that tests exist and pass.  
- Ensures infra impact is understood.

### 6.2 Review Checklist

ReviewAgent should answer these questions:

1. **Zones:**  
   - Did any change touch RED ZONE?  
   - If yes, was it explicitly scoped and justified?  
   - Is the change as small and reversible as possible?

2. **A/B/C/D/E:**  
   - Is there a clear statement of which of A–E the change satisfies?  
   - Does the change actually support that claim?

3. **Tests:**  
   - Are there tests for new behavior?  
   - Are the tests meaningful (fail if behavior regresses)?

4. **Style & Structure:**  
   - Is the code consistent with existing patterns?  
   - Are there obvious cleanups that don’t violate scope?

5. **Risk:**  
   - Are there hidden gotchas, especially in legal/cash areas?  
   - Should a human review be mandatory before merge?

### 6.3 Outcomes

ReviewAgent can:

- Approve and recommend merge.  
- Request changes (with precise comments).  
- Block and escalate to a human or SafetyAgent if high risk.

---

## 7. Infra & Deploy Stage (InfraAgent)

### 7.1 Responsibilities

**InfraAgent** handles:

- DB schema migrations and Supabase updates.  
- CI/CD workflow updates.  
- Deployment notes and rollout strategy.

### 7.2 Infra Behavior

For changes that require migrations:

1. Create explicit migration files in the appropriate directory.  
2. Ensure migrations are **additive and reversible** where possible.  
3. Document any destructive changes (e.g., dropping a column) and require human confirmation.

For CI/CD changes:

1. Update `.github/workflows/lint-test.yml` or `deploy-vercel.yml` as needed.  
2. Ensure the pipeline remains deterministic and not overly complex.  

### 7.3 Deployment

When a PR is merged to `main`:

- `lint-test.yml` runs on push/PR.  
- `deploy-vercel.yml` runs on push to `main`.  

InfraAgent should ensure:

- Dependencies are installed deterministically.  
- Builds use env vars from Vercel/GitHub secrets.  
- Failures return clear errors, not silent timeouts.

---

## 8. Error Handling & Rollback

### 8.1 CI Failures

If CI fails (lint/test/deploy):

- The orchestrator must **stop further automation** on that branch.  
- TestAgent and/or InfraAgent should:
  - Read logs.  
  - Provide a short summary of the failure.  
  - Propose fixes.  

CI is not bypassed by default. Only a human can decide to merge with a failing pipeline.

### 8.2 Runtime/Production Issues

If a new deploy causes runtime issues:

- The system should lean on:
  - Vercel rollbacks or previous deployments.
  - Git tag/branch `pre-antigravity` or similar if attached to a brownfield repo.

Orchestrator should encourage:

- Small, revert-friendly changes.  
- Clear tagging so that rollback is obvious.

### 8.3 Legal/Critical Issues

If an issue touches:

- Legal strategy.  
- Evidence handling.  
- Financial reporting that may be used in a courtroom or in front of regulators.

Then:

- SafetyAgent should default to blocking automated rollback or fixes without human involvement.  
- A human must confirm the appropriate resolution path, even if it’s technically simple.

---

## 9. Greenfield vs Brownfield Orchestration

### 9.1 Greenfield (New Repo)

For a new `antigravityCodeRed` deployment:

- Zones are simpler (most code is GREEN initially).  
- Orchestrator can be more aggressive in refactoring because there is less legacy risk.  
- The main priority is building a clean spine for future SKUs.

Process is the same, but risk is generally lower.

### 9.2 Brownfield (80% Done Repo)

For an existing repo that Antigravity is attaching to:

1. **Initialize with Architecture & Zones**  
   - Human and/or ArchitectAgent must create `architecture.md` reflecting reality.  
   - Many existing directories will be RED or YELLOW by default.

2. **First Tasks Are Non-Destructive**  
   - Add documentation.  
   - Add logging/instrumentation.  
   - Add tests around existing behavior.  

3. **Introduce New Code in GREEN ZONE**  
   - New SKUs and refactors should start in new modules.  
   - Gradual migration from legacy to new modules is preferred over in-place rewrites.

4. **Track All Major Structural Changes**  
   - Use planning docs and/or separate ADRs (architecture decision records) if needed.

---

## 10. Antigravity IDE Integration Contract

When using Antigravity IDE as the cockpit for this repo, the orchestrator assumes:

1. Antigravity will load this repo and have access to `README.md` and all `docs/*.md`.  
2. Each agent inside Antigravity will:
   - Respect zone rules.  
   - Call the correct stage agent (Architect, CodeWriter, Test, Review, Infra, Safety) by behavior.  
3. Antigravity will work via branches + PRs, not direct `main` pushes, unless the human explicitly orders a fast-path.

Recommended **initial instruction** for Antigravity when opening this repo:

```text
1. Read README.md and all files in docs/.
2. Understand the concepts of RED/YELLOW/GREEN zones and A/B/C/D/E merge rules.
3. When I give you a task, run the orchestration pipeline:
   - Intake & classify (zones + risk)
   - Plan (ArchitectAgent)
   - Implement (CodeWriterAgent)
   - Test (TestAgent)
   - Review (ReviewAgent)
   - Infra/Deploy (InfraAgent)
   - Safety checks (SafetyAgent) before risky operations
4. Never push directly to main. Always work on a branch and open a PR.
5. Never modify RED ZONE code unless I explicitly tell you to and the plan calls it out.
```

---

## 11. Orchestration State Machine (High-Level)

You can treat the orchestration as a simple state machine:

```text
[Task Created]
      |
      v
 [Classify Zones & Risk]
      |
      v
 [Plan Created by ArchitectAgent]
      |
      v
 [Implementation by CodeWriterAgent]
      |
      v
 [Tests by TestAgent]
      |
      v
 [Review by ReviewAgent]
   |           |         \ (changes requested)
   |          v
   |      [back to Implementation]
   v
 [Infra & Deploy by InfraAgent]
      |
      v
 [SafetyAgent Final Check on Risky Ops]
      |
      v
   [Merged & Deployed]
```

Any transition can be intercepted by SafetyAgent and routed back to a human.

---

## 12. Human Override Protocol

At any time, a human can override the orchestration flow. When that happens, the system should:

1. Log the override: what step was skipped or altered, and why.  
2. Surface any risks identified by SafetyAgent or ReviewAgent.  
3. Avoid silently reusing that override as a new default; overrides are specific, not global configuration changes.

Examples of overrides:

- “Merge this even though tests are pending; we need the hotfix now.”  
- “Allow this RED ZONE refactor, I’ve reviewed the plan personally.”  
- “Skip InfraAgent for this doc-only change.”

The orchestration brain’s job is to **make the risk visible**, not to block the CEO when they consciously accept it.

---

This file, combined with `agent.md`, `architecture.md`, and `prompt-routing.md`, defines the full **Orchestration Brain** for `antigravityCodeRed`.  
Agents and tools must treat this as the source of truth for how work flows in this repo.
