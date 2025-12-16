"""
MCP Integration Usage Examples
Demonstrates real-world workflows for legal research and eDiscovery
"""

import json
from datetime import datetime, timedelta

def example_legal_research():
    """Example: Comprehensive legal research across multiple sources"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Comprehensive Legal Research")
    print("="*60)

    from westlaw_mcp_server import create_westlaw_mcp
    from lexisnexis_mcp_server import create_lexisnexis_mcp
    from supabase_mcp_server import create_supabase_mcp

    # Initialize MCPs
    westlaw = create_westlaw_mcp()
    lexis = create_lexisnexis_mcp()
    supabase = create_supabase_mcp()

    # Research topic
    research_query = "attorney-client privilege waiver"
    jurisdiction = "federal"

    print(f"\nResearching: {research_query}")
    print(f"Jurisdiction: {jurisdiction}")

    # Search Westlaw
    print("\n1. Searching Westlaw...")
    westlaw_results = westlaw.search_cases(
        query=research_query,
        jurisdiction=jurisdiction,
        limit=10
    )

    if not westlaw_results.get('error'):
        print(f"   Found {westlaw_results['total_results']} cases on Westlaw")
        for case in westlaw_results['cases'][:3]:
            print(f"   - {case['citation']}: {case['title']}")

    # Search LexisNexis
    print("\n2. Searching LexisNexis...")
    lexis_results = lexis.search_cases(
        query=research_query,
        jurisdiction=jurisdiction,
        limit=10
    )

    if not lexis_results.get('error'):
        print(f"   Found {lexis_results['total_results']} cases on LexisNexis")
        for case in lexis_results['cases'][:3]:
            print(f"   - {case['citation']}: {case['title']}")

    # Log research in database
    print("\n3. Logging research query...")
    supabase.log_research_query(
        service="westlaw",
        query=research_query,
        results_count=westlaw_results.get('total_results', 0),
        user="attorney@firm.com"
    )

    supabase.log_research_query(
        service="lexisnexis",
        query=research_query,
        results_count=lexis_results.get('total_results', 0),
        user="attorney@firm.com"
    )

    print("   Research logged to database")

    # Get citation analysis
    if westlaw_results.get('cases'):
        first_case = westlaw_results['cases'][0]
        citation = first_case['citation']

        print(f"\n4. Shepardizing {citation}...")
        treatment = westlaw.shepardize(citation)

        if not treatment.get('error'):
            print(f"   Treatment: {treatment['treatment']}")
            print(f"   Cited by: {treatment['cited_by_count']} cases")


def example_email_discovery():
    """Example: Email discovery with privilege detection"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Email Discovery with Privilege Detection")
    print("="*60)

    from gmail_discovery_mcp import create_gmail_discovery_mcp
    from supabase_mcp_server import create_supabase_mcp

    # Initialize MCPs
    gmail = create_gmail_discovery_mcp()
    supabase = create_supabase_mcp()

    # Discovery parameters
    case_id = "case_2024_001"
    search_query = "contract negotiations Alpha Corp"
    date_from = "2024/01/01"
    date_to = "2024/12/31"

    print(f"\nCase ID: {case_id}")
    print(f"Search Query: {search_query}")
    print(f"Date Range: {date_from} to {date_to}")

    # Search emails
    print("\n1. Searching emails...")
    results = gmail.search_emails(
        query=search_query,
        date_from=date_from,
        date_to=date_to,
        max_results=50
    )

    if not results.get('error'):
        print(f"   Found {results['total_results']} emails")
        print(f"   Privileged: {results['privileged_count']} emails flagged")

        # Save to database
        print("\n2. Saving discovery items to database...")
        saved_count = 0

        for email in results['emails']:
            result = supabase.save_discovery_item(
                item_type="email",
                source="gmail",
                item_id=email['id'],
                content=email,
                privileged=email['privilege_flagged'],
                case_id=case_id
            )

            if result.get('success'):
                saved_count += 1

        print(f"   Saved {saved_count} emails to database")

        # Export non-privileged for production
        print("\n3. Exporting for production...")
        export = gmail.export_for_discovery(
            query=search_query,
            date_from=date_from,
            date_to=date_to,
            include_privileged=False
        )

        print(f"   Exported: {export['total_exported']} emails")
        print(f"   Privileged excluded: {export['privileged_excluded']}")

        # Show privileged examples
        if results['privileged_count'] > 0:
            print("\n4. Privileged emails detected:")
            for email in results['emails']:
                if email['privilege_flagged']:
                    print(f"   - From: {email['from']}")
                    print(f"     Subject: {email['subject']}")
                    print(f"     Confidence: {email['privilege_confidence']}")
                    print(f"     Indicators: {len(email['privilege_indicators'])}")
                    print()


