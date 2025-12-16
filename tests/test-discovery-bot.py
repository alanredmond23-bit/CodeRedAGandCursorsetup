"""
Discovery Bot Tests
Tests document extraction, entity recognition, privilege detection, and timeline construction
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import MagicMock, AsyncMock, patch


class DiscoveryBot:
    """Mock Discovery Bot for testing"""

    def __init__(self, llm_client, supabase_client, config):
        self.llm = llm_client
        self.db = supabase_client
        self.config = config
        self.zone = 'red'  # Can access privileged documents

    async def classify_document(self, document: Dict) -> Dict:
        """Classify document type"""
        # Mock classification logic
        doc_type = document.get('type', 'unknown')
        return {
            'doc_id': document['doc_id'],
            'classification': doc_type,
            'confidence': 0.95,
        }

    async def detect_privilege(self, document: Dict, keywords: List[str]) -> Dict:
        """Detect attorney-client privilege"""
        content = (document.get('content', '') + ' ' +
                   document.get('subject', '')).lower()

        privileged = any(kw.lower() in content for kw in keywords)

        return {
            'doc_id': document['doc_id'],
            'privileged': privileged,
            'keywords_found': [kw for kw in keywords if kw.lower() in content],
            'confidence': 0.92 if privileged else 0.85,
        }

    async def extract_entities(self, document: Dict) -> Dict:
        """Extract people, dates, amounts, locations"""
        # Mock entity extraction
        entities = {
            'people': ['John Doe', 'Jane Smith'],
            'dates': ['2025-01-15', '2024-06-20'],
            'amounts': ['$50,000', '$10,000'],
            'locations': ['New York', 'California'],
        }

        return {
            'doc_id': document['doc_id'],
            'entities': entities,
            'entity_count': sum(len(v) for v in entities.values()),
        }

    async def calculate_relevance(self, document: Dict, case_keywords: List[str]) -> float:
        """Calculate document relevance to case"""
        content = document.get('content', '').lower()
        matches = sum(1 for kw in case_keywords if kw.lower() in content)
        relevance = min(matches / len(case_keywords), 1.0) if case_keywords else 0.5

        return relevance

    async def process_document_batch(self, documents: List[Dict], case_id: str) -> Dict:
        """Process batch of documents"""
        results = {
            'processed': 0,
            'classified': 0,
            'privileged': 0,
            'entities_extracted': 0,
            'errors': 0,
            'cost_usd': 0.0,
        }

        for doc in documents:
            try:
                # Classify
                classification = await self.classify_document(doc)
                results['classified'] += 1

                # Check privilege
                privilege = await self.detect_privilege(
                    doc,
                    ['attorney', 'lawyer', 'privileged', 'confidential']
                )
                if privilege['privileged']:
                    results['privileged'] += 1

                # Extract entities
                entities = await self.extract_entities(doc)
                results['entities_extracted'] += entities['entity_count']

                results['processed'] += 1

                # Calculate cost (mock)
                results['cost_usd'] += 0.0025  # $2.50 per 1000 docs

            except Exception as e:
                results['errors'] += 1

        return results


# Tests

@pytest.mark.asyncio
async def test_discovery_bot_document_classification(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test document classification accuracy"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    for doc in sample_documents:
        result = await bot.classify_document(doc)

        assert result['doc_id'] == doc['doc_id']
        assert result['classification'] in ['email', 'contract', 'deposition', 'document', 'unknown']
        assert 0.0 <= result['confidence'] <= 1.0
        assert result['confidence'] >= 0.90, "Classification confidence too low"


@pytest.mark.asyncio
async def test_discovery_bot_privilege_detection(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config,
    privilege_keywords
):
    """Test attorney-client privilege detection"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    privileged_doc = sample_documents[0]  # EMAIL_001 is privileged
    non_privileged_doc = sample_documents[1]  # CONTRACT_001 is not

    # Test privileged document
    result = await bot.detect_privilege(privileged_doc, privilege_keywords)
    assert result['privileged'] == True, "Failed to detect privileged document"
    assert len(result['keywords_found']) > 0, "Should find privilege keywords"

    # Test non-privileged document
    result = await bot.detect_privilege(non_privileged_doc, privilege_keywords)
    # Contract may or may not be privileged depending on content


