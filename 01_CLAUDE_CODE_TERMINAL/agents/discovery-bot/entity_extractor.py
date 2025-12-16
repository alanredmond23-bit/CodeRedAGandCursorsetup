"""
Entity Extractor - Extract people, organizations, dates, amounts, locations with high accuracy
"""

import json
import logging
import re
from typing import Dict, Any, List
from datetime import datetime
import anthropic

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract named entities from legal documents"""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.model = 'claude-sonnet-4-5-20250929'

    async def extract(
        self,
        text: str,
        classification: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract entities with high accuracy and confidence scoring

        Args:
            text: Document text
            classification: Optional document classification to guide extraction

        Returns:
            Extracted entities with confidence scores and context
        """
        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt(text, classification)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                system=[
                    {
                        "type": "text",
                        "text": """You are an expert legal entity extraction specialist. You extract entities from legal documents with extremely high precision and recall. You understand:

- Legal naming conventions and titles
- Corporate entity structures
- Date formats in legal documents
- Monetary amounts and financial terms
- Geographic locations and jurisdictions
- Attorney-client relationships
- Court and case identifiers

You NEVER hallucinate entities. You only extract what is explicitly present in the text.""",
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

            # Post-process and validate entities
            result = self._validate_and_enrich_entities(result, text)

            # Add usage statistics
            result['tokens_used'] = {
                'input': response.usage.input_tokens,
                'output': response.usage.output_tokens,
                'cache_creation': getattr(response.usage, 'cache_creation_input_tokens', 0),
                'cache_read': getattr(response.usage, 'cache_read_input_tokens', 0)
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse entity extraction response: {e}")
            return self._fallback_extraction(text)
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return self._fallback_extraction(text)

    def _build_extraction_prompt(
        self,
        text: str,
        classification: Optional[Dict]
    ) -> str:
        """Build entity extraction prompt"""

        # Truncate if needed but keep more text for entity extraction
        max_length = 50000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Document truncated...]"

        doc_type = classification.get('document_type', 'unknown') if classification else 'unknown'

        return f"""Extract ALL named entities from this legal document with high precision.

DOCUMENT TYPE: {doc_type}

DOCUMENT TEXT:
{text}

EXTRACTION REQUIREMENTS:

1. PEOPLE:
   - Full names (First Last, Title)
   - Roles/titles (Attorney, CEO, Plaintiff, etc.)
   - Confidence score for each
   - Context snippet showing where found

2. ORGANIZATIONS:
   - Company names (exact as written)
   - Entity types (LLC, Corp, Inc, etc.)
   - Law firms
   - Government entities
   - Confidence score and context

3. DATES:
   - All dates found (normalize to ISO format YYYY-MM-DD)
   - Date context (contract date, filing date, deadline, etc.)
   - Confidence score

4. MONETARY AMOUNTS:
   - Exact amounts with currency
   - Amount context (settlement, damages, price, etc.)
   - Normalized value in USD

5. LOCATIONS:
   - Cities, states, countries
   - Addresses (if present)
   - Jurisdictions
   - Venues

6. CASE IDENTIFIERS:
   - Case numbers
   - Docket numbers
   - Matter IDs

7. OTHER RELEVANT ENTITIES:
   - Email addresses
   - Phone numbers
   - Document references
   - Legal citations

OUTPUT FORMAT (valid JSON only):
{{
  "people": [
    {{
      "name": "John Smith",
      "title": "Senior Counsel",
      "role": "attorney",
      "confidence": 0.99,
      "context": "John Smith, Senior Counsel at...",
      "first_mention_position": 145
    }}
  ],
  "organizations": [
    {{
      "name": "Acme Corporation",
      "entity_type": "corporation",
      "confidence": 0.98,
      "context": "Acme Corporation, a Delaware corporation",
      "first_mention_position": 89
    }}
  ],
  "dates": [
    {{
      "date": "2024-03-15",
      "original_format": "March 15, 2024",
      "context": "settlement deadline",
      "confidence": 1.0,
      "position": 234
    }}
  ],
  "amounts": [
    {{
      "amount": "$2,500,000.00",
      "normalized_usd": 2500000.00,
      "context": "settlement amount",
      "confidence": 1.0,
      "position": 456
    }}
  ],
  "locations": [
    {{
      "location": "San Francisco, California",
      "type": "city_state",
      "confidence": 0.95,
      "context": "venue for trial",
      "position": 678
    }}
  ],
  "case_identifiers": [
    {{
      "identifier": "CV-2024-001",
      "type": "case_number",
      "confidence": 1.0,
      "context": "Case No. CV-2024-001",
      "position": 23
    }}
  ],
  "other_entities": [
    {{
      "type": "email",
      "value": "jsmith@lawfirm.com",
      "confidence": 1.0,
      "position": 123
    }}
  ],
  "extraction_summary": {{
    "total_entities": 15,
    "high_confidence_entities": 14,
    "needs_review": false
  }}
}}

CRITICAL RULES:
- Extract ONLY entities explicitly present in the text
- DO NOT infer or hallucinate entities
- Provide exact context snippets (20-50 chars around entity)
- Include position in document (character offset)
- Flag low confidence extractions (< 0.85)

Respond with ONLY the JSON object, no additional text."""

    def _validate_and_enrich_entities(
        self,
        result: Dict[str, Any],
        text: str
    ) -> Dict[str, Any]:
        """Validate and enrich extracted entities"""

        # Validate dates
        if 'dates' in result:
            validated_dates = []
            for date_entity in result['dates']:
                try:
                    # Verify date format
                    datetime.fromisoformat(date_entity['date'])
                    validated_dates.append(date_entity)
                except ValueError:
                    logger.warning(f"Invalid date format: {date_entity['date']}")
                    date_entity['confidence'] *= 0.5  # Reduce confidence
                    date_entity['validation_error'] = 'Invalid date format'
                    validated_dates.append(date_entity)
            result['dates'] = validated_dates

        # Validate monetary amounts
        if 'amounts' in result:
            for amount_entity in result['amounts']:
                # Verify normalized amount is numeric
                if 'normalized_usd' in amount_entity:
                    try:
                        float(amount_entity['normalized_usd'])
                    except (ValueError, TypeError):
                        amount_entity['normalized_usd'] = None
                        amount_entity['validation_error'] = 'Could not normalize amount'

        # Verify entities actually appear in text
        for entity_type in ['people', 'organizations', 'locations']:
            if entity_type in result:
                for entity in result[entity_type]:
                    name = entity.get('name', '') or entity.get('location', '')
                    if name and name not in text:
                        entity['confidence'] *= 0.7
                        entity['validation_warning'] = 'Entity name not found in exact form'

        # Calculate statistics
        total_entities = sum(
            len(result.get(key, []))
            for key in ['people', 'organizations', 'dates', 'amounts', 'locations', 'case_identifiers', 'other_entities']
        )

        high_confidence = sum(
            1 for key in ['people', 'organizations', 'dates', 'amounts', 'locations']
            for entity in result.get(key, [])
            if entity.get('confidence', 0) >= 0.85
        )

        result['extraction_summary'] = {
            'total_entities': total_entities,
            'high_confidence_entities': high_confidence,
            'needs_review': high_confidence < total_entities * 0.9
        }

        return result

    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using regex patterns"""

        result = {
            'people': [],
            'organizations': [],
            'dates': [],
            'amounts': [],
            'locations': [],
            'case_identifiers': [],
            'other_entities': [],
            'extraction_summary': {
                'total_entities': 0,
                'high_confidence_entities': 0,
                'needs_review': True,
                'fallback_used': True
            },
            'tokens_used': {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            }
        }

        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.finditer(email_pattern, text)
        for match in emails:
            result['other_entities'].append({
                'type': 'email',
                'value': match.group(),
                'confidence': 0.95,
                'position': match.start()
            })

        # Extract monetary amounts
        amount_pattern = r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?'
        amounts = re.finditer(amount_pattern, text)
        for match in amounts:
            amount_str = match.group()
            normalized = float(amount_str.replace('$', '').replace(',', ''))
            result['amounts'].append({
                'amount': amount_str,
                'normalized_usd': normalized,
                'context': 'unknown',
                'confidence': 0.7,
                'position': match.start()
            })

        # Extract case numbers
        case_pattern = r'\b(?:Case No\.|Case Number|Docket No\.)\s*([A-Z0-9-]+)\b'
        cases = re.finditer(case_pattern, text, re.IGNORECASE)
        for match in cases:
            result['case_identifiers'].append({
                'identifier': match.group(1),
                'type': 'case_number',
                'confidence': 0.8,
                'context': match.group(),
                'position': match.start()
            })

        result['extraction_summary']['total_entities'] = (
            len(result['amounts']) +
            len(result['other_entities']) +
            len(result['case_identifiers'])
        )

        return result
