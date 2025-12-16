"""
Discovery Bot - Main Orchestration Engine
Processes legal documents for discovery with classification, extraction, and analysis
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import anthropic
from concurrent.futures import ThreadPoolExecutor
import hashlib

from document_classifier import DocumentClassifier
from entity_extractor import EntityExtractor
from privilege_detector import PrivilegeDetector
from timeline_builder import TimelineBuilder
from keyword_analyzer import KeywordAnalyzer
from embedding_generator import EmbeddingGenerator
from source_tracker import SourceTracker
from batch_processor import BatchProcessor
from validation import Validator
from cost_calculator import CostCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discovery_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DiscoveryBot:
    """Main orchestration engine for document discovery processing"""

    def __init__(self, api_key: str, config: Optional[Dict] = None):
        """
        Initialize Discovery Bot with all components

        Args:
            api_key: Anthropic API key
            config: Optional configuration overrides
        """
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.config = self._load_config(config)

        # Initialize all components
        self.classifier = DocumentClassifier(self.client)
        self.entity_extractor = EntityExtractor(self.client)
        self.privilege_detector = PrivilegeDetector(self.client)
        self.timeline_builder = TimelineBuilder()
        self.keyword_analyzer = KeywordAnalyzer(self.client)
        self.embedding_generator = EmbeddingGenerator(self.client)
        self.source_tracker = SourceTracker()
        self.batch_processor = BatchProcessor(self)
        self.validator = Validator()
        self.cost_calculator = CostCalculator()

        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'privileged': 0,
            'total_cost': 0.0,
            'start_time': None,
            'end_time': None
        }

    def _load_config(self, config: Optional[Dict] = None) -> Dict:
        """Load configuration with defaults"""
        default_config = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 4096,
            'temperature': 0.0,
            'batch_size': 100,
            'parallel_workers': 10,
            'cache_results': True,
            'cache_dir': './cache',
            'output_dir': './output',
            'min_confidence': 0.85,
            'enable_validation': True,
            'save_intermediate': True
        }

        if config:
            default_config.update(config)

        # Create necessary directories
        Path(default_config['cache_dir']).mkdir(parents=True, exist_ok=True)
        Path(default_config['output_dir']).mkdir(parents=True, exist_ok=True)

        return default_config

    async def process_document(
        self,
        document: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single document through the complete pipeline

        Args:
            document: Document dict with 'text', 'metadata', etc.
            document_id: Optional document identifier

        Returns:
            Complete analysis results
        """
        try:
            # Generate document ID if not provided
            if not document_id:
                document_id = self._generate_doc_id(document)

            logger.info(f"Processing document: {document_id}")

            # Check cache first
            if self.config['cache_results']:
                cached = self._get_cached_result(document_id)
                if cached:
                    logger.info(f"Using cached result for {document_id}")
                    return cached

            # Extract document text and metadata
            text = document.get('text', '')
            metadata = document.get('metadata', {})

            if not text or len(text.strip()) < 10:
                raise ValueError(f"Document {document_id} has insufficient text")

            # Track source information
            source_info = self.source_tracker.track(document_id, metadata)

            # Step 1: Classify document type
            logger.info(f"Classifying document {document_id}")
            classification = await self.classifier.classify(text, metadata)

            # Step 2: Extract entities
            logger.info(f"Extracting entities from {document_id}")
            entities = await self.entity_extractor.extract(text, classification)

            # Step 3: Detect privilege
            logger.info(f"Checking privilege for {document_id}")
            privilege = await self.privilege_detector.detect(text, metadata, entities)

            if privilege['is_privileged']:
                self.stats['privileged'] += 1

            # Step 4: Analyze keywords and relevance
            logger.info(f"Analyzing keywords in {document_id}")
            keywords = await self.keyword_analyzer.analyze(text, classification)

            # Step 5: Generate embeddings
            logger.info(f"Generating embeddings for {document_id}")
            embeddings = await self.embedding_generator.generate(text, entities)

            # Compile results
            results = {
                'document_id': document_id,
                'source': source_info,
                'classification': classification,
                'entities': entities,
                'privilege': privilege,
                'keywords': keywords,
                'embeddings': embeddings,
                'processed_at': datetime.utcnow().isoformat(),
                'model_used': self.config['model']
            }

            # Step 6: Validate results
            if self.config['enable_validation']:
                logger.info(f"Validating results for {document_id}")
                validation = self.validator.validate(results)
                results['validation'] = validation

                if not validation['is_valid']:
                    logger.warning(f"Validation failed for {document_id}: {validation['errors']}")

            # Calculate costs
            cost = self.cost_calculator.calculate(results)
            results['cost'] = cost
            self.stats['total_cost'] += cost['total_cost']

            # Cache results
            if self.config['cache_results']:
                self._cache_result(document_id, results)

            # Save intermediate results if configured
            if self.config['save_intermediate']:
                self._save_intermediate(document_id, results)

            self.stats['successful'] += 1
            logger.info(f"Successfully processed {document_id}")

            return results

        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            return {
                'document_id': document_id,
                'error': str(e),
                'status': 'failed',
                'processed_at': datetime.utcnow().isoformat()
            }
        finally:
            self.stats['total_processed'] += 1

    async def process_batch(
        self,
        documents: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Process a batch of documents

        Args:
            documents: List of document dicts
            show_progress: Whether to show progress updates

        Returns:
            Batch processing results with timeline and summary
        """
        logger.info(f"Starting batch processing of {len(documents)} documents")
        self.stats['start_time'] = datetime.utcnow()

        # Process documents in parallel batches
        results = await self.batch_processor.process(
            documents,
            batch_size=self.config['batch_size'],
            parallel_workers=self.config['parallel_workers'],
            show_progress=show_progress
        )

        self.stats['end_time'] = datetime.utcnow()

        # Build timeline from all successful results
        successful_results = [r for r in results if 'error' not in r]
        timeline = self.timeline_builder.build(successful_results)

        # Generate summary statistics
        summary = self._generate_summary(results, timeline)

        # Compile final output
        output = {
            'summary': summary,
            'timeline': timeline,
            'results': results,
            'statistics': self.stats,
            'configuration': self.config
        }

        # Validate entire batch
        if self.config['enable_validation']:
            batch_validation = self.validator.validate_batch(output)
            output['batch_validation'] = batch_validation

        # Save final output
        output_path = self._save_output(output)
        logger.info(f"Batch processing complete. Output saved to {output_path}")

        return output

    def _generate_summary(self, results: List[Dict], timeline: Dict) -> Dict:
        """Generate summary statistics for batch processing"""
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]

        # Document type distribution
        doc_types = {}
        for result in successful:
            doc_type = result.get('classification', {}).get('document_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        # Entity statistics
        total_entities = {
            'people': 0,
            'organizations': 0,
            'dates': 0,
            'amounts': 0,
            'locations': 0
        }

        for result in successful:
            entities = result.get('entities', {})
            for entity_type in total_entities.keys():
                total_entities[entity_type] += len(entities.get(entity_type, []))

        # Privilege statistics
        privileged_count = sum(
            1 for r in successful
            if r.get('privilege', {}).get('is_privileged', False)
        )

        # Calculate processing rate
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            docs_per_second = len(results) / duration if duration > 0 else 0
        else:
            duration = 0
            docs_per_second = 0

        return {
            'total_documents': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'privileged_documents': privileged_count,
            'document_types': doc_types,
            'total_entities': total_entities,
            'timeline_events': len(timeline.get('events', [])),
            'total_cost': self.stats['total_cost'],
            'processing_duration_seconds': duration,
            'documents_per_second': round(docs_per_second, 2),
            'average_cost_per_document': round(
                self.stats['total_cost'] / len(successful) if successful else 0,
                4
            )
        }

    def _generate_doc_id(self, document: Dict) -> str:
        """Generate unique document ID from content hash"""
        text = document.get('text', '')
        metadata = json.dumps(document.get('metadata', {}), sort_keys=True)
        content = f"{text}{metadata}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_cached_result(self, document_id: str) -> Optional[Dict]:
        """Retrieve cached result if available"""
        cache_path = Path(self.config['cache_dir']) / f"{document_id}.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache for {document_id}: {e}")
        return None

    def _cache_result(self, document_id: str, result: Dict) -> None:
        """Cache processing result"""
        try:
            cache_path = Path(self.config['cache_dir']) / f"{document_id}.json"
            with open(cache_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to cache result for {document_id}: {e}")

    def _save_intermediate(self, document_id: str, result: Dict) -> None:
        """Save intermediate results"""
        try:
            intermediate_dir = Path(self.config['output_dir']) / 'intermediate'
            intermediate_dir.mkdir(parents=True, exist_ok=True)

            output_path = intermediate_dir / f"{document_id}.json"
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save intermediate result for {document_id}: {e}")

    def _save_output(self, output: Dict) -> str:
        """Save final batch output"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_path = Path(self.config['output_dir']) / f"discovery_output_{timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        return str(output_path)

    def reset_statistics(self) -> None:
        """Reset processing statistics"""
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'privileged': 0,
            'total_cost': 0.0,
            'start_time': None,
            'end_time': None
        }


async def main():
    """Example usage of Discovery Bot"""
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')

    # Initialize bot
    bot = DiscoveryBot(api_key)

    # Example documents
    documents = [
        {
            'text': '''
            CONFIDENTIAL ATTORNEY-CLIENT COMMUNICATION

            From: John Smith, Senior Counsel <jsmith@lawfirm.com>
            To: Sarah Johnson, CEO <sjohnson@acmecorp.com>
            Date: March 15, 2024
            Re: Settlement Strategy for Jones v. Acme Corp

            Sarah,

            This email contains my legal advice regarding the Jones litigation.
            I recommend we settle for $2.5 million to avoid trial risks.
            The plaintiff's damages claim of $5 million is overstated.

            Please keep this confidential as it's protected by attorney-client privilege.

            Best regards,
            John Smith, Esq.
            ''',
            'metadata': {
                'filename': 'email_2024_03_15.eml',
                'date_received': '2024-03-15',
                'case_number': 'CV-2024-001'
            }
        },
        {
            'text': '''
            SALES AGREEMENT

            This Sales Agreement ("Agreement") is entered into as of January 10, 2024,
            by and between Acme Corporation, a Delaware corporation ("Seller"),
            and Tech Innovations LLC, a California LLC ("Buyer").

            Purchase Price: $750,000.00
            Payment Terms: 50% down, balance within 30 days
            Delivery Date: February 1, 2024

            Products: 500 units of Model X-100 widgets

            Signed:
            Robert Chen, VP Sales, Acme Corporation
            Maria Rodriguez, CEO, Tech Innovations LLC
            ''',
            'metadata': {
                'filename': 'sales_agreement_20240110.pdf',
                'date_created': '2024-01-10',
                'document_type': 'contract'
            }
        }
    ]

    # Process batch
    results = await bot.process_batch(documents, show_progress=True)

    # Print summary
    print("\n" + "="*80)
    print("DISCOVERY BOT PROCESSING SUMMARY")
    print("="*80)
    print(json.dumps(results['summary'], indent=2))
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
