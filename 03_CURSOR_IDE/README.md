# Cursor IDE Integration for CodeRed Legal Discovery

**Complete Cursor IDE configuration for legal discovery workflows with AI agent orchestration**

Version: 1.0
Last Updated: December 16, 2025

---

## Overview

This package provides a complete Cursor IDE integration for the CodeRed Legal Discovery system. It enables:

- **6 AI Agents** accessible via keyboard shortcuts
- **Automatic RAG context injection** from case documents
- **Real-time cost tracking** logged to Supabase
- **Privilege detection** to protect attorney-client communications
- **Zone-based permissions** (RED/YELLOW/GREEN)
- **Seamless workflow** - never leave the IDE

---

## Quick Start (5 Minutes)

### 1. Install Prerequisites

```bash
# Install Python dependencies
pip install supabase openai python-dotenv

# Optional: Install Cursor IDE extensions
# Open Cursor → Extensions → Search for:
# - Python
# - Supabase
# - GitLens
```

### 2. Configure Credentials

```bash
# Copy environment template
cp cursor/.env.example cursor/.env.local

# Edit .env.local with your credentials
# Get these from:
# - Supabase: https://app.supabase.com → Settings → API
# - OpenAI: https://platform.openai.com → API Keys
```

### 3. Test Connection

```bash
# Test Supabase connection
python cursor/codered-client.py test

# Should output:
# ✅ Connection successful! Found 5 agents
```

### 4. Open Cursor and Use Agents

```
1. Open any file in your legal case
2. Press Cmd+Shift+A (Architect agent)
3. Ask: "What is the case strength?"
4. Get response with RAG context automatically injected
5. Cost logged to Supabase
```

---

## Keyboard Shortcuts

| Shortcut | Agent | Purpose | Cost |
|----------|-------|---------|------|
| `Cmd+Shift+A` | **Architect** | Case strategy, settlement analysis | $3-5 |
| `Cmd+Shift+C` | **Code** | Document parsing, automation | $2-3 |
| `Cmd+Shift+T` | **Test** | QA, validation (cheap!) | $0.10-0.50 |
| `Cmd+Shift+R` | **Review** | Document/code review | $2-3 |
| `Cmd+Shift+E` | **Evidence** | Timeline analysis, contradictions | $3-4 |
| `Cmd+Shift+S` | **Cynic** | Risk assessment, privilege check | $3-5 |

---

## Files Included

```
cursor/
├── cursor-rules.md              # Complete rules and usage guide
├── cursor-settings.json         # IDE configuration with keybindings
├── agents.yaml                  # 6 agent definitions
├── tools.yaml                   # Tool permissions and capabilities
├── codered-client.py            # Supabase database client
├── rag-context-fetcher.py       # Automatic context fetching
├── cost-tracker.py              # Cost tracking and reporting
├── privilege-detector.py        # Privilege detection
├── extensions.json              # Recommended VS Code extensions
├── launch.json                  # Debug configurations
├── .env.example                 # Environment template
├── README.md                    # This file
└── example-workflow.md          # Detailed workflow walkthrough
```

---

## Setup Guide

### Step 1: Copy Configuration Files

```bash
# If using Cursor in a specific project directory
cd /path/to/your/legal/case
mkdir -p .cursor

# Copy Cursor configuration
cp /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/cursor-settings.json .cursor/settings.json

# Copy helper scripts
cp -r /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/*.py .cursor/

# Copy .env template
cp /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/.env.example .env.local
```

### Step 2: Configure Environment Variables

Edit `.env.local`:

```bash
# Required
SUPABASE_URL=https://xgcqjwviirrkyhwlaeyr.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # From Supabase dashboard
OPENAI_API_KEY=sk-proj-...       # From OpenAI dashboard

# Optional (for enhanced features)
WESTLAW_API_KEY=...
LEXISNEXIS_API_KEY=...
```

**IMPORTANT**: Add `.env.local` to `.gitignore`:

```bash
echo ".env.local" >> .gitignore
```

### Step 3: Test All Components

```bash
# Test Supabase connection
python .cursor/codered-client.py test

# Test RAG context fetching
python .cursor/rag-context-fetcher.py \
  --file /path/to/case/document.txt \
  --top-k 5

# Test privilege detection
python .cursor/privilege-detector.py \
  --file /path/to/email.txt

# Test cost tracking
python .cursor/cost-tracker.py --report today
```

