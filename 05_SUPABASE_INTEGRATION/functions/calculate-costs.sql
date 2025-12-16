-- =====================================================================
-- COST CALCULATION FUNCTIONS
-- Purpose: Automated cost calculation and tracking functions
-- Version: 1.0.0
-- =====================================================================

-- =====================================================================
-- CALCULATE ATTORNEY TIME COST
-- =====================================================================

CREATE OR REPLACE FUNCTION calculate_attorney_time_cost(
  p_user_id UUID,
  p_case_id UUID,
  p_duration_minutes INTEGER,
  p_description TEXT,
  p_date DATE DEFAULT CURRENT_DATE
)
RETURNS UUID AS $$
DECLARE
  v_hourly_rate DECIMAL(10,2);
  v_cost_entry_id UUID;
  v_category_id UUID;
  v_organization_id UUID;
  v_cost_type cost_type;
  v_user_role user_role;
BEGIN
  -- Get user details
  SELECT
    COALESCE(ct.hourly_rate_override, u.hourly_rate, 0),
    u.organization_id,
    u.role
  INTO v_hourly_rate, v_organization_id, v_user_role
  FROM users u
  LEFT JOIN case_team ct ON u.id = ct.user_id AND ct.case_id = p_case_id
  WHERE u.id = p_user_id;

  IF v_hourly_rate IS NULL THEN
    RAISE EXCEPTION 'User not found or hourly rate not set: %', p_user_id;
  END IF;

  -- Determine cost type based on role
  v_cost_type := CASE
    WHEN v_user_role IN ('lead_attorney', 'associate_attorney') THEN 'attorney_time'::cost_type
    WHEN v_user_role = 'paralegal' THEN 'paralegal_time'::cost_type
    ELSE 'attorney_time'::cost_type
  END;

  -- Get cost category
  SELECT id INTO v_category_id
  FROM cost_categories
  WHERE name = 'Legal Services' AND is_active = true
  LIMIT 1;

  -- Create cost entry
  INSERT INTO cost_entries (
    organization_id,
    case_id,
    user_id,
    cost_type,
    category_id,
    description,
    quantity,
    unit_cost,
    duration_minutes,
    cost_date,
    metadata
  ) VALUES (
    v_organization_id,
    p_case_id,
    p_user_id,
    v_cost_type,
    v_category_id,
    p_description,
    p_duration_minutes / 60.0, -- Convert to hours
    v_hourly_rate,
    p_duration_minutes,
    p_date,
    jsonb_build_object(
      'hourly_rate', v_hourly_rate,
      'user_role', v_user_role
    )
  ) RETURNING id INTO v_cost_entry_id;

  RETURN v_cost_entry_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- CALCULATE API CALL COST
-- =====================================================================

