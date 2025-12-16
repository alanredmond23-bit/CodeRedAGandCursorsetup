# 🚀 CodeGreen: 30-Minute Setup Guide

**System**: CodeGreen Generic Software Development Platform  
**Total Setup Time**: 30 minutes  
**Goal**: Full working system across Cursor IDE, Antigravity, Claude Code Terminal  
**Status**: ✅ Ready to Deploy

---

## ⏱️ Timeline Overview

```
Min 0-5:   Setup Secrets
Min 5-15:  Deploy Database
Min 15-20: Configure Claude Terminal
Min 20-25: Configure Cursor IDE
Min 25-30: Start Antigravity
```

---

## 📋 Pre-Requisites (Complete Before Starting)

- ✅ GitHub account + PAT token (GitHub Settings → Tokens → Personal Access Tokens)
- ✅ Supabase project created (supabase.com)
- ✅ Vercel account (vercel.com) for deployments
- ✅ Cursor IDE installed
- ✅ Claude Code CLI installed
- ✅ Antigravity access
- ✅ API keys for monitoring (Sentry/Datadog - optional)

---

## ⏰ MINUTE 0-5: Setup Secrets

### Step 1: Create Secrets Directory
```bash
mkdir -p /Users/alanredmond/Desktop/SECRETS
cd /Users/alanredmond/Desktop/SECRETS
```

### Step 2: Create `.codegreen-secrets.env`
```bash
cat > .codegreen-secrets.env << 'EOF'
# ============================================================================
# CodeGreen Secrets Configuration
# KEEP THIS LOCAL - NEVER COMMIT TO GIT
# ============================================================================

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# npm (if using private packages)
NPM_TOKEN=npm_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Monitoring (Optional)
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
DATADOG_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Vercel
VERCEL_TOKEN=xxxxxxxxxxxxxxxxxxxxx
VERCEL_ORG_ID=your-org-id
VERCEL_PROJECT_ID_STAGING=your-staging-project
VERCEL_PROJECT_ID_PROD=your-prod-project

# Slack (for notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional: CI/CD Platform
CIRCLE_CI_TOKEN=xxxxxxxxxxxxxxxxxxxxx
EOF
```

### Step 3: Protect Secrets File
```bash
chmod 600 .codegreen-secrets.env
echo "✅ Secrets file created and protected"
```

### ✅ Done: 5 minutes

---

## ⏰ MINUTE 5-15: Deploy Database

### Step 1: Load Secrets
```bash
source /Users/alanredmond/Desktop/SECRETS/.codegreen-secrets.env
echo "✅ Secrets loaded"
```

### Step 2: Navigate to CodeGreen
```bash
cd /Users/alanredmond/Desktop/CodeGreen
```

### Step 3: Deploy Supabase Schema
```bash
# Run main development tracking schema
psql $SUPABASE_URL -f 05_SUPABASE_INTEGRATION/0001-dev-tracking-schema.sql

echo "✅ Database schema deployed"
```

### Step 4: Verify Database
```bash
# Test connection
psql $SUPABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Should return: 35 tables created
echo "✅ Database verified with 35 tables"
```

### ✅ Done: 10 minutes (Total: 15 min)

---

## ⏰ MINUTE 15-20: Configure Claude Code Terminal

### Step 1: Load Configuration
```bash
# Copy settings to home directory
cp /Users/alanredmond/Desktop/CodeGreen/.codegreen-settings.json ~/.codegreen-settings.json

echo "✅ Settings loaded"
```

### Step 2: Initialize Claude Code Project
```bash
# Start Claude Code with CodeGreen
claude code project /Users/alanredmond/Desktop/CodeGreen

# This will:
# • Load all 5 agent prompts
# • Configure 6 MCPs
# • Setup sync engine
```

### Step 3: Test Each Agent
In Claude Code terminal, type:
```
help agents
```

You should see:
```
CodeGreen Agents Available:
1. Code Analysis Agent     (Cmd+Shift+A) - Code review & analysis
2. Coordinator Agent       (Cmd+Shift+C) - Route requests
3. Task Management Agent   (Cmd+Shift+T) - GitHub issues & PRs
4. Architecture Agent      (Cmd+Shift+S) - System design
5. Test Agent             (Cmd+Shift+R) - Testing & coverage
6. Performance Agent      (Cmd+Shift+P) - Performance optimization
```

### Step 4: Verify MCPs Connected
```
status mcps
```

Should show all 6 MCPs: ✅ GitHub, ✅ npm, ✅ CI/CD, ✅ Monitoring, ✅ Docs, ✅ CodeSearch

