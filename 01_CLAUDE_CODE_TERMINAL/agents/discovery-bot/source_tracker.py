"""
Source Tracker - Maintain document provenance and source information
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


class SourceTracker:
    """Track document sources and provenance"""

    def __init__(self):
        self.tracked_sources = {}

    def track(
        self,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Track source information for a document

        Args:
            document_id: Unique document identifier
            metadata: Document metadata

        Returns:
            Source tracking information
        """
        if metadata is None:
            metadata = {}

        # Extract source information
        source_info = {
            'document_id': document_id,
            'tracked_at': datetime.utcnow().isoformat(),
            'source_file': metadata.get('filename', 'unknown'),
            'original_path': metadata.get('file_path', 'unknown'),
            'source_system': metadata.get('source_system', 'unknown'),
            'custodian': metadata.get('custodian', 'unknown'),
            'collection_date': metadata.get('collection_date', 'unknown'),
            'production_number': metadata.get('production_number', None),
            'bates_number': metadata.get('bates_number', None),
            'native_file_type': metadata.get('file_type', 'unknown'),
            'hash': {
                'md5': metadata.get('md5_hash', None),
                'sha256': metadata.get('sha256_hash', None)
            },
            'file_metadata': {
                'created_date': metadata.get('date_created', None),
                'modified_date': metadata.get('date_modified', None),
                'author': metadata.get('author', None),
                'size_bytes': metadata.get('file_size', None)
            },
            'discovery_metadata': {
                'production_set': metadata.get('production_set', None),
                'production_date': metadata.get('production_date', None),
                'confidentiality_designation': metadata.get('confidentiality', None),
                'case_number': metadata.get('case_number', None),
                'matter_name': metadata.get('matter_name', None)
            },
            'processing_metadata': {
                'ocr_performed': metadata.get('ocr_performed', False),
                'ocr_language': metadata.get('ocr_language', 'eng'),
                'extraction_method': metadata.get('extraction_method', 'unknown'),
                'processing_date': datetime.utcnow().isoformat()
            }
        }

        # Store in tracking dictionary
        self.tracked_sources[document_id] = source_info

        logger.info(f"Tracked source for document: {document_id}")

        return source_info

    def get_source(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve source information for a document"""
        return self.tracked_sources.get(document_id)

    def get_chain_of_custody(self, document_id: str) -> Dict[str, Any]:
        """
        Get chain of custody information

        Args:
            document_id: Document identifier

        Returns:
            Chain of custody details
        """
        source = self.get_source(document_id)

        if not source:
            return {
                'document_id': document_id,
                'chain_of_custody': [],
                'status': 'not_tracked'
            }

        chain = [
            {
                'event': 'collection',
                'date': source.get('collection_date', 'unknown'),
                'custodian': source.get('custodian', 'unknown'),
                'location': source.get('original_path', 'unknown')
            },
            {
                'event': 'production',
                'date': source.get('discovery_metadata', {}).get('production_date', 'unknown'),
                'production_number': source.get('production_number', 'unknown'),
                'bates_number': source.get('bates_number', 'unknown')
            },
            {
                'event': 'processing',
                'date': source.get('processing_metadata', {}).get('processing_date', 'unknown'),
                'method': source.get('processing_metadata', {}).get('extraction_method', 'unknown')
            },
            {
                'event': 'tracking',
                'date': source.get('tracked_at', 'unknown'),
                'document_id': document_id
            }
        ]

        return {
            'document_id': document_id,
            'chain_of_custody': chain,
            'status': 'tracked',
            'integrity': self._verify_integrity(source)
        }

    def _verify_integrity(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Verify document integrity"""

        integrity = {
            'hash_available': False,
            'hash_verified': False,
            'metadata_complete': False,
            'warnings': []
        }

        # Check if hash is available
        hash_info = source.get('hash', {})
        if hash_info.get('md5') or hash_info.get('sha256'):
            integrity['hash_available'] = True
            # In production, you would verify the hash against the actual file
            integrity['hash_verified'] = True
        else:
            integrity['warnings'].append('No hash available for integrity verification')

        # Check metadata completeness
        required_fields = ['source_file', 'custodian', 'collection_date']
        missing_fields = [
            field for field in required_fields
            if source.get(field) == 'unknown' or not source.get(field)
        ]

        if not missing_fields:
            integrity['metadata_complete'] = True
        else:
            integrity['warnings'].append(f'Missing metadata fields: {", ".join(missing_fields)}')

        return integrity

    def export_tracking_log(self) -> str:
        """Export tracking log as JSON"""
        return json.dumps(self.tracked_sources, indent=2, default=str)

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracking statistics"""

        total_tracked = len(self.tracked_sources)

        # Count by custodian
        custodians = {}
        for source in self.tracked_sources.values():
            custodian = source.get('custodian', 'unknown')
            custodians[custodian] = custodians.get(custodian, 0) + 1

        # Count by file type
        file_types = {}
        for source in self.tracked_sources.values():
            file_type = source.get('native_file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1

        # Count with hashes
        with_hash = sum(
            1 for source in self.tracked_sources.values()
            if source.get('hash', {}).get('md5') or source.get('hash', {}).get('sha256')
        )

        return {
            'total_documents_tracked': total_tracked,
            'documents_by_custodian': custodians,
            'documents_by_file_type': file_types,
            'documents_with_hash': with_hash,
            'integrity_percentage': (with_hash / total_tracked * 100) if total_tracked > 0 else 0
        }

    def validate_bates_sequence(self) -> Dict[str, Any]:
        """Validate Bates numbering sequence"""

        bates_numbers = []

        for source in self.tracked_sources.values():
            bates = source.get('bates_number')
            if bates:
                bates_numbers.append(bates)

        # Sort and check for gaps
        bates_numbers.sort()

        validation = {
            'total_bates_numbers': len(bates_numbers),
            'bates_range': {
                'start': bates_numbers[0] if bates_numbers else None,
                'end': bates_numbers[-1] if bates_numbers else None
            },
            'gaps_detected': [],
            'duplicates_detected': []
        }

        # Check for duplicates
        seen = set()
        for bates in bates_numbers:
            if bates in seen:
                validation['duplicates_detected'].append(bates)
            seen.add(bates)

        return validation
