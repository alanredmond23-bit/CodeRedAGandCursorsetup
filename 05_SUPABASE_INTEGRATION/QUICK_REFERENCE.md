# Quick Reference Guide

## Database Schema Summary

### Core Tables (19 Total)

**Case Management:**
- `organizations` - Law firms and companies
- `users` - Attorneys, paralegals, clients
- `legal_cases` - Legal cases/matters
- `case_parties` - Plaintiffs, defendants, witnesses
- `case_team` - Attorney assignments

**Documents:**
- `documents` - Core document metadata
- `document_versions` - Version history
- `document_relationships` - Document links
- `document_annotations` - Comments, highlights
- `document_collections` - Document sets
- `document_collection_items` - Collection membership

**Discovery:**
- `discovery_requests` - Production requests
- `discovery_productions` - Document productions

**Vector Embeddings:**
- `embedding_configs` - Model configurations
- `document_chunks` - Text chunks
- `document_embeddings` - Vector embeddings (1536-dim)
- `embedding_jobs` - Batch processing jobs
- `semantic_search_history` - Search analytics

**Privilege:**
- `privilege_detection_rules` - Auto-detection rules
- `privilege_detections` - Detection results
- `privilege_waivers` - Waiver tracking
- `privilege_logs` - Formal privilege log
- `privilege_review_queue` - Review workflow

**Costs:**
- `cost_categories` - Cost classification
- `cost_entries` - Individual cost records
- `case_budgets` - Budget allocations
- `user_cost_allocations` - Shared costs
- `budget_alerts` - Budget warnings
- `cost_forecasts` - Predictive analytics

**Audit:**
- `audit_logs` - Complete activity log
- `document_access_logs` - Document access tracking
- `privilege_change_logs` - Privilege changes
- `search_audit_logs` - Search history
- `data_export_logs` - Export tracking
- `security_events` - Security incidents
- `compliance_reports` - Compliance reporting

**Other:**
- `saved_searches` - Saved queries
- `embedding_quality_metrics` - Quality tracking
- `query_cache` - Query result caching

## Essential Functions

### Search Functions
```sql
-- Semantic search
search_by_embedding(embedding, case_id, user_id, limit, threshold, filters)

-- Hybrid search (semantic + keyword)
hybrid_search(query_text, embedding, case_id, user_id, limit, semantic_weight, filters)

-- Contextual search (with surrounding chunks)
contextual_search(embedding, case_id, user_id, context_chunks, limit)

-- Text search
search_documents(case_id, search_text, start_date, end_date, author, tags, privilege_filter, status, limit, offset)

-- Timeline search
search_documents_by_timeline(case_id, start_date, end_date, include_privileged)

-- Find similar
find_similar_documents(document_id, similarity_threshold, limit)
```

### Cost Functions
```sql
-- Track attorney time
calculate_attorney_time_cost(user_id, case_id, duration_minutes, description, date)

-- Track API costs
calculate_api_cost(case_id, user_id, api_service, tokens_used, cost_per_token, description)

-- Calculate embedding costs
batch_calculate_embedding_costs(embedding_job_id)

-- Get cost summary
get_case_cost_summary(case_id)

-- Cost breakdown
get_cost_breakdown(case_id, start_date, end_date)

-- Budget forecast
forecast_budget_depletion(case_id, lookback_days)

-- Estimate costs
estimate_document_costs(file_size_bytes, page_count, embedding_model)
```

### Privilege Functions
```sql
-- Detect privilege
detect_privilege(document_id)

-- Check access
can_access_privileged_document(document_id, user_id)

-- Generate privilege log
generate_privilege_log(case_id)

-- Export privilege log
export_privilege_log(case_id, format)
```

### Analytics Functions
```sql
-- Case summary
get_case_summary(case_id)

-- Active cases
get_active_cases_summary(organization_id)

-- Document trends
get_document_upload_trends(case_id, days)

-- User activity
get_user_activity_summary(user_id, days)

-- Database health
get_database_health()

-- Search performance
analyze_search_performance(case_id)
```

### Maintenance Functions
```sql
-- Weekly maintenance
SELECT perform_table_maintenance();

-- Daily view refresh
SELECT refresh_all_materialized_views();

-- Hourly cache cleanup
SELECT cleanup_query_cache();

-- Reindex tables
SELECT reindex_search_tables();
```

## Key Indexes

### Vector Indexes (pgvector)
- `idx_document_embeddings_embedding_hnsw` - Cosine similarity (primary)
- `idx_document_embeddings_embedding_l2` - L2 distance
- `idx_document_embeddings_embedding_ip` - Inner product

### Full-Text Indexes
- `idx_documents_text_search` - Document content search
- `idx_documents_weighted_search` - Weighted search (title > content)
- `idx_document_chunks_text_search` - Chunk content search

### Performance Indexes
- `idx_documents_case` - Fast case lookups
- `idx_document_embeddings_case_status` - Filtered embeddings
- `idx_documents_case_not_privileged` - Non-privileged docs
- `idx_documents_date_range` - Date range queries

## Common Queries

### Upload Document
```sql
INSERT INTO documents (
  case_id, organization_id, title, file_name, file_path,
  file_size, mime_type, file_hash, uploaded_by
) VALUES (
  'case-uuid', 'org-uuid', 'Title', 'file.pdf', '/path',
  1024000, 'application/pdf', 'hash', 'user-uuid'
);
```

