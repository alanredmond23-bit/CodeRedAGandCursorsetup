# MVP – Top 10 Checklist (One-Hour Build)

Use this when you sit down to actually wire the MVP. If these 10 are done, Phase 1 is real.

1. **Clone + Open Repo**  
   - Repo: `antigravityCodeRed`  
   - Open in AntiGravity / IDE of choice.

2. **Create `.env.example`**  
   - Add placeholders for: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `AG_ENV`.

3. **Create `.env.local`**  
   - Fill with real values on your machine (dev keys only).

4. **Define 4 Core Agents (YAML skeletons)**  
   - Create in `/agents/`:
     - `orchestrator_codered.yaml`
     - `cynic_evaluator_v1.yaml`
     - `legal_research_v1.yaml`
     - `twilio_campaign_v1.yaml`

5. **Fill MVP Fields for Each Agent**  
   - For all 4 agents, fill:
     - `agent_id`, `name`, `domain`, `tier`
     - `role`, `goals`, `non_goals`
     - `models.primary`, 1 backup, `temperature`, `max_tokens`
     - 2–3 `tools` with `name` + `mode`
     - `limits.max_runtime_minutes`, `max_recursion_depth`, `max_child_agents`, `max_estimated_cost_usd`
     - `memory_profile.persistence: run`, `memory_profile.supabase_schema: codered`
     - `guardrails.hallucination_policy: strict`, `guardrails.can_touch_production`
     - `cynic_hooks.enabled: true`, `cynic_hooks.scoring_profile`

6. **Create Supabase Migration (Core Tables)**  
   - File: `supabase/migrations/0001_codered_core.sql`  
   - Define tables:
     - `codered.agent_runs` (include tokens + cost fields)
     - `codered.tool_calls` (minimal; can expand later)
     - `codered.evals_cynic` (MVP fields from cynic spec)

7. **Write `rules.md`**  
   - Orchestrator rules (microtasks, agent routing, Cynic calls, logging).  
   - Agent rules (domain boundaries, tool use, respect limits).  
   - MVP boundaries (Cynic advisory only; no auto-deploy/tuning).

8. **Wire Token ¼ Logic**  
   - After an agent run, record into `agent_runs`:
     - `tokens_in`, `tokens_out`, `cost_usd_estimate`, `model_name`, `duration_ms`.  
   - Use a simple pricing map for your primary model.

9. **Wire Cynic ¼ Logic**  
   - Ensure `cynic_evaluator_v1` can be called manually.  
   - On call, write a row into `evals_cynic` with score + grade + brief feedback.

10. **Run One End-to-End Test**  
   - Trigger a simple task via orchestrator (e.g. small legal or Twilio planning task).  
   - Confirm:
     - An `agent_runs` row exists with tokens + cost.  
     - You can manually call Cynic on the result.  
     - A row appears in `evals_cynic`.

If Item 10 passes cleanly, your MVP environment is **live** and ready for Phase 2 upgrades.
