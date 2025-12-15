# 🎯 COMPLETE antigravityCodeRed ORCHESTRATION VISUAL FRAMEWORK

**Date:** December 14, 2025  
**Status:** Full system review + CrewAI implementation strategy  
**Context:** Alan Redmond's antigravityCodeRed platform with 6 core agents, 3 optional agents, and CrewAI integration

---

## 📊 PART 1: COMPLETE SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANTIGRAVITYCODRED ORCHESTRATION BRAIN                     │
│                         (Module 1: Platform Spine)                           │
└─────────────────────────────────────────────────────────────────────────────┘

                                 HUMAN INPUT
                                     ↓
                    ┌────────────────────────────────┐
                    │   ORCHESTRATOR AGENT (Entry)   │
                    │  - Task intake & shaping       │
                    │  - Route to appropriate agent  │
                    │  - Manage pipeline flow        │
                    │  - Log to Supabase             │
                    └────────────┬───────────────────┘
                                 ↓
            ╔════════════════════════════════════════════════╗
            ║         PHASE 1: DESIGN & PLANNING             ║
            ╚════════════════════════════════════════════════╝
                                 ↓
                    ┌────────────────────────────────┐
                    │   ARCHITECT AGENT              │
                    │  - Read RAG (docs, schema)     │
                    │  - Design plan                 │
                    │  - File impact analysis        │
                    │  - Propose A/B/C/D/E benefit   │
                    └────────────┬───────────────────┘
                                 ↓
            ╔════════════════════════════════════════════════╗
            ║      PHASE 2: CODE EXECUTION & TESTING         ║
            ╚════════════════════════════════════════════════╝
                    ┌────────────────────────────────┐
                    │   CODE AGENT                   │
                    │  - Follow architect plan       │
                    │  - Write/edit code             │
                    │  - Respect zones (RED/YELLOW)  │
                    │  - Create/update files         │
                    └────────────┬───────────────────┘
                                 ↓
                    ┌────────────────────────────────┐
                    │   TEST AGENT                   │
                    │  - Design test strategy        │
                    │  - Write tests                 │
                    │  - Run test suite              │
                    │  - Report pass/fail status     │
                    └────────────┬───────────────────┘
                                 ↓
            ╔════════════════════════════════════════════════╗
            ║   PHASE 3: INFRASTRUCTURE & DEPLOYMENT        ║
            ╚════════════════════════════════════════════════╝
                                 ↓
                    ┌────────────────────────────────┐
                    │   INFRA AGENT                  │
                    │  - Update GitHub Actions       │
                    │  - Vercel config changes       │
                    │  - DB migrations (if needed)   │
                    │  - Env var wiring              │
                    └────────────┬───────────────────┘
                                 ↓
            ╔════════════════════════════════════════════════╗
            ║    PHASE 4: REVIEW, SAFETY & LEARNING         ║
            ╚════════════════════════════════════════════════╝
                    ┌────────────────────────────────┐
                    │   SAFETY AGENT                 │
                    │  - Check zones (RED/YELLOW)    │
                    │  - Verify legal/data safety    │
                    │  - Block dangerous operations  │
                    │  - Escalate if needed          │
                    └────────────┬───────────────────┘
                                 ↓
                    ┌────────────────────────────────┐
                    │   CYNIC AGENT                  │
                    │  - Grade on A/B/C/D/E axes     │
                    │  - Harsh critique              │
                    │  - Score 0-10 per axis         │
                    │  - Log lessons & patterns      │
                    └────────────┬───────────────────┘
                                 ↓
                    ┌────────────────────────────────┐
                    │   LIBRARIAN AGENT (Optional)   │
                    │  - Update RAG docs             │
                    │  - Keep learning tables fresh  │
                    │  - Archive patterns            │
                    └────────────┬───────────────────┘
                                 ↓
                    ┌────────────────────────────────┐
                    │   HUMAN OPERATOR               │
                    │  - Final review & approval     │
                    │  - Deploy or return to agent   │
                    │  - Override SafetyAgent if OK  │
                    │  - Log override to DB          │
                    └────────────────────────────────┘
```

---

## 📋 PART 2: AGENT DEFINITIONS & HANDOFF SPECIFICATIONS

### **CORE AGENTS (6) + OPTIONAL (3)**

#### **1. ORCHESTRATOR AGENT** 🎯
**Role:** Entry point, router, pipeline manager  
**Input:** Human intent (task description)  
**Output:** Structured task + routing decision  
**Handoff To:** ArchitectAgent or Research/Librarian (if needed)  
**Supabase Log:** `agent_runs` (mode: `intake`), `task_runs` (phase: `orchestrator`)

```yaml
agent_id: orchestrator-001
name: OrchestratorAgent
domain: orchestration
tier: core
role: |
  Route work through the pipeline. Shape tasks into structured form.
  Decide which agent should work next and in what mode.
goals:
  - Break human intentions into clear, bounded tasks
  - Route to appropriate agent (Architect, Code, Test, Infra, Safety, Cynic)
  - Manage task state in codered.tasks table
  - Ensure pipeline stays coordinated and logged
