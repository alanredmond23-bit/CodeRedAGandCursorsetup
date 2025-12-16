# Cursor IDE Installation & Setup Guide

**Complete installation guide for CodeRed Legal Discovery Cursor integration**

Version: 1.0
Time Required: 30-45 minutes
Difficulty: Beginner

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Cursor IDE** installed ([https://cursor.sh](https://cursor.sh))
- [ ] **Python 3.9+** installed (`python --version`)
- [ ] **Supabase account** with CodeRed database deployed
- [ ] **OpenAI API key** ([https://platform.openai.com](https://platform.openai.com))
- [ ] **Git** installed (for version control)
- [ ] **Code editor** (for editing .env files)

---

## Step 1: Install Python Dependencies (5 minutes)

### Option A: Using pip

```bash
# Navigate to cursor folder
cd /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import supabase; print('✅ Supabase installed')"
python -c "import openai; print('✅ OpenAI installed')"
```

### Option B: Using conda

```bash
# Create virtual environment
conda create -n codered python=3.11
conda activate codered

# Install dependencies
pip install -r requirements.txt
```

### Option C: Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure Environment Variables (10 minutes)

### 2.1 Copy Template

```bash
cd /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/
cp .env.example .env.local
```

### 2.2 Get Supabase Credentials

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Select your project: `xgcqjwviirrkyhwlaeyr`
3. Click **Settings** → **API**
4. Copy:
   - **URL**: `https://xgcqjwviirrkyhwlaeyr.supabase.co`
   - **Service Role Key**: `eyJhbGc...` (long string starting with "eyJ")

### 2.3 Get OpenAI API Key

1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Click **API Keys**
3. Click **Create new secret key**
4. Copy key (starts with `sk-proj-...`)

### 2.4 Edit .env.local

```bash
# Open in your editor
nano .env.local
# OR
code .env.local
# OR
open -a "TextEdit" .env.local
```

**Required fields**:
```bash
SUPABASE_URL=https://xgcqjwviirrkyhwlaeyr.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # Paste your key
OPENAI_API_KEY=sk-proj-...       # Paste your key
```

**Optional fields** (can configure later):
```bash
# Anthropic (if using Claude models)
ANTHROPIC_API_KEY=sk-ant-...

# Westlaw (for legal research)
WESTLAW_API_KEY=...

# LexisNexis (for legal research)
LEXISNEXIS_API_KEY=...
```

### 2.5 Secure the File

```bash
# Make .env.local read-only
chmod 600 .env.local

# Add to .gitignore (if using Git)
echo ".env.local" >> .gitignore
```

---

## Step 3: Test Supabase Connection (5 minutes)

### 3.1 Run Connection Test

```bash
cd /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/
python codered-client.py test
```

**Expected output**:
```
✅ Connection successful! Found 5 agents
```

**If you see errors**:

**Error: "Missing credentials"**
```bash
# Check .env.local exists
ls -la .env.local

# Check it's loaded
python -c "from dotenv import load_dotenv; load_dotenv('.env.local'); import os; print(os.getenv('SUPABASE_URL'))"
```

**Error: "Connection failed"**
```bash
# Check Supabase URL is correct
# Should be: https://xgcqjwviirrkyhwlaeyr.supabase.co

# Check Supabase service key is correct
# Should start with: eyJhbGc...

# Test network connection
curl https://xgcqjwviirrkyhwlaeyr.supabase.co/rest/v1/
```

### 3.2 Verify Database Tables

```bash
# Check agents exist
python codered-client.py query

# Should show 5 agents:
# - architect
# - code
# - test
# - review
# - evidence
# - cynic
```

---

## Step 4: Configure Cursor IDE (10 minutes)

### 4.1 Install Cursor IDE

If not already installed:

1. Download from [https://cursor.sh](https://cursor.sh)
2. Install application
3. Open Cursor

### 4.2 Create Workspace

```bash
# Create workspace folder for your cases
mkdir -p ~/legal-cases
cd ~/legal-cases

# Copy Cursor configuration
cp -r /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor .cursor

# Copy .env.local
cp /Users/alanredmond/Desktop/CodeRedAGandCursorsetup/cursor/.env.local .

# Open in Cursor
cursor .
```

### 4.3 Load Configuration

**Method 1: Via Settings UI**

1. Press `Cmd+,` (open Settings)
2. Click **Workspace** tab
3. Click **Open Settings (JSON)**
4. Paste contents from `.cursor/cursor-settings.json`
5. Save and restart Cursor

**Method 2: Via Command Line**

```bash
# Copy settings to Cursor workspace
mkdir -p .vscode
cp .cursor/cursor-settings.json .vscode/settings.json
```

### 4.4 Install Extensions

1. Press `Cmd+Shift+X` (open Extensions)
2. Install required extensions:
   - **Python** (ms-python.python)
   - **Pylance** (ms-python.vscode-pylance)
   - **Supabase** (supabase.supabase-vscode)

3. Install recommended extensions:
   - **GitLens** (eamodio.gitlens)
   - **Markdown All in One** (yzhang.markdown-all-in-one)
   - **Code Spell Checker** (streetsidesoftware.code-spell-checker)

### 4.5 Configure Keybindings

Verify keyboard shortcuts are configured:

1. Press `Cmd+K Cmd+S` (open Keyboard Shortcuts)
2. Search for "cursor.chat.openWithContext"
3. Should see 6 bindings:
   - `Cmd+Shift+A` → Architect
   - `Cmd+Shift+C` → Code
   - `Cmd+Shift+T` → Test
   - `Cmd+Shift+R` → Review
   - `Cmd+Shift+E` → Evidence
   - `Cmd+Shift+S` → Cynic

**If not configured**, manually add to `keybindings.json`:

1. `Cmd+K Cmd+S` → Click **keybindings.json** icon (top right)
2. Paste contents from `.cursor/cursor-settings.json` → `keybindings` section

---

## Step 5: Test Agent Integration (5 minutes)

### 5.1 Create Test File

```bash
# Create test case folder
mkdir -p ~/legal-cases/TEST-2024-001
cd ~/legal-cases/TEST-2024-001

# Create test document
cat > test-note.md << 'EOF'
# Test Case Note

Case ID: TEST-2024-001
Type: Testing Cursor integration

This is a test document to verify agent integration.
EOF
```

### 5.2 Test Each Agent

**Open test-note.md in Cursor**

1. **Test Architect** (`Cmd+Shift+A`)
   - Ask: "What is this document about?"
   - Should get response with RAG context
   - Check status bar shows cost

2. **Test Code** (`Cmd+Shift+C`)
   - Ask: "Write a Python script to read this file"
   - Should get working Python code

3. **Test Test** (`Cmd+Shift+T`)
   - Ask: "Validate this document format"
   - Should get validation report

4. **Test Review** (`Cmd+Shift+R`)
   - Ask: "Review this document"
   - Should get review feedback

5. **Test Evidence** (`Cmd+Shift+E`)
   - Ask: "Extract key facts"
   - Should get fact extraction

6. **Test Cynic** (`Cmd+Shift+S`)
   - Ask: "What could go wrong?"
   - Should get risk assessment

### 5.3 Verify Logging

```bash
# Check costs were logged
python .cursor/cost-tracker.py --report today

# Should show:
# - Total Cost: $X.XX
# - Query Count: 6
# - By Agent: (breakdown)
```

---

## Step 6: Ingest Your First Document (5 minutes)

### 6.1 Prepare Document

```bash
# Example: Ingest a case note
python .cursor/rag-context-fetcher.py \
  --ingest \
  --file ~/legal-cases/TEST-2024-001/test-note.md \
  --case-id TEST-2024-001 \
  --zone GREEN
```

**Expected output**:
```json
{
  "document_id": "uuid-here",
  "status": "success"
}
```

### 6.2 Test RAG Retrieval

```bash
# Query for the document
python .cursor/rag-context-fetcher.py \
  --file ~/legal-cases/TEST-2024-001/test-note.md \
  --top-k 5
```

**Expected output**:
```markdown
# CASE CONTEXT (Auto-Fetched)

Case ID: TEST-2024-001
Relevant Documents (1 found):
- Test Case Note (similarity: 100%)
```

---

## Step 7: Configure Budget Alerts (Optional)

### 7.1 Set Budget Thresholds

Edit `.env.local`:

```bash
# Daily budget (per attorney)
DAILY_COST_BUDGET=200.0

# Weekly budget
WEEKLY_COST_BUDGET=1000.0

# Monthly budget
MONTHLY_COST_BUDGET=5000.0

# Alert email
COST_ALERT_EMAIL=attorney@lawfirm.com
```

### 7.2 Test Budget Alerts

```bash
# Check budget status
python .cursor/cost-tracker.py \
  --check-budget \
  --budget 200.0
```

**Expected output**:
```
Budget Status: OK
Spent: $X.XX / $200.00
Remaining: $YY.YY
```

---

## Step 8: Verify Privilege Detection (Optional)

### 8.1 Create Test Privileged Document

```bash
cat > ~/legal-cases/TEST-2024-001/privileged-email.txt << 'EOF'
From: attorney@lawfirm.com
To: client@email.com
Subject: Attorney-Client Privileged Communication

Dear Client,

This email contains confidential attorney-client privileged information
regarding our trial strategy for your custody case.

[Content redacted for test]

Best regards,
Your Attorney
EOF
```

### 8.2 Test Privilege Detection

```bash
python .cursor/privilege-detector.py \
  --file ~/legal-cases/TEST-2024-001/privileged-email.txt
```

**Expected output**:
```markdown
# PRIVILEGE DETECTION REPORT

Is Privileged: YES
Confidence: 85%
Recommendation: 🔴 RED ZONE

Keywords Found:
- attorney-client privileged
- confidential
- trial strategy

Patterns Detected:
- Attorney email domain: attorney@lawfirm.com
```

---

## Step 9: Final Verification

### Checklist

- [ ] Python dependencies installed
- [ ] `.env.local` configured with credentials
- [ ] Supabase connection successful
- [ ] Cursor IDE configured
- [ ] All 6 agents tested
- [ ] RAG document ingestion working
- [ ] Cost tracking logging correctly
- [ ] Privilege detection working
- [ ] Budget alerts configured (optional)

### Test Full Workflow

1. **Create a case folder**
   ```bash
   mkdir -p ~/legal-cases/REAL-CASE-001
   cd ~/legal-cases/REAL-CASE-001
   ```

2. **Add a case document** (email, note, etc.)

3. **Ingest to RAG**
   ```bash
   python ~/.cursor/rag-context-fetcher.py \
     --ingest \
     --file document.txt \
     --case-id REAL-CASE-001 \
     --zone YELLOW
   ```

4. **Open in Cursor**
   ```bash
   cursor document.txt
   ```

5. **Press Cmd+Shift+A** (Architect)

6. **Ask a question** about the case

7. **Verify**:
   - RAG context appears
   - Response is relevant
   - Cost is logged
   - Status bar updates

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'supabase'"

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: "Connection to Supabase failed"

**Solution**:
```bash
# Check credentials
cat .env.local | grep SUPABASE

# Test URL
curl https://xgcqjwviirrkyhwlaeyr.supabase.co/rest/v1/

# Verify service key (should be long string starting with "eyJ")
```

### Issue: "Keyboard shortcuts not working"

**Solution**:
1. Open Cursor
2. `Cmd+K Cmd+S` (Keyboard Shortcuts)
3. Search "cursor.chat.openWithContext"
4. Manually add keybindings if missing

### Issue: "RAG context not appearing"

**Solution**:
```bash
# Check embeddings exist
python .cursor/codered-client.py query

# Ingest documents
python .cursor/rag-context-fetcher.py --ingest --file YOUR_FILE --case-id CASE_ID
```

### Issue: "Costs not logging"

**Solution**:
```bash
# Check Supabase connection
python .cursor/codered-client.py test

# Check cost_tracking table exists
# (Run in Supabase SQL editor)
SELECT * FROM codered.cost_tracking LIMIT 1;
```

---

## Next Steps

1. **Read Documentation**
   - `README.md` - Overview
   - `cursor-rules.md` - Complete usage guide
   - `example-workflow.md` - Real-world example

2. **Ingest Your Cases**
   - Organize case folders by case ID
   - Ingest all case documents to RAG
   - Tag with appropriate zones (RED/YELLOW/GREEN)

3. **Train Your Team**
   - Share this guide with other attorneys
   - Practice with test cases first
   - Set up shared Supabase access

4. **Monitor Costs**
   - Check daily reports
   - Adjust budgets as needed
   - Optimize agent usage

---

## Support

- **Documentation**: See `/cursor/README.md`
- **Issues**: Check Supabase logs
- **Questions**: Review `cursor-rules.md`

---

**Installation Complete!** 🎉

You now have a fully functional Cursor IDE integration for CodeRed Legal Discovery.

**Next**: Open `example-workflow.md` to see a complete 30-minute workflow example.

---

*Version 1.0 | December 16, 2025*
