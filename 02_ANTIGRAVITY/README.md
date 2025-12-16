# Antigravity Cloud Orchestration System

**Production-ready bidirectional sync between Antigravity agents and Claude Code Terminal**

## Overview

The Antigravity Cloud Orchestration System is a comprehensive solution for managing AI-powered legal case workflows using Google Vertex AI (Antigravity) agents that seamlessly synchronize with CrewAI tasks running in Claude Code Terminal.

### Key Features

- **Bidirectional Synchronization**: Automatic sync between Antigravity agents and CrewAI tasks every 30 seconds
- **CrewAI Priority**: All conflicts are resolved with CrewAI as the authoritative source
- **3 Native Agents**: Orchestrator, Researcher, and Executor agents with specialized capabilities
- **Cost Tracking**: Per-agent cost monitoring with budget enforcement
- **Conflict Resolution**: Automatic conflict detection and resolution with full audit trail
- **Health Monitoring**: Real-time health checks with automatic recovery
- **Scalable Architecture**: Handles millions of documents with efficient batching
- **Compliance Ready**: Attorney-client privilege protection and 7-year audit trails

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Terminal (CrewAI)                 │
│                     Source of Truth / Orchestrator               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 30-second sync cycle
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────────┐            ┌──────────────────┐
│  Crew → Antigrav │            │  Antigrav → Crew │
│      Sync        │            │      Sync        │
└────────┬─────────┘            └─────────┬────────┘
         │                                 │
         │                                 │
         ▼                                 ▼
┌─────────────────────────────────────────────────────────┐
│              Conflict Resolver (CrewAI Priority)         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Antigravity Agents (Google Vertex AI)          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Orchestrator │  │ Researcher  │  │  Executor   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ CodeRed  │   │ Supabase │   │   GCS    │
   │    DB    │   │ Logging  │   │ Storage  │
   └──────────┘   └──────────┘   └──────────┘
```

## Components

### Core Sync System

1. **crew-sync.py** - Main orchestrator
   - Coordinates bidirectional sync
   - Manages sync cycles (30-second default)
   - Enforces budget limits
   - Handles errors and recovery

2. **crew-to-antigrav.py** - CrewAI → Antigravity
   - Pulls task updates from Claude
   - Maps to agent parameters
   - Applies updates (CrewAI wins conflicts)

3. **antigrav-to-crew.py** - Antigravity → CrewAI
   - Pulls agent outputs
   - Maps to task results
   - Pushes updates to Claude

4. **conflict-resolver.py** - Conflict Resolution
   - Detects conflicts automatically
   - Applies CrewAI priority policy
   - Logs all conflicts with full diff

### Support Systems

5. **codered-connector.py** - CodeRed Database Bridge
   - Case data synchronization
   - Document management
   - Agent activity logging
   - Cost tracking storage

6. **supabase-bridge.py** - Logging & Vector Store
   - Real-time sync logging
   - Conflict resolution tracking
   - Performance metrics
   - Health check storage
   - Vector search (pgvector)

7. **health-check.py** - System Monitoring
   - GCP connectivity checks
   - Database health monitoring
   - Agent responsiveness
   - Automatic failure detection

8. **sync-metrics.py** - Performance Analytics
   - Sync latency tracking
   - Success/failure rates
   - Conflict frequency
   - Cost per agent
   - Anomaly detection

### Configuration

9. **antigravity-config.yaml** - Main configuration
   - Agent definitions
   - Tool configurations
   - Sync settings
   - Budget controls
   - Security policies

10. **agent-mapping.yaml** - Agent/Task Mapping
    - Input/output mappings
    - Transform functions
    - Sync policies
    - Validation rules

## Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Platform account with Vertex AI enabled
- Claude API access
- PostgreSQL (for CodeRed)
- Supabase account (optional, for logging)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd antigravity

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Configuration

1. **Configure GCP Credentials**

```bash
# Set up service account
gcloud auth application-default login

# Or use service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

2. **Configure Environment Variables**

Edit `.env` file with your actual values:

```bash
# GCP
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Claude API
CLAUDE_API_URL=https://api.anthropic.com/v1
CLAUDE_API_KEY=your-api-key

# CodeRed Database
CODERED_CONNECTION_STRING=postgresql://user:pass@host:5432/db

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
```

