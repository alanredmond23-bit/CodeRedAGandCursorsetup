"""
Validation - Quality checks before output
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Validator:
    """Validate document processing results for quality and completeness"""

    def __init__(self):
        self.validation_rules = {
            'min_confidence': 0.5,
            'require_classification': True,
            'require_entities': False,
            'require_privilege_check': True,
            'min_entities_for_validation': 1
        }

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single document processing result

        Args:
            result: Document processing result

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []
        validation_checks = []

        # Check 1: Document ID present
        check = self._check_document_id(result)
        validation_checks.append(check)
        if not check['passed']:
            errors.append(check['message'])

        # Check 2: Classification present and valid
        check = self._check_classification(result)
        validation_checks.append(check)
        if not check['passed']:
            if self.validation_rules['require_classification']:
                errors.append(check['message'])
            else:
                warnings.append(check['message'])

        # Check 3: Entity extraction present
        check = self._check_entities(result)
        validation_checks.append(check)
        if not check['passed']:
            if self.validation_rules['require_entities']:
                errors.append(check['message'])
            else:
                warnings.append(check['message'])

        # Check 4: Privilege determination present
        check = self._check_privilege(result)
        validation_checks.append(check)
        if not check['passed']:
            if self.validation_rules['require_privilege_check']:
                errors.append(check['message'])
            else:
                warnings.append(check['message'])

        # Check 5: Confidence scores adequate
        check = self._check_confidence_scores(result)
        validation_checks.append(check)
        if not check['passed']:
            warnings.append(check['message'])

        # Check 6: No processing errors
        check = self._check_processing_errors(result)
        validation_checks.append(check)
        if not check['passed']:
            errors.append(check['message'])

        # Check 7: Source tracking present
        check = self._check_source_tracking(result)
        validation_checks.append(check)
        if not check['passed']:
            warnings.append(check['message'])

        # Check 8: Data consistency
        check = self._check_data_consistency(result)
        validation_checks.append(check)
        if not check['passed']:
            warnings.append(check['message'])

        # Overall validation status
        is_valid = len(errors) == 0
        needs_review = len(warnings) > 0 or not is_valid

        validation_result = {
            'is_valid': is_valid,
            'needs_review': needs_review,
            'errors': errors,
            'warnings': warnings,
            'checks_performed': len(validation_checks),
            'checks_passed': sum(1 for c in validation_checks if c['passed']),
            'validation_checks': validation_checks,
            'validated_at': datetime.utcnow().isoformat()
        }

        if not is_valid:
            logger.warning(
                f"Validation failed for document {result.get('document_id', 'unknown')}: "
                f"{len(errors)} errors, {len(warnings)} warnings"
            )

        return validation_result

    def validate_batch(self, batch_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate batch processing results

        Args:
            batch_result: Batch processing result

        Returns:
            Batch validation summary
        """
        results = batch_result.get('results', [])

        if not results:
            return {
                'is_valid': False,
                'errors': ['No results to validate'],
                'warnings': [],
                'summary': {}
            }

        # Validate each result
        validations = []
        for result in results:
            if 'error' not in result:  # Skip already-failed documents
                validation = result.get('validation')
                if not validation:
                    # Validate if not already validated
                    validation = self.validate(result)
                validations.append(validation)

        # Aggregate statistics
        total_validated = len(validations)
        valid_count = sum(1 for v in validations if v['is_valid'])
        needs_review_count = sum(1 for v in validations if v['needs_review'])

        all_errors = []
        all_warnings = []
        for v in validations:
            all_errors.extend(v.get('errors', []))
            all_warnings.extend(v.get('warnings', []))

        # Batch-level checks
        batch_errors = []
        batch_warnings = []

        # Check timeline validity
        timeline = batch_result.get('timeline', {})
        if not timeline or timeline.get('total_events', 0) == 0:
            batch_warnings.append('No timeline events extracted from batch')

        # Check success rate
        summary = batch_result.get('summary', {})
        total_docs = summary.get('total_documents', 0)
        successful = summary.get('successful', 0)
        success_rate = (successful / total_docs) if total_docs > 0 else 0

        if success_rate < 0.9:
            batch_warnings.append(f'Success rate below 90%: {success_rate*100:.1f}%')

        if success_rate < 0.7:
            batch_errors.append(f'Success rate critically low: {success_rate*100:.1f}%')

        # Check for privileged documents
        privileged = summary.get('privileged_documents', 0)
        if privileged == 0 and total_docs > 10:
            batch_warnings.append('No privileged documents detected (may need review)')

        return {
            'is_valid': len(batch_errors) == 0 and valid_count == total_validated,
            'needs_review': needs_review_count > 0 or len(batch_warnings) > 0,
            'errors': batch_errors,
            'warnings': batch_warnings,
            'summary': {
                'total_documents_validated': total_validated,
                'valid_documents': valid_count,
                'invalid_documents': total_validated - valid_count,
                'documents_needing_review': needs_review_count,
                'total_errors': len(all_errors),
                'total_warnings': len(all_warnings),
                'success_rate': round(success_rate * 100, 2)
            },
            'error_breakdown': self._categorize_errors(all_errors),
            'warning_breakdown': self._categorize_warnings(all_warnings),
            'validated_at': datetime.utcnow().isoformat()
        }

    def _check_document_id(self, result: Dict) -> Dict:
        """Check if document ID is present"""
        doc_id = result.get('document_id')
        return {
            'check': 'document_id',
            'passed': bool(doc_id),
            'message': 'Document ID missing' if not doc_id else 'Document ID present'
        }

    def _check_classification(self, result: Dict) -> Dict:
        """Check if classification is present and valid"""
        classification = result.get('classification', {})

        if not classification:
            return {
                'check': 'classification',
                'passed': False,
                'message': 'Classification missing'
            }

        doc_type = classification.get('document_type')
        confidence = classification.get('confidence', 0)

        if not doc_type:
            return {
                'check': 'classification',
                'passed': False,
                'message': 'Document type not classified'
            }

        if confidence < self.validation_rules['min_confidence']:
            return {
                'check': 'classification',
                'passed': False,
                'message': f'Classification confidence too low: {confidence}'
            }

        return {
            'check': 'classification',
            'passed': True,
            'message': f'Classification valid: {doc_type} (confidence: {confidence})'
        }

    def _check_entities(self, result: Dict) -> Dict:
        """Check if entities were extracted"""
        entities = result.get('entities', {})

        if not entities:
            return {
                'check': 'entities',
                'passed': False,
                'message': 'No entities extracted'
            }

        # Count total entities
        total_entities = sum(
            len(entities.get(key, []))
            for key in ['people', 'organizations', 'dates', 'amounts', 'locations']
        )

        if total_entities < self.validation_rules['min_entities_for_validation']:
            return {
                'check': 'entities',
                'passed': False,
                'message': f'Too few entities extracted: {total_entities}'
            }

        return {
            'check': 'entities',
            'passed': True,
            'message': f'Entities extracted: {total_entities} total'
        }

    def _check_privilege(self, result: Dict) -> Dict:
        """Check if privilege determination was made"""
        privilege = result.get('privilege', {})

        if not privilege:
            return {
                'check': 'privilege',
                'passed': False,
                'message': 'Privilege determination missing'
            }

        is_privileged = privilege.get('is_privileged')
        if is_privileged is None:
            return {
                'check': 'privilege',
                'passed': False,
                'message': 'Privilege determination incomplete'
            }

        confidence = privilege.get('confidence', 0)
        if confidence < self.validation_rules['min_confidence']:
            return {
                'check': 'privilege',
                'passed': True,  # Still pass, but note low confidence
                'message': f'Privilege determination has low confidence: {confidence}'
            }

        return {
            'check': 'privilege',
            'passed': True,
            'message': f'Privilege determined: {is_privileged} (confidence: {confidence})'
        }

    def _check_confidence_scores(self, result: Dict) -> Dict:
        """Check if confidence scores are adequate"""
        low_confidence_items = []

        # Check classification confidence
        classification = result.get('classification', {})
        if classification.get('confidence', 1.0) < self.validation_rules['min_confidence']:
            low_confidence_items.append('classification')

        # Check entity confidences
        entities = result.get('entities', {})
        for entity_type in ['people', 'organizations', 'dates', 'amounts']:
            for entity in entities.get(entity_type, []):
                if entity.get('confidence', 1.0) < self.validation_rules['min_confidence']:
                    low_confidence_items.append(f'{entity_type}:{entity.get("name", "unknown")}')

        if low_confidence_items:
            return {
                'check': 'confidence_scores',
                'passed': False,
                'message': f'Low confidence in: {", ".join(low_confidence_items[:5])}'
            }

        return {
            'check': 'confidence_scores',
            'passed': True,
            'message': 'All confidence scores adequate'
        }

    def _check_processing_errors(self, result: Dict) -> Dict:
        """Check if processing completed without errors"""
        if 'error' in result:
            return {
                'check': 'processing',
                'passed': False,
                'message': f'Processing error: {result["error"]}'
            }

        return {
            'check': 'processing',
            'passed': True,
            'message': 'Processing completed successfully'
        }

    def _check_source_tracking(self, result: Dict) -> Dict:
        """Check if source tracking is present"""
        source = result.get('source', {})

        if not source:
            return {
                'check': 'source_tracking',
                'passed': False,
                'message': 'Source tracking information missing'
            }

        required_fields = ['document_id', 'source_file']
        missing = [f for f in required_fields if not source.get(f)]

        if missing:
            return {
                'check': 'source_tracking',
                'passed': False,
                'message': f'Missing source fields: {", ".join(missing)}'
            }

        return {
            'check': 'source_tracking',
            'passed': True,
            'message': 'Source tracking complete'
        }

    def _check_data_consistency(self, result: Dict) -> Dict:
        """Check for data consistency issues"""
        issues = []

        # Check if document marked privileged but no privilege indicators
        privilege = result.get('privilege', {})
        if privilege.get('is_privileged') and not privilege.get('privilege_indicators'):
            issues.append('Document marked privileged but no indicators provided')

        # Check if dates extracted but no timeline contribution
        entities = result.get('entities', {})
        dates = entities.get('dates', [])
        if len(dates) > 5 and privilege.get('is_privileged'):
            # This is expected - privileged docs might not contribute to timeline
            pass

        if issues:
            return {
                'check': 'data_consistency',
                'passed': False,
                'message': '; '.join(issues)
            }

        return {
            'check': 'data_consistency',
            'passed': True,
            'message': 'Data consistency checks passed'
        }

    def _categorize_errors(self, errors: List[str]) -> Dict[str, int]:
        """Categorize errors by type"""
        categories = {
            'missing_data': 0,
            'low_confidence': 0,
            'processing_error': 0,
            'validation_error': 0,
            'other': 0
        }

        for error in errors:
            error_lower = error.lower()
            if 'missing' in error_lower:
                categories['missing_data'] += 1
            elif 'confidence' in error_lower:
                categories['low_confidence'] += 1
            elif 'processing' in error_lower or 'error' in error_lower:
                categories['processing_error'] += 1
            elif 'validation' in error_lower:
                categories['validation_error'] += 1
            else:
                categories['other'] += 1

        return categories

    def _categorize_warnings(self, warnings: List[str]) -> Dict[str, int]:
        """Categorize warnings by type"""
        return self._categorize_errors(warnings)  # Same logic
