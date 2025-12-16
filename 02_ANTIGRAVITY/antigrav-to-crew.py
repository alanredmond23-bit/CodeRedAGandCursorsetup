#!/usr/bin/env python3
"""
Antigravity → CrewAI Sync Module

Syncs agent outputs from Antigravity to CrewAI task inputs in Claude Code Terminal.
This flows results and status updates from Antigravity agents back to the orchestrating
CrewAI system.

Flow:
1. Query Antigravity agent states
2. Extract outputs and status
3. Map to CrewAI task format
4. Push updates to Claude Code Terminal
5. Track costs and metrics

Author: Antigravity Orchestration Team
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import yaml
import httpx
from google.cloud import aiplatform
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class AntigravityToCrewSync:
    """
    Handles synchronization from Antigravity agents to CrewAI tasks

    Responsibilities:
    - Poll Antigravity agent states
    - Extract outputs and status updates
    - Map to CrewAI task format using agent-mapping.yaml
    - Push updates to Claude Code Terminal API
    - Track costs per agent
    - Handle errors and retries
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Antigravity → CrewAI sync"""
        self.config = config
        self.mapping = self._load_mapping()
        self.client = None
        self.cost_tracker = {}
        self._init_clients()

        logger.info("AntigravityToCrewSync initialized")

    def _load_mapping(self) -> Dict[str, Any]:
        """Load agent mapping configuration"""
        try:
            with open('agent-mapping.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load agent mapping: {e}")
            raise

    def _init_clients(self):
        """Initialize API clients"""
        try:
            # Google Cloud / Vertex AI client
            credentials_path = self.config['gcp']['credentials_path']
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )

            aiplatform.init(
                project=self.config['gcp']['project_id'],
                location=self.config['gcp']['region'],
                credentials=credentials
            )

            # HTTP client for Claude API
            self.claude_client = httpx.AsyncClient(
                base_url=self.config['crew_bridge']['claude']['api_base_url'],
                headers={
                    'Authorization': f"Bearer {self.config['crew_bridge']['claude']['api_key']}",
                    'Content-Type': 'application/json'
                },
                timeout=self.config['crew_bridge']['claude']['timeout']
            )

            logger.info("API clients initialized")

        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise

    async def sync(self) -> Dict[str, Any]:
        """
        Main sync method - pull from Antigravity and push to CrewAI

        Returns:
            Dict with sync results including records synced, errors, and costs
        """
        sync_start = datetime.utcnow()
        results = {
            'timestamp': sync_start.isoformat(),
            'records_synced': 0,
            'errors': [],
            'cost': 0.0,
            'agents': {}
        }

        try:
            # Get list of active agents
            agents = self.config['agents'].keys()

            # Sync each agent
            for agent_id in agents:
                try:
                    agent_result = await self._sync_agent(agent_id)
                    results['agents'][agent_id] = agent_result
                    results['records_synced'] += agent_result['records_synced']
                    results['cost'] += agent_result['cost']

                except Exception as e:
                    error_msg = f"Failed to sync agent {agent_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append({
                        'agent_id': agent_id,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })

            # Calculate sync duration
            results['duration'] = (datetime.utcnow() - sync_start).total_seconds()

            logger.info(
                f"Antigrav→Crew sync completed: {results['records_synced']} records, "
                f"${results['cost']:.4f} cost"
            )

            return results

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            results['errors'].append({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return results

    async def _sync_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Sync a single agent's outputs to CrewAI

        Args:
            agent_id: Agent identifier (orchestrator, researcher, executor)

        Returns:
            Dict with agent sync results
        """
        logger.info(f"Syncing agent: {agent_id}")

        result = {
            'agent_id': agent_id,
            'records_synced': 0,
            'cost': 0.0,
            'outputs': []
        }

        try:
            # Step 1: Get agent state from Antigravity
            agent_state = await self._get_agent_state(agent_id)

            if not agent_state:
                logger.debug(f"No state found for agent {agent_id}")
                return result

            # Step 2: Extract outputs
            outputs = self._extract_outputs(agent_id, agent_state)

            if not outputs:
                logger.debug(f"No outputs to sync for agent {agent_id}")
                return result

            # Step 3: Map to CrewAI format
            crew_updates = self._map_to_crew_format(agent_id, outputs)

            # Step 4: Push to Claude Code Terminal
            for update in crew_updates:
                try:
                    response = await self._push_to_crew(agent_id, update)
                    result['outputs'].append(response)
                    result['records_synced'] += 1

                except Exception as e:
                    logger.error(f"Failed to push update for {agent_id}: {e}")

            # Step 5: Track costs
            result['cost'] = self._calculate_cost(agent_id, agent_state)
            self.cost_tracker[agent_id] = result['cost']

            logger.info(
                f"Agent {agent_id} synced: {result['records_synced']} records, "
                f"${result['cost']:.4f} cost"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to sync agent {agent_id}: {e}")
            raise

    async def _get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current state of Antigravity agent

        This would query Vertex AI or your agent state store
        """
        try:
            # In production, this would query your actual agent state
            # For now, we'll simulate with a state store query

            # Example: Query from state persistence
            state_key = f"antigrav_agent_{agent_id}"

            # This is a placeholder - implement actual state retrieval
            # Could be from Firestore, Cloud Storage, or agent runtime API
            agent_state = {
                'agent_id': agent_id,
                'status': 'active',
                'last_output_time': datetime.utcnow().isoformat(),
                'output': {},
                'metrics': {
                    'tokens_used': 0,
                    'cost': 0.0,
                    'execution_time': 0.0
                }
            }

            return agent_state

        except Exception as e:
            logger.error(f"Failed to get state for agent {agent_id}: {e}")
            return None

    def _extract_outputs(self, agent_id: str, agent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract outputs from agent state"""
        try:
            outputs = []

            # Get output mapping for this agent
            mapping = self.mapping['mappings'][agent_id]
            output_mapping = mapping.get('output_mapping', {})

            # Extract each mapped output field
            for field_name, field_config in output_mapping.items():
                source_path = field_config['source']
                value = self._get_nested_value(agent_state, source_path)

                if value is not None:
                    outputs.append({
                        'field': field_name,
                        'value': value,
                        'target': field_config['target'],
                        'type': field_config['type'],
                        'required': field_config.get('required', False)
                    })

            return outputs

        except Exception as e:
            logger.error(f"Failed to extract outputs for {agent_id}: {e}")
            return []

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dict using dot notation path"""
        try:
            keys = path.split('.')
            value = data

            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return None

            return value

        except Exception:
            return None

    def _map_to_crew_format(self, agent_id: str, outputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map Antigravity outputs to CrewAI task format"""
        try:
            mapping = self.mapping['mappings'][agent_id]
            task_id = mapping['crewai']['task_id']

            crew_updates = []

            for output in outputs:
                crew_update = {
                    'task_id': task_id,
                    'agent_id': agent_id,
                    'field': output['field'],
                    'target_path': output['target'],
                    'value': output['value'],
                    'type': output['type'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'antigravity'
                }

                crew_updates.append(crew_update)

            return crew_updates

        except Exception as e:
            logger.error(f"Failed to map outputs to CrewAI format: {e}")
            return []

    async def _push_to_crew(self, agent_id: str, update: Dict[str, Any]) -> Dict[str, Any]:
        """Push update to Claude Code Terminal / CrewAI"""
        try:
            # Call Claude API to update task
            response = await self.claude_client.post(
                '/tasks/update',
                json=update
            )

            response.raise_for_status()

            result = response.json()
            logger.debug(f"Pushed update to CrewAI for {agent_id}: {result}")

            return result

        except Exception as e:
            logger.error(f"Failed to push to CrewAI: {e}")
            raise

    def _calculate_cost(self, agent_id: str, agent_state: Dict[str, Any]) -> float:
        """Calculate cost for agent operations"""
        try:
            metrics = agent_state.get('metrics', {})

            # Get token usage
            tokens_used = metrics.get('tokens_used', 0)

            # Get pricing from config (example rates)
            # Gemini Pro: ~$0.00025 per 1K tokens (input)
            cost_per_1k_tokens = 0.00025

            cost = (tokens_used / 1000) * cost_per_1k_tokens

            return cost

        except Exception as e:
            logger.error(f"Failed to calculate cost: {e}")
            return 0.0

    async def close(self):
        """Close connections"""
        try:
            if self.claude_client:
                await self.claude_client.aclose()
            logger.info("AntigravityToCrewSync connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")


# Example usage
async def main():
    """Example usage"""
    import yaml

    # Load config
    with open('antigravity-config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create sync instance
    sync = AntigravityToCrewSync(config)

    try:
        # Run sync
        results = await sync.sync()
        print(json.dumps(results, indent=2))

    finally:
        await sync.close()


if __name__ == "__main__":
    asyncio.run(main())
