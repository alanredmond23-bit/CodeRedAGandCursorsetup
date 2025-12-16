"""
MCP Compliance Logging System
Tracks all API calls for legal compliance and auditing
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import traceback

class MCPLogger:
    """Compliance-focused logging for all MCP operations"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create separate loggers for different purposes
        self.api_logger = self._setup_logger('api_calls', 'api_calls.log')
        self.auth_logger = self._setup_logger('auth', 'auth.log')
        self.error_logger = self._setup_logger('errors', 'errors.log')
        self.compliance_logger = self._setup_logger('compliance', 'compliance.log')

        # Cost tracking
        self.cost_tracking = {
            'westlaw': {'calls': 0, 'estimated_cost': 0.0},
            'lexisnexis': {'calls': 0, 'estimated_cost': 0.0},
            'gmail': {'calls': 0, 'estimated_cost': 0.0},
            'slack': {'calls': 0, 'estimated_cost': 0.0},
            'supabase': {'calls': 0, 'estimated_cost': 0.0},
            'github': {'calls': 0, 'estimated_cost': 0.0}
        }

    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        """Setup a rotating file logger"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Rotating file handler (max 10MB, keep 10 backups)
        handler = RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=10*1024*1024,
            backupCount=10
        )

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def log_api_call(self,
                     service: str,
                     endpoint: str,
                     method: str = 'GET',
                     query: str = None,
                     params: Dict = None,
                     response_status: int = None,
                     response_time_ms: float = None,
                     cached: bool = False,
                     user: str = None):
        """Log an API call with full details"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'endpoint': endpoint,
            'method': method,
            'query': query,
            'params': self._sanitize_params(params),
            'response_status': response_status,
            'response_time_ms': response_time_ms,
            'cached': cached,
            'user': user or 'system'
        }

        self.api_logger.info(json.dumps(log_entry))

        # Update cost tracking
        self._update_cost_tracking(service, cached)

    def log_auth_event(self,
                       service: str,
                       event_type: str,
                       success: bool,
                       details: str = None,
                       user: str = None):
        """Log authentication events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'event_type': event_type,
            'success': success,
            'details': details,
            'user': user or 'system'
        }

        self.auth_logger.info(json.dumps(log_entry))

        if not success:
            self.error_logger.warning(f"Auth failure for {service}: {details}")

    def log_error(self,
                  service: str,
                  error_type: str,
                  error_message: str,
                  query: str = None,
                  stack_trace: str = None):
        """Log errors with full context"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'error_type': error_type,
            'error_message': error_message,
            'query': query,
            'stack_trace': stack_trace or traceback.format_exc()
        }

        self.error_logger.error(json.dumps(log_entry))

    def log_privilege_detection(self,
                                service: str,
                                item_id: str,
                                item_type: str,
                                privilege_indicators: list,
                                confidence: float,
                                flagged: bool):
        """Log privilege detection for compliance"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'item_id': item_id,
            'item_type': item_type,
            'privilege_indicators': privilege_indicators,
            'confidence': confidence,
            'flagged': flagged,
            'compliance_critical': True
        }

        self.compliance_logger.info(json.dumps(log_entry))

    def log_discovery_action(self,
                            service: str,
                            action_type: str,
                            items_processed: int,
                            items_flagged: int,
                            query: str = None,
                            date_range: Dict = None):
        """Log discovery actions for legal compliance"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'action_type': action_type,
            'items_processed': items_processed,
            'items_flagged': items_flagged,
            'query': query,
            'date_range': date_range,
            'compliance_critical': True
        }

        self.compliance_logger.info(json.dumps(log_entry))

    def _sanitize_params(self, params: Dict) -> Dict:
        """Remove sensitive data from parameters"""
        if not params:
            return {}

        sanitized = params.copy()
        sensitive_keys = ['password', 'token', 'api_key', 'secret', 'authorization']

        for key in list(sanitized.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'

        return sanitized

    def _update_cost_tracking(self, service: str, cached: bool):
        """Update cost tracking for service"""
        if cached:
            return  # No cost for cached responses

        # Estimated costs per API call (in USD)
        cost_per_call = {
            'westlaw': 0.10,      # Westlaw API calls are expensive
            'lexisnexis': 0.08,   # LexisNexis per-query cost
            'gmail': 0.00,        # Gmail API is free but rate-limited
            'slack': 0.00,        # Slack API free for standard tier
            'supabase': 0.001,    # Supabase database queries
            'github': 0.00        # GitHub API free for authenticated users
        }

        if service in self.cost_tracking:
            self.cost_tracking[service]['calls'] += 1
            self.cost_tracking[service]['estimated_cost'] += cost_per_call.get(service, 0.0)

    def get_cost_report(self, service: str = None) -> Dict[str, Any]:
        """Get cost tracking report"""
        if service:
            return self.cost_tracking.get(service, {})

        total_cost = sum(data['estimated_cost'] for data in self.cost_tracking.values())
        total_calls = sum(data['calls'] for data in self.cost_tracking.values())

        return {
            'total_calls': total_calls,
            'total_estimated_cost': round(total_cost, 2),
            'by_service': self.cost_tracking,
            'report_date': datetime.now().isoformat()
        }

    def get_compliance_summary(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Generate compliance summary for date range"""
        # Parse compliance log for summary
        compliance_log_path = self.log_dir / 'compliance.log'

        if not compliance_log_path.exists():
            return {'error': 'No compliance logs found'}

        summary = {
            'privilege_detections': 0,
            'discovery_actions': 0,
            'items_flagged': 0,
            'services_accessed': set()
        }

        try:
            with open(compliance_log_path, 'r') as f:
                for line in f:
                    try:
                        # Extract JSON from log line
                        json_start = line.find('{')
                        if json_start != -1:
                            entry = json.loads(line[json_start:])

                            # Filter by date range if specified
                            if start_date or end_date:
                                entry_date = entry.get('timestamp', '')
                                if start_date and entry_date < start_date:
                                    continue
                                if end_date and entry_date > end_date:
                                    continue

                            # Count different types of compliance events
                            if 'privilege_indicators' in entry:
                                summary['privilege_detections'] += 1
                                if entry.get('flagged'):
                                    summary['items_flagged'] += 1

                            if 'action_type' in entry:
                                summary['discovery_actions'] += 1

                            if 'service' in entry:
                                summary['services_accessed'].add(entry['service'])

                    except json.JSONDecodeError:
                        continue

            summary['services_accessed'] = list(summary['services_accessed'])
            return summary

        except Exception as e:
            return {'error': str(e)}


# Singleton instance
_logger = None

def get_mcp_logger() -> MCPLogger:
    """Get singleton logger instance"""
    global _logger
    if _logger is None:
        _logger = MCPLogger()
    return _logger
