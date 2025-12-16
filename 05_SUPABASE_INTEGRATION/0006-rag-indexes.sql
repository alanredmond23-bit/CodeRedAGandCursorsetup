-- =====================================================================
-- RAG INDEXES & PERFORMANCE OPTIMIZATION
-- Purpose: Optimized indexes for fast semantic search and RAG queries
-- Version: 1.0.0
-- Target: <1 second semantic search on millions of documents
-- =====================================================================

-- =====================================================================
-- ADDITIONAL VECTOR INDEXES FOR DIFFERENT USE CASES
-- =====================================================================

-- L2 distance index (for some embedding models)
CREATE INDEX idx_document_embeddings_embedding_l2 ON document_embeddings
  USING hnsw (embedding vector_l2_ops)
  WITH (m = 16, ef_construction = 64);

-- Inner product index (for normalized embeddings)
CREATE INDEX idx_document_embeddings_embedding_ip ON document_embeddings
  USING hnsw (embedding vector_ip_ops)
  WITH (m = 16, ef_construction = 64);

-- =====================================================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- =====================================================================

-- Fast lookup: embeddings by case + status
CREATE INDEX idx_document_embeddings_case_status ON document_embeddings(case_id, status)
  WHERE status = 'completed';

-- Fast lookup: non-privileged documents for search
CREATE INDEX idx_documents_case_not_privileged ON documents(case_id, created_at DESC)
  WHERE is_privileged = false AND is_deleted = false;

-- Fast lookup: documents by date range (common filter)
CREATE INDEX idx_documents_date_range ON documents(document_date, case_id)
  WHERE document_date IS NOT NULL AND is_deleted = false;

-- Fast lookup: chunks ready for embedding
CREATE INDEX idx_document_chunks_pending_embedding ON document_chunks(case_id, created_at)
  WHERE is_embedded = false;

-- Partial index for active embedding jobs
CREATE INDEX idx_embedding_jobs_active ON embedding_jobs(organization_id, created_at DESC)
  WHERE status IN ('pending', 'running');

-- =====================================================================
-- FULL-TEXT SEARCH INDEXES
-- =====================================================================

-- Weighted full-text search (title more important than content)
CREATE INDEX idx_documents_weighted_search ON documents
  USING gin(
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(extracted_text, '')), 'C')
  );

-- Search by author and recipient
CREATE INDEX idx_documents_parties_search ON documents
  USING gin(
    to_tsvector('english', COALESCE(author, '')) ||
    to_tsvector('english', COALESCE(array_to_string(recipient, ' '), ''))
  );

-- =====================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- =====================================================================

-- Pre-aggregated case statistics
CREATE MATERIALIZED VIEW mv_case_statistics AS
SELECT
  lc.id as case_id,
  lc.case_number,
  lc.title,
  lc.status,
  lc.organization_id,

  -- Document counts
  COUNT(DISTINCT d.id) as total_documents,
  COUNT(DISTINCT d.id) FILTER (WHERE d.is_privileged) as privileged_documents,
  COUNT(DISTINCT d.id) FILTER (WHERE d.status = 'processed') as processed_documents,

  -- Embedding counts
  COUNT(DISTINCT dc.id) as total_chunks,
  COUNT(DISTINCT de.id) as total_embeddings,
  COUNT(DISTINCT de.id) FILTER (WHERE de.status = 'completed') as completed_embeddings,

  -- Costs
  COALESCE(SUM(ce.total_cost), 0) as total_cost,
  COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type = 'embedding'), 0) as embedding_cost,

  -- Dates
  MIN(d.document_date) as earliest_document_date,
  MAX(d.document_date) as latest_document_date,
  MAX(d.created_at) as last_document_uploaded,

  -- Sizes
  SUM(d.file_size) as total_file_size,
  SUM(d.page_count) as total_pages,

  -- Updated timestamp
  NOW() as last_refreshed
FROM legal_cases lc
LEFT JOIN documents d ON lc.id = d.case_id AND d.is_deleted = false
LEFT JOIN document_chunks dc ON d.id = dc.document_id
LEFT JOIN document_embeddings de ON dc.id = de.chunk_id
LEFT JOIN cost_entries ce ON lc.id = ce.case_id
GROUP BY lc.id, lc.case_number, lc.title, lc.status, lc.organization_id;

