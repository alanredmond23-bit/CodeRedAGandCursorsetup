# CodeGreen Integration Tests - Quick Reference

## Running the Tests

### Quick Start
```bash
cd /Users/alanredmond/Desktop/CodeGreen
python3 codegreen-integration-tests.py
```

### What Gets Tested

The test suite automatically verifies:

1. **Claude Terminal Agent System** (6 tests)
   - MCP configuration file exists and is valid JSON
   - All 5 required MCP servers are configured (westlaw, lexisnexis, gmail, slack, supabase)
   - Agent directories exist
   - 5 agents are invocable (Code Analysis, Coordinator, Architecture, Test, Performance)

2. **Cursor IDE Keyboard Shortcuts** (7 tests)
   - Cursor settings file exists and is valid JSON
   - All 5 keyboard shortcuts are properly mapped:
     - `Cmd+Shift+A` → Code Analysis Agent
     - `Cmd+Shift+C` → Coordinator Agent
     - `Cmd+Shift+S` → Architecture Agent
     - `Cmd+Shift+R` → Test Agent
     - `Cmd+Shift+P` → Performance Agent

3. **Antigravity Sync Mechanism** (5 tests)
   - Config file exists and is valid YAML
   - Sync interval is 30 seconds
   - Conflict resolver is configured (source_wins strategy)
   - Database sync target is correct (supabase)

4. **Database Schema** (10 tests)
   - Schema file exists and is readable
   - All 22 required tables are defined:
     - Organizations: 4 tables
     - Projects: 4 tables
     - Code Management: 4 tables
     - Testing: 3 tables
     - Performance: 3 tables
     - Deployments: 2 tables
     - Utilities: 2 tables

5. **File Structure & Permissions** (5 tests)
   - All critical configuration files exist
   - Files have correct read permissions

6. **MCP Server Connectivity** (7 tests)
   - All 7 MCP servers have complete configurations
   - Command paths, environment variables, and capabilities are defined

## Test Output

The test script produces:

### Console Output
- Real-time colored progress indicators
- Green checkmarks (✓) for passed tests
- Red X marks (✗) for failed tests
- Yellow warnings (⚠) for issues

### Generated Files
1. **integration-test-results.json** - Machine-readable test results
2. **INTEGRATION_TEST_REPORT.md** - Detailed human-readable report
3. **TEST_SUMMARY.txt** - Visual summary with ASCII art

## Understanding Results

### Status Indicators

| Status | Meaning | Action |
|--------|---------|--------|
| 🟢 GREEN | All tests passed | Proceed with deployment |
| 🟡 YELLOW | Some warnings present | Review warnings, deploy with caution |
| 🔴 RED | Critical failures | Fix blockers before deployment |

### Success Rate
- **100%** - Perfect, ready to deploy
- **95-99%** - Minor issues, review warnings
- **< 95%** - Critical issues, investigate failures

## Test Files Location

All test files are in: `/Users/alanredmond/Desktop/CodeGreen/`

```
CodeGreen/
├── codegreen-integration-tests.py    ← Main test script
├── integration-test-results.json     ← JSON results
├── INTEGRATION_TEST_REPORT.md        ← Detailed report
├── TEST_SUMMARY.txt                  ← Quick summary
└── RUN_TESTS.md                      ← This file
```

## Re-running Tests

You can run tests as many times as needed:

```bash
# Run from CodeGreen directory
python3 codegreen-integration-tests.py

# Or specify a different base path
python3 codegreen-integration-tests.py /path/to/codegreen
```

## Exit Codes

- **0** - All tests passed (GREEN status)
- **1** - Some tests failed (YELLOW or RED status)

## Troubleshooting

### Common Issues

**Problem:** `ModuleNotFoundError: No module named 'yaml'`
- **Solution:** The script includes a built-in YAML parser, no external dependencies needed

**Problem:** "File not found" errors
- **Solution:** Make sure you're running from the CodeGreen directory

**Problem:** Permission denied
- **Solution:** Check file permissions with `ls -l`

### Getting Help

If tests fail:
1. Check the detailed report: `cat INTEGRATION_TEST_REPORT.md`
2. Review specific test results: `cat integration-test-results.json`
3. Look for BLOCKERS section in TEST_SUMMARY.txt

## Current Status

**Last Run:** 2025-12-16
**Status:** 🟢 GREEN
**Tests Passed:** 40/40 (100%)
**Blockers:** None
**Readiness:** ✅ APPROVED FOR DEPLOYMENT

## What's Next

After all tests pass:

1. **Deploy Systems**
   - Set up Claude Terminal with MCP config
   - Configure Cursor IDE with shortcuts
   - Enable Antigravity sync (30s interval)
   - Deploy Supabase database schema

2. **Post-Deployment**
   - Re-run tests in production environment
   - Monitor sync latency and success rates
   - Verify end-to-end agent functionality

3. **Monitoring**
   - Watch for sync failures
   - Track agent invocation metrics
   - Monitor database performance

---

**Test Suite Version:** 1.0
**Created:** 2025-12-16
**Maintained by:** CodeGreen Integration Team
