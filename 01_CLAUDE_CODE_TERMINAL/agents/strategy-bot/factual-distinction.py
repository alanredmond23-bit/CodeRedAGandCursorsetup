"""
Factual Distinction Module

Identifies factual distinctions between precedents and current case.
Critical for arguing why unfavorable precedents don't apply or why
favorable precedents are directly applicable.
"""

import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DistinctionType(Enum):
    """Types of factual distinctions"""
    MATERIAL = "material"  # Significant difference affecting outcome
    PROCEDURAL = "procedural"  # Different procedural posture
    TEMPORAL = "temporal"  # Different time period/circumstances
    JURISDICTIONAL = "jurisdictional"  # Different jurisdiction/law
    EVIDENTIARY = "evidentiary"  # Different evidence available
    CONTEXTUAL = "contextual"  # Different surrounding circumstances


class DistinctionImpact(Enum):
    """Impact of distinction on case applicability"""
    CRITICAL = "critical"  # Renders precedent inapplicable
    SIGNIFICANT = "significant"  # Substantially limits applicability
    MODERATE = "moderate"  # Somewhat limits applicability
    MINOR = "minor"  # Does not significantly affect applicability


@dataclass
class Distinction:
    """A factual distinction between precedent and current case"""
    distinction_type: DistinctionType
    impact: DistinctionImpact
    precedent_fact: str
    current_fact: str
    legal_significance: str
    argument_use: str  # How to use this distinction in argument


