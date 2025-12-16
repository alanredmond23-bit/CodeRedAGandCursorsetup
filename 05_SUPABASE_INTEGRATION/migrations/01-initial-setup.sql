-- =====================================================================
-- COMBINED INITIAL MIGRATION
-- Purpose: Complete database setup for legal discovery with RAG
-- Version: 1.0.0
-- Run Order: Execute files in numerical order
-- =====================================================================

-- Run this migration to set up the complete database schema

-- Step 1: Core schema (cases, documents, users)
\i ../0001-legal-discovery-schema.sql

-- Step 2: Vector embeddings and RAG
\i ../0002-vector-embeddings.sql

-- Step 3: Cost tracking and budgets
\i ../0003-cost-tracking.sql

-- Step 4: Audit trail and compliance
\i ../0004-audit-trail.sql

-- Step 5: Privilege detection and management
\i ../0005-privilege-management.sql

-- Step 6: Performance indexes and optimization
\i ../0006-rag-indexes.sql

-- =====================================================================
-- POST-MIGRATION SETUP
-- =====================================================================

-- Create default admin user (replace with actual values)
DO $$
DECLARE
  v_org_id UUID;
  v_user_id UUID;
BEGIN
  -- Create default organization
  INSERT INTO organizations (name, type, email)
  VALUES ('Default Organization', 'law_firm', 'admin@example.com')
  RETURNING id INTO v_org_id;

  -- Create admin user
  INSERT INTO users (organization_id, email, full_name, role, hourly_rate)
  VALUES (
    v_org_id,
    'admin@example.com',
    'System Administrator',
    'super_admin',
    200.00
  )
  RETURNING id INTO v_user_id;

  RAISE NOTICE 'Created default organization: %', v_org_id;
  RAISE NOTICE 'Created admin user: %', v_user_id;
END $$;

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================

-- Verify tables created
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Verify indexes created
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;

-- Verify extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm');

-- Verify functions
SELECT
  proname as function_name,
  pronargs as argument_count,
  pg_get_function_identity_arguments(oid) as arguments
FROM pg_proc
WHERE pronamespace = 'public'::regnamespace
  AND proname LIKE '%search%' OR proname LIKE '%privilege%' OR proname LIKE '%cost%'
ORDER BY proname;

-- =====================================================================
-- PERFORMANCE TUNING RECOMMENDATIONS
-- =====================================================================

SELECT * FROM get_performance_recommendations();

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '=====================================================';
  RAISE NOTICE 'MIGRATION COMPLETED SUCCESSFULLY';
  RAISE NOTICE '=====================================================';
  RAISE NOTICE '';
  RAISE NOTICE 'Database Schema Summary:';
  RAISE NOTICE '  - 19 core tables created';
  RAISE NOTICE '  - Vector embeddings (pgvector) configured';
  RAISE NOTICE '  - Cost tracking enabled';
  RAISE NOTICE '  - Audit trail active';
  RAISE NOTICE '  - Privilege detection configured';
  RAISE NOTICE '  - Performance indexes created';
  RAISE NOTICE '';
  RAISE NOTICE 'Next Steps:';
  RAISE NOTICE '  1. Review and adjust embedding configurations';
  RAISE NOTICE '  2. Configure privilege detection rules for your organization';
  RAISE NOTICE '  3. Set up cost budgets for cases';
  RAISE NOTICE '  4. Import existing documents';
  RAISE NOTICE '  5. Run embedding jobs';
  RAISE NOTICE '';
  RAISE NOTICE 'Maintenance:';
  RAISE NOTICE '  - Run perform_table_maintenance() weekly';
  RAISE NOTICE '  - Run refresh_all_materialized_views() daily';
  RAISE NOTICE '  - Monitor query_cache and cleanup_query_cache() hourly';
  RAISE NOTICE '';
END $$;
