#!/usr/bin/env python3
"""
CODERED-SYNC.PY
Direct Supabase Integration for Claude Code Terminal

Purpose: Sync all case data, research, and session state with Supabase database
Integrates with CODERED Protocol documented in /IDE:DEV ENVIRONMENT/ELON PROTOCOL/

Author: Claude Code Terminal System
Version: 2.0
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codered-sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CaseContext:
    """Case metadata and context"""
    case_number: str
    case_name: str
    court: str
    filing_date: str
    case_type: str
    status: str
    attorney: str
    parties: Dict[str, str]
    deadlines: List[Dict]
    metadata: Dict = None

@dataclass
class DiscoveryResult:
    """Discovery search results"""
    discovery_id: str
    mode: str
    timestamp: str
    case_number: str
    source: str
    query: str
    results_count: int
    results: Dict
    privilege_flags: List[Dict]
    attorney: str

@dataclass
class Evidence:
    """Evidence item"""
    evidence_id: str
    case_number: str
    evidence_type: str
    description: str
    source_document: str
    date_obtained: str
    authentication_status: str
    privilege_status: str
    chain_of_custody: List[Dict]
    metadata: Dict

@dataclass
class SessionCheckpoint:
    """Session state snapshot"""
    session_id: str
    timestamp: str
    active_mode: str
    case_context: Dict
    conversation_history: List[Dict]
    mode_results: Dict
    privilege_log: List[Dict]
    attorney: str


# ============================================================================
# SUPABASE CLIENT
# ============================================================================

class SupabaseClient:
    """Supabase database client for Claude Code Terminal"""

    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

        self.client: Client = create_client(self.url, self.key)
        logger.info(f"Connected to Supabase at {self.url}")

    # ========================================================================
    # CASE MANAGEMENT
    # ========================================================================

    def create_case(self, case: CaseContext) -> Dict:
        """
        Create new case record in Supabase

        Args:
            case: CaseContext object

        Returns:
            Created case record
        """
        try:
            data = {
                'case_number': case.case_number,
                'case_name': case.case_name,
                'court': case.court,
                'filing_date': case.filing_date,
                'case_type': case.case_type,
                'status': case.status,
                'attorney': case.attorney,
                'parties': case.parties,
                'deadlines': case.deadlines,
                'metadata': case.metadata or {},
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            result = self.client.table('cases').insert(data).execute()
            logger.info(f"Created case: {case.case_number}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error creating case: {e}")
            raise

    def get_case(self, case_number: str) -> Optional[Dict]:
        """
        Retrieve case by case number

        Args:
            case_number: Case identifier

        Returns:
            Case record or None
        """
        try:
            result = self.client.table('cases').select('*').eq(
                'case_number', case_number
            ).execute()

            if result.data:
                logger.info(f"Retrieved case: {case_number}")
                return result.data[0]
            else:
                logger.warning(f"Case not found: {case_number}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving case: {e}")
            raise

    def update_case(self, case_number: str, updates: Dict) -> Dict:
        """
        Update case record

        Args:
            case_number: Case identifier
            updates: Dictionary of fields to update

        Returns:
            Updated case record
        """
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()

            result = self.client.table('cases').update(updates).eq(
                'case_number', case_number
            ).execute()

            logger.info(f"Updated case: {case_number}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error updating case: {e}")
            raise

    def list_active_cases(self, attorney: str) -> List[Dict]:
        """
        List all active cases for attorney

        Args:
            attorney: Attorney email

        Returns:
            List of active cases
        """
        try:
            result = self.client.table('cases').select('*').eq(
                'attorney', attorney
            ).eq(
                'status', 'active'
            ).execute()

            logger.info(f"Retrieved {len(result.data)} active cases for {attorney}")
            return result.data

        except Exception as e:
            logger.error(f"Error listing cases: {e}")
            raise

    # ========================================================================
    # DISCOVERY RESULTS
    # ========================================================================

    def store_discovery_result(self, discovery: DiscoveryResult) -> Dict:
        """
        Store discovery search results

        Args:
            discovery: DiscoveryResult object

        Returns:
            Created discovery record
        """
        try:
            data = {
                'discovery_id': discovery.discovery_id,
                'mode': discovery.mode,
                'timestamp': discovery.timestamp,
                'case_number': discovery.case_number,
                'source': discovery.source,
                'query': discovery.query,
                'results_count': discovery.results_count,
                'results': discovery.results,
                'privilege_flags': discovery.privilege_flags,
                'attorney': discovery.attorney
            }

            result = self.client.table('discovery_results').insert(data).execute()
            logger.info(f"Stored discovery result: {discovery.discovery_id}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error storing discovery result: {e}")
            raise

    def search_discovery_results(
        self,
        case_number: str,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search discovery results for case

        Args:
            case_number: Case identifier
            source: Filter by source (Westlaw, Gmail, etc.)
            limit: Maximum results to return

        Returns:
            List of discovery results
        """
        try:
            query = self.client.table('discovery_results').select('*').eq(
                'case_number', case_number
            )

            if source:
                query = query.eq('source', source)

            result = query.order('timestamp', desc=True).limit(limit).execute()

            logger.info(f"Retrieved {len(result.data)} discovery results for {case_number}")
            return result.data

        except Exception as e:
            logger.error(f"Error searching discovery results: {e}")
            raise

    # ========================================================================
    # EVIDENCE MANAGEMENT
    # ========================================================================

    def store_evidence(self, evidence: Evidence) -> Dict:
        """
        Store evidence item

        Args:
            evidence: Evidence object

        Returns:
            Created evidence record
        """
        try:
            data = {
                'evidence_id': evidence.evidence_id,
                'case_number': evidence.case_number,
                'evidence_type': evidence.evidence_type,
                'description': evidence.description,
                'source_document': evidence.source_document,
                'date_obtained': evidence.date_obtained,
                'authentication_status': evidence.authentication_status,
                'privilege_status': evidence.privilege_status,
                'chain_of_custody': evidence.chain_of_custody,
                'metadata': evidence.metadata,
                'created_at': datetime.utcnow().isoformat()
            }

            result = self.client.table('evidence').insert(data).execute()
            logger.info(f"Stored evidence: {evidence.evidence_id}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error storing evidence: {e}")
            raise

    def get_case_evidence(self, case_number: str) -> List[Dict]:
        """
        Retrieve all evidence for case

        Args:
            case_number: Case identifier

        Returns:
            List of evidence items
        """
        try:
            result = self.client.table('evidence').select('*').eq(
                'case_number', case_number
            ).execute()

            logger.info(f"Retrieved {len(result.data)} evidence items for {case_number}")
            return result.data

        except Exception as e:
            logger.error(f"Error retrieving evidence: {e}")
            raise

    def update_chain_of_custody(
        self,
        evidence_id: str,
        custody_entry: Dict
    ) -> Dict:
        """
        Add chain of custody entry to evidence

        Args:
            evidence_id: Evidence identifier
            custody_entry: Chain of custody event

        Returns:
            Updated evidence record
        """
        try:
            # Get current evidence
            current = self.client.table('evidence').select('chain_of_custody').eq(
                'evidence_id', evidence_id
            ).execute()

            if not current.data:
                raise ValueError(f"Evidence not found: {evidence_id}")

            chain = current.data[0].get('chain_of_custody', [])
            chain.append(custody_entry)

            # Update evidence
            result = self.client.table('evidence').update({
                'chain_of_custody': chain,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('evidence_id', evidence_id).execute()

            logger.info(f"Updated chain of custody for evidence: {evidence_id}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error updating chain of custody: {e}")
            raise

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def save_session_checkpoint(self, session: SessionCheckpoint) -> Dict:
        """
        Save session checkpoint

        Args:
            session: SessionCheckpoint object

        Returns:
            Created checkpoint record
        """
        try:
            data = {
                'session_id': session.session_id,
                'timestamp': session.timestamp,
                'active_mode': session.active_mode,
                'case_context': session.case_context,
                'conversation_history': session.conversation_history,
                'mode_results': session.mode_results,
                'privilege_log': session.privilege_log,
                'attorney': session.attorney
            }

            result = self.client.table('session_checkpoints').insert(data).execute()
            logger.info(f"Saved session checkpoint: {session.session_id}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error saving session checkpoint: {e}")
            raise

    def load_session_checkpoint(self, session_id: str) -> Optional[Dict]:
        """
        Load session checkpoint

        Args:
            session_id: Session identifier

        Returns:
            Session checkpoint or None
        """
        try:
            result = self.client.table('session_checkpoints').select('*').eq(
                'session_id', session_id
            ).execute()

            if result.data:
                logger.info(f"Loaded session checkpoint: {session_id}")
                return result.data[0]
            else:
                logger.warning(f"Session checkpoint not found: {session_id}")
                return None

        except Exception as e:
            logger.error(f"Error loading session checkpoint: {e}")
            raise

    def get_latest_session(self, attorney: str) -> Optional[Dict]:
        """
        Get most recent session for attorney

        Args:
            attorney: Attorney email

        Returns:
            Latest session checkpoint or None
        """
        try:
            result = self.client.table('session_checkpoints').select('*').eq(
                'attorney', attorney
            ).order('timestamp', desc=True).limit(1).execute()

            if result.data:
                logger.info(f"Retrieved latest session for {attorney}")
                return result.data[0]
            else:
                logger.warning(f"No sessions found for {attorney}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving latest session: {e}")
            raise

    # ========================================================================
    # PRIVILEGE LOG
    # ========================================================================

    def log_privilege_flag(self, privilege_entry: Dict) -> Dict:
        """
        Log privilege flag event

        Args:
            privilege_entry: Privilege flag details

        Returns:
            Created privilege log entry
        """
        try:
            data = {
                **privilege_entry,
                'timestamp': datetime.utcnow().isoformat()
            }

            result = self.client.table('privilege_log').insert(data).execute()
            logger.info(f"Logged privilege flag for {privilege_entry.get('document_id')}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error logging privilege flag: {e}")
            raise

    def get_privilege_log(
        self,
        case_number: str,
        reviewed: Optional[bool] = None
    ) -> List[Dict]:
        """
        Retrieve privilege log for case

        Args:
            case_number: Case identifier
            reviewed: Filter by review status

        Returns:
            List of privilege log entries
        """
        try:
            query = self.client.table('privilege_log').select('*').eq(
                'case_number', case_number
            )

            if reviewed is not None:
                query = query.eq('reviewed', reviewed)

            result = query.order('timestamp', desc=True).execute()

            logger.info(f"Retrieved {len(result.data)} privilege log entries for {case_number}")
            return result.data

        except Exception as e:
            logger.error(f"Error retrieving privilege log: {e}")
            raise

    # ========================================================================
    # FULL-TEXT SEARCH (RAG)
    # ========================================================================

    def semantic_search(
        self,
        query: str,
        case_number: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Perform semantic search across case documents

        Uses Supabase's pgvector extension for vector similarity search

        Args:
            query: Search query
            case_number: Optional case filter
            limit: Maximum results

        Returns:
            List of relevant documents
        """
        try:
            # This is a placeholder for actual vector search implementation
            # Requires pgvector extension and embedding generation

            query_obj = self.client.table('case_documents').select('*')

            if case_number:
                query_obj = query_obj.eq('case_number', case_number)

            # Text search as fallback (replace with vector search in production)
            result = query_obj.text_search('document_text', query).limit(limit).execute()

            logger.info(f"Semantic search returned {len(result.data)} results for: {query}")
            return result.data

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise

    # ========================================================================
    # AUDIT TRAIL
    # ========================================================================

    def log_audit_event(self, event: Dict) -> Dict:
        """
        Log audit trail event

        Args:
            event: Audit event details

        Returns:
            Created audit log entry
        """
        try:
            data = {
                **event,
                'timestamp': datetime.utcnow().isoformat()
            }

            result = self.client.table('audit_trail').insert(data).execute()
            logger.info(f"Logged audit event: {event.get('action')}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            raise

    def get_audit_trail(
        self,
        case_number: Optional[str] = None,
        attorney: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Retrieve audit trail with filters

        Args:
            case_number: Filter by case
            attorney: Filter by attorney
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum results

        Returns:
            List of audit log entries
        """
        try:
            query = self.client.table('audit_trail').select('*')

            if case_number:
                query = query.eq('case_number', case_number)
            if attorney:
                query = query.eq('attorney', attorney)
            if start_date:
                query = query.gte('timestamp', start_date)
            if end_date:
                query = query.lte('timestamp', end_date)

            result = query.order('timestamp', desc=True).limit(limit).execute()

            logger.info(f"Retrieved {len(result.data)} audit trail entries")
            return result.data

        except Exception as e:
            logger.error(f"Error retrieving audit trail: {e}")
            raise


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def initialize_database_schema():
    """
    Initialize Supabase database schema

    Creates all required tables if they don't exist
    Run this once during initial setup
    """
    # NOTE: In production, create tables via Supabase dashboard or migration scripts
    # This is a reference schema

    schema = """
    -- Cases table
    CREATE TABLE IF NOT EXISTS cases (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        case_number TEXT UNIQUE NOT NULL,
        case_name TEXT NOT NULL,
        court TEXT,
        filing_date DATE,
        case_type TEXT,
        status TEXT,
        attorney TEXT,
        parties JSONB,
        deadlines JSONB,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Discovery results table
    CREATE TABLE IF NOT EXISTS discovery_results (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        discovery_id TEXT UNIQUE NOT NULL,
        mode TEXT,
        timestamp TIMESTAMP,
        case_number TEXT REFERENCES cases(case_number),
        source TEXT,
        query TEXT,
        results_count INTEGER,
        results JSONB,
        privilege_flags JSONB,
        attorney TEXT
    );

    -- Evidence table
    CREATE TABLE IF NOT EXISTS evidence (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        evidence_id TEXT UNIQUE NOT NULL,
        case_number TEXT REFERENCES cases(case_number),
        evidence_type TEXT,
        description TEXT,
        source_document TEXT,
        date_obtained DATE,
        authentication_status TEXT,
        privilege_status TEXT,
        chain_of_custody JSONB,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Session checkpoints table
    CREATE TABLE IF NOT EXISTS session_checkpoints (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        session_id TEXT UNIQUE NOT NULL,
        timestamp TIMESTAMP,
        active_mode TEXT,
        case_context JSONB,
        conversation_history JSONB,
        mode_results JSONB,
        privilege_log JSONB,
        attorney TEXT
    );

    -- Privilege log table
    CREATE TABLE IF NOT EXISTS privilege_log (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        case_number TEXT REFERENCES cases(case_number),
        document_id TEXT,
        privilege_type TEXT,
        confidence TEXT,
        reviewed BOOLEAN DEFAULT FALSE,
        attorney_decision TEXT,
        timestamp TIMESTAMP DEFAULT NOW()
    );

    -- Audit trail table
    CREATE TABLE IF NOT EXISTS audit_trail (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        timestamp TIMESTAMP DEFAULT NOW(),
        case_number TEXT,
        attorney TEXT,
        mode TEXT,
        action TEXT,
        details JSONB
    );

    -- Case documents table (for RAG)
    CREATE TABLE IF NOT EXISTS case_documents (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        case_number TEXT REFERENCES cases(case_number),
        document_id TEXT UNIQUE NOT NULL,
        document_type TEXT,
        document_text TEXT,
        embedding VECTOR(1536),  -- For OpenAI embeddings
        metadata JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Create indexes
    CREATE INDEX idx_cases_attorney ON cases(attorney);
    CREATE INDEX idx_discovery_case ON discovery_results(case_number);
    CREATE INDEX idx_evidence_case ON evidence(case_number);
    CREATE INDEX idx_audit_case ON audit_trail(case_number);
    CREATE INDEX idx_audit_attorney ON audit_trail(attorney);
    """

    logger.info("Database schema reference generated")
    return schema


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    """Test Supabase integration"""

    # Initialize client
    db = SupabaseClient()

    # Example: Create a test case
    test_case = CaseContext(
        case_number="CV-2024-TEST-001",
        case_name="Test v. Example",
        court="Superior Court of California",
        filing_date="2024-12-16",
        case_type="Civil",
        status="active",
        attorney="alan.redmond@law.com",
        parties={"plaintiff": "Test Corp", "defendant": "Example Inc"},
        deadlines=[
            {"type": "discovery_cutoff", "date": "2025-06-01"},
            {"type": "trial", "date": "2025-09-15"}
        ]
    )

    try:
        # Create case
        created_case = db.create_case(test_case)
        print(f"Created case: {created_case}")

        # Retrieve case
        retrieved_case = db.get_case("CV-2024-TEST-001")
        print(f"Retrieved case: {retrieved_case}")

        # List active cases
        active_cases = db.list_active_cases("alan.redmond@law.com")
        print(f"Active cases: {len(active_cases)}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
