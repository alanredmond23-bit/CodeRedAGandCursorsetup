# 🏛️ LEGAL TECH ORCHESTRATION ARCHITECTURE

**Complete System for AI-Powered Legal Discovery & Case Management**
**Built for: Personal Legal Cases (Custody, FEDS, Bankruptcy, Malpractice)**
**Scope: Millions of documents, Multiple attorneys, Real-time coordination**

---

## 🎯 SYSTEM OVERVIEW

```
┌────────────────────────────────────────────────────────────────────────┐
│                     CODERED LEGAL ORCHESTRATOR                         │
│        (Supabase PostgreSQL + CrewAI + RAG + Multi-Agent System)       │
│                                                                         │
│  ┌─ Agents Registry ─┐  ┌─ Cost Tracking ─┐  ┌─ RAG Database ────┐  │
│  │ - Discovery Bot   │  │ - Per-attorney  │  │ - Case files      │  │
│  │ - Coordinator Bot │  │ - Per-task      │  │ - Legal precedents│  │
│  │ - Strategy Bot    │  │ - Per-document  │  │ - Playbooks       │  │
│  │ - Evidence Bot    │  │ - Per-mode      │  │ - Comm threads    │  │
│  │ - Analysis Bot    │  │ - Audit log     │  │ - Indexed search  │  │
│  └───────────────────┘  └─────────────────┘  └───────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
         ▲                       ▲                         ▲
         │                       │                         │
    ┌────┴────┐        ┌────────┴────────┐       ┌────────┴────────┐
    │          │        │                 │       │                 │
    ▼          ▼        ▼                 ▼       ▼                 ▼
┌─────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐
│ CURSOR  │ │ANTIGRAV. │ │ CLAUDE CODE  │ │   GITHUB    │ │  VERCEL    │
│  IDE    │ │(Cloud)   │ │  TERMINAL    │ │  ACTIONS    │ │ DEPLOYMENT │
│         │ │          │ │   (CLI)      │ │  (CI/CD)    │ │ (Frontend) │
└─────────┘ └──────────┘ └──────────────┘ └──────────────┘ └─────────────┘
    │           │            │                   │              │
    └───────────┴────────────┴───────────────────┴──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Westlaw/   │
                    │  LexisNexis  │
                    │     APIs     │
                    └──────────────┘
```

---

## 🤖 FIVE SPECIALIZED AGENTS

### **1. DISCOVERY BOT** (Extraction & Analysis)
- **Purpose**: Parse millions of documents, extract evidence
- **Capabilities**:
  - Document classification (email, contract, deposition, etc.)
  - Entity extraction (people, dates, amounts, locations)
  - Timeline construction from scattered documents
  - Privilege detection and flagging
  - Relevance scoring
- **Tools**: DISCO/Everlaw/Logikcull APIs + Claude AI
- **Cost Model**: Gold (gpt-4o) - $2-3 per 1K documents
- **Zone Access**: All zones (RED documents possible)
- **Output**: Structured evidence summaries with citations

### **2. ATTORNEY COORDINATOR BOT** (Workflow Management)
- **Purpose**: Manage 6 attorneys, deadlines, deliverables
- **Capabilities**:
  - Track which attorney assigned to which task
  - Deadline reminders and escalation
  - Work product consolidation
  - Meeting scheduling and minutes
  - Status updates and reports
- **Tools**: Clio/SmartAdvocate APIs + Calendar/Slack integration
- **Cost Model**: Silver (gpt-4o-mini) - $1 per coordinator action
- **Zone Access**: Yellow/Green only
- **Output**: Automated status reports, alerts, dashboards

### **3. LEGAL STRATEGY BOT** (Case Analysis & Research)
- **Purpose**: Research case law, find winning arguments
- **Capabilities**:
  - Westlaw/LexisNexis research automation
  - Precedent analysis and comparison
  - Argument strength assessment
  - Risk analysis on legal theories
  - Opposition counter-argument generation
