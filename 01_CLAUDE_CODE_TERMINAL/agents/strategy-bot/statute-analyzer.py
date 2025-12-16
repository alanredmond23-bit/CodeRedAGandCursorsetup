"""
Statute Analyzer Module

Analyzes applicable statutes, regulations, and rules.
Identifies statutory requirements, elements, and defenses.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StatuteType(Enum):
    """Types of statutory authority"""
    STATUTE = "statute"
    REGULATION = "regulation"
    RULE_OF_COURT = "rule_of_court"
    CONSTITUTIONAL = "constitutional"
    LOCAL_RULE = "local_rule"


@dataclass
class StatuteAnalysis:
    """Analysis of a statute"""
    statute: Dict
    statute_type: StatuteType
    applicability: str  # "directly_applicable", "partially_applicable", "not_applicable"
    elements: List[str]
    requirements: List[str]
    defenses: List[str]
    case_law_interpretation: List[Dict]
    our_compliance: Dict  # Which elements we satisfy


class StatuteAnalyzer:
    """
    Analyzes applicable statutes and regulations
    """

    def __init__(self):
        """Initialize statute analyzer"""
        self.statute_database = self._load_statute_database()

    def find_applicable_statutes(self, case_type: Any, jurisdiction: Any,
                                legal_issues: List[str]) -> List[Dict]:
        """
        Find statutes applicable to case

        Args:
            case_type: Type of case (custody, criminal, etc.)
            jurisdiction: Jurisdiction (federal, state)
            legal_issues: List of legal issues

        Returns:
            List of statute dictionaries
        """
        logger.info(f"Finding applicable statutes for {case_type.value} in {jurisdiction.value}")

        statutes = []

        # Get statutes from database based on case type
        case_type_statutes = self.statute_database.get(case_type.value, {}).get(
            jurisdiction.value, []
        )
        statutes.extend(case_type_statutes)

        # Get statutes based on legal issues
        for issue in legal_issues:
            issue_statutes = self._find_statutes_for_issue(issue, jurisdiction.value)
            statutes.extend(issue_statutes)

        # Remove duplicates
        unique_statutes = self._deduplicate_statutes(statutes)

        logger.info(f"Found {len(unique_statutes)} applicable statutes")
        return unique_statutes

    def analyze_statute(self, statute: Dict, case_facts: Any) -> StatuteAnalysis:
        """
        Analyze a single statute for applicability

        Args:
            statute: Statute dictionary
            case_facts: Current case facts

        Returns:
            StatuteAnalysis object
        """
        # Determine statute type
        statute_type = self._determine_statute_type(statute)

        # Determine applicability
        applicability = self._assess_applicability(statute, case_facts)

        # Extract elements
        elements = self._extract_elements(statute)

        # Extract requirements
        requirements = self._extract_requirements(statute)

        # Identify defenses
        defenses = self._identify_defenses(statute)

        # Find case law interpreting statute
        case_law = []  # Would query research modules

        # Assess our compliance
        compliance = self._assess_compliance(elements, requirements, case_facts)

        return StatuteAnalysis(
            statute=statute,
            statute_type=statute_type,
            applicability=applicability,
            elements=elements,
            requirements=requirements,
            defenses=defenses,
            case_law_interpretation=case_law,
            our_compliance=compliance
        )

    def _load_statute_database(self) -> Dict:
        """
        Load database of common statutes by case type

        In production, this would be a comprehensive database
        """
        return {
            'custody': {
                'california': [
                    {
                        'citation': 'Cal. Fam. Code § 3011',
                        'title': 'Best Interest of Child Factors',
                        'text': 'Court shall consider: health, safety, and welfare of child; any history of abuse; nature and amount of contact with both parents; habitual or continual illegal use of controlled substances; etc.',
                        'jurisdiction': 'California',
                        'effective_date': '1993-01-01',
                        'type': 'statute'
                    },
                    {
                        'citation': 'Cal. Fam. Code § 3020',
                        'title': 'Joint Custody Policy',
                        'text': 'Joint custody preferred to assure child frequent and continuing contact with both parents',
                        'jurisdiction': 'California',
                        'effective_date': '1980-01-01',
                        'type': 'statute'
                    },
                    {
                        'citation': 'Cal. Fam. Code § 3044',
                        'title': 'Domestic Violence Custody Presumption',
                        'text': 'Perpetrator of domestic violence presumed not to have custody',
                        'jurisdiction': 'California',
                        'effective_date': '1997-01-01',
                        'type': 'statute'
                    }
                ],
                'federal': []
            },
            'federal_criminal': {
                'federal': [
                    {
                        'citation': '18 U.S.C. § 3553',
                        'title': 'Sentencing Factors',
                        'text': 'Court shall impose sentence sufficient but not greater than necessary',
                        'jurisdiction': 'Federal',
                        'effective_date': '1984-11-01',
                        'type': 'statute'
                    },
                    {
                        'citation': 'USSG § 1B1.1',
                        'title': 'Application of Guidelines',
                        'text': 'Sentencing guidelines application instructions',
                        'jurisdiction': 'Federal',
                        'effective_date': '1987-11-01',
                        'type': 'guideline'
                    }
                ]
            },
            'bankruptcy': {
                'federal': [
                    {
                        'citation': '11 U.S.C. § 522',
                        'title': 'Exemptions',
                        'text': 'Property that debtor may exempt from estate',
                        'jurisdiction': 'Federal',
                        'effective_date': '1978-11-06',
                        'type': 'statute'
                    },
                    {
                        'citation': '11 U.S.C. § 362',
                        'title': 'Automatic Stay',
                        'text': 'Petition operates as stay of various actions',
                        'jurisdiction': 'Federal',
                        'effective_date': '1978-11-06',
                        'type': 'statute'
                    }
                ]
            }
        }

    def _find_statutes_for_issue(self, issue: str, jurisdiction: str) -> List[Dict]:
        """Find statutes related to specific legal issue"""
        statutes = []
        issue_lower = issue.lower()

        # Custody-related issues
        if 'best interest' in issue_lower:
            statutes.append({
                'citation': 'Cal. Fam. Code § 3011' if 'california' in jurisdiction else 'State Code § XXX',
                'title': 'Best Interest Factors',
                'text': 'Statutory factors for determining best interest of child',
                'jurisdiction': jurisdiction,
                'type': 'statute'
            })

        if 'substance abuse' in issue_lower:
            statutes.append({
                'citation': 'Cal. Fam. Code § 3011(d)' if 'california' in jurisdiction else 'State Code § XXX',
                'title': 'Habitual Substance Abuse Factor',
                'text': 'Habitual or continual illegal use of controlled substances or alcohol',
                'jurisdiction': jurisdiction,
                'type': 'statute'
            })

        if 'domestic violence' in issue_lower:
            statutes.append({
                'citation': 'Cal. Fam. Code § 3044' if 'california' in jurisdiction else 'State Code § XXX',
                'title': 'Domestic Violence Presumption',
                'text': 'Rebuttable presumption against custody for DV perpetrator',
                'jurisdiction': jurisdiction,
                'type': 'statute'
            })

        return statutes

    def _deduplicate_statutes(self, statutes: List[Dict]) -> List[Dict]:
        """Remove duplicate statutes"""
        seen = set()
        unique = []

        for statute in statutes:
            citation = statute.get('citation', '')
            if citation and citation not in seen:
                seen.add(citation)
                unique.append(statute)

        return unique

    def _determine_statute_type(self, statute: Dict) -> StatuteType:
        """Determine type of statutory authority"""
        statute_type = statute.get('type', '').lower()

        if 'regulation' in statute_type or 'cfr' in statute_type:
            return StatuteType.REGULATION
        elif 'rule' in statute_type:
            return StatuteType.RULE_OF_COURT
        elif 'constitution' in statute_type:
            return StatuteType.CONSTITUTIONAL
        else:
            return StatuteType.STATUTE

    def _assess_applicability(self, statute: Dict, case_facts: Any) -> str:
        """Assess whether statute applies to our case"""
        # Simplified assessment - would be more detailed in production

        statute_text = statute.get('text', '').lower()
        our_facts = case_facts.facts_summary.lower()

        # Check for keyword matches
        keywords = set(statute_text.split()) & set(our_facts.split())

        if len(keywords) > 10:
            return "directly_applicable"
        elif len(keywords) > 5:
            return "partially_applicable"
        else:
            return "potentially_applicable"

    def _extract_elements(self, statute: Dict) -> List[str]:
        """
        Extract legal elements from statute

        Elements are the required components that must be proven
        """
        elements = []
        text = statute.get('text', '')

        # Look for numbered elements
        import re
        numbered = re.findall(r'\((\d+)\)\s*([^;.]+)', text)
        elements.extend([item[1].strip() for item in numbered])

        # Look for lettered elements
        lettered = re.findall(r'\(([a-z])\)\s*([^;.]+)', text)
        elements.extend([item[1].strip() for item in lettered])

        # Look for keyword patterns
        patterns = [
            r'shall (?:prove|establish|show) ([^;.]+)',
            r'requires ([^;.]+)',
            r'must ([^;.]+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            elements.extend(matches)

        return elements[:10]  # Limit to top 10

    def _extract_requirements(self, statute: Dict) -> List[str]:
        """Extract procedural and substantive requirements"""
        requirements = []
        text = statute.get('text', '')

        # Look for requirement patterns
        import re
        patterns = [
            r'shall ([^;.]+)',
            r'must ([^;.]+)',
            r'required to ([^;.]+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            requirements.extend(matches)

        return requirements[:10]

    def _identify_defenses(self, statute: Dict) -> List[str]:
        """Identify statutory defenses or exceptions"""
        defenses = []
        text = statute.get('text', '').lower()

        # Look for defense/exception language
        import re
        patterns = [
            r'unless ([^;.]+)',
            r'except ([^;.]+)',
            r'does not apply (?:if|when) ([^;.]+)',
            r'defense (?:if|that) ([^;.]+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            defenses.extend(matches)

        return defenses

    def _assess_compliance(self, elements: List[str], requirements: List[str],
                          case_facts: Any) -> Dict:
        """
        Assess whether our case satisfies statutory elements/requirements

        Args:
            elements: List of statutory elements
            requirements: List of statutory requirements
            case_facts: Our case facts

        Returns:
            Dictionary showing compliance status
        """
        compliance = {
            'satisfied_elements': [],
            'unsatisfied_elements': [],
            'uncertain_elements': [],
            'overall_compliance': 'unknown'
        }

        our_facts_lower = case_facts.facts_summary.lower()

        # Check each element
        for element in elements:
            element_keywords = set(element.lower().split())

            # Simple keyword matching
            if any(keyword in our_facts_lower for keyword in element_keywords):
                compliance['satisfied_elements'].append(element)
            else:
                compliance['uncertain_elements'].append(element)

        # Determine overall compliance
        total_elements = len(elements)
        if total_elements == 0:
            compliance['overall_compliance'] = 'unknown'
        else:
            satisfied_pct = len(compliance['satisfied_elements']) / total_elements

            if satisfied_pct >= 0.8:
                compliance['overall_compliance'] = 'likely_compliant'
            elif satisfied_pct >= 0.5:
                compliance['overall_compliance'] = 'partially_compliant'
            else:
                compliance['overall_compliance'] = 'likely_noncompliant'

        return compliance

    def generate_statute_memo(self, statutes: List[Dict], case_facts: Any) -> str:
        """
        Generate memo section on applicable statutes

        Args:
            statutes: List of statute dictionaries
            case_facts: Case facts

        Returns:
            Formatted memo text
        """
        memo = "APPLICABLE STATUTES AND REGULATIONS\n\n"

        for statute in statutes:
            analysis = self.analyze_statute(statute, case_facts)

            memo += f"Statute: {statute.get('citation')}\n"
            memo += f"Title: {statute.get('title')}\n"
            memo += f"Applicability: {analysis.applicability.upper()}\n\n"

            if analysis.elements:
                memo += "Elements:\n"
                for i, element in enumerate(analysis.elements, 1):
                    memo += f"  {i}. {element}\n"
                memo += "\n"

            if analysis.requirements:
                memo += "Requirements:\n"
                for req in analysis.requirements:
                    memo += f"  - {req}\n"
                memo += "\n"

            memo += f"Our Compliance: {analysis.our_compliance['overall_compliance'].upper()}\n"

            if analysis.our_compliance['satisfied_elements']:
                memo += "  Satisfied Elements:\n"
                for elem in analysis.our_compliance['satisfied_elements']:
                    memo += f"    ✓ {elem}\n"

            if analysis.our_compliance['uncertain_elements']:
                memo += "  Elements Needing Further Evidence:\n"
                for elem in analysis.our_compliance['uncertain_elements']:
                    memo += f"    ? {elem}\n"

            memo += "\n" + "=" * 70 + "\n\n"

        return memo
