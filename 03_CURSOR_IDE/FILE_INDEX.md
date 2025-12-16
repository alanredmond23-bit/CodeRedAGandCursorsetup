# Cursor IDE Integration - Complete File Index

**Version**: 1.0
**Last Updated**: December 16, 2025
**Total Files**: 13 core files + documentation

---

## Quick Reference

| File | Type | Purpose | Size |
|------|------|---------|------|
| **cursor-rules.md** | Documentation | Complete usage guide with keyboard shortcuts | 19 KB |
| **cursor-settings.json** | Configuration | IDE settings, keybindings, agent configs | 13 KB |
| **agents.yaml** | Configuration | 6 agent definitions with prompts | 16 KB |
| **tools.yaml** | Configuration | Tool permissions and capabilities | 10 KB |
| **codered-client.py** | Python Script | Supabase database client | 11 KB |
| **rag-context-fetcher.py** | Python Script | RAG context fetching | 7.8 KB |
| **cost-tracker.py** | Python Script | Cost tracking and reporting | 9.7 KB |
| **privilege-detector.py** | Python Script | Privilege detection | 9.7 KB |
| **extensions.json** | Configuration | Recommended VS Code extensions | 2.5 KB |
| **launch.json** | Configuration | Debug configurations | 3.4 KB |
| **.env.example** | Template | Environment variables template | 1.7 KB |
| **requirements.txt** | Dependencies | Python package requirements | 636 B |
| **README.md** | Documentation | Main setup and usage guide | 13 KB |
| **example-workflow.md** | Documentation | Complete 30-min workflow example | 24 KB |
| **INSTALLATION_GUIDE.md** | Documentation | Step-by-step installation | 12 KB |

**Total Package Size**: ~155 KB

---

## File Descriptions

### Core Configuration Files

#### 1. cursor-rules.md
**Purpose**: Master reference guide for Cursor IDE integration

**Contents**:
- Keyboard shortcuts for 6 agents (Cmd+Shift+A/C/T/R/E/S)
- Zone-based permission rules (RED/YELLOW/GREEN)
- Automatic RAG context injection explanation
- Cost tracking model
- Privilege detection workflow
- Agent-specific usage guidelines
- Troubleshooting guide
- Keyboard shortcut reference card

**When to use**: First document to read after installation. Keep open for reference.

**Key sections**:
- Line 1-50: Keyboard shortcuts overview
- Line 51-150: Zone-based permissions
- Line 151-250: RAG context injection
- Line 251-350: Cost tracking
- Line 351-450: Privilege detection
- Line 451-650: Agent-specific rules
- Line 651-750: Example workflow
- Line 751-800: Troubleshooting

---

#### 2. cursor-settings.json
**Purpose**: Complete Cursor IDE configuration (settings, keybindings, tasks)

**Contents**:
- 6 keybindings (Cmd+Shift+A/C/T/R/E/S)
- Editor settings (format on save, rulers, word wrap)
- RAG configuration (enabled, database, top_k)
- Cost tracking settings (budgets, alerts)
- Privilege detection settings (keywords, thresholds)
- Agent model configurations (gpt-4o, gpt-4o-mini)
- Task definitions (test connection, fetch context, etc.)
- Launch configurations (debugging)
- Code snippets (case notes, evidence markers)
- Status bar customization
- Custom commands

**How to install**:
```bash
# Copy to workspace
cp cursor-settings.json .vscode/settings.json

# OR load via Cursor UI
# Cmd+, → Workspace → Open Settings (JSON) → Paste contents
```

**Key sections**:
- `keybindings`: Keyboard shortcut definitions
- `settings.codered.*`: CodeRed-specific settings
- `tasks`: Runnable tasks (test, ingest, costs)
- `snippets`: Code/markdown snippets
- `statusBar`: Status bar customization

---

#### 3. agents.yaml
**Purpose**: Define 6 AI agents with prompts, capabilities, and permissions