- **Tools**: Westlaw API + LexisNexis API + Claude
- **Cost Model**: Gold (gpt-4o) - $2-3 per research task
- **Zone Access**: All zones (RED strategy needed)
- **Output**: Legal memoranda, precedent summaries, strategy recommendations

### **4. EVIDENCE ANALYSIS BOT** (Pattern Recognition)
- **Purpose**: Find connections, patterns, inconsistencies
- **Capabilities**:
  - Timeline validation across documents
  - Contradictions between witnesses/evidence
  - Financial flow analysis
  - Communication pattern analysis
  - Behavioral anomalies
- **Tools**: RAG + Advanced search + Claude
- **Cost Model**: Gold (gpt-4o) - $3-4 per analysis task
- **Zone Access**: All zones (RED evidence critical)
- **Output**: Evidence maps, contradiction reports, pattern analysis

### **5. CASE ANALYSIS BOT** (Holistic Assessment)
- **Purpose**: Overall case strength, settlement value, risk assessment
- **Capabilities**:
  - Case strength scoring (A/B/C/D/E framework)
  - Settlement range estimation
  - Win probability assessment
  - Key weakness identification
  - Trial readiness evaluation
- **Tools**: All other bots + RAG + Claude Opus
- **Cost Model**: Gold (gpt-4o) - $3-5 per comprehensive analysis
- **Zone Access**: Red/Yellow (requires approval)
- **Output**: Executive case assessment, recommendations

---

## 🔌 CRITICAL MCPs (Model Context Protocol Integrations)

### **MCP #1: Westlaw Legal Research**
```yaml
name: westlaw-mcp
description: Access 100+ Thomson Reuters APIs for legal research
authentication: API key (from Thomson Reuters Developer Portal)
capabilities:
  - Full case law search
  - Statute and regulation access
  - Secondary sources (treatises, restatements)
  - Practice guides
  - AI-assisted research (Thomson Reuters AI)
endpoints:
  - /content/search (full-text search)
  - /content/cases/{cite} (retrieve specific case)
  - /statutes (statutory research)
  - /precedent-finder (find similar cases)
cost_model: Pay-per-query ($0.10-1.00 per query)
credentials_location: ~/.env.local → WESTLAW_API_KEY
```

### **MCP #2: LexisNexis Legal Research**
```yaml
name: lexisnexis-mcp
description: Access LexisNexis Protégé AI + 99% of legal content
authentication: OAuth (LexisNexis API Portal)
capabilities:
  - Comprehensive case law (all jurisdictions)
  - Regulatory research
  - Legal news and analysis
  - Protégé AI assistant (hallucination-minimized research)
  - Firm-specific knowledge base integration
endpoints:
  - /search/cases
  - /search/statutes
  - /search/regulations
  - /ai-research (AI-assisted research)
cost_model: Tiered subscription ($500-2000/month)
credentials_location: ~/.env.local → LEXISNEXIS_API_KEY
```

### **MCP #3: Gmail Discovery Integration**
```yaml
name: gmail-discovery-mcp
description: Access Gmail for discovery, thread reconstruction, privilege detection
authentication: OAuth (Gmail API)
capabilities:
  - Search emails with legal hold
  - Reconstruct email threads
  - Extract attachments
  - Metadata extraction (dates, parties, subjects)
  - Privilege detection (keywords, CC patterns)
  - Label-based organization
endpoints:
  - /messages/search
  - /messages/{id}/attachments
  - /threads/{id}
cost_model: Free (Google Workspace)
credentials_location: ~/.env.local → GMAIL_SERVICE_ACCOUNT
privilege_keywords:
  - "attorney"
  - "lawyer"
  - "legal counsel"
  - "privileged"
  - "confidential"
  - "work product"
```

