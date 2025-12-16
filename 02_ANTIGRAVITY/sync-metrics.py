#!/usr/bin/env python3
"""
Sync Metrics Collection and Analysis

Tracks performance metrics, conflict rates, and system health.
Provides analytics for optimization and troubleshooting.

Metrics Tracked:
- Sync latency and throughput
- Success/failure rates
- Conflict frequency and resolution time
- Agent utilization
- Cost per agent/task
- Error rates and types

Author: Antigravity Orchestration Team
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class SyncMetric:
    """Single sync metric data point"""
    timestamp: str
    metric_type: str
    value: float
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SyncMetrics:
    """
    Collects and analyzes sync performance metrics

    Responsibilities:
    - Collect real-time metrics
    - Calculate aggregates and trends
    - Detect anomalies
    - Generate performance reports
    - Track SLA compliance
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize metrics collection"""
        self.config = config
        self.metrics_config = config.get('monitoring', {}).get('metrics', {})
        self.tracked_metrics = self.metrics_config.get('tracked_metrics', [])
        self.collection_interval = self.metrics_config.get('collection_interval', 30)

        # In-memory storage for recent metrics
        self.metrics_buffer: List[SyncMetric] = []
        self.max_buffer_size = 10000

        # Aggregated stats
        self.stats = defaultdict(list)

        logger.info("SyncMetrics initialized")

    async def log(self, metrics: Dict[str, Any]):
        """
        Log metrics data point

        Args:
            metrics: Dictionary containing metric values
        """
        try:
            timestamp = metrics.get('timestamp', datetime.utcnow().isoformat())

            # Extract and store individual metrics
            for metric_name in self.tracked_metrics:
                if metric_name in metrics:
                    metric = SyncMetric(
                        timestamp=timestamp,
                        metric_type=metric_name,
                        value=float(metrics[metric_name]),
                        agent_id=metrics.get('agent_id'),
                        task_id=metrics.get('task_id'),
                        metadata=metrics.get('metadata')
                    )

                    self.metrics_buffer.append(metric)

                    # Update stats
                    self.stats[metric_name].append(metric.value)

            # Trim buffer if too large
            if len(self.metrics_buffer) > self.max_buffer_size:
                self.metrics_buffer = self.metrics_buffer[-self.max_buffer_size:]

            logger.debug(f"Logged metrics: {len(metrics)} data points")

        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

    async def get_sync_latency(
        self,
        window_minutes: int = 60
    ) -> Dict[str, float]:
        """Get sync latency statistics"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            latencies = [
                m.value for m in self.metrics_buffer
                if m.metric_type == 'sync_latency'
                and datetime.fromisoformat(m.timestamp) >= since
            ]

            if not latencies:
                return {
                    'count': 0,
                    'mean': 0.0,
                    'median': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'p95': 0.0,
                    'p99': 0.0
                }

            return {
                'count': len(latencies),
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'min': min(latencies),
                'max': max(latencies),
                'p95': self._percentile(latencies, 95),
                'p99': self._percentile(latencies, 99)
            }

        except Exception as e:
            logger.error(f"Failed to calculate sync latency: {e}")
            return {}

    async def get_success_rate(
        self,
        window_minutes: int = 60
    ) -> float:
        """Get sync success rate"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            success_metrics = [
                m.value for m in self.metrics_buffer
                if m.metric_type == 'sync_success_rate'
                and datetime.fromisoformat(m.timestamp) >= since
            ]

            if not success_metrics:
                return 1.0

            return statistics.mean(success_metrics)

        except Exception as e:
            logger.error(f"Failed to calculate success rate: {e}")
            return 0.0

    async def get_conflict_rate(
        self,
        window_minutes: int = 60
    ) -> float:
        """Get conflict rate"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            conflict_metrics = [
                m.value for m in self.metrics_buffer
                if m.metric_type == 'conflict_rate'
                and datetime.fromisoformat(m.timestamp) >= since
            ]

            if not conflict_metrics:
                return 0.0

            return statistics.mean(conflict_metrics)

        except Exception as e:
            logger.error(f"Failed to calculate conflict rate: {e}")
            return 0.0

    async def get_agent_utilization(
        self,
        agent_id: Optional[str] = None,
        window_minutes: int = 60
    ) -> Dict[str, float]:
        """Get agent utilization statistics"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            utilization_metrics = [
                m for m in self.metrics_buffer
                if m.metric_type == 'agent_utilization'
                and datetime.fromisoformat(m.timestamp) >= since
                and (agent_id is None or m.agent_id == agent_id)
            ]

            if agent_id:
                # Single agent stats
                values = [m.value for m in utilization_metrics]

                if not values:
                    return {
                        'agent_id': agent_id,
                        'mean': 0.0,
                        'max': 0.0
                    }

                return {
                    'agent_id': agent_id,
                    'mean': statistics.mean(values),
                    'max': max(values)
                }
            else:
                # All agents stats
                by_agent = defaultdict(list)
                for m in utilization_metrics:
                    if m.agent_id:
                        by_agent[m.agent_id].append(m.value)

                return {
                    agent: {
                        'mean': statistics.mean(values),
                        'max': max(values)
                    }
                    for agent, values in by_agent.items()
                    if values
                }

        except Exception as e:
            logger.error(f"Failed to calculate agent utilization: {e}")
            return {}

    async def get_cost_metrics(
        self,
        agent_id: Optional[str] = None,
        window_minutes: int = 60
    ) -> Dict[str, float]:
        """Get cost metrics"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            cost_metrics = [
                m for m in self.metrics_buffer
                if m.metric_type == 'cost_per_agent'
                and datetime.fromisoformat(m.timestamp) >= since
                and (agent_id is None or m.agent_id == agent_id)
            ]

            if agent_id:
                # Single agent costs
                costs = [m.value for m in cost_metrics]

                if not costs:
                    return {
                        'agent_id': agent_id,
                        'total': 0.0,
                        'mean': 0.0
                    }

                return {
                    'agent_id': agent_id,
                    'total': sum(costs),
                    'mean': statistics.mean(costs)
                }
            else:
                # All agents costs
                by_agent = defaultdict(list)
                for m in cost_metrics:
                    if m.agent_id:
                        by_agent[m.agent_id].append(m.value)

                return {
                    agent: {
                        'total': sum(values),
                        'mean': statistics.mean(values)
                    }
                    for agent, values in by_agent.items()
                    if values
                }

        except Exception as e:
            logger.error(f"Failed to calculate cost metrics: {e}")
            return {}

    async def get_error_rate(
        self,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get error rate statistics"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            error_metrics = [
                m for m in self.metrics_buffer
                if m.metric_type == 'error_rate'
                and datetime.fromisoformat(m.timestamp) >= since
            ]

            if not error_metrics:
                return {
                    'rate': 0.0,
                    'count': 0
                }

            rates = [m.value for m in error_metrics]

            return {
                'rate': statistics.mean(rates),
                'count': len(error_metrics),
                'max': max(rates)
            }

        except Exception as e:
            logger.error(f"Failed to calculate error rate: {e}")
            return {}

    async def get_throughput(
        self,
        window_minutes: int = 60
    ) -> Dict[str, float]:
        """Get throughput statistics"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            throughput_metrics = [
                m.value for m in self.metrics_buffer
                if m.metric_type == 'throughput'
                and datetime.fromisoformat(m.timestamp) >= since
            ]

            if not throughput_metrics:
                return {
                    'mean': 0.0,
                    'max': 0.0
                }

            return {
                'mean': statistics.mean(throughput_metrics),
                'max': max(throughput_metrics),
                'min': min(throughput_metrics)
            }

        except Exception as e:
            logger.error(f"Failed to calculate throughput: {e}")
            return {}

    async def generate_report(
        self,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'window_minutes': window_minutes,
                'sync_latency': await self.get_sync_latency(window_minutes),
                'success_rate': await self.get_success_rate(window_minutes),
                'conflict_rate': await self.get_conflict_rate(window_minutes),
                'agent_utilization': await self.get_agent_utilization(window_minutes=window_minutes),
                'cost_metrics': await self.get_cost_metrics(window_minutes=window_minutes),
                'error_rate': await self.get_error_rate(window_minutes),
                'throughput': await self.get_throughput(window_minutes)
            }

            logger.info("Generated metrics report")

            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {}

    async def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics"""
        anomalies = []

        try:
            # Check for high latency
            latency_stats = await self.get_sync_latency(window_minutes=10)
            if latency_stats.get('p95', 0) > 10.0:  # More than 10 seconds
                anomalies.append({
                    'type': 'high_latency',
                    'severity': 'warning',
                    'message': f"High sync latency detected: {latency_stats['p95']:.2f}s",
                    'value': latency_stats['p95']
                })

            # Check for low success rate
            success_rate = await self.get_success_rate(window_minutes=10)
            if success_rate < 0.95:  # Less than 95%
                anomalies.append({
                    'type': 'low_success_rate',
                    'severity': 'critical',
                    'message': f"Low sync success rate: {success_rate:.1%}",
                    'value': success_rate
                })

            # Check for high conflict rate
            conflict_rate = await self.get_conflict_rate(window_minutes=10)
            if conflict_rate > 0.1:  # More than 10%
                anomalies.append({
                    'type': 'high_conflict_rate',
                    'severity': 'warning',
                    'message': f"High conflict rate: {conflict_rate:.1%}",
                    'value': conflict_rate
                })

            # Check for high error rate
            error_stats = await self.get_error_rate(window_minutes=10)
            if error_stats.get('rate', 0) > 0.05:  # More than 5%
                anomalies.append({
                    'type': 'high_error_rate',
                    'severity': 'critical',
                    'message': f"High error rate: {error_stats['rate']:.1%}",
                    'value': error_stats['rate']
                })

            if anomalies:
                logger.warning(f"Detected {len(anomalies)} anomalies")

            return anomalies

        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return []

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)

        return sorted_values[index]

    async def export_metrics(
        self,
        output_file: str,
        window_minutes: int = 60
    ):
        """Export metrics to JSON file"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)

            metrics_to_export = [
                asdict(m) for m in self.metrics_buffer
                if datetime.fromisoformat(m.timestamp) >= since
            ]

            with open(output_file, 'w') as f:
                json.dump(metrics_to_export, f, indent=2)

            logger.info(f"Exported {len(metrics_to_export)} metrics to {output_file}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")


# Example usage
async def main():
    """Example usage"""
    import yaml

    # Load config
    with open('antigravity-config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create metrics collector
    metrics = SyncMetrics(config)

    # Log some example metrics
    for i in range(10):
        await metrics.log({
            'timestamp': datetime.utcnow().isoformat(),
            'sync_latency': 0.5 + (i * 0.1),
            'sync_success_rate': 0.95,
            'conflict_rate': 0.02,
            'agent_utilization': 0.7,
            'cost_per_agent': 0.01,
            'error_rate': 0.01,
            'throughput': 100,
            'agent_id': 'orchestrator'
        })
        await asyncio.sleep(0.1)

    # Generate report
    report = await metrics.generate_report(window_minutes=60)
    print(json.dumps(report, indent=2))

    # Check for anomalies
    anomalies = await metrics.detect_anomalies()
    if anomalies:
        print("\nAnomalies detected:")
        print(json.dumps(anomalies, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
