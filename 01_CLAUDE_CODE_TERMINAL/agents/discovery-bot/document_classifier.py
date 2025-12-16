"""
Document Classifier - Classify legal document types with high accuracy
"""

import json
import logging
from typing import Dict, Any, Optional
import anthropic

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classify legal documents into specific types"""

    DOCUMENT_TYPES = [
        'email',
        'contract',
        'deposition',
        'pleading',
        'motion',
        'order',
        'letter',
        'memo',
        'invoice',
        'receipt',
        'agreement',
        'policy',
        'report',
        'presentation',
        'spreadsheet',
        'other'
    ]

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.model = 'claude-sonnet-4-5-20250929'

    async def classify(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Classify document type with confidence scoring

        Args:
            text: Document text content
            metadata: Optional metadata that might help classification

        Returns:
            Classification results with confidence scores
        """
        try:
            # Prepare classification prompt
            prompt = self._build_classification_prompt(text, metadata)

            # Call Claude API with prompt caching for efficiency
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.0,
                system=[
                    {
                        "type": "text",
                        "text": "You are an expert legal document classifier with 20+ years experience in litigation and discovery. You classify documents with extremely high accuracy.",
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

            # Add usage statistics
            result['tokens_used'] = {
                'input': response.usage.input_tokens,
                'output': response.usage.output_tokens,
                'cache_creation': getattr(response.usage, 'cache_creation_input_tokens', 0),
                'cache_read': getattr(response.usage, 'cache_read_input_tokens', 0)
            }

            # Validate classification
            if result['document_type'] not in self.DOCUMENT_TYPES:
                logger.warning(f"Unexpected document type: {result['document_type']}")
                result['document_type'] = 'other'

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
            return self._fallback_classification(text, metadata)
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._fallback_classification(text, metadata)

    def _build_classification_prompt(
        self,
        text: str,
        metadata: Optional[Dict]
    ) -> str:
        """Build classification prompt"""

        # Truncate very long documents
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Document truncated for classification...]"

        metadata_str = ""
        if metadata:
            metadata_str = f"\n\nMETADATA:\n{json.dumps(metadata, indent=2)}"

        return f"""Classify the following legal document with high precision.

DOCUMENT TEXT:
{text}
{metadata_str}

INSTRUCTIONS:
1. Determine the primary document type from this list:
   - email: Email correspondence
   - contract: Contracts, agreements, terms of service
   - deposition: Deposition transcripts or testimony
   - pleading: Complaints, answers, counterclaims
   - motion: Motions to the court
   - order: Court orders or rulings
   - letter: Formal letters or correspondence (non-email)
   - memo: Internal memos or memoranda
   - invoice: Invoices or bills
   - receipt: Payment receipts or confirmations
   - agreement: General agreements or settlements
   - policy: Company policies or procedures
   - report: Reports, analyses, or summaries
   - presentation: Slide decks or presentations
   - spreadsheet: Financial data or tabular data
   - other: Any other document type

2. Provide confidence score (0.0 to 1.0)

3. Identify key indicators that led to this classification

4. Note any sub-classifications or special characteristics

5. Flag if the document appears to be OCR'd (contains OCR errors)

OUTPUT FORMAT (valid JSON only):
{{
  "document_type": "email",
  "confidence": 0.98,
  "sub_type": "attorney-client communication",
  "indicators": [
    "Contains From/To/Subject headers",
    "Email formatting and structure",
    "Email signature block present"
  ],
  "characteristics": [
    "confidential",
    "attorney-client privileged"
  ],
  "is_ocr": false,
  "ocr_quality": null,
  "needs_review": false,
  "review_reason": null
}}

Respond with ONLY the JSON object, no additional text."""

    def _fallback_classification(
        self,
        text: str,
        metadata: Optional[Dict]
    ) -> Dict[str, Any]:
        """Provide fallback classification using simple heuristics"""

        text_lower = text.lower()

        # Simple keyword-based classification
        if any(word in text_lower for word in ['from:', 'to:', 'subject:', 'sent:']):
            doc_type = 'email'
            confidence = 0.7
        elif any(word in text_lower for word in ['agreement', 'contract', 'party', 'whereas']):
            doc_type = 'contract'
            confidence = 0.6
        elif 'deposition' in text_lower or 'q.' in text_lower and 'a.' in text_lower:
            doc_type = 'deposition'
            confidence = 0.6
        elif any(word in text_lower for word in ['complaint', 'plaintiff', 'defendant', 'cause of action']):
            doc_type = 'pleading'
            confidence = 0.6
        else:
            doc_type = 'other'
            confidence = 0.3

        return {
            'document_type': doc_type,
            'confidence': confidence,
            'sub_type': 'unknown',
            'indicators': ['Fallback classification used'],
            'characteristics': [],
            'is_ocr': False,
            'ocr_quality': None,
            'needs_review': True,
            'review_reason': 'Classification API failed, using fallback heuristics',
            'tokens_used': {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            }
        }

    def batch_classify(self, documents: list) -> list:
        """Classify multiple documents (synchronous wrapper for async)"""
        import asyncio

        async def _batch_classify():
            tasks = [self.classify(doc['text'], doc.get('metadata')) for doc in documents]
            return await asyncio.gather(*tasks)

        return asyncio.run(_batch_classify())
