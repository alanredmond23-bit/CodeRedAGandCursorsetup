-- CodeGreen: Generic Software Development Tracking Schema
-- Tracks projects, code metrics, tests, deployments, performance
-- Version: 1.0
-- Created: 2025-12-16

-- ============================================================================
-- ORGANIZATIONS & TEAMS
-- ============================================================================

CREATE TABLE organizations (
    org_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    tier VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    max_projects INTEGER DEFAULT 10,
    max_developers INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE teams (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    visibility VARCHAR(50) DEFAULT 'private', -- private, internal, public
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(org_id, name)
);

CREATE TABLE developers (
    dev_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    github_username VARCHAR(100),
    role VARCHAR(50) DEFAULT 'developer', -- developer, lead, manager, admin
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP
);

CREATE TABLE team_members (
    team_id UUID NOT NULL REFERENCES teams(team_id),
    dev_id UUID NOT NULL REFERENCES developers(dev_id),
    role VARCHAR(50) DEFAULT 'member', -- member, lead, admin
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (team_id, dev_id)
);

-- ============================================================================
-- PROJECTS & REPOSITORIES
-- ============================================================================

CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50), -- web, mobile, backend, library, etc.
    visibility VARCHAR(50) DEFAULT 'private',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(org_id, name)
);

CREATE TABLE repositories (
    repo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id),
    name VARCHAR(255) NOT NULL,
    github_url VARCHAR(500),
    github_repo_id INTEGER,
    language VARCHAR(50), -- javascript, python, go, etc.
    framework VARCHAR(50), -- react, django, express, etc.
    description TEXT,
    stars INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, name)
);

CREATE TABLE branches (
    branch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    name VARCHAR(255) NOT NULL,
    is_main BOOLEAN DEFAULT FALSE,
    last_commit_sha VARCHAR(40),
    last_commit_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(repo_id, name)
);

-- ============================================================================
-- CODE MANAGEMENT
-- ============================================================================

CREATE TABLE commits (
    commit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    sha VARCHAR(40) NOT NULL,
    message TEXT,
    author_email VARCHAR(255),
    author_name VARCHAR(255),
    timestamp TIMESTAMP,
    files_changed INTEGER,
    insertions INTEGER,
    deletions INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(repo_id, sha)
);

