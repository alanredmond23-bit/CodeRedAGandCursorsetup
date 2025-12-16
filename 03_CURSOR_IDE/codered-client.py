#!/usr/bin/env python3
"""
CodeRed Supabase Client
Handles all database operations for Cursor IDE integration
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from supabase import create_client, Client

class CodeRedClient:
    """Client for CodeRed Supabase database operations"""

    def __init__(self):
        """Initialize Supabase client with credentials from environment"""
        self.url = os.environ.get('SUPABASE_URL')
        self.key = os.environ.get('SUPABASE_SERVICE_KEY')

        if not self.url or not self.key:
            raise ValueError(
                "Missing credentials. Set SUPABASE_URL and SUPABASE_SERVICE_KEY "
                "in environment or .env.local file"
            )

        self.client: Client = create_client(self.url, self.key)

    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try to query agents table
            response = self.client.table('codered.agents').select('id').limit(1).execute()
            print(f"✅ Connection successful! Found {len(response.data)} agents")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def log_agent_run(
        self,
        agent_id: str,
        task_id: Optional[str],
        case_id: str,
        attorney_id: str,
        zone_access: str,
        query_text: str,
        response_text: str,
        approx_cost_usd: float,
        tokens_used: int
    ) -> Dict[str, Any]:
        """
        Log an agent run to the database

        Args:
            agent_id: Agent role (architect, code, test, review, evidence, cynic)
            task_id: Associated task ID (optional)
            case_id: Case identifier
            attorney_id: Attorney making the query
            zone_access: Zone level (RED, YELLOW, GREEN)
            query_text: User's query
            response_text: Agent's response
            approx_cost_usd: Estimated cost
            tokens_used: Number of tokens consumed

        Returns:
            Dictionary with run_id and status
        """
        try:
            data = {
                'agent_id': agent_id,
                'task_id': task_id,
                'case_id': case_id,
                'attorney_id': attorney_id,
                'zone_access': zone_access,
                'query_text': query_text,
                'response_text': response_text[:5000],  # Truncate if too long
                'approx_cost_usd': approx_cost_usd,
                'tokens_used': tokens_used,
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('codered.agent_runs').insert(data).execute()

            return {
                'run_id': response.data[0]['id'],
                'status': 'success',
                'cost_usd': approx_cost_usd
            }
        except Exception as e:
            print(f"❌ Failed to log agent run: {e}")
            return {
                'run_id': None,
                'status': 'error',
                'error': str(e)
            }

    def query_embeddings(
        self,
        query: str,
        case_id: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Query RAG embeddings for relevant documents

        Args:
            query: Search query
            case_id: Case to search within
            top_k: Number of results to return
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of relevant documents with similarity scores
        """
        try:
            # Call search_embeddings function
            response = self.client.rpc(
                'search_embeddings',
                {
                    'query_text': query,
                    'case_filter': case_id,
                    'match_count': top_k,
                    'similarity_threshold': threshold
                }
            ).execute()

            return response.data
        except Exception as e:
            print(f"❌ Failed to query embeddings: {e}")
            return []

    def ingest_document(
        self,
        title: str,
        content: str,
        source_path: str,
        case_id: str,
        zone: str = 'YELLOW'
    ) -> Dict[str, Any]:
        """
        Ingest a document into the RAG database

        Args:
            title: Document title
            content: Full text content
            source_path: File path or URL
            case_id: Case identifier
            zone: Zone classification (RED, YELLOW, GREEN)

        Returns:
            Dictionary with document_id and status
        """
        try:
            response = self.client.rpc(
                'ingest_document',
                {
                    'doc_title': title,
                    'doc_content': content,
                    'doc_source': source_path,
                    'doc_case_id': case_id,
                    'doc_zone': zone
                }
            ).execute()

            return {
                'document_id': response.data,
                'status': 'success'
            }
        except Exception as e:
            print(f"❌ Failed to ingest document: {e}")
            return {
                'document_id': None,
                'status': 'error',
                'error': str(e)
            }

    def get_case_metadata(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific case

        Args:
            case_id: Case identifier

        Returns:
            Case metadata dictionary or None
        """
        try:
            response = self.client.table('codered.cases') \
                .select('*') \
                .eq('case_id', case_id) \
                .single() \
                .execute()

            return response.data
        except Exception as e:
            print(f"❌ Failed to get case metadata: {e}")
            return None

    def track_cost(
        self,
        agent_id: str,
        case_id: str,
        attorney_id: str,
        cost_usd: float,
        description: str
    ) -> Dict[str, Any]:
        """
        Track a cost entry

        Args:
            agent_id: Agent that incurred the cost
            case_id: Associated case
            attorney_id: Attorney responsible
            cost_usd: Cost amount
            description: What the cost was for

        Returns:
            Dictionary with cost_id and status
        """
        try:
            data = {
                'agent_id': agent_id,
                'case_id': case_id,
                'attorney_id': attorney_id,
                'cost_usd': cost_usd,
                'description': description,
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('codered.cost_tracking').insert(data).execute()

            return {
                'cost_id': response.data[0]['id'],
                'status': 'success'
            }
        except Exception as e:
            print(f"❌ Failed to track cost: {e}")
            return {
                'cost_id': None,
                'status': 'error',
                'error': str(e)
            }

    def get_costs_today(self, attorney_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get today's costs, optionally filtered by attorney

        Args:
            attorney_id: Optional attorney filter

        Returns:
            List of cost records
        """
        try:
            query = self.client.table('codered.cost_tracking') \
                .select('*') \
                .gte('created_at', datetime.utcnow().date().isoformat())

            if attorney_id:
                query = query.eq('attorney_id', attorney_id)

            response = query.execute()
            return response.data
        except Exception as e:
            print(f"❌ Failed to get costs: {e}")
            return []

    def flag_privilege(
        self,
        document_id: str,
        confidence: float,
        keywords_found: List[str],
        recommendation: str
    ) -> Dict[str, Any]:
        """
        Flag a document as potentially privileged

        Args:
            document_id: Document to flag
            confidence: Privilege confidence score (0.0-1.0)
            keywords_found: List of privilege keywords detected
            recommendation: Recommended zone (RED, YELLOW, GREEN)

        Returns:
            Dictionary with flag_id and status
        """
        try:
            data = {
                'document_id': document_id,
                'confidence': confidence,
                'keywords_found': keywords_found,
                'recommendation': recommendation,
                'flagged_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('codered.privilege_flags').insert(data).execute()

            return {
                'flag_id': response.data[0]['id'],
                'status': 'success'
            }
        except Exception as e:
            print(f"❌ Failed to flag privilege: {e}")
            return {
                'flag_id': None,
                'status': 'error',
                'error': str(e)
            }


def main():
    """Command-line interface for testing"""
    if len(sys.argv) < 2:
        print("Usage: python codered-client.py <command>")
        print("Commands: test, log, query, ingest, costs")
        sys.exit(1)

    command = sys.argv[1]
    client = CodeRedClient()

    if command == 'test':
        # Test connection
        success = client.test_connection()
        sys.exit(0 if success else 1)

    elif command == 'log':
        # Example: Log an agent run
        result = client.log_agent_run(
            agent_id='architect',
            task_id=None,
            case_id='CUSTODY-2024-001',
            attorney_id='john_doe',
            zone_access='YELLOW',
            query_text='What is the case strength?',
            response_text='Based on the evidence...',
            approx_cost_usd=3.50,
            tokens_used=2500
        )
        print(json.dumps(result, indent=2))

    elif command == 'query':
        # Example: Query embeddings
        results = client.query_embeddings(
            query='timeline March 2024',
            case_id='CUSTODY-2024-001',
            top_k=5
        )
        print(json.dumps(results, indent=2))

    elif command == 'ingest':
        # Example: Ingest document
        result = client.ingest_document(
            title='Email: Smith to Jones',
            content='This is the email content...',
            source_path='/cases/CUSTODY-2024-001/emails/email_001.pdf',
            case_id='CUSTODY-2024-001',
            zone='YELLOW'
        )
        print(json.dumps(result, indent=2))

    elif command == 'costs':
        # Get today's costs
        costs = client.get_costs_today()
        total = sum(c['cost_usd'] for c in costs)
        print(f"Today's costs: ${total:.2f}")
        print(json.dumps(costs, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
