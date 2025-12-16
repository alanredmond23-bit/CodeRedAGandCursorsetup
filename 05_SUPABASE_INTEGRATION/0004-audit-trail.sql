-- =====================================================================
-- AUDIT TRAIL & COMPLIANCE LOGGING
-- Purpose: Complete audit trail for compliance, security, and chain of custody
-- Version: 1.0.0
-- Supports: GDPR, HIPAA, legal discovery compliance
-- =====================================================================

-- =====================================================================
-- ENUM TYPES
-- =====================================================================

CREATE TYPE audit_action AS ENUM (
  'create',
  'read',
  'update',
  'delete',
  'download',
  'upload',
  'share',
  'unshare',
  'grant_access',
  'revoke_access',
  'export',
  'print',
  'email',
  'search',
  'login',
  'logout',
  'failed_login',
  'privilege_flag',
  'privilege_unflag',
  'redact',
  'unredact'
);

CREATE TYPE audit_severity AS ENUM (
  'low',
  'medium',
  'high',
  'critical'
);

CREATE TYPE entity_type AS ENUM (
  'document',
  'case',
  'user',
  'organization',
  'embedding',
  'cost_entry',
  'budget',
  'annotation',
  'collection',
  'search',
  'system'
);

-- =====================================================================
-- TABLE: audit_logs (Complete activity tracking)
-- =====================================================================

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Who (actor)
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  user_email TEXT,
  user_name TEXT,
  user_role user_role,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,

  -- What (action and entity)
  action audit_action NOT NULL,
  entity_type entity_type NOT NULL,
  entity_id UUID,
  entity_name TEXT,

  -- Related entities
  case_id UUID REFERENCES legal_cases(id) ON DELETE SET NULL,
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

  -- Details
  description TEXT,
  severity audit_severity DEFAULT 'low',

  -- Changes (before/after for updates)
  old_values JSONB,
  new_values JSONB,
  changes JSONB, -- Computed diff

  -- Context
  ip_address INET,
  user_agent TEXT,
  session_id UUID,
  request_id UUID,

  -- Result
  success BOOLEAN DEFAULT true,
  error_message TEXT,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,
  tags TEXT[],

  -- Timestamp
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partitioning by month for performance (implement when data grows)
-- CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
--   FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_org ON audit_logs(organization_id, created_at DESC);
CREATE INDEX idx_audit_logs_case ON audit_logs(case_id, created_at DESC);
CREATE INDEX idx_audit_logs_document ON audit_logs(document_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity) WHERE severity IN ('high', 'critical');
CREATE INDEX idx_audit_logs_failed ON audit_logs(success) WHERE success = false;
CREATE INDEX idx_audit_logs_ip ON audit_logs(ip_address);
CREATE INDEX idx_audit_logs_session ON audit_logs(session_id);
CREATE INDEX idx_audit_logs_tags ON audit_logs USING gin(tags);

-- =====================================================================
-- TABLE: document_access_logs (Detailed document access tracking)
-- =====================================================================

CREATE TABLE document_access_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Access details
  access_type TEXT NOT NULL CHECK (access_type IN (
    'view', 'download', 'print', 'export', 'share', 'edit', 'delete'
  )),
  access_duration_seconds INTEGER,
  pages_viewed INTEGER[],

  -- Document state at access time
  document_status document_status,
  was_privileged BOOLEAN,

  -- Purpose (for compliance)
  access_purpose TEXT,
  justification TEXT,

  -- Context
  ip_address INET,
  user_agent TEXT,
  session_id UUID,

  -- Result
  success BOOLEAN DEFAULT true,
  denial_reason TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT document_access_logs_duration_positive CHECK (
    access_duration_seconds IS NULL OR access_duration_seconds >= 0
  )
);

CREATE INDEX idx_document_access_logs_document ON document_access_logs(document_id, created_at DESC);
CREATE INDEX idx_document_access_logs_user ON document_access_logs(user_id, created_at DESC);
CREATE INDEX idx_document_access_logs_case ON document_access_logs(case_id);
CREATE INDEX idx_document_access_logs_privileged ON document_access_logs(was_privileged) WHERE was_privileged = true;
CREATE INDEX idx_document_access_logs_created ON document_access_logs(created_at DESC);