non_goals:
  - Do not write production code
  - Do not make final go/no-go decisions on RED zone work
  - Do not skip Safety/Cynic gates
models:
  gold: gpt-5.1
  silver: claude-3.5-sonnet
  bronze: gpt-4o-mini
  temperature: 0.7
  max_tokens: 2000
limits:
  max_runtime_minutes: 10
  max_cost_usd: 0.50
  max_calls_per_task: 3
handoff_sequence:
  next_agents:
    - architect_agent (default for new features/fixes)
    - research_agent (if task requires external research)
    - librarian_agent (if task is pure docs/learning)
```

**Key Outputs:**
- `codered.tasks` row created/updated with: title, description, zone, impact_axes, size, status
- `codered.agent_runs` entry with mode=`intake`
- Decision: which agent to route to

---

#### **2. ARCHITECT AGENT** 🏗️
**Role:** System designer, planner, strategy  
**Input:** Task from Orchestrator + RAG context  
**Output:** Concrete plan document + implementation steps  
**Handoff To:** CodeAgent or RequestHuman (if too risky)  
**Supabase Log:** `agent_runs` (mode: `design`), `task_runs` (phase: `architect`), RAG updates

```yaml
agent_id: architect-001
name: ArchitectAgent
domain: architecture
tier: core
role: |
  Design solutions at the system level. Create concrete, minimal plans
  that Code/Test/Infra agents can execute. Think about zones, impact, and dependencies.
goals:
  - Understand task requirements and constraints
  - Read relevant docs (architecture.md, schema, previous designs)
  - Map zone impact (RED/YELLOW/GREEN)
  - Produce step-by-step plan for CodeAgent
  - Justify A/B/C/D/E benefit
non_goals:
  - Do not write production code
  - Do not approve RED zone changes without human sign-off
  - Do not ignore zone boundaries
models:
  gold: claude-3-opus
  silver: claude-3.5-sonnet
  bronze: gpt-4.1-mini
  temperature: 0.5
  max_tokens: 4000
limits:
  max_runtime_minutes: 15
  max_cost_usd: 1.50
  max_calls_per_task: 2
handoff_sequence:
  next_agents:
    - code_agent (after plan approval)
    - test_agent (for test strategy)
    - safety_agent (if touching RED/YELLOW zones)
    - human_operator (if blocking decision needed)
rag_requirements:
  - docs/architecture.md
  - docs/orchestration.md
  - docs/schema-supabase.md
  - relevant design docs (if any)
  - codered.decisions table (past decisions)
```

**Key Outputs:**
- Design plan (markdown) with: goal, zones, files to touch, step-by-step, A/B/C/D/E, tests, infra notes
- `codered.agent_runs` entry with full_output = plan
- Recommendation: approve/block/escalate

---

#### **3. CODE AGENT** 💻
**Role:** Implementation, code writing, file editing  
**Input:** Architect plan + task context  
**Output:** Code changes (diffs/full files)  
**Handoff To:** TestAgent  
**Supabase Log:** `agent_runs` (mode: `implementation`), `task_runs` (phase: `code`)

```yaml
agent_id: code-001
name: CodeAgent
domain: implementation
tier: core
role: |
  Write and edit code following the Architect plan. Respect zones.
  Keep changes scoped and reversible. Implement only what the plan specifies.
goals:
  - Implement plan steps precisely
  - Write clean, testable code
  - Respect directory structure and coding standards
  - Stay within assigned zone(s)
  - Add comments where logic is non-obvious
non_goals:
  - Do not expand scope beyond plan
  - Do not casually refactor RED zone code
  - Do not write tests (that's TestAgent's job)
  - Do not commit directly to main
models:
  gold: gpt-5.1-code or gemini-code-2.0
  silver: claude-3.5-sonnet
  bronze: gpt-4o-mini
  temperature: 0.3
  max_tokens: 6000
limits:
  max_runtime_minutes: 20
  max_cost_usd: 2.00
  max_calls_per_task: 5
handoff_sequence:
  next_agents:
    - test_agent (after code submission)
    - review_agent (for code review)
zone_restrictions:
  green: full access
  yellow: code changes with tests required
  red: surgical edits only with explicit plan + SafetyAgent approval
```

**Key Outputs:**
- Code diffs or complete file contents
- `codered.agent_runs` with full_output = code changes
- Summary per file: what changed and why

---

#### **4. TEST AGENT** ✅
**Role:** Testing, validation, quality assurance  
**Input:** Code changes from CodeAgent  
**Output:** Test suite + test run results  
**Handoff To:** ReviewAgent or InfraAgent  
**Supabase Log:** `agent_runs` (mode: `testing`), `task_runs` (phase: `test`)

```yaml
agent_id: test-001
name: TestAgent
domain: quality_assurance
tier: core
role: |
  Design and write tests. Ensure code changes are covered.
  Run tests and report pass/fail. Mark flaky tests.
