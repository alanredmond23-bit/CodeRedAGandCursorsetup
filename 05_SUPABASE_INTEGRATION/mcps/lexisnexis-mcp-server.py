"""
LexisNexis MCP Server
LexisNexis Protégé API integration for legal research
"""

import os
import json
import time
import base64
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime
from mcp_auth_handler import get_auth_handler
from mcp_cache import get_cache, cached_mcp_call
from mcp_logging import get_mcp_logger

class LexisNexisMCPServer:
    """MCP Server for LexisNexis Legal Research"""

    def __init__(self):
        self.auth_handler = get_auth_handler()
        self.cache = get_cache()
        self.logger = get_mcp_logger()
        self.credentials = None
        self.access_token = None
        self._initialize()

    def _initialize(self):
        """Initialize LexisNexis connection and get access token"""
        try:
            self.credentials = self.auth_handler.get_lexisnexis_credentials()
            self.base_url = self.credentials['base_url']
            self._get_access_token()
            self.logger.log_auth_event('lexisnexis', 'initialization', True)
        except Exception as e:
            self.logger.log_auth_event('lexisnexis', 'initialization', False, str(e))
            raise

    def _get_access_token(self):
        """Get OAuth access token"""
        auth_url = 'https://auth.lexisnexis.com/oauth/v2/token'
        auth_string = f"{self.credentials['api_key']}:{self.credentials['api_secret']}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'client_credentials',
            'scope': 'api.lexisnexis.com'
        }

        try:
            response = requests.post(auth_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            self.logger.log_auth_event('lexisnexis', 'token_grant', True)
        except Exception as e:
            self.logger.log_auth_event('lexisnexis', 'token_grant', False, str(e))
            raise

    def _make_request(self,
                      endpoint: str,
                      method: str = 'POST',
                      params: Dict = None,
                      data: Dict = None,
                      max_retries: int = 3) -> Dict[str, Any]:
        """Make API request with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
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

                self.logger.log_api_call(
                    service='lexisnexis',
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    response_status=response.status_code,
                    response_time_ms=response_time
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.log_error('lexisnexis', 'rate_limit', f'Rate limited, retry after {retry_after}s')
                    time.sleep(retry_after)
                    continue

                # Token expired - refresh
                if response.status_code == 401:
                    self._get_access_token()
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5
                    self.logger.log_error('lexisnexis', 'request_error', str(e), query=endpoint)
                    time.sleep(wait_time)
                else:
                    self.logger.log_error('lexisnexis', 'request_failed', str(e), query=endpoint)
                    raise

        return {'error': 'Max retries exceeded'}

    @cached_mcp_call('lexisnexis', ttl=86400)
    def search_cases(self,
                     query: str,
                     jurisdiction: str = None,
                     date_from: str = None,
                     date_to: str = None,
                     limit: int = 25) -> Dict[str, Any]:
        """
        Search LexisNexis case law

        Args:
            query: Search query (natural language or boolean)
            jurisdiction: Jurisdiction filter
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            limit: Maximum results

        Returns:
            Case search results with citations
        """
        search_data = {
            'query': query,
            'source': 'cases',
            'pagination': {
                'pageSize': limit
            },
            'sort': 'relevance'
        }

        if jurisdiction:
            search_data['filters'] = search_data.get('filters', {})
            search_data['filters']['jurisdiction'] = jurisdiction

        if date_from or date_to:
            search_data['filters'] = search_data.get('filters', {})
            search_data['filters']['dateRange'] = {}
            if date_from:
                search_data['filters']['dateRange']['from'] = date_from
            if date_to:
                search_data['filters']['dateRange']['to'] = date_to

        try:
            results = self._make_request('search', method='POST', data=search_data)

            formatted_results = {
                'query': query,
                'total_results': results.get('totalResults', 0),
                'cases': self._format_cases(results.get('results', [])),
                'search_date': datetime.now().isoformat()
            }

            return formatted_results

        except Exception as e:
            self.logger.log_error('lexisnexis', 'search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def _format_cases(self, results: List[Dict]) -> List[Dict]:
        """Format case results"""
        formatted = []

        for result in results:
            doc = result.get('document', {})
            formatted.append({
                'title': doc.get('title'),
                'citation': doc.get('citation'),
                'court': doc.get('court'),
                'date': doc.get('decisionDate'),
                'judges': doc.get('judges', []),
                'summary': doc.get('summary'),
                'headnotes': doc.get('headnotes', []),
                'shepards_signal': doc.get('shepardsSignal'),
                'url': doc.get('url'),
                'document_id': doc.get('documentId')
            })

        return formatted

    @cached_mcp_call('lexisnexis', ttl=86400)
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve full document by ID

        Args:
            document_id: LexisNexis document ID

        Returns:
            Full document content
        """
        try:
            result = self._make_request(f'documents/{document_id}', method='GET')

            return {
                'document_id': document_id,
                'title': result.get('title'),
                'citation': result.get('citation'),
                'court': result.get('court'),
                'date': result.get('decisionDate'),
                'full_text': result.get('fullText'),
                'headnotes': result.get('headnotes', []),
                'counsel': result.get('counsel', []),
                'judges': result.get('judges', [])
            }

        except Exception as e:
            self.logger.log_error('lexisnexis', 'document_error', str(e), query=document_id)
            return {'error': str(e), 'document_id': document_id}

    @cached_mcp_call('lexisnexis', ttl=86400)
    def search_statutes(self,
                       query: str,
                       jurisdiction: str = None,
                       code: str = None,
                       limit: int = 25) -> Dict[str, Any]:
        """
        Search statutes and codes

        Args:
            query: Search query
            jurisdiction: Jurisdiction (e.g., 'US', 'CA')
            code: Specific code (e.g., 'USC', 'CFR')
            limit: Maximum results

        Returns:
            Statute search results
        """
        search_data = {
            'query': query,
            'source': 'statutes',
            'pagination': {
                'pageSize': limit
            }
        }

        if jurisdiction or code:
            search_data['filters'] = {}
            if jurisdiction:
                search_data['filters']['jurisdiction'] = jurisdiction
            if code:
                search_data['filters']['code'] = code

        try:
            results = self._make_request('search', method='POST', data=search_data)

            return {
                'query': query,
                'total_results': results.get('totalResults', 0),
                'statutes': [{
                    'title': r.get('document', {}).get('title'),
                    'citation': r.get('document', {}).get('citation'),
                    'jurisdiction': r.get('document', {}).get('jurisdiction'),
                    'code': r.get('document', {}).get('code'),
                    'section': r.get('document', {}).get('section'),
                    'effective_date': r.get('document', {}).get('effectiveDate'),
                    'text': r.get('document', {}).get('text'),
                    'url': r.get('document', {}).get('url')
                } for r in results.get('results', [])]
            }

        except Exception as e:
            self.logger.log_error('lexisnexis', 'statute_search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def shepardize(self, citation: str) -> Dict[str, Any]:
        """
        Get Shepard's Citations analysis

        Args:
            citation: Case citation

        Returns:
            Citation treatment and analysis
        """
        try:
            data = {'citation': citation}
            result = self._make_request('shepards/analyze', method='POST', data=data)

            return {
                'citation': citation,
                'signal': result.get('signal'),  # red flag, yellow flag, etc.
                'treatment': result.get('treatment'),
                'cited_by_count': result.get('citedByCount', 0),
                'citing_decisions': [{
                    'citation': c.get('citation'),
                    'treatment': c.get('treatment'),
                    'analysis': c.get('analysis'),
                    'court': c.get('court'),
                    'date': c.get('date')
                } for c in result.get('citingDecisions', [])[:50]],
                'analysis_summary': result.get('analysisSummary')
            }

        except Exception as e:
            self.logger.log_error('lexisnexis', 'shepards_error', str(e), query=citation)
            return {'error': str(e), 'citation': citation}

    @cached_mcp_call('lexisnexis', ttl=3600)
    def search_news(self,
                    query: str,
                    date_from: str = None,
                    date_to: str = None,
                    limit: int = 25) -> Dict[str, Any]:
        """
        Search legal news and publications

        Args:
            query: Search query
            date_from: Start date
            date_to: End date
            limit: Maximum results

        Returns:
            News search results
        """
        search_data = {
            'query': query,
            'source': 'news',
            'pagination': {
                'pageSize': limit
            }
        }

        if date_from or date_to:
            search_data['filters'] = {'dateRange': {}}
            if date_from:
                search_data['filters']['dateRange']['from'] = date_from
            if date_to:
                search_data['filters']['dateRange']['to'] = date_to

        try:
            results = self._make_request('search', method='POST', data=search_data)

            return {
                'query': query,
                'total_results': results.get('totalResults', 0),
                'articles': [{
                    'title': r.get('document', {}).get('title'),
                    'publication': r.get('document', {}).get('publication'),
                    'date': r.get('document', {}).get('publicationDate'),
                    'author': r.get('document', {}).get('author'),
                    'summary': r.get('document', {}).get('summary'),
                    'url': r.get('document', {}).get('url')
                } for r in results.get('results', [])]
            }

        except Exception as e:
            self.logger.log_error('lexisnexis', 'news_search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    @cached_mcp_call('lexisnexis', ttl=3600)
    def search_law_reviews(self,
                          query: str,
                          limit: int = 25) -> Dict[str, Any]:
        """
        Search law review articles

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Law review search results
        """
        search_data = {
            'query': query,
            'source': 'law-reviews',
            'pagination': {
                'pageSize': limit
            }
        }

        try:
            results = self._make_request('search', method='POST', data=search_data)

            return {
                'query': query,
                'total_results': results.get('totalResults', 0),
                'articles': [{
                    'title': r.get('document', {}).get('title'),
                    'author': r.get('document', {}).get('author'),
                    'law_review': r.get('document', {}).get('publication'),
                    'volume': r.get('document', {}).get('volume'),
                    'page': r.get('document', {}).get('page'),
                    'date': r.get('document', {}).get('publicationDate'),
                    'citation': r.get('document', {}).get('citation'),
                    'abstract': r.get('document', {}).get('abstract'),
                    'url': r.get('document', {}).get('url')
                } for r in results.get('results', [])]
            }

        except Exception as e:
            self.logger.log_error('lexisnexis', 'law_review_search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def get_api_status(self) -> Dict[str, Any]:
        """Check LexisNexis API status"""
        try:
            result = self._make_request('status', method='GET')
            return {
                'status': 'operational',
                'service': 'lexisnexis',
                'timestamp': datetime.now().isoformat(),
                **result
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'lexisnexis',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def create_lexisnexis_mcp():
    """Factory function to create LexisNexis MCP server"""
    return LexisNexisMCPServer()


if __name__ == '__main__':
    # Test the MCP server
    mcp = create_lexisnexis_mcp()
    print("LexisNexis MCP Server initialized")
    print("\nTesting case search:")
    results = mcp.search_cases("attorney-client privilege", jurisdiction="federal", limit=5)
    print(json.dumps(results, indent=2))
