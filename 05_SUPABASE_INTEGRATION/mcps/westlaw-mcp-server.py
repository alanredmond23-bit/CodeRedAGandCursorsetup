"""
Westlaw MCP Server
Thomson Reuters Westlaw API integration for legal research
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime
from mcp_auth_handler import get_auth_handler
from mcp_cache import get_cache, cached_mcp_call
from mcp_logging import get_mcp_logger

class WestlawMCPServer:
    """MCP Server for Westlaw Legal Research"""

    def __init__(self):
        self.auth_handler = get_auth_handler()
        self.cache = get_cache()
        self.logger = get_mcp_logger()
        self.credentials = None
        self._initialize()

    def _initialize(self):
        """Initialize Westlaw connection"""
        try:
            self.credentials = self.auth_handler.get_westlaw_credentials()
            self.base_url = self.credentials['base_url']
            self.api_key = self.credentials['api_key']
            self.logger.log_auth_event('westlaw', 'initialization', True)
        except Exception as e:
            self.logger.log_auth_event('westlaw', 'initialization', False, str(e))
            raise

    def _make_request(self,
                      endpoint: str,
                      method: str = 'GET',
                      params: Dict = None,
                      data: Dict = None,
                      max_retries: int = 3) -> Dict[str, Any]:
        """Make API request with retry logic and exponential backoff"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
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

                # Log the API call
                self.logger.log_api_call(
                    service='westlaw',
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    response_status=response.status_code,
                    response_time_ms=response_time
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.log_error('westlaw', 'rate_limit', f'Rate limited, retry after {retry_after}s')
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 5
                    self.logger.log_error('westlaw', 'request_error', str(e), query=endpoint)
                    time.sleep(wait_time)
                else:
                    self.logger.log_error('westlaw', 'request_failed', str(e), query=endpoint)
                    raise

        return {'error': 'Max retries exceeded'}

    @cached_mcp_call('westlaw', ttl=86400)  # Cache for 24 hours
    def search_cases(self,
                     query: str,
                     jurisdiction: str = None,
                     date_from: str = None,
                     date_to: str = None,
                     limit: int = 25) -> Dict[str, Any]:
        """
        Search Westlaw case law database

        Args:
            query: Search query (natural language or boolean)
            jurisdiction: Jurisdiction filter (e.g., 'federal', 'CA', 'NY')
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            limit: Maximum results to return

        Returns:
            Dictionary with search results and citations
        """
        params = {
            'query': query,
            'resultSize': limit,
            'orderBy': 'relevance'
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to

        try:
            results = self._make_request('cases/search', params=params)

            # Format results with citations
            formatted_results = {
                'query': query,
                'total_results': results.get('totalResults', 0),
                'cases': self._format_cases(results.get('documents', [])),
                'search_date': datetime.now().isoformat()
            }

            return formatted_results

        except Exception as e:
            self.logger.log_error('westlaw', 'search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def _format_cases(self, documents: List[Dict]) -> List[Dict]:
        """Format case results with proper citations"""
        formatted = []

        for doc in documents:
            formatted.append({
                'title': doc.get('title'),
                'citation': doc.get('citation'),
                'court': doc.get('court'),
                'date': doc.get('decisionDate'),
                'summary': doc.get('summary'),
                'key_numbers': doc.get('keyNumbers', []),
                'headnotes': doc.get('headnotes', []),
                'url': doc.get('url'),
                'document_id': doc.get('documentId')
            })

        return formatted

    @cached_mcp_call('westlaw', ttl=86400)
    def get_case_by_citation(self, citation: str) -> Dict[str, Any]:
        """
        Retrieve full case text by citation

        Args:
            citation: Case citation (e.g., "410 U.S. 113")

        Returns:
            Full case document with all opinions
        """
        try:
            result = self._make_request(f'cases/citation/{citation}')

            return {
                'citation': citation,
                'title': result.get('title'),
                'court': result.get('court'),
                'date': result.get('decisionDate'),
                'judges': result.get('judges', []),
                'opinion': result.get('fullText'),
                'headnotes': result.get('headnotes', []),
                'cited_cases': result.get('citedCases', []),
                'citing_cases_count': result.get('citingCasesCount', 0)
            }

        except Exception as e:
            self.logger.log_error('westlaw', 'citation_error', str(e), query=citation)
            return {'error': str(e), 'citation': citation}

    @cached_mcp_call('westlaw', ttl=86400)
    def search_statutes(self,
                       query: str,
                       jurisdiction: str = None,
                       limit: int = 25) -> Dict[str, Any]:
        """
        Search statutes and regulations

        Args:
            query: Search query
            jurisdiction: Jurisdiction (e.g., 'US', 'CA')
            limit: Maximum results

        Returns:
            Statute search results
        """
        params = {
            'query': query,
            'resultSize': limit,
            'contentType': 'STATUTES'
        }

        if jurisdiction:
            params['jurisdiction'] = jurisdiction

        try:
            results = self._make_request('statutes/search', params=params)

            return {
                'query': query,
                'total_results': results.get('totalResults', 0),
                'statutes': [{
                    'title': s.get('title'),
                    'citation': s.get('citation'),
                    'jurisdiction': s.get('jurisdiction'),
                    'effective_date': s.get('effectiveDate'),
                    'text': s.get('text'),
                    'url': s.get('url')
                } for s in results.get('documents', [])]
            }

        except Exception as e:
            self.logger.log_error('westlaw', 'statute_search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def shepardize(self, citation: str) -> Dict[str, Any]:
        """
        Shepardize a case (get treatment and citation history)

        Args:
            citation: Case citation to shepardize

        Returns:
            Citation analysis with treatment signals
        """
        try:
            result = self._make_request(f'citator/shepards/{citation}')

            return {
                'citation': citation,
                'treatment': result.get('treatment'),  # positive, negative, caution, etc.
                'signal': result.get('signal'),
                'cited_by_count': result.get('citedByCount', 0),
                'citing_cases': [{
                    'citation': c.get('citation'),
                    'treatment': c.get('treatment'),
                    'depth': c.get('depth'),
                    'court': c.get('court')
                } for c in result.get('citingCases', [])[:50]],  # Limit to 50 most important
                'analysis': result.get('analysis')
            }

        except Exception as e:
            self.logger.log_error('westlaw', 'shepardize_error', str(e), query=citation)
            return {'error': str(e), 'citation': citation}

    @cached_mcp_call('westlaw', ttl=3600)
    def search_secondary_sources(self,
                                 query: str,
                                 source_type: str = 'all',
                                 limit: int = 25) -> Dict[str, Any]:
        """
        Search secondary sources (treatises, law reviews, etc.)

        Args:
            query: Search query
            source_type: Type of source ('treatises', 'law_reviews', 'all')
            limit: Maximum results

        Returns:
            Secondary source results
        """
        params = {
            'query': query,
            'resultSize': limit,
            'contentType': 'SECONDARY_SOURCES'
        }

        if source_type != 'all':
            params['sourceType'] = source_type

        try:
            results = self._make_request('secondary/search', params=params)

            return {
                'query': query,
                'source_type': source_type,
                'total_results': results.get('totalResults', 0),
                'sources': [{
                    'title': s.get('title'),
                    'author': s.get('author'),
                    'publication': s.get('publication'),
                    'date': s.get('publicationDate'),
                    'citation': s.get('citation'),
                    'summary': s.get('summary'),
                    'url': s.get('url')
                } for s in results.get('documents', [])]
            }

        except Exception as e:
            self.logger.log_error('westlaw', 'secondary_search_error', str(e), query=query)
            return {'error': str(e), 'query': query}

    def get_api_status(self) -> Dict[str, Any]:
        """Check Westlaw API status"""
        try:
            result = self._make_request('status')
            return {
                'status': 'operational',
                'service': 'westlaw',
                'timestamp': datetime.now().isoformat(),
                **result
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'westlaw',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# MCP Server Interface
def create_westlaw_mcp():
    """Factory function to create Westlaw MCP server"""
    return WestlawMCPServer()


if __name__ == '__main__':
    # Test the MCP server
    mcp = create_westlaw_mcp()
    print("Westlaw MCP Server initialized")
    print("\nTesting case search:")
    results = mcp.search_cases("attorney client privilege", jurisdiction="federal", limit=5)
    print(json.dumps(results, indent=2))