### **MCP #4: Slack Communications Discovery**
```yaml
name: slack-discovery-mcp
description: Archive and discover Slack messages for legal cases
authentication: OAuth (Slack workspace)
capabilities:
  - Export legal matter channels
  - Thread reconstruction
  - Privilege channel identification
  - Participant mapping
  - Reaction and emoji context
  - File attachment discovery
endpoints:
  - /conversations/history (channel messages)
  - /threads/{channel}/{ts} (specific threads)
  - /files/list (files in channels)
cost_model: Slack Enterprise features
credentials_location: ~/.env.local → SLACK_BOT_TOKEN
privilege_channels:
  - "#legal-*"
  - "#attorney-*"
  - "#case-*"
  - "#strategy-*"
```

### **MCP #5: Supabase CodeRed Integration**
```yaml
name: supabase-codered-mcp
description: Connect to CodeRed database for cost tracking, logging, RAG
authentication: Supabase service key
capabilities:
  - Log agent runs and decisions
  - Track costs per attorney/task/agent
  - Store case metadata
  - Query RAG database (embeddings)
  - Maintain audit log
  - Update dashboard in real-time
endpoints:
  - /agent_runs (log interactions)
  - /tasks (case-related tasks)
  - /embeddings/search (semantic search over case docs)
  - /decisions (audit trail)
cost_model: Supabase pay-as-you-go ($5-100/month)
credentials_location: ~/.env.local → SUPABASE_URL, SUPABASE_SERVICE_KEY
```

### **MCP #6: GitHub Integration**
```yaml
name: github-mcp
description: Version control for legal tech configs, playbooks, templates
authentication: GitHub PAT (personal access token)
capabilities:
  - Store case templates
  - Version control for playbooks
  - Collaboration on documents
  - CI/CD integration
  - Issue tracking for tasks
endpoints:
  - /repos/{owner}/{repo}/contents
  - /repos/{owner}/{repo}/issues
cost_model: Free (GitHub public repos) or GitHub Pro ($4/month)
credentials_location: ~/.env.local → GITHUB_TOKEN
```

---

## 📁 FOLDER STRUCTURE & FILES

### **claude-code-terminal/** (Direct LLM Interface)
- Six mode-based agent interfaces (@architect, @code, @test, @review, @safety, @cynic)
- Each mode tailored for legal case work
- Direct access to Supabase + MCPs
- Session management and checkpoints

**Key Files**:
- `system-prompt.md` - Master system prompt for legal discovery
- `discovery-mode.prompt` - Discovery bot mode
- `coordinator-mode.prompt` - Attorney coordinator mode
- `strategy-mode.prompt` - Legal strategy bot mode
- `evidence-mode.prompt` - Evidence analysis mode
- `case-analysis-mode.prompt` - Case analysis mode
- `.env.example` - Credentials template
- `codered-sync.py` - Direct database integration

### **antigravity/** (Cloud-Based Orchestration)
- Bidirectional sync with Claude Code Terminal
- Multi-agent orchestration
- Async task queue
- Real-time collaboration features

**Key Files**:
- `antigravity-config.yaml` - Agent definitions
- `crew-sync.py` - Bidirectional sync with Claude
- `codered-connector.py` - CodeRed integration
- `conflict-resolver.py` - Handle sync conflicts
- `health-check.py` - System monitoring

### **cursor/** (Code Editor Integration)
- IDE-native shortcuts for legal workflows
- Rules-based agent triggering
- Real-time RAG context injection
- Cost tracking and approval gates

**Key Files**:
- `cursor-rules.md` - Keyboard shortcuts and rules
- `agents.yaml` - Agent definitions for Cursor
- `cursor-settings.json` - IDE configuration
- `codered-client.py` - Database client
- `rag-context-fetcher.py` - Fetch context from CodeRed

### **github-vercel/** (CI/CD & Deployment)
- GitHub Actions workflows for case pipeline
- Automated legal doc processing
- Vercel deployment for dashboards
- Continuous deployment of configs

