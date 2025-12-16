-- =====================================================================
-- SEMANTIC SEARCH FUNCTIONS
-- Purpose: Core functions for semantic search using pgvector
-- Version: 1.0.0
-- =====================================================================

-- =====================================================================
-- MAIN SEMANTIC SEARCH FUNCTION (Optimized for performance)
-- =====================================================================

CREATE OR REPLACE FUNCTION search_by_embedding(
  p_query_embedding vector(1536),
  p_case_id UUID,
  p_user_id UUID,
  p_limit INTEGER DEFAULT 10,
  p_similarity_threshold FLOAT DEFAULT 0.7,
  p_filters JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  document_id UUID,
  chunk_id UUID,
  title TEXT,
  content TEXT,
  similarity FLOAT,
  document_date DATE,
  author TEXT,
  is_privileged BOOLEAN,
  page_number INTEGER,
  metadata JSONB
) AS $$
DECLARE
  v_start_time TIMESTAMPTZ := clock_timestamp();
  v_execution_time INTEGER;
  v_results_count INTEGER;
  v_include_privileged BOOLEAN;
BEGIN
  -- Extract filters
  v_include_privileged := COALESCE((p_filters->>'include_privileged')::BOOLEAN, false);

  -- Check if user can access privileged documents
  IF v_include_privileged THEN
    v_include_privileged := EXISTS(
      SELECT 1 FROM users u
      WHERE u.id = p_user_id
        AND u.role IN ('super_admin', 'firm_admin', 'lead_attorney', 'associate_attorney')
    );
  END IF;

  -- Perform search using HNSW index (optimized)
  RETURN QUERY
  SELECT
    d.id,
    dc.id,
    d.title,
    dc.content,
    cosine_similarity(p_query_embedding, de.embedding) as similarity,
    d.document_date,
    d.author,
    d.is_privileged,
    dc.page_number,
    jsonb_build_object(
      'file_name', d.file_name,
      'chunk_index', dc.chunk_index,
      'word_count', dc.word_count
    ) as metadata
  FROM document_embeddings de
  INNER JOIN document_chunks dc ON de.chunk_id = dc.id
  INNER JOIN documents d ON de.document_id = d.id
  WHERE
    de.case_id = p_case_id
    AND de.status = 'completed'
    AND d.is_deleted = false
    AND (v_include_privileged OR d.is_privileged = false)
    AND cosine_similarity(p_query_embedding, de.embedding) >= p_similarity_threshold
    -- Apply date filters
    AND (
      (p_filters->>'start_date' IS NULL) OR
      (d.document_date >= (p_filters->>'start_date')::DATE)
    )
    AND (
      (p_filters->>'end_date' IS NULL) OR
      (d.document_date <= (p_filters->>'end_date')::DATE)
    )
    -- Apply author filter
    AND (
      (p_filters->>'author' IS NULL) OR
      (d.author ILIKE '%' || (p_filters->>'author') || '%')
    )
    -- Apply tag filter
    AND (
      (p_filters->>'tags' IS NULL) OR
      (d.tags && string_to_array(p_filters->>'tags', ','))
    )
  ORDER BY similarity DESC
  LIMIT p_limit;

  -- Get result count
  GET DIAGNOSTICS v_results_count = ROW_COUNT;

  -- Calculate execution time
  v_execution_time := EXTRACT(MILLISECOND FROM clock_timestamp() - v_start_time)::INTEGER;

  -- Log search to semantic_search_history
  INSERT INTO semantic_search_history (
    user_id,
    case_id,
    query_text,
    query_embedding,
    filters,
    results_count,
    execution_time_ms,
    search_config
  ) VALUES (
    p_user_id,
    p_case_id,
    'Vector similarity search',
    p_query_embedding,
    p_filters,
    v_results_count,
    v_execution_time,
    jsonb_build_object(
      'limit', p_limit,
      'similarity_threshold', p_similarity_threshold
    )
  );
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- HYBRID SEARCH (Combine semantic + keyword search)
-- =====================================================================

