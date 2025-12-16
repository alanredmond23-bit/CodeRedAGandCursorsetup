# CURSOR IDE RULES - CODERED LEGAL DISCOVERY

**Role**: Cursor IDE Integration for Legal Discovery Workflow with CodeRed AG
**Goal**: Enable in-IDE AI agent interaction with RAG context, cost tracking, and privilege protection
**Version**: 1.0
**Last Updated**: December 16, 2025

---

## KEYBOARD SHORTCUTS (6 AGENT MODES)

Press these keyboard shortcuts to invoke specialized agents:

| Shortcut | Agent | LLM Model | Purpose | Zone Access | Cost |
|----------|-------|-----------|---------|-------------|------|
| `Cmd+Shift+A` | **ARCHITECT** | gpt-4o | System design, case strategy, architecture | Red/Yellow/Green | $3-5/query |
| `Cmd+Shift+C` | **CODE** | gpt-4o | Implementation, document parsing, automation | Yellow/Green | $2-3/query |
| `Cmd+Shift+T` | **TEST** | gpt-4o-mini | Testing, validation, QA | Green only | $0.10-0.50/query |
| `Cmd+Shift+R` | **REVIEW** | gpt-4o | Code review, legal document review | Yellow/Green | $2-3/query |
| `Cmd+Shift+E` | **EVIDENCE** | gpt-4o | Evidence analysis, timeline reconstruction | Red/Yellow | $3-4/query |
| `Cmd+Shift+S` | **CYNIC** | gpt-4o | Risk assessment, devil's advocate, privilege check | Red only | $3-5/query |

**Usage**:
1. Open any file in Cursor
2. Press shortcut (e.g., `Cmd+Shift+A`)
3. Agent activates with RAG context automatically injected
4. Cost is logged to CodeRed Supabase
5. Privilege violations are flagged

---

## ZONE-BASED PERMISSIONS

### RED ZONE (Highly Privileged)
**Access**: ARCHITECT, EVIDENCE, CYNIC agents only
**Requires**: Senior attorney approval + Cynic clearance
**Content**:
- Attorney-client privileged communications
- Work product (case strategy, legal research memos)
- Confidential settlement negotiations
- Expert witness strategies
- Trial preparation materials

**Rules**:
- Must not be exposed to unauthorized agents
- Logging mandatory (audit trail)
- Cost ceiling: $10/query max
- Approval workflow triggers automatically

### YELLOW ZONE (Moderately Sensitive)
**Access**: ARCHITECT, CODE, REVIEW, EVIDENCE agents
**Requires**: Standard review process
**Content**:
- Discovery documents (emails, contracts)
- Financial records under protective order
- Depositions (non-privileged)
- Court filings (unsealed)
- Case timelines

**Rules**:
- Review required but not blocking
- Cost ceiling: $5/query max
- Logging for billing purposes

### GREEN ZONE (Public/Low Risk)
**Access**: All agents
**Requires**: No approval
**Content**:
- Public court records
- Case law and statutes
- Non-confidential emails
- Administrative documents
- Templates and playbooks

**Rules**:
- Autonomous operation allowed
- Cost ceiling: $2/query max
- Standard logging

---

## AUTOMATIC RAG CONTEXT INJECTION

When you invoke an agent (via keyboard shortcut), the system automatically:

1. **Detects Current File Context**
   - File path, line number, selection
   - Case ID (extracted from file metadata or path)
   - Document type (email, contract, deposition, etc.)

2. **Fetches Relevant RAG Context**
   ```python
   # Automatically runs in background:
   rag_context = fetch_case_context(
       case_id=detect_case_id(current_file),
       query=current_selection or current_line,
       top_k=5,
       include_precedents=True
   )
   ```

3. **Injects into Agent Prompt**
   ```
   [SYSTEM]
   You are the ARCHITECT agent for legal discovery.

   [CASE CONTEXT - AUTO-FETCHED]
   Case ID: CUSTODY-2024-001
   Relevant Documents:
   - Email: Smith to Jones, March 15, 2024 (custodial interference)
   - Deposition: Jane Smith, April 2, 2024 (timeline conflict)
   - Court Filing: Motion for Modification, May 1, 2024

   [LEGAL PRECEDENTS]
   - In re Marriage of Johnson (2022) - custody modification standards
   - Smith v. Doe (2023) - evidence of parental alienation

   [USER QUERY]
   {your_question_here}
   ```

