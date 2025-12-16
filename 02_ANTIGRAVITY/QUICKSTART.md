# Antigravity Quick Start Guide

Get up and running in 10 minutes.

## 1. Prerequisites Check

```bash
# Python 3.9+
python3 --version

# Git (if cloning)
git --version

# GCP account with Vertex AI enabled
# Claude API access
# PostgreSQL database
```

## 2. Installation

```bash
# Navigate to antigravity directory
cd antigravity

# Run automated setup
./setup.sh

# This will:
# - Create virtual environment
# - Install dependencies
# - Create directories
# - Copy .env template
```

## 3. Configuration (5 minutes)

### Edit .env file

```bash
nano .env
```

**Required settings**:

```bash
# GCP
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Claude API
CLAUDE_API_KEY=your-api-key

# CodeRed Database
CODERED_CONNECTION_STRING=postgresql://user:pass@host:5432/db

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
```

### Set GCP credentials

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

## 4. Verify Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Run health check
python3 health-check.py
```

Expected output:
```json
{
  "timestamp": "2025-12-16T10:00:00Z",
  "overall": "healthy",
  "checks": {
    "gcp_connection": {"status": "healthy"},
    "codered_connection": {"status": "healthy"},
    "claude_connection": {"status": "healthy"}
  }
}
```

## 5. Start Sync

```bash
# Start the orchestrator
python3 crew-sync.py
```

You should see:
```
2025-12-16 10:00:00 - INFO - CrewSync Orchestrator initialized
2025-12-16 10:00:00 - INFO - Starting CrewSync orchestrator
2025-12-16 10:00:00 - INFO - Health checks complete: healthy
2025-12-16 10:00:30 - INFO - Starting CrewAI → Antigravity sync
2025-12-16 10:00:31 - INFO - Starting Antigravity → CrewAI sync
2025-12-16 10:00:32 - INFO - Sync cycle 1 completed (0 conflicts resolved)
```

## 6. Monitor

### Real-time logs

```bash
# In another terminal
tail -f logs/crew-sync.log
```

### Check conflicts

```bash
cat conflict-log.jsonl | jq
```

### View metrics

```bash
python3 -c "
from sync_metrics import SyncMetrics
import yaml, asyncio, json

async def main():
    with open('antigravity-config.yaml') as f:
        config = yaml.safe_load(f)
    metrics = SyncMetrics(config)
    report = await metrics.generate_report(window_minutes=60)
    print(json.dumps(report, indent=2))

asyncio.run(main())
"
```

## 7. Common Commands

```bash
# Stop sync (Ctrl+C in running terminal)
^C

# Restart sync
python3 crew-sync.py

# Check health
python3 health-check.py

# View recent logs
tail -n 100 logs/crew-sync.log

# Count conflicts
cat conflict-log.jsonl | wc -l

# Check daily cost
python3 -c "
from supabase_bridge import SupabaseBridge
import yaml, asyncio

async def main():
    with open('antigravity-config.yaml') as f:
        config = yaml.safe_load(f)
    bridge = SupabaseBridge(config)
    cost = await bridge.get_daily_cost()
    print(f'Daily cost: ${cost:.2f}')

asyncio.run(main())
"
```

## 8. Test with Example Task

```bash
# Create a test task in Claude Code Terminal
# The sync engine will automatically:
# 1. Detect the new task
# 2. Map it to the appropriate Antigravity agent
# 3. Start the agent
# 4. Sync results back to CrewAI
# 5. Log all activities
```

## Troubleshooting

### "Failed to connect to GCP"

```bash
# Verify credentials
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### "Failed to connect to CodeRed"

```bash
# Test database connection
psql $CODERED_CONNECTION_STRING -c "SELECT 1"

# Check firewall rules
# Verify credentials in .env
```

### "Failed to connect to Claude"

```bash
# Test API
curl -H "Authorization: Bearer $CLAUDE_API_KEY" \
     https://api.anthropic.com/v1/health

# Verify API key in .env
```

### "Budget exceeded"

```bash
# Check current usage
cat logs/crew-sync.log | grep "Budget status"

# Adjust limits in antigravity-config.yaml
# Or reset (wait until midnight UTC)
```

## Next Steps

1. **Read full README.md** for detailed documentation
2. **Review agent configurations** in antigravity-config.yaml
3. **Customize mappings** in agent-mapping.yaml
4. **Set up monitoring dashboards** using Supabase
5. **Configure alerts** for critical events
6. **Test with real cases** in your environment

## Support

- Full docs: README.md
- Config reference: antigravity-config.yaml
- Mapping reference: agent-mapping.yaml
- GitHub issues: [Create issue](https://github.com/your-repo/issues)

## Key Files Reference

| File | Purpose |
|------|---------|
| `crew-sync.py` | Main orchestrator (start here) |
| `antigravity-config.yaml` | System configuration |
| `agent-mapping.yaml` | Agent/task mappings |
| `.env` | Credentials (never commit!) |
| `conflict-log.jsonl` | Conflict history |
| `logs/crew-sync.log` | Runtime logs |
| `README.md` | Full documentation |

## Production Checklist

Before going to production:

- [ ] All credentials configured
- [ ] Health checks passing
- [ ] Budget limits set appropriately
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Database backups enabled
- [ ] Audit logging enabled
- [ ] Security review completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented

**You're ready to go! The system will now keep Antigravity and CrewAI perfectly in sync.**
