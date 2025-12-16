-- =====================================================================
-- COST TRACKING & BILLING
-- Purpose: Track costs per attorney, agent, task, and case
-- Version: 1.0.0
-- Supports: Real-time cost tracking, budget alerts, detailed billing
-- =====================================================================

-- =====================================================================
-- ENUM TYPES
-- =====================================================================

CREATE TYPE cost_type AS ENUM (
  'api_call',
  'embedding',
  'llm_query',
  'storage',
  'processing',
  'attorney_time',
  'paralegal_time',
  'expert_time',
  'third_party_service',
  'other'
);

CREATE TYPE billing_status AS ENUM (
  'unbilled',
  'billed',
  'paid',
  'disputed',
  'written_off'
);

-- =====================================================================
-- TABLE: cost_categories (Categorize costs for reporting)
-- =====================================================================

CREATE TABLE cost_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  parent_category_id UUID REFERENCES cost_categories(id) ON DELETE SET NULL,
  default_rate DECIMAL(10,6),
  is_billable BOOLEAN DEFAULT true,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default categories
INSERT INTO cost_categories (name, description, default_rate, is_billable) VALUES
  ('AI Services', 'AI and ML API costs', 0, true),
  ('Embeddings', 'Vector embedding generation', 0.0001, true),
  ('LLM Queries', 'Large language model queries', 0.002, true),
  ('Legal Services', 'Attorney and paralegal time', 150.00, true),
  ('Storage', 'Document storage costs', 0, false),
  ('Processing', 'Document processing and OCR', 0, true);

CREATE INDEX idx_cost_categories_active ON cost_categories(is_active) WHERE is_active = true;

-- =====================================================================
-- TABLE: cost_entries (Individual cost records)
-- =====================================================================

CREATE TABLE cost_entries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  case_id UUID REFERENCES legal_cases(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Cost details
  cost_type cost_type NOT NULL,
  category_id UUID REFERENCES cost_categories(id),
  description TEXT NOT NULL,

  -- Amounts
  quantity DECIMAL(15,4) DEFAULT 1.0 CHECK (quantity >= 0),
  unit_cost DECIMAL(10,6) NOT NULL CHECK (unit_cost >= 0),
  total_cost DECIMAL(15,6) GENERATED ALWAYS AS (quantity * unit_cost) STORED,

  -- Related entities
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
  embedding_job_id UUID REFERENCES embedding_jobs(id) ON DELETE SET NULL,

  -- Billing
  billing_status billing_status DEFAULT 'unbilled',
  invoice_id UUID, -- Reference to external invoice system
  billed_at TIMESTAMPTZ,
  paid_at TIMESTAMPTZ,

  -- Time tracking (for hourly work)
  time_started TIMESTAMPTZ,
  time_ended TIMESTAMPTZ,
  duration_minutes INTEGER,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,
  tags TEXT[],

  -- Timestamps
  cost_date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT cost_entries_time_valid CHECK (
    time_ended IS NULL OR time_started IS NULL OR time_ended >= time_started
  )
);

-- Partitioning by month for large datasets
CREATE INDEX idx_cost_entries_org ON cost_entries(organization_id, cost_date DESC);
CREATE INDEX idx_cost_entries_case ON cost_entries(case_id, cost_date DESC);
CREATE INDEX idx_cost_entries_user ON cost_entries(user_id, cost_date DESC);
CREATE INDEX idx_cost_entries_billing_status ON cost_entries(billing_status);
CREATE INDEX idx_cost_entries_type ON cost_entries(cost_type);
CREATE INDEX idx_cost_entries_category ON cost_entries(category_id);
CREATE INDEX idx_cost_entries_date ON cost_entries(cost_date DESC);
CREATE INDEX idx_cost_entries_document ON cost_entries(document_id);
CREATE INDEX idx_cost_entries_tags ON cost_entries USING gin(tags);

-- =====================================================================
-- TABLE: case_budgets (Budget management for cases)
-- =====================================================================

