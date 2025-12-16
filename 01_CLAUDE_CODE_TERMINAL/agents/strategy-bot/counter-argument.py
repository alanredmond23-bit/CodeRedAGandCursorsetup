"""
Counter-Argument Analyzer Module

Identifies and analyzes potential counter-arguments from opposing party.
CRITICAL: Must not ignore adverse precedents or opposing arguments.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CounterArgument:
    """Structure for a counter-argument"""
    argument: str
    strength: str  # "strong", "moderate", "weak"
    supporting_authority: List[Dict]
    rebuttal_strategy: str
    rebuttal_cases: List[Dict]
    risk_level: str  # "high", "medium", "low"


class CounterArgumentAnalyzer:
    """
    Analyzes potential counter-arguments from opposing party
    """

    def __init__(self):
        """Initialize counter-argument analyzer"""
        pass

    def analyze_theories(self, theories: List[Any], case_facts: Any) -> List[Any]:
        """
        Add counter-argument analysis to each legal theory

        Args:
            theories: List of LegalTheory objects
            case_facts: Current case facts

        Returns:
            Updated theories with counter-arguments added
        """
        logger.info("Analyzing counter-arguments for each theory")

        for theory in theories:
            counter_args = self._identify_counter_arguments(theory, case_facts)
            theory.counter_arguments = [ca.argument for ca in counter_args]

            # Add detailed counter-argument objects as additional attribute
            theory.detailed_counter_arguments = counter_args

        return theories

    def _identify_counter_arguments(self, theory: Any, case_facts: Any) -> List[CounterArgument]:
        """
        Identify counter-arguments to a legal theory

        Args:
            theory: LegalTheory object
            case_facts: Current case facts

        Returns:
            List of CounterArgument objects
        """
        counter_args = []

        # Generate counter-arguments based on case type
        if case_facts.case_type.value == 'custody':
            counter_args.extend(self._custody_counter_arguments(theory, case_facts))
        elif case_facts.case_type.value == 'federal_criminal':
            counter_args.extend(self._criminal_counter_arguments(theory, case_facts))
        elif case_facts.case_type.value == 'bankruptcy':
            counter_args.extend(self._bankruptcy_counter_arguments(theory, case_facts))

        # General counter-arguments based on theory weaknesses
        counter_args.extend(self._general_counter_arguments(theory, case_facts))

        # Counter-arguments from opposing party's explicit arguments
        if case_facts.opposing_arguments:
            counter_args.extend(
                self._analyze_opposing_arguments(case_facts.opposing_arguments, theory)
            )

        return counter_args

    def _custody_counter_arguments(self, theory: Any, case_facts: Any) -> List[CounterArgument]:
        """Generate custody-specific counter-arguments"""
        counter_args = []

        # Best interests standard counter-argument
        if 'best interest' in theory.theory_name.lower():
            counter_args.append(CounterArgument(
                argument="Status quo presumption: Children's stability should be maintained",
                strength="moderate",
                supporting_authority=[{
                    'citation': 'In re Marriage of Carney, 24 Cal.3d 725 (1979)',
                    'summary': 'Stability and continuity important in custody decisions'
                }],
                rebuttal_strategy="Demonstrate changed circumstances make status quo no longer in best interest",
                rebuttal_cases=[],
                risk_level="medium"
            ))

        # Substance abuse counter-argument
        if 'substance abuse' in theory.theory_name.lower():
            counter_args.append(CounterArgument(
                argument="Past substance abuse is rehabilitated and no longer relevant",
                strength="moderate",
                supporting_authority=[{
                    'citation': 'In re Marriage of Montenegro, 26 Cal.4th 249 (2001)',
                    'summary': 'Past substance abuse alone insufficient without current impact'
                }],
                rebuttal_strategy="Provide evidence of recent/ongoing substance issues affecting parenting",
                rebuttal_cases=[],
                risk_level="medium"
            ))

        # Changed circumstances counter
        if 'changed circumstances' in theory.theory_name.lower():
            counter_args.append(CounterArgument(
                argument="Changes are temporary and not substantial enough to warrant modification",
                strength="strong",
                supporting_authority=[],
                rebuttal_strategy="Document persistent, substantial changes affecting child welfare",
                rebuttal_cases=[],
                risk_level="high"
            ))

        return counter_args

    def _criminal_counter_arguments(self, theory: Any, case_facts: Any) -> List[CounterArgument]:
        """Generate criminal case counter-arguments"""
        counter_args = []

        # Sentencing guidelines
        if 'sentencing' in theory.theory_name.lower():
            counter_args.append(CounterArgument(
                argument="Guidelines range should be followed absent extraordinary circumstances",
                strength="moderate",
                supporting_authority=[{
                    'citation': 'United States v. Booker, 543 U.S. 220 (2005)',
                    'summary': 'Guidelines serve as starting point for sentencing'
                }],
                rebuttal_strategy="Present mitigating factors justifying variance from guidelines",
                rebuttal_cases=[],
                risk_level="medium"
            ))

        # Constitutional challenge
        if 'constitutional' in theory.theory_name.lower():
            counter_args.append(CounterArgument(
                argument="Defendant failed to preserve constitutional issue for appeal",
                strength="strong",
                supporting_authority=[],
                rebuttal_strategy="Demonstrate plain error or show issue was preserved",
                rebuttal_cases=[],
                risk_level="high"
            ))

        return counter_args

    def _bankruptcy_counter_arguments(self, theory: Any, case_facts: Any) -> List[CounterArgument]:
        """Generate bankruptcy counter-arguments"""
        counter_args = []

        counter_args.append(CounterArgument(
            argument="Debtor's claimed exemptions are improper or overstated",
            strength="moderate",
            supporting_authority=[],
            rebuttal_strategy="Provide detailed documentation supporting exemption claims",
            rebuttal_cases=[],
            risk_level="medium"
        ))

        return counter_args

    def _general_counter_arguments(self, theory: Any, case_facts: Any) -> List[CounterArgument]:
        """Generate general counter-arguments based on theory weaknesses"""
        counter_args = []

        # Attack based on identified weaknesses
        for weakness in theory.weaknesses:
            if 'persuasive authority only' in weakness.lower():
                counter_args.append(CounterArgument(
                    argument="Cited precedents are not binding and should not be followed",
                    strength="moderate",
                    supporting_authority=[],
                    rebuttal_strategy="Argue persuasive precedents are well-reasoned and applicable",
                    rebuttal_cases=[],
                    risk_level="medium"
                ))

            elif 'limited factual similarity' in weakness.lower():
                counter_args.append(CounterArgument(
                    argument="Cited cases are factually distinguishable and inapplicable",
                    strength="strong",
                    supporting_authority=[],
                    rebuttal_strategy="Emphasize legal principles transcend factual differences",
                    rebuttal_cases=[],
                    risk_level="high"
                ))

            elif 'older precedent' in weakness.lower():
                counter_args.append(CounterArgument(
                    argument="Precedent is outdated and does not reflect current legal standards",
                    strength="moderate",
                    supporting_authority=[],
                    rebuttal_strategy="Show precedent remains good law and principles still apply",
                    rebuttal_cases=[],
                    risk_level="medium"
                ))

        # Attack based on needed distinctions
        if len(theory.factual_distinctions_needed) > 0:
            counter_args.append(CounterArgument(
                argument="Material factual differences make precedents inapplicable",
                strength="strong",
                supporting_authority=[],
                rebuttal_strategy="Address each distinction and show legal principles still apply",
                rebuttal_cases=[],
                risk_level="high"
            ))

        # Attack based on limited supporting cases
        if len(theory.supporting_cases) < 2:
            counter_args.append(CounterArgument(
                argument="Insufficient case law support for proposed legal theory",
                strength="moderate",
                supporting_authority=[],
                rebuttal_strategy="Emphasize quality over quantity of precedent; cite statute if applicable",
                rebuttal_cases=[],
                risk_level="medium"
            ))

        return counter_args

    def _analyze_opposing_arguments(self, opposing_arguments: List[str],
                                   theory: Any) -> List[CounterArgument]:
        """
        Analyze explicitly stated opposing arguments

        Args:
            opposing_arguments: List of arguments from opposing party
            theory: Current legal theory

        Returns:
            List of CounterArgument objects
        """
        counter_args = []

        for opp_arg in opposing_arguments:
            counter_args.append(CounterArgument(
                argument=opp_arg,
                strength="unknown",  # Would need to analyze
                supporting_authority=[],
                rebuttal_strategy=self._generate_rebuttal_strategy(opp_arg, theory),
                rebuttal_cases=[],
                risk_level="medium"
            ))

        return counter_args

    def _generate_rebuttal_strategy(self, opposing_argument: str, theory: Any) -> str:
        """
        Generate rebuttal strategy for opposing argument

        Args:
            opposing_argument: The counter-argument to rebut
            theory: Our legal theory

        Returns:
            Suggested rebuttal strategy
        """
        # Simplified - would be more sophisticated in production

        opp_lower = opposing_argument.lower()

        if 'status quo' in opp_lower:
            return "Demonstrate material change in circumstances makes status quo no longer appropriate"

        if 'work schedule' in opp_lower or 'availability' in opp_lower:
            return "Show flexibility in work schedule and strong support system"

        if 'treatment' in opp_lower or 'rehabilitation' in opp_lower:
            return "Question genuineness and sustainability of rehabilitation efforts"

        if 'distinguished' in opp_lower or 'different facts' in opp_lower:
            return "Emphasize that legal principles apply despite factual differences"

        # Default
        return "Address opposing argument with specific factual evidence and legal authority"

    def identify_adverse_precedents(self, all_cases: List[Dict],
                                   case_facts: Any) -> List[Dict]:
        """
        Identify adverse precedents that oppose our position

        Args:
            all_cases: All cases found in research
            case_facts: Current case facts

        Returns:
            List of adverse precedent dictionaries
        """
        logger.info("Identifying adverse precedents")

        adverse = []

        for case in all_cases:
            if self._is_adverse_precedent(case, case_facts):
                adverse.append({
                    'case': case,
                    'why_adverse': self._explain_why_adverse(case, case_facts),
                    'distinguish_strategy': self._generate_distinguish_strategy(case, case_facts),
                    'risk_if_not_addressed': self._assess_risk(case)
                })

        logger.info(f"Identified {len(adverse)} adverse precedents")
        return adverse

    def _is_adverse_precedent(self, case: Dict, case_facts: Any) -> bool:
        """Determine if case is adverse to our position"""
        # Simplified - would analyze disposition and holdings in detail

        disposition = case.get('disposition', '').lower()
        summary = case.get('summary', '').lower()

        # Check if outcome is contrary to what we want
        desired = case_facts.desired_outcome.lower()

        # This is oversimplified - would need sophisticated analysis
        if 'denied' in disposition and 'grant' in desired:
            return True

        if 'dismissed' in disposition and 'relief' in desired:
            return True

        return False

    def _explain_why_adverse(self, case: Dict, case_facts: Any) -> str:
        """Explain why this precedent is adverse"""
        return f"Case outcome contrary to desired result in {case_facts.case_type.value} matter"

    def _generate_distinguish_strategy(self, case: Dict, case_facts: Any) -> str:
        """Generate strategy for distinguishing adverse precedent"""
        return "Identify material factual distinctions and show different legal principles apply"

    def _assess_risk(self, case: Dict) -> str:
        """Assess risk posed by adverse precedent"""
        # Based on court level, recency, etc.
        if 'Supreme Court' in case.get('court', ''):
            return "HIGH - Supreme Court precedent"

        year = case.get('year', 0)
        if year >= 2020:
            return "MEDIUM - Recent precedent"

        return "LOW - Can likely distinguish"

    def generate_counter_argument_memo(self, theories: List[Any]) -> str:
        """
        Generate memo section on counter-arguments

        Args:
            theories: List of theories with counter-arguments

        Returns:
            Formatted memo text
        """
        memo = "ANTICIPATED COUNTER-ARGUMENTS AND REBUTTALS\n\n"

        for i, theory in enumerate(theories, 1):
            memo += f"\nTheory {i}: {theory.theory_name}\n"
            memo += "=" * 60 + "\n\n"

            if hasattr(theory, 'detailed_counter_arguments'):
                for j, counter in enumerate(theory.detailed_counter_arguments, 1):
                    memo += f"Counter-Argument {j} ({counter.risk_level.upper()} RISK):\n"
                    memo += f"  {counter.argument}\n\n"
                    memo += f"  Strength: {counter.strength.upper()}\n"

                    if counter.supporting_authority:
                        memo += f"  Opposing Authority:\n"
                        for auth in counter.supporting_authority:
                            memo += f"    - {auth.get('citation')}: {auth.get('summary')}\n"

                    memo += f"\n  Rebuttal Strategy:\n"
                    memo += f"    {counter.rebuttal_strategy}\n\n"
                    memo += "-" * 60 + "\n"

        return memo
