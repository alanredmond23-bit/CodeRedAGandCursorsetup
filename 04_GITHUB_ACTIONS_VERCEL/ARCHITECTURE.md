# Discovery Pipeline Architecture

## System Overview

The Discovery Pipeline is an automated legal discovery document processing system built on GitHub Actions and Vercel, designed to handle large-scale document processing with AI-powered analysis, privilege detection, and cost tracking.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │ discovery-docs │  │   case-files   │  │   .github/       │  │
│  │   (PDFs/DOCX)  │  │  (Documents)   │  │   workflows/     │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions Workflows                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Discovery Pipeline (discovery-pipeline.yml)          │  │
│  │     • Document validation                                 │  │
│  │     • Privilege screening                                 │  │
│  │     • Parallel batch processing                           │  │
│  │     • Cost calculation                                    │  │
│  │     • Supabase ingestion                                  │  │
│  │     • Dashboard deployment                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  2. Privilege Check (privilege-check.yml)                │  │
│  │     • Keyword analysis                                    │  │
│  │     • Pattern matching                                    │  │
│  │     • Dual AI validation (OpenAI + Anthropic)            │  │
│  │     • Confidence scoring                                  │  │
│  │     • Legal team notification                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  3. Cost Tracking (cost-tracking.yml)                    │  │
│  │     • Scheduled cost calculation (every 6 hours)         │  │
│  │     • Budget threshold monitoring                         │  │
│  │     • Cost optimization recommendations                   │  │
│  │     • Slack/Email alerts                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  4. Supabase Ingestion (supabase-ingest.yml)            │  │
│  │     • Document chunking                                   │  │
│  │     • Parallel embedding generation                       │  │
│  │     • Vector store ingestion                              │  │
│  │     • Index optimization                                  │  │
│  │     • Verification tests                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  5. Daily Reports (generate-reports.yml)                 │  │
│  │     • Case summaries (AI-generated)                       │  │
│  │     • Privilege reports                                   │  │
│  │     • Cost analysis                                       │  │
│  │     • Email/Slack distribution                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────┬───────────────────┬──────────────────┬──────────┘
                │                   │                  │
                ▼                   ▼                  ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   OpenAI API         │  │  Anthropic API   │  │  Supabase        │
│   ---------------    │  │  --------------   │  │  --------        │
│   • GPT-4 Turbo      │  │  • Claude 3.5    │  │  • PostgreSQL    │
│   • Embeddings       │  │    Sonnet        │  │  • pgvector      │
│   • Token tracking   │  │  • Streaming     │  │  • Storage       │
└──────────────────────┘  └──────────────────┘  │  • Edge Functions│
                                                 └──────────────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │  Vector Database │
                                                 │  ---------------  │
                                                 │  • Document store │
                                                 │  • Embeddings     │
                                                 │  • Metadata       │
                                                 │  • Search index   │
                                                 └──────────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Vercel Dashboard                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Real-time processing stats                              │ │
│  │  • Privilege alerts                                        │ │
│  │  • Cost breakdown charts                                   │ │
│  │  • Document listings                                       │ │
│  │  • Search interface                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Document Upload Flow

```
Developer commits documents → GitHub Actions triggered → Validation
                                                             │
                                                             ▼
                                                    Manifest generated
                                                             │
                                                             ▼
                                                    Privilege detection
                                                             │
                                                      ┌──────┴──────┐
                                                      ▼             ▼
                                              Privileged       Non-privileged
                                                   │                │
                                                   ▼                ▼
                                          Legal review      Process in batches
                                                                    │
                                                                    ▼
                                                            AI analysis
                                                                    │
                                                                    ▼
                                                            Generate embeddings
                                                                    │
                                                                    ▼
                                                            Ingest to Supabase
                                                                    │
                                                                    ▼
                                                            Deploy dashboard
```

### 2. Privilege Detection Flow

```
Document text → Keyword analysis (weighted scoring)
                        │
                        ▼
                Pattern matching (email headers, law firms)
                        │
                        ▼
                AI analysis (dual providers)
                        │
                ┌───────┴───────┐
                ▼               ▼
            OpenAI         Anthropic
            GPT-4          Claude 3.5
                │               │
                └───────┬───────┘
                        ▼
                Confidence aggregation
                        │
                ┌───────┴───────┐
                ▼               ▼
        High confidence    Low confidence
        (>0.8)            (<0.8)
                │               │
                ▼               ▼
        Block pipeline    Allow with warning
```

### 3. Cost Tracking Flow

```
Document processed → Track tokens used → Calculate costs
                                               │
                                               ▼
                                    Store in Supabase
                                               │
                                        ┌──────┴──────┐
                                        ▼             ▼
                                  Daily total   Monthly total
                                        │             │
                                        ▼             ▼
                                  Compare to    Compare to
                                    budget        budget
                                        │             │
                                        └──────┬──────┘
                                               │
                                        ┌──────┴──────┐
                                        ▼             ▼
                                  Under budget  Over budget
                                               │
                                               ▼
                                        Send alerts
                                        (Slack/Email)
```

