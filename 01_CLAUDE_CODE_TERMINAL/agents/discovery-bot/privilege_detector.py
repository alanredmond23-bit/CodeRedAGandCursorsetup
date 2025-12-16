"""
Privilege Detector - Detect attorney-client privilege and work product with high confidence
"""

import json
import logging
from typing import Dict, Any, List, Optional
import anthropic

logger = logging.getLogger(__name__)


class PrivilegeDetector:
    """Detect privileged communications in legal documents"""

    # Privilege indicators
    ATTORNEY_TITLES = [
        'attorney', 'counsel', 'lawyer', 'esq', 'esquire',
        'legal counsel', 'general counsel', 'associate',
        'partner', 'solicitor', 'barrister'
    ]

    PRIVILEGE_MARKERS = [
        'attorney-client privilege',
        'attorney work product',
        'privileged and confidential',
        'legal advice',
        'in anticipation of litigation',
        'subject to privilege'
    ]

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.model = 'claude-sonnet-4-5-20250929'

    async def detect(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        entities: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Detect privilege with high confidence and detailed reasoning

        Args:
            text: Document text
            metadata: Document metadata
            entities: Extracted entities (helpful for identifying attorneys)

        Returns:
            Privilege determination with confidence and reasoning
        """
        try:
            # Quick heuristic check first
            heuristic_check = self._heuristic_privilege_check(text, metadata, entities)

            # If heuristic is very confident (either way), we can skip API call
            if heuristic_check['confidence'] > 0.95 or heuristic_check['confidence'] < 0.05:
                logger.info(f"Heuristic privilege check sufficient: {heuristic_check['is_privileged']} (confidence: {heuristic_check['confidence']})")
                return heuristic_check

            # Use Claude for complex cases
            prompt = self._build_privilege_prompt(text, metadata, entities)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.0,
                system=[
                    {
                        "type": "text",
                        "text": """You are an expert legal privilege reviewer with deep knowledge of:

- Attorney-client privilege requirements and exceptions
- Work product doctrine
- Common interest privilege
- Crime-fraud exception
- Waiver of privilege
- Federal Rules of Evidence 502

You analyze documents to determine if they are protected by privilege with extremely high accuracy. You understand that privilege determinations are critical and must be conservative - when in doubt, flag for attorney review.

You NEVER make hasty privilege determinations. You provide detailed reasoning.""",
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

            # Validate and enrich result
            result = self._validate_privilege_determination(result, heuristic_check)

            # Add usage statistics
            result['tokens_used'] = {
                'input': response.usage.input_tokens,
                'output': response.usage.output_tokens,
                'cache_creation': getattr(response.usage, 'cache_creation_input_tokens', 0),
                'cache_read': getattr(response.usage, 'cache_read_input_tokens', 0)
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse privilege detection response: {e}")
            return self._conservative_privilege_response(text, metadata)
        except Exception as e:
            logger.error(f"Privilege detection error: {e}")
            return self._conservative_privilege_response(text, metadata)

    def _build_privilege_prompt(
        self,
        text: str,
        metadata: Optional[Dict],
        entities: Optional[Dict]
    ) -> str:
        """Build privilege detection prompt"""

        # Truncate text if very long
        max_length = 20000
        if len(text) > max_length:
            text = text[:max_length] + "\n\n[Document truncated...]"

        metadata_str = ""
        if metadata:
            metadata_str = f"\n\nMETADATA:\n{json.dumps(metadata, indent=2)}"

        entities_str = ""
        if entities and 'people' in entities:
            people = [p['name'] for p in entities['people'][:10]]  # Top 10
            entities_str = f"\n\nKEY PEOPLE IDENTIFIED:\n{json.dumps(people, indent=2)}"

        return f"""Analyze this document for attorney-client privilege or work product protection.

DOCUMENT TEXT:
{text}
{metadata_str}
{entities_str}

PRIVILEGE ANALYSIS REQUIREMENTS:

1. Determine if document is privileged (attorney-client or work product)

2. Identify privilege type:
   - attorney_client: Communication between attorney and client for legal advice
   - work_product: Materials prepared in anticipation of litigation
   - common_interest: Shared privilege among parties with common legal interest
   - none: Not privileged

3. Confidence score (0.0 to 1.0):
   - 1.0: Absolutely certain (explicit privilege markers)
   - 0.9-0.99: Very confident (clear indicators)
   - 0.7-0.89: Confident (multiple indicators)
   - 0.5-0.69: Moderate (some indicators, needs review)
   - Below 0.5: Not privileged or insufficient indicators

4. Identify privilege indicators found:
   - Attorney participation (who)
   - Legal advice being provided
   - Confidentiality markers
   - Purpose of communication
   - Anticipation of litigation

5. Identify any privilege exceptions or concerns:
   - Crime-fraud exception
   - Waiver (forwarded to third party, etc.)
   - Business advice vs legal advice
   - Not confidential

6. Provide detailed reasoning

7. Recommend if attorney review is needed

OUTPUT FORMAT (valid JSON only):
{{
  "is_privileged": true,
  "privilege_types": ["attorney_client"],
  "confidence": 0.95,
  "privilege_indicators": [
    {{
      "indicator": "Communication from attorney to client",
      "evidence": "From: John Smith, Senior Counsel",
      "weight": "strong"
    }},
    {{
      "indicator": "Explicit privilege claim",
      "evidence": "CONFIDENTIAL ATTORNEY-CLIENT COMMUNICATION",
      "weight": "strong"
    }},
    {{
      "indicator": "Legal advice provided",
      "evidence": "This email contains my legal advice regarding...",
      "weight": "strong"
    }}
  ],
  "privilege_concerns": [
    {{
      "concern": "None identified",
      "severity": "none"
    }}
  ],
  "participants": {{
    "attorneys": ["John Smith, Senior Counsel"],
    "clients": ["Sarah Johnson, CEO"],
    "third_parties": []
  }},
  "reasoning": "This document is clearly privileged attorney-client communication. It contains: (1) communication from attorney (John Smith, Senior Counsel) to client (Sarah Johnson, CEO), (2) explicit privilege header 'CONFIDENTIAL ATTORNEY-CLIENT COMMUNICATION', (3) legal advice regarding litigation strategy and settlement recommendations, (4) request to maintain confidentiality. No waiver or exceptions identified.",
  "needs_attorney_review": false,
  "review_reason": null,
  "redaction_recommended": true,
  "redaction_scope": "entire document"
}}

CRITICAL RULES:
- Be CONSERVATIVE - when in doubt, flag as potentially privileged
- Require BOTH attorney participation AND legal advice for attorney-client privilege
- Work product requires anticipation of litigation
- Identify any third-party recipients (may waive privilege)
- Flag crime-fraud exception if suspected
- Consider context and purpose of communication

Respond with ONLY the JSON object, no additional text."""

    def _heuristic_privilege_check(
        self,
        text: str,
        metadata: Optional[Dict],
        entities: Optional[Dict]
    ) -> Dict[str, Any]:
        """Fast heuristic privilege check"""

        text_lower = text.lower()
        score = 0.0
        indicators = []
        concerns = []

        # Check for explicit privilege markers (very strong indicator)
        for marker in self.PRIVILEGE_MARKERS:
            if marker in text_lower:
                score += 0.4
                indicators.append({
                    'indicator': f"Explicit privilege marker: '{marker}'",
                    'evidence': marker,
                    'weight': 'strong'
                })

        # Check for attorney participation
        has_attorney = False
        if entities and 'people' in entities:
            for person in entities['people']:
                title = person.get('title', '').lower()
                role = person.get('role', '').lower()
                if any(atty in title or atty in role for atty in self.ATTORNEY_TITLES):
                    has_attorney = True
                    score += 0.2
                    indicators.append({
                        'indicator': 'Attorney participant identified',
                        'evidence': person['name'],
                        'weight': 'moderate'
                    })
                    break

        # Check text for attorney indicators
        if not has_attorney:
            for title in self.ATTORNEY_TITLES:
                if title in text_lower:
                    has_attorney = True
                    score += 0.15
                    indicators.append({
                        'indicator': f"Attorney title found: '{title}'",
                        'evidence': title,
                        'weight': 'moderate'
                    })
                    break

        # Check for legal advice language
        legal_advice_terms = [
            'legal advice', 'my recommendation', 'legal opinion',
            'litigation strategy', 'settlement', 'legal analysis'
        ]
        for term in legal_advice_terms:
            if term in text_lower:
                score += 0.15
                indicators.append({
                    'indicator': f"Legal advice language: '{term}'",
                    'evidence': term,
                    'weight': 'moderate'
                })
                break

        # Check for confidentiality markers
        confidentiality_terms = [
            'confidential', 'privileged', 'do not forward',
            'attorney eyes only', 'not for distribution'
        ]
        for term in confidentiality_terms:
            if term in text_lower:
                score += 0.1
                indicators.append({
                    'indicator': f"Confidentiality marker: '{term}'",
                    'evidence': term,
                    'weight': 'weak'
                })
                break

        # Check for privilege concerns
        # Third party recipients
        if 'cc:' in text_lower or 'bcc:' in text_lower:
            concerns.append({
                'concern': 'Document may have third-party recipients (check CC/BCC)',
                'severity': 'moderate'
            })

        # Business vs legal
        business_terms = ['sales', 'marketing', 'operational', 'business plan']
        if any(term in text_lower for term in business_terms):
            concerns.append({
                'concern': 'Document may contain business advice rather than legal advice',
                'severity': 'moderate'
            })
            score -= 0.1

        # Cap score between 0 and 1
        score = max(0.0, min(1.0, score))

        return {
            'is_privileged': score >= 0.5,
            'privilege_types': ['attorney_client'] if score >= 0.5 else [],
            'confidence': score,
            'privilege_indicators': indicators,
            'privilege_concerns': concerns if concerns else [{'concern': 'None identified', 'severity': 'none'}],
            'participants': {'attorneys': [], 'clients': [], 'third_parties': []},
            'reasoning': 'Heuristic privilege analysis based on keyword and pattern matching.',
            'needs_attorney_review': 0.3 < score < 0.7,  # Flag borderline cases
            'review_reason': 'Borderline privilege determination' if 0.3 < score < 0.7 else None,
            'redaction_recommended': score >= 0.5,
            'redaction_scope': 'entire document' if score >= 0.8 else 'partial',
            'method': 'heuristic',
            'tokens_used': {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            }
        }

    def _validate_privilege_determination(
        self,
        result: Dict[str, Any],
        heuristic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate privilege determination and cross-check with heuristic"""

        # If AI and heuristic strongly disagree, flag for review
        ai_privileged = result.get('is_privileged', False)
        heuristic_privileged = heuristic.get('is_privileged', False)
        ai_confidence = result.get('confidence', 0.5)
        heuristic_confidence = heuristic.get('confidence', 0.5)

        if ai_privileged != heuristic_privileged:
            if ai_confidence > 0.7 and heuristic_confidence > 0.7:
                result['needs_attorney_review'] = True
                result['review_reason'] = 'AI and heuristic analysis disagree on privilege determination'
                result['disagreement'] = {
                    'ai_determination': ai_privileged,
                    'ai_confidence': ai_confidence,
                    'heuristic_determination': heuristic_privileged,
                    'heuristic_confidence': heuristic_confidence
                }

        # Conservative approach: if either says privileged with high confidence, treat as privileged
        if not ai_privileged and heuristic_privileged and heuristic_confidence > 0.85:
            result['is_privileged'] = True
            result['needs_attorney_review'] = True
            result['review_reason'] = 'Heuristic analysis suggests privilege; AI disagreed'

        return result

    def _conservative_privilege_response(
        self,
        text: str,
        metadata: Optional[Dict]
    ) -> Dict[str, Any]:
        """Conservative response when analysis fails - assume potential privilege"""

        text_lower = text.lower()

        # Check for any privilege markers
        has_privilege_marker = any(marker in text_lower for marker in self.PRIVILEGE_MARKERS)

        return {
            'is_privileged': has_privilege_marker,
            'privilege_types': ['unknown'] if has_privilege_marker else [],
            'confidence': 0.3,
            'privilege_indicators': [
                {
                    'indicator': 'Analysis failed - conservative determination',
                    'evidence': 'Privilege detection API failed',
                    'weight': 'unknown'
                }
            ],
            'privilege_concerns': [
                {
                    'concern': 'Privilege analysis failed - requires manual review',
                    'severity': 'high'
                }
            ],
            'participants': {'attorneys': [], 'clients': [], 'third_parties': []},
            'reasoning': 'Privilege detection analysis failed. Conservative approach: flagging for attorney review.',
            'needs_attorney_review': True,
            'review_reason': 'Privilege detection API failed',
            'redaction_recommended': has_privilege_marker,
            'redaction_scope': 'requires review',
            'error': True,
            'tokens_used': {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            }
        }
