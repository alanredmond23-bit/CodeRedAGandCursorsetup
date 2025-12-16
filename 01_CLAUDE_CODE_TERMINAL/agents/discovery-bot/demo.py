"""
Discovery Bot Demo
Demonstrates complete document discovery processing
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from discovery_bot_main import DiscoveryBot

# Load environment
load_dotenv()


# Sample documents for testing
SAMPLE_DOCUMENTS = [
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
        The plaintiff's damages claim of $5 million is overstated based
        on the evidence we have reviewed.

        Key considerations:
        1. Our liability exposure is significant given the contract breach evidence
        2. Trial costs could exceed $500,000
        3. Jury verdict risk is high in this jurisdiction
        4. Settlement now preserves business relationship

        Please keep this confidential as it's protected by attorney-client privilege.

        Best regards,
        John Smith, Esq.
        Senior Counsel, Legal Department
        ''',
        'metadata': {
            'filename': 'email_2024_03_15.eml',
            'date_received': '2024-03-15',
            'case_number': 'CV-2024-001',
            'custodian': 'Sarah Johnson',
            'production_number': 'PROD-001-00123',
            'bates_number': 'ACME-0001234'
        }
    },
    {
        'text': '''
        SALES AGREEMENT

        This Sales Agreement ("Agreement") is entered into as of January 10, 2024,
        by and between Acme Corporation, a Delaware corporation having its principal
        place of business at 123 Main Street, San Francisco, California ("Seller"),
        and Tech Innovations LLC, a California limited liability company having its
        principal place of business at 456 Oak Avenue, Palo Alto, California ("Buyer").

        WHEREAS, Seller manufactures and sells industrial widgets; and
        WHEREAS, Buyer desires to purchase certain products from Seller;

        NOW, THEREFORE, in consideration of the mutual covenants and agreements
        contained herein, the parties agree as follows:

        1. PURCHASE AND SALE
        Seller agrees to sell and Buyer agrees to purchase 500 units of Model X-100
        widgets ("Products") for the total purchase price of Seven Hundred Fifty
        Thousand Dollars ($750,000.00).

        2. PAYMENT TERMS
        Buyer shall pay:
        - 50% down payment ($375,000.00) upon execution of this Agreement
        - Balance ($375,000.00) within 30 days of delivery

        3. DELIVERY
        Seller shall deliver the Products to Buyer's facility in Palo Alto, California
        on or before February 1, 2024.

        4. WARRANTY
        Seller warrants that all Products shall be free from defects in materials and
        workmanship for a period of one (1) year from the date of delivery.

        IN WITNESS WHEREOF, the parties have executed this Agreement as of the date
        first written above.

        ACME CORPORATION                    TECH INNOVATIONS LLC

        /s/ Robert Chen                     /s/ Maria Rodriguez
        Robert Chen                         Maria Rodriguez
        VP Sales                            CEO
        Date: January 10, 2024             Date: January 10, 2024
        ''',
        'metadata': {
            'filename': 'sales_agreement_20240110.pdf',
            'date_created': '2024-01-10',
            'document_type': 'contract',
            'custodian': 'Robert Chen',
            'production_number': 'PROD-001-00456',
            'bates_number': 'ACME-0002345'
        }
    },
    {
        'text': '''
        INTERNAL MEMO

        TO: All Sales Team Members
        FROM: Robert Chen, VP Sales
        DATE: December 5, 2023
        RE: Q4 Sales Targets and Year-End Push

        Team,

        As we enter the final month of Q4, I wanted to update everyone on our progress
        toward year-end sales targets and outline our strategy for closing strong.

        CURRENT STATUS:
        - Q4 Target: $10 million
        - Current: $7.2 million (72% of target)
        - Outstanding proposals: $4.5 million
        - Pipeline: $8 million

        FOCUS AREAS:
        1. Tech Innovations deal ($750K) - expected to close by Jan 10, 2024
        2. Global Systems contract ($1.2M) - in final negotiations
        3. Midwest Manufacturing ($500K) - awaiting purchase approval

        ACTION ITEMS:
        - Follow up on all proposals over $100K
        - Schedule client meetings for week of Dec 11
        - Prepare year-end pricing incentives
        - Update CRM with latest pipeline status

        We're in good position to exceed our target if we execute on these key deals.
        Let's finish the year strong!

        Robert Chen
        VP Sales, Acme Corporation
        rchen@acmecorp.com
        ''',
        'metadata': {
            'filename': 'memo_20231205.docx',
            'date_created': '2023-12-05',
            'author': 'Robert Chen',
            'custodian': 'Robert Chen',
            'production_number': 'PROD-001-00789',
            'bates_number': 'ACME-0003456'
        }
    }
]


async def run_demo():
    """Run complete Discovery Bot demonstration"""

    print("=" * 80)
    print("DISCOVERY BOT DEMONSTRATION")
    print("=" * 80)
    print()

    # Initialize bot
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        print("Please set your API key in .env file")
        return

    print("Initializing Discovery Bot...")
    bot = DiscoveryBot(api_key, config={
        'batch_size': 10,
        'parallel_workers': 3,
        'cache_results': True,
        'enable_validation': True,
        'min_confidence': 0.85
    })
    print("Bot initialized successfully\n")

    # Demo 1: Single document processing
    print("-" * 80)
    print("DEMO 1: Single Document Processing")
    print("-" * 80)
    print()

    print("Processing attorney-client privileged email...")
    result = await bot.process_document(SAMPLE_DOCUMENTS[0])

    print(f"\nDocument ID: {result['document_id']}")
    print(f"Classification: {result['classification']['document_type']} "
          f"(confidence: {result['classification']['confidence']})")
    print(f"Privileged: {result['privilege']['is_privileged']} "
          f"(confidence: {result['privilege']['confidence']})")

    entities = result['entities']
    print(f"\nEntities Extracted:")
    print(f"  - People: {len(entities.get('people', []))}")
    print(f"  - Organizations: {len(entities.get('organizations', []))}")
    print(f"  - Dates: {len(entities.get('dates', []))}")
    print(f"  - Amounts: {len(entities.get('amounts', []))}")

    if entities.get('amounts'):
        print(f"\nMonetary Amounts Found:")
        for amount in entities['amounts']:
            print(f"  - {amount['amount']} ({amount['context']})")

    print(f"\nKeywords (top 3):")
    for kw in result['keywords']['primary_keywords'][:3]:
        print(f"  - {kw['keyword']} (relevance: {kw['relevance']})")

    print(f"\nCost: ${result['cost']['total_cost']:.6f}")
    print(f"Cache Savings: ${result['cost']['cache_savings']:.6f}")

    print("\n" + "=" * 80)
    input("Press Enter to continue to batch processing demo...")
    print()

    # Demo 2: Batch processing
    print("-" * 80)
    print("DEMO 2: Batch Processing (3 documents)")
    print("-" * 80)
    print()

    print("Processing batch of documents...")
    batch_results = await bot.process_batch(SAMPLE_DOCUMENTS, show_progress=True)

    print("\n" + "-" * 80)
    print("BATCH PROCESSING SUMMARY")
    print("-" * 80)

    summary = batch_results['summary']
    print(f"\nProcessing Results:")
    print(f"  Total Documents: {summary['total_documents']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Privileged: {summary['privileged_documents']}")

    print(f"\nDocument Types:")
    for doc_type, count in summary['document_types'].items():
        print(f"  - {doc_type}: {count}")

    print(f"\nTotal Entities Extracted:")
    for entity_type, count in summary['total_entities'].items():
        print(f"  - {entity_type}: {count}")

    print(f"\nTimeline:")
    print(f"  Events: {summary['timeline_events']}")
    timeline = batch_results['timeline']
    if timeline.get('date_range'):
        print(f"  Date Range: {timeline['date_range']['earliest']} to "
              f"{timeline['date_range']['latest']}")
        print(f"  Span: {timeline['date_range']['span_days']} days")

    print(f"\nPerformance:")
    print(f"  Duration: {summary['processing_duration_seconds']:.2f} seconds")
    print(f"  Rate: {summary['documents_per_second']:.2f} docs/second")

    print(f"\nCosts:")
    print(f"  Total: ${summary['total_cost']:.4f}")
    print(f"  Per Document: ${summary['average_cost_per_document']:.6f}")

    print("\n" + "-" * 80)
    print("KEY DATES FROM TIMELINE")
    print("-" * 80)
    for event in timeline.get('key_dates', [])[:5]:
        print(f"\n{event['date']}: {event['description']}")
        print(f"  Type: {event['event_type']}")
        print(f"  Source: {event['source_document'][:16]}...")

    print("\n" + "-" * 80)
    print("PRIVILEGE SUMMARY")
    print("-" * 80)

    for i, result in enumerate(batch_results['results'], 1):
        if 'error' in result:
            continue

        privilege = result['privilege']
        print(f"\nDocument {i}: {result['classification']['document_type']}")
        print(f"  Privileged: {privilege['is_privileged']}")

        if privilege['is_privileged']:
            print(f"  Types: {', '.join(privilege['privilege_types'])}")
            print(f"  Confidence: {privilege['confidence']}")
            print(f"  Redaction: {privilege['redaction_scope']}")

    # Demo 3: Cost estimation
    print("\n" + "=" * 80)
    input("Press Enter to see cost estimation for large project...")
    print()

    print("-" * 80)
    print("DEMO 3: Cost Estimation for Large Discovery Project")
    print("-" * 80)
    print()

    estimate = bot.cost_calculator.estimate_project_cost(
        num_documents=50000,
        avg_doc_length=2000,
        cache_enabled=True,
        cache_hit_rate=0.6
    )

    print("Project: 50,000 document discovery review")
    print(f"Average document length: {estimate['project_scope']['avg_doc_length_tokens']} tokens")
    print(f"Cache enabled: Yes (60% hit rate)")
    print()

    print("Estimated Tokens:")
    print(f"  Input: {estimate['estimated_tokens']['total_input']:,}")
    print(f"  Output: {estimate['estimated_tokens']['total_output']:,}")
    print(f"  Cache reads: {estimate['estimated_tokens']['cache_read']:,}")
    print()

    print("Estimated Costs:")
    print(f"  Total: ${estimate['estimated_costs']['total']:,.2f}")
    print(f"  Per document: ${estimate['estimated_costs']['per_document']:.4f}")
    print(f"  Cache savings: ${estimate['cache_savings']:,.2f}")
    print()

    if estimate.get('cost_comparison'):
        print("Cost Comparison:")
        print(f"  With cache: ${estimate['cost_comparison']['with_cache']:,.2f}")
        print(f"  Without cache: ${estimate['cost_comparison']['without_cache']:,.2f}")
        savings_pct = (1 - estimate['cost_comparison']['with_cache'] /
                       estimate['cost_comparison']['without_cache']) * 100
        print(f"  Savings: {savings_pct:.1f}%")

    # Output file location
    print("\n" + "=" * 80)
    print("OUTPUT FILES")
    print("=" * 80)
    print()
    print("Batch results saved to:")
    print(f"  Output directory: {bot.config['output_dir']}/")
    print(f"  Cache directory: {bot.config['cache_dir']}/")
    print(f"  Log file: discovery_bot.log")
    print()

    print("Sample output structure:")
    print(json.dumps({
        "document_id": "...",
        "classification": {"document_type": "email", "confidence": 0.98},
        "entities": {"people": [], "organizations": [], "dates": []},
        "privilege": {"is_privileged": True, "confidence": 0.95},
        "keywords": {"primary_keywords": []},
        "cost": {"total_cost": 0.061}
    }, indent=2))

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review output files in ./output/ directory")
    print("2. Check example-outputs.json for detailed format")
    print("3. See README.md for integration examples")
    print("4. Adjust configuration in .env for your use case")
    print()


if __name__ == "__main__":
    asyncio.run(run_demo())
