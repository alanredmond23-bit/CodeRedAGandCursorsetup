# CodeRed Legal Tech Orchestration - Integration Test Suite

## Overview

Comprehensive integration test suite validating all 9 agents, MCPs, sync systems, and legal compliance for the CodeRed Legal Tech platform.

## Test Coverage

### Core Agents (5)
1. **Discovery Bot** - Document extraction, entity recognition, privilege detection
2. **Coordinator Bot** - Attorney workflow management
3. **Strategy Bot** - Legal research and precedent analysis
4. **Evidence Bot** - Pattern recognition and contradiction detection
5. **Case Analysis Bot** - Holistic case assessment

### Sync Systems (3)
6. **Claude Terminal Sync** - Bidirectional sync with Supabase
7. **Antigravity Sync** - Cloud orchestration sync
8. **Cursor Integration** - IDE integration

### Infrastructure (3)
9. **MCP Connections** - Westlaw, LexisNexis, Gmail, Slack, Supabase, GitHub
10. **Supabase Database** - Database operations, RAG, cost tracking
11. **GitHub Actions** - CI/CD pipeline validation

### Compliance (2)
12. **Legal Compliance** - Privilege protection, audit trails, discovery compliance
13. **Cost Tracking** - Cost accuracy within 0.1%

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install pytest pytest-asyncio pytest-mock

# Set up test environment
cp .env.example .env.test
# Edit .env.test with test credentials
```

### Run All Tests

```bash
# Run complete test suite
python integration-test-runner.py

# Run specific test file
pytest tests/test-discovery-bot.py -v

# Run tests with markers
pytest -m "asyncio" -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py                    # Package init
├── conftest.py                    # Shared fixtures and test data
├── test-discovery-bot.py          # Discovery Bot tests
├── test-coordinator-bot.py        # Coordinator Bot tests
├── test-strategy-bot.py           # Strategy Bot tests
├── test-evidence-bot.py           # Evidence Bot tests
├── test-case-analysis-bot.py      # Case Analysis Bot tests
├── test-claude-sync.py            # Claude Terminal sync tests
├── test-antigravity-sync.py       # Antigravity sync tests
├── test-cursor-integration.py     # Cursor IDE tests
├── test-mcps.py                   # MCP connection tests
├── test-supabase.py               # Database tests
├── test-github-actions.py         # CI/CD tests
├── test-legal-compliance.py       # Legal compliance tests
└── test-cost-tracking.py          # Cost validation tests
```

## Success Criteria

### Production Readiness Checklist

- [x] All agent tests pass
- [x] Legal compliance verified
- [x] Costs accurate to within 0.1%
- [x] Sync works bidirectionally
- [x] MCPs connect and respond
- [x] No data loss
- [x] Performance acceptable (1000+ docs/day)
- [x] Audit trail complete
- [x] Privilege protection enforced
- [x] Zone restrictions enforced

## Running Integration Tests

### Full Suite

```bash
# Run all tests with production readiness check
python integration-test-runner.py

# Expected output:
# ✅ All Agent Tests Pass
# ✅ Legal Compliance Verified
# ✅ Cost Accuracy Validated
# ✅ MCPs Connected
# ✅ Sync Bidirectional
# ✅ Database Operations Work
# ✅ CI/CD Pipeline Ready
# 🎉 SYSTEM READY FOR PRODUCTION DEPLOYMENT
```

---

**Last Updated**: December 16, 2025
**Version**: 1.0.0
**Status**: Production Ready
