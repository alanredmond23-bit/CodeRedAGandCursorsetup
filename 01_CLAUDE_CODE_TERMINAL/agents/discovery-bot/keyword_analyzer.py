"""
Keyword Analyzer - Extract keywords and calculate relevance scores
"""

import json
import logging
from typing import Dict, Any, List
from collections import Counter
import re
import anthropic

logger = logging.getLogger(__name__)


class KeywordAnalyzer:
    """Analyze documents for keywords and relevance"""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.model = 'claude-sonnet-4-5-20250929'

        # Common legal stopwords to filter
        self.legal_stopwords = set([
            'hereby', 'whereas', 'therefore', 'aforementioned',
            'pursuant', 'notwithstanding', 'thereof', 'herein'
        ])

    async def analyze(
        self,
        text: str,
        classification: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze document for keywords and relevance

        Args:
            text: Document text
            classification: Document classification

        Returns:
            Keywords with relevance scores and context
        """
        try:
            # Extract basic keywords first
            basic_keywords = self._extract_basic_keywords(text)

            # Use Claude for semantic keyword extraction
            prompt = self._build_keyword_prompt(text, classification)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.0,
                system=[
                    {
                        "type": "text",
                        "text": """You are an expert legal keyword analyst. You identify the most relevant and important keywords, phrases, and concepts in legal documents. You understand:

- Legal terminology and concepts
- Issue spotting and legal theories
- Key facts vs background information
- Document relevance and importance
- Search term optimization

You extract keywords that would be most useful for:
- Document search and retrieval
- Issue identification
- Case theory development
- Evidence organization""",
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

            # Combine with basic keywords
            result['basic_keywords'] = basic_keywords

            # Add usage statistics
            result['tokens_used'] = {
                'input': response.usage.input_tokens,
                'output': response.usage.output_tokens,
                'cache_creation': getattr(response.usage, 'cache_creation_input_tokens', 0),
                'cache_read': getattr(response.usage, 'cache_read_input_tokens', 0)
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse keyword analysis response: {e}")
            return self._fallback_keyword_analysis(text)
        except Exception as e:
            logger.error(f"Keyword analysis error: {e}")
            return self._fallback_keyword_analysis(text)

    def _build_keyword_prompt(
        self,
        text: str,
        classification: Optional[Dict]
    ) -> str:
        """Build keyword analysis prompt"""

        # Truncate if needed
        max_length = 15000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Document truncated...]"

        doc_type = classification.get('document_type', 'unknown') if classification else 'unknown'

        return f"""Analyze this legal document for keywords and relevance.

DOCUMENT TYPE: {doc_type}

DOCUMENT TEXT:
{text}

ANALYSIS REQUIREMENTS:

1. Extract PRIMARY KEYWORDS (most important):
   - Legal concepts and theories
   - Key issues and claims
   - Important parties and entities
   - Critical facts
   - Provide relevance score (0.0 to 1.0)

2. Extract SECONDARY KEYWORDS (supporting):
   - Supporting facts
   - Procedural terms
   - Document-specific terminology
   - Provide relevance score

3. Identify KEY PHRASES:
   - Multi-word phrases that capture important concepts
   - Legal terms of art
   - Unique identifiers

4. Determine DOCUMENT RELEVANCE:
   - Overall importance score (0.0 to 1.0)
   - Relevance to potential legal issues
   - Discovery value

5. Suggest SEARCH TERMS:
   - Terms that would help find similar documents
   - Boolean search queries
   - Concept searches

OUTPUT FORMAT (valid JSON only):
{{
  "primary_keywords": [
    {{
      "keyword": "settlement",
      "relevance": 0.95,
      "frequency": 5,
      "context": "settlement negotiations",
      "category": "legal_concept"
    }},
    {{
      "keyword": "breach of contract",
      "relevance": 0.9,
      "frequency": 3,
      "context": "claims for breach of contract",
      "category": "legal_issue"
    }}
  ],
  "secondary_keywords": [
    {{
      "keyword": "payment terms",
      "relevance": 0.7,
      "frequency": 2,
      "context": "discussing payment terms",
      "category": "fact"
    }}
  ],
  "key_phrases": [
    {{
      "phrase": "material breach",
      "relevance": 0.85,
      "frequency": 2,
      "type": "legal_term"
    }}
  ],
  "relevance_analysis": {{
    "overall_relevance": 0.85,
    "relevance_factors": [
      "Contains settlement discussions",
      "Identifies breach of contract claims",
      "Includes damages calculations"
    ],
    "discovery_value": "high",
    "key_issues": [
      "contract breach",
      "damages",
      "settlement"
    ]
  }},
  "search_suggestions": {{
    "keyword_searches": [
      "settlement AND breach",
      "damages AND contract"
    ],
    "concept_searches": [
      "contract disputes",
      "breach remedies"
    ],
    "related_terms": [
      "liquidated damages",
      "specific performance",
      "rescission"
    ]
  }},
  "summary": "Document discusses settlement of contract breach claim with damages calculations."
}}

CRITICAL RULES:
- Focus on legal relevance, not just word frequency
- Identify concepts, not just individual words
- Consider what makes this document discoverable
- Think about what a lawyer would search for

Respond with ONLY the JSON object, no additional text."""

    def _extract_basic_keywords(self, text: str) -> Dict[str, Any]:
        """Extract basic keywords using statistical methods"""

        # Clean and tokenize
        text_lower = text.lower()

        # Remove punctuation except hyphens (for terms like "attorney-client")
        text_clean = re.sub(r'[^\w\s-]', ' ', text_lower)

        # Tokenize
        words = text_clean.split()

        # Filter stopwords and short words
        common_stopwords = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'it', 'its'
        ])

        filtered_words = [
            word for word in words
            if len(word) > 2 and word not in common_stopwords and word not in self.legal_stopwords
        ]

        # Count frequencies
        word_freq = Counter(filtered_words)

        # Get top keywords
        top_keywords = [
            {
                'keyword': word,
                'frequency': count,
                'relevance': min(1.0, count / 10)  # Simple relevance heuristic
            }
            for word, count in word_freq.most_common(30)
        ]

        # Extract bigrams (two-word phrases)
        bigrams = [
            f"{filtered_words[i]} {filtered_words[i+1]}"
            for i in range(len(filtered_words) - 1)
        ]
        bigram_freq = Counter(bigrams)

        top_bigrams = [
            {
                'phrase': phrase,
                'frequency': count,
                'relevance': min(1.0, count / 5)
            }
            for phrase, count in bigram_freq.most_common(20)
            if count > 1  # Only include repeated phrases
        ]

        return {
            'top_keywords': top_keywords,
            'top_phrases': top_bigrams,
            'total_words': len(words),
            'unique_words': len(word_freq),
            'method': 'statistical'
        }

    def _fallback_keyword_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback keyword analysis"""

        basic = self._extract_basic_keywords(text)

        return {
            'primary_keywords': basic['top_keywords'][:10],
            'secondary_keywords': basic['top_keywords'][10:30],
            'key_phrases': basic['top_phrases'],
            'relevance_analysis': {
                'overall_relevance': 0.5,
                'relevance_factors': ['Unable to perform semantic analysis'],
                'discovery_value': 'unknown',
                'key_issues': []
            },
            'search_suggestions': {
                'keyword_searches': [],
                'concept_searches': [],
                'related_terms': []
            },
            'summary': 'Fallback keyword extraction used (semantic analysis unavailable)',
            'basic_keywords': basic,
            'method': 'fallback',
            'tokens_used': {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            }
        }
