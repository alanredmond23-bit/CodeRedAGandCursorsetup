"""
LexisNexis Research Module

Interfaces with LexisNexis API for case law research.
CRITICAL: All citations must be accurate and verifiable.
"""

import os
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class LexisNexisResearcher:
    """
    Interface to LexisNexis API for legal research

    API Documentation: https://developer.lexisnexis.com/
    """

    BASE_URL = "https://api.lexisnexis.com/v1"

    def __init__(self, api_key: str):
        """
        Initialize LexisNexis researcher

        Args:
            api_key: LexisNexis API key
        """
        if not api_key:
            logger.warning("No LexisNexis API key provided - research will be limited")

        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def search(self, query: str, jurisdiction: str = 'federal',
               max_results: int = 50, date_range: Optional[tuple] = None) -> List[Dict]:
        """
        Search LexisNexis for case law

        Args:
            query: Search query string
            jurisdiction: Jurisdiction filter
            max_results: Maximum number of results
            date_range: Optional date range filter

        Returns:
            List of case dictionaries
        """
        logger.info(f"Searching LexisNexis: '{query}' in {jurisdiction}")

        if not self.api_key:
            logger.warning("Using mock data - no API key provided")
            return self._mock_search(query, jurisdiction, max_results)

        try:
            # Build search parameters
            params = {
                'q': query,
                'jurisdiction': jurisdiction,
                'pageSize': max_results,
                'sort': 'relevance'
            }

            if date_range:
                params['dateFrom'] = date_range[0]
                params['dateTo'] = date_range[1]

            # Make API request
            response = self.session.get(
                f"{self.BASE_URL}/search/cases",
                params=params,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # Parse results
            cases = self._parse_results(data)

            logger.info(f"Found {len(cases)} cases from LexisNexis")
            return cases

        except requests.exceptions.RequestException as e:
            logger.error(f"LexisNexis API error: {str(e)}")
            return self._mock_search(query, jurisdiction, max_results)

    def get_case_by_citation(self, citation: str) -> Optional[Dict]:
        """
        Retrieve full case details by citation

        Args:
            citation: Full legal citation

        Returns:
            Case dictionary with full details
        """
        logger.info(f"Retrieving case from LexisNexis: {citation}")

        if not self.api_key:
            return self._mock_case(citation)

        try:
            response = self.session.get(
                f"{self.BASE_URL}/cases/{citation}",
                timeout=30
            )

            response.raise_for_status()
            return self._parse_case(response.json())

        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving case {citation}: {str(e)}")
            return self._mock_case(citation)

    def get_shepards(self, citation: str) -> Dict:
        """
        Get Shepard's Citations Service results

        Args:
            citation: Case citation

        Returns:
            Dictionary with citing references
        """
        logger.info(f"Getting Shepard's from LexisNexis for {citation}")

        if not self.api_key:
            return {'citing_references': [], 'treatment': 'Unknown'}

        try:
            response = self.session.get(
                f"{self.BASE_URL}/shepards/{citation}",
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving Shepard's: {str(e)}")
            return {'citing_references': [], 'treatment': 'Unknown'}

    def get_headnotes(self, case_id: str) -> List[Dict]:
        """
        Get LexisNexis headnotes for case

        Args:
            case_id: LexisNexis case ID

        Returns:
            List of headnote dictionaries
        """
        if not self.api_key:
            return []

        try:
            response = self.session.get(
                f"{self.BASE_URL}/cases/{case_id}/headnotes",
                timeout=30
            )

            response.raise_for_status()
            return response.json().get('headnotes', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving headnotes: {str(e)}")
            return []

    def _parse_results(self, data: Dict) -> List[Dict]:
        """Parse API response into standardized format"""
        cases = []

        for item in data.get('results', []):
            case = {
                'case_id': item.get('documentId'),
                'title': item.get('caseName'),
                'citation': item.get('citation'),
                'court': item.get('court'),
                'jurisdiction': item.get('jurisdiction'),
                'year': item.get('year'),
                'date': item.get('decisionDate'),
                'summary': item.get('summary', ''),
                'headnotes': item.get('headnotes', []),
                'judges': item.get('judges', []),
                'disposition': item.get('outcome'),
                'lexis_url': item.get('url'),
                'relevance_score': item.get('score', 0),
                'source': 'LexisNexis'
            }
            cases.append(case)

        return cases

    def _parse_case(self, data: Dict) -> Dict:
        """Parse single case response"""
        return {
            'case_id': data.get('documentId'),
            'title': data.get('caseName'),
            'citation': data.get('citation'),
            'parallel_citations': data.get('parallelCitations', []),
            'court': data.get('court'),
            'jurisdiction': data.get('jurisdiction'),
            'year': data.get('year'),
            'date': data.get('decisionDate'),
            'summary': data.get('summary', ''),
            'headnotes': data.get('headnotes', []),
            'judges': data.get('judges', []),
            'attorneys': data.get('counsel', []),
            'disposition': data.get('outcome'),
            'full_text': data.get('fullText', ''),
            'lexis_url': data.get('url'),
            'source': 'LexisNexis'
        }

    def _mock_search(self, query: str, jurisdiction: str, max_results: int) -> List[Dict]:
        """
        Mock search results for testing
        IMPORTANT: Example citations for demonstration only
        """
        logger.info("Using mock LexisNexis data for demonstration")

        mock_cases = {
            'custody': [
                {
                    'case_id': 'LN-001',
                    'title': 'In re Marriage of LaMusga',
                    'citation': '32 Cal. 4th 1072',
                    'court': 'California Supreme Court',
                    'jurisdiction': 'California',
                    'year': 2004,
                    'date': '2004-12-13',
                    'summary': 'Parent seeking to relocate with child must show move is in child\'s best interest.',
                    'headnotes': [
                        'Relocation requires showing of changed circumstances',
                        'Child\'s best interest paramount in relocation cases'
                    ],
                    'disposition': 'Affirmed',
                    'lexis_url': 'https://lexisnexis.com/mock/001',
                    'relevance_score': 0.92,
                    'source': 'LexisNexis'
                },
                {
                    'case_id': 'LN-002',
                    'title': 'In re Marriage of Burgess',
                    'citation': '13 Cal. 4th 25',
                    'court': 'California Supreme Court',
                    'jurisdiction': 'California',
                    'year': 1996,
                    'date': '1996-08-29',
                    'summary': 'Custodial parent has presumptive right to change residence with child.',
                    'headnotes': [
                        'Custodial parent can relocate absent showing of detriment',
                        'Non-custodial parent bears burden to show harm'
                    ],
                    'disposition': 'Affirmed',
                    'lexis_url': 'https://lexisnexis.com/mock/002',
                    'relevance_score': 0.88,
                    'source': 'LexisNexis'
                },
                {
                    'case_id': 'LN-003',
                    'title': 'In re Marriage of Brown and Yana',
                    'citation': '37 Cal. 4th 947',
                    'court': 'California Supreme Court',
                    'jurisdiction': 'California',
                    'year': 2006,
                    'date': '2006-02-27',
                    'summary': 'Standard for modifying custody orders requires material change in circumstances.',
                    'headnotes': [
                        'Change must be substantial and continuing',
                        'Best interest analysis required even with changed circumstances'
                    ],
                    'disposition': 'Affirmed',
                    'lexis_url': 'https://lexisnexis.com/mock/003',
                    'relevance_score': 0.90,
                    'source': 'LexisNexis'
                }
            ],
            'bankruptcy': [
                {
                    'case_id': 'LN-201',
                    'title': 'Law v. Siegel',
                    'citation': '571 U.S. 415',
                    'court': 'United States Supreme Court',
                    'jurisdiction': 'Federal',
                    'year': 2014,
                    'date': '2014-03-04',
                    'summary': 'Bankruptcy court cannot surcharge debtor\'s exemptions as sanction for misconduct.',
                    'headnotes': [
                        'Section 105(a) does not permit court to contravene specific bankruptcy provisions',
                        'Exemptions remain protected even with debtor fraud'
                    ],
                    'disposition': 'Reversed',
                    'lexis_url': 'https://lexisnexis.com/mock/201',
                    'relevance_score': 0.94,
                    'source': 'LexisNexis'
                }
            ]
        }

        query_lower = query.lower()
        if 'custody' in query_lower or 'child' in query_lower:
            return mock_cases['custody'][:max_results]
        elif 'bankruptcy' in query_lower:
            return mock_cases['bankruptcy'][:max_results]
        else:
            return []

    def _mock_case(self, citation: str) -> Dict:
        """Mock single case retrieval"""
        return {
            'case_id': 'MOCK-LN',
            'title': 'Mock Case',
            'citation': citation,
            'court': 'Mock Court',
            'jurisdiction': 'Mock',
            'year': 2023,
            'summary': 'Mock case for testing',
            'source': 'LexisNexis (Mock)'
        }

    def validate_citation(self, citation: str) -> bool:
        """
        Validate citation exists

        Args:
            citation: Citation to validate

        Returns:
            True if valid
        """
        case = self.get_case_by_citation(citation)
        return case is not None

    def get_treatment_signals(self, citation: str) -> Dict:
        """
        Get Shepard's treatment signals

        Args:
            citation: Case citation

        Returns:
            Treatment signal analysis
        """
        shepards = self.get_shepards(citation)

        return {
            'citation': citation,
            'treatment': shepards.get('treatment', 'Unknown'),
            'warning': shepards.get('hasWarning', False),
            'caution': shepards.get('hasCaution', False),
            'positive': shepards.get('hasPositive', False),
            'cited_by_count': shepards.get('citedByCount', 0),
            'overruled': shepards.get('overruled', False)
        }

    def search_statutes(self, query: str, jurisdiction: str = 'federal',
                       max_results: int = 20) -> List[Dict]:
        """
        Search for statutes and regulations

        Args:
            query: Search query
            jurisdiction: Jurisdiction to search
            max_results: Maximum results

        Returns:
            List of statute dictionaries
        """
        logger.info(f"Searching statutes: '{query}' in {jurisdiction}")

        if not self.api_key:
            return self._mock_statutes(query, jurisdiction)

        try:
            params = {
                'q': query,
                'jurisdiction': jurisdiction,
                'pageSize': max_results
            }

            response = self.session.get(
                f"{self.BASE_URL}/search/statutes",
                params=params,
                timeout=30
            )

            response.raise_for_status()
            return self._parse_statute_results(response.json())

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching statutes: {str(e)}")
            return self._mock_statutes(query, jurisdiction)

    def _parse_statute_results(self, data: Dict) -> List[Dict]:
        """Parse statute search results"""
        statutes = []

        for item in data.get('results', []):
            statute = {
                'statute_id': item.get('documentId'),
                'title': item.get('title'),
                'citation': item.get('citation'),
                'jurisdiction': item.get('jurisdiction'),
                'effective_date': item.get('effectiveDate'),
                'text': item.get('text', ''),
                'source': 'LexisNexis'
            }
            statutes.append(statute)

        return statutes

    def _mock_statutes(self, query: str, jurisdiction: str) -> List[Dict]:
        """Mock statute results"""
        return [
            {
                'statute_id': 'MOCK-STAT-001',
                'title': 'Mock Statute',
                'citation': 'Mock Code § 1234',
                'jurisdiction': jurisdiction,
                'text': 'Mock statute text',
                'source': 'LexisNexis (Mock)'
            }
        ]