CREATE UNIQUE INDEX idx_mv_case_statistics_case_id ON mv_case_statistics(case_id);
CREATE INDEX idx_mv_case_statistics_org ON mv_case_statistics(organization_id);

-- Pre-computed document search view (for fast filtering)
CREATE MATERIALIZED VIEW mv_document_search_index AS
SELECT
  d.id,
  d.case_id,
  d.organization_id,
  d.title,
  d.document_number,
  d.file_name,
  d.author,
  d.recipient,
  d.document_date,
  d.is_privileged,
  d.privilege_status,
  d.status,
  d.tags,
  d.file_size,
  d.page_count,
  d.mime_type,
  d.created_at,

  -- Pre-computed text search vectors
  to_tsvector('english', COALESCE(d.title, '')) as title_vector,
  to_tsvector('english', COALESCE(d.extracted_text, '')) as content_vector,

  -- Embedding status
  EXISTS(
    SELECT 1 FROM document_chunks dc
    WHERE dc.document_id = d.id AND dc.is_embedded = true
  ) as has_embeddings,

  -- Access counts (for relevance ranking)
  (
    SELECT COUNT(*) FROM document_access_logs dal
    WHERE dal.document_id = d.id
  ) as access_count,

  NOW() as last_refreshed
FROM documents d
WHERE d.is_deleted = false;

CREATE UNIQUE INDEX idx_mv_document_search_index_id ON mv_document_search_index(id);
CREATE INDEX idx_mv_document_search_index_case ON mv_document_search_index(case_id);
CREATE INDEX idx_mv_document_search_index_privileged ON mv_document_search_index(is_privileged);
CREATE INDEX idx_mv_document_search_index_date ON mv_document_search_index(document_date);
CREATE INDEX idx_mv_document_search_index_title_vector ON mv_document_search_index USING gin(title_vector);
CREATE INDEX idx_mv_document_search_index_content_vector ON mv_document_search_index USING gin(content_vector);

-- =====================================================================
-- FUNCTIONS FOR MATERIALIZED VIEW REFRESH
-- =====================================================================

CREATE OR REPLACE FUNCTION refresh_case_statistics()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_case_statistics;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refresh_document_search_index()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_document_search_index;
END;
$$ LANGUAGE plpgsql;

-- Refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
  PERFORM refresh_case_statistics();
  PERFORM refresh_document_search_index();
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- PERFORMANCE TUNING FUNCTIONS
-- =====================================================================

-- Function to get optimal HNSW search parameters
CREATE OR REPLACE FUNCTION get_hnsw_search_params(
  p_dataset_size BIGINT,
  p_accuracy_level TEXT DEFAULT 'balanced' -- 'fast', 'balanced', 'accurate'
)
RETURNS TABLE (ef_search INTEGER, list_scan INTEGER) AS $$
BEGIN
  RETURN QUERY
  SELECT
    CASE p_accuracy_level
      WHEN 'fast' THEN 40
      WHEN 'balanced' THEN 100
      WHEN 'accurate' THEN 200
      ELSE 100
    END as ef_search,
    CASE
      WHEN p_dataset_size < 1000 THEN 100
      WHEN p_dataset_size < 10000 THEN 500
      WHEN p_dataset_size < 100000 THEN 1000
      ELSE 2000
    END as list_scan;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to analyze query performance
CREATE OR REPLACE FUNCTION analyze_search_performance(p_case_id UUID DEFAULT NULL)
RETURNS TABLE (
  metric TEXT,
  value NUMERIC,
  unit TEXT
) AS $$
BEGIN
  RETURN QUERY

  -- Average search time
  SELECT
    'avg_search_time'::TEXT,
    AVG(execution_time_ms)::NUMERIC,
    'milliseconds'::TEXT
  FROM semantic_search_history
  WHERE (p_case_id IS NULL OR case_id = p_case_id)
    AND created_at > NOW() - INTERVAL '7 days'

  UNION ALL

  -- P95 search time
  SELECT
    'p95_search_time'::TEXT,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms)::NUMERIC,
    'milliseconds'::TEXT
  FROM semantic_search_history
  WHERE (p_case_id IS NULL OR case_id = p_case_id)
    AND created_at > NOW() - INTERVAL '7 days'

  UNION ALL

  -- Average results returned
  SELECT
    'avg_results_count'::TEXT,
    AVG(results_count)::NUMERIC,
    'documents'::TEXT
  FROM semantic_search_history
  WHERE (p_case_id IS NULL OR case_id = p_case_id)
    AND created_at > NOW() - INTERVAL '7 days'

  UNION ALL

  -- Total embeddings
  SELECT
    'total_embeddings'::TEXT,
    COUNT(*)::NUMERIC,
    'embeddings'::TEXT
  FROM document_embeddings de
  JOIN documents d ON de.document_id = d.id
  WHERE de.status = 'completed'
    AND (p_case_id IS NULL OR d.case_id = p_case_id);
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- QUERY OPTIMIZATION HELPERS
-- =====================================================================