4. **Returns Response with Citations**
   ```
   Based on the evidence in Smith's email (March 15) and her deposition
   testimony (April 2), there appears to be a timeline inconsistency...

   [CITATIONS]
   - Email: /cases/CUSTODY-2024-001/emails/smith_001.pdf
   - Deposition: /cases/CUSTODY-2024-001/deps/smith_dep.txt:lines 145-167
   ```

---

## COST TRACKING

Every agent invocation is logged to CodeRed Supabase:

```sql
INSERT INTO codered.agent_runs (
  agent_id,
  task_id,
  case_id,
  attorney_id,
  zone_access,
  query_text,
  response_text,
  approx_cost_usd,
  tokens_used,
  created_at
) VALUES (
  'architect',
  'current_task_id',
  'CUSTODY-2024-001',
  'attorney_john_doe',
  'RED',
  'Analyze timeline inconsistencies',
  '[Response truncated for storage]',
  3.45,
  2500,
  NOW()
);
```

**Cost Monitoring**:
- Real-time cost display in Cursor status bar
- Daily budget alerts (per attorney)
- Monthly cost reports (per case)
- Approval gates for Red zone queries over $10

**Dashboard Query** (run in Supabase):
```sql
-- Today's costs by agent
SELECT agent_id, COUNT(*), SUM(approx_cost_usd) as total_cost
FROM codered.agent_runs
WHERE created_at >= CURRENT_DATE
GROUP BY agent_id
ORDER BY total_cost DESC;
```

---

## PRIVILEGE DETECTION

Before any agent processes a document, privilege detection runs automatically:

```python
# privilege-detector.py (runs in background)
def detect_privilege(document_text):
    """
    Returns: {
      "is_privileged": True/False,
      "confidence": 0.0-1.0,
      "keywords_found": ["attorney", "legal advice"],
      "recommendation": "RED_ZONE"
    }
    """
    privilege_keywords = [
        "attorney", "lawyer", "legal counsel", "privileged",
        "confidential", "work product", "settlement strategy",
        "trial preparation", "expert witness strategy"
    ]

    # Check for keywords
    found_keywords = [kw for kw in privilege_keywords if kw in document_text.lower()]

    # Check for patterns (e.g., "From: john.smith@law.com")
    attorney_email_pattern = r'\b\w+@\w+law\.\w+\b'
    attorney_emails = re.findall(attorney_email_pattern, document_text)

    # Confidence scoring
    confidence = min(1.0, (len(found_keywords) * 0.2) + (len(attorney_emails) * 0.3))

    return {
        "is_privileged": confidence > 0.5,
        "confidence": confidence,
        "keywords_found": found_keywords,
        "attorney_emails": attorney_emails,
        "recommendation": "RED_ZONE" if confidence > 0.7 else "YELLOW_ZONE"
    }
```

**Flagging Process**:
1. Document opened in Cursor
2. Privilege detector scans in background
3. If privileged (confidence > 0.5):
   - Red banner appears in Cursor
   - Only Architect/Evidence/Cynic agents allowed
   - Cost tracking marks as RED_ZONE
   - Audit log entry created
4. If uncertain (confidence 0.3-0.5):
   - Yellow banner appears
   - Human review recommended
5. If not privileged (confidence < 0.3):
   - Green banner (or no banner)
   - All agents allowed

---

## CURSOR RULES (APPLIED TO ALL AGENTS)

### 1. ELON PROTOCOL (Simplicity First)
- Follow the 5-step algorithm (see ELONRULE.md)
- Question requirements before implementing
- Delete unnecessary code/features
- Simplify before optimizing
- Accelerate iteration speed
- Automate only stable, boring tasks

