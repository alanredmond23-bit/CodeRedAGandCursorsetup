# Antigravity System Architecture

Comprehensive technical architecture documentation.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE TERMINAL                             │
│                     (CrewAI - Source of Truth)                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ CrewAI Orchestration                                                │ │
│  │ - Task Management                                                   │ │
│  │ - Agent Coordination                                                │ │
│  │ - Decision Making                                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ REST API
                                │ (30-second sync)
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                        SYNC ORCHESTRATOR                                 │
│                         (crew-sync.py)                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │  Health Check    │  │  Budget Control  │  │  Metrics         │     │
│  │  (60s interval)  │  │  (Real-time)     │  │  (30s collect)   │     │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘     │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               BIDIRECTIONAL SYNC ENGINE                           │  │
│  │                                                                    │  │
│  │  ┌─────────────────────┐      ┌─────────────────────┐            │  │
│  │  │ Crew → Antigrav     │      │ Antigrav → Crew     │            │  │
│  │  │ (Commands Down)     │      │ (Results Up)        │            │  │
│  │  │                     │      │                     │            │  │
│  │  │ 1. Poll Claude      │      │ 1. Poll Agents      │            │  │
│  │  │ 2. Extract Tasks    │      │ 2. Extract Outputs  │            │  │
│  │  │ 3. Map to Agents    │      │ 3. Map to Tasks     │            │  │
│  │  │ 4. Update Agents    │      │ 4. Update Claude    │            │  │
│  │  └─────────────────────┘      └─────────────────────┘            │  │
│  │                                                                    │  │
│  │                    ┌──────────────────────┐                       │  │
│  │                    │  Conflict Resolver   │                       │  │
│  │                    │  (CrewAI Priority)   │                       │  │
│  │                    │                      │                       │  │
│  │                    │  - Detect conflicts  │                       │  │
│  │                    │  - Apply CrewAI wins │                       │  │
│  │                    │  - Log all diffs     │                       │  │
│  │                    └──────────────────────┘                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Agent Mapping   │ │   CodeRed    │ │  Supabase    │
    │  (YAML Config)   │ │   Bridge     │ │   Bridge     │
    └──────────────────┘ └──────────────┘ └──────────────┘
                                │               │
                                ▼               ▼
                        ┌──────────────┐ ┌──────────────┐
                        │  PostgreSQL  │ │  Logging +   │
                        │  (Cases DB)  │ │  Vectors     │
                        └──────────────┘ └──────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      GOOGLE VERTEX AI / ANTIGRAVITY                       │
│                                                                           │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │   ORCHESTRATOR      │  │     RESEARCHER      │  │    EXECUTOR     │ │
│  │                     │  │                     │  │                 │ │
│  │ Role: Coordinator   │  │ Role: Analyst       │  │ Role: Impl.     │ │
│  │ Model: Gemini Pro   │  │ Model: Gemini Pro   │  │ Model: Gemini   │ │
│  │ Budget: $30/day     │  │ Budget: $40/day     │  │ Budget: $30/day │ │
│  │                     │  │                     │  │                 │ │
│  │ Capabilities:       │  │ Capabilities:       │  │ Capabilities:   │ │
│  │ - Task delegation   │  │ - Doc analysis      │  │ - Doc gen       │ │
│  │ - Priority mgmt     │  │ - Case research     │  │ - Templates     │ │
│  │ - Resource alloc    │  │ - Evidence extract  │  │ - File org      │ │
│  │ - Progress track    │  │ - Citation verify   │  │ - Notifications │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         SHARED TOOLS                              │   │
│  │                                                                    │   │
│  │  Google Search | Doc Loader | Web Scraper | PDF Analyzer |       │   │
│  │  Vector Search | Template Engine | File Manager | Email |        │   │
│  │  Calendar Integration | Cost Tracking                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Command Flow (CrewAI → Antigravity)