### Step 4: Configure Cursor IDE

1. **Open Cursor Settings** (Cmd+,)
2. **Load configuration**:
   - Settings → Workspace → Open Settings (JSON)
   - Copy contents from `cursor-settings.json`
3. **Install recommended extensions**:
   - Open Extensions panel
   - Search for extensions listed in `extensions.json`
4. **Verify keybindings**:
   - Preferences → Keyboard Shortcuts
   - Search for "cursor.chat.openWithContext"
   - Should see Cmd+Shift+A/C/T/R/E/S bindings

---

## Usage Examples

### Example 1: Case Strength Analysis

```
1. Open case summary file
2. Press Cmd+Shift+A (Architect)
3. Ask: "Analyze the case strength and identify weaknesses"

Response:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CASE CONTEXT (Auto-Fetched)

Case ID: CUSTODY-2024-001
Relevant Documents:
- Email: Smith to Jones, March 15 (similarity: 87%)
- Deposition: Smith testimony (similarity: 82%)
- Motion: Modification request (similarity: 79%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSIS

Case Strength: B+ (Strong, but with vulnerabilities)

Strengths:
1. Clear documentation of custodial interference
2. Witness corroboration from 3rd party
3. Favorable precedent: In re Johnson (2022)

Weaknesses:
1. Timeline inconsistency in Smith deposition
2. Missing financial records for March-April
3. Opposing counsel has strong character witnesses

Recommendations:
1. Subpoena financial records immediately
2. Cross-examine on timeline inconsistency
3. Depose character witnesses

Settlement Range: $75K-$125K

Cost: $3.45 | Zone: YELLOW | Logged: run_12345
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Example 2: Document Parsing Automation

```
1. Open email batch folder
2. Press Cmd+Shift+C (Code)
3. Ask: "Parse these emails and extract timeline"

Response:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Here's a Python script to parse the emails:

```python
import os
import re
from datetime import datetime

def parse_emails(folder_path):
    timeline = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            with open(os.path.join(folder_path, filename)) as f:
                content = f.read()

                # Extract date
                date_match = re.search(r'Date: (.+)', content)
                date = datetime.strptime(date_match.group(1), '%Y-%m-%d')

                # Extract parties
                from_match = re.search(r'From: (.+)', content)
                to_match = re.search(r'To: (.+)', content)

                timeline.append({
                    'date': date,
                    'from': from_match.group(1),
                    'to': to_match.group(1),
                    'file': filename
                })

    # Sort by date
    timeline.sort(key=lambda x: x['date'])

    return timeline

# Usage
timeline = parse_emails('/cases/CUSTODY-2024-001/emails/')
for event in timeline:
    print(f"{event['date']}: {event['from']} → {event['to']}")
```

Cost: $2.25 | Zone: GREEN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Example 3: Privilege Detection

```
1. Open potentially privileged email
2. Press Cmd+Shift+S (Cynic)
3. Privilege detector runs automatically

Response:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 PRIVILEGED COMMUNICATION DETECTED

Confidence: 85%
Recommendation: RED ZONE

Keywords Found:
- "attorney-client privilege"
- "confidential"
- "legal strategy"

Patterns Detected:
- Attorney email domain: jsmith@lawfirm.com
- Privilege header in subject line

⚠️ ACCESS RESTRICTED
Only Architect, Evidence, and Cynic agents may access.
Human attorney approval required for queries.

Cost: $4.15 | Zone: RED | Flagged: flag_67890
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Zone-Based Permissions

### RED Zone (Highly Privileged)
- **Content**: Attorney-client communications, work product, trial strategy
- **Agents**: Architect, Evidence, Cynic only
- **Approval**: Required for queries over $5
- **Flagging**: Automatic via privilege detector

### YELLOW Zone (Moderately Sensitive)
- **Content**: Discovery documents, depositions, financial records
- **Agents**: All except Test
- **Approval**: Standard review
- **Flagging**: Manual or on keywords

### GREEN Zone (Public)
- **Content**: Public filings, case law, templates
- **Agents**: All agents
- **Approval**: None
- **Flagging**: None

---

## Cost Tracking

### View Today's Costs

```bash
python cursor/cost-tracker.py --report today
```

Output:
```
# COST REPORT - TODAY

Total Cost: $42.75
Query Count: 15
Average Cost: $2.85/query