### 2. LEGAL COMPLIANCE
- Respect attorney-client privilege (automatic detection)
- Maintain audit trail (all queries logged)
- Human attorney makes final decisions (agents advise only)
- Proportionality in discovery (don't over-process)
- Metadata preservation (track document provenance)

### 3. COST AWARENESS
- Always display estimated cost before query
- Warn if query will exceed daily budget
- Use cheaper models when appropriate (Test agent uses gpt-4o-mini)
- Batch operations to reduce API calls
- Cache RAG results to avoid redundant embeddings

### 4. CITATION DISCIPLINE
- Every agent response must cite sources
- Link to original documents (file paths)
- Include page numbers, line numbers, timestamps
- Distinguish between:
  - Evidence (factual)
  - Precedents (legal authority)
  - Agent inferences (analysis)

### 5. ZONE ENFORCEMENT
- Agents cannot access zones they're not authorized for
- Attempting to access Red zone triggers approval workflow
- Zone violations logged and reported
- Privilege breaches immediately flagged

---

## AGENT-SPECIFIC RULES

### ARCHITECT Agent (Cmd+Shift+A)
**Purpose**: High-level case strategy, system architecture
**Access**: Red/Yellow/Green zones
**Capabilities**:
- Case strength assessment (A/B/C/D/E framework)
- Settlement value estimation
- Legal strategy recommendations
- Research direction planning
- Expert witness identification

**Example Workflow**:
1. Open case summary file
2. Press `Cmd+Shift+A`
3. Ask: "What is our case strength? Identify key weaknesses."
4. Architect fetches:
   - All case documents (RAG)
   - Relevant precedents (Westlaw/LexisNexis)
   - Prior case assessments
5. Returns:
   - Overall grade (e.g., "B+ case")
   - Key strengths (3-5 bullet points)
   - Critical weaknesses (2-3 bullet points)
   - Recommended strategy
   - Estimated settlement range

**Cost**: $3-5 per comprehensive analysis

---

### CODE Agent (Cmd+Shift+C)
**Purpose**: Implementation, automation, document parsing
**Access**: Yellow/Green zones
**Capabilities**:
- Write document parsing scripts
- Automate discovery workflows
- Create data extraction pipelines
- Build timeline reconstruction tools
- Generate report templates

**Example Workflow**:
1. Open batch of emails
2. Press `Cmd+Shift+C`
3. Ask: "Parse these emails and extract: sender, date, subject, key facts"
4. Code agent:
   - Generates Python script
   - Parses emails using NLP
   - Extracts structured data
   - Outputs CSV/JSON
5. Returns:
   - Parsing script (ready to run)
   - Extracted data
   - Error handling

**Cost**: $2-3 per implementation task

---

### TEST Agent (Cmd+Shift+T)
**Purpose**: Quality assurance, validation, testing
**Access**: Green zone only
**Capabilities**:
- Test document parsing accuracy
- Validate timeline consistency
- Check data integrity
- Verify citation accuracy
- QA generated reports

**Example Workflow**:
1. Open generated timeline
2. Press `Cmd+Shift+T`
3. Ask: "Validate this timeline against source documents"
4. Test agent:
   - Cross-references every date
   - Checks for contradictions
   - Verifies citations
   - Flags anomalies
5. Returns:
   - Validation report
   - List of errors/warnings
   - Suggested corrections

**Cost**: $0.10-0.50 per test (using gpt-4o-mini for cost efficiency)

---

### REVIEW Agent (Cmd+Shift+R)
**Purpose**: Code review, document review, quality gates
**Access**: Yellow/Green zones
**Capabilities**:
- Review code quality
- Check document completeness
- Verify legal citations
- Assess argument strength
- Identify gaps in discovery

**Example Workflow**:
1. Open draft motion
2. Press `Cmd+Shift+R`
3. Ask: "Review this motion for legal sufficiency"
4. Review agent:
   - Checks all legal citations
   - Verifies factual statements against evidence
   - Assesses argument logic
   - Identifies missing authorities
5. Returns:
   - Review report
   - Specific issues (with line numbers)
   - Suggested improvements
   - Missing citations

**Cost**: $2-3 per review task

---

### EVIDENCE Agent (Cmd+Shift+E)
**Purpose**: Evidence analysis, pattern recognition, timeline reconstruction
**Access**: Red/Yellow zones
**Capabilities**:
- Timeline analysis across documents
- Contradiction detection
- Financial flow tracking
- Communication pattern analysis
- Behavioral anomaly detection

**Example Workflow**:
1. Open case folder with 1,000+ documents
2. Press `Cmd+Shift+E`
3. Ask: "Find all contradictions between witness depositions and emails"
4. Evidence agent:
   - Scans all depositions (OCR'd)
   - Scans all emails (text extracted)
   - Compares statements
   - Identifies inconsistencies
5. Returns:
   - Contradiction report
   - Side-by-side comparisons
   - Citations to specific documents
   - Timeline visualization

**Cost**: $3-4 per analysis task

---

### CYNIC Agent (Cmd+Shift+S)
**Purpose**: Risk assessment, devil's advocate, privilege protection
**Access**: Red zone only
**Capabilities**:
- Challenge case assumptions
- Identify weaknesses opposing counsel will exploit
- Assess privilege waiver risks
- Evaluate ethical compliance
- Red-team legal strategy

**Example Workflow**:
1. Open proposed settlement strategy
2. Press `Cmd+Shift+S`
3. Ask: "What are the risks of this settlement approach?"
4. Cynic agent:
   - Analyzes strategy critically
   - Identifies potential pitfalls
   - Considers opposing counsel's perspective
   - Checks for privilege issues
   - Assesses ethical compliance
5. Returns:
   - Risk assessment (1-10 scale)
   - Specific risks (ranked by severity)
   - Recommended mitigations
   - Privilege warnings
   - Ethical considerations

**Cost**: $3-5 per risk assessment

---

## INTEGRATION WITH CODERED SUPABASE

All Cursor agents connect to CodeRed database via MCP:

```yaml
# .cursor/mcp-config.yaml
mcpServers:
  supabase-codered:
    command: "python"
    args: ["/Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/codered-client.py"]
    env:
      SUPABASE_URL: "${SUPABASE_URL}"
      SUPABASE_SERVICE_KEY: "${SUPABASE_SERVICE_KEY}"
    capabilities:
      - log_agent_runs
      - fetch_rag_context
      - track_costs
      - detect_privilege
      - query_cases
      - update_tasks
```

**Database Operations**:
1. **Log Agent Run**: Every shortcut press logs to `codered.agent_runs`
2. **Fetch RAG Context**: Queries `codered.embeddings` for relevant docs
3. **Track Costs**: Updates `codered.cost_tracking` table
4. **Detect Privilege**: Checks `codered.privilege_flags` table
5. **Query Cases**: Retrieves case metadata from `codered.cases`
6. **Update Tasks**: Marks tasks complete in `codered.tasks`

---

## WORKFLOW EXAMPLE

**Scenario**: Analyzing timeline inconsistencies in custody case

1. **Open email** in Cursor: `/cases/CUSTODY-2024-001/emails/smith_march15.pdf`

2. **Press `Cmd+Shift+E`** (Evidence agent)

3. **Privilege detector runs**:
   - Scans email content
   - Detects "attorney" keyword
   - Confidence: 0.8 (HIGH)
   - Flags as RED ZONE
   - Only Evidence agent allowed (authorized for Red)

4. **RAG context fetched**:
   - Queries `codered.embeddings` with: "timeline March 2024 custody"
   - Returns:
     - Email: Smith to Jones, March 15 (current file)
     - Deposition: Smith testimony, April 2 (lines 145-167)
     - Court filing: Motion for modification, May 1
     - Precedent: *In re Johnson* (custody timeline analysis)

5. **Evidence agent processes**:
   - Compares email date/content with deposition testimony
   - Identifies contradiction:
     - Email says: "I was in California on March 15"
     - Deposition says: "I was in New York on March 15"
   - Calculates confidence: 0.95 (HIGH)

6. **Returns response**:
   ```
   TIMELINE INCONSISTENCY DETECTED

   Contradiction: Jane Smith's location on March 15, 2024

   Evidence 1: Email to opposing party
   - Source: /cases/CUSTODY-2024-001/emails/smith_march15.pdf
   - Date: March 15, 2024
   - Statement: "I was in California on March 15"

   Evidence 2: Deposition testimony
   - Source: /cases/CUSTODY-2024-001/deps/smith_dep.txt:lines 145-167
   - Date: April 2, 2024 (testimony about March 15)
   - Statement: "I was in New York on March 15"

   Analysis: Direct contradiction. Smith cannot have been in both locations.

   Recommendation: Cross-examine on this inconsistency. Request phone records
   or credit card statements to verify actual location.

   [COST: $3.25 | ZONE: RED | LOGGED: agent_run_12345]
   ```

7. **Cost logged to Supabase**:
   ```sql
   INSERT INTO codered.agent_runs VALUES (
     'run_12345',
     'evidence',
     'CUSTODY-2024-001',
     'attorney_john_doe',
     'RED',
     'Find timeline inconsistencies',
     '[Response above]',
     3.25,
     2100,
     NOW()
   );
   ```

8. **Dashboard updated**:
   - Attorney John Doe: $3.25 spent today
   - Case CUSTODY-2024-001: $3.25 spent today
   - Evidence agent: 1 query, $3.25 avg cost

---

## TROUBLESHOOTING

### Agent not responding
**Cause**: MCP connection to Supabase failed
**Fix**:
```bash
# Check credentials
cat /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/.env.local

# Test connection
python /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/codered-client.py test
```

### RAG context not appearing
**Cause**: Embeddings not generated for case documents
**Fix**:
```sql
-- Check embeddings exist
SELECT COUNT(*) FROM codered.embeddings WHERE case_id = 'CUSTODY-2024-001';

-- If none, ingest documents
SELECT codered.ingest_document('Title', 'Content', 'source_path', 'CUSTODY-2024-001');
```

### Privilege detection inaccurate
**Cause**: Keywords not tuned for your jurisdiction
**Fix**: Update `privilege-detector.py` with jurisdiction-specific keywords

### Costs too high
**Cause**: Using gpt-4o for tasks that could use gpt-4o-mini
**Fix**:
- Use Test agent (gpt-4o-mini) for simple validation
- Cache RAG results to reduce embeddings API calls
- Batch queries instead of one-by-one

---

## KEYBOARD SHORTCUT REFERENCE CARD

```
╔══════════════════════════════════════════════════════════════════╗
║           CURSOR IDE - CODERED LEGAL DISCOVERY                   ║
║                  KEYBOARD SHORTCUTS                              ║
╠══════════════════════════════════════════════════════════════════╣
║ Cmd+Shift+A  │  ARCHITECT   │  Strategy & Architecture          ║
║ Cmd+Shift+C  │  CODE        │  Implementation & Automation      ║
║ Cmd+Shift+T  │  TEST        │  QA & Validation (cheap)          ║
║ Cmd+Shift+R  │  REVIEW      │  Code/Document Review             ║
║ Cmd+Shift+E  │  EVIDENCE    │  Timeline & Pattern Analysis      ║
║ Cmd+Shift+S  │  CYNIC       │  Risk Assessment & Red Team       ║
╠══════════════════════════════════════════════════════════════════╣
║ ZONES:                                                           ║
║ 🔴 RED    = Privileged (Architect/Evidence/Cynic only)          ║
║ 🟡 YELLOW = Sensitive (All except Test)                         ║
║ 🟢 GREEN  = Public (All agents)                                 ║
╠══════════════════════════════════════════════════════════════════╣
║ Auto-Features:                                                   ║
║ ✓ RAG context injection                                         ║
║ ✓ Cost tracking                                                 ║
║ ✓ Privilege detection                                           ║
║ ✓ Citation linking                                              ║
╚══════════════════════════════════════════════════════════════════╝
```

---

**Last Updated**: December 16, 2025
**Version**: 1.0
**System**: CodeRed Legal Discovery Orchestrator
