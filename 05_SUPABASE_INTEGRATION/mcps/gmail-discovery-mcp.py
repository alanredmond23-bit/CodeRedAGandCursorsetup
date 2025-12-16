"""
Gmail Discovery MCP Server
Gmail API integration for eDiscovery with privilege detection
"""

import os
import json
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp_auth_handler import get_auth_handler
from mcp_cache import get_cache
from mcp_logging import get_mcp_logger

class GmailDiscoveryMCP:
    """MCP Server for Gmail eDiscovery with privilege protection"""

    def __init__(self):
        self.auth_handler = get_auth_handler()
        self.cache = get_cache()
        self.logger = get_mcp_logger()
        self.service = None
        self._initialize()

        # Privilege detection patterns
        self.privilege_patterns = [
            r'\battorney[- ]client\b',
            r'\bprivileged\b.*\bcommunication\b',
            r'\bwork[- ]product\b',
            r'\bin confidence\b',
            r'\blegal advice\b',
            r'\bcounsel\b',
            r'\bconfidential\b.*\blegal\b',
            r'\bprivilege\b.*\blog\b',
            r'\bdo not produce\b',
            r'\battorney eyes only\b'
        ]

    def _initialize(self):
        """Initialize Gmail API connection"""
        try:
            creds = self.auth_handler.get_gmail_credentials()
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.log_auth_event('gmail', 'initialization', True)
        except Exception as e:
            self.logger.log_auth_event('gmail', 'initialization', False, str(e))
            raise

    def search_emails(self,
                     query: str,
                     date_from: str = None,
                     date_to: str = None,
                     sender: str = None,
                     recipient: str = None,
                     max_results: int = 100) -> Dict[str, Any]:
        """
        Search Gmail with discovery filters

        Args:
            query: Search query
            date_from: Start date (YYYY/MM/DD)
            date_to: End date (YYYY/MM/DD)
            sender: Filter by sender email
            recipient: Filter by recipient email
            max_results: Maximum emails to retrieve

        Returns:
            Email search results with privilege flags
        """
        # Build Gmail search query
        gmail_query = query

        if date_from:
            gmail_query += f' after:{date_from}'
        if date_to:
            gmail_query += f' before:{date_to}'
        if sender:
            gmail_query += f' from:{sender}'
        if recipient:
            gmail_query += f' to:{recipient}'

        try:
            start_time = time.time()

            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=gmail_query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            # Retrieve full message details
            emails = []
            privileged_count = 0

            for msg in messages:
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)
                    if email_data.get('privilege_flagged'):
                        privileged_count += 1

            response_time = (time.time() - start_time) * 1000

            self.logger.log_api_call(
                service='gmail',
                endpoint='messages.list',
                method='GET',
                query=gmail_query,
                response_status=200,
                response_time_ms=response_time
            )

            # Log discovery action
            self.logger.log_discovery_action(
                service='gmail',
                action_type='email_search',
                items_processed=len(emails),
                items_flagged=privileged_count,
                query=gmail_query
            )

            return {
                'query': query,
                'gmail_query': gmail_query,
                'total_results': len(emails),
                'privileged_count': privileged_count,
                'emails': emails,
                'search_date': datetime.now().isoformat()
            }

        except HttpError as e:
            self.logger.log_error('gmail', 'search_error', str(e), query=gmail_query)
            return {'error': str(e), 'query': query}

    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full email details with privilege detection"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}

            # Extract body
            body = self._extract_body(message['payload'])

            # Detect privilege
            privilege_result = self._detect_privilege(
                subject=headers.get('Subject', ''),
                body=body,
                sender=headers.get('From', ''),
                recipient=headers.get('To', '')
            )

            email_data = {
                'id': message_id,
                'thread_id': message.get('threadId'),
                'date': headers.get('Date'),
                'from': headers.get('From'),
                'to': headers.get('To'),
                'cc': headers.get('Cc'),
                'bcc': headers.get('Bcc'),
                'subject': headers.get('Subject'),
                'body': body[:1000] if not privilege_result['flagged'] else '[PRIVILEGED - REDACTED]',
                'labels': message.get('labelIds', []),
                'privilege_flagged': privilege_result['flagged'],
                'privilege_confidence': privilege_result['confidence'],
                'privilege_indicators': privilege_result['indicators'],
                'has_attachments': self._has_attachments(message['payload'])
            }

            # Log privilege detection if flagged
            if privilege_result['flagged']:
                self.logger.log_privilege_detection(
                    service='gmail',
                    item_id=message_id,
                    item_type='email',
                    privilege_indicators=privilege_result['indicators'],
                    confidence=privilege_result['confidence'],
                    flagged=True
                )

            return email_data

        except HttpError as e:
            self.logger.log_error('gmail', 'message_error', str(e), query=message_id)
            return None

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ''

        if 'body' in payload and 'data' in payload['body']:
            import base64
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if 'data' in part['body']:
                        import base64
                        body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')

        return body

    def _has_attachments(self, payload: Dict) -> bool:
        """Check if email has attachments"""
        if 'parts' in payload:
            return any(
                part.get('filename') and part['filename'] != ''
                for part in payload['parts']
            )
        return False

    def _detect_privilege(self,
                         subject: str,
                         body: str,
                         sender: str,
                         recipient: str) -> Dict[str, Any]:
        """
        Detect attorney-client privilege in email

        Returns:
            Dictionary with flagged status, confidence, and indicators
        """
        indicators = []
        confidence = 0.0

        # Combine all text for analysis
        full_text = f"{subject} {body}".lower()

        # Check for privilege patterns
        for pattern in self.privilege_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                indicators.append({
                    'pattern': pattern,
                    'matches': len(matches),
                    'context': matches[0] if matches else None
                })
                confidence += 0.15

        # Check for law firm domains
        law_firm_patterns = [
            r'@.*law\.com',
            r'@.*legal\.com',
            r'@.*llp\.com',
            r'@.*attorneys\.com'
        ]

        email_addresses = f"{sender} {recipient}".lower()
        for pattern in law_firm_patterns:
            if re.search(pattern, email_addresses):
                indicators.append({
                    'pattern': 'law_firm_domain',
                    'context': pattern
                })
                confidence += 0.20

        # Check subject line for privilege markers
        privilege_subject_markers = ['privileged', 'confidential', 'attorney', 'legal']
        for marker in privilege_subject_markers:
            if marker in subject.lower():
                indicators.append({
                    'pattern': 'subject_marker',
                    'context': marker
                })
                confidence += 0.10

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        # Flag if confidence exceeds threshold
        flagged = confidence >= 0.30

        return {
            'flagged': flagged,
            'confidence': round(confidence, 2),
            'indicators': indicators
        }

    def get_email_by_id(self, message_id: str) -> Dict[str, Any]:
        """
        Retrieve specific email by ID

        Args:
            message_id: Gmail message ID

        Returns:
            Full email details
        """
        try:
            email_data = self._get_email_details(message_id)
            if email_data:
                return email_data
            else:
                return {'error': 'Email not found', 'message_id': message_id}

        except Exception as e:
            self.logger.log_error('gmail', 'get_email_error', str(e), query=message_id)
            return {'error': str(e), 'message_id': message_id}

    def export_for_discovery(self,
                           query: str,
                           output_format: str = 'json',
                           include_privileged: bool = False,
                           **kwargs) -> Dict[str, Any]:
        """
        Export emails for discovery production

        Args:
            query: Search query
            output_format: Export format ('json', 'csv', 'eml')
            include_privileged: Include privileged communications (requires special handling)

        Returns:
            Export results
        """
        search_results = self.search_emails(query, **kwargs)

        if 'error' in search_results:
            return search_results

        emails = search_results['emails']

        # Filter privileged if not included
        if not include_privileged:
            emails = [e for e in emails if not e.get('privilege_flagged')]

        export_data = {
            'export_date': datetime.now().isoformat(),
            'query': query,
            'total_exported': len(emails),
            'privileged_excluded': search_results['privileged_count'] if not include_privileged else 0,
            'format': output_format,
            'emails': emails
        }

        # Log discovery export
        self.logger.log_discovery_action(
            service='gmail',
            action_type='export_for_discovery',
            items_processed=search_results['total_results'],
            items_flagged=search_results['privileged_count'],
            query=query
        )

        return export_data

    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        Get complete email thread

        Args:
            thread_id: Gmail thread ID

        Returns:
            All emails in thread
        """
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()

            messages = []
            for msg in thread.get('messages', []):
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    messages.append(email_data)

            return {
                'thread_id': thread_id,
                'message_count': len(messages),
                'messages': messages
            }

        except HttpError as e:
            self.logger.log_error('gmail', 'thread_error', str(e), query=thread_id)
            return {'error': str(e), 'thread_id': thread_id}

    def get_api_status(self) -> Dict[str, Any]:
        """Check Gmail API status"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'status': 'operational',
                'service': 'gmail',
                'email_address': profile.get('emailAddress'),
                'total_messages': profile.get('messagesTotal'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'gmail',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def create_gmail_discovery_mcp():
    """Factory function to create Gmail Discovery MCP"""
    return GmailDiscoveryMCP()


if __name__ == '__main__':
    # Test the MCP server
    mcp = create_gmail_discovery_mcp()
    print("Gmail Discovery MCP Server initialized")
    print("\nTesting email search:")
    results = mcp.search_emails("attorney", max_results=5)
    print(json.dumps(results, indent=2, default=str))
