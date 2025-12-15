# 🔐 Secrets Management Guide

**Status**: Secrets stay LOCAL on your desktop - NOT committed to GitHub
**Last Updated**: December 15, 2025

---

## ⚠️ Critical Security Rule

**SECRETS NEVER GO TO GITHUB**

All three systems (Cursor IDE, Google Antigravity, Claude Code Terminal) load their secrets from **local files on your desktop**, not from version control.

```
❌ NEVER commit to git:
  - .env files with API keys
  - Credentials
  - API tokens
  - Database passwords
  - 1Password emergency kits

✅ ALWAYS keep local:
  - ~/.env.local
  - /Users/alanredmond/Desktop/SECRETS/
  - SECRETS.env files
```

---

## 📁 Where Secrets Live (Desktop)

### Main Secrets Location
```
/Users/alanredmond/Desktop/SECRETS/
├── SECRETS.env                    # Master secrets file
├── SUPABASE_KEYS.env             # Supabase credentials
├── OPENAI_API_KEY.env            # OpenAI keys
├── TWILIO_KEYS.env               # Twilio tokens (if using)
├── GITHUB_TOKENS.env             # GitHub PATs
├── ANTHROPIC_API_KEY.env         # Claude/Anthropic keys
└── 1PASSWORD/                     # Emergency recovery
    └── 1Password_Emergency_Kit.pdf
```

**Do NOT share these files. Do NOT commit them.**

---

## 🎯 How Each System Loads Secrets

### 1️⃣ **CURSOR IDE**

**Location**: `/path/to/project/.env.local`

**How to setup**:
```bash
# Copy secrets to project root
cp /Users/alanredmond/Desktop/SECRETS/SECRETS.env .env.local

# Add to .cursor/settings.json
{
  "env": {
    "SUPABASE_URL": "${SUPABASE_URL}",
    "SUPABASE_KEY": "${SUPABASE_KEY}",
    "OPENAI_API_KEY": "${OPENAI_API_KEY}",
    "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
  }
}
```

**What it needs**:
| Variable | Source | Purpose |
|----------|--------|---------|
| `SUPABASE_URL` | `/Users/alanredmond/Desktop/SECRETS/SUPABASE_KEYS.env` | Connect to CodeRed database |
| `SUPABASE_SERVICE_KEY` | `/Users/alanredmond/Desktop/SECRETS/SUPABASE_KEYS.env` | Admin access for migrations |
| `OPENAI_API_KEY` | `/Users/alanredmond/Desktop/SECRETS/OPENAI_API_KEY.env` | (Optional) GPT integration |
| `ANTHROPIC_API_KEY` | `/Users/alanredmond/Desktop/SECRETS/ANTHROPIC_API_KEY.env` | Claude model access |
| `GITHUB_TOKEN` | `/Users/alanredmond/Desktop/SECRETS/GITHUB_TOKENS.env` | Repository operations |

**How to load in Cursor**:
```bash
# In .cursor/hooks/pre-load.sh
#!/bin/bash
source ~/.env.local
export SUPABASE_URL
export SUPABASE_KEY
export ANTHROPIC_API_KEY
```

**Never commit**:
- `.env.local` ✋ Local only
- `.env.production` ✋ Local only
- Any file with API keys ✋ Local only

---

### 2️⃣ **GOOGLE ANTIGRAVITY**

**Location**: Workspace settings (not in git)

**How to setup**:

1. **In Antigravity Workspace**:
   ```json
   // .antigravity/workspace-secrets.json (LOCAL ONLY)
   {
     "secrets": {
       "SUPABASE_URL": "https://xxxxx.supabase.co",
       "SUPABASE_KEY": "eyJhbGc...",
       "ANTHROPIC_API_KEY": "sk-ant-...",
       "TWILIO_AUTH_TOKEN": "ACxxxxx"
     }
   }
   ```

2. **Add to .antigravity/agent-modes/orchestrator.json**:
   ```json
   {
     "orchestrator": {
       "capabilities": {
         "database": {
           "supabase_url": "${SUPABASE_URL}",
           "supabase_key": "${SUPABASE_KEY}"
         },
         "cloud_ai": {
           "anthropic_key": "${ANTHROPIC_API_KEY}"
         }
       }
     }
   }
   ```