CREATE TABLE case_budgets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Budget details
  budget_name TEXT NOT NULL,
  total_budget DECIMAL(15,2) NOT NULL CHECK (total_budget >= 0),
  budget_period TEXT CHECK (budget_period IN ('monthly', 'quarterly', 'annual', 'case_lifetime')),

  -- Period dates
  start_date DATE NOT NULL,
  end_date DATE,

  -- Spending tracking (computed via triggers)
  spent_amount DECIMAL(15,6) DEFAULT 0.00,
  remaining_amount DECIMAL(15,6) GENERATED ALWAYS AS (total_budget - spent_amount) STORED,
  percent_used DECIMAL(5,2) GENERATED ALWAYS AS (
    CASE WHEN total_budget > 0 THEN (spent_amount / total_budget * 100) ELSE 0 END
  ) STORED,

  -- Alerts
  alert_threshold_percent DECIMAL(5,2) DEFAULT 80.00 CHECK (alert_threshold_percent >= 0 AND alert_threshold_percent <= 100),
  alert_triggered BOOLEAN DEFAULT false,
  alert_triggered_at TIMESTAMPTZ,

  -- Status
  is_active BOOLEAN DEFAULT true,
  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  CONSTRAINT case_budgets_dates_valid CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_case_budgets_case ON case_budgets(case_id);
CREATE INDEX idx_case_budgets_active ON case_budgets(is_active) WHERE is_active = true;
CREATE INDEX idx_case_budgets_alert ON case_budgets(alert_triggered) WHERE alert_triggered = true;

-- =====================================================================
-- TABLE: user_cost_allocations (Allocate costs across users/teams)
-- =====================================================================

CREATE TABLE user_cost_allocations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cost_entry_id UUID NOT NULL REFERENCES cost_entries(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  allocation_percent DECIMAL(5,2) NOT NULL CHECK (allocation_percent > 0 AND allocation_percent <= 100),
  allocated_amount DECIMAL(15,6),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT user_cost_allocations_unique UNIQUE (cost_entry_id, user_id)
);

CREATE INDEX idx_user_cost_allocations_cost ON user_cost_allocations(cost_entry_id);
CREATE INDEX idx_user_cost_allocations_user ON user_cost_allocations(user_id);

-- =====================================================================
-- TABLE: budget_alerts (Alert history for budget overruns)
-- =====================================================================

CREATE TABLE budget_alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_budget_id UUID NOT NULL REFERENCES case_budgets(id) ON DELETE CASCADE,
  alert_type TEXT NOT NULL CHECK (alert_type IN ('threshold_reached', 'budget_exceeded', 'forecast_warning')),
  severity TEXT DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'critical')),
  message TEXT NOT NULL,
  current_spent DECIMAL(15,6),
  current_budget DECIMAL(15,2),
  percent_used DECIMAL(5,2),

  -- Notification tracking
  notified_users UUID[],
  notification_sent_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  acknowledged_at TIMESTAMPTZ,
  acknowledged_by UUID REFERENCES users(id)
);

CREATE INDEX idx_budget_alerts_budget ON budget_alerts(case_budget_id);
CREATE INDEX idx_budget_alerts_created ON budget_alerts(created_at DESC);
CREATE INDEX idx_budget_alerts_unacknowledged ON budget_alerts(acknowledged_at) WHERE acknowledged_at IS NULL;

-- =====================================================================
-- TABLE: cost_forecasts (Predict future costs based on trends)
-- =====================================================================

CREATE TABLE cost_forecasts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  forecast_date DATE NOT NULL,
  forecast_period TEXT NOT NULL CHECK (forecast_period IN ('daily', 'weekly', 'monthly', 'case_completion')),

  -- Historical data used
  historical_days INTEGER NOT NULL,
  data_points_used INTEGER,

  -- Forecast
  predicted_cost DECIMAL(15,6),
  confidence_level DECIMAL(5,2) CHECK (confidence_level >= 0 AND confidence_level <= 100),

  -- Breakdown by type
  cost_breakdown JSONB DEFAULT '{}'::jsonb,

  -- Metadata
  model_used TEXT,
  parameters JSONB,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_cost_forecasts_case ON cost_forecasts(case_id, forecast_date DESC);

-- =====================================================================
-- FUNCTIONS FOR COST TRACKING
-- =====================================================================

