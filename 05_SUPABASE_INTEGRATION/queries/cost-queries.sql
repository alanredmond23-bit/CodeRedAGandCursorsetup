-- =====================================================================
-- COST TRACKING & BUDGET QUERIES
-- Purpose: Cost analysis, budget monitoring, and financial reporting
-- Version: 1.0.0
-- =====================================================================

-- =====================================================================
-- COST SUMMARY QUERIES
-- =====================================================================

-- Query: Get real-time cost summary for a case
CREATE OR REPLACE FUNCTION get_case_cost_summary(p_case_id UUID)
RETURNS TABLE (
  total_cost NUMERIC,
  total_budget NUMERIC,
  budget_remaining NUMERIC,
  budget_percent_used NUMERIC,
  unbilled_cost NUMERIC,
  ai_service_cost NUMERIC,
  attorney_cost NUMERIC,
  entry_count BIGINT,
  last_cost_date DATE
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COALESCE(SUM(ce.total_cost), 0) as total_cost,
    lc.total_budget,
    lc.total_budget - COALESCE(SUM(ce.total_cost), 0) as budget_remaining,
    CASE
      WHEN lc.total_budget > 0 THEN (COALESCE(SUM(ce.total_cost), 0) / lc.total_budget * 100)
      ELSE 0
    END as budget_percent_used,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.billing_status = 'unbilled'), 0) as unbilled_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('api_call', 'embedding', 'llm_query')), 0) as ai_service_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('attorney_time', 'paralegal_time')), 0) as attorney_cost,
    COUNT(ce.id) as entry_count,
    MAX(ce.cost_date) as last_cost_date
  FROM legal_cases lc
  LEFT JOIN cost_entries ce ON lc.id = ce.case_id
  WHERE lc.id = p_case_id
  GROUP BY lc.id, lc.total_budget;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Get cost breakdown by user
CREATE OR REPLACE FUNCTION get_cost_by_user(
  p_case_id UUID,
  p_start_date DATE DEFAULT NULL,
  p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
  user_id UUID,
  user_name TEXT,
  user_role user_role,
  total_cost NUMERIC,
  billable_hours NUMERIC,
  ai_service_cost NUMERIC,
  entry_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    u.id,
    u.full_name,
    u.role,
    COALESCE(SUM(ce.total_cost), 0) as total_cost,
    COALESCE(SUM(ce.duration_minutes) / 60.0, 0) as billable_hours,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('api_call', 'embedding', 'llm_query')), 0) as ai_service_cost,
    COUNT(ce.id) as entry_count
  FROM users u
  LEFT JOIN cost_entries ce ON u.id = ce.user_id
  WHERE ce.case_id = p_case_id
    AND (p_start_date IS NULL OR ce.cost_date >= p_start_date)
    AND (p_end_date IS NULL OR ce.cost_date <= p_end_date)
  GROUP BY u.id, u.full_name, u.role
  HAVING COUNT(ce.id) > 0
  ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- BUDGET MONITORING QUERIES
-- =====================================================================

