#!/usr/bin/env python3
"""
RAG Context Fetcher
Automatically fetches relevant case context for AI agent queries
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional
from pathlib import Path
from codered_client import CodeRedClient

try:
    from openai import OpenAI
except ImportError:
    print("Warning: OpenAI library not installed. Install with: pip install openai")
    OpenAI = None


class RAGContextFetcher:
    """Fetch relevant context from RAG database for agent queries"""

    def __init__(self):
        """Initialize with CodeRed client and OpenAI"""
        self.codered = CodeRedClient()

        # OpenAI for embeddings (if available)
        if OpenAI:
            api_key = os.environ.get('OPENAI_API_KEY')
            self.openai = OpenAI(api_key=api_key) if api_key else None
        else:
            self.openai = None

    def detect_case_id(self, file_path: str) -> Optional[str]:
        """
        Detect case ID from file path

        Examples:
            /cases/CUSTODY-2024-001/emails/...  -> CUSTODY-2024-001
            /legal/FEDS-2024-042/docs/...       -> FEDS-2024-042

        Args:
            file_path: Full file path

        Returns:
            Case ID or None
        """
        # Pattern: WORD-YYYY-NNN
        pattern = r'([A-Z]+[-_]\d{4}[-_]\d{3})'
        match = re.search(pattern, file_path)

        if match:
            case_id = match.group(1).replace('_', '-')
            return case_id

        return None

    def extract_query(self, file_path: str, selection: Optional[str] = None) -> str:
        """
        Extract query text from file or selection

        Args:
            file_path: Path to current file
            selection: Selected text (if any)

        Returns:
            Query string
        """
        if selection and len(selection.strip()) > 0:
            return selection.strip()

        # Try to read first few lines of file
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()[:10]
                return ' '.join(line.strip() for line in lines)
        except Exception:
            # If can't read file, use filename
            return Path(file_path).stem

    def fetch_context(
        self,
        file_path: str,
        selection: Optional[str] = None,
        top_k: int = 5,
        include_precedents: bool = True
    ) -> Dict[str, any]:
        """
        Fetch RAG context for current file/selection

        Args:
            file_path: Current file path
            selection: Selected text (optional)
            top_k: Number of results
            include_precedents: Include legal precedents

        Returns:
            Dictionary with context and metadata
        """
        # Detect case ID
        case_id = self.detect_case_id(file_path)
        if not case_id:
            return {
                'error': 'Could not detect case ID from file path',
                'file_path': file_path
            }

        # Extract query
        query = self.extract_query(file_path, selection)

        # Query embeddings database
        results = self.codered.query_embeddings(
            query=query,
            case_id=case_id,
            top_k=top_k,
            threshold=0.7
        )

        # Format results
        documents = []
        for result in results:
            documents.append({
                'title': result.get('title', 'Untitled'),
                'content': result.get('content', '')[:500],  # First 500 chars
                'source': result.get('source_path', ''),
                'similarity': result.get('similarity', 0.0),
                'zone': result.get('zone', 'UNKNOWN')
            })

        # Get case metadata
        case_metadata = self.codered.get_case_metadata(case_id)

        # Format for agent consumption
        context = {
            'case_id': case_id,
            'case_name': case_metadata.get('name', 'Unknown') if case_metadata else 'Unknown',
            'case_type': case_metadata.get('type', 'Unknown') if case_metadata else 'Unknown',
            'query': query,
            'relevant_documents': documents,
            'document_count': len(documents),
            'precedents': []  # TODO: Add precedent search
        }

        return context

    def format_for_agent(self, context: Dict) -> str:
        """
        Format context as markdown for agent prompt

        Args:
            context: Context dictionary

        Returns:
            Formatted markdown string
        """
        if 'error' in context:
            return f"⚠️ **Error**: {context['error']}"

        md = f"""
# CASE CONTEXT (Auto-Fetched)

**Case ID**: {context['case_id']}
**Case Name**: {context['case_name']}
**Case Type**: {context['case_type']}

## Relevant Documents ({context['document_count']} found)

"""
        for i, doc in enumerate(context['relevant_documents'], 1):
            zone_emoji = {'RED': '🔴', 'YELLOW': '🟡', 'GREEN': '🟢'}.get(doc['zone'], '⚪')
            md += f"""
### {i}. {doc['title']} {zone_emoji}

**Source**: `{doc['source']}`
**Similarity**: {doc['similarity']:.2%}

```
{doc['content']}...
```

"""

        if context['precedents']:
            md += f"\n## Legal Precedents ({len(context['precedents'])} found)\n"
            for prec in context['precedents']:
                md += f"\n- **{prec['case_name']}**: {prec['summary']}\n"

        return md

    def ingest_file(
        self,
        file_path: str,
        case_id: str,
        zone: str = 'YELLOW'
    ) -> Dict[str, any]:
        """
        Ingest a file into the RAG database

        Args:
            file_path: Path to file to ingest
            case_id: Case identifier
            zone: Zone classification

        Returns:
            Result dictionary
        """
        try:
            # Read file content
            with open(file_path, 'r') as f:
                content = f.read()

            # Extract title from filename
            title = Path(file_path).stem

            # Ingest
            result = self.codered.ingest_document(
                title=title,
                content=content,
                source_path=file_path,
                case_id=case_id,
                zone=zone
            )

            return result
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch RAG context for legal discovery')
    parser.add_argument('--file', required=True, help='File path to analyze')
    parser.add_argument('--selection', help='Selected text (optional)')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results')
    parser.add_argument('--ingest', action='store_true', help='Ingest file instead of fetching')
    parser.add_argument('--case-id', help='Case ID (for ingest)')
    parser.add_argument('--zone', default='YELLOW', help='Zone for ingest (RED/YELLOW/GREEN)')
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown',
                        help='Output format')

    args = parser.parse_args()

    fetcher = RAGContextFetcher()

    if args.ingest:
        # Ingest mode
        if not args.case_id:
            print("Error: --case-id required for ingest")
            sys.exit(1)

        result = fetcher.ingest_file(args.file, args.case_id, args.zone)
        print(json.dumps(result, indent=2))
    else:
        # Fetch mode
        context = fetcher.fetch_context(
            file_path=args.file,
            selection=args.selection,
            top_k=args.top_k
        )

        if args.format == 'json':
            print(json.dumps(context, indent=2))
        else:
            print(fetcher.format_for_agent(context))


if __name__ == '__main__':
    main()
