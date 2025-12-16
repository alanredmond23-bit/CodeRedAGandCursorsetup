# MCP Integration Architecture

## System Overview

The MCP (Model Context Protocol) Integration Suite provides a unified interface for legal research and eDiscovery across multiple platforms. It implements proper authentication, caching, logging, and compliance tracking.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Integration Layer                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Westlaw    │  │  LexisNexis  │  │    Gmail     │          │
│  │     MCP      │  │     MCP      │  │ Discovery MCP│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Slack     │  │   Supabase   │  │    GitHub    │          │
│  │ Discovery MCP│  │     MCP      │  │     MCP      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                      Supporting Systems                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     Auth     │  │    Cache     │  │   Logging    │          │
│  │   Handler    │  │    System    │  │   System     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

```
mcps/
├── README.md                      # Main documentation
├── ARCHITECTURE.md                # This file - system architecture
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── quick-start.sh                 # Setup script
│
├── Core Components
│   ├── mcp-auth-handler.py        # Authentication management
│   ├── mcp-cache.py               # Caching system
│   ├── mcp-logging.py             # Compliance logging
│   └── mcp-config.json            # Configuration
│
├── MCP Servers
│   ├── westlaw-mcp-server.py      # Westlaw integration
│   ├── lexisnexis-mcp-server.py   # LexisNexis integration
│   ├── gmail-discovery-mcp.py     # Gmail discovery
│   ├── slack-discovery-mcp.py     # Slack discovery
│   ├── supabase-mcp-server.py     # Supabase database
│   └── github-mcp-server.py       # GitHub integration
│
├── Testing & Examples
│   ├── test-mcp-connections.py    # Connection tests
│   └── example-usage.py           # Usage examples
│
└── Runtime Directories
    ├── logs/                      # Log files
    │   ├── api_calls.log
    │   ├── auth.log
    │   ├── errors.log
    │   └── compliance.log
    │
    └── cache/                     # Cache storage
        └── tokens.pkl             # OAuth tokens
```

## Component Responsibilities

### 1. Authentication Handler (`mcp-auth-handler.py`)
**Purpose**: Centralized authentication for all services

**Features**:
- OAuth2 flow management (Gmail, Slack, LexisNexis)
- API key storage and validation
- Token caching and refresh
- Credential hashing for security

**Key Methods**:
- `get_westlaw_credentials()` - Westlaw API key
- `get_lexisnexis_credentials()` - LexisNexis OAuth
- `get_gmail_credentials()` - Gmail OAuth with scopes
- `get_slack_credentials()` - Slack OAuth token
- `get_supabase_credentials()` - Supabase service key
- `get_github_credentials()` - GitHub personal access token

### 2. Cache System (`mcp-cache.py`)
**Purpose**: Reduce API costs through intelligent caching

**Features**:
- File-based caching (default)
- Optional Redis support for distributed caching
- Per-service TTL configuration
- Cache invalidation strategies
- Statistics tracking

**Cache TTLs**:
- Westlaw: 24 hours (case law is stable)
- LexisNexis: 24 hours
- Gmail: 1 hour (emails change frequently)
- Slack: 30 minutes (active communications)
- Supabase: 5 minutes (database queries)
- GitHub: 10 minutes (repository data)

### 3. Logging System (`mcp-logging.py`)
**Purpose**: Compliance tracking and cost monitoring

**Log Types**:
1. **API Calls** - All API requests with timing
2. **Authentication** - Auth events and failures
3. **Errors** - Detailed error tracking with stack traces
4. **Compliance** - Discovery actions and privilege detection

**Features**:
- Rotating file handlers (10MB max, 10 backups)
- Cost tracking per service
- Privilege detection logging
- Compliance summaries with 7-year retention

### 4. MCP Servers

#### Westlaw MCP (`westlaw-mcp-server.py`)
**Capabilities**:
- Case law search with jurisdictions
- Citation retrieval
- Shepard's Citations analysis
- Statute searching
- Secondary source research

