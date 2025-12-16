-- =====================================================================
-- LEGAL DISCOVERY CORE SCHEMA
-- Purpose: Core tables for managing legal cases, documents, and discovery
-- Version: 1.0.0
-- Supports: Millions of documents, concurrent access, full audit trail
-- =====================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search performance

-- =====================================================================
-- DOMAIN TYPES FOR VALIDATION
-- =====================================================================

CREATE DOMAIN email AS TEXT
  CHECK (VALUE ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');

CREATE DOMAIN phone AS TEXT
  CHECK (VALUE ~ '^\+?[1-9]\d{1,14}$');

-- =====================================================================
-- ENUM TYPES
-- =====================================================================

CREATE TYPE case_status AS ENUM (
  'active',
  'discovery',
  'trial',
  'settled',
  'closed',
  'archived'
);

CREATE TYPE document_status AS ENUM (
  'uploaded',
  'processing',
  'processed',
  'embedded',
  'reviewed',
  'privileged',
  'error',
  'archived'
);

CREATE TYPE privilege_type AS ENUM (
  'attorney_client',
  'work_product',
  'settlement_negotiation',
  'expert_consultant',
  'trade_secret',
  'none'
);

CREATE TYPE party_role AS ENUM (
  'plaintiff',
  'defendant',
  'third_party',
  'witness',
  'expert',
  'attorney'
);

CREATE TYPE user_role AS ENUM (
  'super_admin',
  'firm_admin',
  'lead_attorney',
  'associate_attorney',
  'paralegal',
  'legal_assistant',
  'expert',
  'client',
  'viewer'
);

-- =====================================================================
-- TABLE: organizations (Law firms, companies)
-- =====================================================================

CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('law_firm', 'corporation', 'government', 'individual')),
  email email,
  phone phone,
  address JSONB,
  billing_config JSONB DEFAULT '{"plan": "professional", "rate": 150.00}'::jsonb,
  settings JSONB DEFAULT '{}'::jsonb,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID,

  CONSTRAINT organizations_name_unique UNIQUE (name)
);

CREATE INDEX idx_organizations_active ON organizations(is_active) WHERE is_active = true;
CREATE INDEX idx_organizations_type ON organizations(type);

-- =====================================================================
-- TABLE: users (Attorneys, paralegals, clients)
-- =====================================================================

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email email NOT NULL,
  full_name TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'viewer',
  phone phone,
  bar_number TEXT,
  hourly_rate DECIMAL(10,2) DEFAULT 0.00,
  is_active BOOLEAN DEFAULT true,
  last_login_at TIMESTAMPTZ,
  settings JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT users_email_unique UNIQUE (email),
  CONSTRAINT users_hourly_rate_positive CHECK (hourly_rate >= 0)
);

CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- =====================================================================
-- TABLE: legal_cases
-- =====================================================================

CREATE TABLE legal_cases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  case_number TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  status case_status DEFAULT 'active',
  jurisdiction TEXT,
  court TEXT,
  judge_name TEXT,
  filing_date DATE,
  trial_date DATE,
  close_date DATE,
  total_budget DECIMAL(15,2),
  budget_spent DECIMAL(15,2) DEFAULT 0.00,
  metadata JSONB DEFAULT '{}'::jsonb,
  tags TEXT[],
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  CONSTRAINT legal_cases_case_number_org_unique UNIQUE (case_number, organization_id),
  CONSTRAINT legal_cases_budget_valid CHECK (total_budget IS NULL OR total_budget >= 0),
  CONSTRAINT legal_cases_budget_spent_valid CHECK (budget_spent >= 0)
);

CREATE INDEX idx_legal_cases_org ON legal_cases(organization_id);
CREATE INDEX idx_legal_cases_status ON legal_cases(status);
CREATE INDEX idx_legal_cases_active ON legal_cases(is_active) WHERE is_active = true;
CREATE INDEX idx_legal_cases_case_number ON legal_cases(case_number);
CREATE INDEX idx_legal_cases_filing_date ON legal_cases(filing_date);
CREATE INDEX idx_legal_cases_tags ON legal_cases USING gin(tags);

-- =====================================================================
-- TABLE: case_parties (Plaintiffs, defendants, witnesses)
-- =====================================================================

CREATE TABLE case_parties (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  party_type party_role NOT NULL,
  name TEXT NOT NULL,
  entity_type TEXT CHECK (entity_type IN ('individual', 'corporation', 'government', 'organization')),
  email email,
  phone phone,
  address JSONB,
  notes TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_case_parties_case ON case_parties(case_id);
CREATE INDEX idx_case_parties_type ON case_parties(party_type);
CREATE INDEX idx_case_parties_name ON case_parties(name);

-- =====================================================================
-- TABLE: case_team (Attorney assignments)
-- =====================================================================

CREATE TABLE case_team (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('lead_counsel', 'co_counsel', 'paralegal', 'legal_assistant', 'expert')),
  assigned_date DATE DEFAULT CURRENT_DATE,
  removed_date DATE,
  hourly_rate_override DECIMAL(10,2),
  permissions JSONB DEFAULT '{"can_view": true, "can_edit": false, "can_delete": false}'::jsonb,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT case_team_user_case_unique UNIQUE (case_id, user_id),
  CONSTRAINT case_team_dates_valid CHECK (removed_date IS NULL OR removed_date >= assigned_date)
);

