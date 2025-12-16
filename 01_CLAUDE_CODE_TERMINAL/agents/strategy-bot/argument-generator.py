"""
Argument Generator Module

Generates legal theories and arguments based on case law research,
statutes, and factual distinctions. Assigns confidence scores.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


@dataclass
class LegalTheory:
    """Structure for legal theories"""
    theory_name: str
    supporting_cases: List[Dict]
    supporting_statutes: List[Dict]
    confidence_score: float
    strengths: List[str]
    weaknesses: List[str]
    factual_distinctions_needed: List[str]
    counter_arguments: List[str]


class ArgumentGenerator:
    """
    Generates legal theories and arguments with confidence scoring
    """

    def __init__(self):
        """Initialize argument generator"""
        pass

    def generate_theories(self, precedent_analysis: Dict, statutes: List[Dict],
                         distinctions: Dict, case_facts: Any) -> List[LegalTheory]:
        """
        Generate legal theories based on research

        Args:
            precedent_analysis: Output from PrecedentAnalyzer
            statutes: List of applicable statutes
            distinctions: Output from FactualDistinguisher
            case_facts: Current case facts

        Returns:
            List of LegalTheory objects with confidence scores
        """
        logger.info("Generating legal theories")

        theories = []

        # Generate theories from binding precedents
        binding_theories = self._generate_from_binding_precedents(
            precedent_analysis.get('binding_precedents', []),
            statutes,
            distinctions,
            case_facts
        )
        theories.extend(binding_theories)

        # Generate theories from persuasive precedents
        persuasive_theories = self._generate_from_persuasive_precedents(
            precedent_analysis.get('persuasive_precedents', []),
            statutes,
            distinctions,
            case_facts
        )
        theories.extend(persuasive_theories)

        # Generate theories from statutes directly
        statute_theories = self._generate_from_statutes(
            statutes,
            precedent_analysis,
            case_facts
        )
        theories.extend(statute_theories)

        # Remove duplicate theories
        unique_theories = self._deduplicate_theories(theories)

        # Calculate confidence scores
        scored_theories = [self._calculate_confidence(t, precedent_analysis)
                          for t in unique_theories]

        # Sort by confidence
        scored_theories.sort(key=lambda x: x.confidence_score, reverse=True)

        logger.info(f"Generated {len(scored_theories)} legal theories")

        return scored_theories

    def _generate_from_binding_precedents(self, binding_precedents: List,
                                         statutes: List[Dict],
                                         distinctions: Dict,
                                         case_facts: Any) -> List[LegalTheory]:
        """Generate theories from binding precedents"""
        theories = []

        for precedent in binding_precedents:
            # Extract key holdings
            for holding in precedent.key_holdings:
                theory = self._create_theory_from_holding(
                    holding,
                    precedent,
                    statutes,
                    distinctions,
                    case_facts,
                    is_binding=True
                )
                if theory:
                    theories.append(theory)

        return theories

    def _generate_from_persuasive_precedents(self, persuasive_precedents: List,
                                            statutes: List[Dict],
                                            distinctions: Dict,
                                            case_facts: Any) -> List[LegalTheory]:
        """Generate theories from persuasive precedents"""
        theories = []

        # Only use strongest persuasive precedents
        strong_persuasive = [p for p in persuasive_precedents
                            if p.similarity_score >= 0.7]

        for precedent in strong_persuasive:
            for holding in precedent.key_holdings:
                theory = self._create_theory_from_holding(
                    holding,
                    precedent,
                    statutes,
                    distinctions,
                    case_facts,
                    is_binding=False
                )
                if theory:
                    theories.append(theory)

        return theories

    def _generate_from_statutes(self, statutes: List[Dict],
                               precedent_analysis: Dict,
                               case_facts: Any) -> List[LegalTheory]:
        """Generate theories from statutes"""
        theories = []

        for statute in statutes:
            theory = self._create_theory_from_statute(
                statute,
                precedent_analysis,
                case_facts
            )
            if theory:
                theories.append(theory)

        return theories

    def _create_theory_from_holding(self, holding: str, precedent: Any,
                                   statutes: List[Dict], distinctions: Dict,
                                   case_facts: Any, is_binding: bool) -> LegalTheory:
        """Create a legal theory from a case holding"""

        # Build theory name from holding
        theory_name = self._extract_theory_name(holding, case_facts)

        # Gather supporting cases
        supporting_cases = [{
            'citation': precedent.case.get('citation'),
            'title': precedent.case.get('title'),
            'year': precedent.case.get('year'),
            'summary': precedent.case.get('summary'),
            'holding': holding,
            'is_binding': is_binding
        }]

        # Find related statutes
        supporting_statutes = self._find_related_statutes(holding, statutes)

        # Identify strengths
        strengths = self._identify_strengths(precedent, is_binding, case_facts)

        # Identify weaknesses
        weaknesses = self._identify_weaknesses(precedent, distinctions)

        # Identify needed distinctions
        needed_distinctions = self._identify_needed_distinctions(
            precedent, distinctions
        )

        # Placeholder for counter-arguments (filled in by counter-argument module)
        counter_arguments = []

        return LegalTheory(
            theory_name=theory_name,
            supporting_cases=supporting_cases,
            supporting_statutes=supporting_statutes,
            confidence_score=0.0,  # Calculated later
            strengths=strengths,
            weaknesses=weaknesses,
            factual_distinctions_needed=needed_distinctions,
            counter_arguments=counter_arguments
        )

    def _create_theory_from_statute(self, statute: Dict, precedent_analysis: Dict,
                                   case_facts: Any) -> LegalTheory:
        """Create a legal theory from a statute"""

        theory_name = f"Statutory Claim: {statute.get('title', 'Unknown')}"

        # Find cases interpreting this statute
        supporting_cases = self._find_cases_interpreting_statute(
            statute, precedent_analysis
        )

        supporting_statutes = [statute]

        strengths = [
            "Based on clear statutory language",
            "Direct statutory authority"
        ]

        weaknesses = []
        if not supporting_cases:
            weaknesses.append("Limited case law interpreting this statute")

        return LegalTheory(
            theory_name=theory_name,
            supporting_cases=supporting_cases,
            supporting_statutes=supporting_statutes,
            confidence_score=0.0,
            strengths=strengths,
            weaknesses=weaknesses,
            factual_distinctions_needed=[],
            counter_arguments=[]
        )

    def _extract_theory_name(self, holding: str, case_facts: Any) -> str:
        """Extract concise theory name from holding"""
        # Simplified - would use NLP in production
        if case_facts.case_type.value == 'custody':
            if 'best interest' in holding.lower():
                return "Best Interests of Child Standard"
            elif 'substance abuse' in holding.lower():
                return "Parental Substance Abuse Impact Theory"
            elif 'changed circumstances' in holding.lower():
                return "Material Change in Circumstances"
            elif 'relocation' in holding.lower():
                return "Parental Relocation Standard"
        elif case_facts.case_type.value == 'federal_criminal':
            if 'sentencing' in holding.lower():
                return "Sentencing Guidelines Theory"
            elif 'constitutional' in holding.lower():
                return "Constitutional Challenge"

        # Default
        return f"{case_facts.case_type.value.title()} Legal Theory"

    def _find_related_statutes(self, holding: str, statutes: List[Dict]) -> List[Dict]:
        """Find statutes related to this holding"""
        related = []

        holding_lower = holding.lower()

        for statute in statutes:
            statute_text = (statute.get('title', '') + ' ' +
                          statute.get('text', '')).lower()

            # Simple keyword matching - would be more sophisticated
            if self._has_keyword_overlap(holding_lower, statute_text):
                related.append(statute)

        return related

    def _has_keyword_overlap(self, text1: str, text2: str) -> bool:
        """Check if two texts have keyword overlap"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        # Exclude common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
        words1 -= stop_words
        words2 -= stop_words

        overlap = words1 & words2
        return len(overlap) >= 2

    def _identify_strengths(self, precedent: Any, is_binding: bool,
                          case_facts: Any) -> List[str]:
        """Identify strengths of this theory"""
        strengths = []

        if is_binding:
            strengths.append("Based on binding precedent in same jurisdiction")

        if precedent.similarity_score >= 0.8:
            strengths.append("Highly similar factual circumstances")

        if precedent.case.get('year', 0) >= 2020:
            strengths.append("Recent precedent reflecting current law")

        if 'Supreme Court' in precedent.case.get('court', ''):
            strengths.append("Decided by highest court")

        if precedent.strength.value in ['very_strong', 'strong']:
            strengths.append("Strong precedential authority")

        if len(precedent.reasons_to_follow) > 3:
            strengths.append(f"{len(precedent.reasons_to_follow)} reasons support applicability")

        return strengths

    def _identify_weaknesses(self, precedent: Any, distinctions: Dict) -> List[str]:
        """Identify weaknesses of this theory"""
        weaknesses = []

        if precedent.similarity_score < 0.5:
            weaknesses.append("Limited factual similarity")

        if precedent.case.get('year', 0) < 1990:
            weaknesses.append("Older precedent - may not reflect current standards")

        if precedent.authority_type.value != 'binding':
            weaknesses.append("Persuasive authority only - not binding")

        if len(precedent.reasons_to_distinguish) > 2:
            weaknesses.append(f"{len(precedent.reasons_to_distinguish)} potential distinguishing factors")

        # Check for adverse distinctions
        for distinction_analysis in distinctions.get('unfavorable_precedent_distinctions', []):
            if distinction_analysis['case'].get('citation') == precedent.case.get('citation'):
                critical_distinctions = sum(
                    1 for d in distinction_analysis['distinctions']
                    if d.impact.value == 'critical'
                )
                if critical_distinctions > 0:
                    weaknesses.append(f"{critical_distinctions} critical factual distinctions")

        return weaknesses

    def _identify_needed_distinctions(self, precedent: Any,
                                     distinctions: Dict) -> List[str]:
        """Identify factual distinctions that must be addressed"""
        needed = []

        for distinction_analysis in distinctions.get('all_distinction_analyses', []):
            if distinction_analysis['case'].get('citation') == precedent.case.get('citation'):
                for distinction in distinction_analysis['distinctions']:
                    if distinction.impact.value in ['critical', 'significant']:
                        needed.append(distinction.legal_significance)

        return needed

    def _find_cases_interpreting_statute(self, statute: Dict,
                                        precedent_analysis: Dict) -> List[Dict]:
        """Find cases that interpret this statute"""
        cases = []

        statute_citation = statute.get('citation', '')

        for precedent in precedent_analysis.get('all_analyses', []):
            case_text = precedent.case.get('summary', '') + ' '.join(precedent.case.get('headnotes', []))

            if statute_citation in case_text:
                cases.append({
                    'citation': precedent.case.get('citation'),
                    'title': precedent.case.get('title'),
                    'year': precedent.case.get('year'),
                    'summary': precedent.case.get('summary')
                })

        return cases

    def _calculate_confidence(self, theory: LegalTheory,
                             precedent_analysis: Dict) -> LegalTheory:
        """
        Calculate confidence score for a legal theory (0.0 to 1.0)

        Factors:
        - Binding vs persuasive authority
        - Number and quality of supporting cases
        - Factual similarity
        - Recency of precedent
        - Number of weaknesses
        - Availability of counter-arguments
        """
        score = 0.5  # Base score

        # Authority type
        if any(case.get('is_binding') for case in theory.supporting_cases):
            score += 0.2
        else:
            score += 0.05

        # Number of supporting cases
        num_cases = len(theory.supporting_cases)
        if num_cases >= 5:
            score += 0.15
        elif num_cases >= 3:
            score += 0.10
        elif num_cases >= 1:
            score += 0.05

        # Statutory support
        if theory.supporting_statutes:
            score += 0.10

        # Strengths vs weaknesses
        strength_ratio = len(theory.strengths) / (len(theory.weaknesses) + 1)
        if strength_ratio >= 2.0:
            score += 0.15
        elif strength_ratio >= 1.0:
            score += 0.08
        else:
            score -= 0.05

        # Recency
        if theory.supporting_cases:
            max_year = max(case.get('year', 0) for case in theory.supporting_cases)
            if max_year >= 2020:
                score += 0.10
            elif max_year >= 2010:
                score += 0.05
            elif max_year < 1990:
                score -= 0.05

        # Needed distinctions (reduce score)
        if len(theory.factual_distinctions_needed) > 3:
            score -= 0.15
        elif len(theory.factual_distinctions_needed) > 1:
            score -= 0.08

        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))

        theory.confidence_score = score
        return theory

    def _deduplicate_theories(self, theories: List[LegalTheory]) -> List[LegalTheory]:
        """Remove duplicate theories"""
        seen = set()
        unique = []

        for theory in theories:
            if theory.theory_name not in seen:
                seen.add(theory.theory_name)
                unique.append(theory)
            else:
                # Merge supporting cases if duplicate
                for existing in unique:
                    if existing.theory_name == theory.theory_name:
                        existing.supporting_cases.extend(theory.supporting_cases)
                        break

        return unique
