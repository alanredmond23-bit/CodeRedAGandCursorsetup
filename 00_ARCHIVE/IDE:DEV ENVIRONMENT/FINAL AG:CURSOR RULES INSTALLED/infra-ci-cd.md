# Infra, CI/CD & Deployment Standards – antigravityCodeRed

**File:** `docs/infra-ci-cd.md`  
**Scope:** How CodeRed expects GitHub, CI, Vercel, and Supabase to be wired for Modules 1–2.

This is the **deployment contract** for the brain.  
It tells AntiGravity, your IDE, and your agents what “correct” infra looks like so they can:

- Propose valid GitHub Actions files.
- Fix broken CI/CD with known patterns.
- Keep Supabase migrations under control.
- Use secrets and env vars safely.

If reality diverges from this doc, **either reality is wrong, or this doc is out of date**. Fix one before you let agents go wild.

---

## 1. High-Level Infra Topology

For Modules 1–2, we assume:

- **Repo host:** GitHub
- **Primary branches:**
  - `main` – production
  - `develop` – staging / integration
  - feature branches – `feat/*`, `fix/*`
- **CI:** GitHub Actions
- **Hosting:** Vercel for the web app (if present)
- **Database / backend:** Supabase (Postgres + auth + storage)
- **Secret management:**
  - GitHub: repo/action-level secrets
  - Vercel: environment-specific env vars
  - Supabase: project-level secrets/keys (used only from server/edge)

Modules 1–2 are focused on **observability and correctness**, not on maximum horizontal scaling. That comes later.

---

## 2. Branch & Environment Strategy

### 2.1 Branches

- `main` – always deployable to production.
- `develop` – integration branch, auto-deploys to staging/preview.
- `feat/*`, `fix/*` – short-lived branches used for feature work.

### 2.2 Environments

- `preview` – auto deployments from non-`main` branches.
- `staging` – tied to `develop` (optional but recommended).
- `production` – tied to `main`.

**Rule:**  
No direct deploys to production from anything except `main` (manual hotfixes still use `main` but via fast PRs if possible).

---

## 3. GitHub Actions – CI/CD Pipelines

We standardize on the following workflows:

1. `ci.yml` – core test/build pipeline for pushes and PRs.
2. `deploy-preview.yml` – deploy previews for feature branches (optional if Vercel Git integration handles this).
3. `deploy-production.yml` – production deploy, triggered on `main` and/or manual dispatch.

### 3.1 `ci.yml` – Core Pipeline

**Triggers:**

- `push` to any branch.
- `pull_request` targeting `develop` or `main`.

**Jobs (minimum):**

1. **`lint-and-test`**
2. **`typecheck`** (if TS)
3. **`build-check`** – confirm the app builds (no artefact needed if Vercel builds separately).

Example outline (pseudocode):

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["develop", "main"]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20.x"
          cache: "npm"
      - run: npm ci
      - run: npm run lint
      - run: npm test --if-present

  typecheck:
    runs-on: ubuntu-latest
    needs: lint-and-test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20.x"
          cache: "npm"
      - run: npm ci
      - run: npm run typecheck --if-present

  build-check:
    runs-on: ubuntu-latest
    needs: typecheck
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20.x"
          cache: "npm"
      - run: npm ci
      - run: npm run build
```

AntiGravity/CodeAgent should treat this as the baseline and only diverge with a clear reason (monorepo, turbo, pnpm, etc.).

---

### 3.2 `deploy-production.yml` – Production Deploy

**Options:**

- Use Vercel’s Git integration and have `main` automatically trigger production.
- Or use a GitHub Action that triggers Vercel via API.

Preferred pattern for control: **manual approval** for production deploys even after `main` is green.

Example outline:

```yaml
name: Deploy Production