```
CrewAI Task Created
       │
       ├─→ Stored in Claude State
       │
       ▼
Sync Cycle (30s)
       │
       ├─→ crew-to-antigrav.py polls Claude API
       │
       ├─→ Extracts task data:
       │   - task_id
       │   - parameters
       │   - priority
       │   - context
       │
       ├─→ Maps using agent-mapping.yaml:
       │   - input_mapping rules
       │   - transform functions
       │   - validation rules
       │
       ├─→ Converts to Antigravity format:
       │   - agent_id
       │   - agent_params
       │   - workflow_config
       │
       ├─→ Pushes to Antigravity agent
       │
       ├─→ Logs to CodeRed database
       │
       └─→ Logs to Supabase
```

### 2. Result Flow (Antigravity → CrewAI)

```
Agent Produces Output
       │
       ├─→ Stored in Agent State
       │
       ▼
Sync Cycle (30s)
       │
       ├─→ antigrav-to-crew.py queries agent state
       │
       ├─→ Extracts output data:
       │   - agent_output
       │   - status
       │   - metrics (tokens, cost)
       │   - errors
       │
       ├─→ Maps using agent-mapping.yaml:
       │   - output_mapping rules
       │   - result formatting
       │   - validation
       │
       ├─→ Converts to CrewAI format:
       │   - task_result
       │   - status update
       │   - metadata
       │
       ├─→ Pushes to Claude API
       │
       ├─→ Tracks costs
       │
       └─→ Logs metrics
```

### 3. Conflict Resolution Flow

```
Sync Cycle Completes
       │
       ├─→ Both directions synced
       │
       ▼
Conflict Detection
       │
       ├─→ Compare CrewAI state vs Antigravity state
       │
       ├─→ Detect mismatches:
       │   - Status differences
       │   - Parameter differences
       │   - Priority differences
       │   - Output divergence
       │
       ▼
Conflict Resolution
       │
       ├─→ Apply resolution strategy:
       │   - crew_wins (default)
       │   - antigrav_wins
       │   - merge
       │   - latest
       │
       ├─→ CrewAI value selected (priority)
       │
       ├─→ Update Antigravity with CrewAI value
       │
       ├─→ Log conflict with full diff:
       │   - conflict_id
       │   - conflict_type
       │   - crew_value
       │   - antigrav_value
       │   - resolved_value
       │   - diff
       │
       └─→ Store in conflict-log.jsonl
```

## Component Architecture

### Sync Orchestrator (crew-sync.py)

**Responsibilities**:
- Main event loop (30-second cycles)
- Health check coordination
- Budget enforcement
- Error handling and recovery
- State persistence

**Key Methods**:
```python
async def run():
    """Main sync loop"""
    while status == "running":
        - Perform health checks
        - Check budget
        - Sync CrewAI → Antigravity
        - Sync Antigravity → CrewAI
        - Resolve conflicts
        - Update costs
        - Log metrics
        - Persist state
        - Wait for next cycle
```

### CrewAI → Antigravity Sync (crew-to-antigrav.py)

**Responsibilities**:
- Poll Claude Code Terminal API
- Extract task updates
- Map to agent parameters
- Apply updates to agents

**Key Methods**:
```python
async def sync():
    """Pull from CrewAI, push to Antigravity"""
    - Get updates from Claude since last sync
    - For each task:
        - Map task to agent
        - Extract parameters
        - Transform using mapping rules
        - Update agent configuration
        - Verify update applied
    - Return results
```

### Antigravity → CrewAI Sync (antigrav-to-crew.py)

**Responsibilities**:
- Query agent states
- Extract outputs and status
- Map to CrewAI format
- Push updates to Claude

**Key Methods**:
```python
async def sync():
    """Pull from Antigravity, push to CrewAI"""
    - For each agent:
        - Get agent state
        - Extract outputs
        - Map to CrewAI format
        - Push to Claude API
        - Track costs
    - Return results
```

### Conflict Resolver (conflict-resolver.py)

**Responsibilities**:
- Detect conflicts between states
- Apply resolution policies
- Log all conflicts with diffs
- Apply resolved values

**Key Methods**:
```python
async def resolve(crew_results, antigrav_results):
    """Resolve conflicts with CrewAI priority"""
    - Detect conflicts:
        - Status mismatches
        - Parameter mismatches
        - Priority mismatches
        - Output divergence
    - Apply resolution strategy
    - Log conflicts
    - Apply resolved values
    - Return conflict list
```

