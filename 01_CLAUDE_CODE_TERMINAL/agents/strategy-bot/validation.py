"""
Citation Validation Module

Validates that all citations are accurate and cases still good law.
CRITICAL: Must verify citations before use in court filings.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of citation validation"""
    citation: str
    is_valid: bool
    is_good_law: bool
    issues: List[str]
    treatment: str  # "positive", "negative", "overruled", "distinguished"
    shepards_signal: Optional[str]


class CitationValidator:
    """
    Validates citations and checks whether cases are still good law
    """

    def __init__(self, westlaw_researcher=None, lexis_researcher=None):
        """
        Initialize citation validator

        Args:
            westlaw_researcher: WestlawResearcher instance
            lexis_researcher: LexisNexisResearcher instance
        """
        self.westlaw = westlaw_researcher
        self.lexis = lexis_researcher

    def validate_all(self, cases: List[Dict]) -> bool:
        """
        Validate all citations

        Args:
            cases: List of case dictionaries to validate

        Returns:
            True if all citations valid, False otherwise
        """
        logger.info(f"Validating {len(cases)} citations")

        all_valid = True
        validation_results = []

        for case in cases:
            citation = case.get('citation')
            if not citation:
                logger.warning(f"Case missing citation: {case.get('title')}")
                all_valid = False
                continue

            result = self.validate_citation(citation)
            validation_results.append(result)

            if not result.is_valid or not result.is_good_law:
                all_valid = False
                logger.error(f"Citation validation failed: {citation}")
                for issue in result.issues:
                    logger.error(f"  - {issue}")

        logger.info(f"Validation complete: {all_valid}")
        return all_valid

    def validate_citation(self, citation: str) -> ValidationResult:
        """
        Validate a single citation

        Args:
            citation: Citation to validate

        Returns:
            ValidationResult object
        """
        logger.info(f"Validating citation: {citation}")

        issues = []
        is_valid = True
        is_good_law = True
        treatment = "unknown"
        shepards_signal = None

        # Check citation format
        if not self._check_citation_format(citation):
            issues.append("Invalid citation format")
            is_valid = False

        # Check if case exists (if research tools available)
        if is_valid and (self.westlaw or self.lexis):
            exists = self._verify_case_exists(citation)
            if not exists:
                issues.append("Citation not found in legal databases")
                is_valid = False

        # Check if still good law (Shepardize)
        if is_valid and (self.westlaw or self.lexis):
            shepards_result = self._shepardize(citation)
            treatment = shepards_result['treatment']
            shepards_signal = shepards_result['signal']

            if shepards_result['overruled']:
                issues.append("Case has been overruled")
                is_good_law = False

            if shepards_result['negative_treatment']:
                issues.append(f"Case has negative treatment: {shepards_result['negative_treatment']}")
                # Still might be good law for certain propositions

        return ValidationResult(
            citation=citation,
            is_valid=is_valid,
            is_good_law=is_good_law,
            issues=issues,
            treatment=treatment,
            shepards_signal=shepards_signal
        )

    def _check_citation_format(self, citation: str) -> bool:
        """
        Check if citation format is valid

        Args:
            citation: Citation to check

        Returns:
            True if format appears valid
        """
        # Basic format checks
        if not citation or len(citation) < 5:
            return False

        # Check for common citation patterns
        import re

        # U.S. Reports (e.g., "410 U.S. 113")
        us_pattern = r'\d+\s+U\.S\.\s+\d+'

        # Federal Reporter (e.g., "123 F.3d 456")
        f_pattern = r'\d+\s+F\.\d?d?\s+\d+'

        # State reporters (e.g., "31 Cal.4th 1114")
        state_pattern = r'\d+\s+\w+\.\s*\d*\w*\s+\d+'

        patterns = [us_pattern, f_pattern, state_pattern]

        for pattern in patterns:
            if re.search(pattern, citation):
                return True

        return False

    def _verify_case_exists(self, citation: str) -> bool:
        """
        Verify case exists in legal databases

        Args:
            citation: Citation to verify

        Returns:
            True if case exists
        """
        # Try Westlaw first
        if self.westlaw:
            try:
                case = self.westlaw.get_case_by_citation(citation)
                if case:
                    return True
            except Exception as e:
                logger.warning(f"Westlaw verification failed: {str(e)}")

        # Try LexisNexis
        if self.lexis:
            try:
                case = self.lexis.get_case_by_citation(citation)
                if case:
                    return True
            except Exception as e:
                logger.warning(f"LexisNexis verification failed: {str(e)}")

        # If no research tools, assume valid
        if not self.westlaw and not self.lexis:
            logger.warning("No research tools available - cannot verify case existence")
            return True

        return False

    def _shepardize(self, citation: str) -> Dict:
        """
        Get Shepard's Citations analysis

        Args:
            citation: Citation to shepardize

        Returns:
            Dictionary with Shepard's results
        """
        result = {
            'treatment': 'unknown',
            'signal': None,
            'overruled': False,
            'negative_treatment': None
        }

        # Try Westlaw Shepard's
        if self.westlaw:
            try:
                shepards = self.westlaw.get_treatment_analysis(citation)
                result['treatment'] = shepards.get('treatment', 'unknown')
                result['overruled'] = shepards.get('overruled', False)

                if shepards.get('negative_treatment', 0) > 0:
                    result['negative_treatment'] = f"{shepards['negative_treatment']} negative citing references"

                return result
            except Exception as e:
                logger.warning(f"Westlaw Shepardization failed: {str(e)}")

        # Try LexisNexis Shepard's
        if self.lexis:
            try:
                shepards = self.lexis.get_treatment_signals(citation)
                result['treatment'] = shepards.get('treatment', 'unknown')
                result['signal'] = 'warning' if shepards.get('warning') else 'positive'
                result['overruled'] = shepards.get('overruled', False)

                if shepards.get('caution'):
                    result['negative_treatment'] = "Caution flag raised"

                return result
            except Exception as e:
                logger.warning(f"LexisNexis Shepardization failed: {str(e)}")

        return result

    def generate_validation_report(self, cases: List[Dict]) -> str:
        """
        Generate validation report for all citations

        Args:
            cases: List of cases to validate

        Returns:
            Formatted validation report
        """
        report = "CITATION VALIDATION REPORT\n"
        report += "=" * 70 + "\n\n"

        all_valid = True
        validation_results = []

        for case in cases:
            citation = case.get('citation')
            if not citation:
                continue

            result = self.validate_citation(citation)
            validation_results.append(result)

        # Summary
        valid_count = sum(1 for r in validation_results if r.is_valid)
        good_law_count = sum(1 for r in validation_results if r.is_good_law)

        report += f"Total Citations: {len(validation_results)}\n"
        report += f"Valid Format: {valid_count}/{len(validation_results)}\n"
        report += f"Good Law: {good_law_count}/{len(validation_results)}\n\n"

        if valid_count == len(validation_results) and good_law_count == len(validation_results):
            report += "STATUS: ✓ ALL CITATIONS VALIDATED\n\n"
        else:
            report += "STATUS: ✗ CITATION ISSUES FOUND - REVIEW REQUIRED\n\n"

        # Detailed results
        report += "Detailed Validation Results:\n"
        report += "-" * 70 + "\n\n"

        for result in validation_results:
            report += f"Citation: {result.citation}\n"
            report += f"  Format Valid: {'✓' if result.is_valid else '✗'}\n"
            report += f"  Good Law: {'✓' if result.is_good_law else '✗'}\n"
            report += f"  Treatment: {result.treatment}\n"

            if result.shepards_signal:
                report += f"  Shepard's Signal: {result.shepards_signal}\n"

            if result.issues:
                report += "  Issues:\n"
                for issue in result.issues:
                    report += f"    ! {issue}\n"

            report += "\n"

        # Recommendations
        report += "=" * 70 + "\n"
        report += "RECOMMENDATIONS:\n\n"

        has_issues = any(not r.is_valid or not r.is_good_law for r in validation_results)

        if has_issues:
            report += "⚠ CRITICAL: Manual review required before using citations in court filings.\n"
            report += "⚠ Verify all flagged citations independently.\n"
            report += "⚠ Consider replacing overruled or negatively treated cases.\n"
        else:
            report += "✓ All citations appear valid and good law.\n"
            report += "✓ Recommend independent verification before filing.\n"

        report += "\n" + "=" * 70 + "\n"

        return report

    def check_circuit_split(self, citations: List[str]) -> Optional[Dict]:
        """
        Check if citations reveal circuit split

        Args:
            citations: List of citations to analyze

        Returns:
            Dictionary describing circuit split if found
        """
        # Group citations by circuit
        circuits = {}

        for citation in citations:
            circuit = self._identify_circuit(citation)
            if circuit:
                if circuit not in circuits:
                    circuits[circuit] = []
                circuits[circuit].append(citation)

        # Check for conflicting holdings
        if len(circuits) >= 2:
            return {
                'split_exists': True,
                'circuits': list(circuits.keys()),
                'description': f"Potential circuit split between {len(circuits)} circuits",
                'recommendation': "Consider Supreme Court review potential"
            }

        return None

    def _identify_circuit(self, citation: str) -> Optional[str]:
        """Identify circuit from citation"""
        import re

        # Look for circuit patterns (e.g., "123 F.3d 456 (9th Cir. 2000)")
        circuit_match = re.search(r'\((\d+)(?:st|nd|rd|th)\s+Cir\.', citation)
        if circuit_match:
            return f"{circuit_match.group(1)}th Circuit"

        # Look for D.C. Circuit
        if 'D.C. Cir' in citation:
            return "D.C. Circuit"

        return None
