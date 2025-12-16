-- =====================================================================
-- DISCOVERY & SEARCH QUERIES
-- Purpose: Legal discovery and document search queries
-- Version: 1.0.0
-- =====================================================================

-- =====================================================================
-- DOCUMENT SEARCH QUERIES
-- =====================================================================

-- Query: Advanced document search with filters
CREATE OR REPLACE FUNCTION search_documents(
  p_case_id UUID,
  p_search_text TEXT DEFAULT NULL,
  p_start_date DATE DEFAULT NULL,
  p_end_date DATE DEFAULT NULL,
  p_author TEXT DEFAULT NULL,
  p_tags TEXT[] DEFAULT NULL,
  p_privilege_filter TEXT DEFAULT 'all', -- 'all', 'privileged', 'not_privileged'
  p_status document_status[] DEFAULT NULL,
  p_limit INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  document_number TEXT,
  document_date DATE,
  author TEXT,
  file_name TEXT,
  page_count INTEGER,
  is_privileged BOOLEAN,
  privilege_type privilege_type,
  status document_status,
  relevance_score REAL,
  snippet TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    d.document_number,
    d.document_date,
    d.author,
    d.file_name,
    d.page_count,
    d.is_privileged,
    d.privilege_status,
    d.status,
    CASE
      WHEN p_search_text IS NOT NULL THEN
        ts_rank(
          to_tsvector('english', COALESCE(d.title, '') || ' ' || COALESCE(d.extracted_text, '')),
          plainto_tsquery('english', p_search_text)
        )
      ELSE 0
    END as relevance_score,
    CASE
      WHEN p_search_text IS NOT NULL THEN
        ts_headline('english', COALESCE(d.extracted_text, ''), plainto_tsquery('english', p_search_text),
                    'MaxWords=30, MinWords=10, MaxFragments=2')
      ELSE NULL
    END as snippet
  FROM documents d
  WHERE d.case_id = p_case_id
    AND d.is_deleted = false
    AND (p_search_text IS NULL OR
         to_tsvector('english', COALESCE(d.title, '') || ' ' || COALESCE(d.extracted_text, '')) @@
         plainto_tsquery('english', p_search_text))
    AND (p_start_date IS NULL OR d.document_date >= p_start_date)
    AND (p_end_date IS NULL OR d.document_date <= p_end_date)
    AND (p_author IS NULL OR d.author ILIKE '%' || p_author || '%')
    AND (p_tags IS NULL OR d.tags && p_tags)
    AND (p_privilege_filter = 'all' OR
         (p_privilege_filter = 'privileged' AND d.is_privileged = true) OR
         (p_privilege_filter = 'not_privileged' AND d.is_privileged = false))
    AND (p_status IS NULL OR d.status = ANY(p_status))
  ORDER BY
    CASE WHEN p_search_text IS NOT NULL THEN relevance_score ELSE 0 END DESC,
    d.document_date DESC NULLS LAST,
    d.created_at DESC
  LIMIT p_limit
  OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Search documents by date range (timeline view)
CREATE OR REPLACE FUNCTION search_documents_by_timeline(
  p_case_id UUID,
  p_start_date DATE,
  p_end_date DATE,
  p_include_privileged BOOLEAN DEFAULT false
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  document_date DATE,
  author TEXT,
  recipient TEXT[],
  is_privileged BOOLEAN,
  document_type TEXT,
  page_count INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    d.document_date,
    d.author,
    d.recipient,
    d.is_privileged,
    d.metadata->>'document_type' as document_type,
    d.page_count
  FROM documents d
  WHERE d.case_id = p_case_id
    AND d.is_deleted = false
    AND d.document_date IS NOT NULL
    AND d.document_date BETWEEN p_start_date AND p_end_date
    AND (p_include_privileged = true OR d.is_privileged = false)
  ORDER BY d.document_date, d.created_at;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Find similar documents (duplicates, near-duplicates)
CREATE OR REPLACE FUNCTION find_similar_documents(
  p_document_id UUID,
  p_similarity_threshold FLOAT DEFAULT 0.8,
  p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  similar_document_id UUID,
  title TEXT,
  similarity_score FLOAT,
  file_hash TEXT,
  is_exact_duplicate BOOLEAN
) AS $$
DECLARE
  v_embedding vector(1536);
  v_file_hash TEXT;
BEGIN
  -- Get the embedding and file hash of the source document
  SELECT e.embedding, d.file_hash
  INTO v_embedding, v_file_hash
  FROM documents d
  LEFT JOIN document_embeddings e ON d.id = e.document_id
  WHERE d.id = p_document_id
  LIMIT 1;

  IF v_embedding IS NULL THEN
    RAISE EXCEPTION 'Document has no embedding: %', p_document_id;
  END IF;

  RETURN QUERY
  SELECT
    d.id,
    d.title,
    cosine_similarity(v_embedding, e.embedding) as similarity_score,
    d.file_hash,
    (d.file_hash = v_file_hash) as is_exact_duplicate
  FROM documents d
  JOIN document_embeddings e ON d.id = e.document_id
  WHERE d.id != p_document_id
    AND e.status = 'completed'
    AND (
      d.file_hash = v_file_hash OR
      cosine_similarity(v_embedding, e.embedding) >= p_similarity_threshold
    )
  ORDER BY similarity_score DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- SEMANTIC SEARCH QUERIES
-- =====================================================================

-- Query: Semantic search using vector embeddings
CREATE OR REPLACE FUNCTION semantic_search(
  p_case_id UUID,
  p_query_embedding vector(1536),
  p_user_id UUID,
  p_similarity_threshold FLOAT DEFAULT 0.7,
  p_include_privileged BOOLEAN DEFAULT false,
  p_limit INTEGER DEFAULT 10,
  p_filters JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  document_id UUID,
  chunk_id UUID,
  title TEXT,
  content_snippet TEXT,
  similarity_score FLOAT,
  document_date DATE,
  is_privileged BOOLEAN,
  page_number INTEGER
) AS $$
DECLARE
  v_search_id UUID;
  v_start_time TIMESTAMPTZ := clock_timestamp();
  v_execution_time INTEGER;
  v_results_count INTEGER;
  v_privileged_count INTEGER;
BEGIN
  -- Perform semantic search
  CREATE TEMP TABLE IF NOT EXISTS temp_search_results AS
  SELECT
    d.id as document_id,
    dc.id as chunk_id,
    d.title,
    LEFT(dc.content, 300) as content_snippet,
    cosine_similarity(p_query_embedding, de.embedding) as similarity_score,
    d.document_date,
    d.is_privileged,
    dc.page_number
  FROM document_embeddings de
  JOIN document_chunks dc ON de.chunk_id = dc.id
  JOIN documents d ON de.document_id = d.id
  WHERE de.case_id = p_case_id
    AND de.status = 'completed'
    AND d.is_deleted = false
    AND (p_include_privileged = true OR d.is_privileged = false)
    AND cosine_similarity(p_query_embedding, de.embedding) >= p_similarity_threshold
    -- Apply additional filters from p_filters JSONB
    AND (
      (p_filters->>'start_date' IS NULL OR d.document_date >= (p_filters->>'start_date')::DATE) AND
      (p_filters->>'end_date' IS NULL OR d.document_date <= (p_filters->>'end_date')::DATE) AND
      (p_filters->>'author' IS NULL OR d.author ILIKE '%' || (p_filters->>'author') || '%')
    )
  ORDER BY similarity_score DESC
  LIMIT p_limit;

  -- Get counts
  SELECT COUNT(*), COUNT(*) FILTER (WHERE is_privileged)
  INTO v_results_count, v_privileged_count
  FROM temp_search_results;

  -- Calculate execution time
  v_execution_time := EXTRACT(MILLISECOND FROM clock_timestamp() - v_start_time)::INTEGER;

  -- Log search for audit
  INSERT INTO search_audit_logs (
    user_id,
    case_id,
    search_type,
    search_query,
    search_filters,
    results_count,
    privileged_results_count,
    execution_time_ms
  ) VALUES (
    p_user_id,
    p_case_id,
    'semantic',
    'Vector similarity search',
    p_filters,
    v_results_count,
    v_privileged_count,
    v_execution_time
  ) RETURNING id INTO v_search_id;

  -- Return results
  RETURN QUERY SELECT * FROM temp_search_results;

  DROP TABLE IF EXISTS temp_search_results;
END;
$$ LANGUAGE plpgsql;

-- Query: Semantic search with text query (auto-embed)
CREATE OR REPLACE FUNCTION semantic_search_text(
  p_case_id UUID,
  p_query_text TEXT,
  p_user_id UUID,
  p_similarity_threshold FLOAT DEFAULT 0.7,
  p_include_privileged BOOLEAN DEFAULT false,
  p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  content_snippet TEXT,
  similarity_score FLOAT,
  document_date DATE,
  is_privileged BOOLEAN
) AS $$
BEGIN
  -- Note: In production, this would call an embedding API to convert text to vector
  -- For now, fall back to text search
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    LEFT(dc.content, 300) as content_snippet,
    ts_rank(
      to_tsvector('english', dc.content),
      plainto_tsquery('english', p_query_text)
    )::FLOAT as similarity_score,
    d.document_date,
    d.is_privileged
  FROM documents d
  JOIN document_chunks dc ON d.id = dc.document_id
  WHERE d.case_id = p_case_id
    AND d.is_deleted = false
    AND (p_include_privileged = true OR d.is_privileged = false)
    AND to_tsvector('english', dc.content) @@ plainto_tsquery('english', p_query_text)
  ORDER BY similarity_score DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- PRIVILEGE LOG QUERIES
-- =====================================================================

-- Query: Generate privilege log export
CREATE OR REPLACE FUNCTION export_privilege_log(
  p_case_id UUID,
  p_format TEXT DEFAULT 'detailed' -- 'detailed' or 'summary'
)
RETURNS TABLE (
  entry_number INTEGER,
  document_id TEXT,
  bates_number TEXT,
  document_date DATE,
  author TEXT,
  recipients TEXT,
  description TEXT,
  privilege_type privilege_type,
  privilege_basis TEXT,
  pages INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ROW_NUMBER() OVER (ORDER BY pl.document_date DESC NULLS LAST)::INTEGER,
    COALESCE(pl.document_number, d.id::TEXT),
    pl.bates_number,
    COALESCE(pl.document_date, d.document_date),
    COALESCE(pl.author, d.author),
    array_to_string(COALESCE(pl.recipients, d.recipient), '; '),
    pl.description,
    pl.privilege_type,
    pl.privilege_basis,
    COALESCE(pl.page_count, d.page_count)
  FROM privilege_logs pl
  JOIN documents d ON pl.document_id = d.id
  WHERE pl.case_id = p_case_id
    AND pl.withheld = true
  ORDER BY pl.document_date DESC NULLS LAST, pl.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- PRODUCTION SET QUERIES
-- =====================================================================

-- Query: Get documents for production request
CREATE OR REPLACE FUNCTION get_production_documents(
  p_discovery_request_id UUID,
  p_include_redacted BOOLEAN DEFAULT true
)
RETURNS TABLE (
  production_number TEXT,
  bates_number TEXT,
  document_id UUID,
  title TEXT,
  document_date DATE,
  author TEXT,
  page_count INTEGER,
  is_redacted BOOLEAN,
  file_path TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    dp.production_number,
    dp.bates_number,
    d.id,
    d.title,
    d.document_date,
    d.author,
    d.page_count,
    dp.is_redacted,
    d.file_path
  FROM discovery_productions dp
  JOIN documents d ON dp.document_id = d.id
  WHERE dp.discovery_request_id = p_discovery_request_id
    AND (p_include_redacted = true OR dp.is_redacted = false)
  ORDER BY dp.bates_number, dp.production_number;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Find responsive documents for discovery request
CREATE OR REPLACE FUNCTION find_responsive_documents(
  p_case_id UUID,
  p_search_terms TEXT[],
  p_start_date DATE DEFAULT NULL,
  p_end_date DATE DEFAULT NULL,
  p_exclude_privileged BOOLEAN DEFAULT true
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  document_date DATE,
  author TEXT,
  matched_terms TEXT[],
  relevance_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    d.document_date,
    d.author,
    ARRAY(
      SELECT term
      FROM unnest(p_search_terms) AS term
      WHERE d.extracted_text ILIKE '%' || term || '%'
    ) as matched_terms,
    ts_rank(
      to_tsvector('english', COALESCE(d.extracted_text, '')),
      to_tsquery('english', array_to_string(p_search_terms, ' | '))
    ) as relevance_score
  FROM documents d
  WHERE d.case_id = p_case_id
    AND d.is_deleted = false
    AND (p_exclude_privileged = false OR d.is_privileged = false)
    AND (p_start_date IS NULL OR d.document_date >= p_start_date)
    AND (p_end_date IS NULL OR d.document_date <= p_end_date)
    AND to_tsvector('english', COALESCE(d.extracted_text, '')) @@
        to_tsquery('english', array_to_string(p_search_terms, ' | '))
  ORDER BY relevance_score DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- RELATIONSHIP QUERIES
-- =====================================================================

-- Query: Get document threads (email chains, amendments)
CREATE OR REPLACE FUNCTION get_document_thread(
  p_document_id UUID,
  p_max_depth INTEGER DEFAULT 5
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  document_date DATE,
  author TEXT,
  relationship_type TEXT,
  depth INTEGER
) AS $$
BEGIN
  RETURN QUERY
  WITH RECURSIVE doc_thread AS (
    -- Base case: the document itself
    SELECT
      d.id,
      d.title,
      d.document_date,
      d.author,
      'origin'::TEXT as relationship_type,
      0 as depth
    FROM documents d
    WHERE d.id = p_document_id

    UNION ALL

    -- Recursive case: related documents
    SELECT
      d.id,
      d.title,
      d.document_date,
      d.author,
      dr.relationship_type,
      dt.depth + 1
    FROM doc_thread dt
    JOIN document_relationships dr ON dt.document_id = dr.source_document_id
    JOIN documents d ON dr.target_document_id = d.id
    WHERE dt.depth < p_max_depth
  )
  SELECT * FROM doc_thread
  ORDER BY depth, document_date;
END;
$$ LANGUAGE plpgsql STABLE;

-- Query: Find documents by party involvement
CREATE OR REPLACE FUNCTION find_documents_by_party(
  p_case_id UUID,
  p_party_name TEXT,
  p_role TEXT DEFAULT 'any' -- 'author', 'recipient', 'any'
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  document_date DATE,
  author TEXT,
  recipients TEXT[],
  party_role TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    d.document_date,
    d.author,
    d.recipient,
    CASE
      WHEN d.author ILIKE '%' || p_party_name || '%' THEN 'author'
      WHEN EXISTS(SELECT 1 FROM unnest(d.recipient) AS r WHERE r ILIKE '%' || p_party_name || '%') THEN 'recipient'
      ELSE 'mentioned'
    END as party_role
  FROM documents d
  WHERE d.case_id = p_case_id
    AND d.is_deleted = false
    AND (
      (p_role IN ('author', 'any') AND d.author ILIKE '%' || p_party_name || '%') OR
      (p_role IN ('recipient', 'any') AND EXISTS(
        SELECT 1 FROM unnest(d.recipient) AS r WHERE r ILIKE '%' || p_party_name || '%'
      ))
    )
  ORDER BY d.document_date DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- ANALYTICS QUERIES
-- =====================================================================

-- Query: Document clustering by content similarity
CREATE OR REPLACE FUNCTION cluster_documents_by_similarity(
  p_case_id UUID,
  p_cluster_threshold FLOAT DEFAULT 0.85,
  p_min_cluster_size INTEGER DEFAULT 2
)
RETURNS TABLE (
  cluster_id INTEGER,
  document_ids UUID[],
  representative_title TEXT,
  cluster_size INTEGER,
  avg_similarity FLOAT
) AS $$
BEGIN
  -- Note: This is a simplified version. Production would use more sophisticated clustering
  RETURN QUERY
  WITH similarities AS (
    SELECT
      e1.document_id as doc1,
      e2.document_id as doc2,
      cosine_similarity(e1.embedding, e2.embedding) as similarity
    FROM document_embeddings e1
    JOIN document_embeddings e2 ON e1.case_id = e2.case_id AND e1.document_id < e2.document_id
    WHERE e1.case_id = p_case_id
      AND e1.status = 'completed'
      AND e2.status = 'completed'
      AND cosine_similarity(e1.embedding, e2.embedding) >= p_cluster_threshold
  ),
  clusters AS (
    SELECT
      ROW_NUMBER() OVER () as cluster_id,
      ARRAY_AGG(DISTINCT doc_id) as document_ids,
      COUNT(DISTINCT doc_id) as cluster_size,
      AVG(similarity) as avg_similarity
    FROM (
      SELECT doc1 as doc_id, similarity FROM similarities
      UNION
      SELECT doc2 as doc_id, similarity FROM similarities
    ) clustered_docs
    GROUP BY doc1, doc2
    HAVING COUNT(DISTINCT doc_id) >= p_min_cluster_size
  )
  SELECT
    c.cluster_id,
    c.document_ids,
    (SELECT title FROM documents WHERE id = c.document_ids[1]) as representative_title,
    c.cluster_size,
    c.avg_similarity::FLOAT
  FROM clusters c
  ORDER BY c.cluster_size DESC, c.avg_similarity DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON FUNCTION search_documents IS 'Advanced document search with multiple filters and full-text search';
COMMENT ON FUNCTION semantic_search IS 'Semantic search using vector embeddings with audit logging';
COMMENT ON FUNCTION find_similar_documents IS 'Find similar documents for duplicate detection';
COMMENT ON FUNCTION export_privilege_log IS 'Generate privilege log for production';
COMMENT ON FUNCTION get_document_thread IS 'Get document thread/chain (emails, amendments)';
COMMENT ON FUNCTION find_responsive_documents IS 'Find documents responsive to discovery request';