def example_slack_discovery():
    """Example: Slack message discovery"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Slack Message Discovery")
    print("="*60)

    from slack_discovery_mcp import create_slack_discovery_mcp
    from supabase_mcp_server import create_supabase_mcp

    # Initialize MCPs
    slack = create_slack_discovery_mcp()
    supabase = create_supabase_mcp()

    case_id = "case_2024_002"
    search_query = "merger acquisition confidential"

    print(f"\nCase ID: {case_id}")
    print(f"Search Query: {search_query}")

    # List available channels
    print("\n1. Listing accessible channels...")
    channels = slack.list_channels()

    if not channels.get('error'):
        print(f"   Found {channels['total_channels']} channels")

        # Find legal-related channels
        legal_channels = [
            c for c in channels['channels']
            if 'legal' in c['name'].lower() or 'compliance' in c['name'].lower()
        ]

        if legal_channels:
            print(f"   Legal-related channels: {len(legal_channels)}")
            for channel in legal_channels[:3]:
                print(f"   - #{channel['name']} ({channel['num_members']} members)")

    # Search messages
    print("\n2. Searching messages...")
    results = slack.search_messages(
        query=search_query,
        count=50
    )

    if not results.get('error'):
        print(f"   Found {results['total_results']} messages")
        print(f"   Privileged: {results['privileged_count']} messages flagged")

        # Save to database
        print("\n3. Saving messages to database...")
        saved_count = 0

        for msg in results['messages']:
            result = supabase.save_discovery_item(
                item_type="slack_message",
                source="slack",
                item_id=msg['timestamp'],
                content=msg,
                privileged=msg['privilege_flagged'],
                case_id=case_id
            )

            if result.get('success'):
                saved_count += 1

        print(f"   Saved {saved_count} messages to database")


def example_cross_platform_discovery():
    """Example: Cross-platform discovery aggregation"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Cross-Platform Discovery Aggregation")
    print("="*60)

    from gmail_discovery_mcp import create_gmail_discovery_mcp
    from slack_discovery_mcp import create_slack_discovery_mcp
    from supabase_mcp_server import create_supabase_mcp

    # Initialize MCPs
    gmail = create_gmail_discovery_mcp()
    slack = create_slack_discovery_mcp()
    supabase = create_supabase_mcp()

    case_id = "case_2024_003"
    keyword = "trade secret"

    print(f"\nCase ID: {case_id}")
    print(f"Keyword: {keyword}")

    all_items = []

    # Search Gmail
    print("\n1. Searching Gmail...")
    gmail_results = gmail.search_emails(query=keyword, max_results=25)

    if not gmail_results.get('error'):
        print(f"   Found {gmail_results['total_results']} emails")
        all_items.extend([
            {'source': 'gmail', 'type': 'email', 'data': email}
            for email in gmail_results['emails']
        ])

    # Search Slack
    print("\n2. Searching Slack...")
    slack_results = slack.search_messages(query=keyword, count=25)

    if not slack_results.get('error'):
        print(f"   Found {slack_results['total_results']} messages")
        all_items.extend([
            {'source': 'slack', 'type': 'message', 'data': msg}
            for msg in slack_results['messages']
        ])

    # Aggregate results
    print(f"\n3. Aggregating results...")
    print(f"   Total items: {len(all_items)}")

    privileged_items = [
        item for item in all_items
        if item['data'].get('privilege_flagged')
    ]

    print(f"   Privileged items: {len(privileged_items)}")

    # Save all to database
    print("\n4. Saving to database...")
    for item in all_items:
        supabase.save_discovery_item(
            item_type=item['type'],
            source=item['source'],
            item_id=item['data'].get('id') or item['data'].get('timestamp'),
            content=item['data'],
            privileged=item['data'].get('privilege_flagged', False),
            case_id=case_id
        )

    # Retrieve aggregated discovery items
    print("\n5. Retrieving from database...")
    db_items = supabase.get_discovery_items(case_id=case_id, limit=100)

    if not db_items.get('error'):
        print(f"   Retrieved {db_items['count']} items from database")

        # Breakdown by source
        sources = {}
        for item in db_items['data']:
            source = item['source']
            sources[source] = sources.get(source, 0) + 1

        print("\n   Breakdown by source:")
        for source, count in sources.items():
            print(f"   - {source}: {count} items")


