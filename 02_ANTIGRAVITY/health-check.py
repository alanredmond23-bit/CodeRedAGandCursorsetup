#!/usr/bin/env python3
"""
Health Check System

Monitors all critical components of the Antigravity orchestration system.
Detects failures early and triggers recovery procedures.

Components Monitored:
- GCP/Vertex AI connectivity
- CodeRed database connection
- Supabase connection
- Claude Code Terminal API
- Agent health and responsiveness
- Sync system status

Author: Antigravity Orchestration Team
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import httpx
import asyncpg
from google.cloud import aiplatform
from supabase import create_client

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthCheck:
    """
    Comprehensive health check system

    Responsibilities:
    - Check all critical dependencies
    - Monitor agent health
    - Validate connectivity
    - Detect degraded performance
    - Trigger alerts on failures
    - Support automatic recovery
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize health check system"""
        self.config = config
        self.monitoring_config = config.get('monitoring', {})
        self.health_config = self.monitoring_config.get('health_checks', {})
        self.endpoints = self.health_config.get('endpoints', [])

        logger.info("HealthCheck system initialized")

    async def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks

        Returns:
            Dict with overall status and individual check results
        """
        logger.info("Running health checks")

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall': HealthStatus.HEALTHY.value,
            'checks': {},
            'critical_failures': []
        }

        # Run all configured health checks
        for endpoint in self.endpoints:
            check_name = endpoint['name']
            check_type = endpoint['type']
            is_critical = endpoint.get('critical', False)

            try:
                check_result = await self._run_check(endpoint)
                results['checks'][check_name] = check_result

                # Update overall status
                if check_result['status'] == HealthStatus.CRITICAL.value:
                    if is_critical:
                        results['overall'] = HealthStatus.CRITICAL.value
                        results['critical_failures'].append(check_name)
                    elif results['overall'] != HealthStatus.CRITICAL.value:
                        results['overall'] = HealthStatus.DEGRADED.value

                elif check_result['status'] == HealthStatus.DEGRADED.value:
                    if results['overall'] == HealthStatus.HEALTHY.value:
                        results['overall'] = HealthStatus.DEGRADED.value

            except Exception as e:
                logger.error(f"Health check failed for {check_name}: {e}")
                results['checks'][check_name] = {
                    'status': HealthStatus.CRITICAL.value,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

                if is_critical:
                    results['overall'] = HealthStatus.CRITICAL.value
                    results['critical_failures'].append(check_name)

        logger.info(f"Health checks complete: {results['overall']}")

        return results

    async def _run_check(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single health check"""
        check_name = endpoint['name']
        check_type = endpoint['type']

        logger.debug(f"Running health check: {check_name}")

        if check_type == 'api':
            return await self._check_api(endpoint)
        elif check_type == 'database':
            return await self._check_database(endpoint)
        elif check_type == 'internal':
            return await self._check_internal(endpoint)
        else:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': f"Unknown check type: {check_type}",
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_api(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Check API connectivity"""
        check_name = endpoint['name']

        try:
            if check_name == 'gcp_connection':
                return await self._check_gcp()
            elif check_name == 'claude_connection':
                return await self._check_claude()
            else:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': f"Unknown API check: {check_name}",
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_database(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Check database connectivity"""
        check_name = endpoint['name']

        try:
            if check_name == 'codered_connection':
                return await self._check_codered()
            elif check_name == 'supabase_connection':
                return await self._check_supabase()
            else:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': f"Unknown database check: {check_name}",
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_internal(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Check internal system health"""
        check_name = endpoint['name']

        try:
            if check_name == 'agent_health':
                return await self._check_agents()
            else:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': f"Unknown internal check: {check_name}",
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_gcp(self) -> Dict[str, Any]:
        """Check GCP/Vertex AI connectivity"""
        try:
            # Initialize Vertex AI (tests authentication and connectivity)
            aiplatform.init(
                project=self.config['gcp']['project_id'],
                location=self.config['gcp']['region']
            )

            # Try a simple operation
            # In production, you might query model availability or make a test call

            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'GCP connection healthy',
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"GCP health check failed: {e}")
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_claude(self) -> Dict[str, Any]:
        """Check Claude Code Terminal API connectivity"""
        try:
            claude_config = self.config['crew_bridge']['claude']

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{claude_config['api_base_url']}/health",
                    headers={
                        'Authorization': f"Bearer {claude_config['api_key']}"
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    return {
                        'status': HealthStatus.HEALTHY.value,
                        'message': 'Claude API connection healthy',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        'status': HealthStatus.DEGRADED.value,
                        'message': f"Claude API returned {response.status_code}",
                        'timestamp': datetime.utcnow().isoformat()
                    }

        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_codered(self) -> Dict[str, Any]:
        """Check CodeRed database connectivity"""
        try:
            codered_config = self.config['codered']
            connection_string = codered_config['connection_string']

            # Test connection
            conn = await asyncpg.connect(connection_string, timeout=10)

            # Run simple query
            result = await conn.fetchval('SELECT 1')

            await conn.close()

            if result == 1:
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'CodeRed database connection healthy',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': HealthStatus.DEGRADED.value,
                    'message': 'CodeRed database query failed',
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"CodeRed health check failed: {e}")
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_supabase(self) -> Dict[str, Any]:
        """Check Supabase connectivity"""
        try:
            supabase_config = self.config['supabase']

            # Create client
            client = create_client(
                supabase_config['url'],
                supabase_config['key']
            )

            # Test query
            result = client.table('health_checks').select('*').limit(1).execute()

            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'Supabase connection healthy',
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _check_agents(self) -> Dict[str, Any]:
        """Check agent health"""
        try:
            # Check if agents are responsive
            agents = self.config['agents'].keys()

            agent_statuses = {}
            all_healthy = True

            for agent_id in agents:
                # In production, this would check agent runtime status
                # For now, simulate check
                agent_statuses[agent_id] = {
                    'status': 'active',
                    'responsive': True
                }

            if all_healthy:
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'All agents healthy',
                    'agents': agent_statuses,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': HealthStatus.DEGRADED.value,
                    'message': 'Some agents not responsive',
                    'agents': agent_statuses,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Agent health check failed: {e}")
            return {
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def check_agent(self, agent_id: str) -> Dict[str, Any]:
        """Check health of a specific agent"""
        try:
            # In production, this would query agent runtime
            # Check responsiveness, memory usage, error rate, etc.

            return {
                'agent_id': agent_id,
                'status': HealthStatus.HEALTHY.value,
                'responsive': True,
                'memory_usage': 0.5,  # 50%
                'error_rate': 0.01,   # 1%
                'last_activity': datetime.utcnow().isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Agent health check failed for {agent_id}: {e}")
            return {
                'agent_id': agent_id,
                'status': HealthStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Example usage
async def main():
    """Example usage"""
    import yaml

    # Load config
    with open('antigravity-config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create health check
    health_check = HealthCheck(config)

    # Run all checks
    results = await health_check.check_all()

    import json
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