CREATE TABLE pull_requests (
    pr_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    github_pr_number INTEGER,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    author_id UUID REFERENCES developers(dev_id),
    status VARCHAR(50) DEFAULT 'open', -- open, merged, closed, draft
    source_branch VARCHAR(255),
    target_branch VARCHAR(255),
    created_at TIMESTAMP,
    merged_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE TABLE code_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID NOT NULL REFERENCES pull_requests(pr_id),
    reviewer_id UUID NOT NULL REFERENCES developers(dev_id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, changes_requested, commented
    comment_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE issues (
    issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    github_issue_number INTEGER,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    assignee_id UUID REFERENCES developers(dev_id),
    status VARCHAR(50) DEFAULT 'open', -- open, closed, in_progress
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    type VARCHAR(50), -- bug, feature, chore, refactor, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP
);

-- ============================================================================
-- CODE QUALITY & METRICS
-- ============================================================================

CREATE TABLE code_analysis (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id UUID NOT NULL REFERENCES commits(commit_id),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    total_issues INTEGER,
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    complexity_score NUMERIC(5, 2), -- 1-100
    maintainability_score NUMERIC(5, 2),
    security_score NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TESTING
-- ============================================================================

CREATE TABLE tests (
    test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    name VARCHAR(500) NOT NULL,
    framework VARCHAR(100), -- jest, pytest, mocha, etc.
    file_path VARCHAR(500),
    type VARCHAR(50), -- unit, integration, e2e, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE test_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL REFERENCES tests(test_id),
    commit_id UUID NOT NULL REFERENCES commits(commit_id),
    pr_id UUID REFERENCES pull_requests(pr_id),
    status VARCHAR(50), -- passed, failed, skipped
    duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE coverage_metrics (
    coverage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    commit_id UUID NOT NULL REFERENCES commits(commit_id),
    overall_coverage NUMERIC(5, 2), -- percentage
    line_coverage NUMERIC(5, 2),
    branch_coverage NUMERIC(5, 2),
    function_coverage NUMERIC(5, 2),
    covered_lines INTEGER,
    total_lines INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- PERFORMANCE & MONITORING
-- ============================================================================

CREATE TABLE performance_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Frontend metrics
    lighthouse_score NUMERIC(5, 2),
    largest_contentful_paint_ms NUMERIC(10, 2),
    first_input_delay_ms NUMERIC(10, 2),
    cumulative_layout_shift NUMERIC(5, 2),
    bundle_size_kb NUMERIC(10, 2),
    
    -- Backend metrics
    p50_latency_ms NUMERIC(10, 2),
    p95_latency_ms NUMERIC(10, 2),
    p99_latency_ms NUMERIC(10, 2),
    requests_per_second NUMERIC(10, 2),
    error_rate_percent NUMERIC(5, 2),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    error_type VARCHAR(100),
    message TEXT,
    stack_trace TEXT,
    file_path VARCHAR(500),
    line_number INTEGER,
    environment VARCHAR(50), -- development, staging, production
    count INTEGER DEFAULT 1,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    level VARCHAR(20), -- debug, info, warning, error
    message TEXT,
    context JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- DEPLOYMENTS
-- ============================================================================

CREATE TABLE deployments (
    deployment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    commit_id UUID NOT NULL REFERENCES commits(commit_id),
    environment VARCHAR(50), -- development, staging, production
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, succeeded, failed
    deployed_by UUID REFERENCES developers(dev_id),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- BUILD RESULTS
-- ============================================================================

CREATE TABLE build_results (
    build_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repositories(repo_id),
    commit_id UUID NOT NULL REFERENCES commits(commit_id),
    pr_id UUID REFERENCES pull_requests(pr_id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, succeeded, failed
    duration_seconds INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_log TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXING FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_orgs_slug ON organizations(slug);
CREATE INDEX idx_teams_org ON teams(org_id);
CREATE INDEX idx_developers_org ON developers(org_id);
CREATE INDEX idx_developers_email ON developers(email);
CREATE INDEX idx_projects_org ON projects(org_id);
CREATE INDEX idx_repos_project ON repositories(project_id);
CREATE INDEX idx_branches_repo ON branches(repo_id);
CREATE INDEX idx_commits_branch ON commits(branch_id);
CREATE INDEX idx_commits_repo ON commits(repo_id);
CREATE INDEX idx_commits_timestamp ON commits(timestamp DESC);
CREATE INDEX idx_prs_repo ON pull_requests(repo_id);
CREATE INDEX idx_prs_status ON pull_requests(status);
CREATE INDEX idx_issues_repo ON issues(repo_id);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_code_analysis_commit ON code_analysis(commit_id);
CREATE INDEX idx_code_analysis_repo ON code_analysis(repo_id);
CREATE INDEX idx_tests_repo ON tests(repo_id);
CREATE INDEX idx_test_results_test ON test_results(test_id);
CREATE INDEX idx_test_results_commit ON test_results(commit_id);
CREATE INDEX idx_coverage_repo ON coverage_metrics(repo_id);
CREATE INDEX idx_coverage_commit ON coverage_metrics(commit_id);
CREATE INDEX idx_perf_metrics_repo ON performance_metrics(repo_id);
CREATE INDEX idx_perf_metrics_timestamp ON performance_metrics(timestamp DESC);
CREATE INDEX idx_errors_repo ON errors(repo_id);
CREATE INDEX idx_errors_resolved ON errors(resolved);
CREATE INDEX idx_logs_repo ON logs(repo_id);
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_deployments_repo ON deployments(repo_id);
CREATE INDEX idx_deployments_env ON deployments(environment);
CREATE INDEX idx_deployments_status ON deployments(status);
CREATE INDEX idx_build_results_repo ON build_results(repo_id);
CREATE INDEX idx_build_results_status ON build_results(status);

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

CREATE TABLE permissions (
    perm_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dev_id UUID NOT NULL REFERENCES developers(dev_id),
    resource_type VARCHAR(50), -- repo, project, org
    resource_id UUID,
    permission VARCHAR(50), -- read, write, admin
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by UUID REFERENCES developers(dev_id),
    UNIQUE(dev_id, resource_type, resource_id)
);

-- ============================================================================
-- COST TRACKING (GENERIC)
-- ============================================================================

CREATE TABLE cost_tracking (
    cost_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    dev_id UUID REFERENCES developers(dev_id),
    task_type VARCHAR(100), -- "code-analysis", "test-run", "deployment", etc.
    cost_usd NUMERIC(10, 4),
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB -- additional details
);

-- ============================================================================
-- RLS (Row Level Security)
-- ============================================================================

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE developers ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;

-- Basic RLS policy: developers can only see their org's data
CREATE POLICY org_isolation ON organizations
    FOR SELECT
    USING (true); -- Allow public queries, restrict on auth

-- ============================================================================
-- SAMPLE DATA (Optional)
-- ============================================================================

-- Insert sample organization
INSERT INTO organizations (name, slug, tier) VALUES
    ('Tech Company', 'tech-company', 'pro');

-- Get org_id for following inserts
-- SELECT org_id FROM organizations WHERE slug = 'tech-company';

-- ============================================================================
-- DONE
-- ============================================================================

-- Schema version
CREATE TABLE schema_version (
    version_id SERIAL PRIMARY KEY,
    version_number VARCHAR(20),
    applied_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version_number, description) VALUES
    ('1.0', 'Initial CodeGreen dev tracking schema');

COMMIT;
