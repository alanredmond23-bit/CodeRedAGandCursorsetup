"""
Timeline Builder - Construct chronological timelines from extracted dates and events
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class TimelineBuilder:
    """Build chronological timelines from document analysis"""

    def __init__(self):
        pass

    def build(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build comprehensive timeline from multiple document results

        Args:
            results: List of document analysis results

        Returns:
            Timeline with events, statistics, and visualizations
        """
        try:
            events = []

            # Extract all dated events from documents
            for result in results:
                if 'error' in result:
                    continue

                doc_id = result.get('document_id', 'unknown')
                doc_type = result.get('classification', {}).get('document_type', 'unknown')
                entities = result.get('entities', {})
                dates = entities.get('dates', [])

                # Process each date as a potential event
                for date_entity in dates:
                    event = self._create_event(date_entity, result, doc_id, doc_type)
                    if event:
                        events.append(event)

            # Sort events chronologically
            events.sort(key=lambda x: x['date'])

            # Build timeline structure
            timeline = {
                'total_events': len(events),
                'date_range': self._get_date_range(events),
                'events': events,
                'events_by_year': self._group_by_year(events),
                'events_by_month': self._group_by_month(events),
                'events_by_type': self._group_by_type(events),
                'key_dates': self._identify_key_dates(events),
                'timeline_statistics': self._calculate_statistics(events)
            }

            return timeline

        except Exception as e:
            logger.error(f"Error building timeline: {e}")
            return {
                'total_events': 0,
                'date_range': {},
                'events': [],
                'events_by_year': {},
                'events_by_month': {},
                'events_by_type': {},
                'key_dates': [],
                'timeline_statistics': {},
                'error': str(e)
            }

    def _create_event(
        self,
        date_entity: Dict,
        result: Dict,
        doc_id: str,
        doc_type: str
    ) -> Optional[Dict]:
        """Create timeline event from date entity"""

        try:
            # Parse date
            date_str = date_entity.get('date')
            if not date_str:
                return None

            # Try to parse as datetime
            try:
                date_obj = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None

            # Extract context and description
            context = date_entity.get('context', 'Date mentioned in document')
            original_format = date_entity.get('original_format', date_str)

            # Determine event type based on context
            event_type = self._categorize_event(context, doc_type)

            # Get related entities from the same document
            entities = result.get('entities', {})
            related_people = [p['name'] for p in entities.get('people', [])[:5]]
            related_orgs = [o['name'] for o in entities.get('organizations', [])[:5]]
            related_amounts = [a['amount'] for a in entities.get('amounts', [])[:3]]

            # Check if this event is from a privileged document
            is_privileged = result.get('privilege', {}).get('is_privileged', False)

            event = {
                'date': date_str,
                'date_object': date_obj.isoformat(),
                'original_format': original_format,
                'description': context,
                'event_type': event_type,
                'source_document': doc_id,
                'document_type': doc_type,
                'is_privileged': is_privileged,
                'confidence': date_entity.get('confidence', 0.5),
                'related_people': related_people,
                'related_organizations': related_orgs,
                'related_amounts': related_amounts,
                'position_in_document': date_entity.get('position', 0)
            }

            return event

        except Exception as e:
            logger.warning(f"Error creating event from date entity: {e}")
            return None

    def _categorize_event(self, context: str, doc_type: str) -> str:
        """Categorize event type based on context"""

        context_lower = context.lower()

        # Categorization logic
        if any(term in context_lower for term in ['filing', 'filed', 'submit']):
            return 'filing'
        elif any(term in context_lower for term in ['deadline', 'due', 'must']):
            return 'deadline'
        elif any(term in context_lower for term in ['agreement', 'contract', 'signed']):
            return 'agreement'
        elif any(term in context_lower for term in ['payment', 'paid', 'invoice']):
            return 'payment'
        elif any(term in context_lower for term in ['meeting', 'deposition', 'hearing']):
            return 'meeting'
        elif any(term in context_lower for term in ['email', 'sent', 'received']):
            return 'communication'
        elif any(term in context_lower for term in ['settlement', 'offer']):
            return 'settlement'
        elif doc_type == 'email':
            return 'communication'
        elif doc_type == 'contract':
            return 'agreement'
        else:
            return 'other'

    def _get_date_range(self, events: List[Dict]) -> Dict:
        """Get date range of timeline"""

        if not events:
            return {}

        dates = [e['date'] for e in events if e.get('date')]
        if not dates:
            return {}

        return {
            'earliest': min(dates),
            'latest': max(dates),
            'span_days': (
                datetime.fromisoformat(max(dates)) -
                datetime.fromisoformat(min(dates))
            ).days
        }

    def _group_by_year(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group events by year"""

        by_year = defaultdict(list)

        for event in events:
            try:
                year = event['date'][:4]  # Extract YYYY
                by_year[year].append(event)
            except (KeyError, IndexError):
                continue

        # Convert to regular dict with counts
        return {
            year: {
                'count': len(year_events),
                'events': year_events
            }
            for year, year_events in sorted(by_year.items())
        }

    def _group_by_month(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group events by month"""

        by_month = defaultdict(list)

        for event in events:
            try:
                month = event['date'][:7]  # Extract YYYY-MM
                by_month[month].append(event)
            except (KeyError, IndexError):
                continue

        # Convert to regular dict with counts
        return {
            month: {
                'count': len(month_events),
                'events': month_events
            }
            for month, month_events in sorted(by_month.items())
        }

    def _group_by_type(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group events by type"""

        by_type = defaultdict(list)

        for event in events:
            event_type = event.get('event_type', 'other')
            by_type[event_type].append(event)

        # Convert to regular dict with counts
        return {
            event_type: {
                'count': len(type_events),
                'events': type_events
            }
            for event_type, type_events in sorted(by_type.items())
        }

    def _identify_key_dates(self, events: List[Dict]) -> List[Dict]:
        """Identify key dates that are likely important"""

        key_dates = []

        # Key date indicators
        key_indicators = [
            'filing', 'deadline', 'settlement', 'signed',
            'agreement', 'trial', 'hearing', 'judgment'
        ]

        for event in events:
            description = event.get('description', '').lower()

            # Check if description contains key indicators
            is_key = any(indicator in description for indicator in key_indicators)

            # High-value amounts also indicate key dates
            related_amounts = event.get('related_amounts', [])
            if related_amounts:
                is_key = True

            # High confidence dates are more likely to be key
            confidence = event.get('confidence', 0)
            if is_key and confidence >= 0.8:
                key_dates.append({
                    'date': event['date'],
                    'description': event['description'],
                    'event_type': event['event_type'],
                    'source_document': event['source_document'],
                    'importance_score': confidence
                })

        # Sort by importance
        key_dates.sort(key=lambda x: x['importance_score'], reverse=True)

        return key_dates[:20]  # Top 20 key dates

    def _calculate_statistics(self, events: List[Dict]) -> Dict:
        """Calculate timeline statistics"""

        if not events:
            return {}

        # Event type distribution
        event_types = defaultdict(int)
        for event in events:
            event_types[event.get('event_type', 'other')] += 1

        # Privileged events
        privileged_count = sum(1 for e in events if e.get('is_privileged', False))

        # High confidence events
        high_confidence = sum(1 for e in events if e.get('confidence', 0) >= 0.85)

        # Documents contributing to timeline
        unique_docs = len(set(e.get('source_document') for e in events))

        return {
            'total_events': len(events),
            'event_type_distribution': dict(event_types),
            'privileged_events': privileged_count,
            'high_confidence_events': high_confidence,
            'documents_with_dates': unique_docs,
            'average_confidence': sum(e.get('confidence', 0) for e in events) / len(events)
        }
