#!/usr/bin/env python3
"""
CONTEXT-INJECTOR.PY
RAG Context Loading for Claude Code Terminal

Purpose: Load relevant case context from Supabase before mode execution
Implements semantic search and context ranking for optimal Claude performance

Author: Claude Code Terminal System
Version: 2.0
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from codered_sync import SupabaseClient
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure OpenAI for embeddings
openai.api_key = os.getenv('OPENAI_API_KEY')


# ============================================================================
# CONTEXT INJECTOR
# ============================================================================

class ContextInjector:
    """
    RAG (Retrieval-Augmented Generation) context loader

    Loads relevant context from Supabase before Claude mode execution:
    - Case documents
    - Prior research
    - Communication logs
    - Strategic memos
    - Evidence database
    """

    def __init__(self):
        """Initialize context injector"""
        self.db = SupabaseClient()
        logger.info("Context Injector initialized")

    # ========================================================================
    # MAIN CONTEXT LOADING
    # ========================================================================

    def load_context_for_mode(
        self,
        mode: str,
        query: str,
        case_number: Optional[str] = None
    ) -> Dict:
        """
        Load relevant context for mode execution

        Args:
            mode: Mode name (discovery, strategy, evidence, analysis, coordinator)
            query: User query or task description
            case_number: Optional case filter

        Returns:
            Context dictionary with all relevant information
        """
        logger.info(f"Loading context for {mode} mode: {query}")

        context = {
            "mode": mode,
            "query": query,
            "case_number": case_number,
            "timestamp": datetime.utcnow().isoformat(),
            "context_sources": {}
        }

        # Load case context if case specified
        if case_number:
            context["case_context"] = self._load_case_context(case_number)

        # Mode-specific context loading
        if mode == "discovery":
            context["context_sources"] = self._load_discovery_context(query, case_number)

        elif mode == "strategy":
            context["context_sources"] = self._load_strategy_context(query, case_number)

        elif mode == "evidence":
            context["context_sources"] = self._load_evidence_context(query, case_number)

        elif mode == "analysis":
            context["context_sources"] = self._load_analysis_context(query, case_number)

        elif mode == "coordinator":
            context["context_sources"] = self._load_coordinator_context(query, case_number)

        # Add privilege warnings
        context["privilege_warnings"] = self._get_privilege_warnings(case_number)

        # Add recent activity
        context["recent_activity"] = self._get_recent_activity(case_number)

        logger.info(f"Context loaded with {len(context['context_sources'])} sources")
        return context

    # ========================================================================
    # CASE CONTEXT
    # ========================================================================

    def _load_case_context(self, case_number: str) -> Dict:
        """
        Load full case context

        Args:
            case_number: Case identifier

        Returns:
            Case context dictionary
        """
        case = self.db.get_case(case_number)

        if not case:
            logger.warning(f"Case not found: {case_number}")
            return {}

        return {
            "case_number": case["case_number"],
            "case_name": case["case_name"],
            "court": case["court"],
            "filing_date": case["filing_date"],
            "case_type": case["case_type"],
            "status": case["status"],
            "parties": case["parties"],
            "deadlines": case["deadlines"],
            "metadata": case.get("metadata", {})
        }

    # ========================================================================
    # MODE-SPECIFIC CONTEXT LOADING
    # ========================================================================

    def _load_discovery_context(
        self,
        query: str,
        case_number: Optional[str]
    ) -> Dict:
        """
        Load context for discovery mode

        Includes:
        - Prior search results on similar queries
        - Related case law from previous searches
        - Relevant communication threads
        """
        context = {}

        # Load prior discovery results
        if case_number:
            prior_searches = self.db.search_discovery_results(
                case_number=case_number,
                limit=10
            )
            context["prior_searches"] = prior_searches

        # Semantic search for relevant documents
        relevant_docs = self._semantic_search(query, case_number, limit=5)
        context["relevant_documents"] = relevant_docs

        return context

    def _load_strategy_context(
        self,
        query: str,
        case_number: Optional[str]
    ) -> Dict:
        """
        Load context for strategy mode

        Includes:
        - Prior legal research
        - Related motions and briefs
        - Strategic memos
        - Case law on similar issues
        """
        context = {}

        # Load prior discovery results (for case law)
        if case_number:
            discovery_results = self.db.search_discovery_results(
                case_number=case_number,
                source="Westlaw",
                limit=20
            )
            context["case_law_research"] = discovery_results

        # Semantic search for strategic memos
        strategic_docs = self._semantic_search(
            query + " strategy memo motion argument",
            case_number,
            limit=5
        )
        context["strategic_documents"] = strategic_docs

        return context

    def _load_evidence_context(
        self,
        query: str,
        case_number: Optional[str]
    ) -> Dict:
        """
        Load context for evidence mode

        Includes:
        - Existing evidence database
        - Prior fact extractions
        - Related documents
        - Timeline events
        """
        context = {}

        # Load existing evidence
        if case_number:
            evidence = self.db.get_case_evidence(case_number)
            context["existing_evidence"] = evidence

        # Semantic search for related documents
        related_docs = self._semantic_search(query, case_number, limit=10)
        context["related_documents"] = related_docs

        return context

    def _load_analysis_context(
        self,
        query: str,
        case_number: Optional[str]
    ) -> Dict:
        """
        Load context for analysis mode

        Includes:
        - All evidence
        - All case law research
        - Prior analyses
        - Strategic memos
        """
        context = {}

        if case_number:
            # Load evidence
            context["evidence"] = self.db.get_case_evidence(case_number)

            # Load discovery results (all sources)
            context["research"] = self.db.search_discovery_results(
                case_number=case_number,
                limit=50
            )

        # Comprehensive semantic search
        comprehensive_docs = self._semantic_search(query, case_number, limit=20)
        context["comprehensive_documents"] = comprehensive_docs

        return context

    def _load_coordinator_context(
        self,
        query: str,
        case_number: Optional[str]
    ) -> Dict:
        """
        Load context for coordinator mode

        Includes:
        - Recent activity across all modes
        - Pending tasks
        - Upcoming deadlines
        - Session history
        """
        context = {}

        # Get attorney from session
        attorney = os.getenv('ATTORNEY_EMAIL', 'alan.redmond@law.com')

        # Load recent session
        recent_session = self.db.get_latest_session(attorney)
        if recent_session:
            context["last_session"] = recent_session

        # Load active cases
        active_cases = self.db.list_active_cases(attorney)
        context["active_cases"] = active_cases

        # Get upcoming deadlines
        context["upcoming_deadlines"] = self._get_upcoming_deadlines(active_cases)

        return context

    # ========================================================================
    # SEMANTIC SEARCH
    # ========================================================================

    def _semantic_search(
        self,
        query: str,
        case_number: Optional[str],
        limit: int = 10
    ) -> List[Dict]:
        """
        Perform semantic search using embeddings

        Args:
            query: Search query
            case_number: Optional case filter
            limit: Maximum results

        Returns:
            List of relevant documents
        """
        try:
            # Generate embedding for query
            embedding = self._generate_embedding(query)

            # Perform vector similarity search in Supabase
            # NOTE: Requires pgvector extension configured in Supabase

            # Fallback to text search for now
            results = self.db.semantic_search(query, case_number, limit)

            # Rank results by relevance
            ranked_results = self._rank_results(results, query)

            return ranked_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate OpenAI embedding for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response['data'][0]['embedding']

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

    def _rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Rank search results by relevance

        Args:
            results: Search results
            query: Original query

        Returns:
            Ranked results
        """
        # Simple keyword-based ranking (replace with vector similarity in production)
        query_terms = query.lower().split()

        for result in results:
            text = result.get('document_text', '').lower()
            score = sum(1 for term in query_terms if term in text)
            result['relevance_score'] = score

        # Sort by relevance
        ranked = sorted(results, key=lambda r: r.get('relevance_score', 0), reverse=True)

        return ranked

    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================

    def _get_privilege_warnings(self, case_number: Optional[str]) -> List[Dict]:
        """
        Get unreviewed privilege flags

        Args:
            case_number: Optional case filter

        Returns:
            List of privilege warnings
        """
        if not case_number:
            return []

        try:
            warnings = self.db.get_privilege_log(
                case_number=case_number,
                reviewed=False
            )
            return warnings

        except Exception as e:
            logger.error(f"Error retrieving privilege warnings: {e}")
            return []

    def _get_recent_activity(self, case_number: Optional[str]) -> List[Dict]:
        """
        Get recent audit trail activity

        Args:
            case_number: Optional case filter

        Returns:
            Recent activity log
        """
        try:
            # Get activity from last 7 days
            start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()

            activity = self.db.get_audit_trail(
                case_number=case_number,
                start_date=start_date,
                limit=20
            )
            return activity

        except Exception as e:
            logger.error(f"Error retrieving recent activity: {e}")
            return []

    def _get_upcoming_deadlines(self, cases: List[Dict]) -> List[Dict]:
        """
        Extract upcoming deadlines from cases

        Args:
            cases: List of case dictionaries

        Returns:
            List of upcoming deadlines
        """
        all_deadlines = []

        for case in cases:
            case_number = case.get('case_number')
            deadlines = case.get('deadlines', [])

            for deadline in deadlines:
                deadline_date = datetime.fromisoformat(deadline['date'])
                days_until = (deadline_date - datetime.utcnow()).days

                if days_until >= 0:  # Future deadlines only
                    all_deadlines.append({
                        'case_number': case_number,
                        'case_name': case.get('case_name'),
                        'deadline_type': deadline.get('type'),
                        'deadline_date': deadline['date'],
                        'days_remaining': days_until,
                        'priority': 'HIGH' if days_until <= 7 else 'MEDIUM' if days_until <= 14 else 'LOW'
                    })

        # Sort by date
        all_deadlines.sort(key=lambda d: d['deadline_date'])

        return all_deadlines

    # ========================================================================
    # CONTEXT FORMATTING
    # ========================================================================

    def format_context_for_prompt(self, context: Dict) -> str:
        """
        Format context as markdown for Claude prompt injection

        Args:
            context: Context dictionary

        Returns:
            Formatted markdown string
        """
        md = "# INJECTED CONTEXT\n\n"

        # Case context
        if context.get('case_context'):
            case = context['case_context']
            md += f"## Case: {case['case_name']}\n"
            md += f"**Case Number:** {case['case_number']}\n"
            md += f"**Court:** {case['court']}\n"
            md += f"**Status:** {case['status']}\n\n"

            # Deadlines
            if case.get('deadlines'):
                md += "### Upcoming Deadlines:\n"
                for deadline in case['deadlines']:
                    md += f"- {deadline['type']}: {deadline['date']}\n"
                md += "\n"

        # Privilege warnings
        if context.get('privilege_warnings'):
            md += "## ⚠️ PRIVILEGE WARNINGS\n"
            md += f"{len(context['privilege_warnings'])} unreviewed privilege flags\n\n"

        # Recent activity
        if context.get('recent_activity'):
            md += "## Recent Activity\n"
            for activity in context['recent_activity'][:5]:
                md += f"- {activity.get('action')} ({activity.get('timestamp')})\n"
            md += "\n"

        # Context sources
        if context.get('context_sources'):
            md += "## Relevant Context\n"

            for source_type, sources in context['context_sources'].items():
                if sources:
                    md += f"\n### {source_type.replace('_', ' ').title()}\n"
                    if isinstance(sources, list):
                        md += f"{len(sources)} items loaded\n"

        return md


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def inject_context(mode: str, query: str, case_number: Optional[str] = None) -> Dict:
    """
    Main function to inject context before mode execution

    Args:
        mode: Mode name
        query: User query
        case_number: Optional case number

    Returns:
        Context dictionary
    """
    injector = ContextInjector()
    return injector.load_context_for_mode(mode, query, case_number)


def format_context(context: Dict) -> str:
    """
    Format context as markdown

    Args:
        context: Context dictionary

    Returns:
        Formatted markdown
    """
    injector = ContextInjector()
    return injector.format_context_for_prompt(context)


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    """Test context injection"""

    # Test discovery mode context
    context = inject_context(
        mode="discovery",
        query="Find cases on Fourth Amendment traffic stops",
        case_number="CV-2024-TEST-001"
    )

    print("=" * 80)
    print("CONTEXT LOADED:")
    print("=" * 80)
    print(json.dumps(context, indent=2))

    print("\n" + "=" * 80)
    print("FORMATTED CONTEXT:")
    print("=" * 80)
    print(format_context(context))