**Key Files**:
- `.github/workflows/discovery-pipeline.yml` - Document discovery automation
- `.github/workflows/cost-tracking.yml` - Cost calculation and alerts
- `.github/workflows/config-deploy.yml` - Deploy configs to all systems
- `vercel.json` - Frontend dashboard deployment

### **supabase-integration/** (Database Layer)
- Specialized for legal discovery workflows
- RAG database for case documents
- Cost tracking and audit logs
- Multi-tenant case management

**Key Files**:
- `0001-legal-discovery-schema.sql` - Database schema
- `legal-embeddings.sql` - Vector embedding setup
- `cost-tracking.sql` - Attorney/task cost tracking
- `audit-trail.sql` - Compliance logging
- `dashboard-queries.sql` - Analytics queries

---

## 🗂️ GROUNDING DOCUMENTS (RAG Database)

### **Tier 1: Your Case Files** (Highest Priority)
```
Raw Discovery Documents:
├── Emails (threaded, privilege-marked)
├── Court Filings (organized by case)
├── Depositions (transcribed with timestamps)
├── Financial Records (with metadata)
├── Contracts (with analysis)
└── Evidence (photos, documents, exhibits)

Processing:
→ OCR scanned documents
→ Extract entities (people, dates, amounts)
→ Generate embeddings (1536-dim vectors)
→ Index in Supabase pgvector
→ Link to original documents
```

### **Tier 2: Legal Precedents** (Research Context)
```
From Westlaw/LexisNexis:
├── Custody law precedents (relevant to your cases)
├── Federal criminal law (FEDS cases)
├── Bankruptcy statutes and case law
├── Malpractice standards and precedents
└── Local court rules and practice patterns

Storage:
→ Import via Westlaw/LexisNexis APIs
→ Generate embeddings
→ Tag by legal area
→ Link to winning arguments
```

### **Tier 3: Your Playbooks** (Proprietary Knowledge)
```
Templates & Strategies:
├── Motion templates (custody, discovery, summary judgment)
├── Deposition question frameworks
├── Cross-examination strategies
├── Settlement analysis frameworks
├── Expert witness guidelines
└── Trial preparation checklists

Enhancement:
→ Embed attorney expertise
→ Tag by case type
→ Version control in GitHub
→ Update as you win cases
```

---

## 🔄 DATA FLOW: DISCOVERY TO DECISION

```
PHASE 1: INGESTION
┌─────────────────┐
│ Raw Documents   │
│ (Millions)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Preprocessing   │
│ - OCR           │
│ - Dedup         │
│ - Normalize     │
└────────┬────────┘
         │
         ▼
PHASE 2: DISCOVERY BOT PROCESSES
┌──────────────────────────┐
│ Discovery Bot:           │
│ - Classify documents     │
│ - Extract entities       │
│ - Detect privilege       │
│ - Flag relevance         │
└────────┬─────────────────┘
         │
         ▼
PHASE 3: EMBEDDING & INDEXING
┌──────────────────────────┐
│ Generate Embeddings      │
│ (1536-dimensional)       │
│ Store in pgvector        │
│ Create semantic index    │
└────────┬─────────────────┘
         │
         ▼
PHASE 4: INTELLIGENT SEARCH
┌──────────────────────────────────┐
│ Evidence Analysis Bot queries:    │
│ - "Timeline from March-May"       │
│ - "Contradictions in testimony"   │
│ - "Financial transfers"           │
│ - "Communication patterns"        │
└────────┬───────────────────────────┘
         │
         ▼
PHASE 5: ATTORNEY COORDINATOR BOT
┌──────────────────────────────────┐
│ - Assign analysis to attorneys   │
│ - Track deadlines                │
│ - Consolidate findings           │
│ - Generate reports               │
└────────┬───────────────────────────┘
         │
         ▼
PHASE 6: CASE ANALYSIS BOT
┌──────────────────────────────────┐
│ - Assess case strength           │
│ - Identify weaknesses            │
│ - Recommend strategy             │
│ - Estimate settlement value      │
└────────┬───────────────────────────┘
         │
         ▼
PHASE 7: LEGAL STRATEGY BOT
┌──────────────────────────────────┐
│ - Research precedents (Westlaw)  │
│ - Find winning arguments          │
│ - Counter opposition claims      │
│ - Prepare motion drafts          │
└────────┬───────────────────────────┘
         │
         ▼
DECISION: ATTORNEY REVIEW
┌──────────────────────────────────┐
│ Final human judgment:            │
│ - Review AI recommendations      │
│ - Make case decisions            │
│ - File motions/responses         │
│ - Execute strategy               │
└──────────────────────────────────┘
```

