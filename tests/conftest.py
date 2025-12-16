"""
Pytest Configuration and Shared Fixtures
Provides test data, mock clients, and reusable components
"""

import pytest
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch
import json

# Test Configuration
TEST_CONFIG = {
    'supabase_url': 'https://test.supabase.co',
    'supabase_key': 'test_key_12345',
    'redis_host': 'localhost',
    'redis_port': 6379,
    'westlaw_api_key': 'test_westlaw_key',
    'lexisnexis_api_key': 'test_lexis_key',
    'gmail_credentials': 'test_gmail_creds',
    'slack_token': 'test_slack_token',
    'github_token': 'test_github_token',
}

# Legal Test Data
LEGAL_TEST_CASES = {
    'custody': {
        'case_id': 'CUSTODY_001',
        'case_type': 'custody',
        'attorney': 'john_doe',
        'documents': 150,
        'status': 'active',
        'zone': 'red',  # Privileged
    },
    'feds': {
        'case_id': 'FEDS_002',
        'case_type': 'federal_criminal',
        'attorney': 'jane_smith',
        'documents': 5000,
        'status': 'discovery',
        'zone': 'red',
    },
    'bankruptcy': {
        'case_id': 'BANK_003',
        'case_type': 'bankruptcy',
        'attorney': 'bob_jones',
        'documents': 800,
        'status': 'filing',
        'zone': 'yellow',
    },
    'malpractice': {
        'case_id': 'MAL_004',
        'case_type': 'legal_malpractice',
        'attorney': 'alice_williams',
        'documents': 300,
        'status': 'investigation',
        'zone': 'red',
    },
}

# Sample Documents for Discovery
SAMPLE_DOCUMENTS = [
    {
        'doc_id': 'EMAIL_001',
        'type': 'email',
        'from': 'opposing@counsel.com',
        'to': 'attorney@client.com',
        'subject': 'RE: Custody Agreement',
        'date': '2025-01-15',
        'content': 'Regarding custody arrangement...',
        'privileged': True,
        'keywords': ['attorney', 'privileged', 'confidential'],
        'relevance_score': 0.95,
    },
    {
        'doc_id': 'CONTRACT_001',
        'type': 'contract',
        'parties': ['Client Corp', 'Vendor LLC'],
        'date': '2024-06-20',
        'content': 'Service agreement for...',
        'privileged': False,
        'keywords': ['payment', 'services', 'breach'],
        'relevance_score': 0.87,
    },
    {
        'doc_id': 'DEPOSITION_001',
        'type': 'deposition',
        'witness': 'John Witness',
        'date': '2025-02-10',
        'content': 'Q: Did you observe... A: Yes, I saw...',
        'privileged': False,
        'keywords': ['testimony', 'observation', 'timeline'],
        'relevance_score': 0.92,
    },
]

# Cost Tracking Test Data
COST_TEST_DATA = {
    'discovery_bot': {
        'model': 'gpt-4o',
        'cost_per_1k_docs': 2.50,
        'expected_accuracy': 0.95,
    },
    'coordinator_bot': {
        'model': 'gpt-4o-mini',
        'cost_per_action': 1.00,
        'expected_accuracy': 0.90,
    },
    'strategy_bot': {
        'model': 'gpt-4o',
        'cost_per_query': 2.50,
        'expected_accuracy': 0.93,
    },
    'evidence_bot': {
        'model': 'gpt-4o',
        'cost_per_analysis': 3.50,
        'expected_accuracy': 0.94,
    },
    'case_analysis_bot': {
        'model': 'claude-3-opus',
        'cost_per_assessment': 4.50,
        'expected_accuracy': 0.96,
    },
}


@pytest.fixture
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG.copy()


@pytest.fixture
def legal_test_cases():
    """Provide legal test case data"""
    return LEGAL_TEST_CASES.copy()


@pytest.fixture
def sample_documents():
    """Provide sample discovery documents"""
    return SAMPLE_DOCUMENTS.copy()


