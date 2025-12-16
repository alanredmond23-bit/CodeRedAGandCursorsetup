# MCP Legal Research & Discovery Integration Suite

Comprehensive Model Context Protocol (MCP) integrations for Westlaw, LexisNexis, Gmail, Slack, Supabase, and GitHub. Built for legal research, eDiscovery, and compliance tracking.

## Features

### Legal Research
- **Westlaw Integration**: Case law search, Shepard's Citations, statutory research
- **LexisNexis Integration**: Protégé API for comprehensive legal research
- Advanced citation analysis and treatment tracking
- Secondary source searching (treatises, law reviews)

### eDiscovery
- **Gmail Discovery**: Email search with automatic privilege detection
- **Slack Discovery**: Message archiving with privilege flagging
- Configurable confidence thresholds for privilege detection
- Automatic redaction of privileged content
- Compliance logging for all discovery actions

### Data Management
- **Supabase Integration**: Database operations for cases, documents, and discovery items
- Research query logging and tracking
- Discovery item storage with privilege metadata

### Version Control
- **GitHub Integration**: Repository management, commit history, PR tracking
- Code search across repositories
- Issue creation and tracking

### Supporting Systems
- **Caching**: File-based or Redis caching to reduce API costs
- **Logging**: Comprehensive compliance logging with 7-year retention
- **Cost Tracking**: Per-service cost estimation and daily budget alerts
- **Rate Limiting**: Automatic retry with exponential backoff
- **Graceful Degradation**: Fallback strategies when services fail

## Installation

### Prerequisites
- Python 3.8+
- API credentials for each service (see Setup section)
- Optional: Redis for distributed caching

### Install Dependencies

```bash
pip install -r requirements.txt
```

Create `requirements.txt`:
```
requests>=2.31.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
supabase>=2.0.0
redis>=5.0.0
python-dotenv>=1.0.0
```

## Setup

### 1. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# Westlaw
WESTLAW_API_KEY=your_westlaw_api_key

# LexisNexis
LEXISNEXIS_API_KEY=your_lexisnexis_key
LEXISNEXIS_API_SECRET=your_lexisnexis_secret

# Gmail (download credentials.json from Google Cloud Console)
GMAIL_CREDENTIALS_PATH=credentials.json

# Slack (get from https://api.slack.com/apps)
SLACK_OAUTH_TOKEN=xoxb-your-slack-token

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# GitHub
GITHUB_TOKEN=ghp_your_github_token
```

### 2. Gmail OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download `credentials.json` to this directory
6. First run will open browser for authorization

### 3. Slack OAuth Setup

1. Go to [Slack API](https://api.slack.com/apps)
2. Create new app or select existing
3. Add OAuth scopes:
   - `channels:history`
   - `channels:read`
   - `search:read`
   - `users:read`
4. Install app to workspace
5. Copy OAuth token to `.env`

### 4. Test Connections

Run the connection test suite:
```bash
python test-mcp-connections.py
```

This will validate all integrations and generate `mcp_test_results.json`.

## Usage

### Westlaw Research

```python
from westlaw_mcp_server import create_westlaw_mcp

mcp = create_westlaw_mcp()

# Search cases
results = mcp.search_cases(
    query="attorney-client privilege",
    jurisdiction="federal",
    date_from="2020-01-01",
    limit=25
)

# Get case by citation
case = mcp.get_case_by_citation("410 U.S. 113")

# Shepardize a case
treatment = mcp.shepardize("410 U.S. 113")

# Search statutes
statutes = mcp.search_statutes(
    query="Federal Rules of Evidence 502",
    jurisdiction="US"
)
```

### LexisNexis Research

```python
from lexisnexis_mcp_server import create_lexisnexis_mcp

mcp = create_lexisnexis_mcp()

# Search cases
results = mcp.search_cases(
    query="work product doctrine",
    jurisdiction="federal",
    limit=25
)

# Get document
doc = mcp.get_document("document_id_here")

# Shepardize
treatment = mcp.shepardize("123 F.3d 456")