3. **Set Up Database Tables**

```bash
# Run database migrations
python scripts/setup_database.py
```

### Running the System

```bash
# Start the sync orchestrator
python crew-sync.py

# The system will:
# 1. Initialize all connections
# 2. Run health checks
# 3. Start sync loop (every 30 seconds)
# 4. Monitor costs and enforce budgets
# 5. Resolve conflicts automatically
# 6. Log all activities
```

### Monitoring

```bash
# View real-time logs
tail -f logs/crew-sync.log

# Check conflict log
cat conflict-log.jsonl | jq

# View metrics
python -c "
from sync_metrics import SyncMetrics
import yaml
import asyncio
import json

async def main():
    with open('antigravity-config.yaml') as f:
        config = yaml.safe_load(f)

    metrics = SyncMetrics(config)
    report = await metrics.generate_report(window_minutes=60)
    print(json.dumps(report, indent=2))

asyncio.run(main())
"
```

## Agents

### 1. Orchestrator Agent

**Purpose**: Master coordinator for all case management activities

**Capabilities**:
- Task delegation
- Priority management
- Resource allocation
- Workflow coordination
- Progress tracking

**Configuration**:
```yaml
orchestrator:
  model: gemini-pro
  temperature: 0.5
  max_iterations: 50
  budget_per_day: $30.00
```

**Typical Tasks**:
- Coordinate multi-agent workflows
- Manage case priorities
- Allocate resources
- Monitor progress
- Handle escalations

### 2. Researcher Agent

**Purpose**: Deep document analysis and legal research

**Capabilities**:
- Document analysis
- Case law research
- Evidence extraction
- Precedent identification
- Citation verification

**Tools**:
- Google Search API
- Document loader (PDF, DOCX, etc.)
- Web scraper
- PDF analyzer with OCR
- Vector search

**Configuration**:
```yaml
researcher:
  model: gemini-pro
  temperature: 0.3  # Lower for factual accuracy
  max_iterations: 100
  budget_per_day: $40.00
```

**Typical Tasks**:
- Analyze legal documents
- Research case precedents
- Extract evidence
- Verify citations
- Correlate facts

### 3. Executor Agent

**Purpose**: Action implementation and document generation

**Capabilities**:
- Document generation
- Template application
- Data formatting
- File organization
- Status updates

**Tools**:
- Document generator
- Template engine (Jinja2)
- File manager (GCS)
- Email notifier
- Calendar integration

**Configuration**:
```yaml
executor:
  model: gemini-pro
  temperature: 0.6
  max_iterations: 30
  budget_per_day: $30.00
```

**Typical Tasks**:
- Generate legal documents
- Apply templates
- Format outputs
- Organize files
- Send notifications

## Synchronization Flow

### CrewAI → Antigravity (Commands Flow Down)

1. **Poll Claude Code Terminal** for task updates every 30 seconds
2. **Extract task assignments** and parameters
3. **Map to agent format** using agent-mapping.yaml
4. **Apply updates to agents** (CrewAI values override Antigravity)
5. **Verify updates applied** successfully

**Example**:
```python
# CrewAI creates a high-priority research task
crew_task = {
    'task_id': 'research_001',
    'priority': 'high',
    'query': 'Find precedents for employment discrimination',
    'depth': 'deep'
}

# Sync engine maps to Antigravity researcher agent
antigrav_params = {
    'priority': 'high',
    'query': 'Find precedents for employment discrimination',
    'max_iterations': 100  # Mapped from 'deep'
}

# Updates applied to agent - CrewAI is authoritative
```

### Antigravity → CrewAI (Results Flow Up)

1. **Poll agent states** every 30 seconds
2. **Extract outputs and status**
3. **Map to CrewAI format** using agent-mapping.yaml
4. **Push updates to Claude**
5. **Track costs** per agent

**Example**:
```python
# Antigravity researcher completes analysis
agent_output = {
    'status': 'completed',
    'findings': [...],
    'citations': [...],
    'confidence': 0.92
}

# Sync engine maps to CrewAI task result
crew_result = {
    'task_id': 'research_001',
    'status': 'completed',
    'result': {
        'findings': [...],
        'citations': [...],
        'confidence': 0.92
    }
}

# Results pushed to Claude Code Terminal
```

