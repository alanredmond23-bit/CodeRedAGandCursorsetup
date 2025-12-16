# architecture.md — antigravityCodeRed Architecture & Zones

This document defines the **physical structure** of the `antigravityCodeRed` repository and how that structure maps to:

- RED / YELLOW / GREEN **zones**
- Agent permissions (see `agent.md`)
- Orchestration flows (see `orchestration.md`)
- Future SKUs (cashflow brain, legal war room, Twilio machine, closer bot, etc.)

If you are an LLM/agent or an automated tool:  
You must treat this file as the **source of truth for where work is allowed to happen and how the repo is organized.**

---

## 0. Scope & Naming

**Repo name:** `antigravityCodeRed`

This repo is the **platform spine**, not a single app. It provides:

- Module 1 – **Orchestration Brain** (agents, process, rules)
- Module 2 – **Infrastructure & Repo Skeleton** (structure, CI/CD, Supabase wiring)

All product SKUs (cashflow engine, legal war room, FBI/superseding indictment analysis, Twilio marketing machine, closer bot, etc.) will be added **inside this architecture**, not as separate, unrelated repos.

This document:

- Defines the **intended directory layout** for a greenfield build.  
- Provides a framework to **classify and zone** an existing brownfield repo that is 80% built.  
- Explains how to gradually migrate messy legacy code into this structure *without breaking everything.*

---

## 1. High-Level Mental Model

Conceptually, the repo is divided into layers:

```text
+---------------------------------------------------+
|                     UI Layer                      |
|            (src/ui, public assets, etc.)          |
+------------------------+--------------------------+
|         API Layer      |      Background Jobs     |
|      (src/api)         |   (src/services/* jobs)  |
+------------------------+--------------------------+
|              Domain / Service Layer               |
|                (src/services)                     |
+------------------------+--------------------------+
|              Shared Libraries Layer               |
|       (lib, src/shared, utils, orchestrator)      |
+------------------------+--------------------------+
|             Infra & Integration Layer             |
|   (.github/, migrations/, env, Supabase wiring)   |
+---------------------------------------------------+
```

Zones overlay this structure:

- **RED ZONE** — critical legacy systems, fragile core flows, and legal/financial logic that must not be casually touched.
- **YELLOW ZONE** — currently active services & APIs; changeable but with discipline.
- **GREEN ZONE** — new work and refactors; where we prefer to build SKUs and orchestrator logic.

---

## 2. Baseline Directory Layout (Greenfield Template)

For a *new* `antigravityCodeRed` deployment, the recommended baseline structure is:

```text
antigravityCodeRed/
├── README.md
├── package.json
├── tsconfig.json / jsconfig.json
├── .env.example
├── docs/
│   ├── agent.md
│   ├── orchestration.md
│   ├── architecture.md
│   └── prompt-routing.md
├── src/
│   ├── orchestrator/
│   │   ├── index.ts
│   │   └── pipelines/
│   ├── services/
│   │   ├── platform/
│   │   ├── cashflow/         # future SKU
│   │   ├── legal/            # future SKU
│   │   ├── marketing/        # future SKU (Twilio, funnels)
│   │   └── closer/           # future SKU
│   ├── api/
│   │   ├── health/
│   │   └── v1/
│   ├── ui/
│   │   ├── components/
│   │   ├── pages/ or app/
│   │   └── layouts/
│   ├── shared/
│   │   ├── types/
│   │   └── utils/
│   └── config/
│       └── index.ts
├── lib/
│   ├── supabaseClient.ts
│   ├── logger.ts
│   └── llm/
│       └── client.ts
├── agents/
│   ├── architect.prompt.md
│   ├── codewriter.prompt.md
│   ├── test.prompt.md
│   ├── review.prompt.md
│   ├── infra.prompt.md
│   └── safety.prompt.md
├── migrations/              # optional if using Supabase/SQL migrations
├── .github/
│   └── workflows/
│       ├── lint-test.yml
│       └── deploy-vercel.yml
└── tests/                   # optional; or colocated tests per directory
```

You can adapt this to your preferred framework (Next.js, Nest, Express, etc.), but the **logical layout and zones should remain consistent.**

---

## 3. Zones: Definitions & Mapping

### 3.1 Zone Definitions (Conceptual)