CREATE OR REPLACE FUNCTION calculate_api_cost(
  p_case_id UUID,
  p_user_id UUID,
  p_api_service TEXT,
  p_tokens_used INTEGER,
  p_cost_per_token DECIMAL(10,8),
  p_description TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  v_cost_entry_id UUID;
  v_category_id UUID;
  v_organization_id UUID;
BEGIN
  -- Get organization
  SELECT organization_id INTO v_organization_id
  FROM legal_cases
  WHERE id = p_case_id;

  -- Get cost category
  SELECT id INTO v_category_id
  FROM cost_categories
  WHERE name = 'AI Services' AND is_active = true
  LIMIT 1;

  -- Create cost entry
  INSERT INTO cost_entries (
    organization_id,
    case_id,
    user_id,
    cost_type,
    category_id,
    description,
    quantity,
    unit_cost,
    metadata
  ) VALUES (
    v_organization_id,
    p_case_id,
    p_user_id,
    'api_call',
    v_category_id,
    COALESCE(p_description, format('API call: %s', p_api_service)),
    p_tokens_used,
    p_cost_per_token,
    jsonb_build_object(
      'api_service', p_api_service,
      'tokens', p_tokens_used
    )
  ) RETURNING id INTO v_cost_entry_id;

  RETURN v_cost_entry_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- BATCH CALCULATE EMBEDDING COSTS
-- =====================================================================

CREATE OR REPLACE FUNCTION batch_calculate_embedding_costs(
  p_embedding_job_id UUID
)
RETURNS DECIMAL(10,6) AS $$
DECLARE
  v_total_cost DECIMAL(10,6);
  v_config RECORD;
  v_job RECORD;
  v_category_id UUID;
BEGIN
  -- Get job details
  SELECT * INTO v_job
  FROM embedding_jobs
  WHERE id = p_embedding_job_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Embedding job not found: %', p_embedding_job_id;
  END IF;

  -- Get embedding config
  SELECT * INTO v_config
  FROM embedding_configs
  WHERE id = v_job.config_id;

  -- Calculate total cost
  v_total_cost := (v_job.total_tokens / 1000.0) * v_config.cost_per_1k_tokens;

  -- Update job with cost
  UPDATE embedding_jobs
  SET
    total_cost = v_total_cost,
    updated_at = NOW()
  WHERE id = p_embedding_job_id;

  -- Get cost category
  SELECT id INTO v_category_id
  FROM cost_categories
  WHERE name = 'Embeddings' AND is_active = true
  LIMIT 1;

  -- Create cost entry
  INSERT INTO cost_entries (
    organization_id,
    case_id,
    user_id,
    cost_type,
    category_id,
    description,
    quantity,
    unit_cost,
    embedding_job_id,
    metadata
  ) VALUES (
    v_job.organization_id,
    v_job.case_id,
    v_job.started_by,
    'embedding',
    v_category_id,
    format('Embedding job: %s chunks, %s tokens', v_job.processed_chunks, v_job.total_tokens),
    v_job.total_tokens,
    v_config.cost_per_1k_tokens / 1000.0,
    p_embedding_job_id,
    jsonb_build_object(
      'model', v_config.model,
      'chunks_processed', v_job.processed_chunks,
      'config_name', v_config.name
    )
  );

  RETURN v_total_cost;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- CALCULATE STORAGE COSTS
-- =====================================================================

CREATE OR REPLACE FUNCTION calculate_storage_costs(
  p_organization_id UUID,
  p_cost_per_gb_month DECIMAL(10,6) DEFAULT 0.023,
  p_billing_month DATE DEFAULT CURRENT_DATE
)
RETURNS UUID AS $$
DECLARE
  v_total_gb DECIMAL(15,6);
  v_cost_entry_id UUID;
  v_category_id UUID;
BEGIN
  -- Calculate total storage for organization
  SELECT COALESCE(SUM(file_size), 0) / 1024.0 / 1024.0 / 1024.0
  INTO v_total_gb
  FROM documents d
  JOIN legal_cases lc ON d.case_id = lc.id
  WHERE lc.organization_id = p_organization_id
    AND d.is_deleted = false;

  -- Get cost category
  SELECT id INTO v_category_id
  FROM cost_categories
  WHERE name = 'Storage' AND is_active = true
  LIMIT 1;

  -- Create cost entry (monthly)
  INSERT INTO cost_entries (
    organization_id,
    cost_type,
    category_id,
    description,
    quantity,
    unit_cost,
    cost_date,
    metadata
  ) VALUES (
    p_organization_id,
    'storage',
    v_category_id,
    format('Storage for %s', to_char(p_billing_month, 'Month YYYY')),
    v_total_gb,
    p_cost_per_gb_month,
    p_billing_month,
    jsonb_build_object(
      'total_gb', v_total_gb,
      'billing_month', p_billing_month
    )
  ) RETURNING id INTO v_cost_entry_id;

  RETURN v_cost_entry_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- CALCULATE PROJECTED COSTS
-- =====================================================================

CREATE OR REPLACE FUNCTION calculate_projected_costs(
  p_case_id UUID,
  p_projection_days INTEGER DEFAULT 30,
  p_lookback_days INTEGER DEFAULT 30
)
RETURNS TABLE (
  cost_type cost_type,
  current_daily_avg NUMERIC,
  projected_cost NUMERIC,
  confidence TEXT
) AS $$
BEGIN
  RETURN QUERY
  WITH daily_costs AS (
    SELECT
      ce.cost_type,
      DATE(ce.cost_date) as date,
      SUM(ce.total_cost) as daily_cost
    FROM cost_entries ce
    WHERE ce.case_id = p_case_id
      AND ce.cost_date >= CURRENT_DATE - p_lookback_days
    GROUP BY ce.cost_type, DATE(ce.cost_date)
  ),
  averages AS (
    SELECT
      dc.cost_type,
      AVG(dc.daily_cost) as avg_daily,
      STDDEV(dc.daily_cost) as stddev_daily,
      COUNT(*) as data_points
    FROM daily_costs dc
    GROUP BY dc.cost_type
  )
  SELECT
    a.cost_type,
    ROUND(a.avg_daily, 6),
    ROUND(a.avg_daily * p_projection_days, 6),
    CASE
      WHEN a.data_points >= 20 AND a.stddev_daily / NULLIF(a.avg_daily, 0) < 0.3 THEN 'high'
      WHEN a.data_points >= 10 THEN 'medium'
      ELSE 'low'
    END
  FROM averages a
  ORDER BY a.avg_daily DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- ALLOCATE SHARED COSTS
-- =====================================================================

CREATE OR REPLACE FUNCTION allocate_shared_cost(
  p_cost_entry_id UUID,
  p_user_allocations JSONB -- {"user_id": percent, ...}
)
RETURNS INTEGER AS $$
DECLARE
  v_cost_entry RECORD;
  v_user_id UUID;
  v_percent DECIMAL(5,2);
  v_allocated_amount DECIMAL(15,6);
  v_total_percent DECIMAL(5,2) := 0;
  v_allocation_count INTEGER := 0;
BEGIN
  -- Get cost entry
  SELECT * INTO v_cost_entry
  FROM cost_entries
  WHERE id = p_cost_entry_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Cost entry not found: %', p_cost_entry_id;
  END IF;

  -- Validate total percentage
  SELECT SUM((value)::TEXT::DECIMAL) INTO v_total_percent
  FROM jsonb_each(p_user_allocations);

  IF v_total_percent != 100 THEN
    RAISE EXCEPTION 'Total allocation percentage must equal 100, got: %', v_total_percent;
  END IF;

  -- Create allocations
  FOR v_user_id, v_percent IN
    SELECT key::UUID, (value)::TEXT::DECIMAL
    FROM jsonb_each(p_user_allocations)
  LOOP
    v_allocated_amount := v_cost_entry.total_cost * (v_percent / 100.0);

    INSERT INTO user_cost_allocations (
      cost_entry_id,
      user_id,
      allocation_percent,
      allocated_amount
    ) VALUES (
      p_cost_entry_id,
      v_user_id,
      v_percent,
      v_allocated_amount
    );

    v_allocation_count := v_allocation_count + 1;
  END LOOP;

  RETURN v_allocation_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- RECONCILE BUDGET
-- =====================================================================

CREATE OR REPLACE FUNCTION reconcile_case_budget(p_case_id UUID)
RETURNS TABLE (
  budget_id UUID,
  budget_name TEXT,
  calculated_spent NUMERIC,
  recorded_spent NUMERIC,
  difference NUMERIC,
  status TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    cb.id,
    cb.budget_name,
    COALESCE(SUM(ce.total_cost), 0) as calculated_spent,
    cb.spent_amount as recorded_spent,
    COALESCE(SUM(ce.total_cost), 0) - cb.spent_amount as difference,
    CASE
      WHEN ABS(COALESCE(SUM(ce.total_cost), 0) - cb.spent_amount) < 0.01 THEN 'balanced'
      WHEN COALESCE(SUM(ce.total_cost), 0) > cb.spent_amount THEN 'understated'
      ELSE 'overstated'
    END as status
  FROM case_budgets cb
  LEFT JOIN cost_entries ce ON cb.case_id = ce.case_id
  WHERE cb.case_id = p_case_id
    AND cb.is_active = true
  GROUP BY cb.id, cb.budget_name, cb.spent_amount;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- CALCULATE COST PER DOCUMENT
-- =====================================================================

CREATE OR REPLACE FUNCTION calculate_cost_per_document(p_case_id UUID)
RETURNS TABLE (
  document_id UUID,
  document_title TEXT,
  total_cost NUMERIC,
  embedding_cost NUMERIC,
  processing_cost NUMERIC,
  storage_cost NUMERIC,
  page_count INTEGER,
  cost_per_page NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    COALESCE(SUM(ce.total_cost), 0) as total_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type = 'embedding'), 0) as embedding_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type = 'processing'), 0) as processing_cost,
    COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type = 'storage'), 0) as storage_cost,
    d.page_count,
    CASE
      WHEN d.page_count > 0 THEN COALESCE(SUM(ce.total_cost), 0) / d.page_count
      ELSE 0
    END as cost_per_page
  FROM documents d
  LEFT JOIN cost_entries ce ON d.id = ce.document_id
  WHERE d.case_id = p_case_id
  GROUP BY d.id, d.title, d.page_count
  HAVING SUM(ce.total_cost) > 0
  ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- AUTO-GENERATE COST ESTIMATES