## Conflict Resolution

### Resolution Policy

**Core Principle**: CrewAI is the source of truth. All CrewAI decisions override Antigravity state.

### Conflict Types

1. **Status Mismatch**: Different task/agent status
   - **Resolution**: Use CrewAI status
   - **Action**: Update Antigravity agent

2. **Parameter Mismatch**: Different configuration values
   - **Resolution**: Use CrewAI parameters
   - **Action**: Reconfigure Antigravity agent

3. **Priority Mismatch**: Different priority levels
   - **Resolution**: Use CrewAI priority
   - **Action**: Re-prioritize agent tasks

4. **Output Mismatch**: Divergent outputs (rare)
   - **Resolution**: Use latest timestamp OR CrewAI
   - **Action**: Reconcile outputs

5. **Data Divergence**: Fundamental data differences
   - **Resolution**: Use CrewAI data
   - **Action**: Resync Antigravity state

### Conflict Logging

All conflicts are logged to `conflict-log.jsonl`:

```json
{
  "conflict_id": "a1b2c3d4e5f6g7h8",
  "conflict_type": "status_mismatch",
  "agent_id": "orchestrator",
  "task_id": "coordination_task",
  "field_name": "status",
  "crew_value": "running",
  "antigrav_value": "idle",
  "resolution_strategy": "crew_wins",
  "resolved_value": "running",
  "timestamp": "2025-12-16T10:15:30.123456Z",
  "diff": {
    "crew": "running",
    "antigrav": "idle"
  },
  "metadata": {
    "resolution_time_ms": 45,
    "sync_cycle": 127
  }
}
```

## Cost Tracking

### Budget Controls

```yaml
budget:
  daily_limit_usd: 100.00
  monthly_limit_usd: 2500.00
  alert_threshold_percent: 80
  hard_stop_enabled: true
```

### Per-Agent Budgets

```yaml
orchestrator:
  cost_tracking:
    enabled: true
    budget_per_day: 30.00
    alert_threshold: 25.00

researcher:
  cost_tracking:
    enabled: true
    budget_per_day: 40.00
    alert_threshold: 35.00

executor:
  cost_tracking:
    enabled: true
    budget_per_day: 30.00
    alert_threshold: 25.00
```

### Cost Calculation

Costs are calculated based on:
- Token usage (input + output)
- Model pricing (Gemini Pro: ~$0.00025/1K tokens)
- API calls
- Storage operations

### Budget Enforcement

1. **Soft Limit** (80%): Send alert
2. **Hard Limit** (100%): Pause sync, require approval
3. **Daily Reset**: Budget resets at midnight UTC
4. **Monthly Tracking**: Cumulative monthly spend

## Health Checks

### Monitored Components

1. **GCP/Vertex AI**: API connectivity and authentication
2. **CodeRed Database**: Connection and query performance
3. **Supabase**: API availability and response time
4. **Claude API**: Endpoint health and rate limits
5. **Agent Health**: Responsiveness and error rates

### Health Check Schedule

- **Interval**: Every 60 seconds
- **Timeout**: 10 seconds per check
- **Retry**: 3 attempts on failure

### Health Status Levels

- **Healthy**: All systems operational
- **Degraded**: Non-critical issues detected
- **Critical**: Critical component failure

### Automatic Recovery

When health checks fail:

1. **Log failure** to Supabase
2. **Send alert** to configured channels
3. **Attempt recovery** (up to 3 times)
4. **Pause sync** if recovery fails
5. **Resume** when health restored

## Security & Compliance

### Attorney-Client Privilege

```yaml
security:
  privilege_separation:
    enabled: true
    validate_permissions: true
    log_access: true

  compliance:
    attorney_client_privilege: true
    work_product_doctrine: true
    chain_of_custody: true
    audit_trail: true
```

### Data Protection

- **Encryption at Rest**: All stored data encrypted
- **Encryption in Transit**: TLS 1.3 for all connections
- **PII Masking**: Automatic masking of sensitive data
- **Secure Deletion**: Cryptographic deletion of expired data

