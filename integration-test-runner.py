#!/usr/bin/env python3
"""
Integration Test Runner - Master Orchestrator
Runs all tests for 9 agents, MCPs, sync systems, and legal compliance
Validates system is ready for production deployment
"""

import sys
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import json


class IntegrationTestRunner:
    """Master test orchestrator for CodeRed Legal Tech system"""

    def __init__(self):
        self.start_time = None
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'test_suites': {},
        }

    def print_header(self):
        """Print test runner header"""
        print("=" * 80)
        print("🧪 CODERED LEGAL TECH INTEGRATION TEST SUITE")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

    def print_section(self, title: str):
        """Print section header"""
        print()
        print(f"{'─' * 80}")
        print(f"📋 {title}")
        print(f"{'─' * 80}")

    async def run_test_suite(self, name: str, file_path: str, markers: str = None) -> Tuple[bool, Dict]:
        """Run a single test suite"""
        print(f"\n🔍 Running: {name}...")

        cmd = ['pytest', file_path, '-v', '--tb=short']

        if markers:
            cmd.extend(['-m', markers])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per suite
            )

            # Parse pytest output
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            # Extract stats
            stats = {
                'passed': output.count(' PASSED'),
                'failed': output.count(' FAILED'),
                'skipped': output.count(' SKIPPED'),
                'output': output,
            }

            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {status} - {stats['passed']} passed, {stats['failed']} failed, {stats['skipped']} skipped")

            return passed, stats

        except subprocess.TimeoutExpired:
            print(f"   ⏱️  TIMEOUT - Test suite exceeded 5 minutes")
            return False, {'passed': 0, 'failed': 1, 'skipped': 0, 'output': 'Timeout'}

        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            return False, {'passed': 0, 'failed': 1, 'skipped': 0, 'output': str(e)}

    async def run_all_tests(self):
        """Run all test suites"""
        self.start_time = datetime.now()
        self.print_header()

        tests_dir = Path(__file__).parent / 'tests'

        # Define test suites
        test_suites = [
            # Core Agent Tests
            ('Discovery Bot', 'tests/test-discovery-bot.py'),
            ('Coordinator Bot', 'tests/test-coordinator-bot.py'),
            ('Strategy Bot', 'tests/test-strategy-bot.py'),
            ('Evidence Bot', 'tests/test-evidence-bot.py'),
            ('Case Analysis Bot', 'tests/test-case-analysis-bot.py'),

            # Integration Tests
            ('Claude Terminal Sync', 'tests/test-claude-sync.py'),
            ('Antigravity Sync', 'tests/test-antigravity-sync.py'),
            ('Cursor Integration', 'tests/test-cursor-integration.py'),

            # Infrastructure Tests
            ('MCP Connections', 'tests/test-mcps.py'),
            ('Supabase Database', 'tests/test-supabase.py'),
            ('GitHub Actions CI/CD', 'tests/test-github-actions.py'),

            # Compliance Tests
            ('Legal Compliance', 'tests/test-legal-compliance.py'),
            ('Cost Tracking', 'tests/test-cost-tracking.py'),
        ]

        all_passed = True

        for name, file_path in test_suites:
            if not Path(file_path).exists():
                print(f"\n⚠️  Skipping: {name} (file not found: {file_path})")
                self.results['skipped'] += 1
                continue

            passed, stats = await self.run_test_suite(name, file_path)

            self.results['test_suites'][name] = {
                'passed': passed,
                'stats': stats,
            }

            self.results['total_tests'] += stats['passed'] + stats['failed'] + stats['skipped']
            self.results['passed'] += stats['passed']
            self.results['failed'] += stats['failed']
            self.results['skipped'] += stats['skipped']

            if not passed:
                all_passed = False
                self.results['errors'].append({
                    'suite': name,
                    'output': stats.get('output', 'Unknown error')
                })

        return all_passed

    def print_summary(self):
        """Print test summary"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print()
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        # Overall stats
        print(f"\nTotal Tests:    {self.results['total_tests']}")
        print(f"✅ Passed:      {self.results['passed']}")
        print(f"❌ Failed:      {self.results['failed']}")
        print(f"⚠️  Skipped:     {self.results['skipped']}")
        print(f"⏱️  Duration:    {elapsed:.2f}s")

        # Pass rate
        if self.results['total_tests'] > 0:
            pass_rate = (self.results['passed'] / self.results['total_tests']) * 100
            print(f"📈 Pass Rate:   {pass_rate:.1f}%")

        # Suite breakdown
        print("\n" + "─" * 80)
        print("Test Suite Results:")
        print("─" * 80)

        for suite_name, suite_data in self.results['test_suites'].items():
            status = "✅" if suite_data['passed'] else "❌"
            stats = suite_data['stats']
            print(f"{status} {suite_name}: {stats['passed']}P / {stats['failed']}F / {stats['skipped']}S")

        # Failed tests
        if self.results['errors']:
            print("\n" + "─" * 80)
            print("❌ Failed Test Suites:")
            print("─" * 80)

            for error in self.results['errors']:
                print(f"\n{error['suite']}:")
                # Print first 500 chars of output
                output_preview = error['output'][:500]
                print(f"  {output_preview}...")

        print("\n" + "=" * 80)

    def print_production_readiness(self, all_passed: bool):
        """Print production readiness assessment"""
        print("🚀 PRODUCTION READINESS ASSESSMENT")
        print("=" * 80)

        checklist = {
            'All Agent Tests Pass': all_passed,
            'Legal Compliance Verified': 'Legal Compliance' in self.results['test_suites'] and
                                          self.results['test_suites']['Legal Compliance']['passed'],
            'Cost Accuracy Validated': 'Cost Tracking' in self.results['test_suites'] and
                                        self.results['test_suites']['Cost Tracking']['passed'],
            'MCPs Connected': 'MCP Connections' in self.results['test_suites'] and
                              self.results['test_suites']['MCP Connections']['passed'],
            'Sync Bidirectional': ('Claude Terminal Sync' in self.results['test_suites'] and
                                   self.results['test_suites']['Claude Terminal Sync']['passed'] and
                                   'Antigravity Sync' in self.results['test_suites'] and
                                   self.results['test_suites']['Antigravity Sync']['passed']),
            'Database Operations Work': 'Supabase Database' in self.results['test_suites'] and
                                        self.results['test_suites']['Supabase Database']['passed'],
            'CI/CD Pipeline Ready': 'GitHub Actions CI/CD' in self.results['test_suites'] and
                                    self.results['test_suites']['GitHub Actions CI/CD']['passed'],
        }

        for check, passed in checklist.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")

        production_ready = all(checklist.values())

        print("\n" + "=" * 80)

        if production_ready:
            print("🎉 SYSTEM READY FOR PRODUCTION DEPLOYMENT")
            print("=" * 80)
            print("\nAll checks passed. System is validated and ready to deploy.")
            print("\nNext steps:")
            print("  1. Deploy to production environment")
            print("  2. Configure production secrets")
            print("  3. Run smoke tests in production")
            print("  4. Monitor initial deployment")
            print("  5. Enable agent orchestration")
        else:
            print("⚠️  SYSTEM NOT READY FOR PRODUCTION")
            print("=" * 80)
            print("\nSome checks failed. Review failed tests and fix issues before deploying.")
            print("\nFailed checks:")
            for check, passed in checklist.items():
                if not passed:
                    print(f"  ❌ {check}")

        print("\n" + "=" * 80)

        return production_ready

    def save_results(self):
        """Save results to JSON file"""
        output_file = Path('test-results.json')

        results_json = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'summary': {
                'total': self.results['total_tests'],
                'passed': self.results['passed'],
                'failed': self.results['failed'],
                'skipped': self.results['skipped'],
            },
            'test_suites': {
                name: {
                    'passed': data['passed'],
                    'stats': {
                        'passed': data['stats']['passed'],
                        'failed': data['stats']['failed'],
                        'skipped': data['stats']['skipped'],
                    }
                }
                for name, data in self.results['test_suites'].items()
            },
        }

        with open(output_file, 'w') as f:
            json.dump(results_json, f, indent=2)

        print(f"\n📄 Results saved to: {output_file}")


async def main():
    """Main entry point"""
    runner = IntegrationTestRunner()

    try:
        all_passed = await runner.run_all_tests()
        runner.print_summary()
        production_ready = runner.print_production_readiness(all_passed)
        runner.save_results()

        # Exit code
        sys.exit(0 if production_ready else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(2)

    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                                                                            ║
    ║                  CODERED LEGAL TECH INTEGRATION TESTS                      ║
    ║                                                                            ║
    ║  Testing: 9 Agents | MCPs | Sync Systems | Legal Compliance | Costs      ║
    ║                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())