on:
  workflow_dispatch:
  push:
    branches: ["main"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Call Vercel Deploy Hook
        run: |
          curl -X POST "$VERCEL_DEPLOY_HOOK_URL"
        env:
          VERCEL_DEPLOY_HOOK_URL: ${{ secrets.VERCEL_DEPLOY_HOOK_URL }}
```

You can decide whether to use `workflow_dispatch` only (manual button) or allow auto deploys on `main` pushes.

---

## 4. Vercel Configuration

### 4.1 Project Linking

- One Vercel project per web app (e.g. `antigravity-codered-web`).
- Vercel connected to GitHub repo.
- Environment map:
  - Preview → non-main branches.
  - Production → `main` branch.

### 4.2 Build Settings

Standard modern Next.js/React pattern:

- **Framework Preset:** Next.js (if applicable)
- **Build Command:** `npm run build` or `pnpm build`/`yarn build`
- **Output Directory:** `.next` (or framework-specific)
- **Node Version:** 20+ (match CI)

### 4.3 Environment Variables (Vercel)

Define per-environment:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (server only functions; not for front-end)
- Any LLM keys (server-side only):
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GEMINI_API_KEY`
  - `XAI_API_KEY`

Rules:

- Never expose **service role keys** or **secret keys** to client-side code.
- Use Vercel’s Environment Variable UI or `vercel env` CLI.
- Keep **names consistent** between GitHub and Vercel (e.g., `SUPABASE_URL` vs `NEXT_PUBLIC_SUPABASE_URL` pattern is intentional).

---

## 5. Supabase – DB, Auth & Migrations

### 5.1 Connection Strategy

- Local dev:
  - Use Supabase CLI or project URL + anon key.
- Server/CI:
  - Use env var `SUPABASE_DB_URL` for direct PG access (if needed).
  - For app code, use URL+key environment vars.

### 5.2 Migrations

We standardize on:

- Folder: `supabase/migrations/` or `db/migrations/`
- Tool: Supabase CLI or your chosen migration tool (e.g., Prisma/Drizzle) but mapping must align with `schema-supabase.md`.

Rules:

- No direct schema changes in Supabase UI for core `codered` schema without also generating a migration.
- Migrations are:
  - Idempotent (or reversible where possible).
  - Applied automatically in CI for testing.
  - Applied in production as part of controlled deployment flow (manual or pipeline).

### 5.3 RLS (Row-Level Security)

For Modules 1–2 (single-tenant internal brain), you can initially:

- Disable RLS on `codered.*` tables to simplify iteration **OR**
- Use a simple `role = service` pattern via service role key for all writes.

Clarify in config which approach you’re taking. Agents need to know whether they should expect RLS errors or not.

---

## 6. Secrets & Environment Management

### 6.1 GitHub Secrets

At minimum:

- `SUPABASE_DB_URL` (if migrations run via CI)
- `SUPABASE_SERVICE_ROLE_KEY` (if needed in CI/infra tasks)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY` (if tests use real LLMs)
- `VERCEL_DEPLOY_HOOK_URL` (if using manual deploy hook)

**Rules:**

- Secrets are **never** committed to the repo.
- Secrets are referenced via `${{ secrets.NAME }}` only.
- If a workflow fails due to a missing secret, InfraAgent should:
  - Check this doc and suggest exactly which secret is missing and where.

### 6.2 Local `.env`

Use `.env.local` for local dev, **never** commit:

- `.gitignore` must include `.env`, `.env.local`, `.env.*.local`

The repo should include an example file:

- `.env.example` – listing all required env names without values.

---

## 7. Standard CI/CD Checks

CodeRed expects the following checks as a baseline for any web app in this ecosystem:

1. **Lint** – ESLint or equivalent.
2. **Typecheck** – TypeScript (if used).
3. **Unit tests** – Jest, Vitest, etc. at least stubs.
4. **Build** – framework build (Next.js, etc.).
5. **Optionally:** E2E or smoke test (Playwright/Cypress) for key flows.

If an app does **not** implement all of these, ArchitectAgent should **note the gap** and either:

- Plan to add the missing checks, or
- Document why they are intentionally omitted (e.g., CLI-only tool).

---

## 8. Mapping to Playbooks

Infra issues are usually pattern-based. This doc gives the **structure**, while the playbook (see `docs/playbooks/ci-vercel-supabase.md`) gives the **tactical responses**:

- CI fails during `npm install` → see `npm/yarn/pnpm` playbook.
- Vercel deploy fails → see Vercel playbook + Supabase connection playbook.
- Supabase migration errors → see migration RLS/playbook section.

InfraAgent and CynicAgent should always reference both:

- This doc – structure & standards.
- Playbooks – concrete “do this now” steps.

---

## 9. MVP Criteria for Infra & CI/CD

Infra for Modules 1–2 is **MVP-complete** when:

1. GitHub repo has at least:
   - `ci.yml` (or equivalent) with lint/test/build.
   - A production deploy mechanism (`deploy-production.yml` or Vercel Git autodeploy).
2. Vercel project:
   - Is connected to the repo.
   - Correctly maps `main` → production.
   - Has required env vars set for each environment.
3. Supabase:
   - Has the `codered` schema matching `schema-supabase.md` (or a strict subset, then extended).
   - Uses migrations stored in the repo.
4. Secrets:
   - Exist in GitHub and Vercel matching this doc.
5. At least one end-to-end cycle:
   - Feature branch → CI → preview/staging → `main` → production deploy
   - Has executed successfully and is logged in:
     - `ci_events`
     - `deployments`
     - `errors` (for any failures).

After MVP, we harden with more playbooks, E2E tests, and multi-project support.
