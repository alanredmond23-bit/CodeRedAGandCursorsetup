-- ============================================================================
-- SETUP RAG SYSTEM SQL
-- antigravityCodeRed RAG (Retrieval-Augmented Generation) Setup
-- Execute this in Supabase SQL Editor after Phase 2 (agent seeding)
-- ============================================================================

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table for document vectors
CREATE TABLE IF NOT EXISTS codered.document_embeddings (
  id BIGSERIAL PRIMARY KEY,
  document_chunk_id BIGINT NOT NULL REFERENCES codered.document_chunks(id) ON DELETE CASCADE,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on embedding vectors for fast similarity search
CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector 
ON codered.document_embeddings 
USING IVFFLAT (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index on document_chunk_id for quick lookups
CREATE INDEX IF NOT EXISTS idx_document_embeddings_chunk_id 
ON codered.document_embeddings(document_chunk_id);

-- Function: search_embeddings
-- Performs semantic similarity search on document embeddings
-- Returns documents similar to the query embedding
CREATE OR REPLACE FUNCTION codered.search_embeddings(
  query_embedding vector(1536),
  similarity_threshold float DEFAULT 0.5,
  limit_results int DEFAULT 10
)
RETURNS TABLE(
  chunk_id BIGINT,
  document_id BIGINT,
  document_title TEXT,
  chunk_content TEXT,
  similarity float,
  metadata JSONB
) AS $$
  SELECT
    de.document_chunk_id,
    dc.document_id,
    d.title,
    dc.content,
    (1 - (de.embedding <=> query_embedding))::float as similarity,
    dc.metadata
  FROM codered.document_embeddings de
  JOIN codered.document_chunks dc ON de.document_chunk_id = dc.id
  JOIN codered.documents d ON dc.document_id = d.id
  WHERE (1 - (de.embedding <=> query_embedding)) > similarity_threshold
  ORDER BY de.embedding <=> query_embedding
  LIMIT limit_results;
$$ LANGUAGE SQL STABLE;

-- Function: compute_similarity
-- Helper function to compute cosine similarity between two embeddings
CREATE OR REPLACE FUNCTION codered.compute_similarity(
  embedding1 vector(1536),
  embedding2 vector(1536)
)
RETURNS float AS $$
  SELECT (1 - (embedding1 <=> embedding2))::float;
$$ LANGUAGE SQL IMMUTABLE;

-- Function: ingest_document
-- Main document ingestion function
-- Handles document processing, chunking, and preparation for embedding
CREATE OR REPLACE FUNCTION codered.ingest_document(
  p_title TEXT,
  p_content TEXT,
  p_source_url TEXT DEFAULT NULL,
  p_document_type TEXT DEFAULT 'general',
  p_metadata JSONB DEFAULT '{}',
  p_organization_id UUID DEFAULT NULL
)
RETURNS TABLE(
  document_id BIGINT,
  chunks_created INT,
  total_tokens INT
) AS $$
DECLARE
  v_doc_id BIGINT;
  v_chunk_count INT := 0;
  v_total_tokens INT := 0;
  v_chunk_start INT := 0;
  v_chunk_end INT := 0;
  v_chunk_content TEXT;
  v_content_length INT;
  v_chunk_size INT := 1800;  -- tokens per chunk
  v_overlap INT := 200;      -- token overlap
BEGIN
  -- Insert document
  INSERT INTO codered.documents (
    title,
    content,
    source_url,
    document_type,
    metadata,
    organization_id,
    created_at,
    updated_at
  ) VALUES (
    p_title,
    p_content,
    p_source_url,
    p_document_type,
    p_metadata,
    p_organization_id,
    NOW(),
    NOW()
  )
  RETURNING id INTO v_doc_id;

  -- Calculate approximate token count (rough estimate: ~4 chars per token)
  v_content_length := LENGTH(p_content);
  v_total_tokens := CEIL(v_content_length::float / 4);

  -- Create chunks with overlap
  v_chunk_start := 1;
  WHILE v_chunk_start < v_content_length LOOP
    -- Calculate chunk end position
    v_chunk_end := LEAST(
      v_chunk_start + (v_chunk_size * 4),  -- approximate char count
      v_content_length
    );

    -- Extract chunk content
    v_chunk_content := SUBSTRING(
      p_content,
      v_chunk_start,
      v_chunk_end - v_chunk_start
    );

    -- Create chunk record
    IF LENGTH(TRIM(v_chunk_content)) > 0 THEN
      INSERT INTO codered.document_chunks (
        document_id,
        chunk_index,
        content,
        metadata,
        created_at,
        updated_at
      ) VALUES (
        v_doc_id,
        v_chunk_count,
        v_chunk_content,
        jsonb_build_object(
          'start_position', v_chunk_start,
          'end_position', v_chunk_end,
          'token_estimate', CEIL(LENGTH(v_chunk_content)::float / 4)
        ),
        NOW(),
        NOW()
      );

      v_chunk_count := v_chunk_count + 1;
    END IF;

    -- Move to next chunk (with overlap)
    v_chunk_start := v_chunk_end - (v_overlap * 4);
  END LOOP;

  RETURN QUERY SELECT v_doc_id, v_chunk_count, v_total_tokens;
END;
$$ LANGUAGE plpgsql;

-- Create index on documents for faster lookups
CREATE INDEX IF NOT EXISTS idx_documents_title 
ON codered.documents(title);

CREATE INDEX IF NOT EXISTS idx_documents_organization_id 
ON codered.documents(organization_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id 
ON codered.document_chunks(document_id);

-- Create view for active documents with chunk count
CREATE OR REPLACE VIEW codered.documents_with_chunks AS
SELECT
  d.id,
  d.title,
  d.document_type,
  d.source_url,
  COUNT(dc.id) as chunk_count,
  d.metadata,
  d.created_at,
  d.updated_at
FROM codered.documents d
LEFT JOIN codered.document_chunks dc ON d.id = dc.document_id
GROUP BY d.id, d.title, d.document_type, d.source_url, d.metadata, d.created_at, d.updated_at;

-- Verify RAG system setup
SELECT 
  'pgvector extension' as component,
  EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector') as status
UNION ALL
SELECT 
  'document_embeddings table',
  EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'document_embeddings' AND table_schema = 'codered')
UNION ALL
SELECT 
  'search_embeddings function',
  EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'search_embeddings' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'codered'))
UNION ALL
SELECT 
  'ingest_document function',
  EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'ingest_document' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'codered'))
UNION ALL
SELECT 
  'embeddings vector index',
  EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = 'idx_document_embeddings_vector' AND schemaname = 'codered');

-- All components should return 'true' for status