**Contents**:
- **Architect Agent**: Strategy, settlement analysis (gpt-4o, RED/YELLOW/GREEN)
- **Code Agent**: Implementation, automation (gpt-4o, YELLOW/GREEN)
- **Test Agent**: QA, validation (gpt-4o-mini, GREEN only)
- **Review Agent**: Document/code review (gpt-4o, YELLOW/GREEN)
- **Evidence Agent**: Timeline analysis, contradictions (gpt-4o, RED/YELLOW)
- **Cynic Agent**: Risk assessment, privilege check (gpt-4o, RED only)

**For each agent**:
- Model configuration (provider, name, temperature, max_tokens)
- Cost settings (per_query_usd, ceiling_usd, budgets)
- Capabilities list
- Zone access permissions
- Restrictions
- System prompts
- User prompt templates
- Keyboard shortcut
- Integration settings (Supabase, Westlaw, etc.)

**How to customize**:
```yaml
# Edit agent model
architect:
  model:
    name: "gpt-4o"  # Change to "claude-3-opus-20240229" for Claude
    temperature: 0.3  # Lower = more deterministic

# Edit cost ceiling
  cost:
    ceiling_usd: 10.0  # Increase limit
```

**Key agents**:
- `architect`: Strategic analysis (most expensive, most valuable)
- `evidence`: Pattern detection (critical for discovery)
- `test`: Cheap validation (use liberally)
- `cynic`: Risk assessment (use for high-stakes decisions)

---

#### 4. tools.yaml
**Purpose**: Define tools available to agents with permissions

**Contents**:
- **Supabase Client**: Database operations (all agents)
- **RAG Context Fetcher**: Automatic context retrieval (most agents)
- **Cost Tracker**: Cost logging and reporting (all agents)
- **Privilege Detector**: Privilege flagging (Architect, Review, Evidence, Cynic)
- **Westlaw API**: Legal research (Architect, Review, Evidence)
- **LexisNexis API**: Legal research (Architect, Review, Evidence)
- **Gmail Discovery**: Email processing (Evidence only)
- **GitHub Integration**: Version control (Code agent)

**For each tool**:
- Name and description
- Type (database, rag, monitoring, security, external_api)
- Enabled status
- Capabilities list
- Configuration (connection, endpoints, costs)
- Zone permissions
- Agent-specific restrictions

**MCP Server Configuration**:
```yaml
mcp_servers:
  supabase:
    command: "python"
    args: ["cursor/codered-client.py", "mcp"]
```

**Agent-Tool Permissions Matrix**:
| Agent | Supabase | RAG | Cost | Privilege | Westlaw | GitHub |
|-------|----------|-----|------|-----------|---------|--------|
| Architect | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Code | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Test | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Review | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Evidence | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Cynic | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

---

### Python Helper Scripts

#### 5. codered-client.py
**Purpose**: Supabase database client for all database operations

**Functions**:
- `test_connection()`: Test Supabase connectivity
- `log_agent_run()`: Log agent query to database
- `query_embeddings()`: Semantic search over case documents
- `ingest_document()`: Add document to RAG database
- `get_case_metadata()`: Retrieve case information
- `track_cost()`: Log cost entry
- `get_costs_today()`: Retrieve today's costs
- `flag_privilege()`: Flag privileged document

**Usage**:
```bash
# Test connection
python codered-client.py test

# Log agent run
python codered-client.py log

# Query embeddings
python codered-client.py query

# Ingest document
python codered-client.py ingest

# View costs
python codered-client.py costs
```

**Dependencies**: `supabase`, `python-dotenv`

**Environment variables required**:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

---

#### 6. rag-context-fetcher.py
**Purpose**: Automatically fetch relevant case context for agent queries

**Functions**:
- `detect_case_id()`: Extract case ID from file path
- `extract_query()`: Extract query from file/selection
- `fetch_context()`: Fetch RAG context (top-k documents)
- `format_for_agent()`: Format context as markdown
- `ingest_file()`: Ingest file to RAG database

