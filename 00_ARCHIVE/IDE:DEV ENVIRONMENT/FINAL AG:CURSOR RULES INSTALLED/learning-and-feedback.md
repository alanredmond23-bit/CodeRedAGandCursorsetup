# Learning & Feedback Loops – antigravityCodeRed

**File:** `docs/learning-and-feedback.md`  
**Scope:** How CodeRed learns from successes and failures, and how that learning is fed back into prompts, RAG, and orchestration.

Think of this file as the **neural plasticity** of the system: how it gets better instead of just getting busier.

---

## 1. Goals of the Learning System

1. **Fewer repeated mistakes.**  
   CI failures, deploy errors, and miswired infra should trend down, not remain flat.

2. **Sharper defaults over time.**  
   - Better warm-start prompts.
   - Better model choices.
   - Better routing decisions.

3. **Explicit knowledge, not vibes.**  
   We capture:
   - “What failed?”
   - “Why did it fail?”
   - “What do we do differently next time?”

4. **Link to real outcomes.**  
   Over time, we want to connect:
   - Technical decisions → revenue, cost, legal risk, and operational wins.

---

## 2. Core Learning Objects

We mainly use three tables for learning in the `codered` schema:

1. **`codered.lessons`**
2. **`codered.bug_patterns`**
3. **`codered.decisions`**

Other tables provide raw signals:

- `codered.tasks`
- `codered.task_runs`
- `codered.agent_runs`
- `codered.ci_events`
- `codered.deployments`
- `codered.errors`
- `codered.llm_usage_*`

### 2.1 `codered.lessons`

Captures *specific* learnings, often from single incidents.

Fields (conceptual):

- `id`
- `project_id`
- `title`
- `description`
- `source_type` – `ci_failure`, `cynic_review`, `safety_escalation`, `success_story`, etc.
- `related_task_id` (optional)
- `related_agent_id` (optional)
- `tags` – e.g., `["vercel","supabase","twilio","legal"]`
- `recommendations` – bullet list of what to do next time
- `status` – `draft`, `applied`, `deprecated`

### 2.2 `codered.bug_patterns`

Captures recurring error archetypes and their playbooks.

Fields:

- `id`
- `name`
- `pattern_signature` – text or regex describing the symptom
- `examples` – references to `errors`, `ci_events`, or `task_runs`
- `impact` – severity and blast radius
- `playbook` – step-by-step fix and prevention
- `tags`
- `status` – `draft`, `active`, `deprecated`

### 2.3 `codered.decisions`

Captures explicit tradeoffs and final calls (especially important for legal/infra/revenue).

Fields:

- `id`
- `project_id`
- `title`
- `description`
- `context` – short background
- `options_considered`
- `chosen_option`
- `rationale`
- `impact_axes` – which of A–E are involved
- `timestamp`
- `owner` – who made the call (human or agent)- `status` – `active`, `reversed`, `superseded`

---

## 3. Who Creates Learning Objects?

Learning objects are created by:

1. **LibrarianAgent** – primary owner of the learning pipeline.
2. **CynicAgent** – when harsh review reveals recurring issues.
3. **SafetyAgent** – when there are escalations or blocked tasks.
4. **Orchestrator** – when a multi-step flow yields a major outcome.
5. **Human Operator** – you can directly author lessons/decisions when needed.

The rule of thumb:

- If the same thought would be useful **three or more times in the future**, capture it.

---

## 4. Learning Pipeline (End-to-End)

At a high level:

```text
[Raw Signals: agent_runs, ci_events, errors, reviews]
      ↓
[Extraction: LibrarianAgent & friends]
      ↓
[Structured Learning: lessons, bug_patterns, decisions]
      ↓
[Surfacing: RAG, prompts, dashboards]
      ↓
[Behavior Change: better plans, routing, and code]
```

### 4.1 Raw Signals

Sources include:

- CI failures (from `ci_events` + `errors`)
- Deployment rollbacks
- SafetyAgent escalations / blocks
- CynicAgent “revise” verdicts
- Human feedback (“this sucked”, “this was great”)

These are logged already as part of Modules 1–2 infrastructure.

### 4.2 Extraction (LibrarianAgent)

LibrarianAgent runs periodically or is triggered by events. It should:

1. Scan recent `errors`, `ci_events`, `task_runs`, `agent_runs`.
2. Identify candidates for `lessons` or `bug_patterns`.
3. Propose new learning objects with:
   - Clear titles,
   - Concise descriptions,
   - Appropriate tags,
   - Initial recommendations.