3. **Workspace Trust Configuration**:
   ```json
   // .antigravity/trust-config.json
   {
     "secret_paths": [
       "/Users/alanredmond/Desktop/SECRETS/*"
     ],
     "require_approval": [
       "*.env*",
       "*SECRETS*",
       "*KEY*"
     ]
   }
   ```

**What it needs**:
| Variable | Source | Purpose |
|----------|--------|---------|
| `SUPABASE_URL` | `/Users/alanredmond/Desktop/SECRETS/SUPABASE_KEYS.env` | Connect to CodeRed database |
| `SUPABASE_KEY` | `/Users/alanredmond/Desktop/SECRETS/SUPABASE_KEYS.env` | Database operations |
| `ANTHROPIC_API_KEY` | `/Users/alanredmond/Desktop/SECRETS/ANTHROPIC_API_KEY.env` | Agent model access |
| `TWILIO_AUTH_TOKEN` | `/Users/alanredmond/Desktop/SECRETS/TWILIO_KEYS.env` | SMS/voice notifications |

**How to load**:
```bash
# In Antigravity's agent startup
# Antigravity reads from workspace-secrets.json (local only)
# Never exposed to version control
```

**Never commit**:
- `.antigravity/workspace-secrets.json` ✋ Local only
- Any `.antigravity/*-secrets*` files ✋ Local only
- Agent mode files with keys ✋ Local only

---

### 3️⃣ **CLAUDE CODE TERMINAL**

**Location**: `~/.claude/.env.local` (global) or `.claude/.env.local` (project)

**How to setup**:

1. **Global Setup** (`~/.claude/`):
   ```bash
   # Create ~/.claude/.env.local
   SUPABASE_URL="https://xxxxx.supabase.co"
   SUPABASE_SERVICE_KEY="eyJhbGc..."
   ANTHROPIC_API_KEY="sk-ant-..."
   GITHUB_TOKEN="ghp_xxxx..."
   ```

2. **Project Setup** (`.claude/.env.local`):
   ```bash
   # Copy from desktop for local project
   cp /Users/alanredmond/Desktop/SECRETS/SECRETS.env .claude/.env.local

   # Add to .claude/settings.json
   {
     "environmentVariables": {
       "SUPABASE_URL": "${SUPABASE_URL}",
       "SUPABASE_SERVICE_KEY": "${SUPABASE_SERVICE_KEY}",
       "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
     }
   }
   ```

3. **Load in MCP configuration** (`.mcp.json`):
   ```json
   {
     "mcpServers": {
       "supabase": {
         "env": {
           "SUPABASE_URL": "${SUPABASE_URL}",
           "SUPABASE_SERVICE_KEY": "${SUPABASE_SERVICE_KEY}"
         }
       },
       "github": {
         "env": {
           "GITHUB_TOKEN": "${GITHUB_TOKEN}"
         }
       }
     }
   }
   ```

**What it needs**:
| Variable | Source | Purpose |
|----------|--------|---------|
| `SUPABASE_URL` | `/Users/alanredmond/Desktop/SECRETS/SUPABASE_KEYS.env` | Connect to CodeRed database |
| `SUPABASE_SERVICE_KEY` | `/Users/alanredmond/Desktop/SECRETS/SUPABASE_KEYS.env` | Admin operations for deployment |
| `ANTHROPIC_API_KEY` | `/Users/alanredmond/Desktop/SECRETS/ANTHROPIC_API_KEY.env` | Model access |
| `GITHUB_TOKEN` | `/Users/alanredmond/Desktop/SECRETS/GITHUB_TOKENS.env` | Repository access |

**How to load**:
```bash
# In ~/.claude/hooks/pre-load.sh
#!/bin/bash
source ~/.claude/.env.local
# Now all $VARIABLE references in .mcp.json work
```

**Never commit**:
- `.claude/.env.local` ✋ Local only
- `~/.claude/.env.local` ✋ Home directory, not version controlled
- Any mcp-servers.json with actual keys ✋ Use ${VAR} syntax instead

---

## 🔄 Loading Secrets in Each System

### Cursor IDE Flow
```
1. Developer opens project
2. Cursor loads .cursor/settings.json
3. Reads .env.local from project root
4. Variables available to agents via ${VARIABLE}
5. Agents use MCP to connect to Supabase with keys
```