-- =====================================================================
-- TABLE: privilege_change_logs (Track privilege status changes)
-- =====================================================================

CREATE TABLE privilege_change_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Change details
  old_privilege_status privilege_type,
  new_privilege_status privilege_type NOT NULL,
  old_is_privileged BOOLEAN,
  new_is_privileged BOOLEAN NOT NULL,

  -- Reason and justification
  reason TEXT NOT NULL,
  justification TEXT,
  supporting_evidence JSONB,

  -- Review process
  changed_by UUID NOT NULL REFERENCES users(id),
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ,
  review_notes TEXT,

  -- Compliance
  requires_notification BOOLEAN DEFAULT false,
  notification_sent BOOLEAN DEFAULT false,
  notification_sent_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_privilege_change_logs_document ON privilege_change_logs(document_id, created_at DESC);
CREATE INDEX idx_privilege_change_logs_case ON privilege_change_logs(case_id);
CREATE INDEX idx_privilege_change_logs_changed_by ON privilege_change_logs(changed_by);
CREATE INDEX idx_privilege_change_logs_pending_notification ON privilege_change_logs(requires_notification)
  WHERE requires_notification = true AND notification_sent = false;

-- =====================================================================
-- TABLE: search_audit_logs (Track all searches for compliance)
-- =====================================================================

CREATE TABLE search_audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
  case_id UUID REFERENCES legal_cases(id) ON DELETE SET NULL,

  -- Search details
  search_type TEXT NOT NULL CHECK (search_type IN (
    'keyword', 'semantic', 'advanced', 'boolean', 'date_range'
  )),
  search_query TEXT NOT NULL,
  search_filters JSONB DEFAULT '{}'::jsonb,

  -- Results
  results_count INTEGER,
  privileged_results_count INTEGER DEFAULT 0,
  results_shown_count INTEGER,
  execution_time_ms INTEGER,

  -- User actions on results
  documents_viewed UUID[],
  documents_downloaded UUID[],

  -- Context
  ip_address INET,
  session_id UUID,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_search_audit_logs_user ON search_audit_logs(user_id, created_at DESC);
CREATE INDEX idx_search_audit_logs_case ON search_audit_logs(case_id);
CREATE INDEX idx_search_audit_logs_created ON search_audit_logs(created_at DESC);
CREATE INDEX idx_search_audit_logs_privileged ON search_audit_logs(privileged_results_count)
  WHERE privileged_results_count > 0;

-- =====================================================================
-- TABLE: data_export_logs (Track data exports for compliance)
-- =====================================================================

CREATE TABLE data_export_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
  case_id UUID REFERENCES legal_cases(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Export details
  export_type TEXT NOT NULL CHECK (export_type IN (
    'document_download', 'bulk_export', 'report', 'data_request', 'backup'
  )),
  export_format TEXT CHECK (export_format IN (
    'pdf', 'zip', 'csv', 'json', 'xml', 'native'
  )),

  -- Content
  document_ids UUID[],
  record_count INTEGER,
  total_size_bytes BIGINT,

  -- Purpose
  export_purpose TEXT NOT NULL,
  justification TEXT,

  -- Approval workflow
  requires_approval BOOLEAN DEFAULT false,
  approved_by UUID REFERENCES users(id),
  approved_at TIMESTAMPTZ,
  approval_notes TEXT,

  -- File information
  file_path TEXT,
  file_hash TEXT,

  -- Status
  status TEXT DEFAULT 'pending' CHECK (status IN (
    'pending', 'approved', 'processing', 'completed', 'failed', 'denied'
  )),
  error_message TEXT,

  -- Security
  encryption_enabled BOOLEAN DEFAULT false,
  watermarked BOOLEAN DEFAULT false,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,

  CONSTRAINT data_export_logs_record_count_positive CHECK (record_count IS NULL OR record_count >= 0)
);

CREATE INDEX idx_data_export_logs_user ON data_export_logs(user_id, created_at DESC);
CREATE INDEX idx_data_export_logs_case ON data_export_logs(case_id);
CREATE INDEX idx_data_export_logs_org ON data_export_logs(organization_id);
CREATE INDEX idx_data_export_logs_status ON data_export_logs(status);
CREATE INDEX idx_data_export_logs_pending_approval ON data_export_logs(requires_approval)
  WHERE requires_approval = true AND approved_at IS NULL;

