# Discovery Pipeline CI/CD

Automated legal discovery document processing pipeline using GitHub Actions and Vercel.

## Overview

This CI/CD pipeline automates the entire discovery document processing workflow:

1. **Document Validation** - Validates uploaded discovery documents
2. **Privilege Detection** - AI-powered attorney-client privilege detection
3. **Document Processing** - Extracts text, generates embeddings, performs AI analysis
4. **Cost Tracking** - Calculates and monitors processing costs
5. **Supabase Ingestion** - Ingests documents into vector database for RAG
6. **Dashboard Deployment** - Deploys real-time dashboard to Vercel
7. **Report Generation** - Creates daily discovery reports

## Quick Start

### Prerequisites

- GitHub repository with Actions enabled
- Vercel account
- Supabase project
- OpenAI API key
- Anthropic API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd github-vercel
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure GitHub Secrets**

   Go to Settings → Secrets and Variables → Actions, and add:

   ```
   SUPABASE_URL=<your-supabase-url>
   SUPABASE_SERVICE_KEY=<your-service-key>
   SUPABASE_ANON_KEY=<your-anon-key>
   OPENAI_API_KEY=<your-openai-key>
   ANTHROPIC_API_KEY=<your-anthropic-key>
   VERCEL_TOKEN=<your-vercel-token>
   VERCEL_ORG_ID=<your-org-id>
   VERCEL_PROJECT_ID=<your-project-id>
   SLACK_WEBHOOK=<slack-webhook-url>
   SMTP_SERVER=<smtp-server>
   SMTP_PORT=<smtp-port>
   SMTP_USERNAME=<smtp-username>
   SMTP_PASSWORD=<smtp-password>
   LEGAL_TEAM_EMAIL=<legal-team-email>
   REPORT_RECIPIENTS=<report-recipients>
   ```

4. **Create discovery documents directory**
   ```bash
   mkdir -p discovery-docs
   ```

5. **Upload documents**
   ```bash
   # Add your discovery documents
   cp /path/to/documents/* discovery-docs/
   git add discovery-docs/
   git commit -m "Add discovery documents"
   git push
   ```

   The pipeline will automatically trigger!

## Workflows

### 1. Discovery Pipeline (`discovery-pipeline.yml`)

Main workflow that processes discovery documents.

**Triggers:**
- Push to `discovery-docs/` or `case-files/`
- Manual dispatch

**Jobs:**
- Document validation
- Privilege screening
- Document processing (parallel batches)
- Cost calculation
- Supabase ingestion
- Dashboard deployment
- Audit trail generation

**Usage:**
```bash
# Trigger manually
gh workflow run discovery-pipeline.yml -f case_number="CV-2024-12345"
```

### 2. Cost Tracking (`cost-tracking.yml`)

Monitors and alerts on processing costs.

**Triggers:**
- Every 6 hours (scheduled)
- After discovery pipeline completes
- Manual dispatch

**Features:**
- Daily/weekly/monthly cost calculation
- Budget threshold alerts
- Cost optimization recommendations
- Slack/email notifications

**Budget Configuration:**
Edit `.github/workflows/cost-tracking.yml`:
```yaml
env:
  BUDGET_DAILY: 500    # USD
  BUDGET_WEEKLY: 2500  # USD
  BUDGET_MONTHLY: 10000 # USD
```

### 3. Privilege Check (`privilege-check.yml`)

AI-powered privilege detection.

**Triggers:**
- Push to `discovery-docs/`
- Manual dispatch

**Detection Methods:**
- Keyword analysis
- Pattern matching (email headers, law firm letterhead)
- Dual AI analysis (OpenAI + Anthropic)
- Confidence scoring

**Sensitivity Levels:**
- **Low** (0.7 threshold) - Strict detection
- **Medium** (0.5 threshold) - Balanced (default)
- **High** (0.3 threshold) - Aggressive flagging

**Usage:**
```bash
gh workflow run privilege-check.yml \
  -f document_path="discovery-docs/email-001.pdf" \
  -f sensitivity_level="high"
```

### 4. Supabase Ingestion (`supabase-ingest.yml`)

Ingests documents into vector database.

**Process:**
1. Document chunking (configurable size/overlap)
2. Embedding generation (parallel batches)
3. Vector store ingestion
4. Index optimization
5. Metadata enrichment
6. Verification tests

**Configuration:**
```yaml
env:
  EMBEDDING_MODEL: 'text-embedding-3-large'
  CHUNK_SIZE: 1000
  CHUNK_OVERLAP: 200
```

### 5. Daily Reports (`generate-reports.yml`)

Generates comprehensive daily reports.

**Triggers:**
- Daily at 8 AM UTC
- Manual dispatch

**Report Sections:**
- Case summaries (AI-generated)
- Privilege report
- Cost analysis
- Document timeline
- Document index

