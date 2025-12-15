# AGENT.MD - Multi-Agent Orchestration Rules
## Billionaire-Speed Execution Protocol v1.0

---

## 🎯 CORE PRINCIPLES

### Time Blocks (NO EXCEPTIONS)
- **1 minute:** Simple queries, status checks, single-file edits
- **5 minutes:** Multi-file changes, API integrations, small features
- **10 minutes:** Complex features, database schemas, deployment configs
- **30 minutes:** Full module implementation, testing suites
- **1 hour:** Complete system integration, production deployment
- **WARNING:** >2 hours = "Could fuck your day Alan" - ABORT AND REFACTOR

### Success Metrics
- **Completion Probability:** Every task gets 1-100% score
- **Error Pre-Detection:** Find ALL errors BEFORE execution
- **Speed:** EXTREME SPEED, NO ERRORS DURING DEV
- **Reporting:** McKinsey-grade, zero fluff, NO EMOJIS EVER

---

## 🏗️ AGENT HIERARCHY

```
┌─────────────────────────────────────┐
│     MASTER ORCHESTRATOR (Claude)    │
│   • Brainstorming & Research        │
│   • Error prediction & mitigation   │
│   • Resource allocation             │
└────────────┬────────────────────────┘
             │
      ┌──────▼──────┐
      │  HARDENER   │
      │ • Validates │
      │ • Optimizes │
      │ • Documents │
      └──────┬──────┘
             │
    ┌────────▼────────┐
    │ PROJECT MANAGER │
    │  • GitHub save  │
    │  • Task chunks  │
    │  • Delegation    │
    └────────┬────────┘
             │
    ┌────────┴────────────────────────┐
    │                                  │
┌───▼───┐ ┌────▼────┐ ┌────▼────┐ ┌──▼───┐
│FRONTEND│ │BACKEND  │ │DATABASE │ │DEPLOY│
│ Agent  │ │  Agent  │ │  Agent  │ │Agent │
└────┬───┘ └────┬────┘ └────┬────┘ └──┬───┘
     │          │            │         │
     └──────────┴────────────┴─────────┘
                    │
            ┌───────▼────────┐
            │ QUALITY CHECKER │
            │  • Test suite   │
            │  • Performance  │
            │  • Security     │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │ FINALIZER      │
            │ • Vercel deploy │
            │ • Rust build   │
            └────────────────┘
```

---

## 📋 AGENT RESPONSIBILITIES

### MASTER ORCHESTRATOR
**Model:** Claude Opus 4.1 (legal) / Sonnet 4.5 (technical)
**Responsibilities:**
- Web search for similar projects/errors
- Identify ALL potential roadblocks
- Calculate completion probability
- Delegate to appropriate sub-agents
- Monitor overall progress

### PROJECT MANAGER AGENT
**Model:** GPT-4 or Claude Sonnet
**Responsibilities:**
- Break projects into 1-60 minute chunks
- Create GitHub issues/milestones
- Assign tasks to worker agents
- Track dependencies
- Update README.md with progress

### WORKER AGENTS

#### Frontend Agent
**Model:** Claude Sonnet / GPT-4
**Tasks:**
- React/Next.js components
- Tailwind CSS styling
- API integration
- State management
- Performance optimization

#### Backend Agent
**Model:** Claude Sonnet / GPT-4
**Tasks:**
- API endpoints
- Authentication
- Business logic
- Third-party integrations
- Error handling

#### Database Agent
**Model:** Claude Sonnet
**Tasks:**
- Schema design
- Migrations
- Query optimization
- Vectorization setup
- Backup strategies

#### Deployment Agent
**Model:** GPT-4
**Tasks:**
- Vercel configuration
- Environment variables
- CI/CD pipeline
- Monitoring setup
- Rollback procedures

### QUALITY CHECKER
**Model:** Claude Opus
**Responsibilities:**
- Run test suites
- Performance benchmarks
- Security scanning
- Code review
- Documentation check

### FINALIZER
**Model:** Any fast model
**Responsibilities:**
- Push to production
- Build Rust desktop app
- Update deployment status
- Notify completion
- Archive project

---

## 🔄 COMMUNICATION PROTOCOL

### Message Format
```json
{
  "agent_id": "frontend_001",
  "task_id": "implement_dashboard",
  "status": "in_progress|completed|blocked|error",
  "completion": 75,
  "time_remaining": "5min",
  "dependencies": ["backend_api_ready"],
  "errors": [],
  "output": {
    "files": ["dashboard.tsx", "dashboard.css"],
    "tests": ["dashboard.test.tsx"],
    "docs": ["dashboard.md"]
  },
  "next_agent": "quality_checker"
}
```

### State Management
- **Redis Key Pattern:** `project:{project_id}:agent:{agent_id}:state`
- **Persistence:** All state changes logged to Supabase
- **Recovery:** Checkpoint every completed task
- **Rollback:** Maintain last 3 good states

### Error Handling
```yaml
error_levels:
  warning: Log and continue
  blocking: Halt agent, escalate to orchestrator
  critical: Full stop, human intervention required
  
recovery_strategy:
  1. Retry with backoff (3 attempts)
  2. Fallback to alternative approach
  3. Escalate to orchestrator
  4. Request human input
```

---

## 🚀 EXECUTION WORKFLOW

### Phase 1: BRAINSTORM (1-5 min)
```bash
1. Master receives idea/request
2. Web search for similar implementations
3. Identify ALL potential issues
4. Calculate completion probability
5. If <70%, refactor approach
```

### Phase 2: HARDEN (5-10 min)
```bash
1. Validate technical feasibility
2. Create project structure
3. Define test criteria
4. Document approach
5. Save to GitHub as project
```

