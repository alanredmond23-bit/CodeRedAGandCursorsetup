-- =====================================================================
-- VECTOR EMBEDDINGS & RAG CONFIGURATION
-- Purpose: pgvector setup for semantic search and RAG capabilities
-- Version: 1.0.0
-- Supports: 1536-dimensional embeddings (OpenAI ada-002), fast similarity search
-- =====================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================================
-- ENUM TYPES FOR EMBEDDINGS
-- =====================================================================

CREATE TYPE embedding_model AS ENUM (
  'openai_ada_002',           -- 1536 dimensions
  'openai_text_embedding_3_small',  -- 1536 dimensions
  'openai_text_embedding_3_large',  -- 3072 dimensions
  'cohere_embed_english_v3',  -- 1024 dimensions
  'custom'
);

CREATE TYPE embedding_status AS ENUM (
  'pending',
  'processing',
  'completed',
  'failed',
  'stale'  -- Needs re-embedding due to content change
);

CREATE TYPE chunk_type AS ENUM (
  'full_document',
  'page',
  'paragraph',
  'section',
  'sentence',
  'custom'
);

-- =====================================================================
-- TABLE: embedding_configs (Configuration for embedding models)
-- =====================================================================

CREATE TABLE embedding_configs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  model embedding_model NOT NULL,
  dimensions INTEGER NOT NULL CHECK (dimensions > 0),
  max_tokens INTEGER NOT NULL CHECK (max_tokens > 0),
  cost_per_1k_tokens DECIMAL(10,6) NOT NULL DEFAULT 0.0001,
  provider TEXT NOT NULL,
  api_endpoint TEXT,
  is_active BOOLEAN DEFAULT true,
  settings JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default configurations
INSERT INTO embedding_configs (name, model, dimensions, max_tokens, cost_per_1k_tokens, provider, settings) VALUES
  ('openai-ada-002', 'openai_ada_002', 1536, 8191, 0.0001, 'openai', '{"batch_size": 100}'::jsonb),
  ('openai-text-3-small', 'openai_text_embedding_3_small', 1536, 8191, 0.00002, 'openai', '{"batch_size": 100}'::jsonb),
  ('openai-text-3-large', 'openai_text_embedding_3_large', 3072, 8191, 0.00013, 'openai', '{"batch_size": 50}'::jsonb);

CREATE INDEX idx_embedding_configs_active ON embedding_configs(is_active) WHERE is_active = true;

-- =====================================================================
-- TABLE: document_chunks (Text chunks for embedding)
-- =====================================================================

CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Chunk identification
  chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
  chunk_type chunk_type DEFAULT 'paragraph',

  -- Content
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL, -- SHA-256 for deduplication
  token_count INTEGER,
  word_count INTEGER,

  -- Position in document
  page_number INTEGER,
  start_char INTEGER,
  end_char INTEGER,

  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb, -- {heading, section, author, date, etc.}

  -- Status
  is_embedded BOOLEAN DEFAULT false,
  embedded_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT document_chunks_unique UNIQUE (document_id, chunk_index),
  CONSTRAINT document_chunks_content_not_empty CHECK (length(content) > 0)
);

-- Partitioning by case_id for large datasets (optional, implement when scaling)
CREATE INDEX idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_case ON document_chunks(case_id);
CREATE INDEX idx_document_chunks_embedded ON document_chunks(is_embedded);
CREATE INDEX idx_document_chunks_hash ON document_chunks(content_hash);

-- Full-text search on chunk content
CREATE INDEX idx_document_chunks_text_search ON document_chunks USING gin(to_tsvector('english', content));

-- =====================================================================
-- TABLE: document_embeddings (Vector embeddings for semantic search)
-- =====================================================================

CREATE TABLE document_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  case_id UUID NOT NULL REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Embedding configuration
  config_id UUID NOT NULL REFERENCES embedding_configs(id),
  model embedding_model NOT NULL,

  -- Vector embedding (1536 dimensions for OpenAI ada-002)
  embedding vector(1536) NOT NULL,

  -- Status and tracking
  status embedding_status DEFAULT 'completed',
  tokens_used INTEGER,
  cost DECIMAL(10,6),
  error_message TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT document_embeddings_chunk_config_unique UNIQUE (chunk_id, config_id)
);

-- Indexes for vector similarity search (HNSW for best performance)
-- HNSW (Hierarchical Navigable Small World) is optimal for high-dimensional vectors
CREATE INDEX idx_document_embeddings_embedding_hnsw ON document_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64); -- Tuned for accuracy vs speed

-- Fallback IVFFlat index for different use cases
-- CREATE INDEX idx_document_embeddings_embedding_ivfflat ON document_embeddings
--   USING ivfflat (embedding vector_cosine_ops)
--   WITH (lists = 100); -- Use when dataset > 1M vectors

