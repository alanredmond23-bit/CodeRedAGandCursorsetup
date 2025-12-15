# antigravityCodeRed

**antigravityCodeRed** is the control spine for how you use Antigravity, Cursor, VS Code, and other LLM-powered tools to **build, refactor, and run your entire product stack without blowing your feet off.**

This repo is *not* “the cashflow app” or “the legal war room” or “the Twilio machine” by itself.

It is the **platform and operating system** that:

- Wires your IDE + LLM agents into a single, disciplined workflow.  
- Defines how repos are structured (zones, modules, services).  
- Gives Antigravity and other tools a **clear rulebook** so they don’t wreck legacy code or legal-critical logic.  
- Creates the foundation for future SKUs:
  - Cashflow brain and revenue dashboard  
  - Legal war room for FBI / superseding indictment / court cases  
  - Twilio marketing machine / lead faucet  
  - Closer bot and operator consoles  

Modules **1 and 2** live here **today** and everything else will plug into them.

---

## Core Modules

### Module 1 — Orchestration Brain

Module 1 defines *how work happens* in this ecosystem.

It gives you:

- A roster of agents (Architect, CodeWriter, Test, Review, Infra, Safety).  
- A standard pipeline (Plan → Code → Test → Review → Infra → Safety → Deploy).  
- A prompt routing system so your IDE / Antigravity knows **who to be** for each task.  
- Rules for when to slow down, when to escalate, and when to block changes.

In terms of files, Module 1 is:

- [`docs/agent.md`](docs/agent.md) — Agent roles & permissions (who does what).  
- [`docs/orchestration.md`](docs/orchestration.md) — Pipelines and phases (how work flows).  
- [`docs/prompt-routing.md`](docs/prompt-routing.md) — How to talk to the system; task templates and modes.

If you plug this repo into Antigravity or any LLM-IDE, **Module 1 is what turns it from a “clever code monkey” into a disciplined engineering team.**

### Module 2 — Infrastructure & Repo Skeleton

Module 2 defines *where things live* and how they are wired.

It gives you:

- A consistent directory layout (services, APIs, UI, shared libs).  
- RED / YELLOW / GREEN zones to protect critical/legal/legacy code.  
- CI/CD + migration patterns (GitHub Actions, Supabase/SQL, env wiring).  
- A clean separation between platform and product SKUs.

In terms of files, Module 2 is:

- [`docs/architecture.md`](docs/architecture.md) — Directory layout, zones, and migration strategy.  
- `.github/workflows/*` — CI/CD baselines (lint, test, deploy).  
- `migrations/` (optional) — Database/schema changes.  
- `lib/`, `src/` skeleton — Shared libs, services, APIs, UI (even if some pieces are still stubs).

Together, Modules 1 and 2 form **the operating system** for everything else you’re going to build.

---

## Future Modules (Planned SKUs)

These **do not** have to be fully implemented on day one. The whole point of this repo is that the *platform* is ready before the SKUs explode.

Future modules will plug into:

- `src/services/`  
- `src/api/`  
- `src/ui/`  
- `lib/`  

and follow the same zoning and agent rules.

Planned SKUs include:

1. **Cashflow Brain (Module 3)**  
   - `src/services/cashflow/`  
   - `src/api/v1/cashflow/`  
   - UI dashboards under `src/ui/`  
   - Focus: revenue, expenses, deposits, processor health, runway.

2. **Legal War Room (Module 4)**  
   - `src/services/legal/`  
   - `src/api/v1/legal/`  
   - UI for cases, motions, evidence, timelines.  
   - Focus: FBI case, superseding indictment, other federal/civil matters.  
   - This will rapidly become a **RED ZONE** when live.

3. **Twilio Marketing Machine / Lead Faucet (Module 5)**  
   - `src/services/marketing/`  
   - `src/api/v1/marketing/`  
   - UI for campaigns, funnels, and analytics.  
   - Focus: SMS/RCS/email/voice campaigns, RedTrack integration, funnels.

4. **Closer Bot / Operator Console** (fits under services + UI)  
   - Uses outputs of cashflow + marketing + legal to drive operator flows.  

You don’t need every SKU online to get value. You need Modules 1–2 solid, then you can bring SKUs online **one by one, cleanly**.