-- Function to calculate total costs for a case
CREATE OR REPLACE FUNCTION calculate_case_costs(
  p_case_id UUID,
  p_start_date DATE DEFAULT NULL,
  p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
  total_cost DECIMAL(15,6),
  by_type JSONB,
  by_user JSONB,
  entry_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COALESCE(SUM(ce.total_cost), 0) as total_cost,
    jsonb_object_agg(
      ce.cost_type,
      COALESCE(SUM(ce.total_cost), 0)
    ) FILTER (WHERE ce.cost_type IS NOT NULL) as by_type,
    jsonb_object_agg(
      u.full_name,
      COALESCE(SUM(ce.total_cost), 0)
    ) FILTER (WHERE u.full_name IS NOT NULL) as by_user,
    COUNT(ce.id) as entry_count
  FROM cost_entries ce
  LEFT JOIN users u ON ce.user_id = u.id
  WHERE
    ce.case_id = p_case_id AND
    (p_start_date IS NULL OR ce.cost_date >= p_start_date) AND
    (p_end_date IS NULL OR ce.cost_date <= p_end_date);
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to update budget spent amount
CREATE OR REPLACE FUNCTION update_budget_spent_amount()
RETURNS TRIGGER AS $$
DECLARE
  v_budget_id UUID;
  v_total_spent DECIMAL(15,6);
  v_budget_total DECIMAL(15,2);
  v_alert_threshold DECIMAL(5,2);
  v_percent_used DECIMAL(5,2);
BEGIN
  -- Get active budgets for this case
  FOR v_budget_id, v_budget_total, v_alert_threshold IN
    SELECT id, total_budget, alert_threshold_percent
    FROM case_budgets
    WHERE
      case_id = COALESCE(NEW.case_id, OLD.case_id) AND
      is_active = true AND
      (end_date IS NULL OR end_date >= CURRENT_DATE)
  LOOP
    -- Calculate total spent for this budget
    SELECT COALESCE(SUM(total_cost), 0)
    INTO v_total_spent
    FROM cost_entries
    WHERE case_id = COALESCE(NEW.case_id, OLD.case_id);

    -- Update budget
    UPDATE case_budgets
    SET
      spent_amount = v_total_spent,
      updated_at = NOW()
    WHERE id = v_budget_id;

    -- Check if alert threshold reached
    v_percent_used := (v_total_spent / v_budget_total * 100);

    IF v_percent_used >= v_alert_threshold AND NOT (
      SELECT alert_triggered FROM case_budgets WHERE id = v_budget_id
    ) THEN
      -- Trigger alert
      UPDATE case_budgets
      SET
        alert_triggered = true,
        alert_triggered_at = NOW()
      WHERE id = v_budget_id;

      -- Create alert record
      INSERT INTO budget_alerts (
        case_budget_id,
        alert_type,
        severity,
        message,
        current_spent,
        current_budget,
        percent_used
      ) VALUES (
        v_budget_id,
        CASE
          WHEN v_percent_used >= 100 THEN 'budget_exceeded'
          ELSE 'threshold_reached'
        END,
        CASE
          WHEN v_percent_used >= 100 THEN 'critical'
          WHEN v_percent_used >= 90 THEN 'warning'
          ELSE 'info'
        END,
        format('Budget alert: %s%% of budget used', ROUND(v_percent_used, 2)),
        v_total_spent,
        v_budget_total,
        v_percent_used
      );
    END IF;
  END LOOP;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to record embedding costs automatically
CREATE OR REPLACE FUNCTION record_embedding_cost()
RETURNS TRIGGER AS $$
DECLARE
  v_category_id UUID;
  v_user_id UUID;
BEGIN
  IF NEW.cost IS NOT NULL AND NEW.cost > 0 THEN
    -- Get embedding category
    SELECT id INTO v_category_id
    FROM cost_categories
    WHERE name = 'Embeddings' AND is_active = true
    LIMIT 1;

    -- Get user from embedding job
    SELECT started_by INTO v_user_id
    FROM embedding_jobs
    WHERE id = NEW.id;

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
    )
    SELECT
      ej.organization_id,
      ej.case_id,
      v_user_id,
      'embedding',
      v_category_id,
      format('Embedding job: %s tokens', NEW.total_tokens),
      NEW.total_tokens,
      NEW.total_cost / NULLIF(NEW.total_tokens, 0),
      NEW.id,
      jsonb_build_object(
        'model', (SELECT model FROM embedding_configs WHERE id = NEW.config_id),
        'chunks_processed', NEW.processed_chunks
      )
    FROM embedding_jobs ej
    WHERE ej.id = NEW.id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- TRIGGERS
-- =====================================================================

CREATE TRIGGER update_cost_entries_updated_at BEFORE UPDATE ON cost_entries
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_case_budgets_updated_at BEFORE UPDATE ON case_budgets
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update budget spent amount when costs change
CREATE TRIGGER trigger_update_budget_spent
  AFTER INSERT OR UPDATE OR DELETE ON cost_entries
  FOR EACH ROW
  EXECUTE FUNCTION update_budget_spent_amount();

-- Trigger to automatically record embedding costs
CREATE TRIGGER trigger_record_embedding_cost
  AFTER UPDATE ON embedding_jobs
  FOR EACH ROW
  WHEN (NEW.status = 'completed' AND NEW.total_cost > 0)
  EXECUTE FUNCTION record_embedding_cost();

-- =====================================================================
-- VIEWS FOR REPORTING
-- =====================================================================