**API Endpoints**:
- `/cases/search` - Search case law
- `/cases/citation/{citation}` - Get case by citation
- `/citator/shepards/{citation}` - Shepardize
- `/statutes/search` - Search statutes
- `/secondary/search` - Search secondary sources

#### LexisNexis MCP (`lexisnexis-mcp-server.py`)
**Capabilities**:
- Case law search
- Document retrieval
- Shepard's analysis
- Statutory research
- Law review searches
- Legal news

**Authentication**: OAuth2 with client credentials

#### Gmail Discovery MCP (`gmail-discovery-mcp.py`)
**Capabilities**:
- Email search with filters
- Thread retrieval
- Privilege detection
- Discovery export
- Compliance logging

**Privilege Detection**:
- Pattern matching (attorney-client, work product, etc.)
- Law firm domain detection
- Subject line analysis
- Configurable confidence thresholds

#### Slack Discovery MCP (`slack-discovery-mcp.py`)
**Capabilities**:
- Message search across channels
- Channel history retrieval
- Privilege detection
- Discovery export
- User information

**Privilege Detection**:
- Pattern matching
- Legal channel detection
- Confidence scoring

#### Supabase MCP (`supabase-mcp-server.py`)
**Capabilities**:
- Table queries with filters
- Record CRUD operations
- Case management
- Document tracking
- Discovery item storage
- Research query logging

**Key Tables**:
- `cases` - Legal case records
- `documents` - Document metadata
- `research_queries` - Query history
- `discovery_items` - Discovery storage

#### GitHub MCP (`github-mcp-server.py`)
**Capabilities**:
- Repository information
- Commit history
- Pull request tracking
- Issue management
- Code search

## Data Flow

### Legal Research Flow
```
1. User Query
   ↓
2. Westlaw MCP → Check Cache
   ↓              ↓
3. API Call → Cache Hit? → Return Cached
   ↓              ↓
4. Parse Results  Cache Miss
   ↓              ↓
5. Store Cache ← API Response
   ↓
6. Log to Supabase
   ↓
7. Return Results
```

### Discovery Flow
```
1. Discovery Request
   ↓
2. Gmail/Slack MCP → Search
   ↓
3. Retrieve Messages
   ↓
4. Privilege Detection
   ↓              ↓
5. Flagged   → Not Flagged
   ↓              ↓
6. Redact      → Include
   ↓              ↓
7. Log Compliance
   ↓
8. Save to Supabase
   ↓
9. Export for Production
```

## Security Architecture

### Authentication Layers
1. **API Keys**: Stored in environment variables
2. **OAuth Tokens**: Cached with refresh capability
3. **Service Keys**: Supabase service role key

### Data Protection
- Sensitive data redaction in logs
- Privileged content automatic redaction
- Optional cache encryption
- Token storage in secure cache

### Compliance
- 7-year log retention
- Privilege detection logging
- Discovery action tracking
- Cost tracking and alerts

## Rate Limiting Strategy

### Implementation
1. Detect rate limit (HTTP 429)
2. Read `Retry-After` header
3. Exponential backoff: 5s → 10s → 20s
4. Max retries: 3
5. Cache stale data on failure

### Service Limits
- **Westlaw**: 60/min, 5000/day
- **LexisNexis**: 60/min, 5000/day
- **Gmail**: 250/min, unlimited/day
- **Slack**: 1-100/min (tier-based)
- **GitHub**: 5000/hour
- **Supabase**: 1000/min

## Graceful Degradation

### Strategies
1. **Service Fallback**: Westlaw ↔ LexisNexis
2. **Stale Cache**: Return old data on API failure
3. **Partial Results**: Return what's available
4. **Error Logging**: Track all failures

### Configuration
Set in `mcp-config.json`:
```json
{
  "graceful_degradation": {
    "enabled": true,
    "fallback_strategies": {
      "westlaw": {
        "fallback_to": "lexisnexis",
        "cache_stale_on_error": true
      }
    }
  }
}
```

## Cost Management

### Cost Tracking
- Per-service call counting
- Estimated costs per API call
- Daily budget monitoring
- Alert thresholds (80% default)

