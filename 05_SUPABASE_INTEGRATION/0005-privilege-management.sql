-- =====================================================================
-- PRIVILEGE DETECTION & MANAGEMENT
-- Purpose: Automated privilege detection, flagging, and management
-- Version: 1.0.0
-- Supports: Attorney-client privilege, work product, settlement negotiations
-- =====================================================================

-- =====================================================================
-- TABLE: privilege_detection_rules (Rules for automatic detection)
-- =====================================================================

CREATE TABLE privilege_detection_rules (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Rule details
  rule_name TEXT NOT NULL,
  description TEXT,
  privilege_type privilege_type NOT NULL,
  priority INTEGER DEFAULT 0,

  -- Detection criteria
  keywords TEXT[], -- Keywords that trigger privilege flag
  patterns TEXT[], -- Regex patterns for detection
  sender_domains TEXT[], -- Email domains (e.g., @lawfirm.com)
  recipient_domains TEXT[],
  author_patterns TEXT[],

  -- Document metadata criteria
  metadata_conditions JSONB, -- {"document_type": "email", "subject_contains": ["privileged"]}

  -- Machine learning
  use_ml_model BOOLEAN DEFAULT false,
  ml_model_name TEXT,
  confidence_threshold DECIMAL(5,4) DEFAULT 0.85,

  -- Actions
  auto_flag BOOLEAN DEFAULT true,
  require_review BOOLEAN DEFAULT true,
  notify_users UUID[],

  -- Status
  is_active BOOLEAN DEFAULT true,
  last_run TIMESTAMPTZ,
  documents_flagged INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  CONSTRAINT privilege_detection_rules_name_org_unique UNIQUE (organization_id, rule_name)
);

CREATE INDEX idx_privilege_detection_rules_org ON privilege_detection_rules(organization_id);
CREATE INDEX idx_privilege_detection_rules_active ON privilege_detection_rules(is_active) WHERE is_active = true;
CREATE INDEX idx_privilege_detection_rules_type ON privilege_detection_rules(privilege_type);

-- Insert default detection rules
INSERT INTO privilege_detection_rules (
  organization_id,
  rule_name,
  description,
  privilege_type,
  keywords,
  patterns,
  priority,
  auto_flag,
  require_review
)
SELECT
  o.id,
  'Attorney-Client Communication',
  'Detect communications between attorney and client',
  'attorney_client',
  ARRAY['attorney-client', 'privileged', 'confidential communication', 'legal advice', 'in confidence'],
  ARRAY[
    '\y(attorney|lawyer)\s+(client|privilege)\y',
    '\yprivileged\s+and\s+confidential\y',
    '\ylegal\s+advice\y'
  ],
  10,
  true,
  true
FROM organizations o;

INSERT INTO privilege_detection_rules (
  organization_id,
  rule_name,
  description,
  privilege_type,
  keywords,
  patterns,
  priority,
  auto_flag,
  require_review
)
SELECT
  o.id,
  'Work Product Doctrine',
  'Detect attorney work product',
  'work_product',
  ARRAY['work product', 'trial preparation', 'litigation strategy', 'attorney notes', 'draft pleading'],
  ARRAY[
    '\ywork\s+product\y',
    '\ytrial\s+preparation\y',
    '\ylitigation\s+strategy\y'
  ],
  8,
  true,
  true
FROM organizations o;

INSERT INTO privilege_detection_rules (
  organization_id,
  rule_name,
  description,
  privilege_type,
  keywords,
  patterns,
  priority,
  auto_flag,
  require_review
)
SELECT
  o.id,
  'Settlement Negotiations',
  'Detect settlement negotiation communications',
  'settlement_negotiation',
  ARRAY['settlement offer', 'settlement discussion', 'without prejudice', 'confidential settlement', 'mediation'],
  ARRAY[
    '\ysettlement\s+(offer|discussion|negotiation)\y',
    '\ywithout\s+prejudice\y',
    '\yFRE\s+408\y'
  ],
  7,
  true,
  true
FROM organizations o;

-- =====================================================================
-- TABLE: privilege_detections (Results of privilege detection)
-- =====================================================================

