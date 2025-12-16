"""
Slack Discovery MCP Server
Slack API integration for message archiving and eDiscovery
"""

import os
import json
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from mcp_auth_handler import get_auth_handler
from mcp_cache import get_cache
from mcp_logging import get_mcp_logger

class SlackDiscoveryMCP:
    """MCP Server for Slack eDiscovery with privilege detection"""

    def __init__(self):
        self.auth_handler = get_auth_handler()
        self.cache = get_cache()
        self.logger = get_mcp_logger()
        self.credentials = None
        self._initialize()

        # Privilege detection patterns
        self.privilege_patterns = [
            r'\battorney[- ]client\b',
            r'\bprivileged\b.*\bcommunication\b',
            r'\bwork[- ]product\b',
            r'\blegal advice\b',
            r'\bconfidential\b.*\blegal\b',
            r'\battorney eyes only\b',
            r'\bcounsel\b.*\bonly\b'
        ]

    def _initialize(self):
        """Initialize Slack API connection"""
        try:
            self.credentials = self.auth_handler.get_slack_credentials()
            self.base_url = self.credentials['base_url']
            self.token = self.credentials['oauth_token']
            self.logger.log_auth_event('slack', 'initialization', True)
        except Exception as e:
            self.logger.log_auth_event('slack', 'initialization', False, str(e))
            raise

    def _make_request(self,
                      endpoint: str,
                      method: str = 'GET',
                      params: Dict = None,
                      data: Dict = None,
                      max_retries: int = 3) -> Dict[str, Any]:
        """Make Slack API request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                if method == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=30)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response_time = (time.time() - start_time) * 1000

                result = response.json()

                self.logger.log_api_call(
                    service='slack',
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    response_status=response.status_code,
                    response_time_ms=response_time
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.log_error('slack', 'rate_limit', f'Rate limited, retry after {retry_after}s')
                    time.sleep(retry_after)
                    continue

                if not result.get('ok'):
                    raise Exception(f"Slack API error: {result.get('error')}")

                return result

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5
                    self.logger.log_error('slack', 'request_error', str(e), query=endpoint)
                    time.sleep(wait_time)
                else:
                    self.logger.log_error('slack', 'request_failed', str(e), query=endpoint)
                    raise

        return {'ok': False, 'error': 'Max retries exceeded'}

    def search_messages(self,
                       query: str,
                       count: int = 100,
                       sort: str = 'timestamp',
                       sort_dir: str = 'desc') -> Dict[str, Any]:
        """
        Search Slack messages across all channels

        Args:
            query: Search query
            count: Number of results (max 100 per page)
            sort: Sort field ('score' or 'timestamp')
            sort_dir: Sort direction ('asc' or 'desc')

        Returns:
            Search results with privilege flags
        """
        params = {
            'query': query,
            'count': min(count, 100),
            'sort': sort,
            'sort_dir': sort_dir
        }

        try:
            result = self._make_request('search.messages', params=params)

            messages = result.get('messages', {}).get('matches', [])

            # Process messages for privilege detection
            processed_messages = []
            privileged_count = 0

            for msg in messages:
                message_data = self._process_message(msg)
                processed_messages.append(message_data)
                if message_data.get('privilege_flagged'):
                    privileged_count += 1

            # Log discovery action
            self.logger.log_discovery_action(
                service='slack',
                action_type='message_search',
                items_processed=len(processed_messages),
                items_flagged=privileged_count,
                query=query
            )

            return {
                'query': query,
                'total_results': result.get('messages', {}).get('total', 0),
                'privileged_count': privileged_count,
                'messages': processed_messages,
                'search_date': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.log_error('slack', 'search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def _process_message(self, message: Dict) -> Dict[str, Any]:
        """Process message with privilege detection"""
        text = message.get('text', '')
        user = message.get('user', message.get('username'))
        channel = message.get('channel', {})

        # Detect privilege
        privilege_result = self._detect_privilege(text, user, channel)

        message_data = {
            'timestamp': message.get('ts'),
            'date': datetime.fromtimestamp(float(message.get('ts', 0))).isoformat() if message.get('ts') else None,
            'user': user,
            'channel_id': channel.get('id') if isinstance(channel, dict) else channel,
            'channel_name': channel.get('name') if isinstance(channel, dict) else None,
            'text': text[:500] if not privilege_result['flagged'] else '[PRIVILEGED - REDACTED]',
            'type': message.get('type'),
            'permalink': message.get('permalink'),
            'privilege_flagged': privilege_result['flagged'],
            'privilege_confidence': privilege_result['confidence'],
            'privilege_indicators': privilege_result['indicators'],
            'has_files': bool(message.get('files', [])),
            'reactions': message.get('reactions', [])
        }

        # Log privilege detection if flagged
        if privilege_result['flagged']:
            self.logger.log_privilege_detection(
                service='slack',
                item_id=message.get('ts', 'unknown'),
                item_type='message',
                privilege_indicators=privilege_result['indicators'],
                confidence=privilege_result['confidence'],
                flagged=True
            )

        return message_data

    def _detect_privilege(self, text: str, user: str, channel: Any) -> Dict[str, Any]:
        """Detect privilege in Slack message"""
        indicators = []
        confidence = 0.0

        text_lower = text.lower()

        # Check for privilege patterns
        for pattern in self.privilege_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                indicators.append({
                    'pattern': pattern,
                    'matches': len(matches)
                })
                confidence += 0.20

        # Check for legal channel names
        channel_name = ''
        if isinstance(channel, dict):
            channel_name = channel.get('name', '').lower()
        elif isinstance(channel, str):
            channel_name = channel.lower()

        legal_channel_patterns = ['legal', 'attorney', 'counsel', 'privileged', 'law']
        for pattern in legal_channel_patterns:
            if pattern in channel_name:
                indicators.append({
                    'pattern': 'legal_channel',
                    'context': channel_name
                })
                confidence += 0.15

        # Cap confidence
        confidence = min(confidence, 1.0)

        # Flag if confidence exceeds threshold
        flagged = confidence >= 0.30

        return {
            'flagged': flagged,
            'confidence': round(confidence, 2),
            'indicators': indicators
        }

    def get_channel_history(self,
                           channel_id: str,
                           oldest: str = None,
                           latest: str = None,
                           limit: int = 100) -> Dict[str, Any]:
        """
        Get message history for a specific channel

        Args:
            channel_id: Slack channel ID
            oldest: Oldest timestamp to include
            latest: Latest timestamp to include
            limit: Maximum messages to retrieve

        Returns:
            Channel message history
        """
        params = {
            'channel': channel_id,
            'limit': min(limit, 1000)
        }

        if oldest:
            params['oldest'] = oldest
        if latest:
            params['latest'] = latest

        try:
            result = self._make_request('conversations.history', params=params)

            messages = result.get('messages', [])

            # Process messages
            processed_messages = []
            privileged_count = 0

            for msg in messages:
                message_data = self._process_message(msg)
                processed_messages.append(message_data)
                if message_data.get('privilege_flagged'):
                    privileged_count += 1

            # Log discovery action
            self.logger.log_discovery_action(
                service='slack',
                action_type='channel_history',
                items_processed=len(processed_messages),
                items_flagged=privileged_count,
                query=channel_id
            )

            return {
                'channel_id': channel_id,
                'message_count': len(processed_messages),
                'privileged_count': privileged_count,
                'messages': processed_messages,
                'has_more': result.get('has_more', False)
            }

        except Exception as e:
            self.logger.log_error('slack', 'channel_history_error', str(e), query=channel_id)
            return {'error': str(e), 'channel_id': channel_id}

    def list_channels(self, types: str = 'public_channel,private_channel') -> Dict[str, Any]:
        """
        List all accessible channels

        Args:
            types: Channel types to include

        Returns:
            List of channels
        """
        params = {
            'types': types,
            'limit': 1000
        }

        try:
            result = self._make_request('conversations.list', params=params)

            channels = result.get('channels', [])

            return {
                'total_channels': len(channels),
                'channels': [{
                    'id': c.get('id'),
                    'name': c.get('name'),
                    'is_private': c.get('is_private'),
                    'is_archived': c.get('is_archived'),
                    'num_members': c.get('num_members'),
                    'created': c.get('created'),
                    'topic': c.get('topic', {}).get('value'),
                    'purpose': c.get('purpose', {}).get('value')
                } for c in channels]
            }

        except Exception as e:
            self.logger.log_error('slack', 'list_channels_error', str(e))
            return {'error': str(e)}

    def export_for_discovery(self,
                           channel_id: str = None,
                           query: str = None,
                           date_from: str = None,
                           date_to: str = None,
                           include_privileged: bool = False) -> Dict[str, Any]:
        """
        Export Slack messages for discovery production

        Args:
            channel_id: Specific channel to export
            query: Search query
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            include_privileged: Include privileged messages

        Returns:
            Export data
        """
        messages = []

        if channel_id:
            # Export specific channel
            oldest = None
            latest = None

            if date_from:
                oldest = str(int(datetime.strptime(date_from, '%Y-%m-%d').timestamp()))
            if date_to:
                latest = str(int(datetime.strptime(date_to, '%Y-%m-%d').timestamp()))

            result = self.get_channel_history(channel_id, oldest, latest, limit=1000)
            if 'messages' in result:
                messages = result['messages']

        elif query:
            # Export by search query
            result = self.search_messages(query, count=100)
            if 'messages' in result:
                messages = result['messages']

        else:
            return {'error': 'Must provide either channel_id or query'}

        # Filter privileged if not included
        privileged_count = sum(1 for m in messages if m.get('privilege_flagged'))

        if not include_privileged:
            messages = [m for m in messages if not m.get('privilege_flagged')]

        export_data = {
            'export_date': datetime.now().isoformat(),
            'channel_id': channel_id,
            'query': query,
            'date_range': {
                'from': date_from,
                'to': date_to
            },
            'total_exported': len(messages),
            'privileged_excluded': privileged_count if not include_privileged else 0,
            'messages': messages
        }

        # Log export
        self.logger.log_discovery_action(
            service='slack',
            action_type='export_for_discovery',
            items_processed=len(messages) + (privileged_count if not include_privileged else 0),
            items_flagged=privileged_count,
            query=query or channel_id
        )

        return export_data

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information"""
        try:
            result = self._make_request('users.info', params={'user': user_id})

            user = result.get('user', {})
            return {
                'id': user.get('id'),
                'name': user.get('name'),
                'real_name': user.get('real_name'),
                'email': user.get('profile', {}).get('email'),
                'title': user.get('profile', {}).get('title'),
                'is_admin': user.get('is_admin'),
                'is_bot': user.get('is_bot')
            }

        except Exception as e:
            self.logger.log_error('slack', 'user_info_error', str(e), query=user_id)
            return {'error': str(e), 'user_id': user_id}

    def get_api_status(self) -> Dict[str, Any]:
        """Check Slack API status"""
        try:
            result = self._make_request('auth.test')
            return {
                'status': 'operational',
                'service': 'slack',
                'team': result.get('team'),
                'user': result.get('user'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'slack',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def create_slack_discovery_mcp():
    """Factory function to create Slack Discovery MCP"""
    return SlackDiscoveryMCP()


if __name__ == '__main__':
    # Test the MCP server
    mcp = create_slack_discovery_mcp()
    print("Slack Discovery MCP Server initialized")
    print("\nTesting message search:")
    results = mcp.search_messages("legal", count=5)
    print(json.dumps(results, indent=2, default=str))