## Component Details

### GitHub Actions Workflows

**discovery-pipeline.yml**
- Entry point for all document processing
- Orchestrates all other workflows
- Runs on push to `discovery-docs/` or manual dispatch
- Jobs run in parallel where possible for speed
- Includes automatic retries and error handling

**privilege-check.yml**
- Specialized workflow for privilege detection
- Uses multiple detection methods for accuracy
- Configurable sensitivity levels
- Blocks pipeline if high-risk documents detected
- Generates Fed. R. Civ. P. 26(b)(5) compliant logs

**cost-tracking.yml**
- Scheduled to run every 6 hours
- Monitors daily/weekly/monthly budgets
- Sends alerts at 80% threshold
- Provides cost optimization recommendations
- Tracks historical costs for trend analysis

**supabase-ingest.yml**
- Handles vector database ingestion
- Generates embeddings in parallel batches
- Creates optimized indexes
- Verifies ingestion success
- Updates metadata with AI enrichment

**generate-reports.yml**
- Runs daily at 8 AM UTC
- Generates comprehensive reports
- Uses AI for case summaries
- Distributes via email/Slack
- Archives reports in repository

### Core Scripts

**discovery-processor.js**
- Multi-format document processing (PDF, DOCX, TXT)
- OCR fallback for scanned documents
- AI-powered document analysis
- Metadata extraction
- Cost calculation per document
- Exponential backoff retry logic

**privilege-detector.js**
- Three-stage privilege detection
- Keyword analysis with weighted scoring
- Pattern matching (emails, letterhead, headers)
- Dual AI validation (OpenAI + Anthropic)
- Configurable sensitivity levels
- Confidence score aggregation

**cost-calculator.js**
- Accurate cost calculation per operation
- Supports multiple AI providers
- Tracks token usage
- Generates cost breakdowns
- Provides optimization recommendations
- Historical cost analysis

**generate-dashboard.js**
- Generates static HTML dashboard
- Real-time stats and charts
- Privilege alerts
- Cost visualizations
- Document listings
- Responsive design

**supabase-ingest.js**
- Batch document ingestion
- Embedding generation
- Vector database operations
- Metadata enrichment
- Verification and validation

### Database Schema

**discovery_documents**
- Stores processed documents
- Includes embeddings for RAG
- Metadata for filtering/search
- Indexes for fast retrieval

**processing_costs**
- Tracks all processing costs
- Breakdown by operation type
- Daily/weekly/monthly aggregation
- Budget comparison data

**privilege_logs**
- Compliance audit trail
- Privilege detection results
- Legal review tracking
- 7-year retention

## Security Architecture

### Secrets Management
- All sensitive data in GitHub Secrets
- Environment-specific secrets
- Automatic rotation reminders
- No secrets in logs or code

### Access Control
- Supabase RLS policies
- Service role for workflows
- Limited scope API keys
- Audit logging

### Compliance
- 7-year audit trail retention
- Immutable git history
- Privilege log generation
- Chain of custody tracking

## Performance Optimizations

### Parallel Processing
- Batch processing (4 parallel batches)
- Parallel embedding generation (8 batches)
- Concurrent API calls where possible

### Caching
- Document hash-based deduplication
- Avoid reprocessing unchanged files
- Embedding caching

### Cost Optimization
- Model selection by task complexity
- Batch API calls
- Efficient chunking strategy
- Rate limiting to avoid overages

## Scalability

### Current Limits
- ~1000 documents per run
- 100MB max file size
- 5-minute timeout per job

### Scaling Options
- Increase batch count for more parallelism
- Use GitHub Actions matrix for massive parallelism
- Implement distributed processing
- Add caching layer (Redis)
- Use cheaper models for simple tasks

## Monitoring & Observability

### Metrics Tracked
- Documents processed per run
- Processing time per document
- Cost per document/batch/run
- Privilege detection accuracy
- API token usage
- Error rates

### Alerts
- Budget threshold alerts (80%)
- Privilege detection alerts
- Processing failures
- API quota warnings
- Daily summary reports

## Disaster Recovery

### Backup Strategy
- Git history (immutable)
- Supabase automatic backups
- Artifact retention (30-365 days)
- Audit log retention (7 years)

### Recovery Procedures
- Reprocess from git history
- Restore from Supabase backup
- Download artifacts from GitHub
- Replay from audit trail

## Future Enhancements

### Planned Features
- Real-time websocket updates
- Advanced RAG query interface
- ML-powered document classification
- Automatic case summarization
- Predictive cost modeling
- Multi-language support

### Performance Improvements
- Distributed processing
- Smart caching layer
- Model fine-tuning
- Batch optimization
- Edge function processing

---

**Last Updated:** 2024-12-16
**Version:** 1.0.0