CREATE TABLE privilege_detections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  rule_id UUID REFERENCES privilege_detection_rules(id) ON DELETE SET NULL,

  -- Detection details
  detected_privilege_type privilege_type NOT NULL,
  detection_method TEXT NOT NULL CHECK (detection_method IN (
    'rule_based', 'ml_model', 'manual', 'hybrid'
  )),
  confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),

  -- Evidence
  matched_keywords TEXT[],
  matched_patterns TEXT[],
  matching_text_snippets TEXT[],
  evidence_locations JSONB, -- Page numbers, positions, etc.

  -- Status
  status TEXT DEFAULT 'pending_review' CHECK (status IN (
    'pending_review', 'confirmed', 'rejected', 'escalated'
  )),

  -- Review
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ,
  review_notes TEXT,
  final_determination privilege_type,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT privilege_detections_confidence_valid CHECK (
    detection_method = 'manual' OR confidence_score IS NOT NULL
  )
);

CREATE INDEX idx_privilege_detections_document ON privilege_detections(document_id);
CREATE INDEX idx_privilege_detections_case ON privilege_detections(case_id);
CREATE INDEX idx_privilege_detections_rule ON privilege_detections(rule_id);
CREATE INDEX idx_privilege_detections_status ON privilege_detections(status);
CREATE INDEX idx_privilege_detections_pending ON privilege_detections(status)
  WHERE status = 'pending_review';
CREATE INDEX idx_privilege_detections_type ON privilege_detections(detected_privilege_type);

-- =====================================================================
-- TABLE: privilege_waivers (Track privilege waivers)
-- =====================================================================

CREATE TABLE privilege_waivers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Waiver details
  waiver_type TEXT NOT NULL CHECK (waiver_type IN (
    'express', 'implied', 'subject_matter', 'inadvertent_disclosure', 'crime_fraud_exception'
  )),
  waiver_reason TEXT NOT NULL,
  scope TEXT, -- Full waiver, partial waiver, etc.

  -- Authorization
  authorized_by UUID NOT NULL REFERENCES users(id),
  authorized_at TIMESTAMPTZ DEFAULT NOW(),
  authorization_evidence JSONB,

  -- Clawback
  clawback_attempted BOOLEAN DEFAULT false,
  clawback_successful BOOLEAN,
  clawback_date TIMESTAMPTZ,
  clawback_notes TEXT,

  -- Status
  is_active BOOLEAN DEFAULT true,
  revoked_at TIMESTAMPTZ,
  revoked_by UUID REFERENCES users(id),
  revocation_reason TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_privilege_waivers_document ON privilege_waivers(document_id);
CREATE INDEX idx_privilege_waivers_case ON privilege_waivers(case_id);
CREATE INDEX idx_privilege_waivers_active ON privilege_waivers(is_active) WHERE is_active = true;

-- =====================================================================
-- TABLE: privilege_logs (Complete privilege log for production)
-- =====================================================================

CREATE TABLE privilege_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

  -- Document identification
  document_number TEXT,
  bates_number TEXT,
  document_date DATE,

  -- Description
  description TEXT NOT NULL,
  document_type TEXT,

  -- Parties
  author TEXT,
  recipients TEXT[],
  cc_recipients TEXT[],
  bcc_recipients TEXT[],

  -- Privilege assertion
  privilege_type privilege_type NOT NULL,
  privilege_basis TEXT NOT NULL,
  detailed_justification TEXT,

  -- Production status
  withheld BOOLEAN DEFAULT true,
  withheld_reason TEXT,
  produced_in_redacted_form BOOLEAN DEFAULT false,
  redaction_description TEXT,

  -- Metadata
  page_count INTEGER,
  attachment_count INTEGER,
  metadata JSONB DEFAULT '{}'::jsonb,

  -- Review
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ,
  approved_by UUID REFERENCES users(id),
  approved_at TIMESTAMPTZ,

  -- Export
  included_in_production BOOLEAN DEFAULT false,
  production_date DATE,
  production_number TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT privilege_logs_document_case_unique UNIQUE (case_id, document_id)
);

