"""
Embedding Generator - Create vector embeddings for semantic search
"""

import json
import logging
from typing import Dict, Any, List, Optional
import anthropic
import hashlib

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for semantic search and similarity"""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.model = 'claude-sonnet-4-5-20250929'

    async def generate(
        self,
        text: str,
        entities: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings and semantic representations

        Note: Claude API doesn't natively support embeddings like OpenAI.
        This implementation creates semantic summaries that can be embedded
        by other services (like Voyage AI, Cohere, or sentence-transformers)

        Args:
            text: Document text
            entities: Extracted entities

        Returns:
            Semantic summaries and chunked text for embedding
        """
        try:
            # Generate semantic summary
            prompt = self._build_summary_prompt(text, entities)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.0,
                system=[
                    {
                        "type": "text",
                        "text": """You are an expert at creating concise, semantically rich summaries of legal documents for embedding and semantic search. You create summaries that capture the essence and key concepts while being optimized for vector similarity search.""",
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            result_text = response.content[0].text
            result = json.loads(result_text)

            # Chunk text for embedding
            chunks = self._chunk_text(text)

            # Create embedding-ready output
            embedding_data = {
                'semantic_summary': result.get('summary', ''),
                'key_concepts': result.get('key_concepts', []),
                'semantic_tags': result.get('semantic_tags', []),
                'chunks': chunks,
                'chunk_count': len(chunks),
                'metadata': {
                    'doc_hash': self._hash_text(text),
                    'text_length': len(text),
                    'chunk_size': 512,
                    'overlap': 50
                },
                'tokens_used': {
                    'input': response.usage.input_tokens,
                    'output': response.usage.output_tokens,
                    'cache_creation': getattr(response.usage, 'cache_creation_input_tokens', 0),
                    'cache_read': getattr(response.usage, 'cache_read_input_tokens', 0)
                }
            }

            # Add instructions for downstream embedding
            embedding_data['embedding_instructions'] = {
                'recommended_service': 'voyage-law-2 or sentence-transformers/legal-bert-base-uncased',
                'primary_text': embedding_data['semantic_summary'],
                'chunk_texts': [chunk['text'] for chunk in chunks],
                'use_case': 'semantic search and document similarity'
            }

            return embedding_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse embedding generation response: {e}")
            return self._fallback_embedding(text)
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return self._fallback_embedding(text)

    def _build_summary_prompt(
        self,
        text: str,
        entities: Optional[Dict]
    ) -> str:
        """Build semantic summary prompt"""

        # Truncate if needed
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Document truncated...]"

        entities_str = ""
        if entities:
            # Include key entities for context
            people = [p['name'] for p in entities.get('people', [])[:5]]
            orgs = [o['name'] for o in entities.get('organizations', [])[:5]]
            if people or orgs:
                entities_str = f"\n\nKEY ENTITIES:\nPeople: {', '.join(people)}\nOrganizations: {', '.join(orgs)}"

        return f"""Create a semantic summary of this legal document optimized for embedding and semantic search.

DOCUMENT TEXT:
{text}
{entities_str}

REQUIREMENTS:

1. Create a concise semantic summary (2-3 sentences) that captures:
   - Core subject matter
   - Key parties involved
   - Main legal issues or transaction type
   - Critical facts or outcomes

2. Extract key concepts (single words or short phrases) that represent:
   - Legal theories
   - Document purpose
   - Important topics
   - Searchable terms

3. Generate semantic tags for categorization:
   - Practice area (e.g., "contract law", "tort", "employment")
   - Document function (e.g., "evidence", "pleading", "correspondence")
   - Content type (e.g., "transactional", "litigation", "advisory")

OUTPUT FORMAT (valid JSON only):
{{
  "summary": "Email from attorney John Smith to client Sarah Johnson providing legal advice on settlement strategy for Jones v. Acme Corp breach of contract case, recommending $2.5M settlement to avoid trial risks.",
  "key_concepts": [
    "attorney-client communication",
    "settlement strategy",
    "breach of contract",
    "litigation risk assessment",
    "damages negotiation"
  ],
  "semantic_tags": [
    "practice_area:litigation",
    "practice_area:contract_law",
    "document_type:legal_advice",
    "privilege:attorney_client",
    "content:settlement_discussion",
    "matter:jones_v_acme"
  ]
}}

Respond with ONLY the JSON object, no additional text."""

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Chunk text for embedding generation

        Args:
            text: Full text
            chunk_size: Characters per chunk
            overlap: Overlap between chunks

        Returns:
            List of chunks with metadata
        """
        chunks = []
        text_length = len(text)

        # Split by paragraphs first
        paragraphs = text.split('\n\n')

        current_chunk = ""
        chunk_index = 0
        start_pos = 0

        for para in paragraphs:
            # If adding this paragraph exceeds chunk size, save current chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append({
                    'chunk_id': chunk_index,
                    'text': current_chunk.strip(),
                    'start_position': start_pos,
                    'end_position': start_pos + len(current_chunk),
                    'length': len(current_chunk)
                })

                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para
                start_pos = start_pos + len(current_chunk) - overlap - len(para)
                chunk_index += 1
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        # Add final chunk
        if current_chunk:
            chunks.append({
                'chunk_id': chunk_index,
                'text': current_chunk.strip(),
                'start_position': start_pos,
                'end_position': start_pos + len(current_chunk),
                'length': len(current_chunk)
            })

        return chunks

    def _hash_text(self, text: str) -> str:
        """Generate hash of text for deduplication"""
        return hashlib.sha256(text.encode()).hexdigest()

    def _fallback_embedding(self, text: str) -> Dict[str, Any]:
        """Fallback embedding generation"""

        chunks = self._chunk_text(text)

        # Create simple summary (first 500 chars)
        summary = text[:500] + "..." if len(text) > 500 else text

        return {
            'semantic_summary': summary,
            'key_concepts': [],
            'semantic_tags': [],
            'chunks': chunks,
            'chunk_count': len(chunks),
            'metadata': {
                'doc_hash': self._hash_text(text),
                'text_length': len(text),
                'chunk_size': 512,
                'overlap': 50,
                'method': 'fallback'
            },
            'embedding_instructions': {
                'recommended_service': 'voyage-law-2 or sentence-transformers/legal-bert-base-uncased',
                'primary_text': summary,
                'chunk_texts': [chunk['text'] for chunk in chunks],
                'use_case': 'semantic search and document similarity'
            },
            'tokens_used': {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            }
        }
