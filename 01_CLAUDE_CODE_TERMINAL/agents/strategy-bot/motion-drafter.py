"""
Motion Drafter Module

Generates motion strategies and draft motion templates based on legal research.
Provides complete motion outlines with citation support.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class MotionDraft:
    """Complete motion draft"""
    motion_type: str
    title: str
    introduction: str
    statement_of_facts: str
    argument_sections: List[Dict]
    conclusion: str
    relief_requested: str
    supporting_citations: List[str]


class MotionDrafter:
    """
    Generates motion drafts and filing strategies
    """

    def __init__(self):
        """Initialize motion drafter"""
        pass

    def generate_strategy(self, theories: List[Any], case_facts: Any) -> Dict:
        """
        Generate motion filing strategy

        Args:
            theories: List of LegalTheory objects
            case_facts: Current case facts

        Returns:
            Dictionary with motion strategy
        """
        logger.info("Generating motion strategy")

        # Determine appropriate motions for case type
        recommended_motions = self._identify_appropriate_motions(case_facts)

        # Generate timeline
        timeline = self._generate_motion_timeline(case_facts)

        # Generate draft for primary motion
        primary_draft = None
        if theories:
            primary_draft = self._draft_motion(
                recommended_motions[0] if recommended_motions else 'motion',
                theories,
                case_facts
            )

        return {
            'recommended_motions': recommended_motions,
            'timeline': timeline,
            'primary_motion_draft': primary_draft,
            'procedural_requirements': self._identify_procedural_requirements(case_facts),
            'supporting_declarations': self._identify_needed_declarations(case_facts)
        }

    def _identify_appropriate_motions(self, case_facts: Any) -> List[str]:
        """Identify appropriate motions for case type"""

        motions = []

        if case_facts.case_type.value == 'custody':
            motions = [
                'Motion for Modification of Custody Order',
                'Motion for Emergency Custody Order',
                'Motion for Supervised Visitation',
                'Request for Order (RFO)'
            ]

        elif case_facts.case_type.value == 'federal_criminal':
            motions = [
                'Motion for Downward Departure from Guidelines',
                'Motion to Suppress Evidence',
                'Motion for New Trial',
                'Motion in Arrest of Judgment'
            ]

        elif case_facts.case_type.value == 'bankruptcy':
            motions = [
                'Motion to Avoid Lien',
                'Motion to Modify Plan',
                'Motion for Relief from Stay',
                'Motion to Dismiss'
            ]

        elif case_facts.case_type.value == 'civil_litigation':
            motions = [
                'Motion for Summary Judgment',
                'Motion to Dismiss',
                'Motion for Preliminary Injunction',
                'Motion in Limine'
            ]

        return motions

    def _generate_motion_timeline(self, case_facts: Any) -> Dict:
        """Generate timeline for motion practice"""

        today = datetime.now()

        timeline = {
            'draft_motion': today + timedelta(days=7),
            'file_motion': today + timedelta(days=14),
            'opposition_due': today + timedelta(days=30),
            'reply_due': today + timedelta(days=37),
            'hearing_date': today + timedelta(days=45)
        }

        return {k: v.strftime('%Y-%m-%d') for k, v in timeline.items()}

    def _draft_motion(self, motion_type: str, theories: List[Any],
                     case_facts: Any) -> MotionDraft:
        """
        Draft a complete motion

        Args:
            motion_type: Type of motion to draft
            theories: Legal theories supporting motion
            case_facts: Case facts

        Returns:
            MotionDraft object
        """

        # Generate title
        title = self._generate_motion_title(motion_type, case_facts)

        # Draft introduction
        introduction = self._draft_introduction(motion_type, theories, case_facts)

        # Draft statement of facts
        facts = self._draft_statement_of_facts(case_facts)

        # Draft argument sections
        arguments = self._draft_argument_sections(theories, case_facts)

        # Draft conclusion
        conclusion = self._draft_conclusion(motion_type, case_facts)

        # Draft relief requested
        relief = self._draft_relief_requested(motion_type, case_facts)

        # Compile citations
        citations = self._compile_citations(theories)

        return MotionDraft(
            motion_type=motion_type,
            title=title,
            introduction=introduction,
            statement_of_facts=facts,
            argument_sections=arguments,
            conclusion=conclusion,
            relief_requested=relief,
            supporting_citations=citations
        )

    def _generate_motion_title(self, motion_type: str, case_facts: Any) -> str:
        """Generate motion title"""

        parties = case_facts.parties

        petitioner = parties.get('petitioner', 'Petitioner')
        respondent = parties.get('respondent', 'Respondent')

        return f"""
{petitioner}
                                                        Petitioner,
v.
{respondent}
                                                        Respondent.

{motion_type.upper()}
"""

    def _draft_introduction(self, motion_type: str, theories: List[Any],
                           case_facts: Any) -> str:
        """Draft motion introduction"""

        intro = f"""
INTRODUCTION

Petitioner {case_facts.parties.get('petitioner', 'Petitioner')} respectfully submits this {motion_type} and requests that this Court grant the following relief:

{case_facts.desired_outcome}

This motion is supported by the following legal authorities and factual circumstances:
"""

        # Add theory summaries
        for i, theory in enumerate(theories[:3], 1):
            intro += f"\n{i}. {theory.theory_name} (Confidence: {theory.confidence_score:.0%})"

        return intro

    def _draft_statement_of_facts(self, case_facts: Any) -> str:
        """Draft statement of facts section"""

        facts = """