**Distribution:**
- Email (PDF attachment)
- Slack notification
- Vercel dashboard
- Repository commit

### 6. Config Deployment (`config-deploy.yml`)

Deploys configurations to all systems.

**Targets:**
- Supabase (migrations, edge functions, RLS policies)
- Vercel (environment variables)
- GitHub (repository secrets)

**Safety Features:**
- Config validation
- Secrets exposure check
- Integration tests
- Automatic rollback on failure

### 7. Integration Tests (`integration-tests.yml`)

Tests all integrations.

**Test Suites:**
- Supabase (connection, CRUD, vector search, RLS)
- OpenAI (connection, embeddings, chat, tokens)
- Anthropic (connection, streaming, analysis)
- Document processing (PDF, DOCX, OCR)
- Privilege detection
- Cost calculation
- End-to-end pipeline

## Scripts

### `scripts/discovery-processor.js`

Processes discovery documents with AI analysis.

**Features:**
- Multi-format support (PDF, DOCX, TXT)
- OCR fallback for scanned documents
- AI analysis (document type, parties, dates, topics)
- Metadata extraction
- Cost calculation
- Retry logic with exponential backoff

**Usage:**
```bash
node scripts/discovery-processor.js --batch 1
```

### `scripts/privilege-detector.js`

Detects attorney-client privilege.

**Detection Stages:**
1. Keyword analysis (weighted scoring)
2. Pattern matching (emails, letterhead)
3. AI analysis (dual provider validation)
4. Confidence aggregation

**Usage:**
```bash
node scripts/privilege-detector.js \
  --provider anthropic \
  --sensitivity medium \
  --files changed-files.txt \
  --output privilege-results.json
```

### `scripts/cost-calculator.js`

Calculates processing costs.

**Cost Categories:**
- Text extraction (OCR if needed)
- Embedding generation
- AI analysis
- Storage

**Pricing Models:**
- OpenAI (GPT-4, embeddings)
- Anthropic (Claude models)
- Supabase (storage, bandwidth)

**Usage:**
```bash
node scripts/cost-calculator.js ./output/batch-1
```

### `scripts/generate-dashboard.js`

Generates HTML dashboard.

**Dashboard Features:**
- Real-time processing stats
- Privilege alerts
- Cost breakdown
- Document listings
- Progress tracking

**Usage:**
```bash
node scripts/generate-dashboard.js ./reports
```

## Cost Optimization

### Recommended Models by Task

**Simple Classification:**
- Claude 3 Haiku ($0.25/$1.25 per 1M tokens)
- GPT-3.5 Turbo ($0.50/$1.50 per 1M tokens)

**Complex Analysis:**
- Claude 3.5 Sonnet ($3/$15 per 1M tokens) ✅ Default
- GPT-4 Turbo ($10/$30 per 1M tokens)

**Embeddings:**
- text-embedding-3-small ($0.02 per 1M tokens) - Cost-effective
- text-embedding-3-large ($0.13 per 1M tokens) ✅ Default - Better quality

### Cost Reduction Tips

1. **Use smaller embedding models** for non-critical documents
2. **Implement caching** to avoid reprocessing
3. **Batch processing** reduces overhead
4. **Filter documents** before expensive operations
5. **Use cheaper models** for initial screening

### Budget Alerts

Configure in `cost-tracking.yml`:
```yaml
env:
  BUDGET_DAILY: 500
  ALERT_THRESHOLD_PERCENT: 80  # Alert at 80% of budget
```

## Security

### Secrets Management

**Never commit:**
- API keys
- Database credentials
- Access tokens

**Use GitHub Secrets for:**
- All API keys
- Database credentials
- SMTP credentials
- Webhook URLs

### Legal Compliance

**Audit Trail:**
- All processing logged
- 7-year retention for audit logs
- Privilege logs retained indefinitely
- Immutable commit history

**Privilege Protection:**
- Automatic detection and flagging
- Legal team notification
- Pipeline blocking for high-risk documents
- Federal Rule 26(b)(5) compliant privilege logs

## Troubleshooting

### Pipeline Fails

1. Check workflow logs in GitHub Actions
2. Verify all secrets are configured
3. Check API quota/limits
4. Review error messages in artifacts

### Privilege Detection Issues

**False Positives:**
- Lower sensitivity level
- Adjust keyword weights
- Review AI prompts

**False Negatives:**
- Increase sensitivity level
- Add custom keywords
- Enable dual AI validation

### Cost Overruns

1. Review cost breakdown in dashboard
2. Check for failed retries
3. Optimize model selection
4. Implement document filtering

### Ingestion Failures

1. Check Supabase connection
2. Verify vector dimensions match
3. Check for rate limiting
4. Review chunk size/overlap

## Support

For issues or questions:
1. Check GitHub Issues
2. Review workflow logs
3. Contact legal ops team

## License

MIT License - See LICENSE file for details

---

**Generated by Discovery Pipeline CI/CD System**
