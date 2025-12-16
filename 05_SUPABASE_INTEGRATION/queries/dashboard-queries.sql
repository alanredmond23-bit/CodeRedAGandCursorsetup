-- =====================================================================
-- DASHBOARD & ANALYTICS QUERIES
-- Purpose: Pre-built queries for dashboard and reporting
-- Version: 1.0.0
-- =====================================================================

-- =====================================================================
-- CASE OVERVIEW QUERIES
-- =====================================================================

-- Query: Get case summary with statistics
-- Usage: Display on case dashboard
CREATE OR REPLACE FUNCTION get_case_summary(p_case_id UUID)
RETURNS TABLE (
  case_id UUID,
  case_number TEXT,
  title TEXT,
  status case_status,
  total_documents BIGINT,
  privileged_documents BIGINT,
  processed_documents BIGINT,
  embedded_documents BIGINT,
  total_pages BIGINT,
  total_cost NUMERIC,
  budget_remaining NUMERIC,
  budget_percent_used NUMERIC,
  team_member_count BIGINT,
  last_activity TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    lc.id,
    lc.case_number,
    lc.title,
    lc.status,
    mcs.total_documents,
    mcs.privileged_documents,
    mcs.processed_documents,
    mcs.completed_embeddings,
    mcs.total_pages,
    mcs.total_cost,
    lc.total_budget - lc.budget_spent as budget_remaining,
    CASE
      WHEN lc.total_budget > 0 THEN (lc.budget_spent / lc.total_budget * 100)
      ELSE 0
    END as budget_percent_used,
    (SELECT COUNT(*) FROM case_team WHERE case_id = lc.id AND is_active = true) as team_member_count,
    GREATEST(
      lc.updated_at,
      (SELECT MAX(created_at) FROM documents WHERE case_id = lc.id),
      (SELECT MAX(created_at) FROM audit_logs WHERE case_id = lc.id)
    ) as last_activity
  FROM legal_cases lc
  LEFT JOIN mv_case_statistics mcs ON lc.id = mcs.case_id
  WHERE lc.id = p_case_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Get all active cases with summary
CREATE OR REPLACE FUNCTION get_active_cases_summary(p_organization_id UUID)
RETURNS TABLE (
  case_id UUID,
  case_number TEXT,
  title TEXT,
  status case_status,
  total_documents BIGINT,
  privileged_documents BIGINT,
  total_cost NUMERIC,
  budget_health TEXT,
  days_since_activity INTEGER,
  priority_score NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    lc.id,
    lc.case_number,
    lc.title,
    lc.status,
    COALESCE(mcs.total_documents, 0),
    COALESCE(mcs.privileged_documents, 0),
    COALESCE(mcs.total_cost, 0),
    CASE
      WHEN lc.total_budget IS NULL THEN 'no_budget'
      WHEN (lc.budget_spent / NULLIF(lc.total_budget, 0) * 100) >= 100 THEN 'exceeded'
      WHEN (lc.budget_spent / NULLIF(lc.total_budget, 0) * 100) >= 90 THEN 'critical'
      WHEN (lc.budget_spent / NULLIF(lc.total_budget, 0) * 100) >= 75 THEN 'warning'
      ELSE 'good'
    END as budget_health,
    EXTRACT(DAY FROM NOW() - GREATEST(
      lc.updated_at,
      (SELECT MAX(created_at) FROM documents WHERE case_id = lc.id)
    ))::INTEGER as days_since_activity,
    -- Priority score based on activity, budget, and deadlines
    (
      CASE WHEN lc.trial_date IS NOT NULL AND lc.trial_date < NOW() + INTERVAL '30 days' THEN 50 ELSE 0 END +
      CASE WHEN (lc.budget_spent / NULLIF(lc.total_budget, 0) * 100) >= 90 THEN 30 ELSE 0 END +
      CASE WHEN COALESCE(mcs.total_documents, 0) > 10000 THEN 20 ELSE 0 END
    )::NUMERIC as priority_score
  FROM legal_cases lc
  LEFT JOIN mv_case_statistics mcs ON lc.id = mcs.case_id
  WHERE lc.organization_id = p_organization_id
    AND lc.is_active = true
    AND lc.status NOT IN ('closed', 'archived')
  ORDER BY priority_score DESC, lc.updated_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- DOCUMENT ANALYTICS QUERIES
-- =====================================================================

-- Query: Document upload trends
CREATE OR REPLACE FUNCTION get_document_upload_trends(
  p_case_id UUID,
  p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
  upload_date DATE,
  document_count BIGINT,
  total_size_mb NUMERIC,
  privileged_count BIGINT,
  cumulative_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  WITH daily_uploads AS (
    SELECT
      DATE(created_at) as upload_date,
      COUNT(*) as document_count,
      ROUND(SUM(file_size)::NUMERIC / 1024 / 1024, 2) as total_size_mb,
      COUNT(*) FILTER (WHERE is_privileged) as privileged_count
    FROM documents
    WHERE case_id = p_case_id
      AND created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY DATE(created_at)
  )
  SELECT
    du.upload_date,
    du.document_count,
    du.total_size_mb,
    du.privileged_count,
    SUM(du.document_count) OVER (ORDER BY du.upload_date) as cumulative_count
  FROM daily_uploads du
  ORDER BY du.upload_date;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Document status breakdown
CREATE OR REPLACE FUNCTION get_document_status_breakdown(p_case_id UUID)
RETURNS TABLE (
  status document_status,
  count BIGINT,
  total_size_mb NUMERIC,
  percentage NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  WITH totals AS (
    SELECT COUNT(*) as total_count FROM documents WHERE case_id = p_case_id
  )
  SELECT
    d.status,
    COUNT(*) as count,
    ROUND(SUM(d.file_size)::NUMERIC / 1024 / 1024, 2) as total_size_mb,
    ROUND((COUNT(*)::NUMERIC / t.total_count * 100), 2) as percentage
  FROM documents d
  CROSS JOIN totals t
  WHERE d.case_id = p_case_id
  GROUP BY d.status, t.total_count
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- COST ANALYTICS QUERIES
-- =====================================================================

-- Query: Cost breakdown by type
CREATE OR REPLACE FUNCTION get_cost_breakdown(
  p_case_id UUID,
  p_start_date DATE DEFAULT NULL,
  p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
  cost_type cost_type,
  total_cost NUMERIC,
  entry_count BIGINT,
  avg_cost NUMERIC,
  percentage NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  WITH totals AS (
    SELECT COALESCE(SUM(total_cost), 0) as total
    FROM cost_entries
    WHERE case_id = p_case_id
      AND (p_start_date IS NULL OR cost_date >= p_start_date)
      AND (p_end_date IS NULL OR cost_date <= p_end_date)
  )
  SELECT
    ce.cost_type,
    COALESCE(SUM(ce.total_cost), 0) as total_cost,
    COUNT(*) as entry_count,
    ROUND(AVG(ce.total_cost), 6) as avg_cost,
    ROUND((COALESCE(SUM(ce.total_cost), 0) / NULLIF(t.total, 0) * 100), 2) as percentage
  FROM cost_entries ce
  CROSS JOIN totals t
  WHERE ce.case_id = p_case_id
    AND (p_start_date IS NULL OR ce.cost_date >= p_start_date)
    AND (p_end_date IS NULL OR ce.cost_date <= p_end_date)
  GROUP BY ce.cost_type, t.total
  ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Monthly cost trends
CREATE OR REPLACE FUNCTION get_monthly_cost_trends(
  p_case_id UUID,
  p_months INTEGER DEFAULT 12
)
RETURNS TABLE (
  month DATE,
  total_cost NUMERIC,
  ai_cost NUMERIC,
  attorney_cost NUMERIC,
  other_cost NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    DATE_TRUNC('month', ce.cost_date)::DATE as month,
    COALESCE(SUM(ce.total_cost), 0) as total_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('api_call', 'embedding', 'llm_query')), 0) as ai_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('attorney_time', 'paralegal_time')), 0) as attorney_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type NOT IN ('api_call', 'embedding', 'llm_query', 'attorney_time', 'paralegal_time')), 0) as other_cost
  FROM cost_entries ce
  WHERE ce.case_id = p_case_id
    AND ce.cost_date >= DATE_TRUNC('month', NOW() - (p_months || ' months')::INTERVAL)
  GROUP BY DATE_TRUNC('month', ce.cost_date)
  ORDER BY month;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- USER ACTIVITY QUERIES