class FactualDistinguisher:
    """
    Analyzes factual distinctions between precedents and current case
    """

    def __init__(self):
        """Initialize factual distinguisher"""
        pass

    def analyze(self, precedent_analysis: Dict, case_facts: Any) -> Dict:
        """
        Analyze factual distinctions between precedents and current case

        Args:
            precedent_analysis: Output from PrecedentAnalyzer
            case_facts: Current case facts

        Returns:
            Dictionary with distinction analysis
        """
        logger.info("Analyzing factual distinctions")

        all_precedents = precedent_analysis.get('all_analyses', [])

        # Analyze each precedent
        distinction_analyses = []
        for precedent in all_precedents:
            distinctions = self._identify_distinctions(precedent, case_facts)
            distinction_analyses.append({
                'case': precedent.case,
                'distinctions': distinctions,
                'overall_impact': self._assess_overall_impact(distinctions)
            })

        # Categorize by whether favorable or unfavorable
        favorable_distinctions = self._identify_favorable_distinctions(
            distinction_analyses, case_facts
        )
        unfavorable_distinctions = self._identify_unfavorable_distinctions(
            distinction_analyses, case_facts
        )

        return {
            'all_distinction_analyses': distinction_analyses,
            'favorable_precedent_distinctions': favorable_distinctions,
            'unfavorable_precedent_distinctions': unfavorable_distinctions,
            'strategic_recommendations': self._generate_recommendations(
                favorable_distinctions,
                unfavorable_distinctions
            )
        }

    def _identify_distinctions(self, precedent_analysis: Any, case_facts: Any) -> List[Distinction]:
        """
        Identify specific factual distinctions

        Args:
            precedent_analysis: Single PrecedentAnalysis object
            case_facts: Current case facts

        Returns:
            List of Distinction objects
        """
        distinctions = []

        # Extract case information
        case = precedent_analysis.case
        case_summary = case.get('summary', '').lower()
        our_facts = case_facts.facts_summary.lower()

        # Analyze different types of distinctions
        distinctions.extend(self._identify_material_distinctions(case, case_facts))
        distinctions.extend(self._identify_procedural_distinctions(case, case_facts))
        distinctions.extend(self._identify_temporal_distinctions(case, case_facts))
        distinctions.extend(self._identify_evidentiary_distinctions(case, case_facts))
        distinctions.extend(self._identify_contextual_distinctions(case, case_facts))

        return distinctions

    def _identify_material_distinctions(self, case: Dict, case_facts: Any) -> List[Distinction]:
        """Identify material factual distinctions"""
        distinctions = []

        # Custody-specific distinctions
        if case_facts.case_type.value == 'custody':
            distinctions.extend(self._custody_material_distinctions(case, case_facts))

        # Criminal-specific distinctions
        elif case_facts.case_type.value == 'federal_criminal':
            distinctions.extend(self._criminal_material_distinctions(case, case_facts))

        # General material distinctions
        case_summary = case.get('summary', '').lower()
        our_facts = case_facts.facts_summary.lower()

        # Check for key factual elements
        key_elements = self._extract_key_elements(case_facts)

        for element_type, our_element in key_elements.items():
            # Look for corresponding element in precedent
            precedent_element = self._find_element_in_case(element_type, case)

            if precedent_element and precedent_element != our_element:
                distinctions.append(Distinction(
                    distinction_type=DistinctionType.MATERIAL,
                    impact=DistinctionImpact.SIGNIFICANT,
                    precedent_fact=f"{element_type}: {precedent_element}",
                    current_fact=f"{element_type}: {our_element}",
                    legal_significance=f"Different {element_type} affects application of rule",
                    argument_use=f"Precedent involved {precedent_element}, whereas our case involves {our_element}"
                ))

        return distinctions

    def _custody_material_distinctions(self, case: Dict, case_facts: Any) -> List[Distinction]:
        """Identify custody-specific material distinctions"""
        distinctions = []
        case_text = case.get('summary', '').lower()
        our_facts = case_facts.facts_summary.lower()

        # Substance abuse distinction
        if 'substance abuse' in case_text and 'substance abuse' in our_facts:
            # Both have substance abuse - not a distinction
            pass
        elif 'substance abuse' in case_text and 'substance abuse' not in our_facts:
            distinctions.append(Distinction(
                distinction_type=DistinctionType.MATERIAL,
                impact=DistinctionImpact.CRITICAL,
                precedent_fact="Involved substance abuse allegations",
                current_fact="No substance abuse issues present",
                legal_significance="Substance abuse is material factor in best interest analysis",
                argument_use="Unlike the precedent case, there are no substance abuse concerns here"
            ))
        elif 'substance abuse' not in case_text and 'substance abuse' in our_facts:
            distinctions.append(Distinction(
                distinction_type=DistinctionType.MATERIAL,
                impact=DistinctionImpact.CRITICAL,
                precedent_fact="No substance abuse issues",
                current_fact="Substance abuse allegations present",
                legal_significance="Substance abuse materially affects best interest determination",
                argument_use="This case involves substance abuse concerns not present in precedent"
            ))

        # Domestic violence distinction
        if 'domestic violence' in our_facts and 'domestic violence' not in case_text:
            distinctions.append(Distinction(
                distinction_type=DistinctionType.MATERIAL,
                impact=DistinctionImpact.CRITICAL,
                precedent_fact="No domestic violence history",
                current_fact="Domestic violence alleged or proven",
                legal_significance="DV creates rebuttable presumption against custody",
                argument_use="This case involves domestic violence issues requiring special consideration"
            ))

        # Relocation distinction
        if 'relocation' in case_text or 'move' in case_text:
            if 'relocation' not in our_facts and 'move' not in our_facts:
                distinctions.append(Distinction(
                    distinction_type=DistinctionType.MATERIAL,
                    impact=DistinctionImpact.SIGNIFICANT,
                    precedent_fact="Involved relocation/move away request",
                    current_fact="No relocation at issue",
                    legal_significance="Relocation cases apply different legal standard",
                    argument_use="Precedent's relocation analysis inapplicable to non-move case"
                ))

        return distinctions

    def _criminal_material_distinctions(self, case: Dict, case_facts: Any) -> List[Distinction]:
        """Identify criminal case material distinctions"""
        distinctions = []
        case_text = case.get('summary', '').lower()

        # Type of crime
        crimes = ['fraud', 'drug', 'violence', 'weapons', 'white collar']
        for crime_type in crimes:
            if crime_type in case_text:
                if crime_type not in case_facts.facts_summary.lower():
                    distinctions.append(Distinction(
                        distinction_type=DistinctionType.MATERIAL,
                        impact=DistinctionImpact.SIGNIFICANT,
                        precedent_fact=f"Involved {crime_type} offense",
                        current_fact=f"Does not involve {crime_type} offense",
                        legal_significance="Different offense types may affect sentencing guidelines",
                        argument_use=f"Precedent's {crime_type} context distinguishable"
                    ))

        return distinctions

    def _identify_procedural_distinctions(self, case: Dict, case_facts: Any) -> List[Distinction]:
        """Identify procedural distinctions"""
        distinctions = []

        case_text = case.get('summary', '').lower()

        # Motion type
        motion_types = ['summary judgment', 'dismiss', 'preliminary injunction', 'trial']
        for motion_type in motion_types:
            if motion_type in case_text:
                distinctions.append(Distinction(
                    distinction_type=DistinctionType.PROCEDURAL,
                    impact=DistinctionImpact.MODERATE,
                    precedent_fact=f"Decided on {motion_type}",
                    current_fact="Different procedural posture",
                    legal_significance="Different standards may apply at different stages",
                    argument_use=f"Precedent's {motion_type} standard may not apply here"
                ))

        return distinctions

    def _identify_temporal_distinctions(self, case: Dict, case_facts: Any) -> List[Distinction]:
        """Identify temporal distinctions"""
        distinctions = []

        case_year = case.get('year', 0)
        current_year = 2025

        # Old precedent
        if case_year < 1990:
            distinctions.append(Distinction(
                distinction_type=DistinctionType.TEMPORAL,
                impact=DistinctionImpact.MODERATE,
                precedent_fact=f"Decided in {case_year}",
                current_fact=f"Current case in {current_year}",
                legal_significance="Legal standards and social context have evolved",
                argument_use="Precedent reflects outdated legal landscape"
            ))

        # Check for superseding legislation
        # (Would check actual legislative history in production)

        return distinctions

    def _identify_evidentiary_distinctions(self, case: Dict, case_facts: Any) -> List[Distinction]:
        """Identify evidentiary distinctions"""
        distinctions = []

        case_text = case.get('summary', '').lower()

        # Evidence types
        evidence_types = ['expert testimony', 'documentary evidence', 'witness testimony']

        # This is simplified - would do deeper analysis in production
        return distinctions

    def _identify_contextual_distinctions(self, case: Dict, case_facts: Any) -> List[Distinction]:
        """Identify contextual distinctions"""
        distinctions = []

        # Different statutory framework
        if case.get('jurisdiction') != case_facts.jurisdiction.value:
            distinctions.append(Distinction(
                distinction_type=DistinctionType.JURISDICTIONAL,
                impact=DistinctionImpact.SIGNIFICANT,
                precedent_fact=f"Decided under {case.get('jurisdiction')} law",
                current_fact=f"Current case under {case_facts.jurisdiction.value} law",
                legal_significance="Different jurisdictions may apply different standards",
                argument_use="Precedent's jurisdiction has different legal framework"
            ))

        return distinctions

    def _extract_key_elements(self, case_facts: Any) -> Dict[str, str]:
        """Extract key factual elements from case facts"""
        elements = {}

        facts_text = case_facts.facts_summary.lower()

        # Extract parties (if applicable)
        if 'parties' in dir(case_facts) and case_facts.parties:
            for role, party in case_facts.parties.items():
                elements[role] = party

        # Extract key factual themes
        themes = {
            'substance_abuse': ['substance abuse', 'drug', 'alcohol'],
            'violence': ['violence', 'abuse', 'assault'],
            'stability': ['stable', 'unstable', 'housing'],
            'employment': ['employed', 'job', 'work']
        }

        for theme, keywords in themes.items():
            for keyword in keywords:
                if keyword in facts_text:
                    elements[theme] = f"Present ({keyword})"
                    break
            else:
                elements[theme] = "Not present"

        return elements

    def _find_element_in_case(self, element_type: str, case: Dict) -> str:
        """Find corresponding element in precedent case"""
        case_text = case.get('summary', '').lower()

        # Simple keyword matching - would be more sophisticated in production
        if element_type in case_text:
            return "Present"
        else:
            return "Not present"

    def _assess_overall_impact(self, distinctions: List[Distinction]) -> str:
        """Assess overall impact of all distinctions"""
        if not distinctions:
            return "highly_applicable"

        critical_count = sum(1 for d in distinctions if d.impact == DistinctionImpact.CRITICAL)
        significant_count = sum(1 for d in distinctions if d.impact == DistinctionImpact.SIGNIFICANT)

        if critical_count > 0:
            return "substantially_distinguishable"
        elif significant_count >= 2:
            return "moderately_distinguishable"
        elif significant_count == 1:
            return "somewhat_distinguishable"
        else:
            return "minimally_distinguishable"

    def _identify_favorable_distinctions(self, distinction_analyses: List[Dict],
                                        case_facts: Any) -> List[Dict]:
        """Identify distinctions from favorable precedents we want to emphasize"""
        favorable = []

        for analysis in distinction_analyses:
            case = analysis['case']

            # Check if case outcome is favorable
            disposition = case.get('disposition', '').lower()
            if self._is_favorable_outcome(disposition, case_facts):
                # For favorable cases, we want to minimize distinctions
                # Or show why distinctions don't matter
                favorable.append({
                    'case': case,
                    'distinctions': analysis['distinctions'],
                    'strategy': 'minimize_distinctions',
                    'argument': self._generate_minimize_argument(analysis['distinctions'])
                })

        return favorable

    def _identify_unfavorable_distinctions(self, distinction_analyses: List[Dict],
                                          case_facts: Any) -> List[Dict]:
        """Identify distinctions from unfavorable precedents we want to emphasize"""
        unfavorable = []

        for analysis in distinction_analyses:
            case = analysis['case']

            disposition = case.get('disposition', '').lower()
            if not self._is_favorable_outcome(disposition, case_facts):
                # For unfavorable cases, we want to maximize distinctions
                unfavorable.append({
                    'case': case,
                    'distinctions': analysis['distinctions'],
                    'strategy': 'maximize_distinctions',
                    'argument': self._generate_maximize_argument(analysis['distinctions'])
                })

        return unfavorable

    def _is_favorable_outcome(self, disposition: str, case_facts: Any) -> bool:
        """Determine if case outcome is favorable to our position"""
        # Simplified - would analyze based on desired outcome
        favorable_terms = ['affirmed', 'granted', 'reversed']
        unfavorable_terms = ['denied', 'dismissed']

        for term in favorable_terms:
            if term in disposition:
                return True

        return False

    def _generate_minimize_argument(self, distinctions: List[Distinction]) -> str:
        """Generate argument minimizing distinctions from favorable precedent"""
        if not distinctions:
            return "Precedent directly applicable with no material distinctions"

        critical = [d for d in distinctions if d.impact == DistinctionImpact.CRITICAL]

        if not critical:
            return "Minor factual differences do not affect applicability of legal principles"

        return "Despite some factual differences, controlling legal principles apply equally"

    def _generate_maximize_argument(self, distinctions: List[Distinction]) -> str:
        """Generate argument maximizing distinctions from unfavorable precedent"""
        if not distinctions:
            return "RISK: No significant distinctions identified"

        critical = [d for d in distinctions if d.impact == DistinctionImpact.CRITICAL]
        significant = [d for d in distinctions if d.impact == DistinctionImpact.SIGNIFICANT]

        if critical:
            return f"Precedent distinguishable on {len(critical)} critical factual grounds"
        elif significant:
            return f"Precedent distinguishable on {len(significant)} significant factual grounds"
        else:
            return "Precedent distinguishable on procedural/contextual grounds"

    def _generate_recommendations(self, favorable: List[Dict],
                                 unfavorable: List[Dict]) -> List[str]:
        """Generate strategic recommendations based on distinction analysis"""
        recommendations = []

        # Analyze favorable precedents
        if favorable:
            avg_distinctions = sum(len(f['distinctions']) for f in favorable) / len(favorable)
            if avg_distinctions < 2:
                recommendations.append(
                    "Strong argument: Favorable precedents closely aligned with our facts"
                )
            else:
                recommendations.append(
                    "Moderate argument: Some distinctions from favorable precedents to address"
                )

        # Analyze unfavorable precedents
        if unfavorable:
            critical_distinctions = sum(
                sum(1 for d in u['distinctions'] if d.impact == DistinctionImpact.CRITICAL)
                for u in unfavorable
            )

            if critical_distinctions > 0:
                recommendations.append(
                    f"Can distinguish {critical_distinctions} unfavorable precedents on critical facts"
                )
            else:
                recommendations.append(
                    "RISK: Difficult to distinguish unfavorable precedents - consider alternative theories"
                )

        return recommendations