### Antigravity Flow
```
1. Open Antigravity workspace
2. Workspace reads workspace-secrets.json (local)
3. .antigravity/agent-modes/ receive secrets
4. Agents authenticate to CodeRed database
5. Trust configuration validates secret access
```

### Claude Code Terminal Flow
```
1. Load Claude Code project/workspace
2. .claude/settings.json loads .env.local
3. MCP servers (.mcp.json) read ${VARIABLE} from environment
4. All MCPs (Supabase, GitHub, etc.) authenticated
5. Agents can deploy, log costs, and query database
```

---

## ✅ Verification Checklist

Before deploying, verify:

### For Cursor IDE
- [ ] `.env.local` exists in project root
- [ ] Contains `SUPABASE_URL` and `SUPABASE_KEY`
- [ ] `.cursor/settings.json` references env variables
- [ ] `.env.local` is in `.gitignore`
- [ ] Test: Can you query Supabase from agent? ✅

### For Antigravity
- [ ] `.antigravity/workspace-secrets.json` exists locally
- [ ] Contains all required API keys
- [ ] `.antigravity/trust-config.json` allows secret access
- [ ] Agent modes can access secrets
- [ ] Secrets are NOT in any `.md` files ✅
- [ ] Test: Can agents authenticate to CodeRed? ✅

### For Claude Code Terminal
- [ ] `~/.claude/.env.local` exists in home directory
- [ ] Contains `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, etc.
- [ ] `.claude/.env.local` (project) has local secrets
- [ ] `.mcp.json` uses `${VARIABLE}` syntax (not literal keys)
- [ ] Test: Can MCP connect to Supabase? ✅

---

## 🚨 Emergency Access

**If you lose local secrets:**

1. **1Password Recovery**:
   ```bash
   cd /Users/alanredmond/Desktop/SECRETS/1PASSWORD/
   open "1Password Emergency Kit.pdf"
   # Use emergency recovery code to unlock 1Password
   # Regenerate API keys from original sources
   ```

2. **Recreate from Sources**:
   - Supabase: https://app.supabase.com → Settings → API Keys
   - OpenAI: https://platform.openai.com → API Keys
   - Anthropic: https://console.anthropic.com → API Keys
   - GitHub: https://github.com/settings/tokens

3. **Regenerate Locally**:
   ```bash
   # Create fresh SECRETS.env
   cd /Users/alanredmond/Desktop/SECRETS/
   cat > SECRETS.env << 'EOF'
   # Get these from your account dashboards
   SUPABASE_URL="..."
   SUPABASE_KEY="..."
   # etc.
   EOF
   chmod 600 SECRETS.env  # Restrict permissions
   ```

---

## 📋 Final Rules

| Rule | Consequence |
|------|-----------|
| ✅ Store secrets locally on desktop | Systems can load them securely |
| ❌ Never commit .env files | Prevents key leaks |
| ❌ Never hardcode API keys | GitHub scans will catch and prevent |
| ✅ Use ${VARIABLE} syntax in configs | Allows dynamic secret loading |
| ✅ Use .gitignore for all secret files | Extra protection |
| ✅ Regenerate keys regularly | Security best practice |
| ❌ Don't share SECRETS folder | Obvious but critical |

---

## 🎯 TL;DR

1. **All secrets live at**: `/Users/alanredmond/Desktop/SECRETS/`
2. **Each system loads independently**:
   - Cursor: `.env.local` in project
   - Antigravity: `workspace-secrets.json`
   - Claude Code: `~/.claude/.env.local`
3. **Nothing goes to GitHub**: `.gitignore` blocks it
4. **GitHub protects us**: Secret scanning catches accidents
5. **Never hardcode keys**: Use `${VARIABLE}` syntax

---

## 📞 Questions?

- **"Where do I get SUPABASE_KEY?"** → Supabase dashboard, Settings → API → Service Role
- **"What if my key leaks?"** → Regenerate immediately in Supabase dashboard
- **"Can I commit .env.example?"** → YES! Just without actual values
- **"How often regenerate?"** → Quarterly, or after any security incident

---

**🔒 Secrets management is CRITICAL for security. Follow these rules exactly.**

*Last reviewed: December 15, 2025*