-- =====================================================================

-- Query: User activity summary
CREATE OR REPLACE FUNCTION get_user_activity_summary(
  p_user_id UUID,
  p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
  activity_type TEXT,
  count BIGINT,
  most_recent TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY

  -- Document views
  SELECT
    'document_views'::TEXT,
    COUNT(*)::BIGINT,
    MAX(created_at)
  FROM document_access_logs
  WHERE user_id = p_user_id
    AND created_at >= NOW() - (p_days || ' days')::INTERVAL

  UNION ALL

  -- Searches
  SELECT
    'searches'::TEXT,
    COUNT(*)::BIGINT,
    MAX(created_at)
  FROM search_audit_logs
  WHERE user_id = p_user_id
    AND created_at >= NOW() - (p_days || ' days')::INTERVAL

  UNION ALL

  -- Document uploads
  SELECT
    'document_uploads'::TEXT,
    COUNT(*)::BIGINT,
    MAX(created_at)
  FROM documents
  WHERE uploaded_by = p_user_id
    AND created_at >= NOW() - (p_days || ' days')::INTERVAL

  UNION ALL

  -- Annotations
  SELECT
    'annotations'::TEXT,
    COUNT(*)::BIGINT,
    MAX(created_at)
  FROM document_annotations
  WHERE user_id = p_user_id
    AND created_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- PRIVILEGE ANALYTICS QUERIES
-- =====================================================================

-- Query: Privilege detection effectiveness
CREATE OR REPLACE FUNCTION get_privilege_detection_metrics(p_case_id UUID)
RETURNS TABLE (
  total_detections BIGINT,
  pending_review BIGINT,
  confirmed BIGINT,
  rejected BIGINT,
  avg_confidence NUMERIC,
  avg_review_time_hours NUMERIC,
  detection_accuracy NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*)::BIGINT as total_detections,
    COUNT(*) FILTER (WHERE status = 'pending_review')::BIGINT as pending_review,
    COUNT(*) FILTER (WHERE status = 'confirmed')::BIGINT as confirmed,
    COUNT(*) FILTER (WHERE status = 'rejected')::BIGINT as rejected,
    ROUND(AVG(confidence_score), 4) as avg_confidence,
    ROUND(AVG(EXTRACT(EPOCH FROM (reviewed_at - created_at)) / 3600), 2) FILTER (WHERE reviewed_at IS NOT NULL) as avg_review_time_hours,
    CASE
      WHEN COUNT(*) FILTER (WHERE status IN ('confirmed', 'rejected')) > 0 THEN
        ROUND((COUNT(*) FILTER (WHERE status = 'confirmed')::NUMERIC /
               COUNT(*) FILTER (WHERE status IN ('confirmed', 'rejected'))::NUMERIC * 100), 2)
      ELSE 0
    END as detection_accuracy
  FROM privilege_detections
  WHERE case_id = p_case_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- SEARCH ANALYTICS QUERIES
-- =====================================================================

-- Query: Popular search terms
CREATE OR REPLACE FUNCTION get_popular_search_terms(
  p_case_id UUID DEFAULT NULL,
  p_days INTEGER DEFAULT 30,
  p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
  search_query TEXT,
  search_count BIGINT,
  avg_results INTEGER,
  avg_execution_time_ms INTEGER,
  last_searched TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    sal.search_query,
    COUNT(*)::BIGINT as search_count,
    ROUND(AVG(sal.results_count))::INTEGER as avg_results,
    ROUND(AVG(sal.execution_time_ms))::INTEGER as avg_execution_time_ms,
    MAX(sal.created_at) as last_searched
  FROM search_audit_logs sal
  WHERE (p_case_id IS NULL OR sal.case_id = p_case_id)
    AND sal.created_at >= NOW() - (p_days || ' days')::INTERVAL
  GROUP BY sal.search_query
  ORDER BY search_count DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- SYSTEM HEALTH QUERIES
-- =====================================================================

-- Query: Database health check
CREATE OR REPLACE FUNCTION get_database_health()
RETURNS TABLE (
  metric TEXT,
  value TEXT,
  status TEXT
) AS $$
BEGIN
  RETURN QUERY

  -- Total documents
  SELECT
    'total_documents'::TEXT,
    COUNT(*)::TEXT,
    CASE WHEN COUNT(*) < 1000000 THEN 'healthy' ELSE 'review' END
  FROM documents

  UNION ALL

  -- Total embeddings
  SELECT
    'total_embeddings'::TEXT,
    COUNT(*)::TEXT,
    'healthy'::TEXT
  FROM document_embeddings

  UNION ALL

  -- Pending embeddings
  SELECT
    'pending_embedding_jobs'::TEXT,
    COUNT(*)::TEXT,
    CASE WHEN COUNT(*) > 100 THEN 'warning' ELSE 'healthy' END
  FROM embedding_jobs
  WHERE status IN ('pending', 'running')

  UNION ALL

  -- Failed embeddings
  SELECT
    'failed_embeddings'::TEXT,
    COUNT(*)::TEXT,
    CASE WHEN COUNT(*) > 1000 THEN 'critical' ELSE 'healthy' END
  FROM document_embeddings
  WHERE status = 'failed'

  UNION ALL

  -- Database size
  SELECT
    'database_size'::TEXT,
    pg_size_pretty(pg_database_size(current_database())),
    'healthy'::TEXT

  UNION ALL

  -- Largest table
  SELECT
    'largest_table'::TEXT,
    (SELECT tablename || ': ' || pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
     FROM pg_tables
     WHERE schemaname = 'public'
     ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
     LIMIT 1),
    'info'::TEXT;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON FUNCTION get_case_summary IS 'Get comprehensive case summary with statistics for dashboard';
COMMENT ON FUNCTION get_active_cases_summary IS 'Get all active cases with priority scoring';
COMMENT ON FUNCTION get_document_upload_trends IS 'Get document upload trends over time';
COMMENT ON FUNCTION get_cost_breakdown IS 'Get cost breakdown by type with percentages';
COMMENT ON FUNCTION get_user_activity_summary IS 'Get user activity summary for recent days';
COMMENT ON FUNCTION get_privilege_detection_metrics IS 'Get privilege detection effectiveness metrics';
COMMENT ON FUNCTION get_database_health IS 'Quick database health check';
