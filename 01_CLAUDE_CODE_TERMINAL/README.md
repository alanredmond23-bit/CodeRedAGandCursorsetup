# CLAUDE CODE TERMINAL - Legal Discovery System
## Multi-Agent AI Assistant for Legal Practice

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE TERMINAL v2.0                     │
│                    Legal Discovery Multi-Agent System            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  DISCOVERY   │───▶│  COORDINATOR │◀───│   STRATEGY   │     │
│  │     BOT      │    │     BOT      │    │     BOT      │     │
│  └──────────────┘    └──────┬───────┘    └──────────────┘     │
│         │                    │                    │             │
│         │                    ▼                    │             │
│         │            ┌──────────────┐             │             │
│         └───────────▶│   EVIDENCE   │◀────────────┘             │
│                      │  ANALYSIS    │                           │
│                      └──────┬───────┘                           │
│                             │                                   │
│                             ▼                                   │
│                      ┌──────────────┐                           │
│                      │     CASE     │                           │
│                      │   ANALYSIS   │                           │
│                      └──────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [Mode Reference](#mode-reference)
8. [MCP Integration](#mcp-integration)
9. [Security & Compliance](#security--compliance)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)
12. [Support](#support)

---

## OVERVIEW

Claude Code Terminal is a specialized AI-powered legal discovery and research system designed for Attorney Alan Redmond's practice. It operates as a multi-agent system with five distinct modes, each optimized for specific legal tasks:

- **@discovery** - Legal research and evidence discovery
- **@coordinator** - Attorney interface and task orchestration
- **@strategy** - Legal strategy and motion development
- **@evidence** - Fact extraction and evidence organization
- **@analysis** - Deep analytical reasoning and outcome prediction

### Key Capabilities

- **Legal Research**: Automated Westlaw and LexisNexis searches
- **Email Discovery**: Gmail integration with privilege detection
- **Communication Discovery**: Slack message retrieval
- **Case Management**: Supabase database for case tracking
- **Evidence Organization**: Automated fact extraction and timeline generation
- **Strategic Analysis**: Motion development and case outcome prediction
- **Privilege Protection**: Automatic privilege detection and flagging
- **Audit Trail**: Comprehensive logging for legal compliance

---

## FEATURES

### 🔍 Discovery Bot
- Search Westlaw case law database
- Search LexisNexis statutes and regulations
- Gmail email discovery with Boolean operators
- Slack message retrieval
- Automatic privilege detection
- Citation verification (KeyCite/Shepardize)

### 🎯 Coordinator Bot
- Attorney-facing conversational interface
- Multi-agent orchestration
- Executive summaries
- Case status tracking
- Deadline management
- Session state management

### ⚖️ Strategy Bot
- Legal motion development
- Argument structure (IRAC)
- Counter-argument anticipation
- Risk assessment
- Settlement strategy
- Appellate preservation

### 📋 Evidence Bot
- Fact extraction from documents
- Timeline construction
- Evidence categorization
- Authentication checklists
- Hearsay analysis
- Chain of custody tracking

### 📊 Analysis Bot
- Causal chain analysis
- Legal theory development
- Outcome prediction (Bayesian)
- Element-by-element breakdown
- Comparative case analysis
- Risk assessment matrices

---

## ARCHITECTURE

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE TERMINAL                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  PROMPT LAYER (Mode-Specific Prompts)             │    │
│  │  - system-prompt-master.md                         │    │
│  │  - discovery-mode.prompt                           │    │
│  │  - coordinator-mode.prompt                         │    │
│  │  - strategy-mode.prompt                            │    │
│  │  - evidence-mode.prompt                            │    │
│  │  - case-analysis-mode.prompt                       │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  INTEGRATION LAYER (Python Scripts)                │    │
│  │  - codered-sync.py (Supabase integration)          │    │
│  │  - context-injector.py (RAG context loading)       │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MCP LAYER (External Service Connections)          │    │
│  │  - Westlaw MCP                                      │    │
│  │  - LexisNexis MCP                                   │    │
│  │  - Gmail MCP                                        │    │
│  │  - Slack MCP                                        │    │
│  │  - Supabase MCP                                     │    │
│  │  - OpenAI MCP (embeddings)                          │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  DATA LAYER (Supabase PostgreSQL)                  │    │
│  │  - Cases table                                      │    │
│  │  - Discovery results table                          │    │
│  │  - Evidence table                                   │    │
│  │  - Session checkpoints table                        │    │
│  │  - Privilege log table                              │    │
│  │  - Audit trail table                                │    │
│  │  - Case documents table (RAG)                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Coordinator Bot receives request
2. **Context Loading** → `context-injector.py` loads relevant case data from Supabase
3. **Mode Routing** → Coordinator delegates to specialist mode
4. **MCP Execution** → Specialist mode calls external services (Westlaw, Gmail, etc.)
5. **Privilege Detection** → All outputs scanned for privilege markers
6. **Result Storage** → `codered-sync.py` persists results to Supabase
7. **Synthesis** → Coordinator synthesizes multi-mode outputs
8. **Attorney Output** → Formatted response with citations and next steps

---

## INSTALLATION

### Prerequisites

- Python 3.9 or higher
- Claude Code Terminal (with Claude Sonnet 4.5 or higher)
- Supabase account (free tier sufficient for testing)
- API credentials for required services (see Configuration)

### Step 1: Clone Repository

```bash
cd /path/to/your/projects
git clone <your-repo-url>
cd claude-code-terminal
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
```txt
supabase-py>=2.0.0
python-dotenv>=1.0.0
openai>=1.0.0
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.0.0
slack-sdk>=3.0.0
requests>=2.31.0
```

### Step 3: Configure Environment Variables

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

See [Configuration](#configuration) section for detailed credential setup.

### Step 4: Initialize Supabase Database

```bash
# Connect to your Supabase project
psql postgresql://user:password@db.xxx.supabase.co:5432/postgres

# Run database schema creation
\i supabase_schema.sql
```

Alternatively, use Supabase dashboard to create tables:

1. Go to https://app.supabase.com/project/_/editor
2. Run the schema SQL from `codered-sync.py` (see `initialize_database_schema()`)
3. Enable pgvector extension for vector search:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### Step 5: Authenticate Google Services (Gmail)

```bash
# Run authentication script
python authenticate_gmail.py

# Follow OAuth flow in browser
# Credentials will be saved to gmail_token.json
```

### Step 6: Test Installation

```bash
# Test Supabase connection
python codered-sync.py

# Test context injection
python context-injector.py

# Verify MCP connections
python test_mcps.py
```

---

## CONFIGURATION

### 1. Westlaw API Setup

1. Sign up for Westlaw API access at https://developer.westlaw.com/
2. Create API application
3. Copy API Key and Secret to `.env`:
   ```
   WESTLAW_API_KEY=your_key_here
   WESTLAW_API_SECRET=your_secret_here
   ```

### 2. LexisNexis API Setup

1. Register at https://developer.lexisnexis.com/
2. Create OAuth 2.0 application
3. Copy Client ID and Secret to `.env`:
   ```
   LEXIS_CLIENT_ID=your_client_id
   LEXIS_CLIENT_SECRET=your_client_secret
   ```

### 3. Gmail API Setup

**Detailed Instructions:**

1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Download credentials JSON
5. Save credentials:
   ```bash
   mv ~/Downloads/client_secret_xxx.json ./gmail_credentials.json
   ```
6. Update `.env`:
   ```
   GMAIL_CREDENTIALS_JSON=./gmail_credentials.json
   GMAIL_TOKEN_JSON=./gmail_token.json
   ```
7. Run authentication:
   ```bash
   python authenticate_gmail.py
   ```

### 4. Slack API Setup

1. Go to https://api.slack.com/apps
2. Click "Create New App" > "From scratch"
3. Add Bot Token Scopes:
   - `channels:history`
   - `search:read`
   - `files:read`
   - `users:read`
4. Install to workspace
5. Copy tokens to `.env`:
   ```
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_APP_TOKEN=xapp-your-token
   ```

### 5. Supabase Setup

**Detailed Instructions:**

1. Create account at https://supabase.com/
2. Create new project
3. Go to Settings > API
4. Copy values to `.env`:
   ```
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   ```
5. Initialize database schema (see Installation Step 4)

### 6. OpenAI API Setup (for embeddings)

1. Create account at https://platform.openai.com/
2. Generate API key
3. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

---

## USAGE GUIDE

### Starting a Session

```bash
# Open Claude Code Terminal
claude-code

# System will automatically load configuration
# Coordinator mode is default
```

### Basic Commands

**Invoke a mode:**
```
@discovery "Find California cases on trade secret misappropriation"
@strategy "Draft motion to dismiss arguments"
@evidence "Extract facts from Smith deposition transcript"
@analysis "Predict outcome for breach of contract claim"
```

**Administrative commands:**
```
/status                 # Show all active tasks
/cases                  # List all open cases
/checkpoint save        # Save current session
/checkpoint load <id>   # Restore previous session
/audit last_30_days     # Generate audit report
/privilege scan         # Check all docs for privilege
/mcp status             # Verify MCP connections
/help discovery         # Get mode-specific help
```

### Example Workflows

#### Workflow 1: Simple Case Law Research

```
User: @discovery "Find recent California employment discrimination cases"

Discovery Bot:
✓ Searching Westlaw...
✓ Found 47 cases (2020-2025)
✓ KeyCite verification complete
✓ 0 privilege issues

Top 3 Cases:
1. Harris v. City of Santa Monica, 56 Cal. App. 5th 123 (2023)
   - Age discrimination, summary judgment reversed

2. Chen v. Tech Startup Inc., 54 Cal. App. 5th 789 (2022)
   - Disability accommodation failure

3. Martinez v. County of Los Angeles, 52 Cal. App. 5th 456 (2021)
   - FEHA retaliation claim

Next steps: Review cases, or pass to @strategy for argument development?
```

#### Workflow 2: Complex Multi-Mode Motion Preparation

```
User: Prepare motion to suppress evidence in Smith case - Fourth Amendment issue

Coordinator:
Multi-mode workflow initiated...

Step 1/4: @discovery searching Fourth Amendment cases... ✓
  - Found 23 relevant cases

Step 2/4: @evidence extracting facts from arrest report... ✓
  - 12 key facts identified
  - Timeline constructed

Step 3/4: @strategy drafting motion arguments... ✓
  - 3 arguments developed
  - Counter-arguments prepared

Step 4/4: @analysis predicting success probability... ✓
  - 65% success probability

EXECUTIVE SUMMARY:
Strong motion based on lack of reasonable suspicion. Primary argument:
Officer lacked specific articulable facts (People v. Wells). Success
probability 65%. Recommend filing with expert witness support.

Deliverables ready:
- Motion outline
- Supporting case citations
- Fact-to-element mapping
- Risk assessment

Proceed with motion drafting?
```

#### Workflow 3: Email Discovery with Privilege Issues

```
User: @discovery "Find all emails between Smith and Jones about merger negotiations"

Discovery Bot:
⚠️ PRIVILEGE WARNING ⚠️

Search complete:
- 15 emails found
- 3 emails flagged as PRIVILEGED

Privilege breakdown:
🔒 Email 1: Attorney-client (Smith → Attorney Redmond re: legal advice)
🔒 Email 2: Attorney-client (Attorney Redmond → Smith re: legal strategy)
🔒 Email 3: Work product (Internal strategy discussion)

REQUIRED ACTIONS:
1. Manual review of 3 privileged emails
2. Prepare privilege log if withholding from production
3. Redact if partial privilege

Remaining 12 emails cleared for use.

Pass to @evidence for fact extraction from non-privileged emails?
```

---

## MODE REFERENCE

### Discovery Mode (@discovery)

**Purpose:** Execute searches across legal databases and communication platforms

**Invocation:**
```
@discovery "search query here"
```

**Example Queries:**
```
@discovery "Fourth Amendment reasonable suspicion cases California"
@discovery "Find emails from:smith@company.com subject:contract"
@discovery "Search Slack for 'discovery deadline extension'"
@discovery "Find all depositions in Smith v. TechCorp case"
```

**Output:** Structured JSON with citations, privilege flags, relevance scores

**See:** `discovery-mode.prompt` for full documentation

---

### Coordinator Mode (@coordinator)

**Purpose:** Attorney interface, task delegation, status reporting

**Invocation:** Default mode, or explicitly:
```
@coordinator "task description"
```

**Example Commands:**
```
@coordinator "What's the status of Smith v. TechCorp?"
@coordinator "Prepare motion to compel for Jones case"
@coordinator "Show upcoming deadlines"
@coordinator "Summarize discovery results from last week"
```

**Output:** Executive summaries, task delegation, conversational responses

**See:** `coordinator-mode.prompt` for full documentation

---

### Strategy Mode (@strategy)

**Purpose:** Legal strategy formulation and motion development

**Invocation:**
```
@strategy "strategic task"
```

**Example Queries:**
```
@strategy "Draft motion to dismiss arguments for Smith case"
@strategy "Analyze opposing counsel's summary judgment motion"
@strategy "Develop settlement strategy with 70% success probability"
@strategy "Prepare counter-arguments for privilege objections"
```

**Output:** Legal arguments (IRAC), motion outlines, strategic memos

**Classification:** ATTORNEY WORK PRODUCT - All outputs privileged

**See:** `strategy-mode.prompt` for full documentation

---

### Evidence Mode (@evidence)

**Purpose:** Fact extraction, evidence organization, timeline construction

**Invocation:**
```
@evidence "evidence task"
```

**Example Queries:**
```
@evidence "Extract facts from Smith deposition transcript"
@evidence "Build timeline for contract negotiation (Aug-Nov 2023)"
@evidence "Generate authentication checklist for email exhibits"
@evidence "Map evidence to breach of contract elements"
```

**Output:** Fact databases, timelines, authentication checklists

**See:** `evidence-mode.prompt` for full documentation

---

### Analysis Mode (@analysis)

**Purpose:** Deep analytical reasoning and outcome prediction

**Invocation:**
```
@analysis "analytical task"
```

**Example Queries:**
```
@analysis "Predict outcome for negligence claim"
@analysis "Analyze causation chain for product liability"
@analysis "Compare our case to precedent"
@analysis "Generate risk assessment matrix"
```

**Output:** Probability assessments, causal analysis, theory matrices

**See:** `case-analysis-mode.prompt` for full documentation

---

## MCP INTEGRATION

### MCP Architecture

Model Context Protocol (MCP) enables Claude to connect to external services:

```
Claude Code Terminal
    │
    ├── Westlaw MCP ────────▶ Westlaw API
    ├── LexisNexis MCP ─────▶ LexisNexis API
    ├── Gmail MCP ──────────▶ Gmail API
    ├── Slack MCP ──────────▶ Slack API
    ├── Supabase MCP ───────▶ Supabase PostgreSQL
    └── OpenAI MCP ─────────▶ OpenAI Embeddings API
```

### MCP Configuration

All MCP settings in `mcp-config.json`:

```json
{
  "mcpServers": {
    "westlaw": { /* Westlaw config */ },
    "lexisnexis": { /* LexisNexis config */ },
    "gmail": { /* Gmail config */ },
    "slack": { /* Slack config */ },
    "supabase": { /* Supabase config */ }
  }
}
```

### Testing MCP Connections

```bash
# Test all MCPs
python test_mcps.py

# Test specific MCP
python test_mcps.py westlaw
```

### MCP Troubleshooting

**Issue: MCP connection failed**

```bash
# Check credentials
cat .env | grep WESTLAW

# Verify network connectivity
curl https://api.westlaw.com/v1/health

# Check MCP logs
tail -f mcp-connections.log
```

**Issue: Rate limit exceeded**

```bash
# Check quota usage
python check_quotas.py

# Wait for quota reset, or:
# Adjust rate limits in mcp-config.json
```

---

## SECURITY & COMPLIANCE

### Privilege Protection

**Automatic Detection:**
- All emails scanned for attorney-client markers
- Slack channels flagged as work product
- Document content analyzed for privilege terms

**Privilege Patterns:**
```python
PRIVILEGE_PATTERNS = {
    "attorney_client": [
        "attorney-client",
        "legal advice",
        "privileged communication"
    ],
    "work_product": [
        "work product",
        "legal strategy",
        "prepared in anticipation of litigation"
    ]
}
```

**Manual Review Required:**
- All flagged documents quarantined
- Attorney must approve before disclosure
- Privilege log generated automatically

### Audit Trail

**Logged Events:**
- All MCP queries
- Document access
- Privilege flags
- Mode invocations
- Session checkpoints

**Audit Report:**
```bash
# Generate audit report
python generate_audit_report.py --start 2024-01-01 --end 2024-12-31

# Export to PDF
python generate_audit_report.py --format pdf --output audit_2024.pdf
```

**Retention:** 7 years (configurable in `.env`)

### Data Security

**Encryption:**
- At rest: Supabase encryption enabled
- In transit: TLS 1.3 for all API calls
- Credentials: Stored in environment variables (not in code)

**Access Control:**
- Single-user system (attorney only)
- MCP service accounts with minimal permissions
- API keys rotated every 90 days

**Compliance:**
- California Rules of Professional Conduct
- ABA Model Rules of Professional Conduct
- Attorney-client privilege protection
- Work product doctrine protection

---

## TROUBLESHOOTING

### Common Issues

#### Issue: "Supabase connection failed"

**Cause:** Invalid credentials or network issue

**Solution:**
```bash
# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
curl $SUPABASE_URL/rest/v1/ -H "apikey: $SUPABASE_KEY"

# Check firewall/VPN
ping xxx.supabase.co
```

#### Issue: "Gmail authentication expired"

**Cause:** OAuth token expired (happens after 7 days)

**Solution:**
```bash
# Re-authenticate
python authenticate_gmail.py

# Token will be refreshed automatically
```

#### Issue: "Privilege detection not working"

**Cause:** Patterns not configured correctly

**Solution:**
```bash
# Check privilege patterns in mcp-config.json
cat mcp-config.json | grep -A 10 "privilege_detection"

# Add custom patterns
nano mcp-config.json
# Edit "patterns" section

# Test privilege detection
python test_privilege_detection.py
```

#### Issue: "Context injection slow"

**Cause:** Large case database, embeddings taking time

**Solution:**
```bash
# Reduce context limit
nano context-injector.py
# Change limit parameter in semantic_search()

# Enable caching
export CACHE_ENABLED=true

# Pre-generate embeddings
python pregenerate_embeddings.py
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
export DEBUG_MCP_CONNECTIONS=true
export DEBUG_PRIVILEGE_DETECTION=true
export DEBUG_CONTEXT_INJECTION=true

# Run with debug output
python codered-sync.py 2>&1 | tee debug.log
```

### Support Logs

Generate support bundle:

```bash
python generate_support_bundle.py

# Creates support_bundle_YYYYMMDD.zip containing:
# - All logs
# - Configuration (credentials redacted)
# - MCP status
# - System info
```

---

## FAQ

**Q: Can I use this for multiple cases simultaneously?**

A: Yes. The coordinator tracks all active cases. Use case_number parameter to switch context:
```
@discovery "search query" --case CV-2024-12345
```

**Q: How do I add new privilege patterns?**

A: Edit `mcp-config.json` under `privilege_detection.patterns`:
```json
"custom_patterns": [
  "my custom privilege marker",
  "confidential.*legal"
]
```

**Q: Can I export discovery results to PDF?**

A: Yes:
```bash
python export_discovery.py --discovery-id disc_xxx --format pdf
```

**Q: How much does this cost to run?**

A:
- Supabase: Free tier supports ~500MB database (sufficient for testing)
- Westlaw/Lexis: Varies by subscription ($100-500/month typical)
- Gmail/Slack: Free (within quotas)
- OpenAI embeddings: ~$0.10 per 1000 documents
- Claude Code Terminal: Included with Claude Pro subscription

**Q: Is this compliant with California legal ethics rules?**

A: Yes, designed with compliance in mind:
- Preserves attorney-client privilege
- Maintains audit trail
- Requires attorney supervision
- Discloses AI assistance
- But: Attorney has ultimate responsibility for all legal work

**Q: Can I customize the mode prompts?**

A: Yes, all prompts are editable:
```bash
nano discovery-mode.prompt
# Make changes
# Restart Claude Code Terminal to load new prompt
```

**Q: How do I backup my data?**

A:
```bash
# Backup Supabase database
python backup_supabase.py --output backup_$(date +%Y%m%d).sql

# Backup local files
tar -czf backup_$(date +%Y%m%d).tar.gz *.json *.py *.prompt .env
```

---

## SUPPORT

### Contact

- **Attorney:** Alan Redmond (alan.redmond@law.com)
- **System Issues:** See Troubleshooting section above
- **Feature Requests:** Document in GitHub Issues (if using version control)

### Documentation

- **Master System Prompt:** `system-prompt-master.md`
- **Mode Prompts:** `{mode}-mode.prompt` files
- **API Documentation:** See individual MCP provider docs

### Updates

Check for system updates:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Contributing

To improve the system:

1. Document the issue or enhancement
2. Test thoroughly in isolated environment
3. Update relevant prompt files
4. Update this README if adding features
5. Commit with descriptive message

---

## LICENSE

Proprietary - For use by Alan Redmond Law Firm only.

Unauthorized copying, distribution, or modification is prohibited.

---

## VERSION HISTORY

**v2.0** (2025-12-16)
- Multi-agent architecture with 5 specialized modes
- Full MCP integration (Westlaw, Lexis, Gmail, Slack, Supabase)
- RAG context injection system
- Comprehensive privilege detection
- Audit trail and session management

**v1.5** (2024-10-15)
- Enhanced privilege detection
- Added session checkpoints
- Improved error handling

**v1.0** (2024-06-01)
- Initial single-mode implementation
- Basic Westlaw integration
- Manual privilege review

---

## QUICK START CHECKLIST

- [ ] Python 3.9+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] Supabase database initialized
- [ ] Gmail OAuth completed
- [ ] All MCP connections tested
- [ ] Test case created in database
- [ ] First discovery search successful
- [ ] Privilege detection working
- [ ] Session checkpoint saved

**Once checklist complete, system is ready for production use.**

---

**END OF README**

For additional help, consult `system-prompt-master.md` or contact support.