### CodeRed Connector (codered-connector.py)

**Responsibilities**:
- Database operations
- Case data sync
- Activity logging
- Cost tracking

**Key Methods**:
```python
async def log_sync(direction, results):
    """Log sync operation to database"""

async def log_agent_activity(agent_id, activity, details):
    """Log agent activity"""

async def log_cost(agent_id, cost, tokens, details):
    """Log cost tracking"""
```

### Supabase Bridge (supabase-bridge.py)

**Responsibilities**:
- Real-time logging
- Metrics collection
- Conflict logging
- Health check storage
- Vector search

**Key Methods**:
```python
async def log_sync(sync_data):
    """Log sync to Supabase"""

async def log_conflict(conflict):
    """Log conflict with full diff"""

async def log_costs(cost_data):
    """Log cost tracking"""

async def log_health_check(health_data):
    """Log health check results"""
```

### Health Check (health-check.py)

**Responsibilities**:
- Monitor all dependencies
- Detect failures
- Trigger alerts
- Support recovery

**Key Methods**:
```python
async def check_all():
    """Run all health checks"""
    - Check GCP connectivity
    - Check CodeRed database
    - Check Supabase
    - Check Claude API
    - Check agent health
    - Return overall status
```

### Sync Metrics (sync-metrics.py)

**Responsibilities**:
- Collect performance metrics
- Calculate aggregates
- Detect anomalies
- Generate reports

**Key Methods**:
```python
async def log(metrics):
    """Log metrics data point"""

async def get_sync_latency(window_minutes):
    """Get latency statistics"""

async def detect_anomalies():
    """Detect performance anomalies"""

async def generate_report(window_minutes):
    """Generate comprehensive report"""
```

## Configuration Architecture

### antigravity-config.yaml Structure

```yaml
version: "1.0"
system: {...}         # System-wide settings
gcp: {...}            # Google Cloud config
agents: {...}         # Agent definitions
tools: {...}          # Tool configurations
crew_bridge: {...}    # Sync configuration
codered: {...}        # Database config
supabase: {...}       # Logging config
monitoring: {...}     # Health & metrics
conflict_resolution: {...}  # Conflict policies
logging: {...}        # Logging config
security: {...}       # Security settings
recovery: {...}       # Recovery config
performance: {...}    # Performance tuning
```

### agent-mapping.yaml Structure

```yaml
mappings:
  orchestrator:
    antigravity: {...}
    crewai: {...}
    input_mapping: {...}   # CrewAI → Antigravity
    output_mapping: {...}  # Antigravity → CrewAI
    sync: {...}

  researcher:
    # ... same structure

  executor:
    # ... same structure

transforms: {...}      # Transform functions
status_sync: {...}     # Status field mappings
cost_sync: {...}       # Cost tracking
error_handling: {...}  # Error policies
validation: {...}      # Validation rules
```

## Security Architecture

### Authentication Flow

```
Client Request
    │
    ├─→ GCP Service Account
    │   - JSON key file
    │   - IAM permissions
    │   - Vertex AI access
    │
    ├─→ Claude API
    │   - Bearer token
    │   - API key rotation
    │   - Rate limiting
    │
    ├─→ CodeRed Database
    │   - PostgreSQL credentials
    │   - SSL/TLS connection
    │   - Connection pooling
    │
    └─→ Supabase
        - API key authentication
        - Row-level security
        - JWT tokens
```

### Data Protection

```
Data at Rest:
    │
    ├─→ GCS: Server-side encryption (AES-256)
    ├─→ CodeRed: PostgreSQL encryption
    ├─→ Supabase: AES-256 encryption
    └─→ Logs: Encrypted file system

Data in Transit:
    │
    ├─→ All API calls: TLS 1.3
    ├─→ Database connections: SSL
    └─→ Internal comms: Encrypted
```

### Attorney-Client Privilege

