#!/usr/bin/env python3
"""
Cost Tracker
Track and report AI usage costs for legal discovery
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from codered_client import CodeRedClient


class CostTracker:
    """Track and report AI agent costs"""

    # Model pricing (per 1K tokens)
    PRICING = {
        'gpt-4o': {
            'input': 0.0025,
            'output': 0.010
        },
        'gpt-4o-mini': {
            'input': 0.000150,
            'output': 0.000600
        },
        'text-embedding-3-small': {
            'input': 0.00002,
            'output': 0.00000
        }
    }

    # Agent default models
    AGENT_MODELS = {
        'architect': 'gpt-4o',
        'code': 'gpt-4o',
        'test': 'gpt-4o-mini',
        'review': 'gpt-4o',
        'evidence': 'gpt-4o',
        'cynic': 'gpt-4o'
    }

    def __init__(self):
        """Initialize with CodeRed client"""
        self.codered = CodeRedClient()

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for a query

        Args:
            model: Model name (gpt-4o, gpt-4o-mini, etc.)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        if model not in self.PRICING:
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']

        return input_cost + output_cost

    def estimate_agent_cost(
        self,
        agent_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for an agent query

        Args:
            agent_id: Agent role
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        model = self.AGENT_MODELS.get(agent_id, 'gpt-4o')
        return self.estimate_cost(model, input_tokens, output_tokens)

    def log_cost(
        self,
        agent_id: str,
        case_id: str,
        attorney_id: str,
        cost_usd: float,
        description: str
    ) -> Dict[str, any]:
        """
        Log a cost to the database

        Args:
            agent_id: Agent that incurred cost
            case_id: Associated case
            attorney_id: Attorney responsible
            cost_usd: Cost amount
            description: What the cost was for

        Returns:
            Result dictionary
        """
        return self.codered.track_cost(
            agent_id=agent_id,
            case_id=case_id,
            attorney_id=attorney_id,
            cost_usd=cost_usd,
            description=description
        )

    def get_costs(
        self,
        period: str = 'today',
        attorney_id: Optional[str] = None,
        case_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get costs for a period

        Args:
            period: 'today', 'week', 'month'
            attorney_id: Filter by attorney (optional)
            case_id: Filter by case (optional)

        Returns:
            List of cost records
        """
        # For now, get today's costs
        # TODO: Implement period filtering in database
        return self.codered.get_costs_today(attorney_id=attorney_id)

    def generate_report(
        self,
        period: str = 'today',
        attorney_id: Optional[str] = None,
        case_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate cost report

        Args:
            period: 'today', 'week', 'month'
            attorney_id: Filter by attorney (optional)
            case_id: Filter by case (optional)

        Returns:
            Report dictionary with breakdown
        """
        costs = self.get_costs(period, attorney_id, case_id)

        # Aggregate by agent
        by_agent = defaultdict(float)
        by_case = defaultdict(float)
        by_attorney = defaultdict(float)

        for cost in costs:
            by_agent[cost['agent_id']] += cost['cost_usd']
            by_case[cost['case_id']] += cost['cost_usd']
            by_attorney[cost['attorney_id']] += cost['cost_usd']

        total = sum(by_agent.values())

        report = {
            'period': period,
            'total_cost_usd': total,
            'query_count': len(costs),
            'by_agent': dict(by_agent),
            'by_case': dict(by_case),
            'by_attorney': dict(by_attorney),
            'details': costs
        }

        return report

    def format_report(self, report: Dict) -> str:
        """
        Format report as readable text

        Args:
            report: Report dictionary

        Returns:
            Formatted report string
        """
        output = f"""
# COST REPORT - {report['period'].upper()}

**Total Cost**: ${report['total_cost_usd']:.2f}
**Query Count**: {report['query_count']}
**Average Cost**: ${report['total_cost_usd'] / max(report['query_count'], 1):.2f}/query

## By Agent

"""
        for agent, cost in sorted(report['by_agent'].items(), key=lambda x: -x[1]):
            pct = (cost / report['total_cost_usd'] * 100) if report['total_cost_usd'] > 0 else 0
            output += f"- **{agent}**: ${cost:.2f} ({pct:.1f}%)\n"

        output += "\n## By Case\n\n"
        for case, cost in sorted(report['by_case'].items(), key=lambda x: -x[1]):
            pct = (cost / report['total_cost_usd'] * 100) if report['total_cost_usd'] > 0 else 0
            output += f"- **{case}**: ${cost:.2f} ({pct:.1f}%)\n"

        output += "\n## By Attorney\n\n"
        for attorney, cost in sorted(report['by_attorney'].items(), key=lambda x: -x[1]):
            pct = (cost / report['total_cost_usd'] * 100) if report['total_cost_usd'] > 0 else 0
            output += f"- **{attorney}**: ${cost:.2f} ({pct:.1f}%)\n"

        return output

    def check_budget(
        self,
        period: str = 'today',
        budget_usd: float = 200.0
    ) -> Dict[str, any]:
        """
        Check if budget threshold is exceeded

        Args:
            period: 'today', 'week', 'month'
            budget_usd: Budget threshold

        Returns:
            Dictionary with status and current spend
        """
        costs = self.get_costs(period)
        total = sum(c['cost_usd'] for c in costs)

        pct_used = (total / budget_usd * 100) if budget_usd > 0 else 0

        status = 'OK'
        if pct_used >= 100:
            status = 'EXCEEDED'
        elif pct_used >= 80:
            status = 'WARNING'

        return {
            'period': period,
            'budget_usd': budget_usd,
            'spent_usd': total,
            'remaining_usd': max(0, budget_usd - total),
            'percent_used': pct_used,
            'status': status,
            'query_count': len(costs)
        }

    def alert_if_threshold_exceeded(
        self,
        period: str = 'today',
        budget_usd: float = 200.0
    ) -> Optional[str]:
        """
        Generate alert message if budget exceeded

        Args:
            period: 'today', 'week', 'month'
            budget_usd: Budget threshold

        Returns:
            Alert message or None
        """
        check = self.check_budget(period, budget_usd)

        if check['status'] == 'EXCEEDED':
            return f"""
🚨 BUDGET ALERT - {period.upper()}

Budget: ${budget_usd:.2f}
Spent: ${check['spent_usd']:.2f} ({check['percent_used']:.1f}%)
Over Budget: ${check['spent_usd'] - budget_usd:.2f}

Please review usage and consider:
1. Deferring non-urgent queries
2. Using Test agent (gpt-4o-mini) for simple tasks
3. Caching RAG results
4. Batching operations
"""
        elif check['status'] == 'WARNING':
            return f"""
⚠️ BUDGET WARNING - {period.upper()}

Budget: ${budget_usd:.2f}
Spent: ${check['spent_usd']:.2f} ({check['percent_used']:.1f}%)
Remaining: ${check['remaining_usd']:.2f}

You're approaching your budget limit.
"""
        return None


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Track AI costs for legal discovery')
    parser.add_argument('--report', choices=['today', 'week', 'month'], default='today',
                        help='Generate cost report')
    parser.add_argument('--attorney', help='Filter by attorney ID')
    parser.add_argument('--case', help='Filter by case ID')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                        help='Output format')
    parser.add_argument('--budget', type=float, default=200.0,
                        help='Budget threshold for alerts')
    parser.add_argument('--check-budget', action='store_true',
                        help='Check budget status')

    args = parser.parse_args()

    tracker = CostTracker()

    if args.check_budget:
        # Budget check
        check = tracker.check_budget(period=args.report, budget_usd=args.budget)
        alert = tracker.alert_if_threshold_exceeded(period=args.report, budget_usd=args.budget)

        if args.format == 'json':
            print(json.dumps(check, indent=2))
        else:
            print(f"Budget Status: {check['status']}")
            print(f"Spent: ${check['spent_usd']:.2f} / ${check['budget_usd']:.2f}")
            print(f"Remaining: ${check['remaining_usd']:.2f}")
            if alert:
                print(alert)
    else:
        # Generate report
        report = tracker.generate_report(
            period=args.report,
            attorney_id=args.attorney,
            case_id=args.case
        )

        if args.format == 'json':
            print(json.dumps(report, indent=2))
        else:
            print(tracker.format_report(report))


if __name__ == '__main__':
    main()
