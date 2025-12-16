#!/usr/bin/env python3
"""
Supabase Bridge

Handles logging, cost tracking, and vector storage for Antigravity system.
Provides real-time monitoring, conflict logging, and health check tracking.

Features:
- Sync log storage
- Conflict resolution logging
- Cost tracking and analytics
- Health check monitoring
- Agent metrics collection
- Vector search for documents

Author: Antigravity Orchestration Team
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from supabase import create_client, Client
import httpx

logger = logging.getLogger(__name__)


class SupabaseBridge:
    """
    Bridge to Supabase for logging and vector storage

    Responsibilities:
    - Log sync operations
    - Log conflicts with full diff
    - Track costs per agent
    - Store health check results
    - Collect agent metrics
    - Vector search for documents
    - Real-time monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Supabase bridge"""
        self.config = config
        self.supabase_config = config.get('supabase', {})
        self.url = self.supabase_config.get('url')
        self.key = self.supabase_config.get('key')
        self.client: Optional[Client] = None
        self.tables = self.supabase_config.get('tables', {})

        self._init_client()

        logger.info("SupabaseBridge initialized")

    def _init_client(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(self.url, self.key)
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    async def log_sync(self, sync_data: Dict[str, Any]):
        """Log sync operation to Supabase"""
        try:
            result = self.client.table(self.tables['sync_logs']).insert({
                'timestamp': sync_data.get('timestamp', datetime.utcnow().isoformat()),
                'direction': sync_data.get('direction'),
                'records_synced': sync_data.get('records_synced', 0),
                'errors_count': len(sync_data.get('errors', [])),
                'cost': sync_data.get('cost', 0.0),
                'duration': sync_data.get('duration', 0.0),
                'status': 'success' if not sync_data.get('errors') else 'partial',
                'details': json.dumps(sync_data)
            }).execute()

            logger.debug("Logged sync operation to Supabase")

        except Exception as e:
            logger.error(f"Failed to log sync to Supabase: {e}")

    async def log_conflict(self, conflict: Dict[str, Any]):
        """Log conflict to Supabase with full details"""
        try:
            result = self.client.table(self.tables['conflict_logs']).insert({
                'conflict_id': conflict.get('conflict_id'),
                'timestamp': conflict.get('timestamp', datetime.utcnow().isoformat()),
                'conflict_type': conflict.get('conflict_type'),
                'agent_id': conflict.get('agent_id'),
                'task_id': conflict.get('task_id'),
                'field_name': conflict.get('field_name'),
                'crew_value': json.dumps(conflict.get('crew_value')),
                'antigrav_value': json.dumps(conflict.get('antigrav_value')),
                'resolution_strategy': conflict.get('resolution_strategy'),
                'resolved_value': json.dumps(conflict.get('resolved_value')),
                'diff': json.dumps(conflict.get('diff', {})),
                'metadata': json.dumps(conflict.get('metadata', {}))
            }).execute()

            logger.debug(f"Logged conflict {conflict.get('conflict_id')} to Supabase")

        except Exception as e:
            logger.error(f"Failed to log conflict to Supabase: {e}")

    async def log_costs(self, cost_data: Dict[str, Any]):
        """Log cost tracking to Supabase"""
        try:
            result = self.client.table(self.tables['cost_tracking']).insert({
                'timestamp': cost_data.get('timestamp', datetime.utcnow().isoformat()),
                'crew_cost': cost_data.get('crew_cost', 0.0),
                'antigrav_cost': cost_data.get('antigrav_cost', 0.0),
                'total_cost': cost_data.get('total_cost', 0.0),
                'cumulative_cost': cost_data.get('cumulative_cost', 0.0),
                'details': json.dumps(cost_data)
            }).execute()

            logger.debug("Logged costs to Supabase")

        except Exception as e:
            logger.error(f"Failed to log costs to Supabase: {e}")

    async def log_health_check(self, health_data: Dict[str, Any]):
        """Log health check results to Supabase"""
        try:
            result = self.client.table(self.tables['health_checks']).insert({
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': health_data.get('overall'),
                'checks': json.dumps(health_data.get('checks', {})),
                'details': json.dumps(health_data)
            }).execute()

            logger.debug("Logged health check to Supabase")

        except Exception as e:
            logger.error(f"Failed to log health check to Supabase: {e}")

    async def log_agent_metrics(self, metrics: Dict[str, Any]):
        """Log agent performance metrics to Supabase"""
        try:
            result = self.client.table(self.tables['agent_metrics']).insert({
                'timestamp': metrics.get('timestamp', datetime.utcnow().isoformat()),
                'agent_id': metrics.get('agent_id'),
                'tokens_used': metrics.get('tokens_used', 0),
                'cost': metrics.get('cost', 0.0),
                'execution_time': metrics.get('execution_time', 0.0),
                'success_rate': metrics.get('success_rate', 1.0),
                'error_count': metrics.get('error_count', 0),
                'details': json.dumps(metrics)
            }).execute()

            logger.debug(f"Logged metrics for agent {metrics.get('agent_id')} to Supabase")

        except Exception as e:
            logger.error(f"Failed to log agent metrics to Supabase: {e}")

    async def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        """Get total costs for a specific date"""
        if date is None:
            date = datetime.utcnow()

        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            result = self.client.table(self.tables['cost_tracking']) \
                .select('total_cost') \
                .gte('timestamp', start_of_day.isoformat()) \
                .lt('timestamp', end_of_day.isoformat()) \
                .execute()

            if result.data:
                return sum(row['total_cost'] for row in result.data)

            return 0.0

        except Exception as e:
            logger.error(f"Failed to get daily cost from Supabase: {e}")
            return 0.0

    async def get_recent_conflicts(
        self,
        limit: int = 100,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent conflicts"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            result = self.client.table(self.tables['conflict_logs']) \
                .select('*') \
                .gte('timestamp', since.isoformat()) \
                .order('timestamp', desc=True) \
                .limit(limit) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to get recent conflicts from Supabase: {e}")
            return []

    async def get_agent_performance(
        self,
        agent_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance metrics for an agent"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            result = self.client.table(self.tables['agent_metrics']) \
                .select('*') \
                .eq('agent_id', agent_id) \
                .gte('timestamp', since.isoformat()) \
                .execute()

            if not result.data:
                return {
                    'agent_id': agent_id,
                    'total_cost': 0.0,
                    'total_tokens': 0,
                    'avg_execution_time': 0.0,
                    'success_rate': 1.0,
                    'total_errors': 0
                }

            # Aggregate metrics
            total_cost = sum(row['cost'] for row in result.data)
            total_tokens = sum(row['tokens_used'] for row in result.data)
            avg_execution_time = sum(row['execution_time'] for row in result.data) / len(result.data)
            success_rate = sum(row['success_rate'] for row in result.data) / len(result.data)
            total_errors = sum(row['error_count'] for row in result.data)

            return {
                'agent_id': agent_id,
                'total_cost': total_cost,
                'total_tokens': total_tokens,
                'avg_execution_time': avg_execution_time,
                'success_rate': success_rate,
                'total_errors': total_errors,
                'sample_count': len(result.data)
            }

        except Exception as e:
            logger.error(f"Failed to get agent performance from Supabase: {e}")
            return {}

    async def save_state(self, state_key: str, state_data: Dict[str, Any]):
        """Save state to Supabase"""
        try:
            # Upsert state
            result = self.client.table('system_state').upsert({
                'state_key': state_key,
                'timestamp': datetime.utcnow().isoformat(),
                'data': json.dumps(state_data)
            }, on_conflict='state_key').execute()

            logger.debug(f"Saved state {state_key} to Supabase")

        except Exception as e:
            logger.error(f"Failed to save state to Supabase: {e}")

    async def load_state(self, state_key: str) -> Optional[Dict[str, Any]]:
        """Load state from Supabase"""
        try:
            result = self.client.table('system_state') \
                .select('data') \
                .eq('state_key', state_key) \
                .limit(1) \
                .execute()

            if result.data:
                return json.loads(result.data[0]['data'])

            return None

        except Exception as e:
            logger.error(f"Failed to load state from Supabase: {e}")
            return None

    async def send_alert(self, alert_data: Dict[str, Any]):
        """Send alert notification"""
        try:
            result = self.client.table('alerts').insert({
                'timestamp': alert_data.get('timestamp', datetime.utcnow().isoformat()),
                'message': alert_data.get('message'),
                'severity': alert_data.get('severity', 'info'),
                'details': json.dumps(alert_data)
            }).execute()

            logger.info(f"Alert sent: {alert_data.get('message')}")

        except Exception as e:
            logger.error(f"Failed to send alert to Supabase: {e}")

    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        Vector search for documents using Supabase pgvector

        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Similarity threshold (0-1)

        Returns:
            List of matching documents with similarity scores
        """
        try:
            # This would use Supabase's vector search capability
            # Requires pgvector extension and embedding generation

            # Generate embedding for query (pseudo-code)
            # query_embedding = await self._generate_embedding(query)

            # Perform vector search
            # result = self.client.rpc('match_documents', {
            #     'query_embedding': query_embedding,
            #     'match_threshold': threshold,
            #     'match_count': limit
            # }).execute()

            # For now, return empty list (implement when vector store is set up)
            logger.warning("Vector search not yet implemented")
            return []

        except Exception as e:
            logger.error(f"Failed to search documents in Supabase: {e}")
            return []

    async def get_sync_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get sync performance metrics"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            result = self.client.table(self.tables['sync_logs']) \
                .select('*') \
                .gte('timestamp', since.isoformat()) \
                .execute()

            if not result.data:
                return {
                    'total_syncs': 0,
                    'success_rate': 0.0,
                    'avg_duration': 0.0,
                    'total_records': 0,
                    'total_errors': 0
                }

            total_syncs = len(result.data)
            successful_syncs = sum(1 for row in result.data if row['status'] == 'success')
            success_rate = successful_syncs / total_syncs if total_syncs > 0 else 0.0
            avg_duration = sum(row['duration'] for row in result.data) / total_syncs
            total_records = sum(row['records_synced'] for row in result.data)
            total_errors = sum(row['errors_count'] for row in result.data)

            return {
                'total_syncs': total_syncs,
                'success_rate': success_rate,
                'avg_duration': avg_duration,
                'total_records': total_records,
                'total_errors': total_errors
            }

        except Exception as e:
            logger.error(f"Failed to get sync metrics from Supabase: {e}")
            return {}

    async def close(self):
        """Close connections"""
        logger.info("SupabaseBridge connections closed")


# Example usage
async def main():
    """Example usage"""
    import yaml

    # Load config
    with open('antigravity-config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create bridge
    bridge = SupabaseBridge(config)

    try:
        # Log a sync operation
        await bridge.log_sync({
            'direction': 'crew_to_antigrav',
            'records_synced': 10,
            'errors': [],
            'cost': 0.05,
            'duration': 2.5
        })

        # Get daily cost
        daily_cost = await bridge.get_daily_cost()
        print(f"Daily cost: ${daily_cost:.2f}")

        # Get sync metrics
        metrics = await bridge.get_sync_metrics(hours=24)
        print(f"Sync metrics: {json.dumps(metrics, indent=2)}")

    finally:
        await bridge.close()


if __name__ == "__main__":
    asyncio.run(main())
