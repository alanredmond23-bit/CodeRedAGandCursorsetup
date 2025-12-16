"""
Supabase MCP Server
Supabase database integration for CodeRed system
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from supabase import create_client, Client
from mcp_auth_handler import get_auth_handler
from mcp_cache import get_cache, cached_mcp_call
from mcp_logging import get_mcp_logger

class SupabaseMCPServer:
    """MCP Server for Supabase database operations"""

    def __init__(self):
        self.auth_handler = get_auth_handler()
        self.cache = get_cache()
        self.logger = get_mcp_logger()
        self.client: Optional[Client] = None
        self._initialize()

    def _initialize(self):
        """Initialize Supabase connection"""
        try:
            credentials = self.auth_handler.get_supabase_credentials()
            self.client = create_client(
                credentials['url'],
                credentials['service_key']
            )
            self.logger.log_auth_event('supabase', 'initialization', True)
        except Exception as e:
            self.logger.log_auth_event('supabase', 'initialization', False, str(e))
            raise

    def _log_query(self, table: str, operation: str, params: Dict = None):
        """Log database query"""
        self.logger.log_api_call(
            service='supabase',
            endpoint=f'{table}/{operation}',
            method='POST',
            params=params,
            response_status=200,
            response_time_ms=0
        )

    @cached_mcp_call('supabase', ttl=300)  # 5 minute cache
    def query_table(self,
                    table: str,
                    filters: Dict = None,
                    select: str = '*',
                    order_by: str = None,
                    limit: int = 100) -> Dict[str, Any]:
        """
        Query a Supabase table

        Args:
            table: Table name
            filters: Filter conditions (e.g., {'status': 'active'})
            select: Columns to select
            order_by: Column to order by
            limit: Maximum rows to return

        Returns:
            Query results
        """
        try:
            start_time = time.time()

            query = self.client.table(table).select(select)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            # Apply ordering
            if order_by:
                query = query.order(order_by)

            # Apply limit
            query = query.limit(limit)

            result = query.execute()

            response_time = (time.time() - start_time) * 1000

            self.logger.log_api_call(
                service='supabase',
                endpoint=f'{table}/select',
                method='GET',
                params=filters,
                response_status=200,
                response_time_ms=response_time
            )

            return {
                'table': table,
                'count': len(result.data),
                'data': result.data,
                'query_time_ms': round(response_time, 2)
            }

        except Exception as e:
            self.logger.log_error('supabase', 'query_error', str(e), query=table)
            return {'error': str(e), 'table': table}

    def insert_record(self, table: str, data: Dict) -> Dict[str, Any]:
        """
        Insert a record into a table

        Args:
            table: Table name
            data: Record data

        Returns:
            Inserted record
        """
        try:
            result = self.client.table(table).insert(data).execute()

            self._log_query(table, 'insert', {'record_count': 1})

            return {
                'table': table,
                'success': True,
                'data': result.data,
                'inserted_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.log_error('supabase', 'insert_error', str(e), query=table)
            return {'error': str(e), 'table': table, 'success': False}

    def update_record(self,
                     table: str,
                     filters: Dict,
                     updates: Dict) -> Dict[str, Any]:
        """
        Update records in a table

        Args:
            table: Table name
            filters: Filter conditions
            updates: Update data

        Returns:
            Updated records
        """
        try:
            query = self.client.table(table).update(updates)

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.execute()

            self._log_query(table, 'update', {'filters': filters, 'record_count': len(result.data)})

            return {
                'table': table,
                'success': True,
                'updated_count': len(result.data),
                'data': result.data,
                'updated_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.log_error('supabase', 'update_error', str(e), query=table)
            return {'error': str(e), 'table': table, 'success': False}

    def delete_record(self, table: str, filters: Dict) -> Dict[str, Any]:
        """
        Delete records from a table

        Args:
            table: Table name
            filters: Filter conditions

        Returns:
            Deletion result
        """
        try:
            query = self.client.table(table).delete()

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.execute()

            self._log_query(table, 'delete', {'filters': filters, 'record_count': len(result.data)})

            return {
                'table': table,
                'success': True,
                'deleted_count': len(result.data),
                'deleted_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.log_error('supabase', 'delete_error', str(e), query=table)
            return {'error': str(e), 'table': table, 'success': False}

    @cached_mcp_call('supabase', ttl=600)
    def get_cases(self,
                  status: str = None,
                  assigned_to: str = None,
                  limit: int = 50) -> Dict[str, Any]:
        """
        Get legal cases from database

        Args:
            status: Filter by status
            assigned_to: Filter by assigned attorney
            limit: Maximum cases to return

        Returns:
            Case list
        """
        filters = {}
        if status:
            filters['status'] = status
        if assigned_to:
            filters['assigned_to'] = assigned_to

        return self.query_table('cases', filters=filters, limit=limit, order_by='created_at')

    @cached_mcp_call('supabase', ttl=600)
    def get_documents(self,
                     case_id: str = None,
                     document_type: str = None,
                     limit: int = 100) -> Dict[str, Any]:
        """
        Get legal documents from database

        Args:
            case_id: Filter by case ID
            document_type: Filter by document type
            limit: Maximum documents to return

        Returns:
            Document list
        """
        filters = {}
        if case_id:
            filters['case_id'] = case_id
        if document_type:
            filters['document_type'] = document_type

        return self.query_table('documents', filters=filters, limit=limit, order_by='created_at')

    def log_research_query(self,
                          service: str,
                          query: str,
                          results_count: int,
                          user: str = None) -> Dict[str, Any]:
        """
        Log a legal research query to database

        Args:
            service: Research service (westlaw, lexisnexis)
            query: Search query
            results_count: Number of results
            user: User who made the query

        Returns:
            Logged query record
        """
        data = {
            'service': service,
            'query': query,
            'results_count': results_count,
            'user': user or 'system',
            'timestamp': datetime.now().isoformat()
        }

        return self.insert_record('research_queries', data)

    def save_discovery_item(self,
                           item_type: str,
                           source: str,
                           item_id: str,
                           content: Dict,
                           privileged: bool = False,
                           case_id: str = None) -> Dict[str, Any]:
        """
        Save discovered item (email, message) to database

        Args:
            item_type: Type ('email', 'slack_message')
            source: Source service
            item_id: Original item ID
            content: Item content
            privileged: Whether item is privileged
            case_id: Associated case ID

        Returns:
            Saved item record
        """
        data = {
            'item_type': item_type,
            'source': source,
            'item_id': item_id,
            'content': json.dumps(content),
            'privileged': privileged,
            'case_id': case_id,
            'discovered_at': datetime.now().isoformat()
        }

        result = self.insert_record('discovery_items', data)

        # Log discovery save
        if result.get('success'):
            self.logger.log_discovery_action(
                service='supabase',
                action_type='save_discovery_item',
                items_processed=1,
                items_flagged=1 if privileged else 0,
                query=item_id
            )

        return result

    @cached_mcp_call('supabase', ttl=300)
    def get_discovery_items(self,
                           case_id: str = None,
                           privileged: bool = None,
                           item_type: str = None,
                           limit: int = 100) -> Dict[str, Any]:
        """
        Retrieve discovery items from database

        Args:
            case_id: Filter by case ID
            privileged: Filter by privilege status
            item_type: Filter by item type
            limit: Maximum items to return

        Returns:
            Discovery items
        """
        filters = {}
        if case_id:
            filters['case_id'] = case_id
        if privileged is not None:
            filters['privileged'] = privileged
        if item_type:
            filters['item_type'] = item_type

        result = self.query_table('discovery_items', filters=filters, limit=limit, order_by='discovered_at')

        # Parse JSON content
        if result.get('data'):
            for item in result['data']:
                if 'content' in item and isinstance(item['content'], str):
                    try:
                        item['content'] = json.loads(item['content'])
                    except:
                        pass

        return result

    def execute_sql(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """
        Execute raw SQL query

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        try:
            start_time = time.time()

            result = self.client.rpc('execute_sql', {'query': query, 'params': params or {}}).execute()

            response_time = (time.time() - start_time) * 1000

            self.logger.log_api_call(
                service='supabase',
                endpoint='execute_sql',
                method='POST',
                params={'query_length': len(query)},
                response_status=200,
                response_time_ms=response_time
            )

            return {
                'success': True,
                'data': result.data,
                'query_time_ms': round(response_time, 2)
            }

        except Exception as e:
            self.logger.log_error('supabase', 'sql_error', str(e), query=query[:100])
            return {'error': str(e), 'success': False}

    def get_api_status(self) -> Dict[str, Any]:
        """Check Supabase connection status"""
        try:
            # Try a simple query
            result = self.client.table('cases').select('id').limit(1).execute()

            return {
                'status': 'operational',
                'service': 'supabase',
                'connected': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'service': 'supabase',
                'connected': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def create_supabase_mcp():
    """Factory function to create Supabase MCP server"""
    return SupabaseMCPServer()


if __name__ == '__main__':
    # Test the MCP server
    mcp = create_supabase_mcp()
    print("Supabase MCP Server initialized")
    print("\nChecking API status:")
    status = mcp.get_api_status()
    print(json.dumps(status, indent=2))
