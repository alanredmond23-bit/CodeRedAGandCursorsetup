#!/usr/bin/env python3
"""
Privilege Detector
Automatically detect attorney-client privilege in legal documents
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional
from pathlib import Path
from codered_client import CodeRedClient


class PrivilegeDetector:
    """Detect attorney-client privilege in documents"""

    # Privilege keywords with confidence weights
    KEYWORDS = {
        'high_confidence': {
            'attorney-client privilege': 0.9,
            'privileged and confidential': 0.9,
            'work product': 0.8,
            'trial strategy': 0.8,
            'settlement strategy': 0.8,
            'trial preparation': 0.7,
            'expert witness strategy': 0.7,
        },
        'medium_confidence': {
            'attorney': 0.3,
            'lawyer': 0.3,
            'legal counsel': 0.4,
            'confidential': 0.2,
            'privileged': 0.4,
            'counsel': 0.3,
        },
        'low_confidence': {
            'legal': 0.1,
            'law firm': 0.2,
            'legal advice': 0.3,
        }
    }

    # Patterns with weights
    PATTERNS = [
        {
            'name': 'attorney_email',
            'regex': r'\b\w+@\w+law\.\w+\b',
            'weight': 0.3,
            'description': 'Email from law firm domain'
        },
        {
            'name': 'attorney_header',
            'regex': r'(?i)(from|to):\s*.*\b(attorney|lawyer|counsel)\b',
            'weight': 0.4,
            'description': 'Email header with attorney/lawyer/counsel'
        },
        {
            'name': 'privilege_header',
            'regex': r'(?i)subject:.*\b(privileged|confidential|attorney)\b',
            'weight': 0.3,
            'description': 'Subject line with privilege keywords'
        },
        {
            'name': 'legal_letterhead',
            'regex': r'(?i)(law offices of|attorneys at law|legal counsel)',
            'weight': 0.4,
            'description': 'Legal letterhead pattern'
        },
        {
            'name': 'privilege_notice',
            'regex': r'(?i)this (email|communication|message) is (privileged|confidential)',
            'weight': 0.5,
            'description': 'Explicit privilege notice'
        },
    ]

    def __init__(self):
        """Initialize with CodeRed client"""
        self.codered = CodeRedClient()

    def detect(self, text: str) -> Dict[str, any]:
        """
        Detect privilege in text

        Args:
            text: Document text to analyze

        Returns:
            Dictionary with detection results
        """
        text_lower = text.lower()

        # Check keywords
        keywords_found = []
        keyword_score = 0.0

        for category, keywords in self.KEYWORDS.items():
            for keyword, weight in keywords.items():
                if keyword.lower() in text_lower:
                    keywords_found.append({
                        'keyword': keyword,
                        'category': category,
                        'weight': weight
                    })
                    keyword_score += weight

        # Check patterns
        patterns_found = []
        pattern_score = 0.0

        for pattern in self.PATTERNS:
            matches = re.findall(pattern['regex'], text, re.IGNORECASE)
            if matches:
                patterns_found.append({
                    'pattern': pattern['name'],
                    'description': pattern['description'],
                    'matches': matches[:3],  # First 3 matches
                    'count': len(matches),
                    'weight': pattern['weight']
                })
                pattern_score += pattern['weight']

        # Calculate overall confidence
        # Normalize scores (max keyword score ~3.0, max pattern score ~2.0)
        normalized_keyword = min(1.0, keyword_score / 3.0)
        normalized_pattern = min(1.0, pattern_score / 2.0)

        # Weighted combination (60% keywords, 40% patterns)
        confidence = (normalized_keyword * 0.6) + (normalized_pattern * 0.4)

        # Determine zone recommendation
        if confidence >= 0.7:
            recommendation = 'RED'
        elif confidence >= 0.4:
            recommendation = 'YELLOW'
        else:
            recommendation = 'GREEN'

        return {
            'is_privileged': confidence >= 0.5,
            'confidence': round(confidence, 3),
            'recommendation': recommendation,
            'keywords_found': keywords_found,
            'patterns_found': patterns_found,
            'keyword_score': round(normalized_keyword, 3),
            'pattern_score': round(normalized_pattern, 3),
        }

    def detect_file(self, file_path: str) -> Dict[str, any]:
        """
        Detect privilege in a file

        Args:
            file_path: Path to file

        Returns:
            Detection results with file metadata
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

            # Detect
            result = self.detect(text)

            # Add file metadata
            result['file_path'] = file_path
            result['file_name'] = Path(file_path).name
            result['file_size'] = len(text)

            return result
        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path
            }

    def flag_document(
        self,
        document_id: str,
        detection_result: Dict
    ) -> Dict[str, any]:
        """
        Flag document in database if privileged

        Args:
            document_id: Document identifier
            detection_result: Result from detect() or detect_file()

        Returns:
            Flagging result
        """
        if not detection_result.get('is_privileged'):
            return {
                'status': 'not_flagged',
                'reason': 'Not privileged (confidence below threshold)'
            }

        keywords_list = [
            kw['keyword'] for kw in detection_result.get('keywords_found', [])
        ]

        return self.codered.flag_privilege(
            document_id=document_id,
            confidence=detection_result['confidence'],
            keywords_found=keywords_list,
            recommendation=detection_result['recommendation']
        )

    def format_report(self, result: Dict) -> str:
        """
        Format detection result as readable report

        Args:
            result: Detection result

        Returns:
            Formatted report string
        """
        if 'error' in result:
            return f"❌ Error: {result['error']}"

        # Zone emoji
        zone_emoji = {
            'RED': '🔴',
            'YELLOW': '🟡',
            'GREEN': '🟢'
        }.get(result['recommendation'], '⚪')

        output = f"""
# PRIVILEGE DETECTION REPORT

**File**: {result.get('file_name', 'N/A')}
**Is Privileged**: {'YES' if result['is_privileged'] else 'NO'}
**Confidence**: {result['confidence']:.1%}
**Recommendation**: {zone_emoji} {result['recommendation']} ZONE

## Confidence Breakdown

- **Keyword Score**: {result['keyword_score']:.1%}
- **Pattern Score**: {result['pattern_score']:.1%}
- **Overall Confidence**: {result['confidence']:.1%}

"""

        # Keywords found
        if result.get('keywords_found'):
            output += "## Keywords Found\n\n"
            for kw in result['keywords_found']:
                output += f"- **{kw['keyword']}** ({kw['category']}, weight: {kw['weight']})\n"
            output += "\n"

        # Patterns found
        if result.get('patterns_found'):
            output += "## Patterns Detected\n\n"
            for pat in result['patterns_found']:
                output += f"- **{pat['pattern']}**: {pat['description']}\n"
                output += f"  - Matches: {pat['count']}\n"
                if pat['matches']:
                    output += f"  - Examples: {', '.join(pat['matches'])}\n"
            output += "\n"

        # Recommendation
        output += "## Recommendation\n\n"
        if result['recommendation'] == 'RED':
            output += """
🔴 **RED ZONE** - Highly Privileged

This document appears to contain attorney-client privileged communications
or attorney work product. Restrict access to:
- Architect agent
- Evidence agent
- Cynic agent

Requires senior attorney approval for any queries.
"""
        elif result['recommendation'] == 'YELLOW':
            output += """
🟡 **YELLOW ZONE** - Potentially Sensitive

This document may contain privileged or confidential information.
Exercise caution and review manually if uncertain.

Allowed agents: Architect, Code, Review, Evidence
"""
        else:
            output += """
🟢 **GREEN ZONE** - Public/Low Risk

This document does not appear to contain privileged information.
All agents may access.
"""

        return output


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Detect attorney-client privilege in documents')
    parser.add_argument('--file', required=True, help='File to analyze')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                        help='Output format')
    parser.add_argument('--flag', help='Document ID to flag in database if privileged')

    args = parser.parse_args()

    detector = PrivilegeDetector()

    # Detect privilege
    result = detector.detect_file(args.file)

    # Flag if requested
    if args.flag and result.get('is_privileged'):
        flag_result = detector.flag_document(args.flag, result)
        result['flag_result'] = flag_result

    # Output
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print(detector.format_report(result))


if __name__ == '__main__':
    main()