-- Function to suggest missing indexes
CREATE OR REPLACE FUNCTION suggest_missing_indexes()
RETURNS TABLE (
  table_name TEXT,
  column_names TEXT,
  index_type TEXT,
  reason TEXT
) AS $$
BEGIN
  -- This is a placeholder - in production, analyze pg_stat_statements
  RETURN QUERY
  SELECT
    'documents'::TEXT,
    'case_id, document_date'::TEXT,
    'btree'::TEXT,
    'Frequent date range queries'::TEXT
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname = 'public'
      AND tablename = 'documents'
      AND indexdef LIKE '%case_id%document_date%'
  );
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- PARTITIONING SETUP (For scaling to millions of documents)
-- =====================================================================

-- Example partitioning function for documents table (run when scaling)
CREATE OR REPLACE FUNCTION setup_document_partitioning()
RETURNS VOID AS $$
BEGIN
  -- Note: This requires recreating the documents table
  -- Only run when migrating to partitioned architecture

  RAISE NOTICE 'Document partitioning setup requires manual migration';
  RAISE NOTICE 'Partition by: RANGE (created_at) monthly or quarterly';
  RAISE NOTICE 'See migration guide for detailed steps';

  -- Example partition creation (commented out):
  -- CREATE TABLE documents_2024_01 PARTITION OF documents
  --   FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- INDEX MAINTENANCE
-- =====================================================================

-- Function to rebuild indexes
CREATE OR REPLACE FUNCTION reindex_search_tables()
RETURNS VOID AS $$
BEGIN
  REINDEX TABLE documents;
  REINDEX TABLE document_chunks;
  REINDEX TABLE document_embeddings;
  ANALYZE documents;
  ANALYZE document_chunks;
  ANALYZE document_embeddings;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- VACUUM AND ANALYZE SCHEDULING
-- =====================================================================

-- Function to perform maintenance on large tables
CREATE OR REPLACE FUNCTION perform_table_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Vacuum large tables
  VACUUM ANALYZE documents;
  VACUUM ANALYZE document_chunks;
  VACUUM ANALYZE document_embeddings;
  VACUUM ANALYZE audit_logs;
  VACUUM ANALYZE cost_entries;

  -- Refresh materialized views
  PERFORM refresh_all_materialized_views();

  -- Update statistics
  ANALYZE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- QUERY RESULT CACHING
-- =====================================================================

-- Table for caching expensive query results
CREATE TABLE query_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cache_key TEXT NOT NULL UNIQUE,
  query_type TEXT NOT NULL,
  query_params JSONB NOT NULL,
  result_data JSONB NOT NULL,
  result_count INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  access_count INTEGER DEFAULT 0,
  last_accessed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_query_cache_key ON query_cache(cache_key);
CREATE INDEX idx_query_cache_expires ON query_cache(expires_at);
CREATE INDEX idx_query_cache_type ON query_cache(query_type);

-- Function to get or set cached query result
CREATE OR REPLACE FUNCTION get_cached_query(
  p_cache_key TEXT,
  p_ttl_seconds INTEGER DEFAULT 3600
)
RETURNS JSONB AS $$
DECLARE
  v_result JSONB;
