"""
Legal Strategy Bot Package

Comprehensive legal research and strategy analysis system.

CRITICAL DISCLAIMERS:
- For attorney use only
- Not legal advice
- All citations must be independently verified
- Requires licensed attorney review
"""

__version__ = "1.0.0"
__author__ = "Legal Strategy Bot Team"

# Import main components
try:
    from .strategy_bot_main import (
        LegalStrategyBot,
        CaseFacts,
        CaseType,
        Jurisdiction,
        LegalTheory,
        StrategyOutput
    )

    from .westlaw_research import WestlawResearcher
    from .lexisnexis_research import LexisNexisResearcher
    from .precedent_analyzer import PrecedentAnalyzer, AuthorityType, Strength
    from .factual_distinction import FactualDistinguisher, DistinctionType
    from .argument_generator import ArgumentGenerator
    from .counter_argument import CounterArgumentAnalyzer
    from .statute_analyzer import StatuteAnalyzer
    from .case_law_synthesizer import CaseLawSynthesizer
    from .motion_drafter import MotionDrafter
    from .settlement_analyzer import SettlementAnalyzer
    from .validation import CitationValidator, ValidationResult

    __all__ = [
        'LegalStrategyBot',
        'CaseFacts',
        'CaseType',
        'Jurisdiction',
        'LegalTheory',
        'StrategyOutput',
        'WestlawResearcher',
        'LexisNexisResearcher',
        'PrecedentAnalyzer',
        'AuthorityType',
        'Strength',
        'FactualDistinguisher',
        'DistinctionType',
        'ArgumentGenerator',
        'CounterArgumentAnalyzer',
        'StatuteAnalyzer',
        'CaseLawSynthesizer',
        'MotionDrafter',
        'SettlementAnalyzer',
        'CitationValidator',
        'ValidationResult'
    ]

except ImportError as e:
    # If imports fail, package can still be used with direct imports
    import warnings
    warnings.warn(f"Some modules could not be imported: {str(e)}")
    __all__ = []


def get_version():
    """Return the version string"""
    return __version__


def get_disclaimers():
    """Return critical legal disclaimers"""
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
