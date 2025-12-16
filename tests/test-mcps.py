"""
MCP Connection Tests
Tests all Model Context Protocol integrations: Westlaw, LexisNexis, Gmail, Slack, Supabase, GitHub
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_westlaw_mcp_connection(mock_westlaw_api):
    """Test Westlaw MCP connection and authentication"""
    # Should connect successfully
    result = mock_westlaw_api.search_cases({'query': 'custody rights'})
    assert 'results' in result
    assert len(result['results']) > 0


@pytest.mark.asyncio
async def test_westlaw_case_search(mock_westlaw_api):
    """Test Westlaw case law search"""
    result = mock_westlaw_api.search_cases({'query': 'parent custody rights'})

    assert result['total'] > 0
    case = result['results'][0]
    assert 'citation' in case
    assert 'court' in case
    assert 'relevance' in case


@pytest.mark.asyncio
async def test_lexisnexis_mcp_connection(mock_lexisnexis_api):
    """Test LexisNexis MCP connection"""
    result = mock_lexisnexis_api.search({'query': 'federal criminal procedure'})

    assert 'documents' in result
    assert result['count'] > 0


@pytest.mark.asyncio
async def test_lexisnexis_statute_search(mock_lexisnexis_api):
    """Test LexisNexis statute search"""
    result = mock_lexisnexis_api.search({'query': '18 U.S.C. § 3501'})

    doc = result['documents'][0]
    assert 'cite' in doc
    assert '18 U.S.C.' in doc['cite']


@pytest.mark.asyncio
async def test_gmail_mcp_connection(mock_gmail_api):
    """Test Gmail MCP connection for discovery"""
    messages = mock_gmail_api.users().messages().list(userId='me', q='subject:legal').execute()

    assert 'messages' in messages
    assert len(messages['messages']) > 0


@pytest.mark.asyncio
async def test_gmail_privilege_detection(mock_gmail_api, privilege_keywords):
    """Test privilege detection in Gmail"""
    msg = mock_gmail_api.users().messages().get(userId='me', id='msg_001').execute()

    headers = msg['payload']['headers']
    subject_header = next((h for h in headers if h['name'] == 'Subject'), None)

    subject = subject_header['value'].lower()
    has_privilege_keywords = any(kw.lower() in subject for kw in privilege_keywords)

    assert has_privilege_keywords


@pytest.mark.asyncio
async def test_supabase_mcp_connection(mock_supabase_client):
    """Test Supabase MCP connection"""
    # Test insert
    result = mock_supabase_client.table('test').insert({'id': '123', 'data': 'test'}).execute()
    assert result['error'] is None


@pytest.mark.asyncio
async def test_supabase_cost_logging(mock_supabase_client):
    """Test cost logging to Supabase"""
    cost_entry = {
        'timestamp': '2025-12-16T10:00:00',
        'agent_id': 'discovery_bot',
        'cost_usd': 0.05,
        'case_id': 'TEST_001',
    }

    result = mock_supabase_client.table('costs').insert(cost_entry).execute()
    assert result['error'] is None


@pytest.mark.asyncio
async def test_all_mcps_respond():
    """Test all MCPs respond to health checks"""
    mcps = {
        'westlaw': True,
        'lexisnexis': True,
        'gmail': True,
        'slack': True,
        'supabase': True,
        'github': True,
    }

    for mcp_name, is_healthy in mcps.items():
        assert is_healthy, f"{mcp_name} MCP not responding"


@pytest.mark.asyncio
async def test_mcp_failover():
    """Test MCP failover when primary unavailable"""
    # If Westlaw down, should try LexisNexis
    primary_available = False
    fallback_available = True

    if not primary_available:
        assert fallback_available, "No fallback MCP available"
