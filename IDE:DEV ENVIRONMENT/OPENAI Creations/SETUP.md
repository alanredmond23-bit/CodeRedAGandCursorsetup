# FIRST5HOURS / SETUP.md

**Mission:** In the first ~5 hours, you are going to:

1. Strap **antigravityCodeRed** onto your environment (Antigravity, GitHub, Supabase, Vercel).  
2. Make the repo self-explanatory for both humans and LLMs.  
3. Turn loose chaos (existing code) into a **zoned, governed system**.  
4. Ship at least one *real* platform improvement (not just pretty docs).

You are not building every SKU today. You are building the **runway** so cashflow, legal, and Twilio can land without crashing.

Time is rough and aggressive. If something takes longer, you adjust, but you do **not** skip the order.

---

## 0. Overview — Time Blocks

- **Hour 0–1:** Environment + Repo Wiring  
- **Hour 1–2:** Docs & Zones Locked (Modules 1–2 online)  
- **Hour 2–3:** Antigravity / IDE Integration + Agent Modes  
- **Hour 3–4:** Brownfield Mapping + First Safe Changes  
- **Hour 4–5:** One Concrete Platform Win + Checklist for Next 5 Hours

You can run this on:
- A brand new `antigravityCodeRed` repo, **or**
- Your main app repo, using these files as the platform spine.

---

## Hour 0–1 — Environment & Repo Wiring

### Step 0.1 — Confirm the Repo You’re Targeting

Decide **where** Module 1–2 live:

- Option A: Dedicated `antigravityCodeRed` repo that acts as the “platform spine”.  
- Option B: Your main app repo (cashflow / legal / Twilio / etc.) with these docs added to the root.

**Recommendation:**  
If your main app is already a mess, start with **Option A** for clarity, then gradually sync patterns into the main app.

### Step 0.2 — Clone / Create Repo

If new:

```bash
mkdir antigravityCodeRed
cd antigravityCodeRed
git init
```

If existing:

```bash
git clone <your-repo-url> antigravityCodeRed
cd antigravityCodeRed
```

### Step 0.3 — Ensure Core Structure Exists

You want at least this skeleton:

```text
antigravityCodeRed/
├── README.md
├── docs/
├── src/
├── lib/
├── .github/
└── migrations/      # optional
```

If `docs/`, `src/`, `lib/`, or `.github/` are missing, create them now:

```bash
mkdir -p docs src lib .github/workflows migrations
```

### Step 0.4 — Drop in the Core Docs

Make sure the following files exist and are populated with the content we’ve already defined:

- `README.md`
- `docs/agent.md`
- `docs/orchestration.md`
- `docs/architecture.md`
- `docs/prompt-routing.md`

If they’re not in the repo yet, paste them in from your assistant exports (one file at a time).

### Step 0.5 — Basic Node / TS Setup (If Not Already Present)

If this repo will host real code (highly recommended):

1. Initialize package.json:

   ```bash
   npm init -y
   ```

2. Add TypeScript and basic tooling:

   ```bash
   npm install --save-dev typescript ts-node @types/node
   npx tsc --init
   ```

3. Add a basic `src/index.ts` (or framework entry) so the repo is not empty code-wise.

This does not have to be fully wired. You’re simply making sure the repo is structurally alive.

---

## Hour 1–2 — Docs & Zones Locked (Modules 1–2 Online)

Goal: by the end of Hour 2, a human or LLM can open the repo, read 4–5 files, and know **exactly** how to behave.

### Step 1.1 — Sanity Pass on README.md

- Open `README.md`.  
- Confirm it accurately reflects:
  - This repo’s role as **platform spine**.  
  - Modules 1–2 (Orchestration + Infra/Skeleton).  
  - Planned SKUs (cashflow, legal, Twilio, closer).  
  - Greenfield vs Brownfield modes.

If your current reality differs (e.g., no cashflow code yet), keep it in the **“Planned SKUs”** bucket but do not pretend it’s live.

### Step 1.2 — Verify agent.md & prompt-routing.md

- `docs/agent.md` should define:
  - ArchitectAgent, CodeWriterAgent, TestAgent, ReviewAgent, InfraAgent, SafetyAgent.  
  - Zone access matrix.  
  - How a single LLM “picks a hat” (mode) per phase.

- `docs/prompt-routing.md` should define:
  - Global system prompt to use in Antigravity / Cursor.  
  - Task templates.  
  - Modes: `[MODE: ARCHITECT]`, `[MODE: CODE]`, etc.  
  - Scenarios: new SKU, legal war room, attaching at 80%, etc.

If anything feels off or missing, fix it now while the context is fresh.

### Step 1.3 — Lock In Zones in architecture.md

Open `docs/architecture.md` and make sure it contains:

- High-level description of:
  - `src/services/`
  - `src/api/`
  - `src/ui/`
  - `lib/`
  - `agents/` (optional)
  - `.github/workflows/`
  - `migrations/`

- A **RED / YELLOW / GREEN** assignment table for:
  - Platform orchestrator code (Module 1 concrete code if present).  
  - Future SKU folders: `src/services/cashflow/`, `src/services/legal/`, `src/services/marketing/`, etc.  
  - Any existing legal/cashflow logic in your legacy repos (mark them RED or YELLOW).