CREATE INDEX idx_privilege_logs_case ON privilege_logs(case_id);
CREATE INDEX idx_privilege_logs_document ON privilege_logs(document_id);
CREATE INDEX idx_privilege_logs_type ON privilege_logs(privilege_type);
CREATE INDEX idx_privilege_logs_withheld ON privilege_logs(withheld);
CREATE INDEX idx_privilege_logs_production ON privilege_logs(production_number);

-- =====================================================================
-- TABLE: privilege_review_queue (Review workflow for flagged documents)
-- =====================================================================

CREATE TABLE privilege_review_queue (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  detection_id UUID REFERENCES privilege_detections(id) ON DELETE SET NULL,

  -- Queue details
  priority INTEGER DEFAULT 0,
  queue_date TIMESTAMPTZ DEFAULT NOW(),
  due_date TIMESTAMPTZ,

  -- Assignment
  assigned_to UUID REFERENCES users(id),
  assigned_at TIMESTAMPTZ,

  -- Status
  status TEXT DEFAULT 'pending' CHECK (status IN (
    'pending', 'in_review', 'completed', 'escalated', 'deferred'
  )),

  -- Review
  review_started_at TIMESTAMPTZ,
  review_completed_at TIMESTAMPTZ,
  review_duration_minutes INTEGER,
  decision TEXT CHECK (decision IN ('privileged', 'not_privileged', 'uncertain', 'escalate')),
  decision_notes TEXT,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT privilege_review_queue_document_unique UNIQUE (document_id)
);

CREATE INDEX idx_privilege_review_queue_case ON privilege_review_queue(case_id);
CREATE INDEX idx_privilege_review_queue_assigned ON privilege_review_queue(assigned_to, status);
CREATE INDEX idx_privilege_review_queue_status ON privilege_review_queue(status);
CREATE INDEX idx_privilege_review_queue_priority ON privilege_review_queue(priority DESC, queue_date);
CREATE INDEX idx_privilege_review_queue_due ON privilege_review_queue(due_date) WHERE due_date IS NOT NULL;

-- =====================================================================
-- FUNCTIONS FOR PRIVILEGE MANAGEMENT
-- =====================================================================

-- Function to run privilege detection on a document
CREATE OR REPLACE FUNCTION detect_privilege(p_document_id UUID)
RETURNS TABLE (
  rule_id UUID,
  privilege_type privilege_type,
  confidence DECIMAL(5,4),
  matched_keywords TEXT[],
  matched_patterns TEXT[]
) AS $$
DECLARE
  v_doc RECORD;
  v_rule RECORD;
  v_matched_keywords TEXT[];
  v_matched_patterns TEXT[];
  v_confidence DECIMAL(5,4);
  v_detection_id UUID;