These proposals can be auto-accepted for low-risk topics (e.g., “improve logging for X”), or require human approval for sensitive topics (e.g., legal strategy).

### 4.3 Surfacing Learning

When agents work on new tasks, RAG must surface relevant learnings:

- ArchitectAgent:
  - Fetches `lessons` and `bug_patterns` with matching tags/domain.
- InfraAgent:
  - Always sees active `bug_patterns` around CI/CD.
- Orchestrator:
  - Reads `decisions` relevant to current tasks and milestones.
- CynicAgent:
  - References prior critiques when judging new work.

Implementation:

- Learning tables are ingested into RAG corpora (as chunks).
- RAG queries include filters by tags/domain where possible.
- Prompts explicitly say:
  - “If there are relevant lessons or bug patterns, apply them.”

### 4.4 Closing the Loop

For each learning object, we track:

- `status` – `draft`, `applied`, `deprecated`
- `applied_count` – how many times it influenced work
- `last_applied_at` – when it last mattered

LibrarianAgent periodically cleans up:

- Deprecates outdated lessons.
- Merges duplicate bug patterns.
- Promotes the most useful ones into higher-visibility docs (e.g., `docs/playbooks/*.md`).

---

## 5. Feedback from You (Human Operator)

Your feedback is extremely high-signal and must be captured cleanly.

### 5.1 Feedback Channels

- **Inline ratings** in the IDE (future UI):
  - “Useful / Not useful / Dangerous / Brilliant”
- **Manual learning entries**:
  - Directly author/edit `lessons` or `decisions` via UI/API.
- **Cynic override notes**:
  - When you override CynicAgent’s verdict, log why.

### 5.2 How Feedback Changes Behavior

- Frequent “Not useful” ratings on a certain pattern:
  - Trigger rework of prompts or RAG for the responsible agent.
- “Dangerous” flags:
  - Create urgent `lessons` and `bug_patterns` with SafetyAgent involvement.
- Highly-rated patterns:
  - Get promoted to “playbook” status and emphasized in prompts.

Over time, this shapes:

- Which examples we surface in context.
- How aggressively CynicAgent scores certain mistakes.
- How SafetyAgent interprets risk in similar scenarios.

---

## 6. Link to Metrics and Outcomes

Longer-term, CodeRed should connect:

- Technical changes → KPI shifts.

### 6.1 Metric Sources

- Revenue & cost dashboards (outside Modules 1–2 but linkable)
- Lead conversion metrics
- Legal milestones (e.g., motions filed, rulings)
- Operational metrics (deploy frequency, failure rate, MTTR)

### 6.2 Tagging Decisions with Outcomes

For important decisions in `codered.decisions`, we should later attach:

- `observed_outcome` – narrative + metrics
- `outcome_rating` – `positive`, `neutral`, `negative`
- `time_to_impact` – short/medium/long-term

These can then be used by:

- ArchitectAgent and Orchestrator to bias future plans toward historically good patterns.
- CynicAgent to criticize ideas that look like past failures.

---

## 7. Learning in Red-Zone / Legal Contexts (High-Level)

For legal and FBI-related domains:

- Learning objects must be treated as **sensitive**:

  - Access-controlled tables/schemas.
  - Separate RAG indexes with tighter rules.
  - SafetyAgent always in the loop.

- Lessons should emphasize:
  - Accuracy of citations and timelines.
  - Clear distinctions between fact, allegation, and argument.
  - Interaction with licensed counsel.

Nothing in `lessons` or `decisions` should be treated as binding legal reality. They are **internal strategy artifacts** only.

---

## 8. MVP Criteria for Learning & Feedback

We consider learning and feedback **MVP-complete** when:

1. `lessons`, `bug_patterns`, and `decisions` tables exist and are wired to:
   - LibrarianAgent,
   - CynicAgent,
   - SafetyAgent,
   - Orchestrator.
2. LibrarianAgent can:
   - Turn at least one incident into a `lesson`,
   - And have that lesson surface in a later related task via RAG.
3. At least one `bug_pattern` is defined for:
   - CI/CD failures or infra problems.
4. At least one `decision` has been logged for:
   - A meaningful architectural or infra tradeoff.
5. Dashboards provide a basic view of:
   - Number of lessons,
   - Active bug patterns,
   - Recent decisions.

From here, we:

- Add more detailed metrics.
- Refine prompts to consume learning objects more intelligently.
- Tie learning outcomes directly to business/legal KPIs.