CREATE INDEX idx_document_embeddings_chunk ON document_embeddings(chunk_id);
CREATE INDEX idx_document_embeddings_document ON document_embeddings(document_id);
CREATE INDEX idx_document_embeddings_case ON document_embeddings(case_id);
CREATE INDEX idx_document_embeddings_status ON document_embeddings(status);
CREATE INDEX idx_document_embeddings_model ON document_embeddings(model);

-- =====================================================================
-- TABLE: embedding_jobs (Track batch embedding jobs)
-- =====================================================================

CREATE TABLE embedding_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id UUID REFERENCES legal_cases(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  config_id UUID NOT NULL REFERENCES embedding_configs(id),

  -- Job details
  job_type TEXT DEFAULT 'document_embedding' CHECK (job_type IN (
    'document_embedding', 'reembedding', 'batch_update'
  )),
  total_chunks INTEGER NOT NULL DEFAULT 0,
  processed_chunks INTEGER DEFAULT 0,
  failed_chunks INTEGER DEFAULT 0,

  -- Status
  status TEXT DEFAULT 'pending' CHECK (status IN (
    'pending', 'running', 'completed', 'failed', 'cancelled'
  )),

  -- Cost tracking
  total_tokens INTEGER DEFAULT 0,
  total_cost DECIMAL(10,6) DEFAULT 0,

  -- Error handling
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,

  -- User tracking
  started_by UUID REFERENCES users(id),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT embedding_jobs_chunks_valid CHECK (
    processed_chunks >= 0 AND
    failed_chunks >= 0 AND
    processed_chunks + failed_chunks <= total_chunks
  )
);

CREATE INDEX idx_embedding_jobs_case ON embedding_jobs(case_id);
CREATE INDEX idx_embedding_jobs_org ON embedding_jobs(organization_id);
CREATE INDEX idx_embedding_jobs_status ON embedding_jobs(status);
CREATE INDEX idx_embedding_jobs_started_by ON embedding_jobs(started_by);

-- =====================================================================
-- TABLE: semantic_search_history (Track semantic searches for analytics)
-- =====================================================================

CREATE TABLE semantic_search_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  case_id UUID REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Search details
  query_text TEXT NOT NULL,
  query_embedding vector(1536),
  filters JSONB DEFAULT '{}'::jsonb,

  -- Results
  results_count INTEGER,
  top_result_similarity FLOAT,
  execution_time_ms INTEGER,

  -- Configuration
  search_config JSONB DEFAULT '{
    "limit": 10,
    "similarity_threshold": 0.7,
    "include_privileged": false
  }'::jsonb,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_semantic_search_history_user ON semantic_search_history(user_id);
CREATE INDEX idx_semantic_search_history_case ON semantic_search_history(case_id);
CREATE INDEX idx_semantic_search_history_created ON semantic_search_history(created_at DESC);

-- =====================================================================
-- TABLE: embedding_quality_metrics (Monitor embedding quality)
-- =====================================================================

CREATE TABLE embedding_quality_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  config_id UUID NOT NULL REFERENCES embedding_configs(id),
  case_id UUID REFERENCES legal_cases(id) ON DELETE CASCADE,

  -- Quality metrics
  metric_type TEXT NOT NULL CHECK (metric_type IN (
    'search_accuracy', 'duplicate_detection', 'clustering_quality'
  )),
  score FLOAT CHECK (score >= 0 AND score <= 1),

  -- Details
  sample_size INTEGER,
  metadata JSONB DEFAULT '{}'::jsonb,

  measured_at TIMESTAMPTZ DEFAULT NOW(),
  measured_by UUID REFERENCES users(id)
);

CREATE INDEX idx_embedding_quality_metrics_config ON embedding_quality_metrics(config_id);
CREATE INDEX idx_embedding_quality_metrics_case ON embedding_quality_metrics(case_id);
CREATE INDEX idx_embedding_quality_metrics_type ON embedding_quality_metrics(metric_type);

-- =====================================================================
-- FUNCTIONS FOR VECTOR OPERATIONS
-- =====================================================================

-- Function to calculate cosine similarity between two vectors
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS FLOAT AS $$
BEGIN
  RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE;

-- Function to get embedding dimensions for a config
CREATE OR REPLACE FUNCTION get_embedding_dimensions(config_name TEXT)
RETURNS INTEGER AS $$
DECLARE
  dims INTEGER;
BEGIN
  SELECT dimensions INTO dims
  FROM embedding_configs
  WHERE name = config_name AND is_active = true;

  IF dims IS NULL THEN
    RAISE EXCEPTION 'Embedding config not found or inactive: %', config_name;
  END IF;

  RETURN dims;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to update embedding job progress