-- =====================================================================

CREATE OR REPLACE FUNCTION estimate_document_costs(
  p_file_size_bytes BIGINT,
  p_page_count INTEGER,
  p_embedding_model TEXT DEFAULT 'openai-ada-002'
)
RETURNS TABLE (
  cost_type TEXT,
  estimated_cost NUMERIC,
  basis TEXT
) AS $$
DECLARE
  v_config RECORD;
  v_estimated_tokens INTEGER;
BEGIN
  -- Get embedding config
  SELECT * INTO v_config
  FROM embedding_configs
  WHERE name = p_embedding_model AND is_active = true
  LIMIT 1;

  -- Estimate tokens (rough: 1 page ≈ 500 tokens)
  v_estimated_tokens := p_page_count * 500;

  RETURN QUERY

  -- Embedding cost
  SELECT
    'embedding'::TEXT,
    ((v_estimated_tokens / 1000.0) * v_config.cost_per_1k_tokens)::NUMERIC,
    format('%s tokens × $%s per 1k', v_estimated_tokens, v_config.cost_per_1k_tokens)::TEXT

  UNION ALL

  -- Storage cost (monthly for 1 year)
  SELECT
    'storage_annual'::TEXT,
    ((p_file_size_bytes / 1024.0 / 1024.0 / 1024.0) * 0.023 * 12)::NUMERIC,
    format('%s GB × $0.023/month × 12 months', ROUND((p_file_size_bytes / 1024.0 / 1024.0 / 1024.0)::NUMERIC, 4))::TEXT

  UNION ALL

  -- Processing cost (estimate: $0.01 per page)
  SELECT
    'processing'::TEXT,
    (p_page_count * 0.01)::NUMERIC,
    format('%s pages × $0.01/page', p_page_count)::TEXT;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- BULK COST OPERATIONS