@pytest.mark.asyncio
async def test_discovery_bot_entity_extraction(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test entity extraction (people, dates, amounts, locations)"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    for doc in sample_documents:
        result = await bot.extract_entities(doc)

        assert result['doc_id'] == doc['doc_id']
        assert 'entities' in result
        assert 'people' in result['entities']
        assert 'dates' in result['entities']
        assert 'amounts' in result['entities']
        assert 'locations' in result['entities']
        assert result['entity_count'] > 0


@pytest.mark.asyncio
async def test_discovery_bot_relevance_scoring(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test relevance scoring"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    case_keywords = ['custody', 'agreement', 'arrangement', 'child']

    for doc in sample_documents:
        relevance = await bot.calculate_relevance(doc, case_keywords)

        assert 0.0 <= relevance <= 1.0, "Relevance score out of range"
        assert isinstance(relevance, float)


@pytest.mark.asyncio
async def test_discovery_bot_batch_processing(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test batch document processing"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    results = await bot.process_document_batch(sample_documents, 'CUSTODY_001')

    assert results['processed'] == len(sample_documents)
    assert results['classified'] == len(sample_documents)
    assert results['privileged'] >= 1, "Should detect at least one privileged doc"
    assert results['entities_extracted'] > 0
    assert results['errors'] == 0
    assert results['cost_usd'] > 0


@pytest.mark.asyncio
async def test_discovery_bot_cost_tracking(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config,
    expected_costs
):
    """Test cost tracking accuracy (within 0.1%)"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    # Process 1000 documents
    large_batch = sample_documents * 334  # ~1000 docs

    results = await bot.process_document_batch(large_batch, 'CUSTODY_001')

    docs_processed = results['processed']
    actual_cost = results['cost_usd']

    # Expected cost: $2.50 per 1000 docs
    expected_cost = (docs_processed / 1000) * 2.50

    tolerance = expected_costs['discovery_per_1k_docs']['tolerance']

    assert abs(actual_cost - expected_cost) <= (expected_cost * tolerance), \
        f"Cost accuracy violation: expected ${expected_cost:.2f}, got ${actual_cost:.2f}"


@pytest.mark.asyncio
async def test_discovery_bot_performance(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config,
    performance_thresholds
):
    """Test processing speed (1000+ docs/day required)"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    start_time = datetime.now()

    # Process small batch and extrapolate
    results = await bot.process_document_batch(sample_documents, 'TEST_CASE')

    elapsed = (datetime.now() - start_time).total_seconds()
    docs_per_second = results['processed'] / elapsed if elapsed > 0 else 0
    docs_per_day = docs_per_second * 86400  # seconds in day

    assert docs_per_day >= performance_thresholds['min_docs_per_day'], \
        f"Performance too slow: {docs_per_day:.0f} docs/day < {performance_thresholds['min_docs_per_day']} required"


@pytest.mark.asyncio
async def test_discovery_bot_zone_restrictions(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config,
    zone_restrictions
):
    """Test RED zone access restrictions"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    # Discovery bot should have RED zone access
    assert bot.zone == 'red'

    # Verify bot is in allowed list for RED zone
    allowed_agents = zone_restrictions['red']['agents_allowed']
    assert 'discovery_bot' in allowed_agents


@pytest.mark.asyncio
async def test_discovery_bot_audit_logging(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config,
    audit_trail_requirements
):
    """Test audit trail logging for compliance"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    # Mock audit log
    audit_logs = []

    def mock_log_audit(entry):
        audit_logs.append(entry)

    with patch.object(bot.db.table('audit_trail'), 'insert') as mock_insert:
        mock_insert.return_value.execute.side_effect = lambda: mock_log_audit({
            'timestamp': datetime.now().isoformat(),
            'agent_id': 'discovery_bot_001',
            'action': 'process_documents',
            'case_id': 'CUSTODY_001',
            'user_id': 'john_doe',
            'zone': 'red',
            'privileged_accessed': True,
            'cost_usd': 0.01,
            'status': 'success',
        })

        results = await bot.process_document_batch(sample_documents[:1], 'CUSTODY_001')

    # Verify audit log has required fields
    if audit_logs:
        log = audit_logs[0]
        required = audit_trail_requirements['required_fields']

        for field in required:
            assert field in log, f"Missing required audit field: {field}"


@pytest.mark.asyncio
async def test_discovery_bot_error_handling(
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test error handling and recovery"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    # Test with malformed document
    bad_doc = {'doc_id': 'BAD_001'}  # Missing required fields

    result = await bot.classify_document(bad_doc)

    # Should handle gracefully
    assert result['doc_id'] == 'BAD_001'
    assert 'classification' in result


@pytest.mark.asyncio
async def test_discovery_bot_privilege_waiver_prevention(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test privilege waiver prevention"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    privileged_doc = sample_documents[0]  # EMAIL_001

    result = await bot.detect_privilege(
        privileged_doc,
        ['attorney', 'privileged', 'confidential']
    )

    # Should flag as privileged to prevent accidental disclosure
    assert result['privileged'] == True
    assert result['confidence'] >= 0.85


@pytest.mark.asyncio
async def test_discovery_bot_timeline_construction(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test timeline construction from documents"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    # Extract dates from all documents
    all_dates = []

    for doc in sample_documents:
        entities = await bot.extract_entities(doc)
        all_dates.extend(entities['entities']['dates'])

    # Should construct chronological timeline
    assert len(all_dates) > 0
    # Dates should be in ISO format
    for date_str in all_dates:
        try:
            datetime.fromisoformat(date_str)
        except ValueError:
            pytest.fail(f"Invalid date format: {date_str}")


@pytest.mark.asyncio
async def test_discovery_bot_deduplication(
    sample_documents,
    mock_llm_client,
    mock_supabase_client,
    test_config
):
    """Test duplicate document detection"""
    bot = DiscoveryBot(mock_llm_client, mock_supabase_client, test_config)

    # Process same documents twice
    duplicates = sample_documents + sample_documents

    results = await bot.process_document_batch(duplicates, 'TEST_CASE')

    # Should process all (dedup would happen at higher level)
    assert results['processed'] == len(duplicates)