**Usage**:
```bash
# Fetch context for file
python rag-context-fetcher.py \
  --file /path/to/document.txt \
  --top-k 5

# Ingest file
python rag-context-fetcher.py \
  --ingest \
  --file /path/to/document.txt \
  --case-id CASE-2024-001 \
  --zone YELLOW
```

**Dependencies**: `supabase`, `openai`, `python-dotenv`

**Environment variables required**:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `OPENAI_API_KEY` (optional, for embeddings)

**Output format**:
```markdown
# CASE CONTEXT (Auto-Fetched)

Case ID: CASE-2024-001
Relevant Documents (5 found):
1. Email: Smith to Jones - 87% similarity
2. Deposition: Smith testimony - 82% similarity
...
```

---

#### 7. cost-tracker.py
**Purpose**: Track and report AI usage costs

**Functions**:
- `estimate_cost()`: Estimate cost for query (model, tokens)
- `estimate_agent_cost()`: Estimate cost for agent query
- `log_cost()`: Log cost to database
- `get_costs()`: Retrieve costs (today, week, month)
- `generate_report()`: Generate cost breakdown
- `format_report()`: Format report as markdown
- `check_budget()`: Check budget threshold
- `alert_if_threshold_exceeded()`: Generate alert message

**Usage**:
```bash
# View today's costs
python cost-tracker.py --report today

# Check budget
python cost-tracker.py --check-budget --budget 200.0

# Filter by attorney
python cost-tracker.py --report today --attorney john_doe

# Filter by case
python cost-tracker.py --report today --case CUSTODY-2024-001
```

**Pricing** (per 1K tokens):
- gpt-4o: $0.0025 input, $0.010 output
- gpt-4o-mini: $0.000150 input, $0.000600 output
- text-embedding-3-small: $0.00002 input

**Output format**:
```
# COST REPORT - TODAY

Total Cost: $42.75
Query Count: 15
Average Cost: $2.85/query

By Agent:
- architect: $15.50 (36.3%)
- evidence: $12.25 (28.7%)
...
```

---

#### 8. privilege-detector.py
**Purpose**: Automatically detect attorney-client privilege in documents

**Functions**:
- `detect()`: Detect privilege in text (confidence scoring)
- `detect_file()`: Detect privilege in file
- `flag_document()`: Flag in database if privileged
- `format_report()`: Format detection report

**Keywords** (with weights):
- High confidence: "attorney-client privilege" (0.9), "work product" (0.8)
- Medium confidence: "attorney" (0.3), "confidential" (0.2)
- Low confidence: "legal" (0.1)

**Patterns**:
- Attorney email: `\w+@\w+law\.\w+` (weight: 0.3)
- Attorney header: `(from|to):.*attorney` (weight: 0.4)
- Privilege notice: `this (email|communication) is privileged` (weight: 0.5)

**Usage**:
```bash
# Detect privilege
python privilege-detector.py --file /path/to/email.txt

# Flag in database
python privilege-detector.py \
  --file /path/to/email.txt \
  --flag document_id_123
```

**Confidence scoring**:
- >= 0.7: RED zone recommendation
- >= 0.4: YELLOW zone recommendation
- < 0.4: GREEN zone recommendation

**Output format**:
```markdown
# PRIVILEGE DETECTION REPORT

Is Privileged: YES
Confidence: 85%
Recommendation: 🔴 RED ZONE

Keywords Found:
- attorney-client privilege (high confidence)
- confidential (medium confidence)

Patterns Detected:
- Attorney email: attorney@lawfirm.com
```

---

### Configuration & Debug Files

#### 9. extensions.json
**Purpose**: List of recommended VS Code/Cursor extensions

**Required extensions**:
- **Cursor IDE** (cursor.cursor-vscode)
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Supabase** (supabase.supabase-vscode)

**Recommended extensions**:
- GitLens, Markdown All in One, Code Spell Checker, etc.

**How to install**:
```bash
# Open Cursor
# Press Cmd+Shift+X (Extensions)
# Search for each extension and click Install
```

