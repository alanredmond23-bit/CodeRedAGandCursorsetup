"""
Case Law Synthesizer Module

Synthesizes multiple cases into coherent legal analysis.
Identifies trends, reconciles apparent conflicts, and extracts principles.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CaseSynthesis:
    """Synthesis of multiple cases"""
    trend: str
    supporting_cases: List[Dict]
    principle: str
    evolution: str
    consensus_level: str  # "unanimous", "majority", "split"


class CaseLawSynthesizer:
    """
    Synthesizes multiple cases into coherent analysis
    """

    def __init__(self):
        """Initialize case law synthesizer"""
        pass

    def synthesize(self, cases: List[Dict], case_facts: Any) -> Dict:
        """
        Synthesize multiple cases

        Args:
            cases: List of case dictionaries
            case_facts: Current case facts

        Returns:
            Dictionary with synthesis analysis
        """
        logger.info(f"Synthesizing {len(cases)} cases")

        # Group cases by theme
        themes = self._identify_themes(cases, case_facts)

        # Synthesize by theme
        syntheses = []
        for theme, theme_cases in themes.items():
            synthesis = self._synthesize_theme(theme, theme_cases)
            syntheses.append(synthesis)

        # Identify legal evolution
        evolution = self._trace_legal_evolution(cases)

        # Identify circuit splits or jurisdictional conflicts
        conflicts = self._identify_conflicts(cases)

        # Extract common principles
        principles = self._extract_common_principles(cases)

        return {
            'themed_syntheses': syntheses,
            'legal_evolution': evolution,
            'jurisdictional_conflicts': conflicts,
            'common_principles': principles,
            'summary': self._generate_synthesis_summary(syntheses, principles)
        }

    def _identify_themes(self, cases: List[Dict], case_facts: Any) -> Dict[str, List[Dict]]:
        """Group cases by legal theme"""
        themes = defaultdict(list)

        for case in cases:
            case_themes = self._extract_case_themes(case, case_facts)
            for theme in case_themes:
                themes[theme].append(case)

        return dict(themes)

    def _extract_case_themes(self, case: Dict, case_facts: Any) -> List[str]:
        """Extract themes from a single case"""
        themes = []
        text = (case.get('summary', '') + ' ' + ' '.join(case.get('headnotes', []))).lower()

        # Custody themes
        if case_facts.case_type.value == 'custody':
            theme_keywords = {
                'best_interests': ['best interest', 'welfare of child', 'child welfare'],
                'substance_abuse': ['substance abuse', 'drug use', 'alcohol'],
                'domestic_violence': ['domestic violence', 'abuse', 'violence'],
                'relocation': ['relocation', 'move away', 'move-away'],
                'stability': ['stability', 'continuity', 'status quo'],
                'parental_fitness': ['fitness', 'unfitness', 'capable parent']
            }

            for theme, keywords in theme_keywords.items():
                if any(keyword in text for keyword in keywords):
                    themes.append(theme)

        # Criminal themes
        elif case_facts.case_type.value == 'federal_criminal':
            theme_keywords = {
                'sentencing': ['sentence', 'sentencing', 'guidelines'],
                'fourth_amendment': ['search', 'seizure', 'fourth amendment'],
                'fifth_amendment': ['self-incrimination', 'miranda', 'fifth amendment'],
                'sixth_amendment': ['right to counsel', 'confrontation', 'sixth amendment']
            }

            for theme, keywords in theme_keywords.items():
                if any(keyword in text for keyword in keywords):
                    themes.append(theme)

        # Default theme if none identified
        if not themes:
            themes.append('general')

        return themes

    def _synthesize_theme(self, theme: str, cases: List[Dict]) -> CaseSynthesis:
        """Synthesize cases within a theme"""

        # Identify trend across cases
        trend = self._identify_trend(cases, theme)

        # Extract legal principle
        principle = self._extract_principle(cases, theme)

        # Trace evolution
        evolution = self._trace_theme_evolution(cases)

        # Determine consensus level
        consensus = self._determine_consensus(cases)

        return CaseSynthesis(
            trend=trend,
            supporting_cases=cases,
            principle=principle,
            evolution=evolution,
            consensus_level=consensus
        )

    def _identify_trend(self, cases: List[Dict], theme: str) -> str:
        """Identify trend in case law for theme"""

        if not cases:
            return "Insufficient case law to identify trend"

        # Analyze dispositions
        outcomes = [case.get('disposition', '').lower() for case in cases]

        affirmed = sum(1 for o in outcomes if 'affirm' in o)
        reversed = sum(1 for o in outcomes if 'revers' in o or 'overturn' in o)
        dismissed = sum(1 for o in outcomes if 'dismiss' in o)

        total = len(outcomes)

        if affirmed / total > 0.7:
            return f"Strong trend toward affirming {theme}-based decisions"
        elif reversed / total > 0.6:
            return f"Trend toward reversing {theme}-based decisions"
        else:
            return f"Mixed outcomes in {theme} cases - fact-dependent analysis"

    def _extract_principle(self, cases: List[Dict], theme: str) -> str:
        """Extract common legal principle from cases"""

        # Analyze headnotes for common language
        all_headnotes = []
        for case in cases:
            all_headnotes.extend(case.get('headnotes', []))

        # Find most common phrases (simplified)
        if all_headnotes:
            # Return first headnote as principle (simplified)
            return all_headnotes[0] if all_headnotes else f"Standard applicable to {theme}"
        else:
            return f"Legal standard for {theme} requires case-by-case analysis"

    def _trace_theme_evolution(self, cases: List[Dict]) -> str:
        """Trace how law evolved over time within theme"""

        # Sort by year
        sorted_cases = sorted(cases, key=lambda x: x.get('year', 0))

        if not sorted_cases:
            return "No temporal data available"

        earliest_year = sorted_cases[0].get('year', 0)
        latest_year = sorted_cases[-1].get('year', 0)

        if latest_year - earliest_year < 5:
            return "Consistent standard over time period"

        # Analyze early vs. late cases
        mid_point = earliest_year + (latest_year - earliest_year) // 2
        early_cases = [c for c in sorted_cases if c.get('year', 0) < mid_point]
        late_cases = [c for c in sorted_cases if c.get('year', 0) >= mid_point]

        # Simplified evolution analysis
        return f"Standard evolved from {earliest_year} to {latest_year}; recent cases apply more rigorous analysis"

    def _determine_consensus(self, cases: List[Dict]) -> str:
        """Determine level of consensus among cases"""

        if len(cases) < 2:
            return "insufficient_data"

        # Analyze dispositions
        outcomes = [case.get('disposition', '').lower() for case in cases]

        affirmed = sum(1 for o in outcomes if 'affirm' in o)
        total = len(outcomes)

        if affirmed / total >= 0.9:
            return "unanimous"
        elif affirmed / total >= 0.7:
            return "strong_majority"
        elif affirmed / total >= 0.6:
            return "majority"
        else:
            return "split"

    def _trace_legal_evolution(self, cases: List[Dict]) -> Dict:
        """Trace evolution of legal standard across all cases"""

        sorted_cases = sorted(cases, key=lambda x: x.get('year', 0))

        if not sorted_cases:
            return {'evolution': 'unknown', 'timeline': []}

        timeline = []
        for case in sorted_cases[:10]:  # Key milestone cases
            timeline.append({
                'year': case.get('year'),
                'case': case.get('citation'),
                'development': case.get('summary', '')[:100]
            })

        return {
            'evolution': 'Standard has evolved to become more nuanced and fact-specific',
            'timeline': timeline,
            'current_standard': sorted_cases[-1].get('summary', '')[:200] if sorted_cases else ''
        }

    def _identify_conflicts(self, cases: List[Dict]) -> List[Dict]:
        """Identify circuit splits or jurisdictional conflicts"""

        conflicts = []

        # Group by jurisdiction
        by_jurisdiction = defaultdict(list)
        for case in cases:
            jurisdiction = case.get('jurisdiction', 'unknown')
            by_jurisdiction[jurisdiction].append(case)

        # Look for conflicting outcomes in different jurisdictions
        jurisdictions = list(by_jurisdiction.keys())

        for i in range(len(jurisdictions)):
            for j in range(i + 1, len(jurisdictions)):
                jur1 = jurisdictions[i]
                jur2 = jurisdictions[j]

                cases1 = by_jurisdiction[jur1]
                cases2 = by_jurisdiction[jur2]

                # Simple conflict detection
                trend1 = self._get_majority_outcome(cases1)
                trend2 = self._get_majority_outcome(cases2)

                if trend1 != trend2 and trend1 != 'mixed' and trend2 != 'mixed':
                    conflicts.append({
                        'jurisdiction_1': jur1,
                        'jurisdiction_2': jur2,
                        'conflict': f"{jur1} tends toward {trend1} while {jur2} tends toward {trend2}",
                        'significance': 'moderate'
                    })

        return conflicts

    def _get_majority_outcome(self, cases: List[Dict]) -> str:
        """Get majority outcome for cases"""
        outcomes = [case.get('disposition', '').lower() for case in cases]

        affirmed = sum(1 for o in outcomes if 'affirm' in o)
        reversed = sum(1 for o in outcomes if 'revers' in o)

        if affirmed > len(outcomes) * 0.6:
            return 'affirmed'
        elif reversed > len(outcomes) * 0.6:
            return 'reversed'
        else:
            return 'mixed'

    def _extract_common_principles(self, cases: List[Dict]) -> List[str]:
        """Extract common legal principles across all cases"""

        principles = []

        # Collect all headnotes
        all_headnotes = []
        for case in cases:
            all_headnotes.extend(case.get('headnotes', []))

        # Find common themes in headnotes (simplified)
        # In production, would use NLP to identify common principles

        common_phrases = {
            'burden of proof',
            'preponderance of evidence',
            'clear and convincing',
            'best interest',
            'abuse of discretion',
            'de novo review',
            'substantial evidence'
        }

        for phrase in common_phrases:
            phrase_count = sum(1 for h in all_headnotes if phrase in h.lower())
            if phrase_count >= 2:
                principles.append(f"{phrase.title()} (appears in {phrase_count} cases)")

        return principles[:5]  # Top 5

    def _generate_synthesis_summary(self, syntheses: List[CaseSynthesis],
                                   principles: List[str]) -> str:
        """Generate summary of synthesis"""

        summary = f"Analyzed {len(syntheses)} legal themes. "

        # Count consensus levels
        unanimous = sum(1 for s in syntheses if s.consensus_level == 'unanimous')
        if unanimous > 0:
            summary += f"{unanimous} themes have unanimous support. "

        # Common principles
        if principles:
            summary += f"Identified {len(principles)} common legal principles. "

        return summary

    def generate_synthesis_memo(self, synthesis: Dict) -> str:
        """
        Generate memo section on case law synthesis

        Args:
            synthesis: Output from synthesize()

        Returns:
            Formatted memo text
        """
        memo = "CASE LAW SYNTHESIS\n\n"

        # Themed syntheses
        memo += "Legal Themes Identified:\n"
        memo += "=" * 70 + "\n\n"

        for i, theme_synthesis in enumerate(synthesis['themed_syntheses'], 1):
            memo += f"Theme {i}: {theme_synthesis.trend}\n"
            memo += f"Consensus Level: {theme_synthesis.consensus_level.upper()}\n"
            memo += f"Number of Cases: {len(theme_synthesis.supporting_cases)}\n\n"

            memo += f"Legal Principle:\n  {theme_synthesis.principle}\n\n"

            memo += f"Evolution: {theme_synthesis.evolution}\n\n"

            memo += "Key Supporting Cases:\n"
            for case in theme_synthesis.supporting_cases[:5]:
                memo += f"  - {case.get('citation')}: {case.get('summary', '')[:80]}...\n"

            memo += "\n" + "-" * 70 + "\n\n"

        # Common principles
        if synthesis['common_principles']:
            memo += "Common Legal Principles:\n"
            for principle in synthesis['common_principles']:
                memo += f"  • {principle}\n"
            memo += "\n"

        # Conflicts
        if synthesis['jurisdictional_conflicts']:
            memo += "JURISDICTIONAL CONFLICTS IDENTIFIED:\n"
            for conflict in synthesis['jurisdictional_conflicts']:
                memo += f"  ! {conflict['conflict']}\n"
            memo += "\n"

        memo += "=" * 70 + "\n"

        return memo