-- =====================================================================
-- TABLE: security_events (Security incidents and anomalies)
-- =====================================================================

CREATE TABLE security_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type TEXT NOT NULL CHECK (event_type IN (
    'unauthorized_access',
    'failed_authentication',
    'privilege_escalation',
    'suspicious_activity',
    'data_breach',
    'policy_violation',
    'anomaly_detection'
  )),
  severity audit_severity NOT NULL,

  -- Involved parties
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  affected_entity_type entity_type,
  affected_entity_id UUID,

  -- Details
  description TEXT NOT NULL,
  detection_method TEXT,
  indicators JSONB,

  -- Response
  response_required BOOLEAN DEFAULT true,
  response_status TEXT DEFAULT 'open' CHECK (response_status IN (
    'open', 'investigating', 'resolved', 'false_positive', 'escalated'
  )),
  assigned_to UUID REFERENCES users(id),
  resolution_notes TEXT,
  resolved_at TIMESTAMPTZ,

  -- Context
  ip_address INET,
  user_agent TEXT,
  session_id UUID,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_security_events_severity ON security_events(severity, created_at DESC);
CREATE INDEX idx_security_events_user ON security_events(user_id);
CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_status ON security_events(response_status);
CREATE INDEX idx_security_events_open ON security_events(response_required)
  WHERE response_required = true AND response_status = 'open';

-- =====================================================================
-- TABLE: compliance_reports (Generated compliance reports)
-- =====================================================================

CREATE TABLE compliance_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  case_id UUID REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Report details
  report_type TEXT NOT NULL CHECK (report_type IN (
    'gdpr_access', 'hipaa_audit', 'discovery_chain_of_custody',
    'privilege_log', 'access_summary', 'security_audit'
  )),
  report_period_start DATE NOT NULL,
  report_period_end DATE NOT NULL,

  -- Content
  report_data JSONB NOT NULL,
  summary TEXT,
  findings JSONB,
  recommendations JSONB,

  -- File
  file_path TEXT,
  file_format TEXT,

  -- Status
  status TEXT DEFAULT 'draft' CHECK (status IN (
    'draft', 'review', 'approved', 'published', 'archived'
  )),

  -- Tracking
  generated_by UUID REFERENCES users(id),
  approved_by UUID REFERENCES users(id),
  approved_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT compliance_reports_dates_valid CHECK (report_period_end >= report_period_start)
);

CREATE INDEX idx_compliance_reports_org ON compliance_reports(organization_id, created_at DESC);
CREATE INDEX idx_compliance_reports_case ON compliance_reports(case_id);
CREATE INDEX idx_compliance_reports_type ON compliance_reports(report_type);
CREATE INDEX idx_compliance_reports_status ON compliance_reports(status);

-- =====================================================================
-- FUNCTIONS FOR AUDIT LOGGING
-- =====================================================================

