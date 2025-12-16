# Playbooks – CI, Vercel & Supabase – antigravityCodeRed

**File:** `docs/playbooks/ci-vercel-supabase.md`  
**Scope:** Concrete “if X is broken, do Y” playbooks for CI, Vercel, and Supabase issues in Modules 1–2.

This is the **tactical manual** for InfraAgent, ArchitectAgent, CodeAgent, and CynicAgent when infra blows up.

- `infra-ci-cd.md` = structure & standards.  
- This file = how to fix real failures fast.

---

## 1. CI Failures (GitHub Actions)

### 1.1 Pipeline Fails During `npm install` / `npm ci`

**Common Symptoms:**

- `npm ERR!` logs
- Missing lockfile or dependency conflicts
- Wrong Node version

**Checklist:**

1. **Check Node version:**
   - Ensure `actions/setup-node` uses the same version as local dev.
   - If local is 20.x, CI should be `node-version: "20.x"`.

2. **Lockfile consistency:**
   - If using `npm`, ensure `package-lock.json` is committed and up-to-date.
   - If using `pnpm` or `yarn`, standardize and remove other lockfiles.

3. **Broken dependency:**
   - If a specific package is failing, look for:
     - Peer dependency warnings that became errors.
     - Node version incompatibilities.

4. **Action for agents:**

   - ArchitectAgent:
     - Propose consistent tooling (npm vs pnpm vs yarn) and update docs.
   - CodeAgent:
     - Update `package.json` to align versions with current ecosystem.
   - InfraAgent:
     - Patch CI workflow to match local Node/tooling.

**When to escalate:**

- If external registry issues persist (npm outage), mark CI status as `blocked` and retry later.

---

### 1.2 Lint/Typecheck Failures

**Symptoms:**

- ESLint errors in CI that devs “ignore locally”.
- TypeScript `TSxxxx` errors appearing only in CI.

**Checklist:**

1. **Run same commands locally:**
   - `npm run lint`
   - `npm run typecheck`

2. **Align configs:**
   - Confirm `.eslintrc` and `tsconfig.json` are committed.
   - Look for `exclude`/`include` mismatches in `tsconfig`.

3. **Action for agents:**

   - CodeAgent:
     - Fix actual lint/TS errors.
     - Avoid suppressing with `any` or `// eslint-disable` unless justified in comments.
   - ArchitectAgent:
     - Propose rule tuning only if truly necessary (e.g., relax overly strict rules blocking real progress).

**When to escalate:**

- If lint rules are fundamentally misaligned with project reality, create a `lesson` and adjust rules with rationale.

---

### 1.3 Build Failures

**Symptoms:**

- Next.js build errors (`ReferenceError: window is not defined`).
- Missing env vars at build time.
- Dynamic imports misused.

**Checklist:**

1. **Check env vars in CI:**
   - Ensure required envs are set as GitHub `env`/`secrets` or in Vercel (for Vercel builds).

2. **SSR vs client-only code:**
   - Identify modules using `window`, `document`, or browser APIs.
   - Wrap with `useEffect` or `dynamic(() => import(...), { ssr: false })` where appropriate.

3. **Broken imports:**
   - Look for path aliases not configured in `tsconfig.paths` or bundler config.

4. **Action for agents:**

   - CodeAgent:
     - Patch broken components and imports.
   - ArchitectAgent:
     - Define clear pattern for server vs client components.

**When to escalate:**

- If build passes locally but fails in CI, check Node version, env vars, and differences between local env and CI env.

---

## 2. Vercel Deployment Issues

### 2.1 Vercel Build Fails

**Symptoms:**

- Build succeeds in GitHub CI but fails in Vercel.
- Error messages reference missing env vars or Node version.

**Checklist:**

1. **Check Vercel build logs.**
2. **Validate env vars:**
   - Confirm all required `NEXT_PUBLIC_*` and server-side vars are set in Vercel for the relevant environment.
3. **Node version & settings:**
   - Ensure Vercel’s Node version matches CI (via `engines` in `package.json` or Vercel settings).
4. **Monorepo specifics:**
   - If using monorepo, make sure `root directory` and `build command` are set correctly per app.

**Action for agents:**

- InfraAgent:
  - Cross-check `infra-ci-cd.md` expectations with Vercel’s project settings.
- CodeAgent:
  - Fix runtime-only code in `getStaticProps` / `getServerSideProps` that relies on browser globals.
- LibrarianAgent:
  - Turn repeated failures into `bug_patterns` for future detection.

---

### 2.2 Vercel 500 / Runtime Errors After Deploy

**Symptoms:**

- Build succeeds but app returns 500/Runtime errors in production.
- Errors reference missing env vars, DB connections, or auth issues.

**Checklist:**

1. **Check Vercel logs for the deployment.**
2. **Check env var differences** between staging and production.
3. **Confirm Supabase URL/keys are correct** and not swapped between projects.
4. **Confirm migrations are applied** to the Supabase project backing that environment.

**Action for agents:**

- InfraAgent:
  - Compare environment configs across staging/production.
- CodeAgent:
  - Improve error handling and logging around external service calls.
- ArchitectAgent:
  - If needed, adjust configuration pattern (central config module).

---

## 3. Supabase – Migrations & RLS Problems

### 3.1 Migration Fails

**Symptoms:**

