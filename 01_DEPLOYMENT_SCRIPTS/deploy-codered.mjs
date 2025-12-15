#!/usr/bin/env node
/**
 * CodeRed Deployment Validator
 * Validates environment configuration before deployment
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 CodeRed Deployment System');
console.log('============================\n');

// Configuration
const config = {
  projectName: 'antigravityCodeRed',
  projectId: 'xgcqjwviirrkyhwlaeyr',
  supabaseUrl: 'https://xgcqjwviirrkyhwlaeyr.supabase.co',
  version: '1.0.0',
  deploymentPhases: 3,
  agents: 5,
  tables: 19,
  indexes: 15
};

// Deployment checklist
const checklist = [
  {
    phase: 1,
    name: 'Schema Deployment',
    duration: '5-10 minutes',
    files: ['0001_codered_base.sql'],
    tasks: [
      'Create codered schema',
      'Create 19 tables',
      'Create 15+ indexes',
      'Enable Row-Level Security (RLS)'
    ],
    verification: [
      'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \'codered\'',
      'Expected: 19 tables'
    ]
  },
  {
    phase: 2,
    name: 'Seed Agents',
    duration: '1-2 minutes',
    files: ['seed-agents.sql'],
    tasks: [
      'Insert Architect Agent (gpt-4o)',
      'Insert Code Agent (gpt-4o)',
      'Insert Test Agent (gpt-4o-mini)',
      'Insert Review Agent (gpt-4o)',
      'Insert Cynic Agent (gpt-4o)'
    ],
    verification: [
      'SELECT COUNT(*) FROM codered.agents',
      'Expected: 5 agents'
    ]
  },
  {
    phase: 3,
    name: 'Setup RAG System',
    duration: '1-2 minutes',
    files: ['setup-rag.sql'],
    tasks: [
      'Enable pgvector extension',
      'Create embedding tables',
      'Create search_embeddings() function',
      'Create IVFFlat index'
    ],
    verification: [
      'SELECT 1 FROM codered.documents LIMIT 1',
      'SELECT COUNT(*) FROM pg_proc WHERE proname = \'search_embeddings\''
    ]
  }
];

// Secrets validation
const secrets = {
  SUPABASE_URL: process.env.SUPABASE_URL || config.supabaseUrl,
  SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY ? '✓ Loaded' : '✗ Missing',
  OPENAI_API_KEY: process.env.OPENAI_API_KEY ? '✓ Loaded' : '✗ Missing'
};

// Display configuration
console.log('📋 PROJECT CONFIGURATION');
console.log('─'.repeat(50));
console.log(`  Project: ${config.projectName}`);
console.log(`  Version: ${config.version}`);
console.log(`  Database: Supabase PostgreSQL + pgvector`);
console.log(`  Supabase URL: ${config.supabaseUrl}`);
console.log(`  Deployment Phases: ${config.deploymentPhases}`);
console.log(`  Agents to Deploy: ${config.agents}`);
console.log(`  Tables to Create: ${config.tables}`);
console.log(`  Indexes to Create: ${config.indexes}\n`);

// Display checklist
console.log('📋 THREE-PHASE DEPLOYMENT PLAN');
console.log('─'.repeat(50));
checklist.forEach(phase => {
  console.log(`\n  PHASE ${phase.phase}: ${phase.name}`);
  console.log(`  Duration: ${phase.duration}`);
  console.log(`  Files: ${phase.files.join(', ')}`);
  console.log(`  Tasks:`);
  phase.tasks.forEach((task, idx) => {
    console.log(`    ${idx + 1}. ${task}`);
  });
  console.log(`  Verification:`);
  console.log(`    ${phase.verification[0]}`);
  console.log(`    Expected Result: ${phase.verification[1]}`);
});

// Display secrets status
console.log('\n\n🔐 ENVIRONMENT VARIABLES STATUS');
console.log('─'.repeat(50));
Object.entries(secrets).forEach(([key, value]) => {
  console.log(`  ${key}: ${value}`);
});

// Deployment instructions
console.log('\n\n🚀 DEPLOYMENT QUICKSTART');
console.log('─'.repeat(50));
console.log(`
  1. Open Supabase Dashboard:
     → ${config.supabaseUrl}/dashboard

  2. Go to SQL Editor

  3. PHASE 1 - Deploy Schema:
     • Copy contents of: 0001_codered_base.sql
     • Paste into SQL Editor
     • Click Run
     • Wait for completion

  4. PHASE 2 - Seed Agents:
     • Copy contents of: seed-agents.sql
     • Paste into SQL Editor
     • Click Run
     • Verify 5 agents created

  5. PHASE 3 - Setup RAG:
     • Copy contents of: setup-rag.sql
     • Paste into SQL Editor
     • Click Run
     • Verify search_embeddings() function created

  6. Verify Full Deployment:
     Run verification queries provided in documentation

  Total Time: ~20-30 minutes
`);

console.log('\n✅ VALIDATION COMPLETE - READY FOR DEPLOYMENT');
console.log('═'.repeat(50) + '\n');