---

## Two Primary Operating Modes

This repo is designed for **two real-world scenarios**:

1. **Greenfield** — You start a brand new project in Antigravity.  
2. **Brownfield (80% done repo)** — Antigravity attaches to an existing, half-built, slightly-chaotic repo.

Everything in this README, and in the `docs/` suite, is structured to make both modes safe and predictable.

---

## 1. Quick Start — Human Operator

This is what *you* do before you let the machines touch anything.

### 1.1 Prerequisites

You should have:

- Node.js (LTS) + npm or pnpm  
- GitHub account & access to target repo(s)  
- Antigravity IDE, Cursor, or another LLM-capable IDE (optional but recommended)  
- (Optional) Supabase project for DB + auth  
- (Optional) Vercel project for hosting

You do **not** need all the infrastructure wired on day one. Modules 1–2 are mostly docs + structure and can be used even while infra is still inbound.

### 1.2 Clone and Inspect

```bash
git clone <your-repo-url> antigravityCodeRed
cd antigravityCodeRed
```

Inside the repo, you should see at minimum:

```text
README.md
docs/
src/
lib/
.github/
migrations/      # optional
```

### 1.3 Install Dependencies (if package.json is present)

```bash
npm install
# or
pnpm install
```

If this is purely a “docs + skeleton” stage, you may not have a full app yet, which is fine.

### 1.4 Env Setup

Copy `.env.example` (if present) to your local `.env` or framework-specific env file:

```bash
cp .env.example .env.local   # Next.js-style, as an example
```

Fill in:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `AG_TOKEN` (Antigravity)
- Any other required env vars

Secrets are **never** committed to the repo. Only templates live here.

### 1.5 Run Dev Server (If App Skeleton Exists)

If you have a Next.js app or similar:

```bash
npm run dev
```

Otherwise you may just be in a “platform-only” stage and will use this repo as a **rulebook + skeleton** while AG operates inside another concrete app repo.

---

## 2. Quick Start — LLM / IDE Operator

This is what your **LLM tools** should do as soon as they attach to the repo.

### 2.1 Set the Global System Prompt

Set a workspace-level instruction similar to this:

> You are operating inside the repository "antigravityCodeRed"...

Use the full text from [`docs/prompt-routing.md`](docs/prompt-routing.md), Section **1.1 Recommended Global Prompt**.

This tells the model:

- What this repo is (platform spine).  
- What Modules 1–2 are.  
- That it must obey `docs/*.md` and zone rules.  
- That all work must map to A/B/C/D/E and go through a pipeline.

### 2.2 Read the Core Docs First

Any LLM operating in this repo should read, in this order:

1. `README.md` (this file) — context and modules.  
2. `docs/architecture.md` — directory layout + zones.  
3. `docs/agent.md` — who the agents are and what they can do.  
4. `docs/orchestration.md` — pipeline and phases.  
5. `docs/prompt-routing.md` — how to structure tasks and prompts.

Only after that should the model start reading `src/`, `lib/`, `.github/`, etc.

### 2.3 Adopt Roles Explicitly

For any serious task, the LLM should **name its mode** when responding:

- `[MODE: ARCHITECT]` — for planning.  
- `[MODE: CODE]` — for implementing code.  
- `[MODE: TEST]` — for tests.  
- `[MODE: REVIEW]` — for code review.  
- `[MODE: INFRA]` — for CI/CD and migrations.  
- `[MODE: SAFETY]` — for risk assessments.

This is described in more detail in `docs/agent.md` and `docs/prompt-routing.md`.

---

## 3. Zones: RED / YELLOW / GREEN (Conceptual Overview)

Full details live in [`docs/architecture.md`](docs/architecture.md).

At a high level:

- **GREEN** — New and low-risk areas.  
  - Where new SKUs and orchestrator logic should be built.  
  - Safe for CodeWriterAgent to create and refactor.

- **YELLOW** — Active business logic and APIs.  
  - Important but manageable if tests and CI are in place.  
  - Requires more discipline; Architect + Test + Review must be used.

- **RED** — Critical legal, financial, and fragile legacy.  
  - FBI/legal war room logic.  
  - Billing / cashflow / evidence-handling.  
  - Changes here are **rare**, heavily planned, and gated by SafetyAgent + human.