-- Query: Get budget alerts and warnings
CREATE OR REPLACE FUNCTION get_budget_alerts(
  p_case_id UUID DEFAULT NULL,
  p_organization_id UUID DEFAULT NULL,
  p_severity TEXT DEFAULT 'all' -- 'all', 'warning', 'critical'
)
RETURNS TABLE (
  alert_id UUID,
  case_number TEXT,
  case_title TEXT,
  budget_name TEXT,
  total_budget NUMERIC,
  spent_amount NUMERIC,
  percent_used NUMERIC,
  budget_health TEXT,
  alert_type TEXT,
  alert_message TEXT,
  days_remaining INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ba.id,
    lc.case_number,
    lc.title,
    cb.budget_name,
    cb.total_budget,
    cb.spent_amount,
    cb.percent_used,
    CASE
      WHEN cb.percent_used >= 100 THEN 'exceeded'
      WHEN cb.percent_used >= 90 THEN 'critical'
      WHEN cb.percent_used >= cb.alert_threshold_percent THEN 'warning'
      ELSE 'good'
    END as budget_health,
    ba.alert_type,
    ba.message,
    CASE
      WHEN cb.end_date IS NOT NULL THEN (cb.end_date - CURRENT_DATE)
      ELSE NULL
    END as days_remaining
  FROM budget_alerts ba
  JOIN case_budgets cb ON ba.case_budget_id = cb.id
  JOIN legal_cases lc ON cb.case_id = lc.id
  WHERE (p_case_id IS NULL OR cb.case_id = p_case_id)
    AND (p_organization_id IS NULL OR lc.organization_id = p_organization_id)
    AND ba.acknowledged_at IS NULL
    AND (p_severity = 'all' OR
         (p_severity = 'warning' AND cb.percent_used >= cb.alert_threshold_percent AND cb.percent_used < 90) OR
         (p_severity = 'critical' AND cb.percent_used >= 90))
  ORDER BY cb.percent_used DESC, ba.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Forecast budget depletion
CREATE OR REPLACE FUNCTION forecast_budget_depletion(
  p_case_id UUID,
  p_lookback_days INTEGER DEFAULT 30
)
RETURNS TABLE (
  current_budget NUMERIC,
  current_spent NUMERIC,
  daily_avg_cost NUMERIC,
  projected_days_remaining INTEGER,
  projected_depletion_date DATE,
  forecast_confidence TEXT
) AS $$
DECLARE
  v_total_budget NUMERIC;
  v_spent_amount NUMERIC;
  v_daily_avg NUMERIC;
  v_days_remaining INTEGER;
  v_data_points INTEGER;
BEGIN
  -- Get current budget status
  SELECT total_budget, budget_spent
  INTO v_total_budget, v_spent_amount
  FROM legal_cases
  WHERE id = p_case_id;

  -- Calculate daily average cost
  SELECT
    AVG(daily_cost),
    COUNT(*)
  INTO v_daily_avg, v_data_points
  FROM (
    SELECT DATE(cost_date), SUM(total_cost) as daily_cost
    FROM cost_entries
    WHERE case_id = p_case_id
      AND cost_date >= CURRENT_DATE - p_lookback_days
    GROUP BY DATE(cost_date)
  ) daily_costs;

  -- Calculate days remaining
  IF v_daily_avg > 0 AND v_total_budget > v_spent_amount THEN
    v_days_remaining := ((v_total_budget - v_spent_amount) / v_daily_avg)::INTEGER;
  ELSE
    v_days_remaining := NULL;
  END IF;

  RETURN QUERY
  SELECT
    v_total_budget,
    v_spent_amount,
    COALESCE(v_daily_avg, 0),
    v_days_remaining,
    CASE
      WHEN v_days_remaining IS NOT NULL THEN CURRENT_DATE + v_days_remaining
      ELSE NULL
    END,
    CASE
      WHEN v_data_points >= 20 THEN 'high'
      WHEN v_data_points >= 10 THEN 'medium'
      ELSE 'low'
    END;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- AI SERVICE COST QUERIES
-- =====================================================================

-- Query: Get embedding costs breakdown
CREATE OR REPLACE FUNCTION get_embedding_costs(
  p_case_id UUID DEFAULT NULL,
  p_organization_id UUID DEFAULT NULL,
  p_start_date DATE DEFAULT NULL,
  p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
  model_name TEXT,
  total_tokens BIGINT,
  total_cost NUMERIC,
  documents_processed BIGINT,
  avg_cost_per_document NUMERIC,
  avg_tokens_per_document NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ec.name,
    COALESCE(SUM(ej.total_tokens), 0)::BIGINT,
    COALESCE(SUM(ej.total_cost), 0),
    COUNT(DISTINCT ej.id)::BIGINT,
    CASE
      WHEN COUNT(DISTINCT ej.id) > 0 THEN COALESCE(SUM(ej.total_cost), 0) / COUNT(DISTINCT ej.id)
      ELSE 0
    END,
    CASE
      WHEN COUNT(DISTINCT ej.id) > 0 THEN COALESCE(SUM(ej.total_tokens), 0)::NUMERIC / COUNT(DISTINCT ej.id)
      ELSE 0
    END
  FROM embedding_configs ec
  LEFT JOIN embedding_jobs ej ON ec.id = ej.config_id
  WHERE (p_case_id IS NULL OR ej.case_id = p_case_id)
    AND (p_organization_id IS NULL OR ej.organization_id = p_organization_id)
    AND (p_start_date IS NULL OR DATE(ej.completed_at) >= p_start_date)
    AND (p_end_date IS NULL OR DATE(ej.completed_at) <= p_end_date)
    AND ej.status = 'completed'
  GROUP BY ec.id, ec.name
  ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Cost efficiency metrics
CREATE OR REPLACE FUNCTION get_cost_efficiency_metrics(p_case_id UUID)
RETURNS TABLE (
  metric_name TEXT,
  metric_value NUMERIC,
  metric_unit TEXT,
  benchmark TEXT
) AS $$
BEGIN
  RETURN QUERY

  -- Cost per document
  SELECT
    'cost_per_document'::TEXT,
    CASE
      WHEN COUNT(d.id) > 0 THEN COALESCE(SUM(ce.total_cost), 0) / COUNT(d.id)
      ELSE 0
    END,
    'USD'::TEXT,
    'Lower is better'::TEXT
  FROM documents d
  LEFT JOIN cost_entries ce ON d.case_id = ce.case_id
  WHERE d.case_id = p_case_id

  UNION ALL

  -- Cost per page
  SELECT
    'cost_per_page'::TEXT,
    CASE
      WHEN SUM(d.page_count) > 0 THEN COALESCE(SUM(ce.total_cost), 0) / SUM(d.page_count)
      ELSE 0
    END,
    'USD'::TEXT,
    'Lower is better'::TEXT
  FROM documents d
  LEFT JOIN cost_entries ce ON d.case_id = ce.case_id
  WHERE d.case_id = p_case_id

  UNION ALL

  -- AI cost as percentage of total
  SELECT
    'ai_cost_percentage'::TEXT,
    CASE
      WHEN SUM(ce.total_cost) > 0 THEN
        SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('api_call', 'embedding', 'llm_query')) / SUM(ce.total_cost) * 100
      ELSE 0
    END,
    'percent'::TEXT,
    'Track trend'::TEXT
  FROM cost_entries ce
  WHERE ce.case_id = p_case_id

  UNION ALL

  -- Average cost per embedding
  SELECT
    'cost_per_embedding'::TEXT,
    CASE
      WHEN COUNT(de.id) > 0 THEN COALESCE(SUM(ej.total_cost), 0) / COUNT(de.id)
      ELSE 0
    END,
    'USD'::TEXT,
    'Lower is better'::TEXT
  FROM document_embeddings de
  LEFT JOIN embedding_jobs ej ON de.id = ej.id
  JOIN documents d ON de.document_id = d.id
  WHERE d.case_id = p_case_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- BILLING QUERIES
-- =====================================================================

-- Query: Generate billing summary
CREATE OR REPLACE FUNCTION generate_billing_summary(
  p_case_id UUID,
  p_start_date DATE,
  p_end_date DATE,
  p_billing_status billing_status DEFAULT 'unbilled'
)
RETURNS TABLE (
  category_name TEXT,
  quantity NUMERIC,
  unit_cost NUMERIC,
  total_cost NUMERIC,
  entry_count BIGINT,
  user_breakdown JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COALESCE(cc.name, 'Uncategorized'),
    SUM(ce.quantity),
    AVG(ce.unit_cost),
    SUM(ce.total_cost),
    COUNT(ce.id)::BIGINT,
    jsonb_object_agg(
      u.full_name,
      SUM(ce.total_cost)
    ) FILTER (WHERE u.full_name IS NOT NULL) as user_breakdown
  FROM cost_entries ce
  LEFT JOIN cost_categories cc ON ce.category_id = cc.id
  LEFT JOIN users u ON ce.user_id = u.id
  WHERE ce.case_id = p_case_id
    AND ce.cost_date BETWEEN p_start_date AND p_end_date
    AND ce.billing_status = p_billing_status
  GROUP BY cc.name
  ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Mark costs as billed
CREATE OR REPLACE FUNCTION mark_costs_billed(
  p_case_id UUID,
  p_cost_entry_ids UUID[],
  p_invoice_id TEXT
)
RETURNS INTEGER AS $$
DECLARE
  v_updated_count INTEGER;
BEGIN
  UPDATE cost_entries
  SET
    billing_status = 'billed',
    invoice_id = p_invoice_id,
    billed_at = NOW()
  WHERE case_id = p_case_id
    AND id = ANY(p_cost_entry_ids)
    AND billing_status = 'unbilled';

  GET DIAGNOSTICS v_updated_count = ROW_COUNT;

  RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- COST COMPARISON QUERIES
-- =====================================================================

-- Query: Compare costs across cases
CREATE OR REPLACE FUNCTION compare_case_costs(
  p_organization_id UUID,
  p_case_ids UUID[] DEFAULT NULL
)
RETURNS TABLE (
  case_id UUID,
  case_number TEXT,
  case_title TEXT,
  total_documents BIGINT,
  total_cost NUMERIC,
  cost_per_document NUMERIC,
  ai_cost NUMERIC,
  attorney_cost NUMERIC,
  cost_rank INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    lc.id,
    lc.case_number,
    lc.title,
    mcs.total_documents,
    mcs.total_cost,
    CASE
      WHEN mcs.total_documents > 0 THEN mcs.total_cost / mcs.total_documents
      ELSE 0
    END as cost_per_document,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('api_call', 'embedding', 'llm_query')), 0) as ai_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('attorney_time', 'paralegal_time')), 0) as attorney_cost,
    RANK() OVER (ORDER BY mcs.total_cost DESC)::INTEGER as cost_rank
  FROM legal_cases lc
  LEFT JOIN mv_case_statistics mcs ON lc.id = mcs.case_id
  LEFT JOIN cost_entries ce ON lc.id = ce.case_id
  WHERE lc.organization_id = p_organization_id
    AND lc.is_active = true
    AND (p_case_ids IS NULL OR lc.id = ANY(p_case_ids))
  GROUP BY lc.id, lc.case_number, lc.title, mcs.total_documents, mcs.total_cost
  ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- TIME TRACKING QUERIES