# Search law reviews
articles = mcp.search_law_reviews("attorney-client privilege")
```

### Gmail Discovery

```python
from gmail_discovery_mcp import create_gmail_discovery_mcp

mcp = create_gmail_discovery_mcp()

# Search emails with privilege detection
results = mcp.search_emails(
    query="contract negotiations",
    date_from="2024/01/01",
    sender="attorney@lawfirm.com",
    max_results=100
)

# Privileged emails are automatically flagged
for email in results['emails']:
    if email['privilege_flagged']:
        print(f"PRIVILEGED: {email['subject']} (confidence: {email['privilege_confidence']})")

# Export for discovery (excludes privileged by default)
export = mcp.export_for_discovery(
    query="project alpha",
    include_privileged=False
)

# Get email thread
thread = mcp.get_thread("thread_id_here")
```

### Slack Discovery

```python
from slack_discovery_mcp import create_slack_discovery_mcp

mcp = create_slack_discovery_mcp()

# Search messages
results = mcp.search_messages(
    query="legal advice",
    count=100
)

# Get channel history
history = mcp.get_channel_history(
    channel_id="C123456",
    oldest="1640995200",  # Unix timestamp
    limit=1000
)

# Export for discovery
export = mcp.export_for_discovery(
    channel_id="C123456",
    date_from="2024-01-01",
    date_to="2024-12-31",
    include_privileged=False
)

# List channels
channels = mcp.list_channels()
```

### Supabase Database

```python
from supabase_mcp_server import create_supabase_mcp

mcp = create_supabase_mcp()

# Query cases
cases = mcp.get_cases(
    status="active",
    assigned_to="attorney@firm.com"
)

# Save discovery item
item = mcp.save_discovery_item(
    item_type="email",
    source="gmail",
    item_id="msg_123",
    content=email_data,
    privileged=True,
    case_id="case_456"
)

# Get discovery items
items = mcp.get_discovery_items(
    case_id="case_456",
    privileged=False  # Non-privileged only
)

# Log research query
mcp.log_research_query(
    service="westlaw",
    query="attorney-client privilege",
    results_count=25,
    user="attorney@firm.com"
)
```

### GitHub Integration

```python
from github_mcp_server import create_github_mcp

mcp = create_github_mcp()

# Get repository info
repo = mcp.get_repository("owner", "repo-name")

# Get commits
commits = mcp.get_commits(
    owner="owner",
    repo="repo-name",
    branch="main",
    limit=50
)

# Get pull requests
prs = mcp.get_pull_requests(
    owner="owner",
    repo="repo-name",
    state="open"
)

# Create issue
issue = mcp.create_issue(
    owner="owner",
    repo="repo-name",
    title="Bug Report",
    body="Description of issue",
    labels=["bug", "priority-high"]
)

# Search code
results = mcp.search_code(
    query="attorney client privilege",
    repo="owner/repo-name",
    language="python"
)
```

## Privilege Detection

All discovery MCPs (Gmail, Slack) include automatic privilege detection:

### Detection Patterns
- Attorney-client communications
- Work product materials
- Legal advice markers
- Confidential legal communications
- Law firm domain detection

### Confidence Scoring
- Pattern matches: +0.15 per match
- Law firm domain: +0.20
- Subject markers: +0.10
- Legal channel: +0.15

### Configuration
Adjust in `mcp-config.json`:
```json
{
  "privilege_detection": {
    "confidence_threshold": 0.30,
    "redact_privileged": true
  }
}
```

## Caching

Reduce API costs with intelligent caching:

### Cache TTL by Service
- Westlaw: 24 hours (case law changes rarely)
- LexisNexis: 24 hours
- Gmail: 1 hour
- Slack: 30 minutes
- Supabase: 5 minutes
- GitHub: 10 minutes

### Enable Redis (Optional)
```bash
# Install Redis
brew install redis  # macOS
# or
apt-get install redis  # Linux

# Start Redis
redis-server

# Enable in .env
USE_REDIS=true
REDIS_URL=redis://localhost:6379
```

## Logging & Compliance

### Log Files
- `logs/api_calls.log` - All API calls with timing
- `logs/auth.log` - Authentication events
- `logs/errors.log` - Errors and failures
- `logs/compliance.log` - Discovery and privilege detection (7-year retention)

### Cost Tracking
```python
from mcp_logging import get_mcp_logger