Antigravity, Cursor, and other LLM tools use these zones to decide **how aggressive** they’re allowed to be.

---

## 4. A/B/C/D/E — Why We Merge Anything

For non-trivial work, every change should answer at least one of:

- **A – Deployment** — Does this make the system easier/safer/faster to deploy?  
- **B – Revenue** — Does this help us make more money?  
- **C – Cost** — Does this reduce infra, tooling, or human cost?  
- **D – Organization** — Does this make the system clearer, more maintainable, or more legible?  
- **E – Legal** — Does this strengthen our legal/compliance posture, documentation, or evidentiary clarity?

If a change doesn’t hit any of A/B/C/D/E, you either:

- Don’t understand its value, or  
- Don’t need it.

Agents are required (by `docs/agent.md`) to map tasks to at least one letter. Humans should do the same when writing tasks.

---

## 5. Greenfield vs Brownfield Playbooks

### 5.1 Greenfield: Starting Fresh in Antigravity

When you open a **brand new** repo and want to use `antigravityCodeRed` as your spine:

1. **Initialize Repo**
   ```bash
   mkdir antigravityCodeRed
   cd antigravityCodeRed
   git init
   ```

2. **Add Core Files**  
   - Copy in:
     - `README.md`
     - `docs/agent.md`
     - `docs/orchestration.md`
     - `docs/architecture.md`
     - `docs/prompt-routing.md`
   - Set up basic `package.json`, `tsconfig`, `src/`, `lib/` as per `docs/architecture.md`.

3. **Tell Antigravity / IDE the Rules**  
   - Set the global prompt from `docs/prompt-routing.md`.  
   - Start your first tasks in `[MODE: ARCHITECT]` to plan the structure of your first SKU or platform module.

4. **Bring Online Modules 1–2 First**  
   - Make sure docs are accurate.  
   - Stub out directory structure in `src/` and `lib/`.  
   - Introduce basic CI (lint + test), even with placeholder tests.

5. **Then Start the First SKU (e.g., Cashflow Stage 1)**  
   - New work goes to `src/services/cashflow/`, `src/api/v1/cashflow/`, and `src/ui/` stubs.  
   - All with GREEN zone classification initially.

### 5.2 Brownfield: Attaching to an 80% Done Repo

More interesting, and more dangerous.

When Antigravity or any LLM attaches to a partially-built repo:

1. **Do Not Refactor Immediately.**  
   - No “clean up everything” passes. That’s how things break.

2. **First Task = Map the Existing Repo to Zones**  
   - Run a task like:

     ```text
     [MODE: ARCHITECT]

     You are attaching to a brownfield repo that is ~80% complete.

     1. Read README.md (if exists) and any high-level docs.
     2. Inspect src/, lib/, and other key directories.
     3. Propose a zone mapping (RED/YELLOW/GREEN) for existing paths and output it as a table suitable for docs/architecture.md.
     4. Do not change any code yet.
     ```

   - Paste the resulting table into `docs/architecture.md` under “Brownfield Zone Mapping”.

3. **Second Task = Safe Stabilization**  
   - Add missing docs and tests; no behavior changes yet.  
   - Focus on:
     - `README.md`
     - `docs/`
     - Test coverage for critical flows.

4. **Third Task = Introduce Skeleton for Modules 1–2**  
   - Add or align `docs/agent.md`, `docs/orchestration.md`, `docs/prompt-routing.md`.  
   - Ensure zone rules and A/B/C/D/E are reflected correctly.

5. **Only Then Start Refactors or New SKUs**  
   - And always in GREEN first, linking to existing legacy code without rewriting it all at once.

---

## 6. Branching, PR, and CI Expectations

This repo assumes a **branch + PR** model, even if you are a solo operator.

### 6.1 Branching

- Feature branches: `feature/<short-desc>`  
- Fix branches: `fix/<short-desc>`  
- Infra branches: `infra/<short-desc>`

Never let the model assume it can push directly to `main`.

### 6.2 PR Content

PRs should include:

- A short description of the change.  
- The relevant A/B/C/D/E letters and a one-line justification.  
- A note on zones affected (e.g., “GREEN only” or “YELLOW services + GREEN tests”).  
- Links or references to ArchitectAgent’s plan and ReviewAgent’s review.

