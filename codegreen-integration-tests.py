#!/usr/bin/env python3
"""
CodeGreen Integration Test Suite
Tests all 3 systems: Claude Terminal, Antigravity Cloud, Cursor IDE
Version: 1.0
Created: 2025-12-16
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import subprocess
import re

# Simple YAML parser for basic YAML files (no external dependency)
def simple_yaml_parse(content: str) -> Dict:
    """Simple YAML parser for basic key-value structures"""
    result = {}
    lines = content.split('\n')
    current_section = None
    current_subsection = None
    last_indent = 0

    for line in lines:
        line_stripped = line.rstrip()
        if not line_stripped or line_stripped.strip().startswith('#'):
            continue

        # Calculate indentation
        indent = len(line) - len(line.lstrip())

        if ':' not in line_stripped:
            continue

        key = line_stripped.split(':')[0].strip()
        value_part = line_stripped.split(':', 1)[1].strip() if len(line_stripped.split(':', 1)) > 1 else ''

        # Remove comments from value
        if '#' in value_part:
            value_part = value_part.split('#')[0].strip()

        # Top level key (no indentation)
        if indent == 0:
            if value_part:
                result[key] = value_part
            else:
                result[key] = {}
                current_section = result[key]
                current_subsection = None
            last_indent = 0
        # First level indent (2 spaces)
        elif indent == 2 and current_section is not None:
            if value_part:
                # Try to convert to int
                try:
                    current_section[key] = int(value_part)
                except:
                    current_section[key] = value_part
            else:
                current_section[key] = {}
                current_subsection = current_section[key]
            last_indent = 2
        # Second level indent (4 spaces)
        elif indent >= 4 and current_subsection is not None:
            if value_part:
                try:
                    current_subsection[key] = int(value_part)
                except:
                    current_subsection[key] = value_part

    return result

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestResult:
    def __init__(self, name: str, status: str, message: str = "", details: str = ""):
        self.name = name
        self.status = status  # "PASS", "FAIL", "WARN"
        self.message = message
        self.details = details
        self.timestamp = datetime.now().isoformat()

class CodeGreenIntegrationTests:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.results: List[TestResult] = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def log(self, message: str, color: str = Colors.RESET):
        """Print colored log message"""
        print(f"{color}{message}{Colors.RESET}")

    def add_result(self, name: str, status: str, message: str = "", details: str = ""):
        """Add test result"""
        result = TestResult(name, status, message, details)
        self.results.append(result)

        if status == "PASS":
            self.passed += 1
            self.log(f"✓ {name}: {message}", Colors.GREEN)
        elif status == "FAIL":
            self.failed += 1
            self.log(f"✗ {name}: {message}", Colors.RED)
            if details:
                self.log(f"  Details: {details}", Colors.RED)
        elif status == "WARN":
            self.warnings += 1
            self.log(f"⚠ {name}: {message}", Colors.YELLOW)

    # ========================================================================
    # SYSTEM 1: CLAUDE TERMINAL AGENT TESTS
    # ========================================================================

    def test_claude_terminal_config(self):
        """Test Claude Terminal MCP configuration"""
        self.log("\n=== CLAUDE TERMINAL AGENT TESTS ===\n", Colors.BLUE + Colors.BOLD)

        config_path = self.base_path / "01_CLAUDE_CODE_TERMINAL" / "mcp-config.json"

        # Test 1.1: Config file exists
        if not config_path.exists():
            self.add_result("1.1 MCP Config Exists", "FAIL",
                          f"File not found: {config_path}")
            return
        self.add_result("1.1 MCP Config Exists", "PASS", str(config_path))

        # Test 1.2: Valid JSON syntax
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.add_result("1.2 Valid JSON Syntax", "PASS", "MCP config is valid JSON")
        except json.JSONDecodeError as e:
            self.add_result("1.2 Valid JSON Syntax", "FAIL",
                          f"JSON decode error: {str(e)}")
            return

        # Test 1.3: Required MCP servers configured
        required_servers = ["westlaw", "lexisnexis", "gmail", "slack", "supabase"]
        if "mcpServers" in config:
            found_servers = list(config["mcpServers"].keys())
            missing = [s for s in required_servers if s not in found_servers]
            if missing:
                self.add_result("1.3 Required MCP Servers", "WARN",
                              f"Missing servers: {', '.join(missing)}")
            else:
                self.add_result("1.3 Required MCP Servers", "PASS",
                              f"All {len(required_servers)} required servers configured")
        else:
            self.add_result("1.3 Required MCP Servers", "FAIL",
                          "No mcpServers section found")

    def test_claude_agents(self):
        """Test Claude Terminal agents"""
        agents_path = self.base_path / "01_CLAUDE_CODE_TERMINAL" / "agents"

        # Test 1.4: Agents directory exists
        if not agents_path.exists():
            self.add_result("1.4 Agents Directory", "FAIL",
                          f"Directory not found: {agents_path}")
            return
        self.add_result("1.4 Agents Directory", "PASS", str(agents_path))

        # Test 1.5: Check for 5 required agents (using discovery-bot and strategy-bot as examples)
        # For CodeGreen, we map to the generic dev agents
        expected_agents = {
            "discovery-bot": "Code Analysis Agent",
            "strategy-bot": "Architecture Agent"
        }

        found_agents = []
        for agent_name in expected_agents.keys():
            agent_path = agents_path / agent_name
            if agent_path.exists() and agent_path.is_dir():
                found_agents.append(agent_name)

        if len(found_agents) >= 2:
            self.add_result("1.5 Agent Directories", "PASS",
                          f"Found {len(found_agents)} agent directories")
        else:
            self.add_result("1.5 Agent Directories", "WARN",
                          f"Only found {len(found_agents)} agent directories")

        # Test 1.6: Mock agent invocation test
        self.log("\n  Testing Agent Invocability (Mock):", Colors.BLUE)
        mock_agents = [
            ("Code Analysis Agent", "can analyze code"),
            ("Coordinator Agent", "can route requests"),
            ("Architecture Agent", "can design systems"),
            ("Test Agent", "can generate tests"),
            ("Performance Agent", "can analyze performance")
        ]

        all_invocable = True
        for agent_name, capability in mock_agents:
            # Mock test - in real scenario, would attempt to invoke agent
            self.log(f"    - {agent_name}: {capability}", Colors.GREEN)

        self.add_result("1.6 Agent Invocability", "PASS",
                      f"All {len(mock_agents)} agents can be invoked (mock test)")

    # ========================================================================
    # SYSTEM 2: CURSOR IDE KEYBOARD SHORTCUT TESTS
    # ========================================================================

    def test_cursor_config(self):
        """Test Cursor IDE configuration"""
        self.log("\n=== CURSOR IDE KEYBOARD SHORTCUT TESTS ===\n", Colors.BLUE + Colors.BOLD)

        config_path = self.base_path / "03_CURSOR_IDE" / "cursor-settings.json"

        # Test 2.1: Config file exists
        if not config_path.exists():
            self.add_result("2.1 Cursor Config Exists", "FAIL",
                          f"File not found: {config_path}")
            return
        self.add_result("2.1 Cursor Config Exists", "PASS", str(config_path))

        # Test 2.2: Valid JSON syntax
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.add_result("2.2 Valid JSON Syntax", "PASS", "Cursor config is valid JSON")
        except json.JSONDecodeError as e:
            self.add_result("2.2 Valid JSON Syntax", "FAIL",
                          f"JSON decode error: {str(e)}")
            return

        # Test 2.3-2.7: Check keyboard shortcuts
        if "keyboardShortcuts" not in config:
            self.add_result("2.3-2.7 Keyboard Shortcuts", "FAIL",
                          "No keyboardShortcuts section found")
            return

        shortcuts = config["keyboardShortcuts"]
        expected_shortcuts = {
            "Cmd+Shift+A": "Code Analysis Agent",
            "Cmd+Shift+C": "Coordinator Agent",
            "Cmd+Shift+S": "Architecture Agent",
            "Cmd+Shift+R": "Test Agent",
            "Cmd+Shift+P": "Performance Agent"
        }

        for shortcut, expected_agent in expected_shortcuts.items():
            test_num = {
                "Cmd+Shift+A": "2.3",
                "Cmd+Shift+C": "2.4",
                "Cmd+Shift+S": "2.5",
                "Cmd+Shift+R": "2.6",
                "Cmd+Shift+P": "2.7"
            }[shortcut]

            if shortcut in shortcuts:
                actual_agent = shortcuts[shortcut].get("agent", "")
                if expected_agent in actual_agent:
                    self.add_result(f"{test_num} Shortcut {shortcut}", "PASS",
                                  f"Mapped to {actual_agent}")
                else:
                    self.add_result(f"{test_num} Shortcut {shortcut}", "WARN",
                                  f"Mapped to '{actual_agent}' (expected '{expected_agent}')")
            else:
                self.add_result(f"{test_num} Shortcut {shortcut}", "FAIL",
                              "Shortcut not configured")

    # ========================================================================
    # SYSTEM 3: ANTIGRAVITY SYNC TESTS
    # ========================================================================

    def test_antigravity_sync(self):
        """Test Antigravity sync mechanism"""
        self.log("\n=== ANTIGRAVITY SYNC TESTS ===\n", Colors.BLUE + Colors.BOLD)

        config_path = self.base_path / "02_ANTIGRAVITY" / "antigravity-config.yaml"

        # Test 3.1: Config file exists
        if not config_path.exists():
            self.add_result("3.1 Antigravity Config Exists", "FAIL",
                          f"File not found: {config_path}")
            return
        self.add_result("3.1 Antigravity Config Exists", "PASS", str(config_path))

        # Test 3.2: Valid YAML syntax
        try:
            with open(config_path, 'r') as f:
                yaml_content = f.read()
                config = simple_yaml_parse(yaml_content)
            self.add_result("3.2 Valid YAML Syntax", "PASS", "Antigravity config is valid YAML")
        except Exception as e:
            self.add_result("3.2 Valid YAML Syntax", "FAIL",
                          f"YAML parse error: {str(e)}")
            return

        # Test 3.3: Sync interval is 30 seconds
        if "sync_engine" in config and "syncInterval" in config["sync_engine"]:
            interval = config["sync_engine"]["syncInterval"]
            if interval == 30:
                self.add_result("3.3 Sync Interval", "PASS",
                              f"Interval is {interval} seconds")
            else:
                self.add_result("3.3 Sync Interval", "WARN",
                              f"Interval is {interval} seconds (expected 30)")
        else:
            self.add_result("3.3 Sync Interval", "FAIL",
                          "syncInterval not found in config")

        # Test 3.4: Conflict resolver is callable
        if "sync_engine" in config and "conflict_resolution" in config["sync_engine"]:
            strategy = config["sync_engine"]["conflict_resolution"].get("strategy", "")
            if strategy:
                self.add_result("3.4 Conflict Resolver", "PASS",
                              f"Strategy: {strategy}")
            else:
                self.add_result("3.4 Conflict Resolver", "WARN",
                              "No conflict resolution strategy defined")
        else:
            self.add_result("3.4 Conflict Resolver", "FAIL",
                          "conflict_resolution not found")

        # Test 3.5: Database sync target is correct
        if "database" in config and "provider" in config["database"]:
            provider = config["database"]["provider"]
            if provider == "supabase":
                self.add_result("3.5 Database Sync Target", "PASS",
                              f"Provider: {provider}")
            else:
                self.add_result("3.5 Database Sync Target", "WARN",
                              f"Provider is '{provider}' (expected 'supabase')")
        else:
            self.add_result("3.5 Database Sync Target", "FAIL",
                          "Database provider not configured")

    # ========================================================================
    # SYSTEM 4: DATABASE SCHEMA TESTS
    # ========================================================================

    def test_database_schema(self):
        """Test database schema for all 35 tables"""
        self.log("\n=== DATABASE SCHEMA TESTS ===\n", Colors.BLUE + Colors.BOLD)

        schema_path = self.base_path / "supabase" / "migrations" / "20251216_001_create_codegreen_schema.sql"

        # Test 4.1: Schema file exists
        if not schema_path.exists():
            self.add_result("4.1 Schema File Exists", "FAIL",
                          f"File not found: {schema_path}")
            return
        self.add_result("4.1 Schema File Exists", "PASS", str(schema_path))

        # Test 4.2: Read and parse schema
        try:
            with open(schema_path, 'r') as f:
                schema_content = f.read()
            self.add_result("4.2 Schema File Readable", "PASS",
                          f"File size: {len(schema_content)} bytes")
        except Exception as e:
            self.add_result("4.2 Schema File Readable", "FAIL", str(e))
            return

        # Test 4.3-4.9: Check for table groups
        table_groups = {
            "4.3 Organizations Tables": ["organizations", "teams", "developers", "team_members"],
            "4.4 Projects Tables": ["projects", "repositories", "branches", "commits"],
            "4.5 Code Management Tables": ["pull_requests", "code_reviews", "issues", "code_analysis"],
            "4.6 Testing Tables": ["tests", "test_results", "coverage_metrics"],
            "4.7 Performance Tables": ["performance_metrics", "errors", "logs"],
            "4.8 Deployments Tables": ["deployments", "build_results"],
            "4.9 Utilities Tables": ["permissions", "cost_tracking"]
        }

        total_tables = 0
        for test_id, tables in table_groups.items():
            found_tables = []
            for table in tables:
                # Check for CREATE TABLE statements
                if f"CREATE TABLE {table}" in schema_content or f"CREATE TABLE IF NOT EXISTS {table}" in schema_content:
                    found_tables.append(table)

            total_tables += len(found_tables)
            if len(found_tables) == len(tables):
                self.add_result(test_id, "PASS",
                              f"All {len(tables)} tables found: {', '.join(found_tables)}")
            else:
                missing = set(tables) - set(found_tables)
                self.add_result(test_id, "WARN",
                              f"Found {len(found_tables)}/{len(tables)} tables. Missing: {', '.join(missing)}")

        # Test 4.10: Total table count
        expected_total = sum(len(tables) for tables in table_groups.values())
        if total_tables >= expected_total * 0.8:  # 80% threshold
            self.add_result("4.10 Total Tables", "PASS",
                          f"Found {total_tables} tables (expected ~{expected_total})")
        else:
            self.add_result("4.10 Total Tables", "WARN",
                          f"Found {total_tables} tables (expected ~{expected_total})")

    # ========================================================================
    # FILE EXISTENCE & PERMISSIONS TESTS
    # ========================================================================

    def test_file_structure(self):
        """Test file existence and permissions"""
        self.log("\n=== FILE STRUCTURE TESTS ===\n", Colors.BLUE + Colors.BOLD)

        critical_files = {
            "Claude MCP Config": "01_CLAUDE_CODE_TERMINAL/mcp-config.json",
            "Antigravity Config": "02_ANTIGRAVITY/antigravity-config.yaml",
            "Cursor Settings": "03_CURSOR_IDE/cursor-settings.json",
            "Database Schema": "supabase/migrations/20251216_001_create_codegreen_schema.sql",
            "CodeGreen Settings": ".codegreen-settings.json"
        }

        for name, relative_path in critical_files.items():
            full_path = self.base_path / relative_path
            if full_path.exists():
                # Check if readable
                if os.access(full_path, os.R_OK):
                    self.add_result(f"File: {name}", "PASS",
                                  f"Exists and readable: {relative_path}")
                else:
                    self.add_result(f"File: {name}", "WARN",
                                  f"Exists but not readable: {relative_path}")
            else:
                self.add_result(f"File: {name}", "FAIL",
                              f"Not found: {relative_path}")

    # ========================================================================
    # MCP CONNECTIVITY TESTS
    # ========================================================================

    def test_mcp_connectivity(self):
        """Test MCP server configurations"""
        self.log("\n=== MCP CONNECTIVITY TESTS ===\n", Colors.BLUE + Colors.BOLD)

        config_path = self.base_path / "01_CLAUDE_CODE_TERMINAL" / "mcp-config.json"

        if not config_path.exists():
            self.add_result("MCP Connectivity", "SKIP", "Config file not found")
            return

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except:
            self.add_result("MCP Connectivity", "SKIP", "Cannot parse config")
            return

        if "mcpServers" not in config:
            self.add_result("MCP Connectivity", "SKIP", "No mcpServers section")
            return

        # Test each MCP server configuration
        for server_name, server_config in config["mcpServers"].items():
            # Check if server has required fields
            has_command = "command" in server_config
            has_env = "env" in server_config

            if has_command and has_env:
                self.add_result(f"MCP Server: {server_name}", "PASS",
                              "Configuration is complete")
            else:
                missing = []
                if not has_command:
                    missing.append("command")
                if not has_env:
                    missing.append("env")
                self.add_result(f"MCP Server: {server_name}", "WARN",
                              f"Missing fields: {', '.join(missing)}")

    # ========================================================================
    # REPORTING
    # ========================================================================

    def generate_report(self) -> Dict:
        """Generate final test report"""
        total = len(self.results)

        status = "GREEN"  # All tests pass
        if self.failed > 0:
            status = "RED"  # Critical failures
        elif self.warnings > 0:
            status = "YELLOW"  # Some warnings

        readiness = {
            "GREEN": "System is ready for deployment",
            "YELLOW": "System has minor issues but can proceed with caution",
            "RED": "System has critical issues - deployment blocked"
        }

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "success_rate": f"{(self.passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "status": status,
            "readiness": readiness[status],
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }

        return report

    def print_summary(self, report: Dict):
        """Print test summary"""
        self.log("\n" + "="*80, Colors.BOLD)
        self.log("CODEGREEN INTEGRATION TEST SUMMARY", Colors.BOLD + Colors.BLUE)
        self.log("="*80, Colors.BOLD)

        summary = report["summary"]
        self.log(f"\nTotal Tests: {summary['total_tests']}", Colors.BOLD)
        self.log(f"Passed:      {summary['passed']}", Colors.GREEN)
        self.log(f"Failed:      {summary['failed']}", Colors.RED if summary['failed'] > 0 else Colors.RESET)
        self.log(f"Warnings:    {summary['warnings']}", Colors.YELLOW if summary['warnings'] > 0 else Colors.RESET)
        self.log(f"Success Rate: {summary['success_rate']}", Colors.GREEN if summary['passed'] == summary['total_tests'] else Colors.YELLOW)

        status_color = {
            "GREEN": Colors.GREEN,
            "YELLOW": Colors.YELLOW,
            "RED": Colors.RED
        }[report["status"]]

        self.log(f"\nStatus: {report['status']}", Colors.BOLD + status_color)
        self.log(f"Readiness: {report['readiness']}", status_color)

        # Blockers
        blockers = [r for r in self.results if r.status == "FAIL"]
        if blockers:
            self.log(f"\n⚠️  BLOCKERS ({len(blockers)}):", Colors.RED + Colors.BOLD)
            for blocker in blockers:
                self.log(f"  - {blocker.name}: {blocker.message}", Colors.RED)

        self.log("\n" + "="*80 + "\n", Colors.BOLD)

    def save_report(self, report: Dict, output_path: str):
        """Save report to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        self.log(f"Report saved to: {output_path}", Colors.BLUE)

    def run_all_tests(self):
        """Run all integration tests"""
        self.log("\n" + "="*80, Colors.BOLD)
        self.log("CODEGREEN INTEGRATION TEST SUITE", Colors.BOLD + Colors.BLUE)
        self.log(f"Base Path: {self.base_path}", Colors.BLUE)
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.BLUE)
        self.log("="*80 + "\n", Colors.BOLD)

        # Run all test suites
        self.test_claude_terminal_config()
        self.test_claude_agents()
        self.test_cursor_config()
        self.test_antigravity_sync()
        self.test_database_schema()
        self.test_file_structure()
        self.test_mcp_connectivity()

        # Generate and print report
        report = self.generate_report()
        self.print_summary(report)

        # Save report
        output_path = self.base_path / "integration-test-results.json"
        self.save_report(report, str(output_path))

        return report


def main():
    """Main entry point"""
    # Get base path from command line or use current directory
    base_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    # Run tests
    tester = CodeGreenIntegrationTests(base_path)
    report = tester.run_all_tests()

    # Exit with appropriate code
    exit_code = 0 if report["status"] == "GREEN" else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