logger = get_mcp_logger()

# Get cost report
report = logger.get_cost_report()
print(f"Total cost: ${report['total_estimated_cost']}")
print(f"Total calls: {report['total_calls']}")

# Per-service costs
for service, data in report['by_service'].items():
    print(f"{service}: {data['calls']} calls, ${data['estimated_cost']}")

# Compliance summary
compliance = logger.get_compliance_summary(
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

## Rate Limiting

All MCPs implement automatic rate limiting with exponential backoff:

### Retry Strategy
1. First retry: 5 seconds
2. Second retry: 10 seconds
3. Third retry: 20 seconds
4. Max retries: 3

### Service Limits
- Westlaw: 60/min, 5000/day
- LexisNexis: 60/min, 5000/day
- Gmail: 250/min, unlimited/day
- Slack: Tier-based (1-100/min)
- GitHub: 5000/hour
- Supabase: 1000/min

## Graceful Degradation

### Fallback Strategies
- Westlaw fails → Try LexisNexis
- LexisNexis fails → Try Westlaw
- Any service fails → Return cached data (even if stale)
- Partial results on timeout

### Configuration
In `mcp-config.json`:
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

## Security Best Practices

1. **Never commit `.env` file** - Contains API keys
2. **Use service keys** - Not personal credentials
3. **Encrypt cache** - Set `ENCRYPT_CACHE=true` for sensitive data
4. **Rotate tokens** - Regularly update API credentials
5. **Monitor logs** - Review compliance logs regularly
6. **Limit scopes** - Use minimum required OAuth scopes

## Cost Optimization

### Estimated Costs (per 1000 queries)
- Westlaw: $100
- LexisNexis: $80
- Gmail: $0 (free)
- Slack: $0 (free tier)
- Supabase: $1
- GitHub: $0 (authenticated)

### Optimization Tips
1. **Enable caching** - Reduces repeat calls by 60-80%
2. **Use Redis** - Faster cache access
3. **Batch queries** - Combine searches when possible
4. **Filter early** - Use date ranges and jurisdictions
5. **Monitor budget** - Set `DAILY_BUDGET_USD` in config

## Troubleshooting

### Connection Test Failures

**Westlaw/LexisNexis**
- Verify API key is active
- Check account has API access enabled
- Confirm base URL is correct

**Gmail**
- Ensure `credentials.json` exists
- Check OAuth scopes match requirements
- Delete cached token and re-authenticate: `rm cache/tokens.pkl`

**Slack**
- Verify OAuth token starts with `xoxb-`
- Confirm all required scopes are granted
- Check app is installed to workspace

**Supabase**
- Verify project URL and service key
- Check database tables exist
- Ensure service role key (not anon key)

**GitHub**
- Verify token has required permissions
- Check token hasn't expired
- Confirm rate limits not exceeded

### Common Issues

**Rate Limit Errors**
- Wait for rate limit reset
- Enable caching to reduce calls
- Use Redis for distributed caching

**Authentication Failures**
- Check credentials in `.env`
- Verify tokens haven't expired
- Re-run OAuth flow for Gmail/Slack

**Cache Issues**
- Clear cache: `rm -rf cache/*`
- Check disk space
- Verify cache directory permissions

## API Documentation

### Official Documentation
- [Westlaw API](https://developer.thomsonreuters.com/westlaw)
- [LexisNexis API](https://www.lexisnexis.com/api)
- [Gmail API](https://developers.google.com/gmail/api)
- [Slack API](https://api.slack.com/)
- [Supabase Docs](https://supabase.com/docs)
- [GitHub API](https://docs.github.com/en/rest)

## Support

For issues, questions, or feature requests:
1. Check troubleshooting section
2. Review test results: `mcp_test_results.json`
3. Check logs in `logs/` directory
4. Verify configuration in `mcp-config.json`

## License

Proprietary - CodeRed Legal Technology Suite

## Version

1.0.0 - Initial release with full MCP integration suite
