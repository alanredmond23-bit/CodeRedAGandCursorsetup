#!/usr/bin/env python3
"""
CrewAI → Antigravity Sync Module

Syncs task assignments and decisions from CrewAI/Claude Code Terminal to Antigravity agents.
This is the authoritative flow - CrewAI decisions override Antigravity state.

Flow:
1. Poll Claude Code Terminal for task updates
2. Extract task assignments and parameters
3. Map to Antigravity agent format
4. Push updates to Antigravity agents
5. Verify updates applied

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


class CrewToAntigravitySync:
    """
    Handles synchronization from CrewAI tasks to Antigravity agents

    Responsibilities:
    - Poll Claude Code Terminal for task updates
    - Extract task assignments and parameters
    - Map to Antigravity agent format using agent-mapping.yaml
    - Push updates to Antigravity agents
    - Verify updates applied
    - Handle priority overrides (CrewAI wins)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the CrewAI → Antigravity sync"""
        self.config = config
        self.mapping = self._load_mapping()
        self.last_sync_timestamp = datetime.utcnow()
        self._init_clients()

        logger.info("CrewToAntigravitySync initialized")

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
        Main sync method - pull from CrewAI and push to Antigravity

        Returns:
            Dict with sync results including records synced, errors, and costs
        """
        sync_start = datetime.utcnow()
        results = {
            'timestamp': sync_start.isoformat(),
            'records_synced': 0,
            'errors': [],
            'cost': 0.0,
            'tasks': {}
        }

        try:
            # Step 1: Get updates from Claude Code Terminal since last sync
            task_updates = await self._get_crew_updates()

            if not task_updates:
                logger.debug("No CrewAI updates to sync")
                return results

            logger.info(f"Retrieved {len(task_updates)} task updates from CrewAI")

            # Step 2: Process each task update
            for task_update in task_updates:
                task_id = task_update.get('task_id')

                try:
                    # Map task to agent
                    agent_id = self._map_task_to_agent(task_update)

                    if not agent_id:
                        logger.warning(f"No agent mapping found for task {task_id}")
                        continue

                    # Sync task to agent
                    task_result = await self._sync_task_to_agent(agent_id, task_update)

                    results['tasks'][task_id] = task_result
                    results['records_synced'] += task_result.get('records_synced', 0)

                except Exception as e:
                    error_msg = f"Failed to sync task {task_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append({
                        'task_id': task_id,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })

            # Update last sync timestamp
            self.last_sync_timestamp = sync_start

            # Calculate sync duration
            results['duration'] = (datetime.utcnow() - sync_start).total_seconds()

            logger.info(
                f"Crew→Antigrav sync completed: {results['records_synced']} records"
            )

            return results

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            results['errors'].append({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return results

    async def _get_crew_updates(self) -> List[Dict[str, Any]]:
        """
        Get task updates from Claude Code Terminal since last sync

        Returns:
            List of task updates
        """
        try:
            # Query Claude API for task updates
            response = await self.claude_client.get(
                '/tasks/updates',
                params={
                    'since': self.last_sync_timestamp.isoformat(),
                    'limit': self.config['crew_bridge']['sync']['batch_size']
                }
            )

            response.raise_for_status()

            updates = response.json()
            logger.debug(f"Retrieved {len(updates)} task updates from CrewAI")

            return updates

        except Exception as e:
            logger.error(f"Failed to get CrewAI updates: {e}")
            return []

    def _map_task_to_agent(self, task_update: Dict[str, Any]) -> Optional[str]:
        """
        Map CrewAI task to Antigravity agent

        Args:
            task_update: Task update from CrewAI

        Returns:
            Agent ID or None if no mapping found
        """
        try:
            task_id = task_update.get('task_id')

            # Look up mapping
            for agent_id, mapping in self.mapping['mappings'].items():
                if mapping['crewai']['task_id'] == task_id:
                    return agent_id

            logger.warning(f"No agent mapping found for task {task_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to map task to agent: {e}")
            return None

    async def _sync_task_to_agent(
        self,
        agent_id: str,
        task_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync a single task update to Antigravity agent

        Args:
            agent_id: Target agent ID
            task_update: Task update from CrewAI

        Returns:
            Dict with sync results
        """
        logger.info(f"Syncing task to agent {agent_id}")

        result = {
            'agent_id': agent_id,
            'task_id': task_update.get('task_id'),
            'records_synced': 0,
            'updates_applied': []
        }

        try:
            # Step 1: Map task inputs to agent parameters
            agent_params = self._map_task_to_agent_params(agent_id, task_update)

            if not agent_params:
                logger.debug(f"No parameters to update for agent {agent_id}")
                return result

            # Step 2: Apply updates to agent
            for param in agent_params:
                try:
                    update_result = await self._update_agent_param(
                        agent_id,
                        param['param_name'],
                        param['value']
                    )

                    result['updates_applied'].append(update_result)
                    result['records_synced'] += 1

                except Exception as e:
                    logger.error(
                        f"Failed to update param {param['param_name']} "
                        f"for agent {agent_id}: {e}"
                    )

            # Step 3: Handle special cases (stop, priority, etc.)
            await self._handle_special_updates(agent_id, task_update)

            logger.info(
                f"Agent {agent_id} updated: {result['records_synced']} parameters"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to sync task to agent {agent_id}: {e}")
            raise

    def _map_task_to_agent_params(
        self,
        agent_id: str,
        task_update: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Map task inputs to agent parameters"""
        try:
            agent_params = []

            # Get input mapping for this agent
            mapping = self.mapping['mappings'][agent_id]
            input_mapping = mapping.get('input_mapping', {})

            # Extract each mapped input field
            for param_name, param_config in input_mapping.items():
                source_path = param_config['source']
                value = self._get_nested_value(task_update, source_path)

                # Apply default if value is None and default exists
                if value is None and 'default' in param_config:
                    value = param_config['default']

                # Skip if required and no value
                if param_config.get('required', False) and value is None:
                    logger.warning(
                        f"Required parameter {param_name} missing for agent {agent_id}"
                    )
                    continue

                # Apply transform if specified
                if 'transform' in param_config and value is not None:
                    value = self._apply_transform(
                        param_config['transform'],
                        value
                    )

                if value is not None:
                    agent_params.append({
                        'param_name': param_name,
                        'value': value,
                        'target': param_config['target'],
                        'type': param_config['type']
                    })

            return agent_params

        except Exception as e:
            logger.error(f"Failed to map task to agent params: {e}")
            return []

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dict using dot notation path"""
        try:
            # Remove 'crew.task.' prefix if present
            path = path.replace('crew.task.', '')

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

    def _apply_transform(self, transform_name: str, value: Any) -> Any:
        """Apply transform function to value"""
        try:
            # Get transform from mapping config
            transforms = self.mapping.get('transforms', {})
            transform_config = transforms.get(transform_name, {})

            if 'mapping' in transform_config:
                # Simple mapping transform
                return transform_config['mapping'].get(value, value)

            elif 'function' in transform_config:
                # Lambda function transform
                func = eval(transform_config['function'])
                return func(value)

            return value

        except Exception as e:
            logger.error(f"Failed to apply transform {transform_name}: {e}")
            return value

    async def _update_agent_param(
        self,
        agent_id: str,
        param_name: str,
        value: Any
    ) -> Dict[str, Any]:
        """
        Update a single agent parameter

        This would call Vertex AI or your agent control API
        """
        try:
            # In production, this would update the actual agent runtime
            # For now, we'll simulate with a state store update

            logger.debug(
                f"Updating agent {agent_id} parameter {param_name} = {value}"
            )

            # Example: Update agent state
            # This would be actual Vertex AI API call or agent runtime update
            update_result = {
                'agent_id': agent_id,
                'param_name': param_name,
                'value': value,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True
            }

            return update_result

        except Exception as e:
            logger.error(f"Failed to update agent parameter: {e}")
            raise

    async def _handle_special_updates(
        self,
        agent_id: str,
        task_update: Dict[str, Any]
    ):
        """Handle special update types (stop, priority, etc.)"""
        try:
            # Check for stop signal
            if task_update.get('action') == 'stop':
                logger.warning(f"Stop signal received for agent {agent_id}")
                await self._stop_agent(agent_id)

            # Check for priority update
            if 'priority' in task_update.get('context', {}):
                priority = task_update['context']['priority']
                await self._update_agent_priority(agent_id, priority)

            # Check for parameter changes
            if task_update.get('action') == 'update_config':
                config_updates = task_update.get('config', {})
                await self._update_agent_config(agent_id, config_updates)

        except Exception as e:
            logger.error(f"Failed to handle special updates: {e}")

    async def _stop_agent(self, agent_id: str):
        """Stop an Antigravity agent"""
        logger.warning(f"Stopping agent {agent_id}")
        # Implement agent stop logic
        pass

    async def _update_agent_priority(self, agent_id: str, priority: str):
        """Update agent priority"""
        logger.info(f"Updating agent {agent_id} priority to {priority}")
        # Implement priority update logic
        pass

    async def _update_agent_config(self, agent_id: str, config: Dict[str, Any]):
        """Update agent configuration"""
        logger.info(f"Updating agent {agent_id} configuration")
        # Implement config update logic
        pass

    async def close(self):
        """Close connections"""
        try:
            if self.claude_client:
                await self.claude_client.aclose()
            logger.info("CrewToAntigravitySync connections closed")
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
    sync = CrewToAntigravitySync(config)

    try:
        # Run sync
        results = await sync.sync()
        print(json.dumps(results, indent=2))

    finally:
        await sync.close()


if __name__ == "__main__":
    asyncio.run(main())