CREATE OR REPLACE FUNCTION hybrid_search(
  p_query_text TEXT,
  p_query_embedding vector(1536),
  p_case_id UUID,
  p_user_id UUID,
  p_limit INTEGER DEFAULT 10,
  p_semantic_weight FLOAT DEFAULT 0.5, -- 0.0 = keyword only, 1.0 = semantic only
  p_filters JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
  document_id UUID,
  chunk_id UUID,
  title TEXT,
  content TEXT,
  combined_score FLOAT,
  semantic_score FLOAT,
  keyword_score FLOAT,
  document_date DATE,
  is_privileged BOOLEAN
) AS $$
DECLARE
  v_keyword_weight FLOAT := 1.0 - p_semantic_weight;
BEGIN
  RETURN QUERY
  WITH semantic_results AS (
    SELECT
      de.document_id,
      dc.id as chunk_id,
      cosine_similarity(p_query_embedding, de.embedding) as score
    FROM document_embeddings de
    INNER JOIN document_chunks dc ON de.chunk_id = dc.id
    INNER JOIN documents d ON de.document_id = d.id
    WHERE
      de.case_id = p_case_id
      AND de.status = 'completed'
      AND d.is_deleted = false
      AND cosine_similarity(p_query_embedding, de.embedding) >= 0.5
  ),
  keyword_results AS (
    SELECT
      d.id as document_id,
      dc.id as chunk_id,
      ts_rank(
        to_tsvector('english', dc.content),
        plainto_tsquery('english', p_query_text)
      ) as score
    FROM documents d
    INNER JOIN document_chunks dc ON d.id = dc.document_id
    WHERE
      d.case_id = p_case_id
      AND d.is_deleted = false
      AND to_tsvector('english', dc.content) @@ plainto_tsquery('english', p_query_text)
  ),
  combined AS (
    SELECT
      COALESCE(sr.document_id, kr.document_id) as document_id,
      COALESCE(sr.chunk_id, kr.chunk_id) as chunk_id,
      (COALESCE(sr.score, 0) * p_semantic_weight + COALESCE(kr.score, 0) * v_keyword_weight) as combined_score,
      COALESCE(sr.score, 0) as semantic_score,
      COALESCE(kr.score, 0) as keyword_score
    FROM semantic_results sr
    FULL OUTER JOIN keyword_results kr
      ON sr.document_id = kr.document_id AND sr.chunk_id = kr.chunk_id
  )
  SELECT
    c.document_id,
    c.chunk_id,
    d.title,
    dc.content,
    c.combined_score,
    c.semantic_score,
    c.keyword_score,
    d.document_date,
    d.is_privileged
  FROM combined c
  INNER JOIN documents d ON c.document_id = d.id
  INNER JOIN document_chunks dc ON c.chunk_id = dc.id
  ORDER BY c.combined_score DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- MULTI-VECTOR SEARCH (Search across multiple embeddings)
-- =====================================================================