### Cost per 1000 Queries
- Westlaw: $100
- LexisNexis: $80
- Gmail: $0 (free)
- Slack: $0 (free tier)
- Supabase: $1
- GitHub: $0 (authenticated)

### Optimization
1. **Caching**: 60-80% cost reduction
2. **Rate limiting**: Prevent overages
3. **Batch operations**: Combine queries
4. **Budget alerts**: Email notifications

## Extension Points

### Adding New MCP Server
1. Create `{service}-mcp-server.py`
2. Inherit base patterns from existing servers
3. Implement authentication in `mcp-auth-handler.py`
4. Add configuration to `mcp-config.json`
5. Add tests to `test-mcp-connections.py`
6. Update README.md with usage examples

### Custom Privilege Detection
1. Add patterns to `mcp-config.json`
2. Adjust confidence weights
3. Implement custom detection logic
4. Test with real data
5. Monitor false positives/negatives

## Monitoring & Observability

### Logs to Monitor
- `api_calls.log` - Response times, status codes
- `errors.log` - Failures and retries
- `compliance.log` - Privilege detections

### Metrics to Track
- API call volume per service
- Cache hit rates
- Error rates
- Privilege detection accuracy
- Cost vs. budget

### Alerting
- Daily budget exceeded
- High error rates
- Authentication failures
- Rate limit violations

## Integration with Claude/Cursor/Antigravity

### Claude Integration
MCPs provide tool interfaces that Claude can invoke:
```python
# Claude can call:
westlaw.search_cases(query="attorney-client privilege")
gmail.search_emails(query="contract", date_from="2024/01/01")
```

### Cursor Integration
Cursor can use MCPs for context:
- Legal research while coding
- Discovery item retrieval
- Case information lookup

### Antigravity Integration
Antigravity can orchestrate multiple MCPs:
- Cross-platform searches
- Aggregated discovery
- Compliance reporting

## Best Practices

### Development
1. Always check credentials before deployment
2. Test with small result sets first
3. Monitor costs during development
4. Use example queries from documentation

### Production
1. Enable Redis caching
2. Set up monitoring alerts
3. Regular credential rotation
4. Weekly compliance log reviews
5. Monthly cost analysis

### Security
1. Never commit `.env` or `credentials.json`
2. Use service keys, not personal credentials
3. Enable cache encryption for sensitive data
4. Regular security audits of logs
5. Implement IP whitelisting where available

## Troubleshooting Guide

### Authentication Failures
1. Check `.env` credentials
2. Verify token expiration
3. Clear token cache: `rm cache/tokens.pkl`
4. Re-run OAuth flows

### Rate Limit Issues
1. Enable caching
2. Reduce query frequency
3. Use Redis for better caching
4. Implement query batching

### Privilege Detection Issues
1. Review false positives in compliance logs
2. Adjust confidence threshold
3. Add custom patterns
4. Test with known privileged content

### Performance Issues
1. Enable Redis caching
2. Increase cache TTLs for stable data
3. Use filtering to reduce result sets
4. Implement query optimization

## Future Enhancements

### Planned Features
1. Machine learning privilege detection
2. Multi-tenant support
3. Real-time notification system
4. Advanced analytics dashboard
5. Automated report generation

### API Roadmap
1. REST API wrapper for MCPs
2. GraphQL interface
3. WebSocket for real-time updates
4. Mobile SDK

## Support & Resources

### Documentation
- README.md - Getting started
- ARCHITECTURE.md - This file
- mcp-config.json - Configuration reference
- example-usage.py - Code examples

### Testing
- test-mcp-connections.py - Connection validation
- quick-start.sh - Automated setup

### Community
- GitHub Issues - Bug reports
- Documentation PRs - Improvements
- Example contributions - Usage patterns

## Version History

### v1.0.0 (Current)
- Initial release
- Full MCP integration for 6 services
- Privilege detection
- Compliance logging
- Cost tracking
- Caching system

### Roadmap to v2.0.0
- ML-based privilege detection
- Advanced analytics
- Multi-tenant support
- REST API interface
- Real-time notifications
