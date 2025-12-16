"""
Cost Calculator - Calculate processing costs per document
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculate API costs for document processing"""

    # Claude Sonnet 4.5 pricing (as of December 2024)
    # Prices per million tokens
    PRICING = {
        'claude-sonnet-4-5-20250929': {
            'input': 3.00,
            'output': 15.00,
            'cache_write': 3.75,  # 25% premium
            'cache_read': 0.30    # 90% discount
        },
        'claude-opus-4-5-20251101': {
            'input': 15.00,
            'output': 75.00,
            'cache_write': 18.75,
            'cache_read': 1.50
        }
    }

    def __init__(self):
        pass

    def calculate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate cost for a single document processing result

        Args:
            result: Document processing result

        Returns:
            Cost breakdown
        """
        try:
            model = result.get('model_used', 'claude-sonnet-4-5-20250929')
            pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])

            # Aggregate token usage from all components
            total_tokens = {
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            }

            # Classification tokens
            classification = result.get('classification', {})
            self._add_tokens(total_tokens, classification.get('tokens_used', {}))

            # Entity extraction tokens
            entities = result.get('entities', {})
            self._add_tokens(total_tokens, entities.get('tokens_used', {}))

            # Privilege detection tokens
            privilege = result.get('privilege', {})
            self._add_tokens(total_tokens, privilege.get('tokens_used', {}))

            # Keyword analysis tokens
            keywords = result.get('keywords', {})
            self._add_tokens(total_tokens, keywords.get('tokens_used', {}))

            # Embedding generation tokens
            embeddings = result.get('embeddings', {})
            self._add_tokens(total_tokens, embeddings.get('tokens_used', {}))

            # Calculate costs
            input_cost = (total_tokens['input'] / 1_000_000) * pricing['input']
            output_cost = (total_tokens['output'] / 1_000_000) * pricing['output']
            cache_write_cost = (total_tokens['cache_creation'] / 1_000_000) * pricing['cache_write']
            cache_read_cost = (total_tokens['cache_read'] / 1_000_000) * pricing['cache_read']

            total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost

            # Calculate savings from caching
            cache_savings = 0
            if total_tokens['cache_read'] > 0:
                # Savings = what we would have paid - what we actually paid
                would_have_paid = (total_tokens['cache_read'] / 1_000_000) * pricing['input']
                actually_paid = cache_read_cost
                cache_savings = would_have_paid - actually_paid

            return {
                'model': model,
                'tokens': total_tokens,
                'costs': {
                    'input': round(input_cost, 6),
                    'output': round(output_cost, 6),
                    'cache_write': round(cache_write_cost, 6),
                    'cache_read': round(cache_read_cost, 6),
                    'total': round(total_cost, 6)
                },
                'total_cost': round(total_cost, 6),
                'cache_savings': round(cache_savings, 6),
                'pricing_info': pricing,
                'calculated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating costs: {e}")
            return {
                'model': 'unknown',
                'tokens': {'input': 0, 'output': 0, 'cache_creation': 0, 'cache_read': 0},
                'costs': {'input': 0, 'output': 0, 'cache_write': 0, 'cache_read': 0, 'total': 0},
                'total_cost': 0,
                'cache_savings': 0,
                'error': str(e)
            }

    def calculate_batch_cost(self, results: list) -> Dict[str, Any]:
        """
        Calculate total cost for batch processing

        Args:
            results: List of document processing results

        Returns:
            Aggregated cost summary
        """
        total_costs = {
            'input': 0,
            'output': 0,
            'cache_write': 0,
            'cache_read': 0,
            'total': 0
        }

        total_tokens = {
            'input': 0,
            'output': 0,
            'cache_creation': 0,
            'cache_read': 0
        }

        total_savings = 0
        doc_costs = []

        for result in results:
            if 'error' in result:
                continue

            cost = result.get('cost')
            if not cost:
                cost = self.calculate(result)

            # Aggregate costs
            for key in total_costs:
                total_costs[key] += cost.get('costs', {}).get(key, 0)

            # Aggregate tokens
            for key in total_tokens:
                total_tokens[key] += cost.get('tokens', {}).get(key, 0)

            total_savings += cost.get('cache_savings', 0)

            doc_costs.append(cost.get('total_cost', 0))

        # Calculate statistics
        num_docs = len([r for r in results if 'error' not in r])

        avg_cost_per_doc = total_costs['total'] / num_docs if num_docs > 0 else 0

        # Find min/max costs
        min_cost = min(doc_costs) if doc_costs else 0
        max_cost = max(doc_costs) if doc_costs else 0

        # Calculate cache efficiency
        total_input_tokens = total_tokens['input'] + total_tokens['cache_creation'] + total_tokens['cache_read']
        cache_hit_rate = (total_tokens['cache_read'] / total_input_tokens) if total_input_tokens > 0 else 0

        return {
            'total_documents': num_docs,
            'total_tokens': total_tokens,
            'total_costs': {
                key: round(value, 4) for key, value in total_costs.items()
            },
            'statistics': {
                'average_cost_per_document': round(avg_cost_per_doc, 6),
                'min_cost': round(min_cost, 6),
                'max_cost': round(max_cost, 6),
                'total_cache_savings': round(total_savings, 4),
                'cache_hit_rate': round(cache_hit_rate * 100, 2),
                'effective_cost_per_document': round(
                    (total_costs['total'] - total_savings) / num_docs if num_docs > 0 else 0,
                    6
                )
            },
            'calculated_at': datetime.utcnow().isoformat()
        }

    def estimate_project_cost(
        self,
        num_documents: int,
        avg_doc_length: int = 2000,
        model: str = 'claude-sonnet-4-5-20250929',
        cache_enabled: bool = True,
        cache_hit_rate: float = 0.5
    ) -> Dict[str, Any]:
        """
        Estimate costs for a project

        Args:
            num_documents: Number of documents to process
            avg_doc_length: Average document length in tokens
            model: Model to use
            cache_enabled: Whether caching is enabled
            cache_hit_rate: Expected cache hit rate (0.0 to 1.0)

        Returns:
            Cost estimate
        """
        pricing = self.PRICING.get(model, self.PRICING['claude-sonnet-4-5-20250929'])

        # Estimate tokens per document
        # Input: document text + system prompts
        # Output: structured results
        input_tokens_per_doc = avg_doc_length + 500  # Add overhead for prompts
        output_tokens_per_doc = 1500  # Estimated structured output

        # Total tokens
        total_input_tokens = num_documents * input_tokens_per_doc
        total_output_tokens = num_documents * output_tokens_per_doc

        if cache_enabled:
            # Split input tokens between cache hits and misses
            cache_read_tokens = int(total_input_tokens * cache_hit_rate)
            regular_input_tokens = total_input_tokens - cache_read_tokens

            input_cost = (regular_input_tokens / 1_000_000) * pricing['input']
            cache_read_cost = (cache_read_tokens / 1_000_000) * pricing['cache_read']
            total_input_cost = input_cost + cache_read_cost
        else:
            total_input_cost = (total_input_tokens / 1_000_000) * pricing['input']
            cache_read_cost = 0

        output_cost = (total_output_tokens / 1_000_000) * pricing['output']
        total_cost = total_input_cost + output_cost

        # Calculate savings from caching
        savings = 0
        if cache_enabled:
            without_cache_cost = (total_input_tokens / 1_000_000) * pricing['input'] + output_cost
            savings = without_cache_cost - total_cost

        return {
            'project_scope': {
                'num_documents': num_documents,
                'avg_doc_length_tokens': avg_doc_length,
                'model': model,
                'cache_enabled': cache_enabled,
                'cache_hit_rate': cache_hit_rate if cache_enabled else 0
            },
            'estimated_tokens': {
                'total_input': total_input_tokens,
                'total_output': total_output_tokens,
                'cache_read': int(total_input_tokens * cache_hit_rate) if cache_enabled else 0
            },
            'estimated_costs': {
                'input': round(total_input_cost, 2),
                'output': round(output_cost, 2),
                'total': round(total_cost, 2),
                'per_document': round(total_cost / num_documents, 4) if num_documents > 0 else 0
            },
            'cache_savings': round(savings, 2) if cache_enabled else 0,
            'cost_comparison': {
                'with_cache': round(total_cost, 2),
                'without_cache': round((total_input_tokens / 1_000_000) * pricing['input'] + output_cost, 2)
            } if cache_enabled else None
        }

    def _add_tokens(self, total: Dict, component: Dict) -> None:
        """Add component token usage to total"""
        total['input'] += component.get('input', 0)
        total['output'] += component.get('output', 0)
        total['cache_creation'] += component.get('cache_creation', 0)
        total['cache_read'] += component.get('cache_read', 0)