STATEMENT OF FACTS

"""

        # Add key dates
        if case_facts.key_dates:
            facts += "Relevant Timeline:\n"
            for event, date in case_facts.key_dates.items():
                facts += f"  • {event.replace('_', ' ').title()}: {date}\n"
            facts += "\n"

        # Add fact summary
        facts += "Factual Background:\n\n"
        facts += case_facts.facts_summary

        return facts

    def _draft_argument_sections(self, theories: List[Any], case_facts: Any) -> List[Dict]:
        """Draft argument sections for each theory"""

        sections = []

        for i, theory in enumerate(theories[:3], 1):  # Top 3 theories
            section = {
                'number': i,
                'heading': theory.theory_name,
                'content': self._draft_argument_content(theory, case_facts),
                'citations': [case.get('citation') for case in theory.supporting_cases]
            }
            sections.append(section)

        return sections

    def _draft_argument_content(self, theory: Any, case_facts: Any) -> str:
        """Draft argument content for a theory"""

        content = f"""
Standard:

{theory.supporting_cases[0].get('holding', 'Legal standard') if theory.supporting_cases else 'See cited authority'}

Application to This Case:

The facts of this case satisfy the legal standard because:
"""

        # Add strengths as arguments
        for strength in theory.strengths:
            content += f"\n  • {strength}"

        content += "\n\nSupporting Authority:\n"

        # Add case citations with holdings
        for case in theory.supporting_cases[:5]:
            content += f"\n  {case.get('citation')}: {case.get('summary', '')[:150]}..."

        # Address weaknesses proactively
        if theory.weaknesses:
            content += "\n\nDistinguishing Contrary Authority:\n"
            for weakness in theory.weaknesses[:3]:
                content += f"\n  • {weakness}"

        return content

    def _draft_conclusion(self, motion_type: str, case_facts: Any) -> str:
        """Draft conclusion section"""

        return f"""
CONCLUSION

For the foregoing reasons, Petitioner respectfully requests that this Court grant this {motion_type} and provide the relief requested herein.

The legal authorities cited demonstrate clear support for the requested relief. The facts of this case warrant the Court's intervention to ensure justice is served.

Respectfully submitted,

Dated: {datetime.now().strftime('%B %d, %Y')}

                                        _________________________
                                        Attorney for Petitioner
"""

    def _draft_relief_requested(self, motion_type: str, case_facts: Any) -> str:
        """Draft relief requested section"""

        relief = """
RELIEF REQUESTED

WHEREFORE, Petitioner requests that this Court:

"""

        # Add specific relief based on desired outcome
        relief += f"1. {case_facts.desired_outcome};\n\n"

        # Add standard relief requests
        relief += "2. Grant such other and further relief as the Court deems just and proper.\n"

        return relief

    def _compile_citations(self, theories: List[Any]) -> List[str]:
        """Compile all citations from theories"""

        citations = []

        for theory in theories:
            for case in theory.supporting_cases:
                citation = case.get('citation')
                if citation and citation not in citations:
                    citations.append(citation)

            for statute in theory.supporting_statutes:
                citation = statute.get('citation')
                if citation and citation not in citations:
                    citations.append(citation)

        return citations

    def _identify_procedural_requirements(self, case_facts: Any) -> List[str]:
        """Identify procedural requirements for filing"""

        requirements = [
            "File motion with court clerk",
            "Serve opposing party (proof of service required)",
            "File proposed order",
            "Pay filing fee (or file fee waiver)"
        ]

        # Add jurisdiction-specific requirements
        if case_facts.jurisdiction.value == 'california':
            requirements.extend([
                "Include declaration under penalty of perjury",
                "Comply with California Rules of Court",
                "Provide proof of service (CCP § 1005)"
            ])

        return requirements

    def _identify_needed_declarations(self, case_facts: Any) -> List[str]:
        """Identify declarations needed to support motion"""

        declarations = [
            "Declaration of Petitioner in support of motion",
            "Declaration of counsel (if necessary)"
        ]

        # Case-specific declarations
        if case_facts.case_type.value == 'custody':
            declarations.extend([
                "Declaration regarding child's best interests",
                "Declaration regarding changed circumstances",
                "Expert declaration (if substance abuse/mental health at issue)"
            ])

        return declarations

    def generate_complete_motion_document(self, motion_draft: MotionDraft) -> str:
        """
        Generate complete formatted motion document

        Args:
            motion_draft: MotionDraft object

        Returns:
            Formatted motion as string
        """

        document = f"""
{motion_draft.title}

{'-' * 70}

{motion_draft.introduction}

{'-' * 70}

{motion_draft.statement_of_facts}

{'-' * 70}

ARGUMENT

"""

        # Add each argument section
        for section in motion_draft.argument_sections:
            document += f"""
{section['number']}. {section['heading'].upper()}

{section['content']}

"""

        document += f"""
{'-' * 70}

{motion_draft.conclusion}

{'-' * 70}

{motion_draft.relief_requested}

{'-' * 70}

TABLE OF AUTHORITIES

Cases:
"""

        for citation in motion_draft.supporting_citations:
            if 'U.S.' in citation or 'Cal.' in citation or 'F.' in citation:
                document += f"  {citation}\n"

        document += "\nStatutes:\n"

        for citation in motion_draft.supporting_citations:
            if 'Code' in citation or '§' in citation or 'U.S.C.' in citation:
                document += f"  {citation}\n"

        return document