BEGIN
  -- Try to get from cache
  SELECT result_data INTO v_result
  FROM query_cache
  WHERE cache_key = p_cache_key
    AND expires_at > NOW();

  -- Update access stats if found
  IF FOUND THEN
    UPDATE query_cache
    SET
      access_count = access_count + 1,
      last_accessed_at = NOW()
    WHERE cache_key = p_cache_key;
  END IF;

  RETURN v_result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_cached_query(
  p_cache_key TEXT,
  p_query_type TEXT,
  p_query_params JSONB,
  p_result_data JSONB,
  p_ttl_seconds INTEGER DEFAULT 3600
)
RETURNS VOID AS $$
BEGIN
  INSERT INTO query_cache (
    cache_key,
    query_type,
    query_params,
    result_data,
    result_count,
    expires_at
  ) VALUES (
    p_cache_key,
    p_query_type,
    p_query_params,
    p_result_data,
    (p_result_data->>'count')::INTEGER,
    NOW() + (p_ttl_seconds || ' seconds')::INTERVAL
  )
  ON CONFLICT (cache_key) DO UPDATE SET
    result_data = EXCLUDED.result_data,
    result_count = EXCLUDED.result_count,
    expires_at = EXCLUDED.expires_at,
    created_at = NOW(),
    access_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_query_cache()
RETURNS INTEGER AS $$
DECLARE
  v_deleted INTEGER;
BEGIN
  DELETE FROM query_cache WHERE expires_at < NOW();
  GET DIAGNOSTICS v_deleted = ROW_COUNT;
  RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- STATISTICS AND MONITORING
-- =====================================================================

-- View: Index usage statistics
CREATE OR REPLACE VIEW v_index_usage AS
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as index_scans,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- View: Table sizes
CREATE OR REPLACE VIEW v_table_sizes AS
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
  pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- View: Query performance stats (requires pg_stat_statements extension)
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT
  SUBSTRING(query, 1, 100) as query_preview,
  calls,
  ROUND(total_exec_time::numeric, 2) as total_time_ms,
  ROUND(mean_exec_time::numeric, 2) as mean_time_ms,
  ROUND(max_exec_time::numeric, 2) as max_time_ms,
  ROUND((100 * total_exec_time / SUM(total_exec_time) OVER ())::numeric, 2) as pct_total_time
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC
LIMIT 50;

-- =====================================================================
-- PERFORMANCE CONFIGURATION RECOMMENDATIONS
-- =====================================================================

-- Function to get recommended configuration
CREATE OR REPLACE FUNCTION get_performance_recommendations()
RETURNS TABLE (
  setting TEXT,
  current_value TEXT,
  recommended_value TEXT,
  reason TEXT
) AS $$
BEGIN
  RETURN QUERY

  -- shared_buffers
  SELECT
    'shared_buffers'::TEXT,
    current_setting('shared_buffers')::TEXT,
    '4GB'::TEXT,
    'Increase for better caching of frequently accessed data'::TEXT

  UNION ALL

  -- effective_cache_size
  SELECT
    'effective_cache_size'::TEXT,
    current_setting('effective_cache_size')::TEXT,
    '12GB'::TEXT,
    'Help query planner make better decisions'::TEXT

  UNION ALL

  -- maintenance_work_mem
  SELECT
    'maintenance_work_mem'::TEXT,
    current_setting('maintenance_work_mem')::TEXT,
    '1GB'::TEXT,
    'Faster index builds and vacuuming'::TEXT

  UNION ALL

  -- work_mem
  SELECT
    'work_mem'::TEXT,
    current_setting('work_mem')::TEXT,
    '64MB'::TEXT,
    'Better sort and hash operations'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON MATERIALIZED VIEW mv_case_statistics IS 'Pre-aggregated case statistics for dashboard performance';
COMMENT ON MATERIALIZED VIEW mv_document_search_index IS 'Pre-computed search index for fast document filtering';
COMMENT ON TABLE query_cache IS 'Cache for expensive query results to improve performance';
COMMENT ON FUNCTION refresh_all_materialized_views IS 'Refresh all materialized views - run daily or after bulk operations';
COMMENT ON FUNCTION analyze_search_performance IS 'Analyze semantic search performance metrics';
COMMENT ON FUNCTION perform_table_maintenance IS 'Perform vacuum, analyze, and refresh - run weekly';

-- =====================================================================
-- INITIAL ANALYSIS
-- =====================================================================

-- Analyze all tables for query planner
ANALYZE organizations;
ANALYZE users;
ANALYZE legal_cases;
ANALYZE documents;
ANALYZE document_chunks;
ANALYZE document_embeddings;
ANALYZE cost_entries;
ANALYZE audit_logs;