-- =====================================================================

-- Query: Get attorney time summary
CREATE OR REPLACE FUNCTION get_attorney_time_summary(
  p_case_id UUID,
  p_start_date DATE DEFAULT NULL,
  p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
  user_id UUID,
  attorney_name TEXT,
  role user_role,
  total_hours NUMERIC,
  billable_hours NUMERIC,
  hourly_rate NUMERIC,
  total_cost NUMERIC,
  entries_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    u.id,
    u.full_name,
    u.role,
    COALESCE(SUM(ce.duration_minutes) / 60.0, 0) as total_hours,
    COALESCE(SUM(ce.duration_minutes) FILTER (WHERE cc.is_billable) / 60.0, 0) as billable_hours,
    COALESCE(u.hourly_rate, ct.hourly_rate_override, 0) as hourly_rate,
    COALESCE(SUM(ce.total_cost), 0) as total_cost,
    COUNT(ce.id)::BIGINT as entries_count
  FROM users u
  LEFT JOIN case_team ct ON u.id = ct.user_id AND ct.case_id = p_case_id
  LEFT JOIN cost_entries ce ON u.id = ce.user_id AND ce.case_id = p_case_id
  LEFT JOIN cost_categories cc ON ce.category_id = cc.id
  WHERE ce.cost_type IN ('attorney_time', 'paralegal_time')
    AND (p_start_date IS NULL OR ce.cost_date >= p_start_date)
    AND (p_end_date IS NULL OR ce.cost_date <= p_end_date)
  GROUP BY u.id, u.full_name, u.role, u.hourly_rate, ct.hourly_rate_override
  HAVING COUNT(ce.id) > 0
  ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- EXPORT QUERIES
-- =====================================================================

-- Query: Export costs for accounting system
CREATE OR REPLACE FUNCTION export_costs_for_accounting(
  p_organization_id UUID,
  p_start_date DATE,
  p_end_date DATE,
  p_format TEXT DEFAULT 'detailed' -- 'detailed' or 'summary'
)
RETURNS TABLE (
  transaction_id UUID,
  transaction_date DATE,
  case_number TEXT,
  category TEXT,
  description TEXT,
  quantity NUMERIC,
  unit_cost NUMERIC,
  total_cost NUMERIC,
  billing_status billing_status,
  user_email TEXT,
  invoice_id TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ce.id,
    ce.cost_date,
    lc.case_number,
    COALESCE(cc.name, ce.cost_type::TEXT),
    ce.description,
    ce.quantity,
    ce.unit_cost,
    ce.total_cost,
    ce.billing_status,
    u.email,
    ce.invoice_id
  FROM cost_entries ce
  JOIN legal_cases lc ON ce.case_id = lc.id
  LEFT JOIN cost_categories cc ON ce.category_id = cc.id
  LEFT JOIN users u ON ce.user_id = u.id
  WHERE lc.organization_id = p_organization_id
    AND ce.cost_date BETWEEN p_start_date AND p_end_date
  ORDER BY ce.cost_date, lc.case_number, ce.created_at;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON FUNCTION get_case_cost_summary IS 'Get real-time cost summary for case dashboard';
COMMENT ON FUNCTION get_budget_alerts IS 'Get budget alerts and warnings that need attention';
COMMENT ON FUNCTION forecast_budget_depletion IS 'Forecast when budget will be depleted based on spending trends';
COMMENT ON FUNCTION get_embedding_costs IS 'Get detailed breakdown of AI embedding costs';
COMMENT ON FUNCTION generate_billing_summary IS 'Generate billing summary for invoicing';
COMMENT ON FUNCTION compare_case_costs IS 'Compare costs across multiple cases';
COMMENT ON FUNCTION get_attorney_time_summary IS 'Get attorney time tracking summary';