CREATE INDEX idx_case_team_case ON case_team(case_id);
CREATE INDEX idx_case_team_user ON case_team(user_id);
CREATE INDEX idx_case_team_active ON case_team(is_active) WHERE is_active = true;

-- =====================================================================
-- TABLE: documents (Core document metadata)
-- =====================================================================

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Document identification
  document_number TEXT,
  title TEXT NOT NULL,
  description TEXT,

  -- File information
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size BIGINT NOT NULL CHECK (file_size > 0),
  mime_type TEXT NOT NULL,
  file_hash TEXT NOT NULL, -- SHA-256 hash for deduplication

  -- Status and classification
  status document_status DEFAULT 'uploaded',
  privilege_status privilege_type DEFAULT 'none',
  is_privileged BOOLEAN DEFAULT false,
  privilege_reason TEXT,

  -- Dates
  document_date DATE,
  received_date DATE,
  uploaded_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ,

  -- Parties involved
  author TEXT,
  recipient TEXT[],
  parties_involved TEXT[],

  -- Content
  extracted_text TEXT,
  page_count INTEGER,
  word_count INTEGER,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb,
  tags TEXT[],

  -- Chain of custody
  uploaded_by UUID REFERENCES users(id),
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMPTZ,

  -- Soft delete
  is_deleted BOOLEAN DEFAULT false,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id),

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT documents_file_hash_unique UNIQUE (file_hash, case_id)
);

-- Partitioning strategy for large document sets (by creation month)
-- This will be applied when migrating existing data
CREATE INDEX idx_documents_case ON documents(case_id, created_at DESC);
CREATE INDEX idx_documents_org ON documents(organization_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_privilege ON documents(is_privileged) WHERE is_privileged = true;
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);
CREATE INDEX idx_documents_document_date ON documents(document_date);
CREATE INDEX idx_documents_tags ON documents USING gin(tags);
CREATE INDEX idx_documents_metadata ON documents USING gin(metadata);

-- Full-text search on extracted text (with performance optimization)
CREATE INDEX idx_documents_text_search ON documents USING gin(to_tsvector('english', COALESCE(extracted_text, '')));
CREATE INDEX idx_documents_title_trgm ON documents USING gin(title gin_trgm_ops);

-- =====================================================================
-- TABLE: document_versions (Version history for documents)
-- =====================================================================

CREATE TABLE document_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  file_hash TEXT NOT NULL,
  changes_description TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT document_versions_unique UNIQUE (document_id, version_number),
  CONSTRAINT document_versions_number_positive CHECK (version_number > 0)
);

CREATE INDEX idx_document_versions_doc ON document_versions(document_id, version_number DESC);

-- =====================================================================
-- TABLE: document_relationships (Links between documents)
-- =====================================================================

CREATE TABLE document_relationships (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  target_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  relationship_type TEXT NOT NULL CHECK (relationship_type IN (
    'reply_to', 'attachment', 'amended_by', 'supersedes', 'references', 'exhibits'
  )),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  CONSTRAINT document_relationships_not_self CHECK (source_document_id != target_document_id),
  CONSTRAINT document_relationships_unique UNIQUE (source_document_id, target_document_id, relationship_type)
);

CREATE INDEX idx_doc_relationships_source ON document_relationships(source_document_id);
CREATE INDEX idx_doc_relationships_target ON document_relationships(target_document_id);
CREATE INDEX idx_doc_relationships_type ON document_relationships(relationship_type);

-- =====================================================================
-- TABLE: discovery_requests (Production requests, interrogatories)
-- =====================================================================

CREATE TABLE discovery_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  request_type TEXT NOT NULL CHECK (request_type IN (
    'production', 'interrogatory', 'admission', 'deposition', 'subpoena'
  )),
  request_number TEXT,
  title TEXT NOT NULL,
  description TEXT,
  requesting_party TEXT,
  responding_party TEXT,
  date_served DATE,
  date_due DATE,
  date_responded DATE,
  status TEXT DEFAULT 'pending' CHECK (status IN (
    'pending', 'in_progress', 'responded', 'objected', 'completed', 'withdrawn'
  )),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id),

  CONSTRAINT discovery_requests_dates_valid CHECK (
    date_due IS NULL OR date_served IS NULL OR date_due >= date_served
  )
);

