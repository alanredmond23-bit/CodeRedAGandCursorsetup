"""
Precedent Analyzer Module

Analyzes case law precedents for applicability to current case.
Evaluates binding vs. persuasive authority, factual similarity, and legal principles.
"""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class AuthorityType(Enum):
    """Types of precedential authority"""
    BINDING = "binding"  # Same jurisdiction, must follow
    PERSUASIVE = "persuasive"  # Different jurisdiction, may follow
    DISTINGUISHABLE = "distinguishable"  # Different facts, limited applicability
    OVERRULED = "overruled"  # No longer good law
    SUPERSEDED = "superseded"  # Superseded by statute


class Strength(Enum):
    """Strength of precedent"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"


@dataclass
class PrecedentAnalysis:
    """Analysis result for a single precedent"""
    case: Dict
    authority_type: AuthorityType
    strength: Strength
    similarity_score: float  # 0.0 to 1.0
    key_holdings: List[str]
    applicable_rules: List[str]
    factual_similarities: List[str]
    factual_differences: List[str]
    reasons_to_follow: List[str]
    reasons_to_distinguish: List[str]
    excerpt_quotes: List[str]


class PrecedentAnalyzer:
    """
    Analyzes case law precedents for applicability and strength
    """

    def __init__(self):
        """Initialize precedent analyzer"""
        self.court_hierarchy = self._build_court_hierarchy()

    def analyze(self, cases: List[Dict], case_facts: Any) -> Dict:
        """
        Analyze list of cases for precedential value

        Args:
            cases: List of case dictionaries from research
            case_facts: CaseFacts object with current case details

        Returns:
            Dictionary with categorized precedent analysis
        """
        logger.info(f"Analyzing {len(cases)} precedents")

        analyzed = []
        for case in cases:
            analysis = self._analyze_single_case(case, case_facts)
            analyzed.append(analysis)

        # Categorize by authority type and strength
        categorized = self._categorize_precedents(analyzed)

        return {
            'total_analyzed': len(analyzed),
            'binding_precedents': categorized['binding'],
            'persuasive_precedents': categorized['persuasive'],
            'distinguishable_precedents': categorized['distinguishable'],
            'all_analyses': analyzed,
            'summary': self._generate_summary(categorized)
        }

    def _analyze_single_case(self, case: Dict, case_facts: Any) -> PrecedentAnalysis:
        """
        Analyze a single case for precedential value

        Args:
            case: Case dictionary
            case_facts: Current case facts

        Returns:
            PrecedentAnalysis object
        """
        # Determine authority type
        authority_type = self._determine_authority_type(
            case.get('jurisdiction'),
            case.get('court'),
            case_facts.jurisdiction.value
        )

        # Calculate similarity score
        similarity_score = self._calculate_similarity(case, case_facts)

        # Determine strength
        strength = self._determine_strength(case, authority_type, similarity_score)

        # Extract key holdings
        key_holdings = self._extract_holdings(case)

        # Extract applicable rules
        applicable_rules = self._extract_rules(case, case_facts)

        # Identify similarities and differences
        similarities, differences = self._compare_facts(case, case_facts)

        # Generate reasons to follow or distinguish
        reasons_follow = self._generate_reasons_to_follow(
            case, authority_type, similarity_score, similarities
        )
        reasons_distinguish = self._generate_reasons_to_distinguish(
            case, differences, authority_type
        )

        # Extract key quotes
        quotes = self._extract_key_quotes(case)

        return PrecedentAnalysis(
            case=case,
            authority_type=authority_type,
            strength=strength,
            similarity_score=similarity_score,
            key_holdings=key_holdings,
            applicable_rules=applicable_rules,
            factual_similarities=similarities,
            factual_differences=differences,
            reasons_to_follow=reasons_follow,
            reasons_to_distinguish=reasons_distinguish,
            excerpt_quotes=quotes
        )

    def _determine_authority_type(self, case_jurisdiction: str,
                                  case_court: str, our_jurisdiction: str) -> AuthorityType:
        """
        Determine if case is binding or persuasive authority

        Args:
            case_jurisdiction: Jurisdiction of precedent
            case_court: Court that decided precedent
            our_jurisdiction: Our case's jurisdiction

        Returns:
            AuthorityType enum
        """
        # Supreme Court is binding on all federal cases
        if case_court and 'Supreme Court' in case_court and 'United States' in case_court:
            if our_jurisdiction == 'federal':
                return AuthorityType.BINDING

        # Same jurisdiction and higher/same level court = binding
        if case_jurisdiction and case_jurisdiction.lower() in our_jurisdiction.lower():
            if self._is_binding_court(case_court, our_jurisdiction):
                return AuthorityType.BINDING

        # Different jurisdiction = persuasive
        return AuthorityType.PERSUASIVE

    def _is_binding_court(self, court: str, jurisdiction: str) -> bool:
        """Check if court is binding in jurisdiction"""
        if not court:
            return False

        court_lower = court.lower()

        # Supreme courts are binding
        if 'supreme court' in court_lower:
            return True

        # Courts of appeal are binding (in most jurisdictions)
        if 'court of appeal' in court_lower or 'appellate' in court_lower:
            return True

        # District/trial courts are persuasive only
        return False

    def _calculate_similarity(self, case: Dict, case_facts: Any) -> float:
        """
        Calculate factual similarity score (0.0 to 1.0)

        Args:
            case: Precedent case
            case_facts: Our case facts

        Returns:
            Similarity score
        """
        score = 0.0
        factors = 0

        # Case type similarity
        if case_facts.case_type.value in case.get('summary', '').lower():
            score += 0.3
        factors += 1

        # Legal issue overlap
        case_text = (case.get('summary', '') + ' ' + ' '.join(case.get('headnotes', []))).lower()
        issue_matches = 0
        for issue in case_facts.legal_issues:
            if issue.lower() in case_text:
                issue_matches += 1

        if case_facts.legal_issues:
            score += (issue_matches / len(case_facts.legal_issues)) * 0.4
            factors += 1

        # Recency (newer cases weighted higher)
        case_year = case.get('year', 0)
        if case_year >= 2020:
            score += 0.2
        elif case_year >= 2010:
            score += 0.15
        elif case_year >= 2000:
            score += 0.1
        elif case_year >= 1990:
            score += 0.05
        factors += 1

        # Relevance score from search
        if 'relevance_score' in case:
            score += case['relevance_score'] * 0.1
            factors += 1

        return min(score, 1.0)

    def _determine_strength(self, case: Dict, authority_type: AuthorityType,
                           similarity_score: float) -> Strength:
        """
        Determine overall strength of precedent

        Args:
            case: Case dictionary
            authority_type: Binding or persuasive
            similarity_score: Factual similarity

        Returns:
            Strength enum
        """
        # Binding authority is generally stronger
        if authority_type == AuthorityType.BINDING:
            if similarity_score >= 0.8:
                return Strength.VERY_STRONG
            elif similarity_score >= 0.6:
                return Strength.STRONG
            elif similarity_score >= 0.4:
                return Strength.MODERATE
            else:
                return Strength.WEAK

        # Persuasive authority
        else:
            if similarity_score >= 0.9:
                return Strength.STRONG
            elif similarity_score >= 0.7:
                return Strength.MODERATE
            elif similarity_score >= 0.5:
                return Strength.WEAK
            else:
                return Strength.VERY_WEAK

    def _extract_holdings(self, case: Dict) -> List[str]:
        """
        Extract key legal holdings from case

        Args:
            case: Case dictionary

        Returns:
            List of holding statements
        """
        holdings = []

        # Extract from headnotes (most reliable)
        if 'headnotes' in case:
            holdings.extend(case['headnotes'][:5])  # Top 5 headnotes

        # Extract from summary if available
        if 'summary' in case and case['summary']:
            # Simple extraction - look for holding language
            summary = case['summary']
            holding_patterns = [
                r'held that ([^.]+)',
                r'holding that ([^.]+)',
                r'ruled that ([^.]+)',
                r'found that ([^.]+)',
                r'concluded that ([^.]+)'
            ]

            for pattern in holding_patterns:
                matches = re.findall(pattern, summary, re.IGNORECASE)
                holdings.extend(matches)

        return holdings[:10]  # Limit to top 10

    def _extract_rules(self, case: Dict, case_facts: Any) -> List[str]:
        """
        Extract applicable legal rules from case

        Args:
            case: Case dictionary
            case_facts: Our case facts

        Returns:
            List of legal rules
        """
        rules = []

        # Look for rule statements in headnotes and summary
        text = case.get('summary', '') + ' ' + ' '.join(case.get('headnotes', []))

        # Common rule patterns
        rule_patterns = [
            r'standard (?:is|requires) ([^.]+)',
            r'test (?:is|requires) ([^.]+)',
            r'factors? (?:include|are) ([^.]+)',
            r'elements? (?:are|include) ([^.]+)',
            r'requirement (?:is|that) ([^.]+)',
            r'burden (?:is|requires) ([^.]+)'
        ]

        for pattern in rule_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rules.extend(matches)

        return rules[:8]

    def _compare_facts(self, case: Dict, case_facts: Any) -> Tuple[List[str], List[str]]:
        """
        Compare facts of precedent to our case

        Args:
            case: Precedent case
            case_facts: Our case facts

        Returns:
            Tuple of (similarities, differences)
        """
        similarities = []
        differences = []

        # This is simplified - in production would use NLP/ML
        case_text = case.get('summary', '').lower()
        our_facts = case_facts.facts_summary.lower()

        # Look for common keywords
        case_words = set(case_text.split())
        our_words = set(our_facts.split())

        # Common substantive words (excluding stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        common_words = (case_words & our_words) - stop_words

        if len(common_words) > 5:
            similarities.append(f"Similar fact patterns with {len(common_words)} common elements")

        # Case type
        if case_facts.case_type.value in case_text:
            similarities.append(f"Both involve {case_facts.case_type.value} matters")

        # This would be much more sophisticated in production
        return similarities, differences

    def _generate_reasons_to_follow(self, case: Dict, authority_type: AuthorityType,
                                   similarity_score: float, similarities: List[str]) -> List[str]:
        """Generate reasons why this precedent should be followed"""
        reasons = []

        if authority_type == AuthorityType.BINDING:
            reasons.append("Binding precedent in same jurisdiction")

        if similarity_score >= 0.8:
            reasons.append("Highly similar factual circumstances")

        if case.get('court') and 'Supreme Court' in case.get('court'):
            reasons.append("Decided by highest court")

        if case.get('year', 0) >= 2020:
            reasons.append("Recent precedent reflecting current law")

        if similarities:
            reasons.append(f"Factual similarities: {len(similarities)} identified")

        return reasons

    def _generate_reasons_to_distinguish(self, case: Dict, differences: List[str],
                                        authority_type: AuthorityType) -> List[str]:
        """Generate reasons why this precedent could be distinguished"""
        reasons = []

        if authority_type == AuthorityType.PERSUASIVE:
            reasons.append("Persuasive authority only - not binding")

        if differences:
            reasons.extend(differences)

        if case.get('year', 0) < 1990:
            reasons.append("Older precedent - legal landscape may have evolved")

        return reasons

    def _extract_key_quotes(self, case: Dict) -> List[str]:
        """Extract quotable excerpts from case"""
        quotes = []

        # From headnotes (already extracted points)
        if 'headnotes' in case:
            quotes.extend(case['headnotes'][:3])

        # Would extract from full text in production
        # For now, use summary excerpts
        summary = case.get('summary', '')
        if summary and len(summary) > 50:
            quotes.append(summary[:200] + "...")

        return quotes

    def _categorize_precedents(self, analyses: List[PrecedentAnalysis]) -> Dict:
        """Categorize precedents by type and strength"""
        categorized = {
            'binding': [],
            'persuasive': [],
            'distinguishable': []
        }

        for analysis in analyses:
            if analysis.authority_type == AuthorityType.BINDING:
                categorized['binding'].append(analysis)
            elif analysis.authority_type == AuthorityType.PERSUASIVE:
                categorized['persuasive'].append(analysis)
            else:
                categorized['distinguishable'].append(analysis)

        # Sort each category by strength/similarity
        for category in categorized:
            categorized[category].sort(
                key=lambda x: (x.strength.value, x.similarity_score),
                reverse=True
            )

        return categorized

    def _generate_summary(self, categorized: Dict) -> str:
        """Generate summary of precedent analysis"""
        binding_count = len(categorized['binding'])
        persuasive_count = len(categorized['persuasive'])
        distinguishable_count = len(categorized['distinguishable'])

        summary = f"Found {binding_count} binding precedents, "
        summary += f"{persuasive_count} persuasive precedents, "
        summary += f"and {distinguishable_count} distinguishable cases. "

        if binding_count > 0:
            strong_binding = sum(1 for p in categorized['binding']
                               if p.strength in [Strength.VERY_STRONG, Strength.STRONG])
            summary += f"{strong_binding} binding precedents are strong support. "

        return summary

    def _build_court_hierarchy(self) -> Dict:
        """Build court hierarchy for determining precedential value"""
        return {
            'federal': {
                'supreme': ['United States Supreme Court'],
                'appellate': ['Circuit Court of Appeals', 'Court of Appeals'],
                'district': ['District Court']
            },
            'california': {
                'supreme': ['California Supreme Court'],
                'appellate': ['California Court of Appeal'],
                'trial': ['Superior Court']
            }
            # Add more jurisdictions as needed
        }