- Migration command fails in CI or locally with SQL errors.
- Tables do not match `schema-supabase.md`.

**Checklist:**

1. **Inspect failing migration file:**
   - Look for duplicate table creation or column conflicts.
   - Confirm schema name (`codered`) is correct.

2. **Check current DB state:**
   - List existing tables and columns in Supabase.
   - Compare to `schema-supabase.md`.

3. **Action for agents:**

   - ArchitectAgent:
     - Propose a migration plan to move from current DB to target schema (including `ALTER TABLE` instead of `CREATE TABLE` where needed).
   - InfraAgent:
     - Update migration scripts to be idempotent and safe.

4. **If DB is heavily divergent:**
   - Create a clear decision:
     - Fix schema to match doc, or
     - Update doc to match chosen schema, then regenerate migrations.

---

### 3.2 RLS Blocking Writes/Reads

**Symptoms:**

- App or agent code gets 401/403 or “permission denied” errors from Supabase.
- Queries that work in Supabase SQL editor fail in app.

**Checklist:**

1. **Check if RLS is enabled** on affected tables.
2. **Check which key is being used:**
   - `anon` key (RLS enforced) vs service role key (bypass RLS).
3. **Inspect RLS policies** and see if they match intended access pattern.

**Action for agents:**

- InfraAgent:
  - Disable RLS temporarily for internal-only `codered.*` tables in dev **or**
  - Add service role usage with secure server-side calls only.
- ArchitectAgent:
  - Design proper RLS policies for multi-tenant future, but not mandatory for Modules 1–2.

---

## 4. Patterns from Repeated Failures

To avoid “Groundhog Day” failures, we convert repeated issues into `bug_patterns` and `lessons`.

### 4.1 CI Pattern: Env Vars Missing in CI

**Signature:**
- CI logs show `process.env.*` as `undefined` or failing checks.

**Playbook:**
- Ensure `.env.example` lists all required env vars.
- Update GitHub secrets to include the missing env.
- LibrarianAgent:
  - Add a `lesson` and `bug_pattern`:
    - “CI environment variables checklist for this project.”

### 4.2 Vercel Pattern: Different Config Than CI

**Signature:**
- CI build succeeds, Vercel build fails with config/env issues.

**Playbook:**
- InfraAgent:
  - Compare Node version, env vars, and build commands between CI and Vercel.
- LibrarianAgent:
  - Create `lesson` + `bug_pattern`:
    - “Always mirror Node version and build commands between CI and Vercel.”

### 4.3 Supabase Pattern: Schema Drift

**Signature:**
- Migrations referencing columns/tables that don’t exist or already exist.

**Playbook:**
- ArchitectAgent:
  - Run a one-time schema diff between actual DB and `schema-supabase.md`.
- InfraAgent:
  - Generate and apply correcting migrations.
- LibrarianAgent:
  - Capture the incident as a `lesson` (“schema drift correction”) and `bug_pattern` for future detection.

---

## 5. Roles in an Incident

When something breaks, we want a **clear division of labor**:

- **InfraAgent:**
  - Reads CI/Vercel/Supabase logs.
  - Maps errors to known patterns/playbooks.
  - Proposes config/workflow changes.

- **CodeAgent:**
  - Fixes code-level issues (imports, SSR bugs, etc.).

- **ArchitectAgent:**
  - Adjusts high-level patterns when systemic issues appear (e.g., how env vars are passed, how schema is organized).

- **CynicAgent:**
  - Grades the response:
    - Did we actually fix root cause?
    - Did we capture a lesson/bug_pattern?
    - Does this incident suggest tightening standards?

- **LibrarianAgent:**
  - Converts the incident into:
    - `lessons`
    - `bug_patterns`
  - Ensures RAG has updated guidance for future agents.

---

## 6. Quick Triage Flow (ASCII)

When a build/deploy breaks, the flow should look like this:

```text
[CI / Deploy Failure]
       ↓
InfraAgent:
  - Collect logs, classify source (CI, Vercel, Supabase, Other)
       ↓
Match to Playbook:
  - npm/install?
  - lint/typecheck?
  - build?
  - Vercel build/runtime?
  - Supabase migration/RLS?
       ↓
CodeAgent + ArchitectAgent:
  - Apply targeted fixes
  - Update workflows/configs if needed
       ↓
Re-run CI / Deploy
       ↓
CynicAgent:
  - Review incident, score quality of fix
       ↓
LibrarianAgent:
  - Write lesson / bug_pattern
  - Update RAG/docs if needed
```

This ensures each failure **improves** the system, not just consumes time.

---

## 7. MVP Criteria for Playbooks

Playbooks are **MVP-complete** when:

1. There is at least one documented path for:
   - CI install failures.
   - Lint/typecheck failures.
   - Build failures.
   - Vercel build/runtime issues.
   - Supabase migration problems.
2. Agents know, via their prompts, to:
   - Check playbooks when infra errors appear.
   - Convert repeated issues into `lessons` and `bug_patterns`.
3. At least one real incident has been:
   - Resolved using this file,
   - Logged in `errors`, `ci_events`, `deployments`,
   - Captured as a `lesson` or `bug_pattern`,
   - Ingested into RAG for future use.

From here, we continue adding **path-specific** playbooks:
- Twilio API failures,
- Legal RAG sync issues,
- Multi-tenant / white-label infra patterns.