def example_cost_and_compliance_reporting():
    """Example: Cost tracking and compliance reporting"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Cost Tracking & Compliance Reporting")
    print("="*60)

    from mcp_logging import get_mcp_logger
    from mcp_cache import get_cache

    logger = get_mcp_logger()
    cache = get_cache()

    # Cost report
    print("\n1. API Cost Report:")
    cost_report = logger.get_cost_report()

    print(f"   Total API calls: {cost_report['total_calls']}")
    print(f"   Total estimated cost: ${cost_report['total_estimated_cost']:.2f}")

    print("\n   Breakdown by service:")
    for service, data in cost_report['by_service'].items():
        if data['calls'] > 0:
            print(f"   - {service}:")
            print(f"     Calls: {data['calls']}")
            print(f"     Cost: ${data['estimated_cost']:.2f}")

    # Cache statistics
    print("\n2. Cache Statistics:")
    cache_stats = cache.get_stats()

    print(f"   Cache type: {cache_stats['type']}")
    if cache_stats['type'] == 'file':
        print(f"   Entries: {cache_stats['entries']}")
        print(f"   Total size: {cache_stats['total_size_mb']} MB")
    else:
        print(f"   Keys: {cache_stats['keys']}")
        print(f"   Memory: {cache_stats['memory']}")

    # Compliance summary
    print("\n3. Compliance Summary:")
    compliance = logger.get_compliance_summary()

    if not compliance.get('error'):
        print(f"   Privilege detections: {compliance['privilege_detections']}")
        print(f"   Discovery actions: {compliance['discovery_actions']}")
        print(f"   Items flagged: {compliance['items_flagged']}")
        print(f"   Services accessed: {', '.join(compliance['services_accessed'])}")


def example_github_integration():
    """Example: GitHub repository tracking"""
    print("\n" + "="*60)
    print("EXAMPLE 6: GitHub Repository Tracking")
    print("="*60)

    from github_mcp_server import create_github_mcp

    github = create_github_mcp()

    owner = "your-org"
    repo = "your-repo"

    print(f"\nRepository: {owner}/{repo}")

    # Get repository info
    print("\n1. Repository Information:")
    repo_info = github.get_repository(owner, repo)

    if not repo_info.get('error'):
        print(f"   Name: {repo_info['name']}")
        print(f"   Description: {repo_info['description']}")
        print(f"   Language: {repo_info['language']}")
        print(f"   Stars: {repo_info['stars']}")
        print(f"   Forks: {repo_info['forks']}")

    # Get recent commits
    print("\n2. Recent Commits:")
    commits = github.get_commits(owner, repo, limit=5)

    if not commits.get('error'):
        print(f"   Found {commits['count']} recent commits:")
        for commit in commits['commits']:
            print(f"   - {commit['sha'][:7]}: {commit['message'][:50]}")
            print(f"     Author: {commit['author']} ({commit['date']})")

    # Get open issues
    print("\n3. Open Issues:")
    issues = github.get_issues(owner, repo, state='open', limit=5)

    if not issues.get('error'):
        print(f"   Found {issues['count']} open issues:")
        for issue in issues['issues']:
            print(f"   - #{issue['number']}: {issue['title']}")
            print(f"     Labels: {', '.join(issue['labels'])}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("MCP INTEGRATION USAGE EXAMPLES")
    print("="*60)
    print("\nThese examples demonstrate real-world workflows.")
    print("Some examples may fail if credentials are not configured.")
    print("\n" + "="*60)

    try:
        example_legal_research()
    except Exception as e:
        print(f"\n❌ Example 1 failed: {str(e)}")

    try:
        example_email_discovery()
    except Exception as e:
        print(f"\n❌ Example 2 failed: {str(e)}")

    try:
        example_slack_discovery()
    except Exception as e:
        print(f"\n❌ Example 3 failed: {str(e)}")

    try:
        example_cross_platform_discovery()
    except Exception as e:
        print(f"\n❌ Example 4 failed: {str(e)}")

    try:
        example_cost_and_compliance_reporting()
    except Exception as e:
        print(f"\n❌ Example 5 failed: {str(e)}")

    try:
        example_github_integration()
    except Exception as e:
        print(f"\n❌ Example 6 failed: {str(e)}")

    print("\n" + "="*60)
    print("EXAMPLES COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