-- =====================================================================

-- Recalculate all costs for a case (use with caution)
CREATE OR REPLACE FUNCTION recalculate_case_costs(p_case_id UUID)
RETURNS JSONB AS $$
DECLARE
  v_result JSONB;
  v_job RECORD;
  v_total_recalculated NUMERIC := 0;
BEGIN
  -- Recalculate embedding costs
  FOR v_job IN
    SELECT id FROM embedding_jobs
    WHERE case_id = p_case_id AND status = 'completed'
  LOOP
    v_total_recalculated := v_total_recalculated + batch_calculate_embedding_costs(v_job.id);
  END LOOP;

  -- Update budget spent amounts
  PERFORM update_budget_spent_amount()
  FROM cost_entries
  WHERE case_id = p_case_id
  LIMIT 1;

  v_result := jsonb_build_object(
    'case_id', p_case_id,
    'recalculated_amount', v_total_recalculated,
    'timestamp', NOW()
  );

  RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON FUNCTION calculate_attorney_time_cost IS 'Calculate and record attorney/paralegal time costs';
COMMENT ON FUNCTION calculate_api_cost IS 'Calculate and record API service costs';
COMMENT ON FUNCTION batch_calculate_embedding_costs IS 'Calculate costs for completed embedding job';
COMMENT ON FUNCTION calculate_storage_costs IS 'Calculate monthly storage costs for organization';
COMMENT ON FUNCTION calculate_projected_costs IS 'Project future costs based on historical trends';
COMMENT ON FUNCTION allocate_shared_cost IS 'Allocate a cost entry across multiple users';
COMMENT ON FUNCTION reconcile_case_budget IS 'Reconcile calculated vs recorded budget amounts';
COMMENT ON FUNCTION estimate_document_costs IS 'Estimate costs before processing a document';