BEGIN
  -- Get document content
  SELECT * INTO v_doc FROM documents WHERE id = p_document_id;

  IF v_doc IS NULL THEN
    RAISE EXCEPTION 'Document not found: %', p_document_id;
  END IF;

  -- Get active detection rules for this organization
  FOR v_rule IN
    SELECT * FROM privilege_detection_rules
    WHERE organization_id = v_doc.organization_id
      AND is_active = true
    ORDER BY priority DESC
  LOOP
    v_matched_keywords := ARRAY[]::TEXT[];
    v_matched_patterns := ARRAY[]::TEXT[];
    v_confidence := 0;

    -- Check keywords
    IF v_rule.keywords IS NOT NULL AND array_length(v_rule.keywords, 1) > 0 THEN
      SELECT array_agg(keyword)
      INTO v_matched_keywords
      FROM unnest(v_rule.keywords) AS keyword
      WHERE v_doc.extracted_text ILIKE '%' || keyword || '%';
    END IF;

    -- Check patterns
    IF v_rule.patterns IS NOT NULL AND array_length(v_rule.patterns, 1) > 0 THEN
      SELECT array_agg(pattern)
      INTO v_matched_patterns
      FROM unnest(v_rule.patterns) AS pattern
      WHERE v_doc.extracted_text ~* pattern;
    END IF;

    -- Calculate confidence based on matches
    IF array_length(v_matched_keywords, 1) > 0 OR array_length(v_matched_patterns, 1) > 0 THEN
      v_confidence := LEAST(
        (COALESCE(array_length(v_matched_keywords, 1), 0) * 0.1 +
         COALESCE(array_length(v_matched_patterns, 1), 0) * 0.2)::DECIMAL(5,4),
        1.0
      );

      -- Only return if confidence meets threshold
      IF v_confidence >= COALESCE(v_rule.confidence_threshold, 0.5) THEN
        -- Create detection record
        INSERT INTO privilege_detections (
          document_id,
          case_id,
          rule_id,
          detected_privilege_type,
          detection_method,
          confidence_score,
          matched_keywords,
          matched_patterns,
          status
        ) VALUES (
          p_document_id,
          v_doc.case_id,
          v_rule.id,
          v_rule.privilege_type,
          'rule_based',
          v_confidence,
          v_matched_keywords,
          v_matched_patterns,
          CASE WHEN v_rule.require_review THEN 'pending_review' ELSE 'confirmed' END
        ) RETURNING id INTO v_detection_id;

        -- Auto-flag if rule specifies
        IF v_rule.auto_flag THEN
          UPDATE documents
          SET
            is_privileged = true,
            privilege_status = v_rule.privilege_type,
            privilege_reason = format('Auto-detected by rule: %s (confidence: %s)', v_rule.rule_name, v_confidence)
          WHERE id = p_document_id;
        END IF;

        -- Add to review queue if required
        IF v_rule.require_review THEN
          INSERT INTO privilege_review_queue (
            document_id,
            case_id,
            detection_id,
            priority,
            due_date
          ) VALUES (
            p_document_id,
            v_doc.case_id,
            v_detection_id,
            v_rule.priority,
            NOW() + INTERVAL '3 days'
          )
          ON CONFLICT (document_id) DO NOTHING;
        END IF;

        -- Return result
        RETURN QUERY SELECT
          v_rule.id,
          v_rule.privilege_type,
          v_confidence,
          v_matched_keywords,
          v_matched_patterns;
      END IF;
    END IF;
  END LOOP;

  RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to generate privilege log for a case
