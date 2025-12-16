# ATTORNEY COORDINATION PROMPTS
## Prompts for Case Management and Team Coordination

---

## PROMPT 1: DEADLINE TRACKING SETUP

### Input
```
Initialize deadline tracking for:

**Case:** [Case name/number]
**Court:** [Jurisdiction]
**Key Dates:**
- Trial Date: [Date]
- Discovery Cutoff: [Date]
- Dispositive Motion Deadline: [Date]
- [Additional dates]

**Standing Orders:** [Any court-specific deadline rules]

Setup: Automated alerts, escalation protocols, contingency planning
```

### Expected Output
```markdown
# DEADLINE MANAGEMENT SYSTEM INITIALIZED

## MASTER DEADLINE CALENDAR
[Comprehensive list with alert schedule]

## ALERT PROTOCOL
**Critical (Statutory):** Alerts at 30, 14, 7, 3, 1 days
**High (Court-Ordered):** Alerts at 14, 7, 3 days
**Medium (Discovery):** Alerts at 7, 3 days

## CURRENT STATUS
**Next Critical Deadline:** [Date - Description]
**Days Remaining:** [X]
**Status:** [ON TRACK / AT RISK / OVERDUE]
**Action Required:** [Immediate steps]

## CONTINGENCY PLANS
[For each critical deadline, backup plan if primary timeline at risk]
```

---

## PROMPT 2: DAILY STATUS UPDATE GENERATION

### Input
```
Generate daily case status update for:

**Case:** [Name]
**Date:** [Date]
**Recipients:** [Attorney team members]

Include: Accomplishments, in-progress tasks, blockers, upcoming deadlines, action items
```

### Expected Output
```markdown
# DAILY CASE STATUS - [Date]

## ACCOMPLISHMENTS TODAY
✅ [Completed items]

## IN PROGRESS
⏳ [Tasks underway with % complete and owner]

## BLOCKERS
⚠️ [Issues requiring resolution]
**Action:** [Who needs to do what]

## UPCOMING DEADLINES (Next 7 Days)
🚨 [Critical deadlines with days remaining]

## ACTION ITEMS FOR TOMORROW
- [ ] [Task 1 - Owner]
- [ ] [Task 2 - Owner]

## TEAM WORKLOAD
[Capacity analysis for each attorney/paralegal]

**Recommendations:** [Any reallocation needed]
```

---

## PROMPT 3: RESOURCE REALLOCATION ANALYSIS

### Input
```
Analyze workload and recommend reallocation:

**Team Members:** [List with current capacity %]
**Critical Deadlines:** [Upcoming deadlines requiring resources]
**Current Task Assignments:** [Who is doing what]

Optimize for: Deadline adherence, skill matching, workload balance
```

### Expected Output
```markdown
# RESOURCE REALLOCATION RECOMMENDATIONS

## CURRENT WORKLOAD ANALYSIS
[Table showing each team member's capacity and critical tasks]

## BOTTLENECKS IDENTIFIED
[Tasks at risk due to over-allocation]

## REALLOCATION RECOMMENDATIONS

### RECOMMENDATION #1
**Task:** [Description]
**From:** [Current assignee - X% capacity]
**To:** [Proposed assignee - Y% capacity]
**Rationale:** [Explanation]
**Impact:** [Effect on deadlines and workload]
**Priority:** [HIGH/MEDIUM/LOW]

**Action:** [Specific steps to reallocate]

[Additional recommendations]

## PROJECTED WORKLOAD POST-REALLOCATION
[Updated capacity table showing improvement]
```

---

## PROMPT 4: RISK ASSESSMENT & ESCALATION

### Input
```
Assess case risks in:

**Case:** [Name]
**Focus Areas:** [Deadlines/Budget/Merits/Client Relations]
**Recent Developments:** [Any changes since last assessment]

Deliverable: Risk dashboard with escalation recommendations
```

### Expected Output
```markdown
# CASE RISK ASSESSMENT
**Assessment Date:** [Date]
**Overall Risk Level:** [RED/YELLOW/GREEN]

## RISK BREAKDOWN

### DEADLINE RISK: [COLOR]
**Status:** [Description]
**Impact:** [HIGH/MODERATE/LOW]
**Probability:** [X]%
**Mitigation:** [Actions being taken]

### BUDGET RISK: [COLOR]
[Similar structure]

### MERITS RISK: [COLOR]
[Similar structure]

### CLIENT SATISFACTION: [COLOR]
[Similar structure]

## ESCALATION RECOMMENDATIONS
[Items requiring managing partner/client notification]

## ACTION ITEMS
[Specific risk mitigation steps with owners and deadlines]
```

---

## PROMPT 5: MEETING AGENDA GENERATION

### Input
```
Generate agenda for:

**Meeting Type:** [Strategy/Status/Client Update]
**Attendees:** [List]
**Duration:** [Time]
**Objectives:** [Key decisions needed or updates to provide]

Prior Context: [Recent developments, last meeting notes]
```

### Expected Output
```markdown
# MEETING AGENDA
**Date/Time:** [When]
**Duration:** [X minutes]
**Attendees:** [List]
**Objective:** [Purpose]

## AGENDA ITEMS

### 1. Case Status Review (10 minutes)
- Discovery progress update
- Recent motion rulings
- Upcoming deadlines

### 2. Strategic Decisions Needed (20 minutes)
**Decision #1:** [Description]
- **Background:** [Context]
- **Options:** [A, B, C]
- **Recommendation:** [With rationale]
- **Required Decision-Maker:** [Who must decide]

[Additional items]

### 3. Resource Allocation (10 minutes)
- Workload review
- Reallocation proposals

### 4. Client Communication (10 minutes)
- Update to client on [topic]
- Decisions needed from client

### 5. Next Steps & Action Items (10 minutes)
- Assign tasks
- Set deadlines
- Schedule next meeting

## PRE-MEETING MATERIALS
[Documents to review before meeting]

## POST-MEETING ACTIONS
[Follow-up tasks anticipated]
```

---

## PROMPT 6: SETTLEMENT POSITIONING MEMO

### Input
```
Prepare settlement positioning memo for:

**Case:** [Name]
**Settlement Conference Date:** [Date]
**Mediator:** [Name]
**Current Posture:** [Last demand/offer]

Include: Case strength, valuation, strategy, opening position, walk-away number
```

---

## PROMPT 7: TRIAL PREPARATION CHECKLIST

### Input
```
Generate trial preparation checklist for:

**Trial Date:** [Date]
**Days Until Trial:** [X]
**Case Type:** [e.g., Product Liability]

Deliverable: Comprehensive checklist with deadlines and assignments
```

---

## COORDINATION QUALITY STANDARDS

### Deadline Tracking
- Zero missed deadlines (target: 100%)
- Alert timeliness: 100% on schedule
- Contingency plans for all critical deadlines

### Status Updates
- Daily updates by 5pm each day
- Accuracy of progress reporting: >95%
- Actionable recommendations in every update

### Resource Management
- Team utilization: 70-85% (optimal range)
- Overload alerts: Trigger at >90% capacity
- Skill-task matching: Appropriate assignments

---

END ATTORNEY COORDINATION PROMPTS