- **RED ZONE (Protected)**  
  - Critical legacy logic (billing, legal, financial, evidence-handling).  
  - Modules whose failure would create serious legal or cash damage.  
  - Highly fragile or poorly-understood code that works today and must not be casually refactored.

- **YELLOW ZONE (Controlled)**  
  - Actively maintained business logic and APIs.  
  - Code you routinely extend and modify, but that still needs discipline.  
  - Errors here are annoying/expensive but not catastrophic if tests and CI are in place.

- **GREEN ZONE (Preferred/New)**  
  - New modules, new SKUs, orchestrator logic, analytics, dashboards.  
  - Internal utilities, documentation, experimental features.  
  - Where we want Antigravity and agents to operate most of the time.

### 3.2 Default Zone Mapping (Greenfield)

For a fresh `antigravityCodeRed` repo **with no legacy baggage**, initial zones are:

| Path / Area                 | Zone   | Rationale                                               |
|----------------------------|--------|---------------------------------------------------------|
| `docs/`                    | GREEN  | Documentation only; safe for agents to extend.         |
| `README.md`                | GREEN  | Top-level docs only.                                   |
| `src/orchestrator/`        | GREEN  | Orchestration logic; central but expected to evolve.   |
| `src/services/platform/`   | YELLOW | Core platform services; important but not legacy yet.  |
| `src/services/*` (new SKUs)| GREEN  | New SKU work; safe to build and iterate.               |
| `src/api/`                 | YELLOW | External contracts; careful changes with tests.        |
| `src/ui/`                  | YELLOW | User-facing; medium risk of regressions.               |
| `src/shared/`              | YELLOW | Shared types/utils; changes ripple; need discipline.   |
| `src/config/`              | YELLOW | Config patterns; tests needed to avoid breakage.       |
| `lib/`                     | GREEN  | Shared libs; safe to extend with tests.                |
| `agents/`                  | GREEN  | Prompt templates; safe to iterate.                     |
| `.github/workflows/*`      | YELLOW | CI/CD; errors hurt deploys; InfraAgent must handle.    |
| `migrations/`              | YELLOW | DB changes; must be additive & reviewed.               |
| `.env.example`             | GREEN  | Template only; real env vars live outside repo.        |

There is **no RED ZONE yet** in a truly greenfield project. RED ZONE emerges when:

- Code is in production and is critical to cash or legal outcomes.  
- Modules become fragile and too risky to change casually.  
- We explicitly mark areas as RED ZONE due to dependency/complexity.

When that happens, you update this file to mark those paths as RED.

---

## 4. Brownfield Mapping (80% Done Repo)

If `antigravityCodeRed` is being **applied to an existing, messy repo**, you must:

1. **Tell the truth** about how your repo actually looks.  
2. Map **current directories** into zones, even if the structure is ugly.  
3. Avoid rewriting everything at once; instead, use this architecture doc as an overlay.

### 4.1 Capture the Real Structure

Start by documenting something like:

```text
src/
├── old/
│   ├── billing/
│   ├── leads/
│   └── reporting/
├── components/
├── pages/
├── api/
└── utils/
```

Then classify:

- `src/old/billing/` → RED (critical billing; legacy; fragile).  
- `src/old/leads/` → YELLOW (important but can be evolved).  
- `src/old/reporting/` → YELLOW or GREEN (depends on impact).  
- `src/components/` → YELLOW.  
- `src/pages/` → YELLOW.  
- `src/api/` → YELLOW.  
- `src/utils/` → YELLOW (may contain cross-cutting helpers).

Update this file with a table like:

```markdown
### 4.1 Brownfield Zone Mapping (Current State)

| Path                      | Zone   | Notes                                              |
|---------------------------|--------|----------------------------------------------------|
| `src/old/billing/`        | RED    | Legacy billing; do not refactor without a plan.   |
| `src/old/leads/`          | YELLOW | Stable but changeable; tests required.            |
| `src/old/reporting/`      | YELLOW | Medium risk; safe with tests.                     |
| `src/components/`         | YELLOW | UI components; safe with visual/testing.          |
| `src/pages/`              | YELLOW | Routing & pages; stable with tests.               |
| `src/api/`                | YELLOW | External contracts; high visibility.              |
| `src/utils/`              | YELLOW | Cross-cutting; be careful with shared deps.       |
```

### 4.2 Introduce the New Structure Slowly

You don’t need to move everything in one pass. Instead:

