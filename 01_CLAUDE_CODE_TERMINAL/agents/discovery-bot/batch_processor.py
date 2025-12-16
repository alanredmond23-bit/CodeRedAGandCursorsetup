"""
Batch Processor - Process thousands of documents efficiently
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Efficient batch processing of large document sets"""

    def __init__(self, discovery_bot):
        """
        Initialize batch processor

        Args:
            discovery_bot: Reference to main DiscoveryBot instance
        """
        self.bot = discovery_bot

    async def process(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
        parallel_workers: int = 10,
        show_progress: bool = True,
        rate_limit_delay: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Process documents in parallel batches

        Args:
            documents: List of documents to process
            batch_size: Documents per batch
            parallel_workers: Number of parallel workers
            show_progress: Show progress updates
            rate_limit_delay: Delay between requests (seconds)

        Returns:
            List of processing results
        """
        total_docs = len(documents)
        logger.info(f"Starting batch processing of {total_docs} documents")
        logger.info(f"Batch size: {batch_size}, Parallel workers: {parallel_workers}")

        start_time = time.time()
        results = []

        # Split into batches
        batches = [
            documents[i:i + batch_size]
            for i in range(0, total_docs, batch_size)
        ]

        total_batches = len(batches)
        logger.info(f"Split into {total_batches} batches")

        # Process each batch
        for batch_num, batch in enumerate(batches, 1):
            batch_start = time.time()

            if show_progress:
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")

            # Process batch in parallel
            batch_results = await self._process_batch_parallel(
                batch,
                parallel_workers,
                rate_limit_delay
            )

            results.extend(batch_results)

            batch_duration = time.time() - batch_start
            docs_per_second = len(batch) / batch_duration if batch_duration > 0 else 0

            if show_progress:
                processed = len(results)
                successful = sum(1 for r in results if 'error' not in r)
                failed = sum(1 for r in results if 'error' in r)
                progress_pct = (processed / total_docs) * 100

                logger.info(
                    f"Batch {batch_num} complete: "
                    f"{batch_duration:.2f}s, "
                    f"{docs_per_second:.2f} docs/sec, "
                    f"Progress: {progress_pct:.1f}% "
                    f"({processed}/{total_docs}), "
                    f"Success: {successful}, Failed: {failed}"
                )

        total_duration = time.time() - start_time
        overall_rate = total_docs / total_duration if total_duration > 0 else 0

        logger.info(
            f"Batch processing complete: "
            f"{total_docs} documents in {total_duration:.2f}s "
            f"({overall_rate:.2f} docs/sec)"
        )

        return results

    async def _process_batch_parallel(
        self,
        batch: List[Dict[str, Any]],
        parallel_workers: int,
        rate_limit_delay: float
    ) -> List[Dict[str, Any]]:
        """Process a batch with parallel workers"""

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(parallel_workers)

        async def process_with_semaphore(doc, doc_id):
            async with semaphore:
                result = await self.bot.process_document(doc, doc_id)
                if rate_limit_delay > 0:
                    await asyncio.sleep(rate_limit_delay)
                return result

        # Generate document IDs
        doc_ids = [
            doc.get('document_id') or self.bot._generate_doc_id(doc)
            for doc in batch
        ]

        # Process all documents in parallel (but limited by semaphore)
        tasks = [
            process_with_semaphore(doc, doc_id)
            for doc, doc_id in zip(batch, doc_ids)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing document {doc_ids[i]}: {result}")
                processed_results.append({
                    'document_id': doc_ids[i],
                    'error': str(result),
                    'status': 'failed',
                    'processed_at': datetime.utcnow().isoformat()
                })
            else:
                processed_results.append(result)

        return processed_results

    async def process_with_retry(
        self,
        documents: List[Dict[str, Any]],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process documents with retry logic for failures

        Args:
            documents: Documents to process
            max_retries: Maximum retry attempts per document
            retry_delay: Delay between retries (seconds)
            **kwargs: Additional arguments for process()

        Returns:
            Processing results with retry statistics
        """
        retry_stats = {
            'total_attempts': 0,
            'retries_by_document': {},
            'final_failures': []
        }

        # First attempt
        results = await self.process(documents, **kwargs)

        # Extract failures
        failed_docs = []
        failed_indices = []

        for i, result in enumerate(results):
            if 'error' in result:
                failed_docs.append(documents[i])
                failed_indices.append(i)
                doc_id = result.get('document_id', f'doc_{i}')
                retry_stats['retries_by_document'][doc_id] = 0

        # Retry failed documents
        retry_attempt = 0
        while failed_docs and retry_attempt < max_retries:
            retry_attempt += 1
            retry_stats['total_attempts'] += 1

            logger.info(
                f"Retry attempt {retry_attempt}/{max_retries} "
                f"for {len(failed_docs)} failed documents"
            )

            await asyncio.sleep(retry_delay * retry_attempt)  # Exponential backoff

            # Retry
            retry_results = await self.process(
                failed_docs,
                show_progress=False,
                **kwargs
            )

            # Update results
            new_failed_docs = []
            new_failed_indices = []

            for i, (retry_result, orig_idx) in enumerate(zip(retry_results, failed_indices)):
                if 'error' not in retry_result:
                    # Success! Update the result
                    results[orig_idx] = retry_result
                    doc_id = retry_result.get('document_id', f'doc_{orig_idx}')
                    retry_stats['retries_by_document'][doc_id] = retry_attempt
                    logger.info(f"Document {doc_id} succeeded on retry {retry_attempt}")
                else:
                    # Still failing
                    new_failed_docs.append(failed_docs[i])
                    new_failed_indices.append(orig_idx)

            failed_docs = new_failed_docs
            failed_indices = new_failed_indices

        # Record final failures
        if failed_docs:
            for doc, idx in zip(failed_docs, failed_indices):
                doc_id = results[idx].get('document_id', f'doc_{idx}')
                retry_stats['final_failures'].append({
                    'document_id': doc_id,
                    'attempts': max_retries + 1,
                    'error': results[idx].get('error', 'Unknown error')
                })

        return {
            'results': results,
            'retry_statistics': retry_stats,
            'summary': {
                'total_documents': len(documents),
                'successful': len(documents) - len(failed_docs),
                'failed': len(failed_docs),
                'retry_attempts': retry_stats['total_attempts']
            }
        }

    def estimate_processing_time(
        self,
        num_documents: int,
        docs_per_second: float = 2.0
    ) -> Dict[str, Any]:
        """
        Estimate processing time and cost

        Args:
            num_documents: Number of documents to process
            docs_per_second: Expected processing rate

        Returns:
            Time and cost estimates
        """
        total_seconds = num_documents / docs_per_second
        hours = total_seconds / 3600
        minutes = (total_seconds % 3600) / 60

        # Estimate costs (rough estimate)
        # Assuming ~2000 tokens input + 1000 output per document
        input_tokens = num_documents * 2000
        output_tokens = num_documents * 1000

        # Claude Sonnet 4.5 pricing (approximate)
        input_cost_per_million = 3.00
        output_cost_per_million = 15.00

        estimated_cost = (
            (input_tokens / 1_000_000) * input_cost_per_million +
            (output_tokens / 1_000_000) * output_cost_per_million
        )

        return {
            'num_documents': num_documents,
            'estimated_duration': {
                'seconds': int(total_seconds),
                'minutes': int(minutes),
                'hours': round(hours, 2),
                'human_readable': f"{int(hours)}h {int(minutes)}m" if hours >= 1 else f"{int(minutes)}m"
            },
            'estimated_tokens': {
                'input': input_tokens,
                'output': output_tokens,
                'total': input_tokens + output_tokens
            },
            'estimated_cost': {
                'total_usd': round(estimated_cost, 2),
                'per_document_usd': round(estimated_cost / num_documents, 4) if num_documents > 0 else 0
            },
            'assumptions': {
                'docs_per_second': docs_per_second,
                'avg_tokens_per_doc': 3000,
                'model': 'claude-sonnet-4-5'
            }
        }