CREATE OR REPLACE FUNCTION multi_vector_search(
  p_query_embeddings vector(1536)[],
  p_case_id UUID,
  p_user_id UUID,
  p_limit INTEGER DEFAULT 10,
  p_aggregation_method TEXT DEFAULT 'max' -- 'max', 'avg', 'min'
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  aggregated_similarity FLOAT,
  chunk_similarities FLOAT[],
  best_chunk_id UUID,
  best_chunk_content TEXT
) AS $$
BEGIN
  RETURN QUERY
  WITH vector_similarities AS (
    SELECT
      de.document_id,
      de.chunk_id,
      dc.content,
      ARRAY_AGG(
        cosine_similarity(v, de.embedding)
        ORDER BY cosine_similarity(v, de.embedding) DESC
      ) as similarities
    FROM unnest(p_query_embeddings) v
    CROSS JOIN document_embeddings de
    INNER JOIN document_chunks dc ON de.chunk_id = dc.id
    INNER JOIN documents d ON de.document_id = d.id
    WHERE
      de.case_id = p_case_id
      AND de.status = 'completed'
      AND d.is_deleted = false
    GROUP BY de.document_id, de.chunk_id, dc.content
  ),
  aggregated AS (
    SELECT
      vs.document_id,
      vs.chunk_id,
      vs.content,
      vs.similarities,
      CASE p_aggregation_method
        WHEN 'max' THEN (SELECT MAX(s) FROM unnest(vs.similarities) s)
        WHEN 'avg' THEN (SELECT AVG(s) FROM unnest(vs.similarities) s)
        WHEN 'min' THEN (SELECT MIN(s) FROM unnest(vs.similarities) s)
        ELSE (SELECT MAX(s) FROM unnest(vs.similarities) s)
      END as agg_similarity
    FROM vector_similarities vs
  ),
  ranked AS (
    SELECT
      a.*,
      ROW_NUMBER() OVER (PARTITION BY a.document_id ORDER BY a.agg_similarity DESC) as rn
    FROM aggregated a
  )
  SELECT
    r.document_id,
    d.title,
    r.agg_similarity,
    r.similarities,
    r.chunk_id,
    r.content
  FROM ranked r
  INNER JOIN documents d ON r.document_id = d.id
  WHERE r.rn = 1
  ORDER BY r.agg_similarity DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- CONTEXTUAL SEARCH (Search with context window)
-- =====================================================================

CREATE OR REPLACE FUNCTION contextual_search(
  p_query_embedding vector(1536),
  p_case_id UUID,
  p_user_id UUID,
  p_context_chunks INTEGER DEFAULT 2, -- Number of chunks before/after to include
  p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
  document_id UUID,
  title TEXT,
  matched_chunk_index INTEGER,
  context_content TEXT,
  similarity FLOAT,
  context_chunks JSONB
) AS $$
BEGIN
  RETURN QUERY
  WITH matched_chunks AS (
    SELECT
      de.document_id,
      dc.id as chunk_id,
      dc.chunk_index,
      dc.content,
      d.title,
      cosine_similarity(p_query_embedding, de.embedding) as similarity
    FROM document_embeddings de
    INNER JOIN document_chunks dc ON de.chunk_id = dc.id
    INNER JOIN documents d ON de.document_id = d.id
    WHERE
      de.case_id = p_case_id
      AND de.status = 'completed'
      AND d.is_deleted = false
      AND cosine_similarity(p_query_embedding, de.embedding) >= 0.7
    ORDER BY similarity DESC
    LIMIT p_limit
  ),
  with_context AS (
    SELECT
      mc.document_id,
      mc.title,
      mc.chunk_index,
      mc.similarity,
      STRING_AGG(
        ctx.content,
        E'\n\n---\n\n'
        ORDER BY ctx.chunk_index
      ) as context_content,
      jsonb_agg(
        jsonb_build_object(
          'chunk_index', ctx.chunk_index,
          'content', ctx.content,
          'is_matched', ctx.chunk_index = mc.chunk_index
        )
        ORDER BY ctx.chunk_index
      ) as context_chunks
    FROM matched_chunks mc
    INNER JOIN document_chunks ctx
      ON mc.document_id = ctx.document_id
      AND ctx.chunk_index BETWEEN (mc.chunk_index - p_context_chunks) AND (mc.chunk_index + p_context_chunks)
    GROUP BY mc.document_id, mc.title, mc.chunk_index, mc.similarity
  )
  SELECT
    wc.document_id,
    wc.title,
    wc.chunk_index,
    wc.context_content,
    wc.similarity,
    wc.context_chunks
  FROM with_context wc
  ORDER BY wc.similarity DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- FILTERED SEMANTIC SEARCH (Optimized with pre-filtering)
-- =====================================================================