### 6.3 CI / CD

At minimum, CI should:

- Run lint and tests on every PR.  
- Block merges if tests fail.  
- Optionally, build/deploy previews on main or specific branches.

As you mature the stack, InfraAgent will enrich `.github/workflows/` and migrations under `migrations/`.

---

## 7. Where Things Live (High-Level File Map)

See `docs/architecture.md` for the full breakdown. At a glance:

```text
antigravityCodeRed/
├── README.md
├── docs/
│   ├── agent.md             # who the agents are
│   ├── orchestration.md     # pipelines, phases
│   ├── architecture.md      # directory layout + zones
│   └── prompt-routing.md    # how to talk to the system
├── src/
│   ├── orchestrator/        # optional orchestration engine (Module 1 concrete code)
│   ├── services/            # Modules 3–5 live here
│   │   ├── platform/        # baseline platform services
│   │   ├── cashflow/        # planned (Module 3)
│   │   ├── legal/           # planned (Module 4)
│   │   ├── marketing/       # planned (Module 5)
│   │   └── closer/          # planned
│   ├── api/                 # HTTP/RPC endpoints
│   ├── ui/                  # dashboards & screens
│   ├── shared/              # shared types & utils
│   └── config/              # config helpers
├── lib/
│   ├── supabaseClient.ts    # DB client
│   ├── logger.ts            # logging
│   └── llm/
│       └── client.ts        # LLM wrappers (Antigravity, etc.)
├── agents/                  # prompt templates per agent (optional)
├── migrations/              # DB migrations (if using SQL)
├── .github/
│   └── workflows/           # CI/CD pipelines
└── tests/ or **/__tests__/  # test suites
```

This layout is the **default**; an 80% repo may differ. In that case, `docs/architecture.md` should document reality and your migration path.

---

## 8. How to Start Today (Concrete Steps)

If you’ve got ~5 hours and want to get real value **today**:

1. **Drop these docs into your main repo** (or a dedicated spine repo):  
   - `README.md` (this file)  
   - `docs/agent.md`  
   - `docs/orchestration.md`  
   - `docs/architecture.md`  
   - `docs/prompt-routing.md`

2. **Wire Antigravity / IDE**  
   - Set the global project prompt (from `prompt-routing.md`).  
   - Load the docs into context.

3. **Run an Architect Pass**  
   - For your current main repo, ask ArchitectAgent to:
     - Classify directories into zones.  
     - Propose a migration plan into this architecture.  
     - Identify immediate low-risk, high-win tasks (docs, tests, logging).

4. **Implement Module 1 in Practice**  
   - Actually start labeling tasks as `[MODE: ARCHITECT]`, `[MODE: CODE]`, etc.  
   - Push yourself to map every change to A/B/C/D/E.

5. **Implement Module 2 Skeleton**  
   - Align your directory structure as close as possible to the one in `docs/architecture.md`.  
   - Set up or stabilize `.github/workflows/*` for lint/test.

6. **Pick One SKU to Start** (cashflow or legal or Twilio)  
   - Scaffold it in GREEN zones only.  
   - Keep logic simple; focus on wiring rather than features.  
   - Add basic tests and a stub UI view so it’s visible.

From that point on, `antigravityCodeRed` is not just a repo — it’s the **playbook** and **guardrail system** that lets you push fast (Twilio war machines, legal brains, cash dashboards) without waking up to a broken indictment argument or a dead deployment.

---

## 9. Contributing / Evolving the System

When you evolve this system:

- Update `docs/architecture.md` when structure or zones change.  
- Update `docs/agent.md` if you add or change agent roles.  
- Update `docs/orchestration.md` if your pipeline changes.  
- Update `docs/prompt-routing.md` if you refine task templates or prompts.  
- Keep this `README.md` accurate enough that a new engineer or LLM can on-board in one pass.

If the docs and the code ever disagree, first fix the docs to match reality, then decide how to refactor the code. Do not let them drift quietly.

---

antigravityCodeRed is where you stop letting “AI” freestyle your repos and start treating it like a disciplined engineering team operating under a clear charter.

Use it that way.