If you’re attaching this spine to an 80% repo:

- Add a **“Brownfield Zone Mapping”** section and list the real-world paths and their zones.  
- You can refine this later, but you want an explicit first-pass mapping **today**.

### Step 1.4 — Confirm orchestration.md Exists

`docs/orchestration.md` should:

- Describe the pipeline: **Plan → Code → Test → Review → Infra → Safety → Deploy**.  
- Define which agent leads each phase.  
- Clarify how to pass artifacts between phases (plans, diffs, test lists).

If it feels too abstract, add one concrete example using “Cashflow Stage 1” or “Legal War Room Base Schema” as a walkthrough.

By the end of Hour 2:

- Modules 1–2 are **real**, not theoretical.  
- A new dev or LLM can read 4–5 docs and understand the game.

---

## Hour 2–3 — Antigravity / IDE Integration + Agent Modes

Goal: wire your tools so they actually respect this system instead of freelancing.

### Step 2.1 — Configure Antigravity Workspace Prompt

In Antigravity (or your chosen IDE with agent support):

- Set the **project-level system prompt** using the **Recommended Global Prompt** from `docs/prompt-routing.md` Section 1.1.

Key expectations inside that prompt:

- “You are operating inside the repository `antigravityCodeRed`.”  
- “This is a platform spine, not a single app.”  
- “You must obey `README.md` and all `docs/*.md`.”  
- “Work must map to A/B/C/D/E and respect zones.”  
- “Always classify tasks by zones and run Architect → Code → Test → Review → Infra → Safety.”

### Step 2.2 — Create Agent Snippets / Commands

In Antigravity / Cursor / VS Code, set up **reusable snippets**:

- `AG-ARCH` — expands to ArchitectAgent prompt template.  
- `AG-CODE` — expands to CodeWriterAgent template.  
- `AG-TEST` — expands to TestAgent template.  
- `AG-REVIEW` — expands to ReviewAgent template.  
- `AG-INFRA` — expands to InfraAgent template.  
- `AG-SAFETY` — expands to SafetyAgent template.

This saves you from retyping long prompts and keeps behavior consistent.

### Step 2.3 — Wire In Repo-Specific Instructions

For this repo, add context like:

- “Cashflow = Module 3, lives under `src/services/cashflow/` and `src/api/v1/cashflow/`.”  
- “Legal war room = Module 4, lives under `src/services/legal/` and is RED once live.”  
- “Twilio marketing machine = Module 5 under `src/services/marketing/`.”

You can embed this as part of the global system prompt or as a separate context note.

### Step 2.4 — Sanity Test: Dry-Run Architect

Run a **small Architect task** to confirm everything is wired correctly:

Example prompt:

```text
[MODE: ARCHITECT]

Goal:
Sanity check the current repo and list the top 5 safe, high-leverage tasks we should do next.

Constraints:
- You may not modify any files.
- You must respect zones from docs/architecture.md.
- You must map each proposed task to A/B/C/D/E.

Output:
- Table of 5 tasks: Title, Zones, A/B/C/D/E, Risk, Est Hours.
```

Review the output. If the agent ignores zones, docs, or A/B/C/D/E, **fix the global system prompt now**.

---

## Hour 3–4 — Brownfield Mapping + First Safe Changes

Goal: now that the docs and agents are wired, you want actual movement — but safe, controlled, non-destructive movement.

### Step 3.1 — Brownfield Mapping (If Applicable)

If this spine is being attached to a chaotic / legacy repo:

- Run a more detailed **ArchitectAgent** pass:

```text
[MODE: ARCHITECT]

Task:
Map our existing codebase to RED/YELLOW/GREEN using docs/architecture.md as a guide.

Steps:
1. Identify main directories: src/services, src/api, src/ui, lib, others.
2. For each, propose a zone (RED/YELLOW/GREEN) and justify.
3. Flag any obvious legal/cash-critical modules as candidate RED.
4. Output: a markdown table suitable for "Brownfield Zone Mapping" in docs/architecture.md.

Constraints:
- Do not change any files.
- If uncertain, err on the side of higher risk (YELLOW/RED).
```

- Paste the output table into `docs/architecture.md`.  
- This is the **first concrete artifact** of Antigravity understanding your code reality.

### Step 3.2 — Choose 1–3 Safe Platform Tasks

From the Architect “top 5 tasks” list, choose **tasks that are**:

- GREEN-only.  
- High on D (Organization) and A (Deployment).  
- Low risk: docs, test skeletons, logging hooks, type tightening.

Examples:

- “Add missing docs to src/services/platform/.”  
- “Introduce basic logger in lib/logger.ts and wire it to a couple of non-critical services.”  
- “Add placeholder test suites for services with zero tests.”

### Step 3.3 — Execute One Task End-to-End Through the Pipeline

Pick **one** task and run it through:

