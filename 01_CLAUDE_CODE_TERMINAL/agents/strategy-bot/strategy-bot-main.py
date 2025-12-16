"""
Legal Strategy Bot - Main Orchestration Module

CRITICAL GUARDRAILS:
- MUST cite actual case law from Westlaw/LexisNexis
- CANNOT fabricate precedents or citations
- MUST analyze precedents for factual distinctions
- CANNOT give legal advice (attorneys only)
- MUST provide confidence scores for legal theories
- MUST identify counter-arguments
- CANNOT ignore adverse precedents
- MUST tailor strategy to specific case type
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import submodules
from westlaw_research import WestlawResearcher
from lexisnexis_research import LexisNexisResearcher
from precedent_analyzer import PrecedentAnalyzer
from factual_distinction import FactualDistinguisher
from argument_generator import ArgumentGenerator
from counter_argument import CounterArgumentAnalyzer
from statute_analyzer import StatuteAnalyzer
from case_law_synthesizer import CaseLawSynthesizer
from motion_drafter import MotionDrafter
from settlement_analyzer import SettlementAnalyzer
from validation import CitationValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CaseType(Enum):
    """Supported case types"""
    CUSTODY = "custody"
    FEDERAL_CRIMINAL = "federal_criminal"
    BANKRUPTCY = "bankruptcy"
    MEDICAL_MALPRACTICE = "medical_malpractice"
    CIVIL_LITIGATION = "civil_litigation"
    EMPLOYMENT = "employment"
    CONTRACT = "contract"
    PERSONAL_INJURY = "personal_injury"
    FAMILY_LAW = "family_law"
    CORPORATE = "corporate"


class Jurisdiction(Enum):
    """Supported jurisdictions"""
    FEDERAL = "federal"
    STATE_CA = "california"
    STATE_NY = "new_york"
    STATE_TX = "texas"
    STATE_FL = "florida"
    # Add more states as needed


@dataclass
class CaseFacts:
    """Structure for case facts input"""
    case_type: CaseType
    jurisdiction: Jurisdiction
    facts_summary: str
    parties: Dict[str, str]
    key_dates: Dict[str, str]
    legal_issues: List[str]
    desired_outcome: str
    opposing_arguments: Optional[List[str]] = None
    relevant_documents: Optional[List[str]] = None
    budget_hours: Optional[int] = None


@dataclass
class LegalTheory:
    """Structure for legal theories"""
    theory_name: str
    supporting_cases: List[Dict]
    supporting_statutes: List[Dict]
    confidence_score: float  # 0.0 to 1.0
    strengths: List[str]
    weaknesses: List[str]
    factual_distinctions_needed: List[str]
    counter_arguments: List[str]


@dataclass
class StrategyOutput:
    """Complete strategy analysis output"""
    case_id: str
    timestamp: str
    case_facts: CaseFacts
    legal_theories: List[LegalTheory]
    recommended_strategy: Dict
    motion_strategy: Dict
    settlement_analysis: Optional[Dict]
    research_summary: Dict
    citations_verified: bool
    disclaimers: List[str]


class LegalStrategyBot:
    """
    Main orchestration class for legal strategy research and analysis.

    IMPORTANT DISCLAIMERS:
    - This tool is for attorney use only
    - Does not provide legal advice
    - All outputs must be reviewed by licensed attorney
    - Citations must be independently verified
    - Not a substitute for professional legal judgment
    """

    def __init__(self, westlaw_api_key: str = None, lexis_api_key: str = None):
        """
        Initialize the Legal Strategy Bot

        Args:
            westlaw_api_key: API key for Westlaw access
            lexis_api_key: API key for LexisNexis access
        """
        # API keys from environment or parameters
        self.westlaw_api_key = westlaw_api_key or os.getenv('WESTLAW_API_KEY')
        self.lexis_api_key = lexis_api_key or os.getenv('LEXISNEXIS_API_KEY')

        # Initialize research modules
        self.westlaw = WestlawResearcher(self.westlaw_api_key) if self.westlaw_api_key else None
        self.lexis = LexisNexisResearcher(self.lexis_api_key) if self.lexis_api_key else None

        # Initialize analysis modules
        self.precedent_analyzer = PrecedentAnalyzer()
        self.factual_distinguisher = FactualDistinguisher()
        self.argument_generator = ArgumentGenerator()
        self.counter_analyzer = CounterArgumentAnalyzer()
        self.statute_analyzer = StatuteAnalyzer()
        self.synthesizer = CaseLawSynthesizer()
        self.motion_drafter = MotionDrafter()
        self.settlement_analyzer = SettlementAnalyzer()
        self.validator = CitationValidator(self.westlaw, self.lexis)

        logger.info("Legal Strategy Bot initialized")

    def analyze_case(self, case_facts: CaseFacts) -> StrategyOutput:
        """
        Main analysis pipeline for case strategy

        Args:
            case_facts: CaseFacts object with all relevant case information

        Returns:
            StrategyOutput with complete legal analysis
        """
        logger.info(f"Starting analysis for {case_facts.case_type.value} case")

        # Generate unique case ID
        case_id = self._generate_case_id(case_facts)

        try:
            # Step 1: Research relevant case law
            logger.info("Step 1: Researching case law...")
            case_law = self._research_case_law(case_facts)

            # Step 2: Research relevant statutes
            logger.info("Step 2: Researching statutes...")
            statutes = self._research_statutes(case_facts)

            # Step 3: Analyze precedents
            logger.info("Step 3: Analyzing precedents...")
            precedent_analysis = self._analyze_precedents(case_law, case_facts)

            # Step 4: Identify factual distinctions
            logger.info("Step 4: Identifying factual distinctions...")
            distinctions = self._identify_distinctions(precedent_analysis, case_facts)

            # Step 5: Generate legal theories
            logger.info("Step 5: Generating legal theories...")
            theories = self._generate_theories(
                precedent_analysis,
                statutes,
                distinctions,
                case_facts
            )

            # Step 6: Identify counter-arguments
            logger.info("Step 6: Analyzing counter-arguments...")
            theories = self._add_counter_arguments(theories, case_facts)

            # Step 7: Synthesize case law
            logger.info("Step 7: Synthesizing case law...")
            synthesis = self._synthesize_case_law(case_law, case_facts)

            # Step 8: Generate recommended strategy
            logger.info("Step 8: Generating strategy recommendations...")
            strategy = self._generate_strategy(theories, case_facts)

            # Step 9: Generate motion strategy
            logger.info("Step 9: Developing motion strategy...")
            motion_strategy = self._generate_motion_strategy(theories, case_facts)

            # Step 10: Settlement analysis (if applicable)
            logger.info("Step 10: Analyzing settlement options...")
            settlement = self._analyze_settlement(case_law, case_facts)

            # Step 11: Validate all citations
            logger.info("Step 11: Validating citations...")
            citations_valid = self._validate_citations(theories)

            # Step 12: Compile output
            logger.info("Step 12: Compiling final output...")
            output = StrategyOutput(
                case_id=case_id,
                timestamp=datetime.now().isoformat(),
                case_facts=case_facts,
                legal_theories=theories,
                recommended_strategy=strategy,
                motion_strategy=motion_strategy,
                settlement_analysis=settlement,
                research_summary={
                    'total_cases_reviewed': len(case_law),
                    'statutes_analyzed': len(statutes),
                    'theories_generated': len(theories),
                    'synthesis': synthesis
                },
                citations_verified=citations_valid,
                disclaimers=self._get_disclaimers()
            )

            # Save output
            self._save_output(output)

            logger.info(f"Analysis complete for case {case_id}")
            return output

        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            raise

    def _research_case_law(self, case_facts: CaseFacts) -> List[Dict]:
        """Research relevant case law from both Westlaw and LexisNexis"""
        all_cases = []

        # Build search queries based on case type and issues
        queries = self._build_search_queries(case_facts)

        # Search Westlaw
        if self.westlaw:
            for query in queries:
                westlaw_results = self.westlaw.search(
                    query=query,
                    jurisdiction=case_facts.jurisdiction.value,
                    max_results=50
                )
                all_cases.extend(westlaw_results)

        # Search LexisNexis
        if self.lexis:
            for query in queries:
                lexis_results = self.lexis.search(
                    query=query,
                    jurisdiction=case_facts.jurisdiction.value,
                    max_results=50
                )
                all_cases.extend(lexis_results)

        # Remove duplicates and rank by relevance
        unique_cases = self._deduplicate_cases(all_cases)
        ranked_cases = self._rank_cases(unique_cases, case_facts)

        logger.info(f"Found {len(ranked_cases)} relevant cases")
        return ranked_cases

    def _research_statutes(self, case_facts: CaseFacts) -> List[Dict]:
        """Research relevant statutes"""
        return self.statute_analyzer.find_applicable_statutes(
            case_type=case_facts.case_type,
            jurisdiction=case_facts.jurisdiction,
            legal_issues=case_facts.legal_issues
        )

    def _analyze_precedents(self, case_law: List[Dict], case_facts: CaseFacts) -> Dict:
        """Analyze precedents for applicability"""
        return self.precedent_analyzer.analyze(
            cases=case_law,
            case_facts=case_facts
        )

    def _identify_distinctions(self, precedent_analysis: Dict, case_facts: CaseFacts) -> Dict:
        """Identify factual distinctions from precedents"""
        return self.factual_distinguisher.analyze(
            precedent_analysis=precedent_analysis,
            case_facts=case_facts
        )

    def _generate_theories(self, precedent_analysis: Dict, statutes: List[Dict],
                          distinctions: Dict, case_facts: CaseFacts) -> List[LegalTheory]:
        """Generate legal theories with confidence scores"""
        return self.argument_generator.generate_theories(
            precedent_analysis=precedent_analysis,
            statutes=statutes,
            distinctions=distinctions,
            case_facts=case_facts
        )

    def _add_counter_arguments(self, theories: List[LegalTheory],
                               case_facts: CaseFacts) -> List[LegalTheory]:
        """Add counter-argument analysis to theories"""
        return self.counter_analyzer.analyze_theories(
            theories=theories,
            case_facts=case_facts
        )

    def _synthesize_case_law(self, case_law: List[Dict], case_facts: CaseFacts) -> Dict:
        """Synthesize multiple cases into coherent analysis"""
        return self.synthesizer.synthesize(
            cases=case_law,
            case_facts=case_facts
        )

    def _generate_strategy(self, theories: List[LegalTheory], case_facts: CaseFacts) -> Dict:
        """Generate recommended legal strategy"""
        # Sort theories by confidence score
        sorted_theories = sorted(theories, key=lambda x: x.confidence_score, reverse=True)

        return {
            'primary_theory': sorted_theories[0] if sorted_theories else None,
            'alternative_theories': sorted_theories[1:4] if len(sorted_theories) > 1 else [],
            'recommended_approach': self._determine_approach(sorted_theories, case_facts),
            'risks': self._identify_risks(sorted_theories),
            'timeline': self._generate_timeline(case_facts),
            'resources_needed': self._estimate_resources(case_facts)
        }

    def _generate_motion_strategy(self, theories: List[LegalTheory],
                                  case_facts: CaseFacts) -> Dict:
        """Generate motion filing strategy"""
        return self.motion_drafter.generate_strategy(
            theories=theories,
            case_facts=case_facts
        )

    def _analyze_settlement(self, case_law: List[Dict], case_facts: CaseFacts) -> Optional[Dict]:
        """Analyze settlement options and precedents"""
        if case_facts.case_type in [CaseType.FEDERAL_CRIMINAL]:
            return None  # No settlement in criminal cases

        return self.settlement_analyzer.analyze(
            case_law=case_law,
            case_facts=case_facts
        )

    def _validate_citations(self, theories: List[LegalTheory]) -> bool:
        """Validate all citations are accurate"""
        all_cases = []
        for theory in theories:
            all_cases.extend(theory.supporting_cases)

        return self.validator.validate_all(all_cases)

    def _build_search_queries(self, case_facts: CaseFacts) -> List[str]:
        """Build search queries based on case facts"""
        queries = []

        # Query for each legal issue
        for issue in case_facts.legal_issues:
            queries.append(f"{issue} AND {case_facts.case_type.value}")

        # Query for desired outcome
        if case_facts.desired_outcome:
            queries.append(f"{case_facts.desired_outcome} AND {case_facts.case_type.value}")

        return queries

    def _deduplicate_cases(self, cases: List[Dict]) -> List[Dict]:
        """Remove duplicate cases"""
        seen = set()
        unique = []

        for case in cases:
            case_id = case.get('citation', '') + case.get('title', '')
            if case_id not in seen:
                seen.add(case_id)
                unique.append(case)

        return unique

    def _rank_cases(self, cases: List[Dict], case_facts: CaseFacts) -> List[Dict]:
        """Rank cases by relevance"""
        # Simple ranking by year (newer is better) and keyword matches
        # More sophisticated ranking can be implemented
        return sorted(cases, key=lambda x: x.get('year', 0), reverse=True)

    def _determine_approach(self, theories: List[LegalTheory], case_facts: CaseFacts) -> str:
        """Determine recommended legal approach"""
        if not theories:
            return "Insufficient precedent - consider alternative dispute resolution"

        top_theory = theories[0]
        if top_theory.confidence_score > 0.8:
            return "Aggressive litigation - strong precedent support"
        elif top_theory.confidence_score > 0.6:
            return "Moderate litigation - proceed with caution"
        else:
            return "Settlement focus - weak precedent support"

    def _identify_risks(self, theories: List[LegalTheory]) -> List[str]:
        """Identify litigation risks"""
        risks = []

        for theory in theories:
            risks.extend(theory.weaknesses)
            risks.extend(theory.counter_arguments)

        return list(set(risks))[:10]  # Top 10 unique risks

    def _generate_timeline(self, case_facts: CaseFacts) -> Dict:
        """Generate case timeline"""
        # Simplified timeline - can be made more sophisticated
        return {
            'immediate': 'File initial motions within 30 days',
            'short_term': 'Discovery period: 3-6 months',
            'medium_term': 'Motion practice: 6-9 months',
            'trial': 'Trial preparation: 12-18 months'
        }

    def _estimate_resources(self, case_facts: CaseFacts) -> Dict:
        """Estimate resources needed"""
        hours = case_facts.budget_hours or 100

        return {
            'attorney_hours': hours,
            'estimated_cost_range': f"${hours * 300} - ${hours * 500}",
            'expert_witnesses': 'TBD based on case complexity',
            'discovery_costs': 'TBD'
        }

    def _generate_case_id(self, case_facts: CaseFacts) -> str:
        """Generate unique case ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        case_type = case_facts.case_type.value[:3].upper()
        return f"{case_type}-{timestamp}"

    def _get_disclaimers(self) -> List[str]:
        """Get required legal disclaimers"""
        return [
            "This analysis is for attorney use only and does not constitute legal advice.",
            "All citations must be independently verified before use in court filings.",
            "This tool is not a substitute for professional legal judgment.",
            "Confidence scores are computational estimates only.",
            "All outputs must be reviewed by a licensed attorney.",
            "Past case results do not guarantee future outcomes.",
            "Applicable law may have changed since research completion.",
            "Jurisdiction-specific rules and local procedures must be verified."
        ]

    def _save_output(self, output: StrategyOutput) -> None:
        """Save analysis output to file"""
        filename = f"strategy_output_{output.case_id}.json"

        # Convert to dict (handling special types)
        output_dict = {
            'case_id': output.case_id,
            'timestamp': output.timestamp,
            'case_facts': {
                'case_type': output.case_facts.case_type.value,
                'jurisdiction': output.case_facts.jurisdiction.value,
                'facts_summary': output.case_facts.facts_summary,
                'parties': output.case_facts.parties,
                'key_dates': output.case_facts.key_dates,
                'legal_issues': output.case_facts.legal_issues,
                'desired_outcome': output.case_facts.desired_outcome
            },
            'legal_theories': [
                {
                    'theory_name': t.theory_name,
                    'confidence_score': t.confidence_score,
                    'supporting_cases': t.supporting_cases,
                    'supporting_statutes': t.supporting_statutes,
                    'strengths': t.strengths,
                    'weaknesses': t.weaknesses,
                    'factual_distinctions_needed': t.factual_distinctions_needed,
                    'counter_arguments': t.counter_arguments
                }
                for t in output.legal_theories
            ],
            'recommended_strategy': output.recommended_strategy,
            'motion_strategy': output.motion_strategy,
            'settlement_analysis': output.settlement_analysis,
            'research_summary': output.research_summary,
            'citations_verified': output.citations_verified,
            'disclaimers': output.disclaimers
        }

        with open(filename, 'w') as f:
            json.dump(output_dict, f, indent=2)

        logger.info(f"Output saved to {filename}")

    def generate_memo(self, strategy_output: StrategyOutput) -> str:
        """
        Generate formal legal memorandum from strategy output

        Args:
            strategy_output: StrategyOutput object

        Returns:
            Formatted legal memorandum as string
        """
        memo = f"""
LEGAL MEMORANDUM

TO: Reviewing Attorney
FROM: Legal Strategy Bot
DATE: {strategy_output.timestamp}
RE: Case Analysis - {strategy_output.case_id}

{'=' * 80}

I. CASE SUMMARY

Case Type: {strategy_output.case_facts.case_type.value.upper()}
Jurisdiction: {strategy_output.case_facts.jurisdiction.value.upper()}

Facts:
{strategy_output.case_facts.facts_summary}

Desired Outcome:
{strategy_output.case_facts.desired_outcome}

{'=' * 80}

II. LEGAL ISSUES PRESENTED

"""
        for i, issue in enumerate(strategy_output.case_facts.legal_issues, 1):
            memo += f"{i}. {issue}\n"

        memo += f"""
{'=' * 80}

III. LEGAL THEORIES ANALYZED

Total Cases Reviewed: {strategy_output.research_summary['total_cases_reviewed']}
Statutes Analyzed: {strategy_output.research_summary['statutes_analyzed']}
Theories Generated: {strategy_output.research_summary['theories_generated']}

"""

        for i, theory in enumerate(strategy_output.legal_theories, 1):
            memo += f"""
THEORY {i}: {theory.theory_name}
Confidence Score: {theory.confidence_score:.1%}

Supporting Precedents ({len(theory.supporting_cases)}):
"""
            for case in theory.supporting_cases[:5]:  # Top 5
                memo += f"  - {case.get('citation', 'N/A')}: {case.get('summary', 'N/A')}\n"

            memo += f"""
Strengths:
"""
            for strength in theory.strengths:
                memo += f"  + {strength}\n"

            memo += f"""
Weaknesses:
"""
            for weakness in theory.weaknesses:
                memo += f"  - {weakness}\n"

            memo += f"""
Counter-Arguments to Address:
"""
            for counter in theory.counter_arguments:
                memo += f"  ! {counter}\n"

            memo += "\n" + "-" * 80 + "\n"

        memo += f"""
{'=' * 80}

IV. RECOMMENDED STRATEGY

{strategy_output.recommended_strategy.get('recommended_approach', 'N/A')}

Primary Theory: {strategy_output.recommended_strategy.get('primary_theory').theory_name if strategy_output.recommended_strategy.get('primary_theory') else 'N/A'}

Timeline:
"""
        timeline = strategy_output.recommended_strategy.get('timeline', {})
        for phase, description in timeline.items():
            memo += f"  {phase.upper()}: {description}\n"

        memo += f"""
Resources Required:
  Attorney Hours: {strategy_output.recommended_strategy.get('resources_needed', {}).get('attorney_hours', 'N/A')}
  Estimated Cost: {strategy_output.recommended_strategy.get('resources_needed', {}).get('estimated_cost_range', 'N/A')}

{'=' * 80}

V. MOTION STRATEGY

{json.dumps(strategy_output.motion_strategy, indent=2)}

{'=' * 80}

VI. SETTLEMENT ANALYSIS

{json.dumps(strategy_output.settlement_analysis, indent=2) if strategy_output.settlement_analysis else 'N/A - Not applicable for this case type'}

{'=' * 80}

VII. CITATIONS VERIFICATION

All citations verified: {'YES' if strategy_output.citations_verified else 'NO - REQUIRES MANUAL VERIFICATION'}

{'=' * 80}

VIII. DISCLAIMERS

"""
        for disclaimer in strategy_output.disclaimers:
            memo += f"* {disclaimer}\n"

        memo += f"""
{'=' * 80}

END OF MEMORANDUM
"""

        return memo