CREATE OR REPLACE FUNCTION filtered_semantic_search(
  p_query_embedding vector(1536),
  p_case_id UUID,
  p_document_ids UUID[] DEFAULT NULL,
  p_date_range daterange DEFAULT NULL,
  p_privilege_filter BOOLEAN DEFAULT NULL,
  p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  document_id UUID,
  chunk_id UUID,
  content TEXT,
  similarity FLOAT,
  document_metadata JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    dc.id,
    dc.content,
    cosine_similarity(p_query_embedding, de.embedding) as similarity,
    jsonb_build_object(
      'title', d.title,
      'date', d.document_date,
      'author', d.author,
      'is_privileged', d.is_privileged,
      'page_number', dc.page_number
    ) as document_metadata
  FROM document_embeddings de
  INNER JOIN document_chunks dc ON de.chunk_id = dc.id
  INNER JOIN documents d ON de.document_id = d.id
  WHERE
    de.case_id = p_case_id
    AND de.status = 'completed'
    AND d.is_deleted = false
    AND (p_document_ids IS NULL OR d.id = ANY(p_document_ids))
    AND (p_date_range IS NULL OR d.document_date <@ p_date_range)
    AND (p_privilege_filter IS NULL OR d.is_privileged = p_privilege_filter)
  ORDER BY de.embedding <=> p_query_embedding -- Using distance operator for index
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- SEARCH SUGGESTIONS (Find related search terms)
-- =====================================================================

CREATE OR REPLACE FUNCTION get_search_suggestions(
  p_partial_query TEXT,
  p_case_id UUID DEFAULT NULL,
  p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  suggestion TEXT,
  search_count BIGINT,
  avg_results INTEGER,
  last_used TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    sal.search_query,
    COUNT(*) as search_count,
    ROUND(AVG(sal.results_count))::INTEGER as avg_results,
    MAX(sal.created_at) as last_used
  FROM search_audit_logs sal
  WHERE
    (p_case_id IS NULL OR sal.case_id = p_case_id)
    AND sal.search_query ILIKE p_partial_query || '%'
    AND sal.created_at >= NOW() - INTERVAL '90 days'
  GROUP BY sal.search_query
  ORDER BY search_count DESC, last_used DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- PERFORMANCE OPTIMIZATION HELPER
-- =====================================================================

-- Set optimal HNSW search parameters based on dataset size
CREATE OR REPLACE FUNCTION optimize_search_parameters(p_case_id UUID)
RETURNS JSONB AS $$
DECLARE
  v_embedding_count BIGINT;
  v_params JSONB;
BEGIN
  -- Count embeddings for this case
  SELECT COUNT(*)
  INTO v_embedding_count
  FROM document_embeddings
  WHERE case_id = p_case_id AND status = 'completed';

  -- Determine optimal parameters
  v_params := jsonb_build_object(
    'ef_search', CASE
      WHEN v_embedding_count < 10000 THEN 40
      WHEN v_embedding_count < 100000 THEN 100
      ELSE 200
    END,
    'probes', CASE
      WHEN v_embedding_count < 10000 THEN 1
      WHEN v_embedding_count < 100000 THEN 10
      ELSE 20
    END,
    'embedding_count', v_embedding_count,
    'recommended_threshold', CASE
      WHEN v_embedding_count < 10000 THEN 0.7
      ELSE 0.75
    END
  );

  RETURN v_params;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================================
-- COMMENTS
-- =====================================================================

COMMENT ON FUNCTION search_by_embedding IS 'Main semantic search function using vector embeddings with optimized performance';
COMMENT ON FUNCTION hybrid_search IS 'Combine semantic and keyword search for better results';
COMMENT ON FUNCTION multi_vector_search IS 'Search using multiple query embeddings (for complex queries)';
COMMENT ON FUNCTION contextual_search IS 'Semantic search with surrounding context chunks';
COMMENT ON FUNCTION filtered_semantic_search IS 'Optimized semantic search with pre-filtering';
COMMENT ON FUNCTION get_search_suggestions IS 'Get search suggestions based on previous queries';
COMMENT ON FUNCTION optimize_search_parameters IS 'Get optimal search parameters for current dataset size';