1. Create new directories that follow the **target** layout:  
   - `src/services/platform/`  
   - `src/services/cashflow/`  
   - `src/services/legal/`  
   - `src/orchestrator/`  
   - `lib/`

2. Mark these as **GREEN** in this file.  
3. New work (SKUs, refactors) should go into these new GREEN directories, even if old code still lives in `src/old/`.

Over time, you can plan migrations:

- Move a slice of logic from `src/old/leads/` → `src/services/marketing/`, one feature at a time.  
- Keep a mapping table of “old location → new location” in `docs/architecture.md` so agents and humans can find things during migration.

### 4.3 Migration Strategy

For each migration:

1. Create a small **migration plan** (could be a section in `architecture.md` or a separate ADR / plan doc):
   - Source paths in RED/YELLOW.  
   - Target paths in GREEN.  
   - Backwards compatibility plan (if any).  
   - Tests needed.

2. Let ArchitectAgent & CodeWriterAgent implement in GREEN.  
3. Only once the new code is tested, carefully decommission old code (if safe).  

Do not let agents “optimize” the entire legacy structure in one pass. That’s how you trigger unintended breakage.

---

## 5. Module Placement Rules (Where Things Go)

### 5.1 Orchestrator & Platform Brain

- **Location:** `src/orchestrator/`, `lib/llm/`, `agents/`.  
- **Zone:** GREEN by default.  
- **Purpose:**  
  - Implement optional code-level orchestrator for tasks, pipelines, and agent coordination.  
  - Provide reusable LLM helpers and wrappers.

Guidelines:

- Orchestrator code should remain **platform-generic** as much as possible.  
- SKU-specific logic (cashflow, legal, Twilio, etc.) belongs in `src/services/<sku>/`, not in `src/orchestrator/`.

### 5.2 Services (Domain Logic)

- **Location:** `src/services/`  
- **Zone:**  
  - `src/services/platform/` → YELLOW  
  - New SKUs like `src/services/cashflow/`, `src/services/legal/` → GREEN initially  
- **Purpose:**  
  - Encapsulate business logic and domain operations.  
  - Serve as the layer between API/UI and infra.

Guidelines:

- APIs should call into services, not reimplement logic.  
- UI should not contain heavy business logic; it should delegate to services.  
- Legal and cash-related services may become **RED** over time as they go into production and are tied to evidence or financial reporting.

### 5.3 API Layer

- **Location:** `src/api/`  
- **Zone:** YELLOW by default.  
- **Purpose:**  
  - HTTP/REST/RPC entrypoints (depending on framework).  
  - Authentication, authorization, routing, input validation.  
  - Delegation to services.

Guidelines:

- Keep APIs thin: minimal request parsing, then call services.  
- Avoid embedding domain logic directly in handlers.  
- Versioned routes (e.g., `src/api/v1/`) help with stability as you iterate.

### 5.4 UI Layer

- **Location:** `src/ui/` (or `app/` + `components/` structure for Next.js).  
- **Zone:** YELLOW by default.  
- **Purpose:**  
  - Components, pages, layouts, visual flows.  
  - Operator dashboards, admin panels, SKU front-ends.

Guidelines:

- No secrets in UI.  
- No direct DB/infra calls from UI – always go through API/services.  
- Visual/UX refinements can be done more aggressively (with tests and/or visual QA).

### 5.5 Shared & Utilities

- **Location:** `src/shared/`, `lib/`.  
- **Zone:**  
  - `lib/` → GREEN by default.  
  - `src/shared/` → YELLOW (because breakage here can ripple).  
- **Purpose:**  
  - Shared types, schemas, validators, utility functions.  
  - Logging, error handling, Supabase clients, LLM clients.

Guidelines:

- Keep shared utils small and focused.  
- Avoid circular dependencies.  
- Be careful changing shared types in YELLOW zone; require tests.

### 5.6 Infra & CI/CD

- **Location:** `.github/workflows/`, `migrations/`, `src/config/`, `.env.example`.  
- **Zone:** YELLOW.  
- **Purpose:**  
  - GitHub Actions workflows.  
  - Database migrations and configuration.  
  - Config helpers pointing to env vars.

Guidelines:

- No secrets committed.  
- Migrations must be reversible where possible.  
- CI/CD changes should be treated as high-impact: broken CI = blocked velocity.

---

## 6. Env & Secrets Architecture

### 6.1 Files