By Agent:
- architect: $15.50 (36.3%)
- evidence: $12.25 (28.7%)
- code: $8.50 (19.9%)
- review: $6.50 (15.2%)

By Case:
- CUSTODY-2024-001: $28.25 (66.1%)
- FEDS-2024-042: $14.50 (33.9%)
```

### Check Budget Status

```bash
python cursor/cost-tracker.py --check-budget --budget 200.0
```

Output:
```
Budget Status: OK
Spent: $42.75 / $200.00
Remaining: $157.25
```

---

## Troubleshooting

### Agent Not Responding

**Symptom**: Press Cmd+Shift+A, nothing happens

**Fix**:
```bash
# Check Supabase connection
python cursor/codered-client.py test

# Verify environment variables
cat .env.local | grep SUPABASE

# Restart Cursor IDE
```

### RAG Context Not Appearing

**Symptom**: Agent responds without case context

**Fix**:
```bash
# Check embeddings exist
python cursor/codered-client.py query

# Ingest documents if none found
python cursor/rag-context-fetcher.py \
  --ingest \
  --file /path/to/document.txt \
  --case-id CUSTODY-2024-001
```

### Privilege Detection Inaccurate

**Symptom**: False positives or false negatives

**Fix**:
- Edit `cursor/privilege-detector.py`
- Add jurisdiction-specific keywords to `KEYWORDS` dict
- Adjust confidence threshold in `.env.local`

### Costs Too High

**Symptom**: Budget alerts triggered

**Fix**:
- Use Test agent (gpt-4o-mini) for simple tasks
- Enable RAG caching: `RAG_CACHE_ENABLED=true`
- Batch similar queries
- Review agent usage patterns

---

## Advanced Configuration

### Custom Agent Models

Edit `cursor-settings.json`:

```json
"codered.agents": {
  "architect": {
    "model": "gpt-4o-2024-08-06",  // Use specific model version
    "temperature": 0.2,             // Lower = more deterministic
    "maxTokens": 5000               // Increase for longer responses
  }
}
```

### Custom Zone Keywords

Edit `.env.local`:

```bash
# Add custom privilege keywords (comma-separated)
PRIVILEGE_KEYWORDS="settlement,trial prep,expert strategy"
```

### Custom Cost Budgets

Edit `.env.local`:

```bash
DAILY_COST_BUDGET=500.0    # Increase daily budget
WEEKLY_COST_BUDGET=2000.0
MONTHLY_COST_BUDGET=10000.0
```

---

## Integration with Other Systems

### Antigravity Cloud Sync

```bash
# Sync agent runs to Antigravity
# TODO: Add antigravity sync script
```

### Claude Code Terminal

```bash
# Share RAG context with Claude terminal
# TODO: Add terminal integration
```

### GitHub Version Control

```bash
# Version control case templates
git add templates/
git commit -m "Update motion template"
git push
```

---

## Security Best Practices

1. **Never commit .env.local** to version control
2. **Rotate API keys** quarterly
3. **Review privilege flags** manually for high-stakes cases
4. **Audit agent logs** weekly
5. **Limit RED zone access** to senior attorneys only
6. **Use strong Supabase service key** (at least 64 characters)
7. **Enable MFA** on all API accounts

---

## Support & Documentation

- **Full Documentation**: See `cursor-rules.md`
- **Workflow Example**: See `example-workflow.md`
- **Agent Definitions**: See `agents.yaml`
- **Tool Permissions**: See `tools.yaml`
- **Supabase Schema**: See `/03_SCHEMA/0001_codered_base.sql`

---

## FAQ

**Q: Can I use Claude models instead of OpenAI?**
A: Yes, set `ANTHROPIC_API_KEY` and update agent models in `cursor-settings.json`.

**Q: How do I add a new case?**
A: Ingest documents with case ID: `--case-id NEW-CASE-2024-001`

**Q: Can I customize keyboard shortcuts?**
A: Yes, edit `cursor-settings.json` → `keybindings` section.

**Q: How do I share this with other attorneys?**
A: Share this folder (except `.env.local`). Each attorney creates their own `.env.local`.

**Q: Is this HIPAA/SOC2 compliant?**
A: Depends on your Supabase and OpenAI configurations. Consult your compliance team.

---

## License

Copyright 2025 CodeRed Legal Tech
All rights reserved.

---

**Built with**: Cursor IDE, Supabase, OpenAI, Python
**Version**: 1.0
**Last Updated**: December 16, 2025