CREATE OR REPLACE FUNCTION generate_privilege_log(p_case_id UUID)
RETURNS TABLE (
  document_number TEXT,
  document_date DATE,
  author TEXT,
  recipients TEXT,
  description TEXT,
  privilege_type privilege_type,
  privilege_basis TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COALESCE(pl.document_number, d.document_number, d.id::TEXT),
    COALESCE(pl.document_date, d.document_date),
    COALESCE(pl.author, d.author),
    COALESCE(array_to_string(pl.recipients, '; '), array_to_string(d.recipient, '; ')),
    COALESCE(pl.description, d.description, d.title),
    pl.privilege_type,
    pl.privilege_basis
  FROM privilege_logs pl
  JOIN documents d ON pl.document_id = d.id
  WHERE pl.case_id = p_case_id
    AND pl.withheld = true
  ORDER BY pl.document_date DESC NULLS LAST, pl.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to check if user can access privileged document
CREATE OR REPLACE FUNCTION can_access_privileged_document(
  p_document_id UUID,
  p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
  v_is_privileged BOOLEAN;
  v_case_id UUID;
  v_user_role user_role;
  v_is_on_team BOOLEAN;
BEGIN
  -- Get document privilege status
  SELECT is_privileged, case_id INTO v_is_privileged, v_case_id
  FROM documents
  WHERE id = p_document_id;

  -- If not privileged, allow access
  IF NOT v_is_privileged THEN
    RETURN true;
  END IF;

  -- Get user role
  SELECT role INTO v_user_role FROM users WHERE id = p_user_id;

  -- Super admins and firm admins can access
  IF v_user_role IN ('super_admin', 'firm_admin') THEN
    RETURN true;
  END IF;

  -- Check if user is on case team
  SELECT EXISTS(
    SELECT 1 FROM case_team
    WHERE case_id = v_case_id
      AND user_id = p_user_id
      AND is_active = true
  ) INTO v_is_on_team;

  -- Lead attorneys and assigned team members can access
  IF v_is_on_team AND v_user_role IN ('lead_attorney', 'associate_attorney') THEN
    RETURN true;
  END IF;

  -- Default deny
  RETURN false;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- TRIGGERS
-- =====================================================================

CREATE TRIGGER update_privilege_detection_rules_updated_at BEFORE UPDATE ON privilege_detection_rules
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_privilege_detections_updated_at BEFORE UPDATE ON privilege_detections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_privilege_waivers_updated_at BEFORE UPDATE ON privilege_waivers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_privilege_logs_updated_at BEFORE UPDATE ON privilege_logs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_privilege_review_queue_updated_at BEFORE UPDATE ON privilege_review_queue
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-detect privilege on new documents
CREATE OR REPLACE FUNCTION auto_detect_privilege_on_insert()
RETURNS TRIGGER AS $$
BEGIN
  -- Run privilege detection asynchronously (in production, use a job queue)
  -- For now, we'll just queue it for review
  IF NEW.extracted_text IS NOT NULL AND length(NEW.extracted_text) > 0 THEN
    PERFORM detect_privilege(NEW.id);
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_detect_privilege
  AFTER INSERT ON documents
  FOR EACH ROW
  WHEN (NEW.extracted_text IS NOT NULL)
  EXECUTE FUNCTION auto_detect_privilege_on_insert();

-- =====================================================================
-- VIEWS
-- =====================================================================

-- View: Privileged documents requiring review
CREATE OR REPLACE VIEW v_privilege_review_pending AS
SELECT
  prq.id as queue_id,
  d.id as document_id,
  d.title,
  d.document_date,
  d.author,
  pd.detected_privilege_type,
  pd.confidence_score,
  prq.priority,
  prq.queue_date,
  prq.due_date,
  prq.assigned_to,
  u.full_name as assigned_to_name,
  EXTRACT(EPOCH FROM (NOW() - prq.queue_date))/3600 as hours_in_queue
FROM privilege_review_queue prq
JOIN documents d ON prq.document_id = d.id
LEFT JOIN privilege_detections pd ON prq.detection_id = pd.id
LEFT JOIN users u ON prq.assigned_to = u.id
WHERE prq.status IN ('pending', 'in_review')
ORDER BY prq.priority DESC, prq.queue_date;

-- View: Privilege detection statistics
CREATE OR REPLACE VIEW v_privilege_detection_stats AS
SELECT
  lc.id as case_id,
  lc.case_number,
  lc.title as case_title,
  COUNT(DISTINCT d.id) as total_documents,
  COUNT(DISTINCT d.id) FILTER (WHERE d.is_privileged) as privileged_documents,
  COUNT(DISTINCT pd.id) as total_detections,
  COUNT(DISTINCT pd.id) FILTER (WHERE pd.status = 'pending_review') as pending_review,
  COUNT(DISTINCT pd.id) FILTER (WHERE pd.status = 'confirmed') as confirmed,
  COUNT(DISTINCT pd.id) FILTER (WHERE pd.status = 'rejected') as rejected,
  AVG(pd.confidence_score) FILTER (WHERE pd.status = 'confirmed') as avg_confidence
FROM legal_cases lc
LEFT JOIN documents d ON lc.id = d.case_id
LEFT JOIN privilege_detections pd ON d.id = pd.document_id
GROUP BY lc.id, lc.case_number, lc.title;

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON TABLE privilege_detection_rules IS 'Rules for automatic privilege detection using keywords, patterns, and ML';
COMMENT ON TABLE privilege_detections IS 'Results of privilege detection scans on documents';
COMMENT ON TABLE privilege_waivers IS 'Track privilege waivers and clawback attempts';
COMMENT ON TABLE privilege_logs IS 'Formal privilege log for production to opposing counsel';
COMMENT ON TABLE privilege_review_queue IS 'Queue of documents requiring privilege review';

COMMENT ON FUNCTION detect_privilege IS 'Run privilege detection rules on a document and flag if matches found';
COMMENT ON FUNCTION generate_privilege_log IS 'Generate formal privilege log for a case';
COMMENT ON FUNCTION can_access_privileged_document IS 'Check if user has permission to access a privileged document';