-- Function to create audit log entry
CREATE OR REPLACE FUNCTION create_audit_log(
  p_user_id UUID,
  p_action audit_action,
  p_entity_type entity_type,
  p_entity_id UUID,
  p_description TEXT DEFAULT NULL,
  p_old_values JSONB DEFAULT NULL,
  p_new_values JSONB DEFAULT NULL,
  p_metadata JSONB DEFAULT NULL,
  p_severity audit_severity DEFAULT 'low',
  p_ip_address INET DEFAULT NULL,
  p_session_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  v_audit_id UUID;
  v_user_email TEXT;
  v_user_name TEXT;
  v_user_role user_role;
  v_org_id UUID;
  v_changes JSONB;
BEGIN
  -- Get user information
  SELECT email, full_name, role, organization_id
  INTO v_user_email, v_user_name, v_user_role, v_org_id
  FROM users
  WHERE id = p_user_id;

  -- Compute changes if old and new values provided
  IF p_old_values IS NOT NULL AND p_new_values IS NOT NULL THEN
    v_changes := jsonb_build_object(
      'changed_fields', (
        SELECT jsonb_object_agg(key, jsonb_build_object('old', p_old_values->key, 'new', p_new_values->key))
        FROM jsonb_object_keys(p_new_values) key
        WHERE p_old_values->key IS DISTINCT FROM p_new_values->key
      )
    );
  END IF;

  -- Insert audit log
  INSERT INTO audit_logs (
    user_id,
    user_email,
    user_name,
    user_role,
    organization_id,
    action,
    entity_type,
    entity_id,
    description,
    severity,
    old_values,
    new_values,
    changes,
    ip_address,
    session_id,
    metadata
  ) VALUES (
    p_user_id,
    v_user_email,
    v_user_name,
    v_user_role,
    v_org_id,
    p_action,
    p_entity_type,
    p_entity_id,
    p_description,
    p_severity,
    p_old_values,
    p_new_values,
    v_changes,
    p_ip_address,
    p_session_id,
    p_metadata
  ) RETURNING id INTO v_audit_id;

  RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

-- Function to log document access
CREATE OR REPLACE FUNCTION log_document_access(
  p_document_id UUID,
  p_user_id UUID,
  p_access_type TEXT,
  p_access_purpose TEXT DEFAULT NULL,
  p_ip_address INET DEFAULT NULL,
  p_session_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  v_log_id UUID;
  v_case_id UUID;
  v_doc_status document_status;
  v_is_privileged BOOLEAN;
BEGIN
  -- Get document information
  SELECT case_id, status, is_privileged
  INTO v_case_id, v_doc_status, v_is_privileged
  FROM documents
  WHERE id = p_document_id;

  -- Create access log
  INSERT INTO document_access_logs (
    document_id,
    user_id,
    case_id,
    access_type,
    access_purpose,
    document_status,
    was_privileged,
    ip_address,
    session_id
  ) VALUES (
    p_document_id,
    p_user_id,
    v_case_id,
    p_access_type,
    p_access_purpose,
    v_doc_status,
    v_is_privileged,
    p_ip_address,
    p_session_id
  ) RETURNING id INTO v_log_id;

  -- Also create general audit log for high-value actions
  IF p_access_type IN ('download', 'print', 'export', 'delete') THEN
    PERFORM create_audit_log(
      p_user_id,
      p_access_type::audit_action,
      'document',
      p_document_id,
      format('Document %s: %s', p_access_type, p_document_id),
      NULL,
      NULL,
      jsonb_build_object('privileged', v_is_privileged, 'purpose', p_access_purpose),
      CASE WHEN v_is_privileged THEN 'high'::audit_severity ELSE 'medium'::audit_severity END,
      p_ip_address,
      p_session_id
    );
  END IF;

  RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- Auto-audit function for document changes
CREATE OR REPLACE FUNCTION audit_document_changes()
RETURNS TRIGGER AS $$
DECLARE
  v_action audit_action;
  v_old_values JSONB;
  v_new_values JSONB;
BEGIN
  -- Determine action
  IF TG_OP = 'INSERT' THEN
    v_action := 'create';
    v_new_values := to_jsonb(NEW);
  ELSIF TG_OP = 'UPDATE' THEN
    v_action := 'update';
    v_old_values := to_jsonb(OLD);
    v_new_values := to_jsonb(NEW);
  ELSIF TG_OP = 'DELETE' THEN
    v_action := 'delete';
    v_old_values := to_jsonb(OLD);
  END IF;

  -- Create audit log
  PERFORM create_audit_log(
    COALESCE(NEW.uploaded_by, OLD.uploaded_by),
    v_action,
    'document',
    COALESCE(NEW.id, OLD.id),
    format('Document %s: %s', v_action, COALESCE(NEW.title, OLD.title)),
    v_old_values,
    v_new_values,
    NULL,
    CASE WHEN COALESCE(NEW.is_privileged, OLD.is_privileged) THEN 'high'::audit_severity ELSE 'medium'::audit_severity END
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- TRIGGERS FOR AUTOMATIC AUDIT LOGGING
-- =====================================================================

CREATE TRIGGER update_security_events_updated_at BEFORE UPDATE ON security_events
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_reports_updated_at BEFORE UPDATE ON compliance_reports
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-audit document changes
CREATE TRIGGER trigger_audit_document_changes
  AFTER INSERT OR UPDATE OR DELETE ON documents
  FOR EACH ROW
  EXECUTE FUNCTION audit_document_changes();

-- Log privilege changes
CREATE OR REPLACE FUNCTION log_privilege_changes()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.is_privileged IS DISTINCT FROM NEW.is_privileged OR
     OLD.privilege_status IS DISTINCT FROM NEW.privilege_status THEN

    INSERT INTO privilege_change_logs (
      document_id,
      case_id,
      old_privilege_status,
      new_privilege_status,
      old_is_privileged,
      new_is_privileged,
      reason,
      changed_by
    ) VALUES (
      NEW.id,
      NEW.case_id,
      OLD.privilege_status,
      NEW.privilege_status,
      OLD.is_privileged,
      NEW.is_privileged,
      COALESCE(NEW.privilege_reason, 'Status changed'),
      NEW.reviewed_by
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_privilege_changes
  AFTER UPDATE ON documents
  FOR EACH ROW
  WHEN (OLD.is_privileged IS DISTINCT FROM NEW.is_privileged OR
        OLD.privilege_status IS DISTINCT FROM NEW.privilege_status)
  EXECUTE FUNCTION log_privilege_changes();

-- =====================================================================
-- VIEWS FOR AUDIT REPORTING
-- =====================================================================

-- View: Recent high-severity audit events
CREATE OR REPLACE VIEW v_recent_critical_audits AS
SELECT
  al.*,
  u.full_name as user_full_name,
  o.name as organization_name
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
LEFT JOIN organizations o ON al.organization_id = o.id
WHERE al.severity IN ('high', 'critical')
ORDER BY al.created_at DESC
LIMIT 100;

-- View: Document access summary
CREATE OR REPLACE VIEW v_document_access_summary AS
SELECT
  d.id as document_id,
  d.title,
  d.is_privileged,
  COUNT(DISTINCT dal.user_id) as unique_users_accessed,
  COUNT(dal.id) as total_accesses,
  COUNT(dal.id) FILTER (WHERE dal.access_type = 'view') as view_count,
  COUNT(dal.id) FILTER (WHERE dal.access_type = 'download') as download_count,
  COUNT(dal.id) FILTER (WHERE dal.access_type = 'print') as print_count,
  MIN(dal.created_at) as first_access,
  MAX(dal.created_at) as last_access
FROM documents d
LEFT JOIN document_access_logs dal ON d.id = dal.document_id
GROUP BY d.id, d.title, d.is_privileged;

-- View: User activity summary
CREATE OR REPLACE VIEW v_user_activity_summary AS
SELECT
  u.id as user_id,
  u.full_name,
  u.email,
  u.role,
  COUNT(DISTINCT al.id) as total_actions,
  COUNT(DISTINCT dal.document_id) as documents_accessed,
  MAX(al.created_at) as last_activity,
  COUNT(al.id) FILTER (WHERE al.action = 'download') as downloads,
  COUNT(al.id) FILTER (WHERE al.success = false) as failed_actions
FROM users u
LEFT JOIN audit_logs al ON u.id = al.user_id
LEFT JOIN document_access_logs dal ON u.id = dal.user_id
GROUP BY u.id, u.full_name, u.email, u.role;

-- =====================================================================
-- PERFORMANCE OPTIMIZATION
-- =====================================================================

ANALYZE audit_logs;
ANALYZE document_access_logs;
ANALYZE privilege_change_logs;
ANALYZE security_events;

-- =====================================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================================

COMMENT ON TABLE audit_logs IS 'Complete audit trail of all system activities';
COMMENT ON TABLE document_access_logs IS 'Detailed tracking of document access for compliance';
COMMENT ON TABLE privilege_change_logs IS 'History of privilege status changes with justification';
COMMENT ON TABLE search_audit_logs IS 'Audit trail of all search queries and results';
COMMENT ON TABLE data_export_logs IS 'Tracking of data exports for security and compliance';
COMMENT ON TABLE security_events IS 'Security incidents and anomaly detection';
COMMENT ON TABLE compliance_reports IS 'Generated compliance reports for regulatory requirements';

COMMENT ON FUNCTION create_audit_log IS 'Create a comprehensive audit log entry with automatic user context';
COMMENT ON FUNCTION log_document_access IS 'Log document access with automatic compliance tracking';