CREATE OR REPLACE FUNCTION update_embedding_job_progress(
  p_job_id UUID,
  p_processed INTEGER,
  p_failed INTEGER DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
  UPDATE embedding_jobs
  SET
    processed_chunks = processed_chunks + p_processed,
    failed_chunks = failed_chunks + p_failed,
    updated_at = NOW()
  WHERE id = p_job_id;

  -- Auto-complete job if all chunks processed
  UPDATE embedding_jobs
  SET
    status = 'completed',
    completed_at = NOW()
  WHERE
    id = p_job_id AND
    processed_chunks + failed_chunks >= total_chunks AND
    status = 'running';
END;
$$ LANGUAGE plpgsql;

-- Function to mark chunks as needing re-embedding
CREATE OR REPLACE FUNCTION mark_chunks_for_reembedding(p_document_id UUID)
RETURNS INTEGER AS $$
DECLARE
  affected_count INTEGER;
BEGIN
  UPDATE document_embeddings
  SET
    status = 'stale',
    updated_at = NOW()
  WHERE document_id = p_document_id;

  GET DIAGNOSTICS affected_count = ROW_COUNT;
  RETURN affected_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- TRIGGERS
-- =====================================================================

CREATE TRIGGER update_embedding_configs_updated_at BEFORE UPDATE ON embedding_configs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_chunks_updated_at BEFORE UPDATE ON document_chunks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_embeddings_updated_at BEFORE UPDATE ON document_embeddings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_embedding_jobs_updated_at BEFORE UPDATE ON embedding_jobs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update chunk embedded status
CREATE OR REPLACE FUNCTION update_chunk_embedded_status()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'completed' THEN
    UPDATE document_chunks
    SET
      is_embedded = true,
      embedded_at = NOW()
    WHERE id = NEW.chunk_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_chunk_embedded_status
  AFTER INSERT OR UPDATE ON document_embeddings
  FOR EACH ROW
  WHEN (NEW.status = 'completed')
  EXECUTE FUNCTION update_chunk_embedded_status();

-- =====================================================================
-- VIEWS FOR CONVENIENCE
-- =====================================================================

-- View: Embeddings with document context
CREATE OR REPLACE VIEW v_embeddings_with_context AS
SELECT
  e.id,
  e.chunk_id,
  e.document_id,
  e.case_id,
  d.title as document_title,
  d.document_number,
  d.is_privileged,
  dc.content as chunk_content,
  dc.chunk_index,
  dc.page_number,
  e.embedding,
  e.model,
  e.status,
  e.created_at
FROM document_embeddings e
JOIN document_chunks dc ON e.chunk_id = dc.id
JOIN documents d ON e.document_id = d.id
WHERE e.status = 'completed';

-- View: Embedding statistics by case
CREATE OR REPLACE VIEW v_embedding_stats_by_case AS
SELECT
  lc.id as case_id,
  lc.case_number,
  lc.title as case_title,
  COUNT(DISTINCT d.id) as total_documents,
  COUNT(DISTINCT dc.id) as total_chunks,
  COUNT(DISTINCT e.id) as total_embeddings,
  COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'completed') as completed_embeddings,
  COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'failed') as failed_embeddings,
  SUM(e.tokens_used) as total_tokens,
  SUM(e.cost) as total_cost,
  MAX(e.created_at) as last_embedding_date
FROM legal_cases lc
LEFT JOIN documents d ON lc.id = d.case_id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
LEFT JOIN document_embeddings e ON dc.id = e.chunk_id
GROUP BY lc.id, lc.case_number, lc.title;

-- =====================================================================
-- PERFORMANCE TUNING
-- =====================================================================

-- Analyze tables for query optimization
ANALYZE embedding_configs;
ANALYZE document_chunks;
ANALYZE document_embeddings;
ANALYZE embedding_jobs;

-- =====================================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================================

COMMENT ON TABLE embedding_configs IS 'Configuration for different embedding models (OpenAI, Cohere, etc.)';
COMMENT ON TABLE document_chunks IS 'Text chunks extracted from documents for embedding';
COMMENT ON TABLE document_embeddings IS 'Vector embeddings for semantic search using pgvector';
COMMENT ON TABLE embedding_jobs IS 'Batch jobs for processing embeddings';
COMMENT ON TABLE semantic_search_history IS 'History of semantic searches for analytics and improvement';
COMMENT ON TABLE embedding_quality_metrics IS 'Quality metrics for embedding performance monitoring';

COMMENT ON INDEX idx_document_embeddings_embedding_hnsw IS 'HNSW index for fast approximate nearest neighbor search';
COMMENT ON FUNCTION cosine_similarity IS 'Calculate cosine similarity between two vectors (returns 0-1)';
COMMENT ON FUNCTION update_embedding_job_progress IS 'Update progress of embedding job and auto-complete when done';
COMMENT ON FUNCTION mark_chunks_for_reembedding IS 'Mark all chunks of a document as stale when content changes';