---

## 💰 COST TRACKING MODEL

```
┌─ AGENT COSTS ─┐
│ Discovery     │ $2-3 per 1K documents processed
│ Coordinator   │ $1 per action (check-in, update)
│ Strategy      │ $2-3 per research query
│ Evidence      │ $3-4 per analysis task
│ Case Analysis │ $3-5 per comprehensive assessment
└───────────────┘

┌─ API COSTS ─┐
│ Westlaw      │ $0.10-1.00 per query
│ LexisNexis   │ ~$50-100/month subscription
│ Supabase     │ $5-100/month (usage-based)
│ Gmail        │ Free (Workspace included)
│ Slack        │ Free (channels already subscribed)
└──────────────┘

┌─ TOTAL COST ESTIMATE ─┐
│ Per attorney per day  │ $50-150
│ Per case per week     │ $200-500
│ Per case per month    │ $1000-2000
│ All cases per month   │ $4000-10000
│ (Depends on case complexity & discovery size)
└───────────────────────┘
```

---

## ⚠️ LEGAL COMPLIANCE & ETHICS

### **Attorney-Client Privilege Protection**
- All communications marked confidential
- Privilege detection automated (but attorney reviews)
- Secure channels for privileged comms
- Work product doctrine respected
- Waiver prevention procedures

### **Discovery Compliance**
- Proportionality check (FRE 26(b)(1))
- Timely production
- Proper form (native/PDF per court order)
- Metadata preservation
- Audit trail of processing

### **Professional Responsibility**
- ABA Model Rule 1.1: Technology competence
- ABA Model Rule 1.6: Confidentiality maintained
- ABA Model Rule 3.4: Candor to tribunal
- All AI usage documented
- Human attorney makes final decisions

---

## 🎯 QUICK START

1. **Deploy CodeRed** (Phase 1-3) → 30 minutes
2. **Configure Supabase** with legal schema → 1 hour
3. **Set up MCPs** (Westlaw, LexisNexis, Gmail) → 2-3 hours
4. **Configure Claude Code Terminal** → 1 hour
5. **Configure Cursor IDE** → 1 hour
6. **Configure Antigravity** → 1 hour
7. **Ingest first case documents** → 2-4 hours
8. **Run discovery pipeline** → ongoing

**Total Setup**: 8-12 hours
**Ongoing**: 1-2 hours/day for 6 attorneys

---

## 📊 MONITORING & DASHBOARDS

**Real-Time Dashboard Queries**:
```sql
-- Case status overview
SELECT case_id, status, discovery_count, cost_today
FROM cases
ORDER BY cost_today DESC;

-- Attorney workload
SELECT attorney_name, tasks_assigned, hours_logged, cost_today
FROM attorney_workload
ORDER BY cost_today DESC;

-- Discovery progress
SELECT case_id, total_docs, docs_processed, privilege_flagged, completion_pct
FROM discovery_progress;

-- AI agent performance
SELECT agent_name, tasks_completed, avg_cost, accuracy_score, errors
FROM agent_performance;
```

---

**Next**: Start with `/claude-code-terminal/README.md` to configure your first AI agent mode!

*Last Updated: December 15, 2025*
*System: CodeRed Legal Tech Orchestrator v1.0*