```
Privilege Protection:
    │
    ├─→ Access Control
    │   - Role-based permissions
    │   - Need-to-know basis
    │   - Audit all access
    │
    ├─→ Data Handling
    │   - Privilege flags on data
    │   - Separate storage
    │   - No cross-contamination
    │
    └─→ Compliance
        - 7-year retention
        - Secure deletion
        - Chain of custody
        - Audit trail
```

## Scalability Architecture

### Horizontal Scaling

```
Single Instance (Default):
    crew-sync.py → Handles up to 10 agents

Multiple Instances (High Availability):
    Load Balancer
        │
        ├─→ Instance 1 (Primary)
        │   - Leader election
        │   - Active sync
        │
        └─→ Instance 2 (Standby)
            - Monitoring only
            - Takes over on failure
```

### Vertical Scaling

```
Resource Limits:
    │
    ├─→ CPU: 80% max utilization
    ├─→ Memory: 8GB max
    ├─→ Connections: 10 max concurrent
    └─→ Batch Size: 100 records
```

### Performance Optimization

```
Caching Layer (Redis):
    │
    ├─→ Agent states (TTL: 1 hour)
    ├─→ Task results (TTL: 1 hour)
    └─→ Transform results (TTL: 1 hour)

Batching:
    │
    ├─→ Batch size: 100 records
    ├─→ Max wait: 5 seconds
    └─→ Parallel processing: 10 workers
```

## Disaster Recovery

### Backup Strategy

```
Automated Backups:
    │
    ├─→ CodeRed Database
    │   - Daily full backup
    │   - Point-in-time recovery
    │   - 30-day retention
    │
    ├─→ Supabase
    │   - Continuous backup
    │   - Daily snapshots
    │   - 90-day retention
    │
    ├─→ Configuration
    │   - Git version control
    │   - Daily exports
    │
    └─→ Logs
        - Archived to GCS
        - 7-year retention
```

### Recovery Procedures

```
Component Failure:
    │
    ├─→ Detection (health check)
    ├─→ Alert administrators
    ├─→ Attempt auto-recovery (3 times)
    ├─→ Pause sync if recovery fails
    └─→ Manual intervention required

Data Loss:
    │
    ├─→ Detect missing data
    ├─→ Stop all operations
    ├─→ Restore from backup
    ├─→ Verify data integrity
    ├─→ Resume operations
    └─→ Audit recovery process
```

## Monitoring & Observability

### Metrics Collection

```
Real-time Metrics (30s interval):
    │
    ├─→ Sync latency
    ├─→ Success rate
    ├─→ Conflict rate
    ├─→ Agent utilization
    ├─→ Cost per agent
    ├─→ Error rate
    └─→ Throughput

Aggregated Metrics:
    │
    ├─→ P50, P95, P99 latency
    ├─→ Daily cost totals
    ├─→ Weekly conflict trends
    └─→ Monthly performance reports
```

### Alerting

```
Alert Conditions:
    │
    ├─→ Sync failure rate > 10%
    ├─→ Cost burn rate > 90%
    ├─→ Health check critical failure
    ├─→ Conflict rate > 10%
    └─→ Error rate > 5%

Alert Channels:
    │
    ├─→ Email (admin@example.com)
    ├─→ Webhook (Slack, PagerDuty)
    └─→ SMS (critical only)
```

## Cost Optimization

### Budget Control Flow

```
Cost Tracking:
    │
    ├─→ Per-agent tracking
    │   - Orchestrator: $30/day
    │   - Researcher: $40/day
    │   - Executor: $30/day
    │
    ├─→ Real-time monitoring
    │
    ├─→ Alert at 80% threshold
    │
    └─→ Hard stop at 100%

Cost Calculation:
    │
    ├─→ Token usage × model pricing
    ├─→ API calls × call cost
    ├─→ Storage × storage cost
    └─→ Total daily/monthly cost
```

### Optimization Strategies

```
Reduce Costs:
    │
    ├─→ Implement caching
    ├─→ Use batch operations
    ├─→ Optimize agent parameters
    ├─→ Use smaller models when possible
    └─→ Schedule heavy tasks off-peak
```

---

**This architecture supports millions of documents, ensures data consistency, and maintains attorney-client privilege while keeping costs under control.**