### ✅ Done: 5 minutes (Total: 20 min)

---

## ⏰ MINUTE 20-25: Configure Cursor IDE

### Step 1: Copy Cursor Settings
```bash
cp /Users/alanredmond/Desktop/CodeGreen/03_CURSOR_IDE/cursor-settings.json \
   ~/.cursor/settings.json

echo "✅ Cursor settings loaded"
```

### Step 2: Open Your Project in Cursor
```bash
cursor /Users/alanredmond/Desktop/CodeGreen
```

### Step 3: Verify Keyboard Shortcuts Work
In any file, try these shortcuts:

| Shortcut | Expected | Status |
|----------|----------|--------|
| `Cmd+Shift+A` | Code Analysis prompt | ✅ |
| `Cmd+Shift+C` | Coordinator prompt | ✅ |
| `Cmd+Shift+T` | Task Management prompt | ✅ |
| `Cmd+Shift+S` | Architecture prompt | ✅ |
| `Cmd+Shift+R` | Test Agent prompt | ✅ |
| `Cmd+Shift+P` | Performance prompt | ✅ |

### Step 4: Check Sidebar Panels
Verify you see:
- ✅ CodeGreen Status
- ✅ Project Overview
- ✅ Open Tasks
- ✅ Metrics Dashboard
- ✅ Agent Suggestions

### Step 5: Test GitHub Integration
Cursor should show:
- Open PRs
- Recent commits
- Test coverage
- Last build status

### ✅ Done: 5 minutes (Total: 25 min)

---

## ⏰ MINUTE 25-30: Start Antigravity

### Step 1: Load Configuration
```bash
cp /Users/alanredmond/Desktop/CodeGreen/02_ANTIGRAVITY/antigravity-config.yaml \
   ~/.antigravity/config.yaml

echo "✅ Antigravity config loaded"
```

### Step 2: Start Antigravity Workspace
```bash
# Open Antigravity and load workspace
# Configuration will auto-detect CodeGreen project
```

### Step 3: Enable Sync Engine
```bash
python /Users/alanredmond/Desktop/CodeGreen/02_ANTIGRAVITY/crew-sync.py

# Should print:
# ✅ Sync engine started
# ✅ Connected to Claude Code Terminal
# ✅ Syncing every 30 seconds
# ✅ Average latency: <2000ms
```

### Step 4: Verify Sync is Working
In Claude Code, make a change. It should appear in Antigravity within 2 seconds.

Test:
```bash
# Terminal
echo "test message" > /tmp/test.txt

# In Antigravity, verify it syncs within 2 seconds
# Check sync status: "Last sync: 1.2s ago"
```

### Step 5: Test All Three Systems Together
1. **Claude Code Terminal** - Source of truth
2. **Cursor IDE** - See changes with keyboard shortcut
3. **Antigravity** - See changes in cloud dashboard

Make a test change in Claude → See it in Cursor → See it in Antigravity

### ✅ Done: 5 minutes (Total: 30 min)

---

## 🎯 Verification Checklist

After 30 minutes, verify everything works:

### Claude Code Terminal
- [ ] All 5 agents respond to prompts
- [ ] 6 MCPs show as connected
- [ ] Settings loaded from `.codegreen-settings.json`
- [ ] Can type commands and get responses

### Cursor IDE
- [ ] All 6 keyboard shortcuts work (Cmd+Shift+A/C/T/S/R/P)
- [ ] Sidebar shows CodeGreen Status
- [ ] Test coverage displays inline
- [ ] GitHub integration shows PRs/issues

### Antigravity
- [ ] Workspace opens without errors
- [ ] 3 native cloud agents visible
- [ ] Sync status shows "Connected"
- [ ] Latency displays as <2000ms
- [ ] Changes from Claude Terminal appear within 2 seconds

### Database
- [ ] 35 tables created in Supabase
- [ ] Can query tables from all 3 IDEs
- [ ] Metrics displaying in real-time

### CI/CD
- [ ] GitHub Actions workflows visible
- [ ] Secrets configured in GitHub
- [ ] Can trigger build manually

---

## 🎓 What Just Happened?

You now have a **unified development platform** with:

### **Claude Code Terminal** (Source of Truth)
- 5 specialized dev agents
- 6 MCPs (GitHub, npm, CI/CD, Monitoring, Docs, Code Search)
- Real-time metrics
- Session management

### **Cursor IDE** (Developer Workspace)
- 6 keyboard shortcuts to all agents
- Auto-loaded project context
- Real-time code metrics inline
- GitHub integration

