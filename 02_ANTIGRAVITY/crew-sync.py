#!/usr/bin/env python3
"""
Bidirectional Sync Engine for Antigravity ↔ Claude Code Terminal

This is the main synchronization orchestrator that coordinates bidirectional
data flow between Antigravity agents and CrewAI tasks running in Claude Code Terminal.

Features:
- 30-second sync cycles (configurable)
- Conflict resolution with CrewAI priority
- Automatic retry and recovery
- Cost tracking and budget enforcement
- Health monitoring integration
- Audit trail logging

Author: Antigravity Orchestration Team
License: Proprietary
"""

import os
import sys
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import yaml
from pathlib import Path

# Import sync modules
from antigrav_to_crew import AntigravityToCrewSync
from crew_to_antigrav import CrewToAntigravitySync
from conflict_resolver import ConflictResolver
from codered_connector import CodeRedConnector
from supabase_bridge import SupabaseBridge
from health_check import HealthCheck
from sync_metrics import SyncMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/crew-sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """Represents the current state of synchronization"""
    last_sync_time: datetime
    sync_count: int
    conflicts_resolved: int
    errors_count: int
    cost_accumulated: float
    status: str  # running, paused, stopped, error
    health_status: str  # healthy, degraded, critical


class CrewSyncOrchestrator:
    """
    Main orchestrator for bidirectional sync between Antigravity and CrewAI

    Coordinates:
    - Antigravity → CrewAI sync (agent outputs to task inputs)
    - CrewAI → Antigravity sync (task results to agent inputs)
    - Conflict resolution (CrewAI priority)
    - Cost tracking and budget enforcement
    - Health monitoring
    - Recovery and resilience
    """

    def __init__(self, config_path: str = "antigravity-config.yaml"):
        """Initialize the sync orchestrator"""
        self.config = self._load_config(config_path)
        self.state = SyncState(
            last_sync_time=datetime.utcnow(),
            sync_count=0,
            conflicts_resolved=0,
            errors_count=0,
            cost_accumulated=0.0,
            status="initializing",
            health_status="unknown"
        )

        # Initialize components
        self._init_components()

        logger.info("CrewSync Orchestrator initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def _init_components(self):
        """Initialize all sync components"""
        try:
            # Sync engines
            self.antigrav_to_crew = AntigravityToCrewSync(self.config)
            self.crew_to_antigrav = CrewToAntigravitySync(self.config)

            # Support systems
            self.conflict_resolver = ConflictResolver(self.config)
            self.codered = CodeRedConnector(self.config)
            self.supabase = SupabaseBridge(self.config)
            self.health_check = HealthCheck(self.config)
            self.metrics = SyncMetrics(self.config)

            # Sync configuration
            self.sync_interval = self.config['system']['sync_interval']
            self.max_retries = self.config['system']['max_retries']
            self.daily_budget = self.config['system']['budget']['daily_limit_usd']

            logger.info("All components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    async def run(self):
        """
        Main sync loop - runs continuously until stopped

        Flow:
        1. Health check
        2. Budget check
        3. CrewAI → Antigravity sync (decisions flow down)
        4. Antigravity → CrewAI sync (results flow up)
        5. Conflict resolution
        6. Metrics collection
        7. State persistence
        8. Wait for next interval
        """
        logger.info("Starting CrewSync orchestrator")
        self.state.status = "running"

        try:
            while self.state.status == "running":
                cycle_start = time.time()

                try:
                    # Step 1: Health check
                    health_status = await self._perform_health_check()

                    if health_status == "critical":
                        logger.error("Critical health check failure - pausing sync")
                        self.state.status = "paused"
                        await self._send_alert("Critical health check failure")
                        await asyncio.sleep(60)
                        continue

                    # Step 2: Budget check
                    if not await self._check_budget():
                        logger.warning("Daily budget exceeded - pausing sync")
                        self.state.status = "paused"
                        await self._send_alert("Daily budget exceeded")
                        await asyncio.sleep(300)
                        continue

                    # Step 3: CrewAI → Antigravity sync (FIRST - CrewAI decisions are authoritative)
                    logger.info("Starting CrewAI → Antigravity sync")
                    crew_to_antigrav_results = await self._sync_crew_to_antigrav()

                    # Step 4: Antigravity → CrewAI sync (results flow back up)
                    logger.info("Starting Antigravity → CrewAI sync")
                    antigrav_to_crew_results = await self._sync_antigrav_to_crew()

                    # Step 5: Resolve conflicts (CrewAI priority)
                    conflicts = await self._resolve_conflicts(
                        crew_to_antigrav_results,
                        antigrav_to_crew_results
                    )

                    # Step 6: Update cost tracking
                    await self._update_costs(
                        crew_to_antigrav_results,
                        antigrav_to_crew_results
                    )

                    # Step 7: Log metrics
                    await self._log_metrics(cycle_start, conflicts)

                    # Step 8: Persist state
                    await self._persist_state()

                    # Update sync state
                    self.state.last_sync_time = datetime.utcnow()
                    self.state.sync_count += 1
                    self.state.conflicts_resolved += len(conflicts)

                    logger.info(
                        f"Sync cycle {self.state.sync_count} completed "
                        f"({len(conflicts)} conflicts resolved)"
                    )

                except Exception as e:
                    logger.error(f"Error in sync cycle: {e}", exc_info=True)
                    self.state.errors_count += 1

                    # Retry logic
                    if self.state.errors_count >= self.max_retries:
                        logger.error("Max retries exceeded - pausing sync")
                        self.state.status = "error"
                        await self._send_alert("Max sync errors exceeded")
                        break

                # Wait for next sync interval
                cycle_duration = time.time() - cycle_start
                wait_time = max(0, self.sync_interval - cycle_duration)

                logger.info(f"Waiting {wait_time:.1f}s until next sync")
                await asyncio.sleep(wait_time)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.state.status = "stopped"

        finally:
            await self._shutdown()

    async def _perform_health_check(self) -> str:
        """Perform health check on all systems"""
        try:
            health_status = await self.health_check.check_all()
            self.state.health_status = health_status['overall']

            # Log to Supabase
            await self.supabase.log_health_check(health_status)

            return health_status['overall']

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "critical"

    async def _check_budget(self) -> bool:
        """Check if we're within daily budget"""
        try:
            today_cost = await self.supabase.get_daily_cost()

            if today_cost >= self.daily_budget:
                logger.warning(f"Daily budget exceeded: ${today_cost:.2f} / ${self.daily_budget:.2f}")
                return False

            budget_remaining = self.daily_budget - today_cost
            budget_percent = (today_cost / self.daily_budget) * 100

            logger.info(f"Budget status: ${today_cost:.2f} / ${self.daily_budget:.2f} ({budget_percent:.1f}%)")

            # Alert if approaching limit
            if budget_percent >= self.config['system']['budget']['alert_threshold_percent']:
                await self._send_alert(
                    f"Approaching daily budget limit: {budget_percent:.1f}%"
                )

            return True

        except Exception as e:
            logger.error(f"Budget check failed: {e}")
            # Fail open - don't block sync on budget check failure
            return True

    async def _sync_crew_to_antigrav(self) -> Dict[str, Any]:
        """Sync from CrewAI to Antigravity (decisions flow down)"""
        try:
            results = await self.crew_to_antigrav.sync()

            # Log sync to CodeRed
            await self.codered.log_sync(
                direction="crew_to_antigrav",
                results=results
            )

            return results

        except Exception as e:
            logger.error(f"CrewAI → Antigravity sync failed: {e}")
            raise

    async def _sync_antigrav_to_crew(self) -> Dict[str, Any]:
        """Sync from Antigravity to CrewAI (results flow up)"""
        try:
            results = await self.antigrav_to_crew.sync()

            # Log sync to CodeRed
            await self.codered.log_sync(
                direction="antigrav_to_crew",
                results=results
            )

            return results

        except Exception as e:
            logger.error(f"Antigravity → CrewAI sync failed: {e}")
            raise

    async def _resolve_conflicts(
        self,
        crew_results: Dict[str, Any],
        antigrav_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts with CrewAI priority"""
        try:
            conflicts = await self.conflict_resolver.resolve(
                crew_results,
                antigrav_results
            )

            # Log conflicts to Supabase
            for conflict in conflicts:
                await self.supabase.log_conflict(conflict)

            return conflicts

        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            return []

    async def _update_costs(
        self,
        crew_results: Dict[str, Any],
        antigrav_results: Dict[str, Any]
    ):
        """Update cost tracking"""
        try:
            # Calculate costs
            crew_cost = crew_results.get('cost', 0.0)
            antigrav_cost = antigrav_results.get('cost', 0.0)
            total_cost = crew_cost + antigrav_cost

            # Update state
            self.state.cost_accumulated += total_cost

            # Log to Supabase
            await self.supabase.log_costs({
                'timestamp': datetime.utcnow().isoformat(),
                'crew_cost': crew_cost,
                'antigrav_cost': antigrav_cost,
                'total_cost': total_cost,
                'cumulative_cost': self.state.cost_accumulated
            })

        except Exception as e:
            logger.error(f"Cost update failed: {e}")

    async def _log_metrics(self, cycle_start: float, conflicts: List[Dict[str, Any]]):
        """Log performance metrics"""
        try:
            cycle_duration = time.time() - cycle_start

            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'cycle_number': self.state.sync_count,
                'cycle_duration': cycle_duration,
                'conflicts_count': len(conflicts),
                'errors_count': self.state.errors_count,
                'cost_accumulated': self.state.cost_accumulated,
                'health_status': self.state.health_status
            }

            await self.metrics.log(metrics)

        except Exception as e:
            logger.error(f"Metrics logging failed: {e}")

    async def _persist_state(self):
        """Persist current state"""
        try:
            state_dict = asdict(self.state)
            await self.supabase.save_state('crew_sync_state', state_dict)

        except Exception as e:
            logger.error(f"State persistence failed: {e}")

    async def _send_alert(self, message: str):
        """Send alert notification"""
        try:
            await self.supabase.send_alert({
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                'severity': 'warning'
            })

        except Exception as e:
            logger.error(f"Alert sending failed: {e}")

    async def _shutdown(self):
        """Clean shutdown"""
        logger.info("Shutting down CrewSync orchestrator")

        try:
            # Persist final state
            await self._persist_state()

            # Close connections
            await self.codered.close()
            await self.supabase.close()

            logger.info("Shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def pause(self):
        """Pause synchronization"""
        logger.info("Pausing synchronization")
        self.state.status = "paused"

    async def resume(self):
        """Resume synchronization"""
        logger.info("Resuming synchronization")
        self.state.status = "running"

    async def stop(self):
        """Stop synchronization"""
        logger.info("Stopping synchronization")
        self.state.status = "stopped"


async def main():
    """Main entry point"""
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Create orchestrator
    orchestrator = CrewSyncOrchestrator()

    try:
        # Run sync loop
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