CREATE INDEX idx_discovery_requests_case ON discovery_requests(case_id);
CREATE INDEX idx_discovery_requests_status ON discovery_requests(status);
CREATE INDEX idx_discovery_requests_date_due ON discovery_requests(date_due);

-- =====================================================================
-- TABLE: discovery_productions (Document productions in response)
-- =====================================================================

CREATE TABLE discovery_productions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  discovery_request_id UUID NOT NULL REFERENCES discovery_requests(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  production_number TEXT,
  bates_number TEXT,
  notes TEXT,
  is_redacted BOOLEAN DEFAULT false,
  redaction_reason TEXT,
  produced_date DATE,
  produced_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT discovery_productions_unique UNIQUE (discovery_request_id, document_id)
);

CREATE INDEX idx_discovery_productions_request ON discovery_productions(discovery_request_id);
CREATE INDEX idx_discovery_productions_document ON discovery_productions(document_id);
CREATE INDEX idx_discovery_productions_bates ON discovery_productions(bates_number);

-- =====================================================================
-- TABLE: document_annotations (Comments, highlights, notes)
-- =====================================================================

CREATE TABLE document_annotations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  annotation_type TEXT NOT NULL CHECK (annotation_type IN (
    'comment', 'highlight', 'redaction', 'bookmark', 'tag'
  )),
  content TEXT,
  position JSONB, -- {page, x, y, width, height}
  color TEXT,
  is_private BOOLEAN DEFAULT false,
  parent_annotation_id UUID REFERENCES document_annotations(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_document_annotations_doc ON document_annotations(document_id);
CREATE INDEX idx_document_annotations_user ON document_annotations(user_id);
CREATE INDEX idx_document_annotations_type ON document_annotations(annotation_type);

-- =====================================================================
-- TABLE: saved_searches (Save frequently used searches)
-- =====================================================================

CREATE TABLE saved_searches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  case_id UUID REFERENCES legal_cases(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  query_params JSONB NOT NULL,
  is_shared BOOLEAN DEFAULT false,
  use_count INTEGER DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_case ON saved_searches(case_id);

-- =====================================================================
-- TABLE: document_collections (Organize documents into sets)
-- =====================================================================

CREATE TABLE document_collections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  collection_type TEXT CHECK (collection_type IN (
    'privilege_log', 'hot_documents', 'exhibit_list', 'trial_binder', 'custom'
  )),
  is_shared BOOLEAN DEFAULT false,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT document_collections_name_case_unique UNIQUE (case_id, name)
);

CREATE INDEX idx_document_collections_case ON document_collections(case_id);
CREATE INDEX idx_document_collections_type ON document_collections(collection_type);

-- =====================================================================
-- TABLE: document_collection_items
-- =====================================================================

CREATE TABLE document_collection_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  collection_id UUID NOT NULL REFERENCES document_collections(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  sort_order INTEGER,
  notes TEXT,
  added_by UUID REFERENCES users(id),
  added_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT document_collection_items_unique UNIQUE (collection_id, document_id)
);

CREATE INDEX idx_document_collection_items_collection ON document_collection_items(collection_id, sort_order);
CREATE INDEX idx_document_collection_items_document ON document_collection_items(document_id);

-- =====================================================================
-- TRIGGERS FOR updated_at
-- =====================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_legal_cases_updated_at BEFORE UPDATE ON legal_cases
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_case_parties_updated_at BEFORE UPDATE ON case_parties
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_discovery_requests_updated_at BEFORE UPDATE ON discovery_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_annotations_updated_at BEFORE UPDATE ON document_annotations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_searches_updated_at BEFORE UPDATE ON saved_searches
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_collections_updated_at BEFORE UPDATE ON document_collections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================================

COMMENT ON TABLE organizations IS 'Law firms, corporations, and other entities using the system';
COMMENT ON TABLE users IS 'Attorneys, paralegals, clients, and other users with system access';
COMMENT ON TABLE legal_cases IS 'Legal cases and matters being managed';
COMMENT ON TABLE case_parties IS 'Parties involved in legal cases (plaintiffs, defendants, witnesses)';
COMMENT ON TABLE case_team IS 'Attorney and staff assignments to cases';
COMMENT ON TABLE documents IS 'Core document metadata and content for discovery';
COMMENT ON TABLE document_versions IS 'Version history for documents that have been modified';
COMMENT ON TABLE document_relationships IS 'Relationships between documents (replies, attachments, etc.)';
COMMENT ON TABLE discovery_requests IS 'Discovery requests, interrogatories, and production demands';
COMMENT ON TABLE discovery_productions IS 'Documents produced in response to discovery requests';
COMMENT ON TABLE document_annotations IS 'User annotations, comments, and highlights on documents';
COMMENT ON TABLE saved_searches IS 'Saved search queries for quick access';
COMMENT ON TABLE document_collections IS 'Organized sets of documents (privilege logs, hot docs, etc.)';
COMMENT ON TABLE document_collection_items IS 'Documents within collections';