### Create Embedding Job
```sql
INSERT INTO embedding_jobs (
  case_id, organization_id, config_id, total_chunks, started_by
) SELECT
  'case-uuid',
  'org-uuid',
  id,
  (SELECT COUNT(*) FROM document_chunks WHERE case_id = 'case-uuid'),
  'user-uuid'
FROM embedding_configs WHERE name = 'openai-ada-002';
```

### Track Time
```sql
SELECT calculate_attorney_time_cost(
  'user-uuid', 'case-uuid', 120, 'Document review'
);
```

### Search Documents
```sql
SELECT * FROM search_documents(
  'case-uuid',
  'timeline March-May',
  '2024-03-01',
  '2024-05-31',
  NULL, NULL,
  'not_privileged',
  NULL, 50, 0
);
```

### Get Case Stats
```sql
SELECT * FROM get_case_summary('case-uuid');
```

## Performance Tips

### Query Optimization
```sql
-- Use materialized views for dashboards
SELECT * FROM mv_case_statistics WHERE case_id = 'uuid';

-- Pre-filter before vector search
SELECT * FROM filtered_semantic_search(
  embedding, 'case-uuid',
  ARRAY['doc1', 'doc2'], -- specific documents
  daterange('2024-01-01', '2024-12-31'),
  false, -- not privileged
  10
);

-- Use query cache for expensive queries
SELECT get_cached_query('cache-key', 3600);
```

### Index Hints
```sql
-- Force index usage (if needed)
SET enable_seqscan = OFF;

-- Check query plan
EXPLAIN ANALYZE SELECT ...;

-- Optimize HNSW search
SELECT * FROM optimize_search_parameters('case-uuid');
```

### Batch Operations
```sql
-- Batch insert documents
COPY documents FROM '/path/to/csv' CSV HEADER;

-- Batch update costs
UPDATE cost_entries SET billing_status = 'billed'
WHERE id = ANY(ARRAY['id1', 'id2', ...]);
```

## Environment Variables

```bash
# Database connection
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-anon-key"
export SUPABASE_CONNECTION_STRING="postgresql://user:pass@host:port/db"

# OpenAI (for embeddings)
export OPENAI_API_KEY="sk-..."

# Configuration
export EMBEDDING_MODEL="openai-ada-002"
export EMBEDDING_BATCH_SIZE=100
export COST_PER_1K_TOKENS=0.0001
```

## Monitoring Queries

### Check Table Sizes
```sql
SELECT * FROM v_table_sizes ORDER BY size_bytes DESC LIMIT 10;
```

### Check Index Usage
```sql
SELECT * FROM v_index_usage ORDER BY index_scans DESC LIMIT 20;
```

### Check Slow Queries
```sql
SELECT * FROM v_slow_queries LIMIT 10;
```

### Check Pending Work
```sql
-- Pending embeddings
SELECT COUNT(*) FROM document_chunks WHERE is_embedded = false;

-- Pending privilege review
SELECT COUNT(*) FROM privilege_review_queue WHERE status = 'pending';

-- Active jobs
SELECT * FROM embedding_jobs WHERE status IN ('pending', 'running');
```

## Troubleshooting

### Slow Search
1. Check indexes exist: `SELECT * FROM pg_indexes WHERE tablename = 'document_embeddings';`
2. Analyze table: `ANALYZE document_embeddings;`
3. Rebuild index: `REINDEX INDEX idx_document_embeddings_embedding_hnsw;`
4. Check settings: `SELECT * FROM optimize_search_parameters('case-uuid');`

### Budget Not Updating
1. Check trigger: `SELECT trigger_name FROM information_schema.triggers WHERE event_object_table = 'cost_entries';`
2. Reconcile: `SELECT * FROM reconcile_case_budget('case-uuid');`
3. Recalculate: `SELECT recalculate_case_costs('case-uuid');`

### Stale Data
1. Refresh views: `SELECT refresh_all_materialized_views();`
2. Clear cache: `SELECT cleanup_query_cache();`
3. Analyze tables: `ANALYZE;`

## Security Checklist

- [ ] Enable RLS on all tables
- [ ] Configure user authentication (Supabase Auth)
- [ ] Restrict privileged document access
- [ ] Enable audit logging
- [ ] Set up backup schedule
- [ ] Configure SSL connections
- [ ] Review privilege detection rules
- [ ] Test access controls
- [ ] Monitor security events
- [ ] Configure data retention policies

## File Locations

```
supabase-integration/
├── 0001-legal-discovery-schema.sql    # Core tables
├── 0002-vector-embeddings.sql          # pgvector setup
├── 0003-cost-tracking.sql              # Cost tables
├── 0004-audit-trail.sql                # Audit logging
├── 0005-privilege-management.sql       # Privilege detection
├── 0006-rag-indexes.sql                # Performance
├── migrations/
│   └── 01-initial-setup.sql            # Combined migration
├── queries/
│   ├── dashboard-queries.sql           # Analytics
│   ├── discovery-queries.sql           # Search queries
│   └── cost-queries.sql                # Cost analytics
├── functions/
│   ├── search-embeddings.sql           # Search functions
│   └── calculate-costs.sql             # Cost functions
├── setup.py                            # Automated setup
└── README.md                           # Full documentation
```

## Support

For detailed documentation, see:
- **README.md** - Complete usage guide
- **Schema files** (0001-0006) - Table and function documentation
- **Query files** - Pre-built query examples

## Version

Database Schema v1.0.0
Last Updated: 2024-01-01