### Phase 3: CHUNK (5 min)
```bash
1. Project Manager breaks into tasks
2. Each task gets time estimate
3. Dependencies mapped
4. Agents assigned
5. Execution order determined
```

### Phase 4: EXECUTE (varies)
```bash
1. Agents work in parallel where possible
2. State updates every 30 seconds
3. Blockers immediately escalated
4. Progress tracked in real-time
5. Automatic error recovery
```

### Phase 5: VALIDATE (5-10 min)
```bash
1. Quality checker runs all tests
2. Performance benchmarks
3. Security scan
4. Documentation review
5. Final approval
```

### Phase 6: DEPLOY (1-5 min)
```bash
1. Push to GitHub main
2. Vercel auto-deploy triggered
3. Rust desktop build
4. Monitoring activated
5. Success notification
```

---

## 🛠️ TOOLS & INTEGRATIONS

### Required MCP Servers
- **xcodebuild:** Full Xcode project creation/compilation
- **Supabase:** Vector DB and state management
- **Vercel:** Deployment and hosting
- **GitHub:** Version control and project management
- **Redis:** Inter-agent communication
- **OpenTelemetry:** Performance monitoring

### API Integrations
- **OpenAI:** GPT-4 for worker agents
- **Anthropic:** Claude for orchestration
- **Twilio:** Communication services
- **Stripe:** Payment processing
- **Court Listener:** Legal data
- **Pacer Monitor:** Case tracking

### Development Tools
- **Primary IDE:** Cursor with Claude CLI
- **Backup IDE:** VSCode with Copilot
- **Terminal:** Claude Code CLI 4.5
- **Testing:** Jest, Playwright
- **Monitoring:** Datadog, Sentry

---

## 📊 PERFORMANCE METRICS

### Speed Targets
- **Idea to Prototype:** 30 minutes
- **Prototype to MVP:** 2 hours
- **MVP to Production:** 4 hours
- **Bug Fix:** 5-15 minutes
- **Feature Addition:** 30-60 minutes

### Quality Metrics
- **Test Coverage:** >80%
- **Performance Score:** >90/100
- **Security Score:** A+
- **Documentation:** 100% complete
- **Error Rate:** <0.1%

### Business Metrics
- **Cost per Feature:** Track and optimize
- **Revenue Impact:** Measure everything
- **User Satisfaction:** >95%
- **Uptime:** 99.9%
- **Response Time:** <200ms

---

## 🔐 SECURITY PROTOCOLS

### Credential Management
- **Never hardcode:** Use environment variables
- **Rotate regularly:** Monthly minimum
- **Audit access:** Weekly review
- **Encrypt at rest:** Always
- **Zero trust:** Verify everything

### Data Protection
- **PII handling:** Strict compliance
- **Encryption:** AES-256 minimum
- **Backup:** 3-2-1 strategy
- **Recovery:** <1 hour RTO
- **Audit logs:** Immutable

---

## 🚨 EMERGENCY PROTOCOLS

### When Things Go Wrong
```yaml
severity_levels:
  1_minor: Fix and continue
  2_moderate: Pause and assess
  3_major: Rollback immediately
  4_critical: All stop, escalate
  5_catastrophic: Activate disaster recovery

escalation_path:
  1. Worker Agent → Project Manager
  2. Project Manager → Master Orchestrator
  3. Master Orchestrator → Human (Alan)
  4. Human → Emergency response team
```

### Recovery Procedures
1. **Identify root cause** (5 min max)
2. **Isolate affected systems**
3. **Rollback to last known good**
4. **Apply fix**
5. **Test thoroughly**
6. **Deploy carefully**
7. **Monitor closely**
8. **Document everything**

---

## 📝 DOCUMENTATION REQUIREMENTS

### Every Task Must Have
- **README.md:** Project overview and setup
- **CHANGELOG.md:** Version history
- **API.md:** Endpoint documentation
- **TESTING.md:** Test instructions
- **DEPLOY.md:** Deployment guide

### Code Standards
- **Comments:** Explain WHY, not WHAT
- **Functions:** Single responsibility
- **Files:** <300 lines
- **Tests:** One per function minimum
- **Types:** TypeScript/typed Python

---

## 🎯 SUCCESS CRITERIA

### Task Completion
✅ All tests passing
✅ Performance targets met
✅ Security scan clean
✅ Documentation complete
✅ Deployed successfully
✅ Monitoring active
✅ Stakeholder approved

### Project Success
✅ Delivered on time (<2 hours)
✅ Under budget
✅ Zero critical bugs
✅ 95%+ user satisfaction
✅ Revenue positive
✅ Scalable architecture
✅ Maintainable code

---

## 🔄 CONTINUOUS IMPROVEMENT

### Daily Review
- What worked?
- What didn't?
- What was slow?
- What failed?
- How to improve?

### Weekly Optimization
- Refactor slow code
- Update agent prompts
- Improve error handling
- Enhance monitoring
- Update documentation

### Monthly Evolution
- Evaluate new models
- Test new tools
- Refine workflows
- Update metrics
- Train on new patterns

---

## ⚡ QUICK REFERENCE

### Time Boxing
- 1 min: Status check
- 5 min: Simple feature
- 10 min: Complex feature
- 30 min: Full module
- 1 hour: Complete system
- ABORT if >2 hours

### Error Prevention
1. Web search first
2. Check similar projects
3. List ALL roadblocks
4. Plan mitigations
5. Calculate probability
6. Execute only if >70%

### Communication
- Update every 30 seconds
- Escalate immediately
- Document everything
- No surprises
- McKinsey quality
- NO EMOJIS

---

*"Speed of light execution. Zero tolerance for inefficiency. Billionaire thinking only."*

**Last Updated:** November 2024
**Version:** 1.0.0
**Status:** ACTIVE