@pytest.fixture
def cost_test_data():
    """Provide cost tracking test data"""
    return COST_TEST_DATA.copy()


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    mock_client = MagicMock()

    # Mock table operations
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value = {'data': [{'id': '123'}], 'error': None}
    mock_table.select.return_value.execute.return_value = {'data': [], 'error': None}
    mock_table.update.return_value.eq.return_value.execute.return_value = {'data': [{'id': '123'}], 'error': None}
    mock_table.delete.return_value.eq.return_value.execute.return_value = {'data': [], 'error': None}

    mock_client.table.return_value = mock_table
    mock_client.from_.return_value = mock_table

    return mock_client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.lpush.return_value = 1
    mock_redis.brpop.return_value = None
    mock_redis.publish.return_value = 1

    return mock_redis


@pytest.fixture
def mock_westlaw_api():
    """Mock Westlaw API for legal research"""
    mock_api = MagicMock()

    mock_api.search_cases.return_value = {
        'results': [
            {
                'citation': 'Smith v. Jones, 123 F.3d 456 (9th Cir. 2023)',
                'court': 'Ninth Circuit',
                'year': 2023,
                'relevance': 0.92,
                'summary': 'Custody case establishing parent rights...',
            }
        ],
        'total': 1,
    }

    return mock_api


@pytest.fixture
def mock_lexisnexis_api():
    """Mock LexisNexis API for legal research"""
    mock_api = MagicMock()

    mock_api.search.return_value = {
        'documents': [
            {
                'title': 'Federal Criminal Procedure Standard',
                'cite': '18 U.S.C. § 3501',
                'relevance': 0.88,
                'text': 'Requirements for criminal discovery...',
            }
        ],
        'count': 1,
    }

    return mock_api


@pytest.fixture
def mock_gmail_api():
    """Mock Gmail API for discovery"""
    mock_api = MagicMock()

    mock_api.users().messages().list.return_value.execute.return_value = {
        'messages': [
            {'id': 'msg_001', 'threadId': 'thread_001'}
        ]
    }

    mock_api.users().messages().get.return_value.execute.return_value = {
        'id': 'msg_001',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'attorney@client.com'},
                {'name': 'Subject', 'value': 'Privileged Communication'},
            ],
            'body': {'data': 'TWVzc2FnZSBjb250ZW50'}  # Base64 encoded
        }
    }

    return mock_api


@pytest.fixture
def mock_llm_client():
    """Mock LLM client (OpenAI/Anthropic)"""
    mock_llm = MagicMock()

    mock_llm.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"classification": "email", "privileged": true, "entities": ["attorney", "client"], "summary": "Legal communication regarding case strategy"}'
                )
            )
        ],
        usage=MagicMock(
            prompt_tokens=500,
            completion_tokens=150,
            total_tokens=650
        )
    )

    return mock_llm


@pytest.fixture
async def mock_agent_communicator():
    """Mock inter-agent communicator"""
    mock_comm = AsyncMock()

    mock_comm.send_message.return_value = True
    mock_comm.receive_message.return_value = None
    mock_comm.get_task_state.return_value = {'status': 'pending'}
    mock_comm.set_task_state.return_value = True

    return mock_comm


@pytest.fixture
def privilege_keywords():
    """Attorney-client privilege keywords"""
    return [
        'attorney',
        'lawyer',
        'legal counsel',
        'privileged',
        'confidential',
        'attorney-client',
        'work product',
        'in confidence',
        'legal advice',
    ]


@pytest.fixture
def expected_costs():
    """Expected cost ranges for validation"""
    return {
        'discovery_per_1k_docs': {'min': 2.0, 'max': 3.0, 'tolerance': 0.1},
        'coordinator_per_action': {'min': 0.80, 'max': 1.20, 'tolerance': 0.1},
        'strategy_per_query': {'min': 2.0, 'max': 3.0, 'tolerance': 0.1},
        'evidence_per_analysis': {'min': 3.0, 'max': 4.0, 'tolerance': 0.1},
        'case_analysis_per_assessment': {'min': 3.0, 'max': 5.0, 'tolerance': 0.1},
    }


