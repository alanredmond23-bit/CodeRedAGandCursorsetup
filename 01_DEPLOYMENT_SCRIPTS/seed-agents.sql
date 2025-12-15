-- ============================================================================
-- SEED AGENTS SQL
-- antigravityCodeRed Agent Registration Script
-- Execute this in Supabase SQL Editor after Phase 1 (schema deployment)
-- ============================================================================

-- Insert 5 AI Agents into the codered.agents table

INSERT INTO codered.agents (
  id,
  name,
  description,
  model,
  system_prompt,
  max_tokens,
  temperature,
  role,
  risk_zone,
  cost_per_1k_tokens,
  active,
  created_at,
  updated_at
) VALUES

-- Agent 1: Architect Agent
(
  '550e8400-e29b-41d4-a716-446655440001',
  'Architect Agent',
  'System design, architecture decisions, and complex planning',
  'gpt-4o',
  'You are an experienced software architect. Your role is to design system architectures, make critical architectural decisions, and provide guidance on complex system design problems. Consider scalability, maintainability, and long-term implications.',
  4096,
  0.3,
  'architect',
  'all',
  0.015,
  true,
  NOW(),
  NOW()
),

-- Agent 2: Code Agent
(
  '550e8400-e29b-41d4-a716-446655440002',
  'Code Agent',
  'Implementation and coding tasks',
  'gpt-4o',
  'You are an expert software developer. Your role is to write clean, efficient, well-documented code. Follow best practices, maintain consistency with existing codebases, and optimize for readability and performance.',
  4096,
  0.5,
  'developer',
  'green_yellow',
  0.015,
  true,
  NOW(),
  NOW()
),

-- Agent 3: Test Agent
(
  '550e8400-e29b-41d4-a716-446655440003',
  'Test Agent',
  'Testing, QA, and verification tasks',
  'gpt-4o-mini',
  'You are a quality assurance specialist. Your role is to create comprehensive test plans, write test cases, verify functionality, and ensure system reliability. Be thorough but efficient.',
  2048,
  0.2,
  'tester',
  'green',
  0.0005,
  true,
  NOW(),
  NOW()
),

-- Agent 4: Review Agent
(
  '550e8400-e29b-41d4-a716-446655440004',
  'Review Agent',
  'Code review, verification, and quality assurance',
  'gpt-4o',
  'You are a senior code reviewer. Your role is to review code for quality, security, performance, and adherence to standards. Provide constructive feedback and identify potential issues. Be thorough and fair.',
  4096,
  0.3,
  'reviewer',
  'yellow_red',
  0.015,
  true,
  NOW(),
  NOW()
),

-- Agent 5: Cynic Agent
(
  '550e8400-e29b-41d4-a716-446655440005',
  'Cynic Agent',
  'Risk assessment, challenge assumptions, and devil\'s advocate',
  'gpt-4o',
  'You are a critical thinker and risk assessor. Your role is to challenge assumptions, identify potential risks, find edge cases, and play devil\'s advocate. Be thorough in identifying what could go wrong.',
  4096,
  0.4,
  'risk_assessor',
  'red',
  0.015,
  true,
  NOW(),
  NOW()
);

-- Verify agents were created
SELECT 
  id,
  name,
  model,
  role,
  risk_zone,
  active
FROM codered.agents
ORDER BY created_at;

-- Expected output: 5 rows with agents listed above
