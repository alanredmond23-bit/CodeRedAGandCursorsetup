# Discovery Pipeline Setup Guide

Complete setup instructions for the GitHub Actions + Vercel discovery pipeline.

## Prerequisites

Before starting, ensure you have:

- [ ] GitHub repository with Actions enabled
- [ ] Vercel account (Pro plan recommended)
- [ ] Supabase project
- [ ] OpenAI API key with GPT-4 and embeddings access
- [ ] Anthropic API key with Claude 3.5 Sonnet access
- [ ] SMTP credentials for email notifications (optional)
- [ ] Slack workspace webhook URL (optional)

## Step 1: Repository Setup

1. **Clone or create repository**
   ```bash
   git clone <your-repo-url>
   cd <your-repo>
   ```

2. **Copy pipeline files**
   ```bash
   # If using this as a template
   cp -r github-vercel/* .
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

4. **Create required directories**
   ```bash
   mkdir -p discovery-docs case-files config tests
   ```

## Step 2: Supabase Configuration

1. **Create Supabase project**
   - Go to https://supabase.com
   - Create new project
   - Note your project URL and keys

2. **Create database table**

   Run this SQL in Supabase SQL Editor:

   ```sql
   -- Enable pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;

   -- Create discovery documents table
   CREATE TABLE discovery_documents (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     case_id TEXT NOT NULL,
     file_name TEXT NOT NULL,
     file_path TEXT NOT NULL,
     content TEXT NOT NULL,
     embedding vector(1536),
     metadata JSONB DEFAULT '{}'::jsonb,
     word_count INTEGER DEFAULT 0,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Create indexes
   CREATE INDEX idx_discovery_case_id ON discovery_documents(case_id);
   CREATE INDEX idx_discovery_created_at ON discovery_documents(created_at);
   CREATE INDEX idx_discovery_embedding ON discovery_documents
     USING ivfflat (embedding vector_cosine_ops)
     WITH (lists = 100);

   -- Create cost tracking table
   CREATE TABLE processing_costs (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     run_id TEXT NOT NULL,
     date DATE NOT NULL,
     document_count INTEGER DEFAULT 0,
     extraction_cost DECIMAL(10, 4) DEFAULT 0,
     embedding_cost DECIMAL(10, 4) DEFAULT 0,
     analysis_cost DECIMAL(10, 4) DEFAULT 0,
     storage_cost DECIMAL(10, 4) DEFAULT 0,
     total_cost DECIMAL(10, 4) DEFAULT 0,
     metadata JSONB DEFAULT '{}'::jsonb,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Create privilege log table
   CREATE TABLE privilege_logs (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     run_id TEXT NOT NULL,
     document_path TEXT NOT NULL,
     is_privileged BOOLEAN DEFAULT false,
     confidence DECIMAL(3, 2),
     reasons TEXT[],
     keywords TEXT[],
     reviewed_by TEXT,
     reviewed_at TIMESTAMP WITH TIME ZONE,
     decision TEXT,
     metadata JSONB DEFAULT '{}'::jsonb,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Create RLS policies
   ALTER TABLE discovery_documents ENABLE ROW LEVEL SECURITY;
   ALTER TABLE processing_costs ENABLE ROW LEVEL SECURITY;
   ALTER TABLE privilege_logs ENABLE ROW LEVEL SECURITY;

   -- Service role has full access
   CREATE POLICY "Service role full access on discovery_documents"
     ON discovery_documents FOR ALL
     USING (auth.role() = 'service_role');

   CREATE POLICY "Service role full access on processing_costs"
     ON processing_costs FOR ALL
     USING (auth.role() = 'service_role');

   CREATE POLICY "Service role full access on privilege_logs"
     ON privilege_logs FOR ALL
     USING (auth.role() = 'service_role');
   ```

3. **Create vector search function**

   ```sql
   -- Function for similarity search
   CREATE OR REPLACE FUNCTION search_documents(
     query_embedding vector(1536),
     match_threshold float DEFAULT 0.7,
     match_count int DEFAULT 10,
     filter_case_id text DEFAULT NULL
   )
   RETURNS TABLE (
     id uuid,
     file_name text,
     content text,
     similarity float
   )
   LANGUAGE plpgsql
   AS $$
   BEGIN
     RETURN QUERY
     SELECT
       d.id,
       d.file_name,
       d.content,
       1 - (d.embedding <=> query_embedding) AS similarity
     FROM discovery_documents d
     WHERE (filter_case_id IS NULL OR d.case_id = filter_case_id)
       AND 1 - (d.embedding <=> query_embedding) > match_threshold
     ORDER BY d.embedding <=> query_embedding
     LIMIT match_count;
   END;
   $$;
   ```

## Step 3: GitHub Secrets Configuration

Go to your GitHub repository → Settings → Secrets and Variables → Actions

Add these secrets:

### Required Secrets

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
VERCEL_TOKEN=...
VERCEL_ORG_ID=team_...
VERCEL_PROJECT_ID=prj_...
```

### Optional Secrets (for notifications)

```
SLACK_WEBHOOK=https://hooks.slack.com/services/...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
LEGAL_TEAM_EMAIL=legal@company.com
REPORT_RECIPIENTS=person1@company.com,person2@company.com
```

### Get Vercel Credentials

1. **Vercel Token**
   ```bash
   # Install Vercel CLI
   npm i -g vercel

   # Login and get token
   vercel login
   vercel token create
   ```

2. **Vercel Org ID and Project ID**
   ```bash
   # Link your project
   vercel link

   # Get IDs from .vercel/project.json
   cat .vercel/project.json
   ```

## Step 4: Vercel Project Setup

1. **Create Vercel project**
   ```bash
   vercel
   ```

2. **Configure environment variables**
   ```bash
   # Set production environment variables
   vercel env add SUPABASE_URL production
   vercel env add SUPABASE_ANON_KEY production
   ```

3. **Test deployment**
   ```bash
   vercel --prod
   ```

## Step 5: Test the Pipeline

1. **Create test document**
   ```bash
   echo "This is a test discovery document." > discovery-docs/test.txt
   ```

2. **Commit and push**
   ```bash
   git add .
   git commit -m "test: add test document"
   git push
   ```

3. **Monitor workflow**
   - Go to GitHub Actions tab
   - Watch the "Discovery Document Pipeline" workflow
   - Check for errors

4. **Verify results**
   - Check Supabase table for ingested document
   - View deployed dashboard on Vercel
   - Check for notifications

## Step 6: Configure Budget Alerts

Edit `.github/workflows/cost-tracking.yml`:

```yaml
env:
  BUDGET_DAILY: 500      # Adjust to your budget
  BUDGET_WEEKLY: 2500    # Adjust to your budget
  BUDGET_MONTHLY: 10000  # Adjust to your budget
  ALERT_THRESHOLD_PERCENT: 80
```

## Step 7: Customize Privilege Detection

Edit `scripts/privilege-detector.js` to add custom keywords:

```javascript
const PRIVILEGE_KEYWORDS = {
  high: [
    'attorney-client privilege',
    'work product',
    // Add your keywords here
  ],
  medium: [
    'confidential communication',
    'attorney',
    // Add your keywords here
  ]
};
```

## Troubleshooting

### Workflow fails with "API key invalid"

**Solution:** Verify secrets are set correctly
```bash
gh secret list
```

### Documents not ingesting to Supabase

**Solution:** Check Supabase logs and RLS policies
```sql
-- Test connection
SELECT * FROM discovery_documents LIMIT 1;
```

### Cost tracking not working

**Solution:** Verify Supabase cost tracking table exists
```sql
SELECT * FROM processing_costs LIMIT 1;
```

### Dashboard not deploying

**Solution:** Check Vercel logs
```bash
vercel logs <deployment-url>
```

## Next Steps

1. **Add real discovery documents**
   ```bash
   cp /path/to/docs/* discovery-docs/
   git add discovery-docs/
   git commit -m "docs: add discovery documents"
   git push
   ```

2. **Set up scheduled reports**
   - Reports run daily at 8 AM UTC by default
   - Edit `.github/workflows/generate-reports.yml` to change schedule

3. **Configure case management**
   - Use workflow dispatch with case numbers
   - Organize documents by case in subdirectories

4. **Monitor costs**
   - Check cost dashboard regularly
   - Adjust models if costs are too high
   - Implement caching for repeated documents

5. **Review privilege logs**
   - Check privilege reports daily
   - Set up legal team review process
   - Update privilege log in Supabase

## Security Best Practices

1. **Never commit secrets**
   - Use GitHub Secrets only
   - Add `.env` to `.gitignore`

2. **Rotate API keys regularly**
   - Set reminders for quarterly rotation
   - Update GitHub secrets when rotating

3. **Review RLS policies**
   - Ensure proper access controls
   - Test with different roles

4. **Audit trail**
   - Audit logs retained for 7 years
   - Review regularly for compliance

5. **Backup strategy**
   - Export Supabase data regularly
   - Keep offline copies of privilege logs

## Support

For issues or questions:

1. Check GitHub Actions logs
2. Review workflow run artifacts
3. Check Supabase logs
4. Verify API quotas
5. Contact DevOps team

---

**Setup Complete!** You're now ready to process discovery documents automatically.