- `.env.example` — **GREEN**; template only.  
- `.env.local` — not committed; local dev only.  
- CI secrets — in GitHub repository settings.  
- Vercel env vars — in Vercel project settings.

### 6.2 Variables (Baseline)

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# Antigravity / LLM
AG_TOKEN=

# Vercel
VERCEL_TOKEN=
VERCEL_ORG_ID=
VERCEL_PROJECT_ID=

# GitHub (optional)
GITHUB_TOKEN=
```

Guidelines:

- All code that talks to Supabase, GitHub, or external APIs must read secrets from env, not hard-coded strings.  
- UI/client-side code may only use explicitly public env vars (`NEXT_PUBLIC_*` or equivalent).  
- Server-side secrets (e.g., `SUPABASE_SERVICE_KEY`) must be used only in API/services and never in client bundles.

---

## 7. Test Layout

You can choose one of two main strategies:

1. **Colocated tests** (recommended for greenfield):
   - `src/services/cashflow/__tests__/...`  
   - `src/api/v1/__tests__/...`  
   - `src/ui/components/__tests__/...`

2. **Central tests folder:**
   - `tests/services/...`  
   - `tests/api/...`  
   - `tests/ui/...`

Whichever you choose, document it here, and keep it consistent.

Zone wise:

- Tests are generally **GREEN**, but changes to **critical test suites** that guard RED ZONE behavior should be treated as **YELLOW** – you don’t casually delete them.

---

## 8. ASCII Overview of Target Architecture

A more detailed snapshot of the *target* structure once SKUs are in play:

```text
antigravityCodeRed/
├── docs/                        (GREEN)
│   ├── agent.md
│   ├── orchestration.md
│   ├── architecture.md
│   └── prompt-routing.md
├── src/
│   ├── orchestrator/            (GREEN)
│   │   ├── index.ts
│   │   └── pipelines/
│   ├── services/
│   │   ├── platform/            (YELLOW)
│   │   ├── cashflow/            (GREEN → may become YELLOW/RED)
│   │   ├── legal/               (GREEN → likely RED as it hardens)
│   │   ├── marketing/           (GREEN/YELLOW)
│   │   └── closer/              (GREEN/YELLOW)
│   ├── api/                     (YELLOW)
│   │   ├── health/
│   │   └── v1/
│   ├── ui/                      (YELLOW)
│   │   ├── components/
│   │   ├── pages/ or app/
│   │   └── layouts/
│   ├── shared/                  (YELLOW)
│   └── config/                  (YELLOW)
├── lib/                         (GREEN)
│   ├── supabaseClient.ts
│   ├── logger.ts
│   └── llm/
│       └── client.ts
├── agents/                      (GREEN)
├── migrations/                  (YELLOW)
├── .github/
│   └── workflows/               (YELLOW)
└── tests/ or **/__tests__/      (GREEN/YELLOW depending on coverage)
```

As legal and financial SKUs mature and go live, selected directories under `src/services/legal/` and `src/services/cashflow/` may be reclassified as **RED** in this file, with precise notes about what can/cannot be changed.

---

## 9. How Agents Should Use This File

When any agent (Architect, CodeWriter, Test, Review, Infra, Safety) starts work, they should:

1. Read this file fully.  
2. Determine whether the task touches:
   - RED ZONE paths.  
   - YELLOW ZONE paths.  
   - GREEN ZONE paths.  
3. Use this classification to decide:
   - How aggressively to refactor.  
   - Whether to request more planning or human review.  
   - How much testing is mandatory.  

If the physical repo structure drifts from this document, the **first job is to update `architecture.md` to match reality** before agents rely on assumptions.

---

## 10. Evolving the Architecture

This document is **not static**. As the system grows:

- When new directories are added:
  - Add them to the zone mapping table.  
  - Mark their initial zone (GREEN by default).

- When modules become critical/fragile in production:
  - Promote them to YELLOW or RED here.  
  - Tighten agent permissions in `agent.md` accordingly.  

- When large migrations complete:
  - Record the new steady state.  
  - Remove old, unused paths from the mapping, or mark them as deprecated.

The goal is that **at any given time**, a human or an LLM can open `architecture.md` and instantly understand:

- Where the important pieces of the system live.  
- Which areas are safe to build in.  
- Which areas require surgical precision or human sign-off.

If it’s not in here, it isn’t real architecture – it’s just tribal knowledge. This file is where that knowledge gets written down.
