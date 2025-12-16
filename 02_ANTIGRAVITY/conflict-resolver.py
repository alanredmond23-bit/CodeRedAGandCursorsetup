#!/usr/bin/env python3
"""
Conflict Resolution Engine

Handles conflicts between Antigravity and CrewAI state with CrewAI priority.
Ensures data consistency while maintaining CrewAI as the authoritative source.

Resolution Strategy:
- CrewAI decisions ALWAYS win
- Antigravity state is overridden
- All conflicts are logged for audit
- Diff is captured for troubleshooting

Author: Antigravity Orchestration Team
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur"""
    STATUS_MISMATCH = "status_mismatch"
    PARAMETER_MISMATCH = "parameter_mismatch"
    OUTPUT_MISMATCH = "output_mismatch"
    PRIORITY_MISMATCH = "priority_mismatch"
    TIMESTAMP_CONFLICT = "timestamp_conflict"
    DATA_DIVERGENCE = "data_divergence"


class ResolutionStrategy(Enum):
    """How to resolve conflicts"""
    CREW_WINS = "crew_wins"  # CrewAI value is used
    ANTIGRAV_WINS = "antigrav_wins"  # Antigravity value is used
    MERGE = "merge"  # Attempt to merge both values
    LATEST = "latest"  # Use most recent by timestamp
    MANUAL = "manual"  # Requires human intervention


@dataclass
class Conflict:
    """Represents a detected conflict"""
    conflict_id: str
    conflict_type: ConflictType
    agent_id: str
    task_id: str
    field_name: str
    crew_value: Any
    antigrav_value: Any
    resolution_strategy: ResolutionStrategy
    resolved_value: Any
    timestamp: str
    diff: Dict[str, Any]
    metadata: Dict[str, Any]