@pytest.fixture
def performance_thresholds():
    """Performance requirements"""
    return {
        'max_processing_time_per_doc': 2.0,  # seconds
        'min_docs_per_day': 1000,
        'max_error_rate': 0.05,  # 5%
        'min_accuracy': 0.90,  # 90%
        'max_sync_latency': 5.0,  # seconds
    }


@pytest.fixture
def audit_trail_requirements():
    """Audit trail validation requirements"""
    return {
        'required_fields': [
            'timestamp',
            'agent_id',
            'action',
            'case_id',
            'user_id',
            'zone',
            'privileged_accessed',
            'cost_usd',
            'status',
        ],
        'retention_days': 2555,  # 7 years for legal compliance
        'immutable': True,
    }


@pytest.fixture
def zone_restrictions():
    """Zone-based access restrictions"""
    return {
        'red': {
            'requires_approval': True,
            'agents_allowed': ['discovery_bot', 'strategy_bot', 'evidence_bot', 'case_analysis_bot'],
            'logging_level': 'full',
            'privilege_check': 'mandatory',
        },
        'yellow': {
            'requires_approval': True,
            'agents_allowed': ['coordinator_bot', 'case_analysis_bot'],
            'logging_level': 'standard',
            'privilege_check': 'recommended',
        },
        'green': {
            'requires_approval': False,
            'agents_allowed': 'all',
            'logging_level': 'minimal',
            'privilege_check': 'none',
        },
    }


@pytest.fixture
def sync_test_scenarios():
    """Bidirectional sync test scenarios"""
    return [
        {
            'name': 'claude_to_antigravity',
            'source': 'claude-code-terminal',
            'target': 'antigravity',
            'operation': 'create_task',
            'expected_sync_time': 3.0,
        },
        {
            'name': 'antigravity_to_claude',
            'source': 'antigravity',
            'target': 'claude-code-terminal',
            'operation': 'update_status',
            'expected_sync_time': 3.0,
        },
        {
            'name': 'cursor_to_supabase',
            'source': 'cursor',
            'target': 'supabase',
            'operation': 'save_context',
            'expected_sync_time': 2.0,
        },
        {
            'name': 'conflict_resolution',
            'source': 'both',
            'target': 'both',
            'operation': 'concurrent_update',
            'expected_resolution': 'last_write_wins',
        },
    ]


# Helper Functions

def create_mock_discovery_result(doc_count: int = 10, privileged_ratio: float = 0.2) -> List[Dict]:
    """Create mock discovery results"""
    results = []
    for i in range(doc_count):
        results.append({
            'doc_id': f'DOC_{i:04d}',
            'type': 'email' if i % 3 == 0 else 'document',
            'privileged': i < int(doc_count * privileged_ratio),
            'relevance_score': 0.5 + (0.5 * (i / doc_count)),
            'extracted_entities': ['person_A', 'date_B', 'amount_C'],
            'summary': f'Document {i} summary...',
        })
    return results


def create_mock_cost_record(agent: str, operation: str, tokens: int, cost: float) -> Dict:
    """Create mock cost tracking record"""
    return {
        'id': f'cost_{datetime.now().timestamp()}',
        'timestamp': datetime.now().isoformat(),
        'agent_id': agent,
        'operation': operation,
        'tokens_used': tokens,
        'cost_usd': cost,
        'case_id': 'TEST_CASE_001',
        'attorney': 'test_attorney',
    }


def validate_privilege_detection(document: Dict, keywords: List[str]) -> bool:
    """Validate privilege detection accuracy"""
    content = document.get('content', '') + ' ' + document.get('subject', '')
    content_lower = content.lower()

    has_keywords = any(kw.lower() in content_lower for kw in keywords)

    # Should be marked privileged if keywords present
    return document.get('privileged', False) == has_keywords


def validate_cost_accuracy(actual: float, expected: float, tolerance: float = 0.001) -> bool:
    """Validate cost within tolerance (0.1%)"""
    return abs(actual - expected) <= (expected * tolerance)


async def wait_for_sync(check_func, timeout: float = 10.0, interval: float = 0.5) -> bool:
    """Wait for sync operation to complete"""
    elapsed = 0
    while elapsed < timeout:
        if await check_func():
            return True
        await asyncio.sleep(interval)
        elapsed += interval
    return False