def main():
    """Example usage of Legal Strategy Bot"""

    # Initialize bot
    bot = LegalStrategyBot()

    # Example: Custody case
    case_facts = CaseFacts(
        case_type=CaseType.CUSTODY,
        jurisdiction=Jurisdiction.STATE_CA,
        facts_summary="""
        Father seeking primary custody of two minor children (ages 5 and 7).
        Mother currently has primary custody. Father alleges mother has substance
        abuse issues and unstable housing. Mother denies allegations. Children
        have lived primarily with mother for past 3 years. Father has steady
        employment and stable home. No history of domestic violence.
        """,
        parties={
            'petitioner': 'John Doe (Father)',
            'respondent': 'Jane Doe (Mother)',
            'children': 'Child A (age 7), Child B (age 5)'
        },
        key_dates={
            'marriage': '2015-06-01',
            'separation': '2021-03-15',
            'initial_custody_order': '2021-09-01'
        },
        legal_issues=[
            'Best interests of the child standard',
            'Material change in circumstances',
            'Substance abuse impact on custody',
            'Housing stability factors',
            'Children\'s preference consideration'
        ],
        desired_outcome='Primary physical custody to father with supervised visitation for mother',
        opposing_arguments=[
            'Status quo should be maintained',
            'Father\'s work schedule limits availability',
            'Mother has completed treatment program'
        ],
        budget_hours=150
    )

    # Run analysis
    print("Starting legal strategy analysis...")
    output = bot.analyze_case(case_facts)

    # Generate memo
    print("\nGenerating legal memorandum...")
    memo = bot.generate_memo(output)

    # Save memo
    memo_filename = f"legal_memo_{output.case_id}.txt"
    with open(memo_filename, 'w') as f:
        f.write(memo)

    print(f"\nAnalysis complete!")
    print(f"JSON output: strategy_output_{output.case_id}.json")
    print(f"Memo output: {memo_filename}")
    print(f"\nTheories generated: {len(output.legal_theories)}")
    print(f"Citations verified: {output.citations_verified}")


if __name__ == "__main__":
    main()