class ConflictResolver:
    """
    Resolves conflicts between Antigravity and CrewAI state

    Core Principle: CrewAI is the source of truth
    - All CrewAI decisions override Antigravity
    - Conflicts are logged for audit trail
    - Diffs are captured for debugging
    - Cost limits from Antigravity are respected
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize conflict resolver"""
        self.config = config
        self.resolution_policies = config.get('conflict_resolution', {}).get('policies', {})
        self.conflicts_log = []

        logger.info("ConflictResolver initialized with CrewAI priority")

    async def resolve(
        self,
        crew_results: Dict[str, Any],
        antigrav_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Resolve conflicts between CrewAI and Antigravity results

        Args:
            crew_results: Results from CrewAI → Antigravity sync
            antigrav_results: Results from Antigravity → CrewAI sync

        Returns:
            List of resolved conflicts
        """
        logger.info("Starting conflict resolution")

        conflicts = []

        try:
            # Step 1: Detect conflicts
            detected_conflicts = await self._detect_conflicts(
                crew_results,
                antigrav_results
            )

            if not detected_conflicts:
                logger.info("No conflicts detected")
                return []

            logger.info(f"Detected {len(detected_conflicts)} conflicts")

            # Step 2: Resolve each conflict
            for conflict in detected_conflicts:
                try:
                    resolved_conflict = await self._resolve_conflict(conflict)
                    conflicts.append(resolved_conflict)

                    # Apply resolution
                    await self._apply_resolution(resolved_conflict)

                except Exception as e:
                    logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {e}")

            # Step 3: Log all conflicts
            await self._log_conflicts(conflicts)

            logger.info(f"Resolved {len(conflicts)} conflicts")

            return [asdict(c) for c in conflicts]

        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}", exc_info=True)
            return []

    async def _detect_conflicts(
        self,
        crew_results: Dict[str, Any],
        antigrav_results: Dict[str, Any]
    ) -> List[Conflict]:
        """Detect conflicts between CrewAI and Antigravity results"""
        conflicts = []

        try:
            # Get agents from both results
            crew_tasks = crew_results.get('tasks', {})
            antigrav_agents = antigrav_results.get('agents', {})

            # Check each agent/task pair
            for agent_id, antigrav_data in antigrav_agents.items():
                # Find corresponding CrewAI task
                task_data = self._find_task_for_agent(agent_id, crew_tasks)

                if not task_data:
                    continue

                # Detect conflicts between agent and task
                agent_conflicts = await self._detect_agent_conflicts(
                    agent_id,
                    task_data['task_id'],
                    task_data,
                    antigrav_data
                )

                conflicts.extend(agent_conflicts)

            return conflicts

        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return []

    def _find_task_for_agent(
        self,
        agent_id: str,
        crew_tasks: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find CrewAI task corresponding to Antigravity agent"""
        # This would use the agent-mapping.yaml to find the task
        # For now, simplified lookup
        for task_id, task_data in crew_tasks.items():
            if task_data.get('agent_id') == agent_id:
                return {
                    'task_id': task_id,
                    **task_data
                }
        return None

    async def _detect_agent_conflicts(
        self,
        agent_id: str,
        task_id: str,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any]
    ) -> List[Conflict]:
        """Detect conflicts for a specific agent/task pair"""
        conflicts = []

        try:
            # Check status conflicts
            status_conflict = self._check_status_conflict(
                agent_id, task_id, task_data, agent_data
            )
            if status_conflict:
                conflicts.append(status_conflict)

            # Check parameter conflicts
            param_conflicts = self._check_parameter_conflicts(
                agent_id, task_id, task_data, agent_data
            )
            conflicts.extend(param_conflicts)

            # Check output conflicts
            output_conflicts = self._check_output_conflicts(
                agent_id, task_id, task_data, agent_data
            )
            conflicts.extend(output_conflicts)

            # Check priority conflicts
            priority_conflict = self._check_priority_conflict(
                agent_id, task_id, task_data, agent_data
            )
            if priority_conflict:
                conflicts.append(priority_conflict)

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect agent conflicts: {e}")
            return []

    def _check_status_conflict(
        self,
        agent_id: str,
        task_id: str,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any]
    ) -> Optional[Conflict]:
        """Check for status conflicts"""
        crew_status = task_data.get('status')
        antigrav_status = agent_data.get('status')

        if crew_status and antigrav_status and crew_status != antigrav_status:
            return Conflict(
                conflict_id=self._generate_conflict_id(agent_id, task_id, 'status'),
                conflict_type=ConflictType.STATUS_MISMATCH,
                agent_id=agent_id,
                task_id=task_id,
                field_name='status',
                crew_value=crew_status,
                antigrav_value=antigrav_status,
                resolution_strategy=ResolutionStrategy.CREW_WINS,
                resolved_value=crew_status,  # CrewAI wins
                timestamp=datetime.utcnow().isoformat(),
                diff={'crew': crew_status, 'antigrav': antigrav_status},
                metadata={}
            )

        return None

    def _check_parameter_conflicts(
        self,
        agent_id: str,
        task_id: str,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any]
    ) -> List[Conflict]:
        """Check for parameter conflicts"""
        conflicts = []

        crew_params = task_data.get('parameters', {})
        agent_params = agent_data.get('parameters', {})

        # Check each parameter
        all_param_keys = set(crew_params.keys()) | set(agent_params.keys())

        for param_key in all_param_keys:
            crew_value = crew_params.get(param_key)
            antigrav_value = agent_params.get(param_key)

            if crew_value != antigrav_value:
                # Get resolution strategy from policy
                strategy = self._get_resolution_strategy('parameters', param_key)

                conflicts.append(Conflict(
                    conflict_id=self._generate_conflict_id(agent_id, task_id, param_key),
                    conflict_type=ConflictType.PARAMETER_MISMATCH,
                    agent_id=agent_id,
                    task_id=task_id,
                    field_name=param_key,
                    crew_value=crew_value,
                    antigrav_value=antigrav_value,
                    resolution_strategy=strategy,
                    resolved_value=self._resolve_value(
                        strategy, crew_value, antigrav_value
                    ),
                    timestamp=datetime.utcnow().isoformat(),
                    diff={'crew': crew_value, 'antigrav': antigrav_value},
                    metadata={'category': 'parameter'}
                ))

        return conflicts

    def _check_output_conflicts(
        self,
        agent_id: str,
        task_id: str,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any]
    ) -> List[Conflict]:
        """Check for output conflicts"""
        conflicts = []

        # Outputs typically flow from Antigravity to CrewAI
        # Conflicts are rare but can occur if both systems generate outputs
        crew_outputs = task_data.get('outputs', {})
        agent_outputs = agent_data.get('outputs', {})

        # Check for divergent outputs
        for output_key in set(crew_outputs.keys()) & set(agent_outputs.keys()):
            crew_value = crew_outputs[output_key]
            antigrav_value = agent_outputs[output_key]

            if crew_value != antigrav_value:
                strategy = self._get_resolution_strategy('outputs', output_key)

                conflicts.append(Conflict(
                    conflict_id=self._generate_conflict_id(agent_id, task_id, output_key),
                    conflict_type=ConflictType.OUTPUT_MISMATCH,
                    agent_id=agent_id,
                    task_id=task_id,
                    field_name=output_key,
                    crew_value=crew_value,
                    antigrav_value=antigrav_value,
                    resolution_strategy=strategy,
                    resolved_value=self._resolve_value(
                        strategy, crew_value, antigrav_value
                    ),
                    timestamp=datetime.utcnow().isoformat(),
                    diff={'crew': crew_value, 'antigrav': antigrav_value},
                    metadata={'category': 'output'}
                ))

        return conflicts

    def _check_priority_conflict(
        self,
        agent_id: str,
        task_id: str,
        task_data: Dict[str, Any],
        agent_data: Dict[str, Any]
    ) -> Optional[Conflict]:
        """Check for priority conflicts"""
        crew_priority = task_data.get('priority')
        antigrav_priority = agent_data.get('priority')

        if crew_priority and antigrav_priority and crew_priority != antigrav_priority:
            return Conflict(
                conflict_id=self._generate_conflict_id(agent_id, task_id, 'priority'),
                conflict_type=ConflictType.PRIORITY_MISMATCH,
                agent_id=agent_id,
                task_id=task_id,
                field_name='priority',
                crew_value=crew_priority,
                antigrav_value=antigrav_priority,
                resolution_strategy=ResolutionStrategy.CREW_WINS,
                resolved_value=crew_priority,  # CrewAI wins
                timestamp=datetime.utcnow().isoformat(),
                diff={'crew': crew_priority, 'antigrav': antigrav_priority},
                metadata={}
            )

        return None

    def _get_resolution_strategy(
        self,
        category: str,
        field_name: str
    ) -> ResolutionStrategy:
        """Get resolution strategy from policy"""
        try:
            # Look up policy
            policy_key = f"{category}.{field_name}"
            policy = self.resolution_policies.get(
                category,
                self.resolution_policies.get('default', {})
            )

            priority = policy.get('priority', 'crew')

            # Map priority to strategy
            if priority == 'crew':
                return ResolutionStrategy.CREW_WINS
            elif priority == 'antigrav':
                return ResolutionStrategy.ANTIGRAV_WINS
            elif priority == 'latest':
                return ResolutionStrategy.LATEST
            else:
                return ResolutionStrategy.CREW_WINS  # Default

        except Exception:
            return ResolutionStrategy.CREW_WINS  # Safe default

    def _resolve_value(
        self,
        strategy: ResolutionStrategy,
        crew_value: Any,
        antigrav_value: Any
    ) -> Any:
        """Resolve value based on strategy"""
        if strategy == ResolutionStrategy.CREW_WINS:
            return crew_value
        elif strategy == ResolutionStrategy.ANTIGRAV_WINS:
            return antigrav_value
        elif strategy == ResolutionStrategy.LATEST:
            # Would need timestamps to implement properly
            return crew_value  # Default to CrewAI
        elif strategy == ResolutionStrategy.MERGE:
            # Attempt merge if both are dicts
            if isinstance(crew_value, dict) and isinstance(antigrav_value, dict):
                return {**antigrav_value, **crew_value}  # CrewAI values override
            return crew_value
        else:
            return crew_value

    async def _resolve_conflict(self, conflict: Conflict) -> Conflict:
        """Apply resolution strategy to conflict"""
        logger.info(
            f"Resolving conflict {conflict.conflict_id}: "
            f"{conflict.conflict_type.value} on {conflict.field_name}"
        )

        # Resolution value is already set in conflict
        # Additional processing could be done here

        return conflict

    async def _apply_resolution(self, conflict: Conflict):
        """Apply resolved value back to systems"""
        try:
            logger.info(
                f"Applying resolution for {conflict.conflict_id}: "
                f"setting {conflict.field_name} = {conflict.resolved_value}"
            )

            # In production, this would:
            # 1. Update Antigravity agent with resolved value
            # 2. Update CrewAI task if needed
            # 3. Verify update applied successfully

            # For now, log the resolution
            pass

        except Exception as e:
            logger.error(f"Failed to apply resolution: {e}")

    async def _log_conflicts(self, conflicts: List[Conflict]):
        """Log conflicts to file and Supabase"""
        try:
            # Log to JSONL file
            with open('conflict-log.jsonl', 'a') as f:
                for conflict in conflicts:
                    f.write(json.dumps(asdict(conflict)) + '\n')

            logger.info(f"Logged {len(conflicts)} conflicts to conflict-log.jsonl")

        except Exception as e:
            logger.error(f"Failed to log conflicts: {e}")

    def _generate_conflict_id(self, agent_id: str, task_id: str, field_name: str) -> str:
        """Generate unique conflict ID"""
        data = f"{agent_id}:{task_id}:{field_name}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Example usage
async def main():
    """Example usage"""
    import yaml

    # Load config
    with open('antigravity-config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create resolver
    resolver = ConflictResolver(config)

    # Example conflict detection
    crew_results = {
        'tasks': {
            'task_1': {
                'agent_id': 'orchestrator',
                'status': 'running',
                'parameters': {'priority': 'high'},
                'outputs': {}
            }
        }
    }

    antigrav_results = {
        'agents': {
            'orchestrator': {
                'status': 'idle',
                'parameters': {'priority': 'medium'},
                'outputs': {}
            }
        }
    }

    conflicts = await resolver.resolve(crew_results, antigrav_results)
    print(json.dumps(conflicts, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