---

#### 10. launch.json
**Purpose**: Debug configurations for Python scripts

**Configurations**:
1. **Python: Current File** - Debug any Python file
2. **Debug: CodeRed Client** - Test Supabase connection
3. **Debug: RAG Context Fetcher** - Test RAG retrieval
4. **Debug: Cost Tracker** - Test cost reports
5. **Debug: Privilege Detector** - Test privilege detection
6. **Test: Ingest Document** - Test document ingestion
7. **Test: Check Budget** - Test budget alerts

**How to use**:
```bash
# In Cursor:
# 1. Open Python file
# 2. Press F5 (Start Debugging)
# 3. Select configuration
# 4. Breakpoints work as expected
```

---

#### 11. .env.example
**Purpose**: Template for environment variables

**Required variables**:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `OPENAI_API_KEY`: OpenAI API key

**Optional variables**:
- `ANTHROPIC_API_KEY`: For Claude models
- `WESTLAW_API_KEY`: For legal research
- `LEXISNEXIS_API_KEY`: For legal research
- `GMAIL_SERVICE_ACCOUNT`: For email discovery
- `GITHUB_TOKEN`: For version control

**Configuration variables**:
- Budget thresholds (daily, weekly, monthly)
- Zone defaults
- Privilege detection settings
- RAG configuration
- Agent model selections

**How to use**:
```bash
# Copy template
cp .env.example .env.local

# Edit with your credentials
nano .env.local

# Never commit .env.local!
echo ".env.local" >> .gitignore
```

---

#### 12. requirements.txt
**Purpose**: Python package dependencies

**Required packages**:
- `supabase==2.3.0`: Supabase Python client
- `openai>=1.6.0`: OpenAI API client
- `python-dotenv==1.0.0`: Environment variable loading

**Optional packages**:
- `pypdf2`: PDF parsing
- `python-docx`: DOCX parsing
- `beautifulsoup4`: HTML parsing
- `pytest`: Testing framework

**How to install**:
```bash
# Install all dependencies
pip install -r requirements.txt

# OR with conda
conda install --file requirements.txt

# OR in virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Documentation Files

#### 13. README.md
**Purpose**: Main setup and usage guide

**Sections**:
1. **Overview**: What this package provides
2. **Quick Start**: 5-minute setup
3. **Keyboard Shortcuts**: Reference table
4. **Files Included**: Complete file list
5. **Setup Guide**: Detailed installation steps
6. **Usage Examples**: Real-world examples
7. **Zone-Based Permissions**: RED/YELLOW/GREEN explanation
8. **Cost Tracking**: How to monitor costs
9. **Troubleshooting**: Common issues and fixes
10. **Advanced Configuration**: Customization options
11. **Integration**: With other systems
12. **Security**: Best practices
13. **FAQ**: Common questions

**When to read**: After installation, before first use

**Key examples**:
- Case strength analysis workflow
- Document parsing automation
- Privilege detection example

---

#### 14. example-workflow.md
**Purpose**: Complete 30-minute workflow demonstration

**Scenario**: Analyzing timeline inconsistencies in custody case

**Phases**:
1. **Setup** (5 min): Open project, verify config
2. **Initial Assessment** (8 min): Architect agent case analysis
3. **Evidence Analysis** (10 min): Evidence agent contradiction detection
4. **Risk Assessment** (5 min): Cynic agent risk analysis
5. **Action Items** (2 min): Code agent task generation

**Agents used**:
- Architect ($3.85)
- Evidence ($3.65)
- Cynic ($4.25)
- Code ($2.50)

**Total cost**: $15.50
**Total time**: 30 minutes
**Documents analyzed**: 5
**Key finding**: Critical timeline contradiction (confidence: 0.95)

**When to read**: Before using system for first time, to understand workflow

**Key takeaways**:
- RAG context automatically fetched
- Multi-agent collaboration
- Cost tracking in real-time
- Never left IDE

---

#### 15. INSTALLATION_GUIDE.md
**Purpose**: Step-by-step installation instructions

**Steps**:
1. **Install Python Dependencies** (5 min)
2. **Configure Environment Variables** (10 min)
3. **Test Supabase Connection** (5 min)
4. **Configure Cursor IDE** (10 min)
5. **Test Agent Integration** (5 min)
6. **Ingest First Document** (5 min)
7. **Configure Budget Alerts** (optional)
8. **Verify Privilege Detection** (optional)
9. **Final Verification** (checklist)

**Total time**: 30-45 minutes

**Prerequisites**:
- Cursor IDE installed
- Python 3.9+ installed
- Supabase account
- OpenAI API key

**When to use**: During initial installation

**Troubleshooting section**:
- Connection errors
- Missing dependencies
- Keyboard shortcuts not working
- RAG context not appearing
- Cost logging issues

---

## Quick Start Workflow

### For First-Time Users:

1. **Read** → `INSTALLATION_GUIDE.md` (30-45 min)
2. **Follow** → Installation steps
3. **Test** → All 6 agents with test file
4. **Read** → `example-workflow.md` (10 min)
5. **Practice** → Run example workflow
6. **Reference** → `cursor-rules.md` (keep open)
7. **Use** → Start with real cases

### For Experienced Users:

1. **Copy** → `.env.example` to `.env.local`
2. **Configure** → Credentials
3. **Install** → `pip install -r requirements.txt`
4. **Test** → `python codered-client.py test`
5. **Use** → Press `Cmd+Shift+A` and go

---

## File Dependencies

```
cursor-settings.json
├── requires: agents.yaml (agent definitions)
├── requires: tools.yaml (tool permissions)
└── requires: .env.local (credentials)

