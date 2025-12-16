#!/usr/bin/env python3
"""
CodeRed Database Connector

Bridges Antigravity orchestration system with CodeRed legal database.
Handles bidirectional sync, logging, and case data management.

Features:
- Case data synchronization
- Document management
- Agent activity logging
- Task tracking
- Performance metrics
- Batch operations for efficiency

Author: Antigravity Orchestration Team
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import asyncpg
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CodeRedConnector:
    """
    Connector for CodeRed legal case database

    Responsibilities:
    - Sync case data between Antigravity and CodeRed
    - Log agent activities
    - Track task execution
    - Store sync history
    - Query case documents
    - Maintain data consistency
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize CodeRed connector"""
        self.config = config
        self.codered_config = config.get('codered', {})
        self.connection_string = self.codered_config.get('connection_string')
        self.pool: Optional[asyncpg.Pool] = None
        self.tables = self.codered_config.get('tables', {})

        logger.info("CodeRedConnector initialized")

    async def connect(self):
        """Establish connection pool to CodeRed database"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60
            )

            logger.info("Connected to CodeRed database")

            # Verify tables exist
            await self._verify_tables()

        except Exception as e:
            logger.error(f"Failed to connect to CodeRed: {e}")
            raise

    async def _verify_tables(self):
        """Verify required tables exist"""
        try:
            async with self.pool.acquire() as conn:
                # Check if tables exist
                for table_name in self.tables.values():
                    result = await conn.fetchval(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = $1
                        )
                        """,
                        table_name
                    )

                    if not result:
                        logger.warning(f"Table {table_name} does not exist in CodeRed")

            logger.info("CodeRed table verification complete")

        except Exception as e:
            logger.error(f"Table verification failed: {e}")

    async def log_sync(self, direction: str, results: Dict[str, Any]):
        """
        Log sync operation to CodeRed

        Args:
            direction: 'crew_to_antigrav' or 'antigrav_to_crew'
            results: Sync results dictionary
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.tables['sync_log']}
                    (sync_id, direction, timestamp, records_synced, errors_count,
                     cost, duration, status, details)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    self._generate_sync_id(),
                    direction,
                    datetime.utcnow(),
                    results.get('records_synced', 0),
                    len(results.get('errors', [])),
                    results.get('cost', 0.0),
                    results.get('duration', 0.0),
                    'success' if not results.get('errors') else 'partial',
                    json.dumps(results)
                )

            logger.debug(f"Logged sync operation: {direction}")

        except Exception as e:
            logger.error(f"Failed to log sync: {e}")

    async def log_agent_activity(
        self,
        agent_id: str,
        activity_type: str,
        details: Dict[str, Any]
    ):
        """Log agent activity to CodeRed"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.tables['agents']}
                    (agent_id, activity_type, timestamp, details, cost)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    agent_id,
                    activity_type,
                    datetime.utcnow(),
                    json.dumps(details),
                    details.get('cost', 0.0)
                )

            logger.debug(f"Logged activity for agent {agent_id}: {activity_type}")

        except Exception as e:
            logger.error(f"Failed to log agent activity: {e}")

    async def log_task(
        self,
        task_id: str,
        agent_id: str,
        status: str,
        details: Dict[str, Any]
    ):
        """Log task execution to CodeRed"""
        try:
            async with self.pool.acquire() as conn:
                # Upsert task record
                await conn.execute(
                    f"""
                    INSERT INTO {self.tables['tasks']}
                    (task_id, agent_id, status, started_at, updated_at, details)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (task_id) DO UPDATE SET
                        status = $3,
                        updated_at = $5,
                        details = $6
                    """,
                    task_id,
                    agent_id,
                    status,
                    details.get('started_at', datetime.utcnow()),
                    datetime.utcnow(),
                    json.dumps(details)
                )

            logger.debug(f"Logged task {task_id} status: {status}")

        except Exception as e:
            logger.error(f"Failed to log task: {e}")

    async def log_cost(
        self,
        agent_id: str,
        task_id: Optional[str],
        cost: float,
        tokens_used: int,
        details: Dict[str, Any]
    ):
        """Log cost tracking to CodeRed"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.tables['cost_tracking']}
                    (agent_id, task_id, timestamp, cost_usd, tokens_used, details)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    agent_id,
                    task_id,
                    datetime.utcnow(),
                    cost,
                    tokens_used,
                    json.dumps(details)
                )

            logger.debug(f"Logged cost for agent {agent_id}: ${cost:.4f}")

        except Exception as e:
            logger.error(f"Failed to log cost: {e}")

    async def get_case_data(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve case data from CodeRed"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    SELECT * FROM {self.tables['cases']}
                    WHERE case_id = $1
                    """,
                    case_id
                )

                if row:
                    return dict(row)

                return None

        except Exception as e:
            logger.error(f"Failed to get case data: {e}")
            return None

    async def get_case_documents(
        self,
        case_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve documents for a case"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT * FROM {self.tables['documents']}
                    WHERE case_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    case_id,
                    limit
                )

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get case documents: {e}")
            return []

    async def update_case_status(
        self,
        case_id: str,
        status: str,
        updated_by: str
    ):
        """Update case status in CodeRed"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    UPDATE {self.tables['cases']}
                    SET status = $2, updated_at = $3, updated_by = $4
                    WHERE case_id = $1
                    """,
                    case_id,
                    status,
                    datetime.utcnow(),
                    updated_by
                )

            logger.info(f"Updated case {case_id} status to {status}")

        except Exception as e:
            logger.error(f"Failed to update case status: {e}")

    async def store_agent_output(
        self,
        agent_id: str,
        task_id: str,
        output_type: str,
        output_data: Dict[str, Any]
    ):
        """Store agent output in CodeRed"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO agent_outputs
                    (agent_id, task_id, output_type, timestamp, data)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    agent_id,
                    task_id,
                    output_type,
                    datetime.utcnow(),
                    json.dumps(output_data)
                )

            logger.debug(f"Stored output for agent {agent_id}, task {task_id}")

        except Exception as e:
            logger.error(f"Failed to store agent output: {e}")

    async def get_daily_costs(self, date: Optional[datetime] = None) -> float:
        """Get total costs for a specific date"""
        if date is None:
            date = datetime.utcnow()

        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    f"""
                    SELECT COALESCE(SUM(cost_usd), 0.0)
                    FROM {self.tables['cost_tracking']}
                    WHERE DATE(timestamp) = DATE($1)
                    """,
                    date
                )

                return float(result)

        except Exception as e:
            logger.error(f"Failed to get daily costs: {e}")
            return 0.0

    async def get_agent_costs(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """Get costs for a specific agent"""
        try:
            async with self.pool.acquire() as conn:
                if start_date and end_date:
                    result = await conn.fetchval(
                        f"""
                        SELECT COALESCE(SUM(cost_usd), 0.0)
                        FROM {self.tables['cost_tracking']}
                        WHERE agent_id = $1
                        AND timestamp BETWEEN $2 AND $3
                        """,
                        agent_id,
                        start_date,
                        end_date
                    )
                else:
                    result = await conn.fetchval(
                        f"""
                        SELECT COALESCE(SUM(cost_usd), 0.0)
                        FROM {self.tables['cost_tracking']}
                        WHERE agent_id = $1
                        """,
                        agent_id
                    )

                return float(result)

        except Exception as e:
            logger.error(f"Failed to get agent costs: {e}")
            return 0.0

    async def batch_log_activities(self, activities: List[Dict[str, Any]]):
        """Batch log multiple activities"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for activity in activities:
                        await conn.execute(
                            f"""
                            INSERT INTO {self.tables['agents']}
                            (agent_id, activity_type, timestamp, details, cost)
                            VALUES ($1, $2, $3, $4, $5)
                            """,
                            activity['agent_id'],
                            activity['activity_type'],
                            activity.get('timestamp', datetime.utcnow()),
                            json.dumps(activity.get('details', {})),
                            activity.get('cost', 0.0)
                        )

            logger.info(f"Batch logged {len(activities)} activities")

        except Exception as e:
            logger.error(f"Failed to batch log activities: {e}")

    def _generate_sync_id(self) -> str:
        """Generate unique sync ID"""
        import uuid
        return str(uuid.uuid4())

    async def close(self):
        """Close database connection pool"""
        try:
            if self.pool:
                await self.pool.close()
            logger.info("CodeRed connection closed")
        except Exception as e:
            logger.error(f"Error closing CodeRed connection: {e}")


# Example usage
async def main():
    """Example usage"""
    import yaml

    # Load config
    with open('antigravity-config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create connector
    connector = CodeRedConnector(config)

    try:
        # Connect
        await connector.connect()

        # Log a sync operation
        await connector.log_sync(
            direction='crew_to_antigrav',
            results={
                'records_synced': 10,
                'errors': [],
                'cost': 0.05,
                'duration': 2.5
            }
        )

        # Get daily costs
        daily_cost = await connector.get_daily_costs()
        print(f"Daily cost: ${daily_cost:.2f}")

    finally:
        await connector.close()


if __name__ == "__main__":
    asyncio.run(main())
