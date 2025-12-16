"""
Discovery Bot - Legal Document Discovery Processing System
"""

from .discovery_bot_main import DiscoveryBot
from .document_classifier import DocumentClassifier
from .entity_extractor import EntityExtractor
from .privilege_detector import PrivilegeDetector
from .timeline_builder import TimelineBuilder
from .keyword_analyzer import KeywordAnalyzer
from .embedding_generator import EmbeddingGenerator
from .source_tracker import SourceTracker
from .batch_processor import BatchProcessor
from .validation import Validator
from .cost_calculator import CostCalculator

__version__ = "1.0.0"
__author__ = "Discovery Bot Team"

__all__ = [
    "DiscoveryBot",
    "DocumentClassifier",
    "EntityExtractor",
    "PrivilegeDetector",
    "TimelineBuilder",
    "KeywordAnalyzer",
    "EmbeddingGenerator",
    "SourceTracker",
    "BatchProcessor",
    "Validator",
    "CostCalculator"
]