### Audit Trail

All actions logged for 7 years:
- Agent activities
- Sync operations
- Conflicts and resolutions
- Cost tracking
- Health checks
- Access logs

## Performance Optimization

### Caching

```yaml
performance:
  cache:
    enabled: true
    backend: redis
    ttl: 3600  # 1 hour
```

### Batching

```yaml
performance:
  batching:
    enabled: true
    batch_size: 100
    max_wait: 5  # seconds
```

### Parallel Processing

```yaml
performance:
  parallel:
    enabled: true
    max_workers: 10
    pool_type: thread
```

## Troubleshooting

### Sync Not Working

1. **Check health status**:
   ```bash
   python health-check.py
   ```

2. **View logs**:
   ```bash
   tail -f logs/crew-sync.log
   ```

3. **Verify credentials**:
   ```bash
   # Test GCP connection
   gcloud auth application-default login

   # Test Claude API
   curl -H "Authorization: Bearer $CLAUDE_API_KEY" \
        $CLAUDE_API_URL/health
   ```

### High Conflict Rate

1. **Check conflict log**:
   ```bash
   cat conflict-log.jsonl | jq '.conflict_type' | sort | uniq -c
   ```

2. **Review mapping configuration** in `agent-mapping.yaml`

3. **Adjust sync interval** if conflicts are timing-related

### Budget Exceeded

1. **Check cost breakdown**:
   ```python
   from supabase_bridge import SupabaseBridge
   # Query cost tracking table
   ```

2. **Optimize agent parameters**:
   - Reduce max_iterations
   - Lower temperature
   - Use smaller models for simple tasks

3. **Implement caching** to reduce API calls

### Agent Not Responding

1. **Check agent health**:
   ```bash
   python health-check.py
   ```

2. **Review agent logs** in GCP Console

3. **Restart agent** if necessary

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Load tests
pytest tests/load/
```

### Adding a New Agent

1. **Define agent in antigravity-config.yaml**:
   ```yaml
   agents:
     my_new_agent:
       name: "My New Agent"
       role: "Specialist"
       goal: "Do specialized work"
       config: {...}
   ```

2. **Add mapping in agent-mapping.yaml**:
   ```yaml
   mappings:
     my_new_agent:
       antigravity: {...}
       crewai: {...}
       input_mapping: {...}
       output_mapping: {...}
   ```

3. **Update sync engines** to handle new agent

4. **Test thoroughly** before production

## FAQ

### Q: How often does sync occur?

**A**: Every 30 seconds by default. Configurable via `system.sync_interval`.

### Q: What happens if CrewAI and Antigravity disagree?

**A**: CrewAI always wins. Conflicts are logged and Antigravity is updated.

### Q: Can I run multiple sync processes?

**A**: Not recommended. Use a single orchestrator process. For high availability, use leader election.

### Q: How are costs calculated?

**A**: Based on token usage, model pricing, and API calls. Tracked per-agent with daily budgets.

### Q: Is data encrypted?

**A**: Yes. Encryption at rest and in transit. All sensitive data is protected.

### Q: What's the retention period?

**A**: 7 years (2555 days) for legal compliance. Configurable.

### Q: Can I customize conflict resolution?

**A**: Yes. Edit policies in `antigravity-config.yaml` under `conflict_resolution`.

### Q: How do I monitor system health?

**A**: Health checks run every 60 seconds. View logs in Supabase or use `health-check.py`.

## Support

For issues, questions, or contributions:

- **GitHub Issues**: [Create an issue](https://github.com/your-repo/issues)
- **Documentation**: [Full docs](https://docs.example.com)
- **Email**: support@example.com

## License

Proprietary - All Rights Reserved

## Changelog

### Version 1.0.0 (2025-12-16)

- Initial release
- Bidirectional sync with CrewAI
- 3 native agents (Orchestrator, Researcher, Executor)
- Conflict resolution with CrewAI priority
- Cost tracking and budget enforcement
- Health monitoring and auto-recovery
- Comprehensive logging and audit trails
- Production-ready configuration

---

**Built with precision for legal case management workflows.**