codered-client.py
├── requires: .env.local (SUPABASE_URL, SUPABASE_SERVICE_KEY)
└── imports: supabase, python-dotenv

rag-context-fetcher.py
├── requires: .env.local (SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY)
├── imports: codered-client.py
└── imports: supabase, openai, python-dotenv

cost-tracker.py
├── requires: .env.local (SUPABASE_URL, SUPABASE_SERVICE_KEY)
├── imports: codered-client.py
└── imports: supabase, python-dotenv

privilege-detector.py
├── requires: .env.local (SUPABASE_URL, SUPABASE_SERVICE_KEY)
├── imports: codered-client.py
└── imports: supabase, python-dotenv
```

---

## Version History

### Version 1.0 (December 16, 2025)
- Initial release
- 13 core files
- 3 documentation files
- 6 AI agents (Architect, Code, Test, Review, Evidence, Cynic)
- 4 Python helper scripts
- Complete installation guide
- Example workflow demonstration

---

## File Checklist

Use this checklist to verify complete installation:

- [ ] cursor-rules.md (19 KB)
- [ ] cursor-settings.json (13 KB)
- [ ] agents.yaml (16 KB)
- [ ] tools.yaml (10 KB)
- [ ] codered-client.py (11 KB)
- [ ] rag-context-fetcher.py (7.8 KB)
- [ ] cost-tracker.py (9.7 KB)
- [ ] privilege-detector.py (9.7 KB)
- [ ] extensions.json (2.5 KB)
- [ ] launch.json (3.4 KB)
- [ ] .env.example (1.7 KB)
- [ ] requirements.txt (636 B)
- [ ] README.md (13 KB)
- [ ] example-workflow.md (24 KB)
- [ ] INSTALLATION_GUIDE.md (12 KB)
- [ ] FILE_INDEX.md (this file)

**Total**: 16 files

---

## Support

For questions or issues:

1. **Check troubleshooting** in `INSTALLATION_GUIDE.md`
2. **Review** `cursor-rules.md` for usage guidance
3. **Test connection** with `python codered-client.py test`
4. **Check logs** in Supabase dashboard

---

**Complete File Index - Version 1.0**
*Last Updated: December 16, 2025*