-- View: Cost summary by case
CREATE OR REPLACE VIEW v_cost_summary_by_case AS
SELECT
  lc.id as case_id,
  lc.case_number,
  lc.title,
  COUNT(DISTINCT ce.id) as total_entries,
  COALESCE(SUM(ce.total_cost), 0) as total_cost,
  COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.billing_status = 'unbilled'), 0) as unbilled_cost,
  COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.billing_status = 'billed'), 0) as billed_cost,
  COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.billing_status = 'paid'), 0) as paid_cost,
  lc.total_budget,
  CASE
    WHEN lc.total_budget > 0 THEN
      (COALESCE(SUM(ce.total_cost), 0) / lc.total_budget * 100)
    ELSE 0
  END as budget_percent_used,
  MAX(ce.created_at) as last_cost_entry
FROM legal_cases lc
LEFT JOIN cost_entries ce ON lc.id = ce.case_id
GROUP BY lc.id, lc.case_number, lc.title, lc.total_budget;

-- View: Cost summary by user
CREATE OR REPLACE VIEW v_cost_summary_by_user AS
SELECT
  u.id as user_id,
  u.full_name,
  u.role,
  u.organization_id,
  COUNT(DISTINCT ce.id) as total_entries,
  COALESCE(SUM(ce.total_cost), 0) as total_cost,
  COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('attorney_time', 'paralegal_time')), 0) as billable_hours_cost,
  COALESCE(SUM(ce.total_cost) FILTER (WHERE ce.cost_type IN ('api_call', 'embedding', 'llm_query')), 0) as ai_service_cost,
  COALESCE(SUM(ce.duration_minutes), 0) as total_minutes,
  MAX(ce.created_at) as last_cost_entry
FROM users u
LEFT JOIN cost_entries ce ON u.id = ce.user_id
GROUP BY u.id, u.full_name, u.role, u.organization_id;

-- View: Monthly cost trends
CREATE OR REPLACE VIEW v_cost_trends_monthly AS
SELECT
  DATE_TRUNC('month', ce.cost_date) as month,
  ce.case_id,
  lc.case_number,
  ce.cost_type,
  COUNT(*) as entry_count,
  SUM(ce.total_cost) as total_cost,
  AVG(ce.total_cost) as avg_cost
FROM cost_entries ce
JOIN legal_cases lc ON ce.case_id = lc.id
GROUP BY DATE_TRUNC('month', ce.cost_date), ce.case_id, lc.case_number, ce.cost_type
ORDER BY month DESC, total_cost DESC;

-- View: Budget status overview
CREATE OR REPLACE VIEW v_budget_status AS
SELECT
  cb.id,
  cb.case_id,
  lc.case_number,
  lc.title as case_title,
  cb.budget_name,
  cb.total_budget,
  cb.spent_amount,
  cb.remaining_amount,
  cb.percent_used,
  cb.alert_threshold_percent,
  cb.alert_triggered,
  cb.is_active,
  CASE
    WHEN cb.percent_used >= 100 THEN 'exceeded'
    WHEN cb.percent_used >= cb.alert_threshold_percent THEN 'warning'
    WHEN cb.percent_used >= 75 THEN 'caution'
    ELSE 'good'
  END as budget_health,
  cb.start_date,
  cb.end_date,
  CASE
    WHEN cb.end_date IS NOT NULL THEN (cb.end_date - CURRENT_DATE)
    ELSE NULL
  END as days_remaining
FROM case_budgets cb
JOIN legal_cases lc ON cb.case_id = lc.id;

-- =====================================================================
-- PERFORMANCE OPTIMIZATION
-- =====================================================================

ANALYZE cost_categories;
ANALYZE cost_entries;
ANALYZE case_budgets;
ANALYZE budget_alerts;

-- =====================================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================================

COMMENT ON TABLE cost_categories IS 'Categories for organizing and classifying costs';
COMMENT ON TABLE cost_entries IS 'Individual cost records for tracking all expenses';
COMMENT ON TABLE case_budgets IS 'Budget allocations and tracking for legal cases';
COMMENT ON TABLE user_cost_allocations IS 'Allocate shared costs across multiple users';
COMMENT ON TABLE budget_alerts IS 'Alert history for budget thresholds and overruns';
COMMENT ON TABLE cost_forecasts IS 'Predicted future costs based on historical trends';

COMMENT ON FUNCTION calculate_case_costs IS 'Calculate total costs for a case with optional date range';
COMMENT ON FUNCTION update_budget_spent_amount IS 'Trigger function to update budget spent amounts and generate alerts';
COMMENT ON FUNCTION record_embedding_cost IS 'Automatically create cost entries for embedding jobs';