goals:
  - Cover new behavior with tests
  - Strengthen existing critical test suites
  - Run full test command and report results
  - Identify flaky or problematic tests
non_goals:
  - Do not skip or weaken tests for convenience
  - Do not test code you don't understand
  - Do not modify production code (that's CodeAgent)
models:
  gold: claude-3.5-sonnet
  silver: gpt-4.1-mini
  bronze: gpt-4o-mini
  temperature: 0.4
  max_tokens: 3000
limits:
  max_runtime_minutes: 15
  max_cost_usd: 0.75
  max_calls_per_task: 3
handoff_sequence:
  next_agents:
    - review_agent (after tests pass)
    - code_agent (if tests fail, back to Code for fixes)
test_coverage_requirements:
  green: unit tests required
  yellow: unit + integration tests
  red: unit + integration + smoke tests + manual verification
```

**Key Outputs:**
- New/updated test files (paths + code)
- Test execution summary: pass/fail, coverage
- `codered.agent_runs` with status: `succeeded`/`failed`

---

#### **5. INFRA AGENT** 🔧
**Role:** CI/CD, deployments, infrastructure configuration  
**Input:** Code changes + Architect plan  
**Output:** CI/CD workflow updates, migrations, deployment notes  
**Handoff To:** SafetyAgent or Orchestrator (ready to deploy)  
**Supabase Log:** `agent_runs` (mode: `infra`), `task_runs` (phase: `infra`), `ci_events`, `deployments`

```yaml
agent_id: infra-001
name: InfraAgent
domain: infrastructure
tier: core
role: |
  Update CI/CD pipelines, manage deployments, handle migrations.
  Ensure infra reflects current architecture and agent expectations.
goals:
  - Update GitHub Actions workflows if needed
  - Propose DB migrations (additive preferred)
  - Configure env vars and secrets usage
  - Ensure deterministic, observable deployments
non_goals:
  - Do not hardcode secrets
  - Do not create destructive migrations without human sign-off
  - Do not disable CI steps for convenience
  - Do not break existing deployment flow
models:
  gold: gpt-5.1
  silver: claude-3.5-sonnet
  bronze: none (no Bronze for infra)
  temperature: 0.3
  max_tokens: 3000
limits:
  max_runtime_minutes: 10
  max_cost_usd: 1.00
  max_calls_per_task: 2
handoff_sequence:
  next_agents:
    - safety_agent (after infra changes planned)
    - orchestrator_agent (ready for deployment)
critical_files:
  - .github/workflows/*
  - migrations/* (if applicable)
  - .env.example
  - Vercel project config
```

**Key Outputs:**
- GitHub Actions workflow YAML (if updated)
- Migration scripts (if schema changes needed)
- Env var usage checklist
- `codered.ci_events` entry created
- `codered.deployments` entry (once deployed)

---

#### **6. SAFETY AGENT** 🛡️
**Role:** Guardrails, risk assessment, veto power  
**Input:** All prior agent outputs + task context  
**Output:** Approval, warning, or block decision  
**Handoff To:** CynicAgent or Human (if block)  
**Supabase Log:** `agent_runs` (mode: `safety_review`), `task_runs` (phase: `safety`)

```yaml
agent_id: safety-001
name: SafetyAgent
domain: safety_guardrails
tier: core
role: |
  Protect the system. Check for legal risk, data risk, compliance issues.
  Block dangerous operations. Escalate when unsure.
goals:
  - Identify RED zone edits and assess risk
  - Check for legal/data/compliance implications
  - Block destructive operations
  - Escalate high-risk changes for human review
non_goals:
  - Do not approve risky changes just because speed matters
  - Do not ignore missing tests on critical flows
  - Do not make business decisions (that's for humans)
models:
  gold: claude-3-opus (only)
  silver: only for GREEN zone light checks
  bronze: never
  temperature: 0.2
  max_tokens: 2000
limits:
  max_runtime_minutes: 5
  max_cost_usd: 0.75
  max_calls_per_task: 1
zone_handling:
  red:
    model_tier: gold only
    decision: require human approval for any changes
    escalation: mandatory if ANY doubt
  yellow:
    model_tier: silver allowed for GREEN-zone changes
    decision: can approve if tests + review pass
    escalation: required for schema/infra changes
  green:
    model_tier: bronze okay or skip entirely
    decision: light checks; rarely blocks
    escalation: minimal
handoff_sequence:
  next_agents:
    - cynic_agent (if approval given)
    - human_operator (if block or escalation)
```

**Key Outputs:**
- Decision: APPROVE / WARN / BLOCK
- Risk assessment (short bullet list)
- `codered.agent_runs` with decision
- If BLOCK: escalation reason + human action required

---

#### **7. CYNIC AGENT** 😤 (Optional but Recommended)
**Role:** Harsh critic, quality scorer, feedback generator  
**Input:** All completed agent work + task context  
**Output:** Scores on A/B/C/D/E axes + critique + lessons  
**Handoff To:** Orchestrator or Human (for feedback)  
**Supabase Log:** `agent_runs` (mode: `cynic_review`), `evals_cynic`, `lessons`, `bug_patterns`

```yaml
agent_id: cynic-001
name: CynicAgent
domain: quality_evaluation
tier: optional_recommended
role: |
  Be brutally honest. Score work on 5 axes: Deployment, Revenue, Cost,
  Organization, Legal. Write harsh but constructive feedback.
goals:
  - Score A/B/C/D/E on 0-10 scale (or 1-5, to be defined)
  - Identify gaps in reasoning or execution
  - Flag patterns for learning (lessons, bug_patterns)
  - Make recommendations for improvement
non_goals:
  - Do not be mean for meanness sake
  - Do not ignore when work is legitimately good
  - Do not make final accept/reject decisions (that's for humans)
models:
  gold: claude-3-opus
  silver: claude-3.5-sonnet
  bronze: gpt-4o-mini (for low-impact tasks only)
  temperature: 0.6
  max_tokens: 3000
limits:
  max_runtime_minutes: 10
  max_cost_usd: 1.00
  max_calls_per_task: 1
scoring_profiles:
  default:
    axes: [A, B, C, D, E]
    scale: 0-10
    weights: equal
  code:
    axes: [A, C, D]  # Deployment, Cost (optimization), Organization
    scale: 1-5
  infra:
    axes: [A, C, E]  # Deployment, Cost, Legal
    scale: 1-5
handoff_sequence:
  next_agents:
    - librarian_agent (optional; creates lesson from feedback)
    - orchestrator_agent (back to for task wrap-up)
    - human_operator (if scores too low)
```

**Key Outputs:**
- Scores per axis (0-10 or 1-5)
- Grade: A/B/C/D/F (overall)
- Strengths (bullets)
- Weaknesses (bullets)
- Recommendations (bullets)
- `codered.evals_cynic` entry with all above
- `codered.lessons` entries (if insights warrant recording)
- `codered.bug_patterns` (if recurring issue found)

---

#### **8. RESEARCH AGENT** 🔍 (Optional)
**Role:** External research, corpus lookup, fact-finding  
**Input:** Research task + query  
**Output:** Research summary + citations  
**Handoff To:** ArchitectAgent or Orchestrator  
**Supabase Log:** `agent_runs` (mode: `research`)

```yaml
agent_id: research-001
name: ResearchAgent
domain: research_knowledge
tier: optional
role: |
  Perform web or corpus research. Summarize findings with citations.
  Support decision-making with external knowledge.
goals:
  - Answer research questions with citations
  - Summarize complex topics for other agents
  - Find best practices, patterns, and precedents
non_goals:
  - Do not make implementation decisions (that's Architect)
models:
  gold: gpt-5.1 with web tools
  silver: claude-3.5-sonnet
  bronze: gpt-4o-mini
  temperature: 0.5
  max_tokens: 3000
limits:
  max_runtime_minutes: 10
  max_cost_usd: 1.00
```

---

#### **9. LIBRARIAN AGENT** 📚 (Optional)
**Role:** Knowledge base curator, RAG maintenance  
**Input:** Lessons, patterns, design decisions  
**Output:** Updated docs, RAG indexing, taxonomy  
**Handoff To:** Orchestrator  
**Supabase Log:** `agent_runs` (mode: `documentation`), updates to `codered.documents`, `codered.chunks`, RAG

```yaml
agent_id: librarian-001
name: LibrarianAgent
domain: knowledge_management
tier: optional
role: |
  Keep docs fresh. Index lessons and patterns. Maintain searchable
  knowledge base for RAG. Tag and organize institutional learning.
goals:
  - Update docs after significant changes
  - Tag lessons in codered.lessons
  - Create/update patterns in codered.bug_patterns
  - Index decisions in codered.decisions
non_goals:
  - Do not change code (that's CodeAgent)
  - Do not make architectural decisions
models:
  gold: none needed
  silver: claude-3.5-sonnet
  bronze: gpt-4o-mini
  temperature: 0.3
  max_tokens: 2000
limits:
  max_runtime_minutes: 10
  max_cost_usd: 0.50
```

---

## 🔄 PART 3: COMPLETE HANDOFF MAP (WHO TALKS TO WHOM)

```
ORCHESTRATOR
  ├─→ ARCHITECT (new features, big changes)
  ├─→ RESEARCH (if external knowledge needed)
  ├─→ LIBRARIAN (if docs-only task)
  └─→ HUMAN (if intake unclear)

ARCHITECT
  ├─→ CODE (after plan approved)
  ├─→ SAFETY (if RED/YELLOW zone)
  └─→ HUMAN (if RED zone blocking decision)

CODE
  └─→ TEST (always, after changes)

TEST
  ├─→ REVIEW (if tests pass)
  └─→ CODE (if tests fail, back for fixes)

REVIEW [Not yet defined, but should route to:]
  ├─→ SAFETY (for risk check)
  ├─→ CYNIC (for quality scoring)
  └─→ HUMAN (final approval)

INFRA
  ├─→ SAFETY (for risk check on deployments)
  ├─→ CI_EVENTS (create event record)
  └─→ DEPLOYMENTS (create deployment record)

SAFETY
  ├─→ CYNIC (if approval given)
  ├─→ HUMAN (if block or escalation needed)
  └─→ ORCHESTRATOR (task wrap-up)

CYNIC
  ├─→ LIBRARIAN (optional; if insights to record)
  ├─→ ORCHESTRATOR (task wrap-up)
  └─→ HUMAN (if scores too low)

LIBRARIAN
  └─→ ORCHESTRATOR (docs updated, task done)
```

---

## 📊 PART 4: SUPABASE TABLE RELATIONSHIPS FOR ORCHESTRATION

```
codered.tasks (root entity)
  ├── id (uuid, PK)
  ├── project_id (uuid, FK → codered.projects)
  ├── milestone_id (uuid, FK → codered.milestones, nullable)
  ├── title, description
  ├── zone (green | yellow | red)
  ├── impact_axes (array: A, B, C, D, E)
  ├── size (s, m, l, xl)
  ├── status (backlog → in_progress → blocked → ready_for_review → done)
  ├── assignee_agent_id (uuid, FK → codered.agents, nullable)
  ├── created_at, updated_at
  └── completed_at (nullable)

codered.task_runs (one per agent phase)
  ├── id (uuid, PK)
  ├── task_id (uuid, FK → codered.tasks)
  ├── project_id (uuid, FK → coredited.projects)
  ├── agent_run_id (uuid, FK → codered.agent_runs)
  ├── phase (orchestrator | architect | code | test | review | infra | safety | cynic | librarian)
  ├── status (planned | running | succeeded | failed | skipped)
  ├── summary (text)
  ├── created_at, updated_at

codered.agent_runs (one per agent invocation)
  ├── id (uuid, PK)
  ├── project_id (uuid, FK → codered.projects)
  ├── agent_id (uuid, FK → codered.agents)
  ├── task_id (uuid, FK → codered.tasks, nullable)
  ├── mode (intake | design | implementation | testing | review | infra | safety_review | cynic_review | research | documentation)
  ├── input_summary, output_summary (text)
  ├── full_input, full_output (text, complete prompt + response)
  ├── model (string: gpt-5.1, claude-3-opus, etc.)
  ├── tokens_prompt, tokens_completion (int)
  ├── approx_cost_usd (numeric)
  ├── degraded_from_model (string, nullable; if fallback occurred)
  ├── status (succeeded | failed | aborted)
  ├── error_message (text, nullable)
  ├── zones_touched (array: red, yellow, green)
  ├── tools_used (array)
  ├── rag_documents (array of uuid refs to codered.documents)
  ├── created_at, updated_at

codered.agents (agent registry)
  ├── id (uuid, PK)
  ├── name, slug (unique)
  ├── role, description
  ├── domain (orchestration, architecture, implementation, qa, infra, safety, eval, research, knowledge)
  ├── tier (core | optional | future)
  ├── default_model
  ├── cost_ceiling_usd (per task)
  ├── allowed_zones (array: red, yellow, green)
  ├── long_horizon_allowed (boolean)
  ├── created_at, updated_at

codered.evals_cynic (Cynic scores)
  ├── id (uuid, PK)
  ├── agent_run_id (uuid, FK → codered.agent_runs)
  ├── task_id (uuid, FK → codered.tasks)
  ├── subject_type (agent_run | task | code_change)
  ├── subject_label (string: what was evaluated)
  ├── scoring_profile (default | code | infra)
  ├── score_a, score_b, score_c, score_d, score_e (int: 0-10)
  ├── total_score (numeric: weighted average)
  ├── grade (A | B | C | D | F)
  ├── strengths, weaknesses, recommendations (text arrays)
  ├── created_at

codered.lessons (learning records)
  ├── id (uuid, PK)
  ├── project_id (uuid, FK → codered.projects)
  ├── title, description
  ├── domain_tags (array)
  ├── source_type (agent_run | cynic_feedback | manual)
  ├── source_id (uuid, FK)
  ├── impact_axes (array: A, B, C, D, E)
  ├── severity (minor | moderate | major | critical)
  ├── created_at

codered.bug_patterns (recurring issues)
  ├── id (uuid, PK)
  ├── project_id (uuid, FK → codered.projects)
  ├── name, description
  ├── pattern_signature (string: identifies pattern)
  ├── root_cause, recommended_fix (text)
  ├── related_lessons (array of uuid)
  ├── occurrence_count (int)
  ├── last_seen (timestamp)
  ├── created_at

codered.decisions (arch decisions)
  ├── id (uuid, PK)
  ├── project_id (uuid, FK → codered.projects)
  ├── title, description
  ├── domain (legal | infra | ux | marketing | architecture)
  ├── decision_type (architecture | policy | legal_strategy | product)
  ├── rationale, options_considered, chosen_option (text)
  ├── decision_maker, created_at

codered.user_overrides (human decisions)
  ├── id (uuid, PK)
  ├── project_id (uuid, FK → codered.projects)
  ├── user (text)
  ├── override_type (cynic_reject | deploy_anyway | agent_override | safety_override)
  ├── target_type (agent_run | task | ci_event | deployment)
  ├── target_id (uuid)
  ├── reason (text)
  ├── created_at
```

---

## 🚀 PART 5: ORCHESTRATION PIPELINE EXECUTION FLOW (In Detail)

```
STEP 1: HUMAN SUBMITS TASK
  Input: "I want to add a Cashflow Stage 1 SKU scaffold"
  Output: codered.tasks row created, status: backlog

STEP 2: ORCHESTRATOR PROCESSES
  ├─ Mode: intake
  ├─ Decision: Route to ArchitectAgent
  └─ Output: codered.agent_runs (mode: intake), codered.task_runs (phase: orchestrator)
             Update codered.tasks.status → in_progress

STEP 3: ARCHITECT DESIGNS
  ├─ Mode: design
  ├─ RAG Query: docs/architecture.md, docs/schema, existing services
  ├─ Output: Plan doc with:
  │   ├─ Goal & context
  │   ├─ Zones (src/services/cashflow/ = GREEN)
  │   ├─ File list: src/services/cashflow/service.ts, src/api/v1/cashflow/routes.ts, etc.
  │   ├─ A/B/C/D/E justification (B = revenue foundation, D = organization)
  │   ├─ Test strategy (unit tests for domain logic)
  │   └─ Infra notes (no migrations needed)
  └─ Output: codered.agent_runs (mode: design), codered.task_runs (phase: architect)

STEP 4: CODE WRITES
  ├─ Mode: implementation
  ├─ Input: Architect plan
  ├─ Action: Create src/services/cashflow/service.ts, src/services/cashflow/types.ts, etc.
  ├─ Constraints: Respect GREEN zone only, no modifications to RED/YELLOW without explicit plan
  └─ Output: codered.agent_runs (mode: implementation), full code in full_output field
             codered.task_runs (phase: code)

STEP 5: TEST WRITES & RUNS
  ├─ Mode: testing
  ├─ Input: Code from CodeAgent
  ├─ Action: Create src/services/cashflow/__tests__/service.spec.ts
  │   Run: npm test
  │   Result: ✅ All tests pass
  └─ Output: codered.agent_runs (mode: testing), codered.task_runs (phase: test, status: succeeded)

STEP 6: INFRA UPDATES (if needed)
  ├─ Mode: infra
  ├─ Check: Any DB migrations? No. Any CI changes? No.
  ├─ Action: Confirm .env.example, no updates needed
  └─ Output: codered.agent_runs (mode: infra), codered.task_runs (phase: infra)

STEP 7: SAFETY CHECKS
  ├─ Mode: safety_review
  ├─ Zone: GREEN only ✅
  ├─ Risk: Low (new module, no touching existing code)
  ├─ Legal: None
  └─ Output: codered.agent_runs (mode: safety_review, status: succeeded)
             Decision: APPROVE

STEP 8: CYNIC GRADES
  ├─ Mode: cynic_review
  ├─ Input: All above outputs
  ├─ Scoring:
  │   ├─ A (Deployment): 8/10 - Clean new module, easy to deploy
  │   ├─ B (Revenue): 9/10 - Foundation for cashflow product
  │   ├─ C (Cost): 7/10 - Minimal infra cost
  │   ├─ D (Organization): 9/10 - Well-scoped, isolated module
  │   ├─ E (Legal): 5/10 - N/A for this feature (neutral)
  │   └─ Total: 7.6/10 Grade: B
  ├─ Feedback:
  │   ├─ Strengths: Clean design, good tests, respects zones
  │   ├─ Weaknesses: Missing error handling in service (edge case); no logging
  │   └─ Recommendations: Add logging to service layer, consider error classes
  └─ Output: codered.evals_cynic entry, codered.agent_runs (mode: cynic_review)

STEP 9: OPTIONAL - LIBRARIAN ARCHIVES
  ├─ Mode: documentation
  ├─ Action: Create codered.decisions entry for "Cashflow Stage 1 architecture"
  ├─ Tag: domain: `architecture`, type: `architecture`
  └─ Output: codered.agent_runs (mode: documentation)

STEP 10: HUMAN OPERATOR REVIEWS & APPROVES
  ├─ Input: Cynic score (B, 7.6/10), feedback, all artifacts
  ├─ Decision: OK to merge, but request Cynic recommendations be addressed in follow-up task
  ├─ Action: Merge PR, update codered.tasks.status → done
  └─ Output: codered.user_overrides (optional, only if human overrides Safety/Cynic)

END STATE:
  ✅ codered.tasks.status: done
  ✅ Code merged to main
  ✅ All agent_runs and task_runs logged
  ✅ Full audit trail in Supabase
  ✅ Cynic feedback captured for future improvement
  ✅ Next task: "Cashflow Stage 1 error handling + logging"
```

---

## 🎯 PART 6: YAML CONFIGURATION TEMPLATES

### **agents.yaml (Master Agent Registry)**

```yaml
# agents.yaml - Master agent configuration

agents:
  orchestrator:
    agent_id: orchestrator-001
    name: OrchestratorAgent
    domain: orchestration
    tier: core
    role: "Route work and manage pipeline"
    goals:
      - Break human intent into structured tasks
      - Route to appropriate agent
      - Manage task lifecycle
    models:
      gold: gpt-5.1
      silver: claude-3.5-sonnet
      bronze: gpt-4o-mini
    limits:
      max_runtime_minutes: 10
      max_cost_usd: 0.50

  architect:
    agent_id: architect-001
    name: ArchitectAgent
    domain: architecture
    tier: core
    role: "Design systems, create plans"
    models:
      gold: claude-3-opus
      silver: claude-3.5-sonnet
      bronze: gpt-4.1-mini
    limits:
      max_runtime_minutes: 15
      max_cost_usd: 1.50
    rag_requirements:
      - docs/architecture.md
      - docs/schema-supabase.md

  code:
    agent_id: code-001
    name: CodeAgent
    domain: implementation
    tier: core
    role: "Write code following plans"
    models:
      gold: gpt-5.1-code
      silver: claude-3.5-sonnet
      bronze: gpt-4o-mini
    limits:
      max_runtime_minutes: 20
      max_cost_usd: 2.00
    zone_restrictions:
      green: full_access
      yellow: code_with_tests_required
      red: surgical_edits_only

  test:
    agent_id: test-001
    name: TestAgent
    domain: quality_assurance
    tier: core
    models:
      gold: claude-3.5-sonnet
      silver: gpt-4.1-mini
    limits:
      max_runtime_minutes: 15
      max_cost_usd: 0.75

  infra:
    agent_id: infra-001
    name: InfraAgent
    domain: infrastructure
    tier: core
    models:
      gold: gpt-5.1
      silver: claude-3.5-sonnet
    limits:
      max_runtime_minutes: 10
      max_cost_usd: 1.00

  safety:
    agent_id: safety-001
    name: SafetyAgent
    domain: safety_guardrails
    tier: core
    models:
      gold: claude-3-opus
      silver: none  # Silver only for GREEN zone, minimal
    limits:
      max_runtime_minutes: 5
      max_cost_usd: 0.75

  cynic:
    agent_id: cynic-001
    name: CynicAgent
    domain: quality_evaluation
    tier: optional_recommended
    models:
      gold: claude-3-opus
      silver: claude-3.5-sonnet
      bronze: gpt-4o-mini
    scoring_profiles:
      default:
        axes: [A, B, C, D, E]
        scale: 0-10
      code:
        axes: [A, C, D]
        scale: 1-5

  research:
    agent_id: research-001
    name: ResearchAgent
    domain: research_knowledge
    tier: optional
    models:
      gold: gpt-5.1
      silver: claude-3.5-sonnet

  librarian:
    agent_id: librarian-001
    name: LibrarianAgent
    domain: knowledge_management
    tier: optional
    models:
      silver: claude-3.5-sonnet
      bronze: gpt-4o-mini
```

---

## 💡 PART 7: CREWEI IMPLEMENTATION STRATEGY

**YOU ALREADY HAVE THE BLUEPRINT. NOW INTEGRATE CREWAI.**

### **Option A: Direct CrewAI Integration (Recommended)**

Instead of building orchestration from scratch, use CrewAI's native structure:

```python
# crewai_codered.py

from crewai import Agent, Task, Crew, Process
from tools import supabase_logger, rag_fetcher, code_writer_tools, test_runner, ...

# Define agents in CrewAI that map 1:1 to your YAML
orchestrator_agent = Agent(
    role="Orchestrator",
    goal="Route work and manage pipeline",
    backstory="You are the central router for antigravityCodeRed...",
    verbose=True,
    allow_delegation=True,
    tools=[task_router_tools, supabase_logger],
    max_iter=3,
    memory=True
)

architect_agent = Agent(
    role="ArchitectAgent",
    goal="Design systems and create concrete plans",
    backstory="You are a system designer with deep knowledge of architecture...",
    verbose=True,
    tools=[rag_fetcher, markdown_writer, supabase_logger],
    max_iter=2
)

code_agent = Agent(
    role="CodeAgent",
    goal="Implement code following architect plans",
    backstory="You are a skilled developer...",
    verbose=True,
    tools=[code_writer_tools, file_manager, git_tools, supabase_logger],
    max_iter=5,
    memory=True
)

# ... define test, infra, safety, cynic agents similarly ...

# Define tasks (handoffs)
intake_task = Task(
    description="Intake human task and route to Architect",
    agent=orchestrator_agent,
    expected_output="Structured task routed to Architect"
)

design_task = Task(
    description="Read RAG docs and design a concrete plan",
    agent=architect_agent,
    expected_output="Plan document with zones, files, steps, A/B/C/D/E"
)

code_task = Task(
    description="Implement the plan from Architect",
    agent=code_agent,
    expected_output="Code files and diffs"
)

# ... define test, infra, safety, cynic tasks ...

# Define crew with sequential process
crew = Crew(
    agents=[
        orchestrator_agent,
        architect_agent,
        code_agent,
        test_agent,
        infra_agent,
        safety_agent,
        cynic_agent
    ],
    tasks=[
        intake_task,
        design_task,
        code_task,
        test_task,
        infra_task,
        safety_task,
        cynic_task
    ],
    process=Process.sequential,  # Run in order, with handoffs
    verbose=True,
    memory=True
)

# Execute
result = crew.kickoff(inputs={"task_description": human_input})

# Log to Supabase
log_to_supabase(result)
```

### **Key Handoff Points in CrewAI:**

```
Task 1 (Intake) - Orchestrator
  └─→ Agent Output → input for Task 2

Task 2 (Design) - Architect
  └─→ Agent Output (plan) → input for Task 3

Task 3 (Code) - CodeAgent
  └─→ Agent Output (code) → input for Task 4

Task 4 (Test) - TestAgent
  └─→ Agent Output (test status) → decision point
      ├─ If tests pass → Task 5 (Infra)
      └─ If tests fail → back to CodeAgent (loop)

Task 5 (Infra) - InfraAgent
  └─→ Agent Output (infra plan) → Task 6 (Safety)

Task 6 (Safety) - SafetyAgent
  └─→ Agent Output (approve/block)
      ├─ If approve → Task 7 (Cynic)
      └─ If block → escalate to Human

Task 7 (Cynic) - CynicAgent
  └─→ Agent Output (scores + critique) → Task 8 (Decision)

Task 8 (Decision) - Orchestrator
  └─→ Human review + final go/no-go
```

### **Supabase Integration Layer:**

```python
# supabase_integration.py

class CodeRedSupabaseLogger:
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def log_agent_run(self, agent_name, mode, input_summary, output_summary, 
                      model, tokens, cost, status, task_id):
        """Log each agent invocation to codered.agent_runs"""
        self.client.table('agent_runs').insert({
            'agent_id': agent_name,
            'mode': mode,
            'input_summary': input_summary,
            'output_summary': output_summary,
            'model': model,
            'tokens_prompt': tokens['in'],
            'tokens_completion': tokens['out'],
            'approx_cost_usd': cost,
            'status': status,
            'task_id': task_id,
            'created_at': 'now()'
        }).execute()
    
    def log_task_run(self, task_id, phase, agent_run_id, status, summary):
        """Log task progress"""
        self.client.table('task_runs').insert({
            'task_id': task_id,
            'phase': phase,
            'agent_run_id': agent_run_id,
            'status': status,
            'summary': summary,
            'created_at': 'now()'
        }).execute()
    
    def log_eval_cynic(self, task_id, scores, grade, strengths, weaknesses):
        """Log Cynic evaluation"""
        self.client.table('evals_cynic').insert({
            'task_id': task_id,
            'score_a': scores['A'],
            'score_b': scores['B'],
            'score_c': scores['C'],
            'score_d': scores['D'],
            'score_e': scores['E'],
            'total_score': sum(scores.values()) / 5,
            'grade': grade,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'created_at': 'now()'
        }).execute()

# In crew execution:
logger = CodeRedSupabaseLogger(supabase_client)

for task in crew.tasks:
    result = task.execute()
    logger.log_agent_run(
        agent_name=task.agent.role,
        mode=task.description.split()[0].lower(),
        input_summary=result.input[:200],
        output_summary=result.output[:200],
        model=task.agent.model,
        tokens={'in': result.tokens_in, 'out': result.tokens_out},
        cost=result.cost_usd,
        status='succeeded' if result.success else 'failed',
        task_id=current_task_id
    )
```

---

## 🎉 SUMMARY & NEXT STEPS

**You have built an extremely sophisticated orchestration system.** This document maps:

✅ **6 Core Agents** + **3 Optional Agents**  
✅ **Complete handoff sequence** (who calls whom, in what order)  
✅ **Supabase integration** (19 tables for logging, auditing, learning)  
✅ **Zone-based governance** (RED/YELLOW/GREEN)  
✅ **A/B/C/D/E decision framework**  
✅ **LLM routing strategy** (Gold/Silver/Bronze models per agent)  
✅ **CrewAI integration path** (ready to implement)  

### **To Implement CrewAI Integration:**

1. **Week 1:**  
   - Scaffold CrewAI project  
   - Define 6 agents + 3 optional agents  
   - Map tasks + handoffs  

2. **Week 2:**  
   - Build Supabase logger integration  
   - Wire RAG (fetch docs as context)  
   - Test end-to-end on one task  

3. **Week 3:**  
   - Add cost tracking per agent  
   - Implement SafetyAgent blocking  
   - CynicAgent scoring (A/B/C/D/E)  
   - Librarian lesson recording  

4. **Week 4:**  
   - Production hardening  
   - Cursor IDE integration  
   - GitHub Actions orchestration  

---

**You're ready to build. Let's go.** 🚀