1. `[MODE: ARCHITECT]` — plan the task (files, steps, tests).  
2. `[MODE: CODE]` — implement limited steps (e.g., steps 1–3 only).  
3. `[MODE: TEST]` — add tests.  
4. `[MODE: REVIEW]` — review diffs; confirm zones; map to A/B/C/D/E.  
5. `[MODE: INFRA]` — adjust CI only if needed.  
6. `[MODE: SAFETY]` — confirm risk is low and safe to merge.

Even if this is just “add docstring + tests + logger stub”, the point is to **exercise the whole machine once**.

### Step 3.4 — Create a Branch & PR

Manually or via your Git hosting:

```bash
git checkout -b feature/first-platform-task
git add .
git commit -m "chore: first platform task via antigravityCodeRed pipeline"
git push origin feature/first-platform-task
```

Open a PR with:

- Short description.  
- Zones touched (e.g., “GREEN only”).  
- A/B/C/D/E letters and justification.  
- Link to the Architect plan (can be pasted into the PR description).

Merge once you’re satisfied.

At this point, the system is **not theoretical**. It has produced a real, merged change.

---

## Hour 4–5 — One Concrete Platform Win + Next-5-Hours Checklist

Goal: leave this 5-hour block with something meaningful and a clear next sequence.

### Step 4.1 — Choose a Slightly Bigger Win (But Still Safe)

Pick a task that:

- Still avoids RED.  
- Moves you closer to a real SKU, e.g.:  
  - Cashflow Stage 1 skeleton.  
  - Legal war room base types (no real evidence yet).  
  - Twilio campaign service stub.

Example: **Cashflow Stage 1 Skeleton**

- Create: `src/services/cashflow/` with basic domain model (`Account`, `Transaction`, `Processor`).  
- Create: `src/api/v1/cashflow/` with a stub endpoint (e.g., `GET /cashflow/summary` returning mock data).  
- Optionally: Add a simple UI card under `src/ui/dashboard/` that hits that API and displays mock totals.

Run it through the same pipeline:

1. Architect plan.  
2. Code implementation (GREEN only).  
3. Tests.  
4. Review.  
5. Infra check.  
6. Safety check (should say “low risk, allowed”).  
7. Branch + PR + merge.

### Step 4.2 — Log What Worked and What Hurt

Add a short file, e.g. `FIRST5HOURS/RETRO.md` later (for now just jot notes), capturing:

- Which prompts got you the best results.  
- Where the model tried to overreach (e.g., rewrite too much).  
- Where the docs were unclear or incomplete.

This becomes input for improving `docs/prompt-routing.md` and `docs/orchestration.md`.

### Step 4.3 — Define the Next 5-Hour Block

Before you walk away, define **Next5Hours** as a list of 5–10 tasks, each with:

- Title  
- Zones  
- A/B/C/D/E  
- Rough estimate (S/M/L)  
- Agent mode to start with (Architect / Infra / etc.)

You can add this to a new file:

- `FIRST5HOURS/NEXT5HOURS.md`

Example row:

```markdown
1. Scaffold Legal War Room base types
   - Zones: GREEN (src/services/legal/types.ts)
   - A/B/C/D/E: D, E
   - Size: M
   - Start Mode: ARCHITECT
```

---

## Checklist Summary (Copy-Paste Friendly)

You can paste this as a GitHub issue titled: **“FIRST5HOURS: Bring antigravityCodeRed Online”**

```markdown
- [ ] Decide target repo (dedicated antigravityCodeRed vs main app)
- [ ] Ensure core structure exists (README, docs, src, lib, .github, migrations)
- [ ] Add README.md, docs/agent.md, docs/orchestration.md, docs/architecture.md, docs/prompt-routing.md
- [ ] Sanity-check and adjust README for actual reality
- [ ] Lock zones in docs/architecture.md (including Brownfield mapping if needed)
- [ ] Verify agent roles and pipeline in docs/agent.md and docs/orchestration.md
- [ ] Confirm prompt-routing patterns in docs/prompt-routing.md
- [ ] Configure Antigravity / IDE global system prompt for this repo
- [ ] Create agent mode snippets (AG-ARCH, AG-CODE, AG-TEST, AG-REVIEW, AG-INFRA, AG-SAFETY)
- [ ] Run a dry-run Architect task to propose top 5 safe, high-leverage tasks
- [ ] (Brownfield) Run Architect mapping for RED/YELLOW/GREEN and paste into docs/architecture.md
- [ ] Choose 1–3 safe GREEN-only platform tasks
- [ ] Execute one task through the full pipeline (Plan → Code → Test → Review → Infra → Safety)
- [ ] Create feature branch, open PR, tag zones + A/B/C/D/E, and merge
- [ ] Choose one slightly bigger but still safe platform win (e.g., Cashflow Stage 1 skeleton)
- [ ] Run that task through the full pipeline and merge
- [ ] Write quick notes on which prompts worked / failed (seed FIRST5HOURS/RETRO.md later)
- [ ] Create NEXT5HOURS task list with 5–10 scoped tasks for Modules 3–5 + infra
```

If you do just this in the first 5 hours, you’ll walk away with:

- A repo that **tells Antigravity exactly how to behave**.  
- A real merged change proven through the pipeline.  
- A Cashflow / Legal / Twilio runway that can be built out over the next few sessions without starting from chaos every time.