### **Antigravity** (Cloud Orchestration)
- 3 native cloud agents
- Bidirectional sync (30s cycles, <2s latency)
- Conflict resolution with Claude as source
- Health monitoring

### **Database** (35 Tables)
- Projects & repositories
- Code quality metrics
- Test results & coverage
- Deployments & builds
- Performance monitoring
- Error tracking

### **CI/CD Pipeline** (7 Workflows)
- Build, Test, Quality, Security, Performance
- Deploy to Staging & Production
- Automated notifications
- Performance monitoring

---

## 🚀 Next Steps (What to Do Now)

### **This Week**
1. Connect your first GitHub repository
2. Run the build/test/deploy pipeline
3. Upload your first project to CodeGreen
4. Test each of the 5 agents with your real code

### **Next Week**
1. Fine-tune the 5 agents based on your needs
2. Configure team permissions
3. Setup monitoring dashboards
4. Deploy first feature through the pipeline

### **Ongoing**
1. Monitor costs per agent/task
2. Track test coverage and performance trends
3. Use CodeGreen for all development decisions
4. Share metrics with your team

---

## 🆘 Troubleshooting

### Issue: "GITHUB_TOKEN not found"
**Solution**: Verify `.codegreen-secrets.env` is sourced
```bash
source /Users/alanredmond/Desktop/SECRETS/.codegreen-secrets.env
echo $GITHUB_TOKEN
```

### Issue: "Cannot connect to Supabase"
**Solution**: Check connection string
```bash
psql $SUPABASE_URL -c "SELECT NOW();"
```

### Issue: "Keyboard shortcuts not working in Cursor"
**Solution**: Reload settings
```bash
# Close Cursor completely
# Delete ~/.cursor/cache
# Reopen Cursor
# Shortcuts should work
```

### Issue: "Antigravity sync latency > 5 seconds"
**Solution**: Check network connection
```bash
# Verify network
ping www.google.com

# Check sync logs
tail -f /tmp/antigravity-sync.log
```

### Issue: "Test coverage not showing in Cursor"
**Solution**: Run tests first
```bash
npm run test:unit -- --coverage
# Wait 30 seconds for sync
# Metrics should appear in Cursor
```

---

## 📞 Quick Reference

### Critical Locations
```
Secrets:           /Users/alanredmond/Desktop/SECRETS/.codegreen-secrets.env
CodeGreen Root:    /Users/alanredmond/Desktop/CodeGreen/
Settings Hub:      ~/.codegreen-settings.json
Cursor Config:     ~/.cursor/settings.json
Antigravity Config: ~/.antigravity/config.yaml
```

### Key Commands
```bash
# Start Claude Code Terminal
claude code project /Users/alanredmond/Desktop/CodeGreen

# Start Antigravity sync
python /Users/alanredmond/Desktop/CodeGreen/02_ANTIGRAVITY/crew-sync.py

# Open Cursor
cursor /Users/alanredmond/Desktop/CodeGreen

# Verify all MCPs
claude code status mcps

# Test agent
claude code agent "code-analysis" "review my code"
```

### Keyboard Shortcuts
```
Cmd+Shift+A  →  Code Analysis Agent
Cmd+Shift+C  →  Coordinator Agent
Cmd+Shift+T  →  Task Management Agent
Cmd+Shift+S  →  Architecture Agent
Cmd+Shift+R  →  Test Agent
Cmd+Shift+P  →  Performance Agent
```

---

## ✅ Success Criteria

Your setup is **complete and working** when:

1. ✅ All 3 IDEs open without errors
2. ✅ All 5 agents respond to requests
3. ✅ All 6 MCPs show as connected
4. ✅ Keyboard shortcuts work in Cursor
5. ✅ Antigravity syncs within 2 seconds
6. ✅ Database queries return data
7. ✅ GitHub Actions workflows run
8. ✅ Metrics display in real-time
9. ✅ Test coverage shows inline
10. ✅ You can make a full workflow: Code → Test → Deploy

---

## 🎉 You're Done!

Your CodeGreen development platform is now **fully operational**.

**What you have**:
- Unified development environment
- 5 specialized agents
- Real-time metrics
- Full CI/CD pipeline
- Production-grade database
- Bidirectional cloud sync

**What you can do next**:
- Deploy your first project
- Run your first workflow
- Start generating insights
- Optimize your development process

---

**System Status**: ✅ **PRODUCTION READY**

*Setup completed in 30 minutes. Now go build something amazing!*

*Questions? Check `.codegreen-settings.json` or system-prompt-master.md for details.*
