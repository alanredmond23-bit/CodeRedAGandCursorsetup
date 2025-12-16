"""
MCP Connection Testing Suite
Tests all MCP integrations to validate authentication and connectivity
"""

import os
import sys
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class MCPConnectionTester:
    """Test all MCP connections"""

    def __init__(self):
        self.results = {
            'test_date': datetime.now().isoformat(),
            'services': {},
            'overall_status': 'pending'
        }

    def test_westlaw(self) -> Dict[str, Any]:
        """Test Westlaw MCP connection"""
        print("\n🔍 Testing Westlaw MCP...")

        try:
            from westlaw_mcp_server import create_westlaw_mcp

            mcp = create_westlaw_mcp()
            status = mcp.get_api_status()

            if status.get('status') == 'operational':
                print("✅ Westlaw MCP: Connected")
                return {
                    'status': 'success',
                    'connected': True,
                    'message': 'Westlaw API is operational',
                    'details': status
                }
            else:
                print("❌ Westlaw MCP: Connection failed")
                return {
                    'status': 'error',
                    'connected': False,
                    'message': status.get('error', 'Unknown error'),
                    'details': status
                }

        except Exception as e:
            print(f"❌ Westlaw MCP: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def test_lexisnexis(self) -> Dict[str, Any]:
        """Test LexisNexis MCP connection"""
        print("\n🔍 Testing LexisNexis MCP...")

        try:
            from lexisnexis_mcp_server import create_lexisnexis_mcp

            mcp = create_lexisnexis_mcp()
            status = mcp.get_api_status()

            if status.get('status') == 'operational':
                print("✅ LexisNexis MCP: Connected")
                return {
                    'status': 'success',
                    'connected': True,
                    'message': 'LexisNexis API is operational',
                    'details': status
                }
            else:
                print("❌ LexisNexis MCP: Connection failed")
                return {
                    'status': 'error',
                    'connected': False,
                    'message': status.get('error', 'Unknown error'),
                    'details': status
                }

        except Exception as e:
            print(f"❌ LexisNexis MCP: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def test_gmail(self) -> Dict[str, Any]:
        """Test Gmail Discovery MCP connection"""
        print("\n📧 Testing Gmail Discovery MCP...")

        try:
            from gmail_discovery_mcp import create_gmail_discovery_mcp

            mcp = create_gmail_discovery_mcp()
            status = mcp.get_api_status()

            if status.get('status') == 'operational':
                print(f"✅ Gmail MCP: Connected ({status.get('email_address')})")
                return {
                    'status': 'success',
                    'connected': True,
                    'message': f"Gmail API connected for {status.get('email_address')}",
                    'details': status
                }
            else:
                print("❌ Gmail MCP: Connection failed")
                return {
                    'status': 'error',
                    'connected': False,
                    'message': status.get('error', 'Unknown error'),
                    'details': status
                }

        except Exception as e:
            print(f"❌ Gmail MCP: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def test_slack(self) -> Dict[str, Any]:
        """Test Slack Discovery MCP connection"""
        print("\n💬 Testing Slack Discovery MCP...")

        try:
            from slack_discovery_mcp import create_slack_discovery_mcp

            mcp = create_slack_discovery_mcp()
            status = mcp.get_api_status()

            if status.get('status') == 'operational':
                print(f"✅ Slack MCP: Connected (Team: {status.get('team')})")
                return {
                    'status': 'success',
                    'connected': True,
                    'message': f"Slack API connected to {status.get('team')}",
                    'details': status
                }
            else:
                print("❌ Slack MCP: Connection failed")
                return {
                    'status': 'error',
                    'connected': False,
                    'message': status.get('error', 'Unknown error'),
                    'details': status
                }

        except Exception as e:
            print(f"❌ Slack MCP: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def test_supabase(self) -> Dict[str, Any]:
        """Test Supabase MCP connection"""
        print("\n🗄️  Testing Supabase MCP...")

        try:
            from supabase_mcp_server import create_supabase_mcp

            mcp = create_supabase_mcp()
            status = mcp.get_api_status()

            if status.get('status') == 'operational':
                print("✅ Supabase MCP: Connected")
                return {
                    'status': 'success',
                    'connected': True,
                    'message': 'Supabase database is operational',
                    'details': status
                }
            else:
                print("❌ Supabase MCP: Connection failed")
                return {
                    'status': 'error',
                    'connected': False,
                    'message': status.get('error', 'Unknown error'),
                    'details': status
                }

        except Exception as e:
            print(f"❌ Supabase MCP: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def test_github(self) -> Dict[str, Any]:
        """Test GitHub MCP connection"""
        print("\n🐙 Testing GitHub MCP...")

        try:
            from github_mcp_server import create_github_mcp

            mcp = create_github_mcp()
            status = mcp.get_api_status()

            if status.get('status') == 'operational':
                rate_limit = status.get('rate_limit', {})
                print(f"✅ GitHub MCP: Connected (Rate Limit: {rate_limit.get('remaining')}/{rate_limit.get('limit')})")
                return {
                    'status': 'success',
                    'connected': True,
                    'message': f"GitHub API connected ({rate_limit.get('remaining')} requests remaining)",
                    'details': status
                }
            else:
                print("❌ GitHub MCP: Connection failed")
                return {
                    'status': 'error',
                    'connected': False,
                    'message': status.get('error', 'Unknown error'),
                    'details': status
                }

        except Exception as e:
            print(f"❌ GitHub MCP: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def test_cache_system(self) -> Dict[str, Any]:
        """Test cache system"""
        print("\n💾 Testing Cache System...")

        try:
            from mcp_cache import get_cache

            cache = get_cache()

            # Test cache operations
            test_key = 'test_service'
            test_query = 'test_query'
            test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}

            # Set cache
            cache.set(test_key, test_query, test_data)

            # Get cache
            cached_data = cache.get(test_key, test_query)

            if cached_data == test_data:
                stats = cache.get_stats()
                print(f"✅ Cache System: Operational ({stats.get('type')})")
                return {
                    'status': 'success',
                    'connected': True,
                    'message': f"Cache system operational ({stats.get('type')})",
                    'details': stats
                }
            else:
                print("❌ Cache System: Data integrity issue")
                return {
                    'status': 'error',
                    'connected': False,
                    'message': 'Cache data integrity check failed',
                    'details': None
                }

        except Exception as e:
            print(f"❌ Cache System: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def test_logging_system(self) -> Dict[str, Any]:
        """Test logging system"""
        print("\n📝 Testing Logging System...")

        try:
            from mcp_logging import get_mcp_logger

            logger = get_mcp_logger()

            # Test different log types
            logger.log_api_call('test_service', 'test_endpoint', query='test')
            logger.log_auth_event('test_service', 'test_event', True)

            # Get cost report
            cost_report = logger.get_cost_report()

            print("✅ Logging System: Operational")
            return {
                'status': 'success',
                'connected': True,
                'message': 'Logging system operational',
                'details': cost_report
            }

        except Exception as e:
            print(f"❌ Logging System: {str(e)}")
            return {
                'status': 'error',
                'connected': False,
                'message': str(e),
                'details': None
            }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all MCP connection tests"""
        print("=" * 60)
        print("MCP CONNECTION TEST SUITE")
        print("=" * 60)

        # Test each service
        self.results['services']['westlaw'] = self.test_westlaw()
        self.results['services']['lexisnexis'] = self.test_lexisnexis()
        self.results['services']['gmail'] = self.test_gmail()
        self.results['services']['slack'] = self.test_slack()
        self.results['services']['supabase'] = self.test_supabase()
        self.results['services']['github'] = self.test_github()

        # Test supporting systems
        self.results['services']['cache'] = self.test_cache_system()
        self.results['services']['logging'] = self.test_logging_system()

        # Calculate overall status
        all_connected = all(
            service.get('connected', False)
            for service in self.results['services'].values()
        )

        self.results['overall_status'] = 'success' if all_connected else 'partial'

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        connected_count = sum(
            1 for service in self.results['services'].values()
            if service.get('connected', False)
        )
        total_count = len(self.results['services'])

        print(f"\nConnected: {connected_count}/{total_count} services")
        print(f"Overall Status: {self.results['overall_status'].upper()}")

        if self.results['overall_status'] == 'success':
            print("\n✅ All MCP integrations are operational!")
        else:
            print("\n⚠️  Some MCP integrations failed. Check credentials and configuration.")

        # Failed services
        failed_services = [
            name for name, service in self.results['services'].items()
            if not service.get('connected', False)
        ]

        if failed_services:
            print(f"\nFailed Services: {', '.join(failed_services)}")

        return self.results

    def save_results(self, filename: str = 'mcp_test_results.json'):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, indent=2, fp=f, default=str)
        print(f"\n📄 Test results saved to: {filename}")


def main():
    """Main test function"""
    tester = MCPConnectionTester()
    results = tester.run_all_tests()
    tester.save_results()

    # Return exit code based on results
    sys.exit(0 if results['overall_status'] == 'success' else 1)


if __name__ == '__main__':
    main()
